---
name: migrate-axis
description: Use when changing the structure or meaning of an openness, adoption, or capability axis across the whole corpus — splitting a field, normalizing an instrument, restructuring components. A deliberately strict, script-only workflow in os-ai-map. Not for one product's value or one category's ladder.
---

# Migrate an axis

Thin wrapper over a deliberately **low-freedom** workflow. This file does not restate the
checklist; it enforces the posture.

## Trigger
The change is to what an axis *records or means*, corpus-wide — not one product's value
(`update-product`) and not one category's weights or ladder (`edit-category` / `build-rubric`).

## Required reading
**Read `docs/workflows/migrate-axis.md` and follow the ten-step impact checklist in order.**
It covers the contract, the schema, the migration script, the checkers, serialization, the
warehouse and front-end contracts, the docs, the before/after distribution, and the removal
rule for the old shape.

## The rule this skill enforces
**A migration requires a deterministic migration script and prohibits ad-hoc hand edits across
the corpus.** If you find yourself editing product files one at a time, stop — that is what this
workflow exists to prevent. The bulk YAML diff is the script's output; reviewers check the
script and the distributions, not hundreds of files. Use `build/components.py`'s block-safe
helpers, never a `yaml.load`/`dump` round-trip.

## Scripts to run
```bash
uv run python -m build.validate            # under the new schema
uv run python -m build.check_verification
uv run python -m build.check_payload
uv run python -m pytest tests/ -q
```
Plus the before/after distribution comparison, and (maintainer) `check_parity` once the
warehouse side is deployed (`docs/operations/deploy-models.md`).

## Stop and escalate
- It is really one category's ladder → `build-rubric`.
- The warehouse or front-end contract must change in lockstep → coordinate the deploy, don't
  ship the repo half alone.
