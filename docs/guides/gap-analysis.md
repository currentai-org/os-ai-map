# Gap Analysis Guide

How each category is assigned a **maturity stage (0–5)** and a set of **gaps**, from
product scores. Computed in `build/serialize.py` (`_stage_and_gaps`) and emitted per
category into `build/notebook_data.json` as `stage` (`{num, name}`) and `gaps` (a list),
alongside `layer`. The published notebook renders both as a badge + chips per category.

This is the MVP, **category-level** collapse of CF's 6-stage maturity ladder (Void →
Stage 5 / competitive). Per-stage product placement is deliberately out of scope for now.

## Inputs (per product)

- **openness bucket** from `openness.class` → `open` / `open-ish` / `closed`
  (the canonical map in `docs/openness-class-map.json`).
- **adoption** `adoption.level` (1–5), **capability** `capability.score` (1–5, null for datasets).
- **per-category weights** `weights.adopt` / `weights.cap` (sum to 1).

## Maturity score & "mature"

Per-category linear formula: `score = w_adopt·adoption + w_cap·capability` (1–5).
Datasets (no capability) are graded on adoption alone. A product is **mature** when its
score **≥ 4.5** — a deliberately high bar (near-best on both axes).

**Only fully-open products count toward maturity/stage** (strict open-only). Open-ish
products (open-weights / source-available / open-toolchain) do *not* count toward the
ecosystem's maturity; they only surface the openness gap.

## Stage

| | condition |
|---|---|
| **5 Mature Open Ecosystem** | ≥ 4 mature fully-open products **and** ≥ 3 total fully-open |
| **4 Competitive Open Ecosystem** | 1–3 mature fully-open products |
| **3 Viable Alternatives** | 0 mature; best fully-open score ≥ 3.5 |
| **2 Emerging Alternatives** | 0 mature; best fully-open score 3–3.5 |
| **1 Open Experiments** | 0 mature; best fully-open score 2–3 |
| **0 Void** | no viable open option (best fully-open < 2 and nothing mature anywhere) |

## Gaps (a set per category — extensible)

- **Stage 5** → none.
- **Stage 0** → `void`.
- **Stage 4** → `maturity` (competitive, but needs more mature open products for depth/resilience).
- **Stages 1–3** → `maturity` **plus** one diagnostic:
  - `openness` — a *mature* product exists somewhere (open-ish or closed), but none is fully open
    (the map's core finding: open-weights ≠ open-source);
  - else `capability` — the best option's capability < 4 (nothing capable yet);
  - else `adoption` — capable but under-adopted.

The set is designed to grow: future flags (e.g. *maintenance* / *bus-factor*) slot in once
those signals are available, without changing the stage logic.

## Current result (421 products)

| Stage | Categories | Gaps |
|---|---|---|
| 5 Mature | ml_frameworks, orchestration_agents | — |
| 4 Competitive | inference_code, finetuning_code, evaluation_code, benchmark_eval_data, ui_api, agent_tools_protocols, deployment | maturity |
| 3 Viable | base_pretrained, telemetry_observability, edge_hardware | maturity, openness |
| 2 Emerging | training_synthetic_datasets | maturity, adoption |
| 1 Open Experiments | finetuned_chat | maturity, openness |

The story: open developer **tooling** is mature; the open frontier struggles are in
**models, data, and hardware**, which carry openness/adoption gaps.

## Tunable parameters

`_MATURE_MIN` (4.5), `_STAGE5_MIN_MATURE` (4), `_STAGE5_MIN_TOTAL` (3), and the stage-1–3
score bands live at the top of the gap-analysis block in `build/serialize.py`.
