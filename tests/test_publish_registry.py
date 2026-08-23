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


def test_dry_run_creates_no_static_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--dry-run` resolves ids but writes nothing to the platform.

    `resolve_static_models` used to create every missing model up front, before the dry-run
    early return, so a plan-only invocation performed a real `createStaticModel` mutation.
    With `create=not args.dry_run` a missing model is recorded as a would-create instead. No
    create, upload or run mutation may fire, the exit code is 0, and the plan names each
    would-create.
    """
    for table in pr.TABLES:
        write_csv(tmp_path, table, [{"slug": "a", "display_name": "A"}])

    def fake_graphql(query: str, variables: dict, token: str) -> dict:
        if query is pr.Q_DATASETS:
            return {"datasets": {"edges": [{"node": {"id": "ds", "name": "registry", "type": "STATIC_MODEL"}}]}}
        if query is pr.Q_STATIC:
            return {"staticModels": {"edges": []}}
        raise AssertionError(f"dry-run must not mutate the platform, but called: {query[:40]}")

    monkeypatch.setattr(pr, "graphql", fake_graphql)
    monkeypatch.setattr(pr, "upload", lambda path, url: pytest.fail("dry-run must not upload"))
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr("sys.argv", ["publish_registry", "--dry-run", "--dir", str(tmp_path)])

    assert pr.main() == 0
    out = capsys.readouterr().out
    for table in pr.TABLES:
        assert f"would create {table}" in out


def test_resolve_static_models_records_missing_as_would_create_when_not_creating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With `create=False` a missing model becomes `(None, False)` and no M_STATIC fires."""

    def fake_graphql(query: str, variables: dict, token: str) -> dict:
        if query is pr.Q_STATIC:
            return {"staticModels": {"edges": []}}
        raise AssertionError(f"create=False must not mutate, but called: {query[:40]}")

    monkeypatch.setattr(pr, "graphql", fake_graphql)
    models = pr.resolve_static_models("ds", "org", "tok", ("products",), create=False)
    assert models["products"] == (None, False)


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


def test_delete_mutation_asks_for_fields_because_it_returns_an_object() -> None:
    """`deleteStaticModel` returns SimplePayload!, so a bare call is a validation error.

    Sent without a selection set it is rejected with an HTTP 400 before it reaches the
    resolver, which is how the 2026-08-19 registry publish died. Pinning the selection
    set here because the symptom carried no hint of the cause.
    """
    assert "deleteStaticModel" in pr.M_DELETE
    body = pr.M_DELETE.split("deleteStaticModel", 1)[1]
    assert "{" in body and "success" in body


def test_http_error_bodies_are_surfaced(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 4xx carries the GraphQL validation message in a body urlopen never reads.

    Without this the only thing printed was "HTTP Error 400: Bad Request", which says
    nothing about which query was malformed or why.
    """
    import io
    import urllib.error

    def boom(request, timeout=None):  # noqa: ANN001, ARG001
        raise urllib.error.HTTPError(
            "https://api.oso.xyz/v1/graphql",
            400,
            "Bad Request",
            {},
            io.BytesIO(b'{"errors":[{"message":"Field must have a selection of subfields"}]}'),
        )

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(RuntimeError, match="selection of subfields"):
        pr.graphql("mutation{ x }", {}, "tok")


def test_a_failed_delete_does_not_fail_the_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Tidying must not gate publishing.

    The empty model is already excluded from the materialization run, so a token without
    delete permission should still publish the populated tables. Fatal here would mean a
    permission gap blocks the registry entirely.
    """
    for table in pr.TABLES:
        write_csv(
            tmp_path,
            table,
            [] if table == "tail_products" else [{"slug": "a", "display_name": "A"}],
        )

    uploaded: list[str] = []
    ran: list[list[str]] = []

    def fake_graphql(query: str, variables: dict, token: str) -> dict:
        if query is pr.Q_DATASETS:
            return {"datasets": {"edges": [{"node": {"id": "ds", "name": "registry", "type": "STATIC_MODEL"}}]}}
        if query is pr.Q_STATIC:
            return {
                "staticModels": {
                    "edges": [
                        {
                            "node": {
                                "id": f"id-{t}",
                                "name": t,
                                "materializations": {"totalCount": None if t == "tail_products" else 5},
                            }
                        }
                        for t in pr.TABLES
                    ]
                }
            }
        if query is pr.M_DELETE:
            raise RuntimeError("HTTP 403 from the API: User not authorized")
        if query is pr.M_URL:
            return {"createStaticModelUploadUrl": "https://upload.example/put"}
        if query is pr.M_RUN:
            ran.append(variables["input"]["selectedModels"])
            return {"createStaticModelRunRequest": {"run": {"id": "run-1", "status": "QUEUED"}}}
        raise AssertionError(f"unexpected query: {query[:40]}")

    monkeypatch.setattr(pr, "graphql", fake_graphql)
    monkeypatch.setattr(pr, "upload", lambda path, url: uploaded.append(path.name))
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr("sys.argv", ["publish_registry", "--dir", str(tmp_path)])

    assert pr.main() == 0
    assert "tail_products.csv" not in uploaded
    assert len(uploaded) == len(pr.TABLES) - 1
    assert "id-tail_products" not in ran[0]
    assert "WARNING could not delete empty tail_products" in capsys.readouterr().err
