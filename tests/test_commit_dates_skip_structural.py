"""The commit-date fallback must date a claim, not a reshape.

`docs/reference/evidence-and-freshness.md` says the fallback dates the last commit that left the score
standing — a review. A commit that only changes how a score is *stored* reviewed nothing,
so it must not move the date.

Phase 1a is the case that forced this: `openness.components` becomes a mapping carrying a
byte-identical `raw:` copy of the string it replaced. No claim moves, but the file is
committed, and the naive fallback would republish every touched product as freshly
reviewed on the migration date.

Every test here builds a real git repository and makes real commits. Mocking `git log`
would restate the implementation rather than test it, and the thing under test is exactly
what git reports.
"""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import yaml

from build.check_freshness import commit_dates
from build.check_rubric import structure

STRING_FORM = """product: widget
openness:
  score: 5
  class: open_source
  components: license:Apache-2.0(OSI);source:public;core-gated:ungated;governance:vLLM-project(community,PyTorch-ecosystem
    adjacent)
  confidence: high
adoption:
  level: 4
  reach: 1M-10M
"""


def _run(repo: Path, *args: str, when: str | None = None) -> None:
    env = None
    if when is not None:
        stamp = f"{when}T12:00:00+00:00"
        env = {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        env={**_base_env(), **(env or {})},
    )


def _base_env() -> dict[str, str]:
    import os

    return {
        **os.environ,
        "GIT_AUTHOR_NAME": "T",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "T",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }


def _repo(tmp_path: Path) -> Path:
    _run(tmp_path, "init", "-q", "-b", "main", str(tmp_path))
    (tmp_path / "sources" / "scores").mkdir(parents=True)
    return tmp_path


def _commit(repo: Path, slug: str, text: str, when: str, message: str = "change") -> None:
    (repo / "sources" / "scores" / f"{slug}.yaml").write_text(text)
    _run(repo, "add", "-A")
    _run(repo, "commit", "-q", "-m", message, when=when)


def _migrated(text: str) -> str:
    """The Phase 1a reshape: components becomes a mapping, the string moves to `raw`."""
    doc = yaml.safe_load(text)
    raw = doc["openness"]["components"]
    doc["openness"]["components"] = structure(raw)
    doc["openness"]["raw"] = raw
    return yaml.safe_dump(doc, sort_keys=False, width=100)


def test_a_structural_reshape_does_not_advance_the_date(tmp_path):
    """The defect. Migrating the components shape re-verified nothing."""
    repo = _repo(tmp_path)
    _commit(repo, "widget", STRING_FORM, "2026-06-01", "score widget")
    _commit(repo, "widget", _migrated(STRING_FORM), "2026-08-11", "migrate components shape")

    assert commit_dates(repo)["widget"] == date(2026, 6, 1)


def test_a_changed_claim_still_advances_the_date(tmp_path):
    """The converse. A fix that froze every date would be worse than the bug."""
    repo = _repo(tmp_path)
    _commit(repo, "widget", STRING_FORM, "2026-06-01", "score widget")
    _commit(repo, "widget", STRING_FORM.replace("score: 5", "score: 4"), "2026-08-11", "correct score")

    assert commit_dates(repo)["widget"] == date(2026, 8, 11)


def test_a_reshape_that_also_changes_a_component_advances_the_date(tmp_path):
    """A migration that mangled one value is a claim change, and must be dated as one."""
    repo = _repo(tmp_path)
    _commit(repo, "widget", STRING_FORM, "2026-06-01", "score widget")
    mangled = _migrated(STRING_FORM).replace("value: ungated", "value: gated")
    assert "value: gated" in mangled
    _commit(repo, "widget", mangled, "2026-08-11", "migrate components shape")

    assert commit_dates(repo)["widget"] == date(2026, 8, 11)


def test_a_reshape_that_drops_a_keyless_clause_advances_the_date(tmp_path):
    """`free_text` is published in the flat string, so losing one is not score-neutral."""
    repo = _repo(tmp_path)
    with_keyless = STRING_FORM.replace(
        "components: license:Apache-2.0(OSI)", "components: no-model-card;license:Apache-2.0(OSI)"
    )
    _commit(repo, "widget", with_keyless, "2026-06-01", "score widget")
    doc = yaml.safe_load(_migrated(with_keyless))
    doc["openness"]["components"].pop("free_text")
    doc["openness"]["raw"] = doc["openness"]["raw"].replace("no-model-card;", "")
    _commit(repo, "widget", yaml.safe_dump(doc, sort_keys=False, width=100), "2026-08-11", "migrate")

    assert commit_dates(repo)["widget"] == date(2026, 8, 11)


def test_consecutive_structural_commits_are_all_skipped(tmp_path):
    """Six migration batches, and a reformat on top, must not stack into a fresh date."""
    repo = _repo(tmp_path)
    _commit(repo, "widget", STRING_FORM, "2026-06-01", "score widget")
    _commit(repo, "widget", _migrated(STRING_FORM), "2026-08-11", "migrate components shape")
    reflowed = _migrated(STRING_FORM).replace("\nadoption:", "\n\nadoption:")
    _commit(repo, "widget", reflowed, "2026-08-12", "reflow")

    assert commit_dates(repo)["widget"] == date(2026, 6, 1)


def test_a_file_never_touched_since_it_was_added_keeps_its_add_date(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, "widget", STRING_FORM, "2026-06-01", "score widget")

    assert commit_dates(repo)["widget"] == date(2026, 6, 1)


def test_the_walk_survives_an_unparseable_revision_in_history(tmp_path):
    """Nothing crashes, and the date is the commit that made the file readable.

    Note this passes on either rule: the two revisions also differ, so `before != after`
    would carry it. The rule that an unparseable blob COUNTS AS a change is pinned by the
    test below, where that comparison cannot fire.
    """
    repo = _repo(tmp_path)
    _commit(repo, "widget", "product: widget\nopenness: [unclosed\n", "2026-06-01", "wip")
    _commit(repo, "widget", STRING_FORM, "2026-08-11", "score widget")

    assert commit_dates(repo)["widget"] == date(2026, 8, 11)


def test_two_unparseable_revisions_are_not_treated_as_score_identical(tmp_path):
    """Both revisions project to None, so only the None-as-change rule can date this.

    Equality alone would call the commit structural — None == None — skip it, and hand
    back the older date. A revision nothing can read has not been SHOWN score-neutral, and
    the walk must not infer that it was.
    """
    repo = _repo(tmp_path)
    _commit(repo, "widget", STRING_FORM, "2026-06-01", "score widget")
    _commit(repo, "widget", "product: widget\nopenness: [unclosed\n", "2026-07-01", "wip")
    _commit(repo, "widget", "product: widget\nopenness: [still unclosed\n", "2026-08-11", "wip")

    assert commit_dates(repo)["widget"] == date(2026, 8, 11)


def test_other_files_in_a_structural_commit_are_unaffected(tmp_path):
    """One commit can be structural for one file and substantive for another."""
    repo = _repo(tmp_path)
    _commit(repo, "widget", STRING_FORM, "2026-06-01", "score widget")
    (repo / "sources" / "scores" / "gadget.yaml").write_text(STRING_FORM.replace("widget", "gadget"))
    _run(repo, "add", "-A")
    _run(repo, "commit", "-q", "-m", "add gadget", when="2026-07-01")

    (repo / "sources" / "scores" / "widget.yaml").write_text(_migrated(STRING_FORM))
    (repo / "sources" / "scores" / "gadget.yaml").write_text(
        STRING_FORM.replace("widget", "gadget").replace("score: 5", "score: 3")
    )
    _run(repo, "add", "-A")
    _run(repo, "commit", "-q", "-m", "migrate widget, correct gadget", when="2026-08-11")

    dates = commit_dates(repo)
    assert dates["widget"] == date(2026, 6, 1)
    assert dates["gadget"] == date(2026, 8, 11)


def test_a_deleted_file_keeps_the_date_of_its_last_real_change(tmp_path):
    """Deletion is not a reshape; it must not crash the walk either."""
    repo = _repo(tmp_path)
    _commit(repo, "widget", STRING_FORM, "2026-06-01", "score widget")
    (repo / "sources" / "scores" / "widget.yaml").unlink()
    _run(repo, "add", "-A")
    _run(repo, "commit", "-q", "-m", "retire widget", when="2026-08-11")

    assert commit_dates(repo)["widget"] == date(2026, 8, 11)
