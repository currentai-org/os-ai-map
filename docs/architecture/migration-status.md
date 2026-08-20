# Migration status

Temporary phase state and the retirement ledger. Rules live in `data-architecture.md`; this
file records only where the work has got to. Delete a row when it stops being temporary.

**As of 2026-08-20.**

## Phase state

| Phase | State | Note |
|---|---|---|
| 0 — architecture record and inventory | in review | This PR. Read-only; no platform writes. |
| 1 — schedule normalization | not started | 13 datasets on `America/New_York`, 8 crons with no observed run. Also applies the `catalog.stack_map` description fix recorded below. |
| 2 — normalized adoption observations | not started | Must compile `registry.adoption_routes` before any signal roll-up retires. |
| 2B — incremental adoption history | blocked | Blocked on OSO incremental-model support. Not approximated with full-refresh models. |
| 3 — reconciliation report | not started | Report-only first. |
| 4 — blocking agreement gate | not started | |
| 5 — catalog split and long-tail migration | not started | 31 assets carry `migration_status: pending`. |
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

Phase 0 performs no platform write. This is handed to Phase 1.

**`catalog.stack_map` dataset description.** Dataset `3d049fc1-de36-47e1-bc8a-649d4b7d5963`.

Current text asserts: *"Frozen at 2026-05-29 and read by no deployed model; retained for
reference only."*

The second clause is false. `warehouse/models/scores_stack_contributors.sql` reads it in a
`WHERE ... IN (SELECT repo FROM currentai.catalog.stack_map)`, and four notebooks read it
directly: `long-tail-explorer` (tracked, Live), `ai-contribution-load` and
`stf-ai-stewardship-evidence` (both updated 2026-08-20) and `launch-insights`.

Replacement text for that clause: *"Frozen at 2026-05-29 and superseded for scoring, but
still read by `currentai.scores.stack_contributors` and by four notebooks; migrate those
consumers before dropping it."*

Leaving the false claim in place is how a table gets dropped by someone acting in good
faith.

## Retirement ledger

No asset has been retired. Candidates below satisfy the derived condition in
`data-architecture.md` 11.2 — no in-repo code reader, no platform notebook consumer, no
publication role, and `consumer_scope: platform_checked`. None is authorized for deletion;
section 17 requires explicit maintainer approval after a consumer inventory.

| Asset | Finding |
|---|---|
| `catalog.osai_gap_map` | No consumer anywhere. Also misnamed — it is a third-party map whose columns read as ours. |
| `catalog.osai_subcategory_mapping` | No consumer anywhere. |
| `catalog.taxonomy_crosswalk` | No consumer anywhere. |
| `scores.ossd_coverage` | No consumer anywhere. |
| `signal_github.product_adoption` | Unread in repo, but holds the route precedence `pypi > huggingface > stars` in SQL. **Must not retire before `registry.adoption_routes` compiles that ordering.** |
| `signal_lmarena.text_leaderboard` | Capability anchor collected ahead of the axis that will use it. Pre-positioned, not dead. |
| `signal_semanticscholar.paper_citations` | Citation instrument declared in `signal_routing.yaml`, not yet consumed by a repo model. Pre-positioned. |
| `signal_artificialanalysis.model_evaluations` | The platform description says "held deliberately unjoined to gap-map products". Unread by design. |
| `signal_packages.*` (3) | Staged, not deployed. Issue #314. |

The derived condition cannot tell "nobody wants this" from "nothing uses it yet". Four of
the entries above are the second case, which is why the condition produces candidates for a
person and never a deletion.

## Consumers with only a deprecated reader

Weaker than a live consumer, stronger than none. Recorded so the next pass does not treat
them as unread.

| Asset | Read only by |
|---|---|
| `scores.investment_ranking` | `ai-potluck-partners` (Deprecated) |
| `scores.project_summary` | `ai-potluck-partners` (Deprecated) |

`scores.taxonomy` reads similarly but also has `state-of-os-ai`, which is not deprecated.
