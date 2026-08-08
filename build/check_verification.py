"""The three free gates: is a claimed confirmation supported, and is a score even possible.

`docs/guides/verification.md` is normative for all three. This module implements them; when
the two disagree the guide wins. `docs/runbooks/verification-pass.md` has the order of
operations and why the gates land before any bulk editing of `sources/scores/`.

## The invariant

> `last_verified: D` is valid only if, for every dimension the score records, at least one
> source that `establishes` that dimension has `accessed >= D`.

**This validates a claimed date. It never derives one.** The distinction is the whole point
and it is easy to erode: the invariant mentions `accessed`, so someone will eventually
"simplify" it into `last_verified = max(accessed)`. That is issue #115 exactly, and between
#108 and #115 a derived date landed on 19 of the 26 axes that carried one, in six cases
overwriting a date a person had established by checking. Deriving the date asserts a
confirmation nobody made; validating it rejects a confirmation nobody could have made.

Note the aggregation direction, which is also load-bearing: the check is over EVERY
recorded dimension, so the binding constraint is the LEAST recently re-read one.
`max(accessed)` across an axis would pass an axis where one dimension was re-read today and
three were last seen in June — and that is not hypothetical, it is what the 2026-07-28 pass
on the model flagships produced by re-reading only the dataset endpoint.

## The digest requirement — a claimed date needs a fetch to point at

Same scope. Every source read as part of the confirmation carries `http_status` and
`content_sha256`, because those are what only an actual request produces. The invariant
alone catches an unsupported date. It cannot catch a source that never said what `shows`
claims. A missing digest on a newly claimed confirmation means the tool fetched nothing.

## The producible-pair check — a score/class pair must be producible

Full scope, immediately, and unlike the invariant and the digest requirement it needs
nothing to be populated first. For every scored product in a category with a
`scoring_recipe`, `(score, class)` must be the outcome of SOME rule in that recipe.
Deliberately weaker than `build/check_rubric.py`, which asks whether the recipe reproduces
the score from the recorded evidence: producible-pairs ignores the evidence and asks only
whether the pair exists in the ladder at all. That makes it immune to the escape hatch
`check_rubric` has, which is `deferred` — a category can defer a product out of
reproduction, but an impossible pair stays impossible.

Which is how `4 / open_source` survived: no software rule emits 4 with `open_source` (4 is
`open_core`), and no software rule emits 3 at all, since the ladder's rungs are 1, 2, 4, 5.

## How the gates ratchet

The invariant and the digest requirement apply only to axes carrying a `last_verified`,
which is a handful today and grows as the re-read pass proceeds. They therefore cover
exactly what has been done, never block progress, and never permit a regression on ground
already taken. A big-bang gate over all 1370 axes would fail on day one and get switched
off, which is how gates die.

Usage:
    uv run python -m build.check_verification
    uv run python -m build.check_verification --gate producible-pairs
    uv run python -m build.check_verification --verbose
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import yaml

from build.check_rubric import license_read_keys, resolve_dimension, split_components
from build.rubrics import load_product_types, load_shared, recipe_for, resolve_recipe_variants

ROOT = Path(__file__).resolve().parents[1]
AXES = ("openness", "adoption", "capability")

# Axes exempt from the digest requirement because a digest could not have been recorded when
# their sources were read. A visible list that shrinks, rather than a date comparison that
# quietly covers whatever is old.
#
# Empty, and worth saying why. The six axes carrying a date when this gate landed all
# predated it and so would all have qualified. They were re-fetched instead, which took 23
# requests and produced two findings the exemption would have hidden — a Lucie source URL
# that had never resolved as cited, and an `rwkv` weights claim with no source behind it at
# all. Exempting is the cheaper move and it is available. It is not the better one when the
# set is small.
#
# Digests only. An exemption says a digest was unobtainable, which says nothing about whether
# the sources support the date. That is the invariant's question, and the invariant has no
# exemptions.
#
# Each entry names the axis as `<product>:<axis>` and why. Stale entries are reported.
DIGEST_EXEMPT: dict[str, str] = {}


def load() -> tuple[dict, dict, dict]:
    """(scores, categories, resolved recipe variants per category)."""
    scores = {
        p.stem: yaml.safe_load(p.read_text()) or {}
        for p in sorted((ROOT / "sources" / "scores").glob("*.yaml"))
    }
    categories = {
        p.stem: yaml.safe_load(p.read_text()) or {}
        for p in sorted((ROOT / "sources" / "categories").glob("*.yaml"))
    }
    shared = load_shared(ROOT)
    recipes = {}
    for slug, category in categories.items():
        variants, errors = resolve_recipe_variants(category, shared)
        if variants and not errors:
            recipes[slug] = variants
    return scores, categories, recipes


def category_of(categories: dict) -> dict[str, str]:
    """product slug -> its category slug. `validate.py` guarantees exactly one."""
    return {
        product: slug
        for slug, category in categories.items()
        for product in (category.get("products") or [])
    }


def parse_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def recorded_dimensions(components: dict[str, str], recipe: dict) -> dict[str, str]:
    """dimension -> the recorded key that answers it, for every dimension this score RECORDS.

    Two things it is deliberately not:

      * not the dimensions the winning rule reads. That is `dims_relied_on` in the
        warehouse, and it is the wrong denominator — a rule can win on license alone while
        `data` and `code` sit unconfirmed, so counting only what the rule read would let an
        axis claim a confirmation of dimensions nobody looked at.
      * not every key in the components string. Those carry plenty that no ladder scores —
        `paper`, `model_card`, `self-host` — and demanding an establishing source for
        `model_card:open` would make the gate expensive and pointless in the same move.

    So: the dimensions the recipe DECLARES, that this product actually records, plus the
    license, which is recorded rather than derived even though the formula reads the tier.

    Returns the recorded key alongside the dimension name because attribution may use
    either. `finetuned_chat` answers the data question under `post-training-data`, and a
    source that says `establishes: [post-training-data]` is being more precise than one
    saying `[data]`, not less.
    """
    declared = ((recipe.get("openness") or {}).get("dimensions")) or {}
    found: dict[str, str] = {}
    for name in declared:
        key = resolve_dimension(components, name, recipe)
        if key is not None:
            found[name] = key
    for key in license_read_keys(recipe):
        if key in components:
            found["license"] = key
            break
    return found


def invariant(
    scores: dict, categories: dict, recipes: dict, product_types: dict[str, str]
) -> list[str]:
    """Every recorded dimension of a dated axis has an establishing source read since."""
    problems: list[str] = []
    owner = category_of(categories)
    for slug, score in sorted(scores.items()):
        variants = recipes.get(owner.get(slug, ""), {})
        recipe, _ = recipe_for(variants, product_types.get(slug, ""))
        recipe = recipe or {}
        for axis in AXES:
            block = score.get(axis) or {}
            claimed = parse_date(block.get("last_verified"))
            if block.get("last_verified") and claimed is None:
                problems.append(f"{slug}:{axis}: last_verified {block['last_verified']!r} is not a date")
                continue
            if claimed is None:
                continue

            sources = [s for s in (block.get("sources") or []) if isinstance(s, dict)]
            fresh = [s for s in sources if (parse_date(s.get("accessed")) or date.min) >= claimed]
            if not fresh:
                # The floor, and it is the whole of the check for adoption and capability:
                # those axes record one banded value rather than a dimension breakdown, so
                # there is nothing to attribute among, but a confirmation still cannot rest
                # on zero sources read on or after the day it claims to have happened.
                problems.append(
                    f"{slug}:{axis}: claims last_verified {claimed}, but no source was "
                    f"accessed on or after that date"
                )
                continue

            if axis != "openness":
                continue
            components = split_components(block.get("components") or "")
            required = recorded_dimensions(components, recipe)
            for dimension, key in sorted(required.items()):
                names = {dimension, key}
                if not any(names & set(s.get("establishes") or []) for s in fresh):
                    stale = [
                        s.get("accessed")
                        for s in sources
                        if names & set(s.get("establishes") or [])
                    ]
                    detail = (
                        f"only established by a source last read {min(stale)}"
                        if stale
                        else "no source claims to establish it"
                    )
                    problems.append(
                        f"{slug}:{axis}: records {dimension!r} (as {key!r}) but {detail}; "
                        f"last_verified {claimed} is not supported for that dimension"
                    )
    return problems


def digests(scores: dict) -> list[str]:
    """Sources read as part of a claimed confirmation must show they were fetched."""
    problems: list[str] = []
    used: set[str] = set()
    for slug, score in sorted(scores.items()):
        for axis in AXES:
            block = score.get(axis) or {}
            claimed = parse_date(block.get("last_verified"))
            if claimed is None:
                continue
            key = f"{slug}:{axis}"
            if key in DIGEST_EXEMPT:
                used.add(key)
                continue
            for source in block.get("sources") or []:
                if not isinstance(source, dict):
                    continue
                if (parse_date(source.get("accessed")) or date.min) < claimed:
                    continue
                missing = [
                    field
                    for field in ("http_status", "content_sha256")
                    if source.get(field) in (None, "")
                ]
                if missing:
                    problems.append(
                        f"{key}: source {source.get('url')!r} was read on {source.get('accessed')} "
                        f"as part of the confirmation but records no {' and no '.join(missing)}; "
                        f"only an actual fetch produces those"
                    )
    # A stale exemption is an exemption that has stopped shrinking, so it is reported.
    for key, reason in sorted(DIGEST_EXEMPT.items()):
        if key not in used:
            problems.append(
                f"{key}: exempted from the digest requirement ({reason}) but the axis no "
                f"longer carries a last_verified. Drop the exemption."
            )
    return problems


def rule_outcomes(recipe: dict) -> set[tuple[int, str]]:
    """Every (score, class) some rule in the recipe can emit."""
    pairs: set[tuple[int, str]] = set()
    for rule in (recipe.get("openness") or {}).get("formula") or []:
        outcome = rule.get("then") or rule.get("otherwise") or {}
        if "score" in outcome and "class" in outcome:
            pairs.add((outcome["score"], outcome["class"]))
    return pairs


def producible_pairs(
    scores: dict, categories: dict, recipes: dict, product_types: dict[str, str]
) -> list[str]:
    """A recorded (score, class) must be an outcome the category's ladder can produce.

    A mixed category has one ladder per product type. Each product is checked against
    its OWN ladder via `recipe_for` — the same selection the invariant, `check_rubric` and
    `serialize_rubric` all use — not the union of every variant in the category. A
    software product recording a pair only the model ladder can emit must still fail
    here, even though some ladder in the category could have produced it.
    """
    problems: list[str] = []
    for slug, variants in sorted(recipes.items()):
        for product in categories[slug].get("products") or []:
            openness = (scores.get(product) or {}).get("openness") or {}
            score, klass = openness.get("score"), openness.get("class")
            if score is None:
                continue
            recipe, _ = recipe_for(variants, product_types.get(product, ""))
            pairs = rule_outcomes(recipe or {})
            if (score, klass) not in pairs:
                problems.append(
                    f"{product}:openness in {slug}: {score}/{klass} is not an outcome any rule "
                    f"in the recipe produces (it emits {sorted(pairs)}). One of the two values "
                    f"is wrong; read the product rather than widening the ladder to admit it."
                )
    return problems


GATES = {
    "invariant": "a confirmation with no supporting evidence",
    "digests": "a claimed date with no fetch digest",
    "producible-pairs": "an impossible score/class pair",
}
NAME_WIDTH = max(len(name) for name in GATES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=sorted(GATES), help="run one gate only")
    parser.add_argument("--verbose", action="store_true", help="show what each gate covered")
    args = parser.parse_args()

    scores, categories, recipes = load()
    product_types = load_product_types(ROOT)
    results = {
        "invariant": invariant(scores, categories, recipes, product_types),
        "digests": digests(scores),
        "producible-pairs": producible_pairs(scores, categories, recipes, product_types),
    }
    if args.gate:
        results = {args.gate: results[args.gate]}

    dated = sum(
        1
        for score in scores.values()
        for axis in AXES
        if (score.get(axis) or {}).get("last_verified")
    )
    scored = sum(
        1
        for slug in recipes
        for product in categories[slug].get("products") or []
        if ((scores.get(product) or {}).get("openness") or {}).get("score") is not None
    )

    if args.verbose:
        print(f"{dated} axis/axes carry a last_verified  (invariant, digests scope)")
        print(
            f"{scored} scored products in {len(recipes)} categories with a recipe  "
            f"(producible-pairs scope)"
        )
        if DIGEST_EXEMPT:
            print(f"{len(DIGEST_EXEMPT)} digest exemption(s), each of which should be shrinking")
        print()

    failed = False
    for gate, problems in results.items():
        status = "OK" if not problems else "FAIL"
        print(f"{gate:<{NAME_WIDTH}}  {GATES[gate]:<44} [{status}]")
        for problem in problems:
            print(f"  ! {problem}")
        if problems:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
