"""Assert what a machine can judge about a scoring recipe, and block a merge on failure.

`check_rubric` asks whether a recipe reproduces the recorded scores. This asks whether the
recipe is well formed enough to be worth reviewing at all — every rung justified, every
dimension carrying a machine signal, no rule that cannot fire, no product silently abstained
on, no evidence discarded by the parser. The distinction matters because the two fail for
different reasons and want different fixes: a reproduction mismatch is a finding about a
product, while everything here is a defect in the ladder or its wiring.

It exists because `skills/curate-category/SKILL.md` said "edit any of … `scoring_recipe` …"
and gave no guidance, so every ladder so far was authored from scratch by whoever happened to
be doing it. The taxonomy expansion event will add roughly twenty-four more categories, each
born needing a recipe. `skills/build-rubric/SKILL.md` is the procedure; this is the part of it
a machine can enforce.

Almost everything here composes a signal that already exists somewhere and was not gated:
`check_rubric` knows about abstentions, `check_verification`'s producible-pair check knows
about impossible pairs, and `serialize_rubric --check` knows about undeclared dimensions and
out-of-enum values — but it emits them as warnings among 282, which is to say invisibly.
Gating is the contribution.

WHAT THIS DELIBERATELY DOES NOT ASSERT: any threshold on the reproduction rate, in either
direction. A ladder tuned until it reproduces every recorded score is a curve fit to the data
it was supposed to check; it looks rigorous and is worth less than nothing, because it retires
a check while appearing to pass it. `safeguards` reproduced 0 of 26 and that was the correct
outcome — the mismatches were the finding. `tests/test_check_recipe.py` asserts this module's
source contains no such threshold, because the failure mode is someone adding one later in
good faith.

Usage:
    uv run python -m build.check_recipe                    # every category with a recipe
    uv run python -m build.check_recipe --category ui_api
    uv run python -m build.check_recipe --verbose          # itemize what is reported
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from build.check_rubric import (
    ROOT,
    apply_formula,
    check_category,
    dimension_read_map,
    dimension_value,
    head,
    license_read_keys,
    license_tier,
    load_product_types,
    load_shared,
    recipe_for,
    resolve_recipe_variants,
    split_components,
)
from build.check_verification import rule_outcomes


def split_clauses(text: str) -> list[str]:
    """Every `;`-separated clause at paren depth zero, INCLUDING the keyless ones.

    `split_components` drops a clause with no colon, silently — which is the thing being
    checked, so this cannot reuse it. Paren-aware for the same reason it is there: values
    routinely contain semicolons inside parentheses.
    """
    parts: list[str] = []
    depth = 0
    current = ""
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == ";" and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current)
    return [part.strip() for part in parts if part.strip()]


def _openness(recipe: dict) -> dict:
    return recipe.get("openness") or {}


def _dimensions(recipe: dict) -> dict:
    return _openness(recipe).get("dimensions") or {}


def _formula(recipe: dict) -> list[dict]:
    return _openness(recipe).get("formula") or []


def every_rung_has_a_because(slug: str, recipe: dict) -> list[str]:
    """The `because` is the reviewable artifact — what a human reads where a machine cannot judge.

    Strictly `because`. `note` was the other spelling of the same field: `model.yaml` and
    `base_pretrained` used it exclusively while `software.yaml` and `dataset.yaml` used
    `because`, and all six `note` rungs read as justifications rather than asides. They were
    migrated rather than accommodated, because one field under two names is how a required
    key becomes optional in practice.
    """
    problems = []
    for index, rule in enumerate(_formula(recipe)):
        if not str(rule.get("because") or "").strip():
            outcome = rule.get("then") or rule.get("otherwise") or {}
            problems.append(
                f"category '{slug}' formula rule {index} "
                f"({outcome.get('score')}/{outcome.get('class')}) has no `because`"
            )
    return problems


def every_dimension_has_a_machine_signal(slug: str, recipe: dict) -> list[str]:
    """What a fetcher could settle later, and what will always need a human read.

    Required even when the answer is `none`, because "nobody has thought about it" and "this
    needs a human forever" are different facts and the automation roadmap depends on telling
    them apart.
    """
    return [
        f"category '{slug}' dimension '{name}' declares no `machine_signal`"
        for name, spec in _dimensions(recipe).items()
        if not str((spec or {}).get("machine_signal") or "").strip()
    ]


def no_unreachable_rule(slug: str, recipe: dict) -> list[str]:
    """A rule that cannot fire is where a later edit hides.

    Three ways to be unreachable: declared after an `otherwise`, testing a dimension the
    recipe never declared, or testing a value outside that dimension's own enum. The last two
    are already errors inside `serialize_rubric.scoring_rules`; they are recomputed here
    rather than imported so this module does not depend on the serializer's row shape, and
    `tests/test_serialize_rubric.py` keeps the other copy honest.

    #133 is what this catches: two rungs in `software.yaml` handed a non-OSI license an
    open-bucket class and went unnoticed for weeks because the tier's `examples` list was
    empty, so the rungs could never fire.
    """
    problems = []
    declared = _dimensions(recipe)
    tiers = ((_openness(recipe).get("license_tier") or {}).get("values") or {}).keys()
    seen_otherwise = False
    for index, rule in enumerate(_formula(recipe)):
        if seen_otherwise:
            problems.append(
                f"category '{slug}' formula rule {index} is declared after an `otherwise`, "
                f"so it can never fire"
            )
        if "otherwise" in rule:
            seen_otherwise = True
            continue
        for key, value in (rule.get("when") or {}).items():
            if key == "license_tier":
                if value not in tiers:
                    problems.append(
                        f"category '{slug}' rule {index} tests license_tier={value!r}, "
                        f"which is not one of its declared tiers {sorted(tiers)}"
                    )
            elif key not in declared:
                problems.append(
                    f"category '{slug}' rule {index} tests undeclared dimension {key!r}"
                )
            elif value not in ((declared[key] or {}).get("values") or []):
                problems.append(
                    f"category '{slug}' rule {index} tests {key}={value!r}, which is not in "
                    f"its declared values {(declared[key] or {}).get('values')}"
                )
    return problems


def license_tier_order_is_explicit(slug: str, recipe: dict) -> list[str]:
    """`tier_rank` is emitted from declaration order, so the order must be load-bearing.

    Only required above one tier: with nothing to compare against, "most restrictive" has
    nothing to resolve. A ladder with no `license_tier` at all is fine — hardware openness
    turns on design and toolchain rather than a source license.
    """
    spec = _openness(recipe).get("license_tier") or {}
    values = spec.get("values") or {}
    if len(values) > 1 and spec.get("ordered_by") != "restrictiveness_ascending":
        return [
            f"category '{slug}' declares {len(values)} license tiers but no "
            f"`ordered_by: restrictiveness_ascending`, so `tier_rank` has no defined meaning"
        ]
    return []


def _tested_dimensions(recipe: dict) -> set[str]:
    """Dimensions some rung actually reads. A declared-but-untested dimension is legitimate."""
    return {
        key
        for rule in _formula(recipe)
        for key in (rule.get("when") or {})
        if key != "license_tier"
    }


def clauses_parse(
    slug: str, recipe: dict, components: dict[str, str], deferred: set[str]
) -> tuple[list[str], list[str], int]:
    """Return (blocking, reported, total_dropped) for keyless `components` clauses.

    `split_components` discards any clause without a colon, silently. Across the map that is
    170 of 470 products, and asserting on all of them would fail the gate on day one — which
    `docs/guides/verification.md` already identifies as how a gate dies. Narrowing by hand
    found three populations, and only one is a defect:

    - a clause matching nothing in the category's vocabulary: a free-text tail, harmless
    - a clause restating something already recorded under a proper key: overwhelmingly
      `no feature-gated core` beside `core-gated:ungated`, left behind when #128's correction
      pass added the key without removing the prose. Harmless, and failing on it would teach
      contributors that this gate is noise.
    - a clause that is the ONLY record of a dimension: the real defect, and what cost
      `dataset.yaml` five of its eight deferrals

    So a clause blocks only when it is the sole record of a dimension SOME RUNG TESTS and the
    product is not already deferred. Everything else is reported or counted. That starts at
    zero blocking failures, which is what makes it a ratchet rather than a backlog.
    """
    blocking: list[str] = []
    reported: list[str] = []
    total = 0
    tested = _tested_dimensions(recipe)
    dimensions = _dimensions(recipe)

    for product, raw in sorted(components.items()):
        dropped = [clause for clause in split_clauses(raw) if ":" not in clause]
        if not dropped:
            continue
        total += len(dropped)
        parsed = split_components(raw)
        for name, spec in dimensions.items():
            # Already answered under a proper key, so a prose restatement changes nothing.
            if dimension_value(parsed, name, recipe):
                continue
            allowed = {str(value).lower() for value in ((spec or {}).get("values") or [])}
            for clause in dropped:
                words = {
                    word.strip(".,()").lower() for word in clause.replace("-", " ").split()
                } | {clause.lower()}
                if not (words & allowed):
                    continue
                where = f"category '{slug}' product '{product}': {clause!r}"
                if name in tested and product not in deferred:
                    blocking.append(
                        f"{where} is the only record of dimension '{name}', which the "
                        f"formula tests, and the clause has no key so the parser discards "
                        f"it. Record it as `{name}:<value>`."
                    )
                else:
                    why = "deferred" if product in deferred else f"'{name}' is untested"
                    reported.append(f"{where} holds '{name}' with no key ({why})")
    return blocking, reported, total


def undeclared_keys_holding_evidence(
    slug: str, recipe: dict, components: dict[str, str], deferred: set[str]
) -> tuple[list[str], list[str], int]:
    """Return (blocking, reported, undeclared_key_count) for keys outside the vocabulary.

    An undeclared key is only a defect when it is the ONLY answer to a dimension the formula
    tests AND its recorded value is inside that dimension's enum. Then the ladder reads the
    dimension as unrecorded and either abstains or falls through, while the answer was
    sitting in the file under a different name.

    Scoped the same way and for the same reason as `clauses_parse`. `serialize_rubric --check`
    already reports every undeclared key as vocabulary drift, and there are 113 distinct ones
    across 384 recordings — `self-host` alone appears 52 times. Gating that would fail on day
    one, and the alternative of declaring all 113 as context is a curation project, not a
    gate: a schema key that needs 113 entries before it asserts anything asserts nothing.

    So the loose warning stays in `serialize_rubric` where it belongs, and this gates the six
    cases where the key demonstrably holds an answer the ladder wanted. That is a ratchet.

    `ornith` was the one non-deferred instance: it recorded `recipe:closed` and nothing under
    `code`, so its 3/open_weights came from the `otherwise` rather than from its evidence.
    Fixed by adding `recipe` to `code`'s `reads` list, which changed no score.
    """
    vocabulary = set(dimension_read_map(recipe)) | set(license_read_keys(recipe))
    dimensions = _dimensions(recipe)
    tested = _tested_dimensions(recipe)

    blocking: list[str] = []
    reported: list[str] = []
    undeclared: set[str] = set()

    for product, raw in sorted(components.items()):
        parsed = split_components(raw)
        for key, value in parsed.items():
            if key in vocabulary:
                continue
            undeclared.add(key)
            for name in sorted(tested):
                # Already answered under a key the ladder reads, so the synonym is harmless.
                if dimension_value(parsed, name, recipe):
                    continue
                allowed = {
                    str(item).lower() for item in ((dimensions[name] or {}).get("values") or [])
                }
                if head(value).lower() not in allowed:
                    continue
                where = f"category '{slug}' product '{product}': '{key}:{head(value)}'"
                if product in deferred:
                    reported.append(f"{where} could answer '{name}' (product is deferred)")
                else:
                    blocking.append(
                        f"{where} is the only answer to dimension '{name}', which the "
                        f"formula tests, under a key the ladder does not read. Add '{key}' "
                        f"to that dimension's `reads`, or record it under '{name}'."
                    )
    return blocking, reported, len(undeclared)


def stale_deferrals(
    slug: str, variants: dict, product_types: dict[str, str], deferred: set[str]
) -> list[str]:
    """A product declared `deferred:` that the ladder now reproduces on its own.

    The opposite direction to the silent-abstention check, and the one that rots. A silent
    abstention is a product nobody declared; a stale deferral is a product declared as
    undecidable that has since become decidable — because the ladder gained a rung, a license
    joined a tier, or the evidence was corrected. It looks handled and is not, which is worse:
    the product is excluded from the reproduction count it would now pass, so the count
    understates the ladder and the prose reason states something untrue about the file.

    Nothing checked this before. `n8n` was deferred as "source or core-gated is not recorded"
    while recording `source:public` and a `Sustainable-Use-License` that had since been added
    to the `competition_restricted` tier, so it produced its recorded 2/source_available
    exactly. That one went stale in about a week; at forty categories, on prose nobody
    re-reads, they would accumulate silently.
    """
    problems = []
    for product in sorted(deferred):
        path = ROOT / "sources" / "scores" / f"{product}.yaml"
        if not path.exists():
            continue
        recipe, _ = recipe_for(variants, product_types.get(product, ""))
        if recipe is None:
            continue
        openness = (yaml.safe_load(path.read_text()) or {}).get("openness") or {}
        components = split_components(openness.get("components") or "")
        raw = next((components[k] for k in license_read_keys(recipe) if components.get(k)), "")
        tier = license_tier(raw, recipe)
        if tier is None:
            continue
        declared = _dimensions(recipe)
        facts = {name: dimension_value(components, name, recipe) for name in declared}
        facts["license_tier"] = tier
        got = apply_formula(recipe, facts)
        if got is not None and got == (openness.get("score"), openness.get("class")):
            problems.append(
                f"category '{slug}' defers '{product}', but the ladder now reproduces its "
                f"{got[0]}/{got[1]} from the recorded evidence. Remove the deferral."
            )
    return problems


def check_one(slug: str, verbose: bool) -> tuple[list[str], list[str]]:
    """Check one category. Returns (failures, report_lines)."""
    category = yaml.safe_load(
        (ROOT / "sources" / "categories" / f"{slug}.yaml").read_text()
    )
    variants, errors = resolve_recipe_variants(category, load_shared(ROOT))
    if errors:
        return [f"category '{slug}': {error}" for error in errors], []

    product_types = load_product_types(ROOT)
    deferred = set((category.get("scoring_recipe") or {}).get("deferred") or {})
    products = category.get("products") or []

    # A mixed category holds one ladder per product type, so structural assertions run per
    # VARIANT. `safeguards` is the case: a defect in its software half must not be masked by
    # a clean model half.
    failures: list[str] = []
    reported: list[str] = []
    dimension_count = 0
    rule_count = 0
    tier_count = 0
    for _, recipe in sorted(variants.items()):
        failures += every_rung_has_a_because(slug, recipe)
        failures += every_dimension_has_a_machine_signal(slug, recipe)
        failures += no_unreachable_rule(slug, recipe)
        failures += license_tier_order_is_explicit(slug, recipe)
        dimension_count += len(_dimensions(recipe))
        rule_count += len(_formula(recipe))
        tier_count += len(
            (_openness(recipe).get("license_tier") or {}).get("values") or {}
        )

    # Evidence assertions are per product, against that product's own ladder.
    by_recipe: dict[int, dict[str, str]] = {}
    impossible = 0
    for product in products:
        path = ROOT / "sources" / "scores" / f"{product}.yaml"
        if not path.exists():
            continue
        openness = (yaml.safe_load(path.read_text()) or {}).get("openness") or {}
        recipe, _ = recipe_for(variants, product_types.get(product, ""))
        if recipe is None:
            continue
        by_recipe.setdefault(id(recipe), {})[product] = openness.get("components") or ""
        pair = (openness.get("score"), openness.get("class"))
        if pair[0] is not None and pair not in rule_outcomes(recipe):
            impossible += 1
            failures.append(
                f"category '{slug}' product '{product}': {pair[0]}/{pair[1]} is not an "
                f"outcome any rule produces"
            )

    dropped_total = 0
    undeclared_total = 0
    for recipe in {id(r): r for r in variants.values()}.values():
        components = by_recipe.get(id(recipe), {})
        blocking, reports, dropped = clauses_parse(slug, recipe, components, deferred)
        failures += blocking
        reported += reports
        dropped_total += dropped
        blocking, reports, undeclared = undeclared_keys_holding_evidence(
            slug, recipe, components, deferred
        )
        failures += blocking
        reported += reports
        undeclared_total += undeclared

    # Deferral completeness: a product that neither reproduces nor is declared is a silent
    # abstention, which is the exact convention violation the safeguards review found -- 11
    # auto-abstaining products, invisible in the category YAML, while all 41 of their
    # counterparts elsewhere were declared. Nothing caught it.
    reproduced, total, problems, deferrals = check_category(slug, verbose=False)
    silent = [entry for entry in deferrals if "recipe does not decide it" in entry]
    for entry in silent:
        failures.append(
            f"category '{slug}' product '{entry.split(':')[0]}' abstains silently: it is "
            f"not in `deferred:` and no rung decides it"
        )
    for product, block in ((category.get("scoring_recipe") or {}).get("deferred") or {}).items():
        if not str((block or {}).get("because") or "").strip():
            failures.append(
                f"category '{slug}' defers '{product}' with no reason. Deferral is the "
                f"honest state; silence is not."
            )
    failures += stale_deferrals(slug, variants, product_types, deferred)

    lines = [
        f"  dimensions declared ...... {dimension_count:<4}"
        f"({len(variants)} ladder variant(s))",
        f"  rules .................... {rule_count:<4}(0 unreachable, 0 missing `because`)"
        if not failures
        else f"  rules .................... {rule_count}",
        f"  license tiers ............ {tier_count}",
        f"  products ................. {len(products):<4}"
        f"({reproduced} reproduce, {len(deferrals)} deferred, {len(silent)} silent)",
        f"  impossible pairs ......... {impossible}",
        f"  clauses .................. {dropped_total} dropped, "
        f"{len([f for f in failures if 'has no key so the parser' in f])} blocking",
        f"  undeclared keys .......... {undeclared_total} "
        f"(context, reported by serialize_rubric)",
    ]
    if verbose:
        lines += [f"  ~ {line}" for line in reported]
    # `problems` is check_rubric's reproduction mismatch list. Reported, never gated: a
    # mismatch is a finding about a product and gating it would pressure someone into
    # editing a score to make a ladder pass.
    if verbose and problems:
        lines += [f"  ! reproduction mismatch: {line}" for line in problems]
    return failures, lines


def check_recipe(slug: str | None = None, verbose: bool = False) -> tuple[list[str], list[str]]:
    """Check one category, or every category carrying a recipe."""
    shared = load_shared(ROOT)
    if slug:
        slugs = [slug]
    else:
        slugs = []
        for path in sorted((ROOT / "sources" / "categories").glob("*.yaml")):
            category = yaml.safe_load(path.read_text()) or {}
            variants, errors = resolve_recipe_variants(category, shared)
            if variants and not errors:
                slugs.append(category["name"])

    all_failures: list[str] = []
    all_lines: list[str] = []
    for name in slugs:
        failures, lines = check_one(name, verbose)
        all_failures += failures
        all_lines.append(f"\n{name}")
        all_lines += lines
        for failure in failures:
            all_lines.append(f"  FAIL  {failure}")
        all_lines.append("  [FAIL]" if failures else "  [OK]  ready for human review")
    return all_failures, all_lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="one category slug; default is every recipe")
    parser.add_argument("--all", action="store_true", help="every recipe (the default)")
    parser.add_argument("--verbose", action="store_true", help="itemize reported items")
    args = parser.parse_args()

    failures, lines = check_recipe(args.category, args.verbose)
    print("\n".join(lines))
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\n0 failure(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
