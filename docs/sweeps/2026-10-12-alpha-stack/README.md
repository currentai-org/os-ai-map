# Alpha stack gaps: 2026-10-12

This is the `discover-candidates` pass for issue #903. Alpha, the chat at
<https://www.aipotluck.org/chat>, is built mostly from parts the map is meant to cover, and the
issue lists the AI components it runs on that the map lacks. The pass covers every unchecked item in
the issue's "Missing products" section, plus its scope question.

Two items are not candidate rows. The ALIA instruct checkpoint is an artifact added to the head
product `alia-40b`. `shieldstral` and `mistral-medium` are promoted from registry rows to scored head
products under `add-product`, in their own commits in the same pull request.

## Window and sources

Every source was read on 2026-10-12, against `main` at `605493d`.

- **The signal list:** issue #903's "Missing products" and "A scope question" sections.
- **Alpha's code**, `currentai-org/aipotluck.org` at `eb81112`, read for the identifiers Alpha
  actually calls: `web/config/inference.ts` (`PRODUCTION_PICKER`, `ROLE_MODELS`),
  `web/src/lib/chat/routing/catalog.ts` (hosts), `web/src/lib/chat/server/search/openSearch.ts`
  (search endpoints), `web/src/lib/chat/server/storage/csamScan.ts` (HMA),
  `web/src/lib/chat/server/search/rerank.ts` (TEI) and `groundcheck/app.py` (LettuceDetect).
- **Each candidate's primary source:**
  - The Hugging Face model API (`https://huggingface.co/api/models/<id>`) and model listing
    (`/api/models?author=<org>`).
  - GitHub repositories, read as raw `README` and `LICENSE` files from `raw.githubusercontent.com`.
    `api.github.com` is not reachable from this session, so no star counts are recorded.
  - The PyPI JSON API and the npm registry for package names.
  - Vendor pages and Mistral's model documentation (`docs.mistral.ai/models/...`).

## Counts

A raw signal is one product or build the issue names. The three SEA-LION builds are three signals,
and the Wikipedia and Wikinews search APIs are two.

```
raw_signals       = duplicate_signals + unique_candidates
25                = 6                 + 19

unique_candidates = accepted          + parked
19                = 16                + 3
```

## Accepted (16 rows)

| Slug | Registry file | Identifiers | Primary source |
|---|---|---|---|
| `sea-lion` | `finetuned_chat` | `aisingapore/Nemotron-SEA-LION-v4.8-120B-A12B` | HF API: MIT, created 2026-09-08, `base_model` its own `-Base`. One family row, not three. The Qwen 32B (MIT, base `Qwen/Qwen3-32B`) and Gemma 27B (Gemma license) builds are post-trained on other labs' bases, as v4.8 is on Nemotron, so the family sits beside `nemotron` and `hermes` rather than in `base_pretrained`. A registry row holds one Hugging Face id, so promotion adds `aisingapore/Qwen-SEA-LION-v4-32B-IT` and `aisingapore/Gemma-SEA-LION-v4-27B-IT`. All three are in Alpha's `PRODUCTION_PICKER` |
| `bielik` | `finetuned_chat` | `speakleash/Bielik-11B-v3.0-Instruct`, arXiv `2601.11579` | HF API: Apache-2.0, `gated: auto`, base `speakleash/Bielik-11B-v3-Base-20250730`. The paper's abstract says Bielik 11B v3 "extends the Mistral 7B v0.2 architecture, scaled to 11B parameters via depth up-scaling", trained by continuous pre-training then SFT, DPO and RL. It is not trained from scratch, so it goes in `finetuned_chat`. The 2026-09-07 tail batch saw only the `-awq` quantization and dropped it on the download floor |
| `mistral-small` | `finetuned_chat` | `mistralai/Mistral-Small-4-119B-2603` | Alpha's `TASK_MODEL` is `mistral-small-2603`. Mistral's page <https://docs.mistral.ai/models/mistral-small-4-0-26-03> names it Mistral Small 4, v26.03, Apache 2.0, with API id `mistral-small-2603`, and calls it a hybrid model "unifying instruct, reasoning, and coding". HF API: Apache-2.0. It sits with `mistral-medium`, which is also one post-trained checkpoint |
| `mistral-studio` | `inference_code` | `mistralai/client-python`, PyPI `mistralai`, homepage | <https://mistral.ai/products/la-plateforme> now redirects to <https://mistral.ai/products/studio>, titled "Mistral Studio", so the row takes the current name. The official Python SDK (Apache-2.0) is the API's client. Alpha's default model is served from `api.mistral.ai` |
| `infomaniak-ai-services` | `inference_code` | homepage | <https://www.infomaniak.com/en/hosting/ai-services>, titled "AI Service – open source AI on demand via API, hosted in Europe", says its data centres are in Switzerland. Alpha's tests name `api.infomaniak.com` as an Apertus backend |
| `featherless` | `inference_code` | homepage | <https://featherless.ai>, titled "Featherless - Serverless LLM Hosting". Alpha's tests name `api.featherless.ai` as an Apertus backend. The ledger's `featherless-chat-models/*` entries are model mirrors, not this product |
| `scaleway-generative-apis` | `inference_code` | homepage | <https://www.scaleway.com/en/generative-apis/> says all models are hosted in Paris. Alpha's catalog says Scaleway runs GLM for Alpha "in Paris, through Hugging Face" |
| `hugging-face-inference-providers` | `inference_code` | npm `@huggingface/inference`, homepage | <https://huggingface.co/docs/inference-providers/index>. The npm package (MIT, `huggingface/huggingface.js`) is the Inference Providers client. That repository is a monorepo, so the row does not claim it. `huggingface-hub-platform` scores the Hub, not the router, and Alpha calls `router.huggingface.co` |
| `public-ai-inference-utility` | `inference_code` | `forpublicai/platform.publicai.co`, homepage | The repository README (LICENSE MIT) calls it "the developer portal and API gateway for the Public AI Inference Utility". The about page calls the Utility "a nonprofit, open-source project". Alpha's `GATEWAY_BASE_URL` is `api-internal.publicai.co` |
| `text-embeddings-inference` | `inference_code` | `huggingface/text-embeddings-inference` | Repository README and LICENSE (Apache-2.0). It sits beside `text-generation-inference`. Alpha's reranker calls a TEI endpoint's `/rerank` |
| `hasher-matcher-actioner` | `safeguards` | `facebook/ThreatExchange`, homepage (the HMA subtree) | The HMA README calls it "a reference implementation for a key Trust and Safety content moderation capability: copy detection". LICENSE BSD (Meta). **`facebook/ThreatExchange` is a monorepo** that also holds PDQ, TMK and `python-threatexchange`. Its repository counts are not HMA's alone, which promotion has to record. Alpha's `csamScan.ts` calls HMA's `/m/lookup` |
| `openalex` | `search_retrieval` | `ourresearch/openalex-elastic-api`, homepage | That repository's README: "the elasticsearch-backed portion of the OpenAlex API". LICENSE MIT (OurResearch). `openalex.org` answers automated requests with a bot wall, and the API's anonymous daily budget was spent, so the homepage was not read. Alpha calls `api.openalex.org/works` |
| `mediawiki-search-api` | `search_retrieval` | `wikimedia/mediawiki-extensions-CirrusSearch`, homepage | <https://www.mediawiki.org/wiki/API:Search> documents `list=search` (GPL-2.0-or-later). Alpha's `openSearch.ts` calls the same `https://<lang>.<site>/w/api.php` surface for Wikipedia and Wikinews, "differing only by host", so it is one row. CirrusSearch is the extension behind it, and its GitHub repository is a mirror of Wikimedia's Gerrit. The `wikipedia` row stays the training dataset |
| `arxiv-api` | `search_retrieval` | homepage | <https://info.arxiv.org/help/api/index.html>, "arXiv API Access". Alpha calls `export.arxiv.org/api/query`. Homepage only, so it is weaker evidence than a repository-backed row |
| `lettucedetect` | `safeguards` | `KRLabsOrg/LettuceDetect`, PyPI `lettucedetect`, arXiv `2502.17125` | Emitted under R-2026-10-12-b (below). Repository README and LICENSE (MIT); PyPI `lettucedetect` names the repository as its homepage; the README's arXiv badge is the paper. The v2 encoder Alpha runs, `KRLabsOrg/lettucedect-v2-mmbert-base`, is Apache-2.0 on the HF API, created 2026-06-22. Alpha's `groundcheck/app.py` wraps it as a token classifier over each answer |
| `bubblewrap` | `deployment` | `containers/bubblewrap` | README, `COPYING` (LGPL 2.1 text), and `bubblewrap.c` declares `LGPL-2.0-or-later`. It sits beside `gvisor`, `firecracker` and `sandbox-runtime`, which itself uses bubblewrap on Linux. Alpha's `agent-service` runs agent-mode tool calls under `bwrap` |

**New organizations.** Nine orgs, with handles in `sources/org_handles.yaml`:

- `speakleash` (GitHub and Hugging Face `speakleash`, `speakleash.org`)
- `infomaniak` (`infomaniak.com`)
- `featherless` (`featherless.ai`)
- `scaleway` (`scaleway.com`)
- `public-ai` (GitHub `forpublicai`, `publicai.co`)
- `containers` (GitHub `containers`). This is the GitHub organization behind Podman, Buildah and
  bubblewrap. `type: unknown`, since no page establishes it as a company or a foundation.
- `ourresearch` (GitHub `ourresearch`, `openalex.org`)
- `arxiv` (`arxiv.org`)
- `krlabs` (GitHub and Hugging Face `KRLabsOrg`). `type: unknown`, and no homepage: the
  repository and the Hugging Face organization name "KR Labs" and no page establishes what kind of
  body it is.

`meta` also gains a GitHub handle, `facebook`, the account that owns ThreatExchange.

**Seats (`country`)** are in `countries/batch-01.jsonl`, each with the page it was read from.
`speakleash` is `PL`, `infomaniak` `CH`, `featherless` `US` and `scaleway` `FR`. `public-ai`,
`ourresearch` and `arxiv` stay unset, each with its reason in the ledger. `containers` and `krlabs`
are `type: unknown`, so they take no seat.

## Duplicates (6)

| Signal | Resolves to |
|---|---|
| SEA-LION v4 Qwen 32B, SEA-LION v4 Gemma 27B | The `sea-lion` row (self-dedup: one family) |
| Wikinews search API | The `mediawiki-search-api` row (self-dedup: the same `w/api.php` surface) |
| ALIA-40b-instruct | Head product `alia-40b`, which now declares `BSC-LT/ALIA-40b-instruct-2606`. The link in the issue, `BSC-LT/ALIA-40b-instruct`, returns 401: no repository has that name. BSC publishes dated builds (`-2601`, `-2605`, `-2606`, plus `-fc-` function-calling builds). Alpha requests the gateway alias `BSC-LT/ALIA-40b-instruct`, and its own 2026-09-07 research note on public and sovereign assistants cites `-2606`, the latest instruct build and the most downloaded. Which dated build the gateway resolves the alias to was not confirmed |
| Shieldstral | Registry row `shieldstral` (#896), promoted to a head product in this PR |
| Mistral Medium | Registry row `mistral-medium` (#895), promoted in this PR. Alpha calls it as `mistral-medium-2604` against `api.mistral.ai`. Mistral's page <https://docs.mistral.ai/models/mistral-medium-3-5-26-04> names Mistral Medium 3.5, version 26.04, "released as open weights under a Modified MIT license", and links its weights to `huggingface.co/mistralai/Mistral-Medium-3.5-128B`, the checkpoint the row points at. The `-2604` id follows the version number the same way `mistral-small-2603` follows Small 4's v26.03 |

## Parked (3)

| Candidate | Reason |
|---|---|
| AI Singapore's SEA-LION API (`api.sea-lion.ai`) | Not a product, under R-2026-10-12-a (below). Alpha's `gatewayFallbackGate.ts` names it. <https://docs.sea-lion.ai> answers 200 |
| NextBit (ALIA's host) | Not a product, under R-2026-10-12-a, and it has no anchor either way. Alpha's catalog entry is `{name: 'NextBit', blurb: 'Runs ALIA for Alpha.'}` with no URL. `nextbit.es` is a web-design agency in Menorca, not this host. Revisit when the gateway's operators name the provider's site |
| PLGrid's LLMLab (Bielik's host) | Not a product, under R-2026-10-12-a. <https://llmlab.plgrid.pl> answers 200 with a client-rendered page titled "LLM Lab" and no readable text |

## Rulings

All three were decided on the review of #907 and are recorded in `docs/rulings/log.yaml`.

**R-2026-10-12-a: the national hosts are not products.** The Public AI gateway routes SEA-LION to
AI Singapore's API, ALIA to NextBit and Bielik to PLGrid's LLMLab. Each is a distribution
relationship for a model product, unlike Mistral Studio, Infomaniak, Featherless and Scaleway, which
are general hosted-inference products serving many families. The three stay parked. The longer-term
shape is a many-to-many hosting relationship between models and hosts, not a scalar attribute on the
model, and that is outside this sweep.

**R-2026-10-12-b: a groundedness detector goes in `safeguards`.** A serving-time detector that takes
an answer and decides whether it is grounded is a safeguard; a harness whose primary job is running
and grading model evaluations is `evaluation_code`. This matches `granite-guardian` ("hallucination
checks for retrieval pipelines") and `azure-content-safety` ("groundedness detection") in
`safeguards`, while `patronus-evaluation-platform`, built around Lynx, stays in `evaluation_code`.
The `lettucedetect` row is emitted above.

**R-2026-10-12-c: Mistral's Modified MIT license is `use_bounded`.** It withholds every right from a
company whose consolidated monthly revenue exceeds USD 20M, which is the `use_bounded` definition.
The bare `Modified-MIT` spelling that `devstral` recorded resolved to `permissive_non_osi`. The text
is now named `Mistral-Modified-MIT` and listed under `use_bounded` on both the model and pretrained
ladders. The bare spelling is retired from `permissive_non_osi`, since no record uses it any more and
other vendors' "modified MIT" texts carry different terms. `devstral` and `mistral-medium` record the
new name. Both still score 3, because `use_bounded` resolves to 3 before the data and code rungs are
read. The two tiers would have diverged for a release under this license that opened its recipe.

## Promoted to head products

| Product | Category | Openness | Adoption | Capability |
|---|---|---|---|---|
| `shieldstral` | `safeguards` | 3/open_weights: Apache-2.0 weights, ungated. The technical report describes the 54.1M-sample training set, which is not released | 2: 37,660 Hugging Face downloads in 30 days | 4, `at` `gpt-oss-safeguard`. The card's F1 tables put the two level, and Shieldstral adds images but gives no reasoning |
| `mistral-medium` | `finetuned_chat` | 3/open_weights: ungated weights, no data or training code | 2: 72,266 Hugging Face downloads in 30 days. API and Le Chat use is not visible | 3, `at` `o-series`. It scores 14 on the Artificial Analysis Intelligence Index, between GPT-4o (8) and o3 (20) |

## Validation

- `uv run python -m build.validate`: 0 errors.
- `tests/fixtures/identity_edges_pass.json` was regenerated with `build.identity_eval --write-fixture`.
- The homepage handle-coverage baseline was re-pinned with `build.identity_eval
  --write-coverage-baseline`, in its own commit.
- `build.check_artifacts` was not run: it reads `currentai.signal_github.artifact_state`, which this
  session's OSO key cannot read (403).
