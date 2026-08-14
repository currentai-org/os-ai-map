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
- **Research agents return a packet and edit no file.** One agent per product fetches, re-derives,
  and returns a structured packet; it never writes to `sources/`. The deterministic applier below
  is the only writer. Each packet carries, per axis: the exact `shows` extract (quoted verbatim
  from the fetched body, not paraphrased), the **method for any asserted negative** ("grepped the
  uncompressed sdist for `dpo`; none") — an unmethodded negative is rejected — and a **prose claim
  ledger** listing every factual claim in the current `description`/`comments` marked keep / move /
  drop with a reason, so a rewrite cannot silently drop a durable fact.
- **Model tiers: cheap on the many, expensive on the few.** Research is bounded work (fetch, read a
  LICENSE, draft sixty words) — cheap tier, many agents. Auditing is adversarial and expensive. The
  split is safe because the audit re-verifies from saved bodies rather than trusting the packet.
- **The audit is two-shaped.** Shard the **evidence audit** across up to four workers striped over
  the packets — one agent re-fetching a whole category's digests died mid-response once, and a dead
  audit means shipping unverified. Keep the **prose audit single and batch-wide**: it has to compare
  the batch against itself, which is how it caught two products treating identical vendor language
  differently, something no per-slice agent can see. A `failed` verdict **holds** the product; a
  `suspect` verdict applies its **named corrections**. Do not auto-re-run — a second attempt on a
  systemic prompt defect just fails twice.
- **Each research agent reads only two docs** — `product-copy.md` (it is writing prose) and
  `evidence-and-freshness.md` (it is earning the date), plus `identity.md` for a tier/family slug.
  The reading list is multiplied by the batch size, so do not send the orchestration docs. Preflight
  computes the recorded dimensions and hands them over.
- **Fetch only through** `uv run python -m build.fetch_source --body-dir <scratch> <url>`, so the
  digest is one the weekly sampled re-fetch can confirm.

## Four things that belong to the agent, not the orchestrator
Each is a defect the sweep actually hit:

- **Namespace scratch files per agent, `<category>/<product>/`.** The scratchpad is shared; two
  passes had a fetch log overwritten mid-run by a sibling using the same filename. A directory
  named for the *category* is not enough — every product agent in the category still shares it, so
  the scratch path has to descend to the product.
- **Touch only your own category's files** — `sources/{scores,products}/<member>.yaml`. Never
  `docs/`, `tests/`, `.github/`, `build/notebook_data.json`, `notebooks/`, or another category.
- **Escalate anything that moves a level.** The agent that finds a moved `score`/`level`/`class`/
  `reach`, a new or refused artifact, or vanished evidence is not the one who applies it. Escalate
  and carry on — one product does not block the other twenty. A batch escalating nothing is more
  suspicious than one escalating five.
- **Entity moved, not evidence, is a curation call.** A product that merged, split into tiers, or
  was renamed is `docs/reference/identity.md` work, not a re-read. Record it and leave the slug.

## Apply, then gate
**The deterministic applier is the only writer, and it touches only the packet's product.** A
script, never an agent and never by hand — the YAML does not round-trip. It parses the auditor's
replacement text (which arrives in three shapes: a bare value, a `description: ...` line, or a
fragment carrying both prose fields) and edits via `build/components.py`. A held or failed axis is
not dated; it goes to `sources/verification_queue.yaml` with the reason that would settle it. Then
run the canonical gate list from `docs/workflows/refresh-category.md`, and
run `tests/test_components.py` before the full suite (it catches the fragment-nested-as-value bug
that shipped on seven products once). One PR per category, prose and scores together, every moved
score itemized against its evidence. Then stop — a human merges.

## Boundaries
Read-only on the warehouse. Edits `sources/` only, only for the named category. Does not clear
deferrals, split a type, restructure `components`, or change a ladder — each is its own project.

## Related
- `skills/build-rubric/SKILL.md` — when a category's values are not ladderable
- `skills/refresh-all-categories/SKILL.md` — the driver that picks the next category
