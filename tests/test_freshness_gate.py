"""The age gate's exit status.

`--max-age-days N` exits non-zero when a category's oldest axis is over N days old, and zero
when nothing is. `docs/guides/freshness.md` owns the rule and `docs/guides/verification.md`
step 5 owns the window.

Every fixture here is built from dates these tests choose, and `--today` pins the clock. That
is deliberate: a test that borrowed a currently-stale record from `sources/` would pass only
until somebody re-read that category, which is exactly how
`test_relabelling_to_reported_traction_does_not_buy_a_pass` expired once already. Nothing here
reads the corpus.

The fixture is a real git repository with one commit, because `collect` dates a fallback axis
from git history. Every axis below carries a `last_verified`, so no test depends on what that
history says — the repository exists so the walk has something to open.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml

from build.check_freshness import main

TODAY = "2026-08-14"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "T",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "T",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        },
    )


def _corpus(tmp_path: Path, categories: dict[str, dict[str, str | None]]) -> Path:
    """Build a checkout from {category: {product: last_verified or None}}.

    A `None` date writes a score block with no `last_verified`, which is the fallback case.
    """
    (tmp_path / "sources" / "categories").mkdir(parents=True)
    (tmp_path / "sources" / "scores").mkdir(parents=True)

    for category, products in categories.items():
        (tmp_path / "sources" / "categories" / f"{category}.yaml").write_text(
            yaml.safe_dump({"name": category, "products": sorted(products)}, sort_keys=False)
        )
        for product, verified in products.items():
            axes = {}
            for axis, value in (("openness", {"score": 5}), ("adoption", {"level": 3}),
                                ("capability", {"score": 4})):
                axes[axis] = dict(value)
                if verified is not None:
                    axes[axis]["last_verified"] = verified
            (tmp_path / "sources" / "scores" / f"{product}.yaml").write_text(
                yaml.safe_dump({"product": product, **axes}, sort_keys=False)
            )

    _git(tmp_path, "init", "-q", "-b", "main", str(tmp_path))
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "corpus")
    return tmp_path


def _run(root: Path, *args: str) -> int:
    return main([*args, "--today", TODAY], root=root)


def test_everything_inside_the_window_passes(tmp_path):
    root = _corpus(tmp_path, {"widgets": {"a": "2026-08-13", "b": "2026-07-20"}})

    assert _run(root, "--max-age-days", "30") == 0


def test_an_axis_over_the_window_fails(tmp_path):
    """25 days is inside, 31 is not, and one axis over the line is enough."""
    root = _corpus(tmp_path, {"widgets": {"a": "2026-07-20", "b": "2026-07-14"}})

    assert _run(root, "--max-age-days", "30") == 1


def test_the_boundary_is_older_than_rather_than_at(tmp_path):
    """Exactly N days old is inside the window; N + 1 is not."""
    at_the_line = _corpus(tmp_path / "at", {"widgets": {"a": "2026-07-15"}})
    a_day_past = _corpus(tmp_path / "past", {"widgets": {"a": "2026-07-14"}})

    assert _run(at_the_line, "--max-age-days", "30") == 0
    assert _run(a_day_past, "--max-age-days", "30") == 1


def test_a_stale_category_does_not_fail_a_fresh_one_when_scoped(tmp_path):
    """--category limits the gate, which is what makes it usable while re-reading one."""
    root = _corpus(tmp_path, {"fresh": {"a": "2026-08-13"}, "stale": {"b": "2026-06-01"}})

    assert _run(root, "--max-age-days", "30") == 1
    assert _run(root, "--category", "fresh", "--max-age-days", "30") == 0
    assert _run(root, "--category", "stale", "--max-age-days", "30") == 1


def test_without_the_flag_a_stale_corpus_still_exits_zero(tmp_path):
    """The report stays safe to run for information. validate.yml depends on this."""
    root = _corpus(tmp_path, {"widgets": {"a": "2026-01-01"}})

    assert _run(root) == 0


def test_the_failure_names_the_category_and_what_to_do(tmp_path, capsys):
    """A gate whose output does not say what to go and do gets ignored."""
    root = _corpus(tmp_path, {"stale": {"b": "2026-06-01"}})

    assert _run(root, "--max-age-days", "30") == 1
    out = capsys.readouterr().out
    assert "stale" in out
    assert "refresh-category" in out
    assert "verification.md" in out


def test_a_fallback_age_is_labeled_rather_than_counted_as_confirmed(tmp_path, capsys):
    """An axis with no last_verified is dated from git, and the report has to say so."""
    root = _corpus(tmp_path, {"widgets": {"dated": "2026-08-13", "undated": None}})

    assert _run(root, "--max-age-days", "30") == 0
    out = capsys.readouterr().out
    assert "3 of 6 axes carry a real last_verified" in out


def test_an_axis_with_no_date_at_all_fails_the_gate(tmp_path, capsys):
    """The commit-date fallback is unavailable for a file git has never seen, so the window
    has nothing to measure. Unmeasurable is a failure, not a pass."""
    root = _corpus(tmp_path, {"widgets": {"a": "2026-08-13"}})
    (root / "sources" / "categories" / "widgets.yaml").write_text(
        yaml.safe_dump({"name": "widgets", "products": ["a", "uncommitted"]}, sort_keys=False)
    )
    (root / "sources" / "scores" / "uncommitted.yaml").write_text(
        yaml.safe_dump({"product": "uncommitted", "openness": {"score": 5}}, sort_keys=False)
    )

    assert _run(root, "--max-age-days", "30") == 1
    assert "no date for the window to measure" in capsys.readouterr().out
