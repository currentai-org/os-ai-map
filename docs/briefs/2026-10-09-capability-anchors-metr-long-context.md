# Capability anchors: METR time horizons and long-context retrieval, 2026-10-09

This brief carries out the capability part of ruling R-2026-10-08-n (refs #723, OSO-6218):
"Evaluate METR time horizons and long-context retrieval as candidate capability anchors." It
follows point 4 of the Mozilla comparison in
`docs/sweeps/2026-10-07-mozilla-state-of-osai-comparison.md`, which found that no frontier open
family on the map cites a METR time horizon or a long-context retrieval benchmark. It evaluates
and recommends. It changes no score, basis, category or recipe. Like the other records in
`docs/briefs/` and `docs/sweeps/`, it describes what its sources said on the date above, and it
gets refreshed by a new brief, not edited.

Every outside claim cites a fetch made with `uv run python -m build.fetch_source` on 2026-10-09.
The digests and quotes are in [Sources](#sources). Map-side claims cite files in `sources/` on
`main` at the same date.

## The short answer

None of the candidates should become a primary anchor in any category. METR's time horizons stopped
being updated on 2026-09-08, and the current suite measures no open-weight model. Each of the
standalone long-context leaderboards stopped adding models between mid-2025 and January 2026, and
none of them has scored a release the map's frontier records currently read. The one long-context
instrument that is current, independently run and covers open and closed models alike is
**AA-LCR v1.1**. It is already inside the anchor that `base_pretrained` and `finetuned_chat` use,
at 5% of the Artificial Analysis Intelligence Index. The recommendation is to name it as a
tie-break inside that anchor, not to add a new one.

| Candidate | Recommendation | Where |
|---|---|---|
| METR task-completion time horizons | Reject as an anchor | Any category |
| RULER | Reject as an anchor. Per-product citation stays allowed | `base_pretrained`, `finetuned_chat` |
| NoLiMa | Reject | Any category |
| LongBench v2 | Reject as an anchor | `base_pretrained`, `finetuned_chat` |
| Fiction.LiveBench | Reject as an anchor | `base_pretrained`, `finetuned_chat` |
| OpenAI-MRCR (and Michelangelo MRCR) | Reject as an anchor. It is a dataset, not a leaderboard | `base_pretrained`, `finetuned_chat` |
| HELM Long Context | Reject | `base_pretrained`, `finetuned_chat` |
| AA-LCR v1.1 | **Tie-break** inside the existing Artificial Analysis anchor | `base_pretrained`, `finetuned_chat` |

## What an anchor has to do here

`docs/reference/capability.md` sets the tests. A candidate has to pass these:

- **Within one category.** A band is comparable only inside its category. All the candidates rank
  *models*, so the only categories they could anchor are the two model categories,
  `base_pretrained` and `finetuned_chat`. `multimodal_models` bands on `feature_matrix` with
  modality and GUI-agent tie-breaks, and nothing here measures that. `orchestration_agents`
  places harnesses against `openhands` and `langgraph`. METR does run some models inside Claude
  Code or Codex, but it reports the model, not the harness (see METR below), so it cannot place
  `claude-code` or `codex-cli`. `embeddings_retrieval` is anchored on MTEB/MMTEB, and
  `search_retrieval` bands on features. Long-context *retrieval* in the sense of these benchmarks
  means a language model finding facts in its own context window. That is a different task from
  an embedding model ranking passages, so none of these candidates bears on those two categories.
- **A `benchmark` basis that can be re-read.** "Re-reading it is the confirmation; the number is
  a property of a harness-plus-model pairing" (capability.md, `basis`). A source whose primary
  page cannot be read by `fetch_source` cannot confirm a band.
- **Per product, never per cluster.** `basis_detail` names the instrument *for this product*,
  never "a harness the product is absent from". A candidate is only useful where it scores the
  release a record actually reads.
- **Ladder rungs.** No category has calibrated capability rungs. `base_pretrained` declares
  `scoring_recipe.capability.anchor.primary: Artificial Analysis Intelligence Index`, with
  `bands: null` and `bands_status: NOT YET CALIBRATED`. `finetuned_chat` declares no capability
  block in its recipe at all. Its anchor exists only as the `artificialanalysis` and `lmarena`
  routes in `sources/signal_routing.yaml`, both `blocked_by: bridge`. So a new instrument could not
  slot into a rung. It could only be a primary, a fallback or a tie-break inside a peer
  comparison (`relative_to` / `relation`).

How the two model categories stand today (`sources/scores/`, 2026-10-09). 30 of the 32
`base_pretrained` products and 41 of the 42 `finetuned_chat` products carry `basis: benchmark`. The
`basis_detail` values are a mix: the Artificial Analysis index (16 records, 7 and 9), vendor
coding and agentic suites (SWE-bench, Terminal-Bench, DeepSWE) and older academic suites. The
frontier records that `basis_detail` ties to the Artificial Analysis index read current releases:
`claude-opus` (Claude Opus 5.5), `gpt-6` (GPT-6 Astra), `grok` (Grok 4.7), `gemini-pro` (Gemini
3.1 Pro Preview), `deepseek` (DeepSeek-V4.1-Flash) and `mimo-pro` (MiMo-V2.6-Pro).

## METR task-completion time horizons

**What it measures.** "The task duration (measured by human expert completion time) at which an
AI agent is predicted to succeed with a given level of reliability" (S1), reported at 50% and 80%.
The tasks are "drawn from RE-Bench, HCAST, and a set of shorter novel software tasks. These
primarily consist of software engineering, machine learning, and cybersecurity tasks" (S1).

**Who maintains it.** METR, "a research nonprofit". It "has not accepted funding from AI
companies, though we make use of significant free tokens" (S5).

**Cadence.** None. The page says "This page is no longer actively updated. LAST UPDATED September
8, 2026", and its changelog's last addition is "May 8th, 2026: Added Claude Mythos Preview
(early)" (S1). The page also says "You shouldn't treat our reporting as a complete record of the
most capable models", and that "some models were measured long after release and others were
skipped entirely" (S1). METR's research index lists newer measures since then, an "Expenditure
Horizon" (2026-07-21) and "MirrorCode" (2026-04-10), but no time-horizon release after "Time
Horizon 1.1" on 2026-01-29 (S7).

**Methodology.** The method comes from "Measuring AI Ability to Complete Long Software Tasks",
first posted 2025-03-18 and last revised 2026-07-10 (S6). METR fits "a logistic curve to predict the probability it successfully completes
tasks as a function of human task duration" (S1). Each task gets "6 independent runs", and each
evaluation "typically takes at least 1-2 weeks of calendar time" (S1). The model is combined with
"an appropriate scaffold (ReAct, Triframe, Claude Code, Codex, etc.)" chosen per model (S1). Time
Horizon 1.1 (TH1.1) grew the suite "from 170 to 228 tasks" but "measured human baseline times for
only 5 of our 31 long (8h+) tasks" (S4).

**License and reuse.** Not established. The analysis repository's README says "See LICENSE file
for details" (S8). No `LICENSE` file is served at the repository root (S9, HTTP 404), and both
`github.com/METR/eval-analysis-public` and the GitHub license API returned **403** to
`fetch_source` (S10, S11), so the repository's license could not be read. The site footer reads
"© 2026 METR. All rights reserved." (S1). Epoch AI republishes the figures, and its data bundle says
"Epoch AI's data is free to use, distribute, and reproduce provided the source and authors are
credited under the Creative Commons Attribution license" (S12). The bundle does not say whether
that covers rows Epoch sourced from METR.

**Coverage on the map.** TH1.1's published results (S2) hold 26 models. Every one of them is closed:
GPT-2 through GPT-5.4, o1, o3, Claude 3 Opus through Claude Opus 4.6, Gemini 3 Pro and 3.1 Pro, and
"claude_mythos_preview_early". The open-weight models METR measured are all in TH1.0 (S3), the
superseded suite: DeepSeek-V3, V3-0324, R1 and R1-0528, Qwen2 72B, Qwen2.5 72B, Kimi K2 Thinking
and gpt-oss-120b. Against the map:

| Slug | Category | METR rows (suite) | Release the record reads | Same release? |
|---|---|---|---|---|
| `gpt-5` | `finetuned_chat` | GPT-5 203 min, GPT-5.2, GPT-5.4, 5.1-Codex-Max, 5.3-Codex (TH1.1) | GPT-5 at launch | Yes (GPT-5) |
| `o-series` | `finetuned_chat` | o1, o1-preview, o3 119.7 min (TH1.1); o4-mini (TH1.0) | o3 | Yes |
| `gemini-pro` | `finetuned_chat` | Gemini 3 Pro, Gemini 3.1 Pro 384.1 min (TH1.1) | Gemini 3.1 Pro Preview | Yes |
| `gpt-oss` | `finetuned_chat` | gpt-oss-120b 45.1 min (TH1.0 only) | gpt-oss-120b (high) | Yes, on the superseded suite |
| `claude-opus` | `finetuned_chat` | Opus 4, 4.1, 4.5, 4.6 (TH1.1) | Claude Opus 5.5 | No |
| `claude-sonnet` | `finetuned_chat` | 3.5, 3.7 (TH1.1); 4, 4.5 (TH1.0) | Sonnet 5.5 | No |
| `claude-fable` | `finetuned_chat` | Mythos Preview (early) (TH1.1) | Fable 5.1, a Mythos-class tier | No |
| `grok` | `finetuned_chat` | Grok 4 (TH1.0) | Grok 4.7 | No |
| `gpt-4o` | `base_pretrained` | GPT-4o, 2024-05-13 (TH1.1) | GPT-4o (Nov '24) | No (another snapshot) |
| `deepseek`, `deepseek-r1` | both | V3, V3-0324, R1, R1-0528 (TH1.0) | V4.1-Flash; R1 | `deepseek-r1` only, on the superseded suite |
| `qwen`, `qwen-instruct` | both | Qwen2 72B, Qwen2.5 72B (TH1.0) | Qwen3.8 | No |
| `kimi` | `base_pretrained` | Kimi K2 Thinking (TH1.0) | Kimi K3 | No |

So in `base_pretrained` the current suite holds no release that a record reads. In
`finetuned_chat` it holds three: `gpt-5`, `o-series` and `gemini-pro`. All three are closed, and
all three already carry a band.

**Fit with capability.md.** A time horizon is a `benchmark` value and could be cited in
`basis_detail`, but it fails three of the anchor tests. It cannot re-read the current frontier,
because the page is frozen. It cannot place open and closed models on one scale, because TH1.1
measures no open model. And it is not per product for the harnesses: the scaffold is METR's
choice, made per model, so a time horizon belongs to a model-plus-scaffold pairing that names no
product in `orchestration_agents`.

**Weaknesses.**
- *Saturation at the top.* "Measurements above 16 hrs are unreliable with our current task
  suite" (S1). The last model added is at 1,044.8 minutes, about 17.4 hours (S2), already past
  that ceiling. TH1.1 itself says "even our Time Horizon 1.1 suite has relatively few tasks that
  the latest generation of models cannot perform successfully" (S4).
- *Closed-model-only coverage* in the current suite (S2).
- *Suite sensitivity.* "The trend in time horizon is somewhat sensitive to task composition", and
  GPT-5's estimate rose 55% between suites (S4).
- *Cost.* About 1,000 runs per model and one to two weeks of calendar time (S1). The map cannot
  re-run it for a model METR skipped.
- *Contamination* is handled by private tasks. METR requires "zero data retention (required for
  our private tasks)" (S1), so the tasks cannot be inspected either.
- *Domain.* "Our task distribution is primarily composed of software engineering, machine
  learning, or cybersecurity tasks" (S1). It is closer to the coding and agentic suites the
  frontier open records already cite than to a general measure.

Mozilla's open-weight lag "≈4.4 months from measurement (Mozilla's computation on METR's raw
data)" (Mozilla comparison, section 4) can only rest on TH1.0's open-weight rows, since TH1.1 has
none. That is this brief's inference from S2 and S3, not a statement Mozilla makes.

**Recommendation: reject as an anchor in any category.** A curator may still quote a METR
horizon in a `value` or `note` as corroboration for an exact-release match, such as `o-series`,
`gemini-pro` or `gpt-5`. That uses a benchmark like any other and needs no ruling.

## Long-context retrieval benchmarks

### RULER

**What it measures, and how.** Synthetic tasks "with configurable sequence length and task
complexity", 13 tasks in 4 categories, reporting an "effective length" where a model stays above
"Llama-2-7b performance at 4K (85.6%)" (S13). Paper submitted 2024-04-09, last revised 2024-08-06
(S15).
**Maintainer.** NVIDIA. **License.** Apache License 2.0 (S14).
**Cadence.** The README table tops out at 128K. Its newest rows are Qwen3 and EXAONE 4.0, both
marked as "reported by authors" (S13). The README's own updates point to two pipeline branches,
not to new results (S13).
**Coverage on the map** (family match, not release match): `jamba-large`, which already cites
RULER, plus `llama`/`llama-instruct` (Llama 3.1), `qwen`/`qwen-instruct` (Qwen2 through Qwen3),
`mistral-large` (2407, 2411), `mistral-7b-instruct` (v0.2), `command-r`, `yi` (34B-200K), `phi`
(Phi-3), `glm` (GLM4 9B), `internlm` (InternLM2.5) and `gemini-pro` (Gemini 1.5 Pro). None is the
release the record reads, except `jamba-large`.
**Weaknesses.** Saturated at its own maximum length: several rows score 95 or more at 128K (S13).
Many rows are vendor-reported. It is a harness, so each lab runs it its own way.
**Recommendation: reject as an anchor.** It stays a legitimate per-product `benchmark` citation
where a card or paper reports it for the release the record reads, as `jamba-large` does today.

### NoLiMa

**What it measures.** A needle-in-a-haystack variant where "questions and needles have minimal
lexical overlap, requiring models to infer latent associations" (S16, S18). ICML 2025.
**Maintainer.** Adobe Research. **Cadence.** The last README update is "[2025-07-17]: Added
evaluation results on GPT-o3 and GPT-o4 Mini on NoLiMa-Hard" (S16).
**License.** The Adobe Research License grants use "for noncommercial research purposes only",
and "noncommercial research purposes include academic research and teaching only" (S17). That
governs the code and data. Whether quoting its published results on a public map is covered is a
question this brief does not answer.
**Coverage on the map:** `gpt-4o`, `gpt-4-1`, `llama`/`llama-instruct` (3.1, 3.3, 4), `gemini-pro`
and `gemini-flash` (1.5 through 2.5), `gemma` (Gemma 3), `mistral-large` (Large 2), `command-r`
(R+), `claude-sonnet` (3.5) and `o-series` (o1, o3, o3-mini, o4-mini on NoLiMa-Hard) (S16). Of
these, only `gpt-4-1` (GPT-4.1) and `o-series` (o3, on the Hard subset) match the release the
record reads.
**Recommendation: reject.** It is stale, its license restricts reuse, and it covers no current
frontier open family.

### LongBench v2

**What it measures.** "503 challenging multiple-choice questions, with contexts ranging from 8k to
2M words, across six major task categories". Human experts reach "53.7% accuracy under a 15-minute
time constraint" (S20).
**Maintainer.** The LongBench team. The repository license reads "Copyright (c) 2023 THU-KEG &
Zhipu AI" under the MIT License (S21), and the dataset card says "License: apache-2.0" (S23).
**Cadence.** The README says the leaderboard is "(updating)" (S20), but the newest rows on the
leaderboard page are GLM-4.5 and GLM-4.5-Air, dated 2025-07-28 (S19).
**Coverage on the map** (family match): `gemini-pro` and `gemini-flash` (2.0, 2.5),
`qwen`/`qwen-instruct` (Qwen2.5, Qwen3), `deepseek-r1` (R1, R1-0528), `minimax`
(MiniMax-Text-01), `o-series` (o1-preview, o1-mini), `gpt-4o`, `glm` (GLM-4-9B, 4-Plus, 4.5),
`kimi` (K2-Instruct), `claude-sonnet` (3.5), `mistral-large`, `llama`/`llama-instruct` (3.1, 3.3),
`nemotron` (Nemotron 70B) and `command-r` (R+) (S19). Two match the release their record reads:
`deepseek-r1` (R1) and `gpt-4o` (the 2024-11-20 snapshot).
**Weaknesses.** It is not saturated: the top row is 63.3 against the human 53.7 (S19). But the
questions are public, so contamination is possible. And one maintainer is Zhipu AI, whose GLM
models sit on the leaderboard and on the map as `glm`.
**Recommendation: reject as an anchor.** It has scored nothing since July 2025.

### Fiction.LiveBench

**What it measures.** Questions about stories on Fiction.live that need "a theory of mind for the
characters, an understanding of the chronology of events". The benchmark "consists of 36
questions about 30 stories", tested at a range of summary lengths (S24).
**Maintainer.** Fiction.live, a creative-writing platform. Epoch AI mirrors the leaderboard.
**Primary source not readable.** The Fiction.live leaderboard page returned HTTP 200, but its
7,685-byte body is a JavaScript application shell with no results in it (S25). The figures here
come from Epoch's mirror, which says "We source the data directly from the Fiction.liveBench
leaderboard" (S24).
**License.** Fiction.live's terms for the leaderboard were not established. Epoch states a CC-BY
license for its data (S12).
**Cadence.** Epoch's mirror holds 62 rows. The newest release date among them is 2026-01-27
(kimi-k2.5) (S12).
**Coverage on the map** (S12): `o-series` (o1, o3, o3-mini, o3-pro, o4-mini), `gpt-5`, `gpt-4-1`,
`gpt-oss`, `gemini-pro` and `gemini-flash` (2.0, 2.5), `claude-sonnet` and `claude-opus` (3.7,
Opus 4, Sonnet 4), `grok` (3, 4, 4 Fast), `deepseek` and `deepseek-r1` (V3-0324, V3.1, V3.2-Exp,
R1, R1-0528), `qwen` (Qwen3, Qwen3-Next, Qwen3-Max), `kimi` (K2, K2-0905, K2.5), `glm` (4.5),
`minimax` (M1), `llama` (3.3, 4), `gemma` (3) and `nemotron` (Nano 9B v2). Releases that match a
record: `o-series` (o3), `gpt-5`, `gpt-4-1`, `gpt-oss` and `deepseek-r1`.
**Weaknesses.** The set is tiny, and the stories are private, so it can't be checked. Open-weight
rows are run through third-party providers ("chutes/", "fireworks/", "deepinfra/"), and the same
model scores differently by provider: Qwen3-Next-80B-A3B-Instruct gets 0.625 at 120k tokens via
deepinfra and 0.469 via chutes (S12). That is a provider measurement, not a model one.
**Recommendation: reject as an anchor.** It can be quoted as corroboration through Epoch's
mirror.

### OpenAI-MRCR, and MRCR in general

**What it measures.** "A long context dataset for benchmarking an LLM's ability to distinguish
between multiple needles hidden in context". There are 2, 4 or 8 identical asks in a synthetic
conversation, and the model must return the i-th one. Contexts run to 1,048,576 tokens. It is
"inspired by the MRCR eval first introduced by Gemini" (S26), meaning Google DeepMind's
Michelangelo (S27).
**Maintainer and license.** OpenAI. The dataset card says "License: mit" (S26). Its `date_added`
column runs to 2025-12-04 (S26).
**No leaderboard.** The card says "See OpenAI's blog post ... for full results on this benchmark"
(S26), so OpenAI publishes the results for its own models. Context Arena, the third-party site
that runs MRCR across vendors, served a 2,308-byte JavaScript shell with no results in it (S28),
so it could not be read.
**Coverage on the map.** `deepseek-instruct` already cites "MRCR 1M 78.7" from its own card
(`sources/scores/deepseek-instruct.yaml`). That is vendor-reported.
**Weaknesses.** Each vendor reports it for itself, with different variants. HELM's long-context
team found that "the Gemini 2.0 benchmark results used an internal version of MRCR that was not
accessible to external researchers" and that "there are multiple versions of NIAH and MRCR, and
different versions were used on different models" (S29).
**Recommendation: reject as an anchor.** It is a dataset. Citing a vendor's MRCR figure per
product remains acceptable under the `basis_detail` rule.

### HELM Long Context

**What it measures.** Stanford CRFM's leaderboard over RULER SQuAD, RULER HotPotQA, ∞Bench En.MC,
∞Bench En.Sum and OpenAI-MRCR, capped at 128K tokens, with "100 instances from each task" (S29).
It is the one independent, reproducible runner of the candidates above.
**Cadence and coverage.** The launch post (2025-09-29) says "We evaluated 10 recent models from 5
organizations ... only the Meta Llama 4 models are open-weights". Those match `amazon-nova` (Nova
Premier, Pro, Lite), `gemini-flash` (2.0 Flash, Flash Lite), `llama` (Llama 4) and `gpt-4-1`
(S29). The leaderboard page served a 1,295-byte shell (S30), so whether models were added later
could not be checked.
**Recommendation: reject.** It is a one-time snapshot of ten models.

HELMET (Princeton NLP, MIT License) is the harness behind several of these. Its README carries
setup and evaluation sections, not a leaderboard (S31, S32), so it is not a candidate on its own.

### AA-LCR v1.1, the long-context eval already inside the anchor

**What it measures.** "Evaluate long context performance through testing reasoning capabilities
across multiple long documents (~100k tokens measured using cl100k_base tokenizer)". It has "100
hard text-based questions spanning 7 categories of documents (Company Reports, Industry Reports,
Government Consultations, Academia, Legal, Marketing Materials, and Survey Reports)". Version 1.1
"corrects 16 answer keys, and grades with GPT-5.6 Luna (medium). Scores are not directly
comparable with v1.0" (S33).
**Place in the anchor.** "Artificial Analysis Intelligence Index v4.3.2 incorporates 10
evaluations", AA-LCR v1.1 among them, and the weighting table gives AA-LCR v1.1 "5%" (S33). Every
band whose `basis_detail` reads "Artificial Analysis Intelligence Index" already includes it.
**Maintainer and cadence.** Artificial Analysis, the publisher behind the existing anchor. Its
page says "All evaluations are conducted independently by Artificial Analysis", and the chart
shows "31 of 570 models" (S35).
**License.** The question set is published under "License: apache-2.0" (S34).
**Coverage on the map, read on 2026-10-09.** "Kimi K3 (Max) scores the highest on AA-LCR v1.1
with a score of 88.7%, followed by Step 5 Preview with a score of 88.3% and MiMo-V2.6-Pro with a
score of 86.3%" (S35). Kimi K3 is the release `kimi` reads, and MiMo-V2.6-Pro is the release
`mimo-pro` reads. The map records both as `open_weights`. The rest of the 31 rows are drawn in a
chart that the static page does not carry as text, so this brief cannot list them.
**Fit.** It meets all four tests. It ranks models in the two model categories. It is a
`benchmark` number that can be re-read on a fetchable page. It scores the current releases, open
and closed, on one harness. And it comes from the same source as the existing primary, so it
raises no new bridge problem: the `artificialanalysis` route in `signal_routing.yaml` is the
same table.
**Weaknesses.** The question set is public, so it can be trained on. Artificial Analysis says
"We maintain internal copies of all evaluation datasets" (S33), which guards against a changed
copy but not against training on the published one. It is graded by an LLM judge
from one vendor. It has only 100 questions. And at 5% of the index, it barely moves the composite
on its own.

It also changes how Mozilla's long-context claim reads. Mozilla says "Closed still leads in
expert knowledge work, long context, and accountability" (Mozilla comparison, section 4). On
2026-10-09 the top of AA-LCR v1.1 was an open-weight model, with another open-weight model third
(S35). The two sources measure different things at different dates, so this is a reason to cite
the instrument, not a finding against Mozilla.

**Recommendation: tie-break inside the existing anchor** in `base_pretrained` and
`finetuned_chat`. Where two products sit at the same Artificial Analysis Intelligence Index band
and a note claims long-context strength, the AA-LCR v1.1 score is the named tie-break. Like any
other figure, it is quoted per product in `value`.

## If the tie-break is adopted

No `basis` value changes, because a tie-break inside the Artificial Analysis anchor is still
`basis: benchmark`. What would change is `basis_detail` and `value` on records that cite the
tie-break. On the figures read here, no score moves:

| Slug | Category | Score now | AA-LCR v1.1 | Expected direction |
|---|---|---|---|---|
| `kimi` | `base_pretrained` | 5 | 88.7%, first (S35) | None. Already at the top band. `basis_detail` would gain AA-LCR next to Terminal-Bench 2.1/DeepSWE |
| `mimo-pro` | `base_pretrained` | 5 | 86.3%, third (S35) | None. Already at the top band |
| Other records the 31 rows cover | both | | Not readable from the static page | Unknown. A refresh pass would read the chart through the Artificial Analysis bridge or by hand |

Records like `jamba-large`, `seed-oss`, `minicpm`, `lucie-7b` and `deepseek-instruct` already
cite RULER, MRCR, needle plots or "long-context suites" from their own cards. They keep those
citations. The tie-break does not replace a per-product citation.

## Follow-ups for a maintainer to rule on

1. **Adopt AA-LCR v1.1 as the named long-context tie-break in the capability anchor (edit-category).**
   Exactly: in `sources/categories/base_pretrained.yaml`, add under
   `scoring_recipe.capability.anchor` a line naming "AA-LCR v1.1, the long-context component of
   the same index, as the tie-break where two products share a band and a note claims long-context
   strength". The recipe is a bare object that no gate reads, so this needs no schema change.
   Decide also whether `finetuned_chat` gets the same `capability` block. Today it has none, and
   its anchor lives only in `signal_routing.yaml`. If ruled yes, that edit is the normative home,
   and R-2026-10-08-n's `lands_in` names the category file or files.
2. **Reject METR time horizons as an anchor in every category.** Record it so the question is
   not asked again while the page is frozen. Revisit only if METR publishes a successor suite
   that measures open-weight models.
3. **Reject RULER, NoLiMa, LongBench v2, Fiction.LiveBench, OpenAI-MRCR and HELM Long Context as
   anchors**, while keeping per-product citations of a vendor- or harness-reported figure for the
   exact release, which `basis_detail` already allows.
4. **Optional, signal_routing.** If item 1 is adopted, decide whether the `artificialanalysis`
   capability route in `sources/signal_routing.yaml` should name an AA-LCR column next to
   `artificial_analysis_intelligence_index` once the bridge lands. The route is
   `blocked_by: bridge` today, so this changes nothing until then.

## Method and limits

- Every outside page was fetched with `build.fetch_source` on 2026-10-09. A body was quoted only
  where the page served it as text.
- **Not readable:** `github.com/METR/eval-analysis-public` and its license API (403). The
  repository's root `LICENSE` (404). The Fiction.live leaderboard, Context Arena and the HELM Long
  Context leaderboard (200, but JavaScript shells with no results).
- Coverage is matched by family name against `sources/products/` and the release named in each
  record's capability `value` or `note`. A family match is not a release match, and the tables
  keep the two apart.
- The Artificial Analysis rows beyond the top three were not read, so the "if adopted" table is
  incomplete by design.

## Sources

All fetched 2026-10-09 with `uv run python -m build.fetch_source`.

| # | URL | Status | content_sha256 | Quote |
|---|---|---|---|---|
| S1 | https://metr.org/time-horizons/ | 200 | `f9d12ea0f66e8d5ca1fc68f345503db3912acedb5240a7a66962786866dd759f` | "This page is no longer actively updated. LAST UPDATED September 8, 2026"; "Measurements above 16 hrs are unreliable with our current task suite" |
| S2 | https://metr.org/assets/benchmark_results_1_1.yaml | 200 | `aae31902b0519a4da73e16643915e5e8aca13cd3315c3aac893ce3d6dfe92ad9` | `benchmark_name: METR-Horizon-v1.1`; 26 entries under `results`, last `claude_mythos_preview_early_inspect` p50 estimate 1044.780145 |
| S3 | https://metr.org/assets/benchmark_results_1_0.yaml | 200 | `f15fd2f13cd8d28f06f5430fabf21dcd1284193ec152bdedc34e11dcc525df66` | 33 entries, including `gpt-oss-120b` p50 45.1, `kimi_k2_thinking`, `deepseek_r1_0528`, `qwen_2_5_72b` |
| S4 | https://metr.org/blog/2026-1-29-time-horizon-1-1/ | 200 | `c042ba971248c3d800c73cd512671e6e23f60f2f374fe5c91b06736cf39a13e8` | "We increased our suite from 170 to 228 tasks"; "we measured human baseline times for only 5 of our 31 long (8h+) tasks" |
| S5 | https://metr.org/about | 200 | `e56ed14062e49911f3b53e01dc36244e5d23e9c27595e96e05fe98fae16d6e06` | "METR has not accepted funding from AI companies, though we make use of significant free tokens" |
| S6 | https://arxiv.org/abs/2503.14499 | 200 | `b14265aef51cf19ab20e9d300e4ac95cddf0fe3b3558e83b5dd360ae8ee80965` | "Measuring AI Ability to Complete Long Software Tasks" [Submitted on 18 Mar 2025 (v1), last revised 10 Jul 2026 (this version, v4)] |
| S7 | https://metr.org/research/ | 200 | `ccd176f9396e4da0c126967f91b46129c7dd2e57ac3a44e81287f0831feff0d6` | "Expenditure Horizon: Measuring Optimization Ability ... July 21, 2026"; "Time Horizon 1.1 January 29, 2026" |
| S8 | https://raw.githubusercontent.com/METR/eval-analysis-public/main/README.md | 200 | `4f5d2eb62e339e2804448364c8ef2364f8e5fc229aa78c073a36e0d572621a99` | "See LICENSE file for details." |
| S9 | https://raw.githubusercontent.com/METR/eval-analysis-public/main/LICENSE | 404 | | no file at this path |
| S10 | https://github.com/METR/eval-analysis-public | 403 | | the host declined, so this is not evidence of anything |
| S11 | https://api.github.com/repos/METR/eval-analysis-public/license | 403 | | the host declined |
| S12 | https://epoch.ai/data/benchmark_data.zip | 200 | `3a6555c8416de2152f0486383873b0bdb8242d5840dcd50be59d370babdf0996` | README.md: "Epoch AI's data is free to use, distribute, and reproduce provided the source and authors are credited under the Creative Commons Attribution license"; `fictionlivebench_external.csv` (62 rows, latest release 2026-01-27); `metr_time_horizons_external.csv` (latest 2026-04-07, claude-mythos-preview-early) |
| S13 | https://raw.githubusercontent.com/NVIDIA/RULER/main/README.md | 200 | `f3aae5bbd58fcd7de32aab099c455dd2bbc1da23a2efee9db3071eb9fbf894a3` | "We benchmark 17 open-source models across 4 task categories (in total 13 tasks)"; "Qwen3 results are reported by authors" |
| S14 | https://raw.githubusercontent.com/NVIDIA/RULER/main/LICENSE | 200 | `43070e2d4e532684de521b885f385d0841030efa2b1a20bafb76133a5e1379c1` | "Apache License Version 2.0, January 2004" |
| S15 | https://arxiv.org/abs/2404.06654 | 200 | `fc4d644f649918595252e8e4150770521ea8b6e63b77b9516abf5f9f4afc6622` | [Submitted on 9 Apr 2024 (v1), last revised 6 Aug 2024 (this version, v3)] |
| S16 | https://raw.githubusercontent.com/adobe-research/NoLiMa/main/README.md | 200 | `d64d2af4cbba0cb0e2faa46e33a83fcba82221e99a7f5c12bfda04be2c7d81f1` | "[2025-07-17]: Added evaluation results on GPT-o3 and GPT-o4 Mini on NoLiMa-Hard" |
| S17 | https://raw.githubusercontent.com/adobe-research/NoLiMa/main/LICENSE | 200 | `8638b5a5beb5e1cdf06a09512d23268358b64f646775581d8276e47329e0aa06` | "for noncommercial research purposes only"; "noncommercial research purposes include academic research and teaching only" |
| S18 | https://arxiv.org/abs/2502.05167 | 200 | `a01bf52dae11d8f9946194d6ecb977fd1aed9ed83f14ad6352bac548681e9e74` | [Submitted on 7 Feb 2025 (v1), last revised 9 Jul 2025 (this version, v3)] |
| S19 | https://longbench2.github.io/ | 200 | `b16f4683a0970694a1aa4fc74155bc61024fa57f98f257b90cc67d54d48d2d35` | "Gemini-2.5-Pro 🧠 Google - 1M 2025-03-25 - 63.3"; "GLM-4.5 🧠 Z.ai & Tsinghua 355B 128k 2025-07-28"; "Human N/A N/A N/A 53.7" |
| S20 | https://raw.githubusercontent.com/THUDM/LongBench/main/README.md | 200 | `7de8f5cec86e49b9a0f3f90bf112e797903bcf93bd458d78c854fec532b08ef1` | "LongBench v2 consists of 503 challenging multiple-choice questions"; "leaderboard here (updating)" |
| S21 | https://raw.githubusercontent.com/THUDM/LongBench/main/LICENSE | 200 | `bf7f05f274d65931bdf14f060b6855f1c359b8424eb74fd3091d25de89d700c3` | "MIT License Copyright (c) 2023 THU-KEG & Zhipu AI" |
| S22 | https://arxiv.org/abs/2412.15204 | 200 | `55a37ca82f9cdc313322cdc8c24b4694a8a2f898da1b05463f39c7215e2e77aa` | [Submitted on 19 Dec 2024 (v1), last revised 3 Jan 2025 (this version, v2)] |
| S23 | https://huggingface.co/datasets/THUDM/LongBench-v2 | 200 | `f7043986bd90ad7dfeda8e60ef2b0bfe1b216fccf64f87131f0a4aae52fe6f12` | "License: apache-2.0" |
| S24 | https://epoch.ai/benchmarks/fictionlivebench | 200 | `8d445518eb6da57cf6ce5c845ec14f83d9dafa99114d70911e2b45f1696beb84` | "We source the data directly from the Fiction.liveBench leaderboard. The benchmark consists of 36 questions about 30 stories." |
| S25 | https://fiction.live/stories/Fiction-liveBench-Feb-21-2025/oQdzQvKHw8JyXbN87 | 200 | `b47f12ad82dc90ea3edfb3dc881cf8042559b8e28024bbc250c868599dce84c1` | 7,685-byte JavaScript shell; no results in the served body |
| S26 | https://huggingface.co/datasets/openai/mrcr | 200 | `0759b20f2b9b35e7c316e5eda29bb858dff81084f2e7a136c3e10b8ce35a565d` | "License: mit"; "This eval is inspired by the MRCR eval first introduced by Gemini"; "See OpenAI's blog post ... for full results on this benchmark" |
| S27 | https://arxiv.org/abs/2409.12640 | 200 | `8de7b3ebc84702ee86feafa162395e96045da00269c6f179b2679f51f2797305` | "Michelangelo: Long Context Evaluations Beyond Haystacks via Latent Structure Queries" [Submitted on 19 Sep 2024] |
| S28 | https://contextarena.ai/ | 200 | `1406884a9e8776d6337e112a5110136fa57df9f96d89849960cf934e496c96bc` | 2,308-byte JavaScript shell; no results in the served body |
| S29 | https://crfm.stanford.edu/2025/09/29/helm-long-context.html | 200 | `7003f62d92b1cfb240475c1188b8e6b091bb4df13ff20682b3a8f69b092c278e` | "We evaluated 10 recent models from 5 organizations ... only the Meta Llama 4 models are open-weights"; "the Gemini 2.0 benchmark results used an internal version of MRCR that was not accessible to external researchers" |
| S30 | https://crfm.stanford.edu/helm/long-context/latest/ | 200 | `7b5ae08a8aad37b4ba0fe04ccb68d68a62d23695ec874aff3e81833acca8cca0` | 1,295-byte JavaScript shell; no results in the served body |
| S31 | https://raw.githubusercontent.com/princeton-nlp/HELMET/main/README.md | 200 | `7f65d7f593f1cce2a24fb394298705c94ee5c2392bcbcd09a3a109ffd36bed1b` | sections "Setup", "Data", "Running evaluation", "Adding new models"; no leaderboard section |
| S32 | https://raw.githubusercontent.com/princeton-nlp/HELMET/main/LICENSE | 200 | `f460854d0318a2e3bdaece7970c6417e2a84e3b2e7c653f0046128af01315f77` | "MIT License Copyright (c) 2024 Princeton Natural Language Processing" |
| S33 | https://artificialanalysis.ai/methodology/intelligence-benchmarking | 200 | `1b74678ab0d511786971f4d0a187b9349d56f8a2f7bcafec7fb3e233d15a9451` | "Artificial Analysis Intelligence Index v4.3.2 incorporates 10 evaluations"; "AA-LCR v1.1 100 3 Open Answer Equality Checker LLM, pass@1 5%"; "corrects 16 answer keys, and grades with GPT-5.6 Luna (medium)"; "We maintain internal copies of all evaluation datasets" |
| S34 | https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR | 200 | `fcfef88080946e616f4989efe7929fb86cc22bae71ee19428ae028721785b3b8` | "License: apache-2.0"; "test · 100 rows" |
| S35 | https://artificialanalysis.ai/evaluations/artificial-analysis-long-context-reasoning | 200 | `f162295e2dca967969bd8e7979101757f97b176d8d3ac3de3a35d43b5e2dfe48` | "Kimi K3 (Max) scores the highest on AA-LCR v1.1 with a score of 88.7%, followed by Step 5 Preview with a score of 88.3% and MiMo-V2.6-Pro with a score of 86.3%"; "31 of 570 models"; "All evaluations are conducted independently by Artificial Analysis" |
