# Lineage audit: the 39 calibration components, 2026-11-02

## Scope

R-2026-11-02-j and -u created a cited, component-level lineage registry, `sources/lineage.yaml`, and
left it empty. R-2026-11-02-i asks the implementation work to audit pairwise lineage, keep the
evidence and status for each pairing, and run a sensitivity analysis with unverified pairings
excluded and, hypothetically, treated as independent, before any published score changes. This is
that audit for the four calibration sets.

The components are the `component` values on official-evaluation entries in
`sources/scores/{flores-plus,thai-exam,sea-helm,afrobench}.yaml`: 39 in all. Before this pass,
`build.validate` warned that none of them had a registry entry. Each now has one curated record,
written from what its cited sources state, and the warning is gone.

What changed: `sources/lineage.yaml` (34 collections, 39 components, no `relationships`), this
record and a CHANGELOG line. No score, coverage entry, schema or code changed, and no band moved.
The depth ladder is not built, so nothing reads the registry yet.

## What was read

- The rulings: R-2026-11-02-g (one component per task), -h (independence), -i (unverified pairs),
  -j and -u (the registry), and -k (the corroboration formula).
- `docs/reference/capability.md`, "Per-language coverage" and "Component lineage";
  `docs/schemas/lineage.schema.json`; `build/lineage.py`; `tests/fixtures/lineage/registry.yaml`.
- Every source the four score files cite that speaks to where a component's items came from, re-read
  on 2026-11-02, and 27 sources no score file cites: the papers or cards of the components
  themselves (XNLI, XCOPA, XQuAD, TyDi QA, IndicXTREME, IndicXNLI, IndoNLI, XL-Sum, MLHSD, ViHSD,
  MABL, Batayan, IrokoBench's full text, MasakhaPOS, NollySenti, Uhura, AfriSenti, MasakhaNEWS, the
  OpenAI MMMLU card, the MT-Bench Thai card, the Thai Toxicity Tweet, Wisesight and UIT-VSFC cards,
  the SALT card, the XCOPA README and the FLORES+ data-card listing).
- Fetched and not cited, because a cited source already states what the registry records: the
  BHASA abstract (arXiv 2309.06085), the MasakhaPOS and NollySenti abstracts (their full texts are
  cited instead), the IndicXTREME abstract, the XL-Sum and Uhura full texts, and the Hub cards of
  AfriXNLI, AfriMMLU and AfriMGSM.

All were fetched with `uv run python -m build.fetch_source`. A script checked every quoted fragment
in every `shows` against the body it cites (143 fragments, none missing). Where a body was
byte-identical to the one a score file already cites, the registry reuses that citation's `accessed`
date and digest; Hub and arXiv HTML pages changed since 2026-11-01, so those are cited at today's
digest. [Sources read](#sources-read) lists them all.

## How the records were written

- **A collection is a specific example set.** FLORES-200's sentences, newstest2019, MMLU's test
  questions, XNLI's English pairs, COPA, SQuAD v1.1, IFEval's prompts, MT-Bench's prompts, SmSA,
  MAFAND-MT and so on. Wikipedia, news, Twitter and the like go in `domains`, which never decides
  anything.
- **`parents` only when the component carries the parent's own text in the language.** SIB-200 and
  Belebele reuse FLORES-200's sentences verbatim in every language, so both name `flores-plus` as a
  parent and inherit its per-language effort. A component that made its own text from shared source
  examples names the shared collection instead: Batayan re-translated FLORES-200's sentences, so it
  names `flores-200`; AfriXNLI and IndicXNLI translated XNLI's English pairs, so they name
  `xnli-english`. Either way the pair is dependent: a shared ancestor's collection counts, and so does
  a shared collection.
- **`original` when the component collected or wrote its source examples itself**, even if it then
  translated them (FLORES+, XNLI, IndicSentiment, NollySenti, SALT). **`derived` when the examples
  came from an existing set** (NTREX-128 from newstest2019, XCOPA from COPA, XQuAD from SQuAD, the
  MMLU translations, SIB-200 and Belebele from FLORES). MLHSD is `derived` because part of its text
  comes from earlier Indonesian hate-speech datasets; none of them is a component here.
- **`effort` names the work that produced the text in the language.** For a translated set it is
  the translation; for a collected corpus with new labels, the dataset's annotation; for ThaiExam,
  the examination bodies that wrote the questions. AfriMMLU, AfriXNLI and AfriMGSM share
  `irokobench-translation`: the IrokoBench paper describes one translation process per language that
  "started with XNLI, then MGSM and MMLU", and no source states separate translator pools. FLORES-101
  and FLORES-200 translations share one effort; merging them can only make a pair more dependent.
- **`sea-helm` has a task override for every task its entries use**, since SEA-HELM's own items
  have different origins: SEA-IFEval from IFEval, SEA-MTBench from MT-Bench, Kalahi's multiple-choice
  set written with native Filipino speakers, and LINDSEA handcrafted by linguists. The canonical
  record is `origin: unknown`, so any task added later without an override reads as unverified. The
  four overrides select disjoint tasks, as validation requires.
- **Language overrides** only where a source states that the effort or source differs:
  FLORES+'s OLDI-carded languages, MasakhaPOS's MAFAND-MT languages, and NusaX's Indonesian, which is
  SmSA's own text rather than a NusaX translation.

## The registry

| Component | Origin | Collections | Parents | Effort | Overrides | Cited to |
|---|---|---|---|---|---|---|
| `flores-plus` | original | `flores-200` | none | `flores-200-translation` | 25 languages: effort null | [FLORES+ card](https://huggingface.co/datasets/openlanguagedata/flores_plus), [NLLB abstract](https://arxiv.org/abs/2207.04672), [Belebele paper](https://arxiv.org/html/2308.16884), [FLORES+ data-card listing](https://huggingface.co/api/datasets/openlanguagedata/flores_plus/tree/main/dataset_cards) |
| `sib-200` | derived | none | `flores-plus` | `sib-200-annotation` |  | [SIB-200 abstract](https://arxiv.org/abs/2309.07445) |
| `belebele` | derived | none | `flores-plus` | `belebele-translation` |  | [Belebele paper](https://arxiv.org/html/2308.16884), [Belebele README](https://raw.githubusercontent.com/facebookresearch/belebele/main/README.md) |
| `batayan` | derived | `flores-200` | none | `batayan-native-retranslation` |  | [Batayan paper](https://arxiv.org/html/2502.14911), SEA-HELM tables (`datasets_and_prompts.md` in the SEA-HELM GitHub repository), [SEA-HELM paper](https://arxiv.org/html/2502.14301) |
| `ntrex-128` | derived | `newstest2019` | none | `ntrex-128-translation` |  | [NTREX README](https://raw.githubusercontent.com/MicrosoftTranslator/NTREX/main/README.md) |
| `afrimmlu` | derived | `mmlu` | none | `irokobench-translation` |  | [IrokoBench paper](https://arxiv.org/html/2406.03368), [AfroBench paper](https://arxiv.org/html/2311.07978) |
| `afrixnli` | derived | `xnli-english` | none | `irokobench-translation` |  | [IrokoBench paper](https://arxiv.org/html/2406.03368) |
| `afrimgsm` | derived | `mgsm` | none | `irokobench-translation` |  | [IrokoBench paper](https://arxiv.org/html/2406.03368), [IrokoBench abstract](https://arxiv.org/abs/2406.03368) |
| `openai-mmmlu` | derived | `mmlu` | none | `openai-mmmlu-translation` |  | [MMMLU card](https://huggingface.co/datasets/openai/MMMLU), [AfroBench paper](https://arxiv.org/html/2311.07978) |
| `uhura-arc-easy` | derived | `arc-easy` | none | `uhura-translation` |  | [Uhura abstract](https://arxiv.org/abs/2412.00948), [AfroBench paper](https://arxiv.org/html/2311.07978) |
| `injongo-intent` | original | `injongo-utterances` | none | `injongo-native-writing` |  | [Injongo abstract](https://arxiv.org/abs/2502.09814) |
| `afrisenti` | original | `afrisenti-tweets` | none | `afrisenti-annotation` |  | [AfriSenti abstract](https://arxiv.org/abs/2302.08956) |
| `masakhanews` | original | `masakhanews-articles` | none | `masakhanews-annotation` |  | [MasakhaNEWS abstract](https://arxiv.org/abs/2304.09972), [MasakhaNEWS card](https://huggingface.co/datasets/masakhane/masakhanews) |
| `masakhapos` | original | `masakhapos-news` | none | `masakhapos-annotation` | 11 languages: origin derived, collections mafand-mt | [MasakhaPOS paper](https://arxiv.org/pdf/2305.13989) |
| `masakhaner-x` | derived | `masakhaner` | none | null |  | [AfroBench paper](https://arxiv.org/html/2311.07978) |
| `nollysenti` | original | `nollysenti-reviews` | none | `nollysenti-translation` |  | [NollySenti paper](https://arxiv.org/pdf/2305.10971), [AfroBench paper](https://arxiv.org/html/2311.07978) |
| `salt` | original | `salt-sentences` | none | `salt-translation` |  | [SALT card](https://huggingface.co/datasets/Sunbird/salt) |
| `afrobench` | derived | `mafand-mt` | none | `mafand-translation` |  | [AfroBench paper](https://arxiv.org/html/2311.07978), [MAFAND card](https://huggingface.co/datasets/masakhane/mafand) |
| `thai-exam` | original | `thai-exam-questions` | none | `thai-national-exams` |  | [ThaiExam card](https://huggingface.co/datasets/typhoon-ai/thai_exam/raw/main/README.md), [Typhoon abstract](https://arxiv.org/abs/2312.13951) |
| `sea-helm` | unknown | none | none | null | instruction following: origin derived, collections ifeval, effort sea-ifeval-translation<br>text generation: origin derived, collections mt-bench, effort sea-mtbench-translation<br>knowledge exam: origin original, collections kalahi, effort kalahi-writing<br>natural language inference and text classification: origin original, collections lindsea, effort lindsea-writing | [SEA-HELM paper](https://arxiv.org/html/2502.14301), [SEA-IFEval card](https://huggingface.co/datasets/aisingapore/Instruction-Following-IFEval), [SEA-MTBench card](https://huggingface.co/datasets/aisingapore/MultiTurn-Chat-MT-Bench), [Kalahi card](https://huggingface.co/datasets/aisingapore/Cultural-Evaluation-Kalahi), [LINDSEA Pragmatics card](https://huggingface.co/datasets/aisingapore/Linguistic-Diagnostics-Pragmatics), [LINDSEA Syntax card](https://huggingface.co/datasets/aisingapore/Linguistic-Diagnostics-Syntax) |
| `sea-mt-bench-judge` | derived | `mt-bench` | none | `sea-mt-bench-judge-translation` |  | [SEA-MT-Bench-Judge card](https://huggingface.co/datasets/aisingapore/MultiTurn-Chat-MT-Bench-Judge) |
| `kalahi-judge` | derived | `kalahi` | none | `kalahi-writing` |  | [Kalahi-Judge card](https://huggingface.co/datasets/aisingapore/Cultural-Evaluation-Kalahi-Judge) |
| `mt-bench-thai` | derived | `mt-bench`, `mt-bench-thai-knowledge-iii` | none | `mt-bench-thai-annotation` |  | [MT-Bench Thai card](https://huggingface.co/datasets/ThaiLLM-Leaderboard/mt-bench-thai), [SEA-MTBench card](https://huggingface.co/datasets/aisingapore/MultiTurn-Chat-MT-Bench) |
| `nusax` | derived | `smsa` | none | `nusax-translation` | ind: effort smsa-annotation | [NusaX paper](https://aclanthology.org/2023.eacl-main.57.pdf), [SEA-HELM sentiment card](https://huggingface.co/datasets/aisingapore/NLU-Sentiment-Analysis) |
| `xnli` | original | `xnli-english` | none | `xnli-translation` |  | [XNLI abstract](https://arxiv.org/abs/1809.05053), [XNLI paper](https://arxiv.org/pdf/1809.05053), [SEA-HELM NLI card](https://huggingface.co/datasets/aisingapore/NLR-NLI) |
| `indicxnli` | derived | `xnli-english` | none | `indicxnli-machine-translation` |  | [IndicXNLI abstract](https://arxiv.org/abs/2204.08776) |
| `indonli` | original | `indonli-pairs` | none | `indonli-annotation` |  | [IndoNLI abstract](https://arxiv.org/abs/2110.14566) |
| `xcopa` | derived | `copa` | none | `xcopa-translation` |  | [XCOPA paper](https://arxiv.org/pdf/2005.00333), [XCOPA README](https://raw.githubusercontent.com/cambridgeltl/xcopa/master/README.md) |
| `xquad` | derived | `squad-v1-1` | none | `xquad-translation` |  | [XQuAD abstract](https://arxiv.org/abs/1910.11856) |
| `tydi-qa-goldp` | original | `tydi-qa` | none | `tydi-qa-annotation` |  | [TyDi QA abstract](https://arxiv.org/abs/2003.05002), [SEA-HELM QA card](https://huggingface.co/datasets/aisingapore/NLU-Question-Answering) |
| `indicqa` | original | `indicqa-paragraphs` | none | `indicqa-annotation` |  | [IndicXTREME paper](https://arxiv.org/pdf/2212.05409) |
| `indicsentiment` | original | `indicsentiment-reviews` | none | `indicsentiment-translation` |  | [IndicXTREME paper](https://arxiv.org/pdf/2212.05409) |
| `xl-sum` | original | `xl-sum-bbc` | none | `xl-sum-bbc` |  | [XL-Sum abstract](https://arxiv.org/abs/2106.13822), [SEA-HELM summarization card](https://huggingface.co/datasets/aisingapore/NLG-Abstractive-Summarization) |
| `mlhsd` | derived | `mlhsd-tweets` | none | `mlhsd-annotation` |  | [MLHSD paper](https://aclanthology.org/W19-3506.pdf), [SEA-HELM toxicity card](https://huggingface.co/datasets/aisingapore/Safety-Toxicity-Detection) |
| `thai-toxicity-tweet` | original | `thai-toxicity-tweets` | none | `thai-toxicity-tweet-annotation` |  | [Thai Toxicity Tweet card](https://huggingface.co/datasets/tmu-nlp/thai_toxicity_tweet) |
| `wisesight-sentiment` | original | `wisesight-messages` | none | `wisesight-annotation` |  | [Wisesight card](https://huggingface.co/datasets/pythainlp/wisesight_sentiment) |
| `uit-vsfc` | original | `uit-vsfc-sentences` | none | `uit-vsfc-annotation` |  | [UIT-VSFC card](https://huggingface.co/datasets/uitnlp/vietnamese_students_feedback) |
| `vihsd` | original | `vihsd-comments` | none | `vihsd-annotation` |  | [ViHSD abstract](https://arxiv.org/abs/2103.11528) |
| `multilingual-fig-qa` | original | `mabl-metaphors` | none | `mabl-native-writing` |  | [MABL paper](https://arxiv.org/pdf/2305.16171), [SEA-HELM metaphor card](https://huggingface.co/datasets/aisingapore/NLU-Metaphor) |

## Left without documented lineage

No component is wholly `origin: unknown` except the canonical `sea-helm` record, whose every used
task is overridden with documented lineage. Three gaps remain, and every pair they touch is
unverified:

- **`masakhaner-x`: effort null.** AfroBench says it is MasakhaNER reformatted as a generation
  task, so its origin is documented (`derived`, collection `masakhaner`). No source read for this
  audit says where MasakhaNER's Amharic and Luo sentences came from or who produced them, so an
  overlap with MAFAND-MT, which MasakhaPOS's Luo uses, cannot be ruled out.
- **`flores-plus` in 25 languages: effort null.** FLORES+ says "The datasets for some language
  varieties have individual datacards describing their creation", and its data-card directory has
  one for `apd`, `arg`, `ast`, `ccp`, `chv`, `cmn`, `dar`, `fil`, `frp`, `kaa`, `kjh`, `lij`,
  `lld`, `mfe`, `mhr`, `myv`, `nob`, `seh`, `tyv`, `udm`, `uzs`, `vmw`, `wuu`, `yue` and `zgh`. The
  cards are gated (HTTP 401), so who produced those texts is not stated anywhere readable. Their
  collection stays `flores-200`, so their dependence on SIB-200 and Belebele still holds. Languages
  that only gained a second variety with its own card (`cat`, `khk`, `lmo`, `mni`, `nya`, `oci`,
  `tso`) keep the FLORES-200 effort.
- **`sea-helm` outside its four overridden tasks.** None of its coverage entries falls there today.

None of these touches a qualifying entry in the calibration sets: `masakhaner-x`'s entries have
`unknown` provenance, and no suite's FLORES entry is in an OLDI-carded language that counts. That
is why the two sensitivity runs below agree.

## Findings that change an earlier reading

- **Batayan is dependent on FLORES, not unverified.** R-2026-11-02-i ruled it unverified because no
  source then stated its origin. The Batayan paper does: its machine translation task "leveraged the
  Filipino subset of FLORES 200", whose translations the authors found "of subpar quality", so "these
  were re-translated". Table 1 lists it as "Filipino English-adapted Native re-translation", and
  SEA-HELM's paper lists FIL under FLORES in its translation row. New translations of the same source
  sentences are dependent under R-2026-11-02-h, so Batayan and FLORES+ share the `flores-200`
  collection. The finding moves no band: SEA-HELM has no FLORES+ entry for Filipino, and Batayan's
  backing comes from SEA-HELM's own Filipino items.
- **NollySenti's translations are documented.** The calibration recorded NollySenti's Hausa, Igbo and
  Yoruba entries as `unknown` provenance because no fetched source described them. Its paper says "We
  hire professional translators in Nigeria and ask them to translate 1,010 reviews randomly chosen
  from the 1,900 English reviews." This audit changes no coverage entry. A fill pass could record
  those entries as `human_translated`; at 500 items each that would add a band-3 component on text
  classification for three languages that already reach 4 or 5.
- **MasakhaPOS is partly MAFAND-MT.** Its Table 1 gives MAFAND-MT as the source for eleven of its
  twenty languages, which makes it dependent on AfroBench's own AfriADR (also MAFAND-MT) in
  Ghomala, Fon and Wolof. Both carry `unknown` provenance, so this moves nothing today.

## Pairwise statuses that matter

247 distinct pairs of components share a language in some calibration set. Counted once per status
they receive (three pairs get different statuses in different languages), 227 statuses are
independent, 11 dependent and 12 unverified, and all twelve unverified ones involve `masakhaner-x`.
The ones that decide a corroborated band:

| Pair | Status | Why | Where it binds |
|---|---|---|---|
| `flores-plus` and `sib-200` | dependent | SIB-200 derives from FLORES+ | 48 AfroBench languages; for 23 of them these are the only two qualifying components |
| `flores-plus` and `belebele` | dependent | Belebele derives from FLORES+ | 15 AfroBench languages; `ary`, `arz` and `bam` have nothing else |
| `belebele` and `sib-200` | dependent | shared `flores-200` | `tso` has nothing else |
| `afrimmlu`, `afrixnli`, `afrimgsm` | dependent | shared `irokobench-translation` | 15 or 16 languages; moves nothing, since each also has an independent backer |
| `mt-bench-thai` and `sea-mt-bench-judge`; `sea-helm` (text generation) and `sea-mt-bench-judge` | dependent | shared `mt-bench` | same task, so never a backing pair |
| `afrimmlu` and `openai-mmmlu` | dependent | shared `mmlu` | same task, so never a backing pair |
| `ntrex-128` and the IrokoBench, OpenAI MMMLU, Uhura, InjongoIntent, Belebele and SIB-200 components | independent | newstest2019 is disjoint from MMLU, XNLI, MGSM, ARC-Easy, InjongoIntent's utterances and FLORES-200 | carries the 13 AfroBench languages at 4 and Swahili and Yoruba at 5 |
| `flores-plus` and the IrokoBench components or `injongo-intent` | independent | disjoint collections and efforts | carries `lin`, `lug`, `sot` and `twi` at 3 |
| `ntrex-128` and `sib-200` | independent | as above | carries `bem`, `nya`, `plt`, `som` and `ssw` at 3 |
| `flores-plus` and SEA-HELM's own items, IndoNLI, XNLI, XCOPA, IndicSentiment and the classification sets | independent | disjoint collections and efforts | carries `ind`, `tam`, `tha` and `vie` at 3, and `zsm` at 2 |
| `batayan` and SEA-HELM's own Filipino items (SEA-IFEval, Kalahi) | independent | `flores-200` is disjoint from IFEval and Kalahi | carries `fil` at 3 |
| `nusax` and `multilingual-fig-qa` against SEA-HELM's own Javanese and Sundanese items | independent | disjoint | `jav` and `sun` stay 2 because every component there is a 2 |

Two imports of one task never back each other (R-2026-11-02-k), so `tsn` (FLORES+ and NTREX-128,
both translation), `nde` and `ven` (NTREX-128 only), `taq` (FLORES+ only) and `fuv` (SIB-200 only)
stay at 1 whatever their lineage.

## Sensitivity (R-2026-11-02-i)

### Method

A scratch script, kept outside the repository, applied R-2026-11-02-k to each calibration set:
D = max(O, max over imported components i of min(b_i, C_i + 1)), where O is the best band among the
product's own components (component equal to the product slug, plus SEA-HELM's `sea-mt-bench-judge`
and `kalahi-judge`), b_i an imported component's count band, and C_i the best band among the
language's other qualifying components that are independent of i under `build.lineage.pair_status`
(own components on any task, imported ones on a different task), each passed its own task and
split. Count bands: 1 from 1 item, 2 from 100, 3 from 400, 4 from 1,600, 5 from 6,400. Only
official-evaluation entries with `native`, `human_translated` or `post_edited` provenance, or
`mixed` with a `qualifying_count`, qualify. Each import is capped individually, so within a task the
highest single component's corroborated band is what counts (R-2026-11-02-g). A target language with
no measuring entry is unknown; the set's band is the median over target languages with unknowns
filled at 0 and at 5, and "unresolved" when the two differ. Run (a) counts only `independent` pairs
as backing; run (b) also counts `unverified` ones. The same script with an empty registry reproduces
the earlier results.

### Results

| Set | Earlier result (empty registry, every pair unverified) | (a) unverified excluded | (b) unverified as independent | Measured languages by band, (a) and (b) |
|---|---|---|---|---|
| FLORES+ | 3 | **3** | **3** | 0: 3, 3: 185 (27 unknown of 215) |
| ThaiExam | 3 | **3** | **3** | 3: 1 |
| SEA-HELM | 2 | **2** | **2** | 1: 3, 2: 3, 3: 5 |
| AfroBench | 1 | **1** | **1** | 1: 32, 3: 9, 4: 13, 5: 2 (7 unknown of 63) |

(a) and (b) agree in every set and every language. The registry's only unverified pairs involve
`masakhaner-x`, whose entries do not qualify, so treating them as independent backs nothing.

### Which languages move, and why

Against the empty registry under (a), the registry raises no set's band and moves these languages:

- **SEA-HELM.** `ind`, `tha` and `vie` go from 2 to 3, and `tam` from 1 to 3: FLORES+'s 1,012
  sentences (band 3) are now backed by an independent band-3 component on another task (IndoNLI,
  XNLI, XCOPA, IndicSentiment or a classification set), and those components are backed by FLORES+ in
  turn. `fil` goes from 2 to 3: Batayan's 600 sentences are backed by SEA-HELM's own Filipino items.
  `zsm` goes from 1 to 2: FLORES+ is backed only by SEA-MT-Bench-Judge's 58 prompts, a 1. `khm`,
  `lao` and `mya` stay at 1, since FLORES+ is their only component. `jav` and `sun` stay at 2. The
  median of 11 stays 2.
- **AfroBench.** 24 languages rise: `swa` and `yor` to 5 (OpenAI MMMLU's 14,042 questions backed by
  NTREX-128); `afr`, `amh`, `ewe`, `hau`, `ibo`, `kin`, `nso`, `orm`, `sna`, `tir`, `wol`, `xho` and
  `zul` to 4 (NTREX-128's 1,997 sentences backed by an independent band 3); `bem`, `lin`, `lug`,
  `nya`, `plt`, `som`, `sot`, `ssw` and `twi` to 3. 32 stay at 1: the 27 measured only on FLORES+,
  SIB-200 and Belebele, which are one piece of evidence, plus `fuv`, `nde`, `taq`, `tsn` and `ven`.
  With 32 of 63 target languages at 1, the median is 1 even with all seven unknowns
  (`ach`, `arq`, `bbj`, `lgg`, `nyn`, `pcm`, `teo`) at 5.
- **FLORES+ and ThaiExam** have one component each, which is their own, so lineage cannot move them.

Against the empty registry under (b), which is the first draft's "distinct components count as
independent" reading, the registry lowers 27 AfroBench languages from 3 to 1 (the FLORES-only
languages above) and takes AfroBench from 3 to 1. That is known dependence, not missing
documentation, which is the distinction R-2026-11-02-i asked the sensitivity run to make.

### Against the earlier results

The earlier results under the brief's script were FLORES+ 3, ThaiExam 3, SEA-HELM 2 and AfroBench 1,
which R-2026-11-02-k accepted as the provisional corroborated bands. The registry gives the same four
bands under both runs, so no result here differs from them.

One comparison needs a note. The methodology brief's "full definition" row
([`2026-11-02-language-depth-methodology.md`](../briefs/2026-11-02-language-depth-methodology.md))
gave AfroBench "unresolved (1-3)", with 30 languages at 1 and 9 unknown. The records have changed
since: the language-code reconciliation added `nde` and `ven` (each NTREX-128 only, so 1) and took
`nqo` and `por` out of the target population (both were unknown). With 32 at 1 and 7 unknown, the
median no longer depends on the fill, and AfroBench is a resolved 1 under the same definition. The
brief's SEA-HELM distribution (1: 2, 2: 4, 3: 4, Lao unmeasured) is now 1: 3, 2: 3, 3: 5, because Lao
gained a FLORES+ entry (1) and Filipino gained its Batayan entry (3); the median is 2 either way.

### One modeling choice that would move a language

If Batayan were recorded as a child of `flores-plus` instead of naming the `flores-200` collection,
its closure would include FLORES+'s Filipino text, which has a gated OLDI card and so no documented
effort. Its pairs with SEA-HELM's own Filipino items would become unverified, and `fil` would be 2
under (a) and 3 under (b). SEA-HELM's median stays 2 either way. The record names the collection
because Batayan's Filipino text is its own re-translation of FLORES-200's sentences, not FLORES+'s
current Filipino text.

## Not established

- Who produced FLORES+'s text in the 25 OLDI-carded languages, and whether FLORES+'s `fil` text is
  FLORES-200's Tagalog relabeled or recreated. Both sit behind the Hub gate.
- Where MasakhaNER's Amharic and Luo sentences came from, and so whether MasakhaNER-X overlaps
  MAFAND-MT or MasakhaPOS.
- Whether SEA-MT-Bench-Judge's translations are the same ones SEA-MTBench uses. The record gives
  them separate efforts; the shared MT-Bench prompts make them dependent regardless.
- Who translated SALT. The card says each sentence "is translated into all languages" and names the
  collaborating institutions, not the translators. The effort is recorded as SALT's own; its entries
  carry `unknown` provenance, so this moves nothing.
- XNLI's translators. The XNLI abstract says XNLI extended MultiNLI's development and test sets to 15
  languages and SEA-HELM's Table 1 marks it human-translated; the registry records the effort as
  XNLI's own translation without naming who did it.

## Sources read

All fetched with `uv run python -m build.fetch_source`, HTTP 200 unless noted. A source cited at
2026-11-01 or 2026-09-24 returned a byte-identical body on 2026-11-02 and keeps the score file's
citation. One more fetch is not cited: a FLORES+ data card itself
(`dataset_cards/apd_Arab.md` under the dataset's `resolve/main` path), which returned HTTP 401.

| URL | Accessed | sha256 |
|---|---|---|
| FLORES+ card: https://huggingface.co/datasets/openlanguagedata/flores_plus | 2026-11-02 | `9a32fd3840e9b6b28c1896b1f78b0c7ad8a79e24ae90d617cc6206b31dbf8bd9` |
| NTREX README: https://raw.githubusercontent.com/MicrosoftTranslator/NTREX/main/README.md | 2026-11-01 | `d00240af5232e2b89d1e1fb1af23117339fabee04d0d01f72df64162cc207f35` |
| MMMLU card: https://huggingface.co/datasets/openai/MMMLU | 2026-11-02 | `9dd8d63231b6a41327257daba8fa801707c5f0170e497bb2aa3474f352968745` |
| XNLI paper: https://arxiv.org/pdf/1809.05053 | 2026-11-02 | `220fe6b9bf048b4b9fb9016db10bddd2752fe2b2aa34519af20bc727efdf81e5` |
| XCOPA README: https://raw.githubusercontent.com/cambridgeltl/xcopa/master/README.md | 2026-11-02 | `9e6fea9f512dba9616cfa3f22cc77a557636a14100da2dc92493e9828e0a7058` |
| XQuAD abstract: https://arxiv.org/abs/1910.11856 | 2026-11-02 | `d4c8a13c0fd5003dec879f5be392b5f617976f3e37558d933e4e2e9b7348a533` |
| MT-Bench Thai card: https://huggingface.co/datasets/ThaiLLM-Leaderboard/mt-bench-thai | 2026-11-02 | `bfc5a658080315e32a341509b901997208590875a54888a4273ccc364bdc8668` |
| NusaX paper: https://aclanthology.org/2023.eacl-main.57.pdf | 2026-11-01 | `0f2224a02e1d74cfb2410e82ee15f87bce5495bde6a3fe5f26b4bdc56af5e1f0` |
| MAFAND card: https://huggingface.co/datasets/masakhane/mafand | 2026-11-02 | `f488da444ac3cacc35fd93c7cda0db9883e8a0a79ca055004d08242d9d8aab4c` |
| MasakhaPOS paper: https://arxiv.org/pdf/2305.13989 | 2026-11-02 | `921e095268f5611ce5146cdb50bfdb22ae2b848da4d939c0fcc93ecebbe324f2` |
| NLLB abstract: https://arxiv.org/abs/2207.04672 | 2026-11-01 | `4807d538486a3ff6cddf0be6c796025e47074b13a857f86101059b7c3d3c3969` |
| Belebele paper: https://arxiv.org/html/2308.16884 | 2026-11-01 | `5ebf36305c18085e44fa25a809dddf037afb04823923ff10d70c3224e1ebb535` |
| FLORES+ data-card listing: https://huggingface.co/api/datasets/openlanguagedata/flores_plus/tree/main/dataset_cards | 2026-11-02 | `c6e1fb3ff0df5f6cbcd573e4ecb636fe14b90590dee15cf4bae53b8d122983c9` |
| SIB-200 abstract: https://arxiv.org/abs/2309.07445 | 2026-11-01 | `3871243edcb5f0682a105baebbb2645d6297a6947280f15627375e4b66c11cd4` |
| Belebele README: https://raw.githubusercontent.com/facebookresearch/belebele/main/README.md | 2026-11-01 | `f7a9aead9af9056c96837eeb8eafa301ec37a4512e52520f1c3d7903b69ce145` |
| Batayan paper: https://arxiv.org/html/2502.14911 | 2026-11-02 | `da7a50bbce3c255e526fef6061fbce9fb8f4d034b26cb61d7d9b09f3f199a093` |
| SEA-HELM tables: `datasets_and_prompts.md` in the aisingapore/SEA-HELM GitHub repository, raw from its `main` branch | 2026-11-02 | `3cb8b1610ffe510997301fb267f6717bf63c574596a7aa4472a1f2f94d20135f` |
| SEA-HELM paper: https://arxiv.org/html/2502.14301 | 2026-11-02 | `f8685c55a37769a70027bb5c1cb8a227e448156727dce92b9bdea48493036b8d` |
| IrokoBench paper: https://arxiv.org/html/2406.03368 | 2026-11-02 | `8d5940c1e236940dece89ef505c206ccd3f0dd8724e93d73ff7f0cac8e56e698` |
| AfroBench paper: https://arxiv.org/html/2311.07978 | 2026-11-01 | `ef2b0d2751fd66adfd660ee0f45c3e2c928ff04cf846b4c5b7130df0243f6822` |
| IrokoBench abstract: https://arxiv.org/abs/2406.03368 | 2026-11-01 | `53df52b2305ce9322362d95a290fc44871149d7211bf434eb8557ea8bc89f1a5` |
| Uhura abstract: https://arxiv.org/abs/2412.00948 | 2026-11-02 | `62db8e36844c6777f3edad6b1bba1cc12c85cde5d92fd6e24d063b998965d05c` |
| Injongo abstract: https://arxiv.org/abs/2502.09814 | 2026-11-02 | `26b9d6c7e6d3850bd0e75eeeba2fb75930f71484925b5289ec6518c0d5bfc863` |
| AfriSenti abstract: https://arxiv.org/abs/2302.08956 | 2026-11-02 | `1675c998f0bb6fa06b9094d642b5c14de93793ac6bb001f8ed8cde513df1f78d` |
| MasakhaNEWS abstract: https://arxiv.org/abs/2304.09972 | 2026-11-02 | `bc2ef8ef9b5c43e3dc779800399af8a6f525c43b6ba8f27f866aeacbbfd5d898` |
| MasakhaNEWS card: https://huggingface.co/datasets/masakhane/masakhanews | 2026-11-02 | `b9bba47e2c9481fea984fd70d684f330be805ea0dcbf58aa64a5ae3c6730807b` |
| NollySenti paper: https://arxiv.org/pdf/2305.10971 | 2026-11-02 | `82e66680790296604f29808ffe4afeaf93c5506085585779cb5d785408d11082` |
| SALT card: https://huggingface.co/datasets/Sunbird/salt | 2026-11-02 | `e31f5ffd14dd69622fddc675a0de62995095ced977b42c76e84d78fcdba5b14c` |
| ThaiExam card: https://huggingface.co/datasets/typhoon-ai/thai_exam/raw/main/README.md | 2026-09-24 | `860459e28fcaf606f68f1fb40bbdb9bd6b47e74c62fb390e37ac133c0b53b3ff` |
| Typhoon abstract: https://arxiv.org/abs/2312.13951 | 2026-11-02 | `c68254a369ca65b2980596deec80896f7134135b6afcacade7421c029ed2c74f` |
| SEA-IFEval card: https://huggingface.co/datasets/aisingapore/Instruction-Following-IFEval | 2026-11-02 | `aa3e283f62eaf02aa7855ba24aa3022f6c86748349fa3fe81c9a123e619b41fb` |
| SEA-MTBench card: https://huggingface.co/datasets/aisingapore/MultiTurn-Chat-MT-Bench | 2026-11-02 | `c1ede97f6a6759547a32987e9f0d2bb9c8a601515eb803cf30f6948706585699` |
| Kalahi card: https://huggingface.co/datasets/aisingapore/Cultural-Evaluation-Kalahi | 2026-11-02 | `7370d321af7e64125d60ac4c96535a9d18b78ad49a0d9af3582f50484b4de71f` |
| LINDSEA Pragmatics card: https://huggingface.co/datasets/aisingapore/Linguistic-Diagnostics-Pragmatics | 2026-11-02 | `6de4f2a1605fb70e92b59721c6625c3aae4b7130456f990e7f45fd8fcccf6d56` |
| LINDSEA Syntax card: https://huggingface.co/datasets/aisingapore/Linguistic-Diagnostics-Syntax | 2026-11-02 | `f47427b5c6994b9707ba31082e3660b1f12ff5ead48dd8c13b45500702dab9bf` |
| SEA-MT-Bench-Judge card: https://huggingface.co/datasets/aisingapore/MultiTurn-Chat-MT-Bench-Judge | 2026-11-02 | `edf85c8d34d7445766aaa42802f02a5e689d27b0492bd69220bc24f0f2a90d91` |
| Kalahi-Judge card: https://huggingface.co/datasets/aisingapore/Cultural-Evaluation-Kalahi-Judge | 2026-11-02 | `a225b51958b6675edf80695cd2f4917553e02861498a1776b58ae0b6cb4ceace` |
| SEA-HELM sentiment card: https://huggingface.co/datasets/aisingapore/NLU-Sentiment-Analysis | 2026-11-02 | `5d5baec03654ba5462d13189a43e209c9b9fc048abe7823cbbdceaafa9bf122e` |
| XNLI abstract: https://arxiv.org/abs/1809.05053 | 2026-11-02 | `1cb3568655b7fe32880111e036e1b5ef5d2e27ba3f63bcfc4ae52e38ecee3649` |
| SEA-HELM NLI card: https://huggingface.co/datasets/aisingapore/NLR-NLI | 2026-11-02 | `43336824c106532e433dc70c39fe4bab72c6db1b8d5f7e49a9a7a0103a86ff17` |
| IndicXNLI abstract: https://arxiv.org/abs/2204.08776 | 2026-11-02 | `f2caec053c5f48092f03c8c5c716b002f8e1a0de4ba2bd3fdd430cc020b37721` |
| IndoNLI abstract: https://arxiv.org/abs/2110.14566 | 2026-11-02 | `9aa219bbbf48a121273c98eee30447ea18da66afb724a1333853cf3106e95d76` |
| XCOPA paper: https://arxiv.org/pdf/2005.00333 | 2026-11-02 | `3e9886db5983db5da6be884d6e778ef233745c0df9f360dab110b004ebb40943` |
| TyDi QA abstract: https://arxiv.org/abs/2003.05002 | 2026-11-02 | `9ffde4aa47fb1c61ed80c60b4723474b8238d97345cb78490a374641ca74001e` |
| SEA-HELM QA card: https://huggingface.co/datasets/aisingapore/NLU-Question-Answering | 2026-11-02 | `c6bbce2ff4ba0a2a635424131506b504c87d9b51e7cd9462bec06c1e9900a1b6` |
| IndicXTREME paper: https://arxiv.org/pdf/2212.05409 | 2026-11-02 | `8557a53823518382dec3a2b9fbccfa8eafe5e7a3707e80b1fec6b0a1298b3437` |
| XL-Sum abstract: https://arxiv.org/abs/2106.13822 | 2026-11-02 | `9eeed97d9be515ee7cd860ef39c09c40a03f3b059b18cf51ea0eb53fedfba4fd` |
| SEA-HELM summarization card: https://huggingface.co/datasets/aisingapore/NLG-Abstractive-Summarization | 2026-11-02 | `db9393ff683582f5ddf543addec964cc8a015d15fe96a040a17006ff5017e51d` |
| MLHSD paper: https://aclanthology.org/W19-3506.pdf | 2026-11-02 | `7e63c3c8e59f429f41dbeeb1c0b7215ec89a99e112ae343d493358148666a0fc` |
| SEA-HELM toxicity card: https://huggingface.co/datasets/aisingapore/Safety-Toxicity-Detection | 2026-11-02 | `bf549474bbe51041544485f90390a3dabab84e2e6caa7dd734bc8987ab2d3e2a` |
| Thai Toxicity Tweet card: https://huggingface.co/datasets/tmu-nlp/thai_toxicity_tweet | 2026-11-02 | `205d529b88ad26cf994658b3f422fdeab12ed097d2b1de901d2f71b1d930debf` |
| Wisesight card: https://huggingface.co/datasets/pythainlp/wisesight_sentiment | 2026-11-02 | `3147cde790eaaed36a468ef0f48c5e944fd0ebd7f0f5325dfadcc14f42523a2c` |
| UIT-VSFC card: https://huggingface.co/datasets/uitnlp/vietnamese_students_feedback | 2026-11-02 | `67ee2b6dd18f2ba9e774c8fc954601c3c6308cdd9a519e9dba45c08d08a508ab` |
| ViHSD abstract: https://arxiv.org/abs/2103.11528 | 2026-11-02 | `2e17616a97de06c893e237c7843f29a068b774375de5449472871e2ab07c5a59` |
| MABL paper: https://arxiv.org/pdf/2305.16171 | 2026-11-02 | `2fea7493e63b0ce4635f5f3460da5ae18655fbc6a09c8c16b211fcfcdb413932` |
| SEA-HELM metaphor card: https://huggingface.co/datasets/aisingapore/NLU-Metaphor | 2026-11-02 | `483eb8b8f2dd43c640c2efcf76959b85bc7706c650c20030e0235e950eadceda` |
