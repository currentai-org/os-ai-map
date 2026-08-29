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


def test_path_derives_the_table(inventory):
    """Gate 1b: models/<dataset>/<table>.<ext> and data/<dataset>/<table>.csv must derive
    the declared `currentai.<dataset>.<table>`. This replaces the old filename-convention
    check -- a misplaced file fails here rather than being accepted under a plausible name.

    Only the model, schema and data roles carry a table identity. An intermediate CSV
    (data/catalog/top_models.csv) is a fetcher's scratch input that shares a directory with
    a table but is not one, so it is skipped by role, not by guessing."""
    checked = 0
    for asset in inventory:
        for role in ("model", "schema", "data"):
            value = (asset.get("files") or {}).get(role)
            for path in (value if isinstance(value, list) else [value]):
                if not path:
                    continue
                derived = A.table_for_path(path)
                assert derived is not None, f"{asset['id']}:{role} -> {path} is not in the mirror layout"
                assert derived == asset["table"], (
                    f"{asset['id']}:{role} -> {path} derives {derived}, not {asset['table']}"
                )
                checked += 1
    assert checked, "no model/schema/data paths were checked -- the derivation is not running"


def test_current_namespace_matches_the_table(inventory):
    for asset in inventory:
        assert asset["table"].split(".")[1] == asset["current_namespace"], asset["id"]


def test_kind_and_target_namespace_agree(inventory):
    """`kind` is semantic; target_namespace is where the architecture puts it. They must
    agree, with two exceptions:

    - observations legitimately live in signal_* datasets per section 4.3; and
    - a `migration_status: not_planned` asset is deliberately NOT migrated — it stays in its
      current namespace (target == current) and retires, is superseded, or is physically blocked
      in place, so its target need not equal its `kind`. This covers three families: the three
      `signal_*.product_adoption` compatibility/staged tables and the Phase 7 openness chain
      (`scores.openness_facts`/`openness_computed`, `evidence.product_evidence`), all `kind:
      evaluation` but retired not relocated; and the scheduled `entities.*` (`kind: catalog`) and
      `scores.*` (`kind: evaluation`) pipelines, which stay put because their static target
      datasets cannot host a scheduled `USER_MODEL` model (data-architecture.md §11.1, #393).
    """
    for asset in inventory:
        kind, target = asset["kind"], asset["target_namespace"]
        assert kind in NAMESPACES, f"{asset['id']}: unknown kind {kind}"
        if asset["migration_status"] == "not_planned":
            continue  # retirement-in-place: stays put (target == current), not relocated to its kind
        if kind == "observations" and target.startswith("signal_"):
            continue
        assert kind == target, f"{asset['id']}: kind={kind} target_namespace={target}"


def test_migration_status_is_consistent(inventory):
    """Namespaces must AGREE when the asset is not going to move -- `complete` (already moved)
    or `not_planned` (deliberately staying put / retiring in place) -- and must DIFFER while a
    move is still outstanding (`pending`, `in_progress`). Requiring agreement outright would
    reject every `events`/`metrics`/`catalog.*` asset still awaiting its move, which is what the
    migration is for; permitting it for `pending` would let a false "already there" slip through.
    (`entities.*` and `scores.*` are no longer awaiting a move — they are `not_planned`, blocked by
    the dataset-type constraint, so they are in the settled branch below.)"""
    settled = {"complete", "not_planned"}
    for asset in inventory:
        same = asset["current_namespace"] == asset["target_namespace"]
        if asset["migration_status"] in settled:
            assert same, (
                f"{asset['id']}: {asset['migration_status']} but "
                f"{asset['current_namespace']} != {asset['target_namespace']}")
        else:
            assert not same, f"{asset['id']}: {asset['migration_status']} but namespaces already agree"


def test_source_collectors_are_not_reclassified_to_observations(inventory):
    """Source-specific ingestion stays in `signal_*` per `data-architecture.md` §4.3: a
    `kind: observations` table in a `signal_*` namespace is permanently legitimate, so a
    source collector must not be relocated to the `observations` namespace on the strength
    of its `kind` alone. The only relocation Phase 5 still sanctions is the
    `catalog.*->registry` ownership transitions -- never `signal_*->observations`. (All the
    scheduled long-tail pipelines stay put under `not_planned`: `entities->catalog` and
    `scores->evaluation` were cancelled by the dataset-type wall, and `events`/`metrics->observations`
    by the dataset-schedule wall; #393. Phase 2B owns only the observations refresh-model question,
    and any later relocation would require a new architecture decision.) A Phase 5 pilot that relocated
    `signal_semanticscholar.paper_citations` to `observations` was rolled back; this gate keeps
    the mistake from recurring.

    The rule is simple and complete: every `kind: observations` asset currently in a
    `signal_*` namespace must target that same namespace. The `kind: observations` predicate is
    what scopes it to source collectors. The `signal_*.product_adoption` per-source adoption
    tables are `kind: evaluation`, so they are outside THIS gate -- but they do not relocate to
    `evaluation` either: they are `migration_status: not_planned` (retire in place), enforced
    separately by `test_signal_product_adoption_tables_stay_put_and_deployed_ones_are_compat`.
    The `repo_state`/`hub_state` twins similarly stay in `signal_*` like any other collector. An
    explicit future architecture change may amend this gate.
    """
    for asset in inventory:
        if not asset["current_namespace"].startswith("signal_"):
            continue
        if asset["kind"] != "observations":
            continue
        assert asset["target_namespace"] == asset["current_namespace"], (
            f"{asset['id']}: source collector declares target_namespace "
            f"{asset['target_namespace']!r} -- a signal_* kind: observations collector stays "
            f"in signal_* (§4.3) and is not reclassified on the strength of its kind"
        )


def test_not_planned_assets_stay_put_with_a_documented_disposition(inventory):
    """`migration_status: not_planned` means "no namespace move under the currently accepted
    architecture" (§11.5). It must keep the asset in its current namespace (target == current, no
    false relocation claim) and document WHY it will not move -- a `replacement` it is superseded by,
    a `retirement_reason`, or a `not_planned_reason` naming an accepted cause (retirement/supersession,
    immutable dataset-type incompatibility, or dataset-schedule isolation). This is what lets the
    scheduled long-tail pipelines and the earlier corrections drop out of the `pending` move set
    without pretending they will relocate."""
    for asset in inventory:
        if asset["migration_status"] != "not_planned":
            continue
        assert asset["current_namespace"] == asset["target_namespace"], (
            f"{asset['id']}: not_planned must target its current namespace, not "
            f"{asset['target_namespace']!r} (no relocation)")
        assert (asset.get("not_planned_reason") or asset.get("replacement")
                or asset.get("retirement_reason")), (
            f"{asset['id']}: not_planned requires a documented not-planned disposition "
            f"(retirement/supersession, dataset-type, or dataset-schedule constraint)")


def test_signal_product_adoption_tables_stay_put_and_deployed_ones_are_compat(inventory):
    """The three `signal_*.product_adoption` per-source banding tables are superseded by the
    central observations + evaluation layer (data-architecture.md §11.1). Two invariants, held
    apart because supersession-today and namespace-target are different questions:

    1. NONE of the three relocates: each is `migration_status: not_planned` and never targets
       `evaluation` (correcting the misfiled `target_namespace: evaluation` the Phase-5 plan
       flagged).
    2. The DEPLOYED ones (`signal_github`, `signal_huggingface`) are live compatibility shims:
       `status: compatibility` naming `observations.product_adoption_current` as `replacement`.
       The staged sibling (`signal_packages`, never deployed, #314) is exempt -- a table that
       never entered service is not a live shim, and marking it compatibility would assert a
       supersession that never happened.
    """
    seen = 0
    for asset in inventory:
        if not (asset["table"].endswith(".product_adoption")
                and asset["current_namespace"].startswith("signal_")):
            continue
        seen += 1
        assert asset["migration_status"] == "not_planned", (
            f"{asset['id']}: must be migration_status: not_planned (it does not migrate), "
            f"not {asset['migration_status']!r}")
        assert asset["target_namespace"] != "evaluation", (
            f"{asset['id']}: must not target evaluation -- it is superseded and retires in "
            f"place, not relocated")
        if not asset.get("materialized"):
            continue  # staged / never deployed -- not a live compatibility shim
        assert asset["status"] == "compatibility", (
            f"{asset['id']}: a deployed signal_*.product_adoption table must be "
            f"status: compatibility (a superseded shim per §11.1), not {asset['status']!r}")
        assert asset.get("replacement") == "currentai.observations.product_adoption_current", (
            f"{asset['id']}: must name observations.product_adoption_current as its replacement")
    assert seen == 3, f"expected the three signal_*.product_adoption tables, saw {seen}"


def test_phase7_openness_chain_stays_put_until_retirement(inventory):
    """The Phase 7 / §9.3 openness chain -- `evidence.product_evidence`, `scores.openness_facts`,
    `scores.openness_computed` -- is RETIRED (deleted), never relocated to `evaluation`, once the
    repository-owned trace (`evaluation.axis_*`) shows multi-release dual-run agreement (#384).
    So each is `migration_status: not_planned` and never targets `evaluation`, and stays `active`
    (not prematurely marked `compatibility`) until Phase 7 actually retires it."""
    chain = {"currentai.evidence.product_evidence",
             "currentai.scores.openness_facts", "currentai.scores.openness_computed"}
    seen = set()
    for asset in inventory:
        if asset["table"] not in chain:
            continue
        seen.add(asset["table"])
        assert asset["migration_status"] == "not_planned", (
            f"{asset['id']}: Phase 7 retirement target must be migration_status: not_planned, "
            f"not {asset['migration_status']!r}")
        assert asset["target_namespace"] != "evaluation", (
            f"{asset['id']}: retired in Phase 7, not relocated to evaluation")
        assert asset["status"] == "active", (
            f"{asset['id']}: stays active until Phase 7 retirement, not {asset['status']!r}")
    assert seen == chain, f"missing openness-chain entries: {sorted(chain - seen)}"


def test_scheduled_pipelines_do_not_relocate_into_static_namespaces(inventory):
    """The `entities.*` (kind: catalog) and analytical `scores.*` (kind: evaluation) tables are
    scheduled USER_MODEL pipelines. Their `kind` target namespaces -- `catalog` and `evaluation` --
    are static datasets (STATIC_MODEL / compiled release artifacts), and an OSO dataset's type is
    immutable, so a scheduled model cannot be hosted there (data-architecture.md §11.1, verified on
    the catalog case 2026-08-28, #393). So each is `migration_status: not_planned`, keeps its
    current namespace (never targeting `catalog`/`evaluation`), stays `active`, and documents the
    constraint in `not_planned_reason`. Its `kind` is unchanged -- the logical model is intact; this
    is the not_planned exception to `target_namespace == kind`.

    The eight `scores.*` here are the analytical chain (`dependency_graph`, `fragility`,
    `investment_ranking`, `ossd_coverage`, `project_summary`, `repos_summary`, `stack_contributors`,
    `taxonomy`) -- NOT the openness pair, which is a separate Phase 7 retirement gate above.
    """
    entities = {f"currentai.entities.{t}" for t in ("repos", "models", "packages", "projects")}
    scores = {f"currentai.scores.{t}" for t in (
        "dependency_graph", "fragility", "investment_ranking", "ossd_coverage",
        "project_summary", "repos_summary", "stack_contributors", "taxonomy")}
    blocked = entities | scores
    seen = set()
    for asset in inventory:
        if asset["table"] not in blocked:
            continue
        seen.add(asset["table"])
        static_ns = "catalog" if asset["table"] in entities else "evaluation"
        assert asset["migration_status"] == "not_planned", (
            f"{asset['id']}: a scheduled pipeline into a static namespace must be not_planned, "
            f"not {asset['migration_status']!r}")
        assert asset["target_namespace"] == asset["current_namespace"], (
            f"{asset['id']}: stays put -- target must equal current, not {asset['target_namespace']!r}")
        assert asset["target_namespace"] != static_ns, (
            f"{asset['id']}: must not target the static namespace {static_ns!r}")
        assert asset.get("not_planned_reason"), (
            f"{asset['id']}: must document the dataset-type constraint in not_planned_reason")
        assert asset["status"] == "active", (
            f"{asset['id']}: a live pipeline stays active, not {asset['status']!r}")
    assert seen == blocked, f"missing dataset-type-blocked entries: {sorted(blocked - seen)}"


def test_events_metrics_deferred_not_folded_into_observations(inventory):
    """`events.github_events` and `metrics.daily` are `kind: observations` and the `observations`
    dataset is type-compatible (USER_MODEL), but an OSO schedule is a dataset-level sweep and the
    observations dataset is currently manual (product_adoption_current runs MANUAL under the §18
    baseline discipline). Folding these two independently-scheduled pipelines in would force a sweep
    cron onto that §18-sensitive dataset, so they STAY PUT under `migration_status: not_planned`,
    kept in their own namespaces, never targeting `observations`, still `active`, with the constraint
    documented (data-architecture.md §11.1, #393). Phase 2B owns only the observations refresh-model
    question; any later relocation would require a new architecture decision, not an automatic
    follow-on."""
    deferred = {"currentai.events.github_events", "currentai.metrics.daily"}
    seen = set()
    for asset in inventory:
        if asset["table"] not in deferred:
            continue
        seen.add(asset["table"])
        assert asset["migration_status"] == "not_planned", (
            f"{asset['id']}: deferred fold must be not_planned, not {asset['migration_status']!r}")
        assert asset["current_namespace"] == asset["target_namespace"], (
            f"{asset['id']}: stays put -- target must equal current, not {asset['target_namespace']!r}")
        assert asset["target_namespace"] != "observations", (
            f"{asset['id']}: must not target observations while the fold is deferred")
        assert asset.get("not_planned_reason"), (
            f"{asset['id']}: must document the schedule constraint in not_planned_reason")
        assert asset["status"] == "active", (
            f"{asset['id']}: a live pipeline stays active, not {asset['status']!r}")
    assert seen == deferred, f"missing deferred events/metrics entries: {sorted(deferred - seen)}"


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
        # Truthiness is not enough: the field's whole claim is that a tracking issue EXISTS,
        # so a placeholder like 'TBD: open an issue' must fail here, not pass.
        assert A.is_retirement_issue_ref(asset.get("retirement_issue")), (
            f"{asset['id']}: retirement_issue {asset.get('retirement_issue')!r} is not a real "
            f"issue reference (#123 or a GitHub issues URL)"
        )


def test_issue_ref_validator_rejects_placeholders_and_prose():
    """The gate above is only as strong as this validator, so pin its edges."""
    assert A.is_retirement_issue_ref("#348")
    assert A.is_retirement_issue_ref("https://github.com/currentai-org/os-ai-map/issues/348")
    for bad in ("TBD: open an issue before any deletion", "", "  ", "issue 348", "#", "#abc",
                "see #348 later", None, 348):
        assert not A.is_retirement_issue_ref(bad), f"{bad!r} should not be a valid issue ref"


def test_a_staged_unread_asset_is_not_a_retirement_candidate(monkeypatch):
    """A model deployed nowhere cannot be retired -- it has no consumers because it does not
    exist yet, which is a different fact from a live table nobody reads. signal_packages.* is
    the live case (issue #314). Proven by construction: the same asset flips to a candidate
    only when its status is a deployed one."""
    base = {
        "id": "signal_x.staged_model", "read_by": {}, "publication_role": None,
        "external_consumers": "none_confirmed", "platform_model_consumers": None,
        "consumer_checks": {"repository": "checked", "platform_notebooks": "checked",
                            "platform_models": "checked", "external": "unknown"},
        "retirement_reason": "unread", "retirement_issue": "#1",
    }
    monkeypatch.setattr(A, "assets", lambda: [{**base, "status": "staged"}])
    assert A.retirement_candidates() == []
    assert A.no_reviewed_consumers() == []
    monkeypatch.setattr(A, "assets", lambda: [{**base, "status": "active"}])
    assert [a["id"] for a in A.retirement_candidates()] == ["signal_x.staged_model"]


def test_unaudited_consumer_sources_block_candidacy(inventory):
    """An asset nobody checked beyond the repository is not evidence of anything. 16 of
    the org's 20 notebooks are untracked, and no deployed model definition has been read.

    This replaces an assertion on the removed `consumer_scope` field, which could no longer
    fail: `asset.get("consumer_scope")` was always None, so `!= "in_repo_only"` always held.
    A gate that cannot fail is worse than no gate, because it reads as coverage."""
    for asset in A.retirement_candidates():
        checks = asset["consumer_checks"]
        for source in ("repository", "platform_notebooks", "platform_models"):
            assert checks[source] == "checked", f"{asset['id']}: {source} is {checks[source]}"


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
        ["git", "-C", str(ROOT), "ls-files", "warehouse/models"],
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
    needles = ["len(candidates) " + ">", "retirement_candidates()" + " >", ">" + " 0, ",
               "assert non_" + "utc,", "assert pending" + ",", "assert candidates" + ","]
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


# --- refs_in_source: the text entry point for deployed model code -------------------
# Deployed model definitions arrive as a string (the platform's latestRevision.code), not a
# file. refs_in_source runs the same rules as table_refs so a second extractor cannot drift.

def test_refs_in_source_finds_sql_context():
    assert A.refs_in_source(
        "SELECT a FROM currentai.registry.products JOIN currentai.catalog.stack_map ON 1=1", "sql"
    ) == {"currentai.registry.products", "currentai.catalog.stack_map"}


def test_refs_in_source_language_is_case_insensitive():
    """The platform records the language as `sql`, `SQL` or `python`; all must route."""
    code = "SELECT a FROM currentai.registry.products"
    assert A.refs_in_source(code, "SQL") == A.refs_in_source(code, "sql") == {"currentai.registry.products"}


def test_refs_in_source_python_literal_and_bare_identifier():
    assert A.refs_in_source('SQL = "SELECT a FROM currentai.registry.products"', "python") == {
        "currentai.registry.products"
    }
    assert A.refs_in_source('TABLE = "currentai.scores.openness_computed"', "python") == {
        "currentai.scores.openness_computed"
    }


def test_refs_in_source_excludes_python_docstrings():
    """The same docstring exclusion table_refs applies -- a model whose module docstring
    names its INPUT tables in prose must not have them counted as reads."""
    assert A.refs_in_source('"""Reads currentai.registry.products."""\nx = 1\n', "python") == set()


def test_refs_in_source_unquotes_trino_identifiers():
    assert A.refs_in_source('FROM "currentai"."registry"."products"', "sql") == {
        "currentai.registry.products"
    }


def test_refs_in_source_unknown_language_yields_only_depends_on():
    """An unrecognized language contributes only its explicit depends_on: declarations, never
    a guess from arbitrary text."""
    assert A.refs_in_source("-- depends_on: currentai.catalog.stack_map\nblah", "scala") == {
        "currentai.catalog.stack_map"
    }
    assert A.refs_in_source("FROM currentai.registry.products", "scala") == set()


def test_table_refs_delegates_to_refs_in_source(tmp_path):
    """table_refs is now refs_in_source over the file's bytes; the two must agree so the
    file-based graph and the platform audit extract identically."""
    code = "SELECT a FROM currentai.registry.products\n"
    path = _tmp(tmp_path, "d.sql", code)
    assert A.table_refs(path) == A.refs_in_source(code, "sql")


# --- coverage: declared vs tracked, both directions -------------------------------

def test_every_tracked_managed_file_is_declared():
    """Duplicate detection is not coverage. A tracked model or data file that no asset
    claims is invisible to every other gate in this file.

    `.parquet` counts because frozen bytes are a data asset like any other: the
    product_adoption_baseline capture would otherwise have been the first managed file this
    gate could not see."""
    claimed = set(A.produced_files())
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "warehouse/models", "warehouse/data"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    managed = [f for f in tracked
               if f.endswith((".sql", ".py", ".csv", ".parquet"))
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


def test_every_scheduled_asset_declares_a_timezone_and_trigger(inventory):
    """An invariant, not a backlog count. Any asset with a cron must say which timezone it
    is in and what trigger type was last observed -- so a schedule cannot be moved to UTC
    while quietly dropping the evidence that it ever ran.

    An earlier version of this gate asserted the non-UTC list was non-empty, which asserts
    a backlog persists. Section 7 forbids exactly that, and it would have failed the day
    Phase 1 finished its job."""
    scheduled = [a for a in inventory if str(a.get("refresh", "")).startswith("dataset cron")]
    for asset in scheduled:
        assert asset.get("timezone"), f"{asset['id']}: cron with no declared timezone"
        assert "last_observed_trigger" in asset, f"{asset['id']}: cron with no observed-trigger field"


# --- the checked-in DAG must match the renderer ---------------------------------

def test_committed_dag_matches_the_renderer():
    """A generated document that drifts from its generator is worse than no document.

    `render_dag()` emits its own fenced ```mermaid block, so the document must contain it EXACTLY
    once — a substring check alone passed a doubled fence (two openers, two closers) that a
    regeneration bug left behind and Mermaid renders as broken.
    """
    committed = (ROOT / "docs/architecture/current-state-dag.md").read_text(encoding="utf-8")
    rendered = A.render_dag()
    assert rendered in committed, "current-state-dag.md is stale; regenerate it"
    assert committed.count(rendered) == 1, "the rendered Mermaid block appears more than once"
    assert committed.count("```mermaid") == 1, "duplicate ```mermaid fence in current-state-dag.md"


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



def test_quoted_trino_identifiers_are_found(tmp_path):
    """`FROM "currentai"."registry"."x"` is the form every Python mirror model uses. An
    earlier extractor matched only the unquoted form and found these by accident, via a
    separate bare-name constant in the same file."""
    path = _tmp(tmp_path, "q.sql", 'SELECT a FROM "currentai"."registry"."products" WHERE 1\n')
    assert A.table_refs(path) == {"currentai.registry.products"}


def test_explicit_depends_on_is_found(tmp_path):
    """The escape hatch for a dependency no parser can see -- a name assembled at runtime,
    or read through a helper."""
    sql = _tmp(tmp_path, "d.sql", "-- depends_on: currentai.registry.products\nSELECT 1\n")
    py = _tmp(tmp_path, "d.py", "# depends_on: currentai.catalog.stack_map\nx = 1\n")
    assert A.table_refs(sql) == {"currentai.registry.products"}
    assert A.table_refs(py) == {"currentai.catalog.stack_map"}


def test_single_quoted_sql_value_is_not_an_identifier(tmp_path):
    """Unquoting identifiers must not rewrite a value. Trino quotes identifiers with
    double quotes and strings with single quotes."""
    path = _tmp(tmp_path, "v.sql", "SELECT a FROM t WHERE name = 'currentai.registry.products'\n")
    assert A.table_refs(path) == set()

# --- counts, provenance and comment handling -------------------------------------

def test_every_marked_count_matches_its_derived_value():
    """Structural, not a denylist. The gate this replaces scanned prose for numbers that
    had already been wrong -- 49, 28, 56 -- so by construction it could not catch the next
    one, and it did not catch a stale 31 against an actual 34."""
    violations = A.count_claim_violations()
    assert not violations, "stale counts:\n" + "\n".join(violations)


def test_architecture_docs_have_no_unmarked_asset_or_table_counts():
    """A count of assets or tables in prose must carry a marker naming what it counts, or a
    reader cannot tell a derived figure from a typed one either.

    Named for what it checks. An earlier version was called "no unmarked counts" while
    matching only `NN assets`, which left `49 tables in the closure` and `30 model files`
    unmarked under a name implying they were covered."""
    # Covers every noun the architecture docs count. "tracked files" was one that slipped
    # through: 44 was unmarked because the pattern named tables and assets only. "datasets"
    # was the next -- a stale "25 datasets" in a reference doc against an audited 22 showed the
    # gate did not police the dataset count either.
    pattern = re.compile(
        r"\b(\d{2,3})\s+(?:assets|tables|model files|tracked files|tracked warehouse files|datasets)\b"
    )
    for path in sorted((ROOT / "docs" / "architecture").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            before = text[max(0, match.start() - 44):match.start()]
            assert "count:" in before or "observed:" in before, (
                f"{path.name}: unmarked count {match.group(0)!r}"
            )


def test_observed_counts_carry_a_date():
    """Some figures are facts about the platform that this repository cannot derive -- the
    org holds tables in datasets the inventory does not cover. Those carry
    `<!-- observed:YYYY-MM-DD -->` so a reader can see they are a dated reading rather than
    a live value, instead of being silently exempt from the count gate."""
    marker = re.compile(r"<!--\s*observed:([^\s>]*)\s*-->")
    for path in sorted((ROOT / "docs" / "architecture").glob("*.md")):
        for stamp in marker.findall(path.read_text(encoding="utf-8")):
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamp), (
                f"{path.name}: observed marker without a date: {stamp!r}"
            )


def test_inline_sql_comment_is_not_a_read(tmp_path):
    """`SELECT 1 -- FROM currentai.registry.products` invented a dependency: the stripper
    removed whole-line comments but not trailing ones."""
    path = _tmp(tmp_path, "i.sql", "SELECT 1 -- FROM currentai.registry.products\n")
    assert A.table_refs(path) == set()


def test_a_double_dash_inside_a_value_is_not_a_comment(tmp_path):
    """The fix must not overshoot: `--` occurs inside string values, and treating it as a
    comment there would silently drop the rest of a real query."""
    path = _tmp(tmp_path, "v.sql", "SELECT '--' AS dash FROM currentai.registry.products\n")
    assert A.table_refs(path) == {"currentai.registry.products"}


def test_doubled_quote_escape_does_not_break_scanning(tmp_path):
    path = _tmp(tmp_path, "e.sql", "SELECT 'it''s' FROM currentai.catalog.stack_map\n")
    assert A.table_refs(path) == {"currentai.catalog.stack_map"}


def test_mirror_provenance_has_no_violations_against_the_merge_base():
    """Corpus assertion. Returns nothing on the PR that introduces assets.yaml, because
    there is no prior version to compare, and applies on every PR after it."""
    violations = A.mirror_provenance_violations()
    assert not violations, "mirror provenance:\n" + "\n".join(violations)


def test_merge_base_gate_catches_a_silent_byte_swap(monkeypatch):
    """Synthetic. The case the gate exists for: a contributor edits a mirrored file and
    updates local_sha256 to match, so every single-snapshot check passes while the recorded
    platform revision now dates bytes it never saw."""
    before = [{
        "id": "signal_github.repo_state",
        "mirror": {"model_id": "m", "revision": 4, "hash": "aaa",
                   "local_sha256": "OLD", "synced_at": "2026-08-15"},
    }]
    after = [{
        "id": "signal_github.repo_state",
        "mirror": {"model_id": "m", "revision": 4, "hash": "aaa",
                   "local_sha256": "NEW", "synced_at": "2026-08-15"},
    }]
    monkeypatch.setattr(A, "merge_base_assets", lambda base="origin/main": before)
    monkeypatch.setattr(A, "assets", lambda: after)
    violations = A.mirror_provenance_violations()
    # Assert the content, not a count: a stricter gate legitimately changes how many
    # messages one defect produces, and pinning the number makes the test fight the fix.
    assert any("revision" in v for v in violations), violations
    assert any("platform hash did not" in v for v in violations), violations


def test_merge_base_gate_catches_provenance_moving_without_bytes(monkeypatch):
    """The inverse: a revision bumped without the mirrored file changing, which claims a
    refetch that did not happen."""
    before = [{"id": "x.y", "mirror": {"revision": 4, "hash": "a", "local_sha256": "S", "synced_at": "d1"}}]
    after = [{"id": "x.y", "mirror": {"revision": 5, "hash": "a", "local_sha256": "S", "synced_at": "d1"}}]
    monkeypatch.setattr(A, "merge_base_assets", lambda base="origin/main": before)
    monkeypatch.setattr(A, "assets", lambda: after)
    assert A.mirror_provenance_violations() == [
        "x.y: provenance changed but the mirrored bytes did not"
    ]


# --- schedule evidence applies only where a schedule exists ---------------------

def test_schedule_evidence_only_on_scheduled_assets(inventory):
    """A null trigger on an unscheduled asset would read as "no run observed", which is a
    claim about a cron that is not there."""
    for asset in inventory:
        scheduled = str(asset.get("refresh", "")).startswith("dataset cron")
        for field in ("timezone", "last_observed_trigger", "last_run_at"):
            if scheduled:
                assert field in asset, f"{asset['id']}: scheduled but no {field}"
            else:
                assert field not in asset, f"{asset['id']}: unscheduled but carries {field}"


def test_the_openness_chain_is_gap_map(inventory):
    """population describes whose ROWS these are, not who reads them. The `scores` dataset
    holds two populations, so keying on the dataset put the openness chain in long_tail."""
    inv = A.by_table()
    for table in ("scores.openness_facts", "scores.openness_computed",
                  "evidence.product_evidence", "catalog.stack_map"):
        assert inv[table]["population"] == "gap_map", table


def test_release_path_is_consistent_across_the_openness_chain(inventory):
    """The chain is a parallel verification path feeding check_parity, retired in Phase 7 --
    not the release path. Marking one of its three tables release_path and not the others
    was arbitrary."""
    inv = A.by_table()
    chain = ("evidence.product_evidence", "scores.openness_facts", "scores.openness_computed")
    assert len({inv[t]["release_path"] for t in chain}) == 1
    assert all(inv[t]["release_path"] is False for t in chain)


# --- the ledger must list exactly the derived set ------------------------------

def test_no_reviewed_consumer_count_is_derived_not_authored():
    """`retirement_reason` is prose a generator wrote. Counting rows that carry it verifies
    nothing, because the same condition produced both. The count now recomputes the
    predicate independently, so the two can disagree and this can notice."""
    labelled = {a["id"] for a in A.assets() if a.get("retirement_reason")}
    derived = {a["id"] for a in A.no_reviewed_consumers()}
    assert labelled == derived, (
        f"authored label and derived predicate disagree: "
        f"label-only {sorted(labelled - derived)}, predicate-only {sorted(derived - labelled)}"
    )


def test_ledger_lists_exactly_the_assets_with_no_reviewed_consumer():
    """The ledger named `signal_packages.*` (3, staged) when only one of the three
    qualifies -- its two siblings have reviewed model consumers. A prose table that
    generalizes over a wildcard cannot be trusted, so it is compared to the derived set."""
    ledger = (ROOT / "docs/architecture/migration-status.md").read_text(encoding="utf-8")
    section = ledger.split("## Assets with no reviewed consumer")[1].split("\n## ")[0]
    listed = set(re.findall(r"^\| `([a-z_]+\.[a-z_0-9]+)`", section, re.M))
    derived = {a["id"] for a in A.no_reviewed_consumers()}
    assert listed == derived, (
        f"ledger drifted: listed-only {sorted(listed - derived)}, "
        f"derived-only {sorted(derived - listed)}"
    )


def test_deployed_staged_and_dormant_reconcile_to_the_inventory():
    """The three numbers the docs quote must add up, or the explanation of why the
    inventory is larger than the platform is itself wrong."""
    assets = A.assets()
    deployed = len(A.deployed_tables())
    staged = sum(1 for a in assets if a["status"] == "staged")
    dormant = sum(1 for a in assets if a["status"] == "dormant")
    assert deployed + staged + dormant == len(assets)


# --- mirror provenance: regression and identity --------------------------------

def _provenance(monkeypatch, before, after):
    monkeypatch.setattr(A, "merge_base_assets", lambda base="origin/main": before)
    monkeypatch.setattr(A, "assets", lambda: after)
    return A.mirror_provenance_violations()


def _mirror(**overrides):
    base = {"model_id": "m1", "revision": 4, "hash": "h1",
            "local_sha256": "S1", "synced_at": "2026-08-15"}
    return [{"id": "x.y", "mirror": {**base, **overrides}}]


def test_revision_may_not_regress_when_bytes_change(monkeypatch):
    """4 -> 3 passed the first gate, because it only required the value to differ."""
    violations = _provenance(monkeypatch, _mirror(),
                             _mirror(revision=3, hash="h2", local_sha256="S2", synced_at="2026-08-16"))
    assert any("revision went 4 -> 3" in v for v in violations)


def test_model_id_may_not_change_without_authorization(monkeypatch):
    """Repointing an entry at a different deployed model, bytes and provenance untouched."""
    violations = _provenance(monkeypatch, _mirror(), _mirror(model_id="m2"))
    assert any("model_id changed" in v for v in violations)


def test_model_id_change_is_allowed_with_a_migration_note(monkeypatch):
    before = _mirror()
    after = _mirror(model_id="m2")
    after[0]["mirror_migration"] = "redeployed under a new model on 2026-08-21, see #999"
    assert not [v for v in _provenance(monkeypatch, before, after) if "model_id" in v]


def test_synced_at_may_not_move_backward(monkeypatch):
    violations = _provenance(monkeypatch, _mirror(),
                             _mirror(revision=5, hash="h2", local_sha256="S2", synced_at="2026-08-01"))
    assert any("moved backward" in v for v in violations)


def test_a_same_day_refetch_is_legal(monkeypatch):
    """synced_at is date-granular, so requiring it to change would forbid two refetches in
    one day -- an impossible requirement, not a gate."""
    assert not _provenance(monkeypatch, _mirror(),
                           _mirror(revision=5, hash="h2", local_sha256="S2"))


# --- the platform-model audit is reproducible from a committed receipt -------------
# platform_models: checked is not 57 authored booleans; it is backed by
# warehouse/audits/platform_models.json, the credential-free receipt of the Phase 0b audit.
# Regenerate with `uv run python -m build.audit_platform_models` (needs OSO_API_KEY).

from build import audit_platform_models as AU  # noqa: E402


def test_platform_audit_receipt_is_wellformed_and_complete():
    """The full receipt contract, via the module's own validator (a real calendar date,
    unique model_id/table, every field typed, valid hashes and language, deterministic order).
    Plus two repository-side facts: no source body is committed, and every in-scope read
    resolves to an inventory asset."""
    r = AU.load_receipt()
    assert AU.validate_receipt(r) == [], AU.validate_receipt(r)
    ids = set(A.by_table())
    for m in r["models"]:
        assert "code" not in m, f"{m['table']}: receipt must not carry the source body"
        for ref in m["in_scope_reads"]:
            assert ref.removeprefix("currentai.") in ids, f"{m['table']} reads unlisted {ref}"


def _valid_receipt() -> dict:
    return {
        "audited_at": "2026-08-22", "org": AU.ORG, "org_id": AU.ORG_ID, "model_count": 2,
        "models": [
            {"table": "currentai.a.one", "dataset": "a", "name": "one",
             "model_id": "693dba9c-44d0-4a12-8e4d-0358023ceb9c",
             "revision_hash": "a" * 64, "source_sha256": "b" * 64, "language": "SQL",
             "internal_reads": ["currentai.a.two"], "in_scope_reads": [],
             "has_repository_source": True},
            {"table": "currentai.a.two", "dataset": "a", "name": "two",
             "model_id": "693dba9c-44d0-4a12-8e4d-0358023ceb9d",
             "revision_hash": "c" * 64, "source_sha256": "d" * 64, "language": "python",
             "internal_reads": [], "in_scope_reads": [], "has_repository_source": False},
        ],
    }


def test_receipt_validator_rejects_malformed_receipts():
    """Every contract violation must fail the validator, so a bad receipt cannot pass by
    resembling a good one. Same "grade on what you report" discipline the mirror gates carry."""
    assert AU.validate_receipt(_valid_receipt()) == []

    def broken(mutate):
        r = _valid_receipt()
        mutate(r)
        return AU.validate_receipt(r)

    def set_dup_table(r):
        r["models"][1]["table"] = "currentai.a.one"; r["models"][1]["name"] = "one"

    def set_bad_dataset(r):
        # a non-string dataset must fail on its own, even when the table string happens to
        # match its interpolation (`currentai.1.example`)
        r["models"][0]["dataset"] = 1
        r["models"][0]["table"] = "currentai.1.example"
        r["models"][0]["name"] = "example"

    cases = {
        "calendar date": lambda r: r.__setitem__("audited_at", "2026-99-99"),
        "missing top-level field org": lambda r: r.pop("org"),
        "org is": lambda r: r.__setitem__("org", "someone-else"),
        "missing top-level field org_id": lambda r: r.pop("org_id"),
        "org_id is": lambda r: r.__setitem__("org_id", "00000000-0000-0000-0000-000000000000"),
        "every model entry must be a mapping": lambda r: r["models"].__setitem__(1, "not-a-dict"),
        "dataset is not a nonempty string": set_bad_dataset,
        "name is not a nonempty string": lambda r: r["models"][0].__setitem__("name", 2),
        "duplicate table": set_dup_table,
        "duplicate model_id": lambda r: r["models"][1].__setitem__("model_id", r["models"][0]["model_id"]),
        "revision_hash": lambda r: r["models"][0].__setitem__("revision_hash", "abc"),
        "language": lambda r: r["models"][0].__setitem__("language", "scala"),
        "has_repository_source": lambda r: r["models"][0].pop("has_repository_source"),
        "model_count": lambda r: r.__setitem__("model_count", 5),
        "deterministic": lambda r: r.__setitem__("models", list(reversed(r["models"]))),
        "subset": lambda r: r["models"][0].__setitem__("in_scope_reads", ["currentai.z.z"]),
    }
    for needle, mutate in cases.items():
        problems = broken(mutate)
        assert any(needle in p for p in problems), f"{needle}: not caught, got {problems}"


def test_platform_model_consumers_match_the_receipt(inventory):
    """The inventory's platform_model_consumers must be exactly what the receipt derives --
    so a hand-edit of that field (or of platform_models) without re-running the audit fails,
    the same binding read_by has to the tree."""
    derived = AU.consumers_from_receipt(AU.load_receipt())
    authored = {a["id"]: sorted(a["platform_model_consumers"])
                for a in inventory if a.get("platform_model_consumers")}
    assert {k: sorted(v) for k, v in derived.items()} == authored


def test_platform_models_checked_is_backed_by_the_census(inventory):
    """platform_models is `checked` org-wide, so the audit had to cover every deployed model.
    Every mirrored asset is a deployed UDM and must therefore appear in the receipt census;
    and no asset may claim `checked` without the receipt existing to back it."""
    r = AU.load_receipt()
    census = {m["table"] for m in r["models"]}
    for asset in inventory:
        if asset.get("mirror"):
            assert asset["table"] in census, (
                f"{asset['id']} is a platform mirror but is absent from the audit census"
            )
    checked = [a for a in inventory if a["consumer_checks"]["platform_models"] == "checked"]
    assert checked, "no asset is checked, yet a receipt exists"
    assert r["audited_at"], "platform_models is checked but the receipt records no audit date"
