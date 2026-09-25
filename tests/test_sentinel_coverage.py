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


#: Characters in a branch filter that `fnmatch` does not read the way GitHub does. `+` and `?`
#: are quantifiers there, applying to the PRECEDING character -- `ma+in` and `ma?in` both match
#: `main`, while `fnmatch` reads `?` as exactly one character of any kind and so matches neither.
#: `!` negates, with order mattering across the list. Rather than reimplement GitHub's pattern
#: language for a gate, a filter using any of them is treated as possibly reaching `main` -- see
#: `_push_can_reach_main` for why that is the safe direction.
_UNREADABLE_PATTERN = ("!", "+", "?")


def _matches_main(patterns: list[str]) -> bool | None:
    """Does any pattern match `main`? `None` when the filter cannot be read faithfully."""
    if any(char in pattern for pattern in patterns for char in _UNREADABLE_PATTERN):
        return None
    return any(fnmatch.fnmatch(MAIN, pattern) for pattern in patterns)


def _push_can_reach_main(on: dict) -> bool:
    """Could a push to `main` run this workflow?

    Asked this way round on purpose. The first version asked whether `branches` literally
    contained `main`, which answered no for five shapes that all reach it: `on: push`,
    `on: [push]`, a `push:` mapping with no filter, `branches-ignore` naming some other branch,
    and `branches: ['**']`. A workflow written any of those ways would run unattended on main
    while the coverage gate reported it covered.

    So the default is that a push event reaches `main`, and only a filter that demonstrably
    excludes it says otherwise. Where a filter cannot be read faithfully -- GitHub's pattern
    language has `+` and ordered `!` negation, which `fnmatch` does not -- this answers YES.
    The two errors are not equal: over-reporting costs somebody a watch entry or a written
    exemption, and under-reporting is a workflow failing on main with nothing to say so, which
    is the defect this whole file exists to prevent.

    A push filtered to tags only is the one shape that does NOT reach a branch push. GitHub runs
    no branch push when `tags`/`tags-ignore` is the only filter given.
    """
    if "push" not in on:
        return False
    push = on.get("push")
    if not isinstance(push, dict):
        return True  # `on: push` / `on: [push]` -- no filter at all
    ignored = _as_list(push.get("branches-ignore"))
    if ignored:
        excluded = _matches_main(ignored)
        if excluded:
            return False
        if excluded is None:
            return True  # cannot read it; assume it reaches main
    allowed = _as_list(push.get("branches"))
    if allowed:
        reached = _matches_main(allowed)
        return True if reached is None else reached
    if not ignored and (push.get("tags") is not None or push.get("tags-ignore") is not None):
        return False  # tags only: no branch push runs this
    return True


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
# the retry and the auto-close
# ---------------------------------------------------------------------------

#: What a workflow does that a blind re-run of a job failed after it could do twice.
WRITES = ("git push", "gh pr create", "gh issue create", "gh issue comment", "create-pull-request")


def retryable() -> list[str]:
    doc = yaml.safe_load(SENTINEL.read_text()) or {}
    return str((doc.get("env") or {}).get("RETRYABLE", "")).split()


def _workflow_by_name(name: str) -> Path:
    for path in _workflow_files():
        if _name(path, yaml.safe_load(path.read_text()) or {}) == name:
            return path
    raise AssertionError(f"no workflow named {name!r}")


def test_only_watched_workflows_are_retried():
    extra = sorted(set(retryable()) - set(watched_workflows()))
    assert retryable(), "RETRYABLE is empty, so the retry never fires"
    assert not extra, f"RETRYABLE names workflows the sentinel does not watch: {extra}"


def test_no_workflow_that_writes_is_retried():
    """A re-run of a job that failed after opening a PR or pushing would do it twice."""
    writers = {
        name: [w for w in WRITES if w in _workflow_by_name(name).read_text()]
        for name in retryable()
    }
    offenders = {name: found for name, found in writers.items() if found}
    assert not offenders, f"RETRYABLE includes workflows that write: {offenders}"


def test_a_green_unattended_run_closes_the_sentinel():
    doc = yaml.safe_load(SENTINEL.read_text()) or {}
    close = doc["jobs"]["close"]
    assert "'success'" in close["if"]
    assert "head_branch == 'main'" in close["if"], "a green PR run must not close a main failure"
    assert "gh issue close" in close["steps"][0]["run"]


def test_an_older_green_run_cannot_close_a_newer_failure():
    """Overlapping runs finish out of order; closing on any green run would drop a live failure."""
    run = (yaml.safe_load(SENTINEL.read_text()) or {})["jobs"]["close"]["steps"][0]["run"]
    assert "updatedAt" in run and '"$WHEN" > "$UPDATED"' in run
    assert run.index('"$WHEN" > "$UPDATED"') < run.index("gh issue close")


def test_a_second_delivery_of_one_failure_is_not_reported_twice():
    """The watcher files a failed retry itself; if GitHub also delivers the retry's completion,
    that job waits, re-reads the issue and finds the run+attempt mark. No concurrency group:
    GitHub keeps one pending job per group, so a third failure would cancel a queued second
    one unreported. Nothing is skipped by who triggered the run either."""
    report = (yaml.safe_load(SENTINEL.read_text()) or {})["jobs"]["report"]
    assert "concurrency" not in report
    run = report["steps"][0]["run"]
    assert 'MARK="$URL (attempt $ATTEMPT)"' in run
    assert run.index("sleep 150") < run.index('SEEN=')
    assert "triggering_actor" not in SENTINEL.read_text()


def test_the_retry_is_waited_on_not_left_to_workflow_run():
    """Runs started with GITHUB_TOKEN do not reliably trigger workflow_run, so a retry that
    reports back only through it could fail and file nothing."""
    run = (yaml.safe_load(SENTINEL.read_text()) or {})["jobs"]["report"]["steps"][0]["run"]
    assert "gh run rerun" in run and "gh run watch" in run
    assert "timeout 40m gh run watch" in run, "an unbounded watch can outlive the job"
    assert run.index("gh run rerun") < run.index("gh run watch") < run.index("gh issue create")


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
        "on:\n  push:\n    paths: ['src/**']",          # a path filter does not stop a branch push
        "on:\n  push:\n    branches: ['ma+in']",        # GitHub quantifier: unreadable, so assumed yes
        "on:\n  push:\n    branches: ['ma?in']",        # `?` is zero-or-one there, one-char here
        "on:\n  push:\n    branches: ['**', '!main']",  # ordered negation: unreadable, so assumed yes
        "on:\n  push:\n    branches-ignore: ['dev+']",  # unreadable exclusion, so assumed yes
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
        "on:\n  push:\n    tags: ['v*']",               # tags only: no branch push runs it
        "on:\n  push:\n    tags-ignore: ['v*']",
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


def test_an_unreadable_branch_filter_is_assumed_to_reach_main():
    """GitHub's filter language has `+` as a quantifier and ordered `!` negation; `fnmatch` has
    neither. The gate does not reimplement it -- it answers yes and makes somebody write the
    watch entry or the exemption.

    The two errors are not equal. Over-reporting costs a line of YAML. Under-reporting is a
    workflow failing on main with nothing to say so.
    """
    assert _matches_main(["ma+in"]) is None
    assert _matches_main(["ma?in"]) is None
    assert _matches_main(["**", "!main"]) is None
    assert _matches_main(["develop"]) is False
    assert _matches_main(["**"]) is True


def test_a_tag_only_push_is_not_a_branch_push():
    """GitHub runs no branch push when tags are the only filter, so requiring a watch entry for
    a release workflow would be a false demand.
    """
    assert not _push_can_reach_main({"push": {"tags": ["v*"]}})
    assert not _push_can_reach_main({"push": {"tags-ignore": ["v*"]}})
    # but a tag filter alongside a branch filter still reaches main through the branch
    assert _push_can_reach_main({"push": {"tags": ["v*"], "branches": ["main"]}})


def test_both_extensions_are_scanned_independently_of_this_repo(tmp_path, monkeypatch):
    """The corpus has no `.yaml` workflow today, so a test asserting against it would pass a
    `.yml`-only implementation. This one supplies both.
    """
    import tests.test_sentinel_coverage as mod

    folder = tmp_path / "workflows"
    folder.mkdir()
    (folder / "a.yml").write_text("name: a\non:\n  schedule:\n    - cron: '0 6 * * 1'\n")
    (folder / "b.yaml").write_text("name: b\non:\n  schedule:\n    - cron: '0 7 * * 1'\n")
    monkeypatch.setattr(mod, "WORKFLOWS", folder)
    assert {p.name for p in mod._workflow_files()} == {"a.yml", "b.yaml"}
    assert set(mod.unattended_workflows()) == {"a", "b"}


def test_the_reporter_fires_only_on_a_schedule_or_a_main_push():
    """The reporter's condition is the other half of this file's rule, and nothing else pins it.

    `workflow_dispatch` must stay out: somebody pressed the button, so the failure is already in
    front of them, and the coverage gate does not require a dispatch-only workflow to be watched.
    """
    doc = yaml.safe_load(SENTINEL.read_text()) or {}
    condition = " ".join(doc["jobs"]["report"]["if"].split())
    assert "workflow_run.conclusion == 'failure'" in condition
    assert "workflow_run.event == 'schedule'" in condition
    assert "workflow_run.event == 'push'" in condition
    assert "workflow_run.head_branch == 'main'" in condition
    assert "pull_request" not in condition
    assert "workflow_dispatch" not in condition
