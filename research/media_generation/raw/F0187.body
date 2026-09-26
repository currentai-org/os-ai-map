---
license: cc-by-nc-4.0
language:
- zh
- en
pipeline_tag: text-to-audio
tags:
- music-generation
- symbolic-planning
- agentic-editing
- custom_code
---
<p align="center">
  <img src="assets/logo.png" alt="YuE logo" width="144" />
</p>
<h1 align="center">🤗 YuE2-3B</h1>
<p align="center"><strong>Frontier music generation with editable scores</strong></p>

<p align="center">
  <a href="https://github.com/multimodal-art-projection/YuE"><img alt="GitHub" src="https://img.shields.io/badge/GitHub-YuE-181717?logo=github&amp;logoColor=white" height="20" /></a>
  &nbsp;
  <a href="https://discord.gg/ssAyWMnMzu"><img alt="Join Discord" src="https://img.shields.io/discord/842440537755353128?label=Discord&amp;color=5865F2&amp;logo=discord&amp;logoColor=white" height="20" /></a>
</p>
<p align="center">
  <a href="https://map-yue2.github.io/">🎧&nbsp;Demo</a>
  ·
  <a href="https://arena.3-148-255-99.sslip.io:8080">🗳️&nbsp;Music&nbsp;Arena</a>
  ·
  <a href="#quick-start">🚀&nbsp;Quick&nbsp;start</a>
  ·
  <a href="#cover-an-existing-song">🎙️&nbsp;Cover</a>
  ·
  <a href="#export-a-plan-edit-it-and-generate">🤖&nbsp;Edit</a>
  ·
  <a href="#speed-and-resources" title="Speed and resources">⚡&nbsp;Speed</a>
  ·
  <a href="#benchmarks">📊&nbsp;Benchmarks</a>
  ·
  <a href="#citation">📚&nbsp;Citation</a>
</p>
<p align="center">
  <a href="https://huggingface.co/m-a-p/YuE2-3B"><img alt="🤗 YuE2-3B" src="https://img.shields.io/badge/YuE2--3B-374151?logo=huggingface&amp;logoColor=FFD21E" height="20" /></a>
  &nbsp;
  <a href="https://huggingface.co/m-a-p/YuE2-Vae"><img alt="🤗 YuE2-Vae" src="https://img.shields.io/badge/YuE2--Vae-374151?logo=huggingface&amp;logoColor=FFD21E" height="20" /></a>
  &nbsp;
  <a href="https://huggingface.co/m-a-p/YuE2-Vae-legacy"><img alt="🤗 YuE2-Vae-legacy" src="https://img.shields.io/badge/YuE2--Vae--legacy-374151?logo=huggingface&amp;logoColor=FFD21E" height="20" /></a>
  &nbsp;
  <a href="https://huggingface.co/m-a-p/MERT-v2-30s"><img alt="🤗 MERT-v2-30s" src="https://img.shields.io/badge/MERT--v2--30s-374151?logo=huggingface&amp;logoColor=FFD21E" height="20" /></a>
  &nbsp;
  <a href="https://huggingface.co/m-a-p/MERT-v2-FullSong"><img alt="🤗 MERT-v2-FullSong" src="https://img.shields.io/badge/MERT--v2--FullSong-374151?logo=huggingface&amp;logoColor=FFD21E" height="20" /></a>
  &nbsp;
  <a href="https://huggingface.co/datasets/m-a-p/WildSongBench"><img alt="🤗 WildSongBench" src="https://img.shields.io/badge/WildSongBench-374151?logo=huggingface&amp;logoColor=FFD21E" height="20" /></a>
  &nbsp;
  <a href="https://huggingface.co/m-a-p/SheetSage2"><img alt="SheetSage2" src="https://img.shields.io/badge/SheetSage2-374151?logo=huggingface&amp;logoColor=FFD21E" height="20" /></a>
</p>

**YuE2 is an open music generation model with frontier song quality competitive with Suno v5/v6.** Turn lyrics and a style prompt into a complete song with vocals and accompaniment, then shape its melody and chords through an editable score.

<a id="music-arena"></a>

> **🎧 YuE2 needs your ears**
>
> Help evaluate YuE2 alongside leading proprietary music models in our blind listening arena. Listen to anonymous music clips, choose your preference, and contribute to our listener preference study.
>
> **[Listen & vote →](https://arena.3-148-255-99.sslip.io:8080)** · No account needed.

**State-of-the-art results on WildSongBench.** YuE2 (best-of-8) achieves the highest SongBench average among all evaluated open and proprietary models: **6.9632**, compared with **6.8721** for Suno v5, **6.5562** for Suno v6, and **6.4195** for Suno v6 Wild.

![YuE2 song quality and text alignment on WildSongBench](assets/figure1.png)

*Frontier song quality and text alignment on 192 WildSongBench prompts. YuE2 uses symbolic planning; Bo8 means best-of-8.*

September 12, 2026 comparison: 17 settings, including Suno v6 and Suno v6 Wild. [Vector PDF](assets/figure1.pdf) · [SVG](assets/figure1.svg) · [All nine metrics and protocols](https://huggingface.co/datasets/m-a-p/WildSongBench/blob/main/benchmark/results.md) · [Full-precision CSV](https://huggingface.co/datasets/m-a-p/WildSongBench/resolve/main/benchmark/benchmark-results.csv).

- **Compose and edit:** melody + chords, melody-only, or direct generation; bring your own ABC score.
- **Edit with an agent:** turn musical feedback into score, style and lyric revisions, then let YuE2 render the next version. [Hear the editing process](https://map-yue2.github.io/#agentic-music-editing).
- **Run locally:** 48 kHz stereo songs on a 24GB GPU, without quantization.
- **Build on it:** Hugging Face loading, text guidance (CFG), and separate planning and synthesis APIs.

![YuE2 architecture](assets/architecture.png)

*One AR–NAR Mixture-of-Transformers backbone writes the score and semantic tokens, then generates acoustic latents through flow matching. The VAE turns them into stereo audio.*

<a id="listen"></a>

## 🎧 Listen to YuE2

<a id="text-to-music"></a>

### 🎶 Text-to-music

Original songs generated from lyrics and a style prompt.

**Cyber Metal · English · 5:00**

<audio controls preload="none" aria-label="Cyber Metal" src="https://huggingface.co/m-a-p/YuE2-3B/resolve/main/assets/audio/cyber-metal.mp3"></audio>

**今晚不眠 · Mandarin funk / nu-disco · 3:24**

<audio controls preload="none" aria-label="今晚不眠" src="https://huggingface.co/m-a-p/YuE2-3B/resolve/main/assets/audio/tonight-awake.mp3"></audio>

**Passion · English rock · 3:55**

<audio controls preload="none" aria-label="Passion" src="https://huggingface.co/m-a-p/YuE2-3B/resolve/main/assets/audio/passion.mp3"></audio>

*All three songs use [🤗 YuE2-Vae](https://huggingface.co/m-a-p/YuE2-Vae).*

<a id="cover-song"></a>

### 🎙️ Cover songs

Existing songs reimagined in a new style.

[Make your own cover →](#cover-an-existing-song)

**Auld Lang Syne · Jazz-funk cover · 3:10**

<audio controls preload="none" aria-label="Auld Lang Syne — Jazz-funk cover" src="https://huggingface.co/m-a-p/YuE2-3B/resolve/main/assets/audio/auld-lang-syne-jazz-funk-cover.mp3"></audio>

**最炫民族风 · Ballad cover · 4:45**

<audio controls preload="none" aria-label="最炫民族风 — Ballad cover" src="https://huggingface.co/m-a-p/YuE2-3B/resolve/main/assets/audio/zuixuan-ballad-cover.mp3"></audio>

**Jingle Bells · Heavy metal cover · 1:09**

<audio controls preload="none" aria-label="Jingle Bells — Heavy metal cover" src="https://huggingface.co/m-a-p/YuE2-3B/resolve/main/assets/audio/jingle-bells-heavy-metal-cover.mp3"></audio>

<a id="agentic-editing"></a>

### 🤖 Agentic editing

**[Explore the agentic editing demo →](https://map-yue2.github.io/#agentic-music-editing)**

Follow **The Last Train** through **9 steps and 14 versions**, from Mandarin pop to English jazz with modern harmony and a saxophone solo built around two complete statements of “Twinkle, Twinkle, Little Star.” Hear the full songs and inspect the conversation, scores, prompts and lyrics at each step.

[Try editing with an agent →](#export-a-plan-edit-it-and-generate)

<a id="quick-start"></a>

## 🚀 Quick start

Linux · Python 3.10+ · 24GB NVIDIA GPU with BF16 support. Install the inference package:

```bash
python -m pip install huggingface-hub==0.36.2
hf download m-a-p/YuE2-3B yue2_infer-0.1.5-py3-none-any.whl --local-dir .
python -m pip install ./yue2_infer-0.1.5-py3-none-any.whl
```

[Create](#generate-a-song) · [Cover](#cover-an-existing-song) · [Edit & agentic edit](#export-a-plan-edit-it-and-generate)

Load the pipeline once for the examples below:

```python
from pathlib import Path
from yue2 import YuE2Pipeline

pipe = YuE2Pipeline.from_pretrained("m-a-p/YuE2-3B", device="cuda")
```

<a id="generate-a-song"></a>

### 🎶 Create

Turn a style prompt and lyrics into a complete song with vocals and accompaniment.

Use the [style and full lyrics from 今晚不眠](examples/tonight-awake.json), the funk / nu-disco demo above.

```python
import json
from huggingface_hub import hf_hub_download

repo = "m-a-p/YuE2-3B"
prompt_path = hf_hub_download(repo, "examples/tonight-awake.json")
demo = json.loads(Path(prompt_path).read_text(encoding="utf-8"))
style, lyrics = demo["style"], demo["lyrics"]

song = pipe(style=style, lyrics=lyrics, cot="full", seed=demo["seed"])
song.save("song.flac")
song.save_artifacts("outputs/song")  # ABC, tokens, latents, audio and settings
```

Defaults are ready to use: `cot="full"` and [🤗 YuE2-Vae](https://huggingface.co/m-a-p/YuE2-Vae).

| Option | What it does |
|---|---|
| `cot="full"` | Melody + chord planning (default) |
| `cot="melody"` | Melody-only planning; recommended for covers |
| `cot="off"` | Generate without a symbolic plan |
| `cfg_scale=1.2` | Experiment with stronger text guidance |

<a id="cover-an-existing-song"></a>

### 🎙️ Cover

Start from an existing recording and give it a new arrangement.

**For covers, we recommend melody-only mode (`cot="melody"`).**

1. **Get the score:** transcribe the existing song with [🤗 SheetSage2](https://huggingface.co/m-a-p/SheetSage2) and save its melody ABC **without chord symbols** as `melody.abc`.
2. **Get the lyrics:** ask an agent to find them online, or transcribe the singing with [Qwen3-ASR](https://huggingface.co/Qwen/Qwen3-ASR-1.7B) or the [Gemini API](https://ai.google.dev/gemini-api/docs/audio). Check the words, organize them into sections matching the recording, and save them as `cover_lyrics.txt`.
3. **Choose a target style and generate:** review or edit the score and lyrics, then supply them to YuE2 with `cot="melody"` and your target style prompt.

Run the transcription tools in their own environments, then use the YuE2 pipeline:

```python
cover = pipe(
    style="Jazz-funk, warm lead vocal, Rhodes piano, electric bass, tight drums",
    lyrics=Path("cover_lyrics.txt").read_text(encoding="utf-8"),
    abc=Path("melody.abc").read_text(encoding="utf-8"),
    cot="melody", seed=831001,
)
cover.save("cover.flac")
cover.save_artifacts("outputs/cover")
```

`cot="melody"` does not remove chord symbols automatically. Use `cot="full"` if you want to supply the original or edited harmony as well.

<a id="export-a-plan-edit-it-and-generate"></a>

### 🎼 Edit & agentic edit

Edit the ABC yourself, or give an agent the score, original prompt and lyrics, and your requested changes. The agent can reharmonize, develop a solo, or adapt the lyrics and style; YuE2 renders each revision. [Hear the multi-turn editing demo](https://map-yue2.github.io/#agentic-music-editing).

For the song from **Create**, copy `outputs/song/score.abc` to `edited.abc`. To obtain a plan before generating audio, use the same prompt and seed:

```python
plan = pipe.plan(style=style, lyrics=lyrics, cot="full", seed=demo["seed"])
plan.save("original_plan")
# Keep the original and edit a copy as edited.abc.
```

For strict reharmonization, ask the agent to preserve melody pitches and rhythm and check sustained notes against the new chords. Allow selected melody or lyric changes for a broader adaptation. After reviewing `edited.abc`, regenerate with the revised style; this example keeps the lyrics and seed from **Create**:

```python
edited_style = (
    "Jazz, expressive lead vocal, piano, tenor saxophone, upright bass, "
    "brushed drums, no guitar, spacious modern harmony"
)
song = pipe(style=edited_style, lyrics=lyrics, cot="full", seed=demo["seed"],
            abc=Path("edited.abc").read_text(encoding="utf-8"))
song.save("edited.flac")
song.save_artifacts("outputs/edited")
```

<details>
<summary>⚙️ CFG, individual stages, and decoder selection</summary>

Generation shows English progress messages by default, including the current stage, elapsed time, and token throughput. To disable them, use `YuE2Pipeline.from_pretrained(repo, progress=False)` in Python or `yue2 generate --quiet` / `yue2 batch --quiet` on the command line.

Each CoT mode selects its native instruction. Semantic CFG defaults to 1.0 for full/melody and 1.01 for off; ABC sampling uses no CFG.

`pipe.plan()` → `pipe.generate_semantic(plan)` → `pipe.synthesize(semantic)` → `pipe.decode(latents)`. Call `pipe.close()` when finished. For the benchmark decoder, pass `vae="m-a-p/YuE2-Vae-legacy"` to `from_pretrained`.

</details>

<a id="speed-and-resources"></a>

## ⚡ Speed and resources

**A 3.6-minute song in 71 seconds on an RTX 4090.** The HF package uses PyTorch, CUDA graphs, and FlashAttention, with BF16 AR/NAR and FP32 VAE.

| GPU | CoT | Warm samples | LM tokens/s | Generation / audio | Peak VRAM |
|---|---|---:|---:|---:|---:|
| RTX 4090 24GB | full | 32 | 139.48 | 71.04 / 214.85 s | 11.18 GiB |
| RTX 4090 24GB | melody | 32 | 139.32 | 68.68 / 214.67 s | 11.02 GiB |
| RTX 4090 24GB | off | 32 | 121.07 | 57.91 / 196.88 s | 11.09 GiB |
| H800 80GB | full | 1 | 164.38 | 54.74 / 224.96 s | 10.34 GiB |

One song at a time. Use a **24GB GPU** and **24GB available host RAM**; maximum-context testing peaked at **14.08 GiB**.

**H800 server · vLLM 0.19 · full CoT.** This separate serving runtime handles concurrent requests:

| AR concurrency limit | LM system tokens/s | Songs/hour | Peak VRAM |
|---:|---:|---:|---:|
| 1 | 378.42 | 119.43 | 78.55 GiB |
| 16 | 2418.63 | 340.38 | 78.66 GiB |
| 32 | 3231.74 | 373.53 | 76.61 GiB |

<details>
<summary>🔎 Measurement details</summary>

HF: PyTorch 2.10, Transformers 4.57.6, no quantization, default YuE2-Vae. 4090 values average 32 warm requests per mode; H800 is a one-song HF download-and-generation check. Times are synchronized pipeline calls, excluding initial path resolution and saving. NVML records the full-run GPU peak.

Server: 32 songs per row; AR/NAR use PyTorch 2.10 and Triton 3.6, VAE uses PyTorch 2.6. Songs/hour is warm batch throughput through all stages, not request latency. TPS counts output tokens once, excluding prefixes, supplied ABC, and the second CFG branch. Memory includes reserved KV cache. This server is separate from the HF quick start.

</details>

<a id="benchmarks"></a>

## 📊 Benchmarks

<a id="wildsongbench--full-song-generation"></a>

### 🌍 WildSongBench · full-song generation

**🔓 Open models**

| Model | Musicality ↑ | SongBench Avg ↑ | MuLan ↑ | AllMusicCaps ↑ | Q3O ↑ | PER ↓ |
|---|---:|---:|---:|---:|---:|---:|
| YuE 1 | 4.0847 | 4.9165 | 0.2623 | 0.2882 | 3.7301 | 36.38% |
| SongBloom | 3.4493 | 4.2350 | 0.2697 | 0.1926 | 3.0287 | 19.19% |
| LeVo 2 | 5.4590 | 6.3247 | 0.3542 | 0.2680 | 3.9458 | 26.12% |
| ACE-Step 1.5 | 5.1588 | 6.0118 | 0.4372 | 0.3869 | 4.5809 | 7.46% |
| HeartMuLa | 5.4963 | 6.2483 | 0.3823 | 0.2786 | 3.4907 | 10.71% |
| DiffRhythm 2 | 4.4775 | 5.2428 | 0.3782 | 0.3255 | 4.0870 | 18.41% |
| Muse | 5.1692 | 6.0349 | 0.3937 | 0.3466 | 4.4038 | 33.42% |
| MiniMax Music 3 | 5.3482 | 6.2830 | 0.3928 | 0.3609 | 4.4362 | **6.27%** |
| **YuE2** | 5.9075 | 6.7316 | **0.5068** | **0.4054** | 4.6819 | 8.44% |
| **YuE2 (best-of-8)** | **6.2666** | **6.9632** | 0.5051 | 0.3980 | **4.7009** | 9.79% |

**🔒 Proprietary models**

| Model | Musicality ↑ | SongBench Avg ↑ | MuLan ↑ | AllMusicCaps ↑ | Q3O ↑ | PER ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Suno v5 | 5.9918 | 6.8721 | **0.5428** | **0.4353** | 4.5907 | 8.10% |
| Suno v4.5 | 5.8317 | 6.6995 | 0.5022 | 0.3873 | 4.4149 | **5.80%** |
| Suno v5.5 | 5.8087 | 6.7150 | 0.5089 | 0.3917 | 4.5914 | 5.96% |
| Suno v6 | 5.6558 | 6.5562 | 0.4916 | 0.4305 | 4.6258 | 7.58% |
| Suno v6 Wild | 5.5644 | 6.4195 | 0.4999 | 0.4316 | 4.5898 | 7.45% |
| MiniMax Music 2.6 | 5.4437 | 6.3222 | 0.4251 | 0.3670 | 4.5688 | 24.55% |
| Mureka 9 | 6.0488 | 6.9377 | 0.4394 | 0.4102 | 4.6368 | 11.69% |
| **YuE2** | 5.9075 | 6.7316 | 0.5068 | 0.4054 | 4.6819 | 8.44% |
| **YuE2 (best-of-8)** | **6.2666** | **6.9632** | 0.5051 | 0.3980 | **4.7009** | 9.79% |

*192 prompts. Both YuE2 settings use symbolic planning and [🤗 YuE2-Vae-legacy](https://huggingface.co/m-a-p/YuE2-Vae-legacy). Standard YuE2 selects from two candidates; best-of-8 selects from eight.*

<a id="shs100k--zero-shot-cover-generation"></a>

### 🎤 SHS100K · zero-shot cover generation

| Method | CLEWS mAP ↑ | CLEWS Hit@1 ↑ | VINet mAP ↑ | MuLan ↑ | Musicality ↑ |
|---|---:|---:|---:|---:|---:|
| SongEcho | 0.419 | 48.4% | 0.122 | 0.366 | 3.286 |
| ACE-Step 1.5 | 0.024 | 2.4% | 0.006 | 0.166 | 3.689 |
| **YuE2 (full score)** | **0.647** | **71.3%** | **0.288** | 0.382 | 5.104 |
| YuE2 (without chords) | 0.598 | 67.3% | 0.179 | 0.417 | 5.490 |
| YuE2 (without score) | 0.006 | 0.3% | 0.004 | **0.474** | **5.691** |

*948 works × two styles × two seeds: 3,792 songs per method, without candidate selection. The score-conditioned variants use supplied source scores; all YuE2 variants use YuE2-Vae-legacy.*

<details>
<summary>📐 Evaluation protocols and metric definitions</summary>

WSB: SongBench Avg averages seven dimensions; Q3O measures prompt adherence on a 0–5 scale; PER is phoneme error rate. YuE2 selects the lower-PER candidate from two. Best-of-8 selects by Musicality → Q3O → PER. Each candidate's PER uses the lowest-PER of four ASR passes. A pipeline call generates one candidate; selection is separate. Q3O weights differ on 10 of 192 prompts between the two YuE2 settings. Bold marks the best value within each table. Open baselines, Suno v6, and Suno v6 Wild use two candidates and four ASR passes per candidate, followed by lower-PER selection; earlier proprietary systems retain their delivered-candidate protocols. MiniMax Music 3 uses its official caption rewriter. SongBloom uses a fixed audio prompt rather than a style-text input.

SHS100K: CLEWS and Discogs-VINet measure preserved song identity against 10,545 recordings after source exclusion. MuLan measures target-style similarity; Musicality is from SongBench. Identity and quality should be read together. Every displayed metric covers all 3,792 outputs per method; incomplete Q3O scores are omitted. Source-score extraction is separate from this kit.

The overview plot combines SongBench and SongEval for quality, and MuLan, AllMusicCaps, and Q3O for alignment. These are automatic benchmark results under the stated candidate-selection protocols.

</details>

<details>
<summary>🔊 Choosing a VAE</summary>

In our comparisons, [🤗 YuE2-Vae-legacy](https://huggingface.co/m-a-p/YuE2-Vae-legacy) achieves higher musicality scores on benchmarks, while [🤗 YuE2-Vae](https://huggingface.co/m-a-p/YuE2-Vae) delivers better perceptual audio quality. We recommend YuE2-Vae by default; use YuE2-Vae-legacy when reproducing the paper's benchmark results.

</details>

<a id="citation"></a>

## 📚 Citation

**Technical report coming soon.** For now, please cite [YuE](https://arxiv.org/abs/2503.08638) when using YuE2-3B in your research.

```bibtex
@article{yuan2025yue,
  title = {{YuE}: Scaling Open Foundation Models for Long-Form Music Generation},
  author = {Yuan, Ruibin and Lin, Hanfeng and Guo, Shuyue and Zhang, Ge and Pan, Jiahao and Zang, Yongyi and Liu, Haohe and Liang, Yiming and Ma, Wenye and Du, Xingjian and Du, Xinrun and Ye, Zhen and Zheng, Tianyu and Jiang, Zhengxuan and Ma, Yinghao and Liu, Minghao and Tian, Zeyue and Zhou, Ziya and Xue, Liumeng and Qu, Xingwei and Li, Yizhi and Wu, Shangda and Shen, Tianhao and Ma, Ziyang and Zhan, Jun and Wang, Chunhui and Wang, Yatian and Chi, Xiaowei and Zhang, Xinyue and Yang, Zhenzhu and Wang, Xiangzhou and Liu, Shansong and Mei, Lingrui and Li, Peng and Wang, Junjie and Yu, Jianwei and Pang, Guojian and Li, Xu and Wang, Zihao and Zhou, Xiaohuan and Yu, Lijun and Benetos, Emmanouil and Chen, Yong and Lin, Chenghua and Chen, Xie and Xia, Gus and Zhang, Zhaoxiang and Zhang, Chao and Chen, Wenhu and Zhou, Xinyu and Qiu, Xipeng and Dannenberg, Roger and Liu, Jiaheng and Yang, Jian and Huang, Wenhao and Xue, Wei and Tan, Xu and Guo, Yike},
  journal = {arXiv preprint arXiv:2503.08638},
  year = {2025},
  eprint = {2503.08638},
  archivePrefix = {arXiv},
  url = {https://arxiv.org/abs/2503.08638}
}
```

Weights: [CC BY-NC 4.0](LICENSE). [Third-party code licenses](THIRD_PARTY_NOTICES.md).
