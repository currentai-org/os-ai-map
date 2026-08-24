"""The declaration-version identity, and the properties that keep it honest.

`build/declaration_version.py` derives `declaration_version_id` (data-architecture.md §4.5):
the identity of a set of declarations, evaluated by a named evaluator, that
`registry.axis_assessments`, `evaluation.product_adoption_measurements` and
`evaluation.adoption_reconciliation` all key on.

There is no committed golden value to pin — the id embeds `source_git_sha`, and freezing a
receipt would either name its own parent commit or force a regenerate step on every score edit
(see the module docstring). So these tests pin the canonicalization's PROPERTIES instead:
the classified `sources/` inventory, determinism, order-invariance, collision-free encoding,
type rejection, the fail-closed behavior on a dirty tracked worktree, and that the id responds
to each component.
"""

import copy
import hashlib
import subprocess
from pathlib import Path

import pytest

import build.declaration_version as dv
from build.declaration_version import (
    CANONICALIZATION_VERSION,
    DECLARATION_INPUTS,
    EVALUATOR_VERSION,
    NON_DECLARATION_INPUTS,
    POLICY_INPUTS,
    DirtyWorktreeError,
    canonical_json,
    declaration_content,
    declaration_version_id,
    resolve,
    source_content_digest,
    tracked_worktree_is_clean,
)

ROOT = Path(__file__).resolve().parents[1]


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)


def _tiny_repo(tmp_path: Path) -> Path:
    """A throwaway git repo with a tracked declaration file and a tracked implementation file."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t.test")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "x.yaml").write_text("a: 1\n", encoding="utf-8")
    (tmp_path / "impl.py").write_text("# identity implementation\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path


# --- the classified inventory (finding 1, first pass) ----------------------------


def test_source_inventory_is_fully_classified():
    """Every top-level sources/ entry is classified into exactly one bucket."""
    entries = {p.name for p in (ROOT / "sources").iterdir()}
    declaration = set(DECLARATION_INPUTS)
    policy = set(POLICY_INPUTS)
    non_declaration = set(NON_DECLARATION_INPUTS)

    classified = declaration | policy | non_declaration
    assert entries == classified, (
        f"sources/ holds {sorted(entries)}, but the identity classifies {sorted(classified)}; "
        "every entry must be a declaration, a downstream-bound policy, or a declared exclusion."
    )
    assert declaration.isdisjoint(policy)
    assert declaration.isdisjoint(non_declaration)
    assert policy.isdisjoint(non_declaration)


def test_uncovered_declaration_inputs_are_included():
    """The two authoritative inputs load_sources does NOT return are in the digest."""
    assert "evidence_policy.yaml" in DECLARATION_INPUTS
    assert "verification_queue.yaml" in DECLARATION_INPUTS
    content = declaration_content(ROOT)
    assert "evidence_policy.yaml" in content
    assert "verification_queue.yaml" in content


def test_policy_inputs_record_a_binding_obligation():
    """A policy input records a PENDING binding obligation, not a binding that already exists.

    The downstream identities (evaluation.adoption_reconciliation, release_id) are not built yet,
    so there is no binding to prove — only an obligation to record and later ratchet. This test
    asserts the obligation is well-formed and marked pending; it deliberately does NOT assert a
    binding exists. When those tables land, `binding` flips to `bound` and this test tightens.
    """
    assert "signal_routing.yaml" in POLICY_INPUTS
    for name, spec in POLICY_INPUTS.items():
        assert spec.get("policy_version"), f"{name} names no policy version"
        assert spec.get("binds_into"), f"{name} names no downstream identity to bind into"
        assert spec.get("binding") == "pending", (
            f"{name}: until reconciliation/releases land, the binding is an obligation, not a "
            "fact. Ratchet this to 'bound' only when the downstream table is implemented."
        )


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


# --- collision-free encoding (finding 1, second pass) ----------------------------


def test_non_string_mapping_keys_are_rejected():
    """A non-string key would otherwise be coerced so `{1: x}` and `{"1": x}` collide."""
    with pytest.raises(TypeError):
        canonical_json({1: "x"})
    # And the reproduction is genuinely closed: the string-keyed form still serializes.
    assert canonical_json({"1": "x"})


def test_tuples_are_rejected_so_they_cannot_collide_with_lists():
    """A tuple would otherwise serialize as an array, colliding `(1, 2)` with `[1, 2]`."""
    with pytest.raises(TypeError):
        canonical_json((1, 2))
    with pytest.raises(TypeError):
        canonical_json({"k": (1, 2)})
    # The list form is accepted; only the ambiguous tuple is refused.
    assert canonical_json({"k": [1, 2]})


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


# --- fail-closed on a dirty tracked worktree (finding 2) -------------------------


def test_dirty_declaration_file_is_detected(tmp_path):
    """A dirty declaration file makes the worktree unclean."""
    repo = _tiny_repo(tmp_path)
    assert tracked_worktree_is_clean(repo) is True
    (repo / "sources" / "x.yaml").write_text("a: 2\n", encoding="utf-8")
    assert tracked_worktree_is_clean(repo) is False


def test_dirty_identity_implementation_is_detected(tmp_path):
    """A dirty NON-sources tracked file (the identity implementation) is refused too.

    This is the gap the sources/-only check missed: dirty identity code changes the computed id
    while source_git_sha still names HEAD. The cleanliness probe must cover it.
    """
    repo = _tiny_repo(tmp_path)
    assert tracked_worktree_is_clean(repo) is True
    (repo / "impl.py").write_text("# identity implementation CHANGED\n", encoding="utf-8")
    assert tracked_worktree_is_clean(repo) is False


def test_untracked_files_do_not_make_the_worktree_dirty(tmp_path):
    """An untracked file is not read by the computation and must not block a reproducible id."""
    repo = _tiny_repo(tmp_path)
    (repo / "scratch.txt").write_text("ignore me\n", encoding="utf-8")
    assert tracked_worktree_is_clean(repo) is True


def test_resolve_fails_closed_on_a_dirty_worktree(monkeypatch):
    """With any tracked file dirty, resolve() raises rather than emit an unreproducible id."""
    monkeypatch.setattr(dv, "tracked_worktree_is_clean", lambda *a, **k: False)
    with pytest.raises(DirtyWorktreeError):
        resolve()


def test_resolve_allow_dirty_opt_in_returns_a_diagnostic_value(monkeypatch):
    """The explicit opt-in returns a value and records that the tree was dirty."""
    monkeypatch.setattr(dv, "tracked_worktree_is_clean", lambda *a, **k: False)
    info = resolve(allow_dirty=True)
    assert info["worktree_clean"] is False
    assert len(info["declaration_version_id"]) == 64


def test_resolve_clean_path_succeeds(monkeypatch):
    """On a clean tree resolve() returns the full component set without opt-in.

    Cleanliness is forced rather than assumed: during development the real worktree carries the
    very changes under test, so asserting against live git state would be flaky. The digest and
    SHA are still computed over the real repo.
    """
    monkeypatch.setattr(dv, "tracked_worktree_is_clean", lambda *a, **k: True)
    info = resolve()
    assert info["worktree_clean"] is True
    assert len(info["declaration_version_id"]) == 64
    assert len(info["source_content_digest"]) == 64


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
