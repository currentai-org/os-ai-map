---
name: add-product
description: Use when an editor wants to add a new product to the AI Stack Map. Scaffolds the product + score YAML, links its org, and adds it to one category roster and one org roster in os-ai-map.
---

# Add a Product

Creates four coordinated edits: a product file, a score file, a category roster entry, and an org roster entry.

## Steps

1. **Pick the slug**: kebab-case of the product name (e.g. `OLMo 2` becomes `olmo-2`). The
   slug becomes the `name` field. If the slug is taken, suffix the org slug
   (`command-r-cohere`); if that also collides, append a numeric suffix (`-2`, `-3`)
   (matches `build/slugs.py`).
2. **Product**: create `sources/products/<slug>.yaml`. Use `name` for the slug and
   `display_name` for the human label. Declare open artifacts as typed top-level arrays of
   `{url: ...}` objects, one key per source type. Only include keys the product actually
   has; products with no open artifacts include none. Products do NOT carry an `org:` field
   (ownership is declared in the org file, not here).
   ```yaml
   name: <slug>
   display_name: <Display Name>
   type: model | software | dataset
   description: <one paragraph>
   github:
     - url: https://github.com/<owner>/<repo>
   pypi:
     - url: https://pypi.org/project/<package>
   comments: "<release / license / provenance notes>"
   ```
   Supported artifact keys: `github`, `npm`, `pypi`, `crates`, `go`,
   `huggingface_model`, `huggingface_dataset`. Omit any key with no entries.
   `comments` is a free-text string for provenance and scoring notes (e.g. version,
   license, last release date). Omit if there is nothing to note. Flag-style judgments
   are left to analyst downstream business logic; there is no `flags` field.
3. **Score**: create `sources/scores/<slug>.yaml`. Use the owning category's
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
4. **Category roster**: append `<slug>` to the owning `sources/categories/<cat>.yaml`
   `products:`. A product slug must appear in exactly one category roster.
   If the owning category is brand-new, also add its slug to an arc in
   `sources/taxonomy.yaml`, or validate fails with "must appear in exactly one taxonomy arc".
5. **Org roster**: append `<slug>` to the owning `sources/organizations/<org-slug>.yaml`
   `products:` array. If the org file does not exist, create it:
   ```yaml
   name: <org-slug>
   display_name: <Org Display Name>
   type: unknown | company | nonprofit | academic | community
   products:
     - <slug>
   ```
   A product slug must appear in exactly one org roster (validated), parallel to the
   category-roster constraint. Both rosters must be updated in the same PR.
6. **Validate**: `uv run python -m build.validate` must print `0 error(s)`.
7. **Verify the source**: never assert a product/version from memory. Confirm any 2025+
   release against a PRIMARY source (vendor HF org / blog / registry). A plausible press
   claim that does not survive a check is rejected. The map is a forward-dated universe
   that can include speculative entries — if a release cannot be confirmed against any
   primary source, mark it SKIP rather than guess.
8. Rebuild + preview, then open a PR. Preview only: do not commit the regenerated
   `build/notebook_data.json` or `notebooks/ai-stack-map.py` (bot-owned; CI blocks
   hand-edits).

## Openness class & score quick-reference

Assign `class` first, then the 0–5 `score` (full rationale in
`docs/guides/openness-spectrum.md`). Calls that are easy to get wrong:

- **Models:** `closed` (proprietary/API-only, no weights) = 1; `open_weights` (weights
  public but restrictive license and/or no open data) = 3; `open_source` (open weights +
  data + code under an OSI license) = 5. Google's **Gemma license is NOT OSI** →
  Gemma/CodeGemma are `open_weights`, not open_source.
- **Software:** `open_source` (OSI license, full source, no feature-gated core) = 5;
  `open_core` (OSS core + a commercial cloud/feature tier, e.g. LangGraph, LlamaIndex) = 4;
  `source_available` = 2; `closed` = 0–1. **Fair-code** (e.g. n8n's Sustainable Use
  License) and **BSL 1.1** (e.g. Pathway) are NOT OSI → `source_available`, even when
  marketed as "open source".
- A custom copyright line can make GitHub report `NOASSERTION` for a genuine MIT/Apache
  license — check the LICENSE body, don't trust the GitHub classifier.
- Keep generic version buckets (e.g. "GPT-5 line", "Claude Opus 4.x") rather than
  splitting frontier models into every point release.

## Adding in batches

For more than a few products, generate the files with a small Python script
(`yaml.safe_dump(..., sort_keys=False, allow_unicode=True)` for the product/score/org
files, plus a helper that inserts `- <slug>` lines under the `products:` block of existing
category/org YAMLs so their formatting is preserved) — far less error-prone than
hand-writing each file. Verify every product against PRIMARY sources first (parallel
research agents work well). **After a batch, two hand-authored things drift and must be
re-checked:** category **straplines** (see the `curate-category` skill) and the
`build/_frozen_long_tail.json` dedup counts (`scored` / `overlap` / `uncategorized`).

## Boundaries
- Read-only on the warehouse. No MCP, no uploads.
