"""The licence-body gate: a record that disputes GitHub's classifier must cite the file."""
from pathlib import Path

import yaml

from build.check_license_body import BODY, disputed, failures


def _write(tmp_path: Path, slug: str, note: str, urls: list[str]) -> Path:
    (tmp_path / f"{slug}.yaml").write_text(
        yaml.safe_dump(
            {
                "product": slug,
                "openness": {
                    "score": 5,
                    "class": "open_source",
                    "note": note,
                    "sources": [{"url": u} for u in urls],
                },
            },
            sort_keys=False,
        )
    )
    return tmp_path


def test_a_record_that_never_mentions_the_classifier_is_out_of_scope(tmp_path):
    _write(tmp_path, "quiet", "Apache-2.0 throughout.", ["https://github.com/o/r"])
    assert disputed(tmp_path) == []
    assert failures(tmp_path) == []


def test_disputing_the_classifier_without_the_body_fails(tmp_path):
    _write(tmp_path, "loud", "GitHub reports NOASSERTION; the body is Apache-2.0.",
           ["https://github.com/o/r", "https://api.github.com/repos/o/r"])
    assert failures(tmp_path) == ["loud"]


def test_the_endpoint_that_returned_noassertion_cannot_answer_the_dispute(tmp_path):
    """`/license` is the API that reports NOASSERTION, so citing it is circular."""
    _write(tmp_path, "circular", "The API reports NOASSERTION.",
           ["https://api.github.com/repos/o/r/license"])
    assert failures(tmp_path) == ["circular"]


def test_a_raw_body_satisfies_it(tmp_path):
    _write(tmp_path, "cited", "GitHub reports NOASSERTION because of a preamble.",
           ["https://raw.githubusercontent.com/o/r/main/LICENSE"])
    assert failures(tmp_path) == []


def test_a_blob_view_of_a_licence_file_satisfies_it(tmp_path):
    _write(tmp_path, "blob", "NOASSERTION, but the COPYING body is GPL.",
           ["https://github.com/o/r/blob/main/COPYING"])
    assert failures(tmp_path) == []


def test_the_pattern_does_not_match_an_ordinary_repo_page():
    assert not BODY("https://github.com/o/r")
    assert not BODY("https://api.github.com/repos/o/r/license")
    assert BODY("https://raw.githubusercontent.com/o/r/main/LICENSE.md")


def test_the_live_corpus_passes():
    """The ratchet: 23 records dispute the classifier today and all 23 cite the body."""
    assert failures() == []
