"""The corpus goldens live in tests/goldens/corpus.json, written by the bot on main.

Equality against the file is asserted only when the working tree's sources/ fingerprint
matches the fingerprint the file was computed from. On a PR that changes sources/ the
fingerprint differs by construction, so equality is skipped there and the structural
invariants below carry the weight; build.check_corpus_diff carries the per-row content
check on PRs. This is what lets two product PRs merge back to back with no re-pinning.
"""
from pathlib import Path

import pytest

from build import goldens

ROOT = Path(__file__).resolve().parents[1]


def test_fingerprint_is_stable_and_changes_with_sources(tmp_path):
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "a.yaml").write_text("name: a\n")
    first = goldens.fingerprint(tmp_path)
    assert first == goldens.fingerprint(tmp_path)
    (tmp_path / "sources" / "a.yaml").write_text("name: b\n")
    assert goldens.fingerprint(tmp_path) != first


def test_golden_file_exists_and_names_every_section():
    data = goldens.load(ROOT)
    assert set(data) >= {
        "sources_fingerprint", "computed_at_commit", "axis_assessments",
        "adoption_reconciliation", "axis_scoring_trace", "parity", "rubric_rows",
        "check_rubric", "under_coverage",
    }


@pytest.fixture(scope="module")
def computed():
    return goldens.compute(ROOT)


def test_equality_when_tree_matches_golden(computed):
    data = goldens.load(ROOT)
    if goldens.fingerprint(ROOT) != data["sources_fingerprint"]:
        pytest.skip("sources/ differs from the golden's tree; check_corpus_diff gates content on PRs")
    for key in ("axis_assessments", "adoption_reconciliation", "axis_scoring_trace",
                "parity", "rubric_rows", "check_rubric", "under_coverage"):
        assert computed[key] == data[key], key


def test_structural_invariants_hold_regardless_of_tree(computed):
    # Three axis rows per recorded assessment: the pins were largely redundant with this.
    assert computed["axis_assessments"]["rows"] == computed["adoption_reconciliation"]["rows"] * 3
    assert computed["axis_scoring_trace"]["axis_results"][0] == computed["adoption_reconciliation"]["rows"]
    # Full reproduction: every computed product reproduces, none abstains.
    assert computed["parity"]["computed"] + computed["parity"]["deferred"] == computed["adoption_reconciliation"]["rows"]
    for slug, report in computed["check_rubric"].items():
        assert report["reproduced"] == report["total"], slug
    # Ladder inheritance: every software category serializes the same rule count.
    rules = computed["rubric_rows"]["category_scoring_rules"]
    software = {k: v for k, v in rules.items() if k in goldens.SOFTWARE_CATEGORIES}
    assert len(set(software.values())) == 1, software
    # The under-coverage roster is a set of slugs, and its count is the set's size.
    assert computed["under_coverage"]["count"] == len(computed["under_coverage"]["slugs"])
