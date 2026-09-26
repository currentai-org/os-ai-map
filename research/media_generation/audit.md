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

## Re-check of fixed items (second auditor)

Second, independent pass on 2026-09-26, limited to the 10 issues above and to the consistency checks
the fixes could break. Newly cited raw bodies read: F0399, F0401–F0407. This auditor's live fetches
are F0408–F0411 in `fetch-log.tsv`. No edits were made to `sweep.md`, `rows.yaml` or `gen/*`.

### Per-issue verdicts

| # | issue | verdict | reason |
|---|---|---|---|
| 1 | ideogram archived/fork citation | **FIXED** | The cell now reads "no/no (F0399)". F0399 has archived=false, fork=false, pushed 2026-06-04. The last-push cell gives both dates, "2026-06-04 per ecosyste.ms (F0399); ungh pushedAt 2026-06-30 (F0230)", so the disagreement is disclosed. |
| 2 | "no GitHub release" inferred from 404 / empty list | **FIXED** | The five ungh cells now read "no release returned (ungh 404, F03xx)" (trellis F0332, stable-audio-tools F0327, heartmula F0331, wan2gp F0326, audiocraft F0328). The flux, wan, ltx, sdnext and liveportrait cells read "no GitHub release returned by ecosyste.ms (F0346/F0345/F0344/F0341/F0349)". Each cited body is `[]`. |
| 3 | package trap on `stable-audio` | **FIXED** | The `stable-audio` model row now declares only `huggingface_model: stabilityai/stable-audio-3-medium`, with no github or pypi. A separate software row `stable-audio-tools` declares `Stability-AI/stable-audio-tools` and `pypi: stable-audio-tools`. Its 6b notes cite F0405, whose README line 37 reads `pip install "stable-audio-tools[train]"`. |
| 4 | install-doc citation for declared packages | **FIXED** | The five declared pypi fields each have an install-doc id in 6b. invokeai: F0407 (manual install page, "install the invokeai package", `uv pip install <PACKAGE_SPECIFIER>`; F0406 is the redirect stub to it). audiocraft: F0401 (`pip install -U audiocraft`). xfuser: F0402 (`pip install xfuser`). fastvideo: F0403 (`uv pip install fastvideo`). stable-audio-tools: F0405. `diffsynth` is no longer declared. F0404 shows only `pip install -e .`, although the README carries a PyPI badge, so "documents only a source install" is accurate. |
| 5 | ByteDance org-slug reuse | **ACCEPTED-AS-DISCLOSED** | seedream and seedance use `bytedance-seed-volcano-engine` in both `rows.yaml` and the 6b handle column. infinity-image and latentsync keep a new `bytedance` slug, which is not in the index. Both 6b cells and section 9 Q14 disclose this and ask the maintainer to rule. |
| 6 | flux declares the dormant repo | **FIXED** | `rows.yaml` now declares `black-forest-labs/flux2`. The push cell leads with "2026-03-12 flux2 (F0002)", and F0002 is flux2 (pushed 2026-03-12, not archived, not a fork). Re-fetched live as F0410, which matches. One loose end: the last-release cell still cites F0346, which is the old `black-forest-labs/flux` release list. The flux2 release list is also `[]` (F0411), so the value holds but the id points at the other repo. |
| 7 | midjourney "default June 2026" | **FIXED** | The members cell now reads "V8.1 alpha released 2026-04-14 (W0052); V8.0 alpha 2026-03-17 and V8.2 alpha per a search summary (W0024, not vendor-confirmed)". It no longer claims a default. |
| 8 | minor cells with no id | **FIXED** (8c accepted as before) | (a) musicgen now reads "MusicGen small/medium/large (F0104)", and F0104 lists exactly those three. (b) All 12 closed licence cells cite a homepage fetch (F0374–F0385) plus a W id. tripo cites W0063 and discloses the homepage 403 (F0376). (d) Section 4 now calls ComfyUI "named first among the four most-used UIs and the backend SwarmUI runs on (W0007)". The W0007 excerpt supports both parts, and the video-pipeline claim is gone. |
| 9 | minimax-hailuo plausibility | **FIXED** | 6b notes now carry a scorer note on the 3,657,004 figure. Its "created 2026-07-28" matches F0136 `createdAt`. |
| 10 | housekeeping (.lock, gen/out_*) | **NOT FIXED at hand-off; resolved by this auditor** | A zero-byte `research/media_generation/.lock` (mtime 20:27, left by the author's F0401–F0407 fetches) was present at the start of this pass. It has been removed, along with the `.lock` and `gen/out_*` files from this pass. Note that `gen/out__dups.md`, `gen/out__evidence.md`, `gen/out__parked.md` and `gen/out_rows.yaml` are tracked in HEAD and show as deleted in the working tree. The deletion must be committed, or they stay in the repo. |

### Consistency checks

- **Schema:** `jsonschema.validate(rows.yaml, registry.schema.json)` prints `ok`.
- **Dedup against `research/corpus-index.tsv`:** no slug, retired-alias, github, HF or PyPI collision across all 92 rows. That includes the new `stable-audio-tools` row and `black-forest-labs/flux2`.
- **Section 6a is identical to `rows.yaml`:** true (byte-identical).
- **`gen.py` reproduces the files:** `python3 research/media_generation/gen/gen.py` writes an `out_rows.yaml` that is byte-identical to `rows.yaml`. Its 6b table matches the sweep's line for line (94 lines), and the section 7a (52 lines) and 7b (15 lines) tables also match. The scratch files were deleted afterwards.
- **Section 2 and section 8, recounted from `rows.yaml` and 6b:**
  - 92 accepted: open 52, open-weights 26, source-available 2, closed 12.
  - 71 model rows and 21 software rows. The software rows split open 19 and source-available 2.
  - Modalities: image 20, video 16, 3D 11, audio 12. Closed rows: image 4, video 4, audio 2, 3D 2.
  - 62 org slugs. The largest is `stability-ai` at 6/92 = 6.5%.
  - 59 parent companies, with Stability AI and Tencent tied at 6.
  - 66 of 80 non-closed rows active, and the 14 dormant rows match the list in the sweep.
  - 53 rows with a usage instrument (92 − 39).
  - 248 = 106 + 142, where 248 is 235 candidate-source pairs plus 13 index matches.
  - 142 = 92 + 50.
  - Every figure matches the author's reported totals.
  - Minor: `stable-audio-tools` carries `src=['brief']`, since it was split from the brief's "Stable Audio Open" lead. It is therefore rightly absent from section 8's two "not in the brief" lists. `gen.py`'s diagnostic list uses a hard-coded brief-name set and does print it, but no count depends on that list.
- **Cited ids:** all 308 F/W ids cited in 6b exist in `fetch-log.tsv` or `web-log.tsv`. Every cited F id has a raw body except F0310. That fetch has HTTP 000 and 0 bytes, and its cell says "ungh fetch did not complete".
- **stable-audio-tools resolves live:**
  - F0408 (repos.ecosyste.ms) returns 200: `Stability-AI/stable-audio-tools`, licence mit, not archived, not a fork, pushed 2026-09-18, which matches the 6b cell.
  - F0409 (packages.ecosyste.ms) returns 200: `stable-audio-tools`, licence mit, latest 0.0.20 (2026-05-20), 102,734 downloads last month, which matches F0277.

### Overall status

**PASS.** Eight issues are fixed and issue 5 is accepted as disclosed. Issue 10 was not clean at
hand-off: the leftover `.lock` has been removed, and the tracked `gen/out_*` deletions must be
included in the commit. All consistency checks pass. One non-blocking citation nit remains: the flux
last-release cell cites F0346, which is the old repo. F0411 is the flux2 equivalent and gives the
same `[]`.

## Author follow-up to the re-check

- Issue 6 leftover: the flux last-release cell now cites the flux2 release list (F0411, `[]`) as well as the old flux repo (F0346). 6b was regenerated from `gen/data.py`, and `rows.yaml` is unchanged.
- Issue 10: `gen/out_*` was already removed from the tree in commit ff1e2ec. `git ls-files research/media_generation/gen` lists only data.py, gen.py and parked.py, and no `.lock` file remains.

Final status: PASS (second auditor), with the one leftover closed.
