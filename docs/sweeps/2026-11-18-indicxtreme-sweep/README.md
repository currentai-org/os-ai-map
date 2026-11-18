# IndicXTREME sweep, 2026-11-18

Issue #1098 asks for the membership, coverage and provenance rules just applied to SEA-HELM to be
applied to the other regional suites, so every suite is read the same way. This record is the
IndicXTREME half. The SEA-HELM pass is the template: #1091 for coverage, #1094 for member rows,
and `docs/sweeps/2026-11-17-ai-singapore-followups/README.md` for the record. No scoring rule
changed. The aim was a consistent reading, and the reading leaves IndicXTREME's band where it was.

## What was read

IndicXTREME has no task configuration file of the kind SEA-HELM has. What it publishes is a task
list in the IndicBERT README, one evaluation script per task under `fine-tuning/` in the same
repository, the Hugging Face repositories those scripts load, and the paper (arXiv 2212.05409).
All of these were read on 2026-11-18. Split metadata exists for three repositories (IndicXParaphrase,
Naamapadam and IndicXNLI, through the dataset viewer's size endpoint). IndicCOPA, IndicQA and
IndicSentiment load through scripts, so the viewer reads no splits for them; their file lists name
one test file per language, and spot counts of the data files (500 COPA items in Assamese, Santali
and Urdu, 1,000 IndicSentiment reviews in Bodo and Tamil, 1,789 IndicQA questions in Assamese)
match the paper's tables.

| Task | Component | Languages with a published test split and an evaluation script | Recorded before | Change |
|---|---|---|---|---|
| Commonsense reasoning | `indiccopa` | 18 | 18 | none |
| Reading comprehension | `indicqa` | 11 | 11 | none |
| Sentiment | `indicsentiment` | 13 | 13 | none |
| Paraphrase | `indicxparaphrase` | 10, 2,002 items each | 10 | none |
| NLI | `indicxnli` for 11, `xnli` for Urdu | 12 | 12, Urdu as `indicxnli` | Urdu's component corrected |
| Named entities | `naamapadam` | 9 | 6 | Gujarati, Kannada and Marathi added |
| Intent and slot filling | `massive` | 7 | 7 | none |
| Sentence retrieval | `flores-plus` | 18 | 18 | none |

No target language was added or dropped. Naamapadam's repository also has Assamese and Odia test
splits, which its paper calls "silver standard" and which IndicXTREME leaves out (the README names
"manually curated testsets for 9 Indic languages", and Table 20 reports nine), so they are not
counted as IndicXTREME's coverage.

## The two unmeasured languages

Kashmiri and Manipuri are targets because IndicXTREME's sentence-retrieval task runs on them
(Table 23; `fine-tuning/retrieval/retrieval.py` reads FLORES-200's devtest split). That is the only
task that does. The other eight tasks' language lists, in the paper's results tables and in the
Hub files, leave both out. The paper's language-identification table (Table 11) also uses FLORES
devtest, but it is an analysis of IndicBERT, not one of the nine tasks, and language identification
has no measurement model either. The paper notes that FLORES writes Manipuri in Bengali script.

Sentence retrieval has no approved measurement model (R-2026-11-02-b), so both languages stay
unmeasured: nothing IndicXTREME publishes measures them on the ladder. Filled at 0 and at 5 they
do not move the median, so the band stands.

## Provenance

### IndicXNLI's test sets: the published split is not the verified one

Main recorded IndicXNLI's test split in eight languages as `mixed`, with the paper's Table 9
"verified" column as the qualifying count (R-2026-11-03-d), and in Gujarati, Punjabi and Tamil as
`machine_translated`, since Table 9 lists no verified items there.

The paper says the verification was under way and not yet in the benchmark:

- [arXiv 2212.05409](https://arxiv.org/pdf/2212.05409), Table 2: "ζ - Human verification is in
  progress, please refer to Appendix I"; Appendix I: "Our effort to manually correct all the
  translations in the IndicXNLI (Aggarwal et al., 2022) dataset is currently ongoing" and "Once the
  complete test set is verified and cleaned, we plan to update IndicXTREME with the additional data".

What IndicXTREME publishes points at the machine translation:

- [IndicBERT README](https://raw.githubusercontent.com/AI4Bharat/IndicBERT/main/README.md): IndicXNLI is
  "Automatically translated version of XNLI in 11 Indic languages", linked to `Divyanshu/indicxnli`.
- [`fine-tuning/xnli/xnli.py`](https://raw.githubusercontent.com/AI4Bharat/IndicBERT/main/fine-tuning/xnli/xnli.py)
  loads `load_dataset("Divyanshu/indicxnli", f"{args.eval_data}", use_auth_token=True)`.
- [The repository's card](https://huggingface.co/datasets/Divyanshu/indicxnli/raw/main/README.md) gives
  "annotations_creators" and "language_creators" as "machine-generated", and
  [its commit history](https://huggingface.co/api/datasets/Divyanshu/indicxnli/commits/main) shows the
  data last added on 2022-08-26 ("add split dataset") and nothing after 2022-10-06, before the
  verification the paper describes.

So one first-party source says part of the test set was checked by people, and the data the
benchmark's own script runs has not changed since before that check. Under the provenance rule,
sources that disagree would give `unknown`, citing both. But these eight entries are settled by an
in-force ruling, R-2026-11-03-d, which sets each qualifying count to the paper's verified column, and
a sweep applying existing rulings does not overturn one. The entries keep `mixed` with the ruling's
counts, they now also cite the sources above, and the conflict is held on IndicXTREME's capability
axis in `sources/verification_queue.yaml` for the maintainer (question 1). Gujarati, Punjabi and
Tamil stay `machine_translated`, since every source agrees there.

No language's band depends on the answer: IndicXNLI is an import that sets no language's band, and
every one of the eight is at 4 through IndicQA or IndicXParaphrase. Read as `unknown`, the NLI task
would have no band in any language and the task count would fall from 4 to 3.

### Urdu NLI is XNLI's own Urdu

IndicXNLI has no Urdu. The evaluation script loads Urdu from XNLI instead: `if args.eval_data ==
"ur":` then `load_dataset("xtreme", "XNLI")`, filtered to Urdu. So Urdu's entries (2,490 dev,
5,010 test) are now component `xnli`, which has its own lineage record.

Their provenance stays `unknown`, because the sources disagree again. XNLI's paper says "we create
the full XNLI corpus by employing professional translators to translate it into our ten target
languages" ([arXiv 1809.05053](https://arxiv.org/pdf/1809.05053)), while IndicXTREME's Table 2
labels its NLI task "MT" across all 12 of its languages. Section 3.2 describes IndicXNLI as covering
11, which suggests the label belongs to IndicXNLI and not to Urdu, but that is a reading, not a
statement, and is listed as a question below. As `human_translated`, Urdu would still be at 4.

### Naamapadam: unknown stands

Naamapadam's test sentences are the Indic side of Samanantar's English-Indic pairs ("We use the
parallel corpus from the Samanantar Dataset", its card), and its paper says "The annotators had to
verify if the projected NER annotations were correct and rectify the annotations if incorrect",
by "volunteers who are native language speakers". That is a statement about the labels. No source
read here says how the Indic sentences came to be, whether written in the language or translated,
so the six existing entries stay `unknown`.

The paper rounds its Gujarati, Kannada and Marathi counts, which is why main left them out. The
repository's split metadata gives them exactly (1,076, 1,019 and 1,080), so they are added, with the
same provenance as their siblings. Named-entity tagging has no measurement model, so none of the
nine entries can carry a band whatever their provenance.

### One count corrected

IndicXNLI's Tamil validation split holds 3,238 pairs in the published data, not the paper's 2,490.
It is not the official split, so nothing reads it.

## Score changes

From `build/depth_ladder.py`. Every target language's band is the same before and after:

| Language | Before | After |
|---|---|---|
| Assamese, Bengali, Gujarati, Hindi, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, Telugu, Urdu | 4 | 4 |
| Bodo, Konkani, Maithili, Nepali, Sanskrit, Santali, Sindhi | 3 | 3 |
| Kashmiri, Manipuri | unmeasured | unmeasured |
| **IndicXTREME** | **4** | **4** |

Face value 4, best original band 4, bonus 4.47, completeness 19 of 21, unverified-lineage
sensitivity 4, no capped language and 4 tasks, before and after. Depth-unknown entries move from 7
to 10, the three new Naamapadam ones; the 67 provisional count-model entries are unchanged. The full-roster calibration figures
(`tests/test_depth_calibration.py`) do not change.

Urdu's 4 is worth knowing about: it comes from MASSIVE's intent task, an import of 2,974 utterances,
which counts up to one band above the independent IndicCOPA test beside it (band 3). The issue lists
"MASSIVE's intent task" among the tasks with no measurement model, but the record files intent as
text classification, which has one; the seven unresolved MASSIVE entries are its slot-filling task,
filed as sequence labeling.

## IndicXTREME's separately published members (#1101)

Four sets that AI4Bharat made for IndicXTREME and publishes on their own Hub repositories are
proposed as rows in `language_specific_eval_sets`, linked by `lineage.part_of: [indicxtreme]`, under
R-2026-11-18-a. Every target language of each is below the high class at both ends in the
per-language classification, and each was published as a test set. Their coverage entries name the
same components IndicXTREME's do, so they share lineage records with the suite and never
corroborate it.

| Product | Openness | Adoption | Capability | Note |
|---|---|---|---|---|
| IndicCOPA | 4 (CC BY 4.0, card body an empty template) | 1 | 3 | 18 languages, 500 hand-translated items each |
| IndicQA | 5 (CC BY 4.0, card present) | 2 | 4 | 11 languages, 1,517 to 2,017 native questions each |
| IndicSentiment | 2 (no license on the repository), held | 2 | 3 | 13 languages, 1,000 hand-translated reviews each |
| IndicXParaphrase | 2 (no license, no card), held | 1 | 4 | 10 languages, 2,002 verified items each |

The stage stays 2. The category's gaps change from capability and adoption to adoption alone:
IndicQA, open and at band 4, becomes the best fully open product in the category (overall 3.4, up
from INCLUDE's and Belebele's 3.0), and its capability clears the cutoff. The counting rule groups a
suite with its members only for the count of category-leading products, so a member row can move
the best score and the gaps, as this one does.

Not added:

- **Naamapadam.** Its paper presents it as a training corpus ("the largest publicly available Named
  Entity Recognition (NER) dataset for the 11 major Indian languages", with test sets for nine), so
  by the kind test it belongs in `language_specific_datasets`, not here. A row there is an
  add-product of its own.
- **IndicXNLI.** Published separately (Aggarwal, Gupta and Kunchukuttan, 2022) and titled as an
  evaluation set, but its own release is a machine translation whose only human check scored 100
  sampled sentences per language. Whether that reads as a measured zero or an unresolved band is not
  settled by the rules (question 3), and the row would need a new organization. Held for the
  maintainer.
- **MASSIVE.** Amazon's set covers 51 languages, many of them high, and is defined by its task. It is
  borrowed by IndicXTREME, not published by it, and by the category's neighbor rule it would belong
  in `benchmark_eval_data`.
- **FLORES.** Already on the map as `flores-plus`.

## Held

- IndicSentiment's and IndicXParaphrase's openness. Their repositories carry no license, while the
  IndicBERT README says "All the datasets created as part of this work will be released under a CC-0
  license". The records read the repository, as IndicXTREME's own record does, and score 2.
- The four new rows' adoption, from hand-read Hugging Face download counts, until the weekly
  reconciliation measures them, as #1094 did.

Not held: IndicCOPA's and IndicQA's repositories give CC BY 4.0 while the README says CC0. Both are
open licenses on the same rung, so the score does not depend on which applies, and the notes say so.

## Questions for the maintainer

1. **IndicXNLI's verified items.** Should IndicXTREME's IndicXNLI entries keep the paper's verified
   counts (R-2026-11-03-d, as recorded here, with the conflict held), read the published split as
   unreviewed machine translation, or become `unknown`? Proposed: `unknown` until AI4Bharat publishes the verified test set, then the
   verified counts, since R-2026-11-03-d presumed the verified items were the ones evaluated.
2. **Urdu NLI.** Is Table 2's "MT" label a statement about XNLI's Urdu? Proposed: no. Section 3.2
   limits IndicXNLI to 11 languages and the script loads human-translated XNLI for Urdu, so the entry
   could read `human_translated`. Urdu's band is 4 either way.
3. **A sample-only quality check.** IndicXNLI's own paper had people score 100 sampled sentences per
   language and corrected nothing. R-2026-11-03-h covers a review of unstated scope, not one of a
   stated sample. Proposed: no `human_validated` on such entries, so they read as unreviewed machine
   translation (a measured zero), with a ruling to say so; then IndicXNLI can get a row.
4. **Members that fail this category's kind test.** Naamapadam is a member by R-2026-10-30-f but a
   corpus by the kind test. Proposed: it gets a row in `language_specific_datasets` through
   add-product, linked by `part_of`, which groups nothing across categories.
5. **Global sets a suite borrows.** MASSIVE has no row anywhere. Proposed: a `benchmark_eval_data`
   candidate, without a `part_of` edge, since IndicXTREME did not make it.
6. **Measurement models.** Sentence retrieval, sequence labeling (Naamapadam, MASSIVE slot filling)
   and language identification have none, so Kashmiri and Manipuri cannot be measured here. Proposed:
   a separate issue with a proposed ruling, as #1098 says.
7. **Members another suite imports.** SEA-HELM runs IndicQA's and IndicSentiment's Tamil items.
   Proposed: no `part_of: [sea-helm]` on either, since `part_of` marks the suite that made a member,
   and the lineage registry already treats SEA-HELM's copies as imports.
8. **Which ruling admits the rows.** The four rows cite R-2026-11-18-a, which ruled on SEA-HELM's
   members and stated the general rule. Proposed: keep it, or record a named ruling for IndicXTREME
   if the roster freeze (R-2026-11-07-b) wants one per suite.
9. **Licenses on the same rung.** Proposed: a disagreement between two open licenses (CC BY 4.0 and
   CC0) is noted but not held, because no reading moves the score.

## Score changes

| Product | Axis | Before | After | PR |
|---|---|---|---|---|
| IndicXTREME | capability | 4 | 4 (unchanged; IndicXNLI conflict held) | #1100 |
| IndicCOPA (proposed) | openness / adoption / capability | | 4 / 1 / 3 | #1101 |
| IndicQA (proposed) | openness / adoption / capability | | 5 / 2 / 4 | #1101 |
| IndicSentiment (proposed) | openness / adoption / capability | | 2 / 2 / 3 | #1101 |
| IndicXParaphrase (proposed) | openness / adoption / capability | | 2 / 1 / 4 | #1101 |
