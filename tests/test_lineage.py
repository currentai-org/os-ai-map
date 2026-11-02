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


def test_relationship_needs_a_citation(doc):
    errs = broken(doc, lambda d: d["relationships"][0].update(sources=[]))
    assert any("schema" in e for e in errs)


def test_relationship_to_unknown_component(doc):
    errs = broken(doc, lambda d: d["relationships"][0].update(between=["wiki-qa-a", "no-such-set"]))
    assert any("'no-such-set' is not a component" in e for e in errs)


def test_repeated_relationship(doc):
    errs = broken(doc, lambda d: d["relationships"].append(copy.deepcopy(d["relationships"][0])))
    assert any("repeats a relationship" in e for e in errs)


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
