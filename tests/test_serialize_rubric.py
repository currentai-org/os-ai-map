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


def _sources(categories=None, scores=None):
    return {"categories": categories or {}, "scores": scores or {}}


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


def test_every_declared_table_is_present():
    tables, _, _ = build_rubric(_sources(categories={"base": {"scoring_recipe": RECIPE}}), POLICY, {})
    assert set(tables) == set(TABLES)


def test_real_sources_serialize_without_errors():
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing
    from build.validate import load_sources

    root = Path(__file__).resolve().parents[1]
    tables, errors, _ = build_rubric(load_sources(root), load_policy(root), load_routing(root))
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

    assert per_category("category_scoring_rules") == {"base_pretrained": 11, "finetuned_chat": 9}
    # Both fell with the slug migration: release-level products collapsed into the
    # tier the vendor sells, so 25 products left the roster and the closed frontier
    # models moved from base_pretrained to finetuned_chat.
    assert per_category("product_openness_evidence") == {"base_pretrained": 111, "finetuned_chat": 172}
    assert {r["grade"] for r in tables["product_openness_evidence"]} == {"document"}


def test_every_scored_product_carries_a_row_for_each_formula_dimension():
    """The warehouse joins a rule's `condition_key` against the `dimension` column,
    so a dimension recorded under a different key has to be emitted under the
    DIMENSION name. Emitted under the raw key instead, the condition silently fails
    to match and the product falls through to `otherwise` — scored on an absence.
    """
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing
    from build.validate import load_sources

    root = Path(__file__).resolve().parents[1]
    tables, _, _ = build_rubric(load_sources(root), load_policy(root), load_routing(root))

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


def test_license_is_emitted_under_the_name_the_warehouse_joins_on():
    """`license_tier.reads` lets a category accept the license under another key.

    deepseek-coder records `model-license`, because its card separates the code license
    from the one on the weights. check_rubric honours that list, but the serializer used
    to emit the row under its raw key, so the SQL - which looks only for
    `dimension = 'license'` - found nothing and the product abstained in the warehouse
    while reproducing locally. Exactly one license row per scored product, under
    `license`, is what keeps the two in step.
    """
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing
    from build.validate import load_sources

    root = Path(__file__).resolve().parents[1]
    tables, _, _ = build_rubric(load_sources(root), load_policy(root), load_routing(root))

    rows = tables["product_openness_evidence"]
    scored = {(r["product_slug"], r["category_slug"]) for r in rows}
    licensed = {(r["product_slug"], r["category_slug"]) for r in rows if r["dimension"] == "license"}
    assert scored - licensed == set(), f"no license row emitted for: {sorted(scored - licensed)}"

    deepseek = [r for r in rows if r["product_slug"] == "deepseek-coder" and r["dimension"] == "license"]
    assert len(deepseek) == 1 and deepseek[0]["value"] == "DeepSeek-Model-License"


def test_evidence_never_puts_two_values_on_one_grain():
    """One product/category/dimension must carry one value. Two would let the
    warehouse pick between a base corpus and a post-training mixture by row order.
    """
    from collections import Counter
    from pathlib import Path

    from build.serialize_rubric import load_policy, load_routing
    from build.validate import load_sources

    root = Path(__file__).resolve().parents[1]
    tables, _, _ = build_rubric(load_sources(root), load_policy(root), load_routing(root))

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
