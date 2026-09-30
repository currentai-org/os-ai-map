"""The review queue sorts each open question by who can move it, and never loses one."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from build import review_queue as rq
from build.check_contradictions import Finding


def _write(root: Path, rel: str, doc: dict) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc))


def test_classify_reads_the_reason_in_order():
    assert rq.classify("settled by the adoption re-band after the 5 Oct reconciliation") == "schedule"
    assert rq.classify("the pricing page returned HTTP 403 from this pass") == "fetch"
    assert rq.classify("Settling it needs an editor ruling on the no-license files") == "ruling"
    assert rq.classify("No benchmark evidence exists in any fetched page") == "evidence"
    # A schedule marker wins over a fetch marker in the same reason: the run settles it anyway.
    assert rq.classify("returned 403; waits for the reconciliation") == "schedule"


def test_classify_survives_a_line_wrap_inside_a_marker():
    assert rq.classify("the page cannot be\n  re-fetched") == "fetch"


def test_every_held_axis_becomes_one_row(tmp_path):
    _write(tmp_path, "sources/verification_queue.yaml", {"version": 1, "held": {
        "alpha": {"openness": {"because": "needs a ruling", "since": "2026-09-01"},
                  "adoption": {"because": "re-band after the reconciliation", "since": "2026-09-02"}},
        "beta": {"capability": {"because": "nothing found", "since": "2026-09-03"}},
    }})
    rows = rq.gather(tmp_path)
    assert {r.id: r.waits_on for r in rows} == {
        "hold:alpha:adoption": "schedule",
        "hold:alpha:openness": "ruling",
        "hold:beta:capability": "evidence",
    }


def test_only_deferred_rulings_are_open_questions(tmp_path):
    _write(tmp_path, "docs/rulings/log.yaml", {"version": 1, "rulings": [
        {"id": "R-2026-09-01-a", "date": "2026-09-01", "status": "in-force", "question": "q1"},
        {"id": "R-2026-09-02-a", "date": "2026-09-02", "status": "deferred", "question": "q2",
         "reasoning": "wait for the peer set", "refs": ["#759"]},
        {"id": "R-2026-09-03-a", "date": "2026-09-03", "status": "replaced", "question": "q3"},
    ]})
    rows = rq.gather(tmp_path)
    assert [r.id for r in rows] == ["ruling:R-2026-09-02-a"]
    assert rows[0].waits_on == "ruling"
    assert "wait for the peer set" in rows[0].detail


def test_contradictions_join_only_when_asked(tmp_path):
    finding = Finding("retirement", "gamma", "no end_of_life", "archived", "github.com/x/y",
                      "is_archived", "2026-09-28", "archived")
    assert rq.contradiction_rows([finding])[0].id == "contradiction:retirement:gamma:github.com/x/y"
    assert rq.gather(tmp_path) == []


def test_age_is_measured_from_since():
    row = rq.Row(id="x", source="hold", subject="s", waits_on="evidence", detail="", since="2026-09-01")
    assert row.age_days(date(2026, 9, 30)) == 29
    assert rq.Row(id="y", source="hold", subject="s", waits_on="evidence", detail="").age_days(date.today()) is None


def test_main_exits_zero_with_rows_present(tmp_path, capsys):
    _write(tmp_path, "sources/verification_queue.yaml", {"version": 1, "held": {
        "alpha": {"openness": {"because": "needs a ruling", "since": "2026-09-01"}}}})
    assert rq.main(["--markdown"], root=tmp_path, today=date(2026, 9, 30)) == 0
    out = capsys.readouterr().out
    assert "## Waits on ruling (1)" in out and "hold:alpha:openness" in out
