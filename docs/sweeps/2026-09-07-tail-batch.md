# Tail batch — 2026-09-07

Machine-generated review sheet for the weekly candidate sweep (`discover-candidates`). One PR,
label `tail-batch`. Nothing here is scored: every row carries identity and artifacts only.
A human accepts or rejects this batch; automation opened it and does not merge it.

Second revision. The four corrections a first review asked for are folded in and marked where
they land: every emitted row now carries an addressable identifier that is not a URL, mirrors and
acknowledged derivatives are counted as duplicates rather than as unique candidates, every parked
candidate is listed individually with its identifier, source URL, fetch date and reason, and every
field on an emitted row is traced to the observation or declared mapping that produced it. See
**Revisions** at the end for the full list.

## Window and scope

- **Window swept:** 2026-09-07 (single day). All fetches dated 2026-09-07.
- **Categories swept:** the six the map's own gap arithmetic reads at maturity stage 3 or below —
  `dataset_processing_tools` (stage 2), `edge_hardware`, `safeguards`, `base_pretrained`,
  `finetuned_chat`, `compilers` (all stage 3). Category list and lifecycle status read at run time
  through `build.taxonomy.category_statuses(taxonomy)`; all 18 categories are `published`, so every
  row here is promoted later through `add-product`, not `promote-category`.
- **Categories that emit rows:** five. `edge_hardware` was swept and emits nothing — see
  **`edge_hardware`: swept, nothing emitted** below.
- **Not reached:** the warehouse discovery pool (`currentai.entities.repos`). No `OSO_API_KEY` in
  this environment, so the pool was unreachable — reported as a gap, not filled with a guess. It is
  an enrichment and consolidation step, never a rejection step, so its absence does not invalidate
  the dedup below; it does mean multi-signal consolidation rested on self-dedup alone.

## Reconciled counts

| count | value |
|---|---|
| `raw_signals` | 1819 |
| `duplicate_signals` | 708 |
| `unique_candidates` | 1111 |
| `accepted` | 52 |
| `parked` | 1059 |

- `raw_signals = duplicate_signals + unique_candidates` → 1819 = 708 + 1111 ✓
- `unique_candidates = accepted + parked` → 1111 = 52 + 1059 ✓

Each accepted signal maps to exactly one emitted registry row: 52 accepted signals,
52 rows. Every one of the 1059 parked candidates is listed individually below,
215 with a reason of its own and 844 with the disclosed retrieval cutoff
that excluded it. Every duplicate is listed too, with what it folded onto, so the reconciliation
can be reproduced from this sheet without re-running a query.

### Duplicate breakdown

| why | signals |
|---|---|
| a release or SKU of a family already on the map (model_families / release-suffix rule) | 411 |
| same signal returned by more than one query (self-dedup) | 199 |
| resolves to a head product already on the map | 77 |
| mirror, conversion or acknowledged derivative of another signal or head product | 7 |
| other identity fold (see the row) | 7 |
| same product as another row this batch emits | 4 |
| ruled on in sources/resolution_ledger.yaml | 3 |

## Sources swept

Every query, its URL, and how many rows it returned. All executed 2026-09-07.

### GitHub repository search (36 queries)

| query | request URL | rows returned |
|---|---|---|
| `dpt_dedup (dataset_processing_tools)` | https://api.github.com/search/repositories?q=dataset%20deduplication%20llm%20training%20data&sort=stars&order=desc&per_page=30 | 7 |
| `dpt_pipeline (dataset_processing_tools)` | https://api.github.com/search/repositories?q=training%20corpus%20curation%20pipeline%20llm&sort=stars&order=desc&per_page=30 | 2 |
| `dpt_crawl (dataset_processing_tools)` | https://api.github.com/search/repositories?q=web%20crawl%20text%20extraction%20pipeline&sort=stars&order=desc&per_page=30 | 4 |
| `dpt_synth (dataset_processing_tools)` | https://api.github.com/search/repositories?q=synthetic%20data%20generation%20llm&sort=stars&order=desc&per_page=30 | 30 |
| `dpt_docparse (dataset_processing_tools)` | https://api.github.com/search/repositories?q=document%20parsing%20ocr%20pipeline%20llm%20dataset&sort=stars&order=desc&per_page=30 | 1 |
| `dpt_quality (dataset_processing_tools)` | https://api.github.com/search/repositories?q=data%20filtering%20quality%20corpus%20nlp&sort=stars&order=desc&per_page=30 | 1 |
| `dpt_t_synthetic (dataset_processing_tools)` | https://api.github.com/search/repositories?q=topic%3Asynthetic-data&sort=stars&order=desc&per_page=30 | 30 |
| `dpt_t_datacentric (dataset_processing_tools)` | https://api.github.com/search/repositories?q=topic%3Adata-curation&sort=stars&order=desc&per_page=30 | 30 |
| `dpt_t_dedup (dataset_processing_tools)` | https://api.github.com/search/repositories?q=topic%3Adeduplication&sort=stars&order=desc&per_page=30 | 30 |
| `dpt_t_webscraping (dataset_processing_tools)` | https://api.github.com/search/repositories?q=topic%3Aweb-crawler%20topic%3Allm&sort=stars&order=desc&per_page=30 | 30 |
| `dpt_t_dataquality (dataset_processing_tools)` | https://api.github.com/search/repositories?q=topic%3Adata-quality%20topic%3Amachine-learning&sort=stars&order=desc&per_page=30 | 30 |
| `dpt_q_dedup (dataset_processing_tools)` | https://api.github.com/search/repositories?q=deduplication%20minhash%20corpus&sort=stars&order=desc&per_page=30 | 6 |
| `dpt_q_curator (dataset_processing_tools)` | https://api.github.com/search/repositories?q=data%20curator%20llm&sort=stars&order=desc&per_page=30 | 22 |
| `dpt_q_pdf (dataset_processing_tools)` | https://api.github.com/search/repositories?q=pdf%20to%20markdown%20llm&sort=stars&order=desc&per_page=30 | 30 |
| `safe_t_guardrails (safeguards)` | https://api.github.com/search/repositories?q=topic%3Aguardrails&sort=stars&order=desc&per_page=30 | 30 |
| `safe_t_llmsecurity (safeguards)` | https://api.github.com/search/repositories?q=topic%3Allm-security&sort=stars&order=desc&per_page=30 | 30 |
| `safe_t_promptinjection (safeguards)` | https://api.github.com/search/repositories?q=topic%3Aprompt-injection&sort=stars&order=desc&per_page=30 | 30 |
| `safe_t_redteam (safeguards)` | https://api.github.com/search/repositories?q=topic%3Ared-teaming&sort=stars&order=desc&per_page=30 | 30 |
| `safe_t_aisafety (safeguards)` | https://api.github.com/search/repositories?q=topic%3Aai-safety&sort=stars&order=desc&per_page=30 | 30 |
| `safe_t_moderation (safeguards)` | https://api.github.com/search/repositories?q=topic%3Acontent-moderation&sort=stars&order=desc&per_page=30 | 30 |
| `safe_q_jailbreak (safeguards)` | https://api.github.com/search/repositories?q=jailbreak%20detection%20llm&sort=stars&order=desc&per_page=30 | 30 |
| `safe_q_guardrail (safeguards)` | https://api.github.com/search/repositories?q=guardrail%20model%20safety%20classifier&sort=stars&order=desc&per_page=30 | 5 |
| `comp_t_mlir (compilers)` | https://api.github.com/search/repositories?q=topic%3Amlir&sort=stars&order=desc&per_page=30 | 30 |
| `comp_t_quant (compilers)` | https://api.github.com/search/repositories?q=topic%3Aquantization&sort=stars&order=desc&per_page=30 | 30 |
| `comp_t_tensorcompiler (compilers)` | https://api.github.com/search/repositories?q=topic%3Acompiler%20topic%3Adeep-learning&sort=stars&order=desc&per_page=30 | 30 |
| `comp_t_cuda (compilers)` | https://api.github.com/search/repositories?q=topic%3Acuda%20topic%3Akernel&sort=stars&order=desc&per_page=30 | 30 |
| `comp_t_onnx (compilers)` | https://api.github.com/search/repositories?q=topic%3Aonnx&sort=stars&order=desc&per_page=30 | 30 |
| `comp_t_triton (compilers)` | https://api.github.com/search/repositories?q=topic%3Atriton&sort=stars&order=desc&per_page=30 | 30 |
| `comp_q_kernel (compilers)` | https://api.github.com/search/repositories?q=attention%20kernel%20gpu%20inference&sort=stars&order=desc&per_page=30 | 30 |
| `comp_q_convert (compilers)` | https://api.github.com/search/repositories?q=model%20converter%20quantize%20deploy&sort=stars&order=desc&per_page=30 | 0 |
| `edge_t_sbc (edge_hardware)` | https://api.github.com/search/repositories?q=topic%3Asingle-board-computer&sort=stars&order=desc&per_page=30 | 30 |
| `edge_t_edgeai (edge_hardware)` | https://api.github.com/search/repositories?q=topic%3Aedge-ai&sort=stars&order=desc&per_page=30 | 30 |
| `edge_t_npu (edge_hardware)` | https://api.github.com/search/repositories?q=topic%3Anpu&sort=stars&order=desc&per_page=30 | 30 |
| `edge_t_riscv_ai (edge_hardware)` | https://api.github.com/search/repositories?q=topic%3Arisc-v%20topic%3Aaccelerator&sort=stars&order=desc&per_page=30 | 10 |
| `edge_t_openhw (edge_hardware)` | https://api.github.com/search/repositories?q=topic%3Aopen-source-hardware%20topic%3Aai&sort=stars&order=desc&per_page=30 | 6 |
| `edge_q_accel (edge_hardware)` | https://api.github.com/search/repositories?q=npu%20accelerator%20board%20inference&sort=stars&order=desc&per_page=30 | 0 |

### Hugging Face model API (10 queries)

| query | request URL | rows returned |
|---|---|---|
| `hf_textgen_downloads` | https://huggingface.co/api/models?sort=downloads&direction=-1&limit=100&filter=text-generation | 100 |
| `hf_textgen_likes` | https://huggingface.co/api/models?sort=likes&direction=-1&limit=100&filter=text-generation | 100 |
| `hf_textgen_trending` | https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=100&filter=text-generation | 100 |
| `hf_all_downloads` | https://huggingface.co/api/models?sort=downloads&direction=-1&limit=100 | 100 |
| `hf_all_trending` | https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=100 | 100 |
| `hf_guard_search` | https://huggingface.co/api/models?search=guard&sort=downloads&direction=-1&limit=100 | 100 |
| `hf_safety_search` | https://huggingface.co/api/models?search=safety&sort=downloads&direction=-1&limit=100 | 100 |
| `hf_moderation_search` | https://huggingface.co/api/models?search=moderation&sort=downloads&direction=-1&limit=100 | 100 |
| `hf_base_search` | https://huggingface.co/api/models?search=base&sort=downloads&direction=-1&limit=100&filter=text-generation | 100 |
| `hf_instruct_search` | https://huggingface.co/api/models?search=instruct&sort=downloads&direction=-1&limit=100&filter=text-generation | 100 |

### Vendor product pages (edge_hardware)

35 pages fetched directly with `curl -sL`, each checked for HTTP 200 and the product's own
`<title>`. All 35 are in the parked table below: a vendor page is a `homepage`, and this batch
emits no row whose only artifact is a URL.

## Where every field on an emitted row comes from

No field on a row in this batch rests on an editorial reading. Each one is either verbatim from
the API response of the query that returned the signal, or produced by a mapping declared before
the emission pass and published here. A candidate whose category or acceptance would have needed
an editorial call is parked with that reason instead; judgment in this sweep can remove a
candidate, never emit one.

| field | how it is produced |
|---|---|
| `github` / `huggingface_model` | verbatim from the API response (`full_name`, `id`) |
| `homepage` | verbatim from the repository's declared `homepage`, where the API returns a non-empty one |
| `type` | from the source kind: a GitHub repository signal is `software`, a Hugging Face model signal is `model` |
| `category` (GitHub signal) | the category declared for the query that returned the signal — the query→category table below |
| `category` (Hugging Face signal) | the declared-metadata rule below (M1/M2/M3) |
| `slug` | `slugify(declared name)`; where that collides with a slug already in the corpus, `slugify(owner)-slugify(name)`; where the declared name is a checkpoint or release id, the product line it belongs to (`identity.md` release folding) — marked as a transcription per row |
| `display_name` | the declared repository or model name, verbatim or title-cased; marked as a transcription per row where it differs |
| `org` | the declared handle in `sources/org_handles.yaml` where the owner login is declared there; otherwise the existing organization record the owner login belongs to, or `slugify(owner login)` for an owner with no record — marked per row |

**Query → category (GitHub).** Declared before the sweep, one category per query; the query name
carries its category in the *Sources swept* tables above. `dpt_*` → `dataset_processing_tools`,
`safe_*` → `safeguards`, `comp_*` → `compilers`, `edge_*` → `edge_hardware`. No emitted row takes
a category other than the one declared for the query that surfaced it.

**Declared-metadata rule (Hugging Face).** The seven ranked and general queries carry no
category, so for a model the category comes from the model's own declared metadata:

| rule | condition, from the API response | category |
|---|---|---|
| **M1** | declared `tags` contain `conversational` | `finetuned_chat` |
| **M2** | no `conversational` tag, and a declared language-model `pipeline_tag` (`fill-mask`, `text-generation`, `text2text-generation`, `translation`, `summarization`) | `base_pretrained` |
| **M3** | returned by a category-scoped query (`hf_guard_search`, `hf_safety_search`, `hf_moderation_search`) and not caught by M1 or M2 | `safeguards` |
| — | none of the above (no declared `pipeline_tag`, or a task or modality outside the rule) | parked, no derivable category |

The two model categories in the taxonomy are language-model categories, which is why M2 lists the
masked- and causal-LM tasks and nothing else. The fourth branch is what parks the populations the
taxonomy has no category for — embedding and reranking (`feature-extraction`,
`sentence-similarity`), speech and audio, vision and vision-language, generative image and video,
and time-series forecasting — the same populations escalated below for a `category-proposal`
issue. The rule does not stretch a language-model category to hold them.

The rule is applied to every Hugging Face signal in the batch, not case by case. It is what moved
`LiquidAI/LFM2.5-2.6B` into `finetuned_chat` (it declares `conversational`) and what parked
`google/electra-base-discriminator` (it declares no `pipeline_tag` at all),
`baidu/Unlimited-OCR` (`image-text-to-text`) and `Falconsai/nsfw_image_detection`
(`image-classification`) — three rows an earlier revision emitted on a reading of what the model is.

## Retrieval cutoffs, predeclared and disclosed

- **GitHub repository search:** sort by stars descending, top 30 per query, floor 1,000 all-time
  stars and a last push no older than 2025-09-07 (12 months).
- **Hugging Face model API:** top 100 per query. Floor 1,000,000 trailing-30-day downloads on the
  seven ranked/general queries; 5,000 on the three targeted guard, safety and moderation searches,
  because those exist to reach a small-model tail.
- **Vendor pages:** the SBC and merchant edge-NPU vendors already on the `edge_hardware` roster
  plus the adjacent field. 35 pages, no ranking involved.

A cutoff bounds *how much was retrieved*. It never rejects a product the sweep surfaced: 8 sub-floor
candidates were recognized and accepted anyway (`data-prep-kit`, `semhash`, `deepfabric`, `magpie`, `datadreamer`, `bonito`, `gpt-j`, `exaone`),
each flagged in its row note. **Coverage limitation:** every signal below a floor is listed in
*Parked — below a disclosed retrieval cutoff* with the floor that excluded it, but none was
triaged individually, so the sweep says nothing about them either way; the fix is a deliberately
lower floor next week, not a judgment here.

## No rule was invented mid-sweep

Four candidates across two signals were parked on a number rather than a threshold, with the number
stated: `Zaneham/Booth` (1,737 stars on a single-owner repository created 2026-02-16 claiming a full
CUDA, Triton and HIP compiler) and the three `farbodtavakkoli/OTel-*-LLM-*` models (6.9M
trailing-30-day downloads on a 31B model under an individual account with no resolvable lineage).
Both are parked for a person to look at, not rejected, and neither park was applied as a rule to
anything else — no star floor, download floor or growth-rate test adjudicated any other candidate.

The declared-metadata rule above is not such a threshold either: it maps declared metadata to a
category and, where it maps to nothing, parks the candidate. It never adjudicates whether a
discovered product is real, and it never admits a candidate the sweep would otherwise have parked.

Rate limits: GitHub search was consumed at 8.5 requests a minute against an unauthenticated ceiling
of 10, with retry-and-backoff on 403/429/5xx. No fetch was recorded as an absence. Five vendor
product pages 404'd on the paths tried and are parked as incomplete fetches, not as absences.

## Accepted — 52 rows

Every row carries at least one identifier that is not a URL. `homepage`, where present, is a
second artifact on a row that already has one.

### `dataset_processing_tools` — 13

| slug | display_name | type | org | artifacts | source URL (fetched 2026-09-07) | note |
|---|---|---|---|---|---|---|
| `bespoke-curator` | Bespoke Curator | software | `bespoke-labs` | `github: bespokelabsai/curator` | https://github.com/bespokelabsai/curator |  |
| `data-prep-kit` | Data Prep Kit | software | `ibm` | `github: data-prep-kit/data-prep-kit` | https://github.com/data-prep-kit/data-prep-kit | below the disclosed star floor (958); accepted because the cutoff bounds retrieval, it never rejects a discovered product |
| `semhash` | SemHash | software | `minish-lab` | `github: MinishLab/semhash` | https://github.com/MinishLab/semhash | below the disclosed star floor (963); accepted for the same reason |
| `deepfabric` | DeepFabric | software | `nolabs-ai` | `github: nolabs-ai/deepfabric` | https://github.com/nolabs-ai/deepfabric | below the disclosed star floor (885); accepted for the same reason |
| `magpie` | Magpie | software | `magpie-align` | `github: magpie-align/magpie` | https://github.com/magpie-align/magpie | below the disclosed star floor (881) and last push 2025-03-17; accepted as the reference pipeline behind a widely used synthesis method, flagged as low-activity |
| `datadreamer` | DataDreamer | software | `datadreamer-dev` | `github: datadreamer-dev/DataDreamer` | https://github.com/datadreamer-dev/DataDreamer | last push 2025-02-02, outside the disclosed 12-month push window; accepted anyway because the cutoff bounds retrieval only |
| `graphgen` | GraphGen | software | `internscience` | `github: InternScience/GraphGen` | https://github.com/InternScience/GraphGen |  |
| `synthetic-data-kit` | Synthetic Data Kit | software | `meta` | `github: meta-llama/synthetic-data-kit` | https://github.com/meta-llama/synthetic-data-kit |  |
| `aisheets` | AI Sheets | software | `hugging-face` | `github: huggingface/aisheets` | https://github.com/huggingface/aisheets |  |
| `bonito` | Bonito | software | `bats-research` | `github: BatsResearch/bonito` | https://github.com/BatsResearch/bonito | below the disclosed star floor (829); accepted for the same reason |
| `text-extract-api` | Text Extract API | software | `catchthetornado` | `github: CatchTheTornado/text-extract-api` | https://github.com/CatchTheTornado/text-extract-api |  |
| `markpdfdown` | MarkPDFDown | software | `markpdfdown` | `github: MarkPDFdown/markpdfdown` | https://github.com/MarkPDFdown/markpdfdown |  |
| `webclaw` | WebClaw | software | `0xmassi` | `github: 0xMassi/webclaw`; `homepage: https://webclaw.io` | https://github.com/0xMassi/webclaw |  |

Field derivation:

| slug | category from | slug from | display_name from | org from | other declared ids folded in |
|---|---|---|---|---|---|
| `bespoke-curator` | query `dpt_t_synthetic`, declared category `dataset_processing_tools` | transcription (declared name `curator`) | transcription of the declared name `curator` | transcription of the declared owner login `bespokelabsai`, no organization record yet (`bespoke-labs` is new) | — |
| `data-prep-kit` | query `dpt_t_dedup`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, title-cased | transcription of the declared owner login `data-prep-kit`, matched to the existing organization record `ibm` | — |
| `semhash` | query `dpt_t_dedup`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, title-cased | transcription of the declared owner login `MinishLab`, no organization record yet (`minish-lab` is new) | — |
| `deepfabric` | query `dpt_t_synthetic`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, title-cased | declared handle `github:nolabs-ai` -> `nolabs-ai` in sources/org_handles.yaml | — |
| `magpie` | query `dpt_synth`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `datadreamer` | query `dpt_t_synthetic`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) | — |
| `graphgen` | query `dpt_synth`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) | — |
| `synthetic-data-kit` | query `dpt_synth`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, title-cased | transcription of the declared owner login `meta-llama`, matched to the existing organization record `meta` | — |
| `aisheets` | query `dpt_t_synthetic`, declared category `dataset_processing_tools` | slugify(declared name) | transcription of the declared name `aisheets` | declared handle `github:huggingface` -> `hugging-face` in sources/org_handles.yaml | — |
| `bonito` | query `dpt_t_synthetic`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, title-cased | transcription of the declared owner login `BatsResearch`, no organization record yet (`bats-research` is new) | — |
| `text-extract-api` | query `dpt_q_pdf`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `markpdfdown` | query `dpt_q_pdf`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `webclaw` | query `dpt_t_webscraping`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |

### `safeguards` — 17

| slug | display_name | type | org | artifacts | source URL (fetched 2026-09-07) | note |
|---|---|---|---|---|---|---|
| `skillspector` | SkillSpector | software | `nvidia` | `github: NVIDIA/SkillSpector` | https://github.com/NVIDIA/SkillSpector |  |
| `superagent` | Superagent | software | `superagent-ai` | `github: superagent-ai/superagent`; `homepage: https://superagent.sh` | https://github.com/superagent-ai/superagent |  |
| `ai-infra-guard` | AI-Infra-Guard | software | `tencent` | `github: Tencent/AI-Infra-Guard` | https://github.com/Tencent/AI-Infra-Guard |  |
| `agent-governance-toolkit` | Agent Governance Toolkit | software | `microsoft` | `github: microsoft/agent-governance-toolkit` | https://github.com/microsoft/agent-governance-toolkit |  |
| `agentic-security` | Agentic Security | software | `msoedov` | `github: msoedov/agentic_security` | https://github.com/msoedov/agentic_security |  |
| `fuzzyai` | FuzzyAI | software | `cyberark` | `github: cyberark/FuzzyAI` | https://github.com/cyberark/FuzzyAI |  |
| `promptmap` | promptmap | software | `utkusen` | `github: utkusen/promptmap` | https://github.com/utkusen/promptmap |  |
| `agentic-radar` | Agentic Radar | software | `splx-ai` | `github: splx-ai/agentic-radar`; `homepage: https://splx.ai` | https://github.com/splx-ai/agentic-radar |  |
| `valqore` | Valqore | software | `valqore` | `github: valqore/valqore`; `homepage: https://www.valqore.io` | https://github.com/valqore/valqore |  |
| `cc-safety-net` | cc-safety-net | software | `kenryu42` | `github: kenryu42/cc-safety-net`; `homepage: https://ccsafetynet.com` | https://github.com/kenryu42/cc-safety-net |  |
| `stable-diffusion-safety-checker` | Stable Diffusion Safety Checker | model | `compvis` | `huggingface_model: CompVis/stable-diffusion-safety-checker` | https://huggingface.co/CompVis/stable-diffusion-safety-checker |  |
| `ncii-guard` | NCII Guard | model | `hugging-face` | `huggingface_model: hfmlsoc/ncii-guard-v02` | https://huggingface.co/hfmlsoc/ncii-guard-v02 |  |
| `modernguard` | ModernGuard | model | `guardion` | `huggingface_model: guardion/ModernGuard-1` | https://huggingface.co/guardion/ModernGuard-1 | inside the targeted guard-search floor (5,000 downloads), below the ranked-query floor; the targeted search is why it was seen |
| `koalaai-text-moderation` | KoalaAI Text Moderation | model | `koala-ai` | `huggingface_model: KoalaAI/Text-Moderation` | https://huggingface.co/KoalaAI/Text-Moderation |  |
| `gliner-guard-omni` | GLiNER Guard Omni | model | `hivetrace` | `huggingface_model: hivetrace/gliner-guard-omni` | https://huggingface.co/hivetrace/gliner-guard-omni |  |
| `polite-guard` | Polite Guard | model | `intel` | `huggingface_model: Intel/polite-guard` | https://huggingface.co/Intel/polite-guard |  |
| `gliner2-guardrails-pii` | GLiNER2 Guardrails PII | model | `fastino` | `huggingface_model: fastino/GLiNER2-Guardrails-PII-Multi` | https://huggingface.co/fastino/GLiNER2-Guardrails-PII-Multi |  |

Field derivation:

| slug | category from | slug from | display_name from | org from | other declared ids folded in |
|---|---|---|---|---|---|
| `skillspector` | query `safe_t_promptinjection`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | declared handle `github:NVIDIA` -> `nvidia` in sources/org_handles.yaml | — |
| `superagent` | query `safe_t_guardrails`, declared category `safeguards` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `ai-infra-guard` | query `safe_t_llmsecurity`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | declared handle `github:Tencent` -> `tencent` in sources/org_handles.yaml | — |
| `agent-governance-toolkit` | query `safe_t_aisafety`, declared category `safeguards` | slugify(declared name) | declared name, title-cased | declared handle `github:microsoft` -> `microsoft` in sources/org_handles.yaml | — |
| `agentic-security` | query `safe_t_llmsecurity`, declared category `safeguards` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `fuzzyai` | query `safe_t_llmsecurity`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) | — |
| `promptmap` | query `safe_t_promptinjection`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) | — |
| `agentic-radar` | query `safe_t_llmsecurity`, declared category `safeguards` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `valqore` | query `safe_t_aisafety`, declared category `safeguards` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `cc-safety-net` | query `safe_t_guardrails`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) | — |
| `stable-diffusion-safety-checker` | rule **M3** (category-scoped query `hf_safety_search`, declared pipeline_tag `None`) | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `ncii-guard` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `text-classification`) | transcription (declared name `ncii-guard-v02`) | transcription of the declared name `ncii-guard-v02` | transcription of the declared owner login `hfmlsoc`, matched to the existing organization record `hugging-face` | — |
| `modernguard` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `text-classification`) | transcription (declared name `ModernGuard-1`) | transcription of the declared name `ModernGuard-1` | slugify(declared owner login) | — |
| `koalaai-text-moderation` | rule **M3** (category-scoped query `hf_moderation_search`, declared pipeline_tag `text-classification`) | slugify(owner)-slugify(name), collision fallback | transcription of the declared name `Text-Moderation` | transcription of the declared owner login `KoalaAI`, no organization record yet (`koala-ai` is new) | — |
| `gliner-guard-omni` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `zero-shot-classification`) | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `polite-guard` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `text-classification`) | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `gliner2-guardrails-pii` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `token-classification`) | transcription (declared name `GLiNER2-Guardrails-PII-Multi`) | transcription of the declared name `GLiNER2-Guardrails-PII-Multi` | slugify(declared owner login) | — |

### `compilers` — 7

| slug | display_name | type | org | artifacts | source URL (fetched 2026-09-07) | note |
|---|---|---|---|---|---|---|
| `torch-mlir` | Torch-MLIR | software | `llvm` | `github: llvm/torch-mlir` | https://github.com/llvm/torch-mlir |  |
| `nunchaku` | Nunchaku | software | `nunchux-ai` | `github: nunchux-ai/nunchaku`; `homepage: https://nunchux.ai` | https://github.com/nunchux-ai/nunchaku |  |
| `kernl` | Kernl | software | `els-rd` | `github: ELS-RD/kernl`; `homepage: http://www.kernl.ai` | https://github.com/ELS-RD/kernl |  |
| `flaggems` | FlagGems | software | `flagos-ai` | `github: flagos-ai/FlagGems` | https://github.com/flagos-ai/FlagGems |  |
| `autokernel` | AutoKernel | software | `rightnow-ai` | `github: RightNow-AI/autokernel` | https://github.com/RightNow-AI/autokernel |  |
| `intel-extension-for-pytorch` | Intel Extension for PyTorch | software | `intel` | `github: intel/intel-extension-for-pytorch` | https://github.com/intel/intel-extension-for-pytorch |  |
| `pytorch-xla` | PyTorch/XLA | software | `pytorch-foundation` | `github: pytorch/xla`; `homepage: https://pytorch.org/xla` | https://github.com/pytorch/xla | slug deliberately not `xla`: the head product `xla` is the OpenXLA compiler, this is the PyTorch bridge to it |

Field derivation:

| slug | category from | slug from | display_name from | org from | other declared ids folded in |
|---|---|---|---|---|---|
| `torch-mlir` | query `comp_t_mlir`, declared category `compilers` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `nunchaku` | query `comp_t_quant`, declared category `compilers` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `kernl` | query `comp_t_triton`, declared category `compilers` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `flaggems` | query `comp_t_triton`, declared category `compilers` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) | — |
| `autokernel` | query `comp_t_triton`, declared category `compilers` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `intel-extension-for-pytorch` | query `comp_t_quant`, declared category `compilers` | slugify(declared name) | declared name, title-cased | slugify(declared owner login) | — |
| `pytorch-xla` | query `comp_t_tensorcompiler`, declared category `compilers` | slugify(owner)-slugify(name), collision fallback | transcription of the declared name `xla` | transcription of the declared owner login `pytorch`, matched to the existing organization record `pytorch-foundation` | — |

### `base_pretrained` — 12

| slug | display_name | type | org | artifacts | source URL (fetched 2026-09-07) | note |
|---|---|---|---|---|---|---|
| `bert` | BERT | model | `google` | `huggingface_model: google-bert/bert-base-uncased` | https://huggingface.co/google-bert/bert-base-uncased |  |
| `roberta` | RoBERTa | model | `meta` | `huggingface_model: FacebookAI/roberta-base` | https://huggingface.co/FacebookAI/roberta-base |  |
| `xlm-roberta` | XLM-RoBERTa | model | `meta` | `huggingface_model: FacebookAI/xlm-roberta-base` | https://huggingface.co/FacebookAI/xlm-roberta-base |  |
| `t5` | T5 | model | `google` | `huggingface_model: google-t5/t5-small` | https://huggingface.co/google-t5/t5-small |  |
| `deberta` | DeBERTa | model | `microsoft` | `huggingface_model: microsoft/mdeberta-v3-base` | https://huggingface.co/microsoft/mdeberta-v3-base |  |
| `modernbert` | ModernBERT | model | `answer-ai` | `huggingface_model: answerdotai/ModernBERT-base` | https://huggingface.co/answerdotai/ModernBERT-base |  |
| `distilbert` | DistilBERT | model | `hugging-face` | `huggingface_model: distilbert/distilbert-base-uncased` | https://huggingface.co/distilbert/distilbert-base-uncased |  |
| `gpt-2` | GPT-2 | model | `openai` | `huggingface_model: openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 |  |
| `opt` | OPT | model | `meta` | `huggingface_model: facebook/opt-125m` | https://huggingface.co/facebook/opt-125m |  |
| `openelm` | OpenELM | model | `apple` | `huggingface_model: apple/OpenELM-1_1B-Instruct` | https://huggingface.co/apple/OpenELM-1_1B-Instruct |  |
| `powermoe` | PowerMoE | model | `ibm` | `huggingface_model: ibm-research/PowerMoE-3b` | https://huggingface.co/ibm-research/PowerMoE-3b |  |
| `gpt-j` | GPT-J | model | `eleutherai` | `huggingface_model: EleutherAI/gpt-j-6b` | https://huggingface.co/EleutherAI/gpt-j-6b | below the disclosed download floor (261,799); accepted because the cutoff bounds retrieval only |

Field derivation:

| slug | category from | slug from | display_name from | org from | other declared ids folded in |
|---|---|---|---|---|---|
| `bert` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | transcription (declared name `bert-base-uncased`) | transcription of the declared name `bert-base-uncased` | transcription of the declared owner login `google-bert`, matched to the existing organization record `google` | — |
| `roberta` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | transcription (declared name `roberta-base`) | product line folded from the declared checkpoint id | transcription of the declared owner login `FacebookAI`, matched to the existing organization record `meta` | `FacebookAI/roberta-large` |
| `xlm-roberta` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | transcription (declared name `xlm-roberta-base`) | transcription of the declared name `xlm-roberta-base` | transcription of the declared owner login `FacebookAI`, matched to the existing organization record `meta` | — |
| `t5` | rule **M2** (declared pipeline_tag `translation`, no `conversational` tag) | transcription (declared name `t5-small`) | product line folded from the declared checkpoint id | transcription of the declared owner login `google-t5`, matched to the existing organization record `google` | `google-t5/t5-base` |
| `deberta` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | transcription (declared name `mdeberta-v3-base`) | transcription of the declared name `mdeberta-v3-base` | declared handle `huggingface:microsoft` -> `microsoft` in sources/org_handles.yaml | — |
| `modernbert` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | transcription (declared name `ModernBERT-base`) | transcription of the declared name `ModernBERT-base` | transcription of the declared owner login `answerdotai`, no organization record yet (`answer-ai` is new) | — |
| `distilbert` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | transcription (declared name `distilbert-base-uncased`) | transcription of the declared name `distilbert-base-uncased` | transcription of the declared owner login `distilbert`, matched to the existing organization record `hugging-face` | — |
| `gpt-2` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | transcription (declared name `gpt2`) | product line folded from the declared checkpoint id | transcription of the declared owner login `openai-community`, matched to the existing organization record `openai` | `openai-community/gpt2-large` |
| `opt` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | transcription (declared name `opt-125m`) | transcription of the declared name `opt-125m` | transcription of the declared owner login `facebook`, matched to the existing organization record `meta` | — |
| `openelm` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | transcription (declared name `OpenELM-1_1B-Instruct`) | transcription of the declared name `OpenELM-1_1B-Instruct` | slugify(declared owner login) | — |
| `powermoe` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | transcription (declared name `PowerMoE-3b`) | transcription of the declared name `PowerMoE-3b` | transcription of the declared owner login `ibm-research`, matched to the existing organization record `ibm` | — |
| `gpt-j` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | transcription (declared name `gpt-j-6b`) | transcription of the declared name `gpt-j-6b` | slugify(declared owner login) | — |

### `finetuned_chat` — 3

| slug | display_name | type | org | artifacts | source URL (fetched 2026-09-07) | note |
|---|---|---|---|---|---|---|
| `lfm2` | Liquid LFM2 | model | `liquid-ai` | `huggingface_model: LiquidAI/LFM2.5-2.6B` | https://huggingface.co/LiquidAI/LFM2.5-2.6B | base-weights repo chosen over the GGUF repo the ranked query returned; both are the same product |
| `dolphin` | Dolphin | model | `dphn` | `huggingface_model: dphn/dolphin-2.9.1-yi-1.5-34b` | https://huggingface.co/dphn/dolphin-2.9.1-yi-1.5-34b |  |
| `exaone` | EXAONE | model | `lg-ai-research` | `huggingface_model: LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct` | https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct | below the disclosed download floor (373,508); accepted because the cutoff bounds retrieval only |

Field derivation:

| slug | category from | slug from | display_name from | org from | other declared ids folded in |
|---|---|---|---|---|---|
| `lfm2` | rule **M1** (declared tag `conversational`) | transcription (declared name `LFM2.5-2.6B`) | product line folded from the declared checkpoint id | transcription of the declared owner login `LiquidAI`, no organization record yet (`liquid-ai` is new) | `LiquidAI/LFM2.5-2.6B-GGUF` |
| `dolphin` | rule **M1** (declared tag `conversational`) | transcription (declared name `dolphin-2.9.1-yi-1.5-34b`) | transcription of the declared name `dolphin-2.9.1-yi-1.5-34b` | slugify(declared owner login) | — |
| `exaone` | rule **M1** (declared tag `conversational`) | transcription (declared name `EXAONE-3.5-7.8B-Instruct`) | transcription of the declared name `EXAONE-3.5-7.8B-Instruct` | transcription of the declared owner login `LGAI-EXAONE`, no organization record yet (`lg-ai-research` is new) | — |

## `edge_hardware`: swept, nothing emitted

35 vendor product pages were fetched and 15 resolved to a single product with a live page and its
own title. None of the 15 has an addressable identifier that is not a URL: no vendor publishes a
product-level repository, package, Hub entry or paper id for a board or an NPU. `homepage` alone
satisfies `docs/schemas/registry.schema.json`, but this batch requires a non-URL identifier on
every emitted row, so all 15 are parked with their page, fetch date and that reason, and
`sources/registry/edge_hardware.yaml` is not created. Nothing was invented to fill the field.

The parked-with-a-reason table below is where they are recorded, so a later sweep can emit them
the week a vendor publishes an identifier — an SDK repository under the vendor's own account, a
package, or a datasheet with a DOI — rather than rediscovering the board from scratch. The
underlying question for a person: whether the map wants a homepage-only hardware tier at all, or
whether `edge_hardware` should stay at the 20 head products it has until one exists.

## Mirrors and acknowledged derivatives, counted as duplicates

Each of these was surveyed with a reason that already acknowledged it folds onto another signal or
an existing head product. They are counted on the duplicate side of the reconciliation, not as
unique candidates.

| signal | source URL | fetched | folds onto |
|---|---|---|---|
| `autogluon/chronos-2` | https://huggingface.co/autogluon/chronos-2 | 2026-09-07 | mirror of the signal amazon/chronos-2 under a second owner (self-dedup) |
| `autogluon/chronos-bolt-small` | https://huggingface.co/autogluon/chronos-bolt-small | 2026-09-07 | mirror of the signal amazon/chronos-bolt-small under a second owner (self-dedup) |
| `argmaxinc/whisperkit-coreml` | https://huggingface.co/argmaxinc/whisperkit-coreml | 2026-09-07 | Core ML conversion of the signal openai/whisper-large-v3, not a distinct model (self-dedup) |
| `huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF` | https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF | 2026-09-07 | abliterated GGUF redistribution of the signal Qwen/Qwen3.8-27B, which folds onto head product qwen |
| `GuardrailsAI/prompt-saturation-attack-detector` | https://huggingface.co/GuardrailsAI/prompt-saturation-attack-detector | 2026-09-07 | component model published by the org behind head product guardrails-ai; SKU of that product |
| `nod-ai/AMD-SHARK-Studio` | https://github.com/nod-ai/AMD-SHARK-Studio | 2026-09-07 | web UI over SHARK+IREE; SKU of head product iree |
| `nunchux-ai/ComfyUI-nunchaku` | https://github.com/nunchux-ai/ComfyUI-nunchaku | 2026-09-07 | ComfyUI plugin surface of nunchaku, which this batch emits as its own row (self-dedup) |

Two candidates that read like the same class were deliberately **not** folded, because the
evidence does not settle them: `prism-ml/Bonsai-27B-mlx-1bit` and
`prism-ml/Ternary-Bonsai-27B-mlx-2bit` are quantized redistributions whose upstream trainer could
not be identified from the card, and `distilbert/distilgpt2` may be its own product or a variant
of the `distilbert` row. Both stay parked with the ambiguity stated.

## Parked — individually reasoned (215)

Every row below was surveyed and not accepted. Source URL and fetch date are given for parked
candidates on the same terms as accepted ones, so next week's sweep can re-check the reason
instead of triaging from scratch.

| candidate | source URL | fetched | category swept | reason not accepted |
|---|---|---|---|---|
| `0xmaximus/Galaxy-Bugbounty-Checklist` | https://github.com/0xmaximus/Galaxy-Bugbounty-Checklist | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `0xShug0/audio.cpp` | https://github.com/0xShug0/audio.cpp | 2026-09-07 | edge_hardware | boundary: model runtime or serving engine; nearer inference_code |
| `0xsyr0/Awesome-Cybersecurity-Handbooks` | https://github.com/0xsyr0/Awesome-Cybersecurity-Handbooks | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `adithya-s-k/AI-Engineering.academy` | https://github.com/adithya-s-k/AI-Engineering.academy | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `AI-Efficiency/Awesome-Model-Quantization` | https://github.com/AI-Efficiency/Awesome-Model-Quantization | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `akto-api-security/akto` | https://github.com/akto-api-security/akto | 2026-09-07 | safeguards | boundary: API security-posture platform; the category is filters and constraints on model inputs and outputs |
| `amitshekhariitbhu/ai-engineering-interview-questions` | https://github.com/amitshekhariitbhu/ai-engineering-interview-questions | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `Anil-matcha/awesome-gpt-6-astra` | https://github.com/Anil-matcha/awesome-gpt-6-astra | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `arsenetar/dupeguru` | https://github.com/arsenetar/dupeguru | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `axoviq-ai/synthadoc` | https://github.com/axoviq-ai/synthadoc | 2026-09-07 | dataset_processing_tools | ambiguous category: document-to-wiki knowledge compilation positioned as a RAG alternative, not a training-corpus pipeline |
| `beclab/Olares` | https://github.com/beclab/Olares | 2026-09-07 | edge_hardware | boundary: end-user or domain application, not stack tooling in this category |
| `beelzebub-labs/beelzebub` | https://github.com/beelzebub-labs/beelzebub | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `BishopFox/sliver` | https://github.com/BishopFox/sliver | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `BlackArch/blackarch` | https://github.com/BlackArch/blackarch | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `borgbackup/borg` | https://github.com/borgbackup/borg | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `borgmatic-collective/borgmatic` | https://github.com/borgmatic-collective/borgmatic | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `BoundaryML/baml` | https://github.com/BoundaryML/baml | 2026-09-07 | safeguards | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `cactus-compute/cactus` | https://github.com/cactus-compute/cactus | 2026-09-07 | edge_hardware | boundary: on-device inference engine (software); this category is boards and chips |
| `cleanlab/cleanlab` | https://github.com/cleanlab/cleanlab | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `cupcakearmy/autorestic` | https://github.com/cupcakearmy/autorestic | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `cvs-health/uqlm` | https://github.com/cvs-health/uqlm | 2026-09-07 | safeguards | boundary: uncertainty quantification and hallucination scoring, not detection or filtering of unsafe content |
| `CyberStrikeus/CyberStrike` | https://github.com/CyberStrikeus/CyberStrike | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `Data-Centric-AI-Community/fg-data-profiling` | https://github.com/Data-Centric-AI-Community/fg-data-profiling | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `Data-Centric-AI-Community/fg-data-synthetic` | https://github.com/Data-Centric-AI-Community/fg-data-synthetic | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `data-infra/cube-studio` | https://github.com/data-infra/cube-studio | 2026-09-07 | edge_hardware | boundary: end-user or domain application, not stack tooling in this category |
| `data-privacy-stack/presidio` | https://github.com/data-privacy-stack/presidio | 2026-09-07 | safeguards | acceptance rested on an editorial boundary argument (a general-purpose PII detection and redaction framework read as an AI safeguard because head product llm-guard filters PII). No declared mapping settles it, so the candidate is parked for a person rather than emitted |
| `datawhalechina/torch-rechub` | https://github.com/datawhalechina/torch-rechub | 2026-09-07 | edge_hardware | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `deepsense-ai/ragbits` | https://github.com/deepsense-ai/ragbits | 2026-09-07 | safeguards | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `DLR-RM/BlenderProc` | https://github.com/DLR-RM/BlenderProc | 2026-09-07 | dataset_processing_tools | ambiguous boundary: synthetic-image rendering for vision training. In scope by the letter of 'synthetic-data generation pipelines', but every product on this roster builds text or document corpora; needs a boundary ruling before it is emitted |
| `Docta-ai/docta` | https://github.com/Docta-ai/docta | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `elder-plinius/CL4R1T4S` | https://github.com/elder-plinius/CL4R1T4S | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `elder-plinius/L1B3RT4S` | https://github.com/elder-plinius/L1B3RT4S | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `EnzymeAD/Enzyme` | https://github.com/EnzymeAD/Enzyme | 2026-09-07 | compilers | ambiguous boundary: an automatic-differentiation compiler pass for LLVM and MLIR. Whether AD counts as 'otherwise optimizes tensor programs for target accelerator hardware' is a boundary question this sweep should not settle alone |
| `Exorust/TorchLeet` | https://github.com/Exorust/TorchLeet | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `FailproofAI/failproofai` | https://github.com/FailproofAI/failproofai | 2026-09-07 | safeguards | held: sources/resolution_ledger.yaml carries an `unresolved` product_equivalence ruling on this repository |
| `FareedKhan-dev/kimi-k3-in-c` | https://github.com/FareedKhan-dev/kimi-k3-in-c | 2026-09-07 | compilers | boundary: a single-file C inference re-implementation of a model already on the map; not compilation or optimization software (note: the automated family fold matched it to `kimi`, which is wrong -- it is a distinct artifact, parked on its own merits) |
| `FedML-AI/FedML` | https://github.com/FedML-AI/FedML | 2026-09-07 | edge_hardware | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `future-agi/future-agi` | https://github.com/future-agi/future-agi | 2026-09-07 | safeguards | boundary: evaluation / observability platform; nearer telemetry_observability |
| `GH05TCREW/pentestagent` | https://github.com/GH05TCREW/pentestagent | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `GokuMohandas/Made-With-ML` | https://github.com/GokuMohandas/Made-With-ML | 2026-09-07 | dataset_processing_tools | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `google/magika` | https://github.com/google/magika | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `GreenmaskIO/greenmask` | https://github.com/GreenmaskIO/greenmask | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `hemansnation/AI-Engineer-Headquarters` | https://github.com/hemansnation/AI-Engineer-Headquarters | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `hitsz-ids/synthetic-data-generator` | https://github.com/hitsz-ids/synthetic-data-generator | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `hybridgroup/gocv` | https://github.com/hybridgroup/gocv | 2026-09-07 | compilers | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `ifixai-ai/iFixAi` | https://github.com/ifixai-ai/iFixAi | 2026-09-07 | safeguards | boundary: evaluation / observability platform; nearer telemetry_observability |
| `jphall663/awesome-machine-learning-interpretability` | https://github.com/jphall663/awesome-machine-learning-interpretability | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `k2-fsa/sherpa-onnx` | https://github.com/k2-fsa/sherpa-onnx | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `karanhudia/borg-ui` | https://github.com/karanhudia/borg-ui | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `KeygraphHQ/shannon` | https://github.com/KeygraphHQ/shannon | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `Kiln-AI/Kiln` | https://github.com/Kiln-AI/Kiln | 2026-09-07 | dataset_processing_tools | ambiguous category: spans evaluation, RAG, fine-tuning and synthetic data; one product one category cannot be settled from the repository alone |
| `klsdf/GreenResourcesManager` | https://github.com/klsdf/GreenResourcesManager | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category (query noise: unrelated desktop resource manager) |
| `kopia/kopia` | https://github.com/kopia/kopia | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `kornelski/pngquant` | https://github.com/kornelski/pngquant | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `langchain4j/langchain4j` | https://github.com/langchain4j/langchain4j | 2026-09-07 | compilers | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `lennney/stop-that-shit` | https://github.com/lennney/stop-that-shit | 2026-09-07 | safeguards | boundary: coding-agent workflow hook (scope-creep and checksum lint), not a filter or constraint on unsafe model inputs, outputs or actions |
| `lk-geimfari/mimesis` | https://github.com/lk-geimfari/mimesis | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `llvm/circt` | https://github.com/llvm/circt | 2026-09-07 | compilers | boundary: hardware / EDA circuit compilers, not model compilation for accelerators |
| `Luce-Org/lucebox` | https://github.com/Luce-Org/lucebox | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `lutzroeder/netron` | https://github.com/lutzroeder/netron | 2026-09-07 | compilers | boundary: model visualization only; performs no lowering, conversion or optimization |
| `mandiant/commando-vm` | https://github.com/mandiant/commando-vm | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `maurosoria/dirsearch` | https://github.com/maurosoria/dirsearch | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `maximhq/bifrost` | https://github.com/maximhq/bifrost | 2026-09-07 | safeguards | boundary: LLM gateway or model router; nearer ui_api |
| `mhx/dwarfs` | https://github.com/mhx/dwarfs | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `microsoft/ai-dev-gallery` | https://github.com/microsoft/ai-dev-gallery | 2026-09-07 | edge_hardware | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `microsoft/AI-Red-Teaming-Playground-Labs` | https://github.com/microsoft/AI-Red-Teaming-Playground-Labs | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `microsoft/Biodiversity` | https://github.com/microsoft/Biodiversity | 2026-09-07 | edge_hardware | boundary: end-user or domain application, not stack tooling in this category |
| `microsoft/SynapseML` | https://github.com/microsoft/SynapseML | 2026-09-07 | compilers | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `moj-analytical-services/splink` | https://github.com/moj-analytical-services/splink | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `nats-io/nats-server` | https://github.com/nats-io/nats-server | 2026-09-07 | edge_hardware | boundary: end-user or domain application, not stack tooling in this category |
| `niedev/RTranslator` | https://github.com/niedev/RTranslator | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `onnx/models` | https://github.com/onnx/models | 2026-09-07 | compilers | boundary: model zoo or converted-weights collection, not compilation or optimization software |
| `OpenNMT/CTranslate2` | https://github.com/OpenNMT/CTranslate2 | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `openvenues/libpostal` | https://github.com/openvenues/libpostal | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category |
| `oritera/Cairn` | https://github.com/oritera/Cairn | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `outflanknl/RedELK` | https://github.com/outflanknl/RedELK | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `OWASP/www-project-top-10-for-large-language-model-applications` | https://github.com/OWASP/www-project-top-10-for-large-language-model-applications | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `pgmpy/pgmpy` | https://github.com/pgmpy/pgmpy | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category |
| `PINTO0309/PINTO_model_zoo` | https://github.com/PINTO0309/PINTO_model_zoo | 2026-09-07 | compilers | boundary: model zoo or converted-weights collection, not compilation or optimization software |
| `PKU-Alignment/safe-rlhf` | https://github.com/PKU-Alignment/safe-rlhf | 2026-09-07 | safeguards | boundary: safety alignment training method; nearer finetuning_code than a guardrail |
| `PlakarKorp/plakar` | https://github.com/PlakarKorp/plakar | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `plurai-ai/intellagent` | https://github.com/plurai-ai/intellagent | 2026-09-07 | dataset_processing_tools | boundary: evaluation / observability platform; nearer telemetry_observability |
| `prometheus/alertmanager` | https://github.com/prometheus/alertmanager | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category (query noise: matched on 'alertmanager', unrelated to AI data tooling) |
| `RedSiege/C2concealer` | https://github.com/RedSiege/C2concealer | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `Renumics/spotlight` | https://github.com/Renumics/spotlight | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `restic/restic` | https://github.com/restic/restic | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `RightNow-AI/picolm` | https://github.com/RightNow-AI/picolm | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `ROCm/FastFlowLM` | https://github.com/ROCm/FastFlowLM | 2026-09-07 | edge_hardware | boundary: model runtime or serving engine; nearer inference_code |
| `royshil/obs-backgroundremoval` | https://github.com/royshil/obs-backgroundremoval | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `rustic-rs/rustic` | https://github.com/rustic-rs/rustic | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `ruvnet/RuVector` | https://github.com/ruvnet/RuVector | 2026-09-07 | compilers | boundary: vector index and memory database; nearer storage |
| `RyanCodrai/turbovec` | https://github.com/RyanCodrai/turbovec | 2026-09-07 | compilers | held: sources/resolution_ledger.yaml carries an `unresolved` product_equivalence ruling on this repository; it needs a person, not another sweep |
| `sahib/rmlint` | https://github.com/sahib/rmlint | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `ScrapeGraphAI/Scrapegraph-ai` | https://github.com/ScrapeGraphAI/Scrapegraph-ai | 2026-09-07 | dataset_processing_tools | boundary: agent-facing web scraping; its peer firecrawl is already a head product in another category, so this roster is not where it belongs |
| `sdv-dev/CTGAN` | https://github.com/sdv-dev/CTGAN | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `sdv-dev/SDV` | https://github.com/sdv-dev/SDV | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `snakers4/silero-vad` | https://github.com/snakers4/silero-vad | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `stefan-jansen/machine-learning-for-trading` | https://github.com/stefan-jansen/machine-learning-for-trading | 2026-09-07 | dataset_processing_tools | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `stochasticai/xTuring` | https://github.com/stochasticai/xTuring | 2026-09-07 | compilers | boundary: fine-tuning toolkit; nearer finetuning_code |
| `supertone-inc/supertonic` | https://github.com/supertone-inc/supertonic | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `synthetichealth/synthea` | https://github.com/synthetichealth/synthea | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `SYSTRAN/faster-whisper` | https://github.com/SYSTRAN/faster-whisper | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `theopenco/llmgateway` | https://github.com/theopenco/llmgateway | 2026-09-07 | safeguards | boundary: LLM gateway or model router; nearer ui_api |
| `thomasxm/BOAZ_beta` | https://github.com/thomasxm/BOAZ_beta | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions; the repository also declares itself no longer maintained |
| `Threekiii/Awesome-Redteam` | https://github.com/Threekiii/Awesome-Redteam | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `TingsongYu/PyTorch-Tutorial-2nd` | https://github.com/TingsongYu/PyTorch-Tutorial-2nd | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `tracel-ai/burn` | https://github.com/tracel-ai/burn | 2026-09-07 | compilers | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `uber/ADR` | https://github.com/uber/ADR | 2026-09-07 | safeguards | ambiguous category: its own description leads with observability and threat detection, which straddles safeguards and telemetry_observability; one product one category cannot be settled from the repository alone |
| `ufoym/deepo` | https://github.com/ufoym/deepo | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `UFund-Me/Qbot` | https://github.com/UFund-Me/Qbot | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `ultralytics/yolov3` | https://github.com/ultralytics/yolov3 | 2026-09-07 | compilers | boundary: vision model and training repo, not model-compilation software |
| `ultralytics/yolov5` | https://github.com/ultralytics/yolov5 | 2026-09-07 | compilers | boundary: vision model and training repo, not model-compilation software |
| `unrealcv/unrealcv` | https://github.com/unrealcv/unrealcv | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category |
| `visual-layer/fastdup` | https://github.com/visual-layer/fastdup | 2026-09-07 | dataset_processing_tools | ambiguous boundary: image and video dataset deduplication. In scope by the letter of 'deduplication', but this roster is text and document corpus tooling; needs the same boundary ruling as BlenderProc |
| `vllm-project/semantic-router` | https://github.com/vllm-project/semantic-router | 2026-09-07 | safeguards | boundary: LLM gateway or model router; nearer ui_api |
| `voxel51/fiftyone` | https://github.com/voxel51/fiftyone | 2026-09-07 | dataset_processing_tools | ambiguous boundary: computer-vision dataset curation and visualization; same unresolved text-versus-vision boundary |
| `xlite-dev/lite.ai.toolkit` | https://github.com/xlite-dev/lite.ai.toolkit | 2026-09-07 | compilers | boundary: model zoo or converted-weights collection, not compilation or optimization software |
| `ymcui/Chinese-LLaMA-Alpaca` | https://github.com/ymcui/Chinese-LLaMA-Alpaca | 2026-09-07 | compilers | boundary: derivative model weights plus training scripts, not compilation or optimization software |
| `zama-ai/concrete` | https://github.com/zama-ai/concrete | 2026-09-07 | compilers | boundary: fully-homomorphic-encryption compiler, not model lowering or optimization for accelerator targets |
| `zan8in/afrog` | https://github.com/zan8in/afrog | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `Zaneham/Booth` | https://github.com/Zaneham/Booth | 2026-09-07 | compilers | implausible signal, parked with the number: 1,737 stars on a single-owner repository created 2026-02-16 that claims a complete CUDA, Triton and HIP compiler across multiple GPU and CPU architectures. The scope-versus-provenance mismatch is what bothers me; parked for a person, not rejected |
| `Zeyad-Azima/Offensive-Resources` | https://github.com/Zeyad-Azima/Offensive-Resources | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `ZhangJinHaHaHa/AgentLens` | https://github.com/ZhangJinHaHaHa/AgentLens | 2026-09-07 | safeguards | boundary: end-user or domain application, not stack tooling in this category |
| `zinggAI/zingg` | https://github.com/zinggAI/zingg | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `amazon/chronos-2` | https://huggingface.co/amazon/chronos-2 | 2026-09-07 | — | no category fits: time-series forecasting model |
| `amazon/chronos-bolt-small` | https://huggingface.co/amazon/chronos-bolt-small | 2026-09-07 | — | no category fits: time-series forecasting model |
| `autogluon/chronos-2-small` | https://huggingface.co/autogluon/chronos-2-small | 2026-09-07 | — | no category fits: time-series forecasting model |
| `BAAI/bge-base-en-v1.5` | https://huggingface.co/BAAI/bge-base-en-v1.5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-large-en-v1.5` | https://huggingface.co/BAAI/bge-large-en-v1.5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-m3` | https://huggingface.co/BAAI/bge-m3 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-reranker-v2-m3` | https://huggingface.co/BAAI/bge-reranker-v2-m3 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-small-en-v1.5` | https://huggingface.co/BAAI/bge-small-en-v1.5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-small-zh-v1.5` | https://huggingface.co/BAAI/bge-small-zh-v1.5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `baidu/Unlimited-OCR` | https://huggingface.co/baidu/Unlimited-OCR | 2026-09-07 | — | category rested on an editorial analogy (a document-extraction model read into dataset_processing_tools because head product olmocr has that shape). The signal came from a ranked query with no declared category, and its declared pipeline_tag (image-text-to-text) is the same tag this sweep parks elsewhere as no-category-fits |
| `Bingsu/adetailer` | https://huggingface.co/Bingsu/adetailer | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter |
| `Comfy-Org/Krea-2` | https://huggingface.co/Comfy-Org/Krea-2 | 2026-09-07 | — | no category fits: image, video or music generative model; repackaged for ComfyUI |
| `Comfy-Org/stable-diffusion-v1-5-archive` | https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive | 2026-09-07 | — | no category fits: image, video or music generative model; also a repackaged archive rather than the publisher's own repo |
| `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` | https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged | 2026-09-07 | — | no category fits: image, video or music generative model; repackaged for ComfyUI |
| `Comfy-Org/z_image_turbo` | https://huggingface.co/Comfy-Org/z_image_turbo | 2026-09-07 | — | no category fits: image, video or music generative model; repackaged for ComfyUI |
| `coqui/XTTS-v2` | https://huggingface.co/coqui/XTTS-v2 | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `cross-encoder/ms-marco-MiniLM-L4-v2` | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L4-v2 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `cross-encoder/ms-marco-MiniLM-L6-v2` | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `datasocietyco/bge-base-en-v1.5-course-recommender-v5` | https://huggingface.co/datasocietyco/bge-base-en-v1.5-course-recommender-v5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it; also a third-party fine-tune of BAAI/bge-base-en-v1.5 |
| `dbmdz/bert-large-cased-finetuned-conll03-english` | https://huggingface.co/dbmdz/bert-large-cased-finetuned-conll03-english | 2026-09-07 | — | boundary: domain text classifier (finance sentiment, NER), not a safety filter and not a foundation model |
| `distilbert/distilgpt2` | https://huggingface.co/distilbert/distilgpt2 | 2026-09-07 | — | ambiguous identity: a distilled GPT-2 published alongside DistilBERT. Whether it is its own product or a variant of the accepted `distilbert` row is exactly the ambiguity the workflow says to park rather than guess |
| `facebook/contriever` | https://huggingface.co/facebook/contriever | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `facebook/dinov2-small` | https://huggingface.co/facebook/dinov2-small | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter |
| `facebook/sam3` | https://huggingface.co/facebook/sam3 | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter |
| `Falconsai/nsfw_image_detection` | https://huggingface.co/Falconsai/nsfw_image_detection | 2026-09-07 | — | category rested on an editorial call (an image classifier read as a safety filter). The signal came from a ranked query with no declared category, and its declared pipeline_tag (image-classification) is outside the declared-metadata rule |
| `farbodtavakkoli/OTel-2.0-LLM-31B-IT` | https://huggingface.co/farbodtavakkoli/OTel-2.0-LLM-31B-IT | 2026-09-07 | — | implausible signal, parked with the number: 6.9M 30-day downloads on a 31B model published under an individual account with no organization, no lineage on the card and no line I could resolve to a vendor. Parked for a person, not rejected |
| `farbodtavakkoli/OTel-LLM-27B-IT` | https://huggingface.co/farbodtavakkoli/OTel-LLM-27B-IT | 2026-09-07 | — | implausible signal, parked with the number: 6.9M 30-day downloads on a 31B model published under an individual account with no organization, no lineage on the card and no line I could resolve to a vendor. Parked for a person, not rejected |
| `farbodtavakkoli/OTel-LLM-E4B-IT` | https://huggingface.co/farbodtavakkoli/OTel-LLM-E4B-IT | 2026-09-07 | — | implausible signal, parked with the number: 6.9M 30-day downloads on a 31B model published under an individual account with no organization, no lineage on the card and no line I could resolve to a vendor. Parked for a person, not rejected |
| `google/electra-base-discriminator` | https://huggingface.co/google/electra-base-discriminator | 2026-09-07 | — | no derivable category: the model declares no pipeline_tag at all, and the signal came from a ranked query with no declared category, so nothing but an editorial reading places it |
| `google/vit-base-patch16-224` | https://huggingface.co/google/vit-base-patch16-224 | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter |
| `hexgrad/Kokoro-82M` | https://huggingface.co/hexgrad/Kokoro-82M | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `intfloat/multilingual-e5-base` | https://huggingface.co/intfloat/multilingual-e5-base | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `intfloat/multilingual-e5-large` | https://huggingface.co/intfloat/multilingual-e5-large | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `intfloat/multilingual-e5-small` | https://huggingface.co/intfloat/multilingual-e5-small | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `Jeesup/svd-safety-llama3_1_8b_instruct_up_basis_finetuned_keep_0p60` | https://huggingface.co/Jeesup/svd-safety-llama3_1_8b_instruct_up_basis_finetuned_keep_0p60 | 2026-09-07 | — | not a product: a research checkpoint from an ablation sweep, with no named product line |
| `jonatasgrosman/wav2vec2-large-xlsr-53-japanese` | https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-japanese | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `jonatasgrosman/wav2vec2-large-xlsr-53-polish` | https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-polish | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `jonatasgrosman/wav2vec2-large-xlsr-53-portuguese` | https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-portuguese | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `laion/clap-htsat-fused` | https://huggingface.co/laion/clap-htsat-fused | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `Lightricks/LTX-2.5` | https://huggingface.co/Lightricks/LTX-2.5 | 2026-09-07 | — | no category fits: image, video or music generative model |
| `nomic-ai/nomic-embed-text-v1.5` | https://huggingface.co/nomic-ai/nomic-embed-text-v1.5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `openai/clip-vit-base-patch32` | https://huggingface.co/openai/clip-vit-base-patch32 | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter |
| `openai/clip-vit-large-patch14` | https://huggingface.co/openai/clip-vit-large-patch14 | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter |
| `openai/whisper-large-v3` | https://huggingface.co/openai/whisper-large-v3 | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `openai/whisper-large-v3-turbo` | https://huggingface.co/openai/whisper-large-v3-turbo | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `optimum-intel-internal-testing/tiny-random-stable-diffusion-with-safety-checker` | https://huggingface.co/optimum-intel-internal-testing/tiny-random-stable-diffusion-with-safety-checker | 2026-09-07 | — | not a product: tiny random-weight test fixture published for CI |
| `prism-ml/Bonsai-27B-mlx-1bit` | https://huggingface.co/prism-ml/Bonsai-27B-mlx-1bit | 2026-09-07 | — | third-party derivative: a quantized, abliterated or repackaged redistribution of weights already represented on the map; and the upstream trainer of the Bonsai weights could not be identified from the card, so identity is unsettled |
| `prism-ml/Ternary-Bonsai-27B-mlx-2bit` | https://huggingface.co/prism-ml/Ternary-Bonsai-27B-mlx-2bit | 2026-09-07 | — | third-party derivative: a quantized, abliterated or repackaged redistribution of weights already represented on the map; same unresolved upstream as Bonsai-27B-mlx-1bit |
| `ProsusAI/finbert` | https://huggingface.co/ProsusAI/finbert | 2026-09-07 | — | boundary: domain text classifier (finance sentiment, NER), not a safety filter and not a foundation model |
| `pyannote/segmentation-3.0` | https://huggingface.co/pyannote/segmentation-3.0 | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `pyannote/speaker-diarization-3.1` | https://huggingface.co/pyannote/speaker-diarization-3.1 | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `pyannote/speaker-diarization-community-1` | https://huggingface.co/pyannote/speaker-diarization-community-1 | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `pyannote/wespeaker-voxceleb-resnet34-LM` | https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `sentence-transformers/all-MiniLM-L6-v2` | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `sentence-transformers/all-mpnet-base-v2` | https://huggingface.co/sentence-transformers/all-mpnet-base-v2 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `sshleifer/tiny-gpt2` | https://huggingface.co/sshleifer/tiny-gpt2 | 2026-09-07 | — | not a product: tiny random-weight test fixture published for CI |
| `timm/efficientnet_b3.ra2_in1k` | https://huggingface.co/timm/efficientnet_b3.ra2_in1k | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter |
| `timm/mobilenetv3_small_100.lamb_in1k` | https://huggingface.co/timm/mobilenetv3_small_100.lamb_in1k | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter |
| `trl-internal-testing/tiny-Qwen2ForCausalLM-2.5` | https://huggingface.co/trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 | 2026-09-07 | — | not a product: tiny random-weight test fixture published for CI |
| `trl-internal-testing/tiny-Qwen3ForCausalLM` | https://huggingface.co/trl-internal-testing/tiny-Qwen3ForCausalLM | 2026-09-07 | — | not a product: tiny random-weight test fixture published for CI |
| `vikhyatk/moondream2` | https://huggingface.co/vikhyatk/moondream2 | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter; a small vision-language model that would sit between base_pretrained and a category the taxonomy does not have |
| `brainchip.com/akida-neural-processor-soc/` | https://brainchip.com/akida-neural-processor-soc/ | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `coral.ai/products/dev-board-micro/` | https://coral.ai/products/dev-board-micro/ | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `hailo.ai/products/ai-accelerators/hailo-8l-ai-accelerator/` | https://hailo.ai/products/ai-accelerators/hailo-8l-ai-accelerator/ | 2026-09-07 | edge_hardware | SKU: the lower-cost, DRAM-free variant of head product hailo-8. This is the amazon-nova-pro shape docs/reference/identity.md warns about |
| `kinara.ai/products/` | https://kinara.ai/products/ | 2026-09-07 | edge_hardware | fetch did not complete for a product page (404); Kinara's catalog appears to have moved after the NXP acquisition |
| `milkv.io/duo` | https://milkv.io/duo | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `pine64.com/product-category/ox64/` | https://pine64.com/product-category/ox64/ | 2026-09-07 | edge_hardware | store category page rather than a product page; the Ox64 itself needs a product-level source before a row |
| `radxa.com/products/accessories/penta-sata-hat` | https://radxa.com/products/accessories/penta-sata-hat | 2026-09-07 | edge_hardware | boundary: a SATA storage HAT, not an inference board or chip |
| `radxa.com/products/aicore/ai-core-x` | https://radxa.com/products/aicore/ai-core-x | 2026-09-07 | edge_hardware | fetch did not complete (404); the Radxa AI Core X may exist under another path |
| `radxa.com/products/rock5/5c` | https://radxa.com/products/rock5/5c | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `shop.luxonis.com/products/oak-d` | https://shop.luxonis.com/products/oak-d | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `sima.ai/` | https://sima.ai/ | 2026-09-07 | edge_hardware | vendor root only; no product identity |
| `sima.ai/products/` | https://sima.ai/products/ | 2026-09-07 | edge_hardware | fetch did not complete for a product page (404 on /products/ and /modalix/; only the vendor root resolved). No product identity to write down yet |
| `sipeed.com/licheepi4a` | https://sipeed.com/licheepi4a | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `tenstorrent.com/hardware/blackhole` | https://tenstorrent.com/hardware/blackhole | 2026-09-07 | edge_hardware | no category fits: PCIe accelerator cards for workstations and servers. This category is boards and chips that run inference at the edge, and the taxonomy has no datacenter-accelerator category -- needs a category-proposal issue |
| `www.banana-pi.org/en/banana-pi-sbcs/175.html` | https://www.banana-pi.org/en/banana-pi-sbcs/175.html | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.beagleboard.org/boards/beaglebone-ai-64` | https://www.beagleboard.org/boards/beaglebone-ai-64 | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.blaize.com/products/` | https://www.blaize.com/products/ | 2026-09-07 | edge_hardware | vendor product index resolved but no product-level page did, so there is no single product identity to name on a row |
| `www.deepx.ai/dx-m1/` | https://www.deepx.ai/dx-m1/ | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.espressif.com/en/products/socs/esp32-p4` | https://www.espressif.com/en/products/socs/esp32-p4 | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.friendlyelec.com/index.php?route=product/product&product_id=292` | https://www.friendlyelec.com/index.php?route=product/product&product_id=292 | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.khadas.com/vim4` | https://www.khadas.com/vim4 | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/` | https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/ | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.nxp.com/products/eIQ-Neutron-NPU` | https://www.nxp.com/products/eIQ-Neutron-NPU | 2026-09-07 | edge_hardware | fetch did not complete (404); and eIQ Neutron is a licensable NPU IP core rather than a board or chip a reader can buy, so the boundary is doubtful too |
| `www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Ora` | https://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-AIpro.html | 2026-09-07 | edge_hardware | fetch did not complete (connection failed, then 404 on two further paths); not recorded as a measured absence -- the Orange Pi AIpro is a real board and comes back next sweep |
| `www.renesas.com/en/products/microcontrollers-microprocessors/rz-mpus/r` | https://www.renesas.com/en/products/microcontrollers-microprocessors/rz-mpus/rzv2h-quad-core-vision-ai-mpu-drp-ai3-accelerator-and-high-performance-real-time-processor | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.rock-chips.com/a/en/products/RK35_Series/2024/0426/1711.html` | https://www.rock-chips.com/a/en/products/RK35_Series/2024/0426/1711.html | 2026-09-07 | edge_hardware | fetch did not complete (404 on two candidate paths for the RK3576 product page); not a measured absence |
| `www.seeedstudio.com/reComputer-J4012-p-5586.html` | https://www.seeedstudio.com/reComputer-J4012-p-5586.html | 2026-09-07 | edge_hardware | ambiguous identity: a carrier and enclosure around the NVIDIA Jetson Orin NX module, which is already the head product nvidia-jetson-orin-nx. Whether Seeed's reComputer is its own product or a packaging of that one is not settled by the page |
| `www.sophgo.com/sophon-u/product/introduce/bm1684x.html` | https://www.sophgo.com/sophon-u/product/introduce/bm1684x.html | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |

## Parked — below a disclosed retrieval cutoff (844)

Returned by the queries above but outside the predeclared cutoff, so not triaged individually.
Listed candidate by candidate, with the query that returned it and the floor that excluded it, so
nothing in this batch is represented only by a count. The floor that applies to a candidate is the
floor of the query that returned it; no candidate here was below the floor of one query and inside
the floor of another (checked across all ten Hugging Face queries: zero such signals), so the
label on each row is the only floor it was ever measured against:

| candidate | source URL | fetched | returned by | cutoff that excluded it |
|---|---|---|---|---|
| `007revad/Synology_enable_Deduplication` | https://github.com/007revad/Synology_enable_Deduplication | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `1195343015/nwputhesis` | https://github.com/1195343015/nwputhesis | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `1596941391qq/anything-to-md` | https://github.com/1596941391qq/anything-to-md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `666DZY666/micronet` | https://github.com/666DZY666/micronet | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `7satvik/sft-dataset-curator` | https://github.com/7satvik/sft-dataset-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `99-dpm/dedup-engine` | https://github.com/99-dpm/dedup-engine | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aai-institute/pyDVL` | https://github.com/aai-institute/pyDVL | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Adlik/Adlik` | https://github.com/Adlik/Adlik | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `adorad/adorad` | https://github.com/adorad/adorad | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aekanman/gaussian-blur` | https://github.com/aekanman/gaussian-blur | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agencyenterprise/PromptInject` | https://github.com/agencyenterprise/PromptInject | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Agent-Threat-Rule/agent-threat-rules` | https://github.com/Agent-Threat-Rule/agent-threat-rules | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agentanywhere/shuddhi` | https://github.com/agentanywhere/shuddhi | 2026-09-07 | `dpt_dedup`, `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agentcontrol/agent-control` | https://github.com/agentcontrol/agent-control | 2026-09-07 | `safe_t_guardrails`, `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agkaminski/Pocket265` | https://github.com/agkaminski/Pocket265 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agkaminski/Pocket65` | https://github.com/agkaminski/Pocket65 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Ahmad21Omar/Polyglot_Data_Filtering_and_Processing_Pipeline` | https://github.com/Ahmad21Omar/Polyglot_Data_Filtering_and_Processing_Pipeline | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ahmedkhn0611-hash/Tiny-GPT-on-Vortex-GPGPU-for-AMD-Alveo-U280` | https://github.com/ahmedkhn0611-hash/Tiny-GPT-on-Vortex-GPGPU-for-AMD-Alveo-U280 | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AIAnytime/Synthetic-Data-Generation-using-LLM` | https://github.com/AIAnytime/Synthetic-Data-Generation-using-LLM | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aiming-lab/AutoHarness` | https://github.com/aiming-lab/AutoHarness | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aipotheosis-labs/gate22` | https://github.com/aipotheosis-labs/gate22 | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aisa-group/PostTrainBench` | https://github.com/aisa-group/PostTrainBench | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `akav-labs/agentsentry-gateway` | https://github.com/akav-labs/agentsentry-gateway | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alelaguard/agentguards-plugins` | https://github.com/alelaguard/agentguards-plugins | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alex000kim/nsfw_data_scraper` | https://github.com/alex000kim/nsfw_data_scraper | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ALIA-Engineering/Molten` | https://github.com/ALIA-Engineering/Molten | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alibaba/BladeDISC` | https://github.com/alibaba/BladeDISC | 2026-09-07 | `comp_t_mlir`, `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alibaba/feathub` | https://github.com/alibaba/feathub | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alibaba/TePDist` | https://github.com/alibaba/TePDist | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AlienZhang1996/DH-CoT` | https://github.com/AlienZhang1996/DH-CoT | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Alihan26/data_curation_interface` | https://github.com/Alihan26/data_curation_interface | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alpa-projects/alpa` | https://github.com/alpa-projects/alpa | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Amal-David/docingest` | https://github.com/Amal-David/docingest | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `andresribeiro/nsfwjs-docker` | https://github.com/andresribeiro/nsfwjs-docker | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AndySparks/sourceconvert` | https://github.com/AndySparks/sourceconvert | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `anilsathyan7/Portrait-Segmentation` | https://github.com/anilsathyan7/Portrait-Segmentation | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `anlp-team/LTI_Neural_Navigator` | https://github.com/anlp-team/LTI_Neural_Navigator | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `api-evangelist/bespoke-labs` | https://github.com/api-evangelist/bespoke-labs | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `api-evangelist/rivos` | https://github.com/api-evangelist/rivos | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `api-evangelist/tenstorrent` | https://github.com/api-evangelist/tenstorrent | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `apifyforge/ai-training-data-curator` | https://github.com/apifyforge/ai-training-data-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `arcjet/arcjet-js` | https://github.com/arcjet/arcjet-js | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `arekusandr/last_layer` | https://github.com/arekusandr/last_layer | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `arunava5764/USENIX_MIA` | https://github.com/arunava5764/USENIX_MIA | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Aryia-Behroziuan/neurons` | https://github.com/Aryia-Behroziuan/neurons | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `asamassekou10/ship-safe` | https://github.com/asamassekou10/ship-safe | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Asap7772/fewshot-preference-optimization` | https://github.com/Asap7772/fewshot-preference-optimization | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `astutic/Acharya` | https://github.com/astutic/Acharya | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `atfortes/LLMSymbolicReasoningBench` | https://github.com/atfortes/LLMSymbolicReasoningBench | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AutoGPTQ/AutoGPTQ` | https://github.com/AutoGPTQ/AutoGPTQ | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `awesome-mlops/awesome-ml-monitoring` | https://github.com/awesome-mlops/awesome-ml-monitoring | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AXERA-TECH/ax-samples` | https://github.com/AXERA-TECH/ax-samples | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aymanelrody/FlashMLA` | https://github.com/aymanelrody/FlashMLA | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Ayubjon/inject-radar` | https://github.com/Ayubjon/inject-radar | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `azamkhan5556/Cyber-Security-tool-for-LLM-based-Chatbots` | https://github.com/azamkhan5556/Cyber-Security-tool-for-LLM-based-Chatbots | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Azure/AI-in-a-Box` | https://github.com/Azure/AI-in-a-Box | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Azzedde/clever_searcher` | https://github.com/Azzedde/clever_searcher | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `badursun/terlik.js` | https://github.com/badursun/terlik.js | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bastio-ai/bastio` | https://github.com/bastio-ai/bastio | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bayerf42/Lox68k` | https://github.com/bayerf42/Lox68k | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Baze-Bai/Zillusion` | https://github.com/Baze-Bai/Zillusion | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Bestselling-goliath423/turboquant_cutile` | https://github.com/Bestselling-goliath423/turboquant_cutile | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bl33h/productOfTwoVectors` | https://github.com/bl33h/productOfTwoVectors | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bl33h/pythagoreanTheorem` | https://github.com/bl33h/pythagoreanTheorem | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Blaspsoft/blasp` | https://github.com/Blaspsoft/blasp | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `BobMcDear/attorch` | https://github.com/BobMcDear/attorch | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `brainlife/ezbids` | https://github.com/brainlife/ezbids | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `buicongnguyen/NPU_sw_stack` | https://github.com/buicongnguyen/NPU_sw_stack | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bytedance/byteir` | https://github.com/bytedance/byteir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `caichuanwang/OpenDocs` | https://github.com/caichuanwang/OpenDocs | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CALISKAN-EMRE/NSOSYAL` | https://github.com/CALISKAN-EMRE/NSOSYAL | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `can-lehmann/exprgrad` | https://github.com/can-lehmann/exprgrad | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cargo-limit/cargo-limit` | https://github.com/cargo-limit/cargo-limit | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CCCpan/chinese-sensitive-words-mcp` | https://github.com/CCCpan/chinese-sensitive-words-mcp | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `chaffybird56/riscv-soc` | https://github.com/chaffybird56/riscv-soc | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CHATS-lab/verbalized-sampling` | https://github.com/CHATS-lab/verbalized-sampling | 2026-09-07 | `dpt_synth`, `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `check-ai-labs/CorpusFlowAI` | https://github.com/check-ai-labs/CorpusFlowAI | 2026-09-07 | `dpt_pipeline` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `chrisliu298/awesome-llm-unlearning` | https://github.com/chrisliu298/awesome-llm-unlearning | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cleanlab/cleanlab-studio` | https://github.com/cleanlab/cleanlab-studio | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `coderonion/awesome-cuda-and-hpc` | https://github.com/coderonion/awesome-cuda-and-hpc | 2026-09-07 | `comp_t_mlir`, `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `coderonion/awesome-llm-and-aigc` | https://github.com/coderonion/awesome-llm-and-aigc | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `coderonion/zcuda` | https://github.com/coderonion/zcuda | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `collinear-ai/spider` | https://github.com/collinear-ai/spider | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Colton1skees/Dna` | https://github.com/Colton1skees/Dna | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cordum-io/cordum` | https://github.com/cordum-io/cordum | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cornell-zhang/allo` | https://github.com/cornell-zhang/allo | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cortex1020/EvalLeak` | https://github.com/cortex1020/EvalLeak | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cosmo-wander-ai/cosmo-edge` | https://github.com/cosmo-wander-ai/cosmo-edge | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CoWork-OS/CoWork-OS` | https://github.com/CoWork-OS/CoWork-OS | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `credi-net/CrediText` | https://github.com/credi-net/CrediText | 2026-09-07 | `dpt_crawl` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cuevhv/mamma` | https://github.com/cuevhv/mamma | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cuga-project/cuga-agent` | https://github.com/cuga-project/cuga-agent | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cxcscmu/Craw4LLM` | https://github.com/cxcscmu/Craw4LLM | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `d1pakda5/awesome-llm-security-tool` | https://github.com/d1pakda5/awesome-llm-security-tool | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `d4em0n/exrop` | https://github.com/d4em0n/exrop | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `daochenzha/data-centric-AI` | https://github.com/daochenzha/data-centric-AI | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Darsh-Nandu/guardrails` | https://github.com/Darsh-Nandu/guardrails | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Data-Centric-AI-Community/awesome-data-centric-ai` | https://github.com/Data-Centric-AI-Community/awesome-data-centric-ai | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Data-Centric-AI-Community/awesome-python-for-data-science` | https://github.com/Data-Centric-AI-Community/awesome-python-for-data-science | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `davesohamm/GPU-Benchmark` | https://github.com/davesohamm/GPU-Benchmark | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `david-palma/cuda-programming` | https://github.com/david-palma/cuda-programming | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DazzleML/comfyui-triton-and-sageattention-installer` | https://github.com/DazzleML/comfyui-triton-and-sageattention-installer | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dbaran0/datastream-curator` | https://github.com/dbaran0/datastream-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dcharlot-physicalai-bmi/ferric` | https://github.com/dcharlot-physicalai-bmi/ferric | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `deadbits/vigil-llm` | https://github.com/deadbits/vigil-llm | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `decionis/agent-safe-pipeline` | https://github.com/decionis/agent-safe-pipeline | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dengxianghua888-ops/ecoalign-forge` | https://github.com/dengxianghua888-ops/ecoalign-forge | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DFKHelper/token-goat` | https://github.com/DFKHelper/token-goat | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dhanushkumar-amk/GuardLayer` | https://github.com/dhanushkumar-amk/GuardLayer | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dharun36/webscraping-craw4ai` | https://github.com/dharun36/webscraping-craw4ai | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `diaa0516/data_curator` | https://github.com/diaa0516/data_curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `diego-ninja/sentinel` | https://github.com/diego-ninja/sentinel | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Digital-Dermatology/SelfClean` | https://github.com/Digital-Dermatology/SelfClean | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dipampaul17/AgentGuard` | https://github.com/dipampaul17/AgentGuard | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dmriding/kaio` | https://github.com/dmriding/kaio | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DobermanCore/Doberman-Core` | https://github.com/DobermanCore/Doberman-Core | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dortanes/curator.ai` | https://github.com/dortanes/curator.ai | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dpc/rdedup` | https://github.com/dpc/rdedup | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dronefreak/PromptScreen` | https://github.com/dronefreak/PromptScreen | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DT42/BerryNet` | https://github.com/DT42/BerryNet | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `duoan/mega-data-factory` | https://github.com/duoan/mega-data-factory | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `duriantaco/skylos` | https://github.com/duriantaco/skylos | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dusty-nv/NanoLLM` | https://github.com/dusty-nv/NanoLLM | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dvmazur/mixtral-offloading` | https://github.com/dvmazur/mixtral-offloading | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `EasyJailbreak/EasyJailbreak` | https://github.com/EasyJailbreak/EasyJailbreak | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ed766/ed766` | https://github.com/ed766/ed766 | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ego/awesome-mojo` | https://github.com/ego/awesome-mojo | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ehsanmok/tvm-rust` | https://github.com/ehsanmok/tvm-rust | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ehtishammubarik/websieve` | https://github.com/ehtishammubarik/websieve | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ElGap/ai-curator-opencode` | https://github.com/ElGap/ai-curator-opencode | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `embedeep/Free-TPU` | https://github.com/embedeep/Free-TPU | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `embedeep/FREE-TPU-V3plus-for-FPGA` | https://github.com/embedeep/FREE-TPU-V3plus-for-FPGA | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `emmtrix/emx-onnx-cgen` | https://github.com/emmtrix/emx-onnx-cgen | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `EMventura/TokenTurbine` | https://github.com/EMventura/TokenTurbine | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `encord-team/encord-active` | https://github.com/encord-team/encord-active | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `eugeneyan/applied-ml` | https://github.com/eugeneyan/applied-ml | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ext-sakamoro/ALICE-LLM` | https://github.com/ext-sakamoro/ALICE-LLM | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `faiyazabdullah/JailbreakTracer` | https://github.com/faiyazabdullah/JailbreakTracer | 2026-09-07 | `dpt_synth`, `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `fcakyon/content-moderation-deep-learning` | https://github.com/fcakyon/content-moderation-deep-learning | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `fcorbelli/zpaqfranz` | https://github.com/fcorbelli/zpaqfranz | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `feathr-ai/feathr` | https://github.com/feathr-ai/feathr | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `featureform/featureform` | https://github.com/featureform/featureform | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ferro-labs/ai-gateway` | https://github.com/ferro-labs/ai-gateway | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `FIIT-IAU/IAU-course` | https://github.com/FIIT-IAU/IAU-course | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `flatmax/buildroot.rockchip` | https://github.com/flatmax/buildroot.rockchip | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Floe-Labs/floe-guard` | https://github.com/Floe-Labs/floe-guard | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `fluxions-ai/vui` | https://github.com/fluxions-ai/vui | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `flyrank-bih/flyscrape` | https://github.com/flyrank-bih/flyscrape | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `fmh66/kernel-opt-agent` | https://github.com/fmh66/kernel-opt-agent | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ForestHubAI/boardsmith` | https://github.com/ForestHubAI/boardsmith | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `framerslab/agentos` | https://github.com/framerslab/agentos | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `frankmtetwa/thermophysical-curator` | https://github.com/frankmtetwa/thermophysical-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `FunnySaltyFish/bilibili_comments_crawl` | https://github.com/FunnySaltyFish/bilibili_comments_crawl | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GannaAsaad/FRAUDX-Intelligent-Credit-Card-Fraud-Detection-Using-AI-LLM` | https://github.com/GannaAsaad/FRAUDX-Intelligent-Credit-Card-Fraud-Detection-Using-AI-LLM | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `gavinlyonsrepo/Display_Lib_RPI` | https://github.com/gavinlyonsrepo/Display_Lib_RPI | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `georgebuilds/anneal` | https://github.com/georgebuilds/anneal | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `getagentseal/agentseal` | https://github.com/getagentseal/agentseal | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `getmetamapper/metamapper` | https://github.com/getmetamapper/metamapper | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GiovanniPasq/chunky` | https://github.com/GiovanniPasq/chunky | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GirishVerm/cuda-kernels` | https://github.com/GirishVerm/cuda-kernels | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `glincker/glin-profanity` | https://github.com/glincker/glin-profanity | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `globalbao/awesome-azure-policy` | https://github.com/globalbao/awesome-azure-policy | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GokuMohandas/mlops-course` | https://github.com/GokuMohandas/mlops-course | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `google-ai-edge/litert-samples` | https://github.com/google-ai-edge/litert-samples | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `google/heir` | https://github.com/google/heir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `google/jsir` | https://github.com/google/jsir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `goshs-labs/goshs` | https://github.com/goshs-labs/goshs | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Govcraft/rust-docs-mcp-server` | https://github.com/Govcraft/rust-docs-mcp-server | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `gpu-mode/reference-kernels` | https://github.com/gpu-mode/reference-kernels | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GramosoftAI/GcrawlAI` | https://github.com/GramosoftAI/GcrawlAI | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GrayboxTech/weightslab` | https://github.com/GrayboxTech/weightslab | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GURPREETKAURJETHRA/Synthetic-Data-Generation-using-LLM` | https://github.com/GURPREETKAURJETHRA/Synthetic-Data-Generation-using-LLM | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `H0NEYP0T-466/dataset-generator` | https://github.com/H0NEYP0T-466/dataset-generator | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `h5i-dev/h5i` | https://github.com/h5i-dev/h5i | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hailo-ai/hailo_model_zoo` | https://github.com/hailo-ai/hailo_model_zoo | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Hamster-Prime/Smart_Group_Bot` | https://github.com/Hamster-Prime/Smart_Group_Bot | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hashgraph-online/hol-guard` | https://github.com/hashgraph-online/hol-guard | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `HawkClaws/pdf2markdown4llm` | https://github.com/HawkClaws/pdf2markdown4llm | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Helldez/BigMoeOnEdge` | https://github.com/Helldez/BigMoeOnEdge | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hendrycks/ethics` | https://github.com/hendrycks/ethics | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hidet-org/hidet` | https://github.com/hidet-org/hidet | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hivellm/transmutation` | https://github.com/hivellm/transmutation | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hngondoki/ge_sheng_guardrails_project` | https://github.com/hngondoki/ge_sheng_guardrails_project | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `HowieHwong/DataGen` | https://github.com/HowieHwong/DataGen | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `huawei-noah/Pretrained-Language-Model` | https://github.com/huawei-noah/Pretrained-Language-Model | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Humaam-04-06/CastNeuralAI` | https://github.com/Humaam-04-06/CastNeuralAI | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hurry211/ai-assisted-gpu-optimization` | https://github.com/hurry211/ai-assisted-gpu-optimization | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hurry211/cuda-performance-lab` | https://github.com/hurry211/cuda-performance-lab | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hurry211/gpu-operator-optimization` | https://github.com/hurry211/gpu-operator-optimization | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `husnuOzaltun/nlp-data-preprocessing` | https://github.com/husnuOzaltun/nlp-data-preprocessing | 2026-09-07 | `dpt_quality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hwdsl2/docker-docling` | https://github.com/hwdsl2/docker-docling | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Hyland/DocumentFilters` | https://github.com/Hyland/DocumentFilters | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hyunwoongko/nanoRLHF` | https://github.com/hyunwoongko/nanoRLHF | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `iaintheardofu/rocm-scribe` | https://github.com/iaintheardofu/rocm-scribe | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `iamwonseokchoi/synthetic_data_generation_DPO` | https://github.com/iamwonseokchoi/synthetic_data_generation_DPO | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Idun-Group/idun-agent-platform` | https://github.com/Idun-Group/idun-agent-platform | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ifilot/bytecradle-6502` | https://github.com/ifilot/bytecradle-6502 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `imgly/background-removal-js` | https://github.com/imgly/background-removal-js | 2026-09-07 | `comp_t_onnx` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `industrialtablet/qt-everywhere-src-5.14.2-cross-compile-for-RK3566-RK3568-RK3588` | https://github.com/industrialtablet/qt-everywhere-src-5.14.2-cross-compile-for-RK3566-RK3568-RK3588 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `industrialtablet/RK3576S-RK3576-RK3588-Tablet-Development-Board` | https://github.com/industrialtablet/RK3576S-RK3576-RK3588-Tablet-Development-Board | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `industrialtablet/RK3588-POE-SBC` | https://github.com/industrialtablet/RK3588-POE-SBC | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `InectGit/pdf-to-markdown` | https://github.com/InectGit/pdf-to-markdown | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `IntelLabs/nlp-architect` | https://github.com/IntelLabs/nlp-architect | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `irahardianto/qurio` | https://github.com/irahardianto/qurio | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ise-uiuc/nnsmith` | https://github.com/ise-uiuc/nnsmith | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ishwariwakchaure5/medishield-safety-engine` | https://github.com/ishwariwakchaure5/medishield-safety-engine | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `iw4p/url-to-markdown` | https://github.com/iw4p/url-to-markdown | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `iwangjian/TopDial` | https://github.com/iwangjian/TopDial | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `J-Aamir/Domain-Specific-GPT2-Pretraining-Australian-Legal-Corpus` | https://github.com/J-Aamir/Domain-Specific-GPT2-Pretraining-Australian-Legal-Corpus | 2026-09-07 | `dpt_pipeline` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `j2kun/mlir-tutorial` | https://github.com/j2kun/mlir-tutorial | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `J535D165/data-matching-software` | https://github.com/J535D165/data-matching-software | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `J535D165/recordlinkage` | https://github.com/J535D165/recordlinkage | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module` | https://github.com/JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Jean-Regis-M/AegisLLM` | https://github.com/Jean-Regis-M/AegisLLM | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Intel_4004_Single_Board_Computer` | https://github.com/jim11662418/Intel_4004_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Intel_8008_Single_Board_Computer` | https://github.com/jim11662418/Intel_8008_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Intel_8048_Single_Board_Computer` | https://github.com/jim11662418/Intel_8048_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Intel_8080_Single_Board_Computer` | https://github.com/jim11662418/Intel_8080_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Mostek_MK3850_Single_Board_Computer` | https://github.com/jim11662418/Mostek_MK3850_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Motorola_MC14500B_Single_Board_Computer` | https://github.com/jim11662418/Motorola_MC14500B_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Signetics_2650_Single_Board_Computer` | https://github.com/jim11662418/Signetics_2650_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jina-ai/clip-as-service` | https://github.com/jina-ai/clip-as-service | 2026-09-07 | `comp_t_onnx` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Jing-yilin/E2M` | https://github.com/Jing-yilin/E2M | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jmerelnyc/crawl-rag` | https://github.com/jmerelnyc/crawl-rag | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Joey0122/Mini-GPU-Inference-Engine` | https://github.com/Joey0122/Mini-GPU-Inference-Engine | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JonathanSalwan/Tigress_protection` | https://github.com/JonathanSalwan/Tigress_protection | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jorgemunozl/Synthetic-Data` | https://github.com/jorgemunozl/Synthetic-Data | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Jos-Ven/A-smart-home-in-Forth` | https://github.com/Jos-Ven/A-smart-home-in-Forth | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jpjacobpadilla/SearchAI` | https://github.com/jpjacobpadilla/SearchAI | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `juanmanueldaza/linkedin2md` | https://github.com/juanmanueldaza/linkedin2md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JulietMirambo/Units_of_Measure_Harmonization-intelligence-platform` | https://github.com/JulietMirambo/Units_of_Measure_Harmonization-intelligence-platform | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JuneYaooo/self-media-compliance-review` | https://github.com/JuneYaooo/self-media-compliance-review | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Justin-Ju-0413/riscv_cnn_accelerator` | https://github.com/Justin-Ju-0413/riscv_cnn_accelerator | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Justin0504/Aegis` | https://github.com/Justin0504/Aegis | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `justinbt1/Akin` | https://github.com/justinbt1/Akin | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JustVugg/distillery` | https://github.com/JustVugg/distillery | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kagandikmen/clairvoyant` | https://github.com/kagandikmen/clairvoyant | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KaleabTessera/Image-Convolution-Using-CUDA-C` | https://github.com/KaleabTessera/Image-Convolution-Using-CUDA-C | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KalebSabo/study-notes` | https://github.com/KalebSabo/study-notes | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kamalrss88/FlashMLA` | https://github.com/kamalrss88/FlashMLA | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Kare0638/paged-attention-decode` | https://github.com/Kare0638/paged-attention-decode | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kendryte/nncase` | https://github.com/kendryte/nncase | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kennethleungty/Failed-ML` | https://github.com/kennethleungty/Failed-ML | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KenObata/distributed-curator` | https://github.com/KenObata/distributed-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kevinadhiguna/dqlab-career-track` | https://github.com/kevinadhiguna/dqlab-career-track | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KeyValueSoftwareSystems/agent-opfor` | https://github.com/KeyValueSoftwareSystems/agent-opfor | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Kirtan132003/ada-use` | https://github.com/Kirtan132003/ada-use | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kisugez/moderator` | https://github.com/kisugez/moderator | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `klezVirus/inceptor` | https://github.com/klezVirus/inceptor | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KOKOSde/localmod` | https://github.com/KOKOSde/localmod | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kruturaj-18/Newsy--News-Curator` | https://github.com/kruturaj-18/Newsy--News-Curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KuiChi-x/reverseloom` | https://github.com/KuiChi-x/reverseloom | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KylinMountain/markify` | https://github.com/KylinMountain/markify | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lambdaclass/concrete` | https://github.com/lambdaclass/concrete | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lambdamikel/picoram2090` | https://github.com/lambdamikel/picoram2090 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `larq/compute-engine` | https://github.com/larq/compute-engine | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `LaureBerti/Learn2Clean` | https://github.com/LaureBerti/Learn2Clean | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `leeroopedia/workflow-nvidia-nemo-curator-text-curation-pipeline` | https://github.com/leeroopedia/workflow-nvidia-nemo-curator-text-curation-pipeline | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `LeightonSec/ai-firewall` | https://github.com/LeightonSec/ai-firewall | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `leoneversberg/pdf2md_llm` | https://github.com/leoneversberg/pdf2md_llm | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Lexsi-Labs/CuratorKIT` | https://github.com/Lexsi-Labs/CuratorKIT | 2026-09-07 | `dpt_synth`, `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lh0x00/docsifer` | https://github.com/lh0x00/docsifer | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lingo-db/lingo-db` | https://github.com/lingo-db/lingo-db | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Littleboy1004/CrispMiner` | https://github.com/Littleboy1004/CrispMiner | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `liu00222/Open-Prompt-Injection` | https://github.com/liu00222/Open-Prompt-Injection | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ljubomirj/ChEMBLdb-query` | https://github.com/ljubomirj/ChEMBLdb-query | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lonerzee/redteam-llm-lab` | https://github.com/lonerzee/redteam-llm-lab | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lsds/Tempo` | https://github.com/lsds/Tempo | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lucasmartins-ai/lcc` | https://github.com/lucasmartins-ai/lcc | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lucassa3/PEGASOS-SVM-CLASSIFIER` | https://github.com/lucassa3/PEGASOS-SVM-CLASSIFIER | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `luckyPipewrench/pipelock` | https://github.com/luckyPipewrench/pipelock | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MadrasLe/ETL_DatasetNLP` | https://github.com/MadrasLe/ETL_DatasetNLP | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MadrasLe/MegaGemm` | https://github.com/MadrasLe/MegaGemm | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mantisfury/ArkhamMirror` | https://github.com/mantisfury/ArkhamMirror | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `marmik28/Web-Crawler-Python` | https://github.com/marmik28/Web-Crawler-Python | 2026-09-07 | `dpt_crawl` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mattilyra/LSH` | https://github.com/mattilyra/LSH | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MaxMLang/pytector` | https://github.com/MaxMLang/pytector | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MaxXSoft/Bossa` | https://github.com/MaxXSoft/Bossa | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mbrukman/curator-evals` | https://github.com/mbrukman/curator-evals | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mcsorkun/AqSolDB` | https://github.com/mcsorkun/AqSolDB | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mddunlap924/PII-Detection` | https://github.com/mddunlap924/PII-Detection | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `meet244/Intelligent-PDF` | https://github.com/meet244/Intelligent-PDF | 2026-09-07 | `dpt_docparse` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MegEngine/MegCC` | https://github.com/MegEngine/MegCC | 2026-09-07 | `comp_t_mlir`, `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Megvii-BaseDetection/YOLOX` | https://github.com/Megvii-BaseDetection/YOLOX | 2026-09-07 | `comp_t_onnx` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mengysun/DataParasite` | https://github.com/mengysun/DataParasite | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mensfeld/code-on-incus` | https://github.com/mensfeld/code-on-incus | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `merrymercy/awesome-tensor-compilers` | https://github.com/merrymercy/awesome-tensor-compilers | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `meta-pytorch/tritonparse` | https://github.com/meta-pytorch/tritonparse | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mgeeky/Penetration-Testing-Tools` | https://github.com/mgeeky/Penetration-Testing-Tools | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mhamidjamil/orangepi` | https://github.com/mhamidjamil/orangepi | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `microsoft/Build26-LAB520-get-started-with-models-in-microsoft-foundry-to-build-ai-apps` | https://github.com/microsoft/Build26-LAB520-get-started-with-models-in-microsoft-foundry-to-build-ai-apps | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `microsoft/MMdnn` | https://github.com/microsoft/MMdnn | 2026-09-07 | `comp_t_onnx` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `microsoft/nnscaler` | https://github.com/microsoft/nnscaler | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MigoXLab/awesome-data-quality` | https://github.com/MigoXLab/awesome-data-quality | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mikeroyal/LLVM-Guide` | https://github.com/mikeroyal/LLVM-Guide | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Mingye-Lu/AgenticCrawler` | https://github.com/Mingye-Lu/AgenticCrawler | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MiquelNasarre/macrograd` | https://github.com/MiquelNasarre/macrograd | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mit-han-lab/once-for-all` | https://github.com/mit-han-lab/once-for-all | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mit-han-lab/tiny-training` | https://github.com/mit-han-lab/tiny-training | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MIT-RLX/rlx-models` | https://github.com/MIT-RLX/rlx-models | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mlir-rs/melior` | https://github.com/mlir-rs/melior | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mmsaeed509/bspwm-dots` | https://github.com/mmsaeed509/bspwm-dots | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `modaic-ai/modaic` | https://github.com/modaic-ai/modaic | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ModelEngine-Group/unified-cache-management` | https://github.com/ModelEngine-Group/unified-cache-management | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `moonshine-ai/useful-transformers` | https://github.com/moonshine-ai/useful-transformers | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mostly-ai/mostlyai` | https://github.com/mostly-ai/mostlyai | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mufeedvh/moonwalk` | https://github.com/mufeedvh/moonwalk | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mughalhere/prompt-protection` | https://github.com/mughalhere/prompt-protection | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mukul975/mcp-web-scrape` | https://github.com/mukul975/mcp-web-scrape | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NabilAlouani/INSPIRe_` | https://github.com/NabilAlouani/INSPIRe_ | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nareshns2004/custom-cuda-fused-attention-triton` | https://github.com/nareshns2004/custom-cuda-fused-attention-triton | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `natalimuca/jailbreak-activation-detection` | https://github.com/natalimuca/jailbreak-activation-detection | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `neo-chem/awesome-chemical-data` | https://github.com/neo-chem/awesome-chemical-data | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NervanaSystems/he-transformer` | https://github.com/NervanaSystems/he-transformer | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NervanaSystems/ngraph` | https://github.com/NervanaSystems/ngraph | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `netinvent/npbackup` | https://github.com/netinvent/npbackup | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `neuralmagic/deepsparse` | https://github.com/neuralmagic/deepsparse | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NevermindNilas/TheAnimeScripter` | https://github.com/NevermindNilas/TheAnimeScripter | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nicolas-hbt/pygraft` | https://github.com/nicolas-hbt/pygraft | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nizos/probity` | https://github.com/nizos/probity | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nkito/i960_sbc` | https://github.com/nkito/i960_sbc | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NNgen/nngen` | https://github.com/NNgen/nngen | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NotPunchnox/rkllama` | https://github.com/NotPunchnox/rkllama | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NTNU-HPC-Lab/BAT` | https://github.com/NTNU-HPC-Lab/BAT | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nucleuscloud/neosync` | https://github.com/nucleuscloud/neosync | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NVIDIA-ISAAC-ROS/isaac_ros_object_detection` | https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_object_detection | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NVIDIA/tilus` | https://github.com/NVIDIA/tilus | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OAID/Tengine` | https://github.com/OAID/Tengine | 2026-09-07 | `comp_t_onnx`, `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ojasviii14/rag-crawler_Ojasvi` | https://github.com/ojasviii14/rag-crawler_Ojasvi | 2026-09-07 | `dpt_crawl` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Okerew/larkos` | https://github.com/Okerew/larkos | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `oneclickvirt/oneclickvirt` | https://github.com/oneclickvirt/oneclickvirt | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `onnx/turnkeyml` | https://github.com/onnx/turnkeyml | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `openarsenalspecs/IoT` | https://github.com/openarsenalspecs/IoT | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `opendilab/DI-hpc` | https://github.com/opendilab/DI-hpc | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OpenLMLab/MOSS-RLHF` | https://github.com/OpenLMLab/MOSS-RLHF | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OpenSparX/MasterAgent` | https://github.com/OpenSparX/MasterAgent | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OpenTradeOSS/OpenTrade` | https://github.com/OpenTradeOSS/OpenTrade | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OPUSLab/SANTA` | https://github.com/OPUSLab/SANTA | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Oqura-ai/local-datagen-cli` | https://github.com/Oqura-ai/local-datagen-cli | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ot-triton-lab/flash-sinkhorn` | https://github.com/ot-triton-lab/flash-sinkhorn | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PacificAI/langtest` | https://github.com/PacificAI/langtest | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PaddlePaddle/VisualDL` | https://github.com/PaddlePaddle/VisualDL | 2026-09-07 | `comp_t_onnx` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `paladini/harness-score` | https://github.com/paladini/harness-score | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pangu-Immortal/MagicWX` | https://github.com/Pangu-Immortal/MagicWX | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pantheon-Security/medusa` | https://github.com/Pantheon-Security/medusa | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `paolodalprato/pymupdf4llm-gui` | https://github.com/paolodalprato/pymupdf4llm-gui | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `parasj/checkmate` | https://github.com/parasj/checkmate | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `parasj/contracode` | https://github.com/parasj/contracode | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `parinzee/seed-free-synthetic-instruct` | https://github.com/parinzee/seed-free-synthetic-instruct | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ParsBench/PersianSyntheticData` | https://github.com/ParsBench/PersianSyntheticData | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `passpartout42/ConvertRgbToHsv-Cuda` | https://github.com/passpartout42/ConvertRgbToHsv-Cuda | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `passpartout42/SobelFilter-Cuda` | https://github.com/passpartout42/SobelFilter-Cuda | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `patelvishwa112/fallback-curator` | https://github.com/patelvishwa112/fallback-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `patrickfleith/datafast` | https://github.com/patrickfleith/datafast | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pegasi-ai/reins` | https://github.com/pegasi-ai/reins | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pelochus/ezrknpu` | https://github.com/Pelochus/ezrknpu | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pengfei-Yang01/RLShield` | https://github.com/Pengfei-Yang01/RLShield | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PennLINC/CuBIDS` | https://github.com/PennLINC/CuBIDS | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PennyLaneAI/catalyst` | https://github.com/PennyLaneAI/catalyst | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pg-space/panspace` | https://github.com/pg-space/panspace | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Picovoice/speech-to-text-benchmark` | https://github.com/Picovoice/speech-to-text-benchmark | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pliron-org/pliron` | https://github.com/pliron-org/pliron | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `powerserve-project/PowerServe` | https://github.com/powerserve-project/PowerServe | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pradeepanpp/jailbreak-detection-system` | https://github.com/pradeepanpp/jailbreak-detection-system | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PranabNandy/BeagleBone-Black-Platform-Bring-Up` | https://github.com/PranabNandy/BeagleBone-Black-Platform-Bring-Up | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PrismorSec/prismor` | https://github.com/PrismorSec/prismor | 2026-09-07 | `safe_t_promptinjection`, `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `privacera/paig` | https://github.com/privacera/paig | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `protectai/rebuff` | https://github.com/protectai/rebuff | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Prysai/Prysai-LLM-Playbook` | https://github.com/Prysai/Prysai-LLM-Playbook | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PS-003R32/AegisDominus` | https://github.com/PS-003R32/AegisDominus | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PSAL-POSTECH/ONNXim` | https://github.com/PSAL-POSTECH/ONNXim | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PSAL-POSTECH/PyTorchSim` | https://github.com/PSAL-POSTECH/PyTorchSim | 2026-09-07 | `comp_t_tensorcompiler`, `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pulp-platform/picobello` | https://github.com/pulp-platform/picobello | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pylir/Pylir` | https://github.com/Pylir/Pylir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Qengineering/YoloV5-NPU` | https://github.com/Qengineering/YoloV5-NPU | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Qengineering/YoloV8-NPU` | https://github.com/Qengineering/YoloV8-NPU | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `qijianpeng/awesome-edge-computing` | https://github.com/qijianpeng/awesome-edge-computing | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `RaduPetrila-dev/nano-infer` | https://github.com/RaduPetrila-dev/nano-infer | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `raintree-technology/docpull` | https://github.com/raintree-technology/docpull | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Ramshankar07/CUDA-llama3.1-inference` | https://github.com/Ramshankar07/CUDA-llama3.1-inference | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Ratila1/JGuardrails` | https://github.com/Ratila1/JGuardrails | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Red-Hat-AI-Innovation-Team/sdg_hub` | https://github.com/Red-Hat-AI-Innovation-Team/sdg_hub | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `REevee0/wiringMQ` | https://github.com/REevee0/wiringMQ | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Renumics/awesome-open-data-centric-ai` | https://github.com/Renumics/awesome-open-data-centric-ai | 2026-09-07 | `dpt_t_synthetic`, `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Renumics/sliceguard` | https://github.com/Renumics/sliceguard | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `reverieim/voice` | https://github.com/reverieim/voice | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `RiccardoBiosas/awesome-MLSecOps` | https://github.com/RiccardoBiosas/awesome-MLSecOps | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Rijwan123/Scrapping-Summarization` | https://github.com/Rijwan123/Scrapping-Summarization | 2026-09-07 | `dpt_crawl` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rin-nas/postgresql-patterns-library` | https://github.com/rin-nas/postgresql-patterns-library | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `robert-mcdermott/doc2md` | https://github.com/robert-mcdermott/doc2md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `robertoraggi/cplusplus` | https://github.com/robertoraggi/cplusplus | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rocklambros/any2md` | https://github.com/rocklambros/any2md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ROCm/FlyDSL` | https://github.com/ROCm/FlyDSL | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ROCm/iris` | https://github.com/ROCm/iris | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `RoffyS/MarkEverythingDown` | https://github.com/RoffyS/MarkEverythingDown | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rohitpotluri/smol-lm3-3B-custom-kernels` | https://github.com/rohitpotluri/smol-lm3-3B-custom-kernels | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `RomiconEZ/llamator-mcp-server` | https://github.com/RomiconEZ/llamator-mcp-server | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rotsl/nexusrt` | https://github.com/rotsl/nexusrt | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ryomuk/emu8080on4004` | https://github.com/ryomuk/emu8080on4004 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ryomuk/test4004` | https://github.com/ryomuk/test4004 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sahil139/cuda-fused-attention` | https://github.com/sahil139/cuda-fused-attention | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `salehjg/batch-matmul-cuda` | https://github.com/salehjg/batch-matmul-cuda | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Samarth-23-eng/scope-intelligence` | https://github.com/Samarth-23-eng/scope-intelligence | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SantanderAI/autoguardrails` | https://github.com/SantanderAI/autoguardrails | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SaravanaBalaji020394/Guardrails` | https://github.com/SaravanaBalaji020394/Guardrails | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `schmitech/orbit` | https://github.com/schmitech/orbit | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ScrapeGraphAI/just-scrape` | https://github.com/ScrapeGraphAI/just-scrape | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `scthornton/vulnerable-chat` | https://github.com/scthornton/vulnerable-chat | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `secureagentics/Adrian` | https://github.com/secureagentics/Adrian | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `selau642/QuantizedAttention` | https://github.com/selau642/QuantizedAttention | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `selenarib5962/pm-os` | https://github.com/selenarib5962/pm-os | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `shen-shanshan/cs-self-learning` | https://github.com/shen-shanshan/cs-self-learning | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `shibatch/oomstaller` | https://github.com/shibatch/oomstaller | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ShishirPatil/poet` | https://github.com/ShishirPatil/poet | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `shoryasethia/markdrop` | https://github.com/shoryasethia/markdrop | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `shuttle-hq/synth` | https://github.com/shuttle-hq/synth | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `silvioviscuso/nova34` | https://github.com/silvioviscuso/nova34 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SimonZeng7108/efficientsam3` | https://github.com/SimonZeng7108/efficientsam3 | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sipeed/MaixCDK` | https://github.com/sipeed/MaixCDK | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sipeed/MaixPy-v1` | https://github.com/sipeed/MaixPy-v1 | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SJTU-DMTai/awesome-ml-data-quality-papers` | https://github.com/SJTU-DMTai/awesome-ml-data-quality-papers | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SonySemiconductorSolutions/mct-model-optimization` | https://github.com/SonySemiconductorSolutions/mct-model-optimization | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sophgo/tpu-mlir` | https://github.com/sophgo/tpu-mlir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `soumyasagiri/adversarial-prompt-shield` | https://github.com/soumyasagiri/adversarial-prompt-shield | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sourcenetwork/defradb` | https://github.com/sourcenetwork/defradb | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `souvikmajumder26/Multi-Agent-Medical-Assistant` | https://github.com/souvikmajumder26/Multi-Agent-Medical-Assistant | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `spcl/daceml` | https://github.com/spcl/daceml | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `spcl/pymlir` | https://github.com/spcl/pymlir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SponsioLabs/Sponsio` | https://github.com/SponsioLabs/Sponsio | 2026-09-07 | `safe_t_guardrails`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SQLab/symgdb` | https://github.com/SQLab/symgdb | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sreedevk/deduplicator` | https://github.com/sreedevk/deduplicator | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Sriram-PR/doc-scraper` | https://github.com/Sriram-PR/doc-scraper | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `starfishdata/starfish` | https://github.com/starfishdata/starfish | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `steelcityamir/safe-content-ai` | https://github.com/steelcityamir/safe-content-ai | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sudonam/open-college-courses` | https://github.com/sudonam/open-college-courses | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `supadata-ai/js` | https://github.com/supadata-ai/js | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `surge-ai/toxicity` | https://github.com/surge-ai/toxicity | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `swap5114/demo-afterquery-d96054d1` | https://github.com/swap5114/demo-afterquery-d96054d1 | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `swislar/RACo-Deduplication` | https://github.com/swislar/RACo-Deduplication | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `syda-ai/syda` | https://github.com/syda-ai/syda | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Syslifters/OffSec-Reporting` | https://github.com/Syslifters/OffSec-Reporting | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `t3l3machus/hoaxshell` | https://github.com/t3l3machus/hoaxshell | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tanghui315/lumenfolio` | https://github.com/tanghui315/lumenfolio | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tattle-made/Uli` | https://github.com/tattle-made/Uli | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TejasR11/gpu-transformer-kernels` | https://github.com/TejasR11/gpu-transformer-kernels | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tg12/gpt_jailbreak_status` | https://github.com/tg12/gpt_jailbreak_status | 2026-09-07 | `safe_t_promptinjection`, `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `thomas-villani/all2md` | https://github.com/thomas-villani/all2md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ThomasRochefortB/open-agentinstruct` | https://github.com/ThomasRochefortB/open-agentinstruct | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `thousrm/universal_NPU-CNN_accelerator` | https://github.com/thousrm/universal_NPU-CNN_accelerator | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `thuml/depyf` | https://github.com/thuml/depyf | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TieuLongPhan/SynRBL` | https://github.com/TieuLongPhan/SynRBL | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tigerlab-ai/tiger` | https://github.com/tigerlab-ai/tiger | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tldrsec/prompt-injection-defenses` | https://github.com/tldrsec/prompt-injection-defenses | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Tobiaszn8972/turboquant-gpu` | https://github.com/Tobiaszn8972/turboquant-gpu | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `toby-bridges/api-relay-audit` | https://github.com/toby-bridges/api-relay-audit | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TomNisbet/Simple8085` | https://github.com/TomNisbet/Simple8085 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `trailofbits/multiplier` | https://github.com/trailofbits/multiplier | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `trailofbits/vast` | https://github.com/trailofbits/vast | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TrevTron/indiedroid-nova-llm` | https://github.com/TrevTron/indiedroid-nova-llm | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tristanbaldev/Clawidth` | https://github.com/tristanbaldev/Clawidth | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TritonDataCenter/containerpilot` | https://github.com/TritonDataCenter/containerpilot | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TrustAI-laboratory/Learn-Prompt-Hacking` | https://github.com/TrustAI-laboratory/Learn-Prompt-Hacking | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `trylonai/gateway` | https://github.com/trylonai/gateway | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ttguy0707/CyberClaw` | https://github.com/ttguy0707/CyberClaw | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TyloAI/prompt-guard-lite` | https://github.com/TyloAI/prompt-guard-lite | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `UCSC-REAL/DS2` | https://github.com/UCSC-REAL/DS2 | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `UCYBERS/Awesome-Blackhat-Tools` | https://github.com/UCYBERS/Awesome-Blackhat-Tools | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `UIUC-ChenLab/scalehls` | https://github.com/UIUC-ChenLab/scalehls | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `us/crw` | https://github.com/us/crw | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vakra-dev/reader` | https://github.com/vakra-dev/reader | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `verazuo/jailbreak_llms` | https://github.com/verazuo/jailbreak_llms | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vincenzo-afk/Intelis-Agent` | https://github.com/vincenzo-afk/Intelis-Agent | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vincenzo-afk/SocialGuard-RL` | https://github.com/vincenzo-afk/SocialGuard-RL | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vincenzo-afk/verbix` | https://github.com/vincenzo-afk/verbix | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vinodborole/okf-kit` | https://github.com/vinodborole/okf-kit | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Viralmaniar/BigBountyRecon` | https://github.com/Viralmaniar/BigBountyRecon | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `VisharadR/Mini-Transformer---GPU-optimized` | https://github.com/VisharadR/Mini-Transformer---GPU-optimized | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vme-im/vme-content` | https://github.com/vme-im/vme-content | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `WanzhengZhu/Euphemism` | https://github.com/WanzhengZhu/Euphemism | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `wasiahmad/Awesome-LLM-Synthetic-Data` | https://github.com/wasiahmad/Awesome-LLM-Synthetic-Data | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `waynehacking8/inference-kernel-cookbook` | https://github.com/waynehacking8/inference-kernel-cookbook | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `whylabs/langkit` | https://github.com/whylabs/langkit | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `whythawk/data-as-a-science` | https://github.com/whythawk/data-as-a-science | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `wisupai/e2m` | https://github.com/wisupai/e2m | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `wzn1118/AsteriaAnalyst` | https://github.com/wzn1118/AsteriaAnalyst | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `x-CK-x/Dataset-Curation-Tool` | https://github.com/x-CK-x/Dataset-Curation-Tool | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Xilinx/mlir-aie` | https://github.com/Xilinx/mlir-aie | 2026-09-07 | `comp_t_mlir`, `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Xilinx/XRT` | https://github.com/Xilinx/XRT | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `XshuiAi/media-publish-check` | https://github.com/XshuiAi/media-publish-check | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `xxxbrian/mcp-rquest` | https://github.com/xxxbrian/mcp-rquest | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `xybrid-ai/xybrid` | https://github.com/xybrid-ai/xybrid | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yatin-superintelligence/Adversarial-Agent-Intent-Safety-Analysis-240K` | https://github.com/yatin-superintelligence/Adversarial-Agent-Intent-Safety-Analysis-240K | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yifu-ding/LongContext-SparseQuant-Attn` | https://github.com/yifu-ding/LongContext-SparseQuant-Attn | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yifu-ding/MP-Sparse-Attn` | https://github.com/yifu-ding/MP-Sparse-Attn | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yigitkonur/api-llm-ocr` | https://github.com/yigitkonur/api-llm-ocr | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Yomguithereal/talisman` | https://github.com/Yomguithereal/talisman | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yottatsa/80188` | https://github.com/yottatsa/80188 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `youyve/nputop` | https://github.com/youyve/nputop | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yunwei37/prompt-hacker-collections` | https://github.com/yunwei37/prompt-hacker-collections | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zengxiao-he/tessera` | https://github.com/zengxiao-he/tessera | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zengzifan1/multi-agent-moderation` | https://github.com/zengzifan1/multi-agent-moderation | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zentinelproxy/zentinel-agent-ai-gateway` | https://github.com/zentinelproxy/zentinel-agent-ai-gateway | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zeokin/Cuda-Compute-OSS` | https://github.com/zeokin/Cuda-Compute-OSS | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Zyrexnn/Cybermes` | https://github.com/Zyrexnn/Cybermes | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `a1273352/pixtral-12b-construction-safety` | https://huggingface.co/a1273352/pixtral-12b-construction-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `abhiai/ModerationGPT` | https://huggingface.co/abhiai/ModerationGPT | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `AbteeXAILab/lumynax-guard-text-moderation` | https://huggingface.co/AbteeXAILab/lumynax-guard-text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `adaptive-classifier/content-moderation` | https://huggingface.co/adaptive-classifier/content-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `adept/persimmon-8b-base` | https://huggingface.co/adept/persimmon-8b-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `ai-forever/rugpt3medium_based_on_gpt2` | https://huggingface.co/ai-forever/rugpt3medium_based_on_gpt2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `ai-forever/rugpt3small_based_on_gpt2` | https://huggingface.co/ai-forever/rugpt3small_based_on_gpt2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `ai-safety-institute/somo-olmo-7b-nohints-s1-chkpt-1520` | https://huggingface.co/ai-safety-institute/somo-olmo-7b-nohints-s1-chkpt-1520 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `ai-safety-institute/somo-olmo-7b-sdf-sft` | https://huggingface.co/ai-safety-institute/somo-olmo-7b-sdf-sft | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `ai21labs/Jamba-v0.1` | https://huggingface.co/ai21labs/Jamba-v0.1 | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `aishmurtaza/neonatal_guardian_slm` | https://huggingface.co/aishmurtaza/neonatal_guardian_slm | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Akahsizrr/Cyber-Prime-1-2.6B` | https://huggingface.co/Akahsizrr/Cyber-Prime-1-2.6B | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Alibaba-NLP/gte-Qwen2-1.5B-instruct` | https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `allenai/BAR-2x7B-Safety` | https://huggingface.co/allenai/BAR-2x7B-Safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `andriadze/ai-chat-underage-moderation2` | https://huggingface.co/andriadze/ai-chat-underage-moderation2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `andriadze/bert-chat-moderation-X` | https://huggingface.co/andriadze/bert-chat-moderation-X | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `andriadze/bert-chat-moderation-X-V2` | https://huggingface.co/andriadze/bert-chat-moderation-X-V2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `apodex/Apodex-1.1-mini` | https://huggingface.co/apodex/Apodex-1.1-mini | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `arcee-ai/AFM-4.5B-Base` | https://huggingface.co/arcee-ai/AFM-4.5B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `ashwini10521/prompt-safety-classification` | https://huggingface.co/ashwini10521/prompt-safety-classification | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `astroware/Halo0.8B-guard-v1` | https://huggingface.co/astroware/Halo0.8B-guard-v1 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `aubmindlab/aragpt2-base` | https://huggingface.co/aubmindlab/aragpt2-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `AutoCyberAI/crp-safety-deberta-v1` | https://huggingface.co/AutoCyberAI/crp-safety-deberta-v1 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `ayushgupta7777/safetyvision-yolov8` | https://huggingface.co/ayushgupta7777/safetyvision-yolov8 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `BabyLM-community/babylm-multimodal-baseline-flamingo` | https://huggingface.co/BabyLM-community/babylm-multimodal-baseline-flamingo | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `bartowski/Meta-Llama-3.1-8B-Instruct-GGUF` | https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Bazzar/bazzar_moderation` | https://huggingface.co/Bazzar/bazzar_moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Bhavdeepsingh/moderashield-text-moderation` | https://huggingface.co/Bhavdeepsingh/moderashield-text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `bigcode/starcoder` | https://huggingface.co/bigcode/starcoder | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `bigscience/bloom` | https://huggingface.co/bigscience/bloom | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `black-forest-labs/FLUX.1-dev` | https://huggingface.co/black-forest-labs/FLUX.1-dev | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `black-forest-labs/FLUX.2-klein-base-9b-fp8` | https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9b-fp8 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `bloomer010/Ling-3.0-tiny-GGUF` | https://huggingface.co/bloomer010/Ling-3.0-tiny-GGUF | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `bosonai/higgs-tts-3-4b` | https://huggingface.co/bosonai/higgs-tts-3-4b | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `BrCamp/bee-350m-pt-base` | https://huggingface.co/BrCamp/bee-350m-pt-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `BreezeBlue/Breeze-TTS-2` | https://huggingface.co/BreezeBlue/Breeze-TTS-2 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `ByteDance/Ouro-1.4B` | https://huggingface.co/ByteDance/Ouro-1.4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Cactus-Compute/needle2` | https://huggingface.co/Cactus-Compute/needle2 | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `callhub/koala-ai-text-moderation` | https://huggingface.co/callhub/koala-ai-text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Chain-GPT/Solidity-LLM` | https://huggingface.co/Chain-GPT/Solidity-LLM | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `CogEvol/CogEvol-4B` | https://huggingface.co/CogEvol/CogEvol-4B | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `CohereLabs/c4ai-command-r-plus` | https://huggingface.co/CohereLabs/c4ai-command-r-plus | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `CohereLabs/tiny-aya-base` | https://huggingface.co/CohereLabs/tiny-aya-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `DANNY621/H3-World` | https://huggingface.co/DANNY621/H3-World | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Data-Lab/moderation_binary_classification` | https://huggingface.co/Data-Lab/moderation_binary_classification | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Data-Lab/moderation_layer` | https://huggingface.co/Data-Lab/moderation_layer | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Data-Lab/moderation_layer_v2` | https://huggingface.co/Data-Lab/moderation_layer_v2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `dcarpintero/pangolin-guard-base` | https://huggingface.co/dcarpintero/pangolin-guard-base | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2` | https://huggingface.co/DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `DevQuasar-10/mrfakename.mistral-small-3.1-24b-base-2503-hf-GGUF` | https://huggingface.co/DevQuasar-10/mrfakename.mistral-small-3.1-24b-base-2503-hf-GGUF | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `DevQuasar/nvidia.Nemotron-Content-Safety-Reasoning-4B-GGUF` | https://huggingface.co/DevQuasar/nvidia.Nemotron-Content-Safety-Reasoning-4B-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `donate110/apex-moderation-7b` | https://huggingface.co/donate110/apex-moderation-7b | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `dots-studio/dots.llm1.base` | https://huggingface.co/dots-studio/dots.llm1.base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `dots-studio/dots.ocr` | https://huggingface.co/dots-studio/dots.ocr | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `dphn/dolphin-2.5-mixtral-8x7b` | https://huggingface.co/dphn/dolphin-2.5-mixtral-8x7b | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Dream-org/Dream-v0-Base-7B` | https://huggingface.co/Dream-org/Dream-v0-Base-7B | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `drowzeys/keys-DeepSeekV4Flash-Vision-EXP-ablit` | https://huggingface.co/drowzeys/keys-DeepSeekV4Flash-Vision-EXP-ablit | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `duanyu027/moderation_0628` | https://huggingface.co/duanyu027/moderation_0628 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `duanyu027/moderation_0703_deberta_v3_small` | https://huggingface.co/duanyu027/moderation_0703_deberta_v3_small | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `duanyu027/moderation_0703_deberta_v3_small_onnx` | https://huggingface.co/duanyu027/moderation_0703_deberta_v3_small_onnx | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Earlychildhoodeducation/EleMo-V2-Base` | https://huggingface.co/Earlychildhoodeducation/EleMo-V2-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `ellery/text-safety-embedding` | https://huggingface.co/ellery/text-safety-embedding | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF` | https://huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `enguard/medium-guard-128m-xx-prompt-harassment-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-harassment-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/medium-guard-128m-xx-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/medium-guard-128m-xx-prompt-harmfulness-multilabel-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-harmfulness-multilabel-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/medium-guard-128m-xx-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/medium-guard-128m-xx-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/medium-guard-128m-xx-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/medium-guard-128m-xx-prompt-violence-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/small-guard-32m-en-prompt-harassment-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-harassment-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/small-guard-32m-en-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/small-guard-32m-en-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/small-guard-32m-en-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/small-guard-32m-en-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/small-guard-32m-en-prompt-violence-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-2m-en-prompt-harassment-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-harassment-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-2m-en-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-2m-en-prompt-harmfulness-multilabel-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-harmfulness-multilabel-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-2m-en-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-2m-en-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-2m-en-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-2m-en-prompt-violence-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-4m-en-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-4m-en-prompt-harmfulness-multilabel-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-harmfulness-multilabel-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-4m-en-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-4m-en-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-4m-en-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-4m-en-prompt-violence-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-8m-en-prompt-harassment-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-harassment-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-8m-en-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-8m-en-prompt-harmfulness-multilabel-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-harmfulness-multilabel-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-8m-en-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-8m-en-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-8m-en-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `enguard/tiny-guard-8m-en-prompt-violence-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `exeterminal/Exe-Guard-Dynamic-GGUF` | https://huggingface.co/exeterminal/Exe-Guard-Dynamic-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Extropic-AI/Z1T-0` | https://huggingface.co/Extropic-AI/Z1T-0 | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `F16/krea2-turbo-sda` | https://huggingface.co/F16/krea2-turbo-sda | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `facebook/dinov3-vitl16-pretrain-lvd1689m` | https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `facebook/mms-300m` | https://huggingface.co/facebook/mms-300m | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `facebook/sam3.1` | https://huggingface.co/facebook/sam3.1 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `FastVideo/FastVideo-FastH3-4-step-Preview-v1-VSA-DataFree` | https://huggingface.co/FastVideo/FastVideo-FastH3-4-step-Preview-v1-VSA-DataFree | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `flowxai/moderation` | https://huggingface.co/flowxai/moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `FrontiersMind/Nandi-Mini-150M-GuardRails` | https://huggingface.co/FrontiersMind/Nandi-Mini-150M-GuardRails | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `FWKV/Myosotis-1-base` | https://huggingface.co/FWKV/Myosotis-1-base | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `google/timesfm-3.0-pytorch` | https://huggingface.co/google/timesfm-3.0-pytorch | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `GSAI-ML/LLaDA-8B-Base` | https://huggingface.co/GSAI-ML/LLaDA-8B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `GSAI-ML/LLaDA-8B-Instruct` | https://huggingface.co/GSAI-ML/LLaDA-8B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `hayatiali/turkish-safety` | https://huggingface.co/hayatiali/turkish-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `hfmlsoc/ncii-light-guard-v01` | https://huggingface.co/hfmlsoc/ncii-light-guard-v01 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Himanshu101789/xlmr-multi-lingual-content-moderation` | https://huggingface.co/Himanshu101789/xlmr-multi-lingual-content-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `hivetrace/gliner-guard-uniencoder` | https://huggingface.co/hivetrace/gliner-guard-uniencoder | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `HojoAI/Hojo-ASR-Multi-V1` | https://huggingface.co/HojoAI/Hojo-ASR-Multi-V1 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` | https://huggingface.co/hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4 | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `huihui-ai/Huihui-Qwen3.8-Flash-Next-abliterated-GGUF` | https://huggingface.co/huihui-ai/Huihui-Qwen3.8-Flash-Next-abliterated-GGUF | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `huyleit/phobert-vi-moderation-v1.1` | https://huggingface.co/huyleit/phobert-vi-moderation-v1.1 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `iamrazi/text-moderation` | https://huggingface.co/iamrazi/text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `ibm-granite/granitelib-guardian-r1.0` | https://huggingface.co/ibm-granite/granitelib-guardian-r1.0 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `ifmain/ModerationBERT-En-02` | https://huggingface.co/ifmain/ModerationBERT-En-02 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `inclusionAI/Ling-3.0-flash` | https://huggingface.co/inclusionAI/Ling-3.0-flash | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `inclusionAI/Ling-3.0-flash-Fin` | https://huggingface.co/inclusionAI/Ling-3.0-flash-Fin | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `inclusionAI/Ling-3.0-tiny` | https://huggingface.co/inclusionAI/Ling-3.0-tiny | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `inclusionAI/LLaDA-Image` | https://huggingface.co/inclusionAI/LLaDA-Image | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Jackrong/Qwopus3.8-27B-Flash` | https://huggingface.co/Jackrong/Qwopus3.8-27B-Flash | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Jackrong/Qwopus3.8-27B-Flash-GGUF` | https://huggingface.co/Jackrong/Qwopus3.8-27B-Flash-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `jaimevera1107/moderation-topics` | https://huggingface.co/jaimevera1107/moderation-topics | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `JashVora7/hybrid-guardrails-deberta-moderation` | https://huggingface.co/JashVora7/hybrid-guardrails-deberta-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `JashVora7/hybrid-guardrails-distilbert-moderation` | https://huggingface.co/JashVora7/hybrid-guardrails-distilbert-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `JetBrains/Mellum2-12B-A2.5B-Base` | https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `JetBrains/Mellum2-12B-A2.5B-Instruct-GGUF-Q8_0` | https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Instruct-GGUF-Q8_0 | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `K-intelligence/Midm-2.0-Base-Instruct` | https://huggingface.co/K-intelligence/Midm-2.0-Base-Instruct | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `kakaocorp/kanana-2-1.3b-base` | https://huggingface.co/kakaocorp/kanana-2-1.3b-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `kalyan1900/PII-GUARD-Qwen2.5-1.5B` | https://huggingface.co/kalyan1900/PII-GUARD-Qwen2.5-1.5B | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `katanemo/Arch-Guard` | https://huggingface.co/katanemo/Arch-Guard | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `katuni4ka/tiny-random-stable-diffusion-with-safety-checker` | https://huggingface.co/katuni4ka/tiny-random-stable-diffusion-with-safety-checker | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `KennethFal/vh5tape-vhs-lora-minimax-h3` | https://huggingface.co/KennethFal/vh5tape-vhs-lora-minimax-h3 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `keremberke/yolov5m-construction-safety` | https://huggingface.co/keremberke/yolov5m-construction-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `keremberke/yolov5n-construction-safety` | https://huggingface.co/keremberke/yolov5n-construction-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `keremberke/yolov5s-construction-safety` | https://huggingface.co/keremberke/yolov5s-construction-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `kishan4444/text-moderation` | https://huggingface.co/kishan4444/text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `kishan4444/text_moderation_model` | https://huggingface.co/kishan4444/text_moderation_model | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `KORMo-Team/KORMo-10B-base` | https://huggingface.co/KORMo-Team/KORMo-10B-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `krea/Krea-2-Raw` | https://huggingface.co/krea/Krea-2-Raw | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `krea/Krea-2-Turbo` | https://huggingface.co/krea/Krea-2-Turbo | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `lamdx4/phobert-vi-moderation` | https://huggingface.co/lamdx4/phobert-vi-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-AWQ` | https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `lightonai/LightOnOCR-2-1B-base` | https://huggingface.co/lightonai/LightOnOCR-2-1B-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `LiquidAI/LFM2.5-1.2B-Base` | https://huggingface.co/LiquidAI/LFM2.5-1.2B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `LiquidAI/LFM2.5-1.2B-Instruct` | https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `LiquidAI/LFM2.5-1.2B-Instruct-GGUF` | https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `LiquidAI/LFM2.5-2.6B-Base` | https://huggingface.co/LiquidAI/LFM2.5-2.6B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `LiquidAI/LFM2.5-230M-Base` | https://huggingface.co/LiquidAI/LFM2.5-230M-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `LiquidAI/LFM2.5-350M-Base` | https://huggingface.co/LiquidAI/LFM2.5-350M-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `llm-semantic-router/mmbert-safety-binary-hazard` | https://huggingface.co/llm-semantic-router/mmbert-safety-binary-hazard | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mattshumer/Reflection-Llama-3.1-70B` | https://huggingface.co/mattshumer/Reflection-Llama-3.1-70B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `mbehbooei/vit-base-patch16-224-in21k-finetuned-moderation` | https://huggingface.co/mbehbooei/vit-base-patch16-224-in21k-finetuned-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `menezesbruno/manaca-1b-base` | https://huggingface.co/menezesbruno/manaca-1b-base | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `meta-llama/Meta-Llama-3-70B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-70B-Instruct | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `meta-llama/Meta-Llama-3-8B` | https://huggingface.co/meta-llama/Meta-Llama-3-8B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `meta-llama/Meta-Llama-Guard-2-8B` | https://huggingface.co/meta-llama/Meta-Llama-Guard-2-8B | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `meta-models/Muse-Glimmer-30B` | https://huggingface.co/meta-models/Muse-Glimmer-30B | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `mezattn/eva02_base_patch14_448_moderation` | https://huggingface.co/mezattn/eva02_base_patch14_448_moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `microsoft/bitnet-b1.58-2B-4T` | https://huggingface.co/microsoft/bitnet-b1.58-2B-4T | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `microsoft/VibeVoice-ASR-Streaming-7B` | https://huggingface.co/microsoft/VibeVoice-ASR-Streaming-7B | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `miguelonana/camembert-bank-moderation-fr` | https://huggingface.co/miguelonana/camembert-bank-moderation-fr | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `MINSEONG12/moderation` | https://huggingface.co/MINSEONG12/moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mistralai/Mistral-7B-v0.1` | https://huggingface.co/mistralai/Mistral-7B-v0.1 | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `mixedbread-ai/mxbai-rerank-base-v2` | https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `mradermacher/BananaMind-Content-Safety-Mini-1.5-i1-GGUF` | https://huggingface.co/mradermacher/BananaMind-Content-Safety-Mini-1.5-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/BananaMind-V2.5-Content-Safety-GGUF` | https://huggingface.co/mradermacher/BananaMind-V2.5-Content-Safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/dipg-safety-agent-v2-float16-GGUF` | https://huggingface.co/mradermacher/dipg-safety-agent-v2-float16-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/GuardReasoner-VL-Eco-7B-i1-GGUF` | https://huggingface.co/mradermacher/GuardReasoner-VL-Eco-7B-i1-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Heretic-Nemotron-Content-Safety-Reasoning-4B-GGUF` | https://huggingface.co/mradermacher/Heretic-Nemotron-Content-Safety-Reasoning-4B-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Heretic-Nemotron-Content-Safety-Reasoning-4B-i1-GGUF` | https://huggingface.co/mradermacher/Heretic-Nemotron-Content-Safety-Reasoning-4B-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Innospark-72b-safety-GGUF` | https://huggingface.co/mradermacher/Innospark-72b-safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Intelligem-V1-Safety-0.3B-GGUF` | https://huggingface.co/mradermacher/Intelligem-V1-Safety-0.3B-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Mimo-Think-in-Safety-GGUF` | https://huggingface.co/mradermacher/Mimo-Think-in-Safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Open-Telco-LLM-8.3B-Safety-GGUF` | https://huggingface.co/mradermacher/Open-Telco-LLM-8.3B-Safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Reflector-Internalizing-Safety-Llama-3.1-8B-RL-GGUF` | https://huggingface.co/mradermacher/Reflector-Internalizing-Safety-Llama-3.1-8B-RL-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Reflector-Internalizing-Safety-Llama-3.1-8B-RL-i1-GGUF` | https://huggingface.co/mradermacher/Reflector-Internalizing-Safety-Llama-3.1-8B-RL-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/SafeAtlas-Guard-2B-GGUF` | https://huggingface.co/mradermacher/SafeAtlas-Guard-2B-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/SafeAtlas-Guard-4B-GGUF` | https://huggingface.co/mradermacher/SafeAtlas-Guard-4B-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/SafeAtlas-Guard-8B-GGUF` | https://huggingface.co/mradermacher/SafeAtlas-Guard-8B-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Safety-A1-ppo-full-GGUF` | https://huggingface.co/mradermacher/Safety-A1-ppo-full-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/SafeWork-RM-Safety-7B-i1-GGUF` | https://huggingface.co/mradermacher/SafeWork-RM-Safety-7B-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/saroku-safety-0.5b-GGUF` | https://huggingface.co/mradermacher/saroku-safety-0.5b-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Stentor-30M-Instruct-heretic-safety-defiltered-GGUF` | https://huggingface.co/mradermacher/Stentor-30M-Instruct-heretic-safety-defiltered-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/Stentor-30M-Instruct-heretic-safety-defiltered-i1-GGUF` | https://huggingface.co/mradermacher/Stentor-30M-Instruct-heretic-safety-defiltered-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/TinyR1-Safety-8B-GGUF` | https://huggingface.co/mradermacher/TinyR1-Safety-8B-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `mradermacher/WaRP-Safety-Llama3_8B_Instruct-20251027_125759-GGUF` | https://huggingface.co/mradermacher/WaRP-Safety-Llama3_8B_Instruct-20251027_125759-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `MurrayTom/TS-Guard` | https://huggingface.co/MurrayTom/TS-Guard | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `NAMAA-Space/Ara-Prompt-Guard_V0` | https://huggingface.co/NAMAA-Space/Ara-Prompt-Guard_V0 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Nanbeige/Nanbeige4.1-3B` | https://huggingface.co/Nanbeige/Nanbeige4.1-3B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Nanbeige/Nanbeige4.2-3B` | https://huggingface.co/Nanbeige/Nanbeige4.2-3B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Nanbeige/Nanbeige4.2-3B-DSpark` | https://huggingface.co/Nanbeige/Nanbeige4.2-3B-DSpark | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `NemoraAi/modernbert-chat-moderation-X-V2` | https://huggingface.co/NemoraAi/modernbert-chat-moderation-X-V2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `NemoraAi/roberta-chat-moderation-X` | https://huggingface.co/NemoraAi/roberta-chat-moderation-X | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `NeuralTrust/prompt-guard-oss-small` | https://huggingface.co/NeuralTrust/prompt-guard-oss-small | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Niansuh/Prompt-Guard-86M` | https://huggingface.co/Niansuh/Prompt-Guard-86M | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Nikitojo/moderation` | https://huggingface.co/Nikitojo/moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `nisten/Biggie-SmoLlm-0.15B-Base` | https://huggingface.co/nisten/Biggie-SmoLlm-0.15B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `NousResearch/Meta-Llama-3.1-8B-Instruct` | https://huggingface.co/NousResearch/Meta-Llama-3.1-8B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Null-Guard/LFM2.5-230M-distilled-Gemini-3.8-Flash` | https://huggingface.co/Null-Guard/LFM2.5-230M-distilled-Gemini-3.8-Flash | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Null-Guard/LFM2.5-230M-distilled-Gemini-3.8-Flash-Uncensored` | https://huggingface.co/Null-Guard/LFM2.5-230M-distilled-Gemini-3.8-Flash-Uncensored | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Null-Guard/LFM2.5-230M-Uncensored-GGUF` | https://huggingface.co/Null-Guard/LFM2.5-230M-Uncensored-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `nvidia/Aegis-AI-Content-Safety-LlamaGuard-Permissive-1.0` | https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Permissive-1.0 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `nvidia/Cosmos-Guardrail1` | https://huggingface.co/nvidia/Cosmos-Guardrail1 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `nvidia/instruction-data-guard` | https://huggingface.co/nvidia/instruction-data-guard | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `nvidia/Minitron-4B-Base` | https://huggingface.co/nvidia/Minitron-4B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `nvidia/Minitron-8B-Base` | https://huggingface.co/nvidia/Minitron-8B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `nvidia/Mistral-NeMo-Minitron-8B-Base` | https://huggingface.co/nvidia/Mistral-NeMo-Minitron-8B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-Base-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-Base-BF16 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-Base-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-Base-BF16 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Base-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Base-BF16 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `nvidia/NVIDIA-Nemotron-Nano-12B-v2-Base` | https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-12B-v2-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `OctoThinker/OctoThinker-1B-Hybrid-Base` | https://huggingface.co/OctoThinker/OctoThinker-1B-Hybrid-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `onnx-community/Florence-2-base-ft` | https://huggingface.co/onnx-community/Florence-2-base-ft | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `opencerebral/Boris-1.7-D60M-n30M` | https://huggingface.co/opencerebral/Boris-1.7-D60M-n30M | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `openchat/openchat_3.5` | https://huggingface.co/openchat/openchat_3.5 | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `OpenVDN/vdn-minimax-h3` | https://huggingface.co/OpenVDN/vdn-minimax-h3 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `opus-research/opus-moderation-1` | https://huggingface.co/opus-research/opus-moderation-1 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `opus-research/opus-moderation-2` | https://huggingface.co/opus-research/opus-moderation-2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `opus-research/opus-moderation-3` | https://huggingface.co/opus-research/opus-moderation-3 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `opus-research/opus-moderation-4-fast` | https://huggingface.co/opus-research/opus-moderation-4-fast | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `opus-research/opus-moderation-4-large` | https://huggingface.co/opus-research/opus-moderation-4-large | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `oshizo/japanese-sexual-moderation` | https://huggingface.co/oshizo/japanese-sexual-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `oshizo/japanese-sexual-moderation-v2` | https://huggingface.co/oshizo/japanese-sexual-moderation-v2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `OwenElliott/image-safety-classifier-l` | https://huggingface.co/OwenElliott/image-safety-classifier-l | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `OwenElliott/image-safety-classifier-s` | https://huggingface.co/OwenElliott/image-safety-classifier-s | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `OwenElliott/image-safety-classifier-xs` | https://huggingface.co/OwenElliott/image-safety-classifier-xs | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `oxyapi/albert-moderation-001` | https://huggingface.co/oxyapi/albert-moderation-001 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `oxyapi/albert-moderation-001-ONNX` | https://huggingface.co/oxyapi/albert-moderation-001-ONNX | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `peculiar-ragdoll/Dirk-Qwen3.8-27B-GGUF` | https://huggingface.co/peculiar-ragdoll/Dirk-Qwen3.8-27B-GGUF | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF` | https://huggingface.co/peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF-MTP` | https://huggingface.co/peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF-MTP | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `perplexity-ai/pplx-pii-masking` | https://huggingface.co/perplexity-ai/pplx-pii-masking | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `pfnet/plamo-3-nict-2b-base` | https://huggingface.co/pfnet/plamo-3-nict-2b-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `phasefield-audio/Irodori-TTS-v4.1-Anime` | https://huggingface.co/phasefield-audio/Irodori-TTS-v4.1-Anime | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `pipecat-ai/phonellm-alpha-1` | https://huggingface.co/pipecat-ai/phonellm-alpha-1 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `PL-RnD/privacy-moderation-large` | https://huggingface.co/PL-RnD/privacy-moderation-large | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `PL-RnD/privacy-moderation-large-4bit` | https://huggingface.co/PL-RnD/privacy-moderation-large-4bit | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `PL-RnD/privacy-moderation-small` | https://huggingface.co/PL-RnD/privacy-moderation-small | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `PL-RnD/privacy-moderation-small-onnx-8bit` | https://huggingface.co/PL-RnD/privacy-moderation-small-onnx-8bit | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `principled-intelligence/scope-guard-4B-q-2601` | https://huggingface.co/principled-intelligence/scope-guard-4B-q-2601 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `prism-ml/Bonsai-27B-gguf` | https://huggingface.co/prism-ml/Bonsai-27B-gguf | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `prism-ml/Ternary-Bonsai-27B-gguf` | https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `prithivMLmods/GA-Guard-AIO-GGUF` | https://huggingface.co/prithivMLmods/GA-Guard-AIO-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `prithivMLmods/VideoGuard-Qwen3.5-4B-Safety-RL-Uncensored` | https://huggingface.co/prithivMLmods/VideoGuard-Qwen3.5-4B-Safety-RL-Uncensored | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `prithivMLmods/VideoGuard-Qwen3.5-4B-Safety-RL-Uncensored-GGUF` | https://huggingface.co/prithivMLmods/VideoGuard-Qwen3.5-4B-Safety-RL-Uncensored-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `prithivMLmods/VideoGuard-Qwen3.5-9B-Safety-RL-Uncensored-GGUF` | https://huggingface.co/prithivMLmods/VideoGuard-Qwen3.5-9B-Safety-RL-Uncensored-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `PrunaAI/Meta-Llama-Guard-2-8B-GGUF-smashed` | https://huggingface.co/PrunaAI/Meta-Llama-Guard-2-8B-GGUF-smashed | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `QCRI/Fanar-1-9B-Instruct` | https://huggingface.co/QCRI/Fanar-1-9B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `QuantFactory/Meta-Llama-Guard-2-8B-GGUF` | https://huggingface.co/QuantFactory/Meta-Llama-Guard-2-8B-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Qwen/QwQ-32B` | https://huggingface.co/Qwen/QwQ-32B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Qwen/QwQ-32B-Preview` | https://huggingface.co/Qwen/QwQ-32B-Preview | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Raghav-Singhal/pbsftmix-cite-safety10-nosys-epe-3b-nobce` | https://huggingface.co/Raghav-Singhal/pbsftmix-cite-safety10-nosys-epe-3b-nobce | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Raghav-Singhal/pbsftmix-cite-safety10-nosys-normal-3b` | https://huggingface.co/Raghav-Singhal/pbsftmix-cite-safety10-nosys-normal-3b | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Raghav-Singhal/pbsftmix-cite-safety30-nosys-epe-3b-nobce` | https://huggingface.co/Raghav-Singhal/pbsftmix-cite-safety30-nosys-epe-3b-nobce | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Raghav-Singhal/pbsftmix-cite-safety30-nosys-normal-3b` | https://huggingface.co/Raghav-Singhal/pbsftmix-cite-safety30-nosys-normal-3b | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `regnant-io/kw5-lite-base` | https://huggingface.co/regnant-io/kw5-lite-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `RichardErkhov/alpindale_-_Llama-Guard-3-1B-gguf` | https://huggingface.co/RichardErkhov/alpindale_-_Llama-Guard-3-1B-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/Essacheez_-_Llama-2-7b-chat-SafetyData-finetune-translation-10k-old-prompt-style-gguf` | https://huggingface.co/RichardErkhov/Essacheez_-_Llama-2-7b-chat-SafetyData-finetune-translation-10k-old-prompt-style-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-code-1.2k-safetyllamas_stanford-default-style-gguf` | https://huggingface.co/RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-code-1.2k-safetyllamas_stanford-default-style-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-combine-4.2k-default-style-gguf` | https://huggingface.co/RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-combine-4.2k-default-style-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-summerization-1.2k-safetyllamas_stanford-default-style-gguf` | https://huggingface.co/RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-summerization-1.2k-safetyllamas_stanford-default-style-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/guardrail_-_llama-2-7b-guanaco-instruct-sharded-gguf` | https://huggingface.co/RichardErkhov/guardrail_-_llama-2-7b-guanaco-instruct-sharded-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/ibm-granite_-_granite-guardian-3.0-2b-gguf` | https://huggingface.co/RichardErkhov/ibm-granite_-_granite-guardian-3.0-2b-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/ibm-granite_-_granite-guardian-3.0-8b-gguf` | https://huggingface.co/RichardErkhov/ibm-granite_-_granite-guardian-3.0-8b-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/meta-llama_-_Llama-Guard-3-1B-gguf` | https://huggingface.co/RichardErkhov/meta-llama_-_Llama-Guard-3-1B-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/skyai798_-_safety_v2_math_v1-gguf` | https://huggingface.co/RichardErkhov/skyai798_-_safety_v2_math_v1-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/thusinh1969_-_Guardian-V0.1-LLaMA3.1-8B-5G-6Oct2024-epoch1.3-gguf` | https://huggingface.co/RichardErkhov/thusinh1969_-_Guardian-V0.1-LLaMA3.1-8B-5G-6Oct2024-epoch1.3-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/Unispac_-_Gemma-2-9B-IT-With-Deeper-Safety-Alignment-gguf` | https://huggingface.co/RichardErkhov/Unispac_-_Gemma-2-9B-IT-With-Deeper-Safety-Alignment-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `RichardErkhov/ZiweiLiu96_-_llama-3.2-3b-Content-Moderation-gguf` | https://huggingface.co/RichardErkhov/ZiweiLiu96_-_llama-3.2-3b-Content-Moderation-gguf | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Roblox/voice-safety-classifier-v2` | https://huggingface.co/Roblox/voice-safety-classifier-v2 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `rombodawg/Everyone-Coder-4x7b-Base` | https://huggingface.co/rombodawg/Everyone-Coder-4x7b-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `rostlabs/rost-1b-base` | https://huggingface.co/rostlabs/rost-1b-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `RyanStudio/Mezzo-Prompt-Guard-v2-Base` | https://huggingface.co/RyanStudio/Mezzo-Prompt-Guard-v2-Base | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `SafetyMP/corporate-site-harness-llm` | https://huggingface.co/SafetyMP/corporate-site-harness-llm | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Sajeevan2001/bert-question-moderation` | https://huggingface.co/Sajeevan2001/bert-question-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `sapienzanlp/Minerva-350M-base-v1.0` | https://huggingface.co/sapienzanlp/Minerva-350M-base-v1.0 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `sapienzanlp/Minerva-3B-base-v1.0` | https://huggingface.co/sapienzanlp/Minerva-3B-base-v1.0 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `saravanakarthikeyan/GuardShield-Qwen2.5-3B-16bit` | https://huggingface.co/saravanakarthikeyan/GuardShield-Qwen2.5-3B-16bit | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Saswith/text-moderation` | https://huggingface.co/Saswith/text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `saturday-labs/turkish-pii-guard-0.8b` | https://huggingface.co/saturday-labs/turkish-pii-guard-0.8b | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Satya-dev-tech/toxic-comment-moderation` | https://huggingface.co/Satya-dev-tech/toxic-comment-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `sheltron-ai/prompt-guard-68m` | https://huggingface.co/sheltron-ai/prompt-guard-68m | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Sheshank2609/content-moderation-distilbert` | https://huggingface.co/Sheshank2609/content-moderation-distilbert | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `shibing624/macbert4csc-base-chinese` | https://huggingface.co/shibing624/macbert4csc-base-chinese | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `silicondali/doodle-magic-safety` | https://huggingface.co/silicondali/doodle-magic-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `skt/kogpt2-base-v2` | https://huggingface.co/skt/kogpt2-base-v2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `snkii/Sori-1B` | https://huggingface.co/snkii/Sori-1B | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `speakleash/Bielik-11B-v3.0-Instruct-awq` | https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct-awq | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `speakleash/Bielik-Guard-0.1B-v1.1` | https://huggingface.co/speakleash/Bielik-Guard-0.1B-v1.1 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `speakleash/Bielik-Guard-0.5B-v1.1` | https://huggingface.co/speakleash/Bielik-Guard-0.5B-v1.1 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `stelterlab/Mistral-Small-24B-Instruct-2501-AWQ` | https://huggingface.co/stelterlab/Mistral-Small-24B-Instruct-2501-AWQ | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `StrictlyInsecure/discord-moderation-minilm` | https://huggingface.co/StrictlyInsecure/discord-moderation-minilm | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `StrictlyInsecure/discord-moderation-minilm-l12` | https://huggingface.co/StrictlyInsecure/discord-moderation-minilm-l12 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `sullivan1502/base-action-grpo` | https://huggingface.co/sullivan1502/base-action-grpo | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `sullivan1502/base-action-pretrain` | https://huggingface.co/sullivan1502/base-action-pretrain | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `sullivan1502/base-action-sft` | https://huggingface.co/sullivan1502/base-action-sft | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `sullivan1502/base-zone-grpo` | https://huggingface.co/sullivan1502/base-zone-grpo | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `sullivan1502/base-zone-pretrain` | https://huggingface.co/sullivan1502/base-zone-pretrain | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `superwhisper/s1-mini` | https://huggingface.co/superwhisper/s1-mini | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `sweetpapa/sentry-270m-moderation-v3` | https://huggingface.co/sweetpapa/sentry-270m-moderation-v3 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `tencent/ContextPilot-14B` | https://huggingface.co/tencent/ContextPilot-14B | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `tencent/HunyuanImage-3.0` | https://huggingface.co/tencent/HunyuanImage-3.0 | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `tencent/HY-MT1.5-1.8B` | https://huggingface.co/tencent/HY-MT1.5-1.8B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `tencent/Hy-MT2-1.8B` | https://huggingface.co/tencent/Hy-MT2-1.8B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `tencent/Hy4-preview` | https://huggingface.co/tencent/Hy4-preview | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `TheBloke/merlyn-education-safety-GGUF` | https://huggingface.co/TheBloke/merlyn-education-safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `thuml/sundial-base-128m` | https://huggingface.co/thuml/sundial-base-128m | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `togethercomputer/evo-1-8k-base` | https://huggingface.co/togethercomputer/evo-1-8k-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `togethercomputer/GPT-JT-Moderation-6B` | https://huggingface.co/togethercomputer/GPT-JT-Moderation-6B | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `TomLEE2026/image-moderation-v1` | https://huggingface.co/TomLEE2026/image-moderation-v1 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `trl-internal-testing/tiny-Qwen3ForCausalLM-Instruct-2507` | https://huggingface.co/trl-internal-testing/tiny-Qwen3ForCausalLM-Instruct-2507 | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `typhoon-ai/typhoon2-safety-preview` | https://huggingface.co/typhoon-ai/typhoon2-safety-preview | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `unsloth/Meta-Llama-3.1-8B-Instruct` | https://huggingface.co/unsloth/Meta-Llama-3.1-8B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `unsloth/Mistral-Nemo-Base-2407-bnb-4bit` | https://huggingface.co/unsloth/Mistral-Nemo-Base-2407-bnb-4bit | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `usail-hkust/JailJudge-guard` | https://huggingface.co/usail-hkust/JailJudge-guard | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `vaiv/GeM2-Llamion-14B-Base` | https://huggingface.co/vaiv/GeM2-Llamion-14B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `VertexAGI/prism-safety-1-micro` | https://huggingface.co/VertexAGI/prism-safety-1-micro | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Viggle/Viggle-Animate` | https://huggingface.co/Viggle/Viggle-Animate | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `Vrandan/Comment-Moderation` | https://huggingface.co/Vrandan/Comment-Moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `weeqeen/rubert-base-cased-finetuned-moderation` | https://huggingface.co/weeqeen/rubert-base-cased-finetuned-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `winninghealth/WiNGPT2-Llama-3-8B-Base` | https://huggingface.co/winninghealth/WiNGPT2-Llama-3-8B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `XHToken/Spark-X2.5-1.7B` | https://huggingface.co/XHToken/Spark-X2.5-1.7B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `XHToken/Spark-X2.5-1.7B-Base` | https://huggingface.co/XHToken/Spark-X2.5-1.7B-Base | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `XHToken/Spark-X2.5-1.7B-GGUF` | https://huggingface.co/XHToken/Spark-X2.5-1.7B-GGUF | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `XHToken/Spark-X2.5-4B` | https://huggingface.co/XHToken/Spark-X2.5-4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `XHToken/Spark-X2.5-4B-Base` | https://huggingface.co/XHToken/Spark-X2.5-4B-Base | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `XHToken/Spark-X2.5-4B-GGUF` | https://huggingface.co/XHToken/Spark-X2.5-4B-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `XiaomiMiMo/MiMo-7B-Base` | https://huggingface.co/XiaomiMiMo/MiMo-7B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `xlnet/xlnet-base-cased` | https://huggingface.co/xlnet/xlnet-base-cased | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |
| `yueliu1999/GuardReasoner-8B` | https://huggingface.co/yueliu1999/GuardReasoner-8B | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `yueliu1999/GuardReasoner-VL-7B` | https://huggingface.co/yueliu1999/GuardReasoner-VL-7B | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `ZeroLoss-Lab/Innospark-72b-safety` | https://huggingface.co/ZeroLoss-Lab/Innospark-72b-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `ZJU-Safety/DARWIN-Guard` | https://huggingface.co/ZJU-Safety/DARWIN-Guard | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `zjunlp/SafeEdit-Safety-Classifier` | https://huggingface.co/zjunlp/SafeEdit-Safety-Classifier | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (targeted guard/safety/moderation search floor) |
| `Zyphra/Zamba2-1.2B-instruct` | https://huggingface.co/Zyphra/Zamba2-1.2B-instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-query floor) |

## Duplicate mappings (708)

Every signal counted as a duplicate, with what it folded onto. This is the mapping behind
`raw_signals = duplicate_signals + unique_candidates`; the reconciliation can be recomputed from
this table and the two parked tables above.

| signal | source URL | fetched | returned by | folds onto |
|---|---|---|---|---|
| `aaron-xichen/pytorch-playground` | https://github.com/aaron-xichen/pytorch-playground | 2026-09-07 | `comp_t_quant` | release or SKU of pytorch |
| `agentanywhere/shuddhi` | https://github.com/agentanywhere/shuddhi | 2026-09-07 | `dpt_dedup`, `dpt_q_dedup` | repeats signal agentanywhere/shuddhi |
| `agentcontrol/agent-control` | https://github.com/agentcontrol/agent-control | 2026-09-07 | `safe_t_guardrails`, `safe_t_aisafety` | repeats signal agentcontrol/agent-control |
| `ahmad-alismail/LLM_based_Synthetic_Data_Generation` | https://github.com/ahmad-alismail/LLM_based_Synthetic_Data_Generation | 2026-09-07 | `dpt_synth` | release or SKU of llm |
| `akto-api-security/akto` | https://github.com/akto-api-security/akto | 2026-09-07 | `safe_t_guardrails`, `safe_t_redteam` | repeats signal akto-api-security/akto |
| `alibaba/BladeDISC` | https://github.com/alibaba/BladeDISC | 2026-09-07 | `comp_t_mlir`, `comp_t_tensorcompiler` | repeats signal alibaba/BladeDISC |
| `AllisonDing/LLM-data-processing-agentic-skills` | https://github.com/AllisonDing/LLM-data-processing-agentic-skills | 2026-09-07 | `dpt_q_curator` | release or SKU of llm |
| `apache/tvm` | https://github.com/apache/tvm | 2026-09-07 | `comp_t_tensorcompiler` | head product apache-tvm |
| `argilla-io/distilabel` | https://github.com/argilla-io/distilabel | 2026-09-07 | `dpt_t_synthetic` | head product distilabel |
| `arnabroy734/LLM_jailbreak_shield` | https://github.com/arnabroy734/LLM_jailbreak_shield | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm |
| `asamassekou10/ship-safe` | https://github.com/asamassekou10/ship-safe | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal asamassekou10/ship-safe |
| `backblaze-b2-samples/nemo-curator-training-data` | https://github.com/backblaze-b2-samples/nemo-curator-training-data | 2026-09-07 | `dpt_q_curator` | release or SKU of nemo-curator |
| `bespokelabsai/curator` | https://github.com/bespokelabsai/curator | 2026-09-07 | `dpt_t_synthetic`, `dpt_q_curator` | repeats signal bespokelabsai/curator |
| `bitsandbytes-foundation/bitsandbytes` | https://github.com/bitsandbytes-foundation/bitsandbytes | 2026-09-07 | `comp_t_quant` | head product bitsandbytes |
| `buildship-ai/LLM-Web-Crawler` | https://github.com/buildship-ai/LLM-Web-Crawler | 2026-09-07 | `dpt_t_webscraping` | release or SKU of llm |
| `CHATS-lab/verbalized-sampling` | https://github.com/CHATS-lab/verbalized-sampling | 2026-09-07 | `dpt_synth`, `dpt_t_synthetic` | repeats signal CHATS-lab/verbalized-sampling |
| `chawins/llm-sp` | https://github.com/chawins/llm-sp | 2026-09-07 | `safe_t_llmsecurity` | release or SKU of llm |
| `cleanlab/cleanlab` | https://github.com/cleanlab/cleanlab | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal cleanlab/cleanlab |
| `cleanlab/cleanlab-studio` | https://github.com/cleanlab/cleanlab-studio | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal cleanlab/cleanlab-studio |
| `coderonion/awesome-cuda-and-hpc` | https://github.com/coderonion/awesome-cuda-and-hpc | 2026-09-07 | `comp_t_mlir`, `comp_t_triton` | repeats signal coderonion/awesome-cuda-and-hpc |
| `Colin6618/flashinfer-performance-benchmarks` | https://github.com/Colin6618/flashinfer-performance-benchmarks | 2026-09-07 | `comp_q_kernel` | release or SKU of flashinfer |
| `CollieAi/llm-firewall` | https://github.com/CollieAi/llm-firewall | 2026-09-07 | `safe_t_moderation` | release or SKU of llm |
| `CyberStrikeus/CyberStrike` | https://github.com/CyberStrikeus/CyberStrike | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam` | repeats signal CyberStrikeus/CyberStrike |
| `daochenzha/data-centric-AI` | https://github.com/daochenzha/data-centric-AI | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal daochenzha/data-centric-AI |
| `datajuicer/data-juicer` | https://github.com/datajuicer/data-juicer | 2026-09-07 | `dpt_t_synthetic` | head product data-juicer |
| `datawhalechina/llm-algo-leetcode` | https://github.com/datawhalechina/llm-algo-leetcode | 2026-09-07 | `comp_t_triton` | release or SKU of llm |
| `deadbits/vigil-llm` | https://github.com/deadbits/vigil-llm | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal deadbits/vigil-llm |
| `dezoito/markitdown-api` | https://github.com/dezoito/markitdown-api | 2026-09-07 | `dpt_q_pdf` | release or SKU of markitdown |
| `duoan/mega-data-factory` | https://github.com/duoan/mega-data-factory | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal duoan/mega-data-factory |
| `ethz-spylab/agentdojo` | https://github.com/ethz-spylab/agentdojo | 2026-09-07 | `safe_t_promptinjection` | head product agentdojo |
| `evidentlyai/evidently` | https://github.com/evidentlyai/evidently | 2026-09-07 | `dpt_t_dataquality` | head product evidently |
| `facebookresearch/synth_gen` | https://github.com/facebookresearch/synth_gen | 2026-09-07 | `dpt_synth` | release or SKU of synth |
| `faiyazabdullah/JailbreakTracer` | https://github.com/faiyazabdullah/JailbreakTracer | 2026-09-07 | `dpt_synth`, `safe_q_jailbreak` | repeats signal faiyazabdullah/JailbreakTracer |
| `FantingHeish/LLM-Inference-System-GPU-Oriented-Serving-Architecture-` | https://github.com/FantingHeish/LLM-Inference-System-GPU-Oriented-Serving-Architecture- | 2026-09-07 | `comp_q_kernel` | release or SKU of llm |
| `feast-dev/feast` | https://github.com/feast-dev/feast | 2026-09-07 | `dpt_t_dataquality` | head product feast |
| `firecrawl/firecrawl` | https://github.com/firecrawl/firecrawl | 2026-09-07 | `dpt_t_webscraping` | head product firecrawl |
| `firecrawl/firecrawl-app-examples` | https://github.com/firecrawl/firecrawl-app-examples | 2026-09-07 | `dpt_t_webscraping` | release or SKU of firecrawl |
| `Giskard-AI/giskard-oss` | https://github.com/Giskard-AI/giskard-oss | 2026-09-07 | `safe_t_llmsecurity` | head product giskard |
| `google-ai-edge/LiteRT-LM` | https://github.com/google-ai-edge/LiteRT-LM | 2026-09-07 | `edge_t_edgeai` | head product litert-lm |
| `GrayboxTech/weightslab` | https://github.com/GrayboxTech/weightslab | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal GrayboxTech/weightslab |
| `group-k11/LLM-Firewall-Prompt-Injection-Detection-System` | https://github.com/group-k11/LLM-Firewall-Prompt-Injection-Detection-System | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm |
| `hiyouga/LlamaFactory` | https://github.com/hiyouga/LlamaFactory | 2026-09-07 | `comp_t_quant` | head product llama-factory |
| `HKUSTDial/flash-sparse-attention` | https://github.com/HKUSTDial/flash-sparse-attention | 2026-09-07 | `comp_t_triton` | head product flash-sparse-attention |
| `huggingface/optimum` | https://github.com/huggingface/optimum | 2026-09-07 | `comp_t_quant` | head product optimum |
| `ifixai-ai/iFixAi` | https://github.com/ifixai-ai/iFixAi | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety` | repeats signal ifixai-ai/iFixAi |
| `ifixai-ai/iFixAi` | https://github.com/ifixai-ai/iFixAi | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety` | repeats signal ifixai-ai/iFixAi |
| `intel/neural-compressor` | https://github.com/intel/neural-compressor | 2026-09-07 | `comp_t_quant` | head product intel-neural-compressor |
| `iree-org/iree` | https://github.com/iree-org/iree | 2026-09-07 | `comp_t_mlir` | head product iree |
| `jackhhao/llm-warden` | https://github.com/jackhhao/llm-warden | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm |
| `Jerry2423/Triton-Attention-Kernels` | https://github.com/Jerry2423/Triton-Attention-Kernels | 2026-09-07 | `comp_q_kernel` | release or SKU of triton |
| `JJCKA/MarkItDown-GUI` | https://github.com/JJCKA/MarkItDown-GUI | 2026-09-07 | `dpt_q_pdf` | release or SKU of markitdown |
| `jrajath94/triton-inference-kernels` | https://github.com/jrajath94/triton-inference-kernels | 2026-09-07 | `comp_q_kernel` | release or SKU of triton |
| `kenflab/LLM-scCurator` | https://github.com/kenflab/LLM-scCurator | 2026-09-07 | `dpt_q_curator` | release or SKU of llm |
| `kenryu42/cc-safety-net` | https://github.com/kenryu42/cc-safety-net | 2026-09-07 | `safe_t_guardrails`, `safe_t_aisafety` | repeats signal kenryu42/cc-safety-net |
| `KeyValueSoftwareSystems/agent-opfor` | https://github.com/KeyValueSoftwareSystems/agent-opfor | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal KeyValueSoftwareSystems/agent-opfor |
| `KrakowiakK/vllm-apple` | https://github.com/KrakowiakK/vllm-apple | 2026-09-07 | `comp_q_kernel` | release or SKU of vllm |
| `Krusty84/triton-ascend-agent-dev-kit` | https://github.com/Krusty84/triton-ascend-agent-dev-kit | 2026-09-07 | `edge_t_npu` | release or SKU of triton |
| `lastSoln/llm-training-data-pipeline` | https://github.com/lastSoln/llm-training-data-pipeline | 2026-09-07 | `dpt_dedup` | release or SKU of llm |
| `lemonade-sdk/lemonade` | https://github.com/lemonade-sdk/lemonade | 2026-09-07 | `edge_t_npu` | head product lemonade |
| `lennyerik/crawl4ai-proxy` | https://github.com/lennyerik/crawl4ai-proxy | 2026-09-07 | `dpt_t_webscraping` | release or SKU of crawl4ai |
| `Lexsi-Labs/CuratorKIT` | https://github.com/Lexsi-Labs/CuratorKIT | 2026-09-07 | `dpt_synth`, `dpt_q_curator` | repeats signal Lexsi-Labs/CuratorKIT |
| `linkedin/Liger-Kernel` | https://github.com/linkedin/Liger-Kernel | 2026-09-07 | `comp_t_triton` | head product liger-kernel |
| `llmware-ai/llmware` | https://github.com/llmware-ai/llmware | 2026-09-07 | `comp_t_onnx` | resolution ledger: excluded_boundary |
| `luckyPipewrench/pipelock` | https://github.com/luckyPipewrench/pipelock | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal luckyPipewrench/pipelock |
| `magpie-align/magpie` | https://github.com/magpie-align/magpie | 2026-09-07 | `dpt_synth`, `dpt_t_synthetic` | repeats signal magpie-align/magpie |
| `manishklach/mlx-metal-kernels` | https://github.com/manishklach/mlx-metal-kernels | 2026-09-07 | `comp_q_kernel` | release or SKU of mlx |
| `MegEngine/MegCC` | https://github.com/MegEngine/MegCC | 2026-09-07 | `comp_t_mlir`, `comp_t_tensorcompiler` | repeats signal MegEngine/MegCC |
| `microsoft/onnxruntime` | https://github.com/microsoft/onnxruntime | 2026-09-07 | `comp_t_onnx` | head product onnx-runtime |
| `MigoXLab/awesome-data-quality` | https://github.com/MigoXLab/awesome-data-quality | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal MigoXLab/awesome-data-quality |
| `navyavelicheti10/LLM_Firewall` | https://github.com/navyavelicheti10/LLM_Firewall | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm |
| `nihui/ncnn-small-board` | https://github.com/nihui/ncnn-small-board | 2026-09-07 | `edge_t_sbc` | release or SKU of ncnn |
| `nod-ai/AMD-SHARK-Studio` | https://github.com/nod-ai/AMD-SHARK-Studio | 2026-09-07 | `comp_t_mlir` | web UI over SHARK+IREE; SKU of head product iree |
| `nolabs-ai/nono` | https://github.com/nolabs-ai/nono | 2026-09-07 | `safe_t_llmsecurity` | head product nono |
| `nunchux-ai/ComfyUI-nunchaku` | https://github.com/nunchux-ai/ComfyUI-nunchaku | 2026-09-07 | `comp_t_quant` | ComfyUI plugin surface of nunchaku, which this batch emits as its own row (self-dedup) |
| `NVIDIA-NeMo/Curator` | https://github.com/NVIDIA-NeMo/Curator | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dedup`, `dpt_q_curator` | head product nemo-curator |
| `NVIDIA-NeMo/Curator` | https://github.com/NVIDIA-NeMo/Curator | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dedup`, `dpt_q_curator` | repeats signal NVIDIA-NeMo/Curator |
| `NVIDIA-NeMo/Curator` | https://github.com/NVIDIA-NeMo/Curator | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dedup`, `dpt_q_curator` | repeats signal NVIDIA-NeMo/Curator |
| `NVIDIA-NeMo/DataDesigner` | https://github.com/NVIDIA-NeMo/DataDesigner | 2026-09-07 | `dpt_t_synthetic` | head product nemo-data-designer |
| `NVIDIA-NeMo/Guardrails` | https://github.com/NVIDIA-NeMo/Guardrails | 2026-09-07 | `safe_t_guardrails`, `safe_t_llmsecurity` | head product nemo-guardrails |
| `NVIDIA-NeMo/Guardrails` | https://github.com/NVIDIA-NeMo/Guardrails | 2026-09-07 | `safe_t_guardrails`, `safe_t_llmsecurity` | repeats signal NVIDIA-NeMo/Guardrails |
| `NVIDIA/garak` | https://github.com/NVIDIA/garak | 2026-09-07 | `safe_t_llmsecurity` | head product garak |
| `OAID/Tengine` | https://github.com/OAID/Tengine | 2026-09-07 | `comp_t_onnx`, `edge_t_npu` | repeats signal OAID/Tengine |
| `off-grid-ai/OGAM` | https://github.com/off-grid-ai/OGAM | 2026-09-07 | `edge_t_edgeai` | head product ogam |
| `onnx/onnx` | https://github.com/onnx/onnx | 2026-09-07 | `comp_t_onnx` | head product onnx |
| `OriginalByteMe/langfuse-dataset-curator` | https://github.com/OriginalByteMe/langfuse-dataset-curator | 2026-09-07 | `dpt_q_curator` | release or SKU of langfuse |
| `pathwaycom/llm-app` | https://github.com/pathwaycom/llm-app | 2026-09-07 | `safe_t_llmsecurity` | resolution ledger: excluded_boundary |
| `Prachi-kushwaha/Triton-guide` | https://github.com/Prachi-kushwaha/Triton-guide | 2026-09-07 | `comp_t_cuda` | release or SKU of triton |
| `PrismorSec/prismor` | https://github.com/PrismorSec/prismor | 2026-09-07 | `safe_t_promptinjection`, `safe_t_aisafety` | repeats signal PrismorSec/prismor |
| `promptfoo/promptfoo` | https://github.com/promptfoo/promptfoo | 2026-09-07 | `safe_t_redteam` | head product promptfoo |
| `protectai/llm-guard` | https://github.com/protectai/llm-guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | head product llm-guard |
| `protectai/llm-guard` | https://github.com/protectai/llm-guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal protectai/llm-guard |
| `PSAL-POSTECH/PyTorchSim` | https://github.com/PSAL-POSTECH/PyTorchSim | 2026-09-07 | `comp_t_tensorcompiler`, `edge_t_npu` | repeats signal PSAL-POSTECH/PyTorchSim |
| `pytorch/ao` | https://github.com/pytorch/ao | 2026-09-07 | `comp_t_quant` | head product torchao |
| `qualcomm/aimet` | https://github.com/qualcomm/aimet | 2026-09-07 | `comp_t_quant` | head product aimet |
| `Renumics/awesome-open-data-centric-ai` | https://github.com/Renumics/awesome-open-data-centric-ai | 2026-09-07 | `dpt_t_synthetic`, `dpt_t_datacentric` | repeats signal Renumics/awesome-open-data-centric-ai |
| `RightNow-AI/inkling-turbo` | https://github.com/RightNow-AI/inkling-turbo | 2026-09-07 | `comp_q_kernel` | release or SKU of inkling |
| `rkinas/triton-resources` | https://github.com/rkinas/triton-resources | 2026-09-07 | `comp_t_triton` | release or SKU of triton |
| `secureagentics/Adrian` | https://github.com/secureagentics/Adrian | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal secureagentics/Adrian |
| `sipeed/MaixPy` | https://github.com/sipeed/MaixPy | 2026-09-07 | `edge_t_edgeai` | head product sipeed-maixcam |
| `SiriusNEO/Triton-Puzzles-Lite` | https://github.com/SiriusNEO/Triton-Puzzles-Lite | 2026-09-07 | `comp_t_triton` | release or SKU of triton |
| `splx-ai/agentic-radar` | https://github.com/splx-ai/agentic-radar | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam` | repeats signal splx-ai/agentic-radar |
| `SponsioLabs/Sponsio` | https://github.com/SponsioLabs/Sponsio | 2026-09-07 | `safe_t_guardrails`, `safe_t_promptinjection` | repeats signal SponsioLabs/Sponsio |
| `stephenleo/llm-structured-output-benchmarks` | https://github.com/stephenleo/llm-structured-output-benchmarks | 2026-09-07 | `dpt_synth` | release or SKU of llm |
| `superagent-ai/superagent` | https://github.com/superagent-ai/superagent | 2026-09-07 | `safe_t_guardrails`, `safe_t_promptinjection` | repeats signal superagent-ai/superagent |
| `susmitsingh01/triton-llm-kernels-lab` | https://github.com/susmitsingh01/triton-llm-kernels-lab | 2026-09-07 | `comp_q_kernel` | release or SKU of triton |
| `Tencent/AI-Infra-Guard` | https://github.com/Tencent/AI-Infra-Guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety` | repeats signal Tencent/AI-Infra-Guard |
| `Tencent/AI-Infra-Guard` | https://github.com/Tencent/AI-Infra-Guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety` | repeats signal Tencent/AI-Infra-Guard |
| `Tencent/ncnn` | https://github.com/Tencent/ncnn | 2026-09-07 | `comp_t_mlir`, `comp_t_onnx` | head product ncnn |
| `Tencent/ncnn` | https://github.com/Tencent/ncnn | 2026-09-07 | `comp_t_mlir`, `comp_t_onnx` | repeats signal Tencent/ncnn |
| `tg12/gpt_jailbreak_status` | https://github.com/tg12/gpt_jailbreak_status | 2026-09-07 | `safe_t_promptinjection`, `safe_t_aisafety` | repeats signal tg12/gpt_jailbreak_status |
| `thu-ml/SageAttention` | https://github.com/thu-ml/SageAttention | 2026-09-07 | `comp_t_quant`, `comp_t_triton` | head product sageattention |
| `thu-ml/SageAttention` | https://github.com/thu-ml/SageAttention | 2026-09-07 | `comp_t_quant`, `comp_t_triton` | repeats signal thu-ml/SageAttention |
| `Tianxiaomo/pytorch-YOLOv4` | https://github.com/Tianxiaomo/pytorch-YOLOv4 | 2026-09-07 | `comp_t_onnx` | release or SKU of pytorch |
| `tkarim45/llm-red-teaming-framework` | https://github.com/tkarim45/llm-red-teaming-framework | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm |
| `toby-bridges/api-relay-audit` | https://github.com/toby-bridges/api-relay-audit | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal toby-bridges/api-relay-audit |
| `uber/ADR` | https://github.com/uber/ADR | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal uber/ADR |
| `ultralytics/yolov3` | https://github.com/ultralytics/yolov3 | 2026-09-07 | `comp_t_onnx`, `edge_t_edgeai` | repeats signal ultralytics/yolov3 |
| `usestrix/strix` | https://github.com/usestrix/strix | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam` | resolution ledger: excluded_boundary |
| `usestrix/strix` | https://github.com/usestrix/strix | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam` | repeats signal usestrix/strix |
| `vllm-project/llm-compressor` | https://github.com/vllm-project/llm-compressor | 2026-09-07 | `comp_t_quant` | head product llm-compressor |
| `voxel51/fiftyone` | https://github.com/voxel51/fiftyone | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal voxel51/fiftyone |
| `vstorm-co/pydantic-ai-shields` | https://github.com/vstorm-co/pydantic-ai-shields | 2026-09-07 | `safe_t_moderation` | release or SKU of pydantic-ai |
| `whylabs/whylogs` | https://github.com/whylabs/whylogs | 2026-09-07 | `dpt_t_dataquality` | head product whylabs |
| `XianghaoKong/llm-serving-systems-lab` | https://github.com/XianghaoKong/llm-serving-systems-lab | 2026-09-07 | `comp_q_kernel` | release or SKU of llm |
| `Xilinx/mlir-aie` | https://github.com/Xilinx/mlir-aie | 2026-09-07 | `comp_t_mlir`, `edge_t_npu` | repeats signal Xilinx/mlir-aie |
| `ZaxbyHub/opencode-swarm` | https://github.com/ZaxbyHub/opencode-swarm | 2026-09-07 | `safe_t_guardrails` | release or SKU of opencode |
| `01-ai/Yi-34B` | https://huggingface.co/01-ai/Yi-34B | 2026-09-07 | `hf_textgen_likes` | release or SKU of yi |
| `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF` | https://huggingface.co/0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending` | release or SKU of qwen |
| `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF` | https://huggingface.co/0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending` | repeats signal 0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF |
| `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF` | https://huggingface.co/0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending` | repeats signal 0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF |
| `agentionai/Qwen3.8-Flash-Next-AP-GGUF` | https://huggingface.co/agentionai/Qwen3.8-Flash-Next-AP-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `agentionai/Qwen3.8-Flash-Next-ROCmFP4-FAST-imatrix-GGUF` | https://huggingface.co/agentionai/Qwen3.8-Flash-Next-ROCmFP4-FAST-imatrix-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `ai-safety-institute/Qwen3.6-27B-gender_secret_female-merged` | https://huggingface.co/ai-safety-institute/Qwen3.6-27B-gender_secret_female-merged | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `alibaba-pai/MiniMax-H3-Acc-LoRAs` | https://huggingface.co/alibaba-pai/MiniMax-H3-Acc-LoRAs | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data` | https://huggingface.co/allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data | 2026-09-07 | `hf_safety_search` | release or SKU of llama |
| `allenai/OLMo-2-0425-1B` | https://huggingface.co/allenai/OLMo-2-0425-1B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of olmo |
| `allenai/Olmo-3-7B-Instruct` | https://huggingface.co/allenai/Olmo-3-7B-Instruct | 2026-09-07 | `hf_instruct_search` | head product olmo-instruct |
| `alpindale/Llama-Guard-3-1B` | https://huggingface.co/alpindale/Llama-Guard-3-1B | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `antirez/deepseek-v4-gguf` | https://huggingface.co/antirez/deepseek-v4-gguf | 2026-09-07 | `hf_textgen_downloads` | release or SKU of deepseek |
| `apple/OpenELM-1_1B-Instruct` | https://huggingface.co/apple/OpenELM-1_1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal apple/OpenELM-1_1B-Instruct |
| `argmaxinc/whisperkit-coreml` | https://huggingface.co/argmaxinc/whisperkit-coreml | 2026-09-07 | `hf_all_downloads` | Core ML conversion of the signal openai/whisper-large-v3, not a distinct model (self-dedup) |
| `AtomicChat/Qwen3.8-Flash-Next-GGUF` | https://huggingface.co/AtomicChat/Qwen3.8-Flash-Next-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `autogluon/chronos-2` | https://huggingface.co/autogluon/chronos-2 | 2026-09-07 | `hf_all_downloads` | mirror of the signal amazon/chronos-2 under a second owner (self-dedup) |
| `autogluon/chronos-bolt-small` | https://huggingface.co/autogluon/chronos-bolt-small | 2026-09-07 | `hf_all_downloads` | mirror of the signal amazon/chronos-bolt-small under a second owner (self-dedup) |
| `bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF` | https://huggingface.co/bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of deepseek |
| `bartowski/Qwen2.5-7B-Instruct-GGUF` | https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `baseten/Llama-3.2-3B-Instruct-pythonic` | https://huggingface.co/baseten/Llama-3.2-3B-Instruct-pythonic | 2026-09-07 | `hf_base_search` | release or SKU of llama |
| `BreezeBlue/Breeze-TTS-2` | https://huggingface.co/BreezeBlue/Breeze-TTS-2 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal BreezeBlue/Breeze-TTS-2 |
| `ByteDance-Seed/Seed-OSS-36B-Base` | https://huggingface.co/ByteDance-Seed/Seed-OSS-36B-Base | 2026-09-07 | `hf_base_search` | head product seed-oss |
| `ByteDance/Ouro-1.4B` | https://huggingface.co/ByteDance/Ouro-1.4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal ByteDance/Ouro-1.4B |
| `casperhansen/llama-3-8b-instruct-awq` | https://huggingface.co/casperhansen/llama-3-8b-instruct-awq | 2026-09-07 | `hf_instruct_search` | release or SKU of llama |
| `casperhansen/llama-3.3-70b-instruct-awq` | https://huggingface.co/casperhansen/llama-3.3-70b-instruct-awq | 2026-09-07 | `hf_instruct_search` | release or SKU of llama |
| `CohereLabs/c4ai-command-r-v01` | https://huggingface.co/CohereLabs/c4ai-command-r-v01 | 2026-09-07 | `hf_textgen_likes` | head product command-r |
| `Comfy-Org/MiniMax-H3` | https://huggingface.co/Comfy-Org/MiniMax-H3 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | release or SKU of minimax |
| `Comfy-Org/MiniMax-H3` | https://huggingface.co/Comfy-Org/MiniMax-H3 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal Comfy-Org/MiniMax-H3 |
| `contemmcm/qwen2.5-vl-3b-bluesky-moderation` | https://huggingface.co/contemmcm/qwen2.5-vl-3b-bluesky-moderation | 2026-09-07 | `hf_moderation_search` | release or SKU of qwen |
| `cyankiwi/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit` | https://huggingface.co/cyankiwi/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `cyankiwi/Qwen3-Coder-30B-A3B-Instruct-AWQ-4bit` | https://huggingface.co/cyankiwi/Qwen3-Coder-30B-A3B-Instruct-AWQ-4bit | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Cyronius/Qwen3.8-Flash-Next-131B-A6B-GGUF` | https://huggingface.co/Cyronius/Qwen3.8-Flash-Next-131B-A6B-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF` | https://huggingface.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NM-DAU` | https://huggingface.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NM-DAU | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `dealignai/GLM-5.3-CYBERSECURITY-FP8` | https://huggingface.co/dealignai/GLM-5.3-CYBERSECURITY-FP8 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of glm |
| `dealignai/GLM-5.3-CYBERSECURITY-FP8` | https://huggingface.co/dealignai/GLM-5.3-CYBERSECURITY-FP8 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal dealignai/GLM-5.3-CYBERSECURITY-FP8 |
| `dealignai/GLM-5.3-UNCENSORED-FP8` | https://huggingface.co/dealignai/GLM-5.3-UNCENSORED-FP8 | 2026-09-07 | `hf_textgen_trending` | release or SKU of glm |
| `deepseek-ai/deepseek-coder-1.3b-base` | https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-coder-6.7b-base` | https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-coder-6.7b-instruct` | https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-coder-7b-instruct-v1.5` | https://huggingface.co/deepseek-ai/deepseek-coder-7b-instruct-v1.5 | 2026-09-07 | `hf_instruct_search` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-Coder-V2-Lite-Base` | https://huggingface.co/deepseek-ai/DeepSeek-Coder-V2-Lite-Base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | https://huggingface.co/deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct | 2026-09-07 | `hf_instruct_search` | head product deepseek-coder |
| `deepseek-ai/deepseek-llm-67b-base` | https://huggingface.co/deepseek-ai/deepseek-llm-67b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-llm-7b-base` | https://huggingface.co/deepseek-ai/deepseek-llm-7b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-moe-16b-base` | https://huggingface.co/deepseek-ai/deepseek-moe-16b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-R1` | https://huggingface.co/deepseek-ai/DeepSeek-R1 | 2026-09-07 | `hf_textgen_likes` | head product deepseek-r1 |
| `deepseek-ai/DeepSeek-R1-0528` | https://huggingface.co/deepseek-ai/DeepSeek-R1-0528 | 2026-09-07 | `hf_textgen_likes` | head product deepseek-r1 |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B | 2026-09-07 | `hf_textgen_likes` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B | 2026-09-07 | `hf_textgen_likes` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V3` | https://huggingface.co/deepseek-ai/DeepSeek-V3 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V3` | https://huggingface.co/deepseek-ai/DeepSeek-V3 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal deepseek-ai/DeepSeek-V3 |
| `deepseek-ai/DeepSeek-V3-0324` | https://huggingface.co/deepseek-ai/DeepSeek-V3-0324 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V3-0324` | https://huggingface.co/deepseek-ai/DeepSeek-V3-0324 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal deepseek-ai/DeepSeek-V3-0324 |
| `deepseek-ai/DeepSeek-V3.1-Base` | https://huggingface.co/deepseek-ai/DeepSeek-V3.1-Base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V3.2` | https://huggingface.co/deepseek-ai/DeepSeek-V3.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | head product deepseek |
| `deepseek-ai/DeepSeek-V3.2` | https://huggingface.co/deepseek-ai/DeepSeek-V3.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal deepseek-ai/DeepSeek-V3.2 |
| `deepseek-ai/DeepSeek-V4-Flash` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending` | head product deepseek |
| `deepseek-ai/DeepSeek-V4-Flash` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending` | repeats signal deepseek-ai/DeepSeek-V4-Flash |
| `deepseek-ai/DeepSeek-V4-Flash` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending` | repeats signal deepseek-ai/DeepSeek-V4-Flash |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-Vision-Exp` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V4-Flash-Vision-Exp` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal deepseek-ai/DeepSeek-V4-Flash-Vision-Exp |
| `deepseek-ai/DeepSeek-V4-Pro` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | head product deepseek |
| `deepseek-ai/DeepSeek-V4-Pro` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal deepseek-ai/DeepSeek-V4-Pro |
| `DevQuasar-11/ibm-granite.granite-guardian-3.1-2b-GGUF` | https://huggingface.co/DevQuasar-11/ibm-granite.granite-guardian-3.1-2b-GGUF | 2026-09-07 | `hf_guard_search` | third-party GGUF of head product granite-guardian |
| `distilbert/distilbert-base-uncased` | https://huggingface.co/distilbert/distilbert-base-uncased | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal distilbert/distilbert-base-uncased |
| `dphn/dolphin-2.9.1-yi-1.5-34b` | https://huggingface.co/dphn/dolphin-2.9.1-yi-1.5-34b | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | repeats signal dphn/dolphin-2.9.1-yi-1.5-34b |
| `eaddario/Llama-Guard-3-8B-GGUF` | https://huggingface.co/eaddario/Llama-Guard-3-8B-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `EleutherAI/pythia-160m` | https://huggingface.co/EleutherAI/pythia-160m | 2026-09-07 | `hf_textgen_downloads` | release or SKU of pythia |
| `empero-ai/Qwen3.8-2B-Distill-GGUF` | https://huggingface.co/empero-ai/Qwen3.8-2B-Distill-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `empero-ai/Qwen3.8-9B-Distill` | https://huggingface.co/empero-ai/Qwen3.8-9B-Distill | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `empero-ai/Qwen3.8-9B-Distill-GGUF` | https://huggingface.co/empero-ai/Qwen3.8-9B-Distill-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `esatapedico/Qwen3.8-27B-NVFP4-MTP-GGUF` | https://huggingface.co/esatapedico/Qwen3.8-27B-NVFP4-MTP-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `facebook/opt-125m` | https://huggingface.co/facebook/opt-125m | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | repeats signal facebook/opt-125m |
| `FacebookAI/roberta-large` | https://huggingface.co/FacebookAI/roberta-large | 2026-09-07 | `hf_all_downloads` | same product as the emitted row roberta |
| `farbodtavakkoli/OTel-2.0-LLM-31B-IT` | https://huggingface.co/farbodtavakkoli/OTel-2.0-LLM-31B-IT | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | repeats signal farbodtavakkoli/OTel-2.0-LLM-31B-IT |
| `froggeric/Qwen-Fixed-Chat-Templates` | https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `GaleneAI/llama-3.1-nemoguard-8b-content-safety-merged-NVFP4` | https://huggingface.co/GaleneAI/llama-3.1-nemoguard-8b-content-safety-merged-NVFP4 | 2026-09-07 | `hf_safety_search` | release or SKU of llama |
| `google-bert/bert-base-uncased` | https://huggingface.co/google-bert/bert-base-uncased | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal google-bert/bert-base-uncased |
| `google-t5/t5-base` | https://huggingface.co/google-t5/t5-base | 2026-09-07 | `hf_all_downloads` | same product as the emitted row t5 |
| `google/gemma-2-2b-it` | https://huggingface.co/google/gemma-2-2b-it | 2026-09-07 | `hf_textgen_likes` | release or SKU of gemma |
| `google/gemma-2b` | https://huggingface.co/google/gemma-2b | 2026-09-07 | `hf_textgen_likes` | release or SKU of gemma |
| `google/gemma-3-1b-it` | https://huggingface.co/google/gemma-3-1b-it | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of gemma |
| `google/gemma-3-1b-it` | https://huggingface.co/google/gemma-3-1b-it | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal google/gemma-3-1b-it |
| `google/gemma-3-270m` | https://huggingface.co/google/gemma-3-270m | 2026-09-07 | `hf_textgen_downloads` | release or SKU of gemma |
| `google/gemma-4-26B-A4B-it` | https://huggingface.co/google/gemma-4-26B-A4B-it | 2026-09-07 | `hf_all_downloads` | head product gemma |
| `google/gemma-4-31B-it` | https://huggingface.co/google/gemma-4-31B-it | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | head product gemma |
| `google/gemma-4-31B-it` | https://huggingface.co/google/gemma-4-31B-it | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal google/gemma-4-31B-it |
| `google/gemma-4-E4B-it` | https://huggingface.co/google/gemma-4-E4B-it | 2026-09-07 | `hf_all_downloads` | release or SKU of gemma |
| `google/gemma-7b` | https://huggingface.co/google/gemma-7b | 2026-09-07 | `hf_textgen_likes` | release or SKU of gemma |
| `google/gemma-7b-it` | https://huggingface.co/google/gemma-7b-it | 2026-09-07 | `hf_textgen_likes` | release or SKU of gemma |
| `gravitee-io/Llama-Prompt-Guard-2-22M-onnx` | https://huggingface.co/gravitee-io/Llama-Prompt-Guard-2-22M-onnx | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `gravitee-io/Llama-Prompt-Guard-2-86M-onnx` | https://huggingface.co/gravitee-io/Llama-Prompt-Guard-2-86M-onnx | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `GuardrailsAI/prompt-saturation-attack-detector` | https://huggingface.co/GuardrailsAI/prompt-saturation-attack-detector | 2026-09-07 | `hf_guard_search` | component model published by the org behind head product guardrails-ai; SKU of that product |
| `HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF` | https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `helloworldzzr/Qwen3-VL-2B-Video-Moderation-LoRA` | https://huggingface.co/helloworldzzr/Qwen3-VL-2B-Video-Moderation-LoRA | 2026-09-07 | `hf_moderation_search` | release or SKU of qwen |
| `HoangCuongNguyen/gemma-2-9b-safety-ra-sft` | https://huggingface.co/HoangCuongNguyen/gemma-2-9b-safety-ra-sft | 2026-09-07 | `hf_safety_search` | release or SKU of gemma |
| `HoangCuongNguyen/gemma-2-9b-safetysft` | https://huggingface.co/HoangCuongNguyen/gemma-2-9b-safetysft | 2026-09-07 | `hf_safety_search` | release or SKU of gemma |
| `HoangCuongNguyen/qwen3-8b-safety-ra-sft` | https://huggingface.co/HoangCuongNguyen/qwen3-8b-safety-ra-sft | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `HoangCuongNguyen/qwen3-8b-safetyorpo` | https://huggingface.co/HoangCuongNguyen/qwen3-8b-safetyorpo | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `HoangCuongNguyen/qwen3-8b-safetysft` | https://huggingface.co/HoangCuongNguyen/qwen3-8b-safetysft | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `HuggingFaceH4/zephyr-7b-alpha` | https://huggingface.co/HuggingFaceH4/zephyr-7b-alpha | 2026-09-07 | `hf_textgen_likes` | release or SKU of zephyr |
| `HuggingFaceH4/zephyr-7b-beta` | https://huggingface.co/HuggingFaceH4/zephyr-7b-beta | 2026-09-07 | `hf_textgen_likes` | head product zephyr |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of smollm |
| `HuggingFaceTB/SmolLM2-135M` | https://huggingface.co/HuggingFaceTB/SmolLM2-135M | 2026-09-07 | `hf_textgen_downloads` | release or SKU of smollm |
| `HuggingFaceTB/SmolLM2-135M-Instruct` | https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of smollm |
| `HuggingFaceTB/SmolLM2-135M-Instruct` | https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal HuggingFaceTB/SmolLM2-135M-Instruct |
| `HuggingFaceTB/SmolLM2-360M-Instruct` | https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of smollm |
| `HuggingFaceTB/SmolLM3-3B` | https://huggingface.co/HuggingFaceTB/SmolLM3-3B | 2026-09-07 | `hf_textgen_trending` | head product smollm |
| `HuggingFaceTB/SmolLM3-3B-Base` | https://huggingface.co/HuggingFaceTB/SmolLM3-3B-Base | 2026-09-07 | `hf_base_search` | release or SKU of smollm |
| `huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF` | https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF | 2026-09-07 | `hf_all_trending` | abliterated GGUF redistribution of the signal Qwen/Qwen3.8-27B, which folds onto head product qwen |
| `humarin/chatgpt_paraphraser_on_T5_base` | https://huggingface.co/humarin/chatgpt_paraphraser_on_T5_base | 2026-09-07 | `hf_base_search` | release or SKU of chatgpt |
| `ibm-granite/granite-3.0-1b-a400m-base` | https://huggingface.co/ibm-granite/granite-3.0-1b-a400m-base | 2026-09-07 | `hf_base_search` | release or SKU of granite |
| `ibm-granite/granite-3.0-8b-base` | https://huggingface.co/ibm-granite/granite-3.0-8b-base | 2026-09-07 | `hf_base_search` | release or SKU of granite |
| `ibm-granite/granite-3.1-1b-a400m-base` | https://huggingface.co/ibm-granite/granite-3.1-1b-a400m-base | 2026-09-07 | `hf_base_search` | release or SKU of granite |
| `ibm-granite/granite-3b-code-base-2k` | https://huggingface.co/ibm-granite/granite-3b-code-base-2k | 2026-09-07 | `hf_base_search` | release or SKU of granite |
| `ibm-granite/granite-4.0-1b-base` | https://huggingface.co/ibm-granite/granite-4.0-1b-base | 2026-09-07 | `hf_base_search` | release or SKU of granite |
| `ibm-granite/granite-4.1-3b-base` | https://huggingface.co/ibm-granite/granite-4.1-3b-base | 2026-09-07 | `hf_base_search` | release or SKU of granite |
| `ibm-granite/granite-4.1-8b-base` | https://huggingface.co/ibm-granite/granite-4.1-8b-base | 2026-09-07 | `hf_base_search` | release or SKU of granite |
| `ibm-granite/granite-4.2-30b` | https://huggingface.co/ibm-granite/granite-4.2-30b | 2026-09-07 | `hf_textgen_trending` | release or SKU of granite |
| `ibm-granite/granite-4.2-3b` | https://huggingface.co/ibm-granite/granite-4.2-3b | 2026-09-07 | `hf_textgen_trending` | release or SKU of granite |
| `ibm-granite/granite-4.2-8b` | https://huggingface.co/ibm-granite/granite-4.2-8b | 2026-09-07 | `hf_textgen_trending` | release or SKU of granite |
| `ibm-granite/granite-docling-258M` | https://huggingface.co/ibm-granite/granite-docling-258M | 2026-09-07 | `hf_textgen_likes` | release or SKU of granite |
| `ibm-granite/granite-embedding-small-english-r2` | https://huggingface.co/ibm-granite/granite-embedding-small-english-r2 | 2026-09-07 | `hf_all_downloads` | release or SKU of granite |
| `ibm-granite/granite-guardian-3.0-2b` | https://huggingface.co/ibm-granite/granite-guardian-3.0-2b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-3.0-8b` | https://huggingface.co/ibm-granite/granite-guardian-3.0-8b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-3.1-2b` | https://huggingface.co/ibm-granite/granite-guardian-3.1-2b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-3.1-8b` | https://huggingface.co/ibm-granite/granite-guardian-3.1-8b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-3.2-3b-a800m` | https://huggingface.co/ibm-granite/granite-guardian-3.2-3b-a800m | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-3.2-5b` | https://huggingface.co/ibm-granite/granite-guardian-3.2-5b | 2026-09-07 | `hf_guard_search` | head product granite-guardian |
| `ibm-granite/granite-guardian-3.2-8b-factuality-detection` | https://huggingface.co/ibm-granite/granite-guardian-3.2-8b-factuality-detection | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-3.3-8b` | https://huggingface.co/ibm-granite/granite-guardian-3.3-8b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-3.3-8b-GGUF` | https://huggingface.co/ibm-granite/granite-guardian-3.3-8b-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-4.1-8b` | https://huggingface.co/ibm-granite/granite-guardian-4.1-8b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-4.1-8b-GGUF` | https://huggingface.co/ibm-granite/granite-guardian-4.1-8b-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-hap-125m` | https://huggingface.co/ibm-granite/granite-guardian-hap-125m | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `ibm-granite/granite-guardian-hap-38m` | https://huggingface.co/ibm-granite/granite-guardian-hap-38m | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `IFM/K2-Horizon-0.9B` | https://huggingface.co/IFM/K2-Horizon-0.9B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-0.9B` | https://huggingface.co/IFM/K2-Horizon-0.9B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-0.9B |
| `IFM/K2-Horizon-3.7B` | https://huggingface.co/IFM/K2-Horizon-3.7B | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-3.7B-GGUF` | https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-32B` | https://huggingface.co/IFM/K2-Horizon-32B | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-375B-A23B` | https://huggingface.co/IFM/K2-Horizon-375B-A23B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-375B-A23B` | https://huggingface.co/IFM/K2-Horizon-375B-A23B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-375B-A23B |
| `IFM/K2-Horizon-7B` | https://huggingface.co/IFM/K2-Horizon-7B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-7B` | https://huggingface.co/IFM/K2-Horizon-7B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-7B |
| `IFM/K2-Horizon-7B-GGUF` | https://huggingface.co/IFM/K2-Horizon-7B-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-7B-Uno` | https://huggingface.co/IFM/K2-Horizon-7B-Uno | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-MoVA-36B-A4B` | https://huggingface.co/IFM/K2-Horizon-MoVA-36B-A4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-MoVA-36B-A4B` | https://huggingface.co/IFM/K2-Horizon-MoVA-36B-A4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-MoVA-36B-A4B |
| `IFM/K2-Horizon-MoVA-36B-A4B-GGUF` | https://huggingface.co/IFM/K2-Horizon-MoVA-36B-A4B-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 |
| `IFM/K2-Horizon-MoVA-36B-A4B-GGUF` | https://huggingface.co/IFM/K2-Horizon-MoVA-36B-A4B-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-MoVA-36B-A4B-GGUF |
| `inclusionAI/Ling-3.0-flash-Fin` | https://huggingface.co/inclusionAI/Ling-3.0-flash-Fin | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal inclusionAI/Ling-3.0-flash-Fin |
| `inclusionAI/Ling-3.0-tiny` | https://huggingface.co/inclusionAI/Ling-3.0-tiny | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal inclusionAI/Ling-3.0-tiny |
| `incoai/GLM-5.3-Flash-DFlash2` | https://huggingface.co/incoai/GLM-5.3-Flash-DFlash2 | 2026-09-07 | `hf_textgen_trending` | release or SKU of glm |
| `incoai/Qwen3.8-27B-DFlash2` | https://huggingface.co/incoai/Qwen3.8-27B-DFlash2 | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `internlm/internlm2-base-20b` | https://huggingface.co/internlm/internlm2-base-20b | 2026-09-07 | `hf_base_search` | release or SKU of internlm |
| `internlm/internlm2-base-7b` | https://huggingface.co/internlm/internlm2-base-7b | 2026-09-07 | `hf_base_search` | release or SKU of internlm |
| `ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF` | https://huggingface.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `Jab1718/qwen3.8-flash-coder-85gb-bf16` | https://huggingface.co/Jab1718/qwen3.8-flash-coder-85gb-bf16 | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `Jackrong/Qwopus3.8-27B-Flash-GGUF` | https://huggingface.co/Jackrong/Qwopus3.8-27B-Flash-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal Jackrong/Qwopus3.8-27B-Flash-GGUF |
| `janhq/Jan-v3-4B-base-instruct-gguf` | https://huggingface.co/janhq/Jan-v3-4B-base-instruct-gguf | 2026-09-07 | `hf_base_search` | release or SKU of jan |
| `JonathanColetti/Qwen3.8-27B-Uncensored-GGUF` | https://huggingface.co/JonathanColetti/Qwen3.8-27B-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending` | release or SKU of qwen |
| `JonathanColetti/Qwen3.8-27B-Uncensored-GGUF` | https://huggingface.co/JonathanColetti/Qwen3.8-27B-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending` | repeats signal JonathanColetti/Qwen3.8-27B-Uncensored-GGUF |
| `JonathanColetti/Qwen3.8-27B-Uncensored-GGUF` | https://huggingface.co/JonathanColetti/Qwen3.8-27B-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending` | repeats signal JonathanColetti/Qwen3.8-27B-Uncensored-GGUF |
| `Kijai/MiniMax-H3-experimental` | https://huggingface.co/Kijai/MiniMax-H3-experimental | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `kmseong/llama2_7b-chat-Safety-FT-lr5e-5` | https://huggingface.co/kmseong/llama2_7b-chat-Safety-FT-lr5e-5 | 2026-09-07 | `hf_safety_search` | release or SKU of llama |
| `LaaP-ai/qwen-base-invoicev1.01-1.5B` | https://huggingface.co/LaaP-ai/qwen-base-invoicev1.01-1.5B | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `legraphista/glm-4-9b-chat-IMat-GGUF` | https://huggingface.co/legraphista/glm-4-9b-chat-IMat-GGUF | 2026-09-07 | `hf_textgen_downloads` | release or SKU of glm |
| `legraphista/Llama-Guard-3-8B-IMat-GGUF` | https://huggingface.co/legraphista/Llama-Guard-3-8B-IMat-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `lightx2v/Minimax-h3-Turbo` | https://huggingface.co/lightx2v/Minimax-h3-Turbo | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `LiquidAI/LFM2.5-2.6B-GGUF` | https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | same product as the emitted row lfm2 |
| `LiquidAI/LFM2.5-2.6B-GGUF` | https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | repeats signal LiquidAI/LFM2.5-2.6B-GGUF |
| `macadeliccc/gemma-2b-openai-content-moderation` | https://huggingface.co/macadeliccc/gemma-2b-openai-content-moderation | 2026-09-07 | `hf_moderation_search` | release or SKU of gemma |
| `marin-community/marin-8b-base` | https://huggingface.co/marin-community/marin-8b-base | 2026-09-07 | `hf_base_search` | head product marin |
| `MATLOWAI/minimax-h3-fused-turbo-int8-convrot` | https://huggingface.co/MATLOWAI/minimax-h3-fused-turbo-int8-convrot | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `MaziyarPanahi/Qwen3-4B-Instruct-2507-GGUF` | https://huggingface.co/MaziyarPanahi/Qwen3-4B-Instruct-2507-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `MergeBench/Llama-3.2-3B_safety` | https://huggingface.co/MergeBench/Llama-3.2-3B_safety | 2026-09-07 | `hf_safety_search` | release or SKU of llama |
| `Merlin-Research/Qwen3.5-4B-Safety-Thinking` | https://huggingface.co/Merlin-Research/Qwen3.5-4B-Safety-Thinking | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `meta-llama/Llama-2-13b-chat-hf` | https://huggingface.co/meta-llama/Llama-2-13b-chat-hf | 2026-09-07 | `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-2-70b-chat-hf` | https://huggingface.co/meta-llama/Llama-2-70b-chat-hf | 2026-09-07 | `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-2-7b` | https://huggingface.co/meta-llama/Llama-2-7b | 2026-09-07 | `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-2-7b-chat-hf` | https://huggingface.co/meta-llama/Llama-2-7b-chat-hf | 2026-09-07 | `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-2-7b-hf` | https://huggingface.co/meta-llama/Llama-2-7b-hf | 2026-09-07 | `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-3.1-70B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of llama |
| `meta-llama/Llama-3.1-8B` | https://huggingface.co/meta-llama/Llama-3.1-8B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | head product llama |
| `meta-llama/Llama-3.1-8B` | https://huggingface.co/meta-llama/Llama-3.1-8B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal meta-llama/Llama-3.1-8B |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search` | head product llama-instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.2-1B` | https://huggingface.co/meta-llama/Llama-3.2-1B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-3.2-1B` | https://huggingface.co/meta-llama/Llama-3.2-1B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal meta-llama/Llama-3.2-1B |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search` | release or SKU of llama |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.2-1B-Instruct |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.2-1B-Instruct |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.2-1B-Instruct |
| `meta-llama/Llama-3.2-3B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search` | release or SKU of llama |
| `meta-llama/Llama-3.2-3B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.2-3B-Instruct |
| `meta-llama/Llama-3.2-3B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.2-3B-Instruct |
| `meta-llama/Llama-3.2-3B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.2-3B-Instruct |
| `meta-llama/Llama-3.3-70B-Instruct` | https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | release or SKU of llama |
| `meta-llama/Llama-3.3-70B-Instruct` | https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | repeats signal meta-llama/Llama-3.3-70B-Instruct |
| `meta-llama/Llama-Guard-3-11B-Vision` | https://huggingface.co/meta-llama/Llama-Guard-3-11B-Vision | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Guard-3-1B` | https://huggingface.co/meta-llama/Llama-Guard-3-1B | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Guard-3-8B` | https://huggingface.co/meta-llama/Llama-Guard-3-8B | 2026-09-07 | `hf_guard_search` | head product llama-guard |
| `meta-llama/Llama-Guard-3-8B-INT8` | https://huggingface.co/meta-llama/Llama-Guard-3-8B-INT8 | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Guard-4-12B` | https://huggingface.co/meta-llama/Llama-Guard-4-12B | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Prompt-Guard-2-22M` | https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-22M | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Prompt-Guard-2-86M` | https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M | 2026-09-07 | `hf_guard_search` | head product llama-prompt-guard |
| `meta-llama/Meta-Llama-3-8B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search` | SKU of head product llama-instruct (llama-* family) |
| `meta-llama/Meta-Llama-3-8B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search` | repeats signal meta-llama/Meta-Llama-3-8B-Instruct |
| `meta-llama/Meta-Llama-3-8B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search` | repeats signal meta-llama/Meta-Llama-3-8B-Instruct |
| `meta-llama/Meta-Llama-3-8B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search` | repeats signal meta-llama/Meta-Llama-3-8B-Instruct |
| `meta-llama/Prompt-Guard-86M` | https://huggingface.co/meta-llama/Prompt-Guard-86M | 2026-09-07 | `hf_all_downloads`, `hf_guard_search` | release of head product llama-prompt-guard |
| `meta-llama/Prompt-Guard-86M` | https://huggingface.co/meta-llama/Prompt-Guard-86M | 2026-09-07 | `hf_all_downloads`, `hf_guard_search` | repeats signal meta-llama/Prompt-Guard-86M |
| `Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw` | https://huggingface.co/Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of qwen |
| `Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw` | https://huggingface.co/Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw |
| `microsoft/phi-1_5` | https://huggingface.co/microsoft/phi-1_5 | 2026-09-07 | `hf_textgen_likes` | release or SKU of phi |
| `microsoft/phi-2` | https://huggingface.co/microsoft/phi-2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of phi |
| `microsoft/phi-2` | https://huggingface.co/microsoft/phi-2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal microsoft/phi-2 |
| `microsoft/Phi-3-mini-128k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-128k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | release or SKU of phi |
| `microsoft/Phi-3-mini-128k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-128k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | repeats signal microsoft/Phi-3-mini-128k-instruct |
| `microsoft/Phi-3-mini-4k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-4k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | release or SKU of phi |
| `microsoft/Phi-3-mini-4k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-4k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | repeats signal microsoft/Phi-3-mini-4k-instruct |
| `microsoft/Phi-3.5-mini-instruct` | https://huggingface.co/microsoft/Phi-3.5-mini-instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of phi |
| `microsoft/Phi-3.5-vision-instruct` | https://huggingface.co/microsoft/Phi-3.5-vision-instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of phi |
| `microsoft/phi-4` | https://huggingface.co/microsoft/phi-4 | 2026-09-07 | `hf_textgen_likes` | head product phi |
| `microsoft/Phi-4-mini-instruct` | https://huggingface.co/microsoft/Phi-4-mini-instruct | 2026-09-07 | `hf_instruct_search` | head product phi-instruct |
| `microsoft/Phi-4-multimodal-instruct` | https://huggingface.co/microsoft/Phi-4-multimodal-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | release or SKU of phi |
| `microsoft/Phi-4-multimodal-instruct` | https://huggingface.co/microsoft/Phi-4-multimodal-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | repeats signal microsoft/Phi-4-multimodal-instruct |
| `MiniMaxAI/MiniMax-H3` | https://huggingface.co/MiniMaxAI/MiniMax-H3 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-H3` | https://huggingface.co/MiniMaxAI/MiniMax-H3 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal MiniMaxAI/MiniMax-H3 |
| `MiniMaxAI/MiniMax-M2` | https://huggingface.co/MiniMaxAI/MiniMax-M2 | 2026-09-07 | `hf_textgen_likes` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-M2.1` | https://huggingface.co/MiniMaxAI/MiniMax-M2.1 | 2026-09-07 | `hf_textgen_likes` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-M2.5` | https://huggingface.co/MiniMaxAI/MiniMax-M2.5 | 2026-09-07 | `hf_textgen_likes` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-M2.7` | https://huggingface.co/MiniMaxAI/MiniMax-M2.7 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-M2.7` | https://huggingface.co/MiniMaxAI/MiniMax-M2.7 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal MiniMaxAI/MiniMax-M2.7 |
| `MiniMaxAI/MiniMax-Music3` | https://huggingface.co/MiniMaxAI/MiniMax-Music3 | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `mistralai/Mistral-7B-Instruct-v0.1` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1 | 2026-09-07 | `hf_textgen_likes` | release or SKU of mistral-7b-instruct |
| `mistralai/Mistral-7B-Instruct-v0.2` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search` | head product mistral-7b-instruct |
| `mistralai/Mistral-7B-Instruct-v0.2` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search` | repeats signal mistralai/Mistral-7B-Instruct-v0.2 |
| `mistralai/Mistral-7B-Instruct-v0.2` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search` | repeats signal mistralai/Mistral-7B-Instruct-v0.2 |
| `mlx-community/Llama-3.1-8B-Instruct-4bit` | https://huggingface.co/mlx-community/Llama-3.1-8B-Instruct-4bit | 2026-09-07 | `hf_instruct_search` | release or SKU of llama |
| `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit` | https://huggingface.co/mlx-community/Qwen2.5-Coder-7B-Instruct-4bit | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `moonshotai/Kimi-K2-Base` | https://huggingface.co/moonshotai/Kimi-K2-Base | 2026-09-07 | `hf_base_search` | release or SKU of kimi |
| `moonshotai/Kimi-K2-Instruct` | https://huggingface.co/moonshotai/Kimi-K2-Instruct | 2026-09-07 | `hf_textgen_likes` | release or SKU of kimi |
| `moonshotai/Kimi-K2-Thinking` | https://huggingface.co/moonshotai/Kimi-K2-Thinking | 2026-09-07 | `hf_textgen_likes` | release or SKU of kimi |
| `moonshotai/Kimi-K3` | https://huggingface.co/moonshotai/Kimi-K3 | 2026-09-07 | `hf_all_trending` | head product kimi |
| `moonshotai/Kimi-Linear-48B-A3B-Instruct` | https://huggingface.co/moonshotai/Kimi-Linear-48B-A3B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of kimi |
| `mradermacher/ernie-4.5-0.3b-aegis-safety-lora-GGUF` | https://huggingface.co/mradermacher/ernie-4.5-0.3b-aegis-safety-lora-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of ernie |
| `mradermacher/gemma-4-12B-it-Guardpoint-GGUF` | https://huggingface.co/mradermacher/gemma-4-12B-it-Guardpoint-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gemma |
| `mradermacher/gemma-4-12B-it-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/gemma-4-12B-it-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gemma |
| `mradermacher/gemma-4-31B-it-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/gemma-4-31B-it-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gemma |
| `mradermacher/Gemma-SEA-Guard-12B-2602-i1-GGUF` | https://huggingface.co/mradermacher/Gemma-SEA-Guard-12B-2602-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gemma |
| `mradermacher/gpt-oss-20b-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/gpt-oss-20b-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gpt-oss |
| `mradermacher/granite-3.3-2b-instruct-heretic-safety-defiltered-GGUF` | https://huggingface.co/mradermacher/granite-3.3-2b-instruct-heretic-safety-defiltered-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of granite |
| `mradermacher/granite-3.3-2b-instruct-heretic-safety-defiltered-i1-GGUF` | https://huggingface.co/mradermacher/granite-3.3-2b-instruct-heretic-safety-defiltered-i1-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of granite |
| `mradermacher/granite-guardian-3.1-8b-i1-GGUF` | https://huggingface.co/mradermacher/granite-guardian-3.1-8b-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `mradermacher/granite-guardian-3.2-5b-i1-GGUF` | https://huggingface.co/mradermacher/granite-guardian-3.2-5b-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `mradermacher/granite-guardian-3.3-8b-i1-GGUF` | https://huggingface.co/mradermacher/granite-guardian-3.3-8b-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `mradermacher/Llama-3.1-Nemotron-Safety-Guard-8B-v3-GGUF` | https://huggingface.co/mradermacher/Llama-3.1-Nemotron-Safety-Guard-8B-v3-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of llama |
| `mradermacher/Llama-3.1-Tulu-3-8B-SFT-no-safety-data-i1-GGUF` | https://huggingface.co/mradermacher/Llama-3.1-Tulu-3-8B-SFT-no-safety-data-i1-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of llama |
| `mradermacher/Llama-Guard-3-8B-GGUF` | https://huggingface.co/mradermacher/Llama-Guard-3-8B-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `mradermacher/Llama-Guard-3-8B-i1-GGUF` | https://huggingface.co/mradermacher/Llama-Guard-3-8B-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `mradermacher/Nemotron-3-Content-Safety-GGUF` | https://huggingface.co/mradermacher/Nemotron-3-Content-Safety-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron |
| `mradermacher/Nemotron-3.5-Content-Safety-GGUF` | https://huggingface.co/mradermacher/Nemotron-3.5-Content-Safety-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron |
| `mradermacher/Qwen3-14B-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3-14B-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen |
| `mradermacher/Qwen3-32B-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3-32B-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen |
| `mradermacher/Qwen3-VL-8B-SafetyGRPO-ablation-120-GGUF` | https://huggingface.co/mradermacher/Qwen3-VL-8B-SafetyGRPO-ablation-120-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `mradermacher/Qwen3-VL-8B-SafetyGRPO-ablation-120-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3-VL-8B-SafetyGRPO-ablation-120-i1-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `mradermacher/Qwen3.5-27B-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3.5-27B-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen |
| `mradermacher/Qwen3.5-4B-Safety-Thinking-GGUF` | https://huggingface.co/mradermacher/Qwen3.5-4B-Safety-Thinking-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `mradermacher/Qwen3.5-4B-Safety-Thinking-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3.5-4B-Safety-Thinking-i1-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `mrutkows/granite-guardian-4.1-8b-GGUF` | https://huggingface.co/mrutkows/granite-guardian-4.1-8b-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `Mungert/granite-guardian-3.2-3b-a800m-GGUF` | https://huggingface.co/Mungert/granite-guardian-3.2-3b-a800m-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `Mungert/granite-guardian-3.2-5b-GGUF` | https://huggingface.co/Mungert/granite-guardian-3.2-5b-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian |
| `Nanbeige/Nanbeige4.2-3B` | https://huggingface.co/Nanbeige/Nanbeige4.2-3B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal Nanbeige/Nanbeige4.2-3B |
| `NeelRajani/Qwen3-0.6B-Base_SFT-safety100_ADV-pku-v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT-safety100_ADV-pku-v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `NeelRajani/Qwen3-0.6B-Base_SFT-safety25_ADV-pku-v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT-safety25_ADV-pku-v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `NeelRajani/Qwen3-0.6B-Base_SFT-safety50_ADV-pku-v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT-safety50_ADV-pku-v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `NeelRajani/Qwen3-0.6B-Base_SFT-safety75_ADV-pku-v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT-safety75_ADV-pku-v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `NeelRajani/Qwen3-0.6B-Base_SFT_safety_v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT_safety_v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `nm-testing/SmolLM-1.7B-Instruct-quantized.w4a16` | https://huggingface.co/nm-testing/SmolLM-1.7B-Instruct-quantized.w4a16 | 2026-09-07 | `hf_instruct_search` | release or SKU of smollm |
| `nooruiit-864/qwen2.5-1.5b-base-ai-safety-domain-lora` | https://huggingface.co/nooruiit-864/qwen2.5-1.5b-base-ai-safety-domain-lora | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `Null-Guard/Qwen3-0.6B-Uncensored-GGUF` | https://huggingface.co/Null-Guard/Qwen3-0.6B-Uncensored-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen |
| `Null-Guard/Qwen3.5-0.8B-Uncensored-GGUF` | https://huggingface.co/Null-Guard/Qwen3.5-0.8B-Uncensored-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen |
| `nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0` | https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0 | 2026-09-07 | `hf_safety_search` | head product aegis-guard |
| `nvidia/DeepSeek-V4-Flash-0731-NVFP4` | https://huggingface.co/nvidia/DeepSeek-V4-Flash-0731-NVFP4 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of deepseek |
| `nvidia/DeepSeek-V4-Flash-0731-NVFP4` | https://huggingface.co/nvidia/DeepSeek-V4-Flash-0731-NVFP4 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal nvidia/DeepSeek-V4-Flash-0731-NVFP4 |
| `nvidia/Gemma-4-26B-A4B-NVFP4` | https://huggingface.co/nvidia/Gemma-4-26B-A4B-NVFP4 | 2026-09-07 | `hf_textgen_downloads` | release or SKU of gemma |
| `nvidia/Gemma-4-31B-IT-NVFP4` | https://huggingface.co/nvidia/Gemma-4-31B-IT-NVFP4 | 2026-09-07 | `hf_textgen_downloads` | release or SKU of gemma |
| `nvidia/llama-3.1-nemoguard-8b-content-safety` | https://huggingface.co/nvidia/llama-3.1-nemoguard-8b-content-safety | 2026-09-07 | `hf_safety_search` | release or SKU of llama |
| `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF` | https://huggingface.co/nvidia/Llama-3.1-Nemotron-70B-Instruct-HF | 2026-09-07 | `hf_textgen_likes` | release or SKU of llama |
| `nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3` | https://huggingface.co/nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3 | 2026-09-07 | `hf_guard_search`, `hf_safety_search` | release or SKU of llama |
| `nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3` | https://huggingface.co/nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3 | 2026-09-07 | `hf_guard_search`, `hf_safety_search` | repeats signal nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3 |
| `nvidia/Nemotron-3-Content-Safety` | https://huggingface.co/nvidia/Nemotron-3-Content-Safety | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron |
| `nvidia/Nemotron-3.5-Content-Safety` | https://huggingface.co/nvidia/Nemotron-3.5-Content-Safety | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron |
| `nvidia/Nemotron-Content-Safety-Reasoning-4B` | https://huggingface.co/nvidia/Nemotron-Content-Safety-Reasoning-4B | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron |
| `nvidia/Nemotron-H-56B-Base-8K` | https://huggingface.co/nvidia/Nemotron-H-56B-Base-8K | 2026-09-07 | `hf_base_search` | release or SKU of nemotron |
| `nvidia/Nemotron-H-8B-Base-8K` | https://huggingface.co/nvidia/Nemotron-H-8B-Base-8K | 2026-09-07 | `hf_base_search` | release or SKU of nemotron |
| `nvidia/Nemotron-Labs-Diffusion-8B-Base` | https://huggingface.co/nvidia/Nemotron-Labs-Diffusion-8B-Base | 2026-09-07 | `hf_base_search` | release or SKU of nemotron |
| `nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16 | 2026-09-07 | `hf_textgen_downloads` | SKU of head product nemotron |
| `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16 | 2026-09-07 | `hf_textgen_downloads` | head product nemotron |
| `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | SKU of head product nemotron |
| `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | repeats signal nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 |
| `nvidia/Qwen3.5-122B-A10B-NVFP4` | https://huggingface.co/nvidia/Qwen3.5-122B-A10B-NVFP4 | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `nvidia/Qwen3.6-35B-A3B-NVFP4` | https://huggingface.co/nvidia/Qwen3.6-35B-A3B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | release or SKU of qwen |
| `nvidia/Qwen3.6-35B-A3B-NVFP4` | https://huggingface.co/nvidia/Qwen3.6-35B-A3B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | repeats signal nvidia/Qwen3.6-35B-A3B-NVFP4 |
| `nvidia/Qwen3.8-Flash-Next-NVFP4` | https://huggingface.co/nvidia/Qwen3.8-Flash-Next-NVFP4 | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `OBLITERATUS/Ornith-1.5-9B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Ornith-1.5-9B-OBLITERATED | 2026-09-07 | `hf_textgen_trending` | release or SKU of ornith |
| `OBLITERATUS/Qwen3.8-27B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Qwen3.8-27B-OBLITERATED | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | release or SKU of qwen |
| `OBLITERATUS/Qwen3.8-27B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Qwen3.8-27B-OBLITERATED | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | repeats signal OBLITERATUS/Qwen3.8-27B-OBLITERATED |
| `OBLITERATUS/Qwen3.8-27B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Qwen3.8-27B-OBLITERATED | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | repeats signal OBLITERATUS/Qwen3.8-27B-OBLITERATED |
| `OBLITERATUS/Qwen3.8-27B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Qwen3.8-27B-OBLITERATED | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | repeats signal OBLITERATUS/Qwen3.8-27B-OBLITERATED |
| `oneonlee/llama-3.1-nemoguard-8b-content-safety-merged` | https://huggingface.co/oneonlee/llama-3.1-nemoguard-8b-content-safety-merged | 2026-09-07 | `hf_safety_search` | release or SKU of llama |
| `openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal openai-community/gpt2 |
| `openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal openai-community/gpt2 |
| `openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal openai-community/gpt2 |
| `openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal openai-community/gpt2 |
| `openai-community/gpt2-large` | https://huggingface.co/openai-community/gpt2-large | 2026-09-07 | `hf_textgen_downloads` | same product as the emitted row gpt-2 |
| `openai/clip-vit-base-patch32` | https://huggingface.co/openai/clip-vit-base-patch32 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal openai/clip-vit-base-patch32 |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | head product gpt-oss |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | repeats signal openai/gpt-oss-120b |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | repeats signal openai/gpt-oss-120b |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | repeats signal openai/gpt-oss-120b |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | head product gpt-oss |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | repeats signal openai/gpt-oss-20b |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | repeats signal openai/gpt-oss-20b |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | repeats signal openai/gpt-oss-20b |
| `openbmb/MiniCPM5-1B` | https://huggingface.co/openbmb/MiniCPM5-1B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | head product minicpm |
| `openbmb/MiniCPM5-1B` | https://huggingface.co/openbmb/MiniCPM5-1B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal openbmb/MiniCPM5-1B |
| `openbmb/MiniCPM5-1B-Base` | https://huggingface.co/openbmb/MiniCPM5-1B-Base | 2026-09-07 | `hf_base_search` | release or SKU of minicpm |
| `orcarouter/DeepSeek-V4-Flash-Vision-Uncensored` | https://huggingface.co/orcarouter/DeepSeek-V4-Flash-Vision-Uncensored | 2026-09-07 | `hf_textgen_trending` | release or SKU of deepseek |
| `orcarouter/DeepSeek-V4-Flash-Vision-Uncensored-GGUF` | https://huggingface.co/orcarouter/DeepSeek-V4-Flash-Vision-Uncensored-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of deepseek |
| `orcarouter/GLM-5.3-Flash-Uncensored-FP8` | https://huggingface.co/orcarouter/GLM-5.3-Flash-Uncensored-FP8 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of glm |
| `orcarouter/GLM-5.3-Flash-Uncensored-FP8` | https://huggingface.co/orcarouter/GLM-5.3-Flash-Uncensored-FP8 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal orcarouter/GLM-5.3-Flash-Uncensored-FP8 |
| `orcarouter/GLM-5.3-Flash-Uncensored-NVFP4` | https://huggingface.co/orcarouter/GLM-5.3-Flash-Uncensored-NVFP4 | 2026-09-07 | `hf_all_trending` | release or SKU of glm |
| `orcarouter/Qwen3.8-27B-Uncensored` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `orcarouter/Qwen3.8-27B-Uncensored-FP8` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored-FP8 | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `orcarouter/Qwen3.8-27B-Uncensored-GGUF` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `orcarouter/Qwen3.8-27B-Uncensored-MLX` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored-MLX | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF` | https://huggingface.co/orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `Orion-zhen/Qwen2.5-Coder-7B-Instruct-AWQ` | https://huggingface.co/Orion-zhen/Qwen2.5-Coder-7B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `ornith-ai/Ornith-1.0-35B` | https://huggingface.co/ornith-ai/Ornith-1.0-35B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of ornith |
| `ornith-ai/Ornith-1.0-35B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.0-35B-GGUF | 2026-09-07 | `hf_textgen_downloads` | release or SKU of ornith |
| `ornith-ai/Ornith-1.0-9B` | https://huggingface.co/ornith-ai/Ornith-1.0-9B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of ornith |
| `ornith-ai/Ornith-1.0-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.0-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | release or SKU of ornith |
| `ornith-ai/Ornith-1.0-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.0-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | repeats signal ornith-ai/Ornith-1.0-9B-GGUF |
| `ornith-ai/Ornith-1.5-35B-A3B` | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of ornith |
| `ornith-ai/Ornith-1.5-35B-A3B` | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal ornith-ai/Ornith-1.5-35B-A3B |
| `ornith-ai/Ornith-1.5-35B-A3B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | release or SKU of ornith |
| `ornith-ai/Ornith-1.5-35B-A3B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | repeats signal ornith-ai/Ornith-1.5-35B-A3B-GGUF |
| `ornith-ai/Ornith-1.5-9B` | https://huggingface.co/ornith-ai/Ornith-1.5-9B | 2026-09-07 | `hf_textgen_trending` | release or SKU of ornith |
| `ornith-ai/Ornith-1.5-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending` | release or SKU of ornith |
| `ornith-ai/Ornith-1.5-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending` | repeats signal ornith-ai/Ornith-1.5-9B-GGUF |
| `ornith-ai/Ornith-1.5-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending` | repeats signal ornith-ai/Ornith-1.5-9B-GGUF |
| `outsourc-e/Qwen3.8-27B-Unleashed-GGUF` | https://huggingface.co/outsourc-e/Qwen3.8-27B-Unleashed-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `pipecat-ai/phonellm-alpha-1` | https://huggingface.co/pipecat-ai/phonellm-alpha-1 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal pipecat-ai/phonellm-alpha-1 |
| `Playtime-AI/Minimax_H3-Sydney_Sweeney` | https://huggingface.co/Playtime-AI/Minimax_H3-Sydney_Sweeney | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `princeton-nlp/Llama-3-8B-ProLong-64k-Base` | https://huggingface.co/princeton-nlp/Llama-3-8B-ProLong-64k-Base | 2026-09-07 | `hf_base_search` | release or SKU of llama |
| `prism-ml/Ternary-Bonsai-27B-gguf` | https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal prism-ml/Ternary-Bonsai-27B-gguf |
| `prithivMLmods/MiniMax-H3-Facial-Realism-CloseUp` | https://huggingface.co/prithivMLmods/MiniMax-H3-Facial-Realism-CloseUp | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `project-free-llama/Llama-Prompt-Guard-2-86M` | https://huggingface.co/project-free-llama/Llama-Prompt-Guard-2-86M | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `pyannote/speaker-diarization-3.1` | https://huggingface.co/pyannote/speaker-diarization-3.1 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal pyannote/speaker-diarization-3.1 |
| `pyannote/speaker-diarization-community-1` | https://huggingface.co/pyannote/speaker-diarization-community-1 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal pyannote/speaker-diarization-community-1 |
| `QuantFactory/Llama-Guard-3-1B-GGUF` | https://huggingface.co/QuantFactory/Llama-Guard-3-1B-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `QuantFactory/Llama-Guard-3-8B-GGUF` | https://huggingface.co/QuantFactory/Llama-Guard-3-8B-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ` | https://huggingface.co/QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ` | https://huggingface.co/QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ` | https://huggingface.co/QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ |
| `QUASAR-QAT/Qwen3.8-27B-QUASAR-NVFP4` | https://huggingface.co/QUASAR-QAT/Qwen3.8-27B-QUASAR-NVFP4 | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `Qwen/Qwen-72B` | https://huggingface.co/Qwen/Qwen-72B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen-Drive-1.0-4B` | https://huggingface.co/Qwen/Qwen-Drive-1.0-4B | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `Qwen/Qwen2-0.5B-Instruct` | https://huggingface.co/Qwen/Qwen2-0.5B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2-1.5B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2-7B-Instruct` | https://huggingface.co/Qwen/Qwen2-7B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-0.5B` | https://huggingface.co/Qwen/Qwen2.5-0.5B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen2.5-0.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-0.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-0.5B-Instruct |
| `Qwen/Qwen2.5-0.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-0.5B-Instruct |
| `Qwen/Qwen2.5-0.5B-Instruct-GGUF` | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-1.5B` | https://huggingface.co/Qwen/Qwen2.5-1.5B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen2.5-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-1.5B-Instruct |
| `Qwen/Qwen2.5-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-1.5B-Instruct |
| `Qwen/Qwen2.5-1.5B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-1.5B-Instruct-GGUF` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | head product qwen-instruct |
| `Qwen/Qwen2.5-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-14B-Instruct |
| `Qwen/Qwen2.5-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-14B-Instruct-AWQ |
| `Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-32B-Instruct |
| `Qwen/Qwen2.5-32B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-32B-Instruct-GPTQ-Int4` | https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GPTQ-Int4 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-3B-Instruct |
| `Qwen/Qwen2.5-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-3B-Instruct |
| `Qwen/Qwen2.5-3B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-3B-Instruct-GGUF` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-72B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-72B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-72B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-72B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-7B-Instruct |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-7B-Instruct |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-7B-Instruct |
| `Qwen/Qwen2.5-7B-Instruct-1M` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-1M | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-7B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-7B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-7B-Instruct-AWQ |
| `Qwen/Qwen2.5-Coder-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-Coder-14B-Instruct |
| `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-Coder-14B-Instruct-AWQ |
| `Qwen/Qwen2.5-Coder-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search` | head product qwen-coder |
| `Qwen/Qwen2.5-Coder-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-Coder-32B-Instruct |
| `Qwen/Qwen2.5-Coder-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-Coder-32B-Instruct |
| `Qwen/Qwen2.5-Coder-32B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-32B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-Coder-32B-Instruct-AWQ |
| `Qwen/Qwen2.5-Coder-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | head product qwen-coder |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-Coder-7B-Instruct |
| `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-7B-Instruct-GPTQ-Int4` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GPTQ-Int4 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Math-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Math-1.5B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-VL-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct | 2026-09-07 | `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | repeats signal Qwen/Qwen3-0.6B |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | repeats signal Qwen/Qwen3-0.6B |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads` | repeats signal Qwen/Qwen3-0.6B |
| `Qwen/Qwen3-0.6B-Base` | https://huggingface.co/Qwen/Qwen3-0.6B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-1.7B` | https://huggingface.co/Qwen/Qwen3-1.7B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-1.7B-Base` | https://huggingface.co/Qwen/Qwen3-1.7B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-1.7B-Base` | https://huggingface.co/Qwen/Qwen3-1.7B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search` | repeats signal Qwen/Qwen3-1.7B-Base |
| `Qwen/Qwen3-14B` | https://huggingface.co/Qwen/Qwen3-14B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-14B-AWQ` | https://huggingface.co/Qwen/Qwen3-14B-AWQ | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-14B-Base` | https://huggingface.co/Qwen/Qwen3-14B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-235B-A22B` | https://huggingface.co/Qwen/Qwen3-235B-A22B | 2026-09-07 | `hf_textgen_likes` | head product qwen |
| `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8` | https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-30B-A3B` | https://huggingface.co/Qwen/Qwen3-30B-A3B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-30B-A3B-Base` | https://huggingface.co/Qwen/Qwen3-30B-A3B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-30B-A3B-Instruct-2507` | https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-30B-A3B-Instruct-2507` | https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen3-30B-A3B-Instruct-2507 |
| `Qwen/Qwen3-30B-A3B-Instruct-2507-FP8` | https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507-FP8 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-32B` | https://huggingface.co/Qwen/Qwen3-32B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-32B` | https://huggingface.co/Qwen/Qwen3-32B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | repeats signal Qwen/Qwen3-32B |
| `Qwen/Qwen3-4B` | https://huggingface.co/Qwen/Qwen3-4B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-4B` | https://huggingface.co/Qwen/Qwen3-4B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | repeats signal Qwen/Qwen3-4B |
| `Qwen/Qwen3-4B-Base` | https://huggingface.co/Qwen/Qwen3-4B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-4B-Base` | https://huggingface.co/Qwen/Qwen3-4B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search` | repeats signal Qwen/Qwen3-4B-Base |
| `Qwen/Qwen3-4B-Instruct-2507` | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-4B-Instruct-2507` | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen3-4B-Instruct-2507 |
| `Qwen/Qwen3-4B-Instruct-2507-FP8` | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507-FP8 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-4B-Instruct-2507-FP8` | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507-FP8 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen3-4B-Instruct-2507-FP8 |
| `Qwen/Qwen3-8B` | https://huggingface.co/Qwen/Qwen3-8B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-8B` | https://huggingface.co/Qwen/Qwen3-8B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads` | repeats signal Qwen/Qwen3-8B |
| `Qwen/Qwen3-8B` | https://huggingface.co/Qwen/Qwen3-8B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads` | repeats signal Qwen/Qwen3-8B |
| `Qwen/Qwen3-8B-AWQ` | https://huggingface.co/Qwen/Qwen3-8B-AWQ | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-8B-Base` | https://huggingface.co/Qwen/Qwen3-8B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | head product qwen-coder |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | repeats signal Qwen/Qwen3-Coder-30B-A3B-Instruct |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct` | https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct | 2026-09-07 | `hf_textgen_likes` | release or SKU of qwen |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8` | https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8 | 2026-09-07 | `hf_instruct_search` | head product qwen-coder |
| `Qwen/Qwen3-Coder-Next` | https://huggingface.co/Qwen/Qwen3-Coder-Next | 2026-09-07 | `hf_textgen_likes` | release or SKU of qwen |
| `Qwen/Qwen3-Coder-Next-FP8` | https://huggingface.co/Qwen/Qwen3-Coder-Next-FP8 | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-Embedding-0.6B` | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-Embedding-0.6B` | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads` | repeats signal Qwen/Qwen3-Embedding-0.6B |
| `Qwen/Qwen3-Embedding-0.6B` | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads` | repeats signal Qwen/Qwen3-Embedding-0.6B |
| `Qwen/Qwen3-Embedding-4B` | https://huggingface.co/Qwen/Qwen3-Embedding-4B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-Embedding-8B` | https://huggingface.co/Qwen/Qwen3-Embedding-8B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-Next-80B-A3B-Instruct` | https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-Reranker-0.6B` | https://huggingface.co/Qwen/Qwen3-Reranker-0.6B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-Reranker-4B` | https://huggingface.co/Qwen/Qwen3-Reranker-4B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-VL-8B-Instruct` | https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct | 2026-09-07 | `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3.5-4B` | https://huggingface.co/Qwen/Qwen3.5-4B | 2026-09-07 | `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3.5-9B` | https://huggingface.co/Qwen/Qwen3.5-9B | 2026-09-07 | `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3.6-27B` | https://huggingface.co/Qwen/Qwen3.6-27B | 2026-09-07 | `hf_all_downloads` | head product qwen |
| `Qwen/Qwen3.6-27B-FP8` | https://huggingface.co/Qwen/Qwen3.6-27B-FP8 | 2026-09-07 | `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3.6-35B-A3B` | https://huggingface.co/Qwen/Qwen3.6-35B-A3B | 2026-09-07 | `hf_all_downloads` | head product qwen |
| `Qwen/Qwen3.6-35B-A3B-FP8` | https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8 | 2026-09-07 | `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3.8-2.4T-A95B` | https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | release or SKU of qwen |
| `Qwen/Qwen3.8-2.4T-A95B` | https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal Qwen/Qwen3.8-2.4T-A95B |
| `Qwen/Qwen3.8-27B` | https://huggingface.co/Qwen/Qwen3.8-27B | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | release or SKU of qwen |
| `Qwen/Qwen3.8-27B` | https://huggingface.co/Qwen/Qwen3.8-27B | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal Qwen/Qwen3.8-27B |
| `Qwen/Qwen3.8-27B-FP8` | https://huggingface.co/Qwen/Qwen3.8-27B-FP8 | 2026-09-07 | `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3.8-Flash-Next` | https://huggingface.co/Qwen/Qwen3.8-Flash-Next | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `RadixArk/Kimi-K3-DSpark` | https://huggingface.co/RadixArk/Kimi-K3-DSpark | 2026-09-07 | `hf_textgen_downloads` | release or SKU of kimi |
| `RedHatAI/Llama-3.2-1B-Instruct-FP8-dynamic` | https://huggingface.co/RedHatAI/Llama-3.2-1B-Instruct-FP8-dynamic | 2026-09-07 | `hf_instruct_search` | release or SKU of llama |
| `RedHatAI/Llama-Guard-4-12B-quantized.w4a16` | https://huggingface.co/RedHatAI/Llama-Guard-4-12B-quantized.w4a16 | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `Ryn1998/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF` | https://huggingface.co/Ryn1998/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `sentence-transformers/all-MiniLM-L6-v2` | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal sentence-transformers/all-MiniLM-L6-v2 |
| `smhfacct/Minimax-H3-fl2va-ref2va-hybrid-models` | https://huggingface.co/smhfacct/Minimax-H3-fl2va-ref2va-hybrid-models | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `solidrust/Mistral-7B-Instruct-v0.3-AWQ` | https://huggingface.co/solidrust/Mistral-7B-Instruct-v0.3-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of mistral-7b-instruct |
| `speach1sdef178/MiniMax-H3-Semantic-Bridge` | https://huggingface.co/speach1sdef178/MiniMax-H3-Semantic-Bridge | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `swiss-ai/Apertus-8B-Instruct-2509` | https://huggingface.co/swiss-ai/Apertus-8B-Instruct-2509 | 2026-09-07 | `hf_instruct_search` | release or SKU of apertus |
| `tencent/Hy4-preview` | https://huggingface.co/tencent/Hy4-preview | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal tencent/Hy4-preview |
| `ThakiCloud/Qwen3.8-27B-Human-KO-Safety` | https://huggingface.co/ThakiCloud/Qwen3.8-27B-Human-KO-Safety | 2026-09-07 | `hf_safety_search` | release or SKU of qwen |
| `theblackcat102/llama-3.2-1b-instruct-allenai_wildguard_safety` | https://huggingface.co/theblackcat102/llama-3.2-1b-instruct-allenai_wildguard_safety | 2026-09-07 | `hf_safety_search` | release or SKU of llama |
| `tiiuae/falcon-180B` | https://huggingface.co/tiiuae/falcon-180B | 2026-09-07 | `hf_textgen_likes` | release or SKU of falcon |
| `tiiuae/falcon-40b` | https://huggingface.co/tiiuae/falcon-40b | 2026-09-07 | `hf_textgen_likes` | release or SKU of falcon |
| `tiiuae/falcon-40b-instruct` | https://huggingface.co/tiiuae/falcon-40b-instruct | 2026-09-07 | `hf_textgen_likes` | release or SKU of falcon |
| `tiiuae/Falcon-H1-0.5B-Base` | https://huggingface.co/tiiuae/Falcon-H1-0.5B-Base | 2026-09-07 | `hf_base_search` | release or SKU of falcon |
| `tiiuae/Falcon-H1-1.5B-Base` | https://huggingface.co/tiiuae/Falcon-H1-1.5B-Base | 2026-09-07 | `hf_base_search` | release or SKU of falcon |
| `tiiuae/Falcon3-10B-Base` | https://huggingface.co/tiiuae/Falcon3-10B-Base | 2026-09-07 | `hf_base_search` | head product falcon |
| `tiiuae/Falcon3-1B-Base` | https://huggingface.co/tiiuae/Falcon3-1B-Base | 2026-09-07 | `hf_base_search` | release or SKU of falcon |
| `tiiuae/Falcon3-7B-Base` | https://huggingface.co/tiiuae/Falcon3-7B-Base | 2026-09-07 | `hf_base_search` | release or SKU of falcon |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | head product tinyllama-chat |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal TinyLlama/TinyLlama-1.1B-Chat-v1.0 |
| `trl-internal-testing/tiny-Qwen2ForCausalLM-2.5` | https://huggingface.co/trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | repeats signal trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 |
| `unsloth/DeepSeek-R1-GGUF` | https://huggingface.co/unsloth/DeepSeek-R1-GGUF | 2026-09-07 | `hf_textgen_likes` | release or SKU of deepseek |
| `unsloth/DeepSeek-V4-Flash-Vision-Exp-GGUF` | https://huggingface.co/unsloth/DeepSeek-V4-Flash-Vision-Exp-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of deepseek |
| `unsloth/GLM-5.3-Flash-GGUF` | https://huggingface.co/unsloth/GLM-5.3-Flash-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of glm |
| `unsloth/GLM-5.3-Flash-GGUF` | https://huggingface.co/unsloth/GLM-5.3-Flash-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal unsloth/GLM-5.3-Flash-GGUF |
| `unsloth/Llama-3.2-1B-Instruct` | https://huggingface.co/unsloth/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of llama |
| `unsloth/Llama-3.2-3B-Instruct-GGUF` | https://huggingface.co/unsloth/Llama-3.2-3B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of llama |
| `unsloth/Qwen2.5-7B-Instruct` | https://huggingface.co/unsloth/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `unsloth/Qwen3-0.6B-Base` | https://huggingface.co/unsloth/Qwen3-0.6B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `unsloth/Qwen3-1.7B-Base-unsloth-bnb-4bit` | https://huggingface.co/unsloth/Qwen3-1.7B-Base-unsloth-bnb-4bit | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `unsloth/Qwen3-4B-Base` | https://huggingface.co/unsloth/Qwen3-4B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `unsloth/Qwen3-4B-Base-unsloth-bnb-4bit` | https://huggingface.co/unsloth/Qwen3-4B-Base-unsloth-bnb-4bit | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `unsloth/Qwen3-8B-Base-unsloth-bnb-4bit` | https://huggingface.co/unsloth/Qwen3-8B-Base-unsloth-bnb-4bit | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` | https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` | https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_downloads`, `hf_instruct_search` | repeats signal unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF |
| `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` | https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_downloads`, `hf_instruct_search` | repeats signal unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF |
| `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` | https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_downloads`, `hf_instruct_search` | repeats signal unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF |
| `unsloth/Qwen3.8-27B-GGUF` | https://huggingface.co/unsloth/Qwen3.8-27B-GGUF | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | release or SKU of qwen |
| `unsloth/Qwen3.8-27B-GGUF` | https://huggingface.co/unsloth/Qwen3.8-27B-GGUF | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal unsloth/Qwen3.8-27B-GGUF |
| `unsloth/Qwen3.8-Flash-Next-GGUF` | https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `VerifiedAnon/gemma-moderation-finetune` | https://huggingface.co/VerifiedAnon/gemma-moderation-finetune | 2026-09-07 | `hf_moderation_search` | release or SKU of gemma |
| `vikhyatk/moondream2` | https://huggingface.co/vikhyatk/moondream2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal vikhyatk/moondream2 |
| `VitalyProtasov/Nemotron-3.5-Content-Safety-FP8-LLM-Compressor` | https://huggingface.co/VitalyProtasov/Nemotron-3.5-Content-Safety-FP8-LLM-Compressor | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron |
| `WarmBloodAban/Minimax-h3_Singularity` | https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `Weni/Llama-Guard-3-8B-AWQ` | https://huggingface.co/Weni/Llama-Guard-3-8B-AWQ | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `wms2537/qwen3-0.6b-malaysia-moderation-cot` | https://huggingface.co/wms2537/qwen3-0.6b-malaysia-moderation-cot | 2026-09-07 | `hf_moderation_search` | release or SKU of qwen |
| `xai-org/grok-1` | https://huggingface.co/xai-org/grok-1 | 2026-09-07 | `hf_textgen_likes` | release or SKU of grok |
| `XHToken/Spark-X2.5-1.7B` | https://huggingface.co/XHToken/Spark-X2.5-1.7B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal XHToken/Spark-X2.5-1.7B |
| `XHToken/Spark-X2.5-4B` | https://huggingface.co/XHToken/Spark-X2.5-4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal XHToken/Spark-X2.5-4B |
| `XHToken/Spark-X2.5-4B-GGUF` | https://huggingface.co/XHToken/Spark-X2.5-4B-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal XHToken/Spark-X2.5-4B-GGUF |
| `yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | release or SKU of gemma |
| `yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF |
| `yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | release or SKU of gemma |
| `yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF |
| `z-lab/Qwen3.8-27B-DFlash2` | https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2 | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `z-lab/Qwen3.8-27B-DFlash2-GGUF` | https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `zai-org/GLM-4.5` | https://huggingface.co/zai-org/GLM-4.5 | 2026-09-07 | `hf_textgen_likes` | release or SKU of glm |
| `zai-org/GLM-4.5-Air-Base` | https://huggingface.co/zai-org/GLM-4.5-Air-Base | 2026-09-07 | `hf_base_search` | release or SKU of glm |
| `zai-org/GLM-4.6` | https://huggingface.co/zai-org/GLM-4.6 | 2026-09-07 | `hf_textgen_likes` | head product glm |
| `zai-org/GLM-4.7` | https://huggingface.co/zai-org/GLM-4.7 | 2026-09-07 | `hf_textgen_likes` | release or SKU of glm |
| `zai-org/GLM-4.7-Flash` | https://huggingface.co/zai-org/GLM-4.7-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of glm |
| `zai-org/GLM-4.7-Flash` | https://huggingface.co/zai-org/GLM-4.7-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal zai-org/GLM-4.7-Flash |
| `zai-org/GLM-5` | https://huggingface.co/zai-org/GLM-5 | 2026-09-07 | `hf_textgen_likes` | release or SKU of glm |
| `zai-org/GLM-5.1` | https://huggingface.co/zai-org/GLM-5.1 | 2026-09-07 | `hf_textgen_likes` | head product glm |
| `zai-org/GLM-5.2` | https://huggingface.co/zai-org/GLM-5.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | head product glm |
| `zai-org/GLM-5.2` | https://huggingface.co/zai-org/GLM-5.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal zai-org/GLM-5.2 |
| `zai-org/GLM-5.2-FP8` | https://huggingface.co/zai-org/GLM-5.2-FP8 | 2026-09-07 | `hf_textgen_downloads` | release or SKU of glm |
| `zai-org/GLM-5.3` | https://huggingface.co/zai-org/GLM-5.3 | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | release or SKU of glm |
| `zai-org/GLM-5.3` | https://huggingface.co/zai-org/GLM-5.3 | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | repeats signal zai-org/GLM-5.3 |
| `zai-org/GLM-5.3` | https://huggingface.co/zai-org/GLM-5.3 | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | repeats signal zai-org/GLM-5.3 |
| `zai-org/GLM-5.3-Flash` | https://huggingface.co/zai-org/GLM-5.3-Flash | 2026-09-07 | `hf_all_trending` | release or SKU of glm |
| `zerodigest/Qwen3.8-27B-Uncensored-YMQ-MTP-GGUF` | https://huggingface.co/zerodigest/Qwen3.8-27B-Uncensored-YMQ-MTP-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen |
| `ZiweiLiu96/llama-3.2-3b-Content-Moderation` | https://huggingface.co/ZiweiLiu96/llama-3.2-3b-Content-Moderation | 2026-09-07 | `hf_moderation_search` | release or SKU of llama |
| `ZiweiLiu96/llama-3.2-3b-Content-Moderation-Q4_K_M-GGUF` | https://huggingface.co/ZiweiLiu96/llama-3.2-3b-Content-Moderation-Q4_K_M-GGUF | 2026-09-07 | `hf_moderation_search` | release or SKU of llama |
| `www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Ora` | http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-AIpro(20T).html | 2026-09-07 | — | second path tried for the same Orange Pi AIpro signal |
| `sima.ai/modalix/` | https://sima.ai/modalix/ | 2026-09-07 | — | second path tried for the same SiMa.ai signal |
| `www.axelera.ai/metis-aipu` | https://www.axelera.ai/metis-aipu | 2026-09-07 | — | head product axelera-metis-aipu |
| `www.blaize.com/products/blaize-pathfinder-p1600-embedded-som/` | https://www.blaize.com/products/blaize-pathfinder-p1600-embedded-som/ | 2026-09-07 | — | second path tried for the same Blaize signal |
| `www.hailo.ai/products/ai-accelerators/hailo-10h-m-2-generative-ai-acce` | https://www.hailo.ai/products/ai-accelerators/hailo-10h-m-2-generative-ai-acceleration-module/ | 2026-09-07 | — | head product hailo-10h |
| `www.orangepi.org/orangepiwiki/index.php/Orange_Pi_AIpro` | https://www.orangepi.org/orangepiwiki/index.php/Orange_Pi_AIpro | 2026-09-07 | — | third path tried for the same Orange Pi AIpro signal |
| `www.rock-chips.com/a/en/products/RK35_Series/2024/0705/1729.html` | https://www.rock-chips.com/a/en/products/RK35_Series/2024/0705/1729.html | 2026-09-07 | — | second path tried for the same Rockchip RK3576 signal |

## Escalations for a person

1. **The taxonomy has no category for five large, heavily used model populations.** Text embedding
   and reranking models (18 candidates, led by `sentence-transformers/all-MiniLM-L6-v2` at 251M
   trailing-30-day downloads — more than any model on the map), speech and audio models, vision and
   vision-language backbones, generative image and video models, and time-series forecasters. All
   are parked above against a `category-proposal` issue. This is the largest coverage gap the sweep
   found, and taxonomy is a governance event: this workflow does not open it.
2. **No category holds datacenter or workstation accelerators.** Tenstorrent's Blackhole cards are
   parked for this reason; `edge_hardware` is explicitly about the edge.
3. **Hardware has no non-URL identifier, anywhere.** All 15 board-level candidates are parked for
   it. Either the registry needs an identifier kind a board can carry, or `edge_hardware` stays a
   head-only category. A sweep cannot settle that.
4. **An unresolved text-versus-vision boundary in `dataset_processing_tools`.** BlenderProc, fastdup
   and fiftyone are in scope by the letter of the category (synthetic-data generation,
   deduplication) but every product on the roster builds text or document corpora. Parked pending a
   boundary ruling rather than decided by a sweep. `microsoft/presidio` is the same shape on the
   `safeguards` side: a general-purpose PII detection and redaction framework that only an
   editorial argument brings inside a category about filtering model inputs and outputs.
5. **Two ledger holds re-surfaced and were not re-proposed:** `RyanCodrai/turbovec` and
   `FailproofAI/failproofai` both carry `unresolved` product_equivalence rulings in
   `sources/resolution_ledger.yaml`.
6. **Two open boundary questions in `compilers`:** `EnzymeAD/Enzyme` (automatic-differentiation
   compiler pass) and `llvm/circt` (hardware-EDA compiler).
7. **The warehouse discovery pool was unreachable** (no `OSO_API_KEY`). Re-running with warehouse
   access would likely consolidate signals this sweep treated as separate.
8. **29 of the 52 rows name an organization with no record in `sources/organizations/`**
   (for example `bespoke-labs`, `minish-lab`, `guardion`, `flagos-ai`); the org slug there is the
   slugified or transcribed owner login. On 46 of the 52 rows the owner login is not a
   declared handle for the organization named, which is why the derivation tables mark those rows
   as transcriptions. Declared handles belong in `sources/org_handles.yaml` on `main`, which is
   also what repairs the coverage baseline named under **Gates**.

## Gates

- `uv run python -m build.validate` → `0 error(s), 2 warning(s)` (both warnings pre-existing
  `model_families` pattern-overlap notices, unchanged by this batch).
- `uv run python -m build.check_corpus_diff --base main` → no stage, gap, product-count or tier
  move in any category, and no untouched axis-assessment row rewritten. Registry rows are
  signal-only and invisible to the scored payload, which is why the sheet is empty; that is the
  expected result for a `tail-batch` PR and the reason no `stage-move` label is needed.

  ```
  ## Review sheet

  | category | stage | gaps | products | tier changes |
  |---|---|---|---|---|

  stage moves: none

  untouched-product row changes: none
  ```

- `uv run pytest -q` → **5 failed, 1828 passed, 1 skipped**. Every failure is in `tests/test_identity_eval.py`
  (5 failed, 132 passed when that file is run alone), and every one of them repairs only by
  editing a corpus-wide generated fixture:

  | test | what it wants edited |
  |---|---|
  | `test_the_pass_fixture_tail_rows_match_the_corpus` | `tests/fixtures/identity_edges_pass.json` |
  | `test_write_fixture_is_idempotent` | `tests/fixtures/identity_edges_pass.json` |
  | `test_fixture_mode_does_not_grade_the_invariant` | `tests/fixtures/identity_edges_pass.json` |
  | `test_main_prints_a_coverage_line_per_route` | `tests/fixtures/identity_coverage_baseline.json` |
  | `test_the_live_corpus_is_at_or_above_the_committed_baseline` | `tests/fixtures/identity_coverage_baseline.json` |

  The cause is one thing, not five: the 52 new tail rows add artifacts whose organizations declare
  no handle in `sources/org_handles.yaml`, so the coverage *denominators* grow while the numerators
  hold exactly — `github` 211/299 → 211/320, `huggingface` 51/62 → 51/73, `homepage_domain`
  6/27 → 6/35. Nothing lost a handle; the corpus got bigger. All 137 tests in that file pass on
  `main` (verified in a scratch worktree at 9df82a12), so this is caused by the batch and not
  pre-existing.

  Under [ADR-004](../architecture/adr-004-machine-proposals-and-the-public-tail.md#decision) point
  3, a gate whose only repair is a corpus-wide fixture edit does not block a proposal PR:
  "identity membership fixtures and committed coverage baselines" are named there, and they bind
  on `main`, where the fixtures are regenerated, not on a batch that is forbidden to touch them.
  Neither fixture was regenerated here and no `org_handles.yaml` entry was added. A reviewer
  records these failures and merges on the sheet; the right follow-up is declared handles for the
  new organizations, on `main`, in its own commit.

- Diff touches `sources/registry/**` and this file only. No product, score, category-roster,
  taxonomy, org-handle or fixture file, and neither generated artifact.

## Revisions

This is the second revision of the sheet. What changed, and where:

| correction | what it changed |
|---|---|
| Every emitted row needs an identifier that is not a URL | The 15 homepage-only `edge_hardware` rows are parked with their pages and fetch dates; `sources/registry/edge_hardware.yaml` is not created. 52 rows remain across five categories. |
| Mirrors are duplicates, not unique candidates | `autogluon/chronos-2` and `autogluon/chronos-bolt-small` fold onto the Amazon signals, and five more signals whose recorded reason already acknowledged a fold (a Core ML conversion, an abliterated GGUF redistribution, a head-product SKU, a UI over a head product, a plugin surface of a row in this batch) move to the duplicate side. All five counts were recomputed, not adjusted: 1819 = 708 + 1111, 1111 = 52 + 1059. |
| Parked candidates need candidate-level provenance | Every parked candidate is now listed with its identifier, source URL, fetch date and reason — including all 844 below a retrieval cutoff, each with the query that returned it. Every duplicate is listed with what it folded onto. |
| No emitted field may depend on an editorial reading | The query→category mapping, the declared-metadata rule and the per-row derivation tables are published above. Four rows whose acceptance or category rested on an argument are parked (`presidio`, `unlimited-ocr`, `nsfw-image-detection`, `electra`) and one moved to the category the rule names (`lfm2` → `finetuned_chat`). Where a field is still a transcription rather than a verbatim string — a product line folded from a checkpoint id, an owner login mapped to an organization record — the derivation tables mark it row by row, because `docs/reference/identity.md` requires a product row to name a product rather than a release. |

