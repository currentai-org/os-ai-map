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
- `currentai.catalog` mixes discovered inventory, fetcher output, external reference data, and a stale repo-to-warehouse bridge. Verified 2026-08-20: it holds 10 tables, not the 5 its README documents. Only 3 are discovered inventory. `foundation_model_repos`, `osai_subcategory_mapping` and `taxonomy_crosswalk` are curator-controlled and belong in `registry`; `pypi_downloads` is a measurement; `goodailist_repos` is documented as retired but still live; `osai_gap_map` is a third-party map carrying `maturity`, `parity_verdict` and `overall_score` columns that read as gap-map outputs.
- External measurements generally expose current state rather than a durable observation history.
- OSO does not yet support incremental models; the current normalized state must therefore become the first preserved timestamped snapshot rather than being mislabeled as an append-only history.
- Platform model source is mirrored read-only under `warehouse/platform-mirror/`; the platform remains authoritative for those deployed models.
- Dataset scheduling, model throttles, GitHub Actions schedules, and manual operations coexist. A configured cron is not treated as proof that a scheduled run fired. Verified 2026-08-20: of 22 datasets, 13 carry `cronTimezone: America/New_York`, and 8 have a cron configured with `lastRunAt: null` — `signal_semanticscholar`, `signal_pypi`, `ai_demand_curve`, `state_of_os_ai`, `scores`, `events`, `metrics`, `entities`. The `scores` dataset is among them, which means the openness chain that `check_parity` compares against the repository has no observed scheduled run.
- Two platform tables have no repository source and no in-repo consumer: `currentai.scores.investment_ranking` and `currentai.scores.taxonomy`.
- The full org is 22 datasets and 96 tables. The transitive closure of what the repository ships or maintains is 49 of them; the other 47 are separate analytical products. See section 11.3.

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
source  column  signal_type  confidence  unit  cap  cap_because  bands
applies_to_categories  requires_evidence  hand_authored  vocabulary
vocabulary_note  note  attribution_note
```

plus the dimension-level `sum_across_artifacts` and `sum_note`. Two routes have
`source: null`, and only two of seven carry inline `bands`.

A single flat table cannot hold this without loss, so normalize:

```text
registry.adoption_routes            one row per route
registry.adoption_route_scopes      route x applicable category / product type
registry.adoption_aggregation_rules sum_across_artifacts and per-dimension aggregation
registry.adoption_bands             existing; gains band_set_id
```

`registry.adoption_bands` has no `band_set_id` column today — its columns are `product_type`,
`level`, `above`, `reach`, `unit`, `signal_type`. Adding one is part of this work, because two
routes carry bands inline and those must land somewhere addressable.

`registry.adoption_routes` must preserve at minimum:

```text
declaration_version_id
route_id
route_order                  explicit; the YAML encodes precedence by list position
source                       nullable — two routes legitimately have none
source_column
artifact_kind
metric_type                  derived from source + column
instrument_type              the YAML's signal_type; usage_volume | stars_fallback | ...
authority                    authoritative | secondary | fallback
hand_authored
confidence
unit
aggregation_method
band_set_id
cap
cap_because
requires_evidence
freshness_days
abstain_rule
vocabulary                   qualitative vocabulary where the route declares one
policy_version
```

The YAML's `signal_type` compiles to `instrument_type`, and `metric_type` is derived from
`source` and `column`. That mapping is part of the compiler's contract, not something evaluation
infers.

The repository compiler owns these tables. Evaluation reads them and never reinterprets the
YAML. A route the compiler cannot express is a compiler bug to fix, not a case for evaluation to
special-case.

**Acceptance test is round-trip completeness**, not column presence: every semantic field in the
adoption portion of `signal_routing.yaml` is either compiled into these tables or explicitly
classified as documentation-only. `note`, `cap_because`, `sum_note`, `attribution_note` and
`vocabulary_note` are prose and may be classified documentation-only; `cap`,
`applies_to_categories`, `hand_authored`, `requires_evidence`, `vocabulary` and
`sum_across_artifacts` are semantic and must compile. A field that is neither compiled nor
classified fails the test.

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

- `observations.source_runs` — the run contract described below. Required from day one;
- `observations.product_adoption_current` — a full-refresh normalized model containing the latest observations from successful, complete source runs;
- `observations.product_adoption_baseline` — the immutable first snapshot, backed by frozen bytes rather than a query;
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

#### `observations.source_runs`

A current-state table cannot prove that a collector ran. Rows in
`product_adoption_current` cannot distinguish a successful run that returned identical values
from a successful run that returned zero rows, from a failed collector whose previous table
remained readable, from a source that never ran at all, from a partial run. All five look like
"the current value is what it was".

This table is required before reconciliation can honour the rule that a failed or stale source
does not silently reuse itself as current. It can begin as a current-run manifest rather than a
history; it cannot be omitted.

Grain: one row per source run.

```text
source_run_id
source_dataset
source_table
started_at
completed_at
status                       succeeded | failed | partial | running
trigger_type                 SCHEDULED | MANUAL | unknown
expected_scope               what the run was supposed to cover
observed_row_count
rejected_row_count
content_digest
error_class                  nullable
```

Rules:

- `product_adoption_current` selects only from runs with `status = succeeded` and a scope that
  matches `expected_scope`.
- Reconciliation reports a missing or failed current run as its own condition, distinct from a
  product that has no applicable measurement. The first is an infrastructure failure; the
  second is a legitimate abstention. Collapsing them hides outages as data gaps.
- `observation_snapshot_id` is content-addressed over the normalized observations alone. Run
  identifiers are lineage, recorded in `observation_run_ids`, and are NOT inputs to the ID.
  Including them would give every re-run a new snapshot ID even when nothing measured changed,
  which is the opposite of what the ID is for. Identical content means an identical snapshot;
  different content means a different one; the runs that produced it stay visible either way.

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

It selects only from source runs with `status = succeeded`. It begins as a full-refresh model. After the incremental history table exists, replace its implementation with a view over `observations.product_adoption` without changing the consumer-facing name or schema.

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

#### Repository-derived scoring trace

The repository-owned evaluator must eventually publish:

- `evaluation.axis_facts`
- `evaluation.axis_rule_matches`
- `evaluation.axis_results`

These tables must make this chain queryable:

```text
result → matched rule → normalized fact → recorded evidence → source document
```

Suggested grains:

- `axis_facts`: `(declaration_version_id, product_slug, category_slug, axis, dimension, part_index)`
- `axis_rule_matches`: `(declaration_version_id, product_slug, category_slug, axis, rule_index)`
- `axis_results`: `(declaration_version_id, product_slug, category_slug, axis)`

All three are deterministic over declarations alone. None carries a `release_id`.

The evaluator may reuse existing component parsing and rubric helpers. It must not introduce a second scoring implementation.

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

observation_snapshot_id
  = canonical digest of the normalized observation content, and nothing else

release_id
  = declaration_version_id + observation_snapshot_id + reconciliation_policy_version
```

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

#### Gates key on population, not namespace

`observations` and `evaluation` hold two populations: the ~522 curated gap-map products and the
~24,600 discovered long-tail artifacts. They share namespaces deliberately — a GitHub repo
measurement is the same kind of fact whichever population it belongs to.

Release gates therefore apply to an asset only when `release_path: true`. Applying them by
namespace would fire "missing products or axes" and "mixed release IDs" on
`evaluation.fragility`, which belongs to no gap-map release and has no axes, and the only ways
out would be a permanent exemption list or a sixth namespace. Keying on the declared population
avoids both.

Which gates are shared is narrower than "everything except release completeness". The long-tail
population has `catalog` artifact identities, not accepted `registry` product identities, and it
has no adoption route, no accepted axis assessment and no evidence-freshness state at all.

| Gate | gap_map | long_tail |
|---|---|---|
| Observation schema, units, time fields | yes | yes |
| Source-run lineage and completeness | yes | yes |
| Identity integrity | resolves to `registry.product_artifacts` | resolves to a stable `catalog` artifact identity |
| Adoption routing contract | yes | no — no routes exist for it |
| Evidence and axis freshness | yes | no — no axis assessments exist for it |
| Reconciliation | yes | no |
| Release completeness, projection parity | yes | no |

Long-tail evaluation declares its own contracts where it needs them; it does not inherit the
gap map's. An earlier draft said the observation, routing and freshness gates applied to both,
which would have failed `metrics.daily` for having no registry identity and
`evaluation.fragility` for having no axis freshness — neither of which is a defect.

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

Verified against the live `currentai` org on 2026-08-20: 22 datasets, 96 tables, 44
tracked files under `warehouse/`. The structure below is the target; the file manifest in
11.4 is the exact diff from the state on that date.

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
    catalog/
      openllm_leaderboard.py             renamed in Phase 5
      hf_model_repo_links.py             renamed in Phase 5
    observations/
      source_runs.sql                    the run contract; required from day one
      product_adoption.sql               incremental history — Phase 2B, blocked on OSO
      product_adoption_current.sql       full-refresh now, a view over history later
    evaluation/
      product_adoption_measurements.sql  artifact observations -> product-level bands
      adoption_reconciliation.sql
      axis_facts.sql
      axis_rule_matches.sql
      axis_results.sql
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
      openllm_leaderboard.csv            renamed in Phase 5
      hf_model_repo_links.csv            renamed in Phase 5
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

#### The long-tail chain is retained, and folds into the same five namespaces

The `entities`, `events`, `metrics` and analytical `scores` tables are kept. `oss-ai-trends`
and `long-tail-explorer` are both tagged `Live` on the platform, so retiring the chain would
break shipped deliverables.

Retaining it does NOT require a sixth kind. Checked against actual grains, every table maps
onto the five namespaces of section 4 — the earlier `analysis` proposal was accommodating
legacy naming, not a real semantic gap:

| Today | Target | Why |
|---|---|---|
| `entities.repos`, `.projects`, `.packages`, `.models` | `catalog` | Discovered from the goodailist roster, not curated. `long-tail-explorer` calls them "the discovery set not yet scored in the gap map", which is AD-3's definition of catalog. |
| `events.github_events` | `observations` | Grain `(github_id, repo, event_type, time, event_count)` — artifact-level measurement. |
| `metrics.daily` | `observations` | Grain `(repo, github_id, day, metric, value)` — already long-format `metric`/`value`, which is nearly the corrected 4.3 shape. |
| `scores.*` (8 tables) | `evaluation` | Derived from catalog and observations. |

So the fully-migrated `models/` also contains:

```text
    catalog/
      repos.sql projects.sql packages.sql models.sql
    observations/
      github_events.sql daily.sql
    evaluation/
      dependency_graph.sql fragility.sql ossd_coverage.sql
      project_summary.sql repos_summary.sql stack_contributors.sql
```

Two populations, one set of namespaces. The gap map is ~522 curated products; the long tail is
~24,600 discovered artifacts. They share `observations` and `evaluation` because
`signal_github.repo_state` and `metrics.daily` are both measurements of GitHub repositories and
should not live in separate worlds permanently. What keeps the gates coherent is that release
gates key on POPULATION, not namespace — see 11.2's `release_path` field and section 7.

Phase 0 records these as `target_namespace` and changes nothing. The moves land in Phase 5, so
no inventory PR touches a Live notebook.

All file counts in this section must be regenerated mechanically in Phase 0 rather than
maintained in prose. Every count previously written here by hand was wrong.

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

**`kind` is semantic; the namespace is where the table lives today.** These disagree for
every legacy `entities`, `events`, `metrics`, `scores` and `evidence` table, which is the
entire point of the migration. A gate requiring them to match cannot inventory the current
system without misdescribing it. Record both, and require equality only after migration.

**Dependency fields are derived, not authored.** They come from parsing model bodies,
`build/` modules, notebooks and workflows, then get verified in CI. Nothing here is
hand-maintained, because a hand-maintained dependency list drifts exactly like the two
registries this file replaces.

```yaml
- id: scores.stack_contributors
  table: currentai.scores.stack_contributors
  files:                          # keyed by role; every managed file appears in exactly one
    model: warehouse/models/scores/stack_contributors.sql
    schema: null
    data: null
  kind: evaluation                # registry | catalog | observations | evaluation | releases
  current_namespace: scores       # where the table lives today
  target_namespace: evaluation    # where the architecture puts it
  migration_status: pending       # pending | in_progress | complete | not_planned
  authority: repo                 # repo | platform | external
  grain: one row per (developer, repo), trailing 365d COMMIT_CODE
  reads:                          # DERIVED
    - table: currentai.catalog.stack_map
      scope: internal
    - table: oso.int_events__github_unified
      scope: external
  read_by:                        # DERIVED across ALL closure roots of 11.3
    models: []
    build: []
    notebooks: []                 # verified: long-tail-explorer reads repos_summary,
                                  # entities.models, entities.packages and catalog.stack_map
                                  # — NOT this table
    workflows: []
  consumer_scope: in_repo_only    # in_repo_only | platform_checked | externally_confirmed
                                  # so this asset is NOT yet a retirement candidate,
                                  # however empty read_by looks
  external_consumers: unknown     # unknown | none_confirmed | [named]
  publication_role: null          # null | release_sink | public_api | payload_input
  population: long_tail           # gap_map | long_tail | both
  release_path: false             # true only if this asset belongs to a gap-map release
  refresh: dataset cron '0 4 * * 1'
  timezone: UTC
  last_observed_trigger: null     # no SCHEDULED run observed in run history
  owner: carl
  status: active                  # active | staged | deprecated | historical | compatibility
  replacement:
  retirement_reason: null         # set only when the derived test below passes
  retirement_issue: null
  verified_at: '2026-08-20'
```

For `authority: platform`, a `mirror:` block is required. This replaces
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
AND consumer_scope is at least platform_checked
AND no deployed platform model reads it
```

`consumer_scope` is what stops the inventory from overclaiming. `in_repo_only` means nobody
has checked beyond the repository, so an empty `read_by` is not yet evidence of anything, and
the asset cannot be a retirement candidate no matter how unread it appears. Promoting an
asset to `platform_checked` requires actually querying deployed model definitions.

There is no stored `retirement_candidate` boolean. The condition is computed; only the human
outputs — `retirement_reason` and `retirement_issue` — are recorded.

### 11.3 Scope: what the inventory covers

The inventory covers the transitive closure of what the repository ships or maintains. The
roots are:

```text
warehouse/                 30 SQL and Python model files
build/                     the validators, serializers and gates
notebooks/                 the four tracked notebooks
.github/workflows/         the eight workflows and what they invoke
generated public projections   build/notebook_data.json and the front-end payload contract
```

`build/` is a root, not an afterthought. Three modules there hold real queries:

```text
build/apply_scores.py     scores.openness_computed          (TABLE constant)
build/check_parity.py     scores.openness_computed          (TABLE constant)
build/check_artifacts.py  signal_github.repo_state          (SELECT)
                          signal_pypi.package_downloads     (SELECT)
```

An earlier draft rooted the closure at `warehouse/` and the notebooks alone, which would have
reported those tables as having no in-repo consumer and made each a false retirement
candidate. `check_parity.py` is the gate protecting the openness dual-run; scoring its input
as unread would have been a serious error.

That same draft then claimed EIGHT `build/` modules read tables directly, listing
`check_adoption.py`, `check_rubric.py`, `publish_registry.py`, `serialize_scores.py` and
`warehouse.py` alongside the three above. Those five mention tables only in prose — module
docstrings and `#` comments. `build/warehouse.py` is the clearest case: its docstring's usage
example reads `query("SELECT product_slug FROM currentai.scores.openness_computed")`, which is
an illustration, not a query.

The lesson is a rule for the derivation, not a footnote: **strip comments AND docstrings
before counting a reference, and never all string literals.** Comments and docstrings are
prose that names tables freely; string literals hold the real SQL. A grep that ignores the
distinction invents consumers in one direction and, if it stripped every literal, would lose
them in the other.

On 2026-08-20 the closure is 49 of the org's 96 tables.

The remaining 47 are separate analytical products that the gap-map pipeline neither feeds
nor reads — `state_of_os_ai`, `ai_demand_curve`, `aiid`, `hf_live`, `openrouter_snapshot`,
`datasette_plugins`, `linkedin_sources`, the archived `stack_map` v1 dataset, and four
`catalog` tables with no in-repo consumer. They stay on the platform and stay out of
`assets.yaml`. Keeping them out is what allows `kind` to remain the five namespaces of
section 4 with no sixth catch-all.

The closure is mechanical, so it must be recomputed rather than assumed. Three tables that
look out of scope are in it: `catalog.country_populations` and `catalog.pypi_downloads`
are read by the tracked `pypi-geo-trends.py`, and `catalog.foundation_model_repos` is read
by `entities_models.sql`.

### 11.4 File manifest

The diff from 2026-08-20 state. Because the mirror layout keeps each file's base name and
only changes its directory, almost every move is a pure `git mv` — reviewable as a rename
rather than a rewrite.

Counts, stated once and correctly:

```text
warehouse/ tracked files today                        44
  of which SQL/Python models                          30   (12 models, 3 ingest, 15 mirror)
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
| `warehouse/models/README.md` | Per-table detail to `assets.yaml`; enduring prose to `docs/architecture/data-architecture.md`, which avoids creating a seventh file that was never in the Create list. It currently claims 25 datasets against an actual 22, documents 5 `catalog` tables against an actual 10, and records `catalog.goodailist_repos` as retired while the table is live. |
| `warehouse/catalog/.gitkeep` | Directory retired. |

`top_models.csv` and `tracked_models.csv` are NOT deleted. An earlier draft listed them as
orphans loading no table; they are the interface between the two fetchers —
`fetch_huggingface.py` writes both and `fetch_model_benchmarks.py` reads both at line 91.
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
2. `current_namespace` matches the namespace in the deployed `table`. `target_namespace`
   matches what `kind` implies. Equality between the two is required only when
   `migration_status: complete`; a mismatch otherwise must name a migration phase or an open
   issue. `kind: observations` in a `signal_*` namespace is permanently legitimate per 4.3.
   An earlier draft required `kind` to equal the table's namespace outright, which would have
   rejected every legacy `entities`, `events`, `metrics`, `scores` and `evidence` asset — and
   this section's own worked example.
2b. Release-completeness and projection-parity gates apply only to assets with
   `release_path: true`. Every asset declares `population`; an asset with `release_path: true`
   and `population: long_tail` is a contradiction and fails.
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
   `consumer_scope: in_repo_only` may be reported as a retirement candidate.
8. Every entry in `reads` either resolves to an asset in the inventory when
   `scope: internal`, or is `scope: external` and names a table outside the 49-table closure.
   Because the inventory deliberately covers the closure rather than all 96 org tables,
   `oso.*` and out-of-scope `currentai.*` reads must be representable rather than errors.
9. Deprecated assets carry a removal condition; active `compatibility` assets name a
   replacement or state why none exists.
10. No test asserts that a backlog must remain non-empty.

The inventory must not claim visibility into untracked external consumers. `read_by` covers
in-repo consumers only; represent confidence about anything beyond that explicitly.

### 11.6 Decisions resolved 2026-08-20, and what remains

Resolved by looking, not by asking. Each was an open question in an earlier draft that the
repository or the platform already answered:

| Question | Answer | Evidence |
|---|---|---|
| Do the two orphan CSVs get deleted? | No. They are the interface between the two fetchers. | `fetch_huggingface.py` writes both, `fetch_model_benchmarks.py` reads both at line 91 |
| Is `registry.tail_products` misfiled? | No, correctly in `registry`. The platform table is absent because it is empty. | `publish_registry.py`: "94 bytes of header on a push where every tail row was promoted or rejected" — promotion and rejection are curator acts |
| May a `held` axis retain its value? | Yes, with the hold reason and date. | `verification_queue.yaml`: "held at 3" |
| Is a dated null `held` or `not_applicable`? | Neither — it is `confirmed`. | `verification_queue.yaml`: "a null answer that somebody looked for and did not find is a confirmed axis" |
| Is the long-tail chain retired? | No. Retained and migrated into the five namespaces. | `oss-ai-trends` and `long-tail-explorer` are both tagged `Live` on the platform |
| Does the platform support release-scoped tables? | No. Each static-model publish replaces in place. | No version or revision field; `registry.product_scores` has `createdAt == updatedAt` |

Resolved by decision:

| Decision | Resolution | Lands in |
|---|---|---|
| Sixth `kind` for the long-tail chain | Not needed. `entities` to `catalog`, `events`/`metrics` to `observations`, `scores` to `evaluation` | Recorded Phase 0, moved Phase 5 |
| Gates over two populations | Key on `release_path`, not namespace | Section 7 |
| Publication atomicity | `releases.*` atomic from birth; compatibility outputs documented non-atomic | Sections 12.2, 18 |
| `catalog.model_benchmarks` -> `openllm_leaderboard` | Do it, with the `entities` to `catalog` move that creates the collision | Phase 5 |
| `catalog.model_repos` -> `hf_model_repo_links` | Same | Phase 5 |
| `repo_state` / `hub_state` -> `artifact_state` | Do it, with the observations adapters that repoint the same SQL | Phase 2 |
| Untracked notebook audit | Added to Phase 0. Sixteen of twenty notebooks are not in the repository | Phase 0 |
| `catalog.stack_map` archive note | Record the correction in Phase 0; apply it in Phase 1, since a description edit is still a platform write | Phase 0 records, Phase 1 applies |

No rename is performed as a standalone change. Each rides a phase that already repoints the
same SQL, so no PR exists purely to rename a deployed table.

#### Deferred pending the Phase 0 notebook audit

Three tables have no in-repo consumer and cannot be retired on that basis, because
`consumer_scope: in_repo_only` is not evidence of anything while sixteen notebooks sit outside
the repository. Each keeps `retirement_reason: null` and an open issue until the audit promotes
its `consumer_scope` to `platform_checked`.

| Table | State |
|---|---|
| `catalog.goodailist_repos` | Documented retired, table live, superseded by `signal_goodailist.repo_catalog` |
| `scores.investment_ranking` | On the platform with no repository source and no in-repo reader |
| `scores.taxonomy` | Same |

`oss-ai-gaps` and `stack_map_category_maps`, both tagged `Deprecated`, are the plausible
readers of the latter two. Plausible is not checked.

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

- every active data asset has one named semantic role, owner, grain, and refresh mechanism;
- curated declarations live in `registry`, discovered inventory in `catalog`, measurements in `observations`, derived candidates and trace in `evaluation`, and valid snapshots in `releases`;
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
