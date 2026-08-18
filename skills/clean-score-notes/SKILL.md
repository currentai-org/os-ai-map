---
name: clean-score-notes
description: Use when clearing the verification log out of score notes — the "Re-read 2026-08-13 - the source still says X. No change." prose that renders on the public product page. One product per unit of work, edited by hand, in os-ai-map.
---

# Clean score notes

A score `note` says why the score is what it is. It is **not** the log of who checked it and
when — that is `last_verified`, `sources[].accessed` and `sources[].content_sha256`, all of
which are already structured, and all of which the product page already renders as
`Verified <date>`. The prose restates them into the copy a visitor reads.

Measured 2026-08-18: **1,035 of 1,416 notes across 446 of 472 score files**, 370,810 characters,
**44% of all note prose**. See issue #322 for the full audit.

## Trigger
A category's score notes still carry verification prose. Run one category per pass. For a single
product that needs a *score* change, this is the wrong door — use `update-product`.

## Required reading
- `docs/reference/evidence-and-freshness.md` — what `last_verified` means, and who may write it.
  This skill may not.
- `docs/schemas/score.schema.json` — the three `note` descriptions, which are the contract.
- `docs/reference/product-copy.md` — the prose spec for the surrounding record.

## One objective, and a log for everything else

**The objective is the verification prose.** Not better notes, not corrected scores, not a tidier
argument. A pass that stops to fix what it finds never finishes, and the corpus keeps shipping
the log in the meantime.

**Everything a pass may not fix, it writes down.** A note whose surviving prose contradicts its
own score, a fact that looks stale, an argument that no longer matches the product — record it
with slug, axis and one sentence, and move on. The log lands on the PR; each entry is somebody's
later `update-product`.

**A score file must still hold everything needed to settle a disagreement afterwards.** That is
the constraint that decides every marginal call: if deleting a clause would leave a reader unable
to reconstruct why the score is what it is, the clause is durable and it stays — reworded into
the present tense, not deleted.

**The verification history is not discarded, it is relocated to where it already lived.** The
scoring history is the git history of the score file — `git log -p --follow
sources/scores/<slug>.yaml` — which is complete, dated by commit, and needs no upkeep. A pass
removes the narrative from the note precisely because the payload publishes `note` and `sources`
verbatim, so anything written into a note ships to the public product page. The mechanics stay
readable by the agents that need them and stop being product copy.

## This is hand work, not a regex

A scripted strip is wrong for a third of the corpus. Classify every tail before touching it:

| Bucket | Share | What to do |
|---|---:|---|
| **Pure log** — "still says X … No change." | 68% | Delete the tail. |
| **Durable detail in log framing** — a price, a version, a percentage | 29% | Move the fact into the note body in the present tense; delete the framing. |
| **Record-changing** — a claim withdrawn, a band revised | 1% | Keep only the durable claim ("no independent comparison supports this band"); delete the narrative. |

The middle bucket is why this is manual. "Re-read 2026-08-13 — still in stock at Seeed, now
listed at $70.00 rather than $71.99" carries a live fact wearing a log's clothes. Deleting the
sentence loses the price; keeping it dates the note.

## The unit of work is one product file

Not one axis. A curator reading a record needs all three notes at once, because the same tail
often repeats an argument the axis above already made.

1. Read the whole score file, including `last_verified` and every `sources[].shows`.
2. In each axis note, find the tail: the first `Re-read` / `Re-checked` / `Re-fetched` to the end.
3. Classify it against the table above, and act.
4. **Re-read what remains, cold.** Does it explain the score to someone who has not seen the
   sources? If it now reads thin, that is a finding, not a cosmetic problem: the note was never
   doing its job and the tail was hiding it. Write the missing rationale from the sources already
   cited in the record. Do not fetch anything.
5. Apply the same rule to `sources[].shows` — 96 carry the log too, 45 of them in
   `evaluation_code`.
6. Update the category's count in the backlog ledger.

## What a pass may never do

- **Change a score.** If cleaning reveals the score is wrong, stop and file it. That is evidence
  work with its own re-read and its own date, which is `update-product`.
- **Touch `last_verified`.** This is a prose edit. Nothing here re-verifies anything, so nothing
  here earns a date — `docs/reference/evidence-and-freshness.md` is explicit about who may write
  it, and a prose pass is not on the list.
- **Remove a source, or edit `accessed`, `http_status`, `content_sha256`.** Only `shows` prose.
- **Leave a note that no longer stands alone.** The tail was often carrying the whole argument.

## Order and size

**One category per agent, all categories into one PR.** The category is the unit because a
reviewer reads it as one editorial voice; the single PR is because this is one mechanical change
with one contract behind it, and sixteen PRs would take sixteen reviews of the same rule.

Worst-first by note count:

| category | files | notes | `shows` |
|---|---:|---:|---:|
| orchestration_agents | 51 | 120 | 4 |
| ui_api | 43 | 118 | 2 |
| finetuned_chat | 39 | 100 | 4 |
| training_synthetic_datasets | 38 | 76 | 0 |
| evaluation_code | 26 | 75 | 45 |
| agent_tools_protocols | 32 | 69 | 3 |
| telemetry_observability | 26 | 67 | 4 |
| deployment | 27 | 65 | 3 |
| ml_frameworks | 22 | 63 | 0 |
| safeguards | 26 | 60 | 5 |
| benchmark_eval_data | 27 | 58 | 9 |
| base_pretrained | 27 | 56 | 11 |
| dataset_processing_tools | 21 | 42 | 0 |
| edge_hardware | 19 | 39 | 0 |
| finetuning_code | 12 | 15 | 1 |
| inference_code | 10 | 12 | 5 |

**Cleared 2026-08-18**, and the score-history class with it (#323): the dated changelog
sentences that sat inside the arguments - "RE-BANDED", "Class corrected from open_core on
2026-07-30", "DECLARED 2026-08-14" - are gone from all 117 records that carried them.

**A note may no longer state a date.** That is the rule now, guarded by
`test_no_note_states_a_date_unless_it_is_a_product_fact` against an allowlist of 26 axes whose
dates are facts about the product or the source rather than about the reading. `sources[].shows`
is not covered: it quotes the source, and sources carry dates honestly.

**What no guard reaches:** undated chronology - "Recorded level was 3", "Corrected from level 4",
"The note this replaces..." - in roughly 80 notes. No date, no marker, same defect. Only reading
finds it.

**Cleared 2026-08-18 (original re-read table).** That table is the state the sweep started from, kept because it is the
only record of what was there — the corpus now holds zero, and the guard below is strict. A
future pass over a different prose defect should measure its own table the same way rather than
work from a vague sense of the scale.

Three hazards the sweep hit, all of which cost a repair and none of which was obvious up front:

- **A marker mid-sentence.** "...no source was re-read." is not a tail. Cutting there truncates
  the note and the cut looks clean, because the text after it starts with the marker. Match only
  sentence-initial markers, and audit by re-reading what survived, not by checking the cut point.
- **A verb list is not a rule.** `Re-derived` was not in the marker set and survived 23 times
  until an agent noticed. The guard now matches the shape of the thing, not a vocabulary.
- **`set_source` addresses by URL and takes the first match.** An axis citing the same URL twice
  has an unreachable second entry, and the reparse assertion still passes because the expected
  document is built from that same first index. Address by index where a URL repeats.

## Validation

```bash
uv run python -m build.validate
uv run pytest tests/test_score_notes.py     # the ratchet: measured must equal recorded
uv run pytest
```

The guard is strict rather than a ratchet, because the pass clears the whole corpus at once: no
`note` and no `sources[].shows` may carry a re-read marker. A ratchet with an allowlist would be
right for an incremental cleanup and is wrong here — there is no backlog left to name.

Edits go through `build/components.py` (`set_field`, `set_source`), never a load-modify-dump. It
reparses after every edit and asserts the document is unchanged apart from the one field, which
is what catches a spliced tail landing in a neighbouring key. It caught exactly that on
`agent2agent-protocol`, whose note carries an embedded paragraph break the renderer cannot
round-trip; a handful of records like it are hand-edited.

## Stop and escalate
- A note's argument turns out to be wrong, not just badly framed → `update-product`.
- The whole category's evidence is stale → `refresh-category`.
- The `note` contract itself needs to change → `migrate-axis`.

## Related
- Issue #322 — the audit this skill works from.
- `docs/reference/evidence-and-freshness.md` — the date's home.
- `skills/update-product/SKILL.md` — the door for anything that moves a score.
