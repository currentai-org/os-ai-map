# Catalog Gaps

Projects, repos, and orgs that should be in our data foundation but are missing from both GoodAI List and OSS Insights (coverage/ingestion backlog). This doc is about what to add next. Product-level openness/adoption/capability scoring lives in the curated `sources/` tree; see [`warehouse/models/README.md`](../warehouse/models/README.md) for the warehouse model inventory (analysis guidance lives in persona skills).

Last reviewed: 2026-04-28

## Missing Orgs

Major AI organizations with no repos in `ai_repo_activity`:

| Org | Why it matters | Key repos to add |
|-----|---------------|-----------------|
| **stabilityai** | Stable Diffusion ecosystem. Foundational for open image generation | `stabilityai/generative-models`, `stabilityai/StableLM`, `stabilityai/stable-audio-tools` |
| **BAAI / FlagOpen** | BGE embeddings. 28M HF downloads, most popular open embedding model | `FlagOpen/FlagEmbedding`, `FlagOpen/FlagPerf` |
| **CompVis** | Original Stable Diffusion, latent diffusion research | `CompVis/stable-diffusion`, `CompVis/latent-diffusion` |
| **black-forest-labs** | FLUX: leading open image generation model (post-Stability) | `black-forest-labs/flux` |
| **coqui** | XTTS: 7M downloads, leading open TTS | `coqui/TTS` |

## Missing Repos (org exists but key repos not tracked)

| Repo | Org in catalog? | Why it matters |
|------|----------------|---------------|
| `BlinkDL/RWKV-LM` | No (BlinkDL) | RWKV architecture: linear attention alternative to transformers |
| `microsoft/unilm` | Yes (microsoft) | E5 embeddings live here. 7M HF downloads |
| `microsoft/phi-2` | Yes | Phi-2 model repo |
| `microsoft/phi-3` | Yes | Phi-3 model repo |
| `microsoft/phi-4` | Yes | Phi-4 model repo |
| `mistralai/mistral-src` | Yes (mistralai) | Mistral reference implementation (mistral-inference is tracked instead) |
| `qwenlm/qwen2.5` | Yes (qwenlm) | Qwen 2.5 specific repo (qwenlm/qwen is tracked as fallback) |
| `qwenlm/qwen2-vl` | Yes (qwenlm) | Qwen 2 vision-language |
| `tiiuae/falcon3` | Yes (tiiuae) | Falcon 3 model repo (falcon-perception tracked as fallback) |
| `databricks/dbrx` | Yes (databricks) | DBRX model repo (megablocks tracked as fallback) |
| `aisingapore/sea-lion` | Yes (aisingapore) | SEA-LION multilingual LLM |

## Missing Model Families

Foundation models with significant HF presence but no mapping to a GitHub repo:

| HF Author | Downloads | Category | Notes |
|-----------|-----------|----------|-------|
| `colbert-ir` | 14M | Embedding/retrieval | ColBERTv2: late-interaction retrieval |
| `mixedbread-ai` | 4M | Embedding | mxbai-embed: commercial embedding provider |
| `hexgrad` | 9M | TTS | Kokoro-82M: lightweight TTS |
| `pyannote` | 11M | Speech | Speaker diarization, widely used in pipelines |
| `autogluon` | 9M | Time-series | Chronos-Bolt forecasting |
| `moonshotai` | 4M | Multimodal | Kimi-K2.5 vision-language |

## How to Fix

**Option A: Add to GoodAI List upstream.** Contact GoodAI to include these repos. Fixes the gap at the source.

**Option B: Supplemental static model.** Create `warehouse/catalog/supplements/missing_repos.csv` with the same schema as `goodailist_repos`, upload as a static model, and union it with `ai_repo_activity` in a revised UDM.

**Option C: Add to oss-directory.** For repos that are important enough, add them to OSO's oss-directory. This gives full event-level tracking (commits, PRs, issues), not just star counts.

Option B is the fastest path. Option C gives the richest data.
