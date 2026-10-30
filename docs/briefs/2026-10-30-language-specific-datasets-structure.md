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

Separate training data from evaluation data. The category puts corpora, instruction data and
evaluation sets on one capability ladder, and that is the main source of the asymmetries below.
Language-targeted evaluation sets either get their own category or move into `benchmark_eval_data`,
and D1 weighs the two. A split removes the size-cap asymmetry (finding 1) for evaluation sets, but
not for instruction data, which needs its own cap. The bundling rule (finding 5) is independent of
the split. Unbundling needs a counting rule first, so that a suite and its members are not counted
more than once toward the category's stage.

Two of the fixes need data the corpus does not have yet. The `languages` field that #684 added lists
which languages a dataset covers, not how much it holds in each, so per-language depth (finding 4)
waits on an evidence model. "Underrepresented" (finding 7) needs a resource classification with an
explicit `unknown` state, not a single web-share threshold.

No step moves a published product into a preliminary category, or moves a product without
rescoring it in the same PR.

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

The seed sweep also listed a structured `languages` field as an open item. #684 added ISO 639-3
`languages`, required on every product in this category (see
`docs/sweeps/2026-09-30-identity-attributes/README.md`). It records coverage only: which languages,
not how many items, hours or tokens each has, where they came from, or which tasks they fall under.

## Where language-targeted evaluation sets should go

Three placements were considered.

**A global/regional split** (global or English sets, evaluation sets, other languages) was set
aside for three reasons:

- **It adds a second hand-drawn line.** Finding 7 is already a boundary drawn by list. A "global"
  category needs another: SEACrowd covers about 1,000 languages and Belebele 122, and neither
  answer is obvious.
- **It makes the hierarchy structural.** The concern is that global sets outrank regional work. A
  category boundary between them would keep them from being compared, and would also say the map
  treats them as different classes.
- **English corpora are already elsewhere.** They are in `training_synthetic_datasets`.

That leaves two placements for the evaluation sets. Both separate training data from evaluation
data. They differ on whether language scope stays part of the category line.

- **A new language-targeted evaluation category.** The split is then not by kind alone. It is by
  kind within the language-specific scope, so the "underrepresented" line (finding 7) still decides
  membership, now for two categories instead of one.
- **Moving them into `benchmark_eval_data`.** The line becomes kind alone, and regional coverage
  shows through `languages`. But that category's recipe has no capability ladder (its
  `scoring_recipe` carries openness only), and it weights adoption 0.6 against capability 0.4.
  The language-specific recipe weights adoption 0.3 because download counts for a low-resource
  dataset are small by construction. In an adoption-heavy category, a Lao or Thai benchmark would
  be ranked on downloads against MMLU and HumanEval. That measures how many people speak the
  language before it measures the benchmark.

The deciding question is whether a language-targeted evaluation set needs a different ladder from a
general benchmark. It does on two counts. Adoption has to be discounted for language population,
which `benchmark_eval_data`'s weights do not do. And per-language depth and provenance (written in
the language, or translated into it) are questions an English benchmark never faces. Moving the sets
into `benchmark_eval_data` would mean giving that category per-language weights or rungs, a change
for its 32 existing products, or accepting the ranking above. A new category keeps the change to
the products it concerns. D1 asks the question with both options.

Either way, every row in the corpus category is capped and no evaluation set is. The question the
category was built to answer, what a given language has across modalities, no longer needs one
roster. Which languages each dataset covers can be computed from `languages` across categories.
How much each holds per language cannot be yet (see D6).

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
`docs/workflows/edit-category.md`. A product that moves is rescored against the destination's
recipe in the same PR. Its band is relative to its category's rubric and weights, and
`build/check_capability.py` rejects a `relative_to` peer in another category. Under the provisional
roster, five peers cross the line: `lahaja` names `kathbath`, `seacrowd` names `sea-helm`,
`afrihate` and `sold` name `afrobench`, and `americasnlp-shared-task-data` names `flores-plus`.
Four of the five are boundary cases, so D2 settles most of them.

A move must not take a product off the public map. `published_products` in `build/validate.py`
leaves every product on a preliminary category's roster out of the scored payload. Moving the 21
evaluation sets into a new preliminary category would take them off the map until it published.
The [sequence](#sequence) keeps the roster where it is until the new category can publish in the
same PR.

## Decisions

In dependency order. Each carries a recommendation, for the ruling session to confirm or overturn.

**D1. Where evaluation sets go.** Take language-targeted evaluation sets out of the corpus ladder,
and place them in:
- (a) a new language-targeted evaluation category, or
- (b) `benchmark_eval_data`, with regional coverage shown through `languages`.

*Recommend (a), because of the deciding question above.* (b) is the cleaner taxonomy, but only if
`benchmark_eval_data` takes on per-language weights or rungs for all its products. Either way, the
corpus category keeps the current slug, so existing links keep working.

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

*Recommend (a), but not before D4b.* It matches the many-to-many direction of the Public AI hosting
ruling, and (b) would cost FLORES+ its row. The cost is at least thirteen new rows and a lineage
relationship, which is a schema change in its own PR.

**D4b. How a suite and its members count.** A category's stage counts its fully open
category-leading products (`_stage_and_gaps` in `build/serialize.py`; Stage 5 needs
`_STAGE5_MIN_MATURE` of them), and nothing in that count knows about overlap. AfroBench plus ten
member rows could count up to eleven times for what is one body of evaluation work, inflating the
category's apparent maturity. *Recommend: a suite and its members form one lineage group, and a group
counts at most once toward the stage, through its highest-scoring fully open row. Each row keeps its
own scores and stays visible.* This is a change to `build/serialize.py` and
`docs/reference/gap-analysis.md`, and it lands before any member row does. Adoption overlaps the
same way, because a suite's downloads include its members', so a member row's adoption note says
which downloads it counts.

**D5. Source for "underrepresented".** Replace the enumerated list with a per-language resource
classification, computed for every code in `languages`. A single web measure cannot carry it:
- **Coverage.** Common Crawl's published language statistics come from a language detector that
  recognizes far fewer languages than the map's datasets cover. A language the detector does not
  report has not been measured, which is not the same as having no web text.
- **What it measures.** Web-page share measures web text. A language can have plenty of it and
  still have little open speech, instruction or evaluation data.

*Recommend: a reproducible classification that combines signals, where web share is one input and
not the rule.* Other inputs would be the Joshi et al. (2020) resource classes and whether the language
has open speech, instruction and evaluation data, which the map itself can count from `languages`.
Each language gets a class, or `unknown` where the signals do not reach it. `unknown` is a recorded
state, not a default to "underrepresented" or "well-resourced". The classification and the roster
changes it implies are published as a table for review before it is adopted. The current calls for
Arabic, Korean, Indonesian and Vietnamese are the ones to check.

Membership stays with the purpose test the category already uses: a dataset is in when it was built
for languages the classification marks underrepresented. There is no majority rule across a
dataset's languages, so adding more low-resource languages to a set cannot move it out. A dataset
whose target languages are all `unknown` is decided on the purpose test alone, and its row records
that.

**D6. Evaluation-set ladder.** Rungs on per-language depth, provenance (written in the language,
human-translated, machine-translated) and named downstream use, in place of "no other open row
covers the same languages". *Recommend yes in principle, but implement only once both parts below
are ruled and in place.* Without them, a depth rung would still be a judgment about breadth, under a
different name.
- **D6a. A per-language evidence model.** For each language a set covers, record its item count,
  provenance and task, cited to the card or paper. A product-level size is not enough for a
  heterogeneous suite like SEA-HELM, whose tasks cover different languages. *Recommend: a structured
  per-language coverage record on evaluation-set products. It is a schema change in its own PR,
  filled by `refresh-category`.*
- **D6b. An aggregation rule.** The map keeps one capability score per product, so per-language
  depth has to reduce to one number. *Recommend: band on the median per-language depth across the
  set's target languages, excluding pivot languages such as English, and show the per-language
  values in the language view.* The median keeps a few deep languages from carrying a set, and a
  few thin ones from sinking it.

Until D6a and D6b are in place, the evaluation category takes the current rungs, with the breadth
clause replaced by a same-language peer comparison. FLORES+ and SEA-HELM are then read against peers
that cover the languages they cover. No band is presumed in either case.

**D7. Adoption across languages.** Normalize downloads per language served? *Recommend no, for now.*
Dividing by language count penalizes broad sets crudely. Show adoption beside same-language peers
in the per-language view, and revisit once that view exists. If a normalization is adopted later
and changes the instrument, it goes through `migrate-axis`.

## Sequence

Each step is its own PR, on the workflow named. Two rules hold throughout. A published product is
never on a preliminary roster. And a product that changes category is rescored against the
destination's recipe, with its `relative_to` peers re-pointed, in the same PR that moves it. No
product moves with its old capability band intact unless that band has been checked against the
destination rubric and the PR says so.

1. **Ruling session** (`ruling-session`): put D1 to D7 to the maintainer in one pass, and record
   them in `docs/rulings/log.yaml`.
2. **Language classification** (D5): publish the per-language classification table, with its
   `unknown` rows, and the roster changes it implies. Nothing moves in this PR. The ruling that
   adopts it reads the table.
3. **Membership** (`edit-category`, `refresh-category`): re-route the rows the adopted
   classification puts outside the category. Each is rescored against its destination's recipe,
   with peers re-pointed, in this PR.
4. **Evaluation recipe** (`build-rubric`), if D1 is (a): create the evaluation category as
   preliminary, with its recipe and an empty roster, so nothing leaves the payload. Dry-run the
   recipe against the products that will move, and record the computed bands in the PR. If D1 is
   (b), this step changes `benchmark_eval_data`'s recipe instead, and rescores its existing products
   in the same PR.
5. **Split, in one PR** (`edit-category`, `refresh-category`): move the roster per D1 and D2, apply
   the bands from step 4, re-point the crossing peers, add the strapline, and set the category to
   published. `build.preflight` passes, and the published product count is the same before and
   after.
6. **Instruction cap** (D3, `build-rubric`): add the cap to the corpus recipe and rescore the
   instruction sets in the same PR.
7. **Lineage counting** (D4b): the schema relationship and the stage rule in `build/serialize.py`,
   with no member rows yet. Then **unbundling** (D4, `add-product`): the member rows, each scored on
   arrival.
8. **Per-language evidence** (D6a, D6b): the coverage schema, then the depth ladder applied through
   `refresh-category`.
9. **Adoption** (D7), when the per-language view exists.
