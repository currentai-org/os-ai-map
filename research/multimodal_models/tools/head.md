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
