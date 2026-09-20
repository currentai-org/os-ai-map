"""Cover the closed-product survey in `build/closed_inclusion.py`.

**Nothing here asserts where the line falls on the real corpus, and nothing here can fail
because a product sits below it.** That is deliberate and it is the point of the whole job:
ADR-005 states a principle a curator applies, and a test that went red when a product scored
3.7 would turn it into a gate. The real-corpus tests below assert invariants — that the three
states partition the population, that every census row carries a rebuilt stage — and derive
every number they use. No count is pinned.

The one test that asserts a specific outcome does it on a synthetic corpus, and it exists to
prove the withheld-rebuild detector can fire at all. Without it, a census where nothing moved
would be indistinguishable from a census that never looked.
"""
import json

import pytest

from build.closed_inclusion import (ABOVE, BELOW, JUDGED_CAPABILITY, JUDGED_NOTHING,
                                    JUDGED_OVERALL, LINE, UNMEASURED, census, is_closed,
                                    load_inputs, main, screen, stage_and_gap_diff, survey,
                                    withheld)
from build.serialize import ROOT, build_payload


def _row(overall=None, capability=None, openness_score=1):
    return {"slug": "x", "product": "X", "openness": {"score": openness_score, "class": "closed"},
            "overall_score": overall, "capability": {"score": capability},
            "adoption": {"level": None}}


# --- the screen, on fabricated rows ----------------------------------------------------

def test_the_screen_reads_the_overall_score_first():
    assert screen(_row(overall=LINE)) == (ABOVE, JUDGED_OVERALL)
    assert screen(_row(overall=LINE - 0.1)) == (BELOW, JUDGED_OVERALL)
    # A present overall score is read even where capability would say the opposite: the
    # fallback exists for an abstention, not as a second chance.
    assert screen(_row(overall=LINE - 1, capability=5))[0] == BELOW


def test_a_null_overall_score_falls_through_to_capability():
    # A closed hosted API often has no public download channel to count, so adoption
    # abstains and the overall score is null. That is our instrument missing, not the
    # product being weak, which is why capability is read instead.
    assert screen(_row(capability=LINE)) == (ABOVE, JUDGED_CAPABILITY)
    assert screen(_row(capability=LINE - 1)) == (BELOW, JUDGED_CAPABILITY)


def test_unmeasured_is_its_own_state_and_not_a_kind_of_below():
    state, judged = screen(_row())
    assert state == UNMEASURED and judged == JUDGED_NOTHING
    assert state != BELOW


def test_the_population_is_the_openness_score_not_the_class_or_the_bucket():
    assert is_closed(_row(openness_score=1))
    assert is_closed(_row(openness_score=0))
    # `restricted` and `documented` land in the serializer's closed BUCKET but score above
    # the closed floor. ADR-005 governs the score, so they are outside the population.
    assert not is_closed({"openness": {"score": 2, "class": "restricted"}})
    # No score at all is not a licence to assume one.
    assert not is_closed({"openness": {"class": "closed"}})


# --- the withheld-rebuild detector, on a synthetic corpus ------------------------------

def _synthetic_sources():
    """One category with a feeble fully-open product and one category-leading closed one.

    `build/serialize.py` computes `mature_anywhere` over ALL products, so the closed product
    is what holds this category off Stage 0 and what fires the `openness` gap. Withholding it
    therefore has to move both — which is the claim "removing a non-leading closed product
    cannot move a stage" got wrong, and the reason the census measures instead of promising.
    """
    return {
        "organizations": {"o": {"name": "o", "display_name": "O", "type": "unknown",
                                "products": ["weak-open", "big-closed"]}},
        "taxonomy": {"arcs": [{"name": "Arc", "layer": "lyr", "categories": ["cat"]}]},
        "categories": {"cat": {"name": "cat", "display_name": "Cat",
                               "products": ["weak-open", "big-closed"],
                               "weights": {"adopt": 0.5, "cap": 0.5}, "comments": ""}},
        "products": {
            "weak-open": {"name": "weak-open", "display_name": "Weak Open", "type": "software",
                          "description": ""},
            "big-closed": {"name": "big-closed", "display_name": "Big Closed",
                           "type": "software", "description": ""},
        },
        "scores": {
            "weak-open": {"product": "weak-open",
                          "openness": {"score": 5, "class": "open_source"},
                          "adoption": {"level": 1, "signal_type": "usage_volume"},
                          "capability": {"score": 1, "basis": "n/a"}},
            "big-closed": {"product": "big-closed",
                           "openness": {"score": 1, "class": "closed"},
                           "adoption": {"level": 5, "signal_type": "reported_traction"},
                           "capability": {"score": 5, "basis": "n/a"}},
        },
    }


def test_the_withheld_rebuild_detects_a_move_when_there_is_one():
    src = _synthetic_sources()
    baseline = build_payload(src, frozen_long_tail={}, generated="1970-01-01")
    assert baseline["categories"]["cat"]["stage"]["num"] == 1
    assert "openness" in baseline["categories"]["cat"]["gaps"]

    with withheld(src, "big-closed"):
        rebuilt = build_payload(src, frozen_long_tail={}, generated="1970-01-01")
    moved = stage_and_gap_diff(baseline, rebuilt)
    assert "cat" in moved
    assert moved["cat"]["stage_before"]["num"] == 1 and moved["cat"]["stage_after"]["num"] == 0
    assert moved["cat"]["gaps_after"] == ["void"]


def test_a_census_row_over_the_synthetic_corpus_carries_the_rebuilt_numbers():
    src = _synthetic_sources()
    # Drop the closed product below the line so it reaches the census, without touching the
    # fact that it is the only category-leading product in the category.
    src["scores"]["big-closed"]["adoption"]["level"] = 1
    baseline = build_payload(src, frozen_long_tail={}, generated="1970-01-01")
    rows = census(src, {}, baseline=baseline)
    row = next(r for r in rows if r["slug"] == "big-closed")
    assert row["state"] == BELOW
    assert row["stage_with_product"] == baseline["categories"]["cat"]["stage"]
    assert row["stage_withheld"] is not None and row["gaps_withheld"] is not None
    assert "decision for Carl" in row["disposition"] or not row["withheld_moves"]


def test_withholding_restores_the_roster_even_when_the_block_raises():
    src = _synthetic_sources()
    before = list(src["categories"]["cat"]["products"])
    with pytest.raises(RuntimeError):
        with withheld(src, "big-closed"):
            assert "big-closed" not in src["categories"]["cat"]["products"]
            raise RuntimeError("boom")
    assert src["categories"]["cat"]["products"] == before


# --- the real corpus: invariants only --------------------------------------------------

@pytest.fixture(scope="module")
def corpus():
    sources, frozen = load_inputs()
    baseline = build_payload(sources, frozen, generated="1970-01-01")
    return sources, frozen, baseline


def test_the_three_states_partition_the_closed_population(corpus):
    _, _, baseline = corpus
    surveyed = survey(baseline)
    counts = surveyed["counts"]
    assert sum(counts.values()) == surveyed["population"]
    slugs = [r["slug"] for state in surveyed["states"].values() for _, r in state]
    assert len(slugs) == len(set(slugs)), "a product landed in more than one state"
    # The sub-counts have to reconstruct the states, or the report is describing a different
    # split from the one it just made.
    d = surveyed["detail"]
    assert d["scored_at_or_above_line"] + d["null_with_capability_at_or_above_line"] == counts[ABOVE]
    assert d["scored_below_line"] + d["null_with_capability_below_line"] == counts[BELOW]
    assert d["null_with_no_capability"] == counts[UNMEASURED]


def test_every_census_row_carries_a_stage_rebuilt_with_the_product_withheld(corpus):
    """The defect this guards is a row asserting 'no effect' without having rebuilt anything.

    Derived, not pinned: it walks whatever the census returns today, and it does **not**
    assert the census is non-empty. An earlier draft opened with a bare `assert rows`. That
    reads as a sanity check and is really a claim about where the corpus sits against the
    line -- it goes red on the day nothing is below the line, which is the day the principle
    has been fully acted on, and a test that goes red for that reason is the gate this job
    must not write. The census is checked against the survey it was drawn from instead,
    which holds at any count including zero.
    """
    sources, frozen, baseline = corpus
    rosters_before = {cid: list(cat["products"]) for cid, cat in sources["categories"].items()}
    surveyed = survey(baseline)
    rows = census(sources, frozen, baseline=baseline)
    # The census covers exactly the two non-above states, one row per placement. True at
    # 64 rows and true at 0.
    assert len(rows) == surveyed["counts"][BELOW] + surveyed["counts"][UNMEASURED]
    assert {(r["category"], r["slug"]) for r in rows} == {
        (cid, row["slug"]) for state in (BELOW, UNMEASURED)
        for cid, row in surveyed["states"][state]}
    for r in rows:
        assert r["stage_withheld"] is not None, r["slug"]
        assert isinstance(r["gaps_withheld"], list), r["slug"]
        assert isinstance(r["withheld_moves"], dict), r["slug"]
        assert r["stage_with_product"] == baseline["categories"][r["category"]]["stage"]
        # The row's own claim and its measured diff cannot disagree.
        differs = (r["stage_with_product"] != r["stage_withheld"]
                   or r["gaps_with_product"] != r["gaps_withheld"])
        assert differs == (r["category"] in r["withheld_moves"])
    # Withholding mutates the rosters and restores them. A lossy restore would leave the
    # survey measuring a corpus it had eaten, and every later row would be read off it.
    assert {cid: list(cat["products"])
            for cid, cat in sources["categories"].items()} == rosters_before


def test_the_survey_reports_and_never_signals_a_failure(capsys):
    """The exit code is the whole point: a principle that fails a build is a rule."""
    assert main([]) == 0
    report = capsys.readouterr().out
    for label in (ABOVE, BELOW, UNMEASURED):
        assert label in report
    assert "not a removal list" in report


def test_the_json_form_is_machine_readable(capsys):
    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["line"] == LINE
    assert set(payload["counts"]) == {ABOVE, BELOW, UNMEASURED}


def test_the_all_form_widens_the_census_and_says_so(capsys):
    """`--all` puts every closed product in the census, so the heading has to widen with it.

    Not a count assertion: it reads which population the heading claims, which is the part
    that can be wrong while every number under it is right.
    """
    assert main(["--all"]) == 0
    report = capsys.readouterr().out
    assert "the whole population" in report
    assert "products not above the line" not in report
    assert ABOVE in report


def test_the_survey_is_not_wired_into_any_gate():
    """No gate for any of the three tests — including by accident, later.

    `build/preflight.py` is the local gate chain and `.github/workflows/` is the CI one. A
    survey appearing in either would make the principle enforceable, which ADR-005 says it
    is not.
    """
    workflows = ROOT / ".github" / "workflows"
    surfaces = [ROOT / "build" / "preflight.py"] + sorted(
        list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml")))
    offenders = [str(p.relative_to(ROOT)) for p in surfaces
                 if "closed_inclusion" in p.read_text(encoding="utf-8")]
    assert not offenders, f"the survey is wired into a gate surface: {offenders}"
