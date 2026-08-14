---
name: add-product
description: Use when an editor wants to add a new product to the AI Stack Map — scaffolding the product + score YAML, linking its org, and adding it to one category roster and one org roster in os-ai-map.
---

# Add a product

This skill is a thin wrapper. The procedure lives in one place and this file does not restate
it — two copies drift, which is the failure the reorg exists to fix.

## Trigger
A product belongs on the map and does not exist yet. If it already exists, use `update-product`.

## Required reading
**Read `docs/workflows/add-product.md` and follow it.** It carries the five files to touch, the
slug rule, the primary-source verification requirement, and the scoring hand-off. The reference
material it names (`identity.md`, `openness.md`, `adoption.md`, `capability.md`,
`product-copy.md`) is authoritative on the rules.

## Agent orchestration
- For a single product, do it inline against primary sources.
- For a batch, generate files with a script: `yaml.safe_dump(..., sort_keys=False,
  allow_unicode=True)` for new files, plus a helper that inserts `- <slug>` lines under existing
  `products:` blocks. **Never** load-modify-dump an existing corpus file. Research every product
  against PRIMARY sources first; parallel research agents work well, but verification is theirs
  to do, not to skip.

## Scripts to run
```bash
uv run python -m build.validate            # 0 error(s)
uv run python -m build.check_recipe        # the ladder accepts the score
uv run python -m build.check_verification  # producible pair
```

## Stop and escalate
- Needs a new category → `edit-category` first (and add it to `taxonomy.yaml`).
- Category can't ladder the evidence → `build-rubric`.
- A release can't be confirmed against a primary source → SKIP, don't guess.
- Never commit `build/notebook_data.json` or `notebooks/` (bot-owned).
