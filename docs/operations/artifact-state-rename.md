# Runbook: Rename the source artifact-state tables (Phase 2, maintainer)

`data-architecture.md` §11.6 resolved `repo_state` / `hub_state` -> `artifact_state` as
"Do it, with the observations adapters that repoint the same SQL," landing in **Phase 2**.
The same section's closing rule governs the shape of the work: **no rename is performed as a
standalone change — each rides a phase that already repoints the same SQL, so no PR exists
purely to rename a deployed table.** This runbook is that ride. It describes a coordinated
platform-and-repository change; it does not perform one, and nothing here is applied yet.

**This is a maintainer step and needs OSO platform write credentials.** An editor session
cannot run it: creating, repointing and dropping deployed tables are warehouse writes, which
`AGENTS.md` and §17 reserve for a maintainer. The repository half rides in lockstep and is a
normal PR, but it must not merge ahead of the platform half — see the next section for why.

The two assets are `signal_github.repo_state` and `signal_huggingface.hub_state`, renamed to
`signal_github.artifact_state` and `signal_huggingface.artifact_state`.

## Decision on record

- **Two source-specific tables, not one merged table.** The rename gives both assets a common
  basename under their own datasets. It does **not** collapse them into a single
  `observations.artifact_state`. Naming rule 11.1a.4 blesses exactly this: a reused basename is
  correct "when the tables implement a common interface and a compatible grain — the namespace
  is what distinguishes them," and it names `signal_github.artifact_state` and
  `signal_huggingface.artifact_state` as the sanctioned case. Merging the two would be a schema
  normalization with a grain reconciliation — GitHub's grain is
  `one row per (product_slug, repo) at one fetched_at`, Hugging Face's is
  `one row per (product_slug, artifact_kind, artifact_id) at one fetched_at` — and belongs to
  the `observations.*` layer this rename feeds, not to the rename. It is out of scope here.
- **The rename rides the Phase 2 repoint, and only that.** The observation adapters and every
  downstream consumer move to the new tables in the same coordinated change. There is no
  rename-only PR.

## Why this cannot stage ahead of the platform

Renaming the repository assets before the platform tables are renamed would fail a gate and
break provenance. Both are hard stops, not warnings.

- **The deployed-model census gate.** `warehouse/audits/platform_models.json` is the
  credential-free receipt of the Phase 0b audit, and
  `tests/test_assets_inventory.py::test_platform_models_checked_is_backed_by_the_census`
  asserts that every mirrored asset's `table` appears in the census. The receipt records these
  two under their current names, `currentai.signal_github.repo_state` and
  `currentai.signal_huggingface.hub_state`. Rename the `table` fields in `assets.yaml` while the
  platform still serves the old names and the receipt still lists them, and the repository
  declares a table the platform does not have — the gate fails.
- **Mirror provenance.** Each asset carries a provenance-locked `mirror:` block bound to the
  live deployed UDM (`model_id`, `revision`, `hash`, `local_sha256`, `synced_at`).
  `test_mirror_local_sha256_matches_the_bytes` ties `local_sha256` to the exact bytes of the
  model file, and the merge-base gate (`mirror_provenance_violations`) treats any byte change as
  a refetch that must advance `revision`, `hash` and `synced_at` together. Renaming the model
  file's `def` from `repo_state` to `artifact_state` changes the bytes, so the provenance can
  only move once the platform has actually redeployed the model under the new name and produced
  a new revision to record. The repository cannot mint that provenance on its own.

So the flip is a single coordinated event: the platform gains the new tables and redeploys the
models, then the repository records the new names and the new provenance in one PR against that
proven state. The old tables stay alive across the window as compatibility assets until the
consumer inventory is clean.

## Procedure

Ordered. Steps 1-3 and 6 are platform writes; step 4 is the repository PR that must merge only
after step 3 is proven; step 5 spans both.

### 1. Create both new tables alongside the old ones

On the platform, deploy `currentai.signal_github.artifact_state` and
`currentai.signal_huggingface.artifact_state` as source-specific tables with the same
definitions, grains and secrets as the current `repo_state` / `hub_state` models. **Do not drop
the old tables.** Both pairs run in parallel for the whole window. This is a two-model deploy,
not a `RENAME`, precisely so the old names keep serving their consumers until step 3 repoints
them and step 6 retires them.

### 2. Verify schema, identity coverage and row parity old-vs-new

Before anything repoints, prove the new tables reproduce the old ones exactly:

- **Schema** — column names, types and nullability identical between each old table and its new
  twin.
- **Identity coverage** — the same set of `product_slug` (and, for Hugging Face, the same
  `(product_slug, artifact_kind, artifact_id)`) appears in the new table as in the old, with no
  dropped or invented rows.
- **Row parity** — a per-row comparison at a fixed `fetched_at`, not a row count. Every drift
  this project has shipped was invisible to a count; parity here means the new table and the old
  agree row for row on the columns the consumers read.

If parity does not hold, stop. A repoint onto a table that silently differs is exactly the
failure `check_parity` exists to catch elsewhere, and here nothing downstream would fail loudly.

### 3. Repoint the observation adapters and every downstream consumer

Change each consumer below from the old table to its new twin, in the same coordinated change.
Read the repository and confirm the list is complete before starting — grep
`warehouse/models/`, `build/` and `sources/` for `repo_state` and `hub_state`; the SQL/config
reads are the ones that must change, and the prose mentions (see the note after the tables) are
the ones that must not be mistaken for them.

`signal_github.repo_state` -> `signal_github.artifact_state`:

| Consumer | File | Reference |
|---|---|---|
| Evidence adapter | `warehouse/models/evidence/product_evidence.sql` | `FROM currentai.signal_github.repo_state`, and the `source_table` string literal it emits into the evidence rows |
| GitHub adoption banding | `warehouse/models/signal_github/product_adoption.sql` | `FROM currentai.signal_github.repo_state` |
| Redirect probe gate | `build/check_artifacts.py` | `SELECT ... FROM currentai.signal_github.repo_state WHERE resolved_via_redirect = true` |
| Signal routing | `sources/signal_routing.yaml` | `sources.github.table` |

`signal_huggingface.hub_state` -> `signal_huggingface.artifact_state`:

| Consumer | File | Reference |
|---|---|---|
| Evidence adapter | `warehouse/models/evidence/product_evidence.sql` | `FROM currentai.signal_huggingface.hub_state`, and the two `source_table` string literals it emits (license row and privacy/storage row) |
| Hugging Face adoption banding | `warehouse/models/signal_huggingface/product_adoption.sql` | `FROM currentai.signal_huggingface.hub_state` |
| Signal routing (model) | `sources/signal_routing.yaml` | `sources.huggingface_model.table` |
| Signal routing (dataset) | `sources/signal_routing.yaml` | `sources.huggingface_dataset.table` |

Note: the `signal_huggingface.hub_state` route is filtered by `artifact_kind` into the model and
dataset routes, so both `sources.huggingface_model.table` and `sources.huggingface_dataset.table`
name the same table and both must be repointed.

**Prose mentions are not reads and must not be repointed as if they were.** Comments in
`warehouse/models/signal_packages/product_adoption.sql`,
`warehouse/models/signal_packages/downloads.sql` and
`warehouse/models/signal_packages/downloads_daily.py`, and the design comments in the two
`product_adoption.sql` models, name `repo_state` / `hub_state` in explanatory text, not in a
`FROM`. The reads-extraction rule in §11.3 — strip comments and docstrings before counting a
reference, keep string literals — is the discriminator: only the `FROM` clauses, the
`check_artifacts.py` SELECT, the `product_evidence.sql` `source_table` literals, and the
`signal_routing.yaml` `table:` values are consumers. Update the prose mentions for accuracy in
the same PR if you like, but keep them out of the consumer count.

### 4. Update the repository in lockstep

This is the repository PR, merged only after step 3 is proven against real platform state.
Regenerate every derived field rather than hand-editing it (`build/assets.py` owns
`reads`/`read_by` and the DAG; `build.audit_platform_models` owns the census receipt).

- **`warehouse/assets.yaml`** — for each of the two assets:
  - the asset `id` (`signal_github.repo_state` -> `signal_github.artifact_state`;
    `signal_huggingface.hub_state` -> `signal_huggingface.artifact_state`);
  - `table` (`currentai.<dataset>.artifact_state`);
  - `files.model` (see below);
  - `reads` / `read_by` — regenerated by `build/assets.py`, never hand-edited, so the derived
    graph reflects the renamed files and repointed SQL;
  - the `mirror:` block — `model_id`, `revision`, `hash`, `local_sha256` and `synced_at` set to
    the values the step-1 redeploy actually produced. If the platform redeploys under a new
    `model_id`, add a `mirror_migration` note so the provenance gate allows the `model_id`
    change (`test_model_id_change_is_allowed_with_a_migration_note`).
- **Model file paths** — rename with `git mv` and rename the function inside each:
  - `warehouse/models/signal_github/repo_state.py` -> `warehouse/models/signal_github/artifact_state.py` (and `def repo_state` -> `def artifact_state`);
  - `warehouse/models/signal_huggingface/hub_state.py` -> `warehouse/models/signal_huggingface/artifact_state.py` (and `def hub_state` -> `def artifact_state`).
  The path must derive the table (`test_path_derives_the_table`), and the byte change from the
  `def` rename means the mirror provenance must advance in step with the platform redeploy, per
  the provenance rule above.
- **`warehouse/audits/platform_models.json`** — regenerate with
  `uv run python -m build.audit_platform_models` (needs `OSO_API_KEY`) against the real platform
  state, so the census lists the new table names. Do not hand-edit it; the receipt validator and
  `test_platform_model_consumers_match_the_receipt` bind it to what the audit derives.
- **`docs/architecture/current-state-dag.md`** — regenerate against the current state; the DAG
  nodes and edges for `signal_github__repo_state` / `signal_huggingface__hub_state` become the
  `artifact_state` nodes. `test_committed_dag_matches_the_renderer` fails if it is left stale.

**`signal_github.repo_state` carries an external consumer, `sta-grantmaker-view`, in its
`external_consumers`.** It must be carried onto `signal_github.artifact_state`, not silently
dropped. An external consumer is outside `read_by` and invisible to the derived graph, so the
rename cannot see it — record it by hand on the renamed asset and coordinate the cutover with
that consumer's owner. (`signal_huggingface.hub_state` is `external_consumers: none_confirmed`;
carry that value forward unchanged.)

### 5. Keep the old tables as compatibility assets

While both pairs run in parallel, keep `signal_github.repo_state` and
`signal_huggingface.hub_state` in `assets.yaml` as `status: compatibility`, each naming its new
twin as `replacement`
(`test_deprecated_assets_name_a_replacement_or_removal_condition`). They stay deployed and stay
in the census until step 6. This is what lets the external consumer and any unaudited reader move
on their own schedule instead of breaking on the flip.

### 6. Retire the old tables

Drop `currentai.signal_github.repo_state` and `currentai.signal_huggingface.hub_state` from the
platform, and remove their compatibility assets from `assets.yaml`, **only after** the consumer
inventory confirms nothing reads them — the in-repo `read_by` is empty for both, `sta-grantmaker-view`
has confirmed its move off `repo_state`, and `consumer_checks` is clean. An empty in-repo reader
list is not by itself evidence a table is unused (§11 opens with exactly that trap); the external
consumer is the reason retirement is a separate, later step and not part of the flip.

## Rollback

- **Before step 6 (old tables still live).** The flip is reversible with no data loss. Repoint
  the step-3 consumers back to `repo_state` / `hub_state`, revert the step-4 repository PR
  (restoring the old ids, tables, file names, mirror blocks and the regenerated census/DAG), and
  leave the new `artifact_state` tables in place or drop them — nothing depends on them once the
  consumers point back. The old tables never stopped serving, so this is a clean revert.
- **After step 6 (old tables dropped).** Rollback means recreating
  `currentai.signal_github.repo_state` and `currentai.signal_huggingface.hub_state` from their
  model definitions and re-running them, then reverting the repository. This is why step 6 waits
  on a clean consumer inventory: once the old names are gone, undoing the rename is a redeploy,
  not a revert.
