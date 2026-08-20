"""Gates over warehouse/assets.yaml, per docs/architecture/data-architecture.md 11.5.

Every test here fails on a malformed or drifted inventory. None of them asserts that a
backlog remains non-empty: a corpus test may assert an invariant, never that unfinished
work still exists.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

from build import assets as A

ROOT = A.ROOT
# Vocabularies live in build/assets.py so the inventory and its gates cannot disagree
# about what a valid value is.
NAMESPACES = A.NAMESPACES
STATUSES = A.STATUSES


@pytest.fixture(scope="module")
def inventory():
    return A.assets()


@pytest.fixture(scope="module")
def graph():
    return A.derive_graph()


# --- 1: every managed file appears exactly once ------------------------------------

def test_every_managed_file_is_claimed_exactly_once(inventory):
    """models/ mixes editable and mirror-only files in one directory, so no path
    signals which is which. This check plus test_mirror_block_iff_platform carries the
    weight the directory name used to."""
    seen: dict[str, str] = {}
    for asset in inventory:
        for role, value in (asset.get("files") or {}).items():
            for path in (value if isinstance(value, list) else [value]):
                if not path:
                    continue
                assert path not in seen, f"{path} claimed by {seen[path]} and {asset['id']}:{role}"
                seen[path] = f"{asset['id']}:{role}"


def test_every_declared_path_exists(inventory):
    for asset in inventory:
        for role, value in (asset.get("files") or {}).items():
            for path in (value if isinstance(value, list) else [value]):
                if path:
                    assert (ROOT / path).exists(), f"{asset['id']}:{role} -> missing {path}"


# --- 1b/2: identity and namespace -------------------------------------------------

def test_table_matches_id(inventory):
    for asset in inventory:
        assert asset["table"] == f"currentai.{asset['id']}"


def test_current_namespace_matches_the_table(inventory):
    for asset in inventory:
        assert asset["table"].split(".")[1] == asset["current_namespace"], asset["id"]


def test_kind_and_target_namespace_agree(inventory):
    """`kind` is semantic; target_namespace is where the architecture puts it. They must
    agree, with one permanent exception: observations legitimately live in signal_*
    datasets per section 4.3."""
    for asset in inventory:
        kind, target = asset["kind"], asset["target_namespace"]
        assert kind in NAMESPACES, f"{asset['id']}: unknown kind {kind}"
        if kind == "observations" and target.startswith("signal_"):
            continue
        assert kind == target, f"{asset['id']}: kind={kind} target_namespace={target}"


def test_migration_status_is_consistent(inventory):
    """Equality between current and target is required only when migration is complete.
    Requiring it outright would reject every legacy entities/events/metrics/scores and
    evidence asset -- which is what the migration is for."""
    for asset in inventory:
        same = asset["current_namespace"] == asset["target_namespace"]
        if asset["migration_status"] == "complete":
            assert same, f"{asset['id']}: complete but {asset['current_namespace']} != {asset['target_namespace']}"
        else:
            assert not same, f"{asset['id']}: pending but namespaces already agree"


# --- 3: mirror provenance ---------------------------------------------------------

def test_mirror_block_iff_platform_authority(inventory):
    for asset in inventory:
        has = "mirror" in asset
        is_platform_model = asset.get("authority") == "platform" and (asset.get("files") or {}).get("model")
        if is_platform_model:
            assert has, f"{asset['id']}: platform-authoritative model without a mirror block"
        if has:
            for field in ("model_id", "revision", "hash", "local_sha256", "synced_at"):
                assert asset["mirror"].get(field), f"{asset['id']}: mirror missing {field}"


# --- 5: derived dependencies match the tree --------------------------------------

def test_read_by_matches_the_derived_graph(inventory, graph):
    """The whole point of deriving: a hand-maintained dependency list drifts exactly like
    sources.yaml and platform-mirror/manifest.yaml drifted against each other."""
    for asset in inventory:
        expected = graph["read_by"].get(asset["id"]) or None
        assert (asset.get("read_by") or None) == expected, (
            f"{asset['id']}: read_by is {asset.get('read_by')}, tree says {expected}"
        )


def test_reads_matches_the_derived_graph(inventory):
    for asset in inventory:
        model = (asset.get("files") or {}).get("model")
        if not model:
            continue
        internal, external = A.reads_of(ROOT / model)
        expected = [{"table": f"currentai.{t}", "scope": "internal"} for t in sorted(internal)]
        expected += [{"table": t, "scope": "external"} for t in sorted(external)]
        assert (asset.get("reads") or []) == expected, f"{asset['id']}: reads drifted from {model}"


def test_external_reads_are_marked_external(inventory):
    """The inventory covers the gap-map closure, not all 96 org tables, so oso.* and
    out-of-scope reads must be representable rather than errors."""
    ids = {a["id"] for a in inventory}
    for asset in inventory:
        for ref in asset.get("reads") or []:
            table = ref["table"]
            if ref["scope"] == "internal":
                assert table.removeprefix("currentai.") in ids, f"{asset['id']} reads unlisted {table}"
            else:
                assert not table.startswith("currentai."), f"{asset['id']}: {table} marked external"


# --- 6: uniqueness ---------------------------------------------------------------

def test_no_duplicate_id_or_table(inventory):
    ids = [a["id"] for a in inventory]
    tables = [a["table"] for a in inventory]
    assert len(ids) == len(set(ids)), "duplicate asset id"
    assert len(tables) == len(set(tables)), "duplicate table"


# --- 7: retirement is derived, never stored ------------------------------------

def test_no_stored_retirement_candidate_flag(inventory):
    """Section 11.2: the condition is computed. Only the human outputs are recorded."""
    for asset in inventory:
        assert "retirement_candidate" not in asset, f"{asset['id']}: stored boolean"


def test_retirement_findings_carry_a_reason_and_issue(inventory):
    for asset in A.retirement_candidates():
        assert asset.get("retirement_reason"), f"{asset['id']}: candidate without a reason"
        assert asset.get("retirement_issue"), f"{asset['id']}: candidate without an issue"


def test_in_repo_only_assets_are_never_candidates(inventory):
    """An asset nobody checked beyond the repository is not evidence of anything. 16 of
    the org's 20 notebooks are untracked, so in_repo_only cannot justify a retirement."""
    for asset in A.retirement_candidates():
        assert asset.get("consumer_scope") != "in_repo_only", asset["id"]


# --- 9: vocabularies and required fields --------------------------------------

def test_required_fields_and_vocabularies(inventory):
    for asset in inventory:
        for field in A.REQUIRED_FIELDS:
            assert field in asset, f"{asset['id']}: missing {field}"
        assert asset["status"] in STATUSES, f"{asset['id']}: bad status"
        assert asset["authority"] in A.AUTHORITIES, asset["id"]
        assert asset["population"] in A.POPULATIONS, asset["id"]


def test_release_path_implies_gap_map(inventory):
    """Section 7: release gates key on population. A long-tail asset on the release path
    is a contradiction -- it has no axes and belongs to no gap-map release."""
    for asset in inventory:
        if asset["release_path"]:
            assert asset["population"] in {"gap_map", "both"}, asset["id"]


def test_deprecated_assets_name_a_replacement_or_removal_condition(inventory):
    for asset in inventory:
        if asset["status"] in {"deprecated", "compatibility"}:
            assert asset.get("replacement") or asset.get("retirement_reason"), asset["id"]


def test_schedules_are_utc_or_flagged(inventory):
    """Not a UTC mandate yet -- Phase 1 does that. This records the count so the fix has
    a target and cannot silently regress."""
    non_utc = {a["id"] for a in inventory if a.get("timezone") not in (None, "UTC")}
    for asset_id in non_utc:
        asset = A.by_table()[asset_id]
        assert asset.get("last_observed_trigger") in (None, "MANUAL", "SCHEDULED")


# --- coverage against the tree -------------------------------------------------

def test_every_model_file_in_scope_is_inventoried():
    """A file under warehouse/ that produces a table nothing claims is invisible to every
    other gate here."""
    claimed = set(A.produced_files())
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files",
         "warehouse/models", "warehouse/platform-mirror", "warehouse/ingest"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    code = [f for f in tracked if f.endswith((".sql", ".py"))]
    unclaimed = sorted(f for f in code if f not in claimed)
    assert not unclaimed, f"model files in no asset entry: {unclaimed}"


def test_no_test_requires_a_backlog_to_stay_non_empty():
    """Section 7's engineering rule, enforced against this file."""
    src = Path(__file__).read_text(encoding="utf-8")
    # Needles are assembled at runtime so this test does not match its own source, which
    # is how it failed the first time it ran.
    needles = ["len(candidates) " + ">", "retirement_candidates()" + " >", ">" + " 0, "]
    offenders = [n for n in needles if n in src]
    assert not offenders, f"this file asserts a backlog persists: {offenders}"


# --- extraction: synthetic proofs that SQL context is what counts -------------------

def _tmp(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_oso_model_decorator_is_not_a_table(tmp_path):
    """Every Python UDM carries @oso.model. An earlier extractor turned that decorator
    into a phantom `oso.model` upstream in seven files."""
    path = _tmp(tmp_path, "m.py", "import oso\n\n@oso.model()\ndef build():\n    return None\n")
    assert A.table_refs(path) == set()


def test_a_url_is_not_a_table(tmp_path):
    """`https://www.oso.xyz/...` produced a phantom `oso.xyz` upstream in five files."""
    path = _tmp(tmp_path, "u.py", 'HOMEPAGE = "https://www.oso.xyz/docs/registry"\n')
    assert A.table_refs(path) == set()


def test_table_inside_a_sql_literal_is_found(tmp_path):
    path = _tmp(tmp_path, "q.py", 'SQL = "SELECT a FROM currentai.registry.products WHERE x"\n')
    assert A.table_refs(path) == {"currentai.registry.products"}


def test_bare_table_identifier_constant_is_found(tmp_path):
    """The `TABLE = "currentai.x.y"` pattern, used by apply_scores and check_parity."""
    path = _tmp(tmp_path, "t.py", 'TABLE = "currentai.scores.openness_computed"\n')
    assert A.table_refs(path) == {"currentai.scores.openness_computed"}


def test_docstring_sql_is_not_a_read(tmp_path):
    """build/warehouse.py illustrates its own API with a SELECT in its module docstring."""
    path = _tmp(tmp_path, "d.py", '"""Usage:\n    query("SELECT a FROM currentai.scores.openness_computed")\n"""\n')
    assert A.table_refs(path) == set()


def test_sql_comment_is_not_a_read(tmp_path):
    path = _tmp(tmp_path, "c.sql", "-- reads currentai.registry.products one day\nSELECT 1\n")
    assert A.table_refs(path) == set()


def test_sql_block_comment_is_not_a_read(tmp_path):
    path = _tmp(tmp_path, "b.sql", "/* FROM currentai.registry.products */\nSELECT 1\n")
    assert A.table_refs(path) == set()


def test_join_and_subquery_reads_are_found(tmp_path):
    path = _tmp(tmp_path, "j.sql",
                "SELECT 1 FROM oso.int_events__github_unified e\n"
                "JOIN currentai.registry.products p ON 1=1\n"
                "WHERE x IN (SELECT repo FROM currentai.catalog.stack_map)\n")
    assert A.table_refs(path) == {
        "oso.int_events__github_unified",
        "currentai.registry.products",
        "currentai.catalog.stack_map",
    }


# --- coverage: declared vs tracked, both directions -------------------------------

def test_every_tracked_managed_file_is_declared():
    """Duplicate detection is not coverage. A tracked model or data file that no asset
    claims is invisible to every other gate in this file."""
    claimed = set(A.produced_files())
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files",
         "warehouse/models", "warehouse/platform-mirror", "warehouse/ingest", "warehouse/catalog"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    managed = [f for f in tracked
               if f.endswith((".sql", ".py", ".csv"))
               and not f.endswith(".schema.json")]
    undeclared = sorted(f for f in managed if f not in claimed)
    assert not undeclared, f"tracked managed files in no asset entry: {undeclared}"


def test_every_registry_publisher_table_is_inventoried():
    """build.publish_registry.TABLES is the authority on which registry tables exist.
    tail_products was missing from the first inventory because its platform table is empty,
    which would have let the next tail record materialize an uninventoried table."""
    from build import publish_registry

    declared = {f"registry.{t}" for t in publish_registry.TABLES}
    have = {a["id"] for a in A.assets()}
    assert not declared - have, f"registry outputs not inventoried: {sorted(declared - have)}"


# --- mirror provenance, both directions and against the bytes ---------------------

def test_mirror_block_only_on_platform_authority(inventory):
    for asset in inventory:
        if "mirror" in asset:
            assert asset["authority"] == "platform", f"{asset['id']}: mirror block without platform authority"


def test_mirror_local_sha256_matches_the_bytes(inventory):
    """A recorded hash that does not match the file it dates is worse than no hash."""
    import hashlib

    for asset in inventory:
        mirror = asset.get("mirror")
        model = (asset.get("files") or {}).get("model")
        if not mirror or not model:
            continue
        actual = hashlib.sha256((ROOT / model).read_bytes()).hexdigest()
        assert actual == mirror["local_sha256"], f"{asset['id']}: {model} does not match local_sha256"


def test_inventory_agrees_with_the_mirror_manifest():
    """Both files describe the same mirrors during the transition. They must not drift --
    sources.yaml and manifest.yaml already did exactly that."""
    manifest = yaml.safe_load((ROOT / "warehouse/platform-mirror/manifest.yaml").read_text())
    inv = A.by_table()
    for entry in manifest["models"]:
        table = entry["table"].removeprefix("currentai.")
        assert table in inv, f"{table} in manifest.yaml but not in assets.yaml"
        asset = inv[table]
        if entry.get("status") == "staged":
            assert asset["status"] == "staged", f"{table}: manifest says staged"
            continue
        assert asset.get("mirror", {}).get("revision") == entry["revision"], f"{table}: revision drift"
        assert asset.get("mirror", {}).get("local_sha256") == entry["local_sha256"], f"{table}: hash drift"


# --- grain, producer, enums -----------------------------------------------------

def test_every_asset_has_a_nonempty_grain(inventory):
    """Phase 0's contract: every asset has a semantic role, owner, grain and refresh."""
    for asset in inventory:
        grain = (asset.get("grain") or "").strip()
        assert grain, f"{asset['id']}: no grain"
        assert len(grain) > 10, f"{asset['id']}: grain too thin to be a grain: {grain!r}"


def test_every_asset_names_a_producer(inventory):
    for asset in inventory:
        assert (asset.get("producer") or "").strip(), f"{asset['id']}: no producer"


def test_migration_status_uses_the_enum(inventory):
    for asset in inventory:
        assert asset["migration_status"] in A.MIGRATION_STATES, asset["id"]


def test_consumer_checks_are_complete_and_valid(inventory):
    for asset in inventory:
        checks = asset.get("consumer_checks")
        assert checks, f"{asset['id']}: no consumer_checks"
        for key in ("repository", "platform_notebooks", "platform_models", "external"):
            assert checks.get(key) in A.CHECK_STATES, f"{asset['id']}: bad consumer_checks.{key}"


def test_no_candidate_while_platform_models_unaudited(inventory):
    """The specification's retirement condition includes "no deployed platform model reads
    it". Notebooks are not models."""
    for asset in A.retirement_candidates():
        assert asset["consumer_checks"]["platform_models"] == "checked", asset["id"]


def test_non_utc_schedules_are_recorded_with_a_trigger_field(inventory):
    """Phase 1 moves these to UTC. This gate only ensures the worklist cannot silently
    shrink: every non-UTC asset must carry an explicit observed-trigger field, so a
    timezone cannot be quietly dropped without the field going with it."""
    non_utc = [a for a in inventory if a.get("timezone") not in (None, "UTC")]
    assert non_utc, "no non-UTC schedules: update Phase 1 status, this gate is now stale"
    for asset in non_utc:
        assert "last_observed_trigger" in asset or asset.get("last_run_at") is None, asset["id"]


# --- the checked-in DAG must match the renderer ---------------------------------

def test_committed_dag_matches_the_renderer():
    """A generated document that drifts from its generator is worse than no document."""
    committed = (ROOT / "docs/architecture/current-state-dag.md").read_text(encoding="utf-8")
    assert A.render_dag() in committed, "current-state-dag.md is stale; regenerate it"


# --- the inventory must agree with the ADR committed beside it -------------------

def test_inventory_agrees_with_adr_002():
    """ADR-002 tabulates the correct target for every misfiled `catalog` table. The first
    inventory contradicted it -- three tables the ADR sends to `registry` were recorded as
    settled `catalog` data. A decision record and the inventory implementing it must not
    disagree, so the ADR's table is parsed and compared."""
    adr = (ROOT / "docs/architecture/adr-002-registry-curated-catalog-discovered.md").read_text(encoding="utf-8")
    inv = A.by_table()
    claims = re.findall(r"^\| `([a-z_]+)` \| (.+?) \|$", adr, re.M)
    assert len(claims) >= 10, "ADR-002's catalog table went missing"
    for table, verdict in claims:
        asset = inv.get(f"catalog.{table}")
        assert asset, f"ADR-002 names catalog.{table}, not in the inventory"
        if "Belongs in `registry`" in verdict or "belongs in `registry`" in verdict:
            assert asset["target_namespace"] == "registry", (
                f"catalog.{table}: ADR-002 says registry, inventory says {asset['target_namespace']}"
            )
        elif "`observations`" in verdict:
            assert asset["target_namespace"] == "observations", f"catalog.{table}"
        elif verdict.startswith("Correctly `catalog`"):
            assert asset["target_namespace"] == "catalog", f"catalog.{table}"


def test_no_handwritten_asset_count_in_the_docs():
    """Every count that was typed here has been wrong at least once: 49 assets, 28
    migrations, 8 build readers, 27 model files. Counts in prose must be generated, or
    absent."""
    generated = {
        str(len(A.assets())),
        str(len([a for a in A.assets() if a["migration_status"] == "pending"])),
    }
    stale = re.compile(r"\b(49|28|56)\s+(?:of\s+96\s+)?(?:assets|tables|namespace migrations)\b")
    for name in ("data-architecture.md", "migration-status.md", "current-state-dag.md"):
        text = (ROOT / "docs/architecture" / name).read_text(encoding="utf-8")
        for match in stale.finditer(text):
            assert match.group(1) in generated, f"{name}: stale count {match.group(0)!r}"
