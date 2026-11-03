"""Evidence status of a coverage entry, and the `precision` block that makes it estimated.

R-2026-11-02-e sets the three statuses and the task families with a count model, R-2026-11-02-f
what an estimate needs, R-2026-11-02-t the schema. No estimation method is approved yet, so every
estimated case here passes its own `approved` table. docs/reference/capability.md, "Evidence
status", is normative.
"""
from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import jsonschema
import pytest

from build.evidence_status import (
    APPROVED_METHODS,
    COUNT_MODEL_TASKS,
    entry_status,
    precision_errors,
    widest_margin,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
ENTRY_SCHEMA = SCHEMA["properties"]["capability"]["properties"]["language_coverage"]["items"]
TASKS = set(ENTRY_SCHEMA["properties"]["task"]["enum"])
CARD = "https://example.org/card"
RUNS = "https://example.org/runs"
APPROVED = {"document-bootstrap": frozenset({"machine_translation"})}

ENTRY = {
    "language": "hau", "task": "machine_translation", "component": "example-mt",
    "split": "devtest", "official_eval": True, "count": 1012, "unit": "sentences",
    "provenance": "human_translated", "cites": [CARD],
}
PRECISION = {
    "method": "document-bootstrap", "metric": "chrF", "resampling_unit": "document",
    "benchmark_version": "v2.1", "model_selection": "the two most-downloaded open models",
    "evidence_date": "2026-11-01",
    "runs": [
        {"model": "model-a", "model_family": "family-a", "interval": [40.0, 44.2], "cites": [RUNS]},
        {"model": "model-b", "model_family": "family-b", "interval": [51.0, 57.8], "cites": [RUNS]},
    ],
    "cites": [RUNS],
}


def with_precision(**changes) -> dict:
    e = copy.deepcopy(ENTRY)
    e["precision"] = {**copy.deepcopy(PRECISION), **changes}
    return e


def status(entry, approved=None):
    s = entry_status(entry, approved=approved)
    return None if s is None else (s.status, s.reason)


# --- status ------------------------------------------------------------------------------------


def test_no_method_is_approved_yet():
    # R-2026-11-02-f: every calibration set stays provisional until a family's method is ruled.
    assert APPROVED_METHODS == {}


def test_count_model_tasks_are_real_task_classes():
    assert COUNT_MODEL_TASKS <= TASKS


def test_counted_entry_is_provisional():
    assert status(ENTRY) == ("provisional", "count_model")


def test_valid_estimate_under_an_approved_method_is_estimated():
    assert status(with_precision(), APPROVED) == ("estimated", "estimate")


def test_estimate_without_an_approving_ruling_stays_provisional():
    assert status(with_precision()) == ("provisional", "count_model")


def test_entry_outside_the_official_split_has_no_status():
    assert status({**ENTRY, "official_eval": False, "split": "dev"}) is None


@pytest.mark.parametrize("change", [
    {"provenance": "unknown"},
    {"provenance": "mixed"},  # mixed without a qualifying_count
])
def test_unknown_depth_is_unresolved(change):
    assert status({**ENTRY, **change}) == ("unresolved", "depth_unknown")


@pytest.mark.parametrize("entry", [
    {**ENTRY, "provenance": "machine_translated"},
    {**ENTRY, "provenance": "machine_translated", "human_validated": False},
    {**ENTRY, "provenance": "generated", "human_validated": True},  # review never rescues generated
    {k: v for k, v in {**ENTRY, "count": 0}.items() if k != "provenance"},  # documented zero
])
def test_measured_zero_is_provisional(entry):
    assert status(entry) == ("provisional", "measured_zero")


def test_reviewed_machine_translation_counts():
    # R-2026-11-03-b, -h: a source stating people reviewed every translation makes them qualify,
    # and the provenance stays machine_translated.
    reviewed = {**ENTRY, "provenance": "machine_translated", "human_validated": True,
                "review_scope": "all_items"}
    assert status(reviewed) == ("provisional", "count_model")


@pytest.mark.parametrize("scope", ["unstated", None])
def test_a_review_of_unstated_scope_leaves_depth_unknown(scope):
    """R-2026-11-03-h: a review the source describes without saying how many items it covered
    is neither a count nor a zero."""
    reviewed = {**ENTRY, "provenance": "machine_translated", "human_validated": True}
    if scope:
        reviewed["review_scope"] = scope
    assert status(reviewed) == ("unresolved", "depth_unknown")


@pytest.mark.parametrize("task", sorted(TASKS - COUNT_MODEL_TASKS))
def test_task_without_a_measurement_model_is_unresolved(task):
    # Sequence labeling and speech are ruled unresolved; the rest are unruled (R-2026-11-02-b).
    assert status({**ENTRY, "task": task}) == ("unresolved", "no_measurement_model")


@pytest.mark.parametrize("task", ["speech_recognition", "sequence_labeling", "retrieval"])
def test_zero_in_a_family_without_a_model_is_unresolved(task):
    # A zero does not give a family without a model a provisional band (R-2026-11-02-b, -l).
    zero = {k: v for k, v in {**ENTRY, "task": task, "count": 0}.items() if k != "provenance"}
    assert status(zero) == ("unresolved", "no_measurement_model")
    assert status({**ENTRY, "task": task, "provenance": "generated"}) == (
        "unresolved", "no_measurement_model")


def test_unit_a_count_model_cannot_read_is_unresolved():
    assert status({**ENTRY, "unit": "hours"}) == ("unresolved", "unit_not_countable")


# --- the precision block -----------------------------------------------------------------------


def errs(entry, **kw):
    return precision_errors(entry, "x", cited={CARD, RUNS}, approved=APPROVED,
                            today=date(2026, 11, 2), **kw)


def test_valid_block_has_no_errors():
    assert errs(with_precision()) == []


def test_valid_block_matches_the_schema():
    jsonschema.validate(with_precision(), ENTRY_SCHEMA)


def test_unapproved_method_is_an_error():
    assert any("has no approving ruling" in e for e in errs(with_precision(method="other")))


def test_method_approved_for_another_task_is_an_error():
    entry = {**with_precision(), "task": "knowledge_exam", "unit": "questions"}
    assert any("not approved for task" in e for e in errs(entry))


def test_two_runs_from_one_family_are_not_enough():
    runs = copy.deepcopy(PRECISION["runs"])
    runs[1]["model_family"] = "family-a"
    assert any("two different model families" in e for e in errs(with_precision(runs=runs)))


def test_one_run_is_not_enough():
    assert any("two different model families" in e
               for e in errs(with_precision(runs=PRECISION["runs"][:1])))


@pytest.mark.parametrize("interval", [[50, 40], [-1, 10], [90, 101]])
def test_interval_must_be_ordered_and_on_the_score_scale(interval):
    runs = copy.deepcopy(PRECISION["runs"])
    runs[0]["interval"] = interval
    assert any("interval must be" in e for e in errs(with_precision(runs=runs)))


@pytest.mark.parametrize("raw, message", [("2026-02-30", "is not an ISO date"),
                                          ("2999-01-01", "later than today")])
def test_evidence_date_is_real_and_not_in_the_future(raw, message):
    assert any(message in e for e in errs(with_precision(evidence_date=raw)))


def test_citations_must_be_capability_sources():
    runs = copy.deepcopy(PRECISION["runs"])
    runs[0]["cites"] = ["https://example.org/elsewhere"]
    assert any("not the url of any capability.sources" in e for e in errs(with_precision(runs=runs)))


def test_estimate_cannot_stand_in_for_provenance():
    entry = {**with_precision(), "provenance": "unknown"}
    assert any("qualifying depth is not established" in e for e in errs(entry))
    assert status(entry, APPROVED) == ("unresolved", "depth_unknown")


@pytest.mark.parametrize("bad", [
    "not a mapping",
    ["a", "list"],
    {**PRECISION, "runs": "not a list"},
    {**PRECISION, "runs": [{"model": "m", "model_family": "f", "interval": [50], "cites": [RUNS]},
                           {"model": "n", "model_family": "g", "interval": [1, 2, 3], "cites": [RUNS]}]},
    {**PRECISION, "runs": ["not a run", 7]},
    {**PRECISION, "cites": "not a list"},
    {**PRECISION, "method": ["not", "a", "string"]},
    {**PRECISION, "runs": [{"model": "m", "model_family": ["x"], "interval": [1, 2], "cites": [RUNS]},
                           {"model": "n", "model_family": {"y": 1}, "interval": [1, 2], "cites": [RUNS]}]},
])
def test_malformed_block_is_an_error_not_a_crash(bad):
    # Regression: the hook runs before the schema, so a malformed shape raised instead of erring.
    entry = {**ENTRY, "precision": bad}
    assert errs(entry) != []
    assert status(entry, APPROVED) == ("provisional", "count_model")


def test_widest_margin_sets_the_band_figure():
    # Half-widths 2.1 and 3.4: the wider sets the band (R-2026-11-02-f).
    assert widest_margin(PRECISION) == pytest.approx(3.4)


def test_schema_refuses_a_single_run():
    entry = with_precision(runs=PRECISION["runs"][:1])
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(entry, ENTRY_SCHEMA)
