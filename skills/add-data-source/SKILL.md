---
name: add-data-source
description: Use when a governed Gap Map asset needs a new external data input in os-ai-map. Records a platform-owned (OSO or Artio) input as a dependency contract in warehouse/dependencies.yaml, with its reader in the same PR, or a repo-owned file as a governed asset in warehouse/assets.yaml, under ADR-003; building on the platform and syncing mirrors are maintainer runbooks.
---

# Add a Data Source

This repository governs the Gap Map's data system, not OSO's warehouse
([ADR-003](../../docs/architecture/adr-003-repository-scope-boundary.md)). A new source belongs
here only when a **governed asset reads it**: a published Gap Map table, or repo-owned
computation that implements or audits map semantics. A table that merely exists on OSO, or that
only a standalone notebook or another platform product reads, is out of scope. It stays on OSO
and needs nothing in this repository.

Spans two roles. The **curatable** part (anyone can PR) records the source and the reader that
needs it. The **maintainer** part (MCP access) builds or loads the table on the platform and
copies a platform model's released code into its read-only mirror.

## Pick the route first

Who owns the bytes decides the route, and the two files are kept disjoint (gate 3):

- **A platform-owned input: Route A, a dependency contract** in `warehouse/dependencies.yaml`,
  `owner: oso`. This is the usual case. It covers an `oso.*` upstream, and any `currentai.*`
  model built and owned on the platform (OSO or Artio), including one the repo mirrors
  read-only. A contract records what a table carries; it confers no ownership, migration or
  retirement obligation. It never goes in `warehouse/assets.yaml`: `role_violations` refuses
  `authority: platform` under every role, and gate 7 (`mirror_ownership_violations`) refuses a
  governed entry for any file that opens with the `PLATFORM MIRROR (read-only)` banner.
- **A repo-owned artifact: Route B, a governed asset** in `warehouse/assets.yaml`, with a `role`
  and `authority: repo`. Only when the repository itself produces the bytes: a fetcher that needs
  credentials or shaping a platform model cannot do, or a fixed reference set rather than a live
  feed. A committed copy of a live source can only be staler than the source, and nothing
  surfaces the gap: a frozen copy of the GoodAI List listed 300 repos the site had delisted and
  missed 2,056 it had added.

If the source should be built on the platform and does not exist there yet, building it is
platform work: file an issue here naming the governed asset that will read it, mentioning the
maintainer, as ADR-003's "Changing a dependency" section describes. Record the contract once the
table exists.

## Route A: a dependency contract (platform-owned input)

The reader, the contract and, for a `currentai.*` model, its mirror file land in one PR. A PR
missing any of the three fails the gates.

1. **Land the reader in the same PR.** A contract's `required_by` is not trusted: `build/assets.py`
   re-derives it by reachability from a closed root set (governed producer files plus the named
   `AUDIT_ROOTS`; gate 4), and a contract no root reaches fails. So the governed model or module
   that reads the table has to be in the tree. A reader under `build/` that is not a governed
   producer is reachable only if it is named in `AUDIT_ROOTS` in `build/assets.py`, which takes a
   line there with a comment saying what it audits. If the reader also reads governed tables, add
   it to those assets' `read_by`.
2. **Add the contract** to `warehouse/dependencies.yaml`. Required: `table`, `purpose`,
   `expected_grain`, `freshness_requirement`, `required_by` (matching what gate 4 derives) and
   `owner: oso`. Then exactly one provenance anchor:
   - **an `oso.*` upstream**: typed `expected_columns` (`name`, `type`, `nullable` for each),
     `content_contract_sha256` and `verified_at`. The gate recomputes the hash; the recipe is in
     the file's header comment.
   - **a `currentai.*` platform model**: `verified_revision`, equal to `mirror.revision`, a
     `files` block naming the mirror (`model`, plus `schema` when there is one), and a `mirror`
     block (`model_id`, `revision`, `hash`, `synced_at`, and `local_sha256` / `schema_sha256` for
     each claimed file). `platform_schedule` (`cron`, `timezone`, `last_observed_trigger`) is
     optional. Copy the nearest existing contract of the same kind as a template.
3. **The mirror file is required, not optional.** A `currentai.*` contract without one fails
   with "currentai.* dependency needs a mirror model file". The mirror:
   - sits at `warehouse/models/<dataset>/<table>.<ext>` (schema at
     `<table>.schema.json`), so its path derives `currentai.<dataset>.<table>`;
   - opens with the `PLATFORM MIRROR (read-only)` banner on its first line, in `--` form for SQL
     and `#` form for Python; copy the banner from an existing mirror. Gate 7 fails a contract
     whose file lacks it, and a bannered file no contract claims;
   - as `.sql`, names its own table on a `-- currentai.<dataset>.<table>` line within its first
     ten lines (`tests/test_platform_mirror.py`);
   - is hashed against `local_sha256` (and the schema against `schema_sha256`).

   Filling the mirror is a maintainer step. Its bytes and the `mirror` block's values come from
   the released platform model through `GetDataModel`, by steps 1 to 4 of "Mirror resync" in
   [deploy-models.md](../../docs/operations/deploy-models.md). An editor drafts the reader and
   the contract's descriptive fields and asks the maintainer to fill the mirror on the PR.
4. **Contract every table the mirror reads.** Gate 2 follows a mirror file's reads as well as a
   root's, so a non-governed table the mirror reads needs its own contract, with the mirror file
   as its `required_by`. `currentai.evidence.product_evidence`, read by the
   `warehouse/models/scores/openness_facts.sql` mirror, is the template for this
   dependency-to-dependency shape.
5. **A table ADR-003 externalized** (listed in `warehouse/audits/externalization.json`) also
   needs a `reclaims` record in that receipt; see ADR-003's "Reclaiming a dependency".
   `reclaim_violations` refuses a contract for an externalized table without one.
6. **Changing it later.** A field the contract does not carry is a request to the platform, filed
   as an issue against the contract, not an edit to the contract. `uv run python -m
   build.check_mirror_drift` reports a mirror that differs from the platform's latest revision
   (release state is not readable, so it compares against the latest revision, not a deployed
   one).

## Route B: a governed asset (repo-owned artifact)

1. **Add the asset entry** to `warehouse/assets.yaml` with `role` (`governed-output`,
   `repo-computation`, `governed-data` or `compatibility-shim`, as ADR-003's role table defines),
   `authority: repo`, and every other field the inventory requires. `role_violations` re-derives
   the role from the entry's own fields (`release_path: true` is `governed-output`, a model file
   is `repo-computation`, neither is `governed-data`) and fails a disagreement. Copy the nearest
   existing entry of the same role as a template, and let `tests/test_assets_inventory.py` name
   anything missing, including `reads` and `read_by`.
2. **For a fetcher**, add the producer at `warehouse/models/<dataset>/<table>.py`, writing to
   `warehouse/data/<dataset>/<table>.csv`, and name both in the entry's `files` block (`model`
   and `data`). The path mirrors the table: `models/<dataset>/<table>.<ext>` is
   `currentai.<dataset>.<table>`. A repo-owned model file carries no mirror banner (gate 7).
   Large dumps go in `.gitignore`. The `catalog.*` tables are externalized under ADR-003 and have
   no producer in this repository, so nothing under a `catalog` dataset is a template.

## Run the gates (both routes)

Both routes change derived documents. Update every `<!-- count:KEY -->` marker under
`docs/architecture/` the change moves (`dependencies` and `governed_assets` in ADR-003,
`tracked_warehouse_files` in `data-architecture.md`), and regenerate the committed DAG:

```bash
uv run python -c "import sys; from build.assets import render_dag; sys.stdout.write(render_dag())" \
  > docs/architecture/current-state-dag.md
uv run pytest -q tests/test_assets_inventory.py tests/test_scope_gates.py tests/test_platform_mirror.py
uv run python -m build.validate
```

`test_assets_inventory.py` runs the gates over the real manifests: every managed file is claimed
and exists, the path derives the table, `reads`/`read_by` match the tree, the roles hold
(`role_violations`, gate 1), contracts are reachable from the closed root set with a matching
`required_by` and a sound provenance anchor (`dependency_violations`, gates 2 to 4), mirror
banners agree with ownership (`mirror_ownership_violations`, gate 7), mirror bytes move with
their revision against the merge base, the marked counts are current and the committed DAG
matches the renderer. `test_scope_gates.py` shows each of those gates failing on a constructed
violation. `test_platform_mirror.py` checks that each `.sql` mirror declares the table its
contract names. Then open a PR.

## Maintainer step (not in this skill)

Building or releasing a model on the platform (OSO or Artio), loading a CSV into the `currentai`
warehouse (static model or UDM), and copying a released model into its mirror file need MCP
access. They are maintainer steps in `docs/operations/deploy-models.md` (including "Mirror
resync") and `docs/operations/refresh-data.md`; an editor session does not run them.
