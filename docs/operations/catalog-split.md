# Runbook: Phase 5 catalog split — relocate a table to its target namespace (maintainer)

`data-architecture.md` §11.6 resolved the long-tail and signal relocations as "moved Phase 5":
`entities` to `catalog`, `events`/`metrics` to `observations`, `scores` to `evaluation`, and the
signal measurement tables to `observations`. `warehouse/assets.yaml` records each pending move as
`current_namespace` / `target_namespace` with `migration_status: pending`. This runbook is the
**general procedure** for executing one such move, and it grows one **instance** section per move
as each is run. It generalizes `artifact-state-rename.md` — the proven Phase-2 coordinated rename —
to a namespace relocation; read that runbook first, because the gates, the provenance rules, and
the rollback it documents apply here unchanged.

**This is a maintainer step and needs OSO platform write credentials.** An editor session cannot
run it: creating, repointing and dropping deployed tables are warehouse writes, which `AGENTS.md`
and §17 reserve for a maintainer. The repository half rides in lockstep and is a normal PR, but it
must not merge ahead of the platform half — a relocated `table` in `assets.yaml` names a table the
platform does not yet serve, and the deployed-model census gate
(`test_platform_models_checked_is_backed_by_the_census`) fails. Nothing in this doc is applied by
introducing the doc; the doc is docs-only and mergeable on its own.

## Why a move is a rename under the naming rules

A namespace relocation changes a table's fully-qualified name
(`currentai.signal_semanticscholar.paper_citations` →
`currentai.observations.paper_citations`), so every consumer's `FROM` and every source binding that
names it must be repointed. §11.6's closing rule governs the shape: **no move is performed as a
standalone change — each rides Phase 5, which repoints the same SQL, so no PR exists purely to
rename a deployed table.** The basename is preserved across the move; only the namespace changes.
Naming rule 11.1a already blesses a basename living in the namespace that classifies it (a raw
measurement belongs in `observations`, not in a per-source `signal_*` dataset).

## The general procedure

Ordered. Steps 1–3 and 6 are platform writes; step 4 is the repository PR that must merge only
after step 3 is proven; step 5 spans both. This is `artifact-state-rename.md`'s procedure with the
rename target generalized to a namespace move.

### 1. Create the new table alongside the old one

On the platform, deploy the target `currentai.<target_namespace>.<basename>` with the **same
definition, grain and secrets** as the current model. **Do not drop the old table.** Both run in
parallel for the whole window, so the old name keeps serving its consumers until step 3 repoints
them and step 6 retires it. This is a deploy of the same model under a new identity, not a
`RENAME`.

If the model calls `context.fetch()`, the twin must declare
`capabilities=oso.Capabilities(fetch=True)` — the one sanctioned non-identity delta, exactly as in
`artifact-state-rename.md` step 1. A model that instead declares `external_origins=[...]` and does
not call `context.fetch()` carries no such delta; its twin is byte-identical except for identity.

### 2. Verify equivalence old-vs-new (code / schema / identity, not rows)

Before anything repoints, prove the new table is equivalent to the old one on everything
deterministic. **Do not claim byte-for-byte row parity** — two independently running external
fetchers drift on live counts and timestamps, and some source models fail their live fetch
reproducibly (see the paper_citations instance below). Require instead, per
`artifact-state-rename.md` step 2:

- **Identical model code** except the model identity itself (file path, `def` name, target table)
  and any sanctioned `capabilities` line.
- **Identical schema and identity coverage** — column names, types, nullability, and the same set
  of resolved identity keys present in both.
- **A documented comparison of the dynamic fields** at paired run times, with expected drift (or a
  shared upstream failure) explained. An unexplained divergence is the failure this step exists to
  catch.

Assert exact data equality only if both models run against the same captured input snapshot;
otherwise do not advertise it.

### 3. Repoint every consumer

Change each consumer from the old table to the new one in the same coordinated change. **Read the
repository and confirm the list is complete before starting** — grep `warehouse/models/`, `build/`,
`sources/` and `notebooks/` for the old fully-qualified name. §11.3's reads-extraction rule is the
discriminator: strip comments and docstrings before counting a reference, keep string literals.
Only `FROM` clauses, `source_table`/`source_dataset` string literals, `signal_routing.yaml`
`table:` values, and code `SELECT ... FROM` reads are consumers; prose mentions in comments are not
and must not be repointed as reads (update them for accuracy in the same PR if you like, but keep
them out of the consumer count).

**A `signal_routing.yaml` `table:` repoint is a behavior-neutral source relocation, not a routing
policy change.** It names a new address for the same data; it does not change a route, a band, or an
aggregation rule, so it does **not** bump `routing_policy_version` — exactly as the Phase-2
`artifact_state` repoint of `sources.*.table` did not. Only a change to the routing *rules* bumps
that version.

### 4. Update the repository in lockstep

The repository PR, merged only after step 3 is proven against real platform state. Regenerate every
derived field rather than hand-editing it (`build/assets.py` owns `reads`/`read_by` and the DAG;
`build.audit_platform_models` owns the census receipt).

- **`warehouse/assets.yaml`** — change the moved asset's `table` to
  `currentai.<target_namespace>.<basename>`, set `current_namespace: <target_namespace>` and
  `migration_status: done` (delete the `target_namespace` line once it equals the current one, per
  the file's own convention that a row is deleted when it stops being temporary), and point
  `files.model` / `producer` at the relocated model file below. For a platform-authored mirror,
  set the `mirror:` block (`model_id`, `revision`, `hash`, `local_sha256`, `synced_at`) to the
  values the step-1 redeploy actually produced; if the platform deploys under a new `model_id`, add
  a `mirror_migration` note so the provenance gate allows the `model_id` change. A repo-authored
  model (`authority: repo`, no `mirror:` block) carries no mirror provenance — but if it is
  deployed (`materialized: true`) it must still be redeployed at step 1/3 so the census matches.
- **Model file — `git mv` only when the old table is already retired.** While the old table is
  still deployed (steps 1–5), the old mirror file must stay in place with its `mirror:` block
  untouched, and the new file is added alongside — a `git mv` would delete a file whose table the
  platform still serves. Add `warehouse/models/<target_namespace>/<basename>.py` (path derives the
  table, `test_path_derives_the_table`) with its own freshly-fetched `mirror:` block from the
  step-1 redeploy; keep the old file until step 6. If the model is repo-authored and *not* yet
  deployed (`status: staged`), there is no platform table to preserve and the file is `git mv`d
  directly in this PR — a repo-only relocation with no platform coordination.
- **Repointed consumer models advance their own provenance too.** Any repointed consumer that is
  itself a platform-authored mirror has its bytes changed by the repoint, so its redeployed
  revision must be refetched and its `mirror:` block advanced in this same PR. A repo-authored
  consumer (e.g. `observations/product_adoption_current.sql`, `authority: repo`) carries no mirror
  block, but if it is deployed its redeploy is still part of step 3.
- **`warehouse/audits/platform_models.json`** — regenerate with
  `uv run python -m build.audit_platform_models` (needs `OSO_API_KEY`) against real platform state,
  so the census lists the new table name. Never hand-edit it.
- **`docs/architecture/current-state-dag.md`** — regenerate against the current state
  (`test_committed_dag_matches_the_renderer` fails if stale).
- **External consumers travel by hand.** An `external_consumers` entry is outside `read_by` and
  invisible to the derived graph, so it must be carried onto the relocated asset explicitly and its
  cutover coordinated with that consumer's owner — never silently dropped.

### 5. Keep the old table as a compatibility asset

While both run in parallel, keep the old table in `assets.yaml` as `status: compatibility`, naming
the relocated table as its `replacement`
(`test_deprecated_assets_name_a_replacement_or_removal_condition`). It stays deployed and in the
census until step 6, letting external and unaudited readers move on their own schedule.

### 6. Retire the old table

Drop the old table from the platform and remove its compatibility asset **only after** the consumer
inventory confirms nothing reads it — in-repo `read_by` empty, `consumer_checks` clean, and every
external consumer confirmed moved. An empty in-repo reader list is not by itself evidence a table is
unused (§11's opening trap); the external consumers are why retirement is a separate, later step.

## Rollback

Identical to `artifact-state-rename.md`'s rollback. Before step 6 the move is a clean revert:
repoint consumers back, revert the step-4 PR, and drop or ignore the new table (nothing depends on
it once consumers point back), because the old file, id and table were preserved untouched. After
step 6 rollback is a redeploy of the dropped model, not a revert — which is why step 6 waits on a
clean consumer inventory.

---

## Instance 1 — `signal_semanticscholar.paper_citations` → `observations.paper_citations`

The pilot move: the smallest fully-isolatable relocation in Phase 5. One in-repo consumer, no
platform consumers, no external consumers, and no entanglement with the held `scores`/`evidence` →
`evaluation` cluster.

**The asset.** `currentai.signal_semanticscholar.paper_citations` — `authority: platform`
(platform-authored mirror: `model_id cc73d808-5833-4a91-a47b-35bb0414b6f0`; the mirror records
`revision 3`, and the platform's released revision is 4, whose code is byte-identical to revision
3 — only the revision-level cron metadata changed, `@manual` to `""`), `status: active`,
`materialized: true`, dataset cron `0 1 * * 0`. Model file
`warehouse/models/signal_semanticscholar/paper_citations.py` (`async def paper_citations`,
`external_origins=["https://api.semanticscholar.org"]`, `depends_on` the product-artifacts
registry).

**Correction, found in execution (2026-08-26).** An earlier draft of this section claimed the
model "does not call `context.fetch()`" and therefore that the twin carries no `capabilities`
delta. Both halves were wrong: the model body calls `context.fetch()` for the batch POST (it
declares `external_origins` *as well*), and `createDataModelRelease` refused the byte-identical
twin with `undeclared-fetch-capability`. The general procedure's sanctioned-delta rule is what
actually applied — the twin adds the one line `capabilities=oso.Capabilities(fetch=True)`, exactly
as in `artifact-state-rename.md` step 1, and is otherwise byte-identical except for its
path/`def`/table.

**The target.** `currentai.observations.paper_citations`, model file
`warehouse/models/observations/paper_citations.py` (path derives the table). No name collision
exists in `observations`.

**Consumers to repoint (step 3).** The complete list, comments excluded:

| Consumer | File | Reference |
|---|---|---|
| Adoption current-state normalization | `warehouse/models/observations/product_adoption_current.sql` | `FROM currentai.signal_semanticscholar.paper_citations` (line 124) **and** the `source_table` string literal it emits (line 123) |
| Signal routing (arxiv source) | `sources/signal_routing.yaml` | `semanticscholar.table` (line 100) — a behavior-neutral source relocation, no `routing_policy_version` bump |

The comment at `product_adoption_current.sql` line 49 names the table in explanatory prose, not a
`FROM`; update it for accuracy but keep it out of the consumer count. `product_adoption_current` is
`authority: repo` with **no `mirror:` block**, so it advances no mirror provenance — but it is
deployed (`materialized: true`), so its repoint is redeployed at step 3 and must re-materialize
cleanly under its declared-identity guard (revision 3).

**The 429 caveat on step 2.** `paper_citations` fails its live `0 1 * * 0` fetch reproducibly on an
upstream Semantic Scholar HTTP `429` (recorded in `migration-status.md`; the fix is a
platform-owned model change, issue #358-class, out of scope here). Equivalence is therefore proven
on **code, schema and identity coverage** — the twin's code is byte-identical except the sanctioned
`capabilities` line, so its schema and resolved-key coverage are identical — and the dynamic-field
comparison documents the **shared** upstream failure rather than treating it as a divergence. Do
not gate the move on a clean paired live run that the upstream will not currently allow; the
relocation neither causes nor fixes the 429. Verified shared at paired run times 2026-08-26: both
models, fired minutes apart, failed with the identical `semantic scholar batch returned 429 for
24 ids`, the traceback line offset by exactly the twin's one added decorator line. One
consequence the caveat does not remove: the twin's **table** must exist before step 3, because a
consumer cannot be repointed at a name the warehouse does not serve, and a full-refresh model
that has never succeeded has no table. The pilot's step 3 therefore waits on the twin's first
successful materialization.

**Provenance to advance (step 4).**

- New asset `observations.paper_citations`: `table`, `files.model` /`producer` →
  `warehouse/models/observations/paper_citations.py`, and a `mirror:` block refetched from the
  step-1 redeploy. If the redeploy mints a new `model_id`, add a `mirror_migration` note.
- Old asset `signal_semanticscholar.paper_citations`: transitioned to `status: compatibility` at
  step 5 (`replacement: observations.paper_citations`), removed at step 6.
- `product_adoption_current.sql`: repointed (`FROM` + `source_table` literal), redeployed;
  regenerated `read_by`/DAG reflect the new edge. No mirror block to advance.
- Regenerate `platform_models.json` and `current-state-dag.md`.

**Scope note.** `signal_semanticscholar.paper_citations` has `external_consumers: none` and no
`platform_model_consumers`, so step 6 retirement waits only on the in-repo consumer inventory being
clean after step 3.
