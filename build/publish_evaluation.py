"""Publish the serialized adoption evaluation CSVs to OSO as static models.

The maintainer half of the evaluation release path. `build/serialize_evaluation.py` writes the two
CSVs (`product_adoption_measurements`, `adoption_reconciliation`) from one atomic read of
`observations.product_adoption_current`; this validates and uploads them as `currentai.evaluation.*`
static models. It reuses the exact GraphQL mechanics of `build/publish_registry.py` — the `graphql`
helper, `resolve_static_models`, `upload`, `data_rows` — so the two publishers cannot drift.

## Validation before any mutation

Before touching the platform (and in `--plan` / `--dry-run`), the candidate CSVs are validated:
their headers must equal `adoption_measurements.COLUMNS` / `adoption_reconciliation.COLUMNS`
exactly; both tables must be non-empty; the three identity columns (`declaration_version_id`,
`observation_snapshot_id`, `routing_policy_version`) must be constant within each file and equal
across both; each table's grain must be unique; and reconciliation must cover exactly the recorded
adoption assessments (with measurements a subset). A candidate that fails any check is never
uploaded. Arbitrary CSVs — a stray `x,y` header, a truncated file, a mismatched snapshot — are
rejected here rather than published.

## No writes before the dry-run returns

`--plan` (offline, no credentials) and `--dry-run` (read-only id resolution) validate and print the
plan and perform NO mutation and NO local write. The only filesystem write this tool makes is the
immutable deployment archive, and only after a real, successful upload.

## Rollback is by BYTES — an immutable archive of what was deployed

A static-model publication REPLACES the table in place; the platform exposes no prior-revision list,
and `observations.product_adoption_current` may have changed since, so regenerating from an old
commit does not reproduce a previous table. So after a successful deployment this tool archives the
exact bytes it uploaded, plus a completed receipt (row counts, column schema, SHA-256), under an
immutable per-deployment directory `build/evaluation/deployments/<deployment_id>/` — keyed on the
declaration and observation identities. It REFUSES to overwrite an existing archive (a deployment id
is written once). To roll back a later bad deployment, re-run this tool pointed at the PRIOR
deployment archive; before deploying, the tool prints that prior archive as the rollback target.
The candidate CSVs under `build/evaluation/` are never the rollback record — only a completed
deployment archive is.

Environment:
    OSO_API_KEY   required (except for --plan)
    OSO_ORG_ID    required (except for --plan)
    OSO_DATASET   optional, defaults to "evaluation"

Usage:
    uv run python -m build.serialize_evaluation --live      # write build/evaluation/*.csv first
    uv run python -m build.publish_evaluation --plan        # offline: validate + plan, no creds, no network
    uv run python -m build.publish_evaluation --dry-run     # read-only id resolution, no mutation, no write
    uv run python -m build.publish_evaluation               # validate, publish, archive
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from build.adoption_measurements import COLUMNS as MEASUREMENTS_COLUMNS
from build.adoption_reconciliation import COLUMNS as RECONCILIATION_COLUMNS
from build.publish_registry import (
    M_DATASET,
    M_RUN,
    M_URL,
    Q_DATASETS,
    data_rows,
    graphql,
    resolve_static_models,
    upload,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "evaluation"
DEFAULT_DATASET = "evaluation"


def deployments_dir(out_dir: Path) -> Path:
    """Where completed, immutable deployment archives live — beside the candidate CSVs."""
    return out_dir / "deployments"

# table -> (csv basename, expected header columns). The header is exactly the builder's COLUMNS.
EVAL_TABLES: tuple[str, ...] = ("product_adoption_measurements", "adoption_reconciliation")
EXPECTED_HEADERS: dict[str, list[str]] = {
    "product_adoption_measurements": list(MEASUREMENTS_COLUMNS),
    "adoption_reconciliation": list(RECONCILIATION_COLUMNS),
}
_IDENTITY_COLUMNS = ("declaration_version_id", "observation_snapshot_id", "routing_policy_version")
# The grain each table is unique on.
_GRAIN = ("declaration_version_id", "observation_snapshot_id", "product_slug", "category_slug", "route_id")


def csv_provenance(path: Path) -> dict:
    """Row count, column schema, and SHA-256 of a CSV — the bytes a rollback must be able to name.

    ``all_null_columns`` records the declared columns that are empty in EVERY row. The loader
    infers a table schema from records, so it cannot type — and therefore drops — a column that
    carries no value anywhere; recording them here lets the deployment check tell that expected
    absence apart from a column that went missing with data in it.
    """
    raw = path.read_bytes()
    header = path.read_text(encoding="utf-8").splitlines()[0] if raw else ""
    columns, rows = _read_rows(path) if raw else ([], [])
    return {
        "rows": data_rows(path),
        "columns": header.split(",") if header else [],
        "all_null_columns": sorted(
            c for c in columns if all((row.get(c) or "") == "" for row in rows)
        ) if rows else [],
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def build_receipt(out_dir: Path = OUT_DIR) -> dict:
    """The provenance of every evaluation CSV present — the candidate description."""
    return {
        table: csv_provenance(out_dir / f"{table}.csv")
        for table in EVAL_TABLES
        if (out_dir / f"{table}.csv").exists()
    }


def _read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def validate_candidates(out_dir: Path = OUT_DIR, root: Path = ROOT) -> list[str]:
    """Every check that must pass before a byte is uploaded. Returns a list of problems (empty = ok).

    Run in --plan and --dry-run as well as a real publish: a candidate that fails here is never
    published, and the failure is the same whether or not credentials are present.
    """
    from build.validate import load_sources

    errors: list[str] = []
    parsed: dict[str, tuple[list[str], list[dict]]] = {}
    for table in EVAL_TABLES:
        path = out_dir / f"{table}.csv"
        if not path.exists():
            errors.append(f"{table}.csv is missing")
            continue
        header, rows = _read_rows(path)
        parsed[table] = (header, rows)
        if header != EXPECTED_HEADERS[table]:
            errors.append(
                f"{table}.csv header does not match {table}.COLUMNS "
                f"(got {header[:3]}… expected {EXPECTED_HEADERS[table][:3]}…)"
            )
        if not rows:
            errors.append(f"{table}.csv is empty (a static model cannot materialize zero rows)")
    # The cross-checks below index by the real column names, so they run only once every file is
    # present with the exact expected header; a schema error is reported on its own.
    if errors or len(parsed) != len(EVAL_TABLES):
        return errors

    # Identity columns constant within each file and equal across both.
    identities: dict[str, dict[str, set]] = {}
    for table, (_header, rows) in parsed.items():
        identities[table] = {col: {r.get(col) for r in rows} for col in _IDENTITY_COLUMNS}
        for col in _IDENTITY_COLUMNS:
            if len(identities[table][col]) != 1:
                errors.append(f"{table}.csv has inconsistent {col}: {sorted(identities[table][col])[:3]}")
    for col in _IDENTITY_COLUMNS:
        values = {next(iter(identities[t][col])) for t in EVAL_TABLES if len(identities[t][col]) == 1}
        if len(values) > 1:
            errors.append(f"{col} differs between the two files: {sorted(values)}")

    # Grain uniqueness per table.
    for table, (_header, rows) in parsed.items():
        keys = [tuple(r.get(c) for c in _GRAIN) for r in rows]
        if len(keys) != len(set(keys)):
            errors.append(f"{table}.csv is not unique on its grain {_GRAIN}")

    # Coverage: reconciliation covers exactly the recorded adoption assessments; measured ⊆ recorded.
    scores = load_sources(root)["scores"]
    recorded = {s for s, doc in scores.items() if isinstance(doc.get("adoption"), dict)}
    recon_products = {r["product_slug"] for r in parsed["adoption_reconciliation"][1]}
    meas_products = {r["product_slug"] for r in parsed["product_adoption_measurements"][1]}
    if recon_products != recorded:
        errors.append(
            f"adoption_reconciliation does not cover the recorded assessments exactly: "
            f"missing {sorted(recorded - recon_products)[:3]}, extra {sorted(recon_products - recorded)[:3]}"
        )
    if not meas_products <= recon_products:
        errors.append(f"measured products not a subset of reconciled: {sorted(meas_products - recon_products)[:3]}")
    return errors


def deployment_id(out_dir: Path = OUT_DIR) -> str:
    """A stable, immutable id for the candidate: the declaration and observation identities it
    carries. Two publishes of the same declaration + observations share an id (and cannot both be
    archived — a deployment is recorded once)."""
    _header, rows = _read_rows(out_dir / "adoption_reconciliation.csv")
    dvid = rows[0]["declaration_version_id"]
    osid = rows[0]["observation_snapshot_id"]
    return f"{dvid[:12]}-{osid[:12]}"


def archive_deployment(out_dir: Path, receipt: dict) -> Path:
    """Copy the just-deployed CSVs + completed receipt into an immutable per-deployment directory.

    Refuses to overwrite an existing archive: a deployment id is written exactly once, so the record
    of what was live cannot be clobbered by a later (possibly failed) publish.
    """
    target = deployments_dir(out_dir) / deployment_id(out_dir)
    if target.exists():
        raise RuntimeError(
            f"deployment archive {target} already exists — a deployment id is immutable and is "
            f"never overwritten. If you are re-publishing identical bytes, the previous archive "
            f"already records them; if not, the identities would have changed."
        )
    target.mkdir(parents=True)
    for table in EVAL_TABLES:
        shutil.copy2(out_dir / f"{table}.csv", target / f"{table}.csv")
    (target / "receipt.json").write_text(
        json.dumps({"deployment_id": target.name, "tables": receipt}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return target


def latest_archive(out_dir: Path) -> Path | None:
    """The most recently written deployment archive, if any — the rollback target for the next deploy."""
    root = deployments_dir(out_dir)
    if not root.exists():
        return None
    archives = [p for p in root.iterdir() if p.is_dir() and (p / "receipt.json").exists()]
    return max(archives, key=lambda p: p.stat().st_mtime) if archives else None


# A run request is only ACCEPTED synchronously; materialization happens asynchronously, so the
# archive is gated on the run reaching terminal SUCCESS and the deployed data matching, not on the
# request being accepted. `runs(where:{id})` is the same read snapshot_source_runs.py uses.
Q_RUN = """query($where: JSON){ runs(where:$where){ edges{ node{ id status } } } }"""
RUN_SUCCESS = "SUCCESS"
RUN_TERMINAL = frozenset({"SUCCESS", "FAILED", "CANCELED", "CANCELLED", "ERROR", "TIMEOUT", "ABORTED"})


def run_status(run_id: str, token: str) -> str | None:
    """The current status of a run, or None if the platform does not know the id yet."""
    edges = graphql(Q_RUN, {"where": {"id": {"eq": run_id}}}, token)["runs"]["edges"]
    return edges[0]["node"]["status"] if edges else None


def poll_run(run_id: str, token: str, timeout: float = 1800.0, interval: float = 15.0) -> str:
    """Block until the run reaches a terminal state or the timeout elapses; return the last status.

    A non-terminal status at timeout is returned as-is (e.g. RUNNING/QUEUED), which the caller
    treats as not-SUCCESS — so a queued or hung run never certifies a deployment.
    """
    import time

    deadline = time.time() + timeout
    status = run_status(run_id, token)
    while status not in RUN_TERMINAL:
        if time.time() >= deadline:
            return status or "UNKNOWN"
        time.sleep(interval)
        status = run_status(run_id, token)
    return status


def deployed_table_state(dataset: str, table: str, timeout: float = 300.0,
                        interval: float = 15.0) -> dict:
    """Row count and column set of a deployed table, read via pyoso — the materialized reality.

    A just-loaded table is not immediately visible in the query catalog: the verification SELECT
    fired the instant a run reported SUCCESS raises `TablesNotFound` (observed on the first
    publish, 2026-08-25). That is propagation lag, not a failed load, so the read is retried until
    `timeout`; a table still missing at the deadline raises and the deployment is not archived.

    `_dlt_*` columns are the loader's own bookkeeping, present on every loaded table and in no
    candidate. They are excluded so the schema comparison is against the declared columns only.
    """
    import time

    from build.warehouse import query

    deadline = time.time() + timeout
    while True:
        try:
            rows = query(f"SELECT * FROM currentai.{dataset}.{table}")
            break
        except Exception as exc:
            if "TablesNotFound" not in str(exc) or time.time() >= deadline:
                raise
            time.sleep(interval)
    columns = [c for c in (rows[0].keys() if rows else []) if not c.startswith("_dlt_")]
    return {"rows": len(rows), "columns": sorted(columns)}


def runs_all_succeeded(statuses: dict[str, tuple[str, str]]) -> list[str]:
    """Problems if any run did not reach terminal SUCCESS. `statuses` is table -> (run_id, status)."""
    return [
        f"{table}: run {run_id} ended {status!r}, not SUCCESS"
        for table, (run_id, status) in statuses.items()
        if status != RUN_SUCCESS
    ]


def deployment_mismatches(expected: dict, deployed: dict) -> list[str]:
    """Problems if the deployed row count or column set does not match the validated candidate.

    Row counts must match exactly. On columns, the deployed table must carry every candidate column
    that holds a value somewhere, and must carry NO column the candidate does not declare. The one
    permitted absence is a candidate column that is null in every row: the loader types columns from
    records and drops one it never sees a value for, so its absence is the loader's schema inference
    and not lost data (`adoption_reconciliation.override_id` today, with no overrides recorded yet).
    A column with data that fails to arrive is still a mismatch, and so is an unexpected extra.
    """
    problems: list[str] = []
    for table in EVAL_TABLES:
        exp, got = expected[table], deployed[table]
        if got["rows"] != exp["rows"]:
            problems.append(f"{table}: deployed {got['rows']} rows, candidate had {exp['rows']}")
        permitted_absent = set(exp.get("all_null_columns") or ())
        missing = set(exp["columns"]) - set(got["columns"]) - permitted_absent
        extra = set(got["columns"]) - set(exp["columns"])
        if missing:
            problems.append(
                f"{table}: deployed table is missing candidate columns with data: {sorted(missing)}"
            )
        if extra:
            problems.append(f"{table}: deployed table has undeclared columns: {sorted(extra)}")
    return problems


def print_plan(receipt: dict, dataset_name: str) -> None:
    print(f"dataset {dataset_name} (currentai.{dataset_name}.*)")
    for table in EVAL_TABLES:
        entry = receipt.get(table)
        if entry is None:
            print(f"  MISSING {table}.csv — run build.serialize_evaluation first")
        else:
            print(f"  {table}.csv  {entry['rows']:,} rows  sha256 {entry['sha256'][:12]}…")


def resolve_evaluation_dataset(name: str, org_id: str, token: str, create: bool) -> str | None:
    """The evaluation dataset's id, created when absent (and `create`)."""
    found = graphql(Q_DATASETS, {"where": {"org_id": {"eq": org_id}, "name": {"eq": name}}}, token)
    edges = found["datasets"]["edges"]
    if edges:
        return edges[0]["node"]["id"]
    if not create:
        return None
    created = graphql(
        M_DATASET,
        {"input": {
            "orgId": org_id, "name": name, "displayName": "Evaluation", "type": "STATIC_MODEL",
            "description": (
                "os-ai-map evaluation candidates: the product-level adoption rollup and the "
                "report-first reconciliation against recorded scores, keyed on declaration_version_id "
                "+ observation_snapshot_id and carrying routing_policy_version. Built by the "
                "repo-side release builders; see docs/operations/deploy-evaluation.md."
            ),
        }},
        token,
    )
    return created["createDataset"]["dataset"]["id"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="validate + print the plan; no network, no creds, no write")
    parser.add_argument("--dry-run", action="store_true", help="validate + resolve ids read-only; no mutation, no write")
    parser.add_argument("--dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    dataset_name = os.environ.get("OSO_DATASET", DEFAULT_DATASET)
    missing = [t for t in EVAL_TABLES if not (args.dir / f"{t}.csv").exists()]
    if missing:
        print(f"missing CSVs: {missing}. Run `uv run python -m build.serialize_evaluation --live` first.",
              file=sys.stderr)
        return 2

    receipt = build_receipt(args.dir)
    print_plan(receipt, dataset_name)

    # Validate BEFORE any mutation — and in --plan / --dry-run too.
    problems = validate_candidates(args.dir, ROOT)
    if problems:
        print("candidate validation failed:", file=sys.stderr)
        for problem in problems:
            print(f"  ! {problem}", file=sys.stderr)
        return 2

    if args.plan:
        return 0

    token = os.environ.get("OSO_API_KEY")
    org_id = os.environ.get("OSO_ORG_ID")
    if not token or not org_id:
        print("OSO_API_KEY and OSO_ORG_ID must both be set (use --plan for an offline plan)",
              file=sys.stderr)
        return 2

    rollback_target = latest_archive(args.dir)
    if rollback_target is not None:
        print(f"rollback target if this deploy is bad: {rollback_target}")

    dataset_id = resolve_evaluation_dataset(dataset_name, org_id, token, create=not args.dry_run)
    if dataset_id is None:
        print(f"would create dataset {dataset_name}, then create + upload {list(EVAL_TABLES)}")
        return 0  # dry-run only reaches here; no write

    models = resolve_static_models(dataset_id, org_id, token, EVAL_TABLES, create=not args.dry_run)
    print(f"dataset {dataset_name} = {dataset_id}")

    if args.dry_run:
        for table in EVAL_TABLES:
            model_id = models[table][0]
            verb = "would upload" if model_id else "would create + upload"
            print(f"  {verb} {table}.csv ({receipt[table]['rows']:,} rows) -> {model_id}")
        return 0  # NO write on a dry run

    for table in EVAL_TABLES:
        path = args.dir / f"{table}.csv"
        model_id = models[table][0]
        url = graphql(M_URL, {"staticModelId": model_id}, token)["createStaticModelUploadUrl"]
        upload(path, url)
        print(f"  uploaded {table}.csv ({path.stat().st_size:,} bytes, {receipt[table]['rows']:,} rows)")

    # ONE RUN REQUEST PER MODEL, awaited in turn. The request is addressed to a dataset with an
    # explicit model selection (`datasetId` + `selectedModels`) — there is no per-static-model
    # input, so a `{staticModelId}` payload is rejected outright and nothing materializes. But a
    # request naming N models FANS OUT INTO N RUNS and returns only ONE of them, which breaks this
    # publisher's contract in two ways at once, both observed on the first publish (2026-08-25):
    #
    #   * The returned run cannot certify its siblings. Polling it reported SUCCESS while the
    #     sibling run loading the other table had already FAILED — exactly the half-loaded
    #     deployment the wait exists to prevent.
    #   * The sibling runs start concurrently and RACE to create the dataset's Trino schema, which
    #     no run has created yet on a first publish. One wins; the other dies with
    #     "Key 'org_<org>__<dataset>' already exists". Selecting both models is therefore not
    #     merely unverifiable, it is the cause of the failure.
    #
    # Serializing costs a few seconds on two small tables and buys a pollable run id per table and
    # a schema created exactly once. Fail fast: a table that does not load stops the deploy rather
    # than uploading over a table whose sibling is already broken.
    statuses: dict[str, tuple[str, str]] = {}
    for table in EVAL_TABLES:
        run = graphql(
            M_RUN,
            {"input": {"datasetId": dataset_id, "selectedModels": [models[table][0]]}},
            token,
        )["createStaticModelRunRequest"]["run"]
        # A run request is only ACCEPTED here; wait for THIS table's run to reach a terminal state.
        status = poll_run(run["id"], token)
        statuses[table] = (run["id"], status)
        print(f"  {table}: run {run['id']} finished {status}")
        if status != RUN_SUCCESS:
            break
    problems = runs_all_succeeded(statuses)
    if problems:
        print("deployment did not succeed — not archiving:", file=sys.stderr)
        for problem in problems:
            print(f"  ! {problem}", file=sys.stderr)
        return 2

    deployed = {t: deployed_table_state(dataset_name, t) for t in EVAL_TABLES}
    mismatches = deployment_mismatches(receipt, deployed)
    if mismatches:
        print("deployed data does not match the candidate — not archiving:", file=sys.stderr)
        for mismatch in mismatches:
            print(f"  ! {mismatch}", file=sys.stderr)
        return 2

    archive = archive_deployment(args.dir, receipt)
    print(f"\nevery load run SUCCESS and deployed data verified; archived this deployment (immutable) at "
          f"{archive} — the rollback target for the next deploy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
