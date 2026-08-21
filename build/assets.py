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
    # All 30 SQL/Python model files now live under warehouse/models/<dataset>/, the
    # repository mirroring the warehouse. One glob covers editable, mirror and fetcher
    # files alike -- authority is a declared field in assets.yaml, not a directory name.
    # The enumeration stays `git ls-files` rather than a filesystem glob (see
    # tracked_files) so the derived graph does not depend on a working tree.
    "models": [
        "warehouse/models/**/*.sql", "warehouse/models/**/*.py",
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
    """Remove SQL comments, including inline ones, without touching quoted text.

    A line-oriented stripper is not enough: `SELECT 1 -- FROM currentai.registry.products`
    keeps the comment and invents a dependency. Nor is a plain regex, because `--` occurs
    inside values -- `SELECT '--' AS dash FROM t` must not lose the rest of its line.

    So this scans character by character, tracking whether it sits inside a single- or
    double-quoted run. Doubled quotes escape within a quoted run, per SQL.
    """
    out: list[str] = []
    i, n = 0, len(sql)
    quote: str | None = None
    while i < n:
        ch = sql[i]
        if quote:
            out.append(ch)
            if ch == quote:
                if i + 1 < n and sql[i + 1] == quote:   # doubled quote escapes itself
                    out.append(sql[i + 1])
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if sql.startswith("--", i):
            while i < n and sql[i] != "\n":
                i += 1
            continue
        if sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = n if end == -1 else end + 2
            out.append(" ")
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _unquote_identifiers(sql: str) -> str:
    """Normalize Trino quoted identifiers: "a"."b"."c" becomes a.b.c.

    This is the form the Python mirror models actually use. Matching only the unquoted
    form missed every one of them; the dependencies looked present because several files
    also carry the bare name in a separate constant, which is luck, not extraction.

    Safe because Trino quotes identifiers with double quotes and string literals with
    single quotes, so this cannot rewrite a value.
    """
    return re.sub(r'"([a-z_][a-z_0-9]*)"', r"\1", sql, flags=re.IGNORECASE)


def _refs_in_sql(sql: str) -> set[str]:
    return set(SQL_CONTEXT_RE.findall(_unquote_identifiers(_sql_comments_stripped(sql))))


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


# Escape hatch for a dependency no parser can see -- a table name assembled at runtime,
# or read through a helper. Declared as a comment in either language:
#   -- depends_on: currentai.registry.products
#   # depends_on: currentai.registry.products
# Deliberately a declaration rather than a heuristic: a parser that guessed this well
# enough to be trusted would also guess wrong somewhere, silently.
DEPENDS_ON_RE = re.compile(
    r"^\s*(?:--|#)\s*depends_on:\s*(" + QUALIFIED + r")\s*$", re.IGNORECASE | re.MULTILINE
)


def table_refs(path: Path) -> set[str]:
    """Fully-qualified tables this file queries."""
    src = path.read_text(encoding="utf-8", errors="replace")
    declared = set(DEPENDS_ON_RE.findall(src))
    if path.suffix == ".sql":
        return _refs_in_sql(src) | declared
    if path.suffix == ".py":
        return _refs_in_python(src) | declared
    return declared


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


# The mirror layout makes the fully-qualified table name derivable from the path:
# warehouse/models/<dataset>/<table>.<ext> is currentai.<dataset>.<table>, and
# warehouse/data/<dataset>/<table>.csv is the same table's frozen bytes. This replaces
# the old filename-convention check (11.5 gate 1b): a misplaced file now fails rather
# than being accepted under a plausible name.
_MODEL_ROOTS = ("warehouse/models/", "warehouse/data/")


def table_for_path(path: str) -> str | None:
    """The `currentai.<dataset>.<table>` a mirror-layout path derives, or None.

    None for anything that is not a `<dataset>/<table>` file under models/ or data/ --
    intermediate CSVs (data/catalog/top_models.csv) share a directory with a table but
    are a fetcher's scratch input, not a table, so they carry no derivable identity and
    the caller skips them by role rather than by guessing here.
    """
    for prefix in _MODEL_ROOTS:
        if path.startswith(prefix):
            rest = path[len(prefix):]
            if rest.endswith(".schema.json"):
                rest = rest[: -len(".schema.json")]
            else:
                rest = rest.rsplit(".", 1)[0]
            parts = rest.split("/")
            if len(parts) == 2:
                return f"currentai.{parts[0]}.{parts[1]}"
    return None


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
    not evidence of anything, which is what `consumer_checks` guards.
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


def merge_base_assets(base: str = "origin/main") -> list[dict] | None:
    """The inventory as of the merge base, or None if it did not exist there.

    A provenance gate that reads only the current tree cannot detect the case it exists
    for: a contributor edits a mirrored file and updates `local_sha256` to match. Both
    values agree, every single-snapshot check passes, and the recorded platform revision
    now dates bytes it never saw. Catching that needs the previous value.
    """
    try:
        merge_base = subprocess.run(
            ["git", "-C", str(ROOT), "merge-base", "HEAD", base],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{merge_base}:warehouse/assets.yaml"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return (yaml.safe_load(blob) or {}).get("assets") or []


def mirror_provenance_violations(base: str = "origin/main") -> list[str]:
    """Mirror entries whose bytes moved without their provenance moving with them.

    When a mirrored file's `local_sha256` changes, the platform revision it claims to
    mirror must change too -- `revision`, `hash` and `synced_at` all move together, and
    only for the entry whose file actually changed. `synced_at` is per entry for exactly
    this reason: it was one global date until 2026-08-16, which meant refetching two
    models advanced the date on all twelve.
    """
    before = merge_base_assets(base)
    if before is None:
        return []
    old = {a["id"]: a for a in before if a.get("mirror")}
    problems: list[str] = []
    for asset in assets():
        mirror = asset.get("mirror")
        was = old.get(asset["id"])
        if not mirror or not was or not was.get("mirror"):
            continue
        prior = was["mirror"]
        # model_id identifies WHICH deployed model is mirrored. Changing it silently
        # repoints the entry at a different model while the bytes and provenance look
        # untouched, so it is stable unless mirror_migration explains the change.
        if mirror.get("model_id") != prior.get("model_id"):
            if not asset.get("mirror_migration"):
                problems.append(
                    f"{asset['id']}: model_id changed from {prior.get('model_id')} to "
                    f"{mirror.get('model_id')} with no mirror_migration authorizing it"
                )

        if mirror.get("local_sha256") == prior.get("local_sha256"):
            if any(mirror.get(f) != prior.get(f) for f in ("revision", "hash", "synced_at")):
                problems.append(
                    f"{asset['id']}: provenance changed but the mirrored bytes did not"
                )
            continue

        # Bytes moved, so a refetch happened. Everything that dates the refetch moves with
        # it, and forward: an equal value means the provenance was not updated, and a lower
        # one means it was rolled back while presenting as current.
        old_rev, new_rev = prior.get("revision"), mirror.get("revision")
        if isinstance(old_rev, int) and isinstance(new_rev, int):
            if new_rev <= old_rev:
                problems.append(
                    f"{asset['id']}: bytes changed but revision went {old_rev} -> {new_rev}; "
                    "a refetch advances it"
                )
        elif new_rev == old_rev:
            problems.append(f"{asset['id']}: bytes changed but revision did not")

        if mirror.get("hash") == prior.get("hash"):
            problems.append(f"{asset['id']}: bytes changed but the platform hash did not")

        # synced_at is date-granular, so a same-day refetch legitimately keeps its value.
        # Only a backward move is a defect.
        old_at, new_at = str(prior.get("synced_at") or ""), str(mirror.get("synced_at") or "")
        if new_at < old_at:
            problems.append(
                f"{asset['id']}: synced_at moved backward, {old_at} -> {new_at}"
            )
    return problems


COUNT_CLAIMS = {
    "assets": lambda: len(assets()),
    "pending": lambda: sum(1 for a in assets() if a["migration_status"] == "pending"),
    "no_reviewed_consumer": lambda: len(no_reviewed_consumers()),
    "deployed_tables": lambda: len(deployed_tables()),
    "staged_assets": lambda: sum(1 for a in assets() if a["status"] == "staged"),
    "dormant_assets": lambda: sum(1 for a in assets() if a["status"] == "dormant"),
    "tracked_warehouse_files": lambda: len(subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "warehouse"],
        capture_output=True, text=True, check=True,
    ).stdout.split()),
    "catalog_tables": lambda: sum(1 for a in assets() if a["current_namespace"] == "catalog"),
    "model_files": lambda: len(
        [f for f in produced_files() if f.endswith((".sql", ".py"))]
    ),
    "retirement_candidates": lambda: len(retirement_candidates()),
    "in_repo_readers": lambda: len(derive_graph()["read_by"]),
    "unobserved_crons": lambda: sum(
        1 for a in assets()
        if str(a.get("refresh", "")).startswith("dataset cron")
        and a.get("last_observed_trigger") is None
    ),
}

COUNT_MARKER_RE = re.compile(r"<!--\s*count:([a-z_]+)\s*-->\s*(\d+)")


def count_claim_violations() -> list[str]:
    """Check every marked count in the architecture docs against its derived value.

    Marked, not sniffed. An earlier gate scanned prose for a denylist of numbers that had
    already been wrong -- 49, 28, 56 -- which by construction could not catch the next one,
    and did not catch a stale 31 against an actual 34. A count in prose now carries a marker
    naming what it counts, and anything unmarked is invisible to the reader as well.
    """
    problems: list[str] = []
    for path in sorted((ROOT / "docs" / "architecture").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for key, written in COUNT_MARKER_RE.findall(text):
            if key not in COUNT_CLAIMS:
                problems.append(f"{path.name}: unknown count key {key!r}")
                continue
            actual = COUNT_CLAIMS[key]()
            if int(written) != actual:
                problems.append(f"{path.name}: {key} says {written}, derived value is {actual}")
    return problems


def no_reviewed_consumers() -> list[dict]:
    """Assets with no consumer among the sources actually reviewed.

    Derived from the predicate, not read from an authored label. `retirement_reason` is
    prose a generator wrote; counting rows that carry it verifies nothing, because the
    same condition produced both. This recomputes it independently so the two can
    disagree and a gate can notice.

    Weaker than `retirement_candidates`, which additionally requires every consumer
    source to have been checked. This says only: nothing we looked at reads it.
    """
    return [
        a for a in assets()
        if not (a.get("read_by") or {})
        and not a.get("publication_role")
        and a.get("external_consumers") == "none_confirmed"
    ]


def deployed_tables() -> list[dict]:
    """Assets that exist as a table on the platform today.

    The inventory is larger than the platform, deliberately: it also holds staged models
    that are not deployed and dormant outputs whose table is absent only because the last
    serialization was empty. Both are real logical assets -- a file in no asset entry is
    invisible to every gate -- but neither is current deployed state, and a count that
    mixes them misrepresents the warehouse.
    """
    return [a for a in assets() if a["status"] not in ("staged", "dormant")]
