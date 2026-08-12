"""The deferral-reason gate, and proof that it fires.

A deferral reason is hand-written prose that nothing verified, and the deferral list IS the
work queue — `check_recipe` already enforces that a reason exists and runs past 40 characters,
which makes it substantive without making it TRUE.

Across two sessions, roughly six of twenty reasons examined closely misdescribed their own
cause. Two nearly produced wrong work:

  * `arduino-uno-q` claimed it was held at 3 for a proprietary SoC. The hardware ladder never
    applies that reason — every board in the category runs on proprietary silicon, so the cap
    would flatten all twenty and leave the 4 and 5 rungs unreachable. The reason had been
    invented after the fact to explain a number.
  * `model-context-protocol` claimed it was blocked on a rubric ruling about non-OSI licenses.
    It was actually blocked on recording a DOCUMENTATION license inside the `license` compound,
    where most-restrictive-wins applied it to the artifact you run. `autogen` records the
    identical facts under a `docs:` key the ladder does not read. The reason read plausibly
    and survived several reviews.

The gate replays the ladder and requires the prose to name the mechanism that actually stopped
it. These tests exist because a gate that has only ever returned zero has not been shown to
work — that is the shape of instrument failure this repo has found four times.
"""

from pathlib import Path

import pytest
import yaml

from build.check_recipe import deferral_reasons_name_the_real_blocker
from build.rubrics import load_product_types, load_shared, resolve_recipe_variants

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fixture():
    """A real deferred product, its category's ladder variants, and the product-type map."""
    product_types = load_product_types(ROOT)
    shared = load_shared(ROOT)
    for path in sorted((ROOT / "sources" / "categories").glob("*.yaml")):
        category = yaml.safe_load(path.read_text()) or {}
        deferrals = (category.get("scoring_recipe") or {}).get("deferred") or {}
        if deferrals:
            variants, _ = resolve_recipe_variants(category, shared)
            slug = sorted(deferrals)[0]
            return path.stem, variants, product_types, slug, deferrals[slug]
    pytest.skip("no deferrals in the corpus to exercise the gate against")


def test_the_corpus_passes_its_own_gate(fixture):
    """Every deferral on record names the blocker the ladder actually hits."""
    product_types = load_product_types(ROOT)
    shared = load_shared(ROOT)
    problems = []
    for path in sorted((ROOT / "sources" / "categories").glob("*.yaml")):
        category = yaml.safe_load(path.read_text()) or {}
        deferrals = (category.get("scoring_recipe") or {}).get("deferred") or {}
        if not deferrals:
            continue
        variants, _ = resolve_recipe_variants(category, shared)
        problems += deferral_reasons_name_the_real_blocker(
            path.stem, variants, product_types, deferrals
        )
    assert not problems, "\n".join(problems)


def test_the_gate_rejects_a_reason_describing_the_wrong_mechanism(fixture):
    """The one that matters. A plausible reason naming nothing real must FAIL.

    Phrased the way the bad ones actually read — confident, specific, and about a mechanism
    this product's walk never reaches.
    """
    slug, variants, product_types, product, _block = fixture
    doctored = {
        product: {
            "because": (
                "Held back because the vendor ships a proprietary accelerator and the "
                "hardware ladder caps anything with closed silicon at 3, which is a "
                "policy question rather than a recording defect and needs a human ruling "
                "before this product can be scored against its peers."
            )
        }
    }
    problems = deferral_reasons_name_the_real_blocker(slug, variants, product_types, doctored)
    assert problems, f"the gate accepted a reason that names nothing the ladder does for {product}"
    assert product in problems[0]


def test_the_gate_accepts_the_real_reason(fixture):
    """The other half: the recorded reason passes, so the gate is not simply always-fail."""
    slug, variants, product_types, product, block = fixture
    problems = deferral_reasons_name_the_real_blocker(
        slug, variants, product_types, {product: block}
    )
    assert not problems, problems


def test_an_empty_reason_is_left_to_the_check_that_owns_it(fixture):
    """No double-reporting: the empty-reason failure has its own message elsewhere."""
    slug, variants, product_types, product, _ = fixture
    problems = deferral_reasons_name_the_real_blocker(
        slug, variants, product_types, {product: {"because": "   "}}
    )
    assert not problems
