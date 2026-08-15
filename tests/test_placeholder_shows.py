"""A `shows` field has to say what the page shows, not that a batch ran.

29 sources across the 13 flagship score files recorded their evidence as the literal string
`flagship phase-C verification source`. Nothing caught it, and nothing could: `check_verification`'s
`digests` gate asks whether a source was FETCHED and `check_refetch` asks whether it is still
fetchable. A placeholder passes both, because both read the metadata around the claim rather
than the claim.

Three of the 29 were re-fetched and re-digested on 2026-08-13 with the string copied forward,
so this is not a legacy shape that decays on its own — a recent pass reproduced it. Hence a gate.
"""

from __future__ import annotations

import yaml

from build.check_verification import PLACEHOLDER_SHOWS, ROOT, placeholder_shows


def _scores() -> dict:
    return {
        p.stem: yaml.safe_load(p.read_text()) or {}
        for p in sorted((ROOT / "sources" / "scores").glob("*.yaml"))
    }


def test_no_source_records_a_batch_marker():
    problems = placeholder_shows(_scores())
    assert not problems, "\n  ".join(["placeholder `shows` values:"] + problems)


def test_the_gate_catches_one_when_it_is_there():
    """A green gate over a corpus that is already clean proves nothing about the gate."""
    marker = next(iter(PLACEHOLDER_SHOWS))
    planted = {"widget": {"openness": {"sources": [{"url": "https://example.com", "shows": marker}]}}}
    assert placeholder_shows(planted)


def test_a_real_shows_passes():
    fine = {"widget": {"openness": {"sources": [{"url": "https://example.com",
                                                 "shows": "LICENSE is the verbatim MIT text"}]}}}
    assert not placeholder_shows(fine)


def test_the_gate_catches_a_marker_with_a_real_sentence_appended():
    """Four of the 33 appended their substance to the marker instead of replacing it —
    `flagship phase-C verification source; answered HTTP 429 to the 2026-08-13 re-read...`.
    The first cut compared for equality and reported all four clean, so the gate that exists
    to prohibit the marker was passing files that still carried it."""
    marker = next(iter(PLACEHOLDER_SHOWS))
    planted = {
        "widget": {
            "openness": {
                "sources": [
                    {"url": "https://example.com",
                     "shows": f"{marker}; answered HTTP 429 to the re-read after retries"}
                ]
            }
        }
    }
    assert placeholder_shows(planted)


def test_matching_survives_wrapping():
    """A `shows` is a folded YAML scalar, so the marker can arrive with its whitespace
    rewrapped. Matching on the normalized string rather than the raw one is what makes the
    gate independent of how the file happens to be wrapped."""
    marker = next(iter(PLACEHOLDER_SHOWS))
    wrapped = marker.replace(" ", "\n  ", 1)
    planted = {"widget": {"openness": {"sources": [{"url": "u", "shows": wrapped}]}}}
    assert placeholder_shows(planted)
