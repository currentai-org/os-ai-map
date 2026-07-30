"""Tests for G1, G2 and G3.

The one that matters most is `test_g1_fails_when_one_dimension_is_stale`. G1's aggregation
direction is load-bearing — it is over EVERY recorded dimension, so the binding constraint
is the least recently re-read one — and the tempting simplification to `max(accessed)` would
pass exactly that fixture. The failure mode has shipped twice (#108, #115), so it is pinned.
"""

import pytest
import yaml

from build.check_verification import (
    DIGEST_EXEMPT,
    g1_invariant,
    g2_digests,
    g3_producible,
    producible_pairs,
    recorded_dimensions,
)

RECIPE = {
    "openness": {
        "dimensions": {
            "weights": {"values": ["open", "closed"]},
            "data": {"values": ["open", "closed"], "reads": ["data", "post-training-data"]},
            "code": {"values": ["open", "partial", "closed"]},
        },
        "license_tier": {"reads": ["license"], "values": {}},
        "formula": [
            {"when": {"weights": "closed"}, "then": {"score": 1, "class": "closed"}},
            {"when": {"weights": "open"}, "then": {"score": 5, "class": "open_source"}},
        ],
    }
}
CATEGORIES = {"models": {"name": "models", "products": ["m"], "scoring_recipe": RECIPE}}
# `recipes` maps a category to its resolved variants ("*" for a uniform category, or one
# key per product type for a mixed one) - the same shape build.check_verification.load()
# produces via resolve_recipe_variants.
RECIPES = {"models": {"*": RECIPE}}


def _score(**openness):
    block = {
        "score": 5,
        "class": "open_source",
        "components": "weights:open;data:open;code:open;license:Apache-2.0(OSI)",
    }
    block.update(openness)
    return {"m": {"product": "m", "openness": block}}


def _src(url, accessed, establishes=None, fetched=True):
    source = {"url": url, "shows": "x", "accessed": accessed}
    if establishes is not None:
        source["establishes"] = establishes
    if fetched:
        source["http_status"] = 200
        source["content_sha256"] = "a" * 64
    return source


FULL = [
    _src("https://a", "2026-07-30", ["weights", "license"]),
    _src("https://b", "2026-07-30", ["data"]),
    _src("https://c", "2026-07-30", ["code"]),
]


# --- what counts as a recorded dimension ---

def test_recorded_dimensions_are_the_declared_ones_plus_license():
    found = recorded_dimensions(
        {"weights": "open", "data": "open", "code": "open", "license": "Apache-2.0(OSI)"}, RECIPE
    )
    assert found == {"weights": "weights", "data": "data", "code": "code", "license": "license"}


def test_undeclared_components_keys_are_not_dimensions():
    """`paper` and `model_card` are recorded but no ladder scores them, so demanding an
    establishing source for each would make the gate expensive and pointless at once."""
    found = recorded_dimensions(
        {"weights": "open", "paper": "open", "model_card": "open", "license": "MIT"}, RECIPE
    )
    assert set(found) == {"weights", "license"}


def test_a_dimension_answered_under_a_reads_alias_keeps_the_alias():
    """`finetuned_chat` answers the data question under `post-training-data`, and a source
    attributing to that key is being more precise than one attributing to `data`."""
    found = recorded_dimensions({"post-training-data": "open", "license": "MIT"}, RECIPE)
    assert found["data"] == "post-training-data"


# --- G1 ---

def test_g1_passes_when_every_dimension_has_a_fresh_establishing_source():
    scores = _score(last_verified="2026-07-30", sources=FULL)
    assert g1_invariant(scores, CATEGORIES, RECIPES, {}) == []


def test_g1_ignores_an_axis_with_no_date():
    """The ratchet: an axis claiming nothing is not asked to prove anything."""
    assert g1_invariant(_score(sources=[_src("https://a", "2020-01-01")]), CATEGORIES, RECIPES, {}) == []


def test_g1_fails_when_a_dimension_has_no_establishing_source():
    scores = _score(last_verified="2026-07-30", sources=FULL[:2])  # code unattributed
    problems = g1_invariant(scores, CATEGORIES, RECIPES, {})
    assert any("records 'code'" in p and "no source claims to establish it" in p for p in problems)


def test_g1_fails_when_one_dimension_is_stale():
    """The aggregation direction. Three dimensions re-read today, one last seen in June: a
    `max(accessed)` check passes this, and the invariant must not."""
    scores = _score(
        last_verified="2026-07-30",
        sources=[
            _src("https://a", "2026-07-30", ["weights", "license"]),
            _src("https://b", "2026-07-30", ["data"]),
            _src("https://c", "2026-06-01", ["code"]),
        ],
    )
    problems = g1_invariant(scores, CATEGORIES, RECIPES, {})
    assert len(problems) == 1
    assert "records 'code'" in problems[0]
    assert "only established by a source last read 2026-06-01" in problems[0]


def test_g1_fails_when_no_source_was_read_on_or_after_the_claimed_date():
    scores = _score(
        last_verified="2026-07-30",
        sources=[_src("https://a", "2026-06-01", ["weights", "data", "code", "license"])],
    )
    problems = g1_invariant(scores, CATEGORIES, RECIPES, {})
    assert any("no source was accessed on or after that date" in p for p in problems)


def test_g1_never_derives_a_date_it_only_validates_one():
    """Guards against the #115 'simplification'. A fully-attributed axis with no
    `last_verified` must stay silent rather than acquiring one."""
    scores = _score(sources=FULL)
    assert g1_invariant(scores, CATEGORIES, RECIPES, {}) == []
    assert "last_verified" not in scores["m"]["openness"]


def test_g1_floor_applies_to_adoption_where_there_are_no_dimensions():
    """Adoption records one banded value, so there is nothing to attribute among - but a
    confirmation still cannot rest on zero sources read on or after the date it claims."""
    scores = {"m": {"product": "m", "adoption": {"level": 4, "last_verified": "2026-07-30",
                                                "sources": [_src("https://a", "2026-06-01")]}}}
    assert any("no source was accessed on or after" in p for p in g1_invariant(scores, {}, {}, {}))


def test_g1_accepts_adoption_with_one_fresh_source_and_no_attribution():
    scores = {"m": {"product": "m", "adoption": {"level": 4, "last_verified": "2026-07-30",
                                                "sources": [_src("https://a", "2026-07-30")]}}}
    assert g1_invariant(scores, {}, {}, {}) == []


def test_g1_rejects_a_last_verified_that_is_not_a_date():
    scores = _score(last_verified="last week", sources=FULL)
    assert any("is not a date" in p for p in g1_invariant(scores, CATEGORIES, RECIPES, {}))


def test_g1_falls_back_to_the_floor_for_a_category_with_no_recipe():
    """Four categories have no recipe yet, so there is no declared vocabulary to check
    against. The gate degrades to the floor rather than passing vacuously or erroring."""
    scores = _score(last_verified="2026-07-30", sources=[_src("https://a", "2026-06-01")])
    assert any("no source was accessed on or after" in p for p in g1_invariant(scores, {}, {}, {}))


# --- G2 ---

def test_g2_passes_when_every_fresh_source_records_a_fetch():
    assert g2_digests(_score(last_verified="2026-07-30", sources=FULL)) == []


def test_g2_fails_on_a_missing_digest():
    scores = _score(
        last_verified="2026-07-30",
        sources=[_src("https://a", "2026-07-30", ["weights"], fetched=False)],
    )
    problems = g2_digests(scores)
    assert any("no http_status and no content_sha256" in p for p in problems)


def test_g2_ignores_sources_read_before_the_claimed_date():
    """Those were not part of this confirmation, so they are out of scope. Otherwise every
    new date would demand re-fetching evidence it never relied on."""
    scores = _score(
        last_verified="2026-07-30",
        sources=FULL + [_src("https://old", "2026-01-01", fetched=False)],
    )
    assert g2_digests(scores) == []


def test_g2_reports_a_stale_exemption(monkeypatch):
    monkeypatch.setitem(DIGEST_EXEMPT, "ghost:openness", "pre-runbook date")
    problems = g2_digests(_score(last_verified="2026-07-30", sources=FULL))
    assert any("Drop the exemption" in p for p in problems)


def test_g2_honors_a_live_exemption(monkeypatch):
    monkeypatch.setitem(DIGEST_EXEMPT, "m:openness", "pre-runbook date")
    scores = _score(
        last_verified="2026-07-30",
        sources=[_src("https://a", "2026-07-30", ["weights"], fetched=False)],
    )
    assert g2_digests(scores) == []


def test_the_shipped_exemption_list_is_empty():
    """Not a style preference. An exemption is a claim that a digest was unobtainable, and
    every axis dated so far was re-fetched instead."""
    assert DIGEST_EXEMPT == {}


# --- G3 ---

def test_producible_pairs_reads_then_and_otherwise():
    recipe = {"openness": {"formula": [
        {"when": {"a": "b"}, "then": {"score": 2, "class": "source_available"}},
        {"otherwise": {"score": 1, "class": "closed"}},
    ]}}
    assert producible_pairs(recipe) == {(2, "source_available"), (1, "closed")}


def test_g3_passes_on_a_producible_pair():
    assert g3_producible(_score(), CATEGORIES, RECIPES) == []


def test_g3_fails_on_a_class_no_rule_pairs_with_that_score():
    """`4/open_source` in software: 4 exists and `open_source` exists, never together."""
    scores = _score(score=1, **{"class": "open_source"})
    problems = g3_producible(scores, CATEGORIES, RECIPES)
    assert any("1/open_source is not an outcome" in p for p in problems)


def test_g3_fails_on_a_score_no_rule_emits():
    """The software ladder's rungs are 1, 2, 4, 5. A software product scored 3 is impossible
    by construction, however plausible the class looks beside it."""
    scores = _score(score=3, **{"class": "open_source"})
    assert any("3/open_source is not an outcome" in p for p in g3_producible(scores, CATEGORIES, RECIPES))


def test_g3_ignores_an_unscored_product():
    assert g3_producible(_score(score=None), CATEGORIES, RECIPES) == []


def test_g3_is_not_escapable_by_deferring_the_product():
    """`check_rubric` excludes a deferred product from reproduction. G3 must not, or a
    category could defer its way out of an impossible pair - which is how `4/open_source`
    survived a checker that reported 33/33."""
    categories = {"models": dict(CATEGORIES["models"])}
    recipes = {"models": {"*": dict(RECIPE, deferred={"m": {"because": "needs a human, at length"}})}}
    scores = _score(score=3, **{"class": "open_source"})
    assert g3_producible(scores, categories, recipes)


# --- the repo itself ---

def test_the_repo_passes_all_three_gates():
    from build.check_verification import ROOT, load
    from build.rubrics import load_product_types

    scores, categories, recipes = load()
    product_types = load_product_types(ROOT)
    assert g1_invariant(scores, categories, recipes, product_types) == []
    assert g2_digests(scores) == []
    assert g3_producible(scores, categories, recipes) == []


@pytest.mark.parametrize("axis", ["openness", "adoption", "capability"])
def test_every_dated_axis_in_the_repo_carries_establishing_evidence(axis):
    """Restates G1's scope as data rather than logic: whatever carries a date must be
    covered, so a new date cannot land without the gate having an opinion about it."""
    from build.check_verification import ROOT

    for path in sorted((ROOT / "sources" / "scores").glob("*.yaml")):
        block = (yaml.safe_load(path.read_text()) or {}).get(axis) or {}
        if not block.get("last_verified"):
            continue
        fresh = [
            s for s in block.get("sources") or []
            if str(s.get("accessed")) >= str(block["last_verified"])
        ]
        assert fresh, f"{path.name}:{axis}"
        assert all(s.get("content_sha256") for s in fresh), f"{path.name}:{axis}"
