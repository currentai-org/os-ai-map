"""`capability.language_coverage`: the per-language evidence record (R-2026-10-30-h).

The valid record lives in `tests/fixtures/language_coverage/valid.yaml`, and every invalid case
here is that record with one thing broken, so a failure names the one rule it tests. The shape
rules (closed vocabularies, non-negative counts, required fields) are the score schema's; the
cross-file rules (the code list, the product's `languages`, citations on `capability.sources`)
are `build.validate.language_coverage_errors`. Both run through `validate_sources`, which is
what preflight runs. docs/reference/capability.md, "Per-language coverage", is normative.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest
import yaml

from build.serialize import _row, _without_language_coverage
from build.validate import validate_sources

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "language_coverage" / "valid.yaml"
SCHEMA = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
ENTRY = SCHEMA["properties"]["capability"]["properties"]["language_coverage"]["items"]
SLUG = "example-eval"

# Ten scored products, because a published category owes ten; letters rather than digits in
# the filler slugs, because a model slug with a digit reads as a version token.
FILLER = [f"filler-{c}" for c in "abcdefghi"]


def _corpus(with_coverage: bool = True) -> dict:
    fixture = yaml.safe_load(FIXTURE.read_text())
    product, score = fixture["product"], fixture["score"]
    if not with_coverage:
        del score["capability"]["language_coverage"]
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


def _coverage(d: dict) -> list[dict]:
    return d["scores"][SLUG]["capability"]["language_coverage"]


def _schema_errors(errors: list[str]) -> list[str]:
    return [e for e in errors if e.startswith(f"scores/{SLUG}: schema:")]


# --- valid -----------------------------------------------------------------------------------


def test_the_valid_fixture_passes():
    assert validate_sources(_corpus()) == []


def test_a_product_without_the_field_stays_valid():
    assert validate_sources(_corpus(with_coverage=False)) == []


def test_hours_may_be_fractional_and_a_count_may_be_zero():
    """Both are in the fixture already; this pins them so a tightening is deliberate."""
    entries = {e["language"]: e for e in _coverage(_corpus())}
    assert entries["hau"]["unit"] == "hours" and entries["hau"]["count"] == 12.5
    assert entries["yor"]["count"] == 0
    assert validate_sources(_corpus()) == []


# --- shape: the score schema ------------------------------------------------------------------


@pytest.mark.parametrize("field", ENTRY["required"])
def test_every_field_is_required(field):
    d = _corpus()
    del _coverage(d)[1][field]
    errors = _schema_errors(validate_sources(d))
    assert errors and f"{field!r} is a required property" in errors[0]


@pytest.mark.parametrize("field, bad", [
    ("unit", "pages"),
    ("provenance", "translated"),
    ("provenance", "Native"),
    ("pivot", "yes"),
])
def test_closed_vocabularies_refuse_other_values(field, bad):
    d = _corpus()
    _coverage(d)[1][field] = bad
    errors = _schema_errors(validate_sources(d))
    assert errors and "language_coverage[1]" in errors[0]


def test_a_task_outside_the_vocabulary_is_refused():
    d = _corpus()
    _coverage(d)[1]["tasks"] = ["speech_recognition", "sentiment"]
    errors = _schema_errors(validate_sources(d))
    assert errors and "'sentiment' is not one of" in errors[0]


def test_an_entry_with_an_unknown_key_is_refused():
    d = _corpus()
    _coverage(d)[1]["depth"] = 3
    assert _schema_errors(validate_sources(d))


def test_a_negative_count_is_refused():
    d = _corpus()
    _coverage(d)[0]["count"] = -1
    errors = _schema_errors(validate_sources(d))
    assert errors and "less than the minimum of 0" in errors[0]


def test_a_fractional_count_is_refused_outside_hours():
    d = _corpus()
    _coverage(d)[0]["count"] = 999.5
    errors = _schema_errors(validate_sources(d))
    assert errors and "is not of type 'integer'" in errors[0]


@pytest.mark.parametrize("value", [[], {"eng": 1000}])
def test_the_record_is_a_non_empty_list(value):
    d = _corpus()
    d["scores"][SLUG]["capability"]["language_coverage"] = value
    assert _schema_errors(validate_sources(d))


@pytest.mark.parametrize("field", ["tasks", "cites"])
def test_tasks_and_cites_are_non_empty_and_unique(field):
    d = _corpus()
    _coverage(d)[2][field] = []
    assert _schema_errors(validate_sources(d))
    d = _corpus()
    _coverage(d)[2][field] = _coverage(d)[2][field][:1] * 2
    assert _schema_errors(validate_sources(d))


def test_a_cite_must_be_an_http_url():
    d = _corpus()
    _coverage(d)[0]["cites"] = ["the dataset card"]
    assert _schema_errors(validate_sources(d))


# --- cross-file: build.validate.language_coverage_errors ---------------------------------------


@pytest.mark.parametrize("bad", ["mul", "und", "zxx", "xxx"])
def test_a_code_outside_the_iso_list_is_refused_as_languages_would_be(bad):
    d = _corpus()
    _coverage(d)[3]["language"] = bad
    d["scores"][SLUG]["capability"]["language_coverage"] = sorted(
        _coverage(d), key=lambda e: e["language"]
    )
    errors = validate_sources(d)
    assert any("capability.language_coverage" in e and f"language {bad!r} is not an ISO 639-3" in e
               for e in errors)


@pytest.mark.parametrize("bad", ["en", "ENG", "sw"])
def test_a_code_of_the_wrong_shape_fails_the_schema(bad):
    d = _corpus()
    _coverage(d)[0]["language"] = bad
    assert _schema_errors(validate_sources(d))


def test_a_code_must_be_listed_in_the_products_languages():
    d = _corpus()
    _coverage(d)[3]["language"] = "zul"  # a real code, absent from `languages`
    errors = validate_sources(d)
    assert len(errors) == 1 and "'zul' is not in the product's `languages`" in errors[0]


def test_a_product_with_no_languages_cannot_carry_coverage():
    d = _corpus()
    del d["products"][SLUG]["languages"]
    errors = validate_sources(d)
    assert sum("is not in the product's `languages`" in e for e in errors) == 4


def test_coverage_applies_to_datasets_only():
    d = _corpus()
    d["products"][SLUG]["type"] = "model"
    d["scores"][SLUG]["openness"]["class"] = "open_source"
    errors = validate_sources(d)
    assert any("capability.language_coverage applies to datasets only" in e for e in errors)


def test_a_cite_must_be_a_capability_source():
    d = _corpus()
    _coverage(d)[0]["cites"] = ["https://example.org/a-page-nobody-cited"]
    errors = validate_sources(d)
    assert any("'eng' cites 'https://example.org/a-page-nobody-cited'" in e
               and "not the url of any capability.sources entry" in e for e in errors)


def test_a_url_cited_only_on_another_axis_does_not_count():
    """The record is capability evidence; an openness or adoption source is not its citation."""
    d = _corpus()
    d["scores"][SLUG]["capability"]["sources"].pop(1)  # the arXiv paper, cited by hau and swh
    d["scores"][SLUG]["openness"]["sources"].append(
        {"url": "https://arxiv.org/pdf/2601.00001", "shows": "x", "accessed": "2026-10-30"}
    )
    errors = validate_sources(d)
    assert sum("https://arxiv.org/pdf/2601.00001" in e for e in errors) == 2


def test_entries_must_be_sorted_by_language():
    d = _corpus()
    entries = _coverage(d)
    entries[0], entries[1] = entries[1], entries[0]
    errors = validate_sources(d)
    assert any("must be sorted by language" in e for e in errors)


def test_each_language_appears_once():
    d = _corpus()
    _coverage(d).insert(1, copy.deepcopy(_coverage(d)[0]))
    errors = validate_sources(d)
    assert any("each language appears once (repeated: ['eng'])" in e for e in errors)


# --- the payload -------------------------------------------------------------------------------


def test_the_payload_leaves_the_record_out_and_keeps_the_rest_of_the_axis():
    score = yaml.safe_load(FIXTURE.read_text())["score"]
    cap = score["capability"]
    stripped = _without_language_coverage(cap)
    assert "language_coverage" not in stripped
    assert stripped == {k: v for k, v in cap.items() if k != "language_coverage"}
    assert "language_coverage" in cap, "the record itself must not be mutated"

    product = yaml.safe_load(FIXTURE.read_text())["product"]
    row = _row(SLUG, product, "example-org", "Example", score, {"adopt": 0.3, "cap": 0.7})
    assert "language_coverage" not in row["capability"]
    assert row["capability"]["score"] == 3


def test_a_capability_block_without_the_record_ships_as_the_same_object():
    cap = {"score": 3, "basis": "feature_matrix"}
    assert _without_language_coverage(cap) is cap
    assert _without_language_coverage(None) is None


# --- the doc and the schema name the same vocabularies -----------------------------------------


def _doc_section() -> str:
    text = (ROOT / "docs" / "reference" / "capability.md").read_text()
    start = text.index("## Per-language coverage")
    return text[start:text.index("\n## ", start + 1)]


def _first_column(section: str, heading: str) -> set[str]:
    """The backticked values in the first column of the table under a bold heading."""
    block = section[section.index(heading):]
    rows = []
    for line in block.splitlines()[1:]:
        if rows and not line.startswith("|"):
            break
        if line.startswith("|"):
            rows.append(line)
    return {m.group(1) for line in rows if (m := re.match(r"\|\s*`([a-z_]+)`\s*\|", line))}


def test_the_doc_defines_exactly_the_schema_provenance_and_task_values():
    """The schema owns the vocabularies and capability.md says what each value means; a value
    added to one and not the other is a definition nobody wrote or a word nobody can use."""
    section = _doc_section()
    props = ENTRY["properties"]
    assert _first_column(section, "**Provenance.**") == set(props["provenance"]["enum"])
    assert _first_column(section, "**Tasks.**") == set(props["tasks"]["items"]["enum"])
    for unit in props["unit"]["enum"]:
        assert f"`{unit}`" in section, f"unit {unit!r} is not described in capability.md"


def test_the_docs_say_the_ladder_is_not_built():
    section = _doc_section()
    assert "R-2026-10-30-g" in section and "R-2026-10-30-i" in section
    assert "is not built" in section
