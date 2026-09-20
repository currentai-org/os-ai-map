"""Adoption's date comes from the measurement that earned it, and a disagreement earns nothing.

The safety property the whole mechanism rests on is negative: a run that measures a different
band from the one recorded must leave the stored date exactly where it is. It is asserted here
three ways — the planner does not emit a change for it, the writer refuses one if handed it, and
the file on disk is unchanged after a run that queued the product. A date that moved on a
disagreement would be a freshness claim made by the very run that failed to confirm it.

The second property is that a match is not an agreement. A measurement read from a table nobody
can attribute to a run proves nothing about whether a collector ran, so an unbound read dates
nothing at all and still emits its queue. These pin the three ways a read fails to bind.

The gate half is the other side of the same rule. A derived date is supported by the observation
rather than by a citation, so these also pin what makes a derivation unusable: a date that is not
the observation's, a snapshot nothing recorded, a window the date falls outside, a route the
tables do not compile, a level the score no longer carries, a measurement the ledger does not
record, and the field appearing on an axis that does not derive.
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
from build.read_binding import bound_read

SNAPSHOT = "a" * 64
OTHER_SNAPSHOT = "b" * 64
RUN = "980a87f1-3274-408e-928e-70eee35dd8a2"
ROUTE = "pypi.downloads_30d"
_UTC = datetime.timezone.utc

#: A read that named one materialization at both ends of its bracket.
BOUND = {
    "binding_status": "bound",
    "model": "observations.product_adoption_current",
    "model_id": "model-1",
    "materialization_id": "mat-1",
    "run_id": RUN,
    "materialized_at": "2026-09-20T03:30:26Z",
    "read_at": "2026-09-20T05:00:00+00:00",
    "run_trigger_type": "SCHEDULED",
    "run_status": "SUCCESS",
    "run_started_at": "2026-09-20T03:30:16Z",
}
#: A read that straddled a refresh: two materializations, so neither one served the rows.
UNSTABLE = {
    "binding_status": "unstable",
    "model": "observations.product_adoption_current",
    "materialization_id_before": "mat-1",
    "materialization_id_after": "mat-2",
}

LEDGER = {
    SNAPSHOT: {
        "observed_from": "2026-08-16",
        "observed_to": "2026-08-24",
        "source_runs": {
            RUN: {
                "trigger_type": "SCHEDULED",
                "status": "SUCCESS",
                "started_at": "2026-09-20T03:30:16Z",
            }
        },
        "agreements": {
            "widget": {
                "source_run_id": RUN,
                "route_id": ROUTE,
                "measured_level": 3,
                "measurement_as_of": "2026-08-20",
            }
        },
    }
}


def _row(
    slug="widget",
    recorded=3,
    measured=3,
    recorded_instrument="usage_volume",
    measured_instrument="usage_volume",
    route=ROUTE,
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


def test_a_bound_match_takes_the_observation_date(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    changes, _ = af.plan([_row()], BOUND, root=root)
    assert [(c.product_slug, c.was, c.now) for c in changes] == [
        ("widget", "2026-08-01", "2026-08-20")
    ]
    af.apply(changes, root=root)
    block = _adoption(root, "widget")
    assert block["last_verified"] == "2026-08-20"
    assert block["derived_from"] == {
        "observation_snapshot_id": SNAPSHOT,
        "source_run_id": RUN,
        "route_id": ROUTE,
        "measured_level": 3,
        "measurement_as_of": "2026-08-20",
    }


def test_the_date_is_the_observation_not_the_run(tmp_path):
    """The run executes today; the figure it read was observed in August."""
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    changes, _ = af.plan([_row(as_of="2026-08-20")], BOUND, root=root)
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
    changes, _ = af.plan([_row(as_of="2026-08-20")], BOUND, root=root)
    af.apply(changes, root=root)
    assert _adoption(root, "widget")["last_verified"] == "2026-08-20"


def test_a_stored_date_is_never_moved_backwards(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-09-10", "sources": []}})
    changes, declined = af.plan([_row(as_of="2026-08-20")], BOUND, root=root)
    assert changes == []
    assert any("newer than the observation" in line for line in declined)
    assert _adoption(root, "widget")["last_verified"] == "2026-09-10"


def test_an_unchanged_derivation_is_not_rewritten(tmp_path):
    root = _corpus(
        tmp_path,
        {"widget": {"last_verified": "2026-08-20",
                    "derived_from": af.derivation(_row(), BOUND),
                    "sources": []}},
    )
    changes, _ = af.plan([_row(as_of="2026-08-20")], BOUND, root=root)
    assert changes == []


def test_a_later_run_over_the_same_observations_rewrites_nothing(tmp_path):
    """Same snapshot, same band, a new materialization: the date is already the right date."""
    root = _corpus(
        tmp_path,
        {"widget": {"last_verified": "2026-08-20",
                    "derived_from": af.derivation(_row(), {**BOUND, "run_id": "an-older-run"}),
                    "sources": []}},
    )
    changes, _ = af.plan([_row(as_of="2026-08-20")], BOUND, root=root)
    assert changes == []
    assert _adoption(root, "widget")["derived_from"]["source_run_id"] == "an-older-run"


# ── a match is not an agreement without a run ───────────────────────────────────────────────


def test_an_unbound_read_dates_nothing(tmp_path):
    """The frozen baseline names no run, so the same match that would date an axis does not."""
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    changes, declined = af.plan([_row()], af.BASELINE_BINDING, root=root)
    assert changes == []
    assert any("not an agreement" in line for line in declined)
    assert any("records no source run" in line for line in declined)
    assert _adoption(root, "widget")["last_verified"] == "2026-08-01"
    assert "derived_from" not in _adoption(root, "widget")


def test_an_unbound_read_still_emits_the_queue():
    """The comparison is worth running unbound — the queue is what it is for."""
    rows = [_row(recorded=3, measured=5), _row(slug="gadget")]
    assert af.plan(rows, af.BASELINE_BINDING)[0] == []
    entries = af.queue(rows)
    assert [e["product_slug"] for e in entries] == ["widget"]


def test_a_refresh_landing_mid_read_dates_nothing(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    changes, declined = af.plan([_row()], UNSTABLE, root=root)
    assert changes == []
    assert any("mid-read" in line for line in declined)


def test_a_missing_binding_is_not_a_binding():
    assert af.binding_problems(None)
    assert af.binding_problems({})
    assert af.binding_problems({"binding_status": "bound", "model": "m"})
    assert af.binding_problems({"binding_status": "who-knows"})
    assert af.binding_problems(BOUND) == []


def test_a_table_a_person_refreshed_dates_nothing_and_still_queues(tmp_path):
    """A MANUAL run is somebody pressing refresh, and adoption's date is not supposed to be that.

    The whole point of moving adoption's freshness onto the weekly cadence is that the date stops
    being a person's act. A bound read of a table a person materialized is still a bound read —
    the rows are attributable — so this is not a gap in the binding; it is the cadence rule, and
    it is the reason a cron that never fires cannot quietly produce dates by hand instead.
    """
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    manual = {**BOUND, "run_trigger_type": "MANUAL"}
    problems = af.binding_problems(manual)
    assert problems and "MANUAL" in problems[0]

    changes, declined = af.plan([_row(as_of="2026-08-20")], manual, root=root)
    assert changes == []
    assert any("weekly cadence" in line for line in declined)
    assert _adoption(root, "widget")["last_verified"] == "2026-08-01"
    # The comparison is still worth having: the queue is what the week produces either way.
    assert af.queue([_row(recorded=3, measured=5)])[0]["product_slug"] == "widget"


def test_a_run_that_has_not_succeeded_dates_nothing():
    """A materialization exists mid-run too, and a run still going has measured nothing yet."""
    for status in ("RUNNING", "FAILED"):
        problems = af.binding_problems({**BOUND, "run_status": status})
        assert problems and status in problems[0]


def test_a_bound_read_carries_the_trigger_of_the_run_that_served_it(monkeypatch):
    """The trigger comes from the control plane, not from the caller's assumption about it."""
    monkeypatch.setenv("OSO_API_KEY", "test")
    scheduled = bound_read(lambda: [{"product_slug": "widget"}],
                           graphql=_graphql("mat-1", "mat-1"))
    assert scheduled.binding["run_trigger_type"] == "SCHEDULED"
    assert af.binding_problems({**scheduled.binding, "read_at": "2026-09-20T05:00:00+00:00"}) == []

    by_hand = bound_read(lambda: [{"product_slug": "widget"}],
                         graphql=_graphql("mat-1", "mat-1", trigger="MANUAL"))
    assert by_hand.binding["run_trigger_type"] == "MANUAL"
    assert af.binding_problems({**by_hand.binding, "read_at": "2026-09-20T05:00:00+00:00"})


def test_a_stored_date_whose_run_was_not_the_scheduled_one_fails_the_gate():
    """Months later the control plane may no longer answer for the run, so the ledger does.

    Three states are distinguished, because they are different faults: a ledger that records
    nothing about the run (a date nobody can classify), a run it records as MANUAL (a person's
    date), and a run it records as unsuccessful.
    """
    block = {
        "level": 3,
        "last_verified": "2026-08-20",
        "derived_from": af.derivation(_row(), BOUND),
    }
    assert af.derivation_problems("widget", block, LEDGER, {ROUTE}) == []

    entry = dict(LEDGER[SNAPSHOT])
    nothing_recorded = {SNAPSHOT: {k: v for k, v in entry.items() if k != "source_runs"}}
    assert any("records nothing about run" in problem
               for problem in af.derivation_problems("widget", block, nothing_recorded, {ROUTE}))

    by_hand = {SNAPSHOT: {**entry, "source_runs": {
        RUN: {"trigger_type": "MANUAL", "status": "SUCCESS", "started_at": "2026-09-20T03:30:16Z"}}}}
    assert any("weekly cadence" in problem
               for problem in af.derivation_problems("widget", block, by_hand, {ROUTE}))

    failed = {SNAPSHOT: {**entry, "source_runs": {
        RUN: {"trigger_type": "SCHEDULED", "status": "FAILED", "started_at": "2026-09-20T03:30:16Z"}}}}
    assert any("did not succeed" in problem
               for problem in af.derivation_problems("widget", block, failed, {ROUTE}))


def test_the_ledger_keeps_the_trigger_of_every_run_that_ever_dated_a_product(tmp_path):
    """A later run must not erase the run an older agreement still points at."""
    from build.observation_snapshot import load_ledger, record_snapshot

    path = tmp_path / "observation_snapshots.yaml"
    record = {"observation_snapshot_id": SNAPSHOT, "observation_content_digest": "d" * 64,
              "canonicalization_version": 1, "row_count": 2,
              "observed_from": "2026-08-16", "observed_to": "2026-08-24"}
    first = {"run-a": {"trigger_type": "SCHEDULED", "status": "SUCCESS",
                       "started_at": "2026-09-13T03:30:16Z"}}
    second = {"run-b": {"trigger_type": "SCHEDULED", "status": "SUCCESS",
                        "started_at": "2026-09-20T03:30:16Z"}}
    record_snapshot(record, agreements={"widget": {"source_run_id": "run-a"}},
                    source_runs=first, path=path)
    record_snapshot(record, agreements={"gadget": {"source_run_id": "run-b"}},
                    source_runs=second, path=path)
    runs = load_ledger(path)[SNAPSHOT]["source_runs"]
    assert set(runs) == {"run-a", "run-b"}


def test_the_writer_refuses_a_date_with_no_source_run(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    forged = af.Change(
        "widget", "2026-08-01", "2026-08-20",
        {k: v for k, v in af.derivation(_row(), BOUND).items() if k != "source_run_id"},
    )
    with pytest.raises(ValueError, match="no source run behind it"):
        af.apply([forged], root=root)
    assert _adoption(root, "widget")["last_verified"] == "2026-08-01"


def _graphql(*materialization_ids, trigger="SCHEDULED", status="SUCCESS"):
    """A control plane that names these materializations, one per call, in order.

    It answers the run query too, since a bound bracket looks the run up to learn how it was
    started; `trigger` and `status` are what it reports for every run it is asked about.
    """
    calls = iter(materialization_ids)

    def graphql(query, variables, token):
        if "runs(" in query:
            return {"runs": {"edges": [{"node": {
                "id": variables["w"]["id"]["eq"],
                "triggerType": trigger,
                "runType": trigger,
                "status": status,
                "startedAt": "2026-09-20T03:30:16Z",
            }}]}}
        mid = next(calls)
        return {
            "dataModels": {
                "edges": [
                    {
                        "node": {
                            "id": "model-1",
                            "name": "product_adoption_current",
                            "dataset": {"name": "observations"},
                            "materializations": {
                                "edges": [
                                    {
                                        "node": {
                                            "id": mid,
                                            "runId": f"run-of-{mid}",
                                            "createdAt": "2026-09-20T03:30:26Z",
                                        }
                                    }
                                ]
                            },
                        }
                    }
                ]
            }
        }

    return graphql


def test_a_read_served_by_one_materialization_is_bound_to_its_run(monkeypatch):
    monkeypatch.setenv("OSO_API_KEY", "test")
    read = bound_read(lambda: [{"product_slug": "widget"}], graphql=_graphql("mat-1", "mat-1"))
    assert read.binding["binding_status"] == "bound"
    assert read.binding["run_id"] == "run-of-mat-1"
    assert af.binding_problems({**read.binding, "read_at": "2026-09-20T05:00:00+00:00"}) == []


def test_a_read_that_straddled_two_materializations_claims_no_run(monkeypatch):
    monkeypatch.setenv("OSO_API_KEY", "test")
    read = bound_read(lambda: [{"product_slug": "widget"}], graphql=_graphql("mat-1", "mat-2"))
    assert read.binding["binding_status"] == "unstable"
    assert "run_id" not in read.binding
    assert af.plan([_row()], read.binding)[0] == []


# ── the safety property: a disagreement earns nothing ───────────────────────────────────────


def test_a_disagreement_does_not_advance_the_date(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    rows = [_row(recorded=3, measured=5)]
    changes, _ = af.plan(rows, BOUND, root=root)
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
    assert ROUTE in line


def test_the_writer_refuses_a_change_that_is_not_an_agreement(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    forged = af.Change(
        "widget", "2026-08-01", "2026-08-20", af.derivation(_row(), BOUND),
        verdict=af.TIER_CHANGE,
    )
    with pytest.raises(ValueError, match="confirms nothing"):
        af.apply([forged], root=root)
    assert _adoption(root, "widget")["last_verified"] == "2026-08-01"


def test_the_writer_refuses_a_date_that_is_not_the_observation_date(tmp_path):
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    forged = af.Change(
        "widget", "2026-08-01", datetime.date.today().isoformat(),
        af.derivation(_row(), BOUND),
    )
    with pytest.raises(ValueError, match="derive from"):
        af.apply([forged], root=root)


def test_the_writer_refuses_a_score_re_banded_since_the_measurement(tmp_path):
    """The plan was built against level 3; by the time it writes, a person has said 4."""
    root = _corpus(tmp_path, {"widget": {"level": 4, "last_verified": "2026-08-01",
                                         "sources": []}})
    change = af.Change("widget", "2026-08-01", "2026-08-20", af.derivation(_row(), BOUND))
    with pytest.raises(ValueError, match="is not that band"):
        af.apply([change], root=root)
    assert _adoption(root, "widget")["last_verified"] == "2026-08-01"


# ── instruments ─────────────────────────────────────────────────────────────────────────────


def test_a_cross_instrument_match_never_dates_an_axis(tmp_path):
    """Equal numbers on two different instruments are a coincidence, not a confirmation."""
    root = _corpus(tmp_path, {"widget": {"last_verified": "2026-08-01", "sources": []}})
    rows = [_row(recorded=3, measured=3, recorded_instrument="reported_traction",
                 measured_instrument="stars_fallback", route="github.stargazers_count")]
    assert af.verdict(rows[0]) == af.NOT_COMPARED
    changes, _ = af.plan(rows, BOUND, root=root)
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
    assert af.plan(rows, BOUND, root=root)[0] == []


# ── what the gates ask of a derived date ────────────────────────────────────────────────────


def _dated(level=3, **derived) -> dict:
    block = {"level": level, "last_verified": "2026-08-20", "sources": []}
    if derived:
        block["derived_from"] = derived
    return {"widget": {"adoption": block}}


def _derivation(**overrides) -> dict:
    return {"observation_snapshot_id": SNAPSHOT, "source_run_id": RUN, "route_id": ROUTE,
            "measured_level": 3, "measurement_as_of": "2026-08-20", **overrides}


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


def test_a_derivation_with_no_source_run_fails():
    problems = invariant(_dated(**_derivation(source_run_id="")), {}, {}, {}, LEDGER)
    assert any("records no source_run_id" in p for p in problems)


def test_only_adoption_may_derive_its_date():
    scores = {"widget": {"capability": {"score": 3, "last_verified": "2026-08-20",
                                        "derived_from": _derivation(), "sources": []}}}
    problems = invariant(scores, {}, {}, {}, LEDGER)
    assert any("which only adoption may derive" in p for p in problems)


def test_a_re_banded_score_loses_its_derived_confirmation():
    """A person moves the level to 4. The run that agreed with 3 does not date 4."""
    problems = invariant(_dated(level=4, **_derivation()), {}, {}, {}, LEDGER)
    assert any("re-banded score is not confirmed" in p for p in problems)


def test_a_route_the_tables_do_not_compile_fails():
    problems = invariant(_dated(**_derivation(route_id="nonexistent.route")), {}, {}, {}, LEDGER,
                         {ROUTE})
    assert any("not a route the routing tables compile" in p for p in problems)


def test_a_date_the_ledger_does_not_record_fails():
    """Both date fields moved together and stayed inside the window; the ledger still knows."""
    scores = _dated(**_derivation(measurement_as_of="2026-08-24"))
    scores["widget"]["adoption"]["last_verified"] = "2026-08-24"
    problems = invariant(scores, {}, {}, {}, LEDGER)
    assert any("the two records of one measurement disagree" in p for p in problems)


def test_a_product_the_ledger_records_no_measurement_for_fails():
    scores = {"gadget": {"adoption": {"level": 3, "last_verified": "2026-08-20",
                                      "derived_from": _derivation(), "sources": []}}}
    problems = invariant(scores, {}, {}, {}, LEDGER)
    assert any("records no agreeing measurement for this product" in p for p in problems)


def test_the_three_hand_edits_a_self_describing_record_could_not_catch():
    """Re-band the level, rename the route, move the date a few days: each is caught."""
    scores = _dated(level=4, **_derivation(route_id="nonexistent.route",
                                           measurement_as_of="2026-08-24"))
    scores["widget"]["adoption"]["last_verified"] = "2026-08-24"
    problems = invariant(scores, {}, {}, {}, LEDGER, {ROUTE})
    assert any("re-banded score is not confirmed" in p for p in problems)
    assert any("not a route the routing tables compile" in p for p in problems)
    assert any("route_id" in p and "disagree" in p for p in problems)
    assert any("measurement_as_of" in p and "disagree" in p for p in problems)


def test_a_measured_level_of_zero_is_a_level_not_a_missing_field():
    ledger = {SNAPSHOT: {**LEDGER[SNAPSHOT],
                         "agreements": {"widget": {**LEDGER[SNAPSHOT]["agreements"]["widget"],
                                                   "measured_level": 0}}}}
    assert invariant(_dated(level=0, **_derivation(measured_level=0)), {}, {}, {}, ledger) == []


# ── the re-dating gate ──────────────────────────────────────────────────────────────────────


def test_check_redate_accepts_a_derived_move_with_no_fresh_reading():
    before = {"last_verified": "2026-08-01", "sources": [{"accessed": "2026-08-01"}]}
    after = {"level": 3, "last_verified": "2026-08-20", "derived_from": _derivation(),
             "sources": [{"accessed": "2026-08-01"}]}
    assert axis_violations("sources/scores/widget.yaml", "adoption", before, after, LEDGER) == []


def test_check_redate_rejects_a_derived_move_to_some_other_date():
    before = {"last_verified": "2026-08-01", "sources": []}
    after = {"level": 3, "last_verified": "2026-09-19", "derived_from": _derivation(),
             "sources": []}
    problems = axis_violations("sources/scores/widget.yaml", "adoption", before, after, LEDGER)
    assert any("was observed 2026-08-20" in p for p in problems)


def test_check_redate_rejects_a_derived_move_the_ledger_does_not_carry():
    before = {"last_verified": "2026-08-01", "sources": []}
    after = {"level": 3, "last_verified": "2026-08-20", "derived_from": _derivation(),
             "sources": []}
    problems = axis_violations("sources/scores/widget.yaml", "adoption", before, after, {})
    assert any("is not in" in p for p in problems)


def test_check_redate_still_requires_a_reading_where_nothing_was_derived():
    before = {"last_verified": "2026-08-01", "sources": [{"accessed": "2026-08-01"}]}
    after = {"last_verified": "2026-08-20", "sources": [{"accessed": "2026-08-01"}]}
    assert axis_violations("sources/scores/widget.yaml", "adoption", before, after, LEDGER)


# ── the snapshot ledger ─────────────────────────────────────────────────────────────────────


def _observation(stamp: str) -> dict:
    return {"observed_at": datetime.datetime.fromisoformat(stamp)}


def _record() -> dict:
    return {"observation_snapshot_id": SNAPSHOT, "observation_content_digest": "c" * 64,
            "canonicalization_version": 1, "row_count": 2,
            "observed_from": "2026-08-16", "observed_to": "2026-08-24"}


def test_a_snapshot_id_resolves_to_the_window_it_observed(tmp_path):
    rows = [_observation("2026-08-16T04:00:00"), _observation("2026-08-24T11:21:39")]
    assert observed_window(rows) == (datetime.date(2026, 8, 16), datetime.date(2026, 8, 24))


def test_recording_a_snapshot_twice_changes_nothing(tmp_path):
    path = tmp_path / "observation_snapshots.yaml"
    assert record_snapshot(_record(), path=path, recorded_at=datetime.date(2026, 9, 20)) is True
    first = path.read_text()
    assert record_snapshot(_record(), path=path, recorded_at=datetime.date(2026, 9, 27)) is False
    assert path.read_text() == first
    assert load_ledger(path)[SNAPSHOT]["observed_to"] == "2026-08-24"


def test_one_content_hash_cannot_name_two_windows(tmp_path):
    path = tmp_path / "observation_snapshots.yaml"
    record_snapshot(_record(), path=path)
    with pytest.raises(ValueError, match="cannot name two observation sets"):
        record_snapshot({**_record(), "observed_to": "2026-09-01"}, path=path)


def test_the_ledger_records_what_was_measured_for_each_product_it_dated(tmp_path):
    path = tmp_path / "observation_snapshots.yaml"
    changes, _ = af.plan([_row()], BOUND, root=_corpus(tmp_path, {"widget": {"sources": []}}))
    record_snapshot(_record(), agreements=af.agreements(changes), path=path)
    assert load_ledger(path)[SNAPSHOT]["agreements"]["widget"] == {
        "source_run_id": RUN, "route_id": ROUTE, "measured_level": 3,
        "measurement_as_of": "2026-08-20",
    }


def test_a_product_this_run_did_not_date_keeps_the_record_of_the_run_that_did(tmp_path):
    path = tmp_path / "observation_snapshots.yaml"
    first = {"widget": {"source_run_id": RUN, "route_id": ROUTE, "measured_level": 3,
                        "measurement_as_of": "2026-08-20"}}
    second = {"gadget": {"source_run_id": "a-later-run", "route_id": ROUTE, "measured_level": 5,
                         "measurement_as_of": "2026-08-22"}}
    record_snapshot(_record(), agreements=first, path=path)
    assert record_snapshot(_record(), agreements=second, path=path) is True
    assert sorted(load_ledger(path)[SNAPSHOT]["agreements"]) == ["gadget", "widget"]


def test_an_empty_observation_set_has_no_window():
    with pytest.raises(ValueError, match="no observed window"):
        observed_window([])
