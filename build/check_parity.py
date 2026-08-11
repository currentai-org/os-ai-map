"""Compare what the repo computes against what the warehouse published, per product.

The parity gate in `docs/guides/verification.md`. `build/check_rubric.py` walks each
category's ladder in Python. `currentai.scores.openness_computed` walks the same ladder in
Trino. The two are separate implementations of one rubric, and nothing but this makes them
agree.

## Why a per-product comparison and not a count

Because every drift this project has actually shipped was invisible to a count, and four of
them landed in a single day:

  * The serializer emitted evidence under the raw component key, so `post-training-data`
    never matched the formula's `data` condition. Six products would have scored 3 on an
    absence, with no error.
  * `check_rubric` resolved `glm-4` through the recorded-name alias table and the SQL, which
    mirrors `normalize_license` by hand, did not. Local said 47/47; the warehouse said 46/47.
  * Collapsing releases into tiers made `gemma` declare six SKUs across two license tiers,
    and most-restrictive-across-all published the family as `restricted` three months after
    Google relicensed it. `2 / restricted` is a plausible number, which is exactly why only a
    per-product diff catches it.
  * `license:none` resolved to a tier named `proprietary` through check_rubric's definitional
    fallback and to no tier at all through the warehouse's lookup table, so three
    internal-eval benchmarks scored locally and came back null from the warehouse.

Note what those have in common: the aggregate looked right, or looked wrong by one. A gate
that asserts "16/16 categories reproduce" passes through all four.

## What it does not check

Whether the scores are RIGHT. Both sides read evidence parsed out of `sources/scores/`, so
agreement is a fidelity check on two implementations of one formula. `check_verification`
and the re-read pass are what test the facts.

## Reading the output

Every product falls in exactly one bucket:

  agree            both sides produced the same score and class
  both abstain     neither scores it - a declared deferral, or a ladder with no matching rung
  DIVERGE          the two disagree, including one scoring where the other abstains

`DIVERGE` is the only failure. An abstention on both sides is a curation work list, tracked
in `category_deferrals` and printed by `check_rubric`, not a parity problem.

Requires OSO_API_KEY, and reads through `build/warehouse.py` so the query carries a
cache-busting nonce. A parity gate that can read a cached result is not a gate: the
warehouse's SQL API caches on query TEXT, and a fixed verification query returns its first
answer forever.

Usage:
    uv run python -m build.check_parity
    uv run python -m build.check_parity --category safeguards
    uv run python -m build.check_parity --verbose     # print every product, not just diffs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from build.check_rubric import components_of, score_openness
from build.rubrics import load_product_types, load_shared, recipe_for, resolve_recipe_variants
from build.warehouse import query

ROOT = Path(__file__).resolve().parents[1]
TABLE = "currentai.scores.openness_computed"


def local_scores(category_filter: str | None) -> tuple[dict, dict]:
    """(computed, deferred) keyed by (product, category).

    `computed` holds what the ladder produces, or None where it abstains. Deliberately
    replays `check_category`'s resolution rather than reusing its return value, which is a
    count: parity needs the per-product verdict, including for products that category has
    deferred - the warehouse publishes a row for those too and must publish it unscored.
    """
    shared = load_shared(ROOT)
    product_types = load_product_types(ROOT)
    computed: dict[tuple[str, str], tuple[int, str] | None] = {}
    deferred: dict[tuple[str, str], str] = {}

    for path in sorted((ROOT / "sources" / "categories").glob("*.yaml")):
        slug = path.stem
        if category_filter and slug != category_filter:
            continue
        category = yaml.safe_load(path.read_text())
        variants, errors = resolve_recipe_variants(category, shared)
        if errors or not variants:
            continue
        deferrals = (category.get("scoring_recipe") or {}).get("deferred") or {}

        for product in category.get("products") or []:
            key = (product, slug)
            if product in deferrals:
                because = (deferrals[product] or {}).get("because", "no reason recorded")
                deferred[key] = " ".join(str(because).split())
                continue
            score_path = ROOT / "sources" / "scores" / f"{product}.yaml"
            if not score_path.exists():
                continue
            recipe, _ = recipe_for(variants, product_types.get(product, ""))
            if recipe is None:
                computed[key] = None
                continue
            openness = (yaml.safe_load(score_path.read_text()) or {}).get("openness") or {}

            # check_rubric's resolution exactly, via the one function all three modules
            # share. It resolves a license tier only for a rung that tests one, so a
            # product the ladder settles on `source` alone is computed here even when its
            # license maps to no tier - and a product whose deciding rung DOES turn on the
            # license still comes back None.
            #
            # This is a live source of parity noise until the warehouse mirror in
            # `currentai.scores.openness_computed` carries the same rule: the SQL still
            # resolves the tier up front, so the five products that score without one will
            # read as local-scored / warehouse-abstained until it is updated.
            computed[key] = score_openness(recipe, components_of(openness)).result
    return computed, deferred


def warehouse_scores(category_filter: str | None) -> dict[tuple[str, str], dict]:
    where = f"WHERE category_slug = '{category_filter}'" if category_filter else ""
    rows = query(f"""
        SELECT product_slug, category_slug, openness_score, openness_class, is_deferred,
               winning_rule_index, dimension_values, scoring_note
        FROM {TABLE}
        {where}
    """)
    return {(r["product_slug"], r["category_slug"]): r for r in rows}


def as_pair(row: dict) -> tuple[int, str] | None:
    score = row.get("openness_score")
    if score is None:
        return None
    return int(score), row.get("openness_class")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="one category rather than all of them")
    parser.add_argument("--verbose", action="store_true", help="print every product")
    args = parser.parse_args()

    computed, deferred = local_scores(args.category)
    published = warehouse_scores(args.category)

    agree = abstain = 0
    diverged: list[str] = []

    for key in sorted(set(computed) | set(deferred) | set(published)):
        product, category = key
        row = published.get(key)
        if row is None:
            # The warehouse publishes one row per product of every category with rules, so a
            # missing row is a real divergence rather than a coverage gap - and it is how a
            # roster built on the wrong table shows up. 36 deferrals were missing when the
            # roster came from the evidence store, which emits nothing for a deferred product.
            diverged.append(f"{product} [{category}]: no row in the warehouse at all")
            continue
        if key in deferred:
            if row["is_deferred"] and as_pair(row) is None:
                abstain += 1
            elif not row["is_deferred"]:
                diverged.append(
                    f"{product} [{category}]: repo defers it, the warehouse does not know"
                )
            else:
                diverged.append(
                    f"{product} [{category}]: deferred, but the warehouse scored it "
                    f"{as_pair(row)}"
                )
            continue
        if row["is_deferred"]:
            diverged.append(f"{product} [{category}]: the warehouse thinks it is deferred")
            continue

        local = computed.get(key)
        remote = as_pair(row)
        if local == remote:
            if local is None:
                abstain += 1
            else:
                agree += 1
            if args.verbose:
                verdict = "abstain" if local is None else f"{local[0]}/{local[1]}"
                print(f"  ok    {product:34} {category:26} {verdict}")
            continue
        diverged.append(
            f"{product} [{category}]: repo={local or 'abstains'} "
            f"warehouse={remote or 'abstains'} rule={row['winning_rule_index']} "
            f"facts=[{row['dimension_values']}] {row['scoring_note'] or ''}".rstrip()
        )

    print(
        f"\n{agree} agree, {abstain} abstain on both sides, {len(diverged)} diverge "
        f"({len(published)} rows published)"
    )
    for line in diverged:
        print(f"  x {line}")
    if diverged:
        print(
            "\nThe repo and the warehouse disagree. Neither is automatically right: fix "
            "whichever is wrong, and add the case to this file's list if it is a new shape."
        )
        return 1
    print("[OK] repo and warehouse agree on every product")
    return 0


if __name__ == "__main__":
    sys.exit(main())
