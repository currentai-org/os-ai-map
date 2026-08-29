# Runbook: executing the Phase 5 namespace moves

**Status: EXECUTION RUNBOOK. No move is authorized by this document.** It turns the Phase 5 plan
(`phase5-namespace-migration.md`, the what/why/contract) into concrete, ordered, per-table steps.
Each move is a **maintainer platform action plus an editor reconciliation PR**, run under the
source-preserving lockstep. Nothing here is done until the maintainer authorizes that move.

The pending move set is **3 executable moves + 2 held** (5 `pending` rows total). The former
`entities.*→catalog` (4) and `scores.*→evaluation` (8) relocations are **cancelled** — a scheduled
`USER_MODEL` pipeline cannot be hosted in the static `catalog`/`evaluation` datasets (OSO dataset type
is immutable; platform-verified 2026-08-28). The `events`/`metrics`→`observations` fold (2) is
**deferred (schedule wall)** — an OSO schedule is a dataset-level sweep, and folding them into the
manual `observations` dataset would force a sweep cron onto the §18 `product_adoption_current` (see §2
and the plan's schedule section); whether `observations` ever gains a sweep is a Phase-2B refresh-model
decision, and any later move would need a new explicit decision. All 14 are `not_planned` and stay in
their own datasets. The two rides-along
renames (`model_benchmarks→openllm_leaderboard`, `model_repos→hf_model_repo_links`) are **withdrawn**
with the collision that triggered them. Table metadata below was read from `assets.yaml` on 2026-08-28;
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

With `entities.*`, `scores.*`, `events` and `metrics` all staying put, the remaining moves are
independent. Work them:

1. **`catalog.* → registry`** (3 ownership transitions; the fourth, `stack_map`, is a decision gate).
2. **Held:** `catalog.pypi_downloads` (deferred), `catalog.stack_map` (decision gate), and the
   deferred `events`/`metrics` fold (§2, schedule wall; `not_planned`, any move needs a new decision).

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
**dropped 2026-08-29** (authorized 2026-08-28) — a platform-side delete of the 228M-row orphan, with
durable evidence committed at `warehouse/audits/observations_pypi_downloads_deletion.json` (dataset/
model id, prior revision + schema, `deleted_at`, absence verified). See the plan's Freshness section.

## 2. `events`/`metrics → observations` — DEFERRED (schedule wall)

| Table | Source dataset | Scheduled | In-repo consumers (later) |
|---|---|---|---|
| `events.github_events` | `b2109421…` | `0 5 * * 0` | `models/metrics/daily.sql` |
| `metrics.daily` | `5a73a919…` | `0 6 * * 0` | `models/scores/{fragility,project_summary,repos_summary}.sql`, `notebooks/oss-ai-trends.py` |

**Do NOT move these now.** Verified 2026-08-28: an OSO **schedule is a dataset-level sweep**; a
model's cron only throttles which sweeps it is eligible for, it is not an independent trigger. The
`observations` dataset (`c507c9f9`) is type-compatible (`USER_MODEL`) but currently **manual**
(`cron null`); its `product_adoption_current` runs `MANUAL` under the §18 baseline discipline. `events`
(`0 5`) and `metrics` (`0 6`) carry distinct dataset crons, so folding them into `observations` would
force a sweep cron on that dataset that also swept `product_adoption_current` (and the 228M-row pypi
orphan) — a behavior change to a §18-sensitive model. Giving `observations` a `0 5,6 * * 0` sweep and
throttling the manual models to `@manual` is *possible*, but giving `observations` a sweep at all is a
decision about its **refresh model** that belongs with **Phase 2B** (incremental history, blocked on
OSO) — 2B owns that decision, not this fold. Both tables are `not_planned` and stay in their own
datasets; a later relocation would require a **new explicit architecture decision** re-opening their
disposition, not an automatic Phase-2B follow-on.

**If a future decision does relocate them**, the scheduling gate (step 2) applies — a successful `SCHEDULED` run on each
target before canonical consumers repoint — and `metrics.daily` has a **wide reader set** (deployed
`scores.{fragility,project_summary,repos_summary}` — which stay in `scores`, only their read changes —
plus `state_of_os_ai.{country_activity_monthly,star_trajectories}`, the Live `oss-ai-trends` notebook,
external `state-of-os-ai`; `github_events` is read externally by `ai-contribution-load`), so the
repoint is the delicate step.

**Repo↔platform drift to reconcile first (independent of the move).** The deployed `events.github_events`
(rev 8) and `metrics.daily` (rev 5) read `oso.github_events.github_events_last_365_days`, while the repo
SQL + inventory still read the older `oso.int_events__github_unified` / `oso.*opendevdata*` — repo file
sha256 ≠ the Phase-0b audit's deployed `source_sha256` for both. **Resolved 2026-08-29 (#395):** the
deployed rev-8/rev-5 source was captured from the platform and back-ported verbatim, so the repo SQL
now reads `oso.github_events.github_events_last_365_days` and its file sha256 matches the audit's
deployed `source_sha256` for both — the repo mirrors the warehouse again. (Known follow-up: the
back-ported prose still claims a frozen-history union the SQL no longer performs.)

## 3. `catalog.* → registry` — ownership transitions (NOT plain moves)

`registry` compiles from `sources/`; `models/registry/` is forbidden (§11.1). So each needs a
canonical `sources/` representation + serializer integration + the registry-publisher path, proven
equal to the current live table before anything repoints. Type-wise this is static→compiled (both
static-class), so it clears the dataset-type constraint that blocked `entities`/`scores`.

| Table | Current owner | Ownership-transition work |
|---|---|---|
| `catalog.foundation_model_repos` | **repo CSV** already: `warehouse/data/catalog/foundation_model_repos.csv` (72 rows) | **DONE in the repo (in_progress overall).** Data moved to `sources/foundation_model_repos.yaml`, wired into `build/serialize_registry.py` (+ auto-published by `publish_registry.py` via CI on merge), golden added (compiled == the live CSV), consumer `models/entities/models.sql` repointed. Remaining: a maintainer repoints the deployed `state_of_os_ai.family_footprint` reader, then §17 retires `catalog.foundation_model_repos`. The lightest of the three; no platform create needed (CI publishes registry). |
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
Beyond the three executable moves (the `catalog.*→registry` ownership transitions), two items need a
decision before any work: the `catalog.stack_map` disposition, and the canonical `sources/` schema for
`osai_subcategory_mapping` / `taxonomy_crosswalk`.
The one platform action already authorized is the **drop of the orphan `observations.pypi_downloads`**
(§1). No other move, rename, Release, or platform mutation is authorized by this runbook.
