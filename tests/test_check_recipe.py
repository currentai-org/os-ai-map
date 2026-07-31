"""Tests for the recipe gate.

Each assertion gets a synthetic recipe that violates it and one that does not, because a
gate is only worth having if it has been seen to fail. The last test runs `--all` against
the repo's real sources and asserts it exits clean: that is the regression guard, and it is
what fails when someone lands a recipe without a `because`.
"""

import pytest

from build.check_recipe import (
    check_recipe,
    clauses_parse,
    every_dimension_has_a_machine_signal,
    every_rung_has_a_because,
    license_tier_order_is_explicit,
    no_unreachable_rule,
    split_clauses,
    undeclared_keys_holding_evidence,
)

# A structurally complete, passing recipe. Each test below mutates a copy, so the fixture
# doubles as the negative control for every assertion.
GOOD = {
    "version": 1,
    "openness": {
        "dimensions": {
            "source": {
                "question": "Is the source published?",
                "values": ["public", "closed"],
                "machine_signal": "partial - repo presence from signal_github.repo_state",
            },
        },
        "license_tier": {
            "ordered_by": "restrictiveness_ascending",
            "values": {
                "osi": {"examples": ["MIT"]},
                "proprietary": {"definition": "no public license"},
            },
        },
        "formula": [
            {
                "when": {"source": "closed"},
                "then": {"score": 1, "class": "closed"},
                "because": "Nothing published, so the license cannot help.",
            },
            {
                "when": {"source": "public", "license_tier": "osi"},
                "then": {"score": 5, "class": "open_source"},
                "because": "The published source is the whole product.",
            },
        ],
    },
}


def _mutate(**openness):
    recipe = {"version": 1, "openness": {**GOOD["openness"], **openness}}
    return recipe


def test_split_clauses_keeps_the_colonless_ones_the_parser_drops():
    """`split_components` discards a clause with no colon; this must retain it.

    The whole point of the clause assertion is to see what the parser threw away, so it
    cannot reuse the parser.
    """
    from build.check_rubric import split_components

    text = "license:MIT(OSI; see LICENSE);no feature-gated core;source:public"
    assert split_components(text) == {"license": "MIT(OSI; see LICENSE)", "source": "public"}
    assert split_clauses(text) == [
        "license:MIT(OSI; see LICENSE)",
        "no feature-gated core",
        "source:public",
    ]


def test_a_rung_without_a_because_fails():
    assert every_rung_has_a_because("cat", GOOD) == []
    formula = [dict(GOOD["openness"]["formula"][0]), {"otherwise": {"score": 3, "class": "x"}}]
    problems = every_rung_has_a_because("cat", _mutate(formula=formula))
    assert len(problems) == 1
    assert "rule 1" in problems[0]


def test_a_note_does_not_satisfy_the_because_requirement():
    """One field, one name. `note` was the other spelling and it has been migrated."""
    formula = [{"when": {"source": "closed"}, "then": {"score": 1, "class": "closed"},
                "note": "reads like a justification but is not the declared key"}]
    assert len(every_rung_has_a_because("cat", _mutate(formula=formula))) == 1


def test_an_empty_because_fails_like_a_missing_one():
    formula = [{"when": {"source": "closed"}, "then": {"score": 1, "class": "closed"},
                "because": "   "}]
    assert len(every_rung_has_a_because("cat", _mutate(formula=formula))) == 1


def test_a_dimension_without_a_machine_signal_fails():
    assert every_dimension_has_a_machine_signal("cat", GOOD) == []
    dimensions = {"source": {"question": "?", "values": ["public"]}}
    problems = every_dimension_has_a_machine_signal("cat", _mutate(dimensions=dimensions))
    assert len(problems) == 1
    assert "source" in problems[0]


def test_a_rule_after_an_otherwise_is_unreachable():
    assert no_unreachable_rule("cat", GOOD) == []
    formula = [
        {"otherwise": {"score": 3, "class": "open_weights"}, "because": "fallthrough"},
        {"when": {"source": "closed"}, "then": {"score": 1, "class": "closed"}, "because": "dead"},
    ]
    problems = no_unreachable_rule("cat", _mutate(formula=formula))
    assert len(problems) == 1
    assert "rule 1" in problems[0] and "otherwise" in problems[0]


def test_a_rule_testing_an_undeclared_dimension_is_unreachable():
    formula = [
        {"when": {"governance": "foundation"}, "then": {"score": 4, "class": "x"},
         "because": "cannot fire"},
    ]
    problems = no_unreachable_rule("cat", _mutate(formula=formula))
    assert any("governance" in p for p in problems)


def test_a_rule_testing_a_value_outside_the_declared_enum_is_unreachable():
    formula = [
        {"when": {"source": "partial"}, "then": {"score": 2, "class": "source_available"},
         "because": "partial is not declared"},
    ]
    problems = no_unreachable_rule("cat", _mutate(formula=formula))
    assert any("partial" in p for p in problems)


def test_multiple_tiers_without_an_explicit_order_fails():
    assert license_tier_order_is_explicit("cat", GOOD) == []
    tier = {"values": GOOD["openness"]["license_tier"]["values"]}  # no ordered_by
    problems = license_tier_order_is_explicit("cat", _mutate(license_tier=tier))
    assert len(problems) == 1


def test_a_single_tier_needs_no_declared_order():
    """`tier_rank` is only meaningful when there is something to compare against."""
    tier = {"values": {"osi": {"examples": ["MIT"]}}}
    assert license_tier_order_is_explicit("cat", _mutate(license_tier=tier)) == []


def test_a_tier_free_ladder_does_not_crash():
    """Hardware openness turns on design and toolchain, not a source license.

    `check_rubric` cannot yet score such a ladder, but the gate must not be what blocks one
    from being written.
    """
    openness = {k: v for k, v in GOOD["openness"].items() if k != "license_tier"}
    recipe = {"version": 1, "openness": openness}
    assert license_tier_order_is_explicit("cat", recipe) == []
    assert every_rung_has_a_because("cat", recipe) == []


class TestClausesParse:
    """The three-way scoping: fail, report, count.

    Naively asserting that every clause parses fails 166 products, and a gate that fails on
    day one gets switched off. Only a clause that is the ONLY record of a dimension some rung
    actually tests can block.
    """

    def test_a_colonless_clause_holding_a_tested_dimension_blocks(self):
        blocking, reported, total = clauses_parse(
            "cat", GOOD, {"p": "no public source shipped"}, deferred=set()
        )
        assert total == 1
        assert len(blocking) == 1 and "p" in blocking[0]
        assert reported == []

    def test_the_same_clause_only_reports_when_the_product_is_deferred(self):
        blocking, reported, total = clauses_parse(
            "cat", GOOD, {"p": "no public source shipped"}, deferred={"p"}
        )
        assert blocking == []
        assert len(reported) == 1

    def test_a_clause_beside_a_properly_keyed_value_is_only_counted(self):
        """`no feature-gated core;core-gated:ungated` is redundant prose, not lost evidence."""
        blocking, reported, total = clauses_parse(
            "cat", GOOD, {"p": "source:public;no source published"}, deferred=set()
        )
        assert blocking == [] and reported == []
        assert total == 1

    def test_the_matcher_reads_declared_values_not_dimension_names(self):
        """A clause naming the dimension but no value answers nothing.

        The real cases match on the value: `no-feature-gated-core` hits `core_gated`'s
        `gated`, and `dataset card present` hits `documentation`'s `present`.
        """
        blocking, reported, total = clauses_parse(
            "cat", GOOD, {"p": "source unavailable"}, deferred=set()
        )
        assert blocking == [] and reported == []
        assert total == 1

    def test_a_clause_matching_nothing_is_only_counted(self):
        blocking, reported, total = clauses_parse(
            "cat", GOOD, {"p": "source:public;built on ggml"}, deferred=set()
        )
        assert blocking == [] and reported == []
        assert total == 1

    def test_a_clause_holding_a_dimension_no_rung_tests_only_reports(self):
        """`base_pretrained/ernie` is this shape: `checkpoints` is declared and untested."""
        dimensions = {
            **GOOD["openness"]["dimensions"],
            "checkpoints": {"question": "?", "values": ["released", "none"],
                            "machine_signal": "none"},
        }
        blocking, reported, total = clauses_parse(
            "cat", _mutate(dimensions=dimensions),
            {"p": "source:public;no checkpoints released"}, deferred=set(),
        )
        assert blocking == []
        assert len(reported) == 1


class TestUndeclaredKeys:
    """Scoped like the clause check, and for the same reason.

    113 distinct undeclared keys exist across 384 recordings (`self-host` alone appears 52
    times). Gating all of them fails on day one; declaring all of them is a curation project.
    Only a key whose VALUE answers a dimension the formula tests, where nothing else does,
    is a defect — the ladder reads that dimension as unrecorded while the answer sits in the
    file under another name.
    """

    def test_a_synonym_holding_the_only_answer_blocks(self):
        """`ornith` was this: `recipe:closed` and nothing under `code`."""
        blocking, reported, count = undeclared_keys_holding_evidence(
            "cat", GOOD, {"p": "src-tree:public"}, deferred=set()
        )
        assert len(blocking) == 1 and "src-tree" in blocking[0]
        assert count == 1

    def test_the_same_synonym_only_reports_when_deferred(self):
        blocking, reported, _ = undeclared_keys_holding_evidence(
            "cat", GOOD, {"p": "src-tree:public"}, deferred={"p"}
        )
        assert blocking == [] and len(reported) == 1

    def test_a_synonym_beside_a_readable_answer_is_only_counted(self):
        blocking, reported, count = undeclared_keys_holding_evidence(
            "cat", GOOD, {"p": "source:public;src-tree:public"}, deferred=set()
        )
        assert blocking == [] and reported == []
        assert count == 1

    def test_a_context_key_whose_value_answers_nothing_is_only_counted(self):
        """`rows`, `size`, `format`, `github` — context, not openness questions."""
        blocking, reported, count = undeclared_keys_holding_evidence(
            "cat", GOOD, {"p": "source:public;rows:1M;size:940MB"}, deferred=set()
        )
        assert blocking == [] and reported == []
        assert count == 2

    def test_a_key_in_a_dimensions_reads_list_is_declared(self):
        dimensions = {
            "source": {"question": "?", "values": ["public", "closed"],
                       "reads": ["source", "src"], "machine_signal": "none"},
        }
        blocking, _, count = undeclared_keys_holding_evidence(
            "cat", _mutate(dimensions=dimensions), {"p": "src:public"}, deferred=set()
        )
        assert blocking == [] and count == 0

    def test_the_license_read_keys_are_declared(self):
        tier = {**GOOD["openness"]["license_tier"], "reads": ["license", "license-terms"]}
        blocking, _, count = undeclared_keys_holding_evidence(
            "cat", _mutate(license_tier=tier), {"p": "license-terms:MIT"}, deferred=set()
        )
        assert blocking == [] and count == 0


def test_reproduction_rate_is_never_asserted():
    """The one rule above the others.

    A gate that rewards a high reproduction rate turns the ladder into a curve fit to the
    scores it exists to check. `safeguards` reproduced 0 of 26 and that was correct. Asserted
    by reading the module source, because the failure mode is someone adding the check later
    in good faith.
    """
    import inspect

    import build.check_recipe as module

    source = inspect.getsource(module)
    for banned in ("reproduction_rate", "min_reproduced", "MIN_REPRODUCTION", "rate <", "rate >"):
        assert banned not in source, f"check_recipe must not threshold reproduction ({banned})"


@pytest.mark.parametrize("slug", [None])
def test_the_real_sources_pass_the_gate(slug):
    """The regression guard. Anything this catches is a real defect or an over-strict rule."""
    failures, _ = check_recipe(slug)
    assert failures == [], "\n".join(failures)
