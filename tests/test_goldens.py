"""The corpus goldens live in tests/goldens/corpus.json, written by the bot on main.

Equality against the file is asserted only when the working tree's sources/ fingerprint
matches the fingerprint the file was computed from. On a PR that changes sources/ the
fingerprint differs by construction, so equality is skipped there and the structural
invariants below carry the weight; build.check_corpus_diff carries the per-row content
check on PRs. This is what lets two product PRs merge back to back with no re-pinning.
"""
import json
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


def test_software_categories_covers_every_category_that_extends_software_alone():
    """goldens.SOFTWARE_CATEGORIES is derived, not hand-listed; re-derive it independently
    here so a category whose scoring_recipe changes (a new one starts or stops extending
    `software` alone) shows up as a real assertion failure, not silently."""
    from build.rubrics import load_shared, resolve_recipe_variants
    from build.taxonomy import category_statuses
    from build.validate import load_sources

    data = load_sources(ROOT)
    shared = load_shared(ROOT)
    statuses = category_statuses(data.get("taxonomy") or {})
    expected = set()
    for slug, category in (data.get("categories") or {}).items():
        if statuses.get(slug, "published") != "published":
            continue
        variants, errors = resolve_recipe_variants(category or {}, shared)
        if errors or set(variants) != {"*"}:
            continue
        if variants["*"].get("extends") == "software":
            expected.add(slug)
    assert goldens.SOFTWARE_CATEGORIES == expected
    assert expected, "expected at least one published category to extend the software ladder"


def _write_golden(root: Path, **fields):
    path = root / goldens.GOLDEN_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fields))


def test_main_check_treats_a_stale_fingerprint_as_expected_and_self_healing(tmp_path, monkeypatch, capsys):
    """A merge that touched sources/ always leaves the fingerprint stale until
    regenerate.yml's bot commit rewrites it. Plain --check must not redden that merge."""
    _write_golden(tmp_path, sources_fingerprint="old")
    monkeypatch.setattr(goldens, "fingerprint", lambda root: "new")
    rc = goldens.main(["--check"], root=tmp_path)
    assert rc == 0
    assert "::notice::" in capsys.readouterr().out


def test_main_check_strict_fails_on_a_stale_fingerprint(tmp_path, monkeypatch):
    """--strict is for regenerate.yml to self-check right after --write, where a stale
    fingerprint would mean the write itself did not clear the staleness."""
    _write_golden(tmp_path, sources_fingerprint="old")
    monkeypatch.setattr(goldens, "fingerprint", lambda root: "new")
    rc = goldens.main(["--check", "--strict"], root=tmp_path)
    assert rc == 1


def test_main_check_fails_on_producer_drift_with_sources_unchanged(tmp_path, monkeypatch):
    """Sources unchanged (fingerprint matches) but a recompute differs from the golden:
    a producer changed and the golden was never regenerated. This must always fail,
    --strict or not."""
    _write_golden(tmp_path, sources_fingerprint="same", a=1)
    monkeypatch.setattr(goldens, "fingerprint", lambda root: "same")
    monkeypatch.setattr(goldens, "compute", lambda root: {"a": 2})
    rc = goldens.main(["--check"], root=tmp_path)
    assert rc == 1


def test_main_check_passes_when_sources_unchanged_and_nothing_drifted(tmp_path, monkeypatch):
    _write_golden(tmp_path, sources_fingerprint="same", a=1)
    monkeypatch.setattr(goldens, "fingerprint", lambda root: "same")
    monkeypatch.setattr(goldens, "compute", lambda root: {"a": 1})
    rc = goldens.main(["--check"], root=tmp_path)
    assert rc == 0
