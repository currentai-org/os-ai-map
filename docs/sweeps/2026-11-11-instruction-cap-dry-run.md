# Instruction-data cap dry run, 2026-11-11

## Scope

This revises #951, step 5 of #948. In `language_specific_datasets`, instruction data carries no size
cap today. R-2026-10-30-c asked for one, and #951's draft applied it. The maintainer held that draft
because it dropped WangchanThaiInstruct, a 40,000-row set written entirely by people, from 4 to 2.

The hold was lifted once the language-adjusted yardsticks were adopted (R-2026-11-11-m), with one
condition: the cap must keep human-curated data distinct from generated and translated data.

This record scores four cap designs against the eleven instruction sets. **Nothing changes on it.**
No instruction-data scoring policy is approved yet. The maintainer chooses a design from this
record, and #951 then implements it. The held draft's two commits are reverted on #951's branch,
not merged.

## Why the language yardsticks do not decide this

The adopted yardsticks (R-2026-11-11-h) relax nothing here:
- Two of the eleven sets name a single language: WangchanThaiInstruct (Thai) and CIDAR (Arabic).
  Both languages have the reference profile, so neither cap relaxes.
- The other nine are multilingual, so M2 keeps them on today's caps.

The design question is provenance alone.

## Provenance classes

The maintainer's definitions (R-2026-11-11-n) turn on **who authored the instruction and the
response**, not on whether a person touched the example somewhere.

| Class | What it covers |
|---|---|
| Human-authored | People originally wrote both the instruction and the response. A substantially rewritten example counts only where the rewriting is documented. |
| Human-derived or recast | Existing human-made data turned into instructions by templates or scripts: labeled task datasets, a dictionary, parallel text. Kept identifiable, and never counted as human writing. |
| Translated | Machine-translated, whether or not people reviewed it. |
| Generated | Written by a model. |
| Unknown | The sources do not say. |

Review, approval, selection or light editing by people does not move an example out of the
translated or generated class.

## Counts by provenance

Each count comes from a primary source read on 2026-11-11: the paper, the card, or the Hugging Face
datasets server. A row marked "sum" adds parts its source states; nothing is multiplied or divided.

| Product | Total | Human-authored | Recast | Translated | Generated | Unknown | Score today |
|---|---|---|---|---|---|---|---|
| WangchanThaiInstruct | 40,000 (card) | **35,014** (paper: "All samples are human-authored") | | | | 4,986 (card rows beyond the paper's count) | 4 |
| Inkuba-Instruct | 211.58M (card, sum) | 0 | all | | | | 4 |
| Cendol Collection | 42,989,754 (sum of v1 and v2) | 0 verified | 42,758,699 | 75,055 | | 156,000 rows: 93,500 from 187 safety prompts and 62,500 from 125 identity prompts | 4 |
| IndicAlign | 74,854.2k (sum of the card's parts) | 0 | 74,272.2k (IndoWordNet) | 55.2k | 526.8k (Anudesh: people wrote the prompts, a model the responses) | | 2 |
| Updesh | 9.5M (paper) | 0 | | 7.32M | 2.15M | | 2 |
| SEA-Instruct | 7,196,718 (sum) | 0 | | | all | | 2 |
| WangchanX-FLAN | 3,619,450 | 12.2k, imported from WangchanThaiInstruct, not original to this set | about 2.67M | | 564k | about 381k | 3 |
| Samvaad-Hi | 101,476 | | | | | all | 2 |
| CIDAR | 10,000 | 0 verified; about 891 crawled teacher answers | | about 9,109 (reviewed by people) | | about 891 | 2 |
| African UltraChat | 55,000 | | | | | all | 2 |

Typhoon-S stays a boundary case (R-2026-10-30-b) and is not read against any cap, as in the held
draft.

How the totals reconcile with their parts:
- **Cendol Collection.** Recast 42,758,699, translated 75,055, and 93,500 safety plus 62,500
  identity rows sum exactly to the 42,989,754 total. The safety and identity rows are 187 and 125
  prompts, repeated 500 times. Their authorship is not established, so they are unknown.
- **IndicAlign.** The card's component table sums to 74,854.2k: 74,272.2k recast, 55.2k
  translated and 526.8k generated. The paper's "74.7 million" is that total rounded. The card
  gives Anudesh as 36.8k and the paper's Table 7 as 43.3k; the card's figure is used.
- **WangchanX-FLAN.** Its card states 3,619,450 rows. Its source table, rounded to thousands, sums
  to about 3,631.9k, and that rounding is the whole difference.
- **WangchanThaiInstruct.** The paper verifies 35,014 pairs, and the card's release has 40,000. The
  4,986 rows beyond the paper are unknown until reconciled.

## The anchors

Each cap compares a product against the largest open English set of its kind, one order of
magnitude per step, as R-2026-10-30-c set.

- **General-scale track.** It counts every eligible example, of any provenance, human-authored
  ones included. The anchor is NVIDIA's Nemotron-Post-Training-Dataset-v1, which states a total of
  25,659,642 examples. Steps:
  - 5 needs 10M;
  - 4 needs 1M;
  - 3 needs 100k;
  - 2 needs 10k.

  The held draft cited Llama-Nemotron v1.1 at "about 33.0M". Its card states no total, so that
  figure is a sum. The steps are the same either way.
- **Human-authored track.** It counts only pairs whose instruction and response people verifiably
  wrote. The anchor is databricks-dolly-15k: 15,011 examples, people wrote both sides, and it is
  openly licensed. It is a deliberately built, directly comparable reference, not the largest
  human-written set. OASST2 is not interchangeable with it: its 70,642 trees include unfinished and
  rejected ones, and its 13,854 ready trees hold 135,174 messages, not independent pairs. Steps:
  - 5 needs 10k;
  - 4 needs 1k;
  - 3 needs 100;
  - 2 needs 10.

  Larger human-written sets exist only as mined question-and-answer, such as Stack Exchange's 10.7M
  answers. That anchor is shown below as a sensitivity.

## The four options

A capped band is the lower of the score the rubric gives and the cap. Instruction sets carry no cap
today, so today's score is their rubric score.

| Option | Cap |
|---|---|
| **A**, the held draft | Every example counts at face value against the general-scale anchor |
| **B**, split anchors (the leading candidate) | The higher of two caps: human-authored examples against the human anchor, and all examples against the general-scale anchor |
| **C**, human-only | Only human-authored examples count, against the human anchor; a set with none caps at 1 |
| **D**, no cap | Today's rule. Provenance is judged by the rubric alone |

### Results

| Product | Today | A | B | C | D |
|---|---|---|---|---|---|
| WangchanThaiInstruct | 4 | **2** | 4 | 4 | 4 |
| Inkuba-Instruct | 4 | 4 | 4 | **1** | 4 |
| Cendol Collection | 4 | 4 | 4 | **1** | 4 |
| IndicAlign | 2 | 2 | 2 | **1** | 2 |
| Updesh | 2 | 2 | 2 | **1** | 2 |
| SEA-Instruct | 2 | 2 | 2 | **1** | 2 |
| WangchanX-FLAN | 3 | 3 | 3 | 3 | 3 |
| Samvaad-Hi | 2 | 2 | 2 | **1** | 2 |
| CIDAR | 2 | 2 | 2 | **1** | 2 |
| African UltraChat | 2 | 2 | 2 | **1** | 2 |
| **Peer relations broken** | | 8 | 0 | 8 | 0 |

| Product | Cap under B: human-authored track | Cap under B: general-scale track | Score that binds |
|---|---|---|---|
| WangchanThaiInstruct | 5 (35,014) | 2 (40,000) | the rubric's 4 |
| Inkuba-Instruct | none | 5 | the rubric's 4 |
| Cendol Collection | none verified | 5 | the rubric's 4 |
| IndicAlign | none | 5 | the rubric's 2 |
| Updesh | none | 4 | the rubric's 2 |
| SEA-Instruct | none | 4 | the rubric's 2 |
| WangchanX-FLAN | 5 (12.2k) | 4 | the rubric's 3 |
| Samvaad-Hi | none | 3 | the rubric's 2 |
| CIDAR | none verified | 2 | the rubric's 2 and the cap |
| African UltraChat | none | 2 | the rubric's 2 and the cap |

### What this shows

1. **Under split anchors, WangchanThaiInstruct keeps its 4.** Its 35,014 human-authored pairs reach
   the human anchor's top step, so the rubric, not size, sets its score.
2. **Split anchors give templated and generated collections no size advantage.**
   - Their caps come only from the general-scale track, measured against Nemotron's 25.7M
     examples.
   - Recast rows never enter the human track.
   - Today no cap binds any of them, because the rubric already places them lower than their size
     would allow.
   - The cap would bind a future set: a 30,000-example generated set reaches at most 2, while
     30,000 human-authored pairs could reach 5 if the rubric gives it.
3. **The held draft (A) penalizes exactly the human-authored set** and breaks the eight relations
   that compare against it.
4. **Human-only (C) drops eight sets**, including two documented collections with named models
   trained on them, to the lowest score. It does this because nothing they hold was written by
   people. That judges provenance twice: once in the rubric's machine-generated and recast rungs,
   and again in the cap.
5. **Split anchors and no cap give identical scores today.** The difference is that B writes the
   size rule down and keeps the human and generated counts on record.

### Sensitivities

- **Mined Q&A as the human anchor.** With Stack Exchange's 10.7M answers as the anchor, the human
  track's steps equal the general-scale track's. B then gives the same result as A: WangchanThaiInstruct
  falls to 2 and eight relations break. Mined answers were not written as instruction data, which is
  why Dolly is the proposed anchor.
- **Contested provenance items.** Counting Cendol's 187 safety prompts and CIDAR's roughly 891
  crawled answers as human-authored changes only option C: Cendol to 3 instead of 1, and CIDAR to 2
  instead of 1. A, B and D are unchanged.
- **WangchanThaiInstruct's count.** The paper's 35,014 and the card's 40,000 both clear 10k, so
  nothing moves.

## What an implementation would change, if B is chosen

- **Recipe note** in `sources/categories/language_specific_datasets.yaml`. It would state:
  - the two anchors;
  - the provenance classes;
  - that recast, translated and generated rows count only on the general-scale track;
  - that Typhoon-S stays outside the cap.
- **Ten capability records.** Each value would state its count by provenance. No score moves and no
  relation changes.
- **A ruling** recording the choice.

## Decision (2026-11-11)

The maintainer adopted option B, split anchors (R-2026-11-11-o).

- **Anchors.**
  - Human-authored track: databricks-dolly-15k. 5 needs 10,000 human-authored pairs, 4 needs 1,000,
    3 needs 100, and 2 needs 10.
  - General-scale track: Nemotron-Post-Training-Dataset-v1 at 25,659,642 examples.
- **Track names.** The tracks are named for what they count. The general-scale track counts every
  eligible example; the human-authored track counts only verified human-authored pairs. A set's
  human-authored content is kept distinct from content original to that set.
- **The contested items.**
  - Cendol's 187 safety and 125 identity prompts do not count as human-authored pairs. A paper
    saying prompts were written by hand does not establish who wrote both the prompt and the
    response.
  - CIDAR's roughly 891 teacher answers stay outside the verified count. Existing human-written
    source material is not a newly authored instruction-response pair.
  - Typhoon-S keeps its boundary exemption.
  - WangchanThaiInstruct counts its 35,014 paper-verified pairs. Its other card rows stay unknown.
  - WangchanX-FLAN's 12.2k pairs stay human-authored but are marked as imported from
    WangchanThaiInstruct.
- **Option D** stays a baseline, not policy. B is preferred because it sets reproducible ceilings
  for future sets while keeping the rubric.

The implementation is in this PR:
- the recipe note;
- the ten instruction records, whose values state their counts by provenance and whose sources
  were re-read on 2026-11-11;
- no score or peer relation changes.
