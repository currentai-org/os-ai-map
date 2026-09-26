# Robotics & embodied AI + World models sweep — 2026-09-26

Briefs 5a (`robotics_embodied`, issue #12) and 5b (`world_models`, issue #99), run as one sweep
because they share a boundary. Each has its own verdict, metrics, rows file and counts.

**How to read the evidence.** Every fact carries an id. `Fnnnn` is a body fetched live with
`research/rfetch.sh` on 2026-09-26 and saved at `raw/Fnnnn.body` (logged in `fetch-log.tsv` with
UTC time, HTTP code and sha256). `Wnnnn` is a WebSearch or WebFetch call logged in `web-log.tsv`
with a verbatim excerpt. A small number of ids are HTTP 404s from package registries or ecosyste.ms,
cited only as evidence of absence (F0263: no `robocasa` on PyPI; F0307: RynnWorld-Teleop not
indexed). F0086 is a failed curl that was retried (F0090). Nothing below comes from recall.

**Sources worked, in order:** WebSearch discovery (W0001–W0044: 2026 VLA and world-model releases,
awesome-lists, a best-of simulator list, a VLA index, leaderboards); ecosyste.ms repo metadata for
every GitHub candidate; ungh.cc for renames; raw LICENSE and README text; the Hugging Face API
(author listings sorted by 30-day downloads, the `robotics` pipeline and task filters); ecosyste.ms
PyPI download counts; vendor pages via WebFetch for the closed comparators.

**Retrieval cutoffs (coverage limits, not rejections).** HF author listings were read to the top 15
by downloads; the HF `robotics` model filter to the top 60 and the dataset filter to the top 40.
The sinanlabs VLA index (F0001, 40 entries) was used for discovery; an entry was verified only
when an HF listing or search surfaced it independently. Eleven entries that were not (ten VLAs and
Magma) are parked with the index as their only source.

---

# Part A — Robotics & embodied AI (`robotics_embodied`)

## 1. Verdict

**GO-WITH-CHANGES.** Supply is deep and diverse: 60 accepted candidates from 46
organizations, no organization above 10.0% of the set, 49 of them active in the last 12
months, and all four product types represented (models 29, software 17, hardware 8, datasets 6).
The litmus ("does the value depend on acting in, or simulating, the physical world?") separates
cleanly from its neighbors apart from the seams listed in §3. Two changes: first, keep it
as **one category with a per-type ladder map `{model, software, dataset, hardware}`** rather than
splitting, because hardware (8) would fall below the 10-product bar on its own and datasets (6 researched)
are unproven: 16 more HF robotics datasets sit parked as not researched, so that supply is a floor. Second, accept that **no single capability quantity orders the whole set**: capability has to be
read per type (§4). The VLA model population turned over since the brief was written. OpenVLA and
Octo are dormant (last pushes 2025-03-23 and 2024-07-31), and the 2026 supply comes from GR00T
N1.7, MolmoAct2, GigaBrain-0.7, LingBot-VLA, Xiaomi-Robotics, Hy-Embodied-0.5-VLA and InternVLA-A1.5.

## 2. Fit metrics (computed from section 6 by `gen.py`)

- accepted candidates: 60  (open: 49, open-weights: 10, source-available: 0, closed: 1)
- by type: dataset 6, hardware 8, model 29, software 17
- independent organizations: 46; largest org's share: 10.0% (google, 6 rows)
- candidates active in the last 12 months (a dated push or release on/after 2025-09-26; a closed product counts when its product page is live): 49 of 60
- candidates with a usage instrument (PyPI or HF downloads) declared: 42 of 60; the rest are stars-only or unmeasured
- per-type supply: models 29 (open 18, open-weights 10, closed 1; a model whose weights carry no stated license is counted open-weights), software 17 (all open), hardware 8 (all open), datasets 6 (all downloadable; 2 carry CC BY-NC-SA 4.0 and are still marked `open`, meaning downloadable, and their NC terms go to the ladder). The 6 datasets are a floor: another 16 robotics datasets in the HF top 40 are parked as not researched (§7)
- retrieval cutoff: see the header. It excluded nothing already found; eleven index-only entries are parked, not rejected.

## 3. Boundary

- **Definition:** Open frameworks, simulators, robot policy models (VLAs), robot-interaction datasets and
  open hardware designs whose purpose is an agent acting in, or being simulated in, the physical world.
- **Litmus:** Does the product's value depend on producing or simulating physical actions by a robot or vehicle?
- **Exclusions:**
  - Embodied-reasoning VLMs with no action output (RynnBrain, Hy-Embodied VLM, UnifoLM-ER) belong to `multimodal_models`, the sibling proposal.
  - Action-conditioned *predictors* of the environment belong to `world_models` (Part B), including robot world models such as Genie Envisioner, UnifoLM-WMA, BWM and Ctrl-World.
  - Benchmark suites with no simulator of their own (LIBERO) belong to `benchmark_eval_data`, and policy-evaluation harnesses (Isaac Lab-Arena) to `evaluation_code`.
  - Generic RL environment APIs (Gymnasium) belong to `ml_frameworks`.
  - General robotics tooling with no learning surface (ROS 2, dora-rs, Gazebo, Webots, Drake) is out of scope; see question 2.
  - Edge inference boards stay in `edge_hardware`. Robot bodies are not inference boards, so the two don't overlap.

**Contested products** (siblings being swept in parallel are flagged, not resolved):

| product | where it is now | recommendation | reason |
|---|---|---|---|
| Open X-Embodiment, DROID, RoboMIND, AgiBot World, NVIDIA Physical AI Dataset, InternData-A1 | absent (candidate: `training_synthetic_datasets`) | move here | Their consumers are robot policies, and the trajectories are actions, not corpora for language/vision pretraining (question 4) |
| RoboTwin, RoboCasa | absent (candidate: `benchmark_eval_data`) | here | Each ships a simulator and data generator; the benchmark is a by-product |
| LIBERO | absent | other → `benchmark_eval_data` | Benchmark suite only |
| Isaac Lab-Arena | absent | other → `evaluation_code` | Evaluation harness |
| Gymnasium | absent | other → `ml_frameworks` | Generic RL API |
| Gemini Robotics-ER, Hy-Embodied VLM, RynnBrain, UnifoLM-ER | absent | ER stays inside `gemini-robotics`; others → `multimodal_models` (sibling) | No action head; flag to the multimodal sweep |
| VLA-JEPA, RynnVLA-002 (ex-WorldVLA), GigaBrain | absent | here | They output actions; the world model sits inside the policy |
| Alpamayo, CARLA | absent | Alpamayo here, CARLA parked | Driving is acting in the physical world; needs a ruling (question 3) |
| LeRobot | absent | here | The framework is the product; its Hub datasets org may interest the `model_hubs` sibling, flagged |

## 4. Capability quantity

**No single quantity orders the whole set.** That's a finding, not a failure: a VLA, a physics engine,
a dataset and a robot arm don't share an axis. Per type:

- **Models: embodiment generality.** (1) single-task or single-robot fine-tune → (2) multi-task policy
  on one embodiment family → (3) cross-embodiment pretraining on pooled robot data (OpenVLA, Octo,
  RDT) → (4) cross-embodiment plus reasoning and humanoid/bimanual control, commercially licensed
  (GR00T N1.7, an "open reasoning VLA model for humanoid robots", W0002; π0.5) → (5) the frontier
  generalist with a separate embodied-reasoning model and an on-device variant: **Gemini Robotics 2 /
  ER 2 / On-Device 2** (W0036), closed. Top open anchor: **GR00T**.
- **Software: simulation throughput × fidelity.** (1) CPU rigid-body scripting (PyBullet) → (2)
  contact-rich CPU physics (MuJoCo classic, robosuite) → (3) GPU-parallel RL environments (Brax, MJX,
  ManiSkill, mjlab) → (4) GPU-parallel multi-physics with photoreal rendering and sim-to-real
  pipelines (**Isaac Lab / Isaac Sim**, Genesis, Newton). Anchor: **Isaac Lab** (multi-backend physics
  including Newton, W0022).
- **Datasets: episodes × embodiments.** Single-lab sets → DROID (92,223 episodes, W0032) → pooled
  cross-embodiment collections (**Open X-Embodiment**, 58 datasets, W0021; AgiBot World Beta, past
  1M trajectories, W0021). Anchor: **AgiBot World**.
- **Hardware: morphology.** (1) single 6-DoF arm (SO-101, Koch) → (2) bimanual teleoperation rig
  (ALOHA, ALOHA 2, OpenArm) → (3) mobile manipulator (LeKiwi) → (4) full humanoid (**Berkeley
  Humanoid Lite**, W0019). Reachy Mini is an expressive desktop robot that sits outside this ladder.

## 5. Scoring ladder inputs

- Ladders needed: `model` (29 VLAs; none are trained from scratch on raw data, so it's `model`, not `pretrained`),
  `software` (17), `dataset` (6), `hardware` (8). The map is `extends: {model: model, software: software, dataset: dataset, hardware: hardware}`.
- License strings met (products carrying them); **custom or unusual ones are bolded** for a maintainer to place:
  - Apache-2.0: lerobot, mujoco, mujoco-playground, isaac-sim (code), genesis, maniskill, newton, brax, mjlab, roboverse, gr00t (code), pi0 (code), smolvla, rdt (RDT2), x-vla, gigabrain, lingbot-vla, wall-oss (code), molmoact, univla, rynnvla, xiaomi-robotics, being-h (H0.5 weights), spirit-vla (weights), hy-embodied-vla, alpamayo (code), vla-jepa, open-x-embodiment (repo), droid (HF card), robomind, so-101, koch-v1-1, reachy-mini, lekiwi, openarm
  - MIT: habitat, robosuite, robocasa, robomimic, openvla, octo, rdt (RDT-1B), cogact, spatialvla, internvla (M1 code), being-h (H0), spirit-vla (code), eo-1, roboflamingo, aloha, berkeley-humanoid-lite
  - BSD-3-Clause: isaac-lab. zlib (with excepted directories): pybullet
  - **NVIDIA Open Model License** (commercial use allowed): gr00t weights. **nvidia-oneway-noncommercial**: GR00T-N1.5-3B_Assemble_Trocar; nvidia/GR00T-H, labeled `nvidia-license` but linking the same OneWay Noncommercial License (F0096)
  - **Isaac Sim Additional Software and Materials License**: the proprietary runtime components isaac-sim needs (F0159)
  - **OpenMDW-1.1**: alpamayo weights
  - **gemma** (Gemma terms): the LeRobot ports of π0/π0.5 weights; PI's own checkpoint terms not fetched
  - **CC BY-NC-SA 4.0**: internvla, go-1, unifolm-vla, agibot-world, interndata-a1
  - CC-BY-4.0: nvidia-physical-ai-dataset
  - **G0 PLUS Community License / G0.5 Community License** (non-commercial + limited patent, date-split with Apache-2.0): galaxea-g0
  - **No license stated**: wall-oss weights, MolmoAct2 weights, nora, the droid GitHub repo
  - "open source all hardware designs", license text not fetched: aloha-2

## 6. Accepted candidates

### 6a. Registry rows

Paste-ready file: `rows.robotics_embodied.yaml` (validated against `docs/schemas/registry.schema.json`). Contents:

```yaml
category: robotics_embodied
products:
- slug: lerobot
  display_name: LeRobot
  type: software
  org: hugging-face
  github: huggingface/lerobot
  pypi: lerobot
- slug: mujoco
  display_name: MuJoCo
  type: software
  org: google
  github: google-deepmind/mujoco
  pypi: mujoco
- slug: mujoco-playground
  display_name: MuJoCo Playground
  type: software
  org: google
  github: google-deepmind/mujoco_playground
  pypi: playground
- slug: isaac-lab
  display_name: Isaac Lab
  type: software
  org: nvidia
  github: isaac-sim/IsaacLab
  pypi: isaaclab
- slug: isaac-sim
  display_name: Isaac Sim
  type: software
  org: nvidia
  github: isaac-sim/IsaacSim
- slug: genesis
  display_name: Genesis
  type: software
  org: genesis-embodied-ai
  github: Genesis-Embodied-AI/genesis-world
  pypi: genesis-world
- slug: maniskill
  display_name: ManiSkill
  type: software
  org: mani-skill
  github: mani-skill/ManiSkill
  pypi: mani-skill
- slug: habitat
  display_name: Habitat
  type: software
  org: meta
  github: facebookresearch/habitat-sim
- slug: robosuite
  display_name: robosuite
  type: software
  org: arise-initiative
  github: ARISE-Initiative/robosuite
  pypi: robosuite
- slug: robocasa
  display_name: RoboCasa
  type: software
  org: robocasa
  github: robocasa/robocasa
- slug: robomimic
  display_name: robomimic
  type: software
  org: arise-initiative
  github: ARISE-Initiative/robomimic
  pypi: robomimic
- slug: pybullet
  display_name: PyBullet
  type: software
  org: bullet-physics
  github: bulletphysics/bullet3
  pypi: pybullet
- slug: newton
  display_name: Newton
  type: software
  org: newton-physics
  github: newton-physics/newton
- slug: brax
  display_name: Brax
  type: software
  org: google
  github: google/brax
  pypi: brax
- slug: mjlab
  display_name: mjlab
  type: software
  org: mujocolab
  github: mujocolab/mjlab
  pypi: mjlab
- slug: robotwin
  display_name: RoboTwin
  type: software
  org: robotwin-platform
  github: RoboTwin-Platform/RoboTwin
- slug: roboverse
  display_name: RoboVerse
  type: software
  org: roboverse
  github: RoboVerseOrg/RoboVerse
- slug: gr00t
  display_name: Isaac GR00T
  type: model
  org: nvidia
  github: NVIDIA/Isaac-GR00T
  huggingface_model: nvidia/GR00T-N1.7-3B
- slug: pi0
  display_name: π0 (openpi)
  type: model
  org: physical-intelligence
  github: Physical-Intelligence/openpi
- slug: smolvla
  display_name: SmolVLA
  type: model
  org: hugging-face
  huggingface_model: lerobot/smolvla_base
- slug: openvla
  display_name: OpenVLA
  type: model
  org: openvla
  github: openvla/openvla
  huggingface_model: openvla/openvla-7b
- slug: octo
  display_name: Octo
  type: model
  org: octo-models
  github: octo-models/octo
  huggingface_model: rail-berkeley/octo-base-1.5
- slug: rdt
  display_name: RDT (Robotics Diffusion Transformer)
  type: model
  org: thu-ml
  github: thu-ml/RDT2
  huggingface_model: robotics-diffusion-transformer/RDT2-VQ
- slug: x-vla
  display_name: X-VLA
  type: model
  org: tsinghua-air
  github: 2toinf/X-VLA
  huggingface_model: 2toINF/X-VLA-Pt
- slug: gigabrain
  display_name: GigaBrain
  type: model
  org: gigaai
  github: open-gigaai/giga-brain-0
  huggingface_model: open-gigaai/GigaBrain-0.7-3.5B-Base
- slug: galaxea-g0
  display_name: Galaxea G0
  type: model
  org: galaxea
  github: OpenGalaxea/GalaxeaVLA
  huggingface_model: OpenGalaxea/G05
- slug: lingbot-vla
  display_name: LingBot-VLA
  type: model
  org: robbyant
  github: Robbyant/lingbot-vla
  huggingface_model: robbyant/lingbot-vla-4b
- slug: internvla
  display_name: InternVLA
  type: model
  org: shanghai-ai-laboratory
  github: InternRobotics/InternVLA-A-series
  huggingface_model: InternRobotics/InternVLA-A1.5-base
- slug: wall-oss
  display_name: WALL-OSS
  type: model
  org: x-square-robot
  github: X-Square-Robot/wall-x
  huggingface_model: x-square-robot/wall-oss-flow
- slug: molmoact
  display_name: MolmoAct
  type: model
  org: allen-institute-for-ai
  github: allenai/molmoact
  huggingface_model: allenai/MolmoAct2
- slug: cogact
  display_name: CogACT
  type: model
  org: microsoft
  github: microsoft/CogACT
  huggingface_model: CogACT/CogACT-Base
- slug: spatialvla
  display_name: SpatialVLA
  type: model
  org: shanghai-ai-laboratory
  github: SpatialVLA/SpatialVLA
  huggingface_model: IPEC-COMMUNITY/spatialvla-4b-224-pt
- slug: univla
  display_name: UniVLA
  type: model
  org: opendrivelab
  github: OpenDriveLab/UniVLA
  huggingface_model: qwbu/univla-7b
- slug: go-1
  display_name: GO-1 (Genie Operator-1)
  type: model
  org: agibot
  huggingface_model: agibot-world/GO-1
- slug: rynnvla
  display_name: RynnVLA
  type: model
  org: alibaba-damo-academy
  github: alibaba-damo-academy/RynnVLA-002
  huggingface_model: Alibaba-DAMO-Academy/RynnVLA-001-7B-Base
- slug: xiaomi-robotics
  display_name: Xiaomi-Robotics
  type: model
  org: xiaomi
  github: XiaomiRobotics/Xiaomi-Robotics-0
  huggingface_model: XiaomiRobotics/Xiaomi-Robotics-0-Pretrain
- slug: being-h
  display_name: Being-H
  type: model
  org: beingbeyond
  github: BeingBeyond/Being-H0
  huggingface_model: BeingBeyond/Being-H05-2B
- slug: spirit-vla
  display_name: Spirit (Spirit AI VLA)
  type: model
  org: spirit-ai
  github: Spirit-AI-Team/spirit-v1.5
  huggingface_model: Spirit-AI-robotics/Spirit-v1.5
- slug: hy-embodied-vla
  display_name: Hy-Embodied VLA
  type: model
  org: tencent
  github: Tencent-Hunyuan/Hy-Embodied-0.5-VLA
  huggingface_model: tencent/Hy-Embodied-0.5-VLA-UMI
- slug: unifolm-vla
  display_name: UnifoLM-VLA
  type: model
  org: unitree
  huggingface_model: unitreerobotics/UnifoLM-VLA-Base
- slug: alpamayo
  display_name: Alpamayo
  type: model
  org: nvidia
  github: NVlabs/alpamayo
  huggingface_model: nvidia/Alpamayo-1.5-10B
- slug: eo-1
  display_name: EO-1
  type: model
  org: ipec-community
  huggingface_model: IPEC-COMMUNITY/EO-1-3B
- slug: nora
  display_name: NORA
  type: model
  org: declare-lab
  huggingface_model: declare-lab/nora
- slug: roboflamingo
  display_name: RoboFlamingo
  type: model
  org: roboflamingo
  github: RoboFlamingo/RoboFlamingo
- slug: vla-jepa
  display_name: VLA-JEPA
  type: model
  org: ginwind
  github: ginwind/VLA-JEPA
  huggingface_model: ginwind/VLA-JEPA
- slug: gemini-robotics
  display_name: Gemini Robotics
  type: model
  org: google
  homepage: https://deepmind.google/models/gemini-robotics/
- slug: open-x-embodiment
  display_name: Open X-Embodiment
  type: dataset
  org: google
  github: google-deepmind/open_x_embodiment
- slug: droid
  display_name: DROID
  type: dataset
  org: droid-dataset
  github: droid-dataset/droid
  huggingface_dataset: lerobot/droid_1.0.1
- slug: robomind
  display_name: RoboMIND
  type: dataset
  org: x-humanoid
  huggingface_dataset: x-humanoid-robomind/RoboMIND
- slug: agibot-world
  display_name: AgiBot World
  type: dataset
  org: agibot
  github: OpenDriveLab/AgiBot-World
  huggingface_dataset: agibot-world/AgiBotWorld-Beta
- slug: nvidia-physical-ai-dataset
  display_name: NVIDIA Physical AI Dataset
  type: dataset
  org: nvidia
  huggingface_dataset: nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim
- slug: interndata-a1
  display_name: InternData-A1
  type: dataset
  org: shanghai-ai-laboratory
  huggingface_dataset: InternRobotics/InternData-A1
- slug: so-101
  display_name: SO-101 arm
  type: hardware
  org: the-robot-studio
  github: TheRobotStudio/SO-ARM100
- slug: koch-v1-1
  display_name: Koch v1.1 arm
  type: hardware
  org: jess-moss
  github: jess-moss/koch-v1-1
- slug: reachy-mini
  display_name: Reachy Mini
  type: hardware
  org: pollen-robotics
  github: pollen-robotics/reachy_mini
- slug: aloha
  display_name: ALOHA
  type: hardware
  org: tonyzhaozh
  github: tonyzhaozh/aloha
- slug: aloha-2
  display_name: ALOHA 2
  type: hardware
  org: google
  arxiv: '2405.02292'
  homepage: https://aloha-2.github.io/
- slug: berkeley-humanoid-lite
  display_name: Berkeley Humanoid Lite
  type: hardware
  org: uc-berkeley
  github: HybridRobotics/berkeley-humanoid-lite
- slug: lekiwi
  display_name: LeKiwi
  type: hardware
  org: sigrobotics-uiuc
  github: SIGRobotics-UIUC/LeKiwi
- slug: openarm
  display_name: OpenArm
  type: hardware
  org: enactic
  github: enactic/openarm
```

### 6b. Evidence table

| slug | open status | license(s) + source | archived/fork | last push | last release | adoption signal | member checkpoints/SKUs | org GitHub/HF handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| lerobot | open | Apache-2.0 (F0002; PyPI metadata Apache-2.0 F0254) | not archived, not fork (F0002) | 2026-09-22 (F0002) | v0.6.1, 2026-08-03 (F0387) | PyPI 318,966/month (F0254); 27,705 stars (F0002) | policies ACT, Diffusion, SmolVLA, pi0/pi0.5 ports, X-VLA (F0098) | gh huggingface; hf lerobot | README install path `pip install lerobot` (F0276) |
| mujoco | open | Apache-2.0 (F0003) | not archived, not fork (F0003) | 2026-09-20 (F0003) | 3.14.0, 2026-09-22 (F0319) | PyPI 3,790,114/month (F0255); 15,241 stars (F0003) | MJX (in-repo); MuJoCo Warp google-deepmind/mujoco_warp, Apache-2.0, pushed 2026-09-24 (F0005), PyPI mujoco-warp 372,480/month (F0257) | gh google-deepmind | `pip install mujoco` (F0277). Warp folded in as a backend of the same product line; say so if the maintainer wants it split |
| mujoco-playground | open | Apache-2.0 (F0004) | not archived, not fork (F0004) | 2026-09-19 (F0004) | v0.2.0, 2026-03-16 (F0388) | PyPI 9,928/month (F0256); 2,230 stars (F0004) | - | gh google-deepmind | `pip install playground` (F0286); PyPI repository_url matches (F0256) |
| isaac-lab | open | BSD-3-Clause (F0006) | not archived, not fork (F0006) | 2026-09-22 (F0006) | v3.0.0-EA, 2026-09-16 (F0321); 3.0 Beta 2 on 2026-06-23 (W0022) | PyPI 9,747/month (F0258); 8,196 stars (F0006) | Isaac Lab-Arena parked separately | gh isaac-sim | PyPI isaaclab repository_url = isaac-sim/IsaacLab (F0258); README does not show the pip line (F0287) |
| isaac-sim | open | Apache-2.0 for repo code; building/running needs NVIDIA components under the Isaac Sim Additional Software and Materials License (F0159). GitHub label `other` (F0007) | not archived, not fork (F0007) | 2026-06-22 (F0007) | v6.1.0, 2026-09-10 (F0322) | 3,533 stars (F0007); PyPI isaacsim 3,864/month but repository_url empty, not declared (F0259) | - | gh isaac-sim | Open code, proprietary runtime dependencies: flag for ladder placement |
| genesis | open | Apache-2.0 (F0091) | not archived, not fork (F0091) | 2026-09-25 (F0091) | v1.4.2, 2026-09-23 (F0323) | PyPI 97,931/month (F0260); 29,987 stars (F0091) | - | gh Genesis-Embodied-AI | Repo renamed Genesis -> genesis-world; canonical from ungh (F0085). `pip install genesis-world` (F0278) |
| maniskill | open | Apache-2.0 (F0092) | not archived, not fork (F0092) | 2026-08-04 (F0092) | v3.0.1, 2026-04-21 (F0324) | PyPI 19,481/month (F0261); 3,346 stars (F0092) | - | gh mani-skill | Moved haosulab/ManiSkill -> mani-skill/ManiSkill (F0090). README `pip install --upgrade mani_skill` (F0279) |
| habitat | open | MIT (F0010; habitat-lab MIT F0011) | not archived, not fork (F0010) | 2026-07-21 (F0010); habitat-lab 2026-05-07 (F0011) | v0.3.3, 2026-02-12 (F0325) | 3,823 stars (F0010); PyPI habitat-sim is a stale 2023 dev build, 195/month, not declared (F0274) | habitat-sim + habitat-lab (F0011) | gh facebookresearch | Pitched at the platform; sim and lab collapse into one row |
| robosuite | open | MIT text behind label `other` (F0160, F0012) | not archived, not fork (F0012) | 2026-07-11 (F0012) | v1.5.2, 2025-12-24 (F0326) | PyPI 322,909/month (F0262); 2,630 stars (F0012) | - | gh ARISE-Initiative | PyPI repository_url = ARISE-Initiative/robosuite (F0262); README fetched (F0280) shows no pip line |
| robocasa | open | MIT text behind label `other` (F0161, F0013) | not archived, not fork (F0013) | 2026-06-26 (F0013) | v1.0, 2026-02-18 (F0327) | 1,493 stars (F0013); no PyPI package (404, F0263) | - | gh robocasa | Built on robosuite; separate product (benchmark + sim assets) |
| robomimic | open | MIT (F0014) | not archived, not fork (F0014) | 2026-08-09 (F0014) | v0.5.0, 2025-06-27 (F0328); PyPI still 0.3.0 from 2023-07-04 (F0264) | PyPI 48,056/month (F0264); 1,563 stars (F0014) | - | gh ARISE-Initiative | Found while verifying robosuite's org; not in the brief |
| pybullet | open | zlib, except files under Extras and examples/ThirdPartyLibs (F0164); label `other` (F0015) | not archived, not fork (F0015) | 2025-10-22 (F0015) | GitHub 3.25, 2022-04-24 (F0329); PyPI 3.2.7, 2025-01-30 (F0265) | PyPI 638,067/month (F0265); 14,743 stars (F0015) | - | gh bulletphysics | README `pip install pybullet` (F0281). Slowing: last push 11 months ago |
| newton | open | Apache-2.0 (F0017) | not archived, not fork (F0017) | 2026-09-16 (F0017) | v1.6.0, 2026-09-10 (F0330) | 5,643 stars (F0017); PyPI newton-physics 566/month not declared, README does not name it (F0267, F0283) | - | gh newton-physics | Linux Foundation project from NVIDIA, Google DeepMind, Disney Research (W0020) |
| brax | open | Apache-2.0 (F0020) | not archived, not fork (F0020) | 2026-09-15 (F0020) | v0.14.2, 2026-03-15 (F0331) | PyPI 27,561/month (F0269); 3,237 stars (F0020) | - | gh google | README `pip install brax` (F0285) |
| mjlab | open | Apache-2.0 (F0021) | not archived, not fork (F0021) | 2026-09-16 (F0021) | v1.6.0, 2026-08-09 (F0332) | PyPI 84,063/month (F0270); 3,083 stars (F0021) | - | gh mujocolab | README carries the PyPI badge for mjlab (F0282) |
| robotwin | open | MIT (F0309) | not archived, not fork (F0309) | 2026-09-14 (F0309) | tag `release`, 2026-02-26 (F0333) | 2,868 stars (F0309) | RoboTwin 2.0 (ICML 2026, W0044) | gh RoboTwin-Platform | Bimanual data generator + benchmark; contested with benchmark_eval_data |
| roboverse | open | Apache-2.0 (F0310) | not archived, not fork (F0310) | 2026-09-22 (F0310) | v1.0.0-alpha, 2025-08-31 (F0389) | 1,863 stars (F0310); dataset RoboVerseOrg/roboverse_data 70,859 HF downloads (F0297) | - | gh RoboVerseOrg | Unified API over several simulators (W0044) |
| gr00t | open-weights | weights: NVIDIA Open Model License, 'ready for commercial/non-commercial use' (F0237); code Apache-2.0 (F0025, F0231); GR00T-N1.5-3B_Assemble_Trocar carries nvidia-oneway-noncommercial and nvidia/GR00T-H carries `nvidia-license`, whose link is the NVIDIA OneWay Noncommercial License (F0096) | not archived, not fork (F0025) | 2026-08-20 (F0025) | n1.6.1-release, 2026-04-23 (F0390) | HF 125,319/30d for GR00T-N1.7-3B (F0151); 8,121 stars (F0025) | N1-2B, N1.5-3B, N1.6-3B, N1.7-3B, GR00T-H, GR00T-H-N1.7 (F0096) | gh NVIDIA; hf nvidia | Ruled into 5a on 2026-09-25 (brief) |
| pi0 | open-weights | code Apache-2.0 (F0026, F0232); LeRobot ports of the weights carry `gemma` (F0098, F0153); PI's own checkpoint terms not fetched | not archived, not fork (F0026) | 2026-08-24 (F0026) | no GitHub releases recorded (F0391) | 13,932 stars (F0026); LeRobot port lerobot/pi0_base 39,973/30d (F0098) is not PI's artifact, not declared | pi0, pi0-FAST, pi0.5 (W0018, F0098). No open pi0.6 weights found in this run | gh Physical-Intelligence; hf physical-intelligence (only `fast` tokenizer, F0112) | Slug has no version token; pi0.5 is a release of the line |
| smolvla | open | Apache-2.0 on the card (F0152) | HF repo modified 2026-09-17 (F0152) | n/a (code lives in huggingface/lerobot, F0002) | HF lastModified 2026-09-17 (F0152) | HF 71,362/30d (F0152) | smolvla_base, smolvla_libero, smolvla_robotwin (F0098) | hf lerobot | Separate from the LeRobot framework row (model vs engine) |
| openvla | open-weights | MIT on code and card (F0027, F0113); Llama-2 base terms not fetched | not archived; fork=True of TRI-ML/prismatic-vlms (F0027) | 2025-03-23 (F0027) | no GitHub releases recorded (F0392) | HF 445,187/30d (F0113); 2,317 stars (F0027) | openvla-7b, LIBERO fine-tunes, v01-7b (F0113) | gh openvla; hf openvla | Dormant 18 months, yet the most-downloaded robotics model on the Hub (F0298). GitHub marks the repo a fork |
| octo | open | MIT (F0028, F0114) | not archived, not fork (F0028) | 2024-07-31 (F0028) | v1.5, 2024-05-24 (F0393) | HF 128/30d base-1.5, 346 small-1.5 (F0114); 1,789 stars (F0028) | octo-small, octo-base, 1.5 variants (F0114) | gh octo-models; hf rail-berkeley | Dormant since 2024-07 (matches the brief) |
| rdt | open | RDT2 Apache-2.0 (F0030, F0115); RDT-1B MIT (F0029, F0115) | not archived, not fork (F0030) | 2026-02-07 RDT2 (F0030); 2026-01-21 RDT-1 (F0029) | no GitHub releases recorded (F0394) | HF 218/30d RDT2-VQ, 546 rdt-1b (F0115); 806 + 1,804 stars (F0030, F0029) | rdt-170m, rdt-1b, RDT2-VQ, RDT2-FM (F0115) | gh thu-ml; hf robotics-diffusion-transformer | Governing release RDT2 |
| x-vla | open | Apache-2.0 (F0031, F0116) | not archived, not fork (F0031) | 2026-06-10 (F0031) | no GitHub releases recorded (F0395) | HF 10,921/30d (F0116); LeRobot port 4,459 (F0098) | X-VLA-Pt + 10 task fine-tunes (F0116) | gh 2toinf; hf 2toINF | Org per the sinanlabs index: Tsinghua AIR (F0001) |
| gigabrain | open | Apache-2.0 (F0032, F0156) | not archived, not fork (F0032) | 2026-02-13 (F0032) | no GitHub releases recorded (F0396) | HF 1,891/30d (F0156); 2,263 stars (F0032) | GigaBrain-0, 0.1, 0.7 (F0102) | gh open-gigaai; hf open-gigaai | Not in the brief; surfaced by search (W0023) |
| galaxea-g0 | open-weights | date-split: Apache-2.0 before 2026-01-04; G0 PLUS Community License (non-commercial + limited patent) to 2026-06-16; G0.5 Community License (non-commercial + limited patent) after (F0247). G0-VLA card cc-by-nc-sa-4.0 (F0099); G05 card g05-community-license, gated (F0155) | not archived, not fork (F0033) | 2026-08-13 (F0033) | no GitHub releases recorded (F0397) | HF 0/30d on all three repos (F0099); 799 stars (F0033) | G0 (Plus 3B, Tiny 250M), G0.5 (W0023, F0099) | gh OpenGalaxea; hf OpenGalaxea | Custom NC licenses: flag. Adoption instrument reads zero |
| lingbot-vla | open | Apache-2.0 (F0034, F0235; card body F0240) | not archived, not fork (F0034) | 2026-06-11 (F0034) | no GitHub releases recorded (F0398) | HF 1,249/30d 4b, 1,245 v2-6b (F0100); 1,837 stars (F0034) | lingbot-vla-4b, -depth, v2-6b (F0100) | gh Robbyant; hf robbyant | Robbyant is Ant Group's embodied unit per F0001; reuse ant-group org? (question 6) |
| internvla | open-weights | CC BY-NC-SA 4.0, copyright Shanghai AI Laboratory (F0211); weights cc-by-nc-sa-4.0 (F0101); M1 code MIT (F0035) | not archived, not fork (F0093) | 2026-09-14 (F0093) | no GitHub releases recorded (F0399) | HF 125/30d A1.5-base, 111 M1 (F0101); 558 stars (F0093) | InternVLA-M1, A1-3B, A1.5, N1 navigation (F0101) | gh InternRobotics; hf InternRobotics | Repo renamed InternVLA-A1 -> InternVLA-A-series (F0087) |
| wall-oss | open-weights | code Apache-2.0 (F0037, F0234); weights card states no license (F0148, F0239) | not archived, not fork (F0037) | 2026-09-18 (F0037) | no GitHub releases recorded (F0400) | HF 998/30d (F0148); 1,278 stars (F0037) | wall-oss-flow, -fast, -0.5, -flow-0.1 (F0117) | gh X-Square-Robot; hf x-square-robot | Weights license unstated |
| molmoact | open-weights | code Apache-2.0 (F0038, F0233); MolmoAct 1 weights apache-2.0 (F0118); MolmoAct2 card has no license field (F0150, F0238) | not archived, not fork (F0038) | 2026-05-11 (F0038) | no GitHub releases recorded (F0401) | HF 20,533/30d MolmoAct2 (F0150); 389 stars (F0038) | MolmoAct-7B-D (2025), MolmoAct2, -Think, -SO100_101, -DROID (F0118) | gh allenai; hf allenai | MolmoAct2 (2026-05) not in the brief; index also has an `ai2` org slug (question 6) |
| cogact | open | MIT (F0039, F0119) | not archived, not fork (F0039) | 2025-10-30 (F0039) | no GitHub releases recorded (F0402) | HF 968/30d (F0119); 433 stars (F0039) | Small, Base, Large (F0119) | gh microsoft; hf CogACT | - |
| spatialvla | open | MIT in README (F0248), no GitHub label (F0040); card MIT (F0120) | not archived, not fork (F0040) | 2025-06-23 (F0040) | no GitHub releases recorded (F0403) | HF 1,307/30d (F0120); 727 stars (F0040) | 4b-224-pt, -mix, bridge/fractal SFT (F0120) | gh SpatialVLA; hf IPEC-COMMUNITY | Org attribution (Shanghai AI Lab et al.) from F0001 only |
| univla | open | Apache-2.0 (F0041, F0121) | not archived, not fork (F0041) | 2025-11-19 (F0041) | no GitHub releases recorded (F0404) | HF 240/30d (F0121); 1,134 stars (F0041) | univla-7b + SFT variants (F0121) | gh OpenDriveLab; hf qwbu | - |
| go-1 | open-weights | CC BY-NC-SA 4.0 on the card (F0241) | HF modified 2025-09-21 (F0147) | n/a (HF only declared) | HF lastModified 2025-09-21 (F0147) | HF 123/30d (F0147) | GO-1, GO-1-Air (F0110) | hf agibot-world | Code sits in OpenDriveLab/AgiBot-World (F0001), which the agibot-world dataset row claims; so no github here |
| rynnvla | open | Apache-2.0 in README (F0251); RynnVLA-001 Apache-2.0 (F0043, F0135) | not archived, not fork (F0094) | 2025-12-02 RynnVLA-002 (F0094); 2026-01-23 RynnVLA-001 (F0043) | no GitHub releases recorded (F0405) | HF 13/30d (F0135); 1,131 stars (F0094) | RynnVLA-001, RynnVLA-002 (formerly WorldVLA: alibaba-damo-academy/WorldVLA redirects here, F0088; HF WorldVLA F0133) | gh alibaba-damo-academy; hf Alibaba-DAMO-Academy | WorldVLA is now a retired alias of this line |
| xiaomi-robotics | open | Apache-2.0 (F0044, F0103) | not archived, not fork (F0044) | 2026-08-03 (F0044) | no GitHub releases recorded (F0406) | HF 88/30d 0-Pretrain; 785 Robotics-1-RoboCasa365 (F0103); 659 stars (F0044) | Xiaomi-Robotics-0, -1 (5B), -U0 (F0103) | gh XiaomiRobotics; hf XiaomiRobotics | 2026 release not in the brief (W0001) |
| being-h | open | code MIT (F0045); Being-H0 weights MIT, Being-H0.5 weights apache-2.0 (F0123) | not archived, not fork (F0045) | 2026-05-04 (F0045) | no GitHub releases recorded (F0407) | HF 53/30d (F0123); 59 stars (F0045) | Being-H0 1B/8B/14B, Being-H0.5-2B (F0123) | gh BeingBeyond; hf BeingBeyond | Small signal |
| spirit-vla | open | code MIT (F0046); weights apache-2.0 (F0124) | not archived, not fork (F0046) | 2026-05-29 (F0046) | no GitHub releases recorded (F0408) | HF 145/30d (F0124); 661 stars (F0046) | Spirit-v1.5 (F0124) | gh Spirit-AI-Team; hf Spirit-AI-robotics | Slug `spirit` alone is too generic |
| hy-embodied-vla | open | Apache-2.0 with a Tencent header (F0316); label `other` (F0305); card apache-2.0 (F0300) | not archived, not fork (F0305) | 2026-08-04 (F0305) | no GitHub releases recorded (F0409) | HF 262/30d (F0300); 301 stars (F0305) | Hy-Embodied-0.5-VLA-UMI, -RoboTwin; dataset Hy-Embodied-0.5-VLA-Data (W0035) | gh Tencent-Hunyuan; hf tencent | 2026-06 release not in the brief (W0035). The Hy-Embodied VLMs are parked to multimodal_models |
| unifolm-vla | open-weights | CC BY-NC-SA 4.0 on the card (F0243) | HF modified 2026-03-06 (F0157) | n/a (HF only) | HF lastModified 2026-03-06 (F0157) | HF 175/30d (F0157) | UnifoLM-VLA-Base, -Libero (F0111) | hf unitreerobotics | Unitree's own VLA; Unitree SDKs parked |
| alpamayo | open | code Apache-2.0 (F0303); weights openmdw-1.1 (F0299) | not archived, not fork (F0303) | 2026-09-09 (F0303) | no GitHub releases recorded (F0410) | HF 30,625/30d (F0299); 2,028 stars (F0303) | Alpamayo-R1-10B, 1.5-10B, 2-Super (F0299, W0034) | gh NVlabs; hf nvidia | Driving VLA: in only if autonomous driving counts as embodied (question 3) |
| eo-1 | open | MIT on the card (F0120) | HF modified 2026-01-14 (F0120) | n/a (HF only) | HF lastModified 2026-01-14 (F0120) | HF 968/30d (F0120) | EO-1-3B, eo1-qwen25_vl bridge/fractal (F0120) | hf IPEC-COMMUNITY | GitHub IPEC-PUBLIC/EO-1 named in F0001, not fetched, not declared |
| nora | open-weights | card states no license (F0132) | HF modified 2025-08-27 (F0132) | n/a (HF only) | HF lastModified 2025-08-27 (F0132) | HF 600/30d nora, 359 nora-long (F0132) | nora, nora-long, LIBERO fine-tunes (F0132) | hf declare-lab | License absent: record, do not assume |
| roboflamingo | open | MIT (F0047) | not archived, not fork (F0047) | 2024-05-08 (F0047) | no GitHub releases recorded (F0411) | 437 stars only (F0047) | - | gh RoboFlamingo | Dormant 28 months; brief lead |
| vla-jepa | open | README badge Code License Apache-2.0 (F0253); no GitHub label (F0048); card apache-2.0 (F0125) | not archived, not fork (F0048) | 2026-05-01 (F0048) | no GitHub releases recorded (F0412) | HF 0/30d (F0125); 199 stars (F0048) | ported as lerobot/VLA-JEPA-Pretrain (W0011) | gh ginwind; hf ginwind | Brief lists it under 5b; it outputs actions, so it lands here (world model is internal) |
| gemini-robotics | closed | proprietary; no weights (W0036) | live product page (W0036) | n/a | Gemini Robotics ER 2 announced 2026-07-30, public via Gemini API (W0015) | none measurable (hosted API; trusted-tester program of 100+, W0036) | Gemini Robotics 2, ER 2, On-Device 2 (W0036) | - | Closed frontier comparator; capability surface = the robotics model family, not Gemini |
| open-x-embodiment | open | repo Apache-2.0 (F0049); per-dataset terms not fetched | not archived, not fork (F0049) | 2025-11-05 (F0049) | no GitHub releases recorded (F0413) | 2,045 stars (F0049); LeRobot-format mirrors of member sets 130k-220k HF downloads (F0297), not declared | 58 constituent datasets (W0021) | gh google-deepmind | - |
| droid | open | HF card apache-2.0 (F0290); GitHub carries no license label or README line (F0050, F0250) | not archived, not fork (F0050) | 2025-09-15 (F0050) | HF lastModified 2026-06-25 (F0290) | HF 16,522/30d lerobot/droid_1.0.1 (F0290); cadene/droid_1.0.1 252,508 (F0297) | 92,223 episodes (W0032) | gh droid-dataset; hf lerobot | Declared HF id is the LeRobot-format release, not a DROID-team repo |
| robomind | open | apache-2.0 on the card, gated (F0292) | HF modified 2026-04-14 (F0292) | n/a | HF lastModified 2026-04-14 (F0292) | HF 59,850/30d (F0292) | - | hf x-humanoid-robomind | Gated behind contact sharing (W0032) |
| agibot-world | open | CC BY-NC-SA 4.0 (README F0249; gated prompt F0293); AgiBotWorld2026 cc-by-nc-sa-4.0 (F0294) | not archived, not fork (F0042) | 2026-05-29 (F0042) | no GitHub releases recorded (F0415) | HF 92,675/30d Beta (F0293); AgiBotWorld2026 266,412 (F0294); Alpha 35,703 (F0295) | Alpha (2024-12), Beta, AgiBotWorld2026 (F0293-F0295) | gh OpenDriveLab; hf agibot-world | Dataset versions may each be their own identity (question 5). Status `open` means downloadable; NC license |
| nvidia-physical-ai-dataset | open | cc-by-4.0 (F0296) | HF modified 2026-03-05 (F0296) | n/a | HF lastModified 2026-03-05 (F0296) | HF 1,267,768/30d (F0296): top robotics dataset on the Hub (F0297) | GR00T-X-Embodiment-Sim, Open-H-Embodiment 176,135 (F0296) | hf nvidia | Pitched at NVIDIA's named collection (W0021) |
| interndata-a1 | open | CC BY-NC-SA 4.0 (gated community prompt, F0302) | HF dataset live (F0302) | n/a | released 2025-07-26 per license prompt (F0302) | HF 113,556/30d (F0302) | - | hf InternRobotics | Surfaced by the HF robotics-dataset sort (F0297) |
| so-101 | open | Apache-2.0 (F0051) | not archived, not fork (F0051) | 2026-09-06 (F0051) | v0.1.1, 2024-05-17 (F0416) | 7,401 stars (F0051); no download channel | repo carries SO-100 and SO-101 (F0317) | gh TheRobotStudio | Hardware: generation is identity, so SO-100 is parked as the prior generation sharing this repo |
| koch-v1-1 | open | Apache-2.0 (F0052) | not archived, not fork (F0052) | 2024-09-17 (F0052) | no GitHub releases recorded (F0417) | 621 stars (F0052) | - | gh jess-moss | Dormant 2 years; LeRobot documents it (W0033) |
| reachy-mini | open | Apache-2.0 (F0053) | not archived, not fork (F0053) | 2026-09-21 (F0053) | v1.10.0rc6, 2026-08-13 (F0418) | 1,515 stars (F0053); PyPI reachy-mini 12,028/month not declared (no repository_url, F0273) | Lite, Wireless (W0019) | gh pollen-robotics | Pollen Robotics / Hugging Face desktop robot (W0019) |
| aloha | open | MIT (F0054) | not archived, not fork (F0054) | 2024-04-19 (F0054) | no GitHub releases recorded (F0419) | 2,274 stars (F0054) | - | gh tonyzhaozh | First generation, dormant; org is a personal handle (question 6) |
| aloha-2 | open | 'open source all hardware designs' (F0442, F0443); license text not fetched | project page live (F0443) | n/a | arXiv submitted 2024-02-07 (F0442) | none measurable | MuJoCo model included (F0442) | - | Google DeepMind + Stanford (W0033). Weakest-evidence row (hardware, no repo) |
| berkeley-humanoid-lite | open | MIT (F0055) | not archived, not fork (F0055) | 2026-03-10 (F0055) | v1.1.0, 2025-09-07 (F0420) | 1,878 stars (F0055) | - | gh HybridRobotics | Sub-$5,000 open humanoid (W0019) |
| lekiwi | open | Apache-2.0 (F0056) | not archived, not fork (F0056) | 2025-07-10 (F0056) | no GitHub releases recorded (F0421) | 803 stars (F0056) | - | gh SIGRobotics-UIUC | - |
| openarm | open | Apache-2.0 (F0057) | not archived, not fork (F0057) | 2026-09-14 (F0057) | 1.1, 2025-10-31 (F0422) | 3,369 stars (F0057) | - | gh enactic | $6,500 bimanual system (W0033) |

### 6c. Source list

See the combined source list at the end of this document (§D). Every id in 6b resolves there.

## 7. Parked candidates

| name | reason | source ids | fetch date |
|---|---|---|---|
| SO-100 arm | SKU of SO-101 line: prior hardware generation in the same repo (F0317); keep only if generations stay separate | F0317, F0051 | 2026-09-26 |
| Gazebo (gz-sim) | boundary: general robotics simulator with no learning surface; maintainer call (question 2) | F0016, W0004 | 2026-09-26 |
| Webots | boundary: general robotics simulator (question 2) | F0019, W0005 | 2026-09-26 |
| Drake | boundary: model-based planning/control toolbox, not a learning stack (question 2) | F0018, F0170, F0268 | 2026-09-26 |
| CARLA | boundary: autonomous-driving simulator (question 3) | F0022, F0272 | 2026-09-26 |
| ROS 2 | boundary: robotics middleware, not AI | F0059 | 2026-09-26 |
| dora-rs | boundary: robotics dataflow middleware, not AI | F0312, W0044 | 2026-09-26 |
| Gymnasium | boundary -> ml_frameworks: generic RL environment API, most envs are not physical | F0023, F0271 | 2026-09-26 |
| Isaac Lab-Arena | boundary -> evaluation_code: policy evaluation harness | F0311, W0044 | 2026-09-26 |
| LIBERO | boundary -> benchmark_eval_data: benchmark suite | F0060, F0297 | 2026-09-26 |
| Diffusion Policy | unmaintained: last push 2024-12-24; the method ships inside LeRobot (lerobot/diffusion_pusht) | F0024, F0098 | 2026-09-26 |
| Unitree SDK2 | boundary: vendor device SDK for closed hardware | F0058, F0275 | 2026-09-26 |
| Gemini Robotics On-Device | SKU of gemini-robotics | W0015, W0036 | 2026-09-26 |
| RynnBrain | boundary -> multimodal_models: embodied-reasoning VLM, no action head | F0122, W0043 | 2026-09-26 |
| Hy-Embodied VLM | boundary -> multimodal_models: embodied VLM | F0300, W0035 | 2026-09-26 |
| UnifoLM-ER | boundary -> multimodal_models: embodied-reasoning model | F0111 | 2026-09-26 |
| RLDX (RLWRLD) | no addressable artifact: announced as future open source | W0001 | 2026-09-26 |
| A1 (truncated VLA) | no addressable artifact verified: paper only in this run | W0001 | 2026-09-26 |
| Dream-VLA | no addressable artifact verified: paper only | W0001 | 2026-09-26 |
| Pelican-VLA | no addressable artifact verified: paper only | W0001 | 2026-09-26 |
| GraspVLA | coverage limit: listed in the sinanlabs index (CC BY-NC 4.0 per index), not independently fetched | F0001 | 2026-09-26 |
| DexVLA | coverage limit: index entry only | F0001 | 2026-09-26 |
| GR-1 (ByteDance) | coverage limit: index entry only; last activity 2023 per index | F0001 | 2026-09-26 |
| VLA-0 (NVIDIA Research) | coverage limit: index entry only | F0001 | 2026-09-26 |
| MiniVLA | coverage limit: index entry only; derivative of OpenVLA | F0001 | 2026-09-26 |
| HPT | coverage limit: index entry only | F0001 | 2026-09-26 |
| LAPA | coverage limit: index entry only | F0001 | 2026-09-26 |
| LLaVA-VLA | coverage limit: index entry only | F0001 | 2026-09-26 |
| RoboVLMs | coverage limit: index entry only | F0001 | 2026-09-26 |
| Magma (Microsoft) | boundary -> multimodal_models: agentic VLM (index entry) | F0001 | 2026-09-26 |
| VLA-Adapter | coverage limit: index entry only; adapter method | F0001 | 2026-09-26 |
| LeRobot datasets (hub collection) | identity unclear: a hub organization, not one dataset | W0002, F0098 | 2026-09-26 |
| BridgeData V2 | coverage limit: only a third-party RLDS mirror seen (shihao1895/bridge-rlds) | F0297 | 2026-09-26 |
| 10Kh-RealOmin-OpenData (genrobot2025) | coverage limit: in the HF robotics-dataset top 40, not researched | F0297 | 2026-09-26 |
| Hy-Embodied-0.5-VLA-Data | SKU of hy-embodied-vla | F0297, W0035 | 2026-09-26 |
| AlohaMini | coverage limit: surfaced once, not fetched | W0033 | 2026-09-26 |
| Hope Jr / Trossen ViperX / Hello Stretch / Unitree G1 | closed long-tail or not fetched: named in one buyers-guide summary only | W0019 | 2026-09-26 |
| DreamZero-DROID (GEAR-Dreams) | coverage limit: in the HF robotics-model top 60, not researched | F0298 | 2026-09-26 |
| RoboBrain2.0 (BAAI) | boundary -> multimodal_models: embodied brain VLM; in HF top 60, not researched | F0298 | 2026-09-26 |
| PhysBrain1.5 | coverage limit: seen only as third-party GGUF quantizations in HF top 60 | F0298 | 2026-09-26 |
| GraspMolmo (Ai2) | coverage limit: grasp-prediction model in HF top 60, not researched | F0298 | 2026-09-26 |
| SimVLA | coverage limit: LIBERO checkpoint in HF top 60, not researched | F0298 | 2026-09-26 |
| ACE-Data-0 | coverage limit: HF robotics-dataset top 40, not researched | F0297 | 2026-09-26 |
| ABC-130k | coverage limit: HF robotics-dataset top 40, not researched | F0297 | 2026-09-26 |
| stereo-550 | coverage limit: HF robotics-dataset top 40, not researched | F0297 | 2026-09-26 |
| Gen-HumanEgo | coverage limit: HF robotics-dataset top 40 (egocentric human data), not researched | F0297 | 2026-09-26 |
| HiFi-UMI-2K | coverage limit: HF robotics-dataset top 40, not researched | F0297 | 2026-09-26 |
| xperience-10m | coverage limit: HF robotics-dataset top 40, not researched | F0297 | 2026-09-26 |
| OmniAction (OpenMOSS) | coverage limit: HF robotics-dataset top 40, not researched | F0297 | 2026-09-26 |
| L2D (yaak-ai) | coverage limit: driving dataset in HF top 40; depends on question 3 | F0297 | 2026-09-26 |
| Retargeted AMASS (fleaven, 3 repos) | coverage limit: motion-retargeting data in HF top 40, not researched | F0297 | 2026-09-26 |
| MolmoAct-Midtraining-Mixture | SKU of molmoact (training mixture) | F0297 | 2026-09-26 |
| DOM / deform360 / tracker-pov / MetaFold / grand_tour_dataset / trex_dataset | coverage limit: HF robotics-dataset top 40, not researched | F0297 | 2026-09-26 |
| computer-use-large (markov-ai) | boundary: computer-use agent data, not physical | F0297 | 2026-09-26 |

## 8. Reconciled counts

A *signal* is one source id that surfaced a candidate (the `src` list per candidate in `spec.py`,
plus each parked row's source ids). Duplicate signals are the extra surfacings of a candidate
already seen. In Part B, candidates already counted in Part A (VLA-JEPA, GR00T, RynnVLA-002,
WorldVLA) are counted as duplicate signals only, listed separately in Part B §7.

- raw_signals = 174 = duplicate_signals 60 + unique_candidates 114
- unique_candidates = 114 = accepted 60 + parked 54

## 9. Open questions for the maintainer

1. **One category or a split?** Keep `robotics_embodied` as one category with a per-type ladder map, or split it into `robot_foundation_models` (29 models) + `robot_learning_sim` (17 software)? **Recommend one:** hardware (8) can't stand alone, and the shared litmus holds. Datasets are researched at 6, but with 16 parked, unresearched HF datasets their supply is a floor, so a datasets-only split isn't ruled out by supply.
2. **General robotics tools with no learning surface** (Gazebo, Webots, Drake, ROS 2): in or out? **Recommend out.** They are parked now; the AI-stack framing is the reason.
3. **Autonomous driving:** is a driving VLA (Alpamayo) or driving simulator (CARLA) "embodied"? **Recommend yes**, which also promotes CARLA from parked. The alternative is to exclude both.
4. **Robot datasets:** here, or in `training_synthetic_datasets`? **Recommend here.** Their consumers are the VLAs in this category.
5. **Dataset versions:** AgiBot World Alpha, Beta and 2026 as one row or three? **Recommend one row.** All three are CC BY-NC-SA 4.0 (F0293–F0295). Split only if a later release changes terms.
6. **Org slugs:** use `ant-group` for Robbyant (affiliation from F0001 only), and settle `allen-institute-for-ai` vs `ai2` (both exist in the index). Personal handles (tonyzhaozh, jess-moss, ginwind) are used for academic projects. **Recommend:** keep `robbyant` until a primary source confirms, use `allen-institute-for-ai`, and keep the handles.
7. **Isaac Sim openness:** the Apache-2.0 code needs proprietary NVIDIA runtime components (F0159). Tier it by the code or by the runtime? **Recommend by the code**, with the dependency recorded on the score.
8. **SO-100:** a separate product from SO-101 under the hardware-generation rule, even though both share one repo? **Recommend no row for SO-100** until something distinguishes their adoption.
9. **Placement:** a new group **"Embodied & world models"** inside *Model components*, holding `robotics_embodied` and `world_models`, or a new arc? **Recommend the group.** The arcs are the three Columbia layers and robotics adds no layer.

---

# Part B — World models (`world_models`)

## 1. Verdict

**GO-WITH-CHANGES: create it as its own category, next to `robotics_embodied`.** The July count
(about 4 product lines from 2 vendors) no longer holds. This run accepts **21 product lines from
20 organizations**; the largest vendor share is 9.5%, and 19 lines were active in the
last 12 months. Two populations came in since July. The first is robot world models used as data
engines and policy evaluators: BWM, Genie Envisioner, UnifoLM-WMA, GigaWorld, Ctrl-World, RynnWorld,
and Cosmos 3 (2026-06-01). The second is interactive, real-time game and scene world models:
Matrix-Game 3.0, LingBot-World, Yume, Hunyuan-GameCraft, HY-World 2.0 and DreamX-World. Folding them
into 5a would break 5a's litmus, because half the set simulates virtual game worlds rather than a
physical one. Parking them again would ignore nineteen live lines. The changes needed are a
tightened litmus that names what counts as an action (question 10), and decisions on the contested
seams with `media_generation`, `multimodal_models` and `classic_ml_cv`. One caution: adoption is
thin. 12 of the 17 lines with an HF artifact declared show fewer than 200 downloads in 30 days,
and several are single research drops.

## 2. Fit metrics (computed from section 6 by `gen.py`)

- accepted candidates: 21  (open: 12, open-weights: 7, source-available: 0, closed: 2)
- by type: model 21
- independent organizations: 20; largest org's share: 9.5% (tencent, 2 rows)
- candidates active in the last 12 months (a dated push or release on/after 2025-09-26; a closed product counts when its product page is live): 19 of 21 (1 of them only by the live-page rule)
- candidates with a usage instrument (PyPI or HF downloads) declared: 17 of 21; the rest are stars-only or unmeasured
- product lines: 21; vendors: 20; largest-vendor share: 9.5% (Tencent: HY-World + Hunyuan-GameCraft)
- sub-populations: robot/physical world models 9 (cosmos, v-jepa, genie-envisioner, unifolm-wma, gigaworld, ctrl-world, boundless-world-model, rynnworld, aether); interactive game/scene world models 8 (hy-world, hunyuan-gamecraft, matrix-game, lingbot-world, oasis, yume, dreamx-world, diamond); model-based RL latent world models 2 (dreamer, td-mpc); closed frontier 2 (genie, runway-gwm)
- retrieval cutoff: see the header.

## 3. Boundary

- **Definition:** Models that learn a predictive model of an environment and can be rolled forward under an agent's actions.
- **Litmus:** Given a state and an action, does it predict the next state (pixels, latents or 3D)?
- **Exclusions:**
  - Text-to-video or text-to-3D with no action input belongs to `media_generation`: World Labs Marble generates static, editable 3D worlds (W0040).
  - Policies that output actions go to `robotics_embodied`, even when a world model sits inside them (VLA-JEPA, RynnVLA-002/WorldVLA, GigaBrain).
  - Code/LLM "world model" training (CWM) belongs to `base_pretrained`.
  - Web-environment world models (WebWorld) are out unless question 10 widens the scope.

**Contested products:**

| product | where it is now | recommendation | reason |
|---|---|---|---|
| V-JEPA | absent (candidate: `classic_ml_cv` vision backbones, sibling) | here | V-JEPA 2-AC is action-conditioned (F0001). The encoder checkpoints are what gets downloaded (F0109), so flag it to the classic_ml_cv sweep |
| Cosmos (Reason part) | absent (candidate: `multimodal_models`, sibling) | here as one row | Cosmos 3 unifies reasoning, generation and action prediction (W0010); Reason 2.x is a VLM SKU |
| Cosmos (Predict part), Hunyuan-GameCraft, Matrix-Game, Yume, DreamX-World, Oasis | absent (candidate: `media_generation`, sibling) | here | Action/keyboard/camera-conditioned rollouts pass the litmus; plain T2V does not |
| HY-World 1.0 / 2.0 (3D generation), Matrix-3D, Marble | absent | 1.0/2.0 stay inside `hy-world`; Matrix-3D and Marble → `media_generation` | 3D scene generation without actions fails the litmus |
| Genie Envisioner, UnifoLM-WMA, GigaWorld, BWM, Ctrl-World, RynnWorld | absent (could sit in 5a) | here | They predict the next observation from robot actions: world models serving robotics |
| GR00T (and GR00T Dreams) | ruled to 5a | stay in 5a | Ruled 2026-09-25 |
| VLA-JEPA, RynnVLA-002 (ex-WorldVLA) | brief listed under 5b | → `robotics_embodied` | They output actions |

## 4. Capability quantity

**Controllable rollout: how much of a world you can drive, and for how long.** (1) latent-only
action-conditioned prediction used for planning (Dreamer, TD-MPC, V-JEPA 2-AC) → (2) short-horizon
action-conditioned video in a narrow domain (DIAMOND, Oasis 500M, Ctrl-World) → (3) real-time
streaming interactive generation with long-horizon memory (Matrix-Game 3.0, W0009; LingBot-World;
Yume) or robot-action-conditioned simulators used as data engines (BWM, first among open models on
WorldArena Track 1, W0042; GigaWorld; UnifoLM-WMA) → (4) an open omnimodal world model spanning
reasoning, generation and action prediction: **Cosmos 3** (W0010), the top open anchor → (5) the closed
frontier, real-time photoreal worlds that stay controllable and accept promptable events:
**Genie 3** (W0037), with Runway GWM-1 alongside it (W0039). Rung 3 holds two populations (games
and robots) that one quantity orders only loosely. Record it, and let the ladder builder decide
whether the rung needs splitting.

## 5. Scoring ladder inputs

- Ladder needed: `model` for all 21 (Cosmos and V-JEPA could argue for `pretrained`, since both are trained from raw video; flag for the ladder builder).
- License strings met (**custom or unusual in bold**):
  - Apache-2.0: lingbot-world v1, yume, gigaworld, boundless-world-model (code), dreamx-world (code), rynnworld (HF cards), matrix-game (3.0 weights), v-jepa (ViT-g weights)
  - MIT: v-jepa (code + ViT-L/H), matrix-game (repo, 1.0/2.0), oasis (500M), diamond, aether, ctrl-world, dreamer, td-mpc, dreamx-world (weights)
  - **OpenMDW-1.1**: cosmos (Cosmos 3). **NVIDIA Open Model License**: cosmos (2.x SKUs, gated)
  - **Tencent HY-World 2.0 / HunyuanWorld-1.0 / HunyuanWorld-Voyager / HY-WorldPlay Community Licenses** (exclude EU, UK, South Korea): hy-world
  - **Tencent Hunyuan Community License**: hunyuan-gamecraft
  - **CC BY-NC-SA 4.0**: lingbot-world v2 (current), genie-envisioner, unifolm-wma (code; HF card says apache-2.0, a conflict)
  - **LTX-Video Open Weights License** (inherited): genie-envisioner base weights
  - **No license stated**: boundless-world-model HF card, diamond HF card
  - proprietary: genie, runway-gwm (and the parked Oasis 3)

## 6. Accepted candidates

### 6a. Registry rows

Paste-ready file: `rows.world_models.yaml` (validated). Contents:

```yaml
category: world_models
products:
- slug: cosmos
  display_name: NVIDIA Cosmos
  type: model
  org: nvidia
  github: NVIDIA/cosmos
  huggingface_model: nvidia/Cosmos3-Nano
- slug: v-jepa
  display_name: V-JEPA
  type: model
  org: meta
  github: facebookresearch/vjepa2
  huggingface_model: facebook/vjepa2-vitg-fpc64-256
- slug: hy-world
  display_name: HY-World (HunyuanWorld)
  type: model
  org: tencent
  github: Tencent-Hunyuan/HY-World-2.0
  huggingface_model: tencent/HY-World-2.0
- slug: hunyuan-gamecraft
  display_name: Hunyuan-GameCraft
  type: model
  org: tencent
  github: Tencent-Hunyuan/Hunyuan-GameCraft-1.0
  huggingface_model: tencent/Hunyuan-GameCraft-1.0
- slug: matrix-game
  display_name: Matrix-Game
  type: model
  org: skywork
  github: SkyworkAI/Matrix-Game
  huggingface_model: Skywork/Matrix-Game-3.0
- slug: lingbot-world
  display_name: LingBot-World
  type: model
  org: robbyant
  github: Robbyant/lingbot-world
  huggingface_model: robbyant/lingbot-world-fast
- slug: oasis
  display_name: Oasis (open 500M)
  type: model
  org: etched
  github: etched-ai/open-oasis
  huggingface_model: Etched/oasis-500m
- slug: diamond
  display_name: DIAMOND
  type: model
  org: eloialonso
  github: eloialonso/diamond
  huggingface_model: eloialonso/diamond
- slug: yume
  display_name: Yume
  type: model
  org: stdstu12
  github: stdstu12/YUME
  huggingface_model: stdstu123/Yume-I2V-540P
- slug: aether
  display_name: Aether
  type: model
  org: shanghai-ai-laboratory
  github: InternRobotics/Aether
  huggingface_model: AetherWorldModel/AetherV1
- slug: genie-envisioner
  display_name: Genie Envisioner
  type: model
  org: agibot
  github: AgibotTech/Genie-Envisioner-V1
  huggingface_model: agibot-world/Genie-Envisioner-v1.0
- slug: unifolm-wma
  display_name: UnifoLM-WMA
  type: model
  org: unitree
  github: unitreerobotics/unifolm-world-model-action
  huggingface_model: unitreerobotics/UnifoLM-WMA-0-Base
- slug: gigaworld
  display_name: GigaWorld
  type: model
  org: gigaai
  github: open-gigaai/giga-world-0
  huggingface_model: open-gigaai/GigaWorld-0-Video-Pretrain-2b
- slug: ctrl-world
  display_name: Ctrl-World
  type: model
  org: robert-gyj
  github: Robert-gyj/Ctrl-World
  huggingface_model: yjguo/Ctrl-World
- slug: boundless-world-model
  display_name: Boundless World Model (BWM)
  type: model
  org: blm-lab
  github: boundless-large-model/boundless-world-model
  huggingface_model: BLM-Lab/Boundless-World-Model
- slug: dreamer
  display_name: Dreamer
  type: model
  org: danijar
  github: danijar/dreamerv3
- slug: td-mpc
  display_name: TD-MPC
  type: model
  org: nicklashansen
  github: nicklashansen/tdmpc2
- slug: rynnworld
  display_name: RynnWorld
  type: model
  org: alibaba-damo-academy
  github: alibaba-damo-academy/RynnWorld-4D
  huggingface_model: Alibaba-DAMO-Academy/RynnWorld-Teleop
- slug: dreamx-world
  display_name: DreamX-World
  type: model
  org: amap
  github: AMAP-ML/DreamX-World
  huggingface_model: GD-ML/DreamX-World-5B
- slug: genie
  display_name: Genie
  type: model
  org: google
  homepage: https://deepmind.google/models/genie/
- slug: runway-gwm
  display_name: Runway GWM
  type: model
  org: runway
  homepage: https://runway.com/research/introducing-runway-gwm-1
```

### 6b. Evidence table

| slug | open status | license(s) + source | archived/fork | last push | last release | adoption signal | member checkpoints/SKUs | org GitHub/HF handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| cosmos | open | Cosmos 3: OpenMDW-1.1 (LICENSE F0195; cards openmdw1.1-license F0144); earlier Predict/Transfer/Reason 2.x: NVIDIA Open Model License, gated=auto (F0145, F0097) | not archived, not fork (F0061) | 2026-09-23 (F0061) | Cosmos3, 2026-06-01 (F0423) | HF 126,107/30d Cosmos3-Nano (F0144); Cosmos3-Edge 1,380,628 (F0097); 11,904 stars (F0061) | Cosmos3 Edge/Nano/Super; Predict 2/2.5, Transfer 2.5, Reason 1/2, Embed1 (F0097); nvidia-cosmos/cosmos-predict2.5 (F0062) | gh NVIDIA, nvidia-cosmos; hf nvidia | Governing release Cosmos 3 (OpenMDW, permissive). Cosmos-Reason is a VLM: contested with multimodal_models |
| v-jepa | open | code MIT (F0063); weights MIT (ViT-L/H) and apache-2.0 (ViT-g) (F0109) | not archived, not fork (F0063) | 2026-03-23 (F0063) | no GitHub releases recorded (F0424) | HF 200,430/30d vitl, 113,699 vitg (F0109); 4,472 stars (F0063) | V-JEPA 2 ViT-L/H/g, V-JEPA 2-AC action-conditioned (F0001), 2.1 (W0011) | gh facebookresearch; hf facebook | Encoder checkpoints dominate downloads: overlaps classic_ml_cv vision backbones |
| hy-world | open-weights | Tencent HY-World 2.0 Community License, excludes EU/UK/South Korea (F0200). HunyuanWorld-1.0, Voyager, WorldPlay: own Tencent community licenses (F0196, F0201, F0206) | not archived, not fork (F0065) | 2026-08-12 (F0065) | no GitHub releases recorded (F0425) | HF 3,790/30d HY-World-2.0 (F0104); HunyuanWorld-1 4,818 (F0138); 2,674 stars (F0065) | HunyuanWorld-1.0, HunyuanWorld-Voyager (camera-conditioned), HY-WorldPlay (interactive), HY-World 2.0 (F0138-F0140, F0306) | gh Tencent-Hunyuan; hf tencent | 1.0 and 2.0 generate 3D scenes (fails the litmus alone); Voyager is conditioned on camera input (W0017); WorldPlay examined for license only |
| hunyuan-gamecraft | open-weights | Tencent Hunyuan Community License, excludes EU/UK/South Korea (F0202) | not archived, not fork (F0067) | 2025-11-28 (F0067) | no GitHub releases recorded (F0426) | HF 77/30d (F0105); 741 stars (F0067) | GameCraft-1.0; GameCraft-2 paper (W0009) | gh Tencent-Hunyuan; hf tencent | Keyboard/mouse actions mapped to camera space (W0030) |
| matrix-game | open | repo MIT (F0068); Matrix-Game-3.0 weights apache-2.0, 2.0 and 1.0 MIT (F0106) | not archived, not fork (F0068) | 2026-03-30 (F0068) | no GitHub releases recorded (F0427) | HF 174/30d 3.0, 276 2.0 (F0106); 2,341 stars (F0068) | Matrix-Game 1.0, 2.0, 3.0 (F0106) | gh SkyworkAI; hf Skywork | Matrix-3D (3D scene gen) is a separate product, parked |
| lingbot-world | open-weights | v1 Apache-2.0 (F0069; card F0100); v2 CC BY-NC-SA 4.0 (F0209) | not archived, not fork (F0069) | 2026-07-09 v1 (F0069); 2026-09-10 v2 (F0070) | no GitHub releases recorded (F0428) | HF 21,007/30d lingbot-world-fast (F0100); 4,487 + 1,822 stars (F0069, F0070) | lingbot-world base-cam, -fast; lingbot-world-v2 1.3B/14B (F0100, F0137) | gh Robbyant; hf robbyant | Current release v2 is non-commercial, so status open-weights under the current-release rule |
| oasis | open | code and weights MIT (F0071, F0126) | not archived, not fork (F0071) | 2024-11-08 (F0071) | no GitHub releases recorded (F0429) | HF 169/30d, gated=auto (F0126); 2,026 stars (F0071) | Oasis 500M (W0012) | gh etched-ai; hf Etched | Both artifacts are Etched's; Decart's hosted Oasis 3 (W0041) is parked as a separate closed product (question 11) |
| diamond | open-weights | MIT (F0072); HF card no license (F0127) | not archived, not fork (F0072) | 2024-12-06 (F0072) | no GitHub releases recorded (F0430) | HF 0/30d (F0127); 2,089 stars (F0072) | - | gh eloialonso; hf eloialonso | Dormant 21 months |
| yume | open | Apache-2.0 (F0073, F0313) | not archived, not fork (F0073) | 2026-01-14 (F0073) | no GitHub releases recorded (F0431) | HF 0/30d (F0313); 576 stars (F0073) | Yume 1.0, Yume-1.5 (W0011) | gh stdstu12; hf stdstu123 | HF handle differs from GitHub handle (F0313) |
| aether | open | MIT (F0074, F0141) | not archived, not fork (F0074) | 2025-10-26 (F0074) | no GitHub releases recorded (F0432) | HF 0/30d (F0141); 611 stars (F0074) | AetherV1 (F0141) | gh InternRobotics; hf AetherWorldModel | Action-conditioned video prediction + planning (W0011). InternRobotics = Shanghai AI Lab (F0211) |
| genie-envisioner | open-weights | CC BY-NC-SA 4.0 for data and most code; modified Diffusers/LTX/Cosmos parts keep their licenses (F0252); GE-base weights inherit the LTX-Video license (F0244) | not archived, not fork (F0095) | 2026-09-10 (F0095) | no GitHub releases recorded (F0433) | HF 20/30d (F0110); 585 stars (F0095) | GE v1.0, GE-Sim v2.0 (F0110) | gh AgibotTech; hf agibot-world | Repo renamed Genie-Envisioner -> Genie-Envisioner-V1 (F0089) |
| unifolm-wma | open-weights | code CC BY-NC-SA 4.0 (F0210); HF card metadata says apache-2.0 (F0111): conflict, record both | not archived, not fork (F0077) | 2026-03-18 (F0077) | no GitHub releases recorded (F0434) | HF 0/30d, gated=auto (F0111); 1,144 stars (F0077) | WMA-0-Base, WMA-0-Dual (F0111) | gh unitreerobotics; hf unitreerobotics | Unitree's world-model-action framework (W0029) |
| gigaworld | open | Apache-2.0 (F0078, F0102) | not archived, not fork (F0078) | 2025-12-03 (F0078) | no GitHub releases recorded (F0435) | HF 0/30d video pretrain; Giga-World-Policy-0.5 3,732 (F0102); 1,292 stars (F0078) | GigaWorld-0 Video/3D, Giga-World-Policy (F0102) | gh open-gigaai; hf open-gigaai | Same vendor as GigaBrain (5a) |
| ctrl-world | open | MIT (F0079, F0128) | not archived, not fork (F0079) | 2025-10-24 (F0079) | no GitHub releases recorded (F0436) | HF 145/30d (F0128); 50 stars (F0079) | - | gh Robert-gyj; hf yjguo | ICLR 2026 (W0029). Star count (50) is low for the attention it drew; recorded, not judged |
| boundless-world-model | open-weights | code Apache-2.0 (F0080, F0236); HF card no license field, base Wan2.2-TI2V-5B (F0154, F0242) | not archived, not fork (F0080) | 2026-06-15 (F0080) | no GitHub releases recorded (F0437) | HF 37/30d (F0154); 1,829 stars (F0080) | - | gh boundless-large-model; hf BLM-Lab | First among open models on WorldArena Track 1 (W0042) |
| dreamer | open | MIT (F0081) | not archived, not fork (F0081) | 2026-05-25 (F0081) | no GitHub releases recorded (F0438) | 3,822 stars (F0081) | DreamerV3 (F0081); the Dreamer 4 reimplementation next-state/open-dreamer is parked (W0026, F0230) | gh danijar | Model-based RL agent with a learned latent world model; code, no hosted weights |
| td-mpc | open | MIT (F0084) | not archived, not fork (F0084) | 2026-07-13 (F0084) | no GitHub releases recorded (F0439) | 889 stars (F0084) | TD-MPC2 (F0084) | gh nicklashansen | Added by this sweep as a model-based-RL comparator to Dreamer |
| rynnworld | open | HF cards apache-2.0 (F0136, F0314); RynnWorld-4D GitHub label `other`, text not read (F0308) | not archived, not fork (F0308) | 2026-07-06 (F0308) | no GitHub releases recorded (F0440) | HF 53/30d Teleop (F0136); 5 stars 4D (F0308) | RynnWorld-4D, RynnWorld-Teleop 'An Action-Conditioned World Model for Digital Teleoperation' (W0043) | gh alibaba-damo-academy; hf Alibaba-DAMO-Academy | 2026 release not in the brief. Pairs the RynnWorld-4D repo with the RynnWorld-Teleop weights, and the action-conditioning evidence (W0043) is for Teleop, whose repo ecosyste.ms does not index (F0307). Maintainer may prefer Teleop-only |
| dreamx-world | open | code Apache-2.0 (F0083); weights mit (F0315) | not archived, not fork (F0083) | 2026-07-23 (F0083) | no GitHub releases recorded (F0441) | HF 1,095/30d 5B, 610 5B-Cam (F0315); 775 stars (F0083) | DreamX-World-5B, -5B-Cam (F0315) | gh AMAP-ML; hf GD-ML | Camera control + text events; action input is camera pose only (marginal on the litmus) |
| genie | closed | proprietary; no weights (W0037) | live (W0037) | n/a | Project Genie to AI Ultra subscribers 2026-01-29 (W0008) | none measurable (subscription product) | Genie 3 via Project Genie (W0008) | - | Closed frontier comparator (interactive, action-controllable) |
| runway-gwm | closed | proprietary; no weights discussed (W0039) | live (W0039) | n/a | GWM-1 (W0013) | none measurable (API + Python SDK, W0039) | GWM Worlds, GWM Avatars, GWM Robotics (W0039) | - | Action-conditioning on camera, events, robot pose, speech (W0039). Only the Robotics/Worlds variants fit |

### 6c. Source list

See §D.

## 7. Parked candidates

| name | reason | source ids | fetch date |
|---|---|---|---|
| World Labs Marble | boundary -> media_generation: generates editable static 3D worlds, no action->next-state (W0040) | W0040, W0013 | 2026-09-26 |
| Mirage (Dynamics Lab) | closed long-tail: demo/preview, no open code or API found | W0016, W0041 | 2026-09-26 |
| open-dreamer | no addressable open artifact: 'All rights reserved' placeholder license, 1 star | F0230, F0082, W0026 | 2026-09-26 |
| WebWorld (Qwen) | boundary: web-environment world model, not physical (question 7) | W0003 | 2026-09-26 |
| CWM (Meta) | boundary -> base_pretrained: code LLM trained with world-model data | W0003 | 2026-09-26 |
| HY-WorldPlay | SKU of hy-world | F0140, F0306 | 2026-09-26 |
| HunyuanWorld-Voyager | SKU of hy-world | F0139, W0017 | 2026-09-26 |
| Hunyuan-GameCraft-2 | SKU of hunyuan-gamecraft (paper) | W0009 | 2026-09-26 |
| Cosmos-Reason | SKU of cosmos; VLM part contested with multimodal_models | F0097 | 2026-09-26 |
| Matrix-3D | SKU/boundary: Skywork 3D scene generator -> media_generation | F0106 | 2026-09-26 |
| Giga-World-Policy | SKU of gigaworld | F0102 | 2026-09-26 |
| EnerVerse-AC (AgiBot) | coverage limit: HF listing only (0 downloads) | F0110 | 2026-09-26 |
| LingBot-VA | identity unclear: video-action policy from Robbyant, not fetched | W0031 | 2026-09-26 |
| Oasis 3 (Decart) | closed long-tail: hosted interactive world model, no fetched source ties it to the open Etched 500M release; maintainer call (question 11) | W0041 | 2026-09-26 |
| Odyssey-2 Max | closed long-tail: named once, not fetched | W0013 | 2026-09-26 |
| SolarWM | no addressable artifact verified: paper only | W0009 | 2026-09-26 |
| WorldScape / FlowWAM-FiveAges | identity unclear: leaderboard names only | W0042 | 2026-09-26 |
| OmniWorld (InternRobotics) | coverage limit: dataset for world modeling in HF robotics top 40, not researched | F0297 | 2026-09-26 |
| DreamX-Phi | no addressable artifact verified: surfaced once in a search result (W0043); arXiv fetch did not complete (HTTP 406, F0598) | W0043 | 2026-09-26 |

**Cross-category duplicates** (counted in Part A; in Part B they are duplicate signals, not unique candidates):

| name | reason | source ids | fetch date |
|---|---|---|---|
| VLA-JEPA | duplicate: accepted in robotics_embodied (outputs actions) | W0011 | 2026-09-26 |
| GR00T / GR00T Dreams | duplicate: ruled into robotics_embodied | W0002 | 2026-09-26 |
| RynnVLA-002 | duplicate: member of rynnvla in robotics_embodied | F0088 | 2026-09-26 |
| WorldVLA | retired alias -> rynnvla (repo redirects to RynnVLA-002) in robotics_embodied | F0088, F0133 | 2026-09-26 |

## 8. Reconciled counts

- raw_signals = 70 = duplicate_signals 30 (includes 5 signals from the 4 cross-category duplicates) + unique_candidates 40
- unique_candidates = 40 = accepted 21 + parked 19

## 9. Open questions for the maintainer

10. **What counts as an action?** Does camera pose or keyboard control count (DreamX-World, Yume, HunyuanWorld-Voyager, Matrix-Game), and do non-physical environments count (games yes? web no?)? **Recommend:** camera and keyboard control count, since they are the agent's control input; games count; web and text environments don't.
11. **Oasis:** the accepted row is Etched's open Oasis 500M (MIT; both artifacts are Etched's, F0071, F0126). Decart's hosted Oasis 3 (W0041) is parked, because no fetched source ties the two. Merge them into one Decart-pitched line (which the current-release rule would make closed), or keep the open 500M row alone? **Recommend keeping the open row** and adding Oasis 3 as a closed comparator only if a primary source links the lines.
12. **Create, fold into 5a, or park again?** **Recommend create**, in the same new group as `robotics_embodied` (Part A, question 9). There's no need for the planned late-October revisit.
13. **HY-World collapse:** one `hy-world` row across HunyuanWorld 1.0, Voyager, WorldPlay and HY-World 2.0, or split the 3D-generation releases out to `media_generation`? **Recommend one row** pitched at the brand Tencent sells, with the litmus applied to the interactive members.
14. **Ladder type for Cosmos and V-JEPA:** `model` or `pretrained`? **Recommend `model`** for the category, with those two flagged.

---

# C. Breadth: candidates this sweep surfaced that the briefs did not name

- **Robotics (33):** robomimic, newton, brax, mjlab, robotwin, roboverse, gigabrain, galaxea-g0, lingbot-vla, internvla, wall-oss, molmoact, cogact, spatialvla, univla, go-1, rynnvla, xiaomi-robotics, being-h, spirit-vla, hy-embodied-vla, unifolm-vla, alpamayo, eo-1, nora, x-vla, vla-jepa (named in 5b), nvidia-physical-ai-dataset, interndata-a1, berkeley-humanoid-lite, lekiwi, openarm, aloha-2. Parked discoveries: Isaac Lab-Arena, dora-rs, Gymnasium, RoboTwin data, LIBERO.
- **World models (12):** hunyuan-gamecraft, genie-envisioner, unifolm-wma, gigaworld, ctrl-world, boundless-world-model, dreamer, td-mpc, rynnworld, dreamx-world, runway-gwm, and the Cosmos 3 release (2026-06-01).

**Corrections to the briefs found live:** WorldVLA now redirects to RynnVLA-002 (F0088). Genesis's
repo is now `Genesis-Embodied-AI/genesis-world` (F0085), and ManiSkill has moved to `mani-skill/ManiSkill`
(F0090). HY-World 2.0 ships under a Tencent community license that excludes the EU, UK and South Korea, not an OSI license (F0200).
openvla/openvla is marked a fork of TRI-ML/prismatic-vlms (F0027). open-dreamer is all-rights-reserved (F0230).

# D. Source list (every id cited in §6/§7, with URL and fetch time)

| id | fetched (UTC) | status / tool | URL or query |
|---|---|---|---|
| F0001 | 2026-09-26T20:02:02Z | HTTP 200 | https://raw.githubusercontent.com/sinanlabs/robo/HEAD/data/seed_v0.json |
| F0002 | 2026-09-26T20:04:20Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/huggingface%2Flerobot |
| F0003 | 2026-09-26T20:04:20Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-deepmind%2Fmujoco |
| F0004 | 2026-09-26T20:04:20Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-deepmind%2Fmujoco_playground |
| F0005 | 2026-09-26T20:04:20Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-deepmind%2Fmujoco_warp |
| F0006 | 2026-09-26T20:04:21Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/isaac-sim%2FIsaacLab |
| F0007 | 2026-09-26T20:04:21Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/isaac-sim%2FIsaacSim |
| F0010 | 2026-09-26T20:04:22Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fhabitat-sim |
| F0011 | 2026-09-26T20:04:22Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fhabitat-lab |
| F0012 | 2026-09-26T20:04:23Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ARISE-Initiative%2Frobosuite |
| F0013 | 2026-09-26T20:04:23Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/robocasa%2Frobocasa |
| F0014 | 2026-09-26T20:04:23Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ARISE-Initiative%2Frobomimic |
| F0015 | 2026-09-26T20:04:24Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bulletphysics%2Fbullet3 |
| F0016 | 2026-09-26T20:04:24Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/gazebosim%2Fgz-sim |
| F0017 | 2026-09-26T20:04:24Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/newton-physics%2Fnewton |
| F0018 | 2026-09-26T20:04:25Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/RobotLocomotion%2Fdrake |
| F0019 | 2026-09-26T20:04:25Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/cyberbotics%2Fwebots |
| F0020 | 2026-09-26T20:04:25Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google%2Fbrax |
| F0021 | 2026-09-26T20:04:25Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/mujocolab%2Fmjlab |
| F0022 | 2026-09-26T20:04:26Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/carla-simulator%2Fcarla |
| F0023 | 2026-09-26T20:04:26Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Farama-Foundation%2FGymnasium |
| F0024 | 2026-09-26T20:04:26Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/real-stanford%2Fdiffusion_policy |
| F0025 | 2026-09-26T20:04:26Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVIDIA%2FIsaac-GR00T |
| F0026 | 2026-09-26T20:04:27Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Physical-Intelligence%2Fopenpi |
| F0027 | 2026-09-26T20:04:27Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/openvla%2Fopenvla |
| F0028 | 2026-09-26T20:04:27Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/octo-models%2Focto |
| F0029 | 2026-09-26T20:04:28Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/thu-ml%2FRoboticsDiffusionTransformer |
| F0030 | 2026-09-26T20:04:28Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/thu-ml%2FRDT2 |
| F0031 | 2026-09-26T20:04:28Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/2toinf%2FX-VLA |
| F0032 | 2026-09-26T20:04:29Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-gigaai%2Fgiga-brain-0 |
| F0033 | 2026-09-26T20:04:29Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenGalaxea%2FGalaxeaVLA |
| F0034 | 2026-09-26T20:04:29Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/robbyant%2Flingbot-vla |
| F0035 | 2026-09-26T20:04:29Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/InternRobotics%2FInternVLA-M1 |
| F0037 | 2026-09-26T20:04:30Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/X-Square-Robot%2Fwall-x |
| F0038 | 2026-09-26T20:04:30Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/allenai%2FMolmoAct |
| F0039 | 2026-09-26T20:04:31Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2FCogACT |
| F0040 | 2026-09-26T20:04:31Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SpatialVLA%2FSpatialVLA |
| F0041 | 2026-09-26T20:04:31Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenDriveLab%2FUniVLA |
| F0042 | 2026-09-26T20:04:32Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenDriveLab%2FAgiBot-World |
| F0043 | 2026-09-26T20:04:32Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/alibaba-damo-academy%2FRynnVLA-001 |
| F0044 | 2026-09-26T20:04:32Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/XiaomiRobotics%2FXiaomi-Robotics-0 |
| F0045 | 2026-09-26T20:04:33Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/BeingBeyond%2FBeing-H0 |
| F0046 | 2026-09-26T20:04:33Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Spirit-AI-Team%2Fspirit-v1.5 |
| F0047 | 2026-09-26T20:04:33Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/RoboFlamingo%2FRoboFlamingo |
| F0048 | 2026-09-26T20:04:34Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ginwind%2FVLA-JEPA |
| F0049 | 2026-09-26T20:04:34Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-deepmind%2Fopen_x_embodiment |
| F0050 | 2026-09-26T20:04:34Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/droid-dataset%2Fdroid |
| F0051 | 2026-09-26T20:04:35Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/TheRobotStudio%2FSO-ARM100 |
| F0052 | 2026-09-26T20:04:35Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/jess-moss%2Fkoch-v1-1 |
| F0053 | 2026-09-26T20:04:35Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/pollen-robotics%2Freachy_mini |
| F0054 | 2026-09-26T20:04:35Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/tonyzhaozh%2Faloha |
| F0055 | 2026-09-26T20:04:36Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/HybridRobotics%2FBerkeley-Humanoid-Lite |
| F0056 | 2026-09-26T20:04:36Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SIGRobotics-UIUC%2FLeKiwi |
| F0057 | 2026-09-26T20:04:36Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/enactic%2Fopenarm |
| F0058 | 2026-09-26T20:04:43Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/unitreerobotics%2Funitree_sdk2 |
| F0059 | 2026-09-26T20:04:37Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ros2%2Fros2 |
| F0060 | 2026-09-26T20:04:37Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Lifelong-Robot-Learning%2FLIBERO |
| F0061 | 2026-09-26T20:04:37Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVIDIA%2FCosmos |
| F0062 | 2026-09-26T20:04:38Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nvidia-cosmos%2Fcosmos-predict2.5 |
| F0063 | 2026-09-26T20:04:38Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fvjepa2 |
| F0065 | 2026-09-26T20:04:38Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHY-World-2.0 |
| F0067 | 2026-09-26T20:04:39Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuan-GameCraft-1.0 |
| F0068 | 2026-09-26T20:04:39Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SkyworkAI%2FMatrix-Game |
| F0069 | 2026-09-26T20:04:40Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/robbyant%2Flingbot-world |
| F0070 | 2026-09-26T20:04:40Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/robbyant%2Flingbot-world-v2 |
| F0071 | 2026-09-26T20:04:40Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/etched-ai%2Fopen-oasis |
| F0072 | 2026-09-26T20:04:41Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/eloialonso%2Fdiamond |
| F0073 | 2026-09-26T20:04:41Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stdstu12%2FYUME |
| F0074 | 2026-09-26T20:04:41Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/InternRobotics%2FAether |
| F0077 | 2026-09-26T20:04:42Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/unitreerobotics%2Funifolm-world-model-action |
| F0078 | 2026-09-26T20:04:42Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-gigaai%2Fgiga-world-0 |
| F0079 | 2026-09-26T20:04:43Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Robert-gyj%2FCtrl-World |
| F0080 | 2026-09-26T20:04:43Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/boundless-large-model%2Fboundless-world-model |
| F0081 | 2026-09-26T20:04:43Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/danijar%2Fdreamerv3 |
| F0082 | 2026-09-26T20:04:44Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/next-state%2Fopen-dreamer |
| F0083 | 2026-09-26T20:04:44Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/AMAP-ML%2FDreamX-World |
| F0084 | 2026-09-26T20:04:44Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nicklashansen%2Ftdmpc2 |
| F0085 | 2026-09-26T20:04:58Z | HTTP 200 | https://ungh.cc/repos/Genesis-Embodied-AI/Genesis |
| F0086 | 2026-09-26T20:05:10Z | HTTP 000000 | https://ungh.cc/repos/haosulab/ManiSkill |
| F0087 | 2026-09-26T20:05:11Z | HTTP 200 | https://ungh.cc/repos/InternRobotics/InternVLA-A1 |
| F0088 | 2026-09-26T20:05:12Z | HTTP 200 | https://ungh.cc/repos/alibaba-damo-academy/WorldVLA |
| F0089 | 2026-09-26T20:05:13Z | HTTP 200 | https://ungh.cc/repos/AgibotTech/Genie-Envisioner |
| F0090 | 2026-09-26T20:05:17Z | HTTP 200 | https://ungh.cc/repos/haosulab/ManiSkill |
| F0091 | 2026-09-26T20:05:25Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Genesis-Embodied-AI%2Fgenesis-world |
| F0092 | 2026-09-26T20:05:25Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/mani-skill%2FManiSkill |
| F0093 | 2026-09-26T20:05:26Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/InternRobotics%2FInternVLA-A-series |
| F0094 | 2026-09-26T20:05:26Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/alibaba-damo-academy%2FRynnVLA-002 |
| F0095 | 2026-09-26T20:05:27Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/AgibotTech%2FGenie-Envisioner-V1 |
| F0096 | 2026-09-26T20:05:43Z | HTTP 200 | https://huggingface.co/api/models?author=nvidia&search=GR00T&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0097 | 2026-09-26T20:05:44Z | HTTP 200 | https://huggingface.co/api/models?author=nvidia&search=Cosmos&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0098 | 2026-09-26T20:05:44Z | HTTP 200 | https://huggingface.co/api/models?author=lerobot&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0099 | 2026-09-26T20:05:44Z | HTTP 200 | https://huggingface.co/api/models?author=OpenGalaxea&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0100 | 2026-09-26T20:05:45Z | HTTP 200 | https://huggingface.co/api/models?author=robbyant&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0101 | 2026-09-26T20:05:45Z | HTTP 200 | https://huggingface.co/api/models?author=InternRobotics&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0102 | 2026-09-26T20:05:45Z | HTTP 200 | https://huggingface.co/api/models?author=open-gigaai&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0103 | 2026-09-26T20:05:46Z | HTTP 200 | https://huggingface.co/api/models?author=XiaomiRobotics&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0104 | 2026-09-26T20:05:46Z | HTTP 200 | https://huggingface.co/api/models?author=tencent&search=World&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0105 | 2026-09-26T20:05:46Z | HTTP 200 | https://huggingface.co/api/models?author=tencent&search=GameCraft&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0106 | 2026-09-26T20:05:46Z | HTTP 200 | https://huggingface.co/api/models?author=Skywork&search=Matrix&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0109 | 2026-09-26T20:05:47Z | HTTP 200 | https://huggingface.co/api/models?author=facebook&search=vjepa&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0110 | 2026-09-26T20:05:47Z | HTTP 200 | https://huggingface.co/api/models?author=agibot-world&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0111 | 2026-09-26T20:05:47Z | HTTP 200 | https://huggingface.co/api/models?author=unitreerobotics&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0112 | 2026-09-26T20:05:47Z | HTTP 200 | https://huggingface.co/api/models?author=physical-intelligence&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0113 | 2026-09-26T20:05:47Z | HTTP 200 | https://huggingface.co/api/models?author=openvla&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0114 | 2026-09-26T20:05:48Z | HTTP 200 | https://huggingface.co/api/models?author=rail-berkeley&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0115 | 2026-09-26T20:05:48Z | HTTP 200 | https://huggingface.co/api/models?author=robotics-diffusion-transformer&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0116 | 2026-09-26T20:05:48Z | HTTP 200 | https://huggingface.co/api/models?author=2toINF&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0117 | 2026-09-26T20:05:48Z | HTTP 200 | https://huggingface.co/api/models?author=x-square-robot&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0118 | 2026-09-26T20:05:48Z | HTTP 200 | https://huggingface.co/api/models?author=allenai&search=MolmoAct&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0119 | 2026-09-26T20:05:49Z | HTTP 200 | https://huggingface.co/api/models?author=CogACT&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0120 | 2026-09-26T20:05:49Z | HTTP 200 | https://huggingface.co/api/models?author=IPEC-COMMUNITY&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0121 | 2026-09-26T20:05:49Z | HTTP 200 | https://huggingface.co/api/models?author=qwbu&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0122 | 2026-09-26T20:05:49Z | HTTP 200 | https://huggingface.co/api/models?author=Alibaba-DAMO-Academy&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0123 | 2026-09-26T20:05:49Z | HTTP 200 | https://huggingface.co/api/models?author=BeingBeyond&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0124 | 2026-09-26T20:05:50Z | HTTP 200 | https://huggingface.co/api/models?author=Spirit-AI-robotics&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0125 | 2026-09-26T20:05:50Z | HTTP 200 | https://huggingface.co/api/models?author=ginwind&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0126 | 2026-09-26T20:05:50Z | HTTP 200 | https://huggingface.co/api/models?author=Etched&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0127 | 2026-09-26T20:05:50Z | HTTP 200 | https://huggingface.co/api/models?author=eloialonso&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0128 | 2026-09-26T20:05:50Z | HTTP 200 | https://huggingface.co/api/models?author=yjguo&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0132 | 2026-09-26T20:05:51Z | HTTP 200 | https://huggingface.co/api/models?author=declare-lab&sort=downloads&limit=40&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0133 | 2026-09-26T20:06:07Z | HTTP 200 | https://huggingface.co/api/models/Alibaba-DAMO-Academy/WorldVLA?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0135 | 2026-09-26T20:06:08Z | HTTP 200 | https://huggingface.co/api/models/Alibaba-DAMO-Academy/RynnVLA-001-7B-Base?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0136 | 2026-09-26T20:06:08Z | HTTP 200 | https://huggingface.co/api/models/Alibaba-DAMO-Academy/RynnWorld-Teleop?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0137 | 2026-09-26T20:06:08Z | HTTP 200 | https://huggingface.co/api/models/robbyant/lingbot-world-base-cam?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0138 | 2026-09-26T20:06:08Z | HTTP 200 | https://huggingface.co/api/models/tencent/HunyuanWorld-1?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0139 | 2026-09-26T20:06:08Z | HTTP 200 | https://huggingface.co/api/models/tencent/HunyuanWorld-Voyager?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0140 | 2026-09-26T20:06:08Z | HTTP 200 | https://huggingface.co/api/models/tencent/HY-WorldPlay?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0141 | 2026-09-26T20:06:09Z | HTTP 200 | https://huggingface.co/api/models/AetherWorldModel/AetherV1?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0144 | 2026-09-26T20:06:09Z | HTTP 200 | https://huggingface.co/api/models/nvidia/Cosmos3-Nano?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0145 | 2026-09-26T20:06:09Z | HTTP 200 | https://huggingface.co/api/models/nvidia/Cosmos-Predict2.5-2B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0147 | 2026-09-26T20:06:10Z | HTTP 200 | https://huggingface.co/api/models/agibot-world/GO-1?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0148 | 2026-09-26T20:06:10Z | HTTP 200 | https://huggingface.co/api/models/x-square-robot/wall-oss-flow?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0150 | 2026-09-26T20:06:10Z | HTTP 200 | https://huggingface.co/api/models/allenai/MolmoAct2?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0151 | 2026-09-26T20:06:11Z | HTTP 200 | https://huggingface.co/api/models/nvidia/GR00T-N1.7-3B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0152 | 2026-09-26T20:06:11Z | HTTP 200 | https://huggingface.co/api/models/lerobot/smolvla_base?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0153 | 2026-09-26T20:06:11Z | HTTP 200 | https://huggingface.co/api/models/lerobot/pi05_base?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0154 | 2026-09-26T20:06:11Z | HTTP 200 | https://huggingface.co/api/models/BLM-Lab/Boundless-World-Model?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0155 | 2026-09-26T20:06:11Z | HTTP 200 | https://huggingface.co/api/models/OpenGalaxea/G05?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0156 | 2026-09-26T20:06:12Z | HTTP 200 | https://huggingface.co/api/models/open-gigaai/GigaBrain-0.7-3.5B-Base?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0157 | 2026-09-26T20:06:12Z | HTTP 200 | https://huggingface.co/api/models/unitreerobotics/UnifoLM-VLA-Base?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0159 | 2026-09-26T20:06:29Z | HTTP 200 | https://raw.githubusercontent.com/isaac-sim/IsaacSim/HEAD/LICENSE |
| F0160 | 2026-09-26T20:06:29Z | HTTP 200 | https://raw.githubusercontent.com/ARISE-Initiative/robosuite/HEAD/LICENSE |
| F0161 | 2026-09-26T20:06:29Z | HTTP 200 | https://raw.githubusercontent.com/robocasa/robocasa/HEAD/LICENSE |
| F0164 | 2026-09-26T20:06:30Z | HTTP 200 | https://raw.githubusercontent.com/bulletphysics/bullet3/HEAD/LICENSE.txt |
| F0170 | 2026-09-26T20:06:32Z | HTTP 200 | https://raw.githubusercontent.com/RobotLocomotion/drake/HEAD/LICENSE.TXT |
| F0195 | 2026-09-26T20:06:38Z | HTTP 200 | https://raw.githubusercontent.com/NVIDIA/cosmos/HEAD/LICENSE |
| F0196 | 2026-09-26T20:06:38Z | HTTP 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanWorld-1.0/HEAD/LICENSE |
| F0200 | 2026-09-26T20:06:39Z | HTTP 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/HY-World-2.0/HEAD/License.txt |
| F0201 | 2026-09-26T20:06:39Z | HTTP 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanWorld-Voyager/HEAD/LICENSE |
| F0202 | 2026-09-26T20:06:40Z | HTTP 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan-GameCraft-1.0/HEAD/LICENSE |
| F0206 | 2026-09-26T20:06:41Z | HTTP 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/HY-WorldPlay/HEAD/License.txt |
| F0209 | 2026-09-26T20:06:41Z | HTTP 200 | https://raw.githubusercontent.com/Robbyant/lingbot-world-v2/HEAD/LICENSE.txt |
| F0210 | 2026-09-26T20:06:42Z | HTTP 200 | https://raw.githubusercontent.com/unitreerobotics/unifolm-world-model-action/HEAD/LICENSE |
| F0211 | 2026-09-26T20:06:42Z | HTTP 200 | https://raw.githubusercontent.com/InternRobotics/InternVLA-A-series/HEAD/LICENSE |
| F0230 | 2026-09-26T20:06:46Z | HTTP 200 | https://raw.githubusercontent.com/next-state/open-dreamer/HEAD/LICENSE |
| F0231 | 2026-09-26T20:06:47Z | HTTP 200 | https://raw.githubusercontent.com/NVIDIA/Isaac-GR00T/HEAD/LICENSE |
| F0232 | 2026-09-26T20:06:47Z | HTTP 200 | https://raw.githubusercontent.com/Physical-Intelligence/openpi/HEAD/LICENSE |
| F0233 | 2026-09-26T20:06:47Z | HTTP 200 | https://raw.githubusercontent.com/allenai/molmoact/HEAD/LICENSE |
| F0234 | 2026-09-26T20:06:48Z | HTTP 200 | https://raw.githubusercontent.com/X-Square-Robot/wall-x/HEAD/LICENSE |
| F0235 | 2026-09-26T20:06:48Z | HTTP 200 | https://raw.githubusercontent.com/Robbyant/lingbot-vla/HEAD/LICENSE |
| F0236 | 2026-09-26T20:06:48Z | HTTP 200 | https://raw.githubusercontent.com/boundless-large-model/boundless-world-model/HEAD/LICENSE |
| F0237 | 2026-09-26T20:07:01Z | HTTP 200 | https://huggingface.co/nvidia/GR00T-N1.7-3B/raw/main/README.md |
| F0238 | 2026-09-26T20:07:02Z | HTTP 200 | https://huggingface.co/allenai/MolmoAct2/raw/main/README.md |
| F0239 | 2026-09-26T20:07:02Z | HTTP 200 | https://huggingface.co/x-square-robot/wall-oss-flow/raw/main/README.md |
| F0240 | 2026-09-26T20:07:02Z | HTTP 200 | https://huggingface.co/robbyant/lingbot-vla-4b/raw/main/README.md |
| F0241 | 2026-09-26T20:07:02Z | HTTP 200 | https://huggingface.co/agibot-world/GO-1/raw/main/README.md |
| F0242 | 2026-09-26T20:07:03Z | HTTP 200 | https://huggingface.co/BLM-Lab/Boundless-World-Model/raw/main/README.md |
| F0243 | 2026-09-26T20:07:03Z | HTTP 200 | https://huggingface.co/unitreerobotics/UnifoLM-VLA-Base/raw/main/README.md |
| F0244 | 2026-09-26T20:07:03Z | HTTP 200 | https://huggingface.co/agibot-world/Genie-Envisioner-v1.0/raw/main/README.md |
| F0247 | 2026-09-26T20:07:04Z | HTTP 200 | https://raw.githubusercontent.com/OpenGalaxea/GalaxeaVLA/HEAD/README.md |
| F0248 | 2026-09-26T20:07:05Z | HTTP 200 | https://raw.githubusercontent.com/SpatialVLA/SpatialVLA/HEAD/README.md |
| F0249 | 2026-09-26T20:07:05Z | HTTP 200 | https://raw.githubusercontent.com/OpenDriveLab/AgiBot-World/HEAD/README.md |
| F0250 | 2026-09-26T20:07:05Z | HTTP 200 | https://raw.githubusercontent.com/droid-dataset/droid/HEAD/README.md |
| F0251 | 2026-09-26T20:07:06Z | HTTP 200 | https://raw.githubusercontent.com/alibaba-damo-academy/RynnVLA-002/HEAD/README.md |
| F0252 | 2026-09-26T20:07:06Z | HTTP 200 | https://raw.githubusercontent.com/AgibotTech/Genie-Envisioner-V1/HEAD/README.md |
| F0253 | 2026-09-26T20:07:06Z | HTTP 200 | https://raw.githubusercontent.com/ginwind/VLA-JEPA/HEAD/README.md |
| F0254 | 2026-09-26T20:07:19Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/lerobot |
| F0255 | 2026-09-26T20:07:19Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/mujoco |
| F0256 | 2026-09-26T20:07:19Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/playground |
| F0257 | 2026-09-26T20:07:20Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/mujoco-warp |
| F0258 | 2026-09-26T20:07:20Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/isaaclab |
| F0259 | 2026-09-26T20:07:21Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/isaacsim |
| F0260 | 2026-09-26T20:07:21Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/genesis-world |
| F0261 | 2026-09-26T20:07:21Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/mani-skill |
| F0262 | 2026-09-26T20:07:22Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/robosuite |
| F0263 | 2026-09-26T20:07:22Z | HTTP 404 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/robocasa |
| F0264 | 2026-09-26T20:07:22Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/robomimic |
| F0265 | 2026-09-26T20:07:23Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/pybullet |
| F0267 | 2026-09-26T20:07:23Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/newton-physics |
| F0268 | 2026-09-26T20:07:24Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/drake |
| F0269 | 2026-09-26T20:07:24Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/brax |
| F0270 | 2026-09-26T20:07:24Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/mjlab |
| F0271 | 2026-09-26T20:07:25Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/gymnasium |
| F0272 | 2026-09-26T20:07:25Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/carla |
| F0273 | 2026-09-26T20:07:25Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/reachy-mini |
| F0274 | 2026-09-26T20:07:26Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/habitat-sim |
| F0275 | 2026-09-26T20:07:26Z | HTTP 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/unitree-sdk2py |
| F0276 | 2026-09-26T20:07:39Z | HTTP 200 | https://raw.githubusercontent.com/huggingface/lerobot/HEAD/README.md |
| F0277 | 2026-09-26T20:07:40Z | HTTP 200 | https://raw.githubusercontent.com/google-deepmind/mujoco/HEAD/README.md |
| F0278 | 2026-09-26T20:07:40Z | HTTP 200 | https://raw.githubusercontent.com/Genesis-Embodied-AI/genesis-world/HEAD/README.md |
| F0279 | 2026-09-26T20:07:40Z | HTTP 200 | https://raw.githubusercontent.com/mani-skill/ManiSkill/HEAD/README.md |
| F0280 | 2026-09-26T20:07:41Z | HTTP 200 | https://raw.githubusercontent.com/ARISE-Initiative/robosuite/HEAD/README.md |
| F0281 | 2026-09-26T20:07:41Z | HTTP 200 | https://raw.githubusercontent.com/bulletphysics/bullet3/HEAD/README.md |
| F0282 | 2026-09-26T20:07:41Z | HTTP 200 | https://raw.githubusercontent.com/mujocolab/mjlab/HEAD/README.md |
| F0283 | 2026-09-26T20:07:41Z | HTTP 200 | https://raw.githubusercontent.com/newton-physics/newton/HEAD/README.md |
| F0285 | 2026-09-26T20:07:42Z | HTTP 200 | https://raw.githubusercontent.com/google/brax/HEAD/README.md |
| F0286 | 2026-09-26T20:07:42Z | HTTP 200 | https://raw.githubusercontent.com/google-deepmind/mujoco_playground/HEAD/README.md |
| F0287 | 2026-09-26T20:07:42Z | HTTP 200 | https://raw.githubusercontent.com/isaac-sim/IsaacLab/HEAD/README.md |
| F0290 | 2026-09-26T20:08:05Z | HTTP 200 | https://huggingface.co/api/datasets/lerobot/droid_1.0.1?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0292 | 2026-09-26T20:08:06Z | HTTP 200 | https://huggingface.co/api/datasets/x-humanoid-robomind/RoboMIND?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0293 | 2026-09-26T20:08:06Z | HTTP 200 | https://huggingface.co/api/datasets/agibot-world/AgiBotWorld-Beta?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0294 | 2026-09-26T20:08:06Z | HTTP 200 | https://huggingface.co/api/datasets/agibot-world/AgiBotWorld2026?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0295 | 2026-09-26T20:08:06Z | HTTP 200 | https://huggingface.co/api/datasets/agibot-world/AgiBotWorld-Alpha?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0296 | 2026-09-26T20:08:06Z | HTTP 200 | https://huggingface.co/api/datasets?author=nvidia&search=PhysicalAI-Robotics&sort=downloads&limit=10&expand[]=downloads&expand[]=cardData&expand[]=lastModified |
| F0297 | 2026-09-26T20:08:07Z | HTTP 200 | https://huggingface.co/api/datasets?filter=task_categories:robotics&sort=downloads&limit=40&expand[]=downloads&expand[]=cardData |
| F0298 | 2026-09-26T20:08:07Z | HTTP 200 | https://huggingface.co/api/models?pipeline_tag=robotics&sort=downloads&limit=60&expand[]=downloads&expand[]=cardData |
| F0299 | 2026-09-26T20:08:24Z | HTTP 200 | https://huggingface.co/api/models?author=nvidia&search=Alpamayo&sort=downloads&limit=15&expand[]=downloads&expand[]=cardData&expand[]=lastModified |
| F0300 | 2026-09-26T20:08:25Z | HTTP 200 | https://huggingface.co/api/models?author=tencent&search=Embodied&sort=downloads&limit=15&expand[]=downloads&expand[]=cardData&expand[]=lastModified |
| F0302 | 2026-09-26T20:08:25Z | HTTP 200 | https://huggingface.co/api/datasets/InternRobotics/InternData-A1?expand[]=downloads&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0303 | 2026-09-26T20:08:46Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVlabs%2Falpamayo |
| F0305 | 2026-09-26T20:08:47Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHy-Embodied-0.5-VLA |
| F0306 | 2026-09-26T20:08:48Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHY-WorldPlay |
| F0307 | 2026-09-26T20:09:39Z | HTTP 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/alibaba-damo-academy%2FRynnWorld-Teleop |
| F0308 | 2026-09-26T20:09:40Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/alibaba-damo-academy%2FRynnWorld-4D |
| F0309 | 2026-09-26T20:09:40Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/RoboTwin-Platform%2FRoboTwin |
| F0310 | 2026-09-26T20:09:41Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/RoboVerseOrg%2FRoboVerse |
| F0311 | 2026-09-26T20:09:41Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/isaac-sim%2FIsaacLab-Arena |
| F0312 | 2026-09-26T20:09:41Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/dora-rs%2Fdora |
| F0313 | 2026-09-26T20:09:41Z | HTTP 200 | https://huggingface.co/api/models/stdstu123/Yume-I2V-540P?expand[]=downloads&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0314 | 2026-09-26T20:09:42Z | HTTP 200 | https://huggingface.co/api/models/Alibaba-DAMO-Academy/RynnWorld-4D?expand[]=downloads&expand[]=cardData&expand[]=lastModified&expand[]=gated |
| F0315 | 2026-09-26T20:09:42Z | HTTP 200 | https://huggingface.co/api/models?search=DreamX-World&sort=downloads&limit=10&expand[]=downloads&expand[]=cardData |
| F0316 | 2026-09-26T20:11:14Z | HTTP 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/Hy-Embodied-0.5-VLA/HEAD/LICENSE |
| F0317 | 2026-09-26T20:11:14Z | HTTP 200 | https://raw.githubusercontent.com/TheRobotStudio/SO-ARM100/HEAD/README.md |
| F0319 | 2026-09-26T20:11:32Z | HTTP 200 | https://ungh.cc/repos/google-deepmind/mujoco/releases/latest |
| F0321 | 2026-09-26T20:11:33Z | HTTP 200 | https://ungh.cc/repos/isaac-sim/IsaacLab/releases/latest |
| F0322 | 2026-09-26T20:11:34Z | HTTP 200 | https://ungh.cc/repos/isaac-sim/IsaacSim/releases/latest |
| F0323 | 2026-09-26T20:11:35Z | HTTP 200 | https://ungh.cc/repos/Genesis-Embodied-AI/genesis-world/releases/latest |
| F0324 | 2026-09-26T20:11:36Z | HTTP 200 | https://ungh.cc/repos/mani-skill/ManiSkill/releases/latest |
| F0325 | 2026-09-26T20:11:37Z | HTTP 200 | https://ungh.cc/repos/facebookresearch/habitat-sim/releases/latest |
| F0326 | 2026-09-26T20:11:37Z | HTTP 200 | https://ungh.cc/repos/ARISE-Initiative/robosuite/releases/latest |
| F0327 | 2026-09-26T20:11:38Z | HTTP 200 | https://ungh.cc/repos/robocasa/robocasa/releases/latest |
| F0328 | 2026-09-26T20:11:39Z | HTTP 200 | https://ungh.cc/repos/ARISE-Initiative/robomimic/releases/latest |
| F0329 | 2026-09-26T20:11:40Z | HTTP 200 | https://ungh.cc/repos/bulletphysics/bullet3/releases/latest |
| F0330 | 2026-09-26T20:11:40Z | HTTP 200 | https://ungh.cc/repos/newton-physics/newton/releases/latest |
| F0331 | 2026-09-26T20:11:41Z | HTTP 200 | https://ungh.cc/repos/google/brax/releases/latest |
| F0332 | 2026-09-26T20:11:42Z | HTTP 200 | https://ungh.cc/repos/mujocolab/mjlab/releases/latest |
| F0333 | 2026-09-26T20:11:42Z | HTTP 200 | https://ungh.cc/repos/RoboTwin-Platform/RoboTwin/releases/latest |
| F0387 | 2026-09-26T20:12:25Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/huggingface%2Flerobot/releases?per_page=1 |
| F0388 | 2026-09-26T20:12:26Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-deepmind%2Fmujoco_playground/releases?per_page=1 |
| F0389 | 2026-09-26T20:12:27Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/RoboVerseOrg%2FRoboVerse/releases?per_page=1 |
| F0390 | 2026-09-26T20:12:28Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVIDIA%2FIsaac-GR00T/releases?per_page=1 |
| F0391 | 2026-09-26T20:12:29Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Physical-Intelligence%2Fopenpi/releases?per_page=1 |
| F0392 | 2026-09-26T20:12:30Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/openvla%2Fopenvla/releases?per_page=1 |
| F0393 | 2026-09-26T20:12:31Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/octo-models%2Focto/releases?per_page=1 |
| F0394 | 2026-09-26T20:12:32Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/thu-ml%2FRDT2/releases?per_page=1 |
| F0395 | 2026-09-26T20:12:33Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/2toinf%2FX-VLA/releases?per_page=1 |
| F0396 | 2026-09-26T20:12:34Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-gigaai%2Fgiga-brain-0/releases?per_page=1 |
| F0397 | 2026-09-26T20:12:35Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenGalaxea%2FGalaxeaVLA/releases?per_page=1 |
| F0398 | 2026-09-26T20:12:36Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Robbyant%2Flingbot-vla/releases?per_page=1 |
| F0399 | 2026-09-26T20:12:37Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/InternRobotics%2FInternVLA-A-series/releases?per_page=1 |
| F0400 | 2026-09-26T20:12:38Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/X-Square-Robot%2Fwall-x/releases?per_page=1 |
| F0401 | 2026-09-26T20:12:39Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/allenai%2Fmolmoact/releases?per_page=1 |
| F0402 | 2026-09-26T20:12:40Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2FCogACT/releases?per_page=1 |
| F0403 | 2026-09-26T20:12:41Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SpatialVLA%2FSpatialVLA/releases?per_page=1 |
| F0404 | 2026-09-26T20:12:42Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenDriveLab%2FUniVLA/releases?per_page=1 |
| F0405 | 2026-09-26T20:12:43Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/alibaba-damo-academy%2FRynnVLA-002/releases?per_page=1 |
| F0406 | 2026-09-26T20:12:44Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/XiaomiRobotics%2FXiaomi-Robotics-0/releases?per_page=1 |
| F0407 | 2026-09-26T20:12:45Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/BeingBeyond%2FBeing-H0/releases?per_page=1 |
| F0408 | 2026-09-26T20:12:46Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Spirit-AI-Team%2Fspirit-v1.5/releases?per_page=1 |
| F0409 | 2026-09-26T20:12:47Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHy-Embodied-0.5-VLA/releases?per_page=1 |
| F0410 | 2026-09-26T20:12:48Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVlabs%2Falpamayo/releases?per_page=1 |
| F0411 | 2026-09-26T20:12:49Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/RoboFlamingo%2FRoboFlamingo/releases?per_page=1 |
| F0412 | 2026-09-26T20:12:50Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ginwind%2FVLA-JEPA/releases?per_page=1 |
| F0413 | 2026-09-26T20:12:51Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-deepmind%2Fopen_x_embodiment/releases?per_page=1 |
| F0415 | 2026-09-26T20:12:52Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenDriveLab%2FAgiBot-World/releases?per_page=1 |
| F0416 | 2026-09-26T20:12:54Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/TheRobotStudio%2FSO-ARM100/releases?per_page=1 |
| F0417 | 2026-09-26T20:12:55Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/jess-moss%2Fkoch-v1-1/releases?per_page=1 |
| F0418 | 2026-09-26T20:12:56Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/pollen-robotics%2Freachy_mini/releases?per_page=1 |
| F0419 | 2026-09-26T20:12:57Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/tonyzhaozh%2Faloha/releases?per_page=1 |
| F0420 | 2026-09-26T20:12:58Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/HybridRobotics%2Fberkeley-humanoid-lite/releases?per_page=1 |
| F0421 | 2026-09-26T20:12:59Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SIGRobotics-UIUC%2FLeKiwi/releases?per_page=1 |
| F0422 | 2026-09-26T20:13:01Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/enactic%2Fopenarm/releases?per_page=1 |
| F0423 | 2026-09-26T20:13:02Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVIDIA%2Fcosmos/releases?per_page=1 |
| F0424 | 2026-09-26T20:13:03Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fvjepa2/releases?per_page=1 |
| F0425 | 2026-09-26T20:13:04Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHY-World-2.0/releases?per_page=1 |
| F0426 | 2026-09-26T20:13:05Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuan-GameCraft-1.0/releases?per_page=1 |
| F0427 | 2026-09-26T20:13:06Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SkyworkAI%2FMatrix-Game/releases?per_page=1 |
| F0428 | 2026-09-26T20:13:07Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Robbyant%2Flingbot-world/releases?per_page=1 |
| F0429 | 2026-09-26T20:13:08Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/etched-ai%2Fopen-oasis/releases?per_page=1 |
| F0430 | 2026-09-26T20:13:08Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/eloialonso%2Fdiamond/releases?per_page=1 |
| F0431 | 2026-09-26T20:13:09Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stdstu12%2FYUME/releases?per_page=1 |
| F0432 | 2026-09-26T20:13:10Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/InternRobotics%2FAether/releases?per_page=1 |
| F0433 | 2026-09-26T20:13:11Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/AgibotTech%2FGenie-Envisioner-V1/releases?per_page=1 |
| F0434 | 2026-09-26T20:13:12Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/unitreerobotics%2Funifolm-world-model-action/releases?per_page=1 |
| F0435 | 2026-09-26T20:13:13Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-gigaai%2Fgiga-world-0/releases?per_page=1 |
| F0436 | 2026-09-26T20:13:14Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Robert-gyj%2FCtrl-World/releases?per_page=1 |
| F0437 | 2026-09-26T20:13:15Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/boundless-large-model%2Fboundless-world-model/releases?per_page=1 |
| F0438 | 2026-09-26T20:13:16Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/danijar%2Fdreamerv3/releases?per_page=1 |
| F0439 | 2026-09-26T20:13:17Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nicklashansen%2Ftdmpc2/releases?per_page=1 |
| F0440 | 2026-09-26T20:13:18Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/alibaba-damo-academy%2FRynnWorld-4D/releases?per_page=1 |
| F0441 | 2026-09-26T20:13:19Z | HTTP 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/AMAP-ML%2FDreamX-World/releases?per_page=1 |
| F0442 | 2026-09-26T20:13:29Z | HTTP 200 | https://export.arxiv.org/abs/2405.02292 |
| F0443 | 2026-09-26T20:13:29Z | HTTP 200 | https://aloha-2.github.io/ |
| F0598 | 2026-09-26T20:33:54Z | HTTP 406 | https://export.arxiv.org/abs/2608.13489 |
| W0001 | 2026-09-26T19:59:52Z | WebSearch | open-source vision-language-action model released 2026 |
| W0002 | 2026-09-26T19:59:52Z | WebSearch | open source robot foundation model weights Hugging Face 2025 2026 VLA list |
| W0003 | 2026-09-26T19:59:52Z | WebSearch | open-source world model action-conditioned released 2026 weights |
| W0004 | 2026-09-26T19:59:52Z | WebSearch | awesome embodied AI robot learning simulators github list |
| W0005 | 2026-09-26T20:00:23Z | WebFetch | https://github.com/knmcguire/best-of-robot-simulators |
| W0008 | 2026-09-26T20:00:46Z | WebSearch | Genie 3 world model DeepMind 2026 availability |
| W0009 | 2026-09-26T20:00:46Z | WebSearch | HunyuanWorld Matrix-Game LingBot-World interactive world model open source 2026 |
| W0010 | 2026-09-26T20:00:46Z | WebSearch | NVIDIA Cosmos world foundation models Predict Transfer Reason 2026 release license |
| W0011 | 2026-09-26T20:00:46Z | WebSearch | V-JEPA 2 world model Meta open weights; VLA-JEPA; Yume world model; Aether world model github |
| W0012 | 2026-09-26T20:01:05Z | WebSearch | Oasis Decart open world model weights; DIAMOND world model; Mirage Dynamics world model; open-dreamer |
| W0013 | 2026-09-26T20:01:05Z | WebSearch | World Labs Marble world model; Runway GWM-1 world model; closed world model 2026 |
| W0015 | 2026-09-26T20:01:05Z | WebSearch | Gemini Robotics 1.5 ER availability API 2026; Gemini Robotics On-Device |
| W0016 | 2026-09-26T20:01:32Z | WebSearch | DIAMOND diffusion world model eloialonso github; Mirage generative game world model Dynamics Lab open source |
| W0017 | 2026-09-26T20:01:32Z | WebSearch | HunyuanWorld-Voyager HY-World 2.0 open source weights Tencent license 2026 |
| W0018 | 2026-09-26T20:01:32Z | WebSearch | Physical Intelligence openpi pi0.5 pi0.6 open weights 2026 |
| W0019 | 2026-09-26T20:01:32Z | WebSearch | open-source humanoid robot hardware design 2026 SO-101 Reachy Mini Berkeley Humanoid Lite |
| W0020 | 2026-09-26T20:01:51Z | WebSearch | Newton physics engine Linux Foundation NVIDIA DeepMind Disney 2026 release |
| W0021 | 2026-09-26T20:01:51Z | WebSearch | largest open robot learning datasets 2026 AgiBot World Open X-Embodiment DROID RoboMIND hugging face |
| W0022 | 2026-09-26T20:01:51Z | WebSearch | GR00T N1.7 open model license huggingface nvidia; Isaac Lab 3.0 release 2026 |
| W0023 | 2026-09-26T20:01:51Z | WebSearch | open-source VLA 2026 InternVLA GigaBrain WALL-OSS RDT-2 Galaxea G0 release weights github |
| W0026 | 2026-09-26T20:03:36Z | WebSearch | open-dreamer world model license github |
| W0029 | 2026-09-26T20:03:36Z | WebSearch | Boundless World Model BWM huggingface robot; Ctrl-World github; UnifoLM-WMA-0 github unitree; GigaWorld-0 github |
| W0030 | 2026-09-26T20:03:57Z | WebSearch | Hunyuan-GameCraft github weights action keyboard world model; Skywork Matrix-Game github license |
| W0031 | 2026-09-26T20:03:57Z | WebSearch | LingBot-World github robbyant license huggingface |
| W0032 | 2026-09-26T20:03:57Z | WebSearch | DROID dataset huggingface lerobot; RoboMIND dataset huggingface license; AgiBot World dataset huggingface license |
| W0033 | 2026-09-26T20:03:57Z | WebSearch | Koch v1.1 robot arm github; ALOHA 2 hardware open source; OpenArm enactic github; LeKiwi github |
| W0034 | 2026-09-26T20:08:45Z | WebSearch | NVIDIA Alpamayo github NVlabs autonomous driving VLA open model |
| W0035 | 2026-09-26T20:08:45Z | WebSearch | Tencent HY-Embodied VLA github open source 2026 |
| W0036 | 2026-09-26T20:08:45Z | WebFetch | https://deepmind.google/models/gemini-robotics/ |
| W0037 | 2026-09-26T20:08:45Z | WebFetch | https://deepmind.google/models/genie/ |
| W0039 | 2026-09-26T20:09:15Z | WebFetch | https://runway.com/research/introducing-runway-gwm-1 |
| W0040 | 2026-09-26T20:09:15Z | WebFetch | https://www.worldlabs.ai/ |
| W0041 | 2026-09-26T20:09:15Z | WebFetch | https://decart.ai/ |
| W0042 | 2026-09-26T20:09:38Z | WebSearch | WorldArena leaderboard embodied world model open-source ranking 2026 |
| W0043 | 2026-09-26T20:09:38Z | WebSearch | RynnWorld Alibaba DAMO world model github; Yume weights huggingface stdstu12; DreamX-World weights |
| W0044 | 2026-09-26T20:09:38Z | WebSearch | new open-source robot learning framework or simulator 2026 release (RoboVerse, Isaac Lab Arena, dora-rs, RoboTwin) |
