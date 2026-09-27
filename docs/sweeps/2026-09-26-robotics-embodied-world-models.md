# Robotics & embodied AI and World models seed: 2026-09-26

## Scope and boundary

This batch seeds two preliminary categories in a new taxonomy group, **Embodied & world models**
(`embodied_world`), in the Model components arc: `robotics_embodied` (issue #12) and `world_models`
(issue #99). They were swept together because they share a boundary. Placement, weights, ladders and
the contested rulings come from the 2026-09-26 decision record that ruled on the nine new-category
sweeps, and every ruling is a proposal for the maintainer to review in the PR.

| Category | Weights adopt / cap | `extends` |
|---|---|---|
| `robotics_embodied` | 0.4 / 0.6 | `{model: model, software: software, dataset: dataset, hardware: hardware}` |
| `world_models` | 0.3 / 0.7 | `model` |

**`robotics_embodied`.** Membership test: does the product's value depend on producing, or
simulating, physical actions by a robot or a vehicle? Four product types pass it (policy models,
simulators and robot-learning frameworks, robot-interaction datasets, open robot hardware). Capability
is read per type because the four share no axis: embodiment generality for models, simulation
throughput and fidelity for software, episodes times embodiments for datasets, and morphology for
hardware.

**`world_models`.** Membership test: given a state and an action, does it predict the next state, as
pixels, latents or 3D? An action is the agent's control input, so robot actions, keyboard and mouse
input and camera pose all count, and games count as environments. Web and text environments do not.
The capability quantity is controllable rollout: how much of a world you can drive, and for how long.

The seam between the two: a model that predicts the environment from an action is a world model. A
policy that outputs actions belongs to `robotics_embodied`, even when a world model sits inside it.

Rulings applied (all recorded in the category `comments`):

- **Autonomous driving is in.** Alpamayo stays, and CARLA came in from the parked list.
- **Robot datasets live in `robotics_embodied`**, not `training_synthetic_datasets`. Their consumers
  are the policies in this category.
- **No SO-100 row.** It is the previous hardware generation in the SO-101 repository.
- **GR00T is in `robotics_embodied`** (ruled 2026-09-25).
- **Cosmos, V-JEPA, HY-World and the action-conditioned game world models are in `world_models`.**
- **General robotics tooling with no learning surface** (ROS 2, dora-rs, Gazebo, Webots, Drake) is out.
- **Embodied-reasoning VLMs with no action head** (RynnBrain, Hy-Embodied VLM, UnifoLM-ER) go to
  `multimodal_models`, and Matrix-3D and World Labs Marble go to `media_generation`, in follow-up
  sweeps. None of them is seeded here.
- **`world_models` stays preliminary until the late-October revisit** that #99 already planned. The July
  count no longer holds, but adoption is thin: most lines are single research drops with small Hub
  download counts. It goes last among the new categories to be promoted.
- The sweep's other recommendations stand: one `agibot-world` row across its releases, Isaac Sim tiered
  on its code, the open Oasis 500M row kept apart from Decart's hosted Oasis 3, one `hy-world` row,
  and the `model` ladder for Cosmos and V-JEPA with both flagged for the promotion PR.

No row was scored. Each row carries identity and artifacts only, as the registry schema requires.

## Inputs swept

All fetched on 2026-09-26. The full fetch trail is on the evidence branch
`claude/research-robotics_embodied`, under `research/robotics_embodied/`: `sweep.md`, `fetch-log.tsv`,
`web-log.tsv` and `raw/`. Every body is saved with its UTC time, HTTP code and sha256, and every
WebSearch and WebFetch call is logged with an excerpt. The same directory holds a two-pass independent
audit (`audit.md`) that re-fetched claims live and passed on its re-check.

- WebSearch discovery of 2025 and 2026 VLA and world-model releases, awesome-lists, a simulator
  list, a VLA index and leaderboards.
- ecosyste.ms repository metadata for every GitHub candidate, ungh.cc for renames, and the raw LICENSE
  and README text.
- The Hugging Face API: author listings sorted by 30-day downloads, and the `robotics` model and
  dataset filters.
- ecosyste.ms PyPI download counts, and vendor pages for the closed comparators.

**Retrieval cutoffs (coverage limits, not rejections).** HF author listings were read to the top 15 by
downloads, the HF `robotics` model filter to the top 60 and the dataset filter to the top 40. A
third-party VLA index was used for discovery only. An entry from it was accepted only when a Hub
listing or search surfaced it independently, and entries only the index named are parked as coverage
limits.

## Reconciled counts

Signals and candidates are counted per category. In the world-models count, candidates the robotics
count already holds appear as duplicate signals only.

| | `robotics_embodied` | `world_models` |
|---|---|---|
| raw_signals | 174 | 70 |
| duplicate_signals | 60 | 30 |
| unique_candidates | 114 | 40 |
| accepted | 61 | 21 |
| parked | 53 | 19 |

- `robotics_embodied`: 174 = 60 + 114, and 114 = 61 + 53. The sweep accepted 60 and parked 54, and
  CARLA moved from parked to accepted under the driving ruling.
- `world_models`: 70 = 30 + 40, and 40 = 21 + 19.

The shape at seed:

- `robotics_embodied`: 29 models, 18 software, 8 hardware and 6 datasets, from 47 organizations. The
  largest is Google, with 6 rows (9.8%). One row is closed (Gemini Robotics). The 6 datasets are a
  floor: 16 more robotics datasets in the Hub's top 40 are parked as not researched.
- `world_models`: 21 models from 20 organizations. The largest is Tencent, with 2 rows (9.5%). Two rows
  are closed (Genie, Runway GWM). 12 of the 17 lines with a Hub artifact showed fewer than 200
  downloads in 30 days.

No tail row moved in or out of another category's registry. The boundary matrix assigns no move to
either category, and the collision check against the corpus found no slug or artifact already claimed.

## Organizations and handles

The rows introduce 46 organizations with no record. Each gets an empty-roster record in
`sources/organizations/` so its handles can be registered. `sources/org_handles.yaml` gains a handle
for every new org on each route its rows declare. It also gains handles for existing orgs whose rows
sit under another account: NVIDIA's `isaac-sim` and `NVlabs`, Tencent's `Tencent-Hunyuan` and
`tencent`, Shanghai AI Lab's `InternRobotics`, the Alibaba DAMO and Xiaomi robotics accounts, Hugging
Face's `lerobot` Hub account, the RDT account for `thu-ml`, and `deepmind.google` for Google. Academic
projects keep the owner's handle as the org slug (tonyzhaozh, jess-moss, ginwind, danijar,
nicklashansen, eloialonso, stdstu12, robert-gyj) until a primary source names an institution.

Some handles were deliberately left unregistered because the account is not the org's own:
`rail-berkeley` (Octo's weights, on a lab account that hosts more than Octo), `2toinf` and `qwbu`
(personal accounts behind X-VLA and UniVLA, whose rows are pitched at an institution), `CogACT`,
`SpatialVLA` and `AetherWorldModel` (project accounts), and `lerobot` as the host of the DROID port.
The `allenai` accounts stay unregistered, as they were before, because they are shared with the `ai2`
record, a flagged merge candidate.

## Accepted candidates

The primary source is the first declared artifact. Status is the sweep's reading of the current
release, not a score. The license text, activity dates and adoption figures behind each row are in the
evidence table on the evidence branch.

### `robotics_embodied`

| slug | type | org | status | primary source | fetched |
|---|---|---|---|---|---|
| `lerobot` | software | hugging-face | open | https://github.com/huggingface/lerobot | 2026-09-26 |
| `mujoco` | software | google | open | https://github.com/google-deepmind/mujoco | 2026-09-26 |
| `mujoco-playground` | software | google | open | https://github.com/google-deepmind/mujoco_playground | 2026-09-26 |
| `isaac-lab` | software | nvidia | open | https://github.com/isaac-sim/IsaacLab | 2026-09-26 |
| `isaac-sim` | software | nvidia | open | https://github.com/isaac-sim/IsaacSim | 2026-09-26 |
| `genesis` | software | genesis-embodied-ai | open | https://github.com/Genesis-Embodied-AI/genesis-world | 2026-09-26 |
| `maniskill` | software | mani-skill | open | https://github.com/mani-skill/ManiSkill | 2026-09-26 |
| `habitat` | software | meta | open | https://github.com/facebookresearch/habitat-sim | 2026-09-26 |
| `robosuite` | software | arise-initiative | open | https://github.com/ARISE-Initiative/robosuite | 2026-09-26 |
| `robocasa` | software | robocasa | open | https://github.com/robocasa/robocasa | 2026-09-26 |
| `robomimic` | software | arise-initiative | open | https://github.com/ARISE-Initiative/robomimic | 2026-09-26 |
| `pybullet` | software | bullet-physics | open | https://github.com/bulletphysics/bullet3 | 2026-09-26 |
| `newton` | software | newton-physics | open | https://github.com/newton-physics/newton | 2026-09-26 |
| `brax` | software | google | open | https://github.com/google/brax | 2026-09-26 |
| `mjlab` | software | mujocolab | open | https://github.com/mujocolab/mjlab | 2026-09-26 |
| `robotwin` | software | robotwin-platform | open | https://github.com/RoboTwin-Platform/RoboTwin | 2026-09-26 |
| `roboverse` | software | roboverse | open | https://github.com/RoboVerseOrg/RoboVerse | 2026-09-26 |
| `carla` | software | carla-simulator | open | https://github.com/carla-simulator/carla | 2026-09-26 |
| `gr00t` | model | nvidia | open-weights | https://github.com/NVIDIA/Isaac-GR00T | 2026-09-26 |
| `pi0` | model | physical-intelligence | open-weights | https://github.com/Physical-Intelligence/openpi | 2026-09-26 |
| `smolvla` | model | hugging-face | open | https://huggingface.co/lerobot/smolvla_base | 2026-09-26 |
| `openvla` | model | openvla | open-weights | https://github.com/openvla/openvla | 2026-09-26 |
| `octo` | model | octo-models | open | https://github.com/octo-models/octo | 2026-09-26 |
| `rdt` | model | thu-ml | open | https://github.com/thu-ml/RDT2 | 2026-09-26 |
| `x-vla` | model | tsinghua-air | open | https://github.com/2toinf/X-VLA | 2026-09-26 |
| `gigabrain` | model | gigaai | open | https://github.com/open-gigaai/giga-brain-0 | 2026-09-26 |
| `galaxea-g0` | model | galaxea | open-weights | https://github.com/OpenGalaxea/GalaxeaVLA | 2026-09-26 |
| `lingbot-vla` | model | robbyant | open | https://github.com/Robbyant/lingbot-vla | 2026-09-26 |
| `internvla` | model | shanghai-ai-laboratory | open-weights | https://github.com/InternRobotics/InternVLA-A-series | 2026-09-26 |
| `wall-oss` | model | x-square-robot | open-weights | https://github.com/X-Square-Robot/wall-x | 2026-09-26 |
| `molmoact` | model | allen-institute-for-ai | open-weights | https://github.com/allenai/molmoact | 2026-09-26 |
| `cogact` | model | microsoft | open | https://github.com/microsoft/CogACT | 2026-09-26 |
| `spatialvla` | model | shanghai-ai-laboratory | open | https://github.com/SpatialVLA/SpatialVLA | 2026-09-26 |
| `univla` | model | opendrivelab | open | https://github.com/OpenDriveLab/UniVLA | 2026-09-26 |
| `go-1` | model | agibot | open-weights | https://huggingface.co/agibot-world/GO-1 | 2026-09-26 |
| `rynnvla` | model | alibaba-damo-academy | open | https://github.com/alibaba-damo-academy/RynnVLA-002 | 2026-09-26 |
| `xiaomi-robotics` | model | xiaomi | open | https://github.com/XiaomiRobotics/Xiaomi-Robotics-0 | 2026-09-26 |
| `being-h` | model | beingbeyond | open | https://github.com/BeingBeyond/Being-H0 | 2026-09-26 |
| `spirit-vla` | model | spirit-ai | open | https://github.com/Spirit-AI-Team/spirit-v1.5 | 2026-09-26 |
| `hy-embodied-vla` | model | tencent | open | https://github.com/Tencent-Hunyuan/Hy-Embodied-0.5-VLA | 2026-09-26 |
| `unifolm-vla` | model | unitree | open-weights | https://huggingface.co/unitreerobotics/UnifoLM-VLA-Base | 2026-09-26 |
| `alpamayo` | model | nvidia | open | https://github.com/NVlabs/alpamayo | 2026-09-26 |
| `eo-1` | model | ipec-community | open | https://huggingface.co/IPEC-COMMUNITY/EO-1-3B | 2026-09-26 |
| `nora` | model | declare-lab | open-weights | https://huggingface.co/declare-lab/nora | 2026-09-26 |
| `roboflamingo` | model | roboflamingo | open | https://github.com/RoboFlamingo/RoboFlamingo | 2026-09-26 |
| `vla-jepa` | model | ginwind | open | https://github.com/ginwind/VLA-JEPA | 2026-09-26 |
| `gemini-robotics` | model | google | closed | https://deepmind.google/models/gemini-robotics/ | 2026-09-26 |
| `open-x-embodiment` | dataset | google | open | https://github.com/google-deepmind/open_x_embodiment | 2026-09-26 |
| `droid` | dataset | droid-dataset | open | https://github.com/droid-dataset/droid | 2026-09-26 |
| `robomind` | dataset | x-humanoid | open | https://huggingface.co/datasets/x-humanoid-robomind/RoboMIND | 2026-09-26 |
| `agibot-world` | dataset | agibot | open | https://github.com/OpenDriveLab/AgiBot-World | 2026-09-26 |
| `nvidia-physical-ai-dataset` | dataset | nvidia | open | https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim | 2026-09-26 |
| `interndata-a1` | dataset | shanghai-ai-laboratory | open | https://huggingface.co/datasets/InternRobotics/InternData-A1 | 2026-09-26 |
| `so-101` | hardware | the-robot-studio | open | https://github.com/TheRobotStudio/SO-ARM100 | 2026-09-26 |
| `koch-v1-1` | hardware | jess-moss | open | https://github.com/jess-moss/koch-v1-1 | 2026-09-26 |
| `reachy-mini` | hardware | pollen-robotics | open | https://github.com/pollen-robotics/reachy_mini | 2026-09-26 |
| `aloha` | hardware | tonyzhaozh | open | https://github.com/tonyzhaozh/aloha | 2026-09-26 |
| `aloha-2` | hardware | google | open | https://aloha-2.github.io/ | 2026-09-26 |
| `berkeley-humanoid-lite` | hardware | uc-berkeley | open | https://github.com/HybridRobotics/berkeley-humanoid-lite | 2026-09-26 |
| `lekiwi` | hardware | sigrobotics-uiuc | open | https://github.com/SIGRobotics-UIUC/LeKiwi | 2026-09-26 |
| `openarm` | hardware | enactic | open | https://github.com/enactic/openarm | 2026-09-26 |

### `world_models`

| slug | type | org | status | primary source | fetched |
|---|---|---|---|---|---|
| `cosmos` | model | nvidia | open | https://github.com/NVIDIA/cosmos | 2026-09-26 |
| `v-jepa` | model | meta | open | https://github.com/facebookresearch/vjepa2 | 2026-09-26 |
| `hy-world` | model | tencent | open-weights | https://github.com/Tencent-Hunyuan/HY-World-2.0 | 2026-09-26 |
| `hunyuan-gamecraft` | model | tencent | open-weights | https://github.com/Tencent-Hunyuan/Hunyuan-GameCraft-1.0 | 2026-09-26 |
| `matrix-game` | model | skywork | open | https://github.com/SkyworkAI/Matrix-Game | 2026-09-26 |
| `lingbot-world` | model | robbyant | open-weights | https://github.com/Robbyant/lingbot-world | 2026-09-26 |
| `oasis` | model | etched | open | https://github.com/etched-ai/open-oasis | 2026-09-26 |
| `diamond` | model | eloialonso | open-weights | https://github.com/eloialonso/diamond | 2026-09-26 |
| `yume` | model | stdstu12 | open | https://github.com/stdstu12/YUME | 2026-09-26 |
| `aether` | model | shanghai-ai-laboratory | open | https://github.com/InternRobotics/Aether | 2026-09-26 |
| `genie-envisioner` | model | agibot | open-weights | https://github.com/AgibotTech/Genie-Envisioner-V1 | 2026-09-26 |
| `unifolm-wma` | model | unitree | open-weights | https://github.com/unitreerobotics/unifolm-world-model-action | 2026-09-26 |
| `gigaworld` | model | gigaai | open | https://github.com/open-gigaai/giga-world-0 | 2026-09-26 |
| `ctrl-world` | model | robert-gyj | open | https://github.com/Robert-gyj/Ctrl-World | 2026-09-26 |
| `boundless-world-model` | model | blm-lab | open-weights | https://github.com/boundless-large-model/boundless-world-model | 2026-09-26 |
| `dreamer` | model | danijar | open | https://github.com/danijar/dreamerv3 | 2026-09-26 |
| `td-mpc` | model | nicklashansen | open | https://github.com/nicklashansen/tdmpc2 | 2026-09-26 |
| `rynnworld` | model | alibaba-damo-academy | open | https://github.com/alibaba-damo-academy/RynnWorld-4D | 2026-09-26 |
| `dreamx-world` | model | amap | open | https://github.com/AMAP-ML/DreamX-World | 2026-09-26 |
| `genie` | model | google | closed | https://deepmind.google/models/genie/ | 2026-09-26 |
| `runway-gwm` | model | runway | closed | https://runway.com/research/introducing-runway-gwm-1 | 2026-09-26 |

## Parked candidates

Source ids refer to the evidence branch's fetch and web logs.

### `robotics_embodied`

| name | reason | source ids | fetch date |
|---|---|---|---|
| SO-100 arm | SKU of SO-101 line: prior hardware generation in the same repo (F0317); no row, ruled 2026-09-26 | F0317, F0051 | 2026-09-26 |
| Gazebo (gz-sim) | boundary: general robotics simulator with no learning surface; out, ruled 2026-09-26 | F0016, W0004 | 2026-09-26 |
| Webots | boundary: general robotics simulator; out, ruled 2026-09-26 | F0019, W0005 | 2026-09-26 |
| Drake | boundary: model-based planning/control toolbox, not a learning stack; out, ruled 2026-09-26 | F0018, F0170, F0268 | 2026-09-26 |
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
| L2D (yaak-ai) | coverage limit: driving dataset in HF top 40, in scope since driving is in; not researched | F0297 | 2026-09-26 |
| Retargeted AMASS (fleaven, 3 repos) | coverage limit: motion-retargeting data in HF top 40, not researched | F0297 | 2026-09-26 |
| MolmoAct-Midtraining-Mixture | SKU of molmoact (training mixture) | F0297 | 2026-09-26 |
| DOM / deform360 / tracker-pov / MetaFold / grand_tour_dataset / trex_dataset | coverage limit: HF robotics-dataset top 40, not researched | F0297 | 2026-09-26 |
| computer-use-large (markov-ai) | boundary: computer-use agent data, not physical | F0297 | 2026-09-26 |

### `world_models`

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
| Oasis 3 (Decart) | closed long-tail: hosted interactive world model, no fetched source ties it to the open Etched 500M release; kept apart, ruled 2026-09-26 | W0041 | 2026-09-26 |
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

## Identity notes for promotion

- **Renames found live.** WorldVLA redirects to RynnVLA-002, so it is folded into `rynnvla`. Genesis now
  lives at `Genesis-Embodied-AI/genesis-world`, ManiSkill at `mani-skill/ManiSkill`, and Genie
  Envisioner at `AgibotTech/Genie-Envisioner-V1`. `openvla/openvla` is marked a fork of
  `TRI-ML/prismatic-vlms`.
- **One row per line.** `mujoco` covers MJX and MuJoCo Warp. `gr00t` covers the N1.x line and its
  fine-tunes, `rdt` covers RDT-1B and RDT2, and `being-h` covers H0 and H0.5. `cosmos` covers Predict,
  Transfer, Reason and Cosmos 3, and `hy-world` covers HunyuanWorld 1.0, Voyager, WorldPlay and HY-World
  2.0. The maintainer may want any of these split.
- **Current-release status.** `lingbot-world` is open-weights because its current release (v2) is
  CC BY-NC-SA 4.0, while v1 was Apache-2.0. The `gr00t` line carries non-commercial fine-tunes beside
  the commercially usable base weights: `GR00T-N1.5-3B_Assemble_Trocar`, and `GR00T-H`, whose
  `nvidia-license` label links to the NVIDIA OneWay Noncommercial License.
- **Conflicting license declarations to settle at promotion.** `unifolm-wma`'s code is CC BY-NC-SA 4.0,
  while its Hub card metadata says apache-2.0. The `rynnworld` row pairs the RynnWorld-4D repository
  (license label `other`, text not read) with the RynnWorld-Teleop weights, and the action-conditioning
  evidence is for Teleop.
- **No license stated:** the wall-oss and MolmoAct2 weights, nora, the droid GitHub repository, and the
  Boundless World Model and DIAMOND Hub cards. The license text for `aloha-2`'s hardware was not fetched.
- **Licenses for the maintainer's license-rulings issue.** Products carrying these are deferred at
  promotion: the NVIDIA Open Model License, NVIDIA OneWay Noncommercial, the Isaac Sim additional
  software and materials license, OpenMDW-1.1, the Gemma terms on the LeRobot pi0 ports, the Galaxea
  G0 and G0.5 community licenses, the Tencent HY-World and Hunyuan community licenses (which exclude the
  EU, UK and South Korea), and the LTX-Video license inherited by the Genie Envisioner base weights.
- **Adoption channel.** V-JEPA's downloads come from its encoder checkpoints, which read like a vision
  backbone. The promotion PR should say which artifact carries the adoption.

## Open questions left for the maintainer

1. **The hardware ladder.** It was written for edge boards and modules. Does a robot arm or humanoid
   published as CAD, a bill of materials and firmware sit under `board`, or does the ladder need a
   robot-body rung? Reachy Mini sits outside the morphology quantity either way.
2. **Datasets.** The six researched robot datasets are a floor. Research the 16 parked Hub datasets
   before the promotion tranche is chosen, so the dataset ladder has enough rows to be checked.
3. **L2D.** Bringing driving in puts the parked L2D driving dataset in scope. It is parked as not
   researched, not rejected.
4. **Oasis.** Keep the open Etched 500M row alone, or merge Decart's hosted Oasis 3 into one line
   (which the current-release rule would make closed)? The two stay apart until a primary source links
   them.
5. **Rung 3 of the world-model quantity** holds game and robot world models, which one quantity orders
   only loosely. The promotion PR decides whether to split it.
6. **Org records.** `robbyant` stays until a primary source confirms an Ant Group affiliation. The
   `ai2` and `allen-institute-for-ai` records are still a pending merge, and MolmoAct sits under the
   latter.
