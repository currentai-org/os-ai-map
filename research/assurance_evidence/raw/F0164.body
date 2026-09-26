# DeepProve

Zero-knowledge proof system for neural network inference, with first-class support for end-to-end LLM proving.

## 👉 Looking to run DeepProve? Start with [`zkml/README.md`](zkml/README.md)

That's where the installation steps, model setup, GPU build, and the full end-to-end `bench-llm` tutorial live. The rest of this page is a high-level summary of what DeepProve is and what to expect.

## Overview

DeepProve is the first end-to-end zero-knowledge proof system for full LLM inference. It generates cryptographic proofs of neural network forward passes using sumchecks and logup GKR, achieving sublinear proving time in model size — orders of magnitude faster than circuit-based approaches.

Confirmed working models: **GPT-2**, **Gemma 3**, **Llama 2** — all transformer layers proven end-to-end, from token embeddings through to next-token argmax. MLP and CNN inference is also supported.

This repository is a Rust workspace. The [`zkml`](zkml/) crate is the core proving library; the remaining crates provide the client stack, storage layer, and developer tooling.

## Headline Numbers

Single-machine inference proving on a 24-core / 504 GB CPU server:

| Model   | Sequence   | Prove time | Verify | Proof size | Throughput                    |
|---------|-----------:|-----------:|-------:|-----------:|------------------------------:|
| GPT-2   | 512 tokens |    7.6 min |  1.3 s |   10.7 MiB | 1.12 tokens/s (67 tokens/min) |
| Gemma 3 | 512 tokens |     19 min |  4.3 s |     27 MiB | 0.45 tokens/s (27 tokens/min) |

- **10–30× faster** than the previous published state of the art (e.g. zkGPT reports ≈ 0.05 tokens/s on similar hardware).
- **Accuracy preserved**: ≥99.6% cosine similarity to the floating-point baseline at 12-bit quantization (GPT-2).
- **Scales out**: horizontal proof distribution and GPU acceleration are supported today; clusters of GPU workers are on the roadmap.

For the full methodology and a deeper benchmark sweep across sequence lengths and models, see the DeepProve paper (link to be added) and [`zkml/README.md`](zkml/README.md).

## Repository Structure

| Crate | Description |
|-------|-------------|
| [`zkml`](zkml/) | Core proving library — model quantization, layer implementations (MLP, CNN, transformer), and ZK proof generation/verification |
| [`deep-prove`](deep-prove/) | Client stack — `deep-prove-worker` runs a proof generation server; `deep-prove-cli` submits proving jobs locally or to a remote proving network |
| [`tenstore`](tenstore/) | Storage facade for persisting and retrieving tensor data; supports local and remote (S3-compatible) backends |
| [`tenvis`](tenvis/) | Interactive CLI tool for inspecting and debugging proof data stored in tenstore |
| [`telemetry`](telemetry/) | Shared OpenTelemetry tracing and logging setup used across all crates |
| [`utils`](utils/) | Shared utility helpers: CSV recording, memory tracking, statistical summaries |

## Licensing

Licensed under the [Lagrange License](LICENSE).

## Acknowledgements

This project builds upon the work from [scroll-tech/ceno](https://github.com/scroll-tech/ceno), reusing the sumcheck and GKR implementation from that codebase.
