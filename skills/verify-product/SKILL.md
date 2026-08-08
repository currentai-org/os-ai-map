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

**Where this runs.** In the category sweep the prose refresh happens *inside* the score
re-read (`docs/runbooks/verification-pass.md`, Phase 4): one agent opens a product's sources
once and writes both halves from them, and one PR carries the category. This skill stays the
prose half, and the boundary below still holds — the score half follows
`docs/guides/verification.md`, which is gated and evidence-attributed. Run standalone, the
skill is unchanged.

**How far to verify.** The guide's claim-class table is the rule. Two consequences worth
having in front of you: a superlative, a corporate event, and a curator rationale clause are
**deleted or omitted, never researched**, and a claim the product's own sources do not settle
comes out of the prose rather than staying in on the grounds that it was already written.

## Steps

1. **Locate the product**: `sources/products/<slug>.yaml`. Note its `type` and its
   artifact URLs (`github`, `huggingface_model`, `huggingface_dataset`, `pypi`, `npm`,
   `crates`, `go`, `arxiv`).
2. **Read the PRIMARY sources.** Fetch the product's own artifact URLs plus the vendor
   blog / registry. Never refresh from memory or a secondary summary. If a cited URL 404s
   or has moved, that is a finding — note it; do not paper over it.
3. **Re-derive the checkable facts:**
   - what it is / does / bundles, and ownership + hosting;
   - lifecycle state — archived, maintenance mode, superseded;
   - the license — **read the LICENSE body**, not the GitHub classifier (a custom copyright
     line makes a genuine MIT/Apache repo report `NOASSERTION`); make the OSI / not-OSI
     call (Gemma, Llama Community, BSL 1.1, fair-code are all NOT OSI). Read it to check it
     against the recorded score; **do not write it into prose** (see step 5);
   - the current release, to confirm the project is alive and that nothing moved a score.
     Read it; do not write it into prose either.
4. **Rewrite `description`** to the guide's format only if something material changed:
   2–4 sentences (~35–70 words), lead with the product doing something, present tense,
   neutral register, no marketing cadence, no unsourced superlatives. Leave it untouched
   if nothing moved. **Strip any hardcoded star / download / contributor count** — those
   go stale with no freshness gate; the artifact links and the `adoption` axis carry the
   actuals (see the guide's "Volatile facts" section). This applies even when nothing
   else moved: removing a stale count IS a valid reason to edit.

   `description` is the **load-bearing** field: everything a reader needs about the product
   lives here, including who builds or stewards it. Avoid three sentences in a row opening
   "It …" — recast one around its real subject.

   **Strip the curator rationale clause.** Find it with
   `\b(picked|chosen|included|selected)\s+(because|when|by|for|as|if)\b`. A description
   describes; why the map picked the product up is not a product fact. Work in this order:
   salvage the concrete facts trapped inside the clause and move them into the description
   proper ("powers the Hugging Face Open LLM Leaderboard"), drop the counts, funding and
   superlatives that have collected there, then delete the recommendation framing. Like a
   stale count, this is a valid reason to edit with nothing else moving.

   **Strip corporate events** — acquired, raised, IPO'd. Keep one only when it establishes who
   ships the product today ("Predibase, now part of Rubrik"); never as company history, and
   never funding, which is a proxy for the `adoption` axis.
5. **Rewrite `comments` as a footnote.** It is not a second description. Anything about the
   *product* — what it does, who builds it, what it runs on — moves to `description`; what
   stays is about *the reading*: an evidence gap, a judgment call a score rests on, or
   something in a source that would mislead the next editor. Most products need only the
   verification line, and that alone is a complete entry — do not pad.

   **Strip any "latest / current version" clause** — the next release makes it wrong and
   nothing will notice. Keep a version only when it is the entry's identity (a named model
   release), terminal (the project is archived), or a statement of absence ("no tagged
   releases"). **Strip any license restatement** — the license is `openness.components` in
   the score file, where it carries evidence and a gate; a second copy in prose only drifts.
   Then set the verification line to the canonical form:
   ```
   Verified <YYYY-MM-DD> via <source>.
   ```
   ISO date (today's). `<source>` names **a document someone could reopen** — `GitHub`,
   `PyPI`, `the LICENSE body`, `the HF model card`, `the AWS Neuron documentation`. Never a
   method: `web search` and a bare `primary sources` say how you looked, not what settled
   it. If a search led you to a vendor page, cite the vendor page. Capital V, one line, last.
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
product's own primary sources), then apply the edits with a small script.

**Do not load-modify-dump the whole file.** These YAMLs are hand-wrapped and do not
round-trip: no single `yaml.dump` width reproduces them, so a whole-document rewrite
rewraps every plain scalar in the file and buries a two-field edit in a corpus-wide diff.
Splice the one key instead — take the lines before it, emit just that key, and keep the
rest byte-for-byte:

```python
lines = path.read_text().splitlines(keepends=True)
i = next(n for n, l in enumerate(lines) if l.startswith('comments:'))
block = yaml.dump({'comments': new_text}, width=105, allow_unicode=True,
                  default_flow_style=False, sort_keys=False)
path.write_text(''.join(lines[:i]) + block)   # comments is the last key
```

Run `build.validate` after each batch, not just at the end. A plausible release that cannot
be confirmed against any primary source is SKIPPED, not guessed.

## Boundaries

- Edits `sources/products/<slug>.yaml` only. Never `sources/scores/`, never `last_verified`.
- Read-only on the warehouse. No MCP, no uploads.
- Never assert a fact from memory; primary sources only.
