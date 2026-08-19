---
name: promote-category
description: Use when a preliminary category's signal-only seed roster in sources/registry/ must become fully researched head products and the category published into the map. For creating the category or editing its record use edit-category; for one product use add-product; for re-verifying a published category use refresh-category.
---

# Promote a preliminary category to published

Thin wrapper. The procedure lives in the workflow doc; this file does not restate it.

## Trigger
A category sits in `sources/taxonomy.yaml` as `{name: <slug>, status: preliminary}` with candidates
in `sources/registry/<slug>.yaml`, and the task is to research them into head products and publish.
Not for creating the category (`edit-category`), not for a single product (`add-product`), not for
re-verifying one already published (`refresh-category`).

## Required reading
**Read `docs/workflows/promote-category.md` and follow it.** It carries the triage rules, the
boundary-rejection convention, the six files each promotion touches, the capability-matrix step and
the publication conditions. Read `docs/workflows/add-product.md` too - it governs each individual
record and this workflow does not repeat its traps.

## Agent orchestration
Long job, so it parallelizes badly on judgment and well on fetching. Harvest the evidence for every
candidate first - repo record, license body, README, package metadata - and cache it, then make the
identity, boundary and scoring calls against what was fetched rather than against memory. Never
assert a 2025+ release, a license or a download figure from recall.

Budget the GitHub API: 60 requests an hour unauthenticated, three to four per candidate. Check
`GITHUB_TOKEN` works before the first sweep, because a stale one 401s silently and reads as every
repository being dead.

Write new files with `yaml.safe_dump(..., sort_keys=False, allow_unicode=True)`. Edit existing
corpus files only through `build/components.py` - never load-modify-dump a file in `sources/`.

## Scripts to run
```bash
uv run python -m build.validate            # 0 error(s)
uv run python -m build.check_recipe
uv run python -m build.check_rubric
uv run python -m build.check_verification
uv run python -m build.check_capability
uv run python -m build.check_adoption
uv run python -m build.check_instrument
uv run python -m build.check_artifacts --live
uv run python -m build.serialize_registry --check
uv run python -m build.serialize_rubric --check
uv run pytest -q
```

## Stop and escalate
- Category has no `scoring_recipe`, or its evidence is prose the ladder cannot read → `build-rubric`.
- A product needs a change to a **shared** rubric (a license tier, a dimension) → defer the product
  with a substantive reason and leave the ruling to a maintainer.
- A candidate's identity cannot be settled against primary sources → leave it in the registry.
- Never commit `build/notebook_data.json` or `notebooks/`.
