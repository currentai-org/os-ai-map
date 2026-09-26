# Prose fixes for audit issues 4, 7, 9, 10-14, 17, 18, 20. Applied to head.md / tail.md templates.
T='research/multimodal_models/tools/'
h=open(T+'head.md').read(); t=open(T+'tail.md').read()
def r(s,a,b):
    assert a in s,a[:70]; return s.replace(a,b)
h=r(h,"""UTC. A cited id whose HTTP code is not 200 (F0177, F0182, F0191, F0193, F0194, F0205-F0213,
F0231) is cited only as evidence that a file was gated or absent, never as the source of a
license or number.""","""UTC. The non-200 ids cited in sections 6b and 7 (F0177, F0182, F0191, F0193, F0194,
F0205-F0207, F0211-F0213) show only that a file was gated or absent. None of them is the source
of a license or a number. Web-log timestamps were stamped when each batch of calls was logged,
not per call, so several W rows share a second. All of them fall on 2026-09-26.""")
h=r(h,"""- candidates active in the last 12 months (newest checkpoint, repo push or HF lastModified on or
  after 2025-09-26): **34** of 47. Dormant: smolvlm, idefics, florence-2, kimi-vl, deepseek-vl,
  aria, nvlm, paligemma, mimo-vl, perception-lm, sail-vl, videollama, janus. Pixtral counts as
  active only on an HF lastModified of 2026-06-02 (F0187); its newest checkpoint is 2024-11-14
  (F0026).""","""- candidates active in the last 12 months: **30** of 47. The rule is one test: the newest
  vendor member checkpoint, or a push to a non-archived repo, dated on or after 2025-09-26. HF
  lastModified is not counted, because a card edit is not a release. Dormant (17): smolvlm,
  idefics, florence-2, kimi-vl, deepseek-vl, pixtral, aria, nvlm, paligemma, blip, aya-vision,
  mimo-vl, perception-lm, sail-vl, videollama, vita, janus. Understanding-only scope: 22 of 37
  active.""")
h=r(h,"""Florence-2 is a small seq2seq vision model. The InternVideo""","""Florence-2 is "an advanced vision foundation model that uses a prompt-based approach" for captioning, detection and segmentation (F0243). The InternVideo""")
h=r(h,"| deepseek-ocr, dots-ocr, olmocr, paddleocr, mineru | document_conversion | stay | OCR-first. The same rule parks 20 OCR VLMs found here. |","| deepseek-ocr, dots-ocr, olmocr, paddleocr, mineru | document_conversion | stay | OCR-first. The same rule parks the 21 unmapped OCR-first models found here (12 section-7 rows, 24 names, 3 of them already mapped). |")
h=r(h,"""The quantity that orders the whole set, including omni and GUI, is **breadth of grounded
understanding**. Each rung nests the one below:""","""The quantity that orders the whole set, including omni and GUI, is **breadth of grounded
understanding**. Each rung nests the one below. Examples without a fetch id are illustrative
placements for the ladder-builder, not verified capability claims.""")
h=r(h,"""3. **Video and long context.** Temporal understanding over long video (Qwen-VL: Qwen3-VL's
   "256K-token native context ... hours-long videos", W0019; InternVL, MiniCPM-V, VideoLLaMA,
   MOSS-VL).""","""3. **Video and long context.** Temporal understanding over long video (Qwen-VL: Qwen3-VL's
   "Native 256K context, expandable to 1M; handles books and hours-long video", F0240;
   VideoLLaMA and MOSS-VL are tagged video-text-to-text, F0004; InternVL and MiniCPM-V
   illustrative).""")
h=r(h,"""   "pixels in and actions out", W0018; Holo, Fara, UI-Venus; GLM-4.6V's native tool calling,
   W0014).
5. **Omni.** Audio and video in with streaming speech out, in real time (Qwen-Omni: Qwen3-Omni
   "understanding text, audio, images, and video, as well as generating speech in real time",
   W0017; MiniCPM-o 4.5 full-duplex, W0015; Nemotron Nano Omni).

**Top-rung anchor: `qwen-omni`**, or `minicpm-o` if omni is excluded and rung 4 becomes the top.""","""   "pixels in and actions out", W0018; Holo, W0026; Fara and UI-Venus illustrative; GLM-V's
   "native Function Calling", F0241).
5. **Omni in.** Audio and video understood natively alongside images and text, with text out
   (Nemotron Nano Omni, whose card gives output type Text, F0221; LongCat-Flash-Omni and
   Ming-Omni are tagged any-to-any, F0003/F0054).
6. **Omni in, speech out.** Rung 5 plus streaming speech generation (Qwen-Omni: Qwen3-Omni
   "delivers real-time streaming responses in both text and natural speech", F0242; MiniCPM-o
   4.5 "full-duplex multimodal live streaming", W0015).

**Top-rung anchor: `qwen-omni`.** If omni is excluded, rung 4 is the top and `ui-tars` anchors
it.""")
h=r(h,"""1. **Single-image perception.** Captioning, VQA, detection prompts on one image (BLIP,
   PaliGemma, Florence-2).""","""1. **Single-image perception.** Captioning, VQA, detection prompts on one image (BLIP's
   captioning and VQA checkpoints are tagged image-to-text and visual-question-answering, F0039;
   Florence-2 "captioning, object detection, and segmentation", F0243; PaliGemma illustrative).""")
h=r(h,"""2. **Documents and multi-image.** OCR-grade text reading, charts, several images interleaved
   (Idefics, SmolVLM, Moondream, Aya Vision, North Micro Vision).""","""2. **Documents and multi-image.** OCR-grade text reading, charts, several images interleaved
   (North Micro Vision: "document understanding, charts, tables, and visual grounding", W0009;
   Idefics, SmolVLM, Moondream and Aya Vision illustrative).""")
h=r(h,"""Most rows are a vision encoder grafted onto
  someone else's LLM (Holo on Qwen 3.5, W0026; MiniCPM-V 4.5 on Qwen3-8B + SigLIP2, W0015).""","""Several rows are a vision stack on
  someone else's LLM (Holo3.1 fine-tuned from Qwen 3.5, W0026; MiniCPM-o 4.5 built on SigLip2,
  Whisper-medium, CosyVoice2 and Qwen3-8B, W0015; InternVL3-78B carrying the Qwen license,
  F0204). How many do is not measured here.""")
t=r(t,"""- raw_signals = **223**
- duplicate_signals = **108** (the same candidate seen in a second or later source)
- unique_candidates = **115**
- accepted = **47**
- parked = **68** (one row per line in section 7; the OCR tail, the community derivatives and the
  speech SKUs are grouped as classes, one row each)

223 = 108 + 115, and 115 = 47 + 68.

Candidates this sweep surfaced that the brief did not name (search or listing discovery):
north-vision, holo, fara, ui-venus, ui-tars, moss-vl, sensenova-u, longcat-omni,
nemotron-omni, nemotron-vl, keye-vl, step-vl, ovis, lfm-vl, aya-vision, fastvlm, mimo-vl,
perception-lm, sail-vl, blip, videollama, internvideo, emu, bagel, vita. On the parked side:
Muse Glimmer, Inkling, Isaac, Cosmos-Reason, MolmoAct, the OCR-VLM class and the 9
identity-unclear listings.""","""Every accepted row's source list includes its own family listing(s) (the F ids in its 6b
adoption cell). This applies to all 47 rows under the same rule.

- raw_signals = **272**
- duplicate_signals = **156** (the same candidate seen in a second or later source)
- unique_candidates = **116**
- accepted = **47**
- parked = **69** (one row per line in section 7; the OCR tail, the community derivatives and the
  speech SKUs are grouped as classes, one row each)

272 = 156 + 116, and 116 = 47 + 69.

Candidates not named in the brief:
- **Surfaced by open discovery** (open WebSearch, HF top-N listings, OpenVLM snapshot):
  north-vision (W0005), fara, step-vl and aya-vision (F0002), ui-tars (F0001), blip (F0001),
  keye-vl, videollama, internvideo, moss-vl and vita (F0004), sensenova-u and nemotron-omni
  (F0003, W0002), sail-vl (W0003), ovis (OpenVLM, F0215), ui-venus and holo (W0018, W0026).
- **Named in the researcher's own queries, then verified live:** perception-lm (F0053),
  mimo-vl (F0048), nemotron-vl (F0028), longcat-omni (F0054, W0017), fastvlm and lfm-vl (W0016),
  bagel and emu (W0020).
- Parked side: Muse Glimmer, Inkling, Isaac, Cosmos-Reason, MolmoAct, BLIP3o, the OCR-VLM class
  and the 9 identity-unclear listings.""")
t=r(t,"""6. **OCR-first VLMs** (20 parked, section 7)""","""6. **OCR-first VLMs** (12 section-7 rows naming 24 models, 21 of them unmapped)""")
t=t.rstrip()+"""
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
"""
open(T+'head.md','w').write(h); open(T+'tail.md','w').write(t); print('ok')
