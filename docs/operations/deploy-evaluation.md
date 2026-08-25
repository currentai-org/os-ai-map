# Deploy the adoption evaluation tables

Maintainer runbook (OSO MCP write access). Publishes the two Phase-3 evaluation tables from the
repo-side release builders to the platform. An editor session does not run this — it builds and
tests the candidates in-repo; only a maintainer materializes them.

The tables:

- `currentai.evaluation.product_adoption_measurements` — the product-level adoption rollup
  (`build/adoption_measurements.py`).
- `currentai.evaluation.adoption_reconciliation` — the report-first reconciliation of measured
  against recorded adoption (`build/adoption_reconciliation.py`).

Both are keyed on `declaration_version_id` + `observation_snapshot_id`, and neither is a UDM: a
platform model cannot compute `declaration_version_id`, which encodes the repository git SHA and
the `sources/` content digest the warehouse has no access to. They are cut by the builder, at a
commit, over one atomic read of `observations.product_adoption_current`.

## 1. Preconditions

- The commit you are publishing from is on `main` and the worktree is clean (the builder refuses a
  dirty tree without `--allow-dirty`, because a dirty tree yields an id no commit reproduces).
- `OSO_API_KEY` is set (the builder reads the deployed current table via `pyoso`).
- The `evaluation` dataset exists on the platform. If it does not, create it first — this is the
  same one-time namespace creation `observations` needed in Phase 2. Until it exists, both assets
  stay `staged` / `materialized: false` in `warehouse/assets.yaml`.

## 2. Dry run, then build the candidates from one live read

Validate first — this writes nothing and fails on a dirty tree or a routing/compiler error:

```bash
uv run python -m build.serialize_evaluation --check          # in-memory build, no files, no upload
```

Then build the upload artifacts:

```bash
uv run python -m build.serialize_evaluation --live
```

This reads `observations.product_adoption_current` once, derives `observation_snapshot_id` and
`declaration_version_id` from that read and the working tree, and writes
`build/evaluation/product_adoption_measurements.csv` and `adoption_reconciliation.csv`. The single
read is the point: the snapshot id and both tables describe the same rows, never two reads that
straddle a refresh. The CSVs are git-ignored — they are an upload artifact, not repository state.

Sanity-check the row counts against what the builder reports over the baseline
(`uv run python -m build.adoption_measurements` and `... adoption_reconciliation`), remembering the
live counts move with the live observations.

## 3. Upload as static models

Same GraphQL mechanism `build/publish_registry.py` uses (`graphql()` helper, `OSO_API_KEY` bearer
token, `ORG_ID`). For each of the two tables, in order — `product_adoption_measurements` then
`adoption_reconciliation`:

1. **Resolve or create the dataset.** The `evaluation` dataset must exist; create it once if not
   (mirror `publish_registry.resolve_dataset`). Record its `dataset_id`.
2. **Resolve or create the static model** for the table name:

   ```graphql
   mutation($input: CreateStaticModelInput!) {
     createStaticModel(input:$input){ success staticModel{ id name } } }
   ```

   Capture the returned `staticModel.id` (this is `model_id`). If it already exists, reuse its id.
3. **Get an upload URL and PUT the CSV** (mirror `publish_registry.upload`):

   ```graphql
   mutation($staticModelId: ID!){ createStaticModelUploadUrl(staticModelId:$staticModelId) }
   ```

   then HTTP `PUT` the CSV bytes to that URL.
4. **Trigger the load and capture the revision:**

   ```graphql
   mutation($input: CreateStaticModelRunRequestInput!){
     createStaticModelRunRequest(input:$input){ success run{ id status } } }
   ```

   Record `run.id`, the resulting `revision`, the schema the platform inferred, and the CSV's
   `sha256`. These are the provenance the inventory's `mirror` block (or the evaluation asset's
   deploy note) must carry, exactly as the registry and observation deploys record theirs.

Verify the deployed row counts equal the CSV row counts (`data_rows`), and that
`routing_policy_version` is present and equals the value in `signal_routing.yaml`.

## Rollback

A static-model load is a new revision over the same `model_id`; the previous revision is retained.
To roll back, re-point the model to the prior revision (or re-run step 3 with the last-known-good
CSV, which you can regenerate from the commit whose `declaration_version_id` you recorded). Because
nothing downstream consumes these tables yet (Phase 4's gate is not enabled), a rollback has no
consumer to break — but record the revision you rolled back from and to, so the provenance stays
truthful. If a load fails midway, the model keeps its prior revision; do not leave a half-loaded
table marked `active` in the inventory.

## 4. Reconcile the inventory with reality

Once the tables exist on the platform:

- In `warehouse/assets.yaml`, move each entry from `status: staged` / `materialized: false` to
  `active` / `materialized: true`, and record the `dataset_id`. Update `verified_at`.
- Regenerate the derived counts and DAG with `build/assets.py`, and update the staged/deployed
  counts in `docs/architecture/data-architecture.md`.
- Update the Phase-3 row in `docs/architecture/migration-status.md`.

## Note on the current state

Every measured reconciliation row is `source_unavailable` until row-to-run binding lands (#355):
`product_adoption_current` carries no `source_run_id`, so §4.3 forbids reading a current
measurement as agreement. Publishing the report is still useful — it wires the pipeline end to end
and exposes the measured-vs-recorded deltas — but the blocking gate (Phase 4) must not be enabled
until #355 makes the fuller status set assignable.
