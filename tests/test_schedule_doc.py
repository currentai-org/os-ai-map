"""The schedule table in deploy-models.md must match the workflows it describes.

Written because the table did not. On 2026-08-19 a change to that section recorded the
parity gate at 07:00 UTC when `parity.yml` says `0 6 * * 1` — 07:00 is `artifacts.yml`,
misread off a loop that printed workflow names and crons out of step. The PR carrying it
also claimed the repo had been searched for surviving copies of the old times, and two
survived.

Prose about a cron is a copy of the cron, and a copy drifts. This makes the workflow file
the authority and the doc answerable to it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs/operations/deploy-models.md"
# The gates whose times the doc's table quotes. Dataset crons live on the platform and
# cannot be read from the repo, so they are out of scope here by construction.
GATES = ("parity", "artifacts", "freshness", "channel-authority", "reverify")

_DAYS = {"1": "Monday", "2": "Tuesday", "3": "Wednesday", "4": "Thursday",
         "5": "Friday", "6": "Saturday", "0": "Sunday"}


def workflow_cron(name: str) -> tuple[str, str]:
    """(day, HH:MM) from the workflow's first `cron:` line."""
    text = (ROOT / ".github/workflows" / f"{name}.yml").read_text()
    match = re.search(r'cron:\s*"([^"]+)"', text)
    assert match, f"{name}.yml declares no cron"
    minute, hour, _dom, _mon, dow = match.group(1).split()
    return _DAYS[dow], f"{int(hour):02d}:{int(minute):02d}"


def doc_row(name: str) -> str:
    """The doc table row mentioning this workflow file."""
    rows = [line for line in DOC.read_text().splitlines()
            if line.startswith("|") and f"workflows/{name}.yml" in line]
    assert len(rows) == 1, f"expected exactly one table row for {name}.yml, found {len(rows)}"
    return rows[0]


@pytest.mark.parametrize("name", GATES)
def test_the_doc_quotes_the_cron_the_workflow_actually_declares(name: str):
    day, hhmm = workflow_cron(name)
    row = doc_row(name)
    assert hhmm in row, f"{name}.yml runs at {hhmm} {day}; the doc row says: {row.strip()}"


def test_the_chain_lands_before_parity_grades_it():
    """Parity compares the repo against a warehouse the chain has just recomputed.

    The dataset crons are 03:00 and 04:00 UTC and live on the platform, so this asserts the
    documented order rather than reading them: if parity ever moves ahead of 04:00 it would
    grade a warehouse that has not recomputed and fail for a reason that is not a drift.
    """
    _, parity = workflow_cron("parity")
    assert parity > "04:00", (
        f"parity runs at {parity}, at or before the scores dataset's documented 04:00 sweep"
    )


def test_no_stale_claim_that_the_chain_never_runs_on_a_schedule():
    """A scheduled run was observed on 2026-08-19, so this claim is false wherever it survives."""
    for path in (ROOT / "AGENTS.md", DOC, ROOT / "README.md"):
        if not path.exists():
            continue
        text = path.read_text()
        assert "zero scheduled runs have ever fired" not in text, path
        assert "chain does not run on a schedule" not in text, path
