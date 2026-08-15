---
name: update-product
description: Use when an editor wants to change an existing product in the AI Stack Map — its identity/artifacts, its description/comments prose, a score's evidence or value, its category/org membership, or to retire it. Routes the change to the right procedure. For a brand-new product use add-product.
---

# Update a product

The single door for changing an existing product. Thin wrapper over a router — describe what
changed and the workflow doc sends you to the right procedure. This file does not restate the
routes.

## Trigger
Anything about an existing product needs to change. If it does not exist yet, use `add-product`.

## Required reading
**Read `docs/workflows/update-product.md` and follow its classifier.** It routes by what
changed: identity/artifacts (including a version bump like "add v1.5" — the slug never changes),
prose only, a score's evidence or value, roster membership, or retirement (a slug retires as an
alias, never a deletion).

## Agent orchestration
- **Prose-only** change: rewrite `description`/`comments` to `docs/reference/product-copy.md`
  against primary sources. This never touches scores and never writes `last_verified`.
- **A score moved**: this is evidence work and earns a date — re-read the cited sources, record
  the evidence, and stamp `last_verified` per `docs/reference/evidence-and-freshness.md`. Do not
  just edit the number. If the whole category is stale, use `refresh-category` instead.
- Edit `sources/` files surgically via `build/components.py`; never load-modify-dump.

## Scripts to run
```bash
uv run python -m build.validate
uv run python -m build.check_artifacts     # if artifacts changed
uv run python -m build.check_retirement    # if you recorded an alias
uv run python -m build.check_verification  # if you dated an axis
```

## Stop and escalate
- The change is really axis-wide schema/vocabulary → `migrate-axis`.
- The category can't ladder the new evidence → `build-rubric`.
- Never commit `build/notebook_data.json` or `notebooks/`.
