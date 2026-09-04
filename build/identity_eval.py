"""Replay eval: score the identity graph's edges against prior human decisions.

The `currentai.identity.*` dataset (Phase 1) proposes edges -- an artifact belongs to a
product, two artifacts are the same product, an artifact's org -- at a confidence the
automation can act on. Before any of that is allowed to auto-emit, this module answers one
question: against every identity decision a person has already made, how often would the
graph have agreed?

## Fix rounds

Two rounds of review against the deployed SQL at
`/workspace/GitHub/oso-external/currentai-org/udms/identity_*.sql` shaped this module; the
full history is in
`.superpowers/sdd/2026-09-03-phase-1-identity-implementation/task-6-review.md` (findings
M1-M9, then F1-F5). What follows is the settled contract, not a chronology.

## The declared/pool tier split (F1)

The replay question is "would the graph have recovered what a person already declared" --
and truth (the ledger, `sources/products/*.yaml`, org rosters) is built entirely from
**declared** artifacts. `equivalence_edges`, `org_edges` and `artifact_identity_edges` are
NOT declared-only: they are sourced from `currentai.identity.artifact_nodes`, which spans
every tier -- `head`/`tail` (declared) and `pool` (undeclared candidates nobody has looked
at). Scoring precision/recall over the unfiltered edge set compares two populations that are
disjoint outside the `head`/`tail` slice, which makes a floor unsatisfiable no matter how
good the graph is -- the same defect M8 named for `membership_non_scoring`, recurring here
for `equivalence`/`org`/`artifact_identity` because their SQL, correctly, is not
declared-only.

So every edge in those three tables carries `candidate_tier` (`head`/`tail`/`pool` --
`membership` needs no equivalent column: it is sourced only from
`registry.product_artifacts`/`tail_products`, so it is declared-only already, per its own SQL
header). `replay` splits on it:

- **Precision and recall** are computed over `head`/`tail` edges only -- the population truth
  actually covers. This answers "would the graph have recovered what was already declared".
- **`n_emitted_at_threshold` and `digest_items`** are computed over `pool` edges only -- the
  population automation would actually act on, since a `head`/`tail` artifact is already
  known and has nothing to discover. A `head`/`tail` edge that fails to emit is not a review
  queue item; it is scoring data.

`membership` is unaffected -- it has no pool population to split, so its edges feed both
computations the way they did before this split existed.

## Where truth comes from

Never the warehouse. `Truth` is assembled entirely from repo sources that are readable in
CI with no `OSO_API_KEY`:

- `build.resolution.load()` -- the resolution ledger, read via `.values()` through
  `_equivalence_from_ledger` / `_membership_from_ledger` (pure functions over raw ledger
  entries, not the loader's dict-key identity -- see above). An `existing_product`/`sku_of`
  ruling is a positive `product_equivalence` answer, keyed on `candidate_key`
  (`"<kind>:<folded id>"`, matching the deployed `equivalence_edges`/`org_edges` contract);
  `excluded_boundary`/`excluded_maintenance` is a negative one (the artifact must never
  resolve to *any* product). A `member_of`/`not_member_of` ruling is a positive or negative
  `product_membership` answer, keyed on `(artifact_kind, folded artifact_id, product_slug)`.
- `sources/products/*.yaml` -- every artifact a HEAD product declares is a positive membership
  truth. Two or more DISTINCT declared spellings of the same kind that fold to the same
  comparison key are `artifact_identity` truth (a fold-collapse pair) -- there are none in
  the corpus today, so this truth set is empty; see `test_artifact_identity_truth_is_empty_today`.
- `sources/registry/*.yaml` -- the TAIL. A tail row is a declaration too: somebody wrote down
  that this artifact is this product's, owned by this org, and the replay question ("would the
  graph have recovered what a person already declared") does not care which tier the
  declaration sits in. Tail rows contribute membership truth, `org` truth, and any fold-collapse
  pairs they form with each other or with a head spelling. Read through
  `build.serialize_registry.tail_product_rows`/`load_registry` -- the same derivation
  `registry.tail_products` is built from, so which fields count as artifacts and how a
  homepage is reduced cannot drift between the table and this eval. Every truth item carries
  its `tier`, so the table reports the head/tail split of each relation's `n_truth` rather than
  quietly pooling them.
- `sources/organizations/*.yaml` -- each org's `products:` roster, bridged through a
  product's declared artifacts, gives `candidate_key -> org_slug` truth. A tail row names its
  org directly (`org:`), which is the same truth one step shorter; a tail org need not have an
  `sources/organizations/<slug>.yaml` file at all, and most today do not.
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

Membership truth is keyed on `(artifact_kind, folded artifact_id, product_slug)`, not on the
artifact alone: a `member_of` ruling for package X against product A and a `not_member_of`
for the SAME package against product B are two distinct truth items, not a contradiction.
`build.resolution.load()`'s own key widened to include `resolves_to` for
`product_membership` entries (#478) to represent exactly this, so its dict CAN now hold both
rulings without raising `DuplicateResolution`. This module still reads entries via
`resolution.artifact_of`/`relation_of` on each entry directly, never by parsing the loader's
dict-key shape (`_equivalence_from_ledger`/`_membership_from_ledger` both take an ITERABLE of
raw entries, e.g. `resolution.load().values()`) -- the key's exact shape has already changed
once since this module was written, and reading the entry's own fields is what stays correct
regardless of what it changes to next. See
`tests/test_identity_eval.py::test_membership_truth_keeps_two_products_for_one_artifact_distinct`,
which feeds two entries sharing one artifact key directly, without going through the loader,
so it does not depend on the loader's current or any future key shape either.

`org` truth is `candidate_key -> {org_slug, ...}`, a SET, not a single slug: two folded
artifacts in the corpus today genuinely belong to two orgs each
(`github:swe-bench/swe-bench` under both `princeton-nlp` and `princeton-nlp-openai`;
`huggingface_dataset:allenai/tulu-3-sft-mixture` under both `ai2` and
`allen-institute-for-ai`), and an earlier version of this module used `dict.setdefault`,
which silently kept only the first org read and scored the second as a false positive. Every
emitted org in the truth set for a candidate counts as correct.

## Org recall is measured per handle route, pair by pair

The graph can only recover an org through a declared handle in `sources/org_handles.yaml`
(`registry.org_handles` once published) -- there is no other route from an artifact to an org,
and a route runs from ONE artifact kind to ONE handle platform. So recoverability is a property
of the `(artifact, org)` PAIR, not of the org: whether the org declares a handle on the route
that this artifact's kind actually travels.

- `github:<owner>/<repo>` -- the org must declare a `github` handle whose folded value equals
  `<owner>`.
- `huggingface_model:<ns>/<name>`, `huggingface_dataset:<ns>/<name>` -- a `huggingface` handle
  equal to `<ns>`.
- `homepage:<host><path>` -- a `homepage_domain` handle equal to `<host>`, or a parent domain of
  it (`acme.com` covers `docs.acme.com`).
- `pypi`, `npm`, `crates`, `arxiv` -- no owner concept in the identifier at all, so no route
  exists and no handle could ever bridge one. These are excluded from org recall entirely.

An earlier version restricted recall to pairs whose org declared **any** handle on **any**
platform, which was too generous in both directions at once: it kept a `pypi` pair (structurally
unrecoverable) because the org happened to declare a homepage, and it kept a `github` pair whose
org declares only a homepage domain. `ORG_ROUTES` and `org_pair_recoverable` replace that rule.

Precision truth is unchanged: every emitted org edge is judged against the FULL truth set, since
an edge to an org that declares no matching handle is either wrong (a real false positive) or a
graph capability this eval has no business hiding.

Two things keep the exclusion legible in the output. `Metrics.n_truth_unrecoverable`
(in the table for every relation, 0 except `org`) counts the pairs dropped from the recall
denominator, and `Metrics.unrecoverable_by_kind` breaks that down per artifact kind, printed
under the table -- so a structural exclusion (`pypi`) and a curation gap (a `github` artifact
whose org declares no `github` handle) are two readable numbers rather than one lump. And
`org_handle_coverage` is now per route: for each route, how many of the orgs that actually have
artifacts on it declare the handle it needs.

## Recall is an invariant; handle coverage is the coverage metric

Recall and coverage answer two different questions, and conflating them is what made org
recall read 1.000 and mean nothing:

- **recall = does the resolver use the evidence we gave it.** Recoverable-pair recall is
  computed over exactly the pairs a declared handle could bridge, so recoverability is defined
  by the same route the graph emits on. That makes it a REGRESSION INVARIANT, not a coverage
  target: a miss is the resolver failing to use evidence it already has, which is a bug rather
  than a curation gap. `RECALL_INVARIANTS` pins it at >= 0.99 for `org`, it still exits 1 on
  failure under `--floors`, and the table labels that row `recall invariant` rather than
  `recall floor` so nobody reads a 1.000 as coverage.
- **coverage = have we given it enough evidence.** That is `org_handle_coverage`, per route:
  orgs with a handle on that route over orgs that own artifacts of that kind. Three routes,
  three numbers -- `github`, `huggingface`, `homepage_domain`.

Coverage carries no target floor yet; the `huggingface` route's numbers are pending the HF
handle review in issue #483, and a floor set before that lands would be a guess. What it
carries instead is a **baseline ratchet**: `tests/fixtures/identity_coverage_baseline.json`
pins today's `(with_handle, rostered)` per route, and a run exits 1 if any route's live ratio
falls BELOW its pinned ratio. So coverage can only go up. `--write-coverage-baseline`
rewrites that file from the live corpus; it is a deliberate act in its own commit, never
something a failing run does for itself, or the ratchet would ratchet nothing.

A route whose denominator falls to 0 passes vacuously -- there are no orgs on it to cover.
The comparison is by cross-multiplication rather than float division, so a pinned ratio is
never re-derived at a different precision than it was written at.

**The invariant is scored only under `--from-warehouse`.** A fixture is a snapshot of what the
warehouse emitted on the day it was taken; truth is the corpus as it is today. Declare one
product whose org already declares a matching handle and the fixture's recall drops below 0.99
through no fault of the resolver -- and the message a fixture failure prints ("the resolver
missed a pair a declared handle already bridges") would be a false accusation against a
resolver that emits the pair correctly and was simply never re-snapshotted. So
`invariant_failures` takes `live` and returns nothing in fixture mode, `floor_status` renders
the `org` row `recall invariant not evaluated (fixture)` rather than leaving a reader to infer
it from a passing run, and the PR-time fixture run keeps doing what a fixture can honestly do:
exercise the scoring math, the tier split, precision, and the schema end to end.

Floors are not treated this way. A floor asks whether the emitted edges were WRONG, which a
snapshot can answer -- an incorrect edge stays incorrect however old the snapshot is. Only
recall depends on the fixture being complete.

## What `--from-warehouse` supplies, and what it does not

Only the four edge tables -- `currentai.identity.{artifact_identity,membership,equivalence,
org}_edges` -- read with an explicit column list (never `SELECT *`, see `WAREHOUSE_COLUMNS`).
All three tiered relations' SQL FILES carry `candidate_tier` as of this writing, including
`artifact_identity_edges`; the DEPLOYED table can still lag the file it is built from --
verified live on 2026-09-03 (`artifact_identity_edges` was queryable and missing the column;
`equivalence_edges`/`org_edges` were not deployed at all yet). Read the live run's own error
rather than trusting a sentence here about what is deployed on any given day -- a column
mismatch exits 2 naming the column (`WarehouseQueryFailed`), a missing table exits 2 or 0
under `--allow-unprovisioned` (`WarehouseTableMissing`). Truth is never re-derived from the
warehouse's own `registry.*` mirrors, so the same eval logic runs identically against a live
run and against a fixture.

A missing table exits 2 naming it (or 0, under `--allow-unprovisioned`, ONLY when the failure
is specifically a table-not-found error -- see `_is_table_not_found` and F2 below; every other
failure, including a missing column, a bad key, or an expired `OSO_API_KEY`, exits 2
regardless of the flag). A missing REQUIRED column on an actual row exits 2 naming it too --
`validate_columns` checks before any `_score_*` function ever indexes a row, so no `KeyError`
can escape to a traceback in a scheduled run. Both `validate_columns` and `replay` reject an
edges dict keyed by anything outside `EDGE_RELATIONS` -- a renamed or misspelled relation
(`"orgs"` for `"org"`) raises rather than silently scoring nothing and reporting green.

`--allow-unprovisioned` (`--from-warehouse` only): treats a genuine missing-table error as
"not deployed yet" and exits 0 instead of 2, so the scheduled workflow is not red for months
while the identity dataset ships. It refuses to run at all -- exit 2, before touching the
warehouse -- once the repo records the dataset as deployed: either `warehouse/assets.yaml`
marks an `identity.*` asset `materialized: true`, or `warehouse/dependencies.yaml` carries an
`identity.*` contract with a `mirror` block. So the skip cannot outlive the deploy it is meant
to wait for. All seven models deployed on 2026-09-04 and are contracted, so the flag is refused
today and the workflow no longer passes it.

## Insufficient truth, not a floor that can never be met

A relation's floor is enforced only when `n_truth >= MIN_TRUTH` (20). Below that, the table
prints `insufficient truth (n)` for that relation and `--floors` cannot exit 1 on it --
`artifact_identity` (0 truth pairs today) would otherwise floor on data that cannot possibly
satisfy it, which is exactly the review's M8.

`membership_non_scoring` was in the same position until tail declarations became truth: the
only artifact kind with no adoption route is `homepage`, no head product declares one, and the
tail rows that do were not being read. They are now, which puts the relation over `MIN_TRUTH`
and under a real floor for the first time. Clearing that floor is the graph's job; a floor that
now bites is the point of counting the truth, not a reason to raise `MIN_TRUTH`.

## `membership_non_scoring` has no headroom, so read its failures twice

Its truth set is the tail's homepage declarations and nothing else -- 27 today. One wrong or
missing edge is a ~3.7% swing, which is already more than the 0.98 precision floor allows. Two
things that are not regressions land as a failure on that row, and `FLOOR_NOTES` prints both
next to it so a log alone is enough to tell them apart:

- **Publish lag.** Truth is the repo; the edges are the warehouse. A tail homepage row edited or
  deleted in `sources/registry/*.yaml` is still emitted from the last published
  `registry.tail_products` until the weekly publish lands, so the scheduled Monday run can go
  red on precision for an edit that is already correct. The fix is a republish, not a graph
  change -- diff `sources/registry/*.yaml` against the published table before reading it as a
  defect.
- **A stale fixture.** The committed pass fixture carries the corpus's tail rows, so the same
  edit makes the PR-time fixture run fail too. `--write-fixture` regenerates that block, and
  `test_the_pass_fixture_tail_rows_match_the_corpus` fails first, naming the fixture, so the
  floor message is not the only thing pointing at it.

Neither is a reason to widen the floor or raise `MIN_TRUTH`. The relation is small because the
tail's homepage coverage is small; it gets headroom by the corpus growing.

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
    uv run python -m build.identity_eval --write-coverage-baseline
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path

import yaml

from build import resolution
from build.identity import KINDS, fold_for_proposal, fold_handle
from build.serialize_registry import artifact_id, load_registry, tail_product_rows
from build.validate import _load_optional_yaml

ROOT = Path(__file__).resolve().parents[1]
ASSETS_PATH = ROOT / "warehouse" / "assets.yaml"
DEPENDENCIES_PATH = ROOT / "warehouse" / "dependencies.yaml"

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
#
# `org`'s recall floor is `None` on purpose: recoverability is defined by the same handle route
# the graph emits on, so its recall is not a coverage measure and does not belong in a table of
# coverage floors. It is checked as a regression invariant instead -- see `RECALL_INVARIANTS`
# and the module docstring's "Recall is an invariant" section.
FLOORS: dict[str, tuple[float, float | None]] = {
    "artifact_identity": (0.99, 0.95),
    "membership_non_scoring": (0.98, 0.90),
    "equivalence": (1.00, 0.90),
    "org": (0.97, None),
}

# Recall levels that are regression invariants rather than coverage floors: a miss means the
# resolver failed to use evidence it already has. Checked under `--floors` exactly like a floor
# (same `MIN_TRUTH` gate, same exit 1), and labeled `recall invariant` in the table so a 1.000
# is never misread as coverage.
RECALL_INVARIANTS: dict[str, float] = {"org": 0.99}

# Below this many truth items, a floor cannot mean anything -- see the module docstring on
# `artifact_identity`, 0 in the corpus today.
MIN_TRUTH = 20

# Printed under a floor failure for the named relation. What goes here is the reading a log
# alone cannot supply: which failures are not regressions. See the module docstring's
# "membership_non_scoring has no headroom" section for the arithmetic.
FLOOR_NOTES: dict[str, str] = {
    "membership_non_scoring": (
        "this relation's entire truth set is the tail's homepage declarations (27 today), so a\n"
        "  SINGLE wrong or missing edge is a ~3.7% swing -- there is no headroom by construction.\n"
        "  Two non-regressions look like this failure. (1) A tail homepage row edited in the repo\n"
        "  is still emitted by the warehouse until the weekly registry publish lands, so a red\n"
        "  scheduled run soon after such an edit means republish, not regression -- check\n"
        "  sources/registry/*.yaml against the published registry.tail_products before reading it\n"
        "  as a graph defect. (2) On a fixture run, the fixture's own tail rows may be stale:\n"
        "  regenerate with `uv run python -m build.identity_eval --write-fixture <path>`."
    ),
}

ALL_RELATIONS = ("equivalence", "membership_scoring", "membership_non_scoring", "artifact_identity", "org")

# The artifact kind -> handle platform routes an artifact can reach an org through, and the only
# kinds `org` recall is measured over. A kind absent from this map carries no owner in its
# identifier -- `pypi:torch`, `npm:react`, `crates:serde`, `arxiv:2401.00001` name a package or a
# paper, never who publishes it -- so no handle on any platform could bridge it, and its truth
# pairs are counted unrecoverable rather than held against recall. See the module docstring.
ORG_ROUTES: dict[str, str] = {
    "github": "github",
    "huggingface_model": "huggingface",
    "huggingface_dataset": "huggingface",
    "homepage": "homepage_domain",
}

# How each route is labeled in the `handle coverage` line, in print order.
ORG_ROUTE_LABELS: tuple[tuple[str, str], ...] = (
    ("github", "github handles"),
    ("huggingface", "hf handles"),
    ("homepage_domain", "homepage handles"),
)

# What a route's coverage denominator is named in that same line.
ORG_ROUTE_ARTIFACTS: dict[str, str] = {
    "github": "github",
    "huggingface": "hf",
    "homepage_domain": "homepage",
}

# Today's per-route handle coverage, pinned. A run exits 1 if any route's live ratio falls
# below the ratio pinned here; `--write-coverage-baseline` is the only thing that rewrites it.
# It sits under `tests/fixtures/` with the eval's other committed inputs rather than in
# `sources/`: it is a gate's reference value, not a declaration about any product.
COVERAGE_BASELINE_PATH = ROOT / "tests" / "fixtures" / "identity_coverage_baseline.json"

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

# Explicit column lists for `--from-warehouse` -- never `SELECT *`. All three tiered
# relations' SQL FILES carry `candidate_tier` (see the module docstring for the caveat that
# the deployed table can still lag the file it is built from -- confirmed true, live, for
# `artifact_identity_edges` on 2026-09-03).
WAREHOUSE_COLUMNS: dict[str, tuple[str, ...]] = {
    "artifact_identity": (
        "artifact_kind", "artifact_id_a", "artifact_id_b", "candidate_tier", "confidence",
        "method", "penalties",
    ),
    "membership": (
        "artifact_kind", "artifact_id", "product_tier", "product_slug", "confidence", "method",
        "penalties", "scoring_bearing",
    ),
    "equivalence": (
        "candidate_key", "artifact_kind", "candidate_tier", "product_tier", "product_slug",
        "confidence", "method", "penalties",
    ),
    "org": ("candidate_key", "artifact_kind", "candidate_tier", "org_slug", "confidence", "method", "penalties"),
}

# The columns `_score_*` actually indexes. A row missing one of these cannot be scored --
# `validate_columns` catches it before any `_score_*` function runs, so no `KeyError` escapes.
# `scoring_bearing` is required for `membership`, not merely defaulted, because a missing flag
# defaulting to "not scoring-bearing" would be exactly the kind of fail-open the governance
# rule exists to prevent. `candidate_tier` is required on the three tiered relations because a
# missing value would land in NEITHER the declared nor the pool bucket in `_tier_split`,
# silently zeroing out a metric rather than raising.
REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "artifact_identity": ("artifact_kind", "artifact_id_a", "artifact_id_b", "candidate_tier"),
    "membership": ("artifact_kind", "artifact_id", "product_slug", "scoring_bearing"),
    "equivalence": ("candidate_key", "product_slug", "candidate_tier"),
    "org": ("candidate_key", "org_slug", "candidate_tier"),
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


def _check_known_relations(edges: dict[str, list[dict]]) -> None:
    """Raises if `edges` carries a key outside `EDGE_RELATIONS` -- a rename or a typo
    (`"orgs"` for `"org"`) must not silently score as "not evaluated" and print green (F3).
    """
    unknown = sorted(set(edges) - set(EDGE_RELATIONS))
    if unknown:
        raise ValueError(f"unknown edge relation(s) {unknown!r}; expected one of {EDGE_RELATIONS}")


def emitted_at_threshold(edges: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """`edges`, filtered per relation to what would actually auto-emit."""
    return {relation: [e for e in items if emits(e, relation)] for relation, items in edges.items()}


def digest_items(edges: dict[str, list[dict]]) -> list[dict]:
    """Everything that did NOT auto-emit, flattened across relations -- the review queue.
    A name-match edge and a scoring-bearing membership edge both land here rather than
    vanishing, which is what the two never-auto-emit tests check on top of
    `emitted_at_threshold` being empty: excluded from automation is not discarded.

    Restricted to `pool`-tier rows for the three relations that carry `candidate_tier` --
    the review queue is what automation might actually propose, and a `head`/`tail` edge
    names an artifact that is already declared, so a person reviewing the queue has nothing
    to do with it. `membership` has no tier column (its SQL is declared-only already), so its
    rows are unfiltered, as before the F1 tier split existed.
    """
    out: list[dict] = []
    for relation, items in edges.items():
        candidates = items if relation == "membership" else _tier_split(items)[1]
        out.extend(e for e in candidates if not emits(e, relation))
    return out


def _tier_split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """(declared, pool) -- `rows` split on `candidate_tier`. `declared` is `head`/`tail`, the
    population `Truth` is built from; `pool` is undeclared candidates, the population
    automation might actually act on. A row with a missing or unrecognized `candidate_tier`
    lands in neither bucket, silently zeroing out a metric rather than raising -- this
    function does not itself validate the value, and does not assume its caller did either.
    `validate_columns` DOES check the tier vocabulary (`TIER_VALUES`) for any caller that runs
    it first, which is every path through `main` (SF1) -- but `replay`/`_score_tiered` can
    still be called directly, e.g. from a test, without that check.
    """
    declared = [r for r in rows if r.get("candidate_tier") in ("head", "tail")]
    pool = [r for r in rows if r.get("candidate_tier") == "pool"]
    return declared, pool


def _equivalence_key(e: dict) -> tuple:
    return (e.get("candidate_key"), e.get("product_slug"))


def _org_key(e: dict) -> tuple:
    return (e.get("candidate_key"), e.get("org_slug"))


@dataclass
class Truth:
    """Every prior human decision the graph is replayed against.

    `equivalence`: candidate_key -> the product slug it resolves to (positive).
    `equivalence_negatives`: candidate_keys that must resolve to NO product.
    `membership`: (artifact_kind, folded artifact_id, product_slug) -> True (is a member) or
    False (is known NOT to be -- a ledger `not_member_of` or a `KNOWN_NEGATIVES` entry). Two
    verdicts against the SAME artifact for two different products are two distinct keys, not
    a collision -- see `_membership_from_ledger`.
    `org`: candidate_key -> the SET of org slugs that artifact's product(s) belong to (not a
    single slug -- two folded artifacts in the corpus genuinely belong to two orgs each; see
    the module docstring's F5 note). Any org in the set counts as correct.
    `identity_pairs`: `{(artifact_kind, folded_a, folded_b)}` for declared spelling pairs that
    fold to the same comparison key (folded_a == folded_b by construction -- see the module
    docstring). Empty in the corpus today.
    `route_kinds`: artifact kinds `sources/signal_routing.yaml` compiles at least one adoption
    route for -- used only to split membership truth into scoring/non-scoring buckets for
    `n_truth`, mirroring `identity_membership_edges.sql`'s own `scoring_bearing` derivation.
    `org_handles`: `org_slug -> platform -> {folded handle, ...}`, read from
    `sources/org_handles.yaml` -- the graph's only route from an artifact to an org, and what
    `org_pair_recoverable` consults per pair to decide whether a truth pair belongs in `org`'s
    recall denominator (see the module docstring "Org recall is measured per handle route").
    `org` precision truth is unrestricted.

    The four `*_tier` maps carry the declaring tier (`"head"`/`"tail"`) of each truth item, so
    the table can report the split. A key absent from one of them has no known tier -- a ledger
    ruling naming a product slug that is neither a head product nor a tail row, say -- and
    counts toward `n_truth` but neither `n_head` nor `n_tail`. `org_tier` prefers `"head"` where
    a pair is declared in both tiers, since the head declaration is the stronger record.
    """

    equivalence: dict[str, str] = field(default_factory=dict)
    equivalence_negatives: set[str] = field(default_factory=set)
    membership: dict[tuple[Key, str], bool] = field(default_factory=dict)
    org: dict[str, set[str]] = field(default_factory=dict)
    identity_pairs: set[tuple[str, str, str]] = field(default_factory=set)
    route_kinds: frozenset[str] = field(default_factory=frozenset)
    org_handles: dict[str, dict[str, frozenset[str]]] = field(default_factory=dict)
    equivalence_tier: dict[str, str] = field(default_factory=dict)
    membership_tier: dict[tuple[Key, str], str] = field(default_factory=dict)
    org_tier: dict[tuple[str, str], str] = field(default_factory=dict)
    identity_tier: dict[tuple[str, str, str], str] = field(default_factory=dict)


@dataclass
class Metrics:
    precision: float | None
    recall: float | None
    n_truth: int
    n_emitted_at_threshold: int
    # Truth pairs excluded from `n_truth`/recall because no handle route could recover them --
    # only meaningful for `org`; 0 for every other relation. `unrecoverable_by_kind` breaks the
    # same count down per artifact kind, which is what separates a structural exclusion (`pypi`
    # has no owner in its identifier) from a curation gap (a `github` artifact whose org
    # declares no `github` handle).
    n_truth_unrecoverable: int = 0
    unrecoverable_by_kind: dict[str, int] = field(default_factory=dict)
    # The head/tail split of `n_truth`. These need not sum to `n_truth`: a truth item whose
    # declaring tier is unknown counts in neither (see `Truth`'s `*_tier` maps).
    n_truth_head: int = 0
    n_truth_tail: int = 0


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


def _equivalence_from_ledger(entries: Iterable[dict]) -> tuple[dict[str, str], set[str]]:
    """(positive, negative) equivalence truth, keyed on `candidate_key`.

    `entries` is an iterable of raw ledger ENTRY dicts -- `build.resolution.load().values()`,
    or any list of entries shaped the same way (e.g. `sources/resolution_ledger.yaml`'s
    `resolutions:` list). Reads `resolution.artifact_of`/`relation_of` off each entry directly
    rather than parsing the loader's own dict-key shape -- see `_membership_from_ledger` for
    why that matters: the loader's key shape is `(artifact, relation)` for
    `product_equivalence` but `(artifact, relation, resolves_to)` for `product_membership`
    (`build/resolution.py::key_for`, #478), and this module has no business assuming either
    shape holds.
    """
    positive: dict[str, str] = {}
    negative: set[str] = set()
    for entry in entries:
        if resolution.relation_of(entry) != "product_equivalence":
            continue
        verdict = entry["verdict"]
        ck = candidate_key(*resolution.artifact_of(entry))
        if verdict in ("existing_product", "sku_of"):
            slug = entry.get("resolves_to") or entry.get("product")
            if slug:
                positive[ck] = slug
        elif verdict in ("excluded_boundary", "excluded_maintenance"):
            negative.add(ck)
        # `unresolved` carries no truth signal either way -- a person has not decided.
    return positive, negative


def _membership_from_ledger(entries: Iterable[dict]) -> dict[tuple[Key, str], bool]:
    """Membership truth, keyed on `(artifact_kind, folded artifact_id, product_slug)`.

    `entries` is an iterable of raw ledger ENTRY dicts (see `_equivalence_from_ledger`), read
    via `resolution.artifact_of`/`relation_of` rather than the loader's own dict-key identity.
    `build.resolution.load()` used to enforce uniqueness per bare `(artifact, relation)`,
    which could not represent a `member_of` ruling for artifact X against product A alongside
    a `not_member_of` for the SAME X against product B -- #478 widened the loader's own key to
    `(artifact, relation, resolves_to)` for `product_membership`, fixing that at the source.
    This function still groups on the full `(artifact, resolves_to)` pair itself rather than
    trusting whatever shape the loader's key happens to be, so it stays correct independently
    of that key's exact shape -- `tests/test_identity_eval.py::
    test_membership_truth_keeps_two_products_for_one_artifact_distinct` feeds two entries
    sharing one artifact key without going through the loader at all.
    """
    out: dict[tuple[Key, str], bool] = {}
    for entry in entries:
        if resolution.relation_of(entry) != "product_membership":
            continue
        slug = entry.get("resolves_to")
        if slug:
            out[(resolution.artifact_of(entry), slug)] = entry["verdict"] == "member_of"
    return out


ORG_HANDLES_PATH = ROOT / "sources" / "org_handles.yaml"


def _org_handles(path: Path = ORG_HANDLES_PATH) -> dict[str, dict[str, frozenset[str]]]:
    """`org_slug -> platform -> {folded handle, ...}` from `sources/org_handles.yaml`.

    Reuses `build.validate._load_optional_yaml` -- the same loader `validate_sources` reads
    this file with -- so an older tree that predates the file (no `sources/org_handles.yaml`
    at all) reads as "no org declares a handle" rather than raising, exactly as it does there.
    """
    doc = _load_optional_yaml(path, {"version": 1, "handles": []})
    by_org: dict[str, dict[str, set[str]]] = {}
    for entry in doc.get("handles") or []:
        if not isinstance(entry, dict):
            continue
        org_slug, platform, handle = entry.get("org"), entry.get("platform"), entry.get("handle")
        if not (isinstance(org_slug, str) and isinstance(platform, str) and isinstance(handle, str)):
            continue
        by_org.setdefault(org_slug, {}).setdefault(platform, set()).add(fold_handle(platform, handle))
    return {org: {p: frozenset(h) for p, h in platforms.items()} for org, platforms in by_org.items()}


def _owner_segment(kind: str, folded_id: str) -> str | None:
    """The part of a folded artifact key a handle can be compared to, or None if the kind
    carries no owner. `github`/Hugging Face ids are `<owner>/<name>`; a folded homepage key is
    `<host><path>`, so the host is everything up to the first `/`.
    """
    if kind == "homepage":
        return folded_id.split("/", 1)[0] or None
    owner, separator, _name = folded_id.partition("/")
    return owner if separator and owner else None


def org_pair_recoverable(candidate_key_value: str, org_slug: str, truth: Truth) -> bool:
    """Whether the graph could reach `org_slug` from this artifact through a declared handle.

    True only when the artifact's kind has a handle route (`ORG_ROUTES`) AND the org declares a
    handle on that route matching the artifact's owner segment. A `homepage_domain` handle also
    matches a subdomain of itself (`acme.com` covers `docs.acme.com`), which is the one route
    where the declared handle is deliberately broader than the artifact -- an org publishes one
    domain and hangs product pages off it. The other routes are exact.
    """
    kind, _, folded = (candidate_key_value or "").partition(":")
    route = ORG_ROUTES.get(kind)
    if route is None:
        return False
    owner = _owner_segment(kind, folded)
    if not owner:
        return False
    handles = truth.org_handles.get(org_slug, {}).get(route) or frozenset()
    if route == "homepage_domain":
        return any(owner == handle or owner.endswith(f".{handle}") for handle in handles)
    return owner in handles


def org_handle_coverage(truth: Truth) -> dict[str, tuple[int, int]]:
    """Per route: `(orgs declaring the handle that route needs, orgs with artifacts on it)`.

    The denominator is the population that route's recall is actually drawn from -- orgs that
    own at least one artifact of a kind travelling that route -- not every rostered org, which
    would mix a missing `huggingface` handle into `github`'s coverage and back.
    """
    per_route: dict[str, tuple[set[str], set[str]]] = {
        route: (set(), set()) for route in ORG_ROUTES.values()
    }
    for ck, orgs in truth.org.items():
        kind, _, _folded = ck.partition(":")
        route = ORG_ROUTES.get(kind)
        if route is None:
            continue
        with_handle, rostered = per_route[route]
        for org_slug in orgs:
            rostered.add(org_slug)
            if truth.org_handles.get(org_slug, {}).get(route):
                with_handle.add(org_slug)
    return {route: (len(with_handle), len(rostered)) for route, (with_handle, rostered) in per_route.items()}


def _repo_path(path: Path) -> str:
    """`path` as a repo-relative string where it is inside the repo, absolute otherwise -- so
    a message stays readable when a test points the constant at a tmp directory."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


class CoverageBaselineInvalid(RuntimeError):
    """`tests/fixtures/identity_coverage_baseline.json` is not a `{route: [with_handle,
    rostered]}` object over `ORG_ROUTES`' platforms. Raised rather than defaulted: a baseline
    that silently reads as empty is a ratchet that holds nothing.
    """


def load_coverage_baseline(path: Path = COVERAGE_BASELINE_PATH) -> dict[str, tuple[int, int]]:
    """The pinned per-route coverage, `route -> (with_handle, rostered)`.

    A missing file reads as `{}` -- an older tree that predates the ratchet has nothing to
    ratchet against, and that is not a failure. A file that EXISTS but is malformed raises:
    the whole point of the ratchet is that it cannot be defeated by accident.
    """
    if not path.exists():
        return {}
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise CoverageBaselineInvalid(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise CoverageBaselineInvalid(f"{path} must be an object of route -> [with_handle, rostered]")
    routes = set(ORG_ROUTES.values())
    out: dict[str, tuple[int, int]] = {}
    for route, pair in doc.items():
        if route not in routes:
            raise CoverageBaselineInvalid(
                f"{path} names route {route!r}, which is not one of {sorted(routes)}"
            )
        if not (isinstance(pair, (list, tuple)) and len(pair) == 2):
            raise CoverageBaselineInvalid(f"{path}: {route!r} must be [with_handle, rostered], got {pair!r}")
        with_handle, rostered = pair
        if not (isinstance(with_handle, int) and isinstance(rostered, int)):
            raise CoverageBaselineInvalid(f"{path}: {route!r} must be two integers, got {pair!r}")
        if with_handle < 0 or rostered < 0 or with_handle > rostered:
            raise CoverageBaselineInvalid(
                f"{path}: {route!r} = {pair!r} is not a coverage ratio (0 <= with_handle <= rostered)"
            )
        out[route] = (with_handle, rostered)
    return out


def write_coverage_baseline(
    coverage: dict[str, tuple[int, int]], path: Path = COVERAGE_BASELINE_PATH
) -> dict[str, tuple[int, int]]:
    """Pin `coverage` as the new baseline, in `ORG_ROUTE_LABELS` order. Returns what it wrote.

    Only `--write-coverage-baseline` calls this; nothing on the scoring path does.
    """
    doc = {route: list(coverage.get(route, (0, 0))) for route, _label in ORG_ROUTE_LABELS}
    path.write_text(json.dumps(doc, indent=2) + "\n")
    return {route: tuple(pair) for route, pair in doc.items()}  # type: ignore[misc]


def _below_baseline(live: tuple[int, int], pinned: tuple[int, int]) -> bool:
    """Is `live`'s ratio strictly below `pinned`'s? Cross-multiplied rather than divided, so a
    pinned ratio is never re-derived at a different precision than it was written at.

    A pinned denominator of 0 pins a ratio of 0 and nothing can fall below it; a live
    denominator of 0 leaves no orgs on the route to cover, so it passes vacuously (both fall
    out of the cross-multiplication without a special case).
    """
    live_n, live_d = live
    base_n, base_d = pinned
    return live_n * base_d < base_n * live_d


def coverage_ratchet(
    coverage: dict[str, tuple[int, int]], baseline: dict[str, tuple[int, int]]
) -> list[str]:
    """Routes whose live coverage fell below the pinned baseline, one message each.

    Only routes the baseline actually pins are checked -- a new route in `ORG_ROUTES` with no
    pinned value yet is reported as `no baseline` in the printed lines, not failed.
    """
    failures: list[str] = []
    for route, _label in ORG_ROUTE_LABELS:
        pinned = baseline.get(route)
        if pinned is None:
            continue
        live = coverage.get(route, (0, 0))
        if _below_baseline(live, pinned):
            failures.append(
                f"{route}: coverage {live[0]}/{live[1]} fell below the pinned "
                f"{pinned[0]}/{pinned[1]}"
            )
    return failures


def coverage_lines(
    coverage: dict[str, tuple[int, int]], baseline: dict[str, tuple[int, int]]
) -> list[str]:
    """The three `handle coverage` lines, one per route, each with its ratchet status."""
    lines = [
        "handle coverage (coverage = have we given the resolver enough evidence):",
    ]
    for route, label in ORG_ROUTE_LABELS:
        live_n, live_d = coverage.get(route, (0, 0))
        pinned = baseline.get(route)
        if pinned is None:
            status = "no baseline"
        elif _below_baseline((live_n, live_d), pinned):
            status = f"BELOW BASELINE {pinned[0]}/{pinned[1]}"
        else:
            status = f"at or above baseline {pinned[0]}/{pinned[1]}"
        lines.append(
            f"  {label:18s} {live_n:>4d}/{live_d:<4d} orgs with "
            f"{ORG_ROUTE_ARTIFACTS[route]} artifacts -- {status}"
        )
    return lines


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
    ledger_items = list(resolution.load().values())
    equivalence, equivalence_negatives = _equivalence_from_ledger(ledger_items)
    membership = _membership_from_ledger(ledger_items)

    products = _declared_products()
    # Tail declarations are truth too -- see the module docstring. Read through
    # `serialize_registry`'s own derivation so this eval and `registry.tail_products` cannot
    # disagree about which tail fields are artifacts.
    tail_rows = tail_product_rows(load_registry(ROOT))
    head_slugs = set(products)
    tail_slugs = {row["slug"] for row in tail_rows if row["slug"]}

    def tier_of_product(slug: str | None) -> str | None:
        if slug in head_slugs:
            return "head"
        if slug in tail_slugs:
            return "tail"
        return None

    # fold-collapse artifact_identity truth: distinct declared spellings of one kind that fold
    # to the same comparison key, from either tier. None exist in the corpus today (see the
    # module docstring), so this is deliberately built from first principles rather than
    # assumed empty.
    by_key: dict[Key, dict[str, str]] = {}
    for product in products.values():
        for kind in KINDS:
            for entry in product.get(kind) or []:
                ident = artifact_id(kind, entry.get("url") or "")
                if ident:
                    by_key.setdefault((kind, fold_for_proposal(kind, ident)), {})[ident] = "head"
    for row in tail_rows:
        kind, ident = row["artifact_kind"], row["artifact_id"]
        if ident:
            by_key.setdefault((kind, fold_for_proposal(kind, ident)), {}).setdefault(ident, "tail")

    identity_pairs: set[tuple[str, str, str]] = set()
    identity_tier: dict[tuple[str, str, str], str] = {}
    for (kind, _folded), spellings in by_key.items():
        if len(spellings) < 2:
            continue
        for a, b in itertools.combinations(sorted(spellings), 2):
            fa, fb = fold_for_proposal(kind, a), fold_for_proposal(kind, b)
            lo, hi = sorted((fa, fb))
            pair = (kind, lo, hi)
            identity_pairs.add(pair)
            # A pair spanning both tiers is recorded as head: the head declaration is the
            # stronger record, and a mixed pair counted twice would double the split.
            tier = "head" if "head" in (spellings[a], spellings[b]) else "tail"
            if identity_tier.get(pair) != "head":
                identity_tier[pair] = tier

    # Declared artifacts: positive membership truth, and org truth bridged through each
    # product's org(s). `product_org` is `product_slug -> {org_slug, ...}` -- a SET, not a
    # single value, because a product can be listed in more than one org's roster (e.g.
    # `swe-bench` under both `princeton-nlp` and `princeton-nlp-openai`); a plain assignment
    # here would have the same F5 bug one step removed.
    product_org: dict[str, set[str]] = {}
    for path in sorted((ROOT / "sources" / "organizations").glob("*.yaml")):
        roster = yaml.safe_load(path.read_text()) or {}
        for slug in roster.get("products") or []:
            product_org.setdefault(slug, set()).add(path.stem)

    membership_tier: dict[tuple[Key, str], str] = {}
    org: dict[str, set[str]] = {}
    org_tier: dict[tuple[str, str], str] = {}

    def record_org(ck: str, org_slug: str, tier: str) -> None:
        org.setdefault(ck, set()).add(org_slug)
        if org_tier.get((ck, org_slug)) != "head":
            org_tier[(ck, org_slug)] = tier

    for slug, product in products.items():
        for kind in KINDS:
            for entry in product.get(kind) or []:
                ident = artifact_id(kind, entry.get("url") or "")
                if not ident:
                    continue
                key = _membership_key(kind, ident)
                membership.setdefault((key, slug), True)
                membership_tier[(key, slug)] = "head"
                for org_slug in product_org.get(slug, ()):
                    record_org(candidate_key(kind, ident), org_slug, "head")

    # The tail, same two relations. A tail row names its org directly rather than through a
    # roster, and that org need not have a `sources/organizations/<slug>.yaml` file at all --
    # most tail orgs today do not, which is why their pairs land in `n_truth_unrecoverable`
    # (no file, no handles, no route) rather than dragging recall down.
    for row in tail_rows:
        kind, ident, slug = row["artifact_kind"], row["artifact_id"], row["slug"]
        if not (ident and slug):
            continue
        key = _membership_key(kind, ident)
        membership.setdefault((key, slug), True)
        if membership_tier.get((key, slug)) != "head":
            membership_tier[(key, slug)] = "tail"
        if row.get("org_slug"):
            record_org(candidate_key(kind, ident), row["org_slug"], "tail")

    # Ledger rulings carry no tier of their own; the product they name does.
    for (key, slug) in membership:
        if (key, slug) not in membership_tier:
            tier = tier_of_product(slug)
            if tier:
                membership_tier[(key, slug)] = tier
    equivalence_tier = {
        ck: tier for ck, slug in equivalence.items() if (tier := tier_of_product(slug))
    }

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
        org_handles=_org_handles(),
        equivalence_tier=equivalence_tier,
        membership_tier=membership_tier,
        org_tier=org_tier,
        identity_tier=identity_tier,
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


def _tier_counts(keys: Iterable, tiers: dict) -> tuple[int, int]:
    """`(n_head, n_tail)` over `keys`, read from a `Truth.*_tier` map. A key the map does not
    carry has no known tier and counts in neither, so these need not sum to `n_truth`.
    """
    counted = Counter(tiers.get(key) for key in keys)
    return counted["head"], counted["tail"]


def _score_equivalence(emitted: list[dict], truth: Truth) -> Metrics:
    def correct_fn(e: dict):
        ck, slug = e.get("candidate_key"), e.get("product_slug")
        if ck in truth.equivalence_negatives:
            return False, None
        ok = truth.equivalence.get(ck) == slug
        return ok, (ck if ok else None)

    metrics = _score(emitted, _equivalence_key, correct_fn, len(truth.equivalence))
    metrics.n_truth_head, metrics.n_truth_tail = _tier_counts(truth.equivalence, truth.equivalence_tier)
    return metrics


def _score_membership(emitted: list[dict], truth: Truth, scoring_bearing: bool) -> Metrics:
    def key_fn(e: dict):
        return (_membership_key(e.get("artifact_kind"), e.get("artifact_id")), e.get("product_slug"))

    def correct_fn(e: dict):
        k = key_fn(e)
        ok = truth.membership.get(k) is True
        return ok, (k if ok else None)

    counted = [
        (key, slug)
        for (key, slug), is_member in truth.membership.items()
        if is_member and (key[0] in truth.route_kinds) == scoring_bearing
    ]
    metrics = _score(emitted, key_fn, correct_fn, len(counted))
    metrics.n_truth_head, metrics.n_truth_tail = _tier_counts(counted, truth.membership_tier)
    return metrics


def _score_org(emitted: list[dict], truth: Truth) -> Metrics:
    """F5 fix: `truth.org` maps a candidate_key to a SET of org slugs, and ANY of them is
    correct -- a folded artifact genuinely belonging to two orgs must not score the second,
    correctly emitted org as a false positive. `n_truth` counts distinct
    `(candidate_key, org_slug)` PAIRS, not distinct candidate_keys, so a two-org artifact
    counts as two truth items for recall, not one.

    Recall truth is restricted to pairs `org_pair_recoverable` accepts -- the artifact's kind
    has a handle route and the org declares a matching handle on it (see the module docstring
    "Org recall is measured per handle route"); precision truth is not. `correct_fn` returns
    `tk = None` for a correct-but-unrecoverable match, which keeps it out of
    `matched_truth`/recall (via `_score` filtering `tk is not None`) while it still counts
    toward `n_correct`/precision, since `is_correct` is `True` either way.
    """

    def correct_fn(e: dict):
        ck, slug = e.get("candidate_key"), e.get("org_slug")
        ok = slug in truth.org.get(ck, ())
        recoverable = ok and org_pair_recoverable(ck, slug, truth)
        return ok, ((ck, slug) if recoverable else None)

    pairs = [(ck, slug) for ck, orgs in truth.org.items() for slug in orgs]
    recoverable_pairs = [pair for pair in pairs if org_pair_recoverable(*pair, truth)]
    metrics = _score(emitted, _org_key, correct_fn, len(recoverable_pairs))
    metrics.n_truth_unrecoverable = len(pairs) - len(recoverable_pairs)
    unrecoverable = set(pairs) - set(recoverable_pairs)
    metrics.unrecoverable_by_kind = dict(
        sorted(Counter(ck.partition(":")[0] for ck, _slug in unrecoverable).items())
    )
    metrics.n_truth_head, metrics.n_truth_tail = _tier_counts(recoverable_pairs, truth.org_tier)
    return metrics


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

    metrics = _score(emitted, _identity_pair, correct_fn, len(truth.identity_pairs))
    metrics.n_truth_head, metrics.n_truth_tail = _tier_counts(truth.identity_pairs, truth.identity_tier)
    return metrics


def _score_tiered(rows: list[dict], truth: Truth, relation: str, score_fn, key_fn) -> Metrics:
    """The F1 tier split: precision/recall over `head`/`tail` (declared) edges that pass
    `emits`, `n_emitted_at_threshold` over `pool` (undeclared) edges that pass `emits`.
    `score_fn` is one of `_score_equivalence`/`_score_org`/`_score_identity`; `key_fn` is its
    matching dedup key, reused here so the pool count dedupes the same way precision's
    denominator does.
    """
    declared, pool = _tier_split(rows)
    emitted_declared = [e for e in declared if emits(e, relation)]
    emitted_pool = [e for e in pool if emits(e, relation)]
    metrics = score_fn(emitted_declared, truth)
    pool_count = len({key_fn(e) for e in emitted_pool})
    # `replace`, not a positional rebuild: every field but the emitted count carries over, so a
    # new `Metrics` field cannot be silently dropped here the way a positional call would drop it.
    return replace(metrics, n_emitted_at_threshold=pool_count)


def replay(edges: dict[str, list[dict]], truth: Truth) -> dict[str, Metrics]:
    """Score every relation `edges` carries against `truth`.

    `equivalence`, `org` and `artifact_identity` are tier-split (F1): precision/recall are
    computed over `head`/`tail` edges (the declared population `truth` covers), while
    `n_emitted_at_threshold` is computed over `pool` edges (what automation would actually
    propose) -- see `_score_tiered` and the module docstring. `membership` has no tier
    column (its SQL is declared-only already) and is unaffected.

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
    _check_known_relations(edges)
    out: dict[str, Metrics] = {}

    if "equivalence" in edges:
        out["equivalence"] = _score_tiered(edges["equivalence"], truth, "equivalence", _score_equivalence, _equivalence_key)
    if "artifact_identity" in edges:
        out["artifact_identity"] = _score_tiered(edges["artifact_identity"], truth, "artifact_identity", _score_identity, _identity_pair)
    if "org" in edges:
        out["org"] = _score_tiered(edges["org"], truth, "org", _score_org, _org_key)
    if "membership" in edges:
        at_threshold = [e for e in edges["membership"] if emits(e, "membership")]  # already all non-bearing
        out["membership_non_scoring"] = _score_membership(at_threshold, truth, scoring_bearing=False)
        out["membership_scoring"] = _score_membership([], truth, scoring_bearing=True)

    return out


class WarehouseTableMissing(RuntimeError):
    """The table genuinely does not exist -- the only failure `--allow-unprovisioned` may
    swallow. See `_is_table_not_found`.
    """

    def __init__(self, table: str, cause: Exception):
        super().__init__(
            f"{table} does not exist ({type(cause).__name__}: {cause}). The "
            f"currentai.identity.* dataset has not deployed yet -- see docs/operations/"
            f"deploy-models.md."
        )
        self.table = table


class WarehouseQueryFailed(RuntimeError):
    """A query against `table` failed for a reason OTHER than the table not existing --
    auth, a timeout, a planner error, a missing column on an existing table. Always exits 2,
    `--allow-unprovisioned` or not: F2 -- the flag exists to cover exactly one signal
    ("not deployed yet"), and conflating it with every other failure class would let an
    expired `OSO_API_KEY` or a genuine schema break report "skipped" and stay green.
    """

    def __init__(self, table: str, cause: Exception):
        super().__init__(f"{table} could not be queried ({type(cause).__name__}: {cause})")
        self.table = table


# Trino's own wording for "this table does not exist" (and pyoso/PyStarburst wrapping of it),
# matched case-insensitively against the exception's string form. The real, verified text --
# confirmed live against currentai.identity.equivalence_edges and org_edges while both were
# undeployed -- is `USER_ERROR: TablesNotFound - Tables do not exist or are inaccessible:
# <table>` (a 404). A round-1 version of this list matched the singular "does not exist" and
# the underscored "table_not_found", neither of which appears in that camel-case, plural
# wording, so it never fired -- MF1. `tablesnotfound` (the camel-case error code, lowercased)
# and the plural phrase are the two markers that actually match the live text; `does not
# exist` and `table_not_found`/`TABLE_NOT_FOUND` are kept too, since Trino's own bare wording
# for a missing table elsewhere in its error surface uses the singular. Deliberately narrow:
# any OTHER failure -- auth, timeout, a missing column on a table that DOES exist -- must
# exit 2 and never be read as "not provisioned yet".
_TABLE_NOT_FOUND_MARKERS = (
    "tablesnotfound",
    "do not exist or are inaccessible",
    "does not exist",
    "table_not_found",
    "table not found",
)


def _is_table_not_found(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _TABLE_NOT_FOUND_MARKERS)


class EdgeColumnMissing(RuntimeError):
    def __init__(self, relation: str, column: str):
        super().__init__(
            f"{relation} edges are missing required column {column!r} -- schema drift from "
            f"the deployed SQL contract this eval reads (see WAREHOUSE_COLUMNS/REQUIRED_COLUMNS)."
        )
        self.relation = relation
        self.column = column


# The only tier tokens any deployed model emits. SF1: a redeployed SQL that changes the tier
# vocabulary or its casing (`'Head'`, or a fourth tier) must not silently zero out a metric --
# `_tier_split` puts an unrecognized value in neither bucket with no error of its own.
TIER_VALUES = frozenset({"head", "tail", "pool"})

# Which column(s) on each relation carry a tier value that must be in `TIER_VALUES`.
# `equivalence` carries two independent tiers -- `candidate_tier` (the artifact) and
# `product_tier` (the product it resolves to) -- and both are checked; `membership` has only
# `product_tier` (it has no candidate_tier column at all, being declared-only already).
TIER_COLUMNS: dict[str, tuple[str, ...]] = {
    "artifact_identity": ("candidate_tier",),
    "membership": ("product_tier",),
    "equivalence": ("candidate_tier", "product_tier"),
    "org": ("candidate_tier",),
}


class EdgeValueInvalid(RuntimeError):
    def __init__(self, relation: str, column: str, value: object):
        super().__init__(
            f"{relation} edges: column {column!r} = {value!r}, not one of {sorted(TIER_VALUES)}"
        )
        self.relation = relation
        self.column = column
        self.value = value


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


def _identity_dataset_contracted(path: Path = DEPENDENCIES_PATH) -> list[str]:
    """`currentai.identity.*` tables `warehouse/dependencies.yaml` contracts with a mirror block.

    The identity models are platform-authored, so under ADR-003 they are dependency contracts and
    never governed assets -- `warehouse/assets.yaml` will not carry them, and
    `_identity_dataset_deployed` will keep returning `[]` however deployed the dataset is. A
    contract with a `mirror` block is the equivalent record: it pins a model id, a released
    revision and the hash of the mirrored code, none of which can be written for a table that
    does not exist. So it refuses `--allow-unprovisioned` for the same reason a materialized
    asset does.
    """
    if not path.exists():
        return []
    doc = yaml.safe_load(path.read_text()) or {}
    return sorted(
        str(d.get("table"))
        for d in (doc.get("dependencies") or [])
        if str(d.get("table", "")).startswith("currentai.identity.") and (d.get("mirror") or {})
    )


def load_edges_from_warehouse() -> dict[str, list[dict]]:
    """The four edge tables, read live with an explicit column list per table.

    Raises `WarehouseTableMissing` when the failure's own text says the table does not exist
    (`_is_table_not_found`) -- the only case `--allow-unprovisioned` may treat as "not
    deployed yet". Every other query failure -- auth, timeout, a missing column, a planner
    error -- raises `WarehouseQueryFailed`, which always exits 2 (F2).
    """
    from build.warehouse import query

    edges: dict[str, list[dict]] = {}
    for relation, table in WAREHOUSE_TABLES.items():
        columns = ", ".join(WAREHOUSE_COLUMNS[relation])
        try:
            edges[relation] = query(f"SELECT {columns} FROM {table}")
        except Exception as exc:  # noqa: BLE001 -- re-raised typed, with the table named
            if _is_table_not_found(exc):
                raise WarehouseTableMissing(table, exc) from exc
            raise WarehouseQueryFailed(table, exc) from exc
    return edges


def load_edges_from_file(path: Path) -> dict[str, list[dict]]:
    return json.loads(path.read_text())


# The confidence and method a fixture's tail membership rows carry. Not a claim about what the
# deployed model emits for any particular row: 0.95 clears `membership_non_scoring`'s 0.90
# threshold, and `declared` is what a declaration-sourced membership edge is labeled, which is
# all the fixture needs to exercise the scoring path.
FIXTURE_TAIL_CONFIDENCE = 0.95
FIXTURE_TAIL_METHOD = ("declared",)


def tail_membership_rows(route_kinds: frozenset[str]) -> list[dict]:
    """The `membership` rows a fixture should carry for the tail, in `WAREHOUSE_COLUMNS` shape.

    Derived from the same `tail_product_rows` truth is, so a fixture regenerated with
    `--write-fixture` is the corpus's tail declarations and nothing else. `scoring_bearing`
    mirrors the deployed SQL's own derivation (does the kind have an adoption route), which is
    why this takes `route_kinds` rather than hardcoding `homepage`.
    """
    return [
        {
            "artifact_kind": row["artifact_kind"],
            "artifact_id": row["artifact_id"],
            "product_tier": "tail",
            "product_slug": row["slug"],
            "confidence": FIXTURE_TAIL_CONFIDENCE,
            "method": list(FIXTURE_TAIL_METHOD),
            "penalties": [],
            "scoring_bearing": row["artifact_kind"] in route_kinds,
        }
        for row in sorted(
            tail_product_rows(load_registry(ROOT)),
            key=lambda r: (r["slug"], r["artifact_kind"], r["artifact_id"]),
        )
    ]


def write_fixture(path: Path, route_kinds: frozenset[str]) -> tuple[int, int]:
    """Regenerate `path`'s tail membership rows from the tail registry, in place.

    Every other row and relation is left exactly as it was -- only `membership` rows with
    `product_tier: "tail"` are replaced, so a hand-written head row keeps its wording and a
    regeneration diff shows the corpus change and nothing else. Returns `(rows removed, rows
    written)`.

    The fixture stays COMMITTED rather than being generated at test time on purpose: it is what
    the `identity-eval` workflow grades on every PR, and a gate that builds its own input from
    the corpus it then grades against cannot fail. Committing it keeps the tail block reviewable
    in a diff, and `test_the_pass_fixture_tail_rows_match_the_corpus` is what catches it going
    stale.
    """
    doc = json.loads(path.read_text())
    kept = [row for row in doc.get("membership") or [] if row.get("product_tier") != "tail"]
    generated = tail_membership_rows(route_kinds)
    removed = len(doc.get("membership") or []) - len(kept)
    doc["membership"] = kept + generated
    path.write_text(json.dumps(doc, indent=2) + "\n")
    return removed, len(generated)


def validate_columns(edges: dict[str, list[dict]]) -> None:
    """Every row of every relation `REQUIRED_COLUMNS` names carries those columns with a
    non-null value. Raises `EdgeColumnMissing` naming the first offending relation and
    column, rather than letting a `_score_*` function `KeyError` on a `None` deep inside a
    scheduled run. Also raises (via `_check_known_relations`) if `edges` carries a relation
    name outside `EDGE_RELATIONS` -- a typo must not be silently skipped (F3).

    Also checks (SF1) that every `TIER_COLUMNS` value is actually in `TIER_VALUES`, raising
    `EdgeValueInvalid` with the offending value otherwise -- a redeployed SQL that renames or
    recases a tier would otherwise pass this check, land in neither `_tier_split` bucket, and
    zero out a metric with nothing in the output pointing at the cause.
    """
    _check_known_relations(edges)
    for relation, rows in edges.items():
        required = REQUIRED_COLUMNS.get(relation) or ()
        tier_columns = TIER_COLUMNS.get(relation) or ()
        for row in rows:
            for column in required:
                if row.get(column) is None:
                    raise EdgeColumnMissing(relation, column)
            for column in tier_columns:
                value = row.get(column)
                if value is not None and value not in TIER_VALUES:
                    raise EdgeValueInvalid(relation, column, value)


def floor_status(relation: str, metrics: dict[str, Metrics], live: bool = True) -> str:
    """The status cell for `relation`, naming which rules were applied to it.

    The verdict is `checked (pass)`/`checked (FAIL)` as before, followed by the rules that
    produced it -- `precision floor`, `recall floor`, `recall invariant`. The label matters:
    `org`'s recall is a regression invariant, not a coverage floor (see the module docstring),
    and the table is where a reader learns which of the two they are looking at.

    `live=False` (a `--edges` run) renders a recall invariant as `recall invariant not
    evaluated (fixture)` and leaves it out of the verdict -- a fixture cannot answer the
    question the invariant asks. Defaults to `True` so a caller that forgets the argument
    grades rather than skips.
    """
    if relation not in metrics:
        return "not evaluated (edge table absent from input)"
    if relation not in FLOORS and relation not in RECALL_INVARIANTS:
        return "no floor (never automated)"
    m = metrics[relation]
    if m.n_truth < MIN_TRUTH:
        return f"insufficient truth ({m.n_truth} < {MIN_TRUTH})"
    p_floor, r_floor = FLOORS.get(relation, (None, None))
    invariant = RECALL_INVARIANTS.get(relation)
    # SF2: `precision is None` means the declared slice emitted nothing at all -- there is
    # nothing to have gotten wrong, so it ABSTAINS rather than reading as 0.0 and failing a
    # precision floor for a reason that is not a precision problem. `recall` is never None
    # here (n_truth >= MIN_TRUTH > 0 guarantees `_score` computed a real value), but the
    # fallback is kept for defensive symmetry with `floor_failures`.
    recall = m.recall if m.recall is not None else 0.0
    rules: list[str] = []
    ok = True
    if p_floor is not None:
        rules.append("precision floor")
        ok = ok and (m.precision is None or m.precision >= p_floor)
    if r_floor is not None:
        rules.append("recall floor")
        ok = ok and recall >= r_floor
    if invariant is not None:
        if live:
            rules.append("recall invariant")
            ok = ok and recall >= invariant
        else:
            rules.append("recall invariant not evaluated (fixture)")
    return f"checked ({'pass' if ok else 'FAIL'}): {', '.join(rules)}"


def floor_failures(metrics: dict[str, Metrics]) -> list[str]:
    """Relations under their floor. Only relations `FLOORS` names are checked, and only when
    `n_truth >= MIN_TRUTH` -- see `floor_status` for the same logic surfaced per-relation.
    `precision is None` (nothing emitted in the declared slice) abstains rather than failing
    (SF2); `recall` still fails on 0.0 -- "recovered none of the known truth" is always a real
    signal, unlike "wrong about zero emissions".

    A relation whose recall floor is `None` (`org`) is checked by `invariant_failures`
    instead; both are collected under `--floors` and both exit 1.
    """
    failures: list[str] = []
    for relation, (precision_floor, recall_floor) in FLOORS.items():
        if relation not in metrics:
            continue
        m = metrics[relation]
        if m.n_truth < MIN_TRUTH:
            continue
        if m.precision is not None and m.precision < precision_floor:
            failures.append(f"{relation}: precision {m.precision:.3f} < floor {precision_floor:.2f}")
        if recall_floor is None:
            continue
        recall = m.recall if m.recall is not None else 0.0
        if recall < recall_floor:
            failures.append(f"{relation}: recall {recall:.3f} < floor {recall_floor:.2f}")
    return failures


def invariant_failures(metrics: dict[str, Metrics], live: bool = True) -> list[str]:
    """Relations under a recall INVARIANT -- the resolver failed to use evidence it already
    has. Same `MIN_TRUTH` gate and same exit 1 as a floor; a different message, because the
    reading is different: this is a regression to debug in the resolver, not a curation gap to
    fill by declaring more handles. Coverage is what measures the latter.

    Returns `[]` when `live` is false. The invariant compares live edges against today's
    corpus, and a fixture is a snapshot of edges taken on an earlier corpus -- grading it there
    accuses the resolver of a miss the fixture's own age caused (see the module docstring).
    Defaults to `True`: forgetting the argument grades, it does not skip.
    """
    if not live:
        return []
    failures: list[str] = []
    for relation, invariant in RECALL_INVARIANTS.items():
        if relation not in metrics:
            continue
        m = metrics[relation]
        if m.n_truth < MIN_TRUTH:
            continue
        recall = m.recall if m.recall is not None else 0.0
        if recall < invariant:
            failures.append(
                f"{relation}: recall {recall:.3f} < invariant {invariant:.2f} -- the resolver "
                f"missed a pair a declared handle already bridges"
            )
    return failures


def print_table(metrics: dict[str, Metrics], live: bool = True) -> None:
    """The per-relation table, then the `org` unrecoverable breakdown under it.

    `n_head`/`n_tail` split `n_truth` by the tier that declared each truth item; they need not
    sum to `n_truth` (a ledger ruling naming neither a head product nor a tail row has no
    tier). The breakdown line prints only for relations that have one, which today is `org`.
    """
    header = (
        f"{'relation':24s} {'precision':>10s} {'recall':>10s} {'n_truth':>8s} "
        f"{'n_head':>8s} {'n_tail':>8s} {'n_emitted':>10s} {'n_unrecov':>10s}  status"
    )
    print(header)
    print("-" * len(header))
    for relation in ALL_RELATIONS:
        m = metrics.get(relation)
        precision = f"{m.precision:.3f}" if m and m.precision is not None else "n/a"
        recall = f"{m.recall:.3f}" if m and m.recall is not None else "n/a"
        print(
            f"{relation:24s} {precision:>10s} {recall:>10s} {(m.n_truth if m else 0):>8d} "
            f"{(m.n_truth_head if m else 0):>8d} {(m.n_truth_tail if m else 0):>8d} "
            f"{(m.n_emitted_at_threshold if m else 0):>10d} "
            f"{(m.n_truth_unrecoverable if m else 0):>10d}  {floor_status(relation, metrics, live)}"
        )
    for relation in ALL_RELATIONS:
        m = metrics.get(relation)
        if m and m.unrecoverable_by_kind:
            breakdown = ", ".join(f"{kind} {count}" for kind, count in m.unrecoverable_by_kind.items())
            print(f"\n{relation} truth with no handle route ({m.n_truth_unrecoverable}): {breakdown}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--from-warehouse", action="store_true", help="read the four identity edge tables live")
    source.add_argument("--edges", type=Path, help="path to a JSON fixture of edges, keyed by relation")
    source.add_argument(
        "--write-coverage-baseline", action="store_true",
        help=(
            f"recompute per-route handle coverage from the corpus, pin it in "
            f"{_repo_path(COVERAGE_BASELINE_PATH)}, and exit (scores nothing). This is "
            f"how the ratchet is RAISED, deliberately, in its own commit; a failing run never "
            f"rewrites its own baseline."
        ),
    )
    source.add_argument(
        "--write-fixture", type=Path, metavar="PATH",
        help=(
            "regenerate a fixture's tail membership rows from sources/registry/*.yaml and exit "
            "(scores nothing). Run this after a tail registry edit changes which artifacts the "
            "tail declares."
        ),
    )
    parser.add_argument(
        "--floors", action="store_true",
        help="exit 1 if any relation with automation planned and sufficient truth falls under its floor",
    )
    parser.add_argument(
        "--allow-unprovisioned", action="store_true",
        help=(
            "--from-warehouse only: a missing currentai.identity.* table exits 0 (\"not "
            "provisioned yet\") instead of 2. Refused -- exit 2, no query attempted -- if "
            "warehouse/assets.yaml already marks any identity.* asset materialized: true, or "
            "warehouse/dependencies.yaml contracts any identity.* table with a mirror block."
        ),
    )
    args = parser.parse_args(argv)

    if args.allow_unprovisioned and not args.from_warehouse:
        print("[FAIL] --allow-unprovisioned only applies to --from-warehouse")
        return 2

    if args.write_coverage_baseline:
        # Explicit path, not the bound default -- see the `--allow-unprovisioned` block below
        # for the same reason: a default parameter is bound once at definition time, so a test
        # that monkeypatches the module-level path would otherwise be ignored.
        pinned = write_coverage_baseline(org_handle_coverage(load_truth()), COVERAGE_BASELINE_PATH)
        print(f"{_repo_path(COVERAGE_BASELINE_PATH)}: pinned handle coverage")
        for route, label in ORG_ROUTE_LABELS:
            n, d = pinned[route]
            print(f"  {label:18s} {n}/{d}")
        return 0

    if args.write_fixture:
        removed, written = write_fixture(args.write_fixture, _route_kinds())
        print(
            f"{args.write_fixture}: replaced {removed} tail membership row(s) with {written} "
            f"derived from sources/registry/*.yaml"
        )
        return 0

    if args.from_warehouse:
        if args.allow_unprovisioned:
            # Explicit argument, not the default parameter: the default is bound once at
            # function-definition time, so a test that monkeypatches the module-level
            # ASSETS_PATH would otherwise be silently ignored here.
            deployed = _identity_dataset_deployed(ASSETS_PATH)
            contracted = _identity_dataset_contracted(DEPENDENCIES_PATH)
            if deployed or contracted:
                where = []
                if deployed:
                    where.append(
                        f"warehouse/assets.yaml already marks {', '.join(deployed)} "
                        f"materialized: true"
                    )
                if contracted:
                    where.append(
                        f"warehouse/dependencies.yaml already contracts "
                        f"{', '.join(contracted)} with a mirror block"
                    )
                print(
                    f"[FAIL] --allow-unprovisioned refused: {'; '.join(where)}. The identity "
                    f"dataset is deployed, so a missing table is a real failure, not an "
                    f"unprovisioned skip -- remove --allow-unprovisioned from the caller."
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
        except WarehouseQueryFailed as exc:
            # Never swallowed by --allow-unprovisioned -- see F2 and WarehouseQueryFailed's
            # own docstring. This is deliberately NOT an `except (WarehouseTableMissing,
            # WarehouseQueryFailed)` above with a branch inside: the flag must only ever be
            # able to suppress one exception TYPE, not one condition checked inside a shared
            # handler that a future edit could loosen.
            print(f"[FAIL] {exc}")
            return 2
    else:
        edges = load_edges_from_file(args.edges)

    try:
        validate_columns(edges)
    except (EdgeColumnMissing, EdgeValueInvalid, ValueError) as exc:
        print(f"[FAIL] {exc}")
        return 2

    truth = load_truth()
    metrics = replay(edges, truth)
    print_table(metrics, live=args.from_warehouse)

    coverage = org_handle_coverage(truth)
    try:
        baseline = load_coverage_baseline(COVERAGE_BASELINE_PATH)
    except CoverageBaselineInvalid as exc:
        print(f"[FAIL] {exc}")
        return 2
    print("")
    for line in coverage_lines(coverage, baseline):
        print(line)

    exit_code = 0

    # The ratchet is not gated on `--floors`: a floor is a judgment about the graph, while the
    # ratchet is a fact about the corpus, and it holds on every run that scores.
    ratchet = coverage_ratchet(coverage, baseline)
    if ratchet:
        print("\n[FAIL] handle coverage fell below its pinned baseline:")
        for line in ratchet:
            print(f"  {line}")
        print(
            f"\n  Coverage only ratchets up. Either restore the handles the corpus lost, or -- if\n"
            f"  the drop is deliberate (an org file removed, a route's population genuinely\n"
            f"  shrank) -- re-pin it on purpose with `uv run python -m build.identity_eval\n"
            f"  --write-coverage-baseline` in its own commit, saying why. Nothing rewrites\n"
            f"  {_repo_path(COVERAGE_BASELINE_PATH)} automatically."
        )
        exit_code = 1

    if args.floors:
        failures = floor_failures(metrics) + invariant_failures(metrics, live=args.from_warehouse)
        if failures:
            print("\n[FAIL] under floor or invariant:")
            for line in failures:
                print(f"  {line}")
            for relation, note in FLOOR_NOTES.items():
                if any(failure.startswith(f"{relation}:") for failure in failures):
                    print(f"\n  {relation}: {note}")
            exit_code = 1
        else:
            print("\n[OK] every checked relation clears its floors and invariants")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
