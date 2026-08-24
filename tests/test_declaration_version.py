"""The declaration-version identity, and the properties that keep it honest.

`build/declaration_version.py` derives `declaration_version_id` (data-architecture.md §4.6):
the identity of a set of declarations, evaluated by a named evaluator, that
`registry.axis_assessments`, `evaluation.product_adoption_measurements` and
`evaluation.adoption_reconciliation` all key on.

There is no committed golden value to pin — the id embeds `source_git_sha`, and freezing a
receipt would either name its own parent commit or force a regenerate step on every score edit
(see the module docstring). So these tests pin the canonicalization's PROPERTIES instead:
determinism, order-invariance, the exact digested key-set, the exclusions, the sentinel, and
that the id responds to each component.
"""

import copy
import hashlib
from pathlib import Path

import build.declaration_version as dv
from build.declaration_version import (
    CANONICALIZATION_VERSION,
    DECLARATION_KEYS,
    EVALUATOR_VERSION,
    NON_DECLARATION_KEYS,
    canonical_json,
    declaration_content,
    declaration_version_id,
    source_content_digest,
)
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]


def test_declaration_keys_cover_every_declaration_subtree():
    """The digested key-set must be load_sources MINUS the declared non-declarations, exactly.

    This is the 'declared state matches reality' gate for the identity: add a new declaration
    directory to sources/ (so load_sources grows a key) and this fails until the key is either
    folded into the digest or explicitly classified a non-declaration. A declaration cannot
    slip out of the version unnoticed.
    """
    exposed = set(load_sources(ROOT))
    classified = set(DECLARATION_KEYS) | set(NON_DECLARATION_KEYS)
    assert exposed == classified, (
        f"load_sources exposes {sorted(exposed)}, but the identity classifies "
        f"{sorted(classified)}; every key must be a declaration or a declared exclusion."
    )
    # The two partitions must not overlap: a key is a declaration xor an exclusion.
    assert not (set(DECLARATION_KEYS) & set(NON_DECLARATION_KEYS))


def test_long_tail_is_excluded_from_the_declaration_content():
    """The frozen warehouse sample is a non-declaration and never enters the digest."""
    assert "long_tail" in NON_DECLARATION_KEYS
    assert "long_tail" not in DECLARATION_KEYS
    content = declaration_content(ROOT)
    assert set(content) == set(DECLARATION_KEYS)
    assert "long_tail" not in content


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
    # Rebuild the top-level mapping in reverse key order.
    shuffled = {k: shuffled[k] for k in reversed(list(shuffled))}
    assert hashlib.sha256(canonical_json(shuffled).encode("utf-8")).hexdigest() == baseline


def test_evaluator_version_is_the_declared_sentinel():
    """The Phase-6 evaluator does not exist yet; the component is a deliberate sentinel, not ''.

    Pinned so that the day a real evaluator version replaces it is a deliberate, reviewed change
    (every historical declaration_version_id moves with it) rather than an accident.
    """
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
