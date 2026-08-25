"""Identity of a set of adoption observations — the content digest and the versioned snapshot id.

Two distinct things the release model (data-architecture.md §4.5) names separately, and
`releases.manifest` carries both:

  * ``observation_content_digest`` — a pure SHA-256 of the canonical observation content, "and
    nothing else". This is the raw content address: identical measurements digest identically,
    forever, regardless of the canonicalization rule in force.
  * ``observation_snapshot_id`` — the *identity* that `evaluation.adoption_reconciliation` and
    `releases.manifest` key on, and that binds into `release_id`. It is derived from BOTH the
    ``canonicalization_version`` and the content digest, so a persisted snapshot id names the rule
    that produced it. Without this a caller could store an id and be unable to tell which
    serialization produced it; two rules could even collide on one id.

The earlier revision of this module conflated the two — it exposed only the pure digest under the
name ``observation_snapshot_id`` and left the version unbound. The split here is what §4.5 already
requires.

## What the content digest covers

``observation_content_digest`` is a SHA-256 over the measurement columns only — ``CONTENT_COLUMNS``:
``product_slug``, ``product_type``, ``artifact_kind``, ``artifact_id``, ``channel``,
``metric_type``, ``raw_value``, ``unit``, ``measurement_window_days``, ``observed_at`` — taken as an
order-independent **multiset** (rows serialized, sorted, then hashed). Lineage (``source_run_id``,
``source_record_id``, ``source_dataset``, ``source_table``), capture time (``ingested_at``), the
derived ``observation_id``, ``is_valid``, and ``supersedes_observation_id`` are excluded, so an
unchanged measurement keeps its digest across re-runs; the runs that produced it live in
``observation_run_ids`` beside the id (§4.3), never in it.

## Timestamps are normalized to UTC

``observed_at`` is normalized before hashing: an aware timestamp is converted to UTC; a naive one
is interpreted as UTC (the warehouse emits naive timestamps and the pipeline runs on UTC crons, so
that is their real zone), and it is rendered at fixed microsecond precision with a ``Z`` suffix.
Without this the same instant written ``…+00:00``, ``…-04:00``, or naive would produce three
different digests (§4.5 requires timezone normalization).

## Derived, not stored

Like ``declaration_version_id``, these are run-time computations, not committed receipts — a
full-refresh table's content changes every run, so a frozen value would go stale. Reconciliation
and the release builder compute them over the live ``product_adoption_current`` rows. The tests
exercise them against the one observation set that IS committed and immutable — the Phase-2
baseline parquet — so both digests over it are pinned as fixed contracts.

## The canonicalization ratchet

``CANONICALIZATION_FINGERPRINT`` is the content digest over a fixed in-module fixture: any change to
``CONTENT_COLUMNS`` or the serializer moves it. It is gated two ways — a test asserts it matches the
current serializer, and a merge-base ratchet (``check_canonicalization_ratchet``) fails if the
fingerprint changed against the merge base while ``CANONICALIZATION_VERSION`` did not advance. So a
serialization change cannot land without a version bump, even if someone regenerates the pinned
golden values.

Usage:
    uv run python -m build.observation_snapshot            # digests over the committed baseline
    uv run python -m build.observation_snapshot --json     # same, machine-readable
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_UTC = datetime.timezone.utc

# Bumped when CONTENT_COLUMNS or the serialization changes. Bound INTO observation_snapshot_id (not
# into observation_content_digest), and enforced by the ratchet below.
CANONICALIZATION_VERSION = 1

# The normalized observation content: the measurement itself, and nothing else. Lineage
# (source_run_id / source_record_id / source_dataset / source_table), capture time (ingested_at),
# the derived observation_id, is_valid, and supersedes_observation_id are deliberately excluded.
# Order is fixed: it is the serialization's column order.
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

BASELINE_PARQUET = ROOT / "warehouse/data/observations/product_adoption_baseline.parquet"


def _canonical_timestamp(value: datetime.datetime) -> str:
    """UTC-normalized, fixed-precision, ``Z``-suffixed ISO text.

    Aware timestamps are converted to UTC; naive timestamps are interpreted as UTC (the warehouse
    emits naive UTC). Always six fractional digits, so the same instant has exactly one rendering.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=_UTC)
    value = value.astimezone(_UTC)
    return value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{value.microsecond:06d}Z"


def _canonical_value(value: object) -> object:
    if isinstance(value, datetime.datetime):
        return _canonical_timestamp(value)
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def _canonical_row(row: dict) -> str:
    """One observation's content as a compact JSON array over CONTENT_COLUMNS.

    Timestamps are UTC-normalized; numbers must be finite; every other non-JSON-native type is
    rejected (no permissive ``default``), so an unexpected value fails loudly rather than becoming
    an implementation-dependent string and a non-reproducible digest.
    """
    values = []
    for column in CONTENT_COLUMNS:
        if column not in row:
            raise KeyError(f"observation row is missing content column {column!r}")
        values.append(_canonical_value(row[column]))
    return json.dumps(values, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def observation_content_digest(rows: Iterable[dict]) -> str:
    """The pure content address of a set of observations — §4.5 "content and nothing else".

    SHA-256 over the sorted, newline-joined canonical rows (an order-independent multiset). Does
    NOT depend on the canonicalization version — that binding lives in observation_snapshot_id.
    """
    lines = sorted(_canonical_row(row) for row in rows)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def observation_snapshot_id(rows: Iterable[dict]) -> str:
    """The versioned identity reconciliation and releases key on.

    Binds the canonicalization version to the content digest, so a stored id names the rule that
    produced it and two rules cannot collide on one id.
    """
    return snapshot_id_from_digest(observation_content_digest(rows))


def snapshot_id_from_digest(content_digest: str, version: int | None = None) -> str:
    """Compose a snapshot id from a content digest and the canonicalization version."""
    payload = json.dumps(
        {
            "canonicalization_version": CANONICALIZATION_VERSION if version is None else version,
            "observation_content_digest": content_digest,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --- the canonicalization fingerprint and ratchet --------------------------------

# A fixed fixture exercising the serializer: an aware timestamp, a naive one, a null window, and
# unicode. CANONICALIZATION_FINGERPRINT is its content digest; any CONTENT_COLUMNS or serializer
# change moves it, and the ratchet then requires CANONICALIZATION_VERSION to advance.
_FINGERPRINT_FIXTURE: tuple[dict, ...] = (
    {
        "product_slug": "fixture-a", "product_type": "model", "artifact_kind": "github",
        "artifact_id": "ówner/repo", "channel": "github", "metric_type": "stars",
        "raw_value": 42, "unit": "stars", "measurement_window_days": None,
        "observed_at": datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=_UTC),
    },
    {
        "product_slug": "fixture-b", "product_type": "dataset", "artifact_kind": "huggingface_dataset",
        "artifact_id": "org/set", "channel": "huggingface", "metric_type": "downloads",
        "raw_value": 1000, "unit": "downloads", "measurement_window_days": 30,
        "observed_at": datetime.datetime(2026, 1, 2, 3, 4, 5),  # naive → interpreted UTC
    },
)
CANONICALIZATION_FINGERPRINT = "e2e93998bdcf8fabe99fc2fb6d8e3870bf255785b153ba53138fd15ae578eb5c"


class CanonicalizationRatchetError(RuntimeError):
    """Raised when the canonicalization changed without a version bump."""


def check_canonicalization_ratchet(before: dict | None, now: dict) -> None:
    """Fail if the fingerprint moved against the merge base while the version did not advance.

    ``before`` / ``now`` are ``{"version": int, "fingerprint": str}``; ``before`` is None on the
    introducing PR (the module did not exist at the merge base), which is not a violation.
    """
    if before is None:
        return
    if now["fingerprint"] != before["fingerprint"] and now["version"] <= before["version"]:
        raise CanonicalizationRatchetError(
            "the observation canonicalization changed (CONTENT_COLUMNS or the serializer) but "
            f"CANONICALIZATION_VERSION did not advance ({before['version']} -> {now['version']}). "
            "Bump the version so a snapshot id minted under the old rule cannot be confused with "
            "one minted under the new rule."
        )


def _parse_canonicalization(source: str) -> dict | None:
    """Extract {version, fingerprint} from a copy of this module's source, or None if absent."""
    version = re.search(r"^CANONICALIZATION_VERSION\s*=\s*(\d+)", source, re.M)
    fingerprint = re.search(r'^CANONICALIZATION_FINGERPRINT\s*=\s*"([0-9a-f]{64})"', source, re.M)
    if not version or not fingerprint:
        return None
    return {"version": int(version.group(1)), "fingerprint": fingerprint.group(1)}


def merge_base_canonicalization(base: str = "origin/main") -> dict | None:
    """This module's {version, fingerprint} as of the merge base, or None if it did not exist."""
    rel = "build/observation_snapshot.py"
    try:
        merge_base = subprocess.run(
            ["git", "-C", str(ROOT), "merge-base", "HEAD", base],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        source = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{merge_base}:{rel}"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return _parse_canonicalization(source)


def rows_from_parquet(path: Path | None = None) -> list[dict]:
    import pyarrow.parquet as pq

    return pq.read_table(path or BASELINE_PARQUET).to_pylist()


def resolve_baseline() -> dict:
    rows = rows_from_parquet(BASELINE_PARQUET)
    digest = observation_content_digest(rows)
    return {
        "canonicalization_version": CANONICALIZATION_VERSION,
        "row_count": len(rows),
        "observation_content_digest": digest,
        "observation_snapshot_id": snapshot_id_from_digest(digest),
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
    print(f"canonicalization_version   {info['canonicalization_version']}")
    print(f"row_count                  {info['row_count']}")
    print(f"observation_content_digest {info['observation_content_digest']}")
    print(f"observation_snapshot_id    {info['observation_snapshot_id']}")
    print(f"computed_over              {info['computed_over']}")
    print(
        "\n(Computed over the committed Phase-2 baseline. At reconciliation/release time the same\n"
        "functions run over the live observations.product_adoption_current rows.)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
