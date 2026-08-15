"""Per-product freshness for the serialized payload.

docs/reference/evidence-and-freshness.md is normative. Two tiers, and the payload says which one it used
so the page can label the weaker claim rather than passing it off as the stronger one:

  verified  every axis in the score file carries last_verified.
  partial   some axes are confirmed and at least one is deliberately not. The date is when
            the confirmed part was confirmed, and `verification_holds` names what is missing.
  commit    no axis carries a date. The date of the last commit that changed what
            sources/scores/<slug>.yaml claims. Commits that only changed how a score is
            stored are skipped, so a shape migration cannot republish a product as freshly
            reviewed.

## Why `partial` exists

Until 2026-08-15 this module took `max()` over the axes that HAD a date and ignored the ones
that did not, under a comment claiming the result was "the date on which everything in the
score was last standing". That is false whenever an axis is held: `falcon` carried
`adoption.last_verified: absent` — the axis is parked in `sources/verification_queue.yaml`
because its evidence contradicts its own band — and the payload still published
`{date: 2026-08-13, basis: verified}`. So did `qualcomm-ai-engine-direct` and `aws-neuron`.

The holds were honest inside the repo and invisible outside it, which is the same shape as
every other defect the 2026-08 audit found: a confirmation sitting on top of a non-answer,
one layer up. A held axis is a real editorial state and should not be forced into a score to
make a label tidy — so the payload says `partial` and carries the holds.

A date is NEVER derived from sources[].accessed (evidence-and-freshness.md,
"Why freshness is not max(sources[].accessed)").

There is nothing to fix in this module for that last point: it takes the commit tier
from `check_freshness.commit_dates`, which is where the skip lives, so the report and
the payload cannot disagree about what a commit date means.
"""
import subprocess
from pathlib import Path

import yaml

from build.check_freshness import commit_dates


class ShallowRepositoryError(RuntimeError):
    """Raised when git history is too shallow to date score files honestly."""


def _is_shallow(root: Path | None) -> bool:
    # An ambiguous or failed detection must never default to "not shallow, carry on" --
    # that is the same silent-wrong-date failure the guard exists to prevent, arriving
    # through a different door. `root` not being a git repository at all (exit 128, empty
    # stdout) used to read the same as a clean "false"; it must instead say plainly that
    # shallowness could not be determined, not that history is known to be shallow.
    try:
        out = subprocess.run(["git", "rev-parse", "--is-shallow-repository"],
                             cwd=root, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise ShallowRepositoryError(
            f"could not determine whether {root} is a shallow git checkout: git is not "
            "installed or not on PATH."
        ) from e
    if out.returncode != 0:
        raise ShallowRepositoryError(
            f"could not determine whether {root} is a shallow git checkout: "
            f"`git rev-parse --is-shallow-repository` exited {out.returncode} "
            f"({out.stderr.strip() or 'no stderr'})."
        )
    return out.stdout.strip() == "true"


def _commit_dates(root: Path | None) -> dict[str, str]:
    return {slug: d.isoformat() for slug, d in commit_dates(root).items()}


AXES = ("openness", "adoption", "capability")


def _axis_dates(root: Path | None) -> dict[str, tuple[dict[str, str], list[str]]]:
    """slug -> ({axis: date} for confirmed axes, [axis] for undated ones).

    Both halves are returned because the second is what distinguishes `verified` from
    `partial`, and dropping it is precisely the bug this replaced.
    """
    found: dict[str, tuple[dict[str, str], list[str]]] = {}
    for path in sorted((Path(root) / "sources" / "scores").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        dated: dict[str, str] = {}
        undated: list[str] = []
        for axis in AXES:
            block = doc.get(axis)
            if not isinstance(block, dict):
                continue
            value = block.get("last_verified")
            if value:
                dated[axis] = str(value)
            else:
                undated.append(axis)
        found[path.stem] = (dated, undated)
    return found


def held_axes(root: Path | None) -> dict[str, list[dict]]:
    """slug -> the axes parked in sources/verification_queue.yaml, with reasons.

    An undated axis is normally held — measured 2026-08-15, all 9 in the corpus are. One that
    is undated and NOT in the queue is a different state, and it still produces a `partial`
    basis; it simply carries no reason, which is what `check_freshness` and `sweep_status`
    already report on.
    """
    # `root=None` means the current directory, matching `_is_shallow`'s subprocess cwd.
    path = Path(root or ".") / "sources" / "verification_queue.yaml"
    if not path.exists():
        return {}
    queue = (yaml.safe_load(path.read_text()) or {}).get("held") or {}
    out: dict[str, list[dict]] = {}
    for slug, axes in queue.items():
        for axis, spec in (axes or {}).items():
            entry = {"axis": axis, "since": str((spec or {}).get("since") or "")}
            reason = (spec or {}).get("because")
            if reason:
                entry["reason"] = " ".join(str(reason).split())
            out.setdefault(slug, []).append(entry)
    return {slug: sorted(v, key=lambda e: e["axis"]) for slug, v in out.items()}


def resolve_freshness(root: Path | None) -> dict[str, dict]:
    if _is_shallow(root):
        raise ShallowRepositoryError(
            "git history is shallow, so score-file commit dates would all collapse to the "
            "tip commit. Add `fetch-depth: 0` to the checkout step, or run in a full clone."
        )
    axis_dates = _axis_dates(root)
    commits = _commit_dates(root)
    holds = held_axes(root)
    out: dict[str, dict] = {}
    for slug in sorted(set(axis_dates) | set(commits)):
        dated, undated = axis_dates.get(slug, ({}, []))
        if dated:
            # The date is still the most recent confirmation, which is what it always was.
            # What changes is that it no longer claims to cover an axis that has none.
            record = {
                "date": max(dated.values()),
                "basis": "verified" if not undated else "partial",
            }
            if undated:
                record["unconfirmed_axes"] = sorted(undated)
                if slug in holds:
                    record["verification_holds"] = holds[slug]
        elif slug in commits:
            record = {"date": commits[slug], "basis": "commit"}
        else:
            continue
        out[slug] = record
    return out
