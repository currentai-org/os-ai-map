---
name: verify-product
description: Use when an editor wants to verify or refresh an existing product's prose in the AI Stack Map — its description and comments — against primary sources, applying a consistent format and tone. Updates only the product file; does not touch scores or last_verified.
---

# Verify a Product

Re-checks and rewrites the two hand-authored prose fields of
`sources/products/<slug>.yaml` — `description` and `comments` — against primary sources,
applying the house style. This is a **prose** refresh, not a score re-check: it never
writes `last_verified`, never edits `sources/scores/<slug>.yaml`, and never adjusts an
openness/adoption/capability value.

> Read `docs/guides/product-info.md` first — it is the normative style/format/tone spec
> and the source of the rules below. This skill is the procedure; the guide is the
> authority.

## Steps

1. **Locate the product**: `sources/products/<slug>.yaml`. Note its `type` and its
   artifact URLs (`github`, `huggingface_model`, `huggingface_dataset`, `pypi`, `npm`,
   `crates`, `go`, `arxiv`).
2. **Read the PRIMARY sources.** Fetch the product's own artifact URLs plus the vendor
   blog / registry. Never refresh from memory or a secondary summary. If a cited URL 404s
   or has moved, that is a finding — note it; do not paper over it.
3. **Re-derive the checkable facts:**
   - license — **read the LICENSE body**, not the GitHub classifier (a custom copyright
     line makes a genuine MIT/Apache repo report `NOASSERTION`); make the OSI / not-OSI
     call (Gemma, Llama Community, BSL 1.1, fair-code are all NOT OSI);
   - what it is / does / bundles, and ownership + hosting;
   - lifecycle state — archived, maintenance mode, superseded;
   - the current release, to confirm the project is alive and that nothing moved a score.
     Read it; do not write it into prose (see step 5).
4. **Rewrite `description`** to the guide's format only if something material changed:
   2–4 sentences (~35–70 words), lead with the product doing something, present tense,
   neutral register, no marketing cadence, no unsourced superlatives. Leave it untouched
   if nothing moved. **Strip any hardcoded star / download / contributor count** — those
   go stale with no freshness gate; the artifact links and the `adoption` axis carry the
   actuals (see the guide's "Volatile facts" section). This applies even when nothing
   else moved: removing a stale count IS a valid reason to edit.
5. **Update `comments`:** correct the license and caveat clauses. **Strip any "latest /
   current version" clause** — the next release makes it wrong and nothing will notice.
   Keep a version only when it is the entry's identity (a named model release), terminal
   (the project is archived), or a statement of absence ("no tagged releases"). Then
   set the verification line to the canonical form:
   ```
   Verified <YYYY-MM-DD> via <source>.
   ```
   ISO date (today's), `<source>` naming what you read (`primary sources`, `HF model
   card`, `GitHub`, `PyPI`, `vendor docs`, `LICENSE body`). Capital V, one line, at the end.
6. **American English** throughout — `license`, not `licence`; `behavior`, `labeled`.
7. **Validate:** `uv run python -m build.validate` must print `0 error(s)`.
8. Rebuild + preview, then open a PR. Preview only: do not commit the regenerated
   `build/notebook_data.json` or `notebooks/ai-stack-map.py` (bot-owned; CI blocks
   hand-edits).

## When a re-read moves a score

If the primary source shows something that changes an **openness / adoption / capability**
value — a relicense, weights pulled, a dataset newly gated, an OSI call that was wrong —
**stop.** That is a score change, not a prose edit.

- Do NOT edit `sources/scores/<slug>.yaml` from here, and do NOT write `last_verified`.
- Record the finding (in the PR description, or as a note), and hand off to the flow in
  `docs/guides/verification.md`, which is gated and evidence-attributed.

The `comments` verification line is editorial provenance for the *prose*; it is not a
freshness date and earns no `last_verified`. Keeping these separate is the whole point
(see `freshness.md`).

## Verifying in batches

For many products, drive research with parallel agents (one per product, each reading that
product's own primary sources), then apply the edits with a small script that rewrites only
the `description` and `comments` keys with
`yaml.safe_dump(..., sort_keys=False, allow_unicode=True)` — preserving every other field
byte-for-byte. Run `build.validate` after each batch, not just at the end. A plausible
release that cannot be confirmed against any primary source is SKIPPED, not guessed.

## Boundaries

- Edits `sources/products/<slug>.yaml` only. Never `sources/scores/`, never `last_verified`.
- Read-only on the warehouse. No MCP, no uploads.
- Never assert a fact from memory; primary sources only.
