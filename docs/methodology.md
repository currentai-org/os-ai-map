<!--
Canonical methodology copy for the Open Source AI Map notebook.

This file is HAND-AUTHORED and is the single source of truth for the methodology
prose shown in notebooks/ai-stack-map.py. It is NOT generated.

build/render.py reads it at render time, substitutes the {placeholders} below with
counts computed from build/notebook_data.json, converts the Markdown to HTML, and
bakes the result into the generated notebook (the Summary section into the header,
the Detail section into the Methodology section). The numbers therefore refresh on
every build and cannot drift; edit the prose here and commit.

Placeholders (filled from the payload at build time):
  {total} {scored} {uncategorized} {universe}
  {n_software} {n_models} {n_datasets} {n_hardware}
  {n_orgs} {n_categories} {n_layers} {n_citations} {n_domains}
  {n_openness_gaps} {disc_repos} {disc_models} {disc_packages}
Write prose in the academic register of a methods section: precise, defined,
measured, and forthright about limitations. No marketing cadence.

Companion: docs/guides/openness-spectrum.md is the data-consumer / query reference
for openness (which field to use, openness.class vs openness.score, the class->0-5
gradient table, and cross-category caveats). This file is the reader-facing
narrative; keep the two consistent when the openness model changes.
-->

## Summary

We track {total} open-source AI artifacts across the stack. This map scores {scored} of them in depth on three independent axes: **openness** (graded 0–5 against openness frameworks — the Model Openness Framework for models, OSI classes for software, with data and hardware analogues — not a yes/no), **adoption** (real usage, not stars), and **capability** (benchmarks where they exist, feature coverage where they don't). Every score is sourced. The remaining {uncategorized} are the uncategorized long tail, tracked by usage signal but not yet scored. The openness framework descends directly from the [2024 Columbia Convening on Openness in AI](https://arxiv.org/abs/2405.15802).

## Detail

This document describes how the Open Source AI Map is constructed: how the corpus is assembled, how each product is scored on three axes, how categories are placed on a maturity ladder, and how gaps are derived. The aim is a procedure that is auditable and reproducible rather than a black box. Every non-null score records a primary source and the date it was consulted; values are not inferred or interpolated.

### Corpus and discovery

We distinguish two layers of effort. A **discovery layer** establishes the universe of candidate artifacts, and a more demanding **scoring layer** enriches and grades a curated subset of them.

Discovery draws on large-scale open data through [Open Source Observer](https://www.oso.xyz), an open pipeline for the discovery of open-source software data. From it we assembled approximately {universe} candidate artifacts: roughly {disc_repos} GitHub repositories (identified through the platform's AI topic and keyword search, a catalog of AI-focused organizations and repositories, and the Good AI List), about {disc_models} models and datasets from the Hugging Face Hub, and around {disc_packages} entries from package registries, supplemented by the Open LLM Leaderboard and the AI Incident Database. Candidates were ranked by adoption signal — repository stars, package and model downloads, and related measures — and the most prominent were selected for enrichment.

The scoring layer enriched and graded {scored} products in depth: {n_software} software tools and libraries, {n_models} models, {n_datasets} datasets, and {n_hardware} hardware projects, produced by {n_orgs} organizations. These products are organized into {n_categories} categories across {n_layers} layers of the stack. The remaining {uncategorized} artifacts constitute the uncategorized long tail: they are tracked by usage signal but carry no openness, adoption, or capability score until they are researched and cited.

### The three axes

Each scored product is graded on three axes that answer deliberately different questions: *is it open?* (openness), *is it used?* (adoption), and *is it any good?* (capability). The axes are treated as orthogonal. The analytically interesting cases are those in which they disagree — a widely used model that is barely open, or a fully open project that few have adopted — and holding the axes apart is what makes those cases visible.

#### Openness

Openness is recorded in two fields. The first, the **class**, is a categorical label drawn from the Model Openness Framework and OSI license taxonomy (for example `open_source`, `open_weights`, `open_core`, `source_available`, `restricted`, `gated`, `documented_only`, `closed`). The class is the cross-category normaliser: it is the field to use when positioning a product on an openness spectrum. The second, the **score**, is a 0–5 grade with a component-level breakdown — weights, data, code, checkpoints, and license for models; license tests for software; access, license, and documentation for datasets.

The score is graded relative to what is achievable *within a product type*, so the same number does not carry the same meaning across categories. A pretrained model at 2 is genuinely restricted, because the openness range for models is compressed: open weights typically land near 3, and a 5 requires a fully open pipeline of the Pythia or OLMo kind. A deployment tool at 2 sits elsewhere entirely. The raw 0–5 score should therefore be read as a within-type detail, not as a cross-category coordinate.

For analysis across the whole stack, the class vocabulary is collapsed into three buckets:

| Bucket | Classes |
|--------|---------|
| Open | `open_source`, `open`, `open_core`, `open_hardware` |
| Open-ish | `open_weights`, `source_available`, `gated`, `open_toolchain` |
| Closed | `restricted`, `documented_only`, `closed`, `documented` |

Hardware uses its own openness vocabulary, parallel to the software and model classes: open schematics with an open toolchain (`open_hardware`); proprietary silicon but an open SDK with public datasheets and retail availability (`open_toolchain`); public datasheets but proprietary design or firmware (`documented`); and private or NDA-gated availability (`restricted`).

The framework descends from the [2024 Columbia Convening on Openness in AI](https://arxiv.org/abs/2405.15802) and its [follow-on work](https://arxiv.org/abs/2506.22183), and from the [Model Openness Framework](https://arxiv.org/abs/2403.13784). License, weights, data, and code are each judged separately rather than reduced to a single binary. Primary vendor sources — the blog posts and documentation of Anthropic, Google, OpenAI, Meta, Mistral, NVIDIA, Microsoft, AWS, and others — are cross-checked against the actual LICENSE file in the repository and the model card on the Hugging Face Hub, with arXiv and general web search used to corroborate. The distinction between "open weights" and "open source" is not incidental to the map; it is the distinction the map exists to make.

#### Adoption

Adoption is graded 1–5 and measures real usage — downloads, active users, and deployments — rather than repository popularity. GitHub stars are treated as a weak last-resort signal and never raise a product above level 3.

The sources differ by product type. For repositories we use GitHub stars, forks, and developer activity; for models and datasets, Hugging Face downloads and likes; for packages, registry download statistics (PyPI via pypistats.org, pepy.tech, and pypi.org, together with npm). Relative usage across models is estimated from OpenRouter's per-model token-share leaderboard. For the large closed consumer surfaces, where first-party usage figures are unavailable, we rely on traffic and monthly-active-user trackers such as Business of Apps and DemandSage.

#### Capability

Capability is graded 1–5 and is method-labeled, so the basis of each grade is explicit. Where a community benchmark exists, the grade rests on it; where none does, it rests on a structured feature grid; and where capability is not a meaningful axis for a product type, the value is left null.

Capability means different things for a model, a tool, and a dataset, so capability grades are comparable *within* a category and not across categories. Benchmark evidence is drawn from Artificial Analysis (its Intelligence Index), LMArena / Chatbot Arena, Epoch AI (including FrontierMath, GPQA Diamond, and SWE-bench), Scale's SEAL leaderboards, Vals AI, LLM-Stats, and the EleutherAI evaluation-harness lineage behind the Open LLM Leaderboard. For specialised categories we use domain benchmarks — for example ANN-Benchmarks and Qdrant's published figures for vector databases, and SWE-bench aggregators for coding agents — and in some cases we return to the original arXiv papers for methodology and reported results.

### Maturity stages

Beyond the per-product scores, every category is assigned a **maturity stage** (0–5) and a **set of gaps**. Both are computed deterministically from the scores of the products in the category and are recomputed on every build, so they never drift from the underlying data.

Each product first receives a single maturity score on a 1–5 scale, a per-category weighted blend of its adoption and capability grades, normalised by the weight sum:

```
score = (w_adopt · adoption + w_cap · capability) / (w_adopt + w_cap)
```

The weights vary by category, because the two axes do not matter equally everywhere: adoption is weighted more heavily for end-user surfaces such as UI & API (0.7 adoption to 0.3 capability), and capability more heavily for the model categories (0.3 to 0.7). The weights for each category sum to one, so the blend is a weighted average on the 1–5 scale. Where capability is not a meaningful axis — for datasets, for instance — the product is graded on adoption alone; and a product with no adoption signal at all receives no maturity score and is excluded from its category's stage, neither advancing nor depressing it. A product is considered **mature** only when its blended score reaches **4.5 of 5** — a deliberately demanding, near-best-on-both-axes bar. Because the map already curates the most prominent products in each category, a lower bar would call almost everything mature.

A central rule governs the count: **only fully open products advance a category's stage.** Open-ish products (open weights, source-available, and the like) are used solely to detect the openness gap described below; crediting them to the ladder would blur the open-source-versus-open-weights line the map is built to expose. The ladder therefore measures the health of the genuinely open ecosystem.

| Stage | Name | Condition |
|------:|------|-----------|
| 5 | Mature Open Ecosystem | four or more mature fully open products: redundant and resilient |
| 4 | Competitive Open Ecosystem | at least one mature fully open product, but fewer than four |
| 3 | Viable Alternatives | no mature fully open product, but the best fully open option is strong (blend at or above 3.5) |
| 2 | Emerging Alternatives | no mature fully open product; the best fully open option is promising but limited (blend from 3.0 to 3.5) |
| 1 | Open Experiments | fully open options exist but are weak on both axes (best blend below 3.0) |
| 0 | Void | no usable open option exists (best blend below 2.0, and nothing is mature anywhere) |

These count and score cutoffs — four mature products for Stage 5, the 4.5 maturity bar, and the 3.5 / 3.0 / 2.0 bands on the best fully open option — are explicit policy parameters, chosen so the ladder discriminates between categories rather than bunching them at one rung, and reviewed when the scoring rubric or the curation density changes materially. Not every category needs to reach Stage 5; redundancy matters more in some parts of the stack than others.

### Gaps

Openness is treated as an axis orthogonal to maturity: a category can hold strong, widely adopted options that are simply not *fully* open. Each category therefore carries a set of zero or more gaps, derived from the same metrics as the stage:

- **Void** — no usable open option exists at all.
- **Capability** — the best fully open option is not capable enough to be useful.
- **Adoption** — a capable fully open option exists but is under-adopted.
- **Maturity** — open options exist, and at least one may be mature, but the ecosystem lacks the depth and redundancy of a mature one: too few mature fully open products.
- **Openness** — capable, adopted options exist, but the mature ones are not fully open. This is the orthogonal flag, and it can co-occur with the others.

A fully mature ecosystem carries no gaps. The set is extensible: further gap types, such as maintenance or bus-factor risk, can be added as the underlying signals become available, without changing the staging logic.

Two illustrations. The base/pretrained-models and fine-tuned/chat-models categories both carry an **openness** gap: capable, well-adopted options exist, but the mature ones are not fully open. The inference-code category, by contrast, has mature, competitive, well-adopted open-source options — vLLM, llama.cpp, SGLang — but few of them; this is a **maturity** gap, signalling an ecosystem that depends on a small number of projects continuing to do well. At present {n_openness_gaps} of the {n_categories} categories carry an openness gap.

### The openness verdict

Each category also reports a coarse verdict summarising which openness tier leads among its **standout** products — those whose blended adoption-by-capability score, weighted by the same per-category weights, reaches 4.0 of 5. This standout bar (4.0) is deliberately looser than the maturity bar (4.5): it admits the strong products whose openness is worth summarising, not only the fully mature ones. A tier *leads* only when it holds a clear plurality of those standouts — a larger share than any other tier by at least ten percentage points; otherwise the category reads *competitive*, or *no standout* where nothing clears the bar. The accompanying count chips always show the full openness mix across every product, so a category that is open in its long tail but closed at the top remains visible.

### Triangulation, provenance, and reproducibility

The design is one of multi-source triangulation. Each axis draws on a different family of evidence — adoption from registries, OpenRouter, and traffic trackers; capability from benchmark leaderboards and papers; openness from primary vendor and repository sources — so no single source determines a product's standing. Every non-null value records what the source showed and the date it was accessed. Across the scored set this amounts to {n_citations} primary citations spanning {n_domains} distinct source domains. Products that could not be verified against a primary source were excluded rather than estimated. The result is intended to be audited and reproduced, not taken on trust.

### Limitations

Several constraints bound the present results and are stated plainly. The scored set is a curated sample of the most prominent products, not a census; the {uncategorized} artifacts in the long tail are tracked by usage signal only and remain ungraded. Composition and "known-build" relationships are curator-asserted from documentation rather than mined from deployment telemetry. Product descriptions, and therefore keyword-based lookup, are English-centric. The openness class-to-spectrum mapping is the analysts' editorial judgment, not a law of nature, and some distinctions collapse in it by design. Finally, as noted above, the raw 0–5 openness and capability scores are within-type grades and should not be compared directly across categories.
