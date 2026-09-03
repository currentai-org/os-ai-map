"""Run locally what CI's `validate` workflow runs, and account for every step it does not.

Why this exists. The promotion of five products passed a local loop of `validate` +
`check_recipe` + `check_rubric` + `check_verification` + `pytest`, then failed CI on
`build.check_components` with ten errors: the `raw:` strings had been hand-written and did not
recompose from their structured `components` mappings. `build.validate` does not check that, so
no amount of running it would have caught the problem. That was survivable at five products. It
is not survivable at four hundred.

WHY THIS IS NOT A REGEX. The first version of this module scraped the workflow for commands
matching `uv run python -m build.*` or `uv run pytest`, and its test recomputed the expected list
with the same regex. Any CI command the pattern did not recognize - the notebook AST parse run
through `python -c`, `marimo check`, the `git checkout` that restores generated files, the whole
`generated-files-guard` job - was invisible to the implementation AND to the test, which stayed
green while covering less than it claimed. A test that confirms its own blind spot is worse than
no test, because it is believed.

So the unit here is the workflow's own STEP, read structurally from the YAML, and the invariant
is total:

    every `run:` step in validate.yml is either executed locally or listed in PLAN with a reason

`tests/test_preflight.py` asserts that set equality against the parsed workflow, not against a
second copy of this file's idea of a step. A step added to CI fails the test until somebody
classifies it, which is the only version of "cannot drift" that is true.

Generated files. `serialize` and `render` write `build/notebook_data.json` and
`notebooks/ai-stack-map.py`, which are bot-owned. This module hashes them before the run, reports
any change as a finding, and restores them afterwards, so a regeneration diff cannot hide and the
tree is not left dirty either.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"

GENERATED = ("build/notebook_data.json", "notebooks/ai-stack-map.py")

RUN, SKIP, CI_ONLY = "LOCAL_RUN", "LOCAL_SKIP", "CI_ONLY"

#: Every `run:` step in validate.yml, by its workflow `name`. The value is the mode and, for
#: anything not run locally, the reason. Adding a step to CI without adding it here fails
#: tests/test_preflight.py.
PLAN: dict[str, tuple[str, str]] = {
    "Install dependencies": (SKIP, "the local environment is already synced; `uv run` resolves it per call"),
    "Validate sources (schema + cross-file invariants)": (RUN, ""),
    "Run tests": (RUN, ""),
    "Verification gates (invariant, digests, producible-pairs)": (RUN, ""),
    "Capability gate (recorded comparisons hold)": (RUN, ""),
    "Recipe gate (structure, deferral completeness, discarded evidence)": (RUN, ""),
    "Components gate (a structured mapping matches its raw string)": (RUN, ""),
    "Rubric gate (recorded scores reproduce)": (RUN, ""),
    "Adoption gate (every band exists on its instrument's scale)": (RUN, ""),
    "Instrument gate (every signal_type claim has what it needs to be falsifiable)": (RUN, ""),
    "Routing table structure": (RUN, ""),
    "Freshness report (informational, does not gate)": (RUN, ""),
    "Serialize dry-run": (RUN, ""),
    "Retirement gate (a removed slug carries a redirect alias)": (RUN, ""),
    "Gate the serialized payload": (RUN, ""),
    "Render notebook and check it parses": (RUN, ""),
    "Fail if PR hand-edits bot-owned generated files": (
        CI_ONLY,
        "compares the PR against its merge base, which needs the PR context. Locally the same "
        "class of problem is caught by this module's own generated-file check below.",
    ),
    "Corpus goldens status (informational on PRs, must be current on main)": (
        CI_ONLY,
        "branches on `github.event_name`, which is a GitHub Actions context with no meaning "
        "run locally as plain bash. The local equivalent is `uv run python -m build.goldens "
        "--check` directly.",
    ),
}


def ci_steps(workflow: Path = WORKFLOW) -> list[tuple[str, str, str]]:
    """(job, step name, run block) for every `run:` step in the workflow, in file order."""
    document = yaml.safe_load(workflow.read_text()) or {}
    found = []
    for job_name, job in (document.get("jobs") or {}).items():
        for step in (job.get("steps") or []):
            if "run" in step:
                found.append((job_name, step.get("name") or "", step["run"]))
    return found


def unaccounted(workflow: Path = WORKFLOW) -> list[str]:
    """Step names CI runs that PLAN does not classify. The invariant this module exists for."""
    return [name for _, name, _ in ci_steps(workflow) if name not in PLAN]


def _digests() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for rel in GENERATED:
        path = ROOT / rel
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-tests", action="store_true",
                        help="skip the pytest step, which dominates the wall clock")
    parser.add_argument("--list", action="store_true", help="print the plan and exit")
    args = parser.parse_args()

    missing = unaccounted()
    if missing:
        print("validate.yml has steps this module does not classify; add them to PLAN:")
        for name in missing:
            print(f"  ! {name!r}")
        return 1

    plan = [(job, name, run) for job, name, run in ci_steps()
            if PLAN[name][0] == RUN and not (args.skip_tests and "pytest" in run)]
    if args.list:
        for job, name, _ in ci_steps():
            mode, reason = PLAN[name]
            print(f"  {mode:10} [{job}] {name}" + (f"\n             -> {reason}" if reason else ""))
        return 0

    before = _digests()
    failures: list[str] = []
    for _, name, run in plan:
        started = time.monotonic()
        result = subprocess.run(["bash", "-e", "-c", run], cwd=ROOT, capture_output=True, text=True)
        status = "ok  " if result.returncode == 0 else "FAIL"
        print(f"  {status} {name[:58]:58} {time.monotonic() - started:6.1f}s")
        if result.returncode != 0:
            failures.append(name)
            for line in (result.stdout + result.stderr).strip().splitlines()[-12:]:
                print(f"       | {line}")

    regenerated = [rel for rel, digest in _digests().items() if digest != before[rel]]
    if regenerated:
        print("\ngenerated files changed under this run, and were restored:")
        for rel in regenerated:
            print(f"  ~ {rel}")
        print("  commit them from a bot run, never by hand - CI's generated-files-guard rejects that.")
        subprocess.run(["git", "checkout", "--", *regenerated], cwd=ROOT, check=False)

    skipped = [(n, r) for n, (m, r) in PLAN.items() if m != RUN]
    print()
    if failures:
        print(f"{len(failures)} of {len(plan)} step(s) failed: {', '.join(failures)}")
        return 1
    print(f"all {len(plan)} locally-runnable CI steps pass; {len(skipped)} accounted for and not run.")
    print("check_parity and check_artifacts --live need the warehouse and run in their own workflows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
