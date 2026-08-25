---
name: discover-candidates
description: Use when sweeping the outside world for products the map does not yet have — GitHub, Hugging Face, package registries, papers, launch venues — and turning the result into candidate rows in sources/registry/. This is the step before the map changes. For one product you already know about use add-product; to turn a seeded roster into published products use promote-category; to re-verify what is published use refresh-category.
---

# Discover candidates for the map

Thin wrapper. The procedure lives in the workflow doc; this file does not restate it.

## Trigger

A sweep should turn into candidate rows the map can act on. Typically a recurring pass over
new releases and launches, or a targeted sweep of one category that looks thin.

Not for adding a product you have already chosen (`add-product`), not for promoting a seeded
roster into head products (`promote-category`), not for re-verifying a published category
(`refresh-category`).

## Required reading

**Read `docs/workflows/discover-candidates.md` and follow it.** It carries the dedup order,
the emit contract, the one-product-one-category rule and the escalation conditions. Read
`docs/workflows/promote-category.md` too — it consumes what this produces, and its triage
rules are the standard these rows are eventually held to.

## The four traps, named

The workflow explains each. They are listed here because every one of them has produced a
sweep that had to be thrown away.

1. **Read the category list from `sources/taxonomy.yaml` at run time.** A remembered list
   silently drops every candidate belonging to a category added since.
2. **Emit artifact URLs.** `slug`, `display_name`, `type`, `org` and `github` are required by
   `docs/schemas/registry.schema.json`. Names and star counts alone cannot become a row.
3. **Do not invent a legitimacy rule mid-sweep.** Flag the row and park it. A threshold that
   exists only in one run's output cannot be reproduced or appealed.
4. **A 429 is not a measured absence.** Retry or leave the field out; never record
   "cannot determine" for a rate limit.

## Agent orchestration

Parallelizes well on fetching, badly on judgment. Harvest signals and artifact URLs
concurrently; keep dedup, category assignment and boundary calls in one place, because they
depend on the whole candidate set rather than on any single row.

## Output

Populated `sources/registry/<category>.yaml` files and a summary with reconciled counts and
parked candidates. Not a prose report, and not a PR per candidate.
