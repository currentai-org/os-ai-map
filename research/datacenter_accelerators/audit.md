# Audit: datacenter_accelerators sweep

Independent auditor, 2026-09-26. Re-fetched live from this container (curl through the proxy, ecosyste.ms,
raw.githubusercontent.com, WebSearch). I did not take any conclusion from sweep.md on trust.

| # | check | result |
|---|---|---|
| 1 | Live re-fetch of 15 claims | **PASS** |
| 2 | Unsourced facts / source supports fact | **FAIL (minor)**: 4 citations point at a source that does not hold the stated fact |
| 3 | Artifacts and homepages resolve | **PASS** |
| 4 | Schema and dedup | **PASS** |
| 5 | Counts reconcile, §2 from §6 | **FAIL**: §7 has 45 parked rows, while §1 and §8 say 44 |
| 6 | Recency and breadth | **PASS**, with notes on claims that rest on search excerpts |

## 1. Live re-fetch (PASS)

These claims come from rows across the whole §6b table: rows 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 19, 20 and 22, with one or two claims per row. All were fetched live on 2026-09-26.

| # | slug / cell | sweep says | live result | ok |
|---|---|---|---|---|
| 1 | nvidia-blackwell / license | open-gpu-kernel-modules MIT (GPL dual) | COPYING: "Except where noted otherwise ... licensed as MIT" | yes |
| 2 | nvidia-blackwell / last push | 2026-09-09 | ecosyste.ms pushed_at 2026-09-09T18:57Z, not archived | yes |
| 3 | amd-instinct-mi350 / identity | ROCm/ROCm now ROCm/legacy-rocm-build, meta-repo MIT | ungh ROCm/ROCm returns legacy-rocm-build; ecosyste.ms ROCm/ROCm 404, legacy-rocm-build lic mit, push 2026-09-22 | yes |
| 4 | amd-instinct-mi350 / SKU | 288 GB HBM3E, 8 TB/s | amd.com MI350 page, same text | yes |
| 5 | google-tpu-ironwood / SKU | 4,614 FP8 TFLOPs, 192 GiB | cloud.google.com tpu7x table: 4614 / 192 | yes |
| 6 | aws-trainium3 / GA | Trn3 UltraServers GA Dec 2025, 2.52 PFLOPs FP8, 144 chips | aws whats-new: "announces the general availability", 2.52 PFLOPs, 144 Trainium3 chips | yes |
| 7 | intel-gaudi-3 / archived | Model-References and Gaudi-tutorials archived; push 2026-01-08 | ecosyste.ms archived=true for both, Model-References push 2026-01-08 | yes |
| 8 | cerebras-wse-3 / license + push | modelzoo apache-2.0, 2026-09-01 | apache-2.0, push 2026-09-01; cerebras.ai/chip "900,000 AI-optimized cores", 250 PF | yes |
| 9 | sambanova-sn40l / push | ai-starter-kit 2026-09-21, "other" | push 2026-09-21, lic other | yes |
| 10 | tenstorrent-blackhole / adoption + license | 1,687 stars, Apache-2.0, not archived, push 2026-09-26; p150 $1,399 | 1,687 stars, apache-2.0, archived=false, fork=false, push 2026-09-26T19:16Z; cards page $1,399 | yes |
| 11 | qualcomm-cloud-ai-100 / license + stars | BSD-3-Clear-style text, 85 stars, push 2026-09-23 | LICENSE text "Redistribution ... permitted (subject to the limitations...)"; 85 stars; push 2026-09-23 | yes |
| 12 | furiosa-rngd / license | apache-2.0 label, LICENSE 404 at HEAD, push 2026-03-27 | label apache-2.0, raw LICENSE 404, push 2026-03-27; furiosa.ai 512 TFLOPS FP8 / 180 W | yes |
| 13 | rebellions-atom / SKU | ATOM-Max 128 TFLOPS FP16 | rebellions atom-max page: 128 TFLOPS (FP16) | yes |
| 14 | d-matrix-corsair / GA | "Enters Full Production", 2026-06-09 | press release live, same title | yes |
| 15 | positron-atlas / GA | "Shipping Today" | positron.ai/atlas "Shipping Today" | yes |
| 16 | t-head-zhenwu-m890 / GA | M890 supernodes in large-scale commercial deployment | technode 2026-09-22 article, same text | yes |
| 17 | moore-threads-mtt-s5000 / license + push | torch_musa BSD-3-Clause, push 2026-09-21 | LICENSE "BSD 3-Clause License"; push 2026-09-21 | yes |
| 18 | biren-br100 / SKU | 壁砺 166M OAM | birentech.com live, "壁砺™ 166M ... OAM 模组" | yes |

I found no wrong license, no wrong owner, no archived repo reported as active, and no figure off by more than 25%. One date to note: **google-tpu-ironwood**'s GA date (2026-04-22) rests only on a search excerpt (W0002). A WebSearch today returns both an April 22, 2026 GA report and a Nov 2025 "now generally available" report (winbuzzer 2025-11-06). The row stays valid either way, but the cell should cite a vendor page or note the conflict.

## 2. Unsourced facts (FAIL, minor)

- **Id coverage:** every F/W id cited in sweep.md exists in the logs. No non-200 F row is cited for a fact; the only one used in an evidence cell is F0072 (a 404 cited to show the file is absent, which is correct). Each cited W row has an excerpt. The sha256 and byte count of all 108 raw bodies match fetch-log.tsv.
- **Spot-checks that passed** (grep of the raw bodies): F0002, F0007, F0009, F0010, F0015, F0016, F0018, F0020, F0022, F0023, F0024, F0028, F0029, F0036, F0037, F0040, F0065, F0054, F0069, F0070, F0077, F0078 (PDF: 870 TOPs, 128 GB, 576 MB, 150 W, PCIe Gen 4 x16), F0088, F0090 (submitter list includes AMD, Google, Intel, NVIDIA; MI350P "available"; Rubin "in preview"), F0095 ("7 providers"), F0098, F0102, F0104, F0107, F0108, F0111.
- **Cited source does not hold the fact:**
  1. **§7 Fractile**: "funding news, no product (F0042)". The F0042 body (fractile.ai homepage) has no funding news. The funding is in W0001. Cite W0001, or reword.
  2. **amd-instinct-mi350 / notes**: the quote "open, ROCm software-based foundation" (F0005) comes from the sentence about **MI400** Series GPUs, not MI350. It is misattributed.
  3. **§8 duplicate signals**: `cerebras-inference` cites W0011 and `sambanova-cloud` cites W0012. Neither excerpt mentions an inference API or cloud service; both are about the silicon (WSE-3/CS-4 and SN50).
  4. **huawei-ascend-950 / SKUs**: cites "(F0031, W0044)", but F0031 (the huawei.com MWC post) names only the Atlas 950 SuperPoD. It has no 950PR, 950DT or Atlas 350. W0044 alone carries the chip names. Keep W0044 and narrow F0031 to the SuperPoD.
- **Minor overstatements:**
  - **d-matrix-corsair / adoption**: "shipping in volume to hyperscalers/neoclouds (F0015)". The release says "products **to begin** shipping in volume to priority hyperscalers, neoclouds...". That is future tense.
  - **cerebras-wse-3 / display_name** "(CS-3, CS-4)": F0081 says "First CS-4 shipments begin this quarter", so CS-4 is not yet shipping. Under the sweep's own seeding rule, CS-4 is acceptable only as a same-architecture refresh; say so in the note.
- **Uncited cells:** the org GitHub/HF handle column carries no id for ibm-spyre ("IBM"), positron-atlas ("Positron"), d-matrix-corsair ("d-Matrix") and rebellions-atom ("rebellions"). For rebellions this matters: the only repo probe for it (F0057, rebellions-sw/rbln-model-zoo) returned 404.

## 3. Artifacts resolve (PASS)

- **github** (2 rows): tenstorrent/tt-metal (archived=false, fork=false, push 2026-09-26) and quic/cloud-ai-sdk (archived=false, push 2026-09-23). Both resolve on ecosyste.ms. There are no HF or PyPI artifacts.
- **Homepages** (live curl, 22 of 22): 21 return 200. intel-gaudi-3's intel.com URL returns **403 to curl**, which matches the sweep's F0012 and was covered by WebFetch W0026. That is an access limit, not a dead link. www.hiascend.com, which had no response in the sweep (F0099), returns 200 today.

## 4. Schema and dedup (PASS)

- `jsonschema.validate(rows.yaml, registry.schema.json)` → `ok`. 22 rows, 22 unique slugs.
- No slug in rows.yaml appears in corpus-index.tsv column 3. Neither github artifact (tenstorrent/tt-metal, quic/cloud-ai-sdk) appears in column 6.
- The index does hold the six slugs named as duplicate signals (groq-inference, cerebras-inference, sambanova-cloud, google-cloud-tpu-inference, aws-neuron, axelera-metis-aipu). It also holds the boundary slugs cited (xla, composable-kernel, triton), and the 10 reused org slugs. The 11 new org slugs have no index rows. The sweep's claims about the index are all correct.

## 5. Counts (FAIL)

- **§7 has 45 table rows. §1 ("another 44 surveyed candidates are parked") and §8 (parked = 44) say 44.** With 45 parked, unique = 22 + 45 = 67 and raw = 67 + 6 = 73, not 66 and 72. Either one §7 row should be merged (for example, NVIDIA Groq 3 LPX is described as "SKU of the Vera Rubin generation", which is itself a parked row) or §1 and §8 must be restated.
- **§2 metrics recomputed from §6 and rows.yaml** (all correct):
  - accepted: 22.
  - orgs: 21.
  - largest org: amazon-web-services 2/22 = 9.1%.
  - availability split: 15 merchant + 4 cloud-first + 1 system-bundled + 2 mixed = 22.
  - next/prior-generation parked: 24 (§7 rows 1–12 and 14–25).
  - usage instrument: 0.
  - stars: 1,687 and 85.
- **"Active in the last 12 months: 22" is soft for three rows.**
  - cambricon-mlu590: "mass shipment early 2025", the vendor site does not list MLU590 (F0098), and torch_mlu was last pushed 2025-03-15, more than 12 months ago.
  - biren-br100: mass production since Aug 2025.
  - kunlunxin-p800: the only evidence is an undated search excerpt (W0035).

  All three rest only on WebSearch excerpts. The count is defensible under the sweep's "GA/shipping" definition, but §2 should say these three are excerpt-only.

## 6. Recency and breadth (PASS, with notes)

- **Timestamps:** all 111 fetch-log rows and all 50 web-log rows are dated 2026-09-26 (20:00–20:09Z). The raw file mtimes match.
- **Candidates the sweep found that the brief's leads did not name:**
  - Accepted rows: Positron Atlas, IBM Spyre, Kunlunxin P800, T-Head Zhenwu M890, MetaX C500.
  - Parked: T-Head Zhenwu V900, MetaX C600, NVIDIA Groq 3 LPX, Intel Crescent Island and Jaguar Shores, Qualcomm AI200/AI250, Rebellions Rebel100, OpenAI Jalapeño, Enflame, Hygon DCU BW1000, Fractile, Taalas HC1, Untether AI speedAI240, NextSilicon Maverick-2, VSORA Jotunn 8, Axelera Europa, Lumai Iris Nova and Neurophos OPU.
- **Claims that read like recall (no id attached):**
  - §4: "Helios' 72 GPUs". The fact is true and is in the F0003/F0005 bodies, but it is uncited.
  - §9 Q8: "cloud counts exist for about 5 of 22". No derivation or id.
  - §9 Q2: "edge boards publish design files, and no datacenter part does". Unsourced assertion.
  - §6b tenstorrent-blackhole: Galaxy Blackhole "from $160,000" (F0022, verified). W0007's excerpt says "$110,000". The vendor page wins, but the conflict is not noted.
- **Weak evidence.** These rest only on search excerpts, and the sweep flags most of them:
  - google-tpu-ironwood: GA date (see §1 above).
  - google-tpu-ironwood: select-customer sales (W0041; the vendor source F0097 was 403).
  - huawei-ascend-950: mass production. Corroborated today by WebSearch (Reuters/invezz: mass production from April 2026).
  - cambricon-mlu590, kunlunxin-p800 and biren-br100: all facts.

## Items to fix

1. §1/§7/§8: reconcile 44 vs 45 parked and restate both equations.
2. Fractile citation (F0042 → W0001).
3. MI350 row "open, ROCm software-based foundation" is an MI400 quote.
4. §8 duplicate-signal citations W0011 and W0012 do not mention cerebras-inference or sambanova-cloud.
5. Huawei SKU cell: F0031 does not name 950PR, 950DT or Atlas 350.
6. Soften "shipping in volume" (d-Matrix) and note that CS-4 shipments begin this quarter (Cerebras).
7. Cite or drop: Helios 72 (§4), "5 of 22" (§9 Q8), and the org-handle cells for IBM, Positron, d-Matrix and Rebellions.
8. Optional: note the Ironwood GA-date conflict, and that Cambricon, Biren and Kunlunxin activity is excerpt-only.

## Re-check of fixed items (2026-09-26)

Fresh auditor. Scope: only the items this audit raised above. Checked against sweep.md and rows.yaml as they
stand now, the raw bodies (grep of `raw/Fnnnn.body`), web-log.tsv excerpts and research/corpus-index.tsv.
No live re-fetch.

| # | item | result | evidence |
|---|---|---|---|
| 1 | Parked count, §1 / §7 / §8 | **PASS** | §7 now has 45 table rows. §1 says "another 45", and §8 says parked = 45, unique = 67, raw = 73 (67 + 6). Both equations hold. |
| 2 | Fractile citation | **PASS** | §7 cites W0001 for the funding ("Fractile $220M Series B"), and F0042 for the site. Correction to the original finding: the F0042 body *does* carry the funding headline ("$220M to build the next generation of inference hardware"), and it also has "News" and "Join us" but no product. The current wording is accurate either way. |
| 3 | amd-instinct-mi350 note | **PASS** | The MI400 quote is gone. The note now quotes "an open low and no-cost software ecosystem" (F0001), which appears verbatim in the MI350 page body, in the MI350 context. |
| 4 | §8 duplicate-signal sourcing | **PASS** | W0011 and W0012 are no longer cited in §8. The four inference APIs rest on corpus-index.tsv, where all four slugs are present. aws-neuron rests on F0008, whose body links /ai/machine-learning/neuron/. axelera-metis-aipu rests on F0109, whose body names "Metis®". All six slugs are in the index. |
| 5 | huawei-ascend-950 SKU cell | **PASS** | The cell now reads "Ascend 950PR, 950DT, Atlas 350 card (W0044); Atlas 950 SuperPoD (F0031)". The W0044 excerpt names all three chips and cards. F0031 has "SuperPoD" and no 950PR, 950DT or Atlas 350. |
| 6a | d-Matrix overstatement | **PASS** | The adoption cell now quotes "products to begin shipping in volume to priority hyperscalers, neoclouds, and frontier labs" (F0015), verbatim in the body. |
| 6b | Cerebras CS-4 | **PASS** | The rows.yaml display_name is now "Cerebras WSE-3" (the CS-3/CS-4 parenthetical was dropped). The note says CS-4 first shipments "begin this quarter" (F0081, verbatim) and that "the GA system today is CS-3". |
| 7 | google-tpu-ironwood GA date | **PASS** | The cell says the date rests on a search excerpt only (W0002), names the earlier Nov 2025 report, and says to "treat the date as unverified". That satisfies the "or note the conflict" option. No vendor page was added. |
| 8 | §4 Helios 72 GPUs | **PASS** | It now cites F0003. The F0003 body has "AMD Helios™ rackscale solution powered by 72 AMD Instinct MI455X GPUs". |
| 9 | §9 Q8 cloud count | **PASS** (count) / **FAIL** (new sentence) | The "5 of 22" now lists five rows with ids. Each checks out: F0095 "Compare 7 Providers", F0002 Compute Engine, F0010 Trn3 GA, F0007 "EC2 Inf2 instances", W0026 "IBM Cloud, Denvr Dataworks". **But the rewritten sentence adds "the new accelerators it lists are AMD and NVIDIA parts only (F0090)".** That is wrong. F0090 says "five new processors or accelerators: AMD Ryzen AI Max+ 395, AMD Instinct MI350P, and Intel Arc Pro B70 are all available, and NVIDIA Rubin and NVIDIA Vera Rubin NVL72 is in preview". Intel's part is one of them. Fix: say "AMD, Intel and NVIDIA parts", or drop the clause. |
| 10 | §9 Q2 edge design files | **PASS** | It now cites `sources/categories/edge_hardware.yaml`, whose strapline reads "Open at the board, closed at the silicon. The SBC ecosystem ships schematics", with design-file language on lines 19–49. It is also scoped to "no datacenter part in §6b", which matches the evidence table. |
| 11 | Org-handle cells (IBM, Positron, d-Matrix, Rebellions) | **PASS** | All four now read "none found" rather than an uncited handle. For rebellions this matches F0057 (rebellions-sw/rbln-model-zoo, 404). |
| 12 | Galaxy Blackhole price conflict | **PASS** | The cell reads "from $160,000 on the vendor page (F0022; search excerpt W0007 says $110,000, and the vendor page wins)". F0022 has "Starting at $160,000", and W0007 has "starting at $110,000". |
| 13 | Schema validation | **PASS** | `jsonschema.validate(rows.yaml, registry.schema.json)` → `ok`. 22 rows. |

**Overall: PASS WITH ONE NEW MINOR FAIL.** All 12 original items are fixed, and the schema validates.
One new inaccuracy came in with the §9 Q8 rewrite: MLPerf v6.1's new accelerators include Intel Arc Pro B70 (F0090),
so they are not "AMD and NVIDIA parts only". Fix that clause before merge. Nothing else blocks.

### Author fix after re-check (2026-09-26)

- §9 Q8 MLPerf clause corrected to "AMD, Intel (Arc Pro B70) and NVIDIA parts" per F0090 (grep confirms "Intel Arc Pro B70" in raw/F0090.body). This was the only open item, so the audit is now PASS on all six checks.
