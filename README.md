# os-ai-map

The public data + modeling home behind the [AI Stack Map](https://oso.xyz/currentai/ai-stack-map).

Curated YAML in `sources/` feeds a deterministic build pipeline that serializes to
`build/notebook_data.json`, renders to `notebooks/ai-stack-map.py`, and publishes to
the OSO platform.

---

## Contributing

Community curation happens through pull requests and issue forms. Read
[CONTRIBUTING.md](CONTRIBUTING.md) for the data model and step-by-step recipes,
or open a [product suggestion](../../issues/new?template=suggest-a-product.yml)
if you'd rather not write YAML. Every PR is validated by CI. Code and data are
[MIT licensed](LICENSE).

---

## Data model: four concerns plus one manifest

The curated source set is the four per-record concerns (one YAML file per entity)
**plus** the single `sources/taxonomy.yaml` manifest:

| Path | Contains | Key rule |
|-----------|----------|----------|
| `sources/organizations/` | One file per org (`name`=slug, `display_name`, `type`, `homepage`, optional `github` url array + `comments`; owns `products:` roster) | Org declares which products belong to it via a `products:` array |
| `sources/categories/` | One file per stack-map category (`name`=slug, `display_name`, `products`, optional `comments`) | Category owns the **ordered product roster** (`products:` array). Order = display order. |
| `sources/products/` | One file per product (`name`=slug, `display_name`, `type`, `description`; typed artifact arrays per source: `github`, `npm`, `pypi`, `crates`, `go`, `huggingface_model`, `huggingface_dataset`; optional `comments` string) | One product appears in exactly one category roster AND exactly one org roster. No `org:` field on the product; no `flags` field. |
| `sources/scores/` | One file per product (same slug) with `openness`, `adoption`, `capability` | Every non-null score value needs a `sources:` citation |
| `sources/taxonomy.yaml` | Owns arc grouping + cross-category display order (`arcs:` -> ordered category slugs) | Every category must appear in exactly one arc; `serialize.py` derives order + arc from here |

Category slugs use underscore form (`base_pretrained`, `finetuned_chat`).
Product and org slugs are hyphenated kebab-case (`llama-3-1`, `allen-ai`).

JSON Schemas for all five source files live in `docs/schemas/`.

---

## Build pipeline

```
uv run python -m build.validate        # check sources/ for schema + cross-file errors
uv run python -m build.serialize       # sources/ -> build/notebook_data.json
uv run python build/render.py          # build/notebook_data.json -> notebooks/ai-stack-map.py
uv run marimo export html notebooks/ai-stack-map.py -o /tmp/preview.html
```

Deployment (publish to OSO, deploy UDMs) is a maintainer step described in
`docs/runbooks/`.

`build/_frozen_long_tail.json` is a hand-frozen long-tail snapshot pending the
warehouse-recompute follow-up (Phase 3 queue indexer); it is not yet regenerated from
live data, so treat it as a fixture, not a derived artifact.

---

## Warehouse

`warehouse/` holds the SQL models and data fetchers that power the adoption and
activity signals:

- `warehouse/models/`: UDM SQL (entities, events, metrics, scores). See `warehouse/models/README.md`.
- `warehouse/ingest/`: Python fetchers that write CSVs to `warehouse/catalog/`.
- `warehouse/sources.yaml`: manifest linking each external source to its fetcher.

---

## Editor skills

Four Claude Code skills are available in `.claude/skills/`:

| Skill | When to use |
|-------|------------|
| `curate-category` | Edit a category's definition, weights, or product roster |
| `add-product` | Add a new product (scaffolds product + score YAML, updates roster) |
| `add-data-source` | Register a new external data source and add a fetcher |
| `pyoso-analyst` | Query `currentai.*` tables via `pyoso` (read-only) |

All editor skills operate **read-only on the warehouse**. No MCP, no uploads.

---

## Quick start

```bash
uv sync
uv run python -m build.validate    # must print "0 error(s)"
```

No API key is needed to edit sources or run validation. Warehouse queries (`pyoso`,
the analyst skill) require `OSO_API_KEY` (see `.env.example`). With `direnv`, place it
in `.env` and it loads automatically.

---

## Maintainer runbooks

Deploys, UDM refreshes, and notebook publishing require OSO MCP write access.
See `docs/runbooks/`:

- `deploy-udms.md`: revise and release UDM SQL changes
- `refresh-data.md`: run fetchers and reload static models
- `publish-notebook.md`: serialize, render, and publish the live notebook
