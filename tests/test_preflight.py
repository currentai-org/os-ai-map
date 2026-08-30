"""The preflight step list must stay the CI step list.

The failure this guards against is the one that produced the module: a local gate loop that
looked thorough and was missing the one check that mattered. If preflight can silently cover
fewer steps than CI, it recreates that gap while looking like a fix for it.
"""
import re
from pathlib import Path

from build.preflight import WORKFLOW, steps

ROOT = Path(__file__).resolve().parents[1]


def test_every_ci_step_is_in_the_plan():
    """Parsed against the workflow itself, so adding a CI gate adds it here for free."""
    raw = re.findall(r"uv run (python -m build\.[a-z_]+[^\n]*|pytest[^\n]*)",
                     WORKFLOW.read_text())
    expected = [c.strip().rstrip("\"'") for c in raw if "${{" not in c]
    assert steps() == list(dict.fromkeys(expected))


def test_the_plan_is_not_empty_and_names_the_gate_that_caused_this():
    """`check_components` is the gate the promotion batch failed CI on. A parse that silently
    matched nothing would return an empty list and report success, so both are asserted."""
    plan = steps()
    assert len(plan) >= 10
    assert "python -m build.check_components" in plan
    assert "python -m build.validate" in plan
    assert "pytest -q" in plan


def test_workflow_inputs_are_excluded():
    """Steps carrying a `${{ inputs.x }}` default cannot be reproduced locally and are dropped
    rather than run with a literal `${{ ... }}` argument."""
    assert not any("${{" in command for command in steps())


def test_parses_a_minimal_workflow(tmp_path):
    workflow = tmp_path / "validate.yml"
    workflow.write_text(
        "jobs:\n  validate:\n    steps:\n"
        "      - run: uv run python -m build.validate\n"
        "      - run: uv run pytest -q\n"
        "      - run: uv run python -m build.check_components\n"
        "      - run: uv run python -m build.check_freshness --max-age-days \"${{ inputs.n }}\"\n"
    )
    assert steps(workflow) == [
        "python -m build.validate", "pytest -q", "python -m build.check_components",
    ]
