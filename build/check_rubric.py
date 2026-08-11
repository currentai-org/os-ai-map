"""Verify a category's `scoring_recipe` reproduces its hand-authored scores.

The rubric in each category YAML was reverse-engineered from scores humans wrote.
That only stays true if something checks it. This replays the rubric's formula
against every product's recorded evidence and compares the result to the recorded
score.

Two ways this earns its place:

  * **Before layer-2 exists**, it proves the rubric is a faithful description of
    how the category was actually scored, rather than a plausible-looking
    invention. A rubric that cannot reproduce the past should not be trusted to
    write the future.
  * **After layer-2 exists**, it is the regression test for rubric edits. Changing
    a threshold should produce a small, explainable diff. If a one-line change
    moves 30 products, that is the signal to stop.

It reads the openness `components` string, which is the evidence the human
recorded. It does NOT re-research anything — this checks the formula, not the
facts.

Exit status is 1 on any mismatch, so CI can gate on it.

Usage:
    uv run python -m build.check_rubric                        # every category with a recipe
    uv run python -m build.check_rubric --category base_pretrained
    uv run python -m build.check_rubric --verbose              # show every product
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

from build.rubrics import load_product_types, load_shared, recipe_for, resolve_recipe_variants

ROOT = Path(__file__).resolve().parents[1]


def split_components(text: str) -> dict[str, str]:
    """Parse the `k:v;k:v` components string into a dict.

    Splits on `;` only at paren depth zero. Values routinely contain semicolons
    inside parentheses — 'license:Apache-2.0(OSI; see LICENSE)' — and a naive
    split silently invents dimensions out of the fragments.
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

    out: dict[str, str] = {}
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def head(value: str) -> str:
    """The bare value, before any parenthetical or comma-separated detail.

    Reads a DIMENSION value — `open(downloadable on HF, gated)` -> `open`. Dimension
    vocabularies are single tokens, so cutting at the first `(` or `,` is the whole job.

    It is deliberately NOT the first statement of license resolution any more. A license
    value is not a single token: `Apache-2.0(code, OSI) + custom weights license(non-OSI)`
    is two licenses, and cutting it here resolved the product on its first half and never
    saw the restrictive one. `license_parts` splits first and this runs per part, on a
    fragment that IS a single token followed by its annotation.
    """
    return re.split(r"[(,]", value)[0].strip()


def license_parts(raw: str) -> list[str]:
    """The `+`-joined halves of a compound license, split at paren depth zero.

    Depth zero because annotations carry their own punctuation —
    `Sustainable-Use-License(fair-code,non-OSI: internal-use-only,no-resale/SaaS)+n8n-Enterprise-License`
    is two licenses, and a naive split on `+` or on `,` invents fragments out of the
    parenthetical.

    Only `+` separates licenses. A depth-zero comma does not: every one in the corpus is
    prose trailing a single license (`Proprietary, proprietary service`,
    `MIT(Maple-client)+AGPL-3.0(OpenSecret-platform),both-OSI`), which is why the comma
    stays `head`'s business, inside a part, rather than becoming a separator here.
    """
    parts: list[str] = []
    depth = 0
    current = ""
    for char in raw:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == "+" and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    return [part.strip() for part in parts if part.strip()]


def split_value(raw: str) -> tuple[str, str]:
    """Split a recorded component into its bare value and its trailing detail.

    'open(downloadable on HF, gated)' -> ('open', 'downloadable on HF, gated')

    Lives beside `head` because the bare half must equal `head(raw)` exactly — that is
    what makes a structured `components` mapping score-neutral, and two modules apart is
    how the two would drift. `build/serialize_rubric.py` re-exports it.
    """
    text = (raw or "").strip()
    parts = re.split(r"[(,]", text, maxsplit=1)
    bare = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""
    return bare, rest.rstrip(")").strip()


FREE_TEXT = "free_text"


def _clauses(text: str) -> list[str]:
    """Depth-0 clause split, KEEPING the keyless clauses `split_components` discards.

    `split_components` drops any clause with no colon, silently — 221 of them across 168
    files. The structured form has to put those somewhere, so the migration needs a splitter
    that hands them back.
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
    return parts


def structure(text: str) -> dict:
    """The flat `k:v;k:v` string as a mapping of key -> {value, detail?, raw?}.

    `raw` appears only when `f"{value}({detail})"` does not reproduce the clause
    byte-for-byte. 155 entries on 81 products need one, in three shapes: text after the
    closing paren ('Apache-2.0(OSI) for the framework'), a comma that is a list separator
    rather than a value/detail boundary ('rows:169,352', which every caller of split_value
    already reads as '169' today), and nested parens, where rstrip(')') removes one closer
    and leaves the inner one unbalanced.

    Keyless clauses accumulate under `free_text` in the order they appeared. They are not
    promoted to dimensions here: `dimension_value` would start answering where it answered
    '' and that can change which rung fires, which this phase is not allowed to do.
    """
    out: dict = {}
    free: list[str] = []
    for clause in _clauses(text):
        clause = clause.strip()
        if ":" not in clause:
            free.append(clause)
            continue
        key, value = clause.split(":", 1)
        key, value = key.strip(), value.strip()
        bare, detail = split_value(value)
        entry: dict = {"value": bare}
        if detail:
            entry["detail"] = detail
        if (f"{bare}({detail})" if detail else bare) != value:
            entry["raw"] = value
        out[key] = entry
    if free:
        out[FREE_TEXT] = free
    return out


def recompose(mapping: dict) -> dict[str, str]:
    """The mapping back to the key -> raw-clause dict `split_components` produces.

    This is the join that makes the migration score-neutral: every reader keeps seeing the
    exact strings it saw before the shape changed.
    """
    out: dict[str, str] = {}
    for key, entry in mapping.items():
        if key == FREE_TEXT:
            continue
        if "raw" in entry:
            out[key] = entry["raw"]
            continue
        detail = entry.get("detail")
        out[key] = f"{entry['value']}({detail})" if detail else entry["value"]
    return out


def components_of(openness: dict) -> dict[str, str]:
    """The recorded components as key -> raw clause, from either shape.

    The one function every reader calls. Both shapes are on `main` at once while the corpus
    migrates in batches, so no reader may assume either.
    """
    components = (openness or {}).get("components")
    if isinstance(components, dict):
        return recompose(components)
    return split_components(components or "")


def components_string(openness: dict) -> str:
    """The flat string, for the payload and for anything that re-splits it itself.

    Prefers the verbatim `raw` sibling, which is what the file said before it was migrated;
    falls back to rejoining the mapping. The payload key stays a string so the front end and
    the rendered notebook see no change at all from this migration.
    """
    block = openness or {}
    raw = block.get("raw")
    if isinstance(raw, str) and raw:
        return raw
    components = block.get("components")
    if isinstance(components, str):
        return components
    return ";".join(f"{key}:{value}" for key, value in recompose(components or {}).items())


_RECORDED_ALIASES: dict[str, str] | None = None


def recorded_license_aliases() -> dict[str, str]:
    """Canonical license name for a name as hand-written in a `components` string.

    Read from `sources/signal_routing.yaml`, which already owns the equivalent map
    for Hub-published slugs. One declaration for both, because they are the same
    kind of fact — what a license is CALLED — and two copies would drift.

    Deliberately does not carry a tier. Which tier a license belongs to stays a
    per-category judgment, and a canonical name that appears in no category example
    still abstains. That abstention is the signal to extend the rubric.
    """
    global _RECORDED_ALIASES
    if _RECORDED_ALIASES is None:
        routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text()) or {}
        aliases = ((routing.get("dimensions") or {}).get("license") or {}).get("aliases") or {}
        _RECORDED_ALIASES = {
            str(slug).strip().lower(): str(name).strip()
            for slug, name in (aliases.get("recorded") or {}).items()
        }
    return _RECORDED_ALIASES


def normalize_license(raw: str) -> str:
    """Reduce ONE recorded license to the name the tier examples are written in.

    Runs on a single part, after `license_parts` has split a compound. Three
    mechanical steps, all spelled out in the recipe's `normalization` list:
      * the annotation is dropped — `Apache-2.0(code, OSI)` is Apache-2.0;
      * a `code ` or `model ` scope prefix is dropped, because the scope is which
        artifact the license covers, not a different license;
      * `assumed-Modified-MIT` — the `assumed-` prefix marks confidence, not a
        different license.

    Then the recorded-name alias, which resolves spellings of one license to one
    name. Applied last, so it sees the value after the mechanical steps rather
    than having to enumerate every prefixed variant.

    The `code X + model Y` rule that used to live here — the MODEL license governs —
    is now a consequence rather than a special case: both halves resolve and the most
    restrictive wins, and a weights license is the restrictive half in every recorded
    instance. Where it would not be, the old rule was wrong anyway: a permissive
    weights license does not buy back a restrictive code license.

    Purely mechanical. Anything needing judgment is left alone to be flagged.
    """
    value = head(raw)
    value = re.sub(r"(?i)^\s*(code|model)\s+", "", value.strip()).strip()
    value = re.sub(r"(?i)^assumed-", "", value).strip()
    return recorded_license_aliases().get(value.lower(), value)


def tier_rank(tiers: dict) -> dict[str, int]:
    """Tier name -> position in the recipe's declaration order.

    Declaration order IS restrictiveness order, ascending — every ladder declares
    `ordered_by: restrictiveness_ascending` and `check_recipe` requires it. A name the
    recipe does not declare ranks last, so an unrecognized tier can never be treated as
    the more permissive of a pair.
    """
    return {name: rank for rank, name in enumerate(tiers)}


def _tier_of(needle: str, tiers: dict) -> str | None:
    """The tier whose examples contain `needle`, already normalized and lowercased."""
    for name, spec in tiers.items():
        for example in (spec or {}).get("examples") or []:
            if example.lower() == needle:
                return name
    # Proprietary is the one tier defined by meaning rather than an example list.
    if needle in ("proprietary", "closed", "none"):
        return "proprietary"
    return None


def license_tier(raw: str, recipe: dict) -> str | None:
    """Map a license string onto a tier from the recipe's own examples.

    A compound license resolves on ALL its parts, most restrictive governing. That is
    what `docs/guides/identity.md` already says openness does across a release's SKUs —
    "a product is as open as the most restrictive license you must accept to use it" —
    and a `+` in a recorded value is that same fact written on one line. Before this,
    resolution truncated at the first `(` or `,` and so read only the first half:
    `internlm` records Apache-2.0 code plus a custom application-gated weights license
    and resolved as `osi`, never seeing the license that actually governs the weights.

    Two things this deliberately does not do:

      * It does not skip a part it cannot map. Every part must resolve or the whole
        value abstains, because an unmapped part can only ever be MORE restrictive than
        the tier the mapped parts reached — ignoring it is exactly how partial coverage
        overstates openness.
      * It does not decompose a compound the recipe declared as a single name. The
        whole, untruncated value is looked up first, so a phrase whose `+` is English
        rather than a join — `follows mC4 + OSCAR-2301 terms`, where neither operand is
        a license — resolves as the one thing the curator recorded. A compound whose
        operands ARE license names does not belong in a tier's examples: it is a
        per-product override, and decomposition handles it once each operand is
        declared on its own.

    Returns None when the license is unmapped, which is a finding rather than an
    error — an unmapped license means the rubric has not yet been told how to
    treat it, and `mixed` means the evidence never recorded the outcome.
    """
    tiers = ((recipe.get("openness") or {}).get("license_tier") or {}).get("values") or {}
    if not tiers:
        return None

    declared = _tier_of(
        recorded_license_aliases().get(raw.strip().lower(), raw.strip()).lower(), tiers
    )
    if declared is not None:
        return declared

    resolved = [_tier_of(normalize_license(part).lower(), tiers) for part in license_parts(raw)]
    if not resolved or any(tier is None for tier in resolved):
        return None
    rank = tier_rank(tiers)
    return max(resolved, key=lambda name: rank.get(name, len(tiers)))


def dimension_spec(dimension: str, recipe: dict) -> dict:
    return (((recipe.get("openness") or {}).get("dimensions") or {}).get(dimension)) or {}


def normalize_dimension_value(value: str, spec: dict) -> str:
    """A recorded spelling translated to the declared value it means.

    `reads:` widens which KEY answers a dimension; this widens which VALUE does. The two
    are separate because `reads:` selects a key and takes its value verbatim, so a synonym
    key whose vocabulary differs - `self-host: none` for `core_gated: gated` - still reads
    as unanswered without a translation step. `dataset.yaml`'s `availability` note is the
    same observation from the other side: there, every spelling was declared as its own
    value and the rules were written to test only one polarity, which works because the
    other polarity falls through. `core_gated` has a rung on both sides, so falling through
    is not available and the spellings have to collapse onto the two declared values.

    An unmapped spelling is returned unchanged, which puts it outside the enum and leaves
    the dimension unanswered. That is deliberate: the formula declares no `otherwise`, so
    abstaining is what happens to evidence the ladder does not understand, and guessing a
    polarity from an unrecognized word is exactly the failure that would not surface.
    """
    return (spec.get("value_aliases") or {}).get(value, value)


def resolve_dimension(components: dict[str, str], dimension: str, recipe: dict) -> str | None:
    """Which recorded key answers a dimension, or None if nothing does.

    A dimension's `reads` list names the `components` keys that carry its answer,
    in preference order. It exists because the same question is recorded under
    different keys in different categories: for a base model the data question is
    `data`, the pretraining corpus, while for a fine-tune the corpus belongs to
    somebody else's model and the honest answer lives in `post-training-data`.

    Prefers the first key whose value is in the declared enum, rather than the
    first key present. A product recording both `data:closed` and
    `post-training-data:open` is answering two different questions, and taking
    whichever appeared first in the string would pick between them by accident.

    Falls back to the first present key when none is in the enum, so an
    unrecognized value surfaces in the mismatch message instead of silently
    reading as absent.

    Returns the KEY rather than the value, because callers that write evidence out
    need the parenthetical detail attached to that key too, and re-deriving the
    preference in a second place is how the two would drift.
    """
    spec = dimension_spec(dimension, recipe)
    keys = spec.get("reads") or [dimension]
    allowed = set(spec.get("values") or ())
    present = [key for key in keys if key in components]
    for key in present:
        if normalize_dimension_value(head(components[key]), spec) in allowed:
            return key
    return present[0] if present else None


def dimension_value(components: dict[str, str], dimension: str, recipe: dict) -> str:
    """The bare value the formula reads for a dimension, or '' if unanswered.

    Alias-translated, so the formula only ever tests the declared vocabulary.
    """
    key = resolve_dimension(components, dimension, recipe)
    if key is None:
        return ""
    return normalize_dimension_value(head(components[key]), dimension_spec(dimension, recipe))


def dimension_read_map(recipe: dict) -> dict[str, str]:
    """Recorded key -> the dimension it can answer.

    A key named in some dimension's `reads` is declared vocabulary even though it is
    not itself a dimension name, so it must not be reported as vocabulary drift.
    """
    declared = ((recipe.get("openness") or {}).get("dimensions")) or {}
    return {
        key: name
        for name, spec in declared.items()
        for key in ((spec or {}).get("reads") or [name])
    }


def license_read_keys(recipe: dict) -> list[str]:
    """Recorded keys that may carry the license the tier lookup consumes."""
    return (((recipe.get("openness") or {}).get("license_tier") or {}).get("reads")) or ["license"]


def matches(rule_when: dict, facts: dict) -> bool:
    return all(facts.get(key) == value for key, value in rule_when.items())


def apply_formula(recipe: dict, facts: dict) -> tuple[int, str] | None:
    """Walk the ordered rules, first match wins."""
    for rule in (recipe.get("openness") or {}).get("formula") or []:
        if "otherwise" in rule:
            result = rule["otherwise"]
            return result["score"], result["class"]
        if matches(rule.get("when") or {}, facts):
            result = rule["then"]
            return result["score"], result["class"]
    return None


def check_category(slug: str, verbose: bool) -> tuple[int, int, list[str], list[str]]:
    """Return (reproduced, total, problems, deferred)."""
    category = yaml.safe_load((ROOT / "sources" / "categories" / f"{slug}.yaml").read_text())
    # `extends: software` pulls in one shared ladder for every product; `extends: {model:
    # ..., software: ...}` pulls in one per product type, as `safeguards` does. Resolution
    # errors are returned as problems rather than raising, so one broken category cannot
    # stop the others being checked - and cannot pass silently either.
    variants, recipe_errors = resolve_recipe_variants(category, load_shared(ROOT))
    if recipe_errors:
        return 0, 0, [f"{slug}: {e}" for e in recipe_errors], []
    if not variants:
        return 0, 0, [], []
    product_types = load_product_types(ROOT)
    # Deferrals are a property of the category's declaration, not of any one ladder:
    # products the category has declared the rubric does not yet decide, each with a
    # reason. Deferring is not the same as passing: these are excluded from the
    # reproduction count rather than counted as reproduced, and printed every run so
    # the exclusion cannot go quiet. A rubric that reproduces 45 of 45 while deferring
    # the one product that contradicts it has proved nothing.
    deferrals = (category.get("scoring_recipe") or {}).get("deferred") or {}

    reproduced = 0
    total = 0
    problems: list[str] = []
    deferred: list[str] = []

    for product in category.get("products") or []:
        path = ROOT / "sources" / "scores" / f"{product}.yaml"
        if not path.exists():
            continue
        if product in deferrals:
            because = (deferrals[product] or {}).get("because", "no reason recorded")
            deferred.append(f"{product}: {' '.join(str(because).split())}")
            continue
        recipe, why = recipe_for(variants, product_types.get(product, ""))
        if recipe is None:
            problems.append(f"{product}: {why}")
            continue
        scores = yaml.safe_load(path.read_text())
        openness = scores.get("openness") or {}
        components = components_of(openness)
        total += 1

        # A ladder need not turn on a source license at all. Hardware openness is scored on
        # design, toolchain and availability - `sources/rubrics/hardware.yaml` declares no
        # `license_tier`, and none of the 20 edge products records a license. Resolving a
        # tier against a recipe that declares none returns None for every product and would
        # report all 20 as hard failures, so the tier step only runs where there is a tier
        # vocabulary to resolve against. `license_tier` is then simply absent from `facts`,
        # and a rung testing it could not have been declared: check_recipe's unreachable-rule
        # assertion rejects a `license_tier` condition with no declared tiers.
        #
        # `serialize_rubric` already tolerated a tier-free ladder - `license_tiers()` emits
        # zero rows and only requires `ordered_by` above one tier. This is check_rubric
        # catching up, and it changes shared resolution semantics, so the warehouse mirror
        # in `currentai.scores.openness_computed` needs the same allowance.
        has_tiers = bool(((recipe.get("openness") or {}).get("license_tier") or {}).get("values"))
        tier = None
        if has_tiers:
            raw_license = next(
                (components[key] for key in license_read_keys(recipe) if components.get(key)), ""
            )
            tier = license_tier(raw_license, recipe)
            if tier is None:
                problems.append(
                    f"{product}: license {raw_license!r} maps to no tier "
                    f"(recorded {openness.get('score')} {openness.get('class')})"
                )
                continue

        # Facts come from the dimensions the recipe DECLARES, not a fixed list. The
        # model categories ask about weights/data/code; software categories ask whether
        # the source is public, whether the real thing self-hosts, and whether the core
        # is feature-gated. Hardcoding the model's four here is what would have forced a
        # checker change per product type.
        declared = ((recipe.get("openness") or {}).get("dimensions")) or {}
        facts = {name: dimension_value(components, name, recipe) for name in declared}
        if has_tiers:
            facts["license_tier"] = tier

        got = apply_formula(recipe, facts)
        expected = (openness.get("score"), openness.get("class"))

        # No rule matched and the recipe declares no `otherwise`, so it is telling us it
        # does not decide this product. Abstain rather than score it.
        #
        # This is how a category opts out of guessing. The model recipes end in an
        # `otherwise` and so can never reach here; the software recipes deliberately do
        # not, because their discriminating evidence - whether the published source is the
        # whole product - is recorded for only about two thirds of products, and the
        # `otherwise` rule would quietly record the rest at whatever the last tier was.
        #
        # The facts go in the reason, so the two causes stay distinguishable: a blank
        # value means nobody recorded that dimension, while a full set of values means the
        # ladder itself has a gap. Abstentions print every run and are excluded from the
        # reproduced count, so neither can go quiet.
        if got is None:
            shown = " ".join(f"{name}={facts[name]!r}" for name in declared)
            if has_tiers:
                shown = f"{shown} tier={tier}"
            deferred.append(
                f"{product}: recipe does not decide it [{shown}] "
                f"(recorded {openness.get('score')} {openness.get('class')})"
            )
            total -= 1
            continue

        if got == expected:
            reproduced += 1
            if verbose:
                print(f"  ok    {product:<24} {expected[0]} {expected[1]}")
        else:
            shown = " ".join(f"{name}={facts[name]!r}" for name in declared)
            if has_tiers:
                shown = f"{shown} tier={tier}"
            problems.append(
                f"{product}: rubric says {got}, scores say {expected} [{shown}]"
            )

    unknown = sorted(set(deferrals) - set(category.get("products") or []))
    for product in unknown:
        problems.append(f"{product}: deferred by the recipe but not a product of this category")

    return reproduced, total, problems, deferred


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="limit to one category slug")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    slugs = (
        [args.category]
        if args.category
        else sorted(p.stem for p in (ROOT / "sources" / "categories").glob("*.yaml"))
    )

    failed = False
    checked_any = False
    for slug in slugs:
        reproduced, total, problems, deferred = check_category(slug, args.verbose)
        if total == 0 and not deferred and not problems:
            continue
        checked_any = True
        status = "OK" if not problems else "FAIL"
        suffix = f", {len(deferred)} deferred" if deferred else ""
        print(f"{slug}: {reproduced}/{total} reproduced{suffix}  [{status}]")
        for problem in problems:
            print(f"  ! {problem}")
        for entry in deferred:
            print(f"  ~ deferred  {entry}")
        if problems:
            failed = True

    if not checked_any:
        print("no category defines a scoring_recipe yet")
        return 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
