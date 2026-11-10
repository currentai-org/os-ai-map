# Language membership review, 2026-11-10

## Scope

Step 3 of the language-specific restructure: the language classification adopted in
[`../reference/language-classification.md`](../reference/language-classification.md) (method
version 1) run against every product that declares `languages`. This is a review record. Nothing
moves on it. Each move it proposes is made, if approved, in its own PR, which rescores the product
against its destination's recipe (R-2026-10-30-d).

The rule (R-2026-10-30-d, R-2026-11-10-j):

1. **The purpose test comes first.** A dataset belongs in a language category when it is defined
   by the languages it serves rather than by its task or scale.
2. **The language half.** A product is **in** when any of its target languages is robustly below
   the line, and **out** when every target language is robustly at or above it. There is no
   majority rule. The line is `high`: a language is below it when both ends of its class are `mid`,
   `low` or `very_low`, and at or above it when both ends are `high`.
3. **Otherwise the purpose test decides alone.**

Pivot languages declared in an evaluation set's `capability.pivot_languages` are not targets.

The classes come from `currentai.language_representation.classification` as built on 2026-11-10
(method version 1.0.0, code table 20261015). The language half is computed by
`uv run python -m build.language_representation --membership-review`. Only classes for codes the
map's products declare appear here (R-2026-11-10-s).

## Result

| Category | Products declaring languages | Language half `in` | `out` | Purpose test alone |
|---|---|---|---|---|
| `language_specific_datasets` | 75 | 75 | 0 | 0 |
| `language_specific_eval_sets` | 22 | 20 | 1 (IndoNLU) | 1 (TurkishMMLU) |
| `training_synthetic_datasets` | 35 | 14 | 21 | 0 |
| `benchmark_eval_data` | 27 | 0 | 27 | 0 |
| `robotics_embodied` | 3 | 0 | 3 | 0 |

**One published product would move: IndoNLU.** Every other product either stays where it is or
was already outside the language categories for its purpose, not its language.

## Proposed moves

### IndoNLU: out of `language_specific_eval_sets`

- **Target languages:** Indonesian (`ind`) only.
- **Class:** `high` at both ends.
  - FineWeb-2 has 60.3 billion words without the Bible share, which is band A.
  - CLD2 measures it at 1.06 to 1.16% of pages, also band A.
- **Language half:** `out`, because every target language is at or above the line.
- **Purpose test:** passes. IndoNLU is built for Indonesian. The language half decides, and it puts
  IndoNLU out.
- **Destination:** `benchmark_eval_data`, beside the other evaluation sets for languages above the
  line.
- **Score and peer changes the move would carry:**
  - **Capability.** It is null today, unresolved because its item provenance is unknown
    (R-2026-11-08-a). `benchmark_eval_data` abstains on capability (`basis: n/a`), so it stays null
    with basis `n/a`. The depth-ladder companion figures leave the record, because `build.validate`
    recomputes the ladder only inside `language_specific_eval_sets`.
  - **Openness.** It is 2, `gated`. It is re-derived under `benchmark_eval_data`'s recipe with
    `build.check_rubric`, which reads the same shared dataset ladder.
  - **Adoption.** It is null today and stays null.
  - **Peers.** No product names IndoNLU as `relative_to`, so nothing is re-pointed.
- **Effect on the category.** `language_specific_eval_sets` falls from 22 sets to 21. Its stage
  count is recomputed.

### TurkishMMLU: stays, on the purpose test

- **Target languages:** Turkish (`tur`) only.
- **Class:** `unresolved`, from high to mid.
  - FineWeb-2 puts Turkish in band B, at 41.9 billion words.
  - CLD2 puts it in band A, at 1.14% of pages.
  - That is the one band disagreement between the two web-text sources among the large languages.
- **Language half:** neither in nor out.
- **Purpose test:** it decides alone, and it passes, because TurkishMMLU is built from Turkish
  curriculum exams.
- **Proposal:** TurkishMMLU stays, and no score changes. The record notes that its membership rests
  on the purpose test, and it is re-read at each quarterly refresh.

## Language half passes, purpose test fails: no move

These 14 `training_synthetic_datasets` products include at least one target language below the
line. Each is defined by its task or scale, not by the languages it serves, so the purpose test
keeps it where it is. This matches the category notes, which already route general multilingual
crawls and collections here.

| Product | Targets | Why the purpose test fails |
|---|---|---|
| `fineweb-2` | 1,807 | General multilingual web crawl, defined by scale |
| `madlad-400` | 400 | General multilingual crawl |
| `wikipedia` | 318 | Encyclopedia dumps across every edition |
| `culturax` | 164 | General multilingual crawl |
| `oscar-2301` | 149 | General multilingual crawl |
| `aya-collection` | 115 | Multilingual instruction collection; the category note names it |
| `c4` | 101 | General web crawl (mC4 languages) |
| `wildchat-1m` | 73 | Chat logs, in whatever language users wrote |
| `dolci` | 70 | Post-training mixture, defined by task |
| `tulu-3-sft-mixture` | 70 | Post-training mixture, defined by task |
| `oasst1` | 35 | Crowd-sourced assistant conversations, defined by task |
| `nemotron-cc` | 16 | General web crawl |
| `common-corpus` | 13 | General open-licensed corpus, defined by license and scale |
| `synth` | 8 | Synthetic reasoning corpus, defined by task |

The full per-language breakdown is the output of the command above.

## Unpublished seeds the new line affects

Eleven registry seeds were routed out on 2026-09-23 as "language-specific but not low-resource".
They are not on any roster, so nothing moves. The new line changes the language half for one of
them:

| Seed | Registry | Language | Class | Language half | Note |
|---|---|---|---|---|---|
| `kmmlu` | `benchmark_eval_data` | Korean | mid | **in** | Now eligible for `language_specific_eval_sets`. Adding it goes through `add-product`, with per-language depth evidence for the ladder. |
| `tmmlu-plus` | `benchmark_eval_data` | Mandarin, Traditional script | high | out | Stays routed out |
| `cmmlu` | `benchmark_eval_data` | Mandarin | high | out | Stays routed out |
| `jmmlu` | `benchmark_eval_data` | Japanese | high | out | Stays routed out |
| `chinesewebtext` | `training_synthetic_datasets` | Chinese | high | out | Stays routed out |
| `cci3-hq` | `training_synthetic_datasets` | Chinese | high | out | Stays routed out |
| `map-cc` | `training_synthetic_datasets` | Chinese | high | out | Stays routed out |
| `carolina-corpus` | `training_synthetic_datasets` | Portuguese | high | out | Stays routed out |
| `choclo` | `benchmark_eval_data` | Spanish | high | out | Check for Indigenous-language content before confirming |
| `trueque-benchmark` | `benchmark_eval_data` | Spanish | high | out | Check for Indigenous-language content before confirming |
| `latamgpt-corpus` | `training_synthetic_datasets` | Spanish, Portuguese | high | out | Check for Indigenous-language content before confirming. Any such content would make the language half `in`. |

The seeds carry no `languages` field. The languages above come from each seed's own card, and are
confirmed when a seed is added.

## SOLD's placement

SOLD, the Sinhala Offensive Language Dataset, declares Sinhala (`sin`), whose class is below the
line, so the language half keeps it in a language category. Which of the two categories is not a
language question. The evaluation-set boundary test in `language_specific_eval_sets.yaml` decides
it, and that test called SOLD a corpus: its card is titled as a benchmark, but its paper is
motivated by training data. R-2026-11-08-g froze that placement until the classification landed.

**Proposal:** SOLD stays in `language_specific_datasets`. The classification gives no reason to
reopen the boundary call, so its score stays as it is (capability 3, R-2026-11-08-c).

## Text that changes with the moves

`language_specific_datasets.yaml`'s comment names "Chinese, Japanese, Korean, Spanish or
Portuguese" as languages that fail the language test. Under the classification, Korean is below the
line. The membership PR replaces the list with a pointer to the reference and the classification
table, so the comment does not restate a rule that now lives elsewhere.

## Decisions for the maintainer

1. **IndoNLU:** move to `benchmark_eval_data`, with the score changes above?
2. **TurkishMMLU:** stay on the purpose test, re-read quarterly?
3. **SOLD:** stay in `language_specific_datasets`?
4. **KMMLU:** add it to `language_specific_eval_sets` through `add-product`, as separate work?
5. **The three Latin American seeds:** check them for Indigenous-language content before confirming
   that they stay out?
