"""The empty-table guard in the registry publisher.

`tail_products` turned the 2026-08-19 materialization run red after all 16 populated
tables had already loaded: dlt infers a schema from records, so a header-only CSV
produces no table and the runner fails the whole run. These tests pin the three
outcomes an empty table can have, and the names say which contract each one holds.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from build import publish_registry as pr


def write_csv(directory: Path, table: str, rows: list[dict]) -> None:
    header = ["slug", "display_name"]
    with (directory / f"{table}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def test_data_rows_does_not_count_the_header(tmp_path: Path) -> None:
    write_csv(tmp_path, "empty", [])
    write_csv(tmp_path, "full", [{"slug": "a", "display_name": "A"}])
    assert pr.data_rows(tmp_path / "empty.csv") == 0
    assert pr.data_rows(tmp_path / "full.csv") == 1


def test_an_empty_table_is_never_created(monkeypatch: pytest.MonkeyPatch) -> None:
    """No model for a table with no rows: a model that cannot succeed must not exist."""
    created: list[str] = []

    def fake_graphql(query: str, variables: dict, token: str) -> dict:
        if query is pr.Q_STATIC:
            return {"staticModels": {"edges": []}}
        if query is pr.M_STATIC:
            name = variables["input"]["name"]
            created.append(name)
            return {"createStaticModel": {"staticModel": {"id": f"id-{name}", "name": name}}}
        raise AssertionError(f"unexpected query: {query[:40]}")

    monkeypatch.setattr(pr, "graphql", fake_graphql)
    models = pr.resolve_static_models("ds", "org", "tok", ("products",))
    assert created == ["products"]
    assert "tail_products" not in models


def test_materialization_count_marks_a_model_that_holds_a_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A totalCount of zero or null means never materialized, which is what makes a
    delete safe. Reading it as materialized would block a legitimate publish."""

    def fake_graphql(query: str, variables: dict, token: str) -> dict:
        return {
            "staticModels": {
                "edges": [
                    {"node": {"id": "1", "name": "products", "materializations": {"totalCount": 139}}},
                    {"node": {"id": "2", "name": "tail_products", "materializations": {"totalCount": None}}},
                    {"node": {"id": "3", "name": "fresh", "materializations": None}},
                ]
            }
        }

    monkeypatch.setattr(pr, "graphql", fake_graphql)
    models = pr.resolve_static_models("ds", "org", "tok", ())
    assert models["products"] == ("1", True)
    assert models["tail_products"] == ("2", False)
    assert models["fresh"] == ("3", False)


def test_publish_refuses_when_an_empty_table_already_holds_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Serializing zero rows for a table that HAS a materialized table stops the push.

    Publishing nothing would leave the previous rows served as though the repo still
    declared them, which is the stale-data direction this repo cares most about. The
    exit code is what CI reads, so it is what this asserts.
    """
    for table in pr.TABLES:
        write_csv(tmp_path, table, [] if table == "products" else [{"slug": "a", "display_name": "A"}])

    def fake_graphql(query: str, variables: dict, token: str) -> dict:
        if query is pr.Q_DATASETS:
            return {"datasets": {"edges": [{"node": {"id": "ds", "name": "registry", "type": "STATIC_MODEL"}}]}}
        if query is pr.Q_STATIC:
            return {
                "staticModels": {
                    "edges": [
                        {"node": {"id": f"id-{t}", "name": t, "materializations": {"totalCount": 5}}}
                        for t in pr.TABLES
                    ]
                }
            }
        if query is pr.M_DELETE:
            raise AssertionError("a populated table must never be deleted unattended")
        raise AssertionError(f"unexpected query: {query[:40]}")

    monkeypatch.setattr(pr, "graphql", fake_graphql)
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr("sys.argv", ["publish_registry", "--dir", str(tmp_path)])

    assert pr.main() == 2
    assert "products" in capsys.readouterr().err
