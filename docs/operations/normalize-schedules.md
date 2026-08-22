# Runbook: Normalize pipeline schedules to UTC (Phase 1, maintainer)

`data-architecture.md` §13 requires pinning actual schedules to UTC and verifying a
`SCHEDULED` run from run history afterward. The Phase 0b audit confirmed 13 datasets carry a
daylight-saving `cronTimezone: America/New_York`. Phase 1 normalizes the **10 in-scope
pipeline datasets** to `UTC`.

**Warehouse writes are a maintainer step** (see `AGENTS.md`, and §17). This runbook was
prepared read-only, then **applied on 2026-08-22 with maintainer authorization**. All ten
mutations succeeded and were verified independently of the mutation responses: a fresh
`ListDatasets` filtered on `cron_timezone` returns 3 datasets on `America/New_York`, down from
13, and those 3 are the out-of-scope analytical datasets this runbook deliberately excludes.

The rollback below remains valid and is kept for that reason, not because the change is
pending.

## Decision on record

- **The cron digits are a dependency staircase, and that is why relabelling is safe.** The
  ten jobs are staged one hour apart, and the offsets encode the actual dependency order:
  signals at 01:00–03:00, then `entities` at 04:00 (which reads `signal_goodailist`), `events`
  at 05:00 (which reads `entities`), `metrics` at 06:00 (which reads `events`). Relabelling
  moves all ten by the same four hours, so the ordering is preserved exactly. Recomputing the
  digits per dataset to hold the wall-clock instant — the rejected alternative — would have
  had to reproduce that staircase by hand, and a single wrong digit would run a model before
  its input.
- **Relabel only.** Set `cronTimezone: UTC` and keep the cron digits unchanged. Each job's
  fire time therefore moves from `HH:00` America/New_York to `HH:00` UTC (4–5 hours earlier
  in wall-clock terms), and stops drifting with daylight saving. This was chosen deliberately
  over recomputing the digits to preserve the current wall-clock instant.
- **In-scope pipeline only.** The out-of-scope analytical datasets `ai_demand_curve`,
  `state_of_os_ai` and `aiid` are on `America/New_York` too but are **not** touched here —
  they are outside the inventory this migration governs.

## Baseline and target (captured 2026-08-22, read-only)

`cron` is unchanged; only `cronTimezone` moves. The `America/New_York` value in each row is
the rollback value.

| Dataset | dataset_id | cron (unchanged) | cronTimezone | last observed run |
|---|---|---|---|---|
| `entities` | `663132ed-ea4a-4fce-97a8-742e4479269c` | `0 4 * * 0` | `America/New_York` → `UTC` | — |
| `events` | `b2109421-64a8-4681-9d28-65a37a286f97` | `0 5 * * 0` | `America/New_York` → `UTC` | — |
| `metrics` | `5a73a919-79da-4029-ae5c-f5653bcc1e62` | `0 6 * * 0` | `America/New_York` → `UTC` | — |
| `signal_github` | `cc74e8db-7718-4615-a004-7f27cabaf967` | `0 3 * * 0` | `America/New_York` → `UTC` | 2026-08-15T07:00:13Z |
| `signal_huggingface` | `6108e4d6-868f-4cba-8df5-ee64f8fb301e` | `0 2 * * 0` | `America/New_York` → `UTC` | 2026-08-15T07:00:13Z |
| `signal_pypi` | `c7c3a04c-7e2d-4cea-a7e6-5861c725ea65` | `0 1 * * 0` | `America/New_York` → `UTC` | — |
| `signal_lmarena` | `f248f653-2ea6-4fdf-badb-c99adf9bcbe4` | `0 1 * * 0` | `America/New_York` → `UTC` | 2026-08-15T07:00:13Z |
| `signal_goodailist` | `f7f36dd4-ba41-4ee6-9547-65e409046893` | `0 1 * * 0` | `America/New_York` → `UTC` | 2026-08-16T07:00:14Z |
| `signal_semanticscholar` | `a48ec2ff-1e15-4b22-a38e-8ae03e0096f7` | `0 1 * * 0` | `America/New_York` → `UTC` | — |
| `signal_artificialanalysis` | `7ce58fca-9dda-4a95-8a17-9cef500c0656` | `0 1 * * 0` | `America/New_York` → `UTC` | 2026-08-15T07:00:13Z |

## Apply (maintainer, with OSO write credentials)

Each dataset is one `updateDataset` mutation against `https://api.oso.xyz/v1/graphql`, cron
unchanged, `cronTimezone: "UTC"`:

```graphql
mutation($input: UpdateDatasetInput!){
  updateDataset(input: $input){ success message dataset{ id name cron cronTimezone } }
}
```

Run it for each `dataset_id` above, e.g. with the repo's existing client:

```python
import os
from build.publish_registry import graphql
M = ("mutation($input: UpdateDatasetInput!){ updateDataset(input:$input){ "
     "success message dataset{ id name cron cronTimezone } } }")
tok = os.environ["OSO_API_KEY"]           # a key with write scope
TARGETS = {
    "663132ed-ea4a-4fce-97a8-742e4479269c": "0 4 * * 0",   # entities
    "b2109421-64a8-4681-9d28-65a37a286f97": "0 5 * * 0",   # events
    "5a73a919-79da-4029-ae5c-f5653bcc1e62": "0 6 * * 0",   # metrics
    "cc74e8db-7718-4615-a004-7f27cabaf967": "0 3 * * 0",   # signal_github
    "6108e4d6-868f-4cba-8df5-ee64f8fb301e": "0 2 * * 0",   # signal_huggingface
    "c7c3a04c-7e2d-4cea-a7e6-5861c725ea65": "0 1 * * 0",   # signal_pypi
    "f248f653-2ea6-4fdf-badb-c99adf9bcbe4": "0 1 * * 0",   # signal_lmarena
    "f7f36dd4-ba41-4ee6-9547-65e409046893": "0 1 * * 0",   # signal_goodailist
    "a48ec2ff-1e15-4b22-a38e-8ae03e0096f7": "0 1 * * 0",   # signal_semanticscholar
    "7ce58fca-9dda-4a95-8a17-9cef500c0656": "0 1 * * 0",   # signal_artificialanalysis
}
for dataset_id, cron in TARGETS.items():
    r = graphql(M, {"input": {"id": dataset_id, "cron": cron, "cronTimezone": "UTC"}}, tok)
    print(dataset_id, r["updateDataset"]["success"])
```

## Applied 2026-08-22

All ten returned `success: true`. Verified by re-query, not by the mutation responses:

| Dataset | cron | cronTimezone | nextRunAt |
|---|---|---|---|
| `signal_pypi` | `0 1 * * 0` | UTC | 2026-08-23T01:00:00Z |
| `signal_lmarena` | `0 1 * * 0` | UTC | 2026-08-23T01:00:00Z |
| `signal_goodailist` | `0 1 * * 0` | UTC | 2026-08-23T01:00:00Z |
| `signal_semanticscholar` | `0 1 * * 0` | UTC | 2026-08-23T01:00:00Z |
| `signal_artificialanalysis` | `0 1 * * 0` | UTC | 2026-08-23T01:00:00Z |
| `signal_huggingface` | `0 2 * * 0` | UTC | 2026-08-23T02:00:00Z |
| `signal_github` | `0 3 * * 0` | UTC | 2026-08-23T03:00:00Z |
| `entities` | `0 4 * * 0` | UTC | 2026-08-23T04:00:00Z |
| `events` | `0 5 * * 0` | UTC | 2026-08-23T05:00:00Z |
| `metrics` | `0 6 * * 0` | UTC | 2026-08-23T06:00:00Z |

The staircase is intact, and the Monday openness chain (`evidence` 03:00, `scores` 04:00 UTC)
still runs a day after `metrics` finishes. The three excluded datasets remain on
`America/New_York` at 12:00 UTC Sunday, still downstream of `metrics`.

`warehouse/assets.yaml` declares `timezone: UTC` for the 15 assets those ten datasets hold —
now a statement of platform truth rather than a claim ahead of it.

## Still pending: an observed SCHEDULED run

`last_observed_trigger` remains `null` on all 18 assets that have never been seen to fire, and
`unobserved_crons` still reads 18. §13 requires run history, not configuration, as proof — so
this phase is not complete until a `SCHEDULED` run is observed.

The first fire under UTC is **2026-08-23 01:00Z**. Until then the change is applied but
unproven, and that distinction is the whole point of the gate.

## Verify (after the next weekly fire)

The crons fire weekly on **Sunday**; the first fire under UTC is **2026-08-23**. `SCHEDULED`
verification cannot be done at apply time — wait for that fire, then confirm each dataset's
run history shows a `SCHEDULED` (not `MANUAL`) trigger:

```python
q = "query($w: JSON){ datasets(where:$w){ edges{ node{ name cron cronTimezone lastRunAt } } } }"
# and GetRunsForDataset / the runs API for the trigger type on the newest run
```

Confirm `cronTimezone == "UTC"` on all ten, and a `SCHEDULED` run dated on/after 2026-08-23.

## Then, in the repository (a follow-up PR)

Only once the platform reflects UTC — never before, or the inventory would declare a state
that is not true:

1. Set `timezone: UTC` on the ten datasets' assets in `warehouse/assets.yaml` (cron digits in
   `refresh:` are unchanged).
2. Set `last_observed_trigger: SCHEDULED` and `last_run_at` for each verified dataset.
3. Regenerate any affected count markers (`unobserved_crons`) and run `uv run pytest -q`.

## Rollback

Reversible: re-run the apply mutation for the affected `dataset_id`(s) with
`cronTimezone: "America/New_York"` and the same `cron`. No data is rewritten — only schedule
metadata — so a rollback restores the prior state exactly.
