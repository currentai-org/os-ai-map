"""Tests for the sweep's state, which is derived rather than stored.

`test_state_is_derived_not_stored` is the one that matters. A pointer file recording "we are on
category N" is a second copy of a fact the corpus already carries, and it desyncs the first time
someone finishes a category by hand. These assert the survey reads the corpus.
"""

from build.sweep_status import product_state, survey


def score(**axes) -> dict:
    base = {"openness": {"score": 5}, "adoption": {"level": 3}, "capability": {"score": 4}}
    for axis, extra in axes.items():
        base[axis] = {**base[axis], **extra}
    return base


VERIFIED = "Verified 2026-08-08 via the LICENSE body."


def test_a_product_is_done_when_every_axis_is_dated_and_the_prose_carries_the_line():
    state = product_state(
        "p", {"comments": VERIFIED},
        score(openness={"last_verified": "2026-08-08"},
              adoption={"last_verified": "2026-08-08"},
              capability={"last_verified": "2026-08-08"}),
        held={},
    )
    assert state["done"] is True
    assert set(state["axes"].values()) == {"verified"}


def test_a_dated_product_with_no_verification_line_is_not_done():
    """Prose is half the job. The canonical line is the one part a checker can see."""
    state = product_state(
        "p", {"comments": "Some note without the line."},
        score(openness={"last_verified": "2026-08-08"},
              adoption={"last_verified": "2026-08-08"},
              capability={"last_verified": "2026-08-08"}),
        held={},
    )
    assert state["done"] is False
    assert state["prose"] is False


def test_a_null_axis_abstains_rather_than_blocking():
    """46 axes are deliberately null - a hosted feature with no usage figure to band."""
    state = product_state(
        "p", {"comments": VERIFIED},
        score(openness={"last_verified": "2026-08-08"},
              adoption={"level": None},
              capability={"score": None}),
        held={},
    )
    assert state["axes"]["adoption"] == "abstained"
    assert state["done"] is True


def test_a_held_product_is_resolved_not_remaining():
    """One product whose evidence cannot be settled must not block its category."""
    state = product_state("p", {}, score(), held={"p": {"because": "..."}})
    assert state["held"] is True
    assert state["done"] is True


def test_an_undated_axis_is_open():
    state = product_state("p", {"comments": VERIFIED}, score(), held={})
    assert set(state["axes"].values()) == {"open"}
    assert state["done"] is False


def test_the_real_corpus_surveys_and_orders_worst_coverage_first():
    rows = survey()
    assert len(rows) == 16
    assert sum(r["products"] for r in rows) == 472
    pending = [r for r in rows if r["done"] < r["products"]]
    assert pending, "the sweep is not finished, so something must be pending"
    # Finished categories sort last whatever their coverage; among the rest, worst first.
    coverages = [r["coverage"] for r in rows if r["done"] < r["products"]]
    assert coverages == sorted(coverages), "pending categories must be worst-coverage first"
