"""Flatten the payload into one row per product per category, for the warehouse.

The fat table: every published product, every axis, one row.
`currentai.registry.product_scores`.

## Why this reads the payload rather than `sources/`

Because the derived numbers are the point, and there must be exactly one implementation
of them. `overall_score`, `tier`, `maturity` and `mature` are not recorded anywhere — they
come out of `serialize._maturity_score` against the category's weights, and `mature` folds
in the openness bucket on top. A second implementation over here, or in SQL, is the
repo/warehouse split that `check_parity` exists to catch, one axis over: openness had
exactly that shape and it cost seven wrong scores.

So this calls `build_payload` and transcribes. Every number in the CSV is the number the
front end reads, because it is the same object.

## Grain

One row per (category_slug, product_slug). A product in two categories gets two rows and
they may legitimately differ: openness ladders are per category, and `overall_score` is
weighted by the category's own adoption/capability split.

## Scope: published-map products only

This table carries exactly what the payload carries, which means **preliminary categories are
absent** — `build_payload` drops them, deliberately, so /map never shows a category still being
assembled (see `serialize._filter_long_tail`).

That is narrower than the rest of the registry. `currentai.registry.categories` carries a
`status` column and will happily list a preliminary category whose products have no row here.
The contract is deliberate rather than incidental: this table mirrors what is published, so a
reader can trust that every row in it is a row a visitor to the map could see. A table covering
preliminary categories too would need a second serialization mode through `build_payload`, and
the one thing not worth having is a second implementation of the score derivation.

Today all 18 categories are published, so the table is the whole corpus at 522 rows. The day a
preliminary category lands, its products will be missing from here and present in
`registry.categories` — `test_preliminary_categories_are_out_of_scope_by_construction` pins
that as intended rather than leaving it to be rediscovered.

Usage:
    uv run python -m build.serialize_scores
    uv run python -m build.serialize_scores --out build/registry
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from build.freshness_payload import resolve_freshness
from build.serialize import ROOT, build_payload
from build.serialize_registry import write_tables
from build.validate import load_sources

TABLES: dict[str, tuple[str, ...]] = {
    "product_scores": (
        "product_slug",
        "category_slug",
        "product_type",
        "org_slug",
        # Openness, as recorded. The computed counterpart is
        # currentai.scores.openness_computed; check_parity is what holds them together.
        "openness_score",
        "openness_class",
        "openness_bucket",
        "openness_components",
        "openness_confidence",
        "openness_last_verified",
        # Adoption. `level` is the band, `reach` its human range, and `signal_type` decides
        # what this level may be compared to — a stars band and a downloads band are not
        # the same scale, so a query that ranks across signal_types is wrong.
        "adoption_level",
        "adoption_reach",
        "adoption_signal_type",
        "adoption_confidence",
        "adoption_last_verified",
        # Capability. `basis` names the instrument, and it is the peer comparison rather
        # than an absolute: see docs/reference/capability.md.
        "capability_score",
        "capability_basis",
        "capability_value",
        "capability_confidence",
        "capability_last_verified",
        # Derived, and transcribed rather than recomputed. `overall_score` blends adoption
        # and capability on the category's weights, or is adoption alone where capability
        # is unmeasured; `maturity` is its old name and ships identically. `is_mature`
        # gates the same 4.5 bar on the fully-open bucket, because only fully-open
        # products advance a category's stage.
        "overall_score",
        "maturity",
        "is_mature",
        "score_tier",
        # When the whole row was last confirmed, and on what basis. Not the max of the
        # axes' dates: see docs/reference/evidence-and-freshness.md.
        "freshness_date",
        "freshness_basis",
    )
}


def _cell(value) -> str:
    """None becomes the empty string, explicitly.

    `tier` is None for an unranked product and `overall_score` is None where adoption is
    unmeasured. csv.DictWriter would coerce either to an empty field anyway; spelling it
    out means the CSV does not depend on that, and a reader sees one representation of
    "no value" instead of two.
    """
    return "" if value is None else str(value)


def _axis(product: dict, axis: str) -> dict:
    value = product.get(axis)
    return value if isinstance(value, dict) else {}


def _flat(payload: dict) -> list[dict]:
    """One row per (category, product), in the payload's own order."""
    rows: list[dict] = []
    for category_slug, category in (payload.get("categories") or {}).items():
        for product in category.get("products") or []:
            openness = _axis(product, "openness")
            adoption = _axis(product, "adoption")
            capability = _axis(product, "capability")
            freshness = _axis(product, "freshness")
            rows.append(
                {
                    "product_slug": _cell(product.get("slug", "")),
                    "category_slug": category_slug,
                    "product_type": _cell(product.get("type", "")),
                    "org_slug": _cell(product.get("org_slug", "")),
                    "openness_score": _cell(openness.get("score", "")),
                    "openness_class": _cell(openness.get("class", "")),
                    "openness_bucket": _cell(openness.get("bucket", "")),
                    "openness_components": _cell(openness.get("components", "")),
                    "openness_confidence": _cell(openness.get("confidence", "")),
                    "openness_last_verified": _cell(openness.get("last_verified", "")),
                    "adoption_level": _cell(adoption.get("level", "")),
                    "adoption_reach": _cell(adoption.get("reach", "")),
                    "adoption_signal_type": _cell(adoption.get("signal_type", "")),
                    "adoption_confidence": _cell(adoption.get("confidence", "")),
                    "adoption_last_verified": _cell(adoption.get("last_verified", "")),
                    "capability_score": _cell(capability.get("score", "")),
                    "capability_basis": _cell(capability.get("basis", "")),
                    "capability_value": _cell(capability.get("value", "")),
                    "capability_confidence": _cell(capability.get("confidence", "")),
                    "capability_last_verified": _cell(capability.get("last_verified", "")),
                    "overall_score": _cell(product.get("overall_score", "")),
                    "maturity": _cell(product.get("maturity", "")),
                    "is_mature": _cell(product.get("mature", "")),
                    "score_tier": _cell(product.get("tier", "")),
                    "freshness_date": _cell(freshness.get("date", "")),
                    "freshness_basis": _cell(freshness.get("basis", "")),
                }
            )
    return rows


def build_scores(payload: dict) -> dict[str, list[dict]]:
    return {"product_scores": _flat(payload)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="build only, write nothing")
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "registry")
    parser.add_argument("--date", default=None, help="the payload's 'generated' value")
    args = parser.parse_args()

    sources = load_sources(ROOT)
    frozen = json.load(open(ROOT / "sources" / "snapshots" / "long_tail.json"))
    payload = build_payload(sources, frozen, generated=args.date,
                            freshness=resolve_freshness(ROOT))
    tables = build_scores(payload)
    rows = tables["product_scores"]
    if not rows:
        print("no product rows in the payload; refusing to publish an empty table",
              file=sys.stderr)
        return 2
    if not args.check:
        write_tables(tables, args.out, TABLES)
    products = len({r["product_slug"] for r in rows})
    print(f"{'checked' if args.check else 'wrote'} product_scores.csv "
          f"({len(rows)} rows, {products} products, "
          f"{len({r['category_slug'] for r in rows})} categories)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
