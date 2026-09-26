# Candidate data for the media_generation sweep. Every fact carries an F/W id.
# fields: slug, name, type, org, gh, hf, pypi, home, status, modality, bucket,
#         lic, arch, push, rel, adopt, members, handle, notes, src
# bucket: model | tool | closed ; src: discovery sources (brief, aa, ws, topic, hforg)

A = []
def c(**k): A.append(k)

# ---------------- IMAGE MODELS ----------------
c(slug='flux', name='FLUX', type='model', org='black-forest-labs', gh='black-forest-labs/flux2', hf='black-forest-labs/FLUX.1-dev',
  status='open-weights', modality='image', bucket='model',
  lic='weights: FLUX.1 [dev]/FLUX.2 [dev] "FLUX Non-Commercial License" (F0367, F0147, W0021); FLUX.1 [schnell] and FLUX.2 [klein] 4B Apache-2.0 (F0077, F0169); FLUX.2 [klein] 9B non-commercial (F0077); code Apache-2.0 (F0001, F0002)',
  arch='no/no (F0002)', push='2026-03-12 flux2 (F0002); FLUX.1 repo black-forest-labs/flux 2025-07-31 (F0001)', rel='no GitHub release returned by ecosyste.ms (F0346)',
  adopt='HF 30d downloads FLUX.1-dev 692,264 (F0367); FLUX.2-dev 406,993 (F0147); FLUX.2-klein-4B 404,007 (F0077)',
  members='FLUX.1 [dev]/[schnell]/Kontext/Krea/Fill/Redux; FLUX.2 [dev]/[klein] 4B/9B; API-only FLUX.2 pro/flex (W0021, W0011)',
  handle='GH black-forest-labs; HF black-forest-labs', notes='AA open-weights T2I Elo FLUX.2 [dev] 1000 (W0009). Row declares the current FLUX.2 repo and the most-downloaded checkpoint (FLUX.1-dev).',
  src=['brief','aa','ws','hforg'])
c(slug='stable-diffusion', name='Stable Diffusion', type='model', org='stability-ai', gh='Stability-AI/generative-models', hf='stabilityai/stable-diffusion-xl-base-1.0',
  status='open-weights', modality='image', bucket='model',
  lic='SD3.5: Stability AI Community License (free commercial use under USD 1M annual revenue) (F0148, W0019); SDXL: openrail++ (F0368); code MIT (F0003)',
  arch='no/no (F0003)', push='2025-12-16 (F0003); sd3.5 repo 2025-01-08 (F0004)', rel='0.1.0, 2023-07-27 (F0350)',
  adopt='HF 30d downloads SDXL base 3,598,555 (F0368); SD3.5 Large 100,154 (F0148)',
  members='SD 1.5/2.1/XL/Turbo, SD3 Medium, SD3.5 Large/Medium/Turbo (F0078)', handle='GH Stability-AI; HF stabilityai',
  notes='AA open-weights T2I Elo SD3.5 Large 839 (W0009).', src=['brief','aa','hforg'])
c(slug='qwen-image', name='Qwen-Image', type='model', org='alibaba-cloud', gh='QwenLM/Qwen-Image', hf='Qwen/Qwen-Image',
  status='open-weights', modality='image', bucket='model',
  lic='Qwen-Image / 2512 / Edit-2511 Apache-2.0 (F0114, F0115, F0117); Qwen-Image-2.1 "Qwen RESEARCH LICENSE", non-commercial only (F0116, F0170); Qwen-Image-3.0 closed (W0011)',
  arch='no/no (F0005)', push='2026-02-10 (F0005)', rel='not fetched',
  adopt='HF 30d downloads Qwen-Image 290,124 (F0114); Qwen-Image-Edit-2511 317,872 (F0117); Edit-2509 465,386 (F0079)',
  members='Qwen-Image, -2512, -Edit/-2509/-2511, -2.1 (research licence); closed -2.0 Pro / -3.0 (W0011)', handle='GH QwenLM; HF Qwen',
  notes='Separate product from the `qwen` LLM head row, as qwen-coder/qwen3-embedding are. Top open-weights T2I on AA: Qwen-Image-2.1 Elo 1035 (W0009). Current open release is non-commercial.',
  src=['brief','aa','ws','hforg'])
c(slug='hidream', name='HiDream', type='model', org='hidream-ai', gh='HiDream-ai/HiDream-O1-Image', hf='HiDream-ai/HiDream-O1-Image',
  status='open', modality='image', bucket='model', lic='MIT (F0007, F0119; I1: F0006, F0118)', arch='no/no (F0007)',
  push='2026-06-22 (F0007)', rel='not fetched', adopt='HF 30d downloads O1-Image 6,071 (F0119); I1-Fast 54,081 (F0080)',
  members='HiDream-I1 Full/Dev/Fast, HiDream-O1-Image / -Dev', handle='GH HiDream-ai; HF HiDream-ai',
  notes='AA open-weights T2I Elo O1-Image 979 (W0009). O1 open-sourced 2026-05-08 (W0002).', src=['brief','aa','ws','hforg'])
c(slug='sana', name='SANA', type='model', org='nvidia', gh='NVlabs/Sana', hf=None, status='open', modality='image', bucket='model',
  lic='Apache-2.0 code (F0008) and weights (F0120, F0121, F0362)', arch='no/no (F0008)', push='2026-09-21 (F0008)', rel='not fetched',
  adopt='GitHub stars 9,144 (F0008); HF API reports 0 downloads on SANA diffusers repos (F0120, F0362), so no usable HF instrument',
  members='SANA 1.6B, SANA 1.5 4.8B, SANA-Sprint, SANA-Video 2.0 (F0081)', handle='GH NVlabs; HF Efficient-Large-Model',
  notes='AA open-weights T2I Elo Sana Sprint 1.6B 753 (W0009). HF omitted from row: zero-download repos would band adoption wrongly.', src=['brief','aa','topic','hforg'])
c(slug='pixart', name='PixArt', type='model', org='pixart-alpha', gh='PixArt-alpha/PixArt-sigma', hf='PixArt-alpha/PixArt-Sigma-XL-2-1024-MS',
  status='open-weights', modality='image', bucket='model', lic='weights openrail++ (F0370); code Apache-2.0 (F0009)', arch='no/no (F0009)',
  push='2024-10-31 (F0009)', rel='not fetched', adopt='HF 30d downloads Sigma-XL-2-1024 34,593 (F0370)', members='PixArt-alpha, PixArt-Sigma (F0082)',
  handle='GH/HF PixArt-alpha', notes='Dormant: no push since 2024-10.', src=['brief','hforg'])
c(slug='kolors', name='Kolors', type='model', org='kuaishou', gh='Kwai-Kolors/Kolors', hf='Kwai-Kolors/Kolors-diffusers', status='open', modality='image', bucket='model',
  lic='Apache-2.0 on repo and HF card (F0010, F0141, F0371)', arch='no/no (F0010)', push='2024-11-13 (F0010)', rel='not fetched',
  adopt='HF 30d downloads Kolors-diffusers 5,336 (F0371)', members='Kolors, Kolors IP-Adapter variants (F0083)', handle='GH/HF Kwai-Kolors',
  notes='Dormant since 2024-11.', src=['brief','hforg'])
c(slug='lumina', name='Lumina', type='model', org='alpha-vllm', gh='Alpha-VLLM/Lumina-Image-2.0', hf='Alpha-VLLM/Lumina-Image-2.0', status='open', modality='image', bucket='model',
  lic='Apache-2.0 (F0011, F0140)', arch='no/no (F0011)', push='2026-05-22 (F0011)', rel='not fetched', adopt='HF 30d downloads 996 (F0140)',
  members='Lumina-Image 2.0, Lumina-mGPT, Lumina-DiMOO (F0084)', handle='GH/HF Alpha-VLLM', notes='AA open-weights T2I Elo Lumina Image v2 781 (W0009).', src=['brief','aa','hforg'])
c(slug='hunyuan-image', name='HunyuanImage', type='model', org='tencent', gh='Tencent-Hunyuan/HunyuanImage-3.0', hf='tencent/HunyuanImage-3.0', status='open-weights', modality='image', bucket='model',
  lic='Tencent Hunyuan Community License; does not apply in the EU, UK and South Korea (F0179, F0364)', arch='no/no (F0012)', push='2026-06-23 (F0012)', rel='not fetched',
  adopt='HF 30d downloads HunyuanImage-3.0-Instruct 17,466 (F0085); 3.0 3,417 (F0364)', members='HunyuanImage 2.1, 3.0, 3.0-Instruct (F0013, F0085)', handle='GH Tencent-Hunyuan; HF tencent',
  notes='AA open-weights T2I Elo 3.0 Instruct 963 (W0009). Distinct from the `hunyuan` LLM tail row.', src=['brief','aa','hforg'])
c(slug='z-image', name='Z-Image', type='model', org='alibaba-cloud', gh='Tongyi-MAI/Z-Image', hf='Tongyi-MAI/Z-Image-Turbo', status='open', modality='image', bucket='model',
  lic='Apache-2.0 (F0014, F0158)', arch='no/no (F0014)', push='2026-02-09 (F0014)', rel='not fetched', adopt='HF 30d downloads Z-Image-Turbo 609,489 (F0158); Z-Image 59,864 (F0086)',
  members='Z-Image, Z-Image-Turbo', handle='GH/HF Tongyi-MAI', notes='AA open-weights T2I Elo Z-Image Turbo 940 (W0009). Tongyi-MAI line, marketed apart from Qwen-Image.', src=['aa','ws','hforg'])
c(slug='fibo', name='FIBO', type='model', org='bria-ai', gh='Bria-AI/FIBO', hf='briaai/FIBO', status='open-weights', modality='image', bucket='model',
  lic='CC BY-NC 4.0 (repo LICENSE F0238; HF license_name bria-fibo linking CC BY-NC F0163)', arch='no/no (F0015)', push='2026-01-07 (F0015)', rel='not fetched',
  adopt='HF 30d downloads FIBO 702 (F0163); Fibo-Edit-1.5-turbo 2,383 (F0087)', members='FIBO, FIBO Lite, Fibo-1.5, Fibo-Edit (F0087)', handle='GH Bria-AI; HF briaai',
  notes='AA open-weights T2I Elo FIBO 879 (W0009).', src=['aa','hforg'])
c(slug='glm-image', name='GLM-Image', type='model', org='zhipu-z-ai', gh='zai-org/GLM-Image', hf='zai-org/GLM-Image', status='open', modality='image', bucket='model',
  lic='weights MIT (F0165); code Apache-2.0 (F0016)', arch='no/no (F0016)', push='2026-03-20 (F0016)', rel='not fetched', adopt='HF 30d downloads 8,011 (F0165)',
  members='GLM-Image; predecessor CogView4-6B (F0088)', handle='GH/HF zai-org', notes='AA open-weights T2I Elo 889 (W0009). Contested: SKU of `glm` head or its own line?', src=['aa','hforg'])
c(slug='ideogram', name='Ideogram', type='model', org='ideogram', gh='ideogram-oss/ideogram4', hf='ideogram-ai/ideogram-4-fp8', status='open-weights', modality='image', bucket='model',
  lic='weights "Ideogram 4 Non-Commercial" model agreement, gated (F0137, W0022); commercial use needs paid licence (W0022); code licence per W0045 Apache-2.0, repo LICENSE fetched (F0250)',
  arch='no/no (F0399)', push='2026-06-04 per ecosyste.ms (F0399); ungh pushedAt 2026-06-30 (F0230)', rel='not fetched', adopt='HF 30d downloads ideogram-4-fp8 58,610 (F0137); nf4 2,584 (F0138)',
  members='Ideogram 4.0 open weights (fp8, nf4); hosted API tiers', handle='GH ideogram-oss; HF ideogram-ai',
  notes='First open-weight Ideogram model, 9.3B, 2026-06-03 (W0020). AA open-weights T2I Elo 1010 (W0009).', src=['aa','ws'])
c(slug='ernie-image', name='ERNIE-Image', type='model', org='baidu', gh=None, hf='baidu/ERNIE-Image', status='open', modality='image', bucket='model',
  lic='Apache-2.0 (F0164)', arch='n/a (no GitHub repo fetched)', push='HF lastModified 2026-04-17 (F0164)', rel='not fetched',
  adopt='HF 30d downloads ERNIE-Image 990 (F0164); ERNIE-Image-Turbo 3,900 (F0111)', members='ERNIE-Image, ERNIE-Image-Turbo', handle='HF baidu',
  notes='AA open-weights T2I Elo Turbo 923 (W0009). Contested: SKU of `ernie` head?', src=['aa','hforg'])
c(slug='longcat-image', name='LongCat-Image', type='model', org='meituan', gh='meituan-longcat/LongCat-Image', hf='meituan-longcat/LongCat-Image', status='open', modality='image', bucket='model',
  lic='Apache-2.0 (F0021, F0092)', arch='no/no (F0021)', push='2026-04-02 (F0021)', rel='not fetched',
  adopt='HF 30d downloads LongCat-Image 13,815; Edit-Turbo 23,408 (F0092)', members='LongCat-Image, -Dev, -Edit, -Edit-Turbo', handle='GH/HF meituan-longcat',
  notes='AA open-weights T2I Elo 860 (W0009).', src=['aa','ws','hforg'])
c(slug='omnigen', name='OmniGen', type='model', org='vectorspacelab', gh='VectorSpaceLab/OmniGen2', hf='OmniGen2/OmniGen2', status='open', modality='image', bucket='model',
  lic='Apache-2.0 (F0017, F0089)', arch='no/no (F0017)', push='2026-03-20 (F0017)', rel='not fetched', adopt='HF 30d downloads 4,767 (F0089)',
  members='OmniGen, OmniGen2', handle='GH VectorSpaceLab; HF OmniGen2', notes='AA open-weights T2I Elo OmniGen V2 726 (W0009). Unified generation/editing; borderline with multimodal_models.', src=['aa','hforg'])
c(slug='infinity-image', name='Infinity', type='model', org='bytedance', gh='FoundationVision/Infinity', hf='FoundationVision/Infinity', status='open', modality='image', bucket='model',
  lic='MIT (F0019, F0144)', arch='no/no (F0019)', push='2026-04-16 (F0019)', rel='not fetched', adopt='HF 30d downloads 79 (F0144)',
  members='Infinity 2B/8B', handle='GH/HF FoundationVision', notes='AA open-weights T2I Elo Infinity 8B 873 (W0009). Org attributed as ByteDance by AA (W0009). Slug avoids the `infinity` storage head product. New org slug `bytedance` (non-Seed ByteDance teams); Q14.', src=['aa'])
c(slug='ming-image', name='Ming-Image', type='model', org='inclusion-ai', gh=None, hf='inclusionAI/Ming-Image-0.1-Design', status='open', modality='image', bucket='model',
  lic='MIT (F0145)', arch='n/a', push='HF created 2026-09-17, lastModified 2026-09-23 (F0145)', rel='not fetched', adopt='HF API reports 0 downloads (F0145)',
  members='Ming-Image-0.1-Design', handle='HF inclusionAI', notes='AA open-weights T2I #7, Elo 996 (W0009). Nine days old at fetch. Ming-Omni models belong to brief 2.', src=['aa'])
c(slug='nextstep', name='NextStep', type='model', org='stepfun', gh=None, hf='stepfun-ai/NextStep-1.1', status='open', modality='image', bucket='model',
  lic='Apache-2.0 (F0101)', arch='n/a', push='HF lastModified 2025-12-23 (F0101)', rel='not fetched', adopt='HF 30d downloads 1,453 (F0101)',
  members='NextStep-1, NextStep-1.1', handle='HF stepfun-ai', notes='Autoregressive T2I.', src=['hforg'])
c(slug='step1x-edit', name='Step1X-Edit', type='model', org='stepfun', gh='stepfun-ai/Step1X-Edit', hf=None, status='open', modality='image', bucket='model',
  lic='Apache-2.0 (F0373)', arch='no/no (F0373)', push='2026-04-29 (F0373)', rel='not fetched', adopt='GitHub stars 2,264 (F0373)',
  members='Step1X-Edit v1.0, v1p1, v1p2', handle='GH stepfun-ai', notes='Instruction image editor named among main open editors (W0065).', src=['ws'])

# ---------------- VIDEO MODELS ----------------
c(slug='wan', name='Wan', type='model', org='alibaba-cloud', gh='Wan-Video/Wan2.2', hf='Wan-AI/Wan2.1-T2V-1.3B-Diffusers', status='open', modality='video', bucket='model',
  lic='Apache-2.0 for every Wan 2.1/2.2 checkpoint fetched (F0093, F0149, F0162, F0369); Wan 2.5/2.6/2.7/3.0 closed, API-only (W0016, W0011, W0012; no Wan3 weights on HF F0191, F0192)',
  arch='no/no (F0023)', push='2026-09-21 (F0023)', rel='no GitHub release returned by ecosyste.ms (F0345)',
  adopt='HF 30d downloads Wan2.1-T2V-1.3B-Diffusers 264,951 (F0369); Wan2.2-TI2V-5B-Diffusers 159,486 (F0093)',
  members='Wan 2.1 (T2V/I2V/VACE), Wan 2.2 (T2V-A14B, I2V-A14B, TI2V-5B, S2V, Animate, Animate-2), Wan-Dancer (F0093, F0192)', handle='GH Wan-Video; HF Wan-AI',
  notes='Top closed video Elo is Wan 3.0 (1335, W0012). Current flagship closed; newest open drop Wan2.2-Animate-2 (2026-08-06, F0192).', src=['brief','aa','ws','topic','hforg'])
c(slug='hunyuan-video', name='HunyuanVideo', type='model', org='tencent', gh='Tencent-Hunyuan/HunyuanVideo', hf='tencent/HunyuanVideo-1.5', status='open-weights', modality='video', bucket='model',
  lic='Tencent Hunyuan Community License, EU/UK/South Korea excluded (F0168, F0122, F0123)', arch='no/no (F0024)', push='2026-06-29 (F0024); 1.5 repo 2026-04-10 (F0025)', rel='not fetched',
  adopt='HF 30d downloads 1.5: 1,193; v1: 1,269 (F0123, F0122); GitHub stars 12,550 (F0024)', members='HunyuanVideo, HunyuanVideo-I2V, HunyuanVideo 1.5 (8.3B, W0001)', handle='GH Tencent-Hunyuan; HF tencent',
  notes='Not on AA open-weights video boards as fetched (W0010, W0013).', src=['brief','ws','topic'])
c(slug='cogvideo', name='CogVideo', type='model', org='zhipu-z-ai', gh='zai-org/CogVideo', hf='zai-org/CogVideoX-5b', status='open-weights', modality='video', bucket='model',
  lic='CogVideoX License: academic free; commercial needs registration, 1M visits/month cap (F0171); CogVideoX-2b Apache-2.0 (F0088); code Apache-2.0 (F0026)',
  arch='no/no (F0026)', push='2025-11-04 (F0026)', rel='not fetched', adopt='HF 30d downloads CogVideoX-5b 20,115; 2b 17,232 (F0088)', members='CogVideo, CogVideoX 2b/5b/5b-I2V, CogVideoX1.5', handle='GH/HF zai-org',
  notes='', src=['brief','ws','topic','hforg'])
c(slug='ltx', name='LTX', type='model', org='lightricks', gh='Lightricks/LTX-2', hf='Lightricks/LTX-2.5', status='open-weights', modality='video', bucket='model',
  lic='LTX-2.x Community License (2026-08-11), revenue threshold USD 10M for free commercial use (F0180, F0150); LTX-Video repo Apache-2.0 (F0240, F0027)',
  arch='no/no (F0028)', push='2026-08-26 (F0028)', rel='no GitHub release returned by ecosyste.ms (F0344)',
  adopt='HF 30d downloads LTX-2.5 1,604,804 (F0150); LTX-2.3 1,098,602; LTX-Video 773,634 (F0094)', members='LTX-Video 0.9.x, LTX-2, LTX-2.3, LTX-2.5 (+ fp8/nvfp4, IC-LoRAs) (F0094)',
  handle='GH/HF Lightricks', notes='Open-weights video board: LTX-2.5 Fast Elo 1055 (W0010); 1218 no-audio (W0012).', src=['brief','aa','ws','topic','hforg'])
c(slug='mochi', name='Mochi', type='model', org='genmo', gh='genmoai/mochi', hf='genmo/mochi-1-preview', status='open', modality='video', bucket='model',
  lic='Apache-2.0 (F0029, F0155)', arch='no/no (F0029)', push='2025-11-14 (F0029)', rel='not fetched', adopt='HF 30d downloads 7,819 (F0155)', members='Mochi 1 preview', handle='GH genmoai; HF genmo', notes='', src=['brief','ws'])
c(slug='open-sora', name='Open-Sora', type='model', org='hpc-ai-tech', gh='hpcaitech/Open-Sora', hf='hpcai-tech/Open-Sora-v2', status='open', modality='video', bucket='model',
  lic='Apache-2.0 (F0030, F0157)', arch='no/no (F0030)', push='2026-04-09 (F0030)', rel='v1.3, 2025-02-21 (F0347)', adopt='HF 30d downloads Open-Sora-v2 1,189 (F0157); GitHub stars 29,836 (F0030)',
  members='Open-Sora 1.x, 2.0', handle='GH hpcaitech; HF hpcai-tech', notes='Org already on map via colossal-ai tail row.', src=['brief'])
c(slug='magi', name='MAGI', type='model', org='sand-ai', gh='SandAI-org/MAGI-1', hf='sand-ai/MAGI-2-preview', status='open', modality='video', bucket='model',
  lic='Apache-2.0 (F0031, F0126, F0127, F0202; W0017)', arch='no/no (F0031)', push='2026-06-17 MAGI-1; 2026-08-06 MAGI-2-preview (F0031, F0202)', rel='not fetched',
  adopt='HF API reports 0 downloads (F0126, F0127); GitHub stars 3,788 (F0031)', members='MAGI-1, MAGI-2-preview (114B MoE, W0017)', handle='GH SandAI-org; HF sand-ai',
  notes='Open-weights I2V board #2, Elo 1094 (W0013).', src=['aa','ws'])
c(slug='skyreels', name='SkyReels', type='model', org='skywork', gh='SkyworkAI/SkyReels-V2', hf='Skywork/SkyReels-V2-T2V-14B-720P', status='open-weights', modality='video', bucket='model',
  lic='Skywork community licence, custom terms (F0174, F0267, F0161)', arch='no/no (F0032)', push='2026-01-29 (F0032)', rel='not fetched', adopt='HF 30d downloads 1,407 (F0161); V3-A2V 1,110 (F0098)',
  members='SkyReels V1, V2, V3 (open); V4 closed (W0012)', handle='GH SkyworkAI; HF Skywork', notes='', src=['aa','ws','hforg'])
c(slug='kandinsky', name='Kandinsky', type='model', org='kandinsky-lab', gh='kandinskylab/kandinsky-5', hf=None, status='open', modality='video', bucket='model',
  lic='MIT per repo metadata and HF card (F0033, F0142); a search summary says Apache-2.0 (W0066), unresolved', arch='no/no (F0033)', push='2026-03-31 (F0033)', rel='not fetched',
  adopt='GitHub stars 736 (F0033); HF reports 0 downloads (F0142)', members='Kandinsky 5.0 Video Lite/Pro, Image Lite (W0066); earlier Kandinsky 2/3 (W0038)', handle='GH/HF kandinskylab',
  notes='Backed by Sber (W0066). Covers image and video.', src=['ws','topic'])
c(slug='step-video', name='Step-Video', type='model', org='stepfun', gh='stepfun-ai/Step-Video-T2V', hf='stepfun-ai/stepvideo-t2v', status='open', modality='video', bucket='model',
  lic='MIT (F0212, F0360)', arch='no/no (F0212)', push='2025-03-17 (F0212)', rel='not fetched', adopt='HF 30d downloads 80 (F0360)', members='Step-Video-T2V, -TI2V', handle='GH/HF stepfun-ai', notes='Dormant since 2025-03.', src=['recall-lead'])
c(slug='minimax-hailuo', name='MiniMax Hailuo (H3)', type='model', org='minimax', gh='MiniMax-AI/MiniMax-H3', hf='MiniMaxAI/MiniMax-H3', status='open-weights', modality='video', bucket='model',
  lic='MiniMax H3 Community License; excluded territories EU, UK, South Korea and the USA (F0181, F0136)', arch='no/no (F0221)', push='2026-08-15 (F0221)', rel='not fetched',
  adopt='HF 30d downloads 3,657,004 (F0136)', members='MiniMax-H3 33B, H3-Regenerate-2K (W0015); closed Hailuo API tiers', handle='GH MiniMax-AI; HF MiniMaxAI',
  notes='#1 open-weights video on AA: T2V Elo 1220 with audio, 1302 no-audio (W0010, W0012). Distinct from `minimax` LLM head row. Scorer note: 3,657,004 30d downloads is the largest in the set for a model released ~6 weeks before fetch (created 2026-07-28, F0136); worth a second read before banding.', src=['aa','ws'])
c(slug='longcat-video', name='LongCat-Video', type='model', org='meituan', gh=None, hf='meituan-longcat/LongCat-Video', status='open', modality='video', bucket='model',
  lic='MIT (F0092)', arch='n/a', push='HF lastModified 2025-10-29 (F0092)', rel='not fetched', adopt='HF 30d downloads 1,710 (F0092)', members='LongCat-Video, LongCat-Video-Avatar-1.5 (F0092)', handle='HF meituan-longcat',
  notes='Same vendor brand as longcat-image; one row or two is Q9.', src=['hforg'])
c(slug='helios', name='Helios', type='model', org='pku-yuan-group', gh='PKU-YuanGroup/Helios', hf='BestWishYsh/Helios-Distilled', status='open', modality='video', bucket='model',
  lic='Apache-2.0 (F0207, F0359)', arch='no/no (F0207)', push='2026-08-24 (F0207)', rel='not fetched', adopt='HF 30d downloads 1,374 (F0359)',
  members='Helios 14B real-time long video (F0307)', handle='GH PKU-YuanGroup; HF BestWishYsh', notes='2026 release (arXiv 2603.04379, F0307).', src=['topic'])
c(slug='stable-video-diffusion', name='Stable Video Diffusion', type='model', org='stability-ai', gh=None, hf='stabilityai/stable-video-diffusion-img2vid-xt', status='open-weights', modality='video', bucket='model',
  lic='stable-video-diffusion-community (F0356)', arch='n/a', push='HF lastModified 2024-07-10 (F0356)', rel='not fetched', adopt='HF 30d downloads img2vid-xt 249,578 (F0356); img2vid 86,202 (F0078)',
  members='SVD img2vid, img2vid-xt', handle='HF stabilityai', notes='Dormant since 2024.', src=['hforg'])
c(slug='liveportrait', name='LivePortrait', type='model', org='kuaishou', gh='KlingAIResearch/LivePortrait', hf='KlingTeam/LivePortrait', status='open', modality='video', bucket='model',
  lic='MIT, copyright Kuaishou Visual Generation and Interaction Center (F0241, F0351)', arch='no/no (F0196)', push='2026-06-01 (F0196)', rel='no GitHub release returned by ecosyste.ms (F0349)',
  adopt='HF 30d downloads 10,340 (F0351); GitHub stars 19,114 (F0196)', members='LivePortrait (humans, animals)', handle='GH KlingAIResearch; HF KlingTeam', notes='Portrait animation; scope Q7.', src=['topic'])
c(slug='latentsync', name='LatentSync', type='model', org='bytedance', gh='bytedance/LatentSync', hf='ByteDance/LatentSync-1.6', status='open-weights', modality='video', bucket='model',
  lic='weights openrail++ (F0355); code Apache-2.0 (F0197)', arch='no/no (F0197)', push='2025-06-20 (F0197)', rel='not fetched', adopt='HF 30d downloads 1.6: 200,128; 1.5: 70,958 (F0113)',
  members='LatentSync 1.5, 1.6', handle='GH bytedance; HF ByteDance', notes='Lip-sync video; scope Q7. New org slug `bytedance`; Q14.', src=['hforg'])

# ---------------- 3D MODELS ----------------
c(slug='trellis', name='TRELLIS', type='model', org='microsoft', gh='microsoft/TRELLIS', hf='microsoft/TRELLIS-image-large', status='open', modality='3d', bucket='model',
  lic='MIT (F0034, F0035, F0366, F0151)', arch='no/no (F0034)', push='2026-06-26 TRELLIS; 2026-07-10 TRELLIS.2 (F0034, F0035)', rel='no release returned (ungh 404, F0332)',
  adopt='HF 30d downloads TRELLIS-image-large 2,118,600 (F0366); TRELLIS.2-4B 1,724,957 (F0151)', members='TRELLIS (image/text large), TRELLIS.2-4B', handle='GH microsoft; HF microsoft', notes='', src=['brief','ws','topic','hforg'])
c(slug='hunyuan-3d', name='Hunyuan3D', type='model', org='tencent', gh='Tencent-Hunyuan/Hunyuan3D-2', hf='tencent/Hunyuan3D-2', status='open-weights', modality='3d', bucket='model',
  lic='Tencent Hunyuan 3D Community License, EU/UK/South Korea excluded (F0172, F0365); 2.5/3.0/3.1 API-only (W0064)', arch='no/no (F0036)', push='2025-10-28 (F0036)', rel='not fetched',
  adopt='HF 30d downloads Hunyuan3D-2 108,234; 2.1 54,794; 2mini 33,588 (F0085)', members='Hunyuan3D 2.0, 2mini, 2mv, 2.1', handle='GH Tencent-Hunyuan; HF tencent', notes='Current flagship closed.', src=['brief','ws','topic','hforg'])
c(slug='step1x-3d', name='Step1X-3D', type='model', org='stepfun', gh='stepfun-ai/Step1X-3D', hf='stepfun-ai/Step1X-3D', status='open', modality='3d', bucket='model',
  lic='Apache-2.0 (F0038, F0129)', arch='no/no (F0038)', push='2025-09-08 (F0038)', rel='not fetched', adopt='HF API reports 0 downloads (F0129); GitHub stars 870 (F0038)', members='Step1X-3D', handle='GH/HF stepfun-ai', notes='', src=['ws'])
c(slug='triposg', name='TripoSG', type='model', org='vast-ai', gh='VAST-AI-Research/TripoSG', hf='VAST-AI/TripoSG', status='open', modality='3d', bucket='model',
  lic='MIT (F0039, F0159)', arch='no/no (F0039)', push='2025-04-18 (F0039)', rel='not fetched', adopt='HF 30d downloads 4,986 (F0159)', members='TripoSG', handle='GH VAST-AI-Research; HF VAST-AI', notes='', src=['ws','topic'])
c(slug='triposr', name='TripoSR', type='model', org='vast-ai', gh='VAST-AI-Research/TripoSR', hf='stabilityai/TripoSR', status='open', modality='3d', bucket='model',
  lic='MIT (F0040, F0160)', arch='no/no (F0040)', push='2026-06-04 (F0040)', rel='not fetched', adopt='HF 30d downloads 201,115 (F0160)', members='TripoSR (VAST with Stability AI; weights on stabilityai HF)', handle='GH VAST-AI-Research; HF stabilityai',
  notes='Joint VAST/Stability release; org attribution Q.', src=['ws','hforg'])
c(slug='stable-fast-3d', name='Stable Fast 3D', type='model', org='stability-ai', gh='Stability-AI/stable-fast-3d', hf='stabilityai/stable-fast-3d', status='open-weights', modality='3d', bucket='model',
  lic='Stability AI Community License (F0247, F0131)', arch='no/no (F0041)', push='2025-01-22 (F0041)', rel='not fetched', adopt='HF 30d downloads 14,447 (F0131)', members='SF3D', handle='GH Stability-AI; HF stabilityai', notes='', src=['hforg'])
c(slug='spar3d', name='Stable Point Aware 3D', type='model', org='stability-ai', gh='Stability-AI/stable-point-aware-3d', hf='stabilityai/stable-point-aware-3d', status='open-weights', modality='3d', bucket='model',
  lic='stabilityai-ai-community (F0357)', arch='no/no (F0042)', push='2025-05-05 (F0042)', rel='not fetched', adopt='HF 30d downloads 8,780 (F0357)', members='SPAR3D', handle='GH Stability-AI; HF stabilityai', notes='', src=['hforg'])
c(slug='instantmesh', name='InstantMesh', type='model', org='tencent', gh='TencentARC/InstantMesh', hf='TencentARC/InstantMesh', status='open', modality='3d', bucket='model',
  lic='Apache-2.0 (F0043, F0358)', arch='no/no (F0043)', push='2025-01-03 (F0043)', rel='not fetched', adopt='HF 30d downloads 18,045 (F0358)', members='InstantMesh', handle='GH/HF TencentARC', notes='Dormant since 2025-01.', src=['ws'])
c(slug='cube', name='Cube', type='model', org='roblox', gh='Roblox/cube', hf='Roblox/cube3d-v0.1', status='open-weights', modality='3d', bucket='model',
  lic='CUBE3D Research-Only RAIL-MS licence (F0173); HF label openrail (F0128)', arch='no/no (F0044)', push='2026-05-28 (F0044)', rel='not fetched', adopt='HF API reports 0 downloads (F0128); GitHub stars 1,256 (F0044)',
  members='Cube3d-v0.1', handle='GH/HF Roblox', notes='Research-only.', src=['topic'])
c(slug='sam-3d', name='SAM 3D', type='model', org='meta', gh='facebookresearch/sam-3d-objects', hf='facebook/sam-3d-objects', status='open-weights', modality='3d', bucket='model',
  lic='SAM License (custom, 2025-11-19) (F0246); HF gated manual (F0353)', arch='no/no (F0216)', push='2026-06-02 (F0216)', rel='not fetched', adopt='HF 30d downloads 3,522 (F0353)',
  members='SAM 3D Objects', handle='GH facebookresearch; HF facebook', notes='Contested with classic_ml_cv (SAM family).', src=['recall-lead'])
c(slug='partcrafter', name='PartCrafter', type='model', org='wgsxm', gh='wgsxm/PartCrafter', hf='wgsxm/PartCrafter', status='open', modality='3d', bucket='model',
  lic='MIT (F0217, F0361)', arch='no/no (F0217)', push='2025-09-19 (F0217)', rel='not fetched', adopt='HF 30d downloads 658 (F0361)', members='PartCrafter', handle='GH/HF wgsxm', notes='Academic release.', src=['topic'])

# ---------------- AUDIO / MUSIC / SFX MODELS ----------------
c(slug='stable-audio', name='Stable Audio', type='model', org='stability-ai', gh=None, hf='stabilityai/stable-audio-3-medium', status='open-weights', modality='audio', bucket='model',
  lic='weights "stable-audio-community" licence (F0363, F0130)', arch='n/a (no GitHub repo declared; code is the stable-audio-tools row)', push='HF lastModified 2026-06-16 (F0363)', rel='not fetched',
  adopt='HF 30d downloads Stable Audio 3 Medium 81,781 (F0363); Open 1.0 20,764 (F0130)', members='Stable Audio Open 1.0, Open Small, Stable Audio 3 Medium; API Stable Audio 3 Large/2.5 (W0033)',
  handle='HF stabilityai', notes='Model row; the stable-audio-tools library is its own row (as musicgen/audiocraft). AA instrumental Elo Stable Audio 3 Medium 1000 (W0033).', src=['brief','aa','hforg'])
c(slug='musicgen', name='MusicGen', type='model', org='meta', gh=None, hf='facebook/musicgen-medium', status='open-weights', modality='audio', bucket='model',
  lic='CC BY-NC 4.0 (F0153)', arch='n/a', push='HF lastModified 2023-11-17 (F0153)', rel='n/a', adopt='HF 30d downloads musicgen-medium 1,947,422; small 142,904; large 89,340 (F0104)',
  members='MusicGen small/medium/large (F0104)', handle='HF facebook', notes='Model row; the AudioCraft library is its own row. AA instrumental Elo 882 (W0033).', src=['brief','aa','ws','hforg'])
c(slug='ace-step', name='ACE-Step', type='model', org='ace-step', gh='ace-step/ACE-Step-1.5', hf='ACE-Step/Ace-Step1.5', status='open', modality='audio', bucket='model',
  lic='MIT for 1.5 (F0048, F0154); v1 Apache-2.0 (F0047)', arch='no/no (F0048)', push='2026-09-03 (F0048)', rel='v0.1.8, 2026-05-18 (F0329)', adopt='HF 30d downloads Ace-Step1.5 59,314 (F0154)',
  members='ACE-Step v1 3.5B, ACE-Step 1.5 (base/sft/turbo/XL) (F0105)', handle='GH ace-step; HF ACE-Step', notes='', src=['brief','ws','hforg'])
c(slug='yue', name='YuE', type='model', org='m-a-p', gh='multimodal-art-projection/YuE', hf='m-a-p/YuE2-3B', status='open-weights', modality='audio', bucket='model',
  lic='YuE2 weights CC BY-NC 4.0 (F0372, F0187); YuE v1 weights Apache-2.0 (F0133); code Apache-2.0 (F0049)', arch='no/no (F0049)', push='2026-09-23 (F0049)', rel='yue2-v0.1.6, 2026-09-09 (F0330)',
  adopt='HF 30d downloads YuE2-3B 25,798 (F0372); YuE-s1-7B 8,430 (F0133)', members='YuE s1/s2 (v1), YuE2-3B', handle='GH multimodal-art-projection; HF m-a-p', notes='Licence tightened from Apache (v1) to NC (v2).', src=['brief','ws','topic','hforg'])
c(slug='heartmula', name='HeartMuLa', type='model', org='heartmula', gh='HeartMuLa/heartlib', hf='HeartMuLa/HeartMuLa-oss-3B', status='open', modality='audio', bucket='model',
  lic='Apache-2.0 (F0050, F0146)', arch='no/no (F0050)', push='2026-09-26 (F0050)', rel='no release returned (ungh 404, F0331)', adopt='HF 30d downloads 791 (F0146); happy-new-year 2,711 (F0107)',
  members='HeartMuLa-oss-3B, RL-oss-3B, HeartCodec', handle='GH/HF HeartMuLa', notes='2026 release (W0004).', src=['ws'])
c(slug='songgeneration', name='SongGeneration', type='model', org='tencent-ai-lab', gh='tencent-ailab/SongGeneration', hf=None, status='open-weights', modality='audio', bucket='model',
  lic='GitHub label "other" (F0051); LICENSE text fetch did not complete (F0186 404 at /LICENSE); HF metadata fetch returned 401 (F0134)', arch='no/no (F0051)', push='2026-03-12 (F0051)', rel='not fetched',
  adopt='GitHub stars 1,529 (F0051)', members='SongGeneration (LeVo)', handle='GH tencent-ailab', notes='Licence text still unread; status tag provisional.', src=['recall-lead'])
c(slug='diffrhythm', name='DiffRhythm', type='model', org='aslp-lab', gh='ASLP-lab/DiffRhythm', hf='ASLP-lab/DiffRhythm-1_2', status='open', modality='audio', bucket='model',
  lic='Apache-2.0 per repo (F0052); HF card has no licence field (F0135)', arch='no/no (F0052)', push='2025-11-27 (F0052)', rel='not fetched', adopt='HF 30d downloads 157 (F0135)', members='DiffRhythm 1.0, 1.2', handle='GH/HF ASLP-lab', notes='', src=['recall-lead'])
c(slug='minimax-music', name='MiniMax Music', type='model', org='minimax', gh=None, hf='MiniMaxAI/MiniMax-Music3', status='open-weights', modality='audio', bucket='model',
  lic='MiniMax-Music3 Community License: MIT-style grant plus attribution and a separate authorization above USD 20M yearly revenue (F0188)', arch='n/a', push='HF lastModified 2026-08-14 (F0190)', rel='not fetched',
  adopt='HF 30d downloads 10,096 (F0190)', members='MiniMax Music 3.0 open weights; API Music 2.x (W0032)', handle='HF MiniMaxAI', notes='Released 2026-08-13 (W0004). AA vocal Elo 1000 (W0032).', src=['ws','aa'])
c(slug='mmaudio', name='MMAudio', type='model', org='hkchengrex', gh='hkchengrex/MMAudio', hf='hkchengrex/MMAudio', status='open-weights', modality='audio', bucket='model',
  lic='code MIT (F0053); weights CC BY-NC 4.0 (F0132)', arch='no/no (F0053)', push='2026-02-23 (F0053)', rel='not fetched', adopt='HF API reports 0 downloads (F0132); GitHub stars 2,267 (F0053)',
  members='MMAudio S/M/L', handle='GH/HF hkchengrex', notes='Video-to-audio (CVPR 2025) from UIUC and Sony AI (W0035).', src=['ws'])
c(slug='thinksound', name='ThinkSound', type='model', org='alibaba-cloud', gh='QwenAudio/ThinkSound', hf='FunAudioLLM/ThinkSound', status='open', modality='audio', bucket='model',
  lic='Apache-2.0 per README (F0270) and HF card (F0352); no LICENSE file at repo root (F0249, F0258, F0263)', arch='no/no (F0199)', push='2026-04-03 (F0199)', rel='not fetched',
  adopt='HF API reports 0 downloads (F0352); GitHub stars 1,380 (F0199)', members='ThinkSound', handle='GH QwenAudio; HF FunAudioLLM', notes='Tongyi Lab (W0035).', src=['ws'])
c(slug='hunyuanvideo-foley', name='HunyuanVideo-Foley', type='model', org='tencent', gh='Tencent-Hunyuan/HunyuanVideo-Foley', hf='tencent/HunyuanVideo-Foley', status='open-weights', modality='audio', bucket='model',
  lic='tencent-hunyuan-community (F0125)', arch='no/no (F0055)', push='2025-09-28 (F0055)', rel='not fetched', adopt='HF 30d downloads 455 (F0125)', members='HunyuanVideo-Foley', handle='GH Tencent-Hunyuan; HF tencent', notes='', src=['ws'])
c(slug='foleycrafter', name='FoleyCrafter', type='model', org='open-mmlab', gh='open-mmlab/FoleyCrafter', hf=None, status='open', modality='audio', bucket='model',
  lic='Apache-2.0 (F0215)', arch='no/no (F0215)', push='2026-06-15 (F0215)', rel='not fetched', adopt='GitHub stars 664 (F0215)', members='FoleyCrafter', handle='GH open-mmlab', notes='', src=['ws'])

# ---------------- SOFTWARE: media-generation apps, UIs, engines ----------------
def t(**k): k.setdefault('bucket','tool'); k.setdefault('type','software'); k.setdefault('hf',None); c(**k)
t(slug='comfyui', name='ComfyUI', org='comfy-org', gh='Comfy-Org/ComfyUI', status='open', modality='tool', lic='GPL-3.0 (F0176)', arch='no/no (F0076)', push='2026-09-25 (F0076)', rel='v0.37.0, 2026-09-21 (F0308)',
  adopt='GitHub stars 134,880 (F0076); no first-party package fetched', members='ComfyUI core (moved from comfyanonymous, F0056 404 on old name)', handle='GH Comfy-Org', notes='', src=['brief','ws','topic'])
t(slug='stable-diffusion-webui', name='Stable Diffusion web UI (AUTOMATIC1111)', org='automatic1111', gh='AUTOMATIC1111/stable-diffusion-webui', status='open', modality='tool', lic='AGPL-3.0 (F0057)', arch='no/no (F0057)',
  push='2026-03-02 (F0057)', rel='v1.10.1, 2025-02-09 (F0312)', adopt='GitHub stars 165,027 (F0057)', members='', handle='GH AUTOMATIC1111', notes='Described as superseded by Forge (W0007).', src=['brief','ws','topic'])
t(slug='forge', name='Stable Diffusion WebUI Forge', org='lllyasviel', gh='lllyasviel/stable-diffusion-webui-forge', status='open', modality='tool', lic='AGPL-3.0 (F0058)', arch='no/no (F0058)', push='2025-07-31 (F0058)', rel='"latest", 2024-02-05 (F0313)',
  adopt='GitHub stars 13,032 (F0058)', members='', handle='GH lllyasviel', notes='Community forks reForge and Forge Classic parked.', src=['brief','ws'])
t(slug='invokeai', name='InvokeAI', org='invoke-ai', gh='invoke-ai/InvokeAI', pypi='invokeai', status='open', modality='tool', lic='Apache-2.0 (F0059, F0275)', arch='no/no (F0059)', push='2026-09-21 (F0059)', rel='v6.14.1, 2026-09-06 (F0309)',
  adopt='PyPI invokeai 23,263/month (F0275)', members='', handle='GH invoke-ai', notes='PyPI project_urls point to invoke-ai/InvokeAI (F0305); install doc says to install the invokeai package (F0407).', src=['brief','ws','topic'])
t(slug='fooocus', name='Fooocus', org='lllyasviel', gh='lllyasviel/Fooocus', status='open', modality='tool', lic='GPL-3.0 (F0060)', arch='no/no (F0060)', push='2025-12-01 (F0060)', rel='v2.5.5, 2024-08-12 (F0314)', adopt='GitHub stars 53,101 (F0060)', members='', handle='GH lllyasviel', notes='', src=['brief'])
t(slug='sdnext', name='SD.Next', org='vladmandic', gh='vladmandic/sdnext', status='open', modality='tool', lic='Apache-2.0 (F0061)', arch='no/no (F0061)', push='2026-09-23 (F0061)', rel='no GitHub release returned by ecosyste.ms (F0341); ungh fetch did not complete (F0310)',
  adopt='GitHub stars 7,346 (F0061)', members='', handle='GH vladmandic', notes='', src=['brief','ws'])
t(slug='swarmui', name='SwarmUI', org='mcmonkeyprojects', gh='mcmonkeyprojects/SwarmUI', status='open', modality='tool', lic='MIT (F0062)', arch='no/no (F0062)', push='2026-09-22 (F0062)', rel='0.9.8-Beta, 2026-02-06 (F0311)', adopt='GitHub stars 4,586 (F0062)', members='', handle='GH mcmonkeyprojects', notes='Runs on a ComfyUI backend (W0007).', src=['brief','ws'])
t(slug='krita-ai-diffusion', name='Krita AI Diffusion', org='acly', gh='Acly/krita-ai-diffusion', status='open', modality='tool', lic='GPL-3.0 (F0065)', arch='no/no (F0065)', push='2026-09-23 (F0065)', rel='v1.51.1, 2026-06-05 (F0342)', adopt='GitHub stars 10,631 (F0065)', members='', handle='GH Acly', notes='', src=['topic'])
t(slug='stability-matrix', name='Stability Matrix', org='lykos-ai', gh='LykosAI/StabilityMatrix', status='open', modality='tool', lic='AGPL-3.0 (F0074)', arch='no/no (F0074)', push='2026-09-16 (F0074)', rel='v2.16.4, 2026-09-16 (F0316)', adopt='GitHub stars 8,837 (F0074)', members='', handle='GH LykosAI', notes='Package manager / launcher for SD UIs (W0041).', src=['topic'])
t(slug='easy-diffusion', name='Easy Diffusion', org='easydiffusion', gh='easydiffusion/easydiffusion', status='source-available', modality='tool', lic='custom licence: MIT-style Section I plus Section II restricted uses (F0237)', arch='no/no (F0206)', push='2026-09-11 (F0206)', rel='v3.0.16, 2026-03-31 (F0323)',
  adopt='GitHub stars 10,462 (F0206); PyPI sdkit (its engine, easydiffusion/sdkit) 34,063/month (F0293), not declared', members='', handle='GH easydiffusion', notes='', src=['recall-lead'])
t(slug='diffusionbee', name='DiffusionBee', org='divamgupta', gh='divamgupta/diffusionbee-stable-diffusion-ui', status='open', modality='tool', lic='AGPL-3.0 (F0204)', arch='no/no (F0204)', push='2024-10-30 (F0204)', rel='2.5.3, 2024-08-14 (F0324)', adopt='GitHub stars 13,585 (F0204)', members='', handle='GH divamgupta', notes='Dormant since 2024-10.', src=['topic'])
t(slug='dream-textures', name='Dream Textures', org='carson-katri', gh='carson-katri/dream-textures', status='open', modality='tool', lic='GPL-3.0 (F0223)', arch='no/no (F0223)', push='2026-09-17 (F0223)', rel='0.4.1, 2024-08-26 (F0325)', adopt='GitHub stars 8,206 (F0223)', members='', handle='GH carson-katri', notes='Blender add-on.', src=['topic'])
t(slug='wan2gp', name='WanGP', org='deepbeepmeep', gh='deepbeepmeep/Wan2GP', status='source-available', modality='tool', lic='WanGP Community License 2.0: free use, no resale/SaaS/white-label without a commercial licence (F0185)', arch='no / FORK=true per ecosyste.ms (F0066)', push='2026-09-18 (F0066)',
  rel='no release returned (ungh 404, F0326)', adopt='GitHub stars 9,510 (F0066)', members='', handle='GH deepbeepmeep', notes='Flagged as a GitHub fork; low-VRAM video app.', src=['recall-lead'])
t(slug='framepack', name='FramePack', org='lllyasviel', gh='lllyasviel/FramePack', status='open', modality='tool', lic='Apache-2.0 (F0068)', arch='no/no (F0068)', push='2025-10-16 (F0068)', rel='"windows", 2025-04-18 (F0348)', adopt='GitHub stars 17,264 (F0068)', members='', handle='GH lllyasviel', notes='Next-frame video method + desktop app.', src=['recall-lead'])
t(slug='stable-diffusion-cpp', name='stable-diffusion.cpp', org='leejet', gh='leejet/stable-diffusion.cpp', status='open', modality='tool', lic='MIT (F0067)', arch='no/no (F0067)', push='2026-09-19 (F0067)', rel='master-920-2f88688, 2026-09-25 (F0317)',
  adopt='GitHub stars 7,022 (F0067); third-party binding stable-diffusion-cpp-python 2,600/month (F0294), not declared', members='', handle='GH leejet', notes='Contested with inference_code.', src=['recall-lead'])
t(slug='xdit', name='xDiT', org='xdit-project', gh='xdit-project/xDiT', pypi='xfuser', status='open', modality='tool', lic='Apache-2.0 (F0070)', arch='no/no (F0070)', push='2026-09-18 (F0070)', rel='0.7.0, 2026-09-25 (F0320)',
  adopt='PyPI xfuser 23,947/month (F0278)', members='', handle='GH xdit-project', notes='PyPI homepage is the xDiT repo (F0306); README: pip install xfuser (F0402). Contested with inference_code.', src=['recall-lead'])
t(slug='lightx2v', name='LightX2V', org='modeltc', gh='ModelTC/LightX2V', status='open', modality='tool', lic='Apache-2.0 (F0073)', arch='no/no (F0073)', push='2026-09-25 (F0073)', rel='0.5.0, 2026-09-10 (F0319)', adopt='GitHub stars 2,858 (F0073); no PyPI package found (F0285)', members='', handle='GH ModelTC', notes='Contested with inference_code.', src=['recall-lead'])
t(slug='fastvideo', name='FastVideo', org='hao-ai-lab', gh='hao-ai-lab/FastVideo', pypi='fastvideo', status='open', modality='tool', lic='Apache-2.0 (F0072, F0279)', arch='no/no (F0072)', push='2026-09-25 (F0072)', rel='v0.2.0, 2026-06-04 (F0321)', adopt='PyPI fastvideo 1,332/month (F0279)', members='', handle='GH hao-ai-lab', notes='README: pip install fastvideo (F0403). Contested with inference_code.', src=['recall-lead'])
t(slug='diffsynth-studio', name='DiffSynth-Studio', org='modelscope-alibaba', gh='modelscope/DiffSynth-Studio', status='open', modality='tool', lic='Apache-2.0 (F0069, F0280)', arch='no/no (F0069)', push='2026-09-21 (F0069)', rel='v1.1.9, 2025-11-18 (F0322); PyPI 2.0.17, 2026-07-14 (F0280)',
  adopt='GitHub stars 13,156 (F0069); PyPI diffsynth 5,432/month (F0280) not declared: README documents only a source install (F0404)', members='', handle='GH modelscope', notes='PyPI author ModelScope Team (F0303). Contested with ml_frameworks/finetuning_code.', src=['recall-lead'])
t(slug='stable-audio-tools', name='stable-audio-tools', org='stability-ai', gh='Stability-AI/stable-audio-tools', pypi='stable-audio-tools', status='open', modality='tool', lic='MIT (F0045, F0277)', arch='no/no (F0045)', push='2026-09-18 (F0045)', rel='no release returned (ungh 404, F0327); PyPI 0.0.20, 2026-05-20 (F0277)',
  adopt='PyPI stable-audio-tools 102,734/month (F0277)', members='training/inference library for Stable Audio models', handle='GH Stability-AI', notes='PyPI author Stability AI (F0302); README documents pip install "stable-audio-tools[train]" (F0405).', src=['brief'])
t(slug='audiocraft', name='AudioCraft', org='meta', gh='facebookresearch/audiocraft', pypi='audiocraft', status='open', modality='tool', lic='MIT code (F0046, F0276)', arch='no/no (F0046)', push='2026-03-03 (F0046)', rel='no release returned (ungh 404, F0328); PyPI 1.3.0, 2024-06-03 (F0276)',
  adopt='PyPI audiocraft 9,695/month (F0276)', members='library for MusicGen, AudioGen, EnCodec', handle='GH facebookresearch', notes='Library row; the MusicGen weights are their own row. README: pip install -U audiocraft (F0401).', src=['brief'])

# ---------------- CLOSED FRONTIER COMPARATORS (ADR-005) ----------------
def z(**k): k.update(bucket='closed', status='closed', type='model', gh=None, hf=None, arch='n/a', push='n/a', rel='see notes', adopt='none: hosted, no download channel; AA Elo in notes'); k.setdefault('members',''); c(**k)
z(slug='gpt-image', name='GPT Image', org='openai', home='https://developers.openai.com/api/docs/models', modality='image', lic='proprietary API (hosted-only product per vendor page / arena listing: F0384, W0051)', handle='openai',
  members='GPT-Image-2.5 Sunburst, Flare (W0051); GPT Image 2, 1.5 (W0011)', notes='AA T2I #1 Elo 1196 (W0011).', src=['brief','aa'])
z(slug='nano-banana', name='Nano Banana (Gemini Image)', org='google', home='https://deepmind.google/models/gemini-image/', modality='image', lic='proprietary API (hosted-only product per vendor page / arena listing: F0383, W0053)', handle='google',
  members='Nano Banana 2 (Gemini 3.1 Flash Image), Nano Banana 2 Lite, Nano Banana Pro (W0053, W0011)', notes='AA T2I Elo 1123 (W0011). Brief lead "Imagen" not separately verified (parked).', src=['brief','aa'])
z(slug='midjourney', name='Midjourney', org='midjourney', home='https://www.midjourney.com', modality='image', lic='proprietary service (hosted-only product per vendor page / arena listing: F0374, W0052)', handle='midjourney',
  members='V8.1 alpha released 2026-04-14 (W0052); V8.0 alpha 2026-03-17 and V8.2 alpha per a search summary (W0024, not vendor-confirmed)', notes='Homepage 200 (F0374). Not in AA T2I top 25 as fetched (W0011); kept as the best-known closed image service, brief lead.', src=['brief','ws'])
z(slug='seedream', name='Seedream', org='bytedance-seed-volcano-engine', home='https://seed.bytedance.com/en/seedream', modality='image', lic='proprietary API (hosted-only product per vendor page / arena listing: F0377, W0011)', handle='bytedance-seed-volcano-engine',
  members='Seedream 4.0, 4.5, 5.0 Pro (W0011)', notes='AA T2I Elo 5.0 Pro 1078 (W0011). Vendor page redirected, not followed (W0057).', src=['aa'])
z(slug='veo', name='Veo', org='google', home='https://deepmind.google/models/veo/', modality='video', lic='proprietary API (hosted-only product per vendor page / arena listing: F0381, W0048)', handle='google',
  members='Veo 3.1, 3.1 Fast, 3.1 Lite (W0048, W0012)', notes='AA T2V Elo 3.1 1157 (W0012).', src=['brief','aa'])
z(slug='kling', name='Kling', org='kuaishou', home='https://kling.ai/', modality='video', lic='proprietary service/API (hosted-only product per vendor page / arena listing: F0380, W0059)', handle='kuaishou',
  members='Kling VIDEO 3.0, 3.0 Omni (W0059, W0012)', notes='AA T2V Elo 3.0 1080p Pro 1164 (W0012). Kuaishou attribution via KlingAIResearch MIT notice (F0241).', src=['brief','aa'])
z(slug='seedance', name='Seedance', org='bytedance-seed-volcano-engine', home='https://seed.bytedance.com/en/seedance', modality='video', lic='proprietary API (hosted-only product per vendor page / arena listing: F0385, W0056)', handle='bytedance-seed-volcano-engine',
  members='Seedance 1.0 (vendor page, W0056); Dreamina Seedance 2.0 (W0012)', notes='AA T2V Elo 2.0 720p 1235 (W0012).', src=['aa'])
z(slug='runway-gen', name='Runway Gen', org='runway', home='https://runway.com', modality='video', lic='proprietary service/API (hosted-only product per vendor page / arena listing: F0378, W0060)', handle='runway',
  members='Gen-4.5 (W0060)', notes='Not in AA T2V top 25 as fetched (W0012); brief lead, vendor claims "world\'s best video model" (W0060). ADR-005 look recommended.', src=['brief'])
z(slug='suno', name='Suno', org='suno', home='https://suno.com', modality='audio', lic='proprietary service (hosted-only product per vendor page / arena listing: F0375, W0054)', handle='suno',
  members='v5.5, v6, v6-mini (W0054, W0023, W0032)', notes='AA vocal #1 Elo 1134, instrumental 1143 (W0032, W0033).', src=['brief','aa','ws'])
z(slug='lyria', name='Lyria', org='google', home='https://deepmind.google/models/lyria/', modality='audio', lic='proprietary API (hosted-only product per vendor page / arena listing: F0382, W0050)', handle='google',
  members='Lyria 2, 3 Pro, 3.5 (W0050, W0032)', notes='AA vocal Elo 3.5 1045 (W0032).', src=['aa','ws'])
z(slug='meshy', name='Meshy', org='meshy', home='https://www.meshy.ai/', modality='3d', lic='proprietary service (hosted-only product per vendor page / arena listing: F0379, W0061)', handle='meshy',
  members='Meshy 7 (W0061); Meshy 5 on Pixazo board (W0063)', notes='3D arena Elo Meshy 5 1280 per Pixazo (W0063).', src=['ws'])
z(slug='tripo', name='Tripo', org='vast-ai', home='https://www.tripo3d.ai/', modality='3d', lic='proprietary service (hosted-only product per vendor page / arena listing: W0063; homepage 403 F0376)', handle='vast-ai',
  members='Tripo v3.1 (W0063)', notes='Ranked #1 on Sloyd arena summary (W0063); vendor page 403 via WebFetch (W0062) and curl (F0376): bot block, not a finding. Same org as open TripoSG/TripoSR.', src=['ws'])
