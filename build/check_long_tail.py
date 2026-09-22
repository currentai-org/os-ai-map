"""The long-tail counts must be measured, and measured recently.

`build/sync_long_tail.py` recomputes `sources/snapshots/long_tail.json` from the warehouse and
stamps `measured_on`. This gate is the other half: it fails when that stamp is missing or old.

## Why a staleness gate rather than a value gate

The counts cannot be checked against the warehouse here. This runs on every pull request, and the
warehouse needs credentials and a network; a gate that needs either is a gate that gets skipped.
What CAN be checked for free is whether the numbers were computed recently enough to still be
true, which is the failure this file has actually had: the stored figures sat unchanged while
their sources moved, and the map published them in the present tense with nothing beside them to
say when they were read.

So the contract is narrow. The sync script owns correctness; this owns recency.

## The window

`MAX_AGE_DAYS` is two refresh cycles. Both upstream sources rebuild weekly, so one missed cycle is
a slow week and two is a job that has stopped. The same reasoning sets the parity gate's window,
and for the same reason: a gate's tolerance has to be a multiple of the cadence of the thing it
polices, or it fails for reasons that are nobody's fault.

Usage:
    uv run python -m build.check_long_tail
    uv run python -m build.check_long_tail --today 2026-10-01
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "sources" / "snapshots" / "long_tail.json"

#: Two weekly refresh cycles.
MAX_AGE_DAYS = 14

#: Written by the sync, never by hand. `universe` is deliberately absent: nothing rendered it.
REQUIRED = ("repos", "models", "packages", "total", "matched", "overlap")


def _count(value: object) -> int | None:
    """`value` as a count, or None when it is not one.

    `isinstance(True, int)` is True in Python, so a bool reaches an arithmetic check and passes
    it. A count is also never negative. Both are cheap to reject here and expensive to notice
    downstream, where they surface as a published negative rather than as a bad snapshot.
    """
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def check(snapshot: dict, today: date) -> list[str]:
    """Every reason this snapshot is not publishable, in the order a reader would find them."""
    problems: list[str] = []
    counts = snapshot.get("counts") or {}

    missing = [key for key in REQUIRED if _count(counts.get(key)) is None]
    if missing:
        problems.append(
            f"counts is missing or is not a count: {', '.join(missing)} — run "
            "`uv run python -m build.sync_long_tail --write`"
        )

    total = _count(counts.get("total"))
    parts = [_count(counts.get(k)) for k in ("repos", "models", "packages")]
    if total is not None and all(p is not None for p in parts) and total != sum(parts):
        # Cheap, and it catches the one way a hand edit still slips in: changing a slice and
        # leaving the sum, which is how a typed number used to hide.
        problems.append(f"total is {total:,} but the three slices sum to {sum(parts):,}")

    # The two subtractions `serialize` makes must stay possible. `uncategorized` is
    # total - matched, so a matched above total publishes a negative tail, which is the shape a
    # roster moving under a snapshot produces rather than anything a curator would type.
    matched = _count(counts.get("matched"))
    if total is not None and matched is not None and matched > total:
        problems.append(
            f"matched is {matched:,} against a universe of {total:,}: more artifacts are claimed "
            "by scored products than exist, so the uncategorized remainder would be negative"
        )

    stamp = snapshot.get("measured_on")
    if not stamp:
        problems.append("no measured_on, so the counts cannot be told from a hand-typed set")
        return problems
    try:
        measured = date.fromisoformat(str(stamp))
    except ValueError:
        problems.append(f"measured_on {stamp!r} is not an ISO date")
        return problems

    age = (today - measured).days
    if age < 0:
        # A future stamp would otherwise buy itself the window twice over: the age test only
        # rejects `age > MAX_AGE_DAYS`, so a date a month out passes for a month and a half.
        # Reachable from a hand edit and from `sync_long_tail --today`, which takes any date.
        problems.append(f"measured_on {stamp} is in the future, so the window cannot be read")
        return problems
    if age > MAX_AGE_DAYS:
        problems.append(
            f"counts were measured {age} days ago ({stamp}), past the {MAX_AGE_DAYS}-day window. "
            "The weekly sync has not run, and the map is publishing numbers it cannot stand behind."
        )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args(argv)

    problems = check(json.loads(SNAPSHOT.read_text()), date.fromisoformat(args.today))
    for problem in problems:
        print(f"  x {problem}")
    if problems:
        print(f"\nlong-tail counts  {len(problems)} problem(s)")
        return 1
    print("[OK] the long-tail counts are measured and inside the window")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
