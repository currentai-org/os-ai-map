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

import fnmatch
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github/workflows"
SENTINEL = WORKFLOWS / "report-failure.yml"


def _workflow_files() -> list[Path]:
    """Every workflow file. GitHub accepts `.yaml` as well as `.yml`, and a gate that reads only
    one of them is a gate a new file can be added past without noticing.
    """
    return sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])

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
    check would silently pass on every workflow. The value takes three shapes and all of them
    normalize to a dict so callers read one: a bare string (`on: push`), a list (`on: [push]`)
    -- neither of which carries a branch filter -- and a mapping.
    """
    on = doc.get("on", doc.get(True)) or {}
    if isinstance(on, str):
        return {on: None}
    if isinstance(on, list):
        return {key: None for key in on}
    return on if isinstance(on, dict) else {}


MAIN = "main"


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _push_can_reach_main(on: dict) -> bool:
    """Could a push to `main` run this workflow?

    Asked this way round on purpose. The first version asked whether `branches` literally
    contained `main`, which answered no for five shapes that all reach it: `on: push`,
    `on: [push]`, a `push:` mapping with no filter, `branches-ignore` naming some other branch,
    and `branches: ['**']`. A workflow written any of those ways would run unattended on main
    while the coverage gate reported it covered.

    So the default is that a push event reaches `main`, and only an explicit filter that
    excludes it says otherwise. `fnmatch` because a branch filter is a glob, and `**` and `*`
    both match a branch with no `/` in it.
    """
    if "push" not in on:
        return False
    push = on.get("push")
    if not isinstance(push, dict):
        return True  # `on: push` / `on: [push]` -- no filter at all
    ignored = _as_list(push.get("branches-ignore"))
    if any(fnmatch.fnmatch(MAIN, pattern) for pattern in ignored):
        return False
    allowed = _as_list(push.get("branches"))
    if not allowed:
        return True  # a push mapping with no branch filter
    return any(fnmatch.fnmatch(MAIN, pattern) for pattern in allowed)


def _runs_unattended(doc: dict) -> bool:
    """Does this workflow run where no one is watching a pull request?

    Two ways: a schedule, or a push that can reach `main`. A pull-request-only workflow is
    excluded because its failure is already in front of the person who caused it.
    """
    on = _triggers(doc)
    return "schedule" in on or _push_can_reach_main(on)


def _name(path: Path, doc: dict) -> str:
    return doc.get("name") or path.stem


def unattended_workflows() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in _workflow_files():
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
    for path in _workflow_files():
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


# ---------------------------------------------------------------------------
# what counts as reaching main
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [
        "on: push",                                   # scalar, no filter
        "on: [push]",                                 # list, no filter
        "on:\n  push: {}",                            # mapping, no filter
        "on:\n  push:\n    branches: [main]",
        "on:\n  push:\n    branches: [main, develop]",
        "on:\n  push:\n    branches: ['**']",         # glob covering everything
        "on:\n  push:\n    branches: ['*']",
        "on:\n  push:\n    branches-ignore: [dev]",   # excludes something else
        "on:\n  push:\n    branches: main",           # scalar branch
    ],
)
def test_these_push_shapes_reach_main(source):
    """Each of these runs on a push to main. The first version of this check asked whether
    `branches` literally contained `main`, and answered no for five of them -- a workflow written
    any of those ways would have run unattended while the gate reported it covered.
    """
    assert _runs_unattended(yaml.safe_load(source)), source


@pytest.mark.parametrize(
    "source",
    [
        "on:\n  push:\n    branches: [develop]",
        "on:\n  push:\n    branches-ignore: [main]",
        "on:\n  push:\n    branches-ignore: ['ma*']",
        "on:\n  pull_request:\n    branches: [main]",  # a PR is attended by definition
        "on:\n  workflow_call: {}",
    ],
)
def test_these_do_not(source):
    """The gate has to be able to answer no, or the cases above prove nothing."""
    assert not _runs_unattended(yaml.safe_load(source)), source


def test_a_schedule_counts_however_the_push_is_filtered():
    assert _runs_unattended(yaml.safe_load("on:\n  schedule:\n    - cron: '0 6 * * 1'"))
    assert _runs_unattended(
        yaml.safe_load("on:\n  schedule:\n    - cron: '0 6 * * 1'\n  push:\n    branches: [develop]")
    )


def test_the_yaml_boolean_trap_is_handled():
    """`on` is the YAML 1.1 boolean True, so a plain doc["on"] finds nothing and every check
    would pass on every workflow.
    """
    doc = yaml.safe_load("on:\n  schedule:\n    - cron: '0 6 * * 1'")
    assert "on" not in doc and True in doc, "safe_load no longer folds `on` to True; simplify _triggers"
    assert _triggers(doc), "the boolean key is not being read"


def test_both_workflow_extensions_are_scanned():
    """GitHub accepts .yaml as well as .yml, and a gate reading one of them is a gate a new file
    can be added past.
    """
    suffixes = {path.suffix for path in _workflow_files()}
    assert suffixes <= {".yml", ".yaml"}
    globbed = {p.name for p in WORKFLOWS.glob("*.yml")} | {p.name for p in WORKFLOWS.glob("*.yaml")}
    assert {p.name for p in _workflow_files()} == globbed
