# Language-specific datasets seed: 2026-09-23

## Scope and boundary

This batch seeds the preliminary `language_specific_datasets` category proposed in issue #686. The
membership test is the one the issue set: a dataset belongs when it is defined by the languages it
serves rather than by its task or scale. A general multilingual crawl that happens to include a
language stays in `training_synthetic_datasets`, and Aya Collection stays there too. Every modality is
in scope: pretraining text, speech, instruction and dialogue data, parallel text, and evaluation sets.

Three boundary rules were needed during the sweep, and all three are recorded in the category's `comments`
so the next editor applies them rather than re-deriving them:

- **A many-language set belongs here when it was built to reach underrepresented languages.**
  FLORES+, Belebele, SIB-200, FLEURS, SMOL, OLDI Seed, Bloom Library and Glot500-c pass. A general
  benchmark translated into the major languages (Global-MMLU, Greek MMLU) is defined by its task and
  stays in `benchmark_eval_data`. A Common Crawl corpus filtered by language ID (GlotCC) sits with
  MADLAD-400 in `training_synthetic_datasets`, even when its stated purpose is minority languages.
- **The language has to be underrepresented.** KMMLU, TMMLU+, CMMLU, ChineseWebText, Carolina and
  the LatamGPT Corpus are assembled for one language or region, but the language is Korean,
  Chinese, Portuguese or Spanish. They were routed to the seed rosters of their neighbors, the
  three evaluation sets to `benchmark_eval_data` and the three corpora to
  `training_synthetic_datasets`. The smaller European languages stay in.
- **A benchmark suite that redistributes other datasets is the product.** AfroBench carries
  IrokoBench, AfriSenti, MasakhaNER, MAFAND-MT and SALT, and SEACrowd's dataloaders carry NusaX and
  PhoMT, so those seven are parked as members of their suites. Membership was read from AfroBench's
  published Hugging Face collection and SEACrowd's `seacrowd/sea_datasets` directory (401
  dataloaders). The exception is a global set a regional suite borrows a slice of: Belebele,
  FLORES+ and SIB-200 are in AfroBench's collection for their African languages and stay their own
  rows.

No row was scored. Each row carries identity and artifacts only, as the registry schema requires.

## Inputs swept

All fetched on 2026-09-23.

| Code | Input |
|---|---|
| I | The candidates named in issue #686 |
| P | A candidate proposal supplied in the session (33 candidates) |
| A | Sweep of African-language datasets |
| S | Sweep of South Asian datasets |
| E | Sweep of Southeast and East Asian datasets |
| M | Sweep of Arabic, Middle Eastern, Central Asian and smaller European datasets |
| X | Sweep of the Indigenous Americas, the Pacific, and cross-regional low-resource resources |

Each sweep read the Hugging Face dataset API (`id`, `gated`, `cardData.license`, languages,
`downloads`), the dataset card, the GitHub README (repositories confirmed with `git ls-remote`), and
the arXiv abstract page (title matched). Discovery catalogs consulted for candidates: ATLAS
(https://atlas-data.ai), Lanfrica (https://lanfrica.com), and the SEACrowd catalogue.

Retrieval cutoff, declared before triage: each regional sweep returned its 8 to 14 strongest
candidates and listed the rest as secondary. A secondary candidate is parked below with that reason,
and nothing was rejected for low downloads. VMLU and LaoBench were promoted from a sweep's
secondary list for that reason: each is the only evaluation set found for its language.

## Reconciled counts

A raw signal is one input naming one candidate. A duplicate is a candidate named by more than one
input, including the same product arriving under a superseded or stub identifier (`facebook/flores`
for FLORES+, the Common Voice Hub stubs, Common Voice's regional collections). Accepted counts every
row the sweep emitted: 65 into `language_specific_datasets` and 6 routed to neighboring
categories.

```text
raw_signals       = 211
duplicate_signals = 41
unique_candidates = 170
accepted          = 71
parked            = 99

211 = 41 + 170
170 = 71 + 99
```

No candidate collided with a head product, a retired alias, an existing registry row, or a
resolution-ledger ruling (`build.validate`, 0 errors).

## Should closed datasets be represented?

Yes, a few, on the terms ADR-005 sets for closed products: to mark the frontier, not to catalog the
long tail. The precedent is `benchmark_eval_data`, which carries lab-internal evaluation suites at
openness 0. Here the closed side has three different shapes, and each is worth one or two rows:

- **Paid catalogs that hold the classic low-resource collections.** The LDC's IARPA Babel and
  LORELEI language packs underpin a large share of published low-resource speech and text
  research, and they cost a membership or a license fee. Seeded as two rows.
- **Corpora a frontier lab or national champion built and did not release.** Meta's MMS-lab data
  (about 49K hours of New Testament recordings in 1,130 languages, models released and data not)
  and Sarvam-2T (about 2T Indic tokens behind Sarvam-1). Seeded as two rows. The Jais pretraining
  data is the same case, parked because its only artifact is the paper a Jais model product would
  claim.
- **Community-governed data.** Te Hiku Media's te reo Māori corpus is held under the Kaitiakitanga
  License, which grants use to the community the data came from and generally not outside it. It is
  closed by design rather than by commercial choice, and the map should be able to say that. Seeded
  as one row. The category's `scoring_recipe.note` flags that the dataset ladder may need a rung
  for this license at promotion.

Vendor catalogs (Appen, Defined.ai, ELRA, Karya) are parked: each is a bundle rather than a product
(ADR-005, surface not bundle), and entering them one by one would be the long tail ADR-005 declines.
Restricted parts of open products (the SEA-PILE v2 internal pool of about 1T tokens, Latxa's
unfiltered original, the Norwegian newspapers withdrawn in 2024, the Icelandic Gigaword restricted
subcorpora, the LatamGPT research tier) are not separate products. They belong in those products'
availability evidence at promotion.

## What the seed lets the map say

A first cut of the per-region answer the issue asks for, assembled by hand from this sweep. A
`languages` field would make it computable; that was judged a nice-to-have and deferred (see the
decisions below).

| Region | Open pretraining text | Open speech | Open instruction data | Open evaluation |
|---|---|---|---|---|
| Africa | WURA, Vuk'uzenzele; Inkuba-Mono (no license) | WAXAL, Afrivoice, ZA African Next Voices, BibleTTS; NaijaVoices (NC) | none found beyond machine-translated sets | AfroBench (carrying IrokoBench, MasakhaNER, AfriSenti) |
| South Asia | Sangraha, TituLM (Bangla), Nepali Text Corpus | IndicVoices, Vaani | IndicAlign; Updesh (non-commercial) | MILU, IndicGenBench |
| Southeast Asia | SEA-PILE v2, Mangosteen (Thai) | Khmer ASR; Burmese and Lao have none found | SEA-Instruct, Cendol, WangchanThaiInstruct | SEA-HELM, SeaExam, SEACrowd (carrying NusaX), ThaiExam, VMLU, LaoBench |
| Arabic and Persian | 101 Billion Arabic Words, naab | none found | CIDAR | ArabicMMLU, DarijaMMLU |
| Central Asia | none found | Kazakh Speech Corpus 2 | none found | none (KazMMLU parked) |
| Smaller European languages | Latxa, CATalog, CorpusNós, Dynaword, NCC, IGC, Sámi web, UberText; Korpus Malti (NC) | none found beyond Common Voice | none found | none found |
| Indigenous Americas | none found | none found beyond Common Voice | none | AmericasNLI, AmericasNLP data |
| Pacific | none open; te reo Māori is community-governed | none open | none | only as languages inside FLORES+, SMOL and Bloom Library |

## Accepted candidates


### Cross-regional: built to cover underrepresented languages

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| Mozilla Common Voice | `common-voice` | IPXA | speech | 295 languages (Scripted Speech v27.0) | CC0-1.0 | terms (Mozilla Data Collective) | https://github.com/common-voice/cv-dataset |
| FLORES+ | `flores-plus` | IPX | MT eval | about 220 varieties | CC-BY-SA-4.0 | gated (terms) | https://huggingface.co/datasets/openlanguagedata/flores_plus |
| OLDI Seed | `oldi-seed` | X | MT training | 44 | CC-BY-SA-4.0 | open | https://huggingface.co/datasets/openlanguagedata/oldi_seed |
| SMOL | `smol` | X | MT training | 124+ low-resource (221 with GATITOS) | CC-BY-4.0 | open | https://huggingface.co/datasets/google/smol |
| FLEURS | `fleurs` | PX | speech eval | 102 | CC-BY-4.0 | open | https://huggingface.co/datasets/google/fleurs |
| Belebele | `belebele` | PX | reading-comprehension eval | 122 variants | CC-BY-SA-4.0 | open | https://huggingface.co/datasets/facebook/belebele |
| SIB-200 | `sib-200` | PX | topic-classification eval | 205+ | CC-BY-SA-4.0 | open | https://huggingface.co/datasets/Davlan/sib200 |
| INCLUDE | `include-benchmark` | PX | knowledge eval from regional exams | 44 | Apache-2.0 | open | https://huggingface.co/datasets/CohereLabs/include-base-44 |
| Bloom Library datasets | `bloom-library-datasets` | X | text, captioning, speech | 363 | per item, mostly CC-BY-NC | gated (terms) | https://huggingface.co/datasets/sil-ai/bloom-lm |
| Glot500-c | `glot500-c` | X | pretraining text | 511 | per source | open | https://huggingface.co/datasets/cis-lmu/Glot500 |

### Africa

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| WAXAL | `waxal` | A | speech (ASR, TTS) | 29 African languages | CC-BY-4.0 / CC-BY-SA-4.0 by provider | open | https://huggingface.co/datasets/google/WaxalNLP |
| NaijaVoices | `naijavoices` | A | speech (ASR) | ig, ha, yo | CC-BY-NC-SA-4.0; paid commercial waiver | gated (auto) | https://huggingface.co/datasets/naijavoices/naijavoices-dataset |
| Afrivoice | `afrivoice` | A | speech (ASR) | sn, ln, ful, mg, wo, so; sibling repos for sw, Ethiopian languages, Kirundi and others | CC-BY-4.0 | gated (auto) | https://huggingface.co/datasets/DigitalUmuganda/Afrivoice |
| ZA African Next Voices | `za-african-next-voices` | AP | speech (ASR) | zul, sot, xho, tsn, tso, nde, ven | CC-BY-4.0 plus a no-TTS, no-voice-cloning term | gated (auto) | https://huggingface.co/datasets/dsfsi-anv/za-african-next-voices |
| AfriVoices-KE | `afrivoices-ke` | A | speech (ASR) | luo, kik, kln, mas, som | CC-BY-4.0 (paper; card silent) | gated (manual) | https://arxiv.org/abs/2604.08448 |
| BibleTTS | `bibletts` | AP | speech (TTS) | 10 West and Central African languages | CC-BY-SA-4.0 | open | https://www.openslr.org/129/ |
| WURA | `wura` | AP | pretraining text | 16 African languages plus en, fr, pt | Apache-2.0 | open | https://huggingface.co/datasets/castorini/wura |
| Inkuba-Mono | `inkuba-mono` | AP | pretraining text | sw, ha, zu, xh, yo | none declared | gated (auto) | https://huggingface.co/datasets/lelapa/Inkuba-Mono |
| Vuk'uzenzele corpus | `vukuzenzele` | A | monolingual and parallel text | 11 South African official languages | CC-BY-4.0 | open | https://huggingface.co/datasets/dsfsi/vukuzenzele-monolingual |
| AfroBench | `afrobench` | A | eval suite (15 tasks, 22 datasets) | 64 African languages | per component | open | https://github.com/McGill-NLP/AfroBench |

### South Asia

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| Sangraha | `sangraha` | ISP | pretraining text | 22 Indic languages | CC-BY-4.0 | open | https://huggingface.co/datasets/ai4bharat/sangraha |
| IndicVoices | `indicvoices` | SP | speech (ASR) | 22 scheduled Indian languages | CC-BY-4.0 | gated (auto) | https://huggingface.co/datasets/ai4bharat/IndicVoices |
| Bharat Parallel Corpus Collection | `bpcc` | SP | parallel text | 22 Indic languages paired with en | CC0 (mined) and CC-BY-4.0 (human seed) | gated (auto) | https://huggingface.co/datasets/ai4bharat/BPCC |
| IndicAlign | `indicalign` | SP | instruction and safety data | 14 Indic plus en | CC-BY-4.0 | open | https://huggingface.co/datasets/ai4bharat/indic-align |
| MILU | `milu` | S | knowledge eval | 11 Indic plus en | CC-BY-4.0 | gated (auto) | https://huggingface.co/datasets/ai4bharat/MILU |
| Project Vaani | `vaani` | S | image-prompted speech | 105 languages from 165 districts | CC-BY-4.0 | gated (auto) | https://huggingface.co/datasets/ARTPARK-IISc/Vaani |
| IndicGenBench | `indicgenbench` | S | generation eval | 29 Indic languages | per source (CC-BY-SA-4.0 on flores_in, xquad_in) | open | https://github.com/google-research-datasets/indic-gen-bench |
| Updesh | `updesh` | S | synthetic instruction data | 13 Indic plus en | Microsoft Research License (non-commercial, no redistribution) | downloadable under terms | https://huggingface.co/datasets/microsoft/Updesh_beta |
| TituLM Bangla corpus | `titulm-bangla-corpus` | S | pretraining text | Bengali | CC-BY-4.0 | open | https://huggingface.co/datasets/hishab/titulm-bangla-corpus |
| Nepali Text Corpus | `nepali-text-corpus` | S | pretraining text | Nepali | MIT | open | https://huggingface.co/datasets/IRIIS-RESEARCH/Nepali-Text-Corpus |
| L3Cube-MahaCorpus | `l3cube-mahacorpus` | S | pretraining text | Marathi | CC-BY-NC-SA-4.0 | open (Google Drive) | https://github.com/l3cube-pune/MarathiNLP |

### Southeast Asia

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| SEACrowd | `seacrowd` | IEP | data hub: standardized loaders and benchmarks | nearly 1,000 SEA languages; benchmarks cover 36 | per dataset; hub code Apache-2.0 | open | https://github.com/SEACrowd/seacrowd-datahub |
| SEA-PILE | `sea-pile` | E | pretraining text | vi, id, ta, ms, th, tl, km, lo, my | ODC-By-1.0 plus Common Crawl terms | open | https://huggingface.co/datasets/aisingapore/SEA-PILE-v2 |
| SEA-Instruct | `sea-instruct` | EP | instruction data | 11 including en and zh | ODC-By | gated (auto) | https://huggingface.co/datasets/aisingapore/SEA-Instruct-2602 |
| SEA-HELM | `sea-helm` | EP | eval suite | fil, id, ta, th, vi, jv, su, ms, my, lo | per dataset | gated (auto; some manual) | https://github.com/aisingapore/SEA-HELM |
| SeaExam | `seaexam` | E | exam eval (with SeaBench) | en, zh, id, vi, th | Apache-2.0 | open | https://huggingface.co/datasets/SeaLLMs/SeaExam |
| Cendol Collection | `cendol-collection` | E | instruction data | Indonesian and local languages | Apache-2.0 | open | https://huggingface.co/datasets/indonlp/cendol_collection_v2 |
| Mangosteen | `mangosteen` | E | pretraining text | Thai | ODC-By | open | https://huggingface.co/datasets/aisingapore/WangchanLION-Web |
| WangchanThaiInstruct | `wangchan-thai-instruct` | E | human-written instructions | Thai | CC-BY-SA-4.0 | open | https://huggingface.co/datasets/airesearch/WangchanThaiInstruct |
| ThaiExam | `thai-exam` | E | exam eval | Thai | Apache-2.0 | open | https://huggingface.co/datasets/typhoon-ai/thai_exam |
| Khmer ASR Cultural Dataset | `khmer-speech-dataset` | E | speech (ASR) | Khmer | CC-BY-SA-4.0 | open | https://huggingface.co/datasets/Digital-Divide-Data/khmer-speech-dataset |
| VMLU | `vmlu` | E | knowledge eval | Vietnamese | not yet stated (README: TBU) | download; test answers withheld | https://vmlu.ai |
| LaoBench | `laobench` | E | eval | Lao | Apache-2.0 | open | https://huggingface.co/datasets/BAAI/LaoBench |

### Middle East, Central Asia and Europe

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| 101 Billion Arabic Words | `101-billion-arabic-words` | M | pretraining text | Arabic | Apache-2.0 | open | https://huggingface.co/datasets/ClusterlabAi/101_billion_arabic_words_dataset |
| ArabicMMLU | `arabicmmlu` | M | knowledge eval from native exams | Arabic | CC-BY-NC-4.0 | open | https://huggingface.co/datasets/MBZUAI/ArabicMMLU |
| CIDAR | `cidar` | M | instruction data | Arabic | Apache-2.0 | open | https://huggingface.co/datasets/arbml/CIDAR |
| DarijaMMLU | `darijammlu` | M | knowledge eval (adapted from MMLU and ArabicMMLU) | Moroccan Arabic | MIT | open | https://huggingface.co/datasets/MBZUAI-Paris/DarijaMMLU |
| naab | `naab` | M | pretraining text | Persian | MIT | open | https://huggingface.co/datasets/SLPL/naab |
| Kazakh Speech Corpus 2 | `kazakh-speech-corpus-2` | M | speech (ASR) | Kazakh, with Kazakh-Russian code-switching | MIT | open | https://huggingface.co/datasets/issai/Kazakh_Speech_Corpus_2 |
| Latxa Corpus | `latxa-corpus` | M | pretraining text | Basque | per document | open (curated; original on request) | https://huggingface.co/datasets/HiTZ/latxa-corpus-v2 |
| CATalog | `catalog-catalan-corpus` | MP | pretraining text | Catalan, including Valencian and Balearic | per source | open | https://huggingface.co/datasets/projecte-aina/CATalog |
| CorpusNós | `corpusnos` | M | pretraining text | Galician | per subcorpus, mostly CC-BY-SA-4.0 | open | https://huggingface.co/datasets/proxectonos/corpusnos |
| Korpus Malti | `korpus-malti` | M | pretraining text | Maltese | CC-BY-NC-SA-4.0 | gated (identity fields, non-commercial pledge) | https://huggingface.co/datasets/MLRS/korpus_malti |
| Danish Dynaword | `danish-dynaword` | M | pretraining text | Danish | CC0-1.0 collection; open per-source terms | open | https://huggingface.co/datasets/danish-foundation-models/danish-dynaword |
| Norwegian Colossal Corpus | `norwegian-colossal-corpus` | M | pretraining text | Norwegian | per document type | open (newspapers withdrawn 2024-12) | https://huggingface.co/datasets/NbAiLab/NCC |
| Icelandic Gigaword Corpus | `icelandic-gigaword-corpus` | M | pretraining text | Icelandic | CC-BY-4.0 (open subset); restricted subcorpora | open subset | https://huggingface.co/datasets/arnastofnun/IGC-2024 |
| Northern Sámi web corpus | `saami-web` | M | pretraining text | Northern Sámi | CC0-1.0 | open | https://huggingface.co/datasets/ltg/saami-web |
| UberText | `ubertext` | M | pretraining text | Ukrainian | none stated | open download | https://lang.org.ua/en/ubertext/ |

### Indigenous Americas

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| AmericasNLI | `americasnli` | PX | NLI eval | 10 Indigenous languages of the Americas | CC-BY-SA-4.0 | open | https://huggingface.co/datasets/nala-cub/americas_nli |
| AmericasNLP shared-task data | `americasnlp-shared-task-data` | X | MT, speech translation | 13 Indigenous languages (2025) | per sub-corpus | open | https://github.com/AmericasNLP/americasnlp2021 |

### Closed and restricted: the frontier the open rows are measured against

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| Te Hiku Media te reo Māori corpus | `te-hiku-media-reo-maori-corpus` | X | speech and text | te reo Māori | Kaitiakitanga License | restricted (permission tied to tikanga) | https://papareo.io |
| IARPA Babel language packs | `iarpa-babel-language-packs` | X | conversational telephone speech | about 25 languages, one pack each | LDC IARPA Babel agreement | paid | https://catalog.ldc.upenn.edu/LDC2016S10 |
| LORELEI language packs | `lorelei-language-packs` | X | text, annotation, lexicons | one pack per language | LDC user agreement | paid | https://catalog.ldc.upenn.edu/LDC2023T02 |
| MMS-lab data | `mms-lab-data` | X | speech (New Testament recordings) | 1,130 languages, about 49K hours | not released | closed | https://arxiv.org/abs/2305.13516 |
| Sarvam-2T | `sarvam-2t` | S | pretraining text | 10 Indic languages, about 2T tokens | not released | closed | https://www.sarvam.ai/blogs/sarvam-1 |

### Routed to neighboring categories

Language-specific but not low-resource. Emitted as rows in the named category's registry file.

| Candidate | Slug | Routed to | Inputs | Modality | License as stated | Primary source |
|---|---|---|---|---|---|---|
| KMMLU | `kmmlu` | `benchmark_eval_data` | E | knowledge eval, Korean | CC-BY-ND-4.0 | https://huggingface.co/datasets/HAERAE-HUB/KMMLU |
| TMMLU+ | `tmmlu-plus` | `benchmark_eval_data` | E | knowledge eval, Traditional Chinese (Taiwan) | MIT | https://huggingface.co/datasets/ikala/tmmluplus |
| CMMLU | `cmmlu` | `benchmark_eval_data` | E | knowledge eval, Simplified Chinese | disputed: CC-BY-NC-SA-4.0 (repo) vs CC-BY-NC-4.0 (card) | https://github.com/haonan-li/CMMLU |
| ChineseWebText | `chinesewebtext` | `training_synthetic_datasets` | P | pretraining text, Chinese | Apache-2.0 (v2.0) | https://huggingface.co/datasets/CASIA-LM/ChineseWebText2.0 |
| Carolina Corpus | `carolina-corpus` | `training_synthetic_datasets` | P | pretraining text, Brazilian Portuguese | CC-BY-4.0 | https://huggingface.co/datasets/carolina-c4ai/corpus-carolina |
| LatamGPT Corpus | `latamgpt-corpus` | `training_synthetic_datasets` | X | pretraining text, es, pt, en across 20 countries | per document | https://huggingface.co/datasets/latam-gpt/LatamGPT-Corpus-1.0 |

Where a product line spans several Hub repositories (Afrivoice, AfriVoices-KE, IndicGenBench,
SEA-HELM, Bloom Library, and the AfroBench and SEACrowd suites), the row carries its most
representative artifact and promotion adds the rest to the head record. Licenses marked *disputed*
disagree between the Hub card and the repository; promotion settles them against the primary source
rather than picking one here.

## Parked candidates

| Candidate | Inputs | Reason | Source |
|---|---|---|---|
| AfriBERTa corpus | A | superseded by WURA from the same group | https://huggingface.co/datasets/castorini/afriberta-corpus |
| MasakhaNEWS | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/masakhane/masakhanews |
| MasakhaPOS | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/masakhane/masakhapos |
| AfriQA | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/masakhane/afriqa |
| AfriHate | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/afrihate/afrihate |
| Kencorpus | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/Kencorpus/KenCorpus_text |
| AfriSpeech-200 | A | boundary: African-accented English, so defined by region and accent rather than language | https://huggingface.co/datasets/intronhealth/afrispeech-200 |
| Masakhane machine-translated SFT sets | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected; machine-translated | https://huggingface.co/datasets/masakhane/african-ultrachat |
| Inkuba-Instruct | AP | sibling of Inkuba-Mono; review with it at promotion | https://huggingface.co/datasets/lelapa/Inkuba-instruct |
| Lacuna Fund | A | a funder, not a dataset | https://lacunafund.org |
| ALFFA | A | legacy (about 2016) and superseded by WAXAL and Afrivoice | https://github.com/getalp/ALFFA_PUBLIC |
| NCHLT / SADiLaR corpora | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/nwu-ctext/nchlt |
| Open Bible African subset | A | a re-host of another dataset | https://huggingface.co/datasets/AfriSpeech/open-bible-speech-african |
| Individual Amharic uploads | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/yordanoswuletaw/amharic-pretraining-corpus |
| Other Digital Umuganda repos | A | siblings of Afrivoice, folded into that row | https://huggingface.co/datasets/DigitalUmuganda/Afrivoice_Swahili |
| MasakhaNER 1.0 | A | superseded by MasakhaNER 2.0 | https://github.com/masakhane-io/masakhane-ner |
| AfriDocMT, Uhura, InjongoIntent | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected; covered by AfroBench | https://huggingface.co/masakhane |
| Lelapa ViXSD (Esethu License) | A | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected; the Esethu License is a model worth recording at promotion | https://huggingface.co/datasets/lelapa/Vukuzenzele_isiXhosa_Speech_Dataset_ViXSD |
| Intron Health clinical speech | A | closed and has no addressable artifact of its own; only press coverage | https://www.intron.io/research/ |
| N-ATLaS training data | A | closed; only the model is published, and that is a model artifact | https://techcabal.com/2025/09/25/nigerian-government-awarri-launch-n-atlas/ |
| IndicCorp v2 | IS | a distinct, earlier corpus that Sangraha succeeds for LLM use; revisit at promotion | https://huggingface.co/datasets/ai4bharat/IndicCorpV2 |
| Kathbath | S | part of AI4Bharat's IndicVoices speech line | https://huggingface.co/datasets/ai4bharat/Kathbath |
| Shrutilipi | S | part of AI4Bharat's IndicVoices speech line | https://huggingface.co/datasets/ai4bharat/Shrutilipi |
| IndicVoices-R | S | derived from IndicVoices | https://huggingface.co/datasets/ai4bharat/indicvoices_r |
| Rasa | S | sibling of IndicVoices (expressive TTS) | https://huggingface.co/datasets/ai4bharat/Rasa |
| Aksharantar | S | task-defined (transliteration) | https://arxiv.org/abs/2205.03018 |
| Pralekha | S | task-defined (document alignment) | https://arxiv.org/abs/2411.19096 |
| IndicSentiment | S | part of IndicXTREME | https://github.com/AI4Bharat/IndicBERT |
| Samanantar | SP | superseded by BPCC | https://huggingface.co/datasets/ai4bharat/samanantar |
| IN22 | S | the BPCC test set, part of that row | https://github.com/AI4Bharat/IndicTrans2 |
| IndicXTREME | SP | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected; no single artifact, split across per-task repos | https://github.com/AI4Bharat/IndicBERT |
| Lahaja | S | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/ai4bharat |
| Svarah | S | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/ai4bharat |
| Sarvam samvaad-hi | S | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/sarvamai/samvaad-hi-v1 |
| SPRINGLab IndicTTS mirrors | S | re-hosts of the IIT Madras Indic TTS database | https://huggingface.co/datasets/SPRINGLab/IndicTTS-Hindi |
| SPRING-INX | S | per-language repos with no umbrella identifier, and no data license found | https://huggingface.co/datasets/SPRINGLab/SPRING_INX_Malayalam_R1 |
| XL-Sum (Bangla) | S | boundary: a 43-language task set | https://huggingface.co/datasets/csebuetnlp/xlsum |
| Open large Bengali ASR data | S | an aggregation of other corpora | https://huggingface.co/datasets/SKNahin/open-large-bengali-asr-data |
| OOD-Speech | S | its training split is distributed inside Common Voice Bangla | https://arxiv.org/abs/2305.09688 |
| IIT Bombay English-Hindi | S | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/cfilt/iitb-english-hindi |
| Sinhala sets (SOLD and others) | S | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/sinhala-nlp/SOLD |
| UrduSpeech | S | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/ASLP-lab/UrduSpeech |
| Pashto community uploads | S | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets?search=pashto |
| Bangla2B+ | S | restricted (request form, non-commercial); a candidate for the closed tier at promotion | https://github.com/csebuetnlp/banglabert |
| LDC-IL corpora | S | restricted government corpora; a candidate for the closed tier at promotion | https://data.ldcil.org/accessing-data |
| Indic TTS database | S | license page unreachable on the sweep date (timeout); retry | https://www.iitm.ac.in/donlab/indictts/ |
| Bhashini / ULCA / AIKosh | S | platforms and catalogs, not datasets | https://github.com/bhashini-dibd/ulca |
| IndoNLU / Indo4B | E | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://github.com/IndoNLP/indonlu |
| FilBench | E | boundary: an evaluation harness over existing datasets, so evaluation_code | https://github.com/filbench/filbench-eval |
| SEA-VL | E | boundary: image-text data, outside the category's modalities | https://huggingface.co/datasets/SEACrowd/sea-vl_crawling |
| SeaEval | E | boundary: a cross-lingual mix not scoped to one region | https://huggingface.co/datasets/SeaEval/SeaEval_datasets |
| Viettel Vietnamese curated dataset | E | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/VTSNLP/vietnamese_curated_dataset |
| LLM-jp Corpus | EP | boundary: 17.8T of v4's 19.5T tokens are English, so not language-defined | https://gitlab.llm-jp.nii.ac.jp/datasets/llm-jp-corpus-v4 |
| JMMLU | E | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/nlp-waseda/JMMLU |
| BAAI CCI3 | E | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/BAAI/CCI3-HQ |
| Other Thai sets (WangchanX-FLAN, Typhoon-S) | E | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/airesearch/WangchanX-FLAN-v6.1 |
| Swallow Corpus | E | closed: the build code is public and the corpus is not, so there is no data artifact | https://github.com/swallow-llm/swallow-corpus |
| Sahabat-AI Javanese and Sundanese piles | E | unreleased as far as the sweep could establish; unconfirmed | https://huggingface.co/GoToCompany |
| SEALD | IEP | no dataset released under the name; its public output so far is the ATLAS catalog | https://aisingapore.org/aiproducts/southeast-asian-languages-in-one-network-data-seald/ |
| ATLAS | IEXP | a catalog, a discovery source for this category, not a product | https://atlas-data.ai |
| TurkishMMLU | M | full set by email only; 1,845 rows on the Hub; no license | https://huggingface.co/datasets/AYueksel/TurkishMMLU |
| ArabicWeb24 | M | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected; overlaps 101 Billion Arabic Words | https://huggingface.co/datasets/lightonai/ArabicWeb24 |
| HeDC4 | M | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/HeNLP/HeDC4 |
| Greek MMLU | M | boundary: a translation of MMLU | https://huggingface.co/datasets/ilsp/mmlu_greek |
| KazMMLU | M | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/MBZUAI/KazMMLU |
| Khayyam Challenge | M | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/raia-center/khayyam-challenge |
| Atlaset | M | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/atlasia/Atlaset |
| Irish FineWeb-Edu | M | boundary: derived from FineWeb | https://huggingface.co/datasets/ReliableAI/irish_fineweb_edu |
| Estonian and Uzbek sets (smugri-data and others) | M | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/tartuNLP/smugri-data |
| EusCrawl | MP | folded into the Latxa Corpus, which includes it | https://huggingface.co/datasets/HiTZ/euscrawl |
| Danish Gigaword | M | superseded by Danish Dynaword | https://huggingface.co/datasets/danish-foundation-models/danish-gigaword |
| Icelandic Dynaword | M | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected; overlaps the Icelandic Gigaword Corpus | https://huggingface.co/datasets/danish-foundation-models/icelandic-dynaword |
| AraBench | M | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/arbml/AraBench |
| Jais pretraining data | M | closed; its only artifact is the Jais paper, which a Jais model product would claim | https://arxiv.org/abs/2308.16149 |
| LDC Arabic Gigaword | M | paid; the LDC is represented by its Babel and LORELEI rows | https://catalog.ldc.upenn.edu/LDC2011T11 |
| Malyuk | M | derived from UberText and others | https://huggingface.co/datasets/lang-uk/malyuk |
| ChrEn (Cherokee-English) | X | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected; no data license found | https://github.com/ZhangShiyue/ChrEn |
| Jojajovai (Guaraní-Spanish) | X | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://github.com/pln-fing-udelar/jojajovai |
| Axolotl (Nahuatl-Spanish) | X | a sub-source of the AmericasNLP data | https://huggingface.co/datasets/somosnlp-hackathon-2022/Axolotl-Spanish-Nahuatl |
| Llamacha monolingual Quechua | X | below this sweep's per-region retrieval cutoff (the 8-14 strongest per region); not rejected | https://huggingface.co/datasets/Llamacha/monolingual-quechua-iic |
| CMU Wilderness | X | scripts that re-align third-party recordings; distributes no data | https://github.com/festvox/datasets-CMU_Wilderness |
| LatamGPT CHOCLO and Trueque | X | folded into the LatamGPT Corpus row | https://huggingface.co/datasets/latam-gpt/CHOCLO |
| Global-MMLU | X | boundary: MMLU translated into 42 languages, defined by its task; belongs in benchmark_eval_data | https://huggingface.co/datasets/CohereLabs/Global-MMLU |
| GlotCC | X | boundary: a Common Crawl corpus like MADLAD-400; belongs with it in training_synthetic_datasets | https://huggingface.co/datasets/cis-lmu/GlotCC-V1 |
| Bloom speech and captioning | X | siblings of the Bloom Library row | https://huggingface.co/datasets/sil-ai/bloom-speech |
| Lanfrica | X | a catalog, a discovery source | https://lanfrica.com |
| ELRA / ELDA catalog | X | a vendor catalog, a bundle rather than a product (ADR-005, surface not bundle) | https://catalog.elra.info |
| Appen off-the-shelf datasets | X | a vendor catalog, a bundle rather than a product (ADR-005) | https://www.appen.com/ots-datasets |
| Defined.ai marketplace | X | a vendor catalog, a bundle rather than a product (ADR-005) | https://defined.ai/datasets |
| Karya | X | a data vendor, a bundle rather than a product (ADR-005) | https://www.karya.in |
| MAP-CC | P | the alternative Chinese corpus; ChineseWebText 2.0 carries the more open license (MAP-CC is CC-BY-NC-ND-4.0) | https://huggingface.co/datasets/m-a-p/MAP-CC |
| VoxPopuli | P | boundary: parliamentary speech in 16 mostly major European languages, a general multilingual corpus | https://huggingface.co/datasets/facebook/voxpopuli |
| IrokoBench | AP | carried by the `afrobench` suite, which is the product under the bundle ruling; LLM eval (AfriMMLU, AfriXNLI, AfriMGSM), 17 African languages, Apache-2.0 | https://huggingface.co/datasets/masakhane/afrimmlu |
| AfriSenti | AP | carried by the `afrobench` suite, which is the product under the bundle ruling; sentiment, 14 African languages, disputed: CC-BY-4.0 (repo) vs CC-BY-NC-SA-2.0 (card) | https://huggingface.co/datasets/masakhane/afrisenti |
| MasakhaNER 2.0 | IAP | carried by the `afrobench` suite, which is the product under the bundle ruling; NER, 20 African languages, disputed: AFL-3.0 (card) vs CC-BY-NC (repo) | https://huggingface.co/datasets/masakhane/masakhaner2 |
| MAFAND-MT | AP | carried by the `afrobench` suite, which is the product under the bundle ruling; MT (news), 21 African languages, CC-BY-NC-4.0 | https://huggingface.co/datasets/masakhane/mafand |
| SALT | A | carried by the `afrobench` suite, which is the product under the bundle ruling; parallel text and speech, English plus 8 Ugandan languages, CC-BY-SA-4.0 | https://huggingface.co/datasets/Sunbird/salt |
| NusaX | EP | carried by the `seacrowd` suite, which is the product under the bundle ruling; sentiment and MT, Indonesian, English and 10 local languages, CC-BY-SA-4.0 | https://huggingface.co/datasets/indonlp/NusaX-senti |
| PhoMT | P | carried by the `seacrowd` suite, which is the product under the bundle ruling; parallel text, Vietnamese and English, none declared on the card | https://huggingface.co/datasets/vinai/PhoMT |

## Decisions recorded before promotion

Taken on review of the first draft of this seed, 2026-09-23:

1. **No `languages` field for now.** It would make the per-language gap computable rather than
   hand-assembled, and it is a schema change. Judged a nice-to-have; the category works without it.
2. **Language-targeted evaluation sets stay in this category**, not `benchmark_eval_data`.
3. **High-resource languages are out.** The six such rows were routed to their neighbors.
4. **Bundles are the product.** AfroBench and SEACrowd stand for the datasets they carry.
5. **Weights are `adopt: 0.3, cap: 0.7`.** Download counts for a low-resource corpus are small by
   construction, so adoption carries less of the overall score than in the neighboring categories.

## Still open for promotion

- **Whether the dataset ladder needs a rung for a community-governed license** such as Te Hiku
  Media's Kaitiakitanga License (see the category's `scoring_recipe.note`).
- **The disputed licenses** on MasakhaNER 2.0, AfriSenti and CMMLU, and the undeclared ones on
  Inkuba-Mono, PhoMT, UberText and VMLU, which promotion has to read at the source.
