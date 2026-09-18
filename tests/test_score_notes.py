"""A note that appears under two axes was written for one of them.

## Why this is a test rather than prose

`personahub` recorded capability 2 with `value: null` and `confidence: high`, and the note
under it argued CC-BY-NC-SA and the commercial-use test — an OPENNESS argument, verbatim the
openness note, pasted into the capability block when the openness score moved to 2 on
2026-08-01. The capability score followed it down. Nothing on that axis had been assessed.

A licence says what you may do with a corpus. It says nothing about what training on it
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

from build.prose_worklist import counts as prose_tell_counts
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

# Axes whose note states a date that is a fact about the PRODUCT or the SOURCE, not about when
# somebody looked: a GA or ship date, an archive date, a measurement window, a retirement date.
# Each was reviewed when the score-history sweep (#323) ran. Adding to this list is a claim that
# the date would still be true if nobody ever re-read the record.
DATES_THAT_ARE_PRODUCT_FACTS = {
    # --- Model Context Protocol specification revisions, added 2026-09-17 with the
    # agent_protocols category. These dates are the NAMES OF SPECIFICATION VERSIONS -
    # 2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25, 2026-07-28 - and the category's ladder
    # requires every implementation to name the revision its coverage was read against, because
    # band 5 asks for the current one. The date is the product's own version string, true
    # whether or not anybody re-reads the record, and removing it would delete the denominator
    # the band is computed from. `mcp-apps` carries its own extension spec version, 2026-01-26.
    ("mcp-apps", "capability"),
    ("mcp-go", "capability"),
    ("mcp-go-sdk", "capability"),
    ("mcp-java-sdk", "capability"),
    ("mcp-python-sdk", "capability"),
    ("mcp-rust-sdk", "capability"),
    ("mcp-swift-sdk", "capability"),
    ("mcp-typescript-sdk", "capability"),
    # `model-context-protocol` states the date its governance moved to the Linux Foundation's
    # AAIF, which is a fact about the project rather than about the reading.
    ("model-context-protocol", "capability"),
    ("amazon-bedrock-evaluations", "adoption"),
    ("apertus", "adoption"),
    # A release date on each side of a trailing registry line. The whole reason the band does
    # not rest on the download figure is that the registry stopped at 1.0.4 in June while the
    # repository is on 2.1.0 from August; drop the dates and the note asserts a lag it can no
    # longer show. Both are publication facts, true whether or not anybody re-reads them.
    ("areal", "adoption"),
    ("apertus", "openness"),
    ("atropos", "adoption"),
    ("claude-haiku", "capability"),
    ("claude-sonnet", "capability"),
    ("claude-sonnet", "openness"),
    ("cloudflare-sandboxes", "adoption"),
    ("compar-ia", "adoption"),
    ("cruxeval", "adoption"),
    ("google-coral-dev-board", "adoption"),
    ("khoj", "openness"),
    ("kimi", "adoption"),
    ("langflow", "adoption"),
    ("localai", "adoption"),
    ("mmmu", "openness"),
    ("n8n", "adoption"),
    ("open-llm-leaderboard", "adoption"),
    ("perplexica", "adoption"),
    ("ragflow", "adoption"),
    ("sandbox-runtime", "adoption"),
    ("vercel-sandbox", "adoption"),
    # Same shape as areal: the PyPI upload of 2025-07-11 and the v1.0.1 release of 2026-05-15
    # are the two publication dates the 416-day gap is measured between.
    ("xtuner", "adoption"),
}


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
    honestly — a GitHub `pushed_at`, a copyright year inside licence text, "29 June 2007" inside
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


# ── The note is written for the reader, not the auditor ─────────────────────────────────────
#
# #619 measured the corpus on 2026-09-17: 960 notes used the rubric's own words (rung, ladder,
# anchor, band 3, level 5, <name>_rule, abstain, instrument) and 306 ran past the 600-character
# guard the goldens in docs/reference/product-copy.md set. Both counts are pinned here and may
# only fall. `build/prose_worklist.py` owns the detectors, so the worklist the pass works from
# and the ratchet that holds its result cannot disagree about what a tell is.
#
# A ratchet rather than a strict gate, because the pass runs one category per commit and the
# corpus is between states until it finishes. Lower each pin as a category lands; at zero,
# replace the pair with a strict assertion, the way the verification-line tests did.

RUBRIC_VOCABULARY_BACKLOG = 806
OVERLONG_NOTE_BACKLOG = 278


def test_rubric_vocabulary_in_notes_only_goes_down():
    measured = prose_tell_counts().get("vocabulary", 0)
    assert measured <= RUBRIC_VOCABULARY_BACKLOG, (
        f"{measured - RUBRIC_VOCABULARY_BACKLOG} more note(s) use rubric vocabulary than the pin "
        "allows. Write for the reader who has never seen the rubric: docs/reference/product-copy.md "
        "has the plain equivalent for each word. `uv run python -m build.prose_worklist --category "
        "<slug>` lists them."
    )


def test_overlong_notes_only_go_down():
    measured = prose_tell_counts().get("length", 0)
    assert measured <= OVERLONG_NOTE_BACKLOG, (
        f"{measured - OVERLONG_NOTE_BACKLOG} more note(s) run past 600 characters than the pin "
        "allows. A note argues the rung in two sentences; the detail belongs in `shows` and "
        "`components[].detail`. See the goldens in docs/reference/product-copy.md."
    )


def test_the_prose_pins_have_not_silently_gone_stale():
    """Measured must equal recorded, or the slack becomes room for the next regression. Same
    two-sided shape as the allowlists above."""
    c = prose_tell_counts()
    assert c.get("vocabulary", 0) == RUBRIC_VOCABULARY_BACKLOG, (
        f"{c.get('vocabulary', 0)} notes use rubric vocabulary; RUBRIC_VOCABULARY_BACKLOG says "
        f"{RUBRIC_VOCABULARY_BACKLOG}. Record the new count."
    )
    assert c.get("length", 0) == OVERLONG_NOTE_BACKLOG, (
        f"{c.get('length', 0)} notes are over the guard; OVERLONG_NOTE_BACKLOG says "
        f"{OVERLONG_NOTE_BACKLOG}. Record the new count."
    )
