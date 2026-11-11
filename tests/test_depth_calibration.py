"""The full-roster depth calibration reproduces from the repository.

These pin the headline figures of docs/sweeps/2026-11-03-depth-calibration-full-roster.md to
`build.depth_calibration` run over `sources/`, so the record cannot drift from the data it
describes. A coverage, lineage or rule change that moves one of them fails here: update the record
and these figures together, in the same PR.
"""
from __future__ import annotations

import pytest

from build import depth_calibration as dc
from build import depth_ladder
from build import lineage
from build.depth_calibration import ROOT
from build.own_components import is_own


def include_claim() -> dict:
    """INCLUDE's own-slug claim, as its score record states it (R-2026-11-03-i)."""
    return next(c for c in dc.record_claims("include-benchmark")
                if c["component"] == "include-benchmark")


INCLUDE_IMPORTED = frozenset(include_claim()["except_languages"])
INCLUDE_MIXED = frozenset(include_claim()["mixed_languages"])

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


RECORD = ROOT / "docs/sweeps/2026-11-03-depth-calibration-full-roster.md"
LABELS = {
    "flores-plus": "FLORES+", "fleurs": "FLEURS", "belebele": "Belebele", "sib-200": "SIB-200",
    "include-benchmark": "INCLUDE", "afrobench": "AfroBench", "milu": "MILU",
    "indicgenbench": "IndicGenBench", "indicxtreme": "IndicXTREME", "lahaja": "Lahaja",
    "sea-helm": "SEA-HELM", "seaexam": "SeaExam", "thai-exam": "ThaiExam", "vmlu": "VMLU",
    "laobench": "LaoBench", "indonlu": "IndoNLU", "arabicmmlu": "ArabicMMLU",
    "darijammlu": "DarijaMMLU", "turkishmmlu": "TurkishMMLU", "kazmmlu": "KazMMLU",
    "khayyam-challenge": "Khayyam Challenge", "americasnlp-shared-task-data": "AmericasNLP",
}


def _table_rows() -> list[list[str]]:
    lines = RECORD.read_text().split("## Results", 1)[1].splitlines()
    rows = [ln for ln in lines if ln.startswith("| ")]
    return [[c.strip() for c in r.strip("|").split("|")] for r in rows[1:]]  # skip the header


PUBLICATION = ROOT / "docs/sweeps/2026-11-08-depth-ladder-publication.md"


def _scores_before_publication() -> dict[str, str]:
    """The publication record's "Main score" column: each set's score before the ladder published
    (R-2026-11-07-b), keyed by the record's display name."""
    section = PUBLICATION.read_text().split("## The score-change diff", 1)[1].split("\n## ", 1)[0]
    lines = section.splitlines()
    rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines if ln.startswith("| ")]
    return {r[0]: r[1] for r in rows[1:]}  # skip the header


def test_the_record_s_table_matches_the_calibration(results):
    """Every row of the record's results table, in roster order, against the module's output.

    The table's "now" column is the score the map published on 2026-11-03, before the ladder
    replaced it. It is checked against the publication record's "Main score" column, which states
    the same pre-publication score, and the score recorded today is checked against the band the
    ladder publishes."""
    rows = _table_rows()
    assert len(rows) == len(dc.ROSTER)
    assert [r[0] for r in rows] == [LABELS[slug] for slug in dc.ROSTER]
    before = _scores_before_publication()
    names = {"americasnlp-shared-task-data": "AmericasNLP shared-task data"}
    for slug, (_, now, a_band, b_band, face, bonus, measured, capped) in zip(dc.ROSTER, rows):
        a, b = results[slug]["a"], results[slug]["b"]
        unresolved = a["band"].startswith("unresolved")
        assert now == before[names.get(slug, LABELS[slug])], slug
        assert a["score_now"] == (None if unresolved else int(a["band"])), slug
        assert a_band == a["band"], slug
        assert b_band == ("same" if unresolved and b["band"] == a["band"] else b["band"]), slug
        # The table shortens an unresolved face value to "unresolved"; anything else is exact.
        face_unresolved = a["face_value"].startswith("unresolved")
        assert face == ("unresolved" if face_unresolved else a["face_value"]), slug
        assert bonus == ("" if a["bonus"] is None else f"{a['bonus']:.2f}"), slug
        assert measured == f"{a['measured']} / {a['targets']}", slug
        assert capped == str(len(a["capped"])), slug


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
    assert results["include-benchmark"]["a"]["capped"] == sorted(INCLUDE_IMPORTED)
    assert all(results["include-benchmark"]["a"]["per_language"][lang] == 1
               for lang in INCLUDE_IMPORTED)


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
    assert imported == INCLUDE_IMPORTED
    assert mixed == INCLUDE_MIXED


def test_include_s_imported_languages_are_derived_in_lineage(doc):
    """R-2026-11-03-i: where INCLUDE carries a parent's items, its effective lineage is the
    parent's, not INCLUDE's own exams, so later comparisons see no false shared collection."""
    rec = next(c for c in doc["components"] if c["id"] == "include-benchmark")
    for lang in INCLUDE_IMPORTED:
        eff = lineage.effective(rec, lang)
        assert eff["origin"] == "derived" and eff["collections"] == [], lang
        assert "include-local-exams" not in (eff["effort"], *eff["collections"]), lang
        parent = next(c for c in doc["components"] if c["id"] == eff["parents"][0])
        assert eff["effort"] == parent["effort"], lang
    for lang in INCLUDE_MIXED:
        assert "include-local-exams" in lineage.effective(rec, lang)["collections"], lang


@pytest.mark.parametrize("count, expected", [
    (0, 0), (1, 1), (99, 1), (100, 2), (399, 2), (400, 3), (1600, 4), (6399, 4), (6400, 5),
])
def test_the_count_ladder(count, expected):
    assert dc.band(count) == expected


def owns(slug, component, language):
    entry = {"component": component, "language": language, "task": "any", "split": "test"}
    return is_own(slug, entry, dc.record_claims(slug))


def test_ownership_scopes_from_the_records():
    assert not owns("include-benchmark", "include-benchmark", "ara")
    assert owns("include-benchmark", "include-benchmark", "deu")
    assert owns("indicgenbench", "flores-in", "brx")
    assert not owns("indicgenbench", "flores-in", "hin")
    assert not owns("indicgenbench", "crosssum-in", "nep")
    assert owns("indicgenbench", "crosssum-in", "asm")
    # A set's own slug is its own by default; an unclaimed import is not.
    assert owns("sea-helm", "sea-helm", "tha")
    assert not owns("sea-helm", "xnli", "tha")


# The scopes build/depth_calibration.py held as constants before #978 moved them into the records.
# Pinned here so that an edit to a claim, which would move a band, fails until the record and these
# figures change together.
EXPECTED_CLAIMS = {
    "include-benchmark": {"include-benchmark": ("except", {"ara", "tur"})},
    "sea-helm": {"sea-mt-bench-judge": None, "kalahi-judge": None},
    "indicxtreme": {"indiccopa": None, "indicqa": None, "indicxparaphrase": None,
                    "indicsentiment": None},
    "indicgenbench": {
        "flores-in": ("only", {"bgc", "brx", "gbm", "gom", "hoj", "mup", "mwr"}),
        "crosssum-in": ("except", {"ben", "guj", "hin", "mar", "nep", "pan", "pus", "tam", "tel",
                                   "urd"}),
        "xquad-in": None,
        "xorqa-in": ("except", {"ben", "tel"}),
    },
}


def test_the_record_claims_are_the_calibrated_scopes():
    got = {}
    for slug in dc.ROSTER:
        claims = dc.record_claims(slug)
        if not claims:
            continue
        got[slug] = {}
        for c in claims:
            assert not (c.keys() & {"tasks", "splits"}), (slug, c["component"])
            if "languages" in c:
                got[slug][c["component"]] = ("only", set(c["languages"]))
            elif "except_languages" in c:
                got[slug][c["component"]] = ("except", set(c["except_languages"]))
            else:
                got[slug][c["component"]] = None
    assert got == EXPECTED_CLAIMS
    assert INCLUDE_MIXED == {"deu", "fas", "fra", "ita", "lit", "pol", "por", "sqi", "vie", "zho"}


# --- the method on hand-built inputs -----------------------------------------------------------
# The figures above pin the method's output on the records; these check the method itself, so a
# change to D5 or the median that happened to leave the roster's bands alone still fails here.


def comp(component, band, task="knowledge_exam"):
    return {"component": component, "language": "xxx", "band": band, "task": task, "split": "test"}


@pytest.fixture
def pairs(monkeypatch):
    """Stub lineage: `table` maps a frozenset pair to its status; anything else is dependent."""
    table = {}

    def pair_status(doc, a, b, language=None, **kw):
        return lineage.PairStatus(table.get(frozenset((a, b)), "dependent"), "stub")

    # The ladder binds `pair_status` by name, so the stub replaces it where the ladder reads it.
    monkeypatch.setattr(depth_ladder, "pair_status", pair_status)
    return table


def band_of(comps, *, loose=False):
    return dc.language_band({}, "own", "xxx", comps, loose=loose, claims=[])


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
