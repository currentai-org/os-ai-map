"""The capability axis's gates: a recorded comparison must be consistent, and must be fresh.

`docs/reference/evidence-and-freshness.md` is normative. This module implements what that guide says about
capability, and where the two disagree the guide wins.

## Why this exists

Openness earned its gates by making the thing the score rests on into data. Its win was not
`components` in itself, it was that a judgment became a recorded structure, attributable to a
source and walkable by a ladder.

Capability's scores rest on something else, and the corpus says so plainly: measured on
2026-08-08, 79 of 472 products sit at capability 5 and roughly a hundred place themselves
against a named peer in the same category — "one tier below the Megatron-LM anchor", "not the
frontier multi-node-scale anchor". That comparison IS the instrument for most of the axis. It
lived in an English sentence, so nothing could check it, nothing refreshed it, and nothing
noticed when the product it referred to moved.

`relative_to` and `relation` record it. This module then asks the three questions that a
recorded comparison makes answerable and a sentence never did.

## The three checks

**Consistency.** If a product records `relative_to: megatron-lm, relation: one_below`, then its
score must be exactly one below Megatron-LM's. This is the direct analogue of the
producible-pair check: the recorded relation and the recorded scores are two statements of the
same fact, and they can disagree. Unlike the openness ladder it needs no rubric, because
arithmetic over two integers is the whole rule.

**Same category.** A band is placed against a peer, and a peer is something in the same
category. A cross-category comparison is not obviously wrong, but it is never what the notes
are doing, and allowing it silently would let the anchor graph sprawl into a ranking of the
whole map.

**Transitive freshness.** A confirmation of a derived band cannot be more recent than the
confirmation of the band it derives from. If Megatron-LM's capability was last confirmed in
June and `trl` claims today, `trl` is claiming to have re-derived a comparison against a fact
nobody re-read. This is the structural analogue of the openness invariant, which is why it is
worth the trouble: it is the same insight, that a date is only as good as the least recently
confirmed thing underneath it.

## What this does NOT do

It does not make capability derivable, and it produces no score from evidence. The comparison
remains a judgment with no cited source behind it. It converts an unfalsifiable claim into a
falsifiable one and gives it a freshness dependency — the same thing `establishes` did for
openness, which also does not verify that a source says what it claims. The sampled re-fetch
does that.

## Why it ratchets

The three checks apply only to products that record `relative_to`, which is a minority today
and grows as the axis is curated. The gate therefore covers exactly what has been done and
never blocks progress, which is how the openness gates were landed and the only way one gets
adopted mid-corpus. `--candidates` reports the products that look like they should carry the
field and do not; that number is the backlog, and it is reported rather than failed so that a
curation job cannot masquerade as a regression.

Usage:
    uv run python -m build.check_capability
    uv run python -m build.check_capability --candidates
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml

from build.vocabulary import parse_date

ROOT = Path(__file__).resolve().parents[1]

# `at` is not redundant with "no relation recorded". It says the placement was made by
# comparison and landed level, which is a different claim from never having compared.
DELTA = {"at": 0, "one_below": -1, "two_below": -2, "one_above": 1}

# Comparative language, for the candidate report only. Deliberately loose: a false positive
# costs a reader ten seconds and a false negative hides exactly the case this exists to find.
COMPARATIVE = re.compile(
    r"\b(one tier|two tiers|a tier|tier below|tier above|anchor|reference point|"
    r"on par|par with|compared to|relative to|versus|vs\.?|behind|ahead of|"
    r"below the|above the|mid-tier|top-tier|best-in-class|not the frontier)\b",
    re.I,
)


def load() -> tuple[dict, dict]:
    """(scores by slug, category slug by product slug)."""
    scores = {}
    for path in sorted((ROOT / "sources" / "scores").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        if doc.get("product"):
            scores[doc["product"]] = doc
    owner = {}
    for path in sorted((ROOT / "sources" / "categories").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        for product in doc.get("products") or []:
            owner[product] = doc.get("name") or path.stem
    return scores, owner


def check(scores: dict, owner: dict) -> list[str]:
    problems: list[str] = []
    for slug, doc in sorted(scores.items()):
        block = doc.get("capability") or {}
        target = block.get("relative_to")
        relation = block.get("relation")
        if not target and not relation:
            continue
        if not target or not relation:
            # The schema's dependentRequired catches this too. Repeated here because a gate
            # that assumes another gate ran is a gate that silently passes when it does not.
            problems.append(f"{slug}:capability: records {'relation' if relation else 'relative_to'} without the other")
            continue

        if target == slug:
            problems.append(f"{slug}:capability: relative_to points at itself")
            continue
        if target not in scores:
            problems.append(f"{slug}:capability: relative_to {target!r} is not a product on the map")
            continue
        if owner.get(slug) != owner.get(target):
            problems.append(
                f"{slug}:capability: relative_to {target!r} is in {owner.get(target)!r}, not "
                f"{owner.get(slug)!r}. A band is placed against a peer in its own category"
            )
            continue

        other = scores[target].get("capability") or {}
        mine, theirs = block.get("score"), other.get("score")
        if mine is None or theirs is None:
            problems.append(
                f"{slug}:capability: {relation} {target}, but "
                f"{'this score' if mine is None else f'{target}'} is null, so the relation "
                f"asserts nothing"
            )
            continue
        expected = theirs + DELTA[relation]
        if not 1 <= expected <= 5:
            # The relation cannot be satisfied by any legal band, so it is wrong regardless of
            # what this product scores. `one_above` a 5 is the case that turns up in practice.
            problems.append(
                f"{slug}:capability: records {relation} {target} ({theirs}), which needs a band "
                f"of {expected}. The scale stops at 1 and 5, so no score satisfies it"
            )
        elif mine != expected:
            problems.append(
                f"{slug}:capability: records {relation} {target} ({theirs}), which is {expected}, "
                f"but the score is {mine}. The relation and the scores disagree"
            )

        claimed = parse_date(block.get("last_verified"))
        if claimed is None:
            continue
        anchor_date = parse_date(other.get("last_verified"))
        if anchor_date is None:
            problems.append(
                f"{slug}:capability: claims last_verified {claimed} while its comparison "
                f"{target} carries no confirmation at all. A derived band cannot be fresher "
                f"than what it derives from"
            )
        elif anchor_date < claimed:
            problems.append(
                f"{slug}:capability: claims last_verified {claimed}, but {target} was last "
                f"confirmed {anchor_date}. The comparison was not re-derived"
            )
    return problems


def candidates(scores: dict, owner: dict) -> list[str]:
    """Products whose note compares them to a same-category peer without recording it."""
    found: list[str] = []
    for slug, doc in sorted(scores.items()):
        block = doc.get("capability") or {}
        if block.get("relative_to"):
            continue
        text = f"{block.get('note') or ''} {block.get('value') or ''}"
        if not COMPARATIVE.search(text):
            continue
        for peer in scores:
            if peer == slug or owner.get(peer) != owner.get(slug):
                continue
            if re.search(rf"\b{re.escape(peer.replace('-', '[- ]'))}\b", text, re.I):
                found.append(f"{slug}:capability: note compares against {peer}, unrecorded")
                break
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates", action="store_true", help="also list the unrecorded comparisons"
    )
    args = parser.parse_args()

    scores, owner = load()
    problems = check(scores, owner)
    recorded = sum(1 for d in scores.values() if (d.get("capability") or {}).get("relative_to"))

    status = "OK" if not problems else "FAIL"
    print(f"capability-anchors  a recorded comparison that does not hold  [{status}]")
    for problem in problems:
        print(f"  ! {problem}")
    print(f"  {recorded} of {len(scores)} products record a comparison")

    if args.candidates:
        backlog = candidates(scores, owner)
        print(f"\n  {len(backlog)} unrecorded comparison(s), the curation backlog:")
        for line in backlog:
            print(f"    - {line}")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
