# Speech & audio seed: 2026-09-26

## Scope and boundary

This batch seeds the preliminary `speech_audio` category ruled on issue #602 on 2026-09-25. The
membership test: **is the primary input or output a speech waveform, and is speech the headline
rather than one modality among several?** Recognition (ASR), synthesis (TTS), speech-to-speech and
full-duplex conversation, and the pipeline components around them (diarization, voice activity
detection) are in. Models and engines are separate rows, and a speech-first engine lives here while a
general runtime does not.

The rulings, all recorded in the category's `comments` so the next editor applies rather than
re-derives them:

- **Out, by neighbor.** Chat-first audio LLMs and omni models (Voxtral Small 24B, Qwen2.5-Omni) go to
  the foundation-model categories or `multimodal_models`. Music and sound effects (Stable Audio,
  MusicGen, ACE-Step) go to `media_generation`. Speech datasets stay in `language_specific_datasets`
  or `training_synthetic_datasets`. General runtimes that also serve audio (llama.cpp, ggml, ONNX
  Runtime, Triton) stay in `inference_code` / `ml_frameworks`. Voice-agent orchestration goes to
  `orchestration_agents`. Single-model API wrappers (Kokoro-FastAPI) are not products here.
- **NVIDIA NeMo moves in** from the `finetuning_code` registry. `NVIDIA/NeMo` now redirects to
  `NVIDIA-NeMo/Speech`, whose README is titled NeMo Speech and installs `nemo-toolkit[asr,tts]`; LLM
  training lives in `nemo-rl` and `megatron-lm`, which are already on the map. The row's github was
  corrected and its display name is now "NVIDIA NeMo Speech".
- **Families fold into one row.** Distil-Whisper into `whisper`, the DSM Kyutai TTS into
  `kyutai-stt` (display name now "Kyutai STT/TTS (DSM)"), Canary-Qwen into `canary`, Voxtral TTS
  into `voxtral`, ZONOS2 into `zonos`, Higgs Audio v3 STT into `higgs-audio`, Dia2 into `dia`.
  Kyutai Pocket TTS is its own row, `pocket-tts`: a separate repository, package and model.
- **VibeVoice is one row, declared on VibeVoice-ASR.** Microsoft removed the TTS code on 2025-09-05
  and the line now leads with ASR; the TTS checkpoints stay members.
- **Qwen slugs drop the version token** (`qwen-asr`, `qwen-tts`); the display names keep "Qwen3".
- **Closed comparators are surfaces, not vendors** (ADR-005): ElevenLabs TTS, Deepgram Nova,
  AssemblyAI Universal, OpenAI's speech API models, and Cartesia Sonic.

No row was scored. Each row carries identity and artifacts only, as the registry schema requires.

## Inputs swept

| Code | Input |
|---|---|
| R | The ruled list on issue #602 (43 named rows, 7 reserve, 2 folds) and the two legacy names in its seed proposal |
| L | Live discovery: WebSearch for 2025-2026 releases and leaderboards, and Hugging Face author searches sorted by downloads (top 15 per query) |
| X | The user's externally run TTS sweep (26 rows), re-verified live 21/21 on 2026-09-26 |

Every fact traces to a fetch made on 2026-09-26 (UTC). The full evidence trail - fetch log with
sha256, raw bodies, web log, the §6b evidence table and a two-pass independent audit - is on the
evidence branch `claude/research-speech_audio` under `research/speech_audio/`; the external sweep
is on `claude/research-kit` under `research/external_tts/`.

**Retrieval cutoff.** The ruled list and its reserve, plus WebSearch discovery and HF author searches
at 15 results each. Hugging Face task-filter sweeps (every `automatic-speech-recognition` or
`text-to-speech` model by downloads) were not run, so community fine-tunes and quantized re-uploads
are out of view. That is a coverage limit, not a rejection.

## Reconciled counts

A raw signal is one input naming one candidate. Duplicates are the folds listed above plus every
row of the external sweep that names a candidate R or L already counted (24 of its 26).

```text
raw_signals       = 108   (82 from R and L, 26 from X)
duplicate_signals = 34    (10 folds, 24 external rows already counted)
unique_candidates = 74    (72 from R and L, plus VoxCPM and Maya1 from X)
accepted          = 52
parked            = 22

108 = 34 + 74
 74 = 52 + 22
```

Against the sweep as audited (42 accepted, 30 parked), the decision record of 2026-09-26 moved
eight parked candidates to accepted - the `nemo` move, the five §9 Q5(a) additions (Cohere
Transcribe, MOSS-Transcribe-Diarize, Breeze TTS 2, OmniVoice, IndexTTS), Kyutai Pocket TTS and
Cartesia Sonic - and added VoxCPM and Maya1 from the external sweep.

No row collides with a head product, a retired alias, another registry row, or a resolution-ledger
ruling (`build.validate`, 0 errors).

## Organizations and handles

The seed introduces 31 organizations. Each has a minimal `sources/organizations/` file (empty
`products:` roster, as the #688 seed did) and its GitHub, Hugging Face or homepage accounts declared
in `sources/org_handles.yaml`. Accounts on existing orgs were declared where a row put an artifact
under a new owner: `QwenAudio` and `FunAudioLLM` (alibaba-cloud, CosyVoice), `NVIDIA-NeMo`
(nvidia), `ibm-granite` on GitHub (ibm) and `OpenBMB` on GitHub (openbmb). A handle whose account
name differs from the org slug carries a note. Handle coverage went up on every route and the
baseline was re-pinned upward; nothing was lowered.

Org mappings a reviewer should check: `silero` publishes under the `snakers4` account; `bilibili`
owns `index-tts` and `IndexTeam`, read from the bilibili Model Use License on the repository;
`swivid` is the GitHub handle behind F5-TTS, whose README carries an SJTU X-LANCE badge;
`open-home-foundation` owns `OHF-Voice`, read from the Piper README's badge.

## Accepted candidates

Order in the registry file: ASR models, TTS models, speech-to-speech models, speech-first engines
and pipeline components, closed comparators. The primary source is the row's canonical artifact;
the evidence table on the evidence branch carries the license, activity and adoption facts for each,
with their fetch ids.

| slug | type | org | primary source | fetched |
|---|---|---|---|---|
| `whisper` | model | `openai` | https://github.com/openai/whisper | 2026-09-26 |
| `canary` | model | `nvidia` | https://huggingface.co/nvidia/canary-1b-v2 | 2026-09-26 |
| `parakeet` | model | `nvidia` | https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3 | 2026-09-26 |
| `moonshine` | model | `moonshine-ai` | https://github.com/moonshine-ai/moonshine | 2026-09-26 |
| `mms` | model | `meta` | https://huggingface.co/facebook/mms-1b-all | 2026-09-26 |
| `seamless-m4t` | model | `meta` | https://github.com/facebookresearch/seamless_communication | 2026-09-26 |
| `wav2vec` | model | `meta` | https://huggingface.co/facebook/wav2vec2-base-960h | 2026-09-26 |
| `qwen-asr` | model | `alibaba-cloud` | https://github.com/QwenLM/Qwen3-ASR | 2026-09-26 |
| `kyutai-stt` | model | `kyutai` | https://github.com/kyutai-labs/delayed-streams-modeling | 2026-09-26 |
| `granite-speech` | model | `ibm` | https://github.com/ibm-granite/granite-speech-models | 2026-09-26 |
| `voxtral` | model | `mistral-ai` | https://huggingface.co/mistralai/Voxtral-Mini-4B-Realtime-2602 | 2026-09-26 |
| `cohere-transcribe` | model | `cohere` | https://huggingface.co/CohereLabs/cohere-transcribe-03-2026 | 2026-09-26 |
| `moss-transcribe-diarize` | model | `openmoss` | https://github.com/OpenMOSS/MOSS-Transcribe-Diarize | 2026-09-26 |
| `kokoro` | model | `hexgrad` | https://github.com/hexgrad/kokoro | 2026-09-26 |
| `xtts` | model | `coqui` | https://huggingface.co/coqui/XTTS-v2 | 2026-09-26 |
| `f5-tts` | model | `swivid` | https://github.com/SWivid/F5-TTS | 2026-09-26 |
| `cosyvoice` | model | `alibaba-cloud` | https://github.com/QwenAudio/CosyVoice | 2026-09-26 |
| `fish-speech` | model | `fish-audio` | https://github.com/fishaudio/fish-speech | 2026-09-26 |
| `dia` | model | `nari-labs` | https://github.com/nari-labs/dia | 2026-09-26 |
| `sesame-csm` | model | `sesame` | https://github.com/SesameAILabs/csm | 2026-09-26 |
| `orpheus-tts` | model | `canopy-labs` | https://github.com/canopyai/Orpheus-TTS | 2026-09-26 |
| `chatterbox` | model | `resemble-ai` | https://github.com/resemble-ai/chatterbox | 2026-09-26 |
| `melotts` | model | `myshell-ai` | https://github.com/myshell-ai/MeloTTS | 2026-09-26 |
| `zonos` | model | `zyphra` | https://github.com/Zyphra/Zonos | 2026-09-26 |
| `higgs-audio` | model | `boson-ai` | https://github.com/boson-ai/higgs-audio | 2026-09-26 |
| `qwen-tts` | model | `alibaba-cloud` | https://github.com/QwenLM/Qwen3-TTS | 2026-09-26 |
| `vibevoice` | model | `microsoft` | https://github.com/microsoft/VibeVoice | 2026-09-26 |
| `breeze-tts` | model | `breezeblue` | https://github.com/breezeblue-ai/breeze-tts | 2026-09-26 |
| `omnivoice` | model | `k2-fsa` | https://github.com/k2-fsa/OmniVoice | 2026-09-26 |
| `indextts` | model | `bilibili` | https://github.com/index-tts/index-tts | 2026-09-26 |
| `voxcpm` | model | `openbmb` | https://github.com/OpenBMB/VoxCPM | 2026-09-26 |
| `maya1` | model | `maya-research` | https://huggingface.co/maya-research/maya1 | 2026-09-26 |
| `pocket-tts` | model | `kyutai` | https://github.com/kyutai-labs/pocket-tts | 2026-09-26 |
| `moshi` | model | `kyutai` | https://github.com/kyutai-labs/moshi | 2026-09-26 |
| `personaplex` | model | `nvidia` | https://github.com/NVIDIA/personaplex | 2026-09-26 |
| `nemo` | software | `nvidia` | https://github.com/NVIDIA-NeMo/Speech | 2026-09-26 |
| `faster-whisper` | software | `systran` | https://github.com/SYSTRAN/faster-whisper | 2026-09-26 |
| `whisper-cpp` | software | `ggml-org-georgi-gerganov` | https://github.com/ggml-org/whisper.cpp | 2026-09-26 |
| `whisperx` | software | `m-bain` | https://github.com/m-bain/whisperX | 2026-09-26 |
| `espnet` | software | `espnet` | https://github.com/espnet/espnet | 2026-09-26 |
| `speechbrain` | software | `speechbrain` | https://github.com/speechbrain/speechbrain | 2026-09-26 |
| `coqui-tts` | software | `idiap` | https://github.com/idiap/coqui-ai-TTS | 2026-09-26 |
| `piper` | software | `open-home-foundation` | https://github.com/OHF-Voice/piper1-gpl | 2026-09-26 |
| `sherpa-onnx` | software | `k2-fsa` | https://github.com/k2-fsa/sherpa-onnx | 2026-09-26 |
| `vosk` | software | `alpha-cephei` | https://github.com/alphacep/vosk-api | 2026-09-26 |
| `pyannote-audio` | software | `pyannote` | https://github.com/pyannote/pyannote-audio | 2026-09-26 |
| `silero-vad` | software | `silero` | https://github.com/snakers4/silero-vad | 2026-09-26 |
| `elevenlabs-tts` | model | `elevenlabs` | https://elevenlabs.io/text-to-speech | 2026-09-26 |
| `deepgram-nova` | model | `deepgram` | https://deepgram.com/learn/introducing-nova-3-speech-to-text-api | 2026-09-26 |
| `assemblyai-universal` | model | `assemblyai` | https://www.assemblyai.com/universal | 2026-09-26 |
| `openai-speech` | model | `openai` | OpenAI API speech-to-text guide on developers.openai.com (the row's `homepage`) | 2026-09-26 |
| `cartesia-sonic` | model | `cartesia` | https://www.cartesia.ai/sonic | 2026-09-26 |

### Additions verified in this seed session

The sweep researched the five Q5(a) additions, Pocket TTS and Cartesia before parking them; the
external sweep covered VoxCPM and Maya1. Where a row declares an artifact neither sweep fetched,
this session fetched it live on 2026-09-26. Those fetches (F0298-F0310) sit in the local
`research/speech_audio/fetch-log.tsv` of the seed session and were not pushed to the evidence
branch, so the URLs are given here:

| row | fact | URL | result |
|---|---|---|---|
| `voxcpm` | weights repo and license | https://huggingface.co/api/models?author=openbmb&search=VoxCPM | `openbmb/VoxCPM2`, Apache-2.0, 349,760 downloads/30d, modified 2026-08-18 |
| `voxcpm` | package is the documented install | https://raw.githubusercontent.com/OpenBMB/VoxCPM/HEAD/README.md, https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/voxcpm | README `pip install voxcpm`; package points to OpenBMB/VoxCPM, Apache-2.0, 83,892/month |
| `maya1` | weights and license | https://huggingface.co/api/models/maya-research/maya1 | Apache-2.0, 6,658 downloads/30d, modified 2026-07-11 |
| `breeze-tts` | code repository | https://ungh.cc/repos/breezeblue-ai/breeze-tts | "Official PyTorch inference for Breeze TTS 2", pushed 2026-09-09; the model card states Apache-2.0 code, research and non-commercial weights |
| `breeze-tts` | weights | https://huggingface.co/api/models/BreezeBlue/Breeze-TTS-2 | `breezeblue-research-and-non-commercial-license`, 13,603 downloads/30d |
| `indextts` | current checkpoint | https://raw.githubusercontent.com/index-tts/index-tts/HEAD/README.md, https://huggingface.co/api/models/IndexTeam/IndexTTS-2 | README links IndexTTS-2.5, -2, -1.5; the row declares `IndexTeam/IndexTTS-2.5` (13,651/30d, bilibili-model-license, the v2.5.0 release of 2026-08-13) |
| `cartesia-sonic` | primary page | https://www.cartesia.ai/sonic | "Sonic-3.6, Cartesia's streaming TTS API"; on-prem deployment offered, no weights |
| `cohere-transcribe` | code repository | https://ungh.cc/repos/CohereLabs/cohere-transcribe | 404: no GitHub repository at that name, so the row is Hub-only |

## Parked candidates

| candidate | reason | source (evidence id on the evidence branch) |
|---|---|---|
| Bark (Suno) | unmaintained, last push 2024-08-19; reserve not needed | F0040, F0134 |
| Parler-TTS | unmaintained, last push 2024-12-10 | F0038, F0181 |
| StyleTTS2 | unmaintained, last push 2024-08-10 | F0043 |
| Spark-TTS | quiet since 2025-04, CC-BY-NC-SA weights, 911 downloads/30d | F0042, F0137 |
| FunASR (toolkit) | active and MIT, but not in the decision record's additions; revisit at promotion | F0047, F0180 |
| Fun-ASR-Nano | SKU of the FunAudioLLM line; decide with FunASR | F0139 |
| Kaldi | legacy; license label "other", text not read | F0045, W0020 |
| icefall (k2) | research recipes; would fold into the k2-fsa line | F0046, W0020 |
| ARK-ASR (AutoArk) | identity unclear: the named repo resolves to `Edge0/ARK-ASR-3B` | F0197, W0008 |
| Step-Audio-EditX (StepFun) | thin adoption (3,896 downloads/30d) and no weights license on the card; the decision record keeps it parked | F0190, F0227, F0231 |
| MOSS-TTSD | small; decide with the OpenMOSS line | F0232 |
| Speaches | boundary: multi-engine OpenAI-compatible server; held until the `inference_code` boundary is revisited | F0233, W0017 |
| Kokoro-FastAPI | boundary: single-model API wrapper | F0229, W0017 |
| DiariZen (BUT) | small (467 stars); pyannote alternative, revisit | F0238, W0016 |
| TEN VAD | license label "other", text not read | F0230 |
| Hertz-dev | unmaintained, last push 2025-01-05 | F0240, W0009 |
| Human-1 | identity unclear: resolves to `VoiceArena/Human-1`, 100 downloads/30d | F0194, W0009 |
| Voxtral Small 24B | boundary: chat-first, foundation-model categories | F0118 |
| Qwen2.5-Omni | boundary: omni model, `multimodal_models`. No fetch carries it (audit issue 3); it rests on the ruling alone | none |
| Microsoft MAI-Transcribe / MAI-Voice | closed long tail | W0005 |
| Deepgram Flux | closed; a separate Deepgram surface, long tail | W0005 |
| ElevenLabs Scribe | closed; separate STT surface from `elevenlabs-tts`, long tail | W0005 |

## Identity notes for promotion

- **Openness follows the current release, and several rows need it read carefully.** Higgs Audio
  declares the v2 checkpoint (most downloads) while its current TTS release, v3, is non-commercial.
  Voxtral's Apache-2.0 ASR line governs over its CC-BY-NC TTS member. Fish-Speech's code as well as
  its weights moved to the Fish Audio Research License (2026-03-07). Piper's maintained engine is
  GPL-3.0 at `OHF-Voice/piper1-gpl`; the archived `rhasspy/piper` was MIT. Moonshine's default
  models are MIT, its legacy non-English models under a noncommercial community license. OmniVoice's
  `cardData.license` is null; the CC-BY-NC claim rests on card body text. Breeze TTS 2 splits
  Apache-2.0 code from non-commercial weights.
- **Orpheus TTS** carries an Apache-2.0 card on a Llama-3.2-3B-Instruct base, and the card README is
  gated, so whether the Llama license governs could not be read.
- **Package traps.** PyPI `cosyvoice`, `fish-speech`, `zonos`, `melotts`, `pywhispercpp` and
  `mistral-common` are not these products and are not declared.
- **Adoption instruments.** `whisper-cpp` has no official package and its HF weights repo reports
  zero downloads, so it will read stars. `kyutai-stt`'s canonical native-format repos report zero;
  its usage shows on the `-trfs` member. The five closed rows have no public download channel.
- **Custom licenses deferred to the maintainer license-rulings issue:** Coqui Public Model License
  1.0.0 (`xtts`), Fish Audio Research License (`fish-speech`), Boson Higgs Audio 2 Community License
  and Boson Higgs TTS 3 Research and Non-Commercial License (`higgs-audio`), Moonshine AI Community
  License (`moonshine`), bilibili Model Use License (`indextts`), BreezeBlue Research and
  Non-Commercial License (`breeze-tts`). Products carrying one are deferred at promotion.

## Open questions for the maintainer

1. **Capability ladder.** No single quantity orders ASR, TTS, speech-to-speech and engines. The
   category's `scoring_recipe.note` carries the sweep's five-rung "frontier coverage of speech tasks"
   proposal and the per-type reading (WER board, arena Elo, full duplex, what an engine serves).
   `build-rubric` decides at promotion.
2. **Speaches and FunASR.** Speaches passes the litmus but is a serving layer over engines already
   listed; FunASR is an active MIT toolkit the decision record did not add. Both are parked, not
   rejected.
3. **Org records for individuals and projects.** `hexgrad`, `m-bain`, `swivid`, `espnet`,
   `speechbrain`, `pyannote`, `silero`, `k2-fsa`, `nari-labs`, `breezeblue` and `maya-research` are
   typed `unknown` rather than guessed; promotion should settle each type from the org's own page.
4. **Higgs Audio's canonical artifact** stays v2 with both licenses recorded (sweep §9 Q8).
