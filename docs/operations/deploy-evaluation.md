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
uv run python -m build.serialize_evaluation --live      # the deployed current table
uv run python -m build.serialize_evaluation             # the committed Phase-2 baseline
```

Either reads the observation set **once**, derives `observation_snapshot_id` and
`declaration_version_id` from that read and the working tree, and writes
`build/evaluation/product_adoption_measurements.csv` and `adoption_reconciliation.csv`. The single
read is the point: the snapshot id and both tables describe the same rows, never two reads that
straddle a refresh. The CSVs are git-ignored — they are an upload artifact, not repository state.

**`--live` is fixed.** `adoption_measurements.load_current_observations` coerced a pandas
`Timestamp` but not the plain `str` the deployed table's `observed_at` actually arrives as through
`pyoso` (pyoso has no `Timestamp` to hand back for that column, so it serializes it as ISO-8601
text instead), and the strict digest rejected the string on purpose — it would bypass UTC
normalization. The fix is a new `_coerce_observed_at` step at the load boundary, in
`build/adoption_measurements.py`, that parses the string into a `datetime` and hands it to the
digest exactly as it would have received a `Timestamp`; the digest's own UTC-normalization rule
is unchanged. All three `--live` callers (`adoption_measurements`, `adoption_reconciliation`,
`serialize_evaluation`) share this one load function, so the fix covers all three.
`tests/test_adoption_evaluation.py` pins the str/`datetime` digest equivalence and, when
`OSO_API_KEY` is set, a live check that the deployed current table still digest-matches the
committed baseline parquet.

As optional assurance before a publish, the same equivalence can still be checked by hand:

```bash
uv run python -c "from build import adoption_measurements as M; \
from build.observation_snapshot import rows_from_parquet, observation_content_digest as d; \
print(d(rows_from_parquet()) == d(M.load_current_observations()))"
```

`True` means the baseline and the deployed current table are still the same content, so building
from the baseline (if you choose to) would produce the same bytes as `--live`. `False` means the
live table has genuinely moved since the baseline was captured — build from `--live` in that case
rather than treating the baseline as current.

Sanity-check the row counts against what the builder reports over the baseline
(`uv run python -m build.adoption_measurements` and `... adoption_reconciliation`), remembering the
live counts move with the live observations.

## 3. Publish

`build/publish_evaluation.py` does the upload — it reuses `publish_registry`'s `graphql`,
`resolve_static_models`, and `upload`, and before any mutation it VALIDATES the candidates (exact
headers against the builders' `COLUMNS`, non-empty tables, constant-and-matching
`declaration_version_id` / `observation_snapshot_id` / `routing_policy_version`, unique grain, and
reconciliation covering exactly the recorded assessments). A candidate that fails is never uploaded.

```bash
uv run python -m build.publish_evaluation --plan       # validate + plan; offline, no creds, NO write
uv run python -m build.publish_evaluation --dry-run    # validate + read-only id resolution; NO mutation, NO write
uv run python -m build.publish_evaluation              # validate, upload, run, then archive
```

`--plan` and `--dry-run` write nothing. A real publish resolves (or creates) the `evaluation`
dataset and each static model, `PUT`s the CSV, and requests the load run — which is only *accepted*
synchronously. Runs are requested **one model at a time and awaited in turn** — a request naming
both models fans out into two runs, returns only one of them, and the two race to create the
dataset's Trino schema on a first publish. It **waits for each load run to reach terminal
`SUCCESS`** and **verifies the deployed row counts and column schema match the candidate** (read
back via `pyoso`, retrying while the query catalog catches up, and ignoring the loader's own
`_dlt_*` columns). A candidate column that is null in every row may be absent from the deployed
table: the loader types columns from records and drops one it never sees a value for
(`adoption_reconciliation.override_id` today). Only when every run succeeded and the deployed data
matches does it write an **immutable deployment archive** at
`build/evaluation/deployments/<deployment_id>/` (the two CSVs it just uploaded plus a completed
receipt of row counts, column schema, and SHA-256). The `deployment_id` is the declaration and
observation identities; the archive is written once and is never overwritten. **Any partial failure
— a run that ends non-`SUCCESS` or times out, or a deployed count/schema mismatch — returns nonzero
and writes no archive**, so the previous deployment's archive stays the authoritative rollback
target and a later rerun of the same identities is not blocked by an archive that was never truly
deployed. Record the `dataset_id`, `model_id`, and the archive path with the deploy note.

## Rollback — re-upload the previous deployment's archived bytes

A static-model publication **replaces the table in place**; the platform exposes no prior-revision
list to re-point to, and `observations.product_adoption_current` may have changed since, so
regenerating from an old commit does **not** reproduce the previous table. Rollback therefore means
**re-uploading the exact bytes of the previous successful deployment** — which the publisher
archived for you:

1. Find the previous deployment archive. Before a deploy the publisher prints it as the rollback
   target; otherwise it is the appropriate directory under `build/evaluation/deployments/` (its
   `receipt.json` records the row counts and SHA-256 that were live).
2. Re-run the publisher pointed at that archive:

   ```bash
   uv run python -m build.publish_evaluation --dir build/evaluation/deployments/<previous-id>/
   ```

3. Confirm the deployed row counts / SHA-256 match that archive's `receipt.json`.

The candidate CSVs under `build/evaluation/` are never the rollback record — only a completed
deployment archive is, which is why it is written after a successful upload and never overwritten.
Nothing downstream consumes these tables yet (Phase 4's gate is not enabled), so a rollback has no
consumer to break — but do not leave a half-loaded table marked `active` in the inventory: if a
load fails midway, re-upload the previous archive's bytes or revert the inventory entry to `staged`.

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
