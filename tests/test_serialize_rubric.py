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

    # Twelve software categories inherit ONE ladder from sources/rubrics/software.yaml, so
    # they all serialize the same 10 rules. Identical counts are the point: a category
    # showing a different number means it stopped inheriting.
    #
    # Was 16 until the two `permissive_non_osi` rungs came out. Both were unreachable - the
    # tier's `examples` list is empty - and both emitted an open-bucket class from a non-OSI
    # license, which is the boundary tests/test_openness_buckets.py now enforces. Removing
    # them costs 6 rows per software category and 6 from `safeguards`, whose software half
    # inherits the same ladder (25 -> 19 = 10 software + 9 model).
    SOFTWARE = ["agent_tools_protocols", "compilers", "dataset_processing_tools", "deployment",
                "evaluation_code", "finetuning_code", "inference_code", "ml_frameworks",
                "orchestration_agents", "storage", "telemetry_observability", "ui_api"]
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
    # `license_tier`. It was 6: 4 rungs, each a single condition on `schematics` except the
    # two that also test `toolchain`. It is 7 since 2026-08-12, when a single-condition
    # `accessory_host` rung was added at the top of the formula on the ruling that an
    # accessory tracks the platform it completes. It decides a different KIND of product
    # rather than a better one - `raspberry-pi-ai-hat-plus` is a HAT, and the four rungs
    # below it all assume the thing being scored is a board.
    # Software is 13 since 2026-08-12, and `safeguards` 23, because `permissive_non_osi`
    # got a rung back. Three rows, not one: it tests `license_tier`, `source` and
    # `core_gated`, and a three-condition rung serializes as three. Note the shape of the
    # history here - the tier lost 6 rows when its two rungs came out for emitting an
    # open-bucket class from a non-OSI license, and regained 3 for one rung emitting
    # 3/source_available, which is open-ISH. The rows came back; the boundary violation
    # did not.
    assert per_category("category_scoring_rules") == {
        "base_pretrained": 12, "finetuned_chat": 10, "safeguards": 23,
        "benchmark_eval_data": 24, "training_synthetic_datasets": 24, "edge_hardware": 9,
        **{c: 13 for c in SOFTWARE},
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
        #
        # Then +13 rows across seven categories when the license started publishing one row
        # per recorded PART instead of one truncated row per product. Twelve products record a
        # compound license: eleven in two parts and `zed` in three. No product gained a
        # component and none lost one - the same licenses were always in the files, the
        # serializer was publishing the first of them. The split is base_pretrained +1
        # (internlm), finetuned_chat +1 (command-r), inference_code +1 (llamafile),
        # finetuning_code +2 (megatron-lm, unsloth), orchestration_agents +3 (n8n, zed's two
        # extra), telemetry_observability +2 (agentops, langwatch) and
        # training_synthetic_datasets +3 (flan-collection, redpajama-data-v2, smoltalk).
                #
        # Five categories rose on 2026-09-01 with the Round 1 calibration tranche, one new
        # product's evidence set at a time: base_pretrained 117 -> 133 (granite, minicpm,
        # seed-oss, comma), finetuned_chat 174 -> 183 (gpt-oss, magistral), benchmark_eval_data
        # 154 -> 184 (tau-bench, terminal-bench, agentdojo, reward-bench, mle-bench),
        # inference_code 138 -> 166 (seven engines) and evaluation_code 109 -> 129 (five
        # harnesses). No product that was already computed gained or lost a row, which is why
        # the other thirteen categories hold.
        "base_pretrained": 133, "finetuned_chat": 183, "deployment": 131,
        #
        # evaluation_code 78 -> 107 with the 2026-08-11 evidence sweep of that category: all
        # seven of its deferrals came off, and a product that stops being deferred publishes its
        # whole openness evidence set rather than none of it. deepeval was already publishing and
        # gained no rows when its `core-gated` moved gated -> ungated.
        #
        # agent_tools_protocols 113 -> 122 with the 2026-08-12 sweep of that category: three of
        # its four deferrals came off (agent2agent-protocol, yomo and model-context-protocol,
        # the last of which now records source and core-gated but abstains on a three-way
        # license), and a product that stops being deferred publishes its whole openness
        # evidence set rather than none of it.
        #
        # dataset_processing_tools 86 -> 90 when nemo-data-designer's deferral came off on
        # 2026-08-12. A read of NVIDIA-NeMo/DataDesigner established `core-gated: ungated` -
        # the repository ships the generation engine itself and the NeMo Platform adds
        # infrastructure around it rather than withholding anything from it - and the record
        # moved from an unreproducible 1/closed to the 5/open_source the ladder computes.
        #
        # agent_tools_protocols 122 -> 127 when jina-reader's deferral closed on 2026-08-12. A
        # repo and pricing read recorded `core-gated: ungated` - Apache-2.0 throughout with no
        # enterprise directory and paid tiers that buy rate limit on the hosted endpoint - and
        # its recorded 5/open_source reproduces. Five rows, from none while deferred.
        # model-context-protocol still publishes nothing: CC-BY-4.0 now has a tier, so it
        # resolves to permissive_non_osi instead of nothing, and that tier deliberately has no
        # rung.
        # agent_tools_protocols rose 127 -> 134 on 2026-08-12 when the category's last
        # deferral came off. All seven rows are `model-context-protocol`, and they are
        # what a deferral was suppressing: `source`, `core_gated`, two `license` parts,
        # `docs`, `governance` and the raw `core-gated` key. `docs` publishes as an
        # undeclared-key row, exactly as `autogen`'s CC-BY-4.0 documentation license
        # already did - which is the evidence that MCP was made to match an existing
        # convention rather than given a new one.
        # agent_tools_protocols 124 -> 145 on 2026-08-30 with the first promotion out of that
        # category's tail registry: crawl4ai, mineru, context7, marker and lightpanda. Four rows
        # each - `source`, `core_gated`, one `license` part and the raw `core-gated` key - except
        # marker, which carries five because its license is a compound of two parts, Apache-2.0
        # over the code and a modified AI Pubs Open RAIL-M over the weights. No product that was
        # already computed gained or lost a row, which is why the other seventeen categories hold.
        "agent_tools_protocols": 145, "dataset_processing_tools": 92, "evaluation_code": 129,
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
        # finetuning_code 124 -> 133 and inference_code 69 -> 84 with the 2026-08-11 evidence
        # sweep of those categories: five deferrals came off (sglang,
        # text-generation-inference, axolotl, sambanova-cloud, anyscale-fine-tuning), and a
        # product that stops being deferred publishes its whole openness evidence set rather
        # than none of it. openpipe was already publishing and gained no rows.
        # ml_frameworks 80 -> 88 with the same sweep: pysyft and feluda were its only two
        # deferrals and both closed on a `core-gated:ungated` read, so the category now defers
        # nothing at all.
        # finetuning_code 133 -> 137 and inference_code 84 -> 89 when the last two conflicts in
        # those categories were ruled on rather than re-read, on 2026-08-12. unsloth and
        # aws-neuron each already recorded the deciding dimension and were publishing nothing
        # because a deferred product publishes nothing; the score moved to what the ladder
        # computes and the rows appeared.
        "finetuning_code": 159, "inference_code": 166, "ml_frameworks": 100,
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
        #
        # orchestration_agents 163 -> 187 on the 2026-08-11 evidence sweep, which is both
        # effects at once. Six deferrals came off - codex-cli, claude-code, cursor, haystack,
        # langgraph, hexabot - and each newly-computed product starts publishing its rows.
        # The four that stayed deferred (langchain, llama-index, pydantic-ai, zed) recorded a
        # `core-gated` key too, but a deferred product publishes nothing, so they contribute
        # zero rows and the whole rise is the six.
        #
        # 187 -> 207 later the same day, when those same four were ruled ungated and moved to
        # 5/open_source. This rise is purely deferrals coming off: all four already recorded
        # their evidence, they were simply publishing none of it. Five rows each, four
        # products, +20 exactly - and the count is the check that no FIFTH product moved with
        # them, langgraph included.
        #
        # ui_api 160 -> 184 on the 2026-08-11 evidence sweep of that category. All five of its
        # deferrals came off and a newly-computed product publishes its whole openness evidence
        # set rather than none of it: continue and nextchat contribute five rows each, doubao
        # five, and deepseek-chat and meta-ai four apiece, those two recording no license.
        # litellm was already computed and gained nothing when its bare `gated` was evidenced.
        #
        # telemetry_observability 94 -> 99 on the 2026-08-12 evidence sweep of that category.
        # Exactly one deferral came off - langfuse, which now publishes its five openness rows
        # instead of none. agentops, langtrace and weave stayed deferred as conflicts and so
        # still publish nothing, however much evidence their score files now carry, and the
        # count is the check on that. The three bare-`gated` products in the category were
        # already computed: agenta and langwatch kept their 4 with the gate now evidenced, and
        # helicone moved 4 -> 5 on `core-gated:ungated`, none of which adds or removes a row.
        #
        # telemetry_observability 99 -> 112 when the last three came off on 2026-08-12. Each
        # publishes its rows for the first time: agentops five (license, source, commercial,
        # core-gated and the normalized core_gated), langtrace four and weave four. The
        # category now defers nothing.
        #
        # orchestration_agents 210 -> 215 when openhands, its last deferral, closed on
        # 2026-08-12. Its gate had been recorded under `enterprise-dir`, a key the ladder does
        # not read; a repo read confirmed the enterprise directory is carved out to PolyForm
        # Free Trial 1.0.0 while the core stays MIT, `core-gated: gated` was transcribed, and
        # the recorded 4/open_core reproduces. Five rows, and the category now defers nothing.
        #
        # ui_api 184 -> 196 when both of its remaining deferrals closed on 2026-08-12, six rows
        # each. Neither was the conflict its reason claimed: maple-ai and privatemode had both
        # been abstaining on an unanswered dimension since #201 and #203, not disagreeing with
        # a computed score. maple-ai gained `core-gated: ungated` on a read of the Maple and
        # OpenSecret repos, whose billing and feature-flag services are optional external
        # clients; privatemode gained `source: partial`, its recorded `TCB-public` having been
        # outside the dimension's enum. Both reproduce the score they carried. The category now
        # defers nothing.
        "orchestration_agents": 215, "telemetry_observability": 114, "ui_api": 221,
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
        # benchmark_eval_data held at 111: compar-ia-datasets got the same `dataset_card`
        # key and stays deferred on its unrelated gate-vocabulary defect.
        # 111 -> 125 when the card read closed mt-bench and livebench. Each recorded a
        # license and an answer state and nothing else, and each gained a `datasheet` and an
        # `access` key plus the `availability` and `documentation` dimensions they normalize
        # onto - so both go from publishing nothing to publishing seven rows.
        # 125 -> 154 when the owner's rulings of 2026-08-12 closed five of the seven
        # deferrals here. gaia, humanitys-last-exam, compar-ia-datasets, math and
        # swe-bench-verified each start publishing their whole openness evidence set, having
        # published none of it while deferred. livecodebench and multipl-e stay deferred and
        # so still publish nothing, which is what keeps the rise to those five.
        "training_synthetic_datasets": 197, "benchmark_eval_data": 184,
        # safeguards 90 -> 103 and training_synthetic_datasets 158 -> 164: the universal
        # license scale retired five deferrals, and a deferred product publishes no
        # openness evidence at all.
        # safeguards 103 -> 117 when the four guardrail-model deferrals came off. Each of
        # qwen3guard, granite-guardian, gpt-oss-safeguard and wildguard dropped from a
        # recorded 4 to the 3 the ladder computes, and a product that no longer defers
        # publishes its component keys. wildguard carries four of the fourteen rows because
        # the read that settled it added `code:partial` to the three keys it already had.
        # safeguards 117 -> 123 when llamafirewall, its last deferral, closed on 2026-08-12 on
        # the ruling that a product is scored on the artifact it ships rather than on what it
        # can load. Its MIT facts had been sitting under `framework` and `self-host`;
        # transcribing `source` and `license` reproduces the recorded 5/open_source, and the
        # six rows it now publishes include the `framework` and `note` keys it already carried.
        # The category now defers nothing.
        "safeguards": 123,
        # 17 scored hardware products across the five recorded dimensions, less the keys
        # individual products do not record. No license row among them, by design -
        # `edge_hardware` is the only category whose ladder declares no `license_tier`.
        #
        # 83 -> 90 when raspberry-pi-ai-hat-plus's deferral closed on 2026-08-12. It had been
        # publishing nothing while deferred and now publishes its six recorded keys plus the
        # new `accessory-host`, which is the dimension that reproduces its 4: an accessory
        # tracks the platform it completes.
        #
        # 90 -> 95 the same day when arduino-uno-q moved 3/documented to the 5/open_hardware
        # the ladder computes, on openly licensed CC-BY-SA 4.0 design files - the same
        # `schematics: open` as beagley-ai. Five rows, from none while deferred.
        # rockchip-rk3588 stays deferred pending the form_factor proposal (#219) and so still
        # publishes nothing, which is what holds the rise to the one product.
        "edge_hardware": 95,
        # compilers and storage joined on 2026-08-18, promoted from the tail registry with 26
        # and 27 products. Both inherit the shared software ladder and both record the same three
        # dimensions per product, so the row count runs close to 4 x products, short of it because
        # tensorrt records no `core-gated` at all (a `partial` source has nothing to gate) and the
        # two deferred products, liger-kernel and pgvector, publish no openness evidence.
        #
        # storage was 94 on 24 products and agent_tools_protocols 138 on 32. Moving qdrant, milvus
        # and pinecone from the second to the first shifted 14 rows with them, which is more than
        # three products' worth of the shared ladder's three dimensions: those three records carry
        # extra recorded keys the ladder reads or reports, `managed-tier` among them.
        #
        # Both then rose by 4 when the `osi` tier gained BSD-2-Clause and PostgreSQL and the two
        # deferrals closed. A deferred product publishes no openness evidence at all, so closing
        # one adds its whole recorded set at once, and that set is four rows rather than the three
        # dimensions it records: `source`, the resolved `core_gated`, `license`, and `core-gated`
        # again under the hyphenated key the record actually uses. Verified by reading the emitted
        # rows for liger-kernel and pgvector rather than by inferring it from the count.
        #
        # storage rose 112 -> 160 with the Round 2 promotion: 12 products in
        # (weaviate, orama, paradedb, diskann, sptag, openmldb, quilt, oxen, lakesoul,
        # pixeltable, lamindb, redisearch), each recording the same four rows as every other
        # product on the shared software ladder (`source`, the resolved `core_gated`,
        # `license`, and `core-gated` again under the hyphenated key), 12 x 4 = 48.
        "compilers": 102, "storage": 160,
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
    #
    # epoch-ai-benchmarks and scale-evaluation joined them on the 2026-08-11 evidence sweep,
    # which recorded the `source` key their deferrals were waiting on and no license: `partial`
    # and `closed` are settled by rungs 1 and 0, and neither rung tests a tier, so there was
    # nothing to map a license for.
    unlicensed = {
        ("chatbot-arena", "evaluation_code"),
        ("patronus-evaluation-platform", "evaluation_code"),
        ("artificial-analysis-intelligence-index", "evaluation_code"),
        ("epoch-ai-benchmarks", "evaluation_code"),
        ("scale-evaluation", "evaluation_code"),
        # deepseek-chat and meta-ai joined on the ui_api sweep for the same reason: both are
        # hosted assistants recording `source: closed`, decided by rung 0, which tests no tier.
        # doubao is not here because it happens to record `license: Proprietary` as well.
        ("deepseek-chat", "ui_api"),
        ("meta-ai", "ui_api"),
    }
    assert unlicensed <= scored, "a pinned no-license product stopped scoring"
    missing = scored - licensed
    assert missing == unlicensed, f"no license row emitted for: {sorted(missing - unlicensed)}"

    deepseek = [r for r in rows if r["product_slug"] == "deepseek-coder" and r["dimension"] == "license"]
    assert len(deepseek) == 1 and deepseek[0]["value"] == "DeepSeek-Model-License"


def test_a_compound_license_publishes_every_part():
    """The three products check_parity was diverging on, and the one that must NOT split.

    `serialize_rubric` used to publish the license through `split_value`, which severs a
    clause at the first `(`. `zed` went out as `GPL-3.0-or-later` alone and the warehouse
    resolved a tier for a third of the license; `flan-collection`, `smoltalk` and
    `redpajama-data-v2` were the three products where that changed the published score.
    `check_rubric.license_tier` reads all the parts and takes the most restrictive, so the
    parts have to cross the bridge.

    `culturax` is the control. `follows mC4 + OSCAR-2301 terms` is one declared name with a
    `+` inside it — neither operand is a license — and the curator recorded it as a single
    part. A serializer that split on punctuation cannot tell it from `zed`; one that
    publishes what the record says does not have to.
    """
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing

    root = Path(__file__).resolve().parents[1]
    tables, _, _ = build_rubric(_real_sources(root), load_policy(root), load_routing(root))

    def license_parts(product):
        return [
            r["value"]
            for r in sorted(
                (
                    r
                    for r in tables["product_openness_evidence"]
                    if r["product_slug"] == product and r["dimension"] == "license"
                ),
                key=lambda r: r["part_index"],
            )
        ]

    assert license_parts("zed") == ["GPL-3.0-or-later", "GPL-3.0", "Apache-2.0"]
    assert license_parts("flan-collection") == ["Apache-2.0", "per-task"]
    assert license_parts("smoltalk") == ["apache-2.0", "per-component"]
    assert license_parts("redpajama-data-v2") == ["CommonCrawl-ToU", "Apache-2.0"]
    assert license_parts("culturax") == ["follows mC4 + OSCAR-2301 terms"]


def test_evidence_never_puts_two_values_on_one_grain():
    """One product/category/dimension/part must carry one value. Two would let the
    warehouse pick between a base corpus and a post-training mixture by row order.

    `part_index` is in the grain because the license is a LIST — twelve products record a
    compound one and each part gets a row, so the warehouse can resolve every part and take
    the most restrictive. Every other dimension answers once and pins the index at 0, which
    this asserts separately: a dimension that started emitting a second row would otherwise
    hide behind the license's allowance.
    """
    from collections import Counter
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing

    root = Path(__file__).resolve().parents[1]
    tables, _, _ = build_rubric(_real_sources(root), load_policy(root), load_routing(root))
    rows = tables["product_openness_evidence"]

    counts = Counter(
        (r["product_slug"], r["category_slug"], r["dimension"], r["part_index"]) for r in rows
    )
    assert [key for key, n in counts.items() if n > 1] == []
    assert [r for r in rows if r["dimension"] != "license" and r["part_index"] != 0] == []
    # Contiguous from zero, because the index is the recorded order and the warehouse joins
    # the names back together in it to report which license it could not map.
    parts = Counter(
        (r["product_slug"], r["category_slug"]) for r in rows if r["dimension"] == "license"
    )
    for (product, category), n in parts.items():
        indexes = sorted(
            r["part_index"]
            for r in rows
            if r["dimension"] == "license"
            and r["product_slug"] == product
            and r["category_slug"] == category
        )
        assert indexes == list(range(n)), f"{product}/{category} part indexes are {indexes}"


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


def test_route_scales_are_declared_once_per_instrument_and_stars_stay_capped():
    """Some scales are per INSTRUMENT, not per product type.

    A dataset's downloads run an order below a package's, which is why THOSE bands are per
    type. A star is a star whatever it was given to, and a monthly active user is a person
    whatever they came back to — so both are declared once on their route in
    signal_routing.yaml and emitted with product_type '*'. Four copies in four rubrics is
    exactly the drift this whole table exists to stop.
    """
    import yaml
    from pathlib import Path

    from build.serialize_rubric import route_bands

    routing = yaml.safe_load(Path("sources/signal_routing.yaml").read_text())
    rows, warnings = route_bands(routing)

    assert warnings == []
    assert {r["product_type"] for r in rows} == {"*"}
    assert {r["signal_type"] for r in rows} == {"stars_fallback", "active_users"}

    # Capped at 3: stars measure attention rather than use, so a stars-derived band may
    # never claim the top two levels however large the count.
    stars = [r for r in rows if r["signal_type"] == "stars_fallback"]
    assert max(r["level"] for r in stars) == 3
    assert sorted(r["above"] for r in stars) == [-1, 1000, 10000]

    # active_users measures use directly, so unlike stars it has no ceiling. Its thresholds
    # are deliberately the download scale's, so that a level means one magnitude map-wide.
    users = [r for r in rows if r["signal_type"] == "active_users"]
    assert max(r["level"] for r in users) == 5
    assert sorted(r["above"] for r in users) == [-1, 10_000, 100_000, 1_000_000, 10_000_000]

    # Every row carries the unit its band was read in. A band with no unit is the ambiguity
    # that let the download vocabulary colonize active_users in the first place.
    assert all(r["unit"] for r in rows), rows


def test_a_stars_band_above_the_cap_is_dropped_with_a_warning():
    """The cap is enforced, not trusted. A later edit adding a level-4 stars band should
    fail the serializer rather than quietly publish one."""
    from build.serialize_rubric import route_bands

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
    rows, warnings = route_bands(routing)
    assert [r["level"] for r in rows] == [3]
    assert any("exceeds the declared cap" in w for w in warnings)


def test_download_bands_and_route_bands_do_not_collide():
    """All three scales live in one table, distinguished by signal_type. A consumer joining
    without filtering on it would band a package's downloads against the stars scale."""
    from pathlib import Path

    import yaml

    from build.serialize_rubric import adoption_bands, route_bands
    from build.validate import load_sources

    downloads, _ = adoption_bands(load_sources(Path(".")).get("rubrics") or {})
    per_instrument, _ = route_bands(
        yaml.safe_load(Path("sources/signal_routing.yaml").read_text())
    )

    assert {r["signal_type"] for r in downloads} == {"usage_volume"}
    assert all(r["product_type"] != "*" for r in downloads)
    rows = downloads + per_instrument
    keys = {(r["product_type"], r["signal_type"], r["level"]) for r in rows}
    assert len(keys) == len(rows), "a (type, instrument, level) key repeats"

    # And no reach LABEL is shared across instruments either. The key above keeps the
    # warehouse unambiguous; this keeps a human reading a score's `reach` unambiguous, which
    # is the half that failed — a bare `1M-10M` meant downloads on one record and users on
    # another, and that ambiguity is how the download vocabulary spread to an instrument it
    # does not measure.
    by_label: dict[str, set[str]] = {}
    for row in rows:
        by_label.setdefault(row["reach"], set()).add(row["signal_type"])
    ambiguous = {reach: sorted(kinds) for reach, kinds in by_label.items() if len(kinds) > 1}
    assert not ambiguous, f"a reach label means different things on different scales: {ambiguous}"


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
