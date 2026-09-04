"""Load the gap map into Neon (Postgres) as the site's serving layer.

The third publisher of the same content. `build/publish_registry.py` pushes the
declarations to OSO so they can be joined against warehouse measurements; this one pushes
them to Postgres so the site can read products, scores and freshness dates at request time
instead of loading `build/notebook_data.json`. That file stays exactly what it was — the
repo's build artifact and its gate contract — and is the *input* to the site tables here,
never replaced by them.

This module is a generic CSV-to-Postgres loader with an atomic schema swap. It knows nothing
about the gap map: the tables, enums, grain, keys and column types all live in
`build/neon_schema.py`, which is the one place to change when the data model moves. Two
groups today — the designers' target model, built from the payload, and the registry tables
`publish_registry` publishes, prefixed `registry_` so the two surfaces cannot collide.

Nothing computed is here. `scores.openness_facts` and `scores.openness_computed` stay on
OSO, and no table in this schema recomputes an axis. See
`docs/reference/where-scores-live.md`.

One difference from the OSO publisher: an empty table is loaded as an empty table rather
than dropped. OSO has no way to represent a static model with no rows (dlt infers the schema
from records, so zero records is zero tables), which is why `publish_registry` deletes the
model instead. Postgres has a perfectly good empty table, and a serving layer that answers
"no rows" is better than one that answers "no such table".

## The schema, which shares an instance

The Neon instance is shared: `drizzle`, `payload` and `public` belong to other parts of the
site, and `os-ai-map` is the gap map's. So this touches exactly three schemas — its target,
`<target>_staging` and `<target>_previous` — creates and drops nothing else, and refuses
outright to run against a schema on `PROTECTED_SCHEMAS`. The default target's name carries a
hyphen, which is why schema identifiers are quoted everywhere and have their own validator.

All three are steady-state names, not transients. `<target>_staging` exists while a load is
running; `<target>_previous` exists *between* runs, holding the whole previous corpus —
tables, rows, enum types and the `SELECT` grant that travelled with the rename. So the
instance normally carries two readable copies of the map, and the previous one is only
reclaimed at the start of the next publish. Two consequences worth knowing: the storage is
roughly double, and anything with `SELECT` on the map can still read the superseded corpus
under the `_previous` name until the next load. Nothing is meant to read it, and the swap
does not stop anything from trying.

## Atomicity, because a reader is always mid-request

Site readers query this database continuously, so a load must never be observable
half-finished. Rows go into `<target>_staging`, which is dropped and recreated on every run,
and the cutover is two renames in one transaction:

    ALTER SCHEMA "os-ai-map" RENAME TO "os-ai-map_previous"
    ALTER SCHEMA "os-ai-map_staging" RENAME TO "os-ai-map"

A reader sees the old schema or the new one. On the first run there is no target to rename,
so the swap is the single staging rename; that case is decided by reading
`information_schema.schemata`, not by catching an error.

Nothing is dropped inside that transaction, which is deliberate on both counts. `DROP SCHEMA
… CASCADE` takes `AccessExclusiveLock` on every table it removes, so a drop in the cutover
would hold the applied-but-uncommitted renames behind any in-flight site query, and new
readers would then queue behind the pending exclusive lock — one slow reader stalling every
reader for as long as it runs. Pure catalog renames take no table locks at all. `lock_timeout`
is still set on the session and the transaction is retried, because the schema's own catalog
row can be contended.

## Reclaiming the previous schema, which is where the blast radius is

The old schema is left in place as `<target>_previous` and reclaimed at the *start* of the
next run, not at the end of this one. Before dropping it, `pg_depend` is checked for
dependents outside the three schemas this publisher manages, and if any exist the run fails
listing them instead of dropping.

That check is the point. `PROTECTED_SCHEMAS` stops the publisher naming someone else's
schema, but CASCADE follows dependencies, not schema membership: a view in `payload` over
`os-ai-map.products`, or a foreign key from a CMS table into it, still depends on that table
after the rename, because a rename does not detach dependents. A CASCADE would drop the
dependent object too, in its own schema, silently, on every publish — the same accident
`PROTECTED_SCHEMAS` exists to prevent, one indirection out.

A rename-based cutover cannot carry such a dependent forward, so failing loudly is the whole
of the remedy available here. See "What the CMS owns" in `build/neon_schema.py` for what to
build instead.

Grants are applied to the staging schema *before* the swap. A rename carries privileges
with it, so the new schema is readable the instant it becomes visible rather than after a
follow-up statement that could fail on its own.

## Column types: declared for the target model, inferred for the registry

`neon_schema.SITE_TABLES` declares its own types and its enums, because that module defines
the shape.
The serializers declare column *names* only, so a registry column's type is inferred:
TEXT by default and as the fallback, and BOOLEAN, INTEGER/BIGINT, DOUBLE PRECISION or DATE
only when every non-empty value in the column parses as one. Identity columns (`slug`,
anything ending `_slug` or `_id`) are pinned to TEXT whatever they look like — a
numeric-looking artifact id is a string with digits in it, and letting one run of the data
decide otherwise would change the column type from under a query the next time a
non-numeric id arrives.

In CSV mode an unquoted empty field is NULL, so an absent value arrives as NULL rather than
as an empty string, on both groups.

Environment:
    NEON_DATABASE_URL   required for a publish (not for --check)
    NEON_READ_ROLE      optional; the role granted SELECT. Defaults to PUBLIC.

Usage:
    uv run python -m build.publish_neon --check     # plan only, no connection
    uv run python -m build.publish_neon            # load and swap
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from build.neon_schema import (
    ENUMS,
    PAYLOAD_PATH,
    REGISTRY_PREFIX,
    SCHEMA_VERSION,
    SITE_TABLES,
    load_payload,
    write_site_csvs,
)
from build.publish_registry import TABLES as PUBLISHED_TABLES
from build.serialize_registry import OUT_DIR
from build.serialize_registry import TABLES as REGISTRY_TABLES
from build.serialize_registry import build_registry, write_tables

ROOT = Path(__file__).resolve().parents[1]
# The gap map's own schema on a shared Neon instance. Hyphenated, hence quoted everywhere.
DEFAULT_SCHEMA = "os-ai-map"
# Not ours, on the same instance. Refused rather than validated against, because the cost of
# being wrong is dropping someone else's schema with CASCADE.
PROTECTED_SCHEMAS = frozenset(
    {"drizzle", "payload", "public", "information_schema", "pg_catalog", "pg_toast"}
)
# Where the site tables' CSVs are rendered. Separate from build/registry/, which belongs to
# the serializers and is published to OSO from.
SITE_DIR = ROOT / "build" / "neon"
DSN_ENV = "NEON_DATABASE_URL"
READ_ROLE_ENV = "NEON_READ_ROLE"

# The run record. Its own table rather than a column on every table: the identity of a
# publish belongs to the publish, and repeating it 4,000 times would make every table's
# grain depend on how it got here.
RUN_TABLE = "publish_runs"
RUN_COLUMNS: tuple[tuple[str, str], ...] = (
    ("run_id", "TEXT"),
    ("published_at", "TIMESTAMPTZ"),
    # The shape this load was built to. There is no migration tool: the swap rebuilds the
    # schema every time, so this is how a reader tells which shape it is looking at. See
    # "Migrations" in build/neon_schema.py.
    ("schema_version", "INTEGER"),
    # When the payload was built, and when the release it belongs to was cut. The third
    # date — when a product's score was last confirmed — is per product, on `products`.
    ("built_at", "DATE"),
    ("released_at", "DATE"),
    ("source_git_sha", "TEXT"),
    ("declaration_version_id", "TEXT"),
    ("table_count", "INTEGER"),
    ("row_counts", "JSONB"),
)

# Never inferred away from TEXT, however this run's values happen to look.
_TEXT_NAMES = frozenset({"slug", "artifact_id", "alias", "handle", "pattern", "target"})

_INT = re.compile(r"^-?\d+$")
_INT32 = 2**31 - 1
_TRUE_FALSE = frozenset({"true", "false"})


def is_text_column(name: str) -> bool:
    """Identity columns stay TEXT. Slugs and ids are strings that sometimes hold digits."""
    return name in _TEXT_NAMES or name.endswith("_slug") or name.endswith("_id")


def _all_parse(values: list[str], parse) -> bool:
    for value in values:
        try:
            parse(value)
        except (TypeError, ValueError):
            return False
    return True


def infer_column_type(name: str, values: list[str]) -> str:
    """The narrowest type every non-empty value in the column satisfies, else TEXT.

    An all-empty column is TEXT: nothing in the data argues for anything narrower, and a
    guess would be reversed by the first real value.
    """
    if is_text_column(name):
        return "TEXT"
    present = [v for v in values if v != ""]
    if not present:
        return "TEXT"
    if all(v.lower() in _TRUE_FALSE for v in present):
        return "BOOLEAN"
    if all(_INT.match(v) for v in present):
        return "INTEGER" if all(abs(int(v)) <= _INT32 for v in present) else "BIGINT"
    if _all_parse(present, float):
        return "DOUBLE PRECISION"
    if _all_parse(present, lambda v: datetime.strptime(v, "%Y-%m-%d")):
        return "DATE"
    return "TEXT"


@dataclass(frozen=True)
class TablePlan:
    """One CSV, resolved to a table: its name, columns, constraints and row count."""

    name: str
    columns: tuple[tuple[str, str], ...]
    row_count: int
    path: Path
    constraints: tuple[str, ...] = ()


def plan_table(
    path: Path,
    declared: tuple[tuple[str, str], ...] | None = None,
    name: str | None = None,
    constraints: tuple[str, ...] = (),
) -> TablePlan:
    """Plan one CSV. `declared` supplies the column types; without it they are inferred.

    `name` is the destination table, which is not always the file's stem: group A's tables
    are prefixed so they cannot collide with group B's `products`/`categories`/`organizations`
    in the shared schema.

    A declared spec is still checked against the file's header, because a spec that has
    drifted from the CSV it describes would otherwise COPY values into the wrong columns —
    which Postgres would accept wherever the types happened to line up.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        rows = list(reader)
    if declared is not None:
        expected = [name for name, _type in declared]
        if header != expected:
            raise ValueError(
                f"{path.name}: header {header} does not match the declared columns {expected}"
            )
        columns = declared
    else:
        columns = tuple(
            (name, infer_column_type(name, [row[index] if index < len(row) else "" for row in rows]))
            for index, name in enumerate(header)
        )
    return TablePlan(
        name=name or path.stem,
        columns=columns,
        row_count=len(rows),
        path=path,
        constraints=constraints,
    )


def ensure_registry_csvs(directory: Path) -> None:
    """Regenerate the registry serializer's own CSVs when they are absent.

    Only that one. The rubric, routing and scores serializers each have their own
    preconditions, and a publisher that silently invoked all four would hide which one
    produced a surprising table — so their absence is reported by `plan` rather than
    papered over here.
    """
    if all((directory / f"{name}.csv").exists() for name in REGISTRY_TABLES):
        return
    from build.validate import load_sources

    tables, errors, _warnings = build_registry(load_sources(ROOT))
    if errors:
        raise RuntimeError(
            f"the registry does not serialize cleanly ({len(errors)} error(s)); "
            f"run build.serialize_registry to see them"
        )
    write_tables(tables, directory)


def plan(
    directory: Path = OUT_DIR,
    site_dir: Path = SITE_DIR,
    payload_path: Path = PAYLOAD_PATH,
) -> tuple[list[TablePlan], list[str]]:
    """(plans, missing) over both groups, group B first, each in its declared order.

    Never a glob. `missing` names the declared tables whose CSV has not been written, which
    a real publish refuses and `--check` reports — a table is absent because a serializer
    has not run, and loading the rest would publish a partial map that looks complete.

    The site tables are rendered to CSV here from `build/notebook_data.json`, so both groups
    reach the database through one COPY path.
    """
    ensure_registry_csvs(directory)
    plans: list[TablePlan] = []
    missing: list[str] = []

    if payload_path.exists():
        write_site_csvs(load_payload(payload_path), site_dir)
        for name, spec in SITE_TABLES.items():
            plans.append(
                plan_table(
                    site_dir / f"{name}.csv",
                    declared=spec.columns,
                    constraints=spec.constraints,
                )
            )
    else:
        missing.extend(SITE_TABLES)

    for name in PUBLISHED_TABLES:
        path = directory / f"{name}.csv"
        if path.exists():
            plans.append(plan_table(path, name=f"{REGISTRY_PREFIX}{name}"))
        else:
            missing.append(f"{REGISTRY_PREFIX}{name}")
    return plans, missing


def quote_ident(name: str) -> str:
    """Double-quote an identifier. Rejects anything that is not a plain name.

    Table names come from filenames and column names from a serializer's header, so a
    quoted identifier is defence against a filename rather than against a user. Refusing
    the odd shapes outright is clearer than escaping them into something loadable.
    """
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"not a usable SQL identifier: {name!r}")
    return f'"{name}"'


def quote_schema(name: str) -> str:
    """Double-quote a schema name, allowing the hyphen `os-ai-map` carries.

    Its own validator rather than a looser `quote_ident`: a hyphen is fine in a schema
    chosen by a maintainer and is not something a serializer should ever be able to put in
    a table or column name. Anything that would need escaping to survive quoting — a quote
    character, a backslash, whitespace — is refused, because a schema name reaches
    `DROP SCHEMA ... CASCADE`.
    """
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", name):
        raise ValueError(f"not a usable schema name: {name!r}")
    return f'"{name}"'


def check_schema_is_ours(schema: str) -> None:
    """Refuse a schema that belongs to another part of the site.

    This publisher drops and renames whole schemas with CASCADE, and the Neon instance is
    shared with `drizzle`, `payload` and `public`. A typo in `--schema` must not be able to
    take one of those with it.
    """
    quote_schema(schema)
    if schema.lower() in PROTECTED_SCHEMAS:
        raise ValueError(
            f"{schema!r} belongs to another part of the site and this publisher drops "
            f"schemas with CASCADE; refusing. The gap map's schema is {DEFAULT_SCHEMA!r}."
        )
    if schema.lower().endswith(("_staging", "_previous")):
        raise ValueError(
            f"{schema!r} names a schema this publisher manages itself; pass the target "
            f"schema (default {DEFAULT_SCHEMA!r}), not its staging or previous form."
        )


def create_table_sql(
    schema: str,
    columns: tuple[tuple[str, str], ...],
    name: str,
    constraints: tuple[str, ...] = (),
) -> str:
    """DDL for one table. An enum type or a FK target carries `{schema}`, filled in here.

    Enum types are schema-scoped and are created inside the staging schema so they travel
    with the rename, which means a column referencing one has to qualify it — the staging
    schema is never on the search path. A foreign key's target is qualified for the same
    reason, so the reference resolves inside the schema being built rather than against
    whatever `os-ai-map` happens to hold at the time.

    `constraints` is empty for the registry group: the serializers declare column names only,
    so there is nothing to derive a key from, and inventing one would be this module guessing
    at another module's grain.
    """
    quoted_schema = quote_schema(schema)
    parts = [
        f"{quote_ident(column)} {sql_type.format(schema=quoted_schema)}"
        for column, sql_type in columns
    ]
    parts += [clause.format(schema=quoted_schema) for clause in constraints]
    body = ",\n  ".join(parts)
    return f"CREATE TABLE {quoted_schema}.{quote_ident(name)} (\n  {body}\n)"


def create_enum_sql(schema: str) -> list[str]:
    """One CREATE TYPE per enum, inside the schema being built."""
    return [
        f"CREATE TYPE {quote_schema(schema)}.{quote_ident(name)} AS ENUM ("
        + ", ".join(f"'{value}'" for value in values)
        + ")"
        for name, values in ENUMS.items()
    ]


def copy_sql(schema: str, plan_: TablePlan) -> str:
    names = ", ".join(quote_ident(column) for column, _type in plan_.columns)
    return (
        f"COPY {quote_schema(schema)}.{quote_ident(plan_.name)} ({names}) "
        f"FROM STDIN WITH (FORMAT csv, HEADER true)"
    )


def stream_bytes(path: Path, write, chunk_size: int = 1 << 16) -> int:
    """Feed a file to `write` in chunks, byte for byte. Returns the bytes written.

    The CSV is handed to `COPY ... FROM STDIN WITH (FORMAT csv)` verbatim, so Postgres's own
    CSV parser does the quoting — this must not reformat, re-encode or line-split anything.
    A quoted field can hold a newline (several `strapline` and `note` values do), so a
    chunked read that respected line boundaries, or a text-mode read that translated them,
    would corrupt exactly those rows. Bytes in, bytes out, and the chunk boundary is allowed
    to fall anywhere.
    """
    written = 0
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            write(chunk)
            written += len(chunk)
    return written


def grant_sql(schema: str, role: str | None) -> list[str]:
    """USAGE on the schema plus SELECT on its tables, for PUBLIC or a named role."""
    grantee = "PUBLIC" if not role else quote_ident(role)
    return [
        f"GRANT USAGE ON SCHEMA {quote_schema(schema)} TO {grantee}",
        f"GRANT SELECT ON ALL TABLES IN SCHEMA {quote_schema(schema)} TO {grantee}",
    ]


def swap_sql(schema: str, live_exists: bool) -> list[str]:
    """The cutover, as the statements to run inside one transaction. Renames only.

    `live_exists` decides the shape rather than an exception: on the first run there is no
    live schema to rename, and renaming a schema that is not there is a different error
    from every other reason a rename fails.

    Nothing is dropped here. The old schema is left as `<schema>_previous` for the next run
    to reclaim, because a `DROP SCHEMA … CASCADE` in this transaction would both take
    `AccessExclusiveLock` on every table it removes — stalling the cutover behind any
    in-flight reader — and follow dependencies out of this schema. See `reclaim_previous`.
    """
    staging = f"{schema}_staging"
    previous = f"{schema}_previous"
    if not live_exists:
        return [f"ALTER SCHEMA {quote_schema(staging)} RENAME TO {quote_schema(schema)}"]
    return [
        f"ALTER SCHEMA {quote_schema(schema)} RENAME TO {quote_schema(previous)}",
        f"ALTER SCHEMA {quote_schema(staging)} RENAME TO {quote_schema(schema)}",
    ]


# Objects in these schemas may depend on the previous schema's tables: they are ours, and the
# dependency is one this publisher created (a foreign key inside the map group, an index).
def working_schemas(schema: str) -> list[str]:
    return [schema, f"{schema}_staging", f"{schema}_previous"]


# Dependents of the previous schema that live somewhere else on the instance. Three shapes,
# because those are the three a CASCADE would silently take with it, and each is reported with
# the schema, the relation and how it depends — the message has to be actionable by someone
# who did not write this.
#
#   1. a view or materialized view selecting from one of our tables (pg_rewrite);
#   2. a foreign key pointing into one (pg_constraint);
#   3. a column anywhere else typed as one of our enums (pg_attribute -> pg_type).
#
# The third is easy to miss because the hazard is not a table at all. The enum types are
# created inside the staging schema so they travel with the rename, which means they travel
# into `_previous` too — so a CMS column declared `os-ai-map.health_status` ends up typed by a
# type in `_previous`, and reclaiming would drop the type and the column with it. Composite
# types (relkind 'c') are excluded: every table has one, so they would report each of our own
# tables as a dependent of itself.
DEPENDENTS_SQL = """
WITH previous_relations AS (
    SELECT c.oid
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = %(previous)s
),
previous_types AS (
    SELECT t.oid, t.typname
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = %(previous)s
      AND t.typtype <> 'c'
)
SELECT DISTINCT n.nspname AS schema_name, c.relname AS relation, 'view or rule' AS via
FROM pg_depend d
JOIN previous_relations p ON p.oid = d.refobjid
JOIN pg_rewrite r ON r.oid = d.objid AND d.classid = 'pg_rewrite'::regclass
JOIN pg_class c ON c.oid = r.ev_class
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE NOT (n.nspname = ANY(%(working)s))
UNION
SELECT DISTINCT n.nspname, c.relname, 'foreign key ' || co.conname
FROM pg_constraint co
JOIN previous_relations p ON p.oid = co.confrelid
JOIN pg_class c ON c.oid = co.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE NOT (n.nspname = ANY(%(working)s))
UNION
SELECT DISTINCT n.nspname, c.relname || '.' || a.attname, 'column typed ' || t.typname
FROM pg_attribute a
JOIN previous_types t ON t.oid = a.atttypid
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE NOT (n.nspname = ANY(%(working)s))
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY 1, 2
"""


class ExternalDependents(RuntimeError):
    """Something outside this publisher's schemas depends on the schema about to be dropped."""


def schema_exists(cursor, schema: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s", (schema,)
    )
    return cursor.fetchone() is not None


def external_dependents(cursor, schema: str) -> list[tuple[str, str, str]]:
    """(schema, relation, how) for every dependent of `<schema>_previous` we do not own.

    Covers tables and the enum types, which is not the same question: the types are created
    in the staging schema so they travel with the rename, so a column elsewhere declared with
    one of ours is typed by a type that is now in `_previous`.
    """
    cursor.execute(
        DEPENDENTS_SQL,
        {"previous": f"{schema}_previous", "working": working_schemas(schema)},
    )
    return [tuple(row) for row in cursor.fetchall()]


def reclaim_previous(cursor, schema: str) -> bool:
    """Drop `<schema>_previous` if it is safe to. Returns whether anything was dropped.

    Runs at the start of a publish, before the staging build, so a run that cannot safely
    reclaim fails before it has done any work rather than after loading 18,000 rows.

    Raises `ExternalDependents` rather than dropping when anything outside the three working
    schemas depends on it. A rename-based cutover has nowhere to carry such a dependent
    forward, so this cannot be repaired here — but dropping someone else's view to get on
    with a publish is not a trade this publisher is allowed to make on its own.
    """
    previous = f"{schema}_previous"
    if not schema_exists(cursor, previous):
        return False
    dependents = external_dependents(cursor, schema)
    if dependents:
        listed = "\n".join(
            f"  {dep_schema}.{relation}  ({via})" for dep_schema, relation, via in dependents
        )
        raise ExternalDependents(
            f"{len(dependents)} object(s) outside {schema!r} depend on {previous!r}, which "
            f"this run needs to drop:\n{listed}\n"
            f"Dropping it would take them with it (CASCADE follows dependencies, not schema "
            f"membership), so this run has stopped instead. A view over a table in {schema!r} "
            f"cannot survive the cutover in any case — the rename leaves it bound to the old "
            f"table by OID. Drop or repoint these objects, or move them to a schema that "
            f"reads {schema!r} directly; see 'What the CMS owns' in build/neon_schema.py."
        )
    cursor.execute(f"DROP SCHEMA IF EXISTS {quote_schema(previous)} CASCADE")
    return True


# The swap contends only for the schemas' own catalog rows now that it drops nothing, but a
# concurrent DDL or a long transaction holding the namespace can still block it. Five seconds
# is far longer than a rename needs and short enough that a stalled cutover retries rather
# than parks; three attempts, because the second failing for the same reason as the first is
# already evidence that waiting is not the remedy.
LOCK_TIMEOUT = "5s"
SWAP_ATTEMPTS = 3
SWAP_BACKOFF = (1.0, 3.0)
# 55P03 lock_not_available (our lock_timeout firing), 40P01 deadlock_detected.
RETRYABLE_SQLSTATES = frozenset({"55P03", "40P01"})


def is_retryable(error: Exception) -> bool:
    """Whether a failed swap is worth another attempt. Reads the SQLSTATE, never the message.

    A driver-independent predicate: psycopg exposes `sqlstate`, and a test can raise anything
    carrying the attribute without standing up a database.
    """
    return getattr(error, "sqlstate", None) in RETRYABLE_SQLSTATES


def swap_in_place(
    connection,
    schema: str,
    live_exists: bool,
    *,
    attempts: int = SWAP_ATTEMPTS,
    sleep=time.sleep,
) -> int:
    """Run the cutover in one transaction, retrying a lock timeout. Returns the attempt count.

    Each attempt is its own transaction: a lock timeout aborts it, so retrying inside the
    failed transaction would be retrying inside an aborted one.
    """
    for attempt in range(1, attempts + 1):
        try:
            with connection.transaction(), connection.cursor() as cursor:
                for statement in swap_sql(schema, live_exists):
                    cursor.execute(statement)
            return attempt
        except Exception as error:
            if attempt == attempts or not is_retryable(error):
                raise
            delay = SWAP_BACKOFF[min(attempt, len(SWAP_BACKOFF)) - 1]
            print(
                f"  swap attempt {attempt} could not take its lock; retrying in {delay:g}s",
                file=sys.stderr,
            )
            sleep(delay)
    raise AssertionError("unreachable: the loop returns or raises")


def require_ssl(dsn: str) -> str:
    """Append `sslmode=require` unless the DSN already says something about SSL.

    Neon requires TLS, so a DSN without it fails anyway; this makes it fail nowhere rather
    than at connect time on a machine whose libpq defaults differ.
    """
    parsed = urlparse(dsn)
    if not parsed.scheme:
        return dsn if "sslmode=" in dsn else f"{dsn} sslmode=require"
    params = parse_qsl(parsed.query, keep_blank_values=True)
    if any(key == "sslmode" for key, _value in params):
        return dsn
    params.append(("sslmode", "require"))
    return urlunparse(parsed._replace(query=urlencode(params)))


def scrub(text: str, dsn: str) -> str:
    """Remove the DSN, its password and its host from a message before it is printed.

    A libpq failure quotes the host it could not reach, and a URL-shaped DSN carries the
    password one delimiter away from it. Neither belongs in a CI log, so every message
    that could have come from the driver goes through here.
    """
    out = text.replace(dsn, "[redacted]")
    parsed = urlparse(dsn)
    for secret in (parsed.password, parsed.hostname, parsed.username):
        if secret:
            out = out.replace(secret, "[redacted]")
    return out


def declaration_identity() -> tuple[str | None, str | None]:
    """(source_git_sha, declaration_version_id) for the run record, or (None, None).

    `allow_dirty=True` because this records what was published, not what may be trusted as
    reproducible — a dirty tree is a local run, and refusing to write a row would lose the
    record of the load that actually happened. On main the tree is clean and the pair is the
    reproducible identity of the declarations.
    """
    try:
        from build.declaration_version import resolve

        info = resolve(allow_dirty=True)
        return info["source_git_sha"], info["declaration_version_id"]
    except Exception:  # noqa: BLE001 - the run record is not worth failing a publish over
        return None, None


def publish(dsn: str, plans: list[TablePlan], schema: str, read_role: str | None) -> dict:
    """Load every plan into the staging schema and swap it into place. Returns the run record.

    The only schemas touched are `schema`, `<schema>_staging` and `<schema>_previous`, which
    holds the last load until this one reclaims it. `check_schema_is_ours` runs first, because
    the instance is shared and reclaiming drops a schema with CASCADE.

    Order matters: the previous schema is reclaimed before the staging build, so a run that
    cannot safely drop it fails before loading anything, and the swap has a free name to
    rename the live schema to.
    """
    import psycopg

    check_schema_is_ours(schema)
    staging = f"{schema}_staging"
    git_sha, version_id = declaration_identity()
    payload = load_payload() if PAYLOAD_PATH.exists() else {}
    record = {
        "run_id": uuid.uuid4().hex,
        "published_at": datetime.now(UTC),
        "schema_version": SCHEMA_VERSION,
        "built_at": payload.get("generated") or None,
        "released_at": payload.get("released") or None,
        "source_git_sha": git_sha,
        "declaration_version_id": version_id,
        "table_count": len(plans),
        "row_counts": {p.name: p.row_count for p in plans},
    }

    with psycopg.connect(require_ssl(dsn), autocommit=True) as connection:
        with connection.cursor() as cursor:
            # Session-wide, so it covers the swap transaction and every statement here. A
            # rename needs milliseconds; anything that waits five seconds for a lock is
            # contended, and waiting longer inside a cutover is the failure mode to avoid.
            cursor.execute(f"SET lock_timeout = '{LOCK_TIMEOUT}'")
            if reclaim_previous(cursor, schema):
                print(f"  reclaimed {schema}_previous from the last load")
            cursor.execute(f"DROP SCHEMA IF EXISTS {quote_schema(staging)} CASCADE")
            cursor.execute(f"CREATE SCHEMA {quote_schema(staging)}")
            # Enums first: a table referencing one cannot be created before the type exists,
            # and the types live inside the staging schema so the rename carries them.
            for statement in create_enum_sql(staging):
                cursor.execute(statement)
            for plan_ in plans:
                cursor.execute(
                    create_table_sql(staging, plan_.columns, plan_.name, plan_.constraints)
                )
                with cursor.copy(copy_sql(staging, plan_)) as copy:
                    stream_bytes(plan_.path, copy.write)
                print(f"  {plan_.name:<24} {plan_.row_count:>6} rows")

            cursor.execute(create_table_sql(staging, RUN_COLUMNS, RUN_TABLE))
            cursor.execute(
                f"INSERT INTO {quote_schema(staging)}.{quote_ident(RUN_TABLE)} "
                f"(run_id, published_at, schema_version, built_at, released_at, "
                f"source_git_sha, declaration_version_id, table_count, row_counts) "
                f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    record["run_id"],
                    record["published_at"],
                    record["schema_version"],
                    record["built_at"],
                    record["released_at"],
                    record["source_git_sha"],
                    record["declaration_version_id"],
                    record["table_count"],
                    json.dumps(record["row_counts"]),
                ),
            )
            for statement in grant_sql(staging, read_role):
                cursor.execute(statement)

            live_exists = schema_exists(cursor, schema)

        # One transaction, so no reader ever sees the schema absent or half-renamed.
        attempts = swap_in_place(connection, schema, live_exists)
        if attempts > 1:
            print(f"  swap committed on attempt {attempts}")

    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="plan only: print the tables and row counts, connect to nothing"
    )
    parser.add_argument("--dsn-env", default=DSN_ENV, help=f"env var holding the DSN (default {DSN_ENV})")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, help=f"target schema (default {DEFAULT_SCHEMA})")
    parser.add_argument("--dir", type=Path, default=OUT_DIR, help="directory of serialized CSVs")
    parser.add_argument(
        "--site-dir", type=Path, default=SITE_DIR, help="where the site tables' CSVs are rendered"
    )
    args = parser.parse_args()

    try:
        check_schema_is_ours(args.schema)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    plans, missing = plan(args.dir, args.site_dir)

    if args.check:
        # A plan, not a gate on completeness: on a PR only the registry serializer's CSVs
        # exist, because the check job validates the other three without writing. So the
        # unwritten tables are reported as pending rather than failed.
        total_declared = len(PUBLISHED_TABLES) + len(SITE_TABLES)
        print(
            f"would load {total_declared} tables into {args.schema}_staging, "
            f"then swap to {args.schema}:"
        )
        for plan_ in plans:
            group = "map" if plan_.name in SITE_TABLES else "registry"
            keys = f"{len(plan_.constraints):>2} constraints" if plan_.constraints else ""
            print(
                f"  {plan_.name:<28} {plan_.row_count:>6} rows  "
                f"{len(plan_.columns):>2} columns  [{group}] {keys}"
            )
        print(f"  {len(ENUMS)} enums: {', '.join(ENUMS)}")
        print(
            f"  {sum(len(p.constraints) for p in plans)} table constraints "
            f"(primary keys, uniques and foreign keys, on the map group)"
        )
        # Only the inferred types are worth printing. The map group's are declared in
        # build/neon_schema.py, where a reader can see them next to the grain they describe;
        # the registry group's are a guess this run made about the data, which is the thing
        # a reviewer needs to see change.
        for plan_ in plans:
            if plan_.name in SITE_TABLES:
                continue
            for column, sql_type in plan_.columns:
                if sql_type != "TEXT":
                    print(f"    inferred {plan_.name}.{column} -> {sql_type}")
        print(f"  {RUN_TABLE:<28} {1:>6} row   {len(RUN_COLUMNS):>2} columns  [run record]")
        for name in missing:
            print(f"  {name:<28}  pending: not serialized yet")
        return 0

    # Configuration before inputs: with no DSN there is nowhere to publish whatever the
    # inputs turn out to be, and that is the more useful thing to be told first.
    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        print(f"{args.dsn_env} is not set; nothing to publish to", file=sys.stderr)
        return 2

    if missing:
        print(
            f"missing tables: {missing}. Run build.serialize_registry, build.serialize_rubric, "
            f"build.serialize_routing and build.serialize_scores first — loading the rest "
            f"would publish a partial map that looks complete.",
            file=sys.stderr,
        )
        return 2

    read_role = os.environ.get(READ_ROLE_ENV) or None
    print(f"loading {len(plans)} tables into {args.schema}_staging:")
    try:
        record = publish(dsn, plans, args.schema, read_role)
    except Exception as error:  # noqa: BLE001 - re-raised scrubbed; the driver quotes the host
        print(f"publish failed: {scrub(str(error), dsn)}", file=sys.stderr)
        return 1

    total = sum(record["row_counts"].values())
    print(
        f"swapped {args.schema} in place: {record['table_count']} tables, {total:,} rows, "
        f"run {record['run_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
