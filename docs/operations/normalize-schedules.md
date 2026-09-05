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

## Verified 2026-08-23 — every dataset fired SCHEDULED on its UTC cron

The first weekly fire under UTC was **Sunday 2026-08-23**. Run history — not configuration — is
the proof §13 demands, and it is now in hand. Each dataset's newest run at or after its UTC fire
time carries `triggerType: SCHEDULED` (verified by the runs API, not `datasets.lastRunAt`, which
lags), and `cronTimezone == "UTC"` still holds on all ten. The schedule normalization is proven.

| Dataset | UTC fire | Trigger | Model status | Run started |
|---|---|---|---|---|
| `signal_pypi` | 01:00 | SCHEDULED | SUCCESS | 2026-08-23T01:00:15Z |
| `signal_lmarena` | 01:00 | SCHEDULED | SUCCESS | 2026-08-23T01:00:17Z |
| `signal_goodailist` | 01:00 | SCHEDULED | SUCCESS | 2026-08-23T01:00:16Z |
| `signal_semanticscholar` | 01:00 | SCHEDULED | **FAILED** (upstream 429) | 2026-08-23T01:00:14Z |
| `signal_artificialanalysis` | 01:00 | SCHEDULED | SUCCESS | 2026-08-23T01:00:15Z |
| `signal_huggingface` | 02:00 | SCHEDULED | SUCCESS | 2026-08-23T02:01:42Z |
| `signal_github` | 03:00 | SCHEDULED | SUCCESS | 2026-08-23T03:01:43Z |
| `entities` | 04:00 | SCHEDULED | SUCCESS | 2026-08-23T04:00:29Z |
| `events` | 05:00 | SCHEDULED | SUCCESS | 2026-08-23T05:00:16Z |
| `metrics` | 06:00 | SCHEDULED | **FAILED** (transient ConnectTimeout) | 2026-08-23T06:00:16Z |

**The two failures are model-body failures, not schedule defects — both fired exactly on their UTC
cron.** They are recorded here; neither gates Phase 1.

- `metrics.daily` timed out (`ConnectTimeout`) during materialization at 06:00Z. A manual re-run
  the same morning (08:54→09:02Z) succeeded, so this was transient infrastructure, not a defect.
- `signal_semanticscholar.paper_citations` hit an upstream Semantic Scholar HTTP `429`
  (`semantic scholar batch returned 429 for 24 ids`); a manual re-run failed identically, so it is
  reproducible. The deployed UDM has no 429 backoff (the repo's `warehouse/models/catalog/model_repos.py`
  does). The fix is a platform-owned model change under §17; the asset has no reviewed consumer, so
  nothing downstream is affected. Recorded for a maintainer, not acted on here.

## Recorded in the repository (this PR)

The inventory now reflects the proven platform state — never ahead of it:

1. `timezone: UTC` was already set on the fifteen affected assets at apply time (unchanged here).
2. `last_observed_trigger: SCHEDULED` and `last_run_at: '2026-08-23'` set on all fifteen — every
   one of the ten datasets fired SCHEDULED, so every asset they hold records the observation
   (including `signal_semanticscholar`, whose schedule fired even though its model failed).
3. `unobserved_crons` recomputed 18 → 10 (the remaining ten are all out of Phase 1's scope); the
   `uv run pytest -q` passes.

## Rollback

Reversible: re-run the apply mutation for the affected `dataset_id`(s) with
`cronTimezone: "America/New_York"` and the same `cron`. No data is rewritten — only schedule
metadata — so a rollback restores the prior state exactly.
