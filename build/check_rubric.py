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


def normalise_license(raw: str) -> str:
    """Reduce a recorded licence string to the licence that governs the weights.

    Two forms in the data need flattening, both spelled out in the recipe's
    `normalisation` list:
      * `code MIT + model DeepSeek-Model-License` — the model licence governs,
        because it is the one attached to the artifact being scored.
      * `assumed-Modified-MIT` — the `assumed-` prefix marks confidence, not a
        different licence.
    Purely mechanical. Anything needing judgment is left alone to be flagged.
    """
    value = head(raw)
    if "+" in value and "model" in value.lower():
        value = value.split("+")[-1]
        value = re.sub(r"(?i)^\s*model\s+", "", value)
    value = re.sub(r"(?i)^assumed-", "", value.strip())
    return value.strip()


def license_tier(raw: str, recipe: dict) -> str | None:
    """Map a licence string onto a tier from the recipe's own examples.

    Returns None when the licence is unmapped, which is a finding rather than an
    error — an unmapped licence means the rubric has not yet been told how to
    treat it, and `mixed` means the evidence never recorded the outcome.
    """
    tiers = ((recipe.get("openness") or {}).get("license_tier") or {}).get("values") or {}
    needle = normalise_license(raw).lower()
    for name, spec in tiers.items():
        for example in (spec or {}).get("examples") or []:
            if example.lower() == needle:
                return name
    # Proprietary is the one tier defined by meaning rather than an example list.
    if needle in ("proprietary", "closed", "none"):
        return "proprietary"
    return None


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


def check_category(slug: str, verbose: bool) -> tuple[int, int, list[str]]:
    """Return (reproduced, total, problems)."""
    category = yaml.safe_load((ROOT / "sources" / "categories" / f"{slug}.yaml").read_text())
    recipe = category.get("scoring_recipe")
    if not recipe:
        return 0, 0, []

    reproduced = 0
    total = 0
    problems: list[str] = []

    for product in category.get("products") or []:
        path = ROOT / "sources" / "scores" / f"{product}.yaml"
        if not path.exists():
            continue
        scores = yaml.safe_load(path.read_text())
        openness = scores.get("openness") or {}
        components = split_components(openness.get("components") or "")
        total += 1

        raw_license = components.get("license", "")
        tier = license_tier(raw_license, recipe)
        if tier is None:
            problems.append(
                f"{product}: licence {raw_license!r} maps to no tier "
                f"(recorded {openness.get('score')} {openness.get('class')})"
            )
            continue

        facts = {
            "weights": head(components.get("weights", "")),
            "data": head(components.get("data", "")),
            "code": head(components.get("code", "")),
            "license_tier": tier,
        }
        got = apply_formula(recipe, facts)
        expected = (openness.get("score"), openness.get("class"))

        if got == expected:
            reproduced += 1
            if verbose:
                print(f"  ok    {product:<24} {expected[0]} {expected[1]}")
        else:
            problems.append(
                f"{product}: rubric says {got}, scores say {expected} "
                f"[weights={facts['weights']} data={facts['data']} "
                f"code={facts['code']} tier={tier}]"
            )

    return reproduced, total, problems


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
        reproduced, total, problems = check_category(slug, args.verbose)
        if total == 0:
            continue
        checked_any = True
        status = "OK" if not problems else "FAIL"
        print(f"{slug}: {reproduced}/{total} reproduced  [{status}]")
        for problem in problems:
            print(f"  ! {problem}")
        if problems:
            failed = True

    if not checked_any:
        print("no category defines a scoring_recipe yet")
        return 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
