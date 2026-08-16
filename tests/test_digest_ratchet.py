"""Every newly cited source carries a digest. The legacy tail is listed, and may only shrink.

A source with no `content_sha256` cannot be re-fetched, so `check_refetch` — the only gate in
this repo that goes and looks — is blind to it. `check_verification` requires a digest on any
source backing a *claimed date*, which is the right scope for a gate that has to be clearable
inside one PR, and it leaves a tail behind.

**A count budget was the first cut, and it was too weak.** It caps the total, so a pass could
digest one old source while citing a new undigested one and the number would not move — which
is exactly the case the invariant is supposed to forbid. `sources/allowlists/undigested_sources.txt` lists
the tail entry by entry instead. Anything not on the list must carry a digest, so a newly
cited source without a fetch fails on the first assertion rather than being absorbed.

The list is grandfathering, not permission. Measured 2026-08-15 it holds 293 entries — 319
before the 26 placeholder sources repaired in this same change — and its shape is why the
remedy is a ratchet rather than a sweep:

    accessed 2026-06  270
    accessed 2026-07   18
    accessed 2026-08    5

One pre-sweep cohort, with the discipline now running better than 99%. Re-fetching 270 URLs
and hand-authoring 270 `shows` extracts in one pass is exactly the rubber-stamping
`check_refetch` exists to catch; `docs/workflows/refresh-category.md` drives it properly, one
category per PR. **When a pass digests a source, delete its line.** A line that no longer
describes an undigested source fails too, so the list cannot rot into a standing exemption.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
AXES = ("openness", "adoption", "capability")
ALLOWLIST = REPO / "sources" / "allowlists" / "undigested_sources.txt"


def undigested() -> set[str]:
    """`slug|axis|url` for every cited source carrying no content digest."""
    out = set()
    for path in sorted((REPO / "sources" / "scores").glob("*.yaml")):
        score = yaml.safe_load(path.read_text()) or {}
        for axis in AXES:
            for source in ((score.get(axis) or {}).get("sources") or []):
                if not source.get("content_sha256"):
                    out.add(f"{path.stem}|{axis}|{source.get('url', '?')}")
    return out


def allowlisted() -> set[str]:
    return {
        line.strip()
        for line in ALLOWLIST.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }


@pytest.fixture(scope="module")
def tail():
    return undigested()


@pytest.fixture(scope="module")
def allowed():
    return allowlisted()


def test_a_newly_cited_source_carries_a_digest(tail, allowed):
    """The invariant. Not "the total did not grow" — this one."""
    new = sorted(tail - allowed)
    assert not new, (
        f"{len(new)} source(s) cited with no content_sha256 and not in the legacy tail. Only "
        "build.fetch_source produces a digest, and only an actual fetch produces one — cite "
        "nothing rather than citing something nobody opened:\n  " + "\n  ".join(new)
    )


def test_the_allowlist_does_not_rot(tail, allowed):
    """A line that no longer describes an undigested source is stale and must be deleted.

    Without this the list would silently become a permanent exemption: entries would survive
    the sources they described, and a future undigested source at the same slug/axis/url
    would be waved through by a line nobody meant to keep.
    """
    stale = sorted(allowed - tail)
    assert not stale, (
        f"{len(stale)} allowlist line(s) no longer describe an undigested source. Delete "
        "them — the source was digested or removed:\n  " + "\n  ".join(stale)
    )


def test_the_tail_is_still_one_legacy_cohort():
    """If recent accesses start contributing, this is drift rather than a backlog.

    The docstring's claim is that the discipline holds and only the history is dirty. That
    claim has to be re-measured, or it becomes a comforting sentence nobody checked. The
    threshold is deliberately close to the current 5: the allowlist is what enforces the
    invariant, and this is the canary on the story told about it.
    """
    by_month: dict[str, int] = {}
    for path in sorted((REPO / "sources" / "scores").glob("*.yaml")):
        score = yaml.safe_load(path.read_text()) or {}
        for axis in AXES:
            for source in ((score.get(axis) or {}).get("sources") or []):
                if not source.get("content_sha256"):
                    month = str(source.get("accessed"))[:7]
                    by_month[month] = by_month.get(month, 0) + 1
    recent = sum(n for month, n in by_month.items() if month >= "2026-08")
    assert recent <= 10, (
        f"{recent} undigested sources accessed since 2026-08 — the tail is being added to "
        f"rather than drained, so it is drift and not a legacy cohort. Distribution: {by_month}"
    )


def test_the_allowlist_is_shrinking_ground(allowed):
    """A sanity bound. If this file ever exceeds what it was grandfathered at, something has
    been added to it rather than removed, which is the one edit it does not accept."""
    assert len(allowed) <= 293, f"{len(allowed)} entries; the tail was 293 when it was listed"
