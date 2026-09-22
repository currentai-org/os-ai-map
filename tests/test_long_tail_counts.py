"""The long-tail counts: measured, summed, and dated.

These numbers are the map's statement about its own coverage, published in the present tense.
They were hand-typed for months and drifted a long way while their sources moved, which is the
defect the #545 rule names: a number the repo states about itself is computed and compared, never
typed. `build/sync_long_tail.py` computes them and `build/check_long_tail.py` refuses a set that
cannot say when it was computed.

No warehouse here. `measure` takes its query function, so what is tested is the arithmetic and
the abstentions rather than the network.
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from build import check_long_tail as gate
from build import sync_long_tail as sync


def fake_query(repos=10, models=20, packages=5, matched=7, overlap=3):
    """A query function returning one count per statement, in the order `measure` asks."""
    answers = {sync.REPOS: repos, sync.MODELS: models, sync.PACKAGES: packages,
               sync.MATCHED: matched, sync.OVERLAP: overlap}

    def query(statement):
        return [{"n": answers[statement]}]

    return query


def test_total_is_the_sum_of_the_three_slices():
    counts = sync.measure(fake_query(repos=10, models=20, packages=5))
    assert counts["total"] == 35
    assert (counts["repos"], counts["models"], counts["packages"]) == (10, 20, 5)


def test_universe_is_not_written():
    """It duplicated `total` and the only prose reading it now reads `total` instead. A stored
    number with no reader is a maintenance surface with no payoff."""
    assert "universe" not in sync.measure(fake_query())


def test_the_roster_counts_are_not_written_here():
    """`scored`, `scored_outside` and `uncategorized` are derived at serialize time from the
    published roster, so a product addition never edits this file."""
    counts = sync.measure(fake_query())
    for key in ("scored", "scored_outside", "uncategorized"):
        assert key not in counts


def test_apply_dates_the_counts_and_leaves_the_sample_alone():
    before = {"counts": {"repos": 1}, "top": [{"name": "a/b", "type": "repo"}]}
    after = sync.apply(before, {"repos": 9}, "2026-09-21")
    assert after["counts"] == {"repos": 9}
    assert after["measured_on"] == "2026-09-21"
    assert after["top"] == before["top"]
    assert before["counts"] == {"repos": 1}, "the input must not be mutated"


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------


def snapshot(measured_on="2026-09-21", **over):
    counts = {"repos": 10, "models": 20, "packages": 5, "total": 35, "matched": 7, "overlap": 3}
    counts.update(over)
    out = {"counts": counts, "top": []}
    if measured_on is not None:
        out["measured_on"] = measured_on
    return out


def test_a_fresh_measured_set_passes():
    assert gate.check(snapshot(), date(2026, 9, 21)) == []


def test_inside_the_window_passes():
    assert gate.check(snapshot("2026-09-08"), date(2026, 9, 21)) == []


def test_past_the_window_fails():
    """Both sources rebuild weekly, so one missed cycle is a slow week and two is a job that has
    stopped."""
    problems = gate.check(snapshot("2026-09-01"), date(2026, 9, 21))
    assert len(problems) == 1
    assert "past the 14-day window" in problems[0]


def test_no_stamp_fails():
    """Without it, a hand-typed set and a measured one are indistinguishable from the file —
    which is exactly how the old numbers survived."""
    problems = gate.check(snapshot(measured_on=None), date(2026, 9, 21))
    assert any("no measured_on" in p for p in problems)


def test_an_unparseable_stamp_fails_rather_than_being_ignored():
    problems = gate.check(snapshot("last tuesday"), date(2026, 9, 21))
    assert any("not an ISO date" in p for p in problems)


def test_a_slice_edited_without_the_total_fails():
    """The one way a typed number still slips in: change a slice, leave the sum."""
    problems = gate.check(snapshot(repos=999), date(2026, 9, 21))
    assert any("but the three slices sum to" in p for p in problems)


@pytest.mark.parametrize("missing", ["repos", "models", "packages", "total", "matched", "overlap"])
def test_a_missing_count_fails(missing):
    snap = snapshot()
    snap["counts"].pop(missing)
    problems = gate.check(snap, date(2026, 9, 21))
    assert any(missing in p and "missing" in p for p in problems)


def test_the_committed_snapshot_passes_its_own_gate():
    """The real file, so a sync that writes a shape the gate rejects fails here rather than in CI."""
    snap = json.loads(gate.SNAPSHOT.read_text())
    assert gate.check(snap, date.fromisoformat(snap["measured_on"])) == []


def test_matched_and_overlap_are_different_grains():
    """The bug this pair exists to prevent.

    `total` counts artifacts; `overlap` counts products. Subtracting one from the other was
    survivable while repositories were the only slice and a product had roughly one of them.
    Once the universe gained its model and package slices, every scored product's Hugging Face
    model and published package stayed in the universe and was published as not yet scored.
    """
    counts = sync.measure(fake_query())
    assert "matched" in counts and "overlap" in counts
    assert sync.MATCHED is not sync.OVERLAP


def test_uncategorized_subtracts_artifacts_and_scored_outside_subtracts_products():
    from build.serialize import derived_long_tail_counts

    frozen = {"counts": {"repos": 10, "models": 20, "packages": 5, "total": 35,
                         "matched": 9, "overlap": 4}}
    counts = derived_long_tail_counts(frozen, {"a", "b", "c", "d", "e", "f"})
    assert counts["scored"] == 6
    assert counts["scored_outside"] == 6 - 4, "products minus products"
    assert counts["uncategorized"] == 35 - 9, "artifacts minus artifacts"


def test_uncategorized_falls_back_to_overlap_when_matched_is_absent():
    """A snapshot written before `matched` existed still serializes rather than crashing; the
    gate is what refuses to publish it."""
    from build.serialize import derived_long_tail_counts

    frozen = {"counts": {"total": 35, "overlap": 4}}
    assert derived_long_tail_counts(frozen, {"a"})["uncategorized"] == 31
