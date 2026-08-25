"""Normalize recorded axis assessments to long form — `registry.axis_assessments` (§4.4).

`registry.product_scores` is the wide table: one row per `(product, category)`, all three axes as
columns. This is its long-form companion: one row per
`(declaration_version_id, product_slug, category_slug, axis)`, so a downstream model can filter and
join on a single axis without unpivoting the wide table itself. It does not replace the wide table
during the migration.

## Keys on the declaration, never a `release_id`

This table depends ONLY on declarations — the recorded scores in `sources/scores/`, the resolved
rubrics, and the compiled routing — never on an observation. So it keys on `declaration_version_id`
(`build/declaration_version.py`) and MUST NOT carry an `observation_snapshot_id` or a `release_id`
(§4.4). The commit-scoped `source_git_sha` rides alongside as a human-readable handle.

## One fact, one owner — nothing here is recomputed

The published `(category, product, product_type)` population is the same `build_payload` roster
`registry.product_scores` is built from (preliminary categories dropped, the long tail frozen), so
the two tables never disagree about who is published — and because the roster is per
`(category, product)`, a product published in two categories gets its axes in each, with the
per-category openness tier and adoption route resolved for that category. Every value is transcribed
from an existing owner:

  * `declaration_version_id` / `source_git_sha` — `build/declaration_version.py`.
  * the per-category openness rule basis (license tier) — `build/check_rubric.score_openness`
    against the category+type recipe from `build/rubrics.py`; `basis_detail` is the recorded
    components string (`components_string`).
  * the adoption route a declaration resolves to — `build/adoption_measurements.select_route`,
    the same precedence evaluation applies, just without an observation set (route selection never
    needed one); `instrument_type` is the recorded `signal_type`, `basis_detail` the recorded reach.
  * the capability instrument — the recorded `capability.basis` verbatim; `basis_detail` is the
    recorded anchor comparison (`relative_to` / `relation`) where one exists.
  * held status and its reason — `build/freshness_payload.held_axes`, the same reader the payload's
    `verification_holds` uses.

## `basis` is axis-specific, with a disjoint vocabulary per axis

A single free-text `basis` across three axes is how a column ends up carrying three incompatible
conventions (§4.4). Each axis records the basis it actually keeps, and the vocabularies do not
overlap:

    axis         recorded_value   recorded_class   basis                    basis_detail         instrument_type
    openness     openness score   openness class   resolved license tier    recorded components  (null)
    adoption     adoption level   (null)           resolved route_id        recorded reach       recorded signal_type
    capability   capability score (null)           recorded capability basis recorded anchor     (null)

`recorded_class` (openness) and `instrument_type` (adoption) are the dedicated typed columns §4.4
names.

## Status and the field contract (§4.4, normative) — enforced, fail-closed

    status       recorded_value             last_verified   also required
    confirmed    numeric, or a              REQUIRED        source_count >= 1
                 deliberate dated null
    held         prior value, retained      MUST BE NULL    hold_reason, held_since

A held axis carries no `last_verified` by design (`docs/reference/evidence-and-freshness.md`,
enforced by `tests/test_verification_queue_consistency.py`); emitting one WITH a date is the exact
defect the `partial` freshness state was added to fix on 2026-08-15, so the builder fails closed if
the two co-occur, if a held axis is missing its reason or since date, or if a confirmed axis is
undated or unsourced. An undated axis absent from the queue is a genuine anomaly (`check_freshness`
surfaces it), not a silent `held` row — the build stops rather than fabricate a reason.

`not_applicable` is deliberately NOT emitted: §4.4 defers it pending a ruling, and supplies the
ruling this follows — a deliberate dated null is `confirmed` either way. Every null axis in the
corpus (capability `basis: n/a`, an adoption abstention) already carries a `last_verified`, so it
compiles as `confirmed` with a null `recorded_value`.

Usage:
    uv run python -m build.axis_assessments                       # over the committed sources
    uv run python -m build.axis_assessments --json                # emit the rows as JSON lines
    uv run python -m build.axis_assessments --out build/registry  # write the publishable CSV
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from build.adoption_measurements import all_routes, load_inputs as load_routing_inputs, route_scopes, select_route
from build.check_rubric import components_string, score_openness
from build.freshness_payload import held_axes
from build.rubrics import load_shared, recipe_for, resolve_recipe_variants
from build.validate import load_sources
from build.vocabulary import axes

ROOT = Path(__file__).resolve().parents[1]

# The axis vocabulary has a declarative owner (the score schema, via build.vocabulary); this must
# not hold a private copy of it (tests/test_vocabulary_siblings.py).
AXES: tuple[str, ...] = tuple(axes())

# Table order (§4.4). No release_id and no observation_snapshot_id: this table keys on the
# declaration alone.
COLUMNS: tuple[str, ...] = (
    "declaration_version_id",
    "source_git_sha",
    "product_slug",
    "category_slug",
    "product_type",
    "axis",
    "status",
    "recorded_value",
    "recorded_class",
    "basis",
    "basis_detail",
    "instrument_type",
    "confidence",
    "last_verified",
    "hold_reason",
    "held_since",
    "decision_note",
    "source_count",
)

TABLES: dict[str, tuple[str, ...]] = {"axis_assessments": COLUMNS}


def _axis_block(scores_doc: Mapping, axis: str) -> dict:
    block = (scores_doc or {}).get(axis)
    return block if isinstance(block, dict) else {}


def _openness_basis(recipe: dict | None, openness: Mapping) -> tuple[str | None, str | None]:
    """(the license tier the category ladder resolves to, the recorded components string)."""
    detail = components_string(openness) or None
    if recipe is None:
        return None, detail
    return score_openness(recipe, openness).tier, detail


def _adoption_basis(
    slug: str,
    category_slug: str | None,
    adoption: Mapping,
    declared: Mapping[str, set[str]],
    routes: Sequence[Mapping],
    scopes: Mapping[str, set[str]],
) -> tuple[str | None, str | None]:
    """(the route_id the declarations resolve to by precedence, the recorded reach text)."""
    route = select_route(
        declared.get(slug, set()), adoption.get("signal_type"), category_slug, routes, scopes
    )
    return (route["route_id"] if route else None), adoption.get("reach")


def _capability_basis(capability: Mapping) -> tuple[str | None, str | None]:
    """(the recorded `basis` verbatim, the anchor comparison if one is recorded)."""
    relative_to = capability.get("relative_to")
    relation = capability.get("relation")
    detail = f"relative_to={relative_to};relation={relation}" if (relative_to or relation) else None
    return capability.get("basis"), detail


def _status(slug: str, axis: str, block: Mapping, held_lookup: Mapping) -> tuple[str, str | None, str | None, str | None]:
    """(status, last_verified, hold_reason, held_since), fail-closed on every contract breach."""
    last_verified = block.get("last_verified")
    entry = held_lookup.get((slug, axis))
    if entry is not None:
        if last_verified:
            raise ValueError(
                f"{slug}.{axis} is held in the verification queue but carries last_verified "
                f"{last_verified!r}; a held axis is not confirmed"
            )
        reason, since = entry.get("reason"), entry.get("since")
        if not reason or not since:
            raise ValueError(f"{slug}.{axis} is held but is missing a hold_reason or held_since")
        return "held", None, reason, since
    if not last_verified:
        raise ValueError(
            f"{slug}.{axis} is confirmed but carries no last_verified; a confirmed axis must be "
            "dated (§4.4) — an undated axis absent from the verification queue is an anomaly"
        )
    return "confirmed", str(last_verified), None, None


def axis_assessments(
    population: Sequence[tuple[str, str, str]],
    scores: Mapping[str, Mapping],
    held: Mapping[str, Sequence[Mapping]],
    variants_by_category: Mapping[str, Mapping],
    declared: Mapping[str, set[str]],
    routes: Sequence[Mapping],
    scopes: Mapping[str, set[str]],
    *,
    declaration_version_id: str,
    source_git_sha: str,
) -> list[dict]:
    """One row per `(product, category, axis)` for the published population. Pure over its inputs.

    ``population`` is ``(category_slug, product_slug, product_type)`` triples — the published roster.
    An axis with no recorded block yields no row (nothing was assessed); the status/field contract
    is enforced per emitted row.
    """
    held_lookup = {(slug, e["axis"]): e for slug, entries in held.items() for e in entries}
    rows: list[dict] = []
    for category_slug, slug, product_type in population:
        doc = scores.get(slug) or {}
        variants = variants_by_category.get(category_slug) or {}
        recipe = recipe_for(variants, product_type)[0] if variants else None
        for axis in AXES:
            block = _axis_block(doc, axis)
            if not block:
                continue  # no recorded assessment for this axis
            recorded_class = instrument_type = None
            if axis == "openness":
                recorded_value = block.get("score")
                recorded_class = block.get("class")
                basis, basis_detail = _openness_basis(recipe, block)
            elif axis == "adoption":
                recorded_value = block.get("level")
                instrument_type = block.get("signal_type")
                basis, basis_detail = _adoption_basis(slug, category_slug, block, declared, routes, scopes)
            else:  # capability
                recorded_value = block.get("score")
                basis, basis_detail = _capability_basis(block)
            status, last_verified, hold_reason, held_since = _status(slug, axis, block, held_lookup)
            source_count = len(block.get("sources") or [])
            if status == "confirmed" and source_count < 1:
                raise ValueError(f"{slug}.{axis} is confirmed but cites no sources (source_count 0)")
            rows.append(
                {
                    "declaration_version_id": declaration_version_id,
                    "source_git_sha": source_git_sha,
                    "product_slug": slug,
                    "category_slug": category_slug,
                    "product_type": product_type,
                    "axis": axis,
                    "status": status,
                    "recorded_value": recorded_value,
                    "recorded_class": recorded_class,
                    "basis": basis,
                    "basis_detail": basis_detail,
                    "instrument_type": instrument_type,
                    "confidence": block.get("confidence"),
                    "last_verified": last_verified,
                    "hold_reason": hold_reason,
                    "held_since": held_since,
                    "decision_note": None,
                    "source_count": source_count,
                }
            )
    rows.sort(key=lambda r: (r["product_slug"], r["category_slug"], AXES.index(r["axis"])))
    return rows


def canonical_row(row: Mapping) -> str:
    """A flat, deterministic serialization of one row, for digesting and for tests."""
    return json.dumps({k: row.get(k) for k in COLUMNS}, separators=(",", ":"), sort_keys=True)


# --- inputs and resolution -------------------------------------------------------


def load_inputs(root: Path | None = None):
    """Everything the pure builder reads, each from its existing owner.

    Returns ``(population, scores, held, variants_by_category, declared, routes, scopes)``.
    Population comes from `build_payload` (the owner of "what is published"), called with no
    freshness so it needs no git history."""
    from build.serialize import build_payload

    base = root or ROOT
    src = load_sources(base)
    frozen = json.loads((base / "sources" / "snapshots" / "long_tail.json").read_text())
    payload = build_payload(src, frozen)
    population = [
        (category_slug, product.get("slug"), product.get("type"))
        for category_slug, category in (payload.get("categories") or {}).items()
        for product in (category.get("products") or [])
    ]
    held = held_axes(base)
    shared = load_shared(base)
    variants_by_category = {
        slug: resolve_recipe_variants(cat or {}, shared)[0] for slug, cat in src["categories"].items()
    }
    tables, _bands, _category_of, declared, _recorded = load_routing_inputs(base)
    return population, src["scores"], held, variants_by_category, declared, all_routes(tables), route_scopes(tables)


def resolve(root: Path | None = None, allow_dirty: bool = False) -> list[dict]:
    """The atomic entry point: derive the declaration identity and build every row from it."""
    from build.declaration_version import resolve as resolve_declaration

    base = root or ROOT
    identity = resolve_declaration(base, allow_dirty=allow_dirty)
    population, scores, held, variants, declared, routes, scopes = load_inputs(base)
    return axis_assessments(
        population, scores, held, variants, declared, routes, scopes,
        declaration_version_id=identity["declaration_version_id"],
        source_git_sha=identity["source_git_sha"],
    )


def _summary(rows: Sequence[Mapping]) -> str:
    products = len({r["product_slug"] for r in rows})
    confirmed = sum(1 for r in rows if r["status"] == "confirmed")
    held = sum(1 for r in rows if r["status"] == "held")
    return f"{len(rows)} rows, {products} products, {confirmed} confirmed, {held} held"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the rows as JSON lines")
    parser.add_argument("--check", action="store_true", help="build only, write nothing")
    parser.add_argument("--out", type=Path, default=None, help="write axis_assessments.csv here")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="build over a dirty tree (diagnostic id, not reproducible)")
    args = parser.parse_args()

    try:
        rows = resolve(allow_dirty=args.allow_dirty)
    except Exception as exc:  # DirtyWorktreeError, a recipe/routing error, or a contract breach
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not rows:
        print("no axis rows built; refusing to write an empty table", file=sys.stderr)
        return 2
    if args.json:
        print("\n".join(canonical_row(row) for row in rows))
        return 0
    if args.out and not args.check:
        from build.serialize_registry import write_tables

        write_tables({"axis_assessments": rows}, args.out, TABLES)
        print(f"wrote axis_assessments.csv ({_summary(rows)})")
        return 0
    print(f"{'checked' if args.check else 'built'} axis_assessments ({_summary(rows)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
