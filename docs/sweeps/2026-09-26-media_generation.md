# Media generation seed: 2026-09-26

## Scope and boundary

This batch seeds the preliminary `media_generation` category proposed in issue #603: models whose
headline capability is synthesizing an image, video, 3D asset, or music or sound-effect audio from a
prompt or condition, plus the software built specifically to run, compose or serve those models. The
membership test: is the product's primary output a synthesized image, video, 3D asset or non-speech
audio asset, or is the product purpose-built to produce one?

It is one category, not four. Image, video, 3D and audio each have supply enough to stand alone, but a
split would scatter the shared tooling. Modality is recorded by the registry file's section headings
and belongs on the head record at promotion. Models and the apps and engines that run them are
separate products on separate ladders (`extends: {model: model, software: software}`, the
`document_conversion` shape). Weights are `adopt: 0.4, cap: 0.6`, in Model components → Models.

The boundary rulings (exclusions by neighbor, and every contested call) are written into the
category's `comments` so the next editor applies them rather than re-deriving them. In short:

- **Out, to a neighbor.** Speech to `speech_audio`. Understanding VLMs and unified
  understanding-and-generation models (Janus, BAGEL, Emu, SenseNova-U) to `multimodal_models`.
  Action-conditioned environment models (Cosmos, HunyuanWorld) to `world_models`. General runtimes
  (vllm-omni, SGLang diffusion) stay in `inference_code`; `diffusers` stays in `ml_frameworks`; the SD
  safety checker stays in `safeguards`. Agentic video pipelines over third-party models to
  `orchestration_agents`. Diffusion trainers (kohya sd-scripts, musubi-tuner, SimpleTuner,
  diffusion-pipe) are proposed to `finetuning_code` as a follow-up and are not in this PR.
- **In.** Media apps and UIs (not `ui_api`); diffusion-specific engines (not `inference_code` or
  `compilers`), with `nunchaku` moved in from the compilers registry; portrait animation and lip-sync;
  vendor modality lines as their own products beside the vendor's LLM.
- **Not products.** LoRAs, merges and fine-tuned checkpoints (Chroma included), ControlNet-style
  adapters, and ComfyUI custom-node packs.
- **Proposed rule, flagged for the maintainer:** on a line whose newest release is closed, the newest
  *distributed* release governs openness (see open question 1).

No row was scored. Each row carries identity and artifacts only, as the registry schema requires.

## Inputs swept

All fetched on 2026-09-26. The full fetch trail (every `F` id with its URL, UTC timestamp, HTTP code
and body hash; every `W` id with its query and a verbatim excerpt) is on the evidence branch
`claude/research-media_generation`, under `research/media_generation/` (`fetch-log.tsv`, `raw/`,
`web-log.tsv`, `sweep.md` with the per-row evidence table, and `audit.md`, a two-pass independent
audit that re-fetched 16 claims and passed).

| Code | Input |
|---|---|
| brief | The leads named in the issue #603 research brief |
| aa | Artificial Analysis arenas: text-to-image, text-to-video, image-to-video and music, open-weights and overall boards, read as rendered |
| topic | GitHub topic pages, first page (top 20 by stars): text-to-video, text-to-image, music-generation, text-to-3d, stable-diffusion, image-to-3d, video-generation |
| hforg | Hugging Face org listings, `limit=100` sorted by downloads, one call per org, read for generation pipeline tags at 1,000 or more downloads |
| ws | WebSearch for 2025-2026 releases, leaderboards and alternatives |
| recall-lead | A lead named by the researcher and then verified live, never accepted on recall |

Repository facts came from repos.ecosyste.ms and ungh.cc, licences from the LICENSE body on
raw.githubusercontent.com, Hub facts from the Hugging Face API (`downloads` is the rolling 30 days),
and package facts from packages.ecosyste.ms and pypi.org. `api.github.com` was not reachable from the
sweep environment and no 403 was read as an absence.

**Retrieval cutoff.** The ranked sources were read to the cutoffs above; anything below them was not
seen. Nothing already found was rejected for ranking below a cutoff.

## Reconciled counts

A raw signal is one sighting of a candidate in one input family. Duplicates are 93 repeat sightings of
a candidate already counted plus 13 matches against the index or the resolution ledger.

```text
raw_signals       = 248
duplicate_signals = 106
unique_candidates = 142
accepted          = 92
parked            = 50

248 = 106 + 142
142 = 92 + 50
```

The registry file carries **93** rows: the 92 accepted, plus `nunchaku`, which the sweep counted as a
duplicate signal (an existing tail row in `compilers`) and the decision record moves here. Of the 93,
71 are typed `model` (59 open or open-weights generation models: image 20, video 16, 3D 11, audio 12;
plus 12 closed comparators) and 22 `software` (apps, UIs, engines and libraries).

No slug or artifact collides with a head product, a retired alias, another registry row or a
resolution-ledger ruling (`research/crosscheck.py`, 0 findings before writing; `build.validate`,
0 errors after).

## Changes from the sweep, applied from the decision record

The 2026-09-26 decision record lets every recommendation in the sweep's section 9 stand. Applied:

- `nunchaku` moved from `sources/registry/compilers.yaml` to this registry (display name corrected to
  "Nunchaku"; artifact unchanged: `nunchux-ai/nunchaku`. The PyPI package named `nunchaku` is an
  unrelated project, F0301, so it is not declared).
- `infinity-image` and `latentsync` use `bytedance-seed-volcano-engine`, the parent-company slug
  already on the map, instead of the new `bytedance` slug the sweep proposed (section 9 Q14).
- `triposr` stays attributed to `vast-ai` (Q13).
- The unified models (Janus, BAGEL) and the world-model SKUs (Cosmos, HunyuanWorld) stay parked here
  as boundary moves to `multimodal_models` and `world_models`.

## Organizations and handles

Forty-five organizations are new to `sources/organizations/`, each a minimal record (`products: []`)
so the handles below have an owner; the type is `unknown` where the sweep did not establish it. Every
account a row's artifacts live under is declared in `sources/org_handles.yaml`, except the accounts
below, held because ownership is not settled from the record:

- Hugging Face `stabilityai` for `triposr`: Stability AI's account, hosting weights VAST wrote.
  `build.propose_org_handles` reports it as a conflict, correctly.
- Hugging Face `BestWishYsh` for `helios`: a personal account, not PKU-YuanGroup's.
- Hugging Face `OmniGen2` for `omnigen`: a model-named account whose owner the sweep did not confirm.
- Hugging Face `FunAudioLLM` and GitHub `QwenAudio` for `thinksound`: Alibaba team accounts other
  categories may claim; left for the promotion PR.

Added to existing organizations: Alibaba's Tongyi-MAI and Wan accounts, ByteDance's `bytedance` and
FoundationVision accounts plus `bytedance.com`, Tencent's Tencent-Hunyuan and TencentARC accounts,
NVIDIA's NVlabs, `deepmind.google` for Google, and zai-org on GitHub for Zhipu.

## Accepted candidates

Open status is the sweep's reading, not a score. Every primary source was fetched on 2026-09-26.

### Image models

| Candidate | Slug | Type | Org | Open status | Primary source |
|---|---|---|---|---|---|
| FLUX | `flux` | model | `black-forest-labs` | open-weights | https://github.com/black-forest-labs/flux2 |
| Stable Diffusion | `stable-diffusion` | model | `stability-ai` | open-weights | https://github.com/Stability-AI/generative-models |
| Qwen-Image | `qwen-image` | model | `alibaba-cloud` | open-weights | https://github.com/QwenLM/Qwen-Image |
| HiDream | `hidream` | model | `hidream-ai` | open | https://github.com/HiDream-ai/HiDream-O1-Image |
| SANA | `sana` | model | `nvidia` | open | https://github.com/NVlabs/Sana |
| PixArt | `pixart` | model | `pixart-alpha` | open-weights | https://github.com/PixArt-alpha/PixArt-sigma |
| Kolors | `kolors` | model | `kuaishou` | open | https://github.com/Kwai-Kolors/Kolors |
| Lumina | `lumina` | model | `alpha-vllm` | open | https://github.com/Alpha-VLLM/Lumina-Image-2.0 |
| HunyuanImage | `hunyuan-image` | model | `tencent` | open-weights | https://github.com/Tencent-Hunyuan/HunyuanImage-3.0 |
| Z-Image | `z-image` | model | `alibaba-cloud` | open | https://github.com/Tongyi-MAI/Z-Image |
| FIBO | `fibo` | model | `bria-ai` | open-weights | https://github.com/Bria-AI/FIBO |
| GLM-Image | `glm-image` | model | `zhipu-z-ai` | open | https://github.com/zai-org/GLM-Image |
| Ideogram | `ideogram` | model | `ideogram` | open-weights | https://github.com/ideogram-oss/ideogram4 |
| ERNIE-Image | `ernie-image` | model | `baidu` | open | https://huggingface.co/baidu/ERNIE-Image |
| LongCat-Image | `longcat-image` | model | `meituan` | open | https://github.com/meituan-longcat/LongCat-Image |
| OmniGen | `omnigen` | model | `vectorspacelab` | open | https://github.com/VectorSpaceLab/OmniGen2 |
| Infinity | `infinity-image` | model | `bytedance-seed-volcano-engine` | open | https://github.com/FoundationVision/Infinity |
| Ming-Image | `ming-image` | model | `inclusion-ai` | open | https://huggingface.co/inclusionAI/Ming-Image-0.1-Design |
| NextStep | `nextstep` | model | `stepfun` | open | https://huggingface.co/stepfun-ai/NextStep-1.1 |
| Step1X-Edit | `step1x-edit` | model | `stepfun` | open | https://github.com/stepfun-ai/Step1X-Edit |

### Video models, including portrait animation and lip-sync

| Candidate | Slug | Type | Org | Open status | Primary source |
|---|---|---|---|---|---|
| Wan | `wan` | model | `alibaba-cloud` | open | https://github.com/Wan-Video/Wan2.2 |
| HunyuanVideo | `hunyuan-video` | model | `tencent` | open-weights | https://github.com/Tencent-Hunyuan/HunyuanVideo |
| CogVideo | `cogvideo` | model | `zhipu-z-ai` | open-weights | https://github.com/zai-org/CogVideo |
| LTX | `ltx` | model | `lightricks` | open-weights | https://github.com/Lightricks/LTX-2 |
| Mochi | `mochi` | model | `genmo` | open | https://github.com/genmoai/mochi |
| Open-Sora | `open-sora` | model | `hpc-ai-tech` | open | https://github.com/hpcaitech/Open-Sora |
| MAGI | `magi` | model | `sand-ai` | open | https://github.com/SandAI-org/MAGI-1 |
| SkyReels | `skyreels` | model | `skywork` | open-weights | https://github.com/SkyworkAI/SkyReels-V2 |
| Kandinsky | `kandinsky` | model | `kandinsky-lab` | open | https://github.com/kandinskylab/kandinsky-5 |
| Step-Video | `step-video` | model | `stepfun` | open | https://github.com/stepfun-ai/Step-Video-T2V |
| MiniMax Hailuo (H3) | `minimax-hailuo` | model | `minimax` | open-weights | https://github.com/MiniMax-AI/MiniMax-H3 |
| LongCat-Video | `longcat-video` | model | `meituan` | open | https://huggingface.co/meituan-longcat/LongCat-Video |
| Helios | `helios` | model | `pku-yuan-group` | open | https://github.com/PKU-YuanGroup/Helios |
| Stable Video Diffusion | `stable-video-diffusion` | model | `stability-ai` | open-weights | https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt |
| LivePortrait | `liveportrait` | model | `kuaishou` | open | https://github.com/KlingAIResearch/LivePortrait |
| LatentSync | `latentsync` | model | `bytedance-seed-volcano-engine` | open-weights | https://github.com/bytedance/LatentSync |

### 3D asset models

| Candidate | Slug | Type | Org | Open status | Primary source |
|---|---|---|---|---|---|
| TRELLIS | `trellis` | model | `microsoft` | open | https://github.com/microsoft/TRELLIS |
| Hunyuan3D | `hunyuan-3d` | model | `tencent` | open-weights | https://github.com/Tencent-Hunyuan/Hunyuan3D-2 |
| Step1X-3D | `step1x-3d` | model | `stepfun` | open | https://github.com/stepfun-ai/Step1X-3D |
| TripoSG | `triposg` | model | `vast-ai` | open | https://github.com/VAST-AI-Research/TripoSG |
| TripoSR | `triposr` | model | `vast-ai` | open | https://github.com/VAST-AI-Research/TripoSR |
| Stable Fast 3D | `stable-fast-3d` | model | `stability-ai` | open-weights | https://github.com/Stability-AI/stable-fast-3d |
| Stable Point Aware 3D | `spar3d` | model | `stability-ai` | open-weights | https://github.com/Stability-AI/stable-point-aware-3d |
| InstantMesh | `instantmesh` | model | `tencent` | open | https://github.com/TencentARC/InstantMesh |
| Cube | `cube` | model | `roblox` | open-weights | https://github.com/Roblox/cube |
| SAM 3D | `sam-3d` | model | `meta` | open-weights | https://github.com/facebookresearch/sam-3d-objects |
| PartCrafter | `partcrafter` | model | `wgsxm` | open | https://github.com/wgsxm/PartCrafter |

### Music and sound-effect models

| Candidate | Slug | Type | Org | Open status | Primary source |
|---|---|---|---|---|---|
| Stable Audio | `stable-audio` | model | `stability-ai` | open-weights | https://huggingface.co/stabilityai/stable-audio-3-medium |
| MusicGen | `musicgen` | model | `meta` | open-weights | https://huggingface.co/facebook/musicgen-medium |
| ACE-Step | `ace-step` | model | `ace-step` | open | https://github.com/ace-step/ACE-Step-1.5 |
| YuE | `yue` | model | `m-a-p` | open-weights | https://github.com/multimodal-art-projection/YuE |
| HeartMuLa | `heartmula` | model | `heartmula` | open | https://github.com/HeartMuLa/heartlib |
| SongGeneration | `songgeneration` | model | `tencent-ai-lab` | open-weights | https://github.com/tencent-ailab/SongGeneration |
| DiffRhythm | `diffrhythm` | model | `aslp-lab` | open | https://github.com/ASLP-lab/DiffRhythm |
| MiniMax Music | `minimax-music` | model | `minimax` | open-weights | https://huggingface.co/MiniMaxAI/MiniMax-Music3 |
| MMAudio | `mmaudio` | model | `hkchengrex` | open-weights | https://github.com/hkchengrex/MMAudio |
| ThinkSound | `thinksound` | model | `alibaba-cloud` | open | https://github.com/QwenAudio/ThinkSound |
| HunyuanVideo-Foley | `hunyuanvideo-foley` | model | `tencent` | open-weights | https://github.com/Tencent-Hunyuan/HunyuanVideo-Foley |
| FoleyCrafter | `foleycrafter` | model | `open-mmlab` | open | https://github.com/open-mmlab/FoleyCrafter |

### Apps and UIs

| Candidate | Slug | Type | Org | Open status | Primary source |
|---|---|---|---|---|---|
| ComfyUI | `comfyui` | software | `comfy-org` | open | https://github.com/Comfy-Org/ComfyUI |
| Stable Diffusion web UI (AUTOMATIC1111) | `stable-diffusion-webui` | software | `automatic1111` | open | https://github.com/AUTOMATIC1111/stable-diffusion-webui |
| Stable Diffusion WebUI Forge | `forge` | software | `lllyasviel` | open | https://github.com/lllyasviel/stable-diffusion-webui-forge |
| InvokeAI | `invokeai` | software | `invoke-ai` | open | https://github.com/invoke-ai/InvokeAI |
| Fooocus | `fooocus` | software | `lllyasviel` | open | https://github.com/lllyasviel/Fooocus |
| SD.Next | `sdnext` | software | `vladmandic` | open | https://github.com/vladmandic/sdnext |
| SwarmUI | `swarmui` | software | `mcmonkeyprojects` | open | https://github.com/mcmonkeyprojects/SwarmUI |
| Krita AI Diffusion | `krita-ai-diffusion` | software | `acly` | open | https://github.com/Acly/krita-ai-diffusion |
| Stability Matrix | `stability-matrix` | software | `lykos-ai` | open | https://github.com/LykosAI/StabilityMatrix |
| Easy Diffusion | `easy-diffusion` | software | `easydiffusion` | source-available | https://github.com/easydiffusion/easydiffusion |
| DiffusionBee | `diffusionbee` | software | `divamgupta` | open | https://github.com/divamgupta/diffusionbee-stable-diffusion-ui |
| Dream Textures | `dream-textures` | software | `carson-katri` | open | https://github.com/carson-katri/dream-textures |
| WanGP | `wan2gp` | software | `deepbeepmeep` | source-available | https://github.com/deepbeepmeep/Wan2GP |

### Diffusion engines and libraries

| Candidate | Slug | Type | Org | Open status | Primary source |
|---|---|---|---|---|---|
| FramePack | `framepack` | software | `lllyasviel` | open | https://github.com/lllyasviel/FramePack |
| stable-diffusion.cpp | `stable-diffusion-cpp` | software | `leejet` | open | https://github.com/leejet/stable-diffusion.cpp |
| Nunchaku | `nunchaku` | software | `nunchux-ai` | open | https://github.com/nunchux-ai/nunchaku |
| xDiT | `xdit` | software | `xdit-project` | open | https://github.com/xdit-project/xDiT |
| LightX2V | `lightx2v` | software | `modeltc` | open | https://github.com/ModelTC/LightX2V |
| FastVideo | `fastvideo` | software | `hao-ai-lab` | open | https://github.com/hao-ai-lab/FastVideo |
| DiffSynth-Studio | `diffsynth-studio` | software | `modelscope-alibaba` | open | https://github.com/modelscope/DiffSynth-Studio |
| stable-audio-tools | `stable-audio-tools` | software | `stability-ai` | open | https://github.com/Stability-AI/stable-audio-tools |
| AudioCraft | `audiocraft` | software | `meta` | open | https://github.com/facebookresearch/audiocraft |

### Closed comparators (ADR-005): hosted frontier services, homepage only

| Candidate | Slug | Type | Org | Open status | Primary source |
|---|---|---|---|---|---|
| GPT Image | `gpt-image` | model | `openai` | closed | https://developers.openai.com/api/docs/models |
| Nano Banana (Gemini Image) | `nano-banana` | model | `google` | closed | https://deepmind.google/models/gemini-image/ |
| Midjourney | `midjourney` | model | `midjourney` | closed | https://www.midjourney.com |
| Seedream | `seedream` | model | `bytedance-seed-volcano-engine` | closed | https://seed.bytedance.com/en/seedream |
| Veo | `veo` | model | `google` | closed | https://deepmind.google/models/veo/ |
| Kling | `kling` | model | `kuaishou` | closed | https://kling.ai/ |
| Seedance | `seedance` | model | `bytedance-seed-volcano-engine` | closed | https://seed.bytedance.com/en/seedance |
| Runway Gen | `runway-gen` | model | `runway` | closed | https://runway.com |
| Suno | `suno` | model | `suno` | closed | https://suno.com |
| Lyria | `lyria` | model | `google` | closed | https://deepmind.google/models/lyria/ |
| Meshy | `meshy` | model | `meshy` | closed | https://www.meshy.ai/ |
| Tripo | `tripo` | model | `vast-ai` | closed | https://www.tripo3d.ai/ |

## Parked

Evidence ids refer to the fetch and web logs on the evidence branch. All parked entries were fetched
or seen on 2026-09-26.

| name | reason | evidence | discovery source |
|---|---|---|---|
| Janus / Janus-Pro (DeepSeek) | boundary → multimodal_models: unified understanding+generation model, brief 2 lists Janus under omni | F0020, F0091, W0009 (AA T2I Elo 532) | brief2, aa, hforg |
| BAGEL (ByteDance Seed) | boundary → multimodal_models: unified any-to-any model | F0018, F0143, W0009 (Elo 704) | aa |
| Cosmos3 Text2Image / Image2Video (NVIDIA) | boundary → world_models sibling (flag, not resolved): Cosmos is a world-model line; its T2I/I2V SKUs rank on AA | W0009 (Elo 995), W0006, F0109 (openmdw1.1 licence) | aa, hforg |
| HunyuanWorld / HY-World (Tencent) | boundary → world_models sibling (flag) | F0085, W0040 | hforg, topic |
| Chroma (lodestones) | derivative checkpoint of FLUX.1-schnell (Civitai-class question, Q5); slug `chroma` also collides with the storage head product | F0354 (66,047 HF 30d downloads, Apache-2.0), W0046 | ws |
| Civitai LoRAs, fine-tuned checkpoints and merges | not products (class ruling per brief) | brief | brief |
| ComfyUI custom nodes (ltdrdata/ComfyUI-Manager, Lightricks/ComfyUI-LTXVideo, ideogram-oss/ComfyUI-Ideogram4) | plug-ins of a product, not products (two other node packs are already ruled excluded_boundary in the resolution ledger, counted as duplicates) | W0038, W0045; F0226 (Manager repo not found under ltdrdata on ecosyste.ms) | topic |
| ControlNet (lllyasviel) | adapter class (conditioning add-on for a base model), same question as LoRAs (Q5); dormant since 2024-02 | F0075 (34,115 stars, Apache-2.0) | recall-lead |
| Mage-Flow (Microsoft) | identity unclear: search reports a 4B July-2026 release, but HF id microsoft/Mage-Flow returned 401 (not found) | W0002, F0139 | ws |
| Waver 1.0 (ByteDance FoundationVision) | no addressable weights: README offers a tech report and a Discord demo, no licence file | F0214, F0272, F0245 | ws |
| Sora / Sora 2 (OpenAI) | discontinued: app shut 2026-04-26, API shut 2026-09-24 | W0025, W0029 (W0027 help-center fetch 403) | brief, aa, ws |
| Wan 2.5 / 2.6 / 2.7 / 3.0 (Alibaba) | SKU of wan: closed flagship releases of the same line | W0016, W0012, F0191, F0192 | aa, ws |
| Qwen-Image 2.0 Pro / 3.0 (Alibaba) | SKU of qwen-image (closed releases) | W0011 | aa |
| Hunyuan3D 2.5 / 3.0 / 3.1 (Tencent) | SKU of hunyuan-3d (API-only releases) | W0064 | ws |
| FLUX.2 [pro] / [flex] (BFL) | SKU of flux (API-only) | W0021, W0011 | aa |
| SkyReels V4 (Skywork) | SKU of skyreels (closed) | W0012 | aa |
| HappyHorse (Alibaba-ATH) | closed long-tail (ADR-005): second closed Alibaba video line beside Wan 3.0 | W0012 (Elo 1286) | aa |
| MAI-Image (Microsoft AI) | closed long-tail (ADR-005); frontier already represented by GPT Image and Nano Banana | W0011 (Elo 1148) | aa |
| Grok Imagine (SpaceXAI) | closed long-tail (ADR-005) | W0011, W0012 | aa |
| Muse Image (Meta) | closed long-tail (ADR-005) | W0011 (Elo 1111) | aa |
| Mureka | closed long-tail (ADR-005); music frontier represented by Suno and Lyria | W0032, W0033 | aa |
| Eleven Music (ElevenLabs) | closed long-tail (ADR-005); ElevenLabs is a speech_audio closed comparator (flag) | W0032, W0023 | aa, ws |
| Udio | closed long-tail (ADR-005) | W0023 | ws |
| Rodin / Hyper3D | closed long-tail (ADR-005); 3D frontier represented by Meshy and Tripo | W0026 | ws |
| Imagen (Google) | identity unclear: brief lead; Google image page now leads with Nano Banana, Imagen not separately fetched | W0053 | brief |
| Playground v2.5 | not verified beyond a leaderboard line (Feb 2024 release) | W0009 | aa |
| SDXL-Lightning / Hyper-SD (ByteDance) | SKU/distillation of stable-diffusion (adapter class) | F0113, W0009 | aa, hforg |
| SeedVR / SeedVR2 (ByteDance Seed) | boundary question: video restoration / upscaling, not prompt-conditioned generation (Q7) | F0090 | hforg |
| Amphion (open-mmlab) | boundary → speech_audio: audio toolkit centred on TTS/SVC | F0208, W0039 | topic |
| kohya-ss/sd-scripts | boundary → finetuning_code (sibling of onetrainer and ai-toolkit there); propose there | F0063 | brief |
| musubi-tuner (kohya-ss) | boundary → finetuning_code | F0064, W0034; no licence file at root (F0235, F0248, F0257, F0268) | ws |
| SimpleTuner | boundary → finetuning_code | F0200, F0299 (PyPI 4,762/month) | ws |
| diffusion-pipe | boundary → finetuning_code | F0201 | ws |
| OpenMontage | boundary → orchestration_agents (agentic video production over third-party models); also 61,063 stars on a repo created 2026-03-29, a spike worth a look | F0193, W0037 | topic |
| Open-Generative-AI (Anil-matcha) | boundary → ui_api/orchestration (aggregator app over hosted models) | F0194, W0037 | topic |
| Pixelle-Video | boundary → orchestration_agents (automated short-video pipeline) | F0195, W0043 | topic |
| hypit | boundary → orchestration_agents (agentic video cloning); not fetched beyond topic page | W0037, W0043 | topic |
| Toonflow | boundary → orchestration_agents/ui (creative canvas app); not fetched beyond topic page | W0037, W0043 | topic |
| ViMax | boundary → orchestration_agents; not fetched beyond topic page | W0043 | topic |
| Duix-Avatar | boundary question (avatar/digital-human app, Q7); not fetched beyond topic page | W0043 | topic |
| OpenCreator (krillinai) | boundary → ui/orchestration; not fetched beyond topic page | W0043 | topic |
| img2threejs | identity unclear: 16,029 stars on a repo created 2026-07-15 (spike worth a look); purpose not verified | F0224, W0042 | topic |
| IOPaint | unmaintained: archived (last push 2025-04-29) | F0203, W0041 | topic |
| StableStudio (Stability AI) | unmaintained: no push since 2024-04-30 | F0225, W0041 | topic |
| SD WebUI reForge (Panchovix) | fork of forge (GitHub fork flag) | F0205 | recall-lead |
| SD WebUI Forge Classic (Haoming02) | fork of forge (GitHub fork flag) | F0220 | recall-lead |
| lucidrains DALLE2-pytorch / imagen-pytorch / DALLE-pytorch | reimplementations of papers, not products | W0038 | topic |
| stable-dreamfusion / DreamGaussian / zero123 | research code, not verified beyond topic page | W0040, W0042 | topic |
| MochiDiffusion | not verified beyond topic page (Mac app) | W0041 | topic |
| LongCat-Video-Avatar / Wan-Dancer / Wan-Animate | SKUs of longcat-video / wan | F0092, F0192 | hforg |

### Duplicate signals: already on the map or already ruled

| signal | matched | evidence |
|---|---|---|
| diffusers | diffusers (ml_frameworks, head) | F0211, W0041 |
| OneTrainer | onetrainer (finetuning_code, head) | F0209 |
| AI Toolkit (ostris) | ai-toolkit (finetuning_code, head) | F0210 |
| Unsloth (diffusion UI) | unsloth (finetuning_code, head) | W0041 |
| LocalAI | localai (inference_code, head) | W0041 |
| OpenVINO | openvino (ml_frameworks, head) | W0041 |
| vllm-omni | artifact of vllm (inference_code, head) | F0198, W0043 |
| SGLang (sglang-omni / SGLang Diffusion) | sglang (inference_code, head) | W0039, F0307 |
| Nunchaku (nunchux-ai/nunchaku) | nunchaku tail row (compilers) — contested: recommend move here | F0269 (Apache-2.0, 3,948 stars, pushed 2026-09-06), F0318 (v1.2.1 2026-01-25); PyPI `nunchaku` is an unrelated project (F0301) |
| stable-diffusion-safety-checker | tail row in safeguards | index |
| Hunyuan LLM (Tencent) | hunyuan tail row (base_pretrained) — the LLM, distinct from the media lines | index |
| kijai/ComfyUI-WanVideoWrapper | resolution ledger excluded_boundary (#413) | ledger |
| cubiq/ComfyUI_IPAdapter_plus | resolution ledger excluded_boundary (#413) | ledger |

## Identity notes for promotion

- **Representative artifacts.** Most model rows carry one GitHub repository and one Hub checkpoint for
  a family of many: `flux` declares the FLUX.2 repository and the most-downloaded checkpoint
  (FLUX.1-dev); `wan` declares the Wan2.2 repository and a Wan2.1 checkpoint; `hunyuan-video` the
  original repository and the 1.5 checkpoint. Promotion adds the rest of each family to the head
  record; the representative artifact is not the product's whole identity.
- **Models and engines are separate.** `stable-audio` declares only its Hub checkpoint; the
  `stable-audio-tools` library, and its PyPI package, is its own software row. `musicgen` and
  `audiocraft` follow the same line.
- **`wan2gp` is a GitHub fork** (of Wan2.1) and is accepted as a distinct low-VRAM video app under its
  own licence (WanGP Community License 2.0, F0185).
- **`diffsynth-studio` declares no PyPI package**: its README documents only a source install (F0404).
- **No usage instrument** on the 12 closed rows, on 16 of the 22 software rows (GitHub only), and on
  11 models with no Hub repository or a Hub count of 0 (sana, ming-image, step1x-edit, magi,
  kandinsky, step1x-3d, cube, songgeneration, mmaudio, thinksound, foleycrafter). Adoption will abstain
  or rest on stars for these.
- **`minimax-hailuo` reported 3,657,004 Hub downloads in 30 days**, the largest figure in the set, for
  a model created about six weeks before the fetch (F0136, re-fetched F0391). Read it again before
  banding adoption on it.
- **Dormant rows** (no push or Hub update in the 12 months to 2026-09-26): pixart, kolors,
  step-video, stable-video-diffusion, latentsync, step1x-3d, triposg, stable-fast-3d, spar3d,
  instantmesh, partcrafter, musicgen, forge and diffusionbee. Recorded, not rejected.
- **Data disagreements to settle at promotion.** `ideogram`'s last push reads 2026-06-04 on
  ecosyste.ms (F0399) and 2026-06-30 on ungh (F0230). `kandinsky` reads MIT on the repository and the
  Hub while a search summary says Apache-2.0 (W0066).
- **`songgeneration`'s licence text was never read**: GitHub reports "other" and the LICENSE file
  returned 404 (F0051, F0400).

## Licence strings for the maintainer's licence-rulings issue

Per the decision record these go to one shared issue, not to `sources/rubrics/`, and a product
carrying one is deferred at promotion until it is ruled on: FLUX Non-Commercial License; Stability AI
Community License (and its stable-audio and stable-video-diffusion variants); Tencent Hunyuan
Community License (excludes the EU, UK and South Korea); MiniMax H3 Community License (excludes the
EU, UK, South Korea and the USA); MiniMax-Music3 Community License; LTX-2.x Community License; Qwen
Research License; Ideogram 4 Non-Commercial agreement; CogVideoX License; Skywork community licence;
CUBE3D Research-Only RAIL-MS; SAM License (2025-11-19); Easy Diffusion custom licence; WanGP Community
License 2.0; and SongGeneration's unread licence. CreativeML OpenRAIL++-M (SDXL, PixArt, LatentSync)
and CC BY-NC 4.0 (FIBO, MusicGen, YuE2, MMAudio weights) are also met and should be checked against
the shared tiers before promotion.

## Open questions left for the maintainer

1. **The closed flagship on an open line.** Wan 2.5 to 3.0 and Hunyuan3D 2.5 to 3.1 are API-only,
   Qwen-Image 3.0 is closed and Qwen-Image-2.1 is non-commercial. *Ruled in the #720 review
   (2026-09-27):* the proposal that the newest distributed release governs openness was rejected.
   The current release governs, as identity.md says. The affected products keep evidence for both
   releases and are deferred at promotion. How availability is modelled separately from openness
   stays open for the maintainer.
2. **Runway** was outside the fetched arena top 25 (W0012). Keep it as a closed comparator, or drop
   it at promotion under ADR-005? Midjourney is kept regardless.
3. **Capability ladder.** The within-modality arena reading in `scoring_recipe.note` is a sketch. 3D
   has only thin third-party arenas that disagree (W0063); decide whether 3D models abstain above the
   first rung until one settles.
4. **Engines contested with `inference_code`.** The sweep flags FastVideo as the closest call; the ruling
   here puts every diffusion-specific engine in this category.
5. **Follow-ups outside this PR:** the four diffusion trainers to `finetuning_code`; Matrix-3D and
   Marble to a follow-up sweep; SeedVR2 (restoration) confirmed out; OpenMontage (61,063 stars on a
   repository created 2026-03-29) and img2threejs (16,029 stars, created 2026-07-15) are growth spikes
   worth a look before anyone proposes them.
