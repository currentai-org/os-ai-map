"""Tests for the rubric and evidence serializer.

Two things here would corrupt scores silently rather than loudly, so they get the
attention: the ORDER of the formula rules, because the formula is first-match-wins
and a reordering changes scores without changing any value, and the ADMISSION rule,
because a filler source that passes for evidence is worse than no source at all.
"""

import pytest

from build.serialize_rubric import (
    TABLES,
    admit,
    build_rubric,
    evidence_abstentions,
    license_aliases,
    license_tiers,
    scoring_rules,
    split_value,
)

RECIPE = {
    "version": 1,
    "openness": {
        "dimensions": {
            "weights": {"question": "?", "values": ["open", "closed", "pending"]},
            "data": {"question": "?", "values": ["open", "documented-not-released", "closed"]},
            "code": {"question": "?", "values": ["open", "partial", "closed"]},
        },
        "license_tier": {
            "ordered_by": "restrictiveness_ascending",
            "values": {
                "osi": {"examples": ["Apache-2.0", "MIT"]},
                "use_restricted": {"examples": ["Gemma-License"]},
                "proprietary": {"definition": "no public license"},
            },
        },
        "formula": [
            {"when": {"weights": "closed"}, "then": {"score": 1, "class": "closed"}},
            {"when": {"license_tier": "use_restricted"}, "then": {"score": 2, "class": "restricted"}},
            {
                "when": {"data": "open", "code": "open", "license_tier": "osi"},
                "then": {"score": 5, "class": "open_source"},
            },
            {"otherwise": {"score": 3, "class": "open_weights"}},
        ],
    },
}

POLICY = {"admission": {"boilerplate_shows": ["verification source"], "require_nonempty_shows": True}}

# Two shared ladders, minimal but structurally valid, for the product-type variant test.
SHARED_RUBRICS_FIXTURE = {
    "software": {
        "openness": {
            "dimensions": {"weights": {"question": "?", "values": ["open", "closed"]}},
            "license_tier": {
                "ordered_by": "restrictiveness_ascending",
                "values": {"osi": {"examples": ["MIT"]}, "proprietary": {"definition": "no public license"}},
            },
            "formula": [{"otherwise": {"score": 3, "class": "open_weights"}}],
        },
    },
    "model": {
        "openness": {
            "dimensions": {"weights": {"question": "?", "values": ["open", "closed"]}},
            "license_tier": {
                "ordered_by": "restrictiveness_ascending",
                "values": {"osi": {"examples": ["MIT"]}, "proprietary": {"definition": "no public license"}},
            },
            "formula": [{"otherwise": {"score": 3, "class": "open_weights"}}],
        },
    },
}


# Dedicated to test_recipe_for_selects_the_matching_ladder_for_a_scored_product only.
# Unlike SHARED_RUBRICS_FIXTURE, the two ladders here declare DISJOINT `weights` enums,
# so scoring a product against the wrong ladder is visible: the recorded value falls
# outside the other ladder's declared values and trips `in_declared_enum`.
DISJOINT_WEIGHTS_RUBRICS_FIXTURE = {
    "software": {
        "openness": {
            "dimensions": {"weights": {"question": "?", "values": ["closed-source", "source-available"]}},
            "license_tier": {
                "ordered_by": "restrictiveness_ascending",
                "values": {"osi": {"examples": ["MIT"]}, "proprietary": {"definition": "no public license"}},
            },
            "formula": [{"otherwise": {"score": 3, "class": "open_weights"}}],
        },
    },
    "model": {
        "openness": {
            "dimensions": {"weights": {"question": "?", "values": ["open", "closed"]}},
            "license_tier": {
                "ordered_by": "restrictiveness_ascending",
                "values": {"osi": {"examples": ["MIT"]}, "proprietary": {"definition": "no public license"}},
            },
            "formula": [{"otherwise": {"score": 3, "class": "open_weights"}}],
        },
    },
}


def _sources(categories=None, scores=None, rubrics=None, product_types=None):
    return {
        "categories": categories or {},
        "scores": scores or {},
        "rubrics": rubrics or {},
        "product_types": product_types or {},
    }


def _real_sources(root):
    """The repo's real sources, with `product_types` threaded through the way `main()`
    does it (`build/serialize_rubric.py:564`). Without this key every product's `type`
    reads as `""`, which for a mixed category (`extends` mapping product type -> ladder)
    means `recipe_for` resolves to None for every product rather than to its real ladder
    — a test that omits it exercises a path no production run takes.
    """
    from build.rubrics import load_product_types
    from build.validate import load_sources

    sources = load_sources(root)
    sources["product_types"] = load_product_types(root)
    return sources


def test_split_value_separates_the_bare_value_from_its_detail():
    assert split_value("open(downloadable on HF, gated)") == ("open", "downloadable on HF, gated")
    assert split_value("Apache-2.0(OSI)") == ("Apache-2.0", "OSI")
    assert split_value("closed") == ("closed", "")
    assert split_value("") == ("", "")


def test_split_value_bare_half_matches_what_the_formula_consumes():
    """The formula reads check_rubric.head; the two must not diverge."""
    from build.check_rubric import head

    for raw in [
        "open(downloadable on HF, gated/terms acceptance)",
        "code MIT + model DeepSeek-Model-License",
        "documented-not-released",
        "Llama-3.1-Community-License(non-OSI: 700M MAU cap)",
    ]:
        assert split_value(raw)[0] == head(raw)


def test_formula_order_is_preserved_because_first_match_wins():
    rows, errors = scoring_rules("base", RECIPE)
    assert errors == []
    indexes = [r["rule_index"] for r in rows]
    assert indexes == sorted(indexes)
    # The `weights: closed` short circuit has to stay ahead of the tier rules, or a
    # closed model with a restrictive license scores 2 instead of 1.
    assert rows[0] == {
        "category_slug": "base",
        "recipe_version": 1,
        "rule_index": 0,
        "is_otherwise": False,
        "condition_key": "weights",
        "condition_value": "closed",
        "then_score": 1,
        "then_class": "closed",
    }


def test_multi_condition_rule_becomes_several_rows_sharing_a_rule_index():
    rows, _ = scoring_rules("base", RECIPE)
    rule_2 = [r for r in rows if r["rule_index"] == 2]
    assert len(rule_2) == 3
    assert {r["condition_key"] for r in rule_2} == {"data", "code", "license_tier"}
    assert {r["then_score"] for r in rule_2} == {5}


def test_otherwise_rule_carries_no_condition():
    rows, _ = scoring_rules("base", RECIPE)
    fallthrough = [r for r in rows if r["is_otherwise"]]
    assert len(fallthrough) == 1
    assert fallthrough[0]["condition_key"] == ""
    assert fallthrough[0]["then_score"] == 3


def test_rule_testing_an_undeclared_dimension_is_an_error():
    """A dead rule does not raise, it just pushes products into `otherwise`."""
    recipe = {
        "version": 1,
        "openness": {
            "dimensions": {"weights": {"values": ["open"]}},
            "license_tier": {"values": {"osi": {"examples": ["MIT"]}}},
            "formula": [{"when": {"governance": "foundation"}, "then": {"score": 4, "class": "x"}}],
        },
    }
    _, errors = scoring_rules("base", recipe)
    assert any("undeclared dimension 'governance'" in e for e in errors)


def test_rule_testing_a_value_outside_the_declared_enum_is_an_error():
    recipe = {
        "version": 1,
        "openness": {
            "dimensions": {"data": {"values": ["open", "closed"]}},
            "license_tier": {"values": {"osi": {"examples": ["MIT"]}}},
            "formula": [{"when": {"data": "components-listed"}, "then": {"score": 4, "class": "x"}}],
        },
    }
    _, errors = scoring_rules("base", recipe)
    assert any("components-listed" in e for e in errors)


def test_rule_testing_an_undefined_tier_is_an_error():
    recipe = {
        "version": 1,
        "openness": {
            "dimensions": {"data": {"values": ["open"]}},
            "license_tier": {"values": {"osi": {"examples": ["MIT"]}}},
            "formula": [{"when": {"license_tier": "copyleft"}, "then": {"score": 4, "class": "x"}}],
        },
    }
    _, errors = scoring_rules("base", recipe)
    assert any("copyleft" in e for e in errors)


def test_proprietary_tier_is_emitted_definitionally():
    """No vendor publishes a license called 'proprietary', so the tier is defined by
    meaning. Emitting the tokens keeps the warehouse to one lookup table."""
    rows, errors = license_tiers("base", RECIPE)
    assert errors == []
    proprietary = [r for r in rows if r["tier"] == "proprietary"]
    assert {r["example_license"] for r in proprietary} == {"proprietary", "closed", "none"}
    assert all(r["is_definitional"] for r in proprietary)
    osi = [r for r in rows if r["tier"] == "osi"]
    assert not any(r["is_definitional"] for r in osi)


def test_tier_rank_follows_declaration_order():
    """`most restrictive SKU governs` needs an ordering, and it has to be the
    declared one rather than whatever order the YAML happens to use."""
    rows, _ = license_tiers("base", RECIPE)
    rank_of = {r["tier"]: r["tier_rank"] for r in rows}
    assert rank_of["osi"] < rank_of["use_restricted"] < rank_of["proprietary"]


def test_several_tiers_without_a_declared_ordering_is_an_error():
    recipe = {
        "version": 1,
        "openness": {
            "dimensions": {},
            "license_tier": {
                "values": {"osi": {"examples": ["MIT"]}, "use_restricted": {"examples": ["Gemma"]}}
            },
            "formula": [],
        },
    }
    _, errors = license_tiers("base", recipe)
    assert any("ordered_by" in e for e in errors)


def test_a_single_tier_needs_no_declared_ordering():
    """Nothing to compare, so requiring the key would be noise."""
    recipe = {
        "version": 1,
        "openness": {"license_tier": {"values": {"osi": {"examples": ["MIT"]}}}},
    }
    rows, errors = license_tiers("base", recipe)
    assert errors == []
    assert rows[0]["tier_rank"] == 0


def test_license_aliases_come_out_per_source():
    routing = {"dimensions": {"license": {"aliases": {"huggingface": {"gemma": "Gemma-License"}}}}}
    assert license_aliases(routing) == [
        {"source": "huggingface", "license_slug": "gemma", "license_name": "Gemma-License"}
    ]


def test_abstentions_come_from_the_route_and_keep_the_source_specific():
    """Read from signal_routing.yaml, not evidence_policy.yaml. `source` is the route
    name so a model-license abstention cannot be read as a dataset-license one."""
    routing = {
        "dimensions": {
            "license": {
                "routes": [
                    {"source": "huggingface_model", "column": "license",
                     "abstain_values": ["other", "cc"], "abstain_note": "prose for a human"},
                    {"source": "github", "column": "license_spdx_id",
                     "abstain_values": ["NOASSERTION"]},
                    {"source": "huggingface_dataset", "column": "license"},
                ]
            }
        }
    }
    assert evidence_abstentions(routing) == [
        {"source": "huggingface_model", "column_name": "license", "abstain_value": "other"},
        {"source": "huggingface_model", "column_name": "license", "abstain_value": "cc"},
        {"source": "github", "column_name": "license_spdx_id", "abstain_value": "NOASSERTION"},
    ]


def test_the_same_source_column_routed_twice_yields_one_row_per_value():
    """A lookup table with duplicate keys would fan out the evidence join."""
    routing = {
        "dimensions": {
            "license": {"routes": [{"source": "github", "column": "license_spdx_id",
                                    "abstain_values": ["NOASSERTION"]}]},
            "code": {"routes": [{"source": "github", "column": "license_spdx_id",
                                 "abstain_values": ["NOASSERTION"]}]},
        }
    }
    assert len(evidence_abstentions(routing)) == 1


def test_real_abstentions_cover_the_escape_hatches_seen_in_the_data():
    from pathlib import Path

    from build.serialize_rubric import load_routing

    rows = evidence_abstentions(load_routing(Path(__file__).resolve().parents[1]))
    pairs = {(r["source"], r["abstain_value"]) for r in rows}
    assert ("huggingface_model", "other") in pairs
    assert ("huggingface_model", "cc") in pairs
    assert ("github", "NOASSERTION") in pairs


def test_abstentions_are_declared_in_exactly_one_file():
    """Regression guard. NOASSERTION was once declared in both signal_routing.yaml and
    evidence_policy.yaml; a reader fixing one would have missed the other."""
    from pathlib import Path

    from build.serialize_rubric import load_policy

    policy_abstentions = load_policy(Path(__file__).resolve().parents[1]).get("abstentions") or {}
    # Only non-source-specific policy belongs here, and those are scalars/flags.
    for key, value in policy_abstentions.items():
        assert not isinstance(value, dict), (
            f"evidence_policy.yaml declares per-source abstentions under {key!r}; "
            f"those belong on the route in signal_routing.yaml"
        )


def test_admission_rejects_the_declared_boilerplate():
    ok, reason = admit("flagship phase-C verification source", POLICY)
    assert not ok
    assert "boilerplate" in reason


def test_admission_rejects_an_empty_shows():
    ok, reason = admit("", POLICY)
    assert not ok
    assert "no `shows`" in reason


@pytest.mark.parametrize(
    "shows",
    [
        "MIT License text",
        "13,834 monthly downloads",
        "~1,996 stars",
        "AA Intelligence Index 17, rank #29/43",
    ],
)
def test_admission_keeps_short_but_specific_sources(shows):
    """A length floor was tried and rejected. These are all under 40 characters and
    every one of them names a fact; the 199 filler rows are longer than all of them."""
    ok, reason = admit(shows, POLICY)
    assert ok, reason


def test_rejected_sources_are_emitted_not_dropped():
    """Rejection turns an unsourced assertion into a work item. Dropping it would
    make the gap invisible, which is the failure mode being fixed."""
    sources = _sources(
        categories={"base": {"scoring_recipe": RECIPE, "products": ["m"]}},
        scores={
            "m": {
                "openness": {
                    "score": 3,
                    "class": "open_weights",
                    "components": "weights:open;data:closed",
                    "sources": [
                        {"url": "https://x.test/a", "shows": "flagship phase-C verification source", "accessed": "2026-06-04"},
                        {"url": "https://x.test/b", "shows": "Apache-2.0 in the model card", "accessed": "2026-06-04"},
                    ],
                }
            }
        },
    )
    tables, errors, warnings = build_rubric(sources, POLICY, {})
    assert errors == []
    rows = tables["product_score_sources"]
    assert len(rows) == 2
    assert [r["admitted"] for r in rows] == [False, True]
    assert any("cite nothing specific" in w for w in warnings)


def test_evidence_comes_out_at_dimension_grain():
    sources = _sources(
        categories={"base": {"scoring_recipe": RECIPE, "products": ["m"]}},
        scores={"m": {"openness": {"components": "weights:open(on HF);data:closed;license:MIT(OSI)"}}},
    )
    tables, errors, _ = build_rubric(sources, POLICY, {})
    assert errors == []
    by_dimension = {r["dimension"]: r for r in tables["product_openness_evidence"]}
    assert set(by_dimension) == {"weights", "data", "license"}
    assert by_dimension["weights"]["value"] == "open"
    assert by_dimension["weights"]["value_detail"] == "on HF"
    assert by_dimension["weights"]["grade"] == "document"
    # `license` feeds the tier lookup rather than an enum, so it has nothing to check.
    assert by_dimension["license"]["in_declared_enum"] == ""
    assert by_dimension["data"]["in_declared_enum"] is True


def test_value_outside_the_declared_enum_is_a_warning_not_an_error():
    """The rubric being too coarse for the data is a curation finding, and it must
    not block a build."""
    sources = _sources(
        categories={"base": {"scoring_recipe": RECIPE, "products": ["m"]}},
        scores={"m": {"openness": {"components": "data:components-listed"}}},
    )
    tables, errors, warnings = build_rubric(sources, POLICY, {})
    assert errors == []
    assert any("components-listed" in w for w in warnings)
    assert tables["product_openness_evidence"][0]["in_declared_enum"] is False


def test_undeclared_component_dimension_is_a_warning():
    """`marin` records reproducibility:bit-for-bit, which is a real openness fact the
    base-model rubric has no question for. It cannot move a score, but it should not
    pass through unremarked either."""
    sources = _sources(
        categories={"base": {"scoring_recipe": RECIPE, "products": ["m"]}},
        scores={"m": {"openness": {"components": "weights:open;reproducibility:bit-for-bit"}}},
    )
    tables, errors, warnings = build_rubric(sources, POLICY, {})
    assert errors == []
    assert any("'reproducibility'" in w and "does not declare" in w for w in warnings)
    # Still emitted: the scorer ignores it, a curator should not have to.
    assert {r["dimension"] for r in tables["product_openness_evidence"]} == {
        "weights",
        "reproducibility",
    }


def test_license_is_not_treated_as_an_undeclared_dimension():
    """It feeds the tier lookup rather than being a dimension with an enum."""
    sources = _sources(
        categories={"base": {"scoring_recipe": RECIPE, "products": ["m"]}},
        scores={"m": {"openness": {"components": "license:MIT(OSI)"}}},
    )
    _, _, warnings = build_rubric(sources, POLICY, {})
    assert not any("does not declare" in w for w in warnings)


def test_a_category_with_no_recipe_is_a_warning():
    sources = _sources(categories={"base": {"scoring_recipe": RECIPE, "products": []}, "other": {}})
    _, errors, warnings = build_rubric(sources, POLICY, {})
    assert errors == []
    assert any("'other' declares no scoring_recipe" in w for w in warnings)


def test_no_recipe_anywhere_is_an_error():
    _, errors, _ = build_rubric(_sources(categories={"other": {}}), POLICY, {})
    assert any("nothing to score with" in e for e in errors)


def test_rubric_rows_carry_product_type():
    """A uniform category's rubric rows are stamped `*`; a mixed category's rubric
    rows are stamped with the product type of the ladder that produced them. This
    test supplies no `scores`, so it exercises only the per-category rubric-table
    stamping (`category_scoring_rules` and `category_license_tiers`) — the
    per-product `recipe_for` selection is covered separately by
    `test_recipe_for_selects_the_matching_ladder_for_a_scored_product` and
    `test_recipe_miss_still_emits_score_sources_for_other_axes`.
    """
    sources = _sources(
        categories={
            "uniform": {"name": "uniform", "products": ["p1"],
                        "scoring_recipe": {"extends": "software"}},
            "mixed": {"name": "mixed", "products": ["m1", "s1"],
                      "scoring_recipe": {"extends": {"model": "model", "software": "software"}}},
        },
        rubrics=SHARED_RUBRICS_FIXTURE,
        product_types={"p1": "software", "m1": "model", "s1": "software"},
    )
    tables, errors, _ = build_rubric(sources, policy={}, routing={})
    assert errors == []
    uniform_rules = [r for r in tables["category_scoring_rules"] if r["category_slug"] == "uniform"]
    mixed_rules = [r for r in tables["category_scoring_rules"] if r["category_slug"] == "mixed"]
    assert {r["product_type"] for r in uniform_rules} == {"*"}
    assert {r["product_type"] for r in mixed_rules} == {"model", "software"}

    uniform_tiers = [r for r in tables["category_license_tiers"] if r["category_slug"] == "uniform"]
    mixed_tiers = [r for r in tables["category_license_tiers"] if r["category_slug"] == "mixed"]
    assert {r["product_type"] for r in uniform_tiers} == {"*"}
    assert {r["product_type"] for r in mixed_tiers} == {"model", "software"}


def test_recipe_for_selects_the_matching_ladder_for_a_scored_product():
    """A scored product in a mixed-type category is scored against its OWN type's
    ladder, not the other one. `DISJOINT_WEIGHTS_RUBRICS_FIXTURE`'s two ladders
    declare non-overlapping `weights` enums (model: open/closed; software:
    closed-source/source-available), so picking the wrong ladder for a product
    is visible: the recorded value falls outside the other ladder's declared
    values, flipping `in_declared_enum` to False and firing a "not in the
    rubric's declared values" warning. A `recipe_for` that ignored `product_type`
    and always returned one ladder for both products would trip that check on
    whichever product does not match the ladder it hard-coded.
    """
    sources = _sources(
        categories={
            "mixed": {"name": "mixed", "products": ["m1", "s1"],
                      "scoring_recipe": {"extends": {"model": "model", "software": "software"}}},
        },
        scores={
            "m1": {"openness": {"components": "weights:open"}},
            "s1": {"openness": {"components": "weights:source-available"}},
        },
        rubrics=DISJOINT_WEIGHTS_RUBRICS_FIXTURE,
        product_types={"m1": "model", "s1": "software"},
    )
    tables, errors, warnings = build_rubric(sources, policy={}, routing={})
    assert errors == []
    assert not any("in 'mixed':" in w for w in warnings)
    assert not any("not in the rubric's declared values" in w for w in warnings)
    evidence = {
        (r["product_slug"], r["dimension"]): r for r in tables["product_openness_evidence"]
    }
    assert evidence[("m1", "weights")]["value"] == "open"
    assert evidence[("m1", "weights")]["in_declared_enum"] is True
    assert evidence[("s1", "weights")]["value"] == "source-available"
    assert evidence[("s1", "weights")]["in_declared_enum"] is True


def test_recipe_miss_still_emits_score_sources_for_other_axes():
    """A product whose declared `type` does not match any ladder (missing, or not
    one of the mapped keys) loses its openness evidence — `recipe_for` has nothing
    to hand back — but its adoption and capability source rows must still be
    emitted. Those axes read only `record` and `policy`, never `recipe`, so a
    `recipe_for` miss has no bearing on them. This pins Finding 1: narrowing the
    `continue` to skip only the recipe-dependent block, not the whole per-product
    body.
    """
    sources = _sources(
        categories={
            "mixed": {"name": "mixed", "products": ["m1"],
                      "scoring_recipe": {"extends": {"model": "model", "software": "software"}}},
        },
        scores={
            "m1": {
                "openness": {"components": "weights:open"},
                "adoption": {"sources": [{"url": "https://x.test/a", "shows": "13,834 monthly downloads"}]},
                "capability": {"sources": [{"url": "https://x.test/b", "shows": "AA Intelligence Index 17"}]},
            },
        },
        rubrics=SHARED_RUBRICS_FIXTURE,
        product_types={"m1": "unmapped-type"},
    )
    tables, errors, warnings = build_rubric(sources, policy=POLICY, routing={})
    assert errors == []
    assert any("in 'mixed':" in w for w in warnings)
    assert not any(r["product_slug"] == "m1" for r in tables["product_openness_evidence"])
    sources_by_axis = {r["axis"]: r for r in tables["product_score_sources"] if r["product_slug"] == "m1"}
    assert set(sources_by_axis) == {"adoption", "capability"}
    assert sources_by_axis["adoption"]["admitted"] is True
    assert sources_by_axis["capability"]["admitted"] is True


def test_deferred_product_emits_no_openness_evidence():
    """`openness_computed` builds its product roster with `SELECT DISTINCT
    product_slug, category_slug FROM product_evidence` — so a deferred product must
    not appear in `product_openness_evidence` at all, or that downstream model
    computes a score for a product the repo has explicitly declined to stand behind.
    """
    sources = _sources(
        categories={
            "base": {
                "scoring_recipe": {**RECIPE, "deferred": {"m1": {"because": "test reason"}}},
                "products": ["m1", "m2"],
            }
        },
        scores={
            "m1": {"openness": {"components": "weights:open;data:open;code:open;license:MIT(OSI)"}},
            "m2": {"openness": {"components": "weights:open;data:open;code:open;license:MIT(OSI)"}},
        },
    )
    tables, errors, _ = build_rubric(sources, POLICY, {})
    assert errors == []
    assert not any(r["product_slug"] == "m1" for r in tables["product_openness_evidence"])
    # The non-deferred product in the same category is unaffected.
    assert any(r["product_slug"] == "m2" for r in tables["product_openness_evidence"])


def test_deferred_product_still_emits_score_sources():
    """`deferred` is scoped to the openness axis only. `product_score_sources` covers
    all three axes, including adoption and capability, which have nothing to do with
    a deferred openness score — a body-wide `continue` here would silently drop them,
    which is exactly the regression `c151452` had to repair.
    """
    sources = _sources(
        categories={
            "base": {
                "scoring_recipe": {**RECIPE, "deferred": {"m1": {"because": "test reason"}}},
                "products": ["m1"],
            }
        },
        scores={
            "m1": {
                "openness": {"components": "weights:open;data:open;code:open;license:MIT(OSI)"},
                "adoption": {"sources": [{"url": "https://x.test/a", "shows": "1.2M monthly downloads"}]},
                "capability": {"sources": [{"url": "https://x.test/b", "shows": "AA Intelligence Index 17"}]},
            },
        },
    )
    tables, errors, _ = build_rubric(sources, POLICY, {})
    assert errors == []
    assert not any(r["product_slug"] == "m1" for r in tables["product_openness_evidence"])
    sources_by_axis = {r["axis"]: r for r in tables["product_score_sources"] if r["product_slug"] == "m1"}
    assert set(sources_by_axis) == {"adoption", "capability"}


def test_every_declared_table_is_present():
    tables, _, _ = build_rubric(_sources(categories={"base": {"scoring_recipe": RECIPE}}), POLICY, {})
    assert set(tables) == set(TABLES)


def test_real_sources_serialize_without_errors():
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing

    root = Path(__file__).resolve().parents[1]
    tables, errors, _ = build_rubric(_real_sources(root), load_policy(root), load_routing(root))
    assert errors == [], f"rubric has errors: {errors[:5]}"

    # Asserted per category rather than as a total, so a new recipe shows up as its
    # own line instead of moving one opaque number. base_pretrained's counts are
    # pinned as a regression guard: porting the rubric to a second category, adding
    # recorded-name aliases and adding `reads` must not disturb the pilot.
    def per_category(table):
        counts: dict[str, int] = {}
        for row in tables[table]:
            counts[row["category_slug"]] = counts.get(row["category_slug"], 0) + 1
        return counts

    # Ten software categories inherit ONE ladder from sources/rubrics/software.yaml, so
    # they all serialize the same 10 rules. Identical counts are the point: a category
    # showing a different number means it stopped inheriting.
    #
    # Was 16 until the two `permissive_non_osi` rungs came out. Both were unreachable - the
    # tier's `examples` list is empty - and both emitted an open-bucket class from a non-OSI
    # license, which is the boundary tests/test_openness_buckets.py now enforces. Removing
    # them costs 6 rows per software category and 6 from `safeguards`, whose software half
    # inherits the same ladder (25 -> 19 = 10 software + 9 model).
    SOFTWARE = ["agent_tools_protocols", "dataset_processing_tools", "deployment",
                "evaluation_code", "finetuning_code", "inference_code", "ml_frameworks",
                "orchestration_agents", "telemetry_observability", "ui_api"]
    # Two DATASET categories inherit sources/rubrics/dataset.yaml, so both serialize the
    # same 24 rules. Was 22 until compound licenses resolved on all their parts, which put
    # `flan-collection` on a deferred-license tier it had never reached while the resolver
    # truncated at the first parenthesis, and needed a rung for a deferred license paired
    # with a partial card. Two rows because a two-condition rung serializes as two.
    #
    # Each of the four ladders gained exactly one rung with the universal
    # license scale, which split one tier in two - a bounded commercial license at 3, and a
    # license forbidding commerce outright at 2.
    #
    # Formerly 21: 3 not-published rungs, 2 held-out-answer rungs, 6 gate rungs and 5
    # license/documentation rungs, all single-condition except the last 5.
    #
    # Was 14 for training_synthetic_datasets alone. benchmark_eval_data widened the shared
    # ladder rather than overriding it: a benchmark may not be published at all, which the
    # first version had no rung for, and its answers may be held back, which is a question
    # a training corpus does not have. Identical counts are the point - a category showing
    # a different number means it stopped inheriting.
    #
    # `edge_hardware` is the first HARDWARE category and the only ladder with no
    # `license_tier`: 4 rungs, each a single condition on `schematics` except the two that
    # also test `toolchain`, so 6 rows.
    assert per_category("category_scoring_rules") == {
        "base_pretrained": 12, "finetuned_chat": 10, "safeguards": 20,
        "benchmark_eval_data": 24, "training_synthetic_datasets": 24, "edge_hardware": 6,
        **{c: 10 for c in SOFTWARE},
    }
    # Both fell with the slug migration: release-level products collapsed into the
    # tier the vendor sells, so 25 products left the roster and the closed frontier
    # models moved from base_pretrained to finetuned_chat.
    #
    # Eight software categories then rose by 1-3 rows when the score corrections from the
    # producible-pair check landed: fixing an impossible score/class pair means recording the
    # dimension that decides it, so products that had described their gating in prose gained a
    # readable `source:` or `core-gated:` key. The two model categories are untouched, which
    # is what the pilot counts are pinned to catch.
    # `safeguards` is back at 90 rows. It had disappeared from this dict entirely when all
    # 26 of its products were deferred; 17 now reproduce, because sixteen of them were
    # recording the deciding evidence under keys the ladders do not read rather than
    # disagreeing with the ladders. Nine other
    # categories drop too, by however many rows their own deferred products used to
    # carry (1-3 rows per product) — a deferred product publishes no openness evidence
    # at all now, so `openness_computed` never sees enough rows to score a product the
    # repo declined to stand behind.
    assert per_category("product_openness_evidence") == {
        # finetuned_chat rose by 1 when `recipe` joined `code`'s `reads` list: `ornith`
        # recorded only `recipe:closed`, so its `code` dimension had been reading as
        # unrecorded and published no evidence row. check_recipe found it.
        # base_pretrained rose by 5 (111 -> 116) when the fully-open Luciole family was
        # added: five openness dimensions recorded (weights, data, code, checkpoints, license).
        #
        # Five categories rose again when the license tier stopped being resolved ahead of
        # the formula, and every row is a deferral coming off rather than a new key:
        # agent_tools_protocols +4 (apify), evaluation_code +12 (chatbot-arena,
        # patronus-evaluation-platform and artificial-analysis-intelligence-index, four rows
        # each) and ui_api +5 (confer). All five record a `source` value the software ladder
        # settles on its own and were abstained on a license no rung deciding them reads.
        # Note the three evaluation_code products publish no `license` row at all - they
        # record no license key - which is what `check_rubric`'s `~ no tier` report exists
        # to keep visible.
        "base_pretrained": 116, "finetuned_chat": 173, "deployment": 131,
        "agent_tools_protocols": 113, "dataset_processing_tools": 86, "evaluation_code": 78,
        # inference_code 47 -> 64 when the sweep read the category: four stale deferrals came
        # off (a deferred product publishes no openness evidence at all), and several products
        # that had described their gating in prose gained a readable `source:`/`core-gated:`.
        #
        # Three categories then rose by 14 rows in total when five vendor licenses joined the
        # `competition_restricted` tier and the deferrals waiting on them came off:
        # inference_code +4 (max, which records repo-license and commercial-tier beside the two
        # dimensions), orchestration_agents +4 (autogpt and dify, two rows each) and ui_api +6
        # (open-webui and lobe-chat, each with a tier key beside the two). Every row is a
        # deferral coming off; no product that was already computed gained a key, which is why
        # the other twelve categories hold.
        "finetuning_code": 124, "inference_code": 69, "ml_frameworks": 80,
        # orchestration_agents rose by 3 when n8n's stale deferral was removed: a deferred
        # product publishes no openness evidence, and n8n had been deferred as "not recorded"
        # while recording everything the ladder needed. Then by 6 more (140 -> 146) when
        # OpenRAG was added: it records source, core-gated, license, self-host, commercial,
        # and the normalized core_gated the ladder reads from core-gated — the same six-row
        # shape RAGFlow already contributes.
        #
        # Five categories then rose by 41 rows in total when `core_gated` started reading
        # `self-host`, and the split is worth keeping visible because the two causes are
        # different sizes. 29 rows are one new `core_gated` row each, on products that were
        # already computed and stay at the score they had: agent_tools_protocols +1
        # (pinecone), inference_code +1 (apple-core-ml-runtime), telemetry_observability +4,
        # orchestration_agents +8 and ui_api +12, every one of them a closed hosted product
        # the `source: closed` rung decides on its own. The other 12 are three deferrals
        # coming off at 5 rows each, less nothing: syfthub in orchestration_agents,
        # thunderbolt and otari in ui_api. A deferred product publishes no openness evidence
        # at all, so a removed deferral is always the larger of the two effects.
        "orchestration_agents": 163, "telemetry_observability": 94, "ui_api": 160,
        # training_synthetic_datasets is unchanged at 158 across the ladder widening, which
        # is the check that mattered: benchmark_eval_data's new dimensions and rungs did not
        # disturb the category the ladder was derived from.
        # 164 -> 169: `smoltalk`'s deferral was the ladder reading only the first half of
        # `apache-2.0(new-subsets)+per-component`. Reading both halves reproduces its
        # recorded 4/open, the deferral went, and its five component keys publish.
        # 169 -> 194: the five remaining parser deferrals came off together. Each of
        # cosmopedia, openthoughts-114k, synth, tulu-3-sft-mixture and wildchat-1m now
        # publishes five rows - license, the gate key and the card key, plus the
        # `availability` and `documentation` dimensions those two normalize onto - and a
        # deferred product publishes none at all, so 5 x 5 is the whole of the move. The
        # promotion added no key to a product that was already computed, which is why
        # benchmark_eval_data holds at 111: compar-ia-datasets got the same `dataset_card`
        # key and stays deferred on its unrelated gate-vocabulary defect.
        "training_synthetic_datasets": 194, "benchmark_eval_data": 111,
        # safeguards 90 -> 103 and training_synthetic_datasets 158 -> 164: the universal
        # license scale retired five deferrals, and a deferred product publishes no
        # openness evidence at all.
        "safeguards": 103,
        # 17 scored hardware products across the five recorded dimensions, less the keys
        # individual products do not record. No license row among them, by design -
        # `edge_hardware` is the only category whose ladder declares no `license_tier`.
        "edge_hardware": 83,
    }
    assert {r["grade"] for r in tables["product_openness_evidence"]} == {"document"}


def test_every_scored_product_carries_a_row_for_each_formula_dimension():
    """The warehouse joins a rule's `condition_key` against the `dimension` column,
    so a dimension recorded under a different key has to be emitted under the
    DIMENSION name. Emitted under the raw key instead, the condition silently fails
    to match and the product falls through to `otherwise` — scored on an absence.
    """
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing

    root = Path(__file__).resolve().parents[1]
    tables, _, _ = build_rubric(_real_sources(root), load_policy(root), load_routing(root))

    by_product: dict[tuple[str, str], set[str]] = {}
    for row in tables["product_openness_evidence"]:
        by_product.setdefault((row["category_slug"], row["product_slug"]), set()).add(
            row["dimension"]
        )

    # `data` is the dimension finetuned_chat reads from a different key, so it is the
    # one that would go missing.
    missing = [
        product
        for (category, product), dimensions in by_product.items()
        if category == "finetuned_chat" and "data" not in dimensions
    ]
    assert missing == [], f"no data row emitted for: {missing}"


def test_a_value_alias_is_translated_before_it_reaches_the_warehouse():
    """`core_gated` reads `self-host`, whose vocabulary is `yes`/`no`/`none` rather than
    `gated`/`ungated`. The warehouse joins a rule's `condition_value` against this column,
    so the translation has to happen on the way out or `openness_computed` would have to
    carry a copy of the alias table — the repo/warehouse split check_parity exists to catch.
    Normalizing here is what keeps this change off that list.

    The recorded spelling is not lost: `self-host` is still emitted under its own name by
    the traceability pass, so both rows are in the evidence store.
    """
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing

    root = Path(__file__).resolve().parents[1]
    tables, _, _ = build_rubric(_real_sources(root), load_policy(root), load_routing(root))

    rows = {
        (r["dimension"], r["value"], r["in_declared_enum"])
        for r in tables["product_openness_evidence"]
        if r["product_slug"] == "chatgpt" and r["dimension"] in ("core_gated", "self-host")
    }
    assert rows == {("core_gated", "gated", True), ("self-host", "none", "")}


def test_license_is_emitted_under_the_name_the_warehouse_joins_on():
    """`license_tier.reads` lets a category accept the license under another key.

    deepseek-coder records `model-license`, because its card separates the code license
    from the one on the weights. check_rubric honors that list, but the serializer used
    to emit the row under its raw key, so the SQL - which looks only for
    `dimension = 'license'` - found nothing and the product abstained in the warehouse
    while reproducing locally. Exactly one license row per scored product, under
    `license`, is what keeps the two in step.
    """
    from pathlib import Path

    from build.rubrics import resolve_recipe_variants
    from build.serialize_rubric import load_policy, load_routing

    root = Path(__file__).resolve().parents[1]
    sources = _real_sources(root)
    tables, _, _ = build_rubric(sources, load_policy(root), load_routing(root))

    # Deferred products are excluded: a category has declared the rubric does not decide
    # them, and several are deferred precisely BECAUSE no license is recorded. Asserting a
    # license row for those would be asserting evidence we have said we do not have.
    #
    # Note the asymmetry this leaves. `deferred` lives only in the repo - there is no
    # category_deferrals table - so the warehouse does not know these products are held
    # back. With no `otherwise` rule in the software ladder they currently fall out of the
    # scoring model's INNER JOIN rather than being scored wrongly, which is the safe
    # direction but a silent one. Bridging the list is tracked separately.
    #
    # Deferrals are a property of the category's declaration, not of any one resolved
    # ladder — `resolve_recipe_variants` only screens out a category whose `extends` is
    # broken, matching `build/check_rubric.py`'s `check_category`.
    # Categories whose ladder declares no `license_tier` are excluded for the same reason as
    # deferrals: there is no license to emit, so asserting a row would be asserting evidence
    # we have said does not exist. `edge_hardware` is the case - a board's openness turns on
    # whether its design files were published, not on a source license, and not one of its 20
    # products records one.
    #
    # This leaves the same asymmetry the deferral note describes, and it is worth stating
    # plainly: `currentai.scores.openness_computed` mirrors this walk by hand and joins
    # license evidence, so until it carries the same tier-free allowance the repo just gained
    # in `check_rubric.check_category`, hardware products will abstain in the warehouse while
    # reproducing locally. That is the safe direction and a silent one.
    shared = sources.get("rubrics") or {}
    deferred = set()
    tier_free = set()
    for slug, category in sources["categories"].items():
        variants, _ = resolve_recipe_variants(category, shared)
        if not variants:
            continue
        for product in ((category.get("scoring_recipe") or {}).get("deferred") or {}):
            deferred.add((product, slug))
        if not any(
            ((v.get("openness") or {}).get("license_tier") or {}).get("values")
            for v in variants.values()
        ):
            tier_free.add(slug)

    rows = tables["product_openness_evidence"]
    scored = {
        (r["product_slug"], r["category_slug"])
        for r in rows
        if r["category_slug"] not in tier_free
    } - deferred
    licensed = {(r["product_slug"], r["category_slug"]) for r in rows if r["dimension"] == "license"}

    # The third exclusion, and the newest. A product can now score in a tier-carrying
    # category without a license at all: `check_rubric` resolves a tier only for a rung that
    # tests one, so a product the software ladder settles on `source` alone is scored whether
    # or not anyone recorded a license. Three do, all in `evaluation_code`, and none of them
    # records a license clause of any kind — so there is genuinely no row to emit, and
    # asserting one would again be asserting evidence we have said does not exist.
    #
    # Pinned by name rather than computed away, because the set is exactly what
    # `check_rubric`'s `~ no tier` report exists to keep countable, and a silently growing
    # exclusion here would be the way the report stops meaning anything. A fourth product
    # appearing means someone scored something on less evidence than its neighbours, and it
    # should have to be written down here.
    #
    # This carries the same warehouse asymmetry the two notes above describe:
    # `currentai.scores.openness_computed` resolves the tier up front and joins license
    # evidence, so until it carries the same rule these three will abstain there while
    # reproducing here.
    unlicensed = {
        ("chatbot-arena", "evaluation_code"),
        ("patronus-evaluation-platform", "evaluation_code"),
        ("artificial-analysis-intelligence-index", "evaluation_code"),
    }
    assert unlicensed <= scored, "a pinned no-license product stopped scoring"
    missing = scored - licensed
    assert missing == unlicensed, f"no license row emitted for: {sorted(missing - unlicensed)}"

    deepseek = [r for r in rows if r["product_slug"] == "deepseek-coder" and r["dimension"] == "license"]
    assert len(deepseek) == 1 and deepseek[0]["value"] == "DeepSeek-Model-License"


def test_evidence_never_puts_two_values_on_one_grain():
    """One product/category/dimension must carry one value. Two would let the
    warehouse pick between a base corpus and a post-training mixture by row order.
    """
    from collections import Counter
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing

    root = Path(__file__).resolve().parents[1]
    tables, _, _ = build_rubric(_real_sources(root), load_policy(root), load_routing(root))

    counts = Counter(
        (r["product_slug"], r["category_slug"], r["dimension"])
        for r in tables["product_openness_evidence"]
    )
    assert [key for key, n in counts.items() if n > 1] == []


def test_real_license_aliases_cover_every_slug_the_hub_actually_returns():
    """Slugs observed live in signal_huggingface.hub_state on 2026-07-28. A slug with
    no alias reads as an ABSENT license rather than a present one, which is the
    direction that overstates openness."""
    from pathlib import Path

    from build.serialize_rubric import load_routing

    observed_models = {"apache-2.0", "mit", "llama3.1", "gemma", "llama2", "llama3", "bigcode-openrail-m"}
    aliased = {
        r["license_slug"]
        for r in license_aliases(load_routing(Path(__file__).resolve().parents[1]))
        if r["source"] == "huggingface"
    }
    assert observed_models <= aliased, f"unaliased Hub license slugs: {observed_models - aliased}"


def test_adoption_bands_are_declared_per_type_and_hardware_declares_none():
    """The bands were hardcoded in the scoring SQL until 2026-08-09.

    Four types, five levels each, minus hardware — which declares `qualitative: true` and
    an empty `bands`, so it emits no rows. That absence is load-bearing: a consumer that
    finds no band for a type must abstain rather than borrow another type's scale.
    """
    from build.serialize_rubric import adoption_bands
    from build.validate import load_sources
    from pathlib import Path

    rows, _warnings = adoption_bands(load_sources(Path(".")).get("rubrics") or {})
    by_type = {}
    for row in rows:
        by_type.setdefault(row["product_type"], []).append(row)

    assert set(by_type) == {"software", "model", "dataset"}
    assert all(len(v) == 5 for v in by_type.values())

    # `above` is an exclusive lower bound, so it must be strictly decreasing with level
    # or the highest-matching-level rule silently picks the wrong band.
    for product_type, bands in by_type.items():
        ordered = sorted(bands, key=lambda b: -b["level"])
        thresholds = [b["above"] for b in ordered]
        assert thresholds == sorted(thresholds, reverse=True), product_type
        # The floor is -1, not 0, so a figure of exactly ZERO still bands at 1. With 0 it
        # did not — `0 > 0` is false, so the product matched no band and came back
        # unbanded, which asserts "no scale exists for this type" rather than "nobody
        # downloaded it". zentropi-cope surfaced it on the first real run.
        assert ordered[-1]["above"] == -1, f"{product_type} floor must admit zero"


def test_dataset_bands_sit_one_order_below_software():
    """Measured, not assumed: no dataset artifact in the corpus exceeds 10M monthly
    downloads and exactly one exceeds 1M, so the software scale cannot discriminate."""
    from build.serialize_rubric import adoption_bands
    from build.validate import load_sources
    from pathlib import Path

    rows, _ = adoption_bands(load_sources(Path(".")).get("rubrics") or {})
    top = {r["product_type"]: r["above"] for r in rows if r["level"] == 5}
    assert top["software"] == top["model"] == 10_000_000
    assert top["dataset"] == 1_000_000


def test_stars_bands_are_declared_once_and_capped():
    """Stars are per INSTRUMENT, not per product type.

    A dataset's downloads run an order below a package's, which is why those bands are
    per type. A star is a star whatever it was given to, so the scale is declared once on
    its route in signal_routing.yaml and emitted with product_type '*'. Four copies in
    four rubrics is exactly the drift this whole table exists to stop.
    """
    import yaml
    from pathlib import Path

    from build.serialize_rubric import stars_bands

    routing = yaml.safe_load(Path("sources/signal_routing.yaml").read_text())
    rows, warnings = stars_bands(routing)

    assert warnings == []
    assert {r["product_type"] for r in rows} == {"*"}
    assert {r["signal_type"] for r in rows} == {"stars_fallback"}
    # Capped at 3: stars measure attention rather than use, so a stars-derived band may
    # never claim the top two levels however large the count.
    assert max(r["level"] for r in rows) == 3
    assert sorted(r["above"] for r in rows) == [-1, 1000, 10000]


def test_a_stars_band_above_the_cap_is_dropped_with_a_warning():
    """The cap is enforced, not trusted. A later edit adding a level-4 stars band should
    fail the serializer rather than quietly publish one."""
    from build.serialize_rubric import stars_bands

    routing = {
        "dimensions": {
            "adoption": {
                "routes": [
                    {
                        "signal_type": "stars_fallback",
                        "cap": 3,
                        "bands": [
                            {"level": 4, "above": 100000, "reach": ">100K stars"},
                            {"level": 3, "above": 10000, "reach": ">10K stars"},
                        ],
                    }
                ]
            }
        }
    }
    rows, warnings = stars_bands(routing)
    assert [r["level"] for r in rows] == [3]
    assert any("exceeds the declared cap" in w for w in warnings)


def test_download_bands_and_stars_bands_do_not_collide():
    """Both live in one table, distinguished by signal_type. A consumer joining without
    filtering on it would band a package's downloads against the stars scale."""
    from pathlib import Path

    import yaml

    from build.serialize_rubric import adoption_bands, stars_bands
    from build.validate import load_sources

    downloads, _ = adoption_bands(load_sources(Path(".")).get("rubrics") or {})
    stars, _ = stars_bands(yaml.safe_load(Path("sources/signal_routing.yaml").read_text()))

    assert {r["signal_type"] for r in downloads} == {"usage_volume"}
    assert all(r["product_type"] != "*" for r in downloads)
    keys = {(r["product_type"], r["signal_type"], r["level"]) for r in downloads + stars}
    assert len(keys) == len(downloads) + len(stars), "a (type, instrument, level) key repeats"


def test_split_value_bare_half_matches_head_on_the_whole_corpus():
    """The property the structured-dimensions migration rests on, tested against the corpus.

    A structured `components` mapping is score-neutral only because the bare half of
    `split_value` is byte-identical to `check_rubric.head`, which is what every formula
    actually reads. That held on all 1,754 recordings when it was measured, and until now
    it was asserted against four hand-written strings — so an edit to either function could
    move scores with every gate green. Four literals cannot notice that; the corpus can.

    Reads each record's flat string via `components_string`, which is the one function
    every reader uses to look past the migration's shape change: it prefers the verbatim
    `raw` a migrated record keeps, and falls back to the literal `components` string for a
    record not yet migrated. That keeps this walk at the full original population — 1,754
    recordings — regardless of how many records have been reshaped, instead of shrinking
    as `components` stops being a plain string.
    """
    from pathlib import Path

    import yaml

    from build.check_rubric import components_string, head, split_components

    root = Path(__file__).resolve().parents[1]
    mismatches = []
    recordings = 0
    for path in sorted((root / "sources" / "scores").glob("*.yaml")):
        block = (yaml.safe_load(path.read_text()) or {}).get("openness") or {}
        components = components_string(block)
        if not components:
            continue
        for key, raw in split_components(components).items():
            recordings += 1
            if split_value(raw)[0] != head(raw):
                mismatches.append(f"{path.stem}.{key}: {raw!r}")

    # A floor, not an exact count: this is the full pre-migration recording count, and the
    # corpus only grows from here as products are scored and edited (37 commits to
    # sources/scores/ in the last 30 days alone), so recordings > 1,754 is ordinary
    # curation, not a bug. A DROP below it means the walk stopped following the migrated
    # shape — the failure this test exists to catch, which moved the count in hundreds at
    # a time (1,754 -> 1,060 -> 510), never by ones. Growth needs no alarm; a shrink does.
    assert recordings >= 1_754, f"only {recordings} recordings reached; the corpus walk is broken"
    assert mismatches == [], "split_value and head disagree:\n  " + "\n  ".join(mismatches)
