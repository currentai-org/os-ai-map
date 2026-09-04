"""What the Neon serving layer holds — the one place to change the table set.

`build/publish_neon.py` is a generic CSV-to-Postgres loader with an atomic schema swap. It
knows nothing about the gap map. This module is the map half: which tables exist, which
enums, what every column is, and where each row comes from.

Group B is the designers' target model, transcribed in
`Current-AI-Initial-Schema.pdf` (Laith, CLEVER FRANKE) with Carl's amendments. This load
exists to deprecate `build/notebook_data.json` as the site's transport, so every group-B row
is derived from that payload's semantics — the same content the front end reads today, at a
grain a query can use. Rows come from the file rather than from a fresh `build_payload`
because it is the repo's build artifact and its gate contract: what Postgres serves is
byte-for-byte what the repo published, not a second derivation that could disagree with it.

Group A is the registry surface: exactly `build.publish_registry.TABLES`, the four
serializers' declared sets, read from that module rather than from a glob over
`build/registry/`, so Neon and the OSO warehouse carry the same tables by construction.
Group A names are prefixed `registry_` in Postgres, because both groups share one schema and
both have a `products`, a `categories` and an `organizations`.

## Keys are natural where the payload has one

`products.id` exists for the FK shape the designers specified, but it is assigned by sorted
slug order on every load, so the same corpus produces the same ids and a diff of two loads
is readable. The real key is `slug`, which is what a deep link carries. Organizations key on
`slug`, aliases on `alias`, categories carry a `slug` alongside their id (the PDF omitted it
and the site needs it). Ids for `sources` and `product_lineage` are positional over a
deterministic walk, for the same reason.

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
same commit as any change to a group-B table, column, or enum. Once something outside this
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

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from build.publish_registry import TABLES as REGISTRY_TABLES
from build.vocabulary import axes

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = ROOT / "build" / "notebook_data.json"

# Bump on any change to a group-B table, column, constraint or enum. Recorded on every
# publish_runs row.
#   1: the initial load.
#   2: the gallery tables and their three enums removed (CMS-owned); the DBML's primary keys,
#      NOT NULLs, uniques and foreign keys emitted for the first time.
SCHEMA_VERSION = 2

# Group A's tables keep their serializer names, prefixed, because both groups share a schema.
REGISTRY_PREFIX = "registry_"


class UnmappedValue(ValueError):
    """A payload value with no place in the target enum. Fails the load, names the value."""


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
    """One group-B table: its columns, its table-level constraints, and its rows.

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
    """slug -> id, assigned by sorted slug so a load is reproducible and a diff is readable."""
    slugs = sorted(
        {p["slug"] for cid in payload.get("order") or [] for p in payload["categories"][cid]["products"]}
    )
    return {slug: index for index, slug in enumerate(slugs, start=1)}


def category_ids(payload: dict) -> dict[str, int]:
    """slug -> id, in the map's own curated `order`."""
    return {cid: index for index, cid in enumerate(payload.get("order") or [], start=1)}


def layer_ids(payload: dict) -> dict[str, int]:
    return {layer: index for index, layer in enumerate(payload.get("layer_order") or [], start=1)}


def gap_ids(payload: dict) -> dict[str, int]:
    """Gap kind -> id, over the legend rather than over what categories happen to carry.

    A gap kind that no category currently has is still a kind the site renders a label for.
    """
    legend = (payload.get("descriptions") or {}).get("gaps") or {}
    return {kind: index for index, kind in enumerate(sorted(legend), start=1)}


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


# --- group B row builders -------------------------------------------------------------


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


def _sources(payload: dict) -> list[dict]:
    """Every source on every axis, one row each, in the deterministic walk order.

    The target model has a `notes` column the payload has no field for; the payload's
    `establishes`, `content_sha256` and `http_status` have no column. `shows` is the one that
    maps, and `notes` stays NULL rather than being filled with an adjacent field.
    """
    ids = product_ids(payload)
    out = []
    next_id = 1
    for slug, _cid, product in _by_slug(payload):
        for metric in axes():
            for source in _axis(product, metric).get("sources") or []:
                if not isinstance(source, dict):
                    continue
                out.append(
                    {
                        "id": next_id,
                        "url": source.get("url") or "",
                        "shows": source.get("shows") or "",
                        "notes": "",
                        "accessed": source.get("accessed") or "",
                        "product_id": ids[slug],
                        "metric_type": enum_value(
                            "metric_name", metric, column="sources.metric_type"
                        ),
                    }
                )
                next_id += 1
    return out


def _product_lineage(payload: dict) -> list[dict]:
    ids = product_ids(payload)
    out = []
    next_id = 1
    for slug, _cid, product in _by_slug(payload):
        lineage = product.get("lineage")
        if not isinstance(lineage, dict):
            continue
        for relation, targets in lineage.items():
            mapped = enum_value("lineage_relation", relation, column="product_lineage.relation")
            for target in targets or []:
                out.append(
                    {
                        "id": next_id,
                        "product_id": ids[slug],
                        "relation": mapped,
                        "target": target if isinstance(target, str) else str(target),
                    }
                )
                next_id += 1
    return out


def _categories(payload: dict) -> list[dict]:
    cats = category_ids(payload)
    layers = layer_ids(payload)
    legend = (payload.get("descriptions") or {}).get("categories") or {}
    out = []
    for cid, index in cats.items():
        category = payload["categories"][cid]
        layer = category.get("layer") or ""
        if layer not in layers:
            raise UnmappedValue(
                f"category {cid!r} names layer {layer!r}, which is not in layer_order"
            )
        out.append(
            {
                "id": index,
                # Not in the PDF. Added because every deep link and every join from the
                # registry group is by slug, and an id assigned by curated order changes
                # whenever the order does.
                "slug": cid,
                "label": category.get("label") or "",
                "arc": category.get("arc") or "",
                "layer": layers[layer],
                "description": legend.get(cid) or "",
                "stage": (category.get("stage") or {}).get("num"),
            }
        )
    return out


def _layers(payload: dict) -> list[dict]:
    return [{"id": index, "label": layer} for layer, index in layer_ids(payload).items()]


def _stages(payload: dict) -> list[dict]:
    """The stage ladder, id = stage number. Names and descriptions are methodology constants."""
    from build.serialize import _STAGE_NAMES

    legend = (payload.get("descriptions") or {}).get("stages") or {}
    return [
        {"id": num, "label": name, "desc": legend.get(str(num)) or ""}
        for num, name in sorted(_STAGE_NAMES.items())
    ]


def _gaps(payload: dict) -> list[dict]:
    legend = (payload.get("descriptions") or {}).get("gaps") or {}
    return [
        {"id": index, "label": kind, "desc": legend.get(kind) or ""}
        for kind, index in gap_ids(payload).items()
    ]


def _gaps_categories(payload: dict) -> list[dict]:
    cats = category_ids(payload)
    gaps = gap_ids(payload)
    out = []
    for cid, index in cats.items():
        for kind in payload["categories"][cid].get("gaps") or []:
            if kind not in gaps:
                raise UnmappedValue(
                    f"category {cid!r} carries gap {kind!r}, which the payload's gap legend "
                    f"does not describe"
                )
            out.append({"cat_id": index, "gap_id": gaps[kind]})
    return out


def _long_tail_top(payload: dict) -> list[dict]:
    top = (payload.get("long_tail") or {}).get("top") or []
    return [
        {
            "id": index,
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


# --- group B table set ----------------------------------------------------------------

SITE_TABLES: dict[str, SiteTable] = {
    "layers": SiteTable(
        (("id", "INTEGER"), ("label", "VARCHAR")),
        _layers,
        constraints=('PRIMARY KEY ("id")',),
    ),
    "stages": SiteTable(
        (("id", "INTEGER"), ("label", "VARCHAR"), ("desc", "TEXT")),
        _stages,
        constraints=('PRIMARY KEY ("id")',),
    ),
    "gaps": SiteTable(
        (("id", "INTEGER"), ("label", "VARCHAR"), ("desc", "TEXT")),
        _gaps,
        constraints=('PRIMARY KEY ("id")',),
    ),
    "categories": SiteTable(
        (
            ("id", "INTEGER"),
            # NOT NULL as well as UNIQUE: a nullable unique column admits any number of
            # NULLs, which would defeat the deep links the amendment exists for.
            ("slug", "VARCHAR NOT NULL"),
            ("label", "VARCHAR"),
            ("arc", "VARCHAR"),
            ("layer", "INTEGER NOT NULL"),
            ("description", "TEXT"),
            ("stage", "INTEGER NOT NULL"),
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
        (("cat_id", "INTEGER NOT NULL"), ("gap_id", "INTEGER NOT NULL")),
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
            ("id", "INTEGER"),
            ("slug", "VARCHAR NOT NULL"),
            ("org_slug", "VARCHAR NOT NULL"),
            ("name", "VARCHAR"),
            ("org", "VARCHAR"),
            ("type", "VARCHAR"),
            ("category", "INTEGER NOT NULL"),
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
            ("product_id", "INTEGER"),
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
            ("product_id", "INTEGER"),
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
            ("product_id", "INTEGER"),
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
            ("id", "INTEGER"),
            ("url", "TEXT"),
            ("shows", "TEXT"),
            ("notes", "TEXT"),
            ("accessed", "DATE"),
            ("product_id", "INTEGER NOT NULL"),
            ("metric_type", enum_type("metric_name") + " NOT NULL"),
        ),
        _sources,
        constraints=('PRIMARY KEY ("id")', references("product_id", "products", "id")),
    ),
    "product_lineage": SiteTable(
        (
            ("id", "INTEGER"),
            ("product_id", "INTEGER NOT NULL"),
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
            ("id", "INTEGER"),
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

# Group A's names as they appear in Postgres.
REGISTRY_TABLE_NAMES: tuple[str, ...] = tuple(f"{REGISTRY_PREFIX}{n}" for n in REGISTRY_TABLES)
# The full surface, group B then group A, in a stable load order. Group B first so a failure
# in the part the site actually reads is the first thing a log shows.
ALL_TABLES: tuple[str, ...] = tuple(SITE_TABLES) + REGISTRY_TABLE_NAMES


def build_site_tables(payload: dict) -> dict[str, list[dict]]:
    """Every group-B table's rows, keyed by table name."""
    return {name: spec.rows(payload) for name, spec in SITE_TABLES.items()}


def write_site_csvs(payload: dict, out_dir: Path) -> None:
    """Write one CSV per group-B table, so the same loader handles both groups.

    Group A arrives as CSVs the serializers wrote; rendering group B the same way means
    there is one COPY path, one type story and one place a quoting bug could live.
    """
    from build.serialize_registry import write_tables

    spec = {name: table.column_names for name, table in SITE_TABLES.items()}
    write_tables(build_site_tables(payload), out_dir, spec=spec)
