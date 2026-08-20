# Contributing to os-ai-map

Thanks for helping map the open source AI stack. All curation happens through pull requests
editing the YAML files in `sources/`. CI validates every PR, so you can't break anything a
maintainer won't catch. This project is [MIT licensed](LICENSE); contributions are accepted
under the same terms.

## Quick start

```bash
uv sync
uv run python -m build.validate   # must print "0 error(s)"
```

No API keys are needed to edit sources or run validation.

## The data model in one minute

One YAML file per record, four concerns plus one manifest:

| Path | What it holds |
|------|---------------|
| `sources/products/<slug>.yaml` | The product: `name` (slug), `display_name`, `type`, `description`, typed artifact URL arrays, optional `comments` |
| `sources/scores/<slug>.yaml` | Openness / adoption / capability scores. Every non-null value needs a `sources:` citation |
| `sources/organizations/<slug>.yaml` | The org, plus the `products:` roster it owns |
| `sources/categories/<slug>.yaml` | The category, plus its **ordered** `products:` roster (order = display order) |
| `sources/taxonomy.yaml` | Arc grouping and cross-category display order |

Machine-readable JSON Schemas for all five file types live in `docs/schemas/`. Invariants
(validated in CI): a product appears in exactly one category roster and exactly one org roster;
every product has a matching score file; product/org slugs are kebab-case, category slugs
underscore form.

## Find your task

The procedures live in [`docs/README.md`](docs/README.md), which routes you to one workflow per
task. This file no longer restates them, so there is only one copy of each to keep true.

| I want to… | Go to |
|---|---|
| Add a new product | [`docs/workflows/add-product.md`](docs/workflows/add-product.md) |
| Change an existing product | [`docs/workflows/update-product.md`](docs/workflows/update-product.md) |
| Create or edit a category | [`docs/workflows/edit-category.md`](docs/workflows/edit-category.md) |
| Re-verify a category | [`docs/workflows/refresh-category.md`](docs/workflows/refresh-category.md) |
| Change an axis's schema or meaning | [`docs/workflows/migrate-axis.md`](docs/workflows/migrate-axis.md) |

The rules each workflow relies on — scoring ladders, adoption bands, the prose spec, how a
score earns its date — live once in [`docs/reference/`](docs/reference/).

## Suggesting without writing YAML

Open an issue instead — there are structured forms for **suggest a product**, **report an
error**, and **propose a category**. A maintainer (or an agent) turns accepted suggestions into
PRs.

## For agent-assisted editing

If you use a coding agent, the repo ships skills that mirror these workflows: `add-product`,
`update-product`, `edit-category`, `refresh-category`, `migrate-axis`, plus the advanced
`build-rubric`, `add-data-source`, and `pyoso-analyst`. They are registered under
`.claude/skills/`. See `AGENTS.md` for the repo map.

## Touching the warehouse layout

Adding, moving or retiring a data asset means updating
[`warehouse/assets.yaml`](warehouse/assets.yaml) in the same PR — it is one entry per
platform table, and `tests/test_assets_inventory.py` fails if a tracked model or data file
is not declared there.

Do not hand-edit `reads`, `read_by` or any count: they are derived from the tree by
`build/assets.py` and compared against the file. Regenerate instead.

`docs/architecture/data-architecture.md` is the normative document for what the namespaces
mean and which gate protects which edge. Read
`adr-002-registry-curated-catalog-discovered.md` before deciding whether something belongs
in `registry` or `catalog`.
