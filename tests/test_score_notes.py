"""A note that appears under two axes was written for one of them.

## Why this is a test rather than prose

`personahub` recorded capability 2 with `value: null` and `confidence: high`, and the note
under it argued CC-BY-NC-SA and the commercial-use test — an OPENNESS argument, verbatim the
openness note, pasted into the capability block when the openness score moved to 2 on
2026-08-01. The capability score followed it down. Nothing on that axis had been assessed.

A license says what you may do with a corpus. It says nothing about what training on it
produces. So the duplication is not a cosmetic problem: wherever it happened, one axis is
carrying a judgment made about a different question, and its SCORE is the openness score
wearing another name. `personahub` sat at 2 in a 38-product category where the next lowest was
3 — visible as an outlier, invisible as a cause.

It was already written down. The 2026-08-11 handoff lists "7 products carry one note
copy-pasted across all three axes" as an open item, in prose, which is exactly the form a
finding takes when it is about to happen again. This is the gate half.

## What this does and does not claim

It does NOT clear the backlog — resolving the seven means re-deriving a real judgment per axis
per product, which is its own pass. It freezes it: the known seven are named, and an eighth
fails the suite. `check_adoption` shipped the same way, non-strict against a declared backlog,
and the backlog shrank because it was counted.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from build.prose_allowlists import DATES_THAT_ARE_PRODUCT_FACTS, FIGURES_THAT_ARE_PRODUCT_FACTS
from build.prose_worklist import counts as prose_tell_counts, usage_figures
from build.validate import load_sources

AXES = ("openness", "adoption", "capability")

# The seven found on 2026-08-11, each carrying one note under two or more axes. Named
# individually so that fixing one is a one-line deletion here and adding an eighth is a
# failure. Do not add to this list to make the suite pass — that is the failure working.
# Five left the list on 2026-08-13, in the finetuned_chat re-read: codegemma, codellama,
# jamba-large, llama-instruct and tulu each had the openness note re-derived into a real
# capability or adoption judgment. `llama` and `personahub` are still outstanding.
KNOWN_SHARED_NOTES: set[str] = set()
"""EMPTY as of 2026-08-13, and the emptying is the point.

It held seven on the morning of 2026-08-13 — codegemma, codellama, jamba-large, llama,
llama-instruct, personahub, tulu. Every one was cleared by a category verification pass, not
by anybody working this list: rewriting a duplicated note is unavoidable once you actually
re-derive the axis it was pasted onto, and the ratchet below then failed until the slug came
out. Four different passes removed slugs without coordinating.

That is the argument for the shape of this test. The finding was written into a handoff note
first, where it sat and grew; written as a gate, it became a thing that had to be resolved to
make CI pass, and it resolved itself as a side effect of ordinary work.

Keep it empty. An eighth instance now fails the suite on arrival."""


@pytest.fixture(scope="module")
def sources():
    return load_sources(Path("."))


def shared_note_axes(score: dict) -> list[list[str]]:
    """Groups of axes sharing one note, whitespace-normalized.

    Normalized because the corpus is hand-wrapped: the same sentence re-wrapped at a
    different width is the same note, and comparing raw strings would miss exactly the
    copies that have since been edited around.
    """
    by_note: dict[str, list[str]] = {}
    for axis in AXES:
        note = ((score or {}).get(axis) or {}).get("note")
        if note:
            by_note.setdefault(" ".join(note.split()), []).append(axis)
    return [axes for axes in by_note.values() if len(axes) > 1]


def test_no_new_product_shares_one_note_across_axes(sources):
    found = {
        slug for slug, score in sources["scores"].items() if shared_note_axes(score)
    }
    new = found - KNOWN_SHARED_NOTES
    assert not new, (
        f"{sorted(new)} record one note under more than one axis. A note that argues about "
        f"licensing cannot also be the reason for an adoption band or a capability score — "
        f"whichever axis borrowed it has no judgment of its own recorded."
    )


def test_the_known_backlog_has_not_silently_grown_stale(sources):
    """A slug that no longer shares a note should leave the list, not linger in it.

    Otherwise the allowlist stops describing the backlog and starts hiding it — the list
    would keep passing long after the products were fixed, and the next real instance would
    have somewhere to hide.
    """
    still_sharing = {
        slug for slug in KNOWN_SHARED_NOTES if shared_note_axes(sources["scores"].get(slug))
    }
    resolved = KNOWN_SHARED_NOTES - still_sharing
    assert not resolved, (
        f"{sorted(resolved)} no longer share a note across axes — remove them from "
        f"KNOWN_SHARED_NOTES so the list keeps meaning what it says."
    )


# ── The note is not the verification log ────────────────────────────────────────────────────

VERIFICATION_PROSE = re.compile(r"Re-read|Re-checked|Re-fetched|Re-verified", re.I)


def _prose_fields(score: dict):
    """Every hand-written string on a score record that the payload publishes."""
    for axis in ("openness", "adoption", "capability"):
        block = score.get(axis) or {}
        if block.get("note"):
            yield f"{axis}.note", block["note"]
        for i, source in enumerate(block.get("sources") or []):
            if source.get("shows"):
                yield f"{axis}.sources[{i}].shows", source["shows"]


def test_no_score_prose_carries_a_verification_log(sources):
    """A note says why the score is what it is. It is not the log of who checked it and when.

    The payload publishes `note` and `sources[].shows` verbatim, and the product page renders
    them as the prose a visitor reads to understand a score. Between 2026-04 and 2026-08 the
    re-read passes appended their own narrative there — "Re-read 2026-08-13 - the source still
    says X. No change." — until it was 44% of all note prose, in 1,035 of 1,416 notes. Every
    fact those clauses stated was already a field on the same record: `last_verified`,
    `sources[].accessed`, `sources[].http_status`, `sources[].content_sha256`. The page already
    prints `Verified <date>` from the first of them.

    The history is not lost by keeping it out of the prose. The scoring history is the git
    history of the score file, which is complete, dated by commit, and needs no upkeep —
    `git log -p --follow sources/scores/<slug>.yaml`. See docs/reference/evidence-and-freshness.md.

    This is strict rather than a ratchet: the corpus was cleared in one pass (#322), so there is
    no backlog left to name, and an allowlist would only give the next instance somewhere to hide.
    """
    offenders = [
        f"{slug} {field}"
        for slug, score in sources["scores"].items()
        for field, text in _prose_fields(score)
        if VERIFICATION_PROSE.search(text)
    ]
    assert not offenders, (
        f"{len(offenders)} score prose fields carry a verification log:\n  "
        + "\n  ".join(sorted(offenders)[:20])
        + "\n\nA re-read that changed nothing leaves no trace in the note — that is what "
        "`last_verified` moving is for. A re-read that changed something edits the note to say "
        "the new durable thing, not to narrate the discovery."
    )


# ── No date in a note ───────────────────────────────────────────────────────────────────────

ISO_DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")

# The allowlist lives in build/prose_allowlists.py so prose_edit can refuse against it too.


def test_no_note_states_a_date_unless_it_is_a_product_fact(sources):
    """A note says why the score is what it is. A date says when somebody looked.

    #322 took the re-read log out of the notes and #323 took the score history out — "RE-BANDED
    2026-08-14", "Class corrected from open_core on 2026-07-30" — leaving the chronology to git,
    where it already lived with the diff and the digests that produced it.

    This guard is a DATE rule rather than a verb list, deliberately. The first pass guarded on
    `Re-read` and friends, and `Re-derived` rode through it 23 times: a vocabulary can always be
    escaped by picking a new word, and the next pass will pick one. What cannot be escaped is that
    a note about when something happened has to say when.

    `sources[].shows` is deliberately NOT covered. It quotes the source, and sources carry dates
    honestly — a GitHub `pushed_at`, a copyright year inside license text, "29 June 2007" inside
    the GPL, a model-snapshot identifier where the date IS the model's name.
    """
    offenders = [
        f"{slug} {axis}"
        for slug, score in sources["scores"].items()
        for axis in ("openness", "adoption", "capability")
        if (slug, axis) not in DATES_THAT_ARE_PRODUCT_FACTS
        and ISO_DATE.search(((score.get(axis) or {}).get("note")) or "")
    ]
    assert not offenders, (
        f"{len(offenders)} notes state a date:\n  " + "\n  ".join(sorted(offenders)[:20])
        + "\n\nWhen a score changed is git's to remember: `git log -p --follow "
        "sources/scores/<slug>.yaml`. If the date is a fact about the product rather than about "
        "the reading, add it to DATES_THAT_ARE_PRODUCT_FACTS with that justification."
    )


# ── Chronology with no date in it ───────────────────────────────────────────────────────────

# The date rule above rests on a premise that turned out to be false: that "a note about when
# something happened has to say when". It does not. "narrowed from the six models recorded
# previously" is chronology with no date in it and it rode through cleanly (#632).
#
# There is no gate here, and the absence is the finding. The distinction that matters is whose
# past a sentence describes -- the product's, which a note exists to state, or the record's,
# which belongs in git -- and no pattern draws it. The phrase in the violation above is the same
# phrase as in "The SDK previously recorded audio locally". A rule built on it also refuses "the
# free tier no longer includes API access" and "the previously released classifier", which are
# ordinary product facts.
#
# So `build.prose_edit` WARNS at the point of writing and the corpus carries no gate. What is
# tested here is that the warning fires on the real instance and stays quiet on product facts,
# which is all a heuristic of this shape can honestly promise.

from build.prose_edit import RECORD_CHRONOLOGY  # noqa: E402


def test_the_chronology_warning_fires_on_the_instance_that_prompted_it():
    """#632's counterexample. The warning is advisory, so this pins its sensitivity rather than
    any enforcement.
    """
    assert RECORD_CHRONOLOGY.search(
        "The base-model allowlist is now a single model, llama3.1-8b, narrowed from the six "
        "models recorded previously."
    )


def test_the_chronology_warning_stays_quiet_on_product_facts():
    """Each of these appears in the corpus and each is a fact about the world changing, which is
    what a note is for. A warning that fires on them is a warning people learn to ignore.
    """
    for allowed in (
        "the repository is no longer actively maintained",
        "CursorBench at 70% (up from 58% for Opus 4.6)",
        "Cosmopedia v2 has since superseded it",
        "Vercel, Dropbox and Replit no longer appear there",
        "Development responsibility has since passed from the original authors",
    ):
        assert not RECORD_CHRONOLOGY.search(allowed), allowed


def test_the_warning_is_not_a_gate_and_the_corpus_is_not_held_to_it():
    """Stated as a test so the decision is not quietly reversed by somebody reading the pattern
    and assuming it should block.

    Narrowing the record vocabulary did most of the work: dropping `band`, `tier`, `class` and
    `level N` stopped it matching "the free tier no longer includes API access", "the previously
    released classifier" and "Bandwidth is no longer limited", all of which are product facts.

    What survives is the one that cannot be fixed. "recorded" is both the record's word and an
    ordinary verb, so the phrase in #632's violation -- "the six models recorded previously" --
    is the same phrase as in "The SDK previously recorded audio locally". Separating them needs
    to know what the verb takes as its object, which is parsing, not matching. One false positive
    class that no narrowing removes is enough to keep this advisory.
    """
    ordinary_prose_that_still_matches = "The SDK previously recorded audio locally"
    assert RECORD_CHRONOLOGY.search(ordinary_prose_that_still_matches), (
        "the verb ambiguity has gone; if `recorded` can no longer match an ordinary verb phrase, "
        "re-examine whether this can be a gate after all"
    )
    for fixed_by_narrowing in (
        "The free tier no longer includes API access",
        "The previously released classifier supports French",
        "Bandwidth is no longer limited",
    ):
        assert not RECORD_CHRONOLOGY.search(fixed_by_narrowing), fixed_by_narrowing


def test_the_date_allowlist_has_not_gone_stale(sources):
    """An axis whose note no longer states a date must leave the allowlist, not linger in it.

    Otherwise the list stops describing the exceptions and starts hiding them: it would keep
    passing long after the dates were gone, and the next real instance would have somewhere to
    sit unnoticed. Same two-sided shape as
    test_the_known_backlog_has_not_silently_grown_stale above, and the same reason.
    """
    stale = [
        f"{slug} {axis}"
        for slug, axis in DATES_THAT_ARE_PRODUCT_FACTS
        if not ISO_DATE.search(((sources["scores"].get(slug, {}).get(axis) or {}).get("note")) or "")
    ]
    assert not stale, (
        f"{sorted(stale)} no longer state a date - remove them from "
        "DATES_THAT_ARE_PRODUCT_FACTS so the list keeps meaning what it says."
    )


def test_no_note_quotes_a_usage_figure_unless_it_is_a_product_fact(sources):
    """A star count, a download count, a user count in a note is stale the day the source line
    beneath it refreshes; the source line carries the figure with its date. The detector also
    reads a license threshold ("700 million monthly active users") or a dataset size as a
    figure; those are facts about the product and sit on FIGURES_THAT_ARE_PRODUCT_FACTS. This
    is the gate the worklist's `figure` tell was missing: without it a count comes back on the
    next update-product and CI stays green."""
    offenders = [
        f"{slug} {axis}: {figures}"
        for slug, score in sources["scores"].items()
        for axis in ("openness", "adoption", "capability")
        if (slug, axis) not in FIGURES_THAT_ARE_PRODUCT_FACTS
        and (figures := usage_figures(((score.get(axis) or {}).get("note")) or ""))
    ]
    assert not offenders, (
        f"{len(offenders)} notes quote a usage figure:\n  " + "\n  ".join(sorted(offenders)[:20])
        + "\n\nThe source line carries the number with its date; the note says what was measured "
        "and what it cannot show. A durable product fact the detector misreads goes on "
        "FIGURES_THAT_ARE_PRODUCT_FACTS with its justification."
    )


def test_the_figure_allowlist_has_not_gone_stale(sources):
    stale = [
        f"{slug} {axis}"
        for slug, axis in FIGURES_THAT_ARE_PRODUCT_FACTS
        if not usage_figures(((sources["scores"].get(slug, {}).get(axis) or {}).get("note")) or "")
    ]
    assert not stale, (
        f"{sorted(stale)} no longer quote a figure - remove them from "
        "FIGURES_THAT_ARE_PRODUCT_FACTS so the list keeps meaning what it says."
    )


# ── The note is written for the reader, not the auditor ─────────────────────────────────────
#
# #619 measured the corpus on 2026-09-17: 960 notes used the rubric's own words (rung, ladder,
# anchor, band 3, level 5, <name>_rule, abstain, instrument) and 306 ran past the 600-character
# guard the goldens in docs/reference/product-copy.md set. The pass that followed rewrote every
# one, category by category, with the two counts pinned as ratchets that could only fall. At
# zero the ratchets became this strict gate, the way the verification-line tests did.
# `build/prose_worklist.py` owns the detectors, so the worklist a pass works from and the gate
# that holds its result cannot disagree about what a tell is; a source line and a footnote are
# published beside the note, so they are held to the same words.


def test_no_published_prose_uses_the_rubric_vocabulary():
    c = prose_tell_counts()
    offenders = {k: c[k] for k in ("vocabulary", "shows_vocabulary", "footnote_vocabulary") if c.get(k)}
    assert not offenders, (
        f"{offenders}: notes, source lines or footnotes written in the rubric's words. Write for "
        "the reader who has never seen the rubric: docs/reference/product-copy.md has the plain "
        "equivalent for each word, and `uv run python -m build.prose_worklist --category <slug>` "
        "lists the rows."
    )


def test_no_note_runs_past_the_guard():
    measured = prose_tell_counts().get("length", 0)
    assert measured == 0, (
        f"{measured} note(s) run past 600 characters. A note argues the rung in two sentences; "
        "the detail belongs in `shows` and `components[].detail`. See the goldens in "
        "docs/reference/product-copy.md."
    )


def test_no_note_opens_on_a_template():
    measured = prose_tell_counts().get("opening", 0)
    assert measured == 0, (
        f"{measured} note(s) open on the rubric's template (\"Banded on the\", \"One band below\"). "
        "Open with the product and the fact."
    )


def test_prose_edit_warns_but_still_writes(tmp_path, monkeypatch, capsys):
    """The warning must not block the write. An advisory that refuses is a gate with a softer
    error message, and this one cannot be a gate -- see above.
    """
    import build.prose_edit as pe

    root = tmp_path
    (root / "sources" / "scores").mkdir(parents=True)
    path = root / "sources" / "scores" / "widget.yaml"
    path.write_text("openness:\n  note: The allowlist is a single model.\n")
    monkeypatch.setattr(pe, "ROOT", root)

    result = pe.edit_note("widget", "openness",
                          "The allowlist is now a single model, narrowed from the six recorded previously.")
    assert result is None, f"the warning must not refuse the write: {result}"
    assert "narrowed" in path.read_text(), "the note should have been written"
    assert "chronology about the RECORD" in capsys.readouterr().err
