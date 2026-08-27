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
via `pyoso`, and only then records the occurrence. The bytes are persisted BEFORE the platform
mutation, content-addressed by `artifact_id` (SHA-256 over the file manifest) under
`<archive-root>/artifacts/<artifact_id>/` (default `--archive-root`
`build/evaluation/scoring-trace-deployments/`, separate from the evaluation publisher's
`deployments/` so neither reads the other's archives); the append-only occurrence log — not
directory mtimes — decides what is live. The operation is EXPLICIT: a normal publish is a `deploy`;
`--rollback <artifact_id>` re-uploads an already-archived artifact after verifying its recorded
hashes. The archive root is independent of `--dir`, so publishing from an archive never nests. The
mechanism is `build/deployment_archive.py`, shared with the evaluation publisher.

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
import os
import sys
from pathlib import Path

from build import deployment_archive as archive
from build.axis_scoring_trace import TABLES as TRACE_SPEC
from build.publish_evaluation import (
    csv_provenance,
    deployed_table_state,
    materialize,
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
# Its OWN archive root — never the evaluation publisher's `deployments/` — and independent of `--dir`,
# so publishing from an archive never nests. The occurrence log lives here too. See build/deployment_archive.py.
DEFAULT_ARCHIVE_ROOT = OUT_DIR / "scoring-trace-deployments"

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


def archived_files(out_dir: Path = OUT_DIR) -> dict[str, Path]:
    """The candidate files to archive, keyed by their archived name."""
    return {f"{table}.csv": out_dir / f"{table}.csv" for table in TRACE_TABLES}


# The immutable per-deployment archive and the append-only occurrence log that decides what is live
# both live in build/deployment_archive.py, shared with build/publish_evaluation.py (each publisher
# passing its own --archive-root) so the two cannot drift and neither reads the other's archives.


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
    parser.add_argument("--dir", type=Path, default=OUT_DIR, help="where candidate CSVs are read")
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT,
                        help="the durable archive + occurrence log (independent of --dir, so publishing "
                             "from an archive never nests)")
    parser.add_argument("--rollback", metavar="ARTIFACT_ID",
                        help="re-upload an already-archived artifact by its artifact_id; verifies its "
                             "recorded hashes and records a rollback, not a deploy")
    parser.add_argument("--deploy-artifact", metavar="ARTIFACT_ID",
                        help="deploy an already-staged/Released artifact by its artifact_id: re-upload "
                             "its EXACT archived bytes (verified against their recorded hashes) and "
                             "record a deploy — so the OSO publish is bound to the released artifact, "
                             "not to whatever --dir currently holds")
    parser.add_argument("--stage-artifact", action="store_true",
                        help="validate candidates and persist the content-addressed artifact locally, "
                             "print its artifact_id, and exit — NO OSO resolution or mutation. This is "
                             "the network-free first step of stage -> Release -> publish.")
    args = parser.parse_args()

    dataset_name = os.environ.get("OSO_DATASET", DEFAULT_DATASET)

    # The three artifact modes are mutually exclusive — each names one operation. --stage-artifact
    # deliberately WRITES the artifact, so it cannot ride --dry-run/--plan (which promise no write);
    # combining them is what previously wrote despite --dry-run.
    active_modes = [name for name, on in (
        ("--stage-artifact", args.stage_artifact),
        ("--deploy-artifact", bool(args.deploy_artifact)),
        ("--rollback", bool(args.rollback)),
    ) if on]
    if len(active_modes) > 1:
        print(f"{' and '.join(active_modes)} are mutually exclusive — choose one operation", file=sys.stderr)
        return 2
    if args.stage_artifact and (args.dry_run or args.plan):
        print("--stage-artifact writes the artifact and cannot be combined with --dry-run/--plan "
              "(which write nothing); stage first, then run a dry run separately", file=sys.stderr)
        return 2

    if args.stage_artifact:
        # Network-free: build + validate the candidates and persist the artifact so it exists on disk
        # (and can be pushed to a durable Release) BEFORE any OSO call.
        missing = [t for t in TRACE_TABLES if not (args.dir / f"{t}.csv").exists()]
        if missing:
            print(f"missing CSVs: {missing}. Run `uv run python -m build.axis_scoring_trace --out {args.dir}` first.",
                  file=sys.stderr)
            return 2
        receipt = build_receipt(args.dir)
        print_plan(receipt, dataset_name)
        problems = validate_candidates(args.dir)
        if problems:
            print("candidate validation failed:", file=sys.stderr)
            for problem in problems:
                print(f"  ! {problem}", file=sys.stderr)
            return 2
        aid = archive.ensure_artifact(args.archive_root, archived_files(args.dir), receipt, deployment_id(args.dir))
        print(f"staged artifact {aid} at {archive.artifact_dir(args.archive_root, aid)} — no OSO mutation")
        return 0

    # The operation is EXPLICIT and never inferred from the archive:
    #   --rollback ID         re-upload verified archived bytes, record a ROLLBACK;
    #   --deploy-artifact ID  re-upload verified archived bytes, record a DEPLOY (bound to the Release);
    #   (default)             build + canonically validate candidates from --dir at HEAD, then deploy.
    from_archive = bool(args.rollback or args.deploy_artifact)
    if from_archive:
        operation = "rollback" if args.rollback else "deploy"
        aid = args.rollback or args.deploy_artifact
        try:
            # Provenance is reconstructed from the VERIFIED bytes and required to equal receipt.json,
            # which SHA256SUMS does not cover — a tampered receipt cannot ride the re-upload.
            receipt, deployment = archive.verified_rollback_provenance(
                args.archive_root, aid, {f"{t}.csv" for t in TRACE_TABLES}, build_receipt, deployment_id,
            )
        except RuntimeError as exc:
            print(f"cannot {operation} artifact {aid}: {exc}", file=sys.stderr)
            return 2
        src_dir = archive.artifact_dir(args.archive_root, aid)
        print(f"{operation}: artifact {aid} (generation {deployment}) verified against its recorded hashes")
        print_plan(receipt, dataset_name)
    else:
        operation = "deploy"
        missing = [t for t in TRACE_TABLES if not (args.dir / f"{t}.csv").exists()]
        if missing:
            print(f"missing CSVs: {missing}. Run `uv run python -m build.axis_scoring_trace --out {args.dir}` first.",
                  file=sys.stderr)
            return 2
        src_dir = args.dir
        receipt = build_receipt(src_dir)
        print_plan(receipt, dataset_name)
        problems = validate_candidates(src_dir)  # structural + canonical equivalence, BEFORE any mutation
        if problems:
            print("candidate validation failed:", file=sys.stderr)
            for problem in problems:
                print(f"  ! {problem}", file=sys.stderr)
            return 2
        deployment, aid = deployment_id(src_dir), None  # aid is set when the bytes are persisted

    if args.plan:
        return 0

    token = os.environ.get("OSO_API_KEY")
    org_id = os.environ.get("OSO_ORG_ID")
    if not token or not org_id:
        print("OSO_API_KEY and OSO_ORG_ID must both be set (use --plan for an offline plan)",
              file=sys.stderr)
        return 2

    previous = archive.current_live_artifact_id(args.archive_root)
    if previous is not None:
        print(f"currently live artifact (the rollback target if this is bad): {previous}")

    if args.dry_run:
        # READ-ONLY resolution — create=False — so a dry run creates NOTHING and writes nothing.
        dataset_id = resolve_evaluation_dataset(dataset_name, org_id, token, create=False)
        if dataset_id is None:
            print(f"would create dataset {dataset_name}, then create + upload {list(TRACE_TABLES)}")
            return 0
        models = resolve_static_models(dataset_id, org_id, token, TRACE_TABLES, create=False)
        print(f"dataset {dataset_name} = {dataset_id}")
        for table in TRACE_TABLES:
            model_id = models[table][0]
            verb = "would upload" if model_id else "would create + upload"
            print(f"  {verb} {table}.csv ({receipt[table]['rows']:,} rows) -> {model_id}")
        return 0  # NO write, NO create

    # REAL publish. Persist the candidate bytes content-addressed BEFORE any create-capable platform
    # call — `resolve_*` with create=True can create the dataset or static models, so the artifact
    # must already exist on disk first. Bytes re-uploaded from the archive (--rollback /
    # --deploy-artifact) are already archived and verified above.
    if not from_archive:
        aid = archive.ensure_artifact(args.archive_root, archived_files(src_dir), receipt, deployment)

    dataset_id = resolve_evaluation_dataset(dataset_name, org_id, token, create=True)
    models = resolve_static_models(dataset_id, org_id, token, TRACE_TABLES, create=True)
    print(f"dataset {dataset_name} = {dataset_id}")

    if materialize(dataset_id, models, TRACE_TABLES, src_dir, token, dataset_name, receipt, deployment_mismatches):
        return 2

    archive.record_occurrence(args.archive_root, operation, deployment, aid, previous)
    print(f"\nevery load run SUCCESS and deployed data verified; recorded {operation} of artifact {aid} "
          f"(generation {deployment}) — now the live state in {args.archive_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
