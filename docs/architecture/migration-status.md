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
| 2 — normalized adoption observations | in progress | **2A done**: `registry.adoption_routes` + `adoption_route_scopes` / `adoption_route_band_sets` / `adoption_aggregation_rules` compiled from `signal_routing.yaml` and merged (#351), materialized on the platform 2026-08-23 (7 / 1 / 20 / 1 rows). **`source_runs` shipped** (#356). **`artifact_state` source-table rename applied** (Part B runbook): `signal_github.repo_state` and `signal_huggingface.hub_state` twinned to `signal_github.artifact_state` / `signal_huggingface.artifact_state` on the platform, the three consumers repointed and redeployed, and the old tables kept as `compatibility` assets (each naming its replacement) until their step-6 retirement. Remaining: `observations.product_adoption_current` and the baseline before any signal roll-up retires. |
| 2B — incremental adoption history | blocked | Blocked on OSO incremental-model support (issue #352). The stable latest-state contract `observations.product_adoption_current` (full-refresh + `observed_at`) ships in Phase 2; the bare name `observations.product_adoption` is reserved for the incremental append-only history table, created only when OSO supports it. `_current` is not renamed into `product_adoption` — its grain is current-state, and a consumer of the current-state table must not silently inherit a historical grain. |
| 3 — reconciliation report | not started | Report-only first. |
| 4 — blocking agreement gate | not started | |
| 5 — catalog split and long-tail migration | not started | <!-- count:pending -->36 assets carry `migration_status: pending`. |
| 6 — repository-owned scoring trace | not started | |
| 7 — retire duplicate openness computation | not started | |
| 8 — release manifests | not started | |

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
   1's scope. The asset has no reviewed consumer (pre-positioned per the inventory below), so no
   pipeline is affected. Recorded for a maintainer; not acted on here.

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

**Retirement candidates: <!-- count:retirement_candidates -->4.** Phase 0b read all 41 deployed
model definitions in the org, so `consumer_checks.platform_models` is now `checked` on every
asset and the derived candidate list is non-empty for the first time. It is **recorded, not
acted on**: section 17 requires explicit maintainer authorization, a stated rollback path and a
consumer inventory before any deletion. This phase produces the inventory only — no `DROP`, no
dataset deletion, no description or model change. The four are tracked in issue #348, which each
entry references in `retirement_issue`; a `TBD` placeholder no longer satisfies that field.

The <!-- count:no_reviewed_consumer -->4 assets below are **deployed** and have **no reviewed
consumer**: no in-repo code reader, no consumer among the twenty notebooks in the organization,
and no deployed platform model reads them. `external` stays `unknown` — nothing outside this org
was read — so this is still weaker than "no consumer" and is not itself grounds for deletion.

A not-in-service asset is a different state and is **not** listed here. `signal_packages.product_adoption`
has no consumer only because it is staged and deployed nowhere (issue #314); a model that has
not entered service cannot be retired, so `retirement_candidates()` excludes `staged` and
`dormant` by construction, and the staged `signal_packages` models carry `materialized: false`.

Four assets left this list when the audit found a platform-model reader with no repository
source, invisible to the repo-derived graph until the model definitions were read — exactly the
gap Phase 0b existed to close. `catalog.osai_gap_map`, `catalog.osai_subcategory_mapping` and
`catalog.taxonomy_crosswalk` are read by the deployed `scores.taxonomy` (the first two also by
`scores.investment_ranking`), and `signal_lmarena.text_leaderboard` by
`ai_demand_curve.model_capability_current`. All four now carry `platform_model_consumers`.

The derived condition cannot tell "nobody wants this" from "nothing uses it yet", which is why
it produces a list for a person and never an action. Several entries are pre-positioned inputs.

| Asset | Finding |
|---|---|
| `scores.ossd_coverage` | No reviewed consumer, in repo or on the platform. |
| `signal_github.product_adoption` | Unread everywhere reviewed, but holds the route precedence `pypi > huggingface > stars` in SQL. **Must not retire before `registry.adoption_routes` compiles that ordering** — nothing would fail if it did. |
| `signal_semanticscholar.paper_citations` | Citation instrument declared in `signal_routing.yaml`, not yet consumed. Pre-positioned. |
| `signal_artificialanalysis.model_evaluations` | The platform description says "held deliberately unjoined to gap-map products". Unread by design. |

## Consumers with only a deprecated reader

Weaker than a live consumer, stronger than none. Recorded so the next pass does not treat
them as unread.

| Asset | Read only by |
|---|---|
| `scores.investment_ranking` | `ai-potluck-partners` (Deprecated) |
| `scores.project_summary` | `ai-potluck-partners` (Deprecated) |

`scores.taxonomy` reads similarly but also has `state-of-os-ai`, which is not deprecated.
