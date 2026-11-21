"""Report the scoring-trace generations the warehouse holds, and how far each one agrees.

A generation is the set of rows one publish of the scoring trace wrote: every row of
`currentai.evaluation.axis_facts`, `axis_rule_matches` and `axis_results` that carries one
`declaration_version_id`. `build/publish_scoring_trace.py` appends a generation per publish, so the
three tables hold the trace of each commit it was published from, side by side.

That history is what ADR-001 asks for before the duplicate warehouse computation
(`scores.openness_facts`, `scores.openness_computed`) can be retired: the repository-owned evaluator
has to reproduce the recorded score across several releases, and the ruling R-2026-11-08-t in
`docs/rulings/log.yaml` says which generations may count. This module makes the count readable.
A generation counts when all of these hold:

  * every row is `scored`, and every scored row has `reproduces_recorded` true. A row in any
    other status is a product the evaluator did not score, so the generation agrees on fewer
    products than it covers. The report lists those rows by product, because the ruling asks for
    each one to be reconciled or adjudicated and not waved through;
  * its `source_git_sha` is a commit reachable from the checked-out history, which is what ties
    the generation to a real state of this repository. A shallow clone cannot answer that and
    the report says so rather than guessing.

Generations are ordered by the commit date of their `source_git_sha`, read from git. The rows
carry no timestamp of their own: the trace is a deterministic function of the declarations.

This is a report. It exits 0 whatever it finds, including when the table cannot be read, so it
is safe to run after a gate without changing that gate's verdict. Retiring the warehouse
computation needs its own authorization (`docs/operations/deploy-scoring-trace.md`).

Usage:
    uv run python -m build.trace_generations          # the report
    uv run python -m build.trace_generations --json   # the same, machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = "evaluation"
TRACE_TABLES: tuple[str, ...] = ("axis_facts", "axis_rule_matches", "axis_results")

# How many complete generations R-2026-11-08-t accepts as agreement across releases.
REQUIRED_GENERATIONS = 4

# A declaration_version_id is a hex digest and a source_git_sha a git object name. Both are
# interpolated into SQL and git arguments below, so anything else is refused first.
_HEX = re.compile(r"[0-9a-f]{7,64}")


def is_hex_id(value: object) -> bool:
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def _is_true(value: object) -> bool:
    """`reproduces_recorded` as the loader returns it: a boolean, or the CSV's own "True"."""
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def _default_query(sql: str) -> list[dict]:
    from build.warehouse import query

    return query(sql)


def deployed_generations(dataset: str, table: str, run_query=_default_query) -> dict[str, dict]:
    """The generations one trace table holds: `{declaration_version_id: {source_git_sha, rows}}`.

    A table the catalog does not know yet holds none, which is the state before the first publish.
    A `declaration_version_id` that appears under two commits is not a generation this publisher
    wrote, and is reported as an error instead of being merged into one.
    """
    if table not in TRACE_TABLES:
        raise ValueError(f"{table} is not a scoring-trace table")
    try:
        rows = run_query(
            "SELECT declaration_version_id, source_git_sha, COUNT(*) AS n "
            f"FROM currentai.{dataset}.{table} GROUP BY 1, 2"
        )
    except Exception as exc:
        if "TablesNotFound" in str(exc):
            return {}
        raise
    generations: dict[str, dict] = {}
    for row in rows:
        dvid = row["declaration_version_id"]
        if dvid in generations:
            raise RuntimeError(
                f"{table}: declaration_version_id {dvid} appears under more than one source_git_sha"
            )
        generations[dvid] = {"source_git_sha": row["source_git_sha"], "rows": int(row["n"])}
    return generations


def summarize(rows: list[dict]) -> list[dict]:
    """One summary per generation from `axis_results` rows (any order, any number of generations).

    Each input row needs `declaration_version_id`, `source_git_sha`, `product_slug`,
    `category_slug`, `status` and `reproduces_recorded`. `unscored` names every row whose status is
    not `scored`, and `disagreeing` every scored row that does not reproduce the recorded score.
    """
    by_generation: dict[str, dict] = {}
    for row in rows:
        summary = by_generation.setdefault(row["declaration_version_id"], {
            "declaration_version_id": row["declaration_version_id"],
            "source_git_sha": row["source_git_sha"],
            "rows": 0, "scored": 0, "agreeing": 0, "disagreeing": [], "unscored": [],
        })
        summary["rows"] += 1
        product = f"{row['product_slug']} [{row['category_slug']}]"
        if row["status"] != "scored":
            summary["unscored"].append(f"{product}: {row['status']}")
        elif _is_true(row["reproduces_recorded"]):
            summary["scored"] += 1
            summary["agreeing"] += 1
        else:
            summary["scored"] += 1
            summary["disagreeing"].append(product)
    for summary in by_generation.values():
        summary["disagreeing"].sort()
        summary["unscored"].sort()
    return list(by_generation.values())


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def commit_facts(sha: str, root: Path = ROOT) -> dict:
    """What this checkout knows about a generation's commit.

    `identity` is `reachable` when the commit is an ancestor of HEAD, `unreachable` when git knows
    the history and the commit is not in it, and `unknown` when the clone is shallow and so cannot
    tell the two apart. `committed_at` is the commit's ISO date, or None when git cannot read it.
    """
    if not is_hex_id(sha):
        return {"identity": "unreachable", "committed_at": None}
    shallow = _git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == "true"
    is_commit = _git(root, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0
    if not is_commit:
        return {"identity": "unknown" if shallow else "unreachable", "committed_at": None}
    committed_at = _git(root, "show", "-s", "--format=%cI", sha).stdout.strip() or None
    reachable = _git(root, "merge-base", "--is-ancestor", sha, "HEAD").returncode == 0
    identity = "reachable" if reachable else ("unknown" if shallow else "unreachable")
    return {"identity": identity, "committed_at": committed_at}


def assess(summaries: list[dict], facts_for=commit_facts) -> list[dict]:
    """Attach commit facts and the `complete` verdict, oldest commit first.

    A generation whose commit date is unknown sorts last: it cannot be placed, and it does not count.
    """
    assessed = []
    for summary in summaries:
        facts = facts_for(summary["source_git_sha"])
        complete = (
            summary["rows"] > 0
            and not summary["disagreeing"]
            and not summary["unscored"]
            and facts["identity"] == "reachable"
        )
        assessed.append({**summary, **facts, "complete": complete})
    assessed.sort(key=lambda g: (g["committed_at"] is None, g["committed_at"] or "", g["declaration_version_id"]))
    return assessed


def read_generations(dataset: str = DEFAULT_DATASET, run_query=_default_query) -> list[dict]:
    """Every generation in `axis_results`, summarized. An absent table holds none."""
    try:
        rows = run_query(
            "SELECT declaration_version_id, source_git_sha, product_slug, category_slug, status, "
            f"reproduces_recorded FROM currentai.{dataset}.axis_results"
        )
    except Exception as exc:
        if "TablesNotFound" in str(exc):
            return []
        raise
    return summarize(rows)


def render(generations: list[dict], dataset: str = DEFAULT_DATASET) -> str:
    """The report as text. Lines starting `~` are observations, not failures."""
    lines = [f"scoring-trace generations in currentai.{dataset}.axis_results, oldest first"]
    if not generations:
        lines.append("  ~ none: the table is absent or empty, so no publish has landed yet")
        return "\n".join(lines)
    lines.append("")
    lines.append(f"  {'committed':10}  {'commit':12}  {'declaration':12}  {'rows':>6}  {'agree':>6}  "
                 f"{'disagree':>8}  {'unscored':>8}  identity")
    for gen in generations:
        committed = (gen["committed_at"] or "unknown")[:10]
        lines.append(
            f"  {committed:10}  {gen['source_git_sha'][:12]:12}  {gen['declaration_version_id'][:12]:12}  "
            f"{gen['rows']:>6}  {gen['agreeing']:>6}  {len(gen['disagreeing']):>8}  "
            f"{len(gen['unscored']):>8}  {gen['identity']}"
        )
    for gen in generations:
        handle = gen["source_git_sha"][:12]
        for product in gen["disagreeing"]:
            lines.append(f"  ~ {handle}: {product} is scored and does not reproduce the recorded score")
        for product in gen["unscored"]:
            lines.append(f"  ~ {handle}: {product}")
    complete = sum(1 for gen in generations if gen["complete"])
    lines.append("")
    lines.append(
        f"{len(generations)} generation(s), {complete} complete. A complete generation scores every "
        "row, reproduces every recorded score, and comes from a commit in this history."
    )
    lines.append(
        f"R-2026-11-08-t accepts {REQUIRED_GENERATIONS} complete generations as agreement across "
        "releases. Each unscored row above keeps its generation incomplete until it is reconciled "
        "or adjudicated by a ruling."
    )
    return "\n".join(lines)


def report(dataset: str = DEFAULT_DATASET, run_query=_default_query, facts_for=commit_facts) -> str:
    """Read, assess and render. A read failure becomes one `~` line: this never raises."""
    try:
        generations = assess(read_generations(dataset, run_query), facts_for)
    except Exception as exc:
        return f"  ~ scoring-trace generations could not be read: {exc}"
    return render(generations, dataset)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="the dataset holding the trace tables")
    parser.add_argument("--json", action="store_true", help="print the assessed generations as JSON")
    args = parser.parse_args()
    if args.json:
        try:
            print(json.dumps(assess(read_generations(args.dataset)), indent=2))
        except Exception as exc:
            print(json.dumps({"error": str(exc)}))
        return 0
    print(report(args.dataset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
