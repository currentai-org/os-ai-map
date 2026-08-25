"""The evaluation publisher's offline surface — provenance capture and the mutation-free plan.

`build/publish_evaluation.py` uploads the two evaluation CSVs to OSO. The network path needs
credentials and is a maintainer step, but the plan and the provenance receipt (which a rollback
depends on) are pure and are pinned here. A `--plan` run performs no network call and no mutation.
"""

import hashlib
import sys

from build import publish_evaluation as P


def _write_csv(path, header, rows):
    lines = [",".join(header)] + [",".join(str(c) for c in r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_eval_tables_are_the_two_evaluation_outputs():
    assert P.EVAL_TABLES == ("product_adoption_measurements", "adoption_reconciliation")


def test_csv_provenance_reports_rows_columns_and_sha(tmp_path):
    path = _write_csv(tmp_path / "t.csv", ["a", "b"], [[1, 2], [3, 4], [5, 6]])
    prov = P.csv_provenance(path)
    assert prov["rows"] == 3
    assert prov["columns"] == ["a", "b"]
    assert prov["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert prov["bytes"] == len(path.read_bytes())


def test_build_receipt_covers_the_present_tables(tmp_path):
    _write_csv(tmp_path / "product_adoption_measurements.csv", ["x"], [[1]])
    _write_csv(tmp_path / "adoption_reconciliation.csv", ["y"], [[2], [3]])
    receipt = P.build_receipt(tmp_path)
    assert set(receipt) == set(P.EVAL_TABLES)
    assert receipt["product_adoption_measurements"]["rows"] == 1
    assert receipt["adoption_reconciliation"]["rows"] == 2


def test_plan_is_offline_and_mutation_free(tmp_path, monkeypatch, capsys):
    """`--plan` prints the plan with row counts and SHA-256 and touches no network — proven by
    replacing the module's `graphql` with a tripwire that fails if called."""
    _write_csv(tmp_path / "product_adoption_measurements.csv", ["x"], [[1]])
    _write_csv(tmp_path / "adoption_reconciliation.csv", ["y"], [[2]])

    def _no_network(*args, **kwargs):
        raise AssertionError("--plan must not hit the network")

    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--plan", "--dir", str(tmp_path)])
    assert P.main() == 0
    out = capsys.readouterr().out
    assert "product_adoption_measurements.csv" in out and "sha256" in out


def test_missing_csv_is_a_loud_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--plan", "--dir", str(tmp_path)])
    assert P.main() == 2  # no CSVs present


def test_publish_without_credentials_refuses(tmp_path, monkeypatch):
    _write_csv(tmp_path / "product_adoption_measurements.csv", ["x"], [[1]])
    _write_csv(tmp_path / "adoption_reconciliation.csv", ["y"], [[2]])
    monkeypatch.delenv("OSO_API_KEY", raising=False)
    monkeypatch.delenv("OSO_ORG_ID", raising=False)

    def _no_network(*args, **kwargs):
        raise AssertionError("must not hit the network without credentials")

    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(sys, "argv", ["publish_evaluation", "--dry-run", "--dir", str(tmp_path)])
    assert P.main() == 2
