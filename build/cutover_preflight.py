"""Cross-cutover pre-flight invariants for the `evaluator_version` cutover (§0.2 / §8).

The cutover bumps `EVALUATOR_VERSION`, rebuilds every declaration-keyed candidate from ONE clean
commit, and re-uploads them so all five live tables move to a single new `declaration_version_id` in
one coordinated pass (`docs/operations/evaluator-version-cutover.md`). Two invariants make that swap
safe, and this module is both — as PURE functions plus an offline CLI, with no platform mutation:

- **Single identity.** Every candidate across BOTH publishers must share one `declaration_version_id`
  (and, on the tables that carry it, one `source_git_sha`). That proves the single-commit build
  collapsed to one generation rather than smuggling two.

- **Semantic no-change.** The cutover must change **identity only** — not a fact, rule match, score,
  route, status, or reconciliation result. For each live table, the non-content columns
  (`declaration_version_id`, `source_git_sha` where present, and any non-content build timestamp such
  as `adoption_reconciliation.evaluated_at`) are projected out, and the new candidate rows must equal
  the currently-deployed rows as an order-independent multiset. Any difference outside the projected
  columns fails the cutover — it would mean the evaluator bump carried a content change, which D1's
  bump policy forbids without its own justified generation.

The semantic comparison is a pure multiset over canonicalized rows, so the deployed rows can come from
an exported CSV (offline, the reviewed path) or from a read-only `pyoso` query (`--live`). Neither
writes anything; the cutover itself stays unauthorized.

Usage:
    uv run python -m build.cutover_preflight --dir build/evaluation            # single-identity, offline
    uv run python -m build.cutover_preflight --dir build/evaluation \
        --deployed-dir exported/                                               # + semantic vs CSV export
    uv run python -m build.cutover_preflight --dir build/evaluation --live     # + semantic vs pyoso (read-only)
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "evaluation"
DEFAULT_DATASET = "evaluation"

# The five live declaration-keyed tables in the cutover set (registry.axis_assessments is excluded by
# D3 — it has no live identity to re-key). Read the authoritative membership from assets.yaml at
# execution time (§1); this constant is the pre-flight's own expectation of what it compares.
CUTOVER_TABLES: tuple[str, ...] = (
    "product_adoption_measurements",
    "adoption_reconciliation",
    "axis_facts",
    "axis_rule_matches",
    "axis_results",
)

IDENTITY_COLUMN = "declaration_version_id"
SOURCE_SHA_COLUMN = "source_git_sha"

# The non-content columns projected out before the semantic multiset comparison, per table. Everything
# NOT listed here is content and must be reproduced byte-identically (modulo CSV/loader canonicalization)
# across the cutover. `source_git_sha` is on the trace tables only; `evaluated_at` (a build timestamp,
# not a measurement) is on adoption_reconciliation only. The set is stated here and re-affirmed at
# execution time — a column that should be content must never be silently projected away.
NON_CONTENT_COLUMNS: dict[str, tuple[str, ...]] = {
    "product_adoption_measurements": (IDENTITY_COLUMN,),
    "adoption_reconciliation": (IDENTITY_COLUMN, "evaluated_at"),
    "axis_facts": (IDENTITY_COLUMN, SOURCE_SHA_COLUMN),
    "axis_rule_matches": (IDENTITY_COLUMN, SOURCE_SHA_COLUMN),
    "axis_results": (IDENTITY_COLUMN, SOURCE_SHA_COLUMN),
}


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_candidates(src_dir: Path, tables: tuple[str, ...] = CUTOVER_TABLES) -> dict[str, list[dict]]:
    """Every cutover candidate present under `src_dir`, keyed by table name (missing files omitted)."""
    return {t: _read_csv(src_dir / f"{t}.csv") for t in tables if (src_dir / f"{t}.csv").exists()}


def completeness_problems(candidates: dict[str, list[dict]], tables: tuple[str, ...] = CUTOVER_TABLES) -> list[str]:
    """The cutover set must be built completely — cover every table, or do not run."""
    missing = [t for t in tables if t not in candidates]
    return [f"missing cutover candidate(s): {missing}"] if missing else []


def single_identity_problems(candidates: dict[str, list[dict]]) -> list[str]:
    """Every candidate across both publishers must share one `declaration_version_id`, and (on the
    tables that carry it) one `source_git_sha`. Returns a list of problems (empty = ok)."""
    problems: list[str] = []
    all_dvids: set[str] = set()
    all_shas: set[str] = set()
    for table, rows in candidates.items():
        if not rows:
            problems.append(f"{table}: no candidate rows to check identity")
            continue
        columns = rows[0].keys()
        if IDENTITY_COLUMN not in columns:
            problems.append(f"{table}: missing {IDENTITY_COLUMN}")
        else:
            dvids = {r[IDENTITY_COLUMN] for r in rows}
            if len(dvids) != 1:
                problems.append(f"{table}: {IDENTITY_COLUMN} is not constant within the file: {sorted(dvids)[:3]}")
            all_dvids |= dvids
        if SOURCE_SHA_COLUMN in columns:
            shas = {r[SOURCE_SHA_COLUMN] for r in rows}
            if len(shas) != 1:
                problems.append(f"{table}: {SOURCE_SHA_COLUMN} is not constant within the file: {sorted(shas)[:3]}")
            all_shas |= shas
    if len(all_dvids) > 1:
        problems.append(f"candidates do NOT share one {IDENTITY_COLUMN} (two generations built?): {sorted(all_dvids)}")
    if len(all_shas) > 1:
        problems.append(f"candidates do NOT share one {SOURCE_SHA_COLUMN}: {sorted(all_shas)}")
    return problems


def _canonical_scalar(value) -> str:
    """One canonical string per cell, so a candidate CSV string ("4", "True", "") and the loader's
    typed round-trip (4, True, None) compare equal. bool is handled before int (a bool IS an int)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def _canonical_multiset(rows: list[dict], keep: set[str]) -> Counter:
    return Counter(
        tuple(sorted((column, _canonical_scalar(row.get(column))) for column in keep)) for row in rows
    )


def semantic_no_change_problems(
    table: str, candidate_rows: list[dict], deployed_rows: list[dict], non_content: tuple[str, ...] | None = None
) -> list[str]:
    """The candidate must equal the deployed table on CONTENT — identity/timestamp columns projected
    out — as an order-independent multiset. Returns a list of problems (empty = ok).

    A candidate content column that is empty in every row and absent from the deployed table is the
    loader's own all-null-column drop (e.g. `adoption_reconciliation.override_id`) and is tolerated; a
    candidate column that carries data yet is missing downstream, or a deployed content column the
    candidate never declared, is a real difference. The comparison then runs over the shared content
    columns; `_dlt_*` loader bookkeeping is always excluded.
    """
    drop = set(non_content if non_content is not None else NON_CONTENT_COLUMNS.get(table, (IDENTITY_COLUMN,)))
    if not candidate_rows:
        return [f"{table}: no candidate rows"]
    if not deployed_rows:
        return [f"{table}: no deployed rows to compare against"]

    candidate_cols = {c for c in candidate_rows[0] if c not in drop and not c.startswith("_dlt_")}
    deployed_cols = {c for c in deployed_rows[0] if c not in drop and not c.startswith("_dlt_")}
    problems: list[str] = []
    for column in sorted(candidate_cols - deployed_cols):
        if any(_canonical_scalar(r.get(column)) != "" for r in candidate_rows):
            problems.append(f"{table}: candidate column {column!r} carries data but is absent from the deployed table")
    only_deployed = deployed_cols - candidate_cols
    if only_deployed:
        problems.append(f"{table}: deployed table has content column(s) the candidate does not declare: {sorted(only_deployed)}")
    if problems:
        return problems

    compare = candidate_cols & deployed_cols
    candidate = _canonical_multiset(candidate_rows, compare)
    deployed = _canonical_multiset(deployed_rows, compare)
    if candidate == deployed:
        return []
    not_reproduced = deployed - candidate
    invented = candidate - deployed
    if not_reproduced:
        problems.append(
            f"{table}: {sum(not_reproduced.values())} deployed row(s) NOT reproduced by the candidate "
            f"(e.g. {dict(next(iter(not_reproduced)))})"
        )
    if invented:
        problems.append(
            f"{table}: {sum(invented.values())} candidate row(s) NOT present in the deployed table "
            f"(e.g. {dict(next(iter(invented)))})"
        )
    return problems


def deployed_rows(dataset: str, table: str, timeout: float = 300.0, interval: float = 15.0) -> list[dict]:
    """Read a deployed table's full rows via `pyoso` — READ-ONLY, no mutation. Retries while the query
    catalog lags (the same `TablesNotFound` propagation the publishers handle)."""
    import time

    from build.warehouse import query

    deadline = time.time() + timeout
    while True:
        try:
            rows = query(f"SELECT * FROM currentai.{dataset}.{table}")
            break
        except Exception as exc:  # noqa: BLE001 — propagate anything that is not catalog lag
            if "TablesNotFound" not in str(exc) or time.time() >= deadline:
                raise
            time.sleep(interval)
    return [{k: v for k, v in row.items() if not k.startswith("_dlt_")} for row in rows]


def _report(header: str, problems: list[str]) -> None:
    if problems:
        print(f"{header}: FAIL", file=sys.stderr)
        for problem in problems:
            print(f"  ! {problem}", file=sys.stderr)
    else:
        print(f"{header}: ok")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=Path, default=OUT_DIR, help="where the candidate CSVs are read")
    parser.add_argument("--deployed-dir", type=Path, default=None,
                        help="an offline export of the deployed rows (CSV per table) for the semantic check")
    parser.add_argument("--live", action="store_true",
                        help="read the deployed rows via pyoso (READ-ONLY) for the semantic check")
    args = parser.parse_args()

    dataset = None
    if args.live:
        import os
        dataset = os.environ.get("OSO_DATASET", DEFAULT_DATASET)

    candidates = read_candidates(args.dir)
    problems = completeness_problems(candidates)
    if problems:
        _report("completeness", problems)
        return 2
    _report("completeness", [])

    identity = single_identity_problems(candidates)
    _report("single-identity", identity)

    semantic: list[str] = []
    if args.deployed_dir is not None or args.live:
        for table in CUTOVER_TABLES:
            if args.deployed_dir is not None:
                path = args.deployed_dir / f"{table}.csv"
                if not path.exists():
                    semantic.append(f"{table}: no deployed export at {path}")
                    continue
                deployed = _read_csv(path)
            else:
                deployed = deployed_rows(dataset, table)
            semantic.extend(semantic_no_change_problems(table, candidates[table], deployed))
        _report("semantic-no-change", semantic)
    else:
        print("semantic-no-change: skipped (no --deployed-dir or --live)")

    return 2 if (identity or semantic) else 0


if __name__ == "__main__":
    raise SystemExit(main())
