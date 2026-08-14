# os-ai-map documentation

Start here. This repo is organized around the **task you arrived to do**, not the internal
name for it. Find your task below, open the one workflow it points to, and follow it. Each
workflow names the reference material and the exact gates it needs; you should not have to
know the internal vocabulary before you begin.

## Five doors

| I want to… | Workflow | Skill |
|---|---|---|
| Add a new product to the map | [`workflows/add-product.md`](workflows/add-product.md) | `add-product` |
| Change something about an existing product | [`workflows/update-product.md`](workflows/update-product.md) | `update-product` |
| Create a category, or change its definition, weights, or roster | [`workflows/edit-category.md`](workflows/edit-category.md) | `edit-category` |
| Re-verify a whole category against its sources | [`workflows/refresh-category.md`](workflows/refresh-category.md) | `refresh-category` |
| Change the schema or meaning of an axis, corpus-wide | [`workflows/migrate-axis.md`](workflows/migrate-axis.md) | `migrate-axis` |

`update-product` is a router: describe what changed and it sends you to the right procedure.
When in doubt about which door, start there.

## The three kinds of document

- **`workflows/`** answers *how do I accomplish this task?* — one per contributor intent, all
  in the same template.
- **`reference/`** answers *what rules and concepts govern the task?* — the normative specs the
  workflows point at. A rule lives here once; workflows reference it rather than restating it.
- **`operations/`** is maintainer-only: deploying warehouse models, publishing the map, running
  the fetchers. Editors do not run these (see `AGENTS.md` on the read-only boundary).
- **`schemas/`** is the machine-readable JSON Schema for the source files.

## Reference material

| Doc | What it governs |
|---|---|
| [`reference/identity.md`](reference/identity.md) | Slugs, aliases, and how releases combine into a tier |
| [`reference/openness.md`](reference/openness.md) | The openness ladders, license tiers, and classes |
| [`reference/adoption.md`](reference/adoption.md) | The adoption bands and instruments |
| [`reference/capability.md`](reference/capability.md) | The capability axis and the peer-comparison instrument |
| [`reference/evidence-and-freshness.md`](reference/evidence-and-freshness.md) | What `last_verified` means, how an axis earns it, the gates |
| [`reference/product-copy.md`](reference/product-copy.md) | The `description`/`comments` prose spec |
| [`reference/gap-analysis.md`](reference/gap-analysis.md) | How the map derives gaps from scores |
| [`reference/queries.md`](reference/queries.md) | Query conventions for the warehouse |
| [`reference/notebook-design.md`](reference/notebook-design.md) | The published map's visual style |

## Advanced / internal skills

Off the primary path, for maintainers and the automation loop: `build-rubric` (derive a
category's scoring ladder), `add-data-source` (register a fetcher), `refresh-all-categories`
(drive the whole-corpus sweep), `pyoso-analyst` (read-only warehouse analysis).

For the repo map, build pipeline, and data model, see `AGENTS.md`.
