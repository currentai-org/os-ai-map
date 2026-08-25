# Deploy the axis-assessments table

Maintainer runbook (OSO write access). Publishes `currentai.registry.axis_assessments` — the
long-form companion to `registry.product_scores`, one row per recorded axis
(`build/axis_assessments.py`). An editor session does not run this: it builds and tests the
candidate in-repo; only a maintainer materializes it.

The table keys on `declaration_version_id` and carries **no** `release_id` (§4.4): it is a pure
function of the declarations (`sources/scores/` and the published roster), cut by the builder at a
commit. That is why it is not part of the CI registry push (`build/publish_registry.py`, which
refreshes the identity tables on every merge): those tables carry no commit-scoped identity, this
one does, so it is published deliberately by a maintainer from a known-clean commit.

## 1. Preconditions

- The commit you are publishing from is on `main` and the worktree is clean. The builder derives
  `declaration_version_id` from `HEAD` + the working tree and refuses a dirty tree (a dirty tree
  yields an id no commit reproduces); pass `--allow-dirty` only for a throwaway diagnostic.
- `OSO_API_KEY` and `OSO_ORG_ID` are set. `OSO_DATASET` defaults to `registry` — this table lives
  in the same dataset as the other `registry.*` static models.

## 2. Build the candidate CSV

Validate first (builds in memory, writes nothing, fails on a dirty tree):

```bash
uv run python -m build.axis_assessments --check
```

Then write the upload artifact:

```bash
uv run python -m build.axis_assessments --out build/registry
```

This reads the recorded `sources/scores/` and the published roster, stamps every row with the
run-time `declaration_version_id` + `source_git_sha`, and writes
`build/registry/axis_assessments.csv`. That directory is git-ignored — the CSV is an upload
artifact, not repository state. Sanity-check the reported row count (one row per published
`(product, category)` per recorded axis; `3 × 522 = 1566` over the current corpus, all `confirmed`
because the verification queue is empty).

## 3. Publish

The table is a static model in the `registry` dataset. It uses the same publish mechanics as
`build/publish_registry.py` (`resolve_dataset` → `resolve_static_models` → upload URL → `PUT` the
CSV → `createStaticModelRunRequest`, then wait for the run to reach terminal `SUCCESS` and read the
deployed row count/schema back via `pyoso` before trusting it). It is **not** yet wired into
`publish_registry`'s automatic table set, precisely because it is cut at a commit rather than on
every merge; a maintainer publishes it explicitly. Wiring a dedicated publisher (mirroring
`build/publish_evaluation.py`, with the same validate-before-mutation and SUCCESS-gated archive) is
the natural follow-up once this deploy becomes routine.

Record the `dataset_id`, the static-model id, and the `declaration_version_id` you published from in
the deploy note.

## 4. Reconcile the inventory with reality

Once the table exists on the platform:

- In `warehouse/assets.yaml`, move `registry.axis_assessments` from `status: staged` /
  `materialized: false` to `active` / `materialized: true`, record the `dataset_id`, and update
  `verified_at`.
- Regenerate the derived DAG and counts with `build/assets.py` (the `assets` and `staged_assets`
  count markers move), and update `docs/architecture/current-state-dag.md` and the counts in
  `docs/architecture/data-architecture.md`.

## Note on the current state

Nothing consumes this table yet — it is the long-form companion that downstream models will read
instead of unpivoting `registry.product_scores`. Publishing it wires the shape into the platform
ahead of those readers; it changes no existing consumer, so there is no gate to enable and no
rollback consumer to break. `not_applicable` is intentionally not emitted (a dated null is
`confirmed`), pending the §4.4 ruling on how capability `basis: n/a` records should compile.
