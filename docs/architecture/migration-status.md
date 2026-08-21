# Migration status

Temporary phase state and the retirement ledger. Rules live in `data-architecture.md`; this
file records only where the work has got to. Delete a row when it stops being temporary.

**As of 2026-08-20.**

## Phase state

| Phase | State | Note |
|---|---|---|
| 0 — architecture record and inventory | in review | This PR. Read-only; no platform writes. |
| 1 — schedule normalization | not started | <!-- observed:2026-08-20 -->10 datasets on `America/New_York`; <!-- count:unobserved_crons -->18 assets have a cron and no observed run. No platform metadata change is pending — see below. |
| 2 — normalized adoption observations | not started | Must compile `registry.adoption_routes` before any signal roll-up retires. |
| 2B — incremental adoption history | blocked | Blocked on OSO incremental-model support. Not approximated with full-refresh models. |
| 3 — reconciliation report | not started | Report-only first. |
| 4 — blocking agreement gate | not started | |
| 5 — catalog split and long-tail migration | not started | <!-- count:pending -->34 assets carry `migration_status: pending`. |
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

**Retirement candidates: <!-- count:retirement_candidates -->0.** Not zero because everything
is read, but because no asset can be a candidate while `consumer_checks.platform_models` is
`unknown` — and it is unknown for every asset. Deployed model definitions have not been
audited. That is Phase 0b.

The <!-- count:no_reviewed_consumer -->9 assets below have **no reviewed consumer**: no
in-repo code reader, and no consumer among the twenty notebooks in the organization. That is
a weaker claim than "no consumer", and it is not grounds for deletion. Section 17 requires
explicit maintainer approval after a consumer inventory, and the inventory is not complete
until platform models are read.

Four of the nine are pre-positioned inputs rather than dead ends. The derived condition
cannot tell "nobody wants this" from "nothing uses it yet", which is why it produces a list
for a person and never an action.

| Asset | Finding |
|---|---|
| `catalog.osai_gap_map` | No reviewed consumer. Also misnamed — a third-party map whose columns read as ours. |
| `catalog.osai_subcategory_mapping` | No reviewed consumer. |
| `catalog.taxonomy_crosswalk` | No reviewed consumer. |
| `scores.ossd_coverage` | No reviewed consumer. |
| `signal_github.product_adoption` | Unread in repo, but holds the route precedence `pypi > huggingface > stars` in SQL. **Must not retire before `registry.adoption_routes` compiles that ordering** — nothing would fail if it did. |
| `signal_lmarena.text_leaderboard` | Capability anchor collected ahead of the axis that will use it. Pre-positioned. |
| `signal_semanticscholar.paper_citations` | Citation instrument declared in `signal_routing.yaml`, not yet consumed by a repo model. Pre-positioned. |
| `signal_artificialanalysis.model_evaluations` | The platform description says "held deliberately unjoined to gap-map products". Unread by design. |
| `signal_packages.product_adoption` | Staged and not deployed. Issue #314. Its two siblings, `downloads` and `downloads_daily`, DO have reviewed model consumers and are not listed here. |

## Consumers with only a deprecated reader

Weaker than a live consumer, stronger than none. Recorded so the next pass does not treat
them as unread.

| Asset | Read only by |
|---|---|
| `scores.investment_ranking` | `ai-potluck-partners` (Deprecated) |
| `scores.project_summary` | `ai-potluck-partners` (Deprecated) |

`scores.taxonomy` reads similarly but also has `state-of-os-ai`, which is not deprecated.
