# Audit: robotics_embodied + world_models sweep (2026-09-26)

Independent audit of `sweep.md`, `rows.robotics_embodied.yaml`, `rows.world_models.yaml`, `fetch-log.tsv`,
`web-log.tsv` and `raw/`. Audit fetches were logged through `research/rfetch.sh` with labels starting `audit:`
(claim re-checks, F0444–F0463, F0597) and `audit-resolve:` (artifact resolution, F0464–F0596). All ran on
2026-09-26. `api.github.com` and `github.com` were not used (403 in this environment).

**Overall: FAIL.** 6 items to fix (A1–A6 below). Checks 1, 3 and 4 pass. Checks 2, 5 and 6 fail on
specific items. None of the items overturns either verdict, but A5 bears on Part A, question 1.

| # | check | result |
|---|---|---|
| 1 | Live re-fetch of 17 claims | PASS |
| 2 | Unsourced facts / excerpt supports claim | FAIL (A1–A4) |
| 3 | Every artifact resolves live | PASS |
| 4 | Schema and dedup | PASS |
| 5 | Counts reconcile | FAIL (A6, plus a disclosure note) |
| 6 | Recency and breadth | FAIL (A5) |

---

## Check 1: live re-fetch of 17 claims: PASS

Sampled about every 5th evidence row across both parts (Part A rows 5, 10, 15 … 60; Part B rows 1, 4, 9, 14, 19),
mixing license, activity, adoption and identity.

| # | slug (part) | claim in sweep | live result (id) | verdict |
|---|---|---|---|---|
| 1 | isaac-sim (A) | Apache-2.0 repo code; runtime needs NVIDIA components under other terms | LICENSE text says exactly that (F0444, identical sha to F0159) | match |
| 2 | robocasa (A) | no PyPI package (cited via ecosyste.ms 404, F0263) | pypi.org JSON 404 (F0445) | match |
| 3 | robocasa (A) | MIT behind label `other` | LICENSE is MIT, "the RoboCasa Team" (F0446) | match |
| 4 | mjlab (A) | PyPI 84,063/month; repository_url mujocolab/mjlab | 84,063 last-month, repo matches, Apache-2.0 (F0447) | match |
| 5 | smolvla (A) | HF 71,362/30d, apache-2.0, modified 2026-09-17 | 71,362; apache-2.0; 2026-09-17 (F0448) | match |
| 6 | gigabrain (A) | owner open-gigaai, not archived, push 2026-02-13, Apache-2.0, 2,263 stars | identical (F0449) | match |
| 7 | molmoact (A) | MolmoAct2 HF 20,533/30d, no license field | 20,533; cardData has no license (F0450) | match |
| 8 | rynnvla (A) | canonical alibaba-damo-academy/RynnVLA-002, push 2025-12-02, 1,131 stars | identical (F0451) | match |
| 9 | unifolm-vla (A) | HF 175/30d; CC BY-NC-SA 4.0 on the card | 175 (F0452); card metadata has no license, but the README body states CC BY-NC-SA 4.0 (F0243 line 59) | match |
| 10 | vla-jepa (A) | HF 0/30d, card apache-2.0 | 0; apache-2.0 (F0597) | match |
| 11 | agibot-world (A) | Beta 92,675/30d; CC BY-NC-SA 4.0 in the gated prompt | 92,675; gated prompt states CC BY-NC-SA 4.0 (F0454) | match |
| 12 | reachy-mini (A) | push 2026-09-21, Apache-2.0, 1,515 stars | identical (F0455) | match |
| 13 | openarm (A) | Apache-2.0 | Apache License 2.0 text (F0456) | match |
| 14 | openvla (A) | fork of TRI-ML/prismatic-vlms; push 2025-03-23; HF 445,187/30d; MIT | fork=True, source TRI-ML/prismatic-vlms, 2025-03-23 (F0462); 445,187, mit (F0463) | match |
| 15 | cosmos (B) | Cosmos3-Nano 126,107/30d, openmdw1.1 | 126,107; license_name openmdw1.1-license (F0461) | match |
| 16 | hy-world (B) | Tencent HY-World 2.0 Community License, excludes EU/UK/South Korea | same text, same sha as F0200 (F0457) | match |
| 17 | yume / ctrl-world / dreamx-world (B) | Yume HF 0, apache-2.0; Ctrl-World push 2025-10-24, 50 stars, MIT; DreamX-World-5B 1,095, mit | Yume 0, apache-2.0 (F0458); Ctrl-World identical (F0459); DreamX 1,095, mit (F0460) | match |

No drift at all, which is expected for same-day re-fetches. F0453 (401) was an auditor probe of a wrong id
(`ginwind/VLA-JEPA-Pretrain`), not a sweep claim; the declared id was re-fetched as F0597.

## Check 2: unsourced facts: FAIL

**Mechanical pass.** All 339 ids cited in §1–§7 and §C of both parts exist in the logs. Every W id has an
excerpt. Every F id cited as evidence is HTTP 200, apart from the three the header names: F0263 (404), F0307
(404) and F0086 (curl failure, cited only as "retried as F0090"). Every evidence cell that states a fact
carries an id. Cells without an id are the org-handle column, which just restates the declared artifacts,
and judgment notes ("Small signal", "Governing release RDT2", and similar), both acceptable.

**Content pass: body/excerpt vs claim.** Programmatic comparison of 237 cells against their cited bodies
(last push, stars, archived/fork, PyPI monthly downloads, single-repo HF downloads) found **0 mismatches**.
By hand I also checked 40 more cells: licenses F0159, F0161, F0164, F0202, F0209, F0210, F0211, F0230, F0237,
F0241, F0243, F0244, F0247, F0252, F0316; listing-based HF counts F0097, F0098, F0100, F0102, F0106, F0109,
F0110, F0120, F0297, F0299, F0315; release rows F0319, F0387, F0395, F0416, F0423; and web excerpts W0002,
W0008–W0012, W0015–W0023, W0026, W0029–W0036, W0039–W0044. Most hold up. Four do not:

- **A1. `sweep.md` Part B, hy-world row, and §C "Corrections to the briefs": W0017 does not say Apache 2.0.**
  The row reads "A search summary called it Apache 2.0 (W0017); the license text contradicts it", and §C
  repeats "despite what a secondary summary said (W0017 vs F0200)". The full W0017 excerpt ("Tencent-Hunyuan/HY-World-2.0
  multi-modal world model released April 15-16 2026; … HunyuanWorld-Voyager … weights released Sept 2 2025")
  contains no license claim. Either cite the log entry that actually carried the Apache-2.0 statement, or
  drop the sentence. The license itself (F0200) is correct and re-verified (F0457).
- **A2. `sweep.md` Part A, gr00t row and §5: the non-commercial GR00T checkpoints are under-reported.** The
  sweep says "one GR00T-N1.5 fine-tune carries nvidia-oneway-noncommercial (F0096)". F0096 shows **two**:
  `nvidia/GR00T-N1.5-3B_Assemble_Trocar` (license_name `nvidia-oneway-noncommercial`) and **`nvidia/GR00T-H`**
  (license_name `nvidia-license`, link to NVIDIA-OneWay-Noncommercial-License-22Mar2022.pdf). GR00T-H is one of
  the member checkpoints the row itself lists. Record GR00T-H as non-commercial in the license cell and in §5.
- **A3. `sweep.md` Part A, aloha-2 row: the paper date contradicts its source.** The row says "paper 2024-05
  (F0442)". The F0442 arXiv page shows "[Submitted on 7 Feb 2024]" and `citation_date 2024/02/07`. The
  arXiv number 2405.02292 suggests May, but the cited body says February. Use the body's date, or cite
  something that supports 2024-05.
- **A4. `rows.world_models.yaml`, slug `oasis`: `org: decart` is unsupported for the declared artifacts.**
  Both declared artifacts belong to Etched: github `etched-ai/open-oasis` (owner etched-ai, "Inference script
  for Oasis 500M", F0071) and HF `Etched/oasis-500m` (W0012: "etched-ai/open-oasis, Etched/oasis-500m"). The
  only Decart evidence is W0041 (decart.ai, about Oasis 3), and no fetched body ties the open 500M release to
  Decart. Either cite a source that establishes Decart as the vendor of the line, or pick the org the evidence
  supports and put the joint attribution in question 11.

**On the 404s cited as evidence of absence:** acceptable, with one caveat. F0263 (robocasa not on PyPI) is
confirmed by an authoritative pypi.org 404 (F0445); citing F0445-style pypi.org JSON would be stronger than an
ecosyste.ms 404. F0307 is cited only for "RynnWorld-Teleop repo not indexed by ecosyste.ms", which is exactly
what a 404 there shows. It is not used to claim the repo doesn't exist, so that's fine. Neither is a 429/403
passed off as a finding. The 16 ungh 403s and 39 ungh 429s are never cited; release dates come from
ecosyste.ms `/releases` (F0387–F0441).

Minor notes (non-blocking): the so-101 "v0.1.1, 2024-05-17" release is flagged `prerelease: true` in F0416;
worth saying. "No GitHub releases recorded" rests on empty ecosyste.ms `/releases` arrays, which can lag
GitHub. The wording "recorded" is appropriately hedged.

## Check 3: every artifact resolves live: PASS

All **133** artifacts in the two rows files were fetched through `rfetch.sh` (F0464–F0596): 69 github via
ecosyste.ms, 43 HF models, 5 HF datasets, 11 PyPI (pypi.org JSON), 1 arXiv, 4 homepages. **133/133 returned
HTTP 200.**

- GitHub: no repo is archived. `full_name` matches the declared `owner/repo` for all 69 (case-insensitive).
  The only fork is openvla/openvla (of TRI-ML/prismatic-vlms), which the sweep discloses. Repos with a push
  before 2025-09-26 (openvla, octo, spatialvla, roboflamingo, droid, koch-v1-1, aloha, lekiwi, oasis, diamond)
  are all reported dormant with their real dates.
- HF: every id resolves to itself. Gated ids (galaxea-g0, robomind, agibot-world, oasis, unifolm-wma) are
  `gated: auto` and the sweep notes gating on each.
- PyPI: all 11 resolve. mani-skill's PyPI homepage still points to haosulab/ManiSkill, consistent with the
  move the sweep reports. `playground` and `genesis-world` carry no GitHub URL in PyPI metadata; the sweep
  cites README install lines (F0286, F0278) for both, which satisfies the package-trap rule.
- Homepages/arXiv: gemini-robotics and genie pages decode to "Gemini Robotics — Google DeepMind" and "Genie 3 —
  Google DeepMind" (gzip bodies). runway-gwm page title "Introducing Runway GWM-1". aloha-2 page and arXiv
  2405.02292 are live.

## Check 4: schema and dedup: PASS

- `jsonschema.validate` against `docs/schemas/registry.schema.json`: `rows.robotics_embodied.yaml` ok,
  `rows.world_models.yaml` ok.
- Against `research/corpus-index.tsv` (1,055 rows; slug, retired_aliases, github, huggingface, pypi, all
  `;`-split and case-folded): **no slug, alias, github, HF or PyPI collision** in either file. There are no
  duplicate slugs or artifacts across the two files. Near-matches on substrings only (smolvla/smol, molmoact/olmo,
  gemini-robotics/gemini, hunyuan-gamecraft/hunyuan) are different products.
- Org slugs reuse index slugs where the org exists (google, nvidia, meta, microsoft, tencent, hugging-face,
  alibaba-damo-academy, shanghai-ai-laboratory, allen-institute-for-ai). The 50 new org slugs are new vendors.
  The ant-group/robbyant and ai2/allen-institute-for-ai calls are already raised in question 6.

## Check 5: counts reconcile: FAIL (minor)

**Arithmetic balances.** Recomputed from `spec.py`:

- Part A: raw = 103 accepted-row source ids + 54 parked source ids = **157**; unique = 60 + 37 = **97**;
  duplicates = 157 − 97 = **60**. Both equations balance.
- Part B: raw = 40 + 28 = **68**; unique = 21 + 21 = **42**; duplicates = **26**. Both equations balance.

**§2 is consistent with §6** (recounted from the evidence table and rows, independently of gen.py):

- A: 60 rows; open 50 / open-weights 9 / closed 1; model 29, software 17, hardware 8, dataset 6; models open
  19 / open-weights 9 / closed 1; 46 orgs; largest google 6 = 10.0%; active 49 (inactive: openvla, octo,
  spatialvla, go-1, nora, roboflamingo, interndata-a1, koch-v1-1, aloha, aloha-2, lekiwi); usage instrument
  42; datasets with CC BY-NC-SA 2. All match.
- B: 21 rows; open 12 / open-weights 6 / closed 3; 20 orgs; largest tencent 2 = 9.5%; instrument 17; HF lines
  under 200 downloads 12 of 17. All match. Sub-populations 9 + 8 + 2 + 2 = 21 match.

Issues:

- **A6. `sweep.md` Part B §7/§8: rows the sweep itself labels duplicates are counted as unique candidates.**
  PW contains "VLA-JEPA: duplicate: accepted in robotics_embodied", "GR00T / GR00T Dreams: duplicate",
  "RynnVLA-002: duplicate: member of rynnvla", and "WorldVLA: retired alias -> rynnvla". WorldVLA and RynnVLA-002
  are the same line. Under the doc's own definition ("duplicate signals are the extra surfacings of a candidate
  already seen"), these are duplicate signals, not unique candidates. Recount them as duplicates (unique 38,
  parked 17), or state in §8 that the per-part counts treat cross-part duplicates as unique within the part.
- Disclosure note (fix alongside A6): Part B §2 defines "active" as "push or release on/after 2025-09-26", but
  `gen.py:active()` also counts any closed product whose page is live. `runway-gwm` has no dated push or release
  and is counted active only through that rule (19 of 21; 18 of 21 by the stated definition). State the
  closed-product rule in the §2 line, or record GWM-1's release date.

## Check 6: recency and breadth: FAIL

- **Recency: ok.** All 443 sweep fetch rows and all 44 web-log rows are timestamped 2026-09-26 (19:59–20:12Z).
- **Candidates the sweep surfaced that the briefs did not name:** confirmed against §C and the briefs.
  - Robotics accepted: robomimic, newton, brax, mjlab, robotwin, roboverse, gigabrain, galaxea-g0, lingbot-vla,
    internvla, wall-oss, molmoact, cogact, spatialvla, univla, go-1, rynnvla, xiaomi-robotics, being-h,
    spirit-vla, hy-embodied-vla, unifolm-vla, alpamayo, eo-1, nora, x-vla, nvidia-physical-ai-dataset,
    interndata-a1, berkeley-humanoid-lite, lekiwi, openarm, aloha-2, plus agibot-world, which the brief did not
    name either.
  - World models accepted: hunyuan-gamecraft, genie-envisioner, unifolm-wma, gigaworld, ctrl-world,
    boundless-world-model, dreamer, td-mpc, rynnworld, dreamx-world, runway-gwm.
  - Each was traced to a search or listing id (W0001, W0003, W0009, W0011, W0013, W0019–W0023, W0029–W0035,
    W0043, W0044, F0297, F0298).
- **A5. Candidates surfaced inside the declared retrieval cutoffs are neither accepted nor parked.** The
  header says the HF `robotics` model filter was read to the top 60 (F0298) and the dataset filter to the top
  40 (F0297), and the preamble forbids letting a cutoff silently drop something already found. Distinct
  products in those bodies that appear nowhere in `sweep.md` (ports and fine-tunes of accepted lines excluded):
  - F0298 (models): `GEAR-Dreams/DreamZero-DROID` (NVIDIA GEAR world-action model, relevant to Part B),
    `BAAI/RoboBrain2.0-3B` and PhysBrain1.5 (embodied VLMs, likely → multimodal_models like RynnBrain),
    `allenai/GraspMolmo`, `YuankaiLuo/SimVLA-LIBERO`, `CMSManhattan/JiRackPrecisionTokenizer`.
  - F0297 (datasets): `ACERobotics/ACE-Data-0` (256k), `XDOF/ABC-130k` (242k), `fpvlabs/stereo-550` (227k),
    `genrobot2025/Gen-HumanEgo` (138k), `simple-world-lab/HiFi-UMI-2K` (115k), `fleaven/Retargeted_AMASS_*`
    (109–126k), `ropedia-ai/xperience-10m` (85k), `InternRobotics/OmniWorld` (78k), `OpenMOSS-Team/OmniAction`
    (68k), `yaak-ai/L2D` (67k), `leggedrobotics/grand_tour_dataset` (37k), plus smaller ones (deform360,
    MetaFold, trex_dataset).
  - W0043 (Part B): "DreamX-Phi action-conditio…" is surfaced and never mentioned.

  Park each with a reason (a coverage limit is fine), and update §8. This matters beyond bookkeeping. Part A
  question 1 argues that datasets (6) "can't stand alone". Around ten more robotics datasets, several above
  the downloads of accepted rows, sit unexamined in F0297, so the per-type supply figure for datasets is a
  floor, and §1/§9 should say so. Also, the parked row "10Kh-RealOmni-OpenData" misspells the real id,
  `genrobot2025/10Kh-RealOmin-OpenData` (F0297).
- **Recall-like claims:** none found. I scanned the §1/§3/§4/§9 prose of both parts for dates, counts, prices
  and venues without an id. Every specific fact carries one (Cosmos 3 2026-06-01 via F0423/W0010, DROID
  92,223 via W0032, ICML/ICLR via W0044/W0029, prices via W0019/W0033). The uncited statements are
  characterizations: the ladder rung descriptions (PyBullet as CPU rigid-body, MJX/ManiSkill as GPU-parallel)
  and "the three Columbia layers", which is repo context. These are acceptable as framing, not evidence.

---

## Other observations (non-blocking, for the curator)

- **Open-status rule is applied unevenly.** Where the weights carry no license, some rows are `open-weights`
  (wall-oss, nora, boundless-world-model) and others `open` (molmoact, whose governing MolmoAct2 card has no
  license; diamond, whose HF card has no license). NC-licensed models are `open-weights` (internvla, go-1,
  unifolm-vla), but NC-licensed datasets are `open` (agibot-world, interndata-a1, "open means downloadable").
  It doesn't change any count by type, but it moves the open/open-weights split in both §2s. Pick one rule.
- `rynnworld` declares github `RynnWorld-4D` ("4D Embodied World Models for Robotic Manipulation", F0308,
  5 stars, license text unread) and HF `RynnWorld-Teleop`. That is two repos under one line; the
  action-conditioning evidence (W0043) is for Teleop.
- `cosmos` declares github `NVIDIA/cosmos`; ecosyste.ms returns `NVIDIA/Cosmos` (case only; fine).

## Issues to fix

1. **A1**: hy-world row + §C: W0017 does not support "a search summary called it Apache 2.0". Re-cite or remove.
2. **A2**: gr00t row + §5: F0096 shows `nvidia/GR00T-H` (a listed member) under NVIDIA OneWay Non-commercial as
   well as the N1.5 Assemble_Trocar fine-tune. Record both.
3. **A3**: aloha-2 row: "paper 2024-05 (F0442)" vs F0442 "Submitted on 7 Feb 2024". Correct the date or the source.
4. **A4**: `rows.world_models.yaml` oasis `org: decart`: the declared artifacts are Etched's (F0071, W0012).
   Support Decart with a source or change the org.
5. **A5**: park (with reasons) the candidates in F0297/F0298/W0043 listed in check 6, fix the "RealOmni" typo,
   update both §8s, and note in Part A §2/§9 that the dataset supply of 6 is a floor.
6. **A6**: Part B §8: the four "duplicate"/"retired alias" parked rows are counted as unique candidates. Reclassify
   them or state the convention. Also state the closed-product "active" rule in the Part B §2 line (runway-gwm).

---

## Re-check (2026-09-26, fixed items only)

Re-read the regenerated `sweep.md`, `rows.robotics_embodied.yaml`, `rows.world_models.yaml` and `spec.py`.
No new fetches were needed. Every fact checked below is in bodies or excerpts already logged.

**Overall: FAIL.** One item is left: A5 introduced an unsourced arXiv id. Everything else passes.

| item | result | evidence |
|---|---|---|
| A1 hy-world / §C W0017 | PASS | The hy-world license cell now cites only F0200 (and F0196/F0201/F0206). W0017 is cited only for "Voyager is conditioned on camera input", which its excerpt supports. §C now reads "Tencent community license that excludes the EU, UK and South Korea … (F0200)", which matches F0200/F0457. |
| A2 gr00t non-commercial SKUs | PASS (note) | The row and Part A §5 now name both `GR00T-N1.5-3B_Assemble_Trocar` (nvidia-oneway-noncommercial) and `nvidia/GR00T-H` (nvidia-license), F0096, and both match the card metadata. Note: GR00T-H's `license_name` is the generic "nvidia-license", but its `license_link` is the NVIDIA OneWay **Noncommercial** License PDF. Add "(links to the OneWay Noncommercial license)" so a scorer doesn't read it as the commercial Open Model License. Non-blocking. |
| A3 aloha-2 date | PASS | The release cell reads "arXiv submitted 2024-02-07 (F0442)", which matches F0442's `citation_date 2024/02/07`. |
| A4 oasis org | PASS | The row is now `Oasis (open 500M)`, `org: etched`, status open, license "code and weights MIT (F0071, F0126)", with members from W0012. All of this is supported. Decart's Oasis 3 is parked as closed on W0041, and question 11 is rewritten to match. `etched` is a new org slug with no collision in the index. |
| A5 unaccounted candidates | **FAIL** | Everything I listed is now parked with a source id (F0298: DreamZero-DROID, RoboBrain2.0, PhysBrain1.5, GraspMolmo, SimVLA; F0297: 12 dataset rows including the grouped AMASS and DOM/deform360/… rows; Part B: OmniWorld, DreamX-Phi). The typo is fixed (`10Kh-RealOmin-OpenData (genrobot2025)`). §1, §2 and question 1 now call the 6 datasets a floor. The "16 more" count holds if the Retargeted-AMASS repos count as one. **New problem:** the Part B parked row "DreamX-Phi … paper only (arXiv 2608.13489)" cites W0043, but the W0043 excerpt is cut off at "DreamX-Phi action-conditio". The arXiv id **2608.13489** appears nowhere in `web-log.tsv`, `fetch-log.tsv` or `raw/`. That makes it an unsourced fact of exactly the kind check 6 looks for. Fetch it (for example `rfetch.sh robotics_embodied https://export.arxiv.org/abs/2608.13489`) and cite that id, or drop the arXiv id and "paper only" and say "surfaced once in W0043, not fetched". |
| A6 cross-category duplicates / active rule | PASS | VLA-JEPA, GR00T, RynnVLA-002 and WorldVLA now sit in a separate "Cross-category duplicates" table (`spec.DW`), and §8 states the convention. Part B §2 now reads "a closed product counts when its product page is live … 19 of 21 (1 of them only by the live-page rule)", and runway-gwm is that one. |

**Equations (recomputed from `spec.py`):**
- Part A: raw = 103 (accepted src) + 71 (parked src) = **174**; unique = 60 + 54 = **114**; duplicates = **60**. 174 = 60 + 114 and 114 = 60 + 54. Balances. The 17 new parked rows add 17 signals, one each.
- Part B: raw = 40 + 25 (parked) + 5 (cross-category duplicates) = **70**; unique = 21 + 19 = **40**; duplicates = 30, which is the 26 from before, minus the 1 WorldVLA extra signal that is now a duplicate row, plus all 5 duplicate-row signals. 70 = 30 + 40 and 40 = 21 + 19. Balances.
- Grouped parked rows (Retargeted AMASS ×3, DOM/deform360/tracker-pov/MetaFold/grand_tour/trex ×6) count as one candidate each. This is acceptable, but a curator should know the unique-candidate count is conservative.

**§2 vs §6 after the status changes:** Part A: open 49 / open-weights 10 / closed 1; models open 18 / open-weights 10 / closed 1 (molmoact moved). Part B: open 12 / open-weights 7 / closed 2 (oasis to open, diamond to open-weights). Both §2s match the rows. Sub-populations still sum to 21. Orgs are unchanged (46 and 20; largest share 10.0% google and 9.5% tencent).

**Schema, dedup, ids:**
- Both rows files validate against `docs/schemas/registry.schema.json`.
- No slug, alias or artifact collides with `corpus-index.tsv`, and no artifact is duplicated across the two files.
- All 339 ids cited before §D exist in the logs. W ids all have excerpts. The only non-200 F ids are the disclosed F0263 and F0307 (404, evidence of absence) and F0086 (retried).
- Every cited id appears in §D.
- No audit-run id (F0444+) is cited by the sweep.

**Non-blocking notes from the first pass, now handled:** molmoact and diamond moved to open-weights, with the rule stated in §2. The convention that NC datasets stay `open` is stated. The rynnworld note now discloses the 4D/Teleop pairing.

**Still to fix:** A5, the unsourced arXiv id 2608.13489 on the DreamX-Phi parked row (Part B §7). Optional: add the OneWay-Noncommercial link note for GR00T-H (A2).

## Re-check 2 (main session, 2026-09-26): remaining A5 item and the A2 note

- **A5 (DreamX-Phi):** the arXiv id is gone. The parked row now reads "surfaced once in a search result (W0043); arXiv fetch did not complete (HTTP 406, F0598)". F0598 is logged as HTTP 406 and cited only as a failed-fetch disclosure, not as a fact.
- **A2 note:** the GR00T-H license cell and Part A §5 now say the `nvidia-license` label links to the NVIDIA OneWay Noncommercial License (F0096 cardData.license_link).
- Regenerated with render.py: 340 cited ids, 0 missing from the logs. Both rows files are unchanged by this fix and still validate.
