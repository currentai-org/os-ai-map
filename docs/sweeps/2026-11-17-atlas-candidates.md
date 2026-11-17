# ATLAS catalog against the map, 2026-11-17

A check of the language-specific datasets in AI Singapore's ATLAS catalog against the published
products. ATLAS is a discovery source for the language-specific categories, not a product in them.
Each candidate was read on its Hugging Face card and API record on 2026-11-17, and download figures
are the trailing 30 days.

ATLAS lists several AI Singapore repositories under their old names (`cultural_evaluation-kalahi`
rather than `Cultural-Evaluation-Kalahi`), so a match on repository id alone undercounts what the map
already carries. KALAHI and the other SEA-HELM test sets, SEA-PILE and SEA-Instruct were already on
the map under their renamed repositories.

## Added as head products

| Product | Category | Openness evidence |
|---|---|---|
| `in22` | `language_specific_eval_sets` | CC BY 4.0 on both cards; Hub gate with automatic approval |
| `indicifeval` | `language_specific_eval_sets` | CC BY 4.0 card, ungated; evaluation code MIT |
| `indic-rag-suite` | `language_specific_datasets` | MIT card metadata, ungated; the rows carry Wikipedia paragraphs and Llama 3.3 70B output |
| `mangosteen` | `language_specific_datasets` | ODC-By on both repositories, ungated; meets the four elements of the web-crawl test |

IN22 shares a paper with `bpcc`, but BPCC is the training corpus and IN22 the test set, so it is a
product of its own. Both eval sets join `language_specific_eval_sets` by R-2026-11-17-a and band at
3 on the depth ladder: IN22's 1,024 and 1,503 human-translated sentences per language, and IndicIFEval's
reviewer-approved translated prompts (440 to 490 per language). IndicIFEval's generated prompts carry
no depth.

The corpus ATLAS lists as WangchanLION is published under that name on the Hub
(`aisingapore/WangchanLION-Web` and `-Curated`), but its paper (arXiv 2507.14664), its cards and its
pipeline repository (`vistec-AI/Mangosteen`) all call it Mangosteen, so that is its slug. VISTEC
researchers led the paper; AI Singapore publishes the data and funded the work, and owns the product
here. Its 47.4 billion Thai tokens put it at the size cap's 3.

## Added as links on existing products

- `sea-helm`: `aisingapore/kalahi`, Kalahi's original repository, and `aisingapore/seahelm-audio`,
  which reads two SEA-HELM tasks aloud in synthesized speech. Neither changes the depth band.
- `sea-instruct`: `aisingapore/Small-SEA-Instruct-2602`, a 28,000-row sample published as training
  data for the DuDi distillation paper. Adoption stays at 1 with it summed in.

SEA-NLI (`aisingapore/SEA-NLI`) was proposed as a third SEA-HELM link and was not added. Its paper
(arXiv 2606.03284) presents it as a benchmark of its own and does not place it in SEA-HELM, and the
repository is gated with manual approval, where SEA-HELM's record reads automatic approval for every
task repository. It is a candidate product in its own right once its card can be read.

## Held until the license is clear

- **SEASafeguardBench and SEA-Safeguard-Train** (AI Singapore). A Southeast Asian safety benchmark
  and its cultural training data. SEASafeguardBench's Hub record shows no license and manual
  approval for access, and SEA-Safeguard-Train's record does not load without signing in
  (R-2026-11-17-b). They wait for AI Singapore to confirm terms.
- **IndoCulture** (IndoLEM). Not added. Its paper describes "a high-quality cultural reasoning
  dataset in the Indonesian language", and Indonesian is high at both ends of the per-language
  classification, so it fails the language half of `language_specific_eval_sets` as IndoNLU did
  (R-2026-11-11-b). Its non-commercial license (CC BY-NC-SA 4.0) would show an openness gap, not a
  language gap. It is a candidate for `benchmark_eval_data` if that category wants Indonesian
  cultural benchmarks.

## Left off

- The 269 individual SEACrowd datasets: the SEACrowd collection is already a product, and a hub's
  members are not separate rows.
- Mesolitica's 67 Malay datasets: three are open and ungated.
- ViLM's Vietnamese VLSP evaluation sets: license unknown.
- OpenOrca-Viet: a translated distillation set from 2023.
- StingrayBench: not built for one language or a set of related ones.
- Indic-Bias: its card lists English as its only language.
- The Open Development Mekong corpora: at most about 5,800 examples each.
- The 180 ATLAS datasets with no usable license.
