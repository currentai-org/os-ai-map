"""The depth ladder as published: computed bands, the record gate, and the payload.

`build/depth_ladder.py` computes `language_specific_eval_sets`' capability bands; build/validate.py
holds each record to the computed band; build/serialize.py carries the companion figures, labels
adoption-only overall scores, and keeps an unresolved band out of the tier, `mature` and the stage
(R-2026-11-02-k, -o, R-2026-11-07-a, -b, R-2026-11-08-a, -b). docs/reference/capability.md,
"The depth ladder", is normative.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from build import depth_ladder as dl
from build import lineage
from build.depth_calibration import ROSTER
from build.serialize import _stage_and_gaps, build_payload
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]

UNRESOLVED = {
    "fleurs": "no_measurement_model",
    "lahaja": "no_measurement_model",
    "vmlu": "no_official_split",
    "darijammlu": "review_scope_unstated",
}

# Calibrated sets that a ruling has since moved out of the category, with their destination. The
# calibration roster stays the historical 22 (build/depth_calibration.py); membership moves only
# by a recorded ruling (R-2026-11-11-b: IndoNLU targets only Indonesian, which is high).
MOVED_OUT = {"indonlu": "benchmark_eval_data"}
CURRENT = tuple(slug for slug in ROSTER if slug not in MOVED_OUT)


@pytest.fixture(scope="module")
def doc():
    return lineage.load()


@pytest.fixture(scope="module")
def sources():
    return load_sources(ROOT)


@pytest.fixture(scope="module")
def payload(sources):
    long_tail = json.loads((ROOT / "sources/snapshots/long_tail.json").read_text())
    return build_payload(sources, long_tail, generated="test", version="0", released="test")


# --- the ladder ---------------------------------------------------------------------------------


def test_the_category_roster_is_the_calibrated_22_less_ruled_moves():
    """R-2026-11-07-b: the initial membership is the 22 calibrated sets, no more and no fewer.
    A set leaves only by a recorded membership ruling, which MOVED_OUT names."""
    assert set(MOVED_OUT) <= set(ROSTER)
    assert sorted(dl.category_roster()) == sorted(CURRENT)


@pytest.mark.parametrize("slug, reason", sorted(UNRESOLVED.items()))
def test_unresolved_sets_publish_null_with_their_reason(doc, slug, reason):
    r = dl.compute(doc, slug)
    assert (r["band"], r["status"], r["unresolved_reason"]) == (None, "unresolved", reason)
    assert r["best_original"] == "unavailable"


def test_resolved_sets_are_provisional_with_no_reason(doc):
    for slug in CURRENT:
        if slug in UNRESOLVED:
            continue
        r = dl.compute(doc, slug)
        assert r["status"] == "provisional" and r["unresolved_reason"] is None, slug
        assert isinstance(r["band"], int) and 1 <= r["band"] <= 5, slug


def test_the_cap_says_why_it_binds(doc):
    r = dl.compute(doc, "afrobench")
    assert r["cap"]["binds"] and r["cap"]["languages"] == 37
    aeb = r["cap"]["detail"]["aeb"]
    # Tunisian Arabic: its face value is FLORES+, and SIB-200, its only other evidence, shares
    # FLORES's text, so nothing independent backs it.
    assert aeb["face_component"] == "flores-plus"
    assert aeb["backing_component"] is None and "sib-200" in aeb["dependent"]


def test_absent_original_evidence_is_unavailable_not_zero(doc):
    """R-2026-11-02-o, D8: a set with no qualifying own items shows `unavailable`."""
    assert dl.compute(doc, "afrobench")["best_original"] == "unavailable"


# --- the record gate ----------------------------------------------------------------------------


def scores_for(slug):
    import yaml
    return {slug: yaml.safe_load((ROOT / "sources/scores" / f"{slug}.yaml").read_text())}


def test_every_record_matches_the_ladder(doc, sources):
    assert dl.ladder_errors(sources["scores"], dl.category_roster(), doc) == []


def test_a_drifted_band_fails(doc):
    scores = scores_for("thai-exam")
    scores["thai-exam"]["capability"]["score"] = 4
    errs = dl.ladder_errors(scores, ["thai-exam"], doc)
    assert any("records score 4, but the depth ladder computes 3" in e for e in errs)


def test_an_unresolved_set_may_not_keep_an_interim_score(doc):
    scores = scores_for("vmlu")
    scores["vmlu"]["capability"]["score"] = 4
    errs = dl.ladder_errors(scores, ["vmlu"], doc)
    assert any("computes None" in e and "no_official_split" in e for e in errs)


def test_the_basis_must_be_evaluation_depth(doc):
    scores = scores_for("thai-exam")
    scores["thai-exam"]["capability"]["basis"] = "feature_matrix"
    assert any("basis is 'feature_matrix'" in e for e in dl.ladder_errors(scores, ["thai-exam"], doc))


def test_a_computed_band_has_no_peer(doc):
    scores = scores_for("thai-exam")
    scores["thai-exam"]["capability"].update(relative_to="sea-helm", relation="one_below")
    assert any("drop relative_to" in e for e in dl.ladder_errors(scores, ["thai-exam"], doc))


# --- the payload --------------------------------------------------------------------------------


def rows(payload, cid="language_specific_eval_sets"):
    return {r["slug"]: r for r in payload["categories"][cid]["products"]}


def test_the_move_keeps_every_product_published_once(payload, sources):
    eval_rows, lsd_rows = rows(payload), rows(payload, "language_specific_datasets")
    assert set(eval_rows) == set(CURRENT)
    for slug, destination in MOVED_OUT.items():
        assert slug in rows(payload, destination), slug
    assert not set(eval_rows) & set(lsd_rows)
    everywhere = [r["slug"] for c in payload["categories"].values() for r in c["products"]]
    assert len(everywhere) == len(set(everywhere)) == payload["n_total"]


def test_a_set_moved_out_keeps_its_adoption_and_drops_the_depth_figures(payload, sources):
    """R-2026-11-11-b: IndoNLU publishes in benchmark_eval_data with its adoption (level 1) kept,
    capability not scored under that recipe, and no depth-ladder companion figures."""
    r = rows(payload, "benchmark_eval_data")["indonlu"]
    assert r["adoption"]["level"] == 1
    assert r["capability"]["score"] is None and r["capability"]["basis"] == "n/a"
    assert "depth" not in r["capability"]
    assert r["overall_basis"] == "adoption_only" and r["tier"] is None


def test_every_depth_row_carries_its_companion_figures(payload):
    for slug, r in rows(payload).items():
        depth = r["capability"]["depth"]
        assert set(depth) == {"status", "unresolved_reason", "unresolved_reason_text", "face_value",
                              "best_original", "task_count", "completeness", "cap",
                              "sensitivity"}, slug
        assert r["capability"]["basis"] == "evaluation_depth"


@pytest.mark.parametrize("slug", sorted(UNRESOLVED))
def test_an_unresolved_row_is_labeled_adoption_only_with_no_tier(payload, slug):
    r = rows(payload)[slug]
    assert r["capability"]["score"] is None
    assert r["overall_basis"] == "adoption_only"
    assert r["tier"] is None and r["mature"] is False
    assert r["capability"]["depth"]["unresolved_reason_text"]


def test_fleurs_adoption_alone_does_not_lift_the_stage(payload):
    """FLEURS is fully open with adoption 4 and no band. Counted on adoption alone it would be
    the category's best open product and lift the stage from 2 to 3 (R-2026-11-08-a)."""
    r = rows(payload)["fleurs"]
    assert r["openness"]["bucket"] == "open" and r["overall_score"] == 4.0
    assert payload["categories"]["language_specific_eval_sets"]["stage"]["num"] == 2


def test_an_unresolved_row_is_excluded_from_the_stage():
    w = {"adopt": 0.3, "cap": 0.7}
    weak = {"openness": {"class": "open"}, "adoption": {"level": 2},
            "capability": {"score": 2, "depth": {"status": "provisional"}}}
    unresolved = {"openness": {"class": "open"}, "adoption": {"level": 5},
                  "capability": {"score": None, "depth": {"status": "unresolved"}}}
    abstaining = {"openness": {"class": "open"}, "adoption": {"level": 5},
                  "capability": {"score": None}}
    alone = _stage_and_gaps([weak], w)
    assert _stage_and_gaps([weak, unresolved], w) == alone
    # A legacy abstention (no depth block) still counts on adoption alone, as before.
    assert _stage_and_gaps([weak, abstaining], w) != alone


def test_overall_basis_on_every_row(payload):
    for c in payload["categories"].values():
        for r in c["products"]:
            if r["overall_score"] is None:
                assert r["overall_basis"] is None
            elif r["capability"].get("score") is None:
                assert r["overall_basis"] == "adoption_only"
            else:
                assert r["overall_basis"] == "adoption_and_capability"
    assert set(payload["descriptions"]["overall_basis"]) == {"adoption_and_capability",
                                                           "adoption_only"}


# --- stage counting in the migrated category ----------------------------------------------------


def stage_with(sources, part_of: dict[str, list[str]]):
    """Build the payload with four open eval sets made mature, and the given suite edges."""
    src = copy.deepcopy(sources)
    for slug in ("afrobench", "belebele", "sib-200", "include-benchmark"):
        sc = src["scores"][slug]
        sc["openness"] = {**sc["openness"], "class": "open"}
        sc["adoption"] = {**sc["adoption"], "level": 5}
        sc["capability"] = {**sc["capability"], "score": 5}
    for member, suites in part_of.items():
        src["products"][member] = {**src["products"][member], "lineage": {"part_of": suites}}
    long_tail = json.loads((ROOT / "sources/snapshots/long_tail.json").read_text())
    pay = build_payload(src, long_tail, generated="test", version="0", released="test")
    return pay["categories"]["language_specific_eval_sets"]["stage"]["num"]


def test_four_mature_open_sets_reach_stage_5(sources):
    assert stage_with(sources, {}) == 5


def test_a_suite_and_its_members_count_once_in_the_migrated_category(sources):
    """The suite/member rule (R-2026-10-30-e) on the real roster: with Belebele and SIB-200
    declared members of AfroBench, the four mature rows are two units, so the stage is 4."""
    assert stage_with(sources, {"belebele": ["afrobench"], "sib-200": ["afrobench"]}) == 4


def test_a_suite_in_another_category_groups_nothing(sources):
    """An edge to a suite outside this roster does not group, so all four still count."""
    assert stage_with(sources, {"belebele": ["seacrowd"], "sib-200": ["seacrowd"]}) == 5
