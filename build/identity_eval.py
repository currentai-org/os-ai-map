"""Replay eval: score the identity graph's edges against prior human decisions.

The `currentai.identity.*` dataset (Phase 1) proposes edges -- an artifact belongs to a
product, two artifacts are the same product, an artifact's org -- at a confidence the
automation can act on. Before any of that is allowed to auto-emit, this module answers one
question: against every identity decision a person has already made, how often would the
graph have agreed?

## Fix round 1 -- this rewrite

The first version of this module was reviewed against the deployed SQL at
`/workspace/GitHub/oso-external/currentai-org/udms/identity_*.sql` and failed on schema: it
compared `method` (an `ARRAY(VARCHAR)` in every deployed model) to a bare string, so the
name-match prohibition was inert; it read `artifact_kind`/`artifact_id` columns that
`equivalence_edges` and `artifact_identity_edges` do not carry; `org`'s `candidate_key`
carried no kind prefix while truth's did; `artifact_identity` truth was a self-loop that
could never match the deployed pair grain; two `KNOWN_NEGATIVES` were declared, scored
artifacts rather than known negatives; `scoring_bearing` could be bypassed by passing a
metric name instead of an edge-table name; `recall` could exceed 1.0 on duplicate-spelling
edges; and `membership_non_scoring`'s recall floor was mathematically unsatisfiable because
every declared kind in the corpus happens to have an adoption route. This version fixes all
of that -- see the full review at
`.superpowers/sdd/2026-09-03-phase-1-identity-implementation/task-6-review.md` for detail on
each finding (M1-M9).

Two further additions landed in the same fix round, from a second reviewer disposition:

- `--allow-unprovisioned` (`--from-warehouse` only): treats a missing
  `currentai.identity.*` table as "not deployed yet" and exits 0 instead of 2, so the
  scheduled workflow is not red for months while Task 6 waits on the dataset to ship. It
  refuses to run at all -- exit 2, before touching the warehouse -- if `warehouse/assets.yaml`
  already marks any `identity.*` asset `materialized: true`, so the skip cannot outlive the
  deploy it is meant to wait for.
- Membership truth is keyed on `(artifact_kind, folded artifact_id, product_slug)`, not on
  the artifact alone: a `member_of` ruling for package X against product A and a
  `not_member_of` for the SAME package against product B are two distinct truth items, not a
  contradiction. `build.resolution.load()` still enforces uniqueness per `(artifact,
  relation)` today (a stricter grain than the ledger will carry once a parallel PR adds
  `resolves_to` to it), so the ledger-consuming logic here is written as a pure function over
  an ITERABLE of ledger entries -- `_membership_from_ledger` -- rather than assuming the
  loader's returned dict is the final word on how many rulings one artifact can carry. See
  `tests/test_identity_eval.py::test_membership_truth_keeps_two_products_for_one_artifact_distinct`,
  which exercises this with two entries sharing one artifact key and cannot rely on
  `resolution.load()` to prove it, precisely because today's loader would raise
  `DuplicateResolution` on that YAML shape.

## Where truth comes from

Never the warehouse. `Truth` is assembled entirely from repo sources that are readable in
CI with no `OSO_API_KEY`:

- `build.resolution.load()` -- the resolution ledger, read through `_ledger_entries` /
  `_equivalence_from_ledger` / `_membership_from_ledger` (pure functions over the loaded
  items, not the loader's dict identity -- see above). An `existing_product`/`sku_of`
  ruling is a positive `product_equivalence` answer, keyed on `candidate_key`
  (`"<kind>:<folded id>"`, matching the deployed `equivalence_edges`/`org_edges` contract);
  `excluded_boundary`/`excluded_maintenance` is a negative one (the artifact must never
  resolve to *any* product). A `member_of`/`not_member_of` ruling is a positive or negative
  `product_membership` answer, keyed on `(artifact_kind, folded artifact_id, product_slug)`.
- `sources/products/*.yaml` -- every artifact a product declares is a positive membership
  truth. Two or more DISTINCT declared spellings of the same kind that fold to the same
  comparison key are `artifact_identity` truth (a fold-collapse pair) -- there are none in
  the corpus today, so this truth set is empty; see `test_artifact_identity_truth_is_empty_today`.
- `sources/organizations/*.yaml` -- each org's `products:` roster, bridged through a
  product's declared artifacts, gives `candidate_key -> org_slug` truth.
- `KNOWN_NEGATIVES` -- artifacts a person has confirmed do NOT belong where a naive signal
  would place them: eight PyPI packages, verified against `sources/scores/*.yaml` notes in
  the `storage` category, that share (or nearly share) a product's name but are that
  product's client library rather than its own countable artifact, AND are confirmed absent
  from `sources/products/<slug>.yaml`. `load_truth` asserts this at load time and raises if a
  future edit ever declares one -- see `KnownNegativeDeclaredError` and
  `test_known_negative_declared_as_real_artifact_raises`, which exercises the exact
  historical bug (`pymilvus`/`qdrant-client`, both legitimately declared) that the first
  version of `KNOWN_NEGATIVES` got wrong.
- `_route_kinds()` -- compiled from `sources/signal_routing.yaml` via
  `build.serialize_routing`, mirroring `identity_membership_edges.sql`'s own
  `scoring_bearing` derivation (`artifact_kind IN (SELECT artifact_kind FROM
  registry.adoption_routes)`). Used only to partition membership truth into scoring vs
  non-scoring for `membership_non_scoring`'s `n_truth` -- see `MIN_TRUTH` below for why this
  matters.

## What `--from-warehouse` supplies, and what it does not

Only the four edge tables -- `currentai.identity.{artifact_identity,membership,equivalence,
org}_edges`, read with an explicit column list (never `SELECT *`) written to the CONTRACT
this fix round settled, not to the SQL files as they exist today: `equivalence_edges` and
`org_edges` do not yet carry a kind-prefixed `candidate_key` or an `artifact_kind` column,
per the review's M2/M3 -- a parallel change updates the SQL to that shape before deploy.
Truth is never re-derived from the warehouse's own `registry.*` mirrors, so the same eval
logic runs identically against a live run and against a fixture.

A missing table exits 2 naming it (or 0, under `--allow-unprovisioned`, if the dataset is
not yet marked deployed); a missing REQUIRED column on an actual row exits 2 naming it too --
`validate_columns` checks before any `_score_*` function ever indexes a row, so no `KeyError`
can escape to a traceback in a scheduled run.

## Insufficient truth, not a floor that can never be met

A relation's floor is enforced only when `n_truth >= MIN_TRUTH` (20). Below that, the table
prints `insufficient truth (n)` for that relation and `--floors` cannot exit 1 on it --
`artifact_identity` (0 truth pairs today) and `membership_non_scoring` (0 truth items with a
kind that has no adoption route, today only `homepage`, which no product declares) would
otherwise floor on data that cannot possibly satisfy them, which is exactly the review's M8.

## The two rules pinned as tests, not metrics

A metric is a rate that is allowed to miss sometimes. These are not that:

- A `name_match` edge never auto-emits, on any relation, at any confidence -- checked against
  `method` as the deployed models actually emit it, an `ARRAY(VARCHAR)`: an edge emits only
  if `method` is present, non-empty, and carries at least one element other than
  `"name_match"`. Missing or empty `method` never emits either -- fail closed, not fail open.
- A scoring-bearing membership edge never auto-emits, regardless of confidence -- checked
  unconditionally, before `THRESHOLDS` is even consulted, for any relation NAME starting with
  `"membership"` (there is exactly one such edge-table relation, `"membership"`; the check
  does not key off the literal string `"membership"` alone so that passing a metric name by
  mistake cannot silently route around it -- `emits` now rejects any relation that is not one
  of the four edge-table names outright).

Usage:
    uv run python -m build.identity_eval --edges fixture.json
    uv run python -m build.identity_eval --edges fixture.json --floors
    uv run python -m build.identity_eval --from-warehouse --floors
    uv run python -m build.identity_eval --from-warehouse --floors --allow-unprovisioned
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from build import resolution
from build.identity import KINDS, fold_for_proposal
from build.serialize_registry import artifact_id

ROOT = Path(__file__).resolve().parents[1]
ASSETS_PATH = ROOT / "warehouse" / "assets.yaml"

Key = tuple[str, str]

# The four edge tables the identity dataset is designed to publish, and the only relation
# names `emits`/`emitted_at_threshold`/`digest_items` accept. `replay`'s output additionally
# carries `membership_scoring` and `membership_non_scoring` -- synthetic metric names, never
# passed to `emits`, which is exactly what closes M6 (a caller handing `emits` a metric name
# instead of an edge-table name used to bypass the scoring-bearing check).
EDGE_RELATIONS = ("artifact_identity", "membership", "equivalence", "org")

# Confidence an edge needs to auto-emit, per relation (edge-table names; `membership` looks
# up `membership_non_scoring` here since a scoring-bearing membership edge never reaches a
# confidence check at all -- see `emits`).
THRESHOLDS: dict[str, float] = {
    "artifact_identity": 0.99,
    "membership_non_scoring": 0.90,
    "equivalence": 1.00,
    "org": 0.85,
}

# Precision/recall floors, checked only under `--floors`, only for relations where automation
# is planned, and only when the relation clears `MIN_TRUTH` -- see the module docstring.
# `membership_scoring` carries no floor because it is never automated: `emits` forbids a
# scoring-bearing membership edge from emitting at any confidence.
FLOORS: dict[str, tuple[float, float]] = {
    "artifact_identity": (0.99, 0.95),
    "membership_non_scoring": (0.98, 0.90),
    "equivalence": (1.00, 0.90),
    "org": (0.97, 0.85),
}

# Below this many truth items, a floor cannot mean anything -- see the module docstring on
# `artifact_identity` and `membership_non_scoring`, both 0 in the corpus today.
MIN_TRUTH = 20

ALL_RELATIONS = ("equivalence", "membership_scoring", "membership_non_scoring", "artifact_identity", "org")

# Eight storage-category products whose same- or near-same-named PyPI package is a verified
# client library, not the product's own countable artifact -- read from each product's
# `sources/scores/<slug>.yaml` adoption note (2026-08-18 verification pass) and confirmed
# absent from `sources/products/<slug>.yaml`. `pymilvus` (milvus) and `qdrant-client` (qdrant)
# were removed from an earlier version of this list after review: both ARE declared,
# hand-exempted (`artifact_exceptions.pypi_repo_mismatch`) artifacts, scored on exactly the
# package this list would have called a negative -- the storage category resolved that trap
# the other way for those two. `load_truth` asserts every remaining entry here really is
# undeclared and raises `KnownNegativeDeclaredError` if a future edit ever declares one.
KNOWN_NEGATIVES: tuple[dict[str, str], ...] = (
    {"kind": "pypi", "artifact_id": "elasticsearch", "product_slug": "elasticsearch"},
    {"kind": "pypi", "artifact_id": "meilisearch", "product_slug": "meilisearch"},
    {"kind": "pypi", "artifact_id": "typesense", "product_slug": "typesense"},
    {"kind": "pypi", "artifact_id": "weaviate-client", "product_slug": "weaviate"},
    {"kind": "pypi", "artifact_id": "pyvespa", "product_slug": "vespa"},
    {"kind": "pypi", "artifact_id": "aistore", "product_slug": "aistore"},
    {"kind": "pypi", "artifact_id": "openmldb", "product_slug": "openmldb"},
    {"kind": "pypi", "artifact_id": "infinity-sdk", "product_slug": "infinity"},
)

WAREHOUSE_TABLES: dict[str, str] = {
    "artifact_identity": "currentai.identity.artifact_identity_edges",
    "membership": "currentai.identity.membership_edges",
    "equivalence": "currentai.identity.equivalence_edges",
    "org": "currentai.identity.org_edges",
}

# Explicit column lists for `--from-warehouse` -- never `SELECT *`. `equivalence` and `org`
# are written to the candidate_key/artifact_kind CONTRACT this fix round settled (see the
# module docstring), not to `udms/identity_{equivalence,org}_edges.sql` as they read today.
WAREHOUSE_COLUMNS: dict[str, tuple[str, ...]] = {
    "artifact_identity": ("artifact_kind", "artifact_id_a", "artifact_id_b", "confidence", "method", "penalties"),
    "membership": (
        "artifact_kind", "artifact_id", "product_tier", "product_slug", "confidence", "method",
        "penalties", "scoring_bearing",
    ),
    "equivalence": ("artifact_kind", "candidate_key", "product_tier", "product_slug", "confidence", "method", "penalties"),
    "org": ("artifact_kind", "candidate_key", "org_slug", "confidence", "method", "penalties"),
}

# The columns `_score_*` actually indexes. A row missing one of these cannot be scored --
# `validate_columns` catches it before any `_score_*` function runs, so no `KeyError` escapes.
# `scoring_bearing` is required for `membership`, not merely defaulted, because a missing flag
# defaulting to "not scoring-bearing" would be exactly the kind of fail-open the governance
# rule exists to prevent.
REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "artifact_identity": ("artifact_kind", "artifact_id_a", "artifact_id_b"),
    "membership": ("artifact_kind", "artifact_id", "product_slug", "scoring_bearing"),
    "equivalence": ("candidate_key", "product_slug"),
    "org": ("candidate_key", "org_slug"),
}


def candidate_key(kind: str, ident: str) -> str:
    """`"<artifact_kind>:<folded artifact_key>"` -- the format `equivalence` and `org` truth
    and (once the parallel SQL change lands) edges both key on. Folding goes through
    `fold_for_proposal`, which mirrors `identity_artifact_nodes.sql`'s `keyed` CTE exactly.
    """
    return f"{kind}:{fold_for_proposal(kind, ident)}"


def _membership_key(kind: str, ident: str) -> Key:
    return (kind, fold_for_proposal(kind, ident))


def _methods(edge: dict) -> set[str]:
    """`edge["method"]` normalized to a set of tokens. Every deployed model emits `method` as
    `ARRAY(VARCHAR)` (`ARRAY_SORT(ARRAY_DISTINCT(ARRAY_AGG(method)))`); a fixture may still
    hand this a bare string, which is accepted as a single-element set for convenience. `None`
    or an empty array/string normalizes to the empty set, which `emits` treats as fail-closed
    (never emits), not fail-open.
    """
    raw = edge.get("method")
    if raw is None:
        return set()
    if isinstance(raw, str):
        return {raw} if raw else set()
    if isinstance(raw, (list, tuple, set)):
        return {str(m) for m in raw if m}
    return {str(raw)}


def _scoring_bearing(edge: dict) -> bool:
    """`True`/`"true"` (any case) count as bearing; everything else -- `False`, `"false"`,
    `None`, missing -- does not. Deliberately not bare Python truthiness: `bool("false")` is
    `True`, which would suppress a real, correctly-flagged non-bearing edge rather than gate
    on the value it actually carries.
    """
    val = edge.get("scoring_bearing")
    if isinstance(val, str):
        return val.strip().lower() == "true"
    return bool(val)


def emits(edge: dict, relation: str) -> bool:
    """Whether `edge`, drawn from the `relation` edge table, would auto-emit.

    `relation` must be one of `EDGE_RELATIONS` -- a metric name like `membership_non_scoring`
    raises rather than silently routing around the scoring-bearing check (M6). The two
    never-emit rules are checked ahead of any confidence lookup, so there is no confidence
    high enough to satisfy either:

    - Any relation whose name starts with `"membership"` (today, only `"membership"` itself)
      never emits a `scoring_bearing` edge, regardless of confidence.
    - No relation emits an edge whose normalized `method` set is empty, or contains nothing
      besides `"name_match"`.
    """
    if relation not in EDGE_RELATIONS:
        raise ValueError(f"emits() takes an edge-table relation {EDGE_RELATIONS!r}, got {relation!r}")
    if relation.startswith("membership") and _scoring_bearing(edge):
        return False
    methods = _methods(edge)
    if not methods or not (methods - {"name_match"}):
        return False
    threshold = THRESHOLDS["membership_non_scoring"] if relation == "membership" else THRESHOLDS[relation]
    return float(edge.get("confidence") or 0.0) >= threshold


def emitted_at_threshold(edges: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """`edges`, filtered per relation to what would actually auto-emit."""
    return {relation: [e for e in items if emits(e, relation)] for relation, items in edges.items()}


def digest_items(edges: dict[str, list[dict]]) -> list[dict]:
    """Everything that did NOT auto-emit, flattened across relations -- the review queue.
    A name-match edge and a scoring-bearing membership edge both land here rather than
    vanishing, which is what the two never-auto-emit tests check on top of
    `emitted_at_threshold` being empty: excluded from automation is not discarded.
    """
    out: list[dict] = []
    for relation, items in edges.items():
        out.extend(e for e in items if not emits(e, relation))
    return out


@dataclass
class Truth:
    """Every prior human decision the graph is replayed against.

    `equivalence`: candidate_key -> the product slug it resolves to (positive).
    `equivalence_negatives`: candidate_keys that must resolve to NO product.
    `membership`: (artifact_kind, folded artifact_id, product_slug) -> True (is a member) or
    False (is known NOT to be -- a ledger `not_member_of` or a `KNOWN_NEGATIVES` entry). Two
    verdicts against the SAME artifact for two different products are two distinct keys, not
    a collision -- see `_membership_from_ledger`.
    `org`: candidate_key -> the org slug that artifact's product belongs to.
    `identity_pairs`: `{(artifact_kind, folded_a, folded_b)}` for declared spelling pairs that
    fold to the same comparison key (folded_a == folded_b by construction -- see the module
    docstring). Empty in the corpus today.
    `route_kinds`: artifact kinds `sources/signal_routing.yaml` compiles at least one adoption
    route for -- used only to split membership truth into scoring/non-scoring buckets for
    `n_truth`, mirroring `identity_membership_edges.sql`'s own `scoring_bearing` derivation.
    """

    equivalence: dict[str, str] = field(default_factory=dict)
    equivalence_negatives: set[str] = field(default_factory=set)
    membership: dict[tuple[Key, str], bool] = field(default_factory=dict)
    org: dict[str, str] = field(default_factory=dict)
    identity_pairs: set[tuple[str, str, str]] = field(default_factory=set)
    route_kinds: frozenset[str] = field(default_factory=frozenset)


@dataclass
class Metrics:
    precision: float | None
    recall: float | None
    n_truth: int
    n_emitted_at_threshold: int


class KnownNegativeDeclaredError(ValueError):
    """A `KNOWN_NEGATIVES` entry claims an artifact is not a member of a product that
    `sources/products/<slug>.yaml` actually declares it under. See M5/M9 in the review --
    this is the exact shape of bug the guard test now exercises for real, not tautologically.
    """


def _declared_products() -> dict[str, dict]:
    return {
        path.stem: yaml.safe_load(path.read_text()) or {}
        for path in sorted((ROOT / "sources" / "products").glob("*.yaml"))
    }


def _equivalence_from_ledger(entries: Iterable[tuple[tuple[Key, str], dict]]) -> tuple[dict[str, str], set[str]]:
    """(positive, negative) equivalence truth, keyed on `candidate_key`.

    `entries` is an iterable of `((kind, canonical_id), relation), entry` pairs, the shape of
    `build.resolution.load().items()` -- see `_membership_from_ledger` for why this takes an
    iterable rather than requiring that exact dict.
    """
    positive: dict[str, str] = {}
    negative: set[str] = set()
    for (key, relation), entry in entries:
        if relation != "product_equivalence":
            continue
        verdict = entry["verdict"]
        ck = candidate_key(*key)
        if verdict in ("existing_product", "sku_of"):
            slug = entry.get("resolves_to") or entry.get("product")
            if slug:
                positive[ck] = slug
        elif verdict in ("excluded_boundary", "excluded_maintenance"):
            negative.add(ck)
        # `unresolved` carries no truth signal either way -- a person has not decided.
    return positive, negative


def _membership_from_ledger(entries: Iterable[tuple[tuple[Key, str], dict]]) -> dict[tuple[Key, str], bool]:
    """Membership truth, keyed on `(artifact_kind, folded artifact_id, product_slug)`.

    Takes an ITERABLE, not a dict keyed uniquely on `(artifact, relation)` --
    `build.resolution.load()` enforces that narrower uniqueness today
    (`resolution.DuplicateResolution`), but a `member_of` ruling for artifact X against
    product A and a `not_member_of` for the SAME X against product B are two distinct truth
    items, not a contradiction, once the ledger's grain includes `resolves_to` (a parallel
    PR). Grouping on the full `(key, resolves_to)` pair here, rather than trusting the
    loader's key identity, is what makes that safe either way --
    `tests/test_identity_eval.py::test_membership_truth_keeps_two_products_for_one_artifact_distinct`
    proves it with two entries sharing one artifact key, which today's loader could not
    itself return without raising.
    """
    out: dict[tuple[Key, str], bool] = {}
    for (key, relation), entry in entries:
        if relation != "product_membership":
            continue
        slug = entry.get("resolves_to")
        if slug:
            out[(key, slug)] = entry["verdict"] == "member_of"
    return out


def _route_kinds() -> frozenset[str]:
    """Artifact kinds with at least one compiled adoption route -- mirrors
    `identity_membership_edges.sql`'s `scoring_bearing` derivation
    (`artifact_kind IN (SELECT artifact_kind FROM registry.adoption_routes)`), computed from
    `sources/signal_routing.yaml` rather than the warehouse so this stays fixture-safe.
    """
    from build.serialize_routing import adoption_aggregation_rules, load_routing
    from build.serialize_routing import adoption_routes as _adoption_routes

    routing = load_routing(ROOT)
    agg_rows, _ = adoption_aggregation_rules(routing)
    by_instrument = {r["applies_to_instrument"]: r["aggregation_rule_id"] for r in agg_rows}
    routes, errors = _adoption_routes(routing, by_instrument)
    if errors:
        raise RuntimeError(f"sources/signal_routing.yaml did not compile cleanly: {errors}")
    return frozenset(r["artifact_kind"] for r in routes if r["artifact_kind"])


def load_truth(known_negatives: tuple[dict[str, str], ...] = KNOWN_NEGATIVES) -> Truth:
    """Assemble `Truth` from the ledger, declared artifacts, and org rosters.

    `known_negatives` is a parameter, not a hardcoded read of the module constant, so a test
    can inject a bad entry and assert `load_truth` raises rather than silently corrupting the
    membership table -- see `KnownNegativeDeclaredError`.
    """
    ledger_items = list(resolution.load().items())
    equivalence, equivalence_negatives = _equivalence_from_ledger(ledger_items)
    membership = _membership_from_ledger(ledger_items)

    products = _declared_products()

    # fold-collapse artifact_identity truth: distinct declared spellings of one kind that fold
    # to the same comparison key. None exist in the corpus today (see the module docstring),
    # so this is deliberately built from first principles rather than assumed empty.
    by_key: dict[Key, set[str]] = {}
    for product in products.values():
        for kind in KINDS:
            for entry in product.get(kind) or []:
                ident = artifact_id(kind, entry.get("url") or "")
                if ident:
                    by_key.setdefault((kind, fold_for_proposal(kind, ident)), set()).add(ident)
    identity_pairs: set[tuple[str, str, str]] = set()
    for (kind, _folded), spellings in by_key.items():
        if len(spellings) < 2:
            continue
        for a, b in itertools.combinations(sorted(spellings), 2):
            fa, fb = fold_for_proposal(kind, a), fold_for_proposal(kind, b)
            lo, hi = sorted((fa, fb))
            identity_pairs.add((kind, lo, hi))

    # Declared artifacts: positive membership truth, and org truth bridged through each
    # product's org.
    product_org: dict[str, str] = {}
    for path in sorted((ROOT / "sources" / "organizations").glob("*.yaml")):
        roster = yaml.safe_load(path.read_text()) or {}
        for slug in roster.get("products") or []:
            product_org[slug] = path.stem

    org: dict[str, str] = {}
    for slug, product in products.items():
        for kind in KINDS:
            for entry in product.get(kind) or []:
                ident = artifact_id(kind, entry.get("url") or "")
                if not ident:
                    continue
                key = _membership_key(kind, ident)
                membership.setdefault((key, slug), True)
                if slug in product_org:
                    org.setdefault(candidate_key(kind, ident), product_org[slug])

    declared_true = {(k, s) for (k, s), is_member in membership.items() if is_member}
    for neg in known_negatives:
        key = _membership_key(neg["kind"], neg["artifact_id"])
        if (key, neg["product_slug"]) in declared_true:
            raise KnownNegativeDeclaredError(
                f"KNOWN_NEGATIVES claims {neg['kind']}:{neg['artifact_id']!r} is not a member "
                f"of {neg['product_slug']!r}, but sources/products/{neg['product_slug']}.yaml "
                f"declares it as an artifact. Remove it from KNOWN_NEGATIVES or fix the "
                f"declaration."
            )
        membership[(key, neg["product_slug"])] = False

    return Truth(
        equivalence=equivalence,
        equivalence_negatives=equivalence_negatives,
        membership=membership,
        org=org,
        identity_pairs=identity_pairs,
        route_kinds=_route_kinds(),
    )


def _score(emitted: list[dict], key_fn, correct_fn, n_truth: int) -> Metrics:
    """Generic scorer. `key_fn(edge)` is the relation key used to DEDUPE emitted edges (a
    head/tail duplicate of one logical edge counts once, per the review's M7 fix).
    `correct_fn(edge) -> (is_correct, truth_key)`: `truth_key` identifies the distinct truth
    item matched, so recall counts distinct truth items found, not emitted-edge occurrences --
    recall is clamped to 1.0 as a defensive floor, though the dedup already makes exceeding it
    impossible by construction.
    """
    seen: dict = {}
    for e in emitted:
        k = key_fn(e)
        if k not in seen:
            seen[k] = correct_fn(e)
    n_emitted = len(seen)
    n_correct = sum(1 for is_correct, _ in seen.values() if is_correct)
    matched_truth = {tk for is_correct, tk in seen.values() if is_correct and tk is not None}
    precision = n_correct / n_emitted if n_emitted else None
    recall = min(len(matched_truth) / n_truth, 1.0) if n_truth else None
    return Metrics(precision, recall, n_truth, n_emitted)


def _score_equivalence(emitted: list[dict], truth: Truth) -> Metrics:
    def key_fn(e: dict):
        return (e.get("candidate_key"), e.get("product_slug"))

    def correct_fn(e: dict):
        ck, slug = e.get("candidate_key"), e.get("product_slug")
        if ck in truth.equivalence_negatives:
            return False, None
        ok = truth.equivalence.get(ck) == slug
        return ok, (ck if ok else None)

    return _score(emitted, key_fn, correct_fn, len(truth.equivalence))


def _score_membership(emitted: list[dict], truth: Truth, scoring_bearing: bool) -> Metrics:
    def key_fn(e: dict):
        return (_membership_key(e.get("artifact_kind"), e.get("artifact_id")), e.get("product_slug"))

    def correct_fn(e: dict):
        k = key_fn(e)
        ok = truth.membership.get(k) is True
        return ok, (k if ok else None)

    n_truth = sum(
        1
        for (key, _slug), is_member in truth.membership.items()
        if is_member and (key[0] in truth.route_kinds) == scoring_bearing
    )
    return _score(emitted, key_fn, correct_fn, n_truth)


def _score_org(emitted: list[dict], truth: Truth) -> Metrics:
    def key_fn(e: dict):
        return (e.get("candidate_key"), e.get("org_slug"))

    def correct_fn(e: dict):
        ck = e.get("candidate_key")
        ok = truth.org.get(ck) == e.get("org_slug")
        return ok, (ck if ok else None)

    return _score(emitted, key_fn, correct_fn, len(truth.org))


def _identity_pair(e: dict) -> tuple[str, str, str]:
    kind = e.get("artifact_kind")
    fa = fold_for_proposal(kind, e.get("artifact_id_a"))
    fb = fold_for_proposal(kind, e.get("artifact_id_b"))
    lo, hi = sorted((fa, fb))
    return (kind, lo, hi)


def _score_identity(emitted: list[dict], truth: Truth) -> Metrics:
    def correct_fn(e: dict):
        pair = _identity_pair(e)
        ok = pair in truth.identity_pairs
        return ok, (pair if ok else None)

    return _score(emitted, _identity_pair, correct_fn, len(truth.identity_pairs))


def replay(edges: dict[str, list[dict]], truth: Truth) -> dict[str, Metrics]:
    """Score every relation `edges` carries against `truth`.

    `membership` is one edge table but two questions for governance purposes, so it is split
    here into `membership_scoring` and `membership_non_scoring` -- the only two relation
    names this returns that are not literal edge-table keys, and never passed to `emits`
    (see `EDGE_RELATIONS`). `n_truth` for each is partitioned by `truth.route_kinds`, mirroring
    the deployed SQL's own `scoring_bearing` derivation -- fixing the review's M8, where both
    buckets previously drew on the same (unpartitioned) 855-item truth set and made
    `membership_non_scoring`'s recall floor mathematically unsatisfiable.
    `membership_scoring`'s `n_emitted_at_threshold` is always 0 by construction: `emits`
    forbids a scoring-bearing edge from emitting at any confidence.
    """
    at_threshold = emitted_at_threshold(edges)
    out: dict[str, Metrics] = {}

    if "equivalence" in edges:
        out["equivalence"] = _score_equivalence(at_threshold["equivalence"], truth)
    if "artifact_identity" in edges:
        out["artifact_identity"] = _score_identity(at_threshold["artifact_identity"], truth)
    if "org" in edges:
        out["org"] = _score_org(at_threshold["org"], truth)
    if "membership" in edges:
        emitted_membership = at_threshold["membership"]  # already all non-bearing, by `emits`
        out["membership_non_scoring"] = _score_membership(emitted_membership, truth, scoring_bearing=False)
        out["membership_scoring"] = _score_membership([], truth, scoring_bearing=True)

    return out


class WarehouseTableMissing(RuntimeError):
    def __init__(self, table: str, cause: Exception):
        super().__init__(
            f"{table} could not be queried ({type(cause).__name__}: {cause}). The "
            f"currentai.identity.* dataset has not deployed yet -- see docs/operations/"
            f"deploy-models.md."
        )
        self.table = table


class EdgeColumnMissing(RuntimeError):
    def __init__(self, relation: str, column: str):
        super().__init__(
            f"{relation} edges are missing required column {column!r} -- schema drift from "
            f"the deployed SQL contract this eval reads (see WAREHOUSE_COLUMNS/REQUIRED_COLUMNS)."
        )
        self.relation = relation
        self.column = column


def _identity_dataset_deployed(path: Path = ASSETS_PATH) -> list[str]:
    """Asset ids under `identity.*` that `warehouse/assets.yaml` marks `materialized: true`.

    Used only to REJECT `--allow-unprovisioned`: once any identity asset is marked deployed,
    a missing table is a real failure again, not an "unprovisioned, skip" signal, and the flag
    must not be usable to paper over that.
    """
    if not path.exists():
        return []
    doc = yaml.safe_load(path.read_text()) or {}
    return sorted(
        str(a.get("id"))
        for a in (doc.get("assets") or [])
        if str(a.get("id", "")).startswith("identity.") and a.get("materialized") is True
    )


def load_edges_from_warehouse() -> dict[str, list[dict]]:
    """The four edge tables, read live with an explicit column list per table. Raises
    `WarehouseTableMissing` naming whichever table could not be queried, rather than letting
    the first one crash the run opaquely.
    """
    from build.warehouse import query

    edges: dict[str, list[dict]] = {}
    for relation, table in WAREHOUSE_TABLES.items():
        columns = ", ".join(WAREHOUSE_COLUMNS[relation])
        try:
            edges[relation] = query(f"SELECT {columns} FROM {table}")
        except Exception as exc:  # noqa: BLE001 -- re-raised typed, with the table named
            raise WarehouseTableMissing(table, exc) from exc
    return edges


def load_edges_from_file(path: Path) -> dict[str, list[dict]]:
    return json.loads(path.read_text())


def validate_columns(edges: dict[str, list[dict]]) -> None:
    """Every row of every relation `REQUIRED_COLUMNS` names carries those columns with a
    non-null value. Raises `EdgeColumnMissing` naming the first offending relation and
    column, rather than letting a `_score_*` function `KeyError` on a `None` deep inside a
    scheduled run.
    """
    for relation, rows in edges.items():
        required = REQUIRED_COLUMNS.get(relation)
        if not required:
            continue
        for row in rows:
            for column in required:
                if row.get(column) is None:
                    raise EdgeColumnMissing(relation, column)


def floor_status(relation: str, metrics: dict[str, Metrics]) -> str:
    if relation not in metrics:
        return "not evaluated (edge table absent from input)"
    if relation not in FLOORS:
        return "no floor (never automated)"
    m = metrics[relation]
    if m.n_truth < MIN_TRUTH:
        return f"insufficient truth ({m.n_truth} < {MIN_TRUTH})"
    p_floor, r_floor = FLOORS[relation]
    precision = m.precision if m.precision is not None else 0.0
    recall = m.recall if m.recall is not None else 0.0
    return "checked (pass)" if precision >= p_floor and recall >= r_floor else "checked (FAIL)"


def floor_failures(metrics: dict[str, Metrics]) -> list[str]:
    """Relations under their floor. Only relations `FLOORS` names are checked, and only when
    `n_truth >= MIN_TRUTH` -- see `floor_status` for the same logic surfaced per-relation.
    """
    failures: list[str] = []
    for relation, (precision_floor, recall_floor) in FLOORS.items():
        if relation not in metrics:
            continue
        m = metrics[relation]
        if m.n_truth < MIN_TRUTH:
            continue
        precision = m.precision if m.precision is not None else 0.0
        if precision < precision_floor:
            failures.append(f"{relation}: precision {precision:.3f} < floor {precision_floor:.2f}")
        recall = m.recall if m.recall is not None else 0.0
        if recall < recall_floor:
            failures.append(f"{relation}: recall {recall:.3f} < floor {recall_floor:.2f}")
    return failures


def print_table(metrics: dict[str, Metrics]) -> None:
    header = (
        f"{'relation':24s} {'precision':>10s} {'recall':>10s} {'n_truth':>8s} "
        f"{'n_emitted':>10s}  status"
    )
    print(header)
    print("-" * len(header))
    for relation in ALL_RELATIONS:
        m = metrics.get(relation)
        precision = f"{m.precision:.3f}" if m and m.precision is not None else "n/a"
        recall = f"{m.recall:.3f}" if m and m.recall is not None else "n/a"
        n_truth = m.n_truth if m else 0
        n_emitted = m.n_emitted_at_threshold if m else 0
        print(f"{relation:24s} {precision:>10s} {recall:>10s} {n_truth:>8d} {n_emitted:>10d}  {floor_status(relation, metrics)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--from-warehouse", action="store_true", help="read the four identity edge tables live")
    source.add_argument("--edges", type=Path, help="path to a JSON fixture of edges, keyed by relation")
    parser.add_argument(
        "--floors", action="store_true",
        help="exit 1 if any relation with automation planned and sufficient truth falls under its floor",
    )
    parser.add_argument(
        "--allow-unprovisioned", action="store_true",
        help=(
            "--from-warehouse only: a missing currentai.identity.* table exits 0 (\"not "
            "provisioned yet\") instead of 2. Refused -- exit 2, no query attempted -- if "
            "warehouse/assets.yaml already marks any identity.* asset materialized: true."
        ),
    )
    args = parser.parse_args(argv)

    if args.allow_unprovisioned and not args.from_warehouse:
        print("[FAIL] --allow-unprovisioned only applies to --from-warehouse")
        return 2

    if args.from_warehouse:
        if args.allow_unprovisioned:
            # Explicit argument, not the default parameter: the default is bound once at
            # function-definition time, so a test that monkeypatches the module-level
            # ASSETS_PATH would otherwise be silently ignored here.
            deployed = _identity_dataset_deployed(ASSETS_PATH)
            if deployed:
                print(
                    f"[FAIL] --allow-unprovisioned refused: warehouse/assets.yaml already marks "
                    f"{', '.join(deployed)} materialized: true. The identity dataset is deployed, "
                    f"so a missing table is a real failure, not an unprovisioned skip -- remove "
                    f"--allow-unprovisioned from the caller."
                )
                return 2
        try:
            edges = load_edges_from_warehouse()
        except WarehouseTableMissing as exc:
            if args.allow_unprovisioned:
                print(f"skipped: identity dataset not provisioned (missing {exc.table})")
                return 0
            print(f"[FAIL] {exc}")
            return 2
    else:
        edges = load_edges_from_file(args.edges)

    try:
        validate_columns(edges)
    except EdgeColumnMissing as exc:
        print(f"[FAIL] {exc}")
        return 2

    truth = load_truth()
    metrics = replay(edges, truth)
    print_table(metrics)

    if args.floors:
        failures = floor_failures(metrics)
        if failures:
            print("\n[FAIL] under floor:")
            for line in failures:
                print(f"  {line}")
            return 1
        print("\n[OK] every checked relation clears its precision/recall floor")

    return 0


if __name__ == "__main__":
    sys.exit(main())
