"""The adoption evaluation rollup and its reconciliation report, over the frozen baseline.

`build/adoption_measurements.py` aggregates artifact-level observations to the product level by the
compiled routing; `build/adoption_reconciliation.py` compares the result against every recorded
assessment. Both are pure functions of their inputs (the two release identities passed in), so
these tests pin them against the immutable Phase-2 baseline parquet with a fixed test
`declaration_version_id` and the baseline's real `observation_snapshot_id`. The goldens move only
when the routing, the banding, the declarations, or the observations change — never on an ordinary
commit, whose SHA the content digests deliberately exclude.
"""

import datetime
import hashlib
from pathlib import Path

import pytest

from build.adoption_measurements import (
    _band_for,
    _band_index,
    _native,
    _numeric,
    canonical_row as measurement_row,
    load_inputs,
    measurements,
    select_route,
    machine_routes,
    route_scopes,
)
from build.adoption_reconciliation import canonical_row as reconciliation_row, reconcile
from build.observation_snapshot import observation_snapshot_id, rows_from_parquet
from build.validate import load_sources

_ROOT = Path(__file__).resolve().parents[1]

# A fixed test identity so the content digest is stable; the real one is commit-scoped.
TEST_DVID = "test-declaration-version"

BASELINE_SNAPSHOT_ID = "9bd4d93a6fc67a2b9d89d91adeb4bb3f4fd9b612cc26e6647c67210c9a37a8d4"
MEASUREMENTS_DIGEST = "0d71d073786150256b1cb64d62a9703c42cbe1040d2c23c3089769a91ccaf014"
RECONCILIATION_DIGEST = "f296f5d63512ec3adf4f785914e551c3f82c52268706e749f7d8190bf38ad34c"

MEASUREMENT_COUNT = 390
RECORDED_ASSESSMENT_COUNT = 522


@pytest.fixture(scope="module")
def inputs():
    return load_inputs()  # (routing_tables, band_rows, category_of, declared_artifacts)


@pytest.fixture(scope="module")
def observations():
    return rows_from_parquet()


@pytest.fixture(scope="module")
def scores():
    return load_sources(_ROOT)["scores"]


@pytest.fixture(scope="module")
def measurement_rows(inputs, observations):
    tables, band_rows, category_of, declared = inputs
    return measurements(
        observations, tables, band_rows, category_of, declared,
        declaration_version_id=TEST_DVID,
        observation_snapshot_id=observation_snapshot_id(observations),
    )


@pytest.fixture(scope="module")
def reconciliation_rows(inputs, measurement_rows, scores, observations):
    tables, _, category_of, declared = inputs
    return reconcile(
        scores, measurement_rows, tables, category_of, declared,
        declaration_version_id=TEST_DVID,
        observation_snapshot_id=observation_snapshot_id(observations),
        evaluated_at=None,
    )


def _digest(rows, serializer) -> str:
    return hashlib.sha256("\n".join(sorted(serializer(r) for r in rows)).encode("utf-8")).hexdigest()


def _measure(inputs, observation_rows, **overrides):
    tables, band_rows, category_of, declared = inputs
    ids = {"declaration_version_id": TEST_DVID, "observation_snapshot_id": "x" * 64}
    ids.update(overrides)
    return measurements(observation_rows, tables, band_rows, category_of, declared, **ids)


# --- measurements: shape and the pinned golden -----------------------------------


def test_measurements_reproduce_the_baseline_golden(measurement_rows):
    assert len(measurement_rows) == MEASUREMENT_COUNT
    assert _digest(measurement_rows, measurement_row) == MEASUREMENTS_DIGEST


def test_one_row_per_product(measurement_rows):
    slugs = [r["product_slug"] for r in measurement_rows]
    assert len(slugs) == len(set(slugs))


def test_both_identities_are_stamped_on_every_row(measurement_rows):
    for row in measurement_rows:
        assert row["declaration_version_id"] == TEST_DVID
        assert row["observation_snapshot_id"] == BASELINE_SNAPSHOT_ID


def test_only_machine_routes_win(measurement_rows):
    assert not ({"active_users", "reported_traction"} & {r["route_id"] for r in measurement_rows})


# --- measurements: route selection is by declaration, and never falls through ----


def test_route_selection_is_by_declared_artifacts_not_observations(inputs, observations):
    """accelerate declares PyPI and GitHub. Remove only its PyPI observation: it must NOT fall
    through to GitHub stars — it produces no measurement row at all."""
    accelerate_obs = [o for o in observations if o["product_slug"] == "accelerate"]
    assert {"pypi", "github"} <= {o["artifact_kind"] for o in accelerate_obs}

    # With PyPI present, accelerate is measured on the PyPI route.
    with_pypi = [r for r in _measure(inputs, observations) if r["product_slug"] == "accelerate"]
    assert [r["route_id"] for r in with_pypi] == ["pypi.downloads_30d"]

    # Remove only the PyPI observation; GitHub stays.
    no_pypi_obs = [
        o for o in observations
        if not (o["product_slug"] == "accelerate" and o["artifact_kind"] == "pypi")
    ]
    without_pypi = [r for r in _measure(inputs, no_pypi_obs) if r["product_slug"] == "accelerate"]
    assert without_pypi == [], "PyPI-declared product fell through to a weaker route"


def test_winning_route_is_the_top_applicable_declared_route(inputs, measurement_rows):
    """Every measured product's route is exactly select_route over its declarations — the top
    applicable route by precedence, not merely the first route that had an observation."""
    tables, _, category_of, declared = inputs
    routes, scopes = machine_routes(tables), route_scopes(tables)
    for row in measurement_rows:
        winner = select_route(declared[row["product_slug"]], row["category_slug"], routes, scopes)
        assert winner is not None and winner["route_id"] == row["route_id"]


# --- measurements: aggregation, numbers, banding ---------------------------------


def test_usage_volume_sums_across_contributing_artifacts(measurement_rows):
    summed = [
        r for r in measurement_rows
        if r["instrument_type"] == "usage_volume" and len(r["contributing_observation_ids"]) > 1
    ]
    assert summed
    for row in summed:
        assert row["aggregation_method"] == "sum" and row["raw_value"] >= 0


def test_stars_sum_rule_aggregates_multiple_repositories(measurement_rows):
    """sum_stars_across_artifacts: a product with several GitHub repos sums and bands, rather than
    abstaining. bigcodebench declares two repositories."""
    multi_star = [
        r for r in measurement_rows
        if r["route_id"] == "github.stargazers_count" and len(r["contributing_observation_ids"]) > 1
    ]
    assert multi_star, "expected at least one multi-repo stars aggregation in the baseline"
    for row in multi_star:
        assert row["aggregation_method"] == "sum"
        assert row["measured_level"] is not None  # summed and banded, not abstained


def test_no_measurement_abstains_in_the_baseline(measurement_rows):
    """With the stars sum rule declared, every baseline measurement bands; none is null."""
    assert all(r["measured_level"] is not None for r in measurement_rows)


def test_stars_are_capped_by_their_band_set(measurement_rows):
    for row in measurement_rows:
        if row["route_id"] == "github.stargazers_count" and row["measured_level"] is not None:
            assert row["measured_level"] <= 3


def test_hardware_never_bands_on_a_usage_ladder(measurement_rows):
    for row in measurement_rows:
        if row["product_type"] == "hardware" and row["instrument_type"] == "usage_volume":
            assert row["measured_level"] is None


def test_measurement_as_of_is_the_oldest_contributing_observation(inputs, observations):
    obs_by_id = {o["observation_id"]: o for o in observations}
    for row in _measure(inputs, observations):
        contributing = [obs_by_id[i] for i in row["contributing_observation_ids"]]
        assert row["measurement_as_of"] == min(o["observed_at"] for o in contributing)


# --- numbers are preserved, never truncated -------------------------------------


def test_numeric_preserves_floats_and_rejects_bad_types():
    assert _numeric(1000, "raw_value") == 1000
    assert _numeric(1000.9, "raw_value") == 1000.9  # not floored
    for bad in (True, "100", None, {1}):
        with pytest.raises(TypeError):
            _numeric(bad, "raw_value")
    for bad in (float("inf"), float("nan")):
        with pytest.raises(ValueError):
            _numeric(bad, "raw_value")


def test_native_coerces_pyoso_scalars_to_python_types():
    """The live loader must hand the strict digest native ints/floats/datetimes, not numpy/Timestamp."""

    class _Timestamp:
        def to_pydatetime(self):
            return datetime.datetime(2026, 1, 2, 3, 4, 5)

    class _NpScalar:
        def __init__(self, value):
            self._value = value

        def item(self):
            return self._value

    assert _native(5) == 5 and type(_native(5)) is int
    assert _native("github") == "github"
    assert _native(None) is None
    assert _native(_Timestamp()) == datetime.datetime(2026, 1, 2, 3, 4, 5)
    coerced = _native(_NpScalar(7))
    assert coerced == 7 and type(coerced) is int


def test_a_float_just_over_a_threshold_bands_above_not_floored():
    """int() truncation would misband 1000.9 as 1000 (below a 1000 threshold). The real value
    must band above it."""
    index = _band_index([
        {"band_set_id": "b", "level": 1, "above": -1, "reach": "lo"},
        {"band_set_id": "b", "level": 2, "above": 1000, "reach": "hi"},
    ])
    assert _band_for(index, "b", 1000.9) == (2, "hi")   # a floor to 1000 would give level 1
    assert _band_for(index, "b", 1000) == (1, "lo")     # exactly the exclusive bound stays below


def test_a_float_raw_value_survives_into_the_measurement(inputs, observations):
    """A doctored float download count reaches the row unfloored."""
    target = next(o for o in observations if o["artifact_kind"] == "pypi")
    doctored = [
        {**o, "raw_value": 1234.5} if o is target else o
        for o in observations
    ]
    rows = {r["product_slug"]: r for r in _measure(inputs, doctored)}
    row = rows[target["product_slug"]]
    # Only that product's single pypi artifact contributes here; the float is preserved.
    if len(row["contributing_observation_ids"]) == 1:
        assert row["raw_value"] == 1234.5


# --- reconciliation: complete coverage of the recorded assessments ---------------


def test_reconciliation_reproduces_the_baseline_golden(reconciliation_rows):
    assert len(reconciliation_rows) == RECORDED_ASSESSMENT_COUNT
    assert _digest(reconciliation_rows, reconciliation_row) == RECONCILIATION_DIGEST


def test_every_recorded_assessment_gets_exactly_one_row(reconciliation_rows, scores):
    recorded = {s for s, doc in scores.items() if isinstance(doc.get("adoption"), dict)}
    rows_by_product = [r["product_slug"] for r in reconciliation_rows]
    assert set(rows_by_product) == recorded
    assert len(rows_by_product) == len(recorded) == RECORDED_ASSESSMENT_COUNT


def test_deliberate_null_assessments_are_covered_as_abstained(reconciliation_rows, scores):
    null_recorded = {
        s for s, doc in scores.items()
        if isinstance(doc.get("adoption"), dict) and doc["adoption"].get("level") is None
    }
    assert null_recorded  # there are deliberate nulls to cover
    by_product = {r["product_slug"]: r for r in reconciliation_rows}
    for slug in null_recorded:
        assert by_product[slug]["status"] == "abstained"


def test_every_status_is_honest_for_the_pre_355_state(reconciliation_rows):
    allowed = {"abstained", "source_unavailable", "unmeasured"}
    for row in reconciliation_rows:
        assert row["status"] in allowed
        if row["recorded_level"] is None:
            assert row["status"] == "abstained"
        elif row["measured_level"] is not None:
            assert row["status"] == "source_unavailable"  # measured but unbound (#355)
        assert row["measurement_freshness"] == "unknown"
        assert row["override_id"] is None
        assert row["explanation"]


def test_measured_products_all_appear_recorded(measurement_rows, reconciliation_rows):
    """measured ⊆ recorded, so every measurement has a reconciliation row on the same route."""
    m_keys = {(r["product_slug"], r["route_id"]) for r in measurement_rows}
    r_keys = {(r["product_slug"], r["route_id"]) for r in reconciliation_rows}
    assert m_keys <= r_keys


def test_delta_is_present_exactly_when_both_levels_are(reconciliation_rows):
    for row in reconciliation_rows:
        both = row["measured_level"] is not None and row["recorded_level"] is not None
        assert (row["delta"] is not None) == both
        if both:
            assert row["delta"] == row["measured_level"] - row["recorded_level"]


def test_evaluated_at_is_excluded_from_the_content_digest(inputs, measurement_rows, scores, observations):
    tables, _, category_of, declared = inputs
    osid = observation_snapshot_id(observations)
    kw = dict(declaration_version_id=TEST_DVID, observation_snapshot_id=osid)
    a = reconcile(scores, measurement_rows, tables, category_of, declared,
                  evaluated_at=datetime.datetime(2026, 1, 1), **kw)
    b = reconcile(scores, measurement_rows, tables, category_of, declared,
                  evaluated_at=datetime.datetime(2027, 6, 30), **kw)
    assert _digest(a, reconciliation_row) == _digest(b, reconciliation_row)
