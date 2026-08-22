# Runbook: Normalize pipeline schedules to UTC (Phase 1, maintainer)

`data-architecture.md` §13 requires pinning actual schedules to UTC and verifying a
`SCHEDULED` run from run history afterward. The Phase 0b audit confirmed 13 datasets carry a
daylight-saving `cronTimezone: America/New_York`. Phase 1 normalizes the **10 in-scope
pipeline datasets** to `UTC`.

**Warehouse writes are a maintainer step** (see `AGENTS.md`, and §17). The change was
scoped, its rollback captured, and the exact mutations prepared here, but the writes
themselves must be run by a maintainer with OSO write credentials — the implementation agent
cannot mutate the platform.

## Decision on record

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
