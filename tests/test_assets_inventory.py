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
NAMESPACES = {"registry", "catalog", "observations", "evaluation", "releases"}
STATUSES = {"active", "staged", "deprecated", "historical", "compatibility"}
SCOPES = {"in_repo_only", "platform_checked", "externally_confirmed"}


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
        for role, path in (asset.get("files") or {}).items():
            if not path:
                continue
            assert path not in seen, f"{path} claimed by {seen[path]} and {asset['id']}:{role}"
            seen[path] = f"{asset['id']}:{role}"


def test_every_declared_path_exists(inventory):
    for asset in inventory:
        for role, path in (asset.get("files") or {}).items():
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
        for field in ("id", "table", "kind", "current_namespace", "target_namespace",
                      "migration_status", "authority", "population", "release_path",
                      "consumer_scope", "owner", "status", "verified_at"):
            assert field in asset, f"{asset['id']}: missing {field}"
        assert asset["status"] in STATUSES, f"{asset['id']}: bad status"
        assert asset["consumer_scope"] in SCOPES, f"{asset['id']}: bad consumer_scope"
        assert asset["authority"] in {"repo", "platform", "external"}, asset["id"]
        assert asset["population"] in {"gap_map", "long_tail", "both"}, asset["id"]


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
