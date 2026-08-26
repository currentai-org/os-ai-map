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


def test_dry_run_creates_no_dataset_when_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--dry-run` against a MISSING dataset must not fire `createDataset`.

    `resolve_dataset` used to create the dataset unconditionally, and `main()` called it before
    the dry-run early return, so a plan-only invocation against an empty datasets query wrote a
    real dataset. With `create=not args.dry_run` the resolver returns None and the plan reports
    a would-create dataset plus a would-create per populated table — with NO create, upload or
    run mutation of any kind.
    """
    for table in pr.TABLES:
        write_csv(tmp_path, table, [{"slug": "a", "display_name": "A"}])

    def fake_graphql(query: str, variables: dict, token: str) -> dict:
        if query is pr.Q_DATASETS:
            return {"datasets": {"edges": []}}
        raise AssertionError(f"dry-run with absent dataset must not mutate, but called: {query[:40]}")

    monkeypatch.setattr(pr, "graphql", fake_graphql)
    monkeypatch.setattr(pr, "upload", lambda path, url: pytest.fail("dry-run must not upload"))
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr("sys.argv", ["publish_registry", "--dry-run", "--dir", str(tmp_path)])

    assert pr.main() == 0
    out = capsys.readouterr().out
    assert "would create dataset" in out
    for table in pr.TABLES:
        assert f"would create {table}" in out


def test_resolve_dataset_returns_none_when_absent_and_not_creating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With `create=False` an absent dataset becomes None and no M_DATASET fires."""

    def fake_graphql(query: str, variables: dict, token: str) -> dict:
        if query is pr.Q_DATASETS:
            return {"datasets": {"edges": []}}
        raise AssertionError(f"create=False must not mutate, but called: {query[:40]}")

    monkeypatch.setattr(pr, "graphql", fake_graphql)
    assert pr.resolve_dataset("registry", "org", "tok", create=False) is None


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
    ran: list[str] = []

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
            assert "selectedModels" not in variables["input"]
            ran.append(variables["input"]["staticModelId"])
            return {"createStaticModelRunRequest": {"runGroup": {"id": "run-1", "status": "RUNNING"}}}
        if query is pr.Q_RUN_GROUP:
            assert variables["where"]["id"]["eq"] == "run-1"  # poll the exact group we created
            return {"runGroups": {"edges": [{"node": {"id": "run-1", "status": "SUCCESS"}}]}}
        raise AssertionError(f"unexpected query: {query[:40]}")

    monkeypatch.setattr(pr, "graphql", fake_graphql)
    monkeypatch.setattr(pr, "upload", lambda path, url: uploaded.append(path.name))
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr("sys.argv", ["publish_registry", "--dir", str(tmp_path)])

    assert pr.main() == 0
    assert "tail_products.csv" not in uploaded
    assert len(uploaded) == len(pr.TABLES) - 1
    # one run request per populated model, tail_products (empty) skipped from both
    assert len(ran) == len(pr.TABLES) - 1
    assert "id-tail_products" not in ran
    assert "WARNING could not delete empty tail_products" in capsys.readouterr().err


# --- run-group identity binding + serial execution -----------------------------------------

def _populated_tables() -> list[str]:
    """Every table except the empty one the guard skips, in publish order."""
    return [t for t in pr.TABLES if t != "tail_products"]


def _fake_platform(group_status: dict[str, list[str]]):
    """A fake `graphql` over the publish flow with a scripted run-group lifecycle.

    `group_status` maps a run-group id to the statuses returned on successive polls (the last
    repeats). A run request for `id-<table>` mints group id `grp-id-<table>`. `fake.calls`
    records `("run"|"poll", group_id)` in order so a test can assert identity and ordering.
    """
    calls: list[tuple[str, str]] = []
    poll_index: dict[str, int] = {}

    def fake(query: str, variables: dict, token: str) -> dict:
        if query is pr.Q_DATASETS:
            return {"datasets": {"edges": [{"node": {"id": "ds", "name": "registry", "type": "STATIC_MODEL"}}]}}
        if query is pr.Q_STATIC:
            return {"staticModels": {"edges": [
                {"node": {"id": f"id-{t}", "name": t,
                          "materializations": {"totalCount": None if t == "tail_products" else 5}}}
                for t in pr.TABLES]}}
        if query is pr.M_URL:
            return {"createStaticModelUploadUrl": "https://upload.example/put"}
        if query is pr.M_DELETE:
            return {"deleteStaticModel": {"success": True, "message": "ok"}}
        if query is pr.M_RUN:
            assert "selectedModels" not in variables["input"]  # obsolete batch input is gone
            gid = f"grp-{variables['input']['staticModelId']}"
            calls.append(("run", gid))
            return {"createStaticModelRunRequest": {"runGroup": {"id": gid, "status": "RUNNING"}}}
        if query is pr.Q_RUN_GROUP:
            gid = variables["where"]["id"]["eq"]
            calls.append(("poll", gid))
            seq = group_status.get(gid, ["SUCCESS"])
            i = poll_index.get(gid, 0)
            poll_index[gid] = i + 1
            return {"runGroups": {"edges": [{"node": {"id": gid, "status": seq[min(i, len(seq) - 1)]}}]}}
        raise AssertionError(f"unexpected query: {query[:40]}")

    fake.calls = calls  # type: ignore[attr-defined]
    return fake


def _segments(calls: list[tuple[str, str]]) -> list[tuple[str, list[str]]]:
    """Group the call log into (requested_group, [polled_groups...]) per run request."""
    segments: list[tuple[str, list[str]]] = []
    for op, gid in calls:
        if op == "run":
            segments.append((gid, []))
        else:
            segments[-1][1].append(gid)
    return segments


def _run_publish(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake) -> int:
    for t in pr.TABLES:
        write_csv(tmp_path, t, [] if t == "tail_products" else [{"slug": "a", "display_name": "A"}])
    monkeypatch.setattr(pr, "graphql", fake)
    monkeypatch.setattr(pr, "upload", lambda path, url: None)
    monkeypatch.setattr("time.sleep", lambda _s: None)  # no real waiting between polls
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")
    monkeypatch.setattr("sys.argv", ["publish_registry", "--dir", str(tmp_path)])
    return pr.main()


def test_polls_the_exact_run_group_and_waits_for_it(tmp_path, monkeypatch):
    """Each poll targets the run group the mutation returned — never the model's latest run —
    and the publisher waits for that group to leave RUNNING rather than accepting an instant
    answer. This is the guard against an earlier, unrelated SUCCESS satisfying the poll before
    the new run has even appeared."""
    populated = _populated_tables()
    # every group is RUNNING on the first poll and only SUCCEEDS on the second: if the code
    # accepted anything but this exact group's terminal state, it would finish too early.
    status = {f"grp-id-{t}": ["RUNNING", "SUCCESS"] for t in populated}
    fake = _fake_platform(status)
    assert _run_publish(tmp_path, monkeypatch, fake) == 0

    run_gids = [g for op, g in fake.calls if op == "run"]
    poll_gids = {g for op, g in fake.calls if op == "poll"}
    assert run_gids == [f"grp-id-{t}" for t in populated]   # one request per populated model
    assert poll_gids == set(run_gids)                        # polled exactly the groups we created
    # every requested group was polled, and only that group, before the next request:
    for requested, polled in _segments(fake.calls):
        assert polled and set(polled) == {requested}
        assert polled.count(requested) >= 2                  # RUNNING then SUCCESS — it waited


def test_next_model_is_requested_only_after_the_prior_group_succeeds(tmp_path, monkeypatch):
    """Serial execution: run request N+1 must not be issued until group N is terminal-SUCCESS."""
    populated = _populated_tables()
    status = {f"grp-id-{t}": ["RUNNING", "SUCCESS"] for t in populated}
    fake = _fake_platform(status)
    assert _run_publish(tmp_path, monkeypatch, fake) == 0
    # the log strictly alternates: run(g1), poll(g1).., run(g2), poll(g2).. — never run(g2)
    # before g1 has been polled, which (with main()==0) means g1 reached SUCCESS first.
    order = [op for op, _ in fake.calls]
    for i, (op, _) in enumerate(fake.calls):
        if op == "run" and i > 0:
            assert order[i - 1] == "poll", "a new run was requested before polling the previous group"


def test_a_failed_group_fails_fast_and_returns_nonzero(tmp_path, monkeypatch):
    """A FAILED run group stops the publish immediately (no further runs queued) and exits nonzero."""
    populated = _populated_tables()
    status = {f"grp-id-{t}": ["SUCCESS"] for t in populated}
    status[f"grp-id-{populated[1]}"] = ["RUNNING", "FAILED"]  # the second model fails
    fake = _fake_platform(status)
    assert _run_publish(tmp_path, monkeypatch, fake) == 1
    run_gids = [g for op, g in fake.calls if op == "run"]
    # fail-fast: only the first two models were ever requested — nothing after the failure
    assert run_gids == [f"grp-id-{populated[0]}", f"grp-id-{populated[1]}"]


def test_poll_run_group_treats_a_timeout_as_not_success(monkeypatch):
    """A run group stuck non-terminal at the deadline returns its last status, which is not
    SUCCESS, so the caller fails the publish rather than certifying a hung run."""
    def always_running(query, variables, token):
        return {"runGroups": {"edges": [{"node": {"id": variables["where"]["id"]["eq"], "status": "RUNNING"}}]}}

    monkeypatch.setattr(pr, "graphql", always_running)
    status = pr.poll_run_group("g-stuck", "tok", timeout=0.0, interval=0.0)
    assert status == "RUNNING"
    assert status != pr.GROUP_SUCCESS


def test_run_request_input_is_static_model_id_not_selected_models(tmp_path, monkeypatch):
    """The request carries a single staticModelId; the obsolete selectedModels batch input is gone."""
    inputs: list[dict] = []
    base = _fake_platform({f"grp-id-{t}": ["SUCCESS"] for t in _populated_tables()})

    def recording(query, variables, token):
        if query is pr.M_RUN:
            inputs.append(variables["input"])
        return base(query, variables, token)

    assert _run_publish(tmp_path, monkeypatch, recording) == 0
    assert inputs and all(set(i) == {"datasetId", "staticModelId"} for i in inputs)
    assert not any("selectedModels" in i for i in inputs)
