"""The evaluation publisher's safety surface — validation, no-write dry runs, immutable archives.

`build/publish_evaluation.py` uploads the two evaluation CSVs to OSO. The network path is a
maintainer step, but the guards that keep a bad or arbitrary CSV off the platform, the promise that
`--plan`/`--dry-run` write nothing, and the immutable rollback archive are pure and pinned here.
"""

import hashlib
import sys

import build.publish_evaluation as P
import build.publish_registry as PR
from build import serialize_evaluation as SE
from build.observation_snapshot import rows_from_parquet


def _write_csv(path, header, rows):
    lines = [",".join(header)] + [",".join(str(c) for c in r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _valid_candidates(out_dir):
    """Write real, valid evaluation CSVs (over the frozen baseline) into out_dir."""
    measurements, reconciliation = SE.build_tables(
        rows_from_parquet(), allow_dirty=True, evaluated_at=None
    )
    SE.write_csv(measurements, P.EXPECTED_HEADERS["product_adoption_measurements"],
                 out_dir / "product_adoption_measurements.csv")
    SE.write_csv(reconciliation, P.EXPECTED_HEADERS["adoption_reconciliation"],
                 out_dir / "adoption_reconciliation.csv")


def test_eval_tables_are_the_two_evaluation_outputs():
    assert P.EVAL_TABLES == ("product_adoption_measurements", "adoption_reconciliation")


def test_csv_provenance_reports_rows_columns_and_sha(tmp_path):
    path = _write_csv(tmp_path / "t.csv", ["a", "b"], [[1, 2], [3, 4], [5, 6]])
    prov = P.csv_provenance(path)
    assert prov["rows"] == 3
    assert prov["columns"] == ["a", "b"]
    assert prov["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


# --- validation before any mutation ----------------------------------------------


def test_valid_candidates_pass_validation(tmp_path):
    _valid_candidates(tmp_path)
    assert P.validate_candidates(tmp_path, P.ROOT) == []


def test_arbitrary_headers_are_rejected(tmp_path):
    _write_csv(tmp_path / "product_adoption_measurements.csv", ["x", "y"], [[1, 2]])
    _write_csv(tmp_path / "adoption_reconciliation.csv", ["x", "y"], [[1, 2]])
    problems = P.validate_candidates(tmp_path, P.ROOT)
    assert any("header does not match" in p for p in problems)


def test_empty_table_is_rejected(tmp_path):
    _valid_candidates(tmp_path)
    # Truncate reconciliation to its header only.
    header = (tmp_path / "adoption_reconciliation.csv").read_text().splitlines()[0]
    (tmp_path / "adoption_reconciliation.csv").write_text(header + "\n", encoding="utf-8")
    problems = P.validate_candidates(tmp_path, P.ROOT)
    assert any("empty" in p for p in problems)


def test_inconsistent_identity_across_files_is_rejected(tmp_path):
    _valid_candidates(tmp_path)
    # Flip the observation_snapshot_id in one reconciliation row so it is no longer constant.
    path = tmp_path / "adoption_reconciliation.csv"
    lines = path.read_text().splitlines()
    header = lines[0].split(",")
    idx = header.index("observation_snapshot_id")
    row = lines[1].split(",")
    row[idx] = "deadbeef" * 8
    lines[1] = ",".join(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    problems = P.validate_candidates(tmp_path, P.ROOT)
    assert any("observation_snapshot_id" in p for p in problems)


# --- --plan / --dry-run write nothing --------------------------------------------


def test_plan_validates_offline_and_writes_nothing(tmp_path, monkeypatch):
    _valid_candidates(tmp_path)

    def _no_network(*args, **kwargs):
        raise AssertionError("--plan must not hit the network")

    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--plan", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])
    before = set(tmp_path.iterdir())
    assert P.main() == 0
    assert set(tmp_path.iterdir()) == before  # no deployments dir, no receipt


def test_dry_run_with_credentials_makes_no_mutation_and_no_write(tmp_path, monkeypatch):
    """The blocker's exact reproduction: valid creds, read-only resolution, and NOT a single write."""
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
    monkeypatch.setattr(PR, "graphql", fake_graphql)  # resolve_static_models uses publish_registry's
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--dry-run", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])
    before = set(tmp_path.iterdir())
    assert P.main() == 0
    assert set(tmp_path.iterdir()) == before
    assert not (tmp_path / "archive").exists()  # a dry run writes no archive and no occurrence log


def test_publish_without_credentials_refuses(tmp_path, monkeypatch):
    _valid_candidates(tmp_path)
    monkeypatch.delenv("OSO_API_KEY", raising=False)
    monkeypatch.delenv("OSO_ORG_ID", raising=False)

    def _no_network(*args, **kwargs):
        raise AssertionError("must not hit the network without credentials")

    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--dry-run", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])
    assert P.main() == 2


def test_missing_csv_is_a_loud_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--plan", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])
    assert P.main() == 2


# --- the archive is gated on terminal SUCCESS and verified deployed data ---------


def test_run_groups_all_succeeded_requires_terminal_success():
    ok = {"product_adoption_measurements": ("g1", "SUCCESS"),
          "adoption_reconciliation": ("g2", "SUCCESS")}
    assert P.run_groups_all_succeeded(ok) == []
    # A queued/running/failed run group is not success — each is a problem, so no archive.
    for bad in ("RUNNING", "QUEUED", "FAILED", "UNKNOWN", "TIMEOUT"):
        statuses = {"product_adoption_measurements": ("g1", "SUCCESS"),
                    "adoption_reconciliation": ("g2", bad)}
        assert P.run_groups_all_succeeded(statuses), f"{bad} must be treated as not-succeeded"


def test_deployment_mismatches_catches_row_and_schema_drift():
    expected = {
        "product_adoption_measurements": {"rows": 377, "columns": ["a", "b"]},
        "adoption_reconciliation": {"rows": 522, "columns": ["c", "d"]},
    }
    assert P.deployment_mismatches(expected, expected) == []
    wrong_rows = {**expected, "adoption_reconciliation": {"rows": 521, "columns": ["c", "d"]}}
    assert any("rows" in m for m in P.deployment_mismatches(expected, wrong_rows))
    wrong_cols = {**expected, "product_adoption_measurements": {"rows": 377, "columns": ["a"]}}
    assert any("columns" in m for m in P.deployment_mismatches(expected, wrong_cols))


def test_the_publisher_polls_the_exact_run_group_the_mutation_returned(tmp_path, monkeypatch):
    """The reconciled polling (#380) is bound to the run group `createStaticModelRunRequest`
    returns — never a model's latest run — so an earlier unrelated success can't satisfy the wait.

    Pinned by capturing the id handed to `poll_run_group` and asserting it is the group id the
    mutation returned for that model, in order.
    """
    _valid_candidates(tmp_path)
    polled: list[str] = []

    def fake_graphql(query, variables, token):
        if query is P.Q_DATASETS:
            return {"datasets": {"edges": [{"node": {"id": "ds-eval", "name": "evaluation",
                                                     "type": "STATIC_MODEL"}}]}}
        if query is PR.Q_STATIC:
            return {"staticModels": {"edges": [
                {"node": {"id": f"id-{t}", "name": t, "materializations": {"totalCount": 1}}}
                for t in P.EVAL_TABLES
            ]}}
        if query is P.M_URL:
            return {"createStaticModelUploadUrl": "https://upload.example/put"}
        if query is P.M_RUN:
            model = variables["input"]["staticModelId"]
            return {"createStaticModelRunRequest":
                    {"runGroup": {"id": f"grp-for-{model}", "status": "QUEUED"}}}
        raise AssertionError(f"unexpected query: {query[:60]}")

    def record_poll(group_id, token, timeout=1800.0):
        polled.append(group_id)
        return "SUCCESS"

    monkeypatch.setattr(P, "graphql", fake_graphql)
    monkeypatch.setattr(PR, "graphql", fake_graphql)
    monkeypatch.setattr(P, "upload", lambda path, url: None)
    monkeypatch.setattr(P, "poll_run_group", record_poll)
    monkeypatch.setattr(P, "deployed_table_state",
                        lambda dataset, table: {"rows": 0, "columns": []})
    monkeypatch.setattr(P, "deployment_mismatches", lambda expected, deployed: ["stop here"])
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])

    assert P.main() == 2  # stopped at the injected mismatch, after polling every group
    assert polled == [f"grp-for-id-{t}" for t in P.EVAL_TABLES]


# --- the immutable deployment archive --------------------------------------------


def test_deployment_archive_is_immutable_and_rollback_is_an_occurrence(tmp_path):
    _valid_candidates(tmp_path)
    receipt = P.build_receipt(tmp_path)
    root = tmp_path / "archive"
    did = P.deployment_id(tmp_path)

    # First store of a fresh identity is a deploy: the immutable dir + receipt + CSVs are written.
    target, kind = P.archive.store(root, did, P.archived_files(tmp_path), receipt)
    assert kind == "deploy"
    assert target.exists() and (target / "receipt.json").exists()
    for table in P.EVAL_TABLES:
        assert (target / f"{table}.csv").exists()
    assert P.archive.current_live_archive(root) == target
    written = target.stat().st_mtime_ns

    # Re-storing the SAME identity (re-publishing archived bytes) is a rollback: the immutable dir is
    # NOT rewritten, and an occurrence is appended — live-state comes from the log, not mtimes.
    target2, kind2 = P.archive.store(root, did, P.archived_files(tmp_path), receipt)
    assert kind2 == "rollback" and target2 == target
    assert target.stat().st_mtime_ns == written, "the immutable archive was rewritten"
    occ = P.archive.occurrences(root)
    assert [o["kind"] for o in occ] == ["deploy", "rollback"]
    assert P.archive.current_live(root) == did


def test_load_run_is_requested_once_per_model_and_awaited(tmp_path, monkeypatch):
    """Each table gets its OWN run request, naming exactly one model, and is awaited in turn.

    The input is per static model — `CreateStaticModelRunRequestInput` takes
    `(datasetId, staticModelId)`, not a `selectedModels` list (the API drift #380/#381 corrected).
    A single request naming BOTH models would fan out into two runs and return one run group, which
    cannot certify its siblings; the two would also race to create the dataset's Trino schema. One
    request per model, awaited to its own run group's terminal state, is what this pins.
    """
    _valid_candidates(tmp_path)
    requested: list[dict] = []

    def fake_graphql(query, variables, token):
        if query is P.Q_DATASETS:
            return {"datasets": {"edges": [{"node": {"id": "ds-eval", "name": "evaluation",
                                                     "type": "STATIC_MODEL"}}]}}
        if query is PR.Q_STATIC:
            return {"staticModels": {"edges": [
                {"node": {"id": f"id-{t}", "name": t, "materializations": {"totalCount": 1}}}
                for t in P.EVAL_TABLES
            ]}}
        if query is P.M_URL:
            return {"createStaticModelUploadUrl": "https://upload.example/put"}
        if query is P.M_RUN:
            requested.append(variables["input"])
            return {"createStaticModelRunRequest":
                    {"runGroup": {"id": f"group-{len(requested)}", "status": "QUEUED"}}}
        raise AssertionError(f"unexpected query: {query[:60]}")

    monkeypatch.setattr(P, "graphql", fake_graphql)
    monkeypatch.setattr(PR, "graphql", fake_graphql)
    monkeypatch.setattr(P, "upload", lambda path, url: None)
    monkeypatch.setattr(P, "poll_run_group", lambda group_id, token, timeout=1800.0: "SUCCESS")
    monkeypatch.setattr(P, "deployed_table_state",
                        lambda dataset, table: {"rows": 0, "columns": []})
    # Stop before the archive: this test is about the request shape, not the receipt.
    monkeypatch.setattr(P, "deployment_mismatches", lambda expected, deployed: ["stop here"])
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])

    assert P.main() == 2  # stopped at the injected mismatch, after both runs were requested

    assert len(requested) == len(P.EVAL_TABLES), "one run request per model"
    for payload in requested:
        assert payload["datasetId"] == "ds-eval"
        assert "selectedModels" not in payload, "the batch selectedModels payload is gone"
    assert [pl["staticModelId"] for pl in requested] == [f"id-{t}" for t in P.EVAL_TABLES]


def test_a_failed_run_stops_the_deploy_before_the_next_model(tmp_path, monkeypatch):
    """A table that fails to load stops the deploy — no further run is requested, nothing archived."""
    _valid_candidates(tmp_path)
    requested: list[dict] = []

    def fake_graphql(query, variables, token):
        if query is P.Q_DATASETS:
            return {"datasets": {"edges": [{"node": {"id": "ds-eval", "name": "evaluation",
                                                     "type": "STATIC_MODEL"}}]}}
        if query is PR.Q_STATIC:
            return {"staticModels": {"edges": [
                {"node": {"id": f"id-{t}", "name": t, "materializations": {"totalCount": 1}}}
                for t in P.EVAL_TABLES
            ]}}
        if query is P.M_URL:
            return {"createStaticModelUploadUrl": "https://upload.example/put"}
        if query is P.M_RUN:
            requested.append(variables["input"])
            return {"createStaticModelRunRequest": {"runGroup": {"id": "group-1", "status": "QUEUED"}}}
        raise AssertionError(f"unexpected query: {query[:60]}")

    def boom(dataset, table):
        raise AssertionError("must not read deployed state when a run failed")

    monkeypatch.setattr(P, "graphql", fake_graphql)
    monkeypatch.setattr(PR, "graphql", fake_graphql)
    monkeypatch.setattr(P, "upload", lambda path, url: None)
    monkeypatch.setattr(P, "poll_run_group", lambda group_id, token, timeout=1800.0: "FAILED")
    monkeypatch.setattr(P, "deployed_table_state", boom)
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])

    assert P.main() == 2
    assert len(requested) == 1, "the second model is not requested after the first fails"
    assert P.archive.current_live(tmp_path / "archive") is None, "a failed deploy records no occurrence"


# --- the deployed-schema comparison ----------------------------------------------


def test_all_null_candidate_column_may_be_absent_but_a_populated_one_may_not():
    """The loader drops a column that is null in every row; a column with data going missing is a bug."""
    expected = {
        "product_adoption_measurements": {"rows": 2, "columns": ["a", "b"], "all_null_columns": []},
        "adoption_reconciliation": {
            "rows": 2, "columns": ["c", "override_id"], "all_null_columns": ["override_id"],
        },
    }
    deployed = {
        "product_adoption_measurements": {"rows": 2, "columns": ["a", "b"]},
        "adoption_reconciliation": {"rows": 2, "columns": ["c"]},  # override_id dropped: expected
    }
    assert P.deployment_mismatches(expected, deployed) == []

    # The same absence is a mismatch when the candidate column DID carry data.
    with_data = {**expected, "adoption_reconciliation": {
        "rows": 2, "columns": ["c", "override_id"], "all_null_columns": [],
    }}
    assert any("missing" in m for m in P.deployment_mismatches(with_data, deployed))

    # An undeclared extra column is always a mismatch.
    extra = {**deployed, "product_adoption_measurements": {"rows": 2, "columns": ["a", "b", "z"]}}
    assert any("undeclared" in m for m in P.deployment_mismatches(expected, extra))


def test_loader_bookkeeping_columns_are_excluded_from_the_deployed_schema(monkeypatch):
    """`_dlt_*` columns are on every loaded table and in no candidate; they are not a mismatch."""
    monkeypatch.setattr(
        "build.warehouse.query",
        lambda sql: [{"a": 1, "b": 2, "_dlt_id": "x", "_dlt_load_id": "y"}],
    )
    state = P.deployed_table_state("evaluation", "product_adoption_measurements")
    assert state == {"rows": 1, "columns": ["a", "b"]}


def test_deployed_state_retries_while_the_catalog_catches_up(monkeypatch):
    """A just-loaded table is briefly invisible to the query catalog; that is lag, not a failure."""
    calls = {"n": 0}

    def flaky(sql):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("USER_ERROR: TablesNotFound - Tables do not exist or are inaccessible")
        return [{"a": 1}]

    monkeypatch.setattr("build.warehouse.query", flaky)
    state = P.deployed_table_state("evaluation", "adoption_reconciliation",
                                   timeout=10.0, interval=0.0)
    assert state == {"rows": 1, "columns": ["a"]}
    assert calls["n"] == 3


def test_deployed_state_gives_up_at_the_deadline(monkeypatch):
    """Still missing at the deadline raises, so a table that never loaded is never archived."""
    def always_missing(sql):
        raise RuntimeError("USER_ERROR: TablesNotFound - Tables do not exist or are inaccessible")

    monkeypatch.setattr("build.warehouse.query", always_missing)
    try:
        P.deployed_table_state("evaluation", "adoption_reconciliation", timeout=0.0, interval=0.0)
    except RuntimeError as exc:
        assert "TablesNotFound" in str(exc)
    else:
        raise AssertionError("a table missing at the deadline must raise")


def test_all_null_columns_are_recorded_in_the_provenance(tmp_path):
    path = _write_csv(tmp_path / "t.csv", ["a", "empty"], [[1, ""], [2, ""]])
    assert P.csv_provenance(path)["all_null_columns"] == ["empty"]
    path = _write_csv(tmp_path / "u.csv", ["a", "some"], [[1, ""], [2, "v"]])
    assert P.csv_provenance(path)["all_null_columns"] == []
