# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

`os-ai-map` is the public data + modeling home behind the AI Stack Map. It holds curated
YAML (`sources/`), warehouse SQL and fetchers (`warehouse/`), a deterministic build
pipeline (`build/`), and the published notebook (`notebooks/`).

There is no front-end in this repo. The website lives in `ecosystem-mapping/app/`.

## Directory map

```
sources/               Curated YAML: organizations, categories, products, scores + taxonomy.yaml
warehouse/models/      UDM SQL (entities, events, metrics, scores)
warehouse/ingest/      Python fetchers that write CSVs to warehouse/catalog/
warehouse/catalog/     Raw external CSVs (GoodAI List, HF benchmarks, etc.)
warehouse/sources.yaml Manifest linking each external source to its fetcher
build/                 Python pipeline: validate.py, serialize.py, render.py, slugs.py, orgs.py
notebooks/             Generated marimo notebook (ai-stack-map.py)
docs/guides/           Query conventions and notebook style guide
docs/runbooks/         Maintainer deploy runbooks
docs/schemas/          JSON Schemas for the source files (four concerns + taxonomy)
tests/                 pytest suite for build helpers and round-trip proof
```

## Data model

The curated source set is four per-record YAML concerns in `sources/` plus the single
`sources/taxonomy.yaml` manifest:

- **organizations**: one file per org (`name`=slug, `display_name`, `type`, `homepage`),
  referenced by slug from products.
- **categories**: one file per stack-map category (`name`=slug, `display_name`). Owns the
  ordered product roster (`products:` array). Order equals display order. One product
  appears in exactly one category. Category files no longer carry `arc` or cross-category
  `order`. Optional `comments` array for curator notes.
- **products**: one file per product. `name` is the slug (kebab-case); `display_name` is
  the human label. Open artifacts are declared as typed top-level arrays of `{url: ...}`
  objects: `github`, `npm`, `pypi`, `crates`, `go`, `huggingface_model`,
  `huggingface_dataset`. Only keys with entries are included. Optional `comments` array.
- **scores**: one file per product (same slug) with `openness`, `adoption`, `capability`.
  Every non-null score value requires a `sources:` citation entry.
- **taxonomy.yaml**: owns arc grouping + cross-category display order
  (`arcs:` -> ordered category slugs). `serialize.py` derives order + arc from here, and
  validate enforces that every category appears in exactly one arc.

Category slugs are underscore form (`base_pretrained`). Product and org slugs are
hyphenated kebab-case (`llama-3-1`).

## Build pipeline

```bash
uv run python -m build.validate        # validate sources/ (must print "0 error(s)")
uv run python -m build.serialize       # sources/ -> build/notebook_data.json
uv run python build/render.py          # -> notebooks/ai-stack-map.py
uv run marimo export html notebooks/ai-stack-map.py -o /tmp/preview.html
```

## Editor posture (read-only on the warehouse)

Editors (curators, analysts) work only in `sources/`, `docs/`, and `notebooks/`. They
open PRs. They do not:

- Run MCP tools.
- Upload or revise UDMs or static models.
- Push to main directly.

All warehouse write operations are maintainer steps. See `docs/runbooks/`.

## Skills

Four Claude Code skills are defined in `.claude/skills/`:

| Skill | When to use |
|-------|------------|
| `curate-category` | Edit category definition, weights, litmus, or product roster |
| `add-product` | Add a new product (scaffolds product + score YAML, updates roster) |
| `add-data-source` | Register a new external data source and add a fetcher |
| `pyoso-analyst` | Query `currentai.*` tables via `pyoso` (read-only analysis) |

Invoke a skill before doing editor work. The skills enforce the read-only boundary and
walk through validation + preview steps.

## Maintainer runbooks

After a PR merges, a maintainer (OSO MCP write access) may need to:

- `docs/runbooks/deploy-udms.md`: revise, release, and run UDM SQL changes.
- `docs/runbooks/refresh-data.md`: run fetchers and reload static models.
- `docs/runbooks/publish-notebook.md`: serialize, render, upload, and publish the live
  notebook to `/currentai/ai-stack-map` (id `7b29bf47`).

## Environment

- `OSO_API_KEY` loaded automatically via `direnv` (place in `.env`, which is gitignored).
- See `.env.example` for the required variable.
- OSO MCP connects via HTTP to `localhost:8000/mcp` with a Bearer token in `.mcp.json`
  (maintainer only).

## Common references

- Query conventions: `docs/guides/queries.md`
- Notebook style: `docs/guides/notebooks.md`
- Coverage backlog: `docs/catalog-gaps.md`
- Warehouse inventory: `warehouse/models/README.md`
