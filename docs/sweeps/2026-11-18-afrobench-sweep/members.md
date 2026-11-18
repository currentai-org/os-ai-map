# AfroBench's separately published members, 2026-11-18

Part of #1098, alongside the coverage and provenance pass in this directory's README (#1102). It
applies R-2026-11-18-d, the per-suite ruling under R-2026-11-18-a, which applied R-2026-10-30-e and
-f to SEA-HELM's members in #1094: a member a suite also publishes on its own qualifies for a row of
its own, linked by `lineage.part_of`, if it meets the category's inclusion criteria. The suite and
its members count once toward the stage, and shared evidence never corroborates. No rule changed.

## The tests applied

- **On the map already?** Every candidate was searched across `sources/products/` and
  `sources/registry/`, by name, alias and repository. Only AfriHate has a row, in
  `language_specific_datasets`.
- **Language.** Every target language of every candidate is below the high class at both ends in
  `currentai.language_representation.classification` (read on 2026-11-18): very low for most,
  unresolved between low or mid and very low for Hausa, Somali and Swahili, low for Moroccan Arabic,
  and unknown for Vai. English, French and Portuguese, which are high, appear only as pivots or
  alongside African targets.
- **Kind** (R-2026-10-30-b), by what the set's paper or card says it is for. A benchmark or a
  shared-task test belongs in `language_specific_eval_sets`, training splits or not. A labeled set
  published for training is a corpus and goes in `language_specific_datasets`.

## Added to `language_specific_eval_sets`

| Row | Repository | Openness | Adoption (held) | Capability (depth ladder) |
|---|---|---|---|---|
| `afrimmlu` | `masakhane/afrimmlu` | 5, open (Apache 2.0, ungated) | 2 | 3: 500 translated questions in each of 16 languages |
| `afrixnli` | `masakhane/afrixnli` | 5, open | 2 | 3: 600 translated pairs in 15 languages; Swahili is XNLI's, translator not clearly stated, unmeasured |
| `afrimgsm` | `masakhane/afrimgsm` | 5, open | 2 | 2: 250 translated problems in 16 languages; Swahili is MGSM's, so not the set's own, and sits at 1 |
| `injongo-intent` | `masakhane/InjongoIntent` | 5, open | 2 | 3: 640 natively written requests in each of 16 languages (638 in Wolof) |
| `uhura-arc-easy` | `masakhane/uhura-arc-easy` | 5, open (MIT) | 1 | 3: 452 to 509 translated questions in five languages, 300 in Zulu |
| `naijarc` | `Davlan/NaijaRC` | 2, restricted (CC BY-NC 4.0) | 1 | unresolved: no source says the exam passages were written in Hausa, Igbo or Yoruba |

Why each passes the kind test:
- **IrokoBench**: its abstract calls it "a human-translated benchmark dataset", and each card opens
  "an evaluation dataset".
- **InjongoIntent**: "a multicultural, open-source benchmark dataset".
- **Uhura**: "Uhura: A Benchmark for Evaluating Scientific Question Answering and Truthfulness".
- **NaijaRC**: its authors build it to evaluate models without training on them, and its Hausa and
  Igbo splits are test-only.

IrokoBench is one paper with three repositories and three cards. It gets three rows, one per card,
because AfroBench's coverage record already names AfriMMLU, AfriXNLI and AfriMGSM as separate
components. A row's own component is its own slug, so each member row and AfroBench's import of it
read the same lineage record. That is the strongest form of "shares the suite's collections and
effort": the two cannot corroborate each other because they are the same component. Uhura's row
covers its ARC-Easy half, which is what AfroBench runs and what `masakhane/uhura-arc-easy` holds.

AfriMGSM's own-slug claim withdraws ownership in Swahili under R-2026-11-03-i, the INCLUDE
precedent. IrokoBench says its Swahili problems are MGSM's, and MGSM's paper says paid professional
translators made them. The Swahili items count as an import with nothing independent beside them, so
Swahili sits at 1. The 16 languages IrokoBench translated itself are each at 2.

`sources/lineage.yaml` gains:
- a NaijaRC record;
- Swahili overrides on AfriXNLI (XNLI's translation effort) and AfriMGSM (MGSM's).

The overrides move no band: AfroBench's Swahili stays at 5 through OpenAI's MMMLU.

AfriHate already had a row in `language_specific_datasets`, placed there as a corpus by
R-2026-10-30-b. AfroBench runs it as its hate-speech task, so the row now names
`lineage.part_of: [afrobench]`. A suite in another category groups nothing, so neither stage
changes.

**Stage.** The eval-set category stays at stage 2. None of the new rows leads the category: the
best is 2.7, from adoption 2 and capability 3, and AfroBench and its members would count as one
group anyway.

**Shared repositories.** AfroBench declares these member repositories with `not_primary_channel`,
because their downloads are not runs of the suite. The downloads therefore count on the member
rows and not on AfroBench. That matches what AfroBench's own adoption note already says.

## Not added

| Candidate | Why not |
|---|---|
| MasakhaNEWS | Passes both tests (its paper calls it "a new benchmark dataset for news topic classification"), but its license, AFL-3.0, maps to no tier on the dataset ladder, so `check_rubric` cannot score its openness. Its capability would be unresolved for unknown provenance. Waits on a license reading. |
| AfriSenti | Passes both tests (a "Twitter Sentiment Analysis Benchmark" used for a SemEval shared task), but CC BY-NC-SA 2.0 maps to no tier either; only the 3.0 and 4.0 spellings are on the ladder. Its capability would be unresolved too. Waits on a license reading. |
| AfriQA | Kind is unclear: its paper presents "the first cross-lingual QA dataset" with training, development and test splits for retrieval and reading systems, and states no evaluation-only purpose. Its passages and answers are English or French, which #1102 raises as a separate question. |
| MAFAND-MT | A close call on kind, like SOLD and AfriDocMT. The card calls it "the largest MT benchmark for African languages in the news domain". The paper presents "our newly translated news corpus" built to fine-tune translation models from "a few thousand" sentences. On the AfriDocMT precedent it is a corpus and belongs in `language_specific_datasets`, which scores capability differently. Left for its own pass. |
| SALT | A "multi-way parallel text and speech corpus ... to support machine translation": a corpus, for `language_specific_datasets`. Left for its own pass. Its translators are also not established (see the README). |
| MasakhaPOS, MasakhaNER | Labeled datasets published for training and transfer, so corpora by the kind test. Tagging has no measurement model in either category. Left for a corpus pass. AfroBench runs MasakhaNER-X, XTREME-UP's reformatting of MasakhaNER, which has no release of its own outside XTREME-UP. |
| NollySenti | Its paper creates the set to study transfer learning and machine translation for sentiment classification, with training splits. That makes it a corpus by the kind test; a close call. |
| NTREX African | Masakhane's re-host of NTREX-128's African languages, not a separate publication. NTREX-128 itself is a global set that a suite borrows, which would keep a row of its own. That is an add-product question outside this suite pass. |
| AfriADR | Published only as part of AfroBench (`masakhane/diacritics-restoration`, no paper of its own), so it is the suite's own task, not a member. |

## Holds

Each new row's adoption level was read by hand from Hugging Face downloads. Each is held in
`sources/verification_queue.yaml` until the weekly reconciliation measures it, as in #1094. No
licensing conflict came up among the rows added: every card and API tag agree.

## The ruling cited

The maintainer ruled **R-2026-11-18-d**, one named membership ruling per suite under the general rule
in R-2026-11-18-a: the six rows join `language_specific_eval_sets` linked to AfroBench, and AfriHate is
linked to it. `tests/test_depth_ladder.py` `ADDED`, `docs/reference/capability.md`, the category
comment and the changelog cite it.
