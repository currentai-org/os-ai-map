"""The license-body gate: a record that disputes GitHub's classifier must cite the file."""
from pathlib import Path

import pytest
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


def test_a_blob_view_of_a_license_file_satisfies_it(tmp_path):
    _write(tmp_path, "blob", "NOASSERTION, but the COPYING body is GPL.",
           ["https://github.com/o/r/blob/main/COPYING"])
    assert failures(tmp_path) == []


@pytest.mark.parametrize(
    "url",
    [
        "https://raw.githubusercontent.com/o/r/main/LICENSE",
        "https://raw.githubusercontent.com/o/r/main/LICENSE.md",
        "https://github.com/o/r/blob/main/COPYING",
        "https://github.com/o/r/blob/main/legal/LICENCE.txt",
        "https://github.com/o/r/blob/main/LICENSE-APACHE",
        # A fragment or a query follows the filename and must not defeat the match. The
        # first draft anchored on the end of the whole URL and rejected both.
        "https://github.com/o/r/blob/main/LICENSE.md#L1",
        "https://example.com/legal/LICENSE?download=1",
    ],
)
def test_a_license_file_is_a_body(url):
    assert BODY(url)


@pytest.mark.parametrize(
    "url, why",
    [
        ("https://github.com/o/r", "a repository page names no file"),
        ("https://api.github.com/repos/o/r/license", "the endpoint that returned NOASSERTION"),
        # The first draft accepted all three of these on a substring match.
        ("https://raw.githubusercontent.com/o/r/main/README.md", "a raw URL is not automatically a license"),
        ("https://github.com/o/r/blob/main/NOT_A_LICENSE.txt", "contains the word, is not the file"),
        ("https://github.com/o/LICENSE", "a repository that happens to be named LICENSE"),
    ],
)
def test_what_is_not_a_body(url, why):
    assert not BODY(url), why


def test_the_live_corpus_passes():
    """The ratchet: 23 records dispute the classifier today and all 23 cite the body."""
    assert failures() == []
