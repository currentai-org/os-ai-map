"""Reconcile measured adoption against recorded adoption — the report, before the gate (§4.4).

`evaluation.product_adoption_measurements` says what the authoritative route MEASURES for a
product; `sources/scores/<slug>.yaml` records what a human ASSESSED. `evaluation.adoption_
reconciliation` compares the two. It keys on both release identities because a reconciliation
result depends on the declarations that selected the route AND on the measurements it read; it
carries no `release_id` — a release exists only once a pair has passed reconciliation and been
adjudicated for publication (§4.4).

## Complete coverage of the accepted assessments

Every recorded adoption assessment reaches a coherent outcome — the deliberate nulls included.
The population is exactly the products that carry an `adoption` block in `sources/scores`, one row
each, keyed on the applicable route (grain `(declaration_version_id, observation_snapshot_id,
product_slug, category_slug, route_id)`). The applicable route is resolved the same way the
measurements builder resolves it — the first route the product's DECLARATIONS make applicable — so
a measured product and its reconciliation row name the same route. A product that declares no
machine artifact is keyed on its recorded hand-authored instrument's route (`active_users`,
`reported_traction`); one with neither is keyed on its recorded instrument name so the row still
has a stable key.

## Statuses (report before block)

"The initial implementation should report before it blocks" (§4.4). This assigns a `status` and an
`explanation` and enforces nothing. Today, with row-to-run binding still missing (#355):

  * recorded level null                       -> ``abstained`` (a deliberate abstention, not a gap)
  * measured (an observation on the route)    -> ``source_unavailable`` — the observation is not
                                                 run-bound, so §4.3 forbids reading it as agreement;
                                                 the measured level and ``delta`` are still shown
  * the route abstained (null measured level) -> ``abstained``
  * a route applies but was not observed      -> ``unmeasured``

`measurement_freshness` is `unknown` for the same reason: freshness is a property of a bound run,
and there is no binding yet. The fuller status set (`agree`, `expected_difference`,
`route_mismatch`, the override statuses) becomes assignable once #355 binds observations to runs.

## Determinism

Both identities and `evaluated_at` are inputs, so the logic is pure and the goldens pin content
with fixed test identities. `evaluated_at` is a per-run wall-clock stamp and is excluded from the
content digest, as `ingested_at` is excluded from an observation's identity; the CLI stamps a real
UTC value on the emitted table.

Usage:
    uv run python -m build.adoption_reconciliation            # over the committed baseline
    uv run python -m build.adoption_reconciliation --live     # over the deployed current table
    uv run python -m build.adoption_reconciliation --json     # emit the rows
"""

from __future__ import annotations

import argparse
import datetime
import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from build.adoption_measurements import (
    all_routes,
    route_scopes,
    routing_policy_version,
    select_route,
)

ROOT = Path(__file__).resolve().parents[1]
_UTC = datetime.timezone.utc

COLUMNS: tuple[str, ...] = (
    "declaration_version_id",
    "observation_snapshot_id",
    "routing_policy_version",
    "product_slug",
    "category_slug",
    "route_id",
    "recorded_level",
    "recorded_instrument_type",
    "measured_level",
    "measured_instrument_type",
    "channel",
    "raw_value",
    "measurement_as_of",
    "route_authority",
    "measurement_freshness",
    "status",
    "delta",
    "override_id",
    "explanation",
    "evaluated_at",
)

# Columns that vary per run rather than per content, excluded from the content digest.
_NON_CONTENT = frozenset({"declaration_version_id", "evaluated_at"})

_UNBOUND_EXPLANATION = (
    "measurement derives from observations with no source_run_id (row-to-run binding is blocked "
    "on #355), so it cannot be validated as a current bound observation; per §4.3 an unbound "
    "SUCCESS reconciles to source_unavailable, not agreement"
)


def reconcile(
    recorded_scores: Mapping[str, Mapping],
    measurement_rows: Iterable[Mapping],
    routing_tables: Mapping[str, Sequence[Mapping]],
    category_of: Mapping[str, str],
    declared_artifacts: Mapping[str, set[str]],
    *,
    declaration_version_id: str,
    observation_snapshot_id: str,
    evaluated_at: datetime.datetime | None = None,
) -> list[dict]:
    """The reconciliation report over every recorded adoption assessment.

    ``recorded_scores`` is ``load_sources(...)["scores"]``; ``measurement_rows`` is the output of
    ``build.adoption_measurements.measurements`` for the same run. The applicable route is resolved
    from ``declared_artifacts`` (then the recorded instrument), reusing the measurements resolver.
    """
    routes = all_routes(routing_tables)
    scopes = route_scopes(routing_tables)
    policy_version = routing_policy_version(routing_tables)
    # The one authority each instrument carries, read off the compiled routes.
    authority_of = {r["instrument_type"]: r["authority"] for r in routes}
    measured_by_product = {m["product_slug"]: m for m in measurement_rows}

    rows: list[dict] = []
    for product_slug in sorted(recorded_scores):
        adoption = (recorded_scores[product_slug] or {}).get("adoption")
        if not isinstance(adoption, dict):
            continue  # not a recorded adoption assessment
        recorded_level = adoption.get("level")
        recorded_instrument = adoption.get("signal_type") or ""
        category_slug = category_of.get(product_slug)
        measurement = measured_by_product.get(product_slug)

        # Resolve the applicable route the same way the measurements builder does — the first
        # applicable route by precedence over declarations and the recorded instrument — so a
        # measured product names the same route here. When nothing is applicable (no artifact and a
        # non-hand-authored recorded instrument), key on the recorded instrument name for stability.
        route = select_route(
            declared_artifacts.get(product_slug, set()), recorded_instrument,
            category_slug, routes, scopes,
        )
        if route is None:
            route = {"route_id": recorded_instrument or "unresolved",
                     "instrument_type": recorded_instrument, "authority": authority_of.get(recorded_instrument, "")}

        measured_level = measurement["measured_level"] if measurement else None
        measured_instrument = measurement["instrument_type"] if measurement else route.get("instrument_type", "")

        # Never compare across instrument types: a delta is meaningful only when the measured and
        # recorded instruments match. A cross-instrument row withholds the delta and is classified
        # by authority, not turned into a number.
        same_instrument = bool(measurement) and measured_instrument == recorded_instrument
        delta = (
            measured_level - recorded_level
            if same_instrument and measured_level is not None and recorded_level is not None
            else None
        )

        if recorded_level is None:
            status = "abstained"
            explanation = "recorded adoption level is null — a deliberate abstention, not a gap"
        elif measurement is None:
            status = "unmeasured"
            explanation = (
                f"the applicable route {route['route_id']} has no observation for this product "
                f"(unbridged, hand-authored, or uncollected); the recorded assessment stands "
                f"unmeasured rather than being scored on a weaker route"
            )
        elif measured_level is None:
            status = "abstained"
            explanation = (
                f"route {route['route_id']} produced no banded level "
                f"(band_set_id={measurement['band_set_id']!r}); the route abstains"
            )
        elif not same_instrument:
            # The measurement and the recorded assessment are different instruments — a category
            # error to subtract. route_mismatch when an authoritative instrument is on either side
            # (the declaration and the recorded instrument disagree); expected_difference when both
            # are weak signals whose divergence is unsurprising.
            either_authoritative = (
                measurement["route_authority"] == "authoritative"
                or authority_of.get(recorded_instrument) == "authoritative"
            )
            status = "route_mismatch" if either_authoritative else "expected_difference"
            explanation = (
                f"recorded instrument {recorded_instrument!r} but the applicable route measures "
                f"{measured_instrument!r} — different instruments, so no delta is computed; "
                + ("an authoritative instrument disagrees with the measured route"
                   if either_authoritative
                   else "both are weak signals whose divergence is expected")
                + f". The measurement is also unbound ({_UNBOUND_EXPLANATION.split(';')[0]})."
            )
        else:
            status = "source_unavailable"
            explanation = _UNBOUND_EXPLANATION

        rows.append(
            {
                "declaration_version_id": declaration_version_id,
                "observation_snapshot_id": observation_snapshot_id,
                "routing_policy_version": policy_version,
                "product_slug": product_slug,
                "category_slug": category_slug,
                "route_id": route["route_id"],
                "recorded_level": recorded_level,
                "recorded_instrument_type": recorded_instrument,
                "measured_level": measured_level,
                "measured_instrument_type": measured_instrument,
                "channel": measurement["channel"] if measurement else None,
                "raw_value": measurement["raw_value"] if measurement else None,
                "measurement_as_of": measurement["measurement_as_of"] if measurement else None,
                "route_authority": measurement["route_authority"] if measurement else route.get("authority", ""),
                "measurement_freshness": "unknown",
                "status": status,
                "delta": delta,
                "override_id": None,
                "explanation": explanation,
                "evaluated_at": evaluated_at,
            }
        )

    rows.sort(key=lambda r: (r["product_slug"], r["category_slug"] or "", r["route_id"]))
    return rows


def canonical_row(row: Mapping) -> str:
    """A flat, deterministic serialization of one row for digesting — excludes per-run columns."""
    flat = dict(row)
    if isinstance(flat.get("measurement_as_of"), datetime.datetime):
        flat["measurement_as_of"] = flat["measurement_as_of"].isoformat()
    return json.dumps(
        {k: flat.get(k) for k in COLUMNS if k not in _NON_CONTENT},
        separators=(",", ":"),
        sort_keys=True,
    )


def resolve(
    observation_rows: Sequence[Mapping],
    root: Path | None = None,
    allow_dirty: bool = False,
    evaluated_at: datetime.datetime | None = None,
) -> list[dict]:
    """Build the report from an already-read observation set — one read feeds ids, measurements
    and reconciliation, so the whole release candidate is one atomic set of rows."""
    from build.adoption_measurements import load_inputs, measurements
    from build.declaration_version import resolve as resolve_declaration
    from build.observation_snapshot import observation_snapshot_id
    from build.validate import load_sources

    base = root or ROOT
    tables, band_rows, category_of, declared, recorded = load_inputs(base)
    dvid = resolve_declaration(base, allow_dirty=allow_dirty)["declaration_version_id"]
    osid = observation_snapshot_id(observation_rows)
    measurement_rows = measurements(
        observation_rows, tables, band_rows, category_of, declared, recorded,
        declaration_version_id=dvid, observation_snapshot_id=osid,
    )
    return reconcile(
        load_sources(base)["scores"], measurement_rows, tables, category_of, declared,
        declaration_version_id=dvid, observation_snapshot_id=osid, evaluated_at=evaluated_at,
    )


def resolve_over_baseline(root: Path | None = None, allow_dirty: bool = False,
                          evaluated_at: datetime.datetime | None = None) -> list[dict]:
    from build.observation_snapshot import rows_from_parquet

    return resolve(rows_from_parquet(), root=root, allow_dirty=allow_dirty, evaluated_at=evaluated_at)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the reconciliation rows as JSON")
    parser.add_argument("--live", action="store_true", help="read the deployed current table via pyoso")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="stamp a diagnostic declaration_version_id over a dirty worktree")
    args = parser.parse_args()

    if args.live:
        from build.adoption_measurements import load_current_observations

        observation_rows = load_current_observations()
    else:
        from build.observation_snapshot import rows_from_parquet

        observation_rows = rows_from_parquet()

    rows = resolve(
        observation_rows,
        allow_dirty=args.allow_dirty,
        evaluated_at=datetime.datetime.now(_UTC),
    )
    if args.json:
        print("\n".join(canonical_row(row) for row in rows))
        return 0

    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    print(f"reconciliation rows     {len(rows)}  (every recorded adoption assessment)")
    for status in sorted(by_status):
        print(f"  {status:<20}{by_status[status]:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
