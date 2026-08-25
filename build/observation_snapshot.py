"""Identity of a set of adoption observations — the content digest and the versioned snapshot id.

Two distinct things the release model (data-architecture.md §4.5) names separately, and
`releases.manifest` carries both:

  * ``observation_content_digest`` — a pure SHA-256 of the canonical observation content, "and
    nothing else". Identical measurements digest identically, forever, regardless of the
    canonicalization rule in force. Version-independent.
  * ``observation_snapshot_id`` — the *identity* that `evaluation.adoption_reconciliation` and
    `releases.manifest` key on, and that binds into `release_id`. It is a domain-separated hash of
    the ``canonicalization_version`` and the content digest, so a persisted snapshot id names the
    rule that produced it; two rules cannot collide on one id.

## What the content digest covers

``observation_content_digest`` is a SHA-256 over the measurement columns only — ``CONTENT_COLUMNS``:
``product_slug``, ``product_type``, ``artifact_kind``, ``artifact_id``, ``channel``,
``metric_type``, ``raw_value``, ``unit``, ``measurement_window_days``, ``observed_at`` — taken as an
order-independent **multiset** (rows serialized, sorted, then hashed). Lineage, capture time
(``ingested_at``), the derived ``observation_id``, ``is_valid``, and ``supersedes_observation_id``
are excluded; the runs that produced the observations live in ``observation_run_ids`` beside the id
(§4.3), never in it.

## Strict per-column typing

Every value is checked before serialization. ``observed_at`` must be an actual ``datetime`` — a
string or other lookalike is rejected, never passed through (a string would bypass UTC
normalization and produce a non-reproducible digest). Aware timestamps are converted to UTC; naive
ones are interpreted as UTC (the warehouse emits naive UTC), rendered at fixed microsecond
precision with a ``Z`` suffix. Every other column must be a JSON scalar (``str``/``bool``/``int``/
finite ``float``/``None``); anything else raises.

## The snapshot-id preimage (domain-separated, exact bytes)

``observation_snapshot_id`` = ``SHA-256`` of the UTF-8 bytes:

    "os-ai-map:observation-snapshot:v" + str(CANONICALIZATION_VERSION) + "\\0" + content_digest

where ``content_digest`` is the 64-character lowercase-hex ``observation_content_digest``. The
domain label separates this hash from any other SHA-256 in the system; the ``v<N>`` binds the
version; the NUL byte unambiguously delimits the version prefix from the digest. This is a fixed,
documented preimage, not an underspecified concatenation.

## The canonicalization ratchet

``CANONICALIZATION_FINGERPRINT`` is the digest of an explicit contract *descriptor*
(``CANONICALIZATION_CONTRACT``) — the columns, ordering, allowed types, timestamp rule, null/number
encoding, serialization format, and hash. Fingerprinting the descriptor rather than one sample's
output means a declared-rule change is caught even where no fixture exercises it. A merge-base
ratchet (``check_canonicalization_ratchet``) fails if the descriptor changed against the merge base
while ``CANONICALIZATION_VERSION`` did not advance. Implementation *conformance* to the contract is
tested separately (behavioral fixtures and the baseline goldens), so a serializer that drifts from
its declared contract also fails.

## Derived, not stored

Like ``declaration_version_id``, these are run-time computations over the live
``product_adoption_current`` rows; the tests exercise them against the committed, immutable Phase-2
baseline, whose two digests are pinned as fixed contracts.

Usage:
    uv run python -m build.observation_snapshot            # digests over the committed baseline
    uv run python -m build.observation_snapshot --json     # same, machine-readable
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_UTC = datetime.timezone.utc

# Bumped when CONTENT_COLUMNS or the serialization changes. Bound INTO observation_snapshot_id (not
# into observation_content_digest), and enforced by the ratchet below.
CANONICALIZATION_VERSION = 1

# The measurement content: the measurement itself, and nothing else. Order is fixed — it is the
# serialization's column order.
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

# Columns that MUST be a datetime and are UTC-normalized. A string or other lookalike is rejected.
TIMESTAMP_COLUMNS: frozenset[str] = frozenset({"observed_at"})

# Exact scalar types allowed in a non-timestamp content column, by identity (bool listed apart from
# int: both are wanted and serialize to distinct JSON tokens).
_ALLOWED_SCALARS = (str, bool, int, float)

BASELINE_PARQUET = ROOT / "warehouse/data/observations/product_adoption_baseline.parquet"

_SNAPSHOT_DOMAIN = "os-ai-map:observation-snapshot"


def _canonical_timestamp(value: datetime.datetime) -> str:
    """UTC-normalized, fixed-precision, ``Z``-suffixed ISO text (six fractional digits)."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=_UTC)
    value = value.astimezone(_UTC)
    return value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{value.microsecond:06d}Z"


def _canonical_row(row: dict) -> str:
    """One observation's content as a compact JSON array over CONTENT_COLUMNS, strictly typed."""
    values = []
    for column in CONTENT_COLUMNS:
        if column not in row:
            raise KeyError(f"observation row is missing content column {column!r}")
        value = row[column]
        if column in TIMESTAMP_COLUMNS:
            if not isinstance(value, datetime.datetime):
                raise TypeError(
                    f"{column} must be a datetime, got {type(value).__name__!r} "
                    f"({value!r}); a string or other lookalike would bypass UTC normalization"
                )
            values.append(_canonical_timestamp(value))
            continue
        if value is None:
            values.append(None)
        elif type(value) in _ALLOWED_SCALARS:
            if type(value) is float and not math.isfinite(value):
                raise ValueError(f"non-finite number in column {column!r}: {value!r}")
            values.append(value)
        else:
            raise TypeError(
                f"unsupported type {type(value).__name__!r} in content column {column!r}"
            )
    return json.dumps(values, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def observation_content_digest(rows: Iterable[dict]) -> str:
    """The pure content address of a set of observations — §4.5 "content and nothing else"."""
    lines = sorted(_canonical_row(row) for row in rows)
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def snapshot_id_from_digest(content_digest: str, version: int | None = None) -> str:
    """The versioned, domain-separated snapshot id for a content digest (exact bytes in module doc)."""
    v = CANONICALIZATION_VERSION if version is None else version
    preimage = f"{_SNAPSHOT_DOMAIN}:v{v}\0{content_digest}".encode("utf-8")
    return hashlib.sha256(preimage).hexdigest()


def observation_snapshot_id(rows: Iterable[dict]) -> str:
    """The versioned identity reconciliation and releases key on."""
    return snapshot_id_from_digest(observation_content_digest(rows))


# --- the canonicalization contract, its fingerprint, and the ratchet -------------

# The explicit, declared canonicalization contract. The fingerprint is over THIS descriptor, so a
# change to any declared rule — a new column, a changed type rule, the timestamp format — moves the
# fingerprint whether or not a fixture happens to exercise it. Implementation conformance to the
# contract is tested separately.
CANONICALIZATION_CONTRACT: dict = {
    "version": CANONICALIZATION_VERSION,
    "content_columns": list(CONTENT_COLUMNS),
    "timestamp_columns": sorted(TIMESTAMP_COLUMNS),
    "row_ordering": "sorted-multiset-of-per-row-compact-json-arrays-newline-joined",
    "serialization": "json-compact-array;separators=(',',':');utf-8;ensure_ascii=false",
    "allowed_nontimestamp_scalars": ["str", "bool", "int", "finite-float", "NoneType"],
    "timestamp_rule": "datetime-required;to-utc;naive-interpreted-utc;"
    "strftime=%Y-%m-%dT%H:%M:%S.<6-digit-microseconds>Z",
    "null_encoding": "json-null",
    "number_rule": "finite-only;NaN-and-Infinity-rejected",
    "hash": "sha256-lowercase-hex",
    "snapshot_id_preimage": "sha256('os-ai-map:observation-snapshot:v'+version+'\\0'+content_digest)",
}


def canonicalization_fingerprint() -> str:
    """SHA-256 over the canonical serialization of the contract descriptor."""
    payload = json.dumps(CANONICALIZATION_CONTRACT, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


CANONICALIZATION_FINGERPRINT = "cfe7fe9c1cdb30f72f079a2fe0b6437a82c8580ddec3ee2c09d70b08a2a91c86"


class CanonicalizationRatchetError(RuntimeError):
    """Raised when the canonicalization contract changed without a version bump."""


def check_canonicalization_ratchet(before: dict | None, now: dict) -> None:
    """Fail if the contract fingerprint moved against the merge base while the version did not.

    ``before`` / ``now`` are ``{"version": int, "fingerprint": str}``; ``before`` is None on the
    introducing PR (the module did not exist at the merge base), which is not a violation.
    """
    if before is None:
        return
    if now["fingerprint"] != before["fingerprint"] and now["version"] <= before["version"]:
        raise CanonicalizationRatchetError(
            "the observation canonicalization contract changed but CANONICALIZATION_VERSION did "
            f"not advance ({before['version']} -> {now['version']}). Bump the version so a "
            "snapshot id minted under the old rule cannot be confused with one under the new rule."
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
