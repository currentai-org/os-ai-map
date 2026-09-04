"""Load the serialized registry CSVs into Neon (Postgres) as the site's serving layer.

The third publisher of the same declarations. `build/publish_registry.py` pushes them to
OSO so they can be queried and joined against warehouse measurements; this one pushes them
to Postgres so the front end can read them at request time without going through the
warehouse. `build/notebook_data.json` stays what it was — the repo's build artifact and the
gate contract — and nothing here reads or replaces it.

Only the *declarative* layer travels: whatever CSVs the serializers have written into
`build/registry/`. Computed openness lives in `currentai.scores` and is not mirrored here;
see `docs/reference/where-scores-live.md`.

## Atomicity, because a reader is always mid-request

Site readers query this database continuously, so a load must never be observable
half-finished. Rows go into `gapmap_staging`, which is dropped and recreated on every run,
and the cutover is three renames in one transaction:

    DROP SCHEMA IF EXISTS gapmap_previous CASCADE      -- a prior run that died mid-swap
    ALTER SCHEMA gapmap RENAME TO gapmap_previous
    ALTER SCHEMA gapmap_staging RENAME TO gapmap
    DROP SCHEMA gapmap_previous CASCADE

A reader sees the old schema or the new one. On the first run there is no `gapmap` to
rename, so the swap is the single `gapmap_staging` -> `gapmap` rename; that case is decided
by reading `information_schema.schemata`, not by catching an error.

Grants are applied to the staging schema *before* the swap. A rename carries privileges
with it, so the new schema is readable the instant it becomes visible rather than after a
follow-up statement that could fail on its own.

## Column types are inferred conservatively

TEXT is the default and the fallback. A column becomes BOOLEAN, INTEGER/BIGINT, DOUBLE
PRECISION or DATE only when every non-empty value in it parses as one, and identity columns
(`slug`, anything ending `_slug` or `_id`) are pinned to TEXT whatever they look like — a
numeric-looking artifact id is a string with digits in it, and letting one run of the data
decide otherwise would change the column type from under a query the next time a
non-numeric id arrives.

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
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from build.serialize_registry import OUT_DIR
from build.serialize_registry import TABLES as REGISTRY_TABLES
from build.serialize_registry import build_registry, write_tables

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = "gapmap"
DSN_ENV = "NEON_DATABASE_URL"
READ_ROLE_ENV = "NEON_READ_ROLE"

# The run record. Its own table rather than a column on every table: the identity of a
# publish belongs to the publish, and repeating it 4,000 times would make every table's
# grain depend on how it got here.
RUN_TABLE = "publish_runs"
RUN_COLUMNS: tuple[tuple[str, str], ...] = (
    ("run_id", "TEXT"),
    ("published_at", "TIMESTAMPTZ"),
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
    """One CSV, resolved to a table: its name, its typed columns, and its row count."""

    name: str
    columns: tuple[tuple[str, str], ...]
    row_count: int
    path: Path


def plan_table(path: Path) -> TablePlan:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        rows = list(reader)
    columns = tuple(
        (name, infer_column_type(name, [row[index] if index < len(row) else "" for row in rows]))
        for index, name in enumerate(header)
    )
    return TablePlan(name=path.stem, columns=columns, row_count=len(rows), path=path)


def ensure_csvs(directory: Path) -> None:
    """Regenerate the registry CSVs when they are absent.

    Only the registry serializer's own tables are regenerated. The rubric, routing and
    scores serializers write into the same directory and are published from it too, so
    whatever they have left there is loaded as well — but this module does not run them,
    because each has its own preconditions and a publisher silently invoking four
    serializers hides which one produced a surprising table.
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


def plan(directory: Path = OUT_DIR) -> list[TablePlan]:
    """Every CSV in the directory, as a table plan, in a stable order."""
    ensure_csvs(directory)
    return [plan_table(path) for path in sorted(directory.glob("*.csv"))]


def quote_ident(name: str) -> str:
    """Double-quote an identifier. Rejects anything that is not a plain name.

    Table names come from filenames and column names from a serializer's header, so a
    quoted identifier is defence against a filename rather than against a user. Refusing
    the odd shapes outright is clearer than escaping them into something loadable.
    """
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"not a usable SQL identifier: {name!r}")
    return f'"{name}"'


def create_table_sql(schema: str, columns: tuple[tuple[str, str], ...], name: str) -> str:
    body = ",\n  ".join(f"{quote_ident(column)} {sql_type}" for column, sql_type in columns)
    return f"CREATE TABLE {quote_ident(schema)}.{quote_ident(name)} (\n  {body}\n)"


def copy_sql(schema: str, plan_: TablePlan) -> str:
    names = ", ".join(quote_ident(column) for column, _type in plan_.columns)
    return (
        f"COPY {quote_ident(schema)}.{quote_ident(plan_.name)} ({names}) "
        f"FROM STDIN WITH (FORMAT csv, HEADER true)"
    )


def grant_sql(schema: str, role: str | None) -> list[str]:
    """USAGE on the schema plus SELECT on its tables, for PUBLIC or a named role."""
    grantee = "PUBLIC" if not role else quote_ident(role)
    return [
        f"GRANT USAGE ON SCHEMA {quote_ident(schema)} TO {grantee}",
        f"GRANT SELECT ON ALL TABLES IN SCHEMA {quote_ident(schema)} TO {grantee}",
    ]


def swap_sql(schema: str, live_exists: bool) -> list[str]:
    """The cutover, as the statements to run inside one transaction.

    `live_exists` decides the shape rather than an exception: on the first run there is no
    live schema to rename, and renaming a schema that is not there is a different error
    from every other reason a rename fails.
    """
    staging = f"{schema}_staging"
    previous = f"{schema}_previous"
    if not live_exists:
        return [f"ALTER SCHEMA {quote_ident(staging)} RENAME TO {quote_ident(schema)}"]
    return [
        f"DROP SCHEMA IF EXISTS {quote_ident(previous)} CASCADE",
        f"ALTER SCHEMA {quote_ident(schema)} RENAME TO {quote_ident(previous)}",
        f"ALTER SCHEMA {quote_ident(staging)} RENAME TO {quote_ident(schema)}",
        f"DROP SCHEMA {quote_ident(previous)} CASCADE",
    ]


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
    """Load every plan into the staging schema and swap it into place. Returns the run record."""
    import psycopg

    staging = f"{schema}_staging"
    git_sha, version_id = declaration_identity()
    record = {
        "run_id": uuid.uuid4().hex,
        "published_at": datetime.now(UTC),
        "source_git_sha": git_sha,
        "declaration_version_id": version_id,
        "table_count": len(plans),
        "row_counts": {p.name: p.row_count for p in plans},
    }

    with psycopg.connect(require_ssl(dsn), autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP SCHEMA IF EXISTS {quote_ident(staging)} CASCADE")
            cursor.execute(f"CREATE SCHEMA {quote_ident(staging)}")
            for plan_ in plans:
                cursor.execute(create_table_sql(staging, plan_.columns, plan_.name))
                with (
                    plan_.path.open("rb") as handle,
                    cursor.copy(copy_sql(staging, plan_)) as copy,
                ):
                    while chunk := handle.read(1 << 16):
                        copy.write(chunk)
                print(f"  {plan_.name:<24} {plan_.row_count:>6} rows")

            cursor.execute(create_table_sql(staging, RUN_COLUMNS, RUN_TABLE))
            cursor.execute(
                f"INSERT INTO {quote_ident(staging)}.{quote_ident(RUN_TABLE)} "
                f"(run_id, published_at, source_git_sha, declaration_version_id, "
                f"table_count, row_counts) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    record["run_id"],
                    record["published_at"],
                    record["source_git_sha"],
                    record["declaration_version_id"],
                    record["table_count"],
                    json.dumps(record["row_counts"]),
                ),
            )
            for statement in grant_sql(staging, read_role):
                cursor.execute(statement)

            cursor.execute(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s", (schema,)
            )
            live_exists = cursor.fetchone() is not None

        # One transaction, so no reader ever sees the schema absent or half-renamed.
        with connection.transaction(), connection.cursor() as cursor:
            for statement in swap_sql(schema, live_exists):
                cursor.execute(statement)

    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="plan only: print the tables and row counts, connect to nothing"
    )
    parser.add_argument("--dsn-env", default=DSN_ENV, help=f"env var holding the DSN (default {DSN_ENV})")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, help=f"target schema (default {DEFAULT_SCHEMA})")
    parser.add_argument("--dir", type=Path, default=OUT_DIR, help="directory of serialized CSVs")
    args = parser.parse_args()

    plans = plan(args.dir)
    if not plans:
        print(f"no CSVs in {args.dir}", file=sys.stderr)
        return 2

    if args.check:
        print(f"would load {len(plans)} tables into {args.schema}_staging, then swap to {args.schema}:")
        for plan_ in plans:
            print(f"  {plan_.name:<24} {plan_.row_count:>6} rows  {len(plan_.columns)} columns")
        for plan_ in plans:
            for column, sql_type in plan_.columns:
                if sql_type != "TEXT":
                    print(f"    {plan_.name}.{column} -> {sql_type}")
        print(f"  {RUN_TABLE:<24} {1:>6} row   {len(RUN_COLUMNS)} columns")
        return 0

    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        print(f"{args.dsn_env} is not set; nothing to publish to", file=sys.stderr)
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
