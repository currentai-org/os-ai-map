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

NAMESPACES = {"registry", "catalog", "observations", "evaluation", "releases"}
STATUSES = {"active", "staged", "deprecated", "historical", "compatibility", "dormant"}
MIGRATION_STATES = {"pending", "in_progress", "complete", "not_planned"}
CHECK_STATES = {"checked", "unknown", "not_applicable"}
AUTHORITIES = {"repo", "platform", "external"}
POPULATIONS = {"gap_map", "long_tail", "both"}
REQUIRED_FIELDS = (
    "id", "table", "kind", "current_namespace", "target_namespace", "migration_status",
    "authority", "grain", "producer", "population", "release_path", "consumer_checks",
    "refresh", "owner", "status", "verified_at",
)
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

# A table reference counts only in SQL context: after FROM / JOIN / INTO / UPDATE, or as
# a bare table identifier that IS the whole string (the `TABLE = "..."` constant pattern).
#
# Matching bare dotted names anywhere invents tables. `@oso.model` is the decorator every
# Python UDM carries and produced a phantom `oso.model` upstream in seven files;
# `https://www.oso.xyz/...` produced `oso.xyz` in five more. A denylist for those two would
# only grow, so the rule is positive: a reference must look like it is being queried.
QUALIFIED = r"(?:currentai|oso)\.[a-z_][a-z_0-9]*(?:\.[a-z_][a-z_0-9]*)?"
SQL_CONTEXT_RE = re.compile(
    r"\b(?:from|join|into|update)\s+(" + QUALIFIED + r")\b", re.IGNORECASE
)
BARE_IDENTIFIER_RE = re.compile(r"^\s*(" + QUALIFIED + r")\s*$")
SQL_HINT_RE = re.compile(r"\b(?:select|from|join|with|insert|update)\b", re.IGNORECASE)


def _sql_comments_stripped(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )


def _refs_in_sql(sql: str) -> set[str]:
    return set(SQL_CONTEXT_RE.findall(_sql_comments_stripped(sql)))


def _string_literals(src: str) -> list[str]:
    """Every string constant in a Python module, docstrings excluded.

    Docstrings are prose and name tables freely -- `build/warehouse.py` illustrates its
    own API with a SELECT in its module docstring, which is not a query. Other literals
    are where the real SQL lives, so they are read rather than skipped.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    docstrings = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                    and isinstance(first.value.value, str):
                docstrings.add(id(first.value))
    return [
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings
    ]


def _refs_in_python(src: str) -> set[str]:
    found: set[str] = set()
    for literal in _string_literals(src):
        bare = BARE_IDENTIFIER_RE.match(literal)
        if bare:
            found.add(bare.group(1))
            continue
        if SQL_HINT_RE.search(literal):
            found |= _refs_in_sql(literal)
    return found


def table_refs(path: Path) -> set[str]:
    """Fully-qualified tables this file queries."""
    src = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".sql":
        return _refs_in_sql(src)
    if path.suffix == ".py":
        return _refs_in_python(src)
    return set()


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
    """Return (internal currentai tables, external tables) this file queries."""
    refs = table_refs(path)
    internal = {r.removeprefix("currentai.") for r in refs if r.startswith("currentai.")}
    external = {r for r in refs if not r.startswith("currentai.")}
    return internal, external


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
        for role, value in (asset.get("files") or {}).items():
            for path in (value if isinstance(value, list) else [value]):
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
        # The specification's condition includes "no deployed platform model reads it".
        # Notebooks are not models. Until platform model definitions are audited, an
        # asset cannot be a retirement candidate however unread it looks.
        checks = asset.get("consumer_checks") or {}
        if any(checks.get(k) != "checked" for k in ("repository", "platform_notebooks", "platform_models")):
            continue
        out.append(asset)
    return out


def render_dag() -> str:
    """Render the current-state dependency graph as Mermaid, from the derived edges.

    Generated, never drawn: a hand-drawn graph of 57 assets is wrong within a week, and a
    generated document that drifts from its generator is worse than no document. A gate
    compares this output against the committed copy.

    The graph carries three things beyond table-to-table edges, because without them it is
    a table-dependency diagram wearing a DAG's name: external upstreams, in-repo consumers
    that are not themselves assets, and node status.
    """
    graph = derive_graph()
    inv = by_table()
    producer_of = {
        (a.get("files") or {}).get("model"): a["id"]
        for a in assets() if (a.get("files") or {}).get("model")
    }
    out = ["```mermaid", "graph LR"]

    namespaces: dict[str, list[str]] = {}
    for table in sorted(inv):
        namespaces.setdefault(table.split(".")[0], []).append(table)
    for ns, tables in sorted(namespaces.items()):
        out.append(f"  subgraph {ns}")
        for table in tables:
            out.append(f"    {table.replace('.', '__')}[{table.split('.', 1)[1]}]")
        out.append("  end")

    external: set[str] = set()
    consumers: set[tuple[str, str]] = set()
    edges: set[tuple[str, str]] = set()
    for path, refs in sorted(graph["reads"].items()):
        producer = producer_of.get(path)
        for upstream in refs["internal"]:
            if upstream not in inv:
                continue
            if producer and upstream != producer:
                edges.add((upstream.replace(".", "__"), producer.replace(".", "__")))
            elif not producer:
                consumers.add((upstream.replace(".", "__"), path))
        for ext in refs["external"]:
            external.add(ext)
            if producer:
                edges.add((f"EXT_{ext.replace('.', '__')}", producer.replace(".", "__")))

    if external:
        out.append("  subgraph external")
        for ext in sorted(external):
            out.append(f"    EXT_{ext.replace('.', '__')}[{ext}]:::ext")
        out.append("  end")
    if consumers:
        out.append("  subgraph consumers")
        for _, path in sorted(consumers):
            out.append(f"    C_{path.replace('/', '_').replace('.', '_')}[{path}]:::consumer")
        out.append("  end")

    for a, b in sorted(edges):
        out.append(f"  {a} --> {b}")
    for table, path in sorted(consumers):
        out.append(f"  {table} --> C_{path.replace('/', '_').replace('.', '_')}")

    for asset in assets():
        if asset["status"] != "active":
            out.append(f"  class {asset['id'].replace('.', '__')} {asset['status']};")
    out += [
        "  classDef staged stroke-dasharray: 4 3;",
        "  classDef compatibility stroke-width:3px;",
        "  classDef dormant opacity:0.5;",
        "  classDef ext fill:#eee;",
        "  classDef consumer fill:#fff,stroke-dasharray: 2 2;",
        "```",
    ]
    return "\n".join(out)
