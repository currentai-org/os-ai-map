# Multimodal models sweep — 2026-09-26

Dir slug `multimodal_models`, proposed category slug `multimodal_models`, issue #9 (Brief 2).
Every fact below carries a fetch id: `Fnnnn` rows are in `fetch-log.tsv` (bodies in `raw/`),
`Wnnnn` rows are WebSearch/WebFetch calls in `web-log.tsv`. All fetches were made on 2026-09-26
UTC. The non-200 ids cited in sections 6b and 7 (F0177, F0182, F0191, F0193, F0194,
F0205-F0207, F0211-F0213) show only that a file was gated or absent. None of them is the source
of a license or a number. Web-log timestamps were stamped when each batch of calls was logged,
not per call, so several W rows share a second. All of them fall on 2026-09-26.

Retrieval cutoff (a coverage limit, not a filter): the Hugging Face discovery pool was the top
200 `image-text-to-text` models by 30-day downloads and by likes (F0001, F0002), the top 100
by trending score (F0005), and the top 100 `any-to-any` (F0003) and `video-text-to-text`
(F0004) by downloads, plus 27 WebSearch/WebFetch calls. Models outside those lists and not
surfaced by search were not seen. Void fetches: F0077, F0079, F0083, F0097, F0101, F0103,
F0105, F0115, F0121, F0127, F0129, F0131, F0153, F0155 and F0157 were malformed requests (an
empty model id from a shell field-splitting bug) and returned an unrelated listing; they back no
claim and were redone as F0159-F0173. The matching F0078, F0080, F0084, F0098, F0102, F0104,
F0106, F0116, F0122, F0128, F0130, F0132, F0154, F0156 and F0158 are ecosyste.ms 404s for Hub
ids sent as repo names by the same bug; they are void too. The genuine repo 404s were F0074
(OpenBMB/MiniCPM-o), F0082 (vikhyat/moondream), F0110 (AIDC-AI/Ovis) and F0138
(apple/ml-fastvlm). ungh.cc resolved them to their canonical names (F0174, F0175, F0230, F0176).
F0227 died before the transfer (HTTP 000) and was redone as F0229.

## 1. Verdict

**GO-WITH-CHANGES.** Supply is not the problem. 47 candidates clear the bar with an addressable
Hugging Face artifact and a live usage number, from 35 organizations, and no org holds more than
4 rows. The problem is that the category is losing its crux. The most-downloaded
image-text-to-text models on the Hub today are the general LLM families the map already carries.
Qwen3.5 and later, Gemma 4, Kimi K3, GLM-5.3-Flash, DeepSeek-V4-Flash, MiniMax-M3 and Inkling
are all tagged image-text-to-text (F0001, F0223-F0226). Alibaba calls Qwen3.5 "a native
vision-language model" that outperforms Qwen3-VL (W0010), and the Qwen-VL line has not shipped
a checkpoint since 2025-10-31 (F0006). So the category works only if the membership test is
"separately marketed as a vision/omni model", with the frontier general models staying in
`base_pretrained`/`finetuned_chat`. The changes I recommend: (a) take the understanding-VLM
scope with GUI/computer-use and video VLMs inside it, which is 37 rows and clears the bar by
itself; (b) put omni models in too (6 rows), because nothing else on the map owns them and
`speech_audio` already ruled them out; (c) keep the four unified understanding+generation models
contested with `media_generation` until that sweep rules; (d) settle the SKU-vs-row question for
vendor sub-lines (Nemotron VL/Omni, PaliGemma, Qwen-VL) before seeding (section 9).

## 2. Fit metrics (computed from section 6, not estimated)

- accepted candidates: **47** (open: 2, open-weights: 45, source-available: 0, closed: 0)
  - understanding-VLM scope only (image VLMs 30 + video 3 + GUI/computer-use 4): **37**
  - omni (any-to-any input, text/speech out): **6**; unified understanding+generation: **4**
- independent organizations: **35**; largest org's share: **8.5%** (nvidia, 4 of 47: nvlm,
  nemotron-vl, eagle, nemotron-omni). Understanding-only scope: 31 orgs, nvidia 3 of 37 (8.1%).
- candidates active in the last 12 months: **30** of 47. The rule is one test: the newest
  vendor member checkpoint, or a push to a non-archived repo, dated on or after 2025-09-26. HF
  lastModified is not counted, because a card edit is not a release. Dormant (17): smolvlm,
  idefics, florence-2, kimi-vl, deepseek-vl, pixtral, aria, nvlm, paligemma, blip, aya-vision,
  mimo-vl, perception-lm, sail-vl, videollama, vita, janus. Understanding-only scope: 22 of 37
  active.
- candidates with a usage instrument (HF 30-day downloads) as opposed to stars only: **47** of 47.
  None has a PyPI/npm package that *is* the product, so no package is declared.
- retrieval cutoff: see the header. It excluded anything below the top-200 or top-100 lists that
  search did not surface. 9 listing-only models were seen but not researched and are parked as
  "identity unclear" (section 7) instead of being rejected.

## 3. Boundary

**Definition.** Models whose headline capability is understanding non-text input (images,
documents, screens, video, and for omni models audio too) and producing text or actions about
it, marketed as a vision or omni model line separate from the vendor's general LLM.

**Litmus.** Is this a separately named vision/omni model line whose reason for fame is visual
(or audio-visual) understanding, so that listing it as a text LLM would mischaracterize it? A
natively multimodal *general* model (Qwen3.5+, Gemma 4, Llama 4, Kimi K3) answers no: it is
famous as the LLM and stays in its family row.

**Explicit exclusions.**
- Natively multimodal general LLM families: `base_pretrained` / `finetuned_chat` (qwen, gemma,
  llama, kimi, glm, deepseek, minimax, inkling, phi, ernie, muse-spark).
- OCR-first and document-parsing VLMs (dots.ocr, DeepSeek-OCR, olmOCR, PaddleOCR-VL, chandra,
  HunyuanOCR, GOT-OCR2 ...): `document_conversion`. Their capability quantity there is "how much
  of a document survives", which a general VLM ladder does not measure.
- Contrastive/embedding vision-language models (CLIP, OpenCLIP, SigLIP, ColPali, ModernVBERT,
  Nemotron embed-VL): `embeddings_retrieval`. Test: the output is a vector or a relevance score,
  not text.
- Vision backbones and classic CV (timm, DINO, video encoders): `classic_ml_cv` (sibling).
- Image/video/3D generation: `media_generation` (sibling).
- Speech-first ASR/TTS/S2S: `speech_audio`, which ruled omni models out (RUNBOOK Brief 0).
- Vision-language-action and embodied reasoning (MolmoAct, Cosmos-Reason, Isaac 0.5,
  HY-Embodied): `robotics_embodied` / `world_models` (siblings).
- Runtimes and eval tooling (vLLM-Omni, MLX-VLM, lmms-eval, VLMEvalKit): stay in
  `inference_code` / `evaluation_code`.
- Agent apps built on a GUI VLM (UI-TARS-desktop): `orchestration_agents`. The model stays here.

**Contested products.**

| product | where it is now | recommendation | reason |
|---|---|---|---|
| qwen / gemma / llama / kimi / glm (native multimodal generations) | base_pretrained | stay | Famous as the LLM. The VL sub-lines that have their own name and repo (qwen-vl, glm-v, kimi-vl, paligemma) are proposed as rows here. |
| phi (Phi-3.5-vision, Phi-4-multimodal) | base_pretrained | stay (park the VL SKUs) | Microsoft lists multimodal-instruct inside the Phi-4 family (F0218). No separate line. |
| ernie (ERNIE-4.5-VL) | base_pretrained | stay (park SKU) | Shipped as one of the "ERNIE 4.5 models" (F0219). |
| nemotron (Nemotron 3) | finetuned_chat | stay; add nemotron-vl and nemotron-omni here | The Omni card says "part of the Nemotron model family" (F0221). The precedent for separate rows is nemotron-embed / nemotron-rerank. Maintainer call (section 9, Q3). |
| minicpm | base_pretrained | stay; add minicpm-v and minicpm-o here | Own repo, OpenBMB/MiniCPM-V (F0072), distinct from OpenBMB/MiniCPM. |
| colpali, siglip, clip, openclip, modernvbert | embeddings_retrieval | stay | Output is an embedding. |
| deepseek-ocr, dots-ocr, olmocr, paddleocr, mineru | document_conversion | stay | OCR-first. The same rule parks the 19 unmapped OCR-first models found here (12 section-7 rows, 24 names: 3 already mapped, PaddleOCR-VL and MinerU2.5 SKUs of mapped products). |
| mlx-vlm, lmms-eval, vlmevalkit | inference_code / evaluation_code | stay | Software, not models. |
| janus, bagel, emu, sensenova-u | absent | contested with media_generation (sibling): flag, don't resolve | Unified understanding+generation models. Recommend: here if media_generation's litmus ("is the output a synthesized asset?") is read as the *headline* output. Janus-Pro's card tags text-to-image (F0095). |
| emu (Emu3.5) | absent | also contested with world_models (sibling) | Tagged any-to-any (F0049). |
| florence-2, internvideo | absent | contested with classic_ml_cv (sibling) | Florence-2 is "an advanced vision foundation model that uses a prompt-based approach" for captioning, detection and segmentation (F0243). The InternVideo repo also ships video encoders (F0009). The chat checkpoints belong here; the encoders belong in classic_ml_cv. |
| qwen-omni, minicpm-o, nemotron-omni, ming-omni, longcat-omni, vita | absent | here (omni scope) | speech_audio ruled "chat-first audio LLMs and omni models" out, so this is the only home. |
| ui-tars, ui-venus, holo, fara | absent | here | GUI/computer-use VLMs: models, not agent frameworks. |
| cosmos-reason, isaac, molmoact | absent | robotics_embodied / world_models (siblings) | Embodied reasoning / robot control (W0025, F0012, F0062). |
| perception-encoder (tail) | embeddings_retrieval registry | stay | Shares the facebookresearch/perception_models repo with perception-lm, which is why no github is declared on perception-lm. |

## 4. Capability quantity

**No single leaderboard orders the set.** The issue suggests MMMU. The best machine-readable
aggregate is the OpenCompass Open VLM Leaderboard JSON (F0215). It covers **25 of 47**
accepted families (qwen-vl, internvl, minicpm-v, minicpm-o, molmo, smolvlm, idefics, moondream,
llava, kimi-vl, glm-v, deepseek-vl, janus, pixtral, aria, nvlm, eagle, ovis, paligemma, blip,
mimo-vl, emu, vita, cambrian, sail-vl), but its data timestamp is 2025-09-17, so it misses every
2026 release. It also has nothing for the GUI or omni rows. The MMMU site itself released
test-set answers on 2026-02-12 (F0216), which makes new MMMU claims contamination-prone. Its
leaderboard table is script-rendered and did not come through the fetch.

The quantity that orders the whole set, including omni and GUI, is **breadth of grounded
understanding**. Each rung nests the one below. Examples without a fetch id are illustrative
placements for the ladder-builder, not verified capability claims.

1. **Single-image perception.** Captioning, VQA, detection prompts on one image (BLIP's
   captioning and VQA checkpoints are tagged image-to-text and visual-question-answering, F0039;
   Florence-2 "captioning, object detection, and segmentation", F0243; PaliGemma illustrative).
2. **Documents and multi-image.** OCR-grade text reading, charts, several images interleaved
   (North Micro Vision: "document understanding, charts, tables, and visual grounding", W0009;
   Idefics, SmolVLM, Moondream and Aya Vision illustrative).
3. **Video and long context.** Temporal understanding over long video (Qwen-VL: Qwen3-VL's
   "Native 256K context, expandable to 1M; handles books and hours-long video", F0240;
   VideoLLaMA and MOSS-VL are tagged video-text-to-text, F0004; InternVL and MiniCPM-V
   illustrative).
4. **Acting on what it sees.** Grounded actions or native tool calls from visual input (UI-TARS
   "pixels in and actions out", W0018; Holo, W0026; Fara and UI-Venus illustrative; GLM-V's
   "native Function Calling", F0241).
5. **Omni in.** Audio and video understood natively alongside images and text, with text out
   (Nemotron Nano Omni, whose card gives output type Text, F0221; LongCat-Flash-Omni and
   Ming-Omni are tagged any-to-any, F0003/F0054).
6. **Omni in, speech out.** Rung 5 plus streaming speech generation (Qwen-Omni: Qwen3-Omni
   "delivers real-time streaming responses in both text and natural speech", F0242; MiniCPM-o
   4.5 "full-duplex multimodal live streaming", W0015).

**Top-rung anchor: `qwen-omni`.** If omni is excluded, rung 4 is the top and `ui-tars` anchors
it.
Within a rung, a benchmark average (OpenCompass or MMMU-Pro) can break ties where it exists.
This ladder is a sketch for the ladder-builder. It is not a scored claim about any product.

## 5. Scoring ladder inputs

- Shared ladders: every accepted row is a `model` and needs the **pretrained** ladder when the
  vendor trained the vision stack from scratch. Several rows are a vision stack on
  someone else's LLM (Holo3.1 fine-tuned from Qwen 3.5, W0026; MiniCPM-o 4.5 built on SigLip2,
  Whisper-medium, CosyVoice2 and Qwen3-8B, W0015; InternVL3-78B carrying the Qwen license,
  F0204). How many do is not measured here. So
  the embeddings_retrieval approach fits: score `data`/`code` on the stage the publisher
  released, and inherit `pretrained` as that category does. No software, dataset or hardware
  rows.
- License strings met (weights unless marked code):
  - **Apache-2.0:** qwen-vl, internvl (3.5), internvideo, minicpm-v, minicpm-o, molmo, smolvlm,
    idefics, moondream (moondream2), llava, pixtral (12B), aria, ovis, keye-vl, step-vl, ui-tars,
    holo, north-vision, videollama, moss-vl, bagel, emu, cambrian,
    sail-vl, sensenova-u, qwen-omni (card `other` + name apache-2.0, F0065).
  - **MIT:** florence-2, fara, kimi-vl, glm-v, blip, mimo-vl, ming-omni, longcat-omni. Code MIT:
    internvl, deepseek-vl, janus.
  - **Custom or unusual, a maintainer must place these:**
    - DeepSeek License Agreement v1.0 (use-based restrictions, Attachment A): deepseek-vl, janus
      (F0179, F0180).
    - Mistral Research License MRL-0.1 (non-commercial): pixtral (Large SKU) (F0186).
    - NVIDIA Open Model License: nemotron-vl (F0188).
    - NVIDIA Open Model Agreement: nemotron-omni (F0189).
    - NVIDIA `nsclv1`: eagle. The label is all there is; the text sits behind a gate (F0182).
    - Gemma Terms of Use with Prohibited Use Policy: paligemma (F0190).
    - CC-BY-NC-4.0: nvlm, aya-vision.
    - FAIR non-commercial research: perception-lm. Label only; the text is gated (F0191).
    - Apple ML Research Model license (research only): fastvlm (F0183).
    - LFM Open License v1.0 (commercial use only under USD 10M annual revenue): lfm-vl (F0185).
    - Moondream Model License 1.0 (commercial use allowed, general-purpose hosted inference not
      allowed): moondream 3.x (W0027). This is the governing current release.
    - VITA1.5 terms (academic/research only): vita (F0214).
    - Unresolved: ui-venus. The card says the weight license is "pending final confirmation"
      (F0195); the repo has no LICENSE file and GitHub detects no license (F0120), and its
      README shows an Apache-2.0 badge but says "research and educational purposes only" (W0023). keye-vl code has no license at all (F0112, W0021).
  - Qwen license (`other`/`qwen`) on InternVL3-78B (F0204), which inherits it from a Qwen base.
- Governing-release flags: qwen-omni (newest Qwen3.5-Omni is proprietary, W0017), moondream
  (3.x custom vs 2 Apache), pixtral (Apache 12B vs MRL Large, both sizes of one line).

## 6. Accepted candidates

### 6a. Registry rows (YAML, exact schema, paste-ready)

Also written to `rows.yaml`, which validates against `docs/schemas/registry.schema.json`. None of these slugs or artifacts is in `corpus-index.tsv`, `sources/products/` or `sources/registry/`. 13 of the org slugs are new (section 9, Q12).

```yaml
# Registry rows for the proposed multimodal_models category (issue #9), 2026-09-26 sweep.
# Evidence per row: research/multimodal_models/sweep.md section 6b.
category: multimodal_models
products:
- slug: qwen-vl
  display_name: Qwen-VL
  type: model
  org: alibaba-cloud
  github: QwenLM/Qwen3-VL
  huggingface_model: Qwen/Qwen3-VL-8B-Instruct
- slug: internvl
  display_name: InternVL
  type: model
  org: shanghai-ai-laboratory
  github: OpenGVLab/InternVL
  huggingface_model: OpenGVLab/InternVL3_5-8B
- slug: minicpm-v
  display_name: MiniCPM-V
  type: model
  org: openbmb
  github: OpenBMB/MiniCPM-V
  huggingface_model: openbmb/MiniCPM-V-4.6
- slug: molmo
  display_name: Molmo
  type: model
  org: ai2
  github: allenai/molmo2
  huggingface_model: allenai/Molmo2-8B
- slug: smolvlm
  display_name: SmolVLM
  type: model
  org: hugging-face
  huggingface_model: HuggingFaceTB/SmolVLM2-2.2B-Instruct
- slug: idefics
  display_name: Idefics
  type: model
  org: hugging-face
  huggingface_model: HuggingFaceM4/Idefics3-8B-Llama3
- slug: moondream
  display_name: Moondream
  type: model
  org: m87-labs
  github: m87-labs/moondream
  huggingface_model: vikhyatk/moondream2
- slug: florence-2
  display_name: Florence-2
  type: model
  org: microsoft
  huggingface_model: microsoft/Florence-2-large
- slug: llava
  display_name: LLaVA
  type: model
  org: lmms-lab
  github: LLaVA-VL/LLaVA-NeXT
  huggingface_model: lmms-lab/LLaVA-OneVision-1.5-8B-Instruct
- slug: kimi-vl
  display_name: Kimi-VL
  type: model
  org: moonshot-ai
  github: MoonshotAI/Kimi-VL
  huggingface_model: moonshotai/Kimi-VL-A3B-Thinking-2506
- slug: glm-v
  display_name: GLM-V
  type: model
  org: zhipu-z-ai
  github: zai-org/GLM-V
  huggingface_model: zai-org/GLM-4.6V
- slug: deepseek-vl
  display_name: DeepSeek-VL
  type: model
  org: deepseek
  github: deepseek-ai/DeepSeek-VL2
  huggingface_model: deepseek-ai/deepseek-vl2
- slug: pixtral
  display_name: Pixtral
  type: model
  org: mistral-ai
  huggingface_model: mistralai/Pixtral-12B-2409
- slug: aria
  display_name: Aria
  type: model
  org: rhymes-ai
  github: rhymes-ai/Aria
  huggingface_model: rhymes-ai/Aria
- slug: nvlm
  display_name: NVLM
  type: model
  org: nvidia
  huggingface_model: nvidia/NVLM-D-72B
- slug: nemotron-vl
  display_name: Nemotron Nano VL
  type: model
  org: nvidia
  huggingface_model: nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-BF16
- slug: eagle
  display_name: Eagle
  type: model
  org: nvidia
  github: NVlabs/Eagle
  huggingface_model: nvidia/Eagle2.5-8B
- slug: ovis
  display_name: Ovis
  type: model
  org: ath-maas
  github: ATH-MaaS/Ovis
  huggingface_model: ATH-MaaS/Ovis2.6-30B-A3B
- slug: keye-vl
  display_name: Keye-VL
  type: model
  org: kuaishou
  github: Kwai-Keye/Keye
  huggingface_model: Kwai-Keye/Keye-VL-2.0-30B-A3B
- slug: step-vl
  display_name: Step3-VL
  type: model
  org: stepfun
  github: stepfun-ai/Step3-VL-10B
  huggingface_model: stepfun-ai/Step3-VL-10B
- slug: paligemma
  display_name: PaliGemma
  type: model
  org: google
  huggingface_model: google/paligemma2-3b-mix-224
- slug: blip
  display_name: BLIP
  type: model
  org: salesforce
  github: salesforce/LAVIS
  huggingface_model: Salesforce/blip2-opt-2.7b
- slug: lfm-vl
  display_name: LFM-VL
  type: model
  org: liquid-ai
  huggingface_model: LiquidAI/LFM2.5-VL-1.6B
- slug: aya-vision
  display_name: Aya Vision
  type: model
  org: cohere
  huggingface_model: CohereLabs/aya-vision-8b
- slug: north-vision
  display_name: North Micro Vision
  type: model
  org: cohere
  huggingface_model: CohereLabs/North-Micro-Vision-Instruct
- slug: fastvlm
  display_name: FastVLM
  type: model
  org: apple
  github: apple-aiml-research/ml-fastvlm
  huggingface_model: apple/FastVLM-7B
- slug: mimo-vl
  display_name: MiMo-VL
  type: model
  org: xiaomi
  github: XiaomiMiMo/MiMo-VL
  huggingface_model: XiaomiMiMo/MiMo-VL-7B-RL-2508
- slug: cambrian
  display_name: Cambrian
  type: model
  org: nyu-visionx
  github: cambrian-mllm/cambrian
  huggingface_model: nyu-visionx/Cambrian-S-7B
- slug: perception-lm
  display_name: Perception LM
  type: model
  org: meta
  huggingface_model: facebook/Perception-LM-8B
- slug: sail-vl
  display_name: SAIL-VL
  type: model
  org: bytedance-douyin
  huggingface_model: BytedanceDouyinContent/SAIL-VL2-8B
- slug: videollama
  display_name: VideoLLaMA
  type: model
  org: alibaba-damo-academy
  github: DAMO-NLP-SG/VideoLLaMA3
  huggingface_model: DAMO-NLP-SG/VideoLLaMA3-7B
- slug: internvideo
  display_name: InternVideo
  type: model
  org: shanghai-ai-laboratory
  github: OpenGVLab/InternVideo
  huggingface_model: OpenGVLab/InternVideo2_5_Chat_8B
- slug: moss-vl
  display_name: MOSS-VL
  type: model
  org: openmoss
  github: OpenMOSS/MOSS-VL
  huggingface_model: OpenMOSS-Team/MOSS-VL-Instruct-0708
- slug: ui-tars
  display_name: UI-TARS
  type: model
  org: bytedance-seed-volcano-engine
  github: bytedance/UI-TARS
  huggingface_model: ByteDance-Seed/UI-TARS-1.5-7B
- slug: ui-venus
  display_name: UI-Venus
  type: model
  org: inclusion-ai
  github: inclusionAI/UI-Venus
  huggingface_model: inclusionAI/UI-Venus-2-9B
- slug: holo
  display_name: Holo
  type: model
  org: h-company
  huggingface_model: Hcompany/Holo-3.1-35B-A3B
- slug: fara
  display_name: Fara
  type: model
  org: microsoft
  github: microsoft/fara
  huggingface_model: microsoft/Fara1.5-27B
- slug: qwen-omni
  display_name: Qwen-Omni
  type: model
  org: alibaba-cloud
  github: QwenLM/Qwen3-Omni
  huggingface_model: Qwen/Qwen3-Omni-30B-A3B-Instruct
- slug: minicpm-o
  display_name: MiniCPM-o
  type: model
  org: openbmb
  huggingface_model: openbmb/MiniCPM-o-4_5
- slug: nemotron-omni
  display_name: Nemotron Nano Omni
  type: model
  org: nvidia
  huggingface_model: nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16
- slug: ming-omni
  display_name: Ming-Omni
  type: model
  org: inclusion-ai
  github: inclusionAI/Ming
  huggingface_model: inclusionAI/Ming-flash-omni-2.0
- slug: longcat-omni
  display_name: LongCat-Flash-Omni
  type: model
  org: meituan
  github: meituan-longcat/LongCat-Flash-Omni
  huggingface_model: meituan-longcat/LongCat-Flash-Omni
- slug: vita
  display_name: VITA
  type: model
  org: tencent
  github: VITA-MLLM/VITA
  huggingface_model: VITA-MLLM/VITA-1.5
- slug: janus
  display_name: Janus
  type: model
  org: deepseek
  github: deepseek-ai/Janus
  huggingface_model: deepseek-ai/Janus-Pro-7B
- slug: bagel
  display_name: BAGEL
  type: model
  org: bytedance-seed-volcano-engine
  github: ByteDance-Seed/Bagel
  huggingface_model: ByteDance-Seed/BAGEL-7B-MoT
- slug: emu
  display_name: Emu
  type: model
  org: baai
  github: baaivision/Emu3.5
  huggingface_model: BAAI/Emu3.5
- slug: sensenova-u
  display_name: SenseNova-U
  type: model
  org: sensetime
  huggingface_model: sensenova/SenseNova-U1.5-8B-MoT
```

### 6b. Evidence table, one row per candidate

Adoption is the sum of rolling 30-day Hub downloads over the vendor's own member checkpoints in the cited family listing (third-party quantizations and excluded lines left out). Last release = newest member checkpoint's `createdAt`.

| slug | scope | open status | license(s) + source | archived/fork | last push | last release | adoption signal | member checkpoints | org GitHub/HF handle | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen-vl | vlm | open-weights | weights Apache-2.0 (Qwen3-VL-8B card, F0063); code Apache-2.0 (F0064); Qwen3-VL-235B Apache-2.0 per W0012 | archived=False, fork=False (F0064) | 2026-01-30 (F0064); 19,997 stars | newest checkpoint 2025-10-31 (F0006) | HF downloads (rolling 30d) summed over 62 vendor checkpoints: 46,805,754 (F0006); flagship Qwen/Qwen3-VL-8B-Instruct: 18,555,061 (F0063) | Qwen-VL, Qwen2-VL, Qwen2.5-VL, Qwen3-VL (2B-235B), QVQ | QwenLM / Qwen | Line has no chat checkpoint newer than 2025-10-31 (F0006; the 2026-01-07 Qwen3-VL-Embedding/Reranker checkpoints are excluded as embeddings_retrieval models); Qwen3.5 (2026-02-17) is 'a native vision-language model' that outperforms Qwen3-VL (W0010) and Qwen3.6-27B is tagged image-text-to-text (F0226), so the successor lives in the mapped `qwen` family. |
| internvl | vlm | open-weights | weights Apache-2.0 (InternVL3.5-8B, F0067); InternVL3-78B card license `other`/`qwen` (F0204); code MIT (F0068) | archived=False, fork=False (F0068) | 2025-09-22 (F0068); 10,162 stars | newest checkpoint 2025-09-28 (F0236) | HF downloads (rolling 30d) summed over 155 vendor checkpoints: 2,923,773 (F0236); flagship OpenGVLab/InternVL3_5-8B: 50,683 (F0067) | InternVL 1.5, 2, 2.5, 3, 3.5 (1B-241B), InternVL3.5-GPT-OSS | OpenGVLab / OpenGVLab | Top open MMMU score on OpenVLM snapshot (InternVL3-78B 72.2, F0215). InternVL-U (unified gen, W0013) parked as SKU. Repo last push 2025-09-22 (F0068). |
| minicpm-v | vlm | open-weights | weights Apache-2.0 (MiniCPM-V-4.6, F0071); code Apache-2.0 (F0072) | archived=False, fork=False (F0072) | 2026-09-08 (F0072); 26,461 stars | newest checkpoint 2026-06-04 (F0010) | HF downloads (rolling 30d) summed over 31 vendor checkpoints: 1,238,042 (F0010); flagship openbmb/MiniCPM-V-4.6: 388,634 (F0071) | MiniCPM-V 2/2.6/4/4.5/4.6 (+Thinking), MiniCPM-Llama3-V-2.5 | OpenBMB / openbmb | Separately marketed from mapped `minicpm` text line (OpenBMB/MiniCPM); own repo (F0072). MiniCPM-V 4.6 released 2026-05-11 (W0015). |
| molmo | vlm | open | weights Apache-2.0 (Molmo2-8B, F0075); code Apache-2.0 (F0076); paper title 'Open Weights and Data for Vision-Language Models with Video Understanding and Grounding' (arXiv 2601.10611, F0239) | archived=False, fork=False (F0076) | 2026-03-18 (F0076); 734 stars | newest checkpoint 2026-06-15 (F0012) | HF downloads (rolling 30d) summed over 29 vendor checkpoints: 260,168 (F0012); flagship allenai/Molmo2-8B: 71,158 (F0075) | Molmo (7B-D/7B-O/72B/MolmoE-1B), Molmo2 (4B/8B/O-7B/ER) | allenai / allenai | MolmoAct (robotics) parked to robotics_embodied. Org slug `ai2` reused from index. |
| smolvlm | vlm | open | weights Apache-2.0 (F0159); 'All model checkpoints, VLM datasets, training recipes and tools are released under the Apache 2.' (SmolVLM blog, F0238) | n/a (no repo declared) | no repo; HF lastModified 2025-04-08 (F0159) [not counted as activity] | newest checkpoint 2025-04-14 (F0013) | HF downloads (rolling 30d) summed over 12 vendor checkpoints: 2,037,669 (F0013); flagship HuggingFaceTB/SmolVLM2-2.2B-Instruct: 167,971 (F0159) | SmolVLM (256M/500M/2.2B), SmolVLM2 (256M/500M/2.2B, video) | HuggingFaceTB | No github declared: SmolVLM code sits in huggingface/smollm, already declared by mapped `smollm` (index). Last checkpoint 2025-04-14 (F0013). |
| idefics | vlm | open-weights | Idefics3 Apache-2.0 (F0160); idefics2 Apache-2.0 (F0203) | n/a (no repo declared) | no repo; HF lastModified 2024-12-02 (F0160) [not counted as activity] | newest checkpoint 2024-08-05 (F0014) | HF downloads (rolling 30d) summed over 14 vendor checkpoints: 265,081 (F0014); flagship HuggingFaceM4/Idefics3-8B-Llama3: 128,844 (F0160) | IDEFICS 9B/80B, idefics2-8b, Idefics3-8B-Llama3 | HuggingFaceM4 | Dormant: newest checkpoint 2024-08-05 (F0014). |
| moondream | vlm | open-weights | moondream2 Apache-2.0 (F0081); moondream3.1 `moondream-model-license-1.0` (F0196/F0232): commercial use allowed but no hosted general-purpose inference service (W0027); code Apache-2.0 (F0201) | archived=False, fork=False (F0201) | 2026-04-20 (F0201); 10,057 stars | newest checkpoint 2026-06-30 (F0015, F0016) | HF downloads (rolling 30d) summed over 6 vendor checkpoints: 2,114,146 (F0015, F0016); flagship vikhyatk/moondream2: 1,970,584 (F0081) | moondream1, moondream2 (dated revisions), moondream3-preview, moondream3.1-9B-A2B | m87-labs / vikhyatk | Current release (3.1, 2026-06-30, F0016) is on a custom license: governing-release question. Repo canonical m87-labs/moondream (redirect from vikhyat/moondream, F0175). |
| florence-2 | vlm | open-weights | MIT (F0161) | n/a (no repo declared) | no repo; HF lastModified 2025-08-04 (F0161) [not counted as activity] | newest checkpoint 2024-06-15 (F0017) | HF downloads (rolling 30d) summed over 4 vendor checkpoints: 3,790,676 (F0017); flagship microsoft/Florence-2-large: 474,312 (F0161) | Florence-2 base/large (+ft) | microsoft | HF pipeline image-text-to-text (F0001). Dormant: all checkpoints 2024-06-15 (F0017). Contested with classic_ml_cv. |
| llava | vlm | open-weights | LLaVA-OneVision-1.5 Apache-2.0 (F0087); LLaVA-NeXT code Apache-2.0 (F0088) | archived=False, fork=False (F0088) | 2026-06-15 (F0088); 4,721 stars | newest checkpoint 2025-09-30 (F0020, F0021) | HF downloads (rolling 30d) summed over 76 vendor checkpoints: 3,339,632 (F0020, F0021); flagship lmms-lab/LLaVA-OneVision-1.5-8B-Instruct: 15,955 (F0087) | LLaVA 1.5, LLaVA-NeXT (1.6), LLaVA-NeXT-Video, LLaVA-OneVision, LLaVA-Video, LLaVA-OneVision-1.5 | LLaVA-VL / lmms-lab | Downloads split across lmms-lab (77,776, F0020) and HF's official llava-hf conversions (3,261,856, F0021). Multi-org lineage; org slug `lmms-lab` reused from index. |
| kimi-vl | vlm | open-weights | MIT (F0089); code MIT (F0090) | archived=False, fork=False (F0090) | 2025-07-15 (F0090); 1,227 stars | newest checkpoint 2025-06-21 (F0022) | HF downloads (rolling 30d) summed over 3 vendor checkpoints: 221,687 (F0022); flagship moonshotai/Kimi-VL-A3B-Thinking-2506: 7,389 (F0089) | Kimi-VL-A3B Instruct/Thinking/Thinking-2506 | MoonshotAI / moonshotai | Dormant since 2025-07 (F0090). Mapped `kimi` (Kimi K3) is itself image-text-to-text (F0225). |
| glm-v | vlm | open-weights | GLM-4.6V MIT (F0091); GLM-4.6V-Flash MIT (F0202); code Apache-2.0 (F0092) | archived=False, fork=False (F0092) | 2026-09-02 (F0092); 2,393 stars | newest checkpoint 2025-12-07 (F0057) | HF downloads (rolling 30d) summed over 7 vendor checkpoints: 311,852 (F0057); flagship zai-org/GLM-4.6V: 3,606 (F0091) | GLM-4.1V-Thinking, GLM-4.5V, GLM-4.6V, GLM-4.6V-Flash (CogVLM/CogAgent/GLM-4v predecessors) | zai-org / zai-org | Mapped `glm` now ships natively multimodal GLM-5.3-Flash (image-text-to-text, F0224; W0014). Newest GLM-V checkpoint 2025-12-07 (F0057). README: 'we integrate native Function Calling capabilities' (F0241). |
| deepseek-vl | vlm | open-weights | weights DeepSeek License Agreement v1.0 (use-based restrictions; F0093 card, text F0179); code MIT (F0094) | archived=False, fork=False (F0094) | 2025-02-26 (F0094); 5,372 stars | newest checkpoint 2024-12-13 (F0024) | HF downloads (rolling 30d) summed over 7 vendor checkpoints: 122,361 (F0024); flagship deepseek-ai/deepseek-vl2: 9,050 (F0093) | DeepSeek-VL 1.3B/7B, DeepSeek-VL2 tiny/small/base | deepseek-ai / deepseek-ai | Dormant: repo push 2025-02-26 (F0094), newest checkpoint 2024-12-13 (F0024). |
| pixtral | vlm | open-weights | Pixtral-12B Apache-2.0 (F0187); Pixtral-Large Mistral Research License MRL-0.1 (F0162, text F0186: non-commercial) | n/a (no repo declared) | no repo; HF lastModified 2026-06-02 (F0187) [not counted as activity] | newest checkpoint 2024-11-14 (F0026) | HF downloads (rolling 30d) summed over 3 vendor checkpoints: 8,684 (F0026); flagship mistralai/Pixtral-12B-2409: 8,442 (F0187) | Pixtral-12B (base/instruct), Pixtral-Large-Instruct-2411 | mistralai | Two named licenses across SKUs; sizes of one line so flagship governs (identity guide). Dormant: newest 2024-11-14 (F0026). |
| aria | vlm | open-weights | Apache-2.0 (F0099); code Apache-2.0 (F0100) | archived=False, fork=False (F0100) | 2025-01-22 (F0100); 1,088 stars | newest checkpoint 2024-12-01 (F0027) | HF downloads (rolling 30d) summed over 6 vendor checkpoints: 46,273 (F0027); flagship rhymes-ai/Aria: 45,905 (F0099) | Aria, Aria-Base-8K/64K, Aria-Chat | rhymes-ai / rhymes-ai | Dormant: repo push 2025-01-22 (F0100). |
| nvlm | vlm | open-weights | CC-BY-NC-4.0 (F0163) | n/a (no repo declared) | no repo; HF lastModified 2025-01-14 (F0163) [not counted as activity] | newest checkpoint 2024-12-19 (F0029) | HF downloads (rolling 30d) summed over 2 vendor checkpoints: 11,928 (F0029); flagship nvidia/NVLM-D-72B: 11,928 (F0163) | NVLM-D-72B | nvidia | Dormant single release (2024-09-30, F0029). |
| nemotron-vl | vlm | open-weights | NVIDIA Open Model License (label F0164; text F0188: 'Models are commercially usable') | n/a (no repo declared) | no repo; HF lastModified 2026-08-25 (F0164) [not counted as activity] | newest checkpoint 2025-10-22 (F0028) | HF downloads (rolling 30d) summed over 6 vendor checkpoints: 171,865 (F0028); flagship nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-BF16: 20,600 (F0164) | Llama-3.1-Nemotron-Nano-VL-8B-V1, NVIDIA-Nemotron-Nano-12B-v2-VL (BF16/FP8/NVFP4) | nvidia | Card: 'NVIDIA Nemotron Nano v2 12B VL model enables multi-image reasoning and video understanding' (F0220). Mapped `nemotron` (finetuned_chat) is the text line; precedent `nemotron-embed`/`nemotron-rerank` are separate rows. |
| eagle | vlm | open-weights | weights `nsclv1` label (F0107; LICENSE is behind an auto-gate, HTTP 401, F0182: text not fetched); code Apache-2.0 (F0108) | archived=False, fork=False (F0108) | 2026-06-24 (F0108); 3,611 stars | newest checkpoint 2025-04-12 (F0030) | HF downloads (rolling 30d) summed over 4 vendor checkpoints: 21,510 (F0030); flagship nvidia/Eagle2.5-8B: 18,146 (F0107) | Eagle-X5, Eagle2 (1B/2B/9B), Eagle2.5-8B | NVlabs / nvidia | License text not read (gate). |
| ovis | vlm | open-weights | Ovis2.6-30B-A3B Apache-2.0 (F0245); Ovis2.5-9B Apache-2.0 (F0109); code Apache-2.0 (F0233) | archived=False, fork=False (F0233) | 2026-07-15 (F0233); 1,522 stars | newest checkpoint 2026-05-11 (F0234) | HF downloads (rolling 30d) summed over 23 vendor checkpoints: 50,653 (F0234); flagship ATH-MaaS/Ovis2.6-30B-A3B: 1,012 (F0245) | Ovis1.5, Ovis1.6, Ovis2 (1B-34B), Ovis2.5 (2B/9B), Ovis2.6 (30B-A3B, 80B-A3B) | ATH-MaaS / ATH-MaaS | Repo and HF moved from AIDC-AI to ATH-MaaS (ungh redirect F0230; AIDC-AI HF listing empty F0032). OvisOCR2 parked to document_conversion; Ovis-U1 (unified), Ovis-Image-7B (text-to-image) and -Embedding/-Clip entries excluded from the sum (F0234). |
| keye-vl | vlm | open-weights | weights Apache-2.0 (F0111); code repo states no license (ecosyste.ms null F0112; no LICENSE file F0193/F0205-F0207; W0021) | archived=False, fork=False (F0112) | 2026-06-10 (F0112); 812 stars | newest checkpoint 2026-06-18 (F0033) | HF downloads (rolling 30d) summed over 5 vendor checkpoints: 36,637 (F0033); flagship Kwai-Keye/Keye-VL-2.0-30B-A3B: 849 (F0111) | Keye-VL-8B-Preview, Keye-VL-1.5-8B, Keye-VL-671B-A37B, Keye-VL-2.0-30B-A3B | Kwai-Keye / Kwai-Keye | Code has no license text: flag. |
| step-vl | vlm | open-weights | Apache-2.0 (F0113); code Apache-2.0 (F0114) | archived=False, fork=False (F0114) | 2026-01-21 (F0114); 414 stars | newest checkpoint 2026-02-02 (F0034) | HF downloads (rolling 30d) summed over 3 vendor checkpoints: 29,272 (F0034); flagship stepfun-ai/Step3-VL-10B: 28,318 (F0113) | Step3-VL-10B (base/instruct/FP8) | stepfun-ai / stepfun-ai | Step-3.7-Flash (image-text-to-text flagship, F0002) parked as a general line. Slug drops version per identity guide. |
| paligemma | vlm | open-weights | Gemma Terms of Use (F0166; text F0190: Prohibited Use Policy incorporated) | n/a (no repo declared) | no repo; HF lastModified 2025-02-07 (F0166) [not counted as activity] | newest checkpoint 2025-02-03 (F0237) | HF downloads (rolling 30d) summed over 166 vendor checkpoints: 651,853 (F0237); flagship google/paligemma2-3b-mix-224: 19,707 (F0166) | PaliGemma 3B, PaliGemma 2 (3B/10B/28B, pt/mix/ft) | google | Gemma-branded variant; precedent codegemma/shieldgemma/embeddinggemma are separate rows. No github: google-research/big_vision is declared by mapped `siglip`. Dormant: newest member checkpoint 2025-02-03 (F0237). |
| blip | vlm | open-weights | BLIP-2 MIT (F0125); LAVIS code BSD-3-Clause (F0126) | archived=True, fork=False (F0126) | 2026-09-18 (F0126); 11,264 stars [archived: not counted as activity] | newest checkpoint 2023-08-23 (F0039, F0235) | HF downloads (rolling 30d) summed over 22 vendor checkpoints: 3,734,419 (F0039, F0235); flagship Salesforce/blip2-opt-2.7b: 713,833 (F0125) | BLIP (captioning/VQA), BLIP-2 (OPT/Flan-T5), InstructBLIP (F0235) | salesforce / Salesforce | LAVIS repo is ARCHIVED (F0126), so its push date is not counted as activity. BLIP3o / BLIP3o-NEXT (2025-11, generation and editing, F0039) are excluded from the sum and parked to media_generation. Dormant: newest member 2023-08-23. |
| lfm-vl | vlm | open-weights | LFM Open License v1.0 (F0168; text F0185: commercial use limited to entities under USD 10M annual revenue) | n/a (no repo declared) | no repo; HF lastModified 2026-03-30 (F0168) [not counted as activity] | newest checkpoint 2026-09-18 (F0041) | HF downloads (rolling 30d) summed over 31 vendor checkpoints: 307,035 (F0041); flagship LiquidAI/LFM2.5-VL-1.6B: 23,064 (F0168) | LFM2-VL (450M/1.6B), LFM2.5-VL (450M/1.6B/3B) | LiquidAI | Custom license with revenue threshold: flag. Liquid AI has no product in corpus-index.tsv (local check). |
| aya-vision | vlm | open-weights | CC-BY-NC-4.0 (F0169) | n/a (no repo declared) | no repo; HF lastModified 2026-01-09 (F0169) [not counted as activity] | newest checkpoint 2025-03-02 (F0042) | HF downloads (rolling 30d) summed over 2 vendor checkpoints: 3,249 (F0042); flagship CohereLabs/aya-vision-8b: 2,979 (F0169) | aya-vision-8b, aya-vision-32b | CohereLabs | Separately named from tail `aya-expanse`. Dormant: newest checkpoint 2025-03-02 (F0042); an HF lastModified of 2026-01-09 (F0169) is a repo edit, not a release. |
| north-vision | vlm | open-weights | Apache-2.0 (F0170; W0009) | n/a (no repo declared) | no repo; HF lastModified 2026-09-11 (F0170) [not counted as activity] | newest checkpoint 2026-08-10 (F0043) | HF downloads (rolling 30d) summed over 1 vendor checkpoints: 169,774 (F0043); flagship CohereLabs/North-Micro-Vision-Instruct: 169,774 (F0170) | North-Micro-Vision-Instruct (2.4B) | CohereLabs | New 2026-08-12 (W0009), not in brief. Single checkpoint; 'North' is also Cohere's code/translate line (F0043) so the product-line pitch is unclear. |
| fastvlm | vlm | open-weights | weights Apple ML Research Model license (label `apple-amlr` F0137; text F0183: 'for the sole purpose of scientific research'; same text on GitHub F0184); code license `other` (F0200) | archived=False, fork=False (F0200) | 2026-09-11 (F0200); 7,418 stars | newest checkpoint 2025-08-25 (F0047) | HF downloads (rolling 30d) summed over 6 vendor checkpoints: 11,135 (F0047); flagship apple/FastVLM-7B: 1,364 (F0137) | FastVLM 0.5B/1.5B/7B (+int4/int8/fp16) | apple-aiml-research / apple | Research-only weights. Repo canonical apple-aiml-research/ml-fastvlm (F0176/F0200). |
| mimo-vl | vlm | open-weights | MIT (F0139); code Apache-2.0 (F0140) | archived=False, fork=False (F0140) | 2025-08-21 (F0140); 645 stars | newest checkpoint 2025-08-07 (F0048) | HF downloads (rolling 30d) summed over 6 vendor checkpoints: 4,483 (F0048); flagship XiaomiMiMo/MiMo-VL-7B-RL-2508: 1,319 (F0139) | MiMo-VL-7B SFT/RL (+2508) | XiaomiMiMo / XiaomiMiMo | Dormant: repo push 2025-08-21 (F0140). Mapped `mimo-pro` is the text line. |
| cambrian | vlm | open-weights | Apache-2.0 (F0147); code Apache-2.0 (F0148) | archived=False, fork=False (F0148) | 2025-11-07 (F0148); 2,011 stars | newest checkpoint 2026-05-21 (F0052) | HF downloads (rolling 30d) summed over 29 vendor checkpoints: 1,757 (F0052); flagship nyu-visionx/Cambrian-S-7B: 710 (F0147) | Cambrian-1 (8B/13B/34B), Cambrian-S (3B/7B), Cambrian-P | cambrian-mllm / nyu-visionx | Academic line; low usage (1,757 / 30d, F0052). |
| perception-lm | vlm | open-weights | weights `fair-noncommercial-research` label (F0149; LICENSE gated, HTTP 401, F0191: text not fetched); code Apache-2.0 (F0150) | n/a (no repo declared) | no repo; HF lastModified 2025-07-14 (F0149) [not counted as activity] | newest checkpoint 2025-04-10 (F0053) | HF downloads (rolling 30d) summed over 3 vendor checkpoints: 1,621 (F0053); flagship facebook/Perception-LM-8B: 173 (F0149) | Perception-LM 1B/3B/8B | facebook | Named in the researcher's own targeted HF query (F0053), not found by open discovery; not in brief. Non-commercial. No github declared: facebookresearch/perception_models (Apache-2.0, pushed 2026-04-13, F0150) is already declared by tail `perception-encoder` (embeddings_retrieval). |
| sail-vl | vlm | open-weights | Apache-2.0 (F0172) | n/a (no repo declared) | no repo; HF lastModified 2025-09-18 (F0172) [not counted as activity] | newest checkpoint 2025-09-11 (F0056) | HF downloads (rolling 30d) summed over 9 vendor checkpoints: 7,304 (F0056); flagship BytedanceDouyinContent/SAIL-VL2-8B: 221 (F0172) | SAIL-VL 2B, SAIL-VL-1.5/1.6, SAIL-VL2 (2B/8B, Thinking) | BytedanceDouyinContent | Surfaced via W0003 (SAIL-VL2 technical report). HF org is BytedanceDouyinContent (F0056), not ByteDance-Seed; org slug proposed. |
| videollama | video | open-weights | Apache-2.0 (F0133); code Apache-2.0 (F0134) | archived=False, fork=False (F0134) | 2025-08-14 (F0134); 1,184 stars | newest checkpoint 2025-06-17 (F0044) | HF downloads (rolling 30d) summed over 17 vendor checkpoints: 11,148 (F0044); flagship DAMO-NLP-SG/VideoLLaMA3-7B: 3,912 (F0133) | VideoLLaMA2, VideoLLaMA2.1(-AV), VideoLLaMA3 (2B/7B) | DAMO-NLP-SG / DAMO-NLP-SG | HF pipeline video-text-to-text (F0004). Repo push 2025-08-14 (F0134). |
| internvideo | video | open-weights | Apache-2.0 (F0069); code Apache-2.0 (F0070) | archived=False, fork=False (F0070) | 2026-07-02 (F0070); 2,394 stars | newest checkpoint 2025-01-22 (F0009) | HF downloads (rolling 30d) summed over 3 vendor checkpoints: 4,310 (F0009); flagship OpenGVLab/InternVideo2_5_Chat_8B: 4,051 (F0069) | InternVideo2-Chat-8B, InternVideo2.5-Chat-8B (encoders InternVideo2 stage2/CLIP excluded) | OpenGVLab / OpenGVLab | Repo also ships video encoders (classic_ml_cv overlap). Chat checkpoints low usage (4,310 / 30d, F0009). |
| moss-vl | video | open-weights | Apache-2.0 (F0145); code Apache-2.0 (F0146) | archived=False, fork=False (F0146) | 2026-09-23 (F0146); 738 stars | newest checkpoint 2026-09-06 (F0051) | HF downloads (rolling 30d) summed over 10 vendor checkpoints: 4,168 (F0051); flagship OpenMOSS-Team/MOSS-VL-Instruct-0708: 513 (F0145) | MOSS-VL-Instruct 0408/0708, MOSS-VL-Realtime | OpenMOSS / OpenMOSS-Team | New 2026 line (first checkpoint 2026-04-07, F0051); not in brief. |
| ui-tars | gui | open-weights | Apache-2.0 (F0117); code Apache-2.0 (F0118) | archived=False, fork=False (F0118) | 2026-01-27 (F0118); 11,519 stars | newest checkpoint 2025-04-16 (F0037) | HF downloads (rolling 30d) summed over 6 vendor checkpoints: 605,451 (F0037); flagship ByteDance-Seed/UI-TARS-1.5-7B: 598,585 (F0117) | UI-TARS 2B/7B/72B (SFT/DPO), UI-TARS-1.5-7B | bytedance / ByteDance-Seed | GUI-agent VLM ('pixels in and actions out', W0018). UI-TARS-desktop app is a separate software product (orchestration_agents). |
| ui-venus | gui | open-weights | UI-Venus-2 card: 'model-weight license is pending final confirmation' (F0195); HF license field empty (F0119); no LICENSE file (F0194, F0211-F0213); GitHub license detection null (F0120); README carries an Apache-2.0 badge but says 'This project is for research and educational purposes only' (W0023) | archived=False, fork=False (F0120) | 2026-09-17 (F0120); 1,051 stars | newest checkpoint 2026-08-26 (F0060) | HF downloads (rolling 30d) summed over 7 vendor checkpoints: 24,063 (F0060); flagship inclusionAI/UI-Venus-2-9B: 8,276 (F0119) | UI-Venus-Ground-7B, UI-Venus-1.5 (2B/8B/30B-A3B), UI-Venus-2 (9B/27B) | inclusionAI / inclusionAI | Weights license unresolved: flag. Surfaced by W0018 (UI-Venus-1.5 report). |
| holo | gui | open-weights | Apache-2.0 (Holo-3.1-35B-A3B F0167, Holo-3.1-4B F0197, Holo2-4B F0198) | n/a (no repo declared) | no repo; HF lastModified 2026-06-26 (F0167) [not counted as activity] | newest checkpoint 2026-06-02 (F0046) | HF downloads (rolling 30d) summed over 19 vendor checkpoints: 269,481 (F0046); flagship Hcompany/Holo-3.1-35B-A3B: 760 (F0167) | Holo2 (4B...), Holo-3.1 (0.8B/4B/9B/35B-A3B); Holo3-122B-A10B is API-only (W0026) | Hcompany | Surfaced by W0018/W0026, not in brief. Holo3.1 fine-tuned from Qwen 3.5 base (W0026). |
| fara | gui | open-weights | MIT (F0085); code MIT (F0086) | archived=False, fork=False (F0086) | 2026-09-22 (F0086); 6,192 stars | newest checkpoint 2026-07-17 (F0019) | HF downloads (rolling 30d) summed over 5 vendor checkpoints: 16,142 (F0019); flagship microsoft/Fara1.5-27B: 1,867 (F0085) | Fara-7B, Fara1.5 (4B/9B/27B) | microsoft / microsoft | Computer-use model; surfaced by HF likes listing (F0002), not in brief. |
| qwen-omni | omni | open-weights | card license `other` with license_name `apache-2.0` (F0065; HF LICENSE file 404, F0177); code Apache-2.0 (F0066) | archived=False, fork=False (F0066) | 2026-04-23 (F0066); 4,030 stars | newest checkpoint 2025-09-20 (F0007) | HF downloads (rolling 30d) summed over 7 vendor checkpoints: 1,548,543 (F0007); flagship Qwen/Qwen3-Omni-30B-A3B-Instruct: 612,375 (F0065) | Qwen2.5-Omni 3B/7B, Qwen3-Omni-30B-A3B Instruct/Thinking/Captioner | QwenLM / Qwen | Qwen3.5-Omni (2026-04) was 'released ... as proprietary' (W0017), so the newest release is API-only: governing-release question. |
| minicpm-o | omni | open-weights | Apache-2.0 (F0073) | n/a (no repo declared) | no repo; HF lastModified 2026-08-18 (F0073) [not counted as activity] | newest checkpoint 2026-06-02 (F0011) | HF downloads (rolling 30d) summed over 7 vendor checkpoints: 1,153,485 (F0011); flagship openbmb/MiniCPM-o-4_5: 721,159 (F0073) | MiniCPM-o 2.6, MiniCPM-o 4.5 (+gguf/awq) | openbmb | No github declared: OpenBMB/MiniCPM-o redirects to OpenBMB/MiniCPM-V (F0174), which `minicpm-v` declares. Full-duplex vision+speech (W0015). |
| nemotron-omni | omni | open-weights | NVIDIA Open Model Agreement (label F0165; text F0189: 'Works are commercially usable') | n/a (no repo declared) | no repo; HF lastModified 2026-08-24 (F0165) [not counted as activity] | newest checkpoint 2026-04-24 (F0031) | HF downloads (rolling 30d) summed over 3 vendor checkpoints: 2,072,960 (F0031); flagship nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16: 351,706 (F0165) | Nemotron-3-Nano-Omni-30B-A3B-Reasoning (BF16/FP8/NVFP4) | nvidia | Card: 'developed by NVIDIA as part of the Nemotron model family' (F0221): SKU-vs-row question. Released 2026-04-28 (W0017). |
| ming-omni | omni | open-weights | MIT (F0135); code MIT (F0136) | archived=False, fork=False (F0136) | 2026-07-27 (F0136); 671 stars | newest checkpoint 2026-02-10 (F0045) | HF downloads (rolling 30d) summed over 5 vendor checkpoints: 9,635 (F0045); flagship inclusionAI/Ming-flash-omni-2.0: 4,833 (F0135) | Ming-Lite-Omni (1.5), Ming-flash-omni (Preview, 2.0) | inclusionAI / inclusionAI | Ming-omni-tts (pipeline text-to-speech, F0045) and Ming-UniAudio are speech SKUs (speech_audio). |
| longcat-omni | omni | open-weights | MIT (F0151); code MIT (F0152) | archived=False, fork=False (F0152) | 2026-04-15 (F0152); 481 stars | newest checkpoint 2025-10-24 (F0054) | HF downloads (rolling 30d) summed over 2 vendor checkpoints: 314 (F0054); flagship meituan-longcat/LongCat-Flash-Omni: 206 (F0151) | LongCat-Flash-Omni (+FP8) | meituan-longcat / meituan-longcat | Low HF usage (314 / 30d, F0054); not in brief. |
| vita | omni | open-weights | custom VITA1.5 terms: 'only for academic, research and education purposes, and refrain from using it for any commercial or production purposes' (License.txt F0214); HF license empty (F0143) | archived=False, fork=False (F0144) | 2025-03-28 (F0144); 2,334 stars | newest checkpoint 2025-05-15 (F0050) | HF downloads (rolling 30d) summed over 19 vendor checkpoints: 443 (F0050); flagship VITA-MLLM/VITA-1.5: 263 (F0143) | VITA, VITA-1.5, Long-VITA, VITA-Audio (VITA-QinYu audio models and VITA-E excluded, F0050) | VITA-MLLM / VITA-MLLM | Org needs a maintainer call: License.txt copyright is THL A29 (Tencent) (F0214), but OpenCompass lists VITA/VITA-1.5 under Org 'NJU' and Long-VITA under 'Tencent Youtu Lab & Nanjing University' (F0215). Dormant: newest member 2025-05-15 (F0050), last news 2025-01-17 (W0022). |
| janus | unified | open-weights | weights DeepSeek License Agreement v1.0 (card license_name `deepseek`, F0095; text F0180); code MIT (F0096) | archived=False, fork=False (F0096) | 2025-02-01 (F0096); 17,765 stars | newest checkpoint 2025-01-26 (F0025) | HF downloads (rolling 30d) summed over 4 vendor checkpoints: 21,018 (F0025); flagship deepseek-ai/Janus-Pro-7B: 10,483 (F0095) | Janus-1.3B, JanusFlow-1.3B, Janus-Pro 1B/7B | deepseek-ai / deepseek-ai | Card tags 'text-to-image', 'unified-model' (F0095): contested with media_generation. Dormant: push 2025-02-01 (F0096). |
| bagel | unified | open-weights | Apache-2.0 (F0123); code Apache-2.0 (F0124) | archived=False, fork=False (F0124) | 2026-05-04 (F0124); 6,179 stars | newest checkpoint 2025-05-19 (F0038) | HF downloads (rolling 30d) summed over 1 vendor checkpoints: 872 (F0038); flagship ByteDance-Seed/BAGEL-7B-MoT: 872 (F0123) | BAGEL-7B-MoT | ByteDance-Seed / ByteDance-Seed | Unified understanding + generation (W0020): contested with media_generation. HF downloads low (872, F0038) vs 6,179 stars. |
| emu | unified | open-weights | Apache-2.0 (F0141); code Apache-2.0 (F0142) | archived=False, fork=False (F0142) | 2025-12-30 (F0142); 1,557 stars | newest checkpoint 2025-10-31 (F0049) | HF downloads (rolling 30d) summed over 9 vendor checkpoints: 48,234 (F0049); flagship BAAI/Emu3.5: 372 (F0141) | Emu3 (Chat/Gen/VisionTokenizer), Emu3.5 | baaivision / BAAI | Unified model listed with Janus-Pro/BAGEL (W0020); Emu3.5 tagged any-to-any (F0049): contested with media_generation and world_models. |
| sensenova-u | unified | open-weights | Apache-2.0 (F0171) | n/a (no repo declared) | no repo; HF lastModified 2026-09-15 (F0171) [not counted as activity] | newest checkpoint 2026-08-20 (F0055) | HF downloads (rolling 30d) summed over 14 vendor checkpoints: 19,660 (F0055); flagship sensenova/SenseNova-U1.5-8B-MoT: 7,326 (F0171) | SenseNova-U1-8B-MoT (+Infographic, SFT), SenseNova-U1.5-8B-MoT | sensenova | New 2026 any-to-any line (F0003, F0055), not in brief. Closed SenseNova-V6.x are separate (OpenVLM). |

### 6c. Source list: every id cited anywhere in this document (ranges expanded), with fetch time (all 2026-09-26 UTC)

| id | fetched (UTC) | HTTP / tool | URL or query |
|---|---|---|---|
| F0001 | 2026-09-26T20:01:50Z | 200 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 |
| F0002 | 2026-09-26T20:01:50Z | 200 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 |
| F0003 | 2026-09-26T20:01:50Z | 200 | https://huggingface.co/api/models?pipeline_tag=any-to-any&sort=downloads&direction=-1&limit=100 |
| F0004 | 2026-09-26T20:01:51Z | 200 | https://huggingface.co/api/models?pipeline_tag=video-text-to-text&sort=downloads&direction=-1&limit=100 |
| F0005 | 2026-09-26T20:01:51Z | 200 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=trendingScore&direction=-1&limit=100 |
| F0006 | 2026-09-26T20:03:08Z | 200 | https://huggingface.co/api/models?author=Qwen&search=VL&sort=downloads&direction=-1&limit=100 |
| F0007 | 2026-09-26T20:03:09Z | 200 | https://huggingface.co/api/models?author=Qwen&search=Omni&sort=downloads&direction=-1&limit=100 |
| F0009 | 2026-09-26T20:03:09Z | 200 | https://huggingface.co/api/models?author=OpenGVLab&search=InternVideo&sort=downloads&direction=-1&limit=100 |
| F0010 | 2026-09-26T20:03:09Z | 200 | https://huggingface.co/api/models?author=openbmb&search=MiniCPM-V&sort=downloads&direction=-1&limit=100 |
| F0011 | 2026-09-26T20:03:10Z | 200 | https://huggingface.co/api/models?author=openbmb&search=MiniCPM-o&sort=downloads&direction=-1&limit=100 |
| F0012 | 2026-09-26T20:03:10Z | 200 | https://huggingface.co/api/models?author=allenai&search=Molmo&sort=downloads&direction=-1&limit=100 |
| F0013 | 2026-09-26T20:03:10Z | 200 | https://huggingface.co/api/models?author=HuggingFaceTB&search=SmolVLM&sort=downloads&direction=-1&limit=100 |
| F0014 | 2026-09-26T20:03:10Z | 200 | https://huggingface.co/api/models?author=HuggingFaceM4&search=idefics&sort=downloads&direction=-1&limit=100 |
| F0015 | 2026-09-26T20:03:10Z | 200 | https://huggingface.co/api/models?author=vikhyatk&search=moondream&sort=downloads&direction=-1&limit=100 |
| F0016 | 2026-09-26T20:03:11Z | 200 | https://huggingface.co/api/models?author=moondream&search=moondream&sort=downloads&direction=-1&limit=100 |
| F0017 | 2026-09-26T20:03:11Z | 200 | https://huggingface.co/api/models?author=microsoft&search=Florence&sort=downloads&direction=-1&limit=100 |
| F0018 | 2026-09-26T20:03:11Z | 200 | https://huggingface.co/api/models?author=microsoft&search=Phi&sort=downloads&direction=-1&limit=100 |
| F0019 | 2026-09-26T20:03:11Z | 200 | https://huggingface.co/api/models?author=microsoft&search=Fara&sort=downloads&direction=-1&limit=100 |
| F0020 | 2026-09-26T20:03:11Z | 200 | https://huggingface.co/api/models?author=lmms-lab&search=llava&sort=downloads&direction=-1&limit=100 |
| F0021 | 2026-09-26T20:03:12Z | 200 | https://huggingface.co/api/models?author=llava-hf&search=llava&sort=downloads&direction=-1&limit=100 |
| F0022 | 2026-09-26T20:03:12Z | 200 | https://huggingface.co/api/models?author=moonshotai&search=VL&sort=downloads&direction=-1&limit=100 |
| F0023 | 2026-09-26T20:03:12Z | 200 | https://huggingface.co/api/models?author=zai-org&search=V&sort=downloads&direction=-1&limit=100 |
| F0024 | 2026-09-26T20:03:12Z | 200 | https://huggingface.co/api/models?author=deepseek-ai&search=vl&sort=downloads&direction=-1&limit=100 |
| F0025 | 2026-09-26T20:03:12Z | 200 | https://huggingface.co/api/models?author=deepseek-ai&search=Janus&sort=downloads&direction=-1&limit=100 |
| F0026 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models?author=mistralai&search=Pixtral&sort=downloads&direction=-1&limit=100 |
| F0027 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models?author=rhymes-ai&search=Aria&sort=downloads&direction=-1&limit=100 |
| F0028 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models?author=nvidia&search=VL&sort=downloads&direction=-1&limit=100 |
| F0029 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models?author=nvidia&search=NVLM&sort=downloads&direction=-1&limit=100 |
| F0030 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models?author=nvidia&search=Eagle&sort=downloads&direction=-1&limit=100 |
| F0031 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models?author=nvidia&search=Omni&sort=downloads&direction=-1&limit=100 |
| F0032 | 2026-09-26T20:03:14Z | 200 | https://huggingface.co/api/models?author=AIDC-AI&search=Ovis&sort=downloads&direction=-1&limit=100 |
| F0033 | 2026-09-26T20:03:14Z | 200 | https://huggingface.co/api/models?author=Kwai-Keye&search=Keye&sort=downloads&direction=-1&limit=100 |
| F0034 | 2026-09-26T20:03:14Z | 200 | https://huggingface.co/api/models?author=stepfun-ai&search=VL&sort=downloads&direction=-1&limit=100 |
| F0035 | 2026-09-26T20:03:14Z | 200 | https://huggingface.co/api/models?author=baidu&search=VL&sort=downloads&direction=-1&limit=100 |
| F0037 | 2026-09-26T20:03:15Z | 200 | https://huggingface.co/api/models?author=ByteDance-Seed&search=UI-TARS&sort=downloads&direction=-1&limit=100 |
| F0038 | 2026-09-26T20:03:15Z | 200 | https://huggingface.co/api/models?author=ByteDance-Seed&search=BAGEL&sort=downloads&direction=-1&limit=100 |
| F0039 | 2026-09-26T20:03:15Z | 200 | https://huggingface.co/api/models?author=Salesforce&search=blip&sort=downloads&direction=-1&limit=100 |
| F0040 | 2026-09-26T20:03:15Z | 200 | https://huggingface.co/api/models?author=Salesforce&search=xgen-mm&sort=downloads&direction=-1&limit=100 |
| F0041 | 2026-09-26T20:03:15Z | 200 | https://huggingface.co/api/models?author=LiquidAI&search=VL&sort=downloads&direction=-1&limit=100 |
| F0042 | 2026-09-26T20:03:16Z | 200 | https://huggingface.co/api/models?author=CohereLabs&search=vision&sort=downloads&direction=-1&limit=100 |
| F0043 | 2026-09-26T20:03:16Z | 200 | https://huggingface.co/api/models?author=CohereLabs&search=North&sort=downloads&direction=-1&limit=100 |
| F0044 | 2026-09-26T20:03:16Z | 200 | https://huggingface.co/api/models?author=DAMO-NLP-SG&search=VideoLLaMA&sort=downloads&direction=-1&limit=100 |
| F0045 | 2026-09-26T20:03:16Z | 200 | https://huggingface.co/api/models?author=inclusionAI&search=Ming&sort=downloads&direction=-1&limit=100 |
| F0046 | 2026-09-26T20:03:16Z | 200 | https://huggingface.co/api/models?author=Hcompany&search=Holo&sort=downloads&direction=-1&limit=100 |
| F0047 | 2026-09-26T20:03:17Z | 200 | https://huggingface.co/api/models?author=apple&search=FastVLM&sort=downloads&direction=-1&limit=100 |
| F0048 | 2026-09-26T20:03:17Z | 200 | https://huggingface.co/api/models?author=XiaomiMiMo&search=VL&sort=downloads&direction=-1&limit=100 |
| F0049 | 2026-09-26T20:03:17Z | 200 | https://huggingface.co/api/models?author=BAAI&search=Emu&sort=downloads&direction=-1&limit=100 |
| F0050 | 2026-09-26T20:03:17Z | 200 | https://huggingface.co/api/models?author=VITA-MLLM&search=VITA&sort=downloads&direction=-1&limit=100 |
| F0051 | 2026-09-26T20:03:17Z | 200 | https://huggingface.co/api/models?author=OpenMOSS-Team&search=VL&sort=downloads&direction=-1&limit=100 |
| F0052 | 2026-09-26T20:03:18Z | 200 | https://huggingface.co/api/models?author=nyu-visionx&search=cambrian&sort=downloads&direction=-1&limit=100 |
| F0053 | 2026-09-26T20:03:18Z | 200 | https://huggingface.co/api/models?author=facebook&search=Perception&sort=downloads&direction=-1&limit=100 |
| F0054 | 2026-09-26T20:03:18Z | 200 | https://huggingface.co/api/models?author=meituan-longcat&search=Omni&sort=downloads&direction=-1&limit=100 |
| F0055 | 2026-09-26T20:03:18Z | 200 | https://huggingface.co/api/models?author=sensenova&search=U1&sort=downloads&direction=-1&limit=100 |
| F0056 | 2026-09-26T20:03:18Z | 200 | https://huggingface.co/api/models?author=BytedanceDouyinContent&search=SAIL-VL&sort=downloads&direction=-1&limit=100 |
| F0057 | 2026-09-26T20:04:05Z | 200 | https://huggingface.co/api/models?author=zai-org&search=GLM-4&sort=downloads&direction=-1&limit=100 |
| F0060 | 2026-09-26T20:04:06Z | 200 | https://huggingface.co/api/models?search=UI-Venus&sort=downloads&direction=-1&limit=30 |
| F0061 | 2026-09-26T20:04:06Z | 200 | https://huggingface.co/api/models?author=PerceptronAI&sort=downloads&direction=-1&limit=30 |
| F0062 | 2026-09-26T20:04:06Z | 200 | https://huggingface.co/api/models?author=nvidia&search=Cosmos-Reason&sort=downloads&direction=-1&limit=30 |
| F0063 | 2026-09-26T20:04:38Z | 200 | https://huggingface.co/api/models/Qwen/Qwen3-VL-8B-Instruct?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0064 | 2026-09-26T20:04:38Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/QwenLM%2FQwen3-VL |
| F0065 | 2026-09-26T20:04:39Z | 200 | https://huggingface.co/api/models/Qwen/Qwen3-Omni-30B-A3B-Instruct?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0066 | 2026-09-26T20:04:39Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/QwenLM%2FQwen3-Omni |
| F0067 | 2026-09-26T20:04:39Z | 200 | https://huggingface.co/api/models/OpenGVLab/InternVL3_5-8B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0068 | 2026-09-26T20:04:40Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenGVLab%2FInternVL |
| F0069 | 2026-09-26T20:04:40Z | 200 | https://huggingface.co/api/models/OpenGVLab/InternVideo2_5_Chat_8B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0070 | 2026-09-26T20:04:40Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenGVLab%2FInternVideo |
| F0071 | 2026-09-26T20:04:40Z | 200 | https://huggingface.co/api/models/openbmb/MiniCPM-V-4.6?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0072 | 2026-09-26T20:04:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenBMB%2FMiniCPM-V |
| F0073 | 2026-09-26T20:04:41Z | 200 | https://huggingface.co/api/models/openbmb/MiniCPM-o-4_5?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0074 | 2026-09-26T20:04:41Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenBMB%2FMiniCPM-o |
| F0075 | 2026-09-26T20:04:41Z | 200 | https://huggingface.co/api/models/allenai/Molmo2-8B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0076 | 2026-09-26T20:04:42Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/allenai%2Fmolmo2 |
| F0077 | 2026-09-26T20:04:42Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0078 | 2026-09-26T20:04:43Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/HuggingFaceTB%2FSmolVLM2-2.2B-Instruct |
| F0079 | 2026-09-26T20:04:43Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0080 | 2026-09-26T20:04:43Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/HuggingFaceM4%2FIdefics3-8B-Llama3 |
| F0081 | 2026-09-26T20:04:44Z | 200 | https://huggingface.co/api/models/vikhyatk/moondream2?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0082 | 2026-09-26T20:04:44Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/vikhyat%2Fmoondream |
| F0083 | 2026-09-26T20:04:44Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0084 | 2026-09-26T20:04:45Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2FFlorence-2-large |
| F0085 | 2026-09-26T20:04:45Z | 200 | https://huggingface.co/api/models/microsoft/Fara1.5-27B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0086 | 2026-09-26T20:04:45Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2Ffara |
| F0087 | 2026-09-26T20:04:45Z | 200 | https://huggingface.co/api/models/lmms-lab/LLaVA-OneVision-1.5-8B-Instruct?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0088 | 2026-09-26T20:04:46Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/LLaVA-VL%2FLLaVA-NeXT |
| F0089 | 2026-09-26T20:04:46Z | 200 | https://huggingface.co/api/models/moonshotai/Kimi-VL-A3B-Thinking-2506?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0090 | 2026-09-26T20:04:46Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/MoonshotAI%2FKimi-VL |
| F0091 | 2026-09-26T20:04:47Z | 200 | https://huggingface.co/api/models/zai-org/GLM-4.6V?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0092 | 2026-09-26T20:04:47Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/zai-org%2FGLM-V |
| F0093 | 2026-09-26T20:04:47Z | 200 | https://huggingface.co/api/models/deepseek-ai/deepseek-vl2?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0094 | 2026-09-26T20:04:47Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/deepseek-ai%2FDeepSeek-VL2 |
| F0095 | 2026-09-26T20:04:48Z | 200 | https://huggingface.co/api/models/deepseek-ai/Janus-Pro-7B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0096 | 2026-09-26T20:04:48Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/deepseek-ai%2FJanus |
| F0097 | 2026-09-26T20:04:48Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0098 | 2026-09-26T20:04:49Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/mistralai%2FPixtral-Large-Instruct-2411 |
| F0099 | 2026-09-26T20:04:49Z | 200 | https://huggingface.co/api/models/rhymes-ai/Aria?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0100 | 2026-09-26T20:04:49Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/rhymes-ai%2FAria |
| F0101 | 2026-09-26T20:04:50Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0102 | 2026-09-26T20:04:50Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nvidia%2FNVLM-D-72B |
| F0103 | 2026-09-26T20:04:50Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0104 | 2026-09-26T20:04:51Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nvidia%2FNVIDIA-Nemotron-Nano-12B-v2-VL-BF16 |
| F0105 | 2026-09-26T20:04:51Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0106 | 2026-09-26T20:04:51Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nvidia%2FNemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 |
| F0107 | 2026-09-26T20:04:52Z | 200 | https://huggingface.co/api/models/nvidia/Eagle2.5-8B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0108 | 2026-09-26T20:04:52Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVlabs%2FEagle |
| F0109 | 2026-09-26T20:04:52Z | 200 | https://huggingface.co/api/models/ATH-MaaS/Ovis2.5-9B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0110 | 2026-09-26T20:04:53Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/AIDC-AI%2FOvis |
| F0111 | 2026-09-26T20:04:53Z | 200 | https://huggingface.co/api/models/Kwai-Keye/Keye-VL-2.0-30B-A3B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0112 | 2026-09-26T20:04:53Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Kwai-Keye%2FKeye |
| F0113 | 2026-09-26T20:04:53Z | 200 | https://huggingface.co/api/models/stepfun-ai/Step3-VL-10B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0114 | 2026-09-26T20:04:54Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stepfun-ai%2FStep3-VL-10B |
| F0115 | 2026-09-26T20:04:54Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0116 | 2026-09-26T20:04:55Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google%2Fpaligemma2-3b-mix-224 |
| F0117 | 2026-09-26T20:04:55Z | 200 | https://huggingface.co/api/models/ByteDance-Seed/UI-TARS-1.5-7B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0118 | 2026-09-26T20:04:55Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bytedance%2FUI-TARS |
| F0119 | 2026-09-26T20:04:55Z | 200 | https://huggingface.co/api/models/inclusionAI/UI-Venus-2-9B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0120 | 2026-09-26T20:04:56Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/inclusionAI%2FUI-Venus |
| F0121 | 2026-09-26T20:04:56Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0122 | 2026-09-26T20:04:57Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Hcompany%2FHolo-3.1-35B-A3B |
| F0123 | 2026-09-26T20:04:57Z | 200 | https://huggingface.co/api/models/ByteDance-Seed/BAGEL-7B-MoT?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0124 | 2026-09-26T20:04:57Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ByteDance-Seed%2FBagel |
| F0125 | 2026-09-26T20:04:57Z | 200 | https://huggingface.co/api/models/Salesforce/blip2-opt-2.7b?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0126 | 2026-09-26T20:04:58Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/salesforce%2FLAVIS |
| F0127 | 2026-09-26T20:04:58Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0128 | 2026-09-26T20:04:58Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/LiquidAI%2FLFM2.5-VL-1.6B |
| F0129 | 2026-09-26T20:04:59Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0130 | 2026-09-26T20:04:59Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/CohereLabs%2Faya-vision-8b |
| F0131 | 2026-09-26T20:04:59Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0132 | 2026-09-26T20:05:00Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/CohereLabs%2FNorth-Micro-Vision-Instruct |
| F0133 | 2026-09-26T20:05:00Z | 200 | https://huggingface.co/api/models/DAMO-NLP-SG/VideoLLaMA3-7B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0134 | 2026-09-26T20:05:00Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/DAMO-NLP-SG%2FVideoLLaMA3 |
| F0135 | 2026-09-26T20:05:00Z | 200 | https://huggingface.co/api/models/inclusionAI/Ming-flash-omni-2.0?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0136 | 2026-09-26T20:05:01Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/inclusionAI%2FMing |
| F0137 | 2026-09-26T20:05:01Z | 200 | https://huggingface.co/api/models/apple/FastVLM-7B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0138 | 2026-09-26T20:05:01Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/apple%2Fml-fastvlm |
| F0139 | 2026-09-26T20:05:02Z | 200 | https://huggingface.co/api/models/XiaomiMiMo/MiMo-VL-7B-RL-2508?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0140 | 2026-09-26T20:05:02Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/XiaomiMiMo%2FMiMo-VL |
| F0141 | 2026-09-26T20:05:02Z | 200 | https://huggingface.co/api/models/BAAI/Emu3.5?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0142 | 2026-09-26T20:05:03Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/baaivision%2FEmu3.5 |
| F0143 | 2026-09-26T20:05:03Z | 200 | https://huggingface.co/api/models/VITA-MLLM/VITA-1.5?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0144 | 2026-09-26T20:05:03Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/VITA-MLLM%2FVITA |
| F0145 | 2026-09-26T20:05:03Z | 200 | https://huggingface.co/api/models/OpenMOSS-Team/MOSS-VL-Instruct-0708?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0146 | 2026-09-26T20:05:04Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenMOSS%2FMOSS-VL |
| F0147 | 2026-09-26T20:05:04Z | 200 | https://huggingface.co/api/models/nyu-visionx/Cambrian-S-7B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0148 | 2026-09-26T20:05:04Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/cambrian-mllm%2Fcambrian |
| F0149 | 2026-09-26T20:05:05Z | 200 | https://huggingface.co/api/models/facebook/Perception-LM-8B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0150 | 2026-09-26T20:05:05Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fperception_models |
| F0151 | 2026-09-26T20:05:05Z | 200 | https://huggingface.co/api/models/meituan-longcat/LongCat-Flash-Omni?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0152 | 2026-09-26T20:05:06Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/meituan-longcat%2FLongCat-Flash-Omni |
| F0153 | 2026-09-26T20:05:06Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0154 | 2026-09-26T20:05:07Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/sensenova%2FSenseNova-U1.5-8B-MoT |
| F0155 | 2026-09-26T20:05:07Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0156 | 2026-09-26T20:05:07Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/BytedanceDouyinContent%2FSAIL-VL2-8B |
| F0157 | 2026-09-26T20:05:08Z | 200 | https://huggingface.co/api/models/?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0158 | 2026-09-26T20:05:08Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PerceptronAI%2FIsaac-0.5 |
| F0159 | 2026-09-26T20:05:19Z | 200 | https://huggingface.co/api/models/HuggingFaceTB/SmolVLM2-2.2B-Instruct?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0160 | 2026-09-26T20:05:20Z | 200 | https://huggingface.co/api/models/HuggingFaceM4/Idefics3-8B-Llama3?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0161 | 2026-09-26T20:05:20Z | 200 | https://huggingface.co/api/models/microsoft/Florence-2-large?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0162 | 2026-09-26T20:05:20Z | 200 | https://huggingface.co/api/models/mistralai/Pixtral-Large-Instruct-2411?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0163 | 2026-09-26T20:05:21Z | 200 | https://huggingface.co/api/models/nvidia/NVLM-D-72B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0164 | 2026-09-26T20:05:21Z | 200 | https://huggingface.co/api/models/nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-BF16?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0165 | 2026-09-26T20:05:21Z | 200 | https://huggingface.co/api/models/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0166 | 2026-09-26T20:05:21Z | 200 | https://huggingface.co/api/models/google/paligemma2-3b-mix-224?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0167 | 2026-09-26T20:05:21Z | 200 | https://huggingface.co/api/models/Hcompany/Holo-3.1-35B-A3B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0168 | 2026-09-26T20:05:22Z | 200 | https://huggingface.co/api/models/LiquidAI/LFM2.5-VL-1.6B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0169 | 2026-09-26T20:05:22Z | 200 | https://huggingface.co/api/models/CohereLabs/aya-vision-8b?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0170 | 2026-09-26T20:05:22Z | 200 | https://huggingface.co/api/models/CohereLabs/North-Micro-Vision-Instruct?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0171 | 2026-09-26T20:05:22Z | 200 | https://huggingface.co/api/models/sensenova/SenseNova-U1.5-8B-MoT?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0172 | 2026-09-26T20:05:22Z | 200 | https://huggingface.co/api/models/BytedanceDouyinContent/SAIL-VL2-8B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0173 | 2026-09-26T20:05:22Z | 200 | https://huggingface.co/api/models/PerceptronAI/Isaac-0.5?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| F0174 | 2026-09-26T20:05:23Z | 200 | https://ungh.cc/repos/OpenBMB/MiniCPM-o |
| F0175 | 2026-09-26T20:05:24Z | 200 | https://ungh.cc/repos/vikhyat/moondream |
| F0176 | 2026-09-26T20:05:25Z | 200 | https://ungh.cc/repos/apple/ml-fastvlm |
| F0177 | 2026-09-26T20:06:30Z | 404 | https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/raw/main/LICENSE |
| F0179 | 2026-09-26T20:06:31Z | 200 | https://raw.githubusercontent.com/deepseek-ai/DeepSeek-VL2/HEAD/LICENSE-MODEL |
| F0180 | 2026-09-26T20:06:31Z | 200 | https://raw.githubusercontent.com/deepseek-ai/Janus/HEAD/LICENSE-MODEL |
| F0182 | 2026-09-26T20:06:31Z | 401 | https://huggingface.co/nvidia/Eagle2.5-8B/raw/main/LICENSE |
| F0183 | 2026-09-26T20:06:32Z | 200 | https://huggingface.co/apple/FastVLM-7B/raw/main/LICENSE |
| F0184 | 2026-09-26T20:06:32Z | 200 | https://raw.githubusercontent.com/apple/ml-fastvlm/HEAD/LICENSE_MODEL |
| F0185 | 2026-09-26T20:06:32Z | 200 | https://huggingface.co/LiquidAI/LFM2.5-VL-1.6B/raw/main/LICENSE |
| F0186 | 2026-09-26T20:06:32Z | 200 | https://mistral.ai/licenses/MRL-0.1.md |
| F0187 | 2026-09-26T20:06:33Z | 200 | https://huggingface.co/api/models/mistralai/Pixtral-12B-2409?expand[]=cardData&expand[]=lastModified&expand[]=downloads |
| F0188 | 2026-09-26T20:06:33Z | 200 | https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/ |
| F0189 | 2026-09-26T20:06:33Z | 200 | https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/ |
| F0190 | 2026-09-26T20:06:34Z | 200 | https://ai.google.dev/gemma/terms |
| F0191 | 2026-09-26T20:06:34Z | 401 | https://huggingface.co/facebook/Perception-LM-8B/raw/main/LICENSE |
| F0193 | 2026-09-26T20:06:35Z | 404 | https://raw.githubusercontent.com/Kwai-Keye/Keye/HEAD/LICENSE |
| F0194 | 2026-09-26T20:06:35Z | 404 | https://raw.githubusercontent.com/inclusionAI/UI-Venus/HEAD/LICENSE |
| F0195 | 2026-09-26T20:06:35Z | 200 | https://huggingface.co/inclusionAI/UI-Venus-2-9B/raw/main/README.md |
| F0196 | 2026-09-26T20:06:35Z | 200 | https://huggingface.co/api/models/moondream/moondream3.1-9B-A2B?expand[]=cardData&expand[]=lastModified&expand[]=downloads |
| F0197 | 2026-09-26T20:06:35Z | 200 | https://huggingface.co/api/models/Hcompany/Holo-3.1-4B?expand[]=cardData&expand[]=lastModified&expand[]=downloads |
| F0198 | 2026-09-26T20:06:36Z | 200 | https://huggingface.co/api/models/Hcompany/Holo2-4B?expand[]=cardData&expand[]=lastModified&expand[]=downloads |
| F0200 | 2026-09-26T20:06:36Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/apple-aiml-research%2Fml-fastvlm |
| F0201 | 2026-09-26T20:06:37Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/m87-labs%2Fmoondream |
| F0202 | 2026-09-26T20:06:37Z | 200 | https://huggingface.co/api/models/zai-org/GLM-4.6V-Flash?expand[]=cardData&expand[]=lastModified&expand[]=downloads |
| F0203 | 2026-09-26T20:06:37Z | 200 | https://huggingface.co/api/models/HuggingFaceM4/idefics2-8b?expand[]=cardData |
| F0204 | 2026-09-26T20:06:37Z | 200 | https://huggingface.co/api/models/OpenGVLab/InternVL3-78B?expand[]=cardData |
| F0205 | 2026-09-26T20:06:54Z | 404 | https://raw.githubusercontent.com/Kwai-Keye/Keye/HEAD/LICENSE.txt |
| F0206 | 2026-09-26T20:06:55Z | 404 | https://raw.githubusercontent.com/Kwai-Keye/Keye/HEAD/LICENSE.md |
| F0207 | 2026-09-26T20:06:55Z | 404 | https://raw.githubusercontent.com/Kwai-Keye/Keye/HEAD/License |
| F0211 | 2026-09-26T20:06:56Z | 404 | https://raw.githubusercontent.com/inclusionAI/UI-Venus/HEAD/LICENSE.txt |
| F0212 | 2026-09-26T20:06:56Z | 404 | https://raw.githubusercontent.com/inclusionAI/UI-Venus/HEAD/LICENSE.md |
| F0213 | 2026-09-26T20:06:56Z | 404 | https://raw.githubusercontent.com/inclusionAI/UI-Venus/HEAD/License |
| F0214 | 2026-09-26T20:07:12Z | 200 | https://raw.githubusercontent.com/VITA-MLLM/VITA/HEAD/License.txt |
| F0215 | 2026-09-26T20:07:37Z | 200 | http://opencompass.openxlab.space/assets/OpenVLM.json |
| F0216 | 2026-09-26T20:07:37Z | 200 | https://mmmu-benchmark.github.io/ |
| F0218 | 2026-09-26T20:07:38Z | 200 | https://huggingface.co/microsoft/Phi-4-multimodal-instruct/raw/main/README.md |
| F0219 | 2026-09-26T20:07:38Z | 200 | https://huggingface.co/baidu/ERNIE-4.5-VL-28B-A3B-PT/raw/main/README.md |
| F0220 | 2026-09-26T20:07:38Z | 200 | https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-BF16/raw/main/README.md |
| F0221 | 2026-09-26T20:07:39Z | 200 | https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16/raw/main/README.md |
| F0223 | 2026-09-26T20:07:39Z | 200 | https://huggingface.co/api/models/google/gemma-4-31B-it?expand[]=cardData&expand[]=pipeline_tag |
| F0224 | 2026-09-26T20:07:39Z | 200 | https://huggingface.co/api/models/zai-org/GLM-5.3-Flash?expand[]=cardData&expand[]=pipeline_tag&expand[]=downloads |
| F0225 | 2026-09-26T20:07:39Z | 200 | https://huggingface.co/api/models/moonshotai/Kimi-K3?expand[]=cardData&expand[]=pipeline_tag&expand[]=downloads |
| F0226 | 2026-09-26T20:07:40Z | 200 | https://huggingface.co/api/models/Qwen/Qwen3.6-27B?expand[]=cardData&expand[]=pipeline_tag&expand[]=downloads |
| F0227 | 2026-09-26T20:09:11Z | 000000 | https://ungh.cc/repos/perceptron-ai-inc/isaac |
| F0229 | 2026-09-26T20:09:16Z | 200 | https://ungh.cc/repos/perceptron-ai-inc/isaac |
| F0230 | 2026-09-26T20:10:20Z | 200 | https://ungh.cc/repos/AIDC-AI/Ovis |
| F0232 | 2026-09-26T20:10:21Z | 200 | https://huggingface.co/api/models/moondream/moondream3.1-9B-A2B?expand[]=cardData&expand[]=gated |
| F0233 | 2026-09-26T20:10:29Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ATH-MaaS%2FOvis |
| F0234 | 2026-09-26T20:28:15Z | 200 | https://huggingface.co/api/models?author=ATH-MaaS&search=Ovis&sort=downloads&direction=-1&limit=200 |
| F0235 | 2026-09-26T20:28:16Z | 200 | https://huggingface.co/api/models?author=Salesforce&search=instructblip&sort=downloads&direction=-1&limit=100 |
| F0236 | 2026-09-26T20:28:16Z | 200 | https://huggingface.co/api/models?author=OpenGVLab&search=InternVL&sort=downloads&direction=-1&limit=1000 |
| F0237 | 2026-09-26T20:28:16Z | 200 | https://huggingface.co/api/models?author=google&search=paligemma&sort=downloads&direction=-1&limit=1000 |
| F0238 | 2026-09-26T20:28:17Z | 200 | https://huggingface.co/blog/smolvlm |
| F0239 | 2026-09-26T20:28:17Z | 200 | https://arxiv.org/abs/2601.10611 |
| F0240 | 2026-09-26T20:28:17Z | 200 | https://raw.githubusercontent.com/QwenLM/Qwen3-VL/HEAD/README.md |
| F0241 | 2026-09-26T20:28:17Z | 200 | https://raw.githubusercontent.com/zai-org/GLM-V/HEAD/README.md |
| F0242 | 2026-09-26T20:28:18Z | 200 | https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct/raw/main/README.md |
| F0243 | 2026-09-26T20:28:18Z | 200 | https://huggingface.co/microsoft/Florence-2-large/raw/main/README.md |
| F0244 | 2026-09-26T20:28:18Z | 200 | https://huggingface.co/api/models?author=Qwen&search=Omni&sort=downloads&direction=-1&limit=100 |
| F0245 | 2026-09-26T20:28:52Z | 200 | https://huggingface.co/api/models/ATH-MaaS/Ovis2.6-30B-A3B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt |
| W0002 | 2026-09-26T20:00:11Z | WebSearch | open source omni model any-to-any release 2026 text image audio video |
| W0003 | 2026-09-26T20:00:11Z | WebSearch | OpenCompass multimodal leaderboard open-source VLM 2026 |
| W0004 | 2026-09-26T20:00:59Z | WebSearch | Qwen3.5 native multimodal vision language model release Qwen3-VL successor |
| W0005 | 2026-09-26T20:00:59Z | WebSearch | new vision-language model open weights Hugging Face released August September 2026 |
| W0007 | 2026-09-26T20:00:59Z | WebFetch | https://huggingface.co/blog/state-of-open-models-summer-2026 |
| W0009 | 2026-09-26T20:00:59Z | WebFetch | https://huggingface.co/blog/CohereLabs/meet-north-micro-vision-instruct |
| W0010 | 2026-09-26T20:00:59Z | WebFetch | https://www.alibabacloud.com/blog/qwen3-5-towards-native-multimodal-agents_602894 |
| W0011 | 2026-09-26T20:00:59Z | WebSearch | Meta "Muse Glimmer" open weights vision model |
| W0012 | 2026-09-26T20:00:59Z | WebSearch | Qwen3-VL Hugging Face Qwen3-VL-235B-A22B license release |
| W0013 | 2026-09-26T20:01:22Z | WebSearch | InternVL 2026 release OpenGVLab new version |
| W0014 | 2026-09-26T20:01:22Z | WebSearch | GLM-4.6V OR GLM-5V vision model Zhipu open source 2026 |
| W0015 | 2026-09-26T20:01:22Z | WebSearch | MiniCPM-V 4.5 OR MiniCPM-V 5 OR MiniCPM-o 4 release OpenBMB 2026 |
| W0016 | 2026-09-26T20:01:22Z | WebSearch | small vision language model on-device 2026 open weights LFM2-VL FastVLM SmolVLM Moondream |
| W0017 | 2026-09-26T20:01:43Z | WebSearch | open-source omni-modal model 2026 Qwen3.5-Omni Ming-flash-omni LongCat-Flash-Omni Nemotron Omni |
| W0018 | 2026-09-26T20:01:43Z | WebSearch | GUI agent vision language model open weights UI-TARS Holo computer use 2026 |
| W0019 | 2026-09-26T20:01:43Z | WebSearch | video understanding open-source multimodal LLM 2026 long video model release |
| W0020 | 2026-09-26T20:01:43Z | WebSearch | unified multimodal understanding and generation model open source BAGEL Janus Show-o Emu3.5 2026 |
| W0021 | 2026-09-26T20:07:12Z | WebFetch | https://github.com/Kwai-Keye/Keye |
| W0022 | 2026-09-26T20:07:12Z | WebFetch | https://github.com/VITA-MLLM/VITA |
| W0023 | 2026-09-26T20:07:12Z | WebFetch | https://github.com/inclusionAI/UI-Venus |
| W0024 | 2026-09-26T20:09:00Z | WebSearch | Seed1.5-VL OR Seed-VL ByteDance vision-language model API |
| W0025 | 2026-09-26T20:09:00Z | WebSearch | Perceptron Isaac 0.5 perceptive language model release license |
| W0026 | 2026-09-26T20:09:00Z | WebSearch | H Company Holo3 open weights computer use model release |
| W0027 | 2026-09-26T20:10:38Z | WebFetch | https://moondream.ai/licenses/model/1.0 |

## 7. Parked candidates

| name | reason | evidence | source URL | fetch date |
|---|---|---|---|---|
| Qwen3.5 / Qwen3.6 / Qwen3.8 (native VL) | already mapped: `qwen` (base_pretrained). Vendor calls Qwen3.5 'a native vision-language model'; Qwen3.6-27B pipeline image-text-to-text. Stay. | W0010, F0226, F0001 | https://huggingface.co/api/models/Qwen/Qwen3.6-27B | 2026-09-26 |
| Gemma 3 / Gemma 4 (vision, any-to-any E2B/E4B) | already mapped: `gemma`. gemma-4-31B-it is image-text-to-text, Apache-2.0 (F0223); E2B/E4B/12B any-to-any (F0003). Stay. | F0223, F0003 | https://huggingface.co/api/models/google/gemma-4-31B-it | 2026-09-26 |
| Llama 3.2 Vision / Llama 4 Scout, Maverick | SKU of `llama` (Llama-3.2-11B/90B-Vision, Llama-4 image-text-to-text). | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Phi-3.5-vision / Phi-4-multimodal | SKU of `phi`: card lists multimodal-instruct among the Phi-4 family (F0218). | F0018, F0218 | https://huggingface.co/microsoft/Phi-4-multimodal-instruct | 2026-09-26 |
| ERNIE-4.5-VL | SKU of `ernie`: card presents it among 'ERNIE 4.5 models' with joint multimodal MoE pretraining (F0219). | F0035, F0219 | https://huggingface.co/baidu/ERNIE-4.5-VL-28B-A3B-PT | 2026-09-26 |
| Kimi K3 / K2.5 / K2.6 (image-text-to-text) | already mapped: `kimi` (F0225). | F0225, F0001 | https://huggingface.co/api/models/moonshotai/Kimi-K3 | 2026-09-26 |
| GLM-5.3-Flash / GLM-5V-Turbo | already mapped: `glm`; GLM-5.3-Flash image-text-to-text (F0224). | F0224, W0014 | https://huggingface.co/api/models/zai-org/GLM-5.3-Flash | 2026-09-26 |
| DeepSeek-V4-Flash-Vision-Exp / V4.1-Flash | SKU of `deepseek`. | F0001, F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| Inkling (Thinking Machines) | already mapped: `inkling` (base_pretrained). | W0007, F0001 | https://huggingface.co/blog/state-of-open-models-summer-2026 | 2026-09-26 |
| MiniMax-M3 | already mapped: `minimax`. | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| MiniCPM5 | already mapped: `minicpm` (text line). | F0011 | https://huggingface.co/api/models?author=openbmb&search=MiniCPM-o | 2026-09-26 |
| Muse Glimmer (Meta, 30B, Apache-2.0) | boundary -> finetuned_chat / base_pretrained: agentic general model 'with built-in vision support' (W0011). Absent from the map: flag to maintainer. | W0011, F0001 | https://venturebeat.com/technology/meta-returns-to-open-source-with-muse-glimmer-an-apache-2-0-licensed-30b-parameter-ai-model-optimized-for-agents-available-now | 2026-09-26 |
| Step-3.7-Flash (StepFun) | boundary -> finetuned_chat (general flagship, image-text-to-text). | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Ling-3.0-flash-VL (inclusionAI) | SKU of the Ling family (absent from map). | F0005 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=trendingScore&direction=-1&limit=100 | 2026-09-26 |
| Apriel-1.5-15b-Thinker (ServiceNow) | boundary -> finetuned_chat (general reasoning model with vision). | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| HyperCLOVAX-SEED-Think-32B (Naver) | boundary -> finetuned_chat. | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Apertus-v1.5-8B (Swiss AI) | boundary -> base_pretrained (general LLM listed under image-text-to-text). | F0001 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| Command A Vision (Cohere) | SKU of tail `command-a`. | F0042 | https://huggingface.co/api/models?author=CohereLabs&search=vision | 2026-09-26 |
| Seed1.5-VL (Doubao vision API) | closed; SKU of mapped `doubao-seed` (API model id doubao-1-5-thinking-vision-pro, W0024). | W0024 | https://github.com/ByteDance-Seed/Seed1.5-VL | 2026-09-26 |
| Qwen3.5-Omni / Qwen3.8-Omni-Flash | closed tier of `qwen-omni`: Qwen3.5-Omni 'released ... as proprietary' (W0017); no Qwen3.5- or Qwen3.8-Omni weights under author=Qwen (F0244, only Qwen2.5-/Qwen3-Omni). | W0004, W0017, F0244 | https://www.marktechpost.com/2026/03/30/alibaba-qwen-team-releases-qwen3-5-omni-a-native-multimodal-model-for-text-audio-video-and-realtime-interaction/ | 2026-09-26 |
| Holo3-122B-A10B | SKU of `holo` (API-only flagship, W0026). | W0026 | https://hcompany.ai/holo3.1 | 2026-09-26 |
| Qwen-VL-Max / Qwen-VL-Plus | closed API tier of `qwen-vl` (OpenVLM snapshot). | F0215 | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| GLM-4v-Plus | closed API tier of `glm-v` (OpenVLM snapshot). | F0215 | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| SenseNova-V6 / V6.5-Pro | closed long-tail (OpenVLM, OpenSource=No). | F0215 | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| Step-1o / Step-1.5V | closed long-tail (OpenVLM, OpenSource=No). | F0215 | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| HunYuan-Standard-Vision | closed long-tail (OpenVLM, OpenSource=No). | F0215 | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| CongRong-v2.0 | closed long-tail (OpenVLM, OpenSource=No). | F0215 | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| GPT-5 / Gemini-2.5-Pro / Claude 3.7 Sonnet (leaderboard top) | already mapped: `gpt-5`, `gemini-pro`, `claude-sonnet` (finetuned_chat). | F0215 | http://opencompass.openxlab.space/assets/OpenVLM.json | 2026-09-26 |
| InternVL-U | SKU of `internvl` (4B unified understanding+generation variant, W0013). | W0013 | https://github.com/OpenGVLab/InternVL-U | 2026-09-26 |
| CogVLM2 / CogAgent / GLM-Edge-V | SKU (predecessors) of `glm-v`. | F0023, F0004 | https://huggingface.co/api/models?author=zai-org&search=V | 2026-09-26 |
| BLIP3o / BLIP3o-NEXT (Salesforce) | boundary -> media_generation (generation and editing line; 2025-11 checkpoints). | F0039 | https://huggingface.co/api/models?author=Salesforce&search=blip | 2026-09-26 |
| xGen-MM (Salesforce) | SKU of `blip` (proposed fold; same vendor lab, 1,772 / 30d). | F0040 | https://huggingface.co/api/models?author=Salesforce&search=xgen-mm | 2026-09-26 |
| Qwen2.5-VL-7B-Instruct-NVFP4 (nvidia) | SKU of `qwen-vl` (third-party quantization). | F0028 | https://huggingface.co/api/models?author=nvidia&search=VL | 2026-09-26 |
| Llama-3.1-Nemotron-Nano-VL-8B | member of `nemotron-vl`. | F0028 | https://huggingface.co/api/models?author=nvidia&search=VL | 2026-09-26 |
| VideoChat-Flash / VideoChat-R1 / VideoChat3 | identity unclear: OpenGVLab and MCG-NJU both publish VideoChat checkpoints (F0004); not resolved this run. | F0004, W0019 | https://www.alphaxiv.org/abs/2607.14935 | 2026-09-26 |
| AutoGLM-Phone-9B | identity unclear (phone agent model; relation to GLM-V not verified). | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Qianfan-VL (Baidu) | identity unclear (separately named 3B/8B; not researched beyond listing, 539 / 30d). | F0035 | https://huggingface.co/api/models?author=baidu&search=VL | 2026-09-26 |
| JoyAI-VL-Interaction (JD) | identity unclear (not researched beyond listing). | F0004 | https://huggingface.co/api/models?pipeline_tag=video-text-to-text&sort=downloads&direction=-1&limit=100 | 2026-09-26 |
| Marlin-2B (NemoStation) | identity unclear (not researched beyond listing). | F0004 | https://huggingface.co/api/models?pipeline_tag=video-text-to-text&sort=downloads&direction=-1&limit=100 | 2026-09-26 |
| ZDTaichu5.0-9B (TaichuAI) | identity unclear (not researched beyond listing). | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Mage-VL (Microsoft) | identity unclear (not researched beyond listing). | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| LensVLM-9B (Apple) | identity unclear (not researched beyond listing). | F0005 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=trendingScore&direction=-1&limit=100 | 2026-09-26 |
| LocateAnything-3B (NVIDIA) | identity unclear (grounding model; possible classic_ml_cv). | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| OpenOmni (academic, NeurIPS 2025) | no addressable model artifact verified this run. | W0002 | https://github.com/RainBowLuoCS/OpenOmni | 2026-09-26 |
| Show-o2 / MMaDA | not verified this run; unified gen models, contested with media_generation. | W0020 | https://arxiv.org/pdf/2506.15564 | 2026-09-26 |
| Cosmos-Reason 1/2 (NVIDIA) | boundary -> robotics_embodied / world_models (928,415 / 30d). | F0062 | https://huggingface.co/api/models?author=nvidia&search=Cosmos-Reason | 2026-09-26 |
| MolmoAct / MolmoAct2 (Ai2) | boundary -> robotics_embodied (pipeline robotics). | F0012 | https://huggingface.co/api/models?author=allenai&search=Molmo | 2026-09-26 |
| HY-Embodied-0.5 (Tencent) | boundary -> robotics_embodied. | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| Isaac (Perceptron) | boundary -> robotics_embodied: Isaac 0.5 is 'for video understanding, embodied reasoning, and robot control' (W0025); HF pipeline robotics (F0061); repo perceptron-ai-inc/isaac (F0229). | W0025, F0061, F0229 | https://huggingface.co/PerceptronAI/Isaac-0.5 | 2026-09-26 |
| MedGemma | boundary -> scientific_ai_models (domain model; absent from map). | F0001 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| diffusiongemma / omni-dreams | boundary -> media_generation. | F0001, F0031 | https://huggingface.co/api/models?author=nvidia&search=Omni | 2026-09-26 |
| chandra / chandra-ocr-2 (Datalab) | boundary -> document_conversion. | F0001 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| surya-ocr-2 (Datalab) | boundary -> document_conversion. | F0001 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| Unlimited-OCR / Qianfan-OCR (Baidu) | boundary -> document_conversion. | F0001, F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| HunyuanOCR | boundary -> document_conversion. | F0001 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| GOT-OCR2.0 (StepFun) | boundary -> document_conversion. | F0001 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| Nanonets-OCR / OCR2 | boundary -> document_conversion. | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| LightOnOCR-2 | boundary -> document_conversion. | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| PaddleOCR-VL | SKU of mapped `paddleocr` (document_conversion). | F0002, F0005 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| granite-docling / SmolDocling | boundary -> document_conversion (next to mapped `docling`). | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| MinerU2.5 | SKU of mapped `mineru`. | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| RolmOCR / OCRFlux / Dolphin / OvisOCR2 / typhoon-ocr / jina-ocr / TeleOCR | boundary -> document_conversion (class of OCR-first VLMs). | F0001, F0002, F0005 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| dots.ocr / DeepSeek-OCR / olmOCR | already mapped (document_conversion). | F0001, F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |
| nemotron-colembed-vl / llama-nemotron-embed-vl / rerank-vl / omni-embed-nemotron | boundary -> embeddings_retrieval. | F0028, F0031 | https://huggingface.co/api/models?author=nvidia&search=VL | 2026-09-26 |
| Ming-omni-tts / Ming-UniAudio / Step-Audio-2-mini / A.X-K2-Raon-Speech / moondream parakeet / VITA-QinYu | boundary -> speech_audio. | F0045, F0003, F0016, F0050 | https://huggingface.co/api/models?pipeline_tag=any-to-any&sort=downloads&direction=-1&limit=100 | 2026-09-26 |
| UI-TARS-desktop | boundary -> orchestration_agents (agent app, software). | W0018 | https://themenonlab.blog/blog/ui-tars-desktop-open-source-gui-agent | 2026-09-26 |
| OmniParser (Microsoft) | boundary -> orchestration_agents / classic_ml_cv (screen parser, not a VLM). | F0002 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=likes&direction=-1&limit=200 | 2026-09-26 |
| vllm-omni / mlx-vlm / lmms-eval / VLMEvalKit | already mapped (vllm, mlx-vlm, lmms-eval, vlmevalkit). | W0002, W0003 | https://github.com/vllm-project/vllm-omni | 2026-09-26 |
| Community fine-tunes and quantizations (unsloth, DavidAU, HauhauCS, bartowski, lmstudio-community ...) | not products: derivatives of mapped families (class). | F0001, F0002, F0005 | https://huggingface.co/api/models?pipeline_tag=image-text-to-text&sort=downloads&direction=-1&limit=200 | 2026-09-26 |

## 8. Reconciled counts

A **raw signal** is one mention of a candidate in one source: the brief's lead list, one
WebSearch/WebFetch call (W id), one Hub listing (F0001-F0005, the family listings) or the OpenVLM
snapshot (F0215). Signals are counted once per candidate per source. Per-candidate source lists
are in `.evidence.json` (`sig`) for accepted rows and in the fifth (`signals`) field of
`tools/parked.py` for parked ones. That field is a superset of section 7's evidence column.

Every accepted row's source list includes its own family listing(s), the F ids in its 6b
adoption cell. It also includes each top listing (F0001-F0005) that contains the row's declared
flagship or one of its six most-downloaded member checkpoints. The same rule applies to all 47
rows (tools/build.py, `disc`).

- raw_signals = **280**
- duplicate_signals = **164** (the same candidate seen in a second or later source)
- unique_candidates = **116**
- accepted = **47**
- parked = **69** (one row per line in section 7; the OCR tail, the community derivatives and the
  speech SKUs are grouped as classes, one row each)

280 = 164 + 116, and 116 = 47 + 69.

Candidates not named in the brief:
- **Surfaced by open discovery** (open WebSearch, HF top-N listings, OpenVLM snapshot):
  north-vision (W0005), fara, step-vl and aya-vision (F0002), ui-tars (F0001), blip (F0001),
  keye-vl, videollama, internvideo, moss-vl and vita (F0004), sensenova-u and nemotron-omni
  (F0003, W0002), sail-vl (W0003), ovis (OpenVLM, F0215), ui-venus and holo (W0018, W0026).
- **Named in the researcher's own queries, then verified live:** perception-lm (F0053),
  mimo-vl (F0048), nemotron-vl (F0028), longcat-omni (F0054, W0017), fastvlm and lfm-vl (W0016),
  bagel and emu (W0020).
- Parked side: Muse Glimmer, Inkling, Isaac, Cosmos-Reason, MolmoAct, BLIP3o, the OCR-VLM class
  and the 9 identity-unclear listings.

## 9. Open questions for the maintainer

1. **Scope.** Which scope does the category take: (a) understanding VLMs only, including video
   and GUI (37 rows); (b) (a) plus omni (43); or (c) (b) plus unified understanding+generation
   (47)? **Recommend (b).** Omni has no other home now that `speech_audio` has ruled it out.
   The unified four wait on `media_generation`'s ruling.
2. **Membership test.** Do natively multimodal general LLMs (Qwen3.5+, Gemma 4, Llama 4, Kimi
   K3, GLM-5.3, Muse Glimmer) stay in `base_pretrained`/`finetuned_chat`, so that this category
   holds only lines marketed separately as vision/omni models? **Recommend yes.** Otherwise the
   category duplicates the frontier LLM rows, and it keeps losing rows as vendors fold VL into
   the main line, as Qwen has (W0010, F0006).
3. **Vendor sub-lines inside a family.** Does nemotron-vl / nemotron-omni / paligemma each get
   its own row, or is each parked as a SKU of `nemotron` / `gemma`? **Recommend own rows**,
   following the nemotron-embed, nemotron-rerank, embeddinggemma and codegemma precedent.
   They answer a different category's question.
4. **Qwen-VL after Qwen3.5.** The line has shipped nothing since 2025-10-31 (F0006), and its
   successor is the mapped `qwen`. Keep `qwen-vl` as a row, or fold it into `qwen`?
   **Recommend keep.** It is the category's adoption leader (46.8M downloads/30d, F0006). Record
   `qwen` as the successor in prose, and use `end_of_life` only if Alibaba announces one.
5. **GUI / computer-use VLMs** (ui-tars, ui-venus, holo, fara): here, or held for an agent
   category? **Recommend here.** They are weights you download, and the agent apps built on them
   (UI-TARS-desktop) go to `orchestration_agents`.
6. **OCR-first VLMs** (12 section-7 rows naming 24 models, 19 of them unmapped): confirm they belong in `document_conversion`?
   **Recommend yes**, matching how that category already holds dots-ocr, deepseek-ocr and olmocr.
7. **Closed comparators.** Add none and let the closed frontier (gpt-5, gemini-pro,
   claude-sonnet in `finetuned_chat`) serve as the comparator, or add a VLM-specific closed row
   such as Seed1.5-VL (an API SKU of `doubao-seed`, W0024)? **Recommend none.** The best closed
   VLMs are the general frontier models (OpenVLM top of table, F0215), which the map already
   carries, so under ADR-005 a new closed row here would be long tail.
8. **LLaVA's measurement identity.** Most LLaVA usage runs through Hugging Face's official
   `llava-hf` conversions (3,261,856/30d, F0021), not `lmms-lab` (77,776, F0020). Declare
   `lmms-lab/LLaVA-OneVision-1.5-8B-Instruct` (current release) or `llava-hf/llava-1.5-7b-hf`?
   **Recommend the lmms-lab current release**, with adoption research summing both orgs.
9. **Custom licenses to tier** (section 5): LFM Open License v1.0 (revenue cap), Moondream
   Model License 1.0 (hosting ban), Apple ML Research Model, VITA1.5 terms, NVIDIA Open Model
   License vs Agreement, NVIDIA nsclv1, FAIR NC research. **Recommend:** research-only and NC to
   `commercial_forbidden`; the revenue-capped and hosting-restricted ones to the restricted tier
   already used for Llama-style community licenses; both NVIDIA open-model texts to the same
   tier as each other (both say "commercially usable", F0188, F0189).
10. **ui-venus**, whose weight license is "pending final confirmation" (F0195): seed now as
    signal-only and re-check before promotion, or hold? **Recommend seed now.** A registry row
    carries no openness score.
11. **Capability quantity.** Adopt the breadth-of-grounded-understanding ladder in section 4,
    with benchmark averages only as tie-breaks, instead of MMMU? **Recommend yes.** OpenVLM covers
    25/47 rows and stops at 2025-09-17 (F0215), and MMMU's test answers have been public since
    2026-02-12 (F0216).
12. **New org slugs.** rows.yaml uses 13 org slugs that have no `sources/organizations/` record:
    ath-maas, bytedance-douyin, h-company, kuaishou, liquid-ai, m87-labs, meituan,
    nyu-visionx, openmoss, rhymes-ai, salesforce (already used by a registry row in
    `embeddings_retrieval`), sensetime and stepfun. Create them at promotion, or map some onto
    existing orgs (for example bytedance-douyin onto `bytedance-seed-volcano-engine`)?
    **Recommend** one new org each, except where an existing org record shows the same legal
    entity.
13. **VITA's org.** The License.txt copyright is Tencent (THL A29, F0214), but OpenCompass
    credits NJU, and credits Long-VITA to Tencent Youtu Lab and Nanjing University (F0215). Use
    `tencent`, `nanjing-university`, or a joint org? **Recommend `tencent`**, since it is the
    licensor of the weights. Flagged.
