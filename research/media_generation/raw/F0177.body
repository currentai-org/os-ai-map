---
library_name: diffusers
pipeline_tag: text-to-audio
tags:
  - music-generation
  - text-to-music
  - pytorch
  - sglang-omni
---

<div align="center">
  <img width="100%" src="figures/Music3.png" alt="MiniMax">
</div>
<p align="center">
  <a href="https://agent.minimax.io/" target="_blank"><img src="https://img.shields.io/badge/MiniMax%20Agent-FF6C37?logo=minimax&logoColor=white" alt="MiniMax Agent"></a>
  <a href="https://platform.minimax.io/docs/guides/text-generation" target="_blank"><img src="https://img.shields.io/badge/API-FF6C37?logo=minimax&logoColor=white" alt="API"></a>
  <a href="https://www.minimax.io" target="_blank"><img src="https://img.shields.io/badge/MiniMax%20Website-FF6C37?logo=minimax&logoColor=white" alt="MiniMax Website"></a>
  <br>
  <a href="https://modelscope.cn/organization/minimax" target="_blank" rel="noopener noreferrer"><img alt="ModelScope MiniMax AI" src="https://img.shields.io/badge/ModelScope-MiniMax%20AI-white?labelColor=%23EF3D5D"></a>
  <a href="https://platform.minimaxi.com/docs/faq/contact-us" target="_blank"><img src="https://img.shields.io/badge/WeChat-07C160?logo=wechat&logoColor=white" alt="WeChat"></a>
  <a href="https://discord.com/invite/DPC4AHFCBw" target="_blank"><img src="https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://huggingface.co/MiniMaxAI" target="_blank"><img src="https://img.shields.io/badge/Hugging%20Face-FFD21E?logo=huggingface&logoColor=black" alt="Hugging Face"></a>
  <a href="https://github.com/MiniMax-AI/MiniMax-Music3" target="_blank"><img src="https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white" alt="GitHub"></a>
  <a href="https://huggingface.co/MiniMaxAI/MiniMax-Music3/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/badge/LICENSE-4CAF50?logo=creativecommons&logoColor=white" alt="LICENSE"></a>
</p>

# MiniMax Music 3

**MiniMax Music 3** is a high-performance music generation model for creating complete songs up to **five minutes** long. Conditioned on lyrics and a detailed music description, it generates structurally coherent songs with expressive vocals, evolving arrangements, and stable long-form audio quality.

MiniMax Music 3 combines an **8B Global LLM** for long-range musical structure, a **0.6B Local LLM** for frame-level acoustic detail, and a continuous hidden-state synthesis system based on **Flow Matching** and **Flow-VAE**. The model produces 32 kHz, 16-bit stereo WAV audio.
## Demo

Explore music generation examples on the [MiniMax Music 3 Demo](https://minimax-ai.github.io/music3-demo/).

<p align="center">
  <img width="100%" src="figures/music3.0-Architecture-Diagram.png">
</p>

## Complete Songs with Long-Range Coherence

MiniMax Music 3 natively supports full-song generation up to five minutes. The model maintains musical themes, rhythm, vocal identity, and arrangement progression across long sequences, enabling complete structures such as intro, verse, pre-chorus, chorus, bridge, instrumental break, and outro.

## Fine-Grained Music Control

The model accepts two complementary inputs:

- **Lyrics** define the words to be sung and may include explicit section tags such as `[Intro]`, `[Verse]`, `[Pre-Chorus]`, `[Chorus]`, `[Post-Chorus]`, `[Bridge]`, `[Instrumental]`, `[Solo]`, and `[Outro]`.
- **Music description** defines the musical style, emotional progression, vocal performance, instrumentation, arrangement, and production profile.

For precise control, we recommend using a Structured Caption with three sections:

- **Global Metadata**: genre, subgenre, BPM, key, scale, emotional progression, listening scenario, and production profile.
- **Vocal Details**: vocal gender, timbre, performance style, harmony, backing vocals, and vocal effects.
- **Arrangement**: primary and secondary instruments, section-level instrument evolution, groove, bass, percussion, textures, and spatial effects.

This representation allows the model to follow not only a global style, but also the musical development of the song over time.

## Hybrid-LM

MiniMax Music 3 uses a hierarchical autoregressive architecture that separates global musical modeling from local acoustic modeling.

- The **Global LLM (8B)** predicts the first RVQ codebook frame by frame and models the song's long-range semantic and structural progression.
- The **Local LLM (0.6B)** predicts the remaining acoustic codebooks within each frame and restores fine-grained acoustic information.

The Global LLM is initialized from Qwen3-8B. During training, its embedding and output layers are first adapted to semantic music tokens. The Global and Local LLMs are then jointly trained to model all RVQ codebooks.

## Continuous Hidden-State Synthesis

Instead of decoding only from discrete RVQ tokens, the synthesis module fuses the final hidden states of the Global and Local LLMs. These continuous representations preserve richer acoustic information for vocal articulation, instrumental texture, and temporal continuity.

The synthesis path is:

```text
Global and Local LLM hidden states
                ↓
       Hidden-state fusion
                ↓
     Flow Matching (2.4B)
                ↓
        Flow-VAE latent
                ↓
    Flow-VAE Decoder (123M)
                ↓
       32 kHz stereo audio
```

The Flow-VAE architecture is adapted from MiniMax Speech and retrained for the dynamic range and spectral characteristics of music.

## Music Tokenizer

The training tokenizer uses eight layers of Residual Vector Quantization (RVQ):

- The first semantic codebook contains **16,384** entries and captures the core musical semantics and structure.
- The remaining seven acoustic codebooks contain **1,024** entries each and represent residual acoustic details.

Training first optimizes the semantic codebook, then jointly trains all eight codebooks. At inference time, waveform synthesis uses the fused LLM hidden states and does not require the discrete tokenizer decoder.

## How to Use

MiniMax Music 3 is supported by [SGLang-Omni](https://github.com/sgl-project/sglang-omni). Follow the official [installation guide](https://sgl-project.github.io/sglang-omni/get_started/installation.html) to prepare the runtime environment.

### Download the Model

```bash
hf download MiniMaxAI/MiniMax-Music3 --local-dir /path/to/minimax_ttm
```

We recommend the following inference frameworks to serve the model:

- [SGLang](https://docs.sglang.io/) \- see [cookbook](https://sgl-project.github.io/sglang-omni/cookbook/minimax_music3.html) 

- [diffusers](https://github.com/huggingface/diffusers) \- see [diffusers docs](https://github.com/huggingface/diffusers/blob/minimax-music3-integration/docs/source/en/api/pipelines/minimax_music3.md)

- [ComfyUI](https://github.com/Comfy-Org/ComfyUI) see [comfyUI tutorials](https://docs.comfy.org/tutorials/audio/minimax/minimax-music-3)


### Serve with SGLang-Omni

```bash
sgl-omni serve --model-path MiniMaxAI/MiniMax-Music3 --port 8000
```

### Generate Music

The service uses the shared speech API. Put the lyrics in `input` and the music description in `instructions`. Put lyric structure tags such as `[Verse]` and `[Chorus]` on their own lines.

```bash
curl http://127.0.0.1:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "MiniMaxAI/MiniMax-Music3",
    "input": "[Verse]\nMorning light filtering through the pine\n[Chorus]\nSoftly the world begins to breathe",
    "instructions": "A warm acoustic pop song with intimate female vocals, fingerpicked guitar, soft piano, and a gradual emotional build into a wide final chorus.",
    "response_format": "wav",
    "seed": 7,
    "max_new_tokens": 750,
    "stream": false
  }' \
  --output minimax_music3.wav
```

`max_new_tokens` sets the maximum number of audio frames at 25 frames per second. Generation may finish before this limit when the model emits an end-of-audio token. The response is a 32 kHz, 16-bit stereo WAV file.

### Reproducible Example

The following end-to-end example contains the complete lyrics, music description, and generation parameters used to produce the reference audio.

| Use case | Request | Result |
|---|---|---|
| Text-to-music | [View script](https://huggingface.co/MiniMaxAI/MiniMax-Music3/blob/main/scripts/end_to_end/minimax_ttm_test.py) | [minimax_ttm.wav](https://huggingface.co/MiniMaxAI/MiniMax-Music3/blob/main/assets/minimax_ttm.wav) |

## 🧨 Diffusers

MiniMax Music 3 is available as a [diffusers](https://github.com/huggingface/diffusers) modular pipeline. Until [huggingface/diffusers#14456](https://github.com/huggingface/diffusers/pull/14456) is merged, install diffusers from the PR commit:

The snippet below fits 24GB+ VRAM GPUs

```bash
pip install git+https://github.com/huggingface/diffusers@dafe3733fcfdbf3c48915fe77be3aef65b5d6a2d transformers accelerate soundfile
```

```python
import soundfile as sf
import torch
from diffusers import ModularPipeline

pipe = ModularPipeline.from_pretrained("MiniMaxAI/MiniMax-Music3")
pipe.load_components(dtype=torch.bfloat16)
pipe.to("cuda")

lyrics = """[verse]
Morning light filtering through the pine
Every quiet street is yours and mine
[chorus]
Softly the world begins to breathe"""

prompt = (
    "Genre: acoustic pop. BPM: 96. Key: C major. Warm and intimate, building gently into the chorus. "
    "Vocals: soft female lead, close and breathy, light stacked harmonies in the chorus. "
    "Arrangement: fingerpicked guitar and soft piano; brushed drums and upright bass enter in the chorus."
)

audio = pipe(
    prompt=prompt,
    lyrics=lyrics,
    audio_duration=60.0,
    generator=torch.Generator("cuda").manual_seed(7),
    output="audios",
)[0]

sf.write("song.wav", audio.T.float().cpu().numpy(), pipe.sampling_rate)
```

### Low VRAM

The full precision fits under 24GB of VRAM. With automatic CPU offloading, generation takes in ~22 GB; additionally streaming the language model layer by layer makes it fit even 8 GB video cards:

```python
import torch
from diffusers import ComponentsManager, ModularPipeline
from diffusers.hooks import apply_group_offloading

manager = ComponentsManager()
manager.enable_auto_cpu_offload(device="cuda")
pipe = ModularPipeline.from_pretrained("MiniMaxAI/MiniMax-Music3", components_manager=manager)
pipe.load_components(dtype=torch.bfloat16)

# Only needed below ~22 GB of VRAM — slower, but fits in 8 GB.
apply_group_offloading(
    pipe.language_model, onload_device=torch.device("cuda"), offload_type="leaf_level", use_stream=True
)


```

## Prompt Enhancement

A concise natural-language description can be used directly. For richer prompts and more precise control, use the provided [`music-caption-rewriter`](https://github.com/MiniMax-AI/MiniMax-Music3/tree/main/skills/music-caption-rewriter) skill to expand it into a Structured Caption containing `Global Metadata`, `Vocal Details`, and `Arrangement`. The skill preserves musical instructions attached to lyric section tags in the arrangement description while keeping the lyric text in the lyrics input.

```bash
npx skills add MiniMax-AI/MiniMax-Music3 --skill music-caption-rewriter
```

## Limitations

- Inference requires CUDA.
- Only non-streaming generation is currently supported.
- The tokenized text prompt is limited to 5,000 tokens.
- Audio generation is limited to 9,000 acoustic frames.
- Section tags and music descriptions provide generative control rather than strict symbolic guarantees. The generated tempo, key, instrumentation, lyrics, and song structure may not always match every requested detail exactly.

## Contact Us

Contact us at [model@minimax.io](mailto:model@minimax.io).
