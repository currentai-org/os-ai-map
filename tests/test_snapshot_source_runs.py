"""Synthetic gates over build/snapshot_source_runs.py -- no live API is touched.

Mirrors tests/test_assets_inventory.py's platform-audit tests: parsing, coverage derivation,
pagination, row validation, digest and receipt-validator contracts are pinned against hand-built
data, so the module can be trusted without credentials. The run->model binding is asserted to come
from materializations, never from timestamps, because that is the one inference the module must
refuse to make. A final credential-free test loads the COMMITTED receipt and validates it.

Run standalone (no pytest dependency required):
    uv run python -m tests.test_snapshot_source_runs
"""

from __future__ import annotations

import json

import build.snapshot_source_runs as S

CAPTURED = "2026-08-23T12:00:00+00:00"

# Real-shaped UUIDs for synthetic name->id bindings.
_UUID = {
    "signal_github": "cc74e8db-7718-4615-a004-7f27cabaf967",
    "signal_huggingface": "6108e4d6-868f-4cba-8df5-ee64f8fb301e",
}


# --- synthetic run nodes ----------------------------------------------------------

def _mat(mat_id: str, table_id: str, dataset_id: str, created_at: str) -> dict:
    return {"node": {"id": mat_id, "tableId": table_id, "datasetId": dataset_id,
                     "createdAt": created_at}}


def _pi(has_next: bool = False, cursor=None) -> dict:
    return {"hasNextPage": has_next, "endCursor": cursor}


def _step(name: str, mats: list[dict], display_name: str | None = None) -> dict:
    return {"node": {"name": name, "displayName": display_name or name, "status": "SUCCESS",
                     "materializations": {"pageInfo": _pi(), "edges": mats}}}


def _run(run_id: str, *, status="SUCCESS", trigger="SCHEDULED", run_type="MODEL",
         requested_by=None, started="2026-08-23T01:00:00Z", steps=None) -> dict:
    return {
        "id": run_id, "triggerType": trigger, "runType": run_type, "status": status,
        "queuedAt": "2026-08-23T00:59:00Z", "startedAt": started,
        "finishedAt": "2026-08-23T01:05:00Z", "lastHeartbeatAt": None,
        "requestedBy": ({"id": requested_by} if requested_by else None),
        "steps": {"pageInfo": _pi(), "edges": steps or []},
    }


def _one_materialized_run() -> dict:
    return _run("run-1", steps=[
        _step("evaluate_model_repo_state",
              [_mat("mat-1", "tbl-repo-state", "ds-github", "2026-08-23T01:04:00Z")]),
    ])


# --- coverage derived from the routing YAML (Finding 1) ---------------------------

_SYNTHETIC_ROUTING = {
    "sources": {
        "github": {"table": "currentai.signal_github.repo_state", "bridged": True},
        "huggingface_model": {"table": "currentai.signal_huggingface.hub_state", "bridged": True},
        "huggingface_dataset": {"table": "currentai.signal_huggingface.hub_state", "bridged": True},
        "pypi": {"table": "currentai.signal_pypi.package_downloads", "bridged": True},
        "semanticscholar": {"table": "currentai.signal_semanticscholar.paper_citations", "bridged": True},
        "npm": {"table": None, "bridged": False},
    },
    "dimensions": {"adoption": {"routes": [
        {"source": "pypi", "column": "downloads_30d"},
        {"source": "huggingface_model", "column": "downloads_30d"},
        {"source": "huggingface_dataset", "column": "downloads_30d"},
        {"source": "semanticscholar", "column": "citation_count"},
        {"source": None, "signal_type": "active_users"},          # hand-authored -> no dataset
        {"source": "github", "column": "stargazers_count"},
        {"source": "npm", "column": "downloads_30d"},              # unbridged -> excluded
    ]}},
}


def test_deployed_datasets_are_derived_from_routing_and_include_semanticscholar():
    deployed = S.deployed_adoption_source_datasets(_SYNTHETIC_ROUTING)
    # The two Hugging Face routes collapse to one dataset; the hand-authored and unbridged routes
    # contribute nothing; semanticscholar -- the route the old hard-coded list dropped -- is in.
    assert deployed == ("signal_github", "signal_huggingface", "signal_pypi", "signal_semanticscholar")
    assert "signal_semanticscholar" in deployed


def test_source_datasets_add_the_staged_successor_separately():
    requested = S.source_datasets(_SYNTHETIC_ROUTING)
    assert "signal_packages" in requested                      # staged successor, added separately
    assert set(requested) == {"signal_github", "signal_huggingface", "signal_pypi",
                              "signal_semanticscholar", "signal_packages"}


def test_real_routing_yaml_derives_the_deployed_adoption_datasets():
    """Against the committed signal_routing.yaml, not a synthetic one."""
    deployed = S.deployed_adoption_source_datasets(S.load_routing(S.A.ROOT))
    assert "signal_semanticscholar" in deployed
    assert "signal_github" in deployed and "signal_pypi" in deployed
    assert "signal_huggingface" in deployed


# --- parsing the row contract -----------------------------------------------------

def test_parse_binds_model_from_materialization_and_keeps_four_ids_distinct():
    rows = S.parse_run_rows("ds-github", "signal_github", _one_materialized_run(), CAPTURED)
    assert len(rows) == 1
    row = rows[0]
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
    assert u["error_class"] is None


# --- complete pagination (Finding 2) ----------------------------------------------

def test_pagination_reads_every_page_not_just_the_first(monkeypatch):
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
    assert calls["n"] == 2


def test_pagination_rejects_a_repeated_cursor(monkeypatch):
    """hasNextPage stays true but the cursor never advances -- a stall that must raise, not loop."""
    stuck = {"runs": {
        "pageInfo": {"hasNextPage": True, "endCursor": "SAME"},
        "edges": [{"node": _run("run-1")}],
    }}
    monkeypatch.setattr(S, "graphql", lambda q, v, t: stuck)
    try:
        S.fetch_runs("ds-github", token="t")
        assert False, "expected TruncatedConnection on a repeated cursor"
    except S.TruncatedConnection:
        pass


def test_pagination_rejects_a_missing_cursor(monkeypatch):
    """hasNextPage true but endCursor empty -- truncation, must raise rather than stop silently."""
    bad = {"runs": {
        "pageInfo": {"hasNextPage": True, "endCursor": None},
        "edges": [{"node": _run("run-1")}],
    }}
    monkeypatch.setattr(S, "graphql", lambda q, v, t: bad)
    try:
        S.fetch_runs("ds-github", token="t")
        assert False, "expected TruncatedConnection on a missing cursor"
    except S.TruncatedConnection:
        pass


def test_truncated_nested_steps_or_materializations_raise():
    node = _run("run-trunc", steps=[
        _step("evaluate_model_repo_state",
              [_mat("m1", "t1", "ds-github", "2026-08-23T01:04:00Z")]),
    ])
    # A truncated materializations page must raise.
    node["steps"]["edges"][0]["node"]["materializations"]["pageInfo"] = _pi(True, "c")
    try:
        S._assert_nested_complete(node)
        assert False, "expected TruncatedConnection on truncated materializations"
    except S.TruncatedConnection:
        pass
    # A truncated steps page must raise.
    node2 = _run("run-trunc2", steps=[])
    node2["steps"]["pageInfo"] = _pi(True, "c")
    try:
        S._assert_nested_complete(node2)
        assert False, "expected TruncatedConnection on truncated steps"
    except S.TruncatedConnection:
        pass


def test_pagination_fails_closed_on_missing_or_malformed_pageinfo(monkeypatch):
    """A response with no pageInfo, or a non-boolean hasNextPage, cannot be certified as exhausted
    and must raise -- never be read as 'no more pages'."""
    # Top-level runs: no pageInfo at all (the reviewer's reproduction).
    monkeypatch.setattr(S, "graphql", lambda q, v, t: {"runs": {"edges": []}})
    try:
        S.fetch_runs("ds", token="t")
        assert False, "expected TruncatedConnection on runs with no pageInfo"
    except S.TruncatedConnection:
        pass
    # Top-level datasets: no pageInfo.
    monkeypatch.setattr(S, "graphql", lambda q, v, t: {
        "datasets": {"edges": [{"node": {"id": "x", "name": "signal_github"}}]}})
    try:
        S.resolve_datasets(("signal_github",), token="t")
        assert False, "expected TruncatedConnection on datasets with no pageInfo"
    except S.TruncatedConnection:
        pass
    # Top-level runs: hasNextPage present but not a boolean.
    monkeypatch.setattr(S, "graphql", lambda q, v, t: {
        "runs": {"pageInfo": {"hasNextPage": "yes"}, "edges": []}})
    try:
        S.fetch_runs("ds", token="t")
        assert False, "expected TruncatedConnection on non-boolean hasNextPage"
    except S.TruncatedConnection:
        pass


def test_nested_missing_pageinfo_fails_closed():
    """Nested steps/materializations with no pageInfo must raise, not be read as complete -- the
    reviewer's second reproduction."""
    # steps has no pageInfo.
    node = {"id": "r", "steps": {"edges": [
        {"node": {"name": "s", "materializations": {"pageInfo": _pi(), "edges": []}}}]}}
    try:
        S._assert_nested_complete(node)
        assert False, "expected TruncatedConnection on steps with no pageInfo"
    except S.TruncatedConnection:
        pass
    # materializations has no pageInfo.
    node = {"id": "r", "steps": {"pageInfo": _pi(), "edges": [
        {"node": {"name": "s", "materializations": {"edges": []}}}]}}
    try:
        S._assert_nested_complete(node)
        assert False, "expected TruncatedConnection on materializations with no pageInfo"
    except S.TruncatedConnection:
        pass


def test_two_runs_from_one_fire_are_both_kept(monkeypatch):
    same_minute = "2026-08-23T01:00:00Z"
    page = {"runs": {
        "pageInfo": {"hasNextPage": False, "endCursor": None},
        "edges": [{"node": _run("run-a", started=same_minute)},
                  {"node": _run("run-b", started=same_minute)}],
    }}
    monkeypatch.setattr(S, "graphql", lambda q, v, t: page)
    nodes = S.fetch_runs("ds-github", token="t")
    assert {n["id"] for n in nodes} == {"run-a", "run-b"}


# --- row validation (Finding 3) ---------------------------------------------------

def _valid_rows() -> list[dict]:
    return (
        S.parse_run_rows("ds-github", "signal_github", _one_materialized_run(), CAPTURED)
        + S.parse_run_rows("ds-hf", "signal_huggingface", _run("run-2"), CAPTURED)
    )


def test_validate_rows_accepts_a_wellformed_row_set():
    assert S.validate_rows(_valid_rows()) == []


def test_validate_rows_rejects_defects():
    def broken(mutate):
        rows = _valid_rows()
        mutate(rows)
        return S.validate_rows(rows)

    # partial materialization: an id with no table
    p = broken(lambda rows: rows[0].__setitem__("table_id", None))
    assert any("partial materialization" in x for x in p), p

    # duplicate grain: two rows with the same (run, materialization)
    p = broken(lambda rows: rows.append(dict(rows[0])))
    assert any("duplicate grain" in x or "exact-duplicate" in x for x in p), p

    # bad trigger enum
    p = broken(lambda rows: rows[0].__setitem__("trigger_type", "SNEAKY"))
    assert any("trigger_type" in x for x in p), p

    # bad actor enum
    p = broken(lambda rows: rows[0].__setitem__("actor_type", "robot"))
    assert any("actor_type" in x for x in p), p

    # invalid timestamp
    p = broken(lambda rows: rows[0].__setitem__("started_at", "2026-99-99T99:99:99garbage"))
    assert any("started_at" in x and "ISO-8601" in x for x in p), p

    # scope must be unknown
    p = broken(lambda rows: rows[0].__setitem__("scope_status", "complete"))
    assert any("scope must be unknown" in x for x in p), p

    # missing required identifier
    p = broken(lambda rows: rows[0].__setitem__("source_run_id", None))
    assert any("source_run_id" in x for x in p), p


# --- deterministic digest ---------------------------------------------------------

def test_digest_is_order_independent_and_ignores_captured_at():
    rows_a = (
        S.parse_run_rows("ds", "signal_github", _run("r1"), "2026-08-23T12:00:00+00:00")
        + S.parse_run_rows("ds", "signal_github", _one_materialized_run(), "2026-08-23T12:00:00+00:00")
    )
    rows_b = list(reversed(
        S.parse_run_rows("ds", "signal_github", _run("r1"), "2030-01-01T00:00:00+00:00")
        + S.parse_run_rows("ds", "signal_github", _one_materialized_run(), "2030-01-01T00:00:00+00:00")
    ))
    assert S.content_digest(rows_a) == S.content_digest(rows_b)


def test_digest_changes_when_a_non_captured_field_changes():
    base = S.parse_run_rows("ds", "signal_github", _run("r1", status="SUCCESS"), CAPTURED)
    changed = S.parse_run_rows("ds", "signal_github", _run("r1", status="FAILED"), CAPTURED)
    assert S.content_digest(base) != S.content_digest(changed)


# --- receipt validator (Finding 4) ------------------------------------------------

def _valid_receipt() -> dict:
    rows = _valid_rows()
    return S.build_receipt(
        rows,
        requested_datasets=("signal_github", "signal_huggingface", "signal_pypi",
                            "signal_semanticscholar", "signal_packages"),
        deployed_datasets=("signal_github", "signal_huggingface", "signal_pypi",
                           "signal_semanticscholar"),
        staged_datasets=("signal_packages",),
        resolved_dataset_ids={"signal_github": _UUID["signal_github"],
                              "signal_huggingface": _UUID["signal_huggingface"]},
        per_dataset_run_counts={"signal_github": 1, "signal_huggingface": 1},
        unresolved_datasets=["signal_packages", "signal_pypi", "signal_semanticscholar"],
        captured_at=CAPTURED,
    )


def test_receipt_validator_accepts_a_wellformed_receipt():
    receipt = _valid_receipt()
    assert S.validate_receipt(receipt) == [], S.validate_receipt(receipt)
    assert receipt["earliest_started_at"] and receipt["latest_started_at"]
    assert receipt["snapshot"] is True
    assert receipt["schema_version"] == S.SCHEMA_VERSION
    assert receipt["resolved_dataset_ids"]["signal_github"] == _UUID["signal_github"]


def test_receipt_validator_rejects_malformed_receipts():
    assert S.validate_receipt(_valid_receipt()) == []

    def broken(mutate):
        r = _valid_receipt()
        mutate(r)
        return S.validate_receipt(r)

    cases = {
        # the four holes the prior validator let through
        "captured_at": lambda r: r.__setitem__("captured_at", "2026-99-99T99:99:99garbage"),
        "row_count is not a nonnegative int": lambda r: r.__setitem__("row_count", -1),
        "requested_datasets has duplicates":
            lambda r: r["requested_datasets"].append("signal_github"),
        # row_count can never fall below run_count (every run emits >= 1 row)
        "< run_count": lambda r: r.__setitem__("row_count", 0),
        # every dataset list, not just requested, must be dedup'd and canonically sorted
        "deployed_datasets has duplicates":
            lambda r: r["deployed_datasets"].append("signal_github"),
        "is not canonically sorted": lambda r: r["requested_datasets"].reverse(),
        "resolved + unresolved do not partition":
            lambda r: (r["requested_datasets"].append("signal_x"),
                       r["deployed_datasets"].append("signal_x")),
        "resolved_dataset_ids keys do not match":
            lambda r: r["resolved_dataset_ids"].pop("signal_github"),
        "is not a UUID":
            lambda r: r["resolved_dataset_ids"].__setitem__("signal_github", "not-a-uuid"),
        # capture bounds
        "missing top-level field earliest_started_at": lambda r: r.pop("earliest_started_at"),
        "capture bounds out of order": lambda r: (r.__setitem__("earliest_started_at", "2030-01-01T00:00:00Z"),
                                                  r.__setitem__("latest_started_at", "2020-01-01T00:00:00Z")),
        # digest / scope / identity
        "content_digest is not a 64-hex sha256": lambda r: r.__setitem__("content_digest", "abc"),
        "expected_scope is": lambda r: r.__setitem__("expected_scope", "full"),
        "scope_status is": lambda r: r.__setitem__("scope_status", "complete"),
        "snapshot must be true": lambda r: r.__setitem__("snapshot", False),
        "missing top-level field content_digest": lambda r: r.pop("content_digest"),
        "org is": lambda r: r.__setitem__("org", "someone-else"),
        "org_id is": lambda r: r.__setitem__("org_id", "00000000-0000-0000-0000-000000000000"),
        "schema_version is": lambda r: r.__setitem__("schema_version", 999),
        "canonicalization_version is": lambda r: r.__setitem__("canonicalization_version", 999),
        # coverage partitions and counts
        "run_count": lambda r: r.__setitem__("run_count", 99),
        "resolved_datasets disagrees": lambda r: r["per_dataset_run_counts"].pop("signal_github"),
        "both resolved and unresolved": lambda r: r["unresolved_datasets"].append("signal_github"),
        "both deployed and staged": lambda r: r["staged_datasets"].append("signal_github"),
        "window is not a mapping": lambda r: r.__setitem__("window", "unbounded"),
        "window is bounded but records no explicit bound":
            lambda r: r.__setitem__("window", {"bounded": True}),
    }
    for needle, mutate in cases.items():
        problems = broken(mutate)
        assert any(needle in p for p in problems), f"{needle}: not caught, got {problems}"


# --- credential-free: the committed receipt validates ------------------------------

def test_committed_receipt_is_present_and_valid():
    """The committed attestation must load and pass the validator with no credentials -- the same
    gate `--check` runs offline. If the receipt is stale-shaped, this fails."""
    assert S.RECEIPT.exists(), f"committed receipt missing at {S.RECEIPT}"
    receipt = json.loads(S.RECEIPT.read_text())
    assert S.validate_receipt(receipt) == [], S.validate_receipt(receipt)
    assert receipt["snapshot"] is True
    assert receipt["schema_version"] == S.SCHEMA_VERSION
    assert receipt["canonicalization_version"] == S.CANONICALIZATION_VERSION


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in fns:
        try:
            if "monkeypatch" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                continue  # needs pytest's monkeypatch fixture
            fn()
            passed += 1
        except Exception:
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"{passed} passed, {failed} failed (monkeypatch tests skipped in standalone mode)")
    raise SystemExit(1 if failed else 0)
