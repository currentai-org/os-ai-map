# Plan: Phase 5 — catalog split and long-tail namespace migration

**Status: PLAN FOR REVIEW. No asset is moved and no platform mutation is authorized by this
document.** It classifies the 25 assets carrying `migration_status: pending`, resolves which
`target_namespace` values are genuinely sanctioned versus misfiled, orders the sanctioned moves, and
states the per-move execution recipe. Execution lands as separate, individually reviewed units.

## What Phase 5 is

The architecture (`data-architecture.md` §4, §11.1) folds every table into five namespaces —
`registry`, `catalog`, `observations`, `evaluation`, `releases`. Phase 0 recorded each pending
table's `target_namespace` and changed nothing (§11.1 "Phase 0 records these as `target_namespace`
and changes nothing. The moves land in Phase 5"). Phase 5 performs those moves. It is **independent
of the `evaluator_version` cutover** and of the OSO-incremental-blocked tracks (2B, 4): §"the
adoption thread" note — "Phases 5–8 remain separate in-scope tracks."

**Already done under Phase 5** (2026-08-26 scope correction): a pilot that relocated
`signal_semanticscholar.paper_citations` to `observations` was rolled back — §4.3 keeps
source-specific ingestion in `signal_*`, and §11.6 only sanctions `entities→catalog`,
`events`/`metrics`→`observations`, and the `scores`/`evidence`→`evaluation` cluster. The misfiled
`target_namespace: observations` values on the `signal_*` rows were corrected to stay put, and the
regression gate `test_source_collectors_are_not_reclassified_to_observations` now protects source
collectors. This plan is the continuation of that work.

## The 25 pending assets, classified

Derived at write time from `assets.yaml` via `build.assets` (not hand-listed). Three categories:
sanctioned relocations, corrections (a misfiled or nuanced target that must be fixed **before** any
move), and assets that belong to a different phase.

### A. Sanctioned relocations (16)

| Move | Tables | Authority |
|---|---|---|
| `entities.*` → `catalog` (4) | `repos`, `projects`, `packages`, `models` | §11.1 line 1461; §11.6 (the `entities→catalog` decision) — "the discovery set not yet scored," AD-3's definition of catalog |
| `events.github_events` → `observations` (1) | `github_events` | §11.1 line 1462 — artifact-level measurement grain |
| `metrics.daily` → `observations` (1) | `daily` | §11.1 line 1463 — already long-format `metric`/`value` |
| `catalog.pypi_downloads` → `observations` (1) | `pypi_downloads` | §2 line 48 — "`pypi_downloads` is a measurement" |
| `catalog.*` → `registry` (3) | `foundation_model_repos`, `osai_subcategory_mapping`, `taxonomy_crosswalk` | §2 line 48 — "curator-controlled and belong in `registry`" |
| `evidence.product_evidence` → `evaluation` (1) | `product_evidence` | §11.6 the `evidence`→`evaluation` cluster |
| analytical `scores.*` → `evaluation` (5) | `dependency_graph`, `fragility`, `ossd_coverage`, `project_summary`, `repos_summary`, `stack_contributors` | §11.1 lines 1464/1474–1475 — the retained long-tail analytical chain |

**Renames that ride these moves** (§11.6 lines 1964–1966 — "no PR exists purely to rename a deployed
table"): `catalog.model_benchmarks → openllm_leaderboard` and `catalog.model_repos →
hf_model_repo_links`, both triggered by the `entities.*→catalog` collision, land **with** that move,
not separately.

### B. Corrections required before any move (5) — misfiled or nuanced targets

These are the headline findings of this plan. Each `target_namespace` as currently recorded would
move a table the architecture does **not** relocate.

| Asset | Recorded target | Correct disposition | Why |
|---|---|---|---|
| `signal_github.product_adoption` | `evaluation` ❌ | Stay in `signal_*`; set `status: compatibility`, `replacement: observations.product_adoption_current`; **retire in place** | §11.1 lines 1502–1517, 1545–1548: the three signal `product_adoption` tables are "transitional compatibility assets," retired together once the central evaluator is proven — **not** relocated to `evaluation`. Same class as the semanticscholar misfiling. |
| `signal_huggingface.product_adoption` | `evaluation` ❌ | same | same |
| `signal_packages.product_adoption` | `evaluation` ❌ | same (already `staged`) | same |
| `scores.openness_facts` | `evaluation` ❓ | **Phase 7 retirement target, not a Phase 5 move** | These are the duplicate openness computation that `evaluation.axis_*` replaces; Phase 7 retires them once dual-run agreement holds (#384). Relocating them in Phase 5 would move a table slated for deletion. |
| `scores.openness_computed` | `evaluation` ❓ | same | same |

`signal_github.product_adoption` additionally holds the `pypi > huggingface > stars` route
precedence in SQL (§11.1 lines 1510–1517). `registry.adoption_routes` captured that precedence in
Phase 2A, so the precondition for its eventual retirement is met — but retirement is a §17 act
(explicit authorization, rollback path, consumer inventory) and is **out of Phase 5's scope**; this
plan only corrects the `target_namespace`/`status` so the inventory stops asserting a move that will
never happen.

### C. Nuanced — sequence with care (4)

| Asset | Note |
|---|---|
| `catalog.stack_map` → `registry` | Already `status: compatibility`, `replacement: registry.product_scores`. A live repo-to-warehouse bridge read by `scores.stack_contributors` and four notebooks (one Live). Its move is a bridge relocation with real readers — sequence after its consumers are repointed, or move as a compatibility rename. |
| `scores.investment_ranking` → `evaluation` | Read only by the Deprecated `ai-potluck-partners`; itself reads `catalog.osai_*`, `entities.repos`, `scores.fragility`. Must move **after** the catalog/entities tables it reads, or be repointed in the same unit. |
| `scores.taxonomy` → `evaluation` | Read by `ai-potluck-partners` (Deprecated) and the non-deprecated `state-of-os-ai`; reads `catalog.osai_gap_map`, `catalog.osai_subcategory_mapping`, `catalog.taxonomy_crosswalk`. Same dependency constraint. |
| `catalog.osai_gap_map` | Carries `maturity`/`parity_verdict`/`overall_score` (§2 line 48) that read as gap-map **outputs**, not curated registry rows. Confirm target (`evaluation` vs `registry`) before moving; not yet reclassified here. |

## Dependency order

Namespace moves repoint the SQL that reads a table, so a reader must move (or be repointed) no
earlier than the table it reads. Derived order:

1. **Corrections first (B).** Fix the five misfiled/out-of-phase `target_namespace` values in
   `assets.yaml` (pure inventory + gate; no platform mutation). This makes the pending set describe
   only real Phase-5 moves and adds a regression gate mirroring
   `test_source_collectors_are_not_reclassified_to_observations`.
2. **Leaf tables:** `entities.*→catalog` (with the two rides-along renames), `events`/`metrics`/
   `catalog.pypi_downloads`→`observations`, `catalog.{foundation_model_repos,
   osai_subcategory_mapping, taxonomy_crosswalk}`→`registry`.
3. **Readers of those:** the analytical `scores.*`→`evaluation` set and `evidence.product_evidence`,
   then the nuanced `scores.{investment_ranking, taxonomy}` and `catalog.stack_map` once their
   catalog/entities dependencies have landed.

## Per-move execution recipe (each move is its own reviewed unit)

1. **Repoint the model SQL** to the new dataset and update every in-repo consumer
   (`build/`, notebooks) — the move rides the repoint, never a standalone rename (§11.6 line 1970).
2. **Update `assets.yaml`**: set the new namespace, `migration_status: complete`, `verified_at`, and
   record readers via the derived `read_by`.
3. **Regenerate** the DAG and counts (`build/assets.py`) and update `data-architecture.md` /
   `current-state-dag.md` count markers.
4. **Gates**: `build.validate` → `0 error(s)`; `count_claim_violations()` clean;
   `tests/test_assets_inventory.py` green.
5. **Platform step (maintainer runbook, separate + authorized):** deploy the model to the new
   dataset, verify row/schema parity via `pyoso`, repoint deployed readers, and retire the old table
   under §17. No editor unit performs the platform DROP/CREATE.

## Explicitly out of scope for Phase 5

- Retiring the three `signal_*.product_adoption` compatibility tables (a §17 act; Phase 5 only
  corrects their inventory disposition).
- Retiring `scores.openness_facts` / `scores.openness_computed` (Phase 7, gated on multi-release
  dual-run agreement, #384).
- Any platform mutation — every unit above is an editor PR; the deploy/retire steps are maintainer
  runbooks authorized separately.
