"""The adoption routing compiler, and its acceptance test: round-trip completeness.

`build/serialize_routing.py` compiles `dimensions.adoption` from signal_routing.yaml into
`registry.adoption_routes`, `registry.adoption_route_scopes`,
`registry.adoption_route_band_sets` and `registry.adoption_aggregation_rules`, so evaluation
reads normalized facts and never reinterprets the YAML (AD-1).

The acceptance test (data-architecture.md 4.1) is NOT column presence but round-trip
completeness: every semantic field in the adoption portion of the YAML is either compiled
into these tables or explicitly classified documentation-only. A field that is neither must
fail here, so the next field added to a route cannot slip out of the warehouse unnoticed.
"""

import copy
from pathlib import Path

import pytest

from build.serialize_routing import build_routing, load_routing
from build.serialize_rubric import adoption_bands, route_bands
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]

# Round-trip completeness is checked at FOUR levels, each with its own compiled/doc-only sets,
# because the adoption YAML nests: the dimension holds routes and an aggregation block, a route
# holds bands. Classifying only the route-level keys — and treating the whole `aggregation` and
# `bands` containers as "compiled" — let a new field nested inside either be dropped silently.
# The census below recurses into every structural container and fails on any unclassified field
# at any level.

# Contract 1 — the adoption dimension. `routes` and `aggregation` are structural containers the
# census recurses into; `question` is the dimension's prose prompt.
_DIM_STRUCTURAL = {"routes", "aggregation"}
_DIM_DOC_ONLY = {"question"}

# Contract 2 — a route. These reach one of the tables (or, for the structural `bands` container,
# the adoption_bands table `band_set_id` links to). `note`, `attribution_note` and
# `vocabulary_note` are prose a reader consults the YAML for.
_ROUTE_STRUCTURAL = {"bands"}
_ROUTE_COMPILED = {
    "source",
    "column",
    "signal_type",
    "authority",
    "confidence",
    "unit",
    "cap",
    "cap_because",
    "applies_to_categories",
    "hand_authored",
    "requires_evidence",
    "vocabulary",
}
_ROUTE_DOC_ONLY = {"note", "attribution_note", "vocabulary_note"}

# Contract 3 — an aggregation rule, walked from `dimension["aggregation"][*]`.
_AGG_COMPILED = {"rule_id", "method", "scope", "applies_to_instrument"}
_AGG_DOC_ONLY = {"note"}

# Contract 4 — a band, walked from each route's `bands[*]`. Every field compiles into
# adoption_bands; nothing here is documentation-only.
_BAND_COMPILED = {"level", "above", "reach"}
_BAND_DOC_ONLY: set[str] = set()


def _assert_classified(kind, fields, compiled, doc_only, structural=frozenset()):
    """A field at one level is compiled, classified documentation-only, or a structural
    container the census recurses into. Anything else fails."""
    unclassified = set(fields) - set(compiled) - set(doc_only) - set(structural)
    assert not unclassified, (
        f"{kind} fields neither compiled nor classified documentation-only: {sorted(unclassified)}. "
        f"Compile the field into serialize_routing, or classify it documentation-only with a reason."
    )


def _census(adoption):
    """Run the four-contract round-trip completeness census, recursing into every structural
    container. Raises AssertionError on any unclassified field at any level."""
    # Contract 1: the dimension itself.
    _assert_classified(
        "adoption dimension", adoption, compiled=set(),
        doc_only=_DIM_DOC_ONLY, structural=_DIM_STRUCTURAL,
    )
    # Contract 2: every route.
    route_fields: set[str] = set()
    for route in adoption["routes"]:
        route_fields |= set(route)
    _assert_classified(
        "route", route_fields, compiled=_ROUTE_COMPILED,
        doc_only=_ROUTE_DOC_ONLY, structural=_ROUTE_STRUCTURAL,
    )
    # Contract 3: every aggregation rule.
    agg_fields: set[str] = set()
    for rule in adoption.get("aggregation") or []:
        agg_fields |= set(rule)
    _assert_classified("aggregation rule", agg_fields, compiled=_AGG_COMPILED, doc_only=_AGG_DOC_ONLY)
    # Contract 4: every band on every route.
    band_fields: set[str] = set()
    for route in adoption["routes"]:
        for band in route.get("bands") or []:
            band_fields |= set(band)
    _assert_classified("band", band_fields, compiled=_BAND_COMPILED, doc_only=_BAND_DOC_ONLY)


@pytest.fixture(scope="module")
def routing():
    return load_routing(ROOT)


@pytest.fixture(scope="module")
def rubrics():
    return load_sources(ROOT).get("rubrics") or {}


@pytest.fixture(scope="module")
def categories():
    return load_sources(ROOT).get("categories") or {}


@pytest.fixture(scope="module")
def adoption(routing):
    return routing["dimensions"]["adoption"]


@pytest.fixture(scope="module")
def tables(routing, rubrics, categories):
    tables, errors, _warnings = build_routing(routing, rubrics, categories)
    assert errors == [], errors
    return tables


def test_every_adoption_field_is_compiled_or_classified_documentation(adoption):
    """Round-trip completeness, recursive. A field that is neither compiled nor documentation-
    only fails — at the dimension, route, aggregation-rule OR band level.

    This is the check the spec calls the acceptance test: it is what makes the tables a
    faithful compilation of the YAML rather than a lossy subset that drifts as fields are added.
    Recursing into the `aggregation` and `bands` containers is what stops a new nested field
    from being dropped silently while its container reads as "compiled".
    """
    _census(adoption)


def test_a_planted_aggregation_rule_field_fails_the_census(adoption):
    """A new field nested inside an aggregation rule must be caught by the census, not slip
    through because the whole `aggregation` container was classified compiled."""
    planted = copy.deepcopy(adoption)
    planted["aggregation"][0]["mystery_agg_field"] = "x"
    with pytest.raises(AssertionError, match="aggregation rule"):
        _census(planted)


def test_a_planted_route_band_field_fails_the_census(adoption):
    """The same, one container deeper: a new field inside a route's band must fail the census
    rather than ride along because `bands` was classified compiled."""
    planted = copy.deepcopy(adoption)
    for route in planted["routes"]:
        if route.get("bands"):
            route["bands"][0]["mystery_band_field"] = "x"
            break
    else:
        pytest.fail("no route declares bands; the fixture cannot exercise the band census")
    with pytest.raises(AssertionError, match="band"):
        _census(planted)


def test_every_route_compiles_to_one_row_in_contiguous_order(adoption, tables):
    rows = tables["adoption_routes"]
    assert len(rows) == len(adoption["routes"])
    assert [r["route_order"] for r in rows] == list(range(1, len(rows) + 1))


def test_routes_are_in_the_declared_precedence_order(tables):
    """Precedence is monotonic in authority — the five authoritative routes first, then the two
    fallback routes — and within the authoritative download channels the ADR-001 order is
    `pypi > huggingface`. This pins the EXACT ordered route_ids, not merely that route_order is
    contiguous, so a reorder that breaks ADR-001 fails here rather than passing silently."""
    assert [r["route_id"] for r in tables["adoption_routes"]] == [
        "pypi.downloads_30d",
        "huggingface_model.downloads_30d",
        "huggingface_dataset.downloads_30d",
        "semanticscholar.citation_count",
        "active_users",
        "github.stargazers_count",
        "reported_traction",
    ]


def test_null_source_routes_are_empty_source_and_hand_authored(tables):
    """The two hand-authored instruments read no machine source, so their source compiles to
    the empty string and hand_authored is True — the fact that keeps evaluation from expecting
    a fetch behind them."""
    hand = [r for r in tables["adoption_routes"] if r["hand_authored"]]
    assert {r["instrument_type"] for r in hand} == {"active_users", "reported_traction"}
    for row in hand:
        assert row["source"] == ""
        assert row["hand_authored"] is True


def test_semantic_field_values_reach_the_tables(adoption, tables):
    """Not just classified as compiled — actually present. Each semantic field's value is
    found in the output it maps to, so the classification above cannot pass while the value
    is silently dropped."""
    routes = tables["adoption_routes"]
    by_instrument = {r["instrument_type"]: r for r in routes}

    # source / column -> route_id and their own columns; signal_type -> instrument_type.
    for route in adoption["routes"]:
        source = route.get("source") or ""
        column = route.get("column") or ""
        signal_type = route["signal_type"]
        route_id = f"{source}.{column}" if source else signal_type
        row = next(r for r in routes if r["route_id"] == route_id)
        assert row["source"] == source
        assert row["source_column"] == column
        assert row["instrument_type"] == signal_type
        assert row["confidence"] == route["confidence"]
        assert row["authority"] == route["authority"]

    # unit (active_users declares one), cap (stars caps at 3), cap_reason (its prose compiled).
    # Indexed by instrument, not list position: the route order is precedence and may change.
    active_route = next(r for r in adoption["routes"] if r["signal_type"] == "active_users")
    assert by_instrument["active_users"]["unit"] == active_route["unit"]
    assert by_instrument["stars_fallback"]["cap"] == 3
    assert by_instrument["stars_fallback"]["cap_reason"].startswith("Stars measure attention")

    # requires_evidence pipe-joined for the two hand-authored routes.
    assert by_instrument["active_users"]["requires_evidence"] == "accessed|content_sha256"
    assert by_instrument["reported_traction"]["requires_evidence"] == "accessed|content_sha256"

    # vocabulary on reported_traction only.
    assert by_instrument["reported_traction"]["vocabulary"] == "niche|broad|mass-market"

    # applies_to_categories -> a scope row; the aggregation block -> the one aggregation rule.
    assert {"route_id": "semanticscholar.citation_count", "scope_type": "category",
            "scope_value": "benchmark_eval_data"} in tables["adoption_route_scopes"]
    assert tables["adoption_aggregation_rules"] == [
        {"aggregation_rule_id": "sum_usage_across_artifacts", "method": "sum",
         "scope": "artifacts", "applies_to_instrument": "usage_volume"}
    ]


def test_artifact_kind_is_the_sources_artifact_key_not_the_source_name(tables):
    """`artifact_kind` is read from the source's declared `artifact_key`, not from a hardcoded
    map. `semanticscholar`'s key is `arxiv`, so the route compiles `arxiv` — matching
    `registry.product_artifacts.artifact_kind` — rather than a guessed `paper` off the name."""
    by_id = {r["route_id"]: r for r in tables["adoption_routes"]}
    assert by_id["semanticscholar.citation_count"]["artifact_kind"] == "arxiv"
    # The point is the name and the key differ; the compiler followed the key.
    assert by_id["semanticscholar.citation_count"]["source"] == "semanticscholar"


def test_routing_policy_version_is_the_declared_version(routing, tables):
    """The bare version publishes only under `routing_policy_version`. It must NOT reappear
    under a release-identity-sounding name like `declaration_version_id`."""
    version = str(routing["version"])
    for row in tables["adoption_routes"]:
        assert row["routing_policy_version"] == version
        assert "declaration_version_id" not in row
        assert "policy_version" not in row


def test_aggregation_rule_id_is_set_only_where_the_instrument_matches(tables):
    """A route carries the aggregation rule whose `applies_to_instrument` equals its own
    instrument, and no method string is duplicated onto the route. usage_volume routes get
    `sum_usage_across_artifacts`; every other route gets the empty string."""
    rule = tables["adoption_aggregation_rules"][0]
    for row in tables["adoption_routes"]:
        if row["instrument_type"] == rule["applies_to_instrument"]:
            assert row["aggregation_rule_id"] == rule["aggregation_rule_id"]
        else:
            assert row["aggregation_rule_id"] == ""
        # The method string lives on the rule, not the route.
        assert "aggregation_method" not in row


def test_every_route_band_set_resolves_to_an_adoption_bands_row(routing, rubrics, tables):
    """Every `adoption_route_band_sets` row names a band set that resolves to at least one
    `adoption_bands` row — with NO sentinel exemption. The `type:*`/'' sentinels are gone:
    a route x product type that resolves to no scale (hardware usage_volume, reported_traction)
    emits no row at all, so evaluation abstains by finding nothing to join to.
    """
    bands, _ = adoption_bands(rubrics)
    route_scale_rows, _ = route_bands(routing)
    band_ids = {b["band_set_id"] for b in bands + route_scale_rows}

    rows = tables["adoption_route_band_sets"]
    assert rows, "no route band sets emitted"
    for row in rows:
        assert row["band_set_id"].startswith(("route:", "type:")), row
        assert row["band_set_id"] in band_ids, (
            f"route {row['route_id']!r} for product type {row['product_type']!r} points at "
            f"band_set_id {row['band_set_id']!r}, which no adoption_bands row carries"
        )


def test_hardware_usage_volume_has_no_band_set_row(tables):
    """Hardware is qualitative and declares no usage_volume bands, so a usage_volume route
    emits no row for it — evaluation abstains for hardware usage_volume by joining to nothing,
    which is the "abstain rather than substitute" rule expressed as a missing row."""
    usage_routes = {
        r["route_id"] for r in tables["adoption_routes"] if r["instrument_type"] == "usage_volume"
    }
    for row in tables["adoption_route_band_sets"]:
        if row["route_id"] in usage_routes:
            assert row["product_type"] != "hardware", row


def test_type_independent_scales_cover_every_product_type(rubrics, tables):
    """A star is a star and a monthly active user is a person whatever the product type, so
    those two routes emit a row for EVERY product type, not just the banded ones."""
    all_types = set(rubrics.keys())
    by_route: dict[str, set[str]] = {}
    for row in tables["adoption_route_band_sets"]:
        by_route.setdefault(row["route_id"], set()).add(row["product_type"])
    assert by_route["github.stargazers_count"] == all_types
    assert by_route["active_users"] == all_types


def test_reported_traction_resolves_to_no_band_set(tables):
    """A vocabulary instrument with no bands resolves to nothing, so it emits no band-set row."""
    assert not any(
        r["route_id"] == "reported_traction" for r in tables["adoption_route_band_sets"]
    )


def test_source_null_routes_carry_no_derived_artifact_or_metric(tables):
    """A null-source, hand-authored route names no artifact and reads no column, so both
    derived fields are empty rather than a guessed default."""
    for row in tables["adoption_routes"]:
        if row["hand_authored"]:
            assert row["artifact_kind"] == ""
            assert row["metric_type"] == ""


# --- HARD ERRORS: an unknown derivation or a duplicate must fail the compiler ----------


def test_a_source_absent_from_the_sources_block_is_an_error(routing, rubrics, categories):
    """A non-null source the `sources:` block does not declare cannot yield an artifact_kind,
    so it is an error rather than a blank."""
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["routes"].append(
        {"source": "notasource", "column": "downloads_30d", "signal_type": "usage_volume",
         "authority": "authoritative"}
    )
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("notasource" in e and "sources:" in e for e in errors), errors


def test_a_source_with_no_artifact_key_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    bad["sources"]["keyless"] = {"table": "x"}
    bad["dimensions"]["adoption"]["routes"].append(
        {"source": "keyless", "column": "downloads_30d", "signal_type": "usage_volume",
         "authority": "authoritative"}
    )
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("keyless" in e and "artifact_key" in e for e in errors), errors


def test_a_column_with_no_metric_type_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["routes"].append(
        {"source": "huggingface_model", "column": "not_a_metric", "signal_type": "usage_volume",
         "authority": "authoritative"}
    )
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("not_a_metric" in e and "metric_type" in e for e in errors), errors


def test_a_missing_authority_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    del bad["dimensions"]["adoption"]["routes"][0]["authority"]
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("authority" in e for e in errors), errors


def test_an_invalid_authority_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["routes"][0]["authority"] = "supreme"
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("authority" in e and "supreme" in e for e in errors), errors


def test_a_duplicate_route_id_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    routes = bad["dimensions"]["adoption"]["routes"]
    routes.append(copy.deepcopy(routes[0]))
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("duplicate route_id" in e for e in errors), errors


def test_a_band_set_absent_from_adoption_bands_is_an_error(routing, rubrics, categories):
    """Referential integrity. If the stars scale loses its `bands` on the route, `route_bands`
    stops emitting `route:stars_fallback`, but the band-set join still points at it — a
    dangling reference that must fail the serializer rather than publish a broken join."""
    bad = copy.deepcopy(routing)
    for route in bad["dimensions"]["adoption"]["routes"]:
        if route.get("signal_type") == "stars_fallback":
            route.pop("bands", None)
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("route:stars_fallback" in e and "adoption_bands" in e for e in errors), errors


def test_authority_is_read_from_the_yaml_not_a_constant(routing, rubrics, categories):
    """Flipping a route's declared authority in an in-memory copy changes the output, proving
    the value is compiled from the YAML rather than looked up in a Python constant."""
    flipped = copy.deepcopy(routing)
    route = flipped["dimensions"]["adoption"]["routes"][0]
    assert route["authority"] == "authoritative"
    route["authority"] = "fallback"
    tables, errors, _ = build_routing(flipped, rubrics, categories)
    assert errors == [], errors
    row = next(r for r in tables["adoption_routes"] if r["route_order"] == 1)
    assert row["authority"] == "fallback"


def test_an_unknown_signal_type_is_an_error(routing, rubrics, categories):
    """A route instrument outside the canonical vocabulary used to compile an eighth route
    with no error; it is now checked against build/vocabulary.SIGNAL_TYPES."""
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["routes"][0]["signal_type"] = "mystery"
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("signal_type" in e and "mystery" in e for e in errors), errors


def test_signal_type_unknown_is_not_routable(routing, rubrics, categories):
    """`unknown` is a valid recorded-score signal_type (a score with no routable instrument),
    so it lives in SIGNAL_TYPES; but it is not routable, so a route declaring it is checked
    against the narrower ROUTABLE_INSTRUMENTS and fails. Distinct from the `mystery` case: this
    value IS in the shared vocabulary and must still be rejected as a route instrument."""
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["routes"][0]["signal_type"] = "unknown"
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("signal_type" in e and "unknown" in e for e in errors), errors


def test_a_dangling_category_scope_is_an_error(routing, rubrics, categories):
    """`applies_to_categories: [does_not_exist]` names a category no file declares, so the scope
    would narrow the route to a category that cannot exist. Threaded the declared slugs into the
    compiler, an undeclared scope value is a hard error rather than a row nothing joins to."""
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["routes"][0]["applies_to_categories"] = ["does_not_exist"]
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("does_not_exist" in e and "category" in e for e in errors), errors


def test_a_sourced_route_with_no_column_is_an_error(routing, rubrics, categories):
    """A route WITH a non-null source must name a nonempty column; without one it compiled a
    route id like `huggingface_model.` and emitted no error. The source/column/hand_authored
    combination is now enforced, so the empty column is a hard error."""
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["routes"].append(
        {"source": "huggingface_model", "signal_type": "usage_volume", "authority": "authoritative"}
    )
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("huggingface_model." in e and "column" in e for e in errors), errors


# --- HARD ERRORS: a malformed aggregation block must fail the compiler --------------


def test_a_duplicate_aggregation_rule_id_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    rules = bad["dimensions"]["adoption"]["aggregation"]
    dup = copy.deepcopy(rules[0])
    dup["applies_to_instrument"] = "stars_fallback"  # a different instrument, so only the id collides
    rules.append(dup)
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("duplicate rule_id" in e for e in errors), errors


def test_an_empty_aggregation_rule_id_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["aggregation"][0]["rule_id"] = ""
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("no rule_id" in e for e in errors), errors


def test_an_unknown_aggregation_instrument_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["aggregation"][0]["applies_to_instrument"] = "mystery"
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("applies_to_instrument" in e and "mystery" in e for e in errors), errors


def test_an_unknown_aggregation_method_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["aggregation"][0]["method"] = "median"
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("method" in e and "median" in e for e in errors), errors


def test_an_unknown_aggregation_scope_is_an_error(routing, rubrics, categories):
    bad = copy.deepcopy(routing)
    bad["dimensions"]["adoption"]["aggregation"][0]["scope"] = "categories"
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("scope" in e and "categories" in e for e in errors), errors


def test_a_second_aggregation_rule_for_one_instrument_is_an_error(routing, rubrics, categories):
    """Two rules for usage_volume silently overwrote in the {instrument: rule_id} map and
    pointed every usage route at whichever came last."""
    bad = copy.deepcopy(routing)
    rules = bad["dimensions"]["adoption"]["aggregation"]
    second = copy.deepcopy(rules[0])
    second["rule_id"] = "max_usage_across_artifacts"
    second["method"] = "max"
    rules.append(second)
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("second rule for instrument 'usage_volume'" in e for e in errors), errors


def test_categories_is_a_required_argument(routing, rubrics):
    """`categories` has no default: a caller cannot skip the dangling-scope check by omitting
    it. Calling build_routing without categories is a TypeError, not a silent pass."""
    with pytest.raises(TypeError):
        build_routing(routing, rubrics)


def test_a_duplicate_category_scope_is_an_error(routing, rubrics, categories):
    """The table's grain is (route_id, scope_type, scope_value), so the same category listed
    twice on one route would publish two identical rows. That is a hard error, not a duplicate
    row. `benchmark_eval_data` is a real category, so only the duplicate — not a dangling
    reference — is what fails here."""
    bad = copy.deepcopy(routing)
    for route in bad["dimensions"]["adoption"]["routes"]:
        if route.get("signal_type") == "usage_volume":
            route["applies_to_categories"] = ["benchmark_eval_data", "benchmark_eval_data"]
            break
    _, errors, _ = build_routing(bad, rubrics, categories)
    assert any("duplicate applies_to_categories scope" in e for e in errors), errors
