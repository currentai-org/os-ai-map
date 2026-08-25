"""The repository-owned scoring trace — `evaluation.axis_facts` / `axis_rule_matches` /
`axis_results` (§4.4, ADR-001).

ADR-001 makes this repository the only implementation of the scoring rules, and it retires the
warehouse's parallel openness chain (`scores.openness_facts`, `scores.openness_computed`) only
once a repository-owned evaluator publishes equivalent *queryable trace* tables. This module is
that evaluator's published trace. It decomposes the openness ladder walk — the one
`build/check_rubric.py` already runs — into three tables that make this chain queryable:

    result -> matched rule -> normalized fact -> recorded evidence -> source document

The first three hops are these tables; the last two are already owned. `axis_facts` joins to
`registry.product_openness_evidence` (grain `product_slug, category_slug, dimension, part_index`,
the recorded evidence) and `registry.product_score_sources` (grain `product_slug, category_slug,
axis`, carrying `source_url`, the source document) on their natural keys. Republishing either
here would be a second owner of a fact that already has one.

## No second scoring implementation — the whole point of ADR-001

Every value comes from `build/check_rubric.py`, the single owner of the ladder walk:

  * the ordered-rule walk is `check_rubric.walk_formula_trace` — the same primitive
    `walk_formula` (and so `score_openness`, `check_parity`, `check_recipe`) projects, extended
    only to record which rung it touched. `axis_rule_matches` is that step list.
  * the normalized facts are `check_rubric.trace_openness().facts` — `dimension_value` per
    declared dimension, the value the formula reads. `axis_facts` transcribes them.
  * the per-part license tiers are `check_rubric.resolve_license_parts` — the same resolution
    `license_tier` reduces to one governing tier. `axis_facts` publishes the parts and the
    governing tier whole.
  * the result is `walk_formula_trace`'s, identical to the one `score_openness` reports and
    `check_rubric` gates the recorded score against.

If you find yourself re-deriving a fact, a tier or a rung outcome here, stop — it belongs in
`check_rubric.py` and both readers should share it. The `_ResolvedOpenness` split there exists so
the trace and the score cannot resolve one product two ways.

## Openness only, and why

Only openness is scored by a deterministic ordered-rule walk over normalized facts, so only
openness has a fact/rule/result decomposition to publish. `axis` stays in the grain (the §4.4
grain declares it) so the tables are forward-compatible, but every row today is
`axis = openness`. The other two axes already have their traces, owned elsewhere: adoption's
route -> aggregate -> band trace is `evaluation.product_adoption_measurements`, and capability is
recorded verbatim (`registry.axis_assessments`, `capability.basis`). Emitting an empty rule walk
for them, or restating their recorded values here, would add rows that either say nothing or
duplicate an owner.

## Keys on the declaration alone — no `release_id`, no `observation_snapshot_id`

A deterministic evaluation of declarations does not depend on any measurement, so all three tables
key on `declaration_version_id` (`build/declaration_version.py`) and carry the commit-scoped
`source_git_sha` alongside as a human-readable handle (§4.4). None carries a `release_id` (Phase 8)
or an `observation_snapshot_id`.

## The `evaluator_version` cutover is deferred — this work does not flip the sentinel

`declaration_version_id` folds in `evaluator_version`, today the declared sentinel
`v0-no-repo-evaluator` (`build/declaration_version.EVALUATOR_VERSION`). Landing this evaluator is
what eventually replaces that sentinel, but the replacement re-keys EVERY `declaration_version_id`
corpus-wide — including the already-deployed Phase-3 tables that key on it
(`evaluation.product_adoption_measurements`, `evaluation.adoption_reconciliation`,
`registry.axis_assessments`). So the flip is a separate, reviewed step; this module builds the
evaluator and its trace against the current sentinel and changes no id under any other builder.
See `docs/operations/deploy-scoring-trace.md`.

Usage:
    uv run python -m build.axis_scoring_trace                       # summary over the committed sources
    uv run python -m build.axis_scoring_trace --json                # emit the rows as JSON lines
    uv run python -m build.axis_scoring_trace --table axis_results  # one table's rows as JSON
    uv run python -m build.axis_scoring_trace --out build/evaluation # write the three CSVs
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from build.check_rubric import (
    components_of,
    render_license_part,
    trace_openness,
)
from build.rubrics import load_shared, recipe_for, resolve_recipe_variants
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]

# Openness is the only deterministic rule-walk axis; see the module docstring. The column is
# retained so the grain matches §4.4 and the tables are forward-compatible.
AXIS = "openness"

# --- table specifications (§4.4) --------------------------------------------------
# All three key on the declaration alone. No release_id, no observation_snapshot_id.

FACT_COLUMNS: tuple[str, ...] = (
    "declaration_version_id",
    "source_git_sha",
    "product_slug",
    "category_slug",
    "product_type",
    "axis",
    "dimension",
    "part_index",
    "fact_kind",       # dimension | license_part | license_tier
    "recorded_key",    # the components key the evidence was read under; joins to product_openness_evidence
    "recorded_value",  # the clause as recorded — the recorded-evidence hop
    "normalized_value",  # the fact the formula reads: a dimension value, or a resolved license tier
    "in_declared_enum",
)

RULE_COLUMNS: tuple[str, ...] = (
    "declaration_version_id",
    "source_git_sha",
    "product_slug",
    "category_slug",
    "product_type",
    "axis",
    "rule_index",
    "rule_kind",           # when | otherwise
    "outcome",             # fired | skipped | fell_through_tier | blocked_on_tier
    "matched",             # outcome == fired
    "non_tier_matched",
    "tests_license_tier",
    "wanted_tier",
    "rule_conditions",     # the rung's non-tier when-conditions, k=v;k=v (readability + the fact join)
    "result_score",
    "result_class",
)

RESULT_COLUMNS: tuple[str, ...] = (
    "declaration_version_id",
    "source_git_sha",
    "product_slug",
    "category_slug",
    "product_type",
    "axis",
    "status",              # scored | undecided | blocked_on_tier | deferred | no_recipe
    "result_score",
    "result_class",
    "matched_rule_index",
    "matched_rule_kind",
    "has_license_tiers",
    "license_tier",        # the governing (most restrictive) resolved tier, or null
    "raw_license",
    "recorded_score",
    "recorded_class",
    "reproduces_recorded",  # the evaluator agrees with the recorded score (the dual-run check)
    "rule_count",          # rungs the walk evaluated
    "deferral_reason",     # why the recipe declined (status == deferred), else null
)

TABLES: dict[str, tuple[str, ...]] = {
    "axis_facts": FACT_COLUMNS,
    "axis_rule_matches": RULE_COLUMNS,
    "axis_results": RESULT_COLUMNS,
}


def _base(dvid: str, sha: str, slug: str, category_slug: str, product_type: str) -> dict:
    return {
        "declaration_version_id": dvid,
        "source_git_sha": sha,
        "product_slug": slug,
        "category_slug": category_slug,
        "product_type": product_type,
        "axis": AXIS,
    }


def _conditions_text(conditions: Mapping[str, str]) -> str:
    """A rung's non-tier conditions as a stable `k=v;k=v` string, sorted for determinism."""
    return ";".join(f"{key}={conditions[key]}" for key in sorted(conditions))


def _declared_values(recipe: Mapping, dimension: str) -> set[str] | None:
    spec = (((recipe.get("openness") or {}).get("dimensions") or {}).get(dimension)) or {}
    values = spec.get("values")
    return set(values) if values else None


def evaluate(
    population: Sequence[tuple[str, str, str]],
    scores: Mapping[str, Mapping],
    variants_by_category: Mapping[str, Mapping],
    deferrals_by_category: Mapping[str, Mapping],
    *,
    declaration_version_id: str,
    source_git_sha: str,
) -> dict[str, list[dict]]:
    """The three trace tables as one pure function of the declarations. One walk, three
    projections — a single evaluation per product, decomposed rather than recomputed.

    ``population`` is the published ``(category_slug, product_slug, product_type)`` roster, the
    same one `registry.axis_assessments` and `registry.product_scores` are built from, so who is
    evaluated here cannot disagree with who is published. Every product yields exactly one
    ``axis_results`` row; a scored product also yields its facts and its rung walk.
    """
    facts_rows: list[dict] = []
    rule_rows: list[dict] = []
    result_rows: list[dict] = []

    for category_slug, slug, product_type in population:
        base = _base(declaration_version_id, source_git_sha, slug, category_slug, product_type)
        openness = (scores.get(slug) or {}).get("openness") or {}
        recorded_score = openness.get("score")
        recorded_class = openness.get("class")

        variants = variants_by_category.get(category_slug) or {}
        recipe = recipe_for(variants, product_type)[0] if variants else None

        # A category with no ladder for this product cannot be evaluated deterministically.
        if recipe is None:
            result_rows.append(
                {
                    **base,
                    "status": "no_recipe",
                    "result_score": None,
                    "result_class": None,
                    "matched_rule_index": None,
                    "matched_rule_kind": None,
                    "has_license_tiers": None,
                    "license_tier": None,
                    "raw_license": None,
                    "recorded_score": recorded_score,
                    "recorded_class": recorded_class,
                    "reproduces_recorded": None,
                    "rule_count": 0,
                    "deferral_reason": None,
                }
            )
            continue

        # The recipe has declared it does not decide this product. Deferring is not scoring:
        # emit the result row (recorded score, for reference) and no fact or rule rows, so the
        # decline is visible and no invented walk implies the ladder ran.
        deferrals = deferrals_by_category.get(category_slug) or {}
        if slug in deferrals:
            because = (deferrals[slug] or {}).get("because", "no reason recorded")
            result_rows.append(
                {
                    **base,
                    "status": "deferred",
                    "result_score": None,
                    "result_class": None,
                    "matched_rule_index": None,
                    "matched_rule_kind": None,
                    "has_license_tiers": None,
                    "license_tier": None,
                    "raw_license": None,
                    "recorded_score": recorded_score,
                    "recorded_class": recorded_class,
                    "reproduces_recorded": None,
                    "rule_count": 0,
                    "deferral_reason": " ".join(str(because).split()),
                }
            )
            continue

        trace = trace_openness(recipe, openness)
        components = components_of(openness)

        # --- axis_facts: one row per declared dimension, plus the license decomposition ---
        for dimension, value in trace.facts.items():
            key = trace.fact_keys.get(dimension)
            allowed = _declared_values(recipe, dimension)
            facts_rows.append(
                {
                    **base,
                    "dimension": dimension,
                    "part_index": 0,
                    "fact_kind": "dimension",
                    "recorded_key": key,
                    "recorded_value": components.get(key) if key else None,
                    "normalized_value": value or None,
                    "in_declared_enum": (value in allowed) if allowed is not None else None,
                }
            )
        if trace.has_tiers:
            for index, (part, tier) in enumerate(trace.license_parts):
                facts_rows.append(
                    {
                        **base,
                        "dimension": "license",
                        "part_index": index,
                        "fact_kind": "license_part",
                        "recorded_key": trace.license_key,
                        "recorded_value": render_license_part(part),
                        "normalized_value": tier,
                        "in_declared_enum": tier is not None,
                    }
                )
            # The governing fact the rule walk actually tests, so a rung's `license_tier`
            # condition joins to a fact row by dimension name like every other condition.
            facts_rows.append(
                {
                    **base,
                    "dimension": "license_tier",
                    "part_index": 0,
                    "fact_kind": "license_tier",
                    "recorded_key": trace.license_key,
                    "recorded_value": trace.raw_license or None,
                    "normalized_value": trace.tier,
                    "in_declared_enum": trace.tier is not None,
                }
            )

        # --- axis_rule_matches: the ordered rung walk, exactly as it was evaluated ---
        for step in trace.steps:
            rule_rows.append(
                {
                    **base,
                    "rule_index": step.rule_index,
                    "rule_kind": step.kind,
                    "outcome": step.outcome,
                    "matched": step.outcome == "fired",
                    "non_tier_matched": step.non_tier_matched,
                    "tests_license_tier": step.tests_tier,
                    "wanted_tier": step.wanted_tier,
                    "rule_conditions": _conditions_text(step.conditions),
                    "result_score": step.result[0] if step.result else None,
                    "result_class": step.result[1] if step.result else None,
                }
            )

        # --- axis_results: the disposition, and the dual-run agreement check ---
        if trace.result is not None:
            status = "scored"
        elif trace.blocked_on_tier:
            status = "blocked_on_tier"
        else:
            status = "undecided"
        matched_kind = next((s.kind for s in trace.steps if s.outcome == "fired"), None)
        reproduces = (
            trace.result == (recorded_score, recorded_class) if trace.result is not None else None
        )
        result_rows.append(
            {
                **base,
                "status": status,
                "result_score": trace.result[0] if trace.result else None,
                "result_class": trace.result[1] if trace.result else None,
                "matched_rule_index": trace.matched_index,
                "matched_rule_kind": matched_kind,
                "has_license_tiers": trace.has_tiers,
                "license_tier": trace.tier,
                "raw_license": trace.raw_license or None,
                "recorded_score": recorded_score,
                "recorded_class": recorded_class,
                "reproduces_recorded": reproduces,
                "rule_count": len(trace.steps),
                "deferral_reason": None,
            }
        )

    facts_rows.sort(key=lambda r: (r["product_slug"], r["category_slug"], r["dimension"], r["part_index"]))
    rule_rows.sort(key=lambda r: (r["product_slug"], r["category_slug"], r["rule_index"]))
    result_rows.sort(key=lambda r: (r["product_slug"], r["category_slug"]))
    return {"axis_facts": facts_rows, "axis_rule_matches": rule_rows, "axis_results": result_rows}


def canonical_row(table: str, row: Mapping) -> str:
    """A flat, deterministic serialization of one row, for digesting and for tests."""
    return json.dumps({k: row.get(k) for k in TABLES[table]}, separators=(",", ":"), sort_keys=True)


# --- inputs and atomic resolution ------------------------------------------------


def load_inputs(root: Path | None = None):
    """Everything the pure evaluator reads, each from its existing owner.

    Returns ``(population, scores, variants_by_category, deferrals_by_category)``. Population is
    `build_payload`'s published roster — the one owner of "what is published" — so this table's
    population matches `registry.axis_assessments` and `registry.product_scores` exactly.
    """
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
    shared = load_shared(base)
    variants_by_category = {
        slug: resolve_recipe_variants(cat or {}, shared)[0] for slug, cat in src["categories"].items()
    }
    deferrals_by_category = {
        slug: ((cat or {}).get("scoring_recipe") or {}).get("deferred") or {}
        for slug, cat in src["categories"].items()
    }
    return population, src["scores"], variants_by_category, deferrals_by_category


def resolve(root: Path | None = None, allow_dirty: bool = False) -> dict[str, list[dict]]:
    """The atomic entry point: derive the declaration identity and evaluate every product from it."""
    from build.declaration_version import resolve as resolve_declaration

    base = root or ROOT
    identity = resolve_declaration(base, allow_dirty=allow_dirty)
    population, scores, variants, deferrals = load_inputs(base)
    return evaluate(
        population,
        scores,
        variants,
        deferrals,
        declaration_version_id=identity["declaration_version_id"],
        source_git_sha=identity["source_git_sha"],
    )


def _summary(tables: Mapping[str, Sequence[Mapping]]) -> str:
    results = tables["axis_results"]
    by_status: dict[str, int] = {}
    for row in results:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    scored = [r for r in results if r["status"] == "scored"]
    reproduced = sum(1 for r in scored if r["reproduces_recorded"])
    status_text = ", ".join(f"{k} {v}" for k, v in sorted(by_status.items()))
    return (
        f"{len(tables['axis_facts'])} facts, {len(tables['axis_rule_matches'])} rule matches, "
        f"{len(results)} results ({status_text}); {reproduced}/{len(scored)} scored reproduce the recorded score"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the rows as JSON lines")
    parser.add_argument("--table", choices=sorted(TABLES), help="with --json, emit only this table")
    parser.add_argument("--check", action="store_true", help="build only, write nothing")
    parser.add_argument("--out", type=Path, default=None, help="write the three CSVs into this directory")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="build over a dirty tree (diagnostic id, not reproducible)")
    args = parser.parse_args()

    try:
        tables = resolve(allow_dirty=args.allow_dirty)
    except Exception as exc:  # DirtyWorktreeError, a recipe error, or a contract breach
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not tables["axis_results"]:
        print("no result rows built; refusing to write empty tables", file=sys.stderr)
        return 2

    if args.json:
        names = [args.table] if args.table else list(TABLES)
        for name in names:
            for row in tables[name]:
                print(canonical_row(name, row))
        return 0
    if args.out and not args.check:
        from build.serialize_registry import write_tables

        write_tables(tables, args.out, TABLES)
        print(f"wrote axis_facts.csv, axis_rule_matches.csv, axis_results.csv to {args.out}")
        print(_summary(tables))
        return 0
    print(f"{'checked' if args.check else 'built'} scoring trace: {_summary(tables)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
