# Research prompt: candidate sweep for the proposed AI Stack Map categories

How to use this file: copy the **shared preamble** and **one category brief** into a fresh research
agent, and attach `corpus-index.tsv`. Run one agent per brief, all in parallel. Running one agent
over all ten briefs works too, but the per-category runs come back deeper and their boundary
calls don't get blurred together. Briefs 5a and 5b (robotics and world models) and 6a and 6b
(assurance and RAI measurement) should each go to a single agent, because each pair has to agree
on a shared boundary.

Speech & audio (#602) has **no brief**. Its 41-row list and the nine rulings on it are already in
the issue, so it goes straight to seeding.

---

## SHARED PREAMBLE (paste into every agent)

You are running a candidate sweep for the **Open Source AI Gap Map** (the "AI Stack Map"), a
curated public dataset that scores AI products on three axes: openness, adoption and capability.
It is organized into categories. A category gets published once it has a definition, a membership
test, a scoring ladder and at least 10 fully researched products. The data lives in
`github.com/currentai-org/os-ai-map`. If you can clone it, read `AGENTS.md`,
`docs/workflows/discover-candidates.md`, `docs/reference/identity.md` and
`docs/architecture/adr-005-closed-product-inclusion.md` first, and use the repo in place of the
attached index. If you can't clone it, the rules you need are restated below.

Your job is to answer **two questions** for the category in your brief, with primary-source evidence:

1. **Is this a good category?** Is there enough supply, is it diverse enough, is it mutually
   exclusive with its neighbors, and can one capability quantity order the whole set?
2. **If yes, who are the candidates?** Return them as rows ready to paste into the registry,
   with the evidence behind each one.

You are not scoring anything. Never assign openness, adoption or capability values. Record the
raw facts a later scorer will need.

### Hard rules

- **Never assert from memory.** Every license, date, download count, archive status and org
  attribution must come from a page you fetched in this run. Record its URL and the fetch date.
  Your training data is stale for anything from 2025 or later.
- **Read the license text, not the label.** GitHub's license field reports `NOASSERTION` on
  plain MIT or BSD text sitting behind a vendor copyright line. For model weights, the model
  card or `LICENSE` file on Hugging Face governs, not the code repo's license. When the code
  license and the weights license differ, record both.
- **A rate limit is not a finding.** HTTP 429, 403 and 5xx mean "not now." Retry, or leave the
  field blank and write "fetch did not complete." Never record that as a measured absence.
- **Pitch identity at the product line the vendor sells, not at a release.** It's FLUX, not
  FLUX.1-dev; Qwen-VL, not Qwen2.5-VL-7B-Instruct; Instinct, not MI300X. Collapse sizes, versions
  and checkpoints into one row, and list the member checkpoints in the evidence table. Hardware
  is the exception: there the generation is the identity. Say which rule you applied whenever
  it's close.
- **Separate products are separate rows.** A model and the engine that runs it are two products.
  So are a platform's registry surface and its runtime. Never merge them.
- **Closed products (ADR-005):** include only the **best-in-class** frontier comparators, not the
  long tail of closed offerings. A platform enters as the **capability surface** that fits this
  category, never as the whole platform. "Vertex AI" is never a product; "Vertex AI Model
  Garden" might be. Mark each row `open`, `open-weights`, `source-available` or `closed`.
- **Dedup against the existing map before proposing anything.** `corpus-index.tsv` lists every
  head product (`tier=head`) and every signal-only candidate (`tier=tail`), with its category,
  GitHub repo, Hugging Face id, PyPI package and retired aliases. A match on slug, alias or any
  artifact ID means the product is **already known**. Don't propose it as new. If it belongs in
  your category rather than where it sits now, list it under *contested products* with a
  move/stay recommendation.
- **Do not invent a legitimacy threshold mid-sweep.** If a signal looks implausible (a star spike,
  a dead repo with high downloads), park the candidate and state the number that bothered you.
  You may declare a **retrieval cutoff** up front (for example, "top 50 by HF downloads"). Report
  it as a coverage limit, and never use it to reject something you have already found.
- **Check that it's alive.** Record `archived`, `fork`, the last push date and the last release
  date. Being dormant doesn't disqualify a candidate. Record it and let the curator decide.

### Artifact identifiers (exact format — the schema rejects URLs)

| Field | Write | Not |
|---|---|---|
| `github` | `owner/repo` (canonical, after redirects) | a URL |
| `huggingface_model` | `owner/name` | a URL |
| `huggingface_dataset` | `owner/name` | a URL |
| `pypi` / `npm` / `crates` | the package name | a URL |
| `arxiv` | `2401.12345` | a URL |
| `homepage` | a full `https://` URL | (this is the only field that is a URL) |

A row needs at least one of these. `type` is one of `software | model | dataset | hardware`.
Slugs are kebab-case, have no version token for models, and never collide with a slug in the index.
`org` is a kebab-case organization slug. Reuse the org slug from the index when that org is
already on the map.

**The package trap:** a PyPI or npm package that shares the product's name is often a client,
a wrapper or someone else's project. Declare a package only when it *is* the product's
documented install path, and cite the doc page that says so.

### Output contract (return exactly this structure, as one Markdown document)

```
# <Category display name> sweep — <YYYY-MM-DD>

## 1. Verdict
GO | GO-WITH-CHANGES | MERGE-INTO-<x> | PARK | CLOSE, then 3–6 sentences on why.

## 2. Fit metrics (computed from section 6, not estimated)
- accepted candidates: N  (open: a, open-weights: b, source-available: c, closed: d)
- independent organizations: M; largest org's share: X% (<org>)
- candidates active in the last 12 months: K
- candidates with a usage instrument (PyPI/npm/crates downloads or HF downloads), as opposed
  to stars only: U
- retrieval cutoff used, if any, and what it excluded

## 3. Boundary
- Definition (one sentence) and litmus test (one yes/no question).
- Explicit exclusions, naming the neighbor category that owns each.
- Contested products table: | product | where it is now (index category or "absent") |
  recommendation (move here / stay / other) | reason |

## 4. Capability quantity
The ONE quantity that orders this set, as a 3–5 rung sketch (low → high), naming the candidate
that anchors the top rung. If no single quantity works, say so. That is a finding, not a failure.

## 5. Scoring ladder inputs
- Which shared ladder each product type needs: model | pretrained | software | dataset | hardware.
- Every license string you met, with the products carrying it. Flag any that are unusual or
  custom (a later maintainer has to place them in a tier).

## 6. Accepted candidates
### 6a. Registry rows (YAML, exact schema, paste-ready)
category: <proposed_slug>
products:
  - slug: ...
    display_name: ...
    type: model
    org: ...
    github: owner/repo
    huggingface_model: owner/name
### 6b. Evidence table, one row per candidate
| slug | open status | license(s) + URL | archived/fork | last push | last release |
  adoption signal + value + URL | member checkpoints/SKUs | org GitHub/HF handle | notes |
### 6c. Source list: every URL behind section 6, with fetch date.

## 7. Parked candidates
| name | reason (already mapped / retired alias / SKU of X / boundary → Y / unmaintained /
  no addressable artifact / closed long-tail / identity unclear) | source URL | fetch date |

## 8. Reconciled counts
raw_signals = duplicate_signals + unique_candidates
unique_candidates = accepted + parked
(state all five numbers; both equations must balance)

## 9. Open questions for the maintainer
Numbered, each answerable yes/no or as a pick from named options, each with your recommendation.
```

Work sources in this order, as they fit the category: GitHub (topic and keyword search, awesome-lists,
org pages), Hugging Face (task filters sorted by downloads and likes, org pages), PyPI/npm download
stats (pypistats.org, npm API), Papers with Code / arXiv for model lines, vendor product pages and
datasheets for hardware and closed products, plus leaderboards and arenas for the category.

---

## CATEGORY BRIEFS (paste one after the preamble)

### Brief 1: Image / video / 3D generation (issue #603) — proposed slug `media_generation`

**Scope:** models and tools whose headline capability is **generating** images, video, 3D assets,
or music/sound effects (per a 2026-09-25 ruling on #602, music and SFX land here) from a
prompt or condition. **Litmus:** is the output a synthesized image, video, 3D or audio-media
asset? Understanding models (captioning, VQA) belong to brief 2. Speech (TTS/ASR) belongs to
`speech_audio`.

**Starting leads (verify, don't trust):** FLUX (Black Forest Labs), Stable Diffusion
XL/3.x (Stability), HunyuanVideo, HunyuanImage, Hunyuan3D, Wan, CogVideoX, LTX-Video, Mochi,
Open-Sora, Qwen-Image, HiDream, SANA, PixArt, Kolors, Lumina, TRELLIS, Stable Audio Open,
MusicGen/AudioCraft, ACE-Step, YuE. Tooling: ComfyUI, AUTOMATIC1111, Forge, InvokeAI,
Fooocus, SD.Next, SwarmUI. Closed frontier: Midjourney, OpenAI image gen, Imagen, Veo, Sora,
Runway, Kling, Suno.

**Decide and report:**
- Should **tooling/UIs** (ComfyUI, A1111) live here or in `ui_api`? Check `ui_api`'s roster in the index.
  Count each side separately so the maintainer can see whether models alone clear the bar.
- `diffusers`, `onetrainer`, `ai-toolkit` and `kohya` are in the index or relevant. Are they
  `ml_frameworks`/`finetuning_code` (stay) or here?
- Can one capability quantity order both image and video models, or does the set split?
  Consider modality coverage, arena Elo, or controllability. Report the per-modality supply.
- LoRAs, checkpoints and merges on Civitai are **not** products. Park them as a class.

### Brief 2: Multimodal models (issue #9) — proposed slug `multimodal_models`

**Scope (settled 2026-09-25):** #9 stays about multimodal *models*. Vision backbones such as timm
and DINO go to brief 3. Generation goes to brief 1, speech to `speech_audio`. The open question
is **understanding VLMs only, or any-to-any/omni too**. Report the supply under both scopes.
**Litmus:** would the model be mischaracterized if it were listed as a text LLM, because its
reason for fame is image/video/document understanding?

**Starting leads:** Qwen-VL line (Qwen2-VL, Qwen2.5-VL, QVQ), InternVL, Molmo, Pixtral, MiniCPM-V,
SmolVLM, LLaVA / LLaVA-NeXT / LLaVA-OneVision, Florence-2, Idefics, Moondream, PaliGemma, DeepSeek-VL,
Kimi-VL, GLM-4V, Phi-vision, Aria, NVLM, Cambrian, Eagle. Omni: Qwen-Omni, MiniCPM-o,
Ming-Omni, Janus. Closed comparators: the frontier chat models are already on the map
in `finetuned_chat`, so check the index before adding a closed row.

**Decide and report:**
- For each candidate, check whether the vendor's **main family is already a head product** in
  `base_pretrained`/`finetuned_chat` (for example `qwen`, `gemma`, `llama`, `phi`, `minicpm`).
  Is the VL line a separately marketed product (a new row) or a SKU of that family (park it)?
  This is the crux of MECE here. Cite the vendor's own naming.
- The capability basis the issue suggests is MMMU-style benchmarks. Find a leaderboard that
  covers most candidates (OpenCompass VLM, MMMU) and report coverage.
- Name the boundary with `embeddings_retrieval` (CLIP, SigLIP, ColPali already live there).

### Brief 3: Classic ML & computer-vision libraries (issue #600) — proposed slug `classic_ml_cv`

**Scope:** foundational non-LLM ML and CV libraries: classical ML, gradient boosting, classical
NLP, and CV model and training toolkits. The 2026-09-25 ruling says this category **owns timm
and general vision backbones**. **Litmus:** would a data scientist reach for this before any LLM
is involved, and does its reason for fame predate or run orthogonal to the LLM stack?

**Starting leads:** scikit-learn, XGBoost, LightGBM, CatBoost, statsmodels, spaCy, NLTK, gensim,
Stanza, timm, torchvision, Ultralytics YOLO, Detectron2, MMDetection/OpenMMLab, OpenCV, Kornia,
albumentations, supervision, fastai, PyTorch Lightning(?), Optuna(?), SHAP(?), Prophet/sktime/
Darts (time series), PyOD, imbalanced-learn, DINOv2/v3 (backbone weights), SAM/SAM 2 (weights?).

**Decide and report:**
- The boundary with `ml_frameworks`: list every index product in `ml_frameworks` that fails that
  category's "LLM-era foundational framework" reading and passes this one. Recommend a move or
  a stay for each.
- Are pretrained backbone **weights** (DINOv3, SAM) products here, or `embeddings_retrieval`/brief 2?
  The ruling gives backbones to this category, so propose how model rows and library rows coexist:
  a `{model: model, software: software}` ladder map, as `document_conversion` does.
- Tabular AutoML, hyperparameter tuning, explainability and time-series: are they in scope or
  drift? Recommend where to draw the line so the category stays one comparison set.
- PyPI downloads are the natural adoption instrument here. Report monthly downloads for every row.

### Brief 4: Model hubs & registries (issue #601) — proposed slug `model_hubs`

**Scope:** platforms whose product is **hosting, indexing and distributing models/datasets**, a
registry other tools pull from. **Litmus:** is it a place where models live and get discovered,
rather than a library that runs them or a UI that chats with them? Per ADR-005, the row is the
registry **surface**. `huggingface-hub` in the index is the Python client and stays in
`ml_frameworks`, so the Hub *platform* would be a new product.

**Starting leads:** Hugging Face Hub, ModelScope, Ollama library, LM Studio catalog, Civitai,
Kaggle Models (formerly TF Hub), PyTorch Hub, ONNX Model Zoo, NVIDIA NGC catalog, Replicate
model library, OpenCSG, Modelers.cn, WiseModel, GitCode AI, OpenXLab, Tensor.art,
Zenodo/OpenML (in scope?), KitOps/ModelKit and OCI model artifacts (registry *format/tooling*:
in scope?), MLflow Model Registry (check `ml_orchestration` in the index), Vertex Model Garden,
Azure AI Foundry catalog, Bedrock Marketplace.

**Decide and report — this is the brief most likely to fail on supply:**
- How many candidates survive the litmus **as distinct registry surfaces** with real evidence?
  If fewer than ~12, say so plainly and recommend PARK, or a merge target.
- Whether self-hostable registry software (for example an open-source hub you can run yourself)
  and hosted public hubs can share one capability quantity.
- What is the adoption instrument? Hosted platforms have no download channel. Report what's
  measurable: model count, monthly visits from a citable source, or client-library downloads
  (and whether those are a fair proxy).

### Brief 5a: Robotics & embodied AI (issue #12) — proposed slug `robotics_embodied`

**Scope:** open frameworks, simulators, robot foundation models (VLAs), datasets and hardware
designs for embodied AI. **Litmus:** does the project's value depend on acting in, or
simulating, the physical world? GR00T lands here (ruled 2026-09-25).

**Starting leads:** LeRobot, MuJoCo (+ MJX, MuJoCo Playground), Isaac Lab / Isaac Sim, Genesis,
ManiSkill, Habitat, RoboCasa/robosuite, PyBullet, Gazebo(?), OpenVLA, Octo, π0/openpi,
GR00T, SmolVLA, RDT, RoboFlamingo, Gemini Robotics (closed comparator), Open X-Embodiment,
DROID, RoboMIND, LeRobot datasets, SO-100/SO-101, Koch, Reachy / Pollen, ALOHA, Unitree SDKs(?).
Check activity: Octo and OpenVLA hadn't been pushed since 2024-07 and 2025-03.

**Decide and report:**
- This is several product types (models, simulators, libraries, datasets, hardware). Does
  one category with a per-type ladder map (`{model, software, dataset, hardware}`) hold, or should it split
  into `robot_foundation_models` + `robot_learning_sim`? Report per-type supply either way.
- Robotics **datasets**: here, or `training_synthetic_datasets` (check the index)?
- Where it sits: a new arc, or a new group inside an existing arc (Model components / Product-UX
  / Infrastructure)? Recommend one.

### Brief 5b: World models (issue #99) — proposed slug `world_models` (run WITH 5a)

**Scope:** models that learn a predictive model of an environment and can be rolled forward. **Litmus:**
given a state and an action, does it predict the next state? Pure text-to-video without action input
is not a world model (that's brief 1).

**Background:** the July count collapsed to about 4 product lines in 2 vendors (Cosmos, V-JEPA 2,
GR00T, HunyuanWorld, plus Matrix-Game as a marginal fifth), and the category was **not**
recommended. A revisit was planned for late October 2026. GR00T now belongs to 5a.

**Re-measure:** Cosmos (all SKUs), V-JEPA 2, HunyuanWorld, Matrix-Game, LingBot-World, Oasis
(Decart), DIAMOND, Genie (closed), Marble / World Labs (closed), Mirage, Yume, Aether, WorldVLA,
VLA-JEPA, open-dreamer (license), anything new since July. **Report:** product lines, vendors
and largest-vendor share, and one recommendation: create, fold into 5a as a sub-surface, or
keep parked with a date.

### Brief 6a: Assurance & compliance evidence (issue #93) — proposed slug `assurance_evidence`

**Scope:** tools whose main output is machine-readable **evidence about an AI system for a party
outside the operating team**: conformity docs, model/system/dataset cards and documentation
(ruled 2026-09-25: this issue owns governance and documentation tooling, including Croissant),
audit trails, provenance, signing and attestation, compliance-as-code, and independently
verifiable proofs. **Litmus:** is the main artifact evidence for a third party? If it changes
runtime behavior it belongs to `safeguards`. If it measures quality for builders, it belongs to
`evaluation_code`. If it streams ops signals, it belongs to `telemetry_observability`.
**Tie-breaker:** when one artifact is both a control and its evidence, classify by what reaches the
outside party. Tag each row **self-attested** or **independently verifiable**.

**Starting leads:** compliance-trestle, AI Verify, MLTE, sigstore model-transparency, Croissant,
NVIDIA nvtrust (the proposer says "ready to list"), EZKL (hold: no LICENSE file), Proof-of-Control
(a standard, so track it and don't list it), model-card-toolkit (archived; evidence of churn),
Hugging Face model-card tooling, VerifyML (dormant), in-toto / SLSA for ML(?), OpenSSF model
signing, C2PA *authoring for model provenance* (coordinate with 6b), AIBOM/SPDX-AI/CycloneDX ML-BOM
tooling, Credo AI and Holistic AI (closed comparators).

### Brief 6b: Responsible-AI measurement (issue #30) — proposed slug `responsible_ai_measurement` (run WITH 6a)

**Scope (narrowed 2026-09-25):** tools that **quantify** a responsibility attribute: **carbon/energy,
fairness, watermarking**. Governance and documentation went to 6a. **Litmus:** does it
measure a footprint or a responsibility property, as opposed to filtering unsafe I/O (`safeguards`)
or documenting for a third party (6a)?

**Starting leads:** CodeCarbon, Zeus, CarbonTracker, experiment-impact-tracker, ML CO2 Impact,
AI Energy Score, Fairlearn, AIF360, Aequitas, What-If Tool, fairness-indicators, SynthID-Text (currently a
`safeguards` tail row), AudioSeal, VideoSeal, Stable Signature, invisible-watermark, C2PA / c2pa-rs /
c2patool, TrustMark.

**Decide and report (for 6a and 6b together):**
- Are 6a and 6b really two categories, or one with a clean internal line? Watermarking and C2PA
  sit on the seam, so assign each to exactly one.
- Does 6b hold together at all? Carbon, fairness and watermarking are three different quantities.
  If no single capability quantity orders them, report per-sub-area supply and say whether
  any one sub-area stands alone (≥10) or whether the issue should close as out of scope.
- The deeper question on #30 is whether the map charts cross-cutting *attribute* tooling at all.
  Give evidence either way: supply, adoption, and whether a gap statement would come out of it.

### Brief 7: Federated learning (issue #574) — proposed slug `federated_learning`

**Scope (from the 2026-09-14 sweep):** training across data holders who never pool their data.
**Litmus:** does the raw training data stay with its owner for the whole run? Out: volunteer
inference (exo, Petals), decentralized training networks (Prime Intellect, Gensyn), chain SDKs
(Bittensor), compute marketplaces. `pysyft` (now in `ml_frameworks`) and `syfthub` (now in
`orchestration_agents`) would move in.

**Known:** Flower, PySyft, FedML, NVFlare, OpenFL, Substra, SyftHub. Flower draws about 120K
installs a month and NVFlare about 27K; the rest are under 1K.
**Widen the sweep:** FATE, TensorFlow Federated, FederatedScope, Fed-BioMed, APPFL, FLUTE, IBM
Federated Learning, PaddleFL, FedScale, Owkin, Apheris (closed?), Rhino FCP (closed?), and
federated-analytics or secure-aggregation libraries (in or out?).
**Answer the three parked questions with evidence:** (1) admit FedML and Substra? (2) is Flower
one product or two (the SDK vs `flwr-datasets`)? (3) is the volunteer-inference finding worth
recording as an insight? Also: does the set clear 10 without padding, and what is the
largest-vendor share?

### Brief 8: Datacenter accelerators (issue #599) — proposed slug `datacenter_accelerators`

**Scope:** physical training and inference accelerators sold or operated as datacenter silicon.
**Litmus:** is it a chip, board or system you rack or rent *as silicon*, distinct from the API
that fronts it? Groq/Cerebras/SambaNova/AWS Neuron/Cloud TPU inference **APIs** are already in the
index. The hardware is a separate product.

**Starting leads:** Google TPU (by generation), AWS Trainium and Inferentia, Intel Gaudi, AMD
Instinct, NVIDIA datacenter GPUs (Hopper/Blackwell) and Grace-Hopper/GB200 systems, Groq LPU,
Cerebras WSE, SambaNova RDU, Tenstorrent (Wormhole/Blackhole; note its open-source software
stack and RISC-V), Graphcore IPU (status?), Etched Sohu, d-Matrix Corsair, Huawei Ascend,
Cambricon, Meta MTIA, Microsoft Maia, Qualcomm Cloud AI 100, Rebellions, FuriosaAI, Lightmatter,
MatX, Biren, Moore Threads. Also open designs if any exist (for example open-source NPU RTL).

**Decide and report:**
- **Identity:** hardware identity is the generation (as with `raspberry-pi-5`). Is the product
  line one row, or one row per generation? Recommend one, with the edge_hardware precedent in mind.
- **Openness facts available:** public datasheet, open driver/compiler stack (and its license),
  open ISA, buyable vs cloud-only. The shared hardware ladder has a `form_factor: chipset` rung
  that scores public datasheets and availability. Report which facts each candidate exposes.
- **Adoption instrument:** there is no download channel. Report what's citable (cloud regions, disclosed
  shipments, MLPerf submissions) and flag that it will mostly abstain.
- **ADR-005:** nearly all of these are closed. Which are best-in-class frontier comparators, and
  which are long tail?
- **Sibling category, or rename `edge_hardware` to "AI hardware"?** Recommend one.
