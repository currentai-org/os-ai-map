"""`evaluation.axis_facts` / `axis_rule_matches` / `axis_results` — the repository-owned
scoring trace (§4.4, ADR-001).

`build/axis_scoring_trace.py` decomposes the openness ladder walk that `build/check_rubric.py`
already runs into three declaration-keyed tables. The goldens pin the three tables against the
committed corpus with fixed test identities; the digests move only when the declarations or the
ladder move, never on an ordinary commit. The invariants below are what make this a *trace* and
not a second scorer: every scored result reproduces the recorded score, and every value is the one
`check_rubric` produces.
"""

import csv
import hashlib
import json
from pathlib import Path

import pytest

from build.axis_scoring_trace import (
    AXIS,
    RESULT_COLUMNS,
    RULE_COLUMNS,
    FACT_COLUMNS,
    TABLES,
    canonical_row,
    evaluate,
    load_inputs,
)

ROOT = Path(__file__).resolve().parents[1]

# Fixed test identities so the content digests are stable; the real ones are commit-scoped.
TEST_DVID = "test-declaration-version"
TEST_SHA = "test-git-sha"

# Pinned goldens over the committed corpus. A change here is a change in the declarations or the
# ladder — regenerate deliberately, never to make a red test green.
GOLDEN = {
    # Regenerated 2026-09-01 for the Round 1 calibration tranche: 23 products added across
    # five categories (axis_results 553 -> 576), their recorded evidence entering the fact
    # and rule-match tables, and gsm8k's adoption re-band 4 -> 5 - the one pre-existing
    # result row that changed.
    "axis_facts": (2516, "7f0d341049a45e6137607e6bced23e61d9214371b008509498a2e3118a19226b"),
    "axis_rule_matches": (3063, "24ceca80ab5f92cdb6e6ff9bfe79a1e693f72f58a8d27b211ce2230626609688"),
    "axis_results": (576, "2fa24ff9f42c8799547d7fa1e2084505e98f201c42b9a5c441cc1a6a2e5fb653"),
}


@pytest.fixture(scope="module")
def inputs():
    return load_inputs()


@pytest.fixture(scope="module")
def tables(inputs):
    population, scores, variants, deferrals = inputs
    return evaluate(
        population, scores, variants, deferrals,
        declaration_version_id=TEST_DVID, source_git_sha=TEST_SHA,
    )


@pytest.fixture(scope="module")
def sources():
    from build.validate import load_sources
    return load_sources(ROOT)


def _digest(table, rows) -> str:
    return hashlib.sha256("\n".join(sorted(canonical_row(table, r) for r in rows)).encode()).hexdigest()


# --- the pinned goldens ----------------------------------------------------------


@pytest.mark.parametrize("table", sorted(TABLES))
def test_reproduces_the_baseline_golden(tables, table):
    count, digest = GOLDEN[table]
    assert len(tables[table]) == count
    assert _digest(table, tables[table]) == digest


# --- keys on the declaration alone -----------------------------------------------


@pytest.mark.parametrize("table", sorted(TABLES))
def test_keys_on_the_declaration_and_carries_no_release_id(tables, table):
    columns = TABLES[table]
    assert "release_id" not in columns
    assert "observation_snapshot_id" not in columns
    for row in tables[table]:
        assert row["declaration_version_id"] == TEST_DVID
        assert row["source_git_sha"] == TEST_SHA
        assert row["axis"] == AXIS  # openness is the only rule-walk axis today


def test_result_grain_is_unique_and_one_per_published_pair(tables):
    grain = [(r["product_slug"], r["category_slug"]) for r in tables["axis_results"]]
    assert len(grain) == len(set(grain))


def test_fact_grain_is_unique(tables):
    grain = [(r["product_slug"], r["category_slug"], r["axis"], r["dimension"], r["part_index"])
             for r in tables["axis_facts"]]
    assert len(grain) == len(set(grain))


def test_rule_grain_is_unique(tables):
    grain = [(r["product_slug"], r["category_slug"], r["axis"], r["rule_index"])
             for r in tables["axis_rule_matches"]]
    assert len(grain) == len(set(grain))


def test_results_population_matches_product_scores(tables):
    """One owner of "who is published": the trace's result rows cover exactly the wide table's
    (product, category) rows, so the two cannot disagree about the roster."""
    from build.serialize import build_payload
    from build.serialize_scores import build_scores
    from build.validate import load_sources

    frozen = json.load(open(ROOT / "sources" / "snapshots" / "long_tail.json"))
    payload = build_payload(load_sources(ROOT), frozen)
    wide = {(r["product_slug"], r["category_slug"]) for r in build_scores(payload)["product_scores"]}
    got = {(r["product_slug"], r["category_slug"]) for r in tables["axis_results"]}
    assert got == wide


# --- the trace is a trace, not a second scorer -----------------------------------


def test_every_scored_result_reproduces_the_recorded_score(tables):
    """ADR-001's dual-run agreement, made queryable. The repo evaluator must agree with the
    recorded score on every product it scores — the same property `check_rubric` gates in CI."""
    scored = [r for r in tables["axis_results"] if r["status"] == "scored"]
    assert scored
    for row in scored:
        assert row["reproduces_recorded"] is True, row["product_slug"]
        assert (row["result_score"], row["result_class"]) == (row["recorded_score"], row["recorded_class"])


def test_result_matches_check_rubric_score_openness(inputs, sources):
    """No second implementation: the trace's result is byte-for-byte `score_openness`'s."""
    from build.check_rubric import score_openness
    from build.rubrics import recipe_for

    _population, scores, variants, _deferrals = inputs
    checked = 0
    for row in [r for r in _results(inputs) if r["status"] in ("scored", "undecided", "blocked_on_tier")]:
        variant = variants.get(row["category_slug"]) or {}
        recipe = recipe_for(variant, row["product_type"])[0]
        openness = (scores.get(row["product_slug"]) or {}).get("openness") or {}
        expected = score_openness(recipe, openness).result
        got = (row["result_score"], row["result_class"]) if row["result_score"] is not None else None
        assert got == expected, row["product_slug"]
        checked += 1
    assert checked > 400


def test_matched_rule_index_agrees_across_results_and_rule_matches(tables):
    """result -> matched rule: the rule the result names is exactly the rung that fired."""
    fired = {(r["product_slug"], r["category_slug"]): r["rule_index"]
             for r in tables["axis_rule_matches"] if r["matched"]}
    for row in tables["axis_results"]:
        key = (row["product_slug"], row["category_slug"])
        if row["status"] == "scored":
            assert fired.get(key) == row["matched_rule_index"]
        else:
            assert key not in fired  # nothing fired for a non-scored product


def test_matched_rule_conditions_join_to_facts(tables):
    """matched rule -> normalized fact: every condition the firing rung tests is a dimension that
    appears in the product's facts, so the join that explains "why this rule fired" is total."""
    facts_by_pair: dict[tuple, set[str]] = {}
    for row in tables["axis_facts"]:
        facts_by_pair.setdefault((row["product_slug"], row["category_slug"]), set()).add(row["dimension"])
    for row in tables["axis_rule_matches"]:
        if not row["matched"] or not row["rule_conditions"]:
            continue
        dims = facts_by_pair.get((row["product_slug"], row["category_slug"]), set())
        for clause in row["rule_conditions"].split(";"):
            key = clause.split("=", 1)[0]
            assert key in dims, f"{row['product_slug']}: rule condition {key} has no fact row"
        if row["tests_license_tier"]:
            assert "license_tier" in dims


def test_facts_join_to_recorded_evidence(tables):
    """normalized fact -> recorded evidence: a fact read under a recorded key resolves to a
    `registry.product_openness_evidence` row on the natural (product, category, dimension) key —
    the hop these tables leave to its existing owner rather than republish."""
    from build.rubrics import load_product_types
    from build.serialize_rubric import build_rubric, load_policy, load_routing
    from build.validate import load_sources

    src = load_sources(ROOT)
    src["product_types"] = load_product_types(ROOT)  # threaded the way serialize_rubric.main() does
    rubric = build_rubric(src, load_policy(ROOT), load_routing(ROOT))[0]
    evidence = {
        (r["product_slug"], r["category_slug"], r["dimension"], r["part_index"])
        for r in rubric["product_openness_evidence"]
    }
    # A dimension fact answered by a recorded key must have its evidence row; the license parts
    # (dimension "license") likewise. The synthetic "license_tier" aggregate has no evidence row —
    # it is the evaluator's derived fact — so it is excluded.
    checked = 0
    for row in tables["axis_facts"]:
        if row["fact_kind"] == "license_tier":
            continue
        if row["fact_kind"] == "dimension" and row["recorded_key"] is None:
            continue  # an unanswered dimension has no recorded evidence, by design
        key = (row["product_slug"], row["category_slug"], row["dimension"], row["part_index"])
        assert key in evidence, f"no recorded-evidence row for {key}"
        checked += 1
    assert checked > 1000


# --- fact-kind and status vocabularies -------------------------------------------


def test_fact_kinds_are_in_the_declared_set(tables):
    assert {r["fact_kind"] for r in tables["axis_facts"]} <= {"dimension", "license_part", "license_tier"}


def test_rule_outcomes_are_in_the_declared_set(tables):
    assert {r["outcome"] for r in tables["axis_rule_matches"]} <= {
        "fired", "skipped", "fell_through_tier", "blocked_on_tier",
    }


def test_statuses_are_in_the_declared_set(tables):
    assert {r["status"] for r in tables["axis_results"]} <= {
        "scored", "undecided", "blocked_on_tier", "deferred", "no_recipe",
    }


def test_exactly_one_fired_rung_per_scored_product(tables):
    from collections import Counter

    fired = Counter((r["product_slug"], r["category_slug"])
                    for r in tables["axis_rule_matches"] if r["matched"])
    scored = {(r["product_slug"], r["category_slug"]) for r in tables["axis_results"] if r["status"] == "scored"}
    assert set(fired) == scored
    assert set(fired.values()) == {1}


def test_deferred_products_emit_a_result_only(tables):
    """A recipe declining a product is not scoring it: a result row with a reason, and no fact or
    rule rows to imply a walk that did not run."""
    deferred = [(r["product_slug"], r["category_slug"]) for r in tables["axis_results"]
                if r["status"] == "deferred"]
    assert deferred
    fact_pairs = {(r["product_slug"], r["category_slug"]) for r in tables["axis_facts"]}
    rule_pairs = {(r["product_slug"], r["category_slug"]) for r in tables["axis_rule_matches"]}
    for pair in deferred:
        assert pair not in fact_pairs and pair not in rule_pairs
    for row in tables["axis_results"]:
        if row["status"] == "deferred":
            assert row["deferral_reason"] and row["result_score"] is None


def test_a_compound_license_publishes_every_part(tables, sources):
    """flan-collection records `Apache-2.0(recipe)+per-task`; the trace keeps both parts and the
    governing tier, the same decomposition `check_rubric.license_tier` reduces to one cap."""
    parts = [r for r in tables["axis_facts"]
             if r["product_slug"] == "flan-collection" and r["fact_kind"] == "license_part"]
    assert len(parts) == 2
    assert {r["normalized_value"] for r in parts} == {"open_data", "deferred_to_components"}
    agg = next(r for r in tables["axis_facts"]
               if r["product_slug"] == "flan-collection" and r["fact_kind"] == "license_tier")
    assert agg["normalized_value"] == "deferred_to_components"  # the most restrictive part governs


# --- the pure evaluator, synthetic edge cases ------------------------------------


SOFTWARE_RECIPE = {
    "openness": {
        "dimensions": {"source": {"values": ["public", "closed"]}},
        "license_tier": {"values": {"osi": {"examples": ["MIT"]}}},
        "formula": [
            {"when": {"source": "closed"}, "then": {"score": 1, "class": "closed"}},
            {"when": {"source": "public", "license_tier": "osi"}, "then": {"score": 5, "class": "open_source"}},
        ],
    }
}


def _eval_one(scores, variants=None, deferrals=None, product_type="software"):
    return evaluate(
        [("cat", "p", product_type)], scores, variants or {"cat": {"*": SOFTWARE_RECIPE}},
        deferrals or {}, declaration_version_id=TEST_DVID, source_git_sha=TEST_SHA,
    )


def test_scored_product_emits_facts_rules_and_a_result():
    scores = {"p": {"openness": {"score": 5, "class": "open_source",
                                 "components": {"source": {"value": "public"}, "license": [{"name": "MIT"}]}}}}
    out = _eval_one(scores)
    (result,) = out["axis_results"]
    assert result["status"] == "scored" and result["reproduces_recorded"] is True
    assert result["matched_rule_index"] == 1 and result["license_tier"] == "osi"
    assert out["axis_rule_matches"][-1]["matched"] and out["axis_rule_matches"][-1]["outcome"] == "fired"
    assert {r["fact_kind"] for r in out["axis_facts"]} == {"dimension", "license_part", "license_tier"}


def test_undecided_product_when_no_rung_fires_and_no_otherwise():
    scores = {"p": {"openness": {"score": 3, "class": "x",
                                 "components": {"source": {"value": "partial"}, "license": [{"name": "MIT"}]}}}}
    (result,) = _eval_one(scores)["axis_results"]
    assert result["status"] == "undecided" and result["result_score"] is None
    assert result["reproduces_recorded"] is None


def test_blocked_on_tier_when_a_reached_rung_needs_an_unmapped_license():
    scores = {"p": {"openness": {"score": 5, "class": "open_source",
                                 "components": {"source": {"value": "public"},
                                                "license": [{"name": "Some-Unknown-License"}]}}}}
    (result,) = _eval_one(scores)["axis_results"]
    assert result["status"] == "blocked_on_tier" and result["license_tier"] is None


def test_deferred_product_is_declined_by_the_recipe():
    scores = {"p": {"openness": {"score": 5, "class": "open_source",
                                 "components": {"source": {"value": "public"}, "license": [{"name": "MIT"}]}}}}
    out = _eval_one(scores, deferrals={"cat": {"p": {"because": "held for #42"}}})
    (result,) = out["axis_results"]
    assert result["status"] == "deferred" and result["deferral_reason"] == "held for #42"
    assert out["axis_facts"] == [] and out["axis_rule_matches"] == []


def test_no_recipe_when_the_category_has_no_ladder_for_the_type():
    scores = {"p": {"openness": {"score": 5, "class": "open_source"}}}
    out = _eval_one(scores, variants={"cat": {}})
    (result,) = out["axis_results"]
    assert result["status"] == "no_recipe" and result["result_score"] is None
    assert out["axis_facts"] == [] and out["axis_rule_matches"] == []


def test_fell_through_tier_step_is_recorded():
    """A rung whose non-tier conditions match but whose tier differs is part of the honest walk."""
    recipe = {"openness": {
        "dimensions": {"source": {"values": ["public"]}},
        "license_tier": {"values": {"osi": {"examples": ["MIT"]},
                                    "noncommercial": {"examples": ["CC-BY-NC"]}}},
        "formula": [
            {"when": {"source": "public", "license_tier": "noncommercial"}, "then": {"score": 2, "class": "restricted"}},
            {"when": {"source": "public", "license_tier": "osi"}, "then": {"score": 5, "class": "open_source"}},
        ],
    }}
    scores = {"p": {"openness": {"score": 5, "class": "open_source",
                                 "components": {"source": {"value": "public"}, "license": [{"name": "MIT"}]}}}}
    out = evaluate([("cat", "p", "software")], scores, {"cat": {"*": recipe}}, {},
                   declaration_version_id=TEST_DVID, source_git_sha=TEST_SHA)
    outcomes = [r["outcome"] for r in out["axis_rule_matches"]]
    assert outcomes == ["fell_through_tier", "fired"]


# --- serialization ----------------------------------------------------------------


def test_columns_and_tables_spec_agree():
    assert TABLES == {
        "axis_facts": FACT_COLUMNS,
        "axis_rule_matches": RULE_COLUMNS,
        "axis_results": RESULT_COLUMNS,
    }


@pytest.mark.parametrize("table", sorted(TABLES))
def test_canonical_row_emits_exactly_the_declared_columns(tables, table):
    assert set(json.loads(canonical_row(table, tables[table][0]))) == set(TABLES[table])


@pytest.mark.parametrize("table", sorted(TABLES))
def test_csv_round_trip_header_matches_columns(tables, table, tmp_path):
    from build.serialize_registry import write_tables

    write_tables({name: rows[:5] for name, rows in tables.items()}, tmp_path, TABLES)
    with (tmp_path / f"{table}.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(TABLES[table])
        assert len(list(reader)) == 5


def _results(inputs):
    population, scores, variants, deferrals = inputs
    return evaluate(population, scores, variants, deferrals,
                    declaration_version_id=TEST_DVID, source_git_sha=TEST_SHA)["axis_results"]
