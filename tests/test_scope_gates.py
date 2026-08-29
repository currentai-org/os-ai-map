"""Negative tests for the ADR-003 scope-boundary gates and the dependency manifest.

The positive checks (the real inventory passes) live in test_assets_inventory.py. Here each
gate is shown to FAIL on a constructed violation -- a gate that cannot fail catches nothing,
the recurring "check establishes less than it reports" defect this data system keeps closing.
The real assets()/dependencies()/derivation helpers are monkeypatched with synthetic inputs so
a single violation can be isolated without touching the committed files.
"""

from __future__ import annotations

import build.assets as A


def _governed(**over):
    """A minimal governed-output asset (release_path, role governed-output, authority repo)."""
    base = dict(
        id="registry.x", table="currentai.registry.x", population="gap_map",
        release_path=True, role="governed-output", status="active", authority="repo",
    )
    base.update(over)
    return base


# --- role gate (gates 1, 6, per-role, ratchet) ----------------------------------

def test_governed_output_without_release_path_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(release_path=False)])
    assert any("gate 1" in v or "derives" in v for v in A.role_violations())


def test_release_path_without_governed_output_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        role="repo-computation", files={"model": "warehouse/models/registry/x.sql"})])
    assert any("gate 1" in v for v in A.role_violations())


def test_repo_computation_with_platform_authority_is_flagged(monkeypatch):
    # ADR-003 finding 1: a platform mirror is a dependency, never a repo-computation.
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        id="scores.openness_facts", table="currentai.scores.openness_facts",
        release_path=False, role="repo-computation", authority="platform",
        files={"model": "warehouse/models/scores/openness_facts.sql"}, mirror={"revision": 7})])
    assert any("authority is 'platform'" in v for v in A.role_violations())


def test_governed_data_with_model_file_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        id="observations.baseline", table="currentai.observations.baseline",
        release_path=False, role="governed-data", authority="repo",
        files={"model": "warehouse/models/observations/baseline.sql"})])
    assert any("has a model file" in v for v in A.role_violations())


def test_compatibility_shim_without_replacement_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        id="signal_github.repo_state", table="currentai.signal_github.repo_state",
        release_path=False, role="compatibility-shim", status="compatibility", authority="platform")])
    assert any("replacement" in v for v in A.role_violations())


def test_new_long_tail_asset_is_flagged_by_the_ratchet(monkeypatch):
    # finding 3: a NEW long_tail (not in the frozen backlog) must be rejected -- shrink-only.
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        id="scores.brand_new", table="currentai.scores.brand_new",
        population="long_tail", release_path=False, role=None)])
    v = A.role_violations()
    assert any("frozen backlog" in x and "long_tail" in x for x in v)


def test_new_roleless_asset_is_flagged_by_the_ratchet(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        id="registry.brand_new", table="currentai.registry.brand_new",
        population="gap_map", release_path=False, role=None)])
    assert any("frozen externalization backlog" in v for v in A.role_violations())


def test_unknown_role_value_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(role="banana")])
    assert any("not one of" in v for v in A.role_violations())


# --- dependency gate (gates 2, 3, 4, integrity) ---------------------------------

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
    # finding 2: a governed computation reading a non-governed currentai.* table is a contract.
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
    # finding 5: an arbitrary 64-hex string must not pass -- the gate recomputes the fingerprint.
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


# --- F2 fail-closed: currentai mirror integrity + required fields ---------------

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


# --- F1 cross-commit provenance for dependency mirrors --------------------------

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


# --- F1 (re-review): the SCHEMA file is part of the cross-commit byte identity -----

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


# --- F3 the root set is closed ---------------------------------------------------

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
