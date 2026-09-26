# Speech & audio sweep — 2026-09-26

Brief 0 (issue #602). The category was approved on 2026-09-25; this document turns the ruled list into a
verified seed. All facts trace to fetches made on 2026-09-26 (UTC) and are logged in `fetch-log.tsv`
(`F` ids, raw bodies in `raw/`) and `web-log.tsv` (`W` ids). `rows.yaml` is §6a as a registry file.

## 1. Verdict

**GO-WITH-CHANGES.** The ruled list survives live verification: 42 of its 43 named rows are accepted as
new registry rows, and the 43rd (NeMo) is already on the map as a `finetuning_code` tail row, so it is a
move rather than a new row. Supply is deep and diverse (34 organizations, largest share 7%), and 37 of 42
rows carry a real usage instrument. The changes are factual and came out of the fetches, not out of
reopening rulings: NeMo's repo is now `NVIDIA-NeMo/Speech` (the index still says `NVIDIA/NeMo`),
CosyVoice moved to `QwenAudio/CosyVoice`, Moonshine to `moonshine-ai`, Piper to the Open Home Foundation
under GPL-3.0, Fish-Speech's *code* is now under the Fish Audio Research License, Higgs Audio's current
TTS weights are non-commercial, and Microsoft removed the VibeVoice TTS code in 2025-09. Five strong 2026
releases are missing from the list (Cohere Transcribe, MOSS-Transcribe-Diarize, Breeze TTS 2, OmniVoice,
Kyutai Pocket TTS); they are proposed in §9, not accepted.

## 2. Fit metrics (computed from section 6)

- accepted candidates: **42** (open: 11, open-weights: 21, source-available: 6, closed: 4). By type: 31 model, 11 software.
  Status definitions used here: *open* = software under an OSI license; *open-weights* = downloadable weights whose
  license permits commercial use (OSI, CC-BY-4.0, NVIDIA Open Model License); *source-available* = downloadable,
  commercial use forbidden or research-only (CC-BY-NC, CPML, Fish/Boson research licenses); *closed* = API only.
  Higgs Audio is classed by its current TTS release (v3, non-commercial), per the identity guide's "current release
  governs" rule for openness.
- independent organizations: **34**; largest org's share: **7.1%** (3 of 42, a three-way tie: `nvidia`, `meta`,
  `alibaba-cloud`).
- candidates active in the last 12 months (any push to a non-archived repo, a release, or an HF `lastModified` on/after
  2025-09-26, or a dated 2026 release for closed rows; pushes to archived repos do not count): **37**. Inactive: `kokoro` (last push 2025-08-06), `melotts` (2024-12-24),
  `mms` and `wav2vec` (code in archived fairseq, HF edits ≤ 2023-10), `xtts` (HF 2023-12). `sesame-csm` counts as
  active only through an HF card edit (2025-12-01); its repo is quiet since 2025-05.
- candidates with a usage instrument (PyPI or HF downloads): **37**. No instrument: the 4 closed rows and
  `whisper-cpp` (no official package; its HF weights repo reports 0 downloads, F0273). `kyutai-stt` is counted
  through a member checkpoint (`-trfs`, 15,491) because the canonical native-format repos report 0.
- retrieval cutoff: the ruled list plus its reserve, plus WebSearch discovery (W0001–W0003, W0006–W0009, W0015–W0017)
  and HF author searches sorted by downloads (top 15 per query). HF task-filter sweeps (e.g. every
  `automatic-speech-recognition` model by downloads) were **not** run; community fine-tunes and quantized re-uploads
  are therefore out of view, which is a coverage limit, not a rejection.

## 3. Boundary

- **Definition:** models and tools whose headline capability is speech: recognition (ASR), synthesis (TTS),
  speech-to-speech and full-duplex conversation, and the pipeline components around them (diarization, VAD).
- **Litmus:** is the primary input or output a speech waveform, and is speech the headline rather than one modality
  among several?
- **Exclusions:**
  - chat-first audio LLMs and omni models (Voxtral Small, Qwen2.5-Omni) → foundation-model categories /
    `multimodal_models` (brief 2);
  - music and sound-effect generation → `media_generation` (brief 1);
  - speech datasets (Common Voice, IndicVoices, Afrivoice, …) → stay in `language_specific_datasets`;
  - general inference runtimes that also serve audio (llama.cpp, ONNX Runtime, Triton) → stay in `inference_code`;
  - OpenAI-compatible single-model wrappers (Kokoro-FastAPI) → not products of this category;
  - voice-agent orchestration frameworks → `orchestration_agents` (not swept here).
- **Contested products:**

| product | where it is now | recommendation | reason |
|---|---|---|---|
| NVIDIA NeMo (`nemo`) | tail, `finetuning_code`, github `NVIDIA/NeMo` | **move here**, and update github to `NVIDIA-NeMo/Speech` | The repo now resolves to `NVIDIA-NeMo/Speech` (F0051, F0053); its README is titled NeMo Speech and installs `nemo-toolkit[asr,tts]` (F0223). LLM training lives in separate NeMo repos already on the map (`nemo-rl`, `megatron-lm`). |
| whisper.cpp | absent (`ggml`, `llama-cpp` are in `ml_frameworks`/`inference_code`) | here (accepted, `whisper-cpp`) | Speech-first engine per ruling; no artifact collides with the index. |
| Voxtral Small 24B | absent | other (foundation models) | Chat-first per ruling; kept out of the `voxtral` row (F0118). |
| Qwen2.5-Omni | absent | other → `multimodal_models` (sibling sweep) | Omni model; flagged for that sweep, not resolved here (W0009). |
| Stable Audio / MusicGen / ACE-Step | absent | other → `media_generation` (sibling sweep) | Music/SFX per ruling; not fetched here. |
| VibeVoice-ASR vs VibeVoice-TTS | absent | here, one row | Same family and repo (F0019, F0132); TTS code removed (F0226). |
| MMS vs `mms-lab-data` | `mms-lab-data` head in `language_specific_datasets` | both stay | Model vs dataset; no shared artifact. |

## 4. Capability quantity

**No single quantity orders the whole set**, and that is a finding. The set mixes three task families (ASR, TTS,
speech-to-speech) plus software. What exists: the Hugging Face Open ASR Leaderboard orders ASR models by average
WER (W0002), and the Artificial Analysis Speech Arena orders TTS by Elo, with a separate open-weights board
(W0007). Neither covers the other task, and neither covers engines. The workable single axis is **frontier
coverage of speech tasks**, as a 5-rung sketch:

1. Single-task, narrow-language component or legacy model (MeloTTS single-language voices, Vosk models).
2. Single-task, multilingual, no current leaderboard presence (MMS, wav2vec 2.0).
3. Single-task, on a current public leaderboard at mid-table (Whisper large-v3, Kokoro #5 open-weights, W0007).
4. Single-task, at or near the top of a public leaderboard or multi-task (ASR + TTS) in one line (Granite Speech 4.1 at 5.33% WER,
   W0002; Fish Audio S2 Pro #2 open-weights TTS, W0007; VibeVoice ASR+TTS, F0132).
5. Real-time, full-duplex speech-to-speech (Moshi, PersonaPlex), anchored at the top by **Moshi**.

For software rows the same ladder reads as "which rungs of models it can serve, and whether it streams." The
ladder is a proposal for the scorer; `build-rubric` owns the decision.

## 5. Scoring ladder inputs

- Ladders: **model** for the 31 model rows (27 open/source-available + 4 closed), **software** for the 11 engine and
  pipeline rows, per the ruled `extends: {model: model, software: software}`. No `pretrained`, `dataset` or
  `hardware` ladder is needed.
- License strings met (weights unless marked code):

| license | products | tier note |
|---|---|---|
| MIT | whisper (turbo), moonshine (default), chatterbox, melotts, vibevoice; code: whisper, moonshine, f5-tts, personaplex, faster-whisper, whisper-cpp, pyannote-audio, silero-vad, moshi (PyPI) | osi |
| Apache-2.0 | whisper (large-v3 etc.), wav2vec, qwen-asr, qwen-tts, granite-speech, voxtral (Mini/Realtime), kokoro, cosyvoice, dia, sesame-csm, orpheus-tts (card), zonos, higgs-audio v3 STT; code: kyutai-stt (Rust), higgs-audio, espnet, speechbrain, sherpa-onnx, vosk | osi |
| BSD-2-Clause | whisperx | osi |
| MPL-2.0 | coqui-tts | osi |
| GPL-3.0(-or-later) | piper (current; MIT before, on the archived repo) | osi (copyleft) |
| CC-BY-4.0 | canary, parakeet, kyutai-stt/tts, moshi, pyannote community-1 pipeline, pocket-tts | `permissive_non_osi` (ruled) |
| NVIDIA Open Model License | personaplex | `permissive_non_osi` (already named) |
| CC-BY-NC-4.0 | mms, seamless-m4t, f5-tts, voxtral TTS member, canary-1b (legacy), OmniVoice (parked) | `commercial_forbidden` (ruled) |
| CC-BY-NC-SA-4.0 | fish-speech (s1-mini, 1.x), Spark-TTS (parked) | `commercial_forbidden` (ruled) |
| **Coqui Public Model License 1.0.0** (F0207) | xtts | **custom, deferred** (ruled) |
| **Fish Audio Research License, 2026-03-07** (F0204, F0205) | fish-speech (code and S2 Pro weights) | **custom, deferred** (ruled). New: now also covers the code. |
| **Boson Higgs Audio 2 Community License** (Llama-3-derived, F0210) | higgs-audio v2 | **custom, deferred** (ruled) |
| **Boson Higgs TTS 3 Research and Non-Commercial License, 2026-07-08** (F0208) | higgs-audio v3 TTS | **custom, new, deferred**; reads as `commercial_forbidden` |
| **Moonshine AI Community License** (F0202, F0217) | moonshine legacy non-English models | **custom, deferred** (ruled); default tier is MIT |
| Llama 3.2 inheritance | orpheus-tts (card Apache-2.0, base_model Llama-3.2-3B-Instruct, F0250) | **unusual**: card license may not govern |
| bilibili Model Use License (F0213) | IndexTTS (parked) | custom |
| BreezeBlue Research and Non-Commercial License v1.1 (F0216) | Breeze TTS 2 (parked) | custom |
| proprietary | elevenlabs-tts, deepgram-nova, assemblyai-universal, openai-speech | closed |

## 6. Accepted candidates

### 6a. Registry rows

The same content is in `rows.yaml` (validated against `docs/schemas/registry.schema.json`; no slug or artifact
collides with `corpus-index.tsv`). Declared packages are the documented install path, each cited in §6b notes.

```yaml
category: speech_audio
products:
- slug: whisper
  display_name: Whisper
  type: model
  org: openai
  github: openai/whisper
  huggingface_model: openai/whisper-large-v3-turbo
  pypi: openai-whisper
- slug: canary
  display_name: Canary
  type: model
  org: nvidia
  huggingface_model: nvidia/canary-1b-v2
- slug: parakeet
  display_name: Parakeet
  type: model
  org: nvidia
  huggingface_model: nvidia/parakeet-tdt-0.6b-v3
- slug: moonshine
  display_name: Moonshine
  type: model
  org: moonshine-ai
  github: moonshine-ai/moonshine
  huggingface_model: moonshine-ai/moonshine-tiny
  pypi: moonshine-voice
- slug: mms
  display_name: MMS (Massively Multilingual Speech)
  type: model
  org: meta
  huggingface_model: facebook/mms-1b-all
- slug: seamless-m4t
  display_name: SeamlessM4T
  type: model
  org: meta
  github: facebookresearch/seamless_communication
  huggingface_model: facebook/seamless-m4t-v2-large
- slug: wav2vec
  display_name: wav2vec 2.0 / HuBERT
  type: model
  org: meta
  huggingface_model: facebook/wav2vec2-base-960h
- slug: qwen-asr
  display_name: Qwen3-ASR
  type: model
  org: alibaba-cloud
  github: QwenLM/Qwen3-ASR
  huggingface_model: Qwen/Qwen3-ASR-1.7B
  pypi: qwen-asr
- slug: kyutai-stt
  display_name: Kyutai STT
  type: model
  org: kyutai
  github: kyutai-labs/delayed-streams-modeling
  huggingface_model: kyutai/stt-2.6b-en
- slug: granite-speech
  display_name: Granite Speech
  type: model
  org: ibm
  github: ibm-granite/granite-speech-models
  huggingface_model: ibm-granite/granite-speech-4.1-2b
- slug: voxtral
  display_name: Voxtral
  type: model
  org: mistral-ai
  huggingface_model: mistralai/Voxtral-Mini-4B-Realtime-2602
- slug: kokoro
  display_name: Kokoro
  type: model
  org: hexgrad
  github: hexgrad/kokoro
  huggingface_model: hexgrad/Kokoro-82M
  pypi: kokoro
- slug: xtts
  display_name: XTTS
  type: model
  org: coqui
  huggingface_model: coqui/XTTS-v2
- slug: f5-tts
  display_name: F5-TTS
  type: model
  org: swivid
  github: SWivid/F5-TTS
  huggingface_model: SWivid/F5-TTS
  pypi: f5-tts
- slug: cosyvoice
  display_name: CosyVoice
  type: model
  org: alibaba-cloud
  github: QwenAudio/CosyVoice
  huggingface_model: FunAudioLLM/Fun-CosyVoice3-0.5B-2512
- slug: fish-speech
  display_name: Fish Audio S2 (Fish-Speech)
  type: model
  org: fish-audio
  github: fishaudio/fish-speech
  huggingface_model: fishaudio/s2-pro
- slug: dia
  display_name: Dia
  type: model
  org: nari-labs
  github: nari-labs/dia
  huggingface_model: nari-labs/Dia-1.6B
- slug: sesame-csm
  display_name: CSM (Conversational Speech Model)
  type: model
  org: sesame
  github: SesameAILabs/csm
  huggingface_model: sesame/csm-1b
- slug: orpheus-tts
  display_name: Orpheus TTS
  type: model
  org: canopy-labs
  github: canopyai/Orpheus-TTS
  huggingface_model: canopylabs/orpheus-3b-0.1-ft
- slug: chatterbox
  display_name: Chatterbox
  type: model
  org: resemble-ai
  github: resemble-ai/chatterbox
  huggingface_model: ResembleAI/chatterbox
  pypi: chatterbox-tts
- slug: melotts
  display_name: MeloTTS
  type: model
  org: myshell-ai
  github: myshell-ai/MeloTTS
  huggingface_model: myshell-ai/MeloTTS-English
- slug: zonos
  display_name: Zonos
  type: model
  org: zyphra
  github: Zyphra/Zonos
  huggingface_model: Zyphra/Zonos-v0.1-transformer
- slug: higgs-audio
  display_name: Higgs Audio
  type: model
  org: boson-ai
  github: boson-ai/higgs-audio
  huggingface_model: bosonai/higgs-tts-2-3b-base
- slug: qwen-tts
  display_name: Qwen3-TTS
  type: model
  org: alibaba-cloud
  github: QwenLM/Qwen3-TTS
  huggingface_model: Qwen/Qwen3-TTS-12Hz-1.7B-Base
  pypi: qwen-tts
- slug: vibevoice
  display_name: VibeVoice
  type: model
  org: microsoft
  github: microsoft/VibeVoice
  huggingface_model: microsoft/VibeVoice-ASR
- slug: moshi
  display_name: Moshi
  type: model
  org: kyutai
  github: kyutai-labs/moshi
  huggingface_model: kyutai/moshiko-pytorch-bf16
  pypi: moshi
- slug: personaplex
  display_name: PersonaPlex
  type: model
  org: nvidia
  github: NVIDIA/personaplex
  huggingface_model: nvidia/personaplex-7b-v1
- slug: faster-whisper
  display_name: faster-whisper
  type: software
  org: systran
  github: SYSTRAN/faster-whisper
  pypi: faster-whisper
- slug: whisper-cpp
  display_name: whisper.cpp
  type: software
  org: ggml-org-georgi-gerganov
  github: ggml-org/whisper.cpp
- slug: whisperx
  display_name: WhisperX
  type: software
  org: m-bain
  github: m-bain/whisperX
  pypi: whisperx
- slug: espnet
  display_name: ESPnet
  type: software
  org: espnet
  github: espnet/espnet
  pypi: espnet
- slug: speechbrain
  display_name: SpeechBrain
  type: software
  org: speechbrain
  github: speechbrain/speechbrain
  pypi: speechbrain
- slug: coqui-tts
  display_name: Coqui TTS (Idiap fork)
  type: software
  org: idiap
  github: idiap/coqui-ai-TTS
  pypi: coqui-tts
- slug: piper
  display_name: Piper
  type: software
  org: open-home-foundation
  github: OHF-Voice/piper1-gpl
  pypi: piper-tts
- slug: sherpa-onnx
  display_name: sherpa-onnx
  type: software
  org: k2-fsa
  github: k2-fsa/sherpa-onnx
  pypi: sherpa-onnx
- slug: vosk
  display_name: Vosk
  type: software
  org: alpha-cephei
  github: alphacep/vosk-api
  pypi: vosk
- slug: pyannote-audio
  display_name: pyannote.audio
  type: software
  org: pyannote
  github: pyannote/pyannote-audio
  pypi: pyannote.audio
- slug: silero-vad
  display_name: Silero VAD
  type: software
  org: silero
  github: snakers4/silero-vad
  pypi: silero-vad
- slug: elevenlabs-tts
  display_name: ElevenLabs TTS
  type: model
  org: elevenlabs
  homepage: https://elevenlabs.io/text-to-speech
- slug: deepgram-nova
  display_name: Deepgram Nova
  type: model
  org: deepgram
  homepage: https://deepgram.com/learn/introducing-nova-3-speech-to-text-api
- slug: assemblyai-universal
  display_name: AssemblyAI Universal
  type: model
  org: assemblyai
  homepage: https://www.assemblyai.com/universal
- slug: openai-speech
  display_name: OpenAI speech models
  type: model
  org: openai
  homepage: https://developers.openai.com/api/docs/guides/speech-to-text
```

### 6b. Evidence table

| slug | open status | license(s) + source | archived/fork | last push | last release | adoption signal | member checkpoints/SKUs | org GitHub/HF handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| whisper | open-weights | code MIT (F0001); weights: large-v3-turbo MIT, large-v3/small/base/tiny Apache-2.0 per cardData (F0104) | no/no (F0001) | 2026-08-31 (F0001) | v20250625, 2025-06-26 (F0270; PyPI F0241) | HF 30d: large-v3-turbo 6,477,272; large-v3 4,600,554 (F0104); PyPI openai-whisper 5,190,666/mo (F0142) | large-v3-turbo, large-v3, medium, small, base, tiny (+ .en) (F0104); Distil-Whisper folds in per ruling (F0141) | openai / openai | PyPI is the documented install: README `pip install -U openai-whisper` (F0252). Distil-Whisper is Hugging Face's, not OpenAI's (org distil-whisper, F0141); folded only because the ruling says so. |
| canary | open-weights | CC-BY-4.0 (canary-1b-v2, canary-qwen-2.5b, 1b-flash, 180m-flash); legacy canary-1b CC-BY-NC-4.0 (F0103) | n/a (HF only) | HF lastModified 2026-08-31 (F0103) | no GitHub release (model on HF) | HF 30d: canary-1b-v2 56,469; canary-qwen-2.5b 35,182 (F0103, F0188) | canary-1b-v2, canary-qwen-2.5b, canary-1b-flash, canary-180m-flash, canary-1b (F0103) | nvidia / nvidia | CC-BY-4.0 → permissive_non_osi per ruling; legacy canary-1b is NC but current release governs. Engine is NeMo Speech (NVIDIA-NeMo/Speech, F0053), a separate row. |
| parakeet | open-weights | CC-BY-4.0 on every listed checkpoint (F0105) | n/a (HF only) | HF lastModified 2026-08-05 (F0105) | n/a (weights on HF only; no GitHub repo declared) | HF 30d: tdt-0.6b-v3 563,206; ctc-1.1b 372,919; tdt-0.6b-v2 193,528 (F0105) | tdt-0.6b-v3, tdt-0.6b-v2, ctc-1.1b, ctc-0.6b, rnnt-0.6b, rnnt-1.1b, tdt_ctc-110m, tdt_ctc-0.6b-ja (F0105) | nvidia / nvidia |  |
| moonshine | open-weights | code MIT; models MIT by default; legacy non-streaming non-English models under the noncommercial Moonshine Community License (LICENSE text F0202; F0217 https://moonshine.ai/license) | no/no (F0003) | 2026-08-31 (F0003) | v0.1.5, 2026-08-24 (F0056) | HF 30d: moonshine-tiny 36,479; streaming-tiny 36,400; streaming-medium 22,403 (F0199); PyPI moonshine-voice 18,696/mo (F0145) | tiny, base, streaming-tiny/small/medium, tiny-ja/ar/uk, es (F0198, F0199) | moonshine-ai / moonshine-ai | Org renamed from usefulsensors: ungh.cc resolves usefulsensors/moonshine to moonshine-ai/moonshine (F0296); HF author UsefulSensors returns no models (F0106). Old package useful-moonshine 1,081/mo points to usefulesensors (F0146). README: `pip install moonshine-voice` (F0218). Split license stays deferred per ruling. |
| mms | source-available | CC-BY-NC-4.0 on all checkpoints (F0108) | code lives in facebookresearch/fairseq, archived (F0009) | fairseq push 2025-09-30, archived (F0009); HF lastModified 2023-09 max (F0108) | fairseq v0.12.2, 2022-06-27 (F0055) | HF 30d: mms-1b-all 283,610; mms-lid-1024 172,451; mms-tts-eng 147,460 (F0108) | mms-1b-all, mms-300m, mms-lid-126/256/1024, mms-tts-* per language (F0108) | facebookresearch / facebook | Covers ASR, TTS and LID. Dormant: code repo archived. Distinct from the head dataset mms-lab-data (no artifact overlap). CC-BY-NC → commercial_forbidden. |
| seamless-m4t | source-available | LICENSE file is CC-BY-NC-4.0 text (F0203; GitHub label 'other', F0002); weights CC-BY-NC-4.0 (F0111) | no/no (F0002) | 2026-09-08 (F0002) | no published GitHub release (ungh releases/latest 404, F0059) | HF 30d: seamless-m4t-v2-large 300,967; hf-seamless-m4t-medium 118,859 (F0111) | seamless-m4t-v2-large, seamless-m4t-large/medium, unity-small (F0111) | facebookresearch / facebook | Slug drops the version (v2). Speech translation kept here per ruling. |
| wav2vec | open-weights | Apache-2.0 on all checkpoints (F0109, F0110) | code in fairseq, archived (F0009) | HF lastModified 2023-10-31 max (F0110) | fairseq v0.12.2, 2022-06-27 (F0055) | HF 30d: wav2vec2-base 2,178,817; wav2vec2-base-960h 1,438,759; hubert-large-ls960-ft 314,662 (F0109, F0110) | wav2vec2-base/-960h, xls-r-300m, large-xlsr-53, conformer-rope; hubert-base/large/xlarge (F0109, F0110) | facebookresearch / facebook | One family row per ruling. Slug avoids the '2' version token. Dormant, still heavily downloaded (a backbone for fine-tunes). |
| qwen-asr | open-weights | code Apache-2.0 (F0007); weights Apache-2.0 (F0112) | no/no (F0007) | 2026-06-26 (F0007) | no published GitHub release (ungh releases/latest 404, F0058); PyPI 0.0.6 2026-01-30 (F0162) | HF 30d: 1.7B 1,924,880; 0.6B 553,397 (F0112); PyPI qwen-asr 675,395/mo (F0162) | Qwen3-ASR-1.7B, -0.6B, -hf variants (F0112) | QwenLM / Qwen | README: `pip install -U qwen-asr` (F0256). Slug has no version token; index precedent (qwen3-embedding) keeps it, see §9. |
| kyutai-stt | open-weights | code MIT (Python) + Apache (Rust) per README; STT weights CC-BY-4.0 (F0224); repo label apache-2.0 (F0005); TTS weights CC-BY-4.0 (F0117) | no/no (F0005) | 2026-01-26 (F0005) | no published GitHub release (ungh releases/latest 404, F0062) | HF 30d: canonical stt-2.6b-en and stt-1b-en_fr report 0 (native format); stt-2.6b-en-trfs 15,491; folded tts-1.6b-en_fr 227,723 (F0113, F0117) | stt-2.6b-en, stt-1b-en_fr (+ -trfs/-mlx/-candle); folded TTS: tts-1.6b-en_fr, tts-0.75b-en-public (F0113, F0117) | kyutai-labs / kyutai | Kyutai TTS folds here per ruling (same DSM repo). Pocket TTS is a separate repo, see §9. |
| granite-speech | open-weights | README states Apache 2.0 (F0212; GitHub license field null, F0006); weights Apache-2.0 (F0116) | no/no (F0006) | 2026-09-16 (F0006) | no published GitHub release (ungh releases/latest 404, F0061) | HF 30d: 4.1-2b 165,481; 4.1-2b-plus 115,244; 4.1-2b-nar 83,364 (F0116) | speech-3.2-8b, 3.3-2b/8b, 4.1-2b(+plus,+nar), 5.0-470m-turboctc, granite-4.0-1b-speech (F0116) | ibm-granite / ibm-granite | A search result puts Granite Speech 4.1 2B at 5.33% avg WER on the Open ASR Leaderboard (W0002). |
| voxtral | open-weights | Mini/Realtime Apache-2.0; Voxtral-4B-TTS-2603 CC-BY-NC-4.0 (F0118, F0186) | n/a (HF only) | HF lastModified 2026-03-31 (F0186) | n/a (weights on HF only; no GitHub repo declared) | HF 30d: Mini-4B-Realtime 1,788,164; Mini-3B 259,546 (F0118) | Voxtral-Mini-3B-2507, Voxtral-Mini-4B-Realtime-2602; Voxtral-4B-TTS-2603 (F0118) | mistralai / mistralai | Voxtral Small 24B is chat-first and parked (ruling). The TTS member is NC; the ASR line governs as current release — flag for the scorer. mistral-common on PyPI is Mistral's general tokenizer lib, not this product (F0168). |
| kokoro | open-weights | code Apache-2.0 (F0008); weights Apache-2.0 (F0119) | no/no (F0008) | 2025-08-06 (F0008) | no published GitHub release (ungh releases/latest 404, F0060); PyPI 0.9.4 2025-04-05 (F0160) | HF 30d: Kokoro-82M 11,674,701 (F0119); PyPI kokoro 274,131/mo (F0160) | Kokoro-82M, Kokoro-82M-v1.1-zh (F0119) | hexgrad / hexgrad | README: `pip install kokoro` (F0253). Dormant >12 months by push/release, yet the most-downloaded TTS model. #5 open-weights on AA Speech Arena per search (W0007). |
| xtts | source-available | Coqui Public Model License 1.0.0, non-commercial (text F0207; cardData F0120) | n/a (HF only) | HF lastModified 2023-12-11 (F0120) | n/a | HF 30d: XTTS-v2 6,815,205 (F0120) | XTTS-v2, XTTS-v1 (F0120) | coqui / coqui | Coqui (the company) is gone; upstream coqui-ai/TTS last push 2024-08-16 (F0010). CPML stays deferred per ruling. The engine continues as the Idiap fork (coqui-tts row). |
| f5-tts | source-available | code MIT (F0014); weights CC-BY-NC-4.0 (F0122, F0221) | no/no (F0014) | 2026-09-21 (F0014) | 1.1.22, 2026-07-23 (F0063) | HF 30d: SWivid/F5-TTS 905,144 (F0122); PyPI f5-tts 114,012/mo (F0167) | F5-TTS, E2-TTS base models (F0258) | SWivid / SWivid | README: `pip install f5-tts` (F0258); lab badge X-LANCE (SJTU) (F0258). Org slug from the GitHub handle; the maintainer may prefer an SJTU X-LANCE org. |
| cosyvoice | open-weights | code Apache-2.0 (F0054); weights Apache-2.0 (F0123) | no/no (F0054) | 2026-05-25 (F0054) | no published GitHub release (ungh releases/latest 404, F0248) | HF 30d: Fun-CosyVoice3-0.5B-2512 193,282; CosyVoice2-0.5B 4,510 (F0123) | CosyVoice-300M(-SFT/-Instruct), CosyVoice2-0.5B, Fun-CosyVoice3-0.5B-2512 (F0123) | QwenAudio (GitHub) / FunAudioLLM (HF) | Repo moved: ungh.cc resolves FunAudioLLM/CosyVoice to QwenAudio/CosyVoice (F0052); canonical metadata F0054. Package trap: PyPI `cosyvoice` is lucasjinreal's GPL-3.0 repackaging (F0182), not declared. |
| fish-speech | source-available | Fish Audio Research License (updated 2026-03-07) covers the codebase AND weights (F0204, F0228; identical text on s2-pro, F0205); s1-mini and fish-speech-1.x weights CC-BY-NC-SA-4.0 (F0121) | no/no (F0015) | 2026-09-16 (F0015) | v1.5.1, 2025-05-31 (F0070) | HF 30d: s2-pro 56,764; fish-speech-1.5 3,751; s1-mini 1,962 (F0121) | S2 Pro, S1-mini (OpenAudio), fish-speech-1.2/1.4/1.5 (F0121) | fishaudio / fishaudio | Code is no longer Apache: README 'This codebase and its associated model weights are released under FISH AUDIO RESEARCH LICENSE' (F0228). Deferred per ruling. #2 open-weights on AA Speech Arena per search (W0007). Package trap: PyPI `fish-speech` is AnyaCoder's GUI (F0172). |
| dia | open-weights | code Apache-2.0 (F0016); weights Apache-2.0 (F0126) | no/no (F0016) | 2025-11-19 (F0016) | no published GitHub release (ungh releases/latest 404, F0067) | HF 30d: Dia-1.6B 28,524; Dia-1.6B-0626 10,647; Dia2-2B 3,209 (F0126) | Dia-1.6B, Dia-1.6B-0626, Dia2-1B, Dia2-2B (F0126); Dia2 repo nari-labs/dia2 (F0017) | nari-labs / nari-labs | Dia2 is a version of the line (separate repo, Apache-2.0, push 2025-11-29, F0017). |
| sesame-csm | open-weights | code Apache-2.0 (F0011); weights Apache-2.0, gated=auto (F0125) | no/no (F0011) | 2025-05-27 (F0011) | no published GitHub release (ungh releases/latest 404, F0069) | HF 30d: csm-1b 139,102 (F0125) | csm-1b (F0125) | SesameAILabs / sesame | Activity rests on the HF card edit 2025-12-01 (F0125); repo quiet since 2025-05. |
| orpheus-tts | open-weights | code Apache-2.0 (F0021); card Apache-2.0 but base_model meta-llama/Llama-3.2-3B-Instruct (F0250) | no/no (F0021) | 2025-12-05 (F0021) | no published GitHub release (ungh releases/latest 404, F0066) | HF 30d: orpheus-3b-0.1-ft 70,180 (F0124, F0250) | orpheus-3b-0.1-ft, orpheus-3b-0.1-pretrained (F0124) | canopyai / canopylabs | Card README gated (HTTP 401, F0219), so the Llama-inheritance question can't be read from the card text; flag for scorer. |
| chatterbox | open-weights | code MIT (F0020); weights MIT (F0127) | no/no (F0020) | 2026-07-21 (F0020) | v0.1.2, 2025-06-13 (F0064); PyPI 0.1.7 2026-03-26 (F0171) | HF 30d: chatterbox 1,721,415 (F0127); PyPI chatterbox-tts 168,744/mo (F0171) | chatterbox, chatterbox-turbo(-ONNX), chatterbox-nano, Chatterbox-Multilingual-* (F0127) | resemble-ai / ResembleAI | README: `pip install chatterbox-tts` (F0254). |
| melotts | open-weights | code MIT (F0018); weights MIT (F0128) | no/no (F0018) | 2024-12-24 (F0018) | v0.1.2, 2024-03-01 (F0074) | HF 30d: MeloTTS-English 267,672; -English-v3 61,851; -Korean 61,490 (F0128) | English/v2/v3, Korean, Japanese, Chinese, Spanish, French (F0128) | myshell-ai / myshell-ai | Dormant (no push since 2024-12). PyPI `melotts` 2,502/mo has no repository URL (F0170): not declared. |
| zonos | open-weights | code Apache-2.0 (F0025); weights Apache-2.0 incl. ZONOS2 (F0131, F0192) | no/no (F0025) | 2025-03-05 (F0025); ZONOS2 on HF 2026-06-22 (F0192) | no published GitHub release (ungh releases/latest 404, F0077) | HF 30d: v0.1-transformer 114,310; ZONOS2-GGUF 10,611 (F0131) | Zonos-v0.1-transformer, -hybrid, ZONOS1-GGUF, ZONOS2, ZONOS2-GGUF (F0131) | Zyphra / Zyphra | GitHub quiet since 2025-03 but the line shipped ZONOS2 in 2026-06 on HF. PyPI `zonos` points to a placeholder repo URL (F0169): not declared. |
| higgs-audio | source-available | code Apache-2.0 (F0211); v2 weights: Boson Higgs Audio 2 Community License, based on the Meta Llama 3 Community License (F0210); v3 TTS weights: Boson Higgs TTS 3 Research and Non-Commercial License (F0208); v3 STT weights Apache-2.0 (F0130) | no/no (F0022) | 2026-06-05 (F0022) | no published GitHub release (ungh releases/latest 404, F0071) | HF 30d: higgs-tts-2-3b-base 180,091; higgs-tts-3-4b 99,684; audio-v2-tokenizer 64,654 (F0130) | higgs-tts-2-3b-base, higgs-tts-3-4b, higgs-audio-v3-(8b-)stt(-v2) (F0130) | boson-ai / bosonai | Current TTS release (v3) is non-commercial, so open status = source-available. Both custom licenses deferred per ruling. Line now also ships STT (Apache-2.0). |
| qwen-tts | open-weights | code Apache-2.0 (F0023); weights Apache-2.0 (F0114) | no/no (F0023) | 2026-03-17 (F0023) | no published GitHub release (ungh releases/latest 404, F0076); PyPI 0.1.1 2026-02-06 (F0159) | HF 30d: 12Hz-1.7B-Base 3,923,955; 12Hz-1.7B-CustomVoice 2,435,822 (F0114); PyPI qwen-tts 208,685/mo (F0159) | 12Hz-1.7B/0.6B Base, CustomVoice, VoiceDesign; Tokenizer-12Hz (F0114) | QwenLM / Qwen | README: `pip install -U qwen-tts` (F0257). |
| vibevoice | open-weights | code MIT (F0019); weights MIT (F0132) | no/no (F0019) | 2026-09-03 (F0019) | no published GitHub release (ungh releases/latest 404, F0078) | HF 30d: VibeVoice-ASR 740,302; VibeVoice-1.5B 688,963; Realtime-0.5B 216,557 (F0132) | TTS-1.5B, Realtime-0.5B, ASR(-7B/-HF/-BitNet/-Streaming-1.5B/-7B), AcousticTokenizer (F0132) | microsoft / microsoft | 2025-09-05: Microsoft 'removed the VibeVoice-TTS code from this repository'; TTS-1.5B row says 'Disabled' (F0226). The family now leads with ASR, so the row declares VibeVoice-ASR (740,302/30d) as its artifact; TTS-1.5B stays a member. Ruled as TTS: see §9 Q3. |
| moshi | open-weights | code Apache-2.0 repo label (F0024), PyPI moshi MIT (F0151); weights CC-BY-4.0 (F0115) | no/no (F0024) | 2026-09-09 (F0024) | latest tag rustymimi-0.2.2, 2024-09-22 (F0073); PyPI 0.2.13 2026-02-12 (F0151) | HF 30d: moshiko-pytorch-bf16 179,111 (F0115); PyPI moshi 34,480/mo (F0151) | moshiko/moshika in pytorch/candle/mlx/q8/q4, moshika-rag (F0115) | kyutai-labs / kyutai | README: `pip install -U moshi` (F0255). Code license label (Apache) vs PyPI (MIT) differ; both permissive. |
| personaplex | open-weights | code MIT (F0027); weights NVIDIA Open Model License, gated=auto (F0107, F0251) | no/no (F0027) | 2026-03-02 (F0027) | no published GitHub release (ungh releases/latest 404, F0072) | HF 30d: personaplex-7b-v1 192,918 (F0251) | personaplex-7b-v1 (F0107) | NVIDIA / nvidia | base_model kyutai/moshiko-pytorch-bf16 (F0251): a Moshi derivative. NVIDIA Open Model License → permissive_non_osi (already named tier). |
| faster-whisper | open | MIT (F0030, F0155) | no/no (F0030) | 2025-11-19 (F0030) | v1.2.1, 2025-10-31 (F0075) | PyPI 8,271,086/mo (F0155) | — | SYSTRAN | README: `pip install faster-whisper` (F0259). |
| whisper-cpp | open | MIT (F0026) | no/no (F0026) | 2026-09-24 (F0026) | v1.9.4, 2026-09-11 (F0081) | stars only: 53,918 (F0026); no official package; HF ggerganov/whisper.cpp reports 0 downloads (F0273) | — | ggml-org | Not in the index (llama-cpp and ggml are). Package trap: pywhispercpp 313,798/mo is a third-party binding (absadiki, F0165); not declared. |
| whisperx | open | BSD-2-Clause (F0029, F0163) | no/no (F0029) | 2026-08-30 (F0029) | v3.8.6, 2026-05-25 (F0079) | PyPI 328,332/mo (F0163) | — | m-bain | README: `pip install whisperx` (F0260). |
| espnet | open | Apache-2.0 (F0031, F0242) | no/no (F0031) | 2026-09-25 (F0031) | v.202610.post2, 2026-09-24 (F0084); PyPI 202610.post2 (F0242) | PyPI 14,784/mo (F0147) | — | espnet | ecosyste.ms reports a stale latest release (0.10.6, 2022, F0147); pypi.org JSON shows 202610.post2 uploaded 2026-09-24 (F0242). README: `pip install espnet` (F0262). |
| speechbrain | open | Apache-2.0 (F0028, F0174) | no/no (F0028) | 2026-08-27 (F0028) | v1.1.1, 2026-08-27 (F0086) | PyPI 979,442/mo (F0174) | — | speechbrain | README: `pip install speechbrain` (F0261). |
| coqui-tts | open | MPL-2.0 (F0012, F0150) | fork of coqui-ai/TTS (F0012); not archived | 2026-06-10 (F0012) | v0.27.5, 2026-01-26 (F0065) | PyPI coqui-tts 132,494/mo (F0150); upstream TTS package still 66,079/mo (F0149) | — | idiap | Fork flag is true (source coqui-ai/TTS, F0012); the fork is the maintained line. README: `pip install coqui-tts` (F0267). |
| piper | open | GPL-3.0 now (F0036, F0143); old rhasspy/piper MIT, archived (F0035) | no/no (F0036); rhasspy/piper archived (F0035) | 2026-09-17 (F0036) | v1.8.0, 2026-09-04 (F0085) | PyPI piper-tts 904,480/mo (F0143); piper-voices on HF reports 0 downloads (F0140) | voices in rhasspy/piper-voices (MIT card, F0140) | OHF-Voice | README carries the Open Home Foundation badge (F0222); `pip install piper-tts` (F0222). |
| sherpa-onnx | open | Apache-2.0 (F0034, F0177) | no/no (F0034) | 2026-09-17 (F0034) | v1.13.8, 2026-09-10 (F0082) | PyPI 1,278,805/mo (F0177) | — | k2-fsa | Install doc: `pip install sherpa-onnx` (F0272). Kaldi/icefall parked (§7). |
| vosk | open | Apache-2.0 (F0041, F0153) | no/no (F0041) | 2026-08-09 (F0041) | GitHub v0.3.50, 2024-04-22 (F0080); PyPI 0.3.45, 2022-12-14 (F0243) | PyPI 666,339/mo (F0153) | — | alphacep | Install page: `pip3 install vosk` (F0271). PyPI release lags GitHub. |
| pyannote-audio | open | code MIT (F0039, F0158); pretrained pipelines: speaker-diarization-3.1 MIT, community-1 CC-BY-4.0, all gated=auto (F0129) | no/no (F0039) | 2026-09-21 (F0039) | 4.0.7, 2026-06-30 (F0087) | PyPI 2,173,253/mo (F0173); HF speaker-diarization-3.1 7,376,915 and segmentation-3.0 5,466,483 (F0129, F0133) | speaker-diarization-3.1, -community-1, -precision; segmentation-3.0 (F0129, F0133) | pyannote / pyannote | README: `pip install pyannote.audio` (F0265). One software row; the HF pipelines are its members, not separate rows. |
| silero-vad | open | MIT (F0037, F0154) | no/no (F0037) | 2026-09-23 (F0037) | GitHub v6.2.1, 2026-02-24 (F0269); PyPI 6.2.3, 2026-09-23 (F0293) | PyPI 1,683,558/mo (F0154) | — | snakers4 | README: `pip install silero-vad` (F0266). |
| elevenlabs-tts | closed | proprietary API (W0012) | n/a | n/a | Eleven v3 dated Feb 2026 in a third-party table (W0005) | no public download channel | Eleven v3, Multilingual v2, Flash v2.5, Turbo v2.5 (W0012) | — | Surface = TTS models (ADR-005). Scribe (STT) is a separate surface, parked (§7). |
| deepgram-nova | closed | proprietary API (W0010) | n/a | n/a | Nova-3 listed as current in 2026 (W0005) | no public download channel | Nova-3 (W0010) | — | Slug drops the version. Deepgram Flux/Aura are separate surfaces, parked or out. |
| assemblyai-universal | closed | proprietary API (W0011) | n/a | n/a | Universal-3 Pro, 2026-02-03 (W0019); Universal-3.5 Pro per search (W0015, W0005) | no public download channel | Universal-2, Universal-3 Pro (+Streaming), Universal-3.5 Pro (W0011, W0019, W0005) | — | The /universal page still leads with Universal-2 (W0011); the blog dates Universal-3 Pro (W0019). |
| openai-speech | closed | proprietary API (W0014, W0018) | n/a | n/a | gpt-realtime-2.1 dated 2026-07-06 (W0005) | no public download channel | gpt-transcribe, gpt-4o-transcribe(-diarize), gpt-4o-mini-transcribe, whisper-1; gpt-4o-mini-tts, tts-1(-hd) (W0014, W0018); gpt-realtime (W0005) | — | Surface = the API's speech models (STT + TTS + realtime), not OpenAI as a platform. Open Whisper is the separate `whisper` row. |

### 6c. Source list (every id cited in §6b, with UTC fetch time)

- F0001 — 2026-09-26T19:59:11Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/openai%2Fwhisper
- F0002 — 2026-09-26T19:59:22Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fseamless_communication
- F0003 — 2026-09-26T19:59:22Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/moonshine-ai%2Fmoonshine
- F0005 — 2026-09-26T19:59:22Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kyutai-labs%2Fdelayed-streams-modeling
- F0006 — 2026-09-26T19:59:22Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ibm-granite%2Fgranite-speech-models
- F0007 — 2026-09-26T19:59:22Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/QwenLM%2FQwen3-ASR
- F0008 — 2026-09-26T19:59:22Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/hexgrad%2Fkokoro
- F0009 — 2026-09-26T19:59:22Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Ffairseq
- F0010 — 2026-09-26T19:59:23Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/coqui-ai%2FTTS
- F0011 — 2026-09-26T19:59:23Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SesameAILabs%2Fcsm
- F0012 — 2026-09-26T19:59:23Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/idiap%2Fcoqui-ai-TTS
- F0014 — 2026-09-26T19:59:23Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SWivid%2FF5-TTS
- F0015 — 2026-09-26T19:59:23Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/fishaudio%2Ffish-speech
- F0016 — 2026-09-26T19:59:23Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nari-labs%2Fdia
- F0017 — 2026-09-26T19:59:23Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nari-labs%2Fdia2
- F0018 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/myshell-ai%2FMeloTTS
- F0019 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2FVibeVoice
- F0020 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/resemble-ai%2Fchatterbox
- F0021 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/canopyai%2FOrpheus-TTS
- F0022 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/boson-ai%2Fhiggs-audio
- F0023 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/QwenLM%2FQwen3-TTS
- F0024 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kyutai-labs%2Fmoshi
- F0025 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Zyphra%2FZonos
- F0026 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ggml-org%2Fwhisper.cpp
- F0027 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVIDIA%2Fpersonaplex
- F0028 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/speechbrain%2Fspeechbrain
- F0029 — 2026-09-26T19:59:24Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/m-bain%2FwhisperX
- F0030 — 2026-09-26T19:59:25Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SYSTRAN%2Ffaster-whisper
- F0031 — 2026-09-26T19:59:25Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/espnet%2Fespnet
- F0034 — 2026-09-26T19:59:25Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/k2-fsa%2Fsherpa-onnx
- F0035 — 2026-09-26T19:59:25Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/rhasspy%2Fpiper
- F0036 — 2026-09-26T19:59:25Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OHF-Voice%2Fpiper1-gpl
- F0037 — 2026-09-26T19:59:25Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/snakers4%2Fsilero-vad
- F0039 — 2026-09-26T19:59:25Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/pyannote%2Fpyannote-audio
- F0041 — 2026-09-26T19:59:25Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/alphacep%2Fvosk-api
- F0052 — 2026-09-26T19:59:40Z — HTTP 200 — https://ungh.cc/repos/FunAudioLLM/CosyVoice
- F0053 — 2026-09-26T19:59:51Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVIDIA-NeMo%2FSpeech
- F0054 — 2026-09-26T19:59:52Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/QwenAudio%2FCosyVoice
- F0055 — 2026-09-26T19:59:53Z — HTTP 200 — https://ungh.cc/repos/facebookresearch/fairseq/releases/latest
- F0056 — 2026-09-26T19:59:53Z — HTTP 200 — https://ungh.cc/repos/moonshine-ai/moonshine/releases/latest
- F0058 — 2026-09-26T19:59:53Z — HTTP 404 — https://ungh.cc/repos/QwenLM/Qwen3-ASR/releases/latest
- F0059 — 2026-09-26T19:59:53Z — HTTP 404 — https://ungh.cc/repos/facebookresearch/seamless_communication/releases/latest
- F0060 — 2026-09-26T19:59:53Z — HTTP 404 — https://ungh.cc/repos/hexgrad/kokoro/releases/latest
- F0061 — 2026-09-26T19:59:53Z — HTTP 404 — https://ungh.cc/repos/ibm-granite/granite-speech-models/releases/latest
- F0062 — 2026-09-26T19:59:53Z — HTTP 404 — https://ungh.cc/repos/kyutai-labs/delayed-streams-modeling/releases/latest
- F0063 — 2026-09-26T19:59:54Z — HTTP 200 — https://ungh.cc/repos/SWivid/F5-TTS/releases/latest
- F0064 — 2026-09-26T19:59:54Z — HTTP 200 — https://ungh.cc/repos/resemble-ai/chatterbox/releases/latest
- F0065 — 2026-09-26T19:59:54Z — HTTP 200 — https://ungh.cc/repos/idiap/coqui-ai-TTS/releases/latest
- F0066 — 2026-09-26T19:59:54Z — HTTP 404 — https://ungh.cc/repos/canopyai/Orpheus-TTS/releases/latest
- F0067 — 2026-09-26T19:59:54Z — HTTP 404 — https://ungh.cc/repos/nari-labs/dia/releases/latest
- F0069 — 2026-09-26T19:59:54Z — HTTP 404 — https://ungh.cc/repos/SesameAILabs/csm/releases/latest
- F0070 — 2026-09-26T19:59:54Z — HTTP 200 — https://ungh.cc/repos/fishaudio/fish-speech/releases/latest
- F0071 — 2026-09-26T19:59:55Z — HTTP 404 — https://ungh.cc/repos/boson-ai/higgs-audio/releases/latest
- F0072 — 2026-09-26T19:59:55Z — HTTP 404 — https://ungh.cc/repos/NVIDIA/personaplex/releases/latest
- F0073 — 2026-09-26T19:59:55Z — HTTP 200 — https://ungh.cc/repos/kyutai-labs/moshi/releases/latest
- F0074 — 2026-09-26T19:59:55Z — HTTP 200 — https://ungh.cc/repos/myshell-ai/MeloTTS/releases/latest
- F0075 — 2026-09-26T19:59:55Z — HTTP 200 — https://ungh.cc/repos/SYSTRAN/faster-whisper/releases/latest
- F0076 — 2026-09-26T19:59:55Z — HTTP 404 — https://ungh.cc/repos/QwenLM/Qwen3-TTS/releases/latest
- F0077 — 2026-09-26T19:59:55Z — HTTP 404 — https://ungh.cc/repos/Zyphra/Zonos/releases/latest
- F0078 — 2026-09-26T19:59:55Z — HTTP 404 — https://ungh.cc/repos/microsoft/VibeVoice/releases/latest
- F0079 — 2026-09-26T19:59:56Z — HTTP 200 — https://ungh.cc/repos/m-bain/whisperX/releases/latest
- F0080 — 2026-09-26T19:59:56Z — HTTP 200 — https://ungh.cc/repos/alphacep/vosk-api/releases/latest
- F0081 — 2026-09-26T19:59:56Z — HTTP 200 — https://ungh.cc/repos/ggml-org/whisper.cpp/releases/latest
- F0082 — 2026-09-26T19:59:56Z — HTTP 200 — https://ungh.cc/repos/k2-fsa/sherpa-onnx/releases/latest
- F0084 — 2026-09-26T19:59:56Z — HTTP 200 — https://ungh.cc/repos/espnet/espnet/releases/latest
- F0085 — 2026-09-26T19:59:56Z — HTTP 200 — https://ungh.cc/repos/OHF-Voice/piper1-gpl/releases/latest
- F0086 — 2026-09-26T19:59:56Z — HTTP 200 — https://ungh.cc/repos/speechbrain/speechbrain/releases/latest
- F0087 — 2026-09-26T19:59:57Z — HTTP 200 — https://ungh.cc/repos/pyannote/pyannote-audio/releases/latest
- F0103 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=nvidia&search=canary&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0104 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=openai&search=whisper&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0105 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=nvidia&search=parakeet&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0106 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=UsefulSensors&search=moonshine&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0107 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=nvidia&search=personaplex&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0108 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=facebook&search=mms&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0109 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=facebook&search=hubert&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0110 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=facebook&search=wav2vec2&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0111 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=facebook&search=seamless&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0112 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=Qwen&search=ASR&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0113 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=kyutai&search=stt&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0114 — 2026-09-26T20:00:12Z — HTTP 200 — https://huggingface.co/api/models?author=Qwen&search=TTS&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0115 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=kyutai&search=moshi&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0116 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=ibm-granite&search=speech&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0117 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=kyutai&search=tts&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0118 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=mistralai&search=Voxtral&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0119 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=hexgrad&search=Kokoro&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0120 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=coqui&search=XTTS&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0121 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=fishaudio&search=s&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0122 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=SWivid&search=F5&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0123 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=FunAudioLLM&search=CosyVoice&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0124 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=canopylabs&search=orpheus&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0125 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=sesame&search=csm&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0126 — 2026-09-26T20:00:13Z — HTTP 200 — https://huggingface.co/api/models?author=nari-labs&search=Dia&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0127 — 2026-09-26T20:00:14Z — HTTP 200 — https://huggingface.co/api/models?author=ResembleAI&search=chatterbox&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0128 — 2026-09-26T20:00:14Z — HTTP 200 — https://huggingface.co/api/models?author=myshell-ai&search=MeloTTS&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0129 — 2026-09-26T20:00:14Z — HTTP 200 — https://huggingface.co/api/models?author=pyannote&search=diarization&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0130 — 2026-09-26T20:00:14Z — HTTP 200 — https://huggingface.co/api/models?author=bosonai&search=higgs&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0131 — 2026-09-26T20:00:14Z — HTTP 200 — https://huggingface.co/api/models?author=Zyphra&search=Zonos&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0132 — 2026-09-26T20:00:14Z — HTTP 200 — https://huggingface.co/api/models?author=microsoft&search=VibeVoice&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0133 — 2026-09-26T20:00:14Z — HTTP 200 — https://huggingface.co/api/models?author=pyannote&search=segmentation&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0140 — 2026-09-26T20:00:14Z — HTTP 200 — https://huggingface.co/api/models?author=rhasspy&search=piper&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0141 — 2026-09-26T20:00:14Z — HTTP 200 — https://huggingface.co/api/models?author=distil-whisper&search=distil&sort=downloads&limit=15&expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated
- F0142 — 2026-09-26T20:00:27Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/openai-whisper
- F0143 — 2026-09-26T20:00:27Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/piper-tts
- F0145 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/moonshine-voice
- F0146 — 2026-09-26T20:00:27Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/useful-moonshine
- F0147 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/espnet
- F0149 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/TTS
- F0150 — 2026-09-26T20:00:27Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/coqui-tts
- F0151 — 2026-09-26T20:00:27Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/moshi
- F0153 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/vosk
- F0154 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/silero-vad
- F0155 — 2026-09-26T20:00:27Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/faster-whisper
- F0158 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/pyannote-audio
- F0159 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/qwen-tts
- F0160 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/kokoro
- F0162 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/qwen-asr
- F0163 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/whisperx
- F0165 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/pywhispercpp
- F0167 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/f5-tts
- F0168 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/mistral-common
- F0169 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/zonos
- F0170 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/melotts
- F0171 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/chatterbox-tts
- F0172 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fish-speech
- F0173 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/pyannote.audio
- F0174 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/speechbrain
- F0177 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/sherpa-onnx
- F0182 — 2026-09-26T20:00:28Z — HTTP 200 — https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/cosyvoice
- F0186 — 2026-09-26T20:01:38Z — HTTP 200 — https://huggingface.co/api/models/mistralai/Voxtral-4B-TTS-2603?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=author
- F0188 — 2026-09-26T20:01:38Z — HTTP 200 — https://huggingface.co/api/models/nvidia/canary-qwen-2.5b?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=author
- F0192 — 2026-09-26T20:01:38Z — HTTP 200 — https://huggingface.co/api/models/Zyphra/ZONOS2?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated&expand[]=createdAt&expand[]=author
- F0198 — 2026-09-26T20:01:38Z — HTTP 200 — https://huggingface.co/api/models?author=moonshine-ai&limit=10&expand[]=downloads&expand[]=cardData&expand[]=lastModified
- F0199 — 2026-09-26T20:01:38Z — HTTP 200 — https://huggingface.co/api/models?search=moonshine&sort=downloads&limit=10&expand[]=downloads&expand[]=cardData&expand[]=lastModified
- F0202 — 2026-09-26T20:01:54Z — HTTP 200 — https://raw.githubusercontent.com/moonshine-ai/moonshine/HEAD/LICENSE
- F0203 — 2026-09-26T20:01:54Z — HTTP 200 — https://raw.githubusercontent.com/facebookresearch/seamless_communication/HEAD/LICENSE
- F0204 — 2026-09-26T20:01:55Z — HTTP 200 — https://raw.githubusercontent.com/fishaudio/fish-speech/HEAD/LICENSE
- F0205 — 2026-09-26T20:01:55Z — HTTP 200 — https://huggingface.co/fishaudio/s2-pro/raw/main/LICENSE.md
- F0207 — 2026-09-26T20:01:55Z — HTTP 200 — https://huggingface.co/coqui/XTTS-v2/raw/main/LICENSE.txt
- F0208 — 2026-09-26T20:01:56Z — HTTP 200 — https://huggingface.co/bosonai/higgs-tts-3-4b/raw/main/LICENSE
- F0210 — 2026-09-26T20:01:56Z — HTTP 200 — https://huggingface.co/bosonai/higgs-tts-2-3b-base/raw/main/LICENSE
- F0211 — 2026-09-26T20:01:57Z — HTTP 200 — https://raw.githubusercontent.com/boson-ai/higgs-audio/HEAD/LICENSE
- F0212 — 2026-09-26T20:01:57Z — HTTP 200 — https://raw.githubusercontent.com/ibm-granite/granite-speech-models/HEAD/README.md
- F0217 — 2026-09-26T20:01:58Z — HTTP 200 — https://huggingface.co/moonshine-ai/moonshine-es/raw/main/README.md
- F0218 — 2026-09-26T20:01:59Z — HTTP 200 — https://raw.githubusercontent.com/moonshine-ai/moonshine/HEAD/README.md
- F0219 — 2026-09-26T20:01:59Z — HTTP 401 — https://huggingface.co/canopylabs/orpheus-3b-0.1-ft/raw/main/README.md
- F0221 — 2026-09-26T20:02:00Z — HTTP 200 — https://huggingface.co/SWivid/F5-TTS/raw/main/README.md
- F0222 — 2026-09-26T20:02:00Z — HTTP 200 — https://raw.githubusercontent.com/OHF-Voice/piper1-gpl/HEAD/README.md
- F0224 — 2026-09-26T20:02:01Z — HTTP 200 — https://raw.githubusercontent.com/kyutai-labs/delayed-streams-modeling/HEAD/README.md
- F0226 — 2026-09-26T20:02:01Z — HTTP 200 — https://raw.githubusercontent.com/microsoft/VibeVoice/HEAD/README.md
- F0228 — 2026-09-26T20:02:02Z — HTTP 200 — https://raw.githubusercontent.com/fishaudio/fish-speech/HEAD/README.md
- F0241 — 2026-09-26T20:03:24Z — HTTP 200 — https://pypi.org/pypi/openai-whisper/json
- F0242 — 2026-09-26T20:03:24Z — HTTP 200 — https://pypi.org/pypi/espnet/json
- F0243 — 2026-09-26T20:03:24Z — HTTP 200 — https://pypi.org/pypi/vosk/json
- F0248 — 2026-09-26T20:03:43Z — HTTP 404 — https://ungh.cc/repos/QwenAudio/CosyVoice/releases/latest
- F0250 — 2026-09-26T20:03:48Z — HTTP 200 — https://huggingface.co/api/models/canopylabs/orpheus-3b-0.1-ft?expand[]=cardData&expand[]=downloads
- F0251 — 2026-09-26T20:03:49Z — HTTP 200 — https://huggingface.co/api/models/nvidia/personaplex-7b-v1?expand[]=cardData&expand[]=downloads
- F0252 — 2026-09-26T20:04:02Z — HTTP 200 — https://raw.githubusercontent.com/openai/whisper/HEAD/README.md
- F0253 — 2026-09-26T20:04:02Z — HTTP 200 — https://raw.githubusercontent.com/hexgrad/kokoro/HEAD/README.md
- F0254 — 2026-09-26T20:04:03Z — HTTP 200 — https://raw.githubusercontent.com/resemble-ai/chatterbox/HEAD/README.md
- F0255 — 2026-09-26T20:04:03Z — HTTP 200 — https://raw.githubusercontent.com/kyutai-labs/moshi/HEAD/README.md
- F0256 — 2026-09-26T20:04:03Z — HTTP 200 — https://raw.githubusercontent.com/QwenLM/Qwen3-ASR/HEAD/README.md
- F0257 — 2026-09-26T20:04:03Z — HTTP 200 — https://raw.githubusercontent.com/QwenLM/Qwen3-TTS/HEAD/README.md
- F0258 — 2026-09-26T20:04:03Z — HTTP 200 — https://raw.githubusercontent.com/SWivid/F5-TTS/HEAD/README.md
- F0259 — 2026-09-26T20:04:03Z — HTTP 200 — https://raw.githubusercontent.com/SYSTRAN/faster-whisper/HEAD/README.md
- F0260 — 2026-09-26T20:04:04Z — HTTP 200 — https://raw.githubusercontent.com/m-bain/whisperX/HEAD/README.md
- F0261 — 2026-09-26T20:04:04Z — HTTP 200 — https://raw.githubusercontent.com/speechbrain/speechbrain/HEAD/README.md
- F0262 — 2026-09-26T20:04:04Z — HTTP 200 — https://raw.githubusercontent.com/espnet/espnet/HEAD/README.md
- F0265 — 2026-09-26T20:04:05Z — HTTP 200 — https://raw.githubusercontent.com/pyannote/pyannote-audio/HEAD/README.md
- F0266 — 2026-09-26T20:04:05Z — HTTP 200 — https://raw.githubusercontent.com/snakers4/silero-vad/HEAD/README.md
- F0267 — 2026-09-26T20:04:05Z — HTTP 200 — https://raw.githubusercontent.com/idiap/coqui-ai-TTS/HEAD/README.md
- F0269 — 2026-09-26T20:04:06Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/snakers4%2Fsilero-vad/releases?per_page=1
- F0270 — 2026-09-26T20:04:06Z — HTTP 200 — https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/openai%2Fwhisper/releases?per_page=1
- F0271 — 2026-09-26T20:04:13Z — HTTP 200 — https://alphacephei.com/vosk/install
- F0272 — 2026-09-26T20:04:14Z — HTTP 200 — https://k2-fsa.github.io/sherpa/onnx/python/install.html
- F0273 — 2026-09-26T20:05:27Z — HTTP 200 — https://huggingface.co/api/models/ggerganov/whisper.cpp?expand[]=downloads&expand[]=cardData&expand[]=lastModified
- F0293 — 2026-09-26T20:13:07Z — HTTP 200 — https://pypi.org/pypi/silero-vad/json
- F0296 — 2026-09-26T20:15:03Z — HTTP 200 — https://ungh.cc/repos/usefulsensors/moonshine
- W0002 — 2026-09-26T20:00:54Z — WebSearch — open-weight speech recognition model released 2026 Hugging Face open ASR leaderboard
- W0005 — 2026-09-26T20:01:37Z — WebFetch — https://futureagi.com/blog/best-voice-ai-august-2026/
- W0007 — 2026-09-26T20:01:37Z — WebSearch — Artificial Analysis speech arena leaderboard open weights TTS 2026
- W0010 — 2026-09-26T20:03:09Z — WebFetch — https://deepgram.com/learn/introducing-nova-3-speech-to-text-api
- W0011 — 2026-09-26T20:03:09Z — WebFetch — https://www.assemblyai.com/universal
- W0012 — 2026-09-26T20:03:09Z — WebFetch — https://elevenlabs.io/text-to-speech
- W0014 — 2026-09-26T20:03:09Z — WebFetch — https://developers.openai.com/api/docs/guides/speech-to-text
- W0015 — 2026-09-26T20:03:09Z — WebSearch — AssemblyAI Universal-3 Pro speech model announcement
- W0018 — 2026-09-26T20:03:09Z — WebFetch — https://developers.openai.com/api/docs/guides/text-to-speech
- W0019 — 2026-09-26T20:03:09Z — WebFetch — https://www.assemblyai.com/blog/introducing-universal-3-pro

## 7. Parked candidates

| name | reason | source | fetch date |
|---|---|---|---|
| NVIDIA NeMo (Speech) | already mapped (`nemo`, tail `finetuning_code`); move recommended (§3, §9 Q1) | F0053, F0223 | 2026-09-26 |
| Bark (Suno) | reserve not needed (no main row failed); unmaintained, push 2024-08-19 | F0040, F0134 | 2026-09-26 |
| Parler-TTS | reserve not needed; unmaintained, push 2024-12-10; PyPI 1,968/mo | F0038, F0181 | 2026-09-26 |
| StyleTTS2 | reserve not needed; unmaintained, push 2024-08-10 | F0043 | 2026-09-26 |
| Spark-TTS | reserve not needed; push 2025-04-09; weights CC-BY-NC-SA-4.0; HF 911/30d | F0042, F0137 | 2026-09-26 |
| IndexTTS (IndexTTS-2 / 2.5) | reserve not needed; active (v2.5.0 2026-08-13, 23,971 stars), bilibili custom license; proposed in §9 | F0044, F0090, F0136, F0213 | 2026-09-26 |
| OmniVoice (k2-fsa) | reserve not needed; active (0.2.1 2026-07-16), HF 1,369,984/30d, code Apache-2.0 / weights CC-BY-NC; proposed in §9 | F0049, F0138, F0176, F0214, F0249 | 2026-09-26 |
| FunASR (toolkit) | reserve not needed; active (push 2026-09-24), MIT, PyPI 268,564/mo; proposed in §9 | F0047, F0180 | 2026-09-26 |
| Kaldi | legacy (issue #602 proposal, W0020); push 2025-09-22; license label "other", text not read | F0045 | 2026-09-26 |
| icefall (k2) | research recipes (issue #602 proposal, W0020); would fold into the k2-fsa line (sherpa-onnx) | F0046 | 2026-09-26 |
| Cohere Transcribe | new 2026 release, not on the ruled list: proposed addition (§9 Q5). HF 213,697/30d, Apache-2.0, gated=auto | F0187, W0006 | 2026-09-26 |
| MOSS-Transcribe-Diarize (OpenMOSS) | new 2026 release: proposed addition (§9 Q5). HF 163,483/30d, Apache-2.0, repo created 2026-05-13 | F0193, F0235, W0008 | 2026-09-26 |
| Breeze TTS 2 (BreezeBlue) | new 2026 release: proposed addition (§9 Q5). #1 open-weights on AA arena per search; HF 13,603/30d; research/NC weights | F0200, F0215, F0216, W0003, W0007 | 2026-09-26 |
| Kyutai Pocket TTS | identity unclear: fold into `kyutai-stt` or separate (§9 Q4). Own repo (9,642 stars, created 2026-01-07), PyPI pocket-tts 87,767/mo | F0152, F0196, F0234 | 2026-09-26 |
| ARK-ASR (AutoArk) | identity unclear: `AutoArk-AI/ARK-ASR-3B` resolves to `Edge0/ARK-ASR-3B`; HF 7,172/30d | F0197, W0008 | 2026-09-26 |
| Step-Audio-EditX (StepFun) | adoption thin for a seed (HF 3,896/30d, 978 stars); card lists no weights license; revisit | F0190, F0227, F0231, W0007 | 2026-09-26 |
| Fun-ASR-Nano | SKU of the FunAudioLLM line; decide with FunASR | F0139 | 2026-09-26 |
| MOSS-TTSD | small (1,400 stars); decide with the OpenMOSS proposal | F0232 | 2026-09-26 |
| Speaches | boundary: multi-engine OpenAI-compatible speech server (faster-whisper + Kokoro + Piper); in scope only if serving wrappers count as engines (§9 Q6) | F0233, W0017 | 2026-09-26 |
| Kokoro-FastAPI | boundary: single-model API wrapper, not a speech engine | F0229, W0017 | 2026-09-26 |
| DiariZen (BUT) | small (467 stars); pipeline alternative to pyannote, revisit | F0238, W0016 | 2026-09-26 |
| TEN VAD | license label "other", text not read; 2,210 stars | F0230 | 2026-09-26 |
| Hertz-dev (Standard Intelligence) | unmaintained, push 2025-01-05 | F0240, W0009 | 2026-09-26 |
| Human-1 | identity unclear: `JoshTalksAI/Human-1` resolves to `VoiceArena/Human-1`; HF 100/30d | F0194, W0009 | 2026-09-26 |
| Voxtral Small 24B | boundary → foundation models (chat-first, ruled out) | F0118 | 2026-09-26 |
| Qwen2.5-Omni | boundary → `multimodal_models` (omni, ruled out) | W0009 | 2026-09-26 |
| Cartesia Sonic | closed; possible frontier comparator (#1 Provider Voice Elo per third-party table), see §9 Q7 | W0005 | 2026-09-26 |
| Microsoft MAI-Transcribe / MAI-Voice | closed long-tail | W0005 | 2026-09-26 |
| Deepgram Flux | closed; separate Deepgram surface (conversational STT/TTS), long-tail | W0005 | 2026-09-26 |
| ElevenLabs Scribe | closed; separate STT surface from `elevenlabs-tts`, long-tail unless the maintainer wants both | W0005 | 2026-09-26 |

## 8. Reconciled counts

Raw signals = every candidate name collected: the 43 named rows of the ruled list, its 7 reserve names, its 2 fold
names, the 2 legacy names from the issue #602 seed proposal (Kaldi, k2/icefall: W0020; the RUNBOOK brief does not
name them), and 28 names surfaced by live search and fetches.

- duplicate signals: **10** (Distil-Whisper → whisper; Kyutai TTS → kyutai-stt; Voxtral TTS → voxtral; ZONOS2 → zonos;
  Higgs Audio v3 STT → higgs-audio; IndexTTS-2.5 → IndexTTS; upstream coqui-ai/TTS → coqui-tts; rhasspy/piper →
  piper; gpt-realtime → openai-speech; Canary-Qwen → canary)
- unique candidates: **72** (43 + 7 + 2 + 20 discovered)
- accepted: **42**; parked: **30**
- raw_signals = duplicate_signals + unique_candidates → **82 = 10 + 72** ✓
- unique_candidates = accepted + parked → **72 = 42 + 30** ✓

Note: the issue calls the list "41 rows", but its own tables name 11 + 14 + 2 + 10 + 2 + 4 = **43**.

Third-party packages found and **not** declared (package trap; not counted as signals): `pywhispercpp` (F0165),
`cosyvoice` (F0182), `fish-speech` (F0172), `zonos` (F0169), `melotts` (F0170), `mistral_common` (F0168),
`orpheus-speech` (F0148, install path not verified).

Breadth: names surfaced by search that the brief did not name: Cohere Transcribe, MOSS-Transcribe-Diarize,
MOSS-TTSD, ARK-ASR, Breeze TTS 2, Step-Audio-EditX, Kyutai Pocket TTS, Speaches, Kokoro-FastAPI, DiariZen,
TEN VAD, Hertz-dev, Human-1, Fun-ASR-Nano, Cartesia Sonic, MAI-Transcribe/MAI-Voice, Deepgram Flux,
ElevenLabs Scribe, Qwen2.5-Omni, plus the new members ZONOS2, Higgs TTS 3, Voxtral TTS, Dia2 and VibeVoice-ASR.

## 9. Open questions for the maintainer

1. **Move `nemo` from `finetuning_code` into `speech_audio`, and change its github to `NVIDIA-NeMo/Speech`?**
   Recommend **yes** to both: the old repo name redirects there (F0051) and the product is now speech-only (F0223).
   Rename the display name to "NVIDIA NeMo Speech". This also fixes a stale artifact in the index today.
2. **Qwen slugs: `qwen-asr`/`qwen-tts` (prompt rule, no version token) or `qwen3-asr`/`qwen3-tts` (index precedent:
   `qwen3-embedding`, `qwen3-reranker`, `qwen3guard`)?** Recommend **`qwen-asr`/`qwen-tts`**, which will not go stale
   at Qwen4; the display names keep "Qwen3".
3. **VibeVoice: keep it in the seed, declaring the VibeVoice-ASR checkpoint as its artifact, now that Microsoft removed the TTS code (F0226) and the line leads with ASR
   (F0132)?** Recommend **keep one family row** declared on `microsoft/VibeVoice-ASR` (the active, most-downloaded
   member), with the TTS code removal noted in prose.
4. **Kyutai Pocket TTS: fold into `kyutai-stt` or its own row?** It is a separate repo and package (F0234, F0152).
   Recommend **its own row** (`pocket-tts`), and renaming `kyutai-stt`'s display name to "Kyutai STT/TTS (DSM)"
   since the ruling folds the DSM TTS into it.
5. **Add the 2026 releases the list missed?** Options: (a) add Cohere Transcribe, MOSS-Transcribe-Diarize, Breeze
   TTS 2, OmniVoice and IndexTTS now; (b) add only Cohere Transcribe, MOSS-Transcribe-Diarize and OmniVoice (the three
   with >150K HF downloads and an Apache-2.0 license on code or weights: Cohere weights
   F0187, MOSS weights and code F0193/F0235, OmniVoice code F0214); (c) none until promotion. Recommend **(a)**: each is verified live (§7). Breeze TTS 2 is #1 on the AA open-weights TTS board per search
   (W0007); Cohere Transcribe took #1 on the Open ASR Leaderboard at release (5.42% WER) but has since been passed
   by Granite Speech 4.1 (5.33%) and, per the same source, ARK-ASR and MOSS-Transcribe (W0002, W0006).
6. **Do multi-engine OpenAI-compatible speech servers (Speaches) count as speech-first engines?** Recommend
   **yes, later**: it is speech-only, so it passes the litmus, but it is a serving layer over engines already
   listed; revisit with the `inference_code` boundary.
7. **Closed comparators: add Cartesia Sonic as a fifth?** A third-party table puts Sonic-3.6 at #1 Provider Voice
   Elo (W0005). Recommend **yes, after a primary-source fetch** of Cartesia's own page (not done in this run).
8. **Higgs Audio: which checkpoint is canonical?** The row declares `bosonai/higgs-tts-2-3b-base` (most downloads)
   while openness is read from the current v3 non-commercial release. Recommend **keep v2 as the artifact** and
   record both licenses; defer both texts per the ruling.
9. **F5-TTS org: `swivid` (GitHub handle) or an SJTU X-LANCE org?** README carries the X-LANCE badge (F0258).
   Recommend **`swivid`** until the maintainers state an affiliation on the org page.
