"""The adoption routing compiler, and its acceptance test: round-trip completeness.

`build/serialize_routing.py` compiles `dimensions.adoption` from signal_routing.yaml into
`registry.adoption_routes`, `registry.adoption_route_scopes` and
`registry.adoption_aggregation_rules`, so evaluation reads normalized facts and never
reinterprets the YAML (AD-1).

The acceptance test (data-architecture.md 4.1) is NOT column presence but round-trip
completeness: every semantic field in the adoption portion of the YAML is either compiled
into these tables or explicitly classified documentation-only. A field that is neither must
fail here, so the next field added to a route cannot slip out of the warehouse unnoticed.
"""

from pathlib import Path

import pytest
import yaml

from build.serialize_routing import build_routing, load_routing
from build.serialize_rubric import adoption_bands, route_bands
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]

# Containers, not leaf fields. `routes` holds the routes iterated per-field; `question` is the
# dimension's prose prompt, classified with the other documentation below.
_STRUCTURAL = {"routes"}

# Semantic fields that MUST reach one of the three tables (or, for `bands`, the adoption_bands
# table that `band_set_id` links to). This is the list data-architecture.md 4.1 names as
# semantic, plus `bands`, which compiles in serialize_rubric and is referenced by band_set_id.
_COMPILED = {
    "source",
    "column",
    "signal_type",
    "confidence",
    "unit",
    "cap",
    "applies_to_categories",
    "hand_authored",
    "requires_evidence",
    "vocabulary",
    "sum_across_artifacts",
    "bands",
}

# Prose. Allowed to be absent from the tables; a reader consults the YAML for the reasoning.
_DOC_ONLY = {"note", "cap_because", "sum_note", "attribution_note", "vocabulary_note", "question"}


@pytest.fixture(scope="module")
def routing():
    return load_routing(ROOT)


@pytest.fixture(scope="module")
def adoption(routing):
    return routing["dimensions"]["adoption"]


@pytest.fixture(scope="module")
def tables(routing):
    tables, errors, _warnings = build_routing(routing)
    assert errors == [], errors
    return tables


def test_every_adoption_field_is_compiled_or_classified_documentation(adoption):
    """Round-trip completeness. A field that is neither compiled nor documentation-only fails.

    This is the check the spec calls the acceptance test: it is what makes the tables a
    faithful compilation of the YAML rather than a lossy subset that drifts as fields are added.
    """
    fields: set[str] = set()
    for route in adoption["routes"]:
        fields |= set(route)
    fields |= {k for k in adoption if k not in _STRUCTURAL}

    unclassified = fields - _COMPILED - _DOC_ONLY
    assert not unclassified, (
        f"adoption fields neither compiled nor classified documentation-only: {sorted(unclassified)}. "
        f"Compile the field into serialize_routing, or add it to _DOC_ONLY with a reason."
    )


def test_seven_routes_compile_to_seven_rows_in_contiguous_order(tables):
    rows = tables["adoption_routes"]
    assert len(rows) == 7
    assert [r["route_order"] for r in rows] == list(range(1, 8))


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

    # unit (active_users declares one), cap (stars caps at 3).
    assert by_instrument["active_users"]["unit"] == adoption["routes"][5]["unit"]
    assert by_instrument["stars_fallback"]["cap"] == 3

    # requires_evidence pipe-joined for the two hand-authored routes.
    assert by_instrument["active_users"]["requires_evidence"] == "accessed|content_sha256"
    assert by_instrument["reported_traction"]["requires_evidence"] == "accessed|content_sha256"

    # vocabulary on reported_traction only.
    assert by_instrument["reported_traction"]["vocabulary"] == "niche|broad|mass-market"

    # applies_to_categories -> a scope row; sum_across_artifacts -> the aggregation rule.
    assert {"route_id": "semanticscholar.citation_count", "scope_type": "category",
            "scope_value": "benchmark_eval_data"} in tables["adoption_route_scopes"]
    assert tables["adoption_aggregation_rules"] == [
        {"dimension": "adoption", "aggregation_method": "sum", "scope": "artifacts"}
    ]


def test_band_set_id_referential_integrity(routing, tables):
    """Every route band_set_id that names a scale must resolve to at least one adoption_bands
    row; the `type:*` and '' sentinels resolve to none by design.

    `type:*` says the bands are resolved per product type at evaluation, so no single row
    carries it; '' says the instrument has a vocabulary and no bands at all.
    """
    bands, _ = adoption_bands(load_sources(ROOT).get("rubrics") or {})
    route_scale_rows, _ = route_bands(routing)
    band_ids = {b["band_set_id"] for b in bands + route_scale_rows}

    for row in tables["adoption_routes"]:
        band_set = row["band_set_id"]
        if band_set in ("type:*", ""):
            continue
        assert band_set.startswith(("route:", "type:")), band_set
        assert band_set in band_ids, (
            f"route {row['route_id']!r} points at band_set_id {band_set!r}, which no "
            f"adoption_bands row carries"
        )

    # The sentinels really are sentinels: no band row is emitted under them.
    assert "type:*" not in band_ids
    assert "" not in band_ids


def test_source_null_routes_carry_no_derived_artifact_or_metric(tables):
    """A null-source, hand-authored route names no artifact and reads no column, so both
    derived fields are empty rather than a guessed default."""
    for row in tables["adoption_routes"]:
        if row["hand_authored"]:
            assert row["artifact_kind"] == ""
            assert row["metric_type"] == ""
