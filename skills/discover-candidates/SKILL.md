---
name: discover-candidates
description: Use when sweeping the outside world for products the map does not yet have — GitHub, Hugging Face, package registries, papers, launch venues — and turning the result into candidate rows in sources/registry/. Every source is swept, and any candidate with at least one addressable artifact (github, huggingface, a package, arxiv, or homepage) can be emitted. This is the step before the map changes. For one product you already know about use add-product; to turn a seeded roster into published products use promote-category; to re-verify what is published use refresh-category.
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

1. **Read the category list at run time, through `build.taxonomy.category_statuses(taxonomy)`.**
   It takes the loaded taxonomy mapping — `category_statuses(yaml.safe_load(...))`, not a
   zero-argument call, which raises `TypeError`. A remembered list silently drops every
   candidate belonging to a category added since — and parsing `sources/taxonomy.yaml` by hand
   drops the `{name, status}` entries, which is the failure that broke `build_stack_map`.
2. **Artifacts are identifiers, not URLs.** `github: owner/repo`, not
   `https://github.com/owner/repo`; same for `huggingface_*`, `crates`, `arxiv`, and bare
   package names for `pypi` / `npm`. `homepage` is the only URL on the row. Serialization builds
   the public URL *from* the identifier, so a URL there serializes to a doubled link. Source
   URLs and fetch dates go in the batch summary, not on the row.
3. **A row needs at least one addressable artifact, not `github` specifically (#365).** Any of
   `github`, `huggingface_model`, `huggingface_dataset`, `pypi`, `npm`, `crates`, `arxiv` or
   `homepage` satisfies the schema, so an HF-only or package-only candidate can now be emitted.
   A candidate with none of these is still parked in the summary. Never invent an artifact to
   satisfy the schema, and treat an arxiv-only or homepage-only row as weaker evidence than a
   repo- or package-backed one.
4. **Do not invent a legitimacy rule mid-sweep.** Park the candidate and say why in the
   summary. A threshold that exists only in one run's output cannot be reproduced or appealed.
5. **A 429 is not a measured absence.** Retry or leave the field out; never record
   "cannot determine" for a rate limit.

## Agent orchestration

Parallelizes well on fetching, badly on judgment. Harvest signals, source URLs and artifact
identifiers concurrently; keep dedup, category assignment and boundary calls in one place,
because they depend on the whole candidate set rather than on any single row.

## Output

Populated `sources/registry/<category>.yaml` files — appended, or created for a category with
no file yet — and a summary carrying the five reconciled counts (`raw_signals =
duplicate_signals + unique_candidates`; `unique_candidates = accepted + parked`), and the
source URL and fetch date behind every candidate, accepted or parked, each parked one with its
reason. Not a prose report, and not a PR per candidate.

A registry row rejects unknown keys, so the summary is the only place a reason, a source URL
or an ambiguity can be recorded. It is part of the deliverable, not a covering note.
