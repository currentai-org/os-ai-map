# ATLAS catalog reconciliation, 2026-11-18

A full pass of AI Singapore's ATLAS catalogs against the map, following the partial check of
2026-11-17 (`docs/sweeps/2026-11-17-atlas-candidates.md`). ATLAS is a discovery source here, not a
product in the language categories; `atlas-data` is the row for the platform itself. Every entry
ATLAS publicly lists is in `entries.csv` beside this file, one row per entry, with its link, owner,
license and access as ATLAS states them, the artifacts it names, how it was matched, and its status.

No scoring rule changed and no head product was added. The pull request that carries this record
adds 21 rows to the `language_specific_datasets` tail.

## What ATLAS lists, and how it was read

ATLAS has three products under one site: ATLAS-Data (the dataset catalog), ATLAS-Eval ("the neutral
catalogue of AI evaluations") and ATLAS-Arena (head-to-head model runs, which lists models and votes
rather than resources, so it is not enumerated here). Both catalogs were read on 2026-11-18 from the
public JSON the site itself loads, with no sign-in:

| Catalog | Source | Entries |
|---|---|---|
| ATLAS-Data | `https://www.atlas-data.ai/api/datasets/paginated?page=N&limit=100&sort=alphabetical`, five pages; `metadata.total` reads 458 | 458 |
| ATLAS-Data, per entry | `https://www.atlas-data.ai/api/datasets/<id>/croissant`, whose `sameAs` gives the Hugging Face repository ATLAS imported from (445 of 458; the 13 without one are the nine Open Development corpora, three SEALD datasets and VinBigData) | 458 |
| ATLAS-Eval | the `tables/resources.json` blob named by `https://atlas-eval-prod-public-704744419115.s3.ap-southeast-1.amazonaws.com/public/current.json` (snapshot `2026-11-17-r54-complete`, publication 43) | 2,595 |
| ATLAS-Eval, per entry | `<prefix>/guest/detail/resource/<id>.json`, which carries the links (Hugging Face, GitHub, paper, homepage) | 2,595 |

The enumeration is complete for what a signed-out visitor can see. Two limits: ATLAS-Data's dataset
ids run to 532 while the catalog lists 458, so 74 ids are not public (withdrawn or hidden; nothing
says which), and ATLAS's read-only MCP API needs an account key, so it was not used. ATLAS-Eval is
global, not regional: its snapshot reports 2,595 resources across 776 languages, 1,665 of them
tagged English.

The reads behind every claim here, with their digests, are in the evidence table at the end.

## Match method

Every entry was matched on identifiers, never on names alone, against the head products, the tail
registry, the `aliases` on head products, and every typed artifact (GitHub, Hugging Face dataset and
model, PyPI, npm, crates, arXiv) declared anywhere in `sources/products/` and `sources/registry/`.
Comparison uses `build.identity.fold_for_proposal`.

**Renamed repositories.** ATLAS records many repositories under the name they had when it imported
them. AI Singapore renamed its SEA-HELM task sets in 2026 (`aisingapore/cultural_evaluation-kalahi`
became `aisingapore/Cultural-Evaluation-Kalahi`, `nlr-natural_language_inference` became `NLR-NLI`),
SCB 10X moved its datasets to `typhoon-ai`, Cohere moved `CohereForAI` to `CohereLabs`, and
Mesolitica moved several sets to `malaysia-ai`. Case folding does not catch these, because the
punctuation changed too. The fix was to ask each platform for the canonical id before comparing:

- Hugging Face: `GET https://huggingface.co/api/datasets/<id>` (or `/api/models/<id>`) answers
  with the current `id` when given an old one. 2,223 ids resolved; 18 returned 404.
- GitHub: `GET https://api.github.com/repos/<owner>/<repo>` follows renames and transfers and
  answers with the current `full_name`. 2,137 repositories resolved; 5 returned 404 and one 451.

Both sides were resolved: the ATLAS identifiers, and the map's own declared artifacts in the
dataset, evaluation and safeguard categories. An entry matches when either its raw or its canonical
identifier equals either form of a declared artifact. 104 ATLAS entries carried a non-canonical id.
For 13 of them the match depended on resolution: without it, the twelve renamed SEA-HELM task sets
would have matched only `lindsea`, through the BHASA paper they share, which is the wrong row, and
Terminal-Bench (`laude-institute/terminal-bench`, now `harbor-framework/terminal-bench-1`) would not
have matched at all.

**Weak matches.** A shared arXiv paper or a shared repository is evidence of a relationship, not of
identity. SEACrowd's 271 loaders all cite the SEACrowd paper; PurpleLlama hosts CyberSecEval and
LlamaFirewall alike; `huggingface/datasets` turns up as the homepage of a Mesolitica set. Matches
of that kind were classed `component` (related to the named row) rather than `on_map`, and three that
were plainly spurious (`huggingface/datasets`, `wikimedia/wikipedia` and `cais/mmlu` given as the
source of three Mesolitica derivatives) were triaged as unmatched.

**A future matcher** can reuse this directly: resolve both sides through the platform APIs before
comparing, keep a paper or host-repository match out of the identity verdict, and treat
`SEACrowd/*` on Hugging Face as hub loaders. No pipeline is built here.

## The cutoff

ATLAS-Data was triaged in full. ATLAS-Eval was matched in full, but only part of it was triaged.
Before triage, this record declared a retrieval cutoff, as `docs/workflows/discover-candidates.md`
asks for a volume nobody can review: an unmatched ATLAS-Eval resource is triaged when at least half
of its non-English target languages are Southeast Asian, using the ISO 639-3 list in the note below.
That is 97 resources. The other 2,351 unmatched ATLAS-Eval resources are recorded as `not_triaged`.
They are mostly English and Chinese benchmarks and global multilingual sets, and the cutoff makes no
claim about them. ATLAS-Eval's own `southeast-asia` region tag was not used, because it marks
Chinese-language benchmarks as Southeast Asian.

The Southeast Asian list: ind msa zsm zlm min jav sun ban bug ace bjn mad bbc btx bts ljp mak sas nij
mvp gor tet tha tts nod sou lao khm vie mya shn kac ksw kjp blk rki fil tgl ceb ilo hil war pam bik
bcl pag tsg mdh kyk krj cps akl msb mbb suc yka tdt abz urk mnw cja cjm hmn mww blt tyz kxm.

## Counts by status

| Status | ATLAS-Data | ATLAS-Eval | Meaning |
|---|---|---|---|
| `on_map` | 26 | 97 | the entry is a row on the map, or a subset that row declares |
| `component` | 298 | 58 | part of, or related through a shared artifact to, another row (255 are SEACrowd hub loaders, 11 more load IndoNLU tasks) |
| `added_to_tail` | 6 | 14 | a new tail row in this PR (plus `bhasaanuvaad`, assembled from eight entries) |
| `eval_candidate_needs_ruling` | 13 | 24 | an evaluation set that passes the language test; the eval-set roster needs a ruling |
| `fails_language_test` | 1 | 9 | every target language is high at both ends; listed for the category it would go to |
| `out_of_scope` | 8 | 5 | fails a membership test for another reason |
| `held` | 79 | 15 | license or provenance not settled; not proposed |
| `parked` | 27 | 22 | left off for a stated reason: a boundary question, a derivative, or a 2026-11-17 decision |
| `not_triaged` | 0 | 2,351 | outside the cutoff, with no artifact match |
| **Total** | **458** | **2,595** | 3,053 |

The discovery workflow's reconciliation, over the 702 triaged entries (all of ATLAS-Data, plus the
155 matched and 97 cut-off ATLAS-Eval entries):

```
raw_signals       702 = duplicate_signals 478 + unique_candidates 224
unique_candidates 224 = accepted 21 + parked 203
```

Duplicates are the 479 `on_map` and `component` entries less one: the eight BhasaAnuvaad entries fold
into one candidate, and one of them is counted as its signal. Accepted is the 21 rows added (20 entries
plus BhasaAnuvaad); parked is every other unique candidate, whatever its status.

## Added to the tail

All 21 rows go to `sources/registry/language_specific_datasets.yaml`. Each is a dataset built for an
underrepresented language or a set of related ones, published as a corpus or labeled set rather than
as a benchmark (the kind test), with a license stated on the artifact. Rows carry identity and
artifacts only; nothing is scored. The language reading is from
`currentai.language_representation.classification` on 2026-11-18.

| Row | Languages (class) | License on the artifact | Note |
|---|---|---|---|
| `gigaspeech-2` | Thai, Vietnamese (mid); Indonesian (high) | Apache-2.0, automatic gate | about 30,000 raw and 22,000 refined hours of ASR speech |
| `thai-ser` | Thai (mid) | CC BY-SA 4.0 | speech emotion, 41 hours; also a SEACrowd hub member |
| `thai-dialect-corpus` | Thai (mid) | MIT (repository) | 840 hours of read speech, three regional dialects; ATLAS attributes it to Chulalongkorn University |
| `thainer-v2` | Thai (mid) | CC BY 3.0 | named-entity corpus |
| `wisesight-sentiment` | Thai (mid) | CC0 1.0 | 26,737 labeled social messages; also a SEACrowd hub member |
| `thai-toxicity-tweet` | Thai (mid) | CC BY-NC 3.0 | toxicity-labeled tweets |
| `tlunified-ner` | Tagalog (low) | GPL-3.0 | about 7,800 annotated documents |
| `cebuaner` | Cebuano (very low) | CC BY-NC 4.0 | 4,000+ annotated news articles; also a SEACrowd hub member |
| `vietmed` | Vietnamese (mid) | MIT | medical ASR, 16 labeled and 2,200 unlabeled hours |
| `neu-esc` | Vietnamese (mid) | Apache-2.0, automatic gate | 32,966 labeled forum comments |
| `voxvietnam` | Vietnamese (mid) | CC BY-NC 4.0, automatic gate | speaker recognition; ATLAS attributes it to HUST |
| `vitosa` | Vietnamese (mid) | CC BY-NC-ND 4.0, automatic gate | 25 hours of speech with toxic spans |
| `vimd` | Vietnamese (mid) | CC BY-NC-ND 4.0 | 102 hours across 63 provincial dialects |
| `vibidlqa` | Vietnamese (mid) | Apache-2.0 | bidding-law QA, LLM-generated and expert-checked |
| `kesalahan-tatabahasa-instructions` | Malay | MIT | synthetic Malay grammar-correction instructions |
| `mixtral-factual-qa` | Malay | Apache-2.0 | QA generated from Malaysian sources |
| `malaysian-emilia-annotated` | Malay | CC BY-NC 4.0 | 3,169 hours of Malaysian speech with Data-Speech annotations |
| `bhasaanuvaad` | 14 Indian languages | CC BY 4.0 on each component, automatic gate | 44,000 hours of speech translation (arXiv 2411.04699) |
| `seald-cultural-knowledge` | Filipino, Burmese, Tamil (low); Thai (mid); Indonesian (high) | CC BY-SA 4.0 per ATLAS | 12,647 prompt-response pairs, hosted on ATLAS only |
| `seald-cultural-local-wisdom` | as above, plus Javanese, Sundanese | CC BY-SA 4.0 per ATLAS | 2,808 pairs, hosted on ATLAS only |
| `seald-mdw` | Filipino (low), Indonesian (high) | CC BY-SA 4.0 per ATLAS | 3,830 pairs for migrant domestic workers, hosted on ATLAS only |

Malay: `msa` is high at both ends, Standard Malay (`zsm`) is unresolved between mid and low, so the
purpose test decides, and each Mesolitica set was built for Malay. This is the "separate Malay check"
the 2026-11-17 record left open: of Mesolitica's 67 entries, these three carry a license and pass;
`mixtral-magicoder` (MIT) is English-led code instructions and fails the purpose test, two more are
English-only, and the other 61 have no license on their cards and are held.

BhasaAnuvaad is listed by ATLAS as eight separate repositories (IndicVoices-ST, Mann-ki-Baat, NPTEL,
SeamlessAlign, Spoken-Tutorial, UGCE-Resources, Vanipedia, WordProject); its paper presents them as
one corpus, so it is one row, declared by its GitHub repository and paper. No component repository
is declared, because each one's downloads would then stand for the whole corpus.

The SEALD sets have no repository anywhere: ATLAS hosts them and signed-in users download them. Their
only artifact is the ATLAS dataset page, so they carry no adoption signal. For the homepage route
`atlas-data.ai` is added as an AI Singapore handle, on the strength of ATLAS's privacy policy
("ATLAS-Data is an open-source data platform operated by AISG").

Three rows (`cebuaner`, `thai-ser`, `wisesight-sentiment`) are also loaded by SEACrowd. ATLAS lists
each twice, once as the SEACrowd loader and once under its own publisher, and only the second is a
candidate. A promotion should set `lineage.part_of: [seacrowd]` on them.

Thirteen organizations are new. Ten are recorded under the account that publishes the data, as
individuals or with type `unknown`, because no primary page ties the account to the institution
ATLAS names: `speechcolab`, `slscu`, `pythainlp`, `hustep-lab`, `ljvmiranda921`, `josephimperial`,
`leduckhai`, `hung20gg`, `nguyendv02`, `ntphuc149`. Three are institutions with a stated seat,
recorded in `countries/ledger.jsonl`: `mesolitica` (MY), `tmu-nlp` (JP) and `uit-vnu-hcm` (VN).

## Evaluation sets that need a roster ruling

`language_specific_eval_sets` takes additions only by a recorded ruling, so none of these was added.
Each passes the language test and was published as a benchmark or test set. Several will need card
reads before their depth can be computed; the speech sets have no depth measurement model.

| Entry | Languages | License | Artifact |
|---|---|---|---|
| IndoMMLU | Indonesian + 9 local languages | MIT | `indolem/IndoMMLU` |
| LoraxBench | Indonesian + 19 local languages | none on the card | `google/LoraxBench` |
| DeepSEA | 12 SEA languages | Apache-2.0 (code) | `google-research/deep-sea` |
| IndoNLG | Indonesian, Javanese, Sundanese | Apache-2.0 | `IndoNLP/indonlg` |
| ID-CSQA | Indonesian, Sundanese | CC BY-NC-SA 4.0 | `rifkiaputri/id-csqa` |
| SEATauBench | five SEA languages | MIT | `SEACrowd/SEATauBench` |
| SeaEval | seven, including English, Chinese, Spanish (close on purpose) | CC BY-NC 4.0 | `SeaEval/SeaEval_datasets` |
| SEA-SpeechBench | 11 SEA languages, speech | MIT (repository) | `SEA-SpeechBench/SEA-SpeechBench` |
| SeaLLMs-Audio benchmark | Indonesian, Thai, Vietnamese, speech | Apache-2.0 | `DAMO-NLP-SG/SeaLLMs-Audio` |
| SEABED | Indonesian, Malay, Thai, speech | CC BY-NC-ND 4.0 | `CentificAIResearch/SEABED` |
| MalayMMLU | Malay (purpose test decides) | none on the card | `UMxYTLAILabs/MalayMMLU` |
| NitiBench+ | Thai | CC BY 4.0, automatic gate | `VISAI-AI/nitibench-plus` |
| ThaiSafetyBench | Thai | Apache-2.0 | `typhoon-ai/ThaiSafetyBench` |
| Typhoon ASR benchmark | Thai, speech | CC BY 4.0 | `typhoon-ai/gigaspeech2-typhoon` |
| ViGLUE, VLUE, VMMU, VIVID, ViMMRC 2.0, VlogQA, ViSQA, VM14K, ViMedCSS, VietMix | Vietnamese | various; see `entries.csv` | see `entries.csv` |
| IndicNLG Benchmark (five ATLAS entries, one product) | 11 Indic languages | CC BY-NC 4.0 | `ai4bharat/IndicHeadlineGeneration` and four siblings |
| IndicGLUE | Indic languages | "other" | `ai4bharat/indic_glue` |
| Bhasha-Abhijnaanam | 22 Indic languages | CC0 1.0 | `ai4bharat/Bhasha-Abhijnaanam` |
| SRUTI (two ATLAS entries) | Bhojpuri, Hindi, speech | CC BY-SA 4.0 and CC BY 4.0 | `ai4bharat/Rural_Women_Bhojpuri`, `ai4bharat/Rural_Women_ASR_v2` |
| SpeechArenaBench, MANGO | Indic languages, speech | MIT; CC BY 4.0 | `ai4bharat/SpeechArenaBench`, `ai4bharat/MANGO` |
| Hindi ARC and HumanEval translations | Hindi | CC BY-SA 4.0; CC BY 4.0 | `ai4bharat/ai2_arc-hi`, `ai4bharat/human-eval` (low confidence: machine-translated) |

## Failing the language test

Every target language of these is high at both ends, so under the line both language categories read
(R-2026-10-30-d, R-2026-11-10-j) they would go to `benchmark_eval_data` or, for corpora,
`training_synthetic_datasets`, as IndoNLU did (R-2026-11-11-b). They were not emitted: the 2026-11-17
record left IndoCulture as a question for whether `benchmark_eval_data` wants Indonesian cultural
benchmarks, and the rest follow it. Benchmarks: IndoCulture (both catalogs), COPAL-ID, ID-MoCQA,
IndoCareer, IndoNutriQA, the Indonesian mental-health NER set. Corpora: IndoToxic2024, the Indonesian
Twitter Emotion Dataset, Liputan6.

## Held

- **License or provenance not stated (93 entries).** 61 Mesolitica sets with no license on their
  cards; ai4bharat sets with no license field (the Airavata translated evaluation sets and
  instruction data, `wiki-translate`, `IndicMTEval` and others); `IndicCMix`, whose card cannot be
  read without approval; the FilBench data (`UD_Tagalog-NewsCrawl` and the FilBench repository);
  Vietnamese sets with no release license (UIT-ViQuAD, UIT-ViNewsQA, VSMEC, VLSP 2018 ABSA, ViLLM-Eval,
  VN-MTEB, VLegal-Bench, ViCocktail, PhoAudiobook); NusaAksara, BatakJailbreakBench, Tatabahasa,
  SEA-BED; VinBigData's corpus, which ATLAS lists with neither a link nor a license.
- **SEASafeguardBench and SEA-Safeguard-Train (R-2026-11-17-b).** See the next section.

## SEASafeguardBench and SEA-Safeguard-Train

Re-checked against public evidence on 2026-11-18.

- **SEASafeguardBench** (`aisingapore/SEASafeguardBench`). The Hub record still shows no license in
  its card metadata or tags, and access still needs manual approval. Its paper, by AI Singapore and
  VISTEC authors and published in Findings of ACL 2026, has a licensing paragraph the 2026-11-17 check
  did not cite: "For licensing, we adopt the original WildGuard (Han et al., 2024) license for the
  generic subset, CC-BY for the ITW subset, and ChatGPT's license for the CG subset due to its use of
  GPT-generated data. This may restrict the CG subset's usage, particularly in some industry settings,
  but does not affect academic research."
- **SEA-Safeguard-Train**, which is published as `aisingapore/SEA-Safeguard-Train-Cultural-v3`. No
  license in the card metadata or tags, manual approval, and no paper or page that states terms.

So public evidence now states SEASafeguardBench's terms per subset, from the publisher, but not on
the release itself, and one of the three subsets is under OpenAI's terms rather than a data license.
Nothing public settles SEA-Safeguard-Train. Both stay held under R-2026-11-17-b. Whether the paper
counts as AI Singapore confirming the benchmark's license is the maintainer's call; it is listed below
as a question, not proposed as a release.

## Out of scope and parked

- Out of scope: English-only sets (FBI, FERMAT, Focus, RiddleBench, Svarah), English-led code or
  reasoning data in Mesolitica's catalog, multi-language sets not built for a language or related set
  (AudioBench, the Multilingual Sycophancy Benchmark, UGTPhon, a US code-submission dataset), and an
  evaluation study with no dataset release.
- Parked, boundary: 20 vision-task datasets (Vietnamese VQA, captioning and OCR sets, Khmer scene text,
  Baybayin, Burmese handwritten digits, Indonesian receipts, Indic document layout) and one sign-
  language video set (INCLUDE), since the corpus category has no vision-task precedent; SEA-VL
  (four entries), which is defined by region and culture rather than language; three leaderboards
  (ThaiLLM, SEA-LION Voice Agent, Malay LLM), whose `evaluation_code` membership was not checked.
- Parked, derivative: a cleaned IndicVoices copy, filbench's instruction-formatted CebuaNER and
  UniversalNER.
- Parked by the 2026-11-17 record and not re-triaged: OpenOrca-Viet, ViLM's VLSP evaluation sets,
  StingrayBench, Indic-Bias, the nine Open Development corpora.

## Members of suites under concurrent sweeps

AfroBench and IndicXTREME are being swept separately, and SEA-HELM's member rows landed in #1094.
Nothing here touches their product or score files. ATLAS lists these members and variants, recorded
as `component`:

- AfroBench: AfriADR, AfriMGSM, AfriMMLU, AfriQA, AfriSenti, AfriXNLI, MAFAND, MasakhaNEWS,
  MasakhaPOS, SALT, Uhura.
- IndicXTREME: IndicCOPA, IndicQA (plus romanized, Devanagari and translated variants),
  IndicSentiment, IndicXParaphrase, Naamapadam, and translated IndicXNLI and IndicXParaphrase.
- SEA-HELM: eight task repositories under their old names, BURMESE-SAN, SEA-HELM Audio, IFEval-Th,
  and the external sets its record names (Batayan, IndoNLI, MLHSD, NusaX, UIT-VSFC, ViHSD).

## Other observations

- IndicMSMARCO and MSMARCO-XI are the benchmark and training halves of IndicRAGSuite
  (arXiv 2506.01615), which is on the map as `indic-rag-suite`; neither repository is declared there.
- Samanantar is drawn into BPCC (the `bpcc` record lists "BPCC-Mined (Samanantar 19.4M, ...)") and has
  its own paper and repository, so it is a candidate member row.
- One tail row carries a renamed repository: `arena-hard-auto` declares `lmarena/arena-hard-auto`,
  which GitHub now serves as `Arena-OSS/arena-hard-auto`. It is corrected in #1104.

## Questions for the maintainer

Each has a proposed answer; none was acted on.

1. Does the SEASafeguardBench paper's licensing paragraph count as AI Singapore confirming the
   benchmark's license under R-2026-11-17-b? Proposed: yes for the benchmark, read as mixed per
   subset, with the content-generation subset's OpenAI terms treated as a use restriction; the manual
   gate is scored as it stands. SEA-Safeguard-Train stays held.
2. Should SEACrowd members that are published on their own get tail rows? The 2026-11-17 record left
   all of them off, while the identity guide allows a member row linked by `part_of`. Proposed: yes,
   when ATLAS or another source lists the member under its own publisher, as done here for three;
   not from the SEACrowd loader alone.
3. Are vision-task datasets for an underrepresented language (VQA, OCR, captioning, scene text) in
   `language_specific_datasets`? Proposed: yes when defined by the language, as the purpose test reads,
   which would move the 20 parked here into scope.
4. Should a tail candidate with no license on its card be emitted? This record held 93 such entries,
   following the 2026-11-17 record. Proposed: keep holding them, because the tail is public and a row
   with no license reads as an omission rather than a finding.
5. Does `benchmark_eval_data` take single-language benchmarks for languages above the line (the nine
   Indonesian sets here)? Proposed: yes, as IndoNLU's move set the precedent, emitted in a batch of
   their own.
6. Should a suite's undeclared sibling repositories be declared on it (IndicMSMARCO on
   `indic-rag-suite`)? Proposed: no; declare only the repository whose downloads measure the product,
   and record siblings in the product's comments.
7. Should a future ATLAS sweep triage all of ATLAS-Eval rather than a Southeast Asian cutoff?
   Proposed: no; match it in full each time, as here, and triage by the language categories' own
   regions in separate passes.

## Pull requests

- #1103 (this one): the record, `entries.csv`, the 21 tail rows, 13 organizations, their handles and the
  country ledger.
- #1104 corrects `arena-hard-auto`'s repository to its canonical name.

## Evidence

Read with `uv run python -m build.fetch_source` on 2026-11-18.

| URL | Status | SHA-256 |
|---|---|---|
| https://huggingface.co/api/datasets/speechcolab/gigaspeech2 | 200 | `46c2f54297cdc353ed3c300de3bbad0fe83771e3c17d4fb497b07117093dabe0` |
| https://api.github.com/repos/SpeechColab/GigaSpeech2 | 200 | `2902ac038fda6abe09d44f9436b59ec2081f71292a30f19c1836abcc0ab22853` |
| https://huggingface.co/api/datasets/airesearch/thai-ser | 200 | `3ace33bde07966c2efff6c448d3d64b95b6191a7fd73c957323703b538c7fb6f` |
| https://api.github.com/repos/SLSCU/thai-dialect-corpus | 200 | `26bd3d330812251aa2df0072d4f13ac5c5003c319e7163b59f33c294df869b61` |
| https://huggingface.co/api/datasets/pythainlp/thainer-corpus-v2 | 200 | `68dd5e48ff6059a8d1a8ee55648c83e77897331de27666b666d17144ab70124a` |
| https://huggingface.co/api/datasets/pythainlp/wisesight_sentiment | 200 | `4e77fa01bbcf8e1845720eee49da4d4a1d9e1eca2ae77d96398f55909b851bc5` |
| https://api.github.com/repos/PyThaiNLP/wisesight-sentiment | 200 | `048bc8abc8acf25842904e84405ca224132138339f122101e5def815100c6244` |
| https://huggingface.co/api/datasets/ljvmiranda921/tlunified-ner | 200 | `e3f3f2c74d9b4eb6656b606072dfe19cf8bae9f0d386ee2654402faf2d9acada` |
| https://huggingface.co/api/datasets/josephimperial/CebuaNER | 200 | `d6181c67fe923c0b06b2ba33244ea825ad805e96579587e3cf146949dc7dde5c` |
| https://huggingface.co/api/datasets/leduckhai/VietMed | 200 | `0d78356b98ae27fd64eb8db7a999a9789b18ed66a2d8913818b1a9268a4da3d7` |
| https://huggingface.co/api/datasets/hung20gg/NEU-ESC | 200 | `2bdce7b9f64c4f5519004b96c98d8b8e722d31f74955ded77e2086f9d4d09356` |
| https://huggingface.co/api/datasets/hustep-lab/VoxVietnam-Dataset | 200 | `d5285a9ae0ee967d002eac17bce0824186442f690589cac550b8f4fb008fd942` |
| https://huggingface.co/api/datasets/UIT-ViToSA/ViToSA-1.0 | 200 | `02d089ddfa96606485bed186f94e98c1a7fad2c3cbc0f495e971205e699ce91c` |
| https://huggingface.co/api/datasets/nguyendv02/ViMD_Dataset | 200 | `e857408be29bc9795b68632ce83fcb85efa92597c37537b19e77943adba05199` |
| https://huggingface.co/api/datasets/ntphuc149/ViBidLQA_v1 | 200 | `d157a4ec15dfd3f55df739cc31c8bb9f12c5b8f9a74f6d6a6f7e159c55341ceb` |
| https://api.github.com/repos/ntphuc149/ViLQA | 200 | `62ced2c5eb7981b429a6d3ef7c3f92aef9567a5289daff153513be0272cdf3fc` |
| https://huggingface.co/api/datasets/tmu-nlp/thai_toxicity_tweet | 200 | `75ca12ba16f1b5970c1dc0f9b3d6c5e2775aae967ec962417371ae183e13a8c6` |
| https://api.github.com/repos/tmu-nlp/ThaiToxicityTweetCorpus | 200 | `bd6362675f140a0c6c1b73be7afcf1633fb12d07c25af761ed212eeffa4ab380` |
| https://huggingface.co/api/datasets/mesolitica/kesalahan-tatabahasa-instructions | 200 | `dae20f9308b1cbffc48a19e9b0bc2b281a814b22e40a7dee77b6d0a9436b35ae` |
| https://huggingface.co/api/datasets/mesolitica/mixtral-factual-QA | 200 | `3f59173eec5493eff93dc77dd64da9d76adf086508d4f33ecc7511cb38489d36` |
| https://huggingface.co/api/datasets/mesolitica/Malaysian-Emilia-annotated | 200 | `e34de969135135024d99aee3a192ceb5ce65def57244662dc088b8395901976f` |
| https://api.github.com/repos/AI4Bharat/BhasaAnuvaad | 200 | `d0afee1b030feb72e768ac57ec17e7a6b915c12c5459bd932a147186a4f2eae2` |
| https://www.atlas-data.ai/api/datasets/438 | 200 | `2c027b64b430ca11ce3f43b65b9eb051dec76b31e6241b4482e35012e1027517` |
| https://www.atlas-data.ai/api/datasets/439 | 200 | `846d8199ddc5a5200ba2eebbc3426d8d5aa126961c33c1ab9698553e36924203` |
| https://www.atlas-data.ai/api/datasets/440 | 200 | `bc74edff367ab4b5c3df031d0735bb9b525166d185fc81053c8eb6e97b7adefc` |
| https://www.atlas-data.ai/en/datasets/438 | 200 | `47756cafdd70771ed0420ede0aa6d658e05bc288f5000621ac9dd9a3590a7348` |
| https://www.atlas-data.ai/en/datasets/439 | 200 | `6d0d9e5be5bb5d47d749267a391e87b62a9a82c15808cf00040087b37b80362b` |
| https://www.atlas-data.ai/en/datasets/440 | 200 | `5907feb71651012b73789f1648a2088fdb7c2bd6a01dd775ce2e0bc7c9d23aa5` |
| https://api.github.com/orgs/mesolitica | 200 | `2617e0e494e609a1a824e6242596ff40c0c779ac8a6dbbfc4278a5bb3597f2d3` |
| https://api.github.com/orgs/tmu-nlp | 200 | `e69c18ee9ccf879a1c57abdd72a625a9c9976e11c81bbecb090f0c2c4e2a77ba` |
| https://www.uit.edu.vn/ | 200 | `e69f18fea3d21c2e27381e7597f0485ce42c54e429020013811b0e2cb898e79b` |
| https://api.github.com/orgs/PyThaiNLP | 200 | `62fdb1b068e4c9e9dca972bf2b5dbd7817b79dc86ab66934389416379fbd1313` |
| https://www.atlas-data.ai/api/datasets/paginated?page=1&limit=100&sort=alphabetical | 200 | `173f68a08d51045fbd6aa52226a9deabdcb309625a5d30f09cbed460147a3ed8` |
| https://atlas-eval-prod-public-704744419115.s3.ap-southeast-1.amazonaws.com/public/current.json | 200 | `5c3a8f4890812d60c6c7ad2b75699a87afc3b09885c17006feac53e5d982b05a` |
| https://api.github.com/repos/Arena-OSS/arena-hard-auto | 200 | `6b9743a1c09732d239a0d98fcc37303610e7599bc4bafd104643024c35b5ee34` |
| https://api.github.com/repos/lmarena/arena-hard-auto | 200 | `6b9743a1c09732d239a0d98fcc37303610e7599bc4bafd104643024c35b5ee34` |
| https://huggingface.co/datasets/ai4bharat/Rural_Women_Bhojpuri/raw/main/README.md | 200 | `0266e723c7458685769b2951f48ccdf98b775bef9e8d74e927b1a2f6e88acf02` |
| https://huggingface.co/datasets/ai4bharat/Rural_Women_ASR_v2/raw/main/README.md | 200 | `889b10def53a217a3cc3dd70dc5ed64b37bae82f23508c1a7dae086361a7f3e6` |
| https://huggingface.co/datasets/filbench/UD_Tagalog-NewsCrawl/raw/main/README.md | 200 | `85d9e608f8c9e952966b2b22e9f3d6be7050ef68cfa4196c349c59a6d3bb9aed` |
| https://huggingface.co/datasets/mesolitica/kesalahan-tatabahasa-instructions/raw/main/README.md | 200 | `5a47b9ff6d2bb0c6bd50641a6435d795fe798033830981752977ecf3cfa2d55f` |
| https://huggingface.co/datasets/mesolitica/mixtral-factual-QA/raw/main/README.md | 200 | `c85158471b3f5a1c1cf8e2fcc2e0ab1d30465be9afae0ee770aeeb9ebb722d39` |
| https://huggingface.co/datasets/mesolitica/mixtral-magicoder/raw/main/README.md | 200 | `c883a1c0d45d1916fe37a0353a04c87bf39424c3a5ffa4880f645edc3d1a0fcf` |
| https://huggingface.co/datasets/mesolitica/Malaysian-Emilia-annotated/raw/main/README.md | 200 | `4528c2403d458d24a305a14ec51067c803656a1f3493ac62b485e23c1b487cad` |
| https://raw.githubusercontent.com/SLSCU/thai-dialect-corpus/HEAD/README.md | 200 | `bd74307ea2b51c79cbaa1225d403b24590576e0712f2b8f53fd113a6f8e881ed` |
| https://raw.githubusercontent.com/SLSCU/thai-dialect-corpus/HEAD/LICENSE | 200 | `0343b4e33203a9cfa33cce036d0459655a185fcffb4965913f93000560bdfc68` |
| https://huggingface.co/api/datasets/aisingapore/SEASafeguardBench | 200 | `721647052ecfe2f99bde8602cf0c3bb15276eab55931bf942cf396bdf038139d` |
| https://huggingface.co/api/datasets/aisingapore/SEA-Safeguard-Train-Cultural-v3 | 200 | `f17d3c7180be57c587d0daa0fc0bad3eb9e00f92da4911f9c8d97c82d56f03cd` |
| https://huggingface.co/datasets/aisingapore/SEASafeguardBench | 200 | `3284e1ff7adafeb66d327304191c340a87e2c96d22e8c8bfffa0b565a46766f7` |
| https://huggingface.co/datasets/aisingapore/SEA-Safeguard-Train-Cultural-v3 | 200 | `905768d11d4e1b4768ba4eac11d554cb0ecafb581544760dc0cb5dd2e7dab67e` |
| https://arxiv.org/abs/2512.05501 | 200 | `ac52d40c3ca0ceb5ea5a83569de8ab59a0a245b7c4ca453d5afd2cf328062d03` |
| https://aclanthology.org/2026.findings-acl.194.pdf | 200 | `ac5778ad6bdea0c424afc5987d1337980a116249f6129104fd6f358aa0409c25` |
| https://arxiv.org/abs/2411.04699 | 200 | `008424d435b2ca616de501b83c2683503af3d88626d827984729758d2fa5a682` |
| https://arxiv.org/abs/2506.09653 | 200 | `47adefe4c673801a980d524afcb181795858f9926fabdcf878195ffa8ff3876e` |
| https://arxiv.org/abs/2506.01615 | 200 | `c6575fc7c66983d29bf20651b97f9a0085bb6a34485d6b5c5705ab779d8b70f9` |
| https://atlas-eval-prod-public-704744419115.s3.ap-southeast-1.amazonaws.com/public/blobs/guest/tables/resources.0630e5a48dbac719.json | 200 | `0630e5a48dbac719067d88e497e904e4423df0154eddde0beca4ec6e84aa00c2` |
| https://www.atlas-data.ai/privacy-policy | 200 | `85b73852f06b2d591deff7e4933f7242c98ca0ef65173f368f83e04412f3f306` |
