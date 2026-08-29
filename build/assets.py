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

# ADR-003 repository role. Membership is ASSERTED by this field, not inferred from the
# graph. A governed asset carries exactly one role; the externalization backlog (the
# peripheral assets ADR-003 slates for ownership transfer) is deliberately ROLELESS until
# it leaves, so `role` is optional this PR and becomes required once the backlog is empty.
#   governed-output   a published Gap Map artifact whose schema + publication lifecycle
#                     are owned here (must be release_path: true)
#   repo-computation  repo-defined SQL/Python/data implementing or auditing map semantics
#                     (has a repo file or a build/ producer; a platform-authored MIRROR
#                     counts -- the repo owns the tracked definition, ADR-003 wording
#                     refined from "authority: repo" to admit mirrors of deployed models)
#   compatibility-shim  a temporary shim for a (1)/(2) asset (carries `replacement`;
#                     named to avoid collision with the lifecycle `status: compatibility`)
ROLES = {"governed-output", "repo-computation", "compatibility-shim"}

# ADR-003 step 6: the four `gap_map` tables that do not participate in the canonical map
# pipeline (all release_path: false) and externalize individually. Held ROLELESS in the
# backlog with the 24 `long_tail` assets until step 5/6 removes them. Named explicitly
# because they are gap_map -- population alone cannot distinguish them from governed assets.
EXTERNALIZE_QUESTIONABLE = frozenset({
    "catalog.stack_map",
    "scores.stack_contributors",
    "signal_artificialanalysis.model_evaluations",
    "signal_lmarena.text_leaderboard",
})

REQUIRED_FIELDS = (
    "id", "table", "kind", "current_namespace", "target_namespace", "migration_status",
    "authority", "grain", "producer", "population", "release_path", "consumer_checks",
    "refresh", "owner", "status", "verified_at",
)
ASSETS = ROOT / "warehouse" / "assets.yaml"
DEPENDENCIES = ROOT / "warehouse" / "dependencies.yaml"

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


def refs_in_source(code: str, language: str) -> set[str]:
    """Fully-qualified tables referenced by model source given as TEXT.

    The text-based twin of `table_refs`, for deployed model definitions that arrive as a
    string (from the platform's `latestRevision.code`) rather than a file on disk. It runs
    the SAME rules -- SQL context only, quoted Trino identifiers unquoted, comments and
    docstrings stripped, the `depends_on:` escape hatch honored -- because a second extractor
    would drift from the first, which is the failure this whole inventory exists to prevent.

    `language` is matched case-insensitively: the platform records it as `sql`, `SQL` or
    `python`. Anything else contributes only its explicit `depends_on:` declarations.
    """
    declared = set(DEPENDS_ON_RE.findall(code))
    lang = (language or "").strip().lower()
    if lang == "sql":
        return _refs_in_sql(code) | declared
    if lang in ("python", "py"):
        return _refs_in_python(code) | declared
    return declared


_SUFFIX_LANGUAGE = {".sql": "sql", ".py": "python"}


def table_refs(path: Path) -> set[str]:
    """Fully-qualified tables this file queries."""
    src = path.read_text(encoding="utf-8", errors="replace")
    return refs_in_source(src, _SUFFIX_LANGUAGE.get(path.suffix, ""))


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


def dependencies() -> list[dict]:
    """The external dependency contracts (ADR-003 category 3), or [] if the file is absent.

    A dependency is a direct OSO input a governed asset reads but the repository does NOT
    own -- recorded as a contract (purpose, grain, freshness, provenance anchor, owner: oso),
    never as a governed asset. The manifest is disjoint from assets.yaml by gate.
    """
    if not DEPENDENCIES.exists():
        return []
    return (yaml.safe_load(DEPENDENCIES.read_text(encoding="utf-8")) or {}).get("dependencies") or []


# --- ADR-003 roles and the anti-reintroduction gates -----------------------------------
#
# `role` ASSERTS membership; these functions RE-DERIVE it from the asset's own fields so an
# authored role that disagrees with the boundary rule is caught, exactly as the derived
# read_by graph catches a hand-edited reader list. The externalization backlog (24 long_tail
# + the 4 questionable gap_map tables of EXTERNALIZE_QUESTIONABLE) is roleless until ADR-003
# steps 5/6 remove it; every OTHER asset is a governed asset and must carry the derived role.

def in_externalization_backlog(asset: dict) -> bool:
    """True for an asset ADR-003 slates to leave the governed inventory (roleless until then)."""
    return asset["population"] == "long_tail" or asset["id"] in EXTERNALIZE_QUESTIONABLE


def expected_role(asset: dict) -> str | None:
    """The role ADR-003 assigns this asset, or None if it is in the externalization backlog.

    Derived, not read: `governed-output` iff on the release path; a `compatibility-shim` iff
    a live compatibility object; otherwise repo-owned map computation.
    """
    if in_externalization_backlog(asset):
        return None
    if asset["release_path"]:
        return "governed-output"
    if asset["status"] == "compatibility":
        return "compatibility-shim"
    return "repo-computation"


def _has_repo_definition(asset: dict) -> bool:
    """The repository tracks this asset's definition -- a model/data file, or a build/ producer."""
    files = asset.get("files") or {}
    if files.get("model") or files.get("data"):
        return True
    return str(asset.get("producer", "")).startswith("build/")


def role_violations() -> list[str]:
    """Every governed asset carries the correct `role`, and each role's invariants hold.

    Implements ADR-003 gates 1 (governed-output <-> release_path) and 6 (no governed
    long_tail), plus the role taxonomy's per-role "must be" clauses and the backlog rule
    (roleless iff in the externalization backlog).
    """
    problems: list[str] = []
    for a in assets():
        role = a.get("role")
        want = expected_role(a)
        aid = a["id"]

        if role is not None and role not in ROLES:
            problems.append(f"{aid}: role {role!r} is not one of {sorted(ROLES)}")
            continue

        if want is None:
            # Externalization backlog: must stay roleless until it leaves (steps 5/6).
            if role is not None:
                problems.append(
                    f"{aid}: is in the externalization backlog (long_tail or questionable) "
                    f"but carries role {role!r}; the backlog is roleless until ADR-003 step 5/6"
                )
            continue

        if role is None:
            problems.append(f"{aid}: governed asset is missing its role (expected {want!r})")
            continue
        if role != want:
            problems.append(f"{aid}: role is {role!r} but the boundary rule derives {want!r}")

        # Gate 1: governed-output <-> release_path (both directions).
        if role == "governed-output" and not a["release_path"]:
            problems.append(f"{aid}: role governed-output but release_path is false (gate 1)")
        if a["release_path"] and role != "governed-output":
            problems.append(f"{aid}: release_path true but role is {role!r}, not governed-output (gate 1)")

        # repo-computation must have a repo-tracked definition; authority repo, or platform
        # only for a mirror of a deployed model (ADR-003 wording refined to admit mirrors).
        if role == "repo-computation":
            if not _has_repo_definition(a):
                problems.append(f"{aid}: role repo-computation but no repo file or build/ producer")
            if a["authority"] == "platform" and not a.get("mirror"):
                problems.append(
                    f"{aid}: role repo-computation with authority platform but no mirror block; "
                    "only a mirrored deployed model may be platform-authored repo-computation"
                )
            if a["authority"] == "external":
                problems.append(f"{aid}: role repo-computation but authority is external")

        # compatibility-shim must name its exit target.
        if role == "compatibility-shim":
            if a["status"] != "compatibility":
                problems.append(f"{aid}: role compatibility-shim but status is {a['status']!r}")
            if not a.get("replacement"):
                problems.append(f"{aid}: role compatibility-shim but no `replacement` exit target")

    return problems


def _repo_computation_external_reads() -> dict[str, list[str]]:
    """External (non-currentai) tables read by files owned by a role-carrying computation.

    Scoped to GOVERNED assets: the externalization backlog's OSO reads leave with it and are
    not the repository's contracts. Returns {external_table: [reader file paths]}. Only the
    model files of governed-output / repo-computation / compatibility-shim assets are read;
    a standalone notebook read never counts (gate 5).
    """
    owned: dict[str, str] = {}
    for a in assets():
        if a.get("role") is None:
            continue
        model = (a.get("files") or {}).get("model")
        if model:
            owned[model] = a["id"]
    out: dict[str, list[str]] = {}
    graph = derive_graph()
    for path, refs in graph["reads"].items():
        if path not in owned:
            continue
        for ext in refs["external"]:
            out.setdefault(ext, []).append(path)
    for ext in out:
        out[ext].sort()
    return out


def dependency_violations() -> list[str]:
    """The dependency manifest and the inventory obey ADR-003 gates 2, 3 and 4.

    Gate 2: every external table a governed computation reads is a dependency contract exactly
      once (a compatibility-shim is the only governed exception and is not required here).
    Gate 3: assets.yaml and dependencies.yaml are disjoint.
    Gate 4: every dependency has >= 1 named `required_by` repo computation, the recorded
      `required_by` matches the mechanically re-derived readers, and no dependency is read
      only by a notebook or an external product.
    """
    problems: list[str] = []
    deps = dependencies()
    inv_tables = {a["table"] for a in assets()}
    dep_tables: list[str] = [d.get("table") for d in deps]

    # Gate 3: disjoint files.
    for t in dep_tables:
        if t in inv_tables:
            problems.append(f"{t}: appears in both assets.yaml and dependencies.yaml (gate 3)")
    seen: set[str] = set()
    for t in dep_tables:
        if t in seen:
            problems.append(f"{t}: listed more than once in dependencies.yaml (gate 2)")
        seen.add(t)

    derived = _repo_computation_external_reads()

    # Gate 2: every external read by a governed computation is a contract exactly once.
    for ext, readers in sorted(derived.items()):
        if ext not in seen:
            problems.append(
                f"{ext}: read by {', '.join(readers)} but absent from dependencies.yaml (gate 2)"
            )

    # Gate 4: each contract is real, named, and re-derivable.
    for d in deps:
        t = d.get("table")
        recorded = d.get("required_by") or []
        if not recorded:
            problems.append(f"{t}: dependency has no required_by (gate 4)")
        actual = derived.get(t)
        if actual is None:
            problems.append(
                f"{t}: dependency is not read by any governed computation "
                "(only a notebook or an external product, or nothing) (gate 4)"
            )
        elif sorted(recorded) != actual:
            problems.append(
                f"{t}: required_by {sorted(recorded)} disagrees with the derived readers "
                f"{actual} (gate 4)"
            )
        # Provenance anchor: exactly one of verified_revision, or content_contract_sha256 + verified_at.
        has_rev = bool(d.get("verified_revision"))
        has_hash = bool(d.get("content_contract_sha256")) and bool(d.get("verified_at"))
        if has_rev == has_hash:
            problems.append(
                f"{t}: needs exactly one provenance anchor -- verified_revision, OR "
                "content_contract_sha256 + verified_at"
            )
        if d.get("owner") != "oso":
            problems.append(f"{t}: dependency owner must be oso, not {d.get('owner')!r}")

    return problems


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
        # A model that has not entered service cannot be retired. `staged` (deployed nowhere,
        # e.g. signal_packages awaiting #314) and `dormant` (no platform table yet) are
        # not-in-service states, so they are excluded by construction rather than by an empty
        # reader list -- an undeployed model has no consumers because it does not exist yet,
        # which is a different fact from a live table nobody reads. `compatibility` is excluded
        # for the opposite reason: its retirement is already DECIDED -- it names a `replacement`
        # and rides a governing runbook to its drop -- so surfacing it as an un-noticed candidate
        # would be noise and would demand a spurious retirement_issue it does not have.
        if asset["status"] in ("staged", "dormant", "compatibility"):
            continue
        rb = asset.get("read_by") or {}
        if any(rb.get(root) for root in ROOTS):
            continue
        if asset.get("publication_role"):
            continue
        if asset.get("external_consumers") != "none_confirmed":
            continue
        # "no deployed platform model reads it" (11.2). The Phase 0b audit records those in
        # `platform_model_consumers` -- deployed models with no repository source, so they
        # cannot appear in the repo-derived read_by above. A non-empty list is a real reader.
        if asset.get("platform_model_consumers"):
            continue
        # An asset nobody checked beyond the repository is not evidence of anything. Notebooks
        # are not models: before Phase 0b every asset carried platform_models: unknown and none
        # could be a candidate; the audit set it to checked, which is why this list is now able
        # to be non-empty at all.
        checks = asset.get("consumer_checks") or {}
        if any(checks.get(k) != "checked" for k in ("repository", "platform_notebooks", "platform_models")):
            continue
        out.append(asset)
    return out


# A retirement_issue must point at a real tracking issue, not a placeholder. `#123` or a full
# GitHub issues URL. A gate that only checked truthiness let 'TBD: open an issue before any
# deletion' satisfy a field whose whole claim is that an issue exists -- the recurring
# "check establishes less than it reports" defect this inventory keeps closing.
ISSUE_REF_RE = re.compile(
    r"^(?:#\d+|https://github\.com/[\w.-]+/[\w.-]+/issues/\d+)$"
)


def is_retirement_issue_ref(value: object) -> bool:
    return isinstance(value, str) and bool(ISSUE_REF_RE.match(value.strip()))


_BUILD_PRODUCER_RE = re.compile(r"build/[\w./]+\.py")


def _governed_producer_paths() -> dict[str, list[str]]:
    """Each repo path that PRODUCES a governed table -> the governed table(s) it produces.

    A governed model file, or a `build/` module named in an asset's `producer`. This is the
    set of map roots: only these paths are readers in the root-scoped graph, so a standalone
    notebook that merely reads a table is never a root (ADR-003 gate 5).
    """
    out: dict[str, list[str]] = {}
    for table, a in by_table().items():
        if not a.get("role"):
            continue
        model = (a.get("files") or {}).get("model")
        if model:
            out.setdefault(model, []).append(table)
        for bp in _BUILD_PRODUCER_RE.findall(str(a.get("producer") or "")):
            out.setdefault(bp, []).append(table)
    return {p: sorted(set(v)) for p, v in out.items()}


def governed_edges() -> tuple[set[tuple[str, str]], set[tuple[str, str]], set[tuple[str, str]]]:
    """(internal, external, shim) edges among GOVERNED assets, reachable from the map roots.

    `internal`  governed table -> governed table (a map root reads the upstream).
    `external`  a `dependencies.yaml` OSO input -> the governed computation that reads it.
    `shim`      a compatibility-shim -> its `replacement`.

    Backlog tables are not nodes and notebooks/workflows are not roots, so the graph is the
    Gap Map's own data system rather than the OSO organization's warehouse.
    """
    governed = {tbl: a for tbl, a in by_table().items() if a.get("role")}
    producers = _governed_producer_paths()
    graph = derive_graph()
    internal: set[tuple[str, str]] = set()
    external: set[tuple[str, str]] = set()
    for path, refs in graph["reads"].items():
        for target in producers.get(path, []):
            for up in refs["internal"]:
                if up in governed and up != target:
                    internal.add((up, target))
            for ext in refs["external"]:
                external.add((ext, target))
    shim: set[tuple[str, str]] = set()
    for tbl, a in governed.items():
        if a["role"] == "compatibility-shim" and a.get("replacement"):
            shim.add((tbl, a["replacement"].removeprefix("currentai.")))
    return internal, external, shim


def _node(table: str) -> str:
    return table.replace(".", "__")


def _fence(title: str, body: list[str]) -> list[str]:
    return [f"### {title}", "", "```mermaid", "graph LR", *body, "```", ""]


def render_dag() -> str:
    """Render the ROOT-SCOPED dependency graph (ADR-003) as three Mermaid views.

    Generated, never drawn: a hand-drawn graph drifts within a week, and a generated document
    that drifts from its generator is worse than none. A gate compares this output against the
    committed copy. Membership is the governed inventory (assets carrying a `role`) plus the
    external contracts in dependencies.yaml -- not every table on the OSO org, and never a
    standalone notebook (gate 5).
    """
    governed = {tbl: a for tbl, a in by_table().items() if a.get("role")}
    role_of = {tbl: a["role"] for tbl, a in governed.items()}
    internal, external, shim = governed_edges()
    has_incoming = {b for _, b in internal}

    out: list[str] = []

    # View 1 -- map governance: sources/ -> governed outputs, and the computation chain.
    body: list[str] = ["  SRC[sources/]:::src"]
    ns_tables: dict[str, list[str]] = {}
    for tbl in sorted(governed):
        if role_of[tbl] == "compatibility-shim":
            continue  # shims live in the appendix (view 3)
        ns_tables.setdefault(tbl.split(".")[0], []).append(tbl)
    for ns, tables in sorted(ns_tables.items()):
        body.append(f"  subgraph {ns}")
        for tbl in tables:
            body.append(f"    {_node(tbl)}[{tbl.split('.', 1)[1]}]")
        body.append("  end")
    # sources/ feeds every governed output with no governed upstream (the compiled declarations).
    for tbl in sorted(governed):
        if role_of[tbl] == "governed-output" and tbl not in has_incoming:
            body.append(f"  SRC --> {_node(tbl)}")
    for up, dn in sorted(internal):
        if role_of.get(up) == "compatibility-shim" or role_of.get(dn) == "compatibility-shim":
            continue
        body.append(f"  {_node(up)} --> {_node(dn)}")
    body.append("  classDef src fill:#def;")
    out += _fence("View 1 — Map governance (sources → governed outputs)", body)

    # View 2 -- runtime dependencies: OSO inputs (dependencies.yaml) -> map computation.
    body = []
    dep_tables = {d["table"] for d in dependencies()}
    for ext, dn in sorted(external):
        marker = "" if ext in dep_tables else ":::uncontracted"
        body.append(f"  EXT_{_node(ext)}[{ext}]{marker} --> {_node(dn)}")
    if not external:
        body.append("  none[no external runtime dependencies]:::src")
    body.append("  classDef uncontracted fill:#fdd;")
    out += _fence("View 2 — Runtime dependencies (OSO inputs → map computation)", body)

    # View 3 -- compatibility / retirement appendix: shims -> their replacements.
    body = []
    if shim:
        for src, repl in sorted(shim):
            body.append(f"  {_node(src)}[{src}]:::compat --> {_node(repl)}[{repl}]")
    else:
        body.append("  none[no compatibility shims]:::src")
    body.append("  classDef compat stroke-width:3px;")
    out += _fence("View 3 — Compatibility / retirement appendix", body)

    return "\n".join(out).rstrip() + "\n"


def notebook_root_violations() -> list[str]:
    """ADR-003 gate 5: no standalone notebook is a reachability root of the governed graph.

    A notebook path must never appear as a producer of a governed table, so a notebook read
    cannot pull a table into the DAG or confer membership. Re-derived, so a future asset that
    named a notebook as its producer would be caught.
    """
    problems: list[str] = []
    for path in _governed_producer_paths():
        if path.startswith("notebooks/"):
            problems.append(f"{path}: a notebook is a governed-graph root (gate 5)")
    return problems


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
    "governed_assets": lambda: sum(1 for a in assets() if a.get("role")),
    "externalization_backlog": lambda: sum(1 for a in assets() if a.get("role") is None),
    "dependencies": lambda: len(dependencies()),
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
    source to have been checked. This says only: nothing we looked at reads it -- no in-repo
    reader, no reviewed platform-model reader, and no confirmed external consumer.

    `platform_model_consumers` counts here from Phase 0b onward: a deployed model that reads
    the asset is a reviewed consumer even when it has no repository source, so an asset one
    reads is no longer "no reviewed consumer".

    Not-in-service assets (`staged`, `dormant`) are excluded: a model deployed nowhere has no
    consumers because it does not exist yet, which is a different state from a live table
    nobody reads and must not be conflated with it. `compatibility` is excluded too: its
    consumers moved to its named `replacement` by design, so its empty reader list is the
    planned outcome of a rename, not an unnoticed dead table.
    """
    return [
        a for a in assets()
        if a.get("status") not in ("staged", "dormant", "compatibility")
        and not (a.get("read_by") or {})
        and not a.get("publication_role")
        and not a.get("platform_model_consumers")
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
