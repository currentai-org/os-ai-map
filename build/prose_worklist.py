"""Which notes read as written for the score auditor rather than the visitor, by category.

`docs/reference/product-copy.md` says a score note is written for a reader who has never seen
the rubric. Measured 2026-09-17, a third of the corpus was not: 879 of 2,289 notes used the
rubric's own words (rung, ladder, anchor, band 3), 963 restated an exact figure the source line
beneath already showed, and seventy opened with the same three words. Length was not the
defect; the audience was.

This module was the selector for the pass that fixed it (#620, one commit per category) and
stays the single owner of the detectors, so `tests/test_score_notes.py` gates on the same
definitions the worklist is built from. Five tells per note, one per source line, two per
footnote:

  vocabulary   a rubric word or the scorer's shorthand: rung, ladder, anchor, band N, level N,
               <name>_rule, formula, abstain, instrument, "rests on", "measured, not
               inferred", "holds it at", "stands in", "is read the same way", "a band lower",
               "banded at", and the map's machinery named as a noun ("on this dimension",
               "this axis measures", "the top of the scale", "the next level up")
  figure       a usage figure (stars, downloads, users) or a bare comma-grouped count; it is
               stale the day the source refreshes and belongs in the source line. A durable
               product fact with a number (a context window, a benchmark score, a license's
               user threshold) is exempt where the unit says so and otherwise an accepted
               misread, listed and left
  opening      a rubric-speak opening a single prompt wrote hundreds of times ("Banded on
               the", "One band below")
  retracting   the note corrects itself in place (`sweep_status.RETRACTING`); a state fact
               ("superseded by", "withdrawn from circulation") trips it and is left
  length       over the 600-character guard the goldens set
  shape        under the guard but over 400 characters or two sentences: the issue's "one or two
               sentences for the rung", advisory because the goldens themselves run longer where
               the argument needs it
  shows_vocabulary    a source line written in the rubric's words rather than as an extract
  description  a description that refers to this record or the map, speaks as "we" or to "you",
               carries a date, a rubric word or a usage figure
  comments     a product footnote whose vocabulary sits mostly in the notes already
               (`restates_notes`), or one written in the rubric's words (`vocabulary`)

Figure and retracting are advisory: the worklist says where to look, and the person or agent
doing the pass decides. Vocabulary in any of the three published fields, length and opening
are gated at zero in `tests/test_score_notes.py`.

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
    r"|\bmeasured,? not inferred\b"
    # The scorer's shorthand a normal writer would not produce, named by the editor who read
    # the goldens: each is a place where a subject and a verb would have done.
    r"|\bholds? (?:it|this|the \w+) at\b|\bstands? in\b|\b(?:is|are) read the same way\b"
    r"|\ba band (?:lower|higher|below|above)\b|\b(?:at |of )?this band\b|\badjacent bands\b|\bcountable channel\b"
    r"|\bstar-based\b"
    # The map's own machinery named as a noun: "this dimension asks for", "the top of the
    # scale", "the next level up". A reader sees a product, not an axis.
    r"|\bthis (?:dimension|scale|axis) (?:asks|measures|scores|rewards|counts|reads)\b"
    r"|\b(?:on|for|along|against) this (?:dimension|scale|axis)\b"
    r"|\b(?:top|middle|bottom) of (?:this|the) (?:\w+ )?scale\b"
    r"|\bthe next (?:level|band|tier|rung) (?:up|down)\b"
    r"|\bbanded (?:at|on|against)\b"
    # The rung described as a place the product is admitted to: "the top level is reserved
    # for", "clears the threshold for this reading", "the checkpoint the openness score covers".
    r"|\b(?:top|next|higher|highest) (?:level|tier|rung|band),? (?:is )?reserved for\b"
    r"|\bthreshold for (?:this|the|a) (?:reading|score|band|level)\b"
    r"|\b(?:openness|adoption|capability) score covers\b"
    r"|\baxis (?:weighs|follows|rests|reads|scores|measures|asks|counts|resolves|abstains)\b"
    # The score named as a number in the prose ("Scored 4 rather than 5", "puts this at 1"),
    # the instrument named ("scored on the feature matrix"), and the pass narrating itself
    # ("the LICENSE body was read in full", "an earlier reading leaned on"). A random sample of
    # finished pages turned these up in notes the first detectors had not flagged.
    r"|\b(?:scored|score of|puts? (?:this|it) at|sits at|held at|caps? at|capped at|lands? (?:this |it )?at|places? (?:this |it )?at) [0-5]\b"
    r"|\bat [0-5], (?:closed|open|gated|restricted|source[- ]available|open[- ]core|open[- ]weights)\b"
    r"|\bfeature matrix\b|\b(?:was|were) read in full\b"
    r"|\ban earlier (?:reading|pass|draft)\b|\bthis category (?:scores|rates|holds)\b",
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

# A usage figure: stars, downloads, pulls, users, customers, with or without a k/M/million
# shorthand and with up to two words (GitHub, Hugging Face, PyPI) between the number and the
# noun; or a bare comma-grouped or five-digit count, which in a note is nearly always one. Such
# a figure is stale the day the source refreshes; it belongs in the source line with its date.
# A benchmark score, a latency, a parameter count or a context window is a fact about the
# product and is not matched.
FIGURE = re.compile(
    # The lookbehind keeps a version number out: `Apache-2.0 license and installs` is not a
    # count, and the pilot polish tripped on exactly that.
    r"(?<![A-Za-z0-9.-])\d[\d,.]*\s*(?:k|K|M|million|billion|thousand)?\s+(?:[A-Za-z-]+\s+){0,2}"
    r"(?:stars?|stargazers|downloads?|pulls?|installs?|users?|customers?|deployments?|forks?)\b"
    # A bare comma-grouped or five-digit count, unless it is a product dimension or a
    # measured property: a token limit, a parameter count, an embedding size, a context
    # window, a throughput, a latency, a percentage.
    r"|(?<!per )(?<!per-)(?<!/)\b\d{1,3}(?:,\d{3})+\b(?!,\d)(?![\s-]*(?:(?:output |input )?tokens?|RPM|requests?|calls?|pages?|queries|GPUs?|H100|param|dimension|context|d\b|tok/s|t/s|TFLOP|ms\b|seconds?|per second|%|hours?|steps?))"
    r"|(?<!per )(?<!per-)(?<!/)\b\d{5,}\b(?![\s-]*(?:(?:output |input )?tokens?|RPM|requests?|calls?|pages?|queries|GPUs?|H100|param|dimension|context|tok/s|t/s|TFLOP|ms\b|seconds?|per second|%|hours?|steps?))"
)

# The shape the issue asked for: one or two sentences for the rung. The goldens run to 595
# characters and five sentences where the argument needs them, so this is a selector, not a
# gate; the pass reads each one and keeps a third sentence that carries a fact.
SHAPE_CHARS = 400
SHAPE_SENTENCES = 2

# A description talks about the product. One that talks about this record, the map, or the
# reader ("we", "you") is written for the wrong audience.
SELF_REFERENCE = re.compile(
    r"\bthis (?:record|entry|product record)\b|\b(?:on |across )?(?:this|the) map\b"
    r"|\bscore note\b|\bscored (?:separately|here)\b|\bproduct scored\b|\bis scored\b"
    r"|\btime of scoring\b|\bmeasured release\b",
    re.IGNORECASE,
)
VOICE = re.compile(r"\b(?:we|our|ours|you|your|yours)\b", re.IGNORECASE)

# A band range or a band rank stated as prose. The Reach row carries the range; a note that
# repeats it is the rubric talking, and a rank against the category is false the day a
# product is added.
BAND_RANGE = re.compile(
    r"\b(?:the |a )?(?:top|bottom|lowest|highest|second|middle) (?:adoption |download |star )?band\b"
    r"|\b[<>]?\d[\dKkMm.,]*(?:\s*(?:-|to)\s*\d[\dKkMm.,]*)?\+?\s+(?:download |adoption |star |usage )?band\b"
    r"|\bthe most (?:in|of) (?:this|the|its) category\b",
    re.IGNORECASE,
)


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


# "band" as the name of a score: "the adoption band", "one band below vLLM", "nothing to band
# on", "adoption bands on stars". A spectral band in satellite imagery and the stats strip a
# vendor page calls a "stat band" are English and stripped first.
BAND_NOUN = re.compile(
    r"\b(?:adoption|capability|openness|usage|download|customer|reach|higher|lower|same|low|top|old"
    r"|recorded|current|(?:one|two|a|the|its|this|that)(?: \w+)?) bands?\b"
    r"|\bbands? (?:on|at|where|below|above|holds|does not|is |was |still|reads|rests|stands|routes|has"
    r"|floor|re-derived|read on|set on|scored on)\b"
    r"|\bto band\b|\bbands?[.,;]|\b\w+'s band\b|\bbands (?:in|are) ",
    re.IGNORECASE,
)
BAND_ENGLISH = re.compile(
    r"\b(?:\d+|six|spectral|multispectral|hyperspectral|S2|Sentinel|HLS|SRTM|ERA5|frequency)[- ]bands?\b"
    r"|\bbands? (?:are supplied|metadata|plus Dynamic)|\bstat band\b|\bwavelengths?\b",
    re.IGNORECASE,
)


def vocabulary_hits(note: str) -> list[str]:
    text = note or ""
    found = [m for pat in (RUBRIC_VOCABULARY, BAND_RANGE) for m in pat.finditer(text)]
    taken = [(m.start(), m.end()) for m in found]
    plain = BAND_ENGLISH.sub(lambda m: " " * len(m.group(0)), text)
    for m in BAND_NOUN.finditer(plain):
        if not any(a < m.end() and m.start() < b for a, b in taken):
            found.append(m)
    return [m.group(0).strip(".,; ") for m in sorted(found, key=lambda m: m.start())]


def usage_figures(note: str) -> list[str]:
    """Usage figures stated in the note. The source line beneath carries the number with its
    date; a note that repeats it goes stale the day the source refreshes."""
    return [m.group(0) for m in FIGURE.finditer(note or "")]


def note_tells(axis_block: dict) -> dict[str, object]:
    """The tells for one axis block, empty when the note is clean by every detector."""
    note = axis_block.get("note") or ""
    if not note:
        return {}
    tells: dict[str, object] = {}
    if (v := vocabulary_hits(note)):
        tells["vocabulary"] = v
    if (f := usage_figures(note)):
        tells["figure"] = f
    if TEMPLATE_OPENINGS.search(note.strip()):
        tells["opening"] = note.strip().split(".")[0][:40]
    if (m := RETRACTING.search(note)):
        tells["retracting"] = m.group(0)
    if len(note) > NOTE_CEILING:
        tells["length"] = len(note)
    elif len(note) > SHAPE_CHARS or sentence_count(note) > SHAPE_SENTENCES:
        tells["shape"] = [len(note), sentence_count(note)]
    return tells


def sentence_count(text: str) -> int:
    return len(re.findall(r"[.!?](?:\s|$)", text or ""))


def description_tells(text: str) -> dict[str, object]:
    """The tells for a product description: written about the product, for the reader, once."""
    if not text:
        return {}
    tells: dict[str, object] = {}
    if (m := SELF_REFERENCE.findall(text)):
        tells["self_reference"] = m
    if (m := VOICE.findall(re.sub(r"\bYou\.com\b", "", text))):
        tells["voice"] = m
    if (m := re.findall(r"\b20\d\d-\d\d-\d\d\b", text)):
        tells["date"] = m
    # "Texas Instruments", the verb "instruments an application", an OCR product's "formula
    # recognition" and the benchmark subset "MATH Level 5" are English, not the rubric's nouns.
    plain = re.sub(r"Texas Instruments|\b(?:auto-)?instruments? (?:an?|the|your|any|every|applications?|code|calls|models?|LLM)\b"
                   r"|\bformulas? (?:recognition|extraction|detection|parsing|understanding|and|or)\b"
                   r"|\b(?:math(?:ematical)?|chemical|table,) formulas?\b|\bMATH Level [1-5]\b"
                   r"|\b(?:and|these|its|those|onboard|scientific|imaging|the|(?-i:[A-Z]{2,})) instruments'?\b",
                   "", text, flags=re.IGNORECASE)
    if (v := vocabulary_hits(plain)):
        tells["vocabulary"] = v
    if (f := usage_figures(text)):
        tells["figure"] = f
    if len(text) > NOTE_CEILING:
        tells["length"] = len(text)
    return tells


def comments_overlap(comments: str, notes: list[str]) -> float:
    """Share of the footnote's distinctive words that already appear in the product's notes."""
    words = set(re.findall(r"[a-z]{5,}", (comments or "").lower()))
    if not words:
        return 0.0
    body = " ".join(notes).lower()
    return sum(1 for w in words if w in body) / len(words)


def worklist() -> dict[str, list[dict]]:
    """category -> rows of {slug, axis, tells} for flagged notes, {slug, axis, shows_vocabulary}
    rows for source lines written in the rubric's words, and {slug, comments} rows for footnotes
    that restate the notes or use those words. Every one of these fields is published."""
    scores, products, cat_of = _scores(), _products(), _category_of()
    out: dict[str, list[dict]] = defaultdict(list)
    for slug, score in scores.items():
        category = cat_of.get(slug, "?")
        for axis in AXES:
            tells = note_tells(score.get(axis) or {})
            if tells:
                out[category].append({"slug": slug, "axis": axis, "tells": tells})
            for i, src in enumerate((score.get(axis) or {}).get("sources") or []):
                if (v := vocabulary_hits(src.get("shows") or "")):
                    out[category].append({"slug": slug, "axis": axis,
                                          "tells": {"shows_vocabulary": [i, v]}})
        comments = (products.get(slug) or {}).get("comments") or ""
        notes = [(score.get(a) or {}).get("note") or "" for a in AXES]
        ctells: dict[str, object] = {}
        if comments and comments_overlap(comments, notes) > 0.6:
            ctells["restates_notes"] = round(comments_overlap(comments, notes), 2)
        if comments and (v := vocabulary_hits(comments)):
            ctells["vocabulary"] = v
        if ctells:
            out[category].append({"slug": slug, "axis": "comments", "tells": ctells})
        if (dtells := description_tells((products.get(slug) or {}).get("description") or "")):
            out[category].append({"slug": slug, "axis": "description", "tells": dtells})
    return dict(out)


def counts() -> dict[str, int]:
    """Corpus-wide counts per tell, the numbers the ratchet tests pin."""
    scores, products = _scores(), _products()
    c: Counter[str] = Counter()
    for slug, score in scores.items():
        for axis in AXES:
            for tell in note_tells(score.get(axis) or {}):
                c[tell] += 1
            for src in (score.get(axis) or {}).get("sources") or []:
                if vocabulary_hits(src.get("shows") or ""):
                    c["shows_vocabulary"] += 1
        if vocabulary_hits((products.get(slug) or {}).get("comments") or ""):
            c["footnote_vocabulary"] += 1
        for tell in description_tells((products.get(slug) or {}).get("description") or ""):
            c[f"description_{tell}"] += 1
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
    for tell in ("vocabulary", "figure", "opening", "retracting", "length", "shape",
                 "shows_vocabulary", "footnote_vocabulary", "description_self_reference",
                 "description_voice", "description_date", "description_vocabulary",
                 "description_figure", "description_length"):
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
