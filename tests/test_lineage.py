"""The component lineage registry and the pairwise statuses derived from it.

R-2026-11-02-h defines independence (distinct source examples, distinct creation efforts,
neither derived from the other), R-2026-11-02-i the three statuses, and R-2026-11-02-j and -u the
registry. The fixture in `tests/fixtures/lineage/registry.yaml` holds one component per rule, and
every invalid case below is that fixture with one thing broken, so a failure names the rule it
tests. docs/reference/capability.md, "Component lineage", is normative.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from build.lineage import (
    lineage_errors,
    lineage_warnings,
    load,
    pair_status,
    qualifying_components,
)
from build.vocabulary import language_codes

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "lineage" / "registry.yaml"
LANGS = set(language_codes())


@pytest.fixture
def doc() -> dict:
    return yaml.safe_load(FIXTURE.read_text())


def component(doc: dict, cid: str) -> dict:
    return next(c for c in doc["components"] if c["id"] == cid)


def test_fixture_is_valid(doc):
    assert lineage_errors(doc, allowed_languages=LANGS) == []


def test_real_registry_is_valid():
    assert lineage_errors(load(), allowed_languages=LANGS) == []


# --- derived statuses -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, language, status, reason",
    [
        # FLORES and SIB-200 share FLORES-200's sentences: SIB-200 derives from FLORES+.
        ("flores-plus", "sib-200", "hau", "dependent", "derived"),
        # Transitive: a suite's task that re-hosts SIB-200 still depends on FLORES+.
        ("example-suite-topic", "flores-plus", "hau", "dependent", "derived"),
        # Unrelated source collections and separate efforts.
        ("flores-plus", "ntrex-128", "hau", "independent", "disjoint"),
        # Same broad domain (Wikipedia), separately sampled articles: not dependent.
        ("wiki-qa-a", "wiki-qa-b", "yor", "independent", "disjoint"),
        # Batayan shares FLORES's domains but states no origin: unverified, not dependent.
        ("batayan", "flores-plus", "fil", "unverified", "origin_unknown"),
        # A component with no entry, and one whose entry is a placeholder.
        ("flores-plus", "not-in-registry", "hau", "unverified", "not_in_registry"),
        ("flores-plus", "example-uncurated", "hau", "unverified", "not_curated"),
        ("flores-plus", "flores-plus", "hau", "dependent", "same_component"),
    ],
)
def test_pair_status(doc, a, b, language, status, reason):
    got = pair_status(doc, a, b, language)
    assert (got.status, got.reason) == (status, reason)
    # Symmetric: the order of the pair never changes the answer.
    assert pair_status(doc, b, a, language).status == status


def test_language_override_changes_one_language_only(doc):
    # example-mt's Hausa side shares the FLORES translators; its Yoruba side does not.
    assert pair_status(doc, "example-mt", "flores-plus", "hau").reason == "shared_effort"
    assert pair_status(doc, "example-mt", "flores-plus", "yor").status == "independent"


def test_shared_collection_is_dependence(doc):
    d = copy.deepcopy(doc)
    component(d, "ntrex-128")["collections"] = ["newstest2019", "flores-200"]
    got = pair_status(d, "ntrex-128", "flores-plus", "hau")
    assert (got.status, got.reason, got.detail) == ("dependent", "shared_collection", "flores-200")


def test_domains_never_create_dependence(doc):
    d = copy.deepcopy(doc)
    component(d, "ntrex-128")["domains"] = ["wikinews", "wikijunior", "wikivoyage"]
    assert pair_status(d, "ntrex-128", "flores-plus", "hau").status == "independent"


def test_explicit_relationship_takes_precedence_for_its_languages(doc):
    got = pair_status(doc, "wiki-qa-a", "wiki-qa-b", "swh")
    assert (got.status, got.reason) == ("dependent", "explicit")
    assert pair_status(doc, "wiki-qa-a", "wiki-qa-b", "yor").status == "independent"


def test_known_dependence_wins_over_unknown_origin(doc):
    # A stated derivation is dependence even when the child's own origin is otherwise unknown.
    d = copy.deepcopy(doc)
    component(d, "batayan")["parents"] = ["flores-plus"]
    assert pair_status(d, "batayan", "flores-plus", "fil").reason == "derived"


def test_missing_effort_is_unverified(doc):
    d = copy.deepcopy(doc)
    component(d, "ntrex-128")["effort"] = None
    got = pair_status(d, "ntrex-128", "flores-plus", "hau")
    assert (got.status, got.reason) == ("unverified", "origin_unknown")


def test_each_component_is_resolved_in_its_own_task(doc):
    # Regression: one task for both sides applied example-suite-own's exam override to the wrong
    # component, or skipped it. The exam items share the FLORES translators; its other items don't.
    exam = pair_status(doc, "example-suite-own", "flores-plus", "hau",
                       a_task="knowledge_exam", b_task="machine_translation", b_split="devtest")
    assert (exam.status, exam.reason) == ("dependent", "shared_effort")
    other = pair_status(doc, "example-suite-own", "flores-plus", "hau",
                        a_task="instruction_following", b_task="machine_translation")
    assert other.status == "independent"
    # The same pair read the other way round gives the same answer.
    flipped = pair_status(doc, "flores-plus", "example-suite-own", "hau",
                          a_task="machine_translation", b_task="knowledge_exam")
    assert flipped.status == "dependent"


def test_unknown_ancestor_makes_the_pair_unverified(doc):
    # child-of-batayan documents its own effort, but its parent's origin is unknown, so its
    # provenance is not documented all the way up.
    got = pair_status(doc, "child-of-batayan", "ntrex-128", "fil")
    assert (got.status, got.reason, got.detail) == ("unverified", "origin_unknown", "batayan")


def test_known_overlap_still_wins_over_an_unknown_ancestor(doc):
    d = copy.deepcopy(doc)
    component(d, "child-of-batayan")["collections"] = ["newstest2019"]
    got = pair_status(d, "child-of-batayan", "ntrex-128", "fil")
    assert (got.status, got.reason) == ("dependent", "shared_collection")


def test_known_derivation_wins_over_an_uncurated_entry(doc):
    # Regression: the uncurated early return ran before the derivation check, so a component
    # paired with its own stated parent read as unverified rather than dependent.
    got = pair_status(doc, "child-of-uncurated", "example-uncurated", "hau")
    assert (got.status, got.reason) == ("dependent", "derived")


def test_known_derivation_wins_over_a_missing_entry(doc):
    d = copy.deepcopy(doc)
    component(d, "child-of-uncurated")["parents"] = ["not-in-registry"]
    got = pair_status(d, "child-of-uncurated", "not-in-registry", "hau")
    assert (got.status, got.reason) == ("dependent", "derived")


def test_uncurated_ancestor_makes_the_pair_unverified(doc):
    got = pair_status(doc, "child-of-uncurated", "ntrex-128", "hau")
    assert (got.status, got.reason, got.detail) == ("unverified", "not_curated", "example-uncurated")


# --- structural validation --------------------------------------------------------------------


def broken(doc: dict, change) -> list[str]:
    d = copy.deepcopy(doc)
    change(d)
    return lineage_errors(d, allowed_languages=LANGS)


def test_unknown_parent(doc):
    errs = broken(doc, lambda d: component(d, "sib-200").update(parents=["no-such-set"]))
    assert any("parent 'no-such-set' is not a component" in e for e in errs)


def test_unknown_collection(doc):
    errs = broken(doc, lambda d: component(d, "ntrex-128").update(collections=["no-such-collection"]))
    assert any("collection 'no-such-collection' is not a collection" in e for e in errs)


def test_parent_cycle(doc):
    errs = broken(doc, lambda d: component(d, "flores-plus").update(parents=["example-suite-topic"]))
    assert any("parents form a cycle" in e for e in errs)


def test_curated_entry_needs_sources(doc):
    errs = broken(doc, lambda d: component(d, "ntrex-128").update(sources=[]))
    assert any("'ntrex-128': is curated but cites no sources" in e for e in errs)


def test_original_origin_needs_a_collection(doc):
    errs = broken(doc, lambda d: component(d, "wiki-qa-a").update(collections=[]))
    assert any("origin original names no collection" in e for e in errs)


def test_derived_origin_needs_a_parent_or_collection(doc):
    errs = broken(doc, lambda d: component(d, "sib-200").update(parents=[]))
    assert any("origin derived names no parent and no collection" in e for e in errs)


def test_duplicate_component_id(doc):
    errs = broken(doc, lambda d: d["components"].append(copy.deepcopy(component(d, "ntrex-128"))))
    assert any("id 'ntrex-128' appears more than once" in e for e in errs)


def test_override_language_must_be_iso_639_3(doc):
    errs = broken(doc, lambda d: component(d, "example-mt")["overrides"][0].update(languages=["xqz"]))
    assert any("language 'xqz' is not an ISO 639-3 code" in e for e in errs)


def test_overlapping_overrides_are_refused(doc):
    # A language override and a task override that can both match one context are ambiguous.
    def change(d):
        component(d, "example-suite-own")["overrides"].append(
            {"languages": ["hau"], "effort": "someone-else",
             "sources": component(d, "example-suite-own")["sources"]})
    errs = broken(doc, change)
    assert any("overrides[0] and overrides[1] can both match" in e for e in errs)


def test_disjoint_overrides_are_accepted(doc):
    def change(d):
        component(d, "example-suite-own")["overrides"].append(
            {"tasks": ["instruction_following"], "effort": "someone-else",
             "sources": component(d, "example-suite-own")["sources"]})
    assert broken(doc, change) == []


def test_override_task_must_be_a_task_class(doc):
    errs = broken(doc, lambda d: component(d, "example-suite-own")["overrides"][0].update(tasks=["exam"]))
    assert any("task 'exam' is not a task class" in e for e in errs)


def test_relationship_needs_a_citation(doc):
    errs = broken(doc, lambda d: d["relationships"][0].update(sources=[]))
    assert any("schema" in e for e in errs)


def test_relationship_to_unknown_component(doc):
    errs = broken(doc, lambda d: d["relationships"][0].update(between=["wiki-qa-a", "no-such-set"]))
    assert any("'no-such-set' is not a component" in e for e in errs)


def test_repeated_relationship(doc):
    errs = broken(doc, lambda d: d["relationships"].append(copy.deepcopy(d["relationships"][0])))
    assert any("overlaps relationships[0]" in e for e in errs)


def test_relationships_with_overlapping_languages_are_refused(doc):
    # [swh, yor] and [swh] both speak for Swahili; the answer would depend on file order.
    def change(d):
        extra = copy.deepcopy(d["relationships"][0])
        extra.update(status="independent", languages=["swh", "yor"])
        d["relationships"].append(extra)
    assert any("overlaps relationships[0]" in e for e in broken(doc, change))


def test_unrestricted_relationship_overlaps_a_language_one(doc):
    def change(d):
        extra = copy.deepcopy(d["relationships"][0])
        extra.pop("languages")
        extra["status"] = "independent"
        d["relationships"].append(extra)
    assert any("overlaps relationships[0]" in e for e in broken(doc, change))


def test_relationships_for_disjoint_languages_are_accepted(doc):
    def change(d):
        extra = copy.deepcopy(d["relationships"][0])
        extra.update(status="independent", languages=["yor"])
        d["relationships"].append(extra)
    assert broken(doc, change) == []


def test_override_naming_the_component_as_its_own_parent_is_refused(doc):
    # Regression: an override could replace `parents` with the component itself and pass, and
    # the component then read as independent with no source examples at all.
    def change(d):
        component(d, "example-mt")["overrides"][0].update(origin="derived", collections=[],
                                                          parents=["example-mt"])
    errs = broken(doc, change)
    assert any("overrides[0]: names the component itself as a parent" in e for e in errs)


def test_cycle_introduced_by_an_override_is_refused(doc):
    def change(d):
        component(d, "flores-plus").setdefault("overrides", []).append(
            {"languages": ["hau"], "parents": ["example-suite-topic"],
             "sources": component(d, "flores-plus")["sources"]})
    assert any("parents form a cycle" in e for e in broken(doc, change))


def test_override_origin_rules_apply_to_the_effective_record(doc):
    def change(d):
        component(d, "example-mt")["overrides"][0].update(origin="derived", collections=[])
    errs = broken(doc, change)
    assert any("overrides[0]: origin derived names no parent and no collection" in e for e in errs)


def test_undigested_source_is_refused(doc):
    errs = broken(doc, lambda d: component(d, "ntrex-128")["sources"][0].pop("content_sha256"))
    assert any("schema" in e for e in errs)


# --- warnings ---------------------------------------------------------------------------------


def scores_with(*components: str) -> dict:
    entries = [{"language": "hau", "task": "machine_translation", "component": c,
                "split": "official_eval", "official_eval": True, "count": 1} for c in components]
    entries.append({"language": "hau", "task": "machine_translation", "component": "a-dev-split",
                    "split": "dev", "official_eval": False, "count": 1})
    return {"example": {"capability": {"language_coverage": entries}}}


def test_qualifying_components_reads_official_entries_only():
    assert qualifying_components(scores_with("flores-plus")) == {"flores-plus"}


def test_missing_entries_warn_and_never_fail(doc):
    warns = lineage_warnings(doc, scores_with("flores-plus", "not-in-registry"))
    assert len(warns) == 1 and "1 coverage component(s)" in warns[0] and "not-in-registry" in warns[0]
    assert lineage_errors(doc, allowed_languages=LANGS) == []


def test_no_warning_when_every_component_has_an_entry(doc):
    assert lineage_warnings(doc, scores_with("flores-plus", "ntrex-128")) == []
