"""Classify the verification line every product carries in `comments`.

`docs/reference/product-copy.md` standardizes that line on:

    Verified <YYYY-MM-DD> via <document>.

The date is what `sweep_status` ages the prose on. The document is what makes the line
provenance rather than an assertion: it names something a later editor can reopen.

## The five states

| state | meaning |
|---|---|
| `canonical` | `Verified <date> via <document>.` |
| `named_noncanonical` | names a document, but behind `live` / `on` / `against` |
| `ambiguous_noncanonical` | dated, but no document identifiable — `Verified 2026-08-13.` |
| `generic` | names a METHOD — `primary sources`, `research`, `web search` |
| `missing` | no dated verification line at all |

`generic` is the one `product-copy.md` rules out by name: those words "describe how you looked
rather than what settled it, and leave the next editor nothing to re-open".

The whole corpus was brought to `canonical` in the 2026-08 closeout (tag
`baseline-472-2026-08-16`). The classifier stays because that is a property new and edited
products have to keep, not a one-time migration: `sweep_status` reports the state per product,
and `tests/test_product_prose.py` asserts the corpus-wide invariant.

Usage:
    uv run python -m build.product_prose        # the five-state census
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

CANONICAL = re.compile(r"Verified (\d{4}-\d{2}-\d{2}) via ")
# Any dated verification, however it is worded. The corpus has carried `Verified live <date>
# via`, `Verified live <date> on`, `... against`, and lowercase `verified`.
ANY_DATED = re.compile(r"[Vv]erified[^.]{0,45}?(\d{4}-\d{2}-\d{2})")
# What follows the date, which is where a document name would be. The preposition is
# REQUIRED here: a line that just says "Verified 2026-08-13." names nothing, and treating the
# rest of the sentence as a document is how the census would claim more than it checked.
TRAILER = re.compile(r"[Vv]erified[^.]{0,45}?\d{4}-\d{2}-\d{2}[,;]?\s*(?:via|on|against|using)\s+(.*)")

# Words that name a METHOD rather than a document. product-copy.md forbids these outright.
# A leading article is allowed because "the primary sources" is the same claim as "primary
# sources" and would otherwise slip through as a document name.
#
# This is the sole definition. A second, narrower copy in a sibling module let `substitute
# sources` through as a document name; see docs/reference/sibling-invariants.md and
# tests/test_vocabulary_siblings.py.
METHOD_WORDS = re.compile(
    r"^\s*(?:the\s+|a\s+|our\s+)?"
    r"(primary[- ]sources?|primary-source research|research|web ?search|search|"
    r"substitute sources|desk research|secondary sources?)\b",
    re.IGNORECASE,
)

# A document name has to contain an actual word. `Verified 2026-08-13 via .` is canonical in
# shape and names nothing.
HAS_WORD = re.compile(r"[A-Za-z0-9]")


def products() -> dict[str, dict]:
    return {
        p.stem: (yaml.safe_load(p.read_text()) or {})
        for p in sorted((ROOT / "sources" / "products").glob("*.yaml"))
    }


def classify(comments: str) -> tuple[str, str | None, str | None]:
    """(state, date, trailer) for one product's comments.

    **The trailer is tested before the form.** An earlier cut checked `CANONICAL` first and
    returned, so `Verified 2026-08-13 via primary sources.` classified as `canonical` — the
    correct shape wrapped around the exact thing this classifier exists to find.

    It was latent on the corpus (zero canonical-form lines named a method) and not latent in
    the migration: an early rewording pass removed `live` from four hardware records reading
    `via substitute sources`, promoting them into canonical form while they still named a
    method. `generic` wins over `canonical` whenever the trailer is a method, however the
    line is worded.
    """
    text = " ".join(str(comments or "").split())
    dated = ANY_DATED.search(text)
    if not dated:
        return "missing", None, None

    match = TRAILER.search(text)
    trailer = match.group(1).strip() if match else ""

    if METHOD_WORDS.match(trailer):
        return "generic", dated.group(1), trailer
    # A document has to be identifiable before the line can be called one that names one.
    # `Verified 2026-08-13.` and `Verified live 2026-08-13, but only the adoption axis could
    # be re-derived` are dated and not methods, and neither names anything to reopen.
    # Defaulting those to `named_noncanonical` would promise a mechanical fix that does not
    # exist.
    if not trailer or not HAS_WORD.search(trailer):
        return "ambiguous_noncanonical", dated.group(1), trailer
    if CANONICAL.search(text):
        return "canonical", CANONICAL.search(text).group(1), trailer
    return "named_noncanonical", dated.group(1), trailer


def census() -> dict[str, list[str]]:
    by_state: dict[str, list[str]] = {}
    for slug, product in products().items():
        state, _, _ = classify(product.get("comments"))
        by_state.setdefault(state, []).append(slug)
    return by_state


def main() -> int:
    by_state = census()
    total = sum(len(v) for v in by_state.values())
    print(f"{total} products\n")
    for state in ("canonical", "named_noncanonical", "ambiguous_noncanonical",
                  "generic", "missing"):
        print(f"  {state:22}{len(by_state.get(state, [])):>5}")

    unresolved = sum(
        len(by_state.get(s, []))
        for s in ("generic", "ambiguous_noncanonical", "named_noncanonical", "missing")
    )
    print(f"\n  {'unresolved':22}{unresolved:>5}")
    if unresolved:
        for state in ("generic", "ambiguous_noncanonical", "named_noncanonical", "missing"):
            for slug in by_state.get(state, []):
                print(f"    {state:22}{slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
