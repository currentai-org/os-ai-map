"""`capability.language_coverage` and `capability.pivot_languages`: the per-language evidence.

One entry is one unit of evidence, a language x task x dataset component x split
(R-2026-11-01-c), and the pivots are declared once on the axis (R-2026-11-01-b). The valid record
lives in `tests/fixtures/language_coverage/valid.yaml`, and every invalid case here is that
record with one thing broken, so a failure names the one rule it tests. The shape rules (closed
vocabularies, non-negative counts, required fields, pivots required beside coverage) are the
score schema's; the cross-file and cross-entry rules (the code list, the product's `languages`,
the sort key, the official split, the qualifying portion, subsets, citations on
`capability.sources`) are `build.validate.language_coverage_errors`. Both run through
`validate_sources`, which is what preflight runs. docs/reference/capability.md, "Per-language
coverage", is normative.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest
import yaml

from build.serialize import PER_LANGUAGE_KEYS, _row, _without_language_coverage
from build.validate import COVERAGE_KEY, validate_sources

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "language_coverage" / "valid.yaml"
SCHEMA = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
CAPABILITY = SCHEMA["properties"]["capability"]["properties"]
ENTRY = CAPABILITY["language_coverage"]["items"]
SLUG = "example-eval"
CARD = "https://huggingface.co/datasets/example-org/example-eval"
PAPER = "https://arxiv.org/pdf/2601.00001"
WHERE = f"score {SLUG!r}: capability.language_coverage"
PIVOTS = f"score {SLUG!r}: capability.pivot_languages"

# Ten scored products, because a published category owes ten; letters rather than digits in
# the filler slugs, because a model slug with a digit reads as a version token.
FILLER = [f"filler-{c}" for c in "abcdefghi"]


def _corpus(with_coverage: bool = True, with_pivots: bool = True) -> dict:
    fixture = yaml.safe_load(FIXTURE.read_text())
    product, score = fixture["product"], fixture["score"]
    if not with_coverage:
        del score["capability"]["language_coverage"]
    if not with_pivots:
        del score["capability"]["pivot_languages"]
    cite = [{"url": "https://example.com/x", "shows": "y", "accessed": "2026-06-09"}]
    products = {
        slug: {"name": slug, "display_name": slug.title(), "type": "model",
               "github": [{"url": f"https://github.com/example-org/{slug}"}], "comments": ""}
        for slug in FILLER
    }
    scores = {
        slug: {"product": slug,
               "openness": {"score": 2, "class": "restricted", "sources": cite},
               "adoption": {"level": 4, "signal_type": "usage_volume", "sources": cite},
               "capability": {"score": None, "basis": "n/a"}}
        for slug in FILLER
    }
    products[SLUG], scores[SLUG] = product, score
    roster = FILLER + [SLUG]
    return {
        "organizations": {"example-org": {"name": "example-org", "display_name": "Example",
                                          "products": list(roster)}},
        "taxonomy": {"arcs": [{"name": "Model components", "layer": "model_components",
                               "groups": [{"name": "Group", "slug": "group",
                                           "categories": ["base_pretrained"]}]}]},
        "categories": {
            "base_pretrained": {"name": "base_pretrained", "display_name": "Base",
                                "description": "Base / pretrained models.",
                                "strapline": "The layer everything else is trained from.",
                                "weights": {"adopt": 0.6, "cap": 0.4},
                                "scoring_recipe": {"version": 1, "extends": "model"},
                                "products": list(roster), "comments": ""}
        },
        "products": products,
        "scores": scores,
        "model_families": {"version": 1, "families": []},
        "org_handles": {"version": 1, "handles": []},
    }


def _capability(d: dict) -> dict:
    return d["scores"][SLUG]["capability"]


def _coverage(d: dict) -> list[dict]:
    return _capability(d)["language_coverage"]


def _key(entry: dict) -> tuple:
    return tuple(entry[k] for k in COVERAGE_KEY)


def _entry(d: dict, language: str, task: str, component: str, split: str) -> dict:
    """The fixture entry with this key. Looked up by key rather than position, so adding an
    entry to the fixture does not silently retarget every test that indexes into it."""
    (entry,) = [e for e in _coverage(d) if _key(e) == (language, task, component, split)]
    return entry


def _add(d: dict, entry: dict) -> None:
    """Add an entry and keep the record sorted, so only the rule under test can fail."""
    _coverage(d).append(entry)
    _coverage(d).sort(key=_key)


def _lite(**overrides) -> dict:
    """A smaller exam drawn from the suite's own Swahili test questions."""
    entry = {"language": "swh", "task": "knowledge_exam", "component": "example-eval-lite",
             "split": "test", "official_eval": True, "count": 200, "unit": "questions",
             "provenance": "human_translated", "subset_of": "example-eval", "cites": [CARD]}
    entry.update(overrides)
    return entry


def _schema_errors(errors: list[str]) -> list[str]:
    return [e for e in errors if e.startswith(f"scores/{SLUG}: schema:")]


def _only(errors: list[str]) -> str:
    assert len(errors) == 1, errors
    return errors[0]


# --- valid -----------------------------------------------------------------------------------


def test_the_valid_fixture_passes():
    assert validate_sources(_corpus()) == []


def test_a_product_without_either_field_stays_valid():
    assert validate_sources(_corpus(with_coverage=False, with_pivots=False)) == []


def test_pivots_may_be_declared_with_no_coverage_entries():
    """A pivot stays identifiable even with no reported counts (R-2026-11-01-b)."""
    assert validate_sources(_corpus(with_coverage=False)) == []


def test_an_empty_pivot_declaration_says_the_set_was_built_for_every_language():
    d = _corpus()
    _capability(d)["pivot_languages"] = []
    assert validate_sources(d) == []


def test_the_fixture_shows_what_its_header_says():
    """The fixture is the worked example; pin the cases it exists to show, so a later edit that
    drops one is deliberate."""
    d = _corpus()
    entries = _coverage(d)
    assert _capability(d)["pivot_languages"] == ["eng"]
    assert {e["component"] for e in entries} == {"example-eval", "example-mt"}
    assert len({e["task"] for e in entries}) > 1
    mt = [e for e in entries if e["language"] == "hau" and e["component"] == "example-mt"]
    assert {e["split"]: e["official_eval"] for e in mt} == {"dev": False, "devtest": True}
    mixed = _entry(d, "hau", "knowledge_exam", "example-eval", "test")
    assert mixed["provenance"] == "mixed" and mixed["qualifying_count"] < mixed["count"]
    assert _entry(d, "yor", "knowledge_exam", "example-eval", "test")["provenance"] == (
        "machine_translated"
    )
    reviewed = _entry(d, "swh", "knowledge_exam", "example-eval", "train")
    assert reviewed["provenance"] == "generated" and reviewed["human_validated"] is True
    assert reviewed["official_eval"] is False
    mapped = [e for e in entries if "source_language" in e]
    assert [(_key(e), e["source_language"]) for e in mapped] == [
        (("swh", "knowledge_exam", "example-eval", "test"), "swa")
    ]
    zeros = [e for e in entries if e["count"] == 0]
    assert [_key(e) for e in zeros] == [("yor", "speech_recognition", "example-eval", "test")]
    assert zeros[0]["official_eval"] is True and "provenance" not in zeros[0]


def test_hours_may_be_fractional_and_a_count_may_be_zero():
    """Both are in the fixture already; this pins them so a tightening is deliberate."""
    d = _corpus()
    assert _entry(d, "hau", "speech_recognition", "example-eval", "test")["count"] == 12.5
    assert _entry(d, "yor", "speech_recognition", "example-eval", "test")["count"] == 0
    assert validate_sources(d) == []


def test_transliteration_is_a_task():
    """Added by R-2026-11-01-e, and the only addition."""
    d = _corpus()
    _add(d, {"language": "hau", "task": "transliteration", "component": "example-eval",
             "split": "test", "official_eval": True, "count": 500, "unit": "sentences",
             "provenance": "native", "cites": [CARD]})
    assert validate_sources(d) == []


def test_a_dev_split_may_be_the_official_evaluation_split():
    """A dev or validation split counts when it is the benchmark's official split
    (R-2026-11-01-d); what is refused is two official splits, not an official dev."""
    d = _corpus()
    _entry(d, "hau", "machine_translation", "example-mt", "dev")["official_eval"] = True
    _entry(d, "hau", "machine_translation", "example-mt", "devtest")["official_eval"] = False
    assert validate_sources(d) == []


def test_the_official_eval_split_value_is_accepted_when_marked_official():
    d = _corpus()
    _entry(d, "swh", "knowledge_exam", "example-eval", "test")["split"] = "official_eval"
    _coverage(d).sort(key=_key)
    assert validate_sources(d) == []


def test_a_qualifying_count_may_equal_the_count():
    d = _corpus()
    _entry(d, "hau", "knowledge_exam", "example-eval", "test")["qualifying_count"] = 1000
    assert validate_sources(d) == []


def test_a_mixed_entry_may_leave_the_qualifying_portion_unrecorded():
    """Absent means the source does not separate it, and the entry then establishes no
    qualifying depth (R-2026-11-01-h); that is a reading, not an error."""
    d = _corpus()
    del _entry(d, "hau", "knowledge_exam", "example-eval", "test")["qualifying_count"]
    assert validate_sources(d) == []


def test_a_subset_names_the_set_it_is_drawn_from():
    d = _corpus()
    _add(d, _lite())
    assert validate_sources(d) == []


def test_a_subset_may_hold_as_many_items_as_its_set():
    d = _corpus()
    _add(d, _lite(count=1000))
    assert validate_sources(d) == []


# --- shape: the score schema ------------------------------------------------------------------


@pytest.mark.parametrize("field", ENTRY["required"])
def test_every_required_field_is_required(field):
    d = _corpus()
    del _entry(d, "swh", "knowledge_exam", "example-eval", "test")[field]
    errors = _schema_errors(validate_sources(d))
    assert errors and f"{field!r} is a required property" in errors[0]


def test_the_required_fields_are_the_unit_of_evidence_and_its_reading():
    """`provenance` is required on every entry with items and absent on a documented zero, so it
    is conditional on `count` rather than in the unconditional list."""
    assert set(ENTRY["required"]) == set(COVERAGE_KEY) | {
        "official_eval", "count", "unit", "cites"
    }
    assert set(ENTRY["properties"]) - set(ENTRY["required"]) == {
        "provenance", "qualifying_count", "human_validated", "subset_of", "source_language",
        "precision",
    }


def test_provenance_is_required_on_an_entry_with_items():
    d = _corpus()
    del _entry(d, "swh", "knowledge_exam", "example-eval", "test")["provenance"]
    errors = _schema_errors(validate_sources(d))
    assert errors and "'provenance' is a required property" in errors[0]


def test_coverage_requires_a_pivot_declaration():
    errors = _schema_errors(validate_sources(_corpus(with_pivots=False)))
    assert errors and "'pivot_languages' is a dependency of 'language_coverage'" in errors[0]


@pytest.mark.parametrize("field, bad", [
    ("unit", "pages"),
    ("provenance", "translated"),
    ("provenance", "Native"),
    ("split", "eval"),
    ("split", "Test"),
    ("task", "sentiment"),
    ("official_eval", "yes"),
    ("human_validated", "reviewed"),
])
def test_closed_vocabularies_refuse_other_values(field, bad):
    d = _corpus()
    _coverage(d)[1][field] = bad
    errors = _schema_errors(validate_sources(d))
    assert errors and "language_coverage[1]" in errors[0]


def test_an_entry_names_one_task_not_a_list():
    d = _corpus()
    _coverage(d)[1]["task"] = ["machine_translation", "reading_comprehension"]
    assert _schema_errors(validate_sources(d))


@pytest.mark.parametrize("key, value", [
    ("tasks", ["knowledge_exam"]),
    ("pivot", True),
    ("depth", 3),
])
def test_an_entry_with_an_unknown_key_is_refused(key, value):
    """`tasks` and `pivot` are the entry's earlier spellings, and an entry carrying either would
    be an entry nothing reads."""
    d = _corpus()
    _coverage(d)[1][key] = value
    errors = _schema_errors(validate_sources(d))
    assert errors and "Additional properties are not allowed" in errors[0]


@pytest.mark.parametrize("field", ["count", "qualifying_count"])
def test_a_negative_count_is_refused(field):
    d = _corpus()
    _entry(d, "hau", "knowledge_exam", "example-eval", "test")[field] = -1
    errors = _schema_errors(validate_sources(d))
    assert errors and "less than the minimum of 0" in errors[0]


@pytest.mark.parametrize("field, value", [("count", 999.5), ("qualifying_count", 600.5)])
def test_a_fractional_count_is_refused_outside_hours(field, value):
    d = _corpus()
    _entry(d, "hau", "knowledge_exam", "example-eval", "test")[field] = value
    errors = _schema_errors(validate_sources(d))
    assert errors and "is not of type 'integer'" in errors[0]


@pytest.mark.parametrize("value", [[], {"eng": 1000}])
def test_the_record_is_a_non_empty_list(value):
    d = _corpus()
    _capability(d)["language_coverage"] = value
    assert _schema_errors(validate_sources(d))


def test_cites_are_non_empty_and_unique():
    d = _corpus()
    _coverage(d)[3]["cites"] = []
    assert _schema_errors(validate_sources(d))
    d = _corpus()
    _coverage(d)[3]["cites"] = [CARD, CARD]
    assert _schema_errors(validate_sources(d))


def test_a_cite_must_be_an_http_url():
    d = _corpus()
    _coverage(d)[0]["cites"] = ["the dataset card"]
    assert _schema_errors(validate_sources(d))


@pytest.mark.parametrize("bad", ["Example-Eval", "example eval", "-example", "", "example_mt"])
def test_a_component_is_a_kebab_case_slug(bad):
    d = _corpus()
    _coverage(d)[0]["component"] = bad
    assert _schema_errors(validate_sources(d))


@pytest.mark.parametrize("value", [["en"], ["eng", "eng"], "eng", ["ENG"]])
def test_pivot_languages_is_a_list_of_distinct_three_letter_codes(value):
    d = _corpus()
    _capability(d)["pivot_languages"] = value
    assert _schema_errors(validate_sources(d))


# --- cross-file: the code list and the product's `languages` ----------------------------------


@pytest.mark.parametrize("bad", ["mul", "und", "zxx", "xxx"])
def test_a_code_outside_the_iso_list_is_refused_as_languages_would_be(bad):
    d = _corpus()
    _entry(d, "yor", "speech_recognition", "example-eval", "test")["language"] = bad
    _coverage(d).sort(key=_key)
    error = _only(validate_sources(d))
    assert error.startswith(WHERE) and f"language {bad!r} is not an ISO 639-3" in error


@pytest.mark.parametrize("bad", ["mul", "xxx"])
def test_a_pivot_outside_the_iso_list_is_refused(bad):
    d = _corpus()
    _capability(d)["pivot_languages"] = sorted(["eng", bad])
    error = _only(validate_sources(d))
    assert error.startswith(PIVOTS) and f"language {bad!r} is not an ISO 639-3" in error


@pytest.mark.parametrize("bad", ["en", "ENG", "sw"])
def test_a_code_of_the_wrong_shape_fails_the_schema(bad):
    d = _corpus()
    _coverage(d)[0]["language"] = bad
    assert _schema_errors(validate_sources(d))


def test_a_code_must_be_listed_in_the_products_languages():
    d = _corpus()
    _entry(d, "yor", "speech_recognition", "example-eval", "test")["language"] = "zul"
    error = _only(validate_sources(d))
    assert error.startswith(WHERE) and "'zul' is not in the product's `languages`" in error


def test_a_pivot_must_be_listed_in_the_products_languages():
    d = _corpus()
    _capability(d)["pivot_languages"] = ["eng", "fra"]
    error = _only(validate_sources(d))
    assert error.startswith(PIVOTS) and "'fra' is not in the product's `languages`" in error


def test_a_product_with_no_languages_cannot_carry_coverage_or_pivots():
    d = _corpus()
    del d["products"][SLUG]["languages"]
    errors = validate_sources(d)
    unlisted = [e for e in errors if "is not in the product's `languages`" in e]
    assert len(unlisted) == len(_coverage(d)) + 1
    assert len(errors) == len(unlisted)


def test_pivots_are_sorted():
    d = _corpus()
    _capability(d)["pivot_languages"] = ["swh", "eng"]
    error = _only(validate_sources(d))
    assert error.startswith(PIVOTS) and "codes must be sorted (expected ['eng', 'swh'])" in error


def test_pivots_must_leave_a_target_language():
    """A pivot is a language the set was not built for; declaring every listed language one
    leaves no population for the median (R-2026-11-01-b)."""
    d = _corpus()
    _capability(d)["pivot_languages"] = ["eng", "hau", "swh", "yor"]
    error = _only(validate_sources(d))
    assert error.startswith(PIVOTS) and "leaves the set no target language" in error


@pytest.mark.parametrize("field", ["language_coverage", "pivot_languages"])
def test_the_per_language_fields_apply_to_datasets_only(field):
    d = _corpus(with_coverage=field == "language_coverage")
    d["products"][SLUG]["type"] = "model"
    d["scores"][SLUG]["openness"]["class"] = "open_source"
    errors = validate_sources(d)
    assert any(f"capability.{field} applies to datasets only" in e for e in errors)


# --- source_language: the code as the source states it ----------------------------------------


def test_a_source_language_need_not_be_listed_in_the_products_languages():
    """It is the code the source uses where the product lists another, so the product's list
    usually does not carry it; it is held to the code list only."""
    d = _corpus()
    _entry(d, "yor", "knowledge_exam", "example-eval", "test")["source_language"] = "zul"
    assert "zul" not in d["products"][SLUG]["languages"]
    assert validate_sources(d) == []


def test_a_source_language_equal_to_the_language_is_refused():
    d = _corpus()
    _entry(d, "swh", "knowledge_exam", "example-eval", "test")["source_language"] = "swh"
    error = _only(validate_sources(d))
    assert error.startswith(WHERE)
    assert "(swh, knowledge_exam, example-eval, test) carries source_language 'swh'" in error
    assert "same code as `language`" in error


@pytest.mark.parametrize("bad", ["mul", "und", "xxx"])
def test_a_source_language_outside_the_iso_list_is_refused(bad):
    d = _corpus()
    _entry(d, "swh", "knowledge_exam", "example-eval", "test")["source_language"] = bad
    error = _only(validate_sources(d))
    assert error.startswith(WHERE) and f"source_language {bad!r} is not an ISO 639-3" in error


@pytest.mark.parametrize("bad", ["sw", "SWA", "swa_Latn"])
def test_a_source_language_of_the_wrong_shape_fails_the_schema(bad):
    d = _corpus()
    _entry(d, "swh", "knowledge_exam", "example-eval", "test")["source_language"] = bad
    errors = _schema_errors(validate_sources(d))
    assert errors and "source_language" in errors[0]


# --- documented zeros ---------------------------------------------------------------------------


def _zero(d: dict) -> dict:
    return _entry(d, "yor", "speech_recognition", "example-eval", "test")


def test_a_documented_zero_carries_no_provenance():
    """The source states there are no items: a measured zero, not an unknown, and there are no
    items whose provenance could be described."""
    d = _corpus()
    assert "provenance" not in _zero(d) and "qualifying_count" not in _zero(d)
    assert validate_sources(d) == []


@pytest.mark.parametrize("provenance", ["unknown", "native", "machine_translated"])
def test_a_documented_zero_with_provenance_is_refused(provenance):
    d = _corpus()
    _zero(d)["provenance"] = provenance
    error = _only(validate_sources(d))
    assert error.startswith(WHERE)
    assert "(yor, speech_recognition, example-eval, test) is a documented zero" in error
    assert "carries `provenance`" in error


def test_a_documented_zero_with_a_qualifying_count_is_refused():
    d = _corpus()
    _zero(d)["qualifying_count"] = 0
    error = _only(validate_sources(d))
    assert "is a documented zero (count 0) and carries `qualifying_count`" in error


def test_a_non_zero_count_without_provenance_is_refused():
    d = _corpus()
    _zero(d)["count"] = 3.5
    errors = _schema_errors(validate_sources(d))
    assert errors and "'provenance' is a required property" in errors[0]


# --- cross-file: citations --------------------------------------------------------------------


def test_a_cite_must_be_a_capability_source():
    d = _corpus()
    _coverage(d)[0]["cites"] = ["https://example.org/a-page-nobody-cited"]
    error = _only(validate_sources(d))
    assert "(eng, knowledge_exam, example-eval, test) cites " in error
    assert "not the url of any capability.sources entry" in error


def test_a_url_cited_only_on_another_axis_does_not_count():
    """The record is capability evidence; an openness or adoption source is not its citation."""
    d = _corpus()
    _capability(d)["sources"] = [s for s in _capability(d)["sources"] if s["url"] != PAPER]
    d["scores"][SLUG]["openness"]["sources"].append(
        {"url": PAPER, "shows": "x", "accessed": "2026-10-30"}
    )
    errors = validate_sources(d)
    citing_paper = [e for e in _coverage(d) if PAPER in e["cites"]]
    assert sum(PAPER in e for e in errors) == len(citing_paper)


# --- cross-entry: the key, the official split, the qualifying portion, subsets ---------------


@pytest.mark.parametrize("first, second", [
    (("eng", "knowledge_exam", "example-eval", "test"),
     ("hau", "knowledge_exam", "example-eval", "test")),          # language
    (("hau", "knowledge_exam", "example-eval", "test"),
     ("hau", "machine_translation", "example-mt", "dev")),        # task
    (("hau", "machine_translation", "example-mt", "dev"),
     ("hau", "machine_translation", "example-mt", "devtest")),    # split
])
def test_entries_are_sorted_by_the_whole_key(first, second):
    d = _corpus()
    entries = _coverage(d)
    i, j = entries.index(_entry(d, *first)), entries.index(_entry(d, *second))
    entries[i], entries[j] = entries[j], entries[i]
    errors = validate_sources(d)
    assert any("must be sorted by (language, task, component, split)" in e for e in errors)


def test_entries_are_sorted_by_component_within_a_task():
    d = _corpus()
    _add(d, _lite())
    entries = _coverage(d)
    lite = entries.index(_entry(d, "swh", "knowledge_exam", "example-eval-lite", "test"))
    entries.insert(lite - 2, entries.pop(lite))  # ahead of example-eval's test and train
    error = _only(validate_sources(d))
    assert ("(swh, knowledge_exam, example-eval, test) comes before "
            "(swh, knowledge_exam, example-eval-lite, test)") in error


def test_each_key_appears_once():
    d = _corpus()
    _coverage(d).insert(1, copy.deepcopy(_coverage(d)[0]))
    error = _only(validate_sources(d))
    assert "each (language, task, component, split) appears once" in error
    assert "['eng', 'knowledge_exam', 'example-eval', 'test']" in error


def test_one_language_may_hold_several_entries():
    """The old record named each language once; the unit of evidence is now finer."""
    entries = _coverage(_corpus())
    assert len(entries) > len({e["language"] for e in entries})
    assert len({_key(e) for e in entries}) == len(entries)


def test_a_train_split_is_never_the_official_evaluation_split():
    d = _corpus()
    _entry(d, "swh", "knowledge_exam", "example-eval", "train")["official_eval"] = True
    errors = validate_sources(d)
    assert any("marks a train split as the official evaluation split" in e for e in errors)


def test_the_official_eval_split_is_marked_official():
    d = _corpus()
    entry = _entry(d, "swh", "knowledge_exam", "example-eval", "test")
    entry["split"], entry["official_eval"] = "official_eval", False
    _coverage(d).sort(key=_key)
    error = _only(validate_sources(d))
    assert "is on the `official_eval` split, so `official_eval` is true" in error


def test_dev_and_devtest_are_never_both_official():
    """FLORES+ translation depth uses its evaluation split, not dev and devtest added together
    (R-2026-11-01-d)."""
    d = _corpus()
    _entry(d, "hau", "machine_translation", "example-mt", "dev")["official_eval"] = True
    error = _only(validate_sources(d))
    assert "(hau, machine_translation, example-mt) marks 2 splits" in error
    assert "(dev, devtest)" in error


def test_a_qualifying_count_belongs_on_a_mixed_entry_only():
    d = _corpus()
    _entry(d, "swh", "knowledge_exam", "example-eval", "test")["qualifying_count"] = 500
    error = _only(validate_sources(d))
    assert "carries `qualifying_count`, which belongs only on a `mixed` entry" in error


def test_a_qualifying_count_cannot_exceed_the_count():
    d = _corpus()
    _entry(d, "hau", "knowledge_exam", "example-eval", "test")["qualifying_count"] = 1001
    error = _only(validate_sources(d))
    assert "qualifying_count 1001 above its count 1000" in error


def test_human_validation_never_changes_provenance():
    """A generated entry the source says people reviewed is valid as `generated`; the field
    records a quality attribute and does not stand in for `native` or `post_edited`
    (R-2026-11-01-h)."""
    d = _corpus()
    entry = _entry(d, "swh", "knowledge_exam", "example-eval", "train")
    assert entry["provenance"] == "generated" and entry["human_validated"] is True
    entry["human_validated"] = False
    assert validate_sources(d) == []


def test_a_subset_must_name_an_existing_entry():
    d = _corpus()
    _add(d, _lite(subset_of="example-exam"))
    error = _only(validate_sources(d))
    assert "is a subset of 'example-exam', but the record has no entry" in error


def test_a_subset_must_share_the_language_task_and_split():
    d = _corpus()
    _add(d, _lite(split="dev", official_eval=False))
    error = _only(validate_sources(d))
    assert "no entry (swh, knowledge_exam, example-eval, dev)" in error


def test_a_subset_cannot_name_its_own_component():
    d = _corpus()
    _add(d, _lite(subset_of="example-eval-lite"))
    error = _only(validate_sources(d))
    assert "names its own component in `subset_of`" in error


def test_a_subset_names_the_largest_set():
    d = _corpus()
    _add(d, _lite())
    _add(d, _lite(component="example-eval-mini", count=50, subset_of="example-eval-lite"))
    error = _only(validate_sources(d))
    assert "which is itself a subset. Name the largest set" in error


def test_a_subset_is_counted_in_its_sets_unit():
    d = _corpus()
    _add(d, _lite(unit="items"))
    error = _only(validate_sources(d))
    assert "counts 'items' but (swh, knowledge_exam, example-eval, test)" in error


def test_a_subset_cannot_hold_more_than_its_set():
    d = _corpus()
    _add(d, _lite(count=1200))
    error = _only(validate_sources(d))
    assert "holds 1200 questions, more than the 1000" in error


# --- the payload -------------------------------------------------------------------------------


def test_the_payload_leaves_the_per_language_evidence_out_and_keeps_the_rest_of_the_axis():
    score = yaml.safe_load(FIXTURE.read_text())["score"]
    cap = score["capability"]
    stripped = _without_language_coverage(cap)
    assert set(PER_LANGUAGE_KEYS) == {"language_coverage", "pivot_languages"}
    assert not set(PER_LANGUAGE_KEYS) & set(stripped)
    assert stripped == {k: v for k, v in cap.items() if k not in PER_LANGUAGE_KEYS}
    assert set(PER_LANGUAGE_KEYS) <= set(cap), "the record itself must not be mutated"

    product = yaml.safe_load(FIXTURE.read_text())["product"]
    row = _row(SLUG, product, "example-org", "Example", score, {"adopt": 0.3, "cap": 0.7})
    assert not set(PER_LANGUAGE_KEYS) & set(row["capability"])
    assert row["capability"]["score"] == 3


def test_a_pivot_declaration_alone_stays_out_of_the_payload():
    cap = {"score": 3, "basis": "feature_matrix", "pivot_languages": ["eng"]}
    assert _without_language_coverage(cap) == {"score": 3, "basis": "feature_matrix"}


def test_a_capability_block_without_the_evidence_ships_as_the_same_object():
    cap = {"score": 3, "basis": "feature_matrix"}
    assert _without_language_coverage(cap) is cap
    assert _without_language_coverage(None) is None


# --- the doc and the schema name the same vocabularies -----------------------------------------


def _doc_section() -> str:
    text = (ROOT / "docs" / "reference" / "capability.md").read_text()
    start = text.index("## Per-language coverage")
    return text[start:text.index("\n## ", start + 1)]


def _table(section: str, heading: str) -> list[str]:
    """The rows of the table under a heading, header and separator dropped."""
    block = section[section.index(heading):]
    rows: list[str] = []
    for line in block.splitlines()[1:]:
        if rows and not line.startswith("|"):
            break
        if line.startswith("|"):
            rows.append(line)
    return rows[2:]


def _first_column(section: str, heading: str) -> set[str]:
    """The backticked values in the first column of the table under a heading."""
    return {m.group(1) for line in _table(section, heading)
            if (m := re.match(r"\|\s*`([a-z_]+)`\s*\|", line))}


def test_the_doc_defines_exactly_the_schema_vocabularies():
    """The schema owns the vocabularies and capability.md says what each value means; a value
    added to one and not the other is a definition nobody wrote or a word nobody can use."""
    section = _doc_section()
    props = ENTRY["properties"]
    assert _first_column(section, "**Provenance.**") == set(props["provenance"]["enum"])
    assert _first_column(section, "**Tasks.**") == set(props["task"]["enum"])
    assert _first_column(section, "**Splits.**") == set(props["split"]["enum"])
    for unit in props["unit"]["enum"]:
        assert f"`{unit}`" in section, f"unit {unit!r} is not described in capability.md"


def test_the_doc_field_table_lists_exactly_the_schema_fields():
    section = _doc_section()
    assert _first_column(section, "### The fields") == (
        set(ENTRY["properties"]) | {"pivot_languages"}
    )


def test_the_vocabularies_are_the_ruled_ones():
    """Seven provenance values kept, transliteration added to the eighteen task classes, the six
    splits ruled, and nothing else (R-2026-11-01-d, R-2026-11-01-e)."""
    props = ENTRY["properties"]
    assert len(props["provenance"]["enum"]) == 7
    assert len(props["task"]["enum"]) == 19 and "transliteration" in props["task"]["enum"]
    assert set(props["split"]["enum"]) == {
        "train", "dev", "validation", "test", "devtest", "official_eval"
    }


def test_the_doc_states_native_and_generated_as_ruled():
    rows = {m.group(1): line for line in _table(_doc_section(), "**Provenance.**")
            if (m := re.match(r"\|\s*`([a-z_]+)`\s*\|", line))}
    assert "human-authored in the target language" in rows["native"]
    assert "model-generated directly in that language" in rows["generated"]


def test_the_doc_states_which_provenance_counts_toward_depth():
    """R-2026-11-01-h, as a column of the provenance table, so the rule sits beside the value."""
    rows = {m.group(1): line.split("|")[3].strip()
            for line in _table(_doc_section(), "**Provenance.**")
            if (m := re.match(r"\|\s*`([a-z_]+)`\s*\|", line))}
    for value in ("native", "human_translated", "post_edited"):
        assert rows[value].startswith("yes"), value
    for value in ("machine_translated", "generated", "unknown"):
        assert rows[value].startswith("no"), value
    assert "qualifying_count" in rows["mixed"]


def test_the_doc_cites_the_rulings_it_implements():
    section = _doc_section()
    for suffix in "abcdefgh":
        assert f"R-2026-11-01-{suffix}" in section, suffix


def test_the_docs_say_the_ladder_is_not_built():
    section = _doc_section()
    assert "R-2026-10-30-g" in section and "R-2026-10-30-i" in section
    assert "is not built" in section
