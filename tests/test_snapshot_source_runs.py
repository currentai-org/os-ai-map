"""Synthetic gates over build/snapshot_source_runs.py -- no live API is touched.

Mirrors tests/test_assets_inventory.py's platform-audit tests: the parsing, pagination, digest
and receipt-validator contracts are pinned against hand-built run nodes, so the module can be
trusted without credentials. The run->model binding is asserted to come from materializations,
never from timestamps, because that is the one inference the module must refuse to make.
"""

from __future__ import annotations

import build.snapshot_source_runs as S

CAPTURED = "2026-08-23T12:00:00+00:00"


# --- synthetic run nodes ----------------------------------------------------------

def _mat(mat_id: str, table_id: str, dataset_id: str, created_at: str) -> dict:
    return {"node": {"id": mat_id, "tableId": table_id, "datasetId": dataset_id,
                     "createdAt": created_at}}


def _step(name: str, mats: list[dict], display_name: str | None = None) -> dict:
    return {"node": {"name": name, "displayName": display_name or name, "status": "SUCCESS",
                     "materializations": {"edges": mats}}}


def _run(run_id: str, *, status="SUCCESS", trigger="SCHEDULED", run_type="MODEL",
         requested_by=None, started="2026-08-23T01:00:00Z", steps=None) -> dict:
    return {
        "id": run_id, "triggerType": trigger, "runType": run_type, "status": status,
        "queuedAt": "2026-08-23T00:59:00Z", "startedAt": started,
        "finishedAt": "2026-08-23T01:05:00Z", "lastHeartbeatAt": None,
        "requestedBy": ({"id": requested_by} if requested_by else None),
        "steps": {"edges": steps or []},
    }


def _one_materialized_run() -> dict:
    return _run("run-1", steps=[
        _step("evaluate_model_repo_state",
              [_mat("mat-1", "tbl-repo-state", "ds-github", "2026-08-23T01:04:00Z")]),
    ])


# --- parsing the row contract -----------------------------------------------------

def test_parse_binds_model_from_materialization_and_keeps_four_ids_distinct():
    rows = S.parse_run_rows("ds-github", "signal_github", _one_materialized_run(), CAPTURED)
    assert len(rows) == 1
    row = rows[0]
    # Every contract column is present, and the four identifiers are separate values.
    assert set(row) == set(S.COLUMNS)
    assert row["source_run_id"] == "run-1"
    assert row["materialization_id"] == "mat-1"
    assert row["table_id"] == "tbl-repo-state"          # = materialization.tableId (the model)
    assert row["dataset_id"] == "ds-github"             # = materialization.datasetId
    assert row["source_dataset_id"] == "ds-github"
    assert row["source_dataset_name"] == "signal_github"
    assert row["model_name"] == "repo_state"            # parsed from evaluate_model_repo_state
    assert len({row["source_run_id"], row["materialization_id"], row["table_id"]}) == 3


def test_binding_is_from_materializations_never_timestamps():
    """A run whose materialization createdAt is nowhere near its finishedAt still binds to the
    table named by that materialization -- the binding is structural, not temporal."""
    node = _run("run-x", started="2026-08-23T01:00:00Z", steps=[
        _step("evaluate_model_hub_state",
              [_mat("mat-x", "tbl-hub-state", "ds-hf", "1999-01-01T00:00:00Z")]),
    ])
    (row,) = S.parse_run_rows("ds-hf", "signal_huggingface", node, CAPTURED)
    assert row["table_id"] == "tbl-hub-state"
    assert row["materialized_at"] == "1999-01-01T00:00:00Z"  # carried, not used for binding


def test_run_with_no_materialization_still_emits_a_row():
    node = _run("run-empty", status="FAILED", steps=[])
    (row,) = S.parse_run_rows("ds-github", "signal_github", node, CAPTURED)
    assert row["source_run_id"] == "run-empty"
    assert row["execution_status"] == "FAILED"
    assert row["table_id"] is None and row["materialization_id"] is None
    assert row["model_name"] is None and row["materialized_at"] is None
    assert row["dataset_id"] is None


def test_multiple_materializations_yield_one_row_each():
    node = _run("run-multi", steps=[
        _step("evaluate_model_repo_state",
              [_mat("m1", "t1", "ds-github", "2026-08-23T01:04:00Z")]),
        _step("evaluate_model_product_adoption",
              [_mat("m2", "t2", "ds-github", "2026-08-23T01:04:30Z")]),
    ])
    rows = S.parse_run_rows("ds-github", "signal_github", node, CAPTURED)
    assert {r["table_id"] for r in rows} == {"t1", "t2"}
    assert {r["model_name"] for r in rows} == {"repo_state", "product_adoption"}
    assert all(r["source_run_id"] == "run-multi" for r in rows)


# --- execution status is real; scope is unknown -----------------------------------

def test_execution_status_is_real_but_scope_is_unknown():
    node = _run("run-s", status="RUNNING")
    (row,) = S.parse_run_rows("ds-github", "signal_github", node, CAPTURED)
    assert row["execution_status"] == "RUNNING"          # the platform's real status
    assert row["expected_scope"] == "unknown"
    assert row["scope_status"] == "unknown"


# --- output hygiene: actor is an enum, no raw id or error text --------------------

def test_actor_type_is_an_enum_and_the_raw_requested_by_id_never_appears():
    user_run = _run("r-user", trigger="MANUAL", requested_by="user-abc-123")
    system_run = _run("r-sys", trigger="SCHEDULED", requested_by=None)
    (u,) = S.parse_run_rows("ds", "signal_github", user_run, CAPTURED)
    (s,) = S.parse_run_rows("ds", "signal_github", system_run, CAPTURED)
    assert u["actor_type"] == "user" and s["actor_type"] == "system"
    assert "user-abc-123" not in u.values()
    assert "requested_by" not in u and "requestedBy" not in u
    # error_class is a normalized token slot, null here -- never raw error text.
    assert u["error_class"] is None


# --- complete pagination ----------------------------------------------------------

def test_pagination_reads_every_page_not_just_the_first(monkeypatch):
    """A two-page connection must yield all runs. The stub keys off the `after` cursor: page one
    advertises hasNextPage, page two closes it. Reading only page one would drop run-2."""
    page_one = {"runs": {
        "pageInfo": {"hasNextPage": True, "endCursor": "CURSOR-1"},
        "edges": [{"node": _run("run-1")}],
    }}
    page_two = {"runs": {
        "pageInfo": {"hasNextPage": False, "endCursor": None},
        "edges": [{"node": _run("run-2")}],
    }}

    calls = {"n": 0}

    def fake_graphql(query, variables, token):
        calls["n"] += 1
        return page_one if variables.get("after") is None else page_two

    monkeypatch.setattr(S, "graphql", fake_graphql)
    nodes = S.fetch_runs("ds-github", token="t", page_size=1)
    assert [n["id"] for n in nodes] == ["run-1", "run-2"]
    assert calls["n"] == 2  # both pages were actually fetched


def test_two_runs_from_one_fire_are_both_kept(monkeypatch):
    """Two runs started at the same minute are distinct rows -- never deduped by dataset+time."""
    same_minute = "2026-08-23T01:00:00Z"
    page = {"runs": {
        "pageInfo": {"hasNextPage": False, "endCursor": None},
        "edges": [{"node": _run("run-a", started=same_minute)},
                  {"node": _run("run-b", started=same_minute)}],
    }}
    monkeypatch.setattr(S, "graphql", lambda q, v, t: page)
    nodes = S.fetch_runs("ds-github", token="t")
    assert {n["id"] for n in nodes} == {"run-a", "run-b"}


# --- deterministic digest ---------------------------------------------------------

def test_digest_is_order_independent_and_ignores_captured_at():
    rows_a = (
        S.parse_run_rows("ds", "signal_github", _run("r1"), "2026-08-23T12:00:00+00:00")
        + S.parse_run_rows("ds", "signal_github", _one_materialized_run(), "2026-08-23T12:00:00+00:00")
    )
    # Same run-set, reversed order, a DIFFERENT captured_at.
    rows_b = list(reversed(
        S.parse_run_rows("ds", "signal_github", _run("r1"), "2030-01-01T00:00:00+00:00")
        + S.parse_run_rows("ds", "signal_github", _one_materialized_run(), "2030-01-01T00:00:00+00:00")
    ))
    assert S.content_digest(rows_a) == S.content_digest(rows_b)


def test_digest_changes_when_a_non_captured_field_changes():
    base = S.parse_run_rows("ds", "signal_github", _run("r1", status="SUCCESS"), CAPTURED)
    changed = S.parse_run_rows("ds", "signal_github", _run("r1", status="FAILED"), CAPTURED)
    assert S.content_digest(base) != S.content_digest(changed)


# --- receipt validator ------------------------------------------------------------

def _valid_receipt() -> dict:
    rows = (
        S.parse_run_rows("ds-github", "signal_github", _one_materialized_run(), CAPTURED)
        + S.parse_run_rows("ds-hf", "signal_huggingface", _run("run-2"), CAPTURED)
    )
    return S.build_receipt(
        rows,
        requested_datasets=S.SOURCE_DATASETS,
        per_dataset_run_counts={"signal_github": 1, "signal_huggingface": 1},
        unresolved_datasets=["signal_packages", "signal_pypi"],
        captured_at=CAPTURED,
    )


def test_receipt_validator_accepts_a_wellformed_receipt():
    receipt = _valid_receipt()
    assert S.validate_receipt(receipt) == [], S.validate_receipt(receipt)
    # The bounds and coverage the snapshot must carry are actually populated.
    assert receipt["earliest_started_at"] and receipt["latest_started_at"]
    assert receipt["unresolved_datasets"] == ["signal_packages", "signal_pypi"]
    assert receipt["snapshot"] is True


def test_receipt_validator_rejects_malformed_receipts():
    assert S.validate_receipt(_valid_receipt()) == []

    def broken(mutate):
        r = _valid_receipt()
        mutate(r)
        return S.validate_receipt(r)

    cases = {
        # missing capture bounds
        "missing top-level field earliest_started_at": lambda r: r.pop("earliest_started_at"),
        "missing top-level field latest_started_at": lambda r: r.pop("latest_started_at"),
        "capture bounds out of order": lambda r: (r.__setitem__("earliest_started_at", "2030-01-01"),
                                                  r.__setitem__("latest_started_at", "2020-01-01")),
        # bad digest
        "content_digest is not a 64-hex sha256": lambda r: r.__setitem__("content_digest", "abc"),
        # unknown-scope not recorded
        "expected_scope is": lambda r: r.__setitem__("expected_scope", "full"),
        "scope_status is": lambda r: r.__setitem__("scope_status", "complete"),
        # other contract violations
        "snapshot must be true": lambda r: r.__setitem__("snapshot", False),
        "missing top-level field content_digest": lambda r: r.pop("content_digest"),
        "org is": lambda r: r.__setitem__("org", "someone-else"),
        "org_id is": lambda r: r.__setitem__("org_id", "00000000-0000-0000-0000-000000000000"),
        "captured_at": lambda r: r.__setitem__("captured_at", "not-a-timestamp"),
        "run_count": lambda r: r.__setitem__("run_count", 99),
        "resolved_datasets disagrees": lambda r: r["per_dataset_run_counts"].pop("signal_github"),
        "both resolved and unresolved": lambda r: r["unresolved_datasets"].append("signal_github"),
        "window is not a mapping": lambda r: r.__setitem__("window", "unbounded"),
        "window is bounded but records no explicit bound":
            lambda r: r.__setitem__("window", {"bounded": True}),
    }
    for needle, mutate in cases.items():
        problems = broken(mutate)
        assert any(needle in p for p in problems), f"{needle}: not caught, got {problems}"
