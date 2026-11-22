# The proposals bridge

Maintainer runbook. Platform producers (models, rules and, later, agents) cannot write to this
repository. They write rows to a proposals table, and `.github/workflows/proposals.yml` applies
them daily with `build/proposals.py`, gates the result, and keeps one rolling pull request per
kind of proposal (ruling R-2026-11-21-f). The rules it serves are ADR-004 (machines propose, only
a person merges, one label per bot pull request) and R-2026-11-21-e (agents may open pull
requests, never merge or set methodology).

## What a proposal is

A proposal is a request, never the change. The applier for each kind re-derives what it writes
with the repository's own tooling, so nothing in a row is copied into `sources/`. A wrong or stale
proposal costs a fetch and nothing else, and a producer needs no write authority over the corpus.

| Kind | Handler | What it writes | Label |
|---|---|---|---|
| `redate` | `build.reverify.reverify_product` on the named product and axis | `last_verified`, and each confirmed source's `accessed`, `http_status` and `content_sha256` | `freshness` |

A `redate` proposal is limited to openness by the same refusal the weekly re-verification applies,
and an axis is stamped only where the applier's own fetch confirms every recorded dimension
(`docs/reference/evidence-and-freshness.md`, ruling R-2026-11-21-b). The producer's `evidence`
field is shown to the reviewer and decides nothing.

Each proposal ends in one of four outcomes, counted apart in the pull request: **applied**, **not
confirmed** (the applier read the sources and could not confirm the claim), **already current**
(the axis was verified on or after the proposal's `observed_at`), and **rejected** (the row fails
the schema, names no known product, or asks for an axis the kind may not touch).

State is derived, never stored. A proposal whose axis is already current applies nothing, so the
same row read on consecutive days, or after its pull request merged, is harmless.

## The table

One table holds every kind. The row shape is `docs/schemas/proposal.schema.json`; the table stores
two of its fields flat, because nested columns are awkward to write from a SQL model:

| Column | Type | Notes |
|---|---|---|
| `proposal_id` | varchar | Stable and unique. Derive it from what was observed, e.g. `redate:<slug>:<axis>:<observed_at>`, so a re-run of the producer adds nothing new |
| `kind` | varchar | A kind from the schema's enum |
| `product_slug` | varchar | |
| `axis` | varchar | |
| `observed_at` | date | The day the producer made the observation |
| `producer_model` | varchar | The model or rule that wrote the row |
| `producer_revision` | varchar, nullable | Its revision, so a reviewer can trace a bad row to the code that wrote it |
| `evidence` | varchar | JSON array of `{url, outcome, content_sha256?}`, `outcome` one of `unchanged`, `verified` |
| `created_at` | timestamp | The bridge reads rows created in the last seven days |

The table is a SQL model over its producers, one `UNION ALL` branch per producer, each emitting the
columns above. Producers are added as they are built; the first is the source-observation model of
build step 4. With none yet, the model is the empty select:

```sql
SELECT
  CAST(NULL AS varchar) AS proposal_id, CAST(NULL AS varchar) AS kind,
  CAST(NULL AS varchar) AS product_slug, CAST(NULL AS varchar) AS axis,
  CAST(NULL AS date) AS observed_at, CAST(NULL AS varchar) AS producer_model,
  CAST(NULL AS varchar) AS producer_revision, CAST(NULL AS varchar) AS evidence,
  CAST(NULL AS timestamp) AS created_at
WHERE false
```

Keep it in its own dataset, apart from the history models.

**Schedule it after its producers.** A FULL model is materialized when it runs and does not refresh
when its inputs change, so the table shows its producers only as of its own last run. While it has
no producers it needs no schedule. The pull request that adds the first producer also gives this
model a cron that fires after that producer's, and each later producer moves it after its own if
needed.

**Keep it FULL, never incremental.** History belongs in the producers, which keep their
observations; a proposal is a conclusion recomputed from them. Rebuilt in full, the table drops a
bad producer's rows on the next run after that producer is fixed or disabled, where an incremental
model would keep them until someone deleted them by hand. The bridge needs no memory here: it reads
a seven-day window and derives what was already applied from `sources/`.

## Switching it on

1. Create the dataset and the model above on the platform, and confirm it returns zero rows with
   the expected columns.
2. Record it in `warehouse/dependencies.yaml` as a dependency contract read by `build/proposals.py`
   (`skills/add-data-source/SKILL.md`). It is a platform output the repository reads, not a
   governed asset.
3. Set the repository variable `PROPOSALS_TABLE` to its three-part name. The workflow is skipped
   while the variable is unset, so the daily schedule costs nothing until then.
4. Dispatch the workflow once by hand and confirm it exits cleanly with nothing to apply.

The workflow needs no new credential. It reads the table with `OSO_API_KEY` and opens the pull
request with `GH_FETCH_TOKEN`, as `reverify` does, so CI runs on it.

## Running it by hand

```bash
uv run python -m build.proposals apply --kind redate --from-table "$PROPOSALS_TABLE" --report r.json --dry-run
uv run python -m build.proposals apply --kind redate --from-file proposals.jsonl --report r.json
uv run python -m build.proposals summarize r.json
```

`--from-file` reads JSON Lines in the schema's nested shape, which is how to test a producer's
output before it is wired into the table.

## The pull request

One branch per kind, `proposals/<kind>`, rebuilt from `main` on every run and force-pushed, so the
open pull request always holds that day's reading and an unmerged one is replaced rather than
stacked. A day with nothing to apply leaves an open pull request as it is. The run gates the result
with `build.preflight --skip-tests` and `build.check_redate` before it pushes, and opens nothing if
they fail; CI then runs in full on the pull request and writes the review sheet.

A failed scheduled run opens a sentinel issue through `report-failure.yml`. The bridge is not on its
retry list, because it pushes and opens pull requests.

## Adding a kind

A kind needs four things in one pull request: the value in the schema's `kind` enum, a handler in
`build.proposals.HANDLERS` that re-derives its change with existing repository tooling, an ADR-004
label in `KIND_LABELS`, and the kind in the workflow's matrix. `tests/test_proposals.py` fails when
the enum, the handlers and the labels disagree.
