"""The cutover pre-flight invariants (§0.2 / §8): single identity + semantic no-change.

`build/cutover_preflight.py` proves, before any upload, that the `evaluator_version` cutover changes
IDENTITY ONLY — every candidate shares one `declaration_version_id` (and one `source_git_sha` where
carried), and each live table's candidate equals the deployed rows once identity/timestamp columns are
projected out. Pure functions, exercised here with synthetic rows — no platform read or mutation.
"""

import sys

import build.cutover_preflight as CP


def _candidates(dvid="d" * 64, sha="f012d854eb87"):
    """One row per cutover table, all sharing the same declaration + source identity."""
    return {
        "product_adoption_measurements": [{"declaration_version_id": dvid, "product_slug": "p", "raw_value": "1"}],
        "adoption_reconciliation": [{"declaration_version_id": dvid, "product_slug": "p",
                                     "status": "source_unavailable", "evaluated_at": "2026-08-27T00:00:00Z"}],
        "axis_facts": [{"declaration_version_id": dvid, "source_git_sha": sha, "product_slug": "p", "axis": "openness"}],
        "axis_rule_matches": [{"declaration_version_id": dvid, "source_git_sha": sha, "product_slug": "p", "rule_index": "0"}],
        "axis_results": [{"declaration_version_id": dvid, "source_git_sha": sha, "product_slug": "p", "result_score": "4"}],
    }


# --- single identity -----------------------------------------------------------------------------


def test_shared_identity_passes():
    assert CP.single_identity_problems(_candidates()) == []


def test_a_second_declaration_id_across_tables_is_rejected():
    cands = _candidates()
    cands["axis_results"] = [{**cands["axis_results"][0], "declaration_version_id": "e" * 64}]
    problems = CP.single_identity_problems(cands)
    assert any("share one declaration_version_id" in p for p in problems)


def test_a_second_source_sha_across_the_trace_tables_is_rejected():
    cands = _candidates()
    cands["axis_facts"] = [{**cands["axis_facts"][0], "source_git_sha": "deadbeefcafe"}]
    problems = CP.single_identity_problems(cands)
    assert any("share one source_git_sha" in p for p in problems)


def test_a_non_constant_identity_within_a_file_is_rejected():
    cands = _candidates()
    row = cands["axis_facts"][0]
    cands["axis_facts"] = [row, {**row, "declaration_version_id": "e" * 64}]
    problems = CP.single_identity_problems(cands)
    assert any("not constant within the file" in p for p in problems)


# --- completeness --------------------------------------------------------------------------------


def test_an_incomplete_cutover_set_is_rejected():
    cands = _candidates()
    del cands["axis_results"]
    assert any("missing cutover candidate" in p for p in CP.completeness_problems(cands))
    assert CP.completeness_problems(_candidates()) == []


# --- semantic no-change --------------------------------------------------------------------------


def test_identity_only_change_passes_even_across_types():
    """Only declaration_version_id / source_git_sha differ, and the deployed side is loader-TYPED
    (int result_score, not the CSV string) — canonicalization makes them compare equal."""
    candidate = [{"declaration_version_id": "NEW", "source_git_sha": "newsha",
                  "product_slug": "p", "axis": "openness", "result_score": "4"}]
    deployed = [{"declaration_version_id": "OLD", "source_git_sha": "oldsha",
                 "product_slug": "p", "axis": "openness", "result_score": 4, "_dlt_id": "x"}]
    assert CP.semantic_no_change_problems("axis_results", candidate, deployed) == []


def test_a_changed_content_value_is_rejected():
    candidate = [{"declaration_version_id": "NEW", "source_git_sha": "s", "product_slug": "p", "result_score": "4"}]
    deployed = [{"declaration_version_id": "OLD", "source_git_sha": "s", "product_slug": "p", "result_score": "5"}]
    problems = CP.semantic_no_change_problems("axis_results", candidate, deployed)
    assert any("NOT reproduced" in p for p in problems)
    assert any("NOT present" in p for p in problems)


def test_row_multiplicity_difference_is_rejected():
    row = {"declaration_version_id": "NEW", "source_git_sha": "s", "product_slug": "p", "result_score": "4"}
    old = {**row, "declaration_version_id": "OLD"}
    problems = CP.semantic_no_change_problems("axis_results", [row, row], [old])
    assert any("NOT present" in p for p in problems)  # the duplicate candidate row has no deployed match


def test_an_all_null_candidate_column_dropped_by_the_loader_is_tolerated():
    """`adoption_reconciliation.override_id` is empty in every row and the loader drops it; its absence
    downstream is expected, not a content difference."""
    candidate = [{"declaration_version_id": "NEW", "product_slug": "p", "status": "x",
                  "override_id": "", "evaluated_at": "2026-08-27T01:00:00Z"}]
    deployed = [{"declaration_version_id": "OLD", "product_slug": "p", "status": "x",
                 "evaluated_at": "2026-08-27T09:00:00Z"}]  # no override_id, different evaluated_at
    assert CP.semantic_no_change_problems("adoption_reconciliation", candidate, deployed) == []


def test_a_candidate_column_with_data_missing_downstream_is_rejected():
    candidate = [{"declaration_version_id": "NEW", "product_slug": "p", "status": "x",
                  "override_id": "ovr-1", "evaluated_at": "t"}]
    deployed = [{"declaration_version_id": "OLD", "product_slug": "p", "status": "x", "evaluated_at": "t2"}]
    problems = CP.semantic_no_change_problems("adoption_reconciliation", candidate, deployed)
    assert any("carries data but is absent" in p for p in problems)


def test_a_deployed_only_content_column_is_rejected():
    candidate = [{"declaration_version_id": "NEW", "source_git_sha": "s", "product_slug": "p"}]
    deployed = [{"declaration_version_id": "OLD", "source_git_sha": "s", "product_slug": "p", "surprise": "z"}]
    problems = CP.semantic_no_change_problems("axis_results", candidate, deployed)
    assert any("does not declare" in p for p in problems)


def test_empty_sides_are_reported_not_crashed():
    assert CP.semantic_no_change_problems("axis_results", [], [{"a": 1}]) == ["axis_results: no candidate rows"]
    assert CP.semantic_no_change_problems("axis_results", [{"a": 1}], []) == [
        "axis_results: no deployed rows to compare against"]


# --- the offline CLI -----------------------------------------------------------------------------


def _write_candidate_csvs(directory, cands):
    import csv

    for table, rows in cands.items():
        path = directory / f"{table}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def test_cli_runs_the_single_identity_check_offline(tmp_path, monkeypatch, capsys):
    _write_candidate_csvs(tmp_path, _candidates())
    monkeypatch.setattr(sys, "argv", ["cutover_preflight", "--dir", str(tmp_path)])
    assert CP.main() == 0
    out = capsys.readouterr().out
    assert "single-identity: ok" in out
    assert "semantic-no-change: skipped" in out


def test_cli_fails_on_a_split_identity(tmp_path, monkeypatch):
    cands = _candidates()
    cands["axis_results"] = [{**cands["axis_results"][0], "declaration_version_id": "e" * 64}]
    _write_candidate_csvs(tmp_path, cands)
    monkeypatch.setattr(sys, "argv", ["cutover_preflight", "--dir", str(tmp_path)])
    assert CP.main() == 2


def test_cli_semantic_against_a_deployed_export(tmp_path, monkeypatch):
    """A deployed CSV export that matches the candidate on content (differing only on identity /
    evaluated_at) passes; a changed value fails."""
    cands = _candidates()
    cand_dir = tmp_path / "cand"
    cand_dir.mkdir()
    _write_candidate_csvs(cand_dir, cands)

    # The deployed export: same content, re-keyed to the OLD identity + a stale evaluated_at.
    deployed = {table: [dict(rows[0])] for table, rows in cands.items()}
    for rows in deployed.values():
        rows[0]["declaration_version_id"] = "o" * 64
        if "source_git_sha" in rows[0]:
            rows[0]["source_git_sha"] = "oldsha000000"
        if "evaluated_at" in rows[0]:
            rows[0]["evaluated_at"] = "2020-01-01T00:00:00Z"
    export = tmp_path / "deployed"
    export.mkdir()
    _write_candidate_csvs(export, deployed)

    monkeypatch.setattr(sys, "argv",
                        ["cutover_preflight", "--dir", str(cand_dir), "--deployed-dir", str(export)])
    assert CP.main() == 0

    # Now tamper one deployed content value → the semantic check fails.
    deployed["axis_results"][0]["result_score"] = "5"
    _write_candidate_csvs(export, deployed)
    assert CP.main() == 2
