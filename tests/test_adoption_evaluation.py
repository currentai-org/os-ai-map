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
    _coerce_timestamp,
    _native,
    _numeric,
    all_routes,
    canonical_row as measurement_row,
    load_inputs,
    measurements,
    route_scopes,
    select_route,
)
from build.adoption_reconciliation import canonical_row as reconciliation_row, reconcile
from build.observation_snapshot import (
    observation_content_digest,
    observation_snapshot_id,
    rows_from_parquet,
)
from build.validate import load_sources

_ROOT = Path(__file__).resolve().parents[1]

# A fixed test identity so the content digest is stable; the real one is commit-scoped.
TEST_DVID = "test-declaration-version"

BASELINE_SNAPSHOT_ID = "9bd4d93a6fc67a2b9d89d91adeb4bb3f4fd9b612cc26e6647c67210c9a37a8d4"
MEASUREMENTS_DIGEST = "f1ccad234b9e91906b2feb4e9f4d40f82489f4d2d62bb7bb016ac2ae38629742"
RECONCILIATION_DIGEST = "11dad9e7b4f7d85f48bc2020ee4cc43c7de48e7832ca445fa1bf4742edff69e2"

MEASUREMENT_COUNT = 377
RECORDED_ASSESSMENT_COUNT = 527
ROUTING_POLICY_VERSION = "2"


@pytest.fixture(scope="module")
def inputs():
    return load_inputs()  # (routing_tables, band_rows, category_of, declared, recorded_instruments)


@pytest.fixture(scope="module")
def observations():
    return rows_from_parquet()


@pytest.fixture(scope="module")
def scores():
    return load_sources(_ROOT)["scores"]


@pytest.fixture(scope="module")
def measurement_rows(inputs, observations):
    tables, band_rows, category_of, declared, recorded = inputs
    return measurements(
        observations, tables, band_rows, category_of, declared, recorded,
        declaration_version_id=TEST_DVID,
        observation_snapshot_id=observation_snapshot_id(observations),
    )


@pytest.fixture(scope="module")
def reconciliation_rows(inputs, measurement_rows, scores, observations):
    tables, _, category_of, declared, _recorded = inputs
    return reconcile(
        scores, measurement_rows, tables, category_of, declared,
        declaration_version_id=TEST_DVID,
        observation_snapshot_id=observation_snapshot_id(observations),
        evaluated_at=None,
    )


def _digest(rows, serializer) -> str:
    return hashlib.sha256("\n".join(sorted(serializer(r) for r in rows)).encode("utf-8")).hexdigest()


def _measure(inputs, observation_rows, recorded_override=None, **overrides):
    tables, band_rows, category_of, declared, recorded = inputs
    ids = {"declaration_version_id": TEST_DVID, "observation_snapshot_id": "x" * 64}
    ids.update(overrides)
    return measurements(
        observation_rows, tables, band_rows, category_of, declared,
        recorded if recorded_override is None else recorded_override, **ids,
    )


def _obs(slug, artifact_kind, metric_type, raw_value, product_type="software", **kw):
    base = {
        "observation_id": f"{slug}:{artifact_kind}:{metric_type}",
        "product_slug": slug, "product_type": product_type, "artifact_kind": artifact_kind,
        "artifact_id": f"{slug}/{artifact_kind}", "channel": artifact_kind, "metric_type": metric_type,
        "raw_value": raw_value, "unit": metric_type, "measurement_window_days": None,
        "observed_at": datetime.datetime(2026, 8, 20, 12, 0, 0),
    }
    base.update(kw)
    return base


# --- measurements: shape and the pinned golden -----------------------------------


def test_measurements_reproduce_the_baseline_golden(measurement_rows):
    assert len(measurement_rows) == MEASUREMENT_COUNT
    assert _digest(measurement_rows, measurement_row) == MEASUREMENTS_DIGEST


def test_one_row_per_product(measurement_rows):
    slugs = [r["product_slug"] for r in measurement_rows]
    assert len(slugs) == len(set(slugs))


def test_all_three_identity_columns_are_stamped(measurement_rows):
    for row in measurement_rows:
        assert row["declaration_version_id"] == TEST_DVID
        assert row["observation_snapshot_id"] == BASELINE_SNAPSHOT_ID
        assert row["routing_policy_version"] == ROUTING_POLICY_VERSION


def test_only_machine_routes_win(measurement_rows):
    """Measured rows only ever carry an observable machine route; the hand-authored and unbridged
    routes are never measured (they have no observation)."""
    unobservable = {"active_users", "reported_traction", "npm.downloads_30d", "crates.downloads_30d"}
    assert not (unobservable & {r["route_id"] for r in measurement_rows})


# --- measurements: route selection is by declaration, and never falls through ----


def test_route_selection_is_by_declared_artifacts_not_observations(inputs, observations):
    """accelerate declares PyPI and GitHub. Remove only its PyPI observation: it must NOT fall
    through to GitHub stars — it produces no measurement row at all."""
    accelerate_obs = [o for o in observations if o["product_slug"] == "accelerate"]
    assert {"pypi", "github"} <= {o["artifact_kind"] for o in accelerate_obs}

    with_pypi = [r for r in _measure(inputs, observations) if r["product_slug"] == "accelerate"]
    assert [r["route_id"] for r in with_pypi] == ["pypi.downloads_30d"]

    no_pypi_obs = [
        o for o in observations
        if not (o["product_slug"] == "accelerate" and o["artifact_kind"] == "pypi")
    ]
    without_pypi = [r for r in _measure(inputs, no_pypi_obs) if r["product_slug"] == "accelerate"]
    assert without_pypi == [], "PyPI-declared product fell through to a weaker route"


def test_authoritative_active_users_precedes_stars(inputs):
    """A product recorded as active_users with a GitHub artifact must not be scored on stars: the
    authoritative hand-authored route outranks the fallback, and is unmeasured."""
    tables, band_rows, category_of, _declared, _recorded = inputs
    obs = [_obs("synthetic-au", "github", "stars", 5000)]
    declared = {"synthetic-au": {"github"}}

    def run(recorded):
        return measurements(
            obs, tables, band_rows, category_of, declared, recorded,
            declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
        )

    # Recorded as active_users: the active_users route wins, and it has no machine observation.
    assert run({"synthetic-au": "active_users"}) == []
    # With no recorded hand-authored instrument, the same product measures on stars.
    assert [r["route_id"] for r in run({})] == ["github.stargazers_count"]


def test_unbridged_npm_route_precedes_stars(inputs):
    """A product declaring an unbridged npm package must be unmeasured on the npm route, not scored
    on GitHub stars — an unbridged authoritative instrument does not fall through."""
    tables, band_rows, category_of, _declared, recorded = inputs
    obs = [_obs("synthetic-npm", "github", "stars", 5000)]
    with_npm = measurements(
        obs, tables, band_rows, category_of, {"synthetic-npm": {"npm", "github"}}, {},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert [r for r in with_npm if r["product_slug"] == "synthetic-npm"] == []
    without_npm = measurements(
        obs, tables, band_rows, category_of, {"synthetic-npm": {"github"}}, {},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert [r["route_id"] for r in without_npm if r["product_slug"] == "synthetic-npm"] == [
        "github.stargazers_count"
    ]


def test_winning_route_is_the_top_applicable_route(inputs, measurement_rows):
    tables, _, category_of, declared, recorded = inputs
    routes, scopes = all_routes(tables), route_scopes(tables)
    for row in measurement_rows:
        winner = select_route(
            declared[row["product_slug"]], recorded.get(row["product_slug"]),
            row["category_slug"], routes, scopes,
        )
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
    multi_star = [
        r for r in measurement_rows
        if r["route_id"] == "github.stargazers_count" and len(r["contributing_observation_ids"]) > 1
    ]
    assert multi_star
    for row in multi_star:
        assert row["aggregation_method"] == "sum"
        assert row["measured_level"] is not None


def test_no_measurement_abstains_in_the_baseline(measurement_rows):
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
    assert _numeric(1000.9, "raw_value") == 1000.9
    for bad in (True, "100", None, {1}):
        with pytest.raises(TypeError):
            _numeric(bad, "raw_value")
    for bad in (float("inf"), float("nan")):
        with pytest.raises(ValueError):
            _numeric(bad, "raw_value")


def test_native_coerces_pyoso_scalars_to_python_types():
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


def test_str_observed_at_from_pyoso_digests_identically_to_a_datetime():
    """The `--live` fix. `observed_at` arrives from `pyoso` as an ISO string (e.g. the deployed
    table returns `'2026-08-24 11:19:51'`), which the strict digest rejects on purpose. The
    load-boundary coercion must parse it into the same content as the equivalent `datetime`, for
    the naive form the warehouse emits and for aware forms that name the same instant."""
    instant = datetime.datetime(2026, 8, 24, 11, 19, 51)
    dt_digest = observation_content_digest([_obs("p", "package", "downloads_30d", 100, observed_at=instant)])

    for text in ("2026-08-24 11:19:51", "2026-08-24T11:19:51", "2026-08-24 11:19:51+00:00"):
        raw = [_obs("p", "package", "downloads_30d", 100, observed_at=text)]
        with pytest.raises(TypeError):  # the raw string is not a datetime and must be rejected
            observation_content_digest(raw)
        coerced = [{**r, "observed_at": _coerce_timestamp("observed_at", r["observed_at"])} for r in raw]
        assert observation_content_digest(coerced) == dt_digest


def test_coerce_timestamp_passes_through_and_fails_closed():
    assert _coerce_timestamp("observed_at", None) is None
    dt = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    assert _coerce_timestamp("observed_at", dt) is dt
    with pytest.raises(ValueError):  # unparseable text mints no identity
        _coerce_timestamp("observed_at", "not-a-timestamp")


def test_load_current_observations_coerces_pyoso_iso_string(monkeypatch):
    """The `--live` regression, pinned synthetically — no network, no skips. `pyoso` returns
    `observed_at` as an ISO string; `load_current_observations` must coerce it to a `datetime` at
    the load boundary so the strict digest (which rejects a string) accepts the row. An actual live
    read is the runbook's operational check (`docs/operations/deploy-evaluation.md`), not a required
    pytest that would skip without credentials or on legitimate table drift."""
    import build.warehouse

    fake_rows = [
        {
            "observation_id": "p:pypi:downloads_30d",
            "product_slug": "p", "product_type": "software", "artifact_kind": "pypi",
            "artifact_id": "p", "channel": "pypi", "metric_type": "downloads_30d",
            "raw_value": 1234, "unit": "downloads_30d", "measurement_window_days": 30,
            "observed_at": "2026-08-24 11:19:51",  # the exact shape pyoso returns: naive ISO string
        }
    ]
    monkeypatch.setattr(build.warehouse, "query", lambda sql: [dict(r) for r in fake_rows])
    from build.adoption_measurements import load_current_observations

    rows = load_current_observations()
    assert isinstance(rows[0]["observed_at"], datetime.datetime)  # coerced at the boundary
    assert observation_content_digest(rows) == observation_content_digest([
        {**fake_rows[0], "observed_at": datetime.datetime(2026, 8, 24, 11, 19, 51)}
    ])  # the coerced string digests identically to the equivalent datetime, and does not raise


def test_a_float_just_over_a_threshold_bands_above_not_floored():
    index = _band_index([
        {"band_set_id": "b", "level": 1, "above": -1, "reach": "lo"},
        {"band_set_id": "b", "level": 2, "above": 1000, "reach": "hi"},
    ])
    assert _band_for(index, "b", 1000.9) == (2, "hi")
    assert _band_for(index, "b", 1000) == (1, "lo")


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
    assert null_recorded
    by_product = {r["product_slug"]: r for r in reconciliation_rows}
    for slug in null_recorded:
        assert by_product[slug]["status"] == "abstained"


def test_no_delta_across_instrument_types(reconciliation_rows):
    """The core rule: a delta exists only when the measured and recorded instruments match."""
    for row in reconciliation_rows:
        if row["measured_instrument_type"] != row["recorded_instrument_type"]:
            assert row["delta"] is None


def test_cross_instrument_rows_are_mismatch_or_expected_difference(reconciliation_rows):
    """A measured row whose instrument differs from the recorded one is classified by authority,
    never source_unavailable and never a numeric comparison."""
    cross = [
        r for r in reconciliation_rows
        if r["measured_level"] is not None
        and r["measured_instrument_type"] != r["recorded_instrument_type"]
    ]
    assert cross  # the baseline has cross-instrument cases (e.g. reported_traction vs stars)
    for row in cross:
        assert row["status"] in {"route_mismatch", "expected_difference"}
        assert row["delta"] is None
        # An authoritative instrument on either side => mismatch; both weak => expected_difference.
        authoritative = row["route_authority"] == "authoritative" or row["recorded_instrument_type"] in {
            "usage_volume", "active_users"
        }
        assert row["status"] == ("route_mismatch" if authoritative else "expected_difference")


def test_same_instrument_measured_is_source_unavailable_with_a_delta(reconciliation_rows):
    same = [
        r for r in reconciliation_rows
        if r["measured_level"] is not None
        and r["measured_instrument_type"] == r["recorded_instrument_type"]
        and r["recorded_level"] is not None
    ]
    assert same
    for row in same:
        assert row["status"] == "source_unavailable"
        assert row["delta"] == row["measured_level"] - row["recorded_level"]


def test_unmeasured_rows_carry_no_measurement_fields(reconciliation_rows):
    """An unmeasured row has no measurement, so every measurement field is null — never the route's
    would-be instrument. The applicable-route context lives in route_id + route_authority instead."""
    unmeasured = [r for r in reconciliation_rows if r["status"] == "unmeasured"]
    assert unmeasured
    for row in unmeasured:
        for field in ("measured_level", "measured_instrument_type", "channel", "raw_value",
                      "measurement_as_of", "delta"):
            assert row[field] is None, f"{row['product_slug']}: unmeasured but {field}={row[field]!r}"
        assert row["route_id"] and row["route_authority"] is not None  # route context preserved


def test_every_status_is_in_the_allowed_set(reconciliation_rows):
    allowed = {"abstained", "source_unavailable", "unmeasured", "route_mismatch", "expected_difference"}
    for row in reconciliation_rows:
        assert row["status"] in allowed
        assert row["measurement_freshness"] == "unknown"
        assert row["override_id"] is None
        assert row["explanation"]
        assert row["routing_policy_version"] == ROUTING_POLICY_VERSION


def test_active_users_products_are_not_reconciled_against_stars(reconciliation_rows, scores):
    """A product recorded active_users must key on the active_users route (unmeasured), never on
    github stars — the authoritative-precedes-fallback rule reaching reconciliation."""
    for row in reconciliation_rows:
        if row["recorded_instrument_type"] == "active_users":
            assert row["route_id"] != "github.stargazers_count"
            assert row["measured_instrument_type"] != "stars_fallback"


def test_evaluated_at_is_excluded_from_the_content_digest(inputs, measurement_rows, scores, observations):
    tables, _, category_of, declared, _recorded = inputs
    osid = observation_snapshot_id(observations)
    kw = dict(declaration_version_id=TEST_DVID, observation_snapshot_id=osid)
    a = reconcile(scores, measurement_rows, tables, category_of, declared,
                  evaluated_at=datetime.datetime(2026, 1, 1), **kw)
    b = reconcile(scores, measurement_rows, tables, category_of, declared,
                  evaluated_at=datetime.datetime(2027, 6, 30), **kw)
    assert _digest(a, reconciliation_row) == _digest(b, reconciliation_row)
