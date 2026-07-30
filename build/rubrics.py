"""Shared scoring ladders, and how a category inherits one.

A category's `scoring_recipe` may either spell out its own `openness` block or point at a
shared ladder in `sources/rubrics/<name>.yaml` with `extends: <name>`.

## Why this exists

The two model categories were ported by copying the ladder. The copies drifted immediately:
identical tiers and identical ordering, differing only in which licenses each happened to
list, and one of them silently missing a `reads` key. Ten software categories ask the same
two questions of the same four license tiers, so ten copies would have been ten chances for
the same drift, in the layer of the map that is hardest to eyeball.

Inheritance also puts the license-to-tier mapping in ONE place, which is where it belongs:
whether AGPL is `osi` is a fact about AGPL, not about telemetry versus deployment.

## Merge rules, deliberately boring

  * The shared file supplies `openness` entirely.
  * A category's own keys — `derived_from`, `deferred`, `note`, `version` — stay its own.
    They are per-category by nature: `derived_from` records what was verified when, and
    `deferred` names products that category has excluded.
  * If a category also declares `openness`, its top-level keys REPLACE the shared ones
    rather than merging into them. Partial merging of a formula is how you get a rule
    order nobody can predict from reading either file.

An `extends` naming a file that does not exist is an error, not a silent fallback: a
category that inherits nothing would otherwise score nothing and report success.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def load_shared(root: Path) -> dict[str, dict]:
    """Every shared ladder, keyed by filename stem."""
    directory = root / "sources" / "rubrics"
    if not directory.is_dir():
        return {}
    return {p.stem: yaml.safe_load(p.read_text()) or {} for p in sorted(directory.glob("*.yaml"))}


def resolve_recipe(category: dict, shared: dict[str, dict]) -> tuple[dict | None, list[str]]:
    """(recipe with `extends` expanded, errors). None when the category declares none."""
    recipe = category.get("scoring_recipe")
    if not recipe:
        return None, []

    base_name = recipe.get("extends")
    if not base_name:
        return recipe, []

    base = shared.get(base_name)
    if base is None:
        return None, [
            f"scoring_recipe extends {base_name!r}, which is not a file in sources/rubrics/ "
            f"(have: {', '.join(sorted(shared)) or 'none'})"
        ]

    merged = dict(base)
    merged.update({key: value for key, value in recipe.items() if key != "extends"})
    merged["extends"] = base_name
    return merged, []


def recipe_vocabulary(recipe: dict) -> set[str]:
    """Every dimension name a source may claim to establish, for one resolved recipe.

    Three things belong in it, and the third is the one that is easy to leave out:

      * the declared dimension names — `weights`, `source`, `core_gated`;
      * the recorded keys those dimensions `read`, since `post-training-data` and
        `core-gated` are how the evidence is actually written down and attributing to
        the recorded key is more precise than attributing to the dimension;
      * the license keys. `license_tier` is derived rather than recorded, so a source
        establishes the LICENSE, which is what `docs/guides/verification.md` writes in
        its worked example. Omitting it would reject the guide's own illustration.
    """
    openness = (recipe.get("openness") or {}) if recipe else {}
    names: set[str] = set()
    for name, spec in (openness.get("dimensions") or {}).items():
        names.add(name)
        names.update((spec or {}).get("reads") or [])
    names.update(((openness.get("license_tier") or {}).get("reads")) or ["license"])
    return names


def dimension_vocabulary(categories: dict[str, dict], shared: dict[str, dict]) -> set[str]:
    """The union of every recipe's vocabulary, across every category.

    Deliberately a union rather than per-category. A source is cited by an axis, and an
    axis belongs to a product, which belongs to one category — so a per-category check
    would be tighter. It would also reject a correct `establishes: [license]` written on
    a product in one of the four categories that has no recipe yet, and those are exactly
    the products Phase 4 will re-read. The union still catches the failure this exists to
    catch, which is a typo: `licence`, `weight`, `core_gate` name nothing anywhere.
    """
    names: set[str] = set()
    for category in (categories or {}).values():
        recipe, errors = resolve_recipe(category or {}, shared or {})
        if recipe and not errors:
            names |= recipe_vocabulary(recipe)
    return names
