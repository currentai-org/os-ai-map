import os
import subprocess
from datetime import date
from pathlib import Path

import pytest

import build.freshness_payload as fp
from build.freshness_payload import ShallowRepositoryError, resolve_freshness


def _git(*args: str, cwd: Path, env: dict | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=env)


def _init_repo_with_one_score(root: Path, slug: str, commit_date: str) -> None:
    """A throwaway git repository, distinct from this checkout, with exactly one score
    file committed on a fabricated date. Used to prove root-scoping is real rather than
    mocked: this slug and this date exist nowhere in os-ai-map's own history."""
    scores = root / "sources" / "scores"
    scores.mkdir(parents=True)
    (scores / f"{slug}.yaml").write_text("openness:\n  score: 3\n")
    _git("init", "-q", cwd=root)
    _git("-c", "user.email=test@example.com", "-c", "user.name=test",
         "add", "sources/scores", cwd=root)
    env = {**os.environ, "GIT_AUTHOR_DATE": f"{commit_date}T00:00:00",
           "GIT_COMMITTER_DATE": f"{commit_date}T00:00:00"}
    _git("-c", "user.email=test@example.com", "-c", "user.name=test",
         "commit", "-q", "-m", "add score", cwd=root, env=env)


def test_refuses_to_emit_dates_in_a_shallow_clone(tmp_path, monkeypatch):
    """Named for the failure it guards: a --depth 1 checkout dates every score file to the
    tip commit, silently, so all 470 products would publish the same freshness date."""
    monkeypatch.setattr("build.freshness_payload._is_shallow", lambda root: True)
    with pytest.raises(ShallowRepositoryError):
        resolve_freshness(tmp_path)


def test_last_verified_outranks_the_commit_date(tmp_path, monkeypatch):
    monkeypatch.setattr("build.freshness_payload._is_shallow", lambda root: False)
    monkeypatch.setattr("build.freshness_payload._commit_dates", lambda root: {"apertus": "2026-08-05"})
    monkeypatch.setattr("build.freshness_payload._last_verified", lambda root: {"apertus": "2026-07-30"})
    assert resolve_freshness(tmp_path)["apertus"] == {"date": "2026-07-30", "basis": "verified"}


def test_falls_back_to_the_commit_date_and_says_so(monkeypatch):
    """The basis is what lets the page label the weaker claim honestly.

    Uses monkeypatch (not a bare module-attribute assignment) so the substitution is
    reverted after this test — an unguarded `fp._last_verified = ...` here previously
    clobbered the real implementation for every test that ran after it in this file.
    """
    monkeypatch.setattr(fp, "_is_shallow", lambda root: False)
    monkeypatch.setattr(fp, "_commit_dates", lambda root: {"vllm": "2026-06-04"})
    monkeypatch.setattr(fp, "_last_verified", lambda root: {})
    assert fp.resolve_freshness(None)["vllm"] == {"date": "2026-06-04", "basis": "commit"}


def test_last_verified_takes_the_most_recent_date_across_axes(tmp_path):
    """The three tests above all mock `_last_verified` away, so none of them exercise its
    real glob-and-aggregate logic. A product with last_verified on more than one axis must
    report the latest of them, not the first one read or the openness axis specifically."""
    scores = tmp_path / "sources" / "scores"
    scores.mkdir(parents=True)
    (scores / "multi-axis.yaml").write_text(
        "openness:\n  last_verified: '2026-07-01'\n"
        "adoption:\n  last_verified: '2026-07-15'\n"
        "capability:\n  score: 3\n"
    )
    (scores / "no-verification.yaml").write_text("openness:\n  score: 2\n")
    found = fp._last_verified(tmp_path)
    assert found == {"multi-axis": "2026-07-15"}, \
        "must take the max across axes, and must not invent a date for an unverified product"


def test_commit_dates_converts_date_objects_to_isoformat_strings(monkeypatch):
    """`check_freshness.commit_dates()` returns real `date` objects; the payload needs JSON-
    serializable strings, and the conversion must preserve every slug it is handed."""
    monkeypatch.setattr(fp, "commit_dates",
                        lambda root=None: {"vllm": date(2026, 6, 4), "olmo": date(2026, 7, 30)})
    assert fp._commit_dates(None) == {"vllm": "2026-06-04", "olmo": "2026-07-30"}


def test_is_shallow_raises_when_root_is_not_a_git_repository(tmp_path):
    """`git rev-parse` exits 128 with empty stdout when `root` is not a git repository at
    all. The old code read that the same as a clean 'false' -- ambiguous or failed
    detection defaulting to the safe-looking branch is the exact failure the guard exists
    to prevent, arriving through a different door."""
    with pytest.raises(ShallowRepositoryError):
        fp._is_shallow(tmp_path)


def test_is_shallow_raises_when_git_binary_is_missing(tmp_path, monkeypatch):
    """git absent from PATH must fail the same way as git failing: loudly, not as 'false'."""
    def _no_git(*args, **kwargs):
        raise FileNotFoundError("git")
    monkeypatch.setattr(fp.subprocess, "run", _no_git)
    with pytest.raises(ShallowRepositoryError):
        fp._is_shallow(tmp_path)


def test_resolve_freshness_raises_when_root_is_not_a_git_repository(tmp_path):
    """The public entry point must surface the same failure, not just the private helper."""
    (tmp_path / "sources" / "scores").mkdir(parents=True)
    with pytest.raises(ShallowRepositoryError):
        resolve_freshness(tmp_path)


def test_commit_dates_are_scoped_to_the_given_root_not_this_repository(tmp_path):
    """`_commit_dates` used to ignore its own `root` argument and read THIS repository's
    history via check_freshness's module-level ROOT constant. Prove root-scoping is real:
    a throwaway repo with one score file, committed on a date that appears nowhere in
    os-ai-map's own history, for a slug that does not exist in os-ai-map at all. If root
    were ignored, this slug would be missing entirely (real history has no such file)."""
    _init_repo_with_one_score(tmp_path, "throwaway-product", "2020-01-01")
    assert resolve_freshness(tmp_path) == {
        "throwaway-product": {"date": "2020-01-01", "basis": "commit"}
    }
