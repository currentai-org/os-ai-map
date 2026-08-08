"""Tests for the capability comparison gates.

The two that carry the design are `test_relation_and_scores_can_disagree` and
`test_a_derived_band_cannot_be_fresher_than_what_it_derives_from`. The first is the whole
reason to record a comparison rather than write it in a note: two statements of the same fact
can drift, and only one of them was ever checkable. The second is the openness invariant's
shape applied to a different dependency — a date is worth no more than the least recently
confirmed thing underneath it.

`test_the_gate_ratchets` pins the property that let the openness gates land mid-corpus at all.
A product that records no comparison is not a failure; it is work not yet done, and a gate that
cannot tell those apart gets switched off.
"""

from datetime import date
from pathlib import Path

import pytest

from build.check_capability import candidates, check

CATS = {"a": "cat", "b": "cat", "c": "cat", "far": "other"}


def scores(**products) -> dict:
    out = {}
    for slug, block in products.items():
        out[slug] = {"product": slug, "capability": block}
    return out


def test_a_consistent_comparison_passes():
    data = scores(
        a={"score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below"},
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert check(data, CATS) == []


def test_relation_and_scores_can_disagree():
    """The producible-pair check's shape: a recorded relation is falsifiable arithmetic."""
    data = scores(
        a={"score": 3, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below"},
        b={"score": 5, "basis": "feature_matrix"},
    )
    problems = check(data, CATS)
    assert len(problems) == 1
    assert "which is 4" in problems[0] and "the score is 3" in problems[0]


@pytest.mark.parametrize(
    "relation,mine,ok",
    [("at", 5, True), ("at", 4, False), ("one_below", 4, True), ("two_below", 3, True), ("two_below", 4, False)],
)
def test_every_relation_is_arithmetic(relation, mine, ok):
    data = scores(
        a={"score": mine, "basis": "feature_matrix", "relative_to": "b", "relation": relation},
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert (check(data, CATS) == []) is ok


def test_one_above_works_when_the_anchor_leaves_room():
    """Real case: telemetry's operative anchor is a 4, and two products sit above it."""
    data = scores(
        a={"score": 5, "basis": "feature_matrix", "relative_to": "b", "relation": "one_above"},
        b={"score": 4, "basis": "feature_matrix"},
    )
    assert check(data, CATS) == []


def test_a_relation_no_band_could_satisfy_is_its_own_finding():
    data = scores(
        a={"score": 5, "basis": "feature_matrix", "relative_to": "b", "relation": "one_above"},
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert "no score satisfies it" in check(data, CATS)[0]


def test_a_derived_band_cannot_be_fresher_than_what_it_derives_from():
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 8),
        },
        b={"score": 5, "basis": "feature_matrix", "last_verified": date(2026, 6, 4)},
    )
    problems = check(data, CATS)
    assert len(problems) == 1
    assert "was last confirmed 2026-06-04" in problems[0]


def test_an_undated_anchor_cannot_support_a_dated_band():
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 8),
        },
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert "carries no confirmation at all" in check(data, CATS)[0]


def test_an_anchor_confirmed_the_same_day_is_fine():
    same = date(2026, 8, 8)
    data = scores(
        a={"score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below", "last_verified": same},
        b={"score": 5, "basis": "feature_matrix", "last_verified": same},
    )
    assert check(data, CATS) == []


def test_an_undated_band_needs_no_anchor_date():
    """Freshness is only a question once a confirmation is claimed."""
    data = scores(
        a={"score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below"},
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert check(data, CATS) == []


def test_a_comparison_must_stay_inside_the_category():
    data = scores(
        a={"score": 4, "basis": "feature_matrix", "relative_to": "far", "relation": "one_below"},
        far={"score": 5, "basis": "feature_matrix"},
    )
    assert "is in 'other', not 'cat'" in check(data, CATS)[0]


def test_a_missing_target_is_caught():
    data = scores(a={"score": 4, "basis": "feature_matrix", "relative_to": "ghost", "relation": "at"})
    assert "is not a product on the map" in check(data, CATS)[0]


def test_a_self_reference_is_caught():
    data = scores(a={"score": 4, "basis": "feature_matrix", "relative_to": "a", "relation": "at"})
    assert "points at itself" in check(data, CATS)[0]


def test_half_a_comparison_is_caught_here_too():
    """The schema also catches it. A gate that assumes another gate ran passes silently."""
    data = scores(a={"score": 4, "basis": "feature_matrix", "relative_to": "b"})
    assert "without the other" in check(data, CATS)[0]


def test_a_null_score_makes_the_relation_assert_nothing():
    data = scores(
        a={"score": None, "basis": "n/a", "relative_to": "b", "relation": "one_below"},
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert "asserts nothing" in check(data, CATS)[0]


def test_the_gate_ratchets():
    """No comparison recorded is work not yet done, not a failure."""
    data = scores(
        a={"score": 4, "basis": "feature_matrix", "note": "one tier below b, the anchor"},
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert check(data, CATS) == []


def test_candidates_finds_the_unrecorded_comparison():
    data = scores(
        a={"score": 4, "basis": "feature_matrix", "note": "One tier below b, the frontier anchor."},
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert candidates(data, CATS) == ["a:capability: note compares against b, unrecorded"]


def test_candidates_ignores_a_product_that_already_records_one():
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "note": "One tier below b, the frontier anchor.",
        },
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert candidates(data, CATS) == []


def test_candidates_ignores_a_peer_named_without_comparison():
    """Naming a product is not comparing to it. 'Built on b' is a fact about lineage."""
    data = scores(
        a={"score": 4, "basis": "feature_matrix", "note": "Built on b's scheduler."},
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert candidates(data, CATS) == []


def test_candidates_ignores_a_cross_category_mention():
    data = scores(
        a={"score": 4, "basis": "feature_matrix", "note": "One tier below far, the anchor."},
        far={"score": 5, "basis": "feature_matrix"},
    )
    assert candidates(data, CATS) == []


def test_the_real_corpus_holds():
    """Whatever is recorded today must be consistent. This is the gate, run for real."""
    from build.check_capability import load

    corpus, owner = load()
    assert check(corpus, owner) == []


def test_a_relation_outside_capability_is_rejected_by_the_schema():
    """A sweep run wrote `relation` onto openness and adoption on four axes. The fields are
    declared under capability only, but every axis had additionalProperties unset, so they
    validated silently and were read by nothing."""
    import json

    import jsonschema
    import yaml

    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "docs/schemas/score.schema.json").read_text())
    doc = yaml.safe_load((root / "sources/scores/trl.yaml").read_text())

    jsonschema.validate(doc, schema)
    for axis in ("openness", "adoption"):
        stray = yaml.safe_load((root / "sources/scores/trl.yaml").read_text())
        stray[axis]["relation"] = "at"
        with pytest.raises(jsonschema.ValidationError, match="Additional properties"):
            jsonschema.validate(stray, schema)
