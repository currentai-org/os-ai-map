
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
