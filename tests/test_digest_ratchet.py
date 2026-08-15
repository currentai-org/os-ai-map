"""The undigested-source backlog may shrink and may not grow.

A source with no `content_sha256` cannot be re-fetched, so `check_refetch` — the only gate in
this repo that goes and looks — is blind to it. `check_verification` requires a digest on any
source backing a *claimed date*, which is the right scope for a gate that has to be clearable
inside one PR, and it leaves a tail behind.

Measured 2026-08-15 the tail is 319 of 2,722 sources, and its shape is the reason this is a
ratchet rather than a sweep:

    accessed 2026-06  296
    accessed 2026-07   18
    accessed 2026-08    5

It is one pre-sweep cohort, not ongoing drift. August discipline is running better than 99%,
so the discipline does not need a gate — it needs something that stops the cohort growing back
while it is worked off category by category. Re-fetching 296 URLs and hand-authoring 296
`shows` extracts in one pass is exactly the rubber-stamping `check_refetch` exists to catch;
`docs/workflows/refresh-category.md` drives it properly, one category per PR.

**When you clear some, lower the budget in the same PR.** That is the whole mechanism. The
idiom is `tests/test_openness_buckets.py`'s `KNOWN_VIOLATIONS`: an explicit list of what is
wrong today, which fails if it stops being accurate in either direction.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
AXES = ("openness", "adoption", "capability")

# Lower this when a refresh pass digests some. It must never be raised: a new undigested
# source is a new source somebody cited without fetching, which is the thing being ratcheted.
BUDGET = 319


def undigested() -> list[tuple[str, str, str]]:
    """(slug, axis, url) for every cited source carrying no content digest."""
    out = []
    for path in sorted((REPO / "sources" / "scores").glob("*.yaml")):
        score = yaml.safe_load(path.read_text()) or {}
        for axis in AXES:
            for source in ((score.get(axis) or {}).get("sources") or []):
                if not source.get("content_sha256"):
                    out.append((path.stem, axis, source.get("url", "?")))
    return out


@pytest.fixture(scope="module")
def tail():
    return undigested()


def test_the_undigested_tail_does_not_grow(tail):
    assert len(tail) <= BUDGET, (
        f"{len(tail)} undigested sources, over the budget of {BUDGET}. A new one means a "
        "source was cited without being fetched through build.fetch_source. Digest it, or "
        "cite nothing.\nNewest offenders:\n  "
        + "\n  ".join(f"{s}.{a} {u}" for s, a, u in tail[-5:])
    )


def test_the_budget_is_not_slack(tail):
    """A budget far above the real count stops ratcheting. Keep it within 10 of the truth."""
    assert len(tail) > BUDGET - 10, (
        f"only {len(tail)} undigested sources against a budget of {BUDGET} — lower BUDGET to "
        f"{len(tail)} so the ratchet keeps biting."
    )


def test_the_tail_is_still_one_legacy_cohort(tail):
    """If August starts contributing, this is drift and not a backlog, which changes the fix.

    The claim in this module's docstring is that the discipline holds and only the history is
    dirty. That claim has to be checked, or it becomes a comforting sentence nobody re-measured.
    """
    by_month: Counter = Counter()
    for path in sorted((REPO / "sources" / "scores").glob("*.yaml")):
        score = yaml.safe_load(path.read_text()) or {}
        for axis in AXES:
            for source in ((score.get(axis) or {}).get("sources") or []):
                if not source.get("content_sha256"):
                    by_month[str(source.get("accessed"))[:7]] += 1
    recent = sum(n for month, n in by_month.items() if month >= "2026-08")
    assert recent < 40, (
        f"{recent} undigested sources accessed since 2026-08 — the tail is growing rather than "
        f"draining, so it is drift and not a legacy cohort. Distribution: {dict(by_month)}"
    )
