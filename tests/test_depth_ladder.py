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
    # Five of its 64 target languages are unmeasured, enough to move the median between 1 and 3.
    "afrobench": "evidence_incomplete",
    "naijarc": "provenance_unknown",
}
# An unresolved set whose own components qualify in some languages: AfroBench's AfriADR counts in
# Ghomala, Fon and Wolof, so its best original band is itself unresolved rather than unavailable.
UNRESOLVED_OWN = {"afrobench": "unresolved (0-5)"}

# Calibrated sets that a ruling has since moved out of the category, with their destination, and
# sets a ruling has since added, with the ruling. The calibration roster stays the historical 22
# (build/depth_calibration.py); membership moves only by a recorded ruling (R-2026-11-11-b: IndoNLU
# targets only Indonesian, which is high; R-2026-11-11-e: KMMLU targets Korean, which is mid;
# R-2026-11-17-a: IN22 and IndicIFEval target Indic languages below the line).
MOVED_OUT = {"indonlu": "benchmark_eval_data"}
ADDED = {"kmmlu": "R-2026-11-11-e", "in22": "R-2026-11-17-a", "indicifeval": "R-2026-11-17-a",
         # SEA-HELM's independently published members, each with a row linked to the suite
         # (R-2026-11-18-a; #993). Each targets languages below the line.
         "kalahi": "R-2026-11-18-a", "lindsea": "R-2026-11-18-a", "sea-ifeval": "R-2026-11-18-a",
         "sea-mtbench": "R-2026-11-18-a",
         # AfroBench's independently published members, each with a row linked to the suite
         # (R-2026-11-18-d, the per-suite ruling under R-2026-11-18-a; #1098). Each targets
         # languages below the line.
         "afrimmlu": "R-2026-11-18-d", "afrixnli": "R-2026-11-18-d", "afrimgsm": "R-2026-11-18-d",
         "injongo-intent": "R-2026-11-18-d", "uhura-arc-easy": "R-2026-11-18-d",
         "naijarc": "R-2026-11-18-d"}
CURRENT = tuple(slug for slug in ROSTER if slug not in MOVED_OUT) + tuple(ADDED)


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


def test_the_category_roster_is_the_calibrated_22_with_ruled_moves():
    """R-2026-11-07-b: the initial membership is the 22 calibrated sets, no more and no fewer.
    A set leaves or joins only by a recorded membership ruling, which MOVED_OUT and ADDED name."""
    assert set(MOVED_OUT) <= set(ROSTER)
    assert not set(ADDED) & set(ROSTER)
    log = (ROOT / "docs/rulings/log.yaml").read_text()
    for ruling in ADDED.values():
        assert f"id: {ruling}\n" in log, ruling
    assert sorted(dl.category_roster()) == sorted(CURRENT)


@pytest.mark.parametrize("slug, reason", sorted(UNRESOLVED.items()))
def test_unresolved_sets_publish_null_with_their_reason(doc, slug, reason):
    r = dl.compute(doc, slug)
    assert (r["band"], r["status"], r["unresolved_reason"]) == (None, "unresolved", reason)
    assert r["best_original"] == UNRESOLVED_OWN.get(slug, "unavailable")


def test_resolved_sets_are_provisional_with_no_reason(doc):
    for slug in CURRENT:
        if slug in UNRESOLVED:
            continue
        r = dl.compute(doc, slug)
        assert r["status"] == "provisional" and r["unresolved_reason"] is None, slug
        assert isinstance(r["band"], int) and 1 <= r["band"] <= 5, slug


def test_the_cap_says_why_it_binds(doc):
    r = dl.compute(doc, "afrobench")
    assert r["cap"]["binds"] and r["cap"]["languages"] == 29
    aeb = r["cap"]["detail"]["aeb"]
    # Tunisian Arabic: its face value is FLORES+, and SIB-200, its only other evidence, shares
    # FLORES's text, so nothing independent backs it.
    assert aeb["face_component"] == "flores-plus"
    assert aeb["backing_component"] is None and "sib-200" in aeb["dependent"]


def test_absent_original_evidence_is_unavailable_not_zero(doc):
    """R-2026-11-02-o, D8: a set with no qualifying own items shows `unavailable`."""
    assert dl.compute(doc, "darijammlu")["best_original"] == "unavailable"


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
                              "sensitivity", "per_language"}, slug
        assert r["capability"]["basis"] == "evaluation_depth"


# --- the per-language bands (#953) --------------------------------------------------------------


def _targets(sources, slug):
    """A set's target languages from the source records: `languages` less `pivot_languages`."""
    pivots = set(sources["scores"][slug]["capability"].get("pivot_languages") or [])
    return sorted(set(sources["products"][slug].get("languages") or []) - pivots)


def _reproduce(languages: dict) -> str | None:
    """The set band from published per-language bands, read as `set_band` reads a set: measured
    bands as they are, every unmeasured target language filled at 0 and at 5."""
    measured = [e["band"] for e in languages.values() if e["band"] is not None]
    return dl.set_band(measured, len(languages) - len(measured))


def test_the_per_language_bands_reproduce_every_recorded_band(payload, sources):
    """The acceptance check for #953: for every set on the roster, the per-language bands the
    payload publishes give back the band the score record states, exactly. A band that stands is
    that integer; one that does not (no evidence, or a median the unmeasured languages could move)
    is the record's null. Derived from the roster, so a set joining, leaving or moving band is
    checked the same way and nothing here names a band."""
    roster = dl.category_roster()
    published = rows(payload)
    assert roster and set(published) == set(roster)
    checked = 0
    for slug in roster:
        languages = published[slug]["capability"]["depth"]["per_language"]
        result = _reproduce(languages)
        implied = int(result) if result is not None and not result.startswith("unresolved") else None
        recorded = sources["scores"][slug]["capability"]["score"]
        assert implied == recorded, (slug, result, recorded)
        assert dl.band_from_languages(languages) == recorded, slug
        assert published[slug]["capability"]["score"] == recorded, slug
        checked += 1
    assert checked == len(roster)


def test_every_target_language_is_listed_and_an_unmeasured_one_is_explicit(payload, sources):
    """One entry per target language, measured or not (R-2026-11-01-a, -f): an unmeasured
    language is `band: null` with nothing else filled, never a missing key and never a zero."""
    for slug, r in rows(payload).items():
        depth = r["capability"]["depth"]
        languages = depth["per_language"]
        assert sorted(languages) == _targets(sources, slug), slug
        unmeasured = [code for code, e in languages.items() if e["band"] is None]
        assert len(languages) - len(unmeasured) == depth["completeness"]["measured"], slug
        assert len(languages) == depth["completeness"]["targets"], slug
        for code in unmeasured:
            assert languages[code] == {"band": None, "face_value": None, "best_original": None,
                                       "set_by": None, "tasks": []}, (slug, code)


def test_the_set_figures_are_the_medians_of_the_per_language_figures(payload):
    """The face value and the best original band beside the set band are the same median over
    the per-language figures, so the table explains every number the row publishes."""
    for slug, r in rows(payload).items():
        depth = r["capability"]["depth"]
        languages = depth["per_language"]
        measured = [e for e in languages.values() if e["band"] is not None]
        unknown = len(languages) - len(measured)
        assert depth["face_value"] == dl.set_band([e["face_value"] for e in measured], unknown), slug
        own = [e["best_original"] for e in measured if e["best_original"] != "unavailable"]
        expected = dl.set_band(own, len(languages) - len(own)) if own else "unavailable"
        assert depth["best_original"] == expected, slug
        assert depth["task_count"] == len({t for e in measured for t in e["tasks"]}), slug


def test_a_capped_language_shows_the_cap_in_its_own_figures(payload):
    """Every language the cap binds in has a corroborated band below its face value, and every
    language it does not bind in has the two equal."""
    for slug, r in rows(payload).items():
        depth = r["capability"]["depth"]
        capped = set(depth["cap"]["detail"])
        for code, e in depth["per_language"].items():
            if e["band"] is None:
                continue
            assert (e["band"] < e["face_value"]) == (code in capped), (slug, code)


def test_band_from_languages_reads_unmeasured_languages_as_set_band_does():
    one = lambda b: {"band": b}  # noqa: E731
    assert dl.band_from_languages({"aaa": one(3), "bbb": one(3), "ccc": one(1)}) == 3
    # One measured 5 and one unknown: filled at 0 the median is 2, at 5 it is 5, so it does not stand.
    assert dl.band_from_languages({"aaa": one(5), "bbb": one(None)}) is None
    # Enough measured agreement that the unknown cannot move the median.
    assert dl.band_from_languages({"aaa": one(4), "bbb": one(4), "ccc": one(4), "ddd": one(None)}) == 4
    # No evidence at all, and no languages at all.
    assert dl.band_from_languages({"aaa": one(None)}) is None
    assert dl.band_from_languages({}) is None


def test_the_site_table_carries_one_row_per_target_language(payload):
    """`capability_languages` in the Neon load is the per-language mapping at a queryable grain,
    and its bands reproduce each set's recorded band the same way."""
    from build.neon_schema import build_site_tables, product_ids

    ids = product_ids(payload)
    by_product: dict[int, dict] = {}
    for row in build_site_tables(payload)["capability_languages"]:
        by_product.setdefault(row["product_id"], {})[row["language"]] = row
    for slug, r in rows(payload).items():
        table = by_product[ids[slug]]
        assert sorted(table) == sorted(r["capability"]["depth"]["per_language"]), slug
        assert dl.band_from_languages(table) == r["capability"]["score"], slug
    assert set(by_product) == {ids[slug] for slug in rows(payload)}


def test_the_payload_gate_passes_the_built_payload_against_the_source_rosters(payload):
    """`build/check_payload.py` reads each set's target-language roster from `sources/` through
    `dl.set_targets`, and holds every measured language to band <= face value and best original
    band <= band. Every row of the payload built from the same sources passes all of it. (The
    in-test payload carries no freshness records, so the depth check is called row by row.)"""
    from build.check_payload import _check_depth_languages

    checked = 0
    for slug, r in rows(payload).items():
        _check_depth_languages(slug, r["capability"], dl.set_targets)
        checked += 1
    assert checked == len(dl.category_roster())


def test_the_payload_gate_fails_a_language_that_is_not_a_target(payload):
    """Rename one measured language to a well-formed code the set does not target. The count, the
    shape and the median are unchanged, so only the roster check sees it."""
    from build.check_payload import PayloadError, _check_depth_languages

    slug, r = next((slug, r) for slug, r in rows(payload).items()
                   if any(e["band"] is not None
                          for e in r["capability"]["depth"]["per_language"].values()))
    capability = copy.deepcopy(r["capability"])
    languages = capability["depth"]["per_language"]
    code = next(c for c, e in languages.items() if e["band"] is not None)
    stand_in = next(c for c in ("qaa", "qab", "qac") if c not in languages)
    languages[stand_in] = languages.pop(code)
    with pytest.raises(PayloadError, match="per_language keys are not its target languages"):
        _check_depth_languages(slug, capability, dl.set_targets)


def test_set_targets_is_the_roster_load_set_scores(sources):
    """The gate's roster and the ladder's are one derivation, not two copies."""
    for slug in dl.category_roster():
        assert dl.set_targets(slug) == dl.load_set(slug)["targets"], slug
        assert sorted(dl.set_targets(slug)) == _targets(sources, slug), slug


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
    """Build the payload with four open eval sets made mature, and the given suite edges.

    The four must have a band that stands: an unresolved row is left out of the stage whatever its
    recorded score. AfroBench was one of them until its band became unresolved on 2026-11-18, so
    FLORES+ takes its place."""
    src = copy.deepcopy(sources)
    for slug in ("flores-plus", "belebele", "sib-200", "include-benchmark"):
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
    declared members of FLORES+, the four mature rows are two units, so the stage is 4."""
    assert stage_with(sources, {"belebele": ["flores-plus"], "sib-200": ["flores-plus"]}) == 4


def test_a_suite_in_another_category_groups_nothing(sources):
    """An edge to a suite outside this roster does not group, so all four still count."""
    assert stage_with(sources, {"belebele": ["seacrowd"], "sib-200": ["seacrowd"]}) == 5
