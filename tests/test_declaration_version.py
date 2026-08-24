"""The declaration-version identity, and the properties that keep it honest.

`build/declaration_version.py` derives `declaration_version_id` (data-architecture.md §4.5):
the identity of a set of declarations, evaluated by a named evaluator, that
`registry.axis_assessments`, `evaluation.product_adoption_measurements` and
`evaluation.adoption_reconciliation` all key on.

There is no committed golden value to pin — the id embeds `source_git_sha`, and freezing a
receipt would either name its own parent commit or force a regenerate step on every score edit
(see the module docstring). So these tests pin the canonicalization's PROPERTIES instead:
the classified `sources/` inventory, determinism, order-invariance, type rejection, the
fail-closed behavior on a dirty tree, and that the id responds to each component.
"""

import copy
import hashlib
from pathlib import Path

import pytest

import build.declaration_version as dv
from build.declaration_version import (
    CANONICALIZATION_VERSION,
    DECLARATION_INPUTS,
    EVALUATOR_VERSION,
    NON_DECLARATION_INPUTS,
    POLICY_INPUTS,
    DirtyDeclarationsError,
    canonical_json,
    declaration_content,
    declaration_version_id,
    resolve,
    source_content_digest,
)

ROOT = Path(__file__).resolve().parents[1]


# --- the classified inventory (finding 1) ----------------------------------------


def test_source_inventory_is_fully_classified():
    """Every top-level sources/ entry is classified into exactly one bucket.

    This is the 'declared state matches reality' gate for the identity, and it protects the
    WHOLE sources/ inventory rather than only what load_sources parses: add a new authoritative
    input to sources/ and this fails until it is folded into the digest, bound downstream as a
    policy input, or explicitly declared a non-declaration. An input cannot silently escape the
    identity.
    """
    entries = {p.name for p in (ROOT / "sources").iterdir()}
    declaration = set(DECLARATION_INPUTS)
    policy = set(POLICY_INPUTS)
    non_declaration = set(NON_DECLARATION_INPUTS)

    classified = declaration | policy | non_declaration
    assert entries == classified, (
        f"sources/ holds {sorted(entries)}, but the identity classifies {sorted(classified)}; "
        "every entry must be a declaration, a downstream-bound policy, or a declared exclusion."
    )
    # The three buckets are disjoint: an entry is exactly one kind.
    assert declaration.isdisjoint(policy)
    assert declaration.isdisjoint(non_declaration)
    assert policy.isdisjoint(non_declaration)


def test_uncovered_declaration_inputs_are_included():
    """The two authoritative inputs load_sources does NOT return are in the digest.

    evidence_policy.yaml shapes serialized registry output and verification_queue.yaml governs
    release eligibility; both are declarations and must move the id when they change.
    """
    assert "evidence_policy.yaml" in DECLARATION_INPUTS
    assert "verification_queue.yaml" in DECLARATION_INPUTS
    content = declaration_content(ROOT)
    assert "evidence_policy.yaml" in content
    assert "verification_queue.yaml" in content


def test_policy_inputs_name_a_downstream_binding():
    """A policy input is excluded from THIS identity only by naming where its version binds.

    The exclusion is a redirection, not a gap: signal_routing.yaml carries routing_policy_version
    and must bind into a downstream identity, so its record names both.
    """
    assert "signal_routing.yaml" in POLICY_INPUTS
    for name, spec in POLICY_INPUTS.items():
        assert spec.get("policy_version"), f"{name} names no policy version"
        assert spec.get("bound_into"), f"{name} names no downstream identity to bind into"


def test_frozen_snapshot_is_a_non_declaration():
    """The frozen warehouse sample is excluded, with a reason, and never enters the digest."""
    assert "snapshots" in NON_DECLARATION_INPUTS
    assert NON_DECLARATION_INPUTS["snapshots"]
    assert "snapshots" not in declaration_content(ROOT)


# --- canonicalization properties --------------------------------------------------


def test_digest_is_deterministic():
    assert source_content_digest(ROOT) == source_content_digest(ROOT)


def test_digest_matches_the_documented_rule():
    """The public digest is exactly sha256 of canonical_json(declaration_content)."""
    expected = hashlib.sha256(
        canonical_json(declaration_content(ROOT)).encode("utf-8")
    ).hexdigest()
    assert source_content_digest(ROOT) == expected


def test_canonical_json_is_key_order_invariant():
    """A curator reordering keys in a YAML file must produce no change in the serialization."""
    a = {"z": 1, "a": {"y": 2, "x": 3}, "m": [1, 2, 3]}
    b = {"a": {"x": 3, "y": 2}, "m": [1, 2, 3], "z": 1}
    assert canonical_json(a) == canonical_json(b)


def test_canonical_json_preserves_list_order():
    """Key order is normalized; list order is content and must be preserved."""
    assert canonical_json({"k": [1, 2, 3]}) != canonical_json({"k": [3, 2, 1]})


def test_canonical_json_renders_dates_deterministically():
    """A YAML `date` scalar serializes to its ISO text, not a Python repr."""
    import datetime

    out = canonical_json({"last_verified": datetime.date(2026, 8, 13)})
    assert "2026-08-13" in out


def test_reordering_a_loaded_declaration_does_not_change_the_digest():
    """End-to-end order-invariance over the real declaration content."""
    content = declaration_content(ROOT)
    baseline = hashlib.sha256(canonical_json(content).encode("utf-8")).hexdigest()
    shuffled = copy.deepcopy(content)
    shuffled = {k: shuffled[k] for k in reversed(list(shuffled))}
    assert hashlib.sha256(canonical_json(shuffled).encode("utf-8")).hexdigest() == baseline


# --- strict type handling (finding 3) --------------------------------------------


def test_canonical_json_rejects_unsupported_types():
    """A YAML set (or any non-JSON-native object) is rejected, never coerced to a string."""
    with pytest.raises(TypeError):
        canonical_json({"x": {1, 2, 3}})

    class Weird:
        pass

    with pytest.raises(TypeError):
        canonical_json({"x": Weird()})


def test_canonical_json_rejects_non_finite_numbers():
    """NaN and Infinity are not valid JSON and do not round-trip; reject rather than emit."""
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            canonical_json({"x": bad})


# --- fail-closed on a dirty tree (finding 2) -------------------------------------


def test_resolve_fails_closed_on_dirty_declarations(monkeypatch):
    """With uncommitted declarations, resolve() raises rather than emit an unreproducible id.

    Synthetic: the cleanliness probe is forced to report dirty, so the fail-closed branch is
    exercised without dirtying the real tree.
    """
    monkeypatch.setattr(dv, "declaration_paths_are_clean", lambda *a, **k: False)
    with pytest.raises(DirtyDeclarationsError):
        resolve()


def test_resolve_allow_dirty_opt_in_returns_a_diagnostic_value(monkeypatch):
    """The explicit opt-in returns a value and records that the tree was dirty."""
    monkeypatch.setattr(dv, "declaration_paths_are_clean", lambda *a, **k: False)
    info = resolve(allow_dirty=True)
    assert info["declarations_clean"] is False
    assert len(info["declaration_version_id"]) == 64


def test_resolve_clean_tree_succeeds():
    """On a clean tree resolve() returns the full component set without opt-in."""
    info = resolve()
    assert info["declarations_clean"] is True
    assert len(info["declaration_version_id"]) == 64


# --- the id itself ----------------------------------------------------------------


def test_evaluator_version_is_the_declared_sentinel():
    """The Phase-6 evaluator does not exist yet; the component is a deliberate sentinel, not ''."""
    assert EVALUATOR_VERSION == "v0-no-repo-evaluator"
    assert EVALUATOR_VERSION != ""


def test_declaration_version_id_shape():
    """A lowercase 64-hex sha256 — an opaque id, never a readable concatenation."""
    vid = declaration_version_id("a" * 40, "b" * 64)
    assert len(vid) == 64
    assert vid == vid.lower()
    int(vid, 16)  # hex


def test_declaration_version_id_is_sensitive_to_each_component():
    sha, digest = "a" * 40, "b" * 64
    base = declaration_version_id(sha, digest)
    assert declaration_version_id(sha, digest) == base  # stable
    assert declaration_version_id("c" * 40, digest) != base  # git sha
    assert declaration_version_id(sha, "d" * 64) != base  # content digest
    assert declaration_version_id(sha, digest, "v1-real-evaluator") != base  # evaluator


def test_canonicalization_version_participates_in_the_id(monkeypatch):
    """Bumping the canonicalization version changes every id, so a value minted under the old
    rule cannot collide with one minted under the new rule."""
    sha, digest = "a" * 40, "b" * 64
    before = declaration_version_id(sha, digest)
    monkeypatch.setattr(dv, "CANONICALIZATION_VERSION", CANONICALIZATION_VERSION + 1)
    assert dv.declaration_version_id(sha, digest) != before
