"""The classification reader's contract checks (build/language_representation.py).

The rules the table implements are in docs/reference/language-classification.md; these tests
pin only what the reader enforces about the table's shape: no NULL where the contract forbids
one, vocabulary values, coherent interval ends, the method's major version, one row per code,
and a row for every code the map's products declare.
"""

from __future__ import annotations

import math

from build import assets
from build.language_representation import (
    COLUMNS,
    check,
    declared_codes,
    row_errors,
    summary,
)


def good_row(**overrides) -> dict:
    row = {
        "iso639_3": "kor",
        "macrolanguage": None,
        "related_to": [],
        "flags": [],
        "written_best": "B",
        "written_worst": "B",
        "written_state": "measured",
        "representation_class": "mid",
        "representation_class_best": "mid",
        "representation_class_worst": "mid",
        "status_best": "national",
        "status_worst": "national",
        "status_state": "measured",
        "recognized": "no",
        "speakers_low": 77_300_000,
        "speakers_high": 79_300_000,
        "speakers_state": "measured",
        "official": "yes",
        "many_speakers": "yes",
        "large_written_material": "yes",
        "scholarly_works": "unknown",
        "endangerment": "not endangered",
        "descriptive_status": "unknown",
        "provenance": [{"measure": "web_text_words", "source": "fineweb-2"}],
        "code_table_version": "20261015",
        "method_version": "1.0.0",
        "computed_at": "2026-11-10T12:00:00",
    }
    row.update(overrides)
    return row


def test_columns_follow_the_reference():
    """Every contract column the reference names is checked, and only those."""
    reference = (assets.ROOT / "docs" / "reference" / "language-classification.md").read_text()
    section = reference.split("### `language_representation.classification`")[1].split("**Unknown")[0]
    named = set()
    for line in section.splitlines():
        if line.startswith("| `"):
            for cell in line.split("|")[1].split(","):
                named.add(cell.strip().strip("`"))
    assert named == set(COLUMNS)


def test_a_good_row_passes():
    assert row_errors(good_row()) == []


def test_unresolved_with_both_ends_passes():
    row = good_row(
        representation_class="unresolved",
        representation_class_best="high",
        representation_class_worst="mid",
        written_best="A",
        written_worst="B",
        official="unresolved",
        status_best="subnational",
        status_worst="none",
        status_state="not_listed",
    )
    assert row_errors(row) == []


def test_null_in_a_non_null_column_fails():
    errors = row_errors(good_row(official=None))
    assert errors == ["kor: NULL in non-null column official"]


def test_nan_counts_as_null():
    errors = row_errors(good_row(written_state=float("nan")))
    assert errors == ["kor: NULL in non-null column written_state"]


def test_nullable_speaker_ends_may_be_missing():
    assert row_errors(good_row(speakers_low=None, speakers_high=math.nan)) == []


def test_vocabulary_is_enforced():
    errors = row_errors(good_row(official="maybe"))
    assert len(errors) == 1 and "official = 'maybe'" in errors[0]


def test_resolved_class_needs_equal_ends():
    errors = row_errors(good_row(representation_class_worst="low"))
    assert errors == ["kor: resolved class mid has ends mid..low"]


def test_unresolved_class_needs_different_ends():
    errors = row_errors(good_row(representation_class="unresolved"))
    assert errors == ["kor: unresolved class has equal ends mid"]


def test_other_method_major_fails():
    errors = row_errors(good_row(method_version="2.0.0"))
    assert errors == ["kor: method_version 2.0.0 is not major 1"]


def test_missing_column_fails():
    row = good_row()
    del row["provenance"]
    assert row_errors(row) == ["kor: missing columns provenance"]


def test_duplicate_and_missing_codes_fail():
    rows = [good_row(), good_row()]
    errors = check(rows, {"kor": ["p"], "swh": ["q", "r"]})
    assert "kor: 2 rows; the table holds one row per code" in errors
    assert "swh: declared by q, r but has no classification row" in errors


def test_declared_codes_reads_products(tmp_path):
    (tmp_path / "a.yaml").write_text("languages: [kor, swh]\n")
    (tmp_path / "b.yaml").write_text("languages: [swh]\n")
    (tmp_path / "c.yaml").write_text("display_name: no languages\n")
    assert declared_codes(tmp_path) == {"kor": ["a"], "swh": ["a", "b"]}


def test_summary_counts_profiles():
    rows = [good_row(), good_row(iso639_3="swh", official="unresolved")]
    text = summary(rows, {"kor": ["p"]})
    assert "Y/Y/Y  1" in text
    assert "at least one axis unresolved  1" in text


def test_reader_is_an_audit_root_reading_the_table():
    """The reader reaches the contract through gate 4's closed root set."""
    assert "build/language_representation.py" in assets.AUDIT_ROOTS
    internal, _ = assets.reads_of(assets.ROOT / "build" / "language_representation.py")
    assert internal == {"language_representation.classification"}


# ── The membership review's language half (R-2026-10-30-d, R-2026-11-10-j) ────────────────

from build.language_representation import language_verdict, product_verdict  # noqa: E402

CLASSES = {
    "eng": {"representation_class": "high", "representation_class_best": "high",
            "representation_class_worst": "high"},
    "kor": {"representation_class": "mid", "representation_class_best": "mid",
            "representation_class_worst": "mid"},
    "tur": {"representation_class": "unresolved", "representation_class_best": "high",
            "representation_class_worst": "mid"},
    "afr": {"representation_class": "unresolved", "representation_class_best": "low",
            "representation_class_worst": "very_low"},
    "xyz": {"representation_class": "unknown", "representation_class_best": "unknown",
            "representation_class_worst": "unknown"},
}


def test_a_language_is_below_the_line_only_at_both_ends():
    assert language_verdict("kor", CLASSES) == "below"
    assert language_verdict("afr", CLASSES) == "below"
    assert language_verdict("eng", CLASSES) == "at_or_above"
    assert language_verdict("tur", CLASSES) == "undecided"
    assert language_verdict("xyz", CLASSES) == "undecided"
    assert language_verdict("zzz", CLASSES) == "undecided"


def test_any_target_below_the_line_is_in():
    assert product_verdict(["eng", "kor"], CLASSES)[0] == "in"


def test_every_target_at_or_above_is_out():
    assert product_verdict(["eng"], CLASSES)[0] == "out"


def test_otherwise_the_purpose_test_decides_alone():
    assert product_verdict(["tur"], CLASSES)[0] == "purpose_test"
    assert product_verdict(["eng", "tur"], CLASSES)[0] == "purpose_test"
    assert product_verdict([], CLASSES)[0] == "purpose_test"


def test_large_written_material_no_needs_the_web_route_to_fail():
    errors = row_errors(good_row(large_written_material="no", written_best="B", written_worst="C",
                                 representation_class="unresolved",
                                 representation_class_best="mid", representation_class_worst="low"))
    assert errors == ["kor: large_written_material is no but written material reaches B"]
    assert row_errors(good_row(large_written_material="no", written_best="C", written_worst="C",
                               representation_class="low", representation_class_best="low",
                               representation_class_worst="low")) == []
