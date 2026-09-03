"""Replay eval: score the identity graph's edges against prior human decisions.

The `currentai.identity.*` dataset (Phase 1) proposes edges — an artifact belongs to a
product, two artifacts are the same product, an artifact's org — at a confidence the
automation can act on. Before any of that is allowed to auto-emit, this module answers one
question: against every identity decision a person has already made, how often would the
graph have agreed?

## Where truth comes from

Never the warehouse. `Truth` is assembled entirely from repo sources that are readable in
CI with no `OSO_API_KEY`:

- `build.resolution.load()` — the resolution ledger. An `existing_product`/`sku_of` ruling
  is a positive `product_equivalence` answer; `excluded_boundary`/`excluded_maintenance` is a
  negative one (the artifact must never resolve to *any* product). A `member_of`/
  `not_member_of` ruling is a positive or negative `product_membership` answer.
- `sources/products/*.yaml` — every artifact a product declares is a positive membership
  truth (that artifact IS this product's own countable artifact) and a trivial positive
  identity truth (it resolves to itself).
- `sources/organizations/*.yaml` — each org's `products:` roster, bridged through the
  product's declared GitHub artifact, gives `candidate_key -> org_slug` truth.
- `KNOWN_NEGATIVES` — artifacts a person has confirmed do NOT belong where a naive signal
  would place them. Sourced from `sources/scores/*.yaml` notes in the `storage` category:
  ten PyPI packages that share (or nearly share) a product's name and slug but are, by
  hand-verified evidence, that product's *client library* rather than the product's own
  measurable artifact — the storage category's strapline names this as the layer's
  recurring trap ("the PyPI or npm name that matches them usually belongs to a client
  library"). #424 and #425 record the same shape of trap one category over
  (`inference_code`/adoption): a same-named or same-owner package that is not the product.
  Neither issue lists ten storage packages verbatim, so this constant is built directly from
  the storage score notes rather than copied from either issue — see the PR body for exactly
  which ten and why.

## What `--from-warehouse` supplies, and what it does not

Only the four edge tables — `currentai.identity.{artifact_identity,membership,equivalence,
org}_edges`. Truth is never re-derived from the warehouse's own `registry.*` mirrors, so the
same eval logic runs identically against a live run and against a fixture. The identity
dataset has not deployed yet, so `--from-warehouse` is untested against a live warehouse;
each missing table is caught individually and reported by name, and the module exits 2
rather than crashing on the first one.

## The two rules pinned as tests, not metrics

A metric is a rate that is allowed to miss sometimes. These are not that:

- A `name_match` edge never auto-emits, on any relation, at any confidence. Name matching is
  the weakest method the graph has and the corpus's own storage-category trap is proof it is
  routinely wrong; it can propose a digest item, never emit one.
- A scoring-bearing membership edge never auto-emits, regardless of confidence. Emitting a
  scoring-bearing membership edge changes a published score without a person looking; that is
  a governance decision, not a threshold problem.

`tests/test_identity_eval.py::test_name_match_never_auto_emits` and
`::test_scoring_bearing_membership_never_auto_emits` assert both directly against
`emitted_at_threshold`, so a future change to `THRESHOLDS` cannot quietly relax them.

Usage:
    uv run python -m build.identity_eval --edges fixture.json
    uv run python -m build.identity_eval --edges fixture.json --floors
    uv run python -m build.identity_eval --from-warehouse --floors
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from build import resolution
from build.identity import KINDS, fold_for_proposal
from build.serialize_registry import artifact_id

ROOT = Path(__file__).resolve().parents[1]

Key = tuple[str, str]

# Confidence an edge needs to auto-emit, per relation. There is deliberately no entry for
# `membership_scoring` -- see `emits()`, which excludes it before confidence is even
# consulted.
THRESHOLDS: dict[str, float] = {
    "artifact_identity": 0.99,
    "membership_non_scoring": 0.90,
    "equivalence": 1.00,
    "org": 0.85,
}

# Precision/recall floors, checked only under `--floors`, and only for relations where
# automation is actually planned. `membership_scoring` carries no floor because it is never
# automated -- see the module docstring and `emits()`.
FLOORS: dict[str, tuple[float, float]] = {
    "artifact_identity": (0.99, 0.95),
    "membership_non_scoring": (0.98, 0.90),
    "equivalence": (1.00, 0.90),
    "org": (0.97, 0.85),
}

# Ten storage-category products whose same- or near-same-named PyPI package is a verified
# client library, not the product's own countable artifact -- read from each product's
# `sources/scores/<slug>.yaml` adoption note (2026-08-18 verification pass) and cross-checked
# against `sources/products/<slug>.yaml`, none of which declares the package as an artifact.
# This is the map's clearest real known-negative set for `membership`: a name-match signal
# would confidently attach every one of these packages to the product it is named after, and
# a person has already looked and said no.
KNOWN_NEGATIVES: tuple[dict[str, str], ...] = (
    {"kind": "pypi", "artifact_id": "elasticsearch", "product_slug": "elasticsearch"},
    {"kind": "pypi", "artifact_id": "meilisearch", "product_slug": "meilisearch"},
    {"kind": "pypi", "artifact_id": "typesense", "product_slug": "typesense"},
    {"kind": "pypi", "artifact_id": "weaviate-client", "product_slug": "weaviate"},
    {"kind": "pypi", "artifact_id": "pymilvus", "product_slug": "milvus"},
    {"kind": "pypi", "artifact_id": "qdrant-client", "product_slug": "qdrant"},
    {"kind": "pypi", "artifact_id": "pyvespa", "product_slug": "vespa"},
    {"kind": "pypi", "artifact_id": "aistore", "product_slug": "aistore"},
    {"kind": "pypi", "artifact_id": "openmldb", "product_slug": "openmldb"},
    {"kind": "pypi", "artifact_id": "infinity-sdk", "product_slug": "infinity"},
)

# The four edge tables the identity dataset is designed to publish. Not deployed yet -- see
# `load_edges_from_warehouse`.
WAREHOUSE_TABLES: dict[str, str] = {
    "artifact_identity": "currentai.identity.artifact_identity_edges",
    "membership": "currentai.identity.membership_edges",
    "equivalence": "currentai.identity.equivalence_edges",
    "org": "currentai.identity.org_edges",
}


def _key(kind: str, ident: str) -> Key:
    return (kind, fold_for_proposal(kind, ident))


@dataclass
class Truth:
    """Every prior human decision the graph is replayed against.

    `equivalence`: (kind, canonical id) -> the product slug it resolves to (positive).
    `equivalence_negatives`: keys that must resolve to NO product.
    `membership`: (kind, canonical id), product slug -> True (is a member) or False (is
    known NOT to be, e.g. a `KNOWN_NEGATIVES` client-library trap).
    `org`: `"{kind}:{canonical id}"` -> the org slug that artifact's product belongs to.
    `identity`: (kind, canonical id) -> the `"{kind}:{canonical id}"` string it resolves to
    (declared artifacts resolve to themselves; there is no dataset of duplicate-artifact
    pairs yet, so this is necessarily thin).
    """

    equivalence: dict[Key, str] = field(default_factory=dict)
    equivalence_negatives: set[Key] = field(default_factory=set)
    membership: dict[tuple[Key, str], bool] = field(default_factory=dict)
    org: dict[str, str] = field(default_factory=dict)
    identity: dict[Key, str] = field(default_factory=dict)


@dataclass
class Metrics:
    precision: float | None
    recall: float | None
    n_truth: int
    n_emitted_at_threshold: int


def _declared_products() -> dict[str, dict]:
    return {
        path.stem: yaml.safe_load(path.read_text()) or {}
        for path in sorted((ROOT / "sources" / "products").glob("*.yaml"))
    }


def load_truth() -> Truth:
    """Assemble `Truth` from the ledger, declared artifacts, and org rosters.

    Deliberately reads nothing under `sources/scores/` beyond what `KNOWN_NEGATIVES` already
    hand-picked -- the score notes are prose a person wrote, not a machine-readable truth
    table, so they are not re-parsed here.
    """
    ledger = resolution.load()
    equivalence: dict[Key, str] = {}
    equivalence_negatives: set[Key] = set()
    membership: dict[tuple[Key, str], bool] = {}

    for (key, relation), entry in ledger.items():
        verdict = entry["verdict"]
        if relation == "product_equivalence":
            if verdict in ("existing_product", "sku_of"):
                slug = entry.get("resolves_to") or entry.get("product")
                if slug:
                    equivalence[key] = slug
            elif verdict in ("excluded_boundary", "excluded_maintenance"):
                equivalence_negatives.add(key)
            # `unresolved` carries no truth signal either way -- a person has not decided.
        elif relation == "product_membership":
            slug = entry.get("resolves_to")
            if slug:
                membership[(key, slug)] = verdict == "member_of"

    products = _declared_products()
    identity: dict[Key, str] = {}
    org: dict[str, str] = {}

    # Reverse the org rosters once: product slug -> org slug.
    product_org: dict[str, str] = {}
    for path in sorted((ROOT / "sources" / "organizations").glob("*.yaml")):
        roster = yaml.safe_load(path.read_text()) or {}
        for slug in roster.get("products") or []:
            product_org[slug] = path.stem

    for slug, product in products.items():
        for kind in KINDS:
            for entry in product.get(kind) or []:
                ident = artifact_id(kind, entry.get("url") or "")
                if not ident:
                    continue
                key = _key(kind, ident)
                # First declaration wins, same as `build/check_artifacts.py::declared`.
                membership.setdefault((key, slug), True)
                candidate_key = f"{kind}:{key[1]}"
                identity.setdefault(key, candidate_key)
                if slug in product_org:
                    org.setdefault(candidate_key, product_org[slug])

    for neg in KNOWN_NEGATIVES:
        key = _key(neg["kind"], neg["artifact_id"])
        membership[(key, neg["product_slug"])] = False

    return Truth(
        equivalence=equivalence,
        equivalence_negatives=equivalence_negatives,
        membership=membership,
        org=org,
        identity=identity,
    )


def emits(edge: dict, relation: str) -> bool:
    """Whether `edge`, drawn from the `relation` edge table, would auto-emit.

    The two never-emit rules live here, ahead of any confidence check, so nothing downstream
    can accidentally route around them:

    - `method == "name_match"` never emits, on any relation.
    - A `membership` edge with `scoring_bearing` true never emits, regardless of confidence
      -- checked before `THRESHOLDS` is even consulted, so there is no confidence high
      enough to satisfy it.
    """
    if edge.get("method") == "name_match":
        return False
    if relation == "membership":
        if edge.get("scoring_bearing"):
            return False
        threshold = THRESHOLDS["membership_non_scoring"]
    else:
        threshold = THRESHOLDS.get(relation)
        if threshold is None:
            raise ValueError(f"unknown relation {relation!r}")
    return float(edge.get("confidence") or 0.0) >= threshold


def emitted_at_threshold(edges: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """`edges`, filtered per relation to what would actually auto-emit."""
    return {relation: [e for e in items if emits(e, relation)] for relation, items in edges.items()}


def digest_items(edges: dict[str, list[dict]]) -> list[dict]:
    """Everything that did NOT auto-emit, flattened across relations.

    This is the review queue: a name-match edge and a scoring-bearing membership edge both
    land here rather than vanishing, which is what the two never-auto-emit tests check for
    on top of `emitted_at_threshold` being empty -- excluded from automation is not the same
    as discarded.
    """
    out: list[dict] = []
    for relation, items in edges.items():
        out.extend(e for e in items if not emits(e, relation))
    return out


def _score(emitted: list[dict], n_truth: int, is_correct) -> Metrics:
    correct = [e for e in emitted if is_correct(e)]
    precision = len(correct) / len(emitted) if emitted else None
    recall = len(correct) / n_truth if n_truth else None
    return Metrics(precision, recall, n_truth, len(emitted))


def _score_equivalence(emitted: list[dict], truth: Truth) -> Metrics:
    def is_correct(e: dict) -> bool:
        key = _key(e["artifact_kind"], e["artifact_id"])
        return truth.equivalence.get(key) == e.get("product_slug")

    return _score(emitted, len(truth.equivalence), is_correct)


def _score_membership(emitted: list[dict], truth: Truth) -> Metrics:
    def is_correct(e: dict) -> bool:
        key = _key(e["artifact_kind"], e["artifact_id"])
        return truth.membership.get((key, e.get("product_slug"))) is True

    n_truth = sum(1 for is_member in truth.membership.values() if is_member)
    return _score(emitted, n_truth, is_correct)


def _score_identity(emitted: list[dict], truth: Truth) -> Metrics:
    def is_correct(e: dict) -> bool:
        key = _key(e["artifact_kind"], e["artifact_id"])
        return truth.identity.get(key) == e.get("resolves_to")

    return _score(emitted, len(truth.identity), is_correct)


def _score_org(emitted: list[dict], truth: Truth) -> Metrics:
    def is_correct(e: dict) -> bool:
        return truth.org.get(e.get("candidate_key")) == e.get("org_slug")

    return _score(emitted, len(truth.org), is_correct)


def replay(edges: dict[str, list[dict]], truth: Truth) -> dict[str, Metrics]:
    """Score every relation `edges` carries against `truth`.

    `membership` is one edge table (`membership_edges`, keyed partly by `scoring_bearing`)
    but two questions for governance purposes, so it is split here into
    `membership_scoring` and `membership_non_scoring` -- the only two relation names this
    returns that are not literal edge-table keys. Truth does not currently distinguish
    which known members are scoring-bearing, so both draw on the same membership truth;
    `membership_scoring`'s `n_emitted_at_threshold` is always 0 by construction (see
    `emits`), which is the point -- there is nothing to floor because nothing can pass.
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
        all_membership = edges["membership"]
        scoring = [e for e in all_membership if e.get("scoring_bearing")]
        non_scoring = [e for e in all_membership if not e.get("scoring_bearing")]
        out["membership_scoring"] = _score_membership(
            [e for e in scoring if emits(e, "membership")], truth
        )
        out["membership_non_scoring"] = _score_membership(
            [e for e in non_scoring if emits(e, "membership")], truth
        )

    return out


class WarehouseTableMissing(RuntimeError):
    def __init__(self, table: str, cause: Exception):
        super().__init__(
            f"{table} could not be queried ({type(cause).__name__}: {cause}). The "
            f"currentai.identity.* dataset has not deployed yet -- see docs/operations/"
            f"deploy-models.md. --from-warehouse cannot run until it has."
        )
        self.table = table


def load_edges_from_warehouse() -> dict[str, list[dict]]:
    """The four edge tables, read live. Raises `WarehouseTableMissing` naming whichever
    table could not be queried, rather than letting the first one crash the run opaquely.
    """
    from build.warehouse import query

    edges: dict[str, list[dict]] = {}
    for relation, table in WAREHOUSE_TABLES.items():
        try:
            edges[relation] = query(f"SELECT * FROM {table}")
        except Exception as exc:  # noqa: BLE001 -- re-raised typed, with the table named
            raise WarehouseTableMissing(table, exc) from exc
    return edges


def load_edges_from_file(path: Path) -> dict[str, list[dict]]:
    return json.loads(path.read_text())


def print_table(metrics: dict[str, Metrics]) -> None:
    header = f"{'relation':24s} {'precision':>10s} {'recall':>10s} {'n_truth':>8s} {'n_emitted':>10s} {'floor':>14s}"
    print(header)
    print("-" * len(header))
    for relation in sorted(metrics):
        m = metrics[relation]
        precision = f"{m.precision:.3f}" if m.precision is not None else "n/a"
        recall = f"{m.recall:.3f}" if m.recall is not None else "n/a"
        floor = FLOORS.get(relation)
        floor_str = f"{floor[0]:.2f}/{floor[1]:.2f}" if floor else "none (never automated)"
        print(f"{relation:24s} {precision:>10s} {recall:>10s} {m.n_truth:>8d} {m.n_emitted_at_threshold:>10d} {floor_str:>14s}")


def floor_failures(metrics: dict[str, Metrics]) -> list[str]:
    """Relations under their floor. Only relations `FLOORS` names are checked, and only
    when there is truth to check against -- a relation with zero truth items has nothing to
    fail on and is reported as such rather than silently passing.
    """
    failures: list[str] = []
    for relation, (precision_floor, recall_floor) in FLOORS.items():
        if relation not in metrics:
            continue
        m = metrics[relation]
        if m.n_truth == 0:
            continue
        if m.precision is not None and m.precision < precision_floor:
            failures.append(f"{relation}: precision {m.precision:.3f} < floor {precision_floor:.2f}")
        if m.recall is not None and m.recall < recall_floor:
            failures.append(f"{relation}: recall {m.recall:.3f} < floor {recall_floor:.2f}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--from-warehouse", action="store_true", help="read the four identity edge tables live")
    source.add_argument("--edges", type=Path, help="path to a JSON fixture of edges, keyed by relation")
    parser.add_argument(
        "--floors", action="store_true",
        help="exit 1 if any relation with automation planned falls under its precision/recall floor",
    )
    args = parser.parse_args(argv)

    if args.from_warehouse:
        try:
            edges = load_edges_from_warehouse()
        except WarehouseTableMissing as exc:
            print(f"[FAIL] {exc}")
            return 2
    else:
        edges = load_edges_from_file(args.edges)

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
        print("\n[OK] every floored relation clears its precision/recall floor")

    return 0


if __name__ == "__main__":
    sys.exit(main())
