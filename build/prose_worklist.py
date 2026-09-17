"""Which notes read as written for the score auditor rather than the visitor, by category.

`docs/reference/product-copy.md` says a score note is written for a reader who has never seen
the rubric. Measured 2026-09-17, a third of the corpus was not: 879 of 2,289 notes used the
rubric's own words (rung, ladder, anchor, band 3), 963 restated an exact figure the source line
beneath already showed, and seventy opened with the same three words. Length was not the
defect; the audience was.

This module is the selector for the prose pass that fixes it, and the single owner of the
detectors, so `tests/test_score_notes.py` ratchets on the same definitions the worklist is
built from. Five tells per note, one per product:

  vocabulary   a rubric word: rung, ladder, anchor, band N, level N, <name>_rule, formula,
               abstain, instrument, "rests on", "measured, not inferred"
  figure       two or more comma-grouped or five-digit figures that also appear in a `shows`
               on the same axis, so the note is a table set as a sentence
  opening      a rubric-speak opening a single prompt wrote hundreds of times ("Banded on
               the", "One band below")
  retracting   the note corrects itself in place (`sweep_status.RETRACTING`)
  length       over the 600-character guard the goldens set
  comments     a product footnote whose vocabulary sits mostly in the notes already

None of these is a gate on its own. A note can say "anchor" and be fine; the worklist says
where to look, and the person or agent doing the pass decides. What IS gated, in
`tests/test_score_notes.py`, is that the vocabulary and length counts only go down.

Usage:
    uv run python -m build.prose_worklist                     # per-category counts
    uv run python -m build.prose_worklist --category ui_api   # the flagged notes, with tells
    uv run python -m build.prose_worklist --json > worklist.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from build.sweep_status import RETRACTING
from build.vocabulary import axes

ROOT = Path(__file__).resolve().parents[1]
AXES = axes()

#: The 600 comes from the goldens in product-copy.md: the longest rewritten note is 579.
NOTE_CEILING = 600

# Words that belong to the rubric, not to the reader. Each has a plain equivalent in
# product-copy.md's table. `band`/`level`/`rung` followed by a digit is the big one (422 notes);
# "level with" and "the 1M-10M band" do not match, deliberately, because those are English.
RUBRIC_VOCABULARY = re.compile(
    r"\b(?:rungs?|ladders?|anchors?)\b"
    r"|\b(?:band|level|rung) [0-5]\b"
    r"|\b\w+_rule\b|\bformula\b|\bcheck_\w+"
    r"|\babstain(?:s|ed|ing)?\b|\binstruments?\b"
    r"|\b(?:band|score|level) rests on\b"
    r"|\bmeasured,? not inferred\b",
    re.IGNORECASE,
)

# The first words of a note, where one prompt's habit shows AND the words are the rubric's:
# seventy notes opened "Banded on the", thirty-six "One|Two bands below". Deliberately not
# "Apache-2.0 license body confirmed" or "Fully OSI-licensed (MIT), full source public": those
# are short, factual and plain, sixty-eight products share the same facts, and the pilot pass
# that flagged them replaced each with the same 330-character paragraph, name swapped, which
# was the defect wearing a new coat. A short factual note is left alone.
TEMPLATE_OPENINGS = re.compile(
    r"^(?:banded on|one band below|two bands below|one tier below|admitted on the)",
    re.IGNORECASE,
)

# A figure a reader would take as a measurement: comma-grouped, or five or more digits. Not a
# decimal, because a benchmark score in the note and in the source is a claim and its evidence,
# which is the right shape.
FIGURE = re.compile(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{5,}\b")


def _scores() -> dict[str, dict]:
    return {
        p.stem: (yaml.safe_load(p.read_text()) or {})
        for p in sorted((ROOT / "sources" / "scores").glob("*.yaml"))
    }


def _products() -> dict[str, dict]:
    return {
        p.stem: (yaml.safe_load(p.read_text()) or {})
        for p in sorted((ROOT / "sources" / "products").glob("*.yaml"))
    }


def _category_of() -> dict[str, str]:
    out = {}
    for p in (ROOT / "sources" / "categories").glob("*.yaml"):
        doc = yaml.safe_load(p.read_text()) or {}
        for slug in doc.get("products") or []:
            out[slug] = p.stem
    return out


def vocabulary_hits(note: str) -> list[str]:
    return [m.group(0) for m in RUBRIC_VOCABULARY.finditer(note or "")]


def duplicated_figures(note: str, shows: list[str]) -> list[str]:
    """Figures in the note that a `shows` on the same axis already carries, verbatim or with
    the thousands separators removed."""
    haystack = " ".join(shows)
    bare = haystack.replace(",", "")
    return [
        f for f in FIGURE.findall(note or "")
        if f in haystack or f.replace(",", "") in bare
    ]


def note_tells(axis_block: dict) -> dict[str, object]:
    """The tells for one axis block, empty when the note is clean by every detector."""
    note = axis_block.get("note") or ""
    if not note:
        return {}
    shows = [s.get("shows") or "" for s in axis_block.get("sources") or []]
    tells: dict[str, object] = {}
    if (v := vocabulary_hits(note)):
        tells["vocabulary"] = v
    # One figure restated is a claim with its evidence beneath it, which is the right shape.
    # Two or more is a table set as a sentence.
    if len(f := duplicated_figures(note, shows)) >= 2:
        tells["figure"] = f
    if TEMPLATE_OPENINGS.search(note.strip()):
        tells["opening"] = note.strip().split(".")[0][:40]
    if (m := RETRACTING.search(note)):
        tells["retracting"] = m.group(0)
    if len(note) > NOTE_CEILING:
        tells["length"] = len(note)
    return tells


def comments_overlap(comments: str, notes: list[str]) -> float:
    """Share of the footnote's distinctive words that already appear in the product's notes."""
    words = set(re.findall(r"[a-z]{5,}", (comments or "").lower()))
    if not words:
        return 0.0
    body = " ".join(notes).lower()
    return sum(1 for w in words if w in body) / len(words)


def worklist() -> dict[str, list[dict]]:
    """category -> rows of {slug, axis, tells} for flagged notes, plus {slug, comments} rows
    for footnotes that restate the notes."""
    scores, products, cat_of = _scores(), _products(), _category_of()
    out: dict[str, list[dict]] = defaultdict(list)
    for slug, score in scores.items():
        category = cat_of.get(slug, "?")
        for axis in AXES:
            tells = note_tells(score.get(axis) or {})
            if tells:
                out[category].append({"slug": slug, "axis": axis, "tells": tells})
        comments = (products.get(slug) or {}).get("comments") or ""
        notes = [(score.get(a) or {}).get("note") or "" for a in AXES]
        if comments and comments_overlap(comments, notes) > 0.6:
            out[category].append({"slug": slug, "axis": "comments",
                                  "tells": {"restates_notes": round(comments_overlap(comments, notes), 2)}})
    return dict(out)


def counts() -> dict[str, int]:
    """Corpus-wide counts per tell, the numbers the ratchet tests pin."""
    scores = _scores()
    c: Counter[str] = Counter()
    for score in scores.values():
        for axis in AXES:
            for tell in note_tells(score.get(axis) or {}):
                c[tell] += 1
    return dict(c)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--category", help="list the flagged notes in one category")
    parser.add_argument("--json", action="store_true", help="the whole worklist as JSON")
    args = parser.parse_args()

    work = worklist()
    if args.json:
        print(json.dumps(work, indent=1, sort_keys=True))
        return 0
    if args.category:
        rows = work.get(args.category, [])
        print(f"{args.category}: {len(rows)} flagged")
        for row in sorted(rows, key=lambda r: (r["slug"], r["axis"])):
            tells = ", ".join(f"{k}={v}" for k, v in row["tells"].items())
            print(f"  {row['slug']:34} {row['axis']:12} {tells}")
        return 0

    total = counts()
    print("tell        notes")
    for tell in ("vocabulary", "figure", "opening", "retracting", "length"):
        print(f"  {tell:10}{total.get(tell, 0):6}")
    print(f"\n{'category':32}{'flagged':>8}{'files':>7}")
    for category, rows in sorted(work.items(), key=lambda kv: -len(kv[1])):
        files = len({r["slug"] for r in rows})
        print(f"{category:32}{len(rows):8}{files:7}")
    print(f"{'TOTAL':32}{sum(len(r) for r in work.values()):8}"
          f"{len({r['slug'] for rows in work.values() for r in rows}):7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
