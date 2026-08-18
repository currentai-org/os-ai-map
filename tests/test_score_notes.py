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
    ("amazon-bedrock-evaluations", "adoption"),
    ("apertus", "adoption"),
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
    ("playwright-mcp", "adoption"),
    ("ragflow", "adoption"),
    ("sambanova-cloud", "adoption"),
    ("sandbox-runtime", "adoption"),
    ("searxng", "adoption"),
    ("tinker", "capability"),
    ("vercel-sandbox", "adoption"),
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
