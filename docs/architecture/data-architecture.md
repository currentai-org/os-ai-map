# Gap Map data architecture

The stable architectural decisions and the target DAG for the Open Source AI Map data
pipeline. This document is normative: a rule stated here is not restated elsewhere, and a
document that needs it links here.

What is NOT here, deliberately: the delivery phases and the per-phase agent assignments.
Those are session-scoped and live outside the repository. Phase status and the retirement
ledger are in `migration-status.md` next to this file.

Two architecture decision records carry the ownership and namespace decisions in full:
`adr-001-repo-owns-scoring-semantics.md` and
`adr-002-registry-curated-catalog-discovered.md`.

The asset inventory this document specifies is `warehouse/assets.yaml`, gated by
`tests/test_assets_inventory.py`.

## 1. Objective

Rework the Gap Map data architecture so that every dataset, model, gate, and publication step has a clear semantic role, owner, grain, and dependency.

The target system must preserve the repository as the source of truth while allowing OSO to collect external observations, calculate candidate assessments, retain history, surface disagreements, and serve current releases at scale.

The architecture must make these distinctions explicit:

- **Declared:** accepted identity, policy, rubric, evidence, and assessment data in the repository.
- **Discovered:** external products and artifacts that may or may not belong in the curated map.
- **Observed:** measurements or source responses collected at a point in time.
- **Evaluated:** deterministic facts, candidate assessments, and reconciliation results produced from declarations and observations.
- **Released:** an internally consistent, versioned projection approved for downstream use.

The primary design rule is:

> Automate observations and deterministic derivations aggressively; automate acceptance cautiously.

No warehouse model or agent may silently replace an accepted assessment in `sources/`. Machine-produced changes return to the repository as reviewable proposals.

## 2. Current state

As of 2026-08-20:

- `sources/` is the authoritative corpus: 18 published categories and 522 products.
- CI validates and compiles the YAML into registry static models, a JSON payload, and published notebooks.
- `currentai.registry.product_scores` mirrors every published product and all three recorded axes.
- Openness is also recomputed in OSO through `evidence.product_evidence`, `scores.openness_facts`, and `scores.openness_computed`; `build/check_parity.py` compares the independent result with the repository.
- Adoption is recorded in the repository and measured through multiple channel-specific warehouse tables. It has no route-aware reconciliation gate.
- Capability is recorded and mirrored but not recomputed.
- `currentai.catalog` and the other peripheral OSO pipelines are out of scope (ADR-003): they model the OSO organization, not the Gap Map's data system, so they were externalized — frozen under platform ownership and removed from this repo's inventory and publisher.
- External measurements generally expose current state rather than a durable observation history.
- OSO does not yet support incremental models; the current normalized state must therefore become the first preserved timestamped snapshot rather than being mislabeled as an append-only history.
- Platform model source is mirrored read-only under `warehouse/models/<dataset>/`; those mirrors are **dependency contracts in `warehouse/dependencies.yaml`** (each carrying a `mirror:` block — the compatibility shims are the exception, governed assets in `assets.yaml`). The platform remains authoritative for the deployed models; a mirror binds provenance, not ownership.
- Dataset scheduling, model throttles, GitHub Actions schedules, and manual operations coexist. A configured cron is not treated as proof that a scheduled run fired. Verified 2026-08-20: of <!-- observed:2026-08-20 -->22 datasets, 13 carry `cronTimezone: America/New_York`, and 8 have a cron configured with `lastRunAt: null` — `signal_semanticscholar`, `signal_pypi`, `ai_demand_curve`, `state_of_os_ai`, `scores`, `events`, `metrics`, `entities`. The `scores` dataset is among them, which means the openness chain that `check_parity` compares against the repository has no observed scheduled run.
- Two platform tables have no repository source and no in-repo consumer: `currentai.scores.investment_ranking` and `currentai.scores.taxonomy`.
- The full org is <!-- observed:2026-08-20 -->22 datasets by `ListDatasets`, or 23 counting `datasette` — which `ListDatasets` omits because it holds two deployed models and no materialized tables, so a dataset-first sweep misses it (Phase 0b enumerated from `ListDataModels` instead and found it). The org held <!-- observed:2026-08-20 -->96 tables at that 2026-08-20 enumeration. Separately, and as a live derived count rather than a 2026-08-20 subset, the inventory currently tracks <!-- count:deployed_tables -->31 deployed tables in the datasets the repository maintains or reads from; the rest of the org's tables are separate analytical products. The two figures are different populations measured at different times — the 96 is a point-in-time org-wide observation, the <!-- count:deployed_tables -->31 is derived from `assets.yaml` on every run. See section 11.3 for how the <!-- count:deployed_tables -->31 reconciles with the inventory's size.

The redesign must evolve this system without interrupting the existing map, registry tables, notebooks, or website.

## 3. Architectural decisions

These decisions are part of the specification. Changing one requires an explicit architecture decision record rather than an incidental implementation choice.

### AD-1: The repository owns scoring semantics

The repository owns:

- product, organization, category, artifact, alias, and lineage identity;
- category membership and taxonomy;
- rubrics, dimensions, bands, routing, abstentions, and scoring policy;
- the canonical deterministic evaluator;
- accepted axis assessments;
- release construction.

OSO may execute repository-owned logic or materialize its output, but it must not contain an independently maintained interpretation of the same rubric indefinitely.

Scaling research to thousands of products does not change this ownership. Agents and warehouse models may generate observations and candidate assessments at scale; acceptance still occurs through a repository change.

### AD-2: OSO owns observation history and candidate computation

OSO owns:

- scheduled external collection;
- append-only normalized observations;
- current-measurement views;
- joins between declared identities and observations;
- candidate assessments;
- reconciliation and drift reports;
- queryable historical and release materializations.

### AD-3: `registry` and `catalog` have different meanings

Use both names.

- **`registry`** contains curated, authoritative declarations compiled from the repository.
- **`catalog`** contains externally discovered inventory that has not necessarily been accepted into the map.

The naming test is:

> If a curator controls whether the row exists, it belongs in `registry`. If a collector discovers the row, it belongs in `catalog`.

Measurements do not belong in either namespace. They belong in source-specific signal datasets or the normalized `observations` dataset.

### AD-4: Observations are append-only; current state is a view

Append-only observation history is the target contract. A new collection run should append a new observation rather than overwrite the prior one.

**Current platform constraint:** as of 2026-08-20, OSO does not support incremental models. Do not pretend that a full-refresh model is append-only, and do not build a brittle simulation from an ever-growing list of hardcoded snapshots. The initial implementation must:

1. publish a normalized full-refresh current-state model;
2. preserve the current data as the first immutable, UTC-timestamped baseline snapshot;
3. carry stable observation IDs and the time fields required by the eventual history table;
4. open a blocked issue for migration to an incremental model when OSO ships the feature.

The baseline snapshot is the seed for the future incremental table. Later full-refresh executions must not overwrite or relabel that baseline.

Convenience views may expose the latest valid observation per product and channel. Replaceable current-state views must never be mistaken for the historical store.

Corrections are represented by a superseding observation or explicit validity metadata, not destructive mutation of history.

### AD-5: Agreement means route-aware reconciliation, not equality

A measured band and a recorded assessment are not automatically comparable. Reconciliation must consider:

- `instrument_type` and the `metric_type` beneath it;
- product type;
- authoritative versus fallback route;
- measurement window and units;
- freshness;
- abstention policy;
- explicit exceptions or stronger evidence.

A disagreement on a non-authoritative fallback is a review signal. A disagreement on a fresh authoritative route without an accepted explanation is a release blocker.

### AD-6: Recompute the score corpus completely

At the current scale, deterministic score evaluation is cheap. Every relevant declaration change should recompute the complete published corpus.

Incrementalize expensive source collection, not scoring. Do not build fine-grained invalidation until full recomputation is measurably expensive.

### AD-7: A release is a versioned, atomic contract

Published outputs must identify the source commit and the complete set of inputs that produced them. A release manifest is published only after every required table and gate succeeds.

Consumers must be able to determine whether joined tables belong to the same release.

### AD-8: Openness parity is transitional

`openness_facts`, `openness_computed`, and `check_parity` remain during migration. They may be retired only after the repository-owned evaluator emits equivalent queryable trace tables and dual-running demonstrates complete agreement over multiple releases.

## 4. Target namespaces

The core scoring path uses four logical OSO datasets:

```text
registry + observations → evaluation → releases
```

`catalog` is a separate discovery inlet. Existing source-specific `signal_*` datasets remain collection owners and feed `observations`.

### 4.1 `currentai.registry`

Purpose: the compiled, authoritative declaration layer from `sources/`.

Existing tables remain unless a migration explicitly replaces them:

- `products`
- `organizations`
- `categories`
- `tail_products`
- `product_artifacts`
- `product_categories`
- `product_organizations`
- `product_lineage`
- `category_scoring_rules`
- `category_license_tiers`
- `category_dimensions`
- `category_deferrals`
- `adoption_bands`
- `adoption_routes` (new; see below)
- `license_aliases`
- `evidence_abstentions`
- `product_openness_evidence`
- `product_score_sources`
- `product_scores`

Add a normalized accepted-assessment table:

#### `registry.axis_assessments`

Grain: one row per `(declaration_version_id, product_slug, category_slug, axis)`.

This table depends only on declarations, so it keys on the declaration version and must NOT
carry a `release_id`.

Required columns:

```text
declaration_version_id
source_git_sha
product_slug
category_slug
product_type
axis                         openness | adoption | capability
status                       confirmed | held | not_applicable
recorded_value
recorded_class               nullable; openness class where applicable
basis                       axis-specific; see below
basis_detail
instrument_type              nullable; required for measured adoption bands
confidence
last_verified                REQUIRED when confirmed, NULL when held
hold_reason                  required when held
held_since                   required when held
decision_note
source_count
```

This table is a long-form companion to `registry.product_scores`. It does not replace the existing wide table during the migration.

Implemented 2026-08-25 as the repo-side builder `build/axis_assessments.py` (staged, not yet
materialized). It keys on `declaration_version_id` with no `release_id`, draws its published
population from the same `build_payload` roster the wide table uses, and enforces the status/field
contract at build time — a held axis carries no `last_verified`, a confirmed axis is dated and
cites at least one source. It compiles `confirmed` and `held` only; `not_applicable` stays deferred
(see below), so a capability recorded as `basis: n/a` is a `confirmed` axis with a null
`recorded_value`. Publishing is a maintainer step (`docs/operations/deploy-axis-assessments.md`).

Valid field combinations per `status`, so downstream models do not each invent an
interpretation of nulls:

| `status` | `recorded_value` | `last_verified` | Also required |
|---|---|---|---|
| `confirmed` | numeric, or a deliberate null | **REQUIRED** | `confidence`, `source_count` >= 1 |
| `held` | prior value may be retained, marked as retained | **MUST BE NULL** | `hold_reason`, `held_since` |
| `not_applicable` | null | see below | `basis`, explanation |

**A held axis must not carry `last_verified`.** This is the normative contract in
`docs/reference/evidence-and-freshness.md`, and getting it wrong has already shipped as a
defect. `last_verified` means the date on which *everything* in the axis was confirmed still
correct. A hold is by definition an axis "a re-read opened, worked, and honestly could not
settle" (`build/check_freshness.py`), so no such date exists. A held axis reaches the payload
as `basis: partial`, not through the fallback and not as `verified`.

An earlier draft of this section claimed the opposite, citing the queue line
"aws-neuron.adoption — Re-read 2026-08-13 and held at 3" as evidence that a held axis keeps its
date. That reading is backwards twice over. "Held at 3" means the score remained 3, not that the
axis remains in a verification hold — and the entry was removed from the queue precisely because
the value HAD been re-derived, which made the axis `confirmed`. Worse, `aws-neuron` is named in
`evidence-and-freshness.md` as one of three products — with `falcon` and
`qualcomm-ai-engine-direct` — that shipped `basis: verified` over an axis parked in the queue.
That was the live defect the `partial` state was added to fix on 2026-08-15. The one product
cited as proof was the documented example of the bug.

Two related rules follow from the same document and must not be re-derived:

- **Product freshness is the OLDEST confirmed axis, not the newest.** 176 of 472 products carry
  differing axis dates, so this is the common case. Publishing the newest "says at least one
  axis was confirmed then, which is a weaker claim wearing the stronger one's label — the same
  overstatement as publishing a held axis as verified".
- `latest_axis_confirmation` already exists as a DERIVED field emitted only where it differs.
  Do not add a maintained one.

**`not_applicable` needs a ruling before it is implemented.** Capability already records
`basis: n/a`, a dated judgment that the axis does not apply. If that judgment can go stale it is
a confirmed null, not an undated structural state, and the third status may be unnecessary.
Define exactly how existing `basis: n/a` records compile before adding the status; a deliberate
dated null is `confirmed` either way.

`basis` is axis-specific — openness records its rule basis, adoption its route and instrument,
capability its anchor or `n/a`. Either define the vocabulary per axis or split into
axis-specific columns; a single free-text `basis` across three axes is how the payload ends up
with three incompatible conventions in one column.

Product freshness stays DERIVED as the oldest required axis confirmation, per
`docs/reference/evidence-and-freshness.md`. Do not add a maintained `latest_axis_confirmation` field to this
table or anywhere else — that reintroduces exactly the hand-maintained duplicate the freshness
rule was written to remove.

#### `registry.adoption_routes`

Routing semantics are currently declared in `sources/signal_routing.yaml` and only partly
exported. `registry.adoption_bands` carries thresholds — `product_type`, `level`, `above`,
`reach`, `unit`, `signal_type` — and nothing else. Route order, artifact applicability,
authority, fallback status, caps, freshness thresholds and abstention behaviour are not
exported at all.

That is an AD-1 violation waiting to happen. Any evaluation SQL that needs to know which route
is authoritative would have to reinterpret `signal_routing.yaml` independently, which is a
second implementation of routing semantics living in the warehouse. The whole point of AD-1 is
that there is exactly one.

`signal_routing.yaml` routes by ARTIFACT KIND, not by product, and its abstention rule is
"produce no evidence rather than substitute a weaker source". Both must survive compilation.

Inspected 2026-08-20, `dimensions.adoption` carries seven routes whose fields are:

```text
source  column  signal_type  authority  confidence  unit  cap  cap_because  bands
applies_to_categories  requires_evidence  hand_authored  vocabulary
vocabulary_note  note  attribution_note
```

plus the dimension-level `aggregation` block, a list of named rules each carrying `rule_id`,
`method`, `scope` and `applies_to_instrument` (a route picks up its rule by matching
instrument, so the method string is declared once here rather than on every route). Two routes
have `source: null`, and only two of seven carry inline `bands`.

A single flat table cannot hold this without loss, so normalize:

```text
registry.adoption_routes            one row per route
registry.adoption_route_scopes      route x applicable category / product type
registry.adoption_route_band_sets   route x product type -> the band set that resolves it
registry.adoption_aggregation_rules named aggregation rules, bound to routes by instrument
registry.adoption_bands             existing; gains band_set_id
```

`registry.adoption_bands` had no `band_set_id` column — its columns were `product_type`,
`level`, `above`, `reach`, `unit`, `signal_type`. It now leads with `band_set_id`, the identity a
route resolves to: `route:<signal_type>` for a scale declared on its own route (stars, active
users), `type:<product_type>` for a per-product-type usage_volume ladder. The route-to-band link
is **not** a column on `adoption_routes` — it varies by product type, so it lives in
`registry.adoption_route_band_sets`, one row per valid route x product type. Evaluation joins that
table and abstains when no row exists (hardware usage_volume has none, because hardware is
qualitative), rather than reading a `type:*` sentinel and reinterpreting it.

`registry.adoption_routes` must preserve at minimum:

```text
route_id
route_order                  explicit; the YAML encodes precedence by list position
source                       nullable — two routes legitimately have none
source_column
artifact_kind                the source's declared artifact_key (so semanticscholar -> arxiv)
metric_type                  derived from column
instrument_type              the YAML's signal_type; usage_volume | stars_fallback | ...
authority                    declared per route; authoritative | secondary | fallback
hand_authored
confidence
unit
aggregation_rule_id          references adoption_aggregation_rules; method lives there once
cap
cap_reason                   the declared reason a cap applies
requires_evidence
freshness_days
abstain_rule
vocabulary                   qualitative vocabulary where the route declares one
routing_policy_version       the routing YAML version; NOT a release/declaration identity
```

`route_order` is precedence, and precedence is monotonic in authority: the five `authoritative`
routes come first, in list order, then the two `fallback` routes — the last resorts before
abstention. So the hand-authored `active_users` route (authoritative) precedes the
`stars_fallback` route, correcting a prior ordering where the authoritative hand-authored route
sat after the fallback stars route. Within the authoritative download channels the order is the
ADR-001 precedence `pypi > huggingface > stars`, so `pypi` leads the two Hugging Face routes.

The YAML's `signal_type` compiles to `instrument_type`; `metric_type` is derived from the
`column`; and `artifact_kind` is read from the source's declared `artifact_key` in the `sources:`
block (so `semanticscholar` compiles to `arxiv`, matching `registry.product_artifacts`, not a
guessed `paper`). `authority` is declared on each route and compiled, never inferred from the
instrument name. Those derivations are part of the compiler's contract, not something evaluation
infers — and an unknown source, column, instrument, authority, duplicate `route_id`, or dangling
band-set reference is a hard compiler error, not a warning.

The repository compiler owns these tables. Evaluation reads them and never reinterprets the
YAML. A route the compiler cannot express is a compiler bug to fix, not a case for evaluation to
special-case.

**Acceptance test is round-trip completeness**, not column presence: every semantic field in the
adoption portion of `signal_routing.yaml` is either compiled into these tables or explicitly
classified as documentation-only. `note`, `sum_note`, `attribution_note` and `vocabulary_note` are
prose and may be classified documentation-only; `source`, `column`, `signal_type`, `authority`,
`confidence`, `unit`, `cap`, `cap_because` (compiled as `cap_reason`), `applies_to_categories`,
`hand_authored`, `requires_evidence`, `vocabulary` and the `aggregation` block are semantic and
must compile. A field that is neither compiled nor classified fails the test.

`registry.product_scores` remains the stable compatibility table for current consumers. Moving it to `releases` is a future API migration, not part of the first implementation wave.

### 4.2 `currentai.catalog`

Purpose: discovered external inventory and candidate discovery.

Examples:

- discovered GitHub repositories;
- Hugging Face models and datasets;
- package indexes;
- long-tail product candidates;
- external project inventories.

Minimum common discovery fields:

```text
catalog_id
source
artifact_kind
artifact_id
artifact_url
display_name
first_seen_at
last_seen_at
source_run_id
candidate_product_slug       nullable
match_status                 unmatched | candidate | linked | rejected
```

The following do not belong in `catalog` long term:

- accepted category membership;
- recorded Gap Map scores;
- normalized measurements;
- repo-derived bridges presented as external inventory;
- frozen historical tables without an explicit historical label.

`currentai.catalog.stack_map` must be classified and migrated. Its curated identity and membership fields belong in `registry`; any compatibility output required by `scores.stack_contributors` should become an explicitly named compatibility view with a documented deprecation plan.

### 4.3 `currentai.observations`

Purpose: normalized measurements linked to accepted product identity, with append-only history as the target state.

Source-specific ingestion remains in datasets such as `signal_github`, `signal_huggingface`, and `signal_packages`. `observations` standardizes them without erasing their source semantics.

#### Transitional implementation while OSO lacks incremental models

Use three distinct objects so current state is never mislabeled as history:

- `observations.source_runs` — the run contract described below. Required from day one; ships now as a read-only control-plane snapshot (interim Option B, issue #355);
- `observations.product_adoption_current` — a full-refresh normalized model holding the current source state (the latest normalized values). It cannot filter or attribute those values by run until #355 binds observations to runs, so it makes no completeness claim; see the source_runs rules below;
- `observations.product_adoption_baseline` — the immutable first snapshot, backed by frozen bytes rather than a query. **Captured 2026-08-24T22:27:44Z** from the deployed `product_adoption_current` state, in Phase 2 and not deferred to Phase 2B: 654 rows over 392 products, file digest `84e0d574…a569`, content digest `3a942c39…9a9b`. §18 requires one preserved baseline snapshot for the whole temporary full-refresh period, and precisely because `product_adoption_current` is full-refresh (every run overwrites), those bytes would not have survived the next run had they not been frozen deliberately; waiting for 2B would have meant the first snapshot never existed. It anchors the future append-only history but did not wait for it. The capture records honestly that `source_run_id` is NULL for every one of the 654 rows and that no authoritative row-to-run binding exists (#355); no run id is inferred from timestamps or from `source_runs`. It is immutable from here — later full-refresh executions must not overwrite or relabel it;
- `observations.product_adoption` — the target incremental history table, created only after OSO incremental models are available.

#### The baseline is bytes, not a query

An immutable snapshot cannot be a SQL model that selects from live upstream tables: re-running
it produces a different result, which is the opposite of a baseline. The baseline is a frozen
data asset —

```text
warehouse/data/observations/product_adoption_baseline.parquet
```

— or a static platform model loaded from those exact bytes. A view or model may expose it as
`observations.product_adoption_baseline`, but the bytes are the baseline and the query is only
a presentation of them.

Record in `warehouse/assets.yaml`: capture timestamp, per-row `observed_at`, the included
source-run IDs, schema version, row count, content digest, and file digest. Do not refresh it
in place, and do not let the refresh path write to its path.

The capture of 2026-08-24 records all of these in the asset's `capture` block, and repeats them
with the full column schema and the writer settings in the committed receipt
`warehouse/audits/product_adoption_baseline.json`. Two digests, not one: `file_sha256` covers the
parquet bytes as written and is reproducible only under the recorded writer, because the parquet
footer carries the writer's own version string; `content_sha256` covers a writer-independent
canonical serialization of the rows and survives a library upgrade. The included source-run IDs
are the empty list, which is the honest value rather than a missing field — `source_run_id` is
NULL for all 654 rows and #355 has not yet made the binding derivable.

#### `observations.source_runs`

A current-state table cannot prove that a collector ran. Rows in
`product_adoption_current` cannot distinguish a successful run that returned identical values
from a successful run that returned zero rows, from a failed collector whose previous table
remained readable, from a source that never ran at all, from a partial run. All five look like
"the current value is what it was".

This table is required before reconciliation can honour the rule that a failed or stale source
does not silently reuse itself as current; it cannot be omitted.

**Transitional shape (interim Option B, issue #355).** The platform exposes no row-level run id
in the fetcher tables and no expected-scope field, so run completeness is not derivable from what
the control plane offers today. Until the live emitter of #355 lands — its platform mechanism may
come from OSO's incremental-model work (Kariba OSO-4705), but #355 closes on demonstrated row-to-run
binding, not on incremental shipping — `source_runs` is a
READ-ONLY snapshot of platform-retained run history, produced by `build/snapshot_source_runs.py`
against the control-plane `runs` API — **not** a SQL model that selects from upstream, and **not**
a live current-run manifest. It fetches every run the API still retains for each adoption source
dataset and is REPLACED wholesale on each capture; the committed receipt
(`warehouse/audits/source_runs.json`) is its point-in-time attestation, carrying coverage bounds,
per-dataset run counts, the resolved dataset name→id bindings, and a content digest.

Grain: one row per `(source_run_id, materialization_id)`. A run binds to the model it wrote
through `steps → materializations`, authoritatively and never by timestamp; a run that
materialized nothing emits one row with the materialization fields null, and a model materialized
more than once in a run emits one row per materialization.

```text
source_run_id                the run's own id
source_dataset_id            the dataset whose runs were queried
source_dataset_name          signal_github, signal_huggingface, ...
materialization_id           the Materialization node's own id (nullable)
table_id                     materialization.tableId — the materialized model/table (nullable)
model_name                   parsed from the owning step name (nullable)
dataset_id                   materialization.datasetId — where it wrote (nullable)
execution_status             platform run status: SUCCESS | FAILED | RUNNING | ...
trigger_type                 SCHEDULED | MANUAL
run_type                     the platform run type
actor_type                   user | system — normalized from requestedBy, never the id
queued_at / started_at / finished_at
materialized_at              materialization.createdAt (nullable)
error_class                  normalized error-type token, nullable — never raw error text
expected_scope               constant "unknown" (blocked on #355)
scope_status                 constant "unknown" (blocked on #355)
captured_at                  snapshot time — excluded from the content digest
```

**Fields blocked on #355 (the live emitter).** `expected_scope` and `scope_status` are the
constant `"unknown"` here, and there is no `observed_row_count` / `rejected_row_count` and no
row-level binding of an observation to the run that produced it. Real scope, real row counts, and
a row→run binding require either the UDM runtime writing its run id into output rows or a table
version atomically bound to a materialization id — neither of which the control plane offers
today — so they are deferred to #355 and must NOT be reconstructed from timestamps. The platform
mechanism #355 depends on (a UDM writing its run id into its output rows) may be provided by OSO's
incremental-model work (Kariba OSO-4705); #355 stays independently open until live row-to-run
emission and authoritative binding are demonstrated, and is not closed by incremental shipping alone.

Rules:

- `execution_status` is the platform's real run status; it is NOT scope. A `SUCCESS` means the
  run's steps executed without error, not that collection was complete. Reconciliation must
  therefore NOT read a `SUCCESS` carrying `scope_status = "unknown"` and no row-level binding as a
  fully valid current observation: an unbound success reconciles to `source_unavailable`, not to
  agreement.
- Reconciliation reports a missing or failed current run as its own condition, distinct from a
  product that has no applicable measurement. The first is an infrastructure failure; the
  second is a legitimate abstention. Collapsing them hides outages as data gaps.
- Before #355, `source_runs` can report source/model execution state, but it cannot filter,
  validate, or attribute individual observations by run. An unbound `SUCCESS` remains
  `source_unavailable` for reconciliation. After #355 provides authoritative row-to-run binding
  and scope, `product_adoption_current` may include only observations bound to
  `execution_status = "SUCCESS"` with matching scope.
- The observation identity is two things, not one. `observation_content_digest` is
  content-addressed over the normalized observation content alone; `observation_snapshot_id` is
  `SHA-256(domain + canonicalization_version + observation_content_digest)`, binding the
  canonicalization rule so a persisted id names the rule that produced it. Run identifiers are
  lineage, recorded in `observation_run_ids`, and are NOT inputs to either. Including them would
  give every re-run a new content digest even when nothing measured changed, which is the opposite
  of what the digest is for. Under one canonicalization contract, identical content means an
  identical digest and different content means a different one; the runs that produced it stay
  visible either way.

Reconciliation may proceed against `product_adoption_current`; it does not need to wait for incremental support. Historical trend claims must wait.

#### `observations.product_adoption`

Observations are ARTIFACT-level. Product-level measurement is a separate, deterministic
aggregation published in `evaluation`, not something reconciliation rediscovers.

The distinction matters because a product routinely declares several GitHub repositories or
several packages, and a single run measures each of them. A product-level grain collides on
exactly those products — the ones where aggregation semantics are least obvious.

Target grain after incremental support lands: one row per

```text
(
  product_slug,
  artifact_kind,
  artifact_id,
  channel,
  metric_type,
  measurement_window_days,
  observed_at,
  source_run_id
)
```

Required columns:

```text
observation_id               deterministic identifier over the grain above
product_slug
product_type
artifact_kind
artifact_id
channel                      github | huggingface | pypi | npm | crates | other
metric_type                  stars | downloads | weekly_active_users | customers |
                             paid_seats | citations | other
raw_value
unit
measurement_window_days      nullable
observed_at
ingested_at
source_dataset
source_table
source_run_id
source_record_id             nullable
is_valid
supersedes_observation_id    nullable
```

Note what is NOT here: no `measured_level`, no `measured_reach`, no `signal_type`. A band is
a judgment about a measurement, so it belongs to `evaluation`, and an instrument is a scoring
concept, not a property of the raw fact.

#### Metric is not instrument

The earlier draft used a single `signal_type` enum of
`stars | downloads | usage_volume | customers | other`, which mixes two levels. `stars` and
`downloads` are metrics; `usage_volume` is a scoring instrument; `customers` is a metric that
may support more than one instrument depending on policy. Worse, that enum does not match the
corpus. Measured 2026-08-20 across `sources/`, the recorded instruments are:

```text
usage_volume        292
reported_traction   111
stars_fallback       85
active_users         25
unknown              20
```

Keep the two vocabularies separate and carry both:

```text
metric_type       what was measured
                  stars | downloads | weekly_active_users | customers | paid_seats |
                  citations | other

instrument_type   what the measurement is being used as
                  usage_volume | active_users | reported_traction | stars_fallback | unknown
```

`metric_type` lives on the observation. `instrument_type`, `route_id` and `band_id` are
assigned in `evaluation` by the compiled routes of 4.1. Reconciliation compares
`instrument_type` and `route_id`; the underlying `metric_type` and `raw_value` are preserved
so a disagreement can be explained rather than merely detected.

Never rank or compare across different `instrument_type` values.

Rules:

- Never rank or compare a measured level across different `instrument_type` values. Raw
  observations carry `metric_type` only; comparability is an `evaluation` concern.
- Preserve `raw_value`, units, and measurement window even when a band is calculated.
- A missing applicable band produces an abstention, not a band borrowed from another product type.
- Identity joins use declared artifact identifiers, never fuzzy product names.
- Every observation must be traceable to a source run or equivalent immutable collection identifier.

#### `observations.product_adoption_current`

A stable current-state contract selecting the latest valid observation per the artifact
observation identity:

```text
(product_slug, artifact_kind, artifact_id, channel, metric_type, measurement_window_days)
```

Before #355, it holds the current source state and cannot filter or attribute observations by run: an unbound `SUCCESS` in `source_runs` stays `source_unavailable` for reconciliation, not a validated current observation. After #355 provides authoritative row-to-run binding and scope, it may include only observations bound to a run with `execution_status = "SUCCESS"` and matching scope. It begins as a full-refresh model; after the incremental history table exists, replace its implementation with a view over `observations.product_adoption` without changing the consumer-facing name or schema.

The view must use explicit ordering and tie-breaking. It must not use an unordered `MAX()` reduction that can combine fields from different rows.

Future observation families may include:

- `product_capability`
- `source_document_fetches`
- `artifact_activity`

Do not generalize prematurely. Adoption is the first vertical slice.

### 4.4 `currentai.evaluation`

Purpose: deterministic facts, candidate assessments, reconciliation, and traceability.

#### `evaluation.adoption_reconciliation`

Grain: one row per `(declaration_version_id, observation_snapshot_id, product_slug,
category_slug, route_id)`.

It keys on both identities because a reconciliation result depends on declarations AND
measurements. It receives no public `release_id` — a `release_id` exists only once that pair
has passed reconciliation and been adjudicated for publication.

Required columns:

```text
declaration_version_id
observation_snapshot_id
product_slug
category_slug
recorded_level
recorded_instrument_type
measured_level
measured_instrument_type
channel
raw_value
measurement_as_of
route_authority               authoritative | secondary | fallback | inapplicable
measurement_freshness         fresh | stale | unknown
status
delta
override_id                   nullable
explanation
evaluated_at
```

Allowed `status` values:

```text
agree
expected_difference
explicit_override
override_required
stale_measurement
unmeasured
route_mismatch
abstained
source_unavailable
```

Blocking behavior:

- `override_required` blocks release.
- `route_mismatch` blocks release when caused by inconsistent declarations; otherwise it enters a review queue.
- `source_unavailable` blocks release. The source-run contract distinguishes an infrastructure
  failure from a legitimate absence of measurement, and this status is how that distinction
  reaches the gate; without it a failed collector is indistinguishable from `unmeasured`.
- `agree`, `expected_difference`, `explicit_override`, `stale_measurement`, `unmeasured`, and `abstained` do not block by themselves.
- Every non-blocking disagreement must explain why it is non-blocking.

The initial implementation should report before it blocks. Establish and adjudicate the baseline first; only then enable the blocking transition.

#### Structured reconciliation overrides

If authoritative measurements legitimately differ from accepted assessments, record the exception as structured source data rather than searching prose for a reason.

Add `sources/reconciliation_overrides.yaml` only if the baseline demonstrates that such exceptions are required. Its schema should include:

```text
id
product_slug
axis
channel
recorded_value
reason
evidence_url
approved_at
expires_at
```

Requirements:

- Overrides are narrow to one product, axis, and `route_id`. Keying on channel alone is too
  coarse: one channel can serve several routes with different instruments and authorities, so a
  channel-keyed override silently covers routes it was never adjudicated against.
- Overrides expire and must be re-adjudicated.
- Validation rejects retired products, unknown channels, impossible values, missing reasons, and invalid dates.
- A matching measurement after the override was written does not silently extend its expiry.

#### `evaluation.product_adoption_measurements`

Observations are artifact-level; recorded assessments are product-level. Something must
aggregate one into the other, and reconciliation must not do it implicitly — that would put
aggregation semantics inside the gate that is supposed to check them.

Grain: one row per `(declaration_version_id, observation_snapshot_id, product_slug,
category_slug, route_id)`.

```text
declaration_version_id
observation_snapshot_id
product_slug
category_slug
product_type
route_id
channel
metric_type
instrument_type
aggregation_method           from registry.adoption_aggregation_rules
contributing_observation_ids the artifact observations that produced this row
raw_value
unit
measurement_window_days
band_set_id
measured_level               null when the route must abstain
measured_reach
route_authority
measurement_as_of
```

`contributing_observation_ids` is what makes the aggregation auditable: a product measured
across four repositories can be traced back to the four artifact observations and the rule that
combined them. Without it, a disputed band has no re-derivable basis.

The flow is then explicit, with one owner per step:

```text
artifact observations  ->  route selection      (registry.adoption_routes)
                       ->  product aggregation  (this table)
                       ->  banding              (registry.adoption_bands)
                       ->  reconciliation       (evaluation.adoption_reconciliation)
```

Both tables are built by repo-side release builders — `build/adoption_measurements.py` and
`build/adoption_reconciliation.py` — not by an in-warehouse UDM. This is forced by the identities:
`observation_snapshot_id` a UDM could compute from the warehouse content, but
`declaration_version_id` encodes the repository `source_git_sha` and the `sources/` content digest,
which the warehouse sandbox has no access to. The builder has the git checkout and reads the
warehouse, so it computes both identities at run time (`build/declaration_version.py`,
`build/observation_snapshot.py`) and stamps them onto the candidate rows — derived, not stored,
like the identities themselves. The route selection, aggregation and banding read the compiled routing
(`build/serialize_routing.py`, `build/serialize_rubric.py`) and reinterpret none of it; a routing
fact the builder needs but cannot read is a compiler bug to fix at the source.

Route selection is by DECLARED ARTIFACTS and never falls through: the winning route is the first
route, in precedence order, that is applicable — an artifact-driven route (pypi, huggingface,
github, arxiv, and the unbridged npm/crates) applies when the product declares that artifact kind
and the route is in scope; a hand-authored route (`active_users`, `reported_traction`) applies when
the product's recorded instrument names it. Selection spans ALL routes, not only machine ones, so
the declared precedence is executable: an authoritative `active_users` outranks fallback stars, and
an unbridged `npm`/`crates` route outranks stars, so such a product is left UNMEASURED on its
authoritative route rather than scored on a weaker observed one. The builder then looks for an
observation on the winning route only; a missing observation produces no measurement (reconciliation
records the unmeasured outcome), never a fall to a weaker route. Aggregation follows the compiled
rules: both `usage_volume` and `stars_fallback` sum across a family's artifacts
(`sum_stars_across_artifacts` matches the deployed compatibility model's `SUM(stargazers_count)` and
the recorded assessments), with the stars cap still enforced by the band set.

Reconciliation never compares across instrument types. A `delta` is computed only when the measured
and recorded instruments match; a cross-instrument row withholds it and is `route_mismatch` (an
authoritative instrument on either side — inconsistent declarations) or `expected_difference` (both
weak signals). Both evaluation tables carry `routing_policy_version`, stamped from the compiled
routes, so the routing policy that produced a row travels with it. `declaration_version.py`'s
binding is split accordingly: **bound** to the evaluation tables (proven by the column), and still
**pending** for `release_id`, which does not exist until Phase 8 — where the release identity must
then incorporate the reconciliation-policy version.

The builders are pure functions of their inputs (the identities passed in) so the logic is pinned
against the immutable Phase-2 baseline with fixed test identities; `build/serialize_evaluation.py`
reads the current table once and serializes both tables from that one atomic row set, and the OSO
publish is a maintainer step (`docs/operations/deploy-evaluation.md`).

`adoption_reconciliation` reports before it blocks (above) over EVERY recorded adoption assessment —
measured, unmeasured, and the deliberate nulls — one terminal outcome per applicable route. Today
every measured row is `source_unavailable`: `product_adoption_current` carries no `source_run_id`
(row binding is blocked on #355), so §4.3 forbids reading any current measurement as a validated
agreement. That status is the source-run contract reaching the gate, not a defect in the report; it
is the report's **accepted interim state** (§18), not a final one. The fuller status set is
assignable once #355 binds observations to runs — blocked follow-up whose platform mechanism may
come from OSO's incremental-model support (Kariba OSO-4705), though #355 closes on its own
row-to-run evidence, not on incremental shipping. The gate that consumes the fuller set is required
by AD-5 and activates then.

#### Repository-derived scoring trace

The repository-owned evaluator publishes three tables, built repo-side by
`build/axis_scoring_trace.py` and **deployed 2026-08-27** (`status: active` / `materialized: true`,
declaration `eb828b57b14d`) via the dedicated publisher `build/publish_scoring_trace.py`
(`docs/operations/deploy-scoring-trace.md`):

- `evaluation.axis_facts` — grain
  `(declaration_version_id, product_slug, category_slug, axis, dimension, part_index)`
- `evaluation.axis_rule_matches` — grain
  `(declaration_version_id, product_slug, category_slug, axis, rule_index)`
- `evaluation.axis_results` — grain
  `(declaration_version_id, product_slug, category_slug, axis)`

Together they make this chain queryable:

```text
result → matched rule → normalized fact → recorded evidence → source document
```

- **result** is `axis_results` — the score/class the evaluator produced, the `rule_index` it
  matched, the governing license tier, and `reproduces_recorded`, the dual-run agreement with the
  recorded score (true on every scored row today; the property `check_rubric` gates in CI, made
  queryable).
- **matched rule** is `axis_rule_matches` — each rung the ordered first-match-wins walk evaluated,
  in order, with its `outcome` (`fired` / `skipped` / `fell_through_tier` / `blocked_on_tier`). Its
  `rule_conditions` join back to `axis_facts` by dimension name.
- **normalized fact** is `axis_facts` — the value the formula reads for each declared dimension,
  plus the recorded license decomposed into one row per `+`-joined part, each resolved to its tier,
  and the governing `license_tier` the walk tests.
- **recorded evidence** and **source document** are NOT republished here — they already have
  owners. `axis_facts` joins to `registry.product_openness_evidence` (grain
  `product_slug, category_slug, dimension, part_index`, the recorded value and its grade) and to
  `registry.product_score_sources` (carrying `source_url`) on their natural keys.

All three are deterministic over declarations alone: they key on `declaration_version_id` and carry
the commit-scoped `source_git_sha` alongside; none carries a `release_id` or an
`observation_snapshot_id`. Only openness is scored by a deterministic ordered-rule walk, so `axis`
is `openness` on every row; the column is retained so the grain is forward-compatible. Adoption's
trace already exists as `evaluation.product_adoption_measurements`, and capability is recorded
verbatim.

**No second scoring implementation** — this is ADR-001's whole point. Every value is transcribed
from `build/check_rubric.py`, the single owner of the ladder walk: the rung walk is
`walk_formula_trace` (which `walk_formula`, and so `score_openness` / `check_parity` /
`check_recipe`, now projects), the facts are `trace_openness().facts`, and the per-part license
tiers are `resolve_license_parts` (which `license_tier` now projects). The trace cannot resolve a
fact, a tier or a rung outcome differently from the score, because both read the same primitives.

The `evaluator_version` cutover is a separate, gated step — see §4.5 and
`docs/operations/deploy-scoring-trace.md`. Building this evaluator does not flip the sentinel:
`declaration_version_id` folds in `evaluator_version`, so replacing `v0-no-repo-evaluator` re-keys
every declaration-keyed table corpus-wide, the already-deployed Phase-3 tables included, and is
done as its own coordinated republish rather than as a side effect of landing the trace.

### 4.5 `currentai.releases`

Purpose: atomic, consumer-facing snapshots and their provenance.

#### `releases.manifest`

Grain: one row per release.

Required columns:

```text
release_id
source_git_sha
source_content_digest
evaluator_version
registry_run_id
evaluation_run_id
created_at
published_at
status                       building | valid | failed | superseded
product_count
category_count
axis_assessment_count
blocking_finding_count
manifest_digest
```

#### Three identities, not one

A repository version, an observation snapshot, and a published release are three different
things. Deriving one ID from the declaration alone means the same commit reconciled today
and next week against different measurements produces different findings under the same
`release_id`, and a release cannot identify every input that affected its validity.

```text
declaration_version_id
  = source_git_sha + source_content_digest + evaluator_version

observation_content_digest
  = canonical digest of the normalized observation content

observation_snapshot_id
  = SHA-256(domain + canonicalization_version + observation_content_digest)

release_id
  = declaration_version_id + observation_snapshot_id + reconciliation_policy_version
```

`declaration_version_id` is derived by `build/declaration_version.py`, not stored: it embeds
`source_git_sha`, and no commit can record its own SHA, so the release builder (and any
consumer keying a candidate table) computes it from the resolved SHA at run time. Its
`source_content_digest` covers every authoritative declaration input under `sources/` — every
top-level entry is classified into exactly one of three buckets, gated so a new input cannot
escape the digest unnoticed:

- **declaration** (folded into the digest): `products`, `organizations`, `categories`,
  `scores`, `rubrics`, `taxonomy.yaml`, the long-tail `registry` seeds, and — beyond what
  `load_sources` returns — `evidence_policy.yaml` (which shapes serialized registry output) and
  `verification_queue.yaml` (which governs release eligibility), plus the `allowlists`;
- **policy** (excluded from the digest, its own version a pending downstream obligation):
  `signal_routing.yaml`, which publishes under `routing_policy_version` and is applied in the
  evaluation layer. That version must bind into `evaluation.adoption_reconciliation` /
  `release_id`; those tables do not exist yet, so the binding is recorded as an obligation and
  ratcheted into a real assertion when they land;
- **non-declaration** (excluded from the digest, with a reason): the frozen
  `sources/snapshots/long_tail.json` warehouse sample.

The derived score projections (`overall_score`, `tier`, `maturity`, `mature`) are excluded from
the digest by construction — they never live in `sources/`; they are the evaluator's
contribution, already named by `evaluator_version`.

These are exclusions from the **content digest**, not from the identity. `declaration_version_id`
is **commit-scoped**: it also carries `source_git_sha`, so any commit that touches
`signal_routing.yaml`, the frozen snapshot, or the derived projections changes the SHA and
therefore the id. What the digest buys is a content-addressed cross-check — two commits with
identical declaration content share a digest even though their SHAs differ, so a reconciliation
can distinguish a real declaration change from an unrelated one. Because the id is commit-scoped
and computed by tracked code over the working tree, it is derived only over a worktree that
agrees with `HEAD`: a dirty tracked file anywhere (dirty declarations, or dirty identity/evaluator
code), or an untracked file under `sources/` (a declaration the commit does not carry), is
refused unless an explicit diagnostic opt-in is given. The digest reads only git-tracked files, so
an untracked file cannot enter it silently; the guard additionally refuses it so the mismatch
surfaces.

Until the repository-owned evaluator lands (Phase 6), `evaluator_version` is a declared sentinel
`v0-no-repo-evaluator` — well-formed and forward-compatible, and deliberately not the empty
string, so the day a real evaluator version replaces it is a reviewed change that moves every id
with it.

`observation_content_digest` and `observation_snapshot_id` are both derived by
`build/observation_snapshot.py`, and like the declaration version they are run-time computations,
not stored receipts — a full-refresh table's content changes every run, so a frozen value would go
stale. They are two distinct things, as the manifest columns above require:

- **`observation_content_digest`** is a SHA-256 over the normalized observation content **and
  nothing else**: the measurement columns only (`product_slug`, `product_type`, `artifact_kind`,
  `artifact_id`, `channel`, `metric_type`, `raw_value`, `unit`, `measurement_window_days`,
  `observed_at`), taken as an order-independent multiset. Lineage (`source_run_id`,
  `source_record_id`, `source_dataset`, `source_table`), capture time (`ingested_at`), the derived
  `observation_id`, `is_valid`, and `supersedes_observation_id` are excluded, so an unchanged
  measurement keeps its digest across re-runs and the runs that produced it stay visible only in
  `observation_run_ids` beside it. It does not fold in the `canonicalization_version` number — a
  version bump alone does not move it — but it is *not* invariant across canonicalization rules:
  the canonical bytes change if the contract changes, so two content digests are comparable only
  under the same contract.
- **`observation_snapshot_id`** is the identity reconciliation and `release_id` key on. It binds
  the `canonicalization_version` to the content digest, so a persisted id names the rule that
  produced it and two rules cannot collide on one id — the version is bound INTO this id, not
  merely recorded next to it.

`observed_at` is normalized to UTC before hashing (an aware timestamp converted, a naive one
interpreted as UTC — the warehouse emits naive UTC), at fixed microsecond precision with a `Z`
suffix, so one instant has one digest. A merge-base ratchet fails if the serializer or
`CONTENT_COLUMNS` change without `CANONICALIZATION_VERSION` advancing. Both digests are exercised
in-repo against the immutable Phase-2 baseline parquet and pinned there as fixed contracts.

Use them consistently:

- `registry.axis_assessments` belongs to `declaration_version_id`. It does not depend on
  measurements and must not carry a `release_id`.
- `evaluation.adoption_reconciliation` belongs to both `declaration_version_id` and
  `observation_snapshot_id`.
- `evaluation.axis_facts`, `axis_rule_matches` and `axis_results` belong to
  `declaration_version_id` — deterministic evaluation of declarations does not depend on
  observations.
- A public `release_id` identifies the exact pair that was adjudicated for publication.

`releases.manifest` therefore also requires:

```text
declaration_version_id
observation_snapshot_id
observation_content_digest
observation_run_ids
reconciliation_policy_version
reconciled_at
```

Any table keyed on `release_id` above should be re-read against this split: several are
keyed on a declaration version, not a release.

#### Digest canonicalization

A digest is reproducible only if the canonical bytes are defined. For every digest named in
this specification — `source_content_digest`, `observation_content_digest`,
`manifest_digest`, and the mirror `local_sha256` — declare:

- serialization format;
- key ordering;
- date and string normalization, including timezone and null representation;
- hash algorithm;
- a canonicalization version, so the rule can change without silently changing every digest.

Two implementations that disagree on any of these produce different digests from identical
data, which is indistinguishable from real drift.

Declared, for `source_content_digest` (owned by `build/declaration_version.py`,
`canonicalization_version` 1):

- serialization format: JSON, UTF-8, with no insignificant whitespace;
- key ordering: every mapping sorted by key, so reordering a YAML file changes nothing;
- string normalization: preserved verbatim, not ASCII-escaped;
- date and null representation: a date scalar renders as its ISO text, null as JSON `null`;
- number representation: finite only — `NaN`/`Infinity` are rejected, not emitted;
- type handling: only JSON scalars, lists, dicts, and dates are accepted; any other type
  (a YAML `!!set`, an unexpected object) is rejected rather than coerced to a string, which
  would make the digest implementation-dependent;
- hash algorithm: SHA-256, lowercase hex;
- input set: the classified declaration inputs of `sources/` (the full top-level inventory is
  gated, so a new authoritative input cannot silently leave the digest), excluding the
  separately-versioned routing policy and the frozen long-tail sample.

Declared, for `observation_content_digest` (owned by `build/observation_snapshot.py`,
`canonicalization_version` 1):

- serialization format: each observation is a compact JSON array (UTF-8, no insignificant
  whitespace) over the fixed column order `CONTENT_COLUMNS`; strings preserved verbatim, not
  ASCII-escaped;
- row/multiset ordering: the serialized rows are sorted and newline-joined, so the digest is
  independent of the order rows were materialized or read in;
- column set: the measurement columns only — lineage, capture time (`ingested_at`), the derived
  `observation_id`, `is_valid`, and `supersedes_observation_id` are excluded;
- timezone/date normalization: `observed_at` MUST be a `datetime` (a string or lookalike is
  rejected, not coerced); it is converted to UTC (a naive value interpreted as UTC), rendered at
  fixed microsecond precision with a `Z` suffix, so one instant has one rendering; null as JSON
  `null`;
- number/type representation: each column is checked against its declared type (by exact `type`
  identity, so a `bool` never satisfies an `int`/`str` requirement), any other type rejected —
  identity, vocabulary, and unit columns must be nonempty strings; `raw_value` a finite integer or
  float, excluding boolean and null; `measurement_window_days` a nonnegative integer or null,
  excluding boolean; `observed_at` a datetime normalized to UTC (as above);
- hash algorithm: SHA-256, lowercase hex;
- versioning: the `canonicalization_version` number is excluded from the content-digest preimage
  (bumping the version alone does not move `observation_content_digest`), but content digests are
  comparable only under the same canonicalization contract, since the canonical bytes change if the
  contract changes. The
  `canonicalization_version` is bound into `observation_snapshot_id`, whose preimage is the exact
  UTF-8 bytes `"os-ai-map:observation-snapshot:v" + version + "\0" + content_digest`
  (domain-separated, NUL-delimited). A merge-base ratchet forbids changing the canonicalization
  **contract descriptor** — the columns, ordering, types, timestamp rule, null/number encoding,
  serialization, and hash, fingerprinted as a whole rather than by one sample — without advancing
  the version; implementation conformance to the descriptor is tested separately.

Future release tables may include:

- `releases.product_axis_scores`
- `releases.category_scores`
- `releases.category_gaps`

Until consumers migrate, `registry.product_scores`, the generated JSON payload, and notebooks remain supported outputs.

## 5. Target DAGs

Do not implement one giant workflow. Implement three connected DAGs with different triggers and failure behavior.

### 5.1 Declaration and release DAG

Trigger: merge to `main` affecting declarations or the canonical evaluator.

```text
sources/*.yaml
  → validate declarations
  → compile registry tables
  → calculate source digest and release ID
  → publish registry static models
  → run repository-owned evaluator
  → materialize evaluation trace
  → run reconciliation and release gates
  → materialize product/category projections
  → regenerate JSON/notebooks/UI projection
  → validate the complete candidate release
  → mark the manifest valid
  → advance the public release pointer
```

Projection generation and parity happen BEFORE the commit point, not after. An earlier draft
of this section published the manifest and then regenerated projections, which contradicted
12.1: a manifest cannot be valid while the outputs it vouches for do not yet exist.

Initial implementation may keep existing GitHub and OSO jobs separate, but every job must declare which edge it protects and pass forward an explicit release identifier.

Do not publish a valid manifest if downstream models are stale, failed, or belong to another source commit.

### 5.2 Signal refresh DAG

Trigger: source-appropriate schedule or manual dispatch.

```text
external API/source
  → collect source-specific raw state
  → normalize the current observation snapshot
  → preserve the baseline / append history when platform support exists
  → refresh the stable current-observation contract
  → calculate candidate measured bands
  → reconcile against recorded assessments
  → emit findings and proposed changes
```

Signal refresh does not write accepted scores. It may open a review PR containing explicit proposed changes after all packet-binding and evidence requirements pass.

Until OSO incremental models are available, the historical append step is skipped after the immutable baseline is captured. The full-refresh current-state model and reconciliation still run.

### 5.3 Evidence and freshness DAG

Trigger: scheduled source audit, evidence change, or manual verification pass.

```text
cited source
  → refetch
  → preserve fetch result and digest
  → compare with prior fetch
  → determine whether the asserted fact remains established
  → confirm, contradict, hold, or queue the axis
```

HTTP success does not equal verification. A source confirms an assessment only when its content still establishes the recorded claim.

## 6. Time and freshness model

Never collapse these fields:

- `observed_at`: when the underlying measurement applies.
- `accessed_at`: when a source document was fetched or read.
- `verified_at`: when the accepted assessment was re-derived.
- `ingested_at`: when the warehouse received the row.
- `published_at`: when a valid release became available.

For rolling windows, preserve both `observed_at` and `measurement_window_days`.

All dataset schedules and workflow schedules must use UTC. On OSO:

- dataset cron controls when a dataset sweep occurs;
- model cron is a throttle, not the dataset schedule;
- run history `triggerType` is the proof that a schedule fired;
- `nextRunAt` and a configured cron are not proof of execution.

Do not repeat live schedule claims in multiple documents without a behavioral or structural ratchet against the authoritative configuration.

## 7. Gates and their protected edges

| Edge | Gate | Blocking condition |
|---|---|---|
| YAML → registry | Existing validation suite | Invalid schema, identity, roster, rubric, routing, evidence, or retirement state |
| Registry serializer → static models | Serialization contract | Missing table, invalid grain, duplicate key, unexpected empty output, or stale generated input |
| Source signal → observation | Observation contract | Unknown product/artifact, invalid units/time, duplicate observation ID, missing source lineage |
| Registry + observation → evaluation | Routing contract | Wrong signal type, undeclared substitution, invalid band, ambiguous identity |
| Recorded ↔ measured | Adoption reconciliation | Fresh authoritative disagreement without structured disposition |
| Evidence → accepted assessment | Verification contract | Undated and unqueued state, contradiction presented as confirmation, invalid source provenance |
| Evaluation → release | Release completeness | Missing products/axes, stale upstream release, blocking reconciliation finding, mixed release IDs |
| Release → public projection | Projection parity | JSON/notebook/API projection differs from the valid release |

#### Gates key on `release_path`, not namespace

Every governed asset is `population: gap_map` (ADR-003 retired `long_tail` — the discovered
artifacts are externalized). Release gates still key on the asset's `release_path` flag rather than
its namespace, because not every table in the `observations` or `evaluation` namespace is on the
release path: a staged or control artifact shares the namespace but belongs to no gap-map release.
Applying release completeness or "mixed release IDs" by namespace would fire on those; keying on
`release_path` avoids both a permanent exemption list and a namespace split.

Every gate must satisfy these engineering rules:

- Exit status and printed status are derived from the same complete set of findings.
- Tests exercise malformed synthetic inputs, not the current corpus backlog.
- A real-corpus test may assert an invariant, never that unfinished work remains.
- Semantic checks test behavior or structure, not source-code spelling.
- A gate must fail when any class it reports is violated.
- Allowances are explicit, named, narrow, dated where appropriate, and draining rather than permanent.

## 8. Adoption reconciliation rules

This is the first new end-to-end vertical slice.

### 8.1 Route resolution

For each product:

1. Read the product type and declared artifacts from `registry`.
2. Read the applicable route from `registry.adoption_routes`, ordered by `route_order`. Do not
   read or reinterpret `signal_routing.yaml` from the warehouse; the compiled table is the
   only warehouse-side representation of routing semantics.
3. Select measurements only from channels and `metric_type` values the route admits, then
   assign the route's `instrument_type`.
4. Apply the band set the route names for that product type and instrument.
5. Abstain when no declared band exists.
6. Never substitute a fallback for a missing authoritative route without recording that fallback status.

### 8.2 Reconciliation decisions

- Same route, fresh measurement, same level → `agree`.
- Same route, fresh measurement, different level, valid active override → `explicit_override`.
- Same route, fresh measurement, different level, no override → `override_required`.
- Fallback route differs from a score supported by a stronger declared instrument → `expected_difference`.
- Measurement predates the freshness threshold → `stale_measurement`.
- No compatible measurement → `unmeasured`.
- Measurement exists but signal type does not match the declared route → `route_mismatch`.
- Policy says the source/value means no answer → `abstained`.

Do not equate “repo bands higher than stars” with error. Stars are a fallback and live on their own scale. The gate should catch unsupported authoritative disagreement, not punish intentional instrument hierarchy.

### 8.3 Rollout

1. Run reconciliation in report-only mode.
2. Produce a complete baseline census by status and product.
3. Manually audit every proposed `override_required` result.
4. Correct routing, bands, identities, stale measurements, or recorded assessments as appropriate.
5. Add structured overrides only for genuine exceptions.
6. Enable blocking only when the baseline contains zero unexplained authoritative disagreements.

## 9. Openness single-homing migration

Do not delete the warehouse implementation first.

### 9.1 Build the canonical trace

Refactor the existing repository evaluator so one execution produces:

- normalized facts;
- matched rule and rule index;
- computed openness score and class;
- recorded score and class;
- agreement result;
- evidence and source references.

Reuse `build/check_rubric.py`, `build/rubrics.py`, and existing serializers. Do not load-modify-dump YAML and do not reproduce parser logic in another module.

### 9.2 Dual-run

For at least two complete releases:

- publish the repository-derived trace;
- run the current warehouse openness chain;
- compare every applicable product and category;
- require zero unexplained differences;
- confirm trace completeness and queryability.

### 9.3 Retire the duplicate

Only after dual-run acceptance:

- identify every consumer of `evidence.product_evidence`, `scores.openness_facts`, and `scores.openness_computed`;
- migrate consumers to the repository-derived trace or release tables;
- remove scheduled dependencies;
- archive mirror files and manifest entries with a retirement note;
- remove `check_parity` only when there is no independent implementation left to compare;
- preserve historical tables or compatibility views for a defined deprecation window.

Deleting a platform dataset is an irreversible operation and requires explicit maintainer authorization after consumer inventory and backup verification.

## 10. Catalog cleanup

Inventory every `currentai.catalog` table and classify it as:

```text
discovery inventory
curated registry data
raw observation
compatibility bridge
external reference
frozen historical data
unknown
```

For each table record:

- table and dataset;
- grain and primary key;
- semantic owner;
- source and refresh mechanism;
- last successful scheduled run;
- tracked repository consumers;
- deployed platform consumers;
- notebooks or external consumers;
- target namespace;
- migration or retirement action.

Migration rules:

- Move curated identity and membership into `registry`.
- Move measurement history into `observations` or its source-specific signal dataset.
- Keep genuine discovered inventory in `catalog`.
- Name external third-party maps explicitly; do not let them resemble Gap Map outputs.
- Prefix frozen tables or move them to a historical namespace.
- Keep compatibility views during migration and give them an owner and removal date.
- Never infer that a table has no consumers solely because no tracked repository query reads it. Check deployed models and known external notebooks.

## 11. Asset registry and repository layout

Verified against the live `currentai` org on 2026-08-20: <!-- observed:2026-08-20 -->22 datasets,
<!-- observed:2026-08-20 -->96 tables,
<!-- count:tracked_warehouse_files -->26 tracked files under `warehouse/`. The structure below is the target, and the
mirror layout of 11.1 is now in place; the file manifest in 11.4 recorded the exact diff
from the 2026-08-20 state (40 files), Phase 0b added `warehouse/audits/platform_models.json`,
the deployed-model audit receipt, and Phase 2 added `warehouse/audits/source_runs.json`, the
committed point-in-time attestation of the `source_runs` snapshot (§4.3), then the
`artifact_state` rename added the two new source mirror files
`signal_github/artifact_state.py` and `signal_huggingface/artifact_state.py` alongside the
retained `repo_state.py` / `hub_state.py`. Phase 2's baseline capture added two more:
`warehouse/data/observations/product_adoption_baseline.parquet`, the frozen bytes themselves,
and `warehouse/audits/product_adoption_baseline.json`, their provenance receipt. The ADR-003
mechanism then added `warehouse/dependencies.yaml`, the external dependency manifest (§11.7).

### 11.1 Target layout

The repository layout mirrors the warehouse: `models/<dataset>/<table>.<ext>` maps to
`currentai.<dataset>.<table>`. The path is the fully-qualified table name, so the mapping
is derivable rather than conventional, and no separate filename rule needs policing.

Fully migrated — after Phase 7 has retired the duplicate openness chain and Phase 8 has
published releases:

```text
warehouse/
  assets.yaml                          the only registry

  models/
    catalog/                             static reference (STATIC_MODEL dataset)
      model_benchmarks.py                Open LLM Leaderboard; rename WITHDRAWN (#393)
      model_repos.py                     HF-to-GitHub links; rename WITHDRAWN (#393)
    entities/                            kind: catalog, but a scheduled USER_MODEL dataset — stays put (#393)
      repos.sql projects.sql packages.sql models.sql
    events/                              kind: observations, own USER_MODEL sweep — deferred, stays put (#393)
      github_events.sql
    metrics/                             kind: observations, own USER_MODEL sweep — deferred, stays put (#393)
      daily.sql
    observations/
      source_runs                        run contract; a Python control-plane snapshot now
                                         (build/snapshot_source_runs.py), a live-emitter model later (#355)
      product_adoption.sql               incremental history — Phase 2B, blocked on OSO
      product_adoption_current.sql       full-refresh now, a view over history later
    evaluation/
      product_adoption_measurements.sql  artifact observations -> product-level bands
      adoption_reconciliation.sql
      axis_facts.sql
      axis_rule_matches.sql
      axis_results.sql
    scores/                              kind: evaluation, but a scheduled USER_MODEL dataset — stays put (#393)
      dependency_graph.sql fragility.sql investment_ranking.sql ossd_coverage.sql
      project_summary.sql repos_summary.sql stack_contributors.sql taxonomy.sql
    releases/
      manifest.sql
      product_axis_scores.sql
      category_scores.sql
      category_gaps.sql
    signal_github/
      artifact_state.py                  renamed from repo_state in Phase 2
      product_adoption.sql               COMPATIBILITY, retired with the set
    signal_huggingface/
      artifact_state.py                  renamed from hub_state in Phase 2
      product_adoption.sql               COMPATIBILITY, retired with the set
    signal_packages/                     replaces signal_pypi — issue #314
      downloads.sql
      downloads_daily.py
      product_adoption.sql               COMPATIBILITY, retired with the set
    signal_lmarena/
      text_leaderboard.py
    signal_semanticscholar/
      paper_citations.py
    signal_artificialanalysis/
      model_evaluations.py
    signal_goodailist/
      repo_catalog.py

  data/
    catalog/
      model_benchmarks.csv               rename WITHDRAWN (#393)
      model_repos.csv                    rename WITHDRAWN (#393)
      foundation_model_repos.csv
      top_models.csv                     fetcher interface, not an orphan
      tracked_models.csv                 fetcher interface, not an orphan
    observations/
      product_adoption_baseline.parquet   the baseline IS these bytes
```

`product_adoption_baseline` appears under `data/`, not `models/`. An earlier draft of this tree
showed it as a `.sql` file, which contradicts 4.3 — a model that selects from live upstream
tables produces a different result on every run, which is the opposite of an immutable snapshot.
Add a presentation view only if something actually needs one.

#### [Superseded by ADR-003 — historical] The long-tail chain

> An earlier plan kept the `entities`, `events`, `metrics` and analytical `scores` chain in this
> repository, mapping its tables onto the five semantic kinds and reasoning about which OSO dataset
> type/schedule each needed. ADR-003 (steps 5–6) **externalized** the whole chain instead — it
> models the OSO organization, not the Gap Map — so those tables are frozen under platform ownership
> and gone from this inventory, and the `population: long_tail` classification is retired. None of
> that mapping or namespace analysis binds any asset today. Current state: ADR-003, §11.2 and §11.5.

Three consequences worth stating, because each is a true claim the layout makes on its own:

`models/registry/` does not exist, and must not. Every registry table is
serialized from `sources/` by `build/serialize_registry.py` and `build/publish_registry.py`;
there is no authored model to hold. Their `assets.yaml` entries name the build script as
`source`. The absent directory asserts that nothing under `models/` produces a registry
table.

The `evidence/` and `scores/` directories disappear entirely at Phase 7, replaced by the
four files in `evaluation/`. The retirement is visible in the tree rather than buried in a
ledger.

`product_adoption` appears in `observations/` and in all three signal directories. The
architecture resolves that rather than leaving it open: source models emit raw normalized
measurements, and product-level aggregation and banding happen once, centrally, in
`observations` and `evaluation`. The three signal tables are **transitional compatibility
assets** — `status: compatibility`, each naming `observations.product_adoption_current` as its
`replacement` — retired together once the centralized evaluator is proven, not one at a time.

They are not, however, per-source roll-ups, and calling them that understates what retiring
them costs. `signal_github/product_adoption.sql` builds an `already_measured` set from
`signal_pypi` and `signal_huggingface`, then bands GitHub stars only for the products those
channels did not cover. It is the last-resort fallback tier, and the route precedence
`pypi > huggingface > stars` is implemented in its SQL.

That is the concrete instance of the AD-1 violation in 4.1. `registry.adoption_routes` must
capture that precedence BEFORE these three tables retire, or the ordering is lost silently and
nothing fails.

The layout also retires three directories whose names encoded authority implicitly —
`ingest/` ran in CI, `models/` was repo-authored and deployed, `platform-mirror/` was
read-only copy — and two partial registries, `sources.yaml` and
`platform-mirror/manifest.yaml`. Authority is a declared, validated field in `assets.yaml`;
encoding it a second time in the directory tree is the drift this migration exists to
remove. Dataset is not authority, so mirroring the dataset does not reintroduce it.

### 11.1a Table naming rules

These bind new tables. Deployed tables that violate them are listed in 11.6 as a separate
migration decision, not silently renamed.

1. **The dataset names the source; the table must not repeat it.**
   `signal_packages.downloads`, not `signal_packages.package_downloads`.
2. **Qualifiers are suffixes, so related tables sort together.**
   `product_adoption`, `product_adoption_baseline`, `product_adoption_current` — not
   `current_product_adoption`, which lands nowhere near the two tables it belongs with in
   any listing, and inverts the usual reading by giving the shortest name to the history
   and the longest to the view.
3. **A grain shared across sibling tables is named consistently or not at all.**
   The three trace tables in `evaluation/` are all keyed on
   `(declaration_version_id, product_slug, category_slug, axis)`, so all three lead with `axis_`:
   `axis_facts`, `axis_rule_matches`, `axis_results`. The earlier draft had
   `score_facts`, `rule_matches`, `product_axis_results` — three patterns for one grain.
4. **A reused basename must mean the same thing.** Reusing a name across namespaces is
   correct when the tables implement a common interface and a compatible grain — the namespace
   is what distinguishes them. `signal_github.artifact_state` and
   `signal_huggingface.artifact_state` are the same concept per source, and
   `signal_*.product_adoption` alongside `observations.product_adoption` are the same shape at
   different stages. All are fine.
   What is forbidden is the same name over DIFFERENT data, where a mistyped namespace returns
   plausible wrong numbers in silence. `registry.product_scores` stays as the front-end
   contract per 12.3, so the release projection is `releases.product_axis_scores` rather than a
   second `product_scores`.
   An earlier draft stated this as a blanket ban on reuse, which forbade the architecture's own
   `artifact_state` and `product_adoption` naming.
5. **A table named for a generic category must be specific enough to distinguish its
   siblings.** `catalog.model_benchmarks` is Open LLM Leaderboard v2, and it sits beside
   `signal_artificialanalysis.model_evaluations` and `signal_lmarena.text_leaderboard`.

### 11.2 Asset entry

`kind` uses the namespace vocabulary of section 4 rather than a second parallel enum. The
`declaration | discovery | observation | evaluation | release` set of the earlier draft was
the same five concepts under different names; `compatibility` and `historical` are states,
not kinds, and belong to `status`.

Three properties of the schema are load-bearing and were wrong in the first draft:

**An asset has several files, not one.** A mirrored SQL model has a `.sql` and a
`.schema.json`. A fetcher has a `.py` and the `.csv` it produces. The baseline has a model
and frozen bytes. A singular `file` cannot satisfy "every managed file appears exactly once"
and "one entry per table" simultaneously, so files are keyed by role.

**`table` records physical placement; `kind` records the semantic layer.** They agree for every
asset in the `registry`, `observations` and `evaluation` namespaces. They come apart only for the
`signal_*` source datasets: those are physically separate but semantically observations (a raw
source collector) — or evaluations, for the banded `product_adoption` assessments. `kind` is not
decorative: `build/assets.py` `kind_violations()` re-derives it from the table's placement
(`expected_kind`) and rejects a `registry` table that claims `kind: evaluation`. There are no
`current_namespace`, `target_namespace` or `migration_status` fields — the namespace migration is
complete, and a settled inventory records what each asset *is*, not where it was going.

**Dependency fields are derived, not authored.** They come from parsing model bodies,
`build/` modules, notebooks and workflows, then get verified in CI. Nothing here is
hand-maintained, because a hand-maintained dependency list drifts exactly like the two
registries this file replaces.

```yaml
- id: observations.product_adoption_current
  table: currentai.observations.product_adoption_current
  files:                          # keyed by role; every managed file appears in exactly one
    model: warehouse/models/observations/product_adoption_current.sql
    schema: null
    data: null
  kind: observations              # the semantic layer, derived from placement by expected_kind:
                                  #   the table's namespace, except a signal_* source dataset is
                                  #   observations (or evaluation for a *.product_adoption assessment)
  authority: repo                 # repo | platform | external
  population: gap_map             # gap_map — the ONLY governed population (long_tail retired, ADR-003)
  release_path: false             # true only if this asset belongs to a gap-map release
  role: repo-computation          # REQUIRED, one of:
                                  #   governed-output   a published gap-map artifact (release_path: true, authority repo)
                                  #   repo-computation  a repo-OWNED model (has a model file; authority: repo).
                                  #                     A platform mirror is NOT this — it is a dependency
                                  #                     contract (dependencies.yaml); a mirror is provenance,
                                  #                     not ownership.
                                  #   governed-data     a repo-owned data/control artifact, not a computation
                                  #                     (the frozen baseline bytes, the source-runs snapshot)
                                  #   compatibility-shim  a temporary shim for a governed asset (has `replacement`)
                                  # There is NO `owner` field — every governed asset is repo-owned, so a
                                  # uniform owner carried no signal (a dependency records owner: oso instead).
  grain: one row per (product_slug, artifact_kind, artifact_id, channel, metric_type, measurement_window_days)
  reads:                          # DERIVED
    - table: currentai.registry.product_artifacts
      scope: internal
    - table: currentai.signal_github.artifact_state
      scope: internal             # a dependency contract (a platform mirror), not a governed asset
  read_by:                        # DERIVED across the governed roots of 11.3
    build:
    - build/adoption_measurements.py
  consumer_checks:                # what was actually audited, per source of consumers
    repository: checked            #   tracked models, build modules, notebooks, workflows
    platform_notebooks: checked    #   every notebook in the org, tracked or not
    platform_models: checked       #   Phase 0b read every deployed model definition
    external: unknown              #   anything outside this org -- NOT audited
  external_consumers: none_confirmed   # unknown | none_confirmed | [named]
  refresh: repo-authored SQL, full-refresh on the platform
  status: active                  # active | staged | deprecated | historical | compatibility
  verified_at: '2026-08-25'
```

For `authority: platform`, a `mirror:` block is required (the compatibility shims, whose `status:
compatibility` makes a platform mirror legitimate). This replaces
`platform-mirror/manifest.yaml`, including its per-entry `synced_at` discipline — the date
must move only for the entry actually refetched.

```yaml
  mirror:
    model_id: a50ce375-4b91-43c6-b1ce-1fc60911b513
    revision: 4
    hash: efbd5ce1104d2f028c123f5f490fa9e5439be14489e8e069be50e0ecf545e4fd
    local_sha256: a11300a0a4c1a697a217202a43c230af3e00dc9595000c2f73cae74e615b9c66
    synced_at: '2026-08-15'
```

#### Retirement is derived from more than an empty reader list

An empty `read_by` is not sufficient. A table whose whole purpose is external consumption
correctly has no in-repo reader — `releases.manifest` is the clearest case, and would be
flagged for retirement by a naive rule on the day it ships.

An asset is a retirement candidate only when all of the following hold:

```text
read_by is empty across every closure root
AND publication_role is null
AND external_consumers is none_confirmed
AND consumer_checks.platform_models is checked
AND consumer_checks.platform_notebooks is checked
AND no deployed platform model reads it
```

`consumer_checks` is what stops the inventory from overclaiming, and it is four independent
facts rather than one confidence level. A single flag cannot distinguish "we read every
notebook" from "we read every deployed model definition", and those are different pieces of
evidence gathered by different means.

An asset cannot be a retirement candidate while either `platform_models` or
`platform_notebooks` is `unknown`, however unread it appears. Reading notebooks does not
license a retirement, because a deployed model is not a notebook. Until both are `checked`,
the honest claim is "no reviewed consumer found", never "no consumer".

There is no stored `retirement_candidate` boolean. The condition is computed; only the human
outputs — `retirement_reason` and `retirement_issue` — are recorded.

### 11.3 Scope: what the inventory covers

`warehouse/assets.yaml` covers the governed Gap Map data system: the assets reachable UPSTREAM from
the Gap Map's publication sinks and its named audit/control roots (§11.5 gate 4), traversed through
repo-owned producer files. Required OSO inputs a governed asset reads are contracts in
`warehouse/dependencies.yaml`, not governed assets. A standalone notebook is never a reachability root,
so a table only a notebook reads never enters governance (gate 5). Peripheral OSO pipelines the map
neither feeds nor reads are out of scope in both files and stay on the platform.

The root set is closed: a governed root is a governed producer file, one of the named audit modules
(`build/check_parity.py`, `build/apply_scores.py`, `build/check_artifacts.py`, which read tables
directly to gate map semantics), or a declared publication workflow — never "any tracked build module
or notebook". The reference extractor strips SQL and Python comments AND docstrings before counting a
table reference and reads only string literals: comments and docstrings name tables in prose, while the
real SQL lives in literals, so a grep that ignored the distinction would invent consumers one way and
lose them the other.

#### The inventory is larger than the platform, and why

Three numbers that must not be conflated:

```text
deployed tables in the in-scope datasets    <!-- count:deployed_tables -->31
staged, not deployed                         <!-- count:staged_assets -->10
dormant, no platform table yet              <!-- count:dormant_assets -->1
                                            ------
logical assets in warehouse/assets.yaml     <!-- count:assets -->42
```

The staged ten are the three `signal_packages` models from issue #314,
`observations.source_runs` and `observations.product_adoption_baseline` (both Phase 2), the
Phase-3 `registry.axis_assessments` candidate, and the Phase-1 identity outputs
`registry.resolution_ledger`, `registry.product_aliases`, `registry.org_handles` and
`registry.model_families`: tracked assets whose tables do not exist on the platform yet. The
two Phase-3 evaluation candidates that were staged here,
`evaluation.product_adoption_measurements` and `evaluation.adoption_reconciliation`, are now
**deployed** (#368, 2026-08-25) and count among the deployed tables. (`registry.foundation_model_repos`
was later **externalized** under ADR-003 — frozen under platform ownership and removed from this
inventory — so it is no longer a governed asset here.)
`observations.source_runs`, `observations.product_adoption_baseline` and
`registry.axis_assessments` are staged for a reason the `signal_packages` three are not — they are
repository-side artifacts by design (a control-plane snapshot, a frozen-bytes baseline, and a
declaration-keyed release-builder candidate whose row a maintainer publishes), and `staged` here
records only that no platform table carries their name.
Neither the snapshot nor the baseline is unfinished, and neither is waiting on a deploy to become
authoritative; `registry.axis_assessments` awaits its maintainer publish in
`docs/operations/deploy-axis-assessments.md`. `observations.product_adoption_current` was staged the same way when first authored, and is
now **deployed** (2026-08-24, the deploy created the `observations` namespace), so it counts among
the deployed tables rather than the staged ones. The four `registry.adoption_*` routing tables —
`adoption_routes`, `adoption_route_scopes`, `adoption_route_band_sets` and
`adoption_aggregation_rules` — were staged during Phase 2A and are now **deployed** (materialized
2026-08-23, PR #353). The dormant one is `registry.tail_products`, declared by `build.publish_registry.TABLES`,
whose platform table is absent only because the last serialization had no rows.

Both are real logical assets — a tracked file in no asset entry is invisible to every gate in
11.5 — but neither is current deployed state. A count that mixes them misrepresents the
warehouse, so `status` separates them and `build.assets.deployed_tables()` is what to count
when the question is "what exists on the platform right now".

An earlier draft quoted a single "49 of 96" figure that matched none of the three.

The tables outside those datasets are separate analytical products that the gap-map pipeline
neither feeds nor reads — `state_of_os_ai`, `ai_demand_curve`, `aiid`, `hf_live`, `openrouter_snapshot`,
`datasette_plugins`, `linkedin_sources`, the archived `stack_map` v1 dataset, and four
`catalog` tables with no in-repo consumer. They stay on the platform and stay out of
`assets.yaml`. Keeping them out is what allows `kind` to remain the five semantic kinds of
section 4 with no sixth catch-all.

The closure is mechanical, so it must be recomputed rather than assumed. (Under the old rule it
also pulled in tables only a standalone notebook read — `catalog.country_populations` and
`catalog.pypi_downloads` via `pypi-geo-trends.py` — which is exactly the over-scope ADR-003
corrected: those tables are now externalized and out of scope, and a notebook read no longer
confers membership.)

### 11.4 File manifest

DONE. This manifest was executed: the moves below have landed, `warehouse/ingest/`,
`warehouse/models/*.sql` at the top level and `warehouse/platform-mirror/` no longer exist,
and `warehouse/assets.yaml` carries the new paths. The tables below are the record of what
moved where.

The diff from 2026-08-20 state. Because the mirror layout keeps each file's base name and
only changes its directory, almost every move is a pure `git mv` — reviewable as a rename
rather than a rewrite. The one place a base name changed a table identity is
`signal_packages`: rule 11.1a.1 strips the redundant source prefix, so the staged
`signal_packages.package_downloads` / `package_downloads_daily` become `.downloads` /
`.downloads_daily` (nothing deployed; repository-only).

Counts, stated once and correctly. The manifest arithmetic runs from the PRE-Phase-0
baseline, which is why that figure is an `observed:` reading rather than a derived one: Phase 0
itself adds `warehouse/assets.yaml`, so the live count is already one higher than the number
this diff starts from.

```text
warehouse/ tracked files, pre-Phase-0   <!-- observed:2026-08-20 -->44
  of which SQL/Python models   <!-- count:model_files -->15   (13 models, 3 ingest, 17 mirror)
warehouse/ after the move    44 + 1 assets.yaml - 5 = 40
repository-wide             +6 created, -5 deleted   = +1
```

An earlier draft of this section claimed "44 become 40", which double-counted the five created
files that live under `docs/` and `tests/`, and separately claimed 27 current model files
against an actual 30. These numbers must be generated, not typed — see the closing note in
11.1.

**Create (6)**

| Path | Contents |
|---|---|
| `warehouse/assets.yaml` | The registry. Absorbs `sources.yaml` and `platform-mirror/manifest.yaml`. |
| `docs/architecture/data-architecture.md` | Sections 1-13 and 17-18 of this specification. |
| `docs/architecture/adr-001-repo-owns-scoring-semantics.md` | AD-1. |
| `docs/architecture/adr-002-registry-curated-catalog-discovered.md` | AD-3. |
| `docs/architecture/migration-status.md` | Phase status and retirement ledger, including the atomicity split of 12.2. |
| `tests/test_assets_inventory.py` | The checks in 11.5. |

**Move, base name unchanged (24)** — the dataset prefix becomes the directory

Every file below already carries its dataset as a filename prefix, so the move strips the
prefix into a directory and nothing else changes.

| From | To |
|---|---|
| `models/entities_models.sql` | `models/entities/models.sql` |
| `models/entities_packages.sql` | `models/entities/packages.sql` |
| `models/entities_projects.sql` | `models/entities/projects.sql` |
| `models/entities_repos.sql` | `models/entities/repos.sql` |
| `models/events_github_events.sql` | `models/events/github_events.sql` |
| `models/metrics_daily.sql` | `models/metrics/daily.sql` |
| `models/scores_dependency_graph.sql` | `models/scores/dependency_graph.sql` |
| `models/scores_fragility.sql` | `models/scores/fragility.sql` |
| `models/scores_ossd_coverage.sql` | `models/scores/ossd_coverage.sql` |
| `models/scores_project_summary.sql` | `models/scores/project_summary.sql` |
| `models/scores_repos_summary.sql` | `models/scores/repos_summary.sql` |
| `models/scores_stack_contributors.sql` | `models/scores/stack_contributors.sql` |
| `platform-mirror/evidence_product_evidence.sql` | `models/evidence/product_evidence.sql` |
| `platform-mirror/evidence_product_evidence.schema.json` | `models/evidence/product_evidence.schema.json` |
| `platform-mirror/scores_openness_facts.sql` | `models/scores/openness_facts.sql` |
| `platform-mirror/scores_openness_facts.schema.json` | `models/scores/openness_facts.schema.json` |
| `platform-mirror/scores_openness_computed.sql` | `models/scores/openness_computed.sql` |
| `platform-mirror/scores_openness_computed.schema.json` | `models/scores/openness_computed.schema.json` |
| `platform-mirror/github_repo_state.py` | `models/signal_github/repo_state.py` |
| `platform-mirror/github_product_adoption.sql` | `models/signal_github/product_adoption.sql` |
| `platform-mirror/huggingface_hub_state.py` | `models/signal_huggingface/hub_state.py` |
| `platform-mirror/huggingface_product_adoption.sql` | `models/signal_huggingface/product_adoption.sql` |
| `platform-mirror/lmarena_leaderboard.py` | `models/signal_lmarena/text_leaderboard.py` |
| `platform-mirror/semanticscholar_paper_citations.py` | `models/signal_semanticscholar/paper_citations.py` |

**Move, base name corrected (5)** — the old name did not match the table it produces

| From | To | Table |
|---|---|---|
| `platform-mirror/artificialanalysis_models.py` | `models/signal_artificialanalysis/model_evaluations.py` | `.model_evaluations` |
| `platform-mirror/goodailist_repos.py` | `models/signal_goodailist/repo_catalog.py` | `.repo_catalog` |
| `platform-mirror/pypi_package_downloads.sql` | `models/signal_pypi/package_downloads.sql` | unchanged; retired by #314 |
| `platform-mirror/packages_package_downloads.sql` | `models/signal_packages/downloads.sql` | staged; rule 11.1a.1 |
| `platform-mirror/packages_package_downloads_daily.py` | `models/signal_packages/downloads_daily.py` | staged; rule 11.1a.1 |

`platform-mirror/packages_product_adoption.sql` moves to
`models/signal_packages/product_adoption.sql` with its name intact.

**Move and rename (3)** — `ingest/` fetchers, named for the table they load

| From | To | Loads |
|---|---|---|
| `ingest/fetch_model_benchmarks.py` | `models/catalog/model_benchmarks.py` | `catalog.model_benchmarks` |
| `ingest/fetch_huggingface.py` | `models/catalog/model_repos.py` | `catalog.model_repos` |
| `ingest/build_stack_map.py` | `models/catalog/stack_map.py` | `catalog.stack_map` |

**Move (6)** — `catalog/` to `data/<dataset>/<table>.csv`

| From | To |
|---|---|
| `catalog/huggingface/model_benchmarks.csv` | `data/catalog/model_benchmarks.csv` |
| `catalog/huggingface/model_repos.csv` | `data/catalog/model_repos.csv` |
| `catalog/huggingface/foundation_model_repos.csv` | `data/catalog/foundation_model_repos.csv` |
| `catalog/stack_map/repos.csv` | `data/catalog/stack_map.csv` |
| `catalog/huggingface/top_models.csv` | `data/catalog/top_models.csv` |
| `catalog/huggingface/tracked_models.csv` | `data/catalog/tracked_models.csv` |

**Delete (5)**

| Path | Reason |
|---|---|
| `warehouse/sources.yaml` | Absorbed into `assets.yaml`. Its prose on why `goodailist` and `aiid` have no fetcher carries over verbatim. |
| `warehouse/platform-mirror/manifest.yaml` | Absorbed as the nested `mirror:` block. |
| `warehouse/platform-mirror/README.md` | Content to `docs/architecture/data-architecture.md`. |
| `warehouse/models/README.md` | Per-table detail to `assets.yaml`; enduring prose to `docs/architecture/data-architecture.md`, which avoids creating a seventh file that was never in the Create list. Its inventory was stale — a dataset count of 25 against an actual 22, and 5 `catalog` tables documented against an actual 10 — and it recorded `catalog.goodailist_repos` as retired while the table is live. |
| `warehouse/catalog/.gitkeep` | Directory retired. |

`top_models.csv` and `tracked_models.csv` are NOT deleted. An earlier draft listed them as
orphans loading no table; they are the interface between the two fetchers —
`model_repos.py` writes both and `model_benchmarks.py` reads both at line 91.
Deleting them would have broken the benchmark fetcher. They move with the rest to
`data/catalog/`.

The `signal_pypi/` directory is created by this move and retired by issue #314 once
`signal_packages` is deployed. Keeping it visible through the transition is deliberate: the
staged successor and the live predecessor should both be readable in the tree while both
exist.

### 11.5 CI checks

1. Every file under `models/` and `data/` appears exactly once in `assets.yaml`, and every
   declared path exists. Because `models/` mixes editable and mirror-only files within the
   same dataset directory, no path signals which is which; this check plus 3 carries that
   weight.
1b. The path derives the table: `models/<dataset>/<table>.<ext>` must equal the declared
   `table` as `currentai.<dataset>.<table>`. This replaces a filename-convention check —
   a misplaced file fails rather than being silently accepted under a plausible name.
1c. Every managed file appears in exactly one `files:` role across the whole inventory. Roles
   are checked for consistency with `authority` and `kind`: a `data` role requires a fetcher or
   a frozen asset. A `schema` role is available to any model, mirrored or repository-owned —
   restricting it to mirrors would block repository-owned models from declaring schemas.
2. `kind` (the semantic layer) equals what the table's placement derives (`expected_kind`,
   enforced by `kind_violations`): the table's own namespace for a `registry`, `observations` or
   `evaluation` asset, and for a `signal_*` source dataset either `observations` (a raw source
   collector) or `evaluation` (a banded `product_adoption` assessment). This is the one place `kind`
   and namespace intentionally come apart, so the gate enforces it rather than leaving `kind` free.
   There are no `current_namespace`, `target_namespace` or `migration_status` fields: the namespace
   migration is complete, so the inventory records placement (`table`) and semantics (`kind`), not a
   move.
2b. Release-completeness and projection-parity gates apply only to assets with
   `release_path: true`. Every governed asset is `population: gap_map`.
3. `mirror:` is present if and only if `authority: platform`.
4. Mirror drift, in two parts, because a test reading only the current tree cannot detect it.
   A contributor who edits a mirrored file and updates `local_sha256` to match passes any
   single-snapshot check.
   **Offline, in PR CI, against the merge base:** if a mirrored file's bytes changed, then
   `local_sha256` must change, and so must `revision`, the platform `hash` and `synced_at`; and
   only the entry whose file changed may advance. This proves provenance changes are coherent.
   **Credentialed, as a separate job:** refetch each `model_id`'s latest revision and compare
   the claimed `hash` against the platform. This is the only check that proves they are
   truthful. Extends `tests/test_platform_mirror.py`, which today checks only that mirrored
   files are listed and their local hashes match.
5. `reads` and `read_by` match what parsing the model bodies and tracked notebooks finds.
6. No duplicate asset ID or table.
7. The retirement condition of 11.2 is computed, never read from a stored boolean. Any asset
   satisfying it must carry a `retirement_reason` and `retirement_issue`. No asset with
   any `consumer_checks` value other than `checked` for `platform_models` or
   `platform_notebooks` may be reported as a retirement candidate.
8. Every entry in `reads` either resolves to an asset in the inventory when
   `scope: internal`, or is `scope: external` and names a table this inventory does not cover.
   Because the inventory deliberately covers the closure rather than all 96 org tables,
   `oso.*` and out-of-scope `currentai.*` reads must be representable rather than errors.
9. Deprecated assets carry a removal condition; active `compatibility` assets name a
   replacement or state why none exists.
10. Every asset is governed and carries a `role`; there is no backlog or roleless state, and no
    test requires one to exist.

**ADR-003 scope-boundary gates.** Implemented in `build/assets.py` (`role_violations`,
`dependency_violations`, `notebook_root_violations`, `unreachable_repo_computations`) and asserted
in `tests/test_assets_inventory.py` + `tests/test_scope_gates.py`. The `role` each governed asset
carries is RE-DERIVED from its fields (`expected_role`) and must match the authored value, exactly
as `read_by` is re-derived. A role is one of `governed-output`, `repo-computation` (repo-OWNED
model, authority repo), `governed-data` (repo-owned data/control artifact), or `compatibility-shim`.
Every asset in `assets.yaml` is governed and carries a role; there is no roleless/backlog state (the ADR-003 externalization backlog drained in steps 5-6) and `population` is always `gap_map`.

- **G1 governed-output ⇔ release_path.** A `governed-output` is `release_path: true`, and a
  `release_path: true` asset is a `governed-output` (subsumes 2b).
- **G2 needed non-governed tables are contracts.** Every table reachable UPSTREAM from a governed
  root that is not itself governed -- a platform-authored `currentai.*` mirror OR an `oso.*`
  upstream -- appears in `dependencies.yaml` exactly once. Re-derived from the tree, so an
  uncontracted input (of either kind) fails; a table only out-of-scope code (an externalized or
  peripheral reader) touches is not the repository's contract.
- **G3 the two files are disjoint.** A table is a governed asset or a dependency contract, never both.
- **G4 every dependency is reachable, used and named.** Each `dependencies.yaml` entry is reachable
  from a governed root, has ≥1 `required_by` that equals the mechanically re-derived repo readers
  (governed roots + dependency mirror files, never a notebook), and `owner: oso`. Contract
  INTEGRITY: exactly one provenance anchor, self-consistent -- a `currentai.*` mirror uses
  `verified_revision` + a `mirror` block whose `local_sha256` matches the tracked file's bytes; an
  `oso.*` upstream uses `content_contract_sha256` (64 hex, recomputed by the gate from the table,
  grain and TYPED `expected_columns`) + `verified_at`.
- **G5 a notebook is never a graph root.** No standalone notebook produces a governed table or is a
  governed root, so a notebook read cannot confer membership or pull a table into the DAG.
- **G6 `long_tail` is retired; there is no backlog.** `gap_map` is the only governed population
  (the vocabulary is single-valued), and every asset carries a `role`, so there is no roleless or
  backlog state to shrink. The externalized long-tail and questionable tables are frozen platform
  objects recorded in `warehouse/audits/externalization.json`; the reproducible externalization
  gate plus the role/scope gates keep any `long_tail` or peripheral table from re-entering the
  inventory. The tail-candidate registry (`registry.tail_products`) is a distinct governed
  `gap_map` asset, not `long_tail`.
- **Reachability.** Every ACTIVE `repo-computation`/`governed-data` table is reachable upstream from
  a governed sink or a named audit root -- no dead nodes in the governed graph (staged/dormant
  pre-service assets are exempt).

The inventory must not claim visibility into untracked external consumers. `read_by` covers
in-repo consumers only; represent confidence about anything beyond that explicitly.

### 11.7 External dependency manifest (`warehouse/dependencies.yaml`)

Category-3 inputs — tables a governed asset reads but the repository does not own — are recorded
here as **contracts**, never as governed assets (ADR-003). Two kinds:

- **`oso.*` upstreams** — an OSO marketplace/pipeline table. Anchored by `content_contract_sha256`
  + `verified_at`: the fingerprint of the agreed schema (table + `expected_grain` + TYPED
  `expected_columns`, each a `{name, type, nullable}`). The gate recomputes it, so a silent edit to
  the contract terms is caught; live-schema verification against OSO is a credentialed maintainer
  step (CI has no credentials). Names alone are insufficient — columns carry types (the `timestamp(6)`
  drift).
- **`currentai.*` platform mirrors** — a platform-authored model the repo reads read-only (the
  openness chain, the signal ingestion). A `mirror:` block proves provenance, **not** operational
  ownership, so these are dependencies, not governed assets. Anchored by `verified_revision` + the
  `mirror` block; the repo keeps the read-only mirror **file**, claimed by the contract, and the gate
  recomputes its `local_sha256` from the bytes on disk. The three openness models carry a
  `retirement_context`: the repo drives their Phase-7 retirement (#384), it does not own them.

Every entry also states `purpose`, `required_by` (the repo files that read it, mechanically
re-derived), and `owner: oso`. A contract confers **no** migration status, retirement policy, or
namespace-cleanup obligation. G2/G3/G4 (§11.5) keep the manifest reachable and disjoint so it cannot
grow into a second org-wide inventory.

### 11.6 Decisions resolved 2026-08-20, and what remains

Resolved by looking, not by asking. Each was an open question in an earlier draft that the
repository or the platform already answered:

| Question | Answer | Evidence |
|---|---|---|
| Do the two orphan CSVs get deleted? | No. They are the interface between the two fetchers. | `model_repos.py` writes both, `model_benchmarks.py` reads both at line 91 |
| Is `registry.tail_products` misfiled? | No, correctly in `registry`. The platform table is absent because it is empty. | `publish_registry.py`: "94 bytes of header on a push where every tail row was promoted or rejected" — promotion and rejection are curator acts |
| May a `held` axis retain its value? | Yes, with the hold reason and date. | `verification_queue.yaml`: "held at 3" |
| Is a dated null `held` or `not_applicable`? | Neither — it is `confirmed`. | `verification_queue.yaml`: "a null answer that somebody looked for and did not find is a confirmed axis" |
| Is the long-tail chain retired? | **Superseded by ADR-003 (2026-08-29): externalized.** The long-tail pipelines are out of the Gap Map's data system, so they were removed from this repo's inventory/publisher and frozen under platform ownership (steps 5-6). They keep serving `oss-ai-trends` / `long-tail-explorer` on the platform, but this repo no longer governs them. | superseded |
| Does the platform support release-scoped tables? | No. Each static-model publish replaces in place. | No version or revision field; `registry.product_scores` has `createdAt == updatedAt` |

Resolved by decision:

| Decision | Resolution | Lands in |
|---|---|---|
| Sixth `kind` for the long-tail chain | **Moot under ADR-003 (2026-08-29): the long-tail chain is externalized**, so no sixth kind and no namespace decision is needed — `entities.*`, `events`/`metrics` and the analytical `scores.*` left this repo's inventory (frozen under platform ownership, steps 5-6). Historically they were `not_planned` in their own namespaces because a scheduled `USER_MODEL` cannot be hosted in a static dataset (#393); the scope reset made the question irrelevant. | superseded |
| Gates over two populations | Key on `release_path`, not namespace | Section 7 |
| Publication atomicity | `releases.*` atomic from birth; compatibility outputs documented non-atomic | Sections 12.2, 18 |
| `catalog.model_benchmarks` -> `openllm_leaderboard` | **WITHDRAWN (2026-08-28, #393).** Its only trigger was the `catalog.models` name collision the `entities → catalog` move would have created; that move is cancelled (§11.1 dataset-type constraint), so there is no collision to resolve and no PR may exist purely to rename a deployed table. `catalog.model_benchmarks` keeps its name. | no action |
| `catalog.model_repos` -> `hf_model_repo_links` | Same — WITHDRAWN with the collision that triggered it. `catalog.model_repos` keeps its name. | no action |
| `repo_state` / `hub_state` -> `artifact_state` | Do it, with the observations adapters that repoint the same SQL | Phase 2 |
| Untracked notebook audit | Added to Phase 0. Sixteen of twenty notebooks are not in the repository | Phase 0 |
| `catalog.stack_map` archive note | WITHDRAWN. The note sits on `stack_map.*`, not `catalog.stack_map`, and is accurate about deployed models. Two different tables were conflated | no action |

No rename is performed as a standalone change. Each rides a phase that already repoints the
same SQL, so no PR exists purely to rename a deployed table.

#### Resolved by the Phase 0b deployed-model audit

These three tables had no in-repo consumer and could not be judged on that basis while
`consumer_checks.platform_models` was `unknown`. Phase 0b read all 41 deployed model
definitions in the org and set it to `checked`; none of the three is a retirement candidate.

| Table | Finding |
|---|---|
| `catalog.goodailist_repos` | Documented retired, table live, superseded by `signal_goodailist.repo_catalog`; retained by the `ai-safety-incidents` notebook consumer. Not a candidate. |
| `scores.investment_ranking` | No repository source and no in-repo reader; read only by the Deprecated `ai-potluck-partners` notebook. The audit also found it is itself a reader of `catalog.osai_gap_map`, `catalog.osai_subcategory_mapping`, `entities.repos` and `scores.fragility`. |
| `scores.taxonomy` | Same shape; read by `ai-potluck-partners` (Deprecated) and the non-deprecated `state-of-os-ai`. The audit's self-check reproduced: it reads `catalog.osai_gap_map`, `catalog.osai_subcategory_mapping` and `catalog.taxonomy_crosswalk`, which removed those three from the "no reviewed consumer" list. |

`oss-ai-gaps` and `stack_map_category_maps` were the plausible readers named before the audit.
The deployed-model read that actually mattered was `scores.taxonomy`'s, now recorded as those
three tables' `platform_model_consumers`.

## 12. Release mechanics

### 12.1 Release construction

The release builder should:

1. Resolve the exact Git SHA.
2. Validate all source declarations.
3. Serialize registry, rubric/evidence, accepted assessments, and score projections.
4. Compute a digest over the canonical serialized inputs.
5. Derive `declaration_version_id`, then bind `observation_snapshot_id`, then derive the
   candidate `release_id` from both plus `reconciliation_policy_version`.
6. Publish tables carrying that release ID.
7. Run downstream evaluation and reconciliation.
8. Regenerate the JSON payload, notebooks and API projections from the candidate tables.
9. Validate expected row counts, complete axis terminal states, and projection parity.
10. Publish `releases.manifest` as `valid` last.
11. Advance the public release pointer.
12. Only then update the replace-in-place compatibility outputs from that valid release.

Step 12 is the ordering constraint, not an afterthought. Publishing candidate registry tables
before reconciliation succeeds means a FAILED candidate can overwrite `registry.product_scores`
even though no valid release was ever created. Compatibility consumers may briefly straddle two
valid releases — that is the accepted cost in 12.2 — but they must never receive rows from a
candidate that failed.

If the warehouse evaluator cannot run without overwriting current registry tables, record that
as a transitional limitation in `migration-status.md` until release-scoped candidate inputs
exist. Do not describe the ordering as satisfied while the evaluator requires the overwrite.

### 12.2 Atomicity

A manifest is a claim about a set of tables. It is not a mechanism. Because static tables
upload one at a time, an upload can overwrite the previous release's rows before the new
release is valid, and no manifest can restore what was overwritten. Filtering on the newest
`valid` manifest does not protect a consumer that is reading a table which has already been
replaced in place.

Specify the mechanism, and do not claim atomicity without one.

#### Target mechanism

Publish into release-scoped or otherwise immutable materializations, and let a single
pointer decide what is current:

```text
build candidate registry / evaluation / release tables, scoped to the candidate release
→ build the JSON, notebook and API projections from those candidate tables
→ validate the complete candidate release
→ mark the manifest valid
→ advance one public release pointer
```

Every release-aware consumer resolves through the pointer. The previous valid release stays
readable until the pointer moves, and stays recoverable after it moves.

#### Decided: atomic where it is cheap, documented where it is not

Verified 2026-08-20: static models carry no version or revision list, and
`registry.product_scores` reports `createdAt == updatedAt`, so each publish replaces in place.
The platform offers NO native release-scoped materialization. Release-scoped table names plus a
pointer are achievable, but they are something this repository would build.

The resolution is split by consumer, not applied uniformly:

**`releases.*` is atomic from birth.** It does not exist until Phase 8 and has no consumers, so
it is release-scoped with a pointer from the start at no migration cost. Release-aware
consumers resolve through the pointer and never observe a partial release.

**Compatibility outputs stay replace-in-place, and this is documented rather than implied.**
`registry.product_scores`, `build/notebook_data.json` and the published notebooks are pinned by
12.3's stability requirement and cannot resolve a pointer. Retrofitting release-scoped names
onto every `registry` table — one of which carries the front-end contract — costs more
than it returns.

Therefore the definition-of-done clause "joining current public tables cannot mix releases
silently" is **met for release-aware consumers and unmet for compatibility consumers**. Record
that split in `docs/architecture/migration-status.md` and do not mark the clause complete on
the strength of the first half.

If any step fails:

- leave the candidate release as `failed` or absent;
- do not advance the public release pointer;
- preserve enough run metadata to diagnose the failure;
- never combine tables from the failed candidate with the previous valid release.

### 12.3 Projection compatibility

During migration:

- keep `build/notebook_data.json` and `notebooks/ai-stack-map.py` bot-owned;
- keep `registry.product_scores` stable;
- preserve product and organization slugs and aliases;
- avoid changing the frontend payload contract without a coordinated consumer migration;
- test that all public projections correspond to one valid release.

## 13. Scheduling and triggering

### Immediate rules

- Audit every live signal dataset and model schedule.
- Pin actual schedules to UTC.
- Record whether the schedule lives at dataset or model level.
- Treat model cron as a throttle and dataset cron as the sweep.
- Verify at least one `SCHEDULED` run from run history after changing a schedule.
- Keep run-history evidence in the operational change record.

### Event strategy

- Repository declaration changes trigger full registry compilation and full score evaluation.
- Signal collection is source-specific and may refresh independently.
- A successful signal refresh triggers current-state observation normalization and reconciliation.
- Historical append begins only when OSO incremental models are available; until then the preserved baseline is immutable and the current model is full-refresh.
- A failed or stale signal source does not silently reuse itself as current.
- Publication waits for the relevant upstream release or observation run IDs.

Do not build per-product dependency triggering in the initial migration. The asset graph and release IDs should make that possible later without requiring it now.

## 17. Operational and safety constraints

The implementation agent may autonomously:

- inspect repository and platform state read-only;
- add schemas, models, serializers, tests, documentation, and non-destructive compatibility views;
- open focused PRs;
- run existing validation and read-only warehouse queries.

The agent must stop and request maintainer direction before:

- deleting or irreversibly replacing a platform dataset or model;
- changing scoring semantics, thresholds, weights, or category membership;
- automatically accepting a candidate score into `sources/`;
- changing the public payload contract or retiring a consumer-facing table;
- expanding credential permissions;
- resolving a substantive evidence disagreement by judgment;
- introducing a new authoritative source or changing route priority.

Before any platform mutation:

- resolve the exact dataset/model ID;
- capture the current revision and schema;
- identify consumers;
- state the rollback path;
- separate reversible deployment from irreversible deletion.

## 18. Definition of done

The architecture migration is complete when:

- every active data asset has one named semantic **kind** (role), owner, grain, and refresh mechanism;
- every asset is classified by the correct kind — curated declarations `registry`, discovered
  inventory `catalog`, measurements `observations`, derived candidates and trace `evaluation`, valid
  snapshots `releases` — and physically placed in a dataset compatible with its type and schedule.
  A kind maps onto **one or more** physical OSO datasets (a dataset carries one immutable type and one
  sweep schedule), so a scheduled or differently-typed pipeline of a given kind stays in its own
  dataset rather than being forced into a shared namespace; the migration requires correct-kind
  classification and type/schedule-valid placement, **not** one dataset per kind (§11.1, #393);
- adoption observations retain history and reconcile through route-aware rules;
- fresh authoritative adoption disagreement cannot enter a release silently;
- fallback and cross-instrument differences are represented honestly rather than forced into equality;
- the repository is the only semantic implementation of scoring rules;
- openness remains fully traceable after duplicate warehouse derivation is retired;
- every public output belongs to one valid release and source Git SHA, subject to the
  compatibility limitation recorded in 12.2 — the replace-in-place outputs pinned by 12.3
  satisfy this only for the most recent successful publication, not atomically;
- all schedules are UTC and verified through observed run history;
- frozen and compatibility tables are unmistakably labeled and have retirement conditions;
- the full repository suite and all architecture gates pass without skips;
- documentation accurately describes the deployed system.

If OSO incremental models are still unavailable, all unblocked phases may ship, but the architecture migration remains explicitly **partially complete** on observation history. The accepted temporary state is: one preserved baseline snapshot, a full-refresh `product_adoption_current` model, working reconciliation, and the blocked Phase 2B issue above. Do not mark append-only history complete until an incremental platform run has been observed.
