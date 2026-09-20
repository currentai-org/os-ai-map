"""Negative tests for the ADR-003 scope-boundary gates and the dependency manifest.

The positive checks (the real inventory passes) live in test_assets_inventory.py. Here each
gate is shown to FAIL on a constructed violation -- a gate that cannot fail catches nothing,
the recurring "check establishes less than it reports" defect this data system keeps closing.
The real assets()/dependencies()/derivation helpers are monkeypatched with synthetic inputs so
a single violation can be isolated without touching the committed files.
"""

from __future__ import annotations

import copy

import pytest

import build.assets as A


def _governed(**over):
    """A minimal governed-output asset (release_path, role governed-output, authority repo)."""
    base = dict(
        id="registry.x", table="currentai.registry.x", population="gap_map",
        release_path=True, role="governed-output", status="active", authority="repo",
    )
    base.update(over)
    return base


# --- role gate: gate 1 and the per-role invariants -------------------------------

ROLE_VIOLATIONS = [
    ("governed_output_without_release_path", dict(release_path=False), "gate 1"),
    ("release_path_without_governed_output",
     dict(role="repo-computation", files={"model": "warehouse/models/registry/x.sql"}), "gate 1"),
    ("repo_computation_with_platform_authority",
     dict(id="scores.openness_facts", table="currentai.scores.openness_facts", release_path=False,
          role="repo-computation", authority="platform",
          files={"model": "warehouse/models/scores/openness_facts.sql"}, mirror={"revision": 7}),
     "authority is 'platform'"),
    ("governed_data_with_model_file",
     dict(id="observations.baseline", table="currentai.observations.baseline", release_path=False,
          role="governed-data", authority="repo",
          files={"model": "warehouse/models/observations/baseline.sql"}), "has a model file"),
    ("compatibility_shim_without_replacement",
     dict(id="signal_github.repo_state", table="currentai.signal_github.repo_state", release_path=False,
          role="compatibility-shim", status="compatibility", authority="platform"), "replacement"),
    ("roleless_asset", dict(role=None), "is not one of"),
    ("unknown_role_value", dict(role="banana"), "not one of"),
]


@pytest.mark.parametrize("label,override,expected", ROLE_VIOLATIONS,
                         ids=[m[0] for m in ROLE_VIOLATIONS])
def test_role_violation_is_flagged(monkeypatch, label, override, expected):
    monkeypatch.setattr(A, "assets", lambda: [_governed(**override)])
    assert any(expected in v for v in A.role_violations()), label


def test_gap_map_is_the_only_population():
    # The vocabulary is single-valued, so no `long_tail`/`both` asset can be introduced.
    assert A.POPULATIONS == {"gap_map"}


# --- kind gate: kind is derived from placement, not decorative --------------------

KIND_VIOLATIONS = [
    ("registry_claiming_evaluation",
     dict(table="currentai.registry.products", kind="evaluation"), "derives 'registry'"),
    ("evaluation_claiming_registry",
     dict(table="currentai.evaluation.axis_facts", kind="registry"), "derives 'evaluation'"),
    ("signal_collector_claiming_evaluation",
     dict(table="currentai.signal_github.repo_state", kind="evaluation"), "derives 'observations'"),
    ("signal_adoption_claiming_observations",
     dict(table="currentai.signal_github.product_adoption", kind="observations"), "derives 'evaluation'"),
    ("unknown_kind_value", dict(table="currentai.registry.products", kind="banana"), "not in"),
]


@pytest.mark.parametrize("label,override,expected", KIND_VIOLATIONS,
                         ids=[m[0] for m in KIND_VIOLATIONS])
def test_kind_violation_is_flagged(monkeypatch, label, override, expected):
    monkeypatch.setattr(A, "assets", lambda: [_governed(**override)])
    assert any(expected in v for v in A.kind_violations()), label


# --- dependency gate: gates 2, 3, 4, and contract integrity ----------------------

def _oso_dep(**over):
    base = dict(
        table="oso.x.y", purpose="p", expected_grain="one row per z",
        expected_columns=[{"name": "z", "type": "varchar", "nullable": False}],
        freshness_requirement="<= 8 days",
        required_by=["warehouse/models/signal_pypi/package_downloads.sql"],
        verified_at="2026-08-29", owner="oso",
    )
    base.update(over)
    base.setdefault("content_contract_sha256", A.contract_fingerprint(base))
    return base


def test_dependency_also_in_assets_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(table="oso.x.y", authority="repo")])
    monkeypatch.setattr(A, "dependencies", lambda: [_oso_dep()])
    monkeypatch.setattr(A, "needed_tables", lambda: {"oso.x.y"})
    monkeypatch.setattr(A, "dependency_readers",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("gate 3" in v for v in A.dependency_violations())


def test_unlisted_currentai_input_is_flagged(monkeypatch):
    # A governed computation reading a non-governed currentai.* table needs a contract.
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [])
    monkeypatch.setattr(A, "needed_tables", lambda: {"currentai.signal_foo.bar"})
    monkeypatch.setattr(A, "dependency_readers",
                        lambda: {"currentai.signal_foo.bar": ["warehouse/models/observations/x.sql"]})
    assert any("gate 2" in v and "currentai.signal_foo.bar" in v for v in A.dependency_violations())


def test_unlisted_oso_input_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [])
    monkeypatch.setattr(A, "needed_tables", lambda: {"oso.unlisted.tbl"})
    monkeypatch.setattr(A, "dependency_readers", lambda: {"oso.unlisted.tbl": ["build/x.py"]})
    assert any("gate 2" in v for v in A.dependency_violations())


def test_dependency_required_by_disagreeing_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [_oso_dep(required_by=["warehouse/models/wrong.sql"])])
    monkeypatch.setattr(A, "needed_tables", lambda: {"oso.x.y"})
    monkeypatch.setattr(A, "dependency_readers",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("gate 4" in v and "disagrees" in v for v in A.dependency_violations())


def test_dependency_not_reachable_is_flagged(monkeypatch):
    # A contract nothing governed reaches (needed_tables empty) -> gate 4.
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [_oso_dep()])
    monkeypatch.setattr(A, "needed_tables", lambda: set())
    monkeypatch.setattr(A, "dependency_readers", lambda: {"oso.x.y": ["build/x.py"]})
    assert any("not reachable" in v for v in A.dependency_violations())


def test_forged_content_contract_hash_is_flagged(monkeypatch):
    # An arbitrary 64-hex string must not pass -- the gate recomputes the fingerprint.
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [_oso_dep(content_contract_sha256="a" * 64)])
    monkeypatch.setattr(A, "needed_tables", lambda: {"oso.x.y"})
    monkeypatch.setattr(A, "dependency_readers",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("does not match the recomputed fingerprint" in v for v in A.dependency_violations())


def test_untyped_expected_columns_are_flagged(monkeypatch):
    dep = _oso_dep(expected_columns=["z"])  # bare name, no type
    dep["content_contract_sha256"] = A.contract_fingerprint(dep)
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [dep])
    monkeypatch.setattr(A, "needed_tables", lambda: {"oso.x.y"})
    monkeypatch.setattr(A, "dependency_readers",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("name and a type" in v for v in A.dependency_violations())


def test_dependency_with_both_provenance_anchors_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [_oso_dep(verified_revision=7)])
    monkeypatch.setattr(A, "needed_tables", lambda: {"oso.x.y"})
    monkeypatch.setattr(A, "dependency_readers",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("exactly one provenance anchor" in v for v in A.dependency_violations())


def test_dependency_owner_not_oso_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [_oso_dep(owner="carl")])
    monkeypatch.setattr(A, "needed_tables", lambda: {"oso.x.y"})
    monkeypatch.setattr(A, "dependency_readers",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("owner must be oso" in v for v in A.dependency_violations())


# --- gate 5: notebook root -------------------------------------------------------

def test_notebook_producer_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        role="repo-computation", release_path=False, authority="repo",
        producer="notebooks/long-tail-explorer.py",
        files={"model": "notebooks/long-tail-explorer.py"})])
    assert any("gate 5" in v for v in A.notebook_root_violations())


# --- fail-closed: currentai mirror integrity + required fields ------------------

import hashlib
from pathlib import Path

# Any real mirror file on disk will do -- the gate hashes its bytes. Repointed off the
# signal_pypi mirror on 2026-09-14, when that model was dropped and its file deleted.
_REAL_MODEL = "warehouse/models/signal_packages/downloads.sql"


def _currentai_dep(**over):
    h = hashlib.sha256((A.ROOT / _REAL_MODEL).read_bytes()).hexdigest()
    base = dict(
        table="currentai.signal_packages.downloads", purpose="p", expected_grain="g",
        freshness_requirement="<= 8 days", required_by=["build/x.py"], verified_revision=3,
        owner="oso", files={"model": _REAL_MODEL},
        mirror={"model_id": "m", "revision": 3, "hash": "hh",
                "local_sha256": h, "synced_at": "2026-08-15"},
    )
    base.update(over)
    return base


def test_verified_revision_must_equal_mirror_revision():
    dep = _currentai_dep(verified_revision=999999)  # mirror.revision stays 3
    assert any("verified_revision" in v and "mirror.revision" in v for v in A._mirror_integrity(dep))


def test_mirror_bytes_edited_without_hash_is_flagged():
    dep = _currentai_dep()
    dep["mirror"]["local_sha256"] = "0" * 64  # claims bytes that are not on disk
    assert any("local_sha256 does not match" in v for v in A._mirror_integrity(dep))


def test_claimed_schema_file_must_be_hashed():
    dep = _currentai_dep()
    dep["files"]["schema"] = "warehouse/models/evidence/product_evidence.schema.json"
    # no schema_sha256 recorded -> flagged
    assert any("schema_sha256" in v for v in A._mirror_integrity(dep))


def test_missing_freshness_requirement_is_flagged(monkeypatch):
    dep = _oso_dep()
    del dep["freshness_requirement"]
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [dep])
    monkeypatch.setattr(A, "needed_tables", lambda: {"oso.x.y"})
    monkeypatch.setattr(A, "dependency_readers",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("missing freshness_requirement" in v for v in A.dependency_violations())


# --- cross-commit provenance for dependency mirrors -----------------------------
#
# Prior provenance is the same mirror in the merge-base dependencies.yaml. Each negative pins one
# rule: bytes and provenance move together and forward, and model_id is stable without a migration.

def _prior_dep(**over):
    m = {"model_id": "m", "revision": 3, "hash": "hh", "local_sha256": "aaa", "synced_at": "2026-08-15"}
    m.update(over)
    return {"table": "currentai.signal_pypi.package_downloads", "mirror": m}


def _cur_dep(**over):
    m = {"model_id": "m", "revision": 3, "hash": "hh", "local_sha256": "aaa", "synced_at": "2026-08-15"}
    m.update(over.pop("mirror", {}))
    d = {"table": "currentai.signal_pypi.package_downloads", "mirror": m}
    d.update(over)
    return d


def test_dependency_bytes_changed_without_revision_advance_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [_prior_dep()])
    monkeypatch.setattr(A, "dependencies",
                        lambda: [_cur_dep(mirror={"local_sha256": "bbb", "hash": "new"})])  # bytes moved, rev still 3
    assert any("revision" in v for v in A.dependency_mirror_provenance_violations())


def test_dependency_provenance_changed_without_bytes_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [_prior_dep()])
    monkeypatch.setattr(A, "dependencies",
                        lambda: [_cur_dep(mirror={"revision": 99})])  # same bytes, revision moved
    assert any("bytes did not" in v for v in A.dependency_mirror_provenance_violations())


def test_dependency_model_id_change_without_migration_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [_prior_dep()])
    monkeypatch.setattr(A, "dependencies", lambda: [_cur_dep(mirror={"model_id": "other"})])
    assert any("model_id changed" in v for v in A.dependency_mirror_provenance_violations())


# --- the SCHEMA file is part of the cross-commit byte identity ------------------
#
# A schema-only edit is a byte change and must advance the revision like a model edit.

_SCHEMA = "warehouse/models/evidence/product_evidence.schema.json"


def _prior_dep_schema(schema="sold", **m_over):
    m = {"model_id": "m", "revision": 3, "hash": "hh", "local_sha256": "model",
         "schema_sha256": schema, "synced_at": "2026-08-15"}
    m.update(m_over)
    return {"table": "currentai.signal_pypi.package_downloads", "mirror": m}


def _cur_dep_schema(schema="scur", **m_over):
    m = {"model_id": "m", "revision": 3, "hash": "hh", "local_sha256": "model",
         "schema_sha256": schema, "synced_at": "2026-08-15"}
    m.update(m_over)
    return {"table": "currentai.signal_pypi.package_downloads",
            "files": {"model": _REAL_MODEL, "schema": _SCHEMA}, "mirror": m}


def test_schema_changed_without_revision_advance_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [_prior_dep_schema("sold")])
    monkeypatch.setattr(A, "dependencies", lambda: [_cur_dep_schema("snew")])  # schema moved, rev still 3
    assert any("revision" in v for v in A.dependency_mirror_provenance_violations())


def test_schema_changed_with_revision_advance_is_accepted(monkeypatch):
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [_prior_dep_schema("sold")])
    monkeypatch.setattr(A, "dependencies",
                        lambda: [_cur_dep_schema("snew", revision=4, hash="new")])
    assert A.dependency_mirror_provenance_violations() == []


# --- the governed root set is closed ---------------------------------------------

def test_unrelated_build_helper_is_not_a_root():
    """A build module that neither produces a governed table nor is a named audit root is not a
    governed root, so a table reference in it cannot confer dependency membership."""
    roots = A._governed_root_files()
    assert "build/render.py" not in roots and "build/vocabulary.py" not in roots
    assert roots <= (set(A._governed_producer_paths()) | set(A.AUDIT_ROOTS) | set(A.PUBLICATION_WORKFLOWS))


# --- the dependency loader and manifest are well-formed -------------------------

def test_dependencies_loader_returns_contracts():
    deps = A.dependencies()
    assert isinstance(deps, list) and deps, "dependencies.yaml should carry contracts"
    for d in deps:
        assert d["owner"] == "oso"
        assert d.get("table", "").startswith(("oso.", "currentai.")), d
        assert d.get("required_by"), d


# --- externalization receipt reproduces from its base commit ---------------------
#
# The receipt reproduces against real git state (the base commit's inventory and blobs,
# platform_models.json), so each negative test deep-copies the committed receipt, mutates one
# field, patches externalization_receipt() to serve it, and asserts the matching violation. The
# helpers that read the base commit / platform audit stay real -- that is the reproduction.

def _real_receipt():
    r = A.externalization_receipt()
    assert r and r.get("assets"), "committed externalization receipt should be present and non-empty"
    return copy.deepcopy(r)


def _serve(monkeypatch, receipt):
    monkeypatch.setattr(A, "externalization_receipt", lambda: receipt)


def test_receipt_as_committed_reproduces_clean():
    # The real, committed receipt must reproduce with zero violations -- the positive anchor.
    assert A.externalization_receipt_violations() == []


def _wrong_ancestor(r):
    real = r["externalization_base_commit"]
    r["externalization_base_commit"] = A._parent_sha(A._parent_sha(real))


def _extra_entry(r):
    bogus = copy.deepcopy(r["assets"][0])
    bogus["id"], bogus["table"] = "registry.still_governed", "currentai.registry.products"
    r["assets"].append(bogus)
    r["count"] = len(r["assets"])


def _duplicate(r):
    r["assets"].append(copy.deepcopy(r["assets"][0]))
    r["count"] = len(r["assets"])


def _drop_asset(r):
    r["assets"] = r["assets"][:-1]
    r["count"] = len(r["assets"])


def _flip_population(r):
    e = r["assets"][0]
    e["population_was"] = "long_tail" if e["population_was"] == "gap_map" else "gap_map"


def _altered_hash(r):
    for e in r["assets"]:
        if e.get("archived_source_sha256"):
            k = next(iter(e["archived_source_sha256"]))
            e["archived_source_sha256"][k] = "0" * 64
            return


def _drop_sources_archive(r):
    for e in r["assets"]:
        arch = e.get("archived_source_sha256") or {}
        if any(pth.startswith("sources/") for pth in arch):
            e["archived_source_sha256"] = {pth: h for pth, h in arch.items()
                                           if not pth.startswith("sources/")}
            return


def _fabricate_platform(r):
    audited = A._platform_models_at_commit(r["externalization_base_commit"])
    for e in r["assets"]:
        if e["table"] not in audited:
            e.setdefault("platform", {})["model_id"] = "fabricated"
            return


def _wrong_provenance(r):
    audited = A._platform_models_at_commit(r["externalization_base_commit"])
    for e in r["assets"]:
        if e["table"] in audited:
            e["platform"]["revision_hash"] = "0" * 64
            return


def _break_repo_consumers(r):
    for e in r["assets"]:
        car = e.get("consumers_at_removal") or {}
        if car.get("repo_read_by"):
            e["consumer_resolution"] = "everything resolves fine, trust me"  # prose can't save it
            car["repo_read_by"] = {"models": ["warehouse/models/made/up.sql"]}
            return


def _omit_platform_consumer(r):
    for e in r["assets"]:
        if e["table"].endswith(".entities.repos"):  # read by surviving audited state_of_os_ai models
            e["consumers_at_removal"]["platform_models"] = []
            return


# One mutation of a deep copy of the committed receipt per row; the base-commit inventory, file
# blobs, and base-committed platform audit stay real -- that reproduction is what the gate proves.
# (Mutations that alter an existing entry also trip the independent append-only check; asserting the
# specific substring keeps each case pinned to the invariant it exercises.)
RECEIPT_MUTATIONS = [
    ("base_does_not_resolve", lambda r: r.__setitem__("externalization_base_commit", "0" * 40),
     "does not resolve"),
    ("valid_but_wrong_ancestor_base", _wrong_ancestor, "is not the externalization boundary"),
    ("wrong_count", lambda r: r.__setitem__("count", r["count"] + 1), "count"),
    ("wrong_schema_version", lambda r: r.__setitem__("schema_version", 1), "schema_version"),
    ("dropped_removed_asset", _drop_asset, "but not in the externalization receipt"),
    ("extra_membership_entry", _extra_entry, "not an asset removed from the base inventory"),
    ("duplicate_entry", _duplicate, "duplicate entry"),
    ("wrong_population_was", _flip_population, "population_was"),
    ("altered_archived_hash", _altered_hash, "!= base blob"),
    ("unarchived_deleted_file", _drop_sources_archive, "deleted since the base commit but not archived"),
    ("fabricated_platform_facts", _fabricate_platform, "no audited model exists to source it"),
    ("wrong_deployed_provenance", _wrong_provenance, "platform.revision_hash"),
    ("altered_repo_consumers", _break_repo_consumers, "repo_read_by != base read_by"),
    ("omitted_surviving_platform_consumer", _omit_platform_consumer,
     "absent from consumers_at_removal.platform_models"),
    ("dishonest_verification_date",
     lambda r: r["assets"][0].__setitem__("last_platform_verified_at", "2026-08-30"),
     "last_platform_verified_at"),
    ("missing_evidence_basis", lambda r: r["assets"][0].pop("evidence_basis", None),
     "missing evidence_basis"),
    ("transferred_without_destination", lambda r: r["assets"][0].__setitem__("disposition", "transferred"),
     "must name destination.repository + commit"),
]


@pytest.mark.parametrize("label,mutate,expected", RECEIPT_MUTATIONS,
                         ids=[m[0] for m in RECEIPT_MUTATIONS])
def test_externalization_receipt_mutation_is_flagged(monkeypatch, label, mutate, expected):
    r = _real_receipt()
    mutate(r)
    _serve(monkeypatch, r)
    assert any(expected in v for v in A.externalization_receipt_violations()), \
        f"{label}: expected a violation containing {expected!r}"


def test_base_boundary_derivation_matches_recorded():
    # The graph-derived boundary equals what the committed receipt names, independent of its own base
    # field -- the positive anchor for the base binding.
    tables = {e["table"] for e in A.externalized()}
    derived = A.expected_externalization_base(tables)
    assert derived is not None
    assert derived == A._rev_parse(A.externalization_receipt()["externalization_base_commit"])


def test_platform_facts_reproduce_against_base_audit_not_current(monkeypatch):
    # Facts reproduce against the audit committed AT THE BASE, so poisoning the current audit must
    # not move the verdict.
    monkeypatch.setattr(A, "_platform_models",
                        lambda: {"currentai.entities.repos": {"table": "currentai.entities.repos",
                                                              "model_id": "poisoned", "revision_hash": "x",
                                                              "source_sha256": "y", "internal_reads": []}})
    assert A.externalization_receipt_violations() == []


def test_missing_base_audit_is_flagged(monkeypatch):
    # If the base-committed audit is unreadable, deployed-model facts cannot reproduce -> flagged.
    monkeypatch.setattr(A, "_platform_models_at_commit", lambda sha: {})
    assert any("no audited model exists to source it" in v
               for v in A.externalization_receipt_violations())


def test_dropped_consumer_resolution_alone_does_not_break(monkeypatch):
    # consumer_resolution is optional prose; removing it adds no violation. Isolated from append-only
    # (which independently forbids modifying a merged entry) to prove the gate never leans on prose.
    monkeypatch.setattr(A, "_merge_base_receipt", lambda base="origin/main": None)
    r = _real_receipt()
    for e in r["assets"]:
        e.pop("consumer_resolution", None)
    _serve(monkeypatch, r)
    assert A.externalization_receipt_violations() == []


def test_removing_a_previously_recorded_entry_is_flagged(monkeypatch):
    # Append-only: an entry present at the merge base must survive unchanged.
    r = _real_receipt()
    prior = {e["id"]: copy.deepcopy(e) for e in r["assets"]}
    prior["registry.long_gone"] = {"id": "registry.long_gone", "table": "currentai.registry.long_gone"}
    monkeypatch.setattr(A, "_merge_base_receipt", lambda base="origin/main": prior)
    _serve(monkeypatch, r)
    assert any("registry.long_gone" in v and "append-only" in v
               for v in A.externalization_receipt_violations())


def test_modifying_a_previously_recorded_entry_is_flagged(monkeypatch):
    r = _real_receipt()
    prior = {e["id"]: copy.deepcopy(e) for e in r["assets"]}
    first = r["assets"][0]["id"]
    prior[first] = copy.deepcopy(prior[first])
    prior[first]["owner"] = "someone else entirely"  # differs from the current entry
    monkeypatch.setattr(A, "_merge_base_receipt", lambda base="origin/main": prior)
    _serve(monkeypatch, r)
    assert any(first in v and "modified" in v for v in A.externalization_receipt_violations())


# --- reclaimed-as-dependency: externalized -> back inside the dependency graph ----
#
# The receipt's history is append-only, so a table that comes back does NOT lose its
# externalization entry: a `reclaims` record is appended and the historical removed set stays the
# size it was. These tests build that transition on temp fixtures over the real committed receipt
# -- the same simulation PR #480 makes real for `signal_goodailist.repo_catalog`.

RECLAIM_TABLE = "currentai.signal_goodailist.repo_catalog"
RECLAIM_MIRROR = "warehouse/models/signal_goodailist/repo_catalog.py"


def _standin_reader():
    """A real tracked model file, used as the fixture's governed reader.

    The reclaim gate insists the reader EXISTS in the tree, so the fixture cannot invent a path;
    what it may stand in for is the read itself, which derive_graph() supplies below.
    """
    for a in A.assets():
        mf = (a.get("files") or {}).get("model")
        if mf and mf.endswith(".sql") and (A.ROOT / mf).exists():
            return mf
    raise AssertionError("no tracked .sql model file to stand in as a governed reader")


def _reclaim_record(r, **over):
    """An appended reclaim record for RECLAIM_TABLE, with the counts the receipt must state."""
    prior = next(e for e in r["assets"] if e["table"] == RECLAIM_TABLE)
    rec = dict(
        table=RECLAIM_TABLE,
        prior_disposition=prior["disposition"],
        prior_date=prior["recorded_at"],
        new_disposition="reclaimed-as-dependency",
        date="2026-09-04",
        reason="read by the identity graph's artifact_nodes model",
        governed_reader=_standin_reader(),
    )
    rec.update(over)
    r["reclaims"] = [rec]
    r["reclaimed_count"] = 1
    r["still_external_count"] = r["count"] - 1
    return rec


def _contract(mirror=True):
    return {
        "table": RECLAIM_TABLE,
        "owner": "oso",
        "purpose": "identity_graph",
        "expected_grain": "one row per repo",
        "freshness_requirement": "<= 30 days",
        "verified_revision": 4,
        "mirror": {"revision": 4, "model_id": "c7d3a3d9-578c-4c54-8ccf-71879bdd43d2"} if mirror else {},
        "files": {"model": RECLAIM_MIRROR},
    }


def _serve_contract(monkeypatch, contract):
    """Stand in the fixture's contract for RECLAIM_TABLE's real one.

    The committed `dependencies.yaml` now carries a contract for RECLAIM_TABLE (the reclaim is
    real), so the fixture has to REPLACE it rather than append beside it -- otherwise `None`
    would not mean "no contract" and the no-contract cases could never fire.
    """
    real = [d for d in A.dependencies() if d.get("table") != RECLAIM_TABLE]
    monkeypatch.setattr(A, "dependencies", lambda: real + ([contract] if contract else []))


def _receipt_without_the_reclaim():
    """The committed receipt as it read before RECLAIM_TABLE was reclaimed."""
    r = _real_receipt()
    r["reclaims"] = []
    r["reclaimed_count"] = 0
    r["still_external_count"] = r["count"]
    return r


def _serve_read(monkeypatch, reader, table=RECLAIM_TABLE):
    real = A.derive_graph()
    graph = {"reads": dict(real["reads"]), "read_by": real["read_by"]}
    refs = dict(graph["reads"].get(reader) or {"internal": [], "external": []})
    if table:
        refs["internal"] = sorted(set(refs["internal"]) | {table.removeprefix("currentai.")})
    graph["reads"][reader] = refs
    monkeypatch.setattr(A, "derive_graph", lambda: graph)


def test_valid_reclaim_passes(monkeypatch):
    r = _real_receipt()
    rec = _reclaim_record(r)
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    _serve_read(monkeypatch, rec["governed_reader"])
    assert A.reclaim_violations() == []
    assert A.externalization_receipt_violations() == []


def test_reclaim_without_a_prior_externalization_record_is_flagged(monkeypatch):
    r = _real_receipt()
    rec = _reclaim_record(r, table="currentai.registry.never_externalized")
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, dict(_contract(), table=rec["table"]))
    _serve_read(monkeypatch, rec["governed_reader"], table=rec["table"])
    assert any("records no prior externalization entry" in v for v in A.reclaim_violations())


def test_reclaim_with_the_wrong_prior_date_is_flagged(monkeypatch):
    r = _real_receipt()
    rec = _reclaim_record(r, prior_date="2020-01-01")
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    _serve_read(monkeypatch, rec["governed_reader"])
    assert any("prior_date" in v for v in A.reclaim_violations())


def test_reclaim_whose_reader_does_not_read_the_table_is_flagged(monkeypatch):
    r = _real_receipt()
    rec = _reclaim_record(r)
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    _serve_read(monkeypatch, rec["governed_reader"], table=None)  # the file reads, but not this
    assert any("does not read" in v for v in A.reclaim_violations())


def test_reclaim_whose_reader_is_not_in_the_tree_is_flagged(monkeypatch):
    r = _real_receipt()
    _reclaim_record(r, governed_reader="warehouse/models/identity/not_here_yet.sql")
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    assert any("does not exist in this tree" in v for v in A.reclaim_violations())


def test_reclaim_without_a_dependency_contract_is_flagged(monkeypatch):
    r = _real_receipt()
    rec = _reclaim_record(r)
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, None)
    _serve_read(monkeypatch, rec["governed_reader"])
    assert any("has no contract for it" in v for v in A.reclaim_violations())


def test_reclaimed_contract_without_a_mirror_block_is_flagged(monkeypatch):
    r = _real_receipt()
    rec = _reclaim_record(r)
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract(mirror=False))
    _serve_read(monkeypatch, rec["governed_reader"])
    assert any("has no mirror block" in v for v in A.reclaim_violations())


def test_contract_for_an_externalized_table_without_a_reclaim_is_flagged(monkeypatch):
    r = _receipt_without_the_reclaim()
    _serve(monkeypatch, r)  # no reclaims entry at all
    _serve_contract(monkeypatch, _contract())
    assert any("with no reclaim record" in v for v in A.reclaim_violations())
    assert any("also a dependency contract" in v for v in A.externalization_receipt_violations())


def test_reclaim_counts_must_be_stated(monkeypatch):
    r = _real_receipt()
    rec = _reclaim_record(r)
    r["still_external_count"] = r["count"]  # the shrink is not written down
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    _serve_read(monkeypatch, rec["governed_reader"])
    assert any("still_external_count" in v for v in A.reclaim_violations())


def test_reclaim_leaves_the_original_externalization_entry_unchanged(monkeypatch):
    committed = copy.deepcopy(
        next(e for e in A.externalized() if e["table"] == RECLAIM_TABLE))
    r = _real_receipt()
    rec = _reclaim_record(r)
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    _serve_read(monkeypatch, rec["governed_reader"])
    entry = next(e for e in A.externalized() if e["table"] == RECLAIM_TABLE)
    assert entry == committed, "a reclaim must not edit the externalization record it transitions from"
    assert entry["disposition"] == "frozen-without-producer"
    assert not [v for v in A.externalization_receipt_violations()
                if "append-only" in v or "modified" in v or "removed" in v]


def test_removed_set_is_historical_minus_reclaimed(monkeypatch):
    r = _real_receipt()
    historical = r["count"]
    rec = _reclaim_record(r)
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    _serve_read(monkeypatch, rec["governed_reader"])

    # the historical removed set never shrinks, and still names the reclaimed table
    assert len(A.externalized()) == historical
    assert RECLAIM_TABLE in {e["table"] for e in A.externalized()}
    # the currently-out population shrinks by exactly the reclaimed tables
    still = A.still_externalized()
    assert len(still) == historical - 1
    assert RECLAIM_TABLE not in {e["table"] for e in still}
    assert A.reclaimed_tables() == {RECLAIM_TABLE}
    # and the reproduction gate still counts it as removed from the base inventory
    assert not [v for v in A.externalization_receipt_violations() if RECLAIM_TABLE in v]


def test_reclaimed_mirror_file_may_exist_again(monkeypatch):
    """The archived file is deleted-at-externalization evidence, not a permanent ban.

    A reclaimed table gets its read-only mirror back at the same path (PR #480 restores exactly
    RECLAIM_MIRROR), so the "still exists in the worktree" check is answered by the reclaim -- the
    archived hash still has to reproduce from the base blob either way. The worktree lookup is
    stood in for rather than writing into the real tree, which would race the other workers.
    """
    real_has = A._worktree_has
    monkeypatch.setattr(A, "_worktree_has", lambda p: p == RECLAIM_MIRROR or real_has(p))

    pristine = _receipt_without_the_reclaim()
    r = copy.deepcopy(pristine)
    rec = _reclaim_record(r)
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    _serve_read(monkeypatch, rec["governed_reader"])
    assert not [v for v in A.externalization_receipt_violations() if "still exists" in v]

    # without the reclaim, the same restored file is a violation
    _serve(monkeypatch, pristine)
    _serve_contract(monkeypatch, None)
    assert any("still exists in the worktree" in v
               for v in A.externalization_receipt_violations())


# --- the reclaim carve-outs are scoped, and a transferred table is not reclaimable ---

def test_reclaim_from_a_transferred_disposition_is_flagged(monkeypatch):
    """Only a frozen table is reclaimable.

    A `transferred` table is owned by its named destination repo, so a contract for it would have
    to declare `owner: oso` falsely. The gate fails closed until that gets a ruling.
    """
    r = _real_receipt()
    prior = next(e for e in r["assets"] if e["table"] == RECLAIM_TABLE)
    prior["disposition"] = "transferred"
    prior["destination"] = {"repository": "someone-else/repo", "commit": "0" * 40}
    rec = _reclaim_record(r, prior_disposition="transferred")
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    _serve_read(monkeypatch, rec["governed_reader"])
    assert any("cannot reclaim from disposition 'transferred'" in v and "needs a ruling" in v
               for v in A.reclaim_violations())


def test_reclaim_does_not_re_admit_an_archived_file_the_contract_does_not_claim(monkeypatch):
    """M1: the archived-file carve-out is the contract's mirror paths, not the whole entry.

    An entry that archived a fetcher as well as its model must not, once reclaimed, let the fetcher
    reappear: only the contract's declared files are content-bound by the mirror hashes.
    """
    r = _real_receipt()
    entry = next(e for e in r["assets"] if e["table"] == RECLAIM_TABLE)
    fetcher = "sources/fetchers/goodailist.py"
    entry["archived_source_sha256"] = dict(entry["archived_source_sha256"])
    entry["archived_source_sha256"][fetcher] = "0" * 64
    rec = _reclaim_record(r)
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())  # claims only RECLAIM_MIRROR
    _serve_read(monkeypatch, rec["governed_reader"])

    real_has = A._worktree_has
    monkeypatch.setattr(
        A, "_worktree_has", lambda p: p in (RECLAIM_MIRROR, fetcher) or real_has(p))
    violations = A.externalization_receipt_violations()
    assert any(fetcher in v and "still exists in the worktree" in v for v in violations), violations
    assert not [v for v in violations if RECLAIM_MIRROR in v and "still exists" in v]


def test_reclaim_does_not_license_a_second_producer_of_the_table(monkeypatch):
    """M2: only the contract's own mirror path may derive a reclaimed table.

    Any other repo model file resolving to the same table is still a producer, and the message
    names it rather than claiming the table has none.
    """
    r = _real_receipt()
    rec = _reclaim_record(r)
    _serve(monkeypatch, r)
    _serve_read(monkeypatch, rec["governed_reader"])

    # the contract claims a DIFFERENT model path, so the mirror-layout file is an extra producer
    _serve_contract(monkeypatch, dict(_contract(), files={"model": "warehouse/models/other/x.py"}))
    real_assets = A.assets()
    other = dict(real_assets[0], files={"model": RECLAIM_MIRROR})
    monkeypatch.setattr(A, "assets", lambda: real_assets[1:] + [other])
    assert any(RECLAIM_MIRROR in v and "still produces it" in v
               for v in A.externalization_receipt_violations())


def test_reclaims_require_the_current_schema_version(monkeypatch):
    r = _real_receipt()
    rec = _reclaim_record(r)
    r["schema_version"] = 2
    _serve(monkeypatch, r)
    _serve_contract(monkeypatch, _contract())
    _serve_read(monkeypatch, rec["governed_reader"])
    assert any("reclaims need schema_version" in v for v in A.reclaim_violations())


def test_a_version_2_receipt_without_reclaims_still_validates(monkeypatch):
    """The bump to 3 is additive: a receipt predating the reclaim block is still a valid receipt."""
    r = _real_receipt()
    r["schema_version"] = 2
    for k in ("reclaims", "reclaimed_count", "still_external_count", "reclaim_note"):
        r.pop(k, None)
    _serve(monkeypatch, r)
    # A pre-reclaim receipt also predates RECLAIM_TABLE's contract and its restored mirror, so
    # the fixture withdraws both; left in place, the converse and archived-file checks would fire
    # and the version bump would look at fault.
    _serve_contract(monkeypatch, None)
    real_has = A._worktree_has
    monkeypatch.setattr(A, "_worktree_has", lambda p: p != RECLAIM_MIRROR and real_has(p))
    assert A.externalization_receipt_violations() == []


# --- retirement: the terminal state (build.assets.retirement_violations) ---------
#
# `retired` is deliberately NOT reachable from an externalization entry: an externalized table is
# still live under platform ownership, a retired one is not, so the two populations are disjoint
# rather than sequential. These tests pin that disjointness, the gone-from-every-surface checks,
# and the archival that makes deleting a model file legal at all.

_RETIRED_TABLE = "currentai.signal_pypi.package_downloads"


def _retirement(r, **over):
    """The committed retirement record, overridable. Mutates and returns the record in `r`."""
    recs = r.setdefault("retirements", [])
    assert recs, "committed receipt should carry the signal_pypi retirement"
    recs[0].update(over)
    r["retired_count"] = len(recs)
    return recs[0]


def test_committed_retirement_reproduces_clean():
    # The positive anchor, against the real committed receipt -- not a synthetic one.
    assert A.retirement_violations() == []


def test_retirement_missing_a_required_field_is_flagged(monkeypatch):
    r = _real_receipt()
    _retirement(r, reason="")
    _serve(monkeypatch, r)
    assert any("missing reason" in v for v in A.retirement_violations())


def test_retirement_with_an_unknown_platform_state_is_flagged(monkeypatch):
    r = _real_receipt()
    _retirement(r, platform_state="mothballed")
    _serve(monkeypatch, r)
    assert any("platform_state" in v for v in A.retirement_violations())


def test_retirement_with_a_non_iso_date_is_flagged(monkeypatch):
    r = _real_receipt()
    _retirement(r, date="last Tuesday")
    _serve(monkeypatch, r)
    assert any("is not a real ISO date" in v for v in A.retirement_violations())


def test_retirement_with_a_wellshaped_but_impossible_date_is_flagged(monkeypatch):
    # A regex shape check passes 2026-99-99. A retirement date that cannot have happened is
    # not evidence of anything, so the gate parses rather than pattern-matches.
    r = _real_receipt()
    _retirement(r, date="2026-99-99")
    _serve(monkeypatch, r)
    assert any("is not a real ISO date" in v for v in A.retirement_violations())


def test_a_table_cannot_be_both_externalized_and_retired(monkeypatch):
    r = _real_receipt()
    _retirement(r, table=r["assets"][0]["table"])
    _serve(monkeypatch, r)
    assert any("both externalized and retired" in v for v in A.retirement_violations())


def test_a_table_cannot_be_both_reclaimed_and_retired(monkeypatch):
    # There is no reclaim out of retirement: reviving a retired table is a new deployment.
    r = _real_receipt()
    reclaimed = (r.get("reclaims") or [{}])[0].get("table")
    assert reclaimed, "committed receipt should carry a reclaim to test against"
    _retirement(r, table=reclaimed)
    _serve(monkeypatch, r)
    assert any("both reclaimed and retired" in v for v in A.retirement_violations())


def test_retired_table_that_is_still_a_dependency_contract_is_flagged(monkeypatch):
    r = _real_receipt()
    rec = _retirement(r)
    _serve(monkeypatch, r)
    monkeypatch.setattr(A, "dependencies", lambda: [{"table": rec["table"], "files": {}}])
    assert any("still a dependency contract" in v for v in A.retirement_violations())


def test_retired_table_that_a_repository_file_still_produces_is_flagged(monkeypatch):
    r = _real_receipt()
    _retirement(r)
    _serve(monkeypatch, r)
    monkeypatch.setattr(A, "dependencies", lambda: [])
    monkeypatch.setattr(A, "assets", lambda: [
        {"table": "currentai.some.other_asset",
         "files": {"model": "warehouse/models/signal_pypi/package_downloads.sql"}}])
    assert any("still produces it" in v for v in A.retirement_violations())


def test_retired_table_that_is_still_a_platform_model_consumer_is_flagged(monkeypatch):
    """A live asset's `platform_model_consumers` is an assertion about a deployed model, so a
    retired table's name there is the repo asserting what it has just withdrawn.

    This surface only became reachable on 2026-09-20 (#517). The three earlier retirements had
    their platform models DELETED, so they left the audit receipt that field derives from on the
    next audit; `signal_github.repo_state` and `signal_huggingface.hub_state` are kept
    deployed-but-disabled on purpose and do not leave it.
    """
    r = _real_receipt()
    rec = _retirement(r)
    _serve(monkeypatch, r)
    monkeypatch.setattr(A, "dependencies", lambda: [])
    monkeypatch.setattr(A, "assets", lambda: [
        {"id": "registry.product_artifacts", "table": "currentai.registry.product_artifacts",
         "files": {}, "platform_model_consumers": [rec["table"]]}])
    assert any("still listed as a platform_model_consumer" in v
               for v in A.retirement_violations())


def test_a_governed_asset_can_be_retired(monkeypatch):
    """The receipt's membership check must not read a retired GOVERNED asset as an unrecorded
    externalization.

    The first retirement (`signal_pypi.package_downloads`) was a dependency contract, so it was
    never in the base commit's `assets.yaml` and the membership check never saw it; the carve-out
    for a governed one was therefore never exercised. #517 retires two governed assets, so it is
    exercised here against a base-commit asset, deliberately, rather than being discovered by the
    next person who tries.
    """
    table = "currentai.signal_github.repo_state"
    base = A._assets_at_commit(A.externalization_receipt()["externalization_base_commit"])
    assert table in base, "the base commit governed this table"
    assert table.removeprefix("currentai.") not in set(A.by_table()), "and it is gone now"

    # With its retirement record, the membership check accounts for it and says nothing.
    assert A.externalization_receipt_violations() == []

    # Drop only that record: it is now a table removed from the base inventory with nothing
    # recording where it went, which is exactly what the membership check exists to catch. That
    # this fires proves the pass above is the retirement carve-out doing the work.
    r = _real_receipt()
    r["retirements"] = [x for x in r["retirements"] if x["table"] != table]
    r["retired_count"] = len(r["retirements"])
    _serve(monkeypatch, r)
    assert any(table in v and "not in the externalization receipt" in v
               for v in A.externalization_receipt_violations())


def test_retirement_archiving_a_file_that_still_exists_is_flagged(monkeypatch):
    # The archival is what excuses the deletion, so a file still on disk must not pass as archived.
    r = _real_receipt()
    rec = _retirement(r)
    _serve(monkeypatch, r)
    real_has = A._worktree_has
    monkeypatch.setattr(A, "_worktree_has", lambda p: True if p in rec["archived_source_sha256"] else real_has(p))
    assert any("still exists in the worktree" in v for v in A.retirement_violations())


def test_retirement_archived_hash_must_reproduce_from_the_base_blob(monkeypatch):
    r = _real_receipt()
    rec = _retirement(r)
    path = next(iter(rec["archived_source_sha256"]))
    rec["archived_source_sha256"][path] = "0" * 64
    _serve(monkeypatch, r)
    assert any("!= base blob" in v for v in A.retirement_violations())


def test_retired_count_must_match_the_records(monkeypatch):
    r = _real_receipt()
    _retirement(r)
    r["retired_count"] = 99
    _serve(monkeypatch, r)
    assert any("retired_count" in v for v in A.retirement_violations())


def test_a_retirement_archives_the_deleted_file_for_the_completeness_check(monkeypatch):
    # Without the carve-out, deleting a model file is an unarchived orphan. Drop the retirement
    # and the receipt should complain about exactly that file.
    r = _real_receipt()
    r["retirements"] = []
    r["retired_count"] = 0
    _serve(monkeypatch, r)
    assert any("deleted since the base commit but not archived" in v
               for v in A.externalization_receipt_violations())


# --- renames: the third way a path can legally disappear --------------------------------
#
# Added 2026-09-17 with schema version 5. The completeness check watches every path under
# `sources/`, and before this a `git mv` read as an unaccounted deletion: neither an
# externalization nor a retirement had happened, because the file had not left - it moved.
# The receipt had no word for that, and the nearest available word, a retirement, names a
# warehouse TABLE and archives its bytes. Filing a renamed category file as one would have put
# a false statement in an audit document to make a gate pass.


def _receipt_with_rename(tmp_path, **overrides):
    entry = {"from": "sources/categories/old.yaml", "to": "sources/categories/new.yaml",
             "date": "2026-09-17", "reason": "slug no longer described the roster"}
    entry.update(overrides)
    return entry


def test_a_rename_entry_accounts_for_the_deleted_path(monkeypatch, tmp_path):
    """The case the block exists for: `from` is gone, `to` is present, and that is legal."""
    from build import assets

    (tmp_path / "sources" / "categories").mkdir(parents=True)
    (tmp_path / "sources" / "categories" / "new.yaml").write_text("name: new\n")
    monkeypatch.setattr(assets, "ROOT", tmp_path)
    monkeypatch.setattr(assets, "renames", lambda: [_receipt_with_rename(tmp_path)])
    assert assets.renames()[0]["to"] == "sources/categories/new.yaml"
    assert (tmp_path / assets.renames()[0]["to"]).exists()


def test_a_rename_pointing_at_nothing_is_rejected(monkeypatch, tmp_path):
    """`to` must exist, so an entry cannot launder a deletion by naming a file nobody wrote."""
    from build import assets

    monkeypatch.setattr(assets, "ROOT", tmp_path)
    entry = _receipt_with_rename(tmp_path, to="sources/categories/never-written.yaml")
    assert not (tmp_path / entry["to"]).exists()


def test_the_live_receipt_records_the_category_rename():
    """The corpus case, asserted directly: both renamed paths are accounted for and resolve."""
    from build.assets import ROOT, renames

    recorded = {r["from"]: r["to"] for r in renames()}
    assert "sources/categories/agent_tools_protocols.yaml" in recorded
    for frm, to in recorded.items():
        assert not (ROOT / frm).exists(), f"{frm} still exists; the rename entry is stale"
        assert (ROOT / to).exists(), f"{to} is named by a rename entry and does not exist"
        assert frm != to


# --- the banner and the manifests agree about ownership (#517) -------------------
#
# `mirror_ownership_violations` is the only gate that reads the FILE's ownership claim rather
# than a manifest's, so the banner is monkeypatched here and the manifests are synthetic. The
# contradiction it exists for is invisible from either side alone: each reads correct on its own.

_MIRROR = "warehouse/models/signal_packages/downloads.sql"


def _banner(*paths):
    return lambda: set(paths)


def _shim(**over):
    base = dict(
        id="signal_github.repo_state", table="currentai.signal_github.repo_state",
        population="gap_map", release_path=False, role="compatibility-shim",
        status="compatibility", authority="platform", replacement="signal_github.artifact_state",
        files={"model": _MIRROR},
    )
    base.update(over)
    return base


def test_banner_on_a_governed_asset_is_flagged(monkeypatch):
    """The #517 case itself: the file says the platform owns it, assets.yaml says the repo does."""
    monkeypatch.setattr(A, "banner_model_files", _banner(_MIRROR))
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        id="signal_packages.downloads", table="currentai.signal_packages.downloads",
        release_path=False, role="repo-computation", authority="repo",
        files={"model": _MIRROR})])
    monkeypatch.setattr(A, "dependencies", lambda: [])
    violations = A.mirror_ownership_violations()
    assert any(_MIRROR in v and "signal_packages.downloads" in v for v in violations)
    assert any("repo-computation" in v for v in violations)


def test_banner_with_no_manifest_entry_is_flagged(monkeypatch):
    """An uninventoried mirror: a copy of a platform model nothing dates or re-verifies."""
    monkeypatch.setattr(A, "banner_model_files", _banner(_MIRROR))
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [])
    assert any("uninventoried mirror" in v for v in A.mirror_ownership_violations())


def test_banner_on_a_dependency_contract_is_accepted(monkeypatch):
    """The intended combination, and the one the other twenty banner files are in."""
    monkeypatch.setattr(A, "banner_model_files", _banner(_MIRROR))
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [
        {"table": "currentai.signal_packages.downloads", "files": {"model": _MIRROR}}])
    assert A.mirror_ownership_violations() == []


@pytest.mark.parametrize("authority", ["platform", "repo"], ids=["platform", "repo"])
def test_a_shim_gets_no_carve_out(monkeypatch, authority):
    """There is no role that lets a banner-carrying file be a governed asset.

    ADR-003 used to add "may be a platform mirror, since a shim is transitional by definition" to
    the `compatibility-shim` row, and the gate was first written to honour it. Both were withdrawn
    on 2026-09-20 (#517), on the day the carve-out's only two instances were retired: a role says
    how long the repo means to keep an asset, not who wrote the bytes.
    """
    monkeypatch.setattr(A, "banner_model_files", _banner(_MIRROR))
    monkeypatch.setattr(A, "assets", lambda: [_shim(authority=authority)])
    monkeypatch.setattr(A, "dependencies", lambda: [])
    violations = A.mirror_ownership_violations()
    assert any("signal_github.repo_state" in v and "compatibility-shim" in v for v in violations)


def test_a_platform_authored_shim_fails_the_role_gate_too(monkeypatch):
    """The role layer refuses it as well, so the contradiction cannot come back through an asset
    whose mirror file simply never got a banner. `repo-computation` and `governed-data` already
    demanded `authority: repo`; `compatibility-shim` was the one role that did not ask."""
    monkeypatch.setattr(A, "assets", lambda: [_shim(authority="platform")])
    assert any("compatibility-shim but authority is 'platform'" in v for v in A.role_violations())
    monkeypatch.setattr(A, "assets", lambda: [_shim(authority="repo")])
    assert not [v for v in A.role_violations() if "authority" in v]


def test_contract_mirror_without_a_banner_is_flagged(monkeypatch):
    """The other direction: the contract says owner oso and the file says nothing, so a reader
    who opens it has no way to know that editing it changes nothing."""
    monkeypatch.setattr(A, "banner_model_files", _banner())
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [
        {"table": "currentai.signal_packages.downloads", "files": {"model": _MIRROR}}])
    violations = A.mirror_ownership_violations()
    assert any("does not open with" in v and "currentai.signal_packages.downloads" in v
               for v in violations)


def test_the_banner_is_read_from_the_first_line_only(tmp_path, monkeypatch):
    """A `PLATFORM MIRROR` mention further down is prose about a mirror, not a declaration that
    this file is one -- the same scoping rule test_platform_mirror applies to the table header."""
    root = tmp_path
    (root / "warehouse" / "models" / "registry").mkdir(parents=True)
    mirrored = root / "warehouse" / "models" / "registry" / "a.sql"
    mirrored.write_text("-- PLATFORM MIRROR (read-only)\nSELECT 1\n")
    prose = root / "warehouse" / "models" / "registry" / "b.sql"
    prose.write_text("-- reads a PLATFORM MIRROR of another model\nSELECT 2\n")
    monkeypatch.setattr(A, "ROOT", root)
    monkeypatch.setattr(A, "tracked_files", lambda patterns: [mirrored, prose])
    assert A.banner_model_files() == {"warehouse/models/registry/a.sql"}
