# Audit: multimodal_models sweep (2026-09-26)

An independent auditor wrote this report. It follows RUNBOOK.md, "Finishing: independent audit, then push".
Live re-fetches were made on 2026-09-26 with curl against ecosyste.ms, the Hugging Face API,
raw.githubusercontent.com, arxiv.org, huggingface.co/blog, moondream.ai and opencompass. They
were saved outside `research/`. Nothing in the sweep directory was modified except this file.

## Verdicts

| # | check | verdict |
|---|---|---|
| 1 | Re-fetch 15 claims live | **FAIL**. The 15-row sample is clean: 14 match and 1 has a wrong license description (ui-venus). But off-sample re-fetches triggered by the sample found one adoption figure off by about 6x (ovis) and two activity dates taken from non-member checkpoints (blip, vita). |
| 2 | Unsourced facts / log integrity | **FAIL**. Every cited id exists, and every non-200 id is used legitimately (gating or absence only). But 5 quoted excerpts do not appear in the cited W log row, 3 quotes are pinned to the wrong F id, and the header's list of non-200 ids is inaccurate. |
| 3 | Every artifact resolves live | **PASS**. All 47 HF models return 200 and all 34 GitHub repos return 200 on ecosyste.ms with a matching canonical `full_name`. The only archived repo is salesforce/LAVIS, and the sweep says it is archived. |
| 4 | Schema and dedup | **PASS**. rows.yaml validates against `docs/schemas/registry.schema.json` and is identical to the 6a block. No slug, alias or artifact collides with corpus-index.tsv, `sources/products/*.yaml` or `sources/registry/*.yaml`. There is one disclosure gap on new org slugs (issue 17). |
| 5 | Counts reconcile / section-2 metrics | **FAIL**. Both equations hold arithmetically (223 = 108 + 115; 115 = 47 + 68), and 47 / 35 orgs / 8.5% / 34 active reproduce exactly from 6b. But the raw-signal count does not follow the rule the sweep states, and the active count 34 applies its own activity rule inconsistently and counts two rows on dates from non-member checkpoints. |
| 6 | Recency and breadth | **FAIL**. Recency passes: all 233 F rows and 27 W rows are dated 2026-09-26 between 20:00:11Z and 20:10:38Z. Breadth passes: 25 accepted rows were not named in the brief. Recall passes do not: section 4 contradicts the sweep's own fetch on Nemotron Omni, section 5 misattributes a W0015 fact, and several prose quotes and characterizations have no logged source. |

## 15 re-fetched claims (every third 6b row: 2, 5, 8, ... 44)

"Family" means the sweep's family listing, re-fetched with the same URL. The live sums were
identical to the saved bodies (same-day cache).

| # | slug | claim (license / activity / adoption / identity) | sweep value | live value | verdict |
|---|---|---|---|---|---|
| 1 | internvl | weights license; code license; push; flagship 30d dl; repo | Apache-2.0; MIT; 2025-09-22; 50,683; OpenGVLab/InternVL, not archived | apache-2.0; mit; 2025-09-22; 50,683; OpenGVLab/InternVL, archived=false | PASS (family "100 checkpoints" is the `limit=100` cap: 155 exist, sum 2,923,773 vs 2,920,564, +0.1%) |
| 2 | smolvlm | license; HF lastModified; flagship dl; family sum | Apache-2.0; 2025-04-08; 167,971; 2,037,669 | apache-2.0; 2025-04-08; 167,971; 2,038,096 (13 listed) | PASS |
| 3 | florence-2 | license; lastModified; flagship dl; newest ckpt | MIT; 2025-08-04; 474,312; 2024-06-15 | mit; 2025-08-04; 474,312; 2024-06-15 | PASS |
| 4 | glm-v | weights / code license; push; flagship dl; newest | MIT / Apache-2.0; 2026-09-02; 3,606; 2025-12-07 | mit / apache-2.0; 2026-09-02; 3,606; 2025-12-07 | PASS |
| 5 | aria | license; push; archived; flagship dl | Apache-2.0; 2025-01-22; false; 45,905 | apache-2.0; 2025-01-22; false; 45,905 | PASS |
| 6 | eagle | weights label + gate; code; push; flagship / family dl | nsclv1, gated; Apache-2.0; 2026-06-24; 18,146 / 21,510 | other/nsclv1, gated=auto; apache-2.0; 2026-06-24; 18,146 / 21,510 (Eagle2/2.5 filtered) | PASS |
| 7 | step-vl | license; push; flagship dl; family | Apache-2.0; 2026-01-21; 28,318; 29,272 | apache-2.0; 2026-01-21; 28,318; 29,272 | PASS |
| 8 | lfm-vl | license; lastModified; flagship dl; family; newest | LFM Open License v1.0; 2026-03-30; 23,064; 307,035; 2026-09-18 | other/lfm1.0; 2026-03-30; 23,064; 307,035; 2026-09-18 | PASS |
| 9 | fastvlm | weights / code license; canonical repo; push; flagship dl | Apple ML Research; other; apple-aiml-research/ml-fastvlm; 2026-09-11; 1,364 | apple-amlr; other; apple-aiml-research/ml-fastvlm; 2026-09-11; 1,364 | PASS |
| 10 | perception-lm | license; gate; lastModified; flagship / family dl | fair-noncommercial-research, gated; 2025-07-14; 173 / 1,621 | other/fair-noncommercial-research, gated=manual; 2025-07-14; 173 / 1,621 | PASS |
| 11 | internvideo | license; push; flagship dl | Apache-2.0; 2026-07-02; 4,051 | apache-2.0; 2026-07-02; 4,051 | PASS |
| 12 | ui-venus | weights license; repo license; push; flagship dl | pending, HF empty; "repo sidebar Apache-2.0"; 2026-09-17; 8,276 | HF license null; **ecosyste.ms license null** (Apache appears only as a README badge; LICENSE 404); 2026-09-17; 8,276 | PARTIAL: the repo-license description is wrong (issue 6) |
| 13 | qwen-omni | card license; code; push; flagship / family dl | other + apache-2.0; Apache-2.0; 2026-04-23; 612,375 / 1,548,543 | other + apache-2.0; apache-2.0; 2026-04-23; 612,375 / 1,548,543 | PASS |
| 14 | ming-omni | license; code; push; flagship dl | MIT; MIT; 2026-07-27; 4,833 | mit; mit; 2026-07-27; 4,833 | PASS |
| 15 | janus | weights / code license; push; flagship dl; stars | DeepSeek License / MIT; 2025-02-01; 10,483; 17,765 | card `license: mit` + `license_name: deepseek`; mit; 2025-02-01; 10,483; 17,765 | PASS (the cell should mention that the card's `license` field says mit) |

Off-sample re-fetches, triggered by patterns in the sample:

| slug | claim | sweep value | live value | verdict |
|---|---|---|---|---|
| ovis | family adoption; newest checkpoint | 8,256 over 2 checkpoints; 2025-08-15 | ATH-MaaS Ovis1.x/2.x vendor checkpoints: **50,653 over 23**; newest **ATH-MaaS/Ovis2.6-80B-A3B 2026-05-11** (Ovis2.6-30B-A3B 2026-02-12) | **FAIL** (figure off by 6x; a missed release) |
| blip | newest checkpoint | 2025-11-04 | that date belongs to **Salesforce/BLIP3o-NEXT-*** (a generation line not in the member list). Newest BLIP/BLIP-2 checkpoint is 2023-08-23 | **FAIL** (activity) |
| vita | newest checkpoint | 2026-03-19 | that date belongs to **VITA-QinYu-4B/8B** (audio-to-audio, 12-13 downloads), not a listed member | FAIL (activity) |
| paligemma | family size / newest | 100 checkpoints; 2024-12-11 | 166 exist (`limit=100` cap); newest 2025-02-03 (jax mirrors); sum unchanged at 651,853 | minor |

## Issues

1. **Ovis adoption and release undercounted** (sweep.md line 480; `.evidence.json` ovis; section 2
   has no effect on the total). The adoption cell sums only F0059 (`search=Ovis2.5`, global), while the
   member list claims Ovis1.5/1.6/2/2.5. The ATH-MaaS listing holds 23 Ovis1.x/2.x checkpoints at
   50,653 downloads per 30 days, and a newer line, Ovis2.6 (30B-A3B 2026-02-12, 80B-A3B 2026-05-11). The flagship
   should probably be Ovis2.6. *Fix:* rfetch `https://huggingface.co/api/models?author=ATH-MaaS&search=Ovis&limit=200`.
   Exclude Ovis-U1 (unified), OvisOCR2 (parked) and the -Embedding / -Clip entries. Re-sum, set newest to
   2026-05-11, and reconsider the flagship.
2. **blip counted active on a non-member checkpoint** (line 484; section 2 active = 34). The
   "newest checkpoint 2025-11-04 (F0039)" is BLIP3o-NEXT, and the LAVIS repo is archived, so its
   `pushed_at` of 2026-09-18 is not activity. *Fix:* use 2023-08-23 as newest. Mark blip dormant. Either list BLIP3o
   as a member or exclude it from the 24-checkpoint sum. Add InstructBLIP (4 checkpoints, about 65k per 30 days,
   not in F0039) or drop it from "member checkpoints".
3. **vita counted active on a non-member checkpoint** (line 505). The 2026-03-19 date is VITA-QinYu
   (audio-to-audio), while the row's own note says "Dormant: last news 2025-01-17". *Fix:* either add
   VITA-QinYu and VITA-E to the member list and justify it, or set newest to the latest true member
   (VITA-Audio-Plus 2025-05-15) and mark vita dormant.
4. **The activity rule is applied inconsistently** (lines 49-53). Section 2 says the rule is "newest
   checkpoint, repo push or HF lastModified", and it presents Pixtral as the only row that is active
   on lastModified alone. Three problems:
   (a) aya-vision is also active only on lastModified (2026-01-09, F0169), while its 6b note says "Dormant: 2025-03-02".
   (b) kimi-vl's lastModified is 2026-01-30 in the sweep's own F0089, yet it is counted dormant. lastModified was
   only consulted for rows with no repo.
   *Fix:* pick one rule. The recommended rule is newest vendor member checkpoint or non-archived repo push,
   with no lastModified. Under that rule, pixtral, aya-vision and blip (plus vita if issue 3 goes that way)
   become dormant, and the active count falls from 34 to 30 or 31. Restate the count and the dormant list.
5. **Raw-signal count does not follow the rule the sweep states** (section 8, lines 795-808;
   `.evidence.json` `sig`). The definition counts "one Hub listing (F0001-F0005, the family listings)".
   Yet 42 of 47 accepted rows omit their own family listing from `sig` (for example qwen-vl lacks F0006),
   while 5 include it (mimo-vl F0048, perception-lm F0053, longcat-omni F0054, nemotron-vl F0028, ovis F0059).
   The flagships of qwen-vl, smolvlm, moondream, florence-2, blip and ui-tars also appear in F0002 without it
   being counted. *Fix:* either count family listings for every row, or redefine raw signals as
   "discovery sources only (brief, W ids, F0001-F0005, OpenVLM)" and drop the five family-listing
   entries. Then recompute 223 and 108. The equations will still close.
6. **ui-venus repo license misdescribed** (line 497). The cell says "repo sidebar Apache-2.0 (W0023)", but
   the sweep's own F0120 (ecosyste.ms) has `license: null`, and live the Apache mark is only a README
   badge (README line 10) with no LICENSE file. *Fix:* "no LICENSE file; GitHub license detection null
   (F0120); README carries an Apache-2.0 badge but says 'for research and educational purposes only'
   (W0023)".
7. **Quoted excerpts not present in the cited W log row** (the W log is the only evidence for a
   WebSearch):
   - line 467 smolvlm: 'checkpoints, VLM datasets, training recipes and tools released under the Apache 2.0 license' is not in W0016. The text is true live (huggingface.co/blog/smolvlm), and it backs the `open` status.
   - line 466 molmo: 'Open Weights and Data' is not in W0011. The text is true live (arXiv 2601.10611 title), and it backs the `open` status.
   - line 128: '256K-token native context ... hours-long videos' is not in W0019. "hours-long video" is true live in the QwenLM/Qwen3-VL README.
   - line 134: Qwen3-Omni 'understanding text, audio, images, and video, as well as generating speech in real time' is not in W0017, and not found verbatim in the Qwen3-Omni README or card.
   - lines 131-132: GLM-4.6V "native tool calling" is not in W0014. The zai-org/GLM-V README says "native Function Calling".

   *Fix:* rfetch the primary pages (the SmolVLM blog, the arXiv abs, the Qwen3-VL and GLM-V READMEs, the
   Qwen3-Omni card) and cite F ids. Replace the Qwen3-Omni quote with the card's wording ("real-time
   streaming responses in both text and natural speech").
8. **Quotes pinned to the wrong F id** (lines 478, 502, 488). 'Models are commercially usable' is
   cited as "F0164, text F0188", and 'Works are commercially usable' as "F0165, text F0189". F0164 and F0165 are
   400-600-byte HF API JSONs without these strings, and the quotes are in F0188 and F0189. 'for the sole purpose of
   scientific research' is placed beside F0137 (HF API, label `apple-amlr` only); that text
   is in F0183. *Fix:* move each quote next to the id that contains it.
9. **Header list of non-200 ids is inaccurate** (lines 6-8). It lists F0205-F0213 and F0231 as
   cited. F0208-F0210 (VITA license probes) are cited nowhere, and F0231 is cited only in the header itself.
   F0212 is covered only by a range. *Fix:* list exactly the non-200 ids cited in 6b/7 (F0177, F0182, F0191,
   F0193, F0194, F0205-F0207, F0211-F0213). Legitimacy is fine: each cited non-200 id is used only for
   gating or absence, never as the source of a license or number.
10. **Section 4 contradicts the sweep's own fetch on Nemotron Omni** (line 135). Rung 5 is "Audio and
    video in with streaming speech out", and it lists Nemotron Nano Omni. F0221 (its card) says
    "Output Type(s): Text", and W0002 says it "generate[s] text-based responses". *Fix:* move
    Nemotron Nano Omni to a rung for omni input with text output, or split rung 5 into "omni in" and
    "speech out".
11. **Section 5 misattribution** (line 145): "MiniCPM-V 4.5 on Qwen3-8B + SigLIP2, W0015". W0015's
    excerpt says this of **MiniCPM-o 4.5** (SigLip2, Whisper-medium, CosyVoice2, Qwen3-8B). *Fix:*
    change the text to MiniCPM-o 4.5, or fetch the MiniCPM-V 4.5 card.
12. **Uncited characterizations in prose that read as recall.** In section 4 (lines 123-129), the
    rung assignments of BLIP, PaliGemma, Florence-2, Idefics, SmolVLM, Moondream, Aya Vision, InternVL,
    MiniCPM-V, VideoLLaMA and MOSS-VL have no ids. In section 3 (line 103), "Florence-2 is a small seq2seq
    vision model" has none. In section 5 (line 144), "Most rows are a vision encoder grafted onto someone
    else's LLM" rests on 2 citations. *Fix:* cite a card or listing per example (pipeline tags in F0001-F0004
    would do for several), or label the rungs as illustrative, unsourced examples.
13. **"Discovered via search" is overstated for recall-seeded candidates** (line 491 perception-lm
    "Discovered via HF search"; section 8 line 810). perception-lm's only signal is F0053
    (`author=facebook&search=Perception`), a targeted query that presupposes the name. The model is in none of
    F0001-F0005. The same holds for mimo-vl (F0048), nemotron-vl (F0028) and longcat-omni (F0054, plus a
    W0017 query that names it). fastvlm, lfm-vl, bagel and emu were first hit by WebSearch queries that already
    named them (W0016, W0020). *Fix:* split the section-8 list into "surfaced by open discovery" and
    "named by the researcher, verified live" (see the breadth list below).
14. **OCR count mismatch** (line 99 "parks 20 OCR VLMs"; line 839 "20 parked"). Section 7's OCR rows name
    24 models (chandra, chandra-ocr-2, surya-ocr-2, Unlimited-OCR, Qianfan-OCR, HunyuanOCR, GOT-OCR2.0,
    Nanonets-OCR, OCR2, LightOnOCR-2, PaddleOCR-VL, granite-docling, SmolDocling, MinerU2.5, RolmOCR,
    OCRFlux, Dolphin, OvisOCR2, typhoon-ocr, jina-ocr, TeleOCR, dots.ocr, DeepSeek-OCR, olmOCR). *Fix:* state
    the number the sweep actually counted and which models it covers.
15. **Parked Qwen3.5-Omni source URL is the wrong paper** (line 743). arXiv 2609.25611 is "Qwen3.8-Omni"
    per W0017, and it was never fetched. The sweep also never checks whether Qwen3.8-Omni has weights (none
    under `author=Qwen&search=Omni` live), which matters for the governing-release question.
    *Fix:* cite W0017 without that URL, and add one line on Qwen3.8-Omni's status.
16. **Truncated family listings reported as exact counts** (lines 464, 483). InternVL's "100 vendor
    checkpoints" and PaliGemma's "100" are the `limit=100` cap (155 and 166 exist). The sums move less than
    0.2%, but PaliGemma's newest date is 2025-02-03, not 2024-12-11. *Fix:* re-fetch with `limit=1000` and
    restate the count and date. Both rows stay dormant or active as before.
17. **New org slugs not disclosed** (6a/rows.yaml). 13 org slugs have no file in `sources/organizations/`:
    ath-maas, bytedance-douyin, h-company, kuaishou, liquid-ai, m87-labs, meituan, nyu-visionx, openmoss,
    rhymes-ai, salesforce (registry-only, already used in `embeddings_retrieval`), sensetime and stepfun.
    Only sail-vl's org is flagged as "proposed" (line 492). *Fix:* list the new org slugs in section 9
    or next to 6a.
18. **VITA org attribution needs a note** (line 505, org `tencent`). The sweep's own F0215 lists VITA and
    VITA-1.5 under Org "NJU", and Long-VITA under "Tencent Youtu Lab & Nanjing University". Only the
    License.txt copyright (THL A29) points to Tencent. *Fix:* cite both and flag the org for the
    maintainer.
19. **Minor unsourced note cells** (6b notes). ming-omni's "Ming-omni-tts / Ming-UniAudio are speech SKUs"
    has no id (F0045 shows them as text-to-speech, so cite it). lfm-vl's "Liquid AI has no product on the map"
    has no id (cite corpus-index.tsv as a local check). qwen-vl's claim "no checkpoint newer than 2025-10-31" ignores
    Qwen3-VL-Embedding/Reranker (2026-01-07, F0006), which were excluded as embeddings; say so.
20. **W log timestamps are batch-assigned** (web-log.tsv). Nine calls share 20:00:59Z and four share
    20:01:22Z, so the times are not per call. This is not a freshness failure, since all are 2026-09-26, but
    log the real time of each call in future runs.

## Breadth (check 6): candidates not named in the brief

- **Surfaced by open discovery** (open WebSearch, HF top-N listings or the OpenVLM snapshot): north-vision
  (W0005), fara (F0002), step-vl (F0002), aya-vision (F0002), ui-tars (F0001/F0002), blip (F0001),
  keye-vl, videollama, internvideo, moss-vl and vita (F0004), sensenova-u and nemotron-omni (F0003,
  W0002), sail-vl (W0003), ovis (OpenVLM), ui-venus (W0018 result), holo (W0018/W0026, also in F0002).
- **Named by the researcher's own query, then verified live:** perception-lm (F0053), mimo-vl (F0048),
  nemotron-vl (F0028), longcat-omni (F0054/W0017), fastvlm and lfm-vl (W0016), bagel and emu (W0020).
- On the parked side, Muse Glimmer, Inkling, Isaac, Cosmos-Reason, MolmoAct, the OCR-VLM class and the
  9 identity-unclear listings are all present in the logged listings or searches.

## What checked out

- All F ids cited in 6b and 7 exist in fetch-log.tsv. 6c matches the logs exactly (timestamp, code, URL),
  and every id cited in 6b/7 appears in 6c.
- Raw bodies match their logged sha256. The 16 mismatches are the documented 300 KB truncation of bodies over
  1 MB. I re-fetched F0215 in full, and its sha256 matches the log. From it I confirmed the snapshot time
  (20250917), InternVL3-78B MMMU 72.2 as the top open entry, and a closed-model top of table.
- The spot-checked quotes from raw bodies are present: F0220, F0221, F0214 (both quotes and THL A29), F0195,
  F0185, F0186, F0190, F0218, F0219, F0216 (2026-02-12), F0179/F0180 (Attachment A) and F0065. The W0027
  Moondream quote was confirmed live.
- The family sum for qwen-vl (46,805,754 = 49,858,128 minus the 4 embedding/reranker checkpoints) and those
  for kimi-vl and eagle reproduce exactly.
- 6a is byte-identical to rows.yaml, and it validates against the schema.

## Re-check of fixed items (second auditor)

A second, fresh auditor re-checked only the 20 issues above on 2026-09-26, against the current
sweep.md, rows.yaml, .evidence.json, .families.json, the logs and raw bodies, and
tools/metrics.py / tools/parked.py / tools/families_fix.py. Family sums, counts and newest
dates were recomputed independently from the cited raw listing bodies. The OpenVLM JSON (F0215)
was re-fetched in full (sha256 a4cd57a2... matches the log) to check the VITA org text. The saved
raw body is the documented 300 KB truncation and does not contain that text. Two live checks were
made: the HF API for ATH-MaaS/Ovis2.6-30B-A3B and ecosyste.ms for ATH-MaaS/Ovis.

| # | issue | status | evidence |
|---|---|---|---|
| 1 | ovis adoption / release | PARTIAL | Newest checkpoint 2026-05-11 (F0234, Ovis2.6-80B-A3B) and flagship ATH-MaaS/Ovis2.6-30B-A3B are fixed. Live HF API: license apache-2.0, 1,012 dl, created 2026-02-12, matching F0245. The recomputed F0234 sum with the stated exclusions is 24 / 51,036, matching the cell. But one of those 24 is ATH-MaaS/Ovis-Image-7B (pipeline `text-to-image`, diffusers, 383 dl), which is not in the member list or the exclusion regex. The correct figure is 23 / 50,653 (new problem N1; 0.8%). |
| 2 | blip non-member checkpoint | FIXED | Cell: "newest checkpoint 2023-08-23 (F0039, F0235)", "[archived: not counted as activity]", "BLIP3o / BLIP3o-NEXT ... excluded from the sum". Recomputed from F0039+F0235 minus BLIP3o: 22 checkpoints, 3,734,419, newest 2023-08-23, no duplicate ids. Dormant. InstructBLIP (4) is now in the member list and sum (F0235). Note: the 2023-08-23 date is blip2-itm-vit-g (zero-shot-image-classification). Excluding the ITM checkpoints moves newest to 2023-06-03, and it stays dormant either way. |
| 3 | vita non-member checkpoint | FIXED | Members now say "(VITA-QinYu audio models and VITA-E excluded, F0050)". Recomputed: 19 / 443, newest 2025-05-15 (VITA-Audio-Plus-Boost). Dormant. Freeze-Omni and LUCY-Audio-Encoder (0 dl) remain in the 19 without being named; negligible. |
| 4 | activity rule inconsistent | FIXED | Section 2: "The rule is one test: the newest vendor member checkpoint, or a push to a non-archived repo ... HF lastModified is not counted". Recomputed from 6b dates (archived repo pushes dropped): 30 active. The 17 dormant slugs match section 2 exactly and match `.evidence.json` (`newest`, `repo_push`) and tools/metrics.py output. Understanding-only scope: 22 of 37. |
| 5 | raw-signal rule | PARTIAL | Every row's `sig` now contains its adoption-cell family listing ids (0 missing across 47), and the arithmetic reproduces: accepted sig 159 + parked 113 = 272; 272 - 116 = 156; 116 = 47 + 69 (len(P) = 69). But the second half of the issue is not fixed. The declared flagships of qwen-vl, smolvlm, moondream, florence-2, blip and ui-tars are in F0002 and F0002 is still absent from their `sig`. Under the stated definition, raw is at least 278 (dup 162), and higher if any member checkpoint appearing in F0001-F0005 counts (about 13 row/listing pairs, e.g. internvl F0004, molmo F0004, llava F0002, paligemma F0002, holo F0002). |
| 6 | ui-venus repo license | PARTIAL | 6b is fixed: "GitHub license detection null (F0120); README carries an Apache-2.0 badge but says 'This project is for research and educational purposes only' (W0023)". The quote is in the W0023 excerpt. But section 5 (line 184) still says "the repo is Apache in the sidebar" (new problem N4). |
| 7 | W quotes not in cited row | FIXED | Each quote is re-cited to a fetched body, and each string was found there: F0238 "All model checkpoints, VLM datasets, training recipes and tools are released under the Apache 2."; F0239 "Open Weights and Data for Vision-Language Models with Video Understanding and Grounding"; F0240 "Native 256K context, expandable to 1M; handles books and hours-long video"; F0241 "we integrate native Function Calling capabilities"; F0242 "real-time streaming responses in both text and natural speech". All 10 remaining quote-to-W pairs in sweep.md were matched against their web-log excerpts. |
| 8 | quotes on wrong F id | FIXED | "label F0164; text F0188: 'Models are commercially usable'" (string in F0188, not F0164). "label F0165; text F0189: 'Works are commercially usable'" (in F0189). "label `apple-amlr` F0137; text F0183: 'for the sole purpose of scientific research'" (in F0183 across a line break; also in F0184). |
| 9 | header non-200 list | FIXED | The header lists "F0177, F0182, F0191, F0193, F0194, F0205-F0207, F0211-F0213". The recomputed non-200 set cited in 6b/7 (ranges expanded) is exactly this. F0208-F0210 and F0231 are cited nowhere. Minor: F0206 and F0212 appear in 6b only through a range and have no 6c row (N5). |
| 10 | Nemotron Omni rung | FIXED | Rung 5 is now "Omni in ... with text out (Nemotron Nano Omni, whose card gives output type Text, F0221)". F0221 has "Output Type(s):** Text". Speech out moved to rung 6 (Qwen-Omni F0242, MiniCPM-o W0015). |
| 11 | MiniCPM-V/-o misattribution | FIXED | Section 5 now reads "MiniCPM-o 4.5 built on SigLip2, Whisper-medium, CosyVoice2 and Qwen3-8B, W0015", which matches the W0015 excerpt. |
| 12 | uncited characterizations | FIXED | The rungs say "Examples without a fetch id are illustrative placements". Cited examples check out: BLIP image-to-text / visual-question-answering tags (F0039), VideoLLaMA and MOSS-VL video-text-to-text (F0004), LongCat any-to-any (F0054), Ming any-to-any (F0003). Florence-2 is now the F0243 quote, whose strings are present. "Most rows ... grafted" is replaced by "Several rows ... How many do is not measured here" (W0026, W0015, F0204, all verified). |
| 13 | "discovered via search" | FIXED | perception-lm note: "Named in the researcher's own targeted HF query (F0053), not found by open discovery". Section 8 is split into "Surfaced by open discovery" and "Named in the researcher's own queries, then verified live". No "Discovered via" text remains. |
| 14 | OCR count | PARTIAL | Now "12 section-7 rows, 24 names, 3 of them already mapped" and "21 unmapped". 12 rows and 24 names are confirmed. But PaddleOCR-VL and MinerU2.5 are SKUs of the mapped `paddleocr` and `mineru` (corpus-index.tsv; section 7 says so), so the unmapped count is 19, not 21 (N3; section 3 line 101 and section 9 Q6). |
| 15 | Qwen3.5-Omni wrong paper | FIXED | The parked row now cites W0004, W0017 and F0244 with a marktechpost URL, with no arXiv 2609.25611. It says there are "no Qwen3.5- or Qwen3.8-Omni weights under author=Qwen (F0244, only Qwen2.5-/Qwen3-Omni)". F0244 holds 7 ids, all Qwen2.5-Omni or Qwen3-Omni. |
| 16 | truncated family listings | PARTIAL | internvl: F0236 (limit=1000) recomputes to 155 / 2,923,773 / newest 2025-09-28, matching the cell. paligemma: F0237 recomputes to 166 / 651,853 / newest 2025-02-03, matching the cell. But the paligemma notes cell still says "Dormant: newest 2024-12-11 (F0036)" (N2). |
| 17 | new org slugs | FIXED | The 6a preface and section 9 Q12 list 13 new slugs. Recomputed from rows.yaml against `sources/organizations/`, the same 13 lack a record. |
| 18 | VITA org | FIXED | The 6b note and Q13 cite both F0214 (THL A29) and F0215. A live full OpenVLM re-fetch (sha matches the F0215 log row) gives VITA / VITA-1.5 Org "NJU" and Long-VITA-16K "Tencent Youtu Lab & Nanjing University". Flagged for the maintainer. |
| 19 | minor unsourced notes | FIXED | ming-omni: "Ming-omni-tts (pipeline text-to-speech, F0045)"; F0045 also lists Ming-UniAudio. lfm-vl: "Liquid AI has no product in corpus-index.tsv (local check)". qwen-vl: "the 2026-01-07 Qwen3-VL-Embedding/Reranker checkpoints are excluded as embeddings_retrieval models". |
| 20 | batch W timestamps | FIXED (disclosed) | Header: "Web-log timestamps were stamped when each batch of calls was logged, not per call". Per-call times cannot be recovered after the fact. All are 2026-09-26. |

**Other re-verified items.** rows.yaml validates against `docs/schemas/registry.schema.json`
(0 errors) and is identical to the 6a block. Its ovis row is `ATH-MaaS/Ovis` + `ATH-MaaS/Ovis2.6-30B-A3B`,
and ecosyste.ms live shows ATH-MaaS/Ovis archived=false, fork=false, pushed 2026-07-15,
license apache-2.0, matching F0233. No slug, alias or github/HF artifact collides with
corpus-index.tsv, `sources/products/*.yaml` or `sources/registry/*.yaml`. The new fetches
F0233-F0245 are all HTTP 200 and dated 2026-09-26 20:10:29Z-20:28:52Z. `.families.json`
and `.evidence.json` agree (sum, newest) for ovis, blip, vita, internvl and paligemma.

**New problems introduced or left by the fixes (all minor):**
- N1. The ovis sum includes ATH-MaaS/Ovis-Image-7B (text-to-image). The fix is to add `Image` to the families_fix.py exclusion, which gives 23 / 50,653.
- N2. The paligemma notes cell has a stale "Dormant: newest 2024-12-11 (F0036)". It should read 2025-02-03 (F0237).
- N3. The OCR count reads "21 unmapped" but is 19 (PaddleOCR-VL and MinerU2.5 are SKUs of mapped products).
- N4. Section 5 still reads "the repo is Apache in the sidebar" for ui-venus. It should match the corrected 6b cell.
- N5. 6c has no rows for F0206 and F0212 (cited in 6b via ranges). The new prose citations F0216, F0240, F0242, F0243, W0005 and W0016 (sections 2-5 and 8) are also not in 6c. That second part is within 6c's stated scope, but it is worth adding.

### Verdicts for the previously failing checks

| check | verdict | reason |
|---|---|---|
| 1 Re-fetch claims | **PASS** | ovis is now within 1% of the correct figure, with the right newest date and flagship (live-verified). blip and vita no longer rest on non-member checkpoints. The ui-venus 6b cell is correct. N1 and N4 are cosmetic. |
| 2 Unsourced facts / log integrity | **PASS** | Every quote was verified in its cited body or excerpt. All cited ids exist. Non-200 ids are used only for gating or absence, and the header list is exact. N5 is a completeness gap in 6c, not an unsourced fact. |
| 5 Counts / section-2 metrics | **FAIL** | Both equations and all section-2 metrics (47, 35 orgs, 8.5%, 30 active, 17 dormant) reproduce. But the raw-signal count still does not follow its own definition: F0002 is missing from `sig` for 6 rows whose declared flagship is in F0002 (raw at least 278, dup 162). Fix: add those listing ids to `sig` (or narrow the definition), then recompute 272/156. |
| 6 Recency and breadth | **PASS** | All new fetches are from this run. The breadth list is split correctly. The recall items (issues 10-15) are fixed. N2 and N3 are small stale-prose items. |

Overall: **not yet clean**. Check 5 fails on the signal count alone. Fix it together with N1-N5,
then re-check.

## Final re-check (third auditor)

A third auditor re-checked only check 5 and N1-N5 on 2026-09-26, against the current sweep.md,
rows.yaml, .evidence.json, .families.json, tools/parked.py, tools/build.py and the raw bodies.
Nothing was re-fetched. Every figure below was recomputed from those files, not read off the prose.

| item | status | evidence |
|---|---|---|
| Check 5, raw-signal rule | FIXED | Section 8 now states the rule: each row's `sig` holds its 6b family listing ids plus each top listing (F0001-F0005) that contains the declared flagship or one of the family's six most-downloaded member checkpoints (build.py `disc`). Independent recompute: accepted `sig` 167 + parked 113 (tools/parked.py, 5th field) = 280 raw; unique 47 + 69 = 116; duplicates 280 - 116 = 164. Both equations (280 = 164 + 116, 116 = 47 + 69) hold, and the figures match section 8. Uniformity: for all 47 rows, the F0001-F0005 subset of `sig` equals exactly the set the rule predicts from the raw F0001-F0005 bodies (0 missing, 0 extra), so no hand-entered top listing survives unless the rule justifies it. Each `.families.json` `top` list is present in its family listing and sorted by downloads. Where higher-download ids are left out, they are non-members the row excludes, e.g. MiniCPM5 and MiniCPM-V under minicpm-o, and MolmoAct2 under molmo. Spot-checks against the raw bodies: qwen-vl flagship Qwen3-VL-8B-Instruct is in F0001/F0002/F0005, `sig` has all three. smolvlm flagship SmolVLM2-2.2B is in F0002, and SmolVLM2-500M-Video is in F0001, `sig` has F0001+F0002. moondream's vikhyatk/moondream2 is in F0001/F0002, `sig` has both. florence-2 Florence-2-large is in F0001/F0002, `sig` has both. blip blip2-opt-2.7b is in F0001/F0002, `sig` has both. ui-tars UI-TARS-1.5-7B is in F0001/F0002, `sig` has both. The F0002 gap the second auditor found is closed. The rule is narrower than "any member checkpoint", so internvl F0004 and holo F0002 are correctly not counted, and section 8 says so. |
| N1 ovis sum | FIXED | families_fix.py now excludes `Ovis-Image`. Recomputed from raw/F0234.body (33 ids; exclusions Ovis-U, Ovis-Image, OCR, Embed, Clip): 23 checkpoints, 50,653 downloads, newest 2026-05-11. This matches `.families.json`, `.evidence.json` and the 6b cell, which also names Ovis-Image-7B as excluded. |
| N2 paligemma date | FIXED | The 6b notes cell reads "Dormant: newest member checkpoint 2025-02-03 (F0237)", which matches the last-release cell and `.families.json`. |
| N3 OCR count | FIXED | Section 3 (line 101) and section 9 Q6 both say 19 unmapped of 24 names in 12 rows. Recount from tools/parked.py: 24 names; 3 mapped (dots.ocr, DeepSeek-OCR, olmOCR); 2 SKUs of mapped products (PaddleOCR-VL, MinerU2.5); 19 unmapped. |
| N4 ui-venus sentence | FIXED | Section 5 now reads "the repo has no LICENSE file and GitHub detects no license (F0120), and its README shows an Apache-2.0 badge but says 'research and educational purposes only' (W0023)". The "sidebar" wording is gone. The LICENSE claim is backed by the 404s F0194 and F0211-F0213. |
| N5 6c ids | FIXED | F0206, F0212, F0216, F0240, F0242, F0243, W0005 and W0016 all have 6c rows. A full scan found no id cited anywhere outside 6c (ranges expanded) that is missing from 6c's 254 rows. |

**Schema.** `rows.yaml` validates against `docs/schemas/registry.schema.json` (`ok`).

**One remaining minor point (N6, wording only).** Section 8 says the parked source lists are "in
section 7's evidence column". The 113 parked signals are actually counted from the fifth
(`signals`) field of tools/parked.py, which is not published in sweep.md. For 18 of the 69 rows
that field differs from the evidence column: summed, the evidence column gives 98 and the
`signals` field gives 113. For example, Qwen3.5/3.6/3.8 has evidence "W0010, F0226, F0001" and
signals W0004, W0010, F0001, F0005. The arithmetic is right. Only the pointer is wrong. Fix it by
pointing section 8 at tools/parked.py, or by publishing the signals column in section 7.

### Verdict for check 5

**PASS.** The rule is stated explicitly. It is applied mechanically and uniformly to all 47
accepted rows, which was verified against the raw F0001-F0005 bodies. Both equations reproduce
from `.evidence.json` and tools/parked.py (280 = 164 + 116; 116 = 47 + 69). N6 is a documentation
pointer and does not affect any count.

Overall: **clean**. N1-N5 are all fixed. N6 is an optional one-line wording fix.

## Researcher note on N6

Fixed: section 8 now points the parked signal lists at the `signals` field of `tools/parked.py`. The wording changed; the numbers did not.
