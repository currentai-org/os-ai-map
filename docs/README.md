# os-ai-map documentation

Start here. This repo is organized around the **task you arrived to do**, not the internal
name for it. Find your task below, open the one workflow it points to, and follow it. Each
workflow names the reference material and the exact gates it needs; you should not have to
know the internal vocabulary before you begin.

## The doors

| I want to… | Workflow | Skill |
|---|---|---|
| Find products the map does not have yet | [`workflows/discover-candidates.md`](workflows/discover-candidates.md) | `discover-candidates` |
| Add a new product to the map | [`workflows/add-product.md`](workflows/add-product.md) | `add-product` |
| Change something about an existing product | [`workflows/update-product.md`](workflows/update-product.md) | `update-product` |
| Create a category, or change its definition, weights, or roster | [`workflows/edit-category.md`](workflows/edit-category.md) | `edit-category` |
| Turn a preliminary category's seed roster into published products | [`workflows/promote-category.md`](workflows/promote-category.md) | `promote-category` |
| Re-verify a whole category against its sources | [`workflows/refresh-category.md`](workflows/refresh-category.md) | `refresh-category` |
| Change the schema or meaning of an axis, corpus-wide | [`workflows/migrate-axis.md`](workflows/migrate-axis.md) | `migrate-axis` |

`update-product` is a router: describe what changed and it sends you to the right procedure.
When in doubt about which door, start there.

## The kinds of document

- **`workflows/`** answers *how do I accomplish this task?* — one per contributor intent, all
  in the same template.
- **`reference/`** answers *what rules and concepts govern the task?* — the normative specs the
  workflows point at. A rule lives here once; workflows reference it rather than restating it.
- **`operations/`** is maintainer-only: deploying warehouse models, publishing the map, running
  the fetchers, and one-off migrations such as the Phase 2 source-table rename in
  [`operations/artifact-state-rename.md`](operations/artifact-state-rename.md). Editors do not
  run these (see `AGENTS.md` on the read-only boundary).
- **`schemas/`** is the machine-readable JSON Schema for the source files.

## What belongs in a doc

These documents describe how the system works **now**. Someone reading `main` should not have
to mentally subtract six weeks of migration history to understand the current contract.

**Authorship is the test, not subject matter.** A mutable fact may appear only when it is
generated from source at build time. A human must not hand-maintain a value that changes
through normal operation of the system.

| Keep | Delete |
|---|---|
| What a field means, who owns it, how a gate behaves, what the architecture is | Migration chronology: "it was `max()` until…", "these were numbered G1-G6 until…" |
| A current operational limitation, in its one canonical place | Point-in-time observation: "as of 2026-08-20, of 22 datasets, 13 carry…" |
| A date that identifies an immutable artifact — an accepted ADR, a frozen baseline capture, a schema example, a temporary rule while it is still in force | A hand-typed corpus size: "522 products", "openness on all 522 rows" |
| A count interpolated at render time, as `docs/methodology.md` does via `build/render.py` | A count someone typed and must remember to update |

Growth of the corpus should almost never require a documentation change. If adding a product
would make a sentence wrong, that sentence is describing the size of a mutable set — rewrite it
structurally ("adoption may be absent where no qualifying instrument exists") or delete it.

**Every rule has one normative home.** `reference/` holds it; workflows link rather than
restate. Two plausible-looking statements of the same rule are more dangerous than one stale
number, because both read as authoritative. This applies within a file as much as across them.

## Reference material

| Doc | What it governs |
|---|---|
| [`reference/identity.md`](reference/identity.md) | Slugs, aliases, and how releases combine into a tier |
| [`reference/openness.md`](reference/openness.md) | The openness ladders, license tiers, and classes |
| [`reference/adoption.md`](reference/adoption.md) | The adoption bands and instruments |
| [`reference/capability.md`](reference/capability.md) | The capability axis and the peer-comparison instrument |
| [`reference/evidence-and-freshness.md`](reference/evidence-and-freshness.md) | What `last_verified` means, how an axis earns it, the gates |
| [`reference/where-scores-live.md`](reference/where-scores-live.md) | Which axis is in the repo, which is in the warehouse, and which tables only look like scores |
| [`reference/product-copy.md`](reference/product-copy.md) | The `description`/`comments` prose spec |
| [`reference/gap-analysis.md`](reference/gap-analysis.md) | How the map derives gaps from scores |
| [`reference/queries.md`](reference/queries.md) | Query conventions for the warehouse |
| [`reference/sibling-invariants.md`](reference/sibling-invariants.md) | What must hold between a product and its siblings |
| [`reference/notebook-design.md`](reference/notebook-design.md) | The published map's visual style |

## Architecture

How the data assets fit together, as opposed to what any one of them means. Read these
before moving a table between namespaces, retiring a model, or changing what a schedule
claims.

| Doc | What it governs |
|---|---|
| [`architecture/data-architecture.md`](architecture/data-architecture.md) | The namespaces, the target DAG, the gates and their protected edges |
| [`architecture/adr-001-repo-owns-scoring-semantics.md`](architecture/adr-001-repo-owns-scoring-semantics.md) | Why the repository is the only implementation of the scoring rules |
| [`architecture/adr-002-registry-curated-catalog-discovered.md`](architecture/adr-002-registry-curated-catalog-discovered.md) | `registry` versus `catalog`, and which tables are misfiled today |
| [`architecture/adr-003-repository-scope-boundary.md`](architecture/adr-003-repository-scope-boundary.md) | What this repository governs, and what belongs to the platform |
| [`architecture/adr-004-machine-proposals-and-the-public-tail.md`](architecture/adr-004-machine-proposals-and-the-public-tail.md) | Machines propose, humans accept: the tail tier and who may merge what |
| [`architecture/current-state-dag.md`](architecture/current-state-dag.md) | Generated dependency graph |

The inventory those documents specify is [`warehouse/assets.yaml`](../warehouse/assets.yaml),
gated by `tests/test_assets_inventory.py`. It is the authority on what an asset is, who reads
it, and whether its schedule has ever fired — check it before assuming a table is unused.

## Skills off the primary path

Every skill is classified in `skills/registry.yaml` (validated in CI). Beyond the six primary
doors above:

- **Advanced** — deep editorial skills for maintainers: `build-rubric` (derive a category's
  scoring ladder), `clean-score-notes` (strip a record's own history out of its score notes),
  and `refresh-all-categories` (drive the whole-corpus sweep).
- **Internal** — infrastructure and analysis, not map-editing: `add-data-source` (register a
  fetcher), `pyoso-analyst` (read-only warehouse analysis), and `publish-release` (cut a
  versioned release and update the changelog; maintainer only).

For the repo map, build pipeline, and data model, see `AGENTS.md`.
