---
name: add-data-source
description: Use when a governed Gap Map asset needs a new external data input in os-ai-map. Records an OSO-owned input as a dependency contract in warehouse/dependencies.yaml, or a repo-owned file as a governed asset in warehouse/assets.yaml, under ADR-003; the warehouse-deploy step is a maintainer runbook.
---

# Add a Data Source

This repository governs the Gap Map's data system, not OSO's warehouse
([ADR-003](../../docs/architecture/adr-003-repository-scope-boundary.md)). A new source belongs
here only when a **governed asset reads it**: a published Gap Map table, or repo-owned
computation that implements or audits map semantics. A table that merely exists on OSO, or that
only a standalone notebook or another platform product reads, is out of scope. It stays on OSO
and needs nothing in this repository.

Spans two roles. The **curatable** part (anyone can PR) records the source and the reader that
needs it. The **deploy** part (maintainer, MCP write) builds or loads it on the platform.

## Pick the route first

Who owns the bytes decides the route, and the two files are kept disjoint (gate 3):

- **An OSO-owned input: a dependency contract** in `warehouse/dependencies.yaml`, `owner: oso`.
  This is the usual case. It covers an `oso.*` upstream, and any `currentai.*` model authored on
  the platform, including one the repo mirrors read-only. A contract records what a table
  carries; it confers no ownership, migration or retirement obligation. It never goes in
  `warehouse/assets.yaml`: `role_violations` refuses `authority: platform` under every role.
- **A repo-owned artifact: a governed asset** in `warehouse/assets.yaml`, with a `role` and
  `authority: repo`. Only when the repository itself produces the bytes: a fetcher that needs
  credentials or shaping a platform model cannot do, or a fixed reference set rather than a live
  feed. A committed copy of a live source can only be staler than the source. The GoodAI List was
  once ingested that way, and the frozen copy drifted to listing 300 repos the site had delisted
  while missing 2,056 it had added, with nothing surfacing the gap.

If the source should be built on OSO and does not exist there yet, building it is platform work:
file an issue here naming the governed asset that will read it, mentioning the maintainer, as
ADR-003's "Changing a dependency" section describes. Record the contract once the table exists.

## Route A: a dependency contract (OSO-owned input)

1. **Land the reader in the same PR.** A contract's `required_by` is not trusted: `build/assets.py`
   re-derives it by reachability from a closed root set (governed producer files plus the named
   `AUDIT_ROOTS`; gate 4). So the governed model or module that reads the table has to be in the
   tree. A reader under `build/` that is not a governed producer is reachable only if it is named
   in `AUDIT_ROOTS`, which takes a line there with a comment saying what it audits.
2. **Add the contract** to `warehouse/dependencies.yaml`. Required: `table`, `purpose`,
   `expected_grain`, `freshness_requirement`, `required_by` (matching what gate 4 derives) and
   `owner: oso`. Then exactly one provenance anchor:
   - **an `oso.*` upstream**: typed `expected_columns` (`name`, `type`, `nullable` for each),
     `content_contract_sha256` and `verified_at`. The gate recomputes the hash; the recipe is in
     the file's header comment.
   - **a `currentai.*` platform model**: `verified_revision`, equal to `mirror.revision`, and a
     `mirror` block (`model_id`, `revision`, `hash`, `synced_at`, and `local_sha256` /
     `schema_sha256` for each claimed file). The mirror file is required, not optional: the
     contract claims a read-only copy of the model under `warehouse/models/<dataset>/` in `files`,
     the gate hashes it against `local_sha256`, and it opens with the `PLATFORM MIRROR (read-only)`
     banner (gate 7, `mirror_ownership_violations`). A contract without it fails with "currentai.*
     dependency needs a mirror model file". Copy the nearest existing contract of the same kind as
     a template.
3. **Changing it later.** A field the contract does not carry is a request to the platform, filed
   as an issue against the contract, not an edit to the contract. `uv run python -m
   build.check_mirror_drift` reports a mirror that differs from the platform's latest revision
   (release state is not readable, so it compares against the latest revision, not a deployed
   one).

## Route B: a governed asset (repo-owned artifact)

1. **Add the asset entry** to `warehouse/assets.yaml` with `role` (`governed-output`,
   `repo-computation`, `governed-data` or `compatibility-shim`, as ADR-003's role table defines),
   `authority: repo`, and every other field the inventory requires. Copy the nearest existing
   entry of the same role as a template, and let `tests/test_assets_inventory.py` name anything
   missing.
2. **For a fetcher**, add the producer at `warehouse/models/<dataset>/<table>.py`, writing to
   `warehouse/data/<dataset>/<table>.csv`, and name both in the entry's `files` block (`model`
   and `data`). The path mirrors the table: `models/<dataset>/<table>.<ext>` is
   `currentai.<dataset>.<table>`. Large dumps go in `.gitignore`. There are no catalog fetchers
   any more: ADR-003 externalized `catalog.*`, so `warehouse/models/catalog/` is gone and is not a
   template.

## Run the gates (both routes)

```bash
uv run pytest -q tests/test_assets_inventory.py tests/test_scope_gates.py
uv run python -m build.validate
```

`test_assets_inventory.py` checks that every managed file is claimed, every declared path
exists, the path derives the table, and `reads`/`read_by` match the tree.
`test_scope_gates.py` asserts the ADR-003 gates: the two files are disjoint, contracts are
reachable from the closed root set with a matching `required_by`, provenance anchors hold, and
mirror banners agree with ownership. Then open a PR.

## Maintainer step (not in this skill)

Building a platform model, loading a CSV into the `currentai` warehouse (static model or UDM), and
releasing a revision need MCP write access. See `docs/operations/refresh-data.md` and
`docs/operations/deploy-models.md`.
