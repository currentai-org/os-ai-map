# History models: review package (2026-11-23)

This is the review that ruling R-2026-11-21-g asks for before any observation-history model
becomes a production dataset with a weekly schedule: each model's schema, measured cost, and
recovery after a lost run. It describes the pilot as it stood on 2026-11-23 and is a record of that
date, not a contract; the production design, once approved, belongs in
[`../architecture/data-architecture.md`](../architecture/data-architecture.md).

The pilot lives in the scratch dataset `currentai.automation_probe`, which has no schedule and
nothing reading it. It holds eight history models and three probes. This review covers the eight
history models. The probes (`append_probe`, `new_model_triage`, `source_fetch_probe`) tested the
platform and are not candidates for production as they stand.

## What a history model is here

Each upstream feed is a full-refresh model that keeps only its latest sweep. A history model is an
`INCREMENTAL_BY_UNIQUE_KEY` SQL model that selects that sweep and adds an observation date taken
from the upstream's own sweep time. The unique key is the upstream's natural key plus the
observation date, so:

- a run after a new sweep adds one row per key for the new date;
- a second run over the same sweep merges onto the same keys and adds nothing;
- earlier dates are never touched.

No history model calls an LLM or an external host, and none has partitions, clustering, audits or
data tests.

## The models

| Model | Upstream (weekly, Sunday UTC) | Unique key | Observation date from | Released |
|---|---|---|---|---|
| `github_state_history` | `signal_github.artifact_state` (03:00) | product_slug, repo, observed_date | `fetched_at` | yes |
| `package_state_history` | `signal_packages.package_metadata` (01:00) | product_slug, artifact_kind, package, observed_date | `fetched_at` | yes |
| `hf_state_history` | `signal_huggingface.artifact_state` (02:00) | product_slug, artifact_kind, artifact_id, observed_date | `fetched_at` | yes |
| `goodailist_history` | `signal_goodailist.repo_catalog` (01:00) | repo, observed_date | `source_updated_at` (the catalog's own update time) | yes |
| `openrouter_models_history` | `signal_openrouter.models` (01:00) | model_id, observed_date | `fetched_at` | yes |
| `hf_universe_history` | `signal_hfhub.model_universe` (01:30) | hf_id, observed_date | `fetched_at` | yes |
| `product_adoption_history` | `observations.product_adoption_current` (03:30) | observation_id | none: the key is the observation itself | **no** |
| `identity_candidates_history` | `identity.candidates` (05:30) | candidate_key, observed_date | `first_seen` (the sweep date) | **no** |

The two unreleased models have no table and have never run, so their output columns are not yet
resolved and their cost is unmeasured. They need a release in scratch and two runs before they can
be reviewed like the other six.

### Schemas

Every history model passes its upstream's columns through unchanged and adds `observed_date DATE`
(except `product_adoption_history`, which keys on `observation_id`). Resolved columns of the six
released models:

- **github_state_history:** product_slug, repo, observed_date, fetched_at, http_status,
  stargazers_count, forks_count, is_archived, license_spdx_id, license_key, latest_release_tag,
  latest_release_published_at, release_count, release_asset_downloads, eligible_asset_downloads,
  eligible_asset_count.
- **package_state_history:** product_slug, artifact_kind, package, observed_date, fetched_at,
  http_status, latest_version, latest_upload_at, installs_30d, installs_90d, installs_365d,
  pull_count_lifetime.
- **hf_state_history:** product_slug, artifact_kind, artifact_id, observed_date, fetched_at,
  http_status, downloads_30d, likes, license, is_gated, is_private, is_disabled, last_modified.
- **goodailist_history:** repo, observed_date, source_updated_at, category, subcat, language,
  stars, forks, contributors, star_7d, created_at, first_seen, archived.
- **openrouter_models_history:** model_id, observed_date, fetched_at, name, provider, created,
  context_length, pricing_prompt, pricing_completion, architecture_modality.
- **hf_universe_history:** hf_id, observed_date, fetched_at, downloads_30d, likes, license,
  pipeline_tag, gated, created_at.

Declared for the two unreleased models (not yet resolved by a run):

- **product_adoption_history:** observation_id, product_slug, product_type, artifact_kind,
  artifact_id, channel, metric_type, raw_value, unit, measurement_window_days, observed_at,
  ingested_at, source_dataset, source_table, is_valid, supersedes_observation_id.
- **identity_candidates_history:** candidate_key, observed_date, artifact_kind, artifact_key,
  artifact_id, source, last_evidence_change, evidence_kinds, downloads_30d, stars.

## Measured cost

Two observation dates are held, 2026-11-15 and 2026-11-22. The second was added on 2026-11-23 by a
run of the six released models alone.

| Model | Rows for 2026-11-15 | Rows for 2026-11-22 | Run time |
|---|---:|---:|---:|
| `github_state_history` | 938 | 986 | 4–6 s |
| `package_state_history` | 367 | 393 | 4–6 s |
| `hf_state_history` | 1,211 | 1,226 | 4–6 s |
| `goodailist_history` | 22,599 | 22,770 | 4–6 s |
| `openrouter_models_history` | 471 | 476 | 4–6 s |
| `hf_universe_history` | 36,286 | 35,838 | 4–6 s |
| **All six** | **61,872** | **61,689** | |

- **Storage grows by about 62,000 rows a week**, about 3.2 million a year, nearly all of it in
  `hf_universe_history` and `goodailist_history`. Each row is narrow (9 to 16 columns, no text
  bodies).
- **Compute is a full scan of the upstream once a week**, a few seconds per model on the run
  record. Every run on 2026-11-21 and 2026-11-23 finished in 4 to 6 seconds.
- **The platform reports no credits, compute or rows written per run.** The run record carries
  times and status only, and the run log records steps but no counts. Cost has to be watched from
  the platform's admin side, and row growth from the tables themselves.
- **No LLM spend.** None of these models makes an LLM call.

## Recovery

The upstreams keep one sweep each and replace it every Sunday. That sets the whole recovery story:
a history model must run after its upstream's Sunday sweep and before the next one.

| What goes wrong | What is lost | Recovery |
|---|---|---|
| A scheduled run fails or does not fire | Nothing yet | Re-run the model any time before the upstream's next Sunday sweep. The run adds that week's date. |
| No run happens before the next sweep | That week's observation, permanently | None from the warehouse: the upstream no longer holds it. Record the gap as a missing date; never back-fill it from a later sweep. |
| A run is repeated on the same sweep | Nothing | The merge lands on the same keys. Safe to re-run at will. |
| The upstream sweep is partial (some rows missing or failed) | Nothing is removed, but the date records a partial sweep | The merge keeps what it saw. Readers must use the upstream's own `http_status` and coverage columns, not row counts alone. |
| A sweep straddles midnight UTC | One sweep can land on two observation dates | Not seen so far (every upstream held a single date). Taking the date from the dataset run's start, not each row's fetch time, would remove the risk. |
| A revision changes the schema | Possibly the history itself | Unproven. Releases are forwards-only, but OSO-8315 shows a release that drops a column from an incremental model is accepted. Until that is fixed, treat any column removal or rename as a rebuild that loses history, and stage additive changes only. |
| The model is rebuilt from scratch (a fresh build) | All history | None. Before any fresh build, export the table as a frozen snapshot, as was done for `observations.product_adoption_baseline`. |

Two facts specific to one model each:

- `goodailist_history` dates rows by the catalog's own update time. If goodailist.com does not
  update between two sweeps, the second run adds no new date. That is correct behavior, not a lost
  run.
- `product_adoption_history` keys on `observation_id` with no date. It keeps every observation id
  ever emitted, and a value change under the same id overwrites the earlier value. It stores one row
  per observation id, not a time series per artifact.

## What needs a decision before production

1. **Schedule:** weekly, after the last upstream sweep (Sunday 05:30 UTC) and with a day's margin,
   for example Sunday 08:00 UTC. A missed run then has six days to be re-run before data is lost.
2. **Alerting on a missed week:** with no recovery after the next sweep, a failed run needs to reach
   a person within the week. A failed scheduled workflow in this repository opens an issue through
   `report-failure`; a failed platform schedule has no equivalent today.
3. **The two unreleased models:** release them in scratch, run twice, and review them here before
   they are scheduled.
4. **Where the models live:** one production dataset for all history, kept apart from the feeds it
   reads, so a feed's release cannot touch history.
5. **Schema changes:** whether to forbid non-additive changes to history models until OSO-8315 is
   fixed, and to require a frozen export before any fresh build.
