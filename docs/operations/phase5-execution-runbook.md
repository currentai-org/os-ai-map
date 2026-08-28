# Runbook: executing the Phase 5 namespace moves

**Status: EXECUTION RUNBOOK. No move is authorized by this document.** It turns the Phase 5 plan
(`phase5-namespace-migration.md`, the what/why/contract) into concrete, ordered, per-table steps.
Each move is a **maintainer platform action plus an editor reconciliation PR**, run under the
source-preserving lockstep. Nothing here is done until the maintainer authorizes that move.

The pending move set is **16 sanctioned relocations + 3 nuanced** (19 total; the six corrected
`not_planned` assets are excluded — they retire/supersede in place). Table metadata below (datasets,
in-repo consumers, schedules) was read from `assets.yaml` on 2026-08-28; re-derive at execution time.

## The lockstep, per move (from the plan §recipe)

0. **[freshness / supersession pre-check — do this first]** Confirm the source is still the **live**
   source and not a stale snapshot superseded by a subscribed/newer dataset (check `assets.yaml`
   `reads`, the `current-state-dag.md` external-source edges, and recent data/scheduled-run). If it is
   superseded, it is **not** a byte relocation — and whether it re-models or is held depends on
   whether the source's data is actually needed and whether the live successor covers it (a
   rolling-window subscription may not carry the history, but the history may not be needed either).
   See `catalog.pypi_downloads` in §2 and the plan's Freshness section for the worked case, which
   turned out to be **deferred** (notebook-only, no scoring impact), not a move.
1. **[maintainer / platform]** Create the target table alongside the source (new dataset, or new
   registry static model), source left live and unchanged.
2. **[maintainer / platform, read-only ok]** Verify the target against the source via `pyoso`: row
   count, column schema, and — for a scheduled model — a **successful `SCHEDULED` run on the target**
   (the scheduling gate; required before any canonical consumer is repointed).
3. **[maintainer / platform]** Repoint **deployed** readers (deployed models, published notebooks) to
   the target, source still live.
4. **[editor / repo PR]** Reconcile the repository against the verified live state: repoint in-repo
   consumers (the `warehouse/models/*` and `notebooks/*` listed per table), set `assets.yaml`
   (`current_namespace` = target, `migration_status: complete`, `verified_at`, derived `read_by`),
   regenerate the DAG + count markers, pass the gates. This is the reviewable unit; steps 1–3 and 5
   are maintainer runbooks.
5. **[maintainer / platform, separate §17 authorization]** Retire the source table only after its
   consumer inventory is clean.

## Dependency order (a reader moves no earlier than what it reads)

`entities.repos` is the foundation — read by ten models (every other `entities.*`, `events`,
`metrics`, and four `scores.*`). Work outward from it:

1. **`entities.* → catalog`** (4) — with the two rename collisions.
2. **`events`/`metrics`/`catalog.pypi_downloads → observations`** (3).
3. **`catalog.* → registry`** (2 sanctioned ownership transitions; the third, `stack_map`, is a
   nuanced decision gate — see below).
4. **analytical `scores.* → evaluation`** (6), then the nuanced `scores.{investment_ranking,
   taxonomy}`.

## 1. `entities.* → catalog` (dataset `663132ed…`, scheduled `0 4 * * 0`)

Rename collisions ride this move (plan §A; §11.6): `catalog.model_benchmarks → openllm_leaderboard`
and `catalog.model_repos → hf_model_repo_links` — do them **with** this move, never as a standalone
rename.

| Table | In-repo consumers to repoint (step 4) |
|---|---|
| `entities.repos` | `models/catalog/model_benchmarks.py`, `models/entities/{models,packages,projects}.sql`, `models/events/github_events.sql`, `models/metrics/daily.sql`, `models/scores/{dependency_graph,fragility,ossd_coverage,project_summary}.sql` |
| `entities.models` | `models/scores/project_summary.sql`, `notebooks/long-tail-explorer.py` |
| `entities.packages` | `models/scores/project_summary.sql`, `notebooks/long-tail-explorer.py` |
| `entities.projects` | `models/scores/project_summary.sql` |

Scheduled: demonstrate a `SCHEDULED` run on the target `catalog.*` before repointing (step 2 gate).

## 2. `events`/`metrics`/`catalog.pypi_downloads → observations`

| Table | Source dataset | Scheduled | In-repo consumers to repoint |
|---|---|---|---|
| `events.github_events` | `b2109421…` | `0 5 * * 0` | `models/metrics/daily.sql` |
| `metrics.daily` | `5a73a919…` | `0 6 * * 0` | `models/scores/{fragility,project_summary,repos_summary}.sql`, `notebooks/oss-ai-trends.py` |
| `catalog.pypi_downloads` | `046ee25e…` | no | `notebooks/pypi-geo-trends.py` |

`github_events` and `daily` are scheduled — the scheduling gate (step 2) applies: a successful
`SCHEDULED` run on the `observations.*` target must be shown before canonical consumers repoint. This
is the specific lesson the failed semanticscholar pilot encoded.

**`catalog.pypi_downloads` is DEFERRED — do NOT move it in the mechanical pass (freshness pre-check,
step 0), but this is low-stakes and notebook-only.** It is a static per-country snapshot read by
**only** `notebooks/pypi-geo-trends.py`; nothing reads per-country `country_code` for scoring or
signal. Adoption scoring and signal read the live **aggregate**
`oso.pypi_downloads.daily_downloads_by_package` with **trailing-30d/7d** windows, so the ~90-day
rolling window of the per-country successor is **not** a scoring constraint and there is **no G1
item** here. Leave the static as `pending`, held out of the sweep — its disposition (keep frozen for
year-over-year regional viz, or repoint to a live FULL ~90-day `observations.pypi_downloads` and
retire the static) is decided when that notebook is next touched. **Do not build an incremental
accumulator** — no consumer needs accreted per-country history. The orphan
`observations.pypi_downloads` the platform side stood up has no committed consumer and the notebook
stays on the static, so the **maintainer authorized dropping it (2026-08-28)** — a platform-side
delete with no repo reconciliation (no in-repo consumer, no inventory row). See the plan's Freshness
section.

## 3. `catalog.* → registry` — ownership transitions (NOT plain moves)

`registry` compiles from `sources/`; `models/registry/` is forbidden (§11.1). So each needs a
canonical `sources/` representation + serializer integration + the registry-publisher path, proven
equal to the current live table before anything repoints.

| Table | Current owner | Ownership-transition work |
|---|---|---|
| `catalog.foundation_model_repos` | **repo CSV** already: `warehouse/data/catalog/foundation_model_repos.csv` (72 rows) | Data already lives in the repo. Wire it into `build/serialize_registry.py` + `build/publish_registry.py` so it publishes to `registry.foundation_model_repos`, add a golden, repoint its one consumer `models/entities/models.sql`. The lightest of the three. |
| `catalog.osai_subcategory_mapping` | **platform-only** (no repo file) | Export the live table (read-only), design a canonical `sources/` format, author the content, integrate the serializer + publisher, prove compiled == live. **Needs a source-schema design decision.** No in-repo consumer; a deployed reader (`scores.taxonomy`, `scores.investment_ranking`) must be repointed on the platform. |
| `catalog.taxonomy_crosswalk` | **platform-only** (no repo file) | Same as above. **Needs a source-schema design decision.** |

The two platform-only tables are the only Phase-5 items with a genuine repo build attached, and it is
gated on a **canonical-source-schema decision** before authoring — flagged for the maintainer, not
built blind.

## 4. analytical `scores.* → evaluation` (dataset `48ddf155…`, scheduled `0 4 * * 1`)

Move after the `catalog`/`entities`/`observations` tables they read have landed (or repoint in the
same unit). All are scheduled → scheduling gate applies.

| Table | In-repo consumers to repoint |
|---|---|
| `scores.dependency_graph` | `models/scores/fragility.sql` |
| `scores.fragility` | `models/scores/project_summary.sql` |
| `scores.repos_summary` | `notebooks/long-tail-explorer.py`, `notebooks/oss-ai-trends.py` |
| `scores.ossd_coverage`, `scores.project_summary`, `scores.stack_contributors` | none in-repo (deployed/notebook readers only) |

## Nuanced — decision required before moving (plan §C)

- **`catalog.stack_map` → registry** — a live compatibility bridge (`replacement:
  registry.product_scores`), repo CSV `warehouse/data/catalog/stack_map.csv`, read by
  `models/scores/stack_contributors.sql` + `notebooks/long-tail-explorer.py`. **Decision gate
  (unauthorized):** (a) repoint consumers to compiler-owned registry tables and retire in place; or
  (b) compile a curated registry table with a separately named temporary compatibility projection.
- **`scores.investment_ranking`, `scores.taxonomy` → evaluation** — read `catalog.osai_*` /
  `entities.*`, so they move after those; only deprecated/notebook readers.

## What is needed on the platform (summary)

Every sanctioned move needs, per table: a maintainer **create-target** + **verify** (with a fresh
scheduled run for the scheduled tables), **deployed-reader repoint**, and later a §17 **retire**. The
editor reconciliation PR (step 4) is the only repo-side unit and follows the verified live state.
Two items additionally need a decision before any work: the `catalog.stack_map` disposition, and the
canonical `sources/` schema for `osai_subcategory_mapping` / `taxonomy_crosswalk`. No move, rename,
Release, or platform mutation is authorized by this runbook.
