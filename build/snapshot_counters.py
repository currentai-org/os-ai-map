"""Capture lifetime adoption counters weekly, so a monthly figure can be taken as an increment.

GitHub release asset downloads and Docker Hub pulls are LIFETIME totals with no time window, so
neither can be banded on a monthly scale as it stands. A project that peaked years ago keeps its
millions. What can be banded is the increase over a recent window, and that needs the counter's
value at more than one point in time. The platform's models are full refreshes and keep no
history, so until it supports incremental models this module keeps the history here: one row per
counter per platform refresh, appended to `sources/snapshots/asset_counters.csv` by the weekly
adoption-reconciliation workflow. It is an interim, and it retires when the platform can hold the
series itself (#664).

What is captured:

- `github_release`: `eligible_asset_downloads` and `eligible_asset_count` from
  `currentai.signal_github.artifact_state`, for every repo whose release read succeeded. Eligible
  means the assets that deliver the product itself: checksums, signatures, SBOMs, manifests and
  notes are excluded upstream.
- `docker`: `pull_count_lifetime` from `currentai.signal_packages.package_metadata`, for every
  declared image whose read succeeded.

A row is keyed on (source, product_slug, artifact_id, observed_at), where `observed_at` is the
platform's fetch time, so rerunning inside a week adds nothing and a missed week shows as a gap
rather than a repeated value. A reading already recorded with DIFFERENT values is an error, never
silently kept or replaced. The grain is the product: a repository several products declare appears
once per product, so whatever computes an increment must not sum those rows as separate use.
Nothing here computes a band or an increment; the counters are raw.

`.github/workflows/asset-counters.yml` runs this daily, on its own, so a failure elsewhere can
never cost a week: the capture is idempotent, one success per platform refresh is enough, and a
reading the platform has already overwritten cannot be recovered afterwards.

Usage:
    uv run python -m build.snapshot_counters --live     # read the warehouse and append new rows
    uv run python -m build.snapshot_counters --check    # validate the committed history
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "sources" / "snapshots" / "asset_counters.csv"
COLUMNS = ["source", "product_slug", "artifact_id", "observed_at", "counter", "asset_count", "captured_on"]
SOURCES = ("github_release", "docker")
KEY = ("source", "product_slug", "artifact_id", "observed_at")

GITHUB_SQL = (
    "SELECT product_slug, repo AS artifact_id, "
    "CAST(fetched_at AS VARCHAR) AS observed_at, "
    "eligible_asset_downloads AS counter, eligible_asset_count AS asset_count "
    "FROM currentai.signal_github.artifact_state "
    "WHERE releases_http_status = 200 AND eligible_asset_downloads IS NOT NULL "
    # A walk stopped at the page cap is a floor, not a total, and an increment between two
    # floors measures the cap rather than use.
    "AND NOT COALESCE(release_pages_truncated, false)"
)
DOCKER_SQL = (
    "SELECT product_slug, package AS artifact_id, "
    "CAST(fetched_at AS VARCHAR) AS observed_at, "
    "pull_count_lifetime AS counter, CAST(NULL AS BIGINT) AS asset_count "
    "FROM currentai.signal_packages.package_metadata "
    "WHERE artifact_kind = 'docker' AND http_status = 200 AND pull_count_lifetime IS NOT NULL"
)


class ConflictingReading(ValueError):
    """The same platform reading, recorded twice with different values."""


def read_history(path: Path = HISTORY) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _normalize(source: str, row: dict, captured_on: str) -> dict:
    # Both collectors write fetched_at as naive UTC at whole seconds, so the first 19 characters
    # are the whole value; Trino renders it with a ".000" suffix that carries nothing.
    observed = str(row["observed_at"]).replace("T", " ")[:19]
    asset_count = row.get("asset_count")
    return {
        "source": source,
        "product_slug": str(row["product_slug"]),
        "artifact_id": str(row["artifact_id"]),
        "observed_at": observed,
        "counter": str(int(row["counter"])),
        "asset_count": "" if asset_count in (None, "") else str(int(asset_count)),
        "captured_on": captured_on,
    }


def merge(history: list[dict], fresh: dict[str, list[dict]], captured_on: str) -> tuple[list[dict], int]:
    """History plus every fresh row whose key is not already present. Returns (rows, added).

    Pure, so the tests can drive it. Sorted by key so the file diffs cleanly week to week.
    """
    known = {tuple(r[k] for k in KEY): r for r in history}
    rows = list(history)
    added = 0
    for source, source_rows in fresh.items():
        for raw in source_rows:
            row = _normalize(source, raw, captured_on)
            key = tuple(row[k] for k in KEY)
            existing = known.get(key)
            if existing is not None:
                if (existing["counter"], existing["asset_count"]) != (row["counter"], row["asset_count"]):
                    raise ConflictingReading(
                        f"{key} is already recorded as counter={existing['counter']} "
                        f"asset_count={existing['asset_count']!r}, and now reads "
                        f"counter={row['counter']} asset_count={row['asset_count']!r}"
                    )
                continue
            known[key] = row
            rows.append(row)
            added += 1
    rows.sort(key=lambda r: tuple(r[k] for k in KEY))
    return rows, added


def problems(rows: list[dict]) -> list[str]:
    """Structural checks on the committed history. A counter going DOWN is not a problem here:
    it is a real observation (an asset deleted or replaced), and whoever computes an increment
    must void that window rather than this file hiding it."""
    out: list[str] = []
    seen: set[tuple] = set()
    for i, row in enumerate(rows, start=2):
        if list(row.keys()) != COLUMNS:
            out.append(f"line {i}: columns {list(row.keys())} are not {COLUMNS}")
            continue
        if row["source"] not in SOURCES:
            out.append(f"line {i}: unknown source {row['source']!r}")
        key = tuple(row[k] for k in KEY)
        if key in seen:
            out.append(f"line {i}: duplicate key {key}")
        seen.add(key)
        try:
            if int(row["counter"]) < 0:
                out.append(f"line {i}: negative counter")
            datetime.fromisoformat(row["observed_at"])
            datetime.fromisoformat(row["captured_on"])
        except ValueError as exc:
            out.append(f"line {i}: {exc}")
    return out


def write_history(rows: list[dict], path: Path = HISTORY) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="read the warehouse and append new rows")
    parser.add_argument("--check", action="store_true", help="validate the committed history")
    args = parser.parse_args()
    if args.live == args.check:
        parser.error("pass exactly one of --live and --check")

    history = read_history()
    if args.check:
        found = problems(history)
        for line in found:
            print(f"  x {line}")
        print(f"{len(history)} counter rows, {len(found)} problem(s)")
        return 1 if found else 0

    from build.warehouse import query

    fresh = {"github_release": query(GITHUB_SQL), "docker": query(DOCKER_SQL)}
    captured_on = datetime.now(timezone.utc).date().isoformat()
    try:
        rows, added = merge(history, fresh, captured_on)
    except ConflictingReading as exc:
        print(f"  x {exc}", file=sys.stderr)
        return 1
    found = problems(rows)
    if found:
        for line in found:
            print(f"  x {line}", file=sys.stderr)
        return 1
    write_history(rows)
    by_source = {s: len(v) for s, v in fresh.items()}
    print(f"read {by_source}; appended {added} new row(s); history now {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
