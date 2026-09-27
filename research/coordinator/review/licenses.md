# License strings needing a maintainer ruling: promotions #729–#737

## How this was checked

- **What "mapped" means.** A string counts as mapped if it appears literally in the `examples` of a `license_tier` in `sources/rubrics/{software,model,pretrained,dataset}.yaml` on `origin/main` (473ba19f). `hardware.yaml` has no license tier.
- **Aliases checked too.** I also checked the `aliases` tables in `sources/signal_routing.yaml`. They add nothing relevant here.
- **How the list was built.** I ran every license name in every added or changed score file on the nine branches against those examples. That run produced the same set of strings the PR bodies list; nothing extra turned up.
- **Sources.** Every source URL below comes from the product's score file on the PR branch.

**Count:**
- Section A: 22 license entries (30 exact strings) on promoted products that no tier names on the ladder the product climbs. 20 of them drive a deferral. The other two are `AGPL-3.0 OR ValidMind-Commercial-License` (validmind-library, scored rather than deferred) and the FlashVDM code license (triposg, where the PR says no ruling is needed).
- Section C: about 27 more strings on registry rows the PRs left unpromoted.
- Section B lists strings the PRs named that are already mapped, and so are not new.

---

## A. Strings on promoted products that no tier names

### Software ladder

**1. `none-declared`**
- Product: ezkl (#730), deferred at hand 2/source_available.
- Sources:
  - https://ungh.cc/repos/zkonduit/ezkl/files/main (no LICENSE in 545 paths)
  - https://raw.githubusercontent.com/zkonduit/ezkl/main/Cargo.toml
  - https://raw.githubusercontent.com/zkonduit/ezkl/main/pyproject.toml
  - https://raw.githubusercontent.com/zkonduit/ezkl/main/cla.md
- What the PR says: should a public repo with no grant map to `proprietary`, or get a tier of its own?
- Note: `build/check_rubric.py` on main already refers to `confer`'s `none-declared` as "a curation prompt, not a rubric gap". So this string has come up before without a ruling.
- Related no-license cases are in section C: pytorch/hub, bioimage.io, MolmoAct2.

**2. `Lagrange-License`**
- Product: deepprove (#730), deferred at hand 2/source_available.
- Sources:
  - https://raw.githubusercontent.com/Lagrange-Labs/deep-prove/master/LICENSE. This is a revocable grant for internal testing and evaluation.
  - It is contradicted by https://raw.githubusercontent.com/Lagrange-Labs/deep-prove/master/Cargo.toml (`MIT OR Apache-2.0`) and by the GitHub label (apache-2.0, via repos.ecosyste.ms).
- What the PR says: is this `competition_restricted`? It also asks the maintainer to confirm that the LICENSE body governs.

**3. `CC-BY-NC-4.0` on the software ladder**
- Products and PRs:
  - content-seal (#730), hand 2/source_available. Covers the Stable Signature and radioactive-watermark members and the COCO-trained Watermark Anything weights.
  - maniskill (#731), hand 2/source_available. Covers the bundled assets.
- Sources:
  - https://raw.githubusercontent.com/facebookresearch/stable_signature/main/LICENSE
  - https://raw.githubusercontent.com/facebookresearch/radioactive-watermark/main/LICENSE
  - https://raw.githubusercontent.com/facebookresearch/watermark-anything/main/README.md
  - https://raw.githubusercontent.com/mani-skill/ManiSkill/main/README.md
- Status: mapped on model and pretrained (`commercial_forbidden`) and on dataset (`noncommercial`, lowercase `cc-by-nc-4.0`). **Not** mapped on software.
- What the PRs say:
  - #730: add a non-commercial tier to the software ladder, or split the NC members out of the suite.
  - #731: an NC-licensed asset inside an OSI simulator reads closest to `competition_restricted`.

**4. `AGPL-3.0 OR ValidMind-Commercial-License`**
- Product: validmind-library (#730). **Not deferred**: it is scored 2 because `source: partial` settles the score before the tier is read.
- Source: https://raw.githubusercontent.com/validmind/validmind-library/main/LICENSE
- Status: `AGPL-3.0` alone is `osi`. The compound string is not mapped.
- What the PR says: under the elasticsearch precedent it would record the OSI option alone. The sweep's decisions doc routes custom strings to the rulings issue, and the assurance sweep's license notes listed this product for deferral.

**5. `CC-BY` (no version)**
- Product: carla (#731), assets. Deferred at hand 3/source_available, which is where CC-BY-4.0 would land.
- Source: https://raw.githubusercontent.com/carla-simulator/carla/HEAD/README.md ("CARLA specific assets are distributed under the CC-BY License").
- Status: software maps only `CC-BY-4.0`. Dataset has lowercase `cc-by` under `open_data`, but that is not the ladder carla climbs.
- What the PR says: the Unreal Engine dependency under Epic's own terms is a second question for the same ruling.

**6. `zlib`**
- Product: pybullet (#731), deferred at hand 5/open_source.
- Sources:
  - https://raw.githubusercontent.com/bulletphysics/bullet3/HEAD/LICENSE.txt
  - https://pypi.org/pypi/pybullet/json (classifier "OSI Approved :: zlib/libpng License")
- What the PR says: zlib is OSI-approved but not listed in the software `osi` examples. Adding it is a shared-rubric change.

### Model / pretrained ladders

**7. `NVIDIA-OneWay-Noncommercial`**
- Product: gr00t (#731). It covers GR00T-H (N1.6) and the GR00T-N1.5-3B_Assemble_Trocar fine-tune. Deferred at hand 2/restricted.
- Source: https://developer.download.nvidia.com/licenses/NVIDIA-OneWay-Noncommercial-License-22Mar2022.pdf (section 3.3). Card: https://huggingface.co/nvidia/GR00T-H/raw/main/README.md
- What the PR says: it reads as `commercial_forbidden`. A second question is whether the superseded GR00T-H should leave the family, which would make gr00t 3/open_weights.

**8. Prior Labs TabPFN weights licenses** (five strings)
- The strings:
  - `TABPFN-3-License-v1.0` (the only one recorded in the score file)
  - TABPFN-3.5 License v1.0
  - TABPFN-2.6 License v1.0
  - TABPFN-2.5 License v1.1
  - Prior Labs License 1.1 (Apache-2.0 plus an attribution/model-naming clause, TabPFN-2)
- Product: tabpfn (#732), deferred at hand 2/restricted.
- Sources cited:
  - https://huggingface.co/Prior-Labs/tabpfn_3/raw/main/LICENSE
  - https://huggingface.co/Prior-Labs/tabpfn_3_5/raw/main/LICENSE
  - https://cdn.jsdelivr.net/gh/PriorLabs/TabPFN@main/README.md
  - **No source is cited for the 2.5, 2.6 or Prior Labs 1.1 license bodies.**
- What the PR says: the non-commercial grants read as `commercial_forbidden`.

**9. `PML-1.0`** (Roboflow Platform Model License 1.0)
- Product: rf-detr (#732). It covers the XL/2XL weights. Deferred at hand 2/restricted.
- Sources:
  - https://roboflow.com/platform-model-license-1-0
  - https://roboflow.com/licensing
- What the PR says: is it `commercial_forbidden`, `use_bounded` or `proprietary`?

**10. `Moondream-Model-License-1.0`**
- Product: moondream (#734), deferred at hand 3/open_weights.
- Sources:
  - https://moondream.ai/licenses/model/1.0
  - Hub metadata for moondream3.1-9B-A2B
- What the PR says: `permissive_non_osi` (a conduct-style limit adapted from ELv2) or `use_bounded`? Either gives 3.

**11. `NVIDIA-Open-Model-Agreement`** (release date 2026-04-02)
- Product: nemotron-omni (#734), deferred at hand 3/open_weights.
- Source: https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/
- Status: not mapped. The different document `NVIDIA-Open-Model-License` is mapped.
- What the PR says: it has a different title, date and defined terms from the Open Model License. If it joins `permissive_non_osi`, the score is 3.

**12. FLUX non-commercial licenses** (three strings)
- The strings:
  - `FLUX-Non-Commercial-License-2.1`
  - FLUX [dev] Non-Commercial License v2.0
  - FLUX.1 [dev] Non-Commercial License v1.1.1
- Product: flux (#737), deferred at hand 2/restricted.
- Sources:
  - https://cdn.jsdelivr.net/gh/black-forest-labs/flux2@main/model_licenses/LICENSE-FLUX-NON-COMMERICAL
  - …/flux2@main/model_licenses/LICENSE-FLUX-DEV
  - https://cdn.jsdelivr.net/gh/black-forest-labs/flux@main/model_licenses/LICENSE-FLUX1-dev
- What the PR says: reads as `commercial_forbidden`.

**13. `Stability-AI-Community-License`**
- Products: stable-diffusion (#737: SD3, SD3.5, SDXL-Turbo, SD-Turbo) and stable-audio (#737). Both deferred at hand 3/open_weights.
- Sources:
  - https://stability.ai/community-license-agreement
  - https://huggingface.co/stabilityai/sd-turbo/raw/main/LICENSE.md
  - https://huggingface.co/stabilityai/stable-audio-3-medium-base/raw/main/LICENSE.md
- What the PR says: reads as `use_bounded` (free below USD 1M revenue). One ruling settles both products. One SD3 Medium repo's metadata still says a non-commercial research license.

**14. `CreativeML-OpenRAIL++-M`**
- Product: stable-diffusion (#737), covering SDXL 1.0.
- Source: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/raw/main/LICENSE.md
- What the PR says: reads as `permissive_non_osi` under #117.

**15. LTX community / open-weights licenses** (three strings)
- The strings:
  - `LTX-2.x-Community-License`
  - LTX-2 Community License
  - `LTXV-Open-Weights-License-0.X`
- Product: ltx (#737), deferred at hand 3/open_weights.
- Sources:
  - https://raw.githubusercontent.com/Lightricks/LTX-2/main/LICENSE-2_x
  - https://raw.githubusercontent.com/Lightricks/LTX-2/main/LICENSE-2
  - https://huggingface.co/Lightricks/LTX-Video/raw/main/LTX-Video-Open-Weights-License-0.X.txt
- What the PR says: reads as `use_bounded` (USD 10M threshold).

**16. `Open-RAIL-M`**
- Product: ltx (#737), covering LTX-Video 0.9.1/0.9.5.
- Source: https://huggingface.co/Lightricks/LTX-Video/raw/main/ltx-video-2b-v0.9.5.license.txt
- Status: not mapped. Only `AI-Pubs-Open-RAIL-M-Modified` appears, on software.
- What the PR says: reads as `permissive_non_osi`.

**17. `Tencent-Hunyuan-Community-License`**
- Product: hunyuan-video (#737), deferred at hand 3/open_weights.
- Source: https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo-1.5/main/LICENSE
- What the PR says: a 100M-MAU bound plus exclusion of the EU, UK and South Korea. The territorial question is new to the map and could move the score to 2.

**18. Tencent Hunyuan 3D (2.1) Community License**
- Product: hunyuan-3d (#737), on the prior release in `components.context`. The product itself is deferred with null openness as closed frontier on an open line.
- Source: https://huggingface.co/tencent/Hunyuan3D-2.1/raw/main/LICENSE
- What the PR says: the same territorial exclusion. The body also notes it bars output use.

**19. Qwen Research License**
- Product: qwen-image (#737), on the prior release Qwen-Image-2.1. Held with null openness.
- Source: https://huggingface.co/Qwen/Qwen-Image-2.1/raw/main/LICENSE
- Status: not mapped. `Qwen-License-Agreement`, a different license, is `use_bounded`.
- What the PR says: reads as `commercial_forbidden`.

**20. `MiniMax-H3-Community-License`**
- Product: minimax-hailuo (#737), deferred at hand 3/open_weights.
- Source: https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/LICENSE
- Status: not mapped. `minimax-community`, a different string, is `permissive_non_osi`.
- What the PR says: a USD 20M revenue bound plus exclusion of the EU, UK, Republic of Korea and USA, which makes it materially narrower.

**21. `InsightFace-Non-Commercial-Research`**
- Product: liveportrait (#737), deferred at hand 3/open_weights.
- Source: https://ungh.cc/repos/KlingAIResearch/LivePortrait/files/main/LICENSE (MIT, followed by the InsightFace non-commercial clause).
- What the PR says: does a bundled, replaceable third-party model govern the tier? If it does, the score is 2/restricted.
- Cross-ref: the classic_ml_cv sweep notes InsightFace itself has "an MIT-code, non-commercial-models split" in its README (registry row).

**22. Tencent Hunyuan FlashVDM Community License**
- Product: triposg (#737), on the `triposg/` code subdirectory. **Not deferred.**
- Source: https://ungh.cc/repos/VAST-AI-Research/TripoSG/files/main/triposg/LICENSE
- What the PR says: "not needing a ruling", because the MIT weights govern.

### Hardware (no license tier, context only, #729)
None of these block a score.
- `quic/cloud-ai-sdk`: "BSD-3-Clause-Clear-style text with an explicit patent disclaimer". Same family as #735's "Clear BSD" (metisfl).
- AWS neuronx-cc: "Proprietary" on PyPI.
- NVIDIA: the CUDA EULA over the toolkit.

---

## B. Strings the PRs named that are already mapped (not new)

| String | Tier on main | Where it came up |
|---|---|---|
| `BSL-1.1` | software `competition_restricted` | verifywise (#730); listed only because the sweep flagged it |
| `NVIDIA-Open-Model-License` | model and pretrained `permissive_non_osi` | gr00t (#731), nemotron-vl (#734), canary/parakeet (#733) |
| `Llama-2-Community-License` | model `use_bounded` | openvla (#731) |
| `Gemma-License` | model and pretrained `use_bounded` | paligemma (#734). The lerobot pi0 ports' `gemma` slug is aliased to it. |
| `DeepSeek-Model-License` | model and pretrained `permissive_non_osi` | janus (#734) |
| `CC-BY-4.0` | model and pretrained `permissive_non_osi`; software `permissive_non_osi` | speech models (#733) |
| `CC-BY-NC-4.0` | model and pretrained `commercial_forbidden` | f5-tts, canary-1b, moshika (#733); musicgen (#737). Not on software (see A3). |
| `CC-BY-NC-SA-4.0` | model and pretrained `commercial_forbidden` | granite-speech 5.0 turboctc-nc (#733, left in registry) |
| `GPL-3.0`, `AGPL-3.0` | software `osi` | piper (#733); nebula-dfl Community Edition (#735, a gating question, not a tier question) |
| `Mistral-Research-License` | model and pretrained `commercial_forbidden` | pixtral Large (#734, registry) |
| `OpenMDW-1.1` | **pretrained only** `permissive_non_osi`, not in `model.yaml` | alpamayo (#731, registry). #731 correctly calls this a gap on the model ladder. |
| `Qwen-License-Agreement` | model and pretrained `use_bounded` | InternVL3-78B (declared on internvl, #734). The record scores on InternVL3.5 Apache-2.0 instead. The multimodal sweep had listed "the Qwen license on InternVL3-78B" for a ruling. |
| `none` / unstated | dataset `unstated` | droid (#731, scored 2 on the dataset ladder, so no ruling needed) |

---

## C. Strings on registry rows the PRs left unpromoted

These are listed in the PR bodies or the sweeps, deduplicated. Each one would defer its product when that row is promoted.

- **#731 robotics:**
  - `OpenMDW-1.1` on the model ladder (alpamayo; see B)
  - MolmoAct2 cards carry no license field
  - The sweep also lists: Isaac Sim additional software and materials license, Galaxea G0/G0.5 community licenses, Tencent HY-World and Hunyuan community licenses, and the LTX-Video license on Genie Envisioner (overlaps A15/A17)
- **#732 classic_ml_cv:**
  - FSL-1.1-MIT (pycaret). FSL-1.1-ALv2 is mapped, but this sibling is not.
  - BSL-1.0 Boost (dlib). The sweep warns it must not match BSL-1.1.
  - LGPL-2.1 (gensim). Only LGPL-3.0 is in `osi`.
  - DINOv3 License
  - SAM License
  - Sapiens2 License
  - TabFM Non-Commercial License
  - Stable AI LimiX code and weights licenses
  - EXAONE AI Model License 1.2-NC
  - apple-amlr
  - NVIDIA Source Code License
- **#733 speech_audio:**
  - Coqui Public Model License 1.0.0 (xtts)
  - Fish Audio Research License (fish-speech)
  - Boson Higgs Audio 2 Community License and Boson Higgs TTS 3 Research and Non-Commercial License (higgs-audio)
  - Moonshine AI Community License (moonshine)
  - bilibili Model Use License (indextts)
  - `breezeblue-research-and-non-commercial-license` (breeze-tts)
- **#734 multimodal:**
  - NVIDIA `nsclv1` (eagle)
  - FAIR non-commercial research license (perception-lm)
  - Apple ML Research Model license (fastvlm). Possibly the same text as #732's `apple-amlr`; that isn't established.
  - LFM Open License v1.0 (lfm-vl)
  - VITA1.5 terms (vita)
  - UI-Venus weight license (unconfirmed)
- **#735 federated_learning:**
  - Clear BSD (metisfl). Expressly grants no patent rights.
  - Vector Institute License (fl4health). PyPI says Apache-2.0.
- **#736 model_hubs:** no license file on `pytorch/hub`, `bioimage-io/bioimage.io` or `bioimage-io/collection`. This is the same question as A1 `none-declared`. OpenML was resolved as BSD-3-Clause for code and CC-BY for data, and is not a ruling.
- **#737 media_generation (from the sweep, not yet met on promoted rows):**
  - MiniMax-Music3 Community License
  - Ideogram 4 Non-Commercial
  - CogVideoX License
  - Skywork community license
  - CUBE3D Research-Only RAIL-MS
  - SAM License (2025-11-19; overlaps #732)
  - Easy Diffusion custom license
  - WanGP Community License 2.0
  - SongGeneration (license unread)

## Groupings a single ruling could cover

- **Territorial exclusion:** A17, A18, A20, plus HY-World in the robotics sweep. This is a new question for the map.
- **Revenue-bound community licenses:** A13 (USD 1M), A15 (USD 10M), A20 (USD 20M), plus LFM Open License. All read as `use_bounded`.
- **Vendor non-commercial model licenses:** A7, A8, A12, A19, plus several in section C. All read as `commercial_forbidden`.
- **Non-commercial parts inside an otherwise OSI or MIT product:** A3 (software ladder), A21. Both are compound or bundled cases.
- **No grant at all:** A1, the pytorch/hub and bioimage rows, and MolmoAct2.
- **Names missing from the `osi` examples:** A6 zlib, LGPL-2.1, and the A5 unversioned CC-BY.
