# Audit: media_generation sweep, 2026-09-26

Independent audit of `sweep.md`, `rows.yaml`, `fetch-log.tsv` + `raw/`, `web-log.tsv` and `gen/`,
run against the six checks in `research/RUNBOOK.md` ("Finishing: independent audit, then push").
The auditor's own live fetches are F0386–F0400 in `fetch-log.tsv`; its WebFetch calls are
W0067–W0069 in `web-log.tsv`. No edits were made to `sweep.md`, `rows.yaml` or `gen/*`.

## Verdicts

| # | Check | Verdict |
|---|---|---|
| 1 | Re-fetch 15 claims live | **PASS**: 16 of 16 claims match. No wrong licence, owner or archive status, and no figure off by more than 25%. |
| 2 | Unsourced facts | **PASS with minor issues**: 91 rows scripted. Every F/W id exists, every non-200 cited fetch is acknowledged in its cell, and every W id has an excerpt. 21 cells spot-checked against raw bodies, and all support their fact. See issues 1, 2 and 8. |
| 3 | Every artifact resolves live | **PASS with one issue**: every github, HF, PyPI and homepage artifact resolves with HTTP 200 today. The tripo homepage 403 and the wan2gp fork flag are both acknowledged. See issue 3 (package trap on `stable-audio`) and issue 4. |
| 4 | Schema and dedup | **PASS**: `rows.yaml` validates (`ok`). No slug, retired alias, github, HF or PyPI collision with `corpus-index.tsv`. Section 6a is identical to `rows.yaml`. See issue 5 (org-slug reuse). |
| 5 | Counts reconcile, section 2 computed from section 6 | **PASS**: `gen.py` re-run reproduces `rows.yaml` and the 6b table byte for byte. All section-2 metrics match, and both equations balance (247 = 106 + 141; 141 = 91 + 50). |
| 6 | Recency and breadth | **PASS**: all 385 author fetches and 66 web-log rows are timestamped 2026-09-26. 43 accepted candidates beyond the brief were surfaced by search, leaderboards, topic pages or HF listings, plus 12 self-named leads that were verified live. See issues 6–8 for minor recall-like cells. |

No FAIL-level item was found. The issues below are corrections and clarifications, not blockers.

## Check 1: re-fetched claims

Rows were sampled at roughly every sixth row of 6b (rows 3, 9, 15, 21, 27, 31, 37, 44, 48, 60, 66,
72, 75, 82 and 87) plus ideogram (row 13) for its archived/fork cell. The sample covers 13 open rows,
5 software rows and 2 closed rows.

| # | row / claim | sweep value | live value | fetch id | verdict |
|---|---|---|---|---|---|
| 1 | qwen-image: Qwen-Image-2.1 licence | "Qwen RESEARCH LICENSE", non-commercial (F0116, F0170) | cardData `license_name: qwen-research` | F0386 | PASS |
| 2 | hunyuan-image: licence territory | Tencent Hunyuan Community, excludes EU/UK/South Korea | "DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA" | F0387 | PASS |
| 3 | longcat-image: HF 30d downloads | 13,815 (F0092) | 13,815; apache-2.0 | F0388 | PASS |
| 4 | wan: last push / licence / archived | 2026-09-21, Apache-2.0, no/no (F0023) | pushed 2026-09-21, apache-2.0, archived false, fork false | F0389 | PASS |
| 5 | magi: HF downloads / licence | 0 downloads; Apache-2.0 (F0127) | downloads 0; apache-2.0 | F0390 | PASS |
| 6 | minimax-hailuo: HF 30d downloads | 3,657,004 (F0136) | 3,657,004; licence `minimax-h3-community-license-agreement` | F0391 | PASS (see issue 9) |
| 7 | trellis: HF 30d downloads | TRELLIS-image-large 2,118,600 (F0366) | 2,118,600; mit | F0392 | PASS |
| 8 | instantmesh: dormant, last push | 2025-01-03, no/no (F0043) | pushed 2025-01-03, archived false, fork false | F0393 | PASS |
| 9 | stable-audio: PyPI monthly downloads | stable-audio-tools 102,734/month (F0277) | 102,734 last-month | F0394 | PASS (identity: see issue 3) |
| 10 | comfyui: canonical identity / licence / stars | Comfy-Org/ComfyUI, GPL-3.0, 134,880 stars | Comfy-Org/ComfyUI, gpl-3.0, 134,880, not archived | F0395 | PASS |
| 11 | swarmui: licence text | MIT (F0062) | LICENSE.txt: "The MIT License (MIT) Copyright (c) 2024-2025 Alex "mcmonkey" Goodwin" | F0396 | PASS |
| 12 | wan2gp: fork flag | FORK=true (F0066) | fork true (source Wan-Video/Wan2.1), pushed 2026-09-18, licence other | F0397 | PASS |
| 13 | xdit: PyPI xfuser downloads / identity | 23,947/month; homepage is xDiT repo | 23,947 last-month; repository_url github.com/xdit-project/xDiT | F0398 | PASS |
| 14 | ideogram: archived/fork, last push | no/no, 2026-06-30 (F0230, ungh) | ecosyste.ms: archived false, fork false, pushed 2026-06-04 | F0399 | PASS (see issue 1) |
| 15 | midjourney (closed): V8.1 | V8.1, default June 2026 (W0024, W0052) | V8.1 release page dated Apr 14, 2026; the "default" on that page is HD mode within V8.1 | W0068 | PASS (see issue 7) |
| 16 | runway-gen (closed): current model | Gen-4.5, "world's best video model" (W0060) | Gen-4.5, same quote | W0067 | PASS |

Extra live check: AA open-weights text-to-video board (W0069) still reads MiniMax H3 1220, LTX-2.5
Fast 1055, LTX-2.5 Pro 1053, LTX-2.3 Fast 975, which matches W0010.
Extra live attempt: `tencent-ailab/SongGeneration/HEAD/LICENSE.txt` returned 404 (F0400). The
songgeneration licence remains unread, as the sweep already says.

## Check 2: cells spot-checked against raw bodies (21)

All of these supported the cited fact: F0367 (FLUX.1-dev `flux-1-dev-non-commercial-license`),
F0168 (HunyuanVideo EU/UK/KR exclusion), F0180 (LTX-2.x "$10,000,000"), F0181 (MiniMax-H3 excludes
EU, UK, Korea and USA), F0188 (Music3 "20 million US dollars"), F0171 (CogVideoX "1 million visits
per month"), F0185 (Wan2GP no SaaS/white-label), F0238 (FIBO CC BY-NC 4.0), F0246 (SAM License
Nov 19, 2025), F0173 (Cube Research-Only RAIL-MS), F0363 (`stable-audio-community`), F0050 (heartlib
pushed 2026-09-26), F0033 (kandinsky mit), F0170 (Qwen-Image-2.1 non-commercial), F0237 (Easy
Diffusion Section II), F0308 (ComfyUI v0.37.0, 2026-09-21), F0330 (YuE yue2-v0.1.6, 2026-09-09),
F0347 (Open-Sora v1.3, 2025-02-21), F0319 (LightX2V 0.5.0, 2026-09-10), F0324 (DiffusionBee 2.5.3,
2024-08-14) and F0312 (A1111 v1.10.1, 2025-02-09). The org-listing download figures in F0077, F0079,
F0085, F0094, F0104 and F0113 also match 6b exactly.

## Check 6: candidates found beyond the brief's leads

Surfaced by search, AA boards, GitHub topic pages or HF org listings (43): z-image, fibo, glm-image,
ideogram, ernie-image, longcat-image, omnigen, infinity-image, ming-image, nextstep, step1x-edit,
magi, skyreels, kandinsky, minimax-hailuo, longcat-video, helios, stable-video-diffusion,
liveportrait, latentsync, triposg, triposr, step1x-3d, stable-fast-3d, spar3d, instantmesh, cube,
partcrafter, heartmula, minimax-music, mmaudio, thinksound, hunyuanvideo-foley, foleycrafter,
krita-ai-diffusion, stability-matrix, diffusionbee, dream-textures, seedream, seedance, lyria, meshy
and tripo.

Named from the author's own leads, not from a search, and each verified by fetch (12): sam-3d,
diffrhythm, songgeneration, step-video, easy-diffusion, wan2gp, framepack, stable-diffusion-cpp,
xdit, lightx2v, fastvideo and diffsynth-studio. The sweep discloses this split in section 8.

## Issues

1. **6b `ideogram` / archived-fork cell: the cited id does not carry the fact.** The cell reads
   "no/no (F0230)", but F0230 is `ungh.cc/repos/ideogram-oss/ideogram4`, and that response has no
   `archived` or `fork` field. The auditor's ecosyste.ms fetch (F0399) confirms archived=false and
   fork=false, so the value is right but the citation is wrong. The sources also disagree on last
   push: ungh (F0230) gives 2026-06-30 with 2,856 stars, while ecosyste.ms (F0399) gives 2026-06-04
   with 1,234 stars. Fix: cite F0399 for archived/fork, and note that the push date comes from ungh.
2. **"No GitHub release" is inferred from a 404.** The last-release cells for trellis (F0332),
   stable-audio (F0327), heartmula (F0331), wan2gp (F0326) and audiocraft (F0328) cite ungh
   `/releases/latest` responses of HTTP 404 ("GitHub API error: 404"). GitHub does return 404 when a
   repo has no release, so the reading is plausible. It is still a 404 read as an absence, which the
   preamble warns against. The flux, wan, ltx and sdnext cells rely on an empty ecosyste.ms
   `releases?per_page=1` list (`[]`), which may be an indexing gap. Fix: word these cells as "no
   release returned by ungh/ecosyste.ms".
3. **Package trap on `stable-audio` (rows.yaml line for slug `stable-audio`, `pypi:
   stable-audio-tools`).** `stable-audio-tools` is the training and inference library (the engine),
   not the Stable Audio model. The sweep separates engine from model everywhere else (musicgen vs
   audiocraft), and the preamble says "a model and the engine that runs it are two products". On
   top of that, section 2 counts this row as having a usage instrument partly because of the
   package. The row already has a real HF instrument (81,781, F0363), so the count does not change,
   but the declared package measures a different product. Fix: drop `pypi` from `stable-audio`, or
   split out a `stable-audio-tools` software row.
4. **No install-doc citation for any declared package.** The preamble requires "cite the doc page
   that says so" for every declared PyPI package. The sweep cites package metadata instead:
   invokeai project_urls (F0305), xfuser homepage (F0306), stable-audio-tools author "Stability AI"
   (F0302), diffsynth author "ModelScope Team" (F0303), and repository_url for audiocraft and
   fastvideo (F0276, F0279). Ownership is confirmed for all of them, and the auditor found no
   wrong-project package. The install-path doc page is still missing for each. Fix: add a README or
   docs fetch showing `pip install <name>` for invokeai, xfuser, fastvideo, diffsynth and audiocraft.
5. **Org-slug reuse (rows.yaml `infinity-image`, `latentsync`; 6b `seedream`, `seedance`).** The
   index already has ByteDance as `bytedance-seed-volcano-engine`. `rows.yaml` uses that slug for
   seedream and seedance, but introduces a new `bytedance` slug for infinity-image and latentsync.
   The preamble says "Reuse the org slug from the index when that org is already on the map." The
   6b handle column for seedream and seedance also reads `bytedance-seed`, which disagrees with
   `rows.yaml`. Fix: either reuse `bytedance-seed-volcano-engine`, or state in section 9 why the
   non-Seed ByteDance teams get a separate slug. Also make the 6b and `rows.yaml` values agree.
6. **6b `flux`: the declared GitHub artifact is the dormant repo.** `rows.yaml` declares
   `black-forest-labs/flux`, last pushed 2025-07-31 (F0001), which is more than 12 months before the
   run. The "active in last 12 months" metric counts flux as active only through the undeclared
   `black-forest-labs/flux2` (pushed 2026-03-12, F0002). The metric is therefore computed from an
   artifact the row does not carry. Fix: declare `black-forest-labs/flux2` (the current FLUX.2
   release), or note the basis of the activity count.
7. **6b `midjourney` members cell: "V8.0/V8.1 (default June 2026)" rests on a search summary.** The
   only support for "default June 2026" is the W0024 WebSearch excerpt. The vendor page W0052/W0068
   gives the V8.1 date (Apr 14, 2026) but says HD mode is the default within V8.1, not that V8.1
   became the default model. Fix: soften the cell to "per search summary (W0024)", or fetch a vendor
   page that states the default.
8. **Minor cells with no id.**
   (a) 6b `musicgen` members: "small/medium/large/melody/stereo". F0104 lists only small, medium
   and large, so melody and stereo are unsourced.
   (b) All 12 closed rows: the licence cell "proprietary API/service" has no id. The homepage
   fetches (F0374–F0385) exist but are not cited in the cell.
   (c) 6b `ernie-image` archived/fork: "n/a (no GitHub repo fetched)". This one is acceptable as a
   stated absence of a fetch.
   (d) Section 4 calls ComfyUI "the one UI with a mature video pipeline", citing W0007. The W0007
   excerpt supports "SwarmUI runs on top of ComfyUI" but not the video-pipeline claim.
9. **Plausibility note, no fix required: `minimax-hailuo` at 3,657,004 HF 30-day downloads.** This
   33B model was released about six weeks before the run (HF lastModified 2026-08-13), and its
   figure is the largest in the whole set, above SDXL base (3.6M). The live figure matches (F0391).
   The brief says to flag a number that looks implausible instead of silently accepting it. Suggest
   adding a one-line note in 6b so the scorer can decide whether to band adoption on it.
10. **Housekeeping.** `rfetch.sh` leaves a `.lock` file in `research/media_generation/`. The auditor
    removed it, along with the `gen/out_*` scratch files. Make sure neither is committed.
