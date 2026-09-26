# Audit: speech_audio sweep (2026-09-26)

Independent auditor pass over `sweep.md`, `rows.yaml`, `fetch-log.tsv`, `raw/`, `web-log.tsv`.
Audit fetches are logged in `fetch-log.tsv` as F0274–F0296 (labels start with `audit:`). The
artifact-resolution sweep for check 3 used plain curl; its results are recorded below.

## Verdicts

| # | check | verdict |
|---|---|---|
| 1 | Re-fetch 15+ claims live | **PASS**: 19 claims re-fetched; none out of tolerance. One stale-source discrepancy (issue 5) does not reach the failure bar. |
| 2 | Unsourced facts | **PASS with notes**: all 187 ids cited in §6b exist in the logs. The non-200 citations are used honestly. Two W excerpts do not contain the fact they are cited for (issues 3 and 4). |
| 3 | Every artifact resolves live | **PASS**: 81/81 artifacts resolve (32 github, 27 HF, 18 PyPI, 4 homepages). None archived. `idiap/coqui-ai-TTS` is a fork, and the sweep says so. |
| 4 | Schema and dedup | **PASS**: `jsonschema.validate` prints `ok`. No slug, alias, github, HF id or PyPI name collides with `corpus-index.tsv`. |
| 5 | Counts reconcile, §2 computable | **PASS**: 82 = 10 + 72 and 72 = 42 + 30 both hold, and every §2 metric recounts exactly from §6 (with one definitional note, issue 6). |
| 6 | Recency, breadth, recall | **FAIL**: timestamps and breadth are fine, but three statements are unsupported by, or contradict, their cited evidence (issues 1, 2 and 3). |

## Issues

1. **§9 Q5, recommendation sentence: "Cohere Transcribe and Breeze TTS 2 top their respective leaderboards per search (W0002, W0007)."** For Cohere this is contradicted by its own source. W0002 says Cohere *took* the top in March 2026 at 5.42%, that "five weeks later IBM shipped Granite Speech 4.1 2B at 5.33%", and that ARK-ASR-3B and MOSS-Transcribe posted lower numbers still. My WebSearch today agrees: Granite 4.1 2B leads the public-only board at 5.33. The Breeze TTS 2 half is supported (W0007, re-confirmed). Fix: say Cohere briefly topped the board, or drop the claim.
2. **§9 Q5, option (b): "add only Cohere Transcribe and OmniVoice (the two with >150K HF downloads and a permissive code license)."** This is wrong on the sweep's own data. MOSS-Transcribe-Diarize has 163,483 HF downloads over 30 days, and both its weights and its code are Apache-2.0 (F0193, F0235; re-read in audit). So three candidates meet that test, not two. Fix: add MOSS-Transcribe-Diarize to (b) or change the criterion.
3. **§3 contested table (Qwen2.5-Omni row) and §7 (Qwen2.5-Omni row): cited to W0009.** The W0009 excerpt covers Hertz-dev and Human-1 only. Nothing in `web-log.tsv` or `fetch-log.tsv` mentions Qwen2.5-Omni, so the row rests on recall. It is only a boundary exclusion, but it is counted as a unique candidate in §8 and listed under breadth. Fix: fetch its HF card or a search excerpt and cite that, or drop it from the counts.
4. **Excerpts that don't carry the cited fact (W0005).** §6b `elevenlabs-tts` "last release" cell says "Eleven v3 dated Feb 2026 (W0005)". §7 Cartesia Sonic and §9 Q7 say "Sonic-3.6 at #1 Provider Voice Elo (W0005)". The W0005 excerpt in `web-log.tsv` quotes neither fact. I re-fetched the page live, and both are on it: "generally available since February 2026" for Eleven v3, and Cartesia Sonic-3.6 first on Provider Voice at about 1,283 Elo. So the facts are true, but the log excerpt should be extended so they are traceable.
5. **§6b `silero-vad`, last release cell: "v6.2.1, 2026-02-24 (F0269)".** That is the latest *GitHub release* per ecosyste.ms. PyPI shows 6.2.2 (2026-09-17) and 6.2.3 (2026-09-23) (audit F0293), and `packages.ecosyste.ms` also still reports 6.2.1 (F0290), so the source is stale. Activity status is unaffected, because the push is dated 2026-09-23. Fix: record PyPI 6.2.3, 2026-09-23, next to the GitHub release.
6. **§2 "active in the last 12 months" definition vs `mms` / `wav2vec`.** The stated rule counts "any repo push … on/after 2025-09-26". The code repo the sweep attributes to both rows, `facebookresearch/fairseq`, was last pushed 2025-09-30 (F0009; re-confirmed F0295), which is inside the window, and it is archived. The sweep counts both as inactive. That is a defensible reading, since the push is the archive event and neither row declares fairseq, but it contradicts the rule as written. Fix: add "excluding archived repos" or "declared artifacts only" to the definition. The count (37) stays the same either way.
7. **Weak evidence for renames (§6b `moonshine`, `cosyvoice` notes).** These cite ecosyste.ms 404s (F0004, F0013) as proof that the old names are gone. An ecosyste.ms 404 means "not indexed", not "moved". The conclusions are correct: F0052 shows `FunAudioLLM/CosyVoice` → `QwenAudio/CosyVoice`, and audit F0296 shows `usefulsensors/moonshine` → `moonshine-ai/moonshine` via ungh. Fix: cite the redirect evidence (F0052, F0296) rather than the 404s.
8. **§6a / rows.yaml `vibevoice.huggingface_model: microsoft/VibeVoice-1.5B`.** This is the TTS checkpoint that the repo README now marks "Disabled", with its code removed (F0226, re-read). It still resolves on HF (lastModified 2026-01-22). The most-downloaded member is VibeVoice-ASR (740,302/30d, re-confirmed F0285). This is not an error, but the canonical-artifact choice should be settled together with §9 Q3. Consider declaring `microsoft/VibeVoice-ASR`.
9. **§7 Kaldi and icefall are counted as the ruled list's "2 legacy names" (§8), with "legacy (issue said so)".** The brief in `RUNBOOK.md` (Brief 0) doesn't name Kaldi or icefall, and issue #602 isn't in the repo, so this attribution can't be verified from here. The counts still balance if they are reclassified as discovered names (then 22 discovered, 0 legacy). Fix: cite the issue comment, or reclassify them.
10. Minor, §4 rung 4: "Granite Speech 4.1 at 5.33% WER … top of a public leaderboard (W0002)". W0002 itself says ARK-ASR-3B and MOSS-Transcribe "posted lower numbers still". My live search found that Granite 4.1 leads the *public-only* board, so the claim holds if it is qualified that way.

## Check 1: re-fetched claims (spread across §6b rows 1, 4, 7, 10, 13, 16, 19, 22, 23, 25, 28, 30, 31, 34, 37, 38)

| # | slug | claim | sweep value | live value | fetch id | verdict |
|---|---|---|---|---|---|---|
| 1 | whisper | code license, archived, last push | MIT; no/no; 2026-08-31 | mit; archived=false, fork=false; 2026-08-31 | F0274 | match |
| 2 | whisper | HF large-v3-turbo 30d downloads, license | 6,477,272; MIT | 6,477,272; mit | F0275 | match |
| 3 | moonshine | canonical identity, last push | moonshine-ai/moonshine; 2026-08-31 | moonshine-ai/moonshine (old name redirects, F0296); 2026-08-31; license label "other", LICENSE text MIT + community (F0202) | F0276 | match |
| 4 | wav2vec | HF wav2vec2-base-960h downloads, license | 1,438,759; Apache-2.0 | 1,438,759; apache-2.0 | F0277 | match |
| 5 | granite-speech | last push, GitHub license field | 2026-09-16; null (README Apache) | 2026-09-16; null | F0278 | match |
| 6 | granite-speech | HF 4.1-2b downloads, license | 165,481; Apache-2.0 | 165,481; apache-2.0 | F0279 | match |
| 7 | xtts | license, downloads, lastModified | CPML 1.0.0; 6,815,205; 2023-12-11 | coqui-public-model-license; 6,815,205; 2023-12-11 | F0280 | match |
| 8 | fish-speech | code license | Fish Audio Research License, updated 2026-03-07 | LICENSE: "FISH AUDIO RESEARCH LICENSE AGREEMENT … Last Updated: March 7, 2026", commercial use needs separate license | F0281 | match |
| 9 | fish-speech | last push, archived | 2026-09-16; no/no | 2026-09-16; false/false | F0282 | match |
| 10 | orpheus-tts | HF downloads, card license | 70,180; Apache-2.0 | 70,180; apache-2.0 | F0283 | match |
| 11 | zonos | last push, license | 2025-03-05; Apache-2.0 | 2025-03-05; apache-2.0 | F0284 | match |
| 12 | higgs-audio | v3 TTS license, downloads | Boson Higgs TTS 3 Research and Non-Commercial; 99,684 | boson-higgs-tts-3-research-and-non-commercial-license; 99,684 | F0291 | match |
| 13 | vibevoice | HF VibeVoice-ASR downloads, license | 740,302; MIT | 740,302; mit | F0285 | match |
| 14 | faster-whisper | PyPI monthly downloads, license, last release | 8,271,086/mo; MIT; v1.2.1 2025-10-31 | 8,271,086 (last-month); MIT; 1.2.1 2025-10-31 | F0286 | match |
| 15 | whisper-cpp | canonical owner, stars, last push; HF downloads | ggml-org/whisper.cpp; 53,918; 2026-09-24; HF 0 | ggml-org/whisper.cpp; 53,918; 2026-09-24; HF ggerganov/whisper.cpp downloads 0 | F0292, F0294 | match |
| 16 | espnet | PyPI latest release | 202610.post2, 2026-09-24 | 202610.post2 uploaded 2026-09-24T03:02; Apache | F0287 | match |
| 17 | piper | canonical repo, license, last push | OHF-Voice/piper1-gpl; GPL-3.0; 2026-09-17 | OHF-Voice/piper1-gpl; gpl-3.0; 2026-09-17 | F0288 | match |
| 18 | pyannote-audio | PyPI monthly downloads, latest release | 2,173,253/mo; 4.0.7 2026-06-30 | 2,173,253; 4.0.7 2026-06-30; mit | F0289 | match |
| 19 | silero-vad | PyPI monthly downloads; last release | 1,683,558/mo; v6.2.1 2026-02-24 | 1,683,558; PyPI JSON shows 6.2.3 on 2026-09-23 | F0290, F0293 | downloads match; release stale (issue 5, not a failure class) |

W claims spot-checked with WebFetch/WebSearch (live, 2026-09-26):

| W id | claim | live result | verdict |
|---|---|---|---|
| W0019 | Universal-3 Pro release date 2026-02-03 | page byline "February 3, 2026" | match |
| W0010 | Nova-3 "our most advanced speech-to-text model to date" | same sentence on page | match |
| W0007 | AA open-weights TTS top 5: Breeze TTS 2, Fish S2 Pro, Step Audio EditX, Voxtral TTS, Kokoro | same order and Elo values | match |
| W0002 | Cohere 5.42% then Granite 4.1 2B 5.33% | same; Granite leads public-only board | match (but see issue 1 on how §9 uses it) |
| W0005 | Eleven v3 Feb 2026; Cartesia Sonic-3.6 #1 Provider Voice | both present on the page | match (excerpt gap, issue 4) |

## Check 2: sourcing detail

- 187 distinct ids cited in §6b; every one exists (F in `fetch-log.tsv`, W in `web-log.tsv`). Every other id cited elsewhere in the doc also exists.
- Non-200 citations: 16 `ungh …/releases/latest` 404s back "no published GitHub release". Each body is a GitHub API 404, and I re-queried `ungh …/releases` for all 13 affected repos, which returned `{"releases":[]}` every time. **Honest.** F0219 (401, gated Orpheus card) is cited as "can't be read". **Honest.** F0004 and F0013 (ecosyste.ms 404) are weak evidence for renames, though the conclusions are correct (issue 7).
- W0004 (failed WebFetch) is logged as not cited, and it is not cited anywhere in `sweep.md`.

## Check 3: artifact resolution (plain curl, 2026-09-26)

All 81 declared artifacts returned HTTP 200:

- **GitHub (32):** checked via ecosyste.ms. `full_name` equals the declared value for every row. `archived=false` everywhere. `fork=true` only for `idiap/coqui-ai-TTS`, and the sweep says so.
- **HF models (27):** checked via `/api/models/<id>`, and every `id` echoes the declared value.
- **PyPI (18):** checked via `pypi.org/pypi/<name>/json`. Every latest version matches §6b except silero-vad (issue 5). Declared source URLs point at the declared repo, with two exceptions: `moshi` and `pyannote.audio` expose no source URL in `info`, and the sweep backs both with README install lines (F0255, F0265).
- **Homepages (4, closed rows):** all return 200.

## Check 4: schema and dedup

- `uv run python -c "…jsonschema.validate(…)"` prints `ok`.
- The rows.yaml product list is identical to the §6a YAML block. The only difference is a leading comment line.
- No collision on slug, retired alias, github, HF id or normalized PyPI name. `nemo` (tail, `finetuning_code`) is correctly kept out of rows.yaml and handled as a move. Every org slug already on the map is reused (`nvidia`, `meta`, `openai`, `alibaba-cloud`, `ibm`, `mistral-ai`, `microsoft`, `ggml-org-georgi-gerganov`, …). The 26 new org slugs have no near-duplicate in the index.

## Check 5: counts

- **§6b recount:** open 11, open-weights 21, source-available 6, closed 4 = 42. There are 31 model rows and 11 software rows.
- **Orgs:** 34 distinct. The largest share is 3/42 = 7.1%, a tie among nvidia, meta and alibaba-cloud.
- **Active:** 37, with the 5 inactive rows as listed. Recomputed from §6b and re-checked HF lastModified live for kokoro, melotts and coqui. See issue 6 for the definitional note on mms/wav2vec.
- **Usage instrument:** 42 − 4 closed − whisper-cpp = 37.
- **§7 has 30 parked rows.** Both §8 equations balance: 82 = 10 + 72 and 72 = 42 + 30. The 72 break down as 43 + 7 + 2 + 20, and each group reconciles against the §7 rows, the RUNBOOK list (43 named, 7 reserve, 2 folds) and the 10 listed duplicates. The source of the 2 legacy names is unverifiable (issue 9).

## Check 6: recency and breadth

- **Timestamps:** all 273 sweep fetch rows are dated 2026-09-26, running 19:59–20:04Z, and all W rows run 20:00–20:03Z. They are from this run.
- **Candidates surfaced beyond the brief (RUNBOOK Brief 0):** Cohere Transcribe, MOSS-Transcribe-Diarize, MOSS-TTSD, ARK-ASR, Breeze TTS 2, Step-Audio-EditX, Kyutai Pocket TTS, Speaches, Kokoro-FastAPI, DiariZen, TEN VAD, Hertz-dev, Human-1, Fun-ASR-Nano, Cartesia Sonic, Microsoft MAI-Transcribe/MAI-Voice, Deepgram Flux, ElevenLabs Scribe, Voxtral Small 24B and Qwen2.5-Omni. Kaldi and icefall are also absent from the brief. New family members found: ZONOS2, Higgs TTS 3 / v3 STT, Voxtral TTS, Dia2, VibeVoice-ASR. Breadth is adequate.
- **Claims that read like recall, or that their citations don't support:** issues 1, 2 and 3 (and 4 for excerpt gaps). Nothing else in §3, §4, §5, §7 or §9 asserts a license, date or number without a fetch behind it. §3's Stable Audio / MusicGen / ACE-Step row openly says "not fetched here", which is acceptable for a boundary pointer.

## Re-check (fixed items)

Fresh auditor, 2026-09-26. Re-check fetch F0297 (`recheck: vibevoice-asr hf`), plus a live WebSearch rerun of the W0009 query and a GitHub MCP `issue_read get_comments` on currentai-org/os-ai-map#602.

1. **FIXED.** §9 Q5 now says Cohere took #1 at release (5.42%) and has since been passed by Granite Speech 4.1 (5.33%) and, per the same source, by ARK-ASR and MOSS-Transcribe. That matches the W0002 excerpt. The Breeze TTS 2 claim still rests on W0007.
2. **FIXED.** Option (b) now names Cohere Transcribe, MOSS-Transcribe-Diarize and OmniVoice ("the three"). The raw bodies agree: F0187 shows 213,697 downloads and apache-2.0, F0193 shows 163,483 and apache-2.0, and F0235 shows apache-2.0 for the MOSS repo. F0138 shows 1,369,984 downloads for OmniVoice, and F0214 shows Apache 2 code with CC-BY-NC weights. Breeze (13,603 downloads) and IndexTTS (bilibili custom license) are correctly left out. One nit: for Cohere, "Apache-2.0 code" is backed only by the HF card license in F0187, which covers the weights.
3. **FIXED.** The W0009 excerpt now carries a Qwen2.5-Omni quote ("near-duplex … 257ms average latency … full multimodal capability out of the box"). I reran the same WebSearch live and the result returns that Qwen2.5-Omni text. Note that the excerpt was extended in place under its original 20:01:37Z timestamp.
4. **FIXED.** The W0005 excerpt now includes "Sonic-3.6 | Cartesia | … #1 Provider Voice (~1,283 Elo)" and "Eleven v3 | ElevenLabs | … | Feb 2026". This matches the live page as confirmed in the first audit. The §6b elevenlabs-tts row, §7 and §9 Q7 cite it consistently.
5. **FIXED.** The §6b silero-vad row now reads "GitHub v6.2.1, 2026-02-24 (F0269); PyPI 6.2.3, 2026-09-23 (F0293)". The F0293 raw body gives 6.2.3 uploaded 2026-09-23T11:37:20 and 6.2.2 uploaded 2026-09-17.
6. **FIXED.** The §2 active definition now reads "any push to a non-archived repo … pushes to archived repos do not count". That matches the mms/wav2vec treatment. The count is still 37.
7. **FIXED.** The moonshine note now cites the ungh redirect (F0296, whose raw body resolves to `moonshine-ai/moonshine`). The cosyvoice note cites F0052, whose raw body resolves to `QwenAudio/CosyVoice`. F0004 and F0013 are no longer cited anywhere in sweep.md.
8. **FIXED.** The vibevoice row in rows.yaml and in the §6a block now declares `huggingface_model: microsoft/VibeVoice-ASR`. The §6b note and §9 Q3 agree with it. Live F0297 returns id `microsoft/VibeVoice-ASR` with 740,302 downloads and an MIT license. Schema validation prints `ok`. There is no `vibevoice` or `VibeVoice-ASR` entry in `research/corpus-index.tsv`, so there is no collision.
9. **FIXED.** §7 and §8 now attribute Kaldi and k2/icefall to the issue #602 seed proposal (W0020). The live GitHub read of #602 (comment 5816104845 by ccerv1, 2026-09-24) contains the W0020 text word for word: "Kaldi, k2 and icefall are legacy or research; they could be one row or merge into sherpa-onnx." The §8 count of 2 legacy names stands.
10. **FIXED (acceptable).** §4 rung 4 reads "at or near the top of a public leaderboard … Granite Speech 4.1 at 5.33% WER, W0002". W0002 supports "near the top" even with ARK and MOSS posting lower numbers. The text has no explicit "public-only" qualifier, but the hedge is enough.

**Overall: all 10 items FIXED.** Check 6 now passes. No new unsupported citations were introduced.
