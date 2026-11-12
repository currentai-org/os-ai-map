# Open accelerator designs: seed sweep, 2026-11-12

The RISC-V AI accelerator topic on the aifoundry.org list had no home on the map. Neither
hardware category admits a design nobody sells, which is why the 2026-09-26 datacenter-accelerators
sweep parked NVDLA, Gemmini and Vortex as "boundary: open accelerator RTL". This sweep seeds a
preliminary category for them. Nothing is scored. The membership test, the neighbors, and the
proposed position on the ladder, maintenance and general-purpose cores are in
`sources/categories/open_accelerator_designs.yaml`.

## How it was read

Every README and LICENSE was read from `raw.githubusercontent.com` (github.com and its API are
refused to this environment). Last-commit dates come from the Software Heritage archive (latest
visit, then snapshot, then the HEAD branch's commit), with PyPI or a CHANGELOG where the archive
had no record. arXiv IDs were matched to their papers by title. No candidate already existed in
`sources/`.

## Seed

| Row | Type | License (LICENSE body) | What it is | Last activity |
|---|---|---|---|---|
| vortex-gpgpu | hardware | Apache-2.0 | Full-stack open RISC-V GPGPU; README names machine learning as a target | commit 2026-11-09; release 3.0 on 2026-10-07 |
| gemmini | hardware | BSD-3-Clause text, UC Regents | Chisel systolic-array DNN accelerator generator, in Chipyard | commit 2025-09-01 |
| nvdla | hardware | NVIDIA Open NVDLA License and Agreement v1.0 | NVIDIA's configurable inference accelerator RTL | default branch 2018-04-19; newest branch 2019-08-12 (dormant reference) |
| coral-npu | hardware | Apache-2.0 | Google Research NPU IP for ultra-low-power SoCs | commit 2026-09-28 |
| cfu-playground | software | Apache-2.0 | Custom ML instructions for a soft RISC-V CPU on FPGA | commit 2026-02-26 |
| finn | software | BSD-3-Clause text, Xilinx/AMD | Generates dataflow FPGA accelerators for quantized networks | commit 2026-09-06 |
| hls4ml | software | Apache-2.0 | Translates trained models into HLS firmware for FPGA inference | PyPI 1.3.0 on 2026-03-20; commit 2026-11-02 |
| redmule | hardware | README states SHL-0.51 for hardware, Apache-2.0 for software; no root LICENSE file found | FP16/FP8 matrix-multiply accelerator on the PULP HWPE template | unconfirmed |
| neureka | hardware | `LICENSE.hw` SHL-0.51; README states Apache-2.0 for software | Convolution accelerator for PULP clusters, from the Siracusa SoC | unconfirmed |
| snax-cluster | hardware | Apache-2.0 | KU Leuven accelerator-centric cluster with a Chisel GEMM generator | commit 2026-09-16 |
| ztachip | hardware | Apache-2.0 | RISC-V AI accelerator for edge FPGAs and ASICs, with its own compiler | unconfirmed |

## Left out

- **General-purpose cores with no ML claim in their own documentation:** Ara, Spatz, Saturn,
  Snitch cluster, Occamy, Tenstorrent riscv-ocelot, Ventus GPGPU.
- **SoC frameworks:** Chipyard, ESP.
- **Stale or retired:** VTA (removed from Apache TVM after v0.18.0), NE16 (2022-10), Tensil
  (2022-08), OpenTPU (2017).
- **Not an accelerator:** Coyote (an FPGA shell); the AINekko ET platform (runtime, drivers and a
  simulator for the ET-SoC-1, no RTL).
- **Held back:** tiny-tpu (no license declared), VeriGPU (one maintainer, last commit 2024-11).

## Open questions for review

1. The openness ladder for designs, proposed in the category's `scoring_recipe.note`: openness reads the design license and completeness; toolchain reproducibility, hardware validation and maintenance are recorded as evidence and do not lower it.
2. Tiers for SHL-0.51, the NVDLA license, and split hardware/software licensing.
3. How a dormant reference design's maintenance status reaches the published map.
4. Whether RedMulE, NEureka and ztachip need a confirmed recency reading before promotion.
