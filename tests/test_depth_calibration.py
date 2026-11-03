"""The full-roster depth calibration reproduces from the repository.

These pin the headline figures of docs/sweeps/2026-11-03-depth-calibration-full-roster.md to
`build.depth_calibration` run over `sources/`, so the record cannot drift from the data it
describes. A coverage, lineage or rule change that moves one of them fails here: update the record
and these figures together, in the same PR.
"""
from __future__ import annotations

import pytest

from build import depth_calibration as dc
from build import lineage

# slug: (corroborated band, face value, bonus, measured, targets, capped languages)
EXPECTED = {
    "flores-plus": ("3", "3", 3.5, 188, 215, 0),
    "fleurs": ("unresolved (0-5)", "unresolved (0-5)", None, 0, 101, 0),
    "belebele": ("3", "3", 3.5, 114, 114, 0),
    "sib-200": ("2", "2", 2.5, 194, 195, 0),
    "include-benchmark": ("3", "3", 3.49, 44, 44, 2),
    "afrobench": ("1", "3", 1.49, 56, 63, 37),
    "milu": ("4", "4", 4.45, 10, 10, 0),
    "indicgenbench": ("3", "3", 3.48, 29, 29, 1),
    "indicxtreme": ("4", "4", 4.47, 19, 21, 0),
    "lahaja": ("unresolved (0-5)", "unresolved (0-5)", None, 0, 1, 0),
    "sea-helm": ("2", "3", 2.45, 11, 11, 4),
    "seaexam": ("3", "3", 3.38, 4, 4, 1),
    "thai-exam": ("3", "3", 3.0, 1, 1, 0),
    "vmlu": ("unresolved (0-5)", "unresolved (0-5)", None, 0, 1, 0),
    "laobench": ("4", "4", 4.0, 1, 1, 0),
    "indonlu": ("unresolved (0-5)", "unresolved (0-5)", None, 0, 1, 0),
    "arabicmmlu": ("5", "5", 5.0, 1, 1, 0),
    "darijammlu": ("unresolved (0-5)", "unresolved (0-5)", None, 0, 1, 0),
    "turkishmmlu": ("5", "5", 5.0, 1, 1, 0),
    "kazmmlu": ("5", "5", 5.25, 2, 2, 0),
    "khayyam-challenge": ("5", "5", 5.0, 1, 1, 0),
    "americasnlp-shared-task-data": ("1", "3", 1.45, 10, 10, 9),
}


@pytest.fixture(scope="module")
def doc():
    return lineage.load()


@pytest.fixture(scope="module")
def results(doc):
    return dc.calibrate(doc)


def test_the_roster_is_the_record_s():
    assert set(dc.ROSTER) == set(EXPECTED) and len(dc.ROSTER) == 22


@pytest.mark.parametrize("slug", sorted(EXPECTED))
def test_each_set_reproduces(results, slug):
    a = results[slug]["a"]
    got = (a["band"], a["face_value"], a["bonus"], a["measured"], a["targets"], len(a["capped"]))
    assert got == EXPECTED[slug]


def test_the_headline_figures(results):
    s = dc.summary(results)
    assert s["band_5"] == ["arabicmmlu", "turkishmmlu", "kazmmlu", "khayyam-challenge"]
    assert s["resolved"] == 17
    # R-2026-11-02-c: the review trigger fires at one third of the roster.
    assert len(s["band_5"]) < s["sets"] / 3
    # R-2026-11-02-i: no band depends on treating unverified lineage as independent.
    assert s["runs_disagree"] == []


def test_the_ownership_readings_move_no_set_band(doc, results):
    for name, sets in dc.sensitivity(doc).items():
        for slug, r in sets.items():
            assert r["band"] == results[slug]["a"]["band"], (name, slug)
    sens = dc.sensitivity(doc)
    assert len(sens["second_slugs_as_imports"]["indicxtreme"]["capped"]) == 7
    assert len(sens["second_slugs_as_imports"]["indicgenbench"]["capped"]) == 9
    assert len(sens["include_mixed_as_imports"]["include-benchmark"]["capped"]) == 12


def test_include_s_imported_languages_are_capped(results):
    assert results["include-benchmark"]["a"]["capped"] == sorted(dc.INCLUDE_IMPORTED)
    assert all(results["include-benchmark"]["a"]["per_language"][lang] == 1
               for lang in dc.INCLUDE_IMPORTED)


def test_include_s_ownership_follows_its_lineage_record(doc):
    """The imported languages are exactly those whose override names a parent, and the mixed
    ones those whose override adds a collection beside INCLUDE's own exams."""
    rec = next(c for c in doc["components"] if c["id"] == "include-benchmark")
    own_collections = set(rec["collections"])
    imported, mixed = set(), set()
    for ov in rec.get("overrides") or []:
        if ov.get("parents"):
            imported |= set(ov["languages"])
        elif set(ov.get("collections") or []) - own_collections:
            mixed |= set(ov["languages"])
    assert imported == dc.INCLUDE_IMPORTED
    assert mixed == dc.INCLUDE_MIXED


@pytest.mark.parametrize("count, expected", [
    (0, 0), (1, 1), (99, 1), (100, 2), (399, 2), (400, 3), (1600, 4), (6399, 4), (6400, 5),
])
def test_the_count_ladder(count, expected):
    assert dc.band(count) == expected


def test_own_ids_scopes():
    own = dc.OWN_COMPONENTS
    assert dc.own_ids("include-benchmark", "ara", own) == set()
    assert dc.own_ids("include-benchmark", "deu", own) == {"include-benchmark"}
    assert "flores-in" in dc.own_ids("indicgenbench", "brx", own)
    assert "flores-in" not in dc.own_ids("indicgenbench", "hin", own)
    assert "crosssum-in" not in dc.own_ids("indicgenbench", "nep", own)
    assert "crosssum-in" in dc.own_ids("indicgenbench", "asm", own)


# --- the method on hand-built inputs -----------------------------------------------------------
# The figures above pin the method's output on the records; these check the method itself, so a
# change to D5 or the median that happened to leave the roster's bands alone still fails here.


def comp(component, band, task="knowledge_exam"):
    return {"component": component, "band": band, "task": task, "split": "test"}


@pytest.fixture
def pairs(monkeypatch):
    """Stub lineage: `table` maps a frozenset pair to its status; anything else is dependent."""
    table = {}

    def pair_status(doc, a, b, language=None, **kw):
        return lineage.PairStatus(table.get(frozenset((a, b)), "dependent"), "stub")

    monkeypatch.setattr(dc.lineage, "pair_status", pair_status)
    return table


def band_of(comps, *, loose=False):
    return dc.language_band({}, "own", "xxx", comps, loose=loose, own={})


def test_own_items_count_at_face_value(pairs):
    assert band_of([comp("own", 4)]) == (4, 4)


def test_an_uncorroborated_import_is_capped_at_one(pairs):
    assert band_of([comp("imported", 5)]) == (1, 5)


def test_an_import_rises_one_band_above_its_independent_backing(pairs):
    pairs[frozenset(("imported", "own"))] = "independent"
    assert band_of([comp("own", 2), comp("imported", 5)]) == (3, 5)
    # Backing never lifts an import above its own band.
    assert band_of([comp("own", 5), comp("imported", 3)]) == (5, 5)


def test_a_dependent_backer_gives_no_backing(pairs):
    assert band_of([comp("own", 2), comp("imported", 5)]) == (2, 5)


def test_an_import_of_the_same_task_cannot_back_another(pairs):
    pairs[frozenset(("a", "b"))] = "independent"
    assert band_of([comp("a", 5), comp("b", 4)]) == (1, 5)
    # A different task can.
    assert band_of([comp("a", 5), comp("b", 4, task="reading_comprehension")]) == (5, 5)


def test_unverified_lineage_backs_only_in_the_loose_run(pairs):
    pairs[frozenset(("imported", "own"))] = "unverified"
    assert band_of([comp("own", 3), comp("imported", 5)]) == (3, 5)
    assert band_of([comp("own", 3), comp("imported", 5)], loose=True) == (4, 5)


@pytest.mark.parametrize("values, expected", [
    ([], None), ([3], 3), ([1, 5, 5], 5), ([1, 2, 3, 4], 2), ([0, 5], 2), ([4, 5], 4),
])
def test_the_median_rounds_down_on_an_even_count(values, expected):
    assert dc.median_band(values) == expected


@pytest.mark.parametrize("values, unknown, expected", [
    ([3, 3, 3], 0, "3"),
    ([3, 3, 3], 1, "3"),                 # one unknown can't move a median of three agreeing bands
    ([3], 1, "unresolved (1-4)"),        # 0-fill and 5-fill disagree
    ([], 1, "unresolved (0-5)"),
    ([], 0, None),
])
def test_unmeasured_targets_fill_zero_and_five(values, unknown, expected):
    assert dc._set_band(values, unknown) == expected
