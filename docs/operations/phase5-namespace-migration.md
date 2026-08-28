# Plan: Phase 5 — catalog split and long-tail namespace migration

**Status: PLAN FOR REVIEW. No asset is moved and no platform mutation is authorized by this
document.** It classifies the 25 assets carrying `migration_status: pending`, resolves which
`target_namespace` values are genuinely sanctioned versus misfiled or out-of-phase, orders the
sanctioned moves, and states the per-move execution recipe. Execution lands as separate,
individually reviewed units.

## What Phase 5 is

The architecture (`data-architecture.md` §4, §11.1) folds every table into five namespaces —
`registry`, `catalog`, `observations`, `evaluation`, `releases`. Phase 0 recorded each pending
table's `target_namespace` and changed nothing (§11.1 "Phase 0 records these as `target_namespace`
and changes nothing. The moves land in Phase 5"). Phase 5 performs those moves. It is **independent
of the `evaluator_version` cutover** and of the OSO-incremental-blocked tracks (2B, 4): "Phases 5–8
remain separate in-scope tracks."

**Already done under Phase 5** (2026-08-26 scope correction): a pilot that relocated
`signal_semanticscholar.paper_citations` to `observations` was rolled back — §4.3 keeps
source-specific ingestion in `signal_*`. The misfiled `target_namespace: observations` values on the
`signal_*` rows were corrected to stay put, and the regression gate
`test_source_collectors_are_not_reclassified_to_observations` now protects source collectors. This
plan continues that work.

## The 25 pending assets, classified — 16 / 6 / 3

Derived at write time from `assets.yaml` via `build.assets` (not hand-listed), and it reconciles:
**16 sanctioned relocations + 6 corrections/out-of-phase retirement targets + 3 nuanced = 25.**
(`catalog.osai_gap_map` is discussed in the appendix as a separate architecture question; it does
**not** carry `migration_status: pending` and is not part of this census.)

### A. Sanctioned relocations (16)

| Move | Tables | Authority |
|---|---|---|
| `entities.*` → `catalog` (4) | `repos`, `projects`, `packages`, `models` | §11.1 line 1461; §11.6 — "the discovery set not yet scored," AD-3's definition of catalog |
| `events.github_events` → `observations` (1) | `github_events` | §11.1 line 1462 — artifact-level measurement grain |
| `metrics.daily` → `observations` (1) | `daily` | §11.1 line 1463 — already long-format `metric`/`value` |
| `catalog.pypi_downloads` → `observations` (1) | `pypi_downloads` | §2 line 48 — "`pypi_downloads` is a measurement". **DEFERRED — not a mechanical move; its live successor is a ~90-day rolling window, so the static table stays and consolidation is a G1 decision. See §Freshness below.** |
| `catalog.*` → `registry` (3) | `foundation_model_repos`, `osai_subcategory_mapping`, `taxonomy_crosswalk` | §2 line 48 — "curator-controlled and belong in `registry`". **These are ownership transitions, not SQL repoints — see §Registry ownership below.** |
| analytical `scores.*` → `evaluation` (6) | `dependency_graph`, `fragility`, `ossd_coverage`, `project_summary`, `repos_summary`, `stack_contributors` | §11.1 lines 1464 / 1473–1476 — the retained long-tail analytical chain; exactly the six files the target `evaluation/` layout lists |

**Renames that ride these moves** (§11.6 lines 1964–1966 — "no PR exists purely to rename a deployed
table"): `catalog.model_benchmarks → openllm_leaderboard` and `catalog.model_repos →
hf_model_repo_links`, both triggered by the `entities.*→catalog` collision, land **with** that move.

### B. Corrections / out-of-phase retirement targets (6) — NOT relocations

Each `target_namespace` as recorded would move a table the architecture does **not** relocate. These
are inventory corrections, landing first, before any move.

| Asset | Recorded target | Correct disposition | Why |
|---|---|---|---|
| `signal_github.product_adoption` | `evaluation` ❌ | Stay in `signal_*`; `status: compatibility`, `replacement: observations.product_adoption_current`; **retire in place** | §11.1 lines 1502–1517, 1545–1548: the three signal `product_adoption` tables are "transitional compatibility assets," retired together once the central evaluator is proven — not relocated. |
| `signal_huggingface.product_adoption` | `evaluation` ❌ | same | same |
| `signal_packages.product_adoption` | `evaluation` ❌ | same (already `staged`) | same |
| `scores.openness_facts` | `evaluation` ❌ | **Phase 7 / §9.3 retirement target, not a move** | §9.3 retires it after dual-run acceptance; `evaluation.axis_*` replaces it (#384). |
| `scores.openness_computed` | `evaluation` ❌ | same | same |
| `evidence.product_evidence` | `evaluation` ❌ | **Phase 7 / §9.3 retirement target, not a move** | §9.3 retires `evidence.product_evidence` **by name** alongside the two `openness_*` tables; the target `evaluation/` layout (§11.1 lines 1473–1476) contains no `product_evidence`. |

`signal_github.product_adoption` additionally holds the `pypi > huggingface > stars` route
precedence in SQL (§11.1 lines 1510–1517). `registry.adoption_routes` captured that precedence in
Phase 2A, so the precondition for its eventual retirement is met — but retiring a compatibility table
is a **§17** act (explicit authorization, rollback path, consumer inventory) — §9.3 governs the
separate openness chain — and is **out of Phase 5's scope**; this
plan only corrects the `target_namespace`/`status` so the inventory stops asserting a move that will
never happen.

### C. Nuanced — sequence with care (3)

| Asset | Note |
|---|---|
| `catalog.stack_map` → `registry` | **Decision gate — a direct `catalog.stack_map → registry` relocation is NOT authorized until resolved.** It is already `status: compatibility` naming `registry.product_scores` as `replacement`, and `models/registry/` is forbidden, so the generated table cannot simply be moved into `registry`. Choose one: **(a)** repoint its consumers (`scores.stack_contributors` and four notebooks, one Live) to existing/new compiler-owned registry tables and **retire `catalog.stack_map` in place**; or **(b)** compile its curated identity mapping into a new registry table (via `sources/` + the registry publisher) while retaining a **separately named** compatibility projection temporarily. Resolve (a) vs (b) before its execution unit. |
| `scores.investment_ranking` → `evaluation` | Read only by the Deprecated `ai-potluck-partners`; itself reads `catalog.osai_*`, `entities.repos`, `scores.fragility`. Must move **after** the catalog/entities tables it reads, or be repointed in the same unit. |
| `scores.taxonomy` → `evaluation` | Read by `ai-potluck-partners` (Deprecated) and the non-deprecated `state-of-os-ai`; reads `catalog.osai_gap_map`, `catalog.osai_subcategory_mapping`, `catalog.taxonomy_crosswalk`. Same dependency constraint. |

## Registry ownership: the three `catalog.*` → `registry` moves are not clean relocations

`models/registry/` **does not exist and must not** (§11.1 line 1492): every registry table is
serialized from `sources/` by `build/serialize_registry.py` + `build/publish_registry.py`; there is
no authored model to repoint. So `foundation_model_repos`, `osai_subcategory_mapping`, and
`taxonomy_crosswalk` cannot "repoint SQL and deploy into `registry`" — each is an **ownership
transition** whose unit must specify:

1. **Current owner and format.** `foundation_model_repos` is a hand-maintained CSV;
   `osai_subcategory_mapping` and `taxonomy_crosswalk` are **platform-authoritative today with no
   repository file** — the data lives only on the platform.
2. **Canonical source format under `sources/`** — the declaration file(s) the table will be compiled
   from (schema, identity, validation), authored once so the repository, not the platform, is the
   authority.
3. **Serializer/compiler integration** — extend `build/serialize_registry.py` (and its validation
   suite) to emit the table, with goldens.
4. **Ownership transfer** — export the current platform/CSV content, load it into the new `sources/`
   format, and prove the compiled output equals the current live table before anything is repointed.
5. **Registry-publisher path** — publish via `build/publish_registry.py` as a registry static model,
   not a `models/` deploy.

Until a unit does all five, the table stays where it is. This is a larger unit than a namespace move
and is planned as such.

## Freshness / supersession pre-check (before ANY move)

`target_namespace` records where a table's *kind* belongs — not whether that specific table is still
the **live source**. A table can be correctly classified by kind yet be a **stale snapshot superseded
by a newer subscribed/deployed source**, in which case relocating its bytes would enshrine dead data
in the target namespace. So every candidate gets a freshness/supersession check before it is eligible
to move — derivable from the repo's own Phase-0 mapping (`current-state-dag.md` external-source edges,
`warehouse/audits/platform_models.json`, `assets.yaml` `reads`): is the table live (recent
scheduled run / current data), or is there an `oso.*` subscription or newer model that already
supersedes it?

**`catalog.pypi_downloads` is exactly this case, and its plan entry is corrected here.** It is a
**static, manual-upload snapshot** (`day, package, country_code, downloads`), frozen `2025-05-01 →
2026-05-01` (1.6M rows), feeding only the `pypi-geo-trends` notebook. It has been **superseded by a
subscribed dataset** `oso.pypi_downloads.daily_downloads_by_package_country` — same grain. **But that
subscribed source is a ~90-day ROLLING WINDOW** (verified 2026-08-28: 87 distinct days, trimmed at
both ends), not a growing archive. It cannot reproduce the static snapshot's prior-year history
(`2025-05 → 2026-05`), and a `FULL` model over it sits at ~90 days forever.

**Corrected disposition (2026-08-28) — this is NOT a clean Phase-5 relocation, and it is DEFERRED:**

- The static `catalog.pypi_downloads` **stays** — it is the only long-history PyPI-geo asset, and the
  `pypi-geo-trends` notebook keeps reading it. Do **not** retire it, do **not** repoint the notebook.
- The move to `observations` therefore cannot be a copy or a straight supersession; it is a
  **consolidation** (a live forward accumulator plus the retained history) whose shape is a **G1
  scope decision** — see the constraint below. So `catalog.pypi_downloads` remains `pending` but is
  **held out of the mechanical Phase-5 pass** until G1 rules; it is not executed here.
- A live `observations.pypi_downloads` modelled over the subscribed source is a **separate
  forward accumulator**. To be worth keeping it must be `INCREMENTAL_BY_TIME_RANGE` on `day` so
  partitions persist after the ~90-day source drops them (a `FULL` model accretes nothing). Until
  it has a purpose or is incremental, it is an orphan and should be made incremental or dropped.

**Data-foundation constraint → G1 board (client-visible):** live PyPI geography is capped at ~90 days.
No year-over-year, no pre-June-2026 baseline; the 39-package static extract is the only long-history
PyPI asset. Any adoption/trend scoring resting on PyPI download geography inherits this ceiling. The
scope call — whether to start accumulating (incremental now, since each day waited falls off the back
irrecoverably) and whether adoption banding should lean on PyPI geo history at all — is a G1
judgement, not a Phase-5 mechanical move.

## Dependency order

A reader must move (or be repointed) no earlier than the table it reads. Derived order:

1. **Corrections first (B).** Fix the six misfiled/out-of-phase `target_namespace` values in
   `assets.yaml` (pure inventory + regression gate; no platform mutation), so the pending set
   describes only real Phase-5 moves.
2. **Leaf tables:** `entities.*→catalog` (with the two rides-along renames); `events`/`metrics`
   →`observations`; the three `catalog.*→registry` ownership transitions (each its own larger unit,
   per above). **`catalog.pypi_downloads` is held out** — deferred pending the G1 decision above.
3. **Readers of those:** the analytical `scores.*→evaluation` set, then the nuanced
   `scores.{investment_ranking, taxonomy}` and `catalog.stack_map` once their dependencies land.

## Per-move execution recipe — lockstep, source-preserving (each move its own reviewed unit)

> The concrete, ordered, per-table steps (datasets, in-repo consumers to repoint, scheduling checks)
> live in `docs/operations/phase5-execution-runbook.md`. This section is the generic recipe.


Modeled on the proven Phase-2 `repo_state`/`hub_state` → `artifact_state` twinning, never a
cut-over-in-place:

1. **Create the target alongside the source.** Stand up the new table (new dataset, or new registry
   static model) while the source table remains live and unchanged.
2. **Verify the target** — schema, row counts, and (for scheduled models) refresh behavior against
   the source, plus the consumer inventory.
3. **Repoint consumers, while the source remains available** — split by who writes:
   - **3a. Deployed-reader repointing is a platform write** — a **separately authorized maintainer
     action** (repointing a deployed model/notebook to the target dataset), never done by an editor
     unit.
   - **3b. Repository consumer changes** (`build/`, in-repo notebook sources) land in the lockstep
     **reconciliation PR** of step 4 — **after** the target (step 2) and the deployed repoints (3a)
     are verified — so the repo is only reconciled against a live state that already holds.
4. **Reconcile the repository against verified live state** and merge (the reconciliation PR that
   carries 3b): update `assets.yaml` (new namespace, `migration_status: complete`, `verified_at`,
   derived `read_by`), regenerate the DAG and count markers (`build/assets.py`), and pass the gates
   (`build.validate`, `count_claim_violations`, `tests/test_assets_inventory.py`).
5. **Retire the source later, under separate authorization** (§17), only after the consumer
   inventory is clean.

**Scheduling gate (the lesson of the failed pilot).** A move **into `observations`**, and any
**scheduled analytical model moving into `evaluation`**, must preserve its refresh contract and
**demonstrate a successful scheduled run on the target before canonical consumers are repointed**
(step 3a). A move that silently drops a table's schedule is the Phase-1-class defect this gate exists
to catch; `metrics.daily` and `events.github_events` are scheduled and carry this obligation.

No editor unit performs a platform write. The create-and-verify (steps 1–2), the **deployed-reader
repointing (3a)**, and the retirement (step 5) are maintainer runbooks authorized separately; the
editor PR is the step-4 reconciliation carrying the repository consumer changes (3b).

## Explicitly out of scope for Phase 5

- Retiring the three `signal_*.product_adoption` compatibility tables (a §17 act; Phase 5 only
  corrects their inventory disposition).
- Retiring `scores.openness_facts`, `scores.openness_computed`, and `evidence.product_evidence`
  (Phase 7 / §9.3, gated on multi-release dual-run agreement, #384).
- Any platform mutation — every unit above is an editor PR; the create-alongside, verify, and retire
  steps are maintainer runbooks authorized separately.

## Appendix — `catalog.osai_gap_map` (not in the pending census)

`osai_gap_map` carries `maturity`/`parity_verdict`/`overall_score` (§2 line 48) that read as gap-map
**outputs**, not curated registry rows, and it is read by the deployed `scores.taxonomy` /
`scores.investment_ranking`. It does **not** carry `migration_status: pending`, so it is not one of
the 25 and not a Phase-5 move. Whether it is eventually classified `evaluation` (an output) or
`registry` is a separate architecture decision, recorded here only so the question is not lost.
