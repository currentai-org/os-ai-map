"""Tests for the sweep's state, which is derived rather than stored.

`test_state_is_derived_not_stored` is the one that matters. A pointer file recording "we are on
category N" is a second copy of a fact the corpus already carries, and it desyncs the first time
someone finishes a category by hand. These assert the survey reads the corpus.
"""

from datetime import date

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


# --- the refresh window ---

def _dated(day: str) -> dict:
    return score(openness={"last_verified": day},
                 adoption={"last_verified": day},
                 capability={"last_verified": day})


def test_without_a_cutoff_any_confirmation_counts():
    state = product_state("p", {"comments": "Verified 2020-01-01 via GitHub."},
                          _dated("2020-01-01"), held={})
    assert state["done"] is True


def test_a_confirmation_older_than_the_window_is_stale_not_verified():
    """This is what turns the sweep from a one-time pass into a recurring refresh."""
    state = product_state("p", {"comments": "Verified 2026-06-01 via GitHub."},
                          _dated("2026-06-01"), held={}, cutoff=date(2026, 7, 1))
    assert set(state["axes"].values()) == {"stale"}
    assert state["done"] is False


def test_a_confirmation_on_the_cutoff_still_counts():
    state = product_state("p", {"comments": "Verified 2026-07-01 via GitHub."},
                          _dated("2026-07-01"), held={}, cutoff=date(2026, 7, 1))
    assert set(state["axes"].values()) == {"verified"}
    assert state["done"] is True


def test_a_never_confirmed_axis_is_open_not_stale():
    """Open and stale are different jobs: one has never been read, the other has aged."""
    state = product_state("p", {"comments": "Verified 2026-08-08 via GitHub."},
                          score(), held={}, cutoff=date(2026, 7, 1))
    assert set(state["axes"].values()) == {"open"}


def test_the_prose_ages_on_the_same_clock():
    """The canonical line carries its own date, so it can go stale without going missing."""
    fresh = product_state("p", {"comments": "Verified 2026-08-08 via GitHub."},
                          _dated("2026-08-08"), held={}, cutoff=date(2026, 7, 1))
    assert fresh["prose_state"] == "verified"

    aged = product_state("p", {"comments": "Verified 2026-06-01 via GitHub."},
                         _dated("2026-08-08"), held={}, cutoff=date(2026, 7, 1))
    assert aged["prose_state"] == "stale", "a dated line that has aged is stale, not missing"
    assert aged["done"] is False

    none = product_state("p", {"comments": "No line at all."},
                         _dated("2026-08-08"), held={}, cutoff=date(2026, 7, 1))
    assert none["prose_state"] == "missing"


def test_a_held_product_stays_resolved_under_any_window():
    state = product_state("p", {}, _dated("2020-01-01"), held={"p": {}}, cutoff=date(2026, 7, 1))
    assert state["done"] is True


def test_retracting_notes_finds_the_known_cases():
    """`blaxel-sandbox` carries the shape this looks for in two axes: an adoption note whose
    "No last_verified claimed" sentence is retracted three sentences later, and a capability
    note flagging its own benchmark figure as superseded."""
    from build.sweep_status import retracting_notes

    found = {(slug, axis) for slug, axis, _ in retracting_notes()}
    assert ("blaxel-sandbox", "adoption") in found
    assert ("blaxel-sandbox", "capability") in found
    assert len(found) > 30, f"only {len(found)} retracting notes; the walk has drifted"


def test_under_coverage_finds_the_case_the_guide_names():
    """`docs/reference/adoption.md` establishes the rule on `n8n` — npm downloads banded while
    the product ships overwhelmingly as a Docker container. If this stops finding it, the
    detector no longer matches the class the guide describes."""
    from build.sweep_status import under_coverage

    found = {slug for slug, _, _ in under_coverage()}
    assert {"n8n", "mistral-large", "ollama"} <= found


def test_under_coverage_only_reads_measured_instruments():
    """A `reported_traction` band claims no measurement, so it cannot be disowning one.
    Including it would fold this list into the banded_quantity class, which is a different
    problem with a different fix."""
    import yaml
    from pathlib import Path

    from build.sweep_status import ROOT, under_coverage

    for slug, _, _ in under_coverage():
        score = yaml.safe_load((Path(ROOT) / "sources" / "scores" / f"{slug}.yaml").read_text())
        assert score["adoption"]["signal_type"] in ("usage_volume", "stars_fallback")
