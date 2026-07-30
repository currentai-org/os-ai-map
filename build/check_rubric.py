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
    """The bare value, before any parenthetical or comma-separated detail."""
    return re.split(r"[(,]", value)[0].strip()


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
    """Reduce a recorded license string to the license that governs the weights.

    Two forms in the data need flattening, both spelled out in the recipe's
    `normalization` list:
      * `code MIT + model DeepSeek-Model-License` — the model license governs,
        because it is the one attached to the artifact being scored.
      * `assumed-Modified-MIT` — the `assumed-` prefix marks confidence, not a
        different license.

    Then the recorded-name alias, which resolves spellings of one license to one
    name. Applied last, so it sees the value after the mechanical steps rather
    than having to enumerate every prefixed variant.

    Purely mechanical. Anything needing judgment is left alone to be flagged.
    """
    value = head(raw)
    if "+" in value and "model" in value.lower():
        value = value.split("+")[-1]
        value = re.sub(r"(?i)^\s*model\s+", "", value)
    value = re.sub(r"(?i)^assumed-", "", value.strip()).strip()
    return recorded_license_aliases().get(value.lower(), value)


def license_tier(raw: str, recipe: dict) -> str | None:
    """Map a license string onto a tier from the recipe's own examples.

    Returns None when the license is unmapped, which is a finding rather than an
    error — an unmapped license means the rubric has not yet been told how to
    treat it, and `mixed` means the evidence never recorded the outcome.
    """
    tiers = ((recipe.get("openness") or {}).get("license_tier") or {}).get("values") or {}
    needle = normalize_license(raw).lower()
    for name, spec in tiers.items():
        for example in (spec or {}).get("examples") or []:
            if example.lower() == needle:
                return name
    # Proprietary is the one tier defined by meaning rather than an example list.
    if needle in ("proprietary", "closed", "none"):
        return "proprietary"
    return None


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
    spec = (((recipe.get("openness") or {}).get("dimensions") or {}).get(dimension)) or {}
    keys = spec.get("reads") or [dimension]
    allowed = set(spec.get("values") or ())
    present = [key for key in keys if key in components]
    for key in present:
        if head(components[key]) in allowed:
            return key
    return present[0] if present else None


def dimension_value(components: dict[str, str], dimension: str, recipe: dict) -> str:
    """The bare value the formula reads for a dimension, or '' if unanswered."""
    key = resolve_dimension(components, dimension, recipe)
    return head(components[key]) if key is not None else ""


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
    recipe = category.get("scoring_recipe")
    if not recipe:
        return 0, 0, [], []

    # Products the category has declared the rubric does not yet decide, each with
    # a reason. Deferring is not the same as passing: these are excluded from the
    # reproduction count rather than counted as reproduced, and printed every run
    # so the exclusion cannot go quiet. A rubric that reproduces 45 of 45 while
    # deferring the one product that contradicts it has proved nothing.
    deferrals = recipe.get("deferred") or {}

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
        scores = yaml.safe_load(path.read_text())
        openness = scores.get("openness") or {}
        components = split_components(openness.get("components") or "")
        total += 1

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
        facts["license_tier"] = tier

        got = apply_formula(recipe, facts)
        expected = (openness.get("score"), openness.get("class"))

        if got == expected:
            reproduced += 1
            if verbose:
                print(f"  ok    {product:<24} {expected[0]} {expected[1]}")
        else:
            shown = " ".join(f"{name}={facts[name]!r}" for name in declared)
            problems.append(
                f"{product}: rubric says {got}, scores say {expected} [{shown} tier={tier}]"
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
        if total == 0 and not deferred:
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
