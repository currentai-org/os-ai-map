"""Serialize the two adoption evaluation tables to publishable static-model CSVs.

The release-candidate publisher for `evaluation.product_adoption_measurements` and
`evaluation.adoption_reconciliation`. It reads `observations.product_adoption_current` ONCE — the
committed baseline by default, or the deployed table under `--live` — and derives from that single
set of rows both the `observation_snapshot_id` and both evaluation tables, so the snapshot id and
the tables it stamps are one atomic set that cannot straddle a refresh. The `declaration_version_id`
is derived from the working tree at `HEAD` and refused over a dirty worktree without `--allow-dirty`.

Output is two CSVs under `build/evaluation/` (created if absent), one row per table row, with
`contributing_observation_ids` joined by `|` and timestamps in ISO-8601. These are the artifacts a
maintainer uploads as the `currentai.evaluation.*` static models; see
`docs/operations/deploy-evaluation.md`. Nothing here writes to the platform — publishing is the
maintainer step.

A `--live` read is additionally run inside a materialization bracket (`build.read_binding`), and
the verdict lands in `build/evaluation/read_binding.json` beside the CSVs: `bound` proves which
materialization (and so which run) of `product_adoption_current` served the rows the snapshot id
was minted over; `unstable` or `unavailable` records that it could not be proven, claiming
nothing. The receipt is provenance for the read only — it does not enter either table's columns,
does not move `observation_snapshot_id`, and does not bind the underlying fetcher runs (#355).
The baseline path reads frozen bytes, so no receipt is written there.

Usage:
    uv run python -m build.serialize_evaluation                 # baseline -> build/evaluation/*.csv
    uv run python -m build.serialize_evaluation --live          # deployed current table
    uv run python -m build.serialize_evaluation --check         # build in memory, write nothing
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from build import adoption_measurements as M
from build import adoption_reconciliation as R

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "evaluation"
_UTC = datetime.timezone.utc


def build_tables(
    observation_rows: Sequence[Mapping],
    root: Path | None = None,
    allow_dirty: bool = False,
    evaluated_at: datetime.datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    """(measurements, reconciliation) from one observation read, sharing one identity pair."""
    from build.declaration_version import resolve as resolve_declaration
    from build.observation_snapshot import observation_snapshot_id
    from build.validate import load_sources

    base = root or ROOT
    tables, band_rows, category_of, declared, recorded = M.load_inputs(base)
    dvid = resolve_declaration(base, allow_dirty=allow_dirty)["declaration_version_id"]
    osid = observation_snapshot_id(observation_rows)
    measurements = M.measurements(
        observation_rows, tables, band_rows, category_of, declared, recorded,
        declaration_version_id=dvid, observation_snapshot_id=osid,
    )
    reconciliation = R.reconcile(
        load_sources(base)["scores"], measurements, tables, category_of, declared,
        declaration_version_id=dvid, observation_snapshot_id=osid, evaluated_at=evaluated_at,
    )
    return measurements, reconciliation


def read_live_bound() -> tuple[list[dict], dict]:
    """The deployed current table, read inside a materialization bracket where possible.

    A control-plane failure degrades the BINDING, never the read: the rows still load (unbracketed)
    and the receipt records `unavailable` with the reason. The bracket is provenance, not a gate —
    refusing to serialize because a lookup failed would block a deploy on a blip while proving
    nothing about the rows.
    """
    from build.read_binding import bound_read

    try:
        result = bound_read(M.load_current_observations)
    except Exception as exc:  # noqa: BLE001 — any binding failure degrades to `unavailable`, by design
        return M.load_current_observations(), {
            "binding_status": "unavailable",
            "model": "observations.product_adoption_current",
            "reason": str(exc),
        }
    return result.rows, result.binding


def write_binding_receipt(binding: Mapping, observation_rows: Sequence[Mapping], path: Path) -> None:
    """The read-binding verdict plus the identity of the rows it is a verdict about."""
    from build.observation_snapshot import observation_snapshot_id

    receipt = {
        "observation_snapshot_id": observation_snapshot_id(observation_rows),
        "row_count": len(observation_rows),
        **binding,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _flat(row: Mapping, columns: Sequence[str]) -> dict:
    out: dict[str, object] = {}
    for key in columns:
        value = row.get(key)
        if key == "contributing_observation_ids" and isinstance(value, (list, tuple)):
            value = "|".join(value)
        elif isinstance(value, datetime.datetime):
            value = value.isoformat()
        out[key] = value
    return out


def write_csv(rows: Sequence[Mapping], columns: Sequence[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow(_flat(row, columns))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="read the deployed current table via pyoso")
    parser.add_argument("--check", action="store_true", help="build in memory, write nothing")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="stamp a diagnostic declaration_version_id over a dirty worktree")
    args = parser.parse_args()

    binding: dict | None = None
    if args.live:
        observation_rows, binding = read_live_bound()
    else:
        from build.observation_snapshot import rows_from_parquet

        observation_rows = rows_from_parquet()

    measurements, reconciliation = build_tables(
        observation_rows, allow_dirty=args.allow_dirty, evaluated_at=datetime.datetime.now(_UTC)
    )
    print(f"product_adoption_measurements  {len(measurements)} rows")
    print(f"adoption_reconciliation        {len(reconciliation)} rows")
    if binding is not None:
        print(f"read binding                   {binding['binding_status']}")
    if args.check:
        print("\ncheck only: nothing written")
        return 0

    write_csv(measurements, M.COLUMNS, OUT_DIR / "product_adoption_measurements.csv")
    write_csv(reconciliation, R.COLUMNS, OUT_DIR / "adoption_reconciliation.csv")
    print(f"\nwrote {OUT_DIR}/product_adoption_measurements.csv and adoption_reconciliation.csv")
    if binding is not None:
        write_binding_receipt(binding, observation_rows, OUT_DIR / "read_binding.json")
        print(f"wrote {OUT_DIR}/read_binding.json ({binding['binding_status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
