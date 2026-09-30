"""The Phase 4 adoption gate (#410), report-first: what a release would be blocked on, and why.

`data-architecture.md` §18 requires that a fresh authoritative adoption disagreement cannot enter
a release silently. The warehouse cannot enforce that: `evaluation.adoption_reconciliation` has no
row-to-run binding, so every measured row there is `source_unavailable`, and for that table this
is the settled state. The ruling on #410 (route 2) moved the gate repo-side, next to the binding
that already exists, and this is that gate.

## When a measurement counts as current

§4.3 states the conditions, and this module implements them as written. An observation counts
as current only when all three hold. Otherwise it is `source_unavailable`:

  1. the read is bound by `build/read_binding.py` to a materialization of
     `product_adoption_current` whose run was `SCHEDULED` and succeeded, within
     `MAX_BINDING_AGE_DAYS`. This reuses `build.adoption_freshness.binding_problems`, the same
     test that decides whether a read may date an axis, so the gate and the dating cannot
     disagree about what a bound read is;
  2. the latest `SCHEDULED` run of the observation's source dataset that finished before that
     materialization's run started reports `SUCCESS`, within the same age bound. Only the latest
     run counts. An older success behind a newer failure does not qualify, and a failed latest
     run is reported as failed, not as current;
  3. the `source_runs` snapshot was captured after the bound read completed, so the run evidence
     is no older than the read it vouches for.

The evidence is per dataset, not per row. It separates a failed or stale collector from a real
absence of measurement, which is the job `source_unavailable` has. It cannot see an artifact
dropped by a partial run that still reported `SUCCESS`, and §4.3 accepts that blind spot.

## What it would block

With the evidence in place, a measured row on the same instrument gets the §8.2 status: `agree`
when the bands match, `override_required` when they differ. No structured override exists yet
(`sources/reconciliation_overrides.yaml` is added only once the baseline shows it is needed), so
nothing is `explicit_override`. The §4.4 blocking rules then apply:

  * `override_required` and `source_unavailable` would block;
  * `route_mismatch` blocks only when inconsistent declarations cause it, and nothing here can
    tell that cause from the others, so it is reported as review and does not block;
  * everything else does not block, and each row carries the explanation of why.

`stale_measurement` is not assigned. §4.4 names no threshold for it and the gate would have to
invent one. A stale observation from a collector that failed is already caught by condition 2.

## Report first

§4.4 and §8.3 require reporting before blocking. This prints the census and every row it would
block, and exits 0 whatever it finds. Blocking mode comes in a later change, once a few weekly
runs have been read. Unreadable input is the exception: a report over input it could not read
would be a report that checked nothing, so that exits 2.

It reads two files and never the warehouse. Both come from the weekly reconciliation workflow:

  * the `--json-out` document of `build.adoption_freshness --live`, which holds the binding and
    the reconciliation rows from the one read that run made;
  * `source_runs.csv` from `build.snapshot_source_runs --rows-only`, captured after that read.

Usage:
    uv run python -m build.check_reconciliation --read read.json --source-runs build/observations/source_runs.csv
    uv run python -m build.check_reconciliation --read read.json --source-runs runs.csv --json
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from build.adoption_freshness import (
    DATING_STATUS,
    DATING_TRIGGER,
    MAX_BINDING_AGE_DAYS,
    binding_problems,
)
from build.vocabulary import parse_timestamp

ROOT = Path(__file__).resolve().parents[1]

CURRENT = "current"
FAILED = "failed"
STALE = "stale"
MISSING = "missing"

#: §4.4: the statuses that block a release, and the one that goes to review instead.
BLOCKING = frozenset({"override_required", "source_unavailable"})
REVIEW = frozenset({"route_mismatch"})

#: Reconciliation statuses that carry no measurement to vouch for, so they pass through as-is.
_UNMEASURED = frozenset({"abstained", "unmeasured"})
#: Cross-instrument statuses: a current measurement keeps them, since no delta exists to judge.
_CROSS_INSTRUMENT = frozenset({"route_mismatch", "expected_difference"})


def _utcnow() -> datetime.datetime:
    """Now, in UTC. A named seam so a test pins the clock, as in `build.adoption_freshness`."""
    return datetime.datetime.now(datetime.timezone.utc)


def _instant(value: object) -> datetime.datetime | None:
    """A UTC instant, or `None` for an empty or unparseable value. A naive stamp is read as UTC."""
    if value in (None, ""):
        return None
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=datetime.timezone.utc)


@dataclass(frozen=True)
class Evidence:
    """What one source dataset's run history says about the read, as of the snapshot."""

    dataset: str
    verdict: str
    reason: str
    run_id: str | None = None
    finished_at: str | None = None


def dataset_evidence(
    runs: Iterable[Mapping],
    dataset: str,
    bound_run_started_at: datetime.datetime,
    now: datetime.datetime,
) -> Evidence:
    """Condition 2 for one dataset: the authoritative fetch, and whether it counts.

    `runs` are `source_runs` rows, one per (run, materialization), so a run appears once per
    materialization and is collapsed back to one run first. The authoritative run is the latest
    SCHEDULED run that FINISHED before the bound materialization's run started. A run still
    going has no finish time and cannot have fed that materialization. A MANUAL run is never
    authoritative, whatever it reports.
    """
    by_run: dict[str, Mapping] = {}
    for row in runs:
        if row.get("source_dataset_name") == dataset and row.get("source_run_id"):
            by_run.setdefault(str(row["source_run_id"]), row)
    before = []
    for run_id, row in by_run.items():
        if row.get("trigger_type") != DATING_TRIGGER:
            continue
        finished = _instant(row.get("finished_at"))
        if finished is not None and finished < bound_run_started_at:
            before.append((finished, run_id, row))
    if not before:
        return Evidence(
            dataset, MISSING,
            f"no {DATING_TRIGGER} run of {dataset} finished before the bound materialization's "
            f"run started, so nothing shows its collector fed this read",
        )
    finished, run_id, row = max(before, key=lambda item: (item[0], item[1]))
    stamp = finished.isoformat(timespec="seconds")
    status = row.get("execution_status")
    if status != DATING_STATUS:
        return Evidence(
            dataset, FAILED,
            f"the latest {DATING_TRIGGER} run of {dataset} before the read ({run_id}, finished "
            f"{stamp}) reports {status}; an older success behind it does not count",
            run_id, stamp,
        )
    age = (now - finished).days
    if age > MAX_BINDING_AGE_DAYS:
        return Evidence(
            dataset, STALE,
            f"the latest {DATING_TRIGGER} run of {dataset} before the read ({run_id}) finished "
            f"{age} days ago, past the {MAX_BINDING_AGE_DAYS}-day bound",
            run_id, stamp,
        )
    return Evidence(
        dataset, CURRENT,
        f"{dataset}: {DATING_TRIGGER}/{DATING_STATUS} run {run_id} finished {stamp}",
        run_id, stamp,
    )


def read_problems(
    binding: Mapping | None, runs: Sequence[Mapping], now: datetime.datetime
) -> list[str]:
    """Conditions 1 and 3: why no observation from this read can count as current, or `[]`."""
    problems = list(binding_problems(binding, now))
    if problems:
        return problems
    assert binding is not None  # binding_problems refuses a missing binding
    if _instant(binding.get("run_started_at")) is None:
        return ["the bound run names no start time, so the fetch that fed it cannot be identified"]
    read_at = _instant(binding.get("read_at"))
    if read_at is None:
        return ["the binding does not say when the read completed, so the run evidence cannot "
                "be shown to postdate it"]
    if not runs:
        return ["the source_runs snapshot holds no runs, so no collector can be shown to have run"]
    captured = [_instant(row.get("captured_at")) for row in runs]
    if any(c is None for c in captured):
        return ["a source_runs row carries no readable captured_at, so the snapshot cannot be "
                "shown to postdate the read"]
    earliest = min(c for c in captured if c is not None)
    if earliest <= read_at:
        return [
            f"source_runs was captured {earliest.isoformat(timespec='seconds')}, not after the "
            f"read completed {read_at.isoformat(timespec='seconds')}; run evidence older than the "
            f"read cannot vouch for it"
        ]
    return []


@dataclass
class Judgement:
    """One reconciliation row as the gate classifies it."""

    product_slug: str
    route_id: str
    dataset: str | None
    reconciliation_status: str
    status: str
    explanation: str
    route_authority: str | None = None
    recorded_level: object = None
    measured_level: object = None

    @property
    def disposition(self) -> str:
        if self.status in BLOCKING:
            return "block"
        if self.status in REVIEW:
            return "review"
        return "pass"


def judge(
    row: Mapping,
    dataset: str | None,
    problems: Sequence[str],
    evidence: Mapping[str, Evidence],
) -> Judgement:
    """The repo-side status of one reconciliation row, and why."""
    base = row["status"]
    out = Judgement(
        product_slug=row["product_slug"],
        route_id=row["route_id"],
        dataset=dataset,
        reconciliation_status=base,
        status=base,
        explanation=row.get("explanation") or "",
        route_authority=row.get("route_authority"),
        recorded_level=row.get("recorded_level"),
        measured_level=row.get("measured_level"),
    )
    if base in _UNMEASURED:
        return out
    if problems:
        out.status, out.explanation = "source_unavailable", problems[0]
        return out
    if dataset is None:
        out.status = "source_unavailable"
        out.explanation = (f"route {row['route_id']} names no bridged collector dataset, so no "
                           f"run can vouch for its measurement")
        return out
    found = evidence.get(dataset)
    if found is None or found.verdict != CURRENT:
        out.status = "source_unavailable"
        out.explanation = found.reason if found else f"no run evidence for {dataset}"
        return out
    if base in _CROSS_INSTRUMENT:
        out.explanation = f"current ({found.reason}); {out.explanation}"
        return out
    delta = row.get("delta")
    if delta == 0:
        out.status = "agree"
        out.explanation = f"current ({found.reason}); the route measured the recorded band"
    elif delta is not None:
        out.status = "override_required"
        out.explanation = (
            f"current ({found.reason}); measured level {row.get('measured_level')} against "
            f"recorded {row.get('recorded_level')} on the same instrument, with no override"
        )
    else:
        # Unreachable from build.adoption_reconciliation today: a same-instrument row with both
        # levels always carries a delta. Kept visible rather than passed.
        out.status = "route_mismatch"
        out.explanation = f"current ({found.reason}), but the row carries no delta to judge"
    return out


def route_datasets(root: Path | None = None) -> dict[str, str | None]:
    """Each compiled route id -> the collector dataset its source is fetched into.

    Resolved through `build.snapshot_source_runs.source_dataset`, the resolution the snapshot's
    own coverage uses, so the gate asks about exactly the datasets whose runs were captured.
    """
    from build.adoption_measurements import all_routes, load_inputs
    from build.serialize_routing import load_routing
    from build.snapshot_source_runs import source_dataset

    base = root or ROOT
    routing = load_routing(base)
    return {
        route["route_id"]: source_dataset(routing, route.get("source") or None)
        for route in all_routes(load_inputs(base)[0])
    }


@dataclass
class Report:
    """Everything the gate found, in the order it prints."""

    binding: Mapping
    problems: list[str]
    evidence: dict[str, Evidence]
    judgements: list[Judgement] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for j in self.judgements:
            out[j.status] = out.get(j.status, 0) + 1
        return dict(sorted(out.items()))

    def blocked(self) -> list[Judgement]:
        return [j for j in self.judgements if j.disposition == "block"]

    def review(self) -> list[Judgement]:
        return [j for j in self.judgements if j.disposition == "review"]


def evaluate(
    read: Mapping,
    runs: Sequence[Mapping],
    datasets_by_route: Mapping[str, str | None],
    now: datetime.datetime | None = None,
) -> Report:
    """The whole gate over one read and one run snapshot. Pure: no file, clock or network."""
    current = now or _utcnow()
    binding = read.get("binding") or {}
    rows = read.get("rows")
    if rows is None:
        raise ValueError("the read document carries no `rows`; write it with "
                         "`build.adoption_freshness --live --json-out`")
    problems = read_problems(binding, runs, current)
    evidence: dict[str, Evidence] = {}
    if not problems:
        started = _instant(binding["run_started_at"])
        assert started is not None  # read_problems checked it
        for dataset in sorted({d for d in datasets_by_route.values() if d}):
            evidence[dataset] = dataset_evidence(runs, dataset, started, current)
    report = Report(binding=binding, problems=problems, evidence=evidence)
    for row in rows:
        report.judgements.append(
            judge(row, datasets_by_route.get(row["route_id"]), problems, evidence)
        )
    report.judgements.sort(key=lambda j: (j.product_slug, j.route_id))
    return report


def render(report: Report) -> str:
    """The report as text: the evidence, the census, then every row it would block.

    `source_unavailable` rows are grouped by reason, since one failed collector or one unbound
    read accounts for every row it touches and repeating the reason per row buries the rest.
    Every other blocked or review row gets its own line, because each is its own finding.
    """
    lines = ["adoption release gate (report-only; #410)", ""]
    b = report.binding
    if report.problems:
        lines.append(f"read           NOT CURRENT: {report.problems[0]}")
    else:
        lines.append(f"read           bound to run {b.get('run_id')} "
                     f"{b.get('run_trigger_type')}/{b.get('run_status')} started "
                     f"{b.get('run_started_at')}, read {b.get('read_at')}")
    for ev in report.evidence.values():
        lines.append(f"  {ev.dataset:<24}{ev.verdict:<9}{ev.reason}")
    lines.append("")
    for status, n in report.counts().items():
        mark = "block" if status in BLOCKING else ("review" if status in REVIEW else "")
        lines.append(f"  {status:<22}{n:>5}  {mark}".rstrip())
    blocked, review = report.blocked(), report.review()
    lines.append("")
    lines.append(f"would block    {len(blocked)} row(s)")
    lines.append(f"for review     {len(review)} row(s)")

    unavailable: dict[str, list[str]] = {}
    for j in blocked:
        if j.status == "source_unavailable":
            unavailable.setdefault(j.explanation, []).append(j.product_slug)
    for reason, slugs in sorted(unavailable.items()):
        lines.append("")
        lines.append(f"source_unavailable, {len(slugs)} row(s): {reason}")
        lines.append("  " + ", ".join(slugs))
    for title, group in (
        ("would block", [j for j in blocked if j.status != "source_unavailable"]),
        ("for review", review),
    ):
        if not group:
            continue
        lines.append("")
        lines.append(f"{title}:")
        for j in group:
            lines.append(f"  {j.product_slug}  {j.status}  {j.route_id}  "
                         f"recorded {j.recorded_level} measured {j.measured_level}")
            lines.append(f"      {j.explanation}")
    lines.append("")
    lines.append("report-only: nothing is blocked; exit 0")
    return "\n".join(lines)


def as_json(report: Report) -> dict:
    return {
        "mode": "report",
        "binding": dict(report.binding),
        "read_problems": report.problems,
        "evidence": {k: vars(v) for k, v in report.evidence.items()},
        "counts": report.counts(),
        "would_block": [vars(j) | {"disposition": j.disposition} for j in report.blocked()],
        "review": [vars(j) | {"disposition": j.disposition} for j in report.review()],
    }


def load_runs(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read", type=Path, required=True,
                        help="the --json-out document of build.adoption_freshness --live")
    parser.add_argument("--source-runs", type=Path, required=True,
                        help="source_runs.csv from build.snapshot_source_runs, captured after the read")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = parser.parse_args(argv)
    try:
        read = json.loads(args.read.read_text())
        runs = load_runs(args.source_runs)
        report = evaluate(read, runs, route_datasets(root))
    except (OSError, ValueError, KeyError) as exc:
        print(f"cannot report: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(as_json(report), indent=2, default=str))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
