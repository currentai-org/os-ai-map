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
import hashlib
import json
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

NAMESPACES = {"registry", "catalog", "observations", "evaluation", "releases"}
STATUSES = {"active", "staged", "deprecated", "historical", "compatibility", "dormant"}
CHECK_STATES = {"checked", "unknown", "not_applicable"}
AUTHORITIES = {"repo", "platform", "external"}
# Every governed asset is `gap_map`; the vocabulary is single-valued so nothing else can appear.
POPULATIONS = {"gap_map"}

# ADR-003 repository role, ASSERTED by this field and re-derived from the asset's own fields
# (expected_role) so an authored role that disagrees with the boundary rule is caught.
#   governed-output   a published Gap Map artifact whose schema + publication lifecycle are
#                     owned here (release_path: true, authority: repo).
#   repo-computation  repo-OWNED SQL/Python implementing or auditing map semantics. MUST be
#                     authority: repo -- a `mirror` block proves provenance, not ownership, so a
#                     platform-authored mirror is a dependency contract, not a repo-computation.
#   governed-data     a repo-OWNED data/control artifact that is not a computation (the frozen
#                     adoption baseline bytes, the source-runs snapshot). authority: repo.
#   compatibility-shim  a temporary shim carrying `replacement` (named to avoid collision with
#                     `status: compatibility`); may be a platform mirror, since a shim is not owned.
ROLES = {"governed-output", "repo-computation", "governed-data", "compatibility-shim"}

# The named audit / control roots of the governed graph: repo modules that READ governed or
# dependency tables to gate or audit map semantics but do not themselves produce a governed
# table (so reachability from a publication sink alone would miss them). ADR-003 gate 4 / the
# root-scoped DAG treat these as roots alongside the governed-output sinks.
AUDIT_ROOTS = (
    "build/check_parity.py",     # protects the openness dual-run
    "build/apply_scores.py",     # applies the recorded score corpus
    "build/check_artifacts.py",  # audits declared-artifact coverage of the signals
)

# Explicitly declared publication workflows that read tables directly (none today). The root
# set is CLOSED: a governed root is a governed producer file, a named AUDIT_ROOT, or a declared
# workflow here -- never "any tracked build/*.py or workflow", so an
# unrelated future helper that happens to contain a table reference cannot become a semantic
# root and pull a peripheral table into dependencies.yaml.
PUBLICATION_WORKFLOWS: tuple[str, ...] = ()

REQUIRED_FIELDS = (
    "id", "table", "kind", "authority", "grain", "producer", "population", "release_path",
    "role", "consumer_checks", "refresh", "status", "verified_at",
)
ASSETS = ROOT / "warehouse" / "assets.yaml"
DEPENDENCIES = ROOT / "warehouse" / "dependencies.yaml"
EXTERNALIZATION = ROOT / "warehouse" / "audits" / "externalization.json"

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


EXTERNALIZATION_DISPOSITIONS = {"frozen-without-producer", "transferred"}
EXTERNALIZATION_SCHEMA_VERSION = 2
PLATFORM_MODELS = ROOT / "warehouse" / "audits" / "platform_models.json"
# The externalized artifacts live under these path prefixes; every file that existed under them
# at the base commit and is now gone must be archived in the receipt (completeness check).
EXTERNALIZED_FILE_PREFIXES = ("warehouse/models/", "warehouse/data/", "sources/")


def externalization_receipt() -> dict:
    """The full externalization receipt document (ADR-003 steps 5-6), or {} if absent."""
    if not EXTERNALIZATION.exists():
        return {}
    return json.loads(EXTERNALIZATION.read_text(encoding="utf-8")) or {}


def externalized() -> list[dict]:
    """The externalization receipt's asset entries, or [] if absent."""
    return externalization_receipt().get("assets") or []


def _git_commit_exists(sha: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
        capture_output=True,
    ).returncode == 0


def _assets_at_commit(sha: str) -> dict[str, dict] | None:
    """The inventory as of an explicit commit, keyed by table, or None if unreadable there."""
    try:
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{sha}:warehouse/assets.yaml"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return {a["table"]: a for a in (yaml.safe_load(blob) or {}).get("assets") or []}


def _tree_files_at_commit(sha: str, prefixes: tuple[str, ...]) -> set[str]:
    """Every tracked file under any of `prefixes` as of `sha`."""
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", sha],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return set()
    return {p for p in out.splitlines() if p.startswith(prefixes)}


def _platform_models() -> dict[str, dict]:
    """The current deployed-model audit receipt keyed by table, or {} if absent."""
    if not PLATFORM_MODELS.exists():
        return {}
    doc = json.loads(PLATFORM_MODELS.read_text(encoding="utf-8")) or {}
    return {m["table"]: m for m in doc.get("models") or []}


def _platform_models_at_commit(sha: str) -> dict[str, dict]:
    """The deployed-model audit as of an explicit commit, keyed by table, or {} if unreadable.

    The externalization receipt records platform facts *as of removal*; reproducing them against the
    mutable current audit would break the moment a later legitimate audit changed or dropped an
    externalized model, forcing an append-only violation. So the receipt reproduces against the
    audit committed at its own base commit -- immutable evidence for an immutable receipt.
    """
    try:
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{sha}:warehouse/audits/platform_models.json"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return {}
    return {m["table"]: m for m in (json.loads(blob) or {}).get("models") or []}


def _first_add_commit(path: str) -> str | None:
    """The oldest commit reachable from HEAD that added `path`, or None."""
    out = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--reverse", "--diff-filter=A", "--format=%H", "--", path],
        capture_output=True, text=True,
    ).stdout.split()
    return out[0] if out else None


def _rev_parse(ref: str) -> str | None:
    r = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", ref],
        capture_output=True, text=True,
    )
    return r.stdout.strip() or None


def _parent_sha(sha: str) -> str | None:
    return _rev_parse(f"{sha}^")


def expected_externalization_base(recorded_tables: set[str]) -> str | None:
    """Derive the base commit the receipt MUST name, from the commit graph -- not from the receipt.

    ADR-003's externalization boundary is the state just BEFORE the receipted tables left the
    inventory. Anchored to `externalization.json`'s first-add commit so it survives squash merging
    (on the merged trunk the squash commit both removes the tables and adds the receipt, and its
    parent is the pre-externalization trunk tip). Because a multi-commit branch can add the receipt
    a commit or two AFTER the removal, the derivation starts at the first-add commit's parent and
    walks back along first-parent history to the newest commit whose inventory still contains every
    receipted table -- the pre-removal snapshot. Binding the base this way means a substituted older
    commit (regenerating a broader historical removal set) no longer validates: the receipt's
    `externalization_base_commit` must equal the graph-derived boundary.
    """
    add = _first_add_commit("warehouse/audits/externalization.json")
    if not add:
        return None
    base = _parent_sha(add)
    steps = 0
    while base and steps < 100:
        tables = _assets_at_commit(base)
        if tables is not None and recorded_tables <= set(tables):
            return base
        base = _parent_sha(base)
        steps += 1
    return None


def _norm_read_by(rb) -> dict:
    """A read_by block normalized to sorted lists so two provenance snapshots compare by value."""
    if not rb:
        return {}
    return {k: sorted(v) for k, v in rb.items() if v}


def externalization_receipt_violations() -> list[str]:
    """The externalization receipt MECHANICALLY REPRODUCES from its named base commit.

    ADR-003's no-orphan handoff evidence is only worth as much as its reproducibility. This gate
    re-derives every derivable field from the base commit's IMMUTABLE evidence (the inventory, the
    file blobs, and the platform-model audit committed AT THE BASE) and asserts the committed
    receipt matches, so the receipt cannot drift from the state it claims to record. It proves, with
    no OSO credentials:

    * the document is well-formed: `schema_version`, a `count` equal to the entry total, unique ids
      and tables, and a base commit that resolves;
    * BOUNDARY -- `externalization_base_commit` is not free-form: it must equal the graph-derived
      boundary (the pre-removal state anchored to `externalization.json`'s first-add commit, so it
      survives squash merging), so a valid-but-older commit cannot be substituted to attribute a
      broader historical removal set to this externalization;
    * MEMBERSHIP -- the entries are EXACTLY the assets removed from the base inventory (base minus
      the current governed inventory minus the current dependency manifest), both directions;
    * per entry, `id` and `population_was` equal the base asset's, `platform.dataset_id` equals the
      base asset's dataset, and the deployed-model facts (`model_id`, `revision_hash`,
      `source_sha256`) equal the BASE platform audit -- an entry with no audited model carries only a
      dataset id, never fabricated model facts;
    * PROVENANCE -- every `archived_source_sha256` hash equals the file's bytes at the base commit
      and the file is genuinely gone from the worktree; and every file that existed under the
      externalized prefixes at the base commit and is now deleted is archived by some entry (this is
      what catches a deleted source that was left unarchived);
    * CONSUMERS -- `repo_read_by` equals the base asset's `read_by` and `external_notebooks_or_products`
      equals its `external_consumers`; the captured `platform_models` list must at least cover every
      surviving model in the BASE audit that read the table (a reproducible lower bound -- extra
      entries come from the externalization-time platform scan named in `evidence_basis`);
    * HONESTY -- `last_platform_verified_at` equals the base asset's own `verified_at` (its real last
      verification, not a fresh live claim), and `recorded_at`, `evidence_basis`, and `owner` are
      present. `consumer_resolution` is optional prose and is NEVER what satisfies the gate; the
      structured, reproduced consumer fields are;
    * SHAPE -- a real disposition, `frozen-without-producer` names the frozen deployed table (a
      dataset id), `transferred` names a destination (repo + commit) so a freeze cannot be mislabeled
      as a transfer, and each entry is genuinely gone from the governed inventory, the dependency
      manifest, and every repository producer;
    * APPEND-ONLY -- every entry recorded in the receipt at the merge base survives unchanged here.
    """
    problems: list[str] = []
    receipt = externalization_receipt()
    if not receipt:
        return problems  # no receipt is not a violation; nothing was externalized

    entries = receipt.get("assets") or []

    # -- document well-formedness --------------------------------------------------
    if receipt.get("schema_version") != EXTERNALIZATION_SCHEMA_VERSION:
        problems.append(
            f"receipt schema_version {receipt.get('schema_version')!r} != {EXTERNALIZATION_SCHEMA_VERSION}")
    if receipt.get("count") != len(entries):
        problems.append(f"receipt count {receipt.get('count')!r} != {len(entries)} entries")
    ids = [e.get("id") for e in entries]
    tables = [e.get("table") for e in entries]
    if len(set(ids)) != len(ids):
        problems.append("receipt has duplicate entry ids")
    if len(set(tables)) != len(tables):
        problems.append("receipt has duplicate entry tables")

    base = receipt.get("externalization_base_commit")
    if not base or not _git_commit_exists(base):
        problems.append(f"externalization_base_commit {base!r} does not resolve in this repo")
        return problems  # everything below reproduces against the base; without it, stop here

    # The base is not free-form: it must be the graph-derived externalization boundary, so a valid
    # but older commit cannot be substituted to attribute a broader historical removal set here.
    recorded_tables = {t for t in tables if t}
    expected_base = expected_externalization_base(recorded_tables)
    if expected_base is None:
        problems.append("cannot derive the externalization boundary from history "
                        "(externalization.json add commit or a pre-removal inventory is unreachable)")
    elif expected_base != _rev_parse(base):
        problems.append(
            f"externalization_base_commit {base} is not the externalization boundary; the commit "
            f"graph derives {expected_base} (the pre-removal state anchored to externalization.json)")

    base_assets = _assets_at_commit(base)
    if base_assets is None:
        problems.append(f"cannot read warehouse/assets.yaml at base commit {base}")
        return problems

    # -- membership: entries == assets removed from the base inventory --------------
    governed = set(by_table())
    dep_tables = {d.get("table") for d in dependencies()}
    dep_tables_bare = {t.removeprefix("currentai.") for t in dep_tables if t}
    removed = {
        t for t in base_assets
        if t.removeprefix("currentai.") not in governed
        and t.removeprefix("currentai.") not in dep_tables_bare
    }
    recorded = set(tables)
    for t in sorted(removed - recorded):
        problems.append(f"{t}: removed from the base inventory but not in the externalization receipt")
    for t in sorted(recorded - removed):
        problems.append(f"{t}: in the receipt but not an asset removed from the base inventory")

    # -- per-entry reproduction ----------------------------------------------------
    # Platform facts reproduce against the audit committed AT THE BASE (immutable evidence for an
    # immutable receipt), never the mutable current audit.
    pmodels = _platform_models_at_commit(base)
    producers = {(a.get("files") or {}).get("model") for a in assets()}
    producers |= {(d.get("files") or {}).get("model") for d in dependencies()}
    producer_tables = {table_for_path(p) for p in producers if p}
    archived_all: set[str] = set()

    for e in entries:
        t = e.get("table")
        if not t:
            problems.append(f"{e.get('id')!r}: externalization entry has no table")
            continue
        b = base_assets.get(t)
        if b is None:
            continue  # membership check above already flagged this

        # still gone from every live surface
        if t.removeprefix("currentai.") in governed:
            problems.append(f"{t}: externalized but still a governed asset in assets.yaml")
        if t in dep_tables:
            problems.append(f"{t}: externalized but also a dependency contract")
        if t in producer_tables:
            problems.append(f"{t}: externalized but a repository model file still produces it")

        # identity + population reproduce from the base asset
        if e.get("id") != b.get("id"):
            problems.append(f"{t}: id {e.get('id')!r} != base {b.get('id')!r}")
        if e.get("population_was") != b.get("population"):
            problems.append(f"{t}: population_was {e.get('population_was')!r} != base {b.get('population')!r}")

        # platform facts reproduce from the base dataset + the deployed-model audit
        plat = e.get("platform") or {}
        if plat.get("dataset_id") != b.get("dataset_id"):
            problems.append(f"{t}: platform.dataset_id {plat.get('dataset_id')!r} != base {b.get('dataset_id')!r}")
        m = pmodels.get(t)
        if m:
            for f in ("model_id", "revision_hash", "source_sha256"):
                if plat.get(f) != m.get(f):
                    problems.append(f"{t}: platform.{f} {plat.get(f)!r} != audit {m.get(f)!r}")
        else:
            extra = set(plat) - {"dataset_id"}
            if extra:
                problems.append(f"{t}: platform carries {sorted(extra)} but no audited model exists to source it")

        # archived hashes reproduce from base blobs; the files are really gone
        for path, h in (e.get("archived_source_sha256") or {}).items():
            archived_all.add(path)
            want = _git_blob_sha256(base, path)
            if want is None:
                problems.append(f"{t}: archived {path} did not exist at the base commit")
            elif want != h:
                problems.append(f"{t}: archived {path} hash {h} != base blob {want}")
            if (ROOT / path).exists():
                problems.append(f"{t}: archived {path} still exists in the worktree (not deleted)")

        # consumer provenance: repo readers + external consumers reproduce from the base asset
        car = e.get("consumers_at_removal") or {}
        if _norm_read_by(car.get("repo_read_by")) != _norm_read_by(b.get("read_by")):
            problems.append(f"{t}: consumers_at_removal.repo_read_by != base read_by")
        base_ext = b.get("external_consumers")
        want_ext = sorted(base_ext) if isinstance(base_ext, list) else []
        got_ext = sorted(car.get("external_notebooks_or_products") or [])
        if want_ext != got_ext:
            problems.append(f"{t}: external_notebooks_or_products {got_ext} != base external_consumers {want_ext}")
        # the captured platform consumer list must cover every surviving audited reader (lower bound)
        recorded_pm = {p.removeprefix("currentai.") for p in car.get("platform_models") or []}
        for cm in pmodels.values():
            if cm["table"] in recorded or cm["table"] == t:
                continue  # a removed model is not a surviving consumer; nor is the table itself
            reads = {r.removeprefix("currentai.") for r in cm.get("internal_reads") or []}
            if t.removeprefix("currentai.") in reads and cm["table"].removeprefix("currentai.") not in recorded_pm:
                problems.append(
                    f"{t}: surviving audited model {cm['table']} reads it but is absent from "
                    "consumers_at_removal.platform_models")

        # honesty: the verification date is the asset's real prior date, not a fresh live claim
        if str(e.get("last_platform_verified_at")) != str(b.get("verified_at")):
            problems.append(
                f"{t}: last_platform_verified_at {e.get('last_platform_verified_at')!r} != base "
                f"verified_at {b.get('verified_at')!r}")
        for field in ("recorded_at", "evidence_basis", "owner"):
            if not e.get(field):
                problems.append(f"{t}: externalization entry missing {field}")

        # shape
        disp = e.get("disposition")
        if disp not in EXTERNALIZATION_DISPOSITIONS:
            problems.append(f"{t}: disposition {disp!r} not in {sorted(EXTERNALIZATION_DISPOSITIONS)}")
        if disp == "frozen-without-producer" and not plat.get("dataset_id"):
            problems.append(f"{t}: 'frozen-without-producer' must name the frozen deployed table (dataset_id)")
        if disp == "transferred":
            dest = e.get("destination") or {}
            if not (dest.get("repository") and dest.get("commit")):
                problems.append(f"{t}: disposition 'transferred' must name destination.repository + commit")

    # -- completeness: every deleted externalized file is archived ------------------
    base_files = _tree_files_at_commit(base, EXTERNALIZED_FILE_PREFIXES)
    deleted = {p for p in base_files if not (ROOT / p).exists()}
    for p in sorted(deleted - archived_all):
        problems.append(f"{p}: deleted since the base commit but not archived in any receipt entry")

    # -- append-only: prior entries survive unchanged ------------------------------
    prior = _merge_base_receipt()
    if prior:
        cur_by_id = {e.get("id"): e for e in entries}
        for pid, pe in prior.items():
            if pid not in cur_by_id:
                problems.append(f"{pid}: previously recorded externalization entry was removed (append-only)")
            elif cur_by_id[pid] != pe:
                problems.append(f"{pid}: previously recorded externalization entry was modified (append-only)")

    return problems


def _merge_base_receipt(base: str = "origin/main") -> dict[str, dict] | None:
    """The externalization receipt entries as of the merge base, keyed by id, or None if absent."""
    mb = _merge_base_sha(base)
    if not mb:
        return None
    try:
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{mb}:warehouse/audits/externalization.json"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return {e.get("id"): e for e in (json.loads(blob) or {}).get("assets") or []}


# --- ADR-003 roles and the anti-reintroduction gates -----------------------------------
#
# `role` ASSERTS membership; these functions RE-DERIVE it from the asset's own fields so an
# authored role that disagrees with the boundary rule is caught, exactly as the derived
# read_by graph catches a hand-edited reader list. Every asset in assets.yaml is a governed
# asset and carries the derived role; there is no roleless state.

def expected_role(asset: dict) -> str:
    """The role ADR-003 derives for a governed asset, from its own fields.

    `governed-output` iff on the release path; `compatibility-shim` iff a live compatibility
    object; `repo-computation` iff a repo-owned model (has a model file); otherwise
    `governed-data` (a repo-owned data/control artifact -- the baseline bytes, the source-runs
    snapshot). A platform mirror is never governed-output/repo-computation: such tables are not
    in assets.yaml at all -- they are dependency contracts.
    """
    if asset["release_path"]:
        return "governed-output"
    if asset["status"] == "compatibility":
        return "compatibility-shim"
    if (asset.get("files") or {}).get("model"):
        return "repo-computation"
    return "governed-data"


def role_violations() -> list[str]:
    """Every governed asset carries the correct `role` and each role's invariants hold.

    ADR-003 gate 1 (governed-output <-> release_path) and the per-role "must be" clauses. `role`
    and `population: gap_map` are REQUIRED_FIELDS / vocabulary, enforced directly.
    """
    problems: list[str] = []
    for a in assets():
        role = a.get("role")
        want = expected_role(a)
        aid = a["id"]

        if role not in ROLES:
            problems.append(f"{aid}: role {role!r} is not one of {sorted(ROLES)}")
            continue
        if role != want:
            problems.append(f"{aid}: role is {role!r} but the boundary rule derives {want!r}")

        # Gate 1: governed-output <-> release_path (both directions).
        if role == "governed-output" and not a["release_path"]:
            problems.append(f"{aid}: role governed-output but release_path is false (gate 1)")
        if a["release_path"] and role != "governed-output":
            problems.append(f"{aid}: release_path true but role is {role!r}, not governed-output (gate 1)")

        # repo-computation is repo-OWNED: authority repo (a mirror is not ownership), model file.
        if role == "repo-computation":
            if a["authority"] != "repo":
                problems.append(
                    f"{aid}: role repo-computation but authority is {a['authority']!r}; a "
                    "platform mirror is a dependency contract, not a repo computation"
                )
            if not (a.get("files") or {}).get("model"):
                problems.append(f"{aid}: role repo-computation but no model file")

        # governed-data is a repo-owned data/control artifact, not a computation.
        if role == "governed-data":
            if a["authority"] != "repo":
                problems.append(f"{aid}: role governed-data but authority is {a['authority']!r}")
            if a["release_path"]:
                problems.append(f"{aid}: role governed-data but release_path is true (use governed-output)")
            files = a.get("files") or {}
            if files.get("model"):
                problems.append(f"{aid}: role governed-data but has a model file (use repo-computation)")
            if not (files.get("data") or str(a.get("producer", "")).startswith("build/")):
                problems.append(f"{aid}: role governed-data but no data file or build/ producer")

        # compatibility-shim must name its exit target.
        if role == "compatibility-shim":
            if a["status"] != "compatibility":
                problems.append(f"{aid}: role compatibility-shim but status is {a['status']!r}")
            if not a.get("replacement"):
                problems.append(f"{aid}: role compatibility-shim but no `replacement` exit target")

    return problems


def expected_kind(asset: dict) -> str:
    """The semantic layer (`kind`) an asset's PHYSICAL placement derives.

    A governed asset in the `registry`, `observations` or `evaluation` namespace names its own
    kind. A `signal_*` source dataset is physically separate but semantically an OBSERVATION (a
    raw source collector) -- unless it is a banded `product_adoption` assessment, which is an
    EVALUATION. This is the one intentional place `kind` and namespace come apart, so keeping
    `kind` requires enforcing it: nothing else re-derives it.
    """
    namespace = asset["table"].split(".")[1]
    if namespace.startswith("signal_"):
        return "evaluation" if asset["table"].endswith(".product_adoption") else "observations"
    return namespace


def kind_violations() -> list[str]:
    """Every governed asset's `kind` is the one its placement derives (expected_kind), so `kind`
    is a governed field, not decorative: a `registry` table cannot claim `kind: evaluation`."""
    problems: list[str] = []
    for a in assets():
        if a["kind"] not in NAMESPACES:
            problems.append(f"{a['id']}: kind {a['kind']!r} not in {sorted(NAMESPACES)}")
            continue
        want = expected_kind(a)
        if a["kind"] != want:
            problems.append(f"{a['id']}: kind is {a['kind']!r} but its placement derives {want!r}")
    return problems


# --- the governed graph: reachability from map roots ------------------------------------

def _governed_tables() -> set[str]:
    """currentai-stripped table names of the governed assets (those carrying a role)."""
    return {a["table"].removeprefix("currentai.") for a in assets() if a.get("role")}


def _dependency_model_files() -> dict[str, str]:
    """{currentai-stripped table: mirror model file} for currentai.* dependency contracts.

    A dependency keeps a read-only MIRROR file so its provenance is tracked and the openness
    dependency chain remains derivable; the table is not governed but the file is claimed here.
    """
    out: dict[str, str] = {}
    for d in dependencies():
        model = (d.get("files") or {}).get("model")
        if model and d["table"].startswith("currentai."):
            out[d["table"].removeprefix("currentai.")] = model
    return out


def _governed_root_files() -> set[str]:
    """The map roots -- a CLOSED set, never "any build module or workflow".

    A root is a governed producer file (a governed asset's model file, or a `build/` module named
    as a governed asset's `producer`), a named AUDIT_ROOT, or an explicitly declared publication
    workflow. So an unrelated future `build/foo.py` or workflow that merely contains a table
    reference cannot become a semantic root and confer dependency membership. Standalone notebooks
    are excluded (gate 5); a dependency's mirror file is a leaf, not a root.
    """
    roots = set(_governed_producer_paths())
    roots |= set(AUDIT_ROOTS)
    roots |= set(PUBLICATION_WORKFLOWS)
    return roots


def needed_tables() -> set[str]:
    """Every table (full name) reachable UPSTREAM from the governed roots.

    Reachability closure (ADR-003 root-scoped DAG / gate 4): start at the governed roots
    (sinks + audit/control build modules), follow each read to the table it names, and where
    that table has a repo producer file (a governed model OR a dependency mirror) follow that
    file's reads too. Notebooks never enter the traversal. A table not in this set is not part
    of the Gap Map's data system.
    """
    graph = derive_graph()
    producer = {t: mf for t, mf in _dependency_model_files().items()}
    for a in assets():
        if a.get("role"):
            mf = (a.get("files") or {}).get("model")
            if mf:
                producer[a["table"].removeprefix("currentai.")] = mf
    needed: set[str] = set()
    seen_files: set[str] = set()
    queue: list[str] = sorted(_governed_root_files())
    while queue:
        f = queue.pop()
        if f in seen_files:
            continue
        seen_files.add(f)
        refs = graph["reads"].get(f)
        if not refs:
            continue
        for internal in refs["internal"]:
            needed.add(f"currentai.{internal}")
            pf = producer.get(internal)
            if pf and pf not in seen_files:
                queue.append(pf)
        for ext in refs["external"]:
            needed.add(ext)
    return needed


def dependency_readers() -> dict[str, list[str]]:
    """{full dependency table: sorted repo files that read it}.

    Mechanically re-derived so a recorded `required_by` cannot drift. Readers are the governed
    roots (governed model files + build modules + workflows) and the dependency mirror files
    (the openness chain reads dep->dep), and never a notebook (gate 5). This is why an unlisted OSO
    input a governed computation reads is caught: only what a governed root reaches is a contract.
    """
    governed = _governed_tables()
    reader_files = _governed_root_files() | set(_dependency_model_files().values())
    graph = derive_graph()
    out: dict[str, list[str]] = {}
    for path in reader_files:
        refs = graph["reads"].get(path)
        if not refs:
            continue
        for internal in refs["internal"]:
            if internal not in governed:
                out.setdefault(f"currentai.{internal}", []).append(path)
        for ext in refs["external"]:
            out.setdefault(ext, []).append(path)
    return {t: sorted(set(v)) for t, v in out.items()}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def contract_fingerprint(dep: dict) -> str:
    """The reproducible content-contract fingerprint of an oso.* dependency.

    Binds the agreed schema -- table, grain, and each column's name AND type (nullability
    included) -- so a silent edit to the contract terms changes the hash. Names alone are
    insufficient (the timestamp(6) drift): columns carry types.
    """
    cols = dep.get("expected_columns") or []
    rendered = []
    for c in cols:
        if isinstance(c, dict):
            rendered.append(f"{c.get('name')}:{c.get('type')}:{'null' if c.get('nullable') else 'notnull'}")
        else:
            rendered.append(str(c))
    payload = dep["table"] + "\n" + str(dep.get("expected_grain", "")) + "\n" + "\n".join(sorted(rendered))
    return _sha256(payload)


_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def dependency_violations() -> list[str]:
    """assets.yaml and dependencies.yaml obey ADR-003 gates 2, 3, 4 and contract integrity.

    Gate 2: every non-governed table reachable from a governed root is a dependency contract
      exactly once (currentai.* platform inputs AND oso.* upstreams alike).
    Gate 3: the two files are disjoint.
    Gate 4: every dependency is reachable from a governed root, has >= 1 named `required_by`
      that matches the mechanically re-derived repo readers, and is not read only by a notebook.
    Integrity: exactly one provenance anchor, self-consistent -- a currentai.* mirror uses
      verified_revision + a mirror block whose local_sha256 matches the file; an oso.* upstream
      uses content_contract_sha256 (64 hex, recomputed from typed expected_columns) + verified_at.
    """
    problems: list[str] = []
    deps = dependencies()
    governed_full = {a["table"] for a in assets()}
    dep_tables = [d.get("table") for d in deps]
    dep_set = set(dep_tables)

    # Gate 3: disjoint; gate 2: no duplicate contract.
    for t in dep_tables:
        if t in governed_full:
            problems.append(f"{t}: appears in both assets.yaml and dependencies.yaml (gate 3)")
    seen: set[str] = set()
    for t in dep_tables:
        if t in seen:
            problems.append(f"{t}: listed more than once in dependencies.yaml (gate 2)")
        seen.add(t)

    governed = _governed_tables()
    needed = needed_tables()
    readers = dependency_readers()

    # Gate 2: every non-governed table a governed root transitively needs is a contract.
    for t in sorted(needed):
        stripped = t.removeprefix("currentai.")
        if stripped in governed:
            continue
        if t not in dep_set:
            who = ", ".join(readers.get(t, [])) or "the reachability closure"
            problems.append(f"{t}: needed by {who} but absent from dependencies.yaml (gate 2)")

    # Gate 4 + integrity, per contract.
    for d in deps:
        t = d.get("table")
        if t not in needed:
            problems.append(
                f"{t}: dependency is not reachable from any governed root -- read only by a "
                "notebook, an external product, or nothing (gate 4)"
            )
        recorded = sorted(d.get("required_by") or [])
        actual = readers.get(t, [])
        if not recorded:
            problems.append(f"{t}: dependency has no required_by (gate 4)")
        elif recorded != actual:
            problems.append(
                f"{t}: required_by {recorded} disagrees with the derived repo readers {actual} (gate 4)"
            )
        if d.get("owner") != "oso":
            problems.append(f"{t}: dependency owner must be oso, not {d.get('owner')!r}")

        # ADR-003 requires the contract to state purpose, grain and freshness (fail closed).
        for field in ("purpose", "expected_grain", "freshness_requirement"):
            if not str(d.get(field) or "").strip():
                problems.append(f"{t}: dependency contract is missing {field}")

        # Provenance anchor: exactly one, and internally self-consistent.
        has_rev = d.get("verified_revision") is not None
        has_hash = bool(d.get("content_contract_sha256")) and bool(d.get("verified_at"))
        if has_rev == has_hash:
            problems.append(
                f"{t}: needs exactly one provenance anchor -- verified_revision (currentai.* "
                "mirror), OR content_contract_sha256 + verified_at (oso.* upstream)"
            )
            continue
        if has_rev:
            if not str(t).startswith("currentai."):
                problems.append(f"{t}: verified_revision anchors a currentai.* model; this is not one")
            problems += _mirror_integrity(d)
        else:
            if not str(t).startswith("oso."):
                problems.append(f"{t}: content_contract_sha256 anchors an oso.* upstream; this is not one")
            got = d.get("content_contract_sha256")
            if not (isinstance(got, str) and _HEX64_RE.match(got)):
                problems.append(f"{t}: content_contract_sha256 must be 64 lowercase hex chars")
            elif got != contract_fingerprint(d):
                problems.append(
                    f"{t}: content_contract_sha256 does not match the recomputed fingerprint of "
                    "table + grain + typed expected_columns (edit the contract, then the hash)"
                )
            if not d.get("expected_columns"):
                problems.append(f"{t}: oso.* contract needs typed expected_columns (name + type)")
            for c in d.get("expected_columns") or []:
                if not (isinstance(c, dict) and c.get("name") and c.get("type")):
                    problems.append(f"{t}: each expected_columns entry needs a name and a type: {c!r}")

    return problems


def _mirror_integrity(dep: dict) -> list[str]:
    """A currentai.* dependency mirror fails closed: every claimed file's bytes are hashed and
    match, verified_revision equals the mirror revision, and the mirror names a model_id."""
    problems: list[str] = []
    t = dep["table"]
    mirror = dep.get("mirror") or {}
    files = dep.get("files") or {}
    model = files.get("model")
    if not model:
        problems.append(f"{t}: currentai.* dependency needs a mirror model file")
        return problems
    # verified_revision is the anchor; it must equal the mirror block's revision (fail closed).
    if dep.get("verified_revision") != mirror.get("revision"):
        problems.append(
            f"{t}: verified_revision {dep.get('verified_revision')!r} != mirror.revision "
            f"{mirror.get('revision')!r}"
        )
    if not mirror.get("model_id"):
        problems.append(f"{t}: mirror block needs a model_id")
    # Content-bind EVERY claimed file: the model via mirror.local_sha256, the schema via
    # mirror.schema_sha256. A tracked file the contract claims but does not hash is not bound.
    for role, declared_key in (("model", "local_sha256"), ("schema", "schema_sha256")):
        fp = files.get(role)
        if not fp:
            continue
        path = ROOT / fp
        if not path.exists():
            problems.append(f"{t}: mirror {role} file {fp} does not exist")
            continue
        declared = mirror.get(declared_key)
        if not declared:
            problems.append(f"{t}: mirror block needs {declared_key} for the {role} file {fp}")
        elif declared != hashlib.sha256(path.read_bytes()).hexdigest():
            problems.append(f"{t}: mirror {declared_key} does not match {fp} on disk")
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
    # A currentai.* dependency keeps a read-only MIRROR file (ADR-003): it is not a governed
    # asset, but the file is tracked, so the dependency claims it and the "every managed file
    # appears exactly once" gate still holds across both files.
    for dep in dependencies():
        for role, value in (dep.get("files") or {}).items():
            for path in (value if isinstance(value, list) else [value]):
                if path:
                    owned.setdefault(path, f"dependency:{dep['table']}:{role}")
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

    A governed model file, or a `build/` module named in an asset's `producer`. Only these
    paths (and the audit roots) are readers in the root-scoped graph, so a standalone notebook
    that merely reads a table is never a root (ADR-003 gate 5).
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


def _sources_compiled(asset: dict) -> bool:
    """A governed output compiled from sources/ by a serializer (so sources/ is its real root)."""
    return "serialize" in str(asset.get("producer") or "")


def governed_internal_edges() -> set[tuple[str, str]]:
    """governed table -> governed table, where the downstream's producer file reads the upstream.

    Real edges from the tree, not invented: sources/ links are added only for serializer-compiled
    outputs (see render_dag), never by "has no detected upstream".
    """
    governed = {tbl: a for tbl, a in by_table().items() if a.get("role")}
    producers = _governed_producer_paths()
    graph = derive_graph()
    edges: set[tuple[str, str]] = set()
    for path, refs in graph["reads"].items():
        for target in producers.get(path, []):
            for up in refs["internal"]:
                if up in governed and up != target:
                    edges.add((up, target))
    return edges


def unreachable_repo_computations() -> list[str]:
    """ADR-003 gate 4: every ACTIVE repo-computation and governed-data table is
    reachable upstream from a governed sink or a named audit root.

    A staged or dormant asset is pre-service (no consumer yet by construction) and is exempt;
    an active intermediate that nothing governed reads is a dead node the closure should not carry.
    """
    needed = needed_tables()
    problems: list[str] = []
    for a in assets():
        if a.get("role") in ("repo-computation", "governed-data") and a["status"] == "active":
            if a["table"] not in needed:
                problems.append(
                    f"{a['id']}: active {a['role']} not reachable from any governed sink or "
                    "audit root -- a dead node in the governed graph (gate 4)"
                )
    return problems


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
    standalone notebook (gate 5). Edges are real reads: a sources/ link is drawn only for a
    serializer-compiled output, never invented from a missing upstream. Node status carries
    through (staged dashed, dormant faded) so a pre-service asset never reads as live.
    """
    governed = {tbl: a for tbl, a in by_table().items() if a.get("role")}
    role_of = {tbl: a["role"] for tbl, a in governed.items()}
    status_of = {tbl: a["status"] for tbl, a in governed.items()}
    internal = governed_internal_edges()
    deps = dependencies()
    dep_stripped = {d["table"].removeprefix("currentai.") for d in deps}
    producers = _governed_producer_paths()
    dep_model = _dependency_model_files()  # stripped dep table -> mirror file
    file_produces_dep = {mf: t for t, mf in dep_model.items()}

    out: list[str] = []

    # View 1 -- map governance: sources/ -> serializer-compiled outputs + the real computation chain.
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
    for tbl in sorted(governed):
        if role_of[tbl] == "governed-output" and _sources_compiled(governed[tbl]):
            body.append(f"  SRC --> {_node(tbl)}")
    for up, dn in sorted(internal):
        if role_of.get(up) == "compatibility-shim" or role_of.get(dn) == "compatibility-shim":
            continue
        body.append(f"  {_node(up)} --> {_node(dn)}")
    for tbl in sorted(governed):
        if role_of[tbl] != "compatibility-shim" and status_of[tbl] != "active":
            body.append(f"  class {_node(tbl)} {status_of[tbl]};")
    body += ["  classDef src fill:#def;", "  classDef staged stroke-dasharray: 4 3;",
             "  classDef dormant opacity:0.5;"]
    out += _fence("View 1 — Map governance (sources → governed outputs)", body)

    # View 2 -- runtime dependencies: dependencies.yaml inputs -> the governed/dep files reading
    # them. dep->dep edges show the platform openness chain the repo's parity gate reaches into.
    body = []
    edges2: set[tuple[str, str]] = set()
    for dep_full, files in sorted(dependency_readers().items()):
        for f in files:
            for gt in producers.get(f, []):
                edges2.add((dep_full, f"currentai.{gt}"))
            if f in file_produces_dep:
                edges2.add((dep_full, f"currentai.{file_produces_dep[f]}"))
            if f in AUDIT_ROOTS:
                edges2.add((dep_full, f))
    dep_nodes = {d["table"] for d in deps}
    for a, b in sorted(edges2):
        astyle = ":::dep" if a in dep_nodes else ""
        bstyle = ":::dep" if b in dep_nodes else (":::audit" if b in AUDIT_ROOTS else "")
        body.append(f"  {_node(a)}[{a}]{astyle} --> {_node(b)}[{b}]{bstyle}")
    if not edges2:
        body.append("  none[no external runtime dependencies]:::src")
    body += ["  classDef dep fill:#eee;", "  classDef audit fill:#ffd;", "  classDef src fill:#def;"]
    out += _fence("View 2 — Runtime dependencies (dependencies.yaml → map computation)", body)

    # View 3 -- compatibility / retirement appendix: shims -> their replacements.
    body = []
    shim = sorted(
        (tbl, governed[tbl]["replacement"].removeprefix("currentai."))
        for tbl in governed if role_of[tbl] == "compatibility-shim" and governed[tbl].get("replacement")
    )
    if shim:
        for src, repl in shim:
            body.append(f"  {_node(src)}[{src}]:::compat --> {_node(repl)}[{repl}]")
    else:
        body.append("  none[no compatibility shims]:::src")
    body += ["  classDef compat stroke-width:3px;", "  classDef src fill:#def;"]
    out += _fence("View 3 — Compatibility / retirement appendix", body)

    return "\n".join(out).rstrip() + "\n"


def notebook_root_violations() -> list[str]:
    """ADR-003 gate 5: no standalone notebook is a reachability root of the governed graph.

    A notebook path must never appear as a producer of a governed table or in the governed
    roots, so a notebook read cannot pull a table into the DAG or confer membership.
    """
    problems: list[str] = []
    for path in set(_governed_producer_paths()) | _governed_root_files():
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


def merge_base_dependencies(base: str = "origin/main") -> list[dict] | None:
    """The dependency manifest as of the merge base, or None if it did not exist there."""
    try:
        merge_base = subprocess.run(
            ["git", "-C", str(ROOT), "merge-base", "HEAD", base],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{merge_base}:warehouse/dependencies.yaml"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return (yaml.safe_load(blob) or {}).get("dependencies") or []


def _compare_mirror(label: str, prior: dict, cur: dict, has_migration: bool) -> list[str]:
    """The provenance-coherence rules for one mirror across two commits.

    Bytes and provenance move together and forward: if `local_sha256` changed, `revision` must
    advance, `hash` must change, and `synced_at` must not go backward; if the bytes did NOT
    change, none of the provenance may. `model_id` is stable unless a migration authorizes it.
    """
    problems: list[str] = []
    if cur.get("model_id") != prior.get("model_id") and not has_migration:
        problems.append(
            f"{label}: model_id changed from {prior.get('model_id')} to {cur.get('model_id')} "
            "with no migration authorizing it"
        )
    # The byte identity is the COMPLETE claimed artifact: the model AND, when present, the
    # schema. A schema-only edit is a byte change and must advance the revision just like a
    # model edit -- otherwise a contributor could rewrite a schema, bump schema_sha256, and
    # freeze the revision.
    bytes_moved = (cur.get("local_sha256") != prior.get("local_sha256")
                   or cur.get("schema_sha256") != prior.get("schema_sha256"))
    if not bytes_moved:
        if any(cur.get(f) != prior.get(f) for f in ("revision", "hash", "synced_at")):
            problems.append(f"{label}: provenance changed but the mirrored bytes did not")
        return problems
    old_rev, new_rev = prior.get("revision"), cur.get("revision")
    if isinstance(old_rev, int) and isinstance(new_rev, int):
        if new_rev <= old_rev:
            problems.append(
                f"{label}: bytes changed but revision went {old_rev} -> {new_rev}; a refetch advances it"
            )
    elif new_rev == old_rev:
        problems.append(f"{label}: bytes changed but revision did not")
    if cur.get("hash") == prior.get("hash"):
        problems.append(f"{label}: bytes changed but the platform hash did not")
    old_at, new_at = str(prior.get("synced_at") or ""), str(cur.get("synced_at") or "")
    if new_at < old_at:
        problems.append(f"{label}: synced_at moved backward, {old_at} -> {new_at}")
    return problems


def mirror_provenance_violations(base: str = "origin/main") -> list[str]:
    """Governed-asset mirror entries whose bytes moved without their provenance moving with them.

    `synced_at` is per entry for exactly this reason: it was one global date until 2026-08-16,
    which meant refetching two models advanced the date on all twelve.
    """
    before = merge_base_assets(base)
    if before is None:
        return []
    old = {a["id"]: a["mirror"] for a in before if a.get("mirror")}
    problems: list[str] = []
    for asset in assets():
        cur, prior = asset.get("mirror"), old.get(asset["id"])
        if not cur or not prior:
            continue
        problems += _compare_mirror(asset["id"], prior, cur, bool(asset.get("mirror_migration")))
    return problems


def _merge_base_sha(base: str = "origin/main") -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), "merge-base", "HEAD", base],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _git_blob_sha256(sha: str, path: str) -> str | None:
    """sha256 of a file's bytes at a given commit, or None if it did not exist there."""
    try:
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{sha}:{path}"],
            capture_output=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return hashlib.sha256(blob).hexdigest()


def dependency_mirror_provenance_violations(base: str = "origin/main") -> list[str]:
    """Cross-commit provenance for currentai.* DEPENDENCY mirrors -- the protection a single-snapshot
    check cannot give, since a contributor can edit a mirrored file and update its hash to match.

    The byte identity is the model AND, when the contract claims a schema file, the schema
    (`schema_sha256`): a schema-only edit is a byte change and must advance the revision like a model
    edit. Prior provenance is the same mirror in the merge-base `dependencies.yaml`.
    """
    before = merge_base_dependencies(base)
    if before is None:
        return []
    prior = {d["table"]: d["mirror"] for d in before if d.get("mirror")}
    problems: list[str] = []
    for d in dependencies():
        cur, was = d.get("mirror"), prior.get(d["table"])
        if not cur or not was:
            continue
        problems += _compare_mirror(d["table"], was, cur, bool(d.get("mirror_migration")))
    return problems


COUNT_CLAIMS = {
    "assets": lambda: len(assets()),
    "no_reviewed_consumer": lambda: len(no_reviewed_consumers()),
    "deployed_tables": lambda: len(deployed_tables()),
    "staged_assets": lambda: sum(1 for a in assets() if a["status"] == "staged"),
    "dormant_assets": lambda: sum(1 for a in assets() if a["status"] == "dormant"),
    "tracked_warehouse_files": lambda: len(subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "warehouse"],
        capture_output=True, text=True, check=True,
    ).stdout.split()),
    "model_files": lambda: len(
        [f for f in produced_files() if f.endswith((".sql", ".py"))]
    ),
    "retirement_candidates": lambda: len(retirement_candidates()),
    "in_repo_readers": lambda: len(derive_graph()["read_by"]),
    "governed_assets": lambda: sum(1 for a in assets() if a.get("role")),
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
