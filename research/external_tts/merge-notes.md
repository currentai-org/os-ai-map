# External TTS sweep (user-supplied, 2026-09-26): merge notes for the speech_audio seed

Source: a text-to-speech research run the user did outside this session, pasted in on
2026-09-26. It was scoped as a `text_to_speech_models` category, but #602 already ruled one
`speech_audio` category, so the rows go into that seed. `rows.speech_audio.yaml` holds them with
org slugs mapped to the corpus: qwen → `alibaba-cloud`, mistral → `mistral-ai`, fun-audio-llm →
`alibaba-cloud`. Piper is typed `software`, per the ruling that it's an engine.

## Verification (this session, live)
I re-fetched 21 claims into `fetch-log.tsv` / `raw/`. **All 21 match**: licenses, archive
status and HF download counts are exact, and GitHub stars are within 0.3%.
- Filled a gap the source left: Breeze-TTS-2 has **13,603 downloads/mo** and 628 likes, and
  was created 2026-08-25 (F0011).
- OmniVoice: `cardData.license` is null (F0013). The source's CC-BY-NC claim rests on card body
  text, so read the card before scoring.
- The Piper license flip is confirmed: `rhasspy/piper` is archived and MIT (F0006), the current
  engine is GPL-3.0 (F0005), and `piper-tts` draws 904,480 installs/mo (F0007).
- CosyVoice: the canonical repo is `QwenAudio/CosyVoice` (F0019).
- `crosscheck.py`: 0 collisions with the corpus.

## Against the ruled 41-row list (#602)
- **Agrees (on the ruled list):** Kokoro, XTTS, F5-TTS, CosyVoice, Fish Speech, Dia, Sesame CSM,
  Orpheus, Chatterbox, Zonos, Higgs Audio, Qwen3-TTS, VibeVoice, Piper, ElevenLabs, OpenAI speech.
- **Promotes from the reserve:** Bark, IndexTTS(-2), OmniVoice. The ruling said reserve rows come
  in only when a main row fails. Decide at the seed.
- **New, not on the ruled list:** VoxCPM (OpenBMB, 37.9K stars, Apache-2.0), Step-Audio-EditX
  (StepFun), Voxtral TTS (Mistral, CC-BY-NC-4.0, released 2026-03), Pocket TTS (Kyutai,
  CC-BY-4.0 weights), Maya1 (Apache-2.0), Breeze TTS 2 (non-commercial, 2026-08), and Cartesia
  Sonic as a closed comparator.
- **Conflicts with the ruling:**
  - Pocket TTS vs "Kyutai TTS folds into the Kyutai family". Pocket TTS is a separately named
    repo and HF model, so decide whether it's its own row or folds into Kyutai.
  - MeloTTS is on the ruled list; the source rejects it (last push 2024-12). Keep it and record
    the dormancy, or swap in a reserve row.
- **Out of the source's scope (ASR, S2S, engines, pipeline):** still come from the speech
  session's sweep.
