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


def test_reported_traction_records_a_word_and_never_a_number(sources):
    """68 of its 110 records carried a numeric download label until 2026-08-13.

    They were perfectly collinear with the level beside them — `100K-1M` was level 3 on all 33
    of its records, `1M-10M` level 4 on all 23 — so they carried nothing the level did not.
    And they carried something false: `aws-neuron` read `100K-1M` beneath a note saying "no
    download/user count is published for Neuron". A reader sees a numeric band and concludes
    somebody counted something. On an instrument defined by having nothing to count, nobody did.
    """
    from build.check_adoption import declared_vocabularies

    vocab = declared_vocabularies()
    assert vocab["reported_traction"] == {"niche", "broad", "mass-market"}

    # The words are hardware's, which declares `qualitative: true` with an empty bands list and
    # has used exactly these since before the route existed. Sharing beats a parallel set.
    hardware = (sources["rubrics"]["hardware"] or {}).get("adoption") or {}
    assert hardware.get("qualitative") and not hardware.get("bands")

    offenders = []
    for slug, score in sources["scores"].items():
        adoption = (score or {}).get("adoption") or {}
        if adoption.get("signal_type") != "reported_traction":
            continue
        reach = adoption.get("reach")
        # Omitting `reach` is the honest default here, so None is legal on purpose.
        if reach is not None and reach not in vocab["reported_traction"]:
            offenders.append((slug, reach))
    assert not offenders, (
        f"{offenders} record a reach outside the vocabulary. A reported_traction record has no "
        f"count behind it, so a numeric band claims a measurement that was never made."
    )


def test_a_vocabulary_is_not_a_scale_and_does_not_constrain_the_level(sources):
    """The reason `vocabulary` exists as a separate concept from `bands`.

    A scale maps a label to a level, and a disagreement is a finding. A vocabulary says only
    which words exist: the word says what KIND of standing was claimed, the level says how
    much. Measured 2026-08-13, `niche` ran 85% level 3, `broad` 80% level 4, `mass-market` 67%
    level 5 — spreads that a bands table would flatten by forcing agreement.

    Asserted as a real property rather than a comment: at least one word must appear against
    more than one level, or the distinction this design rests on is not doing any work and the
    words may as well be bands.
    """
    from collections import defaultdict

    from build.check_adoption import declared_vocabularies

    words = declared_vocabularies()["reported_traction"]
    levels = defaultdict(set)
    for score in sources["scores"].values():
        adoption = (score or {}).get("adoption") or {}
        if adoption.get("signal_type") == "reported_traction" and adoption.get("reach") in words:
            levels[adoption["reach"]].add(adoption.get("level"))

    assert any(len(seen) > 1 for seen in levels.values()), (
        f"every word maps to exactly one level ({dict(levels)}) — if that holds, the words "
        f"are bands in disguise and should be declared as bands"
    )


def test_an_instrument_with_no_scale_abstains_rather_than_borrowing_one(sources):
    """The rule the first version of this checker broke.

    `docs/guides/adoption.md`: "a `reported_traction` band is measuring something else
    entirely. Comparing it against a download count is a category error, and a check must SKIP
    it rather than flag or waive it." `sources/signal_routing.yaml` states the same principle
    as "abstain rather than substitute".

    The instrument has no declared band table anywhere in the repo, so a checker that falls
    back to the product type's DOWNLOAD scale manufactures a finding for every one of them. It
    did, for all 93 `reported_traction` products, and the false findings were indistinguishable
    from real ones because they had the same shape.

    This still holds after 2026-08-13, and the distinction is the interesting part.
    `reported_traction` now has a VOCABULARY, so it is checked — but it still has no SCALE, so
    `scale_for` must keep returning None for it. A vocabulary constrains which words may be
    recorded; only a scale can say a level is wrong. Conflating the two would reintroduce the
    original bug wearing new clothes.

    `active_users` went the other way on the same day: it declares a real scale and resolves
    below. Both moves came out of the same finding, which is the one worth keeping — the skip
    was correct AND it was what hid the problem. 22 of 23 `active_users` records and 68 of 110
    `reported_traction` ones were wearing download labels, and a checker that declines to look
    never says so. Abstention is the right answer to a missing scale and the wrong answer to a
    scale nobody has declared yet.
    """
    scales = declared_scales(sources)
    for product_type in ("software", "model", "dataset"):
        assert scale_for(scales, product_type, "reported_traction") is None, (
            f"reported_traction borrowed the {product_type} scale; it measures something else"
        )

    # And the instruments that DO declare a scale must still resolve, or the abstention would
    # have been bought by disabling the check.
    assert scale_for(scales, "software", "usage_volume") is not None
    assert scale_for(scales, "software", "stars_fallback") is not None
    assert scale_for(scales, "software", "active_users") is not None


def test_the_active_users_scale_shares_download_thresholds_but_never_a_label(sources):
    """Declared 2026-08-13, on the finding that 22 of 23 records wore a borrowed vocabulary.

    The thresholds are deliberately identical to the download scale, so that a level means one
    magnitude across the whole map. That decision is exactly what makes the labels load-bearing:
    when two live scales share every boundary, an unsuffixed `>10M` cannot be told apart, and
    being unable to tell them apart is how the borrowing went unnoticed.
    """
    scales = declared_scales(sources)
    users = scale_for(scales, "software", "active_users")
    downloads = scale_for(scales, "software", "usage_volume")

    # 1. The same thresholds as downloads at every level, so a level means one magnitude
    #    wherever it appears. Asserted against the download scale itself rather than against
    #    literals, so that moving one scale and not the other fails here.
    by_level = {level: label for label, level in users.items()}
    assert by_level[5] == ">10M users" and by_level[4] == "1M-10M users"
    assert by_level[3] == "100K-1M users" and by_level[2] == "10K-100K users"
    strip = lambda scale: {label.removesuffix(" users"): level for label, level in scale.items()}
    assert strip(users) == downloads, "the two scales' thresholds have drifted apart"

    # 2. Every label carries its unit, so no label is shared with the download scale despite
    #    every boundary being shared. This is what makes a download vocabulary not merely
    #    discouraged here but unusable, and it is the only thing that can, now that the numbers
    #    are identical.
    assert all(label.endswith(" users") for label in users), users
    assert not (set(users) & set(downloads)), "a label is ambiguous between two live scales"

    # 3. No cap. Unlike stars, this measures use directly — unmeasurable by machine is a
    #    question about confidence, not about ceiling.
    assert max(users.values()) == 5, users


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
