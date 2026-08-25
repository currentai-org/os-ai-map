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
- `OSO_API_KEY` and `OSO_ORG_ID` are both set (the builder reads the deployed current table via
  `pyoso`; the publisher uses the same GraphQL API as `build/publish_registry.py`). `OSO_DATASET`
  defaults to `evaluation`.
- The `evaluation` dataset may or may not exist; `build/publish_evaluation.py` creates it on the
  first real publish. Until the tables exist, both assets stay `staged` / `materialized: false` in
  `warehouse/assets.yaml`.

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

## 3. Publish

`build/publish_evaluation.py` does the upload — it reuses `publish_registry`'s `graphql`,
`resolve_static_models`, and `upload`, resolves (or creates) the `evaluation` dataset and each
static model, `PUT`s the CSV, and requests the load run.

```bash
# Archive the current known-good bytes first, so a rollback has something to re-upload (see below).
mkdir -p ~/eval-archive/$(date -u +%Y%m%dT%H%M%SZ) && cp build/evaluation/*.csv ~/eval-archive/…/

uv run python -m build.publish_evaluation --plan       # offline: tables, row counts, SHA-256; no network
uv run python -m build.publish_evaluation --dry-run    # read-only id resolution; NO mutation
uv run python -m build.publish_evaluation              # create/upload/run; writes a provenance receipt
```

The publish writes `build/evaluation/publish_receipt.json` (row count, column schema, SHA-256 per
table) **before** it uploads, and prints each `run.id` and status. Record the `dataset_id`,
`model_id`, and the receipt with the deploy note. Verify the deployed row counts equal the CSV row
counts and that `routing_policy_version` is present and equals the value in `signal_routing.yaml`.

## Rollback — by bytes, not by revision re-pointing

A static-model publication **replaces the table in place**; the platform exposes no prior-revision
list to re-point to, and `observations.product_adoption_current` may have changed since, so
regenerating from an old commit does **not** reproduce the previous table. Rollback therefore means
**re-uploading the exact bytes that were live before the replacement**:

1. Take the archived CSV whose SHA-256 the previous `publish_receipt.json` recorded (the copy you
   made in step 3, or the receipt from the prior deploy).
2. Re-run the publisher against those bytes:

   ```bash
   uv run python -m build.publish_evaluation --dir /path/to/archived-good/   # re-upload known-good bytes
   ```

3. Confirm the deployed SHA-256/row count matches the archived receipt.

Nothing downstream consumes these tables yet (Phase 4's gate is not enabled), so a rollback has no
consumer to break — but do not leave a half-loaded table marked `active` in the inventory: if a
load fails midway, re-upload the known-good bytes or revert the inventory entry to `staged`.

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
