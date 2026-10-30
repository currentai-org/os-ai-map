# Language-specific datasets: structure and scoring review, 2026-10-30

This brief reviews how `language_specific_datasets` compares regional datasets with global ones such
as FLORES+, taking the Southeast Asian rows (SEA-PILE, SEA-Instruct, SEA-HELM) as the worked
example.

It evaluates and recommends. It changes no score, roster, recipe or category. Every change it
proposes waits on a ruling listed in [Decisions](#decisions), and lands in its own PR through the
workflow named for it. Like the other records in `docs/briefs/`, it describes the corpus on the date
above and gets refreshed by a new brief, not edited. Map-side claims cite files in `sources/` on
`main` at the same date.

## The short answer

Split the category by **kind of dataset**, not by **global versus regional**: one category for
language-specific corpora and one for language-targeted evaluation sets. That removes the size-cap
asymmetry (finding 1) for evaluation sets, but not for instruction data, which needs its own cap.
The bundling rule (finding 5) is independent of the split and has to be made symmetric either way.
The `languages` field that #684 added makes the rest feasible: a graded rule for "underrepresented"
(finding 7), then a per-language depth rung for evaluation sets (finding 4), then the adoption
question (finding 6).

## The findings

The overall score is `0.3 · adoption + 0.7 · capability` (`docs/reference/gap-analysis.md`, with the
category's `weights`).

| Product | Openness | Adoption | Capability | Overall |
|---|---|---|---|---|
| `flores-plus` | 3 | 3 | 5 | 4.4 |
| `sea-helm` | 3 | 3 | 5 | 4.4 |
| `sea-pile` | 5 | 2 | 4, size-capped | 3.4 |
| `seacrowd` | 4 | 1 | 3, `relative_to: sea-helm` | 2.4 |
| `sea-instruct` | 3 | 1 | 2, `relative_to: wangchan-thai-instruct` | 1.7 |

1. **The size caps are not applied evenly.** The recipe caps pretraining text, speech and parallel
   text against the largest English and Chinese datasets of the same kind, but exempts evaluation
   sets, instruction data, task annotations and the SEACrowd hub. All six products at 5 are
   evaluation sets (`flores-plus`, `fleurs`, `belebele`, `afrobench`, `sea-helm`, `arabicmmlu`). A
   set of about 2,000 sentences per language can reach 5. SEA-PILE, at about 120 billion tokens the
   largest open corpus for its region, cannot. The same exemption lets uncapped instruction sets
   (`wangchan-thai-instruct`, `cendol-collection`, `inkuba-instruct`, all at 4) sit level with
   capped SEA-PILE.
2. **The cap yardstick measures the language as much as the dataset.** A trillion tokens of Lao or
   Khmer text may not exist. Recorded here and not acted on. A graded underrepresentation measure
   (finding 7) is the input a per-language yardstick would need, so this can be revisited once
   that measure exists.
3. **Model-written data is a lower rung, and human translation from English is not.** SEA-Instruct
   sits at 2 because its responses are model-written, compared with a Thai-only human-written set.
   FLORES+ is human translation of English Wikimedia sentences and sits at 5. The evaluation-set
   ladder (finding 4) is the place to weigh provenance.
4. **Breadth counts for more than depth.** FLORES+'s rung 5 rests partly on no other open row
   covering "the same languages" at comparable scale, which a 230-variety set meets almost by
   construction. The ladder never asks how much a set holds for any one language, or whether it
   was written in that language or translated into it.
5. **The bundling rule favors global sets.** A regional suite's members fold into the suite's row
   (NusaX and PhoMT into `seacrowd`, ten sets into `afrobench`, IndicSentiment into `indicxtreme`).
   A global set a regional suite borrows keeps its own row (FLORES+, Belebele and SIB-200 inside
   AfroBench). SEA-HELM's own task sets get no row, and the FLORES+ row is credited when other
   sets reuse its sentences.
6. **Adoption pools demand across languages.** FLORES+ downloads come from users of 230 varieties
   and the whole machine-translation field. SEA-Instruct's come from Southeast Asian users alone.
   The 0.3 weight softens this without addressing it. Hugging Face and PyPI counts also miss
   publishers' own distribution, such as the SEA-LION API and the SEA-HELM leaderboard.
7. **"Underrepresented" is an enumerated list.** Chinese, Japanese, Korean, Spanish and Portuguese
   are out and everything else is in, so Indonesian and Lao are treated alike. The seed sweep
   (`docs/sweeps/2026-09-23-language-specific-datasets.md`, open items) already asked for a rule
   that reproduces the calls rather than a list that states them.

The seed sweep also listed a structured `languages` field as an open item. That is no longer open:
#684 added ISO 639-3 `languages`, required on every product in this category (see
`docs/sweeps/2026-09-30-identity-attributes/README.md`).

## Why a kind split rather than a global/regional split

A global/regional split was considered (global or English sets, evaluation sets, other languages).
It was set aside for three reasons:

- **It adds a second hand-drawn line.** Finding 7 is already a boundary drawn by list. A "global"
  category needs another: SEACrowd covers about 1,000 languages and Belebele 122, and neither
  answer is obvious.
- **It makes the hierarchy structural.** The concern is that global sets outrank regional work. A
  category boundary between them would keep them from being compared, and would also say the map
  treats them as different classes.
- **English corpora are already elsewhere.** They are in `training_synthetic_datasets`.

A kind split answers finding 1 for evaluation sets directly: every row in the corpus category is
capped and no row in the evaluation category is, and each category gets its own weights. The
question the category was built to answer, what a given language has across modalities, no longer
needs one roster. It can be computed from `languages` across both categories.

### Provisional roster

Read from each product's capability value on this date, before any ruling.

- **Evaluation sets (21):** `flores-plus`, `fleurs`, `belebele`, `sib-200`, `include-benchmark`,
  `afrobench`, `milu`, `indicgenbench`, `indicxtreme`, `lahaja`, `sea-helm`, `seaexam`, `thai-exam`,
  `vmlu`, `laobench`, `indonlu`, `arabicmmlu`, `darijammlu`, `turkishmmlu`, `kazmmlu`,
  `khayyam-challenge`.
- **Boundary cases (7):** task sets that ship training and test splits, and the hub: `afrihate`,
  `sold`, `nchlt`, `afridocmt`, `americasnlp-shared-task-data`, `typhoon-s-sovereign-capability`,
  `seacrowd`. Decision D2 settles them.
- **Corpora:** everything else, including the three withheld corpora (`mms-lab-data`, `sarvam-2t`,
  `te-hiku-media-reo-maori-corpus`).

Twenty-one evaluation sets clear the ten-product publication floor in
`docs/workflows/edit-category.md`. A product that moves needs its capability band re-read, since a
`relative_to` peer must sit in its own category. Under the provisional roster, five peers cross
the line: `lahaja` names `kathbath`, `seacrowd` names `sea-helm`, `afrihate` and `sold` name
`afrobench`, and `americasnlp-shared-task-data` names `flores-plus`. Four of the five are boundary
cases, so D2 settles most of them.

## Decisions

In dependency order. Each carries a recommendation, for the ruling session to confirm or overturn.

**D1. Split shape.** Split `language_specific_datasets` into a corpus category (pretraining text,
speech, parallel text, instruction data) and a new evaluation-set category? *Recommend yes, by kind,
for the reasons above.* The current slug stays with the corpus category, so existing links keep
working.

**D2. Boundary for task sets with training splits.** Does a dataset that ships training and test
splits for one task (AfriHate, SOLD, NCHLT) go with evaluation sets or corpora? Is SEACrowd, a
loader hub, either? *Recommend: by what its paper and card say it is for. A set published as a
benchmark or shared-task test is an evaluation set. A labeled task dataset published for training
is a corpus. SEACrowd goes with corpora, since most of what it loads is training data.*

**D3. A cap for instruction data.** Instruction data is exempt from the caps today, so finding 1
survives the split inside the corpus category. Cap it, counted in examples against the largest
open English instruction sets, one order of magnitude per step? *Recommend yes, with the reference
sets fetched and named in the recipe. Generated and translated examples count at face value, and
provenance is handled by the rungs, not by the cap.*

**D4. The bundling rule.** Make it symmetric:
- (a) **Unbundle.** Every independently published member gets its own row (NusaX, PhoMT, the ten
  AfroBench sets, IndicSentiment, and SEA-HELM's task sets where published separately), linked to
  its suites.
- (b) **Fold everything.** Global sets a suite borrows also lose their own rows.

*Recommend (a).* It matches the many-to-many direction of the Public AI hosting ruling, and (b)
would cost FLORES+ its row. The cost is at least thirteen new rows and a relationship field, which is
a schema change in its own PR.

**D5. Source for "underrepresented".** Replace the enumerated list with a graded measure computed
from `languages`. Candidates:
- (a) the Joshi et al. (2020) resource classes;
- (b) a language's share of Common Crawl pages, which Common Crawl publishes for each crawl;
- (c) keep the list.

*Recommend (b), checked against (a).* It is current, re-fetchable and primary, where (a) is a 2020
snapshot. The threshold is set in the ruling, once the table is fetched and the calls it changes
are listed. Arabic, Korean, Indonesian and Vietnamese are the ones to check, since the current
list's calls for them are not obviously what any threshold reproduces. A multilingual dataset
qualifies when most of its languages are under the threshold.

**D6. Evaluation-set ladder.** Replace "no other open row covers the same languages" with rungs on
per-language depth (items per language), provenance (written in the language, human-translated,
machine-translated) and named downstream use. Breadth counts only through the per-language view.
*Recommend yes.* It answers findings 3 and 4. No band is presumed; FLORES+ and SEA-HELM are
re-read on the new rungs like every other row.

**D7. Adoption across languages.** Normalize downloads per language served? *Recommend no, for now.*
Dividing by language count penalizes broad sets crudely. Show adoption beside same-language peers
in the per-language view, and revisit once that view exists. If a normalization is adopted later
and changes the instrument, it goes through `migrate-axis`.

## Sequence

Each step is its own PR, on the workflow named.

1. **Ruling session** (`ruling-session`): put D1 to D7 to the maintainer in one pass, and record
   them in `docs/rulings/log.yaml`.
2. **Membership rule** (`edit-category`): apply D5. Re-route rows that fall outside the threshold
   to `training_synthetic_datasets` or `benchmark_eval_data`. Rewrite the category comments.
   Membership comes before the split, because both new categories inherit it.
3. **Split** (`edit-category`): create the evaluation-set category as preliminary, add it to
   `sources/taxonomy.yaml`, move the roster per D1 and D2, and re-point the `relative_to` peers
   that cross the new line.
4. **Bundling** (`add-product`, plus a schema PR if D4 is (a)): add member rows and the suite
   relationship.
5. **Ladders** (`build-rubric`): the corpus recipe gains the instruction-data cap (D3). The
   evaluation-set recipe is new (D6).
6. **Re-score and publish** (`refresh-category`, both categories). The evaluation-set category moves
   to published once its strapline and ten scored products are in.
7. **Adoption** (D7), when the per-language view exists.
