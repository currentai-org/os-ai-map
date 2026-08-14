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
    assert artifacts["usage_volume"] == {
        "pypi", "huggingface_model", "huggingface_dataset", "arxiv",
    }
    assert artifacts["stars_fallback"] == {"github"}

    # The two that can never be recomputed have no artifact rule and an evidence rule instead.
    assert "active_users" not in artifacts and "reported_traction" not in artifacts
    assert evidence["reported_traction"] == ["accessed", "content_sha256"]
    assert evidence["active_users"] == ["accessed", "content_sha256"]


def test_an_unbridged_source_does_not_satisfy_recomputation():
    """Declaring an npm package does not make a download count RE-DERIVABLE.

    This is the distinction the whole check rests on. `signal_routing.yaml` declares npm and
    crates with `bridged: false` — the route exists, nothing reads it. `mcp-typescript-sdk`
    declares an npm package and records `usage_volume` at level 5, and no model in the
    pipeline can confirm or refute that number.

    The routing file's own note used to say these products "fall through to the stars scale
    and its cap of 3", which was the comfortable reading and not what happened: 11 of the 13
    npm products record `usage_volume` instead.

    They are not thereby unfalsifiable, which is the correction that reshaped this gate. Most
    of them cite a digested npm API response and are re-checkable by re-fetch; what they are
    not is re-derivable by a pipeline that reads no npm. Route 1 is closed to them and route 2
    is open, and the gate cares only that one of the two is.
    """
    artifacts, _ = instrument_rules()
    assert "npm" not in artifacts["usage_volume"]
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
