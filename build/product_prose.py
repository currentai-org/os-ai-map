"""Classify the verification line every product carries in `comments`.

`docs/reference/product-copy.md` standardizes that line on:

    Verified <YYYY-MM-DD> via <document>.

The date is what `sweep_status` ages the prose on. The document is what makes the line
provenance rather than an assertion: it names something a later editor can reopen. And the
line occupies a whole sentence at the end of the field — nothing before `Verified` that could
negate or qualify it, nothing after the period that could ride on it.

## The five states

| state | meaning |
|---|---|
| `canonical` | the whole contract: a real calendar date, `via`, a document, a period, end |
| `named_noncanonical` | names a document, but not in that form — `live` / `on` / `against`, an impossible date, a missing period, a qualifier before `Verified`, or prose after the line |
| `ambiguous_noncanonical` | dated, but no document identifiable — `Verified 2026-08-13.` |
| `generic` | names a METHOD — `primary sources`, `research`, `web search` |
| `missing` | no dated verification line at all |

Only `canonical` passes. The other four are all "go and fix the prose", and they differ in
what the fix is, which is the whole reason the census reports them separately.

`generic` is the one `product-copy.md` rules out by name: those words "describe how you looked
rather than what settled it, and leave the next editor nothing to re-open".

The whole corpus was brought to `canonical` in the 2026-08 closeout (tag
`baseline-472-2026-08-16`). The classifier stays because that is a property new and edited
products have to keep, not a one-time migration: `sweep_status` reports the state per product,
and `tests/test_product_prose.py` asserts the corpus-wide invariant.

Usage:
    uv run python -m build.product_prose          # the five-state census
    uv run python -m build.product_prose --quiet  # counts only
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

from build.vocabulary import is_iso_date

ROOT = Path(__file__).resolve().parents[1]

# A sentence-terminating "." is one followed by whitespace or end of string; a dot inside a
# URL or filename is not, and neither is the dot of an initialism.
#
# `[^.;]*` alone stopped inside `huggingface.co`. Adding only the whitespace test then split
# `the U.S. AI Safety Institute report` into `the U.S` + `. AI Safety Institute report`,
# which is worse than the URL case, because the result reads as grammatical. The lookbehind
# fires only on a single capital letter at a word boundary, so `U.` is kept and `README.` —
# whose `D` has no word boundary before it — correctly ends the clause.
BOUND = r"(?:[^.;]|\.(?!\s|$)|(?<=\b[A-Z])\.(?=\s))*"

# The canonical line, in full, as `product-copy.md` defines it: the verification form starting
# a sentence, a real date, `via`, a document, a final period, and nothing after it.
#
# **Both ends are load-bearing, and each was missing in turn.** An earlier cut enforced only a
# date-shaped prefix, so `Verified 2026-08-13 via the README` (no period) and
# `Verified 2026-08-13 via the README. This trailing claim is not covered.` both passed. Fixing
# the end left the start open, and a bare search for `Verified` anywhere accepted the line's own
# negations:
#
#     Not Verified 2026-08-13 via the README.
#     Last Verified 2026-08-13 via the README.
#     UnVerified 2026-08-13 via the README.
#     Verification status: Verified 2026-08-13 via the README.
#
# The first three assert the OPPOSITE of what the gate would have read them as, which is worse
# than the trailing-prose case. So the form has to begin the field or a sentence.
#
# `BOUND` is what lets the document keep its dots while trailing prose is still rejected.
CANONICAL = re.compile(
    r"(?:^|(?<=[.;!?]\s))Verified (\d{4}-\d{2}-\d{2}) via (" + BOUND + r")\.\s*$"
)

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

    **`canonical` requires the whole contract**, not a date-shaped prefix of it: a real
    calendar date, `via`, a document, a closing period, and the end of the field. A line
    failing any of those is `named_noncanonical` — it names something, it just does not name
    it in the form `product-copy.md` requires, which is a prose fix rather than a re-read.

    The returned date is `None` unless it parses. `2026-99-99` is not a date this can age
    prose on, and handing it back as one is how a downstream freshness sum would quietly get
    a value it cannot compare.
    """
    text = " ".join(str(comments or "").split())
    dated = ANY_DATED.search(text)
    if not dated:
        return "missing", None, None
    iso = dated.group(1) if is_iso_date(dated.group(1)) else None

    match = TRAILER.search(text)
    trailer = match.group(1).strip() if match else ""

    if METHOD_WORDS.match(trailer):
        return "generic", iso, trailer
    # A document has to be identifiable before the line can be called one that names one.
    # `Verified 2026-08-13.` and `Verified live 2026-08-13, but only the adoption axis could
    # be re-derived` are dated and not methods, and neither names anything to reopen.
    # Defaulting those to `named_noncanonical` would promise a mechanical fix that does not
    # exist.
    if not trailer or not HAS_WORD.search(trailer):
        return "ambiguous_noncanonical", iso, trailer
    terminal = CANONICAL.search(text)
    if terminal and is_iso_date(terminal.group(1)):
        return "canonical", terminal.group(1), terminal.group(2)
    return "named_noncanonical", iso, trailer


def census() -> dict[str, list[str]]:
    by_state: dict[str, list[str]] = {}
    for slug, product in products().items():
        state, _, _ = classify(product.get("comments"))
        by_state.setdefault(state, []).append(slug)
    return by_state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quiet", action="store_true",
                        help="counts only; do not list the products behind them")
    args = parser.parse_args()

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
    if unresolved and not args.quiet:
        for state in ("generic", "ambiguous_noncanonical", "named_noncanonical", "missing"):
            for slug in by_state.get(state, []):
                print(f"    {state:22}{slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
