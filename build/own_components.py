"""Which coverage entries are a suite's own items: `capability.own_components` (R-2026-11-03-c).

The depth ladder counts a suite's own items in full and caps imported ones one band above their
independent backing (R-2026-11-02-k), so it has to know which components a suite made. The product's
own slug is its own by default. `capability.own_components` adds cited claims: a component the suite
made under a second slug, scoped to the languages, tasks and splits where it made it. A claim that
names the own slug replaces the default with its scope, which is how cited reuse of complete items
withdraws ownership in some languages (R-2026-11-03-i).

Ownership is read only after an entry's evidence is established, so it never rescues unknown
provenance, an uncountable unit or a split that is not the official evaluation, and it never changes
lineage: an owned component can still share ancestry with an import (R-2026-11-03-c).

`own_components_errors` is the validation `build.validate` runs on every score record; `is_own` is
what the calibration, and later the ladder, read. docs/reference/capability.md, "Own components", is
normative.
"""
from __future__ import annotations

SELECTORS = ("languages", "except_languages", "tasks", "splits")


def claim_matches(claim: dict, entry: dict) -> bool:
    """True when a coverage entry falls inside a claim's component and selectors."""
    if entry.get("component") != claim.get("component"):
        return False
    lang = entry.get("language")
    if "languages" in claim and lang not in claim["languages"]:
        return False
    if "except_languages" in claim and lang in claim["except_languages"]:
        return False
    if "tasks" in claim and entry.get("task") not in claim["tasks"]:
        return False
    if "splits" in claim and entry.get("split") not in claim["splits"]:
        return False
    return True


def is_own(slug: str, entry: dict, claims: list[dict] | None) -> bool:
    """Whether one coverage entry is the suite's own item.

    The own slug is owned everywhere unless a claim names it; any component a claim names is owned
    exactly where one of its claims matches.
    """
    claims = claims or []
    named = [c for c in claims if c.get("component") == entry.get("component")]
    if not named:
        return entry.get("component") == slug
    return any(claim_matches(c, entry) for c in named)


def without_second_slugs(slug: str, claims: list[dict] | None) -> list[dict]:
    """The claims with every second-slug claim dropped: only the own slug can be owned."""
    return [c for c in claims or [] if c.get("component") == slug]


def without_mixed_pools(claims: list[dict] | None) -> list[dict]:
    """The claims with each claim's `mixed_languages` taken out of its scope."""
    out = []
    for c in claims or []:
        mixed = set(c.get("mixed_languages") or [])
        if not mixed:
            out.append(c)
            continue
        c = {k: v for k, v in c.items() if k != "mixed_languages"}
        if "languages" in c:
            c["languages"] = [lang for lang in c["languages"] if lang not in mixed]
        else:
            c["except_languages"] = sorted(set(c.get("except_languages") or []) | mixed)
        out.append(c)
    return out


def own_components_errors(slug: str, capability: dict) -> list[str]:
    """Cross-entry rules the schema cannot state (R-2026-11-03-c).

    - Each claim names a component that has coverage entries, and matches at least one of them.
    - Every language, task and split a selector lists matches an entry of that component, and so
      does every language `except_languages` withdraws, so no selector is a dead letter.
    - `mixed_languages` lists only languages the claim covers.
    - Two claims never cover the same entry.
    - Every `cites` URL is the `url` of a `capability.sources` entry.
    """
    if not isinstance(capability, dict):
        return []
    claims = capability.get("own_components")
    if not isinstance(claims, list):
        return []
    where = f"score {slug!r}: capability.own_components"
    coverage = [e for e in capability.get("language_coverage") or [] if isinstance(e, dict)]
    urls = {s.get("url") for s in capability.get("sources") or [] if isinstance(s, dict)}
    errors: list[str] = []
    covered: dict[int, int] = {}

    for i, claim in enumerate(claims):
        if not isinstance(claim, dict):
            continue
        comp = claim.get("component")
        label = f"{where}[{i}] ({comp})"
        of_comp = [e for e in coverage if e.get("component") == comp]
        if not of_comp:
            errors.append(f"{label}: no capability.language_coverage entry has component {comp!r}")
            continue
        langs = {e.get("language") for e in of_comp}
        tasks = {e.get("task") for e in of_comp}
        splits = {e.get("split") for e in of_comp}
        for key, have in (("languages", langs), ("except_languages", langs),
                          ("tasks", tasks), ("splits", splits)):
            for value in claim.get(key) or []:
                if value not in have:
                    errors.append(f"{label}: {key} lists {value!r}, which no {comp!r} entry has, "
                                  f"so the selector matches nothing")
        matched = [idx for idx, e in enumerate(coverage) if claim_matches(claim, e)]
        if not matched:
            errors.append(f"{label}: its selectors match no coverage entry")
        claim_langs = {coverage[idx].get("language") for idx in matched}
        for lang in claim.get("mixed_languages") or []:
            if lang not in claim_langs:
                errors.append(f"{label}: mixed_languages lists {lang!r}, a language the claim "
                              f"does not cover")
        for idx in matched:
            if idx in covered:
                e = coverage[idx]
                errors.append(f"{label}: overlaps {where}[{covered[idx]}] on ({e.get('language')}, "
                              f"{e.get('task')}, {comp}, {e.get('split')}); each entry has one claim")
            else:
                covered[idx] = i
        for url in claim.get("cites") or []:
            if url not in urls:
                errors.append(f"{label}: cites {url!r}, which is not the url of any "
                              f"capability.sources entry")
    return errors
