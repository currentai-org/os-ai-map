---
name: curate-category
description: Use when an editor owns a category and wants to edit its definition, litmus, axis weights, scoring recipe, or curate (add/remove/reorder) its product roster in os-ai-map.
---

# Curate a Category

A category editor owns one file: `sources/categories/<slug>.yaml`. It holds the
category's definition, litmus test, axis weights, scoring recipe, and the **ordered
product roster** (the array order is the display order).

## Steps

1. Open `sources/categories/<slug>.yaml`.
2. Edit any of: `display_name`, `strapline`, `weights.{adopt,cap}`,
   `scoring_recipe`, `comments`, and the `products:` roster. The `name` field is the
   slug; do not rename it after creation. To regroup or reorder categories across
   arcs, edit `sources/taxonomy.yaml`: that is the only place arc grouping and
   cross-category display order live (a category file no longer carries `arc` or `order`).
3. To add a product, it must already have a `sources/products/<slug>.yaml` and a
   `sources/scores/<slug>.yaml` (use the `add-product` skill first), then append its slug
   to `products:`. A product slug may appear in exactly one category roster.
4. Reorder by moving slugs within `products:`.
5. Validate: `uv run python -m build.validate`: must print `0 error(s)`.
6. Rebuild + preview: `uv run python -m build.serialize && uv run python build/render.py`,
   then `uv run marimo export html notebooks/ai-stack-map.py -o /tmp/preview.html`.
   Preview only: do not commit `build/notebook_data.json` or `notebooks/ai-stack-map.py`
   (a bot regenerates them on merge; CI blocks PRs that hand-edit them).
7. Open a PR. Do not deploy UDMs or publish. That is a maintainer step (see
   `docs/runbooks/`).

## Boundaries
- Read-only on the warehouse. No MCP, no uploads.
- One product, one category: validation enforces it. If you want a product moved,
  remove its slug from the old roster and add it to yours in the same PR.
- Adding a brand-new category also requires adding its slug to an arc in
  `sources/taxonomy.yaml`, or validate fails with
  "must appear in exactly one taxonomy arc".
