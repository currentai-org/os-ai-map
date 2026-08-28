# Runbook: executing the Phase 5 namespace moves

**Status: EXECUTION RUNBOOK. No move is authorized by this document.** It turns the Phase 5 plan
(`phase5-namespace-migration.md`, the what/why/contract) into concrete, ordered, per-table steps.
Each move is a **maintainer platform action plus an editor reconciliation PR**, run under the
source-preserving lockstep. Nothing here is done until the maintainer authorizes that move.

The pending move set is **5 executable moves + 2 held** (7 `pending` rows total). The former
`entities.*→catalog` (4) and `scores.*→evaluation` (8) relocations are **cancelled** — a scheduled
`USER_MODEL` pipeline cannot be hosted in the static `catalog`/`evaluation` datasets (OSO dataset
type is immutable; platform-verified 2026-08-28). Those 12 tables are `not_planned` and stay in their
own namespaces; see the plan's dataset-type section. The two rides-along renames
(`model_benchmarks→openllm_leaderboard`, `model_repos→hf_model_repo_links`) are **withdrawn** with the
collision that triggered them. Table metadata below was read from `assets.yaml` on 2026-08-28;
re-derive at execution time.

## The lockstep, per move (from the plan §recipe)

0. **[freshness / supersession pre-check — do this first]** Confirm the source is still the **live**
   source and not a stale snapshot superseded by a subscribed/newer dataset (check `assets.yaml`
   `reads`, the `current-state-dag.md` external-source edges, and recent data/scheduled-run). If it is
   superseded, it is **not** a byte relocation — and whether it re-models or is held depends on
   whether the source's data is actually needed and whether the live successor covers it. See
   `catalog.pypi_downloads` in §1 and the plan's Freshness section for the worked case, which turned
   out to be **deferred** (notebook-only, no scoring impact), not a move.
1. **[maintainer / platform]** Create the target table alongside the source (new dataset, or new
   registry static model), source left live and unchanged.
2. **[maintainer / platform, read-only ok]** Verify the target against the source via `pyoso`: row
   count, column schema, and — for a scheduled model — a **successful `SCHEDULED` run on the target**
   (the scheduling gate; required before any canonical consumer is repointed).
3. **[maintainer / platform]** Repoint **deployed** readers (deployed models, published notebooks) to
   the target, source still live.
4. **[editor / repo PR]** Reconcile the repository against the verified live state: repoint in-repo
   consumers, set `assets.yaml` (`current_namespace` = target, `migration_status: complete`,
   `verified_at`, derived `read_by`), regenerate the DAG + count markers, pass the gates. This is the
   reviewable unit; steps 1–3 and 5 are maintainer runbooks.
5. **[maintainer / platform, separate §17 authorization]** Retire the source table only after its
   consumer inventory is clean.

## Dependency order

With `entities.*` and `scores.*` staying put, the remaining moves are nearly independent. Work them:

1. **`events`/`metrics` → `observations`** (2) — scheduled, scheduling gate applies.
2. **`catalog.* → registry`** (3 ownership transitions; the fourth, `stack_map`, is a decision gate).
3. **Held:** `catalog.pypi_downloads` (deferred) and `catalog.stack_map` (decision gate) — neither
   executes until its open question is resolved.

## 1. `catalog.pypi_downloads → observations` — DEFERRED (freshness pre-check, step 0)

**Do NOT move it in the mechanical pass; this is low-stakes and notebook-only.** It is a static
per-country snapshot read by **only** `notebooks/pypi-geo-trends.py`; nothing reads per-country
`country_code` for scoring or signal. Adoption scoring and signal read the live **aggregate**
`oso.pypi_downloads.daily_downloads_by_package` with **trailing-30d/7d** windows, so the ~90-day
rolling window of the per-country successor is **not** a scoring constraint and there is **no G1 item**
here. Leave the static as `pending`, held out of the sweep — its disposition (keep frozen for
year-over-year regional viz, or repoint to a live FULL ~90-day `observations.pypi_downloads` and
retire the static) is decided when that notebook is next touched. **Do not build an incremental
accumulator** — no consumer needs accreted per-country history. The orphan `observations.pypi_downloads`
the platform side stood up has no committed consumer and the notebook stays on the static, so the
**maintainer authorized dropping it (2026-08-28)** — a platform-side delete with no repo reconciliation
(no in-repo consumer, no inventory row). See the plan's Freshness section.

## 2. `events`/`metrics → observations`

| Table | Source dataset | Scheduled | In-repo consumers to repoint |
|---|---|---|---|
| `events.github_events` | `b2109421…` | `0 5 * * 0` | `models/metrics/daily.sql` |
| `metrics.daily` | `5a73a919…` | `0 6 * * 0` | `models/scores/{fragility,project_summary,repos_summary}.sql`, `notebooks/oss-ai-trends.py` |

Both are scheduled — the scheduling gate (step 2) applies: a successful `SCHEDULED` run on the
`observations.*` target must be shown before canonical consumers repoint. This is the specific lesson
the failed semanticscholar pilot encoded. Both are scheduled `USER_MODEL` and the `observations`
dataset (`c507c9f9`, which hosts `product_adoption_current`) is `USER_MODEL`, so the dataset **type**
is compatible — this move clears the wall that stopped `entities`/`scores`.

**Pre-check (schedule granularity).** These two carry different crons (`0 5 * * 0`, `0 6 * * 0`) and
`product_adoption_current` is full-refresh, so co-hosting them in one `observations` dataset requires
**per-model schedules**. OSO exposes a model-level `updateDataModelSchedule`, so schedules are
expected to be per-model (not per-dataset) — confirm this before creating; if a dataset instead
enforces one shared schedule these crons can't fit, **stop and report** (a design decision, not a
force). Create `observations.github_events` **first** and `observations.daily` second: `daily` reads
`github_events`, and the 1-hour cron offset exists to order that dependency — the target `daily` must
read `currentai.observations.github_events`, and its verify run must follow a green `github_events`.

Note: the in-repo consumers to repoint include `scores.*` models. Those models **stay** in `scores`
(dataset-type constraint) — only their *read* of `metrics.daily` changes to the `observations` name;
the models themselves do not move. `metrics.daily` has a wide reader set (deployed
`scores.{fragility,project_summary,repos_summary}`, `state_of_os_ai.{country_activity_monthly,
star_trajectories}`, the Live `oss-ai-trends` notebook, external `state-of-os-ai`; `github_events` is
read externally by `ai-contribution-load`), so the *repoint* is the delicate step — the create+verify
half is safe because nothing reads the targets yet.

## 3. `catalog.* → registry` — ownership transitions (NOT plain moves)

`registry` compiles from `sources/`; `models/registry/` is forbidden (§11.1). So each needs a
canonical `sources/` representation + serializer integration + the registry-publisher path, proven
equal to the current live table before anything repoints. Type-wise this is static→compiled (both
static-class), so it clears the dataset-type constraint that blocked `entities`/`scores`.

| Table | Current owner | Ownership-transition work |
|---|---|---|
| `catalog.foundation_model_repos` | **repo CSV** already: `warehouse/data/catalog/foundation_model_repos.csv` (72 rows) | Data already lives in the repo. Wire it into `build/serialize_registry.py` + `build/publish_registry.py` so it publishes to `registry.foundation_model_repos`, add a golden, repoint its one consumer `models/entities/models.sql`. The lightest of the three. |
| `catalog.osai_subcategory_mapping` | **platform-only** (no repo file) | Export the live table (read-only), design a canonical `sources/` format, author the content, integrate the serializer + publisher, prove compiled == live. **Needs a source-schema design decision.** No in-repo consumer; a deployed reader (`scores.taxonomy`, `scores.investment_ranking`) must be repointed on the platform. |
| `catalog.taxonomy_crosswalk` | **platform-only** (no repo file) | Same as above. **Needs a source-schema design decision.** |

The two platform-only tables are the only Phase-5 items with a genuine repo build attached, gated on
a **canonical-source-schema decision** before authoring — flagged for the maintainer, not built blind.

Note: `models/entities/models.sql` (the consumer of `foundation_model_repos`) stays in `entities`
(dataset-type constraint); only its read of the moved table changes.

## Nuanced — decision required before moving (plan §D)

- **`catalog.stack_map` → registry** — a live compatibility bridge (`replacement:
  registry.product_scores`), repo CSV `warehouse/data/catalog/stack_map.csv`, read by
  `models/scores/stack_contributors.sql` + `notebooks/long-tail-explorer.py`. **Decision gate
  (unauthorized):** (a) repoint consumers to compiler-owned registry tables and retire in place; or
  (b) compile a curated registry table with a separately named temporary compatibility projection.

## What is needed on the platform (summary)

Every sanctioned move needs, per table: a maintainer **create-target** + **verify** (with a fresh
scheduled run for the scheduled tables), **deployed-reader repoint**, and later a §17 **retire**. The
editor reconciliation PR (step 4) is the only repo-side unit and follows the verified live state.
Beyond the five executable moves, two items need a decision before any work: the `catalog.stack_map`
disposition, and the canonical `sources/` schema for `osai_subcategory_mapping` / `taxonomy_crosswalk`.
The one platform action already authorized is the **drop of the orphan `observations.pypi_downloads`**
(§1). No other move, rename, Release, or platform mutation is authorized by this runbook.
