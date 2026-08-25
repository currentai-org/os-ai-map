"""Reconcile measured adoption against recorded adoption — the report, before the gate (§4.4).

`evaluation.product_adoption_measurements` says what the authoritative route MEASURES for a
product; `sources/scores/<slug>.yaml` records what a human ASSESSED. `evaluation.adoption_
reconciliation` compares the two. It keys on both release identities because a reconciliation
result depends on the declarations that selected the route AND on the measurements it read; it
carries no `release_id` — a release exists only once a pair has passed reconciliation and been
adjudicated for publication (§4.4).

## Report before block

"The initial implementation should report before it blocks. Establish and adjudicate the baseline
first; only then enable the blocking transition" (§4.4). This module computes the report. It
assigns a `status` and an `explanation` per row but enforces nothing; no gate reads it yet.

## The honest current state: run binding is missing (#355)

`observations.product_adoption_current` carries no `source_run_id` — the platform exposes no
row-to-run binding, blocked on #355 — so no current measurement can be validated as a bound,
in-scope observation. §4.3 states the consequence directly: "an unbound SUCCESS remains
`source_unavailable` for reconciliation, not a validated current observation." So every measured
row here reconciles to **`source_unavailable`** today, and that is not a defect in this report —
it is the source-run contract reaching the gate exactly as designed, the status that keeps a
failed collector from being read as agreement. The measured-vs-recorded fields and the `delta` are
still populated, so the report shows what WOULD be adjudicated once #355 binds observations to
runs and the fuller status set (`agree`, `expected_difference`, `route_mismatch`, the override
statuses) becomes assignable. A row whose route itself abstained (a null measured level) is
`abstained`, distinct from an infrastructure absence.

`measurement_freshness` is `unknown` for the same reason: freshness is a property of a bound run,
and there is no binding yet.

## Scope of this first report

One row per measurement — grain `(declaration_version_id, observation_snapshot_id, product_slug,
category_slug, route_id)`, 1:1 with `product_adoption_measurements`. Products recorded with a
hand-authored instrument and no machine measurement (`reported_traction`, `active_users`) are not
rows here: their recorded instrument (`usage_volume` especially) maps to several routes, so a
single grain-defining `route_id` is not well defined for an unmeasured product. The CLI reports
how many such recorded-but-unmeasured products exist so the omission is visible rather than silent;
keying them into the report is follow-up work, alongside the run binding that would let their
statuses mean something.

## Identities and determinism

Both identities are inputs (derived at run time by the CLI, like the measurements builder), so the
logic stays pure and the goldens pin content with fixed test identities. `evaluated_at` is a
parameter for the same reason — a wall-clock stamp would make the table nondeterministic — and it
is excluded from the content digest, as `ingested_at` is excluded from an observation's identity.

Usage:
    uv run python -m build.adoption_reconciliation            # over the committed baseline
    uv run python -m build.adoption_reconciliation --json     # same, machine-readable rows
"""

from __future__ import annotations

import argparse
import datetime
import json
from collections.abc import Iterable, Mapping
from pathlib import Path

from build.adoption_measurements import resolve_over_baseline as _measurements_over_baseline

ROOT = Path(__file__).resolve().parents[1]

COLUMNS: tuple[str, ...] = (
    "declaration_version_id",
    "observation_snapshot_id",
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
    measurement_rows: Iterable[Mapping],
    recorded_scores: Mapping[str, Mapping],
    *,
    evaluated_at: datetime.datetime | None = None,
) -> list[dict]:
    """The reconciliation report as a pure function of measurements and recorded scores.

    ``recorded_scores`` is ``load_sources(...)["scores"]`` — slug -> the score document, whose
    ``adoption`` block carries the recorded ``level`` and ``signal_type``.
    """
    rows: list[dict] = []
    for measurement in measurement_rows:
        slug = measurement["product_slug"]
        adoption = (recorded_scores.get(slug) or {}).get("adoption") or {}
        recorded_level = adoption.get("level")
        recorded_instrument = adoption.get("signal_type") or ""
        measured_level = measurement["measured_level"]

        delta = (
            measured_level - recorded_level
            if measured_level is not None and recorded_level is not None
            else None
        )

        if measured_level is None:
            # The route itself abstained (a rule-less multi-artifact aggregation, or a product
            # type with no band set). Nothing to certify, and not an infrastructure absence.
            status = "abstained"
            explanation = (
                f"route {measurement['route_id']} produced no banded level "
                f"(aggregation_method={measurement['aggregation_method']!r}, "
                f"band_set_id={measurement['band_set_id']!r}); the route abstains"
            )
        else:
            # A banded measurement exists, but it is not run-bound (see module doc / §4.3).
            status = "source_unavailable"
            explanation = _UNBOUND_EXPLANATION

        rows.append(
            {
                "declaration_version_id": measurement["declaration_version_id"],
                "observation_snapshot_id": measurement["observation_snapshot_id"],
                "product_slug": slug,
                "category_slug": measurement["category_slug"],
                "route_id": measurement["route_id"],
                "recorded_level": recorded_level,
                "recorded_instrument_type": recorded_instrument,
                "measured_level": measured_level,
                "measured_instrument_type": measurement["instrument_type"],
                "channel": measurement["channel"],
                "raw_value": measurement["raw_value"],
                "measurement_as_of": measurement["measurement_as_of"],
                "route_authority": measurement["route_authority"],
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


def resolve_over_baseline(
    root: Path | None = None,
    allow_dirty: bool = False,
    evaluated_at: datetime.datetime | None = None,
) -> list[dict]:
    """Build the reconciliation report over the immutable baseline, with real identities.

    Reads the measurements this report reconciles from the one measurements builder, so the two
    tables share a single run's declaration_version_id and observation_snapshot_id.
    """
    from build.validate import load_sources

    base = root or ROOT
    measurement_rows = _measurements_over_baseline(base, allow_dirty=allow_dirty)
    recorded_scores = load_sources(base)["scores"]
    return reconcile(measurement_rows, recorded_scores, evaluated_at=evaluated_at)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the reconciliation rows as JSON")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="stamp a diagnostic declaration_version_id over a dirty worktree",
    )
    args = parser.parse_args()

    from build.validate import load_sources

    measurement_rows = _measurements_over_baseline(ROOT, allow_dirty=args.allow_dirty)
    scores = load_sources(ROOT)["scores"]
    rows = reconcile(measurement_rows, scores)

    if args.json:
        print("\n".join(canonical_row(row) for row in rows))
        return 0

    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    measured_slugs = {r["product_slug"] for r in measurement_rows}
    recorded_unmeasured = sum(
        1
        for slug, doc in scores.items()
        if (doc.get("adoption") or {}).get("level") is not None and slug not in measured_slugs
    )
    print(f"reconciliation rows     {len(rows)}")
    for status in sorted(by_status):
        print(f"  {status:<20}{by_status[status]:>5}")
    print(
        f"\nrecorded-but-unmeasured products (not rows in this report, see module doc): "
        f"{recorded_unmeasured}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
