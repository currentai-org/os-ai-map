"""Adoption's date comes from the measurement that earned it, and a disagreement earns nothing.

The safety property the whole mechanism rests on is negative: a run that measures a different
band from the one recorded must leave the stored date exactly where it is. It is asserted here
three ways — the planner does not emit a change for it, the writer refuses one if handed it, and
the file on disk is unchanged after a run that queued the product. A date that moved on a
disagreement would be a freshness claim made by the very run that failed to confirm it.

The gate half is the other side of the same rule. A derived date is supported by the observation
rather than by a citation, so these also pin what makes a derivation unusable: a date that is not
the observation's, a snapshot nothing recorded, a window the date falls outside, and the field
appearing on an axis that does not derive.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
import yaml

from build import adoption_freshness as af
from build.check_redate import axis_violations
from build.check_verification import invariant
from build.observation_snapshot import load_ledger, observed_window, record_snapshot

SNAPSHOT = "a" * 64
OTHER_SNAPSHOT = "b" * 64
LEDGER = {SNAPSHOT: {"observed_from": "2026-08-16", "observed_to": "2026-08-24"}}
_UTC = datetime.timezone.utc


def _row(
    slug="widget",
    recorded=3,
    measured=3,
    recorded_instrument="usage_volume",
    measured_instrument="usage_volume",
    route="pypi.downloads_30d",
    as_of="2026-08-20",
):
    """One reconciliation row, with `delta` computed the way the reconciliation computes it."""
    comparable = (
        measured is not None
        and recorded is not None
        and measured_instrument == recorded_instrument
    )
    return {
        "product_slug": slug,
        "category_slug": "cat",
        "route_id": route,
        "recorded_level": recorded,
        "recorded_instrument_type": recorded_instrument,
        "measured_level": measured,
        "measured_instrument_type": measured_instrument if measured is not None else None,
        "channel": "pypi",
        "raw_value": 1234,
        "measurement_as_of": datetime.datetime.fromisoformat(as_of).replace(tzinfo=_UTC),
        "route_authority": "authoritative",
        "delta": (measured - recorded) if comparable else None,
        "observation_snapshot_id": SNAPSHOT,
        "status": "source_unavailable",
    }


def _corpus(tmp_path: Path, blocks: dict[str, dict]) -> Path:
    (tmp_path / "sources" / "scores").mkdir(parents=True)
    for slug, adoption in blocks.items():
        (tmp_path / "sources" / "scores" / f"{slug}.yaml").write_text(
            yaml.safe_dump(
                {
                    "product": slug,
                    "openness": {"score": 5, "class": "open_source", "sources": []},
                    "adoption": {"level": 3, "signal_type": "usage_volume", **adoption},
                    "capability": {"score": 3, "basis": "feature_matrix", "sources": []},
                }
            )
        )
    return tmp_path


def _adoption(root: Path, slug: str) -> dict:
    return yaml.safe_load((root / "sources" / "scores" / f"{slug}.yaml").read_text())["adoption"]


# ── what a run earns ────────────────────────────────────────────────────────────────────────


def test_an_agreement_takes_the_observation_date(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    changes, _ = af.plan([_row()], root=root)
    assert [(c.product_slug, c.was, c.now) for c in changes] == [("widget", "2026-08-01", "2026-08-20")]
    af.apply(changes, root=root)
    block = _adoption(root, "widget")
    assert block["last_verified"] == "2026-08-20"
    assert block["derived_from"] == {
        "observation_snapshot_id": SNAPSHOT,
        "route_id": "pypi.downloads_30d",
        "measurement_as_of": "2026-08-20",
    }


def test_the_date_is_the_observation_not_the_run(tmp_path):
    """The run executes today; the figure it read was observed in August."""
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    changes, _ = af.plan([_row(as_of="2026-08-20")], root=root)
    af.apply(changes, root=root)
    assert _adoption(root, "widget")["last_verified"] == "2026-08-20"
    assert _adoption(root, "widget")["last_verified"] != datetime.date.today().isoformat()


def test_the_date_is_not_an_accessed_date(tmp_path):
    """A citation read after the observation does not lend its date to the axis."""
    root = _corpus(
        tmp_path,
        {"widget": {"last_verified": "2026-08-01",
                    "sources": [{"url": "https://pypistats.org/api/packages/w/recent",
                                 "accessed": "2026-09-17"}]}},
    )
    changes, _ = af.plan([_row(as_of="2026-08-20")], root=root)
    af.apply(changes, root=root)
    assert _adoption(root, "widget")["last_verified"] == "2026-08-20"


def test_a_stored_date_is_never_moved_backwards(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-09-10", "sources": []}})
    changes, declined = af.plan([_row(as_of="2026-08-20")], root=root)
    assert changes == []
    assert any("newer than the observation" in line for line in declined)
    assert _adoption(root, "widget")["last_verified"] == "2026-09-10"


def test_an_unchanged_derivation_is_not_rewritten(tmp_path):
    root = _corpus(
        tmp_path,
        {"widget": {"last_verified": "2026-08-20",
                    "derived_from": {"observation_snapshot_id": SNAPSHOT,
                                     "route_id": "pypi.downloads_30d",
                                     "measurement_as_of": "2026-08-20"},
                    "sources": []}},
    )
    changes, _ = af.plan([_row(as_of="2026-08-20")], root=root)
    assert changes == []


# ── the safety property: a disagreement earns nothing ───────────────────────────────────────


def test_a_disagreement_does_not_advance_the_date(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    rows = [_row(recorded=3, measured=5)]
    changes, _ = af.plan(rows, root=root)
    assert changes == []
    af.apply(changes, root=root)
    block = _adoption(root, "widget")
    assert block["last_verified"] == "2026-08-01"
    assert "derived_from" not in block


def test_a_disagreement_is_raised_as_a_tier_change(tmp_path):
    entries = af.queue([_row(recorded=3, measured=5)])
    assert [e["kind"] for e in entries] == [af.TIER_CHANGE]
    line = af.render_queue(entries)
    assert "widget" in line and "recorded 3" in line and "measured 5" in line
    assert "pypi.downloads_30d" in line


def test_the_writer_refuses_a_change_that_is_not_an_agreement(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    forged = af.Change(
        "widget", "2026-08-01", "2026-08-20",
        {"observation_snapshot_id": SNAPSHOT, "route_id": "pypi.downloads_30d",
         "measurement_as_of": "2026-08-20"},
        verdict=af.TIER_CHANGE,
    )
    with pytest.raises(ValueError, match="confirms nothing"):
        af.apply([forged], root=root)
    assert _adoption(root, "widget")["last_verified"] == "2026-08-01"


def test_the_writer_refuses_a_date_that_is_not_the_observation_date(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    forged = af.Change(
        "widget", "2026-08-01", datetime.date.today().isoformat(),
        {"observation_snapshot_id": SNAPSHOT, "route_id": "pypi.downloads_30d",
         "measurement_as_of": "2026-08-20"},
    )
    with pytest.raises(ValueError, match="derive from"):
        af.apply([forged], root=root)


# ── instruments ─────────────────────────────────────────────────────────────────────────────


def test_a_cross_instrument_match_never_dates_an_axis(tmp_path):
    """Equal numbers on two different instruments are a coincidence, not a confirmation."""
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    rows = [_row(recorded=3, measured=3, recorded_instrument="reported_traction",
                 measured_instrument="stars_fallback", route="github.stargazers_count")]
    assert af.verdict(rows[0]) == af.NOT_COMPARED
    changes, _ = af.plan(rows, root=root)
    assert changes == []


def test_a_cross_instrument_difference_is_queued_as_a_route_disagreement():
    rows = [_row(recorded=4, measured=1, recorded_instrument="reported_traction",
                 measured_instrument="stars_fallback", route="github.stargazers_count")]
    entries = af.queue(rows)
    assert [e["kind"] for e in entries] == [af.ROUTE_DISAGREEMENT]
    assert "instruments differ" in af.render_queue(entries)


def test_an_unmeasured_row_is_neither_dated_nor_queued(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    rows = [_row(measured=None, measured_instrument=None)]
    assert af.queue(rows) == []
    assert af.plan(rows, root=root)[0] == []


# ── what the gates ask of a derived date ────────────────────────────────────────────────────


def _dated(**derived) -> dict:
    block = {"level": 3, "last_verified": "2026-08-20", "sources": []}
    if derived:
        block["derived_from"] = derived
    return {"widget": {"adoption": block}}


def _derivation(**overrides) -> dict:
    return {"observation_snapshot_id": SNAPSHOT, "route_id": "pypi.downloads_30d",
            "measurement_as_of": "2026-08-20", **overrides}


def test_a_derived_date_needs_no_citation_read_since():
    """The axis cites nothing fresh, and that is the point: the observation is the support."""
    assert invariant(_dated(**_derivation()), {}, {}, {}, LEDGER) == []


def test_a_date_with_no_derivation_still_needs_a_citation():
    problems = invariant(_dated(), {}, {}, {}, LEDGER)
    assert any("no source was accessed on or after" in p for p in problems)


def test_a_derived_date_outside_its_snapshot_window_fails():
    scores = _dated(**_derivation(measurement_as_of="2026-09-30"))
    scores["widget"]["adoption"]["last_verified"] = "2026-09-30"
    problems = invariant(scores, {}, {}, {}, LEDGER)
    assert any("outside snapshot" in p for p in problems)


def test_a_derivation_naming_an_unrecorded_snapshot_fails():
    problems = invariant(_dated(**_derivation(observation_snapshot_id=OTHER_SNAPSHOT)),
                         {}, {}, {}, LEDGER)
    assert any("is not in" in p for p in problems)


def test_a_derived_date_that_is_not_the_observation_date_fails():
    problems = invariant(_dated(**_derivation(measurement_as_of="2026-08-18")), {}, {}, {}, LEDGER)
    assert any("is not the observation date" in p for p in problems)


def test_an_incomplete_derivation_fails():
    problems = invariant(_dated(**_derivation(route_id="")), {}, {}, {}, LEDGER)
    assert any("records no route_id" in p for p in problems)


def test_only_adoption_may_derive_its_date():
    scores = {"widget": {"capability": {"score": 3, "last_verified": "2026-08-20",
                                        "derived_from": _derivation(), "sources": []}}}
    problems = invariant(scores, {}, {}, {}, LEDGER)
    assert any("which only adoption may derive" in p for p in problems)


# ── the re-dating gate ──────────────────────────────────────────────────────────────────────


def test_check_redate_accepts_a_derived_move_with_no_fresh_reading():
    before = {"last_verified": "2026-08-01", "sources": [{"accessed": "2026-08-01"}]}
    after = {"last_verified": "2026-08-20", "derived_from": _derivation(),
             "sources": [{"accessed": "2026-08-01"}]}
    assert axis_violations("sources/scores/widget.yaml", "adoption", before, after) == []


def test_check_redate_rejects_a_derived_move_to_some_other_date():
    before = {"last_verified": "2026-08-01", "sources": []}
    after = {"last_verified": "2026-09-19", "derived_from": _derivation(), "sources": []}
    problems = axis_violations("sources/scores/widget.yaml", "adoption", before, after)
    assert any("was observed 2026-08-20" in p for p in problems)


def test_check_redate_still_requires_a_reading_where_nothing_was_derived():
    before = {"last_verified": "2026-08-01", "sources": [{"accessed": "2026-08-01"}]}
    after = {"last_verified": "2026-08-20", "sources": [{"accessed": "2026-08-01"}]}
    assert axis_violations("sources/scores/widget.yaml", "adoption", before, after)


# ── the snapshot ledger ─────────────────────────────────────────────────────────────────────


def _observation(stamp: str) -> dict:
    return {"observed_at": datetime.datetime.fromisoformat(stamp)}


def test_a_snapshot_id_resolves_to_the_window_it_observed(tmp_path):
    rows = [_observation("2026-08-16T04:00:00"), _observation("2026-08-24T11:21:39")]
    assert observed_window(rows) == (datetime.date(2026, 8, 16), datetime.date(2026, 8, 24))


def test_recording_a_snapshot_twice_changes_nothing(tmp_path):
    path = tmp_path / "observation_snapshots.yaml"
    record = {"observation_snapshot_id": SNAPSHOT, "observation_content_digest": "c" * 64,
              "canonicalization_version": 1, "row_count": 2,
              "observed_from": "2026-08-16", "observed_to": "2026-08-24"}
    assert record_snapshot(record, path=path, recorded_at=datetime.date(2026, 9, 20)) is True
    first = path.read_text()
    assert record_snapshot(record, path=path, recorded_at=datetime.date(2026, 9, 27)) is False
    assert path.read_text() == first
    assert load_ledger(path)[SNAPSHOT]["observed_to"] == "2026-08-24"


def test_one_content_hash_cannot_name_two_windows(tmp_path):
    path = tmp_path / "observation_snapshots.yaml"
    record = {"observation_snapshot_id": SNAPSHOT, "observation_content_digest": "c" * 64,
              "canonicalization_version": 1, "row_count": 2,
              "observed_from": "2026-08-16", "observed_to": "2026-08-24"}
    record_snapshot(record, path=path)
    with pytest.raises(ValueError, match="cannot name two observation sets"):
        record_snapshot({**record, "observed_to": "2026-09-01"}, path=path)


def test_an_empty_observation_set_has_no_window():
    with pytest.raises(ValueError, match="no observed window"):
        observed_window([])
