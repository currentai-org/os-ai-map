# Deploy and refresh the warehouse models (maintainer, MCP write)

Requires an OSO MCP session with write access to the `currentai` org. Editors do not run
this; see `AGENTS.md` on the read-only boundary.

There are **two families of model** in this org, and they deploy the same way but live in
different places.

| Family | Models | Where the SQL lives |
|---|---|---|
| Legacy warehouse | `entities`, `events`, `metrics`, and the legacy `scores` stack-map models | `warehouse/models/` — **in this repo** |
| Scoring chain | `evidence.product_evidence` → `scores.openness_facts` → `scores.openness_computed`, plus the `signal_*` fetchers | On the OSO platform only. The deploy script and `.sql` sit one level up in `currentai-org/{tools,udms}/`, **which is not under version control at all.** |

Mirroring the scoring-chain SQL into `warehouse/udms/` is tracked as T1 of the 2026-08-14
audit. Until it lands, treat the copy in `../udms/` as the only copy that exists, and run the
deploy from that directory.

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

## The schedule: declared, but not firing

This is the part the docs got wrong before the 2026-08-14 audit, so read it carefully.

The scoring chain was **intended** to run weekly — `evidence.product_evidence` Monday 03:00
UTC, `scores.openness_facts` 04:00, `scores.openness_computed` 05:00, with the parity gate
grading at 06:00. Those crons were written onto the model **revisions** via
`deploy_udm.py --cron`.

**The platform schedules from the *dataset*, not the model revision.** The observed fact,
which does not age: **of the 72 `evidence` and `scores` runs inspected on 2026-08-14, none had
a `SCHEDULED` trigger** — every one was requested by hand. Those crons were written onto the
model revisions, which the scheduler does not read.

**A set cron is not a firing cron — check the run history, not the `cron` field.** This is the
part that surprises people, verified against the platform on 2026-08-14:

| dataset | `cron` field | actually fired `SCHEDULED`? |
|---|---|---|
| `signal_goodailist` | `0 3 * * 0` (Sun) | **Yes** — 2026-08-09, `requestedBy: null` |
| `signal_github` | `0 3 * * 6` (Sat) | **No** — 7/7 runs MANUAL, though `lastRunAt` shows a 07:00 slot with no matching run row |
| `signal_huggingface` | `0 3 * * 6` (Sat) | cron set; no confirmed scheduled run |
| `signal_pypi` | **null** | no cron to fire |
| `evidence`, `scores` | none | No — 72/72 MANUAL |

So the mechanism demonstrably works (goodailist), but a populated `cron`/`lastRunAt`/`nextRunAt`
tells you nothing on its own — only a run whose `triggerType` is `SCHEDULED` proves the schedule
fires. Read the dataset's run history, the same way `GetRun` status can read stale.

Until T4 of the audit lands (`updateDataModelSchedule` on the `evidence` and `scores` datasets,
keeping the 03/04/05 spacing so parity stays downstream):

- **Treat every scoring-chain recompute as manual.** A merge that changes a score does not
  reach the warehouse until someone walks the chain above.
- **Do not trust a "the warehouse recomputes weekly" statement** anywhere it survives — check
  the dataset's run history for a `SCHEDULED` trigger before believing it.

**The signal fetchers are the same story.** `signal_github` and `signal_huggingface` carry a
weekly cron but have not been observed firing it (their tables refresh when someone runs them by
hand); `signal_pypi` carries no cron at all; only `signal_goodailist` genuinely refreshes on its
own. So the fetched facts under the scoring chain are, in practice, hand-refreshed too — which is
why scheduling them is a larger decision than a cron expression: it is the point at which scores
start moving on their own, which is what `apply_scores --check` exits non-zero for.

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
has not recomputed and fail for a reason that is not a drift. Note the standing hazard: with the
chain not firing on schedule, parity can be red for staleness rather than drift until T4 and T6
land.

## Related

- `docs/reference/evidence-and-freshness.md` — what the chain computes and the gates over it
- `docs/operations/publish-map.md` — serializing and publishing the notebook
- `docs/operations/refresh-data.md` — running the signal fetchers
- `warehouse/models/README.md` — the legacy in-repo model family
