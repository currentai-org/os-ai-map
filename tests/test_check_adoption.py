"""The adoption gate: is a recorded band on the scale its own rubric declares?

`adoption_bands` were declared per product type, serialized into the warehouse, and covered by
tests for their SHAPE. Nothing compared a product's recorded `(level, reach)` against them, so
the bands were authoritative for the warehouse and advisory for the corpus — the same
hand-mirrored-logic drift `check_parity` exists to catch one axis over.

`dataset.yaml` even predicted the failure in a comment: "14 dataset products record level 4
against a reach of 1M-10M, which is level 5 on this scale ... They are a work list, not a
migration." A work list written into a comment is not a gate, and it grew.
"""

from pathlib import Path

import pytest

from build.check_adoption import collect, declared_scales, scale_for
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def sources():
    return load_sources(ROOT)


def test_every_product_type_with_an_adoption_axis_declares_a_scale(sources):
    """Hardware declares none by design; the other three must, or nothing can be checked."""
    scales = declared_scales(sources)
    for product_type in ("software", "model", "dataset"):
        assert (product_type, "*") in scales, f"{product_type} declares no adoption bands"
    assert ("*", "stars_fallback") in scales, "the stars fallback scale did not load"


def test_the_stars_scale_is_chosen_by_signal_not_by_type(sources):
    """Stars are a property of the SIGNAL, so they override the product type's own scale.

    This is the resolution order the checker depends on, and getting it backwards would
    silently check every stars_fallback product against the download vocabulary.
    """
    scales = declared_scales(sources)
    stars = scale_for(scales, "software", "stars_fallback")
    assert stars is not None
    assert all("star" in label for label in stars), stars
    # And its ceiling is level 3: a star is not a use. validate.py enforces the level; this
    # asserts no label above it exists to record.
    assert max(stars.values()) == 3, stars

    downloads = scale_for(scales, "software", "usage_volume")
    assert downloads is not None and downloads != stars


def test_an_instrument_with_no_scale_abstains_rather_than_borrowing_one(sources):
    """The rule the first version of this checker broke.

    `docs/guides/adoption.md`: "a `reported_traction` or `active_users` band is measuring
    something else entirely. Comparing it against a download count is a category error, and a
    check must SKIP it rather than flag or waive it." `sources/signal_routing.yaml` states the
    same principle as "abstain rather than substitute".

    Neither instrument has a declared band table anywhere in the repo — two of the five values
    in the `signal_type` enum have no scale — so a checker that falls back to the product
    type's DOWNLOAD scale manufactures a finding for every one of them. It did, for all 93
    `reported_traction` products, and the false findings were indistinguishable from real ones
    because they had the same shape.
    """
    scales = declared_scales(sources)
    for instrument in ("reported_traction", "active_users"):
        for product_type in ("software", "model", "dataset"):
            assert scale_for(scales, product_type, instrument) is None, (
                f"{instrument} borrowed the {product_type} scale; it measures something else"
            )

    # And the instruments that ARE denominated in downloads must still resolve, or the
    # abstention would have been bought by disabling the check.
    assert scale_for(scales, "software", "usage_volume") is not None
    assert scale_for(scales, "software", "stars_fallback") is not None


def test_the_dataset_scale_sits_one_order_below_software(sources):
    """The fact the thirteen benchmark corpora were mis-banded against.

    Measured rather than assumed: across 66 HF dataset artifacts the median was 27,648 and
    none exceeded 10M, so on the software scale level 5 would be unreachable.
    """
    scales = declared_scales(sources)
    dataset = scale_for(scales, "dataset", "usage_volume")
    software = scale_for(scales, "software", "usage_volume")

    assert ">1M" in dataset and ">10M" not in dataset
    assert ">10M" in software and ">1M" not in software


def test_the_walk_examines_most_of_the_corpus(sources):
    """A non-zero count guard. Two corpus walks in this repo silently narrowed and passed.

    The floor is 300 rather than 400 because `reported_traction` and `active_users` are now
    correctly skipped — about 110 products whose instrument declares no scale. The guard still
    has to be a real floor: it catches the glob drifting or the scale lookup breaking, which
    would take this to near zero.
    """
    _findings, examined = collect(sources)
    assert examined > 300, f"only examined {examined} products; the walk has drifted"


def test_the_benchmark_corpora_refreshed_on_2026_08_12_are_on_scale(sources):
    """The thirteen this gate was written for. Pinned so they cannot drift back.

    Three moved level, not just label: `mmlu` 5 -> 4 (it claimed >10M against 477,890 monthly
    downloads), `mmmu` 4 -> 3, `evalplus` 4 -> 3.
    """
    scales = declared_scales(sources)
    refreshed = [
        "truthfulqa", "mmmu", "mmlu-pro", "mbpp", "ifeval", "humaneval", "hellaswag",
        "ai2-arc", "mmlu", "gsm8k", "evalplus", "codecontests", "apps",
    ]
    offences = []
    for slug in refreshed:
        adoption = sources["scores"][slug]["adoption"]
        scale = scale_for(scales, "dataset", adoption.get("signal_type") or "")
        reach, level = adoption.get("reach"), adoption.get("level")
        if reach not in scale:
            offences.append(f"{slug}: reach {reach!r} is off the dataset scale")
        elif scale[reach] != level:
            offences.append(f"{slug}: level {level} against reach {reach!r} (scale says {scale[reach]})")
        if adoption.get("last_verified") != "2026-08-12":
            offences.append(f"{slug}: lost its last_verified date")
    assert not offences, "\n".join(offences)
