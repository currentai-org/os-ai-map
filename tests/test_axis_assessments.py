"""`registry.axis_assessments` — the declaration-only, per-axis companion to `product_scores`.

`build/axis_assessments.py` unpivots the recorded scores into one row per
`(declaration_version_id, product_slug, category_slug, axis)`. It is a pure function of the
published roster, the recorded `sources/scores/`, the resolved rubrics, and the compiled routing, so
the golden pins it with a fixed test `declaration_version_id`/`source_git_sha`; the digest moves only
when those inputs change, never on an ordinary commit.
"""

import csv
import hashlib
import json
from pathlib import Path

import pytest

from build.axis_assessments import (
    AXES,
    COLUMNS,
    TABLES,
    _adoption_basis,
    _capability_basis,
    _openness_basis,
    _status,
    axis_assessments,
    canonical_row,
    load_inputs,
)

# Fixed test identities so the content digest is stable; the real ones are commit-scoped.
TEST_DVID = "test-declaration-version"
TEST_SHA = "test-git-sha"

AXIS_ROW_COUNT = 1581
AXIS_ASSESSMENTS_DIGEST = "4bb976a64f6b0a01dca3de0966bb899a25e175472792941fa9c30c2143c8ad4e"


@pytest.fixture(scope="module")
def inputs():
    return load_inputs()


@pytest.fixture(scope="module")
def rows(inputs):
    population, scores, held, variants, declared, routes, scopes = inputs
    return axis_assessments(
        population, scores, held, variants, declared, routes, scopes,
        declaration_version_id=TEST_DVID, source_git_sha=TEST_SHA,
    )


@pytest.fixture(scope="module")
def sources():
    from build.validate import load_sources
    return load_sources(Path(__file__).resolve().parents[1])


def _digest(rows) -> str:
    return hashlib.sha256("\n".join(sorted(canonical_row(r) for r in rows)).encode()).hexdigest()


def _score_block(**over) -> dict:
    base = {"score": 5, "class": "open_source", "components": {"license": [{"name": "MIT"}]},
            "confidence": "high", "last_verified": "2026-08-13",
            "sources": [{"url": "https://example.test"}]}
    base.update(over)
    return base


def _run(scores, held=None, *, population=None):
    """Run the builder over minimal synthetic inputs (no rubric/routing context needed)."""
    return axis_assessments(
        population or [("cat", "p", "software")], scores, held or {}, {}, {}, [], {},
        declaration_version_id=TEST_DVID, source_git_sha=TEST_SHA,
    )


# --- the pinned golden -----------------------------------------------------------


def test_reproduces_the_baseline_golden(rows):
    assert len(rows) == AXIS_ROW_COUNT
    assert _digest(rows) == AXIS_ASSESSMENTS_DIGEST


def test_keys_on_the_declaration_and_carries_no_release_id(rows):
    assert "release_id" not in COLUMNS
    assert "observation_snapshot_id" not in COLUMNS
    for row in rows:
        assert row["declaration_version_id"] == TEST_DVID
        assert row["source_git_sha"] == TEST_SHA


def test_three_axis_rows_per_published_category_product(rows):
    from collections import Counter

    by_pair = Counter((r["product_slug"], r["category_slug"]) for r in rows)
    assert set(by_pair.values()) == {3}
    assert {r["axis"] for r in rows} == set(AXES)


def test_grain_is_unique(rows):
    grain = [(r["product_slug"], r["category_slug"], r["axis"]) for r in rows]
    assert len(grain) == len(set(grain))


def test_matches_product_scores_population(rows):
    """The long form covers exactly the wide table's (product, category) rows — one owner of who is
    published, so the two tables cannot disagree."""
    from build.serialize import ROOT, build_payload
    from build.serialize_scores import build_scores
    from build.validate import load_sources

    frozen = json.load(open(ROOT / "sources" / "snapshots" / "long_tail.json"))
    payload = build_payload(load_sources(ROOT), frozen)
    wide = {(r["product_slug"], r["category_slug"]) for r in build_scores(payload)["product_scores"]}
    long = {(r["product_slug"], r["category_slug"]) for r in rows}
    assert long == wide


# --- status: confirmed / held, and not_applicable never emitted ------------------


def test_status_is_always_in_the_allowed_set(rows):
    """The allowed status set is the invariant — not that the queue happens to be empty today. A
    future verification hold is a valid repository state, so this must not pin all-confirmed."""
    assert {r["status"] for r in rows} <= {"confirmed", "held"}


def test_deliberate_dated_null_stays_confirmed(rows):
    nulls = [r for r in rows if r["recorded_value"] is None]
    assert nulls  # capability n/a and abstained adoption exist in the corpus
    for row in nulls:
        assert row["status"] == "confirmed" and row["last_verified"]


def test_every_confirmed_row_is_dated_and_sourced(rows):
    for row in rows:
        if row["status"] == "confirmed":
            assert row["last_verified"]
            assert row["source_count"] >= 1


# --- basis is axis-specific, transcribed from its one owner (real corpus) ---------


def test_openness_basis_is_the_ladders_resolved_license_tier(rows, sources):
    from build.check_rubric import components_string

    row = next(r for r in rows if r["product_slug"] == "accelerate" and r["axis"] == "openness")
    assert row["basis"] == "osi"
    assert row["basis_detail"] == components_string(sources["scores"]["accelerate"]["openness"])
    assert row["recorded_value"] == sources["scores"]["accelerate"]["openness"]["score"]
    assert row["recorded_class"] == sources["scores"]["accelerate"]["openness"]["class"]


def test_adoption_basis_is_the_declared_route_and_instrument_is_verbatim(rows, sources):
    row = next(r for r in rows if r["product_slug"] == "accelerate" and r["axis"] == "adoption")
    assert row["basis"] == "pypi.downloads_30d"
    assert row["instrument_type"] == sources["scores"]["accelerate"]["adoption"]["signal_type"]
    assert row["basis_detail"] == sources["scores"]["accelerate"]["adoption"].get("reach")


def test_adoption_with_no_applicable_route_abstains_rather_than_guess(rows):
    nulls = [r for r in rows if r["axis"] == "adoption" and r["recorded_value"] is None and r["basis"] is None]
    assert nulls, "expected at least one unroutable null adoption axis in the real corpus"


def test_capability_basis_is_the_recorded_field_verbatim(rows, sources):
    for row in rows:
        if row["axis"] == "capability":
            recorded = sources["scores"][row["product_slug"]].get("capability") or {}
            assert row["basis"] == recorded.get("basis")


def test_recorded_class_only_on_openness_and_instrument_only_on_adoption(rows):
    for row in rows:
        if row["axis"] == "openness":
            assert row["instrument_type"] is None
        elif row["axis"] == "adoption":
            assert row["recorded_class"] is None
        else:  # capability
            assert row["recorded_class"] is None and row["instrument_type"] is None


# --- the axis-specific basis helpers, directly -----------------------------------


def test_openness_basis_helper_returns_none_recipe_gracefully():
    basis, detail = _openness_basis(None, {"components": {"license": [{"name": "MIT", "detail": "OSI"}]}})
    assert basis is None
    assert detail == "license:MIT(OSI)"


def test_adoption_basis_helper_returns_none_when_nothing_applies():
    basis, detail = _adoption_basis("nobody", None, {}, {}, [], {})
    assert basis is None and detail is None


def test_capability_basis_helper_carries_the_anchor():
    assert _capability_basis({"basis": "benchmark"}) == ("benchmark", None)
    basis, detail = _capability_basis({"basis": "feature_matrix", "relative_to": "gpt-4", "relation": "peer"})
    assert basis == "feature_matrix"
    assert "relative_to=gpt-4" in detail and "relation=peer" in detail


# --- status internals, fail-closed (my strict contract) --------------------------


def test_status_confirmed_when_dated():
    assert _status("p", "openness", {"last_verified": "2026-08-01"}, {}) == ("confirmed", "2026-08-01", None, None)


def test_status_held_with_its_queue_reason_when_undated_and_queued():
    lookup = {("p", "adoption"): {"axis": "adoption", "reason": "evidence contradicts", "since": "2026-08-09"}}
    assert _status("p", "adoption", {}, lookup) == ("held", None, "evidence contradicts", "2026-08-09")


def test_status_undated_and_not_queued_fails_closed():
    with pytest.raises(ValueError, match="no last_verified"):
        _status("p", "capability", {}, {})


# --- the builder fails closed on every contract breach ---------------------------


def test_held_axis_is_undated_and_carries_reason_and_since():
    scores = {"p": {"openness": _score_block(last_verified=None)}}
    held = {"p": [{"axis": "openness", "since": "2026-08-01", "reason": "awaiting upstream license"}]}
    (row,) = _run(scores, held)
    assert row["status"] == "held" and row["last_verified"] is None
    assert row["hold_reason"] == "awaiting upstream license" and row["held_since"] == "2026-08-01"


def test_held_axis_with_a_confirmation_date_fails_closed():
    scores = {"p": {"openness": _score_block(last_verified="2026-08-13")}}
    held = {"p": [{"axis": "openness", "since": "2026-08-01", "reason": "r"}]}
    with pytest.raises(ValueError, match="held.*not confirmed"):
        _run(scores, held)


def test_held_axis_without_reason_fails_closed():
    scores = {"p": {"openness": _score_block(last_verified=None)}}
    held = {"p": [{"axis": "openness", "since": "2026-08-01"}]}  # no reason
    with pytest.raises(ValueError, match="hold_reason or held_since"):
        _run(scores, held)


def test_confirmed_axis_without_a_date_fails_closed():
    with pytest.raises(ValueError, match="no last_verified"):
        _run({"p": {"openness": _score_block(last_verified=None)}})


def test_confirmed_axis_without_a_source_fails_closed():
    with pytest.raises(ValueError, match="cites no sources"):
        _run({"p": {"openness": _score_block(sources=[])}})


def test_confirmed_axis_without_confidence_fails_closed():
    """§4.4 requires a confidence for a confirmed axis; the source schema describes it but does not
    require it, so a dated, sourced-but-unconfident assessment must not pass silently."""
    with pytest.raises(ValueError, match="confidence"):
        _run({"p": {"openness": _score_block(confidence=None)}})


def test_confirmed_axis_with_invalid_confidence_fails_closed():
    with pytest.raises(ValueError, match="confidence"):
        _run({"p": {"openness": _score_block(confidence="maybe")}})


def test_held_axis_does_not_require_confidence():
    """The confidence contract is on confirmed only; a held axis carries a reason, not a confidence."""
    scores = {"p": {"openness": _score_block(last_verified=None, confidence=None)}}
    held = {"p": [{"axis": "openness", "since": "2026-08-01", "reason": "awaiting license"}]}
    (row,) = _run(scores, held)
    assert row["status"] == "held" and row["confidence"] is None


# --- serialization: CSV shape matches COLUMNS ------------------------------------


def test_columns_and_tables_spec_agree():
    assert TABLES == {"axis_assessments": COLUMNS}


def test_canonical_row_emits_exactly_the_declared_columns(rows):
    assert set(json.loads(canonical_row(rows[0]))) == set(COLUMNS)


def test_csv_round_trip_header_matches_columns(rows, tmp_path):
    from build.serialize_registry import write_tables

    write_tables({"axis_assessments": rows[:5]}, tmp_path, TABLES)
    with (tmp_path / "axis_assessments.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(COLUMNS)
        assert len(list(reader)) == 5
