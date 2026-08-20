"""Read and verify `warehouse/assets.yaml`, the architecture asset inventory.

The inventory records what each data asset IS. This module derives what each asset
READS and IS READ BY, from the tree rather than from the file, so the two can be
compared. A hand-maintained dependency list drifts exactly like the two registries
assets.yaml replaced -- `warehouse/sources.yaml` and
`warehouse/platform-mirror/manifest.yaml` disagreed with each other for weeks.

Platform facts (cron, timezone, model revision, last observed trigger) are DECLARED
here and captured at audit time, because CI has no platform credentials. Nothing in
this module proves a platform fact is still true; that needs the credentialed job
described in docs/architecture/data-architecture.md section 11.5 check 4.
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "warehouse" / "assets.yaml"

# Closure roots, per data-architecture.md 11.3. `build/` is a root: seven modules
# there read currentai tables directly, and omitting them reports every table they
# read as unconsumed -- which would have made check_parity's own inputs look like
# retirement candidates.
ROOTS = {
    # All 30 SQL/Python model files, which live in three directories until the
    # restructure lands: 12 in models/, 15 mirrored, 3 fetchers. Globbing only
    # models/ reports registry.products as unread -- it is read by the mirrored
    # scores_openness_facts.sql -- and that made fourteen load-bearing tables
    # look like retirement candidates.
    "models": [
        "warehouse/models/*.sql", "warehouse/models/*.py",
        "warehouse/platform-mirror/*.sql", "warehouse/platform-mirror/*.py",
        "warehouse/ingest/*.py",
    ],
    "build": ["build/*.py"],
    "notebooks": ["notebooks/*.py"],
    "workflows": [".github/workflows/*.yml"],
}

TABLE_RE = re.compile(r"\bcurrentai\.([a-z_]+)\.([a-z_0-9]+)")
EXTERNAL_RE = re.compile(r"\b(oso\.[a-z_0-9]+)")


def _uncommented(path: Path) -> str:
    """Source with prose removed: comment lines, and Python docstrings.

    Prose names a table as often as code does. `build/check_rubric.py` names a scores
    table in a comment and queries nothing; three workflow files discuss tables they
    never touch. Counting those invents consumers, which is the failure this inventory
    exists to prevent.

    Docstrings need stripping too, and this module is the proof -- an earlier version
    read its own explanatory docstring and reported itself as a consumer of the table
    that docstring names.

    Only DOCSTRINGS are stripped, never all string literals: several build modules hold
    real SQL in strings, and those reads are genuine.
    """
    src = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".py":
        src = _without_docstrings(src)
    marker = "--" if path.suffix == ".sql" else "#"
    return "\n".join(
        line for line in src.splitlines() if not line.lstrip().startswith(marker)
    )


def _without_docstrings(src: str) -> str:
    """Blank out docstring bodies, preserving line numbering."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return src
    lines = src.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            continue
        for i in range(first.lineno - 1, min(first.end_lineno, len(lines))):
            lines[i] = ""
    return "\n".join(lines)


def tracked_files(patterns: list[str]) -> list[Path]:
    """Git-tracked files matching any pattern.

    Deliberately NOT a filesystem glob. `notebooks/` holds untracked local copies of
    platform notebooks -- france-ecosystem.py and launch-insights.py are both on disk
    and neither is in the repository. Globbing the filesystem makes the derived graph
    depend on what happens to be in a working tree, so the same commit would produce
    different inventories for different people and for CI.
    """
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", *patterns],
        capture_output=True, text=True, check=True,
    ).stdout
    return sorted(ROOT / rel for rel in out.split("\0") if rel)


def reads_of(path: Path) -> tuple[set[str], set[str]]:
    """Return (internal currentai tables, external tables) this file reads."""
    src = _uncommented(path)
    internal = {f"{ds}.{tbl}" for ds, tbl in TABLE_RE.findall(src)}
    return internal, set(EXTERNAL_RE.findall(src))


def derive_graph() -> dict:
    """Derive reads and read_by across every closure root."""
    reads: dict[str, dict] = {}
    read_by: dict[str, dict[str, list[str]]] = {}
    for root, patterns in ROOTS.items():
        for path in tracked_files(patterns):
            rel = str(path.relative_to(ROOT))
            internal, external = reads_of(path)
            if internal or external:
                reads[rel] = {"internal": sorted(internal), "external": sorted(external)}
            for table in internal:
                read_by.setdefault(table, {}).setdefault(root, []).append(rel)
    for table in read_by:
        for root in read_by[table]:
            read_by[table][root].sort()
    return {"reads": reads, "read_by": read_by}


def load() -> dict:
    return yaml.safe_load(ASSETS.read_text(encoding="utf-8"))


def assets() -> list[dict]:
    return load()["assets"]


def by_table() -> dict[str, dict]:
    return {a["table"].removeprefix("currentai."): a for a in assets()}


def produced_files() -> dict[str, str]:
    """Map every managed file path to the asset id that claims it.

    An asset owns several files -- a mirrored model has SQL and a schema, a fetcher
    has code and the CSV it writes. A singular `file` cannot satisfy both "every
    managed file appears exactly once" and "one entry per table".
    """
    owned: dict[str, str] = {}
    for asset in assets():
        for role, path in (asset.get("files") or {}).items():
            if path:
                owned.setdefault(path, f"{asset['id']}:{role}")
    return owned


def retirement_candidates() -> list[dict]:
    """Assets that satisfy every retirement precondition.

    An empty reader list is NOT sufficient. A table whose purpose is external
    consumption correctly has no in-repo reader -- `releases.manifest` would be the
    first false positive. And an asset nobody has checked beyond the repository is
    not evidence of anything, which is what `consumer_scope` guards.
    """
    out = []
    for asset in assets():
        rb = asset.get("read_by") or {}
        if any(rb.get(root) for root in ROOTS):
            continue
        if asset.get("publication_role"):
            continue
        if asset.get("external_consumers") != "none_confirmed":
            continue
        if asset.get("consumer_scope") == "in_repo_only":
            continue
        out.append(asset)
    return out


def render_dag() -> str:
    """Render the current-state dependency graph as Mermaid, from the derived edges.

    Generated, never drawn. A hand-drawn DAG of 56 assets is wrong within a week, and the
    point of this document is to be checkable against the tree.
    """
    graph = derive_graph()
    inv = by_table()
    lines = ["```mermaid", "graph LR"]
    ns_of = lambda t: t.split(".")[0]
    namespaces: dict[str, set[str]] = {}
    for table in inv:
        namespaces.setdefault(ns_of(table), set()).add(table)
    for ns, tables in sorted(namespaces.items()):
        lines.append(f"  subgraph {ns}")
        for t in sorted(tables):
            node = t.replace(".", "__")
            lines.append(f"    {node}[{t.split('.', 1)[1]}]")
        lines.append("  end")
    seen = set()
    for path, refs in sorted(graph["reads"].items()):
        producer = None
        for asset in assets():
            if (asset.get("files") or {}).get("model") == path:
                producer = asset["id"]
                break
        if not producer:
            continue
        for upstream in refs["internal"]:
            if upstream == producer or upstream not in inv:
                continue
            edge = (upstream, producer)
            if edge in seen:
                continue
            seen.add(edge)
            lines.append(f"  {upstream.replace('.', '__')} --> {producer.replace('.', '__')}")
    lines.append("```")
    return "\n".join(lines)
