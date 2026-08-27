"""Publish the serialized adoption evaluation CSVs to OSO as static models.

The maintainer half of the evaluation release path. `build/serialize_evaluation.py` writes the two
CSVs (`product_adoption_measurements`, `adoption_reconciliation`) from one atomic read of
`observations.product_adoption_current`; this validates and uploads them as `currentai.evaluation.*`
static models. It reuses the exact GraphQL mechanics of `build/publish_registry.py` — the `graphql`
helper, `resolve_static_models`, `upload`, `data_rows`, and the run-group-bound `poll_run_group` —
so the two publishers cannot drift.

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

## Rollback is by BYTES — an immutable archive keyed by identity, live-state from an occurrence log

A static-model publication REPLACES the table in place; the platform exposes no prior-revision list,
and `observations.product_adoption_current` may have changed since, so regenerating from an old
commit does not reproduce a previous table. So after a successful deployment this tool archives the
exact bytes it uploaded, plus a completed receipt (row counts, column schema, SHA-256), under an
immutable per-deployment directory `<archive-root>/<deployment_id>/` — keyed on the declaration and
observation identities and written once. The archive root (`--archive-root`, default
`build/evaluation/deployments/`) is independent of `--dir`, so re-publishing from an archive never
nests. What is "live" is read from an append-only occurrence log, not directory mtimes: a fresh
identity records a `deploy`; re-uploading a prior archive (`--dir <that-archive>`) records a
`rollback` without rewriting the immutable bytes. Before deploying, the tool prints the currently-live
archive as the rollback target. The mechanism is `build/deployment_archive.py`, shared with the
scoring-trace publisher. The candidate CSVs under `build/evaluation/` are never the rollback record.

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
import os
import sys
from pathlib import Path

from build import deployment_archive as archive
from build.adoption_measurements import COLUMNS as MEASUREMENTS_COLUMNS
from build.adoption_reconciliation import COLUMNS as RECONCILIATION_COLUMNS
from build.publish_registry import (
    GROUP_SUCCESS,
    M_DATASET,
    M_RUN,
    M_URL,
    Q_DATASETS,
    data_rows,
    graphql,
    poll_run_group,
    resolve_static_models,
    upload,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "evaluation"
DEFAULT_DATASET = "evaluation"
# The durable archive root — the rollback record — is independent of `--dir` (where candidates are
# read), so publishing from an archive never nests a new archive inside it. See build/deployment_archive.py.
DEFAULT_ARCHIVE_ROOT = OUT_DIR / "deployments"

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


def archived_files(out_dir: Path = OUT_DIR) -> dict[str, Path]:
    """The candidate files to archive, keyed by their archived name."""
    return {f"{table}.csv": out_dir / f"{table}.csv" for table in EVAL_TABLES}


# The immutable per-deployment archive and the append-only occurrence log that decides what is live
# both live in build/deployment_archive.py, shared with build/publish_scoring_trace.py so the two
# publishers cannot drift. `deployment_id` above names the archive directory; `archive.store` writes
# it (a fresh identity) or records a rollback (an identity already archived), and `archive.current_live_archive`
# reads the live state from the occurrence log rather than directory mtimes.


# A run request is only ACCEPTED synchronously; materialization happens asynchronously, so the
# archive is gated on the run group reaching terminal SUCCESS and the deployed data matching, not on
# the request being accepted. Polling is `build/publish_registry.py`'s run-group-bound
# `poll_run_group` (imported above), shared so the two publishers cannot drift: it polls the exact
# run group `createStaticModelRunRequest` returns, never a model's "latest run".


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


def run_groups_all_succeeded(statuses: dict[str, tuple[str, str]]) -> list[str]:
    """Problems if any run group did not reach terminal SUCCESS.

    `statuses` is table -> (run_group_id, status).
    """
    return [
        f"{table}: run group {run_group_id} ended {status!r}, not SUCCESS"
        for table, (run_group_id, status) in statuses.items()
        if status != GROUP_SUCCESS
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
    parser.add_argument("--dir", type=Path, default=OUT_DIR, help="where candidate CSVs are read")
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT,
                        help="the durable archive + occurrence log (independent of --dir, so publishing "
                             "from an archive never nests)")
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

    rollback_target = archive.current_live_archive(args.archive_root)
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

    # ONE RUN REQUEST PER MODEL, awaited in turn — the same discipline `build/publish_registry.py`
    # uses, down to its shared run-group-bound `poll_run_group`. `CreateStaticModelRunRequestInput`
    # takes (datasetId, staticModelId), one model per request; a request naming N models would fan
    # out into N runs and return only one run group, which cannot certify its siblings, and the
    # sibling loads would RACE to create the dataset's Trino schema. Both were observed on the first
    # publish (2026-08-25). Serialize, and poll the EXACT run group this request returned — never a
    # model's "latest run", which could be an earlier unrelated success that would pass the poll
    # before this run has even appeared. The 1800s budget keeps the more generous patience this
    # maintainer deploy has always allowed while sharing the one helper. Fail fast: the first model
    # that does not reach SUCCESS stops the deploy rather than uploading over a table whose sibling
    # is already broken.
    statuses: dict[str, tuple[str, str]] = {}
    for table in EVAL_TABLES:
        run_group = graphql(
            M_RUN,
            {"input": {"datasetId": dataset_id, "staticModelId": models[table][0]}},
            token,
        )["createStaticModelRunRequest"]["runGroup"]
        # A run request is only ACCEPTED here; wait for THIS run group to reach a terminal state.
        status = poll_run_group(run_group["id"], token, timeout=1800.0)
        statuses[table] = (run_group["id"], status)
        print(f"  {table}: run group {run_group['id']} finished {status}")
        if status != GROUP_SUCCESS:
            break
    problems = run_groups_all_succeeded(statuses)
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

    target, kind = archive.store(args.archive_root, deployment_id(args.dir), archived_files(args.dir), receipt)
    verb = "archived this deployment (immutable)" if kind == "deploy" else "recorded a rollback to the archived deployment"
    print(f"\nevery load run SUCCESS and deployed data verified; {verb} at "
          f"{target} — now the live state in {args.archive_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
