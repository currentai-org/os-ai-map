"""Derive the ``observation_snapshot_id`` — the identity of a set of adoption observations.

One of the three release identities (data-architecture.md §4.5). Where ``declaration_version_id``
answers "which declarations", this answers "which measurements": it is the content address of the
normalized adoption observations that a reconciliation adjudicated a declaration against. It is
what ``evaluation.adoption_reconciliation`` and ``releases.manifest`` key on alongside the
declaration version.

## Content alone — §4.5, strictly

``observation_snapshot_id`` is "a canonical digest of the normalized observation content, and
nothing else" (§4.5). Two materializations with identical measurements share an id; a re-run that
changes nothing measured keeps the id (§4.3). Two consequences follow, and both are enforced here:

  * **Run identifiers are lineage, not inputs.** ``source_run_id`` and the ``observation_run_ids``
    a snapshot was produced by are recorded *beside* the id, never folded into it (§4.3) —
    otherwise every re-run would mint a new snapshot even when the measurements were identical,
    which is the opposite of what the id is for.
  * **Capture time and provenance are excluded.** ``ingested_at`` (when the row was written),
    ``source_dataset`` / ``source_table`` (which physical table it sat in), ``source_record_id``,
    the derived ``observation_id`` (a hash of the grain, redundant), ``is_valid`` (a constant on
    the valid current-state slice), and ``supersedes_observation_id`` (history, absent pre-2B) are
    all excluded. What remains — ``CONTENT_COLUMNS`` — is the measurement itself.

The digest is over the observations as a **multiset**: the serialized rows are sorted before
hashing, so the id does not depend on the order the rows were materialized or read in.

## Canonicalization version is recorded beside the id, not inside it

§4.7 requires a canonicalization version so the rule can change without silently changing every
digest. But §4.5 says the id is content "and nothing else" — folding the version into the digest
bytes would break that. The two are reconciled by recording ``CANONICALIZATION_VERSION`` alongside
the id (in the reconciliation row / manifest that carries it), never in the hashed input. A rule
change is therefore a visible, declared version bump; the id itself stays a pure content address.
This is the deliberate difference from ``declaration_version_id``, an opaque composite whose
version *is* folded in.

## Derived, not stored

Like ``declaration_version_id``, this is a computation the release builder and reconciliation call
at run time over the live ``observations.product_adoption_current``; it is not a committed receipt.
A full-refresh table's snapshot id must track current content, and a frozen value would go stale
on every run. The tests exercise it against the one observation set that IS committed and
immutable — the Phase-2 baseline parquet — which is why a golden value over the baseline is
pinned: those bytes are ratchet-locked, so the digest over them is a fixed contract.

Usage:
    uv run python -m build.observation_snapshot            # id over the committed baseline
    uv run python -m build.observation_snapshot --json     # same, machine-readable
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Bumped when CONTENT_COLUMNS or the serialization changes, so a value computed under an older
# rule is known not to be comparable. Recorded BESIDE the id by callers, never folded into it.
CANONICALIZATION_VERSION = 1

# The normalized observation content: the measurement itself, and nothing else. Lineage
# (source_run_id / source_record_id / source_dataset / source_table), capture time (ingested_at),
# the derived observation_id, is_valid, and supersedes_observation_id are deliberately excluded —
# see the module docstring. Order is fixed: it is the serialization's column order.
CONTENT_COLUMNS: tuple[str, ...] = (
    "product_slug",
    "product_type",
    "artifact_kind",
    "artifact_id",
    "channel",
    "metric_type",
    "raw_value",
    "unit",
    "measurement_window_days",
    "observed_at",
)

# The committed, immutable observation set the tests and CLI resolve against when no live rows are
# supplied. Its digest is pinned in tests/test_observation_snapshot.py.
BASELINE_PARQUET = ROOT / "warehouse/data/observations/product_adoption_baseline.parquet"


def _canonical_row(row: dict) -> str:
    """One observation's content as a compact JSON array over CONTENT_COLUMNS.

    Dates render as ISO-8601 text; numbers must be finite; every other non-JSON-native type is
    rejected (no permissive ``default``), so an unexpected value fails loudly rather than becoming
    an implementation-dependent string and a non-reproducible id.
    """
    values = []
    for column in CONTENT_COLUMNS:
        if column not in row:
            raise KeyError(f"observation row is missing content column {column!r}")
        value = row[column]
        if isinstance(value, (datetime.date, datetime.datetime)):
            value = value.isoformat()
        values.append(value)
    return json.dumps(values, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def observation_snapshot_id(rows: Iterable[dict]) -> str:
    """The content address of a set of normalized observations.

    A SHA-256 over the sorted, newline-joined canonical rows — a multiset digest, independent of
    row order and of everything outside CONTENT_COLUMNS.
    """
    lines = sorted(_canonical_row(row) for row in rows)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def rows_from_parquet(path: Path | None = None) -> list[dict]:
    """Load observation rows from a parquet file (the baseline, or any frozen snapshot)."""
    import pyarrow.parquet as pq

    return pq.read_table(path or BASELINE_PARQUET).to_pylist()


def resolve_baseline() -> dict:
    """Compute the snapshot id over the committed baseline, with the version recorded beside it."""
    rows = rows_from_parquet(BASELINE_PARQUET)
    return {
        "canonicalization_version": CANONICALIZATION_VERSION,
        "row_count": len(rows),
        "observation_snapshot_id": observation_snapshot_id(rows),
        "computed_over": "warehouse/data/observations/product_adoption_baseline.parquet",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the result as JSON")
    args = parser.parse_args()

    info = resolve_baseline()
    if args.json:
        print(json.dumps(info, indent=2))
        return 0
    print(f"canonicalization_version  {info['canonicalization_version']}")
    print(f"row_count                 {info['row_count']}")
    print(f"observation_snapshot_id   {info['observation_snapshot_id']}")
    print(f"computed_over             {info['computed_over']}")
    print(
        "\n(Computed over the committed Phase-2 baseline. At reconciliation/release time the same\n"
        "function runs over the live observations.product_adoption_current rows.)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
