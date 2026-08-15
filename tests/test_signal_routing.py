"""`signal_routing.yaml` declares which machine-readable sources exist. Nothing else in the
suite checks that declaration against what products actually claim to have, so an artifact
kind can go undeclared indefinitely and every product carrying it silently falls through to
the stars fallback and its cap of 3 — no test fails, no error surfaces, the score is simply
lower than it should be.

**Inverted 2026-08-15 (#184).** The first form built its "in use" set by intersecting each
product record against a hardcoded `ARTIFACT_KINDS`, so it could only catch an undeclared kind
whose name was *already in that set* — which is the one case that cannot happen. A genuinely
new kind never entered `in_use` and the assertion passed, which is the regression the test is
nominally there to prevent. `arxiv` was the live proof: 24 products declare it and it was in
neither the set nor `sources:`.

The inverted form enumerates every top-level product key, subtracts an explicit metadata
allowlist, and requires the remainder to be declared. A new artifact kind is caught **by
default**; the allowlist is the visible thing a contributor has to edit to opt something out,
which is the right polarity.
"""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

# Top-level product keys that are NOT distribution artifacts. Everything not listed here must
# be a declared artifact kind, so adding a key to this set is a deliberate, reviewable claim
# that the thing cannot be counted — not a formality.
#
# `artifact_exceptions` is the subtle one: it is an annotation ABOUT artifacts (why
# `pymilvus`'s downloads stand in for the Milvus server, why distilabel's PyPI metadata names
# a dead org), not an artifact itself.
METADATA_KEYS = {
    "name",
    "display_name",
    "type",
    "description",
    "comments",
    "aliases",
    "lineage",
    "version_in_identity",
    "artifact_exceptions",
}


def _routing() -> dict:
    return yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())


def declared_artifact_kinds(routing: dict) -> set[str]:
    """The artifact kinds routing can name, from `artifact_key` rather than from source names.

    These are two different layers and conflating them is the mistake #184 nearly shipped.
    `arxiv` is a product ARTIFACT KEY; `semanticscholar` is the SOURCE that consumes it, and
    it declares `artifact_key: arxiv`. Reading source names would have reported `arxiv`
    undeclared and invited a duplicate `sources.arxiv` entry for something the router already
    reaches.
    """
    return {
        source["artifact_key"]
        for source in (routing.get("sources") or {}).values()
        if source.get("artifact_key")
    }


def product_keys() -> dict[str, set[str]]:
    """slug -> its top-level keys."""
    out = {}
    for path in sorted((ROOT / "sources" / "products").glob("*.yaml")):
        out[path.stem] = set(yaml.safe_load(path.read_text()) or {})
    return out


@pytest.fixture(scope="module")
def routing():
    return _routing()


def test_every_product_key_is_a_declared_artifact_kind_or_declared_metadata(routing):
    """The inverted check. A new artifact kind fails here by default."""
    declared = declared_artifact_kinds(routing)
    offenders: dict[str, set[str]] = {}
    for slug, keys in product_keys().items():
        unknown = keys - METADATA_KEYS - declared
        if unknown:
            offenders[slug] = unknown

    assert not offenders, (
        "product keys that are neither a declared artifact kind nor declared metadata:\n  "
        + "\n  ".join(f"{slug}: {sorted(keys)}" for slug, keys in sorted(offenders.items()))
        + "\n\nEither declare the source in sources/signal_routing.yaml with an `artifact_key` "
        "(use `bridged: false` if nothing reads it yet), or add the key to METADATA_KEYS with "
        "a reason."
    )


def test_arxiv_is_covered_by_the_source_that_consumes_it(routing):
    """The case that proved the old form was blind, pinned so it cannot regress.

    24 products declare `arxiv`, and it is covered because `semanticscholar` declares it as
    its `artifact_key` — a source may consume a key that shares no name with it. That
    mapping is the invariant.

    What this deliberately does NOT assert is that no source may ever be *named* `arxiv`.
    An earlier draft did, and it froze today's topology: a direct arXiv signal alongside
    Semantic Scholar is a perfectly legitimate future route, and a test forbidding it would
    have made the right change look like a regression.
    """
    sources = routing.get("sources") or {}
    assert "arxiv" in declared_artifact_kinds(routing), (
        "24 products declare arxiv; some source must declare it as an artifact_key"
    )
    assert sources.get("semanticscholar", {}).get("artifact_key") == "arxiv", (
        "semanticscholar is what reaches arxiv today; if that changes, the replacement must "
        "still declare artifact_key: arxiv"
    )


def test_the_metadata_allowlist_does_not_shadow_a_declared_artifact_kind(routing):
    """An entry in both sets would silently exempt a countable artifact from the check."""
    overlap = METADATA_KEYS & declared_artifact_kinds(routing)
    assert not overlap, f"keys claimed as both metadata and artifact kinds: {sorted(overlap)}"


def test_the_allowlist_has_no_dead_entries():
    """A metadata key no product carries is an exemption nobody needs, and it accumulates.

    Kept as its own assertion rather than folded above, because a dead entry is untidy where a
    shadowed one is unsafe — the messages should not be interchangeable.
    """
    seen: set[str] = set()
    for keys in product_keys().values():
        seen |= keys
    dead = METADATA_KEYS - seen
    assert not dead, f"METADATA_KEYS entries no product carries: {sorted(dead)}"


def test_the_walk_reads_the_whole_corpus():
    """A narrowed walk passes vacuously. Two checks in this repo have done exactly that."""
    keys = product_keys()
    assert len(keys) > 400, f"only {len(keys)} product files read; the walk has drifted"


def test_declared_but_unreachable_kinds_are_visible_rather_than_absent(routing):
    """The original test's real subject, kept.

    A product may declare a kind no route can reach — npm and crates are `bridged: false`
    today — but the gap has to be declared rather than silent. That is what turns 13 products
    falling through to the stars cap into a backlog entry instead of an invisible loss.
    """
    sources = routing.get("sources") or {}
    for name in ("npm", "crates"):
        assert name in sources, f"{name} is used by products and must be declared"
        assert "bridged" in sources[name], f"{name} must state whether anything reads it"
