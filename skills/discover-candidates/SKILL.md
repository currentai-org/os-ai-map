---
name: discover-candidates
description: Use when sweeping the outside world for products the map does not yet have — GitHub, Hugging Face, package registries, papers, launch venues — and turning the result into candidate rows in sources/registry/. Every source is swept, but only GitHub-backed candidates can be emitted today. This is the step before the map changes. For one product you already know about use add-product; to turn a seeded roster into published products use promote-category; to re-verify what is published use refresh-category.
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

## The five traps, named

The workflow explains each. They are listed here because every one of them has produced a
sweep that had to be thrown away.

1. **Read the category list at run time, through `build.taxonomy.category_statuses()`.** A
   remembered list silently drops every candidate belonging to a category added since — and
   parsing `sources/taxonomy.yaml` by hand drops the `{name, status}` entries, which is the
   failure that broke `build_stack_map`.
2. **Artifacts are identifiers, not URLs.** `github: owner/repo`, not
   `https://github.com/owner/repo`; same for `huggingface_*`, and bare package names for
   `pypi` / `npm`. `homepage` is the only URL on the row. Serialization builds the public URL
   *from* the identifier, so a URL there serializes to a doubled link. Source URLs and fetch
   dates go in the batch summary, not on the row.
3. **Only GitHub-backed candidates can be emitted.** `github` is required on every row, so an
   HF-only, package-only, paper-only or hardware candidate is parked in the summary against
   issue #365. Never invent a repo to satisfy the schema.
4. **Do not invent a legitimacy rule mid-sweep.** Park the candidate and say why in the
   summary. A threshold that exists only in one run's output cannot be reproduced or appealed.
5. **A 429 is not a measured absence.** Retry or leave the field out; never record
   "cannot determine" for a rate limit.

## Agent orchestration

Parallelizes well on fetching, badly on judgment. Harvest signals, source URLs and artifact
identifiers concurrently; keep dedup, category assignment and boundary calls in one place,
because they depend on the whole candidate set rather than on any single row.

## Output

Populated `sources/registry/<category>.yaml` files and a summary carrying the reconciled
counts, the source URL and fetch date behind each accepted candidate, and the parked
candidates with their reasons. Not a prose report, and not a PR per candidate.

A registry row rejects unknown keys, so the summary is the only place a reason, a source URL
or an ambiguity can be recorded. It is part of the deliverable, not a covering note.
