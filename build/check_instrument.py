"""Does each adoption record have what its own instrument requires?

## The gap this closes, and why the previous gate could not see it

`check_adoption` compares a recorded `(level, reach)` against the scale its instrument
declares. It went to zero findings on 2026-08-13 and gates strict in CI. That check is about
the LABEL.

Nothing checks the INSTRUMENT. `signal_type` is a claim about how the band was read, and
`docs/guides/adoption.md` states what the claim means: "A `usage_volume` band **claims to be
a download count**." Measured 2026-08-13, **56 products claim exactly that with no artifact
any signal model can read** — 12 declare npm or crates, which no model reads, and 44 declare
nothing at all. Twelve of the 56 sit at level 5: `mcp-typescript-sdk`, `openclaw`, `langchain`,
`ray`, `firecracker`, `aws-lambda`.

Every one of them passes `check_adoption --strict` green, because `>10M` is a perfectly valid
label. The label is checkable; the claim underneath it is not. That is the same failure the
adoption sweep spent three days on, moved up one level: first labels nobody could check, now
instruments nobody could check.

It had also already been written down. `adoption.md` records the class as **48** products,
measured 2026-08-10. It is 56 now. A finding in prose grows; a finding in a gate does not.

## One rule, two ways to satisfy it

**An adoption record must be re-checkable by somebody other than its author.** There are
exactly two ways to be, and an instrument decides which is PREFERRED, never which is required:

1. **Recomputation** — the product declares an artifact of a kind some signal model reads, so
   a model can derive the number independently. Strictly the better route: it is automatic,
   and it can disagree with the recorded band.
2. **Re-fetch** — a cited source carries an `accessed` date AND a `content_sha256`, so
   `check_refetch` can pull it again and report drift.

A record failing BOTH is unfalsifiable, and that is the only thing this gate calls a finding.

The first draft of this check required route 1 for `usage_volume` outright, and its own test
caught the error. 15 of the 55 records with no readable artifact already carry a digested
source — `agent-infra-sandbox` cites `api.npmjs.org/downloads/point/last-month` showing 4,670
downloads, with a digest. That claim is perfectly checkable; it just is not re-derivable by a
pipeline that reads no npm. Failing it would have told 15 authors their careful evidence did
not count. **40 records, not 55, are genuinely unbacked.**

None of the routing is hardcoded here. `sources/signal_routing.yaml` already declares which
source feeds which `signal_type` and whether it is `bridged`; `artifact_key` (added for this
check) names what a product must declare for that source to have anything to read. Mirroring
any of it in Python is the drift `check_parity` exists to catch one axis over.

## Why the escape hatch stays closed

Without the evidence leg, any unbacked record could satisfy this gate by relabelling itself
`reported_traction` — moving an unverifiable claim into the one instrument with no scale at
all, which is strictly worse than where it started. With it, relabelling costs a dated,
digested source, and a record that already has one is legitimately re-checkable whatever its
instrument says. Measured 2026-08-13: 95 of 110 `reported_traction` records do not pay it yet.

What no gate can decide is whether a declared artifact is the product's PRIMARY channel — the
under-coverage judgment in `adoption.md`, and the reason a relabel can still be the wrong call
for honest-looking reasons.

## A known cost of route 2

A digest over a COUNT endpoint drifts every time the count moves, so `check_refetch` will
report drift that means nothing. Drift on a vendor claim page is informative; drift on
`api.npmjs.org/downloads/point/last-month` is just Tuesday. That is an argument for bridging
npm (issue #163) rather than for rejecting the evidence, and it is recorded here so the
refetch noise is a known consequence rather than a surprise.

## What this deliberately does NOT check

Whether the recorded figure is CURRENT (`check_freshness`), whether the band matches the scale
(`check_adoption`), or whether a declared artifact is the product's PRIMARY channel — that is
the under-coverage judgment in `adoption.md`, and no gate can make it.

## Exit status

0 unless `--strict`, matching `check_adoption`'s first three days. The backlog predates the
rule being written down, and a gate that fails on day one teaches people to skip it. Turn on
`--strict` once it is cleared.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]


def instrument_rules(root: Path = ROOT) -> tuple[dict[str, set[str]], dict[str, list[str]]]:
    """(signal_type -> artifact keys that satisfy it, signal_type -> required evidence fields).

    Both read straight off `sources/signal_routing.yaml`. A source counts toward an
    instrument's artifact precondition only when it is `bridged` — an unbridged route is
    declared, but nothing reads it, so declaring an npm package does not make a download
    count re-derivable. That distinction is the entire point: `mcp-typescript-sdk` declares
    an npm package and records level 5 `usage_volume`, and no model can confirm or refute it.
    """
    from build.serialize_rubric import load_routing

    routing = load_routing(root)
    sources = routing.get("sources") or {}
    routes = ((routing.get("dimensions") or {}).get("adoption") or {}).get("routes") or []

    artifacts: dict[str, set[str]] = {}
    evidence: dict[str, list[str]] = {}
    for route in routes:
        signal_type = route.get("signal_type")
        if not signal_type:
            continue
        if route.get("requires_evidence"):
            evidence[signal_type] = list(route["requires_evidence"])
        source = sources.get(route.get("source") or "") or {}
        if source.get("bridged") and source.get("artifact_key"):
            artifacts.setdefault(signal_type, set()).add(source["artifact_key"])
    return artifacts, evidence


def is_recomputable(product: dict, artifacts: set[str]) -> bool:
    """Route 1: some signal model can derive this number independently."""
    return any(product.get(key) for key in artifacts)


def is_refetchable(adoption: dict, required: list[str]) -> bool:
    """Route 2: one source carries every field needed to pull it again and compare.

    Every field must sit on the SAME source. An `accessed` date on one and a digest on
    another proves nothing about either — the pair is what makes a re-fetch comparable.
    """
    return any(
        all(src.get(field) for field in required)
        for src in adoption.get("sources") or []
    )


def collect(sources: dict, root: Path = ROOT) -> tuple[list[str], int]:
    artifacts, evidence = instrument_rules(root)
    # The evidence fields are the same for every instrument that declares them, and they are
    # what route 2 means in general, so a record on ANY instrument may satisfy the gate that
    # way. Read from routing rather than restated, and defaulted only if nothing declares it.
    refetch_fields = next(iter(evidence.values()), ["accessed", "content_sha256"])

    findings: list[str] = []
    examined = 0

    for slug, score in sorted(sources["scores"].items()):
        adoption = (score or {}).get("adoption") or {}
        signal = adoption.get("signal_type") or ""
        if adoption.get("level") is None or signal in ("", "unknown"):
            continue
        product = sources["products"].get(slug) or {}
        examined += 1

        if is_recomputable(product, artifacts.get(signal, set())):
            continue
        if is_refetchable(adoption, refetch_fields):
            continue

        if signal in artifacts:
            declared = sorted(
                k for k in ("npm", "crates", "docker") if product.get(k)
            ) or ["nothing countable"]
            findings.append(
                f"{slug}: records {signal} at level {adoption['level']}, which claims a "
                f"count, but declares {', '.join(declared)} and cites no source carrying "
                f"{' + '.join(refetch_fields)}. Declare one of {sorted(artifacts[signal])} "
                f"so a model can recompute it, or digest the source you read"
            )
        else:
            findings.append(
                f"{slug}: records {signal} at level {adoption['level']}, which can never be "
                f"recomputed, and cites no source carrying {' + '.join(refetch_fields)} — "
                f"the claim cannot be re-checked and will not age"
            )
    return findings, examined


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 on any finding")
    parser.add_argument("--verbose", action="store_true", help="print every finding")
    args = parser.parse_args()

    sources = load_sources(ROOT)
    findings, examined = collect(sources)

    # A corpus walk that silently narrows passes green. Two did, earlier in this repo.
    if examined < 300:
        print(
            f"check_instrument: only examined {examined} products; the walk has drifted",
            file=sys.stderr,
        )
        return 1

    shown = findings if args.verbose else findings[:15]
    for line in shown:
        print(f"  x {line}")
    if len(findings) > len(shown):
        print(f"  ... and {len(findings) - len(shown)} more (--verbose for all)")

    status = "OK" if not findings else f"{len(findings)} instruments unsupported"
    print(f"\ncheck_instrument  {examined} adoption records  [{status}]")
    return 1 if findings and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
