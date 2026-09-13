"""The instrument's own precondition, and the escape hatch it has to close.

`check_adoption` gates the label. These gate the claim underneath it. See
`build/check_instrument.py` for why the two counting instruments and the two claiming ones
need different things.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from build.check_instrument import collect, instrument_rules
from build.validate import load_sources


@pytest.fixture(scope="module")
def sources():
    return load_sources(Path("."))


def test_the_rules_are_read_from_routing_and_not_mirrored_in_python():
    """Every precondition traces to `sources/signal_routing.yaml`.

    The checker deliberately has no opinion of its own about which sources exist. Mirroring
    that list in Python is the hand-copied-logic drift `check_parity` exists to catch one
    axis over, and this repo has hit it four times.
    """
    artifacts, evidence = instrument_rules()

    # Counting instruments resolve to the artifact keys a product must declare.
    # npm and crates joined this set on 2026-09-13 when signal_packages.downloads
    # bridged all three package registries (#562 step 3).
    assert artifacts["usage_volume"] == {
        "pypi", "npm", "crates", "huggingface_model", "huggingface_dataset", "arxiv",
    }
    assert artifacts["stars_fallback"] == {"github"}

    # The two that can never be recomputed have no artifact rule and an evidence rule instead.
    assert "active_users" not in artifacts and "reported_traction" not in artifacts
    assert evidence["reported_traction"] == ["accessed", "content_sha256"]
    assert evidence["active_users"] == ["accessed", "content_sha256"]


def test_an_unbridged_source_does_not_satisfy_recomputation(tmp_path):
    """A declared artifact on an UNBRIDGED route does not make a count RE-DERIVABLE.

    This is the distinction the whole check rests on: the route exists, nothing reads it, so
    the recorded number can be neither confirmed nor refuted by the pipeline.

    Written against a synthetic routing file rather than the live one, deliberately. It used
    to assert `"npm" not in artifacts["usage_volume"]`, which was true only while npm happened
    to be unbridged; bridging it on 2026-09-13 broke the test without touching the invariant
    it exists to protect. A gate keyed to whichever source is currently unmeasured will keep
    failing for the good news. This version tests the rule.

    The history is worth keeping. While npm was unbridged, 11 of the then-13 npm products
    recorded `usage_volume` rather than falling through to the stars cap, `mcp-typescript-sdk`
    and `openclaw` at level 5 — an unbridged route does not produce a capped band, it produces
    an unfalsifiable one. They were still re-CHECKABLE by re-fetch, which is the correction
    that reshaped this gate: route 1 was closed to them and route 2 was open, and the gate
    cares only that one of the two is.
    """
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "signal_routing.yaml").write_text(
        "sources:\n"
        "  measured:\n"
        "    artifact_key: measured_kind\n"
        "    bridged: true\n"
        "  unmeasured:\n"
        "    artifact_key: unmeasured_kind\n"
        "    bridged: false\n"
        "dimensions:\n"
        "  adoption:\n"
        "    routes:\n"
        "    - signal_type: usage_volume\n"
        "      source: measured\n"
        "    - signal_type: usage_volume\n"
        "      source: unmeasured\n",
        encoding="utf-8",
    )
    artifacts, _ = instrument_rules(tmp_path)
    assert artifacts["usage_volume"] == {"measured_kind"}
    assert "unmeasured_kind" not in artifacts["usage_volume"]
    assert "crates" not in artifacts["usage_volume"]


def test_relabelling_to_reported_traction_does_not_buy_a_pass(sources):
    """The escape hatch, closed.

    Without an evidence precondition, any `usage_volume` record with nothing countable behind
    it could satisfy this gate by editing one field — landing in the one instrument with no
    scale at all, where nothing checks its level either. That would move an unverifiable claim
    somewhere strictly less checked and call it a fix.

    Asserted by construction rather than by counting: take a record the gate actually fails,
    relabel it the way a lazy fix would, and confirm it still fails.

    Note what is NOT claimed. A record that already carries a dated, digested source may
    legitimately record `reported_traction`, and 15 of the unrouted `usage_volume` records do
    carry one. Whether such a record SHOULD relabel rather than declare its artifact is the
    primary-channel judgment in `adoption.md`, which no gate can make.
    """
    # BUILD the offender rather than borrowing one from the corpus. The first version of
    # this test picked a live failing record, and on 2026-08-14 the corpus ran out of them —
    # so a test asserting the gate still bites failed because the gate had done its job. A
    # test whose setup depends on the bug still existing expires the moment the bug is fixed.
    slug = next(iter(sources["scores"]))
    unbacked = {
        **sources,
        "products": {**sources["products"], slug: {"type": "software"}},
        "scores": {
            **sources["scores"],
            slug: {"adoption": {"level": 4, "signal_type": "usage_volume", "sources": []}},
        },
    }
    offenders, _ = collect(unbacked)
    assert any(f.startswith(f"{slug}:") for f in offenders), (
        "a usage_volume record with no readable artifact and no digested source should fail"
    )

    patched = {
        **unbacked,
        "scores": {
            **unbacked["scores"],
            slug: {"adoption": {"level": 4, "signal_type": "reported_traction", "sources": []}},
        },
    }
    findings, _ = collect(patched)
    assert any(f.startswith(f"{slug}:") for f in findings), (
        f"{slug} escaped the gate by relabelling itself reported_traction"
    )


def test_the_walk_covers_the_corpus(sources):
    """A corpus walk that silently narrows passes green. Two did, earlier in this repo."""
    _findings, examined = collect(sources)
    assert examined > 400, f"only examined {examined} adoption records"
