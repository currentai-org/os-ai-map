---
name: add-product
description: Use when an editor wants to add a new product to the AI Stack Map. Scaffolds the product + score YAML, links its org, and adds it to one category roster in os-ai-map.
---

# Add a Product

Creates three coordinated edits: a product file, a score file, and a roster entry.

## Steps

1. **Pick the slug** — kebab-case of the product name (e.g. `OLMo 2` becomes `olmo-2`). If the
   slug is taken, suffix the org slug (`command-r-cohere`).
2. **Organization** — ensure `sources/organizations/<org-slug>.yaml` exists; if not,
   create it (`slug`, `name`, `type`, `homepage`, `country`).
3. **Product** — create `sources/products/<slug>.yaml`:
   ```yaml
   slug: <slug>
   name: <Display Name>
   org: <org-slug>
   type: model | software | dataset
   description: <one paragraph>
   artifacts:
     repos: [owner/name]        # the warehouse computes adoption from these
     hf_models: []
   flags: []
   ```
4. **Score** — create `sources/scores/<slug>.yaml`. Use the owning category's
   `scoring_recipe` (in its category file) for openness checklist, capability basis, and
   adoption signal. **Every non-null openness/capability value needs a primary `sources:`
   entry** `{url, shows, accessed}`. Adoption may be left for the warehouse to compute
   from artifacts.
   ```yaml
   product: <slug>
   openness:   { score: 5, class: open_source, confidence: high, note: ..., sources: [{url: ..., shows: ..., accessed: 2026-06-09}] }
   adoption:   { level: null, signal_type: unknown, note: "computed from artifacts" }
   capability: { score: null, basis: "n/a" }
   ```
5. **Roster** — append `<slug>` to the owning `sources/categories/<cat>.yaml` `products:`.
6. **Validate**: `uv run python -m build.validate` must print `0 error(s)`.
7. **Verify the source** — never assert a product/version from memory. Confirm any 2025+
   release against a PRIMARY source (vendor HF org / blog / registry). A plausible press
   claim that does not survive a check is rejected.
8. Rebuild + preview, then open a PR.

## Boundaries
- Read-only on the warehouse. No MCP, no uploads.
