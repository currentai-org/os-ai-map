# AIFoundry topic list against the map, 2026-11-12

A targeted check of the open source AI topics on the aifoundry.org list (agentic coding harnesses,
inference frameworks, AI compilers and kernels, bare metal and edge AI, physical AI, inference
servers, open weights training, RISC-V accelerator hardware) against the published products and the
registry. Each named project was looked up by slug, display name and repository.

## Already on the map

Pi (`pi-coding-agent`), OpenCode, GGML, llama.cpp, ZML, PyTorch, Triton, Torch-MLIR, IREE, MAX (which
carries Mojo), ExecuTorch, LiteRT-LM, LeRobot, openpi (`pi0`), NVIDIA Dynamo, OLMo, Unsloth and Bielik.

## Added as head products

| Product | Category | Openness evidence |
|---|---|---|
| `tinygrad` | `ml_frameworks` | MIT LICENSE body; no gated tier |
| `shelley` | `orchestration_agents` | Apache-2.0 LICENSE body; README says Apache, CLA for contributors |
| `docker-model-runner` | `inference_code` | Apache-2.0 LICENSE body; daemon, CLI and standalone `dmr` all in the repository |
| `ramalama` | `inference_code` | MIT LICENSE body and PyPI metadata |
| `litert` | `inference_code` | Apache-2.0 LICENSE body and PyPI classifier |

Docker Model Runner and RamaLama go to `inference_code` rather than `deployment` beside Ollama:
`deployment` bands capability on isolation strength, and these are model servers. Core LiteRT was
missing even though LiteRT-LM, the layer built on it, was already on the map.

## Not added

- **PX4 / Dronecode.** `robotics_embodied` rules out general robotics tooling with no learning
  surface (ROS 2, Gazebo, Webots, Drake), and a flight autopilot falls under the same rule.
- **MLIR.** It is infrastructure inside LLVM, and it reaches the map through Torch-MLIR and IREE.
- **AIFoundry.** This is the organization behind the list rather than a product. Its AINekko ET
  platform ships runtime, drivers and a simulator for the ET-SoC-1 chip, with no RTL.

## Open accelerator designs

The RISC-V accelerator topic had no home: neither hardware category admits a design that nobody
sells. It is proposed as the preliminary category `open_accelerator_designs`, with an 11-row seed
in `sources/registry/open_accelerator_designs.yaml`. The category's `comments` record the
membership test, the neighbors, the boundary and excluded candidates, and the license strings
that need a tier ruling before promotion.

## How the sources were read

github.com and api.github.com are refused from this environment. Repository files were read
from raw.githubusercontent.com at a named branch. `build.fetch_source` returned 404 for those
URLs here, so their `http_status` and `content_sha256` come from a plain `curl` of the same URL;
raw files are static, so the digest should reproduce under `check_refetch`. Every other source
(PyPI, pypistats, Docker Hub, vendor documentation) was fetched with `build.fetch_source`.
Adoption levels were set from hand-read counts and are held in `sources/verification_queue.yaml`
for the scheduled reconciliation to date. Shelley's adoption is left null: it has no package
registry channel, and no star count could be fetched here.

Country ledger: `countries/batch-01.jsonl`.
