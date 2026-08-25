# Migration status

Temporary phase state and the retirement ledger. Rules live in `data-architecture.md`; this
file records only where the work has got to. Delete a row when it stops being temporary.

**As of 2026-08-20; deployed-model audit (Phase 0b) 2026-08-22; Phase 1 verified 2026-08-23.**

## Phase state

| Phase | State | Note |
|---|---|---|
| 0 — architecture record and inventory | done | Merged (#345). The repository now mirrors the warehouse. |
| 0b — deployed model audit | done | Merged (#347). All 41 deployed model definitions read; `platform_models` `checked` on every asset; receipt at `warehouse/audits/platform_models.json`. |
| 1 — schedule normalization | done | Applied (#349) and **verified 2026-08-23**: all ten in-scope datasets fired a `SCHEDULED` run on their UTC cron (01:00–06:00Z Sunday), the run-history proof §13 requires; 3 out-of-scope analytical datasets left on `America/New_York` deliberately. <!-- count:unobserved_crons -->10 assets still have no observed run, all outside Phase 1's scope. Two model runs failed on the scheduled fire — a transient `ConnectTimeout` on `metrics` (cleared on re-run) and a reproducible upstream `429` on `signal_semanticscholar.paper_citations` — but neither is a schedule defect; see the note below. `docs/operations/normalize-schedules.md` carries the per-dataset evidence. |
| 2 — normalized adoption observations | done | **2A done**: `registry.adoption_routes` + `adoption_route_scopes` / `adoption_route_band_sets` / `adoption_aggregation_rules` compiled from `signal_routing.yaml` and merged (#351), materialized on the platform 2026-08-23 (7 / 1 / 20 / 1 rows). **`source_runs` shipped** (#356). **`artifact_state` source-table rename applied** (Part B runbook): `signal_github.repo_state` and `signal_huggingface.hub_state` twinned to `signal_github.artifact_state` / `signal_huggingface.artifact_state` on the platform, the three consumers repointed and redeployed, and the old tables kept as `compatibility` assets (each naming its replacement) until their step-6 retirement. **`observations.product_adoption_current` deployed** (2026-08-24) — the artifact-level, band-free current-state normalization over the four deployed adoption sources; the deploy created the `observations` namespace, and the first run materialized 654 rows over 392 products (`authority: repo`, deployed from the repo SQL). **The declared-identity guard is deployed and enforced** (2026-08-25, revision 3, `a27b153d-76d8-4661-8fcb-4ee4802cb164`). The live model resolves `product_type` by joining `registry.product_artifacts` on `(product_slug, artifact_kind, artifact_id)`, replacing the pre-guard `registry.products` slug join, and FAILs the materialization on any observation whose artifact is not declared for that product. The materialization SUCCEEDED, which is the coverage proof: 654 rows over 392 products, grain unique on all 654, `product_type` non-null on every row, per-channel counts unchanged (github 305, huggingface 189, pypi 136, arxiv 24). `warehouse/audits/platform_models.json` was regenerated against the deployed state and now records source SHA `33a9f760c2701b6926ea3af1479f2aca7f02c0094393592f41d9c2ccdcf1ef08`, matching the repo SQL byte for byte, and `registry.product_artifacts` among the reads. **`observations.product_adoption_baseline` captured** (2026-08-24T22:27:44Z) — §18 requires one preserved baseline snapshot for the temporary full-refresh period, and because `product_adoption_current` is full-refresh (every run overwrites), the deployed state is preserved only by freezing it. The 654 rows over 392 products are now immutable bytes at `warehouse/data/observations/product_adoption_baseline.parquet` (file sha256 `84e0d5747c5963617fd712688bce14210389104f218f624f66aceddace1fa569`, writer-independent content sha256 `3a942c39c203b4d2aa962d1709fa3ca1b045ff17673ed5b00899b259777f9a9b`), with the receipt at `warehouse/audits/product_adoption_baseline.json`. It records honestly that `source_run_id` is NULL for all 654 rows and that no authoritative row-to-run binding exists (#355); no run id is inferred. The baseline is a frozen data asset, not a query, so it carries no platform table and is inventoried `staged` / `materialized: false`. The per-source banding roll-ups retire later, once the evaluation layer + reconciliation replace them. |
| 2B — incremental adoption history | blocked (follow-up) | **Blocked on OSO incremental-model support (issue #352).** Per §18 the architecture migration is explicitly **partially complete on observation history** until this lands: the adoption→reconciliation layer ships on the full-refresh `product_adoption_current` plus the frozen baseline, but append-only history is NOT marked complete until an incremental platform run has been observed. 2B builds forward from the already-captured baseline when OSO incremental lands. The stable latest-state contract `observations.product_adoption_current` (full-refresh + `observed_at`) ships in Phase 2; the bare name `observations.product_adoption` is reserved for the incremental append-only history table, created only when OSO supports it. The `observations.product_adoption_baseline` frozen-bytes snapshot was captured in **Phase 2**, not here (2026-08-24, 654 rows) — it is the immutable anchor the append-only history builds **forward** from, and it already exists for 2B to build on. `_current` is not renamed into `product_adoption` — its grain is current-state, and a consumer of the current-state table must not silently inherit a historical grain. |
| 3 — reconciliation report | done | **Both fully-keyed evaluation tables built as repo-side release builders**, keyed on `declaration_version_id` + `observation_snapshot_id`. **`evaluation.product_adoption_measurements`** (`build/adoption_measurements.py`) aggregates the artifact-level `observations.product_adoption_current` to the product level. Route selection is **by declared artifacts** (`registry.product_artifacts`) and the recorded instrument, first applicable route by `registry.adoption_routes` precedence + `adoption_route_scopes`, then an observation is sought on that route only — **no fallthrough** to a weaker route when the authoritative observation is missing (a PyPI-declared product is never scored on GitHub stars). Applicability now spans **all** routes, not just machine ones: `signal_routing.yaml` gained unbridged `npm`/`crates` authoritative usage routes (ranked after the bridged download channels, before stars) and the hand-authored `active_users`/`reported_traction` routes are selected by the recorded instrument — so an `active_users` product with a GitHub repo, or an npm-only product, is left **unmeasured on its authoritative route** rather than scored on stars. Aggregation by `adoption_aggregation_rules`: both `usage_volume` and `stars_fallback` sum across a family's artifacts (`sum_stars_across_artifacts` added to `signal_routing.yaml`, matching the deployed compatibility model's `SUM(stargazers_count)` and the recorded assessments); banding by `adoption_route_band_sets` → `adoption_bands`, stars capped by the band set. Numbers are preserved, never `int()`-truncated. It reinterprets none of that — the routing compiler is the one owner. **`evaluation.adoption_reconciliation`** (`build/adoption_reconciliation.py`) compares measured vs recorded adoption, **report-first**, over **every recorded adoption assessment** (measured, unmeasured, and the deliberate nulls) — one terminal outcome per applicable route. It **never compares across instrument types**: a `delta` is computed only when the measured and recorded instruments match; a cross-instrument row withholds the delta and is classified `route_mismatch` (an authoritative instrument on either side) or `expected_difference` (both weak signals), not turned into a number. A same-instrument measured row is `source_unavailable` today because observations carry no `source_run_id` (row-to-run binding blocked on #355), exactly as §4.3 requires; the fuller status set activates once #355 binds observations to runs. Both tables carry `routing_policy_version` (now **2**), so the routing policy that produced them travels with the output — `declaration_version.py`'s binding is now split: **bound** to the evaluation tables, **pending** for `release_id` until Phase 8. The two builders read the current table once and derive the snapshot id and both tables from that one atomic row set; `build/serialize_evaluation.py` serializes the publishable static-model CSVs (live via pyoso or the baseline), and both are exercised in-repo against the immutable Phase-2 baseline with pinned goldens (`tests/test_adoption_evaluation.py`). **Deployed 2026-08-25**: the `evaluation` dataset was created (`55a4311d-7659-4811-a4c5-7ff167ef5eef`) and both tables published as static models — 377 measurement rows and 522 reconciliation rows, one identity pair throughout (declaration `8d3e9d8df10d…`, snapshot `9bd4d93a6fc6…`, `routing_policy_version` 2), archived at `build/evaluation/deployments/8d3e9d8df10d-9bd4d93a6fc6/`. Both are now inventoried `active` / `materialized: true`. The deploy was cut over the committed Phase-2 baseline rather than `--live`, which was broken at the time (`load_current_observations` did not coerce the VARCHAR-transported `observed_at`); the baseline was confirmed digest-identical to the deployed current table that day, so the published bytes are what `--live` would have produced. #369 subsequently fixed that coercion, so `--live` now works. The publish also had to fix the publisher itself: `createStaticModelRunRequest` took an invalid `{staticModelId}` input, and a request naming both models fans out into two runs that race to create the dataset's Trino schema — one failed while the returned sibling reported `SUCCESS`. Runs are now requested one model at a time and awaited in turn. **Phase 4's blocking gate stays disabled**: every measured row is `source_unavailable` until row-to-run binding lands (#355), so publishing the report is sound and gating on it is not. |
| 4 — blocking agreement gate | blocked (follow-up) | **Required by AD-5 and §18, not yet active.** A fresh authoritative adoption disagreement is a release blocker and must not enter a release silently (AD-5; §18 "fresh authoritative adoption disagreement cannot enter a release silently"), so the gate is NOT removed from the architecture — it is blocked. Its input is authoritative row-to-run binding (#355): while every measured reconciliation row is `source_unavailable`, the gate has nothing to act on. That `source_unavailable` is the **accepted interim state** (§18), not a final one; the gate activates once #355's binding lands. #355's platform mechanism may come from OSO's incremental-model work (Kariba OSO-4705), but #355 stays independently open until live row-to-run emission and authoritative binding are demonstrated. |
| 5 — catalog split and long-tail migration | not started | <!-- count:pending -->36 assets carry `migration_status: pending`. |
| 6 — repository-owned scoring trace | not started | |
| 7 — retire duplicate openness computation | not started | |
| 8 — release manifests | not started | |

**The adoption observation → reconciliation thread ships the working report; per §18 the
architecture migration is explicitly *partially complete* on observation history.** Row-to-run
binding (#355), the Phase-4 blocking gate it feeds (required by AD-5), and the incremental
append-only history (Phase 2B) are **blocked follow-up**, bundled with OSO's incremental-model
support (issue #352; #355's run-id mechanism may come from Kariba OSO-4705, but #355 closes on its
own row-to-run evidence). The **accepted interim state** (§18) is a preserved baseline, a
full-refresh `product_adoption_current`, a working `evaluation.adoption_reconciliation` with every
measured row `source_unavailable`, and the blocked 2B/4 items above — sound to publish, and unsound
to gate on until the binding lands (§4.3). It is not the final state: append-only history is not
marked complete until an incremental platform run is observed, and the gate activates when #355
lands. Phases 5–8 remain separate in-scope tracks, unaffected by this.

## Versioning identities

Prerequisites for the fully-keyed evaluation tables (`evaluation.product_adoption_measurements`,
`evaluation.adoption_reconciliation`, `registry.axis_assessments`), which key on identities that
did not yet exist in code. Laid ahead of those tables so each is defined once, on its own, rather
than improvised inside the first consumer.

- **`declaration_version_id` — implemented** (`build/declaration_version.py`, `data-architecture.md`
  §4.5). Commit-scoped (it embeds `source_git_sha`), derived at run time rather than stored, and
  refused over a worktree that disagrees with `HEAD` — a dirty tracked file (declarations or
  identity/evaluator code) or an untracked file under `sources/` — without an explicit diagnostic
  opt-in; the digest itself reads only git-tracked files. Its `source_content_digest` covers every authoritative
  declaration input under `sources/` — the full top-level inventory is classified and gated, so
  `evidence_policy.yaml` and `verification_queue.yaml` (which `load_sources` does not return) are
  folded in, while `signal_routing.yaml` (its `routing_policy_version` now **bound to the evaluation
  tables** — carried as a column on `evaluation.adoption_reconciliation` and
  `evaluation.product_adoption_measurements` — with the `release_id` binding still **pending** until
  Phase 8), the frozen long-tail sample, and the derived score projections are excluded from the
  **digest** — not from the id, which changes with any commit that touches them. `evaluator_version` is pinned to the sentinel `v0-no-repo-evaluator` until
  the repository-owned evaluator lands (Phase 6).
- **`observation_snapshot_id` — implemented** (`build/observation_snapshot.py`, `data-architecture.md`
  §4.5), as the two distinct things §4.5 names. **`observation_content_digest`** is a SHA-256 over
  the normalized observation content and nothing else — the ten measurement columns of
  `product_adoption_current` as an order-independent multiset, excluding lineage, capture time, the
  derived `observation_id`, `is_valid`, and `supersedes_observation_id`, with `observed_at`
  normalized to UTC (naive interpreted as UTC) at fixed precision. **`observation_snapshot_id`** is
  the identity reconciliation and `release_id` key on: it binds the `canonicalization_version` into
  the content digest, so a persisted id names its rule. Derived at run time, not stored; a
  merge-base ratchet forbids a serializer change without a version bump. Both digests are pinned
  against the immutable Phase-2 baseline as fixed contracts.

## Atomicity: which state is in force

**Transitional.** Verified 2026-08-20: static models carry no version or revision list, and
`registry.product_scores` reports `createdAt == updatedAt`, so each publish replaces in
place. There is no native release-scoped materialization.

Consequently, and per `data-architecture.md` 12.2:

- `releases.*` does not exist yet. When it does, it is release-scoped with a pointer from
  birth and is atomic.
- `registry.product_scores`, `build/notebook_data.json` and the published notebooks are
  replace-in-place and are **NOT atomic**.
- Definition-of-done clause "joining current public tables cannot mix releases silently" is
  **met for release-aware consumers** and **UNMET for compatibility consumers**. Do not mark
  it complete on the strength of the first half.

## Recorded platform changes, not yet applied

Phase 0 performs no platform write. Anything here is handed to a later phase with credentials.

**Mirror header references to the retired `README.md` / `manifest.yaml`.** The mirror-layout
restructure deleted `warehouse/platform-mirror/README.md` and `manifest.yaml`, but the moved
mirror files still open with `-- See README.md and manifest.yaml in this folder`, now a dead
reference. Those bytes are provenance-locked: each mirror's recorded `local_sha256` binds them,
and the merge-base gate treats any byte change as a refetch that must also advance `revision`,
`hash` and `synced_at`. A local edit alone would break the hash gate or fabricate provenance,
and a credentialed refetch alone will not fix it while the deployed source still carries the
line. The remediation is therefore ordered and platform-side:

1. update the header in each platform-owned model source (in `currentai-org/{tools,udms}/`);
2. release a new revision of each affected model;
3. refetch those revisions into the mirror under `warehouse/models/<dataset>/`;
4. update each mirror's `revision`, `hash`, `local_sha256` and `synced_at` together.

The Phase 1 schedule normalization is **complete** — applied 2026-08-22 and verified 2026-08-23,
recorded in the phase table above and in `docs/operations/normalize-schedules.md`. All ten in-scope
datasets fired a `SCHEDULED` run on their UTC cron, so `assets.yaml` records `last_observed_trigger:
SCHEDULED` and `last_run_at: '2026-08-23'` for the fifteen affected assets alongside `timezone: UTC`.
Nothing there is outstanding.

**Two deployed-model failures surfaced on the first scheduled fire — tracked here, not Phase 1
blockers.** The schedule is what Phase 1 changed and what it verified; whether a model's own body
then succeeds is separate. Both failing models fired exactly on their UTC cron.

1. `metrics.daily` failed its 06:00Z run on a transient `ConnectTimeout` while materializing. A
   manual re-run the same morning succeeded, so this was infrastructure flakiness, not a defect;
   the model is healthy.
2. `signal_semanticscholar.paper_citations` failed its 01:00Z run on an upstream Semantic Scholar
   HTTP `429` (`semantic scholar batch returned 429 for 24 ids`), and a manual re-run failed
   identically — reproducible, not a blip. Root cause: the deployed UDM has no 429 backoff/retry,
   unlike the repo's own `warehouse/models/catalog/model_repos.py`. The fix (backoff, or an
   authenticated Semantic Scholar key) is a **platform-owned model change** under §17, out of Phase
   1's scope. Its only in-repo consumer is `observations.product_adoption_current`, now deployed
   but itself terminal — its Phase 3 consumers are not built — so no live scoring pipeline is
   affected. Recorded for a maintainer; not acted on here.

**No description or schema change is pending.** An earlier draft of this file recorded a
correction for the `catalog.stack_map` dataset description, on the grounds that its "read by no
deployed model" claim was false. That was a conflation of two differently-named tables and is
withdrawn.

The distinction is worth writing down, because the names invite the mistake:

| Table | Dataset | State | Read by |
|---|---|---|---|
| `currentai.stack_map.*` | `stack_map` (`3d049fc1`), **ARCHIVED 2026-08-20** | 9 frozen v1 tables | No deployed model. Two notebooks: `stack_map_category_maps` (Deprecated) and `state-of-os-ai` (not deprecated) |
| `currentai.catalog.stack_map` | `catalog` (`046ee25e`), live | The repo-to-warehouse taxonomy bridge | `warehouse/models/scores/stack_contributors.sql`, plus four notebooks including the Live `long-tail-explorer` |

The archive note sits on the first and is accurate about deployed models.
`docs/reference/where-scores-live.md` already draws this line correctly: it records
`stack_map.*` as archived with no deployed reader, and `catalog.stack_map` as "Live and
stale… Read by `scores.stack_contributors`".

What the note omits, and what this inventory adds, is that `stack_map.*` has two notebook
readers and one of them is not deprecated. "No deployed model" and "no reader" are different
claims, and only the first is true.

## Assets with no reviewed consumer

**Retirement candidates: <!-- count:retirement_candidates -->5.** Phase 0b read all 41 deployed
model definitions in the org, so `consumer_checks.platform_models` is now `checked` on every
asset and the derived candidate list is non-empty for the first time. It is **recorded, not
acted on**: section 17 requires explicit maintainer authorization, a stated rollback path and a
consumer inventory before any deletion. This phase produces the inventory only — no `DROP`, no
dataset deletion, no description or model change. Three are tracked in issue #348 and the two
newly published `evaluation` tables in #355, which each entry references in `retirement_issue`; a
`TBD` placeholder no longer satisfies that field.

The <!-- count:no_reviewed_consumer -->5 assets below are **deployed** and have **no reviewed
consumer**: no in-repo code reader, no consumer among the twenty notebooks in the organization,
and no deployed platform model reads them. `external` stays `unknown` — nothing outside this org
was read — so this is still weaker than "no consumer" and is not itself grounds for deletion.

A not-in-service asset is a different state and is **not** listed here. `signal_packages.product_adoption`
has no consumer only because it is staged and deployed nowhere (issue #314); a model that has
not entered service cannot be retired, so `retirement_candidates()` excludes `staged` and
`dormant` by construction, and the staged `signal_packages` models carry `materialized: false`.
`observations.product_adoption_baseline` is absent for the same reason and a different one: it is
staged because it has no platform table at all — the asset is frozen bytes in the repository — and
it is unread because a baseline is read when there is history to compare against it, which Phase 2B
(#352) has yet to produce. It is a pre-positioned immutable anchor, and the one thing it must never
be is deleted: it is the only surviving copy of the first `observations` state.

Four assets left this list when the audit found a platform-model reader with no repository
source, invisible to the repo-derived graph until the model definitions were read — exactly the
gap Phase 0b existed to close. `catalog.osai_gap_map`, `catalog.osai_subcategory_mapping` and
`catalog.taxonomy_crosswalk` are read by the deployed `scores.taxonomy` (the first two also by
`scores.investment_ranking`), and `signal_lmarena.text_leaderboard` by
`ai_demand_curve.model_capability_current`. All four now carry `platform_model_consumers`.

The derived condition cannot tell "nobody wants this" from "nothing uses it yet", which is why
it produces a list for a person and never an action. Several entries are pre-positioned inputs.

`signal_semanticscholar.paper_citations` left this list in Phase 2: the new
`observations.product_adoption_current` reads it as the citations channel, so it now has an
in-repo reviewed consumer. It was the clearest "pre-positioned, not yet consumed" case, and the
observations layer is what consumes it.

`observations.product_adoption_current` joined this list in Phase 2 when it deployed with no
reader, and **left it in Phase 3**: `build/adoption_measurements.py` now reads it to build
`evaluation.product_adoption_measurements`, so it has an in-repo reviewed consumer and the derived
predicate no longer fires. It was the clearest "nothing uses it yet" case, and the evaluation
rollup is what now uses it.

Both `evaluation` tables joined this list on 2026-08-25, the day they were published, and for the
same reason `observations.product_adoption_current` was on it a phase earlier: the consumer is the
next phase's. The Phase-4 blocking gate is the reader, blocked follow-up (see the phase table): it
stays disabled while every measured reconciliation row is `source_unavailable` for want of
authoritative row-to-run binding (#355). The gate is still **required** by AD-5/§18; `source_unavailable`
is the **accepted interim state**, not a final one, and the gate activates once #355 lands (its
run-id mechanism may come from OSO incremental / OSO-4705, but #355 closes on its own evidence).
Publishing the
report before gating on it is deliberate, so these two are the clearest current case of the blind
spot named above — a table nothing uses **yet** — and neither is a deletion candidate.

| Asset | Finding |
|---|---|
| `scores.ossd_coverage` | No reviewed consumer, in repo or on the platform. |
| `signal_github.product_adoption` | Unread everywhere reviewed, but holds the route precedence `pypi > huggingface > stars` in SQL. **Must not retire before `registry.adoption_routes` compiles that ordering** — nothing would fail if it did. |
| `signal_artificialanalysis.model_evaluations` | The platform description says "held deliberately unjoined to gap-map products". Unread by design. |
| `evaluation.product_adoption_measurements` | Published 2026-08-25. Read in-repo only as candidate rows by the reconciliation builder; the deployed table's reader is the Phase-4 gate, held on #355. |
| `evaluation.adoption_reconciliation` | Published 2026-08-25. The report is the deliverable; the Phase-4 gate that would consume it is required by AD-5 but blocked follow-up, not enabled while every measured row is `source_unavailable` (#355, the accepted interim state) — the binding's mechanism may come from OSO incremental / OSO-4705, but #355 closes on its own evidence. |

## Consumers with only a deprecated reader

Weaker than a live consumer, stronger than none. Recorded so the next pass does not treat
them as unread.

| Asset | Read only by |
|---|---|
| `scores.investment_ranking` | `ai-potluck-partners` (Deprecated) |
| `scores.project_summary` | `ai-potluck-partners` (Deprecated) |

`scores.taxonomy` reads similarly but also has `state-of-os-ai`, which is not deprecated.
