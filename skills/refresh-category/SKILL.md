---
name: refresh-category
description: Use when one category's products need re-verifying against primary sources — researching each product, auditing the evidence, applying scores and prose together, gating, and opening the category PR. Takes one category slug and finishes it, in os-ai-map.
---

# Refresh a category

This skill is the **agent orchestration** for a category re-read. The procedure — the
per-product unit of work, the four rules a pass may not bend, the gate list, the standing
hazards — lives in `docs/workflows/refresh-category.md`, and this file does not restate it. Two
copies drift, which is the exact failure the sweep exists to fix.

## Trigger
One category needs re-verifying against primary sources (never confirmed, or aged past the
window). For a single product, `update-product`. Invoked by `refresh-all-categories`, which
picks the next category; run directly for a specific one.

## Required reading (you, the orchestrator)
- `docs/workflows/refresh-category.md` — the whole procedure and the gate list
- `docs/reference/evidence-and-freshness.md` — the invariant, the gates, capability confirmations
- `docs/reference/product-copy.md` — the prose spec
- `docs/reference/identity.md` — slugs, aliases, combine rules when releases merge

## The fan-out
Dispatch a `Workflow`, **one agent per product**, in three stages: research → audit → apply.

- **Concurrency is `min(16, cores - 2)`, not a number you choose.** Products with the fewest
  artifacts are the *slowest* (no repo to read; the license comes from pricing pages), and
  categories run worst-coverage-first, so the early ones are the slow ones. Budget by the tail.
- **Model tiers: cheap on the many, expensive on the few.** Research is bounded work (fetch,
  read a LICENSE, draft sixty words) — cheap tier, many agents. Auditing is adversarial reading
  — expensive tier, two agents. The orchestrator is expensive. The split is safe because the
  audit re-verifies from saved bodies rather than trusting the packet.
- **Each research agent reads only two docs** — `product-copy.md` (it is writing prose) and
  `evidence-and-freshness.md` (it is earning the date), plus `identity.md` for a tier/family
  slug. The reading list is multiplied by the batch size, so do not send the orchestration docs;
  the agent is not orchestrating. Preflight computes the recorded dimensions and hands them over.
- **Fetch only through** `uv run python -m build.fetch_source --body-dir <scratch> <url>`, so the
  digest is one the weekly sampled re-fetch can confirm.

## Four things that belong to the agent, not the orchestrator
Each is a defect the sweep actually hit:

- **Namespace scratch files per agent.** The scratchpad is shared; two passes had a fetch log
  overwritten mid-run by a sibling using the same filename. Write under a private subdirectory
  named for the category.
- **Touch only your own category's files** — `sources/{scores,products}/<member>.yaml`. Never
  `docs/`, `tests/`, `.github/`, `build/notebook_data.json`, `notebooks/`, or another category.
- **Escalate anything that moves a level.** The agent that finds a moved `score`/`level`/`class`/
  `reach`, a new or refused artifact, or vanished evidence is not the one who applies it. Escalate
  and carry on — one product does not block the other twenty. A batch escalating nothing is more
  suspicious than one escalating five.
- **Entity moved, not evidence, is a curation call.** A product that merged, split into tiers, or
  was renamed is `docs/reference/identity.md` work, not a re-read. Record it and leave the slug.

## Apply, then gate
Apply deterministically with `build/components.py` (never an agent, never by hand — the YAML does
not round-trip). Then run the canonical gate list from `docs/workflows/refresh-category.md`, and
run `tests/test_components.py` before the full suite (it catches the fragment-nested-as-value bug
that shipped on seven products once). One PR per category, prose and scores together, every moved
score itemized against its evidence. Then stop — a human merges.

## Boundaries
Read-only on the warehouse. Edits `sources/` only, only for the named category. Does not clear
deferrals, split a type, restructure `components`, or change a ladder — each is its own project.

## Related
- `skills/build-rubric/SKILL.md` — when a category's values are not ladderable
- `skills/refresh-all-categories/SKILL.md` — the driver that picks the next category
