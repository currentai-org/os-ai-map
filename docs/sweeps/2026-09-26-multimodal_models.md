# Multimodal models seed: 2026-09-26

## Scope and boundary

This batch seeds the preliminary `multimodal_models` category proposed in issue #9. It carries
identity-only registry rows and no head products; the category stays out of the published
payload until a promotion PR researches a first tranche of at least ten.

The membership test: is this a separately named vision or omni model line whose reason for fame
is visual or audio-visual understanding, so that listing it as a text LLM would mischaracterize
it? Natively multimodal general LLM families (Qwen3.5 and later, Gemma 3 and 4, Llama 4, Kimi K3,
GLM-5.x, DeepSeek-V4, MiniMax-M3, Inkling, Phi-4-multimodal, ERNIE-4.5-VL, Muse Glimmer) answer no
and stay in `base_pretrained` / `finetuned_chat`. The test matters because vendors are folding
vision into the main line: the Qwen-VL line has shipped no chat checkpoint since 2025-10-31, and
Alibaba calls Qwen3.5 "a native vision-language model".

Scope, as ruled in the 2026-09-26 decision record: understanding VLMs (image, document,
multi-image, video, and GUI or computer-use models), omni models (audio and video in, text or
speech out; `speech_audio` ruled them out, so this is their only home), and the four unified
understanding-and-generation models janus, bagel, emu and sensenova-u, which `media_generation`
agreed to leave here. No closed rows (see below).

Exclusions, by neighbor, are written out in full in the category's `comments`. In short:
OCR-first VLMs go to `document_conversion`; contrastive and embedding VLMs to
`embeddings_retrieval`; backbones, encoders and detection to `classic_ml_cv`; synthesized-asset
models to `media_generation`; speech-first models to `speech_audio`; VLA and embodied-reasoning
models to `robotics_embodied` / `world_models`; runtimes and harnesses to `inference_code` /
`evaluation_code`; agent apps built on a GUI model to `orchestration_agents`.

Placement and weights follow the decision record: taxonomy group Model components → Models,
weights 0.3 adoption / 0.7 capability, `scoring_recipe: {extends: model}`.

The full fetch trail (every fact with an `F`/`W` id, raw bodies, the two-pass audit) is on the
evidence branch `claude/research-multimodal_models` under `research/multimodal_models/`. The
fetch ids cited below refer to that trail.

## Inputs swept

All fetches were made on 2026-09-26 (UTC). The Hugging Face discovery pool was the top 200
`image-text-to-text` models by 30-day downloads and by likes, the top 100 by trending score, and
the top 100 `any-to-any` and `video-text-to-text` models by downloads, plus 27 WebSearch/WebFetch
calls, the OpenCompass Open VLM Leaderboard snapshot (data timestamp 2025-09-17) and per-family
Hub listings for every accepted row. That is a disclosed retrieval cutoff: a model outside those
lists and not surfaced by search was not seen. Adoption was read as rolling 30-day Hub downloads
summed over each vendor's own member checkpoints; no row has a package that is the product.

Three handle checks were added while seeding (F0246 `apple-aiml-research` is "Apple AI/ML
Research"; F0247 `VITA-MLLM` is an unverified group account; F0248 `vikhyatk` is Vik Korrapati's
personal account, a member of the `moondream` org).

## Reconciled counts

A raw signal is one mention of a candidate in one source, counted once per candidate per source.

```text
raw_signals       = 280
duplicate_signals = 164
unique_candidates = 116
accepted          = 47
parked            = 69

280 = 164 + 116
116 = 47 + 69
```

Of the 47: 30 image/document VLMs, 3 video VLMs, 4 GUI / computer-use models, 6 omni models and
4 unified models, from 35 organizations; the largest, `nvidia`, holds 4 rows (8.5%). 45 are
open-weights and 2 are open (Molmo, SmolVLM); 30 had a member checkpoint or repo push on or after
2025-09-26. The decision record added and removed nothing, so all 47 accepted rows are seeded.
No tail rows moved in or out of other registry files.

## Organizations and handles

Thirteen org slugs are new to the corpus. Each gets a minimal `sources/organizations/` record
with an empty roster, because `validate` requires one for any org that declares a handle: `ath-maas`, `bytedance-douyin`, `h-company`, `kuaishou`, `liquid-ai`, `m87-labs`,
`meituan`, `nyu-visionx`, `openmoss`, `rhymes-ai`, `sensetime`, `stepfun`, and `salesforce`
(already named by one `embeddings_retrieval` row). Each gets its GitHub and Hugging Face handles
in `sources/org_handles.yaml`. Eight existing orgs had no handle on a route these rows introduce
and get one: `ai2` (github and huggingface `allenai`), `apple` (github `apple-aiml-research`,
huggingface `apple`), `openbmb` (github `OpenBMB`), `moonshot-ai` (github `MoonshotAI`),
`zhipu-z-ai` (github `zai-org`), `inclusion-ai` (huggingface `inclusionAI`),
`shanghai-ai-laboratory` (github `OpenGVLab`) and `lmms-lab` (huggingface `lmms-lab`).

Not registered, on purpose: `VITA-MLLM` for `tencent` (a group account whose Tencent ownership is
not established; see the open question on VITA's org). Accounts that differ from an org's
existing handle on the same route (`NVlabs`, `baaivision`, `DAMO-NLP-SG`, `HuggingFaceM4`,
`LLaVA-VL`, `bytedance`, `ByteDance-Seed`, OpenGVLab on Hugging Face) were left for the
promotion PR, which reads each org's roster anyway.

## Should closed models be represented?

No closed row is seeded. The strongest closed VLMs are the general frontier models
`finetuned_chat` already carries (the OpenVLM snapshot's top of table is GPT-5, Gemini-2.5-Pro
and Claude), so under ADR-005 a VLM-specific closed row would be long tail. Vendors' closed API
tiers (Qwen-VL-Max, GLM-4v-Plus, Qwen3.5-Omni, Holo3-122B, Seed1.5-VL) are SKUs of an open row or
of a mapped product and are parked as such.

## Accepted candidates

| slug | display name | sub-type | org | primary source (identity) | fetched |
|---|---|---|---|---|---|
| `qwen-vl` | Qwen-VL | image/document VLM | `alibaba-cloud` | https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct | 2026-09-26 |
| `internvl` | InternVL | image/document VLM | `shanghai-ai-laboratory` | https://huggingface.co/OpenGVLab/InternVL3_5-8B | 2026-09-26 |
| `minicpm-v` | MiniCPM-V | image/document VLM | `openbmb` | https://huggingface.co/openbmb/MiniCPM-V-4.6 | 2026-09-26 |
| `molmo` | Molmo | image/document VLM | `ai2` | https://huggingface.co/allenai/Molmo2-8B | 2026-09-26 |
| `smolvlm` | SmolVLM | image/document VLM | `hugging-face` | https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct | 2026-09-26 |
| `idefics` | Idefics | image/document VLM | `hugging-face` | https://huggingface.co/HuggingFaceM4/Idefics3-8B-Llama3 | 2026-09-26 |
| `moondream` | Moondream | image/document VLM | `m87-labs` | https://huggingface.co/vikhyatk/moondream2 | 2026-09-26 |
| `florence-2` | Florence-2 | image/document VLM | `microsoft` | https://huggingface.co/microsoft/Florence-2-large | 2026-09-26 |
| `llava` | LLaVA | image/document VLM | `lmms-lab` | https://huggingface.co/lmms-lab/LLaVA-OneVision-1.5-8B-Instruct | 2026-09-26 |
| `kimi-vl` | Kimi-VL | image/document VLM | `moonshot-ai` | https://huggingface.co/moonshotai/Kimi-VL-A3B-Thinking-2506 | 2026-09-26 |
| `glm-v` | GLM-V | image/document VLM | `zhipu-z-ai` | https://huggingface.co/zai-org/GLM-4.6V | 2026-09-26 |
| `deepseek-vl` | DeepSeek-VL | image/document VLM | `deepseek` | https://huggingface.co/deepseek-ai/deepseek-vl2 | 2026-09-26 |
| `pixtral` | Pixtral | image/document VLM | `mistral-ai` | https://huggingface.co/mistralai/Pixtral-12B-2409 | 2026-09-26 |
| `aria` | Aria | image/document VLM | `rhymes-ai` | https://huggingface.co/rhymes-ai/Aria | 2026-09-26 |
| `nvlm` | NVLM | image/document VLM | `nvidia` | https://huggingface.co/nvidia/NVLM-D-72B | 2026-09-26 |
| `nemotron-vl` | Nemotron Nano VL | image/document VLM | `nvidia` | https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-BF16 | 2026-09-26 |
| `eagle` | Eagle | image/document VLM | `nvidia` | https://huggingface.co/nvidia/Eagle2.5-8B | 2026-09-26 |
| `ovis` | Ovis | image/document VLM | `ath-maas` | https://huggingface.co/ATH-MaaS/Ovis2.6-30B-A3B | 2026-09-26 |
| `keye-vl` | Keye-VL | image/document VLM | `kuaishou` | https://huggingface.co/Kwai-Keye/Keye-VL-2.0-30B-A3B | 2026-09-26 |
| `step-vl` | Step3-VL | image/document VLM | `stepfun` | https://huggingface.co/stepfun-ai/Step3-VL-10B | 2026-09-26 |
| `paligemma` | PaliGemma | image/document VLM | `google` | https://huggingface.co/google/paligemma2-3b-mix-224 | 2026-09-26 |
| `blip` | BLIP | image/document VLM | `salesforce` | https://huggingface.co/Salesforce/blip2-opt-2.7b | 2026-09-26 |
| `lfm-vl` | LFM-VL | image/document VLM | `liquid-ai` | https://huggingface.co/LiquidAI/LFM2.5-VL-1.6B | 2026-09-26 |
| `aya-vision` | Aya Vision | image/document VLM | `cohere` | https://huggingface.co/CohereLabs/aya-vision-8b | 2026-09-26 |
| `north-vision` | North Micro Vision | image/document VLM | `cohere` | https://huggingface.co/CohereLabs/North-Micro-Vision-Instruct | 2026-09-26 |
| `fastvlm` | FastVLM | image/document VLM | `apple` | https://huggingface.co/apple/FastVLM-7B | 2026-09-26 |
| `mimo-vl` | MiMo-VL | image/document VLM | `xiaomi` | https://huggingface.co/XiaomiMiMo/MiMo-VL-7B-RL-2508 | 2026-09-26 |
| `cambrian` | Cambrian | image/document VLM | `nyu-visionx` | https://huggingface.co/nyu-visionx/Cambrian-S-7B | 2026-09-26 |
| `perception-lm` | Perception LM | image/document VLM | `meta` | https://huggingface.co/facebook/Perception-LM-8B | 2026-09-26 |
| `sail-vl` | SAIL-VL | image/document VLM | `bytedance-douyin` | https://huggingface.co/BytedanceDouyinContent/SAIL-VL2-8B | 2026-09-26 |
| `videollama` | VideoLLaMA | video VLM | `alibaba-damo-academy` | https://huggingface.co/DAMO-NLP-SG/VideoLLaMA3-7B | 2026-09-26 |
| `internvideo` | InternVideo | video VLM | `shanghai-ai-laboratory` | https://huggingface.co/OpenGVLab/InternVideo2_5_Chat_8B | 2026-09-26 |
| `moss-vl` | MOSS-VL | video VLM | `openmoss` | https://huggingface.co/OpenMOSS-Team/MOSS-VL-Instruct-0708 | 2026-09-26 |
| `ui-tars` | UI-TARS | GUI / computer use | `bytedance-seed-volcano-engine` | https://huggingface.co/ByteDance-Seed/UI-TARS-1.5-7B | 2026-09-26 |
| `ui-venus` | UI-Venus | GUI / computer use | `inclusion-ai` | https://huggingface.co/inclusionAI/UI-Venus-2-9B | 2026-09-26 |
| `holo` | Holo | GUI / computer use | `h-company` | https://huggingface.co/Hcompany/Holo-3.1-35B-A3B | 2026-09-26 |
| `fara` | Fara | GUI / computer use | `microsoft` | https://huggingface.co/microsoft/Fara1.5-27B | 2026-09-26 |
| `qwen-omni` | Qwen-Omni | omni | `alibaba-cloud` | https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct | 2026-09-26 |
| `minicpm-o` | MiniCPM-o | omni | `openbmb` | https://huggingface.co/openbmb/MiniCPM-o-4_5 | 2026-09-26 |
| `nemotron-omni` | Nemotron Nano Omni | omni | `nvidia` | https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 | 2026-09-26 |
| `ming-omni` | Ming-Omni | omni | `inclusion-ai` | https://huggingface.co/inclusionAI/Ming-flash-omni-2.0 | 2026-09-26 |
| `longcat-omni` | LongCat-Flash-Omni | omni | `meituan` | https://huggingface.co/meituan-longcat/LongCat-Flash-Omni | 2026-09-26 |
| `vita` | VITA | omni | `tencent` | https://huggingface.co/VITA-MLLM/VITA-1.5 | 2026-09-26 |
| `janus` | Janus | unified understanding + generation | `deepseek` | https://huggingface.co/deepseek-ai/Janus-Pro-7B | 2026-09-26 |
| `bagel` | BAGEL | unified understanding + generation | `bytedance-seed-volcano-engine` | https://huggingface.co/ByteDance-Seed/BAGEL-7B-MoT | 2026-09-26 |
| `emu` | Emu | unified understanding + generation | `baai` | https://huggingface.co/BAAI/Emu3.5 | 2026-09-26 |
| `sensenova-u` | SenseNova-U | unified understanding + generation | `sensetime` | https://huggingface.co/sensenova/SenseNova-U1.5-8B-MoT | 2026-09-26 |


## Identity notes for promotion

- **Governing release.** Three lines span two licenses or an open and a closed tier, and the
  product's openness depends on which release governs: `qwen-omni` (Qwen3-Omni is Apache-2.0;
  Qwen3.5-Omni was released as proprietary, W0017, with no weights under `author=Qwen`, F0244),
  `moondream` (Moondream 2 is Apache-2.0; 3.x carries the Moondream Model License 1.0, W0027) and
  `pixtral` (12B Apache-2.0; Large under the Mistral Research License MRL-0.1, F0186).
- **Custom weights licenses** the shared tiers do not name, for the maintainer's single
  license-rulings issue (the products are deferred at promotion until it rules): DeepSeek
  License v1.0 (`deepseek-vl`, `janus`), MRL-0.1 (`pixtral` Large), NVIDIA Open Model License
  (`nemotron-vl`), NVIDIA Open Model Agreement (`nemotron-omni`), NVIDIA `nsclv1` (`eagle`, text
  gated), Gemma Terms of Use (`paligemma`), CC-BY-NC-4.0 (`nvlm`, `aya-vision`), FAIR
  non-commercial research (`perception-lm`, text gated), Apple ML Research Model license
  (`fastvlm`), LFM Open License v1.0 (`lfm-vl`, revenue cap), Moondream Model License 1.0,
  VITA1.5 terms (`vita`), and the Qwen license on InternVL3-78B (`internvl`).
- **`ui-venus`** is seeded although its weight license is "pending final confirmation" (F0195)
  and the repo has no LICENSE file; re-check before promotion.
- **`llava`** declares the current lmms-lab release (`lmms-lab/LLaVA-OneVision-1.5-8B-Instruct`),
  but most LLaVA usage runs through Hugging Face's `llava-hf` conversions (F0021 against F0020).
  Adoption research at promotion should sum both.
- **`qwen-vl`** keeps its row as the category's adoption leader; its successor is the mapped
  `qwen` family, which the product's prose should say. Use `end_of_life` only if Alibaba
  announces one.
- **`perception-lm`** declares no `github`: it shares `facebookresearch/perception_models` with
  the `perception-encoder` tail row in `embeddings_retrieval`.
- **`florence-2`** and **`internvideo`** sit here on their chat and prompt-driven checkpoints; the
  InternVideo encoders belong in `classic_ml_cv`.
- **`blip`** folds xGen-MM (same Salesforce lab); BLIP3o and BLIP3o-NEXT are a generation line
  and are parked toward `media_generation`. The newest BLIP/BLIP-2 checkpoint is 2023-08-23.
- **`vita`**: the newest-looking 2026 checkpoints are VITA-QinYu (audio-to-audio), not a member.
- **Model-family bridges.** `qwen-vl`, `qwen-omni`, `deepseek-vl`, `glm-v`, `kimi-vl`,
  `nemotron-vl` and `nemotron-omni` all match an existing `sources/model_families.yaml` pattern
  (`qwen-*`, `deepseek-*`, `glm-*`, `kimi-*`, `nemotron-*`) that bridges release names to the
  general family. That is the same position `deepseek-ocr` and `nemotron-embed` are in today.
  At promotion, decide whether each sub-line needs its own family entry (`qwen-vl-*` and so on,
  longest match wins) so a release such as `qwen-vl-max` does not resolve to `qwen`.

## Parked candidates

Each reason cites the evidence ids on the evidence branch.

| candidate | reason | source URL | fetched |
|---|---|---|---|
| Qwen3.5 / Qwen3.6 / Qwen3.8 (native VL) | already mapped: `qwen` (base_pretrained). Vendor calls Qwen3.5 'a native vision-language model'; Qwen3.6-27B pipeline image-text-to-text. Stay. | https://huggingface.co/api/models/Qwen/Qwen3.6-27B | 2026-09-26 |
| Gemma 3 / Gemma 4 (vision, any-to-any E2B/E4B) | already mapped: `gemma`. gemma-4-31B-it is image-text-to-text, Apache-2.0 (F0223); E2B/E4B/12B any-to-any (F0003). Stay. | https://huggingface.co/api/models/google/gemma-4-31B-it | 2026-09-26 |
| Llama 3.2 Vision / Llama 4 Scout, Maverick | SKU of `llama` (Llama-3.2-11B/90B-Vision, Llama-4 image-text-to-text). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Phi-3.5-vision / Phi-4-multimodal | SKU of `phi`: card lists multimodal-instruct among the Phi-4 family (F0218). | https://huggingface.co/microsoft/Phi-4-multimodal-instruct | 2026-09-26 |
| ERNIE-4.5-VL | SKU of `ernie`: card presents it among 'ERNIE 4.5 models' with joint multimodal MoE pretraining (F0219). | https://huggingface.co/baidu/ERNIE-4.5-VL-28B-A3B-PT | 2026-09-26 |
| Kimi K3 / K2.5 / K2.6 (image-text-to-text) | already mapped: `kimi` (F0225). | https://huggingface.co/api/models/moonshotai/Kimi-K3 | 2026-09-26 |
| GLM-5.3-Flash / GLM-5V-Turbo | already mapped: `glm`; GLM-5.3-Flash image-text-to-text (F0224). | https://huggingface.co/api/models/zai-org/GLM-5.3-Flash | 2026-09-26 |
| DeepSeek-V4-Flash-Vision-Exp / V4.1-Flash | SKU of `deepseek`. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| Inkling (Thinking Machines) | already mapped: `inkling` (base_pretrained). | https://huggingface.co/blog/state-of-open-models-summer-2026 | 2026-09-26 |
| MiniMax-M3 | already mapped: `minimax`. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| MiniCPM5 | already mapped: `minicpm` (text line). | https://huggingface.co/api/models?author=openbmb&search=MiniCPM-o | 2026-09-26 |
| Muse Glimmer (Meta, 30B, Apache-2.0) | boundary -> finetuned_chat / base_pretrained: agentic general model 'with built-in vision support' (W0011). Absent from the map: flag to maintainer. | https://venturebeat.com/technology/meta-returns-to-open-source-with-muse-glimmer-an-apache-2-0-licensed-30b-parameter-ai-model-optimized-for-agents-available-now | 2026-09-26 |
| Step-3.7-Flash (StepFun) | boundary -> finetuned_chat (general flagship, image-text-to-text). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Ling-3.0-flash-VL (inclusionAI) | SKU of the Ling family (absent from map). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=trendingScore&direction=-1&limit=100 | 2026-09-26 |
| Apriel-1.5-15b-Thinker (ServiceNow) | boundary -> finetuned_chat (general reasoning model with vision). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| HyperCLOVAX-SEED-Think-32B (Naver) | boundary -> finetuned_chat. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Apertus-v1.5-8B (Swiss AI) | boundary -> base_pretrained (general LLM listed under image-text-to-text). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| Command A Vision (Cohere) | SKU of tail `command-a`. | https://huggingface.co/api/models?author=CohereLabs&search=vision | 2026-09-26 |
| Seed1.5-VL (Doubao vision API) | closed; SKU of mapped `doubao-seed` (API model id doubao-1-5-thinking-vision-pro, W0024). | https://github.com/ByteDance-Seed/Seed1.5-VL | 2026-09-26 |
| Qwen3.5-Omni / Qwen3.8-Omni-Flash | closed tier of `qwen-omni`: Qwen3.5-Omni 'released ... as proprietary' (W0017); no Qwen3.5- or Qwen3.8-Omni weights under author=Qwen (F0244, only Qwen2.5-/Qwen3-Omni). | https://www.marktechpost.com/2026/03/30/alibaba-qwen-team-releases-qwen3-5-omni-a-native-multimodal-model-for-text-audio-video-and-realtime-interaction/ | 2026-09-26 |
| Holo3-122B-A10B | SKU of `holo` (API-only flagship, W0026). | https://hcompany.ai/holo3.1 | 2026-09-26 |
| Qwen-VL-Max / Qwen-VL-Plus | closed API tier of `qwen-vl` (OpenVLM snapshot). | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| GLM-4v-Plus | closed API tier of `glm-v` (OpenVLM snapshot). | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| SenseNova-V6 / V6.5-Pro | closed long-tail (OpenVLM, OpenSource=No). | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| Step-1o / Step-1.5V | closed long-tail (OpenVLM, OpenSource=No). | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| HunYuan-Standard-Vision | closed long-tail (OpenVLM, OpenSource=No). | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| CongRong-v2.0 | closed long-tail (OpenVLM, OpenSource=No). | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| GPT-5 / Gemini-2.5-Pro / Claude 3.7 Sonnet (leaderboard top) | already mapped: `gpt-5`, `gemini-pro`, `claude-sonnet` (finetuned_chat). | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| InternVL-U | SKU of `internvl` (4B unified understanding+generation variant, W0013). | https://github.com/OpenGVLab/InternVL-U | 2026-09-26 |
| CogVLM2 / CogAgent / GLM-Edge-V | SKU (predecessors) of `glm-v`. | https://huggingface.co/api/models?author=zai-org&search=V | 2026-09-26 |
| BLIP3o / BLIP3o-NEXT (Salesforce) | boundary -> media_generation (generation and editing line; 2025-11 checkpoints). | https://huggingface.co/api/models?author=Salesforce&search=blip | 2026-09-26 |
| xGen-MM (Salesforce) | SKU of `blip` (proposed fold; same vendor lab, 1,772 / 30d). | https://huggingface.co/api/models?author=Salesforce&search=xgen-mm | 2026-09-26 |
| Qwen2.5-VL-7B-Instruct-NVFP4 (nvidia) | SKU of `qwen-vl` (third-party quantization). | https://huggingface.co/api/models?author=nvidia&search=VL | 2026-09-26 |
| Llama-3.1-Nemotron-Nano-VL-8B | member of `nemotron-vl`. | https://huggingface.co/api/models?author=nvidia&search=VL | 2026-09-26 |
| VideoChat-Flash / VideoChat-R1 / VideoChat3 | identity unclear: OpenGVLab and MCG-NJU both publish VideoChat checkpoints (F0004); not resolved this run. | https://www.alphaxiv.org/abs/2607.14935 | 2026-09-26 |
| AutoGLM-Phone-9B | identity unclear (phone agent model; relation to GLM-V not verified). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Qianfan-VL (Baidu) | identity unclear (separately named 3B/8B; not researched beyond listing, 539 / 30d). | https://huggingface.co/api/models?author=baidu&search=VL | 2026-09-26 |
| JoyAI-VL-Interaction (JD) | identity unclear (not researched beyond listing). | https://huggingface.co/api/models?pipeline_tag=video-text-to-text&sort=downloads&direction=-1&limit=100 | 2026-09-26 |
| Marlin-2B (NemoStation) | identity unclear (not researched beyond listing). | https://huggingface.co/api/models?pipeline_tag=video-text-to-text&sort=downloads&direction=-1&limit=100 | 2026-09-26 |
| ZDTaichu5.0-9B (TaichuAI) | identity unclear (not researched beyond listing). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Mage-VL (Microsoft) | identity unclear (not researched beyond listing). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| LensVLM-9B (Apple) | identity unclear (not researched beyond listing). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=trendingScore&direction=-1&limit=100 | 2026-09-26 |
| LocateAnything-3B (NVIDIA) | identity unclear (grounding model; possible classic_ml_cv). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| OpenOmni (academic, NeurIPS 2025) | no addressable model artifact verified this run. | https://github.com/RainBowLuoCS/OpenOmni | 2026-09-26 |
| Show-o2 / MMaDA | not verified this run; unified gen models, contested with media_generation. | https://arxiv.org/pdf/2506.15564 | 2026-09-26 |
| Cosmos-Reason 1/2 (NVIDIA) | boundary -> robotics_embodied / world_models (928,415 / 30d). | https://huggingface.co/api/models?author=nvidia&search=Cosmos-Reason | 2026-09-26 |
| MolmoAct / MolmoAct2 (Ai2) | boundary -> robotics_embodied (pipeline robotics). | https://huggingface.co/api/models?author=allenai&search=Molmo | 2026-09-26 |
| HY-Embodied-0.5 (Tencent) | boundary -> robotics_embodied. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Isaac (Perceptron) | boundary -> robotics_embodied: Isaac 0.5 is 'for video understanding, embodied reasoning, and robot control' (W0025); HF pipeline robotics (F0061); repo perceptron-ai-inc/isaac (F0229). | https://huggingface.co/PerceptronAI/Isaac-0.5 | 2026-09-26 |
| MedGemma | boundary -> scientific_ai_models (domain model; absent from map). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| diffusiongemma / omni-dreams | boundary -> media_generation. | https://huggingface.co/api/models?author=nvidia&search=Omni | 2026-09-26 |
| chandra / chandra-ocr-2 (Datalab) | boundary -> document_conversion. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| surya-ocr-2 (Datalab) | boundary -> document_conversion. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| Unlimited-OCR / Qianfan-OCR (Baidu) | boundary -> document_conversion. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| HunyuanOCR | boundary -> document_conversion. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| GOT-OCR2.0 (StepFun) | boundary -> document_conversion. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| Nanonets-OCR / OCR2 | boundary -> document_conversion. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| LightOnOCR-2 | boundary -> document_conversion. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| PaddleOCR-VL | SKU of mapped `paddleocr` (document_conversion). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| granite-docling / SmolDocling | boundary -> document_conversion (next to mapped `docling`). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| MinerU2.5 | SKU of mapped `mineru`. | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| RolmOCR / OCRFlux / Dolphin / OvisOCR2 / typhoon-ocr / jina-ocr / TeleOCR | boundary -> document_conversion (class of OCR-first VLMs). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| dots.ocr / DeepSeek-OCR / olmOCR | already mapped (document_conversion). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| nemotron-colembed-vl / llama-nemotron-embed-vl / rerank-vl / omni-embed-nemotron | boundary -> embeddings_retrieval. | https://huggingface.co/api/models?author=nvidia&search=VL | 2026-09-26 |
| Ming-omni-tts / Ming-UniAudio / Step-Audio-2-mini / A.X-K2-Raon-Speech / moondream parakeet / VITA-QinYu | boundary -> speech_audio. | https://huggingface.co/api/models?pipeline_tag=any-to-any&sort=downloads&direction=-1&limit=100 | 2026-09-26 |
| UI-TARS-desktop | boundary -> orchestration_agents (agent app, software). | https://themenonlab.blog/blog/ui-tars-desktop-open-source-gui-agent | 2026-09-26 |
| OmniParser (Microsoft) | boundary -> orchestration_agents / classic_ml_cv (screen parser, not a VLM). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| vllm-omni / mlx-vlm / lmms-eval / VLMEvalKit | already mapped (vllm, mlx-vlm, lmms-eval, vlmevalkit). | https://github.com/vllm-project/vllm-omni | 2026-09-26 |
| Community fine-tunes and quantizations (unsloth, DavidAU, HauhauCS, bartowski, lmstudio-community ...) | not products: derivatives of mapped families (class). | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |

## Open questions left for the maintainer

1. **VITA's org.** The weights' License.txt names Tencent (THL A29) as copyright holder, while
   OpenCompass credits NJU and credits Long-VITA to Tencent Youtu Lab and Nanjing University. The
   row uses `tencent`, the weights' licensor; `nanjing-university` or a joint org are the
   alternatives.
2. **`ath-maas`.** The Ovis repo moved from `AIDC-AI/Ovis` to `ATH-MaaS/Ovis` (F0110, F0230).
   Who stands behind the renamed account, and so whether the row belongs under an existing
   org, was not established in this sweep, so the org record says `type: unknown`.
3. **`bytedance-douyin`.** Seeded as its own org. If the Douyin content team is the same legal
   entity as `bytedance-seed-volcano-engine`, fold it at promotion.
4. **Ladder choice per row.** The category extends the fine-tuned `model` ladder because most
   rows train a vision stack onto another vendor's LLM. Rows trained from scratch may want the
   `pretrained` ladder; the promotion PR decides with evidence.
5. **Capability quantity.** The sweep proposes breadth of grounded understanding (single-image
   perception; documents and multi-image; video and long context; acting on what it sees; omni
   in; omni in with speech out) over MMMU, whose test answers are public since 2026-02-12, and
   over the OpenCompass leaderboard, which covers 25 of the 47 rows and stops at 2025-09-17.
6. **Follow-ups not seeded here:** embodied-reasoning VLMs with no action head (RynnBrain,
   Hy-Embodied VLM, UnifoLM-ER) wait for their own sweep; OCR-first VLMs go to
   `document_conversion` in a follow-up; the nine identity-unclear listings above (VideoChat,
   AutoGLM-Phone, Qianfan-VL, JoyAI-VL, Marlin, ZDTaichu, Mage-VL, LensVLM, LocateAnything) need
   a live identity check before they can be accepted or ruled out.
7. **Muse Glimmer** (Meta, Apache-2.0, 30B) is absent from the map entirely; it belongs in
   `finetuned_chat` or `base_pretrained`, not here.
