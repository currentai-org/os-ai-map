"""Classify every product's prose verification line, and gather evidence for repairing it.

`docs/reference/product-copy.md` standardizes the line in `comments` on:

    Verified <YYYY-MM-DD> via <document>.

`sweep_status` reported 245 of 472 products as unfinished, which collapsed four materially
different states into one number. Measured 2026-08-15, **no product is missing a verification
line** and every date is in August — so nothing in that 245 is unverified. What varies is
whether the line names something a later editor can reopen.

## The four states

| state | meaning | remedy |
|---|---|---|
| `canonical` | `Verified <date> via <document>.` | none |
| `named_noncanonical` | names a real document behind `live` / `on` / `against` | mechanical rewording |
| `generic` | names a METHOD — `primary sources`, `research`, `web search` | evidence matching, or a re-read |
| `missing` | no dated verification line at all | research |

`generic` is the substantive one, and `product-copy.md` rules it out by name: those words
"describe how you looked rather than what settled it, and leave the next editor nothing to
re-open". Rewording cannot repair them; something has to supply the document.

## Why deriving from score sources is a repair rather than a new claim

Each product's score file records the exact URLs fetched, dated and digested. Where one was
accessed **on the date the prose line already claims**, and its `shows` describes the product
rather than a score dimension, that document is what a reader would have to reopen — naming
it states what the repository already proves was read. Measured 2026-08-15, all 166 `generic`
products have at least one date-aligned source, so date alignment alone decides nothing; the
judgment is entirely whether the source is a nameable, authoritative document that supports
the prose.

**This module does not make that judgment.** It gathers the candidates, applies mechanical
hints, and emits a packet per product for a reviewer to settle. `build/apply_provenance.py`
then writes only the packets marked `derive`.

Usage:
    uv run python -m build.prose_provenance                 # the four-state census
    uv run python -m build.prose_provenance --packets FILE  # write candidate packets
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AXES = ("openness", "adoption", "capability")

CANONICAL = re.compile(r"Verified (\d{4}-\d{2}-\d{2}) via ")
# Any dated verification, however it is worded. The corpus carries `Verified live <date> via`,
# `Verified live <date> on`, `... against`, and lowercase `verified`.
ANY_DATED = re.compile(r"[Vv]erified[^.]{0,45}?(\d{4}-\d{2}-\d{2})")
# What follows the date, which is where a document name would be.
TRAILER = re.compile(r"[Vv]erified[^.]{0,45}?\d{4}-\d{2}-\d{2}[,;]?\s*(?:via|on|against|using)?\s*(.*)")

# Words that name a METHOD rather than a document. product-copy.md forbids these outright.
METHOD_WORDS = re.compile(
    r"^\s*(primary[- ]source|primary sources|research|web search|websearch|search|"
    r"primary-source research|substitute sources)",
    re.IGNORECASE,
)

# URLs that are machine endpoints or count aggregators rather than documents a person reads.
# A source like this can establish a score dimension and still say nothing about what the
# product IS, which is what the prose line has to point at.
NOT_A_DOCUMENT = re.compile(
    r"(/api/|api\.github\.com|huggingface\.co/api/|pypistats\.org|pepy\.tech|"
    r"api\.npmjs\.org|crates\.io/api|/downloads/point/|hub\.docker\.com/v2/)",
    re.IGNORECASE,
)

# `shows` text that describes a measurement rather than the product.
MEASUREMENT_ONLY = re.compile(
    r"^\s*[\d,]+\s*(downloads|stars|pulls|citations)|^\s*`?(downloads|stargazers_count)",
    re.IGNORECASE,
)


def products() -> dict[str, dict]:
    return {
        p.stem: (yaml.safe_load(p.read_text()) or {})
        for p in sorted((ROOT / "sources" / "products").glob("*.yaml"))
    }


def scores() -> dict[str, dict]:
    return {
        p.stem: (yaml.safe_load(p.read_text()) or {})
        for p in sorted((ROOT / "sources" / "scores").glob("*.yaml"))
    }


def classify(comments: str) -> tuple[str, str | None, str | None]:
    """(state, date, trailer) for one product's comments."""
    text = " ".join(str(comments or "").split())
    if CANONICAL.search(text):
        return "canonical", CANONICAL.search(text).group(1), None
    dated = ANY_DATED.search(text)
    if not dated:
        return "missing", None, None
    trailer = ""
    match = TRAILER.search(text)
    if match:
        trailer = match.group(1).strip()
    state = "generic" if METHOD_WORDS.match(trailer) else "named_noncanonical"
    return state, dated.group(1), trailer


def candidates(slug: str, date: str, score: dict) -> list[dict]:
    """Date-aligned sources from the product's own score file, with mechanical hints.

    The hints are advisory. `looks_like_document` false is a strong signal for `reread` — a
    pypistats response cannot tell a reader what a product is — but true is NOT a licence to
    derive: whether the page supports this product's prose is a reading, not a pattern match.
    """
    out = []
    for axis in AXES:
        for source in (score.get(axis) or {}).get("sources") or []:
            if str(source.get("accessed")) != date:
                continue
            url = str(source.get("url") or "")
            shows = " ".join(str(source.get("shows") or "").split())
            out.append({
                "axis": axis,
                "url": url,
                "accessed": date,
                "shows": shows,
                "looks_like_document": not NOT_A_DOCUMENT.search(url),
                "shows_is_measurement_only": bool(MEASUREMENT_ONLY.match(shows)),
            })
    # Deduplicate on URL, keeping the richest `shows`.
    best: dict[str, dict] = {}
    for c in out:
        if c["url"] not in best or len(c["shows"]) > len(best[c["url"]]["shows"]):
            best[c["url"]] = c
    return sorted(best.values(), key=lambda c: (not c["looks_like_document"], c["url"]))


def census() -> dict[str, list[str]]:
    by_state: dict[str, list[str]] = {}
    for slug, product in products().items():
        state, _, _ = classify(product.get("comments"))
        by_state.setdefault(state, []).append(slug)
    return by_state


def packets() -> list[dict]:
    """One decision packet per product needing evidence matching, decision left unset."""
    all_scores = scores()
    out = []
    for slug, product in products().items():
        state, date, trailer = classify(product.get("comments"))
        if state not in ("generic",):
            continue
        cands = candidates(slug, date, all_scores.get(slug) or {})
        usable = [c for c in cands if c["looks_like_document"] and not c["shows_is_measurement_only"]]
        out.append({
            "product": slug,
            "verification_date": date,
            "current_trailer": trailer,
            "description": " ".join(str(product.get("description") or "").split()),
            "candidates": cands,
            # A packet with no usable candidate cannot be derived from evidence, whatever a
            # reader thinks of it: there is no document in the record to name.
            "hint": "reread" if not usable else "needs-judgment",
            "decision": None,
            "selected_document": None,
            "source_url": None,
            "support": None,
            "reason": None,
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", help="write candidate decision packets to this path")
    args = parser.parse_args()

    by_state = census()
    total = sum(len(v) for v in by_state.values())
    print(f"{total} products\n")
    for state in ("canonical", "named_noncanonical", "generic", "missing"):
        n = len(by_state.get(state, []))
        print(f"  {state:22}{n:>5}")

    if args.packets:
        rows = packets()
        Path(args.packets).write_text(yaml.safe_dump(rows, sort_keys=False, allow_unicode=True))
        hints = {}
        for r in rows:
            hints[r["hint"]] = hints.get(r["hint"], 0) + 1
        print(f"\n{len(rows)} packets written to {args.packets}")
        for hint, n in sorted(hints.items()):
            print(f"  hint {hint:16}{n:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
