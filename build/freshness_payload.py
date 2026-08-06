"""Per-product freshness for the serialized payload.

docs/guides/freshness.md is normative. Two tiers, and the payload says which one it used
so the page can label the weaker claim rather than passing it off as the stronger one:

  verified  the score file carries last_verified. 6 of 470 today.
  commit    the git commit date of sources/scores/<slug>.yaml.

A date is NEVER derived from sources[].accessed (freshness.md:30).
"""
import subprocess
from pathlib import Path

import yaml

from build.check_freshness import commit_dates


class ShallowRepositoryError(RuntimeError):
    """Raised when git history is too shallow to date score files honestly."""


def _is_shallow(root: Path | None) -> bool:
    out = subprocess.run(["git", "rev-parse", "--is-shallow-repository"],
                         cwd=root, capture_output=True, text=True)
    return out.stdout.strip() == "true"


def _commit_dates(root: Path | None) -> dict[str, str]:
    return {slug: d.isoformat() for slug, d in commit_dates().items()}


def _last_verified(root: Path | None) -> dict[str, str]:
    found: dict[str, str] = {}
    for path in sorted((Path(root) / "sources" / "scores").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        for axis in ("openness", "adoption", "capability"):
            value = (doc.get(axis) or {}).get("last_verified")
            if value:
                # Most recent confirmation across axes wins; it is the date on which
                # everything in the score was last standing.
                current = found.get(path.stem)
                found[path.stem] = max(current, str(value)) if current else str(value)
    return found


def resolve_freshness(root: Path | None) -> dict[str, dict]:
    if _is_shallow(root):
        raise ShallowRepositoryError(
            "git history is shallow, so score-file commit dates would all collapse to the "
            "tip commit. Add `fetch-depth: 0` to the checkout step, or run in a full clone."
        )
    verified = _last_verified(root)
    commits = _commit_dates(root)
    out: dict[str, dict] = {}
    for slug in sorted(set(verified) | set(commits)):
        if slug in verified:
            out[slug] = {"date": verified[slug], "basis": "verified"}
        else:
            out[slug] = {"date": commits[slug], "basis": "commit"}
    return out
