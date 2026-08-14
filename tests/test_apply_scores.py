"""Tests for the one tool that writes into `sources/scores/`.

`build/apply_scores.py` is the only thing allowed to change a score file without a
person typing the value, which makes what it will NOT touch as much a part of its
contract as what it will.

The regression these pin is not hypothetical. Two separate releases taught the tool to
write `openness.last_verified` from an aggregate of source access dates — #108 the MIN,
#115 the MAX — and between them they put a derived date on 19 of the 26 axes that
carried one, in six cases overwriting a date a person had established by checking. The
normative rule is in `docs/reference/evidence-and-freshness.md`: `last_verified` is a human's
confirmation that everything in the score is still correct, and no aggregation of
readings produces it.

So the first test asserts an absence, deliberately. It fails the moment anyone
reintroduces the write, whatever aggregate they reach for and however plausible the
column name.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from build.apply_scores import apply_to_file, block_bounds, find_key, has_date

SCORE = """\
product: demo
openness:
  score: 3
  class: open_weights
  components: weights:open;data:closed;code:partial;license:Apache-2.0
  confidence: high
  note: A demo product.
  last_verified: '2026-06-01'
  sources:
  - url: https://example.invalid/model
    shows: Apache-2.0 in the model card
    accessed: '2026-07-29'
adoption:
  level: 3
"""


def write(tmp_path: Path, text: str = SCORE) -> Path:
    path = tmp_path / "demo.yaml"
    path.write_text(text)
    return path


@pytest.mark.parametrize(
    "computed",
    [
        {"openness_score": 3, "openness_class": "open_weights", "last_checked": "2026-07-29"},
        # The shapes the two regressions actually arrived in.
        {"openness_score": 3, "openness_class": "open_weights", "freshness_floor": "2026-07-29"},
        {"openness_score": 3, "openness_class": "open_weights", "last_checked": "2026-12-31"},
    ],
)
def test_never_writes_last_verified(tmp_path, computed):
    """No computed date, under any column name, may reach the file."""
    path = write(tmp_path)
    new_lines, changes = apply_to_file(path, computed)
    assert "".join(new_lines).count("last_verified") == 1, "must not add a second one"
    assert "  last_verified: '2026-06-01'\n" in new_lines, "the human's date is untouched"
    assert not any("last_verified" in c for c in changes), f"reported a date change: {changes}"


def test_does_not_add_last_verified_to_a_file_without_one():
    """The earlier writer INSERTED the key before `sources:`. That must not happen."""
    text = SCORE.replace("  last_verified: '2026-06-01'\n", "")
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = write(Path(tmp), text)
        new_lines, _ = apply_to_file(
            path, {"openness_score": 3, "openness_class": "open_weights",
                   "last_checked": "2026-07-29"}
        )
        assert "last_verified" not in "".join(new_lines)


def test_writes_score_and_class_when_they_move(tmp_path):
    """The half of the contract that is a write, so the absence tests cannot pass vacuously."""
    path = write(tmp_path)
    new_lines, changes = apply_to_file(
        path, {"openness_score": 2, "openness_class": "restricted"}
    )
    joined = "".join(new_lines)
    assert "  score: 2\n" in joined and "  class: restricted\n" in joined
    assert len(changes) == 2, changes


def test_leaves_human_prose_alone(tmp_path):
    """note, components, confidence and sources are human judgment."""
    path = write(tmp_path)
    new_lines, _ = apply_to_file(
        path, {"openness_score": 2, "openness_class": "restricted",
               "last_checked": "2026-07-29"}
    )
    joined = "".join(new_lines)
    for line in ("  note: A demo product.\n",
                 "  components: weights:open;data:closed;code:partial;license:Apache-2.0\n",
                 "  confidence: high\n",
                 "    accessed: '2026-07-29'\n"):
        assert line in joined, f"rewrote {line.strip()!r}"


def test_null_score_changes_nothing(tmp_path):
    """A product the rubric declined to score must not be edited toward a guess."""
    path = write(tmp_path)
    new_lines, changes = apply_to_file(path, {"openness_score": None, "openness_class": None})
    assert "".join(new_lines) == SCORE and not changes


def test_find_key_ignores_deeper_indentation(tmp_path):
    """`accessed` sits under a sources entry; a nested key is a different key."""
    lines = SCORE.splitlines(keepends=True)
    bounds = block_bounds(lines, "openness")
    assert bounds is not None
    assert find_key(lines, bounds, "accessed") is None
    assert find_key(lines, bounds, "score") is not None


@pytest.mark.parametrize("value,expected", [
    (None, False), ("", False), ("NaT", False), ("nan", False), ("None", False),
    ("2026-07-29", True),
])
def test_has_date_rejects_the_dataframe_nulls(value, expected):
    """A null DATE arrives as NaT or nan depending on dtype, and both pass `is not None`."""
    assert has_date(value) is expected
