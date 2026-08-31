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

from build.check_capability import candidates, check, stale_attestations

CATS = {"a": "cat", "b": "cat", "c": "cat", "far": "other"}


def attestation(attested, accessed=None, **overrides) -> dict:
    """A well-formed comparison block, so a test can spoil exactly one thing."""
    source = {
        "url": "https://github.com/example/b",
        "shows": "the parallelism claim the band rests on",
        "accessed": accessed or attested,
        "http_status": 200,
        "content_sha256": "0" * 64,
    }
    source.update(overrides)
    return {"last_attested": attested, "sources": [source]}


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


# --- the attestation on the comparison edge (#436) -------------------------------------------
#
# One row per state in the design's semantics table. The row that is not here is the one above:
# a comparison with no attestation block stays on the old rule, and
# `test_a_derived_band_cannot_be_fresher_than_what_it_derives_from` pins it unchanged.


def test_an_attested_comparison_frees_the_band_from_the_roots_axis_date():
    """The unlock. The root's whole-axis date no longer bounds the dependent's."""
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 31),
            "comparison": attestation(date(2026, 8, 31)),
        },
        b={"score": 5, "basis": "feature_matrix", "last_verified": date(2026, 8, 13)},
    )
    assert check(data, CATS) == []


def test_a_whole_axis_date_cannot_outrun_the_attestation_it_contains():
    """`relative_to`/`relation` are part of the axis's score, so the part dates the whole."""
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 31),
            "comparison": attestation(date(2026, 8, 20)),
        },
        b={"score": 5, "basis": "feature_matrix", "last_verified": date(2026, 8, 31)},
    )
    problems = check(data, CATS)
    assert len(problems) == 1
    assert "attested 2026-08-20" in problems[0]


def test_an_attestation_needs_a_source_read_on_or_after_the_date_it_claims():
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 20),
            "comparison": attestation(date(2026, 8, 31), accessed=date(2026, 8, 20)),
        },
        b={"score": 5, "basis": "feature_matrix", "last_verified": date(2026, 8, 13)},
    )
    problems = check(data, CATS)
    assert len(problems) == 1
    assert "no attestation source was read on or after" in problems[0]


@pytest.mark.parametrize("missing", ["http_status", "content_sha256"])
def test_the_source_that_carries_the_date_must_carry_a_fetch(missing):
    """Without this the first pass under pressure attests off the repo's own recorded value."""
    block = attestation(date(2026, 8, 31))
    del block["sources"][0][missing]
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 31), "comparison": block,
        },
        b={"score": 5, "basis": "feature_matrix", "last_verified": date(2026, 8, 13)},
    )
    problems = check(data, CATS)
    assert len(problems) == 1
    assert missing in problems[0]


def test_an_uncovering_source_may_be_thin_as_long_as_one_covering_source_is_not():
    """The requirement is on the source that carries the date, not on every citation."""
    block = attestation(date(2026, 8, 31))
    block["sources"].append(
        {"url": "https://example.com/older", "shows": "context", "accessed": date(2026, 8, 1)}
    )
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 31), "comparison": block,
        },
        b={"score": 5, "basis": "feature_matrix", "last_verified": date(2026, 8, 13)},
    )
    assert check(data, CATS) == []


def test_a_root_re_read_since_the_spacing_was_judged_is_reported_not_failed():
    """The root's `value` can move without its score moving, and the arithmetic will not see it."""
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 20),
            "comparison": attestation(date(2026, 8, 20)),
        },
        b={"score": 5, "basis": "feature_matrix", "last_verified": date(2026, 8, 31)},
    )
    assert check(data, CATS) == []
    assert stale_attestations(data) == [("a", "b", date(2026, 8, 20), date(2026, 8, 31))]


def test_an_attestation_the_root_has_not_outrun_is_not_in_the_queue():
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 31),
            "comparison": attestation(date(2026, 8, 31)),
        },
        b={"score": 5, "basis": "feature_matrix", "last_verified": date(2026, 8, 13)},
    )
    assert stale_attestations(data) == []


def test_an_undated_attestation_is_caught_here_too():
    """The schema requires `last_attested`. A gate that assumes another gate ran passes silently."""
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "last_verified": date(2026, 8, 31),
            "comparison": {"sources": [{"url": "https://example.com", "shows": "x"}]},
        },
        b={"score": 5, "basis": "feature_matrix", "last_verified": date(2026, 8, 13)},
    )
    assert "no last_attested" in check(data, CATS)[0]


def test_an_undated_band_with_an_attestation_still_needs_the_attestation_to_hold():
    """The escape hatch for an undated axis does not extend to the edge's own record."""
    data = scores(
        a={
            "score": 4, "basis": "feature_matrix", "relative_to": "b", "relation": "one_below",
            "comparison": attestation(date(2026, 8, 31), accessed=date(2026, 8, 1)),
        },
        b={"score": 5, "basis": "feature_matrix"},
    )
    assert "no attestation source was read on or after" in check(data, CATS)[0]


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


def test_an_attestation_without_the_comparison_it_attests_to_is_rejected_by_the_schema():
    """`comparison` dates a spacing, so it says nothing without the pointers that name one."""
    import json

    import jsonschema
    import yaml

    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "docs/schemas/score.schema.json").read_text())
    doc = yaml.safe_load((root / "sources/scores/trl.yaml").read_text())
    doc["capability"].pop("relative_to", None)
    doc["capability"].pop("relation", None)
    doc["capability"]["comparison"] = {
        "last_attested": "2026-08-31",
        "sources": [
            {
                "url": "https://example.com/root",
                "shows": "the discriminator still reads as recorded",
                "accessed": "2026-08-31",
                "http_status": 200,
                "content_sha256": "0" * 64,
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, schema)
