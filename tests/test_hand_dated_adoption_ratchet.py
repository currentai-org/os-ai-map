"""Hand-dated adoption axes on a machine-measured route are listed, and the list may only shrink.

`check_verification` refuses an `adoption.last_verified` without `derived_from` wherever the
product's applicable route is one the scheduled reconciliation measures: only
`build/adoption_freshness.py` may date such an axis (`docs/reference/evidence-and-freshness.md`,
"How an adoption date is earned"). The axes hand-dated before that check are grandfathered in
`sources/allowlists/hand_dated_adoption.txt`, slug and date. The gate itself catches a new one;
this file keeps the list honest, so it cannot rot into a standing exemption.
"""

from __future__ import annotations

import pytest

from build.adoption_freshness import DERIVATION_FIELD, HAND_DATED_PATH, hand_dated_allowlist
from build.check_verification import ROOT, load, machine_routed_adoption
from build.vocabulary import parse_date


@pytest.fixture(scope="module")
def corpus():
    scores, categories, _ = load()
    return scores, machine_routed_adoption(scores, categories)


def hand_dated(scores, routed) -> set[str]:
    out = set()
    for slug in routed:
        block = scores[slug].get("adoption") or {}
        claimed = parse_date(block.get("last_verified"))
        if claimed is not None and block.get(DERIVATION_FIELD) is None:
            out.add(f"{slug}|{claimed.isoformat()}")
    return out


def test_every_line_still_describes_a_hand_dated_machine_routed_axis(corpus):
    """When the axis is dated from a run, re-dated by hand or held, its line goes."""
    stale = sorted(hand_dated_allowlist() - hand_dated(*corpus))
    assert not stale, (
        f"{len(stale)} line(s) in {HAND_DATED_PATH} no longer describe a hand-dated adoption axis "
        "on a machine-measured route. Delete them:\n  " + "\n  ".join(stale)
    )


def test_every_hand_dated_machine_routed_axis_is_listed(corpus):
    """The same check `check_verification` makes, restated as data."""
    new = sorted(hand_dated(*corpus) - hand_dated_allowlist())
    assert not new, (
        f"{len(new)} adoption axis/axes carry a hand-written date on a route the scheduled "
        "reconciliation measures. Drop the date and hold the axis with settled_by: "
        "scheduled_reconciliation:\n  " + "\n  ".join(new)
    )


def test_the_list_is_sorted_and_has_no_duplicates():
    lines = [
        line.strip()
        for line in (ROOT / HAND_DATED_PATH).read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert lines == sorted(set(lines))
