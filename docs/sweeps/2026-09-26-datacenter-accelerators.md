# Datacenter accelerators seed: 2026-09-26

## Scope and boundary

This batch seeds the preliminary `datacenter_accelerators` category proposed in issue #599, as a
sibling of `edge_hardware` in Infrastructure → Hardware rather than a rename of it. The two sets
have different capability quantities (TOPS per watt and runnable model size at the edge,
per-package FP8 throughput and memory here) and different openness stories: edge boards can publish
design files, and no datacenter part in this seed does.

**Litmus:** is it a chip, board or system you can rack, or rent as an instance of that silicon, as
distinct from the API that fronts it?

The rules the sweep applied, all recorded in the category's `comments`:

- **Identity is the generation.** One row per silicon generation (`google-tpu-ironwood`,
  `aws-trainium3`), following the hardware precedent of `hailo-8` and `hailo-10h` as separate rows.
  The seed carries the generation each vendor line had generally available or shipping on the sweep
  date. Announced, sampling, preview and superseded generations are parked as SKUs of the line, not
  rejected, and can be swapped in or out by the same rule later.
- **A mid-cycle refresh sharing an architecture collapses into one row:** Blackwell and Blackwell
  Ultra, WSE-3 and WSE-3 Turbo, ATOM and ATOM-Max.
- **A system sold only as a system is pitched at the system.** Positron's Archer accelerators are
  sold only inside the Atlas server, so the row is Positron Atlas.
- **Exclusions by neighbor.** The inference APIs already on the map stay in `inference_code`
  (`groq-inference`, `cerebras-inference`, `sambanova-cloud`, `google-cloud-tpu-inference`), as does
  the Neuron SDK (`aws-neuron`). Compilers stay in `compilers` (`xla`, `composable-kernel`) and
  `triton` in `ml_frameworks`. Edge and embedded parts stay in `edge_hardware`.
- **Captive silicon is parked.** Meta MTIA, Microsoft Maia 200 and OpenAI's Broadcom part cannot be
  racked or rented by an outside party. IBM Spyre is admitted: it can be bought, though only inside
  an IBM system.

No row was scored. Each row carries identity and artifacts only, as the registry schema requires.

## Inputs swept

Discovery was by WebSearch: the vendor names in the issue's brief, "2026" launch searches,
awesome-lists, the MLPerf Inference v6.0 and v6.1 submitter lists, and regional sweeps for China,
Korea and Europe. Facts were then read from vendor pages, datasheets and press releases, repository
metadata from ecosyste.ms and ungh, and license texts from the repositories themselves.

**No retrieval cutoff.** Every surfaced candidate was decided on its merits. The coverage limit is
China: Enflame's site returned 403, Hygon's product page was empty and Cambricon's lists only legacy
parts, so several Chinese generations rest on search-result excerpts rather than vendor pages. The
accepted table marks which.

The raw fetch trail (every fact carries an F or W fetch id, with bodies and hashes) is on the
evidence branch `claude/research-datacenter_accelerators`, under `research/datacenter_accelerators/`:
`sweep.md`, `fetch-log.tsv`, `web-log.tsv`, `raw/` and a two-pass independent `audit.md`, which
passed all six checks after fixes.

## Reconciled counts

A raw signal is one input naming one candidate. The six duplicate signals are candidates already in
the corpus: the four inference APIs and `aws-neuron` in `inference_code`, and `axelera-metis-aipu` in
`edge_hardware`.

```text
raw_signals       = 73
duplicate_signals = 6
unique_candidates = 67
accepted          = 22
parked            = 45

73 = 6 + 67
67 = 22 + 45
```

22 accepted rows from 21 independent organizations; the largest, Amazon Web Services, holds 2 of 22
(9.1%). Of the 22, 15 are merchant parts an outside party can buy, 4 are cloud-first
(`google-tpu-ironwood`, which Google has also sold into select customer data centers since Q2 2026;
`aws-trainium3`; `aws-inferentia2`; `t-head-zhenwu-m890`), 1 is system-bundled (`ibm-spyre`) and 2
are mixed or unclear (`cambricon-mlu590`, `kunlunxin-p800`). No candidate collided with a head
product, a retired alias or an existing registry row (`build.validate`, 0 errors).

## Organizations and handles

Ten rows reuse existing organizations: `nvidia`, `amd`, `google`, `amazon-web-services`, `intel`,
`cerebras-systems`, `sambanova-systems`, `qualcomm`, `ibm` and `huawei`. Eleven are new, each with a
`sources/organizations/` file carrying an empty roster: `tenstorrent`, `furiosaai`, `rebellions`,
`d-matrix`, `positron`, `cambricon`, `kunlunxin`, `t-head`, `moore-threads`, `metax` and `biren`.

`kunlunxin` (Baidu's chip affiliate) and `t-head` (Alibaba's chip subsidiary) are their own
organizations rather than `baidu` and `alibaba-cloud`: both sell externally under their own brand,
and folding them in would inflate those orgs' share.

Every homepage domain a row uses is covered by a `homepage_domain` handle in
`sources/org_handles.yaml`, and both GitHub artifacts by a `github` handle. New handles: a homepage
domain for each new org; `intel.com` for `intel`; `hiascend.com` for `huawei` (the Ascend developer
portal, noted); `quic` for `qualcomm` (the Qualcomm Innovation Center account, noted); and GitHub
accounts for `tenstorrent`, `furiosa-ai`, `MooreThreads` and `Cambricon`, each confirmed on
2026-09-26 against the account's registered name on ecosyste.ms.

## Accepted candidates

"Evidence" says whether the row's generally-available status rests on a vendor page or only on a
search-result excerpt. Every primary source was fetched on 2026-09-26.

| Candidate | Slug | Org | Availability | Stack artifact | Evidence | Primary source |
|---|---|---|---|---|---|---|
| NVIDIA Blackwell (B200/B300, GB200/GB300 NVL72) | `nvidia-blackwell` | nvidia | merchant | none attached | vendor | https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/ |
| AMD Instinct MI350 Series | `amd-instinct-mi350` | amd | merchant | none attached | vendor | https://www.amd.com/en/products/accelerators/instinct/mi350.html |
| Google TPU Ironwood (TPU7x) | `google-tpu-ironwood` | google | cloud-first | none | vendor (GA date excerpt only) | https://cloud.google.com/tpu/docs/tpu7x |
| AWS Trainium3 | `aws-trainium3` | amazon-web-services | cloud-only | none | vendor | https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-ec2-trn3-ultraservers/ |
| AWS Inferentia2 | `aws-inferentia2` | amazon-web-services | cloud-only | none | vendor | https://aws.amazon.com/ai/machine-learning/inferentia/ |
| Intel Gaudi 3 | `intel-gaudi-3` | intel | merchant | none | vendor (WebFetch; curl 403) | https://www.intel.com/content/www/us/en/products/details/processors/ai-accelerators/gaudi.html |
| Cerebras WSE-3 | `cerebras-wse-3` | cerebras-systems | merchant | none attached | vendor | https://www.cerebras.ai/chip |
| SambaNova SN40L RDU | `sambanova-sn40l` | sambanova-systems | merchant | none attached | vendor | https://sambanova.ai/products/sn40l-rdu-ai-chip |
| Tenstorrent Blackhole | `tenstorrent-blackhole` | tenstorrent | merchant | `tenstorrent/tt-metal` (Apache-2.0) | vendor | https://tenstorrent.com/en/hardware/cards |
| Qualcomm Cloud AI 100 (incl. Ultra) | `qualcomm-cloud-ai-100` | qualcomm | merchant | `quic/cloud-ai-sdk` | vendor | https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/Prod-Brief-QCOM-Cloud-AI-100-Ultra.pdf |
| IBM Spyre Accelerator | `ibm-spyre` | ibm | system-bundled | none | vendor | https://newsroom.ibm.com/2025-10-07-ibm-introduces-the-spyre-accelerator-for-commercial-availability |
| FuriosaAI RNGD | `furiosa-rngd` | furiosaai | merchant | none attached | vendor | https://furiosa.ai/rngd |
| Rebellions ATOM (ATOM-Max) | `rebellions-atom` | rebellions | merchant | none | vendor (deployment excerpt only) | https://rebellions.ai/rebellions-product/atom-max/ |
| d-Matrix Corsair | `d-matrix-corsair` | d-matrix | merchant | none | vendor | https://www.d-matrix.ai/announcements/d-matrix-corsair-ai-inference-platform-enters-full-production-to-meet-customer-demand/ |
| Positron Atlas (Archer accelerator) | `positron-atlas` | positron | merchant | none | vendor | https://www.positron.ai/atlas |
| Huawei Ascend 950 (950PR/950DT) | `huawei-ascend-950` | huawei | merchant | none | excerpt (mass production) | https://www.hiascend.com/ |
| Cambricon Siyuan 590 (MLU590) | `cambricon-mlu590` | cambricon | mixed | none | excerpt only | https://www.cambricon.com/ |
| Kunlunxin P800 | `kunlunxin-p800` | kunlunxin | mixed | none | excerpt only | https://www.kunlunxin.com/ |
| T-Head Zhenwu M890 | `t-head-zhenwu-m890` | t-head | cloud-first | none | press (TechNode) | https://technode.com/2026/09/22/t-head-unveils-zhenwu-v900-ai-chip-in-alibabas-push-to-expand-its-ai-infrastructure-stack/ |
| Moore Threads MTT S5000 | `moore-threads-mtt-s5000` | moore-threads | merchant | none attached | vendor | https://en.mthreads.com/product/S5000 |
| MetaX C500 Series | `metax-c500` | metax | merchant | none | vendor (names only) | https://www.metax-tech.com/en/goods/prod.html?cid=107&id=68 |
| Biren BR100 Series (BR106/BR166) | `biren-br100` | biren | merchant | none | vendor (names) + excerpt | https://www.birentech.com/ |

"None attached" means a vendor stack repository exists but spans several generations, so attaching
it to one row would duplicate it across the line: NVIDIA's open GPU kernel modules (MIT/GPL-2.0
dual), AMD's ROCm (the `ROCm/ROCm` repository now redirects to `ROCm/legacy-rocm-build`, so it is not
a stable artifact), Cerebras' modelzoo, SambaNova's ai-starter-kit, FuriosaAI's furiosa-sdk and Moore
Threads' torch_musa (BSD-3-Clause). The two attached repositories are the vendor's own stack for
that chip, following `hailo-8` → `hailo-ai/hailort`. The row's `homepage` is the product page
where one exists; the primary source above is the page that established GA and can differ from it.

## Parked candidates

All fetched 2026-09-26.

| Candidate | Reason | Source |
|---|---|---|
| NVIDIA Vera Rubin (NVL72, HGX/DGX Rubin NVL8) | SKU of `nvidia-blackwell`'s line: next generation, "ramping into full production", "in preview" in MLPerf v6.1 | https://www.nvidia.com/en-us/data-center/technologies/rubin/ |
| NVIDIA Groq 3 LPX | SKU of the Vera Rubin generation (an LPU rack paired with Vera Rubin NVL72) | https://www.nvidia.com/en-us/data-center/lpx/ |
| NVIDIA Hopper (H100/H200/GH200) | SKU of `nvidia-blackwell`'s line: prior generation | https://www.nvidia.com/en-us/data-center/gb300-nvl72/ |
| AMD Instinct MI400 (MI455X, MI430X, Helios) | SKU of `amd-instinct-mi350`'s line: next generation, "expected to offer" on AMD's page; swap in when GA | https://www.amd.com/en/products/accelerators/instinct/mi400.html |
| AMD Instinct MI300 (MI300X/MI325X) | SKU: prior generation of `amd-instinct-mi350` | https://www.amd.com/en/products/accelerators/instinct.html |
| Google TPU 8t / 8i | SKU: next generation of `google-tpu-ironwood`, previewed April 2026 (search excerpt) | search excerpt |
| Google TPU v6e / v5p / v5e | SKU: prior generations of `google-tpu-ironwood` | https://cloud.google.com/tpu/docs/system-architecture-tpu-vm |
| AWS Trainium2 | SKU: prior generation of `aws-trainium3` | https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-ec2-trn3-ultraservers/ |
| AWS Trainium4 | SKU: next generation of `aws-trainium3`, in development (search excerpt) | search excerpt |
| Intel Gaudi 2 | SKU: prior generation of `intel-gaudi-3` | https://www.intel.com/content/www/us/en/products/details/processors/ai-accelerators/gaudi.html |
| Intel Crescent Island | next line; customer samples H2 2026 (search excerpt) | search excerpt |
| Intel Jaguar Shores | next line; 2027 (search excerpt) | search excerpt |
| Groq LPU (Groq's own) | identity unclear: Groq positions as a neocloud whose API is `groq-inference`, its technology is licensed to NVIDIA, and no separately sold Groq hardware SKU was found | https://groq.com/lpu-architecture |
| SambaNova SN50 | SKU: next generation of `sambanova-sn40l`, "will start shipping to customers in the second half of 2026" | https://sambanova.ai/blog/introducing-the-sn50-rdu-purpose-built-for-agentic-inference |
| Tenstorrent Wormhole (n150/n300, Galaxy Wormhole) | SKU: prior generation of `tenstorrent-blackhole`, still sold | https://tenstorrent.com/en/hardware/galaxy |
| Huawei Ascend 910C | SKU: prior generation of `huawei-ascend-950` (search excerpt) | search excerpt |
| Cambricon MLU690 | SKU: next generation of `cambricon-mlu590`, limited volume H2 2026 (search excerpt) | search excerpt |
| MetaX C600 | SKU: next generation of `metax-c500`; listed, mass production unconfirmed | https://www.metax-tech.com/en/goods/prod.html?cid=107&id=68 |
| Biren BR20X | SKU: next generation of `biren-br100`, planned 2026 (search excerpt) | search excerpt |
| T-Head Zhenwu V900 | SKU: next generation of `t-head-zhenwu-m890`, unveiled 2026-09-22 | https://technode.com/2026/09/22/t-head-unveils-zhenwu-v900-ai-chip-in-alibabas-push-to-expand-its-ai-infrastructure-stack/ |
| Rebellions Rebel100 / REBEL-Quad | SKU: next generation of `rebellions-atom`, shipping H2 2026 | https://www.rebellions.ai/rebellions-product/rebel100/ |
| d-Matrix Raptor | SKU: next generation of `d-matrix-corsair` (search excerpt) | search excerpt |
| Positron Asimov / Titan | SKU: next generation of `positron-atlas`, 2027 (search excerpt) | search excerpt |
| Qualcomm AI200 | SKU: next generation of `qualcomm-cloud-ai-100`, "commercially available in 2026", no shipping evidence | search excerpt |
| Qualcomm AI250 | SKU: next generation, 2027 | search excerpt |
| Etched Sohu | not yet generally available: "validating our first rack-scale product with customers" | https://www.etched.com/ |
| Microsoft Maia 200 | boundary: captive to Azure's fleet; SDK in preview, no rentable instance | https://blogs.microsoft.com/blog/2026/01/26/maia-200-the-ai-accelerator-built-for-inference/ |
| Meta MTIA (300/400/450/500) | boundary: captive, internal deployment only | https://ai.meta.com/blog/meta-mtia-scale-ai-chips-for-billions/ |
| OpenAI Jalapeño (Broadcom) | boundary: captive, and announced rather than GA (search excerpt) | search excerpt |
| Graphcore IPU (Bow; Izanagi) | identity unclear: products page 404, homepage carries no product | https://www.graphcore.ai/products |
| Enflame (L600 etc.) | identity unclear: vendor site 403, known only from a search excerpt | https://www.enflame-tech.com/ |
| Hygon DCU (BW1000) | identity unclear: vendor page empty, search excerpt only | https://www.hygon.cn/product/accelerator |
| MatX One | not yet generally available: no ship date on the vendor page | https://matx.com/ |
| Fractile | not yet generally available: funding news and hiring, no product | https://www.fractile.ai/ |
| Taalas HC1 | identity unclear: model-hardwired chip, AMD acquisition announced 2026-08-06 (search excerpt) | search excerpt |
| Untether AI speedAI240 | unmaintained: team acquired by AMD, product support ended (search excerpt) | search excerpt |
| Lightmatter Passage | boundary: photonic interconnect, not an accelerator | https://lightmatter.co/ |
| NextSilicon Maverick-2 | boundary: HPC-first "HPC & AI Accelerator" | https://www.nextsilicon.com/ |
| VSORA Jotunn 8 | not confirmed shipping: availability "Q1 or Q2" 2026 cited from a 2025 interview, no current shipping statement | https://vsora.com/ |
| Axelera Europa | boundary → `edge_hardware` (45 W PCIe, "robot to rack"); a follow-up adds it beside `axelera-metis-aipu` | https://axelera.ai/ |
| Lumai Iris Nova | not generally available: "ready for inference evaluation" | https://lumai.ai/product |
| Neurophos OPU | not yet generally available: Series A, pre-product (search excerpt) | search excerpt |
| NVDLA | boundary: open accelerator RTL, not silicon you rack; last push 2022-03-02 | https://github.com/nvdla/hw |
| Gemmini | boundary: open academic accelerator RTL | https://github.com/ucb-bar/gemmini |
| Vortex GPGPU | boundary: open RISC-V GPGPU RTL (Apache-2.0) | https://github.com/vortexgpgpu/vortex |

The exact URL, timestamp and hash behind each "source" above, and the verbatim excerpt behind each
"search excerpt", are in the evidence branch's `fetch-log.tsv` and `web-log.tsv`.

## Decisions recorded on the draft

From `research/decisions.md` on the research branch and the sweep's own recommendations:

1. **Create** as a sibling of `edge_hardware`, preliminary, after it in Infrastructure → Hardware.
2. **Identity is the generation**, with mid-cycle refreshes collapsed. All 22 GA generations stay at
   seed.
3. **Weights `adopt: 0.2, cap: 0.8`.** Adoption abstains for every row: there is no download
   channel, the hardware ladder declares no numeric bands, and cloud availability and MLPerf
   presence cover under half the seed and are not comparable.
4. **`extends: hardware`**, scored as `form_factor: chipset`. The chipset rung asks for a public
   datasheet and buyable availability, the two questions this set can answer.
5. **IBM Spyre is in**; Maia, MTIA and Jalapeño stay parked until one is rentable as an instance.
6. **Kunlunxin and T-Head are their own orgs.**
7. **HPC-first silicon and open accelerator RTL are out.** Worth recording as a finding: the only
   genuinely open accelerator designs are RTL projects, none of them reaches datacenter silicon,
   and Tenstorrent's open software stack on closed silicon is the closest thing to an open
   datacenter accelerator.

## Open items for promotion

- **Renting is not in the hardware ladder's `retail` vocabulary.** Cloud-only generations
  (Trainium3, Inferentia2, most of Ironwood's volume, T-Head's M890) can be rented as instances of
  the silicon but not bought, which is neither `open_market` nor `restricted`. Under today's ladder
  they fall off the chipset rung and are deferred. Whether rentable-as-silicon counts as `buyable`
  is a shared-rubric ruling for `sources/rubrics/hardware.yaml`, not for this category's PR.
- **ADR-005.** Merchant parts with public datasheets likely land on 3/documented, outside the
  closed-product population the principle governs; the cloud-only rows are the likely closed ones.
  Trainium3 and Ironwood are frontier comparators. Inferentia2 is the trim candidate if the
  principle is applied strictly at promotion.
- **Evidence the promotion must strengthen.** `cambricon-mlu590`, `kunlunxin-p800` and
  `biren-br100` rest on search excerpts (Cambricon's own site lists no MLU590; Kunlunxin's product
  list shows RG800/R200 rather than P800 naming). `google-tpu-ironwood`'s GA date conflicts between
  an April 2026 and a November 2025 report; the row is valid either way.
- **Swap-ins due soon.** SambaNova SN50 (H2 2026), AMD MI400 (shipments reported Q3 2026),
  Rebellions Rebel100 (H2 2026) and Cerebras CS-4 (first shipments this quarter, same WSE-3 Turbo
  generation, so no new row) should be re-checked at promotion.
- **Stack licenses to read at the source.** `furiosa-ai/furiosa-sdk` is labeled Apache-2.0 but has
  no LICENSE file at HEAD; `quic/cloud-ai-sdk` carries BSD-3-Clause-Clear-style text with an explicit
  patent disclaimer and a GitHub label of "other". These are toolchain facts, read by no rung today.
- **Capability abstentions.** Several Chinese vendors publish no throughput figure, and precision
  and sparsity conventions differ across the rest. A rack-level quantity (the scale-up domain)
  orders the frontier better but is unpublished for most of the long tail.
