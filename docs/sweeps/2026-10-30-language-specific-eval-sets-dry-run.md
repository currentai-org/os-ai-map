# Language-specific evaluation sets: boundary calls and recipe dry run, 2026-10-30

## Scope

Step 4 of the sequence in `docs/briefs/2026-10-30-language-specific-datasets-structure.md`. The
preliminary category `language_specific_eval_sets` was created with its recipe and an empty
roster, under rulings R-2026-10-30-a, -b and -g. This record holds the two things the brief says
to settle before the split PR (step 5):

- which of the seven boundary sets are evaluation sets, by the R-2026-10-30-b purpose test, plus
  a check of the 21 provisional evaluation sets by the same test;
- the capability band the new recipe gives every set that would move, with the `relative_to`
  peer it would name in the new category.

Nothing moved. No score, product file or roster changed. The bands below are what the split PR
starts from. That PR still re-reads each product's sources through `refresh-category`, rewrites
the capability notes to the new comparison, and records `comparison` attestations for re-pointed
edges. This record is not that re-verification.

Every source quoted here was fetched on 2026-10-30 with `uv run python -m build.fetch_source`.
Status and digests are in [Sources read](#sources-read).

## Boundary sets (R-2026-10-30-b)

The test: a set published as a benchmark or as a shared-task test is an evaluation set, and a
labeled set published for training is a corpus. SEACrowd was ruled a corpus and was not re-read.

| Product | What its paper or card says it is for | Source | Decision |
|---|---|---|---|
| `afrihate` | "the first high-quality labeled Twitter dataset collection for detecting hate and abusive languages"; the paper's intended uses are framed as "Models built using our datasets should not be used for automated removal", and it closes "AfriHate is a first step towards building high-quality hate speech resources for African languages" | [README](https://raw.githubusercontent.com/afrihate/afrihate/main/README.md), [paper](https://arxiv.org/html/2501.08284) | Corpus |
| `sold` | The paper: "These systems require annotated datasets to train the machine learning (ML) models ... This paper addresses this gap"; it also releases SemiSOLD, "a larger dataset containing more than 145,000 Sinhala tweets, annotated following a semi-supervised approach". The card is headed "SOLD - A Benchmark for Sinhala Offensive Language Identification" | [paper](https://arxiv.org/abs/2212.00851), [card](https://huggingface.co/datasets/sinhala-nlp/SOLD/raw/main/README.md) | Corpus (close call) |
| `nchlt` | "The project focussed on establishing a set of foundational resources that can foster further development of both resources and technologies"; the annotated subsets "were used in the creation of five core-technologies": a tokeniser, sentence splitter, lemmatiser, part-of-speech tagger and morphological decomposer. The Hub entry ships a `train` split only | [card](https://huggingface.co/datasets/nwu-ctext/nchlt/raw/main/README.md) | Corpus |
| `afridocmt` | Paper title "AFRIDOC-MT: Document-level MT Corpus for African Languages"; "Developing and evaluating document-level MT systems for low-resource languages is a useful and under-studied direction, which requires the creation of datasets"; "Fine-tuning selected models leads to substantial performance gains". Ships train, dev and test splits | [paper](https://arxiv.org/html/2501.06374), [card](https://huggingface.co/datasets/masakhane/AfriDocMT/raw/main/README.md) | Corpus (close call) |
| `americasnlp-shared-task-data` | "This is the official repository for the AmericasNLP 2021 Shared Task on Open Machine Translation"; "We provided training sets consisting of data collected from various sources, as well as manually translated sentences for the development and test sets"; 2023: "training on the development set is **not** allowed" | [2021 README](https://raw.githubusercontent.com/AmericasNLP/americasnlp2021/main/README.md), [overview paper](https://aclanthology.org/2021.americasnlp-1.23/), [2023 README](https://raw.githubusercontent.com/AmericasNLP/americasnlp2023/main/README.md) | Evaluation set |
| `typhoon-s-sovereign-capability` | Card headed "Typhoon-S Training Assets", `pretty_name: Typhoon-S Instruct Post-Training`: "Training and evaluation datasets for Section 3, Thai language models used in the Typhoon-S project". Of its files, five are RL, pretraining, SFT or agent training sets and two are test sets | [card](https://huggingface.co/datasets/typhoon-ai/typhoon-s-sovereign-capability-dataset/raw/main/README.md), [paper](https://arxiv.org/abs/2601.18129) | Corpus |
| `seacrowd` | Ruled a corpus in R-2026-10-30-b | | Corpus |

The two close calls, for a reviewer:

- **SOLD.** The card's heading calls it a benchmark. The paper states the purpose as the training
  data that Sinhala offensive-language classifiers lack, and the release's larger half, SemiSOLD,
  is training data only, with no test split. Read as a corpus because the paper says what the set
  is for and the card's heading names a genre. Read the other way it moves, with AfriHate's case
  unchanged.
- **AfriDocMT.** The paper calls itself a corpus, motivates the set by both developing and
  evaluating systems, and fine-tunes on the training split. Its section 4 is titled "Benchmark
  Experiments", but so is every task paper's baseline section, AfriHate's included. Read as a
  corpus.

AmericasNLP is the only boundary set that moves. Its training data is gathered from existing
corpora, and its own contribution is the hand-translated development and test sets the shared
task scores against.

## The 21 provisional evaluation sets, by the same test

All 21 pass. Each one's paper or card says it was built to evaluate.

| Product | Purpose statement | Source |
|---|---|---|
| `flores-plus` | "we introduce the FLORES-101 evaluation benchmark" | [arXiv 2106.03193](https://arxiv.org/abs/2106.03193) |
| `fleurs` | "We introduce FLEURS, the Few-shot Learning Evaluation of Universal Representations of Speech benchmark" | [arXiv 2205.12446](https://arxiv.org/abs/2205.12446) |
| `belebele` | "this dataset enables the evaluation of text models in high-, medium-, and low-resource languages" | [arXiv 2308.16884](https://arxiv.org/abs/2308.16884) |
| `sib-200` | "a large-scale open-sourced benchmark dataset for topic classification ... to address the lack of evaluation dataset" | [arXiv 2309.07445](https://arxiv.org/abs/2309.07445) |
| `include-benchmark` | Title: "INCLUDE: Evaluating Multilingual Language Understanding with Regional Knowledge"; motivated by "the lack of high-quality evaluation resources in languages other than English" | [arXiv 2411.19799](https://arxiv.org/abs/2411.19799) |
| `afrobench` | "we introduce AfroBench -- a multi-task benchmark for evaluating the performance of LLMs across 64 African languages" | [arXiv 2311.07978](https://arxiv.org/abs/2311.07978) |
| `milu` | "We introduce MILU, a Multi task Indic Language Understanding Benchmark, a comprehensive evaluation benchmark" | [arXiv 2411.02538](https://arxiv.org/abs/2411.02538) |
| `indicgenbench` | "To facilitate research on multilingual LLM evaluation, we release IndicGenBench" | [arXiv 2404.16816](https://arxiv.org/abs/2404.16816) |
| `indicxtreme` | The IndicBERT v2 paper's contributions include "(ii) NLU testsets" | [arXiv 2212.05409](https://arxiv.org/abs/2212.05409) |
| `lahaja` | "To enable a robust evaluation of Hindi ASR systems on multiple accents, we create a benchmark, LAHAJA" | [arXiv 2408.11440](https://arxiv.org/abs/2408.11440) |
| `sea-helm` | "we present SEA-HELM, a holistic linguistic and cultural LLM evaluation suite" | [arXiv 2502.14301](https://arxiv.org/abs/2502.14301) |
| `seaexam` | "The SeaExam dataset aims to evaluate Large Language Models (LLMs) on a diverse set of Southeast Asian (SEA) languages" | [card](https://huggingface.co/datasets/SeaLLMs/SeaExam/raw/main/README.md) |
| `thai-exam` | "ThaiExam is a Thai knowledge benchmarking dataset ... originally developed for evaluating Typhoon (Thai LLM)" | [card](https://huggingface.co/datasets/typhoon-ai/thai_exam/raw/main/README.md) |
| `vmlu` | "VMLU is a human-centric benchmark suite specifically designed to evaluate the general capabilities of foundational models with a focus on the Vietnamese language" | [README](https://raw.githubusercontent.com/ZaloAI-Jaist/VMLU/main/README.md) |
| `laobench` | "the first large-scale, high-quality, and multidimensional benchmark for assessing LLM language understanding and reasoning in Lao" | [arXiv 2511.11334](https://arxiv.org/abs/2511.11334) |
| `indonlu` | Title: "IndoNLU: Benchmark and Resources for Evaluating Indonesian Natural Language Understanding"; abstract: "the first-ever vast resource for the training, evaluating, and benchmarking" | [arXiv 2009.05387](https://arxiv.org/abs/2009.05387) |
| `arabicmmlu` | "the first multi-task language understanding benchmark for the Arabic language" | [arXiv 2402.12840](https://arxiv.org/abs/2402.12840) |
| `darijammlu` | "DarijaMMLU is an evaluation benchmark designed to assess large language models' (LLM) performance in Moroccan Darija" | [card](https://huggingface.co/datasets/MBZUAI-Paris/DarijaMMLU/raw/main/README.md) |
| `turkishmmlu` | "We introduce the first multitask, multiple-choice Turkish QA benchmark, TurkishMMLU, to evaluate LLMs' understanding" | [arXiv 2407.12402](https://arxiv.org/abs/2407.12402) |
| `kazmmlu` | Title: "KazMMLU: Evaluating Language Models on Kazakh, Russian, and Regional Knowledge of Kazakhstan" | [arXiv 2502.12829](https://arxiv.org/abs/2502.12829) |
| `khayyam-challenge` | "non-English LLM evaluation lags behind English ... In response to this necessity, we introduce Khayyam Challenge" | [arXiv 2404.06644](https://arxiv.org/abs/2404.06644) |

The weakest pass is `indonlu`. Its title says benchmark, but the abstract names training too, and
its twelve tasks ship training splits that community classifiers are fine-tuned on. It is
published as a benchmark, which is the test, so it moves. `fleurs` and `afrobench` also ship
training data (FLEURS about ten hours per language, AfroBench's members their own training
splits), and both are published as evaluations. `indicxtreme`'s product row cites no paper of its
own. The IndicBERT v2 paper above is the one that introduces its test sets.

## Dry run

The rule is in the category's `scoring_recipe.note`. In short: the corpus category's rungs, no
size cap, and in place of the breadth clause a set reaches 5 only when no same-language peer of
the same kind holds more for most of the languages it was built for. A peer has to be documented
and used downstream by name to outrank anything. Suites are compared with suites. Pivot
languages (English, and Spanish for AmericasNLP, Chinese for LaoBench) are left out.

Applied to the recorded capability values on `main` at this date, plus the sources read above.
Per-language counts are the recorded totals divided by languages unless a finer figure is named.

| Product | Kind | Current | New | `relative_to` (new) | Reason |
|---|---|---|---|---|---|
| `flores-plus` | translation | 5 (root) | **5** | root | Its only translation peer, AmericasNLP (shares `grn`, `quy`), is a 3 and cannot outrank it; used by NLLB-200, FLEURS and Belebele |
| `fleurs` | speech | 5 (root) | **5** | root | Its only speech peer, Lahaja, shares one of 101 languages (`hin`) and has no downstream use; used in Meta's MMS paper |
| `belebele` | understanding | 5 (root) | **5** | root | Its only understanding peer, SIB-200, has no downstream use; in EleutherAI's harness |
| `sib-200` | understanding | 3 (`belebele` two_below) | **3** | `belebele` two_below | Narrow single-task set (topic labels) with no use beyond its own baselines; unchanged |
| `include-benchmark` | knowledge | 4 (`belebele` one_below) | **5** | root | Used peers hold more on 4 of its 44 languages (ArabicMMLU `ara`, Khayyam `fas`, TurkishMMLU `tur`, VMLU `vie`; INCLUDE averages about 514 per language), not most; in EleutherAI's harness. Was one below Belebele, a different kind of test |
| `afrobench` | suite | 5 (root) | **5** | root | No other suite covers an African language; InkubaLM reports on it; public leaderboard |
| `milu` | knowledge | 3 (`indicxtreme` one_below) | **3** | `indicxtreme` two_below | No model or leaderboard outside its paper (rung 3), although it holds more than INCLUDE on its five shared languages; relation re-spaced because IndicXTREME rises to 5 |
| `indicgenbench` | suite | 3 (`indicxtreme` one_below) | **3** | `indicxtreme` two_below | No use beyond its paper's evaluations (rung 3); relation re-spaced as for MILU |
| `indicxtreme` | suite | 4 (`afrobench` one_below) | **5** | root | Its suite peers are IndicGenBench (rung 3) and SEA-HELM on Tamil only; IndicBERT v2 and the Airavata suite report on it. Was one below AfroBench for covering fewer languages, which no longer counts |
| `lahaja` | speech | 3 (`kathbath` at) | **3** | `fleurs` two_below | No use outside its paper (rung 3). Kathbath is a corpus and stays behind, so the peer becomes FLEURS, the speech set that covers Hindi |
| `sea-helm` | suite | 5 (root) | **5** | root | Suite peers touch at most two of its 12 languages (IndoNLU `ind`, IndicXTREME `tam`; LaoBench is a 3); backs a public leaderboard |
| `seaexam` | knowledge | 3 (`sea-helm` two_below) | **2** | `indonlu` two_below | Rung 2: 2,850 of about 4,760 rows per non-English language are MMLU run through Google Translate (card; about 60%), and the rest is the publisher's M3Exam reformatted. See judgment call 1 |
| `thai-exam` | knowledge | 4 (`sea-helm` one_below) | **5** | root | Its only Thai knowledge peer is SeaExam, a 2, which cannot outrank it; in HELM Thai, SEA-HELM and the Thai LLM leaderboard. Was one below SEA-HELM for covering fewer tasks and languages, which no longer counts |
| `vmlu` | knowledge | 4 (`sea-helm` one_below) | **5** | root | 10,880 Vietnamese questions against about 514 in INCLUDE; SeaExam is a 2; publisher's leaderboard scores open and API models. See judgment call 2 on documentation |
| `laobench` | suite | 3 (`sea-helm` two_below) | **3** | `sea-helm` two_below | No outside leaderboard or model report (rung 3); unchanged |
| `indonlu` | suite | 4 (`sea-helm` one_below) | **4** | `sea-helm` one_below | Rung 4's second clause: no used suite outholds it on Indonesian on the recorded evidence, but beyond its own paper's IndoBERT the only named use is community fine-tunes on the Hub; unchanged |
| `arabicmmlu` | knowledge | 5 (root) | **5** | root | 14,575 Arabic questions against about 514 in INCLUDE; DarijaMMLU is built on it; unchanged |
| `darijammlu` | knowledge | 2 (`kazmmlu` one_below) | **2** | `kazmmlu` one_below | Machine-translated (with review) from MMLU and ArabicMMLU (rung 2); unchanged |
| `turkishmmlu` | knowledge | 3 (`arabicmmlu` two_below) | **5** | root | Over 10,000 expert-written questions (1,845 posted openly) against about 514 Turkish in INCLUDE; a community Turkish LLM leaderboard runs on it. Was two below ArabicMMLU, a set for another language. See judgment call 3 |
| `kazmmlu` | knowledge | 3 (`arabicmmlu` two_below) | **3** | `arabicmmlu` two_below | No use outside its paper (rung 3); unchanged |
| `khayyam-challenge` | knowledge | 4 (`arabicmmlu` one_below) | **5** | root | 20,192 Persian questions against about 514 in INCLUDE; ParsBench uses it. Was one below ArabicMMLU for its missing card and restrictive terms, which are openness facts |
| `americasnlp-shared-task-data` | translation | 3 (`flores-plus` two_below) | **3** | `flores-plus` two_below | Hand-translated test sets, no use found outside its shared tasks (rung 3); the edge stays, now inside the category |

**Distribution.** Current bands of these 22: six at 5, six at 4, nine at 3, one at 2. New: twelve
at 5, one at 4, seven at 3, two at 2. Seven bands move: six rise (INCLUDE, IndicXTREME, ThaiExam,
VMLU, Khayyam by one, TurkishMMLU by two) and one falls (SeaExam). Every rise is a band the
current note set by comparing the set with something that covers more languages or more tasks,
or with a set for another language. The recipe note records the wide top rung and how it reads.

**Overall score** (weights unchanged at 0.3/0.7). No set crosses the 4.5 category-leading line,
and FLEURS stays the only one above it. INCLUDE (3.7 to 4.4), IndicXTREME and ThaiExam (3.4 to
4.1) enter the strong tier. SeaExam falls from 2.4 to 1.7.

**Peer arithmetic** was checked against the new bands. Every `relative_to` above names a set that
moves, and no edge forms a cycle.

## Peers left behind

Products staying in `language_specific_datasets` that name a set that moves. The split PR
re-points each one inside the corpus category, against that category's recipe:

- `chren` and `jojajovai` name `americasnlp-shared-task-data` (two_below).
- `afrihate` and `sold` name `afrobench` (two_below).
- `seacrowd` names `sea-helm` (two_below).

The other boundary sets already name corpora (`nchlt` names `wura`, `afridocmt` names
`iitb-english-hindi`, `typhoon-s-sovereign-capability` names `wangchan-thai-instruct`), so they
need no change.

## Judgment calls for review

1. **SeaExam at 2.** The current band, 3, did not apply rung 2. The card says the translated MMLU
   part was "translated from English into Chinese, Indonesian, Thai, and Vietnamese using Google
   Translate", and it is most of each non-English language's rows. If rung 2 is read as applying
   only to a wholly machine-translated set, SeaExam computes 5: its own leaderboard is named use,
   and only VMLU outholds it, on one of its four languages. SeaExam then becomes a qualifying
   peer for Thai, holds more Thai questions than ThaiExam (about 4,760 against 590), and ThaiExam
   computes 4, `seaexam` one_below. The two bands move together.
2. **VMLU's documentation.** It has a README and a website, with no paper. The current note named
   that as one reason it sat below SEA-HELM. It is read here as documented, since the parent rungs
   ask for documentation and not for a paper, and rung 2's "thin documentation" does not describe
   a README that sets out its subjects, sources and leaderboard.
3. **TurkishMMLU's open share.** Only 1,845 of its 10,000-plus questions are posted openly. That
   limits it on the openness axis, where it already sits at 2/restricted, and the recipe judges
   held-out sets on the facts their owners describe. A reviewer who reads 18% posted as rung 1's
   "fragment" would hold it lower. Nothing in the parent rungs says so.
4. **The aggregation.** "Most of its languages" is this PR's reading of "compared with sets
   covering the same languages" for a many-language set. The stricter reading is that any
   stronger peer on any shared language caps a set at 4. Under it, INCLUDE computes 4 (four used
   peers outhold it), and SEA-HELM very likely does too: IndicXTREME almost certainly holds more
   Tamil test items and IndoNLU more Indonesian ones, though neither count is recorded per
   language. FLORES+, FLEURS and Belebele stay at 5, because none of their shared-language peers
   is both used and larger. The recipe note gives the reason for preferring "most": it is the
   interim form of the median R-2026-10-30-i adopts.
5. **Suites compared with suites.** If a suite were also a peer of every kind it contains,
   ThaiExam would meet SEA-HELM's own Thai items, and VMLU its Vietnamese ones. Neither count is
   recorded per language, so the outcome is unknown, and that alone argues for keeping the kinds
   apart until R-2026-10-30-h records them.

## For the split PR (step 5)

- Add `language_specific_eval_sets` to `LANGUAGES_REQUIRED_CATEGORIES` in `build/validate.py`.
  The peer comparison reads `languages`.
- Rewrite each moved product's capability `note` and `value` to the same-language comparison.
  The current notes compare across languages and tasks, which the new recipe does not read.
  Record `comparison` blocks for the re-pointed edges (`lahaja`, `milu`, `indicgenbench`,
  `seaexam`) and for the five corpus edges above.
- Adoption is unchanged: same instruments, same weight.
- Write a strapline, and set the taxonomy entry to `published` in the same PR, so the published
  product count is the same before and after.

## Sources read

All fetched 2026-10-30 with `build.fetch_source`. HTTP 200 unless noted.

| URL | sha256 |
|---|---|
| https://arxiv.org/abs/2501.08284 | `af9cc077d4919fe4149051895ca8e52cb75b6ab7e164cc0e9e31f7132f69516f` |
| https://arxiv.org/html/2501.08284 | `2386e6e9b70514c17bdbd25c496405444ef15f2dfb22b624b364bd13811ab9ea` |
| https://raw.githubusercontent.com/afrihate/afrihate/main/README.md | `c5a3213b381c9b0499003e1992c78f37d121ea181a5578617a3ca6412d657e05` |
| https://huggingface.co/datasets/afrihate/afrihate/raw/main/README.md | HTTP 401 (gated), not read |
| https://arxiv.org/abs/2212.00851 | `7779a1f3e30c10c7d89902d5d3f78010f9c4b6f827e0fdc5fb7ebe0675fd1d8f` |
| https://huggingface.co/datasets/sinhala-nlp/SOLD/raw/main/README.md | `53d4a4b30ee66fdca2646d6d69da4c87e479e0e6cb116f5eab66f94c7a658878` |
| https://huggingface.co/datasets/nwu-ctext/nchlt/raw/main/README.md | `2cc975dd6c8fb6ca61198f3d88c6c166f6eed9faea571dba7f53b9c414e55050` |
| https://arxiv.org/abs/2501.06374 | `d4832c4ac745bd40c9626bd9c251694a77f09db8a67126e5c9efad7aa91c5690` |
| https://arxiv.org/html/2501.06374 | `ec3d44aac54179335d9b9ecbbe3722501186adc8991b3e53a98054f0bce5d81b` |
| https://huggingface.co/datasets/masakhane/AfriDocMT/raw/main/README.md | `915cea082b62e8a970fcc6b4b3343a2c0a50dd7d05af93b3fe784aa42340a33a` |
| https://aclanthology.org/2021.americasnlp-1.23/ | `5e4f32a026553178cae8dbe6a4ecf0fb88359a0fd89c63e54ceb0a77c4489cbb` |
| https://raw.githubusercontent.com/AmericasNLP/americasnlp2021/main/README.md | `90aae8c57419f633de42153c105e798cb21aa68e351c5717ab7e7e976dac6824` |
| https://raw.githubusercontent.com/AmericasNLP/americasnlp2023/main/README.md | `f7885a1a7f5b87fe62ea1b0167a0e941938192f303e4fa0ad6f9a45b6124ad41` |
| https://huggingface.co/datasets/typhoon-ai/typhoon-s-sovereign-capability-dataset/raw/main/README.md | `9ca513194c59c5cf17d46b4d885deaa120c6ca5f2544b2929383fbec9af47cf4` |
| https://arxiv.org/abs/2601.18129 | `134b36b1d87c3cd1f7824a1e134af0fd023714987b37155176894ac0e50dfa47` |
| https://arxiv.org/abs/2106.03193 | `3f1f5a73d1b6ab876346aefdaf9d0effff277406366c202993f6b9d7602f5f70` |
| https://arxiv.org/abs/2205.12446 | `85f31033165cbef20a6734206b5ad15e26a5d5db45a55f1593723294d0aa7dce` |
| https://arxiv.org/abs/2308.16884 | `19c8e41cca4fc3b2a0ddb85eab0d7f592163161ae00d8d5c3a6cf068cf854ca0` |
| https://arxiv.org/abs/2309.07445 | `b2601dc14aa72468241a9d8f132636ff7f6b575cf7767878d8ed4ac592bbb82c` |
| https://arxiv.org/abs/2411.19799 | `1ca3e5306bd425577ff58a8c16a7d96476c097ea27f747b4003e5b6c9261c0bb` |
| https://arxiv.org/abs/2311.07978 | `eb9e149469fc1147a57f73e3b3bd517ba83727eb14c75092116d6a98a46ecefe` |
| https://arxiv.org/abs/2411.02538 | `ede49a6991ff2ecb484dd617365c105627020c83943bdbd6e2c7927e358f0733` |
| https://arxiv.org/abs/2404.16816 | `f8d8bfba0eff6563694539aece4c1f51d654aca1d5218f7c18c118fe576d2f4d` |
| https://arxiv.org/abs/2212.05409 | `ddf4d84bdf38c67fc46b41757b0f6f1ed0e6dfaf174455b90c97b2dd0be98b51` |
| https://arxiv.org/abs/2408.11440 | `ca11d24c461c0fb06ad748aca00fd4af24818c8f4795c420f244fa7b72a59ad4` |
| https://arxiv.org/abs/2502.14301 | `a63caf7a0579c01fe90ab5d0d7425db1e631e18cf7888d82210c802cbd1be0b2` |
| https://huggingface.co/datasets/SeaLLMs/SeaExam/raw/main/README.md | `951aabb036aa594cfe7d991889fe775c88ca94abc8d75e55f8d006cedaae8c7b` |
| https://huggingface.co/datasets/typhoon-ai/thai_exam/raw/main/README.md | `860459e28fcaf606f68f1fb40bbdb9bd6b47e74c62fb390e37ac133c0b53b3ff` |
| https://raw.githubusercontent.com/ZaloAI-Jaist/VMLU/main/README.md | `df64aac6d70eb3eda30de301101b370fab19706aa4f12ece357886f59d0464a4` |
| https://arxiv.org/abs/2511.11334 | `1757e6bc0fe711019f8e557e2ecfaf4f50fb2d567a983ce974fe4fa284c95119` |
| https://arxiv.org/abs/2009.05387 | `d5a936aaf48f35bf29fcd7f8f4758700e1cfeec5c63d8404bd8a94e99e572dbd` |
| https://arxiv.org/abs/2402.12840 | `ec5060d2f18089a5560ceec84a7c8393933280514b505c7ef506bcfc55f2f7a3` |
| https://huggingface.co/datasets/MBZUAI-Paris/DarijaMMLU/raw/main/README.md | `a8fc1cad343e5f3bc627875aaa17b4e6df608af5c873ba1a07f9d6bb053e8fd3` |
| https://arxiv.org/abs/2407.12402 | `e21a9605a3b50992cc198ac45899419fcc6d04f290eda9d8f892e03e73ac615f` |
| https://arxiv.org/abs/2502.12829 | `771a3c8be8edee67df5165b298b0f62770fb268ae082ff8cf71e6af85bee1fa7` |
| https://arxiv.org/abs/2404.06644 | `f45dd165d13e610a867ae8ec1515dc4de5a5fd395435c2014089f199eda66f66` |
