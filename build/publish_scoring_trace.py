"""Publish the three repository-owned scoring-trace CSVs to OSO as static models.

The maintainer half of the Phase-6 scoring-trace deploy (`docs/operations/deploy-scoring-trace.md`).
`build/axis_scoring_trace.py --out build/evaluation` writes the three CSVs — `axis_facts`,
`axis_rule_matches`, `axis_results` — by replaying the openness ladder once per product from the
working tree; this validates and uploads them as `currentai.evaluation.*` static models. It reuses
the exact GraphQL mechanics of `build/publish_registry.py` — the `graphql` helper,
`resolve_static_models`, `upload`, `data_rows`, and the run-group-bound `poll_run_group` — and the
generic read-back/immutable-archive machinery of `build/publish_evaluation.py`, so the evaluation
and trace publishers cannot drift.

## Identity: the declaration alone (§4.4)

The three tables key on `declaration_version_id` and carry NO `release_id` and NO
`observation_snapshot_id` — a deterministic evaluation of the declarations does not depend on any
measurement. Validation pins that: `declaration_version_id` and `source_git_sha` are constant within
each file and equal across all three, and each table is unique on its own grain.

## The dual-run gate

`axis_results.reproduces_recorded` is the ADR-001 dual-run agreement made queryable: `True` on every
scored row means the repository-owned evaluator computed the same score `check_rubric` recorded. A
scored row with `reproduces_recorded` anything but `True` is a `check_rubric` disagreement, and this
publisher REFUSES to upload it — a disagreement is resolved in the evaluator, never deployed around.

## Canonical equivalence is the authority

The structural checks above prove a candidate is internally consistent; they cannot prove it is the
COMPLETE, AUTHENTIC trace. So before any mutation the publisher re-runs the builder in memory
(`build.axis_scoring_trace.resolve()`) and requires the candidate to be byte-for-byte that output —
every product, fact, and rule-walk row, the current `declaration_version_id` and `source_git_sha`,
and every result disposition. A truncated subset or a fabricated/stale identity is rejected here,
and there is no second evaluation that could drift from the builder.

## No writes before the dry-run returns; rollback is by BYTES

Like the evaluation publisher: `--plan` (offline) and `--dry-run` (read-only id resolution) validate
and print the plan and perform NO mutation and NO local write. A real publish uploads, requests one
run per model with `{datasetId, staticModelId}` and awaits each run group to terminal `SUCCESS`
(polling the exact group the mutation returned), verifies the deployed row count and column schema
via `pyoso`, and only then writes an immutable per-deployment archive of the exact bytes it uploaded
— under `build/evaluation/scoring-trace-deployments/<deployment_id>/`, kept separate from the
evaluation publisher's `deployments/` so neither reads the other's archives. It REFUSES to overwrite
an existing archive.

Environment:
    OSO_API_KEY   required (except for --plan)
    OSO_ORG_ID    required (except for --plan)
    OSO_DATASET   optional, defaults to "evaluation"

Usage:
    uv run python -m build.axis_scoring_trace --out build/evaluation   # write the three CSVs first
    uv run python -m build.publish_scoring_trace --plan       # offline: validate + plan, no creds, no network
    uv run python -m build.publish_scoring_trace --dry-run    # read-only id resolution, no mutation, no write
    uv run python -m build.publish_scoring_trace              # validate, publish, archive
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from build.axis_scoring_trace import TABLES as TRACE_SPEC
from build.publish_evaluation import (
    csv_provenance,
    deployed_table_state,
    resolve_evaluation_dataset,
    run_groups_all_succeeded,
)
from build.publish_registry import (
    GROUP_SUCCESS,
    M_RUN,
    M_URL,
    data_rows,
    graphql,
    poll_run_group,
    resolve_static_models,
    upload,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "evaluation"
DEFAULT_DATASET = "evaluation"

# The three trace tables, in a stable publish order, and their exact expected headers.
TRACE_TABLES: tuple[str, ...] = tuple(TRACE_SPEC)
EXPECTED_HEADERS: dict[str, list[str]] = {name: list(cols) for name, cols in TRACE_SPEC.items()}

# The declaration identity every row carries — constant within each file, equal across all three.
_IDENTITY_COLUMNS = ("declaration_version_id", "source_git_sha")

# The grain each table is unique on. All lead with the declaration + product/category/axis; the
# finer tables add their own discriminator.
_GRAIN: dict[str, tuple[str, ...]] = {
    "axis_results": ("declaration_version_id", "product_slug", "category_slug", "axis"),
    "axis_rule_matches": ("declaration_version_id", "product_slug", "category_slug", "axis", "rule_index"),
    "axis_facts": (
        "declaration_version_id", "product_slug", "category_slug", "axis",
        "dimension", "part_index", "fact_kind",
    ),
}


def deployments_dir(out_dir: Path) -> Path:
    """Where completed, immutable trace-deployment archives live.

    Deliberately NOT `deployments/` — that belongs to `build/publish_evaluation.py`, which shares
    this `build/evaluation` directory. A separate subdirectory keeps each publisher's `latest_archive`
    scan blind to the other's archives (a trace archive has no evaluation CSVs, and vice versa).
    """
    return out_dir / "scoring-trace-deployments"


def build_receipt(out_dir: Path = OUT_DIR) -> dict:
    """The provenance of every trace CSV present — the candidate description."""
    return {
        table: csv_provenance(out_dir / f"{table}.csv")
        for table in TRACE_TABLES
        if (out_dir / f"{table}.csv").exists()
    }


def _read_rows(path: Path) -> tuple[list[str], list[dict]]:
    import csv

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def structural_problems(out_dir: Path = OUT_DIR) -> list[str]:
    """The cheap, well-messaged structural checks. Returns a list of problems (empty = ok).

    These are NOT the authority — canonical equivalence (below) is — but they run first because a
    header, empty-table, identity, grain, dual-run, or orphan failure is far more legible reported
    on its own than as a wall of canonical-row diffs. A candidate that passes these is still only
    published if it is byte-for-byte the trace this repository's builder produces.
    """
    errors: list[str] = []
    parsed: dict[str, tuple[list[str], list[dict]]] = {}
    for table in TRACE_TABLES:
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
    if errors or len(parsed) != len(TRACE_TABLES):
        return errors

    # Identity columns constant within each file and equal across all three.
    identities: dict[str, dict[str, set]] = {}
    for table, (_header, rows) in parsed.items():
        identities[table] = {col: {r.get(col) for r in rows} for col in _IDENTITY_COLUMNS}
        for col in _IDENTITY_COLUMNS:
            if len(identities[table][col]) != 1:
                errors.append(f"{table}.csv has inconsistent {col}: {sorted(identities[table][col])[:3]}")
    for col in _IDENTITY_COLUMNS:
        values = {next(iter(identities[t][col])) for t in TRACE_TABLES if len(identities[t][col]) == 1}
        if len(values) > 1:
            errors.append(f"{col} differs across the three files: {sorted(values)}")

    # Grain uniqueness per table.
    for table, (_header, rows) in parsed.items():
        keys = [tuple(r.get(c) for c in _GRAIN[table]) for r in rows]
        if len(keys) != len(set(keys)):
            errors.append(f"{table}.csv is not unique on its grain {_GRAIN[table]}")

    # The dual-run gate: every SCORED result reproduces the recorded score. A false (or any
    # non-"True") reproduces_recorded on a scored row is a check_rubric disagreement, never deployed.
    disagreements = [
        (r.get("product_slug"), r.get("category_slug"))
        for r in parsed["axis_results"][1]
        if r.get("status") == "scored" and r.get("reproduces_recorded") != "True"
    ]
    if disagreements:
        errors.append(
            f"axis_results has {len(disagreements)} scored row(s) that do not reproduce the recorded "
            f"score (e.g. {disagreements[:3]}) — resolve the check_rubric disagreement, do not deploy it"
        )

    # Population coherence: every product/category traced in facts or rules has a result row.
    result_products = {(r["product_slug"], r["category_slug"]) for r in parsed["axis_results"][1]}
    for table in ("axis_facts", "axis_rule_matches"):
        products = {(r["product_slug"], r["category_slug"]) for r in parsed[table][1]}
        orphans = products - result_products
        if orphans:
            errors.append(f"{table} has product/category rows with no axis_results row: {sorted(orphans)[:3]}")
    return errors


def canonical_equivalence_problems(
    out_dir: Path = OUT_DIR, root: Path = ROOT, allow_dirty: bool = False
) -> list[str]:
    """The authority: the candidate must be EXACTLY the trace this repository's builder produces.

    Structural checks prove a candidate is internally consistent; they cannot prove it is complete
    or authentic. A truncated-but-consistent subset (one product, one fact, one rule, one result)
    passes them, and any constant `declaration_version_id` / `source_git_sha` passes them — nothing
    ties the bytes to *this* repository at *this* commit.

    So, before any mutation, re-run the canonical builder in memory and compare. The expected rows
    are written through the very `write_tables` the candidate was written with and read back with
    the same reader, so the comparison is over identical serialization — then each table is an
    order-independent multiset of `canonical_row` strings. Equality proves, in one gate: the exact
    complete population (no omitted product, fact, or rule; no invented row), every value and result
    disposition and `reproduces_recorded` flag, and the current declaration identity + source commit
    (both are columns on every row, so a fabricated or stale id mismatches every row). There is no
    second evaluation here — the authority is the builder itself.
    """
    import collections
    import tempfile

    from build.axis_scoring_trace import canonical_row, resolve
    from build.axis_scoring_trace import TABLES as TRACE_SPEC_LOCAL
    from build.serialize_registry import write_tables

    try:
        expected = resolve(root, allow_dirty=allow_dirty)
    except Exception as exc:  # DirtyWorktreeError, a recipe error, or a contract breach
        return [f"cannot rebuild the canonical trace to compare against (publish from a clean commit): {exc}"]

    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        expected_dir = Path(tmp)
        write_tables(expected, expected_dir, TRACE_SPEC_LOCAL)
        for table in TRACE_TABLES:
            _eh, expected_rows = _read_rows(expected_dir / f"{table}.csv")
            _ch, candidate_rows = _read_rows(out_dir / f"{table}.csv")
            expected_canon = collections.Counter(canonical_row(table, r) for r in expected_rows)
            candidate_canon = collections.Counter(canonical_row(table, r) for r in candidate_rows)
            if candidate_canon == expected_canon:
                continue
            omitted = expected_canon - candidate_canon
            invented = candidate_canon - expected_canon
            detail = []
            if omitted:
                detail.append(f"{sum(omitted.values())} row(s) the builder produced are missing "
                              f"(e.g. {next(iter(omitted))[:160]}…)")
            if invented:
                detail.append(f"{sum(invented.values())} row(s) the builder did not produce are present "
                              f"(e.g. {next(iter(invented))[:160]}…)")
            problems.append(
                f"{table} is not the canonical trace this repository produces: " + "; ".join(detail)
            )
    return problems


def validate_candidates(out_dir: Path = OUT_DIR, root: Path = ROOT, allow_dirty: bool = False) -> list[str]:
    """Every check that must pass before a byte is uploaded (empty = ok).

    Structural checks first, for legible messages; then canonical equivalence, the final authority.
    Run in --plan and --dry-run as well as a real publish — a candidate that fails here is never
    published, and the failure is the same whether or not credentials are present.
    """
    problems = structural_problems(out_dir)
    if problems:
        return problems
    return canonical_equivalence_problems(out_dir, root, allow_dirty)


def deployment_id(out_dir: Path = OUT_DIR) -> str:
    """A stable, immutable id for the candidate: the declaration identity it carries.

    The trace tables have no observation snapshot, so the id is the declaration version and the
    commit it was cut at — two publishes of the same declaration share an id (and cannot both be
    archived; a deployment is recorded once).
    """
    _header, rows = _read_rows(out_dir / "axis_results.csv")
    dvid = rows[0]["declaration_version_id"]
    sha = rows[0]["source_git_sha"]
    return f"{dvid[:12]}-{sha[:12]}"


def archive_deployment(out_dir: Path, receipt: dict) -> Path:
    """Copy the just-deployed CSVs + completed receipt into an immutable per-deployment directory.

    Refuses to overwrite an existing archive: a deployment id is written exactly once.

    KNOWN LIMITATION (non-blocking; shared with build/publish_evaluation.py, follow-up before the
    rollback workflow is relied on): the archive root is derived from `out_dir`, so re-publishing a
    prior archive's bytes with `--dir <that-archive>` would nest a new archive *inside* it and would
    not update the canonical `build/evaluation/scoring-trace-deployments/` root's notion of what is
    live. Deployment identity (the declaration) and deployment occurrence (a publish event) are
    conflated. First deploys are unaffected; a rollback-from-archive flow needs the archive root
    decoupled from the read `--dir` first.
    """
    target = deployments_dir(out_dir) / deployment_id(out_dir)
    if target.exists():
        raise RuntimeError(
            f"deployment archive {target} already exists — a deployment id is immutable and is "
            f"never overwritten. If you are re-publishing identical bytes, the previous archive "
            f"already records them; if not, the declaration identity would have changed."
        )
    target.mkdir(parents=True)
    for table in TRACE_TABLES:
        shutil.copy2(out_dir / f"{table}.csv", target / f"{table}.csv")
    (target / "receipt.json").write_text(
        json.dumps({"deployment_id": target.name, "tables": receipt}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return target


def latest_archive(out_dir: Path) -> Path | None:
    """The most recently written trace-deployment archive, if any — the next deploy's rollback target."""
    root = deployments_dir(out_dir)
    if not root.exists():
        return None
    archives = [p for p in root.iterdir() if p.is_dir() and (p / "receipt.json").exists()]
    return max(archives, key=lambda p: p.stat().st_mtime) if archives else None


def deployment_mismatches(expected: dict, deployed: dict) -> list[str]:
    """Problems if the deployed row count or column set does not match the validated candidate.

    Row counts must match exactly. On columns, the deployed table must carry every candidate column
    that holds a value somewhere, and NO column the candidate does not declare. The one permitted
    absence is a candidate column that is null in every row: the loader types columns from records
    and drops one it never sees a value for, so its absence is schema inference, not lost data.
    """
    problems: list[str] = []
    for table in TRACE_TABLES:
        exp, got = expected[table], deployed[table]
        if got["rows"] != exp["rows"]:
            problems.append(f"{table}: deployed {got['rows']} rows, candidate had {exp['rows']}")
        permitted_absent = set(exp.get("all_null_columns") or ())
        missing = set(exp["columns"]) - set(got["columns"]) - permitted_absent
        extra = set(got["columns"]) - set(exp["columns"])
        if missing:
            problems.append(f"{table}: deployed table is missing candidate columns with data: {sorted(missing)}")
        if extra:
            problems.append(f"{table}: deployed table has undeclared columns: {sorted(extra)}")
    return problems


def print_plan(receipt: dict, dataset_name: str) -> None:
    print(f"dataset {dataset_name} (currentai.{dataset_name}.*)")
    for table in TRACE_TABLES:
        entry = receipt.get(table)
        if entry is None:
            print(f"  MISSING {table}.csv — run build.axis_scoring_trace --out first")
        else:
            print(f"  {table}.csv  {entry['rows']:,} rows  sha256 {entry['sha256'][:12]}…")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="validate + print the plan; no network, no creds, no write")
    parser.add_argument("--dry-run", action="store_true", help="validate + resolve ids read-only; no mutation, no write")
    parser.add_argument("--dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    dataset_name = os.environ.get("OSO_DATASET", DEFAULT_DATASET)
    missing = [t for t in TRACE_TABLES if not (args.dir / f"{t}.csv").exists()]
    if missing:
        print(f"missing CSVs: {missing}. Run `uv run python -m build.axis_scoring_trace --out {args.dir}` first.",
              file=sys.stderr)
        return 2

    receipt = build_receipt(args.dir)
    print_plan(receipt, dataset_name)

    # Validate BEFORE any mutation — and in --plan / --dry-run too.
    problems = validate_candidates(args.dir)
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
        print(f"would create dataset {dataset_name}, then create + upload {list(TRACE_TABLES)}")
        return 0  # dry-run only reaches here; no write

    models = resolve_static_models(dataset_id, org_id, token, TRACE_TABLES, create=not args.dry_run)
    print(f"dataset {dataset_name} = {dataset_id}")

    if args.dry_run:
        for table in TRACE_TABLES:
            model_id = models[table][0]
            verb = "would upload" if model_id else "would create + upload"
            print(f"  {verb} {table}.csv ({receipt[table]['rows']:,} rows) -> {model_id}")
        return 0  # NO write on a dry run

    for table in TRACE_TABLES:
        path = args.dir / f"{table}.csv"
        model_id = models[table][0]
        url = graphql(M_URL, {"staticModelId": model_id}, token)["createStaticModelUploadUrl"]
        upload(path, url)
        print(f"  uploaded {table}.csv ({path.stat().st_size:,} bytes, {receipt[table]['rows']:,} rows)")

    # ONE RUN REQUEST PER MODEL, awaited in turn — the same discipline the registry and evaluation
    # publishers use, down to their shared run-group-bound `poll_run_group`.
    # `CreateStaticModelRunRequestInput` takes (datasetId, staticModelId), one model per request; a
    # request naming N models would fan out into N runs and return one run group, and the sibling
    # loads would race to create the dataset's Trino schema. Serialize, poll the EXACT run group this
    # request returned (never a model's "latest run"), and fail fast on the first non-SUCCESS group.
    statuses: dict[str, tuple[str, str]] = {}
    for table in TRACE_TABLES:
        run_group = graphql(
            M_RUN,
            {"input": {"datasetId": dataset_id, "staticModelId": models[table][0]}},
            token,
        )["createStaticModelRunRequest"]["runGroup"]
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

    deployed = {t: deployed_table_state(dataset_name, t) for t in TRACE_TABLES}
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
