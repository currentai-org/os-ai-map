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
| `ambiguous_noncanonical` | dated, but no document identifiable — `Verified 2026-08-13.` | read the record |
| `generic` | names a METHOD — `primary sources`, `research`, `web search` | evidence matching, or a re-read |
| `missing` | no dated verification line at all | research |

`generic` is the substantive one, and `product-copy.md` rules it out by name: those words
"describe how you looked rather than what settled it, and leave the next editor nothing to
re-open". Rewording cannot repair them; something has to supply the document.

## Why deriving from score sources is a repair rather than a new claim

Each product's score file records the exact URLs fetched, dated and digested. Where one was
accessed **on the date the prose line already claims**, and its `shows` describes the product
rather than a score dimension, that document is what a reader would have to reopen — naming
it states what the repository already proves was read. Measured 2026-08-15, all 172 `generic`
products have at least one date-aligned source, so date alignment alone decides nothing; the
judgment is entirely whether the source is a nameable, authoritative document that supports
the prose.

**This module does not make that judgment.** It gathers the candidates, applies mechanical
hints, and emits a packet per product for a reviewer to settle. `build/apply_provenance.py`
then writes only the packets marked `derive`.

## The candidate packet file is derived, and is not committed

Every field in it comes from the corpus, so a committed copy is a second copy of a fact the
corpus already carries — it drifts the moment a product or score changes and has no parity
gate. Generate it on demand. What IS committed is a decision manifest under
`sources/provenance/<category>.yaml`, because those carry human judgment that exists nowhere
else, split by category so a reviewer reads one batch at a time.

Usage:
    uv run python -m build.prose_provenance                 # the five-state census
    uv run python -m build.prose_provenance --packets FILE  # candidate packets, on demand
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

from build.vocabulary import axes

ROOT = Path(__file__).resolve().parents[1]
AXES = axes()  # build/vocabulary.py owns this; the score schema declares it

CANONICAL = re.compile(r"Verified (\d{4}-\d{2}-\d{2}) via ")
# Any dated verification, however it is worded. The corpus carries `Verified live <date> via`,
# `Verified live <date> on`, `... against`, and lowercase `verified`.
ANY_DATED = re.compile(r"[Vv]erified[^.]{0,45}?(\d{4}-\d{2}-\d{2})")
# What follows the date, which is where a document name would be. The preposition is
# REQUIRED here: a line that just says "Verified 2026-08-13." names nothing, and treating the
# rest of the sentence as a document is how the census would claim more than it checked.
TRAILER = re.compile(r"[Vv]erified[^.]{0,45}?\d{4}-\d{2}-\d{2}[,;]?\s*(?:via|on|against|using)\s+(.*)")

# Words that name a METHOD rather than a document. product-copy.md forbids these outright.
# A leading article is allowed because "the primary sources" is the same claim as "primary
# sources" and would otherwise slip through as a document name.
METHOD_WORDS = re.compile(
    r"^\s*(?:the\s+|a\s+|our\s+)?"
    r"(primary[- ]sources?|primary-source research|research|web ?search|search|"
    r"substitute sources|desk research|secondary sources?)\b",
    re.IGNORECASE,
)

# The dated clause in any of its wordings, removed before digesting the surrounding prose.
CLAUSE_ANY = re.compile(
    r"[Vv]erified(?: live)?\s+\d{4}-\d{2}-\d{2}\s*[,;]?\s*(?:via|on|against|using)?\s*[^.;]*[.;]?"
)

# A document name has to contain an actual word. `Verified 2026-08-13 via .` is canonical in
# shape and names nothing.
HAS_WORD = re.compile(r"[A-Za-z0-9]")

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
    """(state, date, trailer) for one product's comments.

    **The trailer is tested before the form.** An earlier cut checked `CANONICAL` first and
    returned, so `Verified 2026-08-13 via primary sources.` classified as `canonical` — the
    correct shape wrapped around the exact thing this classifier exists to find, which is
    this module's own subject turned on itself.

    It was latent on the corpus (zero canonical-form lines named a method) and not latent in
    the migration: the first cut of the class-A rewording removed `live` from four hardware
    records reading `via substitute sources`, promoting them into canonical form while they
    still named a method. `generic` now wins over `canonical` whenever the trailer is a
    method, however the line is worded.
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
    # be re-derived` are dated and not methods, and neither names anything to reopen —
    # `meta-ai` and `le-chat` are the corpus cases. Defaulting those to `named_noncanonical`
    # would promise a mechanical fix that does not exist, which is the same overstatement
    # this census was built to remove.
    if not trailer or not HAS_WORD.search(trailer):
        return "ambiguous_noncanonical", dated.group(1), trailer
    if CANONICAL.search(text):
        return "canonical", CANONICAL.search(text).group(1), trailer
    return "named_noncanonical", dated.group(1), trailer


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


def prose_digest(product: dict) -> str:
    """A digest over the prose a verification line is provenance for.

    `product-copy.md` defines the line as editorial provenance for BOTH `description` and
    `comments`, so both are covered. The dated clause itself is removed first: it is the thing
    being rewritten, and including it would make every packet invalid the moment it applied.

    Normalized on whitespace so a reflow — which `set_document_field` performs on every write
    — does not read as a change of claim.
    """
    import hashlib

    description = " ".join(str(product.get("description") or "").split())
    comments = " ".join(str(product.get("comments") or "").split())
    stripped = CLAUSE_ANY.sub("", comments).strip()
    return hashlib.sha256(f"{description}\x00{stripped}".encode()).hexdigest()


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
            "comments": " ".join(str(product.get("comments") or "").split()),
            "prose_digest": prose_digest(product),
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
    for state in ("canonical", "named_noncanonical", "ambiguous_noncanonical",
                  "generic", "missing"):
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
