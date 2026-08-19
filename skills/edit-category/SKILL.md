---
name: edit-category
description: Use when an editor wants to create a category or change an existing one's definition, strapline, axis weights, or product roster in os-ai-map. For giving a category its scoring ladder, use build-rubric; for re-verifying a category's products, use refresh-category.
---

# Edit a category

Thin wrapper. The procedure lives in the workflow doc; this file does not restate it.

## Trigger
Creating a category, or changing its `description`, `strapline`, `weights`, or product roster.
Not for authoring a `scoring_recipe` (that is `build-rubric`) and not for re-verifying products
(that is `refresh-category`).

## Required reading
**Read `docs/workflows/edit-category.md` and follow it.** It carries the editable fields, the
roster rules, the taxonomy step for a new category, and the note that there is no `litmus` field
(`category.schema.json` sets `additionalProperties: false`).

## Agent orchestration
Edit `sources/categories/<slug>.yaml` surgically — never load-modify-dump. Creating a category
also touches `sources/taxonomy.yaml` (assign it to an arc and lifecycle status). Preliminary
category seeds live in `sources/registry/<slug>.yaml`; adding a head product to the roster
requires its product + score files to exist first (`add-product`).

## Scripts to run
```bash
uv run python -m build.validate            # 0 error(s)
```

## Stop and escalate
- Needs a `scoring_recipe`, or `components` values are prose not tokens → `build-rubric`.
- Changing what an axis *means* corpus-wide → `migrate-axis`.
- Never commit `build/notebook_data.json` or `notebooks/`.
