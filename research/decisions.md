# New-category decisions: 2026-09-26

This record rules on the nine live sweeps (branches `claude/research-<dir>`, each with its evidence
trail and a two-pass independent audit). The user delegated the calls to this session ("you can run
everything"). Every decision below is a proposal for the maintainer to review in the PRs, and nothing
merges without a person. Where a sweep's recommendation isn't overridden here, **it stands as
written in that sweep's §9**.

## Fit test (adopted before reading the counts)

1. At least 15 accepted candidates with a live artifact.
2. At least 6 independent organizations, and no single org above 30%.
3. One capability quantity, or a per-type ladder map with a per-type or within-modality reading.
4. MECE: one category per product; contested products assigned explicitly.

## Verdicts

| Proposal | Accepted | Orgs / top share | Fit | Decision |
|---|---|---|---|---|
| `speech_audio` (#602) | 42 (+additions) | 34 / 7.1% | pass | **CREATE** (already ruled) |
| `media_generation` (#603) | 92 | 59 parents / 6.5% | pass (within-modality arena reading) | **CREATE** |
| `multimodal_models` (#9) | 47 | 35 / 8.5% | pass | **CREATE**, scope (b) + unified |
| `classic_ml_cv` (#600) | 81 | 68 / 6.2% | pass | **CREATE** as one category (split later if the ladder wants it) |
| `model_hubs` (#601) | 18 | 17 parents / 11.1% | pass, but thin | **CREATE**, last promotion wave |
| `robotics_embodied` (#12) | 60 | 46 / 10.0% | pass (per-type ladder map) | **CREATE** |
| `world_models` (#99) | 21 | 20 / 9.5% | pass, adoption thin | **CREATE (preliminary)**. The July count no longer holds. Promotion waits for the late-October revisit #99 already planned. |
| `assurance_evidence` (#93) | 23 (+C2PA/watermarking) | 23 / 4.3% | pass | **CREATE**, with the SA/IV tag in prose |
| `responsible_ai_measurement` (#30) | 23 | 19 | **fails 3** (three unrelated quantities) | **PARK.** Watermarking → `assurance_evidence`. Fairness (10) and carbon (9) each fail test 1, so the seed rows stay in the sweep record and #30 stays open for a fairness-only or carbon-only proposal. |
| `federated_learning` (#574) | 36 + 2 moves | 33 / 8.3% | pass | **CREATE** |
| `datacenter_accelerators` (#599) | 22 | 21 / 9.1% | pass (adoption abstains) | **CREATE** as a sibling of `edge_hardware` |

## Placement, weights and ladders (preliminary; the promotion PR can revise with evidence)

| Category | Taxonomy group | weights adopt/cap | `extends` |
|---|---|---|---|
| speech_audio | Model components → Models | 0.4 / 0.6 (ruled) | `{model: model, software: software}` (ruled) |
| media_generation | Model components → Models | 0.4 / 0.6 | `{model: model, software: software}` |
| multimodal_models | Model components → Models | 0.3 / 0.7 | `model` |
| robotics_embodied | Model components → **new group "Embodied & world models"** (slug `embodied_world`) | 0.4 / 0.6 | `{model: model, software: software, dataset: dataset, hardware: hardware}` |
| world_models | same new group | 0.3 / 0.7 | `model` |
| federated_learning | Model components → Pipeline code (after `finetuning_code`) | 0.5 / 0.5 | `software` |
| assurance_evidence | Product / UX → Observability | 0.4 / 0.6 | `software` |
| classic_ml_cv | Infrastructure → Compute & runtime (after `ml_frameworks`) | 0.6 / 0.4 | `{model: pretrained, software: software}` |
| model_hubs | Infrastructure → Platform | 0.3 / 0.7 | `software` |
| datacenter_accelerators | Infrastructure → Hardware (after `edge_hardware`) | 0.2 / 0.8 | `hardware` |

## Cross-category rulings (the boundary matrix)

| Product | From | To | Moved in |
|---|---|---|---|
| `nemo` (tail; github → `NVIDIA-NeMo/Speech`, display "NVIDIA NeMo Speech") | finetuning_code registry | speech_audio | seed |
| `nunchaku` (tail) | compilers registry | media_generation | seed |
| `synthid-text` (tail) | safeguards registry | assurance_evidence | seed |
| `segment-anything` + `sam2` (tails), folded into one Segment Anything row | scientific_ai_models registry | classic_ml_cv | seed |
| `pysyft` (head) | ml_frameworks | federated_learning | promotion (rebanded) |
| `syfthub` (head) | orchestration_agents | federated_learning | promotion; the litmus widens to "training, evaluation or querying" |
| janus, bagel, emu, sensenova-u (unified understanding + generation) | contested | multimodal_models | seed (the media sweep agrees) |
| Cosmos, V-JEPA 2, HY-World, action-conditioned game world models | contested | world_models | seed (as the robotics sweep ruled) |
| GR00T | – | robotics_embodied | seed (ruled 2026-09-25) |
| diffusion trainers (kohya sd-scripts, musubi-tuner, SimpleTuner, diffusion-pipe) | – | finetuning_code registry | follow-up (not in this PR) |
| OCR-first VLMs | – | document_conversion | follow-up |
| embodied-reasoning VLMs with no action head (RynnBrain, Hy-Embodied VLM, UnifoLM-ER), Matrix-3D, Marble | – | multimodal_models / media_generation | follow-up sweep; not seeded now |
| dstack | – | deployment | follow-up |
| Axelera Europa | – | edge_hardware | follow-up |

## Per-category overrides of the sweep recommendations

- **speech_audio:** take §9 Q5(a) (add Cohere Transcribe, MOSS-Transcribe-Diarize, Breeze TTS 2,
  OmniVoice and IndexTTS). Also add, from the user's external TTS sweep (verified live, 21/21 claims,
  `research/external_tts/`), VoxCPM and Maya1, plus Cartesia Sonic as a closed comparator (its
  homepage was fetched there). Keep Voxtral TTS inside `voxtral` and Step-Audio-EditX parked (the
  sweep's reasons hold). Slugs are `qwen-asr`/`qwen-tts` (Q2). `pocket-tts` gets its own row (Q4).
- **media_generation:** every §9 recommendation stands. On Q10 (the closed flagship on an open line),
  the newest *distributed* release governs openness. This is a proposal: record it in the category
  `comments` and flag it in the PR for the maintainer, because it decides whether `wan` scores open.
- **multimodal_models:** scope (b) plus the four unified models. The membership test is "separately
  marketed as a vision/omni model" (Q2). No closed rows (Q7).
- **classic_ml_cv:** one category (Q1a). DataRobot is held (Q9).
- **model_hubs:** OCI tooling out (Q3a). No regional closed hubs (Q10). The HF platform slug is
  `huggingface-hub-platform` (Q1).
- **robotics_embodied:** autonomous driving is in (Q3). Robot datasets live here (Q4). No SO-100
  row (Q8).
- **federated_learning:** FedML and Substra are tail rows, not in the first promotion tranche (Q1a).
  Flower is one product (Q2a). Apheris and Rhino FCP are the only closed rows (Q10).
- **datacenter_accelerators:** identity is the generation (Q1a). Keep all 22 at seed. Inferentia2 is
  the ADR-005 trim candidate at promotion (Q4).
- **assurance_evidence:** C2PA and the watermarking rows (SynthID-Text, Content Seal, TrustMark and
  the rest) come in from the 6b seed, per option (c).

## Shared-rubric rulings needed: never inside a category PR

Every custom or new license string a sweep lists in §5 goes to **one** maintainer "license rulings"
issue. Products carrying one are **deferred** at promotion (promote-category step 7). No category PR
edits `sources/rubrics/*.yaml`.

## Promotion scope

A category publishes at ≥10 promoted products. Each promotion PR promotes a **first tranche of
10–30**, chosen for representativeness: the leaders by adoption, the closed comparators ADR-005
needs, and coverage of each sub-type. The rest stay registry rows in the category, which
`add-product` can promote later. `world_models` and `model_hubs` go last.
