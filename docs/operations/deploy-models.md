# Deploy and refresh the warehouse models (maintainer, MCP write)

Requires an OSO MCP session with write access to the `currentai` org. Editors do not run
this; see `AGENTS.md` on the read-only boundary.

There are **two families of model** in this org, and they deploy the same way but live in
different places.

| Family | Models | Where the SQL lives |
|---|---|---|
| Legacy warehouse | `entities`, `events`, `metrics`, and the legacy `scores` stack-map models | `warehouse/models/` — **in this repo** |
| Scoring chain | `evidence.product_evidence` → `scores.openness_facts` → `scores.openness_computed`, plus the `signal_*` fetchers | On the OSO platform. The models are copied **read-only** into `warehouse/models/<dataset>/` (carrying a `mirror:` block in `warehouse/assets.yaml`) so they are legible from the repo; the deploy script and the working copies you push from sit one level up in `currentai-org/{tools,udms}/`, outside version control. **Nothing deploys from the mirror copies.** |

The read-only mirror copies under `warehouse/models/<dataset>/` (T1 of the 2026-08-14 audit)
make the scoring models readable without platform access. They are snapshots, not the source
of truth — see each asset's `mirror:` block in `warehouse/assets.yaml` for the deployed
revision, hash and sync date the file reflects.

## The deploy mechanic: revision → RELEASE → run

For any model whose SQL changed:

1. **Revision** — `createDataModelRevision` with the dataset and the new SQL.
2. **Release** — `createDataModelRelease` pointing at that revision. **This is the step that
   gets forgotten.** A run without it executes the *previous* release, and the symptom is "my
   change had no effect" rather than an error — three runs were once spent concluding a column
   drop had broken materialization when the new SQL had simply never been released. **No automated
   revision-versus-release assertion exists yet** (that latest-revision == latest-release check was
   scoped but never landed), so maintainers must verify by hand that the revision they just created
   is the one that got released before trusting a run.
3. **Run** — `createUserModelRunRequest` with the dataset ID.
4. **Prove it** — read the output table back and, for the scoring chain, run
   `build/check_parity.py`.

For the scoring chain the script wraps steps 1–3:

```bash
# from currentai-org/ (NOT this repo — see the table above)
uv run python tools/deploy_udm.py --dataset scores --model openness_facts \
    --sql udms/scores_openness_facts.sql
```

## The refresh order, which is not optional

The scoring chain does **not** cascade. Refresh the three user models in dependency order,
waiting for each:

```
evidence.product_evidence  ->  scores.openness_facts  ->  scores.openness_computed
```

Getting this wrong looks exactly like a code bug. The first run of the generalized SQL
reported three categories missing entirely; the cause was `product_evidence` sitting three
recipes stale, still holding 47 orchestration products against the repo's 36.

Two traps in the run step, both of which have cost hours:

- **Per-model refresh needs UUIDs, not names.** `createUserModelRunRequest.selectedModels`
  takes model UUIDs; passing `"openness_facts"` fails with `invalid input syntax for type
  uuid`. Without the IDs, the only path is a whole-dataset run — it works and preserves
  topological order, but pulls in unrelated `scores` models and takes minutes against seconds
  targeted.
- **Verify from the data, not the run status.** A `scores` run reports RUNNING for minutes
  after its early models have committed. Query `MAX(last_checked)` through `build/warehouse.py`,
  which forces a cache-busting nonce — without it you read the pre-materialization answer back
  out of the query-text cache.

## The schedule

This is what is **configured**, verified on the platform 2026-08-19. The workflow files are
authoritative for the gates; this table is a copy and a copy can drift, so `tests/test_schedule_doc.py`
holds it against the `cron:` lines it quotes.

| What | When (UTC) | Where the cron lives |
|---|---|---|
| `registry` static models | every push to `main` touching `sources/**` | `.github/workflows/registry.yml`, no cron |
| `evidence` dataset | Monday 03:00 | dataset cron, timezone UTC |
| `scores` dataset | Monday 04:00 | dataset cron, timezone UTC |
| `parity` gate | Monday 06:00 | `.github/workflows/parity.yml` |
| `artifacts` | Monday 07:00 | `.github/workflows/artifacts.yml` |
| `freshness` report | Monday 08:00 | `.github/workflows/freshness.yml` |

The chain lands two hours before parity grades it, and the warehouse is at most a week behind
the repo.

**The chain is two datasets, not three model times.** An earlier version of this section gave
`openness_facts` 04:00 and `openness_computed` 05:00, which cannot be configured: both models
live in the `scores` dataset and the platform sweeps per dataset. Within a sweep they run in
dependency order anyway, so one dataset time covers both. Splitting them would mean splitting
the dataset.

**Set the cron on the dataset, and keep the models' own cron empty.** The dataset cron is when
the sweep happens (`updateDataset`); a model's cron is a THROTTLE on top of it, where `""` means
eligible on every sweep and `@manual` means never scheduled. `updateDataModelSchedule` sets that
throttle, not the sweep — reaching for it to change *when* the chain runs mints a revision and
changes nothing about the timing.

**Pin the timezone to UTC.** These ran on `America/New_York` until 2026-08-19, which moves the
real hour by one across DST while every gate that grades them is UTC-pinned. The margin is
hours, so nothing inverted, but the two clocks had no reason to differ.

**A configured cron is not an observed run, and the repo cannot tell you which you have.** Check
`triggerType` in the dataset's run history: `MANUAL` everywhere means nothing has fired on its
own, however healthy the cron field looks. Two ways that reads as a bug when it is not — a cron
set after this week's slot has passed shows `lastRunAt: null` until the next one comes round, and
`nextRunAt` is computed from the cron whether or not the scheduler ever acts on it. To settle it
in minutes rather than waiting a week, point the cron a few minutes out, watch for a run whose
`triggerType` is `SCHEDULED`, then set the real one back. Confirmed working that way on
2026-08-19: `SCHEDULED/RUNNING started=2026-08-19T18:45:18Z` against a cron set for 18:45.

## A publish is only half a refresh

Pushing the declarations is step 1, not the whole job:

```bash
# push the repo's declarations and wait for the static models to materialize
uv run python -m build.serialize_rubric && uv run python -m build.publish_registry
# then walk the chain above, in order, and prove it with check_parity
```

## The parity gate

`build/check_parity.py` compares `check_rubric`'s local verdict against
`currentai.scores.openness_computed` per product and fails on any divergence. It runs weekly in
`.github/workflows/parity.yml`, Monday 06:00 UTC, behind the models it grades — deliberately
**not** chained onto a publish, because that would compare fresh rules against a warehouse that
has not recomputed and fail for a reason that is not a drift. Because the repo does not verify
that the weekly recompute fired (see "The schedule" above), read a red parity as "check the
datasets' run history first" — it can mean the warehouse is stale rather than that a rule drifted.

## Related

- `docs/reference/evidence-and-freshness.md` — what the chain computes and the gates over it
- `docs/operations/publish-map.md` — serializing and publishing the notebook
- `docs/operations/refresh-data.md` — running the signal fetchers
- `warehouse/assets.yaml` and `docs/architecture/data-architecture.md` — the asset inventory and the model families it covers
