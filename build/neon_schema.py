"""What the Neon serving layer holds — the one place to change the table set.

`build/publish_neon.py` is a generic CSV-to-Postgres loader with an atomic schema swap. It
knows nothing about the gap map. This module is the map half: which tables exist, which
enums, what every column is, and where each row comes from.

`SITE_TABLES` is the designers' target model, transcribed in
`Current-AI-Initial-Schema.pdf` (Laith, CLEVER FRANKE) with Carl's amendments. This load
exists to deprecate `build/notebook_data.json` as the site's transport, so every row here is
derived from that payload's semantics — the same content the front end reads today, at a
grain a query can use. Rows come from the file rather than from a fresh `build_payload`
because it is the repo's build artifact and its gate contract: what Postgres serves is
byte-for-byte what the repo published, not a second derivation that could disagree with it.

That is the whole surface. The registry tables the serializers write to `build/registry/*.csv`
were loaded here too for a while, prefixed `registry_`, so Neon and the warehouse would carry
the same declarations. Nothing on the site ever read them and the designers never asked for
them, so they are gone: the registry surface lives in the warehouse as `currentai.registry.*`
and in `build/registry/*.csv`, and Neon serves the site's tables and nothing else.

## Keys are natural where the payload has one, and every surrogate id is derived from one

`products.id` exists for the FK shape the designers specified. It is not a position: it is
`stable_id("products", slug)`, the first 63 bits of a SHA-256 over the table name and the
row's natural key. Ids used to be assigned by sorted slug order, which meant adding one
product renumbered every row after it — so any id that had escaped into a URL, a cache or a
CMS reference pointed at a different product after the next publish. Deriving the id from
the key instead makes it stable across loads and independent of what else is in the corpus.

Hashing the table name in as well means the same slug in two tables gets two different ids,
so a mistaken join across them finds nothing rather than appearing to work.

The natural key per table: `products.slug`, `categories.slug`, `layers` and `gaps` by their
label, `stages` by their stage number, `long_tail_top` by its name, `product_lineage` by
`(product_slug, relation, target)`, `sources` by
`(product_slug, metric, url, shows, accessed)`. Organizations key on `slug` and aliases on
`alias` directly, with no surrogate at all.

The ids are 63-bit, so the columns are `BIGINT` where the designers' model says `integer`.
Postgres has no unsigned integer type, which is why 63 bits and not 64: the top bit would
make half the ids negative.

**The slug is still the identity.** A stable id is safe to store as an internal reference,
but a link, a bookmark, a CMS row or anything a person reads should carry the slug. The id
is a join key, and it changes if the natural key it is derived from ever changes.

A source's key carries `shows` and `accessed` because the URL alone does not identify the
row: one source list can hold the same URL twice on the same axis (69 pairs today), and each
of those pairs is a re-verification recording a different claim or a different date. They are
two observations, and the key is what tells them apart. `_disambiguate` remains as a last
resort for a future corpus and fires on nothing today, which a test asserts against the real
payload — if it ever did fire it would number by position, and a deleted row would hand its id
to its surviving twin.

## The ordinal the id used to carry now has its own column

`layers.id`, `categories.id`, `stages.id` and `long_tail_top.id` were positions, and each of
those positions carried something: the layer stack order, the map's curated category order,
the long tail's ranking, and — most sharply — the stage number, because `categories.stage`
was literally the number and `stages.id` was literally the number it pointed at. A hashed id
carries none of that.

The designers' model has nowhere else to put it. `layers` is `{id, label}`, `stages` is
`{id, label, desc}`, `long_tail_top` has no ordering field, and `stages` has no number, so
`label` is a display name and the `descriptions.stages` legend keys on a number the table
would no longer hold. Drop the information and a consumer cannot render the stack bottom-up,
cannot reproduce the curated order, cannot rank the tail, and cannot say which stage "Stage 3"
is. So it moved into `layers.sort_order`, `categories.sort_order`, `long_tail_top.sort_order`
and `stages.num`. `ORDER BY sort_order` is what the old `ORDER BY id` meant.

Four columns the designers' model does not declare, and nothing reads Neon today — the front
end still consumes `notebook_data.json`. This is preservation for the consumer that comes
next, because a publish that drops the information destroys it, and the cost of carrying it is
four integers per row.

## The constraints are real, and a violation fails the run

Every `[pk]`, `[not null]`, `[unique]` and `ref:` the DBML declares is emitted in the CREATE
statement, so the database enforces them rather than the site discovering a dangling id at
render time. `categories.slug` gets a UNIQUE the DBML does not declare, because the column
itself is an amendment and a duplicate slug would break the deep links it exists for.

That makes a COPY the integrity gate: a NULL in a `[not null]` column, a duplicate key or an
unresolvable reference aborts the load, the staging schema is discarded and the live schema
stays exactly where it was. Failing there is the point — the alternative is a serving layer
that answers with a foreign key pointing at nothing.

`SITE_TABLES` is therefore ordered parents-first: every table's referents are created and
filled before it is. `tests/test_publish_neon.py` asserts that order against the declared
references rather than trusting the dict's shape.

## Enums are enforced, never coerced

The five enums are created in the schema and the payload's values are mapped onto them by
`ENUM_MAPS`. A value with no mapping raises `UnmappedValue` and fails the load naming the
value and the column — a serving layer that silently coerced an unknown vocabulary item to
something adjacent would be worse than one that stopped.

The DBML declares eight. `health_status`, `integration_type` and `gap_type` belong to the
gallery tables, which are not here (see "What the CMS owns" below), so the types are not
created either: an enum no column can reference is dead metadata, and one created *here*
would be worse than dead, because a CMS table referencing it would acquire a dependency on a
schema this publisher renames out from under it on every load. The vocabulary stays declared
in the DBML, which is the contract with the designers.

One mapping is lossy and worth knowing about. `capability.relation` in the payload is
`at` / `one_above` / `one_below` / `two_below`, a signed distance; the target enum is
`peer` / `tier_above` / `tier_below` / `anchor`, which has no distance. So `one_below` and
`two_below` both arrive as `tier_below`, and the exact distance is only in
`capability.notes`. `anchor` is in the enum and unused by the payload.

## The three dates, which are three different questions

| Where | Column | Question it answers |
|---|---|---|
| `publish_runs` | `built_at` | When was this data built? The payload's `generated`. |
| `publish_runs` | `released_at` | When was the release cut? The payload's `released`, which `build/serialize.py::release_date` reads from `CHANGELOG.md`. |
| `products` | `freshness_date`, `freshness_basis` | When was this product's score last confirmed, and how? |
| `openness` / `adoption` / `capability` | `last_verified` | Same question asked of one axis. |

`docs/reference/evidence-and-freshness.md` is normative for what a freshness date means and how it is
derived. `basis` is `verified` when a human confirmed the axis and `commit` when the date
falls back to the score file's last commit.

## Migrations: the swap is the migration

There is no migration tool and no need for one yet. Every publish rebuilds the schema from
this module and swaps it into place atomically, so a shape change here becomes live on the
next load with no ALTER anywhere. What that costs is a reader's ability to tell which shape
it is looking at, so `publish_runs.schema_version` carries `SCHEMA_VERSION` — bump it in the
same commit as any change to a table, column, constraint or enum here. Once something outside this
repo depends on the shape, this is the point where a real migration path replaces the swap.

## What the CMS owns, and why it cannot live here

The DBML's `gallery`, `gallery_products` and `gallery_gaps` are **not** in this module. They
were, created and left empty so the site's queries would compile, and that was a hazard
rather than a courtesy: this publisher drops and recreates its schema on every load, so the
first gallery row an editor wrote would be deleted by the next push to `main` with nothing
raising anywhere. `--check` would still print `gallery 0 rows` and the read-back would still
report `| gallery | 0 |`, so the loss was invisible in every artifact the publish produced.

A schema rebuilt from source can only hold rows it produced. Gallery content is authored, so
it belongs either in the CMS's own `payload` schema or in a separate `os-ai-map_cms` schema —
which this publisher never creates, never drops and never grants on. The site joins across
schemas; both are on the same database, so that costs a qualified name and nothing else.

Note for whoever builds it: a **view** in that schema over a table in `os-ai-map` will not
survive, because the cutover renames the schema and a view binds to the table it was created
over by OID, not by name. `publish_neon.reclaim_previous` detects exactly that dependency and
refuses to run rather than dropping the view — so the failure is loud, but it is still a
failure. Read the map's tables directly, or materialize a copy on the CMS side.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from build.vocabulary import axes

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = ROOT / "build" / "notebook_data.json"

# Bump on any change to a table, column, constraint or enum here. Recorded on every
# publish_runs row.
#   1: the initial load.
#   2: the gallery tables and their three enums removed (CMS-owned); the DBML's primary keys,
#      NOT NULLs, uniques and foreign keys emitted for the first time.
#   3: the `registry_*` tables dropped from the load — nothing on the site read them and the
#      registry surface lives in the warehouse. Every surrogate id derived from the row's
#      natural key by `stable_id` instead of from its position, so ids no longer renumber
#      when the corpus grows; id and foreign-key columns widened from INTEGER to BIGINT to
#      hold them; the ordinal those ids used to carry moved into `layers.sort_order`,
#      `categories.sort_order`, `long_tail_top.sort_order` and `stages.num`.
SCHEMA_VERSION = 3

class UnmappedValue(ValueError):
    """A payload value with no place in the target enum. Fails the load, names the value."""


class IdCollision(RuntimeError):
    """Two different natural keys hashed to the same id. Fails the load, names both."""


# --- stable ids -----------------------------------------------------------------------

# The composite natural keys (`sources`, `product_lineage`) join their parts with this. The
# join is unambiguous because each key puts its controlled values first and leaves at most one
# unbounded component last, not because the separator is unusual — see `_source_key`.
KEY_SEPARATOR = "|"


def stable_id(table: str, key: str) -> int:
    """A surrogate id for a row, derived from its natural key rather than its position.

    The first 63 bits of `sha256("<table>:<key>")`, as a positive integer. Two properties,
    and the function exists for both:

    1. **Stable across loads.** The same table and key always give the same id, so adding or
       removing a row renumbers nothing else. An id that has escaped into a URL, a cache or a
       CMS reference still points at the same row after the next publish, which an id
       assigned by position did not.
    2. **Scoped to the table.** The table name is hashed in, so the same slug in two tables
       gets two different ids. A join that crosses tables by mistake matches nothing instead
       of appearing to work.

    63 bits rather than 64 because Postgres has no unsigned integer type and the columns are
    `BIGINT`: keeping the top bit would make half the ids negative. 63 bits over a few
    thousand rows per table leaves a collision probability far below any other failure mode
    here, and `_id_map` fails the load rather than trusting that.
    """
    digest = hashlib.sha256(f"{table}:{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") >> 1


def _id_map(table: str, keys: Iterable[str]) -> dict[str, int]:
    """natural key -> id for one table, refusing a collision rather than losing a row.

    A duplicate key is fine and collapses (the callers pass keys that are unique by
    construction); two *different* keys landing on the same id is not, because the table's
    primary key would reject one of them at COPY time with a message naming neither.
    """
    out: dict[str, int] = {}
    by_id: dict[int, str] = {}
    for key in keys:
        ident = stable_id(table, key)
        clash = by_id.get(ident)
        if clash is not None and clash != key:
            raise IdCollision(
                f"{table}: {key!r} and {clash!r} both hash to id {ident}. Two natural keys "
                f"cannot share a surrogate id, so this publish has stopped rather than drop "
                f"one of them. Change one of the keys, or widen stable_id."
            )
        by_id[ident] = key
        out[key] = ident
    return out


def _disambiguate(keys: Iterable[str]) -> list[str]:
    """Append `#2`, `#3` to a key that repeats. A last resort that should never fire.

    It numbers by walk position, so if it ever does fire it carries the bug the natural keys
    exist to avoid: delete the earlier of a repeated pair and the later one is promoted into
    the un-suffixed key, **inheriting the deleted row's id**. A stored reference then resolves
    to a different row with no gate firing, which is worse than the positional scheme this
    module replaced, because that one renumbered visibly and en masse.

    So the keys handed to it must already be unique. `sources` is the only caller and its key
    includes `shows` and `accessed`, under which no two rows in the corpus collide —
    `tests/test_publish_neon.py` asserts that on the real payload. This stays as a guard
    against a future corpus, not as a working part of the scheme.
    """
    seen: dict[str, int] = {}
    out = []
    for key in keys:
        seen[key] = seen.get(key, 0) + 1
        out.append(key if seen[key] == 1 else f"{key}#{seen[key]}")
    return out


_PRIMARY_KEY = re.compile(r'PRIMARY KEY \(([^)]*)\)')


def primary_key(table: str) -> tuple[str, ...]:
    """The columns in a table's declared PRIMARY KEY, or `()` where it declares none.

    Read from the constraint the DDL actually emits rather than restated, so a key that moves
    moves this too. `gaps_categories` and `long_tail_counts` have no key in the DBML and none
    to invent, so they come back empty.
    """
    for clause in SITE_TABLES[table].constraints:
        match = _PRIMARY_KEY.match(clause)
        if match:
            return tuple(part.strip().strip('"') for part in match.group(1).split(","))
    return ()


def check_ids_unique(tables: dict[str, list[dict]]) -> None:
    """Fail the publish if any table repeats its primary key. The last gate before COPY.

    Keyed off each table's declared PRIMARY KEY rather than off a column literally named
    `id`, so it also covers the four whose key is `product_id`, `slug` or `alias`. The two
    tables the DBML gives no key are the two it skips, and nothing else is exempt.

    `_id_map` catches a collision where both natural keys are in hand, which is the case that
    can name them. This is the backstop for every other way a duplicate could reach a table —
    a builder that stopped going through `_id_map`, a key computed twice from different
    fields — and it runs over the rows that are actually about to be written.
    """
    for name, rows in tables.items():
        key_columns = primary_key(name)
        if not key_columns:
            continue
        seen: dict[tuple, dict] = {}
        for row in rows:
            key = tuple(row.get(column) for column in key_columns)
            first = seen.get(key)
            if first is not None:
                shown = key[0] if len(key) == 1 else key
                raise IdCollision(
                    f"{name}: primary key {shown!r} is used by two rows, {first!r} and "
                    f"{row!r}. Postgres would reject one of them at COPY time; this publish "
                    f"has stopped instead."
                )
            seen[key] = row


# --- enums ----------------------------------------------------------------------------

# The DBML's `health_status`, `integration_type` and `gap_type` are absent on purpose: they
# belong to the gallery tables, which the CMS owns. See the module docstring.
ENUMS: dict[str, tuple[str, ...]] = {
    "alias_kind": ("product", "organization"),
    "freshness_basis": ("commit", "verified"),
    "lineage_relation": ("derived_from", "curated_with", "trains"),
    "capability_relation": ("tier_below", "tier_above", "peer", "anchor"),
    # The three scored axes, from the score schema rather than restated here — a fourth axis
    # must not reach a serving layer whose enum silently rejects it.
    "metric_name": axes(),
}

# Payload vocabulary -> enum value, per enum. Identity where the two already agree; spelled
# out anyway so a new payload value is a KeyError here rather than a silent pass-through.
ENUM_MAPS: dict[str, dict[str, str]] = {
    "alias_kind": {"products": "product", "organizations": "organization"},
    "freshness_basis": {"verified": "verified", "commit": "commit"},
    "lineage_relation": {
        "derived_from": "derived_from",
        "curated_with": "curated_with",
        "trains": "trains",
    },
    # Lossy by construction: the payload carries a signed distance and the enum does not.
    # See the module docstring.
    "capability_relation": {
        "at": "peer",
        "one_above": "tier_above",
        "one_below": "tier_below",
        "two_below": "tier_below",
        "anchor": "anchor",
    },
    "metric_name": {axis: axis for axis in axes()},
}


def enum_value(enum: str, value, *, column: str) -> str | None:
    """Map a payload value onto its enum, or fail naming the value and the column."""
    if value in (None, ""):
        return None
    mapping = ENUM_MAPS.get(enum)
    if mapping is None:
        raise UnmappedValue(f"{column}: enum {enum!r} has no payload mapping at all")
    if value not in mapping:
        raise UnmappedValue(
            f"{column}: {value!r} is not a value of enum {enum} "
            f"(known: {', '.join(sorted(mapping))}). Add a mapping in build/neon_schema.py "
            f"or extend the enum; the load will not coerce it."
        )
    return mapping[value]


def enum_type(name: str) -> str:
    """A column type naming an enum in whichever schema is being built.

    `{schema}` is substituted at DDL time by `publish_neon.create_table_sql`. Enum types are
    schema-scoped, so they are created inside the staging schema and travel with the rename;
    that also means a column referencing one must qualify it, since the staging schema is
    not on the search path.
    """
    if name not in ENUMS:
        raise KeyError(f"no such enum: {name}")
    return '{schema}."' + name + '"'


# --- helpers --------------------------------------------------------------------------


def references(column: str, table: str, target: str) -> str:
    """A table-level FOREIGN KEY clause. `{schema}` is filled in at DDL time.

    Qualified with the schema being built, because the staging schema is never on the search
    path — the same reason `enum_type` qualifies an enum.
    """
    return (
        f'FOREIGN KEY ("{column}") REFERENCES {{schema}}."{table}" ("{target}")'
    )


@dataclass(frozen=True)
class SiteTable:
    """One table: its columns, its table-level constraints, and its rows.

    A column's second element is its full definition after the name, so it carries `NOT NULL`
    where the DBML declares one — Postgres has no table-level form of it. Keys, uniques and
    foreign keys are table-level and live in `constraints`, which reads closer to the DBML
    than an inline `[pk]` would and keeps composite cases expressible.
    """

    columns: tuple[tuple[str, str], ...]
    rows: Callable[[dict], list[dict]]
    constraints: tuple[str, ...] = ()

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(name for name, _type in self.columns)


def load_payload(path: Path = PAYLOAD_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _axis(row: dict, axis: str) -> dict:
    value = row.get(axis)
    return value if isinstance(value, dict) else {}


def _pg_array(values) -> str:
    """A Postgres array literal for a `varchar[]` column, every element quoted.

    Quoted unconditionally rather than only when it contains a delimiter: a URL with a comma
    in it is rare enough to be exactly the case nobody tests.
    """
    if not values:
        return "{}"
    if isinstance(values, str):
        values = [values]
    inner = ",".join('"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"' for v in values)
    return "{" + inner + "}"


def product_ids(payload: dict) -> dict[str, int]:
    """slug -> id, hashed from the slug so adding a product renumbers nothing."""
    slugs = sorted(
        {p["slug"] for cid in payload.get("order") or [] for p in payload["categories"][cid]["products"]}
    )
    return _id_map("products", slugs)


def category_ids(payload: dict) -> dict[str, int]:
    """slug -> id. The curated `order` decides `categories.sort_order`, not the id."""
    return _id_map("categories", payload.get("order") or [])


def category_order(payload: dict) -> dict[str, int]:
    """slug -> position in the map's own curated order, 1-based."""
    return {cid: index for index, cid in enumerate(payload.get("order") or [], start=1)}


def layer_ids(payload: dict) -> dict[str, int]:
    return _id_map("layers", payload.get("layer_order") or [])


def layer_order(payload: dict) -> dict[str, int]:
    """label -> position in the stack, bottom first, 1-based."""
    return {layer: index for index, layer in enumerate(payload.get("layer_order") or [], start=1)}


def gap_ids(payload: dict) -> dict[str, int]:
    """Gap kind -> id, over the legend rather than over what categories happen to carry.

    A gap kind that no category currently has is still a kind the site renders a label for.
    """
    legend = (payload.get("descriptions") or {}).get("gaps") or {}
    return _id_map("gaps", sorted(legend))


def stage_ids() -> dict[int, int]:
    """Stage number -> id. The number itself stays readable in `stages.num`."""
    from build.serialize import _STAGE_NAMES

    by_key = _id_map("stages", [str(num) for num in sorted(_STAGE_NAMES)])
    return {num: by_key[str(num)] for num in sorted(_STAGE_NAMES)}


def _walk_products(payload: dict):
    """(category_slug, product) over the curated order — the payload's own iteration."""
    for cid in payload.get("order") or []:
        for product in payload["categories"][cid]["products"]:
            yield cid, product


def _by_slug(payload: dict) -> list[tuple[str, str, dict]]:
    """(slug, category_slug, product), sorted by slug. The deterministic walk for ids."""
    rows = [(product["slug"], cid, product) for cid, product in _walk_products(payload)]
    rows.sort(key=lambda row: row[0])
    return rows


# --- row builders -------------------------------------------------------------


def _products(payload: dict) -> list[dict]:
    ids = product_ids(payload)
    cats = category_ids(payload)
    seen: set[str] = set()
    out = []
    for slug, cid, product in _by_slug(payload):
        if slug in seen:
            # `products.category` is a single FK, so a product in two categories has no
            # representation in this model. The payload has none today; if one appears it is
            # a schema question, not something to resolve by picking a category.
            raise UnmappedValue(
                f"product {slug!r} appears in more than one category, which "
                f"products.category (a single FK) cannot represent"
            )
        seen.add(slug)
        org_slug = product.get("org_slug") or ""
        if not org_slug:
            # `products.org_slug` is NOT NULL and references `organizations`. Writing "" here
            # sent an empty string into COPY, which CSV reads as NULL, so the load died on a
            # constraint naming the column and not the row — leaving whoever hit it to find
            # which of 615 products was missing an org. The payload's own gates should catch
            # this first; if one slips through, it slips through named.
            raise UnmappedValue(
                f"product {slug!r} has no org_slug, which products.org_slug (NOT NULL, "
                f"referencing organizations.slug) cannot represent. Give the product an "
                f"organization in sources/, or the load will refuse it."
            )
        freshness = _axis(product, "freshness")
        out.append(
            {
                "id": ids[slug],
                "slug": slug,
                "org_slug": org_slug,
                "name": product.get("product") or "",
                "org": product.get("org") or "",
                "type": product.get("type") or "",
                "category": cats[cid],
                "description": product.get("description") or "",
                # The payload ships `overall_score` and `maturity` as the same number under
                # two names during the rename; the target model has one column.
                "maturity": product.get("overall_score", product.get("maturity")),
                "mature": product.get("mature"),
                "version_note": product.get("version_note") or "",
                "freshness_date": freshness.get("date") or "",
                "freshness_basis": enum_value(
                    "freshness_basis", freshness.get("basis"), column="products.freshness_basis"
                ),
            }
        )
    return out


def _organizations(payload: dict) -> list[dict]:
    return [
        {
            "slug": slug,
            "display_name": org.get("display_name") or "",
            "type": org.get("type") or "",
            "homepage": org.get("homepage") or "",
            "github": _pg_array(org.get("github")),
            "country": org.get("country") or "",
        }
        for slug, org in sorted((payload.get("organizations") or {}).items())
    ]


def _aliases(payload: dict) -> list[dict]:
    out = []
    for group, entries in sorted((payload.get("aliases") or {}).items()):
        kind = enum_value("alias_kind", group, column="aliases.kind")
        for alias, canonical in sorted((entries or {}).items()):
            out.append({"alias": alias, "kind": kind, "canonical": canonical})
    return out


def _openness(payload: dict) -> list[dict]:
    ids = product_ids(payload)
    out = []
    for slug, _cid, product in _by_slug(payload):
        axis = _axis(product, "openness")
        out.append(
            {
                "product_id": ids[slug],
                "score": axis.get("score"),
                "class": axis.get("class") or "",
                "components": axis.get("components") or "",
                "confidence": axis.get("confidence") or "",
                "notes": axis.get("note") or "",
                "bucket": axis.get("bucket") or "",
                "last_verified": axis.get("last_verified") or "",
                "governing_release": axis.get("governing_release") or "",
            }
        )
    return out


def _adoption(payload: dict) -> list[dict]:
    ids = product_ids(payload)
    out = []
    for slug, _cid, product in _by_slug(payload):
        axis = _axis(product, "adoption")
        out.append(
            {
                "product_id": ids[slug],
                "level": axis.get("level"),
                "reach": axis.get("reach") or "",
                "signal_type": axis.get("signal_type") or "",
                "confidence": axis.get("confidence") or "",
                "notes": axis.get("note") or "",
                "last_verified": axis.get("last_verified") or "",
            }
        )
    return out


def _capability(payload: dict) -> list[dict]:
    ids = product_ids(payload)
    out = []
    for slug, _cid, product in _by_slug(payload):
        axis = _axis(product, "capability")
        out.append(
            {
                "product_id": ids[slug],
                "score": axis.get("score"),
                "basis": axis.get("basis") or "",
                "basis_detail": axis.get("basis_detail") or "",
                "value": axis.get("value") or "",
                "confidence": axis.get("confidence") or "",
                "notes": axis.get("note") or "",
                "last_verified": axis.get("last_verified") or "",
                "relative_to": axis.get("relative_to") or "",
                "relation": enum_value(
                    "capability_relation", axis.get("relation"), column="capability.relation"
                ),
            }
        )
    return out


def _source_key(slug: str, metric: str, source: dict) -> str:
    """`(product_slug, metric, url, shows, accessed)` — the natural key of one source row.

    The URL alone does not identify the row. A product's source list can carry the same URL
    twice on the same axis (69 pairs today), and every one of those pairs is a
    re-verification: the same page read on a different date, or recorded as showing something
    different. They are two observations, not one row duplicated, so the key has to carry what
    tells them apart.

    Keying on the URL alone and numbering the repeats would mean that deleting the earlier of
    a pair promoted the later one into the un-suffixed key and handed it the deleted row's id.
    Anything holding the old id would then resolve to a row with a different claim and a
    different date, with no gate firing — the exact failure the hashed ids exist to prevent.

    Two consequences, both intended. Editing a source's `shows` or `accessed` moves that row's
    id, because it is a different observation of the same URL and the module's rule is that an
    id moves when its natural key does. And the key is order-independent: reordering a source
    list, or deleting a sibling, leaves every other row's id alone.

    The parts are joined slug, metric, accessed, url, shows: the three controlled values
    first, then the free text, with the only genuinely unbounded one (`shows`, which holds
    prose) last. That ordering is what makes the joined string unambiguous, rather than any
    property of the separator — a `|` inside `shows` cannot shift a boundary, because there is
    nothing after it.
    """
    return KEY_SEPARATOR.join(
        (
            slug,
            metric,
            source.get("accessed") or "",
            source.get("url") or "",
            source.get("shows") or "",
        )
    )


def _sources(payload: dict) -> list[dict]:
    """Every source on every axis, one row each, in the deterministic walk order.

    The target model has a `notes` column the payload has no field for; the payload's
    `establishes`, `content_sha256` and `http_status` have no column. `shows` is the one that
    maps, and `notes` stays NULL rather than being filled with an adjacent field.

    The grain is one *observation*, which is why the key carries `shows` and `accessed`: see
    `_source_key`.
    """
    ids = product_ids(payload)
    walked: list[tuple[str, str, dict]] = []
    for slug, _cid, product in _by_slug(payload):
        for metric in axes():
            for source in _axis(product, metric).get("sources") or []:
                if isinstance(source, dict):
                    walked.append((slug, metric, source))
    keys = _disambiguate(_source_key(slug, metric, source) for slug, metric, source in walked)
    source_ids = _id_map("sources", keys)

    out = []
    for key, (slug, metric, source) in zip(keys, walked, strict=True):
        out.append(
            {
                "id": source_ids[key],
                "url": source.get("url") or "",
                "shows": source.get("shows") or "",
                "notes": "",
                "accessed": source.get("accessed") or "",
                "product_id": ids[slug],
                "metric_type": enum_value("metric_name", metric, column="sources.metric_type"),
            }
        )
    return out


def _product_lineage(payload: dict) -> list[dict]:
    """One row per edge, keyed by `(product_slug, relation, target)` — the edge itself."""
    ids = product_ids(payload)
    walked: list[tuple[str, str, str, str]] = []
    for slug, _cid, product in _by_slug(payload):
        lineage = product.get("lineage")
        if not isinstance(lineage, dict):
            continue
        for relation, targets in lineage.items():
            mapped = enum_value("lineage_relation", relation, column="product_lineage.relation")
            for target in targets or []:
                text = target if isinstance(target, str) else str(target)
                walked.append((slug, relation, mapped, text))
    keys = _disambiguate(
        KEY_SEPARATOR.join((slug, relation, target)) for slug, relation, _mapped, target in walked
    )
    edge_ids = _id_map("product_lineage", keys)
    return [
        {
            "id": edge_ids[key],
            "product_id": ids[slug],
            "relation": mapped,
            "target": target,
        }
        for key, (slug, _relation, mapped, target) in zip(keys, walked, strict=True)
    ]


def _categories(payload: dict) -> list[dict]:
    cats = category_ids(payload)
    order = category_order(payload)
    layers = layer_ids(payload)
    stages = stage_ids()
    legend = (payload.get("descriptions") or {}).get("categories") or {}
    out = []
    for cid, ident in cats.items():
        category = payload["categories"][cid]
        layer = category.get("layer") or ""
        if layer not in layers:
            raise UnmappedValue(
                f"category {cid!r} names layer {layer!r}, which is not in layer_order"
            )
        stage_num = (category.get("stage") or {}).get("num")
        if stage_num not in stages:
            raise UnmappedValue(
                f"category {cid!r} is at stage {stage_num!r}, which is not a stage on the "
                f"ladder; categories.stage is NOT NULL and references stages.id"
            )
        out.append(
            {
                "id": ident,
                # Not in the PDF. Added because every deep link is by slug, and the id it
                # sits beside is a hash rather than something a person can read or guess.
                "slug": cid,
                "sort_order": order[cid],
                "label": category.get("label") or "",
                "arc": category.get("arc") or "",
                "layer": layers[layer],
                "description": legend.get(cid) or "",
                "stage": stages[stage_num],
            }
        )
    return out


def _layers(payload: dict) -> list[dict]:
    ids = layer_ids(payload)
    order = layer_order(payload)
    return [{"id": ident, "sort_order": order[layer], "label": layer} for layer, ident in ids.items()]


def _stages(payload: dict) -> list[dict]:
    """The stage ladder. Names and descriptions are methodology constants.

    `num` is the stage number the whole methodology speaks in ("Stage 3"), which used to be
    the id. It is a column of its own now that the id is a hash.
    """
    from build.serialize import _STAGE_NAMES

    ids = stage_ids()
    legend = (payload.get("descriptions") or {}).get("stages") or {}
    return [
        {"id": ids[num], "num": num, "label": name, "desc": legend.get(str(num)) or ""}
        for num, name in sorted(_STAGE_NAMES.items())
    ]


def _gaps(payload: dict) -> list[dict]:
    legend = (payload.get("descriptions") or {}).get("gaps") or {}
    return [
        {"id": ident, "label": kind, "desc": legend.get(kind) or ""}
        for kind, ident in gap_ids(payload).items()
    ]


def _gaps_categories(payload: dict) -> list[dict]:
    cats = category_ids(payload)
    gaps = gap_ids(payload)
    out = []
    for cid, ident in cats.items():
        for kind in payload["categories"][cid].get("gaps") or []:
            if kind not in gaps:
                raise UnmappedValue(
                    f"category {cid!r} carries gap {kind!r}, which the payload's gap legend "
                    f"does not describe"
                )
            out.append({"cat_id": ident, "gap_id": gaps[kind]})
    return out


def _long_tail_top(payload: dict) -> list[dict]:
    top = (payload.get("long_tail") or {}).get("top") or []
    ids = _id_map("long_tail_top", [row.get("name") or "" for row in top])
    return [
        {
            "id": ids[row.get("name") or ""],
            "sort_order": index,
            "name": row.get("name") or "",
            "type": row.get("type") or "",
            "usage_label": row.get("usage_label") or "",
            "description": row.get("description") or "",
        }
        for index, row in enumerate(top, start=1)
    ]


def _long_tail_counts(payload: dict) -> list[dict]:
    counts = (payload.get("long_tail") or {}).get("counts") or {}
    return [{"count": value, "type": key} for key, value in sorted(counts.items())]


# --- the table set ----------------------------------------------------------------

SITE_TABLES: dict[str, SiteTable] = {
    "layers": SiteTable(
        # `sort_order` is the stack position the id used to be, bottom first. Not in the
        # designers' model; added when the id became a hash and stopped carrying it.
        (("id", "BIGINT"), ("sort_order", "INTEGER NOT NULL"), ("label", "VARCHAR")),
        _layers,
        constraints=('PRIMARY KEY ("id")',),
    ),
    "stages": SiteTable(
        # `num` is the stage number the methodology speaks in, 0-5, which used to be the id.
        (
            ("id", "BIGINT"),
            ("num", "INTEGER NOT NULL"),
            ("label", "VARCHAR"),
            ("desc", "TEXT"),
        ),
        _stages,
        constraints=('PRIMARY KEY ("id")', 'UNIQUE ("num")'),
    ),
    "gaps": SiteTable(
        (("id", "BIGINT"), ("label", "VARCHAR"), ("desc", "TEXT")),
        _gaps,
        constraints=('PRIMARY KEY ("id")',),
    ),
    "categories": SiteTable(
        (
            ("id", "BIGINT"),
            # The map's curated order, which the id used to carry. `ORDER BY sort_order` is
            # what `ORDER BY id` used to mean.
            ("sort_order", "INTEGER NOT NULL"),
            # NOT NULL as well as UNIQUE: a nullable unique column admits any number of
            # NULLs, which would defeat the deep links the amendment exists for.
            ("slug", "VARCHAR NOT NULL"),
            ("label", "VARCHAR"),
            ("arc", "VARCHAR"),
            ("layer", "BIGINT NOT NULL"),
            ("description", "TEXT"),
            ("stage", "BIGINT NOT NULL"),
        ),
        _categories,
        constraints=(
            'PRIMARY KEY ("id")',
            'UNIQUE ("slug")',
            references("layer", "layers", "id"),
            references("stage", "stages", "id"),
        ),
    ),
    "gaps_categories": SiteTable(
        (("cat_id", "BIGINT NOT NULL"), ("gap_id", "BIGINT NOT NULL")),
        _gaps_categories,
        constraints=(
            references("cat_id", "categories", "id"),
            references("gap_id", "gaps", "id"),
        ),
    ),
    "organizations": SiteTable(
        (
            ("slug", "VARCHAR"),
            ("display_name", "VARCHAR"),
            ("type", "VARCHAR"),
            ("homepage", "VARCHAR"),
            ("github", "VARCHAR[]"),
            ("country", "VARCHAR"),
        ),
        _organizations,
        constraints=('PRIMARY KEY ("slug")',),
    ),
    "products": SiteTable(
        (
            ("id", "BIGINT"),
            ("slug", "VARCHAR NOT NULL"),
            ("org_slug", "VARCHAR NOT NULL"),
            ("name", "VARCHAR"),
            ("org", "VARCHAR"),
            ("type", "VARCHAR"),
            ("category", "BIGINT NOT NULL"),
            ("description", "TEXT"),
            ("maturity", "REAL"),
            ("mature", "BOOLEAN"),
            ("version_note", "TEXT"),
            ("freshness_date", "DATE"),
            ("freshness_basis", enum_type("freshness_basis")),
        ),
        _products,
        constraints=(
            'PRIMARY KEY ("id")',
            'UNIQUE ("slug")',
            references("org_slug", "organizations", "slug"),
            references("category", "categories", "id"),
        ),
    ),
    "openness": SiteTable(
        (
            ("product_id", "BIGINT"),
            ("score", "INTEGER"),
            ("class", "VARCHAR"),
            ("components", "TEXT"),
            ("confidence", "VARCHAR"),
            ("notes", "TEXT"),
            ("bucket", "VARCHAR"),
            ("last_verified", "DATE"),
            ("governing_release", "VARCHAR"),
        ),
        _openness,
        # `ref: -` in the DBML: one row per product, so the FK column is also the key.
        constraints=('PRIMARY KEY ("product_id")', references("product_id", "products", "id")),
    ),
    "adoption": SiteTable(
        (
            ("product_id", "BIGINT"),
            ("level", "INTEGER"),
            ("reach", "VARCHAR"),
            ("signal_type", "VARCHAR"),
            ("confidence", "VARCHAR"),
            ("notes", "TEXT"),
            ("last_verified", "DATE"),
        ),
        _adoption,
        constraints=('PRIMARY KEY ("product_id")', references("product_id", "products", "id")),
    ),
    "capability": SiteTable(
        (
            ("product_id", "BIGINT"),
            ("score", "INTEGER"),
            ("basis", "VARCHAR"),
            ("basis_detail", "TEXT"),
            ("value", "TEXT"),
            ("confidence", "VARCHAR"),
            ("notes", "TEXT"),
            ("last_verified", "DATE"),
            ("relative_to", "VARCHAR"),
            ("relation", enum_type("capability_relation")),
        ),
        _capability,
        constraints=('PRIMARY KEY ("product_id")', references("product_id", "products", "id")),
    ),
    "sources": SiteTable(
        (
            ("id", "BIGINT"),
            ("url", "TEXT"),
            ("shows", "TEXT"),
            ("notes", "TEXT"),
            ("accessed", "DATE"),
            ("product_id", "BIGINT NOT NULL"),
            ("metric_type", enum_type("metric_name") + " NOT NULL"),
        ),
        _sources,
        constraints=('PRIMARY KEY ("id")', references("product_id", "products", "id")),
    ),
    "product_lineage": SiteTable(
        (
            ("id", "BIGINT"),
            ("product_id", "BIGINT NOT NULL"),
            ("relation", enum_type("lineage_relation")),
            ("target", "VARCHAR"),
        ),
        _product_lineage,
        constraints=('PRIMARY KEY ("id")', references("product_id", "products", "id")),
    ),
    "aliases": SiteTable(
        (("alias", "VARCHAR"), ("kind", enum_type("alias_kind")), ("canonical", "VARCHAR")),
        _aliases,
        constraints=('PRIMARY KEY ("alias")',),
    ),
    "long_tail_top": SiteTable(
        (
            ("id", "BIGINT"),
            # The ranking the id used to carry.
            ("sort_order", "INTEGER NOT NULL"),
            ("name", "VARCHAR"),
            ("type", "VARCHAR"),
            ("usage_label", "VARCHAR"),
            ("description", "TEXT"),
        ),
        _long_tail_top,
        constraints=('PRIMARY KEY ("id")',),
    ),
    # No key in the DBML, and none to invent: the grain is one row per product type.
    "long_tail_counts": SiteTable(
        (("count", "INTEGER"), ("type", "VARCHAR")), _long_tail_counts
    ),
}

def build_site_tables(payload: dict) -> dict[str, list[dict]]:
    """Every table's rows, keyed by table name, with its ids checked for collisions."""
    tables = {name: spec.rows(payload) for name, spec in SITE_TABLES.items()}
    check_ids_unique(tables)
    return tables


def write_site_csvs(payload: dict, out_dir: Path) -> None:
    """Write one CSV per table, so everything reaches Postgres through one COPY path.

    Rendering to CSV rather than inserting row by row means there is one type story and one
    place a quoting bug could live, and it reuses the serializers' writer.
    """
    from build.serialize_registry import write_tables

    spec = {name: table.column_names for name, table in SITE_TABLES.items()}
    write_tables(build_site_tables(payload), out_dir, spec=spec)
