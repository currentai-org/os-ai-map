"""Every open question the corpus is waiting on, in one list, with what each one waits for.

The questions already exist. They are spread across a hold file, a CI run summary, and the
deferred entries of the rulings log, and each is read by a different person on a different
day, or by nobody. This module gathers them into one queue so an agent can decide which ones
to put to the maintainer, and which ones it can take another pass at itself. It reads, prints,
and exits 0. It never writes to `sources/`.

## Where the rows come from

  * **Holds**: `sources/verification_queue.yaml`, one row per held axis.
  * **Deferred rulings**: `docs/rulings/log.yaml`, one row per `status: deferred` entry. These
    are questions that were asked and not answered, with the reason given.
  * **Contradictions** (with `--live` only): `build.check_contradictions.sweep` over the
    warehouse's artifact state, minus what `sources/contradictions_settled.yaml` already settles.
    It is off by default because it is the only leg that needs OSO.

## What a row waits on

Every row carries a `waits_on` value, because the question that matters to whoever works the
queue is who can move it:

  * `ruling`: a person has to decide. Every deferred ruling and every contradiction is one, and
    so is a hold whose reason asks for a ruling or a decision.
  * `fetch`: the evidence exists but could not be read from here, because of a 403, a proxy
    refusal, a script shell or a compressed PDF. The fix is a different route to the page, and
    asking a person about it wastes their time.
  * `schedule`: a scheduled run settles it. A hold says so with `settled_by:
    scheduled_reconciliation` (the marker the weekly reconciliation reads before it dates the
    axis and releases the hold), and only that field puts a hold here. Nothing to do until the
    run.
  * `evidence`: the pass did not find what would settle it. An agent can take another pass
    before anyone is asked.

Any other hold's reason is prose, so its class is read from its wording by the marker lists
below, in the order `fetch`, `ruling`. Wording never yields `schedule`: a reason that mentions a
reconciliation may still be asking a person something, and the field is the one statement that
the run alone settles it. A hold that matches no marker is `evidence`. The
cost of a wrong class is an agent attempting a question that should have gone to a person, and
the agent can escalate it, so the default is the agent's pass, not the maintainer's time.

## Output

A summary by source and class, then the rows. `--json` prints the rows. `--markdown` prints the
queue as a document a person or an OSO page can read. `--waits-on` narrows every form.

Usage:
    uv run python -m build.review_queue
    uv run python -m build.review_queue --waits-on ruling
    uv run python -m build.review_queue --json
    uv run python -m build.review_queue --markdown --live
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping

import yaml

from build.vocabulary import parse_date

ROOT = Path(__file__).resolve().parents[1]
QUEUE = Path("sources") / "verification_queue.yaml"
RULINGS = Path("docs") / "rulings" / "log.yaml"

WAITS_ON = ("ruling", "evidence", "fetch", "schedule")

# Read in this order; the first class whose marker appears in a hold's reason wins.
SCHEDULED = "scheduled_reconciliation"

MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("fetch", ("403", "proxy", "cannot be re-fetched", "not readable", "rate limit", "rate-limit",
               "script shell", "is compressed", "unreachable", "timed out")),
    ("ruling", ("ruling", "decision", "a maintainer", "editor must", "needs a person")),
)


@dataclasses.dataclass(frozen=True)
class Row:
    """One open question, with where it lives and who can move it."""

    id: str
    source: str
    subject: str
    waits_on: str
    detail: str
    since: str = ""
    axis: str = ""
    home: str = ""

    def age_days(self, today: date) -> int | None:
        parsed = parse_date(self.since) if self.since else None
        return (today - parsed).days if parsed else None


def classify(reason: str) -> str:
    text = " ".join(reason.split()).lower()
    for waits_on, markers in MARKERS:
        if any(m in text for m in markers):
            return waits_on
    return "evidence"


def hold_rows(held: Mapping[str, Mapping]) -> list[Row]:
    rows = []
    for slug, axes in sorted(held.items()):
        for axis, entry in sorted((axes or {}).items()):
            reason = " ".join(str((entry or {}).get("because", "")).split())
            rows.append(Row(
                id=f"hold:{slug}:{axis}",
                source="hold",
                subject=slug,
                axis=axis,
                waits_on=("schedule" if (entry or {}).get("settled_by") == SCHEDULED
                          else classify(reason)),
                detail=reason,
                since=str((entry or {}).get("since", "")),
                home=str(QUEUE),
            ))
    return rows


def load_rulings(root: Path | None = None) -> list[dict]:
    path = (root or ROOT) / RULINGS
    if not path.exists():
        return []
    return (yaml.safe_load(path.read_text()) or {}).get("rulings") or []


def ruling_rows(rulings: Iterable[Mapping]) -> list[Row]:
    return [
        Row(
            id=f"ruling:{r['id']}",
            source="ruling",
            subject=", ".join(str(x) for x in r.get("refs") or []) or str(r["id"]),
            waits_on="ruling",
            detail=" ".join(str(r.get("question", "")).split())
                   + (f" Deferred because: {' '.join(str(r['reasoning']).split())}"
                      if r.get("reasoning") else ""),
            since=str(r.get("date", "")),
            home=str(RULINGS),
        )
        for r in rulings
        if r.get("status") == "deferred"
    ]


def contradiction_rows(findings: Iterable) -> list[Row]:
    return [
        Row(
            id=f"contradiction:{f.leg}:{f.product_slug}:{f.artifact}",
            source="contradiction",
            subject=f.product_slug,
            waits_on="ruling",
            detail=f"{f.leg}: recorded {f.recorded}, observed {f.observed} ({f.artifact})",
            since=str(f.as_of),
            home="sources/contradictions_settled.yaml",
        )
        for f in findings
    ]


def gather(root: Path | None = None, live: bool = False, state_rows: Iterable | None = None) -> list[Row]:
    base = root or ROOT
    queue_path = base / QUEUE
    held = (yaml.safe_load(queue_path.read_text()) or {}).get("held") or {} if queue_path.exists() else {}
    rows = hold_rows(held) + ruling_rows(load_rulings(base))
    if live or state_rows is not None:
        from build import check_contradictions as cc

        if state_rows is None:
            from build.warehouse import query

            state_rows = query(cc.STATE_QUERY)
        products, scores, settled = cc.corpus(base)
        findings, _ = cc.sweep(state_rows, products, scores, settled)
        rows += contradiction_rows(findings)
    return rows


def summary(rows: list[Row]) -> str:
    counts = Counter((r.source, r.waits_on) for r in rows)
    sources = sorted({r.source for r in rows})
    lines = [f"{'source':<14}" + "".join(f"{w:>10}" for w in WAITS_ON) + f"{'total':>10}"]
    for s in sources:
        per = [counts[(s, w)] for w in WAITS_ON]
        lines.append(f"{s:<14}" + "".join(f"{n:>10}" for n in per) + f"{sum(per):>10}")
    per = [sum(counts[(s, w)] for s in sources) for w in WAITS_ON]
    lines.append(f"{'TOTAL':<14}" + "".join(f"{n:>10}" for n in per) + f"{sum(per):>10}")
    return "\n".join(lines)


def markdown(rows: list[Row], today: date) -> str:
    lines = ["# Review queue", "", f"Built {today.isoformat()} by `build.review_queue`.", "",
             "```", summary(rows), "```", ""]
    for waits_on in WAITS_ON:
        group = [r for r in rows if r.waits_on == waits_on]
        if not group:
            continue
        lines += [f"## Waits on {waits_on} ({len(group)})", "",
                  "| id | since | detail |", "|---|---|---|"]
        for r in sorted(group, key=lambda r: (r.since or "9999", r.id)):
            detail = r.detail.replace("|", "\\|")
            lines.append(f"| `{r.id}` | {r.since} | {detail} |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None, root: Path | None = None, today: date | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--waits-on", choices=WAITS_ON, help="only the rows that wait on this")
    parser.add_argument("--live", action="store_true", help="add the contradiction sweep (reads OSO)")
    form = parser.add_mutually_exclusive_group()
    form.add_argument("--json", action="store_true", help="print the rows as JSON")
    form.add_argument("--markdown", action="store_true", help="print the queue as a document")
    args = parser.parse_args(argv)

    today = today or date.today()
    rows = gather(root, live=args.live)
    if args.waits_on:
        rows = [r for r in rows if r.waits_on == args.waits_on]

    if args.json:
        print(json.dumps([dataclasses.asdict(r) | {"age_days": r.age_days(today)} for r in rows], indent=2))
    elif args.markdown:
        print(markdown(rows, today))
    else:
        print(summary(rows))
        print()
        for r in rows:
            print(f"{r.waits_on:<9} {r.id}  {r.detail[:120]}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
