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

## A match is not an agreement until a run is attributable

`docs/architecture/data-architecture.md` §4.3 is explicit that a current-state table cannot prove
a collector ran: identical values are what a successful collection, a failed collector whose
previous table stayed readable, and a source that never ran at all all look like. So an
observation with no run behind it may not be read as agreement, and that rule is not suspended
here. The comparison says the measured band MATCHES the recorded one; what turns a match into a
confirmation is evidence of the run that produced the rows.

`build/read_binding.py` is where that evidence comes from. The read of
`observations.product_adoption_current` is bracketed between two control-plane reads of the
model's newest materialization, and a read served by one materialization throughout is bound to
that materialization's `run_id`. The attribution is at READ grain, not row grain — every row came
from the run that materialized the table, which is not yet true of each observation individually
(#355) — so this closes nothing in #355 and the reconciliation's `source_unavailable` status is
unchanged by it. What it changes is that a date now names a run somebody can look up.

Read-grain binding leaves one thing open, and the date itself is what closes it: if a collector
failed and the table is serving last week's figures, the run that materialized it is still
attributable, and what gets written is those figures' own observation date. Staleness is recorded
rather than laundered into currency.

Without a bound read — over the frozen baseline parquet, or when a refresh lands mid-bracket —
nothing is dated at all, and the queue is emitted exactly as it would be otherwise. The
comparison is diagnostic on its own; it dates only when it can say which run measured what.

## One measurement, written down twice

A derived date is recorded in both halves of the evidence, deliberately. The axis carries
`derived_from` — the snapshot, the run, the route, the level that was measured and the date it
was observed — and the snapshot ledger carries the same measurement under the product's slug.
Neither is believed on its own: the gate requires them to agree, so an edit to a score file that
moves the date, re-bands the level or renames the route parts company with the ledger and fails.
A record that describes only itself can be checked against nothing.

The recorded level is part of the support for the same reason. The run confirmed the band it
measured; once a person re-bands the axis, that confirmation describes a band the score has left,
and the date has to be earned again rather than inherited by the new level.

## Advance-only

A stored date newer than the derived one is a person's confirmation of something the run has not
seen, so the run leaves it alone. A derived date only ever moves a date forward.

Usage:
    uv run python -m build.adoption_freshness                  # the queue, over the baseline
    uv run python -m build.adoption_freshness --live           # over the deployed current table
    uv run python -m build.adoption_freshness --queue queue.md # write the tier-change queue
    uv run python -m build.adoption_freshness --live --apply   # write the dates it earned

`--apply` without `--live` earns nothing: the frozen baseline carries no run to attribute a
measurement to, so the run reports what it would have dated and writes no date.
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
DERIVATION_KEYS = (
    "observation_snapshot_id",
    "source_run_id",
    "route_id",
    "measured_level",
    "measurement_as_of",
)

#: The fields the ledger keeps per agreeing product — `derived_from` minus the snapshot id it is
#: already filed under. The gate requires the two records to carry the same values.
AGREEMENT_KEYS = ("source_run_id", "route_id", "measured_level", "measurement_as_of")

#: What a bound read has to name before a measurement may date anything.
BINDING_KEYS = ("run_id", "materialization_id", "model", "read_at")

BAND_MATCH = "band_match"
TIER_CHANGE = "tier_change"
ROUTE_DISAGREEMENT = "route_disagreement"
NOT_COMPARED = "not_compared"


def binding_problems(binding: Mapping | None) -> list[str]:
    """Why this read cannot attribute its rows to a source run, or an empty list.

    The three ways a read fails to bind are different facts and are reported as such: the baseline
    carries no binding at all, a bracket that straddled a refresh cannot say which materialization
    served the rows, and a bound bracket missing its identifiers names a run nobody can look up.
    """
    if not binding:
        return ["the read recorded no binding, so no run can be attributed to it"]
    status = binding.get("binding_status")
    if status == "bound":
        missing = [k for k in BINDING_KEYS if not binding.get(k)]
        if missing:
            return [f"the binding names no {' and no '.join(missing)}"]
        return []
    if status == "unstable":
        return [
            f"a refresh landed mid-read ({binding.get('materialization_id_before')} -> "
            f"{binding.get('materialization_id_after')}), so the rows cannot be attributed to "
            f"one materialization"
        ]
    if status == "unbound":
        return [str(binding.get("reason") or "the observations are not bound to a source run")]
    return [f"unrecognized binding status {status!r}"]


def verdict(row: Mapping) -> str:
    """What one reconciliation row says about the recorded band.

    ``delta`` is the reconciliation's own answer to "may these two numbers be subtracted": it is
    null wherever the instruments differ or either level is absent. So a zero delta is a MATCH on
    the same instrument, and a non-zero one is a tier change. Levels that differ with no delta
    between them are a disagreement about the route, not about the tier.

    A match is as far as a comparison reaches. Whether it is an agreement that may date an axis
    depends on evidence this row does not carry — the run that produced the observations — which
    is `binding_problems`' question and the reason `plan` takes a binding.
    """
    recorded, measured, delta = row["recorded_level"], row["measured_level"], row["delta"]
    if delta == 0:
        return BAND_MATCH
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


def derivation(row: Mapping, binding: Mapping) -> dict:
    """What an agreeing row records beside the date it earns.

    The measured level is kept because the confirmation is OF that level: a score re-banded
    afterwards is no longer the thing the run agreed with. The run id is kept because a date whose
    run cannot be named is a date §4.3 does not allow.
    """
    return {
        "observation_snapshot_id": row["observation_snapshot_id"],
        "source_run_id": binding["run_id"],
        "route_id": row["route_id"],
        "measured_level": row["measured_level"],
        "measurement_as_of": _as_date(row["measurement_as_of"]),
    }


@dataclass(frozen=True)
class Change:
    """One product's derived date, and the derivation that supports it."""

    product_slug: str
    was: str | None
    now: str
    derived_from: dict
    verdict: str = BAND_MATCH


def _score_path(root: Path, slug: str) -> Path:
    return root / "sources" / "scores" / f"{slug}.yaml"


def _already_supported(block: Mapping, derived: Mapping) -> bool:
    """Is this axis already dated by the same measurement, under some run?

    The run id is excluded from the comparison on purpose. A later run that reads the same
    observations mints the same snapshot id and measures the same band, so it re-confirms a date
    that is already correct and re-writing it would churn three hundred files a week to swap one
    opaque identifier for another. What matters is that the measurement is the same measurement.
    """
    stored = block.get(DERIVATION_FIELD)
    if not isinstance(stored, dict):
        return False
    return all(
        stored.get(k) == derived.get(k) for k in DERIVATION_KEYS if k != "source_run_id"
    ) and str(block.get("last_verified")) == str(derived["measurement_as_of"])


def plan(
    rows: Iterable[Mapping], binding: Mapping | None = None, root: Path | None = None
) -> tuple[list[Change], list[str]]:
    """The dates this run earns, and a line for every match it declined to date.

    Declines are reported rather than dropped, because most of them are the mechanism working: a
    match that does not move a date is the normal outcome once the corpus is current; a match
    whose observation is older than the stored date is a person's confirmation the run must not
    overwrite; and a match from a read with no run behind it is a comparison, never a
    confirmation. The last of those declines EVERY match at once, so it is reported once per
    product rather than as a silent empty plan.
    """
    base = root or ROOT
    changes: list[Change] = []
    declined: list[str] = []
    unbound = binding_problems(binding)
    for row in rows:
        if verdict(row) != BAND_MATCH:
            continue
        slug = row["product_slug"]
        if unbound:
            declined.append(
                f"{slug}: the route measured the recorded band, but {unbound[0]}. An unbound "
                f"observation is not an agreement (§4.3), so nothing is dated"
            )
            continue
        derived = derivation(row, binding or {})
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
        if _already_supported(block, derived):
            continue
        changes.append(Change(slug, was, now, derived))
    changes.sort(key=lambda c: c.product_slug)
    return changes, declined


def agreements(changes: Iterable[Change]) -> dict[str, dict]:
    """The ledger's half of the record: what was measured for each product this run dated."""
    return {
        change.product_slug: {k: change.derived_from[k] for k in AGREEMENT_KEYS}
        for change in changes
    }


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
        if change.verdict != BAND_MATCH:
            raise ValueError(
                f"{change.product_slug}: refusing to write adoption.last_verified for a "
                f"{change.verdict!r} row. A disagreement confirms nothing, so it leaves the "
                f"date where it is and goes on the tier-change queue."
            )
        if not change.derived_from.get("source_run_id"):
            raise ValueError(
                f"{change.product_slug}: refusing to write a date with no source run behind it. "
                f"An observation that cannot be attributed to a run is not an agreement (§4.3)."
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
        recorded_level = ((yaml.safe_load(text) or {}).get(DERIVED_AXIS) or {}).get("level")
        if recorded_level != change.derived_from.get("measured_level"):
            raise ValueError(
                f"{change.product_slug}: the score records level {recorded_level} but the "
                f"measurement read {change.derived_from.get('measured_level')}; a run confirms "
                f"the band it measured, and this is not that band"
            )
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


def derivation_problems(
    slug: str,
    block: Mapping,
    ledger: Mapping,
    known_routes: Iterable[str] | None = None,
) -> list[str]:
    """Why this axis's `derived_from` does not support its `last_verified`, or an empty list.

    A malformed derivation is a failure rather than a fallback. The record exists so a date can
    be audited without the warehouse, and a record that cannot be read is a date nobody can
    check — worse than no record, because the field advertises a support it is not giving.

    The questions asked here are the ones a reader of the score file cannot answer alone. Does
    the date equal the observation it names? Is the level still the level that was measured? Is
    the route one the routing tables compile? Does the snapshot ledger, written by the same run,
    record this product's agreeing measurement — with the same run, route, level and date? A
    derivation that only agrees with itself is checked against nothing.

    `known_routes` is the compiled route ids when the caller has them; the route is not checked
    for existence when it is not supplied.
    """
    record = block.get(DERIVATION_FIELD)
    if record is None:
        return []
    key = f"{slug}:{DERIVED_AXIS}"
    if not isinstance(record, dict):
        return [f"{key}: {DERIVATION_FIELD} is {type(record).__name__}, not a mapping"]
    # `not record.get(k)` would read a measured level of 0 as missing, and 0 is a real band.
    missing = [k for k in DERIVATION_KEYS if record.get(k) is None or record.get(k) == ""]
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
    if block.get("level") != record["measured_level"]:
        problems.append(
            f"{key}: the score records level {block.get('level')}, but the measurement that "
            f"dated it read level {record['measured_level']}. A re-banded score is not confirmed "
            f"by the run that agreed with the band it used to carry"
        )
    if known_routes is not None and str(record["route_id"]) not in set(known_routes):
        problems.append(
            f"{key}: route {record['route_id']!r} is not a route the routing tables compile, so "
            f"nothing could have measured this band on it"
        )
    snapshot_id = str(record["observation_snapshot_id"])
    entry = ledger.get(snapshot_id)
    if entry is None:
        problems.append(
            f"{key}: observation snapshot {snapshot_id[:12]}… is not in "
            f"sources/snapshots/observation_snapshots.yaml, so the date it dates cannot be "
            f"resolved to a window"
        )
        return problems
    if not (str(entry["observed_from"]) <= as_of <= str(entry["observed_to"])):
        problems.append(
            f"{key}: the observation date {as_of} is outside snapshot {snapshot_id[:12]}…, "
            f"which observed {entry['observed_from']} .. {entry['observed_to']}"
        )
    agreed = (entry.get("agreements") or {}).get(slug)
    if agreed is None:
        problems.append(
            f"{key}: snapshot {snapshot_id[:12]}… records no agreeing measurement for this "
            f"product, so the date rests on a claim the score file makes about itself"
        )
        return problems
    for field in AGREEMENT_KEYS:
        if agreed.get(field) != record[field]:
            problems.append(
                f"{key}: {DERIVATION_FIELD} says {field} is {record[field]!r}, the snapshot "
                f"ledger says {agreed.get(field)!r}; the two records of one measurement disagree"
            )
    return problems


def known_route_ids(root: Path | None = None) -> set[str]:
    """Every route id the routing tables compile.

    A derived date names the route that measured it, and a route id nothing compiles cannot have
    measured anything — the commonest way for that to be true is a hand edit. Compiling reads the
    routing source, so gates call this once and pass the result down rather than per product.
    """
    from build.adoption_measurements import all_routes, load_inputs

    return {route["route_id"] for route in all_routes(load_inputs(root or ROOT)[0])}


# --- the CLI ---------------------------------------------------------------------


#: What the baseline read honestly reports about its own attribution. The frozen parquet records
#: `source_run_id` as NULL for every row and its capture says so (§4.3); there is no run to name,
#: and inventing one from the capture timestamp is the timestamp inference the binding refuses.
BASELINE_BINDING = {
    "binding_status": "unbound",
    "model": "warehouse/data/observations/product_adoption_baseline.parquet",
    "reason": (
        "the frozen baseline records no source run for any of its rows, so a measurement read "
        "from it cannot be attributed to a run that produced it"
    ),
}


def _reconciliation_rows(
    live: bool, allow_dirty: bool
) -> tuple[list[dict], list[dict], dict]:
    """The reconciliation rows, the observations behind them, and what the read is bound to.

    The live read goes through `build.read_binding.bound_read`, which brackets it between two
    control-plane reads of `observations.product_adoption_current`'s newest materialization. The
    baseline read is honestly unbound: nothing about a frozen file names the run that filled it.
    """
    from build.adoption_reconciliation import resolve

    if live:
        from build.adoption_measurements import load_current_observations
        from build.read_binding import bound_read

        read = bound_read(load_current_observations)
        observations = read.rows
        binding = {
            **read.binding,
            "read_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        }
    else:
        from build.observation_snapshot import rows_from_parquet

        observations = rows_from_parquet()
        binding = dict(BASELINE_BINDING)
    rows = resolve(observations, allow_dirty=allow_dirty,
                   evaluated_at=datetime.datetime.now(datetime.timezone.utc))
    return rows, observations, binding


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

    rows, observations, binding = _reconciliation_rows(args.live, args.allow_dirty)
    snapshot = snapshot_record(observations)
    entries = queue(rows)
    changes, declined = plan(rows, binding, root=base)
    unbound = binding_problems(binding)

    if args.json:
        print(json.dumps({"snapshot": snapshot, "binding": binding, "queue": entries,
                          "dates": [c.__dict__ for c in changes]}, indent=2, default=str))
        return 0

    counts: dict[str, int] = {}
    for row in rows:
        kind = verdict(row)
        counts[kind] = counts.get(kind, 0) + 1
    print(f"observation snapshot    {snapshot['observation_snapshot_id'][:12]}…  "
          f"observed {snapshot['observed_from']} .. {snapshot['observed_to']}  "
          f"({snapshot['row_count']} rows)")
    if unbound:
        print(f"source run              NONE — {unbound[0]}")
    else:
        print(f"source run              {binding['run_id']}  "
              f"(materialization {binding['materialization_id']}, read {binding['read_at']})")
    for kind in sorted(counts):
        print(f"  {kind:<20}{counts[kind]:>5}")
    print(f"dates earned            {len(changes)}")
    print(f"matches not dated       {len(declined)}")
    print()
    print("tier-change queue")
    print(render_queue(entries))

    if args.queue:
        args.queue.write_text(render_queue(entries) + "\n")
    if args.apply and unbound:
        # Not an error. The comparison is worth running unbound — it is what produces the queue —
        # and a read that cannot name its run has simply not earned a date this week.
        print(f"\nno date earned: {unbound[0]}")
    elif args.apply:
        record_snapshot(
            snapshot,
            agreements=agreements(changes),
            path=base / "sources/snapshots/observation_snapshots.yaml",
        )
        written = apply(changes, root=base)
        print(f"\nwrote {written} score file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
