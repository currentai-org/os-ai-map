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

**An attested edge dates itself.** The rule above binds the dependent's *whole-axis* date to the
root's *whole-axis* date, and those are two different claims about two different products. As the
corpus grows, every new product's natural root is older than the product, so the comparison graph
stops growing at the periphery (#436). A product may instead record `capability.comparison`: the
date the spacing itself was last judged, and the read of the root that judged it. That record
carries its own freshness requirements — a source read on or after the date, with a fetch behind
it — and in exchange the root's axis date no longer bounds the dependent's. What it does not do is
let a spacing be reaffirmed on unchanged bytes: a comparison can go false with nothing changing on
either product, because the falsifier is a third product.

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
        comparison = block.get("comparison") or {}
        if comparison:
            problems.extend(_attestation_problems(slug, target, comparison, claimed))
            continue

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


def _attestation_problems(
    slug: str, target: str, comparison: dict, claimed: date | None
) -> list[str]:
    """What an attested edge must satisfy to stand on its own date.

    The attestation is what lets a band be placed against a peer the corpus last confirmed
    weeks ago. That is only sound if the date rests on a real read of the root, so the
    requirements mirror `check_verification`'s two: the date needs a source `accessed` on or
    after it, and that source needs a fetch to point at. Without them the mechanism becomes a
    way to write a fresher date for less reading, which is the failure the whole apparatus
    exists to prevent.

    What is deliberately NOT here: the root's own `capability.last_verified`. Freeing the
    dependent from it is the point. Where the root has since been re-read, `stale_attestations`
    reports the edge for re-judgment rather than failing it.
    """
    problems: list[str] = []
    attested = parse_date(comparison.get("last_attested"))
    if attested is None:
        # The schema requires it. Repeated here for the same reason the half-a-comparison
        # check is: a gate that assumes another gate ran passes silently when it did not.
        return [
            f"{slug}:capability: records a comparison against {target} with no last_attested, "
            f"so nothing dates the spacing"
        ]

    if claimed is not None and claimed > attested:
        problems.append(
            f"{slug}:capability: claims last_verified {claimed}, but the comparison against "
            f"{target} was attested {attested}. `relative_to` and `relation` are part of this "
            f"axis's score, so a whole-axis confirmation cannot outrun one of its parts"
        )

    sources = [s for s in (comparison.get("sources") or []) if isinstance(s, dict)]
    covering = [s for s in sources if (parse_date(s.get("accessed")) or date.min) >= attested]
    if not covering:
        problems.append(
            f"{slug}:capability: attests the comparison against {target} on {attested}, but no "
            f"attestation source was read on or after that date. The date rests on nothing"
        )
        return problems

    for source in covering:
        missing = [k for k in ("http_status", "content_sha256") if not source.get(k)]
        if missing:
            problems.append(
                f"{slug}:capability: the attestation source {source.get('url')!r} carries the "
                f"{attested} date but records no {' or '.join(missing)}. A claimed confirmation "
                f"needs a fetch to point at"
            )
    return problems


def stale_attestations(scores: dict) -> list[tuple[str, str, date, date]]:
    """(dependent, root, attested, root confirmed) for every edge the root has outrun.

    Report-only, and the queue this mechanism exists to make visible. The root has been
    re-read since the spacing was judged, so the judgment may rest on a description that has
    since moved. The arithmetic check already fires when the root's SCORE moves; this catches
    the case where its `value` moved and its score did not, which is exactly what `openhands`
    turned out to have done under 25 dependent bands.
    """
    out: list[tuple[str, str, date, date]] = []
    for slug, doc in sorted(scores.items()):
        block = doc.get("capability") or {}
        target = block.get("relative_to")
        comparison = block.get("comparison") or {}
        if not target or not comparison:
            continue
        attested = parse_date(comparison.get("last_attested"))
        root_date = parse_date(((scores.get(target) or {}).get("capability") or {}).get("last_verified"))
        if attested and root_date and attested < root_date:
            out.append((slug, target, attested, root_date))
    return out


#: A comparison root has to be substantive, not merely present. A null check alone would let the
#: defect mutate into `value: TBD`, so placeholders are named and rejected.
_PLACEHOLDERS = frozenset({
    "tbd", "todo", "unknown", "n/a", "na", "none", "-", "?", "tbc", "pending", "xxx",
    "placeholder", "fixme", "wip", "see note", "as above", "same",
})

#: A prose floor applies ONLY to `feature_matrix`, where the value is a description and a
#: one-word answer says nothing. It must NOT apply to `benchmark`, where the value is an exact
#: observation and `SWE-bench Verified: 74.9` is complete at 24 characters. 63 records already
#: record a benchmark basis, so a blanket length rule would manufacture false weak roots as
#: those values are filled in.
_MIN_PROSE_VALUE = 40


def weak_roots(scores: dict) -> list[tuple[str, int, list[str]]]:
    """(peer, dependents, defects) for every product other bands are placed against.

    Why this exists. On 2026-08-31 `langfuse` was named by 22 records and `openhands` by 25,
    and NEITHER recorded a capability `value`. The arithmetic invariant above held on all 47 of
    those bands - a `one_below` against a 4 really was a 3 - so the gate was green while the
    thing being compared to was unstated. A reader could check the subtraction and not the
    claim, which is the difference between consistent and correct.

    A root is weak when its own capability has no score, no substantive `value`, or no evidence
    behind it. All three matter: a null score makes the arithmetic meaningless, an empty or
    placeholder `value` leaves "one below X" pointing at nothing, and an unsourced value is an
    assertion the next reader cannot re-open. Fan-out is reported so remediation is ordered by
    how many bands rest on each root rather than alphabetically.

    What "substantive" means depends on the instrument, and getting that wrong manufactures
    false findings. A `feature_matrix` value is a description, so a one-word answer says
    nothing and a prose floor applies. A `benchmark` value is an exact observation, and
    `SWE-bench Verified: 74.9` is complete at 24 characters - applying the prose floor there
    would report a perfectly good root as weak.
    """
    dependents: dict[str, list[str]] = {}
    for slug, doc in scores.items():
        target = (doc.get("capability") or {}).get("relative_to")
        if target:
            dependents.setdefault(target, []).append(slug)

    weak: list[tuple[str, int, list[str]]] = []
    for peer, users in dependents.items():
        block = (scores.get(peer) or {}).get("capability") or {}
        defects = []
        if block.get("score") is None:
            defects.append("no capability score")
        value = (block.get("value") or "").strip()
        if not value:
            defects.append("no capability value")
        elif value.lower().rstrip(".").strip() in _PLACEHOLDERS:
            defects.append(f"value is a placeholder ({value!r})")
        elif block.get("basis") == "feature_matrix" and len(value) < _MIN_PROSE_VALUE:
            defects.append(
                f"feature_matrix value is {len(value)} characters, under the "
                f"{_MIN_PROSE_VALUE}-character prose floor"
            )
        if not (block.get("sources") or []):
            defects.append("capability carries no sources")
        if defects:
            weak.append((peer, len(users), defects))
    return sorted(weak, key=lambda row: -row[1])


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

    attested = sum(
        1
        for d in scores.values()
        if (d.get("capability") or {}).get("relative_to")
        and (d.get("capability") or {}).get("comparison")
    )
    print(
        f"  {recorded} comparison(s) recorded, {attested} attested, {recorded - attested} "
        f"resting on their root's axis date"
    )

    outrun = stale_attestations(scores)
    if outrun:
        print(f"\n  {len(outrun)} attested comparison(s) their root has been re-read since:")
        for dep, root, when, root_date in outrun:
            print(f"    ~ {dep} at {root}: attested {when}, {root} re-confirmed {root_date}")
        print("    The spacing may rest on a description that has since moved. Report-only;")
        print("    re-judge the edge and re-attest it.")

    roots = weak_roots(scores)
    if roots:
        resting = sum(n for _, n, _ in roots)
        print(f"\n  {len(roots)} weak comparison root(s), carrying {resting} dependent band(s):")
        for peer, n, defects in roots:
            print(f"    ~ {peer}: weak comparison root - {n} dependent(s) - {'; '.join(defects)}")
        print("    A dependent band is checkable for arithmetic and not for correctness while its")
        print("    root is unstated. Report-only; see the note in weak_roots().")

    if args.candidates:
        backlog = candidates(scores, owner)
        print(f"\n  {len(backlog)} unrecorded comparison(s), the curation backlog:")
        for line in backlog:
            print(f"    - {line}")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
