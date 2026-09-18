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
    description_tells,
    usage_figures,
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
        ("The band rests on stars, which cap at 3.", ["The band", "rests on", "cap at 3"]),
        ("No instrument exists for a hosted registry.", ["instrument"]),
        # The scorer's shorthand the editor named while reading the goldens.
        ("What holds it at 3 is the data question.", ["holds it at", "at 3"][:1]),
        ("Its client SDK stands in for the server.", ["stands in"]),
        ("Qdrant is read the same way through its client.", ["is read the same way"]),
        ("Blaxel, a band lower, lacks durable functions.", ["a band lower"]),
        ("A server has no countable channel of its own.", ["countable channel"]),
        # A band range or rank in prose is the Reach row talking.
        ("Together they land LightRAG in the 100K-1M download band.", ["100K-1M download band"]),
        ("That places it in the top adoption band.", ["the top adoption band"]),
        ("About 76k stars, the most in this category.", ["the most in this category"]),
    ],
)
def test_rubric_vocabulary_is_found(note, expected):
    assert vocabulary_hits(note) == expected


@pytest.mark.parametrize(
    "note",
    [
        "All three sizes ship under Apache-2.0, unusually for a Qwen release.",
        # "level with" is English, not the rubric.
        "That puts it level with xLLM and RTP-LLM on feature breadth.",
        "GitHub stars are the only adoption signal published, and a star is not a use.",
    ],
)
def test_plain_prose_is_not_flagged(note):
    assert vocabulary_hits(note) == []


@pytest.mark.parametrize(
    "note",
    [
        "12,549,679 downloads across the three checkpoints.",
        "About 76k GitHub stars, the most in this category.",
        "About 12.5 million Hugging Face downloads a month.",
        "About 500 GitHub stars is the only signal published.",
        "pymilvus records about 6 million PyPI downloads a month.",
        "Roughly 2,962 downloads in the trailing 30 days.",
    ],
)
def test_a_usage_figure_in_a_note_is_flagged(note):
    """The count is stale the day the source refreshes; it lives in the source line."""
    assert usage_figures(note)
    assert "figure" in note_tells({"note": note})


@pytest.mark.parametrize(
    "note",
    [
        # Facts about the product, not about its use.
        "An 8B model with a 32k context window supporting more than 100 languages.",
        "Harrier-OSS has since overtaken it with a score of 74.3.",
        "Median time-to-interactive of 1.35 seconds on the independent benchmark.",
        "Five accelerator vendors plus pure CPU, across three checkpoint sizes.",
        "The registry stopped at 1.0.4 while the repository is on 2.1.0.",
        "Released under Apache-2.0 and installs with pip; GPL-3.0 users need the other build.",
        "An 8,192-token context window and 1,024-dimension embeddings.",
        "Embeddings of 1,536 dimensions over a 128,000-token context.",
        "Independent benchmarks report 2,100 tokens per second on an H100 and 1,850 tok/s on a B200.",
    ],
)
def test_a_product_fact_with_a_number_is_not_a_usage_figure(note):
    assert usage_figures(note) == []


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


def test_a_note_under_the_guard_but_over_the_shape_is_flagged_as_advice():
    long_two = {"note": "A" * 410 + ". B."}
    assert "shape" in note_tells(long_two) and "length" not in note_tells(long_two)
    three = {"note": "One fact. Two facts. Three facts."}
    assert note_tells(three)["shape"] == [len(three["note"]), 3]
    assert note_tells({"note": "One fact. Two facts."}) == {}


@pytest.mark.parametrize("text, key", [
    ("This record scores the hosted tier.", "self_reference"),
    ("The engine we ship to your cluster.", "voice"),
    ("Released 2026-01-02 as a preview.", "date"),
    ("A rung-4 framework.", "vocabulary"),
])
def test_a_description_written_for_the_wrong_audience_is_flagged(text, key):
    assert key in description_tells(text)


def test_a_plain_description_is_clean():
    assert description_tells("Self-hosted chat interface with native support for OpenAI, "
                             "Anthropic and local backends, plus multi-user authentication.") == {}


@pytest.mark.parametrize("text", [
    "OCR toolkit with table, formula and seal recognition in more than a hundred languages.",
    "It instruments applications through OpenTelemetry.",
    "Texas Instruments' AM67A vision processor with an 8-TOPS accelerator.",
    "Six benchmarks including GPQA Diamond and MATH Level 5, scored on 40 models.",
    "Trained on the Solar Dynamics Observatory's AIA and HMI instruments at native resolution.",
])
def test_english_that_shares_a_word_with_the_rubric_is_not_a_tell(text):
    assert "vocabulary" not in description_tells(text)


@pytest.mark.parametrize("text", [
    "That volume is what places it in the higher usage band.",
    "Dynamo is one band below vLLM.",
    "No download count exists to band, so no reach word is recorded.",
    "Adoption bands on stars.",
    "The band was re-derived against the current page.",
])
def test_band_as_the_name_of_a_score_is_a_tell(text):
    assert vocabulary_hits(text)


@pytest.mark.parametrize("text", [
    "It stops short of the top level, reserved for a platform that hosts its own models.",
    "Downloads clear the threshold for this reading by a narrow margin.",
    "Not the voyage-4-nano checkpoint the openness score covers.",
])
def test_the_rung_described_as_a_place_is_a_tell(text):
    assert vocabulary_hits(text)


@pytest.mark.parametrize("text", [
    "An Earth Engine ImageCollection of 64-band annual embedding images.",
    "Weights from the wavelengths of whatever bands are supplied.",
    "The stat band still reads 94% of Fortune 100.",
])
def test_a_spectral_band_is_english(text):
    assert vocabulary_hits(text) == []


def test_a_product_named_you_com_is_not_second_person():
    assert "voice" not in description_tells("You.com search API returning web results as JSON.")


def test_a_description_is_rewritten_through_the_helper_and_guarded(corpus):
    assert prose_edit.edit_description("mastra", "") is not None
    assert "self_reference" in prose_edit.edit_description("mastra", "This record covers the SDK.")
    assert "voice" in prose_edit.edit_description("mastra", "We ship an SDK.")
    assert prose_edit.edit_description("mastra", "TypeScript agent framework with a workflow engine.") is None
    doc = yaml.safe_load((corpus / "sources" / "products" / "mastra.yaml").read_text())
    assert doc["description"] == "TypeScript agent framework with a workflow engine."


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
        ("scores", ("capability", "comparison", "sources", 0, "shows"), True),
        ("scores", ("capability", "comparison", "sources", 0, "url"), False),
        ("scores", ("capability", "comparison", "last_attested"), False),
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


# The tesseract record as it stood before the pass: an adoption note that opens with the star
# count and carries the pinned "understates" admission, and an openness note without one. A
# synthetic copy rather than the live file, because the pass rewrote the live note and a test
# that read it would have failed the day it did.
OLD_TESSERACT = """product: tesseract
openness:
  score: 5
  class: open_source
  note: Apache-2.0 with no vendor gate; the whole engine is in the public repository.
  sources:
  - url: https://github.com/tesseract-ocr/tesseract
    shows: LICENSE is Apache-2.0.
  - url: https://api.github.com/repos/tesseract-ocr/tesseract/git/trees/main?recursive=1
    shows: The whole tree; one LICENSE file at the root and no enterprise directory.
adoption:
  level: 3
  reach: '>10K stars'
  signal_type: stars_fallback
  confidence: low
  note: 76,518 GitHub stars, the most in this category. Stars are the only comparable adoption
    signal, and that almost certainly understates a library embedded in a very large amount of
    other software.
  last_verified: '2026-09-16'
  sources:
  - url: https://github.com/tesseract-ocr/tesseract
    shows: Repository page showing the star count for tesseract-ocr/tesseract.
    accessed: '2026-09-16'
capability:
  score: 4
  note: Plain OCR of printed text with layout analysis; no handwriting model.
"""


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """A two-file corpus under a temporary ROOT, so the editor writes nowhere real."""
    (tmp_path / "sources" / "scores").mkdir(parents=True)
    (tmp_path / "sources" / "products").mkdir(parents=True)
    (tmp_path / "sources" / "scores" / "tesseract.yaml").write_text(OLD_TESSERACT)
    shutil.copy(ROOT / "sources" / "products" / "mastra.yaml", tmp_path / "sources" / "products")
    monkeypatch.setattr(prose_edit, "ROOT", tmp_path)
    return tmp_path


def _note(root, slug, axis):
    return yaml.safe_load((root / "sources" / "scores" / f"{slug}.yaml").read_text())[axis]["note"]


def test_a_note_is_rewritten_through_the_helper(corpus):
    new = ("Stars are the only public signal for the library, and that understates one embedded "
           "in a very large amount of other software.")
    assert prose_edit.edit_note("tesseract", "adoption", new) is None
    assert _note(corpus, "tesseract", "adoption") == new
    # Nothing else moved: the level, the date and the source are as they were.
    doc = yaml.safe_load((corpus / "sources" / "scores" / "tesseract.yaml").read_text())
    before = yaml.safe_load(OLD_TESSERACT)
    assert {k: v for k, v in doc["adoption"].items() if k != "note"} == \
        {k: v for k, v in before["adoption"].items() if k != "note"}


def test_dropping_a_pinned_under_coverage_phrase_is_refused(corpus):
    reason = prose_edit.edit_note("tesseract", "adoption", "Stars are the only public signal.")
    assert reason and "UNDERSTATES" in reason
    assert _note(corpus, "tesseract", "adoption").startswith("76,518")
    assert prose_edit.edit_note("tesseract", "adoption", "Stars are the only public signal.",
                                allow_phrase_change=True) is None


def test_the_editor_refuses_the_rules_the_gate_reads(corpus):
    """Review of #620: the editor refused an emptied note and a lost date but not the rubric's
    words, a template opening or a fresh usage figure, so those could come back through it
    while the suite stayed red. Now what the editor accepts, the gate accepts."""
    keep = "Stars are the only signal, and that understates a library embedded in other software."
    assert "rubric" in prose_edit.edit_note("tesseract", "adoption", keep + " The band rests on stars.")
    assert "template" in prose_edit.edit_note("tesseract", "adoption", "Verified MIT; " + keep)
    assert "figure" in prose_edit.edit_note("tesseract", "adoption", "About 80k GitHub stars. " + keep)
    # A figure the old note already carried is not a new one; the pass may keep it.
    assert prose_edit.edit_note("tesseract", "adoption", "76,518 GitHub stars. " + keep) is None
    assert "rubric" in prose_edit.edit_shows("tesseract", "openness", 0, "The band rests on this file.")


def test_introducing_a_pinned_under_coverage_phrase_is_refused(corpus):
    """The other direction: the wave wrote "primary distribution channel" into notes that had
    never made the admission, and the pinned set grew by six products in one batch."""
    reason = prose_edit.edit_note(
        "tesseract", "openness",
        "Apache-2.0 with no vendor; PyPI is not the product's primary distribution channel.")
    assert reason and "introduces" in reason
    assert _note(corpus, "tesseract", "openness").startswith("Apache-2.0 with no vendor")


def test_an_empty_or_overlong_note_is_refused(corpus):
    assert "emptied" in prose_edit.edit_note("tesseract", "openness", "")
    assert "over the" in prose_edit.edit_note("tesseract", "openness", "x" * (NOTE_CEILING + 1))


def test_a_hard_wrapped_draft_is_read_as_one_line(tmp_path):
    """A reviewer's draft with newlines for readability embedded them in the published note."""
    draft = tmp_path / "note.txt"
    draft.write_text("Tesseract is distributed as source\n  and through packages.\n")
    assert prose_edit._read_text(str(draft)) == "Tesseract is distributed as source and through packages."


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
