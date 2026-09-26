# Research runbook (read before research-prompt.md)

The research-prompt.md file has the shared preamble and the category briefs. This file covers
**how to fetch** in this environment and **where to write**. Where the two disagree, this file
wins.

## Freshness is the whole point

The user asked specifically for live web research. Your training data is not a source: every
fact must trace to a fetch made during this run, today, 2026-09-26 or later. Concretely:

1. **Every curl-able fact goes through `research/rfetch.sh <dir_slug> <url> "<label>"`.** It
   saves the body to `research/<dir_slug>/raw/Fnnnn.body` and logs the id, UTC timestamp, HTTP
   code and sha256 in `research/<dir_slug>/fetch-log.tsv`. Cite the `Fnnnn` id beside each fact
   in the evidence table.
2. **WebSearch and WebFetch results** (no raw body to save) are logged by hand, one line per
   call, in `research/<dir_slug>/web-log.tsv` with columns `id (Wnnnn)`, `utc timestamp`
   (`date -u +%FT%TZ`), `tool`, `query or url`, `verbatim excerpt supporting the fact (≤300
   chars)`. Cite the `Wnnnn` id.
3. A fact with no `F` or `W` id is **unsourced**. The audit agent will fail your sweep for it.
   If you know something but can't fetch it, write "not fetched" rather than stating it.
4. Use WebSearch actively to **discover** candidates. Search for 2025–2026 releases, "awesome-*"
   lists, leaderboards, and "alternatives to X". Don't limit yourself to the starting leads, which
   are just someone's recollection. Aim for breadth: a good sweep surfaces candidates that the
   brief did not name.

## What works from this container (tested 2026-09-26)

| Need | Use | Notes |
|---|---|---|
| Repo metadata: canonical name, archived, fork, license key, pushed_at, stars | `https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/<owner>%2F<repo>` | Best single source. |
| Canonical name after a rename/redirect, stars, pushedAt | `https://ungh.cc/repos/<owner>/<repo>` | `repo` field is canonical. |
| Latest release | `https://ungh.cc/repos/<o>/<r>/releases/latest` or ecosyste.ms `.../releases?per_page=1` | |
| LICENSE / README body | `https://raw.githubusercontent.com/<o>/<r>/HEAD/LICENSE` (try LICENSE, LICENSE.md, LICENSE.txt, COPYING) and `.../README.md` | Read the text: the label lies. |
| GitHub search / discovery | WebSearch; WebFetch on `https://github.com/topics/<topic>` or `github.com/<org>` | **`api.github.com` and curl on `github.com` are blocked for repos outside this session (403).** Don't treat that 403 as a finding. |
| Hugging Face model/dataset | `https://huggingface.co/api/models/<id>` (add `?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated`), search `https://huggingface.co/api/models?author=<org>&sort=downloads&limit=50` | `downloads` is the rolling 30 days. Weights license is in `cardData.license`; read the LICENSE file on the repo when it's `other`. |
| PyPI downloads | `https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/<name>` (`downloads`, `downloads_period`) — primary. `https://pypistats.org/api/packages/<name>/recent` — fallback, rate-limits (429): wait 20s, retry twice | |
| PyPI metadata | `https://pypi.org/pypi/<name>/json` | project_urls tell you whether the package *is* the product. |
| npm | `https://api.npmjs.org/downloads/point/last-month/<name>`, `https://registry.npmjs.org/<name>` | |
| Other pages (vendor sites, datasheets, docs, blogs, leaderboards) | WebFetch (log it as W), or rfetch if plain HTML is fine | |

HTTP 429/403/5xx on a working endpoint means "not now." Retry with backoff. If a fact still
won't come, write "fetch did not complete," which is different from a measured absence.

## Where to write

Everything goes under `research/<dir_slug>/`:

- `sweep.md`: the full output-contract document from research-prompt.md (sections 1–9).
  Evidence cells cite `F`/`W` ids.
- `rows.yaml`: section 6a alone, as a valid registry file (`category: <slug>` + `products:`).
  Validate it before you finish, like this:
  `uv run python -c "import json,yaml,jsonschema;jsonschema.validate(yaml.safe_load(open('research/<dir_slug>/rows.yaml')),json.load(open('docs/schemas/registry.schema.json')));print('ok')"`
  For a dual brief (5a+5b, 6a+6b), write one rows file per proposed category:
  `rows.<slug>.yaml`.
- `fetch-log.tsv`, `raw/`, `web-log.tsv`: the evidence trail.

Do not touch anything outside `research/<dir_slug>/`. Don't edit `sources/`, don't commit, and
don't push.

Dedup with `research/corpus-index.tsv` (or read `sources/` directly: you're inside the repo checkout). Registry rows in the index are candidates already found, so they don't
count as new.

## Brief 0: Speech & audio (issue #602), dir_slug `speech_audio`, category slug `speech_audio`

**This category is already approved** (ruled 2026-09-25 on issue #602). Your job is to turn the
ruled 41-row list into a verified, paste-ready seed, not to reopen the rulings. The rulings you
must apply:
- Shape `extends: {model: model, software: software}`, weights adopt 0.4 / cap 0.6, in Model
  components → Models.
- Models and engines are separate rows. **Speech-first** engines (faster-whisper, whisper.cpp,
  WhisperX, sherpa-onnx, Vosk, Piper, NeMo, ESPnet, SpeechBrain, Coqui TTS) live here. General
  runtimes stay in `inference_code` (check the index: whisper.cpp may sit under `ggml`).
- Out: chat-first audio LLMs and omni models. In: SeamlessM4T, pyannote.audio and Silero VAD.
  Music and SFX go to media generation, not here. Speech datasets stay where they are.
- CC-BY-4.0 → `permissive_non_osi`, CC-BY-NC → `commercial_forbidden`. The Coqui, Fish Audio,
  Higgs and Moonshine custom licenses stay deferred (still record the text and URL).

**The ruled list:**
- ASR: Whisper, Canary, Parakeet, Moonshine, MMS, SeamlessM4T v2, wav2vec2/HuBERT, Qwen3-ASR,
  Kyutai STT, Granite Speech, Voxtral.
- TTS: Kokoro, XTTS-v2, F5-TTS, CosyVoice, Fish Audio (S2 Pro/S1-mini), Dia, CSM-1B, Orpheus,
  Chatterbox, MeloTTS, Zonos, Higgs Audio, Qwen3-TTS, VibeVoice.
- S2S: Moshi, PersonaPlex.
- Engines: faster-whisper, whisper.cpp, WhisperX, NeMo, ESPnet, SpeechBrain, Coqui TTS (Idiap
  fork), Piper, sherpa-onnx, Vosk.
- Pipeline: pyannote.audio, Silero VAD.
- Closed comparators: ElevenLabs, Deepgram Nova-3, AssemblyAI Universal, OpenAI speech.
- Reserve (use only if a main-list row fails): Bark, Parler-TTS, StyleTTS2, Spark-TTS,
  IndexTTS-2, OmniVoice, FunASR. Distil-Whisper folds into Whisper and Kyutai TTS into Kyutai.

Verify every row live (identity, canonical artifact, license text, activity, adoption signal),
pitch each slug at the product line, resolve collisions against the index, and run a
WebSearch sweep for significant 2026 speech releases the list misses. Report those as
*proposed additions* in §9, not as accepted rows. Sections 1–4 can be short; §5–§8 are the
substance.

## Finishing: independent audit, then push (child sessions)

Before you push, **spawn a fresh subagent with the Agent tool as your auditor** (general-purpose).
It must not inherit your conclusions, so give it only the paths. It checks:

1. **Re-fetch 15 claims live**, spread across the whole evidence table (every third or fourth
   row, not the first 15): license, activity date, adoption number and canonical identity.
   Compare each one to what the sweep says. Numbers drifting by a day are fine; a wrong license,
   a wrong owner, an archived repo reported active, or a figure off by more than 25% is not.
2. **Unsourced facts:** every evidence cell must carry an `F`/`W` id that exists in the logs, and
   the log row for it must show HTTP 200 (or a WebFetch/WebSearch entry with an excerpt).
3. **Every artifact in the rows file resolves live:** github via ecosyste.ms (not archived unless
   the sweep says so), HF via its API, and packages via PyPI/npm JSON.
4. **Schema and dedup:** the rows file validates against `docs/schemas/registry.schema.json`, and
   no slug or artifact collides with `research/corpus-index.tsv`.
5. **The counts reconcile** (both equations), and the section-2 metrics are computed from
   section 6.
6. **Recency and breadth:** the fetch timestamps are from this run, and the sweep surfaced
   candidates the brief did not name via search (list them). Flag any claim that reads like
   recall, for example a release described with no fetch behind it.

The auditor writes `research/<dir_slug>/audit.md` with PASS/FAIL per check and each issue. Fix
every issue, then have the auditor (or a second fresh one) re-check only the fixed items and
append the result. Then:

```bash
git add -f research/<dir_slug>
git commit -m "research(<dir_slug>): live candidate sweep and audit"
git push -u origin HEAD
```

Your final message: the verdict(s), the accepted and parked counts, the audit's final status,
and the branch you pushed. No PR.
