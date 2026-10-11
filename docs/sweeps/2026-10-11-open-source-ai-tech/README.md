# open-source-ai.tech against the map: 2026-10-11

## Scope

This sweep compares the products listed on The Open-Source AI Stack
(<https://www.open-source-ai.tech/>, source repository `Beige-Coffee/open-source-ai`) with the map
on `main` at `02e0333`. It is the product half of Linear OSO-6250. The category half was handled
on 2026-10-07: issues #845 (structured generation), #846 (agent memory) and #847 (decentralized
training, inference and compute) were opened from the same comparison, and agent payment rails went
into `agent_protocols` in #868.

The procedure is `docs/workflows/discover-candidates.md`. Nothing was scored and no category was
created or edited.

## Window

A single snapshot. Every source was read on 2026-10-11. The site has no dated changelog, so the next
comparison should re-read its sitemap in full.

## Files in this directory

| File | What it holds |
|---|---|
| `README.md` | This record |
| `fetch-log.tsv` | Every fetch: id (`F0001`…), date, HTTP status, bytes, sha256 of the body, URL. All 224 returned 200 |
| `candidates.tsv` | All 191 raw signals with the site's identifiers, the proposed or matched slug, the disposition and the fetch ids behind each |

## Sources and what counts as a signal

The site is a static build, so every page was read as HTML without rendering.

- The sitemap (`F0001`, `F0002`) lists 53 project pages, 116 model pages and 23 hardware pages.
- The 11 stack-layer pages (`F0003`–`F0013`) link to the project pages and were used to confirm the
  project list. They add no products of their own.
- Each entity page was read for its title, its own repository (the first GitHub link in document
  order; later links on a page point to related projects), its first Hugging Face link and its
  "Project site" link.

**A raw signal is one entity page.** `models/compare` is a comparison tool, not a product, and is not
counted. That leaves 53 + 115 + 23 = **191 raw signals**.

Hugging Face API reads and primary-source pages for the accepted and parked candidates follow the
entity pages in the fetch log (`F0206` on).

## Counts

```
raw_signals       = duplicate_signals + unique_candidates
191               = 166               + 25

unique_candidates = accepted          + parked
25                = 6                 + 19
```

The 166 duplicates break down as follows.

| Disposition | Signals | Meaning |
|---|---|---|
| `duplicate:product` | 35 | The page's own repository, Hub id, slug or name is already a head product |
| `duplicate:sku_of` | 105 | A release or SKU of a head product that holds the whole line (`claude-sonnet`, `gemini-pro`, `qwen-instruct`, `llama`, `o-series` and so on, per `sources/model_families.yaml` and each record's description), or a prior or current generation of a seeded `datacenter_accelerators` row, which that category's identity rule makes a SKU of the line |
| `duplicate:registry` | 14 | Already a registry row (`structured_generation`, `orchestration_agents`, `agent_protocols`, `finetuned_chat`, `base_pretrained`) |
| `duplicate:self` | 12 | A second page for a candidate already counted, for example Mixtral 8x7B beside Mixtral 8x22B, or the six Apple Mac pages |

Two `duplicate:sku_of` calls rest on judgment rather than a declared artifact, and a reviewer may
want to check them:

- **Llama-3.1-Nemotron Ultra and Llama-3.3-Nemotron Super** go to `nemotron`, as earlier generations
  of NVIDIA's Nemotron line, not to `llama`, although `llama-*` in `model_families.yaml` would
  catch their slugs.
- **Qwen3 Max and Qwen3.5 Plus**, Alibaba's hosted models, go to `qwen`, whose aliases already hold
  `qwen-3-7-max`.

## Accepted (6 rows)

| Slug | Registry file | Identifiers | Signal | Fetches | Note |
|---|---|---|---|---|---|
| `mixtral` | `finetuned_chat` | `mistralai/Mixtral-8x22B-Instruct-v0.1` | `models/mixtral-8x22b-instruct-v0-1` | F0206–F0208 | Apache-2.0. Mistral's sparse mixture-of-experts line from 2023–24. `mistral-large`'s own description calls Large 3 "Mistral AI's first mixture-of-experts model since Mixtral", so Mixtral is a separate line, not a Large SKU. It is a legacy line, as `mistral-7b-instruct` is |
| `mistral-nemo` | `finetuned_chat` | `mistralai/Mistral-Nemo-Instruct-2407` | `models/mistral-nemo-12b-instruct` | F0209–F0210 | Apache-2.0 12B, built with NVIDIA. `mistral-7b-instruct`'s `version_in_identity` already names Nemo as a product of its own |
| `mistral-medium` | `finetuned_chat` | `mistralai/Mistral-Medium-3.5-128B` | `models/mistral-medium-3` | F0211–F0212 | The site lists Medium 3, which was API-only. Mistral Medium 3.5 has open weights under a modified MIT license (Hub license `other`). This also answers the open item in `2026-10-07-mozilla-state-of-osai-comparison.md` (next steps, item 4): Medium 3.5 is a separate Mistral row, not a release of `mistral-large` |
| `apple-foundation-models` | `finetuned_chat` | arXiv `2507.13575`, homepage | `models/apple-foundation-on-device-2025` | F0213–F0214 | Apple's on-device and server models, reached by developers through the Foundation Models framework. The weights are closed. There is no Hub or repository artifact, so this is a paper-and-homepage row, weaker evidence than the others |
| `covenant` | `base_pretrained` | `1Covenant/Covenant-72B`, arXiv `2603.08163`, homepage | `projects/templar-covenant-72b` | F0215–F0218 | Apache-2.0 72B base model trained from scratch by permissionless participants over Bittensor. #847 already places such models in `base_pretrained`, whatever the ruling on its category. The Templar training system itself is dormant, according to its README (F0218), and stays with #847. New org `covenant-ai`, with GitHub `one-covenant`, Hub `1Covenant` and homepage `covenant.ai` handles |
| `common-pile` | `training_synthetic_datasets` | dataset `common-pile/comma_v0.1_training_dataset`, homepage | `projects/common-pile-v0` | F0219–F0221 | EleutherAI's openly licensed 8 TB text corpus. The map has its model, `comma`, but not the dataset, the same split as `olmo` and `dolma`. See the identity note below |

**Identity note on `common-pile`.** `comma` declares `r-three/common-pile`, the repository that
builds the corpus, and arXiv `2506.05209`, the paper that describes both the corpus and the model.
Validation rejects an artifact already claimed elsewhere, so the row carries only the dataset and
the homepage. If the dataset is promoted, the repository and paper probably belong on it rather than
on `comma`, and that is an `update-product` question for `comma`. The row declares the filtered
training mix rather than `common-pile/raw_v0.1_parquet` (F0220), because the filtered mix is the
artifact people download: 21,297 downloads against 3,945 on 2026-10-11.

## Parked (19)

| Candidate | Signal | Reason |
|---|---|---|
| QwQ | `models/qwq-32b-preview` (F0222–F0223) | **identity-unresolved.** Qwen's reasoning line: QwQ-32B-Preview, then QwQ-32B in March 2025, Apache-2.0. Qwen3 folded thinking into its main chat models, so QwQ may be a SKU of `qwen-instruct` rather than a product. `model_families.yaml` has no `qwq-*` pattern either way |
| INTELLECT | `projects/intellect-1` (F0224) | **category-boundary.** INTELLECT-1 is a 10B base model pretrained from scratch over decentralized compute (`base_pretrained`). INTELLECT-2 and INTELLECT-3 are reinforcement-learning post-trains of other labs' bases (`finetuned_chat`). One line straddles two categories, and the call is the reviewer's |
| Prime Intellect `prime` | `projects/prime-intellect` | **category-proposal #847.** Decentralized training system |
| Nous DisTrO | `projects/nous-distro` | **category-proposal #847** |
| Akash Network | `projects/akash` | **category-proposal #847.** Compute marketplace, part 2 of #847's scope question |
| Bittensor | `projects/bittensor-compute` | **category-proposal #847.** Incentive network, part 2 of #847's scope question |
| GPT-4 (and GPT-4 Turbo) | `models/gpt-4` | **superseded.** The map carries OpenAI's current lines (`gpt-4o`, `gpt-4-1`, `gpt-5`, `gpt-6`, `o-series`) |
| GPT-3.5 Turbo | `models/gpt-3-5-turbo` | **superseded**, as above |
| GPT-4.5 | `models/gpt-4-5` | **superseded.** A research preview OpenAI has since withdrawn |
| Apple Private Cloud Compute | `projects/apple-pcc` | **no-home.** Apple's own server stack for its own models, with no public product to run or rent. Neither `deployment` nor `datacenter_accelerators` fits |
| RISC-V | `projects/risc-v` | **not-a-product.** An instruction-set architecture |
| Apple silicon Macs (6 pages) | `hardware/apple-mac-studio-m3-ultra` | **no-home.** See below |
| NVIDIA GeForce RTX (4090, 5090) | `hardware/nvidia-rtx-5090` | **no-home** |
| NVIDIA RTX PRO 6000 Blackwell | `hardware/nvidia-rtx-pro-6000-blackwell` | **no-home** |
| NVIDIA DGX Spark | `hardware/nvidia-dgx-spark` | **no-home** |
| AMD Ryzen AI Max+ 395 | `hardware/amd-ryzen-ai-max-395` | **no-home** |
| AMD Radeon AI PRO R9700 | `hardware/amd-radeon-ai-pro-r9700` | **no-home** |
| Qualcomm Snapdragon X (X Elite, X2 Elite) | `hardware/qualcomm-snapdragon-x2-elite` | **no-home** |
| Intel Core Ultra 200V (Lunar Lake) | `hardware/intel-lunar-lake` | **no-home** |

**The local-hardware gap.** Fifteen of the site's 23 hardware pages are desktops, laptops,
workstation GPUs and PC chips that people run open models on locally. The map has no home for them:
`edge_hardware` holds single-board computers, modules and accelerator chips for embedded inference,
and `datacenter_accelerators` holds silicon you rack or rent. This sweep opens no category proposal
for them. Whether local inference hardware belongs on the map is a question for the maintainer, and
a `category-proposal` issue is the place to raise it if the answer is yes.

## Validation

- `uv run python -m build.validate`: 0 errors.
- `uv run python -m build.preflight`: see the pull request.
