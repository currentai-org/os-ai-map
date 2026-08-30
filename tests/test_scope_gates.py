"""Negative tests for the ADR-003 scope-boundary gates and the dependency manifest.

The positive checks (the real inventory passes) live in test_assets_inventory.py. Here each
gate is shown to FAIL on a constructed violation -- a gate that cannot fail catches nothing,
the recurring "check establishes less than it reports" defect this data system keeps closing.
The real assets()/dependencies()/derivation helpers are monkeypatched with synthetic inputs so
a single violation can be isolated without touching the committed files.
"""

from __future__ import annotations

import copy

import build.assets as A


def _governed(**over):
    """A minimal governed-output asset (release_path, role governed-output, authority repo)."""
    base = dict(
        id="registry.x", table="currentai.registry.x", population="gap_map",
        release_path=True, role="governed-output", status="active", authority="repo",
    )
    base.update(over)
    return base


# --- role gate (gate 1, per-role invariants, retired populations) ---------------

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


def test_retired_populations_are_rejected():
    # finding 3: `long_tail` and `both` are retired; the vocabulary is a single value, so the
    # required-fields/vocab gate rejects any governed asset that is not gap_map.
    assert A.POPULATIONS == {"gap_map"}
    assert "long_tail" not in A.POPULATIONS and "both" not in A.POPULATIONS


def test_roleless_asset_is_flagged(monkeypatch):
    # Every asset must carry a role -- there is no roleless/backlog state any more.
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        id="registry.brand_new", table="currentai.registry.brand_new", role=None)])
    assert any("is not one of" in v for v in A.role_violations())


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


def test_altered_base_commit_is_flagged(monkeypatch):
    r = _real_receipt()
    r["externalization_base_commit"] = "0" * 40  # a real-looking sha that does not resolve
    _serve(monkeypatch, r)
    assert any("does not resolve" in v for v in A.externalization_receipt_violations())


def test_valid_but_wrong_ancestor_base_is_flagged(monkeypatch):
    # A resolvable-but-incorrect ancestor (the grandparent of the true boundary) must be rejected:
    # the base is bound to the graph-derived externalization boundary, not merely to "resolves".
    r = _real_receipt()
    real = r["externalization_base_commit"]
    grandparent = A._parent_sha(A._parent_sha(real))  # a valid older ancestor, not the boundary
    assert grandparent and grandparent != real
    r["externalization_base_commit"] = grandparent
    _serve(monkeypatch, r)
    assert any("is not the externalization boundary" in v
               for v in A.externalization_receipt_violations())


def test_base_boundary_derivation_matches_recorded():
    # The graph-derived boundary equals what the committed receipt names -- the positive anchor for
    # the binding, independent of the receipt's own base field.
    tables = {e["table"] for e in A.externalized()}
    derived = A.expected_externalization_base(tables)
    recorded = A.externalization_receipt()["externalization_base_commit"]
    assert derived is not None
    assert derived == A._rev_parse(recorded)


def test_platform_facts_reproduce_against_base_audit_not_current(monkeypatch):
    # Blocker 2: the receipt reproduces against the audit committed AT THE BASE, so a later change
    # to the CURRENT platform_models.json must not affect the verdict. Poison the current audit and
    # confirm the gate is unmoved.
    monkeypatch.setattr(A, "_platform_models",
                        lambda: {"currentai.entities.repos": {"table": "currentai.entities.repos",
                                                              "model_id": "poisoned", "revision_hash": "x",
                                                              "source_sha256": "y", "internal_reads": []}})
    assert A.externalization_receipt_violations() == []


def test_missing_base_audit_is_flagged(monkeypatch):
    # If the base-committed audit cannot be read, deployed-model facts cannot reproduce -> flagged,
    # never silently skipped.
    monkeypatch.setattr(A, "_platform_models_at_commit", lambda sha: {})
    probs = A.externalization_receipt_violations()
    assert any("no audited model exists to source it" in v for v in probs)


def test_wrong_count_is_flagged(monkeypatch):
    r = _real_receipt()
    r["count"] = r["count"] + 1
    _serve(monkeypatch, r)
    assert any("count" in v for v in A.externalization_receipt_violations())


def test_wrong_schema_version_is_flagged(monkeypatch):
    r = _real_receipt()
    r["schema_version"] = 1
    _serve(monkeypatch, r)
    assert any("schema_version" in v for v in A.externalization_receipt_violations())


def test_dropping_a_removed_asset_is_flagged(monkeypatch):
    # Membership is exact: an asset removed from the base inventory must appear in the receipt.
    r = _real_receipt()
    r["assets"] = r["assets"][:-1]
    r["count"] = len(r["assets"])
    _serve(monkeypatch, r)
    assert any("but not in the externalization receipt" in v for v in A.externalization_receipt_violations())


def test_extra_membership_entry_is_flagged(monkeypatch):
    r = _real_receipt()
    bogus = copy.deepcopy(r["assets"][0])
    bogus["id"] = "registry.still_governed"
    bogus["table"] = "currentai.registry.products"  # a table that is STILL governed, not removed
    r["assets"].append(bogus)
    r["count"] = len(r["assets"])
    _serve(monkeypatch, r)
    assert any("not an asset removed from the base inventory" in v
               for v in A.externalization_receipt_violations())


def test_duplicate_entry_is_flagged(monkeypatch):
    r = _real_receipt()
    r["assets"].append(copy.deepcopy(r["assets"][0]))
    r["count"] = len(r["assets"])
    _serve(monkeypatch, r)
    probs = A.externalization_receipt_violations()
    assert any("duplicate entry ids" in v for v in probs)
    assert any("duplicate entry tables" in v for v in probs)


def test_wrong_population_was_is_flagged(monkeypatch):
    r = _real_receipt()
    r["assets"][0]["population_was"] = "gap_map" if r["assets"][0]["population_was"] != "gap_map" else "long_tail"
    _serve(monkeypatch, r)
    assert any("population_was" in v for v in A.externalization_receipt_violations())


def test_altered_archived_hash_is_flagged(monkeypatch):
    r = _real_receipt()
    for e in r["assets"]:
        if e.get("archived_source_sha256"):
            k = next(iter(e["archived_source_sha256"]))
            e["archived_source_sha256"][k] = "0" * 64
            break
    _serve(monkeypatch, r)
    assert any("!= base blob" in v for v in A.externalization_receipt_violations())


def test_unarchived_deleted_file_is_flagged(monkeypatch):
    # Drop the sources archive from the entry that carries it -> the deleted file is now unarchived.
    r = _real_receipt()
    for e in r["assets"]:
        arch = e.get("archived_source_sha256") or {}
        if any(p.startswith("sources/") for p in arch):
            e["archived_source_sha256"] = {p: h for p, h in arch.items() if not p.startswith("sources/")}
            break
    _serve(monkeypatch, r)
    assert any("deleted since the base commit but not archived" in v
               for v in A.externalization_receipt_violations())


def test_fabricated_platform_model_facts_are_flagged(monkeypatch):
    # An entry with no audited model must not carry model facts.
    pmodels = A._platform_models()
    r = _real_receipt()
    for e in r["assets"]:
        if e["table"] not in pmodels:
            e.setdefault("platform", {})["model_id"] = "fabricated-model-id"
            break
    _serve(monkeypatch, r)
    assert any("no audited model exists to source it" in v
               for v in A.externalization_receipt_violations())


def test_wrong_deployed_model_provenance_is_flagged(monkeypatch):
    pmodels = A._platform_models()
    r = _real_receipt()
    for e in r["assets"]:
        if e["table"] in pmodels:
            e["platform"]["revision_hash"] = "0" * 64
            break
    _serve(monkeypatch, r)
    assert any("platform.revision_hash" in v for v in A.externalization_receipt_violations())


def test_altered_repo_consumers_is_flagged(monkeypatch):
    # Even with consumer_resolution prose intact, breaking the reproduced consumer graph fails --
    # the structured, reproduced field is what satisfies the gate, never the prose.
    r = _real_receipt()
    for e in r["assets"]:
        car = e.get("consumers_at_removal") or {}
        if car.get("repo_read_by"):
            e["consumer_resolution"] = "everything resolves fine, trust me"
            car["repo_read_by"] = {"models": ["warehouse/models/made/up.sql"]}
            break
    _serve(monkeypatch, r)
    assert any("repo_read_by != base read_by" in v for v in A.externalization_receipt_violations())


def test_omitted_surviving_platform_consumer_is_flagged(monkeypatch):
    # The captured platform_models list must cover every surviving audited reader (lower bound).
    r = _real_receipt()
    hit = False
    for e in r["assets"]:
        car = e.get("consumers_at_removal") or {}
        if car.get("platform_models"):
            # entities.repos is read by surviving audited state_of_os_ai models; clear the list.
            if "entities.repos" in e["table"]:
                car["platform_models"] = []
                hit = True
                break
    assert hit, "expected entities.repos to record surviving platform consumers"
    _serve(monkeypatch, r)
    assert any("absent from consumers_at_removal.platform_models" in v
               for v in A.externalization_receipt_violations())


def test_dishonest_verification_date_is_flagged(monkeypatch):
    # last_platform_verified_at must equal the asset's real prior date, not a fresh live claim.
    r = _real_receipt()
    r["assets"][0]["last_platform_verified_at"] = "2026-08-30"  # the recording date, not the base date
    _serve(monkeypatch, r)
    # only trips if the base asset's real date differs from 2026-08-30 (it does: 08-20 or 08-29)
    assert any("last_platform_verified_at" in v for v in A.externalization_receipt_violations())


def test_missing_evidence_basis_is_flagged(monkeypatch):
    r = _real_receipt()
    r["assets"][0].pop("evidence_basis", None)
    _serve(monkeypatch, r)
    assert any("missing evidence_basis" in v for v in A.externalization_receipt_violations())


def test_dropped_consumer_resolution_alone_does_not_satisfy_or_break(monkeypatch):
    # consumer_resolution is optional prose: removing it must NOT change the verdict, proving the
    # gate never leans on it.
    r = _real_receipt()
    for e in r["assets"]:
        e.pop("consumer_resolution", None)
    _serve(monkeypatch, r)
    assert A.externalization_receipt_violations() == []


def test_transferred_without_destination_is_flagged(monkeypatch):
    r = _real_receipt()
    r["assets"][0]["disposition"] = "transferred"  # but no destination named
    _serve(monkeypatch, r)
    assert any("must name destination.repository + commit" in v
               for v in A.externalization_receipt_violations())


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
