"""The three free gates: is a claimed confirmation supported, and is a score even possible.

`docs/reference/evidence-and-freshness.md` is normative for all three. This module implements them; when
the two disagree the guide wins. `docs/workflows/refresh-category.md` has the order of
operations and why the gates land before any bulk editing of `sources/scores/`.

## The invariant

> `last_verified: D` is valid only if, for every dimension the score records, at least one
> source that `establishes` that dimension has `accessed >= D`.

**This validates a claimed date. It never derives one.** The distinction is the whole point
and it is easy to erode: the invariant mentions `accessed`, so someone will eventually
"simplify" it into `last_verified = max(accessed)`. That is issue #115 exactly, and between
#108 and #115 a derived date landed on 19 of the 26 axes that carried one, in six cases
overwriting a date a person had established by checking. Deriving the date asserts a
confirmation nobody made; validating it rejects a confirmation nobody could have made.

Note the aggregation direction, which is also load-bearing: the check is over EVERY
recorded dimension, so the binding constraint is the LEAST recently re-read one.
`max(accessed)` across an axis would pass an axis where one dimension was re-read today and
three were last seen in June — and that is not hypothetical, it is what the 2026-07-28 pass
on the model flagships produced by re-reading only the dataset endpoint.

## The one axis whose support is an observation

An adoption date may instead rest on the measurement that earned it, recorded on the axis as
`derived_from`. The invariant over `accessed` is unchanged for everything else, and this is not
a weaker test of the same thing: it asks the same question of a stronger fact. The route
re-measured the usage figure from an observation a collector fetched, with the date it was
fetched, and banded it to the level the score already records. An `accessed` on such an axis
dates a curator reading a counts endpoint, which is a number that changes daily — the reading is
real, and it is evidence of where the figure came from rather than evidence that it is current.

`build/adoption_freshness.py` owns the shape and is the only writer.
`sources/snapshots/observation_snapshots.yaml` is the other half of the record: it resolves the
recorded snapshot id to the window it observed AND carries, per product, the run, route, level
and date that run measured. So the claim is checkable here with no warehouse, and it is checked
against something other than itself — a date outside the window, a snapshot nothing recorded, a
product the ledger records no measurement for, a level the score has since left, a route the
tables do not compile, or a pair of records that disagree about one measurement.

## A hand-written adoption date where a route measures the band

The derived date is not an alternative to a reading where a route can measure the band: it is
the only way that axis is dated. Where the product's applicable route is machine-measured (an
artifact route the scheduled reconciliation reads, such as PyPI, npm or Hugging Face downloads),
an `adoption.last_verified` without `derived_from` is a curator's date on a number that moves
daily, and the fresh-source floor below would pass it. So the invariant refuses it outright and
never falls back to the floor. The repair is a hold with `settled_by: scheduled_reconciliation`,
which the first scheduled run that measures the same band releases.

Axes no scheduled run can date keep the read-based path: a deliberate null (a searched
absence, re-confirmed by re-reading the page), the hand-authored instruments
(`reported_traction`, `active_users`), which have no collector behind them, and an axis whose
applicable route measures another instrument than the one recorded, which the reconciliation
queues as a route disagreement rather than ever dating. Dating those by
reading is what the guide prescribes, and refusing it would leave them undatable.

The axes hand-dated before this rule are listed, slug and date, in
`sources/allowlists/hand_dated_adoption.txt`. It is a draining list: a line names the exact date
it grandfathers, so a new hand date on a listed product is not covered, and a line that no
longer describes a hand-dated axis fails `tests/test_hand_dated_adoption_ratchet.py`.
`build/adoption_freshness.py` deletes a product's line in the same change that dates it.

## The digest requirement — a claimed date needs a fetch to point at

Same scope. Every source read as part of the confirmation carries `http_status` and
`content_sha256`, because those are what only an actual request produces. The invariant
alone catches an unsupported date. It cannot catch a source that never said what `shows`
claims. A missing digest on a newly claimed confirmation means the tool fetched nothing.

## The producible-pair check — a score/class pair must be producible

Full scope, immediately, and unlike the invariant and the digest requirement it needs
nothing to be populated first. For every scored product in a category with a
`scoring_recipe`, `(score, class)` must be the outcome of SOME rule in that recipe.
Deliberately weaker than `build/check_rubric.py`, which asks whether the recipe reproduces
the score from the recorded evidence: producible-pairs ignores the evidence and asks only
whether the pair exists in the ladder at all. That makes it immune to the escape hatch
`check_rubric` has, which is `deferred` — a category can defer a product out of
reproduction, but an impossible pair stays impossible.

`4 / open_source` is the shape this catches and `check_rubric` cannot: no software rule emits 4
with `open_source`, since 4 is `open_core` and 5 is `open_source`, and a product deferred out of
reproduction is still checked here. The message names the pair, never the repair — which of the
two values moves is a question for the product's recorded components.

## How the gates ratchet

The invariant and the digest requirement apply only to axes carrying a `last_verified`,
which is a handful today and grows as the re-read pass proceeds. They therefore cover
exactly what has been done, never block progress, and never permit a regression on ground
already taken. A big-bang gate over all 1370 axes would fail on day one and get switched
off, which is how gates die.

Usage:
    uv run python -m build.check_verification
    uv run python -m build.check_verification --gate producible-pairs
    uv run python -m build.check_verification --verbose
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import yaml

from build.vocabulary import axes, parse_date
from build.adoption_freshness import (
    DERIVATION_FIELD,
    DERIVED_AXIS,
    HAND_DATED_PATH,
    derivation_problems,
    hand_dated_allowlist,
    known_route_ids,
)
from build.check_rubric import components_of, license_read_keys, resolve_dimension
from build.observation_snapshot import load_ledger
from build.rubrics import load_product_types, load_shared, recipe_for, resolve_recipe_variants

ROOT = Path(__file__).resolve().parents[1]
AXES = axes()  # build/vocabulary.py owns this; the score schema declares it

# Axes exempt from the digest requirement because a digest could not have been recorded when
# their sources were read. A visible list that shrinks, rather than a date comparison that
# quietly covers whatever is old.
#
# Empty, and worth saying why. The six axes carrying a date when this gate landed all
# predated it and so would all have qualified. They were re-fetched instead, which took 23
# requests and produced two findings the exemption would have hidden — a Lucie source URL
# that had never resolved as cited, and an `rwkv` weights claim with no source behind it at
# all. Exempting is the cheaper move and it is available. It is not the better one when the
# set is small.
#
# Digests only. An exemption says a digest was unobtainable, which says nothing about whether
# the sources support the date. That is the invariant's question, and the invariant has no
# exemptions.
#
# Each entry names the axis as `<product>:<axis>` and why. Stale entries are reported.
DIGEST_EXEMPT: dict[str, str] = {}


def load() -> tuple[dict, dict, dict]:
    """(scores, categories, resolved recipe variants per category)."""
    scores = {
        p.stem: yaml.safe_load(p.read_text()) or {}
        for p in sorted((ROOT / "sources" / "scores").glob("*.yaml"))
    }
    categories = {
        p.stem: yaml.safe_load(p.read_text()) or {}
        for p in sorted((ROOT / "sources" / "categories").glob("*.yaml"))
    }
    shared = load_shared(ROOT)
    recipes = {}
    for slug, category in categories.items():
        variants, errors = resolve_recipe_variants(category, shared)
        if variants and not errors:
            recipes[slug] = variants
    return scores, categories, recipes


def category_of(categories: dict) -> dict[str, str]:
    """product slug -> its category slug. `validate.py` guarantees exactly one."""
    return {
        product: slug
        for slug, category in categories.items()
        for product in (category.get("products") or [])
    }


def machine_routed_adoption(scores: dict, categories: dict, root: Path | None = None) -> dict[str, str]:
    """product slug -> route id, for each banded adoption axis a scheduled run can date.

    The route is the one `build/adoption_measurements.select_route` resolves by precedence, the
    same selection the reconciliation and `build/axis_assessments.py` use. A hand-authored route
    (`reported_traction`, `active_users`) has no collector, a null band has nothing to measure,
    and a route on another instrument than the recorded one never dates the axis, so none of
    those is listed.
    """
    from build.adoption_measurements import all_routes, load_inputs, route_scopes, select_route

    tables, _bands, _category_of, declared, *_ = load_inputs(root or ROOT)
    routes, scopes = all_routes(tables), route_scopes(tables)
    owner = category_of(categories)
    out: dict[str, str] = {}
    for slug, score in scores.items():
        block = score.get(DERIVED_AXIS) or {}
        if block.get("level") is None:
            continue
        route = select_route(
            declared.get(slug, set()), block.get("signal_type"), owner.get(slug), routes, scopes
        )
        # Only a route on the recorded instrument can ever date the axis: a cross-instrument
        # match is a coincidence the reconciliation queues as a route disagreement, so holding
        # such an axis for a scheduled run would hold it for good.
        if route and route["artifact_kind"] and route["instrument_type"] == block.get("signal_type"):
            out[slug] = route["route_id"]
    return out


def recorded_dimensions(components: dict[str, str], recipe: dict) -> dict[str, str]:
    """dimension -> the recorded key that answers it, for every dimension this score RECORDS.

    Two things it is deliberately not:

      * not the dimensions the winning rule reads. That is `dims_relied_on` in the
        warehouse, and it is the wrong denominator — a rule can win on license alone while
        `data` and `code` sit unconfirmed, so counting only what the rule read would let an
        axis claim a confirmation of dimensions nobody looked at.
      * not every key in the components string. Those carry plenty that no ladder scores —
        `paper`, `model_card`, `self-host` — and demanding an establishing source for
        `model_card:open` would make the gate expensive and pointless in the same move.

    So: the dimensions the recipe DECLARES, that this product actually records, plus the
    license, which is recorded rather than derived even though the formula reads the tier.

    Returns the recorded key alongside the dimension name because attribution may use
    either. `finetuned_chat` answers the data question under `post-training-data`, and a
    source that says `establishes: [post-training-data]` is being more precise than one
    saying `[data]`, not less.
    """
    declared = ((recipe.get("openness") or {}).get("dimensions")) or {}
    found: dict[str, str] = {}
    for name in declared:
        key = resolve_dimension(components, name, recipe)
        if key is not None:
            found[name] = key
    for key in license_read_keys(recipe):
        if key in components:
            found["license"] = key
            break
    return found


def invariant(
    scores: dict,
    categories: dict,
    recipes: dict,
    product_types: dict[str, str],
    ledger: dict | None = None,
    known_routes: set[str] | None = None,
    machine_routed: dict[str, str] | None = None,
    grandfathered: set[str] | None = None,
) -> list[str]:
    """Every recorded dimension of a dated axis has an establishing source read since.

    `ledger` is the observation-snapshot ledger a derived adoption date is resolved against;
    it is read from the repository when not supplied. `known_routes` is the compiled route ids,
    which the caller supplies because compiling them means reading the whole routing source and
    most corpora have nothing derived to check. `machine_routed` is `machine_routed_adoption`'s
    result, and `grandfathered` the `slug|date` lines of the hand-dated allowlist; an adoption
    axis on a machine-measured route may carry a date only through `derived_from` unless its
    exact date is grandfathered.
    """
    problems: list[str] = []
    owner = category_of(categories)
    ledger = load_ledger() if ledger is None else ledger
    machine_routed = machine_routed or {}
    grandfathered = grandfathered or set()
    for slug, score in sorted(scores.items()):
        variants = recipes.get(owner.get(slug, ""), {})
        recipe, _ = recipe_for(variants, product_types.get(slug, ""))
        recipe = recipe or {}
        for axis in AXES:
            block = score.get(axis) or {}
            claimed = parse_date(block.get("last_verified"))
            if block.get("last_verified") and claimed is None:
                problems.append(f"{slug}:{axis}: last_verified {block['last_verified']!r} is not a date")
                continue
            if claimed is None:
                continue

            sources = [s for s in (block.get("sources") or []) if isinstance(s, dict)]
            fresh = [s for s in sources if (parse_date(s.get("accessed")) or date.min) >= claimed]
            if block.get(DERIVATION_FIELD) is not None:
                # A derived adoption date rests on the observation the route measured, not on a
                # citation. That is not a hole in the floor below: the observation is a fetch
                # somebody's collector made, recorded with the date it was made, and the band it
                # produced matched the recorded one. The citation on such an axis is a hashed
                # snapshot of a figure that moves daily, so an `accessed` on it would date the
                # reading of a page rather than the currency of a number.
                if axis != DERIVED_AXIS:
                    problems.append(
                        f"{slug}:{axis}: carries {DERIVATION_FIELD}, which only "
                        f"{DERIVED_AXIS} may derive"
                    )
                problems.extend(derivation_problems(slug, block, ledger, known_routes))
            elif (
                axis == DERIVED_AXIS
                and slug in machine_routed
                and f"{slug}|{claimed.isoformat()}" not in grandfathered
            ):
                # No fallback to the floor. A fresh citation on a counts endpoint dates a reading
                # of a number that moves daily; where a route measures the band, the scheduled
                # reconciliation is the only thing that can confirm it.
                problems.append(
                    f"{slug}:{axis}: claims last_verified {claimed} without {DERIVATION_FIELD}, "
                    f"but {machine_routed[slug]} measures this band, so only "
                    f"build.adoption_freshness may date it. Drop the date and hold the axis "
                    f"with settled_by: scheduled_reconciliation"
                )
                continue
            elif not fresh:
                # The floor, and it is the whole of the check for adoption and capability:
                # those axes record one banded value rather than a dimension breakdown, so
                # there is nothing to attribute among, but a confirmation still cannot rest
                # on zero sources read on or after the day it claims to have happened.
                problems.append(
                    f"{slug}:{axis}: claims last_verified {claimed}, but no source was "
                    f"accessed on or after that date"
                )
                continue

            if axis != "openness":
                continue
            components = components_of(block)
            required = recorded_dimensions(components, recipe)
            for dimension, key in sorted(required.items()):
                names = {dimension, key}
                if not any(names & set(s.get("establishes") or []) for s in fresh):
                    stale = [
                        s.get("accessed")
                        for s in sources
                        if names & set(s.get("establishes") or [])
                    ]
                    detail = (
                        f"only established by a source last read {min(stale)}"
                        if stale
                        else "no source claims to establish it"
                    )
                    problems.append(
                        f"{slug}:{axis}: records {dimension!r} (as {key!r}) but {detail}; "
                        f"last_verified {claimed} is not supported for that dimension"
                    )
    return problems


def digests(scores: dict) -> list[str]:
    """Sources read as part of a claimed confirmation must show they were fetched."""
    problems: list[str] = []
    used: set[str] = set()
    for slug, score in sorted(scores.items()):
        for axis in AXES:
            block = score.get(axis) or {}
            claimed = parse_date(block.get("last_verified"))
            if claimed is None:
                continue
            key = f"{slug}:{axis}"
            if key in DIGEST_EXEMPT:
                used.add(key)
                continue
            for source in block.get("sources") or []:
                if not isinstance(source, dict):
                    continue
                if (parse_date(source.get("accessed")) or date.min) < claimed:
                    continue
                missing = [
                    field
                    for field in ("http_status", "content_sha256")
                    if source.get(field) in (None, "")
                ]
                if missing:
                    problems.append(
                        f"{key}: source {source.get('url')!r} was read on {source.get('accessed')} "
                        f"as part of the confirmation but records no {' and no '.join(missing)}; "
                        f"only an actual fetch produces those"
                    )
    # A stale exemption is an exemption that has stopped shrinking, so it is reported.
    for key, reason in sorted(DIGEST_EXEMPT.items()):
        if key not in used:
            problems.append(
                f"{key}: exempted from the digest requirement ({reason}) but the axis no "
                f"longer carries a last_verified. Drop the exemption."
            )
    return problems


def rule_outcomes(recipe: dict) -> set[tuple[int, str]]:
    """Every (score, class) some rule in the recipe can emit."""
    pairs: set[tuple[int, str]] = set()
    for rule in (recipe.get("openness") or {}).get("formula") or []:
        outcome = rule.get("then") or rule.get("otherwise") or {}
        if "score" in outcome and "class" in outcome:
            pairs.add((outcome["score"], outcome["class"]))
    return pairs


def producible_pairs(
    scores: dict, categories: dict, recipes: dict, product_types: dict[str, str]
) -> list[str]:
    """A recorded (score, class) must be an outcome the category's ladder can produce.

    A mixed category has one ladder per product type. Each product is checked against
    its OWN ladder via `recipe_for` — the same selection the invariant, `check_rubric` and
    `serialize_rubric` all use — not the union of every variant in the category. A
    software product recording a pair only the model ladder can emit must still fail
    here, even though some ladder in the category could have produced it.
    """
    problems: list[str] = []
    for slug, variants in sorted(recipes.items()):
        for product in categories[slug].get("products") or []:
            openness = (scores.get(product) or {}).get("openness") or {}
            score, klass = openness.get("score"), openness.get("class")
            if score is None:
                continue
            recipe, _ = recipe_for(variants, product_types.get(product, ""))
            pairs = rule_outcomes(recipe or {})
            if (score, klass) not in pairs:
                problems.append(
                    f"{product}:openness in {slug}: {score}/{klass} is not an outcome any rule "
                    f"in the recipe produces (it emits {sorted(pairs)}). One of the two values "
                    f"is wrong; read the product rather than widening the ladder to admit it."
                )
    return problems


# The `shows` field exists so a reader can tell whether the recorded claim follows from the
# page. A batch marker in it says only that a batch ran, and nothing else in this file can
# tell the difference: `digests` asks whether a source was FETCHED, `check_refetch` asks
# whether it is still fetchable, and a placeholder passes both.
#
# 33 sources across the 13 flagship files carried `flagship phase-C verification source` from
# a June batch. Three of them were re-fetched and re-digested on 2026-08-13 with the string
# copied forward, so this is not a legacy shape that decays on its own — a pass reproduced it.
#
# Matched as a SUBSTRING, not by equality. Four of the 33 had a real sentence appended to the
# marker rather than replacing it — "flagship phase-C verification source; answered HTTP 429
# to the 2026-08-13 re-read..." — so an exact-match gate reported clean while the batch
# marker it exists to prohibit was still in the file. The useful half of those four was kept
# and the marker dropped; a gate that only caught the unedited form would have let the next
# half-edit through the same way.
PLACEHOLDER_SHOWS = {
    "flagship phase-C verification source",
}


def placeholder_shows(scores: dict) -> list[str]:
    """A `shows` that records a batch marker rather than what the page shows."""
    problems: list[str] = []
    for slug, score in sorted(scores.items()):
        for axis in AXES:
            for source in (score.get(axis) or {}).get("sources") or []:
                if not isinstance(source, dict):
                    continue
                shows = " ".join(str(source.get("shows", "")).split())
                if any(marker in shows for marker in PLACEHOLDER_SHOWS):
                    problems.append(
                        f"{slug}:{axis}: source {source.get('url')!r} records a batch marker "
                        f"as its `shows` rather than what the page shows. Quote the body, or "
                        f"drop the source"
                    )
    return problems


GATES = {
    "invariant": "a confirmation with no supporting evidence",
    "digests": "a claimed date with no fetch digest",
    "producible-pairs": "an impossible score/class pair",
    "placeholder-shows": "a `shows` that records a batch marker, not the page",
}
NAME_WIDTH = max(len(name) for name in GATES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=sorted(GATES), help="run one gate only")
    parser.add_argument("--verbose", action="store_true", help="show what each gate covered")
    args = parser.parse_args()

    scores, categories, recipes = load()
    product_types = load_product_types(ROOT)
    # Compiling the routes reads the whole routing source, and a corpus with no derived date has
    # no route to check, so this is paid for only where something derives.
    derived = any(
        (score.get(DERIVED_AXIS) or {}).get(DERIVATION_FIELD) for score in scores.values()
    )
    results = {
        "invariant": invariant(
            scores, categories, recipes, product_types,
            known_routes=known_route_ids() if derived else None,
            machine_routed=machine_routed_adoption(scores, categories),
            grandfathered=hand_dated_allowlist(),
        ),
        "digests": digests(scores),
        "producible-pairs": producible_pairs(scores, categories, recipes, product_types),
        "placeholder-shows": placeholder_shows(scores),
    }
    if args.gate:
        results = {args.gate: results[args.gate]}

    dated = sum(
        1
        for score in scores.values()
        for axis in AXES
        if (score.get(axis) or {}).get("last_verified")
    )
    scored = sum(
        1
        for slug in recipes
        for product in categories[slug].get("products") or []
        if ((scores.get(product) or {}).get("openness") or {}).get("score") is not None
    )

    if args.verbose:
        print(f"{dated} axis/axes carry a last_verified  (invariant, digests scope)")
        print(
            f"{scored} scored products in {len(recipes)} categories with a recipe  "
            f"(producible-pairs scope)"
        )
        if DIGEST_EXEMPT:
            print(f"{len(DIGEST_EXEMPT)} digest exemption(s), each of which should be shrinking")
        print(
            f"{len(hand_dated_allowlist())} grandfathered hand-dated adoption axis/axes in "
            f"{HAND_DATED_PATH}, which should be shrinking"
        )
        print()

    failed = False
    for gate, problems in results.items():
        status = "OK" if not problems else "FAIL"
        print(f"{gate:<{NAME_WIDTH}}  {GATES[gate]:<44} [{status}]")
        for problem in problems:
            print(f"  ! {problem}")
        if problems:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
