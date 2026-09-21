"""Compare what the repo computes against what the warehouse published, per product.

The parity gate in `docs/reference/evidence-and-freshness.md`. `build/check_rubric.py` walks each
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
  LAG              the disagreement is a whole category the warehouse has not caught up to
  DIVERGE          the two disagree on a product both sides know about

`DIVERGE` is a failure. An abstention on both sides is a curation work list, tracked in
`category_deferrals` and printed by `check_rubric`, not a parity problem.

## Why LAG is a separate verdict

A taxonomy change lands in the repo on merge and reaches the warehouse only when a maintainer
re-materializes the scoring chain by hand - a publish is half a refresh, and nothing about
merging a category triggers a recompute. The #430 split made this concrete: it created several
categories and deleted one, and the next Monday run reported a wall of divergences of which not
one was a scoring disagreement. Every one was either a product in a category the warehouse had
never computed, or a row still filed under the category the repo had deleted.

Reporting that as drift is wrong twice over. It is not drift, and it fails weekly into a
sentinel issue nobody without warehouse credentials can close. So a divergence is LAG when it
is attributable to a category that exists on exactly one side:

  * every product of a category the warehouse has NO rows for  -> the split has not published
  * every row under a category with no file in `sources/categories/` -> the delete has not published

Both conditions are whole-category. A single missing row inside a category the warehouse does
publish stays a DIVERGE, because that is the shape a roster built on the wrong table produces
and it must not be waved through as lag.

LAG is not free. Each lagging category is dated from the commit that created or deleted its
file, and a lag older than LAG_WINDOW_DAYS fails the gate exactly as drift does. The window
buys a maintainer time to run the recompute; it does not let a taxonomy change sit unpublished
indefinitely while the published map serves a taxonomy that no longer exists.

## An undatable lag fails, unless the clone is shallow

A lagging category no commit explains is not lag. The warehouse is publishing rows under a slug
this repository has no record of ever having had, and exempting it would be a permanent silent
pass on the one case that is certainly not a taxonomy change.

So an undatable lag fails, with one exception: a shallow clone genuinely cannot answer the
question, and failing there reports a property of the checkout rather than anything about the
warehouse. The workflow fetches full history for this reason, so in CI there is no exception.

## What this still cannot see

Two limits worth stating rather than discovering later.

  * A whole category's rows can vanish for a reason that is not a taxonomy change - a roster
    regression, a query that lost them. This reads as lag. The dating is what bounds it: an
    established category reads as many days old and fails at once, so the exposure is a category
    created inside the window, where the two are genuinely indistinguishable from here.
  * While a category is lagging, its products are not compared at all. A scoring drift that
    predates the split is therefore invisible until the recompute lands. It cannot be otherwise:
    the warehouse row was computed by the ladder of a category the repo has replaced, and
    comparing it against the new category's ladder would be comparing two different questions.

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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from build.check_rubric import components_of, score_openness
from build.rubrics import load_product_types, load_shared, recipe_for, resolve_recipe_variants
from build.warehouse import query

ROOT = Path(__file__).resolve().parents[1]
TABLE = "currentai.scores.openness_computed"

# How long a taxonomy change may sit in the repo unpublished before the lag becomes a failure.
# Two Mondays: the recompute chain is weekly, so one Monday is a miss and two is a pattern.
LAG_WINDOW_DAYS = 14


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
            computed[key] = score_openness(recipe, openness).result
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


def repo_categories() -> set[str]:
    """Category slugs with a file today, whatever state their recipe is in.

    Read off the filesystem rather than out of `local_scores`, which skips a category whose
    recipe fails to resolve. A broken ladder is a repo problem, and it must not read here as a
    category the repo has deleted.
    """
    return {path.stem for path in (ROOT / "sources" / "categories").glob("*.yaml")}


def history_is_shallow() -> bool:
    """Whether this checkout's history is truncated.

    The difference between "git cannot answer" and "the answer is no". On a shallow clone an
    undatable category file is an artifact of the checkout; on a complete one it means no commit
    in this repository's history ever created or deleted that category, and a warehouse
    publishing rows under it is not waiting for a recompute.

    A probe that fails is treated as shallow, which is the lenient direction: a gate that hard
    fails because it could not run `git` reports its own environment rather than the warehouse.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-shallow-repository"],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return True
    return result.stdout.strip() != "false"


def category_changed_days_ago(slug: str, kind: str) -> int | None:
    """Days since the commit that added (`kind="A"`) or deleted (`kind="D"`) a category file.

    The most recent such commit in both cases: a category deleted and recreated should date
    from the recreation, not from the original. Returns None when git cannot date it, which the
    caller reads against `history_is_shallow()`: on a complete history an undatable category is
    one no commit explains, and that is a failure rather than a lag.
    """
    try:
        result = subprocess.run(
            # `R` alongside the requested filter: with rename detection on, a file moved INTO
            # this path is reported as a rename rather than an addition, and one moved OUT as a
            # rename rather than a deletion. Either way the path was created or removed, which
            # is the only thing being dated here.
            ["git", "log", f"--diff-filter={kind}R", "--format=%cI", "--",
             f"sources/categories/{slug}.yaml"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    stamps = result.stdout.split()
    if not stamps:
        return None
    try:
        when = datetime.fromisoformat(stamps[0])
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - when).days


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="one category rather than all of them")
    parser.add_argument("--verbose", action="store_true", help="print every product")
    args = parser.parse_args()

    computed, deferred = local_scores(args.category)
    published = warehouse_scores(args.category)

    if not published and not args.category:
        # Only on a whole-corpus run. Under `--category`, no rows is the legitimate answer for
        # a category the warehouse has not computed yet, and the lag report below says so.
        print(
            "\nThe warehouse returned no rows at all. That is not parity, it is an unreadable "
            "table: check the query, the credentials, and that the scoring chain has ever run."
        )
        return 1

    repo_cats = repo_categories()
    warehouse_cats = {category for _product, category in published}

    agree = abstain = 0
    drifted: list[str] = []
    lagging: dict[tuple[str, str], list[str]] = {}

    def record(category: str, message: str, *, missing_row: bool) -> None:
        """File one divergence as taxonomy lag or as drift.

        Both lag tests are whole-category on purpose. A product missing from a category the
        warehouse does publish is drift - that is how a roster built on the wrong table shows
        up, and 36 deferrals went missing that way once.
        """
        if missing_row and category not in warehouse_cats:
            lagging.setdefault((category, "A"), []).append(message)
        elif not missing_row and category not in repo_cats:
            lagging.setdefault((category, "D"), []).append(message)
        else:
            drifted.append(message)

    for key in sorted(set(computed) | set(deferred) | set(published)):
        product, category = key
        row = published.get(key)
        if row is None:
            # The warehouse publishes one row per product of every category with rules, so a
            # missing row is a real divergence rather than a coverage gap - unless the whole
            # category is absent, which `record` reads as a split that has not published yet.
            record(
                category,
                f"{product} [{category}]: no row in the warehouse at all",
                missing_row=True,
            )
            continue
        if key in deferred:
            if row["is_deferred"] and as_pair(row) is None:
                abstain += 1
            elif not row["is_deferred"]:
                record(
                    category,
                    f"{product} [{category}]: repo defers it, the warehouse does not know",
                    missing_row=False,
                )
            else:
                record(
                    category,
                    f"{product} [{category}]: deferred, but the warehouse scored it "
                    f"{as_pair(row)}",
                    missing_row=False,
                )
            continue
        if row["is_deferred"]:
            record(
                category,
                f"{product} [{category}]: the warehouse thinks it is deferred",
                missing_row=False,
            )
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
        record(
            category,
            f"{product} [{category}]: repo={local or 'abstains'} "
            f"warehouse={remote or 'abstains'} rule={row['winning_rule_index']} "
            f"facts=[{row['dimension_values']}] {row['scoring_note'] or ''}".rstrip(),
            missing_row=False,
        )

    lagged = sum(len(products) for products in lagging.values())
    print(
        f"\n{agree} agree, {abstain} abstain on both sides, {len(drifted)} diverge, "
        f"{lagged} behind the taxonomy ({len(published)} rows published)"
    )

    shallow = history_is_shallow()
    overdue: list[str] = []
    unexplained: list[str] = []
    for (category, kind) in sorted(lagging):
        products = lagging[(category, kind)]
        age = category_changed_days_ago(category, kind)
        change = "created" if kind == "A" else "deleted"
        if age is None:
            when = "undatable, shallow clone" if shallow else "explained by no commit"
        else:
            when = f"{change} in the repo {age}d ago"
        print(
            f"  ~ {category}: {when}, "
            f"{len(products)} product(s) not reflected in the warehouse"
        )
        if args.verbose:
            for line in products:
                print(f"      {line}")
        if age is None:
            if not shallow:
                unexplained.append(category)
        elif age > LAG_WINDOW_DAYS:
            overdue.append(f"{category} ({change} {age}d ago)")

    for line in drifted:
        print(f"  x {line}")

    if drifted:
        print(
            "\nThe repo and the warehouse disagree. Neither is automatically right: fix "
            "whichever is wrong, and add the case to this file's list if it is a new shape."
        )
        return 1
    if unexplained:
        print(
            "\nNo commit in this repository's history creates or deletes: "
            + ", ".join(sorted(unexplained))
            + ".\nThat is not a taxonomy change waiting to publish. The warehouse is serving a "
            "category this repo has no record of, so read it as drift rather than lag."
        )
        return 1
    if overdue:
        print(
            f"\nA taxonomy change has been unpublished for more than {LAG_WINDOW_DAYS} days: "
            + ", ".join(overdue)
            + ".\nThe published map is serving a taxonomy the repo no longer has. Re-materialize "
            "the scoring chain (docs/operations/deploy-models.md)."
        )
        return 1
    if lagging:
        print(
            f"[OK] repo and warehouse agree on every product both sides know about. "
            f"{len(lagging)} category/categories await a recompute, all inside the "
            f"{LAG_WINDOW_DAYS}-day window."
        )
        return 0
    print("[OK] repo and warehouse agree on every product")
    return 0


if __name__ == "__main__":
    sys.exit(main())
