"""Tests for the sweep's state, which is derived rather than stored.

`test_state_is_derived_not_stored` is the one that matters. A pointer file recording "we are on
category N" is a second copy of a fact the corpus already carries, and it desyncs the first time
someone finishes a category by hand. These assert the survey reads the corpus.
"""

from datetime import date

import yaml

from build.sweep_status import ROOT, product_state, survey
from build.taxonomy import category_statuses


def score(**axes) -> dict:
    base = {"openness": {"score": 5}, "adoption": {"level": 3}, "capability": {"score": 4}}
    for axis, extra in axes.items():
        base[axis] = {**base[axis], **extra}
    return base


def test_a_product_is_done_when_every_axis_is_dated():
    state = product_state(
        "p", {},
        score(openness={"last_verified": "2026-08-08"},
              adoption={"last_verified": "2026-08-08"},
              capability={"last_verified": "2026-08-08"}),
        held={},
    )
    assert state["done"] is True
    assert set(state["axes"].values()) == {"verified"}


def test_the_prose_has_no_bearing_on_done():
    """`done` used to require `comments` to end in a dated `Verified … via` line, the one
    thing about the prose a checker could see. #619 retired the line, so a footnote, an
    empty field and a field that still carries the old line all read the same here; the
    line's absence is asserted by tests/test_product_prose.py instead."""
    dated = score(openness={"last_verified": "2026-08-08"},
                  adoption={"last_verified": "2026-08-08"},
                  capability={"last_verified": "2026-08-08"})
    for product in ({}, {"comments": "A footnote about the reading."},
                    {"comments": "Verified 2026-08-08 via GitHub."}):
        state = product_state("p", product, dated, held={})
        assert state["done"] is True
        assert "prose" not in state and "prose_state" not in state


def test_a_null_axis_abstains_rather_than_blocking():
    """Some axes are deliberately null - a hosted feature with no usage figure to band."""
    state = product_state(
        "p", {},
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
    state = product_state("p", {}, score(), held={})
    assert set(state["axes"].values()) == {"open"}
    assert state["done"] is False


def test_the_real_corpus_surveys_and_orders_worst_coverage_first():
    """The ordering invariant, which holds at every state of the sweep including finished.

    This used to assert `pending`, with the message "the sweep is not finished, so something
    must be pending" - which made completing the sweep a test failure. It is the fifth test in
    this repository to fail because the work succeeded, so the rule is now explicit: a
    real-corpus test may assert an INVARIANT, never that there is work left to do. The
    non-empty ordering case is proved below on a corpus the test builds.
    """
    rows = survey()
    # Derived rather than pinned. This assertion used to read `== 16` and `== 472`, and it
    # failed the day two categories were published because the corpus had grown - the sixth
    # time in this repository that a test failed because the work succeeded, which is what the
    # docstring above is about. `survey()` covers the PUBLISHED categories (preliminary ones
    # carry no head-product verification work), so that is what this compares against.
    published = [slug for slug, status in category_statuses(
        yaml.safe_load((ROOT / "sources" / "taxonomy.yaml").read_text())).items()
        if status == "published"]
    assert len(rows) == len(published)
    assert sum(r["products"] for r in rows) == sum(
        len(yaml.safe_load((ROOT / "sources" / "categories" / f"{slug}.yaml").read_text())
            .get("products") or []) for slug in published)
    # Finished categories sort last whatever their coverage; among the rest, worst first.
    coverages = [r["coverage"] for r in rows if r["done"] < r["products"]]
    assert coverages == sorted(coverages), "pending categories must be worst-coverage first"
    assert all(r["done"] <= r["products"] for r in rows)


def test_pending_categories_sort_worst_coverage_first_and_finished_ones_last():
    """The ordering with something to order, on a synthetic survey."""
    from build.sweep_status import order_rows

    rows = [
        {"category": "finished", "products": 3, "done": 3, "coverage": 1.0},
        {"category": "mid", "products": 4, "done": 2, "coverage": 0.5},
        {"category": "worst", "products": 4, "done": 1, "coverage": 0.25},
        {"category": "best-pending", "products": 4, "done": 3, "coverage": 0.75},
    ]
    assert [r["category"] for r in order_rows(rows)] == [
        "worst", "mid", "best-pending", "finished"
    ]


# --- the refresh window ---

def _dated(day: str) -> dict:
    return score(openness={"last_verified": day},
                 adoption={"last_verified": day},
                 capability={"last_verified": day})


def test_without_a_cutoff_any_confirmation_counts():
    state = product_state("p", {}, _dated("2020-01-01"), held={})
    assert state["done"] is True


def test_a_confirmation_older_than_the_window_is_stale_not_verified():
    """This is what turns the sweep from a one-time pass into a recurring refresh."""
    state = product_state("p", {}, _dated("2026-06-01"), held={}, cutoff=date(2026, 7, 1))
    assert set(state["axes"].values()) == {"stale"}
    assert state["done"] is False


def test_a_confirmation_on_the_cutoff_still_counts():
    state = product_state("p", {}, _dated("2026-07-01"), held={}, cutoff=date(2026, 7, 1))
    assert set(state["axes"].values()) == {"verified"}
    assert state["done"] is True


def test_a_never_confirmed_axis_is_open_not_stale():
    """Open and stale are different jobs: one has never been read, the other has aged."""
    state = product_state("p", {}, score(), held={}, cutoff=date(2026, 7, 1))
    assert set(state["axes"].values()) == {"open"}


def test_a_held_product_stays_resolved_under_any_window():
    state = product_state("p", {}, _dated("2020-01-01"), held={"p": {}}, cutoff=date(2026, 7, 1))
    assert state["done"] is True


def test_retracting_detector_matches_the_shapes_it_is_for():
    """Detector behaviour, on synthetic notes rather than on the corpus.

    An earlier cut asserted that `blaxel-sandbox` still had both defects and that at least
    30 retracting notes remained. That pins the backlog: the refresh pass these worklists
    exist to feed would have broken CI by doing its job. Test the detector; smoke-test the
    traversal; never assert a defect survives.
    """
    from build.sweep_status import RETRACTING

    for note in [
        "That last sentence is superseded - the axis has now been re-read.",
        "BENCHMARK FIGURE SUPERSEDED - the leaderboard has re-run since.",
        "EVIDENCE REPLACED 2026-08-13. The category pass found a better source.",
        "THE PREVIOUS BASIS IS WITHDRAWN: the valuation is not on any cited page.",
        "the '400M daily actions' figure no longer appears on the announcement",
    ]:
        assert RETRACTING.search(note), note

    for note in [
        "Re-read 2026-08-13 and unchanged; the page still describes the same feature set.",
        "17,574 downloads in the trailing 30 days summed across the family's shipped SKUs.",
        "Held at 5 on 2026-08-14 for the Apertus family, whose current release is 1.5.",
    ]:
        assert not RETRACTING.search(note), note


def test_under_coverage_detector_matches_both_directions():
    from build.sweep_status import INFLATED, UNDERSTATES

    assert UNDERSTATES.search("this understates real use, but the map bands on the artifact")
    assert UNDERSTATES.search("banding on the minority channel that happens to be countable")
    assert UNDERSTATES.search("npm is not the product's primary distribution channel")
    assert INFLATED.search("almost certainly CI/mirror-inflated for an OTel SDK")
    assert not UNDERSTATES.search("429,490 downloads in the trailing 30 days, band unchanged")
    # The affirmative is the opposite claim, not the admission (review of #620: four notes sat
    # in the pinned set on "PyPI is the primary distribution channel for a Python library").
    assert not UNDERSTATES.search("PyPI is the primary distribution channel for a Python library")
    assert not UNDERSTATES.search("the data-designer package is this tool's primary distribution channel")


def test_both_worklists_traverse_the_corpus_without_asserting_a_backlog():
    """A smoke test over real files: the walk runs, returns well-formed rows, and reads only
    the axes it claims to. It deliberately does NOT assert how many findings there are —
    zero is a valid and desirable answer.
    """
    import yaml
    from pathlib import Path

    from build.sweep_status import ROOT, retracting_notes, under_coverage

    for slug, axis, phrase in retracting_notes():
        assert (Path(ROOT) / "sources" / "scores" / f"{slug}.yaml").exists()
        assert axis in ("openness", "adoption", "capability")
        assert phrase

    for slug, direction, phrase in under_coverage():
        assert direction in ("understates", "inflated")
        score = yaml.safe_load((Path(ROOT) / "sources" / "scores" / f"{slug}.yaml").read_text())
        # A reported_traction band claims no measurement, so it cannot be disowning one.
        assert score["adoption"]["signal_type"] in ("usage_volume", "stars_fallback")
