# Single source for rows.<slug>.yaml, the section-6 evidence tables and the section-2/8 numbers.
# Every value carries the fetch id it came from (F = rfetch body in raw/, W = web-log.tsv row).
# Fields: slug, name, type, org, status, art (registry artifacts), lic, alive, push, rel, adopt,
# members, handle, notes, src (signal ids that surfaced the candidate, for section 8).

R = []  # robotics_embodied accepted
W = []  # world_models accepted


def add(bucket, **k):
    bucket.append(k)


# ---------------------------------------------------------------- robotics: software
add(R, slug="lerobot", name="LeRobot", type="software", org="hugging-face", status="open",
    art=dict(github="huggingface/lerobot", pypi="lerobot"),
    lic="Apache-2.0 (F0002; PyPI metadata Apache-2.0 F0254)", alive="not archived, not fork (F0002)",
    push="2026-09-22 (F0002)", rel="v0.6.1, 2026-08-03 (F0387)",
    adopt="PyPI 318,966/month (F0254); 27,705 stars (F0002)", members="policies ACT, Diffusion, SmolVLA, pi0/pi0.5 ports, X-VLA (F0098)",
    handle="gh huggingface; hf lerobot", notes="README install path `pip install lerobot` (F0276)", src=["W0002", "F0098", "W0004"])
add(R, slug="mujoco", name="MuJoCo", type="software", org="google", status="open",
    art=dict(github="google-deepmind/mujoco", pypi="mujoco"),
    lic="Apache-2.0 (F0003)", alive="not archived, not fork (F0003)", push="2026-09-20 (F0003)",
    rel="3.14.0, 2026-09-22 (F0319)", adopt="PyPI 3,790,114/month (F0255); 15,241 stars (F0003)",
    members="MJX (in-repo); MuJoCo Warp google-deepmind/mujoco_warp, Apache-2.0, pushed 2026-09-24 (F0005), PyPI mujoco-warp 372,480/month (F0257)",
    handle="gh google-deepmind", notes="`pip install mujoco` (F0277). Warp folded in as a backend of the same product line; say so if the maintainer wants it split", src=["W0004", "W0005"])
add(R, slug="mujoco-playground", name="MuJoCo Playground", type="software", org="google", status="open",
    art=dict(github="google-deepmind/mujoco_playground", pypi="playground"),
    lic="Apache-2.0 (F0004)", alive="not archived, not fork (F0004)", push="2026-09-19 (F0004)",
    rel="v0.2.0, 2026-03-16 (F0388)", adopt="PyPI 9,928/month (F0256); 2,230 stars (F0004)", members="-",
    handle="gh google-deepmind", notes="`pip install playground` (F0286); PyPI repository_url matches (F0256)", src=["F0003"])
add(R, slug="isaac-lab", name="Isaac Lab", type="software", org="nvidia", status="open",
    art=dict(github="isaac-sim/IsaacLab", pypi="isaaclab"),
    lic="BSD-3-Clause (F0006)", alive="not archived, not fork (F0006)", push="2026-09-22 (F0006)",
    rel="v3.0.0-EA, 2026-09-16 (F0321); 3.0 Beta 2 on 2026-06-23 (W0022)", adopt="PyPI 9,747/month (F0258); 8,196 stars (F0006)",
    members="Isaac Lab-Arena parked separately", handle="gh isaac-sim",
    notes="PyPI isaaclab repository_url = isaac-sim/IsaacLab (F0258); README does not show the pip line (F0287)", src=["W0004", "W0005", "W0022"])
add(R, slug="isaac-sim", name="Isaac Sim", type="software", org="nvidia", status="open",
    art=dict(github="isaac-sim/IsaacSim"),
    lic="Apache-2.0 for repo code; building/running needs NVIDIA components under the Isaac Sim Additional Software and Materials License (F0159). GitHub label `other` (F0007)",
    alive="not archived, not fork (F0007)", push="2026-06-22 (F0007)", rel="v6.1.0, 2026-09-10 (F0322)",
    adopt="3,533 stars (F0007); PyPI isaacsim 3,864/month but repository_url empty, not declared (F0259)", members="-",
    handle="gh isaac-sim", notes="Open code, proprietary runtime dependencies: flag for ladder placement", src=["W0004", "W0027"])
add(R, slug="genesis", name="Genesis", type="software", org="genesis-embodied-ai", status="open",
    art=dict(github="Genesis-Embodied-AI/genesis-world", pypi="genesis-world"),
    lic="Apache-2.0 (F0091)", alive="not archived, not fork (F0091)", push="2026-09-25 (F0091)",
    rel="v1.4.2, 2026-09-23 (F0323)", adopt="PyPI 97,931/month (F0260); 29,987 stars (F0091)", members="-",
    handle="gh Genesis-Embodied-AI", notes="Repo renamed Genesis -> genesis-world; canonical from ungh (F0085). `pip install genesis-world` (F0278)", src=["W0004", "W0005"])
add(R, slug="maniskill", name="ManiSkill", type="software", org="mani-skill", status="open",
    art=dict(github="mani-skill/ManiSkill", pypi="mani-skill"),
    lic="Apache-2.0 (F0092)", alive="not archived, not fork (F0092)", push="2026-08-04 (F0092)",
    rel="v3.0.1, 2026-04-21 (F0324)", adopt="PyPI 19,481/month (F0261); 3,346 stars (F0092)", members="-",
    handle="gh mani-skill", notes="Moved haosulab/ManiSkill -> mani-skill/ManiSkill (F0090). README `pip install --upgrade mani_skill` (F0279)", src=["W0004"])
add(R, slug="habitat", name="Habitat", type="software", org="meta", status="open",
    art=dict(github="facebookresearch/habitat-sim"),
    lic="MIT (F0010; habitat-lab MIT F0011)", alive="not archived, not fork (F0010)", push="2026-07-21 (F0010); habitat-lab 2026-05-07 (F0011)",
    rel="v0.3.3, 2026-02-12 (F0325)", adopt="3,823 stars (F0010); PyPI habitat-sim is a stale 2023 dev build, 195/month, not declared (F0274)",
    members="habitat-sim + habitat-lab (F0011)", handle="gh facebookresearch", notes="Pitched at the platform; sim and lab collapse into one row", src=["W0004", "W0005"])
add(R, slug="robosuite", name="robosuite", type="software", org="arise-initiative", status="open",
    art=dict(github="ARISE-Initiative/robosuite", pypi="robosuite"),
    lic="MIT text behind label `other` (F0160, F0012)", alive="not archived, not fork (F0012)", push="2026-07-11 (F0012)",
    rel="v1.5.2, 2025-12-24 (F0326)", adopt="PyPI 322,909/month (F0262); 2,630 stars (F0012)", members="-",
    handle="gh ARISE-Initiative", notes="PyPI repository_url = ARISE-Initiative/robosuite (F0262); README fetched (F0280) shows no pip line", src=["W0004"])
add(R, slug="robocasa", name="RoboCasa", type="software", org="robocasa", status="open",
    art=dict(github="robocasa/robocasa"),
    lic="MIT text behind label `other` (F0161, F0013)", alive="not archived, not fork (F0013)", push="2026-06-26 (F0013)",
    rel="v1.0, 2026-02-18 (F0327)", adopt="1,493 stars (F0013); no PyPI package (404, F0263)", members="-",
    handle="gh robocasa", notes="Built on robosuite; separate product (benchmark + sim assets)", src=["W0004"])
add(R, slug="robomimic", name="robomimic", type="software", org="arise-initiative", status="open",
    art=dict(github="ARISE-Initiative/robomimic", pypi="robomimic"),
    lic="MIT (F0014)", alive="not archived, not fork (F0014)", push="2026-08-09 (F0014)",
    rel="v0.5.0, 2025-06-27 (F0328); PyPI still 0.3.0 from 2023-07-04 (F0264)", adopt="PyPI 48,056/month (F0264); 1,563 stars (F0014)",
    members="-", handle="gh ARISE-Initiative", notes="Found while verifying robosuite's org; not in the brief", src=["F0012"])
add(R, slug="pybullet", name="PyBullet", type="software", org="bullet-physics", status="open",
    art=dict(github="bulletphysics/bullet3", pypi="pybullet"),
    lic="zlib, except files under Extras and examples/ThirdPartyLibs (F0164); label `other` (F0015)", alive="not archived, not fork (F0015)",
    push="2025-10-22 (F0015)", rel="GitHub 3.25, 2022-04-24 (F0329); PyPI 3.2.7, 2025-01-30 (F0265)",
    adopt="PyPI 638,067/month (F0265); 14,743 stars (F0015)", members="-", handle="gh bulletphysics",
    notes="README `pip install pybullet` (F0281). Slowing: last push 11 months ago", src=["W0004", "W0005"])
add(R, slug="newton", name="Newton", type="software", org="newton-physics", status="open",
    art=dict(github="newton-physics/newton"),
    lic="Apache-2.0 (F0017)", alive="not archived, not fork (F0017)", push="2026-09-16 (F0017)",
    rel="v1.6.0, 2026-09-10 (F0330)", adopt="5,643 stars (F0017); PyPI newton-physics 566/month not declared, README does not name it (F0267, F0283)",
    members="-", handle="gh newton-physics", notes="Linux Foundation project from NVIDIA, Google DeepMind, Disney Research (W0020)", src=["W0005", "W0020"])
add(R, slug="brax", name="Brax", type="software", org="google", status="open",
    art=dict(github="google/brax", pypi="brax"),
    lic="Apache-2.0 (F0020)", alive="not archived, not fork (F0020)", push="2026-09-15 (F0020)",
    rel="v0.14.2, 2026-03-15 (F0331)", adopt="PyPI 27,561/month (F0269); 3,237 stars (F0020)", members="-",
    handle="gh google", notes="README `pip install brax` (F0285)", src=["W0005"])
add(R, slug="mjlab", name="mjlab", type="software", org="mujocolab", status="open",
    art=dict(github="mujocolab/mjlab", pypi="mjlab"),
    lic="Apache-2.0 (F0021)", alive="not archived, not fork (F0021)", push="2026-09-16 (F0021)",
    rel="v1.6.0, 2026-08-09 (F0332)", adopt="PyPI 84,063/month (F0270); 3,083 stars (F0021)", members="-",
    handle="gh mujocolab", notes="README carries the PyPI badge for mjlab (F0282)", src=["W0005"])
add(R, slug="robotwin", name="RoboTwin", type="software", org="robotwin-platform", status="open",
    art=dict(github="RoboTwin-Platform/RoboTwin"),
    lic="MIT (F0309)", alive="not archived, not fork (F0309)", push="2026-09-14 (F0309)",
    rel="tag `release`, 2026-02-26 (F0333)", adopt="2,868 stars (F0309)", members="RoboTwin 2.0 (ICML 2026, W0044)",
    handle="gh RoboTwin-Platform", notes="Bimanual data generator + benchmark; contested with benchmark_eval_data", src=["W0044"])
add(R, slug="roboverse", name="RoboVerse", type="software", org="roboverse", status="open",
    art=dict(github="RoboVerseOrg/RoboVerse"),
    lic="Apache-2.0 (F0310)", alive="not archived, not fork (F0310)", push="2026-09-22 (F0310)",
    rel="v1.0.0-alpha, 2025-08-31 (F0389)", adopt="1,863 stars (F0310); dataset RoboVerseOrg/roboverse_data 70,859 HF downloads (F0297)",
    members="-", handle="gh RoboVerseOrg", notes="Unified API over several simulators (W0044)", src=["W0044", "F0297"])

# ---------------------------------------------------------------- robotics: models
add(R, slug="gr00t", name="Isaac GR00T", type="model", org="nvidia", status="open-weights",
    art=dict(github="NVIDIA/Isaac-GR00T", huggingface_model="nvidia/GR00T-N1.7-3B"),
    lic="weights: NVIDIA Open Model License, 'ready for commercial/non-commercial use' (F0237); code Apache-2.0 (F0025, F0231); GR00T-N1.5-3B_Assemble_Trocar carries nvidia-oneway-noncommercial and nvidia/GR00T-H carries `nvidia-license`, whose link is the NVIDIA OneWay Noncommercial License (F0096)",
    alive="not archived, not fork (F0025)", push="2026-08-20 (F0025)", rel="n1.6.1-release, 2026-04-23 (F0390)",
    adopt="HF 125,319/30d for GR00T-N1.7-3B (F0151); 8,121 stars (F0025)", members="N1-2B, N1.5-3B, N1.6-3B, N1.7-3B, GR00T-H, GR00T-H-N1.7 (F0096)",
    handle="gh NVIDIA; hf nvidia", notes="Ruled into 5a on 2026-09-25 (brief)", src=["W0002", "W0022", "F0001"])
add(R, slug="pi0", name="π0 (openpi)", type="model", org="physical-intelligence", status="open-weights",
    art=dict(github="Physical-Intelligence/openpi"),
    lic="code Apache-2.0 (F0026, F0232); LeRobot ports of the weights carry `gemma` (F0098, F0153); PI's own checkpoint terms not fetched",
    alive="not archived, not fork (F0026)", push="2026-08-24 (F0026)", rel="no GitHub releases recorded (F0391)",
    adopt="13,932 stars (F0026); LeRobot port lerobot/pi0_base 39,973/30d (F0098) is not PI's artifact, not declared", members="pi0, pi0-FAST, pi0.5 (W0018, F0098). No open pi0.6 weights found in this run",
    handle="gh Physical-Intelligence; hf physical-intelligence (only `fast` tokenizer, F0112)", notes="Slug has no version token; pi0.5 is a release of the line", src=["W0002", "W0007", "W0018"])
add(R, slug="smolvla", name="SmolVLA", type="model", org="hugging-face", status="open",
    art=dict(huggingface_model="lerobot/smolvla_base"),
    lic="Apache-2.0 on the card (F0152)", alive="HF repo modified 2026-09-17 (F0152)", push="n/a (code lives in huggingface/lerobot, F0002)",
    rel="HF lastModified 2026-09-17 (F0152)", adopt="HF 71,362/30d (F0152)", members="smolvla_base, smolvla_libero, smolvla_robotwin (F0098)",
    handle="hf lerobot", notes="Separate from the LeRobot framework row (model vs engine)", src=["W0002", "W0007"])
add(R, slug="openvla", name="OpenVLA", type="model", org="openvla", status="open-weights",
    art=dict(github="openvla/openvla", huggingface_model="openvla/openvla-7b"),
    lic="MIT on code and card (F0027, F0113); Llama-2 base terms not fetched", alive="not archived; fork=True of TRI-ML/prismatic-vlms (F0027)",
    push="2025-03-23 (F0027)", rel="no GitHub releases recorded (F0392)", adopt="HF 445,187/30d (F0113); 2,317 stars (F0027)",
    members="openvla-7b, LIBERO fine-tunes, v01-7b (F0113)", handle="gh openvla; hf openvla",
    notes="Dormant 18 months, yet the most-downloaded robotics model on the Hub (F0298). GitHub marks the repo a fork", src=["W0001", "W0002", "W0007"])
add(R, slug="octo", name="Octo", type="model", org="octo-models", status="open",
    art=dict(github="octo-models/octo", huggingface_model="rail-berkeley/octo-base-1.5"),
    lic="MIT (F0028, F0114)", alive="not archived, not fork (F0028)", push="2024-07-31 (F0028)", rel="v1.5, 2024-05-24 (F0393)",
    adopt="HF 128/30d base-1.5, 346 small-1.5 (F0114); 1,789 stars (F0028)", members="octo-small, octo-base, 1.5 variants (F0114)",
    handle="gh octo-models; hf rail-berkeley", notes="Dormant since 2024-07 (matches the brief)", src=["W0007"])
add(R, slug="rdt", name="RDT (Robotics Diffusion Transformer)", type="model", org="thu-ml", status="open",
    art=dict(github="thu-ml/RDT2", huggingface_model="robotics-diffusion-transformer/RDT2-VQ"),
    lic="RDT2 Apache-2.0 (F0030, F0115); RDT-1B MIT (F0029, F0115)", alive="not archived, not fork (F0030)",
    push="2026-02-07 RDT2 (F0030); 2026-01-21 RDT-1 (F0029)", rel="no GitHub releases recorded (F0394)",
    adopt="HF 218/30d RDT2-VQ, 546 rdt-1b (F0115); 806 + 1,804 stars (F0030, F0029)", members="rdt-170m, rdt-1b, RDT2-VQ, RDT2-FM (F0115)",
    handle="gh thu-ml; hf robotics-diffusion-transformer", notes="Governing release RDT2", src=["F0001"])
add(R, slug="x-vla", name="X-VLA", type="model", org="tsinghua-air", status="open",
    art=dict(github="2toinf/X-VLA", huggingface_model="2toINF/X-VLA-Pt"),
    lic="Apache-2.0 (F0031, F0116)", alive="not archived, not fork (F0031)", push="2026-06-10 (F0031)", rel="no GitHub releases recorded (F0395)",
    adopt="HF 10,921/30d (F0116); LeRobot port 4,459 (F0098)", members="X-VLA-Pt + 10 task fine-tunes (F0116)",
    handle="gh 2toinf; hf 2toINF", notes="Org per the sinanlabs index: Tsinghua AIR (F0001)", src=["W0002", "F0001"])
add(R, slug="gigabrain", name="GigaBrain", type="model", org="gigaai", status="open",
    art=dict(github="open-gigaai/giga-brain-0", huggingface_model="open-gigaai/GigaBrain-0.7-3.5B-Base"),
    lic="Apache-2.0 (F0032, F0156)", alive="not archived, not fork (F0032)", push="2026-02-13 (F0032)", rel="no GitHub releases recorded (F0396)",
    adopt="HF 1,891/30d (F0156); 2,263 stars (F0032)", members="GigaBrain-0, 0.1, 0.7 (F0102)", handle="gh open-gigaai; hf open-gigaai",
    notes="Not in the brief; surfaced by search (W0023)", src=["W0023"])
add(R, slug="galaxea-g0", name="Galaxea G0", type="model", org="galaxea", status="open-weights",
    art=dict(github="OpenGalaxea/GalaxeaVLA", huggingface_model="OpenGalaxea/G05"),
    lic="date-split: Apache-2.0 before 2026-01-04; G0 PLUS Community License (non-commercial + limited patent) to 2026-06-16; G0.5 Community License (non-commercial + limited patent) after (F0247). G0-VLA card cc-by-nc-sa-4.0 (F0099); G05 card g05-community-license, gated (F0155)",
    alive="not archived, not fork (F0033)", push="2026-08-13 (F0033)", rel="no GitHub releases recorded (F0397)",
    adopt="HF 0/30d on all three repos (F0099); 799 stars (F0033)", members="G0 (Plus 3B, Tiny 250M), G0.5 (W0023, F0099)",
    handle="gh OpenGalaxea; hf OpenGalaxea", notes="Custom NC licenses: flag. Adoption instrument reads zero", src=["W0023", "F0001"])
add(R, slug="lingbot-vla", name="LingBot-VLA", type="model", org="robbyant", status="open",
    art=dict(github="Robbyant/lingbot-vla", huggingface_model="robbyant/lingbot-vla-4b"),
    lic="Apache-2.0 (F0034, F0235; card body F0240)", alive="not archived, not fork (F0034)", push="2026-06-11 (F0034)", rel="no GitHub releases recorded (F0398)",
    adopt="HF 1,249/30d 4b, 1,245 v2-6b (F0100); 1,837 stars (F0034)", members="lingbot-vla-4b, -depth, v2-6b (F0100)",
    handle="gh Robbyant; hf robbyant", notes="Robbyant is Ant Group's embodied unit per F0001; reuse ant-group org? (question 6)", src=["F0001", "F0100"])
add(R, slug="internvla", name="InternVLA", type="model", org="shanghai-ai-laboratory", status="open-weights",
    art=dict(github="InternRobotics/InternVLA-A-series", huggingface_model="InternRobotics/InternVLA-A1.5-base"),
    lic="CC BY-NC-SA 4.0, copyright Shanghai AI Laboratory (F0211); weights cc-by-nc-sa-4.0 (F0101); M1 code MIT (F0035)",
    alive="not archived, not fork (F0093)", push="2026-09-14 (F0093)", rel="no GitHub releases recorded (F0399)",
    adopt="HF 125/30d A1.5-base, 111 M1 (F0101); 558 stars (F0093)", members="InternVLA-M1, A1-3B, A1.5, N1 navigation (F0101)",
    handle="gh InternRobotics; hf InternRobotics", notes="Repo renamed InternVLA-A1 -> InternVLA-A-series (F0087)", src=["W0007", "F0001"])
add(R, slug="wall-oss", name="WALL-OSS", type="model", org="x-square-robot", status="open-weights",
    art=dict(github="X-Square-Robot/wall-x", huggingface_model="x-square-robot/wall-oss-flow"),
    lic="code Apache-2.0 (F0037, F0234); weights card states no license (F0148, F0239)", alive="not archived, not fork (F0037)",
    push="2026-09-18 (F0037)", rel="no GitHub releases recorded (F0400)", adopt="HF 998/30d (F0148); 1,278 stars (F0037)",
    members="wall-oss-flow, -fast, -0.5, -flow-0.1 (F0117)", handle="gh X-Square-Robot; hf x-square-robot", notes="Weights license unstated", src=["W0023", "F0001"])
add(R, slug="molmoact", name="MolmoAct", type="model", org="allen-institute-for-ai", status="open-weights",
    art=dict(github="allenai/molmoact", huggingface_model="allenai/MolmoAct2"),
    lic="code Apache-2.0 (F0038, F0233); MolmoAct 1 weights apache-2.0 (F0118); MolmoAct2 card has no license field (F0150, F0238)",
    alive="not archived, not fork (F0038)", push="2026-05-11 (F0038)", rel="no GitHub releases recorded (F0401)",
    adopt="HF 20,533/30d MolmoAct2 (F0150); 389 stars (F0038)", members="MolmoAct-7B-D (2025), MolmoAct2, -Think, -SO100_101, -DROID (F0118)",
    handle="gh allenai; hf allenai", notes="MolmoAct2 (2026-05) not in the brief; index also has an `ai2` org slug (question 6)", src=["F0001", "F0298"])
add(R, slug="cogact", name="CogACT", type="model", org="microsoft", status="open",
    art=dict(github="microsoft/CogACT", huggingface_model="CogACT/CogACT-Base"),
    lic="MIT (F0039, F0119)", alive="not archived, not fork (F0039)", push="2025-10-30 (F0039)", rel="no GitHub releases recorded (F0402)",
    adopt="HF 968/30d (F0119); 433 stars (F0039)", members="Small, Base, Large (F0119)", handle="gh microsoft; hf CogACT", notes="-", src=["F0001"])
add(R, slug="spatialvla", name="SpatialVLA", type="model", org="shanghai-ai-laboratory", status="open",
    art=dict(github="SpatialVLA/SpatialVLA", huggingface_model="IPEC-COMMUNITY/spatialvla-4b-224-pt"),
    lic="MIT in README (F0248), no GitHub label (F0040); card MIT (F0120)", alive="not archived, not fork (F0040)", push="2025-06-23 (F0040)",
    rel="no GitHub releases recorded (F0403)", adopt="HF 1,307/30d (F0120); 727 stars (F0040)", members="4b-224-pt, -mix, bridge/fractal SFT (F0120)",
    handle="gh SpatialVLA; hf IPEC-COMMUNITY", notes="Org attribution (Shanghai AI Lab et al.) from F0001 only", src=["F0001"])
add(R, slug="univla", name="UniVLA", type="model", org="opendrivelab", status="open",
    art=dict(github="OpenDriveLab/UniVLA", huggingface_model="qwbu/univla-7b"),
    lic="Apache-2.0 (F0041, F0121)", alive="not archived, not fork (F0041)", push="2025-11-19 (F0041)", rel="no GitHub releases recorded (F0404)",
    adopt="HF 240/30d (F0121); 1,134 stars (F0041)", members="univla-7b + SFT variants (F0121)", handle="gh OpenDriveLab; hf qwbu", notes="-", src=["F0001"])
add(R, slug="go-1", name="GO-1 (Genie Operator-1)", type="model", org="agibot", status="open-weights",
    art=dict(huggingface_model="agibot-world/GO-1"),
    lic="CC BY-NC-SA 4.0 on the card (F0241)", alive="HF modified 2025-09-21 (F0147)", push="n/a (HF only declared)", rel="HF lastModified 2025-09-21 (F0147)",
    adopt="HF 123/30d (F0147)", members="GO-1, GO-1-Air (F0110)", handle="hf agibot-world",
    notes="Code sits in OpenDriveLab/AgiBot-World (F0001), which the agibot-world dataset row claims; so no github here", src=["F0001", "F0110"])
add(R, slug="rynnvla", name="RynnVLA", type="model", org="alibaba-damo-academy", status="open",
    art=dict(github="alibaba-damo-academy/RynnVLA-002", huggingface_model="Alibaba-DAMO-Academy/RynnVLA-001-7B-Base"),
    lic="Apache-2.0 in README (F0251); RynnVLA-001 Apache-2.0 (F0043, F0135)", alive="not archived, not fork (F0094)",
    push="2025-12-02 RynnVLA-002 (F0094); 2026-01-23 RynnVLA-001 (F0043)", rel="no GitHub releases recorded (F0405)",
    adopt="HF 13/30d (F0135); 1,131 stars (F0094)", members="RynnVLA-001, RynnVLA-002 (formerly WorldVLA: alibaba-damo-academy/WorldVLA redirects here, F0088; HF WorldVLA F0133)",
    handle="gh alibaba-damo-academy; hf Alibaba-DAMO-Academy", notes="WorldVLA is now a retired alias of this line", src=["W0014", "F0001", "F0088"])
add(R, slug="xiaomi-robotics", name="Xiaomi-Robotics", type="model", org="xiaomi", status="open",
    art=dict(github="XiaomiRobotics/Xiaomi-Robotics-0", huggingface_model="XiaomiRobotics/Xiaomi-Robotics-0-Pretrain"),
    lic="Apache-2.0 (F0044, F0103)", alive="not archived, not fork (F0044)", push="2026-08-03 (F0044)", rel="no GitHub releases recorded (F0406)",
    adopt="HF 88/30d 0-Pretrain; 785 Robotics-1-RoboCasa365 (F0103); 659 stars (F0044)", members="Xiaomi-Robotics-0, -1 (5B), -U0 (F0103)",
    handle="gh XiaomiRobotics; hf XiaomiRobotics", notes="2026 release not in the brief (W0001)", src=["W0001", "W0028"])
add(R, slug="being-h", name="Being-H", type="model", org="beingbeyond", status="open",
    art=dict(github="BeingBeyond/Being-H0", huggingface_model="BeingBeyond/Being-H05-2B"),
    lic="code MIT (F0045); Being-H0 weights MIT, Being-H0.5 weights apache-2.0 (F0123)", alive="not archived, not fork (F0045)", push="2026-05-04 (F0045)",
    rel="no GitHub releases recorded (F0407)", adopt="HF 53/30d (F0123); 59 stars (F0045)", members="Being-H0 1B/8B/14B, Being-H0.5-2B (F0123)",
    handle="gh BeingBeyond; hf BeingBeyond", notes="Small signal", src=["F0001"])
add(R, slug="spirit-vla", name="Spirit (Spirit AI VLA)", type="model", org="spirit-ai", status="open",
    art=dict(github="Spirit-AI-Team/spirit-v1.5", huggingface_model="Spirit-AI-robotics/Spirit-v1.5"),
    lic="code MIT (F0046); weights apache-2.0 (F0124)", alive="not archived, not fork (F0046)", push="2026-05-29 (F0046)", rel="no GitHub releases recorded (F0408)",
    adopt="HF 145/30d (F0124); 661 stars (F0046)", members="Spirit-v1.5 (F0124)", handle="gh Spirit-AI-Team; hf Spirit-AI-robotics",
    notes="Slug `spirit` alone is too generic", src=["F0001"])
add(R, slug="hy-embodied-vla", name="Hy-Embodied VLA", type="model", org="tencent", status="open",
    art=dict(github="Tencent-Hunyuan/Hy-Embodied-0.5-VLA", huggingface_model="tencent/Hy-Embodied-0.5-VLA-UMI"),
    lic="Apache-2.0 with a Tencent header (F0316); label `other` (F0305); card apache-2.0 (F0300)", alive="not archived, not fork (F0305)",
    push="2026-08-04 (F0305)", rel="no GitHub releases recorded (F0409)", adopt="HF 262/30d (F0300); 301 stars (F0305)",
    members="Hy-Embodied-0.5-VLA-UMI, -RoboTwin; dataset Hy-Embodied-0.5-VLA-Data (W0035)", handle="gh Tencent-Hunyuan; hf tencent",
    notes="2026-06 release not in the brief (W0035). The Hy-Embodied VLMs are parked to multimodal_models", src=["W0035", "F0297"])
add(R, slug="unifolm-vla", name="UnifoLM-VLA", type="model", org="unitree", status="open-weights",
    art=dict(huggingface_model="unitreerobotics/UnifoLM-VLA-Base"),
    lic="CC BY-NC-SA 4.0 on the card (F0243)", alive="HF modified 2026-03-06 (F0157)", push="n/a (HF only)", rel="HF lastModified 2026-03-06 (F0157)",
    adopt="HF 175/30d (F0157)", members="UnifoLM-VLA-Base, -Libero (F0111)", handle="hf unitreerobotics", notes="Unitree's own VLA; Unitree SDKs parked", src=["F0111"])
add(R, slug="alpamayo", name="Alpamayo", type="model", org="nvidia", status="open",
    art=dict(github="NVlabs/alpamayo", huggingface_model="nvidia/Alpamayo-1.5-10B"),
    lic="code Apache-2.0 (F0303); weights openmdw-1.1 (F0299)", alive="not archived, not fork (F0303)", push="2026-09-09 (F0303)", rel="no GitHub releases recorded (F0410)",
    adopt="HF 30,625/30d (F0299); 2,028 stars (F0303)", members="Alpamayo-R1-10B, 1.5-10B, 2-Super (F0299, W0034)", handle="gh NVlabs; hf nvidia",
    notes="Driving VLA: in only if autonomous driving counts as embodied (question 3)", src=["F0298", "W0034"])
add(R, slug="eo-1", name="EO-1", type="model", org="ipec-community", status="open",
    art=dict(huggingface_model="IPEC-COMMUNITY/EO-1-3B"),
    lic="MIT on the card (F0120)", alive="HF modified 2026-01-14 (F0120)", push="n/a (HF only)", rel="HF lastModified 2026-01-14 (F0120)",
    adopt="HF 968/30d (F0120)", members="EO-1-3B, eo1-qwen25_vl bridge/fractal (F0120)", handle="hf IPEC-COMMUNITY", notes="GitHub IPEC-PUBLIC/EO-1 named in F0001, not fetched, not declared", src=["F0001", "F0120"])
add(R, slug="nora", name="NORA", type="model", org="declare-lab", status="open-weights",
    art=dict(huggingface_model="declare-lab/nora"),
    lic="card states no license (F0132)", alive="HF modified 2025-08-27 (F0132)", push="n/a (HF only)", rel="HF lastModified 2025-08-27 (F0132)",
    adopt="HF 600/30d nora, 359 nora-long (F0132)", members="nora, nora-long, LIBERO fine-tunes (F0132)", handle="hf declare-lab",
    notes="License absent: record, do not assume", src=["F0001"])
add(R, slug="roboflamingo", name="RoboFlamingo", type="model", org="roboflamingo", status="open",
    art=dict(github="RoboFlamingo/RoboFlamingo"),
    lic="MIT (F0047)", alive="not archived, not fork (F0047)", push="2024-05-08 (F0047)", rel="no GitHub releases recorded (F0411)",
    adopt="437 stars only (F0047)", members="-", handle="gh RoboFlamingo", notes="Dormant 28 months; brief lead", src=["W0028", "W0007"])
add(R, slug="vla-jepa", name="VLA-JEPA", type="model", org="ginwind", status="open",
    art=dict(github="ginwind/VLA-JEPA", huggingface_model="ginwind/VLA-JEPA"),
    lic="README badge Code License Apache-2.0 (F0253); no GitHub label (F0048); card apache-2.0 (F0125)", alive="not archived, not fork (F0048)",
    push="2026-05-01 (F0048)", rel="no GitHub releases recorded (F0412)", adopt="HF 0/30d (F0125); 199 stars (F0048)", members="ported as lerobot/VLA-JEPA-Pretrain (W0011)",
    handle="gh ginwind; hf ginwind", notes="Brief lists it under 5b; it outputs actions, so it lands here (world model is internal)", src=["W0011"])
add(R, slug="gemini-robotics", name="Gemini Robotics", type="model", org="google", status="closed",
    art=dict(homepage="https://deepmind.google/models/gemini-robotics/"),
    lic="proprietary; no weights (W0036)", alive="live product page (W0036)", push="n/a", rel="Gemini Robotics ER 2 announced 2026-07-30, public via Gemini API (W0015)",
    adopt="none measurable (hosted API; trusted-tester program of 100+, W0036)", members="Gemini Robotics 2, ER 2, On-Device 2 (W0036)",
    handle="-", notes="Closed frontier comparator; capability surface = the robotics model family, not Gemini", src=["W0015", "W0036", "W0007"])

# ---------------------------------------------------------------- robotics: datasets
add(R, slug="open-x-embodiment", name="Open X-Embodiment", type="dataset", org="google", status="open",
    art=dict(github="google-deepmind/open_x_embodiment"),
    lic="repo Apache-2.0 (F0049); per-dataset terms not fetched", alive="not archived, not fork (F0049)", push="2025-11-05 (F0049)", rel="no GitHub releases recorded (F0413)",
    adopt="2,045 stars (F0049); LeRobot-format mirrors of member sets 130k-220k HF downloads (F0297), not declared", members="58 constituent datasets (W0021)",
    handle="gh google-deepmind", notes="-", src=["W0021", "W0002"])
add(R, slug="droid", name="DROID", type="dataset", org="droid-dataset", status="open",
    art=dict(github="droid-dataset/droid", huggingface_dataset="lerobot/droid_1.0.1"),
    lic="HF card apache-2.0 (F0290); GitHub carries no license label or README line (F0050, F0250)", alive="not archived, not fork (F0050)",
    push="2025-09-15 (F0050)", rel="HF lastModified 2026-06-25 (F0290)", adopt="HF 16,522/30d lerobot/droid_1.0.1 (F0290); cadene/droid_1.0.1 252,508 (F0297)",
    members="92,223 episodes (W0032)", handle="gh droid-dataset; hf lerobot", notes="Declared HF id is the LeRobot-format release, not a DROID-team repo", src=["W0032", "W0021", "F0297"])
add(R, slug="robomind", name="RoboMIND", type="dataset", org="x-humanoid", status="open",
    art=dict(huggingface_dataset="x-humanoid-robomind/RoboMIND"),
    lic="apache-2.0 on the card, gated (F0292)", alive="HF modified 2026-04-14 (F0292)", push="n/a", rel="HF lastModified 2026-04-14 (F0292)",
    adopt="HF 59,850/30d (F0292)", members="-", handle="hf x-humanoid-robomind", notes="Gated behind contact sharing (W0032)", src=["W0032"])
add(R, slug="agibot-world", name="AgiBot World", type="dataset", org="agibot", status="open",
    art=dict(github="OpenDriveLab/AgiBot-World", huggingface_dataset="agibot-world/AgiBotWorld-Beta"),
    lic="CC BY-NC-SA 4.0 (README F0249; gated prompt F0293); AgiBotWorld2026 cc-by-nc-sa-4.0 (F0294)", alive="not archived, not fork (F0042)",
    push="2026-05-29 (F0042)", rel="no GitHub releases recorded (F0415)", adopt="HF 92,675/30d Beta (F0293); AgiBotWorld2026 266,412 (F0294); Alpha 35,703 (F0295)",
    members="Alpha (2024-12), Beta, AgiBotWorld2026 (F0293-F0295)", handle="gh OpenDriveLab; hf agibot-world",
    notes="Dataset versions may each be their own identity (question 5). Status `open` means downloadable; NC license", src=["W0021", "W0032"])
add(R, slug="nvidia-physical-ai-dataset", name="NVIDIA Physical AI Dataset", type="dataset", org="nvidia", status="open",
    art=dict(huggingface_dataset="nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim"),
    lic="cc-by-4.0 (F0296)", alive="HF modified 2026-03-05 (F0296)", push="n/a", rel="HF lastModified 2026-03-05 (F0296)",
    adopt="HF 1,267,768/30d (F0296): top robotics dataset on the Hub (F0297)", members="GR00T-X-Embodiment-Sim, Open-H-Embodiment 176,135 (F0296)",
    handle="hf nvidia", notes="Pitched at NVIDIA's named collection (W0021)", src=["W0021", "F0297"])
add(R, slug="interndata-a1", name="InternData-A1", type="dataset", org="shanghai-ai-laboratory", status="open",
    art=dict(huggingface_dataset="InternRobotics/InternData-A1"),
    lic="CC BY-NC-SA 4.0 (gated community prompt, F0302)", alive="HF dataset live (F0302)", push="n/a", rel="released 2025-07-26 per license prompt (F0302)",
    adopt="HF 113,556/30d (F0302)", members="-", handle="hf InternRobotics", notes="Surfaced by the HF robotics-dataset sort (F0297)", src=["F0297"])

# ---------------------------------------------------------------- robotics: hardware
add(R, slug="so-101", name="SO-101 arm", type="hardware", org="the-robot-studio", status="open",
    art=dict(github="TheRobotStudio/SO-ARM100"),
    lic="Apache-2.0 (F0051)", alive="not archived, not fork (F0051)", push="2026-09-06 (F0051)", rel="v0.1.1, 2024-05-17 (F0416)",
    adopt="7,401 stars (F0051); no download channel", members="repo carries SO-100 and SO-101 (F0317)", handle="gh TheRobotStudio",
    notes="Hardware: generation is identity, so SO-100 is parked as the prior generation sharing this repo", src=["W0019", "W0033"])
add(R, slug="koch-v1-1", name="Koch v1.1 arm", type="hardware", org="jess-moss", status="open",
    art=dict(github="jess-moss/koch-v1-1"),
    lic="Apache-2.0 (F0052)", alive="not archived, not fork (F0052)", push="2024-09-17 (F0052)", rel="no GitHub releases recorded (F0417)",
    adopt="621 stars (F0052)", members="-", handle="gh jess-moss", notes="Dormant 2 years; LeRobot documents it (W0033)", src=["W0033"])
add(R, slug="reachy-mini", name="Reachy Mini", type="hardware", org="pollen-robotics", status="open",
    art=dict(github="pollen-robotics/reachy_mini"),
    lic="Apache-2.0 (F0053)", alive="not archived, not fork (F0053)", push="2026-09-21 (F0053)", rel="v1.10.0rc6, 2026-08-13 (F0418)",
    adopt="1,515 stars (F0053); PyPI reachy-mini 12,028/month not declared (no repository_url, F0273)", members="Lite, Wireless (W0019)",
    handle="gh pollen-robotics", notes="Pollen Robotics / Hugging Face desktop robot (W0019)", src=["W0019"])
add(R, slug="aloha", name="ALOHA", type="hardware", org="tonyzhaozh", status="open",
    art=dict(github="tonyzhaozh/aloha"),
    lic="MIT (F0054)", alive="not archived, not fork (F0054)", push="2024-04-19 (F0054)", rel="no GitHub releases recorded (F0419)",
    adopt="2,274 stars (F0054)", members="-", handle="gh tonyzhaozh", notes="First generation, dormant; org is a personal handle (question 6)", src=["W0019", "W0033"])
add(R, slug="aloha-2", name="ALOHA 2", type="hardware", org="google", status="open",
    art=dict(arxiv="2405.02292", homepage="https://aloha-2.github.io/"),
    lic="'open source all hardware designs' (F0442, F0443); license text not fetched", alive="project page live (F0443)", push="n/a", rel="arXiv submitted 2024-02-07 (F0442)",
    adopt="none measurable", members="MuJoCo model included (F0442)", handle="-", notes="Google DeepMind + Stanford (W0033). Weakest-evidence row (hardware, no repo)", src=["W0033"])
add(R, slug="berkeley-humanoid-lite", name="Berkeley Humanoid Lite", type="hardware", org="uc-berkeley", status="open",
    art=dict(github="HybridRobotics/berkeley-humanoid-lite"),
    lic="MIT (F0055)", alive="not archived, not fork (F0055)", push="2026-03-10 (F0055)", rel="v1.1.0, 2025-09-07 (F0420)",
    adopt="1,878 stars (F0055)", members="-", handle="gh HybridRobotics", notes="Sub-$5,000 open humanoid (W0019)", src=["W0019"])
add(R, slug="lekiwi", name="LeKiwi", type="hardware", org="sigrobotics-uiuc", status="open",
    art=dict(github="SIGRobotics-UIUC/LeKiwi"),
    lic="Apache-2.0 (F0056)", alive="not archived, not fork (F0056)", push="2025-07-10 (F0056)", rel="no GitHub releases recorded (F0421)",
    adopt="803 stars (F0056)", members="-", handle="gh SIGRobotics-UIUC", notes="-", src=["W0019", "W0033"])
add(R, slug="openarm", name="OpenArm", type="hardware", org="enactic", status="open",
    art=dict(github="enactic/openarm"),
    lic="Apache-2.0 (F0057)", alive="not archived, not fork (F0057)", push="2026-09-14 (F0057)", rel="1.1, 2025-10-31 (F0422)",
    adopt="3,369 stars (F0057)", members="-", handle="gh enactic", notes="$6,500 bimanual system (W0033)", src=["W0019", "W0033"])

# ---------------------------------------------------------------- world models
add(W, slug="cosmos", name="NVIDIA Cosmos", type="model", org="nvidia", status="open",
    art=dict(github="NVIDIA/cosmos", huggingface_model="nvidia/Cosmos3-Nano"),
    lic="Cosmos 3: OpenMDW-1.1 (LICENSE F0195; cards openmdw1.1-license F0144); earlier Predict/Transfer/Reason 2.x: NVIDIA Open Model License, gated=auto (F0145, F0097)",
    alive="not archived, not fork (F0061)", push="2026-09-23 (F0061)", rel="Cosmos3, 2026-06-01 (F0423)",
    adopt="HF 126,107/30d Cosmos3-Nano (F0144); Cosmos3-Edge 1,380,628 (F0097); 11,904 stars (F0061)",
    members="Cosmos3 Edge/Nano/Super; Predict 2/2.5, Transfer 2.5, Reason 1/2, Embed1 (F0097); nvidia-cosmos/cosmos-predict2.5 (F0062)",
    handle="gh NVIDIA, nvidia-cosmos; hf nvidia", notes="Governing release Cosmos 3 (OpenMDW, permissive). Cosmos-Reason is a VLM: contested with multimodal_models", src=["W0003", "W0010"])
add(W, slug="v-jepa", name="V-JEPA", type="model", org="meta", status="open",
    art=dict(github="facebookresearch/vjepa2", huggingface_model="facebook/vjepa2-vitg-fpc64-256"),
    lic="code MIT (F0063); weights MIT (ViT-L/H) and apache-2.0 (ViT-g) (F0109)", alive="not archived, not fork (F0063)", push="2026-03-23 (F0063)",
    rel="no GitHub releases recorded (F0424)", adopt="HF 200,430/30d vitl, 113,699 vitg (F0109); 4,472 stars (F0063)",
    members="V-JEPA 2 ViT-L/H/g, V-JEPA 2-AC action-conditioned (F0001), 2.1 (W0011)", handle="gh facebookresearch; hf facebook",
    notes="Encoder checkpoints dominate downloads: overlaps classic_ml_cv vision backbones", src=["W0011", "F0001"])
add(W, slug="hy-world", name="HY-World (HunyuanWorld)", type="model", org="tencent", status="open-weights",
    art=dict(github="Tencent-Hunyuan/HY-World-2.0", huggingface_model="tencent/HY-World-2.0"),
    lic="Tencent HY-World 2.0 Community License, excludes EU/UK/South Korea (F0200). HunyuanWorld-1.0, Voyager, WorldPlay: own Tencent community licenses (F0196, F0201, F0206)",
    alive="not archived, not fork (F0065)", push="2026-08-12 (F0065)", rel="no GitHub releases recorded (F0425)",
    adopt="HF 3,790/30d HY-World-2.0 (F0104); HunyuanWorld-1 4,818 (F0138); 2,674 stars (F0065)",
    members="HunyuanWorld-1.0, HunyuanWorld-Voyager (camera-conditioned), HY-WorldPlay (interactive), HY-World 2.0 (F0138-F0140, F0306)",
    handle="gh Tencent-Hunyuan; hf tencent", notes="1.0 and 2.0 generate 3D scenes (fails the litmus alone); Voyager is conditioned on camera input (W0017); WorldPlay examined for license only", src=["W0009", "W0013", "W0017"])
add(W, slug="hunyuan-gamecraft", name="Hunyuan-GameCraft", type="model", org="tencent", status="open-weights",
    art=dict(github="Tencent-Hunyuan/Hunyuan-GameCraft-1.0", huggingface_model="tencent/Hunyuan-GameCraft-1.0"),
    lic="Tencent Hunyuan Community License, excludes EU/UK/South Korea (F0202)", alive="not archived, not fork (F0067)", push="2025-11-28 (F0067)",
    rel="no GitHub releases recorded (F0426)", adopt="HF 77/30d (F0105); 741 stars (F0067)", members="GameCraft-1.0; GameCraft-2 paper (W0009)",
    handle="gh Tencent-Hunyuan; hf tencent", notes="Keyboard/mouse actions mapped to camera space (W0030)", src=["W0009", "W0030"])
add(W, slug="matrix-game", name="Matrix-Game", type="model", org="skywork", status="open",
    art=dict(github="SkyworkAI/Matrix-Game", huggingface_model="Skywork/Matrix-Game-3.0"),
    lic="repo MIT (F0068); Matrix-Game-3.0 weights apache-2.0, 2.0 and 1.0 MIT (F0106)", alive="not archived, not fork (F0068)", push="2026-03-30 (F0068)",
    rel="no GitHub releases recorded (F0427)", adopt="HF 174/30d 3.0, 276 2.0 (F0106); 2,341 stars (F0068)", members="Matrix-Game 1.0, 2.0, 3.0 (F0106)",
    handle="gh SkyworkAI; hf Skywork", notes="Matrix-3D (3D scene gen) is a separate product, parked", src=["W0009", "W0030"])
add(W, slug="lingbot-world", name="LingBot-World", type="model", org="robbyant", status="open-weights",
    art=dict(github="Robbyant/lingbot-world", huggingface_model="robbyant/lingbot-world-fast"),
    lic="v1 Apache-2.0 (F0069; card F0100); v2 CC BY-NC-SA 4.0 (F0209)", alive="not archived, not fork (F0069)", push="2026-07-09 v1 (F0069); 2026-09-10 v2 (F0070)",
    rel="no GitHub releases recorded (F0428)", adopt="HF 21,007/30d lingbot-world-fast (F0100); 4,487 + 1,822 stars (F0069, F0070)",
    members="lingbot-world base-cam, -fast; lingbot-world-v2 1.3B/14B (F0100, F0137)", handle="gh Robbyant; hf robbyant",
    notes="Current release v2 is non-commercial, so status open-weights under the current-release rule", src=["W0009", "W0031"])
add(W, slug="oasis", name="Oasis (open 500M)", type="model", org="etched", status="open",
    art=dict(github="etched-ai/open-oasis", huggingface_model="Etched/oasis-500m"),
    lic="code and weights MIT (F0071, F0126)", alive="not archived, not fork (F0071)",
    push="2024-11-08 (F0071)", rel="no GitHub releases recorded (F0429)", adopt="HF 169/30d, gated=auto (F0126); 2,026 stars (F0071)",
    members="Oasis 500M (W0012)", handle="gh etched-ai; hf Etched",
    notes="Both artifacts are Etched's; Decart's hosted Oasis 3 (W0041) is parked as a separate closed product (question 11)", src=["W0012", "W0041"])
add(W, slug="diamond", name="DIAMOND", type="model", org="eloialonso", status="open-weights",
    art=dict(github="eloialonso/diamond", huggingface_model="eloialonso/diamond"),
    lic="MIT (F0072); HF card no license (F0127)", alive="not archived, not fork (F0072)", push="2024-12-06 (F0072)", rel="no GitHub releases recorded (F0430)",
    adopt="HF 0/30d (F0127); 2,089 stars (F0072)", members="-", handle="gh eloialonso; hf eloialonso", notes="Dormant 21 months", src=["W0016"])
add(W, slug="yume", name="Yume", type="model", org="stdstu12", status="open",
    art=dict(github="stdstu12/YUME", huggingface_model="stdstu123/Yume-I2V-540P"),
    lic="Apache-2.0 (F0073, F0313)", alive="not archived, not fork (F0073)", push="2026-01-14 (F0073)", rel="no GitHub releases recorded (F0431)",
    adopt="HF 0/30d (F0313); 576 stars (F0073)", members="Yume 1.0, Yume-1.5 (W0011)", handle="gh stdstu12; hf stdstu123", notes="HF handle differs from GitHub handle (F0313)", src=["W0011", "W0043"])
add(W, slug="aether", name="Aether", type="model", org="shanghai-ai-laboratory", status="open",
    art=dict(github="InternRobotics/Aether", huggingface_model="AetherWorldModel/AetherV1"),
    lic="MIT (F0074, F0141)", alive="not archived, not fork (F0074)", push="2025-10-26 (F0074)", rel="no GitHub releases recorded (F0432)",
    adopt="HF 0/30d (F0141); 611 stars (F0074)", members="AetherV1 (F0141)", handle="gh InternRobotics; hf AetherWorldModel",
    notes="Action-conditioned video prediction + planning (W0011). InternRobotics = Shanghai AI Lab (F0211)", src=["W0011"])
add(W, slug="genie-envisioner", name="Genie Envisioner", type="model", org="agibot", status="open-weights",
    art=dict(github="AgibotTech/Genie-Envisioner-V1", huggingface_model="agibot-world/Genie-Envisioner-v1.0"),
    lic="CC BY-NC-SA 4.0 for data and most code; modified Diffusers/LTX/Cosmos parts keep their licenses (F0252); GE-base weights inherit the LTX-Video license (F0244)",
    alive="not archived, not fork (F0095)", push="2026-09-10 (F0095)", rel="no GitHub releases recorded (F0433)", adopt="HF 20/30d (F0110); 585 stars (F0095)",
    members="GE v1.0, GE-Sim v2.0 (F0110)", handle="gh AgibotTech; hf agibot-world", notes="Repo renamed Genie-Envisioner -> Genie-Envisioner-V1 (F0089)", src=["W0014", "F0001"])
add(W, slug="unifolm-wma", name="UnifoLM-WMA", type="model", org="unitree", status="open-weights",
    art=dict(github="unitreerobotics/unifolm-world-model-action", huggingface_model="unitreerobotics/UnifoLM-WMA-0-Base"),
    lic="code CC BY-NC-SA 4.0 (F0210); HF card metadata says apache-2.0 (F0111): conflict, record both", alive="not archived, not fork (F0077)",
    push="2026-03-18 (F0077)", rel="no GitHub releases recorded (F0434)", adopt="HF 0/30d, gated=auto (F0111); 1,144 stars (F0077)",
    members="WMA-0-Base, WMA-0-Dual (F0111)", handle="gh unitreerobotics; hf unitreerobotics", notes="Unitree's world-model-action framework (W0029)", src=["W0014", "W0029"])
add(W, slug="gigaworld", name="GigaWorld", type="model", org="gigaai", status="open",
    art=dict(github="open-gigaai/giga-world-0", huggingface_model="open-gigaai/GigaWorld-0-Video-Pretrain-2b"),
    lic="Apache-2.0 (F0078, F0102)", alive="not archived, not fork (F0078)", push="2025-12-03 (F0078)", rel="no GitHub releases recorded (F0435)",
    adopt="HF 0/30d video pretrain; Giga-World-Policy-0.5 3,732 (F0102); 1,292 stars (F0078)", members="GigaWorld-0 Video/3D, Giga-World-Policy (F0102)",
    handle="gh open-gigaai; hf open-gigaai", notes="Same vendor as GigaBrain (5a)", src=["W0014", "W0029"])
add(W, slug="ctrl-world", name="Ctrl-World", type="model", org="robert-gyj", status="open",
    art=dict(github="Robert-gyj/Ctrl-World", huggingface_model="yjguo/Ctrl-World"),
    lic="MIT (F0079, F0128)", alive="not archived, not fork (F0079)", push="2025-10-24 (F0079)", rel="no GitHub releases recorded (F0436)",
    adopt="HF 145/30d (F0128); 50 stars (F0079)", members="-", handle="gh Robert-gyj; hf yjguo",
    notes="ICLR 2026 (W0029). Star count (50) is low for the attention it drew; recorded, not judged", src=["W0014", "W0029"])
add(W, slug="boundless-world-model", name="Boundless World Model (BWM)", type="model", org="blm-lab", status="open-weights",
    art=dict(github="boundless-large-model/boundless-world-model", huggingface_model="BLM-Lab/Boundless-World-Model"),
    lic="code Apache-2.0 (F0080, F0236); HF card no license field, base Wan2.2-TI2V-5B (F0154, F0242)", alive="not archived, not fork (F0080)",
    push="2026-06-15 (F0080)", rel="no GitHub releases recorded (F0437)", adopt="HF 37/30d (F0154); 1,829 stars (F0080)", members="-",
    handle="gh boundless-large-model; hf BLM-Lab", notes="First among open models on WorldArena Track 1 (W0042)", src=["W0003", "W0029", "W0042"])
add(W, slug="dreamer", name="Dreamer", type="model", org="danijar", status="open",
    art=dict(github="danijar/dreamerv3"),
    lic="MIT (F0081)", alive="not archived, not fork (F0081)", push="2026-05-25 (F0081)", rel="no GitHub releases recorded (F0438)",
    adopt="3,822 stars (F0081)", members="DreamerV3 (F0081); the Dreamer 4 reimplementation next-state/open-dreamer is parked (W0026, F0230)", handle="gh danijar",
    notes="Model-based RL agent with a learned latent world model; code, no hosted weights", src=["W0026"])
add(W, slug="td-mpc", name="TD-MPC", type="model", org="nicklashansen", status="open",
    art=dict(github="nicklashansen/tdmpc2"),
    lic="MIT (F0084)", alive="not archived, not fork (F0084)", push="2026-07-13 (F0084)", rel="no GitHub releases recorded (F0439)",
    adopt="889 stars (F0084)", members="TD-MPC2 (F0084)", handle="gh nicklashansen", notes="Added by this sweep as a model-based-RL comparator to Dreamer", src=["F0084"])
add(W, slug="rynnworld", name="RynnWorld", type="model", org="alibaba-damo-academy", status="open",
    art=dict(github="alibaba-damo-academy/RynnWorld-4D", huggingface_model="Alibaba-DAMO-Academy/RynnWorld-Teleop"),
    lic="HF cards apache-2.0 (F0136, F0314); RynnWorld-4D GitHub label `other`, text not read (F0308)", alive="not archived, not fork (F0308)",
    push="2026-07-06 (F0308)", rel="no GitHub releases recorded (F0440)", adopt="HF 53/30d Teleop (F0136); 5 stars 4D (F0308)",
    members="RynnWorld-4D, RynnWorld-Teleop 'An Action-Conditioned World Model for Digital Teleoperation' (W0043)", handle="gh alibaba-damo-academy; hf Alibaba-DAMO-Academy",
    notes="2026 release not in the brief. Pairs the RynnWorld-4D repo with the RynnWorld-Teleop weights, and the action-conditioning evidence (W0043) is for Teleop, whose repo ecosyste.ms does not index (F0307). Maintainer may prefer Teleop-only", src=["F0122", "W0043"])
add(W, slug="dreamx-world", name="DreamX-World", type="model", org="amap", status="open",
    art=dict(github="AMAP-ML/DreamX-World", huggingface_model="GD-ML/DreamX-World-5B"),
    lic="code Apache-2.0 (F0083); weights mit (F0315)", alive="not archived, not fork (F0083)", push="2026-07-23 (F0083)", rel="no GitHub releases recorded (F0441)",
    adopt="HF 1,095/30d 5B, 610 5B-Cam (F0315); 775 stars (F0083)", members="DreamX-World-5B, -5B-Cam (F0315)", handle="gh AMAP-ML; hf GD-ML",
    notes="Camera control + text events; action input is camera pose only (marginal on the litmus)", src=["W0026", "W0043"])
add(W, slug="genie", name="Genie", type="model", org="google", status="closed",
    art=dict(homepage="https://deepmind.google/models/genie/"),
    lic="proprietary; no weights (W0037)", alive="live (W0037)", push="n/a", rel="Project Genie to AI Ultra subscribers 2026-01-29 (W0008)",
    adopt="none measurable (subscription product)", members="Genie 3 via Project Genie (W0008)", handle="-", notes="Closed frontier comparator (interactive, action-controllable)", src=["W0008", "W0037"])
add(W, slug="runway-gwm", name="Runway GWM", type="model", org="runway", status="closed",
    art=dict(homepage="https://runway.com/research/introducing-runway-gwm-1"),
    lic="proprietary; no weights discussed (W0039)", alive="live (W0039)", push="n/a", rel="GWM-1 (W0013)",
    adopt="none measurable (API + Python SDK, W0039)", members="GWM Worlds, GWM Avatars, GWM Robotics (W0039)", handle="-",
    notes="Action-conditioning on camera, events, robot pose, speech (W0039). Only the Robotics/Worlds variants fit", src=["W0013", "W0039"])

# ---------------------------------------------------------------- parked
PR = [  # (name, reason, source ids)
    ("SO-100 arm", "SKU of SO-101 line: prior hardware generation in the same repo (F0317); keep only if generations stay separate", "F0317, F0051"),
    ("Gazebo (gz-sim)", "boundary: general robotics simulator with no learning surface; maintainer call (question 2)", "F0016, W0004"),
    ("Webots", "boundary: general robotics simulator (question 2)", "F0019, W0005"),
    ("Drake", "boundary: model-based planning/control toolbox, not a learning stack (question 2)", "F0018, F0170, F0268"),
    ("CARLA", "boundary: autonomous-driving simulator (question 3)", "F0022, F0272"),
    ("ROS 2", "boundary: robotics middleware, not AI", "F0059"),
    ("dora-rs", "boundary: robotics dataflow middleware, not AI", "F0312, W0044"),
    ("Gymnasium", "boundary -> ml_frameworks: generic RL environment API, most envs are not physical", "F0023, F0271"),
    ("Isaac Lab-Arena", "boundary -> evaluation_code: policy evaluation harness", "F0311, W0044"),
    ("LIBERO", "boundary -> benchmark_eval_data: benchmark suite", "F0060, F0297"),
    ("Diffusion Policy", "unmaintained: last push 2024-12-24; the method ships inside LeRobot (lerobot/diffusion_pusht)", "F0024, F0098"),
    ("Unitree SDK2", "boundary: vendor device SDK for closed hardware", "F0058, F0275"),
    ("Gemini Robotics On-Device", "SKU of gemini-robotics", "W0015, W0036"),
    ("RynnBrain", "boundary -> multimodal_models: embodied-reasoning VLM, no action head", "F0122, W0043"),
    ("Hy-Embodied VLM", "boundary -> multimodal_models: embodied VLM", "F0300, W0035"),
    ("UnifoLM-ER", "boundary -> multimodal_models: embodied-reasoning model", "F0111"),
    ("RLDX (RLWRLD)", "no addressable artifact: announced as future open source", "W0001"),
    ("A1 (truncated VLA)", "no addressable artifact verified: paper only in this run", "W0001"),
    ("Dream-VLA", "no addressable artifact verified: paper only", "W0001"),
    ("Pelican-VLA", "no addressable artifact verified: paper only", "W0001"),
    ("GraspVLA", "coverage limit: listed in the sinanlabs index (CC BY-NC 4.0 per index), not independently fetched", "F0001"),
    ("DexVLA", "coverage limit: index entry only", "F0001"),
    ("GR-1 (ByteDance)", "coverage limit: index entry only; last activity 2023 per index", "F0001"),
    ("VLA-0 (NVIDIA Research)", "coverage limit: index entry only", "F0001"),
    ("MiniVLA", "coverage limit: index entry only; derivative of OpenVLA", "F0001"),
    ("HPT", "coverage limit: index entry only", "F0001"),
    ("LAPA", "coverage limit: index entry only", "F0001"),
    ("LLaVA-VLA", "coverage limit: index entry only", "F0001"),
    ("RoboVLMs", "coverage limit: index entry only", "F0001"),
    ("Magma (Microsoft)", "boundary -> multimodal_models: agentic VLM (index entry)", "F0001"),
    ("VLA-Adapter", "coverage limit: index entry only; adapter method", "F0001"),
    ("LeRobot datasets (hub collection)", "identity unclear: a hub organization, not one dataset", "W0002, F0098"),
    ("BridgeData V2", "coverage limit: only a third-party RLDS mirror seen (shihao1895/bridge-rlds)", "F0297"),
    ("10Kh-RealOmin-OpenData (genrobot2025)", "coverage limit: in the HF robotics-dataset top 40, not researched", "F0297"),
    ("Hy-Embodied-0.5-VLA-Data", "SKU of hy-embodied-vla", "F0297, W0035"),
    ("AlohaMini", "coverage limit: surfaced once, not fetched", "W0033"),
    ("Hope Jr / Trossen ViperX / Hello Stretch / Unitree G1", "closed long-tail or not fetched: named in one buyers-guide summary only", "W0019"),
    ("DreamZero-DROID (GEAR-Dreams)", "coverage limit: in the HF robotics-model top 60, not researched", "F0298"),
    ("RoboBrain2.0 (BAAI)", "boundary -> multimodal_models: embodied brain VLM; in HF top 60, not researched", "F0298"),
    ("PhysBrain1.5", "coverage limit: seen only as third-party GGUF quantizations in HF top 60", "F0298"),
    ("GraspMolmo (Ai2)", "coverage limit: grasp-prediction model in HF top 60, not researched", "F0298"),
    ("SimVLA", "coverage limit: LIBERO checkpoint in HF top 60, not researched", "F0298"),
    ("ACE-Data-0", "coverage limit: HF robotics-dataset top 40, not researched", "F0297"),
    ("ABC-130k", "coverage limit: HF robotics-dataset top 40, not researched", "F0297"),
    ("stereo-550", "coverage limit: HF robotics-dataset top 40, not researched", "F0297"),
    ("Gen-HumanEgo", "coverage limit: HF robotics-dataset top 40 (egocentric human data), not researched", "F0297"),
    ("HiFi-UMI-2K", "coverage limit: HF robotics-dataset top 40, not researched", "F0297"),
    ("xperience-10m", "coverage limit: HF robotics-dataset top 40, not researched", "F0297"),
    ("OmniAction (OpenMOSS)", "coverage limit: HF robotics-dataset top 40, not researched", "F0297"),
    ("L2D (yaak-ai)", "coverage limit: driving dataset in HF top 40; depends on question 3", "F0297"),
    ("Retargeted AMASS (fleaven, 3 repos)", "coverage limit: motion-retargeting data in HF top 40, not researched", "F0297"),
    ("MolmoAct-Midtraining-Mixture", "SKU of molmoact (training mixture)", "F0297"),
    ("DOM / deform360 / tracker-pov / MetaFold / grand_tour_dataset / trex_dataset", "coverage limit: HF robotics-dataset top 40, not researched", "F0297"),
    ("computer-use-large (markov-ai)", "boundary: computer-use agent data, not physical", "F0297"),
]
PW = [
    ("World Labs Marble", "boundary -> media_generation: generates editable static 3D worlds, no action->next-state (W0040)", "W0040, W0013"),
    ("Mirage (Dynamics Lab)", "closed long-tail: demo/preview, no open code or API found", "W0016, W0041"),
    ("open-dreamer", "no addressable open artifact: 'All rights reserved' placeholder license, 1 star", "F0230, F0082, W0026"),
    ("WebWorld (Qwen)", "boundary: web-environment world model, not physical (question 7)", "W0003"),
    ("CWM (Meta)", "boundary -> base_pretrained: code LLM trained with world-model data", "W0003"),
    ("HY-WorldPlay", "SKU of hy-world", "F0140, F0306"),
    ("HunyuanWorld-Voyager", "SKU of hy-world", "F0139, W0017"),
    ("Hunyuan-GameCraft-2", "SKU of hunyuan-gamecraft (paper)", "W0009"),
    ("Cosmos-Reason", "SKU of cosmos; VLM part contested with multimodal_models", "F0097"),
    ("Matrix-3D", "SKU/boundary: Skywork 3D scene generator -> media_generation", "F0106"),
    ("Giga-World-Policy", "SKU of gigaworld", "F0102"),
    ("EnerVerse-AC (AgiBot)", "coverage limit: HF listing only (0 downloads)", "F0110"),
    ("LingBot-VA", "identity unclear: video-action policy from Robbyant, not fetched", "W0031"),
    ("Oasis 3 (Decart)", "closed long-tail: hosted interactive world model, no fetched source ties it to the open Etched 500M release; maintainer call (question 11)", "W0041"),
    ("Odyssey-2 Max", "closed long-tail: named once, not fetched", "W0013"),
    ("SolarWM", "no addressable artifact verified: paper only", "W0009"),
    ("WorldScape / FlowWAM-FiveAges", "identity unclear: leaderboard names only", "W0042"),
    ("OmniWorld (InternRobotics)", "coverage limit: dataset for world modeling in HF robotics top 40, not researched", "F0297"),
    ("DreamX-Phi", "no addressable artifact verified: surfaced once in a search result (W0043); arXiv fetch did not complete (HTTP 406, F0598)", "W0043"),
]
# Cross-category duplicates: counted as duplicate signals in Part B, not as unique candidates.
DW = [
    ("VLA-JEPA", "duplicate: accepted in robotics_embodied (outputs actions)", "W0011"),
    ("GR00T / GR00T Dreams", "duplicate: ruled into robotics_embodied", "W0002"),
    ("RynnVLA-002", "duplicate: member of rynnvla in robotics_embodied", "F0088"),
    ("WorldVLA", "retired alias -> rynnvla (repo redirects to RynnVLA-002) in robotics_embodied", "F0088, F0133"),
]
