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
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--plan", "--dir", str(tmp_path)])
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
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--dry-run", "--dir", str(tmp_path)])
    before = set(tmp_path.iterdir())
    assert P.main() == 0
    assert set(tmp_path.iterdir()) == before
    assert not P.deployments_dir(tmp_path).exists()


def test_publish_without_credentials_refuses(tmp_path, monkeypatch):
    _valid_candidates(tmp_path)
    monkeypatch.delenv("OSO_API_KEY", raising=False)
    monkeypatch.delenv("OSO_ORG_ID", raising=False)

    def _no_network(*args, **kwargs):
        raise AssertionError("must not hit the network without credentials")

    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--dry-run", "--dir", str(tmp_path)])
    assert P.main() == 2


def test_missing_csv_is_a_loud_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--plan", "--dir", str(tmp_path)])
    assert P.main() == 2


# --- the archive is gated on terminal SUCCESS and verified deployed data ---------


def test_runs_all_succeeded_requires_terminal_success():
    ok = {"product_adoption_measurements": ("r1", "SUCCESS"),
          "adoption_reconciliation": ("r2", "SUCCESS")}
    assert P.runs_all_succeeded(ok) == []
    # A queued/running/failed run is not success — each is a problem, so no archive.
    for bad in ("RUNNING", "QUEUED", "FAILED", "UNKNOWN", "TIMEOUT"):
        statuses = {"product_adoption_measurements": ("r1", "SUCCESS"),
                    "adoption_reconciliation": ("r2", bad)}
        assert P.runs_all_succeeded(statuses), f"{bad} must be treated as not-succeeded"


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


def test_poll_run_returns_last_status_at_timeout(monkeypatch):
    """A run that never reaches a terminal state returns its last (non-SUCCESS) status, so the
    caller does not archive a queued run."""
    monkeypatch.setattr(P, "run_status", lambda run_id, token: "RUNNING")
    assert P.poll_run("r1", "tok", timeout=0.0, interval=0.0) == "RUNNING"


# --- the immutable deployment archive --------------------------------------------


def test_deployment_archive_is_immutable(tmp_path):
    _valid_candidates(tmp_path)
    receipt = P.build_receipt(tmp_path)
    archive = P.archive_deployment(tmp_path, receipt)
    assert archive.exists() and (archive / "receipt.json").exists()
    for table in P.EVAL_TABLES:
        assert (archive / f"{table}.csv").exists()
    assert P.latest_archive(tmp_path) == archive
    # A second archive of the same identities is refused — the record is written once.
    try:
        P.archive_deployment(tmp_path, receipt)
    except RuntimeError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("archive_deployment must refuse to overwrite an existing deployment id")
