"""The Phase 4 adoption gate (#410) over fixtures: what counts as current, and what it would block.

The gate's safety property is the §4.3 rule that a measurement is `source_unavailable` unless the
run evidence says otherwise. So most of these pin the ways evidence fails: a read materialized by a
MANUAL run, a source dataset whose latest scheduled fetch is past the age bound, a failed latest
fetch with an older success behind it, a fetch that finished after the bound run started, and run
evidence captured before the read it vouches for. Each must turn a measured row into
`source_unavailable` and leave the unmeasured rows alone. The one positive case is a bound read of
a scheduled materialization plus a fresh scheduled fetch, and it is the only one that yields
`agree` and `override_required`.

The CLI half pins report-first: the gate exits 0 whatever it would block, and exits 2 only when it
could not read its input.
"""

from __future__ import annotations

import csv
import datetime
import json

import pytest

from build import adoption_freshness as af
from build import check_reconciliation as gate
from build import snapshot_source_runs as S

_UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 10, 5, 9, 0, tzinfo=_UTC)

#: A read bound to a SCHEDULED, successful materialization a day old, read at 08:00.
BOUND = {
    "binding_status": "bound",
    "model": "observations.product_adoption_current",
    "model_id": "model-1",
    "materialization_id": "mat-1",
    "run_id": "obs-run",
    "materialized_at": "2026-10-04T03:40:00Z",
    "run_trigger_type": "SCHEDULED",
    "run_status": "SUCCESS",
    "run_started_at": "2026-10-04T03:30:00Z",
    "read_at": "2026-10-05T08:00:00+00:00",
}

ROUTES = {
    "pypi.downloads_30d": "signal_packages",
    "github.stargazers_count": "signal_github",
    "active_users": None,
}

CAPTURED = "2026-10-05T08:05:00+00:00"


def _row(slug, *, route="pypi.downloads_30d", status="source_unavailable", recorded=3,
         measured=3, delta=0, authority="authoritative"):
    return {
        "product_slug": slug, "route_id": route, "status": status,
        "recorded_level": recorded, "measured_level": measured, "delta": delta,
        "route_authority": authority, "explanation": f"reconciliation said {status}",
    }


def _run(run_id, dataset, *, trigger="SCHEDULED", status="SUCCESS",
         finished="2026-10-04T02:00:00Z", captured=CAPTURED):
    return {
        "source_run_id": run_id, "source_dataset_name": dataset, "trigger_type": trigger,
        "execution_status": status, "finished_at": finished, "captured_at": captured,
    }


ROWS = [
    _row("agrees"),
    _row("disagrees", recorded=2, measured=4, delta=2),
    _row("on-stars", route="github.stargazers_count"),
    _row("cross", status="route_mismatch", delta=None, recorded=2, measured=3),
    _row("no-obs", status="unmeasured", measured=None, delta=None),
    _row("abstains", status="abstained", recorded=None, measured=None, delta=None),
]

FRESH_RUNS = [
    _run("pk-1", "signal_packages"),
    _run("gh-1", "signal_github", finished="2026-10-04T01:30:00Z"),
]


def _statuses(report):
    return {j.product_slug: j.status for j in report.judgements}


def _evaluate(binding=BOUND, runs=FRESH_RUNS, rows=ROWS):
    return gate.evaluate({"binding": binding, "rows": rows}, runs, ROUTES, now=NOW)


# --- the positive case ------------------------------------------------------------


def test_a_bound_scheduled_read_with_fresh_fetches_is_current():
    report = _evaluate()
    assert report.problems == []
    assert {k: v.verdict for k, v in report.evidence.items()} == {
        "signal_github": gate.CURRENT, "signal_packages": gate.CURRENT,
    }
    assert _statuses(report) == {
        "agrees": "agree",
        "disagrees": "override_required",
        "on-stars": "agree",
        "cross": "route_mismatch",
        "no-obs": "unmeasured",
        "abstains": "abstained",
    }
    assert [j.product_slug for j in report.blocked()] == ["disagrees"]
    assert [j.product_slug for j in report.review()] == ["cross"]


# --- the read itself is not current -----------------------------------------------


def _all_measured_unavailable(report):
    statuses = _statuses(report)
    for slug in ("agrees", "disagrees", "on-stars", "cross"):
        assert statuses[slug] == "source_unavailable", slug
    assert statuses["no-obs"] == "unmeasured"
    assert statuses["abstains"] == "abstained"


def test_a_manual_materialization_makes_nothing_current():
    report = _evaluate(binding={**BOUND, "run_trigger_type": "MANUAL"})
    assert report.problems and "MANUAL" in report.problems[0]
    assert report.evidence == {}
    _all_measured_unavailable(report)


def test_a_failed_materialization_makes_nothing_current():
    report = _evaluate(binding={**BOUND, "run_status": "FAILED"})
    assert "FAILED" in report.problems[0]
    _all_measured_unavailable(report)


def test_a_stale_materialization_makes_nothing_current():
    report = _evaluate(binding={**BOUND, "materialized_at": "2026-09-15T03:40:00Z"})
    assert "past the 14-day" in report.problems[0]
    _all_measured_unavailable(report)


def test_an_unstable_or_baseline_read_makes_nothing_current():
    unstable = {"binding_status": "unstable", "materialization_id_before": "a",
                "materialization_id_after": "b"}
    _all_measured_unavailable(_evaluate(binding=unstable))
    _all_measured_unavailable(_evaluate(binding=af.BASELINE_BINDING))


def test_run_evidence_captured_before_the_read_cannot_vouch_for_it():
    early = [{**r, "captured_at": "2026-10-05T07:59:00+00:00"} for r in FRESH_RUNS]
    report = _evaluate(runs=early)
    assert "not after the read completed" in report.problems[0]
    _all_measured_unavailable(report)


def test_an_empty_run_snapshot_makes_nothing_current():
    report = _evaluate(runs=[])
    assert "holds no runs" in report.problems[0]
    _all_measured_unavailable(report)


def test_a_binding_with_no_run_start_cannot_find_the_fetch_before_it():
    binding = {k: v for k, v in BOUND.items() if k != "run_started_at"}
    report = _evaluate(binding=binding)
    assert "no start time" in report.problems[0]


# --- the source dataset's fetch ---------------------------------------------------


def test_a_stale_fetch_makes_that_datasets_rows_unavailable_only():
    runs = [_run("pk-old", "signal_packages", finished="2026-09-18T02:00:00Z"), FRESH_RUNS[1]]
    report = _evaluate(runs=runs)
    assert report.evidence["signal_packages"].verdict == gate.STALE
    statuses = _statuses(report)
    assert statuses["agrees"] == statuses["disagrees"] == "source_unavailable"
    assert statuses["on-stars"] == "agree"  # a different dataset, fetched fresh
    assert "past the 14-day bound" in next(
        j.explanation for j in report.judgements if j.product_slug == "agrees")


def test_an_older_success_behind_a_newer_failure_does_not_count():
    runs = [
        _run("pk-good", "signal_packages", finished="2026-10-01T02:00:00Z"),
        _run("pk-bad", "signal_packages", status="FAILED", finished="2026-10-04T02:00:00Z"),
        FRESH_RUNS[1],
    ]
    ev = _evaluate(runs=runs).evidence["signal_packages"]
    assert (ev.verdict, ev.run_id) == (gate.FAILED, "pk-bad")


def test_a_manual_fetch_is_never_the_authoritative_one():
    runs = [
        _run("pk-sched", "signal_packages", status="FAILED", finished="2026-10-03T02:00:00Z"),
        _run("pk-manual", "signal_packages", trigger="MANUAL", finished="2026-10-04T02:00:00Z"),
        FRESH_RUNS[1],
    ]
    ev = _evaluate(runs=runs).evidence["signal_packages"]
    assert (ev.verdict, ev.run_id) == (gate.FAILED, "pk-sched")
    only_manual = [_run("pk-manual", "signal_packages", trigger="MANUAL"), FRESH_RUNS[1]]
    assert _evaluate(runs=only_manual).evidence["signal_packages"].verdict == gate.MISSING


def test_a_fetch_finishing_after_the_bound_run_started_did_not_feed_it():
    runs = [
        _run("pk-before", "signal_packages", status="FAILED", finished="2026-10-04T02:00:00Z"),
        _run("pk-after", "signal_packages", finished="2026-10-04T04:00:00Z"),
        _run("pk-running", "signal_packages", status="RUNNING", finished=""),
        FRESH_RUNS[1],
    ]
    ev = _evaluate(runs=runs).evidence["signal_packages"]
    assert (ev.verdict, ev.run_id) == (gate.FAILED, "pk-before")


def test_one_run_with_several_materializations_is_one_run():
    runs = [_run("pk-1", "signal_packages"), _run("pk-1", "signal_packages"), FRESH_RUNS[1]]
    assert _evaluate(runs=runs).evidence["signal_packages"].verdict == gate.CURRENT


def test_a_dataset_with_no_runs_is_missing():
    report = _evaluate(runs=[FRESH_RUNS[1]])
    assert report.evidence["signal_packages"].verdict == gate.MISSING
    assert _statuses(report)["agrees"] == "source_unavailable"


def test_a_measured_route_with_no_collector_dataset_is_unavailable():
    rows = [_row("hand", route="active_users")]
    assert _statuses(_evaluate(rows=rows)) == {"hand": "source_unavailable"}


def test_rows_are_required_in_the_read_document():
    with pytest.raises(ValueError, match="--json-out"):
        gate.evaluate({"binding": BOUND}, FRESH_RUNS, ROUTES, now=NOW)


# --- routes resolve to the datasets the snapshot captures -------------------------


def test_every_route_dataset_is_one_the_snapshot_requests():
    """The gate asks about exactly the datasets whose runs the snapshot captures."""
    datasets = {d for d in gate.route_datasets().values() if d}
    assert datasets
    assert datasets <= set(S.source_datasets())


def test_source_dataset_refuses_unbridged_and_hand_authored_sources():
    routing = {"sources": {
        "a": {"table": "currentai.signal_a.t", "bridged": True},
        "b": {"table": "currentai.signal_b.t", "bridged": False},
    }}
    assert S.source_dataset(routing, "a") == "signal_a"
    assert S.source_dataset(routing, "b") is None
    assert S.source_dataset(routing, None) is None
    assert S.source_dataset(routing, "nope") is None


# --- the CLI is report-first ------------------------------------------------------


def _write_inputs(tmp_path, binding, runs):
    read = tmp_path / "read.json"
    read.write_text(json.dumps({"binding": binding, "rows": ROWS}))
    runs_csv = tmp_path / "source_runs.csv"
    with runs_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(runs[0]))
        writer.writeheader()
        writer.writerows(runs)
    return read, runs_csv


@pytest.fixture
def _fixed(monkeypatch):
    monkeypatch.setattr(gate, "_utcnow", lambda: NOW)
    monkeypatch.setattr(gate, "route_datasets", lambda root=None: ROUTES)


@pytest.mark.usefixtures("_fixed")
def test_the_cli_reports_what_it_would_block_and_exits_zero(tmp_path, capsys):
    read, runs = _write_inputs(tmp_path, BOUND, FRESH_RUNS)
    assert gate.main(["--read", str(read), "--source-runs", str(runs)]) == 0
    out = capsys.readouterr().out
    assert "would block    1 row(s)" in out
    assert "disagrees  override_required" in out
    assert "report-only" in out


@pytest.mark.usefixtures("_fixed")
def test_the_cli_exits_zero_when_everything_would_block(tmp_path, capsys):
    read, runs = _write_inputs(tmp_path, {**BOUND, "run_trigger_type": "MANUAL"}, FRESH_RUNS)
    assert gate.main(["--read", str(read), "--source-runs", str(runs), "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["mode"] == "report"
    assert doc["counts"]["source_unavailable"] == 4
    assert len(doc["would_block"]) == 4


@pytest.mark.usefixtures("_fixed")
def test_unreadable_input_is_not_a_clean_report(tmp_path, capsys):
    read, runs = _write_inputs(tmp_path, BOUND, FRESH_RUNS)
    assert gate.main(["--read", str(tmp_path / "missing.json"), "--source-runs", str(runs)]) == 2
    read.write_text(json.dumps({"binding": BOUND}))
    assert gate.main(["--read", str(read), "--source-runs", str(runs)]) == 2


def test_the_freshness_json_out_carries_the_rows_of_the_same_read(tmp_path, monkeypatch):
    rows = [_row("agrees")]
    monkeypatch.setattr(af, "_reconciliation_rows", lambda live, dirty: (rows, [], dict(BOUND)))
    monkeypatch.setattr(af, "snapshot_record", lambda obs: {
        "observation_snapshot_id": "a" * 64, "observed_from": "2026-10-01",
        "observed_to": "2026-10-01", "row_count": 0})
    monkeypatch.setattr(af, "plan", lambda rows, binding, root=None: ([], []))
    out = tmp_path / "read.json"
    assert af.main(["--json-out", str(out)], root=tmp_path) == 0
    doc = json.loads(out.read_text())
    assert doc["binding"]["run_id"] == "obs-run"
    assert doc["rows"] == rows
