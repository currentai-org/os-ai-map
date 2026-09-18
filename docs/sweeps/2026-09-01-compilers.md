# Compilers sweep — 2026-09-01

## Scope and boundary

Targeted at issue #434: `compilers` holds three populations (compiler/converter,
quantization/optimizer, kernel library), and no kernel library in the roster at the time scored
above capability 3. #434's read was that the roster, not openness filtering, was the wrong fix
for that, and that the corpus was also missing major kernel and runtime incumbents on
significance alone, independent of openness. This batch completes that incumbent set rather
than filtering on openness in either direction.

## First pass

GitHub search across ten population-representative queries ("gpu kernel library primitives",
"tensor compiler", "quantization inference toolkit", "collective communication gpu", "attention
kernel", "gemm kernel library", "model quantization gptq awq", "graph compiler neural network
mlir", "cuda sparse library", "onnx converter optimizer"), sorted by stars, top 15 per query,
plus direct lookups for the three incumbents #434 names by hand (nccl, miopen, oneMath) and the
four closed vendor primitives it names for completeness (cudnn, cublas, cufft, cutensor). No
additional star floor beyond what each query's top-15 window returned — volume at this window
was small enough to triage by hand. Result: a 16-candidate total (6 accepted + roughly 10
individually parked, ignoring roughly 85 bucket-parked), shared across the categories swept that
day (`compilers` and `storage`, and a third not covered by this document).

## Second pass

Carl's instruction after the first pass came in short of his 50-75 target: re-sweep at a lower
floor and triage every result individually rather than bucket-parking. Effective star floor
lowered from ~100 to 30, each of the original ten queries widened from top-15 to top-30, plus
five new queries covering angles the first pass missed ("sparse attention kernel", "int4 int8
quantization library", "triton kernel library", "cuda graph compiler", "onnx runtime
optimization"). Predeclared retrieval cutoff: GitHub repository search, sort by stars, star
floor 30, top 30 per query across all fifteen queries, executed 2026-09-01.

Across both passes, `compilers` ended with 21 candidate rows.

## Identity and license notes

- GitHub reports `NOASSERTION` for `nccl` and `miopen` because each carries a composite or
  vendor-header LICENSE file; both were verified open by reading the license body directly, per
  #434's own finding and the abstain rule in `sources/signal_routing.yaml`.
- `oneapi-src/oneMKL` (the "Interfaces" project #434 names) has been renamed to
  `uxlfoundation/oneMath` on GitHub — the old slug 302-redirects to the new one — so the row uses
  the canonical repository.
- cuDNN, cuBLAS, cuFFT and cuTENSOR resolve to no public repository (NVIDIA distributes them as
  binaries), so per `docs/workflows/discover-candidates.md` they are parked against #365
  (GitHub-backed storage not yet available), not emitted. `NVIDIA/cudnn-frontend` is explicitly
  **not** used as cuDNN's artifact: #434 names it as the exact hazard from the
  `tinker-cookbook/tinker` case in #431 — an open wrapper repo would let an externally-open
  project lift a closed binary's openness score.
- `rapidsai/raft` stays unresolved per the #428 ledger hold and was not re-proposed.
  `NVIDIA/cuvs`, raft's ANN successor per #428's own note, resurfaced in the second pass's
  widened cuda-sparse-library window and is parked against the same open category-fit question
  rather than resolved unilaterally here.
- Every accepted row's license was read from the LICENSE body, not GitHub's classifier: `taco`,
  `NVIDIA/cuda-tile` and `NX-AI/mlstm_kernels` all report `NOASSERTION` or a nonstandard SPDX id
  from GitHub. `taco`'s body is plain MIT; `NVIDIA/cuda-tile`'s is
  Apache-2.0-with-LLVM-exceptions (real open source, not a closed-binary wrapper — see the
  cudnn-frontend note above for the case this is *not*). `NX-AI/mlstm_kernels` ships the NXAI
  Community License Agreement, a Llama-3-style custom license with commercial-scale
  restrictions — not an open license, but the row is still emitted per this workflow's rule that
  a repository is only excluded for having no public artifact, not for the license it carries;
  its restrictive terms are a scoring-stage fact, not a discovery-stage rejection.
- `NVIDIA/tensor-ir` and `NVIDIA/cuda-tile` are two layers of the same NVIDIA MLIR toolchain
  (tensor-ir is the frontend, cuda-tile is the IR it lowers to) but are distinct repositories
  with distinct real functionality, unlike `NVIDIA/cudnn-frontend`, which stays parked.

## Parked as stale or superseded

- `intel/neural-speed` (int4/int8 quantization library query): archived (`archived: true`, last
  push 2024-08-30) — parked as superseded, not accepted.
- `uwsampl/SparseTIR` (tensor compiler query): last pushed 2023-03-31 — parked as unmaintained
  despite clearing the star floor.
- `Santosh-Gupta/SpeedTorch` (cuda sparse library query): last pushed 2020-02-21 — parked as
  unmaintained despite clearing the star floor.
- `NVIDIA/MinkowskiEngine`: last pushed 2024-03-05, over two years stale — parked unmaintained
  despite 2,956 stars from its 3D deep-learning heyday.

## Promotion triage — 2026-09-02

18 of the 21 rows were promoted to head products (see `sources/categories/compilers.yaml`'s
comments for the roster and two identity corrections: FlashQLA's org resolves to
`alibaba-cloud`, not a separate `qwen` org, and Torch-TensorRT's to `pytorch-foundation`, not a
bare `pytorch`). Three rows were rejected on the category boundary rather than parked as
unresolved, and stay in `sources/registry/compilers.yaml`:

- **`nccl` and `uccl`** are collective-communication and P2P networking libraries (GPU
  allreduce/broadcast, KV-cache and RL weight transfer over RoCE/InfiniBand). Neither lowers,
  converts, quantizes or optimizes a trained model or tensor program, and neither supplies a
  compute primitive (GEMM, convolution, attention) a compiler targets — they move data between
  accelerators, a different function than everything else on the roster, including the other
  kernel-library incumbents (`miopen`, `oneMath`) #434 asked for. No networking category exists
  yet to hold them.
- **`rocalution`** is AMD's iterative sparse-linear-system solver library (CG, GMRES-family
  Krylov methods) for general HPC and scientific-computing workloads on ROCm hardware. Unlike
  the roster's other math libraries — `oneMath` (BLAS/FFT/RNG dispatch), `onednn` and
  `arm-compute-library` (DNN primitives) — it has no primary tie to trained-model or
  tensor-program optimization; it solves linear systems for FEM/CFD-style simulation more than
  it serves AI workloads. Kept out on the same general-purpose-adjacent reasoning round 1 used
  against `redis` and `tidb`.
