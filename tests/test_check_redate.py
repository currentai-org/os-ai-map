"""Tests for the re-dating gate.

The gate exists because a date is the cheapest thing in a score file to move and the most
expensive to have wrong. Two shapes produce an unsupported re-dating without anyone meaning to:
a hand edit that advances `last_verified` past every `accessed` under it, and a merge of two
re-verification runs that keeps the newer conclusion beside the older evidence. Both read fine
in a diff, so the cases below are the two that have to fail.

`test_a_read_source_without_a_re_dated_axis_is_fine` pins the asymmetry that makes the gate
safe to run on any branch: `accessed` moving on its own is correct, because a fetch is a weaker
act than a re-confirmation and `last_verified` is never backfilled from it.
"""

from build.check_redate import axis_violations


def axis(last_verified: str, *accessed: str) -> dict:
    return {
        "last_verified": last_verified,
        "sources": [{"url": f"https://e.example/{i}", "accessed": a} for i, a in enumerate(accessed)],
    }


def test_a_re_dating_backed_by_a_fresh_read_passes():
    before = axis("2026-08-09", "2026-08-09", "2026-07-01")
    after = axis("2026-09-16", "2026-09-16", "2026-07-01")
    assert axis_violations("x.yaml", "openness", before, after) == []


def test_a_re_dating_with_no_source_read_on_that_date_fails():
    """The hand-edit shape: the conclusion is dated today, every reading behind it is old."""
    before = axis("2026-08-09", "2026-08-09")
    after = axis("2026-09-16", "2026-08-09")
    problems = axis_violations("x.yaml", "openness", before, after)
    assert len(problems) == 2
    assert "no source was accessed on that date" in problems[0]


def test_a_newer_conclusion_over_the_same_evidence_fails():
    """The bad-merge shape: the date comes from one run, the sources from an older one.

    The newest `accessed` is unchanged, so nothing was re-read; only the claim moved.
    """
    before = axis("2026-09-09", "2026-09-16", "2026-08-01")
    after = axis("2026-09-16", "2026-09-16", "2026-08-01")
    problems = axis_violations("x.yaml", "openness", before, after)
    assert len(problems) == 1
    assert "did not move" in problems[0]


def test_a_read_source_without_a_re_dated_axis_is_fine():
    before = axis("2026-08-09", "2026-08-09")
    after = axis("2026-08-09", "2026-09-16")
    assert axis_violations("x.yaml", "openness", before, after) == []


def test_an_axis_that_never_carried_a_date_is_not_a_re_dating():
    before = {"sources": [{"url": "https://e.example/0", "accessed": "2026-08-09"}]}
    after = axis("2026-09-16", "2026-09-16")
    assert axis_violations("x.yaml", "adoption", before, after) == []
