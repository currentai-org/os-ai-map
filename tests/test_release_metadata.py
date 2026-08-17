"""Release-metadata gate: the version records must agree, or a release lies about itself.

A release states its version in more than one place, and every one of them is easy to bump
in isolation. When they drift, nothing downstream errors — the wrong number just ships,
which is precisely the metadata drift the `publish-release` skill exists to prevent. This
test makes the agreement a gate instead of a hope.

Four records name a release's version. Three live in the tree and are checked on every PR:

  1. ``pyproject.toml``            -> ``[project].version``
  2. ``uv.lock``                   -> the root package (``source = { virtual = "." }``)
  3. ``CHANGELOG.md``              -> the newest DATED heading (``## [X.Y.Z] - DATE``),
                                      skipping the undated ``## [Unreleased]`` section

The fourth is the annotated git tag ``vX.Y.Z``. It only exists once a release is cut, so it
is checked only when a tag context is present (a tag-triggered CI run, or a maintainer
exporting ``RELEASE_TAG`` locally) — see ``test_git_tag_matches_when_in_tag_context``.
"""

import os
import re
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SEMVER = r"\d+\.\d+\.\d+"


def _pyproject_version() -> str:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def _uv_lock_root_version() -> str:
    """The version of THIS package in uv.lock — the entry whose source is the repo itself."""
    data = tomllib.loads((REPO / "uv.lock").read_text(encoding="utf-8"))
    roots = [
        p for p in data.get("package", [])
        if isinstance(p.get("source"), dict) and p["source"].get("virtual") == "."
    ]
    assert len(roots) == 1, f"expected exactly one root package in uv.lock, found {len(roots)}"
    return roots[0]["version"]


def _changelog_newest_dated_version() -> str:
    """The newest ``## [X.Y.Z] - YYYY-MM-DD`` heading, ignoring ``## [Unreleased]``."""
    text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(rf"^## \[({SEMVER})\]\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}\s*$", text, re.M)
    assert m, "CHANGELOG.md has no dated `## [X.Y.Z] - YYYY-MM-DD` release heading"
    return m.group(1)


def test_version_records_agree():
    """pyproject.toml, uv.lock root package, and the newest dated changelog entry match."""
    records = {
        "pyproject.toml": _pyproject_version(),
        "uv.lock (root package)": _uv_lock_root_version(),
        "CHANGELOG.md (newest dated)": _changelog_newest_dated_version(),
    }
    distinct = set(records.values())
    assert len(distinct) == 1, "version records disagree:\n" + "\n".join(
        f"  {name}: {value}" for name, value in records.items()
    )


def test_changelog_has_unreleased_section():
    """Keep a Changelog keeps a live `## [Unreleased]` section for the next change to land in."""
    text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(r"^## \[Unreleased\]\s*$", text, re.M), (
        "CHANGELOG.md is missing its `## [Unreleased]` section"
    )


def test_git_tag_matches_when_in_tag_context():
    """On a tag-triggered run, the tag must be `v<the agreed version>`.

    The tag is read from ``RELEASE_TAG`` or GitHub's ``GITHUB_REF_NAME`` (only meaningful when
    ``GITHUB_REF_TYPE`` is ``tag``). Outside a tag context the check is skipped — the three
    in-tree records above still gate every PR.
    """
    tag = os.environ.get("RELEASE_TAG")
    if not tag and os.environ.get("GITHUB_REF_TYPE") == "tag":
        tag = os.environ.get("GITHUB_REF_NAME")
    if not tag:
        return  # no tag context; nothing to assert
    assert tag == f"v{_pyproject_version()}", (
        f"tag {tag!r} does not match the release version v{_pyproject_version()}"
    )
