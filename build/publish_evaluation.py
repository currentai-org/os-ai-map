"""Publish the serialized adoption evaluation CSVs to OSO as static models.

The maintainer half of the evaluation release path. `build/serialize_evaluation.py` writes the two
CSVs (`product_adoption_measurements`, `adoption_reconciliation`) from one atomic read of
`observations.product_adoption_current`; this uploads them as `currentai.evaluation.*` static
models. It reuses the exact GraphQL mechanics of `build/publish_registry.py` — the `graphql`
helper, `resolve_static_models`, `upload`, `data_rows` — so the two publishers cannot drift, and
adds an evaluation-specific dataset resolver.

## Rollback is by BYTES, not by revision re-pointing

A static-model publication REPLACES the table in place; the platform exposes no prior-revision
list to re-point to, and `observations.product_adoption_current` may have changed since, so
regenerating from an old commit does not reproduce the old table. Rollback therefore means
re-uploading the exact bytes that were live before the replacement. This publisher writes a
provenance receipt (`build/evaluation/publish_receipt.json`) recording each CSV's row count,
column schema, and SHA-256 BEFORE it uploads, and it refuses to overwrite an archived good copy;
to roll back, re-run this publisher pointed at the archived known-good CSV whose SHA the receipt
records.

## Mutation-free dry run

`--dry-run` prints the plan — tables, row counts, SHA-256, and the dataset/model it would touch —
and performs NO mutation: dataset and model resolution run read-only (`create=False`), and nothing
is uploaded and no run is requested. `--plan` prints the same plan entirely offline (no network, no
credentials), which is what the test exercises.

Environment:
    OSO_API_KEY   required (except for --plan)
    OSO_ORG_ID    required (except for --plan)
    OSO_DATASET   optional, defaults to "evaluation"

Usage:
    uv run python -m build.serialize_evaluation --live      # write build/evaluation/*.csv first
    uv run python -m build.publish_evaluation --plan        # offline plan, no creds, no network
    uv run python -m build.publish_evaluation --dry-run     # read-only id resolution, no mutations
    uv run python -m build.publish_evaluation               # publish
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

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
EVAL_TABLES: tuple[str, ...] = ("product_adoption_measurements", "adoption_reconciliation")
RECEIPT = OUT_DIR / "publish_receipt.json"


def csv_provenance(path: Path) -> dict:
    """Row count, column schema, and SHA-256 of a CSV — the bytes a rollback must be able to name."""
    raw = path.read_bytes()
    header = path.read_text(encoding="utf-8").splitlines()[0] if raw else ""
    return {
        "rows": data_rows(path),
        "columns": header.split(",") if header else [],
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def build_receipt(out_dir: Path = OUT_DIR) -> dict:
    """The provenance receipt for every evaluation CSV present — captured BEFORE any upload."""
    return {
        table: csv_provenance(out_dir / f"{table}.csv")
        for table in EVAL_TABLES
        if (out_dir / f"{table}.csv").exists()
    }


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
    parser.add_argument("--plan", action="store_true", help="print the offline plan; no network, no creds")
    parser.add_argument("--dry-run", action="store_true", help="resolve ids read-only; upload nothing")
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

    if args.plan:
        return 0

    token = os.environ.get("OSO_API_KEY")
    org_id = os.environ.get("OSO_ORG_ID")
    if not token or not org_id:
        print("OSO_API_KEY and OSO_ORG_ID must both be set (use --plan for an offline plan)",
              file=sys.stderr)
        return 2

    # Capture provenance BEFORE any mutation, so a rollback can name the bytes that were live.
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    dataset_id = resolve_evaluation_dataset(dataset_name, org_id, token, create=not args.dry_run)
    if dataset_id is None:
        print(f"would create dataset {dataset_name}, then create + upload {list(EVAL_TABLES)}")
        return 0

    models = resolve_static_models(dataset_id, org_id, token, EVAL_TABLES, create=not args.dry_run)
    print(f"dataset {dataset_name} = {dataset_id}")

    if args.dry_run:
        for table in EVAL_TABLES:
            model_id = models[table][0]
            verb = "would upload" if model_id else "would create + upload"
            print(f"  {verb} {table}.csv ({receipt[table]['rows']:,} rows) -> {model_id}")
        return 0

    for table in EVAL_TABLES:
        path = args.dir / f"{table}.csv"
        model_id = models[table][0]
        url = graphql(M_URL, {"staticModelId": model_id}, token)["createStaticModelUploadUrl"]
        upload(path, url)
        run = graphql(M_RUN, {"input": {"staticModelId": model_id}}, token)["createStaticModelRunRequest"]["run"]
        print(f"  uploaded {table}.csv ({path.stat().st_size:,} bytes, {receipt[table]['rows']:,} rows); "
              f"run {run['id']} {run['status']}")
    print(f"\nprovenance receipt at {RECEIPT} — archive the CSVs + receipt for rollback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
