# Datacenter accelerators sweep — 2026-09-26

Brief 8, issue #599, proposed slug `datacenter_accelerators`. Every fact below carries a fetch
id: `Fnnnn` rows are in `fetch-log.tsv` (bodies under `raw/`), `Wnnnn` rows are WebSearch or
WebFetch calls in `web-log.tsv`. A `W` id that points at a WebSearch is a search-result
excerpt, which is weaker than a vendor page; the evidence table says where a fact rests only on
one.

**Declared up front (coverage rules, not legitimacy thresholds):**

- **Seeding rule.** One row per silicon generation (see §9 Q1). The seed carries the generation
  each vendor line had *generally available or shipping* on 2026-09-26. Announced, sampling
  or "preview" generations and superseded generations of the same line are parked with the
  reason `SKU of X` (next or prior generation), not rejected: a curator can promote any of
  them by the same rule later.
- **Retrieval.** Discovery was by WebSearch (vendor names from the brief, "2026" launch
  searches, awesome-lists, MLPerf v6.0/v6.1 submitter lists, regional sweeps for China, Korea
  and Europe). No numeric cutoff was applied. Coverage limit: Chinese vendors' own sites were
  thin or unreachable (Enflame 403, Hygon empty, Cambricon lists only legacy parts), so several
  Chinese generations rest on search excerpts rather than vendor pages.

## 1. Verdict

**GO-WITH-CHANGES.** Supply is not the problem: 22 generally-available generations from 21
independent organizations survive the litmus, the largest vendor holds 9% of the seed, and
another 45 surveyed candidates are parked with reasons (mostly next/prior generations and
pre-product startups). The changes are four. (1) Make it a **sibling category** in the
existing Infrastructure → Hardware group next to `edge_hardware`, not a rename. The shared
`hardware` ladder already has the `form_factor: chipset` rung and the datasheet/availability
questions this set needs. (2) **Identity is the generation**, seeded at the current GA
generation per line. (3) **Adoption will abstain for every row.** There is no download
channel. The only citable signals (cloud availability, MLPerf participation, disclosed
shipments) cover under half the set and are not comparable. The category should publish with
weights that tolerate that, the way ADR-005's null fallback expects. (4) **ADR-005 needs one
ruling here** (§9 Q4). The shared hardware ladder's `documented` rung (public datasheet +
buyable) means buyable merchant silicon with public specs is likely *not* in ADR-005's
`openness.score <= 1` population. Cloud-only or captive silicon (Trainium, Inferentia, and
TPU until April 2026) likely is. So the best-in-class test bites on only a handful of rows.

## 2. Fit metrics (computed from section 6)

- accepted candidates: **22** (open: 0, open-weights: 0, source-available: 0, closed: 22).
  Every row is closed *silicon*. The software stacks differ: Tenstorrent's kernel/compiler
  stack is Apache-2.0 (F0069) with a GPL-2.0 kernel driver (F0051), Qualcomm's SDK repo is
  BSD-3-Clause-Clear-style text (F0070), and Moore Threads' PyTorch plugin is BSD-3-Clause
  (F0068). See §5.
- independent organizations: **21**. Largest org's share: **9.1%** (amazon-web-services,
  2 of 22: Trainium3 and Inferentia2).
- candidates active in the last 12 months: **22**. For hardware, "active" means generally
  available or shipping as of this sweep; each row's evidence cell has the dated source.
- candidates with a usage instrument (PyPI/npm/crates/HF downloads): **0**. Stars exist only
  for the stack repos attached to two rows: tt-metal 1,687 (F0065) and cloud-ai-sdk 85
  (F0054).
- retrieval cutoff: none numeric. The seeding rule above parked 24 next/prior-generation
  entries (listed in §7), and none of them was rejected on merit.

Split by availability model (from the evidence table): **merchant, buyable** 15
(nvidia-blackwell, amd-instinct-mi350, intel-gaudi-3, cerebras-wse-3, sambanova-sn40l,
tenstorrent-blackhole, qualcomm-cloud-ai-100, furiosa-rngd, rebellions-atom, d-matrix-corsair,
positron-atlas, huawei-ascend-950, moore-threads-mtt-s5000, metax-c500, biren-br100).
**Cloud-first** 4 (google-tpu-ironwood, which has also been sold into select customer data
centers since Q2 2026 per W0041; aws-trainium3; aws-inferentia2; t-head-zhenwu-m890).
**System-bundled** 1 (ibm-spyre, sold inside IBM Z / LinuxONE / Power). **Mixed or unclear**
2 (cambricon-mlu590, kunlunxin-p800, both sold into Chinese hyperscalers and OEM servers per
search excerpts).

## 3. Boundary

- **Definition:** physical AI training and inference accelerators (chip, card, module or rack
  system) that are sold or rented *as silicon* for datacenter deployment.
- **Litmus:** can an outside party rack it, or rent it as an instance of that silicon, as
  distinct from calling an API that happens to run on it?
- **Exclusions:**
  - Inference **APIs** fronting the silicon stay in `inference_code` (`groq-inference`,
    `cerebras-inference`, `sambanova-cloud`, `google-cloud-tpu-inference`).
  - SDKs and compilers stay where they are: `aws-neuron` in `inference_code`, `xla` and
    `composable-kernel` in `compilers`, `triton` in `ml_frameworks`.
  - Edge and embedded parts (M.2/mPCIe, SBCs, low-watt NPUs) stay in `edge_hardware`.
  - Captive silicon no outsider can rack or rent (Meta MTIA, Microsoft Maia 200, OpenAI
    Jalapeño) fails the litmus. It is parked, and §9 Q3 asks whether to admit it.
  - Open accelerator **RTL** (NVDLA, Gemmini, Vortex) is IP rather than silicon you rack, so
    it is parked. §9 Q6 asks whether to admit it.
  - Photonic *interconnect* (Lightmatter Passage) is not an accelerator.
- **Contested products** (these are flags; a sibling session owns none of them):

| product | where it is now | recommendation | reason |
|---|---|---|---|
| groq-inference | inference_code | stay | API surface. Groq's own LPU silicon is not sold separately, and the LPU name now also rides on NVIDIA's Groq 3 LPX (F0017, F0079). Hardware row parked, §7 |
| cerebras-inference | inference_code | stay | API. The silicon is the new row `cerebras-wse-3` |
| sambanova-cloud | inference_code | stay | API. Silicon is `sambanova-sn40l` |
| google-cloud-tpu-inference | inference_code | stay | API. Silicon is `google-tpu-ironwood` |
| aws-neuron | inference_code | stay | SDK. Silicon is `aws-trainium3` / `aws-inferentia2` |
| axelera-metis-aipu | edge_hardware | stay | Edge M.2/PCIe part. Axelera's newer **Europa** PCIe card is sold into Dell/Supermicro servers, "robot to rack" (W0049), and sits on the seam: parked here as boundary → edge_hardware, §9 Q5 |
| xla | compilers | stay | TPU's compiler, not silicon |
| (none) | — | — | No overlap found with the eight sibling proposals: none of them claims silicon |

## 4. Capability quantity

**Peak dense low-precision throughput per accelerator package** (FP8 where published,
otherwise FP16 or INT8, and the precision is always recorded next to the number). Memory
capacity per package is the tiebreaker. This is the quantity every vendor page in §6 leads
with. The sketch:

1. **< 0.25 PFLOPS/POPS**: Rebellions ATOM-Max, 128 TFLOPS FP16 (F0077).
2. **0.25–1**: Qualcomm Cloud AI 100 Ultra, 870 TOPS INT8 (F0078); FuriosaAI RNGD, 512 TFLOPS
   FP8 (F0023).
3. **1–4**: AWS Trainium3, 2.52 PFLOPS FP8 (F0010).
4. **4–20**: Google TPU Ironwood, 4,614 TFLOPS FP8 per chip (F0002).
5. **wafer scale**: Cerebras WSE-3 Turbo, 250 PFLOPS "AI compute" per wafer (F0024). It
   **anchors the top rung**, with a caveat: one wafer is one "package", which flatters
   Cerebras against multi-die GPUs. The fair package-level alternative is a rack or
   scale-up domain.

**Caveats (findings, not failures):** precision is not uniform, several Chinese vendors
publish no figure at all (Cambricon's site lists no MLU590, F0098), and sparsity or
"AI compute" marketing definitions differ. A rack-level alternative (the scale-up domain:
NVL72, Trn3 UltraServer's 144 chips (F0010), the 9,216-chip Ironwood pod (F0002), Helios'
72 MI455X GPUs (F0003)) orders the frontier better but is unpublished for most of the long tail. The
recommendation is per-package peak FP8 with a recorded precision, and a curator should
expect abstentions.

## 5. Scoring ladder inputs

- **Ladder:** `hardware` for every row (`sources/rubrics/hardware.yaml`). Form factor: every
  row is `chipset` in the ladder's sense *or* a card/module/system. Note that the chipset
  rung asks exactly the two questions this set can answer (`datasheets` public/brief/nda and
  buyable). New facts the ladder doesn't yet ask, which a later ladder change might want:
  **cloud-only vs buyable** (availability), **open driver/compiler stack license**, and
  **open ISA** (Tenstorrent's RISC-V cores, F0018).
- **Openness facts each candidate exposes** (per-row detail in §6b):

| fact | rows exposing it |
|---|---|
| public spec sheet or datasheet on vendor site | nvidia-blackwell (F0009), amd-instinct-mi350 (F0001), google-tpu-ironwood (F0002 spec table), aws-trainium3 (F0008), aws-inferentia2 (F0007), cerebras-wse-3 ("CS-3 and WSE-3 Datasheet", F0024), sambanova-sn40l ("SN50 and SN40 RDU Specifications", datasheet download, F0020), tenstorrent-blackhole (F0018), qualcomm-cloud-ai-100 (product brief PDF, F0078), furiosa-rngd (F0023), rebellions-atom (F0077), moore-threads-mtt-s5000 (F0036), ibm-spyre (F0111) |
| spec not published by the vendor (search excerpts only) | cambricon-mlu590 (vendor lists only MLU370/270/220, F0098), kunlunxin-p800 (vendor product list shows RG800/R200, F0033), t-head-zhenwu-m890 (name only, F0104), biren-br100 (module names only, F0102), huawei-ascend-950 (names only, W0044), metax-c500 (names only, F0029), d-matrix-corsair and positron-atlas (marketing specs only, F0103, F0016) |
| buyable by an outside party | merchant rows in §2. Google TPU "select customers" since Q2 2026 (W0041) |
| cloud-only / captive | aws-trainium3, aws-inferentia2 (F0008, F0007); google-tpu-ironwood mostly (F0002, W0041) |
| open-source stack | tenstorrent (tt-metal Apache-2.0 F0069, tt-forge apache-2.0 label F0055, tt-kmd GPL-2.0 label F0051); NVIDIA kernel modules MIT/GPL dual (F0067); AMD ROCm meta-repo MIT (F0074); Huawei CANN repositories hosted on AtomGit/GitCode (F0100), reported fully open-sourced Dec 2025 (W0008) |
| partial / plugin-only open code | Qualcomm cloud-ai-sdk (F0070); Moore Threads torch_musa BSD-3 (F0068); AWS NKI samples MIT-0 (F0050); Cerebras modelzoo apache-2.0 label (F0056); Furiosa furiosa-sdk apache-2.0 label (F0063, no LICENSE file at HEAD, F0072); SambaNova ai-starter-kit "other" (F0061) |

- **Every license string met** (all on stack repos, none on silicon):
  - Apache-2.0: tenstorrent/tt-metal (text read, F0069); tenstorrent/tt-forge (label,
    F0055); Cerebras/modelzoo (label, F0056); furiosa-ai/furiosa-sdk (label only, and the
    LICENSE file is 404 at HEAD, F0063/F0072; **flag**); vortexgpgpu/vortex (label, F0053,
    parked row).
  - GPL-2.0: tenstorrent/tt-kmd (label, F0051).
  - MIT: ROCm meta-repo (text, F0074). **Flag:** `ROCm/ROCm` now redirects to
    `ROCm/legacy-rocm-build` (F0096), so the repo is not a stable artifact for AMD.
  - MIT (dual with GPL-2.0 per file): NVIDIA/open-gpu-kernel-modules, "Except where noted
    otherwise ... licensed as MIT" (F0067). GitHub label "other" (F0052).
  - BSD-3-Clause-Clear-style (redistribution permitted, "NO EXPRESS OR IMPLIED LICENSES TO
    ANY PARTY'S PATENT RIGHTS"): quic/cloud-ai-sdk (text, F0070). The label says "other"
    (F0054). **Flag:** custom-ish, place in tier.
  - BSD-3-Clause: MooreThreads/torch_musa (text, F0068). Label "other" (F0060).
  - MIT-0: aws-neuron/nki-samples (label, F0050).
  - CC-BY-SA-4.0 (documentation): aws-neuron/aws-neuron-sdk LICENSE-DOCUMENTATION (F0073).
    Repo label "other" (F0064).
  - "other" label, text not read: ROCm/amdgpu (F0048), Cambricon/torch_mlu (F0058),
    sambanova/ai-starter-kit (F0061), graphcore/poplibs (F0062), nvdla/hw (F0059),
    ucb-bar/gemmini (F0049).

## 6. Accepted candidates

### 6a. Registry rows

The paste-ready file is `rows.yaml` in this directory. It validates against
`docs/schemas/registry.schema.json` (22 rows). Artifacts: `github` appears on two rows only,
where the repo is the vendor's own driver/compiler stack for that chip, following the
edge_hardware precedent (`hailo-8` → `hailo-ai/hailort`). Every other row is
`homepage`-only, because the stack either has no public repo or spans several generations
and would duplicate across rows.

```yaml
category: datacenter_accelerators
products:
  - {slug: nvidia-blackwell, display_name: "NVIDIA Blackwell (B200/B300, GB200/GB300 NVL72)", type: hardware, org: nvidia, homepage: "https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/"}
  - {slug: amd-instinct-mi350, display_name: AMD Instinct MI350 Series, type: hardware, org: amd, homepage: "https://www.amd.com/en/products/accelerators/instinct/mi350.html"}
  - {slug: google-tpu-ironwood, display_name: Google TPU Ironwood (TPU7x), type: hardware, org: google, homepage: "https://cloud.google.com/tpu/docs/tpu7x"}
  - {slug: aws-trainium3, display_name: AWS Trainium3, type: hardware, org: amazon-web-services, homepage: "https://aws.amazon.com/ai/machine-learning/trainium/"}
  - {slug: aws-inferentia2, display_name: AWS Inferentia2, type: hardware, org: amazon-web-services, homepage: "https://aws.amazon.com/ai/machine-learning/inferentia/"}
  - {slug: intel-gaudi-3, display_name: Intel Gaudi 3, type: hardware, org: intel, homepage: "https://www.intel.com/content/www/us/en/products/details/processors/ai-accelerators/gaudi.html"}
  - {slug: cerebras-wse-3, display_name: Cerebras WSE-3, type: hardware, org: cerebras-systems, homepage: "https://www.cerebras.ai/chip"}
  - {slug: sambanova-sn40l, display_name: SambaNova SN40L RDU, type: hardware, org: sambanova-systems, homepage: "https://sambanova.ai/products/sn40l-rdu-ai-chip"}
  - {slug: tenstorrent-blackhole, display_name: Tenstorrent Blackhole, type: hardware, org: tenstorrent, github: tenstorrent/tt-metal, homepage: "https://tenstorrent.com/en/hardware/blackhole"}
  - {slug: qualcomm-cloud-ai-100, display_name: Qualcomm Cloud AI 100 (incl. Ultra), type: hardware, org: qualcomm, github: quic/cloud-ai-sdk, homepage: "https://www.qualcomm.com/artificial-intelligence/data-center/cloud-ai-100-ultra"}
  - {slug: ibm-spyre, display_name: IBM Spyre Accelerator, type: hardware, org: ibm, homepage: "https://newsroom.ibm.com/2025-10-07-ibm-introduces-the-spyre-accelerator-for-commercial-availability"}
  - {slug: furiosa-rngd, display_name: FuriosaAI RNGD, type: hardware, org: furiosaai, homepage: "https://furiosa.ai/rngd"}
  - {slug: rebellions-atom, display_name: Rebellions ATOM (ATOM-Max), type: hardware, org: rebellions, homepage: "https://rebellions.ai/rebellions-product/atom-max/"}
  - {slug: d-matrix-corsair, display_name: d-Matrix Corsair, type: hardware, org: d-matrix, homepage: "https://www.d-matrix.ai/"}
  - {slug: positron-atlas, display_name: Positron Atlas (Archer accelerator), type: hardware, org: positron, homepage: "https://www.positron.ai/atlas"}
  - {slug: huawei-ascend-950, display_name: Huawei Ascend 950 (950PR/950DT), type: hardware, org: huawei, homepage: "https://www.hiascend.com/"}
  - {slug: cambricon-mlu590, display_name: Cambricon Siyuan 590 (MLU590), type: hardware, org: cambricon, homepage: "https://www.cambricon.com/"}
  - {slug: kunlunxin-p800, display_name: Kunlunxin P800, type: hardware, org: kunlunxin, homepage: "https://www.kunlunxin.com/"}
  - {slug: t-head-zhenwu-m890, display_name: T-Head Zhenwu M890, type: hardware, org: t-head, homepage: "https://www.t-head.cn/"}
  - {slug: moore-threads-mtt-s5000, display_name: Moore Threads MTT S5000, type: hardware, org: moore-threads, homepage: "https://en.mthreads.com/product/S5000"}
  - {slug: metax-c500, display_name: MetaX C500 Series, type: hardware, org: metax, homepage: "https://www.metax-tech.com/en/goods/prod.html?cid=107&id=68"}
  - {slug: biren-br100, display_name: "Biren BR100 Series (BR106/BR166)", type: hardware, org: biren, homepage: "https://www.birentech.com/"}
```

Org slugs reused from the index: nvidia, amd, google, amazon-web-services, intel,
cerebras-systems (the org of `cerebras-inference`), sambanova-systems, qualcomm, ibm, huawei.
New org slugs: tenstorrent, furiosaai, rebellions, d-matrix, positron, cambricon, kunlunxin,
t-head, moore-threads, metax, biren. Kunlunxin (Baidu's chip affiliate) and T-Head (Alibaba's
chip subsidiary, F0037) get their own slugs rather than `baidu`/`alibaba-cloud`. That choice
is §9 Q7.

### 6b. Evidence table

"Open status" is for the silicon. The stack license is in the licenses column.
"archived/fork" and "last push" apply only to an attached repo. "Last release" means the
generation's GA/shipping date. Adoption cells record what is citable. Most will abstain.

| slug | open status | license(s) + URL | archived/fork | last push | last release (GA/shipping) | adoption signal + value + URL | member checkpoints/SKUs | org GitHub/HF handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| nvidia-blackwell | closed | silicon: none. Open kernel modules MIT/GPL-2.0 dual, github.com/NVIDIA/open-gpu-kernel-modules (F0067). CUDA license not fetched | n/a (no repo attached) | kernel modules 2026-09-09 (F0052) | AWS P6-B300 GA Nov 2025 (F0094). GB300 NVL72 on vendor page (F0009) | GB300 rentable from 7 cloud providers (F0095); NVIDIA an MLPerf Inference v6.1 submitter (F0090) | B200, B300 (Blackwell Ultra), GB200 NVL72, GB300 NVL72 "72 NVIDIA Blackwell Ultra GPUs, 36 NVIDIA Grace CPUs" (F0009), HGX (F0011) | NVIDIA | Blackwell + Blackwell Ultra collapsed as one architecture generation. §9 Q1 |
| amd-instinct-mi350 | closed | ROCm meta-repo MIT (F0074); repo renamed legacy-rocm-build (F0096) | n/a | ROCm 2026-09-22 (F0096) | MI350P "available" in MLPerf v6.1 (F0090) | MI350P new in MLPerf Inference v6.1 (F0090) | MI350X, MI355X, MI350P PCIe; 288 GB HBM3E, 8 TB/s (F0001) | ROCm | vendor cites "an open low and no-cost software ecosystem" (F0001) |
| google-tpu-ironwood | closed | none (libtpu license not fetched) | n/a | n/a | available via GKE/Compute Engine (F0002); GA at Cloud Next 2026-04-22 per search excerpt only (W0002). The auditor found an earlier (Nov 2025) GA report, not fetched here, so treat the date as unverified | Rented via GKE/Compute Engine (F0002); sold to "a select group of customers in their own data centers", first revenue Q2 2026 (W0041); Google an MLPerf v6.1 submitter (F0090) | TPU7x; 4,614 FP8 TFLOPs, 192 GiB HBM per chip; 9,216-chip pod (F0002) | google | Prior gens v6e/v5p/v5e parked (F0006). Next gen TPU 8t/8i parked (W0002) |
| aws-trainium3 | closed | Neuron SDK docs CC-BY-SA-4.0 (F0073); NKI samples MIT-0 (F0050) | n/a | aws-neuron-sdk 2026-09-16 (F0064) | Trn3 UltraServers GA Dec 2025 (F0010) | EC2 Trn3 UltraServers in EC2 UltraClusters 3.0 (F0010) | Trainium3 2.52 PFLOPs FP8, 144 GB HBM3e; Trn3 UltraServer 144 chips (F0010) | aws-neuron | Cloud-only (F0008). Trainium2 prior (F0010), Trainium4 future (W0025) |
| aws-inferentia2 | closed | as Trainium (same Neuron stack) | n/a | n/a | Inf2 instances current on vendor page (F0007) | EC2 Inf2 instances, "up to 12 Inferentia2 chips" per instance (F0007) | Inferentia2, 2 NeuronCores per chip (F0007) | aws-neuron | No Inferentia3 announced per search excerpt (W0025). §9 Q4 (long tail?) |
| intel-gaudi-3 | closed | stack repos: HabanaAI/Model-References archived (F0071), HabanaAI/Gaudi-tutorials archived (F0066) | n/a | Model-References 2026-01-08 (F0071) | shipping via OEMs Dell/HPE/Supermicro and IBM Cloud (W0026) | cloud: IBM Cloud, Denvr Dataworks (W0026) | HL-338 PCIe, HL-325L mezzanine, HLB-325 UBB (W0026) | HabanaAI | Archived reference repos are a churn signal. Gaudi 2 prior, Crescent Island / Jaguar Shores future (W0013) |
| cerebras-wse-3 | closed | Cerebras/modelzoo apache-2.0 label (F0056) | n/a | modelzoo 2026-09-01 (F0056) | CS-4 (WSE-3 Turbo) unveiled Aug 2026 (W0011); WSE-3T on vendor page (F0024) | on-prem: "Bring the fastest AI to your data center" (F0081); API `cerebras-inference` already mapped | WSE-3, WSE-3 Turbo (4T transistors, 900,000 cores, 250 PF); systems CS-3, CS-4 = 3× WSE-3T (F0024) | Cerebras | Public "CS-3 and WSE-3 Datasheet" (F0024). No WSE-4 (W0011). CS-4 first shipments "begin this quarter" (F0081), so the GA system today is CS-3 |
| sambanova-sn40l | closed | sambanova/ai-starter-kit "other" (F0061) | n/a | 2026-09-21 (F0061) | on current product page's "SN50 and SN40 RDU Specifications" (F0020, W0040) | API `sambanova-cloud` already mapped. SambaRack sold (F0020) | SN40(L); SambaRack; three-tier SRAM/HBM/DDR memory (F0020) | sambanova | SN50 (5th gen) ships H2 2026 (F0028), parked as next gen. Swap in SN50 once shipping is confirmed |
| tenstorrent-blackhole | closed silicon, **open stack** | tt-metal Apache-2.0 (text, F0069); tt-kmd GPL-2.0 label (F0051) | tt-metal not archived, not fork (F0065) | tt-metal 2026-09-26 (F0065) | cards on sale, "Buy Now" (F0018) | tt-metal 1,687 stars (F0065). Prices: p100a $999, p150a/b $1,399 (F0018), Galaxy Blackhole from $160,000 on the vendor page (F0022; search excerpt W0007 says $110,000, and the vendor page wins) | p100a, p150a, p150b (120 Tensix cores, 28/32 GB GDDR6, "16 big RISC-V cores"), Galaxy Blackhole (F0018, F0022) | tenstorrent | The one open-stack datacenter part. Wormhole prior gen still sold, parked (F0022) |
| qualcomm-cloud-ai-100 | closed | quic/cloud-ai-sdk BSD-3-Clause-Clear-style text (F0070) | not archived (F0054) | 2026-09-23 (F0054) | product page current (F0092) | none citable | Cloud AI 100 Ultra: 870 TOPS INT8, 128 GB LPDDR4x, 576 MB SRAM, 150 W, PCIe Gen4 x16 (F0078) | quic | AI200 (2026) / AI250 (2027) parked as next gen (W0010) |
| ibm-spyre | closed | none fetched | n/a | n/a | GA 2025-10-28 on z17/LinuxONE 5, early Dec 2025 on Power11 (F0111) | sold inside IBM systems (F0111) | 32-core SoC, 25.6B transistors, 5 nm (F0111); PCIe card (W0050) | none found | Not in the brief: found via awesome-list (W0045). System-bundled only. §9 Q3 |
| furiosa-rngd | closed | furiosa-sdk apache-2.0 label (F0063); LICENSE file 404 at HEAD (F0072) | not archived (F0063) | 2026-03-27 (F0063) | shipping as a standalone PCIe card or turnkey server (W0017) | none citable | RNGD PCIe; NXT RNGD Server; 512 TFLOPS FP8, 48 GB HBM3, 180 W (F0023) | furiosa-ai | SDK repo quiet since March. The current SDK may live elsewhere (not fetched) |
| rebellions-atom | closed | SDK docs at docs.rbln.ai (W0028); license not fetched | n/a | n/a | ATOM-Max servers in commercial use at SK Telecom (W0030) | SK Telecom: ~14M AI requests/day on ATOM-Max servers (W0030) | ATOM, ATOM-Max: 128 TFLOPS FP16, 64 GB GDDR6, PCIe Gen5 x16 (F0077) | none found | Rebel100 (HBM3E 144 GB, F0088) ships H2 2026, parked |
| d-matrix-corsair | closed | Aviator software (F0103); license not fetched | n/a | n/a | "Enters Full Production", 2026-06-09 (F0015) | "products to begin shipping in volume to priority hyperscalers, neoclouds, and frontier labs" (F0015) | Corsair PCIe card; rack scale (F0103) | none found | Raptor next gen parked (W0015) |
| positron-atlas | closed | none | n/a | n/a | "Shipping Today" (F0016) | none citable | Atlas server = 8× Positron Archer Transformer Accelerators (F0016) | none found | Row pitched at the system because Archer is only sold inside Atlas (F0016). Asimov/Titan parked (W0022). Whether Archer is custom ASIC or FPGA-based was not fetched |
| huawei-ascend-950 | closed | CANN repos on AtomGit (F0100); open-sourcing reported (W0008); license not fetched | n/a | n/a | 950PR mass production from April 2026 (W0031); 950PR/950DT and Atlas 350 card named on vendor site (W0044) | none citable beyond mass-production start (W0031, search excerpt) | Ascend 950PR, 950DT, Atlas 350 card (W0044); Atlas 950 SuperPoD (F0031) | Ascend (AtomGit) | Atlas 950 SuperPoD (950DT) Q4 2026 (W0031). 910C prior gen parked |
| cambricon-mlu590 | closed | Cambricon/torch_mlu "other" (F0058) | not archived (F0058) | torch_mlu 2025-03-15 (F0058) | mass shipment early 2025 (W0032, search excerpt) | ByteDance largest customer (W0032, search excerpt) | MLU590, 80 GB HBM (W0032) | Cambricon | Vendor site lists only MLU370/270/220 (F0098). Weakest identity evidence in the seed. MLU690 parked |
| kunlunxin-p800 | closed | none fetched | n/a | n/a | 30,000-chip P800 cluster running (W0035, search excerpt) | ~40% of orders from outside customers (W0035) | P800 (3rd gen) (W0035) | none found | Vendor product list shows RG800/R200/R480-X8 (F0033), P800 naming not on the fetched page. §9 Q7 |
| t-head-zhenwu-m890 | closed | none | n/a | n/a | M890 supernodes "entered large-scale commercial deployment" (F0037) | capabilities offered through Alibaba Cloud (F0037) | Zhenwu M890; also 810E (F0104) | none | V900 unveiled 2026-09-22, parked (F0037). Cloud-first |
| moore-threads-mtt-s5000 | closed | MooreThreads/torch_musa BSD-3-Clause (text, F0068) | not archived (F0060) | torch_musa 2026-09-21 (F0060) | product page current (F0036) | none citable | MTT S5000 (PH100 chip, "PingHu" arch, native FP8; KUAE cluster) (F0036) | MooreThreads | MUSA stack. torch_musa is a plugin, not the driver |
| metax-c500 | closed | MXMACA stack named (F0029); license not fetched | n/a | n/a | C500/C500X on product page (F0029) | none citable | C500, C500X, servers, supernode (F0029) | none found | C600 on same page (F0029) but mass-production status unconfirmed (W0023), parked |
| biren-br100 | closed | none | n/a | n/a | BR166 mass production since Aug 2025 (W0036) | none citable | BR106, BR166 (壁砺 166M OAM, 166L) (F0102, W0036) | none found | HKEX listing 2026-01-02 (W0036). BR20X parked |

### 6c. Source list

Every URL behind §6 is in `fetch-log.tsv` (F0001–F0111, UTC timestamps, all 2026-09-26)
and `web-log.tsv` (W0001–W0050). Rows cited above:

- F0001 amd.com MI350 · F0002 cloud.google.com TPU7x · F0005 amd.com Instinct · F0006
  cloud.google.com TPU versions · F0007 aws Inferentia · F0008 aws Trainium · F0009 nvidia
  GB300 NVL72 · F0010 aws Trn3 GA · F0011 nvidia Blackwell · F0015 d-matrix production PR ·
  F0016 positron Atlas · F0017 groq/NVIDIA licence PR · F0018 tenstorrent cards · F0019 groq LPU ·
  F0020 sambanova RDU page · F0022 tenstorrent Galaxy · F0023 furiosa RNGD · F0024 cerebras chip ·
  F0025 microsoft Maia 200 blog · F0026 tenstorrent Blackhole · F0028 sambanova SN50 blog ·
  F0029 metax · F0031 huawei MWC 2026 · F0033 kunlunxin · F0036 mthreads S5000 · F0037 technode
  T-Head V900 · F0048–F0066, F0071, F0076 ecosyste.ms repo records · F0067–F0074 LICENSE texts ·
  F0077 rebellions ATOM-Max · F0078 qualcomm Cloud AI 100 Ultra brief · F0079 nvidia LPX ·
  F0081 cerebras system · F0082/F0090 MLCommons v6.0 / v6.1 · F0088 rebellions Rebel100 ·
  F0092 qualcomm product page · F0094 aws P6-B300 · F0095 getdeploying GB300 · F0096 ungh
  ROCm · F0098 cambricon · F0100 gitcode CANN · F0102 birentech · F0103 d-matrix · F0104
  t-head · F0105 vsora · F0107 nextsilicon · F0108 lumai · F0109 axelera · F0111 IBM Spyre PR.
- Failed or non-200 fetches (not cited for facts): F0012 intel 403 (WebFetch W0026 used
  instead), F0013/F0027/F0038/F0041/F0047/F0057/F0072 404, F0030/F0097/F0106 403,
  F0044 307, F0075/F0099/F0101 no response.

## 7. Parked candidates

All fetch dates 2026-09-26.

| name | reason | source | fetch |
|---|---|---|---|
| NVIDIA Vera Rubin (NVL72, HGX/DGX Rubin NVL8) | SKU of nvidia-blackwell line: next generation. NVIDIA says "ramping into full production" (F0004), MLPerf v6.1 lists it "in preview" (F0090) | F0004, F0090 | ✓ |
| NVIDIA Groq 3 LPX | SKU of the Vera Rubin generation (an LPU rack paired with Vera Rubin NVL72, F0079). Full production per search excerpt (W0033) | F0079, W0033 | ✓ |
| NVIDIA Hopper (H100/H200/GH200) | SKU of nvidia-blackwell line: prior generation (Hopper is GB300's comparison baseline, F0009) | F0009 | ✓ |
| AMD Instinct MI400 (MI455X, MI430X, Helios) | next generation of amd-instinct-mi350. AMD page still says "expected to offer" (F0005). Shipments reported Q3 2026 (W0004). Swap in when GA | F0003, F0005, W0004 | ✓ |
| AMD Instinct MI300 (MI300X/MI325X) | prior generation of amd-instinct-mi350 (F0005 lists MI300 Series) | F0005 | ✓ |
| Google TPU 8t / 8i | next generation of google-tpu-ironwood, previewed April 2026 (W0002) | W0002 | ✓ |
| Google TPU v6e / v5p / v5e | prior generations of google-tpu-ironwood (F0006) | F0006 | ✓ |
| AWS Trainium2 | prior generation of aws-trainium3 (F0010) | F0010 | ✓ |
| AWS Trainium4 | next generation of aws-trainium3, in development (W0025) | W0025 | ✓ |
| Intel Gaudi 2 | prior generation of intel-gaudi-3 (W0026) | W0026 | ✓ |
| Intel Crescent Island | next line. Customer samples H2 2026 (W0013) | W0013 | ✓ |
| Intel Jaguar Shores | next line. 2027 (W0013) | W0013 | ✓ |
| Groq LPU (GroqChip, Groq's own) | identity unclear. Groq now positions as "neocloud" whose API is mapped as `groq-inference`. Its tech is licensed to NVIDIA (F0017), and no separately sold Groq hardware SKU was found (F0019 shows rack specs only) | F0017, F0019 | ✓ |
| SambaNova SN50 | next generation of sambanova-sn40l. "will start shipping to customers in the second half of 2026" (F0028) | F0028, W0034 | ✓ |
| Tenstorrent Wormhole (n150/n300, Galaxy Wormhole) | prior generation of tenstorrent-blackhole, still sold from $70,000 (F0022) | F0022 | ✓ |
| Huawei Ascend 910C | prior generation of huawei-ascend-950 (W0031) | W0031 | ✓ |
| Cambricon MLU690 | next generation of cambricon-mlu590, limited volume H2 2026 (W0018) | W0018 | ✓ |
| MetaX C600 | next generation of metax-c500. Listed (F0029), mass production unconfirmed (W0023) | F0029, W0023 | ✓ |
| Biren BR20X | next generation of biren-br100, planned 2026 (W0018) | W0018 | ✓ |
| T-Head Zhenwu V900 | next generation of t-head-zhenwu-m890, unveiled 2026-09-22 (F0037) | F0037 | ✓ |
| Rebellions Rebel100 / REBEL-Quad | next generation of rebellions-atom, shipping H2 2026 (W0017, W0030; spec F0088) | F0088, W0030 | ✓ |
| d-Matrix Raptor | next generation of d-matrix-corsair (W0015) | W0015 | ✓ |
| Positron Asimov / Titan | next generation of positron-atlas, 2027 (W0022) | W0022 | ✓ |
| Qualcomm AI200 | next generation of qualcomm-cloud-ai-100, "commercially available in 2026" (W0010), no shipping evidence fetched | W0010 | ✓ |
| Qualcomm AI250 | next generation, 2027 (W0010) | W0010 | ✓ |
| Etched Sohu | not yet generally available: "validating our first rack-scale product with customers" (F0040) | F0040, W0016 | ✓ |
| Microsoft Maia 200 | boundary: captive to Azure's fleet and Microsoft/OpenAI services. SDK in preview only, no rentable instance found (F0025). §9 Q3 | F0025 | ✓ |
| Meta MTIA (300/400/450/500) | boundary: captive, internal deployment only (F0014). §9 Q3 | F0014 | ✓ |
| OpenAI Jalapeño (Broadcom) | boundary: captive, and announced rather than GA (W0024) | W0024 | ✓ |
| Graphcore IPU (Bow; Izanagi) | identity unclear: products page 404 (W0039), homepage carries no product (F0035), new Izanagi chip with Ampere per search excerpt (W0020) | F0035, W0020, W0039 | ✓ |
| Enflame (L600 etc.) | identity unclear: vendor site 403 (W0037). Fourth-gen L600 known only from a search excerpt (W0023) | W0023, W0037 | ✓ |
| Hygon DCU (BW1000) | identity unclear: vendor page empty (W0038), search excerpt only (W0023) | W0023, W0038 | ✓ |
| MatX One | not yet generally available: no ship date on vendor page (F0034) | F0034 | ✓ |
| Fractile | not yet generally available: $220M Series B reported (W0001), vendor site shows hiring and news but no product (F0042) | F0042, W0001 | ✓ |
| Taalas HC1 | identity unclear: model-hardwired chip (Llama 3.1 8B), AMD acquisition announced 2026-08-06 (W0022) | W0022 | ✓ |
| Untether AI speedAI240 | unmaintained: team acquired by AMD, product support ended (W0042) | W0042 | ✓ |
| Lightmatter Passage | boundary: photonic interconnect, not an accelerator (F0039) | F0039 | ✓ |
| NextSilicon Maverick-2 | boundary: HPC-first "HPC & AI Accelerator" (F0107). §9 Q6 | F0107 | ✓ |
| VSORA Jotunn 8 | not confirmed shipping. Vendor page cites availability "Q1 or Q2" 2026 from a 2025 interview, and no current shipping statement (W0048) | F0105, W0048 | ✓ |
| Axelera Europa | boundary → edge_hardware (45 W PCIe, "robot to rack", W0049). §9 Q5 | F0109, W0049 | ✓ |
| Lumai Iris Nova | not generally available: "ready for inference evaluation" (F0108) | F0108 | ✓ |
| Neurophos OPU | not yet generally available: Series A, pre-product (W0046) | W0046 | ✓ |
| NVDLA | boundary: open accelerator RTL, not silicon you rack. nvdla/hw last push 2022-03-02 (F0059) | F0059 | ✓ |
| Gemmini | boundary: open academic accelerator RTL, ucb-bar/gemmini pushed 2026-09-25 (F0049) | F0049 | ✓ |
| Vortex GPGPU | boundary: open RISC-V GPGPU RTL, apache-2.0 label, pushed 2026-09-19 (F0053) | F0053 | ✓ |

(The "fetch" column's ✓ means every id in the source column was fetched 2026-09-26. See the
logs for the timestamp.)

## 8. Reconciled counts

- raw_signals = **73**: the 67 unique candidates below, plus 6 signals that matched the index:
  the four inference APIs the brief's scope line names as already in the index (`groq-inference`,
  `cerebras-inference`, `sambanova-cloud`, `google-cloud-tpu-inference`; confirmed in
  corpus-index.tsv), `aws-neuron` (Neuron SDK, surfaced by F0008, in the index), and
  `axelera-metis-aipu` (Metis surfaced by F0109, in the index).
- duplicate_signals = **6**
- unique_candidates = **67**
- accepted = **22**
- parked = **45**

73 = 6 + 67 ✓ · 67 = 22 + 45 ✓

## 9. Open questions for the maintainer

1. **Identity: one row per generation, or one per product line?** Options: (a) generation
   (`google-tpu-ironwood`, `aws-trainium3`), seeding only the current GA generation;
   (b) line (`google-tpu`, `aws-trainium`) with generations in the evidence. **Recommend (a).**
   It matches the preamble's hardware exception and the edge precedent (`hailo-8` and
   `hailo-10h` are separate rows), and capability is a property of a generation. Corollary
   rule to confirm: a mid-cycle refresh sharing an architecture (Blackwell → Blackwell Ultra,
   WSE-3 → WSE-3 Turbo, ATOM → ATOM-Max) collapses into one row.
2. **Sibling category or rename `edge_hardware` → "AI hardware"?** **Recommend sibling
   `datacenter_accelerators`** in the existing Infrastructure → Hardware group. The two
   sets have different capability quantities (edge: TOPS/W and runnable model size;
   datacenter: per-package FP8 and memory) and different openness stories (edge boards
   publish design files, per `sources/categories/edge_hardware.yaml`, and no datacenter part in §6b does). A merged category would put a
   Raspberry Pi and a GB300 on one axis.
3. **Admit captive or system-bundled silicon?** Maia 200 and MTIA can't be racked or rented.
   IBM Spyre can be bought only inside an IBM system. **Recommend: admit ibm-spyre (buyable
   as silicon, even if bundled) and keep Maia/MTIA/Jalapeño parked** until one is rentable
   as an instance.
4. **ADR-005 for this set.** Options: (a) keep every GA generation (22), because merchant parts
   with public datasheets likely score `documented` (3) on the hardware ladder and are then
   outside ADR-005's `openness.score <= 1` population; (b) trim to frontier comparators
   (NVIDIA, AMD, Google, AWS Trainium, Cerebras) plus open-stack or distinctive rows. **Recommend
   (a), with one check:** the cloud-only rows (aws-trainium3, aws-inferentia2, and
   google-tpu-ironwood if its select-customer sales don't count as buyable) are the likely
   ≤1 rows. Of those, Trainium3 and Ironwood are best-in-class frontier comparators. Inferentia2
   is the one long-tail candidate, and it should be dropped if the curator applies ADR-005
   strictly.
5. **Axelera Europa: here or `edge_hardware`?** **Recommend edge_hardware**, alongside
   `axelera-metis-aipu`. At 45 W and 629 TOPS (W0049) it is an edge/enterprise PCIe part.
6. **Admit HPC-first silicon (NextSilicon Maverick-2) and open accelerator RTL (NVDLA,
   Gemmini, Vortex)?** **Recommend no to both** for this category. The RTL projects are the
   map's only genuinely *open* accelerator designs, though, so it's worth recording as an
   insight: no open design reaches datacenter silicon today, and Tenstorrent's open software
   stack on closed silicon is the closest thing.
7. **Org slugs for chip subsidiaries:** `kunlunxin` and `t-head` as their own orgs, or
   folded into `baidu` / `alibaba-cloud`? **Recommend own orgs.** Both sell externally
   under their own brand (W0035, F0037), and folding them would inflate those orgs' share.
8. **Adoption instrument:** accept that adoption abstains category-wide (weights like
   `adopt: 0.2, cap: 0.8`), or build a citable proxy (count of public clouds renting the
   generation, MLPerf submission presence)? **Recommend abstain now.** MLPerf v6.1's submitters
   include AMD, Google, Intel and NVIDIA among these vendors, and the new processors it lists are
   AMD, Intel (Arc Pro B70) and NVIDIA parts, none of them the other 18 rows' silicon (F0090), and a cloud-availability fact exists for only 5 of 22 (nvidia-blackwell F0095,
   google-tpu-ironwood F0002, aws-trainium3 F0010, aws-inferentia2 F0007, intel-gaudi-3 W0026).
