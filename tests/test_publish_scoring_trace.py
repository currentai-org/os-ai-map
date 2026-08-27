"""The scoring-trace publisher's safety surface — validation, no-write dry runs, immutable archives.

`build/publish_scoring_trace.py` uploads the three scoring-trace CSVs (`axis_facts`,
`axis_rule_matches`, `axis_results`) to OSO. The network path is a maintainer step, but the guards
that keep a bad or arbitrary CSV off the platform — the exact headers, the declaration-only identity,
the per-table grain, the ADR-001 `reproduces_recorded` dual-run gate — the promise that
`--plan`/`--dry-run` write nothing, and the immutable rollback archive (in its own subdirectory,
never the evaluation publisher's) are pure and pinned here.
"""

import sys

import build.publish_evaluation as PE
import build.publish_registry as PR
import build.publish_scoring_trace as P


def _write_csv(path, header, rows):
    lines = [",".join(header)] + [",".join(str(c) for c in r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# One tiny, internally-consistent trace: a single scored product reproducing its recorded score,
# with a matching fact and rule-match row, all under one declaration identity.
DVID = "d" * 64
SHA = "f012d854eb87"


def _valid_candidates(out_dir):
    def row(table, **over):
        base = {"declaration_version_id": DVID, "source_git_sha": SHA,
                "product_slug": "p", "category_slug": "c", "product_type": "model", "axis": "openness"}
        base.update(over)
        return [base[c] if base.get(c) is not None else "" for c in P.EXPECTED_HEADERS[table]]

    _write_csv(out_dir / "axis_facts.csv", P.EXPECTED_HEADERS["axis_facts"], [row(
        "axis_facts", dimension="weights", part_index=0, fact_kind="dimension",
        recorded_key="weights", recorded_value="open", normalized_value="open", in_declared_enum="True")])
    _write_csv(out_dir / "axis_rule_matches.csv", P.EXPECTED_HEADERS["axis_rule_matches"], [row(
        "axis_rule_matches", rule_index=0, rule_kind="when", outcome="fired", matched="True",
        non_tier_matched="True", tests_license_tier="False", wanted_tier="", rule_conditions="weights=open",
        result_score=4, result_class="open")])
    _write_csv(out_dir / "axis_results.csv", P.EXPECTED_HEADERS["axis_results"], [row(
        "axis_results", status="scored", result_score=4, result_class="open", matched_rule_index=0,
        matched_rule_kind="when", has_license_tiers="False", license_tier="", raw_license="MIT",
        recorded_score=4, recorded_class="open", reproduces_recorded="True", rule_count=1, deferral_reason="")])


def test_trace_tables_are_the_three_outputs():
    assert P.TRACE_TABLES == ("axis_facts", "axis_rule_matches", "axis_results")


# --- validation before any mutation ----------------------------------------------


def test_valid_candidates_pass_validation(tmp_path):
    _valid_candidates(tmp_path)
    assert P.validate_candidates(tmp_path) == []


def test_arbitrary_headers_are_rejected(tmp_path):
    for t in P.TRACE_TABLES:
        _write_csv(tmp_path / f"{t}.csv", ["x", "y"], [[1, 2]])
    problems = P.validate_candidates(tmp_path)
    assert any("header does not match" in p for p in problems)


def test_empty_table_is_rejected(tmp_path):
    _valid_candidates(tmp_path)
    header = (tmp_path / "axis_facts.csv").read_text().splitlines()[0]
    (tmp_path / "axis_facts.csv").write_text(header + "\n", encoding="utf-8")
    assert any("empty" in p for p in P.validate_candidates(tmp_path))


def test_inconsistent_identity_within_a_file_is_rejected(tmp_path):
    _valid_candidates(tmp_path)
    # A second facts row under a different source_git_sha breaks within-file constancy.
    path = tmp_path / "axis_facts.csv"
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[1] = "deadbeefcafe"  # source_git_sha column
    path.write_text("\n".join(lines + [",".join(row)]) + "\n", encoding="utf-8")
    assert any("source_git_sha" in p for p in P.validate_candidates(tmp_path))


def test_identity_differing_across_files_is_rejected(tmp_path):
    _valid_candidates(tmp_path)
    path = tmp_path / "axis_results.csv"
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[0] = "e" * 64  # a different declaration_version_id than facts/rules carry
    lines[1] = ",".join(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("declaration_version_id" in p for p in P.validate_candidates(tmp_path))


def test_a_scored_row_that_does_not_reproduce_is_rejected(tmp_path):
    """The ADR-001 dual-run gate: a scored result must reproduce the recorded score, or it is a
    check_rubric disagreement that is resolved in the evaluator, never deployed."""
    _valid_candidates(tmp_path)
    path = tmp_path / "axis_results.csv"
    header = P.EXPECTED_HEADERS["axis_results"]
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[header.index("reproduces_recorded")] = "False"
    lines[1] = ",".join(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("reproduce" in p for p in P.validate_candidates(tmp_path))


def test_a_deferred_row_with_blank_reproduces_is_fine(tmp_path):
    """Deferred results carry an empty reproduces_recorded and must NOT trip the dual-run gate."""
    _valid_candidates(tmp_path)
    path = tmp_path / "axis_results.csv"
    header = P.EXPECTED_HEADERS["axis_results"]
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[header.index("status")] = "deferred"
    row[header.index("reproduces_recorded")] = ""
    row[header.index("deferral_reason")] = "no_recipe"
    lines[1] = ",".join(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert P.validate_candidates(tmp_path) == []


def test_grain_uniqueness_is_enforced(tmp_path):
    _valid_candidates(tmp_path)
    path = tmp_path / "axis_results.csv"
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines + [lines[1]]) + "\n", encoding="utf-8")  # duplicate the one result
    assert any("grain" in p for p in P.validate_candidates(tmp_path))


def test_a_fact_with_no_result_row_is_rejected(tmp_path):
    _valid_candidates(tmp_path)
    path = tmp_path / "axis_facts.csv"
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[2] = "orphan"  # product_slug not present in axis_results
    path.write_text("\n".join(lines + [",".join(row)]) + "\n", encoding="utf-8")
    assert any("no axis_results row" in p for p in P.validate_candidates(tmp_path))


# --- --plan / --dry-run write nothing --------------------------------------------


def test_plan_validates_offline_and_writes_nothing(tmp_path, monkeypatch):
    _valid_candidates(tmp_path)

    def _no_network(*a, **k):
        raise AssertionError("--plan must not hit the network")

    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--plan", "--dir", str(tmp_path)])
    before = set(tmp_path.iterdir())
    assert P.main() == 0
    assert set(tmp_path.iterdir()) == before


def test_dry_run_with_credentials_makes_no_mutation_and_no_write(tmp_path, monkeypatch):
    _valid_candidates(tmp_path)
    monkeypatch.setenv("OSO_API_KEY", "test-token")
    monkeypatch.setenv("OSO_ORG_ID", "test-org")

    def fake_graphql(query, variables, token):
        if "datasets(" in query:
            return {"datasets": {"edges": [{"node": {"id": "ds1", "name": "evaluation"}}]}}
        if "staticModels(" in query:
            return {"staticModels": {"edges": []}}
        raise AssertionError(f"a dry run must issue no mutation, got: {query[:48]}")

    monkeypatch.setattr(P, "graphql", fake_graphql)
    monkeypatch.setattr(PR, "graphql", fake_graphql)
    monkeypatch.setattr(PE, "graphql", fake_graphql)  # resolve_evaluation_dataset uses PE's graphql
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dry-run", "--dir", str(tmp_path)])
    before = set(tmp_path.iterdir())
    assert P.main() == 0
    assert set(tmp_path.iterdir()) == before
    assert not P.deployments_dir(tmp_path).exists()


def test_publish_without_credentials_refuses(tmp_path, monkeypatch):
    _valid_candidates(tmp_path)
    monkeypatch.delenv("OSO_API_KEY", raising=False)
    monkeypatch.delenv("OSO_ORG_ID", raising=False)

    def _no_network(*a, **k):
        raise AssertionError("must not hit the network without credentials")

    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dry-run", "--dir", str(tmp_path)])
    assert P.main() == 2


def test_missing_csv_is_a_loud_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--plan", "--dir", str(tmp_path)])
    assert P.main() == 2


# --- per-model run requests, exact-group polling, fail-fast ----------------------


def _platform_graphql(requested):
    def fake_graphql(query, variables, token):
        if query is PE.Q_DATASETS or "datasets(" in query:
            return {"datasets": {"edges": [{"node": {"id": "ds-eval", "name": "evaluation",
                                                     "type": "STATIC_MODEL"}}]}}
        if query is PR.Q_STATIC or "staticModels(" in query:
            return {"staticModels": {"edges": [
                {"node": {"id": f"id-{t}", "name": t, "materializations": {"totalCount": 1}}}
                for t in P.TRACE_TABLES
            ]}}
        if query is P.M_URL:
            return {"createStaticModelUploadUrl": "https://upload.example/put"}
        if query is P.M_RUN:
            requested.append(variables["input"])
            return {"createStaticModelRunRequest":
                    {"runGroup": {"id": f"grp-for-{variables['input']['staticModelId']}", "status": "QUEUED"}}}
        raise AssertionError(f"unexpected query: {query[:60]}")
    return fake_graphql


def test_load_run_is_requested_once_per_model_with_static_model_id(tmp_path, monkeypatch):
    _valid_candidates(tmp_path)
    requested: list[dict] = []
    fake = _platform_graphql(requested)
    monkeypatch.setattr(P, "graphql", fake)
    monkeypatch.setattr(PR, "graphql", fake)
    monkeypatch.setattr(PE, "graphql", fake)
    monkeypatch.setattr(P, "upload", lambda path, url: None)
    monkeypatch.setattr(P, "poll_run_group", lambda gid, token, timeout=1800.0: "SUCCESS")
    monkeypatch.setattr(P, "deployed_table_state", lambda dataset, table: {"rows": 0, "columns": []})
    monkeypatch.setattr(P, "deployment_mismatches", lambda expected, deployed: ["stop here"])
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dir", str(tmp_path)])

    assert P.main() == 2  # stopped at the injected mismatch, after all three runs were requested
    assert len(requested) == len(P.TRACE_TABLES), "one run request per model"
    for payload in requested:
        assert payload["datasetId"] == "ds-eval"
        assert "selectedModels" not in payload
    assert [pl["staticModelId"] for pl in requested] == [f"id-{t}" for t in P.TRACE_TABLES]


def test_the_publisher_polls_the_exact_run_group_the_mutation_returned(tmp_path, monkeypatch):
    _valid_candidates(tmp_path)
    requested: list[dict] = []
    polled: list[str] = []
    fake = _platform_graphql(requested)
    monkeypatch.setattr(P, "graphql", fake)
    monkeypatch.setattr(PR, "graphql", fake)
    monkeypatch.setattr(PE, "graphql", fake)
    monkeypatch.setattr(P, "upload", lambda path, url: None)

    def record_poll(gid, token, timeout=1800.0):
        polled.append(gid)
        return "SUCCESS"

    monkeypatch.setattr(P, "poll_run_group", record_poll)
    monkeypatch.setattr(P, "deployed_table_state", lambda dataset, table: {"rows": 0, "columns": []})
    monkeypatch.setattr(P, "deployment_mismatches", lambda expected, deployed: ["stop here"])
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dir", str(tmp_path)])

    assert P.main() == 2
    assert polled == [f"grp-for-id-{t}" for t in P.TRACE_TABLES]


def test_a_failed_run_stops_the_deploy_before_the_next_model(tmp_path, monkeypatch):
    _valid_candidates(tmp_path)
    requested: list[dict] = []
    fake = _platform_graphql(requested)
    monkeypatch.setattr(P, "graphql", fake)
    monkeypatch.setattr(PR, "graphql", fake)
    monkeypatch.setattr(PE, "graphql", fake)
    monkeypatch.setattr(P, "upload", lambda path, url: None)
    monkeypatch.setattr(P, "poll_run_group", lambda gid, token, timeout=1800.0: "FAILED")

    def boom(dataset, table):
        raise AssertionError("must not read deployed state when a run failed")

    monkeypatch.setattr(P, "deployed_table_state", boom)
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dir", str(tmp_path)])

    assert P.main() == 2
    assert len(requested) == 1, "the second model is not requested after the first fails"
    assert P.latest_archive(tmp_path) is None, "a failed deploy archives nothing"


# --- the deployed-schema comparison and the immutable archive --------------------


def test_deployment_mismatches_catches_row_and_schema_drift():
    expected = {t: {"rows": 3, "columns": ["a", "b"], "all_null_columns": []} for t in P.TRACE_TABLES}
    deployed = {t: {"rows": 3, "columns": ["a", "b"]} for t in P.TRACE_TABLES}
    assert P.deployment_mismatches(expected, deployed) == []
    wrong_rows = {**deployed, "axis_facts": {"rows": 2, "columns": ["a", "b"]}}
    assert any("rows" in m for m in P.deployment_mismatches(expected, wrong_rows))
    wrong_cols = {**deployed, "axis_results": {"rows": 3, "columns": ["a"]}}
    assert any("columns" in m for m in P.deployment_mismatches(expected, wrong_cols))


def test_deployment_archive_is_immutable_and_in_its_own_subdir(tmp_path):
    _valid_candidates(tmp_path)
    receipt = P.build_receipt(tmp_path)
    archive = P.archive_deployment(tmp_path, receipt)
    assert archive.exists() and (archive / "receipt.json").exists()
    for table in P.TRACE_TABLES:
        assert (archive / f"{table}.csv").exists()
    # Its own subdirectory — never the evaluation publisher's `deployments/`.
    assert P.deployments_dir(tmp_path).name == "scoring-trace-deployments"
    assert P.deployments_dir(tmp_path) != PE.deployments_dir(tmp_path)
    assert P.latest_archive(tmp_path) == archive
    try:
        P.archive_deployment(tmp_path, receipt)
    except RuntimeError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("archive_deployment must refuse to overwrite an existing deployment id")
