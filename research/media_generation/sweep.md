# Image / video / 3D / music generation sweep — 2026-09-26

Proposed slug `media_generation` (issue #603). Live sweep run on 2026-09-26. Every fact below
cites an `F` id (`fetch-log.tsv`, body in `raw/`) or a `W` id (`web-log.tsv`). Where a fetch
failed, the cell says so; a 403/429 is never read as an absence.

## 1. Verdict

**GO-WITH-CHANGES.** Supply is the deepest of any proposal in this batch. There are 59 open or
open-weights generation models across four modalities (image 20, video 16, 3D 11, audio/music/SFX 12),
plus 21 media-generation apps, engines and libraries and 12 closed frontier comparators. The 92 rows
come from 59 parent companies, and none holds more than 6.5% of them. Every modality clears 10 on models alone. The changes needed before it is
published: (a) adopt a per-type ladder map `{model: model, software: software}`, as
`document_conversion` does, because models and the apps that run them (ComfyUI, InvokeAI) are
separate products; (b) accept that **no single capability quantity orders image, video, 3D and audio
together**. Arena Elo orders each modality internally, so the ladder should read a within-modality
arena standing (section 4). (c) Rule on the sub-scope questions in section 9: portrait
animation/lip-sync, diffusion engines, and vendor modality lines. One trend for the gap statement:
three vendors that anchored open video, 3D and image generation now ship their flagship closed while
older generations stay open. Wan 2.5–3.0 are API-only (W0016, F0192), Hunyuan3D 2.5–3.1 are API-only
(W0064), and Qwen-Image-2.1 went to a non-commercial research licence (F0170) while 3.0 is closed (W0011).

## 2. Fit metrics (computed from section 6)

- accepted candidates: **92** (open: 52, open-weights: 26, source-available: 2, closed: 12)
  - models (open + open-weights): 59, split image 20 / video 16 / 3D 11 / audio 12
  - software (apps, UIs, engines, libraries): 21 (19 open, 2 source-available)
  - closed comparators: 12 (image 4, video 4, audio 2, 3D 2)
- independent organizations: 62 org slugs, 59 parent companies. Largest org share: 6/92 = 6.5%
  (`stability-ai`). By parent company Stability AI and Tencent tie at 6/92 = 6.5% (Tencent is
  `tencent` 5 plus `tencent-ai-lab` 1).
- candidates active in the last 12 months (push, or HF lastModified for HF-only rows, on or after
  2025-09-26), counted over the 80 non-closed rows: **66**. The 14 dormant rows are pixart, kolors,
  step-video, stable-video-diffusion, latentsync, step1x-3d, triposg, stable-fast-3d, spar3d,
  instantmesh, partcrafter, musicgen, forge and diffusionbee. Dormant rows are recorded here and not
  rejected.
- candidates with a usage instrument (a declared HF model with a download count, or a declared
  PyPI package), as opposed to stars only: **53**. The 39 without one are the 12 closed rows (hosted,
  no download channel), 16 of the 21 software rows (GitHub-only, since none of ComfyUI, A1111, Forge,
  SD.Next, SwarmUI and the rest ships a first-party package), and 11 models whose HF repo reports 0
  downloads or that have no HF repo: sana, ming-image, step1x-edit, magi, kandinsky, step1x-3d, cube,
  songgeneration, mmaudio, thinksound and foleycrafter. The software rows with a declared package are
  invokeai, xdit, fastvideo, audiocraft and stable-audio-tools. DiffSynth-Studio's PyPI package is not
  declared, because its README documents only a source install (F0404).
- retrieval cutoff: HF org listings were fetched at `limit=100` sorted by downloads, one call per org
  (F0077–F0113), and read only for generation pipeline tags at ≥1,000 downloads. GitHub topic pages were
  read at the first page (top 20 by stars) for text-to-video, text-to-image, music-generation,
  text-to-3d, stable-diffusion, image-to-3d and video-generation (W0037–W0043). The Artificial Analysis
  boards were read as rendered (W0009–W0013, W0032–W0033). Anything below those cutoffs was not seen.
  Nothing already found was rejected for falling below a cutoff.

## 3. Boundary

**Definition.** Models whose headline capability is synthesizing an image, video, 3D asset, or
music/sound-effect audio from a prompt or condition, plus the software built specifically to run,
compose or serve those models.

**Litmus.** Is the product's primary output a synthesized image, video, 3D asset or non-speech
audio asset, or is the product purpose-built to produce one?

**Explicit exclusions.**
- Speech TTS/ASR/voice conversion → `speech_audio` (Amphion parked there, F0208).
- Understanding VLMs, and unified understanding+generation models whose fame is understanding
  (Janus, BAGEL) → `multimodal_models` (brief 2).
- Action-conditioned environment models (Cosmos, HunyuanWorld) → `world_models` (brief 5b).
- General LLM runtimes and serving → `inference_code`. vllm-omni is already an artifact of `vllm`
  (index), and SGLang diffusion sits under `sglang`.
- LoRA/checkpoint trainers → `finetuning_code`. OneTrainer and ai-toolkit are already there. Propose
  kohya sd-scripts, musubi-tuner, SimpleTuner and diffusion-pipe there too.
- Core library `diffusers` → stays in `ml_frameworks`.
- Chat UIs and API gateways → `ui_api`. Its roster (index) holds no image/video UI, so the media
  apps are not taken from it.
- Agentic video-production apps built over third-party models (OpenMontage, Pixelle-Video, ViMax)
  → `orchestration_agents` (parked, section 7).
- Civitai LoRAs, fine-tuned checkpoints and merges (including Chroma) and ControlNet-style adapters
  are not products (class park).
- Video restoration/upscaling (SeedVR2) is parked pending Q7.

**Contested products.**

| product | where it is now | recommendation | reason |
|---|---|---|---|
| nunchaku (nunchux-ai/nunchaku) | tail, `compilers` | move here | 4-bit inference engine built for diffusion models (FLUX, Qwen-Image) (F0269). It sits beside the other diffusion engines proposed here. |
| diffusers | head, `ml_frameworks` | stay | general library the whole stack imports (F0211); `ml_frameworks` owns such libraries |
| onetrainer, ai-toolkit | head, `finetuning_code` | stay | trainers; add kohya sd-scripts, musubi-tuner, SimpleTuner and diffusion-pipe to `finetuning_code`'s registry, not here |
| unsloth, localai, openvino | head (finetuning_code / inference_code / ml_frameworks) | stay | general tools that also touch diffusion (W0041) |
| vllm-omni | artifact of `vllm` head | stay | already declared on `vllm` |
| hunyuan (LLM) | tail, `base_pretrained` | stay | the media lines hunyuan-image, hunyuan-video, hunyuan-3d and hunyuanvideo-foley are new rows here |
| qwen / glm / ernie / minimax (LLM heads) | head, `base_pretrained` | stay; add modality lines here | qwen-image, glm-image, ernie-image, minimax-hailuo and minimax-music are separately named lines, the same shape as qwen3-embedding beside qwen (Q8) |
| Janus, BAGEL | absent | → `multimodal_models` (flag to brief 2) | unified any-to-any; brief 2 names Janus as omni |
| OmniGen, Ming-Image | absent | here (flag to brief 2) | generation/editing-first. Ming-Image is a generation SKU, distinct from Ming-Omni |
| Cosmos3 T2I/I2V, HunyuanWorld | absent | → `world_models` (flag to 5b) | action-conditioned world models, even though Cosmos SKUs rank on the AA image and video boards (W0006, W0009) |
| SAM 3D Objects | absent | here (flag to classic_ml_cv) | image-to-3D generation (F0216). The SAM segmentation family belongs to brief 3 |
| Eleven Music | absent | parked here as closed long tail (flag to speech_audio) | ElevenLabs is a speech_audio closed comparator; the music surface is separate |
| stable-diffusion-safety-checker | tail, `safeguards` | stay | a safety classifier, not a generator |
| stable-diffusion.cpp, xDiT, LightX2V, FastVideo, DiffSynth-Studio | absent | here (Q4) | engines purpose-built for diffusion/video generation; the alternative is `inference_code` |

## 4. Capability quantity

**No single quantity orders the whole set.** That is a finding and has three parts:

1. **Across modalities, Elo is not commensurable.** Artificial Analysis runs separate arenas for
   text-to-image (W0009, W0011), text-to-video and image-to-video (W0010, W0012, W0013) and music
   (W0032, W0033). A 1,000 in one is not a 1,000 in another. 3D has only third-party arenas with
   thin, conflicting coverage: Pixazo puts Hunyuan3D-2.5 first at 1325, while Sloyd puts Tripo v3.1
   first (W0063).
2. **Within a modality, arena Elo orders the models well.** The AA open-weights T2I board ranks 53
   open models (W0009), and 16 of our 20 image rows appear on it.
3. **Software needs a different quantity**: breadth of model families and modalities supported.

**Proposed ladder input for models: within-modality arena standing, as a percentile against that
modality's closed frontier.** Rungs, low → high:

1. Released weights, no public arena presence (e.g. partcrafter, step1x-3d).
2. On its modality's public arena, below the open-weights median (e.g. SD3.5 Large 839, W0009).
3. Top-10 open-weights on its modality's board (e.g. FLUX.2 [dev] #4 at 1000, Ming-Image #7 at 996, W0009).
4. #1 open-weights on its modality's board (Qwen-Image-2.1 on T2I at 1035, W0009; MiniMax H3 on T2V).
5. Inside the overall top 3 of its modality, closed models included. **Anchor: MiniMax Hailuo H3**, at
   1302 on the no-audio T2V board, third behind Wan 3.0 (1335) and Gemini Omni Flash (1332) (W0012).
   It is the only open-weights model in any board's overall top 3. On T2I the best open model sits
   18th (W0011).

Per-modality supply, so the maintainer can judge a split: image 20 (+4 closed), video 16 (+4 closed),
3D 11 (+2 closed), audio 12 (+2 closed), software 21. Each modality clears 10 alone. A split into
four categories would be defensible on supply, but it would scatter the shared tooling. The
recommendation is one category with modality recorded per row.

**Software rungs (sketch):** 1 single model family, 2 one modality with several families, 3 image
+ video, 4 image + video + audio/3D with graph composition. The top rung is anchored by **ComfyUI**,
named first among the four most-used UIs and the backend SwarmUI runs on (W0007).

## 5. Scoring ladder inputs

- Ladders needed: `model` for the 59 model rows and 12 closed rows; `software` for the 21
  app/engine/library rows. A `{model: model, software: software}` map is the recommendation.
- Licence strings met (✱ = custom or unusual, needs a tier decision):
  - Apache-2.0: flux ([schnell], [klein] 4B), qwen-image (base/2512/Edit), sana, kolors, lumina,
    z-image, ernie-image, longcat-image, omnigen, nextstep, step1x-edit, wan (2.1/2.2), mochi,
    open-sora, magi, helios, instantmesh, step1x-3d, ace-step v1, yue v1,
    heartmula, diffrhythm, thinksound, foleycrafter, and the software rows invokeai, sdnext,
    framepack, xdit, lightx2v, fastvideo and diffsynth-studio.
  - MIT: hidream, glm-image (weights), infinity-image, ming-image, kandinsky (repo/HF; a search
    summary says Apache, W0066), step-video, longcat-video, trellis, triposg, triposr, partcrafter,
    liveportrait, ace-step 1.5, mmaudio code, audiocraft, stable-audio-tools, swarmui and
    stable-diffusion.cpp.
  - GPL-3.0: comfyui, fooocus, krita-ai-diffusion, dream-textures. AGPL-3.0: stable-diffusion-webui,
    forge, stability-matrix, diffusionbee.
  - CreativeML OpenRAIL++-M: SDXL, pixart, latentsync weights.
  - CC BY-NC 4.0: fibo, musicgen, yue (YuE2), mmaudio weights.
  - ✱ FLUX Non-Commercial License (FLUX.1 [dev], FLUX.2 [dev], FLUX.2 [klein] 9B) (F0147, F0367, W0021).
  - ✱ Stability AI Community License (free commercial use under USD 1M revenue): SD3.5,
    stable-fast-3d, spar3d; variants stable-audio-community and stable-video-diffusion-community
    (W0019, F0247, F0363, F0356).
  - ✱ Tencent Hunyuan Community License, **excluding the EU, UK and South Korea**: hunyuan-image,
    hunyuan-video, hunyuan-3d, hunyuanvideo-foley (F0168, F0172, F0179).
  - ✱ MiniMax H3 Community License, **excluding the EU, UK, South Korea and the USA** (F0181).
  - ✱ MiniMax-Music3 Community License: MIT-style grant with attribution, plus written authorization
    above USD 20M yearly revenue (F0188).
  - ✱ LTX-2.x Community License, USD 10M revenue threshold (F0180).
  - ✱ Qwen RESEARCH LICENSE, non-commercial only: Qwen-Image-2.1 (F0170).
  - ✱ Ideogram 4 Non-Commercial model agreement (gated; paid self-serve commercial licence) (F0137, W0022).
  - ✱ CogVideoX License: registration for commercial use, 1M visits/month cap (F0171).
  - ✱ Skywork community licence (F0174).
  - ✱ CUBE3D Research-Only RAIL-MS (F0173).
  - ✱ SAM License (Meta, 2025-11-19) (F0246).
  - ✱ Easy Diffusion custom licence, MIT-style plus restricted uses (F0237).
  - ✱ WanGP Community License 2.0, no resale or SaaS (F0185).
  - ✱ SongGeneration: GitHub reports "other", and the licence text was not fetched (F0051, F0186).
  - Closed: proprietary service or API (12 rows).

## 6. Accepted candidates

### 6a. Registry rows

The same content is in `rows.yaml`, validated against `docs/schemas/registry.schema.json`, with no
slug or artifact collision against `research/corpus-index.tsv`.

```yaml
# Proposed category media_generation (issue #603). Candidate rows from the 2026-09-26 live sweep.
# Evidence: research/media_generation/sweep.md section 6b. Not yet a registry file.
category: media_generation
products:
- slug: flux
  display_name: FLUX
  type: model
  org: black-forest-labs
  github: black-forest-labs/flux2
  huggingface_model: black-forest-labs/FLUX.1-dev
- slug: stable-diffusion
  display_name: Stable Diffusion
  type: model
  org: stability-ai
  github: Stability-AI/generative-models
  huggingface_model: stabilityai/stable-diffusion-xl-base-1.0
- slug: qwen-image
  display_name: Qwen-Image
  type: model
  org: alibaba-cloud
  github: QwenLM/Qwen-Image
  huggingface_model: Qwen/Qwen-Image
- slug: hidream
  display_name: HiDream
  type: model
  org: hidream-ai
  github: HiDream-ai/HiDream-O1-Image
  huggingface_model: HiDream-ai/HiDream-O1-Image
- slug: sana
  display_name: SANA
  type: model
  org: nvidia
  github: NVlabs/Sana
- slug: pixart
  display_name: PixArt
  type: model
  org: pixart-alpha
  github: PixArt-alpha/PixArt-sigma
  huggingface_model: PixArt-alpha/PixArt-Sigma-XL-2-1024-MS
- slug: kolors
  display_name: Kolors
  type: model
  org: kuaishou
  github: Kwai-Kolors/Kolors
  huggingface_model: Kwai-Kolors/Kolors-diffusers
- slug: lumina
  display_name: Lumina
  type: model
  org: alpha-vllm
  github: Alpha-VLLM/Lumina-Image-2.0
  huggingface_model: Alpha-VLLM/Lumina-Image-2.0
- slug: hunyuan-image
  display_name: HunyuanImage
  type: model
  org: tencent
  github: Tencent-Hunyuan/HunyuanImage-3.0
  huggingface_model: tencent/HunyuanImage-3.0
- slug: z-image
  display_name: Z-Image
  type: model
  org: alibaba-cloud
  github: Tongyi-MAI/Z-Image
  huggingface_model: Tongyi-MAI/Z-Image-Turbo
- slug: fibo
  display_name: FIBO
  type: model
  org: bria-ai
  github: Bria-AI/FIBO
  huggingface_model: briaai/FIBO
- slug: glm-image
  display_name: GLM-Image
  type: model
  org: zhipu-z-ai
  github: zai-org/GLM-Image
  huggingface_model: zai-org/GLM-Image
- slug: ideogram
  display_name: Ideogram
  type: model
  org: ideogram
  github: ideogram-oss/ideogram4
  huggingface_model: ideogram-ai/ideogram-4-fp8
- slug: ernie-image
  display_name: ERNIE-Image
  type: model
  org: baidu
  huggingface_model: baidu/ERNIE-Image
- slug: longcat-image
  display_name: LongCat-Image
  type: model
  org: meituan
  github: meituan-longcat/LongCat-Image
  huggingface_model: meituan-longcat/LongCat-Image
- slug: omnigen
  display_name: OmniGen
  type: model
  org: vectorspacelab
  github: VectorSpaceLab/OmniGen2
  huggingface_model: OmniGen2/OmniGen2
- slug: infinity-image
  display_name: Infinity
  type: model
  org: bytedance
  github: FoundationVision/Infinity
  huggingface_model: FoundationVision/Infinity
- slug: ming-image
  display_name: Ming-Image
  type: model
  org: inclusion-ai
  huggingface_model: inclusionAI/Ming-Image-0.1-Design
- slug: nextstep
  display_name: NextStep
  type: model
  org: stepfun
  huggingface_model: stepfun-ai/NextStep-1.1
- slug: step1x-edit
  display_name: Step1X-Edit
  type: model
  org: stepfun
  github: stepfun-ai/Step1X-Edit
- slug: wan
  display_name: Wan
  type: model
  org: alibaba-cloud
  github: Wan-Video/Wan2.2
  huggingface_model: Wan-AI/Wan2.1-T2V-1.3B-Diffusers
- slug: hunyuan-video
  display_name: HunyuanVideo
  type: model
  org: tencent
  github: Tencent-Hunyuan/HunyuanVideo
  huggingface_model: tencent/HunyuanVideo-1.5
- slug: cogvideo
  display_name: CogVideo
  type: model
  org: zhipu-z-ai
  github: zai-org/CogVideo
  huggingface_model: zai-org/CogVideoX-5b
- slug: ltx
  display_name: LTX
  type: model
  org: lightricks
  github: Lightricks/LTX-2
  huggingface_model: Lightricks/LTX-2.5
- slug: mochi
  display_name: Mochi
  type: model
  org: genmo
  github: genmoai/mochi
  huggingface_model: genmo/mochi-1-preview
- slug: open-sora
  display_name: Open-Sora
  type: model
  org: hpc-ai-tech
  github: hpcaitech/Open-Sora
  huggingface_model: hpcai-tech/Open-Sora-v2
- slug: magi
  display_name: MAGI
  type: model
  org: sand-ai
  github: SandAI-org/MAGI-1
  huggingface_model: sand-ai/MAGI-2-preview
- slug: skyreels
  display_name: SkyReels
  type: model
  org: skywork
  github: SkyworkAI/SkyReels-V2
  huggingface_model: Skywork/SkyReels-V2-T2V-14B-720P
- slug: kandinsky
  display_name: Kandinsky
  type: model
  org: kandinsky-lab
  github: kandinskylab/kandinsky-5
- slug: step-video
  display_name: Step-Video
  type: model
  org: stepfun
  github: stepfun-ai/Step-Video-T2V
  huggingface_model: stepfun-ai/stepvideo-t2v
- slug: minimax-hailuo
  display_name: MiniMax Hailuo (H3)
  type: model
  org: minimax
  github: MiniMax-AI/MiniMax-H3
  huggingface_model: MiniMaxAI/MiniMax-H3
- slug: longcat-video
  display_name: LongCat-Video
  type: model
  org: meituan
  huggingface_model: meituan-longcat/LongCat-Video
- slug: helios
  display_name: Helios
  type: model
  org: pku-yuan-group
  github: PKU-YuanGroup/Helios
  huggingface_model: BestWishYsh/Helios-Distilled
- slug: stable-video-diffusion
  display_name: Stable Video Diffusion
  type: model
  org: stability-ai
  huggingface_model: stabilityai/stable-video-diffusion-img2vid-xt
- slug: liveportrait
  display_name: LivePortrait
  type: model
  org: kuaishou
  github: KlingAIResearch/LivePortrait
  huggingface_model: KlingTeam/LivePortrait
- slug: latentsync
  display_name: LatentSync
  type: model
  org: bytedance
  github: bytedance/LatentSync
  huggingface_model: ByteDance/LatentSync-1.6
- slug: trellis
  display_name: TRELLIS
  type: model
  org: microsoft
  github: microsoft/TRELLIS
  huggingface_model: microsoft/TRELLIS-image-large
- slug: hunyuan-3d
  display_name: Hunyuan3D
  type: model
  org: tencent
  github: Tencent-Hunyuan/Hunyuan3D-2
  huggingface_model: tencent/Hunyuan3D-2
- slug: step1x-3d
  display_name: Step1X-3D
  type: model
  org: stepfun
  github: stepfun-ai/Step1X-3D
  huggingface_model: stepfun-ai/Step1X-3D
- slug: triposg
  display_name: TripoSG
  type: model
  org: vast-ai
  github: VAST-AI-Research/TripoSG
  huggingface_model: VAST-AI/TripoSG
- slug: triposr
  display_name: TripoSR
  type: model
  org: vast-ai
  github: VAST-AI-Research/TripoSR
  huggingface_model: stabilityai/TripoSR
- slug: stable-fast-3d
  display_name: Stable Fast 3D
  type: model
  org: stability-ai
  github: Stability-AI/stable-fast-3d
  huggingface_model: stabilityai/stable-fast-3d
- slug: spar3d
  display_name: Stable Point Aware 3D
  type: model
  org: stability-ai
  github: Stability-AI/stable-point-aware-3d
  huggingface_model: stabilityai/stable-point-aware-3d
- slug: instantmesh
  display_name: InstantMesh
  type: model
  org: tencent
  github: TencentARC/InstantMesh
  huggingface_model: TencentARC/InstantMesh
- slug: cube
  display_name: Cube
  type: model
  org: roblox
  github: Roblox/cube
  huggingface_model: Roblox/cube3d-v0.1
- slug: sam-3d
  display_name: SAM 3D
  type: model
  org: meta
  github: facebookresearch/sam-3d-objects
  huggingface_model: facebook/sam-3d-objects
- slug: partcrafter
  display_name: PartCrafter
  type: model
  org: wgsxm
  github: wgsxm/PartCrafter
  huggingface_model: wgsxm/PartCrafter
- slug: stable-audio
  display_name: Stable Audio
  type: model
  org: stability-ai
  huggingface_model: stabilityai/stable-audio-3-medium
- slug: musicgen
  display_name: MusicGen
  type: model
  org: meta
  huggingface_model: facebook/musicgen-medium
- slug: ace-step
  display_name: ACE-Step
  type: model
  org: ace-step
  github: ace-step/ACE-Step-1.5
  huggingface_model: ACE-Step/Ace-Step1.5
- slug: yue
  display_name: YuE
  type: model
  org: m-a-p
  github: multimodal-art-projection/YuE
  huggingface_model: m-a-p/YuE2-3B
- slug: heartmula
  display_name: HeartMuLa
  type: model
  org: heartmula
  github: HeartMuLa/heartlib
  huggingface_model: HeartMuLa/HeartMuLa-oss-3B
- slug: songgeneration
  display_name: SongGeneration
  type: model
  org: tencent-ai-lab
  github: tencent-ailab/SongGeneration
- slug: diffrhythm
  display_name: DiffRhythm
  type: model
  org: aslp-lab
  github: ASLP-lab/DiffRhythm
  huggingface_model: ASLP-lab/DiffRhythm-1_2
- slug: minimax-music
  display_name: MiniMax Music
  type: model
  org: minimax
  huggingface_model: MiniMaxAI/MiniMax-Music3
- slug: mmaudio
  display_name: MMAudio
  type: model
  org: hkchengrex
  github: hkchengrex/MMAudio
  huggingface_model: hkchengrex/MMAudio
- slug: thinksound
  display_name: ThinkSound
  type: model
  org: alibaba-cloud
  github: QwenAudio/ThinkSound
  huggingface_model: FunAudioLLM/ThinkSound
- slug: hunyuanvideo-foley
  display_name: HunyuanVideo-Foley
  type: model
  org: tencent
  github: Tencent-Hunyuan/HunyuanVideo-Foley
  huggingface_model: tencent/HunyuanVideo-Foley
- slug: foleycrafter
  display_name: FoleyCrafter
  type: model
  org: open-mmlab
  github: open-mmlab/FoleyCrafter
- slug: comfyui
  display_name: ComfyUI
  type: software
  org: comfy-org
  github: Comfy-Org/ComfyUI
- slug: stable-diffusion-webui
  display_name: Stable Diffusion web UI (AUTOMATIC1111)
  type: software
  org: automatic1111
  github: AUTOMATIC1111/stable-diffusion-webui
- slug: forge
  display_name: Stable Diffusion WebUI Forge
  type: software
  org: lllyasviel
  github: lllyasviel/stable-diffusion-webui-forge
- slug: invokeai
  display_name: InvokeAI
  type: software
  org: invoke-ai
  github: invoke-ai/InvokeAI
  pypi: invokeai
- slug: fooocus
  display_name: Fooocus
  type: software
  org: lllyasviel
  github: lllyasviel/Fooocus
- slug: sdnext
  display_name: SD.Next
  type: software
  org: vladmandic
  github: vladmandic/sdnext
- slug: swarmui
  display_name: SwarmUI
  type: software
  org: mcmonkeyprojects
  github: mcmonkeyprojects/SwarmUI
- slug: krita-ai-diffusion
  display_name: Krita AI Diffusion
  type: software
  org: acly
  github: Acly/krita-ai-diffusion
- slug: stability-matrix
  display_name: Stability Matrix
  type: software
  org: lykos-ai
  github: LykosAI/StabilityMatrix
- slug: easy-diffusion
  display_name: Easy Diffusion
  type: software
  org: easydiffusion
  github: easydiffusion/easydiffusion
- slug: diffusionbee
  display_name: DiffusionBee
  type: software
  org: divamgupta
  github: divamgupta/diffusionbee-stable-diffusion-ui
- slug: dream-textures
  display_name: Dream Textures
  type: software
  org: carson-katri
  github: carson-katri/dream-textures
- slug: wan2gp
  display_name: WanGP
  type: software
  org: deepbeepmeep
  github: deepbeepmeep/Wan2GP
- slug: framepack
  display_name: FramePack
  type: software
  org: lllyasviel
  github: lllyasviel/FramePack
- slug: stable-diffusion-cpp
  display_name: stable-diffusion.cpp
  type: software
  org: leejet
  github: leejet/stable-diffusion.cpp
- slug: xdit
  display_name: xDiT
  type: software
  org: xdit-project
  github: xdit-project/xDiT
  pypi: xfuser
- slug: lightx2v
  display_name: LightX2V
  type: software
  org: modeltc
  github: ModelTC/LightX2V
- slug: fastvideo
  display_name: FastVideo
  type: software
  org: hao-ai-lab
  github: hao-ai-lab/FastVideo
  pypi: fastvideo
- slug: diffsynth-studio
  display_name: DiffSynth-Studio
  type: software
  org: modelscope-alibaba
  github: modelscope/DiffSynth-Studio
- slug: stable-audio-tools
  display_name: stable-audio-tools
  type: software
  org: stability-ai
  github: Stability-AI/stable-audio-tools
  pypi: stable-audio-tools
- slug: audiocraft
  display_name: AudioCraft
  type: software
  org: meta
  github: facebookresearch/audiocraft
  pypi: audiocraft
- slug: gpt-image
  display_name: GPT Image
  type: model
  org: openai
  homepage: https://developers.openai.com/api/docs/models
- slug: nano-banana
  display_name: Nano Banana (Gemini Image)
  type: model
  org: google
  homepage: https://deepmind.google/models/gemini-image/
- slug: midjourney
  display_name: Midjourney
  type: model
  org: midjourney
  homepage: https://www.midjourney.com
- slug: seedream
  display_name: Seedream
  type: model
  org: bytedance-seed-volcano-engine
  homepage: https://seed.bytedance.com/en/seedream
- slug: veo
  display_name: Veo
  type: model
  org: google
  homepage: https://deepmind.google/models/veo/
- slug: kling
  display_name: Kling
  type: model
  org: kuaishou
  homepage: https://kling.ai/
- slug: seedance
  display_name: Seedance
  type: model
  org: bytedance-seed-volcano-engine
  homepage: https://seed.bytedance.com/en/seedance
- slug: runway-gen
  display_name: Runway Gen
  type: model
  org: runway
  homepage: https://runway.com
- slug: suno
  display_name: Suno
  type: model
  org: suno
  homepage: https://suno.com
- slug: lyria
  display_name: Lyria
  type: model
  org: google
  homepage: https://deepmind.google/models/lyria/
- slug: meshy
  display_name: Meshy
  type: model
  org: meshy
  homepage: https://www.meshy.ai/
- slug: tripo
  display_name: Tripo
  type: model
  org: vast-ai
  homepage: https://www.tripo3d.ai/
```

### 6b. Evidence table

| slug | open status | license(s) + source | archived/fork | last push | last release | adoption signal | member checkpoints/SKUs | org GitHub/HF handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| flux | open-weights | weights: FLUX.1 [dev]/FLUX.2 [dev] "FLUX Non-Commercial License" (F0367, F0147, W0021); FLUX.1 [schnell] and FLUX.2 [klein] 4B Apache-2.0 (F0077, F0169); FLUX.2 [klein] 9B non-commercial (F0077); code Apache-2.0 (F0001, F0002) | no/no (F0002) | 2026-03-12 flux2 (F0002); FLUX.1 repo black-forest-labs/flux 2025-07-31 (F0001) | no GitHub release returned by ecosyste.ms for flux2 (F0411) or flux (F0346) | HF 30d downloads FLUX.1-dev 692,264 (F0367); FLUX.2-dev 406,993 (F0147); FLUX.2-klein-4B 404,007 (F0077) | FLUX.1 [dev]/[schnell]/Kontext/Krea/Fill/Redux; FLUX.2 [dev]/[klein] 4B/9B; API-only FLUX.2 pro/flex (W0021, W0011) | GH black-forest-labs; HF black-forest-labs | AA open-weights T2I Elo FLUX.2 [dev] 1000 (W0009). Row declares the current FLUX.2 repo and the most-downloaded checkpoint (FLUX.1-dev). |
| stable-diffusion | open-weights | SD3.5: Stability AI Community License (free commercial use under USD 1M annual revenue) (F0148, W0019); SDXL: openrail++ (F0368); code MIT (F0003) | no/no (F0003) | 2025-12-16 (F0003); sd3.5 repo 2025-01-08 (F0004) | 0.1.0, 2023-07-27 (F0350) | HF 30d downloads SDXL base 3,598,555 (F0368); SD3.5 Large 100,154 (F0148) | SD 1.5/2.1/XL/Turbo, SD3 Medium, SD3.5 Large/Medium/Turbo (F0078) | GH Stability-AI; HF stabilityai | AA open-weights T2I Elo SD3.5 Large 839 (W0009). |
| qwen-image | open-weights | Qwen-Image / 2512 / Edit-2511 Apache-2.0 (F0114, F0115, F0117); Qwen-Image-2.1 "Qwen RESEARCH LICENSE", non-commercial only (F0116, F0170); Qwen-Image-3.0 closed (W0011) | no/no (F0005) | 2026-02-10 (F0005) | not fetched | HF 30d downloads Qwen-Image 290,124 (F0114); Qwen-Image-Edit-2511 317,872 (F0117); Edit-2509 465,386 (F0079) | Qwen-Image, -2512, -Edit/-2509/-2511, -2.1 (research licence); closed -2.0 Pro / -3.0 (W0011) | GH QwenLM; HF Qwen | Separate product from the `qwen` LLM head row, as qwen-coder/qwen3-embedding are. Top open-weights T2I on AA: Qwen-Image-2.1 Elo 1035 (W0009). Current open release is non-commercial. |
| hidream | open | MIT (F0007, F0119; I1: F0006, F0118) | no/no (F0007) | 2026-06-22 (F0007) | not fetched | HF 30d downloads O1-Image 6,071 (F0119); I1-Fast 54,081 (F0080) | HiDream-I1 Full/Dev/Fast, HiDream-O1-Image / -Dev | GH HiDream-ai; HF HiDream-ai | AA open-weights T2I Elo O1-Image 979 (W0009). O1 open-sourced 2026-05-08 (W0002). |
| sana | open | Apache-2.0 code (F0008) and weights (F0120, F0121, F0362) | no/no (F0008) | 2026-09-21 (F0008) | not fetched | GitHub stars 9,144 (F0008); HF API reports 0 downloads on SANA diffusers repos (F0120, F0362), so no usable HF instrument | SANA 1.6B, SANA 1.5 4.8B, SANA-Sprint, SANA-Video 2.0 (F0081) | GH NVlabs; HF Efficient-Large-Model | AA open-weights T2I Elo Sana Sprint 1.6B 753 (W0009). HF omitted from row: zero-download repos would band adoption wrongly. |
| pixart | open-weights | weights openrail++ (F0370); code Apache-2.0 (F0009) | no/no (F0009) | 2024-10-31 (F0009) | not fetched | HF 30d downloads Sigma-XL-2-1024 34,593 (F0370) | PixArt-alpha, PixArt-Sigma (F0082) | GH/HF PixArt-alpha | Dormant: no push since 2024-10. |
| kolors | open | Apache-2.0 on repo and HF card (F0010, F0141, F0371) | no/no (F0010) | 2024-11-13 (F0010) | not fetched | HF 30d downloads Kolors-diffusers 5,336 (F0371) | Kolors, Kolors IP-Adapter variants (F0083) | GH/HF Kwai-Kolors | Dormant since 2024-11. |
| lumina | open | Apache-2.0 (F0011, F0140) | no/no (F0011) | 2026-05-22 (F0011) | not fetched | HF 30d downloads 996 (F0140) | Lumina-Image 2.0, Lumina-mGPT, Lumina-DiMOO (F0084) | GH/HF Alpha-VLLM | AA open-weights T2I Elo Lumina Image v2 781 (W0009). |
| hunyuan-image | open-weights | Tencent Hunyuan Community License; does not apply in the EU, UK and South Korea (F0179, F0364) | no/no (F0012) | 2026-06-23 (F0012) | not fetched | HF 30d downloads HunyuanImage-3.0-Instruct 17,466 (F0085); 3.0 3,417 (F0364) | HunyuanImage 2.1, 3.0, 3.0-Instruct (F0013, F0085) | GH Tencent-Hunyuan; HF tencent | AA open-weights T2I Elo 3.0 Instruct 963 (W0009). Distinct from the `hunyuan` LLM tail row. |
| z-image | open | Apache-2.0 (F0014, F0158) | no/no (F0014) | 2026-02-09 (F0014) | not fetched | HF 30d downloads Z-Image-Turbo 609,489 (F0158); Z-Image 59,864 (F0086) | Z-Image, Z-Image-Turbo | GH/HF Tongyi-MAI | AA open-weights T2I Elo Z-Image Turbo 940 (W0009). Tongyi-MAI line, marketed apart from Qwen-Image. |
| fibo | open-weights | CC BY-NC 4.0 (repo LICENSE F0238; HF license_name bria-fibo linking CC BY-NC F0163) | no/no (F0015) | 2026-01-07 (F0015) | not fetched | HF 30d downloads FIBO 702 (F0163); Fibo-Edit-1.5-turbo 2,383 (F0087) | FIBO, FIBO Lite, Fibo-1.5, Fibo-Edit (F0087) | GH Bria-AI; HF briaai | AA open-weights T2I Elo FIBO 879 (W0009). |
| glm-image | open | weights MIT (F0165); code Apache-2.0 (F0016) | no/no (F0016) | 2026-03-20 (F0016) | not fetched | HF 30d downloads 8,011 (F0165) | GLM-Image; predecessor CogView4-6B (F0088) | GH/HF zai-org | AA open-weights T2I Elo 889 (W0009). Contested: SKU of `glm` head or its own line? |
| ideogram | open-weights | weights "Ideogram 4 Non-Commercial" model agreement, gated (F0137, W0022); commercial use needs paid licence (W0022); code licence per W0045 Apache-2.0, repo LICENSE fetched (F0250) | no/no (F0399) | 2026-06-04 per ecosyste.ms (F0399); ungh pushedAt 2026-06-30 (F0230) | not fetched | HF 30d downloads ideogram-4-fp8 58,610 (F0137); nf4 2,584 (F0138) | Ideogram 4.0 open weights (fp8, nf4); hosted API tiers | GH ideogram-oss; HF ideogram-ai | First open-weight Ideogram model, 9.3B, 2026-06-03 (W0020). AA open-weights T2I Elo 1010 (W0009). |
| ernie-image | open | Apache-2.0 (F0164) | n/a (no GitHub repo fetched) | HF lastModified 2026-04-17 (F0164) | not fetched | HF 30d downloads ERNIE-Image 990 (F0164); ERNIE-Image-Turbo 3,900 (F0111) | ERNIE-Image, ERNIE-Image-Turbo | HF baidu | AA open-weights T2I Elo Turbo 923 (W0009). Contested: SKU of `ernie` head? |
| longcat-image | open | Apache-2.0 (F0021, F0092) | no/no (F0021) | 2026-04-02 (F0021) | not fetched | HF 30d downloads LongCat-Image 13,815; Edit-Turbo 23,408 (F0092) | LongCat-Image, -Dev, -Edit, -Edit-Turbo | GH/HF meituan-longcat | AA open-weights T2I Elo 860 (W0009). |
| omnigen | open | Apache-2.0 (F0017, F0089) | no/no (F0017) | 2026-03-20 (F0017) | not fetched | HF 30d downloads 4,767 (F0089) | OmniGen, OmniGen2 | GH VectorSpaceLab; HF OmniGen2 | AA open-weights T2I Elo OmniGen V2 726 (W0009). Unified generation/editing; borderline with multimodal_models. |
| infinity-image | open | MIT (F0019, F0144) | no/no (F0019) | 2026-04-16 (F0019) | not fetched | HF 30d downloads 79 (F0144) | Infinity 2B/8B | GH/HF FoundationVision | AA open-weights T2I Elo Infinity 8B 873 (W0009). Org attributed as ByteDance by AA (W0009). Slug avoids the `infinity` storage head product. New org slug `bytedance` (non-Seed ByteDance teams); Q14. |
| ming-image | open | MIT (F0145) | n/a | HF created 2026-09-17, lastModified 2026-09-23 (F0145) | not fetched | HF API reports 0 downloads (F0145) | Ming-Image-0.1-Design | HF inclusionAI | AA open-weights T2I #7, Elo 996 (W0009). Nine days old at fetch. Ming-Omni models belong to brief 2. |
| nextstep | open | Apache-2.0 (F0101) | n/a | HF lastModified 2025-12-23 (F0101) | not fetched | HF 30d downloads 1,453 (F0101) | NextStep-1, NextStep-1.1 | HF stepfun-ai | Autoregressive T2I. |
| step1x-edit | open | Apache-2.0 (F0373) | no/no (F0373) | 2026-04-29 (F0373) | not fetched | GitHub stars 2,264 (F0373) | Step1X-Edit v1.0, v1p1, v1p2 | GH stepfun-ai | Instruction image editor named among main open editors (W0065). |
| wan | open | Apache-2.0 for every Wan 2.1/2.2 checkpoint fetched (F0093, F0149, F0162, F0369); Wan 2.5/2.6/2.7/3.0 closed, API-only (W0016, W0011, W0012; no Wan3 weights on HF F0191, F0192) | no/no (F0023) | 2026-09-21 (F0023) | no GitHub release returned by ecosyste.ms (F0345) | HF 30d downloads Wan2.1-T2V-1.3B-Diffusers 264,951 (F0369); Wan2.2-TI2V-5B-Diffusers 159,486 (F0093) | Wan 2.1 (T2V/I2V/VACE), Wan 2.2 (T2V-A14B, I2V-A14B, TI2V-5B, S2V, Animate, Animate-2), Wan-Dancer (F0093, F0192) | GH Wan-Video; HF Wan-AI | Top closed video Elo is Wan 3.0 (1335, W0012). Current flagship closed; newest open drop Wan2.2-Animate-2 (2026-08-06, F0192). |
| hunyuan-video | open-weights | Tencent Hunyuan Community License, EU/UK/South Korea excluded (F0168, F0122, F0123) | no/no (F0024) | 2026-06-29 (F0024); 1.5 repo 2026-04-10 (F0025) | not fetched | HF 30d downloads 1.5: 1,193; v1: 1,269 (F0123, F0122); GitHub stars 12,550 (F0024) | HunyuanVideo, HunyuanVideo-I2V, HunyuanVideo 1.5 (8.3B, W0001) | GH Tencent-Hunyuan; HF tencent | Not on AA open-weights video boards as fetched (W0010, W0013). |
| cogvideo | open-weights | CogVideoX License: academic free; commercial needs registration, 1M visits/month cap (F0171); CogVideoX-2b Apache-2.0 (F0088); code Apache-2.0 (F0026) | no/no (F0026) | 2025-11-04 (F0026) | not fetched | HF 30d downloads CogVideoX-5b 20,115; 2b 17,232 (F0088) | CogVideo, CogVideoX 2b/5b/5b-I2V, CogVideoX1.5 | GH/HF zai-org |  |
| ltx | open-weights | LTX-2.x Community License (2026-08-11), revenue threshold USD 10M for free commercial use (F0180, F0150); LTX-Video repo Apache-2.0 (F0240, F0027) | no/no (F0028) | 2026-08-26 (F0028) | no GitHub release returned by ecosyste.ms (F0344) | HF 30d downloads LTX-2.5 1,604,804 (F0150); LTX-2.3 1,098,602; LTX-Video 773,634 (F0094) | LTX-Video 0.9.x, LTX-2, LTX-2.3, LTX-2.5 (+ fp8/nvfp4, IC-LoRAs) (F0094) | GH/HF Lightricks | Open-weights video board: LTX-2.5 Fast Elo 1055 (W0010); 1218 no-audio (W0012). |
| mochi | open | Apache-2.0 (F0029, F0155) | no/no (F0029) | 2025-11-14 (F0029) | not fetched | HF 30d downloads 7,819 (F0155) | Mochi 1 preview | GH genmoai; HF genmo |  |
| open-sora | open | Apache-2.0 (F0030, F0157) | no/no (F0030) | 2026-04-09 (F0030) | v1.3, 2025-02-21 (F0347) | HF 30d downloads Open-Sora-v2 1,189 (F0157); GitHub stars 29,836 (F0030) | Open-Sora 1.x, 2.0 | GH hpcaitech; HF hpcai-tech | Org already on map via colossal-ai tail row. |
| magi | open | Apache-2.0 (F0031, F0126, F0127, F0202; W0017) | no/no (F0031) | 2026-06-17 MAGI-1; 2026-08-06 MAGI-2-preview (F0031, F0202) | not fetched | HF API reports 0 downloads (F0126, F0127); GitHub stars 3,788 (F0031) | MAGI-1, MAGI-2-preview (114B MoE, W0017) | GH SandAI-org; HF sand-ai | Open-weights I2V board #2, Elo 1094 (W0013). |
| skyreels | open-weights | Skywork community licence, custom terms (F0174, F0267, F0161) | no/no (F0032) | 2026-01-29 (F0032) | not fetched | HF 30d downloads 1,407 (F0161); V3-A2V 1,110 (F0098) | SkyReels V1, V2, V3 (open); V4 closed (W0012) | GH SkyworkAI; HF Skywork |  |
| kandinsky | open | MIT per repo metadata and HF card (F0033, F0142); a search summary says Apache-2.0 (W0066), unresolved | no/no (F0033) | 2026-03-31 (F0033) | not fetched | GitHub stars 736 (F0033); HF reports 0 downloads (F0142) | Kandinsky 5.0 Video Lite/Pro, Image Lite (W0066); earlier Kandinsky 2/3 (W0038) | GH/HF kandinskylab | Backed by Sber (W0066). Covers image and video. |
| step-video | open | MIT (F0212, F0360) | no/no (F0212) | 2025-03-17 (F0212) | not fetched | HF 30d downloads 80 (F0360) | Step-Video-T2V, -TI2V | GH/HF stepfun-ai | Dormant since 2025-03. |
| minimax-hailuo | open-weights | MiniMax H3 Community License; excluded territories EU, UK, South Korea and the USA (F0181, F0136) | no/no (F0221) | 2026-08-15 (F0221) | not fetched | HF 30d downloads 3,657,004 (F0136) | MiniMax-H3 33B, H3-Regenerate-2K (W0015); closed Hailuo API tiers | GH MiniMax-AI; HF MiniMaxAI | #1 open-weights video on AA: T2V Elo 1220 with audio, 1302 no-audio (W0010, W0012). Distinct from `minimax` LLM head row. Scorer note: 3,657,004 30d downloads is the largest in the set for a model released ~6 weeks before fetch (created 2026-07-28, F0136); worth a second read before banding. |
| longcat-video | open | MIT (F0092) | n/a | HF lastModified 2025-10-29 (F0092) | not fetched | HF 30d downloads 1,710 (F0092) | LongCat-Video, LongCat-Video-Avatar-1.5 (F0092) | HF meituan-longcat | Same vendor brand as longcat-image; one row or two is Q9. |
| helios | open | Apache-2.0 (F0207, F0359) | no/no (F0207) | 2026-08-24 (F0207) | not fetched | HF 30d downloads 1,374 (F0359) | Helios 14B real-time long video (F0307) | GH PKU-YuanGroup; HF BestWishYsh | 2026 release (arXiv 2603.04379, F0307). |
| stable-video-diffusion | open-weights | stable-video-diffusion-community (F0356) | n/a | HF lastModified 2024-07-10 (F0356) | not fetched | HF 30d downloads img2vid-xt 249,578 (F0356); img2vid 86,202 (F0078) | SVD img2vid, img2vid-xt | HF stabilityai | Dormant since 2024. |
| liveportrait | open | MIT, copyright Kuaishou Visual Generation and Interaction Center (F0241, F0351) | no/no (F0196) | 2026-06-01 (F0196) | no GitHub release returned by ecosyste.ms (F0349) | HF 30d downloads 10,340 (F0351); GitHub stars 19,114 (F0196) | LivePortrait (humans, animals) | GH KlingAIResearch; HF KlingTeam | Portrait animation; scope Q7. |
| latentsync | open-weights | weights openrail++ (F0355); code Apache-2.0 (F0197) | no/no (F0197) | 2025-06-20 (F0197) | not fetched | HF 30d downloads 1.6: 200,128; 1.5: 70,958 (F0113) | LatentSync 1.5, 1.6 | GH bytedance; HF ByteDance | Lip-sync video; scope Q7. New org slug `bytedance`; Q14. |
| trellis | open | MIT (F0034, F0035, F0366, F0151) | no/no (F0034) | 2026-06-26 TRELLIS; 2026-07-10 TRELLIS.2 (F0034, F0035) | no release returned (ungh 404, F0332) | HF 30d downloads TRELLIS-image-large 2,118,600 (F0366); TRELLIS.2-4B 1,724,957 (F0151) | TRELLIS (image/text large), TRELLIS.2-4B | GH microsoft; HF microsoft |  |
| hunyuan-3d | open-weights | Tencent Hunyuan 3D Community License, EU/UK/South Korea excluded (F0172, F0365); 2.5/3.0/3.1 API-only (W0064) | no/no (F0036) | 2025-10-28 (F0036) | not fetched | HF 30d downloads Hunyuan3D-2 108,234; 2.1 54,794; 2mini 33,588 (F0085) | Hunyuan3D 2.0, 2mini, 2mv, 2.1 | GH Tencent-Hunyuan; HF tencent | Current flagship closed. |
| step1x-3d | open | Apache-2.0 (F0038, F0129) | no/no (F0038) | 2025-09-08 (F0038) | not fetched | HF API reports 0 downloads (F0129); GitHub stars 870 (F0038) | Step1X-3D | GH/HF stepfun-ai |  |
| triposg | open | MIT (F0039, F0159) | no/no (F0039) | 2025-04-18 (F0039) | not fetched | HF 30d downloads 4,986 (F0159) | TripoSG | GH VAST-AI-Research; HF VAST-AI |  |
| triposr | open | MIT (F0040, F0160) | no/no (F0040) | 2026-06-04 (F0040) | not fetched | HF 30d downloads 201,115 (F0160) | TripoSR (VAST with Stability AI; weights on stabilityai HF) | GH VAST-AI-Research; HF stabilityai | Joint VAST/Stability release; org attribution Q. |
| stable-fast-3d | open-weights | Stability AI Community License (F0247, F0131) | no/no (F0041) | 2025-01-22 (F0041) | not fetched | HF 30d downloads 14,447 (F0131) | SF3D | GH Stability-AI; HF stabilityai |  |
| spar3d | open-weights | stabilityai-ai-community (F0357) | no/no (F0042) | 2025-05-05 (F0042) | not fetched | HF 30d downloads 8,780 (F0357) | SPAR3D | GH Stability-AI; HF stabilityai |  |
| instantmesh | open | Apache-2.0 (F0043, F0358) | no/no (F0043) | 2025-01-03 (F0043) | not fetched | HF 30d downloads 18,045 (F0358) | InstantMesh | GH/HF TencentARC | Dormant since 2025-01. |
| cube | open-weights | CUBE3D Research-Only RAIL-MS licence (F0173); HF label openrail (F0128) | no/no (F0044) | 2026-05-28 (F0044) | not fetched | HF API reports 0 downloads (F0128); GitHub stars 1,256 (F0044) | Cube3d-v0.1 | GH/HF Roblox | Research-only. |
| sam-3d | open-weights | SAM License (custom, 2025-11-19) (F0246); HF gated manual (F0353) | no/no (F0216) | 2026-06-02 (F0216) | not fetched | HF 30d downloads 3,522 (F0353) | SAM 3D Objects | GH facebookresearch; HF facebook | Contested with classic_ml_cv (SAM family). |
| partcrafter | open | MIT (F0217, F0361) | no/no (F0217) | 2025-09-19 (F0217) | not fetched | HF 30d downloads 658 (F0361) | PartCrafter | GH/HF wgsxm | Academic release. |
| stable-audio | open-weights | weights "stable-audio-community" licence (F0363, F0130) | n/a (no GitHub repo declared; code is the stable-audio-tools row) | HF lastModified 2026-06-16 (F0363) | not fetched | HF 30d downloads Stable Audio 3 Medium 81,781 (F0363); Open 1.0 20,764 (F0130) | Stable Audio Open 1.0, Open Small, Stable Audio 3 Medium; API Stable Audio 3 Large/2.5 (W0033) | HF stabilityai | Model row; the stable-audio-tools library is its own row (as musicgen/audiocraft). AA instrumental Elo Stable Audio 3 Medium 1000 (W0033). |
| musicgen | open-weights | CC BY-NC 4.0 (F0153) | n/a | HF lastModified 2023-11-17 (F0153) | n/a | HF 30d downloads musicgen-medium 1,947,422; small 142,904; large 89,340 (F0104) | MusicGen small/medium/large (F0104) | HF facebook | Model row; the AudioCraft library is its own row. AA instrumental Elo 882 (W0033). |
| ace-step | open | MIT for 1.5 (F0048, F0154); v1 Apache-2.0 (F0047) | no/no (F0048) | 2026-09-03 (F0048) | v0.1.8, 2026-05-18 (F0329) | HF 30d downloads Ace-Step1.5 59,314 (F0154) | ACE-Step v1 3.5B, ACE-Step 1.5 (base/sft/turbo/XL) (F0105) | GH ace-step; HF ACE-Step |  |
| yue | open-weights | YuE2 weights CC BY-NC 4.0 (F0372, F0187); YuE v1 weights Apache-2.0 (F0133); code Apache-2.0 (F0049) | no/no (F0049) | 2026-09-23 (F0049) | yue2-v0.1.6, 2026-09-09 (F0330) | HF 30d downloads YuE2-3B 25,798 (F0372); YuE-s1-7B 8,430 (F0133) | YuE s1/s2 (v1), YuE2-3B | GH multimodal-art-projection; HF m-a-p | Licence tightened from Apache (v1) to NC (v2). |
| heartmula | open | Apache-2.0 (F0050, F0146) | no/no (F0050) | 2026-09-26 (F0050) | no release returned (ungh 404, F0331) | HF 30d downloads 791 (F0146); happy-new-year 2,711 (F0107) | HeartMuLa-oss-3B, RL-oss-3B, HeartCodec | GH/HF HeartMuLa | 2026 release (W0004). |
| songgeneration | open-weights | GitHub label "other" (F0051); LICENSE text fetch did not complete (F0186 404 at /LICENSE); HF metadata fetch returned 401 (F0134) | no/no (F0051) | 2026-03-12 (F0051) | not fetched | GitHub stars 1,529 (F0051) | SongGeneration (LeVo) | GH tencent-ailab | Licence text still unread; status tag provisional. |
| diffrhythm | open | Apache-2.0 per repo (F0052); HF card has no licence field (F0135) | no/no (F0052) | 2025-11-27 (F0052) | not fetched | HF 30d downloads 157 (F0135) | DiffRhythm 1.0, 1.2 | GH/HF ASLP-lab |  |
| minimax-music | open-weights | MiniMax-Music3 Community License: MIT-style grant plus attribution and a separate authorization above USD 20M yearly revenue (F0188) | n/a | HF lastModified 2026-08-14 (F0190) | not fetched | HF 30d downloads 10,096 (F0190) | MiniMax Music 3.0 open weights; API Music 2.x (W0032) | HF MiniMaxAI | Released 2026-08-13 (W0004). AA vocal Elo 1000 (W0032). |
| mmaudio | open-weights | code MIT (F0053); weights CC BY-NC 4.0 (F0132) | no/no (F0053) | 2026-02-23 (F0053) | not fetched | HF API reports 0 downloads (F0132); GitHub stars 2,267 (F0053) | MMAudio S/M/L | GH/HF hkchengrex | Video-to-audio (CVPR 2025) from UIUC and Sony AI (W0035). |
| thinksound | open | Apache-2.0 per README (F0270) and HF card (F0352); no LICENSE file at repo root (F0249, F0258, F0263) | no/no (F0199) | 2026-04-03 (F0199) | not fetched | HF API reports 0 downloads (F0352); GitHub stars 1,380 (F0199) | ThinkSound | GH QwenAudio; HF FunAudioLLM | Tongyi Lab (W0035). |
| hunyuanvideo-foley | open-weights | tencent-hunyuan-community (F0125) | no/no (F0055) | 2025-09-28 (F0055) | not fetched | HF 30d downloads 455 (F0125) | HunyuanVideo-Foley | GH Tencent-Hunyuan; HF tencent |  |
| foleycrafter | open | Apache-2.0 (F0215) | no/no (F0215) | 2026-06-15 (F0215) | not fetched | GitHub stars 664 (F0215) | FoleyCrafter | GH open-mmlab |  |
| comfyui | open | GPL-3.0 (F0176) | no/no (F0076) | 2026-09-25 (F0076) | v0.37.0, 2026-09-21 (F0308) | GitHub stars 134,880 (F0076); no first-party package fetched | ComfyUI core (moved from comfyanonymous, F0056 404 on old name) | GH Comfy-Org |  |
| stable-diffusion-webui | open | AGPL-3.0 (F0057) | no/no (F0057) | 2026-03-02 (F0057) | v1.10.1, 2025-02-09 (F0312) | GitHub stars 165,027 (F0057) |  | GH AUTOMATIC1111 | Described as superseded by Forge (W0007). |
| forge | open | AGPL-3.0 (F0058) | no/no (F0058) | 2025-07-31 (F0058) | "latest", 2024-02-05 (F0313) | GitHub stars 13,032 (F0058) |  | GH lllyasviel | Community forks reForge and Forge Classic parked. |
| invokeai | open | Apache-2.0 (F0059, F0275) | no/no (F0059) | 2026-09-21 (F0059) | v6.14.1, 2026-09-06 (F0309) | PyPI invokeai 23,263/month (F0275) |  | GH invoke-ai | PyPI project_urls point to invoke-ai/InvokeAI (F0305); install doc says to install the invokeai package (F0407). |
| fooocus | open | GPL-3.0 (F0060) | no/no (F0060) | 2025-12-01 (F0060) | v2.5.5, 2024-08-12 (F0314) | GitHub stars 53,101 (F0060) |  | GH lllyasviel |  |
| sdnext | open | Apache-2.0 (F0061) | no/no (F0061) | 2026-09-23 (F0061) | no GitHub release returned by ecosyste.ms (F0341); ungh fetch did not complete (F0310) | GitHub stars 7,346 (F0061) |  | GH vladmandic |  |
| swarmui | open | MIT (F0062) | no/no (F0062) | 2026-09-22 (F0062) | 0.9.8-Beta, 2026-02-06 (F0311) | GitHub stars 4,586 (F0062) |  | GH mcmonkeyprojects | Runs on a ComfyUI backend (W0007). |
| krita-ai-diffusion | open | GPL-3.0 (F0065) | no/no (F0065) | 2026-09-23 (F0065) | v1.51.1, 2026-06-05 (F0342) | GitHub stars 10,631 (F0065) |  | GH Acly |  |
| stability-matrix | open | AGPL-3.0 (F0074) | no/no (F0074) | 2026-09-16 (F0074) | v2.16.4, 2026-09-16 (F0316) | GitHub stars 8,837 (F0074) |  | GH LykosAI | Package manager / launcher for SD UIs (W0041). |
| easy-diffusion | source-available | custom licence: MIT-style Section I plus Section II restricted uses (F0237) | no/no (F0206) | 2026-09-11 (F0206) | v3.0.16, 2026-03-31 (F0323) | GitHub stars 10,462 (F0206); PyPI sdkit (its engine, easydiffusion/sdkit) 34,063/month (F0293), not declared |  | GH easydiffusion |  |
| diffusionbee | open | AGPL-3.0 (F0204) | no/no (F0204) | 2024-10-30 (F0204) | 2.5.3, 2024-08-14 (F0324) | GitHub stars 13,585 (F0204) |  | GH divamgupta | Dormant since 2024-10. |
| dream-textures | open | GPL-3.0 (F0223) | no/no (F0223) | 2026-09-17 (F0223) | 0.4.1, 2024-08-26 (F0325) | GitHub stars 8,206 (F0223) |  | GH carson-katri | Blender add-on. |
| wan2gp | source-available | WanGP Community License 2.0: free use, no resale/SaaS/white-label without a commercial licence (F0185) | no / FORK=true per ecosyste.ms (F0066) | 2026-09-18 (F0066) | no release returned (ungh 404, F0326) | GitHub stars 9,510 (F0066) |  | GH deepbeepmeep | Flagged as a GitHub fork; low-VRAM video app. |
| framepack | open | Apache-2.0 (F0068) | no/no (F0068) | 2025-10-16 (F0068) | "windows", 2025-04-18 (F0348) | GitHub stars 17,264 (F0068) |  | GH lllyasviel | Next-frame video method + desktop app. |
| stable-diffusion-cpp | open | MIT (F0067) | no/no (F0067) | 2026-09-19 (F0067) | master-920-2f88688, 2026-09-25 (F0317) | GitHub stars 7,022 (F0067); third-party binding stable-diffusion-cpp-python 2,600/month (F0294), not declared |  | GH leejet | Contested with inference_code. |
| xdit | open | Apache-2.0 (F0070) | no/no (F0070) | 2026-09-18 (F0070) | 0.7.0, 2026-09-25 (F0320) | PyPI xfuser 23,947/month (F0278) |  | GH xdit-project | PyPI homepage is the xDiT repo (F0306); README: pip install xfuser (F0402). Contested with inference_code. |
| lightx2v | open | Apache-2.0 (F0073) | no/no (F0073) | 2026-09-25 (F0073) | 0.5.0, 2026-09-10 (F0319) | GitHub stars 2,858 (F0073); no PyPI package found (F0285) |  | GH ModelTC | Contested with inference_code. |
| fastvideo | open | Apache-2.0 (F0072, F0279) | no/no (F0072) | 2026-09-25 (F0072) | v0.2.0, 2026-06-04 (F0321) | PyPI fastvideo 1,332/month (F0279) |  | GH hao-ai-lab | README: pip install fastvideo (F0403). Contested with inference_code. |
| diffsynth-studio | open | Apache-2.0 (F0069, F0280) | no/no (F0069) | 2026-09-21 (F0069) | v1.1.9, 2025-11-18 (F0322); PyPI 2.0.17, 2026-07-14 (F0280) | GitHub stars 13,156 (F0069); PyPI diffsynth 5,432/month (F0280) not declared: README documents only a source install (F0404) |  | GH modelscope | PyPI author ModelScope Team (F0303). Contested with ml_frameworks/finetuning_code. |
| stable-audio-tools | open | MIT (F0045, F0277) | no/no (F0045) | 2026-09-18 (F0045) | no release returned (ungh 404, F0327); PyPI 0.0.20, 2026-05-20 (F0277) | PyPI stable-audio-tools 102,734/month (F0277) | training/inference library for Stable Audio models | GH Stability-AI | PyPI author Stability AI (F0302); README documents pip install "stable-audio-tools[train]" (F0405). |
| audiocraft | open | MIT code (F0046, F0276) | no/no (F0046) | 2026-03-03 (F0046) | no release returned (ungh 404, F0328); PyPI 1.3.0, 2024-06-03 (F0276) | PyPI audiocraft 9,695/month (F0276) | library for MusicGen, AudioGen, EnCodec | GH facebookresearch | Library row; the MusicGen weights are their own row. README: pip install -U audiocraft (F0401). |
| gpt-image | closed | proprietary API (hosted-only product per vendor page / arena listing: F0384, W0051) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | GPT-Image-2.5 Sunburst, Flare (W0051); GPT Image 2, 1.5 (W0011) | openai | AA T2I #1 Elo 1196 (W0011). |
| nano-banana | closed | proprietary API (hosted-only product per vendor page / arena listing: F0383, W0053) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | Nano Banana 2 (Gemini 3.1 Flash Image), Nano Banana 2 Lite, Nano Banana Pro (W0053, W0011) | google | AA T2I Elo 1123 (W0011). Brief lead "Imagen" not separately verified (parked). |
| midjourney | closed | proprietary service (hosted-only product per vendor page / arena listing: F0374, W0052) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | V8.1 alpha released 2026-04-14 (W0052); V8.0 alpha 2026-03-17 and V8.2 alpha per a search summary (W0024, not vendor-confirmed) | midjourney | Homepage 200 (F0374). Not in AA T2I top 25 as fetched (W0011); kept as the best-known closed image service, brief lead. |
| seedream | closed | proprietary API (hosted-only product per vendor page / arena listing: F0377, W0011) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | Seedream 4.0, 4.5, 5.0 Pro (W0011) | bytedance-seed-volcano-engine | AA T2I Elo 5.0 Pro 1078 (W0011). Vendor page redirected, not followed (W0057). |
| veo | closed | proprietary API (hosted-only product per vendor page / arena listing: F0381, W0048) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | Veo 3.1, 3.1 Fast, 3.1 Lite (W0048, W0012) | google | AA T2V Elo 3.1 1157 (W0012). |
| kling | closed | proprietary service/API (hosted-only product per vendor page / arena listing: F0380, W0059) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | Kling VIDEO 3.0, 3.0 Omni (W0059, W0012) | kuaishou | AA T2V Elo 3.0 1080p Pro 1164 (W0012). Kuaishou attribution via KlingAIResearch MIT notice (F0241). |
| seedance | closed | proprietary API (hosted-only product per vendor page / arena listing: F0385, W0056) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | Seedance 1.0 (vendor page, W0056); Dreamina Seedance 2.0 (W0012) | bytedance-seed-volcano-engine | AA T2V Elo 2.0 720p 1235 (W0012). |
| runway-gen | closed | proprietary service/API (hosted-only product per vendor page / arena listing: F0378, W0060) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | Gen-4.5 (W0060) | runway | Not in AA T2V top 25 as fetched (W0012); brief lead, vendor claims "world's best video model" (W0060). ADR-005 look recommended. |
| suno | closed | proprietary service (hosted-only product per vendor page / arena listing: F0375, W0054) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | v5.5, v6, v6-mini (W0054, W0023, W0032) | suno | AA vocal #1 Elo 1134, instrumental 1143 (W0032, W0033). |
| lyria | closed | proprietary API (hosted-only product per vendor page / arena listing: F0382, W0050) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | Lyria 2, 3 Pro, 3.5 (W0050, W0032) | google | AA vocal Elo 3.5 1045 (W0032). |
| meshy | closed | proprietary service (hosted-only product per vendor page / arena listing: F0379, W0061) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | Meshy 7 (W0061); Meshy 5 on Pixazo board (W0063) | meshy | 3D arena Elo Meshy 5 1280 per Pixazo (W0063). |
| tripo | closed | proprietary service (hosted-only product per vendor page / arena listing: W0063; homepage 403 F0376) | n/a | n/a | see notes | none: hosted, no download channel; AA Elo in notes | Tripo v3.1 (W0063) | vast-ai | Ranked #1 on Sloyd arena summary (W0063); vendor page 403 via WebFetch (W0062) and curl (F0376): bot block, not a finding. Same org as open TripoSG/TripoSR. |

### 6c. Source list

Every fetch and web call behind this sweep, all made on 2026-09-26 (UTC). Non-200 rows are failed attempts, kept for the audit trail.

| id | fetched (UTC) | status | url | label/excerpt |
|---|---|---|---|---|
| F0001 | 2026-09-26T20:01:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/black-forest-labs%2Fflux | ecosystems black-forest-labs/flux |
| F0002 | 2026-09-26T20:01:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/black-forest-labs%2Fflux2 | ecosystems black-forest-labs/flux2 |
| F0003 | 2026-09-26T20:01:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Stability-AI%2Fgenerative-models | ecosystems Stability-AI/generative-models |
| F0004 | 2026-09-26T20:01:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Stability-AI%2Fsd3.5 | ecosystems Stability-AI/sd3.5 |
| F0005 | 2026-09-26T20:01:22Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/QwenLM%2FQwen-Image | ecosystems QwenLM/Qwen-Image |
| F0006 | 2026-09-26T20:01:22Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/HiDream-ai%2FHiDream-I1 | ecosystems HiDream-ai/HiDream-I1 |
| F0007 | 2026-09-26T20:01:22Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/HiDream-ai%2FHiDream-O1-Image | ecosystems HiDream-ai/HiDream-O1-Image |
| F0008 | 2026-09-26T20:01:23Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVlabs%2FSana | ecosystems NVlabs/Sana |
| F0009 | 2026-09-26T20:01:23Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PixArt-alpha%2FPixArt-sigma | ecosystems PixArt-alpha/PixArt-sigma |
| F0010 | 2026-09-26T20:01:23Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Kwai-Kolors%2FKolors | ecosystems Kwai-Kolors/Kolors |
| F0011 | 2026-09-26T20:01:24Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Alpha-VLLM%2FLumina-Image-2.0 | ecosystems Alpha-VLLM/Lumina-Image-2.0 |
| F0012 | 2026-09-26T20:01:24Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuanImage-3.0 | ecosystems Tencent-Hunyuan/HunyuanImage-3.0 |
| F0013 | 2026-09-26T20:01:24Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuanImage-2.1 | ecosystems Tencent-Hunyuan/HunyuanImage-2.1 |
| F0014 | 2026-09-26T20:01:24Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tongyi-MAI%2FZ-Image | ecosystems Tongyi-MAI/Z-Image |
| F0015 | 2026-09-26T20:01:25Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bria-ai%2FFIBO | ecosystems bria-ai/FIBO |
| F0016 | 2026-09-26T20:01:25Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/zai-org%2FGLM-Image | ecosystems zai-org/GLM-Image |
| F0017 | 2026-09-26T20:01:25Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/VectorSpaceLab%2FOmniGen2 | ecosystems VectorSpaceLab/OmniGen2 |
| F0018 | 2026-09-26T20:01:26Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ByteDance-Seed%2FBagel | ecosystems ByteDance-Seed/Bagel |
| F0019 | 2026-09-26T20:01:26Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/FoundationVision%2FInfinity | ecosystems FoundationVision/Infinity |
| F0020 | 2026-09-26T20:01:26Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/deepseek-ai%2FJanus | ecosystems deepseek-ai/Janus |
| F0021 | 2026-09-26T20:01:27Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/meituan-longcat%2FLongCat-Image | ecosystems meituan-longcat/LongCat-Image |
| F0022 | 2026-09-26T20:01:27Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Wan-Video%2FWan2.1 | ecosystems Wan-Video/Wan2.1 |
| F0023 | 2026-09-26T20:01:27Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Wan-Video%2FWan2.2 | ecosystems Wan-Video/Wan2.2 |
| F0024 | 2026-09-26T20:01:27Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuanVideo | ecosystems Tencent-Hunyuan/HunyuanVideo |
| F0025 | 2026-09-26T20:01:28Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuanVideo-1.5 | ecosystems Tencent-Hunyuan/HunyuanVideo-1.5 |
| F0026 | 2026-09-26T20:01:28Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/zai-org%2FCogVideo | ecosystems zai-org/CogVideo |
| F0027 | 2026-09-26T20:01:28Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Lightricks%2FLTX-Video | ecosystems Lightricks/LTX-Video |
| F0028 | 2026-09-26T20:01:29Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Lightricks%2FLTX-2 | ecosystems Lightricks/LTX-2 |
| F0029 | 2026-09-26T20:01:29Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/genmoai%2Fmochi | ecosystems genmoai/mochi |
| F0030 | 2026-09-26T20:01:29Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/hpcaitech%2FOpen-Sora | ecosystems hpcaitech/Open-Sora |
| F0031 | 2026-09-26T20:01:30Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SandAI-org%2FMAGI-1 | ecosystems SandAI-org/MAGI-1 |
| F0032 | 2026-09-26T20:01:30Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SkyworkAI%2FSkyReels-V2 | ecosystems SkyworkAI/SkyReels-V2 |
| F0033 | 2026-09-26T20:01:30Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kandinskylab%2Fkandinsky-5 | ecosystems kandinskylab/kandinsky-5 |
| F0034 | 2026-09-26T20:01:30Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2FTRELLIS | ecosystems microsoft/TRELLIS |
| F0035 | 2026-09-26T20:01:31Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2FTRELLIS.2 | ecosystems microsoft/TRELLIS.2 |
| F0036 | 2026-09-26T20:01:31Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuan3D-2 | ecosystems Tencent-Hunyuan/Hunyuan3D-2 |
| F0037 | 2026-09-26T20:01:31Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuan3D-2.1 | ecosystems Tencent-Hunyuan/Hunyuan3D-2.1 |
| F0038 | 2026-09-26T20:01:32Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stepfun-ai%2FStep1X-3D | ecosystems stepfun-ai/Step1X-3D |
| F0039 | 2026-09-26T20:01:32Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/VAST-AI-Research%2FTripoSG | ecosystems VAST-AI-Research/TripoSG |
| F0040 | 2026-09-26T20:01:32Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/VAST-AI-Research%2FTripoSR | ecosystems VAST-AI-Research/TripoSR |
| F0041 | 2026-09-26T20:01:33Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Stability-AI%2Fstable-fast-3d | ecosystems Stability-AI/stable-fast-3d |
| F0042 | 2026-09-26T20:01:33Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Stability-AI%2Fstable-point-aware-3d | ecosystems Stability-AI/stable-point-aware-3d |
| F0043 | 2026-09-26T20:01:33Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/TencentARC%2FInstantMesh | ecosystems TencentARC/InstantMesh |
| F0044 | 2026-09-26T20:01:33Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Roblox%2Fcube | ecosystems Roblox/cube |
| F0045 | 2026-09-26T20:01:34Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Stability-AI%2Fstable-audio-tools | ecosystems Stability-AI/stable-audio-tools |
| F0046 | 2026-09-26T20:01:34Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Faudiocraft | ecosystems facebookresearch/audiocraft |
| F0047 | 2026-09-26T20:01:34Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ace-step%2FACE-Step | ecosystems ace-step/ACE-Step |
| F0048 | 2026-09-26T20:01:35Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ace-step%2FACE-Step-1.5 | ecosystems ace-step/ACE-Step-1.5 |
| F0049 | 2026-09-26T20:01:35Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/multimodal-art-projection%2FYuE | ecosystems multimodal-art-projection/YuE |
| F0050 | 2026-09-26T20:01:37Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/HeartMuLa%2Fheartlib | ecosystems HeartMuLa/heartlib |
| F0051 | 2026-09-26T20:01:37Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/tencent-ailab%2FSongGeneration | ecosystems tencent-ailab/SongGeneration |
| F0052 | 2026-09-26T20:01:38Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ASLP-lab%2FDiffRhythm | ecosystems ASLP-lab/DiffRhythm |
| F0053 | 2026-09-26T20:01:39Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/hkchengrex%2FMMAudio | ecosystems hkchengrex/MMAudio |
| F0054 | 2026-09-26T20:01:37Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/FunAudioLLM%2FThinkSound | ecosystems FunAudioLLM/ThinkSound |
| F0055 | 2026-09-26T20:01:39Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuanVideo-Foley | ecosystems Tencent-Hunyuan/HunyuanVideo-Foley |
| F0056 | 2026-09-26T20:01:37Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/comfyanonymous%2FComfyUI | ecosystems comfyanonymous/ComfyUI |
| F0057 | 2026-09-26T20:01:39Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/AUTOMATIC1111%2Fstable-diffusion-webui | ecosystems AUTOMATIC1111/stable-diffusion-webui |
| F0058 | 2026-09-26T20:01:40Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lllyasviel%2Fstable-diffusion-webui-forge | ecosystems lllyasviel/stable-diffusion-webui-forge |
| F0059 | 2026-09-26T20:01:39Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/invoke-ai%2FInvokeAI | ecosystems invoke-ai/InvokeAI |
| F0060 | 2026-09-26T20:01:40Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lllyasviel%2FFooocus | ecosystems lllyasviel/Fooocus |
| F0061 | 2026-09-26T20:01:39Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/vladmandic%2Fsdnext | ecosystems vladmandic/sdnext |
| F0062 | 2026-09-26T20:01:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/mcmonkeyprojects%2FSwarmUI | ecosystems mcmonkeyprojects/SwarmUI |
| F0063 | 2026-09-26T20:01:40Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kohya-ss%2Fsd-scripts | ecosystems kohya-ss/sd-scripts |
| F0064 | 2026-09-26T20:01:40Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kohya-ss%2Fmusubi-tuner | ecosystems kohya-ss/musubi-tuner |
| F0065 | 2026-09-26T20:01:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Acly%2Fkrita-ai-diffusion | ecosystems Acly/krita-ai-diffusion |
| F0066 | 2026-09-26T20:01:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/deepbeepmeep%2FWan2GP | ecosystems deepbeepmeep/Wan2GP |
| F0067 | 2026-09-26T20:01:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/leejet%2Fstable-diffusion.cpp | ecosystems leejet/stable-diffusion.cpp |
| F0068 | 2026-09-26T20:01:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lllyasviel%2FFramePack | ecosystems lllyasviel/FramePack |
| F0069 | 2026-09-26T20:01:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/modelscope%2FDiffSynth-Studio | ecosystems modelscope/DiffSynth-Studio |
| F0070 | 2026-09-26T20:01:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/xdit-project%2FxDiT | ecosystems xdit-project/xDiT |
| F0071 | 2026-09-26T20:01:42Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nunchaku-tech%2Fnunchaku | ecosystems nunchaku-tech/nunchaku |
| F0072 | 2026-09-26T20:01:42Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/hao-ai-lab%2FFastVideo | ecosystems hao-ai-lab/FastVideo |
| F0073 | 2026-09-26T20:01:42Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ModelTC%2FLightX2V | ecosystems ModelTC/LightX2V |
| F0074 | 2026-09-26T20:01:43Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/LykosAI%2FStabilityMatrix | ecosystems LykosAI/StabilityMatrix |
| F0075 | 2026-09-26T20:01:43Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lllyasviel%2FControlNet | ecosystems lllyasviel/ControlNet |
| F0076 | 2026-09-26T20:01:43Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Comfy-Org%2FComfyUI | ecosystems Comfy-Org/ComfyUI |
| F0077 | 2026-09-26T20:02:00Z | 200 | https://huggingface.co/api/models?author=black-forest-labs&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author black-forest-labs |
| F0078 | 2026-09-26T20:02:00Z | 200 | https://huggingface.co/api/models?author=stabilityai&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author stabilityai |
| F0079 | 2026-09-26T20:02:01Z | 200 | https://huggingface.co/api/models?author=Qwen&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author Qwen |
| F0080 | 2026-09-26T20:02:01Z | 200 | https://huggingface.co/api/models?author=HiDream-ai&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author HiDream-ai |
| F0081 | 2026-09-26T20:02:01Z | 200 | https://huggingface.co/api/models?author=Efficient-Large-Model&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author Efficient-Large-Model |
| F0082 | 2026-09-26T20:02:02Z | 200 | https://huggingface.co/api/models?author=PixArt-alpha&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author PixArt-alpha |
| F0083 | 2026-09-26T20:02:02Z | 200 | https://huggingface.co/api/models?author=Kwai-Kolors&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author Kwai-Kolors |
| F0084 | 2026-09-26T20:02:03Z | 200 | https://huggingface.co/api/models?author=Alpha-VLLM&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author Alpha-VLLM |
| F0085 | 2026-09-26T20:02:03Z | 200 | https://huggingface.co/api/models?author=tencent&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author tencent |
| F0086 | 2026-09-26T20:02:03Z | 200 | https://huggingface.co/api/models?author=Tongyi-MAI&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author Tongyi-MAI |
| F0087 | 2026-09-26T20:02:04Z | 200 | https://huggingface.co/api/models?author=briaai&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author briaai |
| F0088 | 2026-09-26T20:02:04Z | 200 | https://huggingface.co/api/models?author=zai-org&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author zai-org |
| F0089 | 2026-09-26T20:02:05Z | 200 | https://huggingface.co/api/models?author=OmniGen2&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author OmniGen2 |
| F0090 | 2026-09-26T20:02:05Z | 200 | https://huggingface.co/api/models?author=ByteDance-Seed&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author ByteDance-Seed |
| F0091 | 2026-09-26T20:02:05Z | 200 | https://huggingface.co/api/models?author=deepseek-ai&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author deepseek-ai |
| F0092 | 2026-09-26T20:02:06Z | 200 | https://huggingface.co/api/models?author=meituan-longcat&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author meituan-longcat |
| F0093 | 2026-09-26T20:02:06Z | 200 | https://huggingface.co/api/models?author=Wan-AI&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author Wan-AI |
| F0094 | 2026-09-26T20:02:07Z | 200 | https://huggingface.co/api/models?author=Lightricks&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author Lightricks |
| F0095 | 2026-09-26T20:02:07Z | 200 | https://huggingface.co/api/models?author=genmo&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author genmo |
| F0096 | 2026-09-26T20:02:07Z | 200 | https://huggingface.co/api/models?author=hpcai-tech&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author hpcai-tech |
| F0097 | 2026-09-26T20:02:08Z | 200 | https://huggingface.co/api/models?author=sand-ai&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author sand-ai |
| F0098 | 2026-09-26T20:02:08Z | 200 | https://huggingface.co/api/models?author=Skywork&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author Skywork |
| F0099 | 2026-09-26T20:02:09Z | 200 | https://huggingface.co/api/models?author=kandinskylab&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author kandinskylab |
| F0100 | 2026-09-26T20:02:09Z | 200 | https://huggingface.co/api/models?author=microsoft&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author microsoft |
| F0101 | 2026-09-26T20:02:09Z | 200 | https://huggingface.co/api/models?author=stepfun-ai&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author stepfun-ai |
| F0102 | 2026-09-26T20:02:10Z | 200 | https://huggingface.co/api/models?author=VAST-AI&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author VAST-AI |
| F0103 | 2026-09-26T20:02:10Z | 200 | https://huggingface.co/api/models?author=Roblox&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author Roblox |
| F0104 | 2026-09-26T20:02:11Z | 200 | https://huggingface.co/api/models?author=facebook&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author facebook |
| F0105 | 2026-09-26T20:02:11Z | 200 | https://huggingface.co/api/models?author=ACE-Step&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author ACE-Step |
| F0106 | 2026-09-26T20:02:11Z | 200 | https://huggingface.co/api/models?author=m-a-p&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author m-a-p |
| F0107 | 2026-09-26T20:02:12Z | 200 | https://huggingface.co/api/models?author=HeartMuLa&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author HeartMuLa |
| F0108 | 2026-09-26T20:02:12Z | 200 | https://huggingface.co/api/models?author=MiniMaxAI&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author MiniMaxAI |
| F0109 | 2026-09-26T20:02:13Z | 200 | https://huggingface.co/api/models?author=nvidia&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author nvidia |
| F0110 | 2026-09-26T20:02:13Z | 200 | https://huggingface.co/api/models?author=ideogram&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author ideogram |
| F0111 | 2026-09-26T20:02:13Z | 200 | https://huggingface.co/api/models?author=baidu&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author baidu |
| F0112 | 2026-09-26T20:02:14Z | 200 | https://huggingface.co/api/models?author=inclusionAI&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author inclusionAI |
| F0113 | 2026-09-26T20:02:14Z | 200 | https://huggingface.co/api/models?author=ByteDance&sort=downloads&limit=100&expand[]=downloads&expand[]=pipeline_tag&expand[]=cardData&expand[]=likes&expand[]=lastModified | hf author ByteDance |
| F0114 | 2026-09-26T20:03:02Z | 200 | https://huggingface.co/api/models/Qwen/Qwen-Image?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Qwen/Qwen-Image |
| F0115 | 2026-09-26T20:03:03Z | 200 | https://huggingface.co/api/models/Qwen/Qwen-Image-2512?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Qwen/Qwen-Image-2512 |
| F0116 | 2026-09-26T20:03:03Z | 200 | https://huggingface.co/api/models/Qwen/Qwen-Image-2.1?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Qwen/Qwen-Image-2.1 |
| F0117 | 2026-09-26T20:03:03Z | 200 | https://huggingface.co/api/models/Qwen/Qwen-Image-Edit-2511?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Qwen/Qwen-Image-Edit-2511 |
| F0118 | 2026-09-26T20:03:03Z | 200 | https://huggingface.co/api/models/HiDream-ai/HiDream-I1-Full?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model HiDream-ai/HiDream-I1-Full |
| F0119 | 2026-09-26T20:03:04Z | 200 | https://huggingface.co/api/models/HiDream-ai/HiDream-O1-Image?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model HiDream-ai/HiDream-O1-Image |
| F0120 | 2026-09-26T20:03:04Z | 200 | https://huggingface.co/api/models/Efficient-Large-Model/Sana_1600M_1024px_diffusers?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Efficient-Large-Model/Sana_1600M_1024px_diffusers |
| F0121 | 2026-09-26T20:03:04Z | 200 | https://huggingface.co/api/models/Efficient-Large-Model/SANA1.5_4.8B_1024px_diffusers?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Efficient-Large-Model/SANA1.5_4.8B_1024px_diffusers |
| F0122 | 2026-09-26T20:03:05Z | 200 | https://huggingface.co/api/models/tencent/HunyuanVideo?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model tencent/HunyuanVideo |
| F0123 | 2026-09-26T20:03:05Z | 200 | https://huggingface.co/api/models/tencent/HunyuanVideo-1.5?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model tencent/HunyuanVideo-1.5 |
| F0124 | 2026-09-26T20:03:05Z | 200 | https://huggingface.co/api/models/tencent/HunyuanImage-2.1?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model tencent/HunyuanImage-2.1 |
| F0125 | 2026-09-26T20:03:06Z | 200 | https://huggingface.co/api/models/tencent/HunyuanVideo-Foley?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model tencent/HunyuanVideo-Foley |
| F0126 | 2026-09-26T20:03:06Z | 200 | https://huggingface.co/api/models/sand-ai/MAGI-1?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model sand-ai/MAGI-1 |
| F0127 | 2026-09-26T20:03:06Z | 200 | https://huggingface.co/api/models/sand-ai/MAGI-2-preview?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model sand-ai/MAGI-2-preview |
| F0128 | 2026-09-26T20:03:06Z | 200 | https://huggingface.co/api/models/Roblox/cube3d-v0.1?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Roblox/cube3d-v0.1 |
| F0129 | 2026-09-26T20:03:07Z | 200 | https://huggingface.co/api/models/stepfun-ai/Step1X-3D?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stepfun-ai/Step1X-3D |
| F0130 | 2026-09-26T20:03:07Z | 200 | https://huggingface.co/api/models/stabilityai/stable-audio-open-1.0?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stabilityai/stable-audio-open-1.0 |
| F0131 | 2026-09-26T20:03:07Z | 200 | https://huggingface.co/api/models/stabilityai/stable-fast-3d?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stabilityai/stable-fast-3d |
| F0132 | 2026-09-26T20:03:08Z | 200 | https://huggingface.co/api/models/hkchengrex/MMAudio?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model hkchengrex/MMAudio |
| F0133 | 2026-09-26T20:03:08Z | 200 | https://huggingface.co/api/models/m-a-p/YuE-s1-7B-anneal-en-cot?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model m-a-p/YuE-s1-7B-anneal-en-cot |
| F0134 | 2026-09-26T20:03:08Z | 401 | https://huggingface.co/api/models/tencent/SongGeneration?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model tencent/SongGeneration |
| F0135 | 2026-09-26T20:03:09Z | 200 | https://huggingface.co/api/models/ASLP-lab/DiffRhythm-1_2?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model ASLP-lab/DiffRhythm-1_2 |
| F0136 | 2026-09-26T20:03:09Z | 200 | https://huggingface.co/api/models/MiniMaxAI/MiniMax-H3?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model MiniMaxAI/MiniMax-H3 |
| F0137 | 2026-09-26T20:03:09Z | 200 | https://huggingface.co/api/models/ideogram-ai/ideogram-4-fp8?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model ideogram-ai/ideogram-4-fp8 |
| F0138 | 2026-09-26T20:03:09Z | 200 | https://huggingface.co/api/models/ideogram-ai/ideogram-4-nf4?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model ideogram-ai/ideogram-4-nf4 |
| F0139 | 2026-09-26T20:03:10Z | 401 | https://huggingface.co/api/models/microsoft/Mage-Flow?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model microsoft/Mage-Flow |
| F0140 | 2026-09-26T20:03:10Z | 200 | https://huggingface.co/api/models/Alpha-VLLM/Lumina-Image-2.0?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Alpha-VLLM/Lumina-Image-2.0 |
| F0141 | 2026-09-26T20:03:10Z | 200 | https://huggingface.co/api/models/Kwai-Kolors/Kolors?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Kwai-Kolors/Kolors |
| F0142 | 2026-09-26T20:03:11Z | 200 | https://huggingface.co/api/models/kandinskylab/Kandinsky-5.0-T2V-Pro-sft-5s?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model kandinskylab/Kandinsky-5.0-T2V-Pro-sft-5s |
| F0143 | 2026-09-26T20:03:11Z | 200 | https://huggingface.co/api/models/ByteDance-Seed/BAGEL-7B-MoT?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model ByteDance-Seed/BAGEL-7B-MoT |
| F0144 | 2026-09-26T20:03:11Z | 200 | https://huggingface.co/api/models/FoundationVision/Infinity?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model FoundationVision/Infinity |
| F0145 | 2026-09-26T20:03:12Z | 200 | https://huggingface.co/api/models/inclusionAI/Ming-Image-0.1-Design?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model inclusionAI/Ming-Image-0.1-Design |
| F0146 | 2026-09-26T20:03:12Z | 200 | https://huggingface.co/api/models/HeartMuLa/HeartMuLa-oss-3B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model HeartMuLa/HeartMuLa-oss-3B |
| F0147 | 2026-09-26T20:03:12Z | 200 | https://huggingface.co/api/models/black-forest-labs/FLUX.2-dev?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model black-forest-labs/FLUX.2-dev |
| F0148 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models/stabilityai/stable-diffusion-3.5-large?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stabilityai/stable-diffusion-3.5-large |
| F0149 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models/Wan-AI/Wan2.2-T2V-A14B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Wan-AI/Wan2.2-T2V-A14B |
| F0150 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models/Lightricks/LTX-2.5?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Lightricks/LTX-2.5 |
| F0151 | 2026-09-26T20:03:13Z | 200 | https://huggingface.co/api/models/microsoft/TRELLIS.2-4B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model microsoft/TRELLIS.2-4B |
| F0152 | 2026-09-26T20:03:14Z | 200 | https://huggingface.co/api/models/tencent/Hunyuan3D-2.1?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model tencent/Hunyuan3D-2.1 |
| F0153 | 2026-09-26T20:03:14Z | 200 | https://huggingface.co/api/models/facebook/musicgen-medium?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model facebook/musicgen-medium |
| F0154 | 2026-09-26T20:03:14Z | 200 | https://huggingface.co/api/models/ACE-Step/Ace-Step1.5?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model ACE-Step/Ace-Step1.5 |
| F0155 | 2026-09-26T20:03:15Z | 200 | https://huggingface.co/api/models/genmo/mochi-1-preview?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model genmo/mochi-1-preview |
| F0156 | 2026-09-26T20:03:15Z | 200 | https://huggingface.co/api/models/zai-org/CogVideoX-5b?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model zai-org/CogVideoX-5b |
| F0157 | 2026-09-26T20:03:15Z | 200 | https://huggingface.co/api/models/hpcai-tech/Open-Sora-v2?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model hpcai-tech/Open-Sora-v2 |
| F0158 | 2026-09-26T20:03:16Z | 200 | https://huggingface.co/api/models/Tongyi-MAI/Z-Image-Turbo?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Tongyi-MAI/Z-Image-Turbo |
| F0159 | 2026-09-26T20:03:16Z | 200 | https://huggingface.co/api/models/VAST-AI/TripoSG?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model VAST-AI/TripoSG |
| F0160 | 2026-09-26T20:03:16Z | 200 | https://huggingface.co/api/models/stabilityai/TripoSR?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stabilityai/TripoSR |
| F0161 | 2026-09-26T20:03:16Z | 200 | https://huggingface.co/api/models/Skywork/SkyReels-V2-T2V-14B-720P?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Skywork/SkyReels-V2-T2V-14B-720P |
| F0162 | 2026-09-26T20:03:17Z | 200 | https://huggingface.co/api/models/Wan-AI/Wan2.2-Animate-14B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Wan-AI/Wan2.2-Animate-14B |
| F0163 | 2026-09-26T20:03:17Z | 200 | https://huggingface.co/api/models/briaai/FIBO?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model briaai/FIBO |
| F0164 | 2026-09-26T20:03:17Z | 200 | https://huggingface.co/api/models/baidu/ERNIE-Image?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model baidu/ERNIE-Image |
| F0165 | 2026-09-26T20:03:18Z | 200 | https://huggingface.co/api/models/zai-org/GLM-Image?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model zai-org/GLM-Image |
| F0166 | 2026-09-26T20:03:34Z | 401 | https://huggingface.co/black-forest-labs/FLUX.2-dev/raw/main/LICENSE.txt | license FLUX.2-dev |
| F0167 | 2026-09-26T20:03:35Z | 401 | https://huggingface.co/stabilityai/stable-diffusion-3.5-large/raw/main/LICENSE.md | license SD3.5 community |
| F0168 | 2026-09-26T20:03:34Z | 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo-1.5/HEAD/LICENSE | license HunyuanVideo-1.5 |
| F0169 | 2026-09-26T20:03:34Z | 200 | https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/raw/main/README.md | card FLUX.2-klein-4B |
| F0170 | 2026-09-26T20:03:34Z | 200 | https://huggingface.co/Qwen/Qwen-Image-2.1/raw/main/LICENSE | license Qwen-Image-2.1 |
| F0171 | 2026-09-26T20:03:34Z | 200 | https://huggingface.co/zai-org/CogVideoX-5b/raw/main/LICENSE | license CogVideoX-5b |
| F0172 | 2026-09-26T20:03:34Z | 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/HEAD/LICENSE | license Hunyuan3D-2.1 |
| F0173 | 2026-09-26T20:03:34Z | 200 | https://raw.githubusercontent.com/Roblox/cube/HEAD/LICENSE | license Roblox cube |
| F0174 | 2026-09-26T20:03:34Z | 200 | https://huggingface.co/Skywork/SkyReels-V2-T2V-14B-720P/raw/main/LICENSE | license SkyReels |
| F0175 | 2026-09-26T20:03:35Z | 401 | https://huggingface.co/ideogram-ai/ideogram-4-fp8/raw/main/LICENSE.md | license ideogram-4 |
| F0176 | 2026-09-26T20:03:35Z | 200 | https://raw.githubusercontent.com/Comfy-Org/ComfyUI/HEAD/LICENSE | license ComfyUI |
| F0177 | 2026-09-26T20:03:34Z | 200 | https://huggingface.co/MiniMaxAI/MiniMax-Music3/raw/main/README.md | card MiniMax-Music3 |
| F0178 | 2026-09-26T20:03:34Z | 401 | https://huggingface.co/briaai/FIBO/raw/main/README.md | card FIBO |
| F0179 | 2026-09-26T20:03:35Z | 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanImage-3.0/HEAD/LICENSE | license HunyuanImage-3.0 |
| F0180 | 2026-09-26T20:03:35Z | 200 | https://raw.githubusercontent.com/Lightricks/LTX-2/HEAD/LICENSE-2_x | license LTX-2.x |
| F0181 | 2026-09-26T20:03:34Z | 200 | https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/LICENSE | license MiniMax-H3 |
| F0182 | 2026-09-26T20:03:34Z | 404 | https://raw.githubusercontent.com/kohya-ss/musubi-tuner/HEAD/LICENSE | license musubi-tuner |
| F0183 | 2026-09-26T20:03:34Z | 401 | https://huggingface.co/stabilityai/stable-audio-3-medium/raw/main/README.md | card stable-audio-3-medium |
| F0184 | 2026-09-26T20:03:34Z | 401 | https://huggingface.co/stabilityai/stable-audio-open-1.0/raw/main/LICENSE.md | license stable-audio-open |
| F0185 | 2026-09-26T20:03:35Z | 200 | https://raw.githubusercontent.com/deepbeepmeep/Wan2GP/HEAD/LICENSE.txt | license Wan2GP |
| F0186 | 2026-09-26T20:03:35Z | 404 | https://raw.githubusercontent.com/tencent-ailab/SongGeneration/HEAD/LICENSE | license SongGeneration |
| F0187 | 2026-09-26T20:03:34Z | 200 | https://huggingface.co/m-a-p/YuE2-3B/raw/main/README.md | card YuE2-3B |
| F0188 | 2026-09-26T20:03:52Z | 200 | https://huggingface.co/MiniMaxAI/MiniMax-Music3/raw/main/LICENSE | license MiniMax-Music3 |
| F0189 | 2026-09-26T20:03:53Z | 200 | https://huggingface.co/MiniMaxAI/MiniMax-Music3?expand=1 | x |
| F0190 | 2026-09-26T20:03:53Z | 200 | https://huggingface.co/api/models/MiniMaxAI/MiniMax-Music3?expand[]=downloads&expand[]=cardData&expand[]=lastModified&expand[]=createdAt | hf model MiniMaxAI/MiniMax-Music3 |
| F0191 | 2026-09-26T20:05:51Z | 200 | https://huggingface.co/api/models?search=Wan3&sort=downloads&limit=20 | hf search Wan3 |
| F0192 | 2026-09-26T20:05:51Z | 200 | https://huggingface.co/api/models?author=Wan-AI&sort=createdAt&limit=10&expand[]=createdAt&expand[]=downloads | hf Wan-AI newest |
| F0193 | 2026-09-26T20:07:03Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/calesthio%2FOpenMontage | ecosystems calesthio/OpenMontage |
| F0194 | 2026-09-26T20:07:03Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Anil-matcha%2FOpen-Generative-AI | ecosystems Anil-matcha/Open-Generative-AI |
| F0195 | 2026-09-26T20:07:03Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ATH-MaaS%2FPixelle-Video | ecosystems ATH-MaaS/Pixelle-Video |
| F0196 | 2026-09-26T20:07:03Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/KlingAIResearch%2FLivePortrait | ecosystems KlingAIResearch/LivePortrait |
| F0197 | 2026-09-26T20:07:04Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bytedance%2FLatentSync | ecosystems bytedance/LatentSync |
| F0198 | 2026-09-26T20:07:04Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/vllm-project%2Fvllm-omni | ecosystems vllm-project/vllm-omni |
| F0199 | 2026-09-26T20:07:04Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/QwenAudio%2FThinkSound | ecosystems QwenAudio/ThinkSound |
| F0200 | 2026-09-26T20:07:04Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bghira%2FSimpleTuner | ecosystems bghira/SimpleTuner |
| F0201 | 2026-09-26T20:07:05Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/tdrussell%2Fdiffusion-pipe | ecosystems tdrussell/diffusion-pipe |
| F0202 | 2026-09-26T20:07:05Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SandAI-org%2FMAGI-2-preview | ecosystems SandAI-org/MAGI-2-preview |
| F0203 | 2026-09-26T20:07:05Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Sanster%2FIOPaint | ecosystems Sanster/IOPaint |
| F0204 | 2026-09-26T20:07:06Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/divamgupta%2Fdiffusionbee-stable-diffusion-ui | ecosystems divamgupta/diffusionbee-stable-diffusion-ui |
| F0205 | 2026-09-26T20:07:06Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Panchovix%2Fstable-diffusion-webui-reForge | ecosystems Panchovix/stable-diffusion-webui-reForge |
| F0206 | 2026-09-26T20:07:06Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/easydiffusion%2Feasydiffusion | ecosystems easydiffusion/easydiffusion |
| F0207 | 2026-09-26T20:07:07Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PKU-YuanGroup%2FHelios | ecosystems PKU-YuanGroup/Helios |
| F0208 | 2026-09-26T20:07:07Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-mmlab%2FAmphion | ecosystems open-mmlab/Amphion |
| F0209 | 2026-09-26T20:07:07Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Nerogar%2FOneTrainer | ecosystems Nerogar/OneTrainer |
| F0210 | 2026-09-26T20:07:08Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ostris%2Fai-toolkit | ecosystems ostris/ai-toolkit |
| F0211 | 2026-09-26T20:07:08Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/huggingface%2Fdiffusers | ecosystems huggingface/diffusers |
| F0212 | 2026-09-26T20:07:17Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stepfun-ai%2FStep-Video-T2V | ecosystems stepfun-ai/Step-Video-T2V |
| F0213 | 2026-09-26T20:07:08Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/aigc-apps%2FVideoX-Fun | ecosystems aigc-apps/VideoX-Fun |
| F0214 | 2026-09-26T20:07:09Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/FoundationVision%2FWaver | ecosystems FoundationVision/Waver |
| F0215 | 2026-09-26T20:07:09Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-mmlab%2FFoleyCrafter | ecosystems open-mmlab/FoleyCrafter |
| F0216 | 2026-09-26T20:07:09Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fsam-3d-objects | ecosystems facebookresearch/sam-3d-objects |
| F0217 | 2026-09-26T20:07:10Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/wgsxm%2FPartCrafter | ecosystems wgsxm/PartCrafter |
| F0218 | 2026-09-26T20:07:10Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nunchaku-ai%2Fnunchaku | ecosystems nunchaku-ai/nunchaku |
| F0219 | 2026-09-26T20:07:10Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/mit-han-lab%2Fnunchaku | ecosystems mit-han-lab/nunchaku |
| F0220 | 2026-09-26T20:07:11Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Haoming02%2Fsd-webui-forge-classic | ecosystems Haoming02/sd-webui-forge-classic |
| F0221 | 2026-09-26T20:07:11Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/MiniMax-AI%2FMiniMax-H3 | ecosystems MiniMax-AI/MiniMax-H3 |
| F0222 | 2026-09-26T20:07:11Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ideogram-ai%2Fideogram-4 | ecosystems ideogram-ai/ideogram-4 |
| F0223 | 2026-09-26T20:07:12Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/carson-katri%2Fdream-textures | ecosystems carson-katri/dream-textures |
| F0224 | 2026-09-26T20:07:12Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/img2threejs%2Fimg2threejs | ecosystems img2threejs/img2threejs |
| F0225 | 2026-09-26T20:07:12Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Stability-AI%2FStableStudio | ecosystems Stability-AI/StableStudio |
| F0226 | 2026-09-26T20:07:12Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ltdrdata%2FComfyUI-Manager | ecosystems ltdrdata/ComfyUI-Manager |
| F0227 | 2026-09-26T20:07:12Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuanImage-3.0 | ecosystems Tencent-Hunyuan/HunyuanImage-3.0 |
| F0228 | 2026-09-26T20:07:13Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lodestones%2Fflow | ecosystems lodestones/flow |
| F0229 | 2026-09-26T20:07:41Z | 200 | https://ungh.cc/repos/nunchaku-ai/nunchaku | ungh nunchaku-ai/nunchaku |
| F0230 | 2026-09-26T20:07:42Z | 200 | https://ungh.cc/repos/ideogram-oss/ideogram4 | ungh ideogram-oss/ideogram4 |
| F0231 | 2026-09-26T20:07:49Z | 000000 | https://ungh.cc/repos/comfyanonymous/ComfyUI | ungh comfyanonymous/ComfyUI |
| F0232 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/QwenAudio/ThinkSound/HEAD/LICENSE | license QwenAudio/ThinkSound (LICENSE) |
| F0233 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/ideogram-oss/ideogram4/HEAD/LICENSE | license ideogram-oss/ideogram4 (LICENSE) |
| F0234 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/Stability-AI/stable-fast-3d/HEAD/LICENSE | license Stability-AI/stable-fast-3d (LICENSE) |
| F0235 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/kohya-ss/musubi-tuner/HEAD/LICENSE | license kohya-ss/musubi-tuner (LICENSE) |
| F0236 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo/HEAD/LICENSE | license Tencent-Hunyuan/HunyuanVideo (LICENSE) |
| F0237 | 2026-09-26T20:07:58Z | 200 | https://raw.githubusercontent.com/easydiffusion/easydiffusion/HEAD/LICENSE | license easydiffusion/easydiffusion (LICENSE) |
| F0238 | 2026-09-26T20:07:58Z | 200 | https://raw.githubusercontent.com/Bria-AI/FIBO/HEAD/LICENSE | license Bria-AI/FIBO (LICENSE) |
| F0239 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/nunchux-ai/nunchaku/HEAD/LICENSE | license nunchux-ai/nunchaku (LICENSE) |
| F0240 | 2026-09-26T20:07:58Z | 200 | https://raw.githubusercontent.com/Lightricks/LTX-Video/HEAD/LICENSE | license Lightricks/LTX-Video (LICENSE) |
| F0241 | 2026-09-26T20:07:58Z | 200 | https://raw.githubusercontent.com/KlingAIResearch/LivePortrait/HEAD/LICENSE | license KlingAIResearch/LivePortrait (LICENSE) |
| F0242 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/black-forest-labs/flux2/HEAD/LICENSE | license black-forest-labs/flux2 (LICENSE) |
| F0243 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/HEAD/LICENSE | license MiniMax-AI/MiniMax-H3 (LICENSE) |
| F0244 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/SkyworkAI/SkyReels-V2/HEAD/LICENSE | license SkyworkAI/SkyReels-V2 (LICENSE) |
| F0245 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/FoundationVision/Waver/HEAD/LICENSE | license FoundationVision/Waver (LICENSE) |
| F0246 | 2026-09-26T20:07:58Z | 200 | https://raw.githubusercontent.com/facebookresearch/sam-3d-objects/HEAD/LICENSE | license facebookresearch/sam-3d-objects (LICENSE) |
| F0247 | 2026-09-26T20:07:58Z | 200 | https://raw.githubusercontent.com/Stability-AI/stable-fast-3d/HEAD/LICENSE.md | license Stability-AI/stable-fast-3d (LICENSE.md) |
| F0248 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/kohya-ss/musubi-tuner/HEAD/LICENSE.md | license kohya-ss/musubi-tuner (LICENSE.md) |
| F0249 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/QwenAudio/ThinkSound/HEAD/LICENSE.md | license QwenAudio/ThinkSound (LICENSE.md) |
| F0250 | 2026-09-26T20:07:58Z | 200 | https://raw.githubusercontent.com/ideogram-oss/ideogram4/HEAD/LICENSE.md | license ideogram-oss/ideogram4 (LICENSE.md) |
| F0251 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/FoundationVision/Waver/HEAD/LICENSE.md | license FoundationVision/Waver (LICENSE.md) |
| F0252 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo/HEAD/LICENSE.md | license Tencent-Hunyuan/HunyuanVideo (LICENSE.md) |
| F0253 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/HEAD/LICENSE.md | license MiniMax-AI/MiniMax-H3 (LICENSE.md) |
| F0254 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/nunchux-ai/nunchaku/HEAD/LICENSE.md | license nunchux-ai/nunchaku (LICENSE.md) |
| F0255 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/SkyworkAI/SkyReels-V2/HEAD/LICENSE.md | license SkyworkAI/SkyReels-V2 (LICENSE.md) |
| F0256 | 2026-09-26T20:07:58Z | 200 | https://raw.githubusercontent.com/black-forest-labs/flux2/HEAD/LICENSE.md | license black-forest-labs/flux2 (LICENSE.md) |
| F0257 | 2026-09-26T20:07:59Z | 404 | https://raw.githubusercontent.com/kohya-ss/musubi-tuner/HEAD/LICENSE.txt | license kohya-ss/musubi-tuner (LICENSE.txt) |
| F0258 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/QwenAudio/ThinkSound/HEAD/LICENSE.txt | license QwenAudio/ThinkSound (LICENSE.txt) |
| F0259 | 2026-09-26T20:07:58Z | 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo/HEAD/LICENSE.txt | license Tencent-Hunyuan/HunyuanVideo (LICENSE.txt) |
| F0260 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/nunchux-ai/nunchaku/HEAD/LICENSE.txt | license nunchux-ai/nunchaku (LICENSE.txt) |
| F0261 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/FoundationVision/Waver/HEAD/LICENSE.txt | license FoundationVision/Waver (LICENSE.txt) |
| F0262 | 2026-09-26T20:07:58Z | 404 | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/HEAD/LICENSE.txt | license MiniMax-AI/MiniMax-H3 (LICENSE.txt) |
| F0263 | 2026-09-26T20:07:59Z | 404 | https://raw.githubusercontent.com/QwenAudio/ThinkSound/HEAD/COPYING | license QwenAudio/ThinkSound (COPYING) |
| F0264 | 2026-09-26T20:07:59Z | 404 | https://raw.githubusercontent.com/nunchux-ai/nunchaku/HEAD/COPYING | license nunchux-ai/nunchaku (COPYING) |
| F0265 | 2026-09-26T20:07:59Z | 404 | https://raw.githubusercontent.com/FoundationVision/Waver/HEAD/COPYING | license FoundationVision/Waver (COPYING) |
| F0266 | 2026-09-26T20:07:59Z | 404 | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/HEAD/COPYING | license MiniMax-AI/MiniMax-H3 (COPYING) |
| F0267 | 2026-09-26T20:07:59Z | 200 | https://raw.githubusercontent.com/SkyworkAI/SkyReels-V2/HEAD/LICENSE.txt | license SkyworkAI/SkyReels-V2 (LICENSE.txt) |
| F0268 | 2026-09-26T20:07:59Z | 404 | https://raw.githubusercontent.com/kohya-ss/musubi-tuner/HEAD/COPYING | license kohya-ss/musubi-tuner (COPYING) |
| F0269 | 2026-09-26T20:08:11Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nunchux-ai%2Fnunchaku | ecosystems nunchux-ai/nunchaku |
| F0270 | 2026-09-26T20:08:12Z | 200 | https://raw.githubusercontent.com/QwenAudio/ThinkSound/HEAD/README.md | readme QwenAudio/ThinkSound |
| F0271 | 2026-09-26T20:08:12Z | 200 | https://raw.githubusercontent.com/kohya-ss/musubi-tuner/HEAD/README.md | readme kohya-ss/musubi-tuner |
| F0272 | 2026-09-26T20:08:12Z | 200 | https://raw.githubusercontent.com/FoundationVision/Waver/HEAD/README.md | readme FoundationVision/Waver |
| F0273 | 2026-09-26T20:08:12Z | 200 | https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/HEAD/README.md | readme MiniMax-AI/MiniMax-H3 |
| F0274 | 2026-09-26T20:08:11Z | 200 | https://raw.githubusercontent.com/nunchux-ai/nunchaku/HEAD/README.md | readme nunchux-ai/nunchaku |
| F0275 | 2026-09-26T20:08:25Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/invokeai | pypi-eco invokeai |
| F0276 | 2026-09-26T20:08:25Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/audiocraft | pypi-eco audiocraft |
| F0277 | 2026-09-26T20:08:26Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/stable-audio-tools | pypi-eco stable-audio-tools |
| F0278 | 2026-09-26T20:08:26Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/xfuser | pypi-eco xfuser |
| F0279 | 2026-09-26T20:08:26Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fastvideo | pypi-eco fastvideo |
| F0280 | 2026-09-26T20:08:26Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/diffsynth | pypi-eco diffsynth |
| F0281 | 2026-09-26T20:08:26Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/comfyui | pypi-eco comfyui |
| F0282 | 2026-09-26T20:08:26Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/comfy-cli | pypi-eco comfy-cli |
| F0283 | 2026-09-26T20:08:27Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/comfyui-frontend-package | pypi-eco comfyui-frontend-package |
| F0284 | 2026-09-26T20:08:27Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/nunchaku | pypi-eco nunchaku |
| F0285 | 2026-09-26T20:08:27Z | 404 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/lightx2v | pypi-eco lightx2v |
| F0286 | 2026-09-26T20:08:27Z | 404 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/mmaudio | pypi-eco mmaudio |
| F0287 | 2026-09-26T20:08:27Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/ace-step | pypi-eco ace-step |
| F0288 | 2026-09-26T20:08:28Z | 404 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/acestep | pypi-eco acestep |
| F0289 | 2026-09-26T20:08:28Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/hy3dgen | pypi-eco hy3dgen |
| F0290 | 2026-09-26T20:08:28Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/trellis | pypi-eco trellis |
| F0291 | 2026-09-26T20:08:28Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/ltx-video | pypi-eco ltx-video |
| F0292 | 2026-09-26T20:08:28Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/ltx-core | pypi-eco ltx-core |
| F0293 | 2026-09-26T20:08:29Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/sdkit | pypi-eco sdkit |
| F0294 | 2026-09-26T20:08:29Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/stable-diffusion-cpp-python | pypi-eco stable-diffusion-cpp-python |
| F0295 | 2026-09-26T20:08:29Z | 404 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/heartlib | pypi-eco heartlib |
| F0296 | 2026-09-26T20:08:29Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/yue | pypi-eco yue |
| F0297 | 2026-09-26T20:08:29Z | 404 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/musubi-tuner | pypi-eco musubi-tuner |
| F0298 | 2026-09-26T20:08:30Z | 404 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/onetrainer | pypi-eco onetrainer |
| F0299 | 2026-09-26T20:08:30Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/simpletuner | pypi-eco simpletuner |
| F0300 | 2026-09-26T20:08:30Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/ai-toolkit | pypi-eco ai-toolkit |
| F0301 | 2026-09-26T20:08:36Z | 200 | https://pypi.org/pypi/nunchaku/json | pypi json nunchaku |
| F0302 | 2026-09-26T20:08:36Z | 200 | https://pypi.org/pypi/stable-audio-tools/json | pypi json stable-audio-tools |
| F0303 | 2026-09-26T20:08:36Z | 200 | https://pypi.org/pypi/diffsynth/json | pypi json diffsynth |
| F0304 | 2026-09-26T20:08:37Z | 200 | https://pypi.org/pypi/comfyui-frontend-package/json | pypi json comfyui-frontend-package |
| F0305 | 2026-09-26T20:08:37Z | 200 | https://pypi.org/pypi/invokeai/json | pypi json invokeai |
| F0306 | 2026-09-26T20:08:37Z | 200 | https://pypi.org/pypi/xfuser/json | pypi json xfuser |
| F0307 | 2026-09-26T20:11:27Z | 200 | https://raw.githubusercontent.com/PKU-YuanGroup/Helios/HEAD/README.md | readme PKU-YuanGroup/Helios |
| F0308 | 2026-09-26T20:11:37Z | 200 | https://ungh.cc/repos/Comfy-Org/ComfyUI/releases/latest | ungh latest release Comfy-Org/ComfyUI |
| F0309 | 2026-09-26T20:11:37Z | 200 | https://ungh.cc/repos/invoke-ai/InvokeAI/releases/latest | ungh latest release invoke-ai/InvokeAI |
| F0310 | 2026-09-26T20:12:07Z | 000000 | https://ungh.cc/repos/vladmandic/sdnext/releases/latest | ungh latest release vladmandic/sdnext |
| F0311 | 2026-09-26T20:11:37Z | 200 | https://ungh.cc/repos/mcmonkeyprojects/SwarmUI/releases/latest | ungh latest release mcmonkeyprojects/SwarmUI |
| F0312 | 2026-09-26T20:11:38Z | 200 | https://ungh.cc/repos/AUTOMATIC1111/stable-diffusion-webui/releases/latest | ungh latest release AUTOMATIC1111/stable-diffusion-webui |
| F0313 | 2026-09-26T20:11:38Z | 200 | https://ungh.cc/repos/lllyasviel/stable-diffusion-webui-forge/releases/latest | ungh latest release lllyasviel/stable-diffusion-webui-forge |
| F0314 | 2026-09-26T20:11:38Z | 200 | https://ungh.cc/repos/lllyasviel/Fooocus/releases/latest | ungh latest release lllyasviel/Fooocus |
| F0315 | 2026-09-26T20:11:44Z | 000000 | https://ungh.cc/repos/Acly/krita-ai-diffusion/releases/latest | ungh latest release Acly/krita-ai-diffusion |
| F0316 | 2026-09-26T20:11:39Z | 200 | https://ungh.cc/repos/LykosAI/StabilityMatrix/releases/latest | ungh latest release LykosAI/StabilityMatrix |
| F0317 | 2026-09-26T20:11:39Z | 200 | https://ungh.cc/repos/leejet/stable-diffusion.cpp/releases/latest | ungh latest release leejet/stable-diffusion.cpp |
| F0318 | 2026-09-26T20:11:39Z | 200 | https://ungh.cc/repos/nunchux-ai/nunchaku/releases/latest | ungh latest release nunchux-ai/nunchaku |
| F0319 | 2026-09-26T20:11:40Z | 200 | https://ungh.cc/repos/ModelTC/LightX2V/releases/latest | ungh latest release ModelTC/LightX2V |
| F0320 | 2026-09-26T20:11:40Z | 200 | https://ungh.cc/repos/xdit-project/xDiT/releases/latest | ungh latest release xdit-project/xDiT |
| F0321 | 2026-09-26T20:11:40Z | 200 | https://ungh.cc/repos/hao-ai-lab/FastVideo/releases/latest | ungh latest release hao-ai-lab/FastVideo |
| F0322 | 2026-09-26T20:11:40Z | 200 | https://ungh.cc/repos/modelscope/DiffSynth-Studio/releases/latest | ungh latest release modelscope/DiffSynth-Studio |
| F0323 | 2026-09-26T20:11:40Z | 200 | https://ungh.cc/repos/easydiffusion/easydiffusion/releases/latest | ungh latest release easydiffusion/easydiffusion |
| F0324 | 2026-09-26T20:11:41Z | 200 | https://ungh.cc/repos/divamgupta/diffusionbee-stable-diffusion-ui/releases/latest | ungh latest release divamgupta/diffusionbee-stable-diffusion-ui |
| F0325 | 2026-09-26T20:11:41Z | 200 | https://ungh.cc/repos/carson-katri/dream-textures/releases/latest | ungh latest release carson-katri/dream-textures |
| F0326 | 2026-09-26T20:11:41Z | 404 | https://ungh.cc/repos/deepbeepmeep/Wan2GP/releases/latest | ungh latest release deepbeepmeep/Wan2GP |
| F0327 | 2026-09-26T20:11:41Z | 404 | https://ungh.cc/repos/Stability-AI/stable-audio-tools/releases/latest | ungh latest release Stability-AI/stable-audio-tools |
| F0328 | 2026-09-26T20:11:41Z | 404 | https://ungh.cc/repos/facebookresearch/audiocraft/releases/latest | ungh latest release facebookresearch/audiocraft |
| F0329 | 2026-09-26T20:11:42Z | 200 | https://ungh.cc/repos/ace-step/ACE-Step-1.5/releases/latest | ungh latest release ace-step/ACE-Step-1.5 |
| F0330 | 2026-09-26T20:11:42Z | 200 | https://ungh.cc/repos/multimodal-art-projection/YuE/releases/latest | ungh latest release multimodal-art-projection/YuE |
| F0331 | 2026-09-26T20:11:42Z | 404 | https://ungh.cc/repos/HeartMuLa/heartlib/releases/latest | ungh latest release HeartMuLa/heartlib |
| F0332 | 2026-09-26T20:11:42Z | 404 | https://ungh.cc/repos/microsoft/TRELLIS/releases/latest | ungh latest release microsoft/TRELLIS |
| F0333 | 2026-09-26T20:11:43Z | 429 | https://ungh.cc/repos/Tencent-Hunyuan/Hunyuan3D-2/releases/latest | ungh latest release Tencent-Hunyuan/Hunyuan3D-2 |
| F0334 | 2026-09-26T20:11:43Z | 403 | https://ungh.cc/repos/Lightricks/LTX-2/releases/latest | ungh latest release Lightricks/LTX-2 |
| F0335 | 2026-09-26T20:11:43Z | 403 | https://ungh.cc/repos/Wan-Video/Wan2.2/releases/latest | ungh latest release Wan-Video/Wan2.2 |
| F0336 | 2026-09-26T20:11:44Z | 429 | https://ungh.cc/repos/black-forest-labs/flux/releases/latest | ungh latest release black-forest-labs/flux |
| F0337 | 2026-09-26T20:11:44Z | 403 | https://ungh.cc/repos/hpcaitech/Open-Sora/releases/latest | ungh latest release hpcaitech/Open-Sora |
| F0338 | 2026-09-26T20:11:44Z | 403 | https://ungh.cc/repos/lllyasviel/FramePack/releases/latest | ungh latest release lllyasviel/FramePack |
| F0339 | 2026-09-26T20:11:44Z | 403 | https://ungh.cc/repos/KlingAIResearch/LivePortrait/releases/latest | ungh latest release KlingAIResearch/LivePortrait |
| F0340 | 2026-09-26T20:11:44Z | 403 | https://ungh.cc/repos/Stability-AI/generative-models/releases/latest | ungh latest release Stability-AI/generative-models |
| F0341 | 2026-09-26T20:12:20Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/vladmandic%2Fsdnext/releases?per_page=1 | eco releases vladmandic/sdnext |
| F0342 | 2026-09-26T20:12:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Acly%2Fkrita-ai-diffusion/releases?per_page=1 | eco releases Acly/krita-ai-diffusion |
| F0343 | 2026-09-26T20:12:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Tencent-Hunyuan%2FHunyuan3D-2/releases?per_page=1 | eco releases Tencent-Hunyuan/Hunyuan3D-2 |
| F0344 | 2026-09-26T20:12:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Lightricks%2FLTX-2/releases?per_page=1 | eco releases Lightricks/LTX-2 |
| F0345 | 2026-09-26T20:12:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Wan-Video%2FWan2.2/releases?per_page=1 | eco releases Wan-Video/Wan2.2 |
| F0346 | 2026-09-26T20:12:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/black-forest-labs%2Fflux/releases?per_page=1 | eco releases black-forest-labs/flux |
| F0347 | 2026-09-26T20:12:21Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/hpcaitech%2FOpen-Sora/releases?per_page=1 | eco releases hpcaitech/Open-Sora |
| F0348 | 2026-09-26T20:12:22Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lllyasviel%2FFramePack/releases?per_page=1 | eco releases lllyasviel/FramePack |
| F0349 | 2026-09-26T20:12:22Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/KlingAIResearch%2FLivePortrait/releases?per_page=1 | eco releases KlingAIResearch/LivePortrait |
| F0350 | 2026-09-26T20:12:22Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Stability-AI%2Fgenerative-models/releases?per_page=1 | eco releases Stability-AI/generative-models |
| F0351 | 2026-09-26T20:12:33Z | 200 | https://huggingface.co/api/models/KwaiVGI/LivePortrait?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model KwaiVGI/LivePortrait |
| F0352 | 2026-09-26T20:12:34Z | 200 | https://huggingface.co/api/models/FunAudioLLM/ThinkSound?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model FunAudioLLM/ThinkSound |
| F0353 | 2026-09-26T20:12:34Z | 200 | https://huggingface.co/api/models/facebook/sam-3d-objects?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model facebook/sam-3d-objects |
| F0354 | 2026-09-26T20:12:34Z | 200 | https://huggingface.co/api/models/lodestones/Chroma1-HD?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model lodestones/Chroma1-HD |
| F0355 | 2026-09-26T20:12:34Z | 200 | https://huggingface.co/api/models/ByteDance/LatentSync-1.6?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model ByteDance/LatentSync-1.6 |
| F0356 | 2026-09-26T20:12:35Z | 200 | https://huggingface.co/api/models/stabilityai/stable-video-diffusion-img2vid-xt?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stabilityai/stable-video-diffusion-img2vid-xt |
| F0357 | 2026-09-26T20:12:35Z | 200 | https://huggingface.co/api/models/stabilityai/stable-point-aware-3d?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stabilityai/stable-point-aware-3d |
| F0358 | 2026-09-26T20:12:35Z | 200 | https://huggingface.co/api/models/TencentARC/InstantMesh?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model TencentARC/InstantMesh |
| F0359 | 2026-09-26T20:12:36Z | 200 | https://huggingface.co/api/models/BestWishYsh/Helios-Distilled?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model BestWishYsh/Helios-Distilled |
| F0360 | 2026-09-26T20:12:36Z | 200 | https://huggingface.co/api/models/stepfun-ai/stepvideo-t2v?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stepfun-ai/stepvideo-t2v |
| F0361 | 2026-09-26T20:12:36Z | 200 | https://huggingface.co/api/models/wgsxm/PartCrafter?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model wgsxm/PartCrafter |
| F0362 | 2026-09-26T20:12:36Z | 200 | https://huggingface.co/api/models/Efficient-Large-Model/Sana_Sprint_1.6B_1024px_diffusers?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Efficient-Large-Model/Sana_Sprint_1.6B_1024px_diffusers |
| F0363 | 2026-09-26T20:12:37Z | 200 | https://huggingface.co/api/models/stabilityai/stable-audio-3-medium?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stabilityai/stable-audio-3-medium |
| F0364 | 2026-09-26T20:12:37Z | 200 | https://huggingface.co/api/models/tencent/HunyuanImage-3.0?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model tencent/HunyuanImage-3.0 |
| F0365 | 2026-09-26T20:12:37Z | 200 | https://huggingface.co/api/models/tencent/Hunyuan3D-2?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model tencent/Hunyuan3D-2 |
| F0366 | 2026-09-26T20:12:38Z | 200 | https://huggingface.co/api/models/microsoft/TRELLIS-image-large?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model microsoft/TRELLIS-image-large |
| F0367 | 2026-09-26T20:12:38Z | 200 | https://huggingface.co/api/models/black-forest-labs/FLUX.1-dev?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model black-forest-labs/FLUX.1-dev |
| F0368 | 2026-09-26T20:12:38Z | 200 | https://huggingface.co/api/models/stabilityai/stable-diffusion-xl-base-1.0?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model stabilityai/stable-diffusion-xl-base-1.0 |
| F0369 | 2026-09-26T20:12:39Z | 200 | https://huggingface.co/api/models/Wan-AI/Wan2.1-T2V-1.3B-Diffusers?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Wan-AI/Wan2.1-T2V-1.3B-Diffusers |
| F0370 | 2026-09-26T20:12:39Z | 200 | https://huggingface.co/api/models/PixArt-alpha/PixArt-Sigma-XL-2-1024-MS?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model PixArt-alpha/PixArt-Sigma-XL-2-1024-MS |
| F0371 | 2026-09-26T20:12:39Z | 200 | https://huggingface.co/api/models/Kwai-Kolors/Kolors-diffusers?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model Kwai-Kolors/Kolors-diffusers |
| F0372 | 2026-09-26T20:12:39Z | 200 | https://huggingface.co/api/models/m-a-p/YuE2-3B?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=pipeline_tag | hf model m-a-p/YuE2-3B |
| F0373 | 2026-09-26T20:13:04Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stepfun-ai%2FStep1X-Edit | ecosystems stepfun-ai/Step1X-Edit |
| F0374 | 2026-09-26T20:17:06Z | 200 | https://www.midjourney.com | homepage check https://www.midjourney.com |
| F0375 | 2026-09-26T20:17:07Z | 200 | https://suno.com | homepage check https://suno.com |
| F0376 | 2026-09-26T20:17:07Z | 403 | https://www.tripo3d.ai | homepage check https://www.tripo3d.ai |
| F0377 | 2026-09-26T20:17:09Z | 200 | https://seed.bytedance.com/en/seedream | homepage check https://seed.bytedance.com/en/seedream |
| F0378 | 2026-09-26T20:17:07Z | 200 | https://runway.com | homepage check https://runway.com |
| F0379 | 2026-09-26T20:17:08Z | 200 | https://www.meshy.ai | homepage check https://www.meshy.ai [truncated-to-300KB] |
| F0380 | 2026-09-26T20:17:08Z | 200 | https://kling.ai | homepage check https://kling.ai |
| F0381 | 2026-09-26T20:17:08Z | 200 | https://deepmind.google/models/veo/ | homepage check https://deepmind.google/models/veo/ |
| F0382 | 2026-09-26T20:17:09Z | 200 | https://deepmind.google/models/lyria/ | homepage check https://deepmind.google/models/lyria/ |
| F0383 | 2026-09-26T20:17:09Z | 200 | https://deepmind.google/models/gemini-image/ | homepage check https://deepmind.google/models/gemini-image/ |
| F0384 | 2026-09-26T20:17:09Z | 200 | https://developers.openai.com/api/docs/models | homepage check https://developers.openai.com/api/docs/models |
| F0385 | 2026-09-26T20:17:11Z | 200 | https://seed.bytedance.com/en/seedance | homepage check https://seed.bytedance.com/en/seedance |
| F0386 | 2026-09-26T20:24:11Z | 200 | https://huggingface.co/api/models/Qwen/Qwen-Image-2.1?expand[]=downloads&expand[]=cardData&expand[]=lastModified | audit: qwen-image 2.1 licence |
| F0387 | 2026-09-26T20:24:12Z | 200 | https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanImage-3.0/HEAD/LICENSE | audit: hunyuan-image licence territory |
| F0388 | 2026-09-26T20:24:12Z | 200 | https://huggingface.co/api/models/meituan-longcat/LongCat-Image?expand[]=downloads&expand[]=cardData&expand[]=lastModified | audit: longcat-image downloads |
| F0389 | 2026-09-26T20:24:12Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Wan-Video%2FWan2.2 | audit: wan push/licence |
| F0390 | 2026-09-26T20:24:13Z | 200 | https://huggingface.co/api/models/sand-ai/MAGI-2-preview?expand[]=downloads&expand[]=cardData&expand[]=lastModified | audit: magi downloads/licence |
| F0391 | 2026-09-26T20:24:13Z | 200 | https://huggingface.co/api/models/MiniMaxAI/MiniMax-H3?expand[]=downloads&expand[]=cardData&expand[]=lastModified | audit: minimax-hailuo downloads |
| F0392 | 2026-09-26T20:24:13Z | 200 | https://huggingface.co/api/models/microsoft/TRELLIS-image-large?expand[]=downloads&expand[]=cardData&expand[]=lastModified | audit: trellis downloads |
| F0393 | 2026-09-26T20:24:13Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/TencentARC%2FInstantMesh | audit: instantmesh push/dormant |
| F0394 | 2026-09-26T20:24:14Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/stable-audio-tools | audit: stable-audio pypi downloads |
| F0395 | 2026-09-26T20:24:14Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Comfy-Org%2FComfyUI | audit: comfyui identity/licence/stars |
| F0396 | 2026-09-26T20:24:14Z | 200 | https://raw.githubusercontent.com/mcmonkeyprojects/SwarmUI/HEAD/LICENSE.txt | audit: swarmui licence text |
| F0397 | 2026-09-26T20:24:14Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/deepbeepmeep%2FWan2GP | audit: wan2gp fork flag |
| F0398 | 2026-09-26T20:24:14Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/xfuser | audit: xdit pypi downloads |
| F0399 | 2026-09-26T20:24:15Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ideogram-oss%2Fideogram4 | audit: ideogram archived/fork |
| F0400 | 2026-09-26T20:24:15Z | 404 | https://raw.githubusercontent.com/tencent-ailab/SongGeneration/HEAD/LICENSE.txt | audit: songgeneration licence (alt name) |
| F0401 | 2026-09-26T20:26:59Z | 200 | https://raw.githubusercontent.com/facebookresearch/audiocraft/HEAD/README.md | install doc README facebookresearch/audiocraft |
| F0402 | 2026-09-26T20:26:59Z | 200 | https://raw.githubusercontent.com/xdit-project/xDiT/HEAD/README.md | install doc README xdit-project/xDiT |
| F0403 | 2026-09-26T20:27:00Z | 200 | https://raw.githubusercontent.com/hao-ai-lab/FastVideo/HEAD/README.md | install doc README hao-ai-lab/FastVideo |
| F0404 | 2026-09-26T20:27:00Z | 200 | https://raw.githubusercontent.com/modelscope/DiffSynth-Studio/HEAD/README.md | install doc README modelscope/DiffSynth-Studio |
| F0405 | 2026-09-26T20:27:00Z | 200 | https://raw.githubusercontent.com/Stability-AI/stable-audio-tools/HEAD/README.md | install doc README Stability-AI/stable-audio-tools |
| F0406 | 2026-09-26T20:27:01Z | 200 | https://invoke-ai.github.io/InvokeAI/installation/manual/ | install doc InvokeAI manual install |
| F0407 | 2026-09-26T20:27:09Z | 200 | https://invoke.ai/start-here/manual | install doc InvokeAI manual install (redirect target) |
| W0001 | 2026-09-26T19:59:48Z | WebSearch | best open-weight text-to-video models 2026 | Wan 2.2 ... released by Alibaba's Tongyi Lab on July 29, 2025 ... LTX-2.3 (released March 5, 2026) ... HunyuanVideo 1.5  |
| W0002 | 2026-09-26T19:59:48Z | WebSearch | open source image generation model release 2026 Hugging Face | FLUX.2 - Released in November 2025 by Black Forest Labs ... HiDream-O1-Image - Open-sourced on May 8, 2026 ... Qwen-Imag |
| W0003 | 2026-09-26T19:59:48Z | WebSearch | open source 3D generation model image-to-3D 2026 | Models like TRELLIS 2, TripoSR, and Hunyuan3D turn a single image or text prompt into a textured, game-ready mesh ... TR |
| W0004 | 2026-09-26T19:59:48Z | WebSearch | open source music generation model 2026 release weights | HeartMuLa-RL-oss-3B was released on January 23, 2026 ... Apache 2.0 ... MiniMax Music 3.0 Released on August 13, 2026 op |
| W0005 | 2026-09-26T20:00:07Z | WebSearch | Artificial Analysis text to image arena leaderboard open weights | Qwen-Image-2.1 currently leads among open weights models in the Artificial Analysis Text to Image Arena with an Elo scor |
| W0006 | 2026-09-26T20:00:07Z | WebSearch | Artificial Analysis video arena leaderboard 2026 open weights model | MiniMax H3 currently leads among open weights Text to Video models with audio ... Elo 1220, followed by LTX-2.5 Fast (El |
| W0007 | 2026-09-26T20:00:07Z | WebSearch | ComfyUI alternatives Stable Diffusion WebUI Forge InvokeAI SwarmUI SD.Next 2026 | ComfyUI, Forge, SwarmUI, and InvokeAI are the four most-used Stable Diffusion UIs in 2026 ... A1111 (the original) is no |
| W0008 | 2026-09-26T20:00:07Z | WebSearch | open source text-to-3D model 2026 Hunyuan3D TRELLIS Step1X-3D TripoSG release | Hunyuan3D 2.1 excludes the EU, UK, and South Korea under its licensing restrictions ... Step1X-3D ... TripoSG is a high- |
| W0009 | 2026-09-26T20:00:38Z | WebFetch | https://artificialanalysis.ai/image/leaderboard/text-to-image/open-weights | 1 Qwen-Image-2.1 Alibaba 1035 Sep 2026; 2 Ideogram 4.0 (Quality) Ideogram 1010 Jun 2026; 4 FLUX.2 [dev] BFL 1000; 7 Ming |
| W0010 | 2026-09-26T20:00:38Z | WebFetch | https://artificialanalysis.ai/video/leaderboard/text-to-video/open-weights | 1 MiniMax H3 MiniMax Elo 1220 Jul 2026; 2 LTX-2.5 Fast Lightricks 1055 Aug 2026; 3 LTX-2.5 Pro 1053; 4 LTX-2.3 Fast 975  |
| W0011 | 2026-09-26T20:00:38Z | WebFetch | https://artificialanalysis.ai/image/leaderboard/text-to-image | 1 GPT Image 2.5 Sunburst (max) OpenAI 1196 No; 3 GPT Image 2 (high) OpenAI 1171; 4 Grok Imagine Image 2.0 SpaceXAI 1157; |
| W0012 | 2026-09-26T20:00:53Z | WebFetch | https://artificialanalysis.ai/video/leaderboard/text-to-video | without audio: 1 Wan 3.0 Alibaba 1335 No; 2 Gemini Omni Flash Google 1332 No; 3 MiniMax H3 MiniMax 1302 Yes; 7 Dreamina  |
| W0013 | 2026-09-26T20:00:53Z | WebFetch | https://artificialanalysis.ai/video/leaderboard/image-to-video/open-weights | Open weights, With Audio: 1 MiniMax H3 1181 Jul 2026; 2 Sand.ai MAGI-2 Preview 1094 Aug 2026; 3 Lightricks LTX-2.5 Fast  |
| W0014 | 2026-09-26T20:02:50Z | WebSearch | Ideogram 4.0 open weights release Hugging Face license | Ideogram released Ideogram 4.0 on June 3, 2026, via Hugging Face (gated access, nf4 and fp8 quantized variants) and GitH |
| W0015 | 2026-09-26T20:02:50Z | WebSearch | MiniMax H3 open weights video model release Hugging Face | MiniMax AI released open weights for its 33B-parameter MiniMax-H3 model on Hugging Face ... open-sourced H3, the omni-mo |
| W0016 | 2026-09-26T20:02:50Z | WebSearch | Wan 3.0 Alibaba video model open source or closed weights | Wan 3.0 is a closed, API-only model, and no weights have been published ... last open-weight video flagship remains Wan  |
| W0017 | 2026-09-26T20:02:50Z | WebSearch | MAGI-2 Sand.ai open weights release license | Sand.ai released MAGI-2 Preview on August 5, an open-source, 114B-parameter mixture-of-experts (MoE) model ... Apache 2. |
| W0018 | 2026-09-26T20:04:20Z | WebFetch | https://huggingface.co/black-forest-labs/FLUX.2-dev/blob/main/LICENSE.txt | HTTP 404 Not Found (gated file; not retrieved) |
| W0019 | 2026-09-26T20:04:20Z | WebFetch | https://stability.ai/license | Use of the Core Models (including Stable Diffusion 3 2B) is free for everyone, unless you're using the Core Models for a |
| W0020 | 2026-09-26T20:04:20Z | WebFetch | https://ideogram.ai/blog/ideogram-4.0/ | 9.3B parameter open-weight text-to-image model ... fp8 and nf4 checkpoints ... first open-weight foundation model ... da |
| W0021 | 2026-09-26T20:04:20Z | WebFetch | https://huggingface.co/black-forest-labs/FLUX.2-dev | The model operates under the FLUX Non-Commercial License. Commercial use of the open-weight model is not permitted—only  |
| W0022 | 2026-09-26T20:04:20Z | WebFetch | https://ideogram.ai/licensing/ | Non-Commercial License - Free for research and prototyping ... research, evaluation, and personal projects ... Self-Serv |
| W0023 | 2026-09-26T20:04:54Z | WebSearch | Suno v5 Udio ElevenLabs Music Lyria best AI music generator 2026 comparison | Suno V5.5 ranks first on the Artificial Analysis vocals arena, and Suno v6 (September 9, 2026, trained on licensed music |
| W0024 | 2026-09-26T20:04:54Z | WebSearch | Midjourney V8 release 2026 | V8.0 was an early access alpha version that launched on March 17, 2026 ... V8.1 Alpha April 14, 2026 ... became the defa |
| W0025 | 2026-09-26T20:04:54Z | WebSearch | Sora app 2026 status OpenAI video generation Sora 2 discontinued | the Sora web and app experiences were discontinued on April 26, 2026, and the Sora API will be discontinued on September |
| W0026 | 2026-09-26T20:04:54Z | WebSearch | best AI 3D model generator 2026 Meshy Tripo Rodin Hunyuan3D 3.0 closed | Rodin (Hyper3D.ai) ... 10-billion-parameter Rodin Gen-2 ... Tripo AI is often called the best overall in 2026 ... Meshy  |
| W0027 | 2026-09-26T20:05:04Z | WebFetch | https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation | HTTP 403 (fetch did not complete) |
| W0028 | 2026-09-26T20:05:04Z | WebFetch | https://artificialanalysis.ai/music/leaderboard | HTTP 404 (wrong path) |
| W0029 | 2026-09-26T20:05:04Z | WebFetch | https://en.wikipedia.org/wiki/Sora_(text-to-video_model) | The Sora app was shut down on April 26, 2026 ... the API was shut down on September 24, 2026 ... announced these discont |
| W0030 | 2026-09-26T20:05:04Z | WebFetch | https://artificialanalysis.ai/text-to-music | HTTP 404 (wrong path) |
| W0031 | 2026-09-26T20:05:27Z | WebSearch | artificialanalysis.ai music arena leaderboard open weights ACE-Step | AA-Music-Instrumental v1.1 leaderboard: 1. Suno v6 (Elo 1143), 2. Suno v6-mini (1112), 3. Mureka V9.5 (1083), 4. Lyria 3 |
| W0032 | 2026-09-26T20:05:27Z | WebFetch | https://artificialanalysis.ai/music/leaderboard/vocals | 1 Suno v6 1134 Suno; 3 Mureka V9.5 1098; 5 Lyria 3.5 1045 Google; 7 Eleven Music v2.5 1010 ElevenLabs; 8 MiniMax Music 3 |
| W0033 | 2026-09-26T20:05:27Z | WebFetch | https://artificialanalysis.ai/music/leaderboard/instrumental | 1 Suno v6 1143; 4 Lyria 3 Pro 1082; 7 Eleven Music 1024; 8 Stable Audio 3 Large 1019 Stability.ai; 13 Stable Audio 3 Med |
| W0034 | 2026-09-26T20:05:50Z | WebSearch | diffusion LoRA training tool 2026 kohya musubi-tuner SimpleTuner diffusion-pipe OneTrainer ai-toolkit | Musubi-Tuner - Kohya-ss's answer to training LoRAs for the current generation of video and image diffusion transformers  |
| W0035 | 2026-09-26T20:05:50Z | WebSearch | open source video-to-audio foley sound effects generation model 2026 MMAudio ThinkSound HunyuanVideo-Foley | GitHub - QwenAudio/ThinkSound: [NeurIPS 2025] ... unified framework for generating audio from any modality ... MMAudio i |
| W0036 | 2026-09-26T20:05:50Z | WebSearch | new open-source video generation model released August September 2026 weights GitHub | Wan 3.0 was released August 24, 2026 as a free open-weight release with access via GitHub for self-hosting (CONTRADICTED |
| W0037 | 2026-09-26T20:06:29Z | WebFetch | https://github.com/topics/text-to-video?o=desc&s=stars | 1 calesthio/OpenMontage 61.4k; 2 Anil-matcha/Open-Generative-AI 29.2k; 3 hypit-ai/hypit 16.3k; 4 HBAI-Ltd/Toonflow-app 1 |
| W0038 | 2026-09-26T20:06:29Z | WebFetch | https://github.com/topics/text-to-image?o=desc&s=stars | 1 Anil-matcha/Open-Generative-AI 29.2k; 4 lucidrains/DALLE2-pytorch 11.3k; 7 XavierXiao/Dreambooth-Stable-Diffusion 7.7k |
| W0039 | 2026-09-26T20:06:29Z | WebFetch | https://github.com/topics/music-generation?o=desc&s=stars | 1 multimodal-art-projection/YuE 10.3k; 2 open-mmlab/Amphion 10.3k; 4 fspecii/ace-step-ui 5k; 5 0xShug0/audio.cpp 3.1k; 7 |
| W0040 | 2026-09-26T20:06:29Z | WebFetch | https://github.com/topics/text-to-3d?o=desc&s=stars | 1 Tencent-Hunyuan/Hunyuan3D-2 15k; 2 microsoft/TRELLIS 13.7k; 3 ashawkey/stable-dreamfusion 8.9k; 7 Tencent-Hunyuan/Huny |
| W0041 | 2026-09-26T20:07:02Z | WebFetch | https://github.com/topics/stable-diffusion?o=desc&s=stars | 1 AUTOMATIC1111/stable-diffusion-webui 165k; 2 Comfy-Org/ComfyUI 135k; 6 huggingface/diffusers 34.6k; 7 invoke-ai/Invoke |
| W0042 | 2026-09-26T20:07:02Z | WebFetch | https://github.com/topics/image-to-3d?o=desc&s=stars | 1 img2threejs/img2threejs 16.9k; 2 Tencent-Hunyuan/Hunyuan3D-2 15k; 3 microsoft/TRELLIS 13.7k; 8 AiuniAI/Unique3D 3.6k;  |
| W0043 | 2026-09-26T20:07:02Z | WebFetch | https://github.com/topics/video-generation?o=desc&s=stars | 1 calesthio/OpenMontage 61.4k agentic video production system; 2 ATH-MaaS/Pixelle-Video 28.4k; 3 KlingAIResearch/LivePor |
| W0044 | 2026-09-26T20:07:40Z | WebSearch | nunchaku SVDQuant github repository 4-bit diffusion inference engine | GitHub - nunchaku-ai/nunchaku: [ICLR2025 Spotlight] SVDQuant ... Nunchaku is a high-performance inference engine for low |
| W0045 | 2026-09-26T20:07:40Z | WebSearch | ideogram 4 github inference code repository apache | GitHub - ideogram-oss/ideogram4: Ideogram 4: Open image model at the forefront of design ... ideogram-oss/ComfyUI-Ideogr |
| W0046 | 2026-09-26T20:07:40Z | WebSearch | Chroma lodestones open source image model Apache FLUX schnell based 2026 | Chroma is an 8.9B parameter model based on FLUX.1-schnell, developed by lodestones. It's fully Apache 2.0 licensed ... l |
| W0047 | 2026-09-26T20:09:14Z | WebFetch | https://platform.openai.com/docs/models | 301 redirect to https://developers.openai.com/api/docs/models (followed in next entry) |
| W0048 | 2026-09-26T20:09:14Z | WebFetch | https://deepmind.google/models/veo/ | Veo 3.1 ... Video, meet audio. Our leading video generation model, designed to empower filmmakers and storytellers. |
| W0049 | 2026-09-26T20:09:14Z | WebFetch | https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version | HTTP 403 (fetch did not complete) |
| W0050 | 2026-09-26T20:09:14Z | WebFetch | https://deepmind.google/models/lyria/ | Lyria 3.5 ... Our most advanced music generation model, now up to 3 minutes long |
| W0051 | 2026-09-26T20:09:14Z | WebFetch | https://developers.openai.com/api/docs/models | GPT-Image-2.5 Sunburst — Our most capable model for image generation and editing; GPT-Image-2.5 Flare — Fast, high-quali |
| W0052 | 2026-09-26T20:09:14Z | WebFetch | https://updates.midjourney.com/v8-1-alpha/ | Release Date: April 14, 2026 ... V8.1 has a consistent and familiar aesthetic in the spirit of V7 ... available only on  |
| W0053 | 2026-09-26T20:09:14Z | WebFetch | https://deepmind.google/models/gemini-image/ | Nano Banana 2, built on Gemini 3.1 Flash Image ... Gemini 3.1 Flash Image offers pro-level image generation and editing, |
| W0054 | 2026-09-26T20:09:14Z | WebFetch | https://suno.com/about | Suno is a music company building the world's first creative entertainment platform ... v6, A New Generation of Music Mod |
| W0055 | 2026-09-26T20:09:33Z | WebFetch | https://klingai.com/global/ | 301 redirect to https://kling.ai/ (followed in later entry) |
| W0056 | 2026-09-26T20:09:33Z | WebFetch | https://seed.bytedance.com/en/seedance | Seedance 1.0 ... A model that supports multi-shot video generation from both text and image. (vendor page stale vs AA bo |
| W0057 | 2026-09-26T20:09:33Z | WebFetch | https://seed.bytedance.com/en/seedream | 302 redirect to seed.bytedance.com/en/seedream3_0 (not followed) |
| W0058 | 2026-09-26T20:09:33Z | WebFetch | https://runwayml.com/research | 308 redirect to https://runway.com/research (followed in later entry) |
| W0059 | 2026-09-26T20:09:33Z | WebFetch | https://kling.ai/ | AI Video & Image Generator ... VIDEO 3.0 and VIDEO 3.0 Omni models feature a fully upgraded architecture ... © 2024-2026 |
| W0060 | 2026-09-26T20:09:33Z | WebFetch | https://runway.com/research | Gen-4.5 ... The world's best video model, featuring state-of-the-art motion quality, prompt adherence and visual fidelit |
| W0061 | 2026-09-26T20:09:33Z | WebFetch | https://www.meshy.ai/ | Meshy is a free AI 3D model generator that turns text or images into ready-to-use 3D models in under a minute ... Meshy  |
| W0062 | 2026-09-26T20:09:33Z | WebFetch | https://www.tripo3d.ai/ | HTTP 403 (fetch did not complete) |
| W0063 | 2026-09-26T20:11:11Z | WebSearch | 3D Arena leaderboard image-to-3D Elo 2026 Hunyuan3D TRELLIS Tripo Meshy | Pixazo leaderboard: Tencent's Hunyuan3D-2.5 leads 3D model generation with a score of 1325, followed by Microsoft's TREL |
| W0064 | 2026-09-26T20:11:11Z | WebSearch | Hunyuan3D 3.0 open source weights or API only | everything after Hunyuan3D 2.1 (including 2.5, PolyGen, 3.0, and 3.1) runs only on Tencent's hosted platform and API ... |
| W0065 | 2026-09-26T20:13:03Z | WebSearch | open-source image editing model 2026 Step1X-Edit Qwen-Image-Edit FLUX Kontext alternatives open weights | The main open-weight editors as of July 2026 are FLUX.1 Kontext, Qwen-Image-Edit, Step1X-Edit, MagicQuill and SUPIR ...  |
| W0066 | 2026-09-26T20:13:03Z | WebSearch | Kandinsky 5.0 video model open source MIT license Sber release | Kandinsky Lab released Kandinsky 5.0 on November 18, 2025 ... Kandinsky Lab, backed by Sberbank ... Video Lite (2B) ...  |
| W0067 | 2026-09-26T20:25:22Z | WebFetch | https://runway.com/research | audit: Gen-4.5 ... The world's best video model, featuring state-of-the-art motion quality, prompt adherence and visual  |
| W0068 | 2026-09-26T20:25:22Z | WebFetch | https://updates.midjourney.com/v8-1-alpha/ | audit: Apr 14, 2026 ... It's so cheap we're making it default for V8.1 (HD mode default within V8.1; page does not say V |
| W0069 | 2026-09-26T20:25:22Z | WebFetch | https://artificialanalysis.ai/video/leaderboard/text-to-video/open-weights | audit: 1 MiniMax H3 (MiniMax) 1220; 2 LTX-2.5 Fast (Lightricks) 1055; 3 LTX-2.5 Pro 1053; 4 LTX-2.3 Fast 975; 5 LTX-2.3  |

## 7. Parked candidates

### 7a. Parked (unique candidates not accepted)

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

All parked entries were fetched or seen on 2026-09-26.

### 7b. Duplicate signals: already on the map or already ruled

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

## 8. Reconciled counts

A raw signal is one sighting of a candidate in one discovery source family: the brief's lead list,
an Artificial Analysis board, a WebSearch, a GitHub topic page, an HF org listing, or a lead I named
myself and then verified live ("recall-lead"). Each row's sources are the `src` field in `gen/data.py` and `gen/parked.py`;
`not named in brief` below lists what search found beyond the brief.

```
raw_signals       = duplicate_signals + unique_candidates
248               = 106               + 142
unique_candidates = accepted + parked
142               = 92       + 50
```

The 106 duplicate signals are 93 repeat sightings of a candidate already counted (for example FLUX
seen in the brief, on the AA board, in a search and in its HF org listing) plus 13 index or ledger
matches (table 7b).

**Found beyond the brief** (accepted, surfaced by search, leaderboards, topic pages or HF listings,
not in the brief's leads). Models: z-image, fibo, glm-image, ideogram, ernie-image, longcat-image,
omnigen, infinity-image, ming-image, nextstep, step1x-edit, magi, skyreels, kandinsky,
minimax-hailuo, longcat-video, helios, stable-video-diffusion, liveportrait, latentsync, triposg,
triposr, step1x-3d, stable-fast-3d, spar3d, instantmesh, cube, partcrafter, heartmula,
minimax-music, mmaudio, thinksound, hunyuanvideo-foley, foleycrafter. Software: krita-ai-diffusion,
stability-matrix, diffusionbee, dream-textures. Closed: seedream, seedance, lyria, meshy, tripo.
Named from my own lead list and verified live, not surfaced by a search: sam-3d, diffrhythm,
songgeneration, step-video, easy-diffusion, wan2gp, framepack, stable-diffusion-cpp, xdit, lightx2v,
fastvideo and diffsynth-studio.

## 9. Open questions for the maintainer

1. **Do media apps and UIs (ComfyUI, A1111, Forge, InvokeAI, Fooocus, SD.Next, SwarmUI…) live here or
   in `ui_api`?** Options: here | ui_api. **Recommend here.** `ui_api` holds chat UIs and gateways,
   and none of its index rows is a media app. Models alone (59) clear the bar either way.
2. **One category with a `{model: model, software: software}` ladder map, or split models from apps?**
   **Recommend one category with the map**, following the `document_conversion` precedent.
3. **Split by modality (image / video / 3D / audio)?** Each clears 10 alone. **Recommend no**: keep
   one category, record modality per row, and read a within-modality arena percentile (section 4).
4. **Diffusion-specific engines** (stable-diffusion.cpp, xDiT, LightX2V, FastVideo, DiffSynth-Studio,
   and the `nunchaku` tail row now in `compilers`): here | inference_code/compilers. **Recommend here,
   and move `nunchaku`.**
5. **Adapters and derivative checkpoints** (Civitai LoRAs and merges, ControlNet, Chroma with 66k HF
   downloads a month, F0354): confirm they are not products? **Recommend yes, park as a class.** Chroma
   is the hardest case, since it was retrained to 8.9B (W0046).
6. **Trainers** kohya sd-scripts, musubi-tuner, SimpleTuner and diffusion-pipe: propose them to
   `finetuning_code` beside OneTrainer and ai-toolkit? **Recommend yes.** `diffusers` stays in
   `ml_frameworks`.
7. **Sub-scope:** is portrait animation and lip-sync (LivePortrait, LatentSync) in, and is video
   restoration (SeedVR2) in? **Recommend animation/lip-sync in** (the output is synthesized video)
   **and restoration out.**
8. **Vendor modality lines:** do qwen-image, glm-image, ernie-image, hunyuan-*, minimax-hailuo and
   minimax-music get their own rows beside the vendors' LLM heads? **Recommend yes**, per the
   qwen3-embedding and qwen-coder precedent and the vendors' own naming (HF ids F0114, F0165, F0164,
   F0136, F0190).
9. **LongCat:** one row for image and video, or two? **Recommend two** (longcat-image, longcat-video),
   split by modality like Hunyuan.
10. **Closed flagships on open lines.** Wan 2.5–3.0, Hunyuan3D 2.5–3.1 and Qwen-Image 3.0 are API-only,
    and Qwen-Image-2.1 is non-commercial. Which release governs openness? The identity guide excludes
    API-only tiers from most-restrictive resolution. **Recommend: the newest *distributed* release
    governs, and the closed flagship is written into the row's comments.** This deserves its own ruling
    because it decides whether `wan` scores open.
11. **Stability AI lines:** stable-diffusion, stable-video-diffusion, stable-audio, stable-fast-3d and
    spar3d as five rows? **Recommend yes.** SF3D and SPAR3D are different models, not sizes.
12. **ADR-005 look:** Midjourney and Runway Gen-4.5 are not in the AA top 25 as fetched (W0011, W0012).
    Keep both? **Recommend keeping Midjourney** as the best-known closed image service, **and looking
    at Runway** before promotion.
13. **TripoSR org:** VAST-AI-Research code with weights on `stabilityai` (F0040, F0160). Attribute it
    to `vast-ai`? **Recommend yes.**
14. **ByteDance org slugs:** infinity-image and latentsync (FoundationVision and ByteDance research, not
    Seed) use a new `bytedance` slug beside the index's `bytedance-seed-volcano-engine`. Reuse the
    existing slug, or keep two? **Recommend reusing `bytedance-seed-volcano-engine`** if the map
    attributes by parent company; the rows keep `bytedance` until you rule.
