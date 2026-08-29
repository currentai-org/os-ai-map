"""Negative tests for the ADR-003 scope-boundary gates and the dependency manifest.

The positive checks (the real inventory passes) live in test_assets_inventory.py. Here each
gate is shown to FAIL on a constructed violation -- a gate that cannot fail catches nothing,
the recurring "check establishes less than it reports" defect this data system keeps closing.
The real assets()/dependencies()/derive_graph() are monkeypatched with synthetic inputs so a
single violation can be isolated without touching the committed files.
"""

from __future__ import annotations

import build.assets as A


def _governed(**over):
    """A minimal governed-output asset (release_path, role governed-output)."""
    base = dict(
        id="registry.x", table="currentai.registry.x", population="gap_map",
        release_path=True, role="governed-output", status="active", authority="repo",
    )
    base.update(over)
    return base


# --- role gate (gates 1, 6, backlog) --------------------------------------------

def test_governed_output_without_release_path_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(release_path=False)])
    # release_path False + role governed-output: expected_role now derives repo-computation,
    # so the authored role disagrees AND gate 1 fires.
    assert any("gate 1" in v or "derives" in v for v in A.role_violations())


def test_release_path_without_governed_output_is_flagged(monkeypatch):
    # A release_path asset mislabelled as repo-computation.
    monkeypatch.setattr(A, "assets", lambda: [_governed(role="repo-computation")])
    assert any("gate 1" in v for v in A.role_violations())


def test_long_tail_carrying_a_role_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [
        _governed(id="entities.models", table="currentai.entities.models",
                  population="long_tail", release_path=False, role="repo-computation"),
    ])
    assert any("backlog" in v for v in A.role_violations())


def test_governed_asset_missing_its_role_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(role=None)])
    assert any("missing its role" in v for v in A.role_violations())


def test_repo_computation_platform_without_mirror_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        id="scores.openness_facts", table="currentai.scores.openness_facts",
        release_path=False, role="repo-computation", authority="platform",
        files={"model": "warehouse/models/scores/openness_facts.sql"},
    )])  # no mirror block
    assert any("no mirror block" in v for v in A.role_violations())


def test_compatibility_shim_without_replacement_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        id="signal_github.repo_state", table="currentai.signal_github.repo_state",
        release_path=False, role="compatibility-shim", status="compatibility",
    )])  # no replacement
    assert any("replacement" in v for v in A.role_violations())


def test_unknown_role_value_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(role="banana")])
    assert any("not one of" in v for v in A.role_violations())


# --- dependency gate (gates 2, 3, 4) --------------------------------------------

def _dep(**over):
    base = dict(
        table="oso.x.y", purpose="p", expected_grain="g",
        required_by=["warehouse/models/signal_pypi/package_downloads.sql"],
        content_contract_sha256="a" * 64, verified_at="2026-08-29", owner="oso",
    )
    base.update(over)
    return base


def test_dependency_also_in_assets_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(table="oso.x.y", authority="repo")])
    monkeypatch.setattr(A, "dependencies", lambda: [_dep()])
    monkeypatch.setattr(A, "_repo_computation_external_reads",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("gate 3" in v for v in A.dependency_violations())


def test_external_read_missing_from_manifest_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [])
    monkeypatch.setattr(A, "_repo_computation_external_reads",
                        lambda: {"oso.unlisted.tbl": ["warehouse/models/foo.sql"]})
    assert any("gate 2" in v for v in A.dependency_violations())


def test_dependency_required_by_disagreeing_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [_dep(required_by=["warehouse/models/wrong.sql"])])
    monkeypatch.setattr(A, "_repo_computation_external_reads",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("gate 4" in v for v in A.dependency_violations())


def test_notebook_only_dependency_is_flagged(monkeypatch):
    # A contract nothing governed reads (only a notebook reads it, so it is absent from the
    # derived governed reads) -> gate 4.
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [_dep()])
    monkeypatch.setattr(A, "_repo_computation_external_reads", lambda: {})
    assert any("gate 4" in v for v in A.dependency_violations())


def test_dependency_with_both_provenance_anchors_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [_dep(verified_revision=7)])
    monkeypatch.setattr(A, "_repo_computation_external_reads",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("exactly one provenance anchor" in v for v in A.dependency_violations())


def test_dependency_with_no_provenance_anchor_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies",
                        lambda: [_dep(content_contract_sha256=None, verified_at=None)])
    monkeypatch.setattr(A, "_repo_computation_external_reads",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("exactly one provenance anchor" in v for v in A.dependency_violations())


def test_dependency_owner_not_oso_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [])
    monkeypatch.setattr(A, "dependencies", lambda: [_dep(owner="carl")])
    monkeypatch.setattr(A, "_repo_computation_external_reads",
                        lambda: {"oso.x.y": ["warehouse/models/signal_pypi/package_downloads.sql"]})
    assert any("owner must be oso" in v for v in A.dependency_violations())


# --- gate 5: notebook root -------------------------------------------------------

def test_notebook_producer_is_flagged(monkeypatch):
    monkeypatch.setattr(A, "assets", lambda: [_governed(
        role="repo-computation", release_path=False,
        producer="notebooks/long-tail-explorer.py",
        files={"model": "notebooks/long-tail-explorer.py"},
    )])
    assert any("gate 5" in v for v in A.notebook_root_violations())


# --- the dependency loader is well-formed ---------------------------------------

def test_dependencies_loader_returns_contracts():
    deps = A.dependencies()
    assert isinstance(deps, list) and deps, "dependencies.yaml should carry at least one contract"
    for d in deps:
        assert d["owner"] == "oso"
        assert d.get("table", "").startswith(("oso.", "currentai.")), d
        assert d.get("required_by"), d
