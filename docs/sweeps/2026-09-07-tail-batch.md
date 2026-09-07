# Tail batch — 2026-09-07

Machine-generated review sheet for the weekly candidate sweep (`discover-candidates`). One PR,
label `tail-batch`. Nothing here is scored: every row carries identity and artifacts only.
A human accepts or rejects this batch; automation opened it and does not merge it.

## Window and scope

- **Window swept:** 2026-09-07 (single day). All fetches dated 2026-09-07 unless a row says otherwise.
- **Categories swept:** the six the map's own gap arithmetic reads at maturity stage 3 or below —
  `dataset_processing_tools` (stage 2), `edge_hardware`, `safeguards`, `base_pretrained`,
  `finetuned_chat`, `compilers` (all stage 3). Category list and lifecycle status read at run time
  through `build.taxonomy.category_statuses(taxonomy)`; all 18 categories are `published`, so every
  row here is promoted later through `add-product`, not `promote-category`.
- **Not reached:** the warehouse discovery pool (`currentai.entities.repos`). No `OSO_API_KEY` in
  this environment, so the pool was unreachable — reported as a gap, not filled with a guess. It is
  an enrichment and consolidation step, never a rejection step, so its absence does not invalidate
  the dedup below; it does mean multi-signal consolidation rested on self-dedup alone.

## Reconciled counts

| count | value |
|---|---|
| `raw_signals` | 1819 |
| `duplicate_signals` | 701 |
| `unique_candidates` | 1118 |
| `accepted` | 71 |
| `parked` | 1047 |

- `raw_signals = duplicate_signals + unique_candidates` → 1819 = 701 + 1118 ✓
- `unique_candidates = accepted + parked` → 1118 = 71 + 1047 ✓

Each accepted signal maps to exactly one emitted registry row: 71 accepted signals,
71 rows. Of the 1047 parked candidates, 203 carry an individual
reason below and 844 fell below a disclosed retrieval cutoff and are grouped, with the
cutoff stated so the next sweep can lower it deliberately.

### Duplicate breakdown

| why | signals |
|---|---|
| a release or SKU of a family already on the map (model_families / release-suffix rule) | 411 |
| same signal returned by more than one query (self-dedup) | 199 |
| resolves to a head product already on the map | 77 |
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
`<title>`. Listed with their verdicts in the accepted and parked tables below.

## Retrieval cutoffs, predeclared and disclosed

- **GitHub repository search:** sort by stars descending, top 30 per query, floor 1,000 all-time
  stars and a last push no older than 2025-09-07 (12 months). 784 rows returned; 580 fell outside
  that window.
- **Hugging Face model API:** top 100 per query. Floor 1,000,000 trailing-30-day downloads on the
  seven ranked/general queries; 5,000 on the three targeted guard, safety and moderation searches,
  because those exist to reach a small-model tail. 1,000 rows returned; 680 fell outside.
- **Vendor pages:** the SBC and merchant edge-NPU vendors already on the `edge_hardware` roster
  plus the adjacent field. 35 pages, no ranking involved.

A cutoff bounds *how much was retrieved*. It never rejects a product the sweep surfaced: nine
sub-floor candidates were recognized and accepted anyway (`data-prep-kit`, `semhash`, `deepfabric`,
`magpie`, `datadreamer`, `bonito`, `gpt-j`, `lfm2`, `exaone`), each flagged in its row note. **Coverage
limitation:** the 1,260 rows below the floors were not triaged individually, so the sweep says
nothing about them either way; the fix is a deliberately lower floor next week, not a judgment here.

## No rule was invented mid-sweep

Four candidates across two signals were parked on a number rather than a threshold, with the number
stated: `Zaneham/Booth` (1,737 stars on a single-owner repository created 2026-02-16 claiming a full
CUDA, Triton and HIP compiler) and the three `farbodtavakkoli/OTel-*-LLM-*` models (6.9M
trailing-30-day downloads on a 31B model under an individual account with no resolvable lineage).
Both are parked for a person to look at, not rejected, and neither park was applied as a rule to
anything else — no star floor, download floor or growth-rate test adjudicated any other candidate.

Rate limits: GitHub search was consumed at 8.5 requests a minute against an unauthenticated ceiling
of 10, with retry-and-backoff on 403/429/5xx. No fetch was recorded as an absence. Five vendor
product pages 404'd on the paths tried and are parked as incomplete fetches, not as absences.

## Accepted — 71 rows

### `dataset_processing_tools` — 14

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
| `unlimited-ocr` | Unlimited OCR | model | `baidu` | `huggingface_model: baidu/Unlimited-OCR` | https://huggingface.co/baidu/Unlimited-OCR | document-extraction model, the olmocr shape already on this roster |

### `safeguards` — 19

| slug | display_name | type | org | artifacts | source URL (fetched 2026-09-07) | note |
|---|---|---|---|---|---|---|
| `skillspector` | SkillSpector | software | `nvidia` | `github: NVIDIA/SkillSpector` | https://github.com/NVIDIA/SkillSpector |  |
| `presidio` | Presidio | software | `data-privacy-stack` | `github: data-privacy-stack/presidio` | https://github.com/data-privacy-stack/presidio |  |
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
| `nsfw-image-detection` | NSFW Image Detection | model | `falconsai` | `huggingface_model: Falconsai/nsfw_image_detection` | https://huggingface.co/Falconsai/nsfw_image_detection |  |
| `ncii-guard` | NCII Guard | model | `hugging-face` | `huggingface_model: hfmlsoc/ncii-guard-v02` | https://huggingface.co/hfmlsoc/ncii-guard-v02 |  |
| `modernguard` | ModernGuard | model | `guardion` | `huggingface_model: guardion/ModernGuard-1` | https://huggingface.co/guardion/ModernGuard-1 | inside the targeted guard-search floor (5,000 downloads), below the ranked-query floor; the targeted search is why it was seen |
| `koalaai-text-moderation` | KoalaAI Text Moderation | model | `koala-ai` | `huggingface_model: KoalaAI/Text-Moderation` | https://huggingface.co/KoalaAI/Text-Moderation |  |
| `gliner-guard-omni` | GLiNER Guard Omni | model | `hivetrace` | `huggingface_model: hivetrace/gliner-guard-omni` | https://huggingface.co/hivetrace/gliner-guard-omni |  |
| `polite-guard` | Polite Guard | model | `intel` | `huggingface_model: Intel/polite-guard` | https://huggingface.co/Intel/polite-guard |  |
| `gliner2-guardrails-pii` | GLiNER2 Guardrails PII | model | `fastino` | `huggingface_model: fastino/GLiNER2-Guardrails-PII-Multi` | https://huggingface.co/fastino/GLiNER2-Guardrails-PII-Multi |  |

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

### `edge_hardware` — 15

| slug | display_name | type | org | artifacts | source URL (fetched 2026-09-07) | note |
|---|---|---|---|---|---|---|
| `radxa-rock-5c` | Radxa ROCK 5C | hardware | `radxa` | `homepage: https://radxa.com/products/rock5/5c` | https://radxa.com/products/rock5/5c |  |
| `banana-pi-bpi-f3` | Banana Pi BPI-F3 | hardware | `banana-pi` | `homepage: https://www.banana-pi.org/en/banana-pi-sbcs/175.html` | https://www.banana-pi.org/en/banana-pi-sbcs/175.html |  |
| `nanopc-t6` | FriendlyElec NanoPC-T6 | hardware | `friendlyelec` | `homepage: https://www.friendlyelec.com/index.php?route=product/product&product_id=292` | https://www.friendlyelec.com/index.php?route=product/product&product_id=292 |  |
| `milk-v-duo` | Milk-V Duo | hardware | `milk-v` | `homepage: https://milkv.io/duo` | https://milkv.io/duo |  |
| `beaglebone-ai-64` | BeagleBone AI-64 | hardware | `beagleboard-org-foundation` | `homepage: https://www.beagleboard.org/boards/beaglebone-ai-64` | https://www.beagleboard.org/boards/beaglebone-ai-64 |  |
| `brainchip-akida-akd1000` | BrainChip Akida AKD1000 | hardware | `brainchip` | `homepage: https://brainchip.com/akida-neural-processor-soc/` | https://brainchip.com/akida-neural-processor-soc/ |  |
| `nvidia-jetson-thor` | NVIDIA Jetson Thor | hardware | `nvidia` | `homepage: https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/` | https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/ |  |
| `google-coral-dev-board-micro` | Coral Dev Board Micro | hardware | `google` | `homepage: https://coral.ai/products/dev-board-micro/` | https://coral.ai/products/dev-board-micro/ | distinct from the head product google-coral-dev-board: different host silicon (RT1176 MCU) and form factor, sold as its own product |
| `khadas-vim4` | Khadas VIM4 | hardware | `khadas` | `homepage: https://www.khadas.com/vim4` | https://www.khadas.com/vim4 |  |
| `sipeed-licheepi-4a` | Sipeed LicheePi 4A | hardware | `sipeed` | `homepage: https://sipeed.com/licheepi4a` | https://sipeed.com/licheepi4a |  |
| `renesas-rz-v2h` | Renesas RZ/V2H | hardware | `renesas` | `homepage: https://www.renesas.com/en/products/microcontrollers-microprocessors/rz-mpus/rzv2h-quad-core-vision-ai-mpu-drp-ai3-accelerator-and-high-performance-real-time-processor` | https://www.renesas.com/en/products/microcontrollers-microprocessors/rz-mpus/rzv2h-quad-core-vision-ai-mpu-drp-ai3-accelerator-and-high-performance-real-time-processor |  |
| `luxonis-oak-d` | Luxonis OAK-D | hardware | `luxonis` | `homepage: https://shop.luxonis.com/products/oak-d` | https://shop.luxonis.com/products/oak-d |  |
| `deepx-dx-m1` | DEEPX DX-M1 | hardware | `deepx` | `homepage: https://www.deepx.ai/dx-m1/` | https://www.deepx.ai/dx-m1/ |  |
| `sophgo-bm1684x` | SOPHGO BM1684X | hardware | `sophgo` | `homepage: https://www.sophgo.com/sophon-u/product/introduce/bm1684x.html` | https://www.sophgo.com/sophon-u/product/introduce/bm1684x.html |  |
| `espressif-esp32-p4` | Espressif ESP32-P4 | hardware | `espressif` | `homepage: https://www.espressif.com/en/products/socs/esp32-p4` | https://www.espressif.com/en/products/socs/esp32-p4 |  |

### `base_pretrained` — 14

| slug | display_name | type | org | artifacts | source URL (fetched 2026-09-07) | note |
|---|---|---|---|---|---|---|
| `bert` | BERT | model | `google` | `huggingface_model: google-bert/bert-base-uncased` | https://huggingface.co/google-bert/bert-base-uncased |  |
| `roberta` | RoBERTa | model | `meta` | `huggingface_model: FacebookAI/roberta-base` | https://huggingface.co/FacebookAI/roberta-base |  |
| `xlm-roberta` | XLM-RoBERTa | model | `meta` | `huggingface_model: FacebookAI/xlm-roberta-base` | https://huggingface.co/FacebookAI/xlm-roberta-base |  |
| `t5` | T5 | model | `google` | `huggingface_model: google-t5/t5-small` | https://huggingface.co/google-t5/t5-small |  |
| `electra` | ELECTRA | model | `google` | `huggingface_model: google/electra-base-discriminator` | https://huggingface.co/google/electra-base-discriminator |  |
| `deberta` | DeBERTa | model | `microsoft` | `huggingface_model: microsoft/mdeberta-v3-base` | https://huggingface.co/microsoft/mdeberta-v3-base |  |
| `modernbert` | ModernBERT | model | `answer-ai` | `huggingface_model: answerdotai/ModernBERT-base` | https://huggingface.co/answerdotai/ModernBERT-base |  |
| `distilbert` | DistilBERT | model | `hugging-face` | `huggingface_model: distilbert/distilbert-base-uncased` | https://huggingface.co/distilbert/distilbert-base-uncased |  |
| `gpt-2` | GPT-2 | model | `openai` | `huggingface_model: openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 |  |
| `opt` | OPT | model | `meta` | `huggingface_model: facebook/opt-125m` | https://huggingface.co/facebook/opt-125m |  |
| `openelm` | OpenELM | model | `apple` | `huggingface_model: apple/OpenELM-1_1B-Instruct` | https://huggingface.co/apple/OpenELM-1_1B-Instruct |  |
| `powermoe` | PowerMoE | model | `ibm` | `huggingface_model: ibm-research/PowerMoE-3b` | https://huggingface.co/ibm-research/PowerMoE-3b |  |
| `lfm2` | Liquid LFM2 | model | `liquid-ai` | `huggingface_model: LiquidAI/LFM2.5-2.6B` | https://huggingface.co/LiquidAI/LFM2.5-2.6B | base-weights repo chosen over the GGUF repo the ranked query returned; both are the same product |
| `gpt-j` | GPT-J | model | `eleutherai` | `huggingface_model: EleutherAI/gpt-j-6b` | https://huggingface.co/EleutherAI/gpt-j-6b | below the disclosed download floor (261,799); accepted because the cutoff bounds retrieval only |

### `finetuned_chat` — 2

| slug | display_name | type | org | artifacts | source URL (fetched 2026-09-07) | note |
|---|---|---|---|---|---|---|
| `dolphin` | Dolphin | model | `dphn` | `huggingface_model: dphn/dolphin-2.9.1-yi-1.5-34b` | https://huggingface.co/dphn/dolphin-2.9.1-yi-1.5-34b |  |
| `exaone` | EXAONE | model | `lg-ai-research` | `huggingface_model: LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct` | https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct | below the disclosed download floor (373,508); accepted because the cutoff bounds retrieval only |

## Parked — individually reasoned (203)

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
| `nod-ai/AMD-SHARK-Studio` | https://github.com/nod-ai/AMD-SHARK-Studio | 2026-09-07 | compilers | SKU: web UI over SHARK+IREE; iree is already a head product |
| `nunchux-ai/ComfyUI-nunchaku` | https://github.com/nunchux-ai/ComfyUI-nunchaku | 2026-09-07 | compilers | SKU: ComfyUI plugin surface of nunchaku, which this batch emits as its own row |
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
| `argmaxinc/whisperkit-coreml` | https://huggingface.co/argmaxinc/whisperkit-coreml | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding); also a Core ML conversion of Whisper rather than a distinct model |
| `autogluon/chronos-2` | https://huggingface.co/autogluon/chronos-2 | 2026-09-07 | — | no category fits: time-series forecasting model; also a mirror of amazon/chronos-2 under a second owner |
| `autogluon/chronos-2-small` | https://huggingface.co/autogluon/chronos-2-small | 2026-09-07 | — | no category fits: time-series forecasting model |
| `autogluon/chronos-bolt-small` | https://huggingface.co/autogluon/chronos-bolt-small | 2026-09-07 | — | no category fits: time-series forecasting model; also a mirror of amazon/chronos-bolt-small |
| `BAAI/bge-base-en-v1.5` | https://huggingface.co/BAAI/bge-base-en-v1.5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-large-en-v1.5` | https://huggingface.co/BAAI/bge-large-en-v1.5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-m3` | https://huggingface.co/BAAI/bge-m3 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-reranker-v2-m3` | https://huggingface.co/BAAI/bge-reranker-v2-m3 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-small-en-v1.5` | https://huggingface.co/BAAI/bge-small-en-v1.5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
| `BAAI/bge-small-zh-v1.5` | https://huggingface.co/BAAI/bge-small-zh-v1.5 | 2026-09-07 | — | no category fits: text-embedding or reranker model. The taxonomy has no retrieval-model category, so this needs a category-proposal issue before any tier can hold it |
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
| `farbodtavakkoli/OTel-2.0-LLM-31B-IT` | https://huggingface.co/farbodtavakkoli/OTel-2.0-LLM-31B-IT | 2026-09-07 | — | implausible signal, parked with the number: 6.9M 30-day downloads on a 31B model published under an individual account with no organization, no lineage on the card and no line I could resolve to a vendor. Parked for a person, not rejected |
| `farbodtavakkoli/OTel-LLM-27B-IT` | https://huggingface.co/farbodtavakkoli/OTel-LLM-27B-IT | 2026-09-07 | — | implausible signal, parked with the number: 6.9M 30-day downloads on a 31B model published under an individual account with no organization, no lineage on the card and no line I could resolve to a vendor. Parked for a person, not rejected |
| `farbodtavakkoli/OTel-LLM-E4B-IT` | https://huggingface.co/farbodtavakkoli/OTel-LLM-E4B-IT | 2026-09-07 | — | implausible signal, parked with the number: 6.9M 30-day downloads on a 31B model published under an individual account with no organization, no lineage on the card and no line I could resolve to a vendor. Parked for a person, not rejected |
| `google/vit-base-patch16-224` | https://huggingface.co/google/vit-base-patch16-224 | 2026-09-07 | — | no category fits: vision or vision-language backbone, detector or segmenter |
| `GuardrailsAI/prompt-saturation-attack-detector` | https://huggingface.co/GuardrailsAI/prompt-saturation-attack-detector | 2026-09-07 | — | SKU: a detector model published by the org behind head product guardrails-ai; a component of that product rather than a product |
| `hexgrad/Kokoro-82M` | https://huggingface.co/hexgrad/Kokoro-82M | 2026-09-07 | — | no category fits: speech or audio model (ASR, TTS, diarization, VAD, audio embedding) |
| `huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF` | https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF | 2026-09-07 | — | third-party derivative: a quantized, abliterated or repackaged redistribution of weights already represented on the map |
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
| `hailo.ai/products/ai-accelerators/hailo-8l-ai-accelerator/` | https://hailo.ai/products/ai-accelerators/hailo-8l-ai-accelerator/ | 2026-09-07 | edge_hardware | SKU: the lower-cost, DRAM-free variant of head product hailo-8. This is the amazon-nova-pro shape docs/reference/identity.md warns about |
| `kinara.ai/products/` | https://kinara.ai/products/ | 2026-09-07 | edge_hardware | fetch did not complete for a product page (404); Kinara's catalog appears to have moved after the NXP acquisition |
| `pine64.com/product-category/ox64/` | https://pine64.com/product-category/ox64/ | 2026-09-07 | edge_hardware | store category page rather than a product page; the Ox64 itself needs a product-level source before a row |
| `radxa.com/products/accessories/penta-sata-hat` | https://radxa.com/products/accessories/penta-sata-hat | 2026-09-07 | edge_hardware | boundary: a SATA storage HAT, not an inference board or chip |
| `radxa.com/products/aicore/ai-core-x` | https://radxa.com/products/aicore/ai-core-x | 2026-09-07 | edge_hardware | fetch did not complete (404); the Radxa AI Core X may exist under another path |
| `sima.ai/` | https://sima.ai/ | 2026-09-07 | edge_hardware | vendor root only; no product identity |
| `sima.ai/products/` | https://sima.ai/products/ | 2026-09-07 | edge_hardware | fetch did not complete for a product page (404 on /products/ and /modalix/; only the vendor root resolved). No product identity to write down yet |
| `tenstorrent.com/hardware/blackhole` | https://tenstorrent.com/hardware/blackhole | 2026-09-07 | edge_hardware | no category fits: PCIe accelerator cards for workstations and servers. This category is boards and chips that run inference at the edge, and the taxonomy has no datacenter-accelerator category -- needs a category-proposal issue |
| `www.blaize.com/products/` | https://www.blaize.com/products/ | 2026-09-07 | edge_hardware | vendor product index resolved but no product-level page did, so there is no single product identity to name on a row |
| `www.nxp.com/products/eIQ-Neutron-NPU` | https://www.nxp.com/products/eIQ-Neutron-NPU | 2026-09-07 | edge_hardware | fetch did not complete (404); and eIQ Neutron is a licensable NPU IP core rather than a board or chip a reader can buy, so the boundary is doubtful too |
| `www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Ora` | https://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-AIpro.html | 2026-09-07 | edge_hardware | fetch did not complete (connection failed, then 404 on two further paths); not recorded as a measured absence -- the Orange Pi AIpro is a real board and comes back next sweep |
| `www.rock-chips.com/a/en/products/RK35_Series/2024/0426/1711.html` | https://www.rock-chips.com/a/en/products/RK35_Series/2024/0426/1711.html | 2026-09-07 | edge_hardware | fetch did not complete (404 on two candidate paths for the RK3576 product page); not a measured absence |
| `www.seeedstudio.com/reComputer-J4012-p-5586.html` | https://www.seeedstudio.com/reComputer-J4012-p-5586.html | 2026-09-07 | edge_hardware | ambiguous identity: a carrier and enclosure around the NVIDIA Jetson Orin NX module, which is already the head product nvidia-jetson-orin-nx. Whether Seeed's reComputer is its own product or a packaging of that one is not settled by the page |

## Parked — below a disclosed retrieval cutoff (844)

Returned by the queries above but outside the predeclared cutoff, so not triaged individually.
Recorded here rather than dropped, with the cutoff that excluded them:

| source | signals | cutoff that excluded them |
|---|---|---|
| GitHub repository search | 504 | fewer than 1,000 all-time stars, or no push since 2025-09-07 |
| Hugging Face model API | 340 | fewer than 1,000,000 trailing-30-day downloads (ranked queries) or 5,000 (guard/safety/moderation searches) |

## Escalations for a person

1. **The taxonomy has no category for five large, heavily used model populations.** Text embedding
   and reranking models (18 candidates, led by `sentence-transformers/all-MiniLM-L6-v2` at 251M
   trailing-30-day downloads — more than any model on the map), speech and audio models (13),
   vision and vision-language backbones (9), generative image and video models (5), and time-series
   forecasters (5). All 50 are parked above against a `category-proposal` issue. This is the largest
   coverage gap the sweep found, and taxonomy is a governance event: this workflow does not open it.
2. **No category holds datacenter or workstation accelerators.** Tenstorrent's Blackhole cards are
   parked for this reason; `edge_hardware` is explicitly about the edge.
3. **An unresolved text-versus-vision boundary in `dataset_processing_tools`.** BlenderProc, fastdup
   and fiftyone are in scope by the letter of the category (synthetic-data generation,
   deduplication) but every product on the roster builds text or document corpora. Parked pending a
   boundary ruling rather than decided by a sweep.
4. **Two ledger holds re-surfaced and were not re-proposed:** `RyanCodrai/turbovec` and
   `FailproofAI/failproofai` both carry `unresolved` product_equivalence rulings in
   `sources/resolution_ledger.yaml`.
5. **Two open boundary questions in `compilers`:** `EnzymeAD/Enzyme` (automatic-differentiation
   compiler pass) and `llvm/circt` (hardware-EDA compiler).
6. **The warehouse discovery pool was unreachable** (no `OSO_API_KEY`). Re-running with warehouse
   access would likely consolidate signals this sweep treated as separate.

## Gates

- `uv run python -m build.validate` → `0 error(s), 2 warning(s)` (both warnings pre-existing
  `model_families` pattern-overlap notices, unchanged by this batch).
- `uv run python -m build.check_corpus_diff --base main` → no stage, gap, product-count or tier
  move in any category, and no untouched axis-assessment row rewritten. Registry rows are
  signal-only and invisible to the scored payload, which is why the sheet is empty; that is the
  expected result for a `tail-batch` PR and the reason no `stage-move` label is needed.
- `uv run pytest -q` → **6 failed, 1827 passed, 1 skipped**. All six failures are in
  `tests/test_identity_eval.py`, and every one of them repairs only by editing a corpus-wide
  generated fixture:

  | test | what it wants edited |
  |---|---|
  | `test_the_pass_fixture_tail_rows_match_the_corpus` | `tests/fixtures/identity_edges_pass.json` |
  | `test_write_fixture_is_idempotent` | `tests/fixtures/identity_edges_pass.json` |
  | `test_a_stale_fixture_tail_row_fails_the_floor_with_the_publish_lag_note` | `tests/fixtures/identity_edges_pass.json` |
  | `test_fixture_mode_does_not_grade_the_invariant` | `tests/fixtures/identity_edges_pass.json` |
  | `test_main_prints_a_coverage_line_per_route` | `tests/fixtures/identity_coverage_baseline.json` |
  | `test_the_live_corpus_is_at_or_above_the_committed_baseline` | `tests/fixtures/identity_coverage_baseline.json` |

  The cause is one thing, not six: 71 new tail rows add artifacts whose organizations declare no
  handle in `sources/org_handles.yaml`, so the coverage *denominators* grow while the numerators
  hold exactly — `github` 211/299 → 211/321, `huggingface` 51/62 → 51/75, `homepage_domain`
  6/27 → 6/48. Nothing lost a handle; the corpus got bigger. All 137 tests in that file pass on
  `main` (verified in a scratch worktree at 9df82a1), so this is caused by the batch and not
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
