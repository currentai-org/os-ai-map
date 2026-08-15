# Deploy and refresh the warehouse models (maintainer, MCP write)

Requires an OSO MCP session with write access to the `currentai` org. Editors do not run
this; see `AGENTS.md` on the read-only boundary.

There are **two families of model** in this org, and they deploy the same way but live in
different places.

| Family | Models | Where the SQL lives |
|---|---|---|
| Legacy warehouse | `entities`, `events`, `metrics`, and the legacy `scores` stack-map models | `warehouse/models/` — **in this repo** |
| Scoring chain | `evidence.product_evidence` → `scores.openness_facts` → `scores.openness_computed`, plus the `signal_*` fetchers | On the OSO platform. The models are copied **read-only** into `warehouse/platform-mirror/` (with a provenance manifest) so they are legible from the repo; the deploy script and the working copies you push from sit one level up in `currentai-org/{tools,udms}/`, outside version control. **Nothing deploys from `warehouse/platform-mirror/`.** |

The `warehouse/platform-mirror/` copy (T1 of the 2026-08-14 audit) makes the scoring models
readable without platform access. It is a snapshot, not the source of truth — see
`warehouse/platform-mirror/README.md` and its `manifest.yaml` for the deployed revision each file reflects.

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

The **intended** operating schedule is weekly, upstream first: `evidence.product_evidence` Monday
03:00 UTC, `scores.openness_facts` 04:00, `scores.openness_computed` 05:00, with the parity gate
grading at 06:00, and the signal fetchers refreshing ahead of it. On that schedule the warehouse
is at most a week behind the repo.

**This repository does not verify whether those scheduled runs actually fired** — that is a
platform concern, not something the repo tracks. When you are diagnosing a freshness problem,
inspect the datasets' run history on the platform rather than assuming this schedule held.

**Schedule a model on its dataset, not its model revision** (`updateDataModelSchedule`) — the
platform's scheduler reads the dataset-level cron. Keep the 03/04/05 spacing so parity, at 06:00,
grades a warehouse that has just recomputed.

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
- `warehouse/models/README.md` — the legacy in-repo model family
