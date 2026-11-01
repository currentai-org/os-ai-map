# Language depth calibration: four records and proposed task bands, 2026-11-01

## Scope

R-2026-11-01-g: before the per-language evidence is filled for every evaluation set, populate a
calibration sample (FLORES+, ThaiExam, SEA-HELM, AfroBench), use it to settle the task-specific depth
bands, and check that the aggregation gives sensible, explainable outcomes. This record holds both
halves:

- **The records.** `capability.pivot_languages` and `capability.language_coverage` are now filled on
  `sources/scores/{flores-plus,thai-exam,sea-helm,afrobench}.yaml`, under the schema and rules in
  `docs/reference/capability.md` ("Per-language coverage") and the clarifications of 2026-11-01 (a
  language whose official entries are all `unknown`, or `mixed` without `qualifying_count`, is
  unmeasured; a single-component set names itself; a suite names its own items with its own slug).
  Every count is one a fetched source states for that language, task, component and split. No
  set-wide total was divided across languages (R-2026-10-30-l).
- **A dry run of the depth ladder.** Proposed task bands, one proposed rule for the unruled step
  from task bands to a language band, and the aggregation of `capability.md` ("How the depth ladder
  will read it") run by hand on all four records.

Nothing else moved. No `capability.score`, `relative_to`, `relation`, `value` or `note`, no recipe,
no roster and no product's `languages` changed, and the bands below are proposals, not adopted. The
records were revised after review; [Changes after review](#changes-after-review) lists what changed
and why.

**How the evidence is dated.** The records' evidence is dated by the `accessed` date of each source
their entries cite: 2026-11-01 for every source this pass fetched, and 2026-09-24 for four that were
already on the axes and are cited again (the NLLB abstract on FLORES+, the ThaiExam card README, and
SEA-HELM's dataset tables on ThaiExam and on SEA-HELM). `capability.last_verified` dates the band,
not the coverage record, and stays at 2026-09-24 on all four because no band was reassessed; see
[The confirmation date](#the-confirmation-date).

Every source this pass read was fetched on 2026-11-01 with `uv run python -m build.fetch_source`; the
records cite them through `capability.sources` with `shows`, `accessed`, `http_status` and
`content_sha256`, and [Sources read](#sources-read) lists them with their digests. The script that
built the entries from the fetched bodies checked that every quoted fragment in a new `shows` appears
in the body it cites, and the fragments added after review were checked the same way.

## The records

| Set | Entries | Target languages | With entries | Measured | Unmeasured or absent | Mapped entries | Documented zeros |
|---|---|---|---|---|---|---|---|
| FLORES+ | 400 | 203 (pivot `eng`) | 199 | 188 | 15 | 8 (4 languages) | 3 |
| ThaiExam | 2 | 1 | 1 | 1 | 0 | 0 | 0 |
| SEA-HELM | 62 | 11 (pivots `eng`, `zho`) | 10 | 10 | 1 | 1 | 0 |
| AfroBench | 275 | 63 (no pivot) | 62 | 54 | 9 | 3 (2 languages) | 0 |

"Measured" is the definition in `capability.md`: an official-split entry whose qualifying depth is
established, by a known provenance or by a documented zero, which counts only for its own
language, task, component and split. A mapped entry carries
`source_language`, because its source names the language with another code; it is an inferred
identity, listed in [Language codes](#language-codes-needs-reconciliation), and is counted as
measured here. Leaving the mapped entries out changes no proposed band (see the
[Hand-run](#hand-run)).

### How provenance was read

`native` is recorded only where a cited source says that the evaluated items, the text, questions or
references being scored, were written by people in that language. A card that describes its corpus
as news articles, tweets or reviews in the language says what the text is, not how it came to be in
the language, and is not enough on its own. `human_translated` and `post_edited` need a source that
says people translated or corrected the items; a source that says only "translated" gives `unknown`.
Where two sources disagree, the entry is `unknown` and cites both, and
[Provenance conflicts](#provenance-conflicts) quotes them.

One reading is a judgment the maintainer should confirm. SEA-HELM's paper marks each dataset in a
"Native" column, and its caption defines the column: "We curate datasets that are created in the
native language (indicated with "-") and translated datasets (either by humans or machines)". The
text adds "We selected datasets that comprised of data originally written in the native language as
far as possible". That is read as the statement the rule asks for, for every dataset Table 1 marks
native. SEA-HELM's GitHub tables use the same column ("Nativeness") and are read the same way where
they are the only source on provenance: ThaiExam ("Thai | Thai Exam | Native") and
Multilingual-Fig-QA in Javanese and Sundanese. LINDSEA and Kalahi need no such reading, since the
paper says how their items were written. If SEA-HELM's label alone is not enough, ThaiExam becomes
unresolved (its one language unmeasured, filled with 0 and with 5) and no SEA-HELM result moves: it
stays a 4 under the highest task band and a 3 under the median of tasks, because translation and
SEA-HELM's own described items carry its languages.

### Provenance conflicts

| Entries | Says native | Says translated | Recorded |
|---|---|---|---|
| SEA-HELM: `jav` and `sun`, `text_classification`, `nusax`, 394 items each | SEA-HELM's dataset tables (`datasets_and_prompts.md` in the aisingapore/SEA-HELM GitHub repository; full URL on both records): the sentiment table's rows "Javanese" and "Sudanese" (sic) read "Native", with no dataset named. The task card, <https://huggingface.co/datasets/aisingapore/NLU-Sentiment-Analysis>, says the items are "sampled from NusaX for Indonesian, Javanese, and Sundanese." | The NusaX paper, <https://aclanthology.org/2023.eacl-main.57.pdf>: "we take an existing dataset in a high-resource local language (Indonesian) as a base for expansion to the other ten languages, and ask human annotators to translate the text." | `unknown`, citing all three |

Neither side is picked. The first version of this record followed the NusaX paper and recorded
`human_translated`.

### FLORES+

One component (`flores-plus`), one task (`machine_translation`), two splits per language: `dev`, 997
sentences, `official_eval: false`; `devtest`, 1,012 sentences, `official_eval: true`. The card states
both counts for every language. `devtest` is marked official because FLORES+ does not carry the
benchmark's own test split ("The separate blind test set, originally developed by Meta, is not
managed by OLDI and not part of this repository") and the FLORES-101 paper says "The devtest is meant
to be used for testing purposes during the development phase". R-2026-11-01-d names the same split.

Provenance follows the language's history. A language on the FLORES-200 list with no FLORES+ data
card of its own is `human_translated`, cited to the FLORES-200 README, the card ("FLORES+ is based
on FLORES-200") and the NLLB abstract ("a human-translated benchmark, Flores-200"). English is
`unknown`: the card says "The original English sentences were sampled in equal amounts from
Wikinews", Wikijunior and Wikivoyage, and the FLORES-101 paper that "All source sentences were
extracted from multiple Wikimedia sources", which says where the sentences came from and not who
wrote them. English is the pivot, so this moves nothing. Unknown, with counts recorded:

- **Recreated or added by OLDI, data card behind the Hub gate (11):** `apd`, `ast`, `kjh`, `lij`, `lld`,
  `mfe`, `mhr`, `nob`, `yue`, `zgh`, `zho`. The card says these "have individual datacards describing
  their creation"; the cards are in the gated repository (HTTP 401), so how their current text was
  made is not stated anywhere this pass could read. `ast`, `lij`, `nob` and `yue` were in FLORES-200,
  but their FLORES+ text has its own card, so FLORES-200's provenance no longer describes it.

**Dev split only, documented zeros (3):** `dar`, `udm`, `uzs`. The card marks them "dev only". Each
has its `dev` entry (997 sentences, `unknown`, since they also carry OLDI cards) and a documented zero
on `devtest`: `count: 0`, no provenance, citing the card. Each is a measured zero for that language,
`machine_translation`, `flores-plus` and `devtest` only, and no longer unknown there. It says nothing
about any other task or component: FLORES+ has only this one, so each language's FLORES+ band is 0,
but the zero does not imply that Dargwa, Udmurt or Southern Uzbek lack evaluation coverage anywhere
else.

No entry, because the card no longer lists the product's code (4): `aka`, `kon`, `tgl`, `tzm`. Four
other product codes are recorded from the code the card uses and carry `source_language`: `ara` from
`arb`, `est` from `ekk`, `grn` from `gug`, `zho` from `cmn`. Both groups, and the card's codes the
product does not list, are in [Language codes](#language-codes-needs-reconciliation).

A language with two scripts or two varieties (`ace`, `apc`, `bjn`, `cat`, `kas`, `khk`, `knc`,
`lld`, `lmo`, `min`, `mni`, `nob`, `nya`, `oci`, `snd`, `taq`, `tso`, `twi`) has one entry per split,
with 1,012 sentences: the variants carry the same aligned sentence ids, so their items are not
distinct.

### ThaiExam

One component (`thai-exam`), `knowledge_exam`, `native`. The card describes "multiple-choice
questions from examinations in Thailand" (for IC, "The exam questions were developed by the Stock
Exchange of Thailand"), and SEA-HELM's dataset tables list "Thai | Thai Exam | Native"; both entries
cite both ([How provenance was read](#how-provenance-was-read)). The Hub's split sizes give the test
split per exam (ONET 162, IC 95, TGAT 65, TPAT-1 116, A-Level 127) and five few-shot examples per exam
in `train`. The record holds `test` 565, official, and `train` 25, not official. The card's per-exam
totals (167, 100, 70, 121, 132; 590 in all) include the few-shot examples, so the 590 in the current
capability `value` and `note` counts 25 items no model is scored on. That prose is left for the next
`refresh-category` pass, as this task does not touch the band's text.

### SEA-HELM

Counts come from the task repositories' Hugging Face cards, each of which has a per-split table.
Provenance comes from the paper's Table 1 (native, or translated by "Human" or "Machine"), from the
cards' "manually translated by native speakers", from the GitHub dataset tables where the paper is
silent, and from the NusaX paper for the Javanese and Sundanese items. Each split the card names by
language (`id`, `th`, `en_to_tha_Thai`) is recorded as `official_eval`; the `*_fewshot` splits are
left out (see the exposures). Imported datasets are named by their own slugs (`flores-plus`, `nusax`,
`xnli`, `xcopa`, `xl-sum` and so on); SEA-HELM's own items (SEA-IFEval, SEA-MTBench, LINDSEA, the
Kalahi multiple-choice set) are `sea-helm`. Translation records one entry per language for both
directions, since the card gives 1,012 sentences each way from the same FLORES sentences.

- **Unknown, no entry (1):** `lao`. No published card states a Lao count. The Belebele task card,
  which the GitHub tables say carries Lao, Malay, Burmese, Javanese and Sundanese reading
  comprehension, has an empty README.
- **Listed by the GitHub tables but with no published per-language count, so not recorded:**
  Filipino (Batayan) sentiment, QA, translation, NLI, causal reasoning, summarization and toxicity;
  Malay, Burmese and Lao sentiment and toxicity; SEA-NLI in eight languages; Global MMLU for
  Indonesian, Burmese, Vietnamese, Malay and Filipino; ThaiExam inside SEA-HELM; LINDSEA Tamil;
  SEA-MTBench for Malay, Burmese, Lao and Khmer. These are unknown, not absent.
- **Recorded with `unknown` provenance:** Javanese and Sundanese NusaX sentiment, where the sources
  disagree ([Provenance conflicts](#provenance-conflicts)); their NusaX translation items stay
  `human_translated`, which only the NusaX paper addresses. English on SEA-IFEval, SEA-MTBench and
  SEA-MT-Bench-Judge, whose cards say how the other languages were translated and nothing about how
  the English was made. English is a pivot.
- **Mapped (1):** Malay translation is recorded under the product's `msa` from the card's `zsm_Latn`
  and carries `source_language: zsm`.

### AfroBench

Counts come from three places, in this order of preference:

1. The member's Hub split sizes, where their sum equals the test total AfroBench's Table 2 gives for
   that dataset: MasakhaPOS (12,190), MasakhaNEWS (6,242), AfriSenti (37,670) and Uhura (3,257).
   InjongoIntent and NTREX are also read from the Hub (see the exposures for their small mismatches).
2. Table 2's single per-language size, over the languages Table 11 marks for that dataset: SIB-200
   204, NollySenti 500, AfriXNLI 600, Belebele 900, AfriMMLU 500, OpenAI MMMLU 14,042, AfriMGSM 250,
   FLORES 1,012, SALT 500. MasakhaNER-X has a stated size only for its two exceptions (Amharic 500,
   Luo 185). AfriADR, AfroBench's own task, is Table 3 (component `afrobench`).
3. Nothing else. Where neither gives a per-language figure the dataset has no entry.

- **Unknown, no entry (1):** `nqo`. No dataset in Table 11 covers N'Ko.
- **Unmeasured, entries all `unknown` provenance (8):** `ach`, `lgg`, `nyn`, `teo` (SALT only, whose
  card says each sentence "is translated into all languages" without saying by whom); `arq` and `por`
  (AfriSenti only); `pcm` (MasakhaPOS, MasakhaNEWS and AfriSenti); `bbj` (MasakhaPOS and AfriADR).
- **Recorded with `unknown` provenance:** NollySenti (Hausa, Igbo, Yoruba), MasakhaNER-X (Amharic,
  Luo) and SALT, which no fetched source describes, and four sets whose sources do not say the items
  were written by people in the language or translated by people:
  - AfriSenti: the card covers "110,000+ annotated tweets in 14 African languages".
  - MasakhaNEWS: the card is "the largest publicly available dataset for news topic classification
    in 16 languages widely spoken in Africa", and "The source language was produced by journalists
    and writers employed by the news agency and newspaper mentioned above", which says people wrote
    the text but not that it was written in the language rather than translated into it.
  - MasakhaPOS: "The source of the data is from the news domain"; AfroBench calls it "created from
    news articles".
  - AfriADR: AfroBench "selected the five languages with extensive use of diacritics from Mafand MT
    dataset" and stripped the diacritics; MAFAND's card says it was "translated from English or
    French to an African language" and does not say by whom.
- **Kept as `native`:** InjongoIntent, whose paper's abstract says it has "utterances generated by
  native speakers", against benchmarks that "rely on translations from English benchmarks".
- **Kept as `human_translated`, with one citation added:** SIB-200 and Belebele now also cite the
  NLLB abstract. Their own sources say their text is FLORES-200's ("The dataset is based on
  Flores-200 machine translation corpus"; "The passages in the Belebele corpus are directly sourced
  from the FLoRes-200 Machine Translation Benchmark"), and the NLLB abstract is the one that says
  FLORES-200 was human-translated.
- **Mapped (3):** Oromo's FLORES and SIB-200 entries come from Table 11's `gaz` row and carry
  `source_language: gaz`; Plateau Malagasy's NTREX-128 entry comes from the repository's `mlg_Latn`
  configuration and carries `source_language: mlg`.
- **Members with no entry at all:** AfriHate (per-language range only, repository gated), AfriQA (the
  card's test splits total 3,560, Table 2 says 3,107), MAFAND (card 29,600 against 29,155),
  MasakhaNER-X other than Amharic and Luo (card 17,285 against 18,192), NaijaRC (range only), XL-Sum
  (range only; the card has no per-language test table).

## Language codes: needs reconciliation

Every place where a record's codes and its sources' codes differ. Each row needs reconciliation; no
product's `languages` was changed. "Mapped" rows are entries recorded under the product's code with
the source's code in `source_language`: an inferred mapping, not a directly observed identity. A
two-letter code a card uses (`id`, `tl`, `sw`) is read as its ISO 639-3 equivalent and is not listed.

| Set | Product code | Source code | Kind | What the source states | Status |
|---|---|---|---|---|---|
| FLORES+ | `ara` | `arb` | mapped (2 entries) | card: `arb` Arab, Modern Standard Arabic; the FLORES-200 README's FLORES-101 map pairs "arb_Arab \| ara" | needs reconciliation |
| FLORES+ | `est` | `ekk` | mapped (2) | card: `ekk` Latn, Estonian | needs reconciliation |
| FLORES+ | `grn` | `gug` | mapped (2) | card: `gug` Latn, Paraguayan Guaraní | needs reconciliation |
| FLORES+ | `zho` | `cmn` | mapped (2) | card: `cmn` Hans and Hant, Mandarin Chinese | needs reconciliation |
| FLORES+ | `aka` | none | product lists, card does not | card has Akuapem and Asante Twi (`twi`) | needs reconciliation |
| FLORES+ | `kon` | none | product lists, card does not | card has Kituba (DRC), `ktu` | needs reconciliation |
| FLORES+ | `tgl` | none | product lists, card does not | card has Filipino, `fil` | needs reconciliation |
| FLORES+ | `tzm` | none | product lists, card does not | card has Standard Moroccan Tamazight, `zgh`, also listed by the product | needs reconciliation |
| FLORES+ | none | `arg`, `brx`, `ccp`, `chv`, `dgo`, `fil`, `frp`, `gom`, `kaa`, `ktu`, `myv`, `nqo`, `tyv`, `vmw`, `wuu` | card has, product does not list | Aragonese, Bodo (dev only), Chakma, Chuvash, Dogri (dev only), Filipino, Savoyard, Goan Konkani (dev only), Karakalpak, Kituba (DRC), Erzya, Nko, Tuvan, Emakhuwa (Central), Wu Chinese (dev only) | needs reconciliation |
| SEA-HELM | `msa` | `zsm` | mapped (1) | translation card: `zsm_Latn` | needs reconciliation |
| SEA-HELM | `tgl` | `fil` (by name) | not mapped | the cards' splits are `tl`; the paper's Table 1 and the GitHub tables name Filipino ("FIL"), which the paper says "is primarily based on Standard Tagalog" | needs reconciliation |
| AfroBench | `orm` | `gaz` | mapped (2) | Table 11's `gaz` row marks SIB-200 and Flores; its `orm` row marks the other Oromo datasets | needs reconciliation |
| AfroBench | `plt` | `mlg` | mapped (1) | NTREX repository configuration `mlg_Latn`; Table 11 marks NTREX-128 under `plt` | needs reconciliation |
| AfroBench | none | `ara`, `nde`, `ven` | source has, product does not list | Table 11: `ara` (OpenAI-MMLU, XL-SUM), `nde` and `ven` (NTREX-128) | needs reconciliation |
| AfroBench | `nqo` | none | product lists, source does not | no dataset in Table 11 | needs reconciliation |
| AfroBench | `por` | `por` (AfriSenti only) | product lists, Table 11 does not | AfriSenti's repository has a `por` (Mozambican Portuguese) configuration; Table 11 has no `por` row | needs reconciliation |

ThaiExam has no discrepancy.

## Proposed task bands

A count is the qualifying items on the official evaluation split: native, human-translated and
post-edited items, never added across tasks. Each ladder's lower bounds are in its task's own unit.

| Task (unit) | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Accuracy-scored tasks: `knowledge_exam`, `reasoning`, `reading_comprehension`, `question_answering`, `natural_language_inference`, `text_classification`, `sequence_labeling`; also `summarization` until calibrated (items, questions, sentences, documents) | 1 | 100 | 400 | 1,600 | 6,400 |
| `machine_translation` (sentences) | 1 | 100 | 500 | 1,000 | 1,500 |
| `instruction_following`, judged `text_generation` (prompts) | 1 | 20 | 80 | 250 | 500 |

**Accuracy-scored tasks.** On n items, the worst-case 95% margin of error on an accuracy is about
0.98/sqrt(n) points: plus or minus 10 at 100 items, 5 at 400, 2.5 at 1,600, 1.2 at 6,400. Each band
halves the margin, so a band says how finely a score on that language can separate two models.
Reference sets fall where their reputation puts them: MGSM 250 per language (2), XCOPA 500 (3),
AfriMMLU 500 and ThaiExam 565 (3), Belebele 900 (3), XNLI 5,010 test pairs per language (4), MMLU and
Global-MMLU 14,042 (5). The four calibration sets put most single datasets in 2 and 3, which is
what they hold: a few hundred to a thousand items per language.

**Translation.** Corpus-level translation metrics are read over a test set, and the field has two
reference sizes per language: a FLORES devtest (1,012) and a WMT news test set (newstest2019, which
NTREX-128 translates, 1,997). Band 4 starts at a FLORES devtest and band 5 sits between the two, so
the reference benchmark is a 4 and a WMT-scale set a 5. NusaX's 394 is a 2 and SALT's 500 a 3.

**Judged generation and instruction following.** Each prompt is a whole conversation or a set of
verifiable constraints, and judge-scored sets are small by construction. MT-Bench has 80 prompts
(band 3 starts there) and IFEval 541 (band 5 starts at 500). SEA-MTBench's 58 is a 2, SEA-IFEval's
105 a 3, MT-Bench Thai's 91 a 3.

Speech units (`hours`, `utterances`) and `transliteration` are not in the sample, so no ladder is
proposed for them. `summarization` is exercised only by SEA-HELM's 100 documents per language; it
uses the accuracy ladder as a placeholder.

## Proposed aggregation

These steps restate `capability.md`, plus two rules that are not ruled and are proposed here.

1. **Within a task (proposed, needs a ruling): the largest single component.** Where a language has
   several components for one task, its task band is the band of the component with the most
   qualifying items. Datasets for one task differ in domain and labels, so their scores are not
   pooled into one estimate, and a suite gets no credit for importing more of them (R-2026-11-01-c).
   Summing distinct components instead changes no set's band in this sample.
2. **From task bands to a language band (proposed, needs a ruling): the highest task band.** A
   language is as deep as the deepest task the set measures it on. Breadth of tasks does not add,
   which is the line R-2026-11-01-c draws, and a thin probe task cannot pull a language down. The
   median of the task bands was run as the sensitivity case.
3. **Across target languages: the median** of the language bands, pivots excluded (R-2026-10-30-i,
   R-2026-11-01-b). With an even count, the mean of the two middle values, rounded down.
4. **Robustness** (R-2026-11-01-a): fill every unmeasured target language with 0, then with 5; the
   band stands only if both medians give the same band.
5. **Completeness:** measured target languages over target languages. A documented zero is
   measured, with a band of 0, for its own task, component and split only; the language's other
   tasks are banded from their own entries.
6. **Tiebreak:** median + 0.5 x (1 - 1/n), n the measured languages with a band above zero, capped
   below the next band. It orders sets inside a band and is reported, not banded.

## Hand-run

Recomputed after review under the same proposed ladders and rules. No proposed band moved.

| Set | Current band | Proposed band | Completeness | Low fill / high fill | Tiebreak | Median rule (sensitivity) |
|---|---|---|---|---|---|---|
| FLORES+ | 5 | **4** | 188 of 203 | 4 / 4 | 4.50 | 4 |
| ThaiExam | 4 | **3** | 1 of 1 | 3 / 3 | 3.00 | 3 |
| SEA-HELM | 5 | **4** | 10 of 11 | 4 / 4 | 4.45 | 3 |
| AfroBench | 5 | **4** | 54 of 63 | 4 / 4 | 4.49 | 3 |

**FLORES+: 4.** Every measured language with items has one task, translation, with 1,012
human-translated devtest sentences, a 4 on the translation ladder. 188 of 203 target languages are
measured: 185 at 4, and the three dev-only languages at 0, as documented zeros. The 15 others are the
four codes the card no longer carries and the 11 languages whose OLDI cards are gated. Filling those
15 with 0 or with 5 leaves the median of 203 at 4, so the band stands. It falls from 5 because depth
is now measured absolutely: a FLORES devtest is the reference translation set, and the ladder keeps 5
for more than it holds.

**ThaiExam: 3.** One language, one task: 565 native exam questions on the test split, between 400
and 1,600, so a 3. Complete (1 of 1). The 25 few-shot examples are training-split items and do not
count. It falls from 4 because the current band compares it with peers across languages and tasks;
the depth ladder only asks how much Thai it holds. Its `native` rests on the reading of SEA-HELM's
label described in [How provenance was read](#how-provenance-was-read); without it, ThaiExam is
unresolved.

**SEA-HELM: 4.** Seven of the ten measured languages reach 4, and in every one of them the 4 comes
from the 1,012-sentence FLORES sample in translation: Indonesian, Khmer, Malay, Burmese, Tamil, Thai
and Vietnamese. Javanese, Sundanese and Tagalog reach 3 on SEA-IFEval's 105 prompts. Its best
non-translation task in any language is a 3 (1,000-item sentiment, toxicity or NLI sets). Lao is
unmeasured; filling it with 0 or 5 leaves the median of 11 at 4. Completeness 10 of 11. Under the
median-of-tasks sensitivity rule it is a 3, because SEA-HELM measures most languages on several
100-item tasks. Javanese and Sundanese sentiment are now unknown, which moves neither language's band.
Per language:

| Language | Task bands (qualifying items, component) | Band (max) | Band (median) |
|---|---|---|---|
| `ind` | instruction following 3 (105 sea-helm); MT 4 (1,012 flores-plus); NLI 3 (1,000 indonli); RC 2 (100 tydi-qa-goldp); reasoning 3 (500 xcopa); summarization 2 (100 xl-sum); classification 3 (1,000 mlhsd); generation 2 (58 sea-helm) | 4 | 3 |
| `jav` | instruction following 3 (105 sea-helm); MT 2 (394 nusax); reasoning 2 (282 multilingual-fig-qa); generation 2 (58 sea-helm) | 3 | 2 |
| `khm` | MT 4 (1,012 flores-plus) | 4 | 4 |
| `lao` | unknown | unknown | unknown |
| `msa` | MT 4 (1,012 flores-plus); generation 2 (58 sea-mt-bench-judge) | 4 | 3 |
| `mya` | MT 4 (1,012 flores-plus) | 4 | 4 |
| `sun` | instruction following 3 (105 sea-helm); MT 2 (394 nusax); reasoning 2 (295 multilingual-fig-qa); generation 2 (58 sea-helm) | 3 | 2 |
| `tam` | MT 4 (1,012 flores-plus); NLI 0 (0, IndicXNLI is machine-translated); RC 2 (100 indicqa); reasoning 3 (500 xcopa); summarization 2 (100 xl-sum); classification 3 (1,000 indicsentiment); generation 2 (58 sea-mt-bench-judge) | 4 | 2 |
| `tgl` | instruction following 3 (105 sea-helm); exam 2 (150 sea-helm); generation 2 (58 sea-mt-bench-judge) | 3 | 2 |
| `tha` | instruction following 3 (105 sea-helm); MT 4 (1,012 flores-plus); NLI 3 (1,000 xnli); RC 2 (100 xquad); reasoning 3 (500 xcopa); summarization 2 (100 xl-sum); classification 3 (1,000 thai-toxicity-tweet); generation 3 (91 mt-bench-thai) | 4 | 3 |
| `vie` | instruction following 3 (105 sea-helm); MT 4 (1,012 flores-plus); NLI 3 (1,000 xnli); RC 2 (100 xquad); reasoning 3 (500 xcopa); summarization 2 (100 xl-sum); classification 3 (1,000 uit-vsfc); generation 2 (58 sea-helm) | 4 | 3 |

**AfroBench: 4.** Of 54 measured languages, 21 are a 5, 31 a 4, 1 a 3 and 1 a 2. Every 5 comes from
NTREX-128's 1,997 sentences in translation, except that Swahili and Yoruba would also reach 5 on
OpenAI MMMLU's 14,042 human-translated questions. Every 4 comes from FLORES's 1,012 sentences; 23
languages are measured only on FLORES and SIB-200. Nine target languages are unmeasured (`ach`,
`lgg`, `nyn`, `teo` on SALT alone; `arq` and `por` on AfriSenti alone; `pcm` on MasakhaPOS,
MasakhaNEWS and AfriSenti; `bbj` on MasakhaPOS and AfriADR; `nqo` with no dataset); filling them with
0 or 5 leaves the median of 63 at 4. Completeness 54 of 63. Under the median-of-tasks rule it is a
3: 49 of the 54 measured languages land on 3, the 23 FLORES-and-SIB languages among them because the
median of a 4 and a 2 is a 3. Per language:

| Language | Task bands (qualifying items, component) | Band (max) | Band (median) |
|---|---|---|---|
| `ach` | unknown | unknown | unknown |
| `aeb` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `afr` | MT 5 (1,997 ntrex-128); RC 3 (900 belebele) | 5 | 4 |
| `aka` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `amh` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); RC 3 (900 belebele); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `arq` | unknown | unknown | unknown |
| `ary` | MT 4 (1,012 flores-plus); RC 3 (900 belebele); classification 2 (204 sib-200) | 4 | 3 |
| `arz` | MT 4 (1,012 flores-plus); RC 3 (900 belebele); classification 2 (204 sib-200) | 4 | 3 |
| `bam` | MT 4 (1,012 flores-plus); RC 3 (900 belebele); classification 2 (204 sib-200) | 4 | 3 |
| `bbj` | unknown | unknown | unknown |
| `bem` | MT 5 (1,997 ntrex-128); classification 2 (204 sib-200) | 5 | 3 |
| `cjk` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `dik` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `dyu` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `ewe` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `fon` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `fuv` | classification 2 (204 sib-200) | 2 | 2 |
| `hau` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); RC 3 (900 belebele); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `ibo` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); RC 3 (900 belebele); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `kab` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `kam` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `kbp` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `kea` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `kik` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `kin` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `kmb` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `knc` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `kon` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `lgg` | unknown | unknown | unknown |
| `lin` | exam 3 (500 afrimmlu); MT 4 (1,012 flores-plus); NLI 3 (600 afrixnli); RC 3 (900 belebele); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 4 | 3 |
| `lua` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `lug` | exam 3 (500 afrimmlu); MT 4 (1,012 flores-plus); NLI 3 (600 afrixnli); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 4 | 3 |
| `luo` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `mos` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `nqo` | unknown | unknown | unknown |
| `nso` | exam 3 (509 uhura-arc-easy); MT 5 (1,997 ntrex-128); classification 2 (204 sib-200) | 5 | 3 |
| `nus` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `nya` | MT 5 (1,997 ntrex-128); classification 2 (204 sib-200) | 5 | 3 |
| `nyn` | unknown | unknown | unknown |
| `orm` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `pcm` | unknown | unknown | unknown |
| `plt` | MT 5 (1,997 ntrex-128); classification 2 (204 sib-200) | 5 | 3 |
| `por` | unknown | unknown | unknown |
| `run` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `sag` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `sna` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); RC 3 (900 belebele); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `som` | MT 5 (1,997 ntrex-128); classification 2 (204 sib-200) | 5 | 3 |
| `sot` | exam 3 (500 afrimmlu); MT 4 (1,012 flores-plus); NLI 3 (600 afrixnli); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 4 | 3 |
| `ssw` | MT 5 (1,997 ntrex-128); classification 2 (204 sib-200) | 5 | 3 |
| `swa` | exam 5 (14,042 openai-mmmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); RC 3 (900 belebele); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `taq` | MT 4 (1,012 flores-plus) | 4 | 4 |
| `teo` | unknown | unknown | unknown |
| `tir` | MT 5 (1,997 ntrex-128); RC 3 (900 belebele); classification 2 (204 sib-200) | 5 | 3 |
| `tsn` | MT 5 (1,997 ntrex-128) | 5 | 5 |
| `tso` | RC 3 (900 belebele); classification 2 (204 sib-200) | 3 | 2 |
| `tum` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `twi` | exam 3 (500 afrimmlu); MT 4 (1,012 flores-plus); NLI 3 (600 afrixnli); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 4 | 3 |
| `tzm` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `umb` | MT 4 (1,012 flores-plus); classification 2 (204 sib-200) | 4 | 3 |
| `wol` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); RC 3 (900 belebele); classification 3 (638 injongo-intent) | 5 | 3 |
| `xho` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); RC 3 (900 belebele); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `yor` | exam 5 (14,042 openai-mmmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); RC 3 (900 belebele); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |
| `zul` | exam 3 (500 afrimmlu); MT 5 (1,997 ntrex-128); NLI 3 (600 afrixnli); RC 3 (900 belebele); reasoning 2 (250 afrimgsm); classification 3 (640 injongo-intent) | 5 | 3 |

**Without the mapped entries.** Leaving out the 12 entries that carry `source_language` makes `ara`,
`est` and `grn` unknown on FLORES+ (185 of 203 measured, still 4 / 4), drops Plateau Malagasy from 5
to 4 on AfroBench (still 4 / 4) and changes no Oromo band, since its NTREX entry is recorded from the
source's own `orm`. Under the highest task band no set moves. Under the median-of-tasks sensitivity
rule SEA-HELM becomes unresolved (medians 2 and 3): Malay is then measured only on
SEA-MT-Bench-Judge's 58 prompts, a 2.

## What the calibration exposed

In order of how much each one changes an outcome.

1. **The task-to-language rule decides two of the four bands, and it is not ruled.** Highest task band
   gives SEA-HELM and AfroBench a 4; median of task bands gives a 3. Neither is clean. Under the
   highest band, a suite's band is the depth of the deepest set it imports: SEA-HELM's 4 rests
   entirely on its FLORES sample, AfroBench's 21 languages at 5 rest entirely on NTREX-128, and
   SEA-HELM ties FLORES+ by sampling it. Dropping the components that have their own row on the map
   (FLORES+, Belebele, SIB-200, ThaiExam) gives SEA-HELM a 3 and leaves AfroBench unresolved (25
   measured, 38 unknown, medians 0 and 5). Under the median, adding a 100-item task lowers a
   language: Khmer and Burmese, measured on translation alone, outrank Indonesian and Thai, measured
   on eight tasks. A ruling is needed on the rule, and on whether components that have their own
   row count toward a suite's depth (R-2026-10-30-e and -f settle stage counting for groups, not
   depth).
2. **The ladders in different units are not on one scale.** 1,000 translation sentences are a 4;
   1,000 classification items are a 3. Under the highest-band rule that gap decides most languages,
   because almost every multilingual set imports FLORES. Equating the translation ladder to the
   accuracy ladder (4 at 1,600) makes FLORES+ a 3 and puts every set in the sample at 3, which is no
   more useful. The maintainer has to choose whether ladders are equated by statistical precision or
   by each task's reference benchmarks; this record proposes the second for translation and judged
   generation and the first for everything else.
3. **No set in the sample reaches 5, and all four fall one band.** That is the intended correction
   for 12 of 22 at 5 (R-2026-10-30-l), but the 5s it will produce are large single-language exams:
   ArabicMMLU's 14,575 questions, Khayyam's 20,192 and VMLU's 10,880 clear 6,400, so the depth ladder
   will place them above FLORES+. Whether that ordering is wanted should be decided before the other
   sets are filled.
4. **The products' `languages` and the sources' codes have drifted.**
   [Language codes](#language-codes-needs-reconciliation) lists every discrepancy. FLORES+ lists
   FLORES-200 codes the card has since replaced; AfroBench and SEA-HELM each have codes on one side
   only. Twelve entries are recorded under the product's code with the source's code in
   `source_language`, an inferred mapping rather than an observed identity. The hand-run counts them,
   and dropping them moves no proposed band but leaves SEA-HELM unresolved under the median-of-tasks
   rule. A ruling is needed on whether a mapped entry counts until the products' `languages` are
   reconciled with the current sources, and the reconciliation itself is a curation pass of its own.
5. **A suite's own documents disagree about what it contains.** SEA-HELM's paper covers Filipino,
   Indonesian, Tamil, Thai and Vietnamese; its Hugging Face cards cover Indonesian, Javanese,
   Sundanese, Tamil, Thai, Vietnamese and Tagalog, with translation for Khmer, Burmese, Malay and
   Chinese; its GitHub tables add Malay, Burmese, Lao and Khmer across several tasks and Filipino
   through Batayan. Only the cards state counts, so the record describes the card version, which may
   not be the leaderboard's current one. AfroBench's Table 2, Table 11 and its members' repositories
   disagree in nine places: MasakhaNER-X, AfriQA and MAFAND totals; Uhura's Northern Sotho and
   MasakhaPOS's Xhosa (in Table 2's totals, not marked in Table 11); AfriMGSM's Wolof (in the
   repository, not in Table 11); SALT's Wolof (marked in Table 11, not a SALT language); NTREX's 2,000
   (the repository has 1,997); InjongoIntent's 640 (Wolof has 638). A rule is needed for which wins
   when a suite's paper and a member's repository disagree. This record took the repository where its
   total matches the paper, the paper's single figure otherwise, and dropped the dataset where they
   conflict.
6. **Provenance is unknown where it matters least to the median and most to the reader.** Under the
   rule in [How provenance was read](#how-provenance-was-read), a card that describes news or tweets
   in the language no longer establishes `native`, so AfriSenti, MasakhaNEWS and MasakhaPOS are
   unknown, and AfriADR is unknown because MAFAND says its text was translated without saying by
   whom. FLORES+'s OLDI-recreated languages have their creation documented only in gated cards; SALT
   never says who translated; NollySenti and MasakhaNER-X are not described by any fetched source.
   Under the highest-task-band rule this moves no band, because translation sets carry every measured
   language, but it takes AfroBench from 58 to 54 measured languages of 63 and leaves four languages
   (`arq`, `bbj`, `pcm`, `por`) with no qualifying evidence at all. The documents also conflict on
   NusaX ([Provenance conflicts](#provenance-conflicts)), and the record keeps both sides. Whether
   SEA-HELM's own "Native" label is an explicit enough statement is the open question: ThaiExam's band
   turns on it.
7. **Schema gaps the records ran into.**
   - No few-shot split. SEA-HELM's `*_fewshot` splits are left out; ThaiExam's are recorded as
     `train`, because its source calls them that.
   - No script, variety or direction in the key. FLORES+'s two-script and two-variety languages and
     SEA-HELM's two translation directions collapse to one entry each. Fine for depth, and lossy for
     the language view of R-2026-11-01-f.
   - Task classes. AfriADR (diacritic restoration) has no class and sits in `text_generation` with
     judged chat prompts, though it is scored per sentence; LINDSEA syntax went to
     `text_classification`, LINDSEA pragmatics to `natural_language_inference`, the MABL metaphor set
     to `reasoning`, and toxicity detection to `text_classification` (the vocabulary's own example of
     hate speech) rather than `safety`. Each is a judgment.
   - Components. A suite cannot name two of its own components in one task, so SEA-HELM's
     criteria-judged sets are `sea-mt-bench-judge` and `kalahi-judge`. ThaiExam's five exams are one
     component, so its test count is the sum of five stated counts rather than a stated total.
   - Overlap without containment. SEA-MTBench and SEA-MT-Bench-Judge share MT-Bench prompts ("some
     prompts were modified"), so neither is `subset_of` the other; under the within-task rule only the
     larger counts. SIB-200 and Belebele reuse FLORES sentences across tasks, which `subset_of` does
     not cover because it is per task.
8. **The official split of FLORES+ is a convention, not the benchmark's.** The benchmark's own test
   split (992 sentences) is held by Meta; `devtest` was built for "testing purposes during the
   development phase". Recording it as official follows R-2026-11-01-d, and every FLORES-derived
   entry in the suites inherits it.
9. **Pivots are a judgment in two of the four.** SEA-HELM's `zho` is declared a pivot, matching the
   current note's "eleven Southeast Asian languages". AfroBench declares none, and keeps `por`
   (Mozambican Portuguese in AfriSenti) a target although its paper lists Portuguese among the
   high-resource comparison languages. FLORES-200's intermediate source languages (Spanish, French,
   Russian, Arabic) stay targets of FLORES+.
10. **The robustness test rarely bit.** Unknowns are 7%, 0%, 9% and 14% of the target languages, so
    every median survived both fills. It bites in the borrowed-rows variant of item 1 and, under the
    median-of-tasks rule, in the variant without mapped entries (item 4). The tiebreak barely
    separates large sets (4.50, 4.49, 4.45) and counts languages, not tasks; task breadth, which
    R-2026-11-01-c says is tracked separately, has no formula yet.

## Before the other evaluation sets are filled

The maintainer's calls, in the order they block:

- the rule from task bands to a language band (item 1), and whether borrowed rows count toward a
  suite's depth;
- whether ladders are equated by precision or by reference benchmarks, and the thresholds above
  (items 2 and 3);
- whether a mapped entry counts until the products' `languages` are reconciled with the current
  sources, and the reconciliation itself (item 4);
- which source wins when a suite's paper and a member's repository disagree (item 5);
- whether SEA-HELM's "Native" label is an explicit enough statement for `native` (item 6);
- the schema changes in item 7: a few-shot split and a task class for diacritic restoration at
  least.

The open questions on aggregation, cross-task scale and imported components (items 1 to 3) stay with
the ladder PR.

## The confirmation date

`capability.last_verified` is unchanged on all four, at 2026-09-24. It dates the band, not the
coverage record: it says the score and its peer comparison were re-derived on that date, and this
pass did not re-derive the band or re-read the peer comparison. The coverage record is dated by the
`accessed` date of each source its entries cite ([Scope](#scope) gives them), and each of those
sources carries its own `http_status` and `content_sha256`. A new source read after an axis's date
fails no gate (the floor asks only that some source was read on or after the date). The existing
FLORES+ card entry was re-read in place, since the record quotes it.

## Changes after review

- **Language identity.** A new optional field, `source_language`, holds the code a source states
  when it differs from `language`, and marks the entry as an inferred mapping. It is on 12 entries:
  FLORES+ `ara`, `est`, `grn` and `zho` (dev and devtest), SEA-HELM's Malay translation, and
  AfroBench's Oromo FLORES and SIB-200 and Plateau Malagasy NTREX-128 entries.
  [Language codes](#language-codes-needs-reconciliation) lists every discrepancy, mapped or not. No
  product's `languages` changed.
- **Documented zeros.** An entry with `count: 0`, no provenance and a citation to the source that
  states the absence is now a measured zero rather than an unknown, for that language, task,
  component and official split only; it implies nothing about the language's coverage on other
  tasks or in other components. FLORES+'s three dev-only languages carry one on `devtest`, which
  takes its completeness from 185 to 188 of 203.
- **Provenance.** 60 entries changed, all to `unknown`: FLORES+ English (2, from `native`); SEA-HELM
  English (3, from `native`) and Javanese and Sundanese NusaX sentiment (2, from `human_translated`,
  now a documented conflict); AfroBench AfriSenti (14), MasakhaNEWS (14) and MasakhaPOS (20), all
  from `native`, and AfriADR (5, from `human_translated`). The reasons are in
  [How provenance was read](#how-provenance-was-read). SIB-200 and Belebele (66 entries) keep
  `human_translated` and now also cite the NLLB abstract; the ThaiExam training entry now also cites
  SEA-HELM's tables. Two SEA-HELM `shows` were extended with the quotes the native reading relies on.
- **Freshness.** This record and `capability.md` now say that the coverage evidence is dated by its
  sources' `accessed` dates and that `capability.last_verified` dates the band.
- **Dry run.** No proposed band and no median-of-tasks result moved. Completeness moved for FLORES+
  (185 to 188 of 203) and AfroBench (58 to 54 of 63); AfroBench's borrowed-rows variant stays
  unresolved (now 25 measured, medians 0 and 5); a variant without mapped entries was added.
- **Read and not cited.** The Multilingual-Fig-QA abstract (arXiv 2305.16171) was fetched to check
  the Javanese and Sundanese metaphor items. It names the languages and does not say how the items
  were written, so it is not on any record.

## Sources read

All fetched 2026-11-01 with `build.fetch_source`, HTTP 200. Hub and arXiv pages change between
fetches; the digests are those of the bodies the `shows` were quoted from. The Multilingual-Fig-QA
abstract was read after review and is not on any record. The last seven rows are the reference
benchmarks the ladders cite, and are not on any record either.

| URL | sha256 |
|---|---|
| https://huggingface.co/datasets/openlanguagedata/flores_plus | `930bd24e2c381e335bcfe9a1f6d0cff88a28fd040d891cebef1f629dbb52d41f` |
| https://raw.githubusercontent.com/facebookresearch/flores/main/flores200/README.md | `74ccbbe29feba9d92cb3ee472387579ab2aa5c0299d47dcec7614b2c06cd49fc` |
| https://aclanthology.org/2022.tacl-1.30.pdf | `f51863eaed9c58c408e917d6c1e6d7c02df0c5d343280eb56741c84dd2e4637d` |
| https://arxiv.org/abs/2207.04672 | `4807d538486a3ff6cddf0be6c796025e47074b13a857f86101059b7c3d3c3969` |
| https://huggingface.co/datasets/typhoon-ai/thai_exam/raw/main/README.md | `860459e28fcaf606f68f1fb40bbdb9bd6b47e74c62fb390e37ac133c0b53b3ff` |
| https://datasets-server.huggingface.co/size?dataset=typhoon-ai/thai_exam | `769cf1f2a3e8a3288a82adc0130010005fb109603a581999e73daf110156e5a9` |
| SEA-HELM's dataset tables, `datasets_and_prompts.md` in the GitHub repository (already cited on both records; body unchanged since 2026-09-24) | `3cb8b1610ffe510997301fb267f6717bf63c574596a7aa4472a1f2f94d20135f` |
| https://huggingface.co/datasets/aisingapore/NLU-Sentiment-Analysis | `d36d2d5e4bfe035a29a15cbd1333a5cfb1c13fb34042e809bee958a4c1f8b02a` |
| https://huggingface.co/datasets/aisingapore/NLU-Question-Answering | `2b1509c205d31fc30e75a743831f9c4ac4c5024a957f6a264eee0fd4e9e7b276` |
| https://huggingface.co/datasets/aisingapore/NLU-Metaphor | `0992529b79d136f7a5f1f37b503d6ade2f3bdc1873686393e21d6393c5fa2000` |
| https://huggingface.co/datasets/aisingapore/NLG-Machine-Translation | `c833d594332191f54afcc345005d5d8ad9b9a708a0737fee54a5c6f6f45b820e` |
| https://huggingface.co/datasets/aisingapore/NLG-Abstractive-Summarization | `1c91c8ac856bf1b0d8519247e132f922c74c206d1bb9f087a0d15d852b0c1801` |
| https://huggingface.co/datasets/aisingapore/NLR-Causal-Reasoning | `4bc8394d76e4e8f32c1b7ffef9d8daa01aab5942b4a12d96b155b498178ba39f` |
| https://huggingface.co/datasets/aisingapore/NLR-NLI | `ba31915371fcef50fcba9ff7ad35a3c15b17713ffa18d46f637fa19baff043b7` |
| https://huggingface.co/datasets/aisingapore/Safety-Toxicity-Detection | `825142b21185681e5f8ad61875946e61478c96ad945fadd38951b33b85a20c76` |
| https://huggingface.co/datasets/aisingapore/Instruction-Following-IFEval | `09654eda1bbdabd05843337aa19f6dd3807ce91cddc99deb09f53a875319315f` |
| https://huggingface.co/datasets/aisingapore/MultiTurn-Chat-MT-Bench | `818cea971b6c403eb58190dab80fc99ba29ca19704ca44bbb3cd09269abe8829` |
| https://huggingface.co/datasets/aisingapore/MultiTurn-Chat-MT-Bench-Judge | `0725d44edc813f6c37e1f3f1f2b66c3d8e9e6d38964f2641191b28546f458a93` |
| https://huggingface.co/datasets/aisingapore/Cultural-Evaluation-Kalahi | `5a81f87dfffdeb845e1a25f5adefbc42783fc889fe5f289f348cbf9c5308990a` |
| https://huggingface.co/datasets/aisingapore/Cultural-Evaluation-Kalahi-Judge | `2efe0997a0103a7edc05a1209f6ce7388b0b4657ec5148e7623861c5b6fdd619` |
| https://huggingface.co/datasets/aisingapore/Linguistic-Diagnostics-Pragmatics | `549195981e7c6e7c1592f34eccb18d5f3c95782a6b46526f889e08c87016b11f` |
| https://huggingface.co/datasets/aisingapore/Linguistic-Diagnostics-Syntax | `997cc49cf070a7fe9fdf605b0cf0ec2055d6ae35beead15636654615cb468657` |
| https://huggingface.co/datasets/aisingapore/NLU-Belebele-MCQA | `16f131a44a263a044037e7285cd38d1389b9afbbd26c3bc951707f62547b0d7a` |
| https://arxiv.org/html/2502.14301 | `7021b8e7ca3b0847fa4cd62ee04d69f6aed6cd911a6a3a8ae70ff7aec22274f6` |
| https://aclanthology.org/2023.eacl-main.57.pdf | `0f2224a02e1d74cfb2410e82ee15f87bce5495bde6a3fe5f26b4bdc56af5e1f0` |
| https://arxiv.org/html/2311.07978 | `ef2b0d2751fd66adfd660ee0f45c3e2c928ff04cf846b4c5b7130df0243f6822` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/masakhapos | `5f6aaae93cdfeeef1f899a4c402974933d41a7e14d5334c81834731e0ba921ba` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/masakhanews | `7866cf2b3738b981ebd2a848ea6db283d26097891599dc403c0d677547537e40` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/afrisenti | `41292f7ff74a7b63ae394537a594830fd26e7506c828ecc31597d693faf8fb88` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/uhura-arc-easy | `89df98e30e47cb7e3ae9e0ef7f34301f8dac3c6dee4dc7d45f2ad47b019c8b28` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/InjongoIntent | `5838bfe30d771407c1a2fce8d7528d9724c5f2e4d1f282952846c0854de4a974` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/ntrex_african | `eea43d72e9d50175c01ce80c1d2671ebf27e7a508744808e6154afe9f199d315` |
| https://arxiv.org/abs/2406.03368 | `53df52b2305ce9322362d95a290fc44871149d7211bf434eb8557ea8bc89f1a5` |
| https://arxiv.org/abs/2309.07445 | `3871243edcb5f0682a105baebbb2645d6297a6947280f15627375e4b66c11cd4` |
| https://arxiv.org/html/2308.16884 | `5ebf36305c18085e44fa25a809dddf037afb04823923ff10d70c3224e1ebb535` |
| https://raw.githubusercontent.com/facebookresearch/belebele/main/README.md | `f7a9aead9af9056c96837eeb8eafa301ec37a4512e52520f1c3d7903b69ce145` |
| https://raw.githubusercontent.com/MicrosoftTranslator/NTREX/main/README.md | `d00240af5232e2b89d1e1fb1af23117339fabee04d0d01f72df64162cc207f35` |
| https://huggingface.co/datasets/masakhane/masakhapos | `731f5f54d45a148a0fbebcd74eab781297eb23fccef07fc58f03af8d858af070` |
| https://huggingface.co/datasets/masakhane/masakhanews | `051aedfd9ada73a54648fdb74842b547954c4494a28e50122e9f3bd7e894565f` |
| https://huggingface.co/datasets/masakhane/afrisenti | `61f4df72ec5c225f1586db62df0f844e495a6ac9fd12ced2f1b309f25181e2d9` |
| https://arxiv.org/abs/2502.09814 | `83adf5235d8bc6a820e62c2d9e40e70f81d976015d87cf91cc60a70ff16df114` |
| https://huggingface.co/datasets/masakhane/mafand | `0931d995a8d40e1273542f85afae7ea3d13d2b51c146268f6c44a12455bc996e` |
| https://huggingface.co/datasets/Sunbird/salt | `b94b453901165af5a0d4cd214b169a154d77b7aee0a274f988c0e3e05c802558` |
| https://huggingface.co/api/datasets/openlanguagedata/flores_plus/tree/main/dataset_cards | `c6e1fb3ff0df5f6cbcd573e4ecb636fe14b90590dee15cf4bae53b8d122983c9` |
| https://arxiv.org/abs/2305.16171 | `8fbc3c678431e037f546aae3b0a228b526e8b2b24f21ae25c9f942ba34cbdcd5` |
| https://datasets-server.huggingface.co/size?dataset=cais/mmlu&config=all | `a6628c2aba3d4485bc34739ab14a9a0885ee606d9f0b7db8f11f23171e241147` |
| https://datasets-server.huggingface.co/size?dataset=facebook/xnli&config=sw | `4daefe07108fa87079431cba6f188f25a8307ddf900d69cc3d7fc03907fa5b2f` |
| https://datasets-server.huggingface.co/size?dataset=cambridgeltl/xcopa&config=th | `20385aa13f1a09e5e17fefc55c61db43c4847f59b4000c5c5302be990024ecf6` |
| https://datasets-server.huggingface.co/size?dataset=juletxara/mgsm&config=sw | `e47940f1181eeb344bdcb4454f62646af5891adef0f2ce164b808aaae4ab18fb` |
| https://datasets-server.huggingface.co/size?dataset=google/IFEval | `55671fae08cdfc2113fddd20b4a8fd95f2bb2a96ee19ff646fbd0b2b7c2bf779` |
| https://datasets-server.huggingface.co/size?dataset=HuggingFaceH4/mt_bench_prompts | `b22a7bc34ec478be52115d89daacc56c8b8615271329fa46f2d3cb8e85d858fe` |
| https://datasets-server.huggingface.co/size?dataset=CohereLabs/Global-MMLU&config=sw | `f9b32d7565c4e53b73e36d2f536486a28774ac34bb36f64aa22ec85496e86915` |
