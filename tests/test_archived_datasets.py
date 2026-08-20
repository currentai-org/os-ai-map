"""An archived dataset must not be described anywhere as if it were current.

The point of archiving is that a reader who finds the table knows not to trust it. That only
holds if the docs agree, and docs are where this repo has drifted before: on 2026-08-19 the
schedule section named a parity time the workflow had never used, and the PR carrying it claimed
the repo had been searched.

So the archive list lives here, in code, and every mention of an archived table in the docs has
to carry a word that says so. Adding a dataset to ARCHIVED without updating the prose fails.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# table prefix -> the date it was archived, for the message only
ARCHIVED = {
    "currentai.stack_map.": "2026-08-20",
}
# Words that mark a mention as historical rather than a recommendation.
MARKERS = ("archived", "superseded", "frozen", "deprecated", "retired", "do not")

DOC_GLOBS = ("docs/**/*.md", "warehouse/**/*.md", "AGENTS.md", "README.md", "skills/**/*.md")


def doc_files() -> list[Path]:
    out: list[Path] = []
    for pattern in DOC_GLOBS:
        out.extend(p for p in ROOT.glob(pattern) if p.is_file())
    return sorted(set(out))


@pytest.mark.parametrize("prefix", sorted(ARCHIVED))
def test_no_doc_presents_an_archived_table_as_current(prefix: str):
    offenders: list[str] = []
    for path in doc_files():
        for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if prefix not in line:
                continue
            if not any(m in line.lower() for m in MARKERS):
                offenders.append(f"{path.relative_to(ROOT)}:{i}: {line.strip()[:100]}")
    assert not offenders, (
        f"{prefix} was archived {ARCHIVED[prefix]}, but these lines describe it without saying "
        f"so — a reader would take them as current:\n  " + "\n  ".join(offenders)
    )


def test_the_archive_list_is_not_empty_and_the_check_can_fail():
    """Guard on the guard: an empty ARCHIVED map would make the test above vacuous."""
    assert ARCHIVED, "nothing archived; delete this test rather than leaving it green by default"
    # And prove the marker logic actually rejects an unmarked mention.
    line = "query currentai.stack_map.product_scores for adoption"
    assert not any(m in line.lower() for m in MARKERS)
