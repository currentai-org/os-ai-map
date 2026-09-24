# Language-specific datasets seed: 2026-09-23

## Scope and boundary

This batch seeds the preliminary `language_specific_datasets` category proposed in issue #686. The
membership test is the one the issue set: a dataset belongs when it is defined by the languages it
serves rather than by its task or scale. A general multilingual crawl that happens to include a
language stays in `training_synthetic_datasets`, and Aya Collection stays there too. Every modality is
in scope: pretraining text, speech, instruction and dialogue data, parallel text, and evaluation sets.

Four boundary rules came out of the sweep, and all four are recorded in the category's `comments`
so the next editor applies them rather than re-deriving them:

- **A many-language set belongs here when it was built to reach underrepresented languages.**
  FLORES+, Belebele, SIB-200, FLEURS, SMOL, OLDI Seed, Bloom Library and Glot500-c pass. A general
  benchmark translated into the major languages (Global-MMLU, Greek MMLU) is defined by its task and
  stays in `benchmark_eval_data`. A Common Crawl corpus filtered by language ID (GlotCC) sits with
  MADLAD-400 in `training_synthetic_datasets`, even when its stated purpose is minority languages.
- **The language has to be underrepresented.** Corpora and benchmarks for Chinese, Japanese, Korean,
  Spanish and Portuguese pass the first test and fail this one. The 11 such candidates were routed
  to the seed rosters of their neighbors. The smaller European languages stay in. The line is an
  enumerated list today rather than a derived rule; see the open items.
- **Accent is not language.** AfriSpeech-200 and Svarah are English speech defined by accent, and are
  out on the same rule.
- **A benchmark suite that redistributes other datasets is the product.** AfroBench carries ten of
  the African candidates, IndicXTREME carries IndicSentiment, and SEACrowd carries NusaX and PhoMT,
  so those members are parked as bundled. Membership was read from AfroBench's published Hugging
  Face collection and SEACrowd's `seacrowd/sea_datasets` directory (401 dataloaders). A global set a
  regional suite borrows a slice of (Belebele, FLORES+ and SIB-200 in AfroBench) stays its own row.

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

**No retrieval cutoff.** The regional sweeps were targeted searches, not walks down a ranked source,
so there was no ordering a cutoff could bound. Every candidate a sweep surfaced was decided on its
merits: accepted, or parked with one of the workflow's reasons (duplicate, superseded, new SKU of an
existing product, bundled into a suite, boundary, no addressable artifact, unverifiable identity,
ambiguous org mapping, unmaintained, or the closed long tail). Nothing was parked for low downloads
or for ranking below other candidates. The coverage this leaves is the searches' coverage, which is
not exhaustive; a later sweep that wants a reproducible bound should walk the Hub's dataset listing
per language tag, ordered by downloads, and declare its N before it starts.

## Reconciled counts

A raw signal is one input naming one candidate. A duplicate is a candidate named by more than one
input, including the same product arriving under a superseded or stub identifier (`facebook/flores`
for FLORES+, the Common Voice Hub stubs, Common Voice's regional collections). Accepted counts every
row the sweep emitted: 97 into `language_specific_datasets` and 11 routed to neighboring
categories.

```text
raw_signals       = 215
duplicate_signals = 41
unique_candidates = 174
accepted          = 108
parked            = 66

215 = 41 + 174
174 = 108 + 66
```

No candidate collided with a head product, a retired alias, an existing registry row, or a
resolution-ledger ruling (`build.validate`, 0 errors).

## Organizations and handles

Every row's organization has a `sources/organizations/` file, and every account a row's artifacts
live under is declared in `sources/org_handles.yaml` in this PR. Hub handles were checked against
the Hub's organization or user overview (the account's full name), GitHub handles against a live
repository, and homepage domains against the row's own URL. Where the account is a person or a
user account run by a group rather than an organization account, the handle carries a note saying
so. The handle-coverage baseline went **up** on every route as a result and was re-pinned upward;
nothing was lowered.

Candidates whose organization could not be settled were held rather than guessed: Mangosteen
(VISTEC's corpus in AI Singapore's Hub namespace), AmericasNLI (a lab account on the Hub, a personal
account on GitHub) and AraBench (ARBML's re-host of a QCRI dataset). BibleTTS's OpenSLR page was
dropped from its row, since OpenSLR hosts it and does not publish it; its GitHub repository and
paper remain.

## Should closed datasets be represented?

Yes, a few, on the terms ADR-005 sets for closed products: to mark the frontier, not to catalog the
long tail. The precedent is `benchmark_eval_data`, which carries lab-internal evaluation suites at
openness 0. The rule used here, also written into the category's `scoring_recipe.note`: **a closed
row is a corpus a frontier lab or national program built and withheld, or one its community
governs.**

- **Built and withheld:** Meta's MMS-lab data (about 49K hours of New Testament recordings in 1,130
  languages; the models were released and the data was not) and Sarvam-2T (about 2T Indic tokens
  behind Sarvam-1). The Jais pretraining data is the same case, parked because its only artifact is
  the paper a Jais model product would claim.
- **Community-governed:** Te Hiku Media's te reo Māori corpus, held under the Kaitiakitanga License,
  which grants use to the community the data came from and generally not outside it. The ladder may
  need a rung for this license at promotion.

Items sold from a vendor or consortium catalog are the closed long tail ADR-005 declines. That covers
the LDC (Arabic Gigaword and the IARPA Babel and LORELEI packs), ELRA, LDC-IL, Appen, Defined.ai and
Karya. A catalog's product line is also a bundle rather than a product: every Babel pack is a
separately licensed item with its own language, so one pack's page cannot stand for the line.
Restricted parts of open products (the SEA-PILE v2 internal pool of about 1T tokens, Latxa's
unfiltered original, the Norwegian newspapers withdrawn in 2024, the Icelandic Gigaword restricted
subcorpora, the LatamGPT research tier) are not separate products; they belong in those products'
availability evidence at promotion.

## What the seed lets the map say

A first cut of the per-region answer the issue asks for, assembled by hand from this sweep. A
structured `languages` field would make it computable; see the open items.

| Region | Open pretraining text | Open speech | Open instruction data | Open evaluation |
|---|---|---|---|---|
| Africa | WURA, Vuk'uzenzele, NCHLT, Kencorpus; Inkuba-Mono (no license) | WAXAL, Afrivoice, ZA African Next Voices, AfriVoices-KE, BibleTTS, ViXSD; NaijaVoices (NC) | Inkuba-Instruct, African UltraChat (machine-translated) | AfroBench, AfriHate, AfriDocMT |
| South Asia | Sangraha, IndicCorp v2, TituLM (Bangla), Nepali Text Corpus, L3Cube-MahaCorpus | IndicVoices, Kathbath, Shrutilipi, IndicVoices-R, Rasa, Vaani, SPRING-INX, UrduSpeech | IndicAlign, Samvaad-Hi; Updesh (non-commercial) | MILU, IndicXTREME, IndicGenBench, Lahaja, SOLD |
| Southeast Asia | SEA-PILE v2, Vietnamese Curated Dataset | Khmer ASR; none found for Burmese or Lao | SEA-Instruct, Cendol, WangchanThaiInstruct, WangchanX-FLAN | SEA-HELM, SeaExam, SEACrowd, IndoNLU, ThaiExam, Typhoon-S, VMLU, LaoBench |
| Arabic, Persian, Hebrew, Turkish | 101 Billion Arabic Words, ArabicWeb24, Atlaset (Darija), naab, HeDC4 | none found | CIDAR | ArabicMMLU, DarijaMMLU, Khayyam Challenge, TurkishMMLU |
| Central Asia | none found | Kazakh Speech Corpus 2 | none found | KazMMLU |
| Smaller European languages | Latxa, CATalog, CorpusNós, Dynaword, NCC, IGC, Icelandic Dynaword, Sámi web, SMUGRI, UberText; Korpus Malti (NC) | none found beyond Common Voice | none found | none found |
| Indigenous Americas | Llamacha Quechua; parallel text in ChrEn (Cherokee) and Jojajovai (Guaraní) | none found beyond Common Voice | none | AmericasNLP shared-task data |
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
| AfriHate | `afrihate` | A | hate-speech classification | 15 African languages | Apache-2.0 | gated (auto) | https://huggingface.co/datasets/afrihate/afrihate |
| Kencorpus | `kencorpus` | A | text and speech corpora | Swahili, Dholuo, Luhya | CC-BY-4.0 | open | https://huggingface.co/datasets/Kencorpus/KenCorpus_text |
| African UltraChat | `african-ultrachat` | A | instruction data (machine-translated) | African languages | MIT | open | https://huggingface.co/datasets/masakhane/african-ultrachat |
| AfriDocMT | `afridocmt` | A | document-level MT | African languages | none declared | open | https://huggingface.co/datasets/masakhane/AfriDocMT |
| NCHLT text corpora | `nchlt` | A | text corpora and annotation | South African languages | CC-BY-2.5 | open | https://huggingface.co/datasets/nwu-ctext/nchlt |
| Inkuba-Instruct | `inkuba-instruct` | AP | instruction data | sw, ha, zu, xh, yo | none declared | gated (auto) | https://huggingface.co/datasets/lelapa/Inkuba-instruct |
| Vuk'uzenzele isiXhosa Speech Dataset (ViXSD) | `vixsd` | A | speech | isiXhosa | Esethu License (other) | gated (auto) | https://huggingface.co/datasets/lelapa/Vukuzenzele_isiXhosa_Speech_Dataset_ViXSD |

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
| IndicCorp v2 | `indiccorp-v2` | IS | pretraining text | 24 Indic languages | CC0 (card text) | open | https://huggingface.co/datasets/ai4bharat/IndicCorpV2 |
| Kathbath | `kathbath` | S | speech (ASR) | 12 Indic languages | CC-BY-4.0 | gated (auto) | https://huggingface.co/datasets/ai4bharat/Kathbath |
| Shrutilipi | `shrutilipi` | S | speech (ASR, All India Radio) | 12 Indic languages | CC-BY-4.0 | gated (auto) | https://huggingface.co/datasets/ai4bharat/Shrutilipi |
| IndicVoices-R | `indicvoices-r` | S | speech (TTS) | 22 Indic languages | CC-BY-4.0 | gated (auto) | https://huggingface.co/datasets/ai4bharat/indicvoices_r |
| Rasa | `rasa` | S | speech (expressive TTS) | Indic languages | CC-BY-4.0 | gated (auto) | https://huggingface.co/datasets/ai4bharat/Rasa |
| Aksharantar | `aksharantar` | S | transliteration | 21 Indic languages | CC (card) | open | https://huggingface.co/datasets/ai4bharat/Aksharantar |
| Pralekha | `pralekha` | S | document alignment | 11 Indic languages | CC-BY-4.0 | open | https://huggingface.co/datasets/ai4bharat/Pralekha |
| IndicXTREME | `indicxtreme` | SP | NLU eval suite | 20 Indic languages | per task (IndicCOPA CC-BY-4.0) | open | https://huggingface.co/datasets/ai4bharat/IndicCOPA |
| Lahaja | `lahaja` | S | speech eval (Hindi, many accents) | Hindi | MIT | gated (auto) | https://huggingface.co/datasets/ai4bharat/Lahaja |
| Samvaad-Hi | `samvaad-hi` | S | dialogue data | Hindi, Hinglish | Apache-2.0 | open | https://huggingface.co/datasets/sarvamai/samvaad-hi-v1 |
| IIT Bombay English-Hindi corpus | `iitb-english-hindi` | S | parallel text | Hindi and English | none declared on the card | open | https://huggingface.co/datasets/cfilt/iitb-english-hindi |
| SOLD (Sinhala Offensive Language Dataset) | `sold` | S | offensive-language classification | Sinhala | none declared on the card | open | https://huggingface.co/datasets/sinhala-nlp/SOLD |
| UrduSpeech | `urduspeech` | S | speech (ASR) | Urdu | none declared | open | https://huggingface.co/datasets/ASLP-lab/UrduSpeech |
| SPRING-INX | `spring-inx` | S | speech (ASR) | 10 Indic languages | none declared | open | https://huggingface.co/datasets/SPRINGLab/SPRING_INX_Malayalam_R1 |

### Southeast Asia

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| SEACrowd | `seacrowd` | IEP | data hub: standardized loaders and benchmarks | nearly 1,000 SEA languages; benchmarks cover 36 | per dataset; hub code Apache-2.0 | open | https://github.com/SEACrowd/seacrowd-datahub |
| SEA-PILE | `sea-pile` | E | pretraining text | vi, id, ta, ms, th, tl, km, lo, my | ODC-By-1.0 plus Common Crawl terms | open | https://huggingface.co/datasets/aisingapore/SEA-PILE-v2 |
| SEA-Instruct | `sea-instruct` | EP | instruction data | 11 including en and zh | ODC-By | gated (auto) | https://huggingface.co/datasets/aisingapore/SEA-Instruct-2602 |
| SEA-HELM | `sea-helm` | EP | eval suite | fil, id, ta, th, vi, jv, su, ms, my, lo | per dataset | gated (auto; some manual) | https://github.com/aisingapore/SEA-HELM |
| SeaExam | `seaexam` | E | exam eval (with SeaBench) | en, zh, id, vi, th | Apache-2.0 | open | https://huggingface.co/datasets/SeaLLMs/SeaExam |
| Cendol Collection | `cendol-collection` | E | instruction data | Indonesian and local languages | Apache-2.0 | open | https://huggingface.co/datasets/indonlp/cendol_collection_v2 |
| WangchanThaiInstruct | `wangchan-thai-instruct` | E | human-written instructions | Thai | CC-BY-SA-4.0 | open | https://huggingface.co/datasets/airesearch/WangchanThaiInstruct |
| ThaiExam | `thai-exam` | E | exam eval | Thai | Apache-2.0 | open | https://huggingface.co/datasets/typhoon-ai/thai_exam |
| Khmer ASR Cultural Dataset | `khmer-speech-dataset` | E | speech (ASR) | Khmer | CC-BY-SA-4.0 | open | https://huggingface.co/datasets/Digital-Divide-Data/khmer-speech-dataset |
| VMLU | `vmlu` | E | knowledge eval | Vietnamese | not yet stated (README: TBU) | download; test answers withheld | https://vmlu.ai |
| LaoBench | `laobench` | E | eval | Lao | Apache-2.0 | open | https://huggingface.co/datasets/BAAI/LaoBench |
| IndoNLU | `indonlu` | E | NLU benchmark | Indonesian | MIT | open | https://huggingface.co/datasets/indonlp/indonlu |
| Vietnamese Curated Dataset | `vietnamese-curated-dataset` | E | pretraining text | Vietnamese | none declared | open | https://huggingface.co/datasets/VTSNLP/vietnamese_curated_dataset |
| WangchanX-FLAN | `wangchanx-flan` | E | instruction data | Thai | other | open | https://huggingface.co/datasets/airesearch/WangchanX-FLAN-v6.1 |
| Typhoon-S sovereign capability dataset | `typhoon-s-sovereign-capability` | E | instruction and eval data | Thai | ODC-By | open | https://huggingface.co/datasets/typhoon-ai/typhoon-s-sovereign-capability-dataset |

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
| TurkishMMLU | `turkishmmlu` | M | knowledge eval | Turkish | none declared; full set by email | open subset (1,845 rows) | https://huggingface.co/datasets/AYueksel/TurkishMMLU |
| ArabicWeb24 | `arabicweb24` | M | pretraining text | Arabic | ODC-By | gated (auto) | https://huggingface.co/datasets/lightonai/ArabicWeb24 |
| HeDC4 | `hedc4` | M | pretraining text | Hebrew | none declared | open | https://huggingface.co/datasets/HeNLP/HeDC4 |
| KazMMLU | `kazmmlu` | M | knowledge eval | Kazakh | CC-BY-NC-4.0 | open | https://huggingface.co/datasets/MBZUAI/KazMMLU |
| Khayyam Challenge | `khayyam-challenge` | M | knowledge eval | Persian | CC-BY-ND-4.0 | gated (manual) | https://huggingface.co/datasets/raia-center/khayyam-challenge |
| Atlaset | `atlaset` | M | pretraining text | Moroccan Arabic | none declared | gated (auto) | https://huggingface.co/datasets/atlasia/Atlaset |
| SMUGRI data | `smugri-data` | M | parallel and monolingual text | low-resource Finno-Ugric languages | CC-BY-4.0 | open | https://huggingface.co/datasets/tartuNLP/smugri-data |
| Icelandic Dynaword | `icelandic-dynaword` | M | pretraining text | Icelandic | CC0-1.0 | open | https://huggingface.co/datasets/danish-foundation-models/icelandic-dynaword |

### Indigenous Americas

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| AmericasNLP shared-task data | `americasnlp-shared-task-data` | X | MT, speech translation | 13 Indigenous languages (2025) | per sub-corpus | open | https://github.com/AmericasNLP/americasnlp2021 |
| ChrEn | `chren` | X | parallel and monolingual text | Cherokee | none found for the data | open | https://github.com/ZhangShiyue/ChrEn |
| Jojajovai | `jojajovai` | X | parallel text | Guaraní | not checked | open | https://github.com/pln-fing-udelar/jojajovai |
| Llamacha monolingual Quechua corpus | `llamacha-quechua` | X | pretraining text | Quechua | Apache-2.0 | open | https://huggingface.co/datasets/Llamacha/monolingual-quechua-iic |

### Closed and restricted: the frontier the open rows are measured against

| Candidate | Slug | Inputs | Modality | Languages | License as stated | Access | Primary source |
|---|---|---|---|---|---|---|---|
| Te Hiku Media te reo Māori corpus | `te-hiku-media-reo-maori-corpus` | X | speech and text | te reo Māori | Kaitiakitanga License | restricted (permission tied to tikanga) | https://papareo.io |
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
| JMMLU | `jmmlu` | `benchmark_eval_data` | E | knowledge eval, Japanese | CC-BY-NC-ND-4.0 | https://huggingface.co/datasets/nlp-waseda/JMMLU |
| CCI3-HQ | `cci3-hq` | `training_synthetic_datasets` | E | pretraining text, Chinese | none declared | https://huggingface.co/datasets/BAAI/CCI3-HQ |
| MAP-CC | `map-cc` | `training_synthetic_datasets` | P | pretraining text, Chinese | CC-BY-NC-ND-4.0 | https://huggingface.co/datasets/m-a-p/MAP-CC |
| CHOCLO | `choclo` | `benchmark_eval_data` | X | eval, Spanish (Latin America) | MIT | https://huggingface.co/datasets/latam-gpt/CHOCLO |
| Trueque Benchmark | `trueque-benchmark` | `benchmark_eval_data` | X | eval, Spanish (Latin America) | Apache-2.0 | https://huggingface.co/datasets/latam-gpt/Trueque-Benchmark-beta-0.1 |

## Parked candidates

| Candidate | Inputs | Reason | Source |
|---|---|---|---|
| AfriBERTa corpus | A | superseded by WURA from the same group | https://huggingface.co/datasets/castorini/afriberta-corpus |
| MasakhaNEWS | A | bundled: carried by `afrobench` | https://huggingface.co/datasets/masakhane/masakhanews |
| MasakhaPOS | A | bundled: carried by `afrobench` | https://huggingface.co/datasets/masakhane/masakhapos |
| AfriQA | A | bundled: carried by `afrobench` | https://huggingface.co/datasets/masakhane/afriqa-gold-passages |
| AfriSpeech-200 | A | boundary: African-accented English, so defined by region and accent rather than language | https://huggingface.co/datasets/intronhealth/afrispeech-200 |
| Lacuna Fund | A | a funder, not a dataset | https://lacunafund.org |
| ALFFA | A | unmaintained: last released around 2016 | https://github.com/getalp/ALFFA_PUBLIC |
| Open Bible African subset | A | a re-host of another dataset | https://huggingface.co/datasets/AfriSpeech/open-bible-speech-african |
| Individual Amharic uploads | A | unverifiable identity: personal uploads with no card saying what the corpus contains or where it came from | https://huggingface.co/datasets/yordanoswuletaw/amharic-pretraining-corpus |
| Other Digital Umuganda repos | A | new SKU of an existing product: Afrivoice's regional releases (Swahili, Ethiopia, V2) | https://huggingface.co/datasets/DigitalUmuganda/Afrivoice_Swahili |
| MasakhaNER 1.0 | A | superseded by MasakhaNER 2.0 | https://github.com/masakhane-io/masakhane-ner |
| Intron Health clinical speech | A | closed and has no addressable artifact of its own; only press coverage | https://www.intron.io/research/ |
| N-ATLaS training data | A | closed; only the model is published, and that is a model artifact | https://techcabal.com/2025/09/25/nigerian-government-awarri-launch-n-atlas/ |
| IndicSentiment | S | bundled: carried by `indicxtreme` | https://huggingface.co/datasets/ai4bharat/IndicSentiment |
| Samanantar | SP | superseded by BPCC | https://huggingface.co/datasets/ai4bharat/samanantar |
| IN22 | S | the BPCC test set, part of that row | https://github.com/AI4Bharat/IndicTrans2 |
| SPRINGLab IndicTTS mirrors | S | re-hosts of the IIT Madras Indic TTS database | https://huggingface.co/datasets/SPRINGLab/IndicTTS-Hindi |
| XL-Sum (Bangla) | S | boundary: a 43-language task set | https://huggingface.co/datasets/csebuetnlp/xlsum |
| Open large Bengali ASR data | S | an aggregation of other corpora | https://huggingface.co/datasets/SKNahin/open-large-bengali-asr-data |
| OOD-Speech | S | its training split is distributed inside Common Voice Bangla | https://arxiv.org/abs/2305.09688 |
| Pashto community uploads | S | no addressable artifact: the sweep found accounts but no specific dataset to emit | https://huggingface.co/datasets?search=pashto |
| Bangla2B+ | S | no artifact of its own: released by request form, and the repository is the BanglaBERT model's | https://github.com/csebuetnlp/banglabert |
| LDC-IL corpora | S | closed long tail: a government catalog of separately licensed corpora, a bundle (ADR-005) | https://data.ldcil.org/accessing-data |
| Indic TTS database | S | held: the homepage timed out on both attempts on 2026-09-23, a transient failure and not a finding; re-check before the next sweep | https://www.iitm.ac.in/donlab/indictts/ |
| Bhashini / ULCA / AIKosh | S | platforms and catalogs, not datasets | https://github.com/bhashini-dibd/ulca |
| FilBench | E | boundary: an evaluation harness over existing datasets, so evaluation_code | https://github.com/filbench/filbench-eval |
| SEA-VL | E | boundary: image-text data, outside the category's modalities | https://huggingface.co/datasets/SEACrowd/sea-vl_crawling |
| SeaEval | E | boundary: a cross-lingual mix not scoped to one region | https://huggingface.co/datasets/SeaEval/SeaEval_datasets |
| LLM-jp Corpus | EP | boundary: 17.8T of v4's 19.5T tokens are English, so not language-defined | https://gitlab.llm-jp.nii.ac.jp/datasets/llm-jp-corpus-v4 |
| Swallow Corpus | E | closed: the build code is public and the corpus is not, so there is no data artifact | https://github.com/swallow-llm/swallow-corpus |
| Sahabat-AI Javanese and Sundanese piles | E | no addressable artifact: named in the Sahabat-AI model card, no release found | https://huggingface.co/GoToCompany |
| SEALD | IEP | no dataset released under the name; its public output so far is the ATLAS catalog | https://aisingapore.org/aiproducts/southeast-asian-languages-in-one-network-data-seald/ |
| ATLAS | IEXP | a catalog, a discovery source for this category, not a product | https://atlas-data.ai |
| Greek MMLU | M | boundary: a translation of MMLU | https://huggingface.co/datasets/ilsp/mmlu_greek |
| Irish FineWeb-Edu | M | boundary: derived from FineWeb | https://huggingface.co/datasets/ReliableAI/irish_fineweb_edu |
| EusCrawl | MP | folded into the Latxa Corpus, which includes it | https://huggingface.co/datasets/HiTZ/euscrawl |
| Danish Gigaword | M | superseded by Danish Dynaword | https://huggingface.co/datasets/danish-foundation-models/danish-gigaword |
| AraBench | M | held, org mapping ambiguous: the only artifact is ARBML's re-host of a dataset QCRI published | https://huggingface.co/datasets/arbml/AraBench |
| Jais pretraining data | M | closed; its only artifact is the Jais paper, which a Jais model product would claim | https://arxiv.org/abs/2308.16149 |
| LDC Arabic Gigaword | M | closed long tail: a single paid LDC catalog item (ADR-005) | https://catalog.ldc.upenn.edu/LDC2011T11 |
| Malyuk | M | derived from UberText and others | https://huggingface.co/datasets/lang-uk/malyuk |
| Axolotl (Nahuatl-Spanish) | X | a sub-source of the AmericasNLP data | https://huggingface.co/datasets/somosnlp-hackathon-2022/Axolotl-Spanish-Nahuatl |
| CMU Wilderness | X | scripts that re-align third-party recordings; distributes no data | https://github.com/festvox/datasets-CMU_Wilderness |
| Global-MMLU | X | boundary: MMLU translated into 42 languages, defined by its task; belongs in benchmark_eval_data | https://huggingface.co/datasets/CohereLabs/Global-MMLU |
| GlotCC | X | boundary: a Common Crawl corpus like MADLAD-400; belongs with it in training_synthetic_datasets | https://huggingface.co/datasets/cis-lmu/GlotCC-V1 |
| Bloom speech and captioning | X | new SKU of an existing product: configurations of the Bloom Library release | https://huggingface.co/datasets/sil-ai/bloom-speech |
| Lanfrica | X | a catalog, a discovery source | https://lanfrica.com |
| ELRA / ELDA catalog | X | closed long tail: a vendor catalog, a bundle rather than a product (ADR-005) | https://catalog.elra.info |
| Appen off-the-shelf datasets | X | closed long tail: a vendor catalog, a bundle rather than a product (ADR-005) | https://www.appen.com/ots-datasets |
| Defined.ai marketplace | X | closed long tail: a vendor catalog, a bundle rather than a product (ADR-005) | https://defined.ai/datasets |
| Karya | X | closed long tail: a vendor catalog, a bundle rather than a product (ADR-005) | https://www.karya.in |
| VoxPopuli | P | boundary: parliamentary speech in 16 mostly major European languages, a general multilingual corpus | https://huggingface.co/datasets/facebook/voxpopuli |
| IrokoBench | AP | bundled: carried by `afrobench`, which is the product; LLM eval (AfriMMLU, AfriXNLI, AfriMGSM), 17 African languages, license Apache-2.0 | https://huggingface.co/datasets/masakhane/afrimmlu |
| AfriSenti | AP | bundled: carried by `afrobench`, which is the product; sentiment, 14 African languages, license disputed: CC-BY-4.0 (repo) vs CC-BY-NC-SA-2.0 (card) | https://huggingface.co/datasets/masakhane/afrisenti |
| MasakhaNER 2.0 | IAP | bundled: carried by `afrobench`, which is the product; NER, 20 African languages, license disputed: AFL-3.0 (card) vs CC-BY-NC (repo) | https://huggingface.co/datasets/masakhane/masakhaner2 |
| MAFAND-MT | AP | bundled: carried by `afrobench`, which is the product; MT (news), 21 African languages, license CC-BY-NC-4.0 | https://huggingface.co/datasets/masakhane/mafand |
| SALT | A | bundled: carried by `afrobench`, which is the product; parallel text and speech, English plus 8 Ugandan languages, license CC-BY-SA-4.0 | https://huggingface.co/datasets/Sunbird/salt |
| NusaX | EP | bundled: carried by `seacrowd`, which is the product; sentiment and MT, Indonesian, English and 10 local languages, license CC-BY-SA-4.0 | https://huggingface.co/datasets/indonlp/NusaX-senti |
| PhoMT | P | bundled: carried by `seacrowd`, which is the product; parallel text, Vietnamese and English, license none declared on the card | https://huggingface.co/datasets/vinai/PhoMT |
| Mangosteen | E | held, org mapping ambiguous: built by VISTEC, the Hub copy sits in AI Singapore's namespace (`aisingapore/WangchanLION-Web`), and it is released as a joint WangchanLION product | https://huggingface.co/datasets/aisingapore/WangchanLION-Web |
| AmericasNLI | PX | held, org mapping ambiguous: the dataset is under the NALA lab's Hub account and the repository under a personal account (`abteen/americasnli`) | https://huggingface.co/datasets/nala-cub/americas_nli |
| IARPA Babel language packs | X | bundle: an LDC product line of separately licensed packs, one per language; one pack's page cannot stand for the line (ADR-005, surface not bundle), and single paid packs are the closed long tail | https://catalog.ldc.upenn.edu/ |
| LORELEI language packs | X | bundle: an LDC product line of separately licensed packs, one per language; one pack's page cannot stand for the line (ADR-005, surface not bundle), and single paid packs are the closed long tail | https://catalog.ldc.upenn.edu/ |
| Uhura | A | bundled: carried by `afrobench` | https://huggingface.co/datasets/masakhane/uhura-arc-easy |
| InjongoIntent | A | bundled: carried by `afrobench` | https://huggingface.co/datasets/masakhane/InjongoIntent |
| Svarah | S | boundary: Indian-accented English, defined by accent rather than language (the AfriSpeech-200 rule) | https://huggingface.co/datasets/ai4bharat/Svarah |

## Decisions recorded on the draft

1. Language-targeted evaluation sets stay in this category, not `benchmark_eval_data`.
2. High-resource languages are out; their candidates were routed to the neighbors.
3. Bundles are the product: AfroBench, IndicXTREME and SEACrowd stand for the datasets they carry.
4. Weights are `adopt: 0.3, cap: 0.7`. Download counts for a low-resource corpus are small by
   construction, so adoption carries less of the overall score than in the neighboring categories.
5. A structured `languages` field was deferred as a nice-to-have. Review on #688 disagrees; see below.

## Open items for promotion

- **A structured `languages` field.** Review on #688 asks for it as a promotion prerequisite: the
  category's central question, coverage by language and modality, cannot be computed from the
  registry schema, which has no field for it. The draft decision above deferred it. This needs a
  maintainer's call before promotion starts. It is a schema change and belongs in its own PR.
- **An operational line for "underrepresented".** The current line is an enumerated list (Chinese,
  Japanese, Korean, Spanish and Portuguese out; the smaller European languages in). Review asks for
  a rule that reproduces those calls rather than a list that states them.
- **Completeness of multi-artifact products.** Several rows carry one representative artifact for a
  product that spans many: Afrivoice, AfriVoices-KE, IrokoBench's members inside AfroBench,
  IndicGenBench, IndicXTREME, SPRING-INX, SEA-HELM, SEACrowd and Bloom Library. Promotion must add
  the rest to the head record; the representative artifact is not the product's whole identity.
- **A ladder rung for a community-governed license** such as the Kaitiakitanga License.
- **Licenses to read at the source:**
  - **Disputed between the Hub card and the repository:** MasakhaNER 2.0 and AfriSenti (now inside
    AfroBench), and CMMLU.
  - **Undeclared:** Inkuba-Mono, Inkuba-Instruct, AfriDocMT, UberText, VMLU, HeDC4, Atlaset,
    UrduSpeech, SPRING-INX, the Vietnamese Curated Dataset and ChrEn.
