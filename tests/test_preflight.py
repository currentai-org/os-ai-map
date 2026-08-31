"""Preflight must account for every CI step, and the accounting must not be self-confirming.

The first version of this file recomputed its expectation with the same regex production used,
so a CI command the pattern did not recognize was omitted from both and the test stayed green
while covering less than it claimed. These tests parse the workflow structurally instead, and
compare against the hand-written PLAN, which is the only thing that can actually disagree.
"""
from pathlib import Path

import pytest
import yaml

from build.preflight import CI_ONLY, GENERATED, PLAN, RUN, SKIP, WORKFLOW, ci_steps, unaccounted

ROOT = Path(__file__).resolve().parents[1]


def test_every_ci_run_step_is_accounted_for():
    """The invariant. A step added to validate.yml fails here until somebody classifies it."""
    assert unaccounted() == [], (
        "these validate.yml steps are neither run locally nor listed in preflight.PLAN with a "
        "reason; classify them"
    )


def test_plan_lists_nothing_ci_does_not_run():
    """The other direction: a PLAN entry for a step that no longer exists is stale."""
    names = {name for _, name, _ in ci_steps()}
    assert set(PLAN) - names == set()


def test_the_steps_are_read_from_the_workflow_not_restated():
    """Parsed structurally, so multi-line shell and non-`uv run` commands are seen too - the
    class the regex version silently dropped."""
    document = yaml.safe_load(WORKFLOW.read_text())
    expected = sum(1 for job in document["jobs"].values()
                   for step in job.get("steps", []) if "run" in step)
    assert len(ci_steps()) == expected
    assert expected >= 15


def test_a_non_uv_command_is_still_a_step(tmp_path):
    """`marimo check` and a `python -c` AST parse are steps the old regex could not see. They
    reach ci_steps() now, which is what makes the accounting total rather than pattern-shaped."""
    workflow = tmp_path / "validate.yml"
    workflow.write_text(
        "jobs:\n  validate:\n    steps:\n"
        "      - name: Gate\n        run: uv run python -m build.validate\n"
        "      - name: Notebook\n        run: |\n"
        "          uv run marimo check notebooks/ai-stack-map.py\n"
        "          uv run python -c 'import ast; ast.parse(open(\"x.py\").read())'\n"
        "      - name: Restore\n        run: git checkout -- build/notebook_data.json\n"
    )
    steps = ci_steps(workflow)
    assert [name for _, name, _ in steps] == ["Gate", "Notebook", "Restore"]
    assert "marimo check" in steps[1][2]
    # None of these names is in PLAN, so all three are unaccounted - including the two the
    # regex version could not even see.
    assert unaccounted(workflow) == ["Gate", "Notebook", "Restore"]


def test_every_plan_mode_is_known_and_reasons_accompany_the_skips():
    for name, (mode, reason) in PLAN.items():
        assert mode in {RUN, SKIP, CI_ONLY}, name
        if mode != RUN:
            assert len(reason) > 20, f"{name} is not run locally and needs a reason"


def test_the_generated_files_are_the_bot_owned_pair():
    """Named so the restore step cannot silently stop covering one of them."""
    assert set(GENERATED) == {"build/notebook_data.json", "notebooks/ai-stack-map.py"}
    for rel in GENERATED:
        assert (ROOT / rel).exists()


@pytest.mark.parametrize("gate", [
    "Components gate (a structured mapping matches its raw string)",
    "Validate sources (schema + cross-file invariants)",
    "Run tests",
])
def test_the_gates_that_caught_real_failures_run_locally(gate):
    """check_components is the gate the promotion batch failed CI on; it must never become a
    CI_ONLY entry, which would reintroduce exactly the blind spot this module was written for."""
    assert PLAN[gate][0] == RUN
