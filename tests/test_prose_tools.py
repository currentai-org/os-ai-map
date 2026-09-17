"""The three tools behind the prose pass: the selector, the diff gate, and the guarded editor.

Each is tested on synthetic records rather than on the corpus, because the corpus is the thing
the pass changes: a test that pinned "tesseract is flagged" would fail the day the pass reached
tesseract. The corpus-wide numbers are pinned as ratchets in tests/test_score_notes.py instead.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from build import prose_edit
from build.check_prose_diff import allowed, leaf_diffs
from build.prose_worklist import (
    NOTE_CEILING,
    comments_overlap,
    duplicated_figures,
    note_tells,
    vocabulary_hits,
)

ROOT = Path(__file__).resolve().parents[1]


# --- the selector ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "note, expected",
    [
        ("Rung 4, the competitive frontier.", ["Rung"]),
        ("It sits at band 3 on the software scale.", ["band 3"]),
        ("One below the anchor on the same table.", ["anchor"]),
        ("multi_sku_rule has nothing restrictive to resolve to.", ["multi_sku_rule"]),
        ("Level 5 here is measured, not inferred.", ["Level 5", "measured, not inferred"]),
        ("The band rests on stars, which cap at 3.", ["band rests on"]),
        ("No instrument exists for a hosted registry.", ["instrument"]),
    ],
)
def test_rubric_vocabulary_is_found(note, expected):
    assert vocabulary_hits(note) == expected


@pytest.mark.parametrize(
    "note",
    [
        "All three sizes ship under Apache-2.0, unusually for a Qwen release.",
        # "level with" and a band expressed as a range are English, not the rubric.
        "That puts it level with xLLM and RTP-LLM, in the 1M to 10M band.",
        "About 76k GitHub stars, the most in this category.",
    ],
)
def test_plain_prose_is_not_flagged(note):
    assert vocabulary_hits(note) == []


def test_two_restated_figures_are_a_table_set_as_a_sentence():
    shows = ["downloads: 7806497", "downloads: 2489577"]
    note = "12,549,679 downloads: 7,806,497 for the 0.6B and 2,489,577 for the 4B."
    assert duplicated_figures(note, shows) == ["7,806,497", "2,489,577"]
    assert "figure" in note_tells({"note": note, "sources": [{"shows": s} for s in shows]})


def test_one_restated_figure_is_a_claim_with_its_evidence():
    block = {"note": "About 76,518 GitHub stars, the most in this category.",
             "sources": [{"shows": "76,518 stargazers"}]}
    assert "figure" not in note_tells(block)


def test_the_template_openings_and_the_ceiling():
    assert "opening" in note_tells({"note": "Banded on the downloads of the client SDK."})
    # Short, factual and plain is not the defect, however many products share the sentence.
    assert "opening" not in note_tells({"note": "Apache-2.0 license body confirmed; public repo."})
    assert "opening" not in note_tells({"note": "Fully OSI-licensed (MIT), full source public."})
    assert "opening" not in note_tells({"note": "Milvus is a server with no channel of its own."})
    assert "length" in note_tells({"note": "x" * (NOTE_CEILING + 1)})
    assert "length" not in note_tells({"note": "x" * NOTE_CEILING})


def test_a_clean_note_has_no_tells():
    assert note_tells({"note": "LICENSE file is the standard, unmodified Apache 2.0 text. The "
                               "repository is public and unarchived."}) == {}
    assert note_tells({}) == {}


def test_a_footnote_that_restates_the_notes_is_measured():
    notes = ["The vendor's GGUF conversions and the separate Qwen3-VL-Embedding line are not counted."]
    assert comments_overlap("The GGUF conversions and the Qwen3-VL-Embedding line are excluded.", notes) > 0.6
    assert comments_overlap("GitHub's classifier cannot read the split license file.", notes) < 0.3
    assert comments_overlap("", notes) == 0.0


# --- the diff gate --------------------------------------------------------------------


def test_leaf_diffs_report_paths_and_treat_a_list_length_change_as_one_diff():
    before = {"openness": {"score": 4, "note": "a", "sources": [{"url": "u", "shows": "x"}]}}
    after = {"openness": {"score": 5, "note": "b", "sources": [{"url": "u", "shows": "y"}]}}
    assert leaf_diffs(before, after) == [
        ("openness", "note"), ("openness", "score"), ("openness", "sources", 0, "shows"),
    ]
    shorter = {"openness": {"score": 4, "note": "a", "sources": []}}
    assert leaf_diffs(before, shorter) == [("openness", "sources")]
    assert leaf_diffs({"comments": "x"}, {}) == [("comments",)]


@pytest.mark.parametrize(
    "kind, path, ok",
    [
        ("scores", ("openness", "note"), True),
        ("scores", ("adoption", "sources", 2, "shows"), True),
        ("scores", ("adoption", "level"), False),
        ("scores", ("openness", "last_verified"), False),
        ("scores", ("openness", "sources", 0, "url"), False),
        ("scores", ("openness", "sources", 0, "content_sha256"), False),
        ("scores", ("openness", "sources"), False),
        ("scores", ("openness", "components", "license"), False),
        ("products", ("comments",), True),
        ("products", ("description",), True),
        ("products", ("github",), False),
        ("categories", ("scoring_recipe", "note"), True),
        ("categories", ("products",), False),
        ("categories", ("weights", "adopt"), False),
    ],
)
def test_only_prose_leaves_are_allowed(kind, path, ok):
    assert allowed(kind, path) is ok


# --- the guarded editor ---------------------------------------------------------------


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """A two-file corpus under a temporary ROOT, so the editor writes nowhere real."""
    (tmp_path / "sources" / "scores").mkdir(parents=True)
    (tmp_path / "sources" / "products").mkdir(parents=True)
    shutil.copy(ROOT / "sources" / "scores" / "tesseract.yaml", tmp_path / "sources" / "scores")
    shutil.copy(ROOT / "sources" / "products" / "mastra.yaml", tmp_path / "sources" / "products")
    monkeypatch.setattr(prose_edit, "ROOT", tmp_path)
    return tmp_path


def _note(root, slug, axis):
    return yaml.safe_load((root / "sources" / "scores" / f"{slug}.yaml").read_text())[axis]["note"]


def test_a_note_is_rewritten_through_the_helper(corpus):
    new = ("About 76k GitHub stars, the most in this category. Stars are the only signal, and "
           "that understates a library embedded in a very large amount of other software.")
    assert prose_edit.edit_note("tesseract", "adoption", new) is None
    assert _note(corpus, "tesseract", "adoption") == new
    # Nothing else moved: the level, the date and the source are as they were.
    doc = yaml.safe_load((corpus / "sources" / "scores" / "tesseract.yaml").read_text())
    real = yaml.safe_load((ROOT / "sources" / "scores" / "tesseract.yaml").read_text())
    assert {k: v for k, v in doc["adoption"].items() if k != "note"} == \
        {k: v for k, v in real["adoption"].items() if k != "note"}


def test_dropping_a_pinned_under_coverage_phrase_is_refused(corpus):
    reason = prose_edit.edit_note("tesseract", "adoption", "About 76k GitHub stars, the most here.")
    assert reason and "UNDERSTATES" in reason
    assert _note(corpus, "tesseract", "adoption").startswith("76,518")
    assert prose_edit.edit_note("tesseract", "adoption", "About 76k GitHub stars, the most here.",
                                allow_phrase_change=True) is None


def test_an_empty_or_overlong_note_is_refused(corpus):
    assert "emptied" in prose_edit.edit_note("tesseract", "openness", "")
    assert "over the" in prose_edit.edit_note("tesseract", "openness", "x" * (NOTE_CEILING + 1))


def test_a_note_may_not_gain_a_date(corpus):
    reason = prose_edit.edit_note("tesseract", "openness", "Apache-2.0 since 2026-08-13, no vendor.")
    assert reason and "date" in reason


def test_a_shows_is_rewritten_by_index_and_may_not_be_emptied(corpus):
    assert prose_edit.edit_shows("tesseract", "openness", 1, "780-entry tree, one root LICENSE.") is None
    doc = yaml.safe_load((corpus / "sources" / "scores" / "tesseract.yaml").read_text())
    assert doc["openness"]["sources"][1]["shows"] == "780-entry tree, one root LICENSE."
    assert "emptied" in prose_edit.edit_shows("tesseract", "openness", 0, "")
    assert "no index" in prose_edit.edit_shows("tesseract", "openness", 9, "x")


def test_comments_can_be_rewritten_or_dropped_but_not_dated(corpus):
    path = corpus / "sources" / "products" / "mastra.yaml"
    assert "verification sentence" in prose_edit.edit_comments(
        "mastra", "Read from the body. Verified 2026-08-12 via the repository tree.")
    assert prose_edit.edit_comments("mastra", "GitHub's classifier cannot read the split license file.") is None
    assert yaml.safe_load(path.read_text())["comments"] == \
        "GitHub's classifier cannot read the split license file."
    assert prose_edit.edit_comments("mastra", None) is None
    assert "comments" not in yaml.safe_load(path.read_text())
    assert "no comments field" in prose_edit.edit_comments("mastra", None)
