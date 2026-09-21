"""Every workflow that runs unattended on `main` must be watched by the sentinel.

`report-failure.yml` turns a failed workflow into an issue somebody sees. It names the
workflows it watches in a literal list, because `workflow_run` requires one -- the list cannot be
computed at trigger time, so it has to be maintained by hand.

Which means it gets forgotten, and a forgotten entry is invisible: the workflow fails, nothing
opens, and the failure is found by somebody looking rather than by being told. That is exactly
how #631 happened -- `regenerate` failed on `main` and no issue appeared, because `regenerate`
was not on the list and nothing said it should be.

So the list stays hand-written and this makes it answerable to the workflows. A workflow runs
unattended when it carries a `schedule:` trigger or pushes to `main`: in both cases nobody is
watching a PR when it fails. Add one of those and the suite fails until the sentinel watches it,
or until the omission is written down here with a reason.

The reason matters more than the entry. A list of exclusions with no justifications is a list
that grows whenever somebody wants the suite to pass.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github/workflows"
SENTINEL = WORKFLOWS / "report-failure.yml"

#: Unattended workflows the sentinel deliberately does not watch, and why. Every entry needs a
#: reason that says how its failure reaches a person by another route.
UNWATCHED: dict[str, str] = {
    "report-failure": (
        "the sentinel itself. It can only run as a consequence of another workflow finishing, so "
        "watching it would either do nothing or recurse."
    ),
}


def _triggers(doc: dict) -> dict:
    """A workflow's `on:` block, whatever shape YAML gave it.

    `on` is the YAML 1.1 boolean `True`, so a plain `doc["on"]` misses it under safe_load and the
    check would silently pass on every workflow. A list form (`on: [push]`) carries no branch
    filter and is normalized to a dict so callers have one shape to read.
    """
    on = doc.get("on", doc.get(True)) or {}
    if isinstance(on, list):
        return {key: None for key in on}
    return on if isinstance(on, dict) else {}


def _runs_unattended(doc: dict) -> bool:
    """Does this workflow run where no one is watching a pull request?

    Two ways: a schedule, or a push to `main`. A pull-request-only workflow is excluded because
    its failure is already in front of the person who caused it.
    """
    on = _triggers(doc)
    if "schedule" in on:
        return True
    push = on.get("push") or {}
    return isinstance(push, dict) and "main" in (push.get("branches") or [])


def _name(path: Path, doc: dict) -> str:
    return doc.get("name") or path.stem


def unattended_workflows() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in sorted(WORKFLOWS.glob("*.yml")):
        doc = yaml.safe_load(path.read_text()) or {}
        if _runs_unattended(doc):
            out[_name(path, doc)] = path
    return out


def watched_workflows() -> list[str]:
    doc = yaml.safe_load(SENTINEL.read_text()) or {}
    return list((_triggers(doc).get("workflow_run") or {}).get("workflows") or [])


def test_every_unattended_workflow_is_watched_or_excused():
    missing = sorted(set(unattended_workflows()) - set(watched_workflows()) - set(UNWATCHED))
    assert not missing, (
        f"{len(missing)} workflow(s) run unattended on main and no sentinel watches them: "
        f"{', '.join(missing)}.\n\nA failure there opens nothing and is found by looking. Add each "
        f"to the `workflows:` list in .github/workflows/report-failure.yml, or to UNWATCHED here "
        f"with a reason saying how its failure reaches a person instead."
    )


def test_the_sentinel_watches_nothing_that_does_not_exist():
    """A watched name that matches no workflow is a typo doing nothing, and it reads as coverage."""
    unattended = unattended_workflows()
    every = {}
    for path in sorted(WORKFLOWS.glob("*.yml")):
        doc = yaml.safe_load(path.read_text()) or {}
        every[_name(path, doc)] = path
    unknown = sorted(set(watched_workflows()) - set(every))
    assert not unknown, f"the sentinel watches {unknown}, which name no workflow in {WORKFLOWS}"
    assert unattended, "no workflow reads as unattended, so this suite is checking nothing"


def test_every_exclusion_carries_a_reason():
    bare = sorted(name for name, reason in UNWATCHED.items() if not reason.strip())
    assert not bare, f"UNWATCHED entries with no reason: {bare}"


def test_the_scheduled_gates_are_all_covered():
    """The case that motivated the sentinel, pinned separately from the general rule: a weekly
    gate whose whole output is a queue somebody reads fails silently into an empty queue.
    """
    scheduled = {
        name
        for name, path in unattended_workflows().items()
        if "schedule" in _triggers(yaml.safe_load(path.read_text()) or {})
    }
    assert scheduled, "no scheduled workflow found, so this is checking nothing"
    uncovered = sorted(scheduled - set(watched_workflows()) - set(UNWATCHED))
    assert not uncovered, f"scheduled gates with no sentinel: {uncovered}"
