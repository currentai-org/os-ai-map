"""Snapshot the platform `runs` API for the source datasets into `observations.source_runs`.

This is a SNAPSHOT, not a history. It captures the CURRENT-RUN execution status of the source
collectors at `captured_at` and retains nothing: it makes no trend or history claim, and a later
snapshot simply replaces this one. A current-state table cannot prove that a collector ran
(data-architecture.md 4.3) -- rows in `product_adoption_current` cannot tell a successful run
that returned identical values from a failed collector whose previous table stayed readable, from
a source that never ran at all -- and `observations.source_runs` is the run manifest that makes
those states distinguishable.

It READS the control-plane `datasets` and `runs` connections only. It performs NO platform
mutation anywhere -- no create, update or delete -- and `--check` reads the same way and writes
nothing to disk either.

Grain: one row per (source_run_id, materialized model/table). The run-to-model binding is
authoritative through `steps -> materializations`, NEVER a timestamp: a run that finished near a
table's `createdAt` proves nothing about which run wrote it. Four identifiers are kept DISTINCT
and never conflated:

  - `source_run_id`     the run's own id (run.id)
  - `materialization_id` the Materialization node's own id
  - `table_id`          the materialized model/table id (materialization.tableId)
  - `dataset_id`        the dataset the materialization wrote into (materialization.datasetId)

Two runs from one scheduled fire are two rows (or two groups of rows); runs are NEVER deduplicated
by dataset+time or reduced to a latest-per-fire. A run that materialized nothing still emits one
row: execution status only, with the four materialization-derived fields null.

Execution is not scope. `execution_status` is the platform's real run status
(SUCCESS/FAILED/RUNNING/...). A platform `SUCCESS` means the run's steps executed without error;
it does NOT mean the collection was complete -- the platform exposes no expected-scope field and
no row-level run id in the fetcher tables, so completeness is not derivable here. Every row
therefore carries `expected_scope = "unknown"` and `scope_status = "unknown"` as constants, and
downstream reconciliation must not read a platform `SUCCESS` as evidence that collection was
complete.

Output hygiene. No raw actor, log or error text is ever stored. `requestedBy` is reduced to
`actor_type` (`user` when an actor is present, else `system`) -- never the id. `logsUrl` and log
contents are not fetched. `error_class` carries only a normalized error-type token when the
platform exposes one and is null otherwise; raw error messages are never stored.

The emitted CSV and the receipt are GENERATED, never committed: they are live data. The receipt
(`warehouse/audits/source_runs.json`, mirroring `platform_models.json`) records the snapshot's
coverage bounds -- earliest/latest `started_at`, per-dataset run counts, which requested datasets
did not resolve -- and a deterministic content digest over the emitted rows sorted canonically and
EXCLUDING the volatile `captured_at`, so two snapshots of an identical run-set digest identically.
`validate_receipt` guards the receipt's shape the way the platform-models audit guards its own.

Environment:
    OSO_API_KEY   required to fetch (emit, or `--check` a live snapshot); absent, `--check`
                  skips the live query and exits 0.

Usage:
    uv run python -m build.snapshot_source_runs                 # emit CSV + receipt
    uv run python -m build.snapshot_source_runs --check         # fetch, validate, emit nothing
    uv run python -m build.snapshot_source_runs --out build/observations
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from build import assets as A
from build.publish_registry import graphql

ORG = "currentai"
ORG_ID = "ad7f4c1c-dd2f-430e-a831-e7f1f16e6d9e"

# The source datasets whose collector runs this snapshot covers. `signal_packages` is not
# deployed yet (issue #314); an unresolved name is recorded in the receipt's coverage, not
# treated as an error.
SOURCE_DATASETS: tuple[str, ...] = (
    "signal_github",
    "signal_huggingface",
    "signal_pypi",
    "signal_packages",
)

# The step name the platform gives each model-evaluation step. `evaluate_model_repo_state`
# names the `repo_state` model; the prefix is stripped to recover the model name. A step whose
# name does not carry the prefix contributes its name unchanged.
_STEP_PREFIX = "evaluate_model_"

# The row contract (data-architecture.md 4.3, narrowed to what the `runs` API exposes). The four
# identifiers are separate columns and are never merged. `captured_at` is last and is EXCLUDED
# from the content digest -- it is the one volatile field.
COLUMNS: tuple[str, ...] = (
    "source_run_id",         # run.id
    "source_dataset_id",     # the dataset whose runs connection was queried
    "source_dataset_name",   # its name (signal_github, ...)
    "materialization_id",    # the Materialization node's own id (nullable)
    "table_id",              # materialization.tableId -- the materialized model/table (nullable)
    "model_name",            # parsed from the owning step name (nullable)
    "dataset_id",            # materialization.datasetId -- where the materialization wrote (nullable)
    "execution_status",      # run.status: SUCCESS | FAILED | RUNNING | ...
    "trigger_type",          # run.triggerType
    "run_type",              # run.runType
    "actor_type",            # user | system, from requestedBy presence -- never the id
    "queued_at",
    "started_at",
    "finished_at",
    "materialized_at",       # materialization.createdAt (nullable)
    "error_class",           # normalized error-type token, nullable -- never raw error text
    "expected_scope",        # constant "unknown"
    "scope_status",          # constant "unknown"
    "captured_at",           # snapshot time -- EXCLUDED from the digest
)
_DIGEST_COLUMNS: tuple[str, ...] = tuple(c for c in COLUMNS if c != "captured_at")

RECEIPT = A.ROOT / "warehouse" / "audits" / "source_runs.json"
DEFAULT_OUT = A.ROOT / "build" / "observations"

# Both queries are READS. This module issues no mutation of any kind.
Q_DATASETS = """query($where: JSON){ datasets(where:$where){ edges{ node{ id name } } } }"""
Q_RUNS = """query($where: JSON, $first: Int, $after: String){
  runs(where:$where, first:$first, after:$after){
    pageInfo{ hasNextPage endCursor }
    edges{ node{
      id triggerType runType status
      queuedAt startedAt finishedAt lastHeartbeatAt
      requestedBy{ id }
      steps{ edges{ node{ name displayName status
        materializations{ edges{ node{ id tableId datasetId createdAt } } } } } }
    } }
  } }"""


def model_name_from_step(step_name: str | None, display_name: str | None) -> str | None:
    """The model name a materialization step binds to, from the step name.

    `evaluate_model_repo_state` -> `repo_state`. The step name is the primary source; the
    display name is a fallback for a step that omits the machine name. Neither is a timestamp:
    the binding is structural, from the step that owns the materialization.
    """
    for candidate in (step_name, display_name):
        if candidate:
            return candidate[len(_STEP_PREFIX):] if candidate.startswith(_STEP_PREFIX) else candidate
    return None


def actor_type(node: dict) -> str:
    """`user` when a `requestedBy` actor is present, else `system`. The raw id is never stored."""
    return "user" if (node.get("requestedBy") or {}).get("id") else "system"


def _materializations(node: dict) -> list[tuple[dict, dict]]:
    """(step, materialization) pairs across every step of a run node."""
    pairs: list[tuple[dict, dict]] = []
    for step_edge in ((node.get("steps") or {}).get("edges") or []):
        step = step_edge.get("node") or {}
        for mat_edge in ((step.get("materializations") or {}).get("edges") or []):
            pairs.append((step, mat_edge.get("node") or {}))
    return pairs


def parse_run_rows(source_dataset_id: str, source_dataset_name: str, node: dict, captured_at: str) -> list[dict]:
    """Rows for one run node, one per (source_run_id, materialized model/table).

    The run->model binding is `materialization.tableId` (the model/table id) plus the owning
    step's name (the model name) -- authoritative, and never a timestamp. Every run.id is its own
    row (or rows); this never dedupes by dataset+time. A run that materialized nothing still emits
    a single row: execution status only, with the materialization-derived fields null.
    """
    base = {
        "source_run_id": node.get("id"),
        "source_dataset_id": source_dataset_id,
        "source_dataset_name": source_dataset_name,
        "execution_status": node.get("status"),
        "trigger_type": node.get("triggerType"),
        "run_type": node.get("runType"),
        "actor_type": actor_type(node),
        "queued_at": node.get("queuedAt"),
        "started_at": node.get("startedAt"),
        "finished_at": node.get("finishedAt"),
        # The established run/step schema exposes no error token, so no raw error text can leak;
        # error_class stays null until the platform surfaces a normalized error-type token.
        "error_class": None,
        # Execution is not scope: the platform exposes neither an expected scope nor a row-level
        # run id, so completeness is unknown by construction, not by omission.
        "expected_scope": "unknown",
        "scope_status": "unknown",
        "captured_at": captured_at,
    }
    pairs = _materializations(node)
    if not pairs:
        return [{
            **base, "materialization_id": None, "table_id": None,
            "model_name": None, "dataset_id": None, "materialized_at": None,
        }]
    rows = []
    for step, mat in pairs:
        rows.append({
            **base,
            "materialization_id": mat.get("id"),
            "table_id": mat.get("tableId"),
            "model_name": model_name_from_step(step.get("name"), step.get("displayName")),
            "dataset_id": mat.get("datasetId"),
            "materialized_at": mat.get("createdAt"),
        })
    return rows


def resolve_datasets(names: tuple[str, ...], token: str) -> dict[str, str]:
    """Map each requested source-dataset name to its platform id, skipping unresolved ones.

    Resolves by name against the org's datasets rather than by timestamp or position, so a
    dataset that is not deployed (e.g. `signal_packages`) simply does not appear in the map and
    is recorded as unresolved in the receipt's coverage. Read-only.
    """
    data = graphql(Q_DATASETS, {"where": {"org_id": {"eq": ORG_ID}}}, token)
    by_name = {e["node"]["name"]: e["node"]["id"] for e in data["datasets"]["edges"]}
    return {name: by_name[name] for name in names if name in by_name}


def fetch_runs(dataset_id: str, token: str, page_size: int = 100) -> list[dict]:
    """Every run node for one dataset, paging the Relay connection to exhaustion.

    Pages via `pageInfo.hasNextPage`/`endCursor` and never stops early: a truncated snapshot
    would silently understate a dataset's run history, which is exactly the blindness
    `source_runs` exists to remove. Read-only.
    """
    nodes: list[dict] = []
    after: str | None = None
    while True:
        data = graphql(
            Q_RUNS,
            {"where": {"dataset_id": {"eq": dataset_id}}, "first": page_size, "after": after},
            token,
        )
        conn = data["runs"]
        nodes.extend(e["node"] for e in conn["edges"])
        page = conn["pageInfo"]
        if not page.get("hasNextPage"):
            return nodes
        after = page["endCursor"]


def content_digest(rows: list[dict]) -> str:
    """A sha256 over the emitted rows, canonicalized and EXCLUDING `captured_at`.

    Order-independent (rows are serialized then sorted) and time-independent (the snapshot's
    wall-clock capture time is dropped), so an identical run-set digests identically no matter
    when or in what order it was fetched.
    """
    serialized = sorted(
        json.dumps({c: row.get(c) for c in _DIGEST_COLUMNS}, sort_keys=True, default=str)
        for row in rows
    )
    return hashlib.sha256("\n".join(serialized).encode("utf-8")).hexdigest()


def _bounds(rows: list[dict]) -> tuple[str | None, str | None]:
    started = sorted(r["started_at"] for r in rows if r.get("started_at"))
    if not started:
        return None, None
    return started[0], started[-1]


def build_receipt(
    rows: list[dict],
    *,
    requested_datasets: tuple[str, ...],
    per_dataset_run_counts: dict[str, int],
    unresolved_datasets: list[str],
    captured_at: str,
    window: dict | None = None,
) -> dict:
    """The committed-shape receipt: a snapshot's coverage bounds, per-dataset counts, and digest.

    Deterministic apart from `captured_at`: the digest excludes it, and the counts and bounds are
    functions of the run-set alone. Records no actor id, no logsUrl and no raw error text.
    """
    earliest, latest = _bounds(rows)
    return {
        "snapshot": True,
        "captured_at": captured_at,
        "org": ORG,
        "org_id": ORG_ID,
        "requested_datasets": list(requested_datasets),
        "resolved_datasets": sorted(per_dataset_run_counts),
        "unresolved_datasets": sorted(unresolved_datasets),
        "per_dataset_run_counts": dict(sorted(per_dataset_run_counts.items())),
        "run_count": sum(per_dataset_run_counts.values()),
        "row_count": len(rows),
        "earliest_started_at": earliest,
        "latest_started_at": latest,
        # A snapshot bounds nothing by default -- every dataset is paged to exhaustion. If a
        # bound is ever introduced it must be explicit here, not silent truncation.
        "window": window or {"bounded": False, "strategy": "full pagination to exhaustion"},
        # Execution status is real; scope is unknown for the whole snapshot, recorded so the
        # separation cannot be lost downstream.
        "expected_scope": "unknown",
        "scope_status": "unknown",
        "content_digest": content_digest(rows),
    }


_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")


def validate_receipt(receipt: dict) -> list[str]:
    """Every part of the receipt contract, so a committed or emitted receipt cannot lie by
    omission. Shape only; a live `--check` is the authoritative comparison against the platform.

    The failures the tests pin: missing capture bounds, a malformed content digest, and a receipt
    that does not record scope as unknown -- each caught here, not left to pass by resembling a
    good receipt.
    """
    problems: list[str] = []
    required = (
        "snapshot", "captured_at", "org", "org_id", "requested_datasets", "resolved_datasets",
        "unresolved_datasets", "per_dataset_run_counts", "run_count", "row_count",
        "earliest_started_at", "latest_started_at", "window", "expected_scope",
        "scope_status", "content_digest",
    )
    for key in required:
        if key not in receipt:
            problems.append(f"missing top-level field {key}")
    if problems:
        return problems  # per-field checks below assume the keys exist

    if receipt["snapshot"] is not True:
        problems.append("snapshot must be true -- this artifact makes no history claim")
    if not _ISO.match(str(receipt["captured_at"])):
        problems.append(f"captured_at {receipt['captured_at']!r} is not an ISO-8601 timestamp")
    if receipt["org"] != ORG:
        problems.append(f"org is {receipt['org']!r}, expected {ORG!r}")
    if receipt["org_id"] != ORG_ID:
        problems.append(f"org_id is {receipt['org_id']!r}, expected {ORG_ID!r}")

    counts = receipt["per_dataset_run_counts"]
    if not isinstance(counts, dict) or not all(
        isinstance(k, str) and isinstance(v, int) and not isinstance(v, bool) for k, v in counts.items()
    ):
        problems.append("per_dataset_run_counts is not a mapping of name -> int")
    else:
        if sorted(counts) != sorted(receipt["resolved_datasets"]):
            problems.append("resolved_datasets disagrees with per_dataset_run_counts keys")
        if receipt["run_count"] != sum(counts.values()):
            problems.append(f"run_count {receipt['run_count']} != {sum(counts.values())} summed")

    for key in ("requested_datasets", "resolved_datasets", "unresolved_datasets"):
        if not isinstance(receipt[key], list) or not all(isinstance(x, str) for x in receipt[key]):
            problems.append(f"{key} is not a list of strings")
    if isinstance(receipt.get("unresolved_datasets"), list) and isinstance(receipt.get("resolved_datasets"), list):
        overlap = set(receipt["unresolved_datasets"]) & set(receipt["resolved_datasets"])
        if overlap:
            problems.append(f"datasets both resolved and unresolved: {sorted(overlap)}")

    if not isinstance(receipt["row_count"], int) or isinstance(receipt["row_count"], bool):
        problems.append("row_count is not an int")

    # Capture bounds must be present (keys already checked) and be a string or null. Two non-null
    # bounds must be ordered.
    lo, hi = receipt["earliest_started_at"], receipt["latest_started_at"]
    for key, value in (("earliest_started_at", lo), ("latest_started_at", hi)):
        if not (value is None or isinstance(value, str)):
            problems.append(f"{key} is neither a string nor null")
    if isinstance(lo, str) and isinstance(hi, str) and lo > hi:
        problems.append(f"capture bounds out of order: {lo} > {hi}")

    window = receipt["window"]
    if not isinstance(window, dict) or "bounded" not in window:
        problems.append("window is not a mapping declaring `bounded`")
    elif window.get("bounded") and not (window.get("from") or window.get("to") or window.get("bound")):
        problems.append("window is bounded but records no explicit bound")

    if not _HEX64.match(str(receipt["content_digest"])):
        problems.append("content_digest is not a 64-hex sha256")

    # Execution is not scope: the receipt must record both scope fields as unknown.
    for key in ("expected_scope", "scope_status"):
        if receipt[key] != "unknown":
            problems.append(f"{key} is {receipt[key]!r}, expected 'unknown' (scope is not derivable)")
    return problems


def snapshot(token: str, page_size: int, captured_at: str) -> tuple[list[dict], dict]:
    """Fetch, parse and assemble (rows, receipt) for the source datasets. Read-only."""
    resolved = resolve_datasets(SOURCE_DATASETS, token)
    unresolved = [name for name in SOURCE_DATASETS if name not in resolved]
    rows: list[dict] = []
    counts: dict[str, int] = {}
    for name, dataset_id in resolved.items():
        nodes = fetch_runs(dataset_id, token, page_size)
        counts[name] = len(nodes)
        for node in nodes:
            rows.extend(parse_run_rows(dataset_id, name, node, captured_at))
    receipt = build_receipt(
        rows,
        requested_datasets=SOURCE_DATASETS,
        per_dataset_run_counts=counts,
        unresolved_datasets=unresolved,
        captured_at=captured_at,
    )
    return rows, receipt


def write_rows(rows: list[dict], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "source_runs.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["source_run_id"] or "", r.get("table_id") or "",
                                               r.get("materialization_id") or "")):
            writer.writerow(row)
    return path


def write_receipt(receipt: dict) -> None:
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=1, sort_keys=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="fetch (read-only) and validate the receipt structure, writing nothing")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="output directory for the generated CSV (default build/observations)")
    ap.add_argument("--page-size", type=int, default=100, help="runs page size")
    args = ap.parse_args(argv)

    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    token = os.environ.get("OSO_API_KEY")

    if args.check and not token:
        # No credentials: the live query is guarded, and there is no committed receipt to
        # validate offline, so this is a graceful skip rather than a failure.
        print("OSO_API_KEY absent; --check skips the live query (nothing to validate offline)")
        return 0
    if not token:
        print("OSO_API_KEY is required to snapshot the runs API", file=sys.stderr)
        return 2

    rows, receipt = snapshot(token, args.page_size, captured_at)
    problems = validate_receipt(receipt)
    if problems:
        print("RECEIPT STRUCTURE INVALID:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.check:
        print(f"receipt is well-formed: {receipt['run_count']} runs, {receipt['row_count']} rows, "
              f"unresolved={receipt['unresolved_datasets']}")
        return 0

    csv_path = write_rows(rows, args.out)
    write_receipt(receipt)
    print(f"wrote {csv_path.relative_to(A.ROOT)} ({receipt['row_count']} rows) and "
          f"{RECEIPT.relative_to(A.ROOT)} ({receipt['run_count']} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
