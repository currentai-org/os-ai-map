"""Report the scoring-trace generations the warehouse holds, and how far each one agrees.

A generation is the set of rows one publish of the scoring trace wrote: every row of
`currentai.evaluation.axis_facts`, `axis_rule_matches` and `axis_results` that carries one
`declaration_version_id`. `build/publish_scoring_trace.py` appends a generation per publish, so the
three tables hold the trace of each commit it was published from, side by side.

That history is what ADR-001 asks for before the duplicate warehouse computation
(`scores.openness_facts`, `scores.openness_computed`) can be retired: the repository-owned evaluator
has to reproduce the recorded score across several releases, and the ruling R-2026-11-08-t in
`docs/rulings/log.yaml` says which generations may count. This module makes the count readable.
A generation is complete when all of these hold:

  * every row is `scored`, and every scored row has `reproduces_recorded` true. A row in any
    other status is a product the evaluator did not score, so the generation agrees on fewer
    products than it covers;
  * its `source_git_sha` is a commit on the main line: an ancestor of `origin/main`, or of
    `HEAD` in a checkout with no such ref. That is what ties the generation to a real state of
    this repository. A shallow clone cannot answer that and the report says so rather than
    guessing.

Unscored rows are of two kinds, and the report keeps them apart. A `deferred` row is a product
its category's `scoring_recipe` declines to score, with the reason written in `sources/`; the
report prints that reason. Any other status means the ladder reached no result. A recorded reason
is not a resolution, so a deferral keeps a generation from being complete. It stops counting
against the generation only once a ruling adjudicates that product's deferral, which the report
reads from `docs/rulings/log.yaml`: an in-force entry whose `refs` carry
`phase-7-deferral:<product slug>`. The second count, complete except adjudicated deferrals, is
the generations where every deferred row has one.

Generations are ordered by the commit time of their `source_git_sha`, read from git in UTC: the
order of the source revisions, which is not the order they were published in. The loader's own
load time is printed beside it, because a commit can be published late or again.

The weekly report reads `axis_results` alone and so shows observed agreement. `--verify` is the
stronger check, and the one to run before a generation is offered as evidence for retiring the
warehouse computation: it rebuilds the trace at the generation's own commit, with that commit's
own code, and requires all three tables to hold exactly those rows, each once. That covers the
expected population, the other two tables, and the generation's identity in one comparison.

The report exits 0 whatever it finds, including when the table cannot be read, so it is safe to
run after a gate without changing that gate's verdict. `--verify` exits 1 when a generation does
not verify. Retiring the warehouse computation needs its own authorization
(`docs/operations/deploy-scoring-trace.md`).

Usage:
    uv run python -m build.trace_generations          # the report
    uv run python -m build.trace_generations --json   # the same, machine-readable
    uv run python -m build.trace_generations --verify            # every generation against a rebuild
    uv run python -m build.trace_generations --verify --last 2   # the newest two only
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = "evaluation"
TRACE_TABLES: tuple[str, ...] = ("axis_facts", "axis_rule_matches", "axis_results")

# How many complete generations R-2026-11-08-t accepts as agreement across releases.
REQUIRED_GENERATIONS = 4

# The ref a generation's commit has to be an ancestor of. A branch's HEAD lacks every commit main
# gained after the branch point, so it would call the newest generations unreachable.
MAIN_REF = "origin/main"

# The `refs` token by which a ruling adjudicates one product's deferral for the Phase 7 count.
ADJUDICATION_REF = "phase-7-deferral:"
RULINGS_LOG = ROOT / "docs" / "rulings" / "log.yaml"

# A declaration_version_id is a hex digest and a source_git_sha a git object name. Both are
# interpolated into SQL and git arguments below, so anything else is refused first.
_HEX = re.compile(r"[0-9a-f]{7,64}")


def is_hex_id(value: object) -> bool:
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def _is_true(value: object) -> bool:
    """`reproduces_recorded` as the loader returns it: a boolean, or the CSV's own "True"."""
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def canonical_scalar(value: object) -> str:
    """One string per cell, so a candidate CSV cell ("4", "True", "") and the loader's typed
    round-trip (4, True, a null) compare equal. A null arrives from pandas as None or as NaN, which
    does not equal itself. bool is handled before str() because a bool is an int."""
    if value is None or value != value:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def content_problems(table: str, candidate_rows: list[dict], stored_rows: list[dict]) -> list[str]:
    """Why the rows a table stores for one generation are not exactly the candidate's (empty = they are).

    An order-independent comparison over every candidate column, counting repeats, so a generation
    stored twice differs from one stored once. A candidate column the table lacks is tolerated only
    when the candidate leaves it empty in every row, which is the loader dropping an all-null
    column. A stored column the candidate does not declare is tolerated only when this generation
    leaves it null: an appended table keeps the columns earlier generations wrote. `_dlt_*` loader
    columns are ignored.
    """
    if not candidate_rows:
        return [f"{table}: the candidate has no rows"]
    if not stored_rows:
        return [f"{table}: the table stores no rows for this generation"]
    candidate_cols = list(candidate_rows[0])
    stored_cols = {c for row in stored_rows for c in row if not c.startswith("_dlt_")}
    problems: list[str] = []
    for column in candidate_cols:
        if column not in stored_cols and any(canonical_scalar(r.get(column)) for r in candidate_rows):
            problems.append(f"{table}: column {column!r} carries data in the candidate and is absent from the table")
    for column in sorted(stored_cols - set(candidate_cols)):
        if any(canonical_scalar(r.get(column)) for r in stored_rows):
            problems.append(f"{table}: the stored generation fills column {column!r}, which the candidate does not declare")
    if problems:
        return problems
    shared = [c for c in candidate_cols if c in stored_cols]
    wanted = Counter(tuple(canonical_scalar(r.get(c)) for c in shared) for r in candidate_rows)
    held = Counter(tuple(canonical_scalar(r.get(c)) for c in shared) for r in stored_rows)
    if wanted == held:
        return []
    missing, extra = wanted - held, held - wanted
    where = [c for c in ("product_slug", "category_slug") if c in shared]

    def example(rows: Counter) -> str:
        row = dict(zip(shared, next(iter(rows))))
        return ", ".join(f"{c}={row[c]}" for c in where) or "a row"

    if missing:
        problems.append(f"{table}: {sum(missing.values())} candidate row(s) are not stored (e.g. {example(missing)})")
    if extra:
        problems.append(f"{table}: {sum(extra.values())} stored row(s) are not the candidate's, or are stored "
                        f"more than once (e.g. {example(extra)})")
    return problems


def read_trace_csvs(directory: Path) -> dict[str, list[dict]]:
    """The three trace CSVs a builder wrote into `directory`, as rows keyed by table."""
    rows: dict[str, list[dict]] = {}
    for table in TRACE_TABLES:
        with (directory / f"{table}.csv").open(newline="", encoding="utf-8") as handle:
            rows[table] = list(csv.DictReader(handle))
    return rows


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


def stored_generation_rows(dataset: str, table: str, generation: str, run_query=_default_query) -> list[dict]:
    """Every row one trace table stores for one generation."""
    if table not in TRACE_TABLES:
        raise ValueError(f"{table} is not a scoring-trace table")
    if not is_hex_id(generation):
        raise ValueError(f"declaration_version_id {generation!r} is not a hex digest")
    return run_query(
        f"SELECT * FROM currentai.{dataset}.{table} WHERE declaration_version_id = '{generation}'"
    )


def adjudicated_deferrals(log: Path = RULINGS_LOG) -> dict[str, str]:
    """`{product slug: ruling id}` for every deferral an in-force ruling adjudicates.

    A ruling adjudicates a deferral by carrying `phase-7-deferral:<product slug>` in its `refs`.
    One ruling may name several products; each product needs its own token, so there is no
    blanket form.
    """
    if not log.exists():
        return {}
    entries = (yaml.safe_load(log.read_text()) or {}).get("rulings") or []
    found: dict[str, str] = {}
    for entry in entries:
        if entry.get("status") != "in-force":
            continue
        for ref in entry.get("refs") or []:
            if isinstance(ref, str) and ref.startswith(ADJUDICATION_REF):
                found[ref[len(ADJUDICATION_REF):]] = entry["id"]
    return found


def summarize(rows: list[dict]) -> list[dict]:
    """One summary per generation from `axis_results` rows (any order, any number of generations).

    Each input row needs `declaration_version_id`, `source_git_sha`, `product_slug`,
    `category_slug`, `status` and `reproduces_recorded`; `deferral_reason` is read when present.
    `deferred` names every declared deferral with its reason, `undecided` every other row whose
    status is not `scored`, and `disagreeing` every scored row that does not reproduce the
    recorded score.
    """
    by_generation: dict[str, dict] = {}
    for row in rows:
        summary = by_generation.setdefault(row["declaration_version_id"], {
            "declaration_version_id": row["declaration_version_id"],
            "source_git_sha": row["source_git_sha"],
            "rows": 0, "scored": 0, "agreeing": 0, "disagreeing": [], "deferred": [], "undecided": [],
            "deferred_slugs": [], "loaded_at": None,
        })
        load_id = row.get("_dlt_load_id")
        if isinstance(load_id, str) and (summary["loaded_at"] is None or load_id < summary["loaded_at"]):
            summary["loaded_at"] = load_id
        summary["rows"] += 1
        product = f"{row['product_slug']} [{row['category_slug']}]"
        if row["status"] == "deferred":
            # A null arrives from pandas as NaN, which is truthy, so test for a string.
            reason = row.get("deferral_reason")
            reason = (reason.strip() if isinstance(reason, str) else "") or "no reason recorded"
            summary["deferred"].append(f"{product}: {reason}")
            summary["deferred_slugs"].append(row["product_slug"])
        elif row["status"] != "scored":
            summary["undecided"].append(f"{product}: {row['status']}")
        elif _is_true(row["reproduces_recorded"]):
            summary["scored"] += 1
            summary["agreeing"] += 1
        else:
            summary["scored"] += 1
            summary["disagreeing"].append(product)
    for summary in by_generation.values():
        for key in ("disagreeing", "deferred", "undecided", "deferred_slugs"):
            summary[key].sort()
        summary["loaded_at"] = _load_time(summary["loaded_at"])
    return list(by_generation.values())


def _load_time(load_id: str | None) -> str | None:
    """The loader's load id is the epoch second the load began; as an ISO time in UTC, or None."""
    try:
        return datetime.fromtimestamp(float(load_id), timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError):
        return None


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def commit_facts(sha: str, root: Path = ROOT) -> dict:
    """What this checkout knows about a generation's commit.

    `identity` is `reachable` when the commit is an ancestor of the main line (`origin/main`, or
    HEAD where that ref does not exist), `unreachable` when git knows the history and the commit
    is not in it, and `unknown` when the clone is shallow and so cannot tell the two apart.
    `committed_at` is the commit time as an ISO string in UTC, so two of them compare in time
    order as strings, or None when git cannot read it.
    """
    if not is_hex_id(sha):
        return {"identity": "unreachable", "committed_at": None}
    shallow = _git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == "true"
    is_commit = _git(root, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0
    if not is_commit:
        return {"identity": "unknown" if shallow else "unreachable", "committed_at": None}
    epoch = _git(root, "show", "-s", "--format=%ct", sha).stdout.strip()
    committed_at = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat() if epoch.isdigit() else None
    has_main = _git(root, "rev-parse", "--verify", "--quiet", f"{MAIN_REF}^{{commit}}").returncode == 0
    reachable = _git(root, "merge-base", "--is-ancestor", sha, MAIN_REF if has_main else "HEAD").returncode == 0
    identity = "reachable" if reachable else ("unknown" if shallow else "unreachable")
    return {"identity": identity, "committed_at": committed_at}


def assess(summaries: list[dict], facts_for=commit_facts, adjudicated: dict[str, str] | None = None) -> list[dict]:
    """Attach commit facts and the two verdicts, oldest commit first.

    `complete_except_adjudicated` holds for every complete generation, and for one whose only
    unscored rows are deferrals that a ruling has each adjudicated (`adjudicated`, by product
    slug). A declared deferral with no ruling keeps it false. A generation whose commit date is
    unknown sorts last: it cannot be placed, and it does not count.
    """
    adjudicated = adjudicated_deferrals() if adjudicated is None else adjudicated
    assessed = []
    for summary in summaries:
        facts = facts_for(summary["source_git_sha"])
        agrees = (
            summary["rows"] > 0
            and not summary["disagreeing"]
            and not summary["undecided"]
            and facts["identity"] == "reachable"
        )
        unadjudicated = [slug for slug in summary["deferred_slugs"] if slug not in adjudicated]
        assessed.append({
            **summary, **facts,
            "unadjudicated": unadjudicated,
            "complete": agrees and not summary["deferred"],
            "complete_except_adjudicated": agrees and not unadjudicated,
        })
    assessed.sort(key=lambda g: (g["committed_at"] is None, g["committed_at"] or "", g["declaration_version_id"]))
    return assessed


def read_generations(dataset: str = DEFAULT_DATASET, run_query=_default_query) -> list[dict]:
    """Every generation in `axis_results`, summarized. An absent table holds none."""
    try:
        # Every column, not a named list: the loader drops a column that is null in every row,
        # so `deferral_reason` is absent from a table that has never held a deferral.
        rows = run_query(f"SELECT * FROM currentai.{dataset}.axis_results")
    except Exception as exc:
        if "TablesNotFound" in str(exc):
            return []
        raise
    return summarize(rows)


def render(generations: list[dict], dataset: str = DEFAULT_DATASET) -> str:
    """The report as text. Lines starting `~` are observations, not failures."""
    lines = [f"scoring-trace generations in currentai.{dataset}.axis_results, by source commit, oldest first"]
    if not generations:
        lines.append("  ~ none: the table is absent or empty, so no publish has landed yet")
        return "\n".join(lines)
    lines.append("")
    lines.append(f"  {'committed':10}  {'commit':12}  {'declaration':12}  {'loaded':16}  {'rows':>6}  {'agree':>6}  "
                 f"{'disagree':>8}  {'deferred':>8}  {'undecided':>9}  identity")
    for gen in generations:
        committed = (gen["committed_at"] or "unknown")[:10]
        loaded = (gen["loaded_at"] or "unknown")[:16].replace("T", " ")
        lines.append(
            f"  {committed:10}  {gen['source_git_sha'][:12]:12}  {gen['declaration_version_id'][:12]:12}  "
            f"{loaded:16}  {gen['rows']:>6}  {gen['agreeing']:>6}  {len(gen['disagreeing']):>8}  "
            f"{len(gen['deferred']):>8}  {len(gen['undecided']):>9}  {gen['identity']}"
        )
    for gen in generations:
        handle = gen["source_git_sha"][:12]
        for product in gen["disagreeing"]:
            lines.append(f"  ~ {handle}: {product} is scored and does not reproduce the recorded score")
        for product in gen["undecided"]:
            lines.append(f"  ~ {handle}: {product} (the ladder reached no result)")
        for product in gen["deferred"]:
            slug = product.split(" ", 1)[0]
            state = "not adjudicated" if slug in gen["unadjudicated"] else "adjudicated"
            lines.append(f"  ~ {handle}: deferred, {state}: {product}")
    complete = sum(1 for gen in generations if gen["complete"])
    adjudicated = sum(1 for gen in generations if gen["complete_except_adjudicated"])
    lines.append("")
    lines.append(
        f"{len(generations)} generation(s): {complete} complete, {adjudicated} complete except "
        "adjudicated deferrals. A complete generation scores every row, reproduces every recorded "
        "score, and comes from a commit on the main line."
    )
    lines.append(
        f"R-2026-11-08-t accepts {REQUIRED_GENERATIONS} complete generations as agreement across "
        "releases. A deferral counts against its generation until a ruling adjudicates that product's "
        f"deferral (`{ADJUDICATION_REF}<slug>` in the ruling's refs). These counts read axis_results "
        "alone; --verify checks a generation's population and its other two tables."
    )
    return "\n".join(lines)


def rebuild_at(sha: str, out_dir: Path, root: Path = ROOT) -> None:
    """Write the trace CSVs for commit `sha` into `out_dir`, built by that commit's own code.

    The commit is checked out into a temporary worktree and its own `build.axis_scoring_trace` is
    run there, so the rows are what that revision of the evaluator produces from that revision of
    the declarations, whatever either has become since.
    """
    if not is_hex_id(sha):
        raise ValueError(f"source_git_sha {sha!r} is not a git object name")
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        added = _git(root, "worktree", "add", "--detach", str(tree), sha)
        if added.returncode != 0:
            raise RuntimeError(f"cannot check out {sha[:12]}: {added.stderr.strip()[:300]}")
        try:
            built = subprocess.run(
                ["uv", "run", "python", "-m", "build.axis_scoring_trace", "--out", str(out_dir)],
                cwd=tree, capture_output=True, text=True, check=False,
            )
            if built.returncode != 0:
                raise RuntimeError(f"the builder at {sha[:12]} failed: {built.stderr.strip()[-400:]}")
        finally:
            _git(root, "worktree", "remove", "--force", str(tree))


def verify_generation(generation: dict, dataset: str = DEFAULT_DATASET, run_query=_default_query,
                      rebuild=rebuild_at) -> list[str]:
    """Why a stored generation is not exactly the trace its own commit produces (empty = it is).

    Rebuilds the trace at the generation's commit and requires, in each of the three tables, that
    the stored rows are the rebuilt rows, each once. The rebuilt rows carry the
    `declaration_version_id` that commit derives, so a stored generation under any other id, a
    table that lacks the generation, a missing or extra product, and a repeated load all fail here.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        try:
            rebuild(generation["source_git_sha"], out_dir)
            rebuilt = read_trace_csvs(out_dir)
        except (RuntimeError, ValueError, OSError) as exc:
            return [f"could not rebuild the trace at its commit: {exc}"]
    problems: list[str] = []
    for table in TRACE_TABLES:
        stored = stored_generation_rows(dataset, table, generation["declaration_version_id"], run_query)
        problems.extend(content_problems(table, rebuilt[table], stored))
    return problems


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
    parser.add_argument("--verify", action="store_true",
                        help="rebuild each generation at its own commit and compare all three tables; "
                             "exits 1 when one does not verify")
    parser.add_argument("--last", type=int, metavar="N",
                        help="with --verify, check only the N generations with the newest source commits")
    args = parser.parse_args()
    if args.verify:
        generations = assess(read_generations(args.dataset))
        chosen = generations[-args.last:] if args.last else generations
        failed = 0
        for gen in chosen:
            handle = f"{gen['source_git_sha'][:12]} ({gen['declaration_version_id'][:12]})"
            if gen["identity"] != "reachable":
                failed += 1
                print(f"  x {handle}: its commit is {gen['identity']} from the main line, so there is nothing to rebuild from")
                continue
            problems = verify_generation(gen, args.dataset)
            if problems:
                failed += 1
                print(f"  x {handle}: does not match a rebuild at its commit")
                for problem in problems:
                    print(f"      {problem}")
            else:
                print(f"  ok {handle}: all three tables hold exactly the trace its commit produces")
        print(f"{len(chosen) - failed} of {len(chosen)} generation(s) verified")
        return 1 if failed else 0
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
