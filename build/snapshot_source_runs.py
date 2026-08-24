"""Snapshot the platform `runs` API for the adoption source datasets into `observations.source_runs`.

This is a SNAPSHOT of platform-retained run history, not a history the repository keeps. The
generator fetches EVERY run the `runs` API still retains for each source dataset -- not merely the
latest run -- and a later snapshot simply REPLACES this one. It is a point-in-time attestation:
the committed receipt records what the platform exposed at `captured_at`, and the content digest
binds that exact row-set, but a digest alone cannot reconstruct rows the platform has since aged
out of its retention window. Read the receipt as "this is what the API held at this instant,"
never as "this is the complete run history for all time."

A current-state table cannot prove that a collector ran (data-architecture.md 4.3) -- rows in
`product_adoption_current` cannot tell a successful run that returned identical values from a
failed collector whose previous table stayed readable, from a source that never ran at all -- and
`observations.source_runs` is the run manifest that makes those states distinguishable.

It READS the control-plane `datasets` and `runs` connections only. It performs NO platform
mutation anywhere -- no create, update or delete -- and `--check` writes nothing to disk either.

Coverage is DERIVED, not hand-listed. The deployed adoption source datasets come from
`sources/signal_routing.yaml`: every `dimensions.adoption` route with a machine source resolves
through the `sources:` block to a `bridged: true` collector dataset, so a route added to the YAML
is covered automatically and none is silently dropped (the omission that let `signal_semanticscholar`
go uncaptured). `signal_packages` is added separately as the STAGED successor -- not deployed yet
(issue #314), so it is recorded as unresolved in the receipt rather than treated as a coverage gap.

Grain: one row per (source_run_id, materialization_id). The run-to-model binding is authoritative
through `steps -> materializations`, NEVER a timestamp: a run that finished near a table's
`createdAt` proves nothing about which run wrote it. Four identifiers are kept DISTINCT and never
conflated:

  - `source_run_id`     the run's own id (run.id)
  - `materialization_id` the Materialization node's own id
  - `table_id`          the materialized model/table id (materialization.tableId)
  - `dataset_id`        the dataset the materialization wrote into (materialization.datasetId)

Two runs from one scheduled fire are two rows (or two groups of rows); runs are NEVER deduplicated
by dataset+time or reduced to a latest-per-fire. A single model may be materialized more than once
in one run, so each materialization is its own row. A run that materialized nothing still emits one
row: execution status only, with the materialization-derived fields null.

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

The per-run CSV is GENERATED, never committed (it is live data). The receipt
(`warehouse/audits/source_runs.json`, mirroring `platform_models.json`) IS committed: it is the
hygiene-clean, point-in-time attestation. It records the snapshot's coverage bounds
(earliest/latest `started_at`), per-dataset run counts, the resolved dataset name->id bindings,
which requested datasets did not resolve, and a deterministic content digest over the emitted rows
sorted canonically and EXCLUDING the volatile `captured_at`, so two snapshots of an identical
run-set digest identically. `validate_rows` gates the row-set and `validate_receipt` gates the
receipt's shape before either is written or trusted.

Environment:
    OSO_API_KEY   required to fetch a live snapshot. When absent, `--check` validates the
                  COMMITTED receipt offline instead of skipping.

Usage:
    uv run python -m build.snapshot_source_runs                 # emit CSV + receipt (needs key)
    uv run python -m build.snapshot_source_runs --check         # validate: live if keyed, else committed
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
import uuid
from datetime import datetime, timezone
from pathlib import Path

from build import assets as A
from build.publish_registry import graphql
from build.serialize_routing import load_routing
from build.vocabulary import is_iso_timestamp, parse_timestamp

ORG = "currentai"
ORG_ID = "ad7f4c1c-dd2f-430e-a831-e7f1f16e6d9e"

# The row/receipt contract version and the digest-canonicalization version. Bumped when the
# columns, the receipt shape, or the way rows are serialized for the digest change, so a stale
# receipt cannot masquerade as current.
SCHEMA_VERSION = 1
CANONICALIZATION_VERSION = 1

# The staged successor to the per-source collectors: a merged package-downloads model that is not
# deployed anywhere yet (issue #314). Kept separate from the derived deployed set so that its
# absence from the platform is recorded as expected, not flagged as a coverage failure.
STAGED_SUCCESSOR_DATASETS: tuple[str, ...] = ("signal_packages",)

# The step name the platform gives each model-evaluation step. `evaluate_model_repo_state`
# names the `repo_state` model; the prefix is stripped to recover the model name. A step whose
# name does not carry the prefix contributes its name unchanged.
_STEP_PREFIX = "evaluate_model_"

# Closed enums, verified against the live platform on 2026-08-24. `trigger_type` and `actor_type`
# are validated against these sets: an unrecognized value is a HARD error, not a silent pass, so
# platform drift forces a conscious widening here rather than slipping through unnoticed.
# `execution_status` is the platform's own status and is validated only as a non-empty uppercase
# token -- it is not ours to normalize, and a new status must not fail a snapshot.
_TRIGGER_TYPES = frozenset({"SCHEDULED", "MANUAL"})
_ACTOR_TYPES = frozenset({"user", "system"})
_STATUS_TOKEN = re.compile(r"^[A-Z][A-Z_]*$")

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

# The five fields a materialization contributes. They are all-present or all-null together: a
# partial materialization row would be a parse defect, so it is rejected rather than emitted.
_MATERIALIZATION_FIELDS: tuple[str, ...] = (
    "materialization_id", "table_id", "model_name", "dataset_id", "materialized_at",
)
# Fields that must always carry a value, on every row.
_REQUIRED_FIELDS: tuple[str, ...] = (
    "source_run_id", "source_dataset_id", "source_dataset_name", "execution_status",
    "trigger_type", "run_type", "actor_type", "captured_at", "expected_scope", "scope_status",
)
_TIMESTAMP_FIELDS: tuple[str, ...] = (
    "queued_at", "started_at", "finished_at", "materialized_at", "captured_at",
)

RECEIPT = A.ROOT / "warehouse" / "audits" / "source_runs.json"
DEFAULT_OUT = A.ROOT / "build" / "observations"

# Both queries are READS. This module issues no mutation of any kind. The nested `steps` and
# `materializations` connections carry `pageInfo` so a truncated default page is DETECTED (and
# raised on) rather than silently dropping steps or materializations.
Q_DATASETS = """query($where: JSON, $first: Int, $after: String){
  datasets(where:$where, first:$first, after:$after){
    pageInfo{ hasNextPage endCursor }
    edges{ node{ id name } }
  } }"""
Q_RUNS = """query($where: JSON, $first: Int, $after: String){
  runs(where:$where, first:$first, after:$after){
    pageInfo{ hasNextPage endCursor }
    edges{ node{
      id triggerType runType status
      queuedAt startedAt finishedAt lastHeartbeatAt
      requestedBy{ id }
      steps{ pageInfo{ hasNextPage } edges{ node{ name displayName status
        materializations{ pageInfo{ hasNextPage } edges{ node{ id tableId datasetId createdAt } } } } } }
    } }
  } }"""


class TruncatedConnection(RuntimeError):
    """A Relay connection could not be paged to exhaustion -- a repeated or missing cursor, or a
    nested page that the query could not exhaust. Raised rather than returning a partial result,
    because a silently truncated snapshot understates run history, which is the exact blindness
    `source_runs` exists to remove."""


# --- coverage derived from the routing YAML --------------------------------------


def _dataset_from_table(table: str | None) -> str | None:
    """`currentai.signal_github.repo_state` -> `signal_github` (the dataset component)."""
    if not table:
        return None
    parts = table.split(".")
    return parts[1] if len(parts) >= 3 else None


def deployed_adoption_source_datasets(routing: dict) -> tuple[str, ...]:
    """The deployed collector datasets behind the adoption routes, derived from the routing YAML.

    Walks `dimensions.adoption.routes`, resolves each machine `source` through the `sources:` block
    to its warehouse table, and keeps the dataset component of every `bridged: true` source. A
    hand-authored route (`source: null`) contributes nothing. Sorted and de-duplicated, so two
    routes on the same dataset (the two Hugging Face routes) yield one entry.
    """
    sources = routing.get("sources") or {}
    routes = (((routing.get("dimensions") or {}).get("adoption") or {}).get("routes")) or []
    datasets: set[str] = set()
    for route in routes:
        source = route.get("source")
        if not source:
            continue
        decl = sources.get(source)
        if not decl or not decl.get("bridged"):
            continue
        name = _dataset_from_table(decl.get("table"))
        if name:
            datasets.add(name)
    return tuple(sorted(datasets))


def source_datasets(routing: dict | None = None) -> tuple[str, ...]:
    """Every dataset the snapshot requests: the derived deployed set plus the staged successor."""
    routing = routing if routing is not None else load_routing(A.ROOT)
    deployed = deployed_adoption_source_datasets(routing)
    staged = tuple(d for d in STAGED_SUCCESSOR_DATASETS if d not in deployed)
    return tuple(sorted(set(deployed) | set(staged)))


# --- parsing the row contract ----------------------------------------------------


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


def _assert_nested_complete(node: dict) -> None:
    """Raise if a run node's steps page, or any step's materializations page, was truncated.

    The default nested page is the safe maximum: the query requests no nested `first`, and if the
    platform ever returns more steps or materializations than one page holds, `hasNextPage` trips
    and this refuses the run rather than emit a run missing some of its materializations.
    """
    run_id = node.get("id")
    steps_conn = node.get("steps") or {}
    if (steps_conn.get("pageInfo") or {}).get("hasNextPage"):
        raise TruncatedConnection(f"run {run_id}: steps connection truncated (more than one page)")
    for step_edge in (steps_conn.get("edges") or []):
        step = step_edge.get("node") or {}
        mats = step.get("materializations") or {}
        if (mats.get("pageInfo") or {}).get("hasNextPage"):
            raise TruncatedConnection(
                f"run {run_id}: materializations of step {step.get('name')!r} truncated")


def parse_run_rows(source_dataset_id: str, source_dataset_name: str, node: dict, captured_at: str) -> list[dict]:
    """Rows for one run node, one per (source_run_id, materialization_id).

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


# --- row validation --------------------------------------------------------------


def validate_rows(rows: list[dict]) -> list[str]:
    """Every row-set invariant, checked BEFORE the digest and the CSV are written.

    A row that violates any of these is a parse or coverage defect, and emitting it would bake the
    defect into a committed digest. The invariants: exact column set; required identifiers present
    and typed; materialization fields all-present-or-all-null; valid timestamps; controlled
    trigger/actor enums; scope constants; a unique (source_run_id, materialization_id) grain; and
    no exact-duplicate rows.
    """
    problems: list[str] = []
    grain: set[tuple] = set()
    exact: set[tuple] = set()
    for i, row in enumerate(rows):
        where = f"row {i} (run {row.get('source_run_id')!r})"
        if set(row) != set(COLUMNS):
            problems.append(f"{where}: column set {sorted(set(row) ^ set(COLUMNS))} does not match contract")
            continue

        for field in _REQUIRED_FIELDS:
            if not (isinstance(row[field], str) and row[field]):
                problems.append(f"{where}: required field {field} is missing or not a non-empty string")

        # Materialization fields are all-present or all-null together.
        present = [f for f in _MATERIALIZATION_FIELDS if row[f] is not None]
        if present and len(present) != len(_MATERIALIZATION_FIELDS):
            missing = [f for f in _MATERIALIZATION_FIELDS if row[f] is None]
            problems.append(f"{where}: partial materialization -- has {present}, missing {missing}")

        for field in _TIMESTAMP_FIELDS:
            if row[field] is not None and not is_iso_timestamp(row[field]):
                problems.append(f"{where}: {field} {row[field]!r} is not an ISO-8601 timestamp")

        if row["trigger_type"] not in _TRIGGER_TYPES:
            problems.append(f"{where}: trigger_type {row['trigger_type']!r} not in {sorted(_TRIGGER_TYPES)}")
        if row["actor_type"] not in _ACTOR_TYPES:
            problems.append(f"{where}: actor_type {row['actor_type']!r} not in {sorted(_ACTOR_TYPES)}")
        if isinstance(row["execution_status"], str) and not _STATUS_TOKEN.match(row["execution_status"]):
            problems.append(f"{where}: execution_status {row['execution_status']!r} is not an uppercase status token")
        if row["expected_scope"] != "unknown" or row["scope_status"] != "unknown":
            problems.append(f"{where}: scope must be unknown (execution status is not scope)")

        key = (row["source_run_id"], row["materialization_id"])
        if key in grain:
            problems.append(f"{where}: duplicate grain (source_run_id, materialization_id)={key}")
        grain.add(key)

        signature = tuple(row[c] for c in COLUMNS)
        if signature in exact:
            problems.append(f"{where}: exact-duplicate row")
        exact.add(signature)
    return problems


# --- digest and receipt ----------------------------------------------------------


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
    deployed_datasets: tuple[str, ...],
    staged_datasets: tuple[str, ...],
    resolved_dataset_ids: dict[str, str],
    per_dataset_run_counts: dict[str, int],
    unresolved_datasets: list[str],
    captured_at: str,
    window: dict | None = None,
) -> dict:
    """The committed-shape receipt: a point-in-time attestation of platform-retained run history.

    Deterministic apart from `captured_at`: the digest excludes it, and the counts, bounds and
    bindings are functions of the run-set alone. Records no actor id, no logsUrl and no raw error
    text -- only normalized coverage, the resolved name->id bindings, and the content digest.
    """
    earliest, latest = _bounds(rows)
    return {
        "snapshot": True,
        "schema_version": SCHEMA_VERSION,
        "canonicalization_version": CANONICALIZATION_VERSION,
        # A point-in-time attestation of what the runs API retained at capture, not a complete or
        # permanent history: the digest binds this row-set but cannot reconstruct aged-out rows.
        "attestation": "point-in-time snapshot of platform-retained run history; not a permanent"
                       " or complete history, and the digest cannot reproduce rows since aged out",
        "captured_at": captured_at,
        "org": ORG,
        "org_id": ORG_ID,
        "requested_datasets": sorted(requested_datasets),
        "deployed_datasets": sorted(deployed_datasets),
        "staged_datasets": sorted(staged_datasets),
        "resolved_datasets": sorted(per_dataset_run_counts),
        "resolved_dataset_ids": dict(sorted(resolved_dataset_ids.items())),
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


def _is_uuid(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def _parse_bound(value):
    """A capture bound: None, or a real ISO-8601 timestamp parsed to a datetime. Returns
    (ok, datetime|None). `ok` is False only for a non-null, non-parseable value. Parsing is
    delegated to `vocabulary.parse_timestamp` so date handling stays in one place."""
    if value is None:
        return True, None
    if not is_iso_timestamp(value):
        return False, None
    return True, parse_timestamp(value)


def validate_receipt(receipt: dict) -> list[str]:
    """Every part of the receipt contract, so a committed or emitted receipt cannot lie by
    omission OR by a value that merely resembles a good one. Shape and internal consistency only;
    a live `--check` is the authoritative comparison against the platform.

    The holes this closes (each previously passed a malformed receipt): a timestamp that matches a
    digit pattern but is not a real date; a negative count; a duplicated requested dataset; a
    dataset that appears in neither the resolved nor the unresolved set; and a resolved dataset with
    no exact name->id binding.
    """
    problems: list[str] = []
    required = (
        "snapshot", "schema_version", "canonicalization_version", "attestation", "captured_at",
        "org", "org_id", "requested_datasets", "deployed_datasets", "staged_datasets",
        "resolved_datasets", "resolved_dataset_ids", "unresolved_datasets",
        "per_dataset_run_counts", "run_count", "row_count", "earliest_started_at",
        "latest_started_at", "window", "expected_scope", "scope_status", "content_digest",
    )
    for key in required:
        if key not in receipt:
            problems.append(f"missing top-level field {key}")
    if problems:
        return problems  # per-field checks below assume the keys exist

    if receipt["snapshot"] is not True:
        problems.append("snapshot must be true -- this artifact makes no history claim")
    if receipt["schema_version"] != SCHEMA_VERSION:
        problems.append(f"schema_version is {receipt['schema_version']!r}, expected {SCHEMA_VERSION}")
    if receipt["canonicalization_version"] != CANONICALIZATION_VERSION:
        problems.append(
            f"canonicalization_version is {receipt['canonicalization_version']!r}, "
            f"expected {CANONICALIZATION_VERSION}")
    if not (isinstance(receipt["attestation"], str) and receipt["attestation"]):
        problems.append("attestation must be a non-empty string")
    if not is_iso_timestamp(receipt["captured_at"]):
        problems.append(f"captured_at {receipt['captured_at']!r} is not an ISO-8601 timestamp")
    if receipt["org"] != ORG:
        problems.append(f"org is {receipt['org']!r}, expected {ORG!r}")
    if receipt["org_id"] != ORG_ID:
        problems.append(f"org_id is {receipt['org_id']!r}, expected {ORG_ID!r}")

    # Every dataset list is a list of strings; requested has no duplicates.
    for key in ("requested_datasets", "deployed_datasets", "staged_datasets",
                "resolved_datasets", "unresolved_datasets"):
        value = receipt[key]
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            problems.append(f"{key} is not a list of strings")
    if isinstance(receipt["requested_datasets"], list):
        req = receipt["requested_datasets"]
        if len(req) != len(set(req)):
            dupes = sorted({x for x in req if req.count(x) > 1})
            problems.append(f"requested_datasets has duplicates: {dupes}")

    # deployed and staged partition requested, disjointly.
    req_set = set(receipt.get("requested_datasets") or [])
    dep_set = set(receipt.get("deployed_datasets") or [])
    stg_set = set(receipt.get("staged_datasets") or [])
    if dep_set & stg_set:
        problems.append(f"datasets both deployed and staged: {sorted(dep_set & stg_set)}")
    if dep_set | stg_set != req_set:
        problems.append("deployed + staged datasets do not partition requested_datasets")

    # resolved and unresolved partition requested, disjointly and completely -- so no requested
    # dataset can go missing from both sets, and none can appear in both.
    res_set = set(receipt.get("resolved_datasets") or [])
    unr_set = set(receipt.get("unresolved_datasets") or [])
    if res_set & unr_set:
        problems.append(f"datasets both resolved and unresolved: {sorted(res_set & unr_set)}")
    if res_set | unr_set != req_set:
        missing = req_set - (res_set | unr_set)
        extra = (res_set | unr_set) - req_set
        problems.append(
            f"resolved + unresolved do not partition requested_datasets"
            f"{f'; unpartitioned {sorted(missing)}' if missing else ''}"
            f"{f'; unexpected {sorted(extra)}' if extra else ''}")

    counts = receipt["per_dataset_run_counts"]
    if not isinstance(counts, dict) or not all(
        isinstance(k, str) and isinstance(v, int) and not isinstance(v, bool) and v >= 0
        for k, v in counts.items()
    ):
        problems.append("per_dataset_run_counts is not a mapping of name -> nonnegative int")
    else:
        if sorted(counts) != sorted(res_set):
            problems.append("resolved_datasets disagrees with per_dataset_run_counts keys")
        if receipt["run_count"] != sum(counts.values()):
            problems.append(f"run_count {receipt['run_count']} != {sum(counts.values())} summed")

    # Exact name->id bindings: one valid UUID per resolved dataset, keys exactly the resolved set.
    ids = receipt["resolved_dataset_ids"]
    if not isinstance(ids, dict):
        problems.append("resolved_dataset_ids is not a mapping")
    else:
        if set(ids) != res_set:
            problems.append("resolved_dataset_ids keys do not match resolved_datasets exactly")
        for name, ds_id in ids.items():
            if not _is_uuid(ds_id):
                problems.append(f"resolved_dataset_ids[{name!r}] = {ds_id!r} is not a UUID")

    for key in ("run_count", "row_count"):
        if not isinstance(receipt[key], int) or isinstance(receipt[key], bool) or receipt[key] < 0:
            problems.append(f"{key} is not a nonnegative int")

    # Capture bounds: real timestamps or null, and ordered. String comparison is not enough --
    # a bound that looks like a date but is not must be rejected.
    lo_ok, lo = _parse_bound(receipt["earliest_started_at"])
    hi_ok, hi = _parse_bound(receipt["latest_started_at"])
    if not lo_ok:
        problems.append(f"earliest_started_at {receipt['earliest_started_at']!r} is not a timestamp or null")
    if not hi_ok:
        problems.append(f"latest_started_at {receipt['latest_started_at']!r} is not a timestamp or null")
    if lo is not None and hi is not None and lo > hi:
        problems.append(f"capture bounds out of order: {receipt['earliest_started_at']} > {receipt['latest_started_at']}")

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


# --- Relay pagination ------------------------------------------------------------


def _connection_pages(query: str, base_vars: dict, connection_key: str, token: str, page_size: int):
    """Yield each page's edges for a Relay connection, paged to exhaustion with cursor guards.

    Stops only when `hasNextPage` is false. A missing `endCursor` while more pages are claimed, or
    a cursor the walk has already used, raises `TruncatedConnection` rather than truncating or
    looping forever -- a truncated snapshot is exactly the failure `source_runs` must not commit.
    """
    after: str | None = None
    seen: set[str] = set()
    while True:
        data = graphql(query, {**base_vars, "first": page_size, "after": after}, token)
        conn = data[connection_key]
        yield conn["edges"]
        page = conn.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            return
        cursor = page.get("endCursor")
        if not cursor:
            raise TruncatedConnection(f"{connection_key}: hasNextPage but endCursor is empty")
        if cursor in seen:
            raise TruncatedConnection(f"{connection_key}: cursor {cursor!r} repeated -- pagination stalled")
        seen.add(cursor)
        after = cursor


def resolve_datasets(names: tuple[str, ...], token: str, page_size: int = 100) -> dict[str, str]:
    """Map each requested source-dataset name to its platform id, skipping unresolved ones.

    Resolves by name against the org's datasets rather than by timestamp or position, paging the
    datasets connection to exhaustion so a dataset on a later page is not missed. A dataset that is
    not deployed (e.g. `signal_packages`) simply does not appear and is recorded as unresolved in
    the receipt. Read-only.
    """
    by_name: dict[str, str] = {}
    for edges in _connection_pages(Q_DATASETS, {"where": {"org_id": {"eq": ORG_ID}}},
                                   "datasets", token, page_size):
        for e in edges:
            by_name[e["node"]["name"]] = e["node"]["id"]
    return {name: by_name[name] for name in names if name in by_name}


def fetch_runs(dataset_id: str, token: str, page_size: int = 100) -> list[dict]:
    """Every run node for one dataset, paging the runs connection to exhaustion.

    Each run node is checked for a truncated nested steps/materializations page before it is kept,
    so a run is never emitted missing some of its materializations. Read-only.
    """
    nodes: list[dict] = []
    for edges in _connection_pages(Q_RUNS, {"where": {"dataset_id": {"eq": dataset_id}}},
                                   "runs", token, page_size):
        for e in edges:
            node = e["node"]
            _assert_nested_complete(node)
            nodes.append(node)
    return nodes


# --- orchestration ---------------------------------------------------------------


def collect(token: str, page_size: int, captured_at: str, routing: dict | None = None):
    """Fetch and parse rows plus coverage for the source datasets. Read-only.

    Returns (rows, deployed, staged, resolved_ids, per_dataset_run_counts, unresolved).
    """
    routing = routing if routing is not None else load_routing(A.ROOT)
    deployed = deployed_adoption_source_datasets(routing)
    staged = tuple(d for d in STAGED_SUCCESSOR_DATASETS if d not in deployed)
    requested = tuple(sorted(set(deployed) | set(staged)))

    resolved = resolve_datasets(requested, token)
    unresolved = [name for name in requested if name not in resolved]
    rows: list[dict] = []
    counts: dict[str, int] = {}
    for name, dataset_id in resolved.items():
        nodes = fetch_runs(dataset_id, token, page_size)
        counts[name] = len(nodes)
        for node in nodes:
            rows.extend(parse_run_rows(dataset_id, name, node, captured_at))
    return rows, deployed, staged, resolved, counts, unresolved


def snapshot(token: str, page_size: int, captured_at: str, routing: dict | None = None) -> tuple[list[dict], dict]:
    """Assemble (rows, receipt), validating the row-set before the receipt (and its digest) is
    built. Raises `ValueError` if the rows violate the contract. Read-only."""
    rows, deployed, staged, resolved, counts, unresolved = collect(token, page_size, captured_at, routing)
    problems = validate_rows(rows)
    if problems:
        raise ValueError("row-set is invalid:\n  - " + "\n  - ".join(problems))
    receipt = build_receipt(
        rows,
        requested_datasets=tuple(sorted(set(deployed) | set(staged))),
        deployed_datasets=deployed,
        staged_datasets=staged,
        resolved_dataset_ids=resolved,
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


def _check_committed_receipt() -> int:
    """Validate the committed receipt offline (no credentials). Fails if it is absent or malformed
    -- it must never exit green after checking nothing."""
    if not RECEIPT.exists():
        print(f"no committed receipt at {RECEIPT.relative_to(A.ROOT)} to validate offline", file=sys.stderr)
        return 1
    try:
        receipt = json.loads(RECEIPT.read_text())
    except json.JSONDecodeError as exc:
        print(f"committed receipt is not valid JSON: {exc}", file=sys.stderr)
        return 1
    problems = validate_receipt(receipt)
    if problems:
        print(f"COMMITTED RECEIPT INVALID ({RECEIPT.relative_to(A.ROOT)}):", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"committed receipt is well-formed: {receipt['run_count']} runs, {receipt['row_count']} rows, "
          f"captured {receipt['captured_at']}, unresolved={receipt['unresolved_datasets']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="validate only, writing nothing: a live snapshot if keyed, else the committed receipt")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="output directory for the generated CSV (default build/observations)")
    ap.add_argument("--page-size", type=int, default=100, help="runs page size")
    args = ap.parse_args(argv)

    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    token = os.environ.get("OSO_API_KEY")

    if args.check and not token:
        # No credentials: validate the COMMITTED receipt offline rather than skip. This is the
        # credential-free gate CI runs, and it must fail on a malformed or missing receipt.
        return _check_committed_receipt()
    if not token:
        print("OSO_API_KEY is required to snapshot the runs API", file=sys.stderr)
        return 2

    rows, deployed, staged, resolved, counts, unresolved = collect(token, args.page_size, captured_at)
    row_problems = validate_rows(rows)
    if row_problems:
        print("ROW-SET INVALID (nothing written):", file=sys.stderr)
        for problem in row_problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    receipt = build_receipt(
        rows,
        requested_datasets=tuple(sorted(set(deployed) | set(staged))),
        deployed_datasets=deployed,
        staged_datasets=staged,
        resolved_dataset_ids=resolved,
        per_dataset_run_counts=counts,
        unresolved_datasets=unresolved,
        captured_at=captured_at,
    )
    receipt_problems = validate_receipt(receipt)
    if receipt_problems:
        print("RECEIPT STRUCTURE INVALID (nothing written):", file=sys.stderr)
        for problem in receipt_problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.check:
        print(f"live snapshot validates: {receipt['run_count']} runs, {receipt['row_count']} rows, "
              f"unresolved={receipt['unresolved_datasets']}")
        return 0

    csv_path = write_rows(rows, args.out)
    write_receipt(receipt)
    print(f"wrote {csv_path.relative_to(A.ROOT)} ({receipt['row_count']} rows) and "
          f"{RECEIPT.relative_to(A.ROOT)} ({receipt['run_count']} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
