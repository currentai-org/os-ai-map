import json
import subprocess
from pathlib import Path

import pytest

import build.check_retirement as cr
from build.check_retirement import RetirementCheckError, _previous_payload, main


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)


def _commit(root: Path, message: str, *, allow_empty: bool = False) -> None:
    args = ["git", "-c", "user.email=test@example.com", "-c", "user.name=test",
            "commit", "-q", "-m", message]
    if allow_empty:
        args.append("--allow-empty")
    subprocess.run(args, cwd=root, check=True, capture_output=True)


def _commit_payload(root: Path, payload: dict, message: str = "payload") -> None:
    build_dir = root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "notebook_data.json").write_text(json.dumps(payload))
    subprocess.run(["git", "add", "build/notebook_data.json"], cwd=root, check=True, capture_output=True)
    _commit(root, message)


def _write_new_payload(root: Path, payload: dict) -> None:
    build_dir = root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "notebook_data.json").write_text(json.dumps(payload))


def _payload(slugs: list[str], aliases: dict | None = None) -> dict:
    return {
        "categories": {"c": {"products": [{"slug": s} for s in slugs]}},
        "aliases": {"products": aliases or {}, "organizations": {}},
    }


# --- _previous_payload: the split this module exists to get right. `git show
# HEAD:<payload>` fails with the same exit code (128) whether the payload was simply never
# committed (a legitimate first run) or something is actually broken (no repository, no
# commit yet, git missing). Only the first of those may read as "skip". ---

def test_returns_none_when_head_has_never_carried_the_payload(tmp_path):
    _init_repo(tmp_path)
    _commit(tmp_path, "init", allow_empty=True)
    assert _previous_payload(tmp_path) is None


def test_raises_when_root_is_not_a_git_repository(tmp_path):
    """Named for the exact confusion the module's docstring calls out: this must not be
    read the same as 'no previous payload'."""
    with pytest.raises(RetirementCheckError):
        _previous_payload(tmp_path)


def test_raises_when_head_has_no_commit_yet(tmp_path):
    """An initialized repo with zero commits: HEAD does not resolve at all. Still not the
    same failure as 'no previous payload' -- there is no payload path to even ask about."""
    _init_repo(tmp_path)
    with pytest.raises(RetirementCheckError):
        _previous_payload(tmp_path)


def test_raises_when_git_binary_is_missing(tmp_path, monkeypatch):
    def _no_git(*args, **kwargs):
        raise FileNotFoundError("git")
    monkeypatch.setattr(cr.subprocess, "run", _no_git)
    with pytest.raises(RetirementCheckError):
        _previous_payload(tmp_path)


def test_returns_the_committed_payload_when_present(tmp_path):
    _init_repo(tmp_path)
    _commit_payload(tmp_path, _payload(["a", "b"]))
    assert _previous_payload(tmp_path) == _payload(["a", "b"])


def test_raises_when_the_committed_payload_is_not_valid_json(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "notebook_data.json").write_text("{not json")
    subprocess.run(["git", "add", "build/notebook_data.json"], cwd=tmp_path, check=True, capture_output=True)
    _commit(tmp_path, "bad json")
    with pytest.raises(RetirementCheckError):
        _previous_payload(tmp_path)


# --- main(): the retirement/alias behavior itself, plus proof the git-failure paths
# above actually reach main() rather than being swallowed on the way there. ---

def test_exits_nonzero_when_a_retired_slug_has_no_alias(tmp_path, monkeypatch, capsys):
    """The failure this file is named after: drop a slug with no alias and watch it go red."""
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _init_repo(tmp_path)
    _commit_payload(tmp_path, _payload(["a", "b"]))
    _write_new_payload(tmp_path, _payload(["a"]))
    assert main() == 1
    assert "b" in capsys.readouterr().err


def test_exits_zero_when_a_retired_slug_is_aliased(tmp_path, monkeypatch):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _init_repo(tmp_path)
    _commit_payload(tmp_path, _payload(["a", "b"]))
    _write_new_payload(tmp_path, _payload(["a"], aliases={"b": "a"}))
    assert main() == 0


def test_exits_zero_on_a_first_run_with_no_committed_payload(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _init_repo(tmp_path)
    _commit(tmp_path, "init", allow_empty=True)
    _write_new_payload(tmp_path, _payload(["a"]))
    assert main() == 0
    assert "skipping" in capsys.readouterr().out


def test_exits_nonzero_rather_than_skipping_when_root_is_not_a_git_repository(tmp_path, monkeypatch, capsys):
    """The failure this whole module is designed around: a check that cannot tell 'no
    history to compare' apart from 'no history I could READ' must not silently pass
    either way. This must go red, and for the right reason (a git failure it could not
    interpret), not the accidental red of an unrelated crash."""
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _write_new_payload(tmp_path, _payload(["a"]))
    assert main() == 1
    assert "could not check retired slugs" in capsys.readouterr().err
