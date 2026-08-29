# Plan: Phase 5 — catalog split and long-tail namespace migration

**Status: PLAN FOR REVIEW. No asset is moved and no platform mutation is authorized by this
document.** It classifies the assets carrying `migration_status: pending`, resolves which
`target_namespace` values are genuinely sanctioned versus misfiled, out-of-phase, or physically
impossible, orders the sanctioned moves, and states the per-move execution recipe. Execution lands as
separate, individually reviewed units.

## What Phase 5 is

The architecture (`data-architecture.md` §4, §11.1) folds every table into five *kinds* —
`registry`, `catalog`, `observations`, `evaluation`, `releases`. Phase 0 recorded each pending table's
`target_namespace` and changed nothing. Phase 5 performs the moves that are both sanctioned by kind
**and** physically realizable. It is **independent of the `evaluator_version` cutover** and of the
OSO-incremental-blocked tracks (2B, 4).

Two scope corrections have since reshaped the census:

- **2026-08-26 (semanticscholar rollback):** a pilot that relocated
  `signal_semanticscholar.paper_citations` to `observations` was rolled back — §4.3 keeps
  source-specific ingestion in `signal_*`. The misfiled `target_namespace: observations` values were
  corrected to stay put, and the gate `test_source_collectors_are_not_reclassified_to_observations`
  now protects source collectors.
- **2026-08-28 (dataset constraints, #393):** the planned `entities.*→catalog` (4) and
  `scores.*→evaluation` (8) relocations are **cancelled** (type wall), and the `events`/`metrics`
  →`observations` fold (2) is **deferred** (schedule wall) — see the constraint section below. All 14
  scheduled models are now `not_planned` in their own namespaces, dropping `pending` 19→5. (The
  refresh-model question that could revisit the fold is Phase 2B's; a later move would need a new
  explicit decision — Phase 2B does not perform it.)

## The dataset constraints — why the scheduled pipelines do not move

Two facets of the same rule (**one type and one sweep schedule per dataset**) stop the scheduled
pipelines from folding into shared namespaces.

### Type — why `entities.*` and `scores.*` do not move

An OSO **namespace is a dataset**, and a dataset's type — `STATIC_MODEL` (upload / compiled) or
`USER_MODEL` (scheduled SQL) — is **fixed at creation and immutable** (there is no `type` field to
update; the API rejects a schedule on a static dataset outright). The two target namespaces are
static, and the twelve tables routed into them are scheduled:

- `currentai.catalog` is a `STATIC_MODEL` dataset (`046ee25e`); `entities.repos/models/packages/
  projects` are a scheduled `USER_MODEL` pipeline (`663132ed`, cron `0 4 * * 0`).
- `currentai.evaluation` is the static compiled release-artifact dataset (`55a4311d`: `axis_*`,
  `adoption_*`); the analytical `scores.*` are a scheduled `USER_MODEL` pipeline (`48ddf155`, cron
  `0 4 * * 1`).

A scheduled model cannot be hosted in a static dataset. **Platform-verified on the catalog case
2026-08-28:** a create / revision / release of a scheduled `catalog.repos` all reported success, then
the run request failed — dataset type `STATIC_MODEL`, a scheduled model needs `USER_MODEL`. The
created model was deleted; catalog was left untouched. Rebuilding `catalog`/`evaluation` as
`USER_MODEL` is not a fix either: it would orphan their static tables, which cannot live in a
`USER_MODEL` dataset. So the scheduled discovery and scoring pipelines **keep their own `USER_MODEL`
namespaces**; `catalog` and `evaluation` remain the static layers they already are.

The `kind` fields stay `catalog` / `evaluation` — the logical model is intact. Only `target_namespace`
moves back to `current_namespace`, under the `migration_status: not_planned` exception to
`target_namespace == kind` (§11.5 rule 2). The 12 rows carry a `not_planned_reason` recording all of
the above.

**The two rename collisions are consequently dropped.** `catalog.model_benchmarks →
openllm_leaderboard` and `catalog.model_repos → hf_model_repo_links` existed only to disambiguate the
`catalog.models` name the `entities→catalog` move would have created. That move never happens, so
there is no collision, and §11.6 forbids a PR that exists purely to rename a deployed table. Both keep
their current names (recorded WITHDRAWN in §11.6).

### Schedule — why `events`/`metrics` do not move (deferred)

`events`/`metrics` are `kind: observations` and `observations` is `USER_MODEL`, so the **type** is
compatible — they first looked like clean moves. But an OSO **schedule is a dataset-level sweep**; a
model's cron only *throttles* which sweeps it is eligible for (`""` = every sweep), it is not an
independent trigger (platform-verified 2026-08-28 via `updateDataModelSchedule`). The `observations`
dataset (`c507c9f9`) is currently **manual** — `cron null`, and its `product_adoption_current` runs
`MANUAL` under the §18 baseline discipline (every run overwrites current state; the frozen baseline
must never be disturbed). `events` (`0 5 * * 0`) and `metrics` (`0 6 * * 0`) carry distinct dataset
crons; folding them into `observations` would force a sweep cron on that dataset that also swept
`product_adoption_current` (and the 228M-row pypi orphan) — a behavior change to a §18-sensitive
model. Giving `observations` a sweep and throttling the manual models is possible, but whether
`observations` becomes swept at all is a decision about its **refresh model** that belongs with
**Phase 2B** (incremental history, currently blocked on OSO) — 2B owns that decision, not this fold.
So `events`/`metrics` are **deferred**: `not_planned`, kept in their own datasets. A later relocation
would require a **new explicit architecture decision** re-opening their disposition, not an automatic
Phase-2B follow-on.

**Emerging pattern.** Type and schedule are both per-dataset and (type) immutable, so an
independently-typed or independently-scheduled pipeline (`entities`, `scores`, `events`, `metrics`)
cannot fold into a shared namespace. Phase 5's real remaining work is therefore the compiled
`catalog.* → registry` ownership transitions; the live pipelines keep their own datasets.

## The pending assets, classified

Derived at write time from `assets.yaml` via `build.assets` (not hand-listed). `pending` now holds
**5** rows; the 14 constraint-blocked tables and the earlier 6 corrections are `not_planned`.

### A. Sanctioned, type-compatible relocations

| Move | Tables | Authority |
|---|---|---|
| `catalog.*` → `registry` (3) | `foundation_model_repos`, `osai_subcategory_mapping`, `taxonomy_crosswalk` | §2 — "curator-controlled and belong in `registry`"; static→compiled. **Ownership transitions, not SQL repoints — see §Registry ownership.** |
| `catalog.pypi_downloads` → `observations` (1) | `pypi_downloads` | §2 — "a measurement". **DEFERRED — notebook-only, no scoring impact; see §Freshness.** |

So of the 5 pending, **three are executable moves** (the `catalog.*→registry` ownership transitions)
and **two are held** — `pypi_downloads` (deferred) and `stack_map` (decision gate, §D).

### B. `not_planned` — do not move (type / schedule constraint, 2026-08-28)

`kind` is correct; the physical target dataset cannot host the model — either its **type** is
immutable-and-wrong, or hosting it would force a **shared sweep schedule** on a dataset that must stay
manual (see the dataset-type and schedule sections). Each stays in its current namespace with a
`not_planned_reason`.

| Tables | Kind | Stays in | Why |
|---|---|---|---|
| `entities.repos`, `.projects`, `.packages`, `.models` (4) | `catalog` | `entities` | scheduled `USER_MODEL`; `catalog` is a static dataset (type wall) |
| `scores.dependency_graph`, `.fragility`, `.investment_ranking`, `.ossd_coverage`, `.project_summary`, `.repos_summary`, `.stack_contributors`, `.taxonomy` (8) | `evaluation` | `scores` | scheduled `USER_MODEL`; `evaluation` is a static dataset (type wall) |
| `events.github_events` (1) | `observations` | `events` | own weekly sweep (`0 5 * * 0`); folding into the manual `observations` dataset would force a sweep cron onto the §18 `product_adoption_current`. **Deferred** (schedule wall); any later move needs a new explicit decision |
| `metrics.daily` (1) | `observations` | `metrics` | own weekly sweep (`0 6 * * 0`); same schedule wall. **Deferred** (schedule wall) |

### C. Earlier corrections / out-of-phase retirement targets (6) — landed #392

Kept here for the record; all `not_planned`, `target_namespace = current_namespace`:

| Asset | Correct disposition | Why |
|---|---|---|
| `signal_github.product_adoption` | Stay in `signal_*`; `status: compatibility`, `replacement: observations.product_adoption_current`; retire in place | transitional compatibility asset, not relocated |
| `signal_huggingface.product_adoption` | same | same |
| `signal_packages.product_adoption` | same (already `staged`) | same |
| `scores.openness_facts` | Phase 7 / §9.3 retirement target, not a move | replaced by `evaluation.axis_*` (#384) |
| `scores.openness_computed` | same | same |
| `evidence.product_evidence` | Phase 7 / §9.3 retirement target, not a move | §9.3 retires it by name; no `product_evidence` in the target layout |

### D. Nuanced — sequence/decide with care (1)

| Asset | Note |
|---|---|
| `catalog.stack_map` → `registry` | **Decision gate — a direct relocation is NOT authorized until resolved.** It is `status: compatibility` naming `registry.product_scores` as `replacement`, and `models/registry/` is forbidden, so it cannot simply be moved into `registry`. Choose one: **(a)** repoint its consumers (`scores.stack_contributors` and four notebooks, one Live) to compiler-owned registry tables and **retire `catalog.stack_map` in place**; or **(b)** compile its curated identity mapping into a new registry table (via `sources/` + the registry publisher) while retaining a **separately named** compatibility projection temporarily. Resolve (a) vs (b) before its execution unit. |

(The former nuanced `scores.investment_ranking` / `scores.taxonomy` are now in tier B — they are
scheduled `scores.*` and stay put under the dataset-type constraint.)

## Registry ownership: the three `catalog.*` → `registry` moves are not clean relocations

`models/registry/` **does not exist and must not** (§11.1): every registry table is serialized from
`sources/` by `build/serialize_registry.py` + `build/publish_registry.py`; there is no authored model
to repoint. So `foundation_model_repos`, `osai_subcategory_mapping`, and `taxonomy_crosswalk` cannot
"repoint SQL and deploy into `registry`" — each is an **ownership transition** whose unit must specify:

1. **Current owner and format.** `foundation_model_repos` is a hand-maintained CSV;
   `osai_subcategory_mapping` and `taxonomy_crosswalk` are **platform-authoritative today with no
   repository file** — the data lives only on the platform.
2. **Canonical source format under `sources/`** — the declaration file(s) the table will be compiled
   from (schema, identity, validation), authored once so the repository, not the platform, is the
   authority. **`osai_subcategory_mapping` / `taxonomy_crosswalk` need a source-schema design decision
   before authoring** (flagged for the maintainer).
3. **Serializer/compiler integration** — extend `build/serialize_registry.py` (and its validation
   suite) to emit the table, with goldens.
4. **Ownership transfer** — export the current platform/CSV content, load it into the new `sources/`
   format, and prove the compiled output equals the current live table before anything is repointed.
5. **Registry-publisher path** — publish via `build/publish_registry.py` as a registry static model.

Type note: this move is static→compiled (both static-class), so unlike `entities`/`scores` it clears
the dataset-type constraint. It is a larger unit than a plain namespace move and is planned as such.

## Freshness / supersession pre-check (before ANY move)

`target_namespace` records where a table's *kind* belongs — not whether that specific table is still
the **live source**. A table can be correctly classified by kind yet be a **stale snapshot superseded
by a newer subscribed/deployed source**, in which case relocating its bytes would enshrine dead data
in the target namespace. So every candidate gets a freshness/supersession check before it is eligible
to move — derivable from the repo's own Phase-0 mapping (`current-state-dag.md` external-source edges,
`warehouse/audits/platform_models.json`, `assets.yaml` `reads`): is the table live (recent scheduled
run / current data), or is there an `oso.*` subscription or newer model that already supersedes it?

**`catalog.pypi_downloads` is exactly this case.** It is a **static, manual-upload snapshot** (`day,
package, country_code, downloads`), frozen `2025-05-01 → 2026-05-01`, feeding only the
`pypi-geo-trends` notebook. Its live analogue `oso.pypi_downloads.daily_downloads_by_package_country`
is a **~90-day ROLLING WINDOW** (verified 2026-08-28: 87 distinct days), not a growing archive — it
cannot reproduce the static's prior-year history.

**The ~90-day window is NOT a scoring constraint — history is not needed for our purposes.** Adoption
scoring and signal (`signal_pypi.package_downloads`, `signal_packages.downloads`) read the live
**aggregate** `oso.pypi_downloads.daily_downloads_by_package` with **trailing-30d / 7d** windows; a
snapshot measures recent adoption, not deep history, and the code already accepts 90-day-max sources
by design (crates.io serves only 90 days). So the rolling window is ample for scoring and signal, and
there is **no data-foundation ceiling and no G1 item here.**

**Corrected disposition (2026-08-28) — low-stakes, viz-only, deferred:** the static per-country
`catalog.pypi_downloads` is read by **only** the `pypi-geo-trends` notebook; nothing reads per-country
`country_code` for scoring or signal. So its move is not urgent and touches no scoring path:

- Leave `catalog.pypi_downloads` as `pending` but **held out of the mechanical Phase-5 pass** — it is
  a notebook-only concern, decided when that notebook is next touched, not part of the move sweep.
- **Do not build an incremental accumulator** — nothing needs accreted per-country history. When the
  notebook is addressed, the choice is simply: keep the static frozen for year-over-year regional
  viz, **or** repoint it to a live `observations.pypi_downloads` (FULL, ~90-day per-country) and
  retire the static, accepting a rolling-window regional view.
- The orphan `observations.pypi_downloads` the platform side stood up has **no committed consumer**
  (scoring/signal don't use per-country) and the notebook stays on the static, so it is a large `FULL`
  table nothing reads. **Maintainer authorized dropping it (2026-08-28)** — a platform-side delete.
  It has no in-repo consumer and no inventory row, but declared-state discipline still requires
  **durable deletion evidence**: after the delete, record a receipt at
  `warehouse/audits/observations_pypi_downloads_deletion.json` (dataset id, model id, prior
  revision/schema, `deleted_at`, and post-delete verification that the table is absent — e.g. a
  refreshed platform census), and commit it in a short repo PR. The deletion is not "done" until that
  evidence is in the repo.

(If per-country geo later becomes a *signal* input, it is still a live ~90-day table read with recent
windows — no history accumulation — so this stays a small, forward decision.)

## Dependency order

A reader must move (or be repointed) no earlier than the table it reads. With `entities.*`, `scores.*`,
`events` and `metrics` all staying put, the remaining moves are independent:

1. **The three `catalog.*→registry` ownership transitions** (each its own larger unit).
2. **Held:** `catalog.pypi_downloads` (deferred), `catalog.stack_map` (decision gate), and the
   deferred `events`/`metrics` fold (Phase 2B) — none executes until its open question is resolved.

## Per-move execution recipe — lockstep, source-preserving (each move its own reviewed unit)

> The concrete, ordered, per-table steps (datasets, in-repo consumers to repoint, scheduling checks)
> live in `docs/operations/phase5-execution-runbook.md`. This section is the generic recipe.

Modeled on the proven Phase-2 `repo_state`/`hub_state` → `artifact_state` twinning, never a
cut-over-in-place:

1. **Create the target alongside the source.** Stand up the new table (new dataset, or new registry
   static model) while the source table remains live and unchanged.
2. **Verify the target** — schema, row counts, and (for scheduled models) refresh behavior against the
   source, plus the consumer inventory.
3. **Repoint consumers, while the source remains available** — split by who writes:
   - **3a. Deployed-reader repointing is a platform write** — a **separately authorized maintainer
     action**, never done by an editor unit.
   - **3b. Repository consumer changes** (`build/`, in-repo notebook sources) land in the lockstep
     **reconciliation PR** of step 4 — **after** the target (step 2) and the deployed repoints (3a)
     are verified.
4. **Reconcile the repository against verified live state** and merge: update `assets.yaml` (new
   namespace, `migration_status: complete`, `verified_at`, derived `read_by`), regenerate the DAG and
   count markers (`build/assets.py`), and pass the gates (`build.validate`, `count_claim_violations`,
   `tests/test_assets_inventory.py`).
5. **Retire the source later, under separate authorization** (§17), only after the consumer inventory
   is clean.

**Scheduling gate (the lesson of the failed pilot).** A move **into `observations`** must preserve its
refresh contract and **demonstrate a successful scheduled run on the target before canonical consumers
are repointed** (step 3a). A move that silently drops a table's schedule is the Phase-1-class defect
this gate exists to catch; `metrics.daily` and `events.github_events` are scheduled and carry this
obligation **only if a future explicit decision relocates them** (the deferred fold is not on any
phase's execution path today).

No editor unit performs a platform write. The create-and-verify (steps 1–2), the **deployed-reader
repointing (3a)**, and the retirement (step 5) are maintainer runbooks authorized separately; the
editor PR is the step-4 reconciliation carrying the repository consumer changes (3b).

## Explicitly out of scope for Phase 5

- Retiring the three `signal_*.product_adoption` compatibility tables (a §17 act; Phase 5 only
  corrects their inventory disposition).
- Retiring `scores.openness_facts`, `scores.openness_computed`, and `evidence.product_evidence`
  (Phase 7 / §9.3, gated on multi-release dual-run agreement, #384).
- Relocating `entities.*` or `scores.*` — cancelled by the dataset-type constraint; they stay in their
  own `USER_MODEL` namespaces. Folding `events`/`metrics` into `observations` — deferred by the schedule
  constraint; they stay in their own datasets, and any later move needs a new explicit decision.
- Any platform mutation — every unit above is an editor PR; the create-alongside, verify, and retire
  steps are maintainer runbooks authorized separately.

## Appendix — `catalog.osai_gap_map` (not in the pending census)

`osai_gap_map` carries `maturity`/`parity_verdict`/`overall_score` (§2) that read as gap-map
**outputs**, not curated registry rows, and it is read by the deployed `scores.taxonomy` /
`scores.investment_ranking`. It does **not** carry `migration_status: pending`, so it is not a
Phase-5 move. Whether it is eventually classified `evaluation` (an output) or `registry` is a separate
architecture decision, recorded here only so the question is not lost.
