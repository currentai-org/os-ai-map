"""The materialization bracket: what it proves, what it refuses to claim, and its receipt.

The bracket's whole value is honesty at the edges, so the tests concentrate there: a stable
bracket binds, a moved bracket claims nothing, a lookup failure degrades the binding and never
the read, and the receipt names the exact rows (by snapshot id) its verdict is about.
"""

from __future__ import annotations

import json

import pytest

from build import read_binding as B
from build import serialize_evaluation as SE


def _control_plane(materialization_lists):
    """A fake GraphQL endpoint serving successive materialization listings for one model.

    `materialization_lists` is consumed one listing per call — the two bracket ends of
    `bound_read` see the first and second entries.
    """
    listings = list(materialization_lists)

    def graphql(query, variables, token):
        assert variables == {"w": {"name": {"eq": "product_adoption_current"}}}
        current = listings.pop(0) if len(listings) > 1 else listings[0]
        return {
            "dataModels": {
                "edges": [
                    {
                        "node": {
                            "id": "model-1",
                            "name": "product_adoption_current",
                            "dataset": {"name": "observations"},
                            "materializations": {
                                "edges": [{"node": m} for m in current]
                            },
                        }
                    }
                ]
            }
        }

    return graphql


M_OLD = {"id": "mat-old", "runId": "run-old", "createdAt": "2026-08-24T15:02:16.919Z"}
M_NEW = {"id": "mat-new", "runId": "run-new", "createdAt": "2026-08-25T05:49:57.943Z"}
ROWS = [{"product_slug": "olmo-3", "raw_value": 7}]


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv("OSO_API_KEY", "test-token")


def test_latest_materialization_is_newest_by_created_at_not_listing_order():
    graphql = _control_plane([[M_OLD, M_NEW]])
    newest = B.latest_materialization(graphql=graphql)
    assert newest.materialization_id == "mat-new"
    assert newest.run_id == "run-new"


def test_stable_bracket_binds_the_read_to_one_run():
    graphql = _control_plane([[M_OLD, M_NEW], [M_OLD, M_NEW]])
    result = B.bound_read(lambda: ROWS, graphql=graphql)
    assert result.rows == ROWS
    assert result.binding["binding_status"] == "bound"
    assert result.binding["materialization_id"] == "mat-new"
    assert result.binding["run_id"] == "run-new"
    assert result.binding["model"] == "observations.product_adoption_current"


def test_moved_bracket_is_unstable_and_claims_no_run():
    m_next = {"id": "mat-next", "runId": "run-next", "createdAt": "2026-08-25T06:10:00.000Z"}
    graphql = _control_plane([[M_NEW], [M_NEW, m_next]])
    result = B.bound_read(lambda: ROWS, graphql=graphql)
    assert result.binding["binding_status"] == "unstable"
    assert "run_id" not in result.binding
    assert result.binding["materialization_id_before"] == "mat-new"
    assert result.binding["materialization_id_after"] == "mat-next"
    assert result.rows == ROWS  # an unstable bracket still returns the rows


def test_missing_model_and_empty_materializations_fail_the_lookup_loudly():
    def wrong_dataset(query, variables, token):
        return {"dataModels": {"edges": [{"node": {
            "id": "model-9", "name": "product_adoption_current",
            "dataset": {"name": "scores"},
            "materializations": {"edges": []},
        }}]}}

    with pytest.raises(B.BindingLookupError, match="no deployed model"):
        B.latest_materialization(graphql=wrong_dataset)
    with pytest.raises(B.BindingLookupError, match="no materialization"):
        B.latest_materialization(graphql=_control_plane([[]]))


def test_duplicate_models_refuse_to_guess():
    def two_models(query, variables, token):
        node = {
            "id": "model-1", "name": "product_adoption_current",
            "dataset": {"name": "observations"},
            "materializations": {"edges": [{"node": M_NEW}]},
        }
        return {"dataModels": {"edges": [{"node": node}, {"node": dict(node, id="model-2")}]}}

    with pytest.raises(B.BindingLookupError, match="refusing to guess"):
        B.latest_materialization(graphql=two_models)


def test_lookup_failure_degrades_the_binding_never_the_read(monkeypatch):
    def broken(*args, **kwargs):
        raise B.BindingLookupError("control plane down")

    monkeypatch.setattr("build.read_binding.bound_read", broken)
    monkeypatch.setattr(SE.M, "load_current_observations", lambda: list(ROWS))
    rows, binding = SE.read_live_bound()
    assert rows == ROWS
    assert binding["binding_status"] == "unavailable"
    assert "control plane down" in binding["reason"]


def test_receipt_names_the_rows_it_judges(tmp_path):
    from build.observation_snapshot import observation_snapshot_id, rows_from_parquet

    rows = rows_from_parquet()
    binding = {
        "binding_status": "bound",
        "model": "observations.product_adoption_current",
        "model_id": "model-1",
        "materialization_id": "mat-new",
        "run_id": "run-new",
        "materialized_at": M_NEW["createdAt"],
    }
    path = tmp_path / "read_binding.json"
    SE.write_binding_receipt(binding, rows, path)
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["observation_snapshot_id"] == observation_snapshot_id(rows)
    assert receipt["row_count"] == len(rows)
    assert receipt["run_id"] == "run-new"


def test_binding_does_not_move_the_snapshot_id():
    """The bracket is provenance about a read; the identity of the rows must not see it."""
    from build.observation_snapshot import observation_snapshot_id, rows_from_parquet

    rows = rows_from_parquet()
    before = observation_snapshot_id(rows)
    graphql = _control_plane([[M_NEW], [M_NEW]])
    result = B.bound_read(lambda: rows, graphql=graphql)
    assert observation_snapshot_id(result.rows) == before
