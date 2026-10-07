# Mozilla's State of Open Source AI v1.1 against the map: 2026-10-07

This record compares Mozilla's *The State of Open Source AI*, Volume 1.1, with the map as it stood on
`main` on 2026-10-07. It answers the read-and-compare half of issue #723 and checks the survey
figures issue #724 rests on. It changes no scores, products or categories. Every claim taken from
the report carries a page number. Every map-side claim cites a file in `sources/` or the generated
payload `build/notebook_data.json` (generated 2026-10-07). Like the other records in this directory,
it describes what its sources said on its date.

## The source

| | |
|---|---|
| Title | *The State of Open Source AI*, "A recurring Mozilla assessment", Open Source AI 2026, Volume 1.1, September 2026 (cover, p. 1) |
| Landing page | <https://stateofopensource.ai/> |
| PDF read | <https://stateofopensource.ai/state-of-open-source-ai-v1-1.pdf>, 91 pages, 8,299,888 bytes, sha256 `6f5e3d3ce6f0c2ca51eafdee9b8d98a446c083f3b7a08fb6cef093a2f03d4ae5`, fetched 2026-10-07 |
| PDF metadata | Title "State of Open Source AI 2026", Author "Mozilla", created 2026-09-14 21:05 UTC |
| Date | The landing page footer reads "v1.1 · September 2026 · Data current to 1 September 2026 · Last updated September 14, 2026". The changelog feed dates v1.1 to Mon, 14 Sep 2026. Issue #723 gives 2026-09-15. |
| Changelog | <https://stateofopensource.ai/changelog.html> (sha256 `ad0543e05c8c128e205575e2f8597bdffd66a2a9162955d0d3570b1dab7a2e6c`), entry "v1.1 — The September edition" |

**How the version was confirmed.** Four things agree. The cover reads "Volume 1.1, September 2026"
(p. 1). The appendix states "This is Volume 1.1, published September 2026, and it supersedes Volume 1
(July 2026) and V.01 (August 2026)" (p. 91). The landing page links the PDF as
`state-of-open-source-ai-v1-1.pdf`, beside the label "v1.1 · Recurring · September 2026". The
changelog's v1.1 entry lists the slides this comparison relies on as added or changed in v1.1, for
example the front-matter openness table and the rebuilt survey bars.

**How the site was confirmed as Mozilla's.** Mozilla's own blog post announcing Volume 1
(<https://blog.mozilla.org/en/mozilla/mozilla-state-of-open-source-ai-report/>, modified 2026-07-13)
links to `https://stateofopensource.ai/`. The PDF's author field is Mozilla, the foreword is signed
by Mozilla's CTO (p. 2), and the contact address is `opensource@mozilla.org`.

**Caveats the report states about itself.** All of these are on p. 91 unless noted.

- "Open" means downloadable weights unless a slide says otherwise (p. 4 and p. 91).
- Mozilla calls itself an interested party: Mozilla.ai builds open source AI tooling, and Mozilla
  Ventures holds financial interests in companies named in the report. It is also a listed ROOST
  partner (p. 25).
- The stack heat map (p. 23) is "an original Mozilla assessment", graded with AI assistance across 44
  subcomponents and 1,361 projects. It "is as of July 2026 and was not re-scored for this edition",
  and its scores "are ordinal and directional, and should not be read as measurements".
- The developer survey was "commissioned and paid for by Mozilla and fielded by SlashData, which
  controlled sampling, weighting and the authoritative export. Mozilla wrote the questions."
- The p. 23 footer says "Full 44-row subcomponent table in the appendix", and the changelog lists
  "survey instrument cuts" in the appendix. The published PDF's appendix is one page (p. 91) and has
  neither. Page 91 also refers to "the survey methodology page", but the PDF gives no address for it,
  and none was found on `stateofopensource.ai`.

## 1. Openness: the sixteen releases

The front matter scores sixteen "notable open releases" on weights, base, data, code, report and
inference, and finds "0 of 16 notable open releases ship the data recipe the OSI definition asks for".
It adds: "No row ships a full corpus: three gate partial data, thirteen publish none" (p. 4). The
three with partial data are the NVIDIA rows. The column values below were read from the rendered
page, because the colored cells carry no text.

| Mozilla row (p. 4) | Mozilla license / restrictions | Mozilla DATA | Map row | Map `data` | Map license | Reading |
|---|---|---|---|---|---|---|
| Kimi K3 · Moonshot | Custom Kimi K3 / MaaS, UI attribution | No | `kimi` (`base_pretrained`) | closed | Modified-MIT | Data agrees. **License disagrees**, see below |
| GLM-5.2 · Zhipu | MIT / none | No | `glm` | closed | MIT | Agree |
| DeepSeek V4 Flash 0731 | MIT / none | No | `deepseek` | closed | MIT | Agree |
| DeepSeek V4 Pro 0813 | MIT / none | No | `deepseek` (governing `deepseek-v4-pro`) | closed | MIT | Agree |
| Qwen3.8-2.4T-A95B | Custom Qwen3.8-Max / attribution + MaaS | No | `qwen` | closed | Qwen3.8-Max-License, Qwen-Community-License-1.0, Apache-2.0 | Agree. The map has no attribution term, see below |
| MiniMax-M3 | MiniMax Community / commercial terms | No | `minimax` | closed | minimax-community | Agree |
| MiMo-V2.5-Pro · Xiaomi | MIT / none | No | `mimo-pro` (governing `mimo-v2-6-pro`) | closed | MIT | Agree. The map's governing release is newer |
| Inkling · Thinking Machines | Apache 2.0 / separate AUP | No | `inkling` | closed | Apache-2.0 | Data agrees. The map does not record the AUP |
| Nemotron 3 Ultra · NVIDIA | OpenMDW 1.1 / dataset gating | Partial / gated | `nemotron` (`finetuned_chat`) | **open** | NVIDIA-Nemotron-Open-Model-License | **Readings differ**, see below |
| Muse Glimmer · Meta | Apache 2.0 / none | No | none | | | Not on the map |
| Mistral Medium 3.5 | Modified MIT / revenue carve-out | No | none | | | Not on the map |
| Gemma 4 31B · Google | Apache 2.0 / none | No | `gemma` | closed | Apache-2.0 | Agree |
| Nemotron 3 Super · NVIDIA | Nemotron Open Model / custom, gating | Partial / gated | `nemotron` | **open** | as above | **Readings differ** |
| gpt-oss-120b · OpenAI | Apache 2.0 / none | No | `gpt-oss` | closed | Apache-2.0 | Agree |
| Nemotron 3.5 Lightning | OpenMDW 1.1 / dataset gating | Partial / gated | `nemotron` | **open** | as above | **Readings differ** |
| Command A+ · Cohere | Apache 2.0 / none | No | `command-r` (governing `command-a-plus-05-2026`) | closed | Apache-2.0 | Agree |

Map values are from `sources/scores/<slug>.yaml` (`openness.components`). Category membership is from
`sources/categories/base_pretrained.yaml` and `sources/categories/finetuned_chat.yaml`.

**Result.** Fourteen of the sixteen releases fall under eleven map rows, and two are not on the map.
On the ten rows that are not `nemotron`, the map's `data` value is `closed`, which matches Mozilla's
"No". None of the sixteen carries `components-listed` on the map. The single difference is
`nemotron`:

- **`nemotron`: the two readings ask different questions.** The map records `data: open` with the
  detail "~40M post-training/SFT+RL samples released as Nemotron-SFT-Data/Nemotron-RL-Data; pretraining
  sets only partly released". `nemotron` sits in `finetuned_chat`, and the ladder there,
  `sources/rubrics/model.yaml`, asks whether the post-training data is released. Mozilla's column is
  about the corpus ("No row ships a full corpus") and notes that "NVIDIA ungates a sample set; the
  remaining code, math and multilingual data needs gating and approval under its Data Access
  Agreement for Model Training" (p. 4). The map's own note concedes the same gating ("Ultra's code,
  math and multilingual data require gated approval"). This is not an error on either side. The
  record says `open` on a question Mozilla does not ask, and the published note covers what Mozilla
  found.
- **`kimi`: the license reading disagrees, and the live license sides with Mozilla.** The map names
  the license `Modified-MIT`, and its note says the license "excludes commercial use above 100 million
  monthly active users or $20 million in monthly revenue". Mozilla calls it "Kimi K3 License (custom):
  MaaS above $20M/yr needs a separate agreement; above 100M MAU or $20M/mo must display 'Kimi K3' in
  the UI. K2 was modified-MIT; that did not settle K3" (p. 81). The LICENSE file at
  `huggingface.co/moonshotai/Kimi-K3/raw/main/LICENSE`, fetched 2026-10-07 (sha256
  `20c797ce19af0c17de52c6afb144644768a591c521655f5ebf5712c9850f2887`), is titled "Kimi K3 License". It
  requires a separate agreement before commercial use by a Model-as-a-Service business above $20M of
  revenue over 12 months (section 2), and requires prominent "Kimi K3" display above the 100M MAU /
  $20M monthly thresholds (section 3). Its digest differs from the one the map cites for the same
  file (`038709cf…`, accessed 2026-08-14). Either the file changed after the map read it, or the map
  read it wrong. Neither the map nor this record can tell which.
- **`inkling`: the AUP.** Mozilla lists "Separate AUP" against Inkling, and in its "Nuance" box says
  that "Inkling-Small pairs Apache 2.0 weights with a separate, changeable Acceptable Use Policy"
  (p. 4). The map's license detail is "OSI for weights only" and does not mention an AUP.
  `docs/reference/openness.md` ("Two places the map deliberately departs from MOF") ranks
  attribution-or-conduct terms separately from OSI terms, so the AUP belongs in the record. Data is
  `closed`, so the openness score is unlikely to move.
- **`qwen`: the attribution threshold.** Mozilla: "Qwen3.8 adds attribution above 100M MAU or $20M
  monthly revenue and a paid MaaS licence above $50M TTM" (p. 4). The map records the MaaS term
  ("the separate license required only above USD 50M annual revenue") but not the attribution term.
- **`glm`: an internal inconsistency the comparison exposed.** Mozilla marks GLM-5.2 CODE "No" and
  inference "Partial" (p. 4). The map records `code: open` with the detail "inference", while
  `sources/rubrics/pretrained.yaml` defines `open` as a full pretraining pipeline and `partial` as
  "inference or fine-tuning code only". The map's own note says "no training pipeline is published".
  The value should be `partial` whatever Mozilla says.
- **CODE elsewhere.** Mozilla marks DeepSeek V4 Pro 0813 CODE "Yes" and V4 Flash 0731 "No" (p. 4).
  The map has one `deepseek` row with `code: partial` ("inference/serving; no training pipeline or
  data"). The PDF does not define its CODE column, so this is noted but not treated as a disagreement.

Two releases are missing from the map:

- **Muse Glimmer (Meta).** "29.78B dense, Apache 2.0, runs on a 24 GB consumer GPU", shipped Aug 10
  (p. 35). Meta's verified Hugging Face org "carries four repos, all Muse Glimmer" (p. 35).
  `sources/categories/multimodal_models.yaml` says Muse Glimmer "stays in its family row in
  base_pretrained or finetuned_chat", but no product or score file mentions it. The only Meta Muse
  row, `muse-spark` (`finetuned_chat`), is scored closed (openness 1).
- **Mistral Medium 3.5.** It is listed as an open release under a modified MIT license with a revenue
  carve-out (p. 4). The map mentions it only inside a `devstral` source (`sources/scores/devstral.yaml`).
  The Mistral rows are `mistral-large` (governing `mistral-large-3`), `mistral-7b-instruct`,
  `devstral` and `codestral`.

## 2. Maturity: Mozilla's nine layers against the map's stages and gaps

Mozilla scores nine stack layers on nine criteria, from 1 to 5, and calls standardization (criterion
average 2.83) and enterprise readiness (2.79) "the operational gap" (p. 23). The crosswalk below is
this record's own judgment. Mozilla publishes only layer rows: its subcomponent table is not in the
PDF, so it cannot say which layer a subcomponent such as "ML frameworks 4.3" belongs to. Stages and
gaps are from `build/notebook_data.json`.

| Mozilla layer (p. 23) | Layer avg | Weakest criteria | Map categories (arc / group) | Map stage and gaps |
|---|---|---|---|---|
| Model code | 3.96 | Enterprise 3.3 | Pipeline code: `inference_code`, `finetuning_code`, `evaluation_code`, `federated_learning` | 5 none; 3 adoption; 4 resiliency; 3 adoption |
| Model weights | 3.67 | Enterprise 2.8, Docs 3.2 | Models: `base_pretrained`, `finetuned_chat`, plus the modality model categories | 3 adoption+openness; 3 adoption+openness |
| Infrastructure | 3.48 | Ease 3.3, Enterprise 3.3 | Infrastructure arc: `ml_frameworks`, `compilers`, `ml_orchestration`, `deployment`, `storage`, `model_hubs`, `edge_hardware` | 5 none; 3 adoption; 4 resiliency; 4 resiliency; 3 capability; 3 adoption+openness; 3 capability+openness |
| Product / UX | 3.41 | Standardization 2.8, Enterprise 3.0 | Interfaces: `ui_api` | 4 resiliency |
| Datasets | 3.33 | Sustainability, Standardization, Enterprise 2.8 | Data group: `training_synthetic_datasets`, `benchmark_eval_data`, `dataset_processing_tools`, `document_conversion`, `language_specific_datasets` | 4 resiliency+disclosure; 4 resiliency; 2 adoption; 4 resiliency; 4 resiliency |
| Documentation | 3.22 | Enterprise 2.3, Perf-vs-closed 2.8 | No category. The map reads documentation inside openness components and the `disclosure` gap | n/a |
| Licensing | 3.11 | Standardization 2.5 | No category. License is an openness component (`sources/rubrics/`) | n/a |
| Agent layer | 3.04 | Interop 2.0, Standardization 2.2, Enterprise 2.3 | `orchestration_agents`, `agent_protocols`, `agent_tools_connectors`, `search_retrieval` | **5 none; 5 none**; 3 capability; 3 capability+adoption+openness |
| Safeguards | 2.64 | Standardization 1.6, Enterprise 2.2 | Observability: `safeguards`, `assurance_evidence`, `telemetry_observability` | 3 adoption; 3 adoption; 4 resiliency |

**Where the two agree.** The ordering at both ends is similar. Mozilla's strongest layer, model code
(3.96), contains the map's Stage 5 `inference_code`. Its strongest subcomponent, "ML frameworks 4.3"
(p. 23), matches `ml_frameworks` at Stage 5. Its weakest layer is safeguards (2.64). Of the three map
categories that layer covers, two (`safeguards`, `assurance_evidence`) sit at Stage 3 with an adoption
gap. Mozilla's datasets layer is weakest on
sustainability (2.8), and the map gives four of the five data categories a resiliency gap.

**Where they disagree.** The agent layer is the clear disagreement. Mozilla puts it second from the
bottom (3.04), with the lowest interop score of any layer (2.0). The map puts `orchestration_agents`
and `agent_protocols` at Stage 5 with no gaps. Two things explain most of this:

- **The constructs differ.** The map's stage comes from openness, adoption and capability per
  product. It has no instrument for standardization, enterprise readiness or ease of adoption, which
  is the point #723 raises. Mozilla's "Perf-vs-closed" criterion is the closest thing it has to the
  map's capability axis, and "Community" and "Ease" are nearest to adoption. Openness has no
  criterion and appears only as the Licensing layer. On those three criteria the agent layer scores
  3.5, 4.2 and 3.3.
- **The heat map dates from July.** It "was not re-scored for this edition" (p. 91). The same report's
  harness section says "interop runs on open standards" (p. 54) and reports MCP at "110M+" monthly
  SDK downloads (p. 61). That sits awkwardly beside an agent-layer interop score of 2.0. Without the
  44-row table, this record cannot tell which subcomponents pull the score down.

For `inference_code` and `ml_frameworks`, which #723 also lists, there is little disagreement to
explain. Mozilla scores model code highest of the nine layers. Infrastructure, at 3.48, is the
third-highest layer, and its standardization score rose "3.1 → 3.4 after Moonshot upstreamed KDA
caching to vLLM" (p. 23).

## 3. Survey figures behind #724

#724 states: "79% of professional developers use open models against 71% for closed, yet open models
reach production 12 points less often." #723 adds the blocker shares. This is what the report
supports.

| Figure as the issues state it | What the report says | Page | Sample stated | Supported? |
|---|---|---|---|---|
| 79% use open models | "79% use open models", and in the funnel "Developers using open models 79%" | p. 22; p. 21 | p. 21 footer: "Mozilla/SlashData 2026 survey, n=1,494 (79/51/63)". p. 22 gives no n | **The figure is supported. "Professional" is not**: pp. 21–22 say "developers" |
| 71% use closed models | "71% use closed models" | p. 22 | none on the page | Supported, with the same qualifier |
| Open reaches production 12 points less often | "Open models reach production 12 points less often than closed ones": "Open models reaching production 51%", "Closed models reaching production 63%" | p. 21 | n=1,494 | **The figures are supported. The denominator is not stated**, see below |
| Blockers: compute 27, security/privacy/compliance 26, maintenance 24, deployment/hosting/scaling 23, specialized support 22, model performance 17 | Identical to the "All" column of the regional table, "Share of developers naming each challenge" | p. 27 | "WEIGHTED SAMPLE … 1,411", "(MZCS1), n=1,411" | **Supported** for all developers. Current open-model users on p. 26 give 27/26/23/22/22, with performance at 15 |

What the report does not settle:

- **Question wording.** The PDF prints no survey question. The appendix it refers to for "survey
  instrument cuts" (changelog) and "the survey methodology page" (p. 91) are not in the PDF, and the
  page was not found on the site.
- **The production denominator.** Page 21 does not say whether 51% and 63% are shares of each
  model's adopters or of all respondents. Page 24 does say so for its cut: "Share of adopters reaching
  production, by organization size", professional developers n=954 (closed/open: small 54/53, mid-size
  66/55, enterprise 73/57). The two pages cannot share both a base and a denominator. The overall
  open figure on p. 21 (51%) is below the open figure in every size band on p. 24 (53–57%), so p. 21
  uses either other respondents or another denominator. The "12 points" therefore belongs to the
  n=1,494 base, and "professional developers" belongs to the size cut.
- **The use base.** On p. 22, 29% "Open only", 50% "Both" and 21% "Closed only" add to 100, and they
  reproduce 79% (29+50) and 71% (21+50). The base for those percentages therefore appears to be
  developers who use at least one model, open or closed, not all developers. The report does not say
  so.
- **The sample size varies by slide.** It is given as n=1,410 (p. 3, and p. 26 "current or churned
  open-model developers"), n=1,411 weighted (p. 27), n=1,494 (p. 21) and n=954 professional developers
  (p. 24). Mozilla's July blog post for Volume 1 described "a global survey of 950+ developers".
- **"The reasons given are operational".** This is #723's wording, and it goes slightly beyond the
  report. Page 27 counts challenges developers name. It does not count reasons a deployment failed to
  reach production. The link to the production gap is Mozilla's interpretation: "The gap comes from
  operational tooling and trust; capability already clears the bar" (p. 21). Page 26 also cuts the
  other way: among developers who churned from open models, "Model performance is not good enough"
  rises to 27% (+12 pp, the largest delta).
- **The 89% figure on the same funnel is a different instrument.** "Firms using open components 89%"
  comes from a Linux Foundation study "commissioned by Meta" (p. 21; p. 91), not from the
  Mozilla/SlashData survey.

**Production-side signals in the report that #724 could use.** OpenRouter token volume ranks eight
open-weight models in the August top ten (p. 14). Page 61 reports that 28% of the Fortune 500 were
"running MCP in production by March 2026", citing a third party (Synvestable). Page 62 reports that
"150+ organizations run A2A in production". The first is the API-channel signal `docs/reference/adoption.md`
calls "the only true API-channel signal". The other two are vendor or third-party claims of the kind
#724 says can only enter as `reported_traction`.

The sharpest example for #724 is `mimo-pro`. The map has it at adoption 2 (`10K-100K`, Hugging Face
downloads of MiMo-V2.5-Pro, `sources/scores/mimo-pro.yaml`). On OpenRouter, Mozilla ranks MiMo-V2.5
third by August token volume at 29.4T (p. 14), and the changelog's v1.0.1 entry (27 July 2026) has
it first in the July leaderboard at 31.2T.
`nemotron`'s adoption note already calls its download count "a floor rather than a ceiling" because
OpenRouter traffic is not counted.

## 4. Capability: the closed edge

Mozilla puts the open-weight lag at "≈4.4 months measured open–closed lag (Mozilla fit on METR
data); Epoch: 4 months" (p. 10). It places the closed edge in "Professional knowledge work",
"long-context fidelity" and "conversational polish" (p. 11). It repeats this as "Closed still leads in
expert knowledge work, long context, and accountability" (p. 28), with closed models handling
"8-to-12-hour tasks" first (p. 10). A keyword search of the `capability` blocks in
`sources/scores/` for the products in the two model categories finds:

- GDPval: no `base_pretrained` row; two `finetuned_chat` rows (`claude-opus`, `gemini-flash`).
- Long-context retrieval (MRCR, needle, RULER, LongBench, "long context"): three `base_pretrained`
  rows (`lucie-7b`, `minicpm`, `seed-oss`) and two `finetuned_chat` rows (`deepseek-instruct`,
  `jamba-large`). None is a frontier open family.
- METR time horizon: no row in either category.

So the map's capability evidence for the frontier open families rests on coding and agentic-terminal
benchmarks (Terminal-Bench, SWE-bench, DeepSWE). Mozilla classes those as parity or contested
(p. 11), not as the closed edge. A keyword search undercounts, so treat these numbers as a lower
bound.

## 5. Coverage: what the report names that the map does not have

Mozilla's harness map says "Every harness sub-layer has products except permission" (p. 54). It
names "Permission & identity · the unsolved gap" and argues for "portable permission" ("OAuth 2.1
handles who the agent is. Nothing yet handles what it may write", p. 86). It does not name five
authorization products. The governance row lists "meta-harness · Omnigent · OPA · agent governance
toolkits" (p. 54), and p. 86 refers to unnamed repositories with "50K+ stars across multiple repos
in August alone". None of these is on the map. The report alone does not meet #723's threshold of
five candidates for a category proposal.

Products the report names, checked against `sources/products/` and `sources/registry/`:

| Report layer and page | On the map | Not on the map |
|---|---|---|
| Coding harnesses, p. 58 census | `claude-code` (closed, agrees), `codex-cli` (Apache 2.0, agrees), `opencode`, `openhands`, `cline`, `aider`, `goose`, `hermes-agent`, `openclaw`, `antigravity` | Kimi Code CLI (MIT), DeepSeek Harness v0.1 (MIT), Mistral Vibe CLI (named only in `codestral`'s description), Pi, Qwen Code |
| Gemini CLI, p. 58: "Gemini CLI → Antigravity CLI · Open → closed (Qwen Code is the living fork)" | `gemini-cli` is scored openness 5 / adoption 4 with no mention of the move. `sources/products/antigravity.yaml` already says its CLI "supersedes the earlier Gemini CLI" | |
| Orchestration and memory, p. 54 | `langgraph`, `crewai`, `autogen`, `llama-index` | Mem0, Zep. Letta is only a tail row in `sources/registry/orchestration_agents.yaml` |
| Interop and surface, p. 54 | `model-context-protocol`, `agent2agent-protocol`, `ag-ui` | A2UI, x402, AP2, UCP. AGENTS.md is a tail row in `sources/registry/agent_tools_connectors.yaml` |
| Sandboxes and eval/observability, p. 54 | `e2b-sandbox`, `daytona-sandbox`, `modal-sandboxes`, `langfuse`, `phoenix` | |
| Training loop (ADAPT), pp. 54, 73 | `tinker` (`finetuning_code`, closed), `together-fine-tuning`, `fireworks-fine-tuning` | SkyRL tx (mentioned only in `anyscale-fine-tuning`), OpenTinker, MinT, Microsoft Foundry's Tinker-style loop, Nebius Token Factory, Prime Intellect |
| Trust and safety (ROOST), p. 25 | `osprey`, `coop`, `gpt-oss-safeguard`, `zentropi-cope`, all in `safeguards` | Roblox's "PII, Sentinel and voice classifiers", Mila's suicide-assistance guardrail |
| Open-weight models, pp. 14, 35 | | Hy3 (Tencent; second on OpenRouter in August at 34.1T, p. 14), Muse Glimmer, Mistral Medium 3.5 |

The report also records two changes of ownership that the map's organization records don't carry:
"Nvidia · Hugging Face · … · $12.93B · Sept 3, 2026 · signed" and "Stripe · OpenRouter · … · Aug 19,
2026 · announced" (p. 49). `sources/organizations/hugging-face.yaml` and
`sources/organizations/openrouter.yaml` list neither. `docs/reference/identity.md` has no field for a
parent company, so this is a question, not a fix.

## Recommended follow-ups

None of these is made here. Each names the door it goes through.

1. **update-product `kimi`.** Re-read the K3 LICENSE (the live digest differs from the cited one).
   Rename the license from `Modified-MIT` to the custom "Kimi K3 License". Replace the "excludes
   commercial use" reading with the MaaS separate-agreement term and the UI-attribution term, and
   let the rubric decide whether the openness value moves.
2. **update-product `glm`.** Change `code: open (inference)` to `partial`, as
   `sources/rubrics/pretrained.yaml` defines it.
3. **update-product `inkling`.** Record the separate, changeable acceptable use policy in the
   license detail and check its license tier.
4. **update-product `qwen`.** Add Qwen3.8's attribution threshold to the license detail.
5. **update-product `nemotron`.** No value change is proposed. Consider saying in the published note
   that `data: open` reads post-training data, so a reader who compares it with Mozilla's "partial /
   gated" sees why the two differ.
6. **add-product or update-product: Muse Glimmer.** Either add it as Meta's open-weight row or name
   the family row that carries it, as `multimodal_models` already says one does.
7. **add-product candidates: Hy3 (Tencent) and Mistral Medium 3.5** for the model categories. Mistral
   Medium 3.5 could instead be an update-product question on which Mistral row it governs.
8. **update-product `gemini-cli`.** Reconcile it with `antigravity`'s statement that the Antigravity
   CLI supersedes Gemini CLI, and with Mozilla's "Open → closed" reading. This may mean retirement.
9. **update-product `mimo-pro` (adoption).** Its Hugging Face reading (adoption 2) contradicts a
   top-three OpenRouter position. This is the calibration case for #724 and for the missing
   OpenRouter adoption route in `sources/signal_routing.yaml`.
10. **add-product candidates for `orchestration_agents`:** Kimi Code CLI, DeepSeek Harness, Mistral
    Vibe CLI, Qwen Code. Run them through discover-candidates first.
11. **Category question: agent memory.** Mem0, Zep and Letta have no home. Decide whether they
    belong in `orchestration_agents` or justify a category (edit-category).
12. **Category question: agent authorization (#723 point 5).** OPA, Omnigent and meta-harness
    tooling are the report's only named candidates. Run discover-candidates before any proposal, and
    check the boundary against `safeguards` and #93.
13. **add-product candidates for `agent_protocols`:** A2UI, x402, AP2 and UCP. Promote AGENTS.md from
    its tail row.
14. **add-product candidates for `finetuning_code`:** SkyRL tx, OpenTinker, Prime Intellect's
    platform and Nebius Token Factory.
15. **add-product candidates for `safeguards`:** Roblox's open classifiers and Mila's guardrail.
16. **Category question for #723 point 2: an operational gap type.** Mozilla's standardization and
    enterprise-readiness columns have no counterpart on the map. Decide whether to pursue one, and
    note that Mozilla's grades are AI-assisted ordinal judgments (p. 91), not measurements the map
    could import.
17. **Category question for #723 point 4: closed-edge workloads.** No frontier open family on the map
    cites GDPval, long-context retrieval or METR time horizons. Decide whether the capability
    anchors in `base_pretrained` and `finetuned_chat` should look for them on the next refresh.
18. **Category question: change of ownership.** Decide whether the map records Nvidia–Hugging Face
    and Stripe–OpenRouter anywhere, for example in a `model_hubs` resiliency reading, given that
    `docs/reference/identity.md` has no parent-company field.

For #724: the report supports 79% and 71% for developers using open and closed models. It supports
51% against 63% reaching production, n=1,494. It does not support the word "professional" for those
figures, and it publishes no question wording. Quote them as "Mozilla/SlashData 2026 developer
survey, n=1,494 (p. 21) and p. 22", not as figures about professional developers.
