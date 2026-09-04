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


def test_a_dispatch_reaches_the_neon_steps_on_any_ref():
    """That is what the dispatch is for: the Neon schema is swapped atomically and
    re-loadable, so a branch run costs nothing beyond a reload."""
    for name in ("Publish to Neon", "Report what Neon is serving"):
        assert "if" not in step_named(name), f"{name} must not be guarded by event or ref"


def test_no_input_decides_whether_oso_is_published():
    """A flag that defaults to the safe value is still a flag someone forgets."""
    doc = yaml.safe_load(WORKFLOW.read_text())
    triggers = doc.get("on") or doc.get(True)
    assert not (triggers.get("workflow_dispatch") or {}).get("inputs")
    assert "inputs." not in WORKFLOW.read_text()


def test_the_closure_is_actually_walking_transitively():
    """Guard on the guard: if the walk stopped at the seeds, the test above would pass
    vacuously the moment someone trimmed the trigger list back to three entries."""
    closure = import_closure()
    assert "build.serialize" in closure, "serialize is reached via serialize_scores"
    assert "build.freshness_payload" in closure, "freshness_payload is reached via serialize_scores"
    assert len(closure) > len(SEEDS) + 2, f"closure looks too small: {sorted(closure)}"
