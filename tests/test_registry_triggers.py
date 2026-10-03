"""registry.yml must trigger on every module that can change what it publishes.

The workflow used to list the three serializers and nothing they import. So a change to
`build/serialize.py` — which derives `overall_score`, `maturity` and `score_tier` — or to
`build/freshness_payload.py`, which supplies the freshness columns, could alter
`currentai.registry.product_scores` with the publishing workflow never running. The table
would then disagree with the repo until something unrelated touched `sources/`.

This recomputes the import closure from the serializers and fails if the trigger lists have
fallen behind it, so the next import declares itself instead of being remembered.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/registry.yml"
REGENERATE = ROOT / ".github/workflows/regenerate.yml"
# What the publish job actually runs. Anything these reach, transitively, is an input.
SEEDS = ("build.serialize_registry", "build.serialize_rubric", "build.serialize_scores")


def _first_party_imports(module: str) -> set[str]:
    path = ROOT / (module.replace(".", "/") + ".py")
    if not path.exists():
        return set()
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("build"):
            found.add(node.module)
        elif isinstance(node, ast.Import):
            found.update(a.name for a in node.names if a.name.startswith("build"))
    return found


def import_closure() -> set[str]:
    seen, queue = set(SEEDS), list(SEEDS)
    while queue:
        for dep in _first_party_imports(queue.pop()):
            if dep not in seen:
                seen.add(dep)
                queue.append(dep)
    return seen


def trigger_paths(event: str) -> set[str]:
    # PyYAML reads the `on:` key as the boolean True, this being YAML.
    doc = yaml.safe_load(WORKFLOW.read_text())
    triggers = doc.get("on") or doc.get(True)
    return set(triggers[event]["paths"])


@pytest.mark.parametrize("event", ["push", "pull_request"])
def test_every_module_the_serializers_reach_triggers_the_workflow(event: str):
    paths = trigger_paths(event)
    missing = sorted(
        module.replace(".", "/") + ".py"
        for module in import_closure()
        if module.replace(".", "/") + ".py" not in paths
    )
    assert not missing, (
        f"registry.yml's {event} trigger does not include {missing}. A change to any of them "
        f"can alter what the publish emits without this workflow running."
    )


def publish_steps() -> list[dict]:
    doc = yaml.safe_load(WORKFLOW.read_text())
    return doc["jobs"]["publish"]["steps"]


def step_named(name: str) -> dict:
    for step in publish_steps():
        if step.get("name") == name:
            return step
    raise AssertionError(f"no step named {name!r} in the publish job")


def test_the_oso_publish_runs_only_on_a_push_to_main():
    """The static models are org-wide. The guard used to be a `neon_only` dispatch input
    defaulting to false, so forgetting `-f neon_only=true` published a branch's declarations
    over them — an invariant the comments asserted and nothing enforced. The event and the
    ref cannot be forgotten."""
    guard = step_named("Publish to OSO")["if"]
    assert "push" in guard
    assert "refs/heads/main" in guard
    assert "github.event_name" in guard and "github.ref" in guard


def test_the_neon_steps_run_only_from_main():
    """aipotluck.org reads the Neon schema live (aipotluck.org#1350), so a load from a branch
    dispatch would be served to visitors within a minute. The read-back is guarded too: its
    secret is the same owner credential, and a branch's code must never be handed it. A push
    and a dispatch from main both run them; nothing else does."""
    for name in ("Publish to Neon", "Report what Neon is serving"):
        guard = step_named(name)["if"]
        assert "refs/heads/main" in guard and "github.ref" in guard, name
        assert "event_name" not in guard, f"{name}: a dispatch from main must still run it"


def test_no_other_step_is_handed_the_neon_secret():
    """The guard means nothing if an unguarded step carries the credential."""
    doc = yaml.safe_load(WORKFLOW.read_text())
    for job in doc["jobs"].values():
        for step in job.get("steps", []):
            if "NEON_DATABASE_URL" in str(step.get("env", {})):
                assert "refs/heads/main" in step.get("if", ""), step.get("name")


def test_no_input_decides_whether_oso_is_published():
    """A flag that defaults to the safe value is still a flag someone forgets."""
    doc = yaml.safe_load(WORKFLOW.read_text())
    triggers = doc.get("on") or doc.get(True)
    assert not (triggers.get("workflow_dispatch") or {}).get("inputs")
    assert "inputs." not in WORKFLOW.read_text()


def test_a_regenerated_payload_reloads_neon():
    """Neon is rendered from the committed payload, and the bot's regeneration push cannot
    start this workflow, because a push made with GITHUB_TOKEN starts no run. So regenerate.yml
    dispatches it from main after pushing a changed payload. Without that, the site serves the
    payload from before the regeneration until the next merge, which is how #811's merge put
    schema 6 live with countries on 10 orgs instead of 489."""
    doc = yaml.safe_load(REGENERATE.read_text())
    assert (doc.get("permissions") or {}).get("actions") == "write"
    steps = doc["jobs"]["regenerate"]["steps"]
    commit = next(i for i, s in enumerate(steps) if s.get("id") == "commit")
    assert "payload=changed" in steps[commit]["run"]
    assert "GITHUB_OUTPUT" in steps[commit]["run"]
    dispatch = next(
        i for i, s in enumerate(steps) if "gh workflow run registry.yml" in s.get("run", "")
    )
    assert dispatch > commit, "the dispatch must follow the push it reloads"
    assert "--ref main" in steps[dispatch]["run"], "only a dispatch from main reloads Neon"
    assert steps[dispatch].get("if") == "steps.commit.outputs.payload == 'changed'"
    assert "github.token" in str(steps[dispatch].get("env", {}).get("GH_TOKEN", ""))
    # The output is set only once the push has landed, inside its success branch.
    run = steps[commit]["run"]
    push_ok = run.index("if git push origin HEAD:main; then")
    assert push_ok < run.index("payload=changed") < run.index("exit 0", push_ok)
    triggers = yaml.safe_load(WORKFLOW.read_text())
    assert "workflow_dispatch" in (triggers.get("on") or triggers.get(True))


def test_a_pull_request_run_cannot_take_a_publish_run_s_queue_slot():
    """GitHub keeps one pending run per concurrency group and cancels the older pending one
    when another queues. A pull request run publishes nothing, so in the publish group it
    could cancel a merge's queued publish, or the Neon reload regenerate.yml dispatches, and
    then skip publishing itself. Pull requests get a group per PR; push and dispatch share
    registry-publish."""
    group = yaml.safe_load(WORKFLOW.read_text())["concurrency"]["group"]
    assert "github.event_name == 'pull_request'" in group
    assert "github.ref" in group, "one group per PR, not one for every PR"
    assert group.rstrip("} ").endswith("|| 'registry-publish'"), "push and dispatch must share it"

def test_the_closure_is_actually_walking_transitively():
    """Guard on the guard: if the walk stopped at the seeds, the test above would pass
    vacuously the moment someone trimmed the trigger list back to three entries."""
    closure = import_closure()
    assert "build.serialize" in closure, "serialize is reached via serialize_scores"
    assert "build.freshness_payload" in closure, "freshness_payload is reached via serialize_scores"
    assert len(closure) > len(SEEDS) + 2, f"closure looks too small: {sorted(closure)}"
