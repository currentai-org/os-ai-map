# os-ai-map

The public data + modeling home behind the [AI Stack Map](https://oso.xyz/currentai/ai-stack-map).

Curated YAML in `sources/` feeds a deterministic build pipeline that serializes to
`build/notebook_data.json`, renders to `notebooks/ai-stack-map.py`, and publishes to
the OSO platform. There is no front-end in this repo; the website lives in
`ecosystem-mapping/app/`.

---

## Contributing

Community curation happens through pull requests and issue forms.

- **[CONTRIBUTING.md](CONTRIBUTING.md)** — data model, scoring rubric, and step-by-step recipes
- **Issue forms** — [suggest a product](https://github.com/currentai-org/os-ai-map/issues/new?template=suggest-a-product.yml), [report an error](https://github.com/currentai-org/os-ai-map/issues/new?template=report-an-error.yml), or [propose a category](https://github.com/currentai-org/os-ai-map/issues/new?template=propose-a-category.yml)

Every PR runs CI: `build.validate`, `pytest`, and a serialize dry-run. PRs that hand-edit
`build/notebook_data.json` or `notebooks/ai-stack-map.py` are blocked — a bot regenerates
those on merge to `main`. Code and data are [MIT licensed](LICENSE).

---

## Repository layout

| Path | Role |
|------|------|
| `sources/` | Curated YAML: organizations, categories, products, scores + `taxonomy.yaml` |
| `build/` | Validate, serialize, render pipeline |
| `notebooks/` | Generated marimo notebook (`ai-stack-map.py`) |
| `warehouse/` | UDM SQL, ingest fetchers, and external CSV catalog |
| `docs/schemas/` | JSON Schemas for all source file types |
| `docs/guides/` | Query and notebook conventions |
| `docs/runbooks/` | Maintainer deploy steps (MCP write access) |
| `skills/` | Agent skills for common editor workflows |
| `tests/` | pytest suite for build helpers |

See [AGENTS.md](AGENTS.md) for agent-oriented project context.

---

## Data model: four concerns plus one manifest

One YAML file per record, four concerns **plus** the single `sources/taxonomy.yaml` manifest:

| Path | Contains | Key rule |
|------|----------|----------|
| `sources/organizations/` | Org metadata (`name`, `display_name`, optional `type`, `homepage`, `github`, `comments`) and a `products:` roster | Each product slug appears in exactly one org roster |
| `sources/categories/` | Category definition (`display_name`, optional `strapline`, `weights`, `scoring_recipe`, `comments`) and an ordered `products:` roster | Order = display order; each product in exactly one category |
| `sources/products/` | Product record (`name`, `display_name`, `type`, `description`, typed artifact URL arrays, optional `comments`) | No `org:` or `flags` fields — org membership is declared in the org file |
| `sources/scores/` | Per-product `openness`, `adoption`, `capability` | Every non-null score value needs a `sources:` citation |
| `sources/taxonomy.yaml` | Arc grouping + cross-category display order (`arcs:` → category slugs) | Every category appears in exactly one arc |

Category slugs use underscore form (`base_pretrained`, `finetuned_chat`). Product and org
slugs use hyphenated kebab-case (`llama-3-1`, `allen-ai`).

Artifact keys on products (include only those that apply): `github`, `npm`, `pypi`,
`crates`, `go`, `huggingface_model`, `huggingface_dataset`.

JSON Schemas: `docs/schemas/`.

---

## Build pipeline

```bash
uv run python -m build.validate        # schema + cross-file invariants (must print "0 error(s)")
uv run python -m build.serialize       # sources/ → build/notebook_data.json
uv run python build/render.py          # → notebooks/ai-stack-map.py
uv run marimo export html notebooks/ai-stack-map.py -o /tmp/preview.html
```

Serialize and render locally for preview only. Do not commit `build/notebook_data.json` or
`notebooks/ai-stack-map.py`.

Note: `build/_frozen_long_tail.json` is a hand-frozen long-tail snapshot (fixture, not derived from
live warehouse data yet).

Deployment (publish notebook, deploy UDMs, refresh warehouse) is maintainer-only — see
`docs/runbooks/`.

---

## Warehouse

`warehouse/` holds SQL models and fetchers that power adoption and activity signals:

- `warehouse/models/` — UDM SQL (entities, events, metrics, scores). See `warehouse/models/README.md`.
- `warehouse/ingest/` — Python fetchers writing CSVs to `warehouse/catalog/`.
- `warehouse/sources.yaml` — manifest linking each external source to its fetcher.

Editors work read-only on the warehouse (no MCP, no uploads). Maintainer runbooks cover writes.

---

## Editor skills

Four skills in `skills/` mirror the CONTRIBUTING recipes:

| Skill | When to use |
|-------|-------------|
| `curate-category` | Edit category definition, weights, litmus, or product roster |
| `add-product` | Scaffold product + score YAML and update category/org rosters |
| `add-data-source` | Register an external data source and add a fetcher |
| `pyoso-analyst` | Query `currentai.*` via `pyoso` (read-only) |

Skills enforce the same read-only warehouse boundary as human editors.

---

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python -m build.validate    # must print "0 error(s)"
uv run pytest -q                   # optional; same suite CI runs
```

No API key is needed to edit sources or run validation. Warehouse queries (`pyoso`, the
analyst skill) require `OSO_API_KEY` (see `.env.example`). With `direnv`, place it in
`.env` and it loads automatically.

---

## Maintainer runbooks

Deploys, UDM refreshes, and notebook publishing require OSO MCP write access.
See `docs/runbooks/`:

- `deploy-udms.md` — revise and release UDM SQL changes
- `refresh-data.md` — run fetchers and reload static models
- `publish-notebook.md` — serialize, render, and publish the live notebook

---

## Further reading

- Query conventions: `docs/guides/queries.md`
- Notebook style: `docs/guides/notebooks.md`
- Warehouse inventory: `warehouse/models/README.md`
