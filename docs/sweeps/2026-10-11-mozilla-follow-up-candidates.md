# Mozilla follow-up candidates: 2026-10-11

This is the `discover-candidates` pass that `2026-10-07-mozilla-state-of-osai-comparison.md` asks for
in its recommended follow-ups (item 4), for Linear OSO-6218 and issue #723. It covers every product
that record names as "not on the map", plus the two ROOST Model Community partners that the ROOST
repository lists alongside Roblox and Mila. Nothing is scored. Item 4's add-product step, and items
1 to 3 (record fixes on existing products), are separate pull requests.

## Window and sources

Every source was read on 2026-10-11, against `main` at `02e0333`.

- **The signal list:** the comparison record's table (section 2) and its follow-ups (item 4).
- **The ROOST Model Community README:** <https://raw.githubusercontent.com/roostorg/model-community/main/README.md>.
- **Each candidate's primary source:**
  - GitHub repositories, read as raw `README.md` and `LICENSE` from `raw.githubusercontent.com`.
  - The Hugging Face model API (`https://huggingface.co/api/models/<id>`, and `/api/organizations/<org>/overview` for org identity).
  - The PyPI JSON API and the npm registry for package names.
  - Vendor pages, where a product has no repository.
- **Web search** was used only to find these sources, never as the evidence itself.

## Counts

```
raw_signals       = duplicate_signals + unique_candidates
28                = 9                 + 19

unique_candidates = accepted          + parked
19                = 18                + 1
```

## Accepted (18 rows)

| Slug | Registry file | Identifiers | Primary source |
|---|---|---|---|
| `muse-glimmer` | `finetuned_chat` | `meta-models/Muse-Glimmer-30B` | HF API (Apache-2.0). The `meta-models` org overview reads "Meta Inc.", verified, with 4 models, all Muse Glimmer. `multimodal_models` keeps it out of that category ("stays in its family row in base_pretrained or finetuned_chat"). `muse-spark` is closed and Spark-only, so Glimmer gets its own row beside it |
| `kimi-code-cli` | `orchestration_agents` | `MoonshotAI/kimi-cli`, PyPI `kimi-cli` | Repository README and LICENSE (Apache-2.0); PyPI 200. Mozilla gives MIT; the repository's LICENSE file is Apache-2.0 |
| `grok-build` | `orchestration_agents` | `xai-org/grok-build` | Repository README and LICENSE (Apache-2.0, "Copyright 2023-2026 SpaceXAI"). `agent-manager` names it only in prose |
| `deepseek-harness` | `orchestration_agents` | `deepseek-ai/deepseek-harness`, npm `@deepseek-ai/dsh` | Repository README and LICENSE (MIT) on `master`; npm 200 |
| `mistral-vibe` | `orchestration_agents` | `mistralai/mistral-vibe`, PyPI `mistral-vibe` | Repository README and LICENSE (Apache-2.0); PyPI 200. `codestral` names it only in prose |
| `qwen-code` | `orchestration_agents` | `QwenLM/qwen-code`, npm `@qwen-code/qwen-code` | Repository README and LICENSE (Apache-2.0); npm 200. Mozilla calls it "the living fork" of Gemini CLI. `qwen-coder` names it only in prose |
| `a2ui` | `agent_protocols` | `google/A2UI`, homepage | Repository README and LICENSE (Apache-2.0); <https://a2ui.org> 200 |
| `universal-commerce-protocol` | `agent_protocols` | `universal-commerce-protocol/ucp`, homepage | Repository README and LICENSE (Apache-2.0); <https://ucp.dev> 200. Google announced it, co-developed with retailers, so `org: google` follows the AP2 row |
| `skyrl` | `finetuning_code` | `NovaSky-AI/SkyRL`, PyPI `skyrl-tx` | Repository README and LICENSE (Apache-2.0). Mozilla names "SkyRL tx", the Tinker-compatible backend that ships as the `skyrl-tx` package inside the SkyRL repository, so the row is the repository. `anyscale-fine-tuning` mentions it only in prose |
| `opentinker` | `finetuning_code` | `open-tinker/OpenTinker`, arXiv `2601.07376` | Repository README and LICENSE (Apache-2.0). The paper is from UIUC |
| `prime-rl` | `finetuning_code` | `PrimeIntellect-ai/prime-rl` | Repository README and LICENSE (Apache-2.0). Mozilla names "Prime Intellect" for the training loop. prime-rl is its open post-training framework; the hosted Lab entrypoint Prime Intellect announced is not separately addressable. `prime-rl` is not on PyPI (404), so there is no package field |
| `nebius-token-factory-post-training` | `finetuning_code` | homepage | <https://nebius.com/services/token-factory/post-training> 200. A closed hosted service, like `tinker` and `together-fine-tuning`. Homepage-only, so weaker evidence than the others |
| `roblox-pii-classifier` | `safeguards` | `Roblox/roblox-pii-classifier-v2` | HF API; ROOST Model Community README |
| `roblox-voice-safety-classifier` | `safeguards` | `Roblox/voice-safety-classifier-v3` | HF API; ROOST Model Community README |
| `roblox-sentinel` | `safeguards` | `Roblox/Sentinel` | Repository README and LICENSE (Apache-2.0); linked from `roostorg/model-community/roblox-sentinel/README.md` |
| `mila-suicide-prevention-guardrail` | `safeguards` | `mila-ai4h/Mila-Suicide-Prevention-Output-Guardrail` | HF API (Apache-2.0, created 2026-08-04); linked from `roostorg/model-community/mila/README.md` |
| `shieldstral` | `safeguards` | `mistralai/Shieldstral-1.0-3B` | HF API. A ROOST Model Community partner model, listed in the README beside Roblox and Mila |
| `policylm` | `safeguards` | `musubilabs/policylm-1.7b` | HF API (Apache-2.0, created 2026-10-02); linked from `roostorg/model-community/musubi-policylm/README.md`. Musubi already appears in `coop`'s description as Coop's hosted provider |

**Three Roblox rows, not one.** The three are separately named releases with separate artifacts: a
text PII model, a voice model and a Python library. Each answers a different question, which is the
identity rule elsewhere in `safeguards`.

**New organizations.** These six new orgs come with handles in `sources/org_handles.yaml`:

- `novasky-ai` (GitHub and Hugging Face `NovaSky-AI`)
- `open-tinker` (GitHub)
- `prime-intellect` (GitHub `PrimeIntellect-ai`, Hugging Face `PrimeIntellect`, `primeintellect.ai`)
- `nebius` (`nebius.com`)
- `mila` (Hugging Face `mila-ai4h`, `mila.quebec`)
- `musubi-labs` (Hugging Face `musubilabs`, `musubilabs.ai`)

Two existing orgs gain a handle: `xai` (GitHub `xai-org`) and `meta-superintelligence-labs`
(Hugging Face `meta-models`).

## Duplicates (9)

| Signal | Resolves to |
|---|---|
| Hy3 (Tencent) | Registry row `hunyuan` in `base_pretrained`, Tencent's Hunyuan line. The row still declares `tencent/Hunyuan-A13B-Instruct`. Hy3 (`tencent/Hy3`, 496,350 downloads on 2026-10-11) is the line's current release, so the row's artifact should move to it when the row is promoted |
| Mistral Medium 3.5 | `mistral-medium`, proposed in #895 |
| Pi | Head product `pi-coding-agent` (#884, #889) |
| x402, AP2 | Registry rows in `agent_protocols` (#868) |
| AGENTS.md | Registry row `agents-md` in `agent_tools_connectors`. Promoting it is an `add-product` step, not this sweep |
| Microsoft Foundry's Tinker-style loop | Head product `azure-openai-fine-tuning`. Foundry's documented path is job-based fine-tuning plus a reinforcement fine-tuning API; no separate product was found |
| Zentropi CoPE-B, gpt-oss-safeguard (ROOST README) | Head products `zentropi-cope` and `gpt-oss-safeguard` |

## Parked (1)

| Candidate | Reason |
|---|---|
| MinT (Mind Lab) | Found only as a research post on macaron.im describing a managed post-training service. There is no product page, API documentation or repository to anchor an identity. Revisit if Mind Lab publishes one |

## Validation

- `uv run python -m build.validate`: 0 errors.
- `tests/fixtures/identity_edges_pass.json` was regenerated with `build.identity_eval --write-fixture`.
