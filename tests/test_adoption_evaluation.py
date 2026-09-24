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
# Moved on 2026-09-11 by the embeddings_retrieval promotion. MEASUREMENT_COUNT is unchanged at
# 377 - the new products carry no observation in the pinned snapshot, so no row was added - but
# the recorded bands they contribute change the content the digest covers.
# Moved again on 2026-09-11 by the agenta recategorization (#302): the product left
# telemetry_observability for orchestration_agents, and `category_slug` is one of the columns
# this digest covers. Same 377 rows, same band, one row's category.
# Moved on 2026-09-13 by the `not_primary_channel` declarations (#562), which is the fourth thing
# this digest tracks: a declaration change. `hexabot`'s npm widget and `yomo`'s crate are declared
# not to be how either product ships, so neither package kind bears a route any more and both
# products fall through to stars - 377 -> 379 rows, both new rows level 2, no existing row's
# value touched (only the added `non_primary_artifacts` column, empty everywhere else).
# Moved again on 2026-09-14 by WITHDRAWING a declaration (#448). `cohere-rerank-api` declared the
# `cohere` PyPI package, which is the vendor's whole client SDK - chat, embed, classify and rerank
# behind one client - so its downloads were never this product's. A declaration asserts that its
# numbers ARE the product's numbers (identity.md), so the fix is to remove it rather than to flag
# it: `not_primary_channel` keeps an artifact whose measurement does belong and drops it only from
# the banded sum, which is a different fact. 379 -> 378 rows, the lost row being this product's
# only machine route; its recorded level 3 reported_traction is unchanged and no other row moved.
# Moved on 2026-09-15 by #585, the first change to the EVALUATOR itself rather than to a
# declaration: partial coverage now abstains. Where the winning route was observed on some but not
# all of a product's declared primary artifacts of that kind, the sum is short by an unknown amount,
# so the band and the value are both suppressed. Three rows change and the row count does not -
# `composable-kernel` (1 of 2 github repos), `glm` (3 of 4 Hugging Face models) and `olmo-instruct`
# (1 of 2); each keeps its row and its contributing_observation_ids and loses measured_level,
# measured_reach and raw_value. This reproduces `is_complete` on the retired
# currentai.signal_packages.product_adoption; the zero-observation case still produces no row.
# Moved on 2026-09-15 by the ml_orchestration promotion (#429), and this is the first kind of
# move again rather than a new one: a product changed category. `ray` left `deployment` for
# `ml_orchestration`, and `category_slug` is one of the columns this digest covers. Measured
# rather than asserted - the row sets were dumped on both sides and diffed: 378 rows before
# and after, exactly one row different, and the only field that differs on it is
# `category_slug`. Same band, same channel, same contributing_observation_ids. The twenty-four
# products added in the same change contribute no rows, because measurements come from the
# frozen observation snapshot rather than from declared artifacts.
# Moved on 2026-09-16 by the document_conversion promotion (#430): three products changed
# category, and `category_slug` is one of the columns this digest covers. Measured rather than
# asserted - the row sets were dumped on both sides and diffed: 378 rows before and after, three
# rows different, and on each the only field that differs is `category_slug` (docling and
# markitdown out of agent_tools_protocols, olmocr out of dataset_processing_tools, all three into
# document_conversion). `marker` and `mineru` moved category too and have no rows, so the change
# is smaller than the roster move; the fifteen products promoted alongside them contribute none
# either, because measurements come from the frozen observation snapshot rather than from
# declared artifacts.
# Moved on 2026-09-17 by the search_retrieval promotion (#430), for the same reason and in the
# same shape. Measured rather than asserted - the row sets were dumped on both sides and diffed:
# 378 rows before and after, five rows different, and on each the only field that differs is
# `category_slug` (firecrawl, tavily-search-api, exa-search-api, jina-reader and searxng out of
# agent_tools_protocols and into search_retrieval). The other six movers and the ten promoted
# products contribute no rows, because measurements come from the frozen observation snapshot
# rather than from declared artifacts.
# Moved on 2026-09-17 by the agent_tools_protocols split, for the same reason and in the same
# shape. Measured rather than asserted - the row sets were dumped on both sides and diffed:
# 378 rows before and after, TWO rows different, and on each the only field that differs is
# `category_slug` (fastmcp and mcp-python-sdk out of agent_tools_protocols and into
# agent_protocols). The other five products that changed category carry no rows, and neither
# do the twenty promoted alongside them, because measurements come from the frozen observation
# snapshot rather than from declared artifacts.
# Moved on 2026-09-17 by the category RENAME, agent_tools_protocols ->
# agent_tools_connectors. `category_slug` is one of the columns this digest covers, so a
# rename moves it exactly as a product move does. Measured rather than asserted: 378 rows
# before and after, six rows different, and on each the only field that differs is the slug
# itself. No product changed category and no band moved.
MEASUREMENTS_DIGEST = "a9356bb01c5b8d2754ff8448df8bbfa11713780dc8e0c7ab8793654617666a12"
# Moved 2026-09-01 by the areal and xtuner relabels (#435): a recorded instrument change
# is a declaration change, which is one of the four things this digest tracks. Both
# levels stay where they were.
# Moved again 2026-09-01 by the Round 1 calibration tranche: 23 recorded assessments
# added with the new products (553 -> 576) and the gsm8k level moved 4 -> 5 on a fresh
# read. MEASUREMENTS_DIGEST is deliberately unchanged: measurements come from the
# warehouse observation parquet, which carries no rows for the new products yet.
# Moved again 2026-09-02 by the compilers round-2 promotion: 18 recorded assessments
# added with the new products (576 -> 594), every one of them a null-level abstention
# (adoption left for the warehouse to band). MEASUREMENTS_DIGEST is again unchanged for
# the same reason: no warehouse observation rows exist yet for the new products.
# Moved again 2026-09-02 by the storage and telemetry_observability legs of the same
# round-2 promotion: 19 more recorded assessments (594 -> 613; 12 storage, 7
# telemetry_observability), most hand-banded on stars/downloads rather than left null.
# MEASUREMENTS_DIGEST stays unchanged for the same reason as the compilers leg: no
# warehouse observation rows exist yet for any of the new products.
# Moved once more within the same tranche when the review fixes landed: the 18 compilers
# assessments went from null to a recorded band, and eight storage/telemetry_observability
# assessments changed instrument or level once client and component packages stopped
# standing in for the product measured. Same 613 rows; MEASUREMENTS_DIGEST unchanged.
# Census and digest now live in tests/goldens/corpus.json; see build/goldens.py.

MEASUREMENT_COUNT = 378
ROUTING_POLICY_VERSION = "2"


@pytest.fixture(scope="module")
def inputs():
    return load_inputs()  # build.adoption_measurements.Inputs, a 6-tuple


@pytest.fixture(scope="module")
def observations():
    return rows_from_parquet()


@pytest.fixture(scope="module")
def scores():
    return load_sources(_ROOT)["scores"]


@pytest.fixture(scope="module")
def measurement_rows(inputs, observations):
    tables, band_rows, category_of, declared, recorded, non_primary, primary = inputs
    return measurements(
        observations, tables, band_rows, category_of, declared, recorded, non_primary,
        primary_artifacts=primary,
        declaration_version_id=TEST_DVID,
        observation_snapshot_id=observation_snapshot_id(observations),
    )


@pytest.fixture(scope="module")
def reconciliation_rows(inputs, measurement_rows, scores, observations):
    tables, _, category_of, declared, _recorded, _non_primary, _primary = inputs
    return reconcile(
        scores, measurement_rows, tables, category_of, declared,
        declaration_version_id=TEST_DVID,
        observation_snapshot_id=observation_snapshot_id(observations),
        evaluated_at=None,
    )


def _digest(rows, serializer) -> str:
    return hashlib.sha256("\n".join(sorted(serializer(r) for r in rows)).encode("utf-8")).hexdigest()


def _measure(inputs, observation_rows, recorded_override=None, **overrides):
    tables, band_rows, category_of, declared, recorded, non_primary, primary = inputs
    ids = {"declaration_version_id": TEST_DVID, "observation_snapshot_id": "x" * 64,
           "primary_artifacts": primary}
    ids.update(overrides)
    return measurements(
        observation_rows, tables, band_rows, category_of, declared,
        recorded if recorded_override is None else recorded_override, non_primary, **ids,
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
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
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
    tables, band_rows, category_of, _declared, recorded, _non_primary, _primary = inputs
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
    tables, _, category_of, declared, recorded, _non_primary, _primary = inputs
    routes, scopes = all_routes(tables), route_scopes(tables)
    for row in measurement_rows:
        winner = select_route(
            declared[row["product_slug"]], recorded.get(row["product_slug"]),
            row["category_slug"], routes, scopes,
        )
        assert winner is not None and winner["route_id"] == row["route_id"]


# --- a declared artifact that is not how the product ships -----------------------


def test_non_primary_artifact_leaves_the_sum_and_nothing_else(inputs):
    """Two PyPI packages, one declared `not_primary_channel`: the PyPI route still applies -- the
    product does ship a package -- and the figure is the primary package alone. The excluded
    observation is still in the input set and still nameable; only the sum moves."""
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
    obs = [
        _obs("synthetic-np", "pypi", "downloads", 900_000, artifact_id="ships-this"),
        _obs("synthetic-np", "pypi", "downloads", 40, artifact_id="widget", observation_id="widget-obs"),
    ]
    rows = measurements(
        obs, tables, band_rows, category_of, {"synthetic-np": {"pypi"}}, {},
        {"synthetic-np": {("pypi", "widget")}},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["route_id"] == "pypi.downloads_30d"
    assert row["raw_value"] == 900_000, "the non-primary package was summed in"
    assert row["contributing_observation_ids"] == ["synthetic-np:pypi:downloads"]
    assert row["non_primary_artifacts"] == "pypi:widget"


def test_a_kind_that_is_all_non_primary_falls_through_to_the_next_route(inputs):
    """The all-non-primary case, which is `hexabot` and `yomo`. The product ships through no
    package at all, so the package kind bears no route and the next applicable one wins. This is
    NOT the forbidden fallthrough: that one substitutes a weaker route when an authoritative route
    was merely unobserved, and here the declaration says there is nothing to observe."""
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
    obs = [
        _obs("synthetic-all-np", "github", "stars", 4_000),
        _obs("synthetic-all-np", "pypi", "downloads", 40, artifact_id="widget"),
    ]
    kw = dict(declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64)
    # What load_inputs computes for such a product: pypi is declared but is not a shipping channel.
    rows = measurements(
        obs, tables, band_rows, category_of, {"synthetic-all-np": {"github"}}, {},
        {"synthetic-all-np": {("pypi", "widget")}}, **kw,
    )
    assert [(r["route_id"], r["measured_level"], r["raw_value"]) for r in rows] == [
        ("github.stargazers_count", 2, 4_000)
    ]
    assert rows[0]["non_primary_artifacts"] == "pypi:widget"
    # Banding the package anyway would have produced a level off 40 downloads, not 4,000 stars.
    without = measurements(
        obs, tables, band_rows, category_of, {"synthetic-all-np": {"pypi", "github"}}, {}, {}, **kw,
    )
    assert [(r["route_id"], r["raw_value"]) for r in without] == [("pypi.downloads_30d", 40)]


def test_an_unobserved_primary_artifact_still_produces_no_row(inputs):
    """The boundary the exclusion must not cross. A product with one primary package and one
    non-primary one, where only the non-primary was observed, is UNMEASURED -- it does not fall
    through to stars, because the route it declares is applicable and simply was not collected."""
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
    obs = [
        _obs("synthetic-unobs", "github", "stars", 4_000),
        _obs("synthetic-unobs", "pypi", "downloads", 40, artifact_id="widget"),
    ]
    rows = measurements(
        obs, tables, band_rows, category_of, {"synthetic-unobs": {"pypi", "github"}}, {},
        {"synthetic-unobs": {("pypi", "widget")}},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert rows == []


def test_partial_coverage_abstains_and_suppresses_the_short_sum(inputs):
    """#585. The winning route WAS observed, but not on every artifact the product declares as a
    shipping channel on that kind, so the aggregate is short by an unknown amount. The band and the
    value both go: leaving a short sum in raw_value with a null level invites a reader to band it
    themselves, which is the error this prevents. The audit trail stays."""
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
    obs = [_obs("synthetic-partial", "pypi", "downloads", 5_000_000, artifact_id="pkg-a")]
    rows = measurements(
        obs, tables, band_rows, category_of, {"synthetic-partial": {"pypi"}}, {}, {},
        primary_artifacts={"synthetic-partial": {("pypi", "pkg-a"), ("pypi", "pkg-b")}},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["measured_level"] is None
    assert row["measured_reach"] is None
    assert row["raw_value"] is None
    # the row is the record of WHY it abstained, so the trail survives
    assert row["contributing_observation_ids"]
    assert row["measurement_as_of"] is not None


def test_complete_coverage_still_bands(inputs):
    """The other side of the same boundary: every declared primary artifact of the winning kind was
    observed, so the sum is whole and bands normally."""
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
    obs = [
        _obs("synthetic-complete", "pypi", "downloads", 4_000_000, artifact_id="pkg-a"),
        _obs("synthetic-complete", "pypi", "downloads", 1_000_000, artifact_id="pkg-b"),
    ]
    rows = measurements(
        obs, tables, band_rows, category_of, {"synthetic-complete": {"pypi"}}, {}, {},
        primary_artifacts={"synthetic-complete": {("pypi", "pkg-a"), ("pypi", "pkg-b")}},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert len(rows) == 1
    assert rows[0]["raw_value"] == 5_000_000
    assert rows[0]["measured_level"] is not None


def test_completeness_is_scoped_to_the_winning_route_kind(inputs):
    """A product declaring an unmeasured artifact of some OTHER kind is not short on the route that
    won. Without the kind filter, any unobserved github repo would suppress a complete pypi sum."""
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
    obs = [_obs("synthetic-otherkind", "pypi", "downloads", 5_000_000, artifact_id="pkg-a")]
    rows = measurements(
        obs, tables, band_rows, category_of, {"synthetic-otherkind": {"pypi", "github"}}, {}, {},
        primary_artifacts={"synthetic-otherkind": {("pypi", "pkg-a"), ("github", "org/unseen")}},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert len(rows) == 1
    assert rows[0]["raw_value"] == 5_000_000
    assert rows[0]["measured_level"] is not None


def test_a_non_primary_artifact_is_not_counted_as_missing_coverage(inputs):
    """`not_primary_channel` takes the artifact out of the sum AND out of the completeness test.
    Counting it as missing would abstain every product carrying one -- hexabot and yomo included --
    which is the opposite of the 2026-08-14 ruling."""
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
    obs = [_obs("synthetic-np", "pypi", "downloads", 5_000_000, artifact_id="pkg-a")]
    rows = measurements(
        obs, tables, band_rows, category_of, {"synthetic-np": {"pypi"}}, {},
        {"synthetic-np": {("pypi", "widget")}},
        primary_artifacts={"synthetic-np": {("pypi", "pkg-a")}},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert len(rows) == 1
    assert rows[0]["raw_value"] == 5_000_000
    assert rows[0]["measured_level"] is not None


def test_zero_coverage_still_produces_no_row_at_all(inputs):
    """The completeness test must not swallow the zero-observation case, which is a DIFFERENT
    outcome: no row, reconciled as `unmeasured`, rather than a row abstaining."""
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
    rows = measurements(
        [], tables, band_rows, category_of, {"synthetic-none": {"pypi"}}, {}, {},
        primary_artifacts={"synthetic-none": {("pypi", "pkg-a")}},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert rows == []


def test_omitting_primary_artifacts_disables_the_check(inputs):
    """The default is "no completeness data, do not enforce" -- right for a synthetic input set and
    never for a real one. Pinned because it is exactly how a production caller that forgets to pass
    it would fail: silently, still banding short sums."""
    tables, band_rows, category_of, _declared, _recorded, _non_primary, _primary = inputs
    obs = [_obs("synthetic-off", "pypi", "downloads", 5_000_000, artifact_id="pkg-a")]
    rows = measurements(
        obs, tables, band_rows, category_of, {"synthetic-off": {"pypi"}}, {}, {},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64,
    )
    assert len(rows) == 1
    assert rows[0]["measured_level"] is not None


def test_load_inputs_reads_the_declaration_off_the_registry():
    """Both readings come from `registry.product_artifacts`, which is where the serializer now
    carries the reason. The artifact keeps its row and the product keeps its key; what it loses is
    that KIND as a route-bearing channel."""
    inputs = load_inputs()
    assert inputs.declared_artifacts["hexabot"] == {"github"}
    assert inputs.non_primary_artifacts["hexabot"] == {("npm", "@hexabot-ai/widget")}
    assert inputs.declared_artifacts["yomo"] == {"github"}
    assert inputs.non_primary_artifacts["yomo"] == {("crates", "yomo")}
    # AfroBench (#689) declares its member datasets: they are downloaded on their own, so their
    # downloads are not runs of the suite, and it keeps only its GitHub and arXiv routes.
    assert inputs.declared_artifacts["afrobench"] == {"github", "arxiv"}
    assert {kind for kind, _ in inputs.non_primary_artifacts["afrobench"]} == {"huggingface_dataset"}
    # Nothing else declares one, so nothing else can have moved.
    assert set(inputs.non_primary_artifacts) == {"hexabot", "yomo", "afrobench"}


def test_the_two_declared_products_band_on_stars_at_two(measurement_rows):
    """The 2026-08-14 minority-channel ruling holds both at level 2. Banding them on a package
    neither ships through fell both to 1, which is what the warehouse models did while
    `not_primary_channel` resolved NULL."""
    rows = {r["product_slug"]: r for r in measurement_rows if r["product_slug"] in ("hexabot", "yomo")}
    assert set(rows) == {"hexabot", "yomo"}
    for slug, row in rows.items():
        assert row["route_id"] == "github.stargazers_count", slug
        assert row["measured_level"] == 2, slug
        assert row["non_primary_artifacts"], slug


def test_no_other_product_carries_an_exclusion(measurement_rows):
    """The column is empty everywhere else, so a reader can tell an exclusion from an absence."""
    carrying = {r["product_slug"] for r in measurement_rows if r["non_primary_artifacts"]}
    assert carrying == {"hexabot", "yomo"}


# --- measurements: aggregation, numbers, banding ---------------------------------


def test_usage_volume_sums_across_contributing_artifacts(measurement_rows):
    summed = [
        r for r in measurement_rows
        if r["instrument_type"] == "usage_volume" and len(r["contributing_observation_ids"]) > 1
    ]
    assert summed
    for row in summed:
        assert row["aggregation_method"] == "sum"
        # raw_value is None on a partial-coverage abstention (#585) -- the short sum is suppressed
        # along with the band. Where a value survives, it is still a real non-negative aggregate.
        assert row["raw_value"] is None or row["raw_value"] >= 0


def test_stars_sum_rule_aggregates_multiple_repositories(measurement_rows):
    multi_star = [
        r for r in measurement_rows
        if r["route_id"] == "github.stargazers_count" and len(r["contributing_observation_ids"]) > 1
    ]
    assert multi_star
    for row in multi_star:
        assert row["aggregation_method"] == "sum"
        assert row["measured_level"] is not None


def test_the_live_partial_coverage_rows_get_the_coverage_explanation(
        inputs, measurement_rows, scores, observations):
    """The explanation must name the RIGHT cause. This branch used to blame the band set in every
    case, which is right for a missing ladder and wrong for short coverage."""
    tables, _, category_of, declared, _recorded, _non_primary, _primary = inputs
    rows = reconcile(
        scores, measurement_rows, tables, category_of, declared,
        declaration_version_id=TEST_DVID,
        observation_snapshot_id=observation_snapshot_id(observations), evaluated_at=None,
    )
    by_slug = {r["product_slug"]: r for r in rows}
    for slug in ("composable-kernel", "glm", "olmo-instruct"):
        row = by_slug[slug]
        assert row["status"] == "abstained", slug
        assert "not on every declared primary artifact" in row["explanation"], slug


def test_a_rule_less_route_with_one_observation_still_reads_as_short_coverage(inputs, scores):
    """The discriminator's sharp edge. A rule-less route with exactly ONE contributing observation
    and two declared primary artifacts takes the `len(values) == 1` path in measurements(), so it
    carries an EMPTY aggregation_method and is genuinely short on coverage. An earlier version
    keyed the coverage arm on the method being non-empty and sent this row to the generic wording.
    Keying on the observation count instead keeps it where it belongs."""
    row = {
        "product_slug": "synthetic-ruleless", "category_slug": "c", "product_type": "software",
        "route_id": "pypi.downloads_30d", "channel": "pypi", "metric_type": "downloads",
        "instrument_type": "usage_volume", "aggregation_method": "",
        "contributing_observation_ids": ["one"], "non_primary_artifacts": "",
        "raw_value": None, "unit": "downloads", "measurement_window_days": 30,
        "band_set_id": "type:software", "measured_level": None, "measured_reach": None,
        "route_authority": "authoritative", "measurement_as_of": None,
        "declaration_version_id": TEST_DVID, "observation_snapshot_id": "x" * 64,
        "routing_policy_version": ROUTING_POLICY_VERSION,
    }
    tables, _, category_of, declared, _recorded, _non_primary, _primary = inputs
    out = reconcile(
        {"synthetic-ruleless": {"adoption": {"level": 3, "signal_type": "usage_volume"}}},
        [row], tables, {**category_of, "synthetic-ruleless": "c"},
        {**declared, "synthetic-ruleless": {"pypi"}},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64, evaluated_at=None,
    )
    match = [r for r in out if r["product_slug"] == "synthetic-ruleless"]
    assert match, "the synthetic row was not reconciled"
    assert match[0]["status"] == "abstained"
    assert "not on every declared primary artifact" in match[0]["explanation"]
    assert "undefined aggregation" not in match[0]["explanation"]


def test_a_row_with_two_causes_reports_both(inputs, scores):
    """Causes are not mutually exclusive and the explanation must not mask one with another. A
    product type with no usage ladder can ALSO be short on coverage; an earlier version led with
    the missing ladder and told the reader to add one, when adding one still would not have
    produced a value."""
    row = {
        "product_slug": "synthetic-both", "category_slug": "c", "product_type": "hardware",
        "route_id": "pypi.downloads_30d", "channel": "pypi", "metric_type": "downloads",
        "instrument_type": "usage_volume", "aggregation_method": "sum",
        "contributing_observation_ids": ["one"], "non_primary_artifacts": "",
        "raw_value": None, "unit": "downloads", "measurement_window_days": 30,
        "band_set_id": "", "measured_level": None, "measured_reach": None,
        "route_authority": "authoritative", "measurement_as_of": None,
        "declaration_version_id": TEST_DVID, "observation_snapshot_id": "x" * 64,
        "routing_policy_version": ROUTING_POLICY_VERSION,
    }
    tables, _, category_of, declared, _recorded, _non_primary, _primary = inputs
    out = reconcile(
        {"synthetic-both": {"adoption": {"level": 2, "signal_type": "usage_volume"}}},
        [row], tables, {**category_of, "synthetic-both": "c"},
        {**declared, "synthetic-both": {"pypi"}},
        declaration_version_id=TEST_DVID, observation_snapshot_id="x" * 64, evaluated_at=None,
    )
    match = [r for r in out if r["product_slug"] == "synthetic-both"]
    assert match, "the synthetic row was not reconciled"
    explanation = match[0]["explanation"]
    assert match[0]["status"] == "abstained"
    assert "not on every declared primary artifact" in explanation, explanation
    assert "no band set is declared" in explanation, explanation


def test_the_baseline_abstains_only_on_partial_coverage(measurement_rows):
    """Before #585 the baseline had no abstentions at all. It now has exactly the rows whose
    winning route was observed on some but not all of the product's declared primary artifacts of
    that kind -- the short sums that used to band. Named rather than counted: an abstention
    appearing for any other reason is a finding, not a tolerance."""
    abstained = {r["product_slug"] for r in measurement_rows if r["measured_level"] is None}
    assert abstained == {"composable-kernel", "glm", "olmo-instruct"}
    for row in measurement_rows:
        if row["measured_level"] is None:
            # the short aggregate goes with the band, and the audit trail stays
            assert row["raw_value"] is None
            assert row["contributing_observation_ids"]


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


def test_every_recorded_assessment_gets_exactly_one_row(reconciliation_rows, scores):
    recorded = {s for s, doc in scores.items() if isinstance(doc.get("adoption"), dict)}
    rows_by_product = [r["product_slug"] for r in reconciliation_rows]
    assert set(rows_by_product) == recorded
    assert len(rows_by_product) == len(recorded)


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
    tables, _, category_of, declared, _recorded, _non_primary, _primary = inputs
    osid = observation_snapshot_id(observations)
    kw = dict(declaration_version_id=TEST_DVID, observation_snapshot_id=osid)
    a = reconcile(scores, measurement_rows, tables, category_of, declared,
                  evaluated_at=datetime.datetime(2026, 1, 1), **kw)
    b = reconcile(scores, measurement_rows, tables, category_of, declared,
                  evaluated_at=datetime.datetime(2027, 6, 30), **kw)
    assert _digest(a, reconciliation_row) == _digest(b, reconciliation_row)
