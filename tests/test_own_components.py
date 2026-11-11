"""`capability.own_components`: which coverage entries are a suite's own items (R-2026-11-03-c, -i).

The matching and the validation live in `build/own_components.py`; the shape rules (mutually
exclusive language selectors, non-empty selectors, `language_coverage` required beside the claims)
are the score schema's. docs/reference/capability.md, "Own components", is normative.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from build.own_components import (
    claim_matches,
    is_own,
    own_components_errors,
    without_mixed_pools,
    without_second_slugs,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
CAPABILITY = SCHEMA["properties"]["capability"]
PAPER = "https://example.org/suite-paper"


def entry(component, language, task="knowledge_exam", split="test"):
    return {"component": component, "language": language, "task": task, "split": split}


@pytest.fixture
def capability():
    return {
        "sources": [{"url": PAPER, "shows": "the suite wrote these", "accessed": "2026-11-07"}],
        "language_coverage": [
            entry("suite", "hau"), entry("suite", "yor"), entry("suite", "ara"),
            entry("suite-judge", "hau", task="text_generation"),
            entry("suite-judge", "yor", task="text_generation"),
            entry("imported-set", "hau"),
        ],
        "own_components": [
            {"component": "suite", "except_languages": ["ara"], "mixed_languages": ["yor"],
             "cites": [PAPER]},
            {"component": "suite-judge", "languages": ["hau"], "cites": [PAPER]},
        ],
    }


# --- matching ---------------------------------------------------------------------------------


def test_the_own_slug_is_own_by_default():
    assert is_own("suite", entry("suite", "hau"), [])
    assert not is_own("suite", entry("imported-set", "hau"), [])


def test_a_claim_on_the_own_slug_replaces_the_default(capability):
    claims = capability["own_components"]
    assert is_own("suite", entry("suite", "hau"), claims)
    assert not is_own("suite", entry("suite", "ara"), claims)


def test_a_second_slug_is_own_only_where_claimed(capability):
    claims = capability["own_components"]
    assert is_own("suite", entry("suite-judge", "hau", task="text_generation"), claims)
    assert not is_own("suite", entry("suite-judge", "yor", task="text_generation"), claims)
    assert not is_own("suite", entry("imported-set", "hau"), claims)


@pytest.mark.parametrize("claim, matches", [
    ({"component": "suite"}, True),
    ({"component": "other"}, False),
    ({"component": "suite", "languages": ["hau"]}, True),
    ({"component": "suite", "languages": ["yor"]}, False),
    ({"component": "suite", "except_languages": ["hau"]}, False),
    ({"component": "suite", "tasks": ["knowledge_exam"]}, True),
    ({"component": "suite", "tasks": ["machine_translation"]}, False),
    ({"component": "suite", "splits": ["test"]}, True),
    ({"component": "suite", "splits": ["dev"]}, False),
])
def test_claim_matches(claim, matches):
    assert claim_matches(claim, entry("suite", "hau")) is matches


def test_without_second_slugs_keeps_only_the_own_slug(capability):
    kept = without_second_slugs("suite", capability["own_components"])
    assert [c["component"] for c in kept] == ["suite"]


def test_without_mixed_pools_withdraws_the_mixed_languages(capability):
    claims = without_mixed_pools(capability["own_components"])
    assert not is_own("suite", entry("suite", "yor"), claims)
    assert is_own("suite", entry("suite", "hau"), claims)
    # A `languages` claim loses its mixed languages too.
    only = without_mixed_pools([{"component": "s", "languages": ["hau", "yor"],
                                 "mixed_languages": ["yor"]}])
    assert only[0]["languages"] == ["hau"]


# --- validation -------------------------------------------------------------------------------


def errors(capability, change=None):
    cap = copy.deepcopy(capability)
    if change:
        change(cap)
    return own_components_errors("suite", cap)


def test_the_fixture_is_valid(capability):
    assert errors(capability) == []


def test_a_component_with_no_coverage_entry(capability):
    errs = errors(capability, lambda c: c["own_components"][1].update(component="no-such-set"))
    assert any("no capability.language_coverage entry has component 'no-such-set'" in e
               for e in errs)


@pytest.mark.parametrize("key, value", [
    ("languages", ["swh"]), ("except_languages", ["swh"]),
    ("tasks", ["machine_translation"]), ("splits", ["dev"]),
])
def test_a_selector_that_matches_nothing(capability, key, value):
    def change(c):
        claim = c["own_components"][1]
        claim.pop("languages", None)
        claim[key] = value
    errs = errors(capability, change)
    assert any(f"{key} lists {value[0]!r}" in e for e in errs)


def test_selectors_that_together_match_nothing(capability):
    # Each value exists, but no entry has both: the judge set has no knowledge_exam entry.
    def change(c):
        c["own_components"][1]["tasks"] = ["knowledge_exam"]
        c["language_coverage"].append(entry("suite-judge", "ara", task="knowledge_exam"))
        c["own_components"][1]["languages"] = ["yor"]
    errs = errors(capability, change)
    assert any("its selectors match no coverage entry" in e for e in errs)


def test_mixed_languages_must_be_covered(capability):
    errs = errors(capability, lambda c: c["own_components"][0].update(mixed_languages=["ara"]))
    assert any("mixed_languages lists 'ara'" in e for e in errs)


def test_overlapping_claims(capability):
    def change(c):
        c["own_components"].append({"component": "suite-judge", "cites": [PAPER]})
    errs = errors(capability, change)
    assert any("overlaps" in e for e in errs)


def test_a_citation_that_resolves_to_no_source(capability):
    errs = errors(capability, lambda c: c["own_components"][0].update(cites=["https://x.org/y"]))
    assert any("is not the url of any capability.sources entry" in e for e in errs)


# --- schema -----------------------------------------------------------------------------------


OWN = CAPABILITY["properties"]["own_components"]


def claim_errors(claim):
    """Schema errors for a one-claim `own_components` list, checked against its own subschema so
    that an unrelated required field elsewhere in `capability` cannot make a test pass."""
    return [e.message for e in jsonschema.Draft202012Validator(OWN).iter_errors([claim])]


def test_the_schema_accepts_a_claim():
    assert claim_errors({"component": "suite", "cites": [PAPER]}) == []
    assert claim_errors({"component": "suite", "except_languages": ["ara"],
                         "mixed_languages": ["deu"], "tasks": ["knowledge_exam"],
                         "splits": ["test"], "cites": [PAPER]}) == []


def test_languages_and_except_languages_are_exclusive():
    claim = {"component": "suite", "languages": ["hau"], "except_languages": ["yor"],
             "cites": [PAPER]}
    assert claim_errors(claim)
    claim.pop("except_languages")
    assert claim_errors(claim) == []


@pytest.mark.parametrize("key", ["languages", "except_languages", "tasks", "splits",
                                 "mixed_languages", "cites"])
def test_an_empty_selector_is_refused(key):
    claim = {"component": "suite", "cites": [PAPER], key: []}
    assert claim_errors(claim)


def test_a_claim_needs_a_citation():
    assert claim_errors({"component": "suite"})


def test_own_components_needs_language_coverage():
    v = jsonschema.Draft202012Validator(CAPABILITY)
    without = [e for e in v.iter_errors({"own_components": [{"component": "suite", "cites": [PAPER]}]})
               if "language_coverage" in e.message]
    assert without
    with_coverage = [e for e in v.iter_errors({"own_components": [{"component": "suite",
                                                                     "cites": [PAPER]}],
                                               "language_coverage": [], "pivot_languages": []})
                     if "language_coverage" in e.message]
    assert with_coverage == []
