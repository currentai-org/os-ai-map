# CLAUDE.md

Entry point for agent sessions in `os-ai-map`. Four things, then get to work:

1. **`AGENTS.md` is the repo map** — directory layout, the `build/` stages, the data model,
   how to write to `sources/`, and the traps that have caught people before. Read it.
2. **`docs/README.md` routes your task to its workflow.** Find yours there and follow the
   workflow document; do not improvise a procedure one already carries.
3. **Use the registered skill for that workflow.** They live under `.claude/skills/` (symlinks
   into `skills/`), so the Skill tool should list them by name; if it does not, read
   `skills/<name>/SKILL.md` directly. `update-product` is the router if you are unsure which
   door.
4. **Warehouse writes are maintainer-only.** UDM revisions, static-model reloads and notebook
   publishes are steps under `docs/operations/`. An editor session works in `sources/`, `docs/`
   and `notebooks/`, and opens a PR.

## Scope boundary

This repository governs the **Open Source AI Gap Map's data system**, not the OSO organization's
warehouse. Two files, kept disjoint: a **governed asset** belongs in `warehouse/assets.yaml` only if it
is a governed output (a published table powering the map), repo-owned computation implementing/auditing
map semantics, or a temporary compatibility shim with an exit. A **direct OSO input** those depend on
belongs in `warehouse/dependencies.yaml` as a contract (not owned) — **never in `assets.yaml`**. A table
that merely exists on OSO, or is read only by a standalone notebook or another platform product, is
**out of scope** entirely — it lives on OSO. See `docs/architecture/adr-003-repository-scope-boundary.md`
(Accepted — implementation pending). **Phase-5 platform migration stays frozen** until the ADR-003
mechanism lands: the `role` field, `warehouse/dependencies.yaml` contracts, the root-scoped DAG, and the
anti-reintroduction gates are all merged. Accepting the ADR does not lift the freeze; the old Phase-5
runbooks are **superseded**, not re-enabled.

## Conventions

- `uv` for everything Python. `uv run python -m build.<module>`; every module takes `--help`.
- Trino SQL for warehouse work.
- American English. No AI tells in commits, PRs, or prose.
- Category slugs are `underscore_form`; product and org slugs are `kebab-case`.
