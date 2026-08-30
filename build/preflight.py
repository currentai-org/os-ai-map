"""Run locally what CI's `validate` workflow runs, in its order, and fail the same way.

Why this exists. The promotion of five products into `agent_tools_protocols` passed a local
loop of `validate` + `check_recipe` + `check_rubric` + `check_verification` + `pytest`, and then
failed CI on `build.check_components` with ten errors: the `raw:` strings had been hand-written
and did not recompose from the structured `components` mappings. `build.validate` does not check
that, so no amount of running it would have caught the problem. The local loop was not
representative of CI, and the only reason that was survivable is that the batch was five
products. It will not be survivable at four hundred.

The step list is READ FROM `.github/workflows/validate.yml` at run time rather than restated
here, so this cannot drift from CI by being forgotten. `tests/test_preflight.py` asserts the
parse finds every step, which is what keeps the reading honest if the workflow's shape changes.

`build.render` and `build.serialize` WRITE bot-owned generated files - `build/notebook_data.json`
and `notebooks/ai-stack-map.py`. CI regenerates them in a throwaway checkout; locally they dirty
your tree, and committing them fails the `generated-files-guard` job. Restore them after a run:
`git checkout -- build/notebook_data.json notebooks/ai-stack-map.py`. They are left rather than
auto-reverted because a run that silently reverted files would hide a real regeneration diff.

Not a substitute for CI. `check_parity` and `check_artifacts --live` need credentials and the
warehouse and run in their own workflows; a green preflight means the offline gates hold, not
that the branch is mergeable.
"""
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"

# Captured to end of line, NOT to the first quote. Stopping at the quote silently truncated
# `--max-age-days "${{ inputs.n }}"` to `--max-age-days`, which passed the `${{` filter below
# and would have run the gate with a missing argument.
_STEP = re.compile(r"uv run (python -m build\.[a-z_]+[^\n]*|pytest[^\n]*)")


def steps(workflow: Path = WORKFLOW) -> list[str]:
    """The `uv run` commands CI executes, in workflow order, de-duplicated."""
    found, seen = [], set()
    for match in _STEP.finditer(workflow.read_text()):
        command = match.group(1).strip().rstrip("\"'")
        if "${{" in command:  # a workflow-input default; not reproducible locally
            continue
        if command not in seen:
            seen.add(command)
            found.append(command)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-tests", action="store_true",
                        help="skip the pytest step, which dominates the wall clock")
    parser.add_argument("--list", action="store_true", help="print the steps and exit")
    args = parser.parse_args()

    plan = steps()
    if args.skip_tests:
        plan = [c for c in plan if not c.startswith("pytest")]
    if args.list:
        print("\n".join(plan))
        return 0

    failures: list[tuple[str, int]] = []
    for command in plan:
        started = time.monotonic()
        result = subprocess.run(["uv", "run", *shlex.split(command)], cwd=ROOT,
                                capture_output=True, text=True)
        elapsed = time.monotonic() - started
        status = "ok  " if result.returncode == 0 else "FAIL"
        print(f"  {status} {command:52} {elapsed:6.1f}s")
        if result.returncode != 0:
            failures.append((command, result.returncode))
            tail = (result.stdout + result.stderr).strip().splitlines()[-12:]
            for line in tail:
                print(f"       | {line}")

    print()
    if failures:
        print(f"{len(failures)} of {len(plan)} step(s) failed: {', '.join(c for c, _ in failures)}")
        return 1
    print(f"all {len(plan)} offline CI steps pass. check_parity and check_artifacts --live "
          f"need the warehouse and run separately.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
