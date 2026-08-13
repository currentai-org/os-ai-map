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

from pathlib import Path

import pytest

from build.validate import load_sources

AXES = ("openness", "adoption", "capability")

# The seven found on 2026-08-11, each carrying one note under two or more axes. Named
# individually so that fixing one is a one-line deletion here and adding an eighth is a
# failure. Do not add to this list to make the suite pass — that is the failure working.
KNOWN_SHARED_NOTES = {
    "codegemma",
    "codellama",
    "jamba-large",
    "llama",
    "llama-instruct",
    "tulu",
}


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
