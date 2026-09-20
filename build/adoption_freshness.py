"""Adoption's date comes from the run that measured it, and a disagreement raises the product.

`build/adoption_reconciliation.py` compares what the authoritative route MEASURES for a product
against what a curator RECORDED, one row per product. This turns that comparison into the two
things it is for:

  * **an agreement dates the axis.** Where the route measured the same band a curator recorded,
    the recorded band has been re-derived from an observation the collectors fetched, and
    `adoption.last_verified` takes the date of that observation.
  * **a disagreement raises the product.** Where the measured band differs, nothing was
    confirmed, the stored date stays exactly where it was, and the product goes on the
    tier-change queue for a person to read.

## Why this is a confirmation and not a computation over the repo

`docs/reference/evidence-and-freshness.md` forbids a date derived by computing over already-
recorded values, and that rule is what makes this legitimate rather than an exception to it.
The comparison's left-hand side comes from outside the repository: a collector fetched a usage
figure, the warehouse recorded it with an `observed_at`, and the routing tables banded it. When
that band equals the recorded one, something external was consulted and the recorded conclusion
was re-established — which is the general case the guide describes, arriving by machine.

What is emphatically NOT a confirmation is the other direction. A curator's citation of a counts
endpoint is a hashed snapshot of a number that changes daily; re-fetching it and finding the
bytes unchanged would confirm the page still renders, never that the figure is current. The date
rests on the observation, and the citation records where a person looked.

## The date is the observation's, not the run's

`measurement_as_of` is the OLDEST contributing observation, so an aggregate is dated by its
stalest part. That is the date written, rather than the day the run executed: a run that
compares month-old observations has confirmed a month-old figure, and dating it today would
claim a currency nobody has. The `observation_snapshot_id` and the route are written beside it,
and `sources/snapshots/observation_snapshots.yaml` resolves that id to the window it observed,
so the claim can be checked without the warehouse.

## Comparing across instruments is not comparing

A row whose measured instrument differs from the recorded one carries no delta, by the
reconciliation's own rule: stars and monthly downloads are not the same quantity, so their
levels neither agree nor disagree. Such a row can never date an axis, and where the two levels
differ it is queued as a route disagreement rather than a tier change — the finding is that the
recorded instrument and the applicable route disagree about what to measure, which is a
different repair from re-banding a figure.

## Advance-only

A stored date newer than the derived one is a person's confirmation of something the run has not
seen, so the run leaves it alone. A derived date only ever moves a date forward.

Usage:
    uv run python -m build.adoption_freshness                  # over the committed baseline
    uv run python -m build.adoption_freshness --live           # over the deployed current table
    uv run python -m build.adoption_freshness --queue queue.md # write the tier-change queue
    uv run python -m build.adoption_freshness --apply          # write the dates it earned
"""

from __future__ import annotations

import argparse
import datetime
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from build import components
from build.observation_snapshot import record_snapshot, snapshot_record

ROOT = Path(__file__).resolve().parents[1]

#: The field a derived date carries beside it, and the axis it may appear on.
DERIVATION_FIELD = "derived_from"
DERIVED_AXIS = "adoption"
DERIVATION_KEYS = ("observation_snapshot_id", "route_id", "measurement_as_of")

AGREED = "agreed"
TIER_CHANGE = "tier_change"
ROUTE_DISAGREEMENT = "route_disagreement"
NOT_COMPARED = "not_compared"


def verdict(row: Mapping) -> str:
    """What one reconciliation row says about the recorded band.

    ``delta`` is the reconciliation's own answer to "may these two numbers be subtracted": it is
    null wherever the instruments differ or either level is absent. So a zero delta is an
    agreement on the same instrument, and a non-zero one is a tier change. Levels that differ
    with no delta between them are a disagreement about the route, not about the tier.
    """
    recorded, measured, delta = row["recorded_level"], row["measured_level"], row["delta"]
    if delta == 0:
        return AGREED
    if delta is not None:
        return TIER_CHANGE
    if recorded is not None and measured is not None and recorded != measured:
        return ROUTE_DISAGREEMENT
    return NOT_COMPARED


def queue(rows: Iterable[Mapping]) -> list[dict]:
    """The tier-change queue: every product whose measured band differs from the recorded one."""
    out = []
    for row in rows:
        kind = verdict(row)
        if kind not in (TIER_CHANGE, ROUTE_DISAGREEMENT):
            continue
        out.append(
            {
                "product_slug": row["product_slug"],
                "kind": kind,
                "recorded_level": row["recorded_level"],
                "recorded_instrument_type": row["recorded_instrument_type"],
                "measured_level": row["measured_level"],
                "measured_instrument_type": row["measured_instrument_type"],
                "route_id": row["route_id"],
                "route_authority": row["route_authority"],
                "raw_value": row["raw_value"],
                "measurement_as_of": _as_date(row["measurement_as_of"]),
            }
        )
    out.sort(key=lambda r: (r["kind"], r["product_slug"]))
    return out


def render_queue(entries: Sequence[Mapping]) -> str:
    """The queue as one line per product, naming both levels and the route."""
    if not entries:
        return "no disagreements: every comparable route measured the band that is recorded"
    lines = []
    for entry in entries:
        lines.append(
            f"{entry['product_slug']:<34} recorded {entry['recorded_level']} "
            f"({entry['recorded_instrument_type'] or 'no instrument'}) vs measured "
            f"{entry['measured_level']} ({entry['measured_instrument_type'] or 'no instrument'}) "
            f"on route {entry['route_id']}"
            + ("" if entry["kind"] == TIER_CHANGE else "  [instruments differ]")
        )
    return "\n".join(lines)


def _as_date(value: object) -> str | None:
    """An observation timestamp as an ISO date string."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)[:10]


def derivation(row: Mapping) -> dict:
    """What an agreeing row records beside the date it earns."""
    return {
        "observation_snapshot_id": row["observation_snapshot_id"],
        "route_id": row["route_id"],
        "measurement_as_of": _as_date(row["measurement_as_of"]),
    }


@dataclass(frozen=True)
class Change:
    """One product's derived date, and the derivation that supports it."""

    product_slug: str
    was: str | None
    now: str
    derived_from: dict
    verdict: str = AGREED


def _score_path(root: Path, slug: str) -> Path:
    return root / "sources" / "scores" / f"{slug}.yaml"


def plan(rows: Iterable[Mapping], root: Path | None = None) -> tuple[list[Change], list[str]]:
    """The dates this run earns, and a line for every agreement it declined to date.

    Declines are reported rather than dropped: an agreement that does not move a date is the
    normal outcome once the corpus is current, and an agreement whose observation is older than
    the stored date is a person's confirmation the run must not overwrite.
    """
    base = root or ROOT
    changes: list[Change] = []
    declined: list[str] = []
    for row in rows:
        if verdict(row) != AGREED:
            continue
        slug = row["product_slug"]
        derived = derivation(row)
        now = derived["measurement_as_of"]
        path = _score_path(base, slug)
        if now is None:
            declined.append(f"{slug}: the agreeing measurement carries no observation date")
            continue
        if not path.exists():
            declined.append(f"{slug}: no score file")
            continue
        block = (yaml.safe_load(path.read_text()) or {}).get(DERIVED_AXIS) or {}
        was = None if block.get("last_verified") is None else str(block["last_verified"])
        if was is not None and was > now:
            declined.append(
                f"{slug}: stored {was} is newer than the observation {now}; a person confirmed "
                f"it more recently than this run measured it"
            )
            continue
        if was == now and block.get(DERIVATION_FIELD) == derived:
            continue
        changes.append(Change(slug, was, now, derived))
    changes.sort(key=lambda c: c.product_slug)
    return changes, declined


def apply(changes: Iterable[Change], root: Path | None = None) -> int:
    """Write the derived dates. Returns how many files changed.

    Every change is re-checked here rather than trusted. `plan` is the only thing that builds
    one, but the write is the act that matters, so the refusal lives beside it: a change that is
    not an agreement, or whose date is not the observation date it claims, is a date with no
    confirmation under it and this raises instead of writing it.
    """
    base = root or ROOT
    written = 0
    for change in changes:
        if change.verdict != AGREED:
            raise ValueError(
                f"{change.product_slug}: refusing to write adoption.last_verified for a "
                f"{change.verdict!r} row. A disagreement confirms nothing, so it leaves the "
                f"date where it is and goes on the tier-change queue."
            )
        if change.now != change.derived_from.get("measurement_as_of"):
            raise ValueError(
                f"{change.product_slug}: the date {change.now} is not the observation date "
                f"{change.derived_from.get('measurement_as_of')} it claims to derive from"
            )
        if change.was is not None and change.was > change.now:
            raise ValueError(
                f"{change.product_slug}: refusing to move adoption.last_verified backwards "
                f"({change.was} -> {change.now})"
            )
        path = _score_path(base, change.product_slug)
        text = path.read_text()
        text = components.put_field(text, change.now, axis=DERIVED_AXIS, key="last_verified")
        text = components.put_field(
            text, dict(change.derived_from), axis=DERIVED_AXIS, key=DERIVATION_FIELD,
            before="sources",
        )
        if text != path.read_text():
            path.write_text(text)
            written += 1
    return written


# --- what the gates ask of a derived date ---------------------------------------


def derivation_problems(slug: str, block: Mapping, ledger: Mapping) -> list[str]:
    """Why this axis's `derived_from` does not support its `last_verified`, or an empty list.

    A malformed derivation is a failure rather than a fallback. The record exists so a date can
    be audited without the warehouse, and a record that cannot be read is a date nobody can
    check — worse than no record, because the field advertises a support it is not giving.
    """
    record = block.get(DERIVATION_FIELD)
    if record is None:
        return []
    key = f"{slug}:{DERIVED_AXIS}"
    if not isinstance(record, dict):
        return [f"{key}: {DERIVATION_FIELD} is {type(record).__name__}, not a mapping"]
    missing = [k for k in DERIVATION_KEYS if not record.get(k)]
    if missing:
        return [f"{key}: {DERIVATION_FIELD} records no {' and no '.join(missing)}"]
    problems = []
    claimed = None if block.get("last_verified") is None else str(block["last_verified"])
    as_of = str(record["measurement_as_of"])
    if claimed != as_of:
        problems.append(
            f"{key}: last_verified {claimed} is not the observation date {as_of} it derives "
            f"from; a derived date is the observation's date, never the run's"
        )
    snapshot_id = str(record["observation_snapshot_id"])
    entry = ledger.get(snapshot_id)
    if entry is None:
        problems.append(
            f"{key}: observation snapshot {snapshot_id[:12]}… is not in "
            f"sources/snapshots/observation_snapshots.yaml, so the date it dates cannot be "
            f"resolved to a window"
        )
    elif not (str(entry["observed_from"]) <= as_of <= str(entry["observed_to"])):
        problems.append(
            f"{key}: the observation date {as_of} is outside snapshot {snapshot_id[:12]}…, "
            f"which observed {entry['observed_from']} .. {entry['observed_to']}"
        )
    return problems


def supports_date(block: Mapping, ledger: Mapping) -> bool:
    """Does this axis carry a derivation that supports its own `last_verified`?

    The one question both date gates ask, in one place, so the two cannot drift into different
    answers. False whenever the record is absent, malformed, or dates something else — a gate
    reading False falls back to its ordinary requirement, and `derivation_problems` is what
    reports the malformed case as a failure.
    """
    return bool(block.get(DERIVATION_FIELD)) and not derivation_problems("_", block, ledger)


# --- the CLI ---------------------------------------------------------------------


def _reconciliation_rows(live: bool, allow_dirty: bool) -> tuple[list[dict], list[dict]]:
    from build.adoption_reconciliation import resolve

    if live:
        from build.adoption_measurements import load_current_observations

        observations = load_current_observations()
    else:
        from build.observation_snapshot import rows_from_parquet

        observations = rows_from_parquet()
    rows = resolve(observations, allow_dirty=allow_dirty,
                   evaluated_at=datetime.datetime.now(datetime.timezone.utc))
    return rows, observations


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="read the deployed current table via pyoso")
    parser.add_argument("--apply", action="store_true",
                        help="write the derived dates into sources/scores/")
    parser.add_argument("--queue", type=Path, default=None,
                        help="write the tier-change queue to this file")
    parser.add_argument("--json", action="store_true", help="emit the queue as JSON")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="stamp a diagnostic declaration_version_id over a dirty worktree")
    args = parser.parse_args(argv)
    base = root or ROOT

    rows, observations = _reconciliation_rows(args.live, args.allow_dirty)
    snapshot = snapshot_record(observations)
    entries = queue(rows)
    changes, declined = plan(rows, root=base)

    if args.json:
        print(json.dumps({"snapshot": snapshot, "queue": entries,
                          "dates": [c.__dict__ for c in changes]}, indent=2, default=str))
        return 0

    counts: dict[str, int] = {}
    for row in rows:
        kind = verdict(row)
        counts[kind] = counts.get(kind, 0) + 1
    print(f"observation snapshot    {snapshot['observation_snapshot_id'][:12]}…  "
          f"observed {snapshot['observed_from']} .. {snapshot['observed_to']}  "
          f"({snapshot['row_count']} rows)")
    for kind in sorted(counts):
        print(f"  {kind:<20}{counts[kind]:>5}")
    print(f"dates earned            {len(changes)}")
    print(f"agreements not dated    {len(declined)}")
    print()
    print("tier-change queue")
    print(render_queue(entries))

    if args.queue:
        args.queue.write_text(render_queue(entries) + "\n")
    if args.apply:
        record_snapshot(snapshot, path=base / "sources/snapshots/observation_snapshots.yaml")
        written = apply(changes, root=base)
        print(f"\nwrote {written} score file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
