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

**GO-WITH-CHANGES.** Supply is deep and diverse: {R_n} accepted candidates from {R_norg}
organizations, no organization above {R_share} of the set, {R_act} of them active in the last 12
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

{R_metrics}
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
{R_rows}```

### 6b. Evidence table

{R_evidence}

### 6c. Source list

See the combined source list at the end of this document (§D). Every id in 6b resolves there.

## 7. Parked candidates

{R_parked}

## 8. Reconciled counts

A *signal* is one source id that surfaced a candidate (the `src` list per candidate in `spec.py`,
plus each parked row's source ids). Duplicate signals are the extra surfacings of a candidate
already seen. In Part B, candidates already counted in Part A (VLA-JEPA, GR00T, RynnVLA-002,
WorldVLA) are counted as duplicate signals only, listed separately in Part B §7.

- raw_signals = {R_raw} = duplicate_signals {R_dup} + unique_candidates {R_uniq}
- unique_candidates = {R_uniq} = accepted {R_acc} + parked {R_park}

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
(about 4 product lines from 2 vendors) no longer holds. This run accepts **{W_n} product lines from
{W_norg} organizations**; the largest vendor share is {W_share}, and {W_act} lines were active in the
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

{W_metrics}
- product lines: {W_n}; vendors: {W_norg}; largest-vendor share: {W_share} (Tencent: HY-World + Hunyuan-GameCraft)
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
{W_rows}```

### 6b. Evidence table

{W_evidence}

### 6c. Source list

See §D.

## 7. Parked candidates

{W_parked}

**Cross-category duplicates** (counted in Part A; in Part B they are duplicate signals, not unique candidates):

{W_dups}

## 8. Reconciled counts

- raw_signals = {W_raw} = duplicate_signals {W_dup} (includes 5 signals from the 4 cross-category duplicates) + unique_candidates {W_uniq}
- unique_candidates = {W_uniq} = accepted {W_acc} + parked {W_park}

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

{sources}
