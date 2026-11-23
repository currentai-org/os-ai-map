import json
from datetime import date

import pytest
import yaml

from build import proposals
from tests.test_reverify import _SOURCE_RECIPE, _score_with_sources, _src

TODAY = date(2026, 11, 23)


def _proposal(**kw):
    base = {
        "proposal_id": "redate:p:openness:2026-11-22",
        "kind": "redate",
        "product_slug": "p",
        "axis": "openness",
        "observed_at": "2026-11-22",
        "producer": {"model": "currentai.proposals.redate", "revision": "r1"},
        "evidence": [{"url": "https://a/LICENSE", "outcome": "unchanged"}],
    }
    return {**base, **kw}


def _corpus(tmp_path):
    return _score_with_sources(tmp_path, [
        _src("https://a/LICENSE", "a" * 64, ["license"]),
        _src("https://a/README", "b" * 64, ["source"]),
    ], recipe=_SOURCE_RECIPE)


def _same_bytes(url, **kw):
    return {"url": url, "http_status": 200,
            "content_sha256": "a" * 64 if url.endswith("LICENSE") else "b" * 64}


def _openness(root):
    return yaml.safe_load((root / "sources" / "scores" / "p.yaml").read_text())["openness"]


def _outcomes(report):
    return [(p["proposal_id"], p["outcome"]) for p in report["proposals"]]


def test_a_confirmed_proposal_is_applied_from_the_appliers_own_reading(tmp_path):
    root = _corpus(tmp_path)
    report = proposals.apply_redate(root, [_proposal()], TODAY, fetch=_same_bytes)
    assert _outcomes(report) == [("redate:p:openness:2026-11-22", "applied")]
    assert str(_openness(root)["last_verified"]) == "2026-11-23"


def test_the_proposals_evidence_decides_nothing(tmp_path):
    # The producer says every source was unchanged; the applier's fetch finds drift.
    root = _corpus(tmp_path)
    before = (root / "sources" / "scores" / "p.yaml").read_text()

    def drifted(url, **kw):
        return {"url": url, "http_status": 200, "content_sha256": "c" * 64}

    report = proposals.apply_redate(root, [_proposal()], TODAY, fetch=drifted)
    assert _outcomes(report) == [("redate:p:openness:2026-11-22", "not_confirmed")]
    assert "drifted" in report["proposals"][0]["reason"]
    assert (root / "sources" / "scores" / "p.yaml").read_text() == before


def test_an_axis_verified_since_the_observation_is_current_and_not_fetched(tmp_path):
    root = _corpus(tmp_path)

    def no_fetch(url, **kw):
        raise AssertionError("a current axis must not be re-read")

    report = proposals.apply_redate(root, [_proposal(observed_at="2026-08-13")], TODAY, fetch=no_fetch)
    assert _outcomes(report) == [("redate:p:openness:2026-11-22", "already_current")]


def test_reading_the_same_rows_again_applies_nothing_twice(tmp_path):
    root = _corpus(tmp_path)
    proposals.apply_redate(root, [_proposal()], TODAY, fetch=_same_bytes)
    after_first = (root / "sources" / "scores" / "p.yaml").read_text()
    report = proposals.apply_redate(root, [_proposal()], TODAY, fetch=_same_bytes)
    assert _outcomes(report) == [("redate:p:openness:2026-11-22", "already_current")]
    assert (root / "sources" / "scores" / "p.yaml").read_text() == after_first


def test_proposals_for_one_axis_share_one_reading(tmp_path):
    root = _corpus(tmp_path)
    fetched = []

    def counting(url, **kw):
        fetched.append(url)
        return _same_bytes(url)

    rows = [_proposal(), _proposal(proposal_id="other-producer", producer={"model": "scout"})]
    report = proposals.apply_redate(root, rows, TODAY, fetch=counting)
    assert sorted(o for _pid, o in _outcomes(report)) == ["applied", "applied"]
    assert sorted(fetched) == ["https://a/LICENSE", "https://a/README"]
    assert len(report["products"]) == 1


@pytest.mark.parametrize("row, reason", [
    (_proposal(axis="adoption"), "limited to openness"),
    (_proposal(product_slug="absent"), "no score file"),
    (_proposal(observed_at="2026-99-99"), "observed_at"),
    (_proposal(evidence=[]), "evidence"),
    ({**_proposal(), "score": 9}, "Additional properties"),
])
def test_rows_the_handler_refuses_are_rejected_with_a_reason(tmp_path, row, reason):
    root = _corpus(tmp_path)
    before = (root / "sources" / "scores" / "p.yaml").read_text()
    report = proposals.apply_redate(root, [row], TODAY, fetch=_same_bytes)
    [outcome] = report["proposals"]
    assert outcome["outcome"] == "rejected"
    assert reason in outcome["reason"]
    assert (root / "sources" / "scores" / "p.yaml").read_text() == before


def test_rows_of_another_kind_are_left_for_that_kinds_run(tmp_path):
    root = _corpus(tmp_path)
    report = proposals.apply_redate(root, [_proposal(kind="registry_row")], TODAY, fetch=_same_bytes)
    assert report["proposals"] == [] and report["products"] == []


def test_a_dry_run_reports_the_outcome_and_writes_nothing(tmp_path):
    root = _corpus(tmp_path)
    before = (root / "sources" / "scores" / "p.yaml").read_text()
    report = proposals.apply_redate(root, [_proposal()], TODAY, fetch=_same_bytes, dry_run=True)
    assert _outcomes(report) == [("redate:p:openness:2026-11-22", "applied")]
    assert (root / "sources" / "scores" / "p.yaml").read_text() == before


def test_a_warehouse_row_becomes_a_proposal_that_passes_the_schema():
    row = {
        "proposal_id": "x", "kind": "redate", "product_slug": "p", "axis": "openness",
        "observed_at": "2026-11-22", "producer_model": "m", "producer_revision": float("nan"),
        "evidence": json.dumps([{"url": "https://a/LICENSE", "outcome": "verified"}]),
        "created_at": "2026-11-22 06:00:00.000 UTC",
    }
    proposal = proposals.row_to_proposal(row)
    assert proposal["producer"] == {"model": "m"}
    assert proposals.schema_error(proposal, proposals.load_schema()) is None


def test_unparseable_evidence_is_rejected_by_the_schema_not_a_crash():
    row = {"proposal_id": "x", "kind": "redate", "product_slug": "p", "axis": "openness",
           "observed_at": "2026-11-22", "producer_model": "m", "evidence": "{not json"}
    assert proposals.schema_error(proposals.row_to_proposal(row), proposals.load_schema())


def test_the_table_query_refuses_anything_but_a_three_part_name():
    sql = proposals.table_query("currentai.proposals.redate", "redate", 7)
    assert "FROM currentai.proposals.redate WHERE kind = 'redate'" in sql
    assert "INTERVAL '7' DAY" in sql
    with pytest.raises(ValueError):
        proposals.table_query("currentai.proposals.redate; DROP TABLE x", "redate", 7)
    with pytest.raises(ValueError):
        proposals.table_query("currentai.proposals.redate", "anything", 7)


def test_every_kind_the_schema_allows_has_a_handler_and_an_adr_004_label():
    kinds = set(proposals.load_schema()["properties"]["kind"]["enum"])
    assert kinds == set(proposals.HANDLERS) == set(proposals.KIND_LABELS)
    assert set(proposals.KIND_LABELS.values()) <= {"tail-batch", "freshness", "promotion", "re-band"}


def test_the_summary_counts_every_outcome_and_lists_what_was_not_applied(tmp_path):
    root = _corpus(tmp_path)
    rows = [_proposal(), _proposal(proposal_id="bad", axis="adoption")]
    report = proposals.apply_redate(root, rows, TODAY, fetch=_same_bytes)
    text = proposals.summary_markdown(report)
    assert "2 proposal(s) read from `currentai.proposals.redate@r1`" in text
    assert "**1 applied.**" in text and "**1 rejected.**" in text
    assert "**0 not confirmed.**" in text and "**0 already current.**" in text
    assert "rejected       p" in text and "bad" in text
    assert "Deterministic re-verification of the 1 product(s) the proposals named" in text
    assert "oldest" not in text


def test_the_cli_applies_a_file_and_summarizes_the_saved_report(tmp_path, capsys):
    # A current axis keeps the CLI path off the network: nothing is due, so nothing is fetched.
    root = _corpus(tmp_path)
    rows = tmp_path / "proposals.jsonl"
    rows.write_text(json.dumps(_proposal(observed_at="2026-08-01")) + "\n")
    saved = tmp_path / "report.json"
    assert proposals.main(["apply", "--kind", "redate", "--from-file", str(rows),
                           "--report", str(saved), "--today", "2026-11-23"], root=root) == 0
    assert "already_current=1" in capsys.readouterr().out
    assert proposals.main(["summarize", str(saved)], root=root) == 0
    assert "**1 already current.**" in capsys.readouterr().out
    assert proposals.main(["label", "redate"], root=root) == 0
    assert capsys.readouterr().out.strip() == "freshness"


def test_the_summary_shows_what_producers_reported_as_untrusted_and_unread(tmp_path):
    root = _corpus(tmp_path)
    rows = [_proposal(evidence=[{"url": "https://a/LICENSE", "outcome": "unchanged",
                                 "content_sha256": "a" * 64}]),
            _proposal(proposal_id="bad", evidence="{not json")]
    report = proposals.apply_redate(root, rows, TODAY, fetch=_same_bytes)
    by_id = {p["proposal_id"]: p for p in report["proposals"]}
    assert by_id["redate:p:openness:2026-11-22"]["evidence"][0]["url"] == "https://a/LICENSE"
    text = proposals.summary_markdown(report)
    shown = text[text.index("What the producers reported"):]
    assert "untrusted; the applier did not read it" in shown
    assert "unchanged https://a/LICENSE sha256=aaaaaaaaaaaa" in shown
    assert "bad (currentai.proposals.redate@r1, rejected)" in shown
    assert "unreadable: '{not json'" in shown


def test_long_lists_are_capped_and_point_at_the_report():
    many = [{"proposal_id": f"p{i}", "product_slug": "p", "axis": "openness", "producer": "m",
             "outcome": "rejected", "reason": "x", "evidence": []} for i in range(proposals.LIST_CAP + 5)]
    text = proposals.summary_markdown({"kind": "redate", "proposals": many, "products": []})
    assert "... and 5 more, in the run's report artifact" in text
