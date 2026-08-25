"""The adoption evaluation rollup and its reconciliation report, over the frozen baseline.

`build/adoption_measurements.py` aggregates artifact-level observations to the product level by
the compiled routing, and `build/adoption_reconciliation.py` compares the result against recorded
scores. Both are pure functions of their inputs (the two release identities passed in), so these
tests pin them against the immutable Phase-2 baseline parquet with a fixed test
`declaration_version_id` and the baseline's real `observation_snapshot_id`. The goldens move only
when the routing, the banding, or the observations change — never on an ordinary commit, whose SHA
the content digests deliberately exclude.
"""

import datetime
import hashlib

import pytest

from build.adoption_measurements import (
    canonical_row as measurement_row,
    load_inputs,
    measurements,
)
from build.adoption_reconciliation import canonical_row as reconciliation_row, reconcile
from build.observation_snapshot import observation_snapshot_id, rows_from_parquet
from build.validate import load_sources

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

# A fixed test identity so the content digest is stable; the real one is commit-scoped.
TEST_DVID = "test-declaration-version"

BASELINE_SNAPSHOT_ID = "9bd4d93a6fc67a2b9d89d91adeb4bb3f4fd9b612cc26e6647c67210c9a37a8d4"
MEASUREMENTS_DIGEST = "d207358d5f48237792e7be105aaae048e9e8bf9611a3f41335951d60543ec526"
RECONCILIATION_DIGEST = "3e8ecf56b5a2b45798f33a4846369bb9253ccb9922358b9f2e428132252dbffe"

# The three products whose winning route is stars_fallback AND that declare several GitHub repos,
# so the rule-less aggregation is undefined and the measurement abstains (module doc).
RULELESS_MULTI_ABSTENTIONS = {"bigcodebench", "confer", "lumo"}


@pytest.fixture(scope="module")
def inputs():
    tables, band_rows, category_of = load_inputs()
    return tables, band_rows, category_of


@pytest.fixture(scope="module")
def observations():
    return rows_from_parquet()


@pytest.fixture(scope="module")
def measurement_rows(inputs, observations):
    tables, band_rows, category_of = inputs
    return measurements(
        observations,
        tables,
        band_rows,
        category_of,
        declaration_version_id=TEST_DVID,
        observation_snapshot_id=observation_snapshot_id(observations),
    )


@pytest.fixture(scope="module")
def reconciliation_rows(measurement_rows):
    return reconcile(measurement_rows, load_sources(_ROOT)["scores"], evaluated_at=None)


def _digest(rows, serializer) -> str:
    return hashlib.sha256("\n".join(sorted(serializer(r) for r in rows)).encode("utf-8")).hexdigest()


# --- measurements: shape and the pinned golden -----------------------------------


def test_measurements_reproduce_the_baseline_golden(measurement_rows):
    assert len(measurement_rows) == 392
    assert _digest(measurement_rows, measurement_row) == MEASUREMENTS_DIGEST


def test_one_row_per_product(measurement_rows):
    slugs = [r["product_slug"] for r in measurement_rows]
    assert len(slugs) == len(set(slugs))


def test_both_identities_are_stamped_on_every_row(measurement_rows):
    for row in measurement_rows:
        assert row["declaration_version_id"] == TEST_DVID
        assert row["observation_snapshot_id"] == BASELINE_SNAPSHOT_ID


def test_only_machine_routes_win(measurement_rows):
    # The two hand-authored routes read no machine signal and can never be a measured winner.
    hand_authored = {"active_users", "reported_traction"}
    assert not (hand_authored & {r["route_id"] for r in measurement_rows})


# --- measurements: the aggregation and banding rules -----------------------------


def test_usage_volume_sums_across_contributing_artifacts(inputs, observations):
    """A model with several Hugging Face repositories sums their downloads (sum_usage rule)."""
    tables, band_rows, category_of = inputs
    rows = measurements(
        observations, tables, band_rows, category_of,
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    summed = [
        r for r in rows
        if r["aggregation_method"] == "sum" and len(r["contributing_observation_ids"]) > 1
    ]
    assert summed, "expected at least one multi-artifact usage_volume aggregation in the baseline"
    for row in summed:
        assert row["raw_value"] is not None and row["raw_value"] >= 0


def test_ruleless_route_with_multiple_artifacts_abstains(measurement_rows):
    """stars_fallback declares no aggregation rule; >1 GitHub repo => abstain, not a fabricated sum."""
    abstained = {r["product_slug"] for r in measurement_rows if r["measured_level"] is None}
    assert abstained == RULELESS_MULTI_ABSTENTIONS
    for row in measurement_rows:
        if row["product_slug"] in RULELESS_MULTI_ABSTENTIONS:
            assert row["route_id"] == "github.stargazers_count"
            assert row["aggregation_method"] == ""
            assert row["raw_value"] is None
            assert len(row["contributing_observation_ids"]) > 1


def test_stars_are_capped_by_their_band_set(measurement_rows):
    """The stars cap (level 3) lives in the band set, so no stars measurement exceeds it."""
    for row in measurement_rows:
        if row["route_id"] == "github.stargazers_count" and row["measured_level"] is not None:
            assert row["measured_level"] <= 3


def test_hardware_never_bands_on_a_usage_ladder(measurement_rows):
    """Hardware declares no usage band set; a hardware usage measurement must abstain (§4.4)."""
    for row in measurement_rows:
        if row["product_type"] == "hardware" and row["instrument_type"] == "usage_volume":
            assert row["measured_level"] is None


def test_winning_route_respects_precedence(inputs, observations):
    """No product is measured on a route when a higher-precedence in-scope route also had an
    observation for it — the first matching route in route_order must win."""
    tables, band_rows, category_of = inputs
    order = {r["route_id"]: r["route_order"] for r in tables["adoption_routes"]}
    machine = [r for r in sorted(tables["adoption_routes"], key=lambda x: x["route_order"]) if r["source"]]
    scopes: dict[str, set] = {}
    for s in tables["adoption_route_scopes"]:
        scopes.setdefault(s["route_id"], set()).add(s["scope_value"])
    by_product: dict[str, list] = {}
    for o in observations:
        by_product.setdefault(o["product_slug"], []).append(o)

    rows = measurements(
        observations, tables, band_rows, category_of,
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    won = {r["product_slug"]: r for r in rows}
    for slug, obs in by_product.items():
        row = won.get(slug)
        if row is None:
            continue
        category = row["category_slug"]
        for route in machine:
            if order[route["route_id"]] >= order[row["route_id"]]:
                break
            scope = scopes.get(route["route_id"])
            if scope is not None and category not in scope:
                continue
            matching = [
                o for o in obs
                if o["artifact_kind"] == route["artifact_kind"] and o["metric_type"] == route["metric_type"]
            ]
            assert not matching, (
                f"{slug} won {row['route_id']} but higher-precedence {route['route_id']} had an observation"
            )


def test_measurement_as_of_is_the_oldest_contributing_observation(inputs, observations):
    tables, band_rows, category_of = inputs
    obs_by_id = {o["observation_id"]: o for o in observations}
    rows = measurements(
        observations, tables, band_rows, category_of,
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    for row in rows:
        contributing = [obs_by_id[i] for i in row["contributing_observation_ids"]]
        assert row["measurement_as_of"] == min(o["observed_at"] for o in contributing)


# --- reconciliation: shape and the pinned golden ---------------------------------


def test_reconciliation_reproduces_the_baseline_golden(reconciliation_rows):
    assert len(reconciliation_rows) == 392
    assert _digest(reconciliation_rows, reconciliation_row) == RECONCILIATION_DIGEST


def test_reconciliation_is_one_to_one_with_measurements(measurement_rows, reconciliation_rows):
    m_keys = {(r["product_slug"], r["category_slug"], r["route_id"]) for r in measurement_rows}
    r_keys = {(r["product_slug"], r["category_slug"], r["route_id"]) for r in reconciliation_rows}
    assert m_keys == r_keys


def test_every_status_is_honest_for_the_pre_355_state(reconciliation_rows):
    """A banded measurement is source_unavailable (unbound, #355); an abstaining route is abstained."""
    for row in reconciliation_rows:
        if row["measured_level"] is None:
            assert row["status"] == "abstained"
        else:
            assert row["status"] == "source_unavailable"
        assert row["measurement_freshness"] == "unknown"
        assert row["override_id"] is None
        assert row["explanation"]


def test_delta_is_present_exactly_when_both_levels_are(reconciliation_rows):
    for row in reconciliation_rows:
        both = row["measured_level"] is not None and row["recorded_level"] is not None
        assert (row["delta"] is not None) == both
        if both:
            assert row["delta"] == row["measured_level"] - row["recorded_level"]


def test_evaluated_at_is_excluded_from_the_content_digest(measurement_rows):
    """Two runs at different evaluated_at times digest identically — it is a per-run column."""
    scores = load_sources(_ROOT)["scores"]
    a = reconcile(measurement_rows, scores, evaluated_at=datetime.datetime(2026, 1, 1))
    b = reconcile(measurement_rows, scores, evaluated_at=datetime.datetime(2027, 6, 30))
    assert _digest(a, reconciliation_row) == _digest(b, reconciliation_row)


def test_recorded_scores_are_read_for_the_recorded_side(reconciliation_rows):
    """At least some rows carry a recorded level and instrument pulled from sources/scores."""
    assert any(r["recorded_level"] is not None for r in reconciliation_rows)
    assert any(r["recorded_instrument_type"] for r in reconciliation_rows)
