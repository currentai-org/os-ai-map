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

_REAL_MODEL = "warehouse/models/signal_pypi/package_downloads.sql"


def _currentai_dep(**over):
    h = hashlib.sha256((A.ROOT / _REAL_MODEL).read_bytes()).hexdigest()
    base = dict(
        table="currentai.signal_pypi.package_downloads", purpose="p", expected_grain="g",
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

def _prior_asset(**over):
    m = {"model_id": "m", "revision": 3, "hash": "hh", "local_sha256": "aaa", "synced_at": "2026-08-15"}
    m.update(over)
    return {"id": "signal_pypi.package_downloads", "table": "currentai.signal_pypi.package_downloads",
            "mirror": m}


def _cur_dep(**over):
    m = {"model_id": "m", "revision": 3, "hash": "hh", "local_sha256": "aaa", "synced_at": "2026-08-15"}
    m.update(over.pop("mirror", {}))
    d = {"table": "currentai.signal_pypi.package_downloads", "mirror": m}
    d.update(over)
    return d


def test_asset_to_dependency_transition_with_identical_provenance_passes(monkeypatch):
    monkeypatch.setattr(A, "merge_base_assets", lambda base="origin/main": [_prior_asset()])
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [])
    monkeypatch.setattr(A, "dependencies", lambda: [_cur_dep()])
    assert A.dependency_mirror_provenance_violations() == []


def test_dependency_bytes_changed_without_revision_advance_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "merge_base_assets", lambda base="origin/main": [_prior_asset()])
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [])
    monkeypatch.setattr(A, "dependencies",
                        lambda: [_cur_dep(mirror={"local_sha256": "bbb", "hash": "new"})])  # bytes moved, rev still 3
    assert any("revision" in v for v in A.dependency_mirror_provenance_violations())


def test_dependency_provenance_changed_without_bytes_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "merge_base_assets", lambda base="origin/main": [_prior_asset()])
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [])
    monkeypatch.setattr(A, "dependencies",
                        lambda: [_cur_dep(mirror={"revision": 99})])  # same bytes, revision moved
    assert any("bytes did not" in v for v in A.dependency_mirror_provenance_violations())


def test_dependency_model_id_change_without_migration_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "merge_base_assets", lambda base="origin/main": [_prior_asset()])
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [])
    monkeypatch.setattr(A, "dependencies", lambda: [_cur_dep(mirror={"model_id": "other"})])
    assert any("model_id changed" in v for v in A.dependency_mirror_provenance_violations())


# --- the SCHEMA file is part of the cross-commit byte identity ------------------

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
    monkeypatch.setattr(A, "merge_base_assets", lambda base="origin/main": [])
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [_prior_dep_schema("sold")])
    monkeypatch.setattr(A, "dependencies", lambda: [_cur_dep_schema("snew")])  # rev still 3
    assert any("revision" in v for v in A.dependency_mirror_provenance_violations())


def test_schema_changed_with_revision_advance_is_accepted(monkeypatch):
    monkeypatch.setattr(A, "merge_base_assets", lambda base="origin/main": [])
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [_prior_dep_schema("sold")])
    monkeypatch.setattr(A, "dependencies",
                        lambda: [_cur_dep_schema("snew", revision=4, hash="new")])
    assert A.dependency_mirror_provenance_violations() == []


def test_transition_with_unchanged_schema_is_accepted(monkeypatch):
    # prior was a governed asset (no schema_sha256); derive it from the merge-base schema file.
    monkeypatch.setattr(A, "merge_base_assets",
                        lambda base="origin/main": [_prior_asset(local_sha256="model")])
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [])
    monkeypatch.setattr(A, "_merge_base_sha", lambda base="origin/main": "fakesha")
    monkeypatch.setattr(A, "_git_blob_sha256", lambda sha, path: "scur")  # == current schema digest
    monkeypatch.setattr(A, "dependencies", lambda: [_cur_dep_schema("scur")])
    assert A.dependency_mirror_provenance_violations() == []


def test_transition_with_changed_schema_and_frozen_provenance_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "merge_base_assets",
                        lambda base="origin/main": [_prior_asset(local_sha256="model")])
    monkeypatch.setattr(A, "merge_base_dependencies", lambda base="origin/main": [])
    monkeypatch.setattr(A, "_merge_base_sha", lambda base="origin/main": "fakesha")
    monkeypatch.setattr(A, "_git_blob_sha256", lambda sha, path: "sold")  # != current schema digest
    monkeypatch.setattr(A, "dependencies", lambda: [_cur_dep_schema("scur")])  # rev still 3
    assert any("revision" in v for v in A.dependency_mirror_provenance_violations())


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
