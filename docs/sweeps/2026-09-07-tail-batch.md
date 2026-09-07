# Tail batch — 2026-09-07

Machine-generated review sheet for the weekly candidate sweep (`discover-candidates`). One PR,
label `tail-batch`. Nothing here is scored: every row carries identity and artifacts only.
A human accepts or rejects this batch; automation opened it and does not merge it.

**Fourth revision.** One correction a third review asked for, and it changed the batch rather than
its prose. A review found that the duplicate table classified `mlabonne/llm-datasets` and
`poloclub/llm-landscape` as releases of `llm` with nothing declared to support either fold, and
asked for the 18 `llm` folds to be audited. Auditing the whole class found 300 folds of that shape,
not 18. Every fold in the batch is now re-audited against the repo's own declarations
(**What a fold has to rest on**); the 300 that rested on a folded name match, a shared domain or a
sentence about what a repository is are **un-folded**, held as unique candidates with the reason
each fold was withdrawn, and all five counts are recomputed rather than adjusted:
2579 = 739 + 1840, and 1840 = 67 + 1773. `accepted` is unchanged at 67, because withdrawing a fold
can only ever move a signal to the parked side.

**Third revision.** Two corrections a second review asked for are folded in, and both changed the
batch rather than its prose:

1. **No emitted field is an assignment any more.** Every field on every row below is produced by
   the derivation in **How a field on a row is produced**, from a string in the API response plus
   mappings already declared in this repo. The three product-family folds the second revision made
   by hand (`roberta-base` + `roberta-large` → `roberta`, and the same shape for `t5` and `gpt-2`)
   are **un-folded**: collapsing two checkpoint ids into one product line is an editorial act, so
   it happens when a person promotes the row, not in a machine batch.
2. **No candidate is accepted below a cutoff any more.** The nine sub-floor exceptions the second
   revision accepted "because the sweep recognized them" are parked with the floor that excluded
   them, and the batch is replenished by a second retrieval pass at the *same* cutoffs — 16 more
   queries, predeclared in a manifest before the first request was issued. Recognition is gone as
   an acceptance reason; acceptance is the predicate below and nothing else.

See **Revisions** at the end for all four revisions in one table.

## Window and scope

- **Window swept:** 2026-09-07 (single day). Every fetch in both passes is dated 2026-09-07.
- **Categories swept:** the six the map's own gap arithmetic reads at maturity stage 3 or below —
  `dataset_processing_tools` (stage 2), `edge_hardware`, `safeguards`, `base_pretrained`,
  `finetuned_chat`, `compilers` (all stage 3). Category list and lifecycle status read at run time
  through `build.taxonomy.category_statuses(taxonomy)`; all 18 categories are `published`, so every
  row here is promoted later through `add-product`, not `promote-category`.
- **Categories that emit rows:** five. `edge_hardware` was swept and emits nothing — see
  **`edge_hardware`: swept, nothing emitted**.
- **Not reached:** the warehouse discovery pool (`currentai.entities.repos`). No `OSO_API_KEY` in
  this environment, so the pool was unreachable — reported as a gap, not filled with a guess. It is
  an enrichment and consolidation step, never a rejection step, so its absence does not invalidate
  the dedup below; it does mean multi-signal consolidation rested on self-dedup alone.

## Reconciled counts

| count | value |
|---|---|
| `raw_signals` | 2579 |
| `duplicate_signals` | 739 |
| `unique_candidates` | 1840 |
| `accepted` | 67 |
| `parked` | 1773 |

- `raw_signals = duplicate_signals + unique_candidates` → 2579 = 739 + 1840 ✓
- `unique_candidates = accepted + parked` → 1840 = 67 + 1773 ✓

Three of the five moved in this revision. 300 signals the third revision folded onto a product on
a name match no declaration supports are un-folded: they leave `duplicate_signals` (1039 → 739),
enter `unique_candidates` (1540 → 1840), and are held in `parked` (1473 → 1773) with the reason
each fold was withdrawn. `raw_signals` cannot move — nothing was re-fetched — and `accepted` does
not move, because withdrawing a fold cannot admit a row. See **What a fold has to rest on**.

One raw signal is one (query, item) occurrence — the grain the two equations are written at, and
the same grain the second revision used. 2579 occurrences came back from 62 queries (46 in the first pass, 16 in the second). A repository returned by
three queries is three raw signals, two of which resolve as duplicates of the first; a signal's
cutoff status, by contrast, is a property of the signal and not of the occurrence — it is inside
the cutoff when it clears the floor of any query that returned it.

Each accepted signal maps to exactly one emitted row: 67 accepted, 67 rows. All
1773 parked candidates are listed individually below — 288 with a reason of their own, 1185 with
the retrieval floor that excluded them, and 300 with the fold this revision withdrew — and all
739 remaining duplicates are listed with the declaration each one rests on.

Where the rows come from, against the second revision: 43 of the 67 were emitted then too (their
identity fields are re-derived, so 36 of those 43 changed a slug, a display_name or an org), 22
are new candidates from the second retrieval pass, and 2 are checkpoints the second revision
folded into a product line by hand (`google-t5/t5-base`, `openai-community/gpt2-large`; the third,
`FacebookAI/roberta-large`, is also returned by a second-pass query). Nine rows the second
revision emitted below a floor are gone.

## How a candidate becomes a row

Acceptance is a predicate over observations. It has no free parameters and no step at which the
sweep decides a product deserves to be in:

```
accepted(signal) :=
      in_cutoff(signal)                  # clears the predeclared floor of some query that returned it
  and survived_dedup(signal)             # steps 1-6 of discover-candidates, in that order
  and derivable_category(signal)         # a declared query category, or the declared-metadata rule
  and addressable_identifier(signal)     # github / huggingface_model - never a URL
  and no_recorded_park_reason(signal)
```

The last clause is the only place a human-style judgment can enter, and it can only ever *remove*
a candidate: a boundary call, a category-fit call, an ambiguity. Every such call is a row in
**Parked — individually reasoned** with the boundary it names. Nothing in this batch was admitted
by an argument, and the words "recognized", "widely used" and "notable" appear nowhere in the
acceptance path.

## How a field on a row is produced

| field | derivation |
|---|---|
| `slug` | `slugify(declared name)`. If that string is a head slug, a retired alias, an existing registry slug or another row in this batch, `slugify(declared owner)-slugify(declared name)` instead. A row colliding after the fallback is parked, never renamed by hand. |
| `display_name` | the declared name, verbatim. |
| `org` | the organization `sources/org_handles.yaml` already declares for that `(platform, owner login)`; where no handle is declared, `slugify(declared owner login)`. |
| `type` | `software` for a GitHub repository signal, `model` for a Hugging Face model repository signal. |
| `category` | the category declared for the query that returned the signal (GitHub), or the category the declared-metadata rule names (Hugging Face). |
| artifacts | the identifier from the API response, plus the repository's declared `homepage` where it declares one. |

`slugify` is `[^a-z0-9]+ → -` over the lowercased string, with runs collapsed and edges trimmed.

**What this deliberately does not do.** It does not fold two checkpoint ids into a product line,
and it does not map an owner login onto an organization the repo has not already declared a handle
for. Both were done by hand in the second revision — `answerdotai` → `answer-ai`,
`bespokelabsai` → `bespoke-labs`, `data-prep-kit` → `ibm`, `roberta-base` + `roberta-large` →
`roberta` — and neither is reproducible from an observation. The consequence is visible and
intended: this batch proposes `roberta-base` and `roberta-large` as two rows, and
`org: answerdotai` rather than `org: answer-ai`. Collapsing them is the editorial act
`docs/reference/identity.md` describes ("pitch the slug at the level the vendor markets as the
product") and `build/validate.py` enforces on *head* model products, and it belongs to the person
who promotes the row through `add-product` — where a `model_families.yaml` pattern or a
`version_in_identity` declaration records the decision. See **Escalations for a person**.

## Category from a declared mapping

A GitHub signal takes the category declared for its query, before the query ran:

| query | declared category | pass |
|---|---|---|
| `B_comp_engine` | `compilers` | second |
| `B_comp_modelopt` | `compilers` | second |
| `B_comp_tensorrt` | `compilers` | second |
| `B_comp_tvm` | `compilers` | second |
| `B_dpt_augment` | `dataset_processing_tools` | second |
| `B_dpt_datasetllm` | `dataset_processing_tools` | second |
| `B_dpt_ocrpdf` | `dataset_processing_tools` | second |
| `B_dpt_tokenizer` | `dataset_processing_tools` | second |
| `B_safe_agentsec` | `safeguards` | second |
| `B_safe_aisec` | `safeguards` | second |
| `B_safe_llmsafety` | `safeguards` | second |
| `B_safe_pii` | `safeguards` | second |
| `comp_q_convert` | `compilers` | first |
| `comp_q_kernel` | `compilers` | first |
| `comp_t_cuda` | `compilers` | first |
| `comp_t_mlir` | `compilers` | first |
| `comp_t_onnx` | `compilers` | first |
| `comp_t_quant` | `compilers` | first |
| `comp_t_tensorcompiler` | `compilers` | first |
| `comp_t_triton` | `compilers` | first |
| `dpt_crawl` | `dataset_processing_tools` | first |
| `dpt_dedup` | `dataset_processing_tools` | first |
| `dpt_docparse` | `dataset_processing_tools` | first |
| `dpt_pipeline` | `dataset_processing_tools` | first |
| `dpt_q_curator` | `dataset_processing_tools` | first |
| `dpt_q_dedup` | `dataset_processing_tools` | first |
| `dpt_q_pdf` | `dataset_processing_tools` | first |
| `dpt_quality` | `dataset_processing_tools` | first |
| `dpt_synth` | `dataset_processing_tools` | first |
| `dpt_t_datacentric` | `dataset_processing_tools` | first |
| `dpt_t_dataquality` | `dataset_processing_tools` | first |
| `dpt_t_dedup` | `dataset_processing_tools` | first |
| `dpt_t_synthetic` | `dataset_processing_tools` | first |
| `dpt_t_webscraping` | `dataset_processing_tools` | first |
| `edge_q_accel` | `edge_hardware` | first |
| `edge_t_edgeai` | `edge_hardware` | first |
| `edge_t_npu` | `edge_hardware` | first |
| `edge_t_openhw` | `edge_hardware` | first |
| `edge_t_riscv_ai` | `edge_hardware` | first |
| `edge_t_sbc` | `edge_hardware` | first |
| `safe_q_guardrail` | `safeguards` | first |
| `safe_q_jailbreak` | `safeguards` | first |
| `safe_t_aisafety` | `safeguards` | first |
| `safe_t_guardrails` | `safeguards` | first |
| `safe_t_llmsecurity` | `safeguards` | first |
| `safe_t_moderation` | `safeguards` | first |
| `safe_t_promptinjection` | `safeguards` | first |
| `safe_t_redteam` | `safeguards` | first |

A Hugging Face ranked listing declares no category, so the category comes from the model's own
declared metadata. The whole rule, in three clauses:

| rule | condition on the model's declared metadata | category |
|---|---|---|
| **M1** | declared tag `conversational`, and declared `pipeline_tag` is `text-generation` or absent | `finetuned_chat` |
| **M2** | no `conversational` tag, and declared `pipeline_tag` ∈ {`text-generation`, `fill-mask`, `translation`} | `base_pretrained` |
| **M3** | returned by a category-scoped query (`hf_guard_search`, `hf_safety_search`, `hf_moderation_search`), and declared `pipeline_tag` ∈ {`text-classification`, `zero-shot-classification`, `token-classification`, absent} | that query's declared category (`safeguards`) |
| — | anything else | **no derivable category → parked** |

M1's `pipeline_tag` clause is new in this revision and it only ever parks: it stops a model that
declares `conversational` alongside `image-text-to-text` (an OCR or vision-language model) from
being routed into `finetuned_chat` by a rule that was written for chat models. Two candidates move
to the parked side because of it (`datalab-to/chandra-ocr-2`, `llava-hf/llava-1.5-7b-hf`), and no
candidate is admitted by it.

## Retrieval cutoffs, predeclared and disclosed

Two passes, one set of cutoffs. The second pass exists because removing the nine sub-floor
exceptions left the batch under the review budget, and the workflow's remedy for that is to
retrieve more, never to lower a bound:

| source | cutoff | applies to |
|---|---|---|
| GitHub repository search | ≥ 1,000 all-time stars **and** a push since 2025-09-07; sorted by stars, top 30 per query | every GitHub query in both passes |
| Hugging Face, ranked listing (`filter=`/`sort=` over a tag) | ≥ 1,000,000 trailing-30-day downloads; top 100 per query | `hf_textgen_*`, `hf_all_*`, `hf_base_search`, `hf_instruct_search`, and all four second-pass listings |
| Hugging Face, category-scoped keyword search (`search=`) | ≥ 5,000 trailing-30-day downloads; top 100 per query | `hf_guard_search`, `hf_safety_search`, `hf_moderation_search` |

The second pass was written down before it ran. The manifest fixes each query, its declared
category, its floor, its sort and its depth:

```json
{
  "cutoffs": {
    "github": "all-time stars >= 1000 AND pushed_at >= 2025-09-07; sort=stars, order=desc, per_page=30 (identical to pass A)",
    "huggingface_category_scoped": "trailing-30-day downloads >= 5000; sort as declared per query, limit=100 (the floor pass A used for its three category-scoped searches)",
    "huggingface_general_ranked": "trailing-30-day downloads >= 1000000 (pass A's floor for unscoped/text-generation ranked listings). No pass-B query is of this kind."
  },
  "github_queries": {
    "B_dpt_augment": {
      "category": "dataset_processing_tools",
      "q": "topic:data-augmentation"
    },
    "B_dpt_ocrpdf": {
      "category": "dataset_processing_tools",
      "q": "topic:ocr topic:pdf"
    },
    "B_dpt_datasetllm": {
      "category": "dataset_processing_tools",
      "q": "topic:dataset topic:llm"
    },
    "B_dpt_tokenizer": {
      "category": "dataset_processing_tools",
      "q": "topic:tokenizer"
    },
    "B_safe_aisec": {
      "category": "safeguards",
      "q": "topic:ai-security"
    },
    "B_safe_pii": {
      "category": "safeguards",
      "q": "topic:pii"
    },
    "B_safe_llmsafety": {
      "category": "safeguards",
      "q": "topic:llm-safety"
    },
    "B_safe_agentsec": {
      "category": "safeguards",
      "q": "topic:agent-security"
    },
    "B_comp_engine": {
      "category": "compilers",
      "q": "topic:inference-engine"
    },
    "B_comp_tvm": {
      "category": "compilers",
      "q": "topic:tvm"
    },
    "B_comp_tensorrt": {
      "category": "compilers",
      "q": "topic:tensorrt"
    },
    "B_comp_modelopt": {
      "category": "compilers",
      "q": "topic:model-optimization"
    }
  },
  "hf_queries": {
    "B_hf_fillmask_dl": {
      "scope": "declared pipeline_tag fill-mask (rule M2 -> base_pretrained)",
      "url": "https://huggingface.co/api/models?filter=fill-mask&sort=downloads&direction=-1&limit=100",
      "floor": 1000000,
      "floor_note": "corrected from 5000 to 1000000; see floor_correction"
    },
    "B_hf_fillmask_likes": {
      "scope": "declared pipeline_tag fill-mask (rule M2 -> base_pretrained)",
      "url": "https://huggingface.co/api/models?filter=fill-mask&sort=likes&direction=-1&limit=100",
      "floor": 1000000,
      "floor_note": "corrected from 5000 to 1000000; see floor_correction"
    },
    "B_hf_conv_dl": {
      "scope": "declared tag conversational (rule M1 -> finetuned_chat)",
      "url": "https://huggingface.co/api/models?filter=conversational&sort=downloads&direction=-1&limit=100",
      "floor": 1000000,
      "floor_note": "corrected from 5000 to 1000000; see floor_correction"
    },
    "B_hf_conv_likes": {
      "scope": "declared tag conversational (rule M1 -> finetuned_chat)",
      "url": "https://huggingface.co/api/models?filter=conversational&sort=likes&direction=-1&limit=100",
      "floor": 1000000,
      "floor_note": "corrected from 5000 to 1000000; see floor_correction"
    }
  }
}
```

**One correction to that manifest, disclosed because it is a correction and not a discovery.** The
manifest first gave the four second-pass Hugging Face queries the 5,000-download floor. That is
the wrong half of the first pass's convention: all four are `filter=`-based ranked listings over a
declared tag, the same shape as the first pass's `filter=text-generation` listings, and the first
pass gave that shape the 1,000,000 floor — the 5,000 floor belongs to `search=` keyword queries
scoped to a category. The batch applies 1,000,000. The correction only tightens: every signal it
excludes was inside the floor the manifest first declared, and nothing it admits was outside it.
At 5,000 the second pass would have proposed 247 rows, most of them research checkpoints
(`julien-c/dummy-unknown`, `facebook/esm2_t6_8M_UR50D`, dozens of language-specific BERT
fine-tunes) that no mechanical rule separates from a vendor's base model — which is the reason a
floor, not a reading, has to do that work.

## Sources swept

| query | pass | source | returned | declared category | cutoff |
|---|---|---|---|---|---|
| `comp_q_convert` | first | https://api.github.com/search/repositories?q=model%20converter%20quantize%20deploy&sort=stars&order=desc&per_page=30 | 0 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `comp_q_kernel` | first | https://api.github.com/search/repositories?q=attention%20kernel%20gpu%20inference&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `comp_t_cuda` | first | https://api.github.com/search/repositories?q=topic%3Acuda%20topic%3Akernel&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `comp_t_mlir` | first | https://api.github.com/search/repositories?q=topic%3Amlir&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `comp_t_onnx` | first | https://api.github.com/search/repositories?q=topic%3Aonnx&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `comp_t_quant` | first | https://api.github.com/search/repositories?q=topic%3Aquantization&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `comp_t_tensorcompiler` | first | https://api.github.com/search/repositories?q=topic%3Acompiler%20topic%3Adeep-learning&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `comp_t_triton` | first | https://api.github.com/search/repositories?q=topic%3Atriton&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_crawl` | first | https://api.github.com/search/repositories?q=web%20crawl%20text%20extraction%20pipeline&sort=stars&order=desc&per_page=30 | 4 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_dedup` | first | https://api.github.com/search/repositories?q=dataset%20deduplication%20llm%20training%20data&sort=stars&order=desc&per_page=30 | 7 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_docparse` | first | https://api.github.com/search/repositories?q=document%20parsing%20ocr%20pipeline%20llm%20dataset&sort=stars&order=desc&per_page=30 | 1 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_pipeline` | first | https://api.github.com/search/repositories?q=training%20corpus%20curation%20pipeline%20llm&sort=stars&order=desc&per_page=30 | 2 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_q_curator` | first | https://api.github.com/search/repositories?q=data%20curator%20llm&sort=stars&order=desc&per_page=30 | 22 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_q_dedup` | first | https://api.github.com/search/repositories?q=deduplication%20minhash%20corpus&sort=stars&order=desc&per_page=30 | 6 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_q_pdf` | first | https://api.github.com/search/repositories?q=pdf%20to%20markdown%20llm&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_quality` | first | https://api.github.com/search/repositories?q=data%20filtering%20quality%20corpus%20nlp&sort=stars&order=desc&per_page=30 | 1 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_synth` | first | https://api.github.com/search/repositories?q=synthetic%20data%20generation%20llm&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_t_datacentric` | first | https://api.github.com/search/repositories?q=topic%3Adata-curation&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_t_dataquality` | first | https://api.github.com/search/repositories?q=topic%3Adata-quality%20topic%3Amachine-learning&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_t_dedup` | first | https://api.github.com/search/repositories?q=topic%3Adeduplication&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_t_synthetic` | first | https://api.github.com/search/repositories?q=topic%3Asynthetic-data&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `dpt_t_webscraping` | first | https://api.github.com/search/repositories?q=topic%3Aweb-crawler%20topic%3Allm&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `edge_q_accel` | first | https://api.github.com/search/repositories?q=npu%20accelerator%20board%20inference&sort=stars&order=desc&per_page=30 | 0 | edge_hardware | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `edge_t_edgeai` | first | https://api.github.com/search/repositories?q=topic%3Aedge-ai&sort=stars&order=desc&per_page=30 | 30 | edge_hardware | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `edge_t_npu` | first | https://api.github.com/search/repositories?q=topic%3Anpu&sort=stars&order=desc&per_page=30 | 30 | edge_hardware | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `edge_t_openhw` | first | https://api.github.com/search/repositories?q=topic%3Aopen-source-hardware%20topic%3Aai&sort=stars&order=desc&per_page=30 | 6 | edge_hardware | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `edge_t_riscv_ai` | first | https://api.github.com/search/repositories?q=topic%3Arisc-v%20topic%3Aaccelerator&sort=stars&order=desc&per_page=30 | 10 | edge_hardware | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `edge_t_sbc` | first | https://api.github.com/search/repositories?q=topic%3Asingle-board-computer&sort=stars&order=desc&per_page=30 | 30 | edge_hardware | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `safe_q_guardrail` | first | https://api.github.com/search/repositories?q=guardrail%20model%20safety%20classifier&sort=stars&order=desc&per_page=30 | 5 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `safe_q_jailbreak` | first | https://api.github.com/search/repositories?q=jailbreak%20detection%20llm&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `safe_t_aisafety` | first | https://api.github.com/search/repositories?q=topic%3Aai-safety&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `safe_t_guardrails` | first | https://api.github.com/search/repositories?q=topic%3Aguardrails&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `safe_t_llmsecurity` | first | https://api.github.com/search/repositories?q=topic%3Allm-security&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `safe_t_moderation` | first | https://api.github.com/search/repositories?q=topic%3Acontent-moderation&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `safe_t_promptinjection` | first | https://api.github.com/search/repositories?q=topic%3Aprompt-injection&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `safe_t_redteam` | first | https://api.github.com/search/repositories?q=topic%3Ared-teaming&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_comp_engine` | second | https://api.github.com/search/repositories?q=topic%3Ainference-engine&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_comp_modelopt` | second | https://api.github.com/search/repositories?q=topic%3Amodel-optimization&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_comp_tensorrt` | second | https://api.github.com/search/repositories?q=topic%3Atensorrt&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_comp_tvm` | second | https://api.github.com/search/repositories?q=topic%3Atvm&sort=stars&order=desc&per_page=30 | 30 | compilers | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_dpt_augment` | second | https://api.github.com/search/repositories?q=topic%3Adata-augmentation&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_dpt_datasetllm` | second | https://api.github.com/search/repositories?q=topic%3Adataset%20topic%3Allm&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_dpt_ocrpdf` | second | https://api.github.com/search/repositories?q=topic%3Aocr%20topic%3Apdf&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_dpt_tokenizer` | second | https://api.github.com/search/repositories?q=topic%3Atokenizer&sort=stars&order=desc&per_page=30 | 30 | dataset_processing_tools | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_safe_agentsec` | second | https://api.github.com/search/repositories?q=topic%3Aagent-security&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_safe_aisec` | second | https://api.github.com/search/repositories?q=topic%3Aai-security&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_safe_llmsafety` | second | https://api.github.com/search/repositories?q=topic%3Allm-safety&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `B_safe_pii` | second | https://api.github.com/search/repositories?q=topic%3Apii&sort=stars&order=desc&per_page=30 | 30 | safeguards | 1,000 stars and a push since 2025-09-07, top 30 by stars |
| `hf_all_downloads` | first | https://huggingface.co/api/models?sort=downloads&direction=-1&limit=100 | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `hf_all_trending` | first | https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=100 | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `hf_base_search` | first | https://huggingface.co/api/models?search=base&sort=downloads&direction=-1&limit=100&filter=text-generation | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `hf_guard_search` | first | https://huggingface.co/api/models?search=guard&sort=downloads&direction=-1&limit=100 | 100 | safeguards | 5,000 trailing-30-day downloads, top 100 (category-scoped search) |
| `hf_instruct_search` | first | https://huggingface.co/api/models?search=instruct&sort=downloads&direction=-1&limit=100&filter=text-generation | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `hf_moderation_search` | first | https://huggingface.co/api/models?search=moderation&sort=downloads&direction=-1&limit=100 | 100 | safeguards | 5,000 trailing-30-day downloads, top 100 (category-scoped search) |
| `hf_safety_search` | first | https://huggingface.co/api/models?search=safety&sort=downloads&direction=-1&limit=100 | 100 | safeguards | 5,000 trailing-30-day downloads, top 100 (category-scoped search) |
| `hf_textgen_downloads` | first | https://huggingface.co/api/models?sort=downloads&direction=-1&limit=100&filter=text-generation | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `hf_textgen_likes` | first | https://huggingface.co/api/models?sort=likes&direction=-1&limit=100&filter=text-generation | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `hf_textgen_trending` | first | https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=100&filter=text-generation | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `B_hf_conv_dl` | second | https://huggingface.co/api/models?filter=conversational&sort=downloads&direction=-1&limit=100 | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `B_hf_conv_likes` | second | https://huggingface.co/api/models?filter=conversational&sort=likes&direction=-1&limit=100 | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `B_hf_fillmask_dl` | second | https://huggingface.co/api/models?filter=fill-mask&sort=downloads&direction=-1&limit=100 | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |
| `B_hf_fillmask_likes` | second | https://huggingface.co/api/models?filter=fill-mask&sort=likes&direction=-1&limit=100 | 100 | — (declared metadata) | 1,000,000 trailing-30-day downloads, top 100 |

## Accepted — 67 rows

Every row, with the signal behind it, the source URL, the fetch date, and the derivation of every
field on it. `homepage` appears only as a second artifact on a row that already carries an
identifier, and it is the repository's own declared homepage.

### `base_pretrained` — 25 rows

| slug | display_name | type | org | artifacts | signal | source URL |
|---|---|---|---|---|---|---|
| `bert-base-cased` | bert-base-cased | model | `google-bert` | `huggingface_model: google-bert/bert-base-cased` | `google-bert/bert-base-cased` | https://huggingface.co/google-bert/bert-base-cased |
| `bert-base-multilingual-cased` | bert-base-multilingual-cased | model | `google-bert` | `huggingface_model: google-bert/bert-base-multilingual-cased` | `google-bert/bert-base-multilingual-cased` | https://huggingface.co/google-bert/bert-base-multilingual-cased |
| `bert-base-multilingual-uncased` | bert-base-multilingual-uncased | model | `google-bert` | `huggingface_model: google-bert/bert-base-multilingual-uncased` | `google-bert/bert-base-multilingual-uncased` | https://huggingface.co/google-bert/bert-base-multilingual-uncased |
| `bert-base-uncased` | bert-base-uncased | model | `google-bert` | `huggingface_model: google-bert/bert-base-uncased` | `google-bert/bert-base-uncased` | https://huggingface.co/google-bert/bert-base-uncased |
| `bert-large-portuguese-cased` | bert-large-portuguese-cased | model | `neuralmind` | `huggingface_model: neuralmind/bert-large-portuguese-cased` | `neuralmind/bert-large-portuguese-cased` | https://huggingface.co/neuralmind/bert-large-portuguese-cased |
| `bio-clinicalbert` | Bio_ClinicalBERT | model | `emilyalsentzer` | `huggingface_model: emilyalsentzer/Bio_ClinicalBERT` | `emilyalsentzer/Bio_ClinicalBERT` | https://huggingface.co/emilyalsentzer/Bio_ClinicalBERT |
| `biomednlp-biomedbert-base-uncased-abstract` | BiomedNLP-BiomedBERT-base-uncased-abstract | model | `microsoft` | `huggingface_model: microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract` | `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract` | https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract |
| `deberta-v3-base` | deberta-v3-base | model | `microsoft` | `huggingface_model: microsoft/deberta-v3-base` | `microsoft/deberta-v3-base` | https://huggingface.co/microsoft/deberta-v3-base |
| `deberta-v3-large` | deberta-v3-large | model | `microsoft` | `huggingface_model: microsoft/deberta-v3-large` | `microsoft/deberta-v3-large` | https://huggingface.co/microsoft/deberta-v3-large |
| `distilbert-base-uncased` | distilbert-base-uncased | model | `distilbert` | `huggingface_model: distilbert/distilbert-base-uncased` | `distilbert/distilbert-base-uncased` | https://huggingface.co/distilbert/distilbert-base-uncased |
| `distilroberta-base` | distilroberta-base | model | `distilbert` | `huggingface_model: distilbert/distilroberta-base` | `distilbert/distilroberta-base` | https://huggingface.co/distilbert/distilroberta-base |
| `gpt2` | gpt2 | model | `openai-community` | `huggingface_model: openai-community/gpt2` | `openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 |
| `gpt2-large` | gpt2-large | model | `openai-community` | `huggingface_model: openai-community/gpt2-large` | `openai-community/gpt2-large` | https://huggingface.co/openai-community/gpt2-large |
| `mdeberta-v3-base` | mdeberta-v3-base | model | `microsoft` | `huggingface_model: microsoft/mdeberta-v3-base` | `microsoft/mdeberta-v3-base` | https://huggingface.co/microsoft/mdeberta-v3-base |
| `modernbert-base` | ModernBERT-base | model | `answerdotai` | `huggingface_model: answerdotai/ModernBERT-base` | `answerdotai/ModernBERT-base` | https://huggingface.co/answerdotai/ModernBERT-base |
| `modernbert-large` | ModernBERT-large | model | `answerdotai` | `huggingface_model: answerdotai/ModernBERT-large` | `answerdotai/ModernBERT-large` | https://huggingface.co/answerdotai/ModernBERT-large |
| `openelm-1-1b-instruct` | OpenELM-1_1B-Instruct | model | `apple` | `huggingface_model: apple/OpenELM-1_1B-Instruct` | `apple/OpenELM-1_1B-Instruct` | https://huggingface.co/apple/OpenELM-1_1B-Instruct |
| `opt-125m` | opt-125m | model | `facebook` | `huggingface_model: facebook/opt-125m` | `facebook/opt-125m` | https://huggingface.co/facebook/opt-125m |
| `powermoe-3b` | PowerMoE-3b | model | `ibm-research` | `huggingface_model: ibm-research/PowerMoE-3b` | `ibm-research/PowerMoE-3b` | https://huggingface.co/ibm-research/PowerMoE-3b |
| `roberta-base` | roberta-base | model | `facebookai` | `huggingface_model: FacebookAI/roberta-base` | `FacebookAI/roberta-base` | https://huggingface.co/FacebookAI/roberta-base |
| `roberta-large` | roberta-large | model | `facebookai` | `huggingface_model: FacebookAI/roberta-large` | `FacebookAI/roberta-large` | https://huggingface.co/FacebookAI/roberta-large |
| `t5-base` | t5-base | model | `google-t5` | `huggingface_model: google-t5/t5-base` | `google-t5/t5-base` | https://huggingface.co/google-t5/t5-base |
| `t5-small` | t5-small | model | `google-t5` | `huggingface_model: google-t5/t5-small` | `google-t5/t5-small` | https://huggingface.co/google-t5/t5-small |
| `xlm-roberta-base` | xlm-roberta-base | model | `facebookai` | `huggingface_model: FacebookAI/xlm-roberta-base` | `FacebookAI/xlm-roberta-base` | https://huggingface.co/FacebookAI/xlm-roberta-base |
| `xlm-roberta-large` | xlm-roberta-large | model | `facebookai` | `huggingface_model: FacebookAI/xlm-roberta-large` | `FacebookAI/xlm-roberta-large` | https://huggingface.co/FacebookAI/xlm-roberta-large |

Field derivation:

| slug | category from | slug from | display_name from | org from |
|---|---|---|---|---|
| `bert-base-cased` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `bert-base-multilingual-cased` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `bert-base-multilingual-uncased` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `bert-base-uncased` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `bert-large-portuguese-cased` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `bio-clinicalbert` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `biomednlp-biomedbert-base-uncased-abstract` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | declared handle `huggingface:microsoft` -> `microsoft` (sources/org_handles.yaml) |
| `deberta-v3-base` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | declared handle `huggingface:microsoft` -> `microsoft` (sources/org_handles.yaml) |
| `deberta-v3-large` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | declared handle `huggingface:microsoft` -> `microsoft` (sources/org_handles.yaml) |
| `distilbert-base-uncased` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `distilroberta-base` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `gpt2` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `gpt2-large` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `mdeberta-v3-base` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | declared handle `huggingface:microsoft` -> `microsoft` (sources/org_handles.yaml) |
| `modernbert-base` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `modernbert-large` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `openelm-1-1b-instruct` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `opt-125m` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `powermoe-3b` | rule **M2** (declared pipeline_tag `text-generation`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `roberta-base` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `roberta-large` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `t5-base` | rule **M2** (declared pipeline_tag `translation`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `t5-small` | rule **M2** (declared pipeline_tag `translation`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `xlm-roberta-base` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `xlm-roberta-large` | rule **M2** (declared pipeline_tag `fill-mask`, no `conversational` tag) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |

### `compilers` — 8 rows

| slug | display_name | type | org | artifacts | signal | source URL |
|---|---|---|---|---|---|---|
| `autokernel` | autokernel | software | `rightnow-ai` | `github: RightNow-AI/autokernel`; `homepage: https://www.rightnowai.co/forge` | `RightNow-AI/autokernel` | https://github.com/RightNow-AI/autokernel |
| `flaggems` | FlagGems | software | `flagos-ai` | `github: flagos-ai/FlagGems` | `flagos-ai/FlagGems` | https://github.com/flagos-ai/FlagGems |
| `intel-extension-for-pytorch` | intel-extension-for-pytorch | software | `intel` | `github: intel/intel-extension-for-pytorch` | `intel/intel-extension-for-pytorch` | https://github.com/intel/intel-extension-for-pytorch |
| `kernl` | kernl | software | `els-rd` | `github: ELS-RD/kernl`; `homepage: http://www.kernl.ai` | `ELS-RD/kernl` | https://github.com/ELS-RD/kernl |
| `nunchaku` | nunchaku | software | `nunchux-ai` | `github: nunchux-ai/nunchaku` | `nunchux-ai/nunchaku` | https://github.com/nunchux-ai/nunchaku |
| `onediff` | onediff | software | `siliconflow` | `github: siliconflow/onediff`; `homepage: https://github.com/siliconflow/onediff/wiki` | `siliconflow/onediff` | https://github.com/siliconflow/onediff |
| `pytorch-xla` | xla | software | `pytorch` | `github: pytorch/xla`; `homepage: https://pytorch.org/xla` | `pytorch/xla` | https://github.com/pytorch/xla |
| `torch-mlir` | torch-mlir | software | `llvm` | `github: llvm/torch-mlir` | `llvm/torch-mlir` | https://github.com/llvm/torch-mlir |

Field derivation:

| slug | category from | slug from | display_name from | org from |
|---|---|---|---|---|
| `autokernel` | query `comp_t_triton`, declared category `compilers` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `flaggems` | query `comp_t_triton`, declared category `compilers` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `intel-extension-for-pytorch` | query `comp_t_quant`, declared category `compilers` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `kernl` | query `comp_t_triton`, declared category `compilers` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `nunchaku` | query `comp_t_quant`, declared category `compilers` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `onediff` | query `B_comp_engine`, declared category `compilers` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `pytorch-xla` | query `comp_t_tensorcompiler`, declared category `compilers` | slugify(declared owner)-slugify(declared name); `xla` is taken | declared name, verbatim | slugify(declared owner login) |
| `torch-mlir` | query `comp_t_mlir`, declared category `compilers` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |

### `dataset_processing_tools` — 15 rows

| slug | display_name | type | org | artifacts | signal | source URL |
|---|---|---|---|---|---|---|
| `ade-cli` | ade-cli | software | `landing-ai` | `github: landing-ai/ade-cli`; `homepage: https://docs.landing.ai/ade/ade-overview` | `landing-ai/ade-cli` | https://github.com/landing-ai/ade-cli |
| `aisheets` | aisheets | software | `hugging-face` | `github: huggingface/aisheets`; `homepage: https://huggingface.co/spaces/aisheets/sheets` | `huggingface/aisheets` | https://github.com/huggingface/aisheets |
| `curator` | curator | software | `bespokelabsai` | `github: bespokelabsai/curator`; `homepage: https://docs.bespokelabs.ai/bespoke-curator` | `bespokelabsai/curator` | https://github.com/bespokelabsai/curator |
| `easy-dataset` | easy-dataset | software | `conardli` | `github: ConardLi/easy-dataset`; `homepage: https://docs.easy-dataset.com` | `ConardLi/easy-dataset` | https://github.com/ConardLi/easy-dataset |
| `gigatoken` | gigatoken | software | `marcelroed` | `github: marcelroed/gigatoken` | `marcelroed/gigatoken` | https://github.com/marcelroed/gigatoken |
| `graphgen` | GraphGen | software | `internscience` | `github: InternScience/GraphGen`; `homepage: https://chenzihong.gitbook.io/graphgen-cookbook/` | `InternScience/GraphGen` | https://github.com/InternScience/GraphGen |
| `markpdfdown` | markpdfdown | software | `markpdfdown` | `github: MarkPDFdown/markpdfdown` | `MarkPDFdown/markpdfdown` | https://github.com/MarkPDFdown/markpdfdown |
| `parsr` | Parsr | software | `axa-group` | `github: axa-group/Parsr` | `axa-group/Parsr` | https://github.com/axa-group/Parsr |
| `pdf-craft` | pdf-craft | software | `oomol-lab` | `github: oomol-lab/pdf-craft`; `homepage: https://pdf.oomol.com` | `oomol-lab/pdf-craft` | https://github.com/oomol-lab/pdf-craft |
| `pymupdf` | PyMuPDF | software | `pymupdf` | `github: pymupdf/PyMuPDF`; `homepage: https://pymupdf.readthedocs.io/?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=about&utm_term=docs` | `pymupdf/PyMuPDF` | https://github.com/pymupdf/PyMuPDF |
| `snorkel` | snorkel | software | `snorkel-team` | `github: snorkel-team/snorkel`; `homepage: https://snorkel.org` | `snorkel-team/snorkel` | https://github.com/snorkel-team/snorkel |
| `synthetic-data-kit` | synthetic-data-kit | software | `meta-llama` | `github: meta-llama/synthetic-data-kit`; `homepage: https://pypi.org/project/synthetic-data-kit/` | `meta-llama/synthetic-data-kit` | https://github.com/meta-llama/synthetic-data-kit |
| `text-extract-api` | text-extract-api | software | `catchthetornado` | `github: CatchTheTornado/text-extract-api`; `homepage: https://demo.doctractor.com` | `CatchTheTornado/text-extract-api` | https://github.com/CatchTheTornado/text-extract-api |
| `unstructured` | unstructured | software | `unstructured-io` | `github: Unstructured-IO/unstructured`; `homepage: https://www.unstructured.io/` | `Unstructured-IO/unstructured` | https://github.com/Unstructured-IO/unstructured |
| `webclaw` | webclaw | software | `0xmassi` | `github: 0xMassi/webclaw`; `homepage: https://webclaw.io` | `0xMassi/webclaw` | https://github.com/0xMassi/webclaw |

Field derivation:

| slug | category from | slug from | display_name from | org from |
|---|---|---|---|---|
| `ade-cli` | query `B_dpt_ocrpdf`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `aisheets` | query `dpt_t_synthetic`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | declared handle `github:huggingface` -> `hugging-face` (sources/org_handles.yaml) |
| `curator` | query `dpt_t_synthetic`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `easy-dataset` | query `B_dpt_datasetllm`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `gigatoken` | query `B_dpt_tokenizer`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `graphgen` | query `dpt_synth`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `markpdfdown` | query `dpt_q_pdf`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `parsr` | query `B_dpt_ocrpdf`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `pdf-craft` | query `B_dpt_ocrpdf`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `pymupdf` | query `B_dpt_ocrpdf`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `snorkel` | query `B_dpt_augment`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `synthetic-data-kit` | query `dpt_synth`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `text-extract-api` | query `dpt_q_pdf`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `unstructured` | query `B_dpt_ocrpdf`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `webclaw` | query `dpt_t_webscraping`, declared category `dataset_processing_tools` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |

### `finetuned_chat` — 1 row

| slug | display_name | type | org | artifacts | signal | source URL |
|---|---|---|---|---|---|---|
| `dolphin-2-9-1-yi-1-5-34b` | dolphin-2.9.1-yi-1.5-34b | model | `dphn` | `huggingface_model: dphn/dolphin-2.9.1-yi-1.5-34b` | `dphn/dolphin-2.9.1-yi-1.5-34b` | https://huggingface.co/dphn/dolphin-2.9.1-yi-1.5-34b |

Field derivation:

| slug | category from | slug from | display_name from | org from |
|---|---|---|---|---|
| `dolphin-2-9-1-yi-1-5-34b` | rule **M1** (declared tag `conversational`, declared pipeline_tag `text-generation`) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |

### `safeguards` — 18 rows

| slug | display_name | type | org | artifacts | signal | source URL |
|---|---|---|---|---|---|---|
| `agent-governance-toolkit` | agent-governance-toolkit | software | `microsoft` | `github: microsoft/agent-governance-toolkit` | `microsoft/agent-governance-toolkit` | https://github.com/microsoft/agent-governance-toolkit |
| `agentic-radar` | agentic-radar | software | `splx-ai` | `github: splx-ai/agentic-radar`; `homepage: https://splx.ai` | `splx-ai/agentic-radar` | https://github.com/splx-ai/agentic-radar |
| `agentic-security` | agentic_security | software | `msoedov` | `github: msoedov/agentic_security`; `homepage: https://agentic-security.vercel.app` | `msoedov/agentic_security` | https://github.com/msoedov/agentic_security |
| `ai-infra-guard` | AI-Infra-Guard | software | `tencent` | `github: Tencent/AI-Infra-Guard`; `homepage: https://tencent.github.io/AI-Infra-Guard/` | `Tencent/AI-Infra-Guard` | https://github.com/Tencent/AI-Infra-Guard |
| `cc-safety-net` | cc-safety-net | software | `kenryu42` | `github: kenryu42/cc-safety-net`; `homepage: https://ccsafetynet.com` | `kenryu42/cc-safety-net` | https://github.com/kenryu42/cc-safety-net |
| `fuzzyai` | FuzzyAI | software | `cyberark` | `github: cyberark/FuzzyAI` | `cyberark/FuzzyAI` | https://github.com/cyberark/FuzzyAI |
| `gliner-guard-omni` | gliner-guard-omni | model | `hivetrace` | `huggingface_model: hivetrace/gliner-guard-omni` | `hivetrace/gliner-guard-omni` | https://huggingface.co/hivetrace/gliner-guard-omni |
| `gliner2-guardrails-pii-multi` | GLiNER2-Guardrails-PII-Multi | model | `fastino` | `huggingface_model: fastino/GLiNER2-Guardrails-PII-Multi` | `fastino/GLiNER2-Guardrails-PII-Multi` | https://huggingface.co/fastino/GLiNER2-Guardrails-PII-Multi |
| `modernguard-1` | ModernGuard-1 | model | `guardion` | `huggingface_model: guardion/ModernGuard-1` | `guardion/ModernGuard-1` | https://huggingface.co/guardion/ModernGuard-1 |
| `nasiko` | nasiko | software | `nasiko-labs` | `github: Nasiko-Labs/nasiko`; `homepage: https://www.nasiko.com` | `Nasiko-Labs/nasiko` | https://github.com/Nasiko-Labs/nasiko |
| `ncii-guard-v02` | ncii-guard-v02 | model | `hfmlsoc` | `huggingface_model: hfmlsoc/ncii-guard-v02` | `hfmlsoc/ncii-guard-v02` | https://huggingface.co/hfmlsoc/ncii-guard-v02 |
| `polite-guard` | polite-guard | model | `intel` | `huggingface_model: Intel/polite-guard` | `Intel/polite-guard` | https://huggingface.co/Intel/polite-guard |
| `promptmap` | promptmap | software | `utkusen` | `github: utkusen/promptmap` | `utkusen/promptmap` | https://github.com/utkusen/promptmap |
| `skillspector` | SkillSpector | software | `nvidia` | `github: NVIDIA/SkillSpector`; `homepage: https://docs.nvidia.com/skills/scanning-agent-skills` | `NVIDIA/SkillSpector` | https://github.com/NVIDIA/SkillSpector |
| `stable-diffusion-safety-checker` | stable-diffusion-safety-checker | model | `compvis` | `huggingface_model: CompVis/stable-diffusion-safety-checker` | `CompVis/stable-diffusion-safety-checker` | https://huggingface.co/CompVis/stable-diffusion-safety-checker |
| `superagent` | superagent | software | `superagent-ai` | `github: superagent-ai/superagent`; `homepage: https://superagent.sh` | `superagent-ai/superagent` | https://github.com/superagent-ai/superagent |
| `text-moderation` | Text-Moderation | model | `koalaai` | `huggingface_model: KoalaAI/Text-Moderation` | `KoalaAI/Text-Moderation` | https://huggingface.co/KoalaAI/Text-Moderation |
| `valqore` | valqore | software | `valqore` | `github: valqore/valqore`; `homepage: https://www.valqore.io` | `valqore/valqore` | https://github.com/valqore/valqore |

Field derivation:

| slug | category from | slug from | display_name from | org from |
|---|---|---|---|---|
| `agent-governance-toolkit` | query `safe_t_aisafety`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | declared handle `github:microsoft` -> `microsoft` (sources/org_handles.yaml) |
| `agentic-radar` | query `safe_t_llmsecurity`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `agentic-security` | query `safe_t_llmsecurity`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `ai-infra-guard` | query `safe_t_llmsecurity`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | declared handle `github:Tencent` -> `tencent` (sources/org_handles.yaml) |
| `cc-safety-net` | query `safe_t_guardrails`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `fuzzyai` | query `safe_t_llmsecurity`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `gliner-guard-omni` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `zero-shot-classification`) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `gliner2-guardrails-pii-multi` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `token-classification`) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `modernguard-1` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `text-classification`) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `nasiko` | query `B_safe_agentsec`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `ncii-guard-v02` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `text-classification`) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `polite-guard` | rule **M3** (category-scoped query `hf_guard_search`, declared pipeline_tag `text-classification`) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `promptmap` | query `safe_t_promptinjection`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `skillspector` | query `safe_t_promptinjection`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | declared handle `github:NVIDIA` -> `nvidia` (sources/org_handles.yaml) |
| `stable-diffusion-safety-checker` | rule **M3** (category-scoped query `hf_safety_search`, declared pipeline_tag `None`) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `superagent` | query `safe_t_guardrails`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `text-moderation` | rule **M3** (category-scoped query `hf_moderation_search`, declared pipeline_tag `text-classification`) | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |
| `valqore` | query `safe_t_aisafety`, declared category `safeguards` | slugify(declared name) | declared name, verbatim | slugify(declared owner login) |

## `edge_hardware`: swept, nothing emitted

Swept with six GitHub queries (five topic-scoped, one free-text that returned nothing) and 28
vendor product pages; no row is emitted. Every
board-level candidate resolves to a vendor page and nothing else — no product-level repository,
package, Hub entry or paper id — and this batch requires an identifier that is not a URL on every
row. All 28 vendor-page candidates are in the parked table with their page and fetch date. No
artifact was invented to fill the gap: a vendor's SDK repository (`hailo-ai/hailort`,
`espressif/esp-idf`) is the software, not the board, and `discover-candidates` says in as many
words not to invent a plausible artifact for a candidate that has none. What a later sweep should
look for: a vendor-account SDK repository that is genuinely the product, a package the board
publishes, or a datasheet DOI. The question underneath it is for a person — see **Escalations**.

## What a fold has to rest on

A duplicate is a claim about identity, and the reconciliation is only as good as that claim. A
wrong fold does not merely mislabel one row: it removes a candidate from `unique_candidates` and
hides it behind arithmetic that still balances. So every fold in this batch has been re-audited
against the repo's own files, and one is kept only when it rests on a declaration or on a
byte-level observation:

| fold | what it rests on | rows |
|---|---|---|
| `repeats signal X` | the identifier is byte-identical to another occurrence of the same signal. No identity judgment is involved. | 463 |
| `head product P`, `tail row P` | the identifier is a **declared artifact** of `sources/products/P.yaml` or of a row already in `sources/registry/*.yaml`. Checked identifier by identifier against the declaration. | 88 |
| `resolution ledger: <verdict>` | the identifier appears in `sources/resolution_ledger.yaml` under a `product_equivalence` verdict in `NOT_A_NEW_PRODUCT`. | 7 |
| `release or SKU of P` | **both** conditions: `sources/model_families.yaml` declares the family `P-*`, and the signal's owner login is a handle `sources/org_handles.yaml` declares for an organization owning `P`'s declared artifacts. A first-party release inside a declared family. | 175 |
| a distribution-format redistribution | same owner login, name equal to another signal's name plus a format suffix, and the repo declares that format in its own `tags`. | 1 |
| a second or third path tried for one hardware signal | two URLs were probes in one lookup for one physical product, not two entities. | 5 |

**A folded name match is not evidence of identity.** `discover-candidates` already says so, in the
identity-digest section: an item whose only evidence is a folded name match is parked, not
proposed. The same discipline has to bind the sweep's own dedup, and in the third revision it did
not: 300 signals were folded onto a product because the product's name appeared in theirs.
`mlabonne/llm-datasets` and `poloclub/llm-landscape` were read as releases of `llm`, which is
Simon Willison's Datasette CLI (`simonw/llm`); `meta-llama/Prompt-Guard-86M` was read as a release
of `llama-prompt-guard`, which declares `meta-llama/Llama-Prompt-Guard-2-86M`, a different model;
`nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16` was read as a SKU of `nemotron`, which declares the 30B
Nano and not the 4B. All 300 are un-folded in **Parked — a withdrawn fold**.

**Withdrawing a fold cannot admit a row.** It moves a signal from the duplicate side of the
reconciliation to the unique side and records a park reason there, which the acceptance predicate
reads through `no_recorded_park_reason` — the one judgment-shaped clause, and the one that can only
ever remove a candidate. This is a dedup rule, not a legitimacy rule: it says nothing about whether
a candidate is a real product, and it cannot reject one. It only refuses to assert an identity the
repo has not declared.

## Format redistributions, counted as duplicates

One signal is folded on the duplicate side as a redistribution rather than parked, on a
mechanical predicate: same owner login, name equal to another signal's name plus a
distribution-format suffix, and the repo declares that format in its own `tags`. The shorter name
— the base-weights repo — is the representative of the pair.

| signal | source URL | fetched | folds onto |
|---|---|---|---|
| `LiquidAI/LFM2.5-2.6B-GGUF` | https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF | 2026-09-07 | distribution-format redistribution of the signal LiquidAI/LFM2.5-2.6B: same owner login, name is that name plus `-GGUF`, and the repo declares tag `gguf`. Folded onto the shorter name (the base-weights repo), which is the representative of the pair |

The seven other folds this section carried through the second and third revisions are
**removed** in this one. Every one of them rested on a sentence about what a repository *is* — a
mirror under a second owner, a Core ML conversion, an abliterated GGUF, a component model, a web
UI, a plugin surface — and not on a declaration, so each is un-folded into
**Parked — a withdrawn fold** as class N5. Three folds the second revision made were removed in
the third for the same kind of reason: `FacebookAI/roberta-large`, `google-t5/t5-base` and
`openai-community/gpt2-large` are each resolved on their own and emitted at the identity they
declare. Two lookalikes stay parked because the evidence does not settle them
(`prism-ml/*Bonsai*`, `distilbert/distilgpt2`).

## Parked — individually reasoned (288)

Every row below was surveyed and not accepted. Source URL and fetch date are given for parked
candidates on the same terms as accepted ones, so next week's sweep can re-check the reason
instead of triaging from scratch. `no category derivable` is the mechanical outcome of the
declared-metadata rule above, not a reading; every other reason names the boundary the category
roster already draws.

| candidate | source URL | fetched | category swept | reason not accepted |
|---|---|---|---|---|
| `0xmaximus/Galaxy-Bugbounty-Checklist` | https://github.com/0xmaximus/Galaxy-Bugbounty-Checklist | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `0xShug0/audio.cpp` | https://github.com/0xShug0/audio.cpp | 2026-09-07 | edge_hardware | boundary: model runtime or serving engine; nearer inference_code |
| `0xSteph/pentest-ai` | https://github.com/0xSteph/pentest-ai | 2026-09-07 | safeguards | boundary: offensive security or application-security tooling (bug hunting, exploit development, code scanning, pentest automation, CVE discovery) aimed at software, not a safeguard on an AI system's inputs, outputs or actions |
| `0xSteph/pentest-ai-agents` | https://github.com/0xSteph/pentest-ai-agents | 2026-09-07 | safeguards | boundary: offensive security or application-security tooling (bug hunting, exploit development, code scanning, pentest automation, CVE discovery) aimed at software, not a safeguard on an AI system's inputs, outputs or actions |
| `0xsyr0/Awesome-Cybersecurity-Handbooks` | https://github.com/0xsyr0/Awesome-Cybersecurity-Handbooks | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `adithya-s-k/AI-Engineering.academy` | https://github.com/adithya-s-k/AI-Engineering.academy | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `AI-Efficiency/Awesome-Model-Quantization` | https://github.com/AI-Efficiency/Awesome-Model-Quantization | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `ai-for-developers/awesome-ai-coding-tools` | https://github.com/ai-for-developers/awesome-ai-coding-tools | 2026-09-07 | safeguards | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `akto-api-security/akto` | https://github.com/akto-api-security/akto | 2026-09-07 | safeguards | boundary: API security-posture platform; the category is filters and constraints on model inputs and outputs |
| `amitshekhariitbhu/ai-engineering-interview-questions` | https://github.com/amitshekhariitbhu/ai-engineering-interview-questions | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `andialbrecht/sqlparse` | https://github.com/andialbrecht/sqlparse | 2026-09-07 | dataset_processing_tools | boundary: general-purpose parser or tokenizer for a programming or data language, with no model or corpus in its declared description or topics |
| `Anil-matcha/awesome-gpt-6-astra` | https://github.com/Anil-matcha/awesome-gpt-6-astra | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `arsenetar/dupeguru` | https://github.com/arsenetar/dupeguru | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `Awarexone/Agentic-Bug-Hunter` | https://github.com/Awarexone/Agentic-Bug-Hunter | 2026-09-07 | safeguards | boundary: offensive security or application-security tooling (bug hunting, exploit development, code scanning, pentest automation, CVE discovery) aimed at software, not a safeguard on an AI system's inputs, outputs or actions |
| `axoviq-ai/synthadoc` | https://github.com/axoviq-ai/synthadoc | 2026-09-07 | dataset_processing_tools | ambiguous category: document-to-wiki knowledge compilation positioned as a RAG alternative, not a training-corpus pipeline |
| `aydinnyunus/ai-captcha-bypass` | https://github.com/aydinnyunus/ai-captcha-bypass | 2026-09-07 | safeguards | boundary: offensive security or application-security tooling (bug hunting, exploit development, code scanning, pentest automation, CVE discovery) aimed at software, not a safeguard on an AI system's inputs, outputs or actions |
| `beclab/Olares` | https://github.com/beclab/Olares | 2026-09-07 | edge_hardware | boundary: end-user or domain application, not stack tooling in this category |
| `beelzebub-labs/beelzebub` | https://github.com/beelzebub-labs/beelzebub | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `beenuar/AiSOC` | https://github.com/beenuar/AiSOC | 2026-09-07 | safeguards | boundary: security-operations or security-engineering tooling (alert triage, incident response, threat modeling) that uses an LLM, rather than a safeguard applied to one |
| `beir-cellar/beir` | https://github.com/beir-cellar/beir | 2026-09-07 | dataset_processing_tools | boundary: evaluation benchmark or leaderboard, not corpus-construction software; nearer telemetry_observability |
| `BishopFox/sliver` | https://github.com/BishopFox/sliver | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `BlackArch/blackarch` | https://github.com/BlackArch/blackarch | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `borgbackup/borg` | https://github.com/borgbackup/borg | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `borgmatic-collective/borgmatic` | https://github.com/borgmatic-collective/borgmatic | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `BoundaryML/baml` | https://github.com/BoundaryML/baml | 2026-09-07 | safeguards | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `cactus-compute/cactus` | https://github.com/cactus-compute/cactus | 2026-09-07 | edge_hardware | boundary: on-device inference engine (software); this category is boards and chips |
| `capitalone/DataProfiler` | https://github.com/capitalone/DataProfiler | 2026-09-07 | safeguards | boundary: general privacy, PII-vault or data-profiling product, not an AI-system safeguard. Same boundary as microsoft/presidio, parked in this batch for the same reason |
| `Chevrotain/chevrotain` | https://github.com/Chevrotain/chevrotain | 2026-09-07 | dataset_processing_tools | boundary: general-purpose parser or tokenizer for a programming or data language, with no model or corpus in its declared description or topics |
| `ciur/papermerge` | https://github.com/ciur/papermerge | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `cleanlab/cleanlab` | https://github.com/cleanlab/cleanlab | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `collabora/WhisperLive` | https://github.com/collabora/WhisperLive | 2026-09-07 | compilers | boundary: computer-vision application or pipeline built on a runtime, not the runtime or compiler |
| `cupcakearmy/autorestic` | https://github.com/cupcakearmy/autorestic | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `cvs-health/uqlm` | https://github.com/cvs-health/uqlm | 2026-09-07 | safeguards | boundary: uncertainty quantification and hallucination scoring, not detection or filtering of unsafe content |
| `cyanfish/naps2` | https://github.com/cyanfish/naps2 | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `CyberStrikeus/CyberStrike` | https://github.com/CyberStrikeus/CyberStrike | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `Data-Centric-AI-Community/fg-data-profiling` | https://github.com/Data-Centric-AI-Community/fg-data-profiling | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `Data-Centric-AI-Community/fg-data-synthetic` | https://github.com/Data-Centric-AI-Community/fg-data-synthetic | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `data-infra/cube-studio` | https://github.com/data-infra/cube-studio | 2026-09-07 | edge_hardware | boundary: end-user or domain application, not stack tooling in this category |
| `data-privacy-stack/presidio` | https://github.com/data-privacy-stack/presidio | 2026-09-07 | safeguards | boundary: general-purpose PII detection and redaction framework, read into safeguards by analogy with head product llm-guard. No declared mapping settles it, so it is parked for a person rather than emitted |
| `datawhalechina/torch-rechub` | https://github.com/datawhalechina/torch-rechub | 2026-09-07 | edge_hardware | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `deepsense-ai/ragbits` | https://github.com/deepsense-ai/ragbits | 2026-09-07 | safeguards | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `DLR-RM/BlenderProc` | https://github.com/DLR-RM/BlenderProc | 2026-09-07 | dataset_processing_tools | ambiguous boundary: synthetic-image rendering for vision training. In scope by the letter of 'synthetic-data generation pipelines', but every product on this roster builds text or document corpora; needs a boundary ruling before it is emitted |
| `Docta-ai/docta` | https://github.com/Docta-ai/docta | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `dusty-nv/jetson-inference` | https://github.com/dusty-nv/jetson-inference | 2026-09-07 | compilers | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `eikek/docspell` | https://github.com/eikek/docspell | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `elder-plinius/CL4R1T4S` | https://github.com/elder-plinius/CL4R1T4S | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `elder-plinius/L1B3RT4S` | https://github.com/elder-plinius/L1B3RT4S | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `elementalsouls/Claude-BugHunter` | https://github.com/elementalsouls/Claude-BugHunter | 2026-09-07 | safeguards | boundary: offensive security or application-security tooling (bug hunting, exploit development, code scanning, pentest automation, CVE discovery) aimed at software, not a safeguard on an AI system's inputs, outputs or actions |
| `enpeizhao/CVprojects` | https://github.com/enpeizhao/CVprojects | 2026-09-07 | compilers | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `EnzymeAD/Enzyme` | https://github.com/EnzymeAD/Enzyme | 2026-09-07 | compilers | ambiguous boundary: an automatic-differentiation compiler pass for LLVM and MLIR. Whether AD counts as 'otherwise optimizes tensor programs for target accelerator hardware' is a boundary question this sweep should not settle alone |
| `Exorust/TorchLeet` | https://github.com/Exorust/TorchLeet | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `FailproofAI/failproofai` | https://github.com/FailproofAI/failproofai | 2026-09-07 | safeguards | held: sources/resolution_ledger.yaml carries an `unresolved` product_equivalence ruling on this repository |
| `FareedKhan-dev/kimi-k3-in-c` | https://github.com/FareedKhan-dev/kimi-k3-in-c | 2026-09-07 | compilers | boundary: a single-file C inference re-implementation of a model already on the map; not compilation or optimization software (note: the automated family fold matched it to `kimi`, which is wrong -- it is a distinct artifact, parked on its own merits) |
| `FedML-AI/FedML` | https://github.com/FedML-AI/FedML | 2026-09-07 | edge_hardware | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `future-agi/future-agi` | https://github.com/future-agi/future-agi | 2026-09-07 | safeguards | boundary: evaluation / observability platform; nearer telemetry_observability |
| `GH05TCREW/pentestagent` | https://github.com/GH05TCREW/pentestagent | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `GokuMohandas/Made-With-ML` | https://github.com/GokuMohandas/Made-With-ML | 2026-09-07 | dataset_processing_tools | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `google/magika` | https://github.com/google/magika | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `GreenmaskIO/greenmask` | https://github.com/GreenmaskIO/greenmask | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `halfrost/Halfrost-Field` | https://github.com/halfrost/Halfrost-Field | 2026-09-07 | compilers | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `hemansnation/AI-Engineer-Headquarters` | https://github.com/hemansnation/AI-Engineer-Headquarters | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `hitsz-ids/synthetic-data-generator` | https://github.com/hitsz-ids/synthetic-data-generator | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `hybridgroup/gocv` | https://github.com/hybridgroup/gocv | 2026-09-07 | compilers | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `hyperai/tvm-cn` | https://github.com/hyperai/tvm-cn | 2026-09-07 | compilers | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `hyperjumptech/grule-rule-engine` | https://github.com/hyperjumptech/grule-rule-engine | 2026-09-07 | compilers | boundary: business rule engine. `inference engine` here is the rule-based sense, not a model compiler or runtime |
| `ifixai-ai/iFixAi` | https://github.com/ifixai-ai/iFixAi | 2026-09-07 | safeguards | boundary: evaluation / observability platform; nearer telemetry_observability |
| `iver56/audiomentations` | https://github.com/iver56/audiomentations | 2026-09-07 | dataset_processing_tools | boundary: image, audio or video augmentation / data-loading library for model training, not text training-corpus construction |
| `iver56/torch-audiomentations` | https://github.com/iver56/torch-audiomentations | 2026-09-07 | dataset_processing_tools | boundary: image, audio or video augmentation / data-loading library for model training, not text training-corpus construction |
| `jiep/offensive-ai-compilation` | https://github.com/jiep/offensive-ai-compilation | 2026-09-07 | safeguards | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `jolibrain/deepdetect` | https://github.com/jolibrain/deepdetect | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code than compilers |
| `jphall663/awesome-machine-learning-interpretability` | https://github.com/jphall663/awesome-machine-learning-interpretability | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `k2-fsa/sherpa-onnx` | https://github.com/k2-fsa/sherpa-onnx | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `karanhudia/borg-ui` | https://github.com/karanhudia/borg-ui | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `KeygraphHQ/shannon` | https://github.com/KeygraphHQ/shannon | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `Kiln-AI/Kiln` | https://github.com/Kiln-AI/Kiln | 2026-09-07 | dataset_processing_tools | ambiguous category: spans evaluation, RAG, fine-tuning and synthetic data; one product one category cannot be settled from the repository alone |
| `klsdf/GreenResourcesManager` | https://github.com/klsdf/GreenResourcesManager | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category (query noise: unrelated desktop resource manager) |
| `kopia/kopia` | https://github.com/kopia/kopia | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `kornelski/pngquant` | https://github.com/kornelski/pngquant | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `Kritt-ai/open-kritt` | https://github.com/Kritt-ai/open-kritt | 2026-09-07 | safeguards | boundary: offensive security or application-security tooling (bug hunting, exploit development, code scanning, pentest automation, CVE discovery) aimed at software, not a safeguard on an AI system's inputs, outputs or actions |
| `langchain4j/langchain4j` | https://github.com/langchain4j/langchain4j | 2026-09-07 | compilers | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `LaoFeng-mouse/flyingmouse-format` | https://github.com/LaoFeng-mouse/flyingmouse-format | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `larlarua/AutoCVE` | https://github.com/larlarua/AutoCVE | 2026-09-07 | safeguards | boundary: offensive security or application-security tooling (bug hunting, exploit development, code scanning, pentest automation, CVE discovery) aimed at software, not a safeguard on an AI system's inputs, outputs or actions |
| `lennney/stop-that-shit` | https://github.com/lennney/stop-that-shit | 2026-09-07 | safeguards | boundary: coding-agent workflow hook (scope-creep and checksum lint), not a filter or constraint on unsafe model inputs, outputs or actions |
| `lk-geimfari/mimesis` | https://github.com/lk-geimfari/mimesis | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `llvm/circt` | https://github.com/llvm/circt | 2026-09-07 | compilers | boundary: hardware / EDA circuit compilers, not model compilation for accelerators |
| `lonePatient/awesome-pretrained-chinese-nlp-models` | https://github.com/lonePatient/awesome-pretrained-chinese-nlp-models | 2026-09-07 | dataset_processing_tools | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `Luce-Org/lucebox` | https://github.com/Luce-Org/lucebox | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `lutzroeder/netron` | https://github.com/lutzroeder/netron | 2026-09-07 | compilers | boundary: model visualization only; performs no lowering, conversion or optimization |
| `mandiant/commando-vm` | https://github.com/mandiant/commando-vm | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `marcoslucianops/DeepStream-Yolo` | https://github.com/marcoslucianops/DeepStream-Yolo | 2026-09-07 | compilers | boundary: model zoo, reference implementation set or converted-weights collection, not compilation or optimization software |
| `maurosoria/dirsearch` | https://github.com/maurosoria/dirsearch | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `maximhq/bifrost` | https://github.com/maximhq/bifrost | 2026-09-07 | safeguards | boundary: LLM gateway or model router; nearer ui_api |
| `mhx/dwarfs` | https://github.com/mhx/dwarfs | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `microsoft/ai-dev-gallery` | https://github.com/microsoft/ai-dev-gallery | 2026-09-07 | edge_hardware | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `microsoft/AI-Red-Teaming-Playground-Labs` | https://github.com/microsoft/AI-Red-Teaming-Playground-Labs | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `microsoft/Biodiversity` | https://github.com/microsoft/Biodiversity | 2026-09-07 | edge_hardware | boundary: end-user or domain application, not stack tooling in this category |
| `microsoft/SynapseML` | https://github.com/microsoft/SynapseML | 2026-09-07 | compilers | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `mikel-brostrom/boxmot` | https://github.com/mikel-brostrom/boxmot | 2026-09-07 | compilers | boundary: computer-vision application or pipeline built on a runtime, not the runtime or compiler |
| `mlc-ai/web-llm` | https://github.com/mlc-ai/web-llm | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code than compilers |
| `moj-analytical-services/splink` | https://github.com/moj-analytical-services/splink | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `mrwadams/attackgen` | https://github.com/mrwadams/attackgen | 2026-09-07 | safeguards | boundary: security-operations or security-engineering tooling (alert triage, incident response, threat modeling) that uses an LLM, rather than a safeguard applied to one |
| `mrwadams/stride-gpt` | https://github.com/mrwadams/stride-gpt | 2026-09-07 | safeguards | boundary: security-operations or security-engineering tooling (alert triage, incident response, threat modeling) that uses an LLM, rather than a safeguard applied to one |
| `natasha/natasha` | https://github.com/natasha/natasha | 2026-09-07 | dataset_processing_tools | boundary: general language-processing toolkit (morphology, NER, embeddings); nearer ml_frameworks than corpus construction |
| `nats-io/nats-server` | https://github.com/nats-io/nats-server | 2026-09-07 | edge_hardware | boundary: end-user or domain application, not stack tooling in this category |
| `niedev/RTranslator` | https://github.com/niedev/RTranslator | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `nobodywho-ooo/nobodywho` | https://github.com/nobodywho-ooo/nobodywho | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code than compilers |
| `NVIDIA/DALI` | https://github.com/NVIDIA/DALI | 2026-09-07 | dataset_processing_tools | boundary: image, audio or video augmentation / data-loading library for model training, not text training-corpus construction |
| `NVIDIA/GenerativeAIExamples` | https://github.com/NVIDIA/GenerativeAIExamples | 2026-09-07 | compilers | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `ocrmypdf/OCRmyPDF` | https://github.com/ocrmypdf/OCRmyPDF | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `onnx/models` | https://github.com/onnx/models | 2026-09-07 | compilers | boundary: model zoo or converted-weights collection, not compilation or optimization software |
| `openai/codex-security` | https://github.com/openai/codex-security | 2026-09-07 | safeguards | boundary: offensive security or application-security tooling (bug hunting, exploit development, code scanning, pentest automation, CVE discovery) aimed at software, not a safeguard on an AI system's inputs, outputs or actions |
| `OpenCSGs/csghub` | https://github.com/OpenCSGs/csghub | 2026-09-07 | dataset_processing_tools | boundary: model and asset management platform / hub; nearer ui_api than dataset_processing_tools |
| `OpenNMT/CTranslate2` | https://github.com/OpenNMT/CTranslate2 | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `openpaperwork/paperwork` | https://github.com/openpaperwork/paperwork | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `openvenues/libpostal` | https://github.com/openvenues/libpostal | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category |
| `oritera/Cairn` | https://github.com/oritera/Cairn | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `outflanknl/RedELK` | https://github.com/outflanknl/RedELK | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `ovg-project/kvcached` | https://github.com/ovg-project/kvcached | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code than compilers |
| `OWASP/www-project-top-10-for-large-language-model-applications` | https://github.com/OWASP/www-project-top-10-for-large-language-model-applications | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `paperless-ngx/paperless-ngx` | https://github.com/paperless-ngx/paperless-ngx | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `pgmpy/pgmpy` | https://github.com/pgmpy/pgmpy | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category |
| `PINTO0309/PINTO_model_zoo` | https://github.com/PINTO0309/PINTO_model_zoo | 2026-09-07 | compilers | boundary: model zoo or converted-weights collection, not compilation or optimization software |
| `PKU-Alignment/safe-rlhf` | https://github.com/PKU-Alignment/safe-rlhf | 2026-09-07 | safeguards | boundary: safety alignment training method; nearer finetuning_code than a guardrail |
| `PlakarKorp/plakar` | https://github.com/PlakarKorp/plakar | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `plurai-ai/intellagent` | https://github.com/plurai-ai/intellagent | 2026-09-07 | dataset_processing_tools | boundary: evaluation / observability platform; nearer telemetry_observability |
| `prometheus/alertmanager` | https://github.com/prometheus/alertmanager | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category (query noise: matched on 'alertmanager', unrelated to AI data tooling) |
| `QData/TextAttack` | https://github.com/QData/TextAttack | 2026-09-07 | dataset_processing_tools | boundary: adversarial-robustness attack and augmentation framework for NLP models; nearer safeguards, and not corpus construction |
| `qualcomm/ai-hub-models` | https://github.com/qualcomm/ai-hub-models | 2026-09-07 | compilers | boundary: model zoo, reference implementation set or converted-weights collection, not compilation or optimization software |
| `R6410418/Jackrong-llm-finetuning-guide` | https://github.com/R6410418/Jackrong-llm-finetuning-guide | 2026-09-07 | dataset_processing_tools | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `rasbt/LLMs-from-scratch` | https://github.com/rasbt/LLMs-from-scratch | 2026-09-07 | dataset_processing_tools | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `RedSiege/C2concealer` | https://github.com/RedSiege/C2concealer | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `Renumics/spotlight` | https://github.com/Renumics/spotlight | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `restic/restic` | https://github.com/restic/restic | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `RightNow-AI/picolm` | https://github.com/RightNow-AI/picolm | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `roboflow/inference` | https://github.com/roboflow/inference | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code than compilers |
| `ROCm/FastFlowLM` | https://github.com/ROCm/FastFlowLM | 2026-09-07 | edge_hardware | boundary: model runtime or serving engine; nearer inference_code |
| `roshan-research/hazm` | https://github.com/roshan-research/hazm | 2026-09-07 | dataset_processing_tools | boundary: general language-processing toolkit (morphology, NER, embeddings); nearer ml_frameworks than corpus construction |
| `royshil/obs-backgroundremoval` | https://github.com/royshil/obs-backgroundremoval | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `rustic-rs/rustic` | https://github.com/rustic-rs/rustic | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `ruvnet/RuVector` | https://github.com/ruvnet/RuVector | 2026-09-07 | compilers | boundary: vector index and memory database; nearer storage |
| `RyanCodrai/turbovec` | https://github.com/RyanCodrai/turbovec | 2026-09-07 | compilers | held: sources/resolution_ledger.yaml carries an `unresolved` product_equivalence ruling on this repository; it needs a person, not another sweep |
| `safe-graph/graph-fraud-detection-papers` | https://github.com/safe-graph/graph-fraud-detection-papers | 2026-09-07 | dataset_processing_tools | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `sahib/rmlint` | https://github.com/sahib/rmlint | 2026-09-07 | dataset_processing_tools | boundary: general-purpose file backup or block-level deduplication; this category is training-corpus construction |
| `scambier/obsidian-omnisearch` | https://github.com/scambier/obsidian-omnisearch | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `ScrapeGraphAI/Scrapegraph-ai` | https://github.com/ScrapeGraphAI/Scrapegraph-ai | 2026-09-07 | dataset_processing_tools | boundary: agent-facing web scraping; its peer firecrawl is already a head product in another category, so this roster is not where it belongs |
| `sdv-dev/CTGAN` | https://github.com/sdv-dev/CTGAN | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `sdv-dev/SDV` | https://github.com/sdv-dev/SDV | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `securitybunker/databunker` | https://github.com/securitybunker/databunker | 2026-09-07 | safeguards | boundary: general privacy, PII-vault or data-profiling product, not an AI-system safeguard. Same boundary as microsoft/presidio, parked in this batch for the same reason |
| `skills/secure-code-game` | https://github.com/skills/secure-code-game | 2026-09-07 | safeguards | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `SmartFlowAI/EmoLLM` | https://github.com/SmartFlowAI/EmoLLM | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category |
| `snakers4/silero-vad` | https://github.com/snakers4/silero-vad | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `stacklok/toolhive` | https://github.com/stacklok/toolhive | 2026-09-07 | safeguards | boundary: agent or MCP runtime / control plane; nearer orchestration_agents |
| `stefan-jansen/machine-learning-for-trading` | https://github.com/stefan-jansen/machine-learning-for-trading | 2026-09-07 | dataset_processing_tools | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `SteveTheKiller/KillerPDF` | https://github.com/SteveTheKiller/KillerPDF | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `stochasticai/xTuring` | https://github.com/stochasticai/xTuring | 2026-09-07 | compilers | boundary: fine-tuning toolkit; nearer finetuning_code |
| `supertone-inc/supertonic` | https://github.com/supertone-inc/supertonic | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `synthetichealth/synthea` | https://github.com/synthetichealth/synthea | 2026-09-07 | dataset_processing_tools | boundary: tabular / privacy synthetic-data generation, not LLM training-corpus construction |
| `SYSTRAN/faster-whisper` | https://github.com/SYSTRAN/faster-whisper | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code |
| `The-Art-of-Hacking/h4cker` | https://github.com/The-Art-of-Hacking/h4cker | 2026-09-07 | safeguards | authored content (curated list, course, book, guide, blog, translated docs, example collection), not software; the resolution ledger already parks this shape pending an ontology decision |
| `theopenco/llmgateway` | https://github.com/theopenco/llmgateway | 2026-09-07 | safeguards | boundary: LLM gateway or model router; nearer ui_api |
| `theori-io/copy-fail-CVE-2026-31431` | https://github.com/theori-io/copy-fail-CVE-2026-31431 | 2026-09-07 | safeguards | not a product: a published proof-of-concept exploit for one CVE |
| `theseer/tokenizer` | https://github.com/theseer/tokenizer | 2026-09-07 | dataset_processing_tools | boundary: general-purpose parser or tokenizer for a programming or data language, with no model or corpus in its declared description or topics |
| `thomasxm/BOAZ_beta` | https://github.com/thomasxm/BOAZ_beta | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions; the repository also declares itself no longer maintained |
| `Threekiii/Awesome-Redteam` | https://github.com/Threekiii/Awesome-Redteam | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `TingsongYu/PyTorch-Tutorial-2nd` | https://github.com/TingsongYu/PyTorch-Tutorial-2nd | 2026-09-07 | compilers | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `TorchIO-project/torchio` | https://github.com/TorchIO-project/torchio | 2026-09-07 | dataset_processing_tools | boundary: image, audio or video augmentation / data-loading library for model training, not text training-corpus construction |
| `tracel-ai/burn` | https://github.com/tracel-ai/burn | 2026-09-07 | compilers | boundary: general ML, tensor or agent framework; nearer ml_frameworks or orchestration_agents |
| `uber/ADR` | https://github.com/uber/ADR | 2026-09-07 | safeguards | ambiguous category: its own description leads with observability and threat detection, which straddles safeguards and telemetry_observability; one product one category cannot be settled from the repository alone |
| `ufoym/deepo` | https://github.com/ufoym/deepo | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `UFund-Me/Qbot` | https://github.com/UFund-Me/Qbot | 2026-09-07 | compilers | boundary: end-user or domain application, not stack tooling in this category |
| `uhop/stream-json` | https://github.com/uhop/stream-json | 2026-09-07 | dataset_processing_tools | boundary: general-purpose parser or tokenizer for a programming or data language, with no model or corpus in its declared description or topics |
| `ultralytics/yolov3` | https://github.com/ultralytics/yolov3 | 2026-09-07 | compilers | boundary: vision model and training repo, not model-compilation software |
| `ultralytics/yolov5` | https://github.com/ultralytics/yolov5 | 2026-09-07 | compilers | boundary: vision model and training repo, not model-compilation software |
| `unrealcv/unrealcv` | https://github.com/unrealcv/unrealcv | 2026-09-07 | dataset_processing_tools | boundary: end-user or domain application, not stack tooling in this category |
| `utkusen/sast-skills` | https://github.com/utkusen/sast-skills | 2026-09-07 | safeguards | boundary: offensive security or application-security tooling (bug hunting, exploit development, code scanning, pentest automation, CVE discovery) aimed at software, not a safeguard on an AI system's inputs, outputs or actions |
| `visual-layer/fastdup` | https://github.com/visual-layer/fastdup | 2026-09-07 | dataset_processing_tools | ambiguous boundary: image and video dataset deduplication. In scope by the letter of 'deduplication', but this roster is text and document corpus tooling; needs the same boundary ruling as BlenderProc |
| `vllm-project/semantic-router` | https://github.com/vllm-project/semantic-router | 2026-09-07 | safeguards | boundary: LLM gateway or model router; nearer ui_api |
| `voxel51/fiftyone` | https://github.com/voxel51/fiftyone | 2026-09-07 | dataset_processing_tools | ambiguous boundary: computer-vision dataset curation and visualization; same unresolved text-versus-vision boundary |
| `wang-xinyu/tensorrtx` | https://github.com/wang-xinyu/tensorrtx | 2026-09-07 | compilers | boundary: model zoo, reference implementation set or converted-weights collection, not compilation or optimization software |
| `webdataset/webdataset` | https://github.com/webdataset/webdataset | 2026-09-07 | dataset_processing_tools | boundary: dataset storage format and I/O system for training loops, not corpus construction |
| `wxyhgk/retain-pdf` | https://github.com/wxyhgk/retain-pdf | 2026-09-07 | dataset_processing_tools | boundary: document workflow for people (scan, archive, manage, search, view, edit, translate, print). The roster is training-corpus construction, and the declared description names a human document task rather than data prepared for a model |
| `xlite-dev/lite.ai.toolkit` | https://github.com/xlite-dev/lite.ai.toolkit | 2026-09-07 | compilers | boundary: model zoo or converted-weights collection, not compilation or optimization software |
| `ymcui/Chinese-LLaMA-Alpaca` | https://github.com/ymcui/Chinese-LLaMA-Alpaca | 2026-09-07 | compilers | boundary: derivative model weights plus training scripts, not compilation or optimization software |
| `youssofal/MTPLX` | https://github.com/youssofal/MTPLX | 2026-09-07 | compilers | boundary: model runtime or serving engine; nearer inference_code than compilers |
| `zama-ai/concrete` | https://github.com/zama-ai/concrete | 2026-09-07 | compilers | boundary: fully-homomorphic-encryption compiler, not model lowering or optimization for accelerator targets |
| `zan8in/afrog` | https://github.com/zan8in/afrog | 2026-09-07 | safeguards | boundary: offensive security / penetration testing of software, not a safeguard on an AI system's inputs, outputs or actions |
| `Zaneham/Booth` | https://github.com/Zaneham/Booth | 2026-09-07 | compilers | implausible signal, parked with the number: 1,737 stars on a single-owner repository created 2026-02-16 that claims a complete CUDA, Triton and HIP compiler across multiple GPU and CPU architectures. The scope-versus-provenance mismatch is what bothers me; parked for a person, not rejected |
| `Zeyad-Azima/Offensive-Resources` | https://github.com/Zeyad-Azima/Offensive-Resources | 2026-09-07 | safeguards | authored content (curated list, course, notes, prompt collection), not software; the ledger already parks this shape pending an ontology decision |
| `ZhangJinHaHaHa/AgentLens` | https://github.com/ZhangJinHaHaHa/AgentLens | 2026-09-07 | safeguards | boundary: end-user or domain application, not stack tooling in this category |
| `zinggAI/zingg` | https://github.com/zinggAI/zingg | 2026-09-07 | dataset_processing_tools | boundary: label-quality, profiling or record-linkage tooling for supervised datasets, not corpus construction |
| `amazon/chronos-2` | https://huggingface.co/amazon/chronos-2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `amazon/chronos-bolt-small` | https://huggingface.co/amazon/chronos-bolt-small | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `autogluon/chronos-2-small` | https://huggingface.co/autogluon/chronos-2-small | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `BAAI/bge-base-en-v1.5` | https://huggingface.co/BAAI/bge-base-en-v1.5 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `BAAI/bge-large-en-v1.5` | https://huggingface.co/BAAI/bge-large-en-v1.5 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `BAAI/bge-m3` | https://huggingface.co/BAAI/bge-m3 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `BAAI/bge-reranker-v2-m3` | https://huggingface.co/BAAI/bge-reranker-v2-m3 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `BAAI/bge-small-en-v1.5` | https://huggingface.co/BAAI/bge-small-en-v1.5 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `BAAI/bge-small-zh-v1.5` | https://huggingface.co/BAAI/bge-small-zh-v1.5 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `baidu/Unlimited-OCR` | https://huggingface.co/baidu/Unlimited-OCR | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `Bingsu/adetailer` | https://huggingface.co/Bingsu/adetailer | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `biohub/ESMC-6B` | https://huggingface.co/biohub/ESMC-6B | 2026-09-07 | base_pretrained | boundary: protein or biological-sequence language model. The base_pretrained roster is text foundation models, and no category in the taxonomy holds a biological-sequence model, so this needs a category-proposal issue before any tier can hold it |
| `Comfy-Org/Krea-2` | https://huggingface.co/Comfy-Org/Krea-2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `Comfy-Org/stable-diffusion-v1-5-archive` | https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` | https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `Comfy-Org/z_image_turbo` | https://huggingface.co/Comfy-Org/z_image_turbo | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `coqui/XTTS-v2` | https://huggingface.co/coqui/XTTS-v2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `cross-encoder/ms-marco-MiniLM-L4-v2` | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L4-v2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `cross-encoder/ms-marco-MiniLM-L6-v2` | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `datalab-to/chandra-ocr-2` | https://huggingface.co/datalab-to/chandra-ocr-2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `datasocietyco/bge-base-en-v1.5-course-recommender-v5` | https://huggingface.co/datasocietyco/bge-base-en-v1.5-course-recommender-v5 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `dbmdz/bert-large-cased-finetuned-conll03-english` | https://huggingface.co/dbmdz/bert-large-cased-finetuned-conll03-english | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `distilbert/distilgpt2` | https://huggingface.co/distilbert/distilgpt2 | 2026-09-07 | base_pretrained | ambiguous identity: a distilled GPT-2 published alongside DistilBERT. Whether it is its own product or a variant of the accepted `distilbert` row is exactly the ambiguity the workflow says to park rather than guess |
| `facebook/contriever` | https://huggingface.co/facebook/contriever | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `facebook/dinov2-small` | https://huggingface.co/facebook/dinov2-small | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `facebook/esm2_t33_650M_UR50D` | https://huggingface.co/facebook/esm2_t33_650M_UR50D | 2026-09-07 | base_pretrained | boundary: protein or biological-sequence language model. The base_pretrained roster is text foundation models, and no category in the taxonomy holds a biological-sequence model, so this needs a category-proposal issue before any tier can hold it |
| `facebook/sam3` | https://huggingface.co/facebook/sam3 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `Falconsai/nsfw_image_detection` | https://huggingface.co/Falconsai/nsfw_image_detection | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `farbodtavakkoli/OTel-2.0-LLM-31B-IT` | https://huggingface.co/farbodtavakkoli/OTel-2.0-LLM-31B-IT | 2026-09-07 | finetuned_chat | implausible signal, parked with the number: 6.9M 30-day downloads on a 31B model published under an individual account with no organization, no lineage on the card and no line I could resolve to a vendor. Parked for a person, not rejected |
| `farbodtavakkoli/OTel-LLM-27B-IT` | https://huggingface.co/farbodtavakkoli/OTel-LLM-27B-IT | 2026-09-07 | finetuned_chat | implausible signal, parked with the number: 6.9M 30-day downloads on a 31B model published under an individual account with no organization, no lineage on the card and no line I could resolve to a vendor. Parked for a person, not rejected |
| `farbodtavakkoli/OTel-LLM-E4B-IT` | https://huggingface.co/farbodtavakkoli/OTel-LLM-E4B-IT | 2026-09-07 | finetuned_chat | implausible signal, parked with the number: 6.9M 30-day downloads on a 31B model published under an individual account with no organization, no lineage on the card and no line I could resolve to a vendor. Parked for a person, not rejected |
| `google/electra-base-discriminator` | https://huggingface.co/google/electra-base-discriminator | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `google/vit-base-patch16-224` | https://huggingface.co/google/vit-base-patch16-224 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `hexgrad/Kokoro-82M` | https://huggingface.co/hexgrad/Kokoro-82M | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `intfloat/multilingual-e5-base` | https://huggingface.co/intfloat/multilingual-e5-base | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `intfloat/multilingual-e5-large` | https://huggingface.co/intfloat/multilingual-e5-large | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `intfloat/multilingual-e5-small` | https://huggingface.co/intfloat/multilingual-e5-small | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `Jeesup/svd-safety-llama3_1_8b_instruct_up_basis_finetuned_keep_0p60` | https://huggingface.co/Jeesup/svd-safety-llama3_1_8b_instruct_up_basis_finetuned_keep_0p60 | 2026-09-07 | safeguards | not a product: a research checkpoint from an ablation sweep, with no named product line |
| `jonatasgrosman/wav2vec2-large-xlsr-53-japanese` | https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-japanese | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `jonatasgrosman/wav2vec2-large-xlsr-53-polish` | https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-polish | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `jonatasgrosman/wav2vec2-large-xlsr-53-portuguese` | https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-portuguese | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `laion/clap-htsat-fused` | https://huggingface.co/laion/clap-htsat-fused | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `Lightricks/LTX-2.5` | https://huggingface.co/Lightricks/LTX-2.5 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `llava-hf/llava-1.5-7b-hf` | https://huggingface.co/llava-hf/llava-1.5-7b-hf | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `mudler/Laguna-XS-2.1-APEX-GGUF` | https://huggingface.co/mudler/Laguna-XS-2.1-APEX-GGUF | 2026-09-07 | finetuned_chat | third-party or vendor quantized redistribution: the repo declares tags `gguf` and `quantized` and publishes no base weights of its own |
| `nomic-ai/nomic-embed-text-v1.5` | https://huggingface.co/nomic-ai/nomic-embed-text-v1.5 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `openai/clip-vit-base-patch32` | https://huggingface.co/openai/clip-vit-base-patch32 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `openai/clip-vit-large-patch14` | https://huggingface.co/openai/clip-vit-large-patch14 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `openai/whisper-large-v3` | https://huggingface.co/openai/whisper-large-v3 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `openai/whisper-large-v3-turbo` | https://huggingface.co/openai/whisper-large-v3-turbo | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `optimum-intel-internal-testing/tiny-random-stable-diffusion-with-safety-checker` | https://huggingface.co/optimum-intel-internal-testing/tiny-random-stable-diffusion-with-safety-checker | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `prism-ml/Bonsai-27B-mlx-1bit` | https://huggingface.co/prism-ml/Bonsai-27B-mlx-1bit | 2026-09-07 | finetuned_chat | third-party derivative: a quantized, abliterated or repackaged redistribution of weights already represented on the map; and the upstream trainer of the Bonsai weights could not be identified from the card, so identity is unsettled |
| `prism-ml/Ternary-Bonsai-27B-mlx-2bit` | https://huggingface.co/prism-ml/Ternary-Bonsai-27B-mlx-2bit | 2026-09-07 | finetuned_chat | third-party derivative: a quantized, abliterated or repackaged redistribution of weights already represented on the map; same unresolved upstream as Bonsai-27B-mlx-1bit |
| `ProsusAI/finbert` | https://huggingface.co/ProsusAI/finbert | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `pyannote/segmentation-3.0` | https://huggingface.co/pyannote/segmentation-3.0 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `pyannote/speaker-diarization-3.1` | https://huggingface.co/pyannote/speaker-diarization-3.1 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `pyannote/speaker-diarization-community-1` | https://huggingface.co/pyannote/speaker-diarization-community-1 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `pyannote/wespeaker-voxceleb-resnet34-LM` | https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `sentence-transformers/all-distilroberta-v1` | https://huggingface.co/sentence-transformers/all-distilroberta-v1 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `sentence-transformers/all-MiniLM-L6-v2` | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `sentence-transformers/all-mpnet-base-v2` | https://huggingface.co/sentence-transformers/all-mpnet-base-v2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `sentence-transformers/multi-qa-mpnet-base-dot-v1` | https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-dot-v1 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `sshleifer/tiny-gpt2` | https://huggingface.co/sshleifer/tiny-gpt2 | 2026-09-07 | base_pretrained | not a product: tiny random-weight test fixture published for CI |
| `timm/efficientnet_b3.ra2_in1k` | https://huggingface.co/timm/efficientnet_b3.ra2_in1k | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `timm/mobilenetv3_small_100.lamb_in1k` | https://huggingface.co/timm/mobilenetv3_small_100.lamb_in1k | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `trl-internal-testing/tiny-Qwen2ForCausalLM-2.5` | https://huggingface.co/trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 | 2026-09-07 | finetuned_chat | not a product: tiny random-weight test fixture published for CI |
| `trl-internal-testing/tiny-Qwen3ForCausalLM` | https://huggingface.co/trl-internal-testing/tiny-Qwen3ForCausalLM | 2026-09-07 | finetuned_chat | not a product: tiny random-weight test fixture published for CI |
| `vikhyatk/moondream2` | https://huggingface.co/vikhyatk/moondream2 | 2026-09-07 | — | no category derivable: the model's declared pipeline_tag is not in the declared-metadata table (docs/sweeps summary, `Category from declared metadata`) and no query that returned it declares a category |
| `brainchip.com/akida-neural-processor-soc/` | https://brainchip.com/akida-neural-processor-soc/ | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `coral.ai/products/dev-board-micro/` | https://coral.ai/products/dev-board-micro/ | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `hailo.ai/products/ai-accelerators/hailo-8l-ai-accelerator/` | https://hailo.ai/products/ai-accelerators/hailo-8l-ai-accelerator/ | 2026-09-07 | edge_hardware | SKU: the lower-cost, DRAM-free variant of head product hailo-8. This is the amazon-nova-pro shape docs/reference/identity.md warns about |
| `kinara.ai/products/` | https://kinara.ai/products/ | 2026-09-07 | edge_hardware | fetch did not complete for a product page (404); Kinara's catalog appears to have moved after the NXP acquisition |
| `milkv.io/duo` | https://milkv.io/duo | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `pine64.com/product-category/ox64/` | https://pine64.com/product-category/ox64/ | 2026-09-07 | edge_hardware | store category page rather than a product page; the Ox64 itself needs a product-level source before a row |
| `radxa.com/products/accessories/penta-sata-hat` | https://radxa.com/products/accessories/penta-sata-hat | 2026-09-07 | edge_hardware | boundary: a SATA storage HAT, not an inference board or chip |
| `radxa.com/products/aicore/ai-core-x` | https://radxa.com/products/aicore/ai-core-x | 2026-09-07 | edge_hardware | fetch did not complete (404); the Radxa AI Core X may exist under another path |
| `radxa.com/products/rock5/5c` | https://radxa.com/products/rock5/5c | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `shop.luxonis.com/products/oak-d` | https://shop.luxonis.com/products/oak-d | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `sima.ai/` | https://sima.ai/ | 2026-09-07 | edge_hardware | vendor root only; no product identity |
| `sima.ai/products/` | https://sima.ai/products/ | 2026-09-07 | edge_hardware | fetch did not complete for a product page (404 on /products/ and /modalix/; only the vendor root resolved). No product identity to write down yet |
| `sipeed.com/licheepi4a` | https://sipeed.com/licheepi4a | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `tenstorrent.com/hardware/blackhole` | https://tenstorrent.com/hardware/blackhole | 2026-09-07 | edge_hardware | no category fits: PCIe accelerator cards for workstations and servers. This category is boards and chips that run inference at the edge, and the taxonomy has no datacenter-accelerator category -- needs a category-proposal issue |
| `www.banana-pi.org/en/banana-pi-sbcs/175.html` | https://www.banana-pi.org/en/banana-pi-sbcs/175.html | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.beagleboard.org/boards/beaglebone-ai-64` | https://www.beagleboard.org/boards/beaglebone-ai-64 | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.blaize.com/products/` | https://www.blaize.com/products/ | 2026-09-07 | edge_hardware | vendor product index resolved but no product-level page did, so there is no single product identity to name on a row |
| `www.deepx.ai/dx-m1/` | https://www.deepx.ai/dx-m1/ | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.espressif.com/en/products/socs/esp32-p4` | https://www.espressif.com/en/products/socs/esp32-p4 | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.friendlyelec.com/index.php?route=product/product&product_id=292` | https://www.friendlyelec.com/index.php?route=product/product&product_id=292 | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.khadas.com/vim4` | https://www.khadas.com/vim4 | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/` | https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/ | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.nxp.com/products/eIQ-Neutron-NPU` | https://www.nxp.com/products/eIQ-Neutron-NPU | 2026-09-07 | edge_hardware | fetch did not complete (404); and eIQ Neutron is a licensable NPU IP core rather than a board or chip a reader can buy, so the boundary is doubtful too |
| `www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Ora` | https://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-AIpro.html | 2026-09-07 | edge_hardware | fetch did not complete (connection failed, then 404 on two further paths); not recorded as a measured absence -- the Orange Pi AIpro is a real board and comes back next sweep |
| `www.renesas.com/en/products/microcontrollers-microprocessors/rz-mpus/r` | https://www.renesas.com/en/products/microcontrollers-microprocessors/rz-mpus/rzv2h-quad-core-vision-ai-mpu-drp-ai3-accelerator-and-high-performance-real-time-processor | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |
| `www.rock-chips.com/a/en/products/RK35_Series/2024/0426/1711.html` | https://www.rock-chips.com/a/en/products/RK35_Series/2024/0426/1711.html | 2026-09-07 | edge_hardware | fetch did not complete (404 on two candidate paths for the RK3576 product page); not a measured absence |
| `www.seeedstudio.com/reComputer-J4012-p-5586.html` | https://www.seeedstudio.com/reComputer-J4012-p-5586.html | 2026-09-07 | edge_hardware | ambiguous identity: a carrier and enclosure around the NVIDIA Jetson Orin NX module, which is already the head product nvidia-jetson-orin-nx. Whether Seeed's reComputer is its own product or a packaging of that one is not settled by the page |
| `www.sophgo.com/sophon-u/product/introduce/bm1684x.html` | https://www.sophgo.com/sophon-u/product/introduce/bm1684x.html | 2026-09-07 | edge_hardware | no addressable identifier that is not a URL. The vendor page satisfies the registry schema through `homepage`, but this batch requires one of github / huggingface_model / huggingface_dataset / pypi / npm / crates / arxiv on every emitted row, and no vendor publishes a product-level repo, package or paper id for this board. Recorded with its page and fetch date so a later sweep can emit it if an identifier appears |

## Parked — below a disclosed retrieval cutoff (1185)

Returned by the queries above but outside the predeclared cutoff of every query that returned it,
so not triaged individually. Listed candidate by candidate, with the queries that returned it and
the floor that excluded it, so nothing in this batch is represented only by a count. A candidate
inside the floor of any one of its queries is not here — it is in one of the two tables above.

The nine candidates the second revision accepted below a floor are in this table now:
`data-prep-kit/data-prep-kit` (958 stars), `MinishLab/semhash` (963), `nolabs-ai/deepfabric`
(885), `magpie-align/magpie` (881 stars, last push 2025-03-17), `datadreamer-dev/DataDreamer`
(last push 2025-02-02), `BatsResearch/bonito` (829), `LiquidAI/LFM2.5-2.6B` (120,565 downloads),
`EleutherAI/gpt-j-6b` (261,799) and `LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct` (373,508). They are
real products and they come back the moment a sweep's declared floor admits them; what they are
not is a reason to keep an exception mechanism.

| candidate | source URL | fetched | returned by | cutoff that excluded it |
|---|---|---|---|---|
| `007revad/Synology_enable_Deduplication` | https://github.com/007revad/Synology_enable_Deduplication | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `0xNyk/awesome-agent-cortex` | https://github.com/0xNyk/awesome-agent-cortex | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `1195343015/nwputhesis` | https://github.com/1195343015/nwputhesis | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `1596941391qq/anything-to-md` | https://github.com/1596941391qq/anything-to-md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `425776024/nlpcda` | https://github.com/425776024/nlpcda | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `599yongyang/DatasetLoom` | https://github.com/599yongyang/DatasetLoom | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `666DZY666/micronet` | https://github.com/666DZY666/micronet | 2026-09-07 | `comp_t_quant`, `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `7satvik/sft-dataset-curator` | https://github.com/7satvik/sft-dataset-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `99-dpm/dedup-engine` | https://github.com/99-dpm/dedup-engine | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aai-institute/pyDVL` | https://github.com/aai-institute/pyDVL | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Adlik/Adlik` | https://github.com/Adlik/Adlik | 2026-09-07 | `comp_t_tensorcompiler`, `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `adobe-research/NoLiMa` | https://github.com/adobe-research/NoLiMa | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `adorad/adorad` | https://github.com/adorad/adorad | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aekanman/gaussian-blur` | https://github.com/aekanman/gaussian-blur | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AgaMiko/data-augmentation-review` | https://github.com/AgaMiko/data-augmentation-review | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agencyenterprise/PromptInject` | https://github.com/agencyenterprise/PromptInject | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Agent-Threat-Rule/agent-threat-rules` | https://github.com/Agent-Threat-Rule/agent-threat-rules | 2026-09-07 | `safe_t_promptinjection`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agentanywhere/shuddhi` | https://github.com/agentanywhere/shuddhi | 2026-09-07 | `dpt_dedup`, `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agentcontrol/agent-control` | https://github.com/agentcontrol/agent-control | 2026-09-07 | `safe_t_guardrails`, `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agkaminski/Pocket265` | https://github.com/agkaminski/Pocket265 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `agkaminski/Pocket65` | https://github.com/agkaminski/Pocket65 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Ahmad21Omar/Polyglot_Data_Filtering_and_Processing_Pipeline` | https://github.com/Ahmad21Omar/Polyglot_Data_Filtering_and_Processing_Pipeline | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ahmedkhn0611-hash/Tiny-GPT-on-Vortex-GPGPU-for-AMD-Alveo-U280` | https://github.com/ahmedkhn0611-hash/Tiny-GPT-on-Vortex-GPGPU-for-AMD-Alveo-U280 | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AIAnytime/Synthetic-Data-Generation-using-LLM` | https://github.com/AIAnytime/Synthetic-Data-Generation-using-LLM | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aiming-lab/AutoHarness` | https://github.com/aiming-lab/AutoHarness | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aipotheosis-labs/gate22` | https://github.com/aipotheosis-labs/gate22 | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aisa-group/PostTrainBench` | https://github.com/aisa-group/PostTrainBench | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `akav-labs/agentsentry-gateway` | https://github.com/akav-labs/agentsentry-gateway | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alasdairforsythe/tokenmonster` | https://github.com/alasdairforsythe/tokenmonster | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alelaguard/agentguards-plugins` | https://github.com/alelaguard/agentguards-plugins | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alex000kim/nsfw_data_scraper` | https://github.com/alex000kim/nsfw_data_scraper | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ALIA-Engineering/Molten` | https://github.com/ALIA-Engineering/Molten | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AliAmini93/Telecom-Churn-Analysis` | https://github.com/AliAmini93/Telecom-Churn-Analysis | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alibaba/anolisa` | https://github.com/alibaba/anolisa | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alibaba/BladeDISC` | https://github.com/alibaba/BladeDISC | 2026-09-07 | `comp_t_mlir`, `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alibaba/feathub` | https://github.com/alibaba/feathub | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alibaba/TePDist` | https://github.com/alibaba/TePDist | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AlienZhang1996/DH-CoT` | https://github.com/AlienZhang1996/DH-CoT | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Alihan26/data_curation_interface` | https://github.com/Alihan26/data_curation_interface | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `alpa-projects/alpa` | https://github.com/alpa-projects/alpa | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Amal-David/docingest` | https://github.com/Amal-David/docingest | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `andersy005/tvm-in-action` | https://github.com/andersy005/tvm-in-action | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `andresribeiro/nsfwjs-docker` | https://github.com/andresribeiro/nsfwjs-docker | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `andrewkchan/yalm` | https://github.com/andrewkchan/yalm | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AndySparks/sourceconvert` | https://github.com/AndySparks/sourceconvert | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `anilsathyan7/Portrait-Segmentation` | https://github.com/anilsathyan7/Portrait-Segmentation | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `anindex/note_model_opt` | https://github.com/anindex/note_model_opt | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `anlp-team/LTI_Neural_Navigator` | https://github.com/anlp-team/LTI_Neural_Navigator | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ant-research/awesome-mllm-guardrails` | https://github.com/ant-research/awesome-mllm-guardrails | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `apache/tvm-rfcs` | https://github.com/apache/tvm-rfcs | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `apache/tvm-vta` | https://github.com/apache/tvm-vta | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `api-evangelist/bespoke-labs` | https://github.com/api-evangelist/bespoke-labs | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `api-evangelist/rivos` | https://github.com/api-evangelist/rivos | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `api-evangelist/tenstorrent` | https://github.com/api-evangelist/tenstorrent | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `apifyforge/ai-training-data-curator` | https://github.com/apifyforge/ai-training-data-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `arcjet/arcjet-js` | https://github.com/arcjet/arcjet-js | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `arekusandr/last_layer` | https://github.com/arekusandr/last_layer | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `arm-education/Advanced-AI-Mixture-of-Experts` | https://github.com/arm-education/Advanced-AI-Mixture-of-Experts | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `arunava5764/USENIX_MIA` | https://github.com/arunava5764/USENIX_MIA | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Aryia-Behroziuan/neurons` | https://github.com/Aryia-Behroziuan/neurons | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `asamassekou10/ship-safe` | https://github.com/asamassekou10/ship-safe | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Asap7772/fewshot-preference-optimization` | https://github.com/Asap7772/fewshot-preference-optimization | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `astutic/Acharya` | https://github.com/astutic/Acharya | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Asymptote-Labs/agent-beacon` | https://github.com/Asymptote-Labs/agent-beacon | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `atfortes/LLMSymbolicReasoningBench` | https://github.com/atfortes/LLMSymbolicReasoningBench | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ATOM00blue/machine-learning-library` | https://github.com/ATOM00blue/machine-learning-library | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Atomic-man007/Awesome_Multimodel_LLM` | https://github.com/Atomic-man007/Awesome_Multimodel_LLM | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AutoGPTQ/AutoGPTQ` | https://github.com/AutoGPTQ/AutoGPTQ | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `awesome-mlops/awesome-ml-monitoring` | https://github.com/awesome-mlops/awesome-ml-monitoring | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `AXERA-TECH/ax-samples` | https://github.com/AXERA-TECH/ax-samples | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `aymanelrody/FlashMLA` | https://github.com/aymanelrody/FlashMLA | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Ayubjon/inject-radar` | https://github.com/Ayubjon/inject-radar | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `azamkhan5556/Cyber-Security-tool-for-LLM-based-Chatbots` | https://github.com/azamkhan5556/Cyber-Security-tool-for-LLM-based-Chatbots | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Azure/AI-in-a-Box` | https://github.com/Azure/AI-in-a-Box | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Azzedde/clever_searcher` | https://github.com/Azzedde/clever_searcher | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Babelscape/ALERT` | https://github.com/Babelscape/ALERT | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `backbay-labs/clawdstrike` | https://github.com/backbay-labs/clawdstrike | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `badursun/terlik.js` | https://github.com/badursun/terlik.js | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `baixianghuang/editing-attack` | https://github.com/baixianghuang/editing-attack | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bastio-ai/bastio` | https://github.com/bastio-ai/bastio | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `BatsResearch/bonito` | https://github.com/BatsResearch/bonito | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bayerf42/Lox68k` | https://github.com/bayerf42/Lox68k | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Baze-Bai/Zillusion` | https://github.com/Baze-Bai/Zillusion | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Bestselling-goliath423/turboquant_cutile` | https://github.com/Bestselling-goliath423/turboquant_cutile | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bl33h/productOfTwoVectors` | https://github.com/bl33h/productOfTwoVectors | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bl33h/pythagoreanTheorem` | https://github.com/bl33h/pythagoreanTheorem | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Blaspsoft/blasp` | https://github.com/Blaspsoft/blasp | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `BLKSerene/Wordless` | https://github.com/BLKSerene/Wordless | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `BlueFalconHD/apple_generative_model_safety_decrypted` | https://github.com/BlueFalconHD/apple_generative_model_safety_decrypted | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bnabis93/vision-language-examples` | https://github.com/bnabis93/vision-language-examples | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `BobMcDear/attorch` | https://github.com/BobMcDear/attorch | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `brainlife/ezbids` | https://github.com/brainlife/ezbids | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `brontoguana/krasis` | https://github.com/brontoguana/krasis | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `broxus/tycho` | https://github.com/broxus/tycho | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `buicongnguyen/NPU_sw_stack` | https://github.com/buicongnguyen/NPU_sw_stack | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bupticybee/FastLoRAChat` | https://github.com/bupticybee/FastLoRAChat | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Buyun-Liang/REALISTA` | https://github.com/Buyun-Liang/REALISTA | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Buyun-Liang/SECA` | https://github.com/Buyun-Liang/SECA | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `bytedance/byteir` | https://github.com/bytedance/byteir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `caichuanwang/OpenDocs` | https://github.com/caichuanwang/OpenDocs | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CALISKAN-EMRE/NSOSYAL` | https://github.com/CALISKAN-EMRE/NSOSYAL | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `can-lehmann/exprgrad` | https://github.com/can-lehmann/exprgrad | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cargo-limit/cargo-limit` | https://github.com/cargo-limit/cargo-limit | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CAS-SIAT-XinHai/CPsyCoun` | https://github.com/CAS-SIAT-XinHai/CPsyCoun | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cbaziotis/ekphrasis` | https://github.com/cbaziotis/ekphrasis | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CCCpan/chinese-sensitive-words-mcp` | https://github.com/CCCpan/chinese-sensitive-words-mcp | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `chaffybird56/riscv-soc` | https://github.com/chaffybird56/riscv-soc | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CHATS-lab/verbalized-sampling` | https://github.com/CHATS-lab/verbalized-sampling | 2026-09-07 | `dpt_synth`, `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `check-ai-labs/CorpusFlowAI` | https://github.com/check-ai-labs/CorpusFlowAI | 2026-09-07 | `dpt_pipeline` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `chrisliu298/awesome-llm-unlearning` | https://github.com/chrisliu298/awesome-llm-unlearning | 2026-09-07 | `safe_t_aisafety`, `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `clawsoftware/clawPDF` | https://github.com/clawsoftware/clawPDF | 2026-09-07 | `B_dpt_ocrpdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cleanlab/cleanlab-studio` | https://github.com/cleanlab/cleanlab-studio | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `clonio-dev/clonio-cli` | https://github.com/clonio-dev/clonio-cli | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `coderonion/awesome-cuda-and-hpc` | https://github.com/coderonion/awesome-cuda-and-hpc | 2026-09-07 | `comp_t_mlir`, `comp_t_triton`, `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `coderonion/awesome-llm-and-aigc` | https://github.com/coderonion/awesome-llm-and-aigc | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `coderonion/awesome-object-detection-datasets` | https://github.com/coderonion/awesome-object-detection-datasets | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `coderonion/zcuda` | https://github.com/coderonion/zcuda | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `collinear-ai/spider` | https://github.com/collinear-ai/spider | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Colton1skees/Dna` | https://github.com/Colton1skees/Dna | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `conradry/copy-paste-aug` | https://github.com/conradry/copy-paste-aug | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cordum-io/cordum` | https://github.com/cordum-io/cordum | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cornell-zhang/allo` | https://github.com/cornell-zhang/allo | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cortex1020/EvalLeak` | https://github.com/cortex1020/EvalLeak | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cosmo-wander-ai/cosmo-edge` | https://github.com/cosmo-wander-ai/cosmo-edge | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CoWork-OS/CoWork-OS` | https://github.com/CoWork-OS/CoWork-OS | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `credi-net/CrediText` | https://github.com/credi-net/CrediText | 2026-09-07 | `dpt_crawl` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CryptoAILab/JailbreakEval` | https://github.com/CryptoAILab/JailbreakEval | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cuevhv/mamma` | https://github.com/cuevhv/mamma | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cuga-project/cuga-agent` | https://github.com/cuga-project/cuga-agent | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cxcscmu/Craw4LLM` | https://github.com/cxcscmu/Craw4LLM | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `cxumol/promptmask` | https://github.com/cxumol/promptmask | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `CyberSunil/LLMVault` | https://github.com/CyberSunil/LLMVault | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `d1pakda5/awesome-llm-security-tool` | https://github.com/d1pakda5/awesome-llm-security-tool | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `d4em0n/exrop` | https://github.com/d4em0n/exrop | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `da2so/DA2Lite` | https://github.com/da2so/DA2Lite | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `danyuchn/pii-guard` | https://github.com/danyuchn/pii-guard | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `daochenzha/data-centric-AI` | https://github.com/daochenzha/data-centric-AI | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dapurv5/awesome-red-teaming-llms` | https://github.com/dapurv5/awesome-red-teaming-llms | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Darsh-Nandu/guardrails` | https://github.com/Darsh-Nandu/guardrails | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Data-Centric-AI-Community/awesome-data-centric-ai` | https://github.com/Data-Centric-AI-Community/awesome-data-centric-ai | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Data-Centric-AI-Community/awesome-python-for-data-science` | https://github.com/Data-Centric-AI-Community/awesome-python-for-data-science | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `data-prep-kit/data-prep-kit` | https://github.com/data-prep-kit/data-prep-kit | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `data-privacy-stack/presidio-research` | https://github.com/data-privacy-stack/presidio-research | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `datadreamer-dev/DataDreamer` | https://github.com/datadreamer-dev/DataDreamer | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `davesohamm/GPU-Benchmark` | https://github.com/davesohamm/GPU-Benchmark | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `david-palma/cuda-programming` | https://github.com/david-palma/cuda-programming | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DazzleML/comfyui-triton-and-sageattention-installer` | https://github.com/DazzleML/comfyui-triton-and-sageattention-installer | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dbaran0/datastream-curator` | https://github.com/dbaran0/datastream-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dcharlot-physicalai-bmi/ferric` | https://github.com/dcharlot-physicalai-bmi/ferric | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `deadbits/vigil-llm` | https://github.com/deadbits/vigil-llm | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `decionis/agent-safe-pipeline` | https://github.com/decionis/agent-safe-pipeline | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `declare-lab/resta` | https://github.com/declare-lab/resta | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `deepcam-cn/yolov5-face` | https://github.com/deepcam-cn/yolov5-face | 2026-09-07 | `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DemisEom/SpecAugment` | https://github.com/DemisEom/SpecAugment | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dengxianghua888-ops/ecoalign-forge` | https://github.com/dengxianghua888-ops/ecoalign-forge | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DFKHelper/token-goat` | https://github.com/DFKHelper/token-goat | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dhanushkumar-amk/GuardLayer` | https://github.com/dhanushkumar-amk/GuardLayer | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dharun36/webscraping-craw4ai` | https://github.com/dharun36/webscraping-craw4ai | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `diaa0516/data_curator` | https://github.com/diaa0516/data_curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `diego-ninja/sentinel` | https://github.com/diego-ninja/sentinel | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Digital-Dermatology/SelfClean` | https://github.com/Digital-Dermatology/SelfClean | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dipampaul17/AgentGuard` | https://github.com/dipampaul17/AgentGuard | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dmlc/nnvm` | https://github.com/dmlc/nnvm | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dmriding/kaio` | https://github.com/dmriding/kaio | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DobermanCore/Doberman-Core` | https://github.com/DobermanCore/Doberman-Core | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DocumindHQ/documind` | https://github.com/DocumindHQ/documind | 2026-09-07 | `B_dpt_ocrpdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `doofzoff/SIMURG` | https://github.com/doofzoff/SIMURG | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dortanes/curator.ai` | https://github.com/dortanes/curator.ai | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dpc/rdedup` | https://github.com/dpc/rdedup | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dqbd/tiktokenizer` | https://github.com/dqbd/tiktokenizer | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dronefreak/PromptScreen` | https://github.com/dronefreak/PromptScreen | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `DT42/BerryNet` | https://github.com/DT42/BerryNet | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `duncatzat/vigils` | https://github.com/duncatzat/vigils | 2026-09-07 | `B_safe_pii`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `duoan/mega-data-factory` | https://github.com/duoan/mega-data-factory | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `duriantaco/skylos` | https://github.com/duriantaco/skylos | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dusty-nv/NanoLLM` | https://github.com/dusty-nv/NanoLLM | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `dvmazur/mixtral-offloading` | https://github.com/dvmazur/mixtral-offloading | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `EasyJailbreak/EasyJailbreak` | https://github.com/EasyJailbreak/EasyJailbreak | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ed766/ed766` | https://github.com/ed766/ed766 | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `EdyVision/pii-codex` | https://github.com/EdyVision/pii-codex | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `eellak/glossAPI` | https://github.com/eellak/glossAPI | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ego/awesome-mojo` | https://github.com/ego/awesome-mojo | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ehsanmok/tvm-rust` | https://github.com/ehsanmok/tvm-rust | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ehtishammubarik/websieve` | https://github.com/ehtishammubarik/websieve | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ElGap/ai-curator-opencode` | https://github.com/ElGap/ai-curator-opencode | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `embedeep/Free-TPU` | https://github.com/embedeep/Free-TPU | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `embedeep/FREE-TPU-V3plus-for-FPGA` | https://github.com/embedeep/FREE-TPU-V3plus-for-FPGA | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `emiliaprotocol/emilia-protocol` | https://github.com/emiliaprotocol/emilia-protocol | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `emmtrix/emx-onnx-cgen` | https://github.com/emmtrix/emx-onnx-cgen | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `EMventura/TokenTurbine` | https://github.com/EMventura/TokenTurbine | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `encord-team/encord-active` | https://github.com/encord-team/encord-active | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `enoch3712/ExtractThinker` | https://github.com/enoch3712/ExtractThinker | 2026-09-07 | `B_dpt_ocrpdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `eqtylab/cupcake` | https://github.com/eqtylab/cupcake | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `eugeneyan/applied-ml` | https://github.com/eugeneyan/applied-ml | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `everx-labs/TVM-Solidity-Compiler` | https://github.com/everx-labs/TVM-Solidity-Compiler | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ext-sakamoro/ALICE-LLM` | https://github.com/ext-sakamoro/ALICE-LLM | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `EzgiKorkmaz/adversarial-reinforcement-learning` | https://github.com/EzgiKorkmaz/adversarial-reinforcement-learning | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `faiyazabdullah/JailbreakTracer` | https://github.com/faiyazabdullah/JailbreakTracer | 2026-09-07 | `dpt_synth`, `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `fcakyon/content-moderation-deep-learning` | https://github.com/fcakyon/content-moderation-deep-learning | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `fcorbelli/zpaqfranz` | https://github.com/fcorbelli/zpaqfranz | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `feathr-ai/feathr` | https://github.com/feathr-ai/feathr | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `featureform/featureform` | https://github.com/featureform/featureform | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ferro-labs/ai-gateway` | https://github.com/ferro-labs/ai-gateway | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `FIIT-IAU/IAU-course` | https://github.com/FIIT-IAU/IAU-course | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `firmai/deltapy` | https://github.com/firmai/deltapy | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `flatmax/buildroot.rockchip` | https://github.com/flatmax/buildroot.rockchip | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Floe-Labs/floe-guard` | https://github.com/Floe-Labs/floe-guard | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `fluxions-ai/vui` | https://github.com/fluxions-ai/vui | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `flyrank-bih/flyscrape` | https://github.com/flyrank-bih/flyscrape | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `fmh66/kernel-opt-agent` | https://github.com/fmh66/kernel-opt-agent | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ForestHubAI/boardsmith` | https://github.com/ForestHubAI/boardsmith | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `FoundationVision/UniTok` | https://github.com/FoundationVision/UniTok | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `framerslab/agentos` | https://github.com/framerslab/agentos | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `frankmtetwa/thermophysical-curator` | https://github.com/frankmtetwa/thermophysical-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `FunnySaltyFish/Better-Ruozhiba` | https://github.com/FunnySaltyFish/Better-Ruozhiba | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `FunnySaltyFish/bilibili_comments_crawl` | https://github.com/FunnySaltyFish/bilibili_comments_crawl | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GannaAsaad/FRAUDX-Intelligent-Credit-Card-Fraud-Detection-Using-AI-LLM` | https://github.com/GannaAsaad/FRAUDX-Intelligent-Credit-Card-Fraud-Detection-Using-AI-LLM | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `gavinlyonsrepo/Display_Lib_RPI` | https://github.com/gavinlyonsrepo/Display_Lib_RPI | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `georgebuilds/anneal` | https://github.com/georgebuilds/anneal | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `getagentseal/agentseal` | https://github.com/getagentseal/agentseal | 2026-09-07 | `safe_t_promptinjection`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `getmetamapper/metamapper` | https://github.com/getmetamapper/metamapper | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `getomni-ai/zerox` | https://github.com/getomni-ai/zerox | 2026-09-07 | `B_dpt_ocrpdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ggwhite/go-masker` | https://github.com/ggwhite/go-masker | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GiovanniPasq/chunky` | https://github.com/GiovanniPasq/chunky | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GirishVerm/cuda-kernels` | https://github.com/GirishVerm/cuda-kernels | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `glayzzle/php-parser` | https://github.com/glayzzle/php-parser | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `glincker/glin-profanity` | https://github.com/glincker/glin-profanity | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `globalbao/awesome-azure-policy` | https://github.com/globalbao/awesome-azure-policy | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GokuMohandas/mlops-course` | https://github.com/GokuMohandas/mlops-course | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `google-ai-edge/litert-samples` | https://github.com/google-ai-edge/litert-samples | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `google/heir` | https://github.com/google/heir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `google/jsir` | https://github.com/google/jsir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GoogleCloudPlatform/dlp-dataflow-deidentification` | https://github.com/GoogleCloudPlatform/dlp-dataflow-deidentification | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `goru001/inltk` | https://github.com/goru001/inltk | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `goshs-labs/goshs` | https://github.com/goshs-labs/goshs | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Govcraft/rust-docs-mcp-server` | https://github.com/Govcraft/rust-docs-mcp-server | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `gpu-mode/reference-kernels` | https://github.com/gpu-mode/reference-kernels | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GramosoftAI/GcrawlAI` | https://github.com/GramosoftAI/GcrawlAI | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GrayboxTech/weightslab` | https://github.com/GrayboxTech/weightslab | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `GURPREETKAURJETHRA/Synthetic-Data-Generation-using-LLM` | https://github.com/GURPREETKAURJETHRA/Synthetic-Data-Generation-using-LLM | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `H0NEYP0T-466/dataset-generator` | https://github.com/H0NEYP0T-466/dataset-generator | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `h5i-dev/h5i` | https://github.com/h5i-dev/h5i | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hailo-ai/hailo_model_zoo` | https://github.com/hailo-ai/hailo_model_zoo | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `haiyan-ai-lab/adaptive-moe-inference` | https://github.com/haiyan-ai-lab/adaptive-moe-inference | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Hamster-Prime/Smart_Group_Bot` | https://github.com/Hamster-Prime/Smart_Group_Bot | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `HanXinzi-AI/awesome-computer-vision-resources` | https://github.com/HanXinzi-AI/awesome-computer-vision-resources | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `haoran-ni/ralph-loop-optimizer` | https://github.com/haoran-ni/ralph-loop-optimizer | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hashgraph-online/hol-guard` | https://github.com/hashgraph-online/hol-guard | 2026-09-07 | `safe_t_promptinjection`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `HawkClaws/pdf2markdown4llm` | https://github.com/HawkClaws/pdf2markdown4llm | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `HeadyZhang/agent-audit` | https://github.com/HeadyZhang/agent-audit | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `heixiaopengyou/TINY-ML-for-FOC-of-PMSM-20092024` | https://github.com/heixiaopengyou/TINY-ML-for-FOC-of-PMSM-20092024 | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Helldez/BigMoeOnEdge` | https://github.com/Helldez/BigMoeOnEdge | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hendrycks/ethics` | https://github.com/hendrycks/ethics | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hermes-labs-ai/lintlang` | https://github.com/hermes-labs-ai/lintlang | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hidet-org/hidet` | https://github.com/hidet-org/hidet | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hivellm/transmutation` | https://github.com/hivellm/transmutation | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hngondoki/ge_sheng_guardrails_project` | https://github.com/hngondoki/ge_sheng_guardrails_project | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `HoloClean/holoclean` | https://github.com/HoloClean/holoclean | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `HowieHwong/DataGen` | https://github.com/HowieHwong/DataGen | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `HowieHwong/TrustLLM` | https://github.com/HowieHwong/TrustLLM | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `HPMLL/BurstGPT` | https://github.com/HPMLL/BurstGPT | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `huawei-noah/Pretrained-Language-Model` | https://github.com/huawei-noah/Pretrained-Language-Model | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Humaam-04-06/CastNeuralAI` | https://github.com/Humaam-04-06/CastNeuralAI | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hurry211/ai-assisted-gpu-optimization` | https://github.com/hurry211/ai-assisted-gpu-optimization | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hurry211/cuda-performance-lab` | https://github.com/hurry211/cuda-performance-lab | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hurry211/gpu-operator-optimization` | https://github.com/hurry211/gpu-operator-optimization | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `husnuOzaltun/nlp-data-preprocessing` | https://github.com/husnuOzaltun/nlp-data-preprocessing | 2026-09-07 | `dpt_quality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hwdsl2/docker-docling` | https://github.com/hwdsl2/docker-docling | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Hyland/DocumentFilters` | https://github.com/Hyland/DocumentFilters | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `hyunwoongko/nanoRLHF` | https://github.com/hyunwoongko/nanoRLHF | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `IAAR-Shanghai/UHGEval` | https://github.com/IAAR-Shanghai/UHGEval | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `IAAR-Shanghai/xFinder` | https://github.com/IAAR-Shanghai/xFinder | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `iaintheardofu/rocm-scribe` | https://github.com/iaintheardofu/rocm-scribe | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `iamwonseokchoi/synthetic_data_generation_DPO` | https://github.com/iamwonseokchoi/synthetic_data_generation_DPO | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Idun-Group/idun-agent-platform` | https://github.com/Idun-Group/idun-agent-platform | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ifilot/bytecradle-6502` | https://github.com/ifilot/bytecradle-6502 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ikawaha/kagome` | https://github.com/ikawaha/kagome | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `imgly/background-removal-js` | https://github.com/imgly/background-removal-js | 2026-09-07 | `comp_t_onnx` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `industrialtablet/qt-everywhere-src-5.14.2-cross-compile-for-RK3566-RK3568-RK3588` | https://github.com/industrialtablet/qt-everywhere-src-5.14.2-cross-compile-for-RK3566-RK3568-RK3588 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `industrialtablet/RK3576S-RK3576-RK3588-Tablet-Development-Board` | https://github.com/industrialtablet/RK3576S-RK3576-RK3588-Tablet-Development-Board | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `industrialtablet/RK3588-POE-SBC` | https://github.com/industrialtablet/RK3588-POE-SBC | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `InectGit/pdf-to-markdown` | https://github.com/InectGit/pdf-to-markdown | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `insight-platform/Savant` | https://github.com/insight-platform/Savant | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `IntelLabs/nlp-architect` | https://github.com/IntelLabs/nlp-architect | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `irahardianto/qurio` | https://github.com/irahardianto/qurio | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ise-uiuc/nnsmith` | https://github.com/ise-uiuc/nnsmith | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ishwariwakchaure5/medishield-safety-engine` | https://github.com/ishwariwakchaure5/medishield-safety-engine | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `iw4p/url-to-markdown` | https://github.com/iw4p/url-to-markdown | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `iwangjian/TopDial` | https://github.com/iwangjian/TopDial | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `J-Aamir/Domain-Specific-GPT2-Pretraining-Australian-Legal-Corpus` | https://github.com/J-Aamir/Domain-Specific-GPT2-Pretraining-Australian-Legal-Corpus | 2026-09-07 | `dpt_pipeline` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `j2kun/mlir-tutorial` | https://github.com/j2kun/mlir-tutorial | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `J535D165/data-matching-software` | https://github.com/J535D165/data-matching-software | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `J535D165/recordlinkage` | https://github.com/J535D165/recordlinkage | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module` | https://github.com/JafarAkhondali/acer-predator-turbo-and-rgb-keyboard-linux-module | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jasonwei20/eda_nlp` | https://github.com/jasonwei20/eda_nlp | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Jean-Regis-M/AegisLLM` | https://github.com/Jean-Regis-M/AegisLLM | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jflex-de/jflex` | https://github.com/jflex-de/jflex | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Intel_4004_Single_Board_Computer` | https://github.com/jim11662418/Intel_4004_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Intel_8008_Single_Board_Computer` | https://github.com/jim11662418/Intel_8008_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Intel_8048_Single_Board_Computer` | https://github.com/jim11662418/Intel_8048_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Intel_8080_Single_Board_Computer` | https://github.com/jim11662418/Intel_8080_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Mostek_MK3850_Single_Board_Computer` | https://github.com/jim11662418/Mostek_MK3850_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Motorola_MC14500B_Single_Board_Computer` | https://github.com/jim11662418/Motorola_MC14500B_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jim11662418/Signetics_2650_Single_Board_Computer` | https://github.com/jim11662418/Signetics_2650_Single_Board_Computer | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jina-ai/clip-as-service` | https://github.com/jina-ai/clip-as-service | 2026-09-07 | `comp_t_onnx` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Jing-yilin/E2M` | https://github.com/Jing-yilin/E2M | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jjang-ai/mlxstudio` | https://github.com/jjang-ai/mlxstudio | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jmerelnyc/crawl-rag` | https://github.com/jmerelnyc/crawl-rag | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Joey0122/Mini-GPU-Inference-Engine` | https://github.com/Joey0122/Mini-GPU-Inference-Engine | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JonathanSalwan/Tigress_protection` | https://github.com/JonathanSalwan/Tigress_protection | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jorgemunozl/Synthetic-Data` | https://github.com/jorgemunozl/Synthetic-Data | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Jos-Ven/A-smart-home-in-Forth` | https://github.com/Jos-Ven/A-smart-home-in-Forth | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `jpjacobpadilla/SearchAI` | https://github.com/jpjacobpadilla/SearchAI | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `js-lee-AI/awesome-llm-agent-papers` | https://github.com/js-lee-AI/awesome-llm-agent-papers | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `juanmanueldaza/linkedin2md` | https://github.com/juanmanueldaza/linkedin2md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JulietMirambo/Units_of_Measure_Harmonization-intelligence-platform` | https://github.com/JulietMirambo/Units_of_Measure_Harmonization-intelligence-platform | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JuneYaooo/self-media-compliance-review` | https://github.com/JuneYaooo/self-media-compliance-review | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Justin-Ju-0413/riscv_cnn_accelerator` | https://github.com/Justin-Ju-0413/riscv_cnn_accelerator | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Justin0504/Aegis` | https://github.com/Justin0504/Aegis | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `justinbt1/Akin` | https://github.com/justinbt1/Akin | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `JustVugg/distillery` | https://github.com/JustVugg/distillery | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kagandikmen/clairvoyant` | https://github.com/kagandikmen/clairvoyant | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KaleabTessera/Image-Convolution-Using-CUDA-C` | https://github.com/KaleabTessera/Image-Convolution-Using-CUDA-C | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KalebSabo/study-notes` | https://github.com/KalebSabo/study-notes | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kamalrss88/FlashMLA` | https://github.com/kamalrss88/FlashMLA | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Kare0638/paged-attention-decode` | https://github.com/Kare0638/paged-attention-decode | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kendryte/nncase` | https://github.com/kendryte/nncase | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kennethleungty/Failed-ML` | https://github.com/kennethleungty/Failed-ML | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KenObata/distributed-curator` | https://github.com/KenObata/distributed-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kevinadhiguna/dqlab-career-track` | https://github.com/kevinadhiguna/dqlab-career-track | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KeyValueSoftwareSystems/agent-opfor` | https://github.com/KeyValueSoftwareSystems/agent-opfor | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Kirtan132003/ada-use` | https://github.com/Kirtan132003/ada-use | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kisugez/moderator` | https://github.com/kisugez/moderator | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `klezVirus/inceptor` | https://github.com/klezVirus/inceptor | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `klouddb/klouddbshield` | https://github.com/klouddb/klouddbshield | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KOKOSde/localmod` | https://github.com/KOKOSde/localmod | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Kronbii/thermal-super-resolution` | https://github.com/Kronbii/thermal-super-resolution | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `kruturaj-18/Newsy--News-Curator` | https://github.com/kruturaj-18/Newsy--News-Curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KuiChi-x/reverseloom` | https://github.com/KuiChi-x/reverseloom | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `KylinMountain/markify` | https://github.com/KylinMountain/markify | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lambdaclass/concrete` | https://github.com/lambdaclass/concrete | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lambdamikel/picoram2090` | https://github.com/lambdamikel/picoram2090 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `larq/compute-engine` | https://github.com/larq/compute-engine | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lasso-security/mcp-gateway` | https://github.com/lasso-security/mcp-gateway | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lattice-ai/Compressed-DNNs-Forget` | https://github.com/lattice-ai/Compressed-DNNs-Forget | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `LaureBerti/Learn2Clean` | https://github.com/LaureBerti/Learn2Clean | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `leeroopedia/workflow-nvidia-nemo-curator-text-curation-pipeline` | https://github.com/leeroopedia/workflow-nvidia-nemo-curator-text-curation-pipeline | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `LeightonSec/ai-firewall` | https://github.com/LeightonSec/ai-firewall | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `leodevbro/vscode-blockman` | https://github.com/leodevbro/vscode-blockman | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `leoneversberg/pdf2md_llm` | https://github.com/leoneversberg/pdf2md_llm | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Lexsi-Labs/CuratorKIT` | https://github.com/Lexsi-Labs/CuratorKIT | 2026-09-07 | `dpt_synth`, `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lh0x00/docsifer` | https://github.com/lh0x00/docsifer | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Libr-AI/OpenRedTeaming` | https://github.com/Libr-AI/OpenRedTeaming | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lindera/lindera` | https://github.com/lindera/lindera | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lingo-db/lingo-db` | https://github.com/lingo-db/lingo-db | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lionsoul2014/friso` | https://github.com/lionsoul2014/friso | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `LirongWu/awesome-graph-self-supervised-learning` | https://github.com/LirongWu/awesome-graph-self-supervised-learning | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Littleboy1004/CrispMiner` | https://github.com/Littleboy1004/CrispMiner | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `liu00222/Open-Prompt-Injection` | https://github.com/liu00222/Open-Prompt-Injection | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ljubomirj/ChEMBLdb-query` | https://github.com/ljubomirj/ChEMBLdb-query | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `localai-org/privacy-filter.cpp` | https://github.com/localai-org/privacy-filter.cpp | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lonerzee/redteam-llm-lab` | https://github.com/lonerzee/redteam-llm-lab | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lovit/soynlp` | https://github.com/lovit/soynlp | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lsds/Tempo` | https://github.com/lsds/Tempo | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `luban-agi/Awesome-Domain-LLM` | https://github.com/luban-agi/Awesome-Domain-LLM | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lucasjinreal/yolov7_d2` | https://github.com/lucasjinreal/yolov7_d2 | 2026-09-07 | `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lucasmartins-ai/lcc` | https://github.com/lucasmartins-ai/lcc | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lucassa3/PEGASOS-SVM-CLASSIFIER` | https://github.com/lucassa3/PEGASOS-SVM-CLASSIFIER | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `luckyPipewrench/pipelock` | https://github.com/luckyPipewrench/pipelock | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lusinlu/gradient-variance-loss` | https://github.com/lusinlu/gradient-variance-loss | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `lydell/js-tokens` | https://github.com/lydell/js-tokens | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MadrasLe/ETL_DatasetNLP` | https://github.com/MadrasLe/ETL_DatasetNLP | 2026-09-07 | `dpt_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MadrasLe/MegaGemm` | https://github.com/MadrasLe/MegaGemm | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `magpie-align/magpie` | https://github.com/magpie-align/magpie | 2026-09-07 | `dpt_synth`, `dpt_t_synthetic`, `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mantisfury/ArkhamMirror` | https://github.com/mantisfury/ArkhamMirror | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `markson14/FaceRecognitionCpp` | https://github.com/markson14/FaceRecognitionCpp | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `marmik28/Web-Crawler-Python` | https://github.com/marmik28/Web-Crawler-Python | 2026-09-07 | `dpt_crawl` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mathewsanders/Mustard` | https://github.com/mathewsanders/Mustard | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mattilyra/LSH` | https://github.com/mattilyra/LSH | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MaxMLang/pytector` | https://github.com/MaxMLang/pytector | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MaxXSoft/Bossa` | https://github.com/MaxXSoft/Bossa | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mbrukman/curator-evals` | https://github.com/mbrukman/curator-evals | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mcsorkun/AqSolDB` | https://github.com/mcsorkun/AqSolDB | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mddunlap924/PII-Detection` | https://github.com/mddunlap924/PII-Detection | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `meet244/Intelligent-PDF` | https://github.com/meet244/Intelligent-PDF | 2026-09-07 | `dpt_docparse` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MegEngine/MegCC` | https://github.com/MegEngine/MegCC | 2026-09-07 | `comp_t_mlir`, `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Megvii-BaseDetection/YOLOX` | https://github.com/Megvii-BaseDetection/YOLOX | 2026-09-07 | `comp_t_onnx`, `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MelihGulum/Comprehensive-Data-Science-AI-Project-Portfolio` | https://github.com/MelihGulum/Comprehensive-Data-Science-AI-Project-Portfolio | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mengysun/DataParasite` | https://github.com/mengysun/DataParasite | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mensfeld/code-on-incus` | https://github.com/mensfeld/code-on-incus | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `merrymercy/awesome-tensor-compilers` | https://github.com/merrymercy/awesome-tensor-compilers | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `merrymercy/tvm-mali` | https://github.com/merrymercy/tvm-mali | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `meta-pytorch/tritonparse` | https://github.com/meta-pytorch/tritonparse | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mgeeky/Penetration-Testing-Tools` | https://github.com/mgeeky/Penetration-Testing-Tools | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mhamidjamil/orangepi` | https://github.com/mhamidjamil/orangepi | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `microsoft/Build26-LAB520-get-started-with-models-in-microsoft-foundry-to-build-ai-apps` | https://github.com/microsoft/Build26-LAB520-get-started-with-models-in-microsoft-foundry-to-build-ai-apps | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `microsoft/MMdnn` | https://github.com/microsoft/MMdnn | 2026-09-07 | `comp_t_onnx` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `microsoft/monitors4codegen` | https://github.com/microsoft/monitors4codegen | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `microsoft/nnscaler` | https://github.com/microsoft/nnscaler | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MigoXLab/awesome-data-quality` | https://github.com/MigoXLab/awesome-data-quality | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mikeroyal/LLVM-Guide` | https://github.com/mikeroyal/LLVM-Guide | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Mingye-Lu/AgenticCrawler` | https://github.com/Mingye-Lu/AgenticCrawler | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MinishLab/semhash` | https://github.com/MinishLab/semhash | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MiquelNasarre/macrograd` | https://github.com/MiquelNasarre/macrograd | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mit-han-lab/once-for-all` | https://github.com/mit-han-lab/once-for-all | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mit-han-lab/tiny-training` | https://github.com/mit-han-lab/tiny-training | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MIT-RLX/rlx-models` | https://github.com/MIT-RLX/rlx-models | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mkbula/HideMyData` | https://github.com/mkbula/HideMyData | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mlc-ai/web-stable-diffusion` | https://github.com/mlc-ai/web-stable-diffusion | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mlir-rs/melior` | https://github.com/mlir-rs/melior | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mmsaeed509/bspwm-dots` | https://github.com/mmsaeed509/bspwm-dots | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `modaic-ai/modaic` | https://github.com/modaic-ai/modaic | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ModelEngine-Group/unified-cache-management` | https://github.com/ModelEngine-Group/unified-cache-management | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `moonshine-ai/useful-transformers` | https://github.com/moonshine-ai/useful-transformers | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mostly-ai/mostlyai` | https://github.com/mostly-ai/mostlyai | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `MrinmoiHossain/Udacity-Intel-Edge-AI-for-IoT-Developers-Nanodegree` | https://github.com/MrinmoiHossain/Udacity-Intel-Edge-AI-for-IoT-Developers-Nanodegree | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mrtnetwork/On_chain` | https://github.com/mrtnetwork/On_chain | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `msnh2012/Msnhnet` | https://github.com/msnh2012/Msnhnet | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mturac/promptguard` | https://github.com/mturac/promptguard | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mufeedvh/moonwalk` | https://github.com/mufeedvh/moonwalk | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mughalhere/prompt-protection` | https://github.com/mughalhere/prompt-protection | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `mukul975/mcp-web-scrape` | https://github.com/mukul975/mcp-web-scrape | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NabilAlouani/INSPIRe_` | https://github.com/NabilAlouani/INSPIRe_ | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nareshns2004/custom-cuda-fused-attention-triton` | https://github.com/nareshns2004/custom-cuda-fused-attention-triton | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `natalimuca/jailbreak-activation-detection` | https://github.com/natalimuca/jailbreak-activation-detection | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `neo-chem/awesome-chemical-data` | https://github.com/neo-chem/awesome-chemical-data | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NervanaSystems/he-transformer` | https://github.com/NervanaSystems/he-transformer | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NervanaSystems/ngraph` | https://github.com/NervanaSystems/ngraph | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `netinvent/npbackup` | https://github.com/netinvent/npbackup | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `neuralmagic/deepsparse` | https://github.com/neuralmagic/deepsparse | 2026-09-07 | `comp_t_quant` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NevermindNilas/TheAnimeScripter` | https://github.com/NevermindNilas/TheAnimeScripter | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nicolas-hbt/pygraft` | https://github.com/nicolas-hbt/pygraft | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `niieani/gpt-tokenizer` | https://github.com/niieani/gpt-tokenizer | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nizos/probity` | https://github.com/nizos/probity | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nkito/i960_sbc` | https://github.com/nkito/i960_sbc | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NNgen/nngen` | https://github.com/NNgen/nngen | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `no-context/moo` | https://github.com/no-context/moo | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `node9-ai/node9-proxy` | https://github.com/node9-ai/node9-proxy | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nolabs-ai/deepfabric` | https://github.com/nolabs-ai/deepfabric | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NotPunchnox/rkllama` | https://github.com/NotPunchnox/rkllama | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NTNU-HPC-Lab/BAT` | https://github.com/NTNU-HPC-Lab/BAT | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `nucleuscloud/neosync` | https://github.com/nucleuscloud/neosync | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NVIDIA-AI-IOT/torch2trt` | https://github.com/NVIDIA-AI-IOT/torch2trt | 2026-09-07 | `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NVIDIA-ISAAC-ROS/isaac_ros_object_detection` | https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_object_detection | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NVIDIA/SkillEvaluator` | https://github.com/NVIDIA/SkillEvaluator | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `NVIDIA/tilus` | https://github.com/NVIDIA/tilus | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OAID/AutoKernel` | https://github.com/OAID/AutoKernel | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OAID/Tengine` | https://github.com/OAID/Tengine | 2026-09-07 | `comp_t_onnx`, `edge_t_npu`, `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ojasviii14/rag-crawler_Ojasvi` | https://github.com/ojasviii14/rag-crawler_Ojasvi | 2026-09-07 | `dpt_crawl` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Okerew/larkos` | https://github.com/Okerew/larkos | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `oneclickvirt/oneclickvirt` | https://github.com/oneclickvirt/oneclickvirt | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `onejune2018/Awesome-LLM-Eval` | https://github.com/onejune2018/Awesome-LLM-Eval | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `onnx/ir-py` | https://github.com/onnx/ir-py | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `onnx/turnkeyml` | https://github.com/onnx/turnkeyml | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `onyx-dot-app/EnterpriseRAG-Bench` | https://github.com/onyx-dot-app/EnterpriseRAG-Bench | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `open-bias/open-bias` | https://github.com/open-bias/open-bias | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `open-korean-text/open-korean-text` | https://github.com/open-korean-text/open-korean-text | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `open-mmlab/mmdeploy` | https://github.com/open-mmlab/mmdeploy | 2026-09-07 | `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `openarsenalspecs/IoT` | https://github.com/openarsenalspecs/IoT | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `opendilab/DI-hpc` | https://github.com/opendilab/DI-hpc | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OpenLMLab/MOSS-RLHF` | https://github.com/OpenLMLab/MOSS-RLHF | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OpenSparX/MasterAgent` | https://github.com/OpenSparX/MasterAgent | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OpenTradeOSS/OpenTrade` | https://github.com/OpenTradeOSS/OpenTrade | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `OPUSLab/SANTA` | https://github.com/OPUSLab/SANTA | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Oqura-ai/local-datagen-cli` | https://github.com/Oqura-ai/local-datagen-cli | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ot-triton-lab/flash-sinkhorn` | https://github.com/ot-triton-lab/flash-sinkhorn | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PacificAI/langtest` | https://github.com/PacificAI/langtest | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PaddlePaddle/Anakin` | https://github.com/PaddlePaddle/Anakin | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PaddlePaddle/VisualDL` | https://github.com/PaddlePaddle/VisualDL | 2026-09-07 | `comp_t_onnx` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `paladini/harness-score` | https://github.com/paladini/harness-score | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pangu-Immortal/MagicWX` | https://github.com/Pangu-Immortal/MagicWX | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pantheon-Security/medusa` | https://github.com/Pantheon-Security/medusa | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `paolodalprato/pymupdf4llm-gui` | https://github.com/paolodalprato/pymupdf4llm-gui | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Paperspace/DataAugmentationForObjectDetection` | https://github.com/Paperspace/DataAugmentationForObjectDetection | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `parameterlab/leaky_thoughts` | https://github.com/parameterlab/leaky_thoughts | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `parasj/checkmate` | https://github.com/parasj/checkmate | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `parasj/contracode` | https://github.com/parasj/contracode | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `parinzee/seed-free-synthetic-instruct` | https://github.com/parinzee/seed-free-synthetic-instruct | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ParsBench/PersianSyntheticData` | https://github.com/ParsBench/PersianSyntheticData | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `passpartout42/ConvertRgbToHsv-Cuda` | https://github.com/passpartout42/ConvertRgbToHsv-Cuda | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `passpartout42/SobelFilter-Cuda` | https://github.com/passpartout42/SobelFilter-Cuda | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `patelvishwa112/fallback-curator` | https://github.com/patelvishwa112/fallback-curator | 2026-09-07 | `dpt_q_curator` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `patrickfleith/datafast` | https://github.com/patrickfleith/datafast | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pegainfer-project/pegainfer` | https://github.com/pegainfer-project/pegainfer | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pegasi-ai/reins` | https://github.com/pegasi-ai/reins | 2026-09-07 | `safe_t_aisafety`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pelochus/ezrknpu` | https://github.com/Pelochus/ezrknpu | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pengfei-Yang01/RLShield` | https://github.com/Pengfei-Yang01/RLShield | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PennLINC/CuBIDS` | https://github.com/PennLINC/CuBIDS | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PennyLaneAI/catalyst` | https://github.com/PennyLaneAI/catalyst | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `peremartra/Rearchitecting-LLMs` | https://github.com/peremartra/Rearchitecting-LLMs | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `perplexityai/numbat` | https://github.com/perplexityai/numbat | 2026-09-07 | `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pg-space/panspace` | https://github.com/pg-space/panspace | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `philterd/phileas` | https://github.com/philterd/phileas | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Picovoice/speech-to-text-benchmark` | https://github.com/Picovoice/speech-to-text-benchmark | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PKU-YuanGroup/Hallucination-Attack` | https://github.com/PKU-YuanGroup/Hallucination-Attack | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pliron-org/pliron` | https://github.com/pliron-org/pliron | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `polm/fugashi` | https://github.com/polm/fugashi | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `powerserve-project/PowerServe` | https://github.com/powerserve-project/PowerServe | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ppogg/YOLOv5-Lite` | https://github.com/ppogg/YOLOv5-Lite | 2026-09-07 | `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ppomes/myanon` | https://github.com/ppomes/myanon | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pradeepanpp/jailbreak-detection-system` | https://github.com/pradeepanpp/jailbreak-detection-system | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PranabNandy/BeagleBone-Black-Platform-Bring-Up` | https://github.com/PranabNandy/BeagleBone-Black-Platform-Bring-Up | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PrismorSec/prismor` | https://github.com/PrismorSec/prismor | 2026-09-07 | `safe_t_promptinjection`, `safe_t_aisafety`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `privacera/paig` | https://github.com/privacera/paig | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `protectai/rebuff` | https://github.com/protectai/rebuff | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Prysai/Prysai-LLM-Playbook` | https://github.com/Prysai/Prysai-LLM-Playbook | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PS-003R32/AegisDominus` | https://github.com/PS-003R32/AegisDominus | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PSAL-POSTECH/ONNXim` | https://github.com/PSAL-POSTECH/ONNXim | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `PSAL-POSTECH/PyTorchSim` | https://github.com/PSAL-POSTECH/PyTorchSim | 2026-09-07 | `comp_t_tensorcompiler`, `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pulp-platform/picobello` | https://github.com/pulp-platform/picobello | 2026-09-07 | `edge_t_riscv_ai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `pylint-dev/astroid` | https://github.com/pylint-dev/astroid | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Pylir/Pylir` | https://github.com/Pylir/Pylir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Qengineering/YoloV5-NPU` | https://github.com/Qengineering/YoloV5-NPU | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Qengineering/YoloV8-NPU` | https://github.com/Qengineering/YoloV8-NPU | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `qijianpeng/awesome-edge-computing` | https://github.com/qijianpeng/awesome-edge-computing | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `quqxui/Awesome-LLM4IE-Papers` | https://github.com/quqxui/Awesome-LLM4IE-Papers | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `QWED-AI/qwed-verification` | https://github.com/QWED-AI/qwed-verification | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `RaduPetrila-dev/nano-infer` | https://github.com/RaduPetrila-dev/nano-infer | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `raintree-technology/docpull` | https://github.com/raintree-technology/docpull | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Ramshankar07/CUDA-llama3.1-inference` | https://github.com/Ramshankar07/CUDA-llama3.1-inference | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Ratila1/JGuardrails` | https://github.com/Ratila1/JGuardrails | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `RD17/ambar` | https://github.com/RD17/ambar | 2026-09-07 | `B_dpt_ocrpdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Red-Hat-AI-Innovation-Team/sdg_hub` | https://github.com/Red-Hat-AI-Innovation-Team/sdg_hub | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `redhuntlabs/Octopii` | https://github.com/redhuntlabs/Octopii | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `REevee0/wiringMQ` | https://github.com/REevee0/wiringMQ | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rehydra-ai/rehydra-sdk` | https://github.com/rehydra-ai/rehydra-sdk | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Renumics/awesome-open-data-centric-ai` | https://github.com/Renumics/awesome-open-data-centric-ai | 2026-09-07 | `dpt_t_synthetic`, `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Renumics/sliceguard` | https://github.com/Renumics/sliceguard | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `reverieim/voice` | https://github.com/reverieim/voice | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `RiccardoBiosas/awesome-MLSecOps` | https://github.com/RiccardoBiosas/awesome-MLSecOps | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Rijwan123/Scrapping-Summarization` | https://github.com/Rijwan123/Scrapping-Summarization | 2026-09-07 | `dpt_crawl` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rin-nas/postgresql-patterns-library` | https://github.com/rin-nas/postgresql-patterns-library | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `risesoft-y9/Data-Labeling` | https://github.com/risesoft-y9/Data-Labeling | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Rizzo-AI-Academy/rizzo-pii` | https://github.com/Rizzo-AI-Academy/rizzo-pii | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `robert-mcdermott/doc2md` | https://github.com/robert-mcdermott/doc2md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `robertoraggi/cplusplus` | https://github.com/robertoraggi/cplusplus | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rocklambros/any2md` | https://github.com/rocklambros/any2md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ROCm/FlyDSL` | https://github.com/ROCm/FlyDSL | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ROCm/iris` | https://github.com/ROCm/iris | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rodrigo-arenas/Sklearn-genetic-opt` | https://github.com/rodrigo-arenas/Sklearn-genetic-opt | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `RoffyS/MarkEverythingDown` | https://github.com/RoffyS/MarkEverythingDown | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rohitcoder/hawk-eye` | https://github.com/rohitcoder/hawk-eye | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rohitpotluri/smol-lm3-3B-custom-kernels` | https://github.com/rohitpotluri/smol-lm3-3B-custom-kernels | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `RomiconEZ/llamator-mcp-server` | https://github.com/RomiconEZ/llamator-mcp-server | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rotsl/nexusrt` | https://github.com/rotsl/nexusrt | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `rpgeeganage/pII-guard` | https://github.com/rpgeeganage/pII-guard | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `runta-dev/clawshell` | https://github.com/runta-dev/clawshell | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ryomuk/emu8080on4004` | https://github.com/ryomuk/emu8080on4004 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ryomuk/test4004` | https://github.com/ryomuk/test4004 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sahil139/cuda-fused-attention` | https://github.com/sahil139/cuda-fused-attention | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `salehjg/batch-matmul-cuda` | https://github.com/salehjg/batch-matmul-cuda | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Samarth-23-eng/scope-intelligence` | https://github.com/Samarth-23-eng/scope-intelligence | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `samber/slog-formatter` | https://github.com/samber/slog-formatter | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SantanderAI/autoguardrails` | https://github.com/SantanderAI/autoguardrails | 2026-09-07 | `safe_t_moderation`, `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SaravanaBalaji020394/Guardrails` | https://github.com/SaravanaBalaji020394/Guardrails | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sayakpaul/Adventures-in-TensorFlow-Lite` | https://github.com/sayakpaul/Adventures-in-TensorFlow-Lite | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sayakpaul/E2E-Object-Detection-in-TFLite` | https://github.com/sayakpaul/E2E-Object-Detection-in-TFLite | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sayakpaul/Knowledge-Distillation-in-Keras` | https://github.com/sayakpaul/Knowledge-Distillation-in-Keras | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `schmitech/orbit` | https://github.com/schmitech/orbit | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ScrapeGraphAI/just-scrape` | https://github.com/ScrapeGraphAI/just-scrape | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `scthornton/vulnerable-chat` | https://github.com/scthornton/vulnerable-chat | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sealandseacat/dbmask` | https://github.com/sealandseacat/dbmask | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SearchSavior/OpenArc` | https://github.com/SearchSavior/OpenArc | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `secureagentics/Adrian` | https://github.com/secureagentics/Adrian | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `selau642/QuantizedAttention` | https://github.com/selau642/QuantizedAttention | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `selenarib5962/pm-os` | https://github.com/selenarib5962/pm-os | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sgasser/pasteguard` | https://github.com/sgasser/pasteguard | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `shen-shanshan/cs-self-learning` | https://github.com/shen-shanshan/cs-self-learning | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `shibatch/oomstaller` | https://github.com/shibatch/oomstaller | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Shikha-code36/early-exit-cnn` | https://github.com/Shikha-code36/early-exit-cnn | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ShishirPatil/poet` | https://github.com/ShishirPatil/poet | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `shoryasethia/markdrop` | https://github.com/shoryasethia/markdrop | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `shuttle-hq/synth` | https://github.com/shuttle-hq/synth | 2026-09-07 | `dpt_t_synthetic` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `silvioviscuso/nova34` | https://github.com/silvioviscuso/nova34 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SimonZeng7108/efficientsam3` | https://github.com/SimonZeng7108/efficientsam3 | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sipeed/MaixCDK` | https://github.com/sipeed/MaixCDK | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sipeed/MaixPy-v1` | https://github.com/sipeed/MaixPy-v1 | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SJTU-DMTai/awesome-ml-data-quality-papers` | https://github.com/SJTU-DMTai/awesome-ml-data-quality-papers | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `smoothnlp/SmoothNLP` | https://github.com/smoothnlp/SmoothNLP | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SonySemiconductorSolutions/mct-model-optimization` | https://github.com/SonySemiconductorSolutions/mct-model-optimization | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sophgo/tpu-mlir` | https://github.com/sophgo/tpu-mlir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `soumyasagiri/adversarial-prompt-shield` | https://github.com/soumyasagiri/adversarial-prompt-shield | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sourcenetwork/defradb` | https://github.com/sourcenetwork/defradb | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `souvikmajumder26/Multi-Agent-Medical-Assistant` | https://github.com/souvikmajumder26/Multi-Agent-Medical-Assistant | 2026-09-07 | `safe_t_guardrails` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sparkfish/augraphy` | https://github.com/sparkfish/augraphy | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `spcl/daceml` | https://github.com/spcl/daceml | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `spcl/pymlir` | https://github.com/spcl/pymlir | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SponsioLabs/Sponsio` | https://github.com/SponsioLabs/Sponsio | 2026-09-07 | `safe_t_guardrails`, `safe_t_promptinjection`, `B_safe_agentsec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `SQLab/symgdb` | https://github.com/SQLab/symgdb | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sreedevk/deduplicator` | https://github.com/sreedevk/deduplicator | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Sriram-PR/doc-scraper` | https://github.com/Sriram-PR/doc-scraper | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `star-whale/starwhale` | https://github.com/star-whale/starwhale | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `starfishdata/starfish` | https://github.com/starfishdata/starfish | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `steelcityamir/safe-content-ai` | https://github.com/steelcityamir/safe-content-ai | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `styfeng/DataAug4NLP` | https://github.com/styfeng/DataAug4NLP | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sub1120/PSR-KD` | https://github.com/sub1120/PSR-KD | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `sudonam/open-college-courses` | https://github.com/sudonam/open-college-courses | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `supadata-ai/js` | https://github.com/supadata-ai/js | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `surge-ai/toxicity` | https://github.com/surge-ai/toxicity | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `swap5114/demo-afterquery-d96054d1` | https://github.com/swap5114/demo-afterquery-d96054d1 | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `swislar/RACo-Deduplication` | https://github.com/swislar/RACo-Deduplication | 2026-09-07 | `dpt_q_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `syda-ai/syda` | https://github.com/syda-ai/syda | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Syslifters/OffSec-Reporting` | https://github.com/Syslifters/OffSec-Reporting | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `t3l3machus/hoaxshell` | https://github.com/t3l3machus/hoaxshell | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tanghui315/lumenfolio` | https://github.com/tanghui315/lumenfolio | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tattle-made/Uli` | https://github.com/tattle-made/Uli | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TCLResearchEurope/ptdeco` | https://github.com/TCLResearchEurope/ptdeco | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Tebmer/Awesome-Knowledge-Distillation-of-LLMs` | https://github.com/Tebmer/Awesome-Knowledge-Distillation-of-LLMs | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TejasR11/gpu-transformer-kernels` | https://github.com/TejasR11/gpu-transformer-kernels | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Tencent/FeatherCNN` | https://github.com/Tencent/FeatherCNN | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Tencent/Forward` | https://github.com/Tencent/Forward | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Tencent/TNN` | https://github.com/Tencent/TNN | 2026-09-07 | `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `textflint/textflint` | https://github.com/textflint/textflint | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tg12/gpt_jailbreak_status` | https://github.com/tg12/gpt_jailbreak_status | 2026-09-07 | `safe_t_promptinjection`, `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `therealoliver/Deepdive-llama3-from-scratch` | https://github.com/therealoliver/Deepdive-llama3-from-scratch | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `thomas-villani/all2md` | https://github.com/thomas-villani/all2md | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ThomasRochefortB/open-agentinstruct` | https://github.com/ThomasRochefortB/open-agentinstruct | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `thoughtbot/top_secret` | https://github.com/thoughtbot/top_secret | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `thousrm/universal_NPU-CNN_accelerator` | https://github.com/thousrm/universal_NPU-CNN_accelerator | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `thuml/depyf` | https://github.com/thuml/depyf | 2026-09-07 | `comp_t_tensorcompiler` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `THUYimingLi/backdoor-learning-resources` | https://github.com/THUYimingLi/backdoor-learning-resources | 2026-09-07 | `B_safe_aisec` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TieuLongPhan/SynRBL` | https://github.com/TieuLongPhan/SynRBL | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TIGER-AI-Lab/ClawBench` | https://github.com/TIGER-AI-Lab/ClawBench | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tigerlab-ai/tiger` | https://github.com/tigerlab-ai/tiger | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tinyvision/DAMO-YOLO` | https://github.com/tinyvision/DAMO-YOLO | 2026-09-07 | `B_comp_tensorrt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tlc-pack/TLCBench` | https://github.com/tlc-pack/TLCBench | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tldrsec/prompt-injection-defenses` | https://github.com/tldrsec/prompt-injection-defenses | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Tobiaszn8972/turboquant-gpu` | https://github.com/Tobiaszn8972/turboquant-gpu | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `toby-bridges/api-relay-audit` | https://github.com/toby-bridges/api-relay-audit | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tokern/piicatcher` | https://github.com/tokern/piicatcher | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TomNisbet/Simple8085` | https://github.com/TomNisbet/Simple8085 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ton-blockchain/TxTracer` | https://github.com/ton-blockchain/TxTracer | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ton-society/grants-and-bounties` | https://github.com/ton-society/grants-and-bounties | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tonkeeper/tongo` | https://github.com/tonkeeper/tongo | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tphakala/birdnet-onnx-converter` | https://github.com/tphakala/birdnet-onnx-converter | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tqchen/ffi-navigator` | https://github.com/tqchen/ffi-navigator | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `trailofbits/multiplier` | https://github.com/trailofbits/multiplier | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `trailofbits/vast` | https://github.com/trailofbits/vast | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `traveller59/torch2trt` | https://github.com/traveller59/torch2trt | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TrevTron/indiedroid-nova-llm` | https://github.com/TrevTron/indiedroid-nova-llm | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tristanbaldev/Clawidth` | https://github.com/tristanbaldev/Clawidth | 2026-09-07 | `edge_t_openhw` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TritonDataCenter/containerpilot` | https://github.com/TritonDataCenter/containerpilot | 2026-09-07 | `comp_t_triton` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TrustAI-laboratory/Learn-Prompt-Hacking` | https://github.com/TrustAI-laboratory/Learn-Prompt-Hacking | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `trylonai/gateway` | https://github.com/trylonai/gateway | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `tstanislawek/awesome-document-understanding` | https://github.com/tstanislawek/awesome-document-understanding | 2026-09-07 | `B_dpt_ocrpdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ttguy0707/CyberClaw` | https://github.com/ttguy0707/CyberClaw | 2026-09-07 | `safe_t_aisafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `TyloAI/prompt-guard-lite` | https://github.com/TyloAI/prompt-guard-lite | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `UCSC-REAL/DS2` | https://github.com/UCSC-REAL/DS2 | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `UCYBERS/Awesome-Blackhat-Tools` | https://github.com/UCYBERS/Awesome-Blackhat-Tools | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `UIUC-ChenLab/scalehls` | https://github.com/UIUC-ChenLab/scalehls | 2026-09-07 | `comp_t_mlir` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `umitkacar/awesome-mobile-ai` | https://github.com/umitkacar/awesome-mobile-ai | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `umitkacar/awesome-ncnn` | https://github.com/umitkacar/awesome-ncnn | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `umitkacar/awesome-tinyml` | https://github.com/umitkacar/awesome-tinyml | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `UofT-EcoSystem/DietCode` | https://github.com/UofT-EcoSystem/DietCode | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `us/crw` | https://github.com/us/crw | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vakra-dev/reader` | https://github.com/vakra-dev/reader | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vanderschaarlab/synthcity` | https://github.com/vanderschaarlab/synthcity | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `verazuo/jailbreak_llms` | https://github.com/verazuo/jailbreak_llms | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `VikParuchuri/textbook_quality` | https://github.com/VikParuchuri/textbook_quality | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vincenzo-afk/Intelis-Agent` | https://github.com/vincenzo-afk/Intelis-Agent | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vincenzo-afk/SocialGuard-RL` | https://github.com/vincenzo-afk/SocialGuard-RL | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vincenzo-afk/verbix` | https://github.com/vincenzo-afk/verbix | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vinodborole/okf-kit` | https://github.com/vinodborole/okf-kit | 2026-09-07 | `dpt_t_webscraping` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Viralmaniar/BigBountyRecon` | https://github.com/Viralmaniar/BigBountyRecon | 2026-09-07 | `safe_t_redteam` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Virtue-Research/guard-eval-harness` | https://github.com/Virtue-Research/guard-eval-harness | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `VisharadR/Mini-Transformer---GPU-optimized` | https://github.com/VisharadR/Mini-Transformer---GPU-optimized | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `vme-im/vme-content` | https://github.com/vme-im/vme-content | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `wangfenjin/simple` | https://github.com/wangfenjin/simple | 2026-09-07 | `B_dpt_tokenizer` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `WangYihang/pii2pw` | https://github.com/WangYihang/pii2pw | 2026-09-07 | `B_safe_pii` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `WanzhengZhu/Euphemism` | https://github.com/WanzhengZhu/Euphemism | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `wasiahmad/Awesome-LLM-Synthetic-Data` | https://github.com/wasiahmad/Awesome-LLM-Synthetic-Data | 2026-09-07 | `dpt_synth` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `waynehacking8/inference-kernel-cookbook` | https://github.com/waynehacking8/inference-kernel-cookbook | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Western-OC2-Lab/Cross-Layer-Autonomous-Cybersecurity-Framework` | https://github.com/Western-OC2-Lab/Cross-Layer-Autonomous-Cybersecurity-Framework | 2026-09-07 | `B_comp_modelopt` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Westlake-AI/openmixup` | https://github.com/Westlake-AI/openmixup | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `whitelok/tvm-lesson` | https://github.com/whitelok/tvm-lesson | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `whylabs/langkit` | https://github.com/whylabs/langkit | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `whythawk/data-as-a-science` | https://github.com/whythawk/data-as-a-science | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `wisupai/e2m` | https://github.com/wisupai/e2m | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `WZBSocialScienceCenter/pdftabextract` | https://github.com/WZBSocialScienceCenter/pdftabextract | 2026-09-07 | `B_dpt_ocrpdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `wzn1118/AsteriaAnalyst` | https://github.com/wzn1118/AsteriaAnalyst | 2026-09-07 | `dpt_t_dataquality` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `x-CK-x/Dataset-Curation-Tool` | https://github.com/x-CK-x/Dataset-Curation-Tool | 2026-09-07 | `dpt_t_datacentric` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `x-zheng16/Awesome-Embodied-AI-Safety` | https://github.com/x-zheng16/Awesome-Embodied-AI-Safety | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `xiayouran/VisuTVM` | https://github.com/xiayouran/VisuTVM | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Xilinx/mlir-aie` | https://github.com/Xilinx/mlir-aie | 2026-09-07 | `comp_t_mlir`, `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Xilinx/XRT` | https://github.com/Xilinx/XRT | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `XshuiAi/media-publish-check` | https://github.com/XshuiAi/media-publish-check | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `xxxbrian/mcp-rquest` | https://github.com/xxxbrian/mcp-rquest | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `xybrid-ai/xybrid` | https://github.com/xybrid-ai/xybrid | 2026-09-07 | `edge_t_edgeai` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yatin-superintelligence/Adversarial-Agent-Intent-Safety-Analysis-240K` | https://github.com/yatin-superintelligence/Adversarial-Agent-Intent-Safety-Analysis-240K | 2026-09-07 | `safe_q_guardrail` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yifu-ding/LongContext-SparseQuant-Attn` | https://github.com/yifu-ding/LongContext-SparseQuant-Attn | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yifu-ding/MP-Sparse-Attn` | https://github.com/yifu-ding/MP-Sparse-Attn | 2026-09-07 | `comp_q_kernel` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yigitkonur/api-llm-ocr` | https://github.com/yigitkonur/api-llm-ocr | 2026-09-07 | `dpt_q_pdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yihedeng9/DuoGuard` | https://github.com/yihedeng9/DuoGuard | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yobix-ai/extractous` | https://github.com/yobix-ai/extractous | 2026-09-07 | `B_dpt_ocrpdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Yomguithereal/talisman` | https://github.com/Yomguithereal/talisman | 2026-09-07 | `dpt_t_dedup` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `YongtaoGE/RetinaFace` | https://github.com/YongtaoGE/RetinaFace | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yongzhuo/nlp_xiaojiang` | https://github.com/yongzhuo/nlp_xiaojiang | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yottatsa/80188` | https://github.com/yottatsa/80188 | 2026-09-07 | `edge_t_sbc` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `youyve/nputop` | https://github.com/youyve/nputop | 2026-09-07 | `edge_t_npu` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `YuliangXiu/MobilePose` | https://github.com/YuliangXiu/MobilePose | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Yulv-git/Model-Inference-Deployment` | https://github.com/Yulv-git/Model-Inference-Deployment | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `yunwei37/prompt-hacker-collections` | https://github.com/yunwei37/prompt-hacker-collections | 2026-09-07 | `safe_t_promptinjection` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `YutongChenVictor/NPU-E2E` | https://github.com/YutongChenVictor/NPU-E2E | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `YutoTerashima/agent-safety-eval-lab` | https://github.com/YutoTerashima/agent-safety-eval-lab | 2026-09-07 | `B_safe_llmsafety` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zengxiao-he/tessera` | https://github.com/zengxiao-he/tessera | 2026-09-07 | `comp_t_triton`, `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zengzifan1/multi-agent-moderation` | https://github.com/zengzifan1/multi-agent-moderation | 2026-09-07 | `safe_t_moderation` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zentinelproxy/zentinel-agent-ai-gateway` | https://github.com/zentinelproxy/zentinel-agent-ai-gateway | 2026-09-07 | `safe_q_jailbreak` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zeokin/Cuda-Compute-OSS` | https://github.com/zeokin/Cuda-Compute-OSS | 2026-09-07 | `comp_t_cuda` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zhanlaoban/EDA_NLP_for_Chinese` | https://github.com/zhanlaoban/EDA_NLP_for_Chinese | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `ZhaoJ9014/face.evoLVe` | https://github.com/ZhaoJ9014/face.evoLVe | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Zhen-Dong/HAWQ` | https://github.com/Zhen-Dong/HAWQ | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zhihu/ZhiLight` | https://github.com/zhihu/ZhiLight | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zhiqwang/yolort` | https://github.com/zhiqwang/yolort | 2026-09-07 | `B_comp_tvm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zhoubear/open-paperless` | https://github.com/zhoubear/open-paperless | 2026-09-07 | `B_dpt_ocrpdf` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zhunzhong07/Random-Erasing` | https://github.com/zhunzhong07/Random-Erasing | 2026-09-07 | `B_dpt_augment` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Zjh-819/LLMDataHub` | https://github.com/Zjh-819/LLMDataHub | 2026-09-07 | `B_dpt_datasetllm` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zjhellofss/KuiperInfer` | https://github.com/zjhellofss/KuiperInfer | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `zjhellofss/KuiperLLama` | https://github.com/zjhellofss/KuiperLLama | 2026-09-07 | `B_comp_engine` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `Zyrexnn/Cybermes` | https://github.com/Zyrexnn/Cybermes | 2026-09-07 | `safe_t_llmsecurity` | fewer than 1,000 all-time stars, or no push since 2025-09-07 (GitHub floor) |
| `5CD-AI/visobert-14gb-corpus` | https://huggingface.co/5CD-AI/visobert-14gb-corpus | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `a1273352/pixtral-12b-construction-safety` | https://huggingface.co/a1273352/pixtral-12b-construction-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `abhiai/ModerationGPT` | https://huggingface.co/abhiai/ModerationGPT | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `AbteeXAILab/lumynax-guard-text-moderation` | https://huggingface.co/AbteeXAILab/lumynax-guard-text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `adaptive-classifier/content-moderation` | https://huggingface.co/adaptive-classifier/content-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `adept/persimmon-8b-base` | https://huggingface.co/adept/persimmon-8b-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `adibvafa/CodonTransformer` | https://huggingface.co/adibvafa/CodonTransformer | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ai-forever/rugpt3medium_based_on_gpt2` | https://huggingface.co/ai-forever/rugpt3medium_based_on_gpt2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ai-forever/rugpt3small_based_on_gpt2` | https://huggingface.co/ai-forever/rugpt3small_based_on_gpt2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ai-forever/ruRoberta-large` | https://huggingface.co/ai-forever/ruRoberta-large | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ai-safety-institute/somo-olmo-7b-nohints-s1-chkpt-1520` | https://huggingface.co/ai-safety-institute/somo-olmo-7b-nohints-s1-chkpt-1520 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `ai-safety-institute/somo-olmo-7b-sdf-sft` | https://huggingface.co/ai-safety-institute/somo-olmo-7b-sdf-sft | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `ai21labs/Jamba-v0.1` | https://huggingface.co/ai21labs/Jamba-v0.1 | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `airesearch/wangchanberta-base-att-spm-uncased` | https://huggingface.co/airesearch/wangchanberta-base-att-spm-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `aishmurtaza/neonatal_guardian_slm` | https://huggingface.co/aishmurtaza/neonatal_guardian_slm | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Akahsizrr/Cyber-Prime-1-2.6B` | https://huggingface.co/Akahsizrr/Cyber-Prime-1-2.6B | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `albert/albert-base-v1` | https://huggingface.co/albert/albert-base-v1 | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `albert/albert-base-v2` | https://huggingface.co/albert/albert-base-v2 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Alibaba-NLP/gte-Qwen2-1.5B-instruct` | https://huggingface.co/Alibaba-NLP/gte-Qwen2-1.5B-instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `allenai/BAR-2x7B-Safety` | https://huggingface.co/allenai/BAR-2x7B-Safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `almanach/camembert-base` | https://huggingface.co/almanach/camembert-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `andriadze/ai-chat-underage-moderation2` | https://huggingface.co/andriadze/ai-chat-underage-moderation2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `andriadze/bert-chat-moderation-X` | https://huggingface.co/andriadze/bert-chat-moderation-X | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `andriadze/bert-chat-moderation-X-V2` | https://huggingface.co/andriadze/bert-chat-moderation-X-V2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `anferico/bert-for-patents` | https://huggingface.co/anferico/bert-for-patents | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `apodex/Apodex-1.1-mini` | https://huggingface.co/apodex/Apodex-1.1-mini | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `arcee-ai/AFM-4.5B-Base` | https://huggingface.co/arcee-ai/AFM-4.5B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ashwini10521/prompt-safety-classification` | https://huggingface.co/ashwini10521/prompt-safety-classification | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `astroware/Halo0.8B-guard-v1` | https://huggingface.co/astroware/Halo0.8B-guard-v1 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `aubmindlab/aragpt2-base` | https://huggingface.co/aubmindlab/aragpt2-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `aubmindlab/bert-base-arabertv02` | https://huggingface.co/aubmindlab/bert-base-arabertv02 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `aubmindlab/bert-base-arabertv2` | https://huggingface.co/aubmindlab/bert-base-arabertv2 | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `AutoCyberAI/crp-safety-deberta-v1` | https://huggingface.co/AutoCyberAI/crp-safety-deberta-v1 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `ayushgupta7777/safetyvision-yolov8` | https://huggingface.co/ayushgupta7777/safetyvision-yolov8 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `BabyLM-community/babylm-multimodal-baseline-flamingo` | https://huggingface.co/BabyLM-community/babylm-multimodal-baseline-flamingo | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `bartowski/Meta-Llama-3.1-8B-Instruct-GGUF` | https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Bazzar/bazzar_moderation` | https://huggingface.co/Bazzar/bazzar_moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Bhavdeepsingh/moderashield-text-moderation` | https://huggingface.co/Bhavdeepsingh/moderashield-text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `bigcode/starcoder` | https://huggingface.co/bigcode/starcoder | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `bigscience/bloom` | https://huggingface.co/bigscience/bloom | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `black-forest-labs/FLUX.1-dev` | https://huggingface.co/black-forest-labs/FLUX.1-dev | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `black-forest-labs/FLUX.2-klein-base-9b-fp8` | https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9b-fp8 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `bloomer010/Ling-3.0-tiny-GGUF` | https://huggingface.co/bloomer010/Ling-3.0-tiny-GGUF | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `bosonai/higgs-tts-3-4b` | https://huggingface.co/bosonai/higgs-tts-3-4b | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `BrCamp/bee-350m-pt-base` | https://huggingface.co/BrCamp/bee-350m-pt-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `BreezeBlue/Breeze-TTS-2` | https://huggingface.co/BreezeBlue/Breeze-TTS-2 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ByteDance/Ouro-1.4B` | https://huggingface.co/ByteDance/Ouro-1.4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Cactus-Compute/needle2` | https://huggingface.co/Cactus-Compute/needle2 | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `callhub/koala-ai-text-moderation` | https://huggingface.co/callhub/koala-ai-text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Chain-GPT/Solidity-LLM` | https://huggingface.co/Chain-GPT/Solidity-LLM | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `chandar-lab/NeoBERT` | https://huggingface.co/chandar-lab/NeoBERT | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `CogEvol/CogEvol-4B` | https://huggingface.co/CogEvol/CogEvol-4B | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `CohereLabs/c4ai-command-r-plus` | https://huggingface.co/CohereLabs/c4ai-command-r-plus | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `CohereLabs/tiny-aya-base` | https://huggingface.co/CohereLabs/tiny-aya-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `cointegrated/rubert-tiny` | https://huggingface.co/cointegrated/rubert-tiny | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `cointegrated/rubert-tiny2` | https://huggingface.co/cointegrated/rubert-tiny2 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ctheodoris/Geneformer` | https://huggingface.co/ctheodoris/Geneformer | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `DANNY621/H3-World` | https://huggingface.co/DANNY621/H3-World | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `dascim/juribert-base` | https://huggingface.co/dascim/juribert-base | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Data-Lab/moderation_binary_classification` | https://huggingface.co/Data-Lab/moderation_binary_classification | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Data-Lab/moderation_layer` | https://huggingface.co/Data-Lab/moderation_layer | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Data-Lab/moderation_layer_v2` | https://huggingface.co/Data-Lab/moderation_layer_v2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `dbmdz/bert-base-german-cased` | https://huggingface.co/dbmdz/bert-base-german-cased | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `dbmdz/bert-base-italian-xxl-cased` | https://huggingface.co/dbmdz/bert-base-italian-xxl-cased | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `dcarpintero/pangolin-guard-base` | https://huggingface.co/dcarpintero/pangolin-guard-base | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `dccuchile/bert-base-spanish-wwm-cased` | https://huggingface.co/dccuchile/bert-base-spanish-wwm-cased | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `dccuchile/bert-base-spanish-wwm-uncased` | https://huggingface.co/dccuchile/bert-base-spanish-wwm-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `DeepChem/ChemBERTa-77M-MLM` | https://huggingface.co/DeepChem/ChemBERTa-77M-MLM | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `deepmind/language-perceiver` | https://huggingface.co/deepmind/language-perceiver | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2` | https://huggingface.co/DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `deepset/gbert-large` | https://huggingface.co/deepset/gbert-large | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `deepvk/RuModernBERT-base` | https://huggingface.co/deepvk/RuModernBERT-base | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `DevQuasar-10/mrfakename.mistral-small-3.1-24b-base-2503-hf-GGUF` | https://huggingface.co/DevQuasar-10/mrfakename.mistral-small-3.1-24b-base-2503-hf-GGUF | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `DevQuasar/nvidia.Nemotron-Content-Safety-Reasoning-4B-GGUF` | https://huggingface.co/DevQuasar/nvidia.Nemotron-Content-Safety-Reasoning-4B-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `distilbert/distilbert-base-cased` | https://huggingface.co/distilbert/distilbert-base-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `distilbert/distilbert-base-multilingual-cased` | https://huggingface.co/distilbert/distilbert-base-multilingual-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `dlicari/Italian-Legal-BERT` | https://huggingface.co/dlicari/Italian-Legal-BERT | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `dmis-lab/biobert-base-cased-v1.2` | https://huggingface.co/dmis-lab/biobert-base-cased-v1.2 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `docling-project/SmolDocling-256M-preview` | https://huggingface.co/docling-project/SmolDocling-256M-preview | 2026-09-07 | `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `donate110/apex-moderation-7b` | https://huggingface.co/donate110/apex-moderation-7b | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `dots-studio/dots.llm1.base` | https://huggingface.co/dots-studio/dots.llm1.base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `dots-studio/dots.ocr` | https://huggingface.co/dots-studio/dots.ocr | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `dphn/dolphin-2.5-mixtral-8x7b` | https://huggingface.co/dphn/dolphin-2.5-mixtral-8x7b | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Dream-org/Dream-v0-Base-7B` | https://huggingface.co/Dream-org/Dream-v0-Base-7B | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `drowzeys/keys-DeepSeekV4Flash-Vision-EXP-ablit` | https://huggingface.co/drowzeys/keys-DeepSeekV4Flash-Vision-EXP-ablit | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `duanyu027/moderation_0628` | https://huggingface.co/duanyu027/moderation_0628 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `duanyu027/moderation_0703_deberta_v3_small` | https://huggingface.co/duanyu027/moderation_0703_deberta_v3_small | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `duanyu027/moderation_0703_deberta_v3_small_onnx` | https://huggingface.co/duanyu027/moderation_0703_deberta_v3_small_onnx | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Earlychildhoodeducation/EleMo-V2-Base` | https://huggingface.co/Earlychildhoodeducation/EleMo-V2-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ehsanaghaei/SecureBERT` | https://huggingface.co/ehsanaghaei/SecureBERT | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `EleutherAI/gpt-j-6b` | https://huggingface.co/EleutherAI/gpt-j-6b | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ellery/text-safety-embedding` | https://huggingface.co/ellery/text-safety-embedding | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `emilyalsentzer/Bio_Discharge_Summary_BERT` | https://huggingface.co/emilyalsentzer/Bio_Discharge_Summary_BERT | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF` | https://huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `enguard/medium-guard-128m-xx-prompt-harassment-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-harassment-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/medium-guard-128m-xx-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/medium-guard-128m-xx-prompt-harmfulness-multilabel-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-harmfulness-multilabel-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/medium-guard-128m-xx-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/medium-guard-128m-xx-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/medium-guard-128m-xx-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/medium-guard-128m-xx-prompt-violence-binary-moderation` | https://huggingface.co/enguard/medium-guard-128m-xx-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/small-guard-32m-en-prompt-harassment-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-harassment-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/small-guard-32m-en-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/small-guard-32m-en-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/small-guard-32m-en-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/small-guard-32m-en-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/small-guard-32m-en-prompt-violence-binary-moderation` | https://huggingface.co/enguard/small-guard-32m-en-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-2m-en-prompt-harassment-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-harassment-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-2m-en-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-2m-en-prompt-harmfulness-multilabel-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-harmfulness-multilabel-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-2m-en-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-2m-en-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-2m-en-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-2m-en-prompt-violence-binary-moderation` | https://huggingface.co/enguard/tiny-guard-2m-en-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-4m-en-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-4m-en-prompt-harmfulness-multilabel-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-harmfulness-multilabel-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-4m-en-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-4m-en-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-4m-en-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-4m-en-prompt-violence-binary-moderation` | https://huggingface.co/enguard/tiny-guard-4m-en-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-8m-en-prompt-harassment-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-harassment-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-8m-en-prompt-harmfulness-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-harmfulness-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-8m-en-prompt-harmfulness-multilabel-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-harmfulness-multilabel-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-8m-en-prompt-hate-speech-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-hate-speech-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-8m-en-prompt-self-harm-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-self-harm-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-8m-en-prompt-sexual-content-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-sexual-content-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `enguard/tiny-guard-8m-en-prompt-violence-binary-moderation` | https://huggingface.co/enguard/tiny-guard-8m-en-prompt-violence-binary-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `EuroBERT/EuroBERT-2.1B` | https://huggingface.co/EuroBERT/EuroBERT-2.1B | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `EuroBERT/EuroBERT-210m` | https://huggingface.co/EuroBERT/EuroBERT-210m | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `exeterminal/Exe-Guard-Dynamic-GGUF` | https://huggingface.co/exeterminal/Exe-Guard-Dynamic-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Extropic-AI/Z1T-0` | https://huggingface.co/Extropic-AI/Z1T-0 | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `F16/krea2-turbo-sda` | https://huggingface.co/F16/krea2-turbo-sda | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `facebook/dinov3-vitl16-pretrain-lvd1689m` | https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `facebook/esm2_t12_35M_UR50D` | https://huggingface.co/facebook/esm2_t12_35M_UR50D | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `facebook/esm2_t30_150M_UR50D` | https://huggingface.co/facebook/esm2_t30_150M_UR50D | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `facebook/esm2_t36_3B_UR50D` | https://huggingface.co/facebook/esm2_t36_3B_UR50D | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `facebook/esm2_t6_8M_UR50D` | https://huggingface.co/facebook/esm2_t6_8M_UR50D | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `facebook/mms-300m` | https://huggingface.co/facebook/mms-300m | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `facebook/sam3.1` | https://huggingface.co/facebook/sam3.1 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `FacebookAI/xlm-mlm-en-2048` | https://huggingface.co/FacebookAI/xlm-mlm-en-2048 | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `faisalq/bert-base-arapoembert` | https://huggingface.co/faisalq/bert-base-arapoembert | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `FastVideo/FastVideo-FastH3-4-step-Preview-v1-VSA-DataFree` | https://huggingface.co/FastVideo/FastVideo-FastH3-4-step-Preview-v1-VSA-DataFree | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `flaubert/flaubert_base_cased` | https://huggingface.co/flaubert/flaubert_base_cased | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `flowxai/moderation` | https://huggingface.co/flowxai/moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `FrontiersMind/Nandi-Mini-150M-GuardRails` | https://huggingface.co/FrontiersMind/Nandi-Mini-150M-GuardRails | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `FWKV/Myosotis-1-base` | https://huggingface.co/FWKV/Myosotis-1-base | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `GerMedBERT/medbert-512` | https://huggingface.co/GerMedBERT/medbert-512 | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `google-bert/bert-base-chinese` | https://huggingface.co/google-bert/bert-base-chinese | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `google-bert/bert-base-german-cased` | https://huggingface.co/google-bert/bert-base-german-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `google-bert/bert-large-cased` | https://huggingface.co/google-bert/bert-large-cased | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `google-bert/bert-large-uncased` | https://huggingface.co/google-bert/bert-large-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `google/muril-base-cased` | https://huggingface.co/google/muril-base-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `google/timesfm-3.0-pytorch` | https://huggingface.co/google/timesfm-3.0-pytorch | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `GSAI-ML/LLaDA-8B-Base` | https://huggingface.co/GSAI-ML/LLaDA-8B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `GSAI-ML/LLaDA-8B-Instruct` | https://huggingface.co/GSAI-ML/LLaDA-8B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `hayatiali/turkish-safety` | https://huggingface.co/hayatiali/turkish-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `hfl/chinese-bert-wwm` | https://huggingface.co/hfl/chinese-bert-wwm | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `hfl/chinese-bert-wwm-ext` | https://huggingface.co/hfl/chinese-bert-wwm-ext | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `hfl/chinese-macbert-base` | https://huggingface.co/hfl/chinese-macbert-base | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `hfl/chinese-macbert-large` | https://huggingface.co/hfl/chinese-macbert-large | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `hfl/chinese-roberta-wwm-ext` | https://huggingface.co/hfl/chinese-roberta-wwm-ext | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `hfl/chinese-roberta-wwm-ext-large` | https://huggingface.co/hfl/chinese-roberta-wwm-ext-large | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `hfmlsoc/ncii-light-guard-v01` | https://huggingface.co/hfmlsoc/ncii-light-guard-v01 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Himanshu101789/xlmr-multi-lingual-content-moderation` | https://huggingface.co/Himanshu101789/xlmr-multi-lingual-content-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `hivetrace/gliner-guard-uniencoder` | https://huggingface.co/hivetrace/gliner-guard-uniencoder | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `HojoAI/Hojo-ASR-Multi-V1` | https://huggingface.co/HojoAI/Hojo-ASR-Multi-V1 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `HooshvareLab/bert-base-parsbert-uncased` | https://huggingface.co/HooshvareLab/bert-base-parsbert-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` | https://huggingface.co/hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4 | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `huggingface/CodeBERTa-small-v1` | https://huggingface.co/huggingface/CodeBERTa-small-v1 | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `huihui-ai/Huihui-Qwen3.8-Flash-Next-abliterated-GGUF` | https://huggingface.co/huihui-ai/Huihui-Qwen3.8-Flash-Next-abliterated-GGUF | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `huyleit/phobert-vi-moderation-v1.1` | https://huggingface.co/huyleit/phobert-vi-moderation-v1.1 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `iamrazi/text-moderation` | https://huggingface.co/iamrazi/text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `ibm-granite/granitelib-guardian-r1.0` | https://huggingface.co/ibm-granite/granitelib-guardian-r1.0 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `ibm-research/MoLFormer-XL-both-10pct` | https://huggingface.co/ibm-research/MoLFormer-XL-both-10pct | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ifmain/ModerationBERT-En-02` | https://huggingface.co/ifmain/ModerationBERT-En-02 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `inclusionAI/Ling-3.0-flash` | https://huggingface.co/inclusionAI/Ling-3.0-flash | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `inclusionAI/Ling-3.0-flash-Fin` | https://huggingface.co/inclusionAI/Ling-3.0-flash-Fin | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `inclusionAI/Ling-3.0-tiny` | https://huggingface.co/inclusionAI/Ling-3.0-tiny | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `inclusionAI/LLaDA-Image` | https://huggingface.co/inclusionAI/LLaDA-Image | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `indolem/indobert-base-uncased` | https://huggingface.co/indolem/indobert-base-uncased | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `InstaDeepAI/nucleotide-transformer-2.5b-multi-species` | https://huggingface.co/InstaDeepAI/nucleotide-transformer-2.5b-multi-species | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `jackaduma/SecBERT` | https://huggingface.co/jackaduma/SecBERT | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Jackrong/Qwopus3.8-27B-Flash` | https://huggingface.co/Jackrong/Qwopus3.8-27B-Flash | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Jackrong/Qwopus3.8-27B-Flash-GGUF` | https://huggingface.co/Jackrong/Qwopus3.8-27B-Flash-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `jaimevera1107/moderation-topics` | https://huggingface.co/jaimevera1107/moderation-topics | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `JashVora7/hybrid-guardrails-deberta-moderation` | https://huggingface.co/JashVora7/hybrid-guardrails-deberta-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `JashVora7/hybrid-guardrails-distilbert-moderation` | https://huggingface.co/JashVora7/hybrid-guardrails-distilbert-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `JetBrains/Mellum2-12B-A2.5B-Base` | https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `JetBrains/Mellum2-12B-A2.5B-Instruct-GGUF-Q8_0` | https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Instruct-GGUF-Q8_0 | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `jhu-clsp/mmBERT-base` | https://huggingface.co/jhu-clsp/mmBERT-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `jhu-clsp/mmBERT-small` | https://huggingface.co/jhu-clsp/mmBERT-small | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `jinaai/jina-embeddings-v2-base-code` | https://huggingface.co/jinaai/jina-embeddings-v2-base-code | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `jinaai/jina-embeddings-v2-base-de` | https://huggingface.co/jinaai/jina-embeddings-v2-base-de | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `julien-c/dummy-unknown` | https://huggingface.co/julien-c/dummy-unknown | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `junnyu/roformer_chinese_small` | https://huggingface.co/junnyu/roformer_chinese_small | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `K-intelligence/Midm-2.0-Base-Instruct` | https://huggingface.co/K-intelligence/Midm-2.0-Base-Instruct | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `kakaobank/kf-deberta-base` | https://huggingface.co/kakaobank/kf-deberta-base | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `kakaocorp/kanana-2-1.3b-base` | https://huggingface.co/kakaocorp/kanana-2-1.3b-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `kalyan1900/PII-GUARD-Qwen2.5-1.5B` | https://huggingface.co/kalyan1900/PII-GUARD-Qwen2.5-1.5B | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `katanemo/Arch-Guard` | https://huggingface.co/katanemo/Arch-Guard | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `katuni4ka/tiny-random-stable-diffusion-with-safety-checker` | https://huggingface.co/katuni4ka/tiny-random-stable-diffusion-with-safety-checker | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `KennethFal/vh5tape-vhs-lora-minimax-h3` | https://huggingface.co/KennethFal/vh5tape-vhs-lora-minimax-h3 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `keremberke/yolov5m-construction-safety` | https://huggingface.co/keremberke/yolov5m-construction-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `keremberke/yolov5n-construction-safety` | https://huggingface.co/keremberke/yolov5n-construction-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `keremberke/yolov5s-construction-safety` | https://huggingface.co/keremberke/yolov5s-construction-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `kishan4444/text-moderation` | https://huggingface.co/kishan4444/text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `kishan4444/text_moderation_model` | https://huggingface.co/kishan4444/text_moderation_model | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `klue/bert-base` | https://huggingface.co/klue/bert-base | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `klue/roberta-base` | https://huggingface.co/klue/roberta-base | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `klue/roberta-large` | https://huggingface.co/klue/roberta-large | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `KORMo-Team/KORMo-10B-base` | https://huggingface.co/KORMo-Team/KORMo-10B-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `krea/Krea-2-Raw` | https://huggingface.co/krea/Krea-2-Raw | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `krea/Krea-2-Turbo` | https://huggingface.co/krea/Krea-2-Turbo | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `ku-nlp/deberta-v2-large-japanese-char-wwm` | https://huggingface.co/ku-nlp/deberta-v2-large-japanese-char-wwm | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `kykim/albert-kor-base` | https://huggingface.co/kykim/albert-kor-base | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `kykim/bert-kor-base` | https://huggingface.co/kykim/bert-kor-base | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `lamdx4/phobert-vi-moderation` | https://huggingface.co/lamdx4/phobert-vi-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `law-ai/InLegalBERT` | https://huggingface.co/law-ai/InLegalBERT | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct` | https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-AWQ` | https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `lightonai/LightOnOCR-2-1B-base` | https://huggingface.co/lightonai/LightOnOCR-2-1B-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `line-corporation/line-distilbert-base-japanese` | https://huggingface.co/line-corporation/line-distilbert-base-japanese | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LiquidAI/LFM2.5-1.2B-Base` | https://huggingface.co/LiquidAI/LFM2.5-1.2B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LiquidAI/LFM2.5-1.2B-Instruct` | https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LiquidAI/LFM2.5-1.2B-Instruct-GGUF` | https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LiquidAI/LFM2.5-2.6B` | https://huggingface.co/LiquidAI/LFM2.5-2.6B | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LiquidAI/LFM2.5-2.6B-Base` | https://huggingface.co/LiquidAI/LFM2.5-2.6B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LiquidAI/LFM2.5-230M-Base` | https://huggingface.co/LiquidAI/LFM2.5-230M-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LiquidAI/LFM2.5-350M-Base` | https://huggingface.co/LiquidAI/LFM2.5-350M-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LiquidAI/LFM2.5-Encoder-230M` | https://huggingface.co/LiquidAI/LFM2.5-Encoder-230M | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `LiquidAI/LFM2.5-Encoder-350M` | https://huggingface.co/LiquidAI/LFM2.5-Encoder-350M | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `llm-semantic-router/mmbert-safety-binary-hazard` | https://huggingface.co/llm-semantic-router/mmbert-safety-binary-hazard | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mattshumer/Reflection-Llama-3.1-70B` | https://huggingface.co/mattshumer/Reflection-Llama-3.1-70B | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `mbehbooei/vit-base-patch16-224-in21k-finetuned-moderation` | https://huggingface.co/mbehbooei/vit-base-patch16-224-in21k-finetuned-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `medicalai/ClinicalBERT` | https://huggingface.co/medicalai/ClinicalBERT | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `menezesbruno/manaca-1b-base` | https://huggingface.co/menezesbruno/manaca-1b-base | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `mental/mental-bert-base-uncased` | https://huggingface.co/mental/mental-bert-base-uncased | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `meta-llama/Meta-Llama-3-70B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-70B-Instruct | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `meta-llama/Meta-Llama-3-8B` | https://huggingface.co/meta-llama/Meta-Llama-3-8B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `meta-llama/Meta-Llama-Guard-2-8B` | https://huggingface.co/meta-llama/Meta-Llama-Guard-2-8B | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `meta-models/Muse-Glimmer-30B` | https://huggingface.co/meta-models/Muse-Glimmer-30B | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `mezattn/eva02_base_patch14_448_moderation` | https://huggingface.co/mezattn/eva02_base_patch14_448_moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `michiyasunaga/BioLinkBERT-base` | https://huggingface.co/michiyasunaga/BioLinkBERT-base | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `michiyasunaga/BioLinkBERT-large` | https://huggingface.co/michiyasunaga/BioLinkBERT-large | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext` | https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/BiomedVLP-CXR-BERT-general` | https://huggingface.co/microsoft/BiomedVLP-CXR-BERT-general | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/BiomedVLP-CXR-BERT-specialized` | https://huggingface.co/microsoft/BiomedVLP-CXR-BERT-specialized | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/bitnet-b1.58-2B-4T` | https://huggingface.co/microsoft/bitnet-b1.58-2B-4T | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/codebert-base-mlm` | https://huggingface.co/microsoft/codebert-base-mlm | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/deberta-base` | https://huggingface.co/microsoft/deberta-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/deberta-v2-xlarge` | https://huggingface.co/microsoft/deberta-v2-xlarge | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/deberta-v3-small` | https://huggingface.co/microsoft/deberta-v3-small | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/deberta-v3-xsmall` | https://huggingface.co/microsoft/deberta-v3-xsmall | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/graphcodebert-base` | https://huggingface.co/microsoft/graphcodebert-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/infoxlm-large` | https://huggingface.co/microsoft/infoxlm-large | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/mpnet-base` | https://huggingface.co/microsoft/mpnet-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `microsoft/VibeVoice-ASR-Streaming-7B` | https://huggingface.co/microsoft/VibeVoice-ASR-Streaming-7B | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `miguelonana/camembert-bank-moderation-fr` | https://huggingface.co/miguelonana/camembert-bank-moderation-fr | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `MINSEONG12/moderation` | https://huggingface.co/MINSEONG12/moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mistralai/Mistral-7B-v0.1` | https://huggingface.co/mistralai/Mistral-7B-v0.1 | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `mixedbread-ai/mxbai-rerank-base-v2` | https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `mosaicml/mosaic-bert-base` | https://huggingface.co/mosaicml/mosaic-bert-base | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `moussaKam/mbarthez` | https://huggingface.co/moussaKam/mbarthez | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `mradermacher/BananaMind-Content-Safety-Mini-1.5-i1-GGUF` | https://huggingface.co/mradermacher/BananaMind-Content-Safety-Mini-1.5-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/BananaMind-V2.5-Content-Safety-GGUF` | https://huggingface.co/mradermacher/BananaMind-V2.5-Content-Safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/dipg-safety-agent-v2-float16-GGUF` | https://huggingface.co/mradermacher/dipg-safety-agent-v2-float16-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/GuardReasoner-VL-Eco-7B-i1-GGUF` | https://huggingface.co/mradermacher/GuardReasoner-VL-Eco-7B-i1-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Heretic-Nemotron-Content-Safety-Reasoning-4B-GGUF` | https://huggingface.co/mradermacher/Heretic-Nemotron-Content-Safety-Reasoning-4B-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Heretic-Nemotron-Content-Safety-Reasoning-4B-i1-GGUF` | https://huggingface.co/mradermacher/Heretic-Nemotron-Content-Safety-Reasoning-4B-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Innospark-72b-safety-GGUF` | https://huggingface.co/mradermacher/Innospark-72b-safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Intelligem-V1-Safety-0.3B-GGUF` | https://huggingface.co/mradermacher/Intelligem-V1-Safety-0.3B-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Mimo-Think-in-Safety-GGUF` | https://huggingface.co/mradermacher/Mimo-Think-in-Safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Open-Telco-LLM-8.3B-Safety-GGUF` | https://huggingface.co/mradermacher/Open-Telco-LLM-8.3B-Safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Reflector-Internalizing-Safety-Llama-3.1-8B-RL-GGUF` | https://huggingface.co/mradermacher/Reflector-Internalizing-Safety-Llama-3.1-8B-RL-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Reflector-Internalizing-Safety-Llama-3.1-8B-RL-i1-GGUF` | https://huggingface.co/mradermacher/Reflector-Internalizing-Safety-Llama-3.1-8B-RL-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/SafeAtlas-Guard-2B-GGUF` | https://huggingface.co/mradermacher/SafeAtlas-Guard-2B-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/SafeAtlas-Guard-4B-GGUF` | https://huggingface.co/mradermacher/SafeAtlas-Guard-4B-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/SafeAtlas-Guard-8B-GGUF` | https://huggingface.co/mradermacher/SafeAtlas-Guard-8B-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Safety-A1-ppo-full-GGUF` | https://huggingface.co/mradermacher/Safety-A1-ppo-full-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/SafeWork-RM-Safety-7B-i1-GGUF` | https://huggingface.co/mradermacher/SafeWork-RM-Safety-7B-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/saroku-safety-0.5b-GGUF` | https://huggingface.co/mradermacher/saroku-safety-0.5b-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Stentor-30M-Instruct-heretic-safety-defiltered-GGUF` | https://huggingface.co/mradermacher/Stentor-30M-Instruct-heretic-safety-defiltered-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/Stentor-30M-Instruct-heretic-safety-defiltered-i1-GGUF` | https://huggingface.co/mradermacher/Stentor-30M-Instruct-heretic-safety-defiltered-i1-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/TinyR1-Safety-8B-GGUF` | https://huggingface.co/mradermacher/TinyR1-Safety-8B-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `mradermacher/WaRP-Safety-Llama3_8B_Instruct-20251027_125759-GGUF` | https://huggingface.co/mradermacher/WaRP-Safety-Llama3_8B_Instruct-20251027_125759-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `MurrayTom/TS-Guard` | https://huggingface.co/MurrayTom/TS-Guard | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Musixmatch/umberto-commoncrawl-cased-v1` | https://huggingface.co/Musixmatch/umberto-commoncrawl-cased-v1 | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `NAMAA-Space/Ara-Prompt-Guard_V0` | https://huggingface.co/NAMAA-Space/Ara-Prompt-Guard_V0 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Nanbeige/Nanbeige4.1-3B` | https://huggingface.co/Nanbeige/Nanbeige4.1-3B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Nanbeige/Nanbeige4.2-3B` | https://huggingface.co/Nanbeige/Nanbeige4.2-3B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Nanbeige/Nanbeige4.2-3B-DSpark` | https://huggingface.co/Nanbeige/Nanbeige4.2-3B-DSpark | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nanonets/Nanonets-OCR-s` | https://huggingface.co/nanonets/Nanonets-OCR-s | 2026-09-07 | `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `naver/efficient-splade-VI-BT-large-query` | https://huggingface.co/naver/efficient-splade-VI-BT-large-query | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `NemoraAi/modernbert-chat-moderation-X-V2` | https://huggingface.co/NemoraAi/modernbert-chat-moderation-X-V2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `NemoraAi/roberta-chat-moderation-X` | https://huggingface.co/NemoraAi/roberta-chat-moderation-X | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `neulab/codebert-python` | https://huggingface.co/neulab/codebert-python | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `neuralmind/bert-base-portuguese-cased` | https://huggingface.co/neuralmind/bert-base-portuguese-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `NeuralTrust/prompt-guard-oss-small` | https://huggingface.co/NeuralTrust/prompt-guard-oss-small | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Niansuh/Prompt-Guard-86M` | https://huggingface.co/Niansuh/Prompt-Guard-86M | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Nikitojo/moderation` | https://huggingface.co/Nikitojo/moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `nisten/Biggie-SmoLlm-0.15B-Base` | https://huggingface.co/nisten/Biggie-SmoLlm-0.15B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nlpaueb/bert-base-uncased-contracts` | https://huggingface.co/nlpaueb/bert-base-uncased-contracts | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nlpaueb/legal-bert-base-uncased` | https://huggingface.co/nlpaueb/legal-bert-base-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nlpaueb/sec-bert-base` | https://huggingface.co/nlpaueb/sec-bert-base | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nomic-ai/nomic-bert-2048` | https://huggingface.co/nomic-ai/nomic-bert-2048 | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `NousResearch/Meta-Llama-3.1-8B-Instruct` | https://huggingface.co/NousResearch/Meta-Llama-3.1-8B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Null-Guard/LFM2.5-230M-distilled-Gemini-3.8-Flash` | https://huggingface.co/Null-Guard/LFM2.5-230M-distilled-Gemini-3.8-Flash | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Null-Guard/LFM2.5-230M-distilled-Gemini-3.8-Flash-Uncensored` | https://huggingface.co/Null-Guard/LFM2.5-230M-distilled-Gemini-3.8-Flash-Uncensored | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Null-Guard/LFM2.5-230M-Uncensored-GGUF` | https://huggingface.co/Null-Guard/LFM2.5-230M-Uncensored-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `nvidia/Aegis-AI-Content-Safety-LlamaGuard-Permissive-1.0` | https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Permissive-1.0 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `nvidia/Cosmos-Guardrail1` | https://huggingface.co/nvidia/Cosmos-Guardrail1 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `nvidia/instruction-data-guard` | https://huggingface.co/nvidia/instruction-data-guard | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `nvidia/LocateAnything-3B` | https://huggingface.co/nvidia/LocateAnything-3B | 2026-09-07 | `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nvidia/Minitron-4B-Base` | https://huggingface.co/nvidia/Minitron-4B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nvidia/Minitron-8B-Base` | https://huggingface.co/nvidia/Minitron-8B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nvidia/Mistral-NeMo-Minitron-8B-Base` | https://huggingface.co/nvidia/Mistral-NeMo-Minitron-8B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-Base-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-Base-BF16 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-Base-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-Base-BF16 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Base-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Base-BF16 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `nvidia/NVIDIA-Nemotron-Nano-12B-v2-Base` | https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-12B-v2-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `OctoThinker/OctoThinker-1B-Hybrid-Base` | https://huggingface.co/OctoThinker/OctoThinker-1B-Hybrid-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `onnx-community/Florence-2-base-ft` | https://huggingface.co/onnx-community/Florence-2-base-ft | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `opencerebral/Boris-1.7-D60M-n30M` | https://huggingface.co/opencerebral/Boris-1.7-D60M-n30M | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `openchat/openchat_3.5` | https://huggingface.co/openchat/openchat_3.5 | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `OpenVDN/vdn-minimax-h3` | https://huggingface.co/OpenVDN/vdn-minimax-h3 | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `opus-research/opus-moderation-1` | https://huggingface.co/opus-research/opus-moderation-1 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `opus-research/opus-moderation-2` | https://huggingface.co/opus-research/opus-moderation-2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `opus-research/opus-moderation-3` | https://huggingface.co/opus-research/opus-moderation-3 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `opus-research/opus-moderation-4-fast` | https://huggingface.co/opus-research/opus-moderation-4-fast | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `opus-research/opus-moderation-4-large` | https://huggingface.co/opus-research/opus-moderation-4-large | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `oshizo/japanese-sexual-moderation` | https://huggingface.co/oshizo/japanese-sexual-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `oshizo/japanese-sexual-moderation-v2` | https://huggingface.co/oshizo/japanese-sexual-moderation-v2 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `OwenElliott/image-safety-classifier-l` | https://huggingface.co/OwenElliott/image-safety-classifier-l | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `OwenElliott/image-safety-classifier-s` | https://huggingface.co/OwenElliott/image-safety-classifier-s | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `OwenElliott/image-safety-classifier-xs` | https://huggingface.co/OwenElliott/image-safety-classifier-xs | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `oxyapi/albert-moderation-001` | https://huggingface.co/oxyapi/albert-moderation-001 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `oxyapi/albert-moderation-001-ONNX` | https://huggingface.co/oxyapi/albert-moderation-001-ONNX | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `PaddlePaddle/PaddleOCR-VL` | https://huggingface.co/PaddlePaddle/PaddleOCR-VL | 2026-09-07 | `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `peculiar-ragdoll/Dirk-Qwen3.8-27B-GGUF` | https://huggingface.co/peculiar-ragdoll/Dirk-Qwen3.8-27B-GGUF | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF` | https://huggingface.co/peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF-MTP` | https://huggingface.co/peculiar-ragdoll/Tiel-Coder-35B-A3B-GGUF-MTP | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `perplexity-ai/pplx-pii-masking` | https://huggingface.co/perplexity-ai/pplx-pii-masking | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `pfnet/plamo-3-nict-2b-base` | https://huggingface.co/pfnet/plamo-3-nict-2b-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `phasefield-audio/Irodori-TTS-v4.1-Anime` | https://huggingface.co/phasefield-audio/Irodori-TTS-v4.1-Anime | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `pile-of-law/legalbert-large-1.7M-2` | https://huggingface.co/pile-of-law/legalbert-large-1.7M-2 | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `pipecat-ai/phonellm-alpha-1` | https://huggingface.co/pipecat-ai/phonellm-alpha-1 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `PL-RnD/privacy-moderation-large` | https://huggingface.co/PL-RnD/privacy-moderation-large | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `PL-RnD/privacy-moderation-large-4bit` | https://huggingface.co/PL-RnD/privacy-moderation-large-4bit | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `PL-RnD/privacy-moderation-small` | https://huggingface.co/PL-RnD/privacy-moderation-small | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `PL-RnD/privacy-moderation-small-onnx-8bit` | https://huggingface.co/PL-RnD/privacy-moderation-small-onnx-8bit | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `principled-intelligence/scope-guard-4B-q-2601` | https://huggingface.co/principled-intelligence/scope-guard-4B-q-2601 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `prism-ml/Bonsai-27B-gguf` | https://huggingface.co/prism-ml/Bonsai-27B-gguf | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `prism-ml/Ternary-Bonsai-27B-gguf` | https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `prithivMLmods/GA-Guard-AIO-GGUF` | https://huggingface.co/prithivMLmods/GA-Guard-AIO-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `prithivMLmods/VideoGuard-Qwen3.5-4B-Safety-RL-Uncensored` | https://huggingface.co/prithivMLmods/VideoGuard-Qwen3.5-4B-Safety-RL-Uncensored | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `prithivMLmods/VideoGuard-Qwen3.5-4B-Safety-RL-Uncensored-GGUF` | https://huggingface.co/prithivMLmods/VideoGuard-Qwen3.5-4B-Safety-RL-Uncensored-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `prithivMLmods/VideoGuard-Qwen3.5-9B-Safety-RL-Uncensored-GGUF` | https://huggingface.co/prithivMLmods/VideoGuard-Qwen3.5-9B-Safety-RL-Uncensored-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `PrunaAI/Meta-Llama-Guard-2-8B-GGUF-smashed` | https://huggingface.co/PrunaAI/Meta-Llama-Guard-2-8B-GGUF-smashed | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `QCRI/Fanar-1-9B-Instruct` | https://huggingface.co/QCRI/Fanar-1-9B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Qdrant/Splade_PP_en_v1` | https://huggingface.co/Qdrant/Splade_PP_en_v1 | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `QuantFactory/Meta-Llama-Guard-2-8B-GGUF` | https://huggingface.co/QuantFactory/Meta-Llama-Guard-2-8B-GGUF | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Qwen/QwQ-32B` | https://huggingface.co/Qwen/QwQ-32B | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Qwen/QwQ-32B-Preview` | https://huggingface.co/Qwen/QwQ-32B-Preview | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Raghav-Singhal/pbsftmix-cite-safety10-nosys-epe-3b-nobce` | https://huggingface.co/Raghav-Singhal/pbsftmix-cite-safety10-nosys-epe-3b-nobce | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Raghav-Singhal/pbsftmix-cite-safety10-nosys-normal-3b` | https://huggingface.co/Raghav-Singhal/pbsftmix-cite-safety10-nosys-normal-3b | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Raghav-Singhal/pbsftmix-cite-safety30-nosys-epe-3b-nobce` | https://huggingface.co/Raghav-Singhal/pbsftmix-cite-safety30-nosys-epe-3b-nobce | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Raghav-Singhal/pbsftmix-cite-safety30-nosys-normal-3b` | https://huggingface.co/Raghav-Singhal/pbsftmix-cite-safety30-nosys-normal-3b | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `regnant-io/kw5-lite-base` | https://huggingface.co/regnant-io/kw5-lite-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `RichardErkhov/alpindale_-_Llama-Guard-3-1B-gguf` | https://huggingface.co/RichardErkhov/alpindale_-_Llama-Guard-3-1B-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/Essacheez_-_Llama-2-7b-chat-SafetyData-finetune-translation-10k-old-prompt-style-gguf` | https://huggingface.co/RichardErkhov/Essacheez_-_Llama-2-7b-chat-SafetyData-finetune-translation-10k-old-prompt-style-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-code-1.2k-safetyllamas_stanford-default-style-gguf` | https://huggingface.co/RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-code-1.2k-safetyllamas_stanford-default-style-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-combine-4.2k-default-style-gguf` | https://huggingface.co/RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-combine-4.2k-default-style-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-summerization-1.2k-safetyllamas_stanford-default-style-gguf` | https://huggingface.co/RichardErkhov/Essacheez_-_LLAMA3.1-8b-SafetyData-summerization-1.2k-safetyllamas_stanford-default-style-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/guardrail_-_llama-2-7b-guanaco-instruct-sharded-gguf` | https://huggingface.co/RichardErkhov/guardrail_-_llama-2-7b-guanaco-instruct-sharded-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/ibm-granite_-_granite-guardian-3.0-2b-gguf` | https://huggingface.co/RichardErkhov/ibm-granite_-_granite-guardian-3.0-2b-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/ibm-granite_-_granite-guardian-3.0-8b-gguf` | https://huggingface.co/RichardErkhov/ibm-granite_-_granite-guardian-3.0-8b-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/meta-llama_-_Llama-Guard-3-1B-gguf` | https://huggingface.co/RichardErkhov/meta-llama_-_Llama-Guard-3-1B-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/skyai798_-_safety_v2_math_v1-gguf` | https://huggingface.co/RichardErkhov/skyai798_-_safety_v2_math_v1-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/thusinh1969_-_Guardian-V0.1-LLaMA3.1-8B-5G-6Oct2024-epoch1.3-gguf` | https://huggingface.co/RichardErkhov/thusinh1969_-_Guardian-V0.1-LLaMA3.1-8B-5G-6Oct2024-epoch1.3-gguf | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/Unispac_-_Gemma-2-9B-IT-With-Deeper-Safety-Alignment-gguf` | https://huggingface.co/RichardErkhov/Unispac_-_Gemma-2-9B-IT-With-Deeper-Safety-Alignment-gguf | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `RichardErkhov/ZiweiLiu96_-_llama-3.2-3b-Content-Moderation-gguf` | https://huggingface.co/RichardErkhov/ZiweiLiu96_-_llama-3.2-3b-Content-Moderation-gguf | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Roblox/voice-safety-classifier-v2` | https://huggingface.co/Roblox/voice-safety-classifier-v2 | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `rombodawg/Everyone-Coder-4x7b-Base` | https://huggingface.co/rombodawg/Everyone-Coder-4x7b-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Rostlab/prot_bert` | https://huggingface.co/Rostlab/prot_bert | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `rostlabs/rost-1b-base` | https://huggingface.co/rostlabs/rost-1b-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `RyanStudio/Mezzo-Prompt-Guard-v2-Base` | https://huggingface.co/RyanStudio/Mezzo-Prompt-Guard-v2-Base | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `s2w-ai/DarkBERT` | https://huggingface.co/s2w-ai/DarkBERT | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `SafetyMP/corporate-site-harness-llm` | https://huggingface.co/SafetyMP/corporate-site-harness-llm | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Sajeevan2001/bert-question-moderation` | https://huggingface.co/Sajeevan2001/bert-question-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `sapienzanlp/Minerva-350M-base-v1.0` | https://huggingface.co/sapienzanlp/Minerva-350M-base-v1.0 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sapienzanlp/Minerva-3B-base-v1.0` | https://huggingface.co/sapienzanlp/Minerva-3B-base-v1.0 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `saravanakarthikeyan/GuardShield-Qwen2.5-3B-16bit` | https://huggingface.co/saravanakarthikeyan/GuardShield-Qwen2.5-3B-16bit | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Saswith/text-moderation` | https://huggingface.co/Saswith/text-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `saturday-labs/turkish-pii-guard-0.8b` | https://huggingface.co/saturday-labs/turkish-pii-guard-0.8b | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Satya-dev-tech/toxic-comment-moderation` | https://huggingface.co/Satya-dev-tech/toxic-comment-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `sbintuitions/modernbert-ja-130m` | https://huggingface.co/sbintuitions/modernbert-ja-130m | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sentence-transformers/all-roberta-large-v1` | https://huggingface.co/sentence-transformers/all-roberta-large-v1 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sentence-transformers/multi-qa-distilbert-dot-v1` | https://huggingface.co/sentence-transformers/multi-qa-distilbert-dot-v1 | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sentence-transformers/multi-qa-mpnet-base-cos-v1` | https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-cos-v1 | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `seyonec/ChemBERTa-zinc-base-v1` | https://huggingface.co/seyonec/ChemBERTa-zinc-base-v1 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sheltron-ai/prompt-guard-68m` | https://huggingface.co/sheltron-ai/prompt-guard-68m | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Sheshank2609/content-moderation-distilbert` | https://huggingface.co/Sheshank2609/content-moderation-distilbert | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `shibing624/macbert4csc-base-chinese` | https://huggingface.co/shibing624/macbert4csc-base-chinese | 2026-09-07 | `hf_base_search`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `silicondali/doodle-magic-safety` | https://huggingface.co/silicondali/doodle-magic-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `skt/kogpt2-base-v2` | https://huggingface.co/skt/kogpt2-base-v2 | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `snkii/Sori-1B` | https://huggingface.co/snkii/Sori-1B | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `speakleash/Bielik-11B-v3.0-Instruct-awq` | https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct-awq | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `speakleash/Bielik-Guard-0.1B-v1.1` | https://huggingface.co/speakleash/Bielik-Guard-0.1B-v1.1 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `speakleash/Bielik-Guard-0.5B-v1.1` | https://huggingface.co/speakleash/Bielik-Guard-0.5B-v1.1 | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `stelterlab/Mistral-Small-24B-Instruct-2501-AWQ` | https://huggingface.co/stelterlab/Mistral-Small-24B-Instruct-2501-AWQ | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `StrictlyInsecure/discord-moderation-minilm` | https://huggingface.co/StrictlyInsecure/discord-moderation-minilm | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `StrictlyInsecure/discord-moderation-minilm-l12` | https://huggingface.co/StrictlyInsecure/discord-moderation-minilm-l12 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `studio-ousia/luke-base` | https://huggingface.co/studio-ousia/luke-base | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sullivan1502/base-action-grpo` | https://huggingface.co/sullivan1502/base-action-grpo | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sullivan1502/base-action-pretrain` | https://huggingface.co/sullivan1502/base-action-pretrain | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sullivan1502/base-action-sft` | https://huggingface.co/sullivan1502/base-action-sft | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sullivan1502/base-zone-grpo` | https://huggingface.co/sullivan1502/base-zone-grpo | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sullivan1502/base-zone-pretrain` | https://huggingface.co/sullivan1502/base-zone-pretrain | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `SulphurAI/Sulphur-2-base` | https://huggingface.co/SulphurAI/Sulphur-2-base | 2026-09-07 | `B_hf_conv_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `superwhisper/s1-mini` | https://huggingface.co/superwhisper/s1-mini | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `sweetpapa/sentry-270m-moderation-v3` | https://huggingface.co/sweetpapa/sentry-270m-moderation-v3 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `tencent/ContextPilot-14B` | https://huggingface.co/tencent/ContextPilot-14B | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `tencent/HunyuanImage-3.0` | https://huggingface.co/tencent/HunyuanImage-3.0 | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `tencent/HY-MT1.5-1.8B` | https://huggingface.co/tencent/HY-MT1.5-1.8B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `tencent/Hy-MT2-1.8B` | https://huggingface.co/tencent/Hy-MT2-1.8B | 2026-09-07 | `hf_textgen_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `tencent/Hy4-preview` | https://huggingface.co/tencent/Hy4-preview | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `TheBloke/merlyn-education-safety-GGUF` | https://huggingface.co/TheBloke/merlyn-education-safety-GGUF | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `thuml/sundial-base-128m` | https://huggingface.co/thuml/sundial-base-128m | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `togethercomputer/evo-1-8k-base` | https://huggingface.co/togethercomputer/evo-1-8k-base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `togethercomputer/GPT-JT-Moderation-6B` | https://huggingface.co/togethercomputer/GPT-JT-Moderation-6B | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `tohoku-nlp/bert-base-japanese` | https://huggingface.co/tohoku-nlp/bert-base-japanese | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `tohoku-nlp/bert-base-japanese-char-v2` | https://huggingface.co/tohoku-nlp/bert-base-japanese-char-v2 | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `tohoku-nlp/bert-base-japanese-whole-word-masking` | https://huggingface.co/tohoku-nlp/bert-base-japanese-whole-word-masking | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `TomLEE2026/image-moderation-v1` | https://huggingface.co/TomLEE2026/image-moderation-v1 | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `trl-internal-testing/tiny-Qwen3ForCausalLM-Instruct-2507` | https://huggingface.co/trl-internal-testing/tiny-Qwen3ForCausalLM-Instruct-2507 | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Twitter/twhin-bert-base` | https://huggingface.co/Twitter/twhin-bert-base | 2026-09-07 | `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `typhoon-ai/typhoon2-safety-preview` | https://huggingface.co/typhoon-ai/typhoon2-safety-preview | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `UBC-NLP/MARBERTv2` | https://huggingface.co/UBC-NLP/MARBERTv2 | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `unsloth/Meta-Llama-3.1-8B-Instruct` | https://huggingface.co/unsloth/Meta-Llama-3.1-8B-Instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `unsloth/Mistral-Nemo-Base-2407-bnb-4bit` | https://huggingface.co/unsloth/Mistral-Nemo-Base-2407-bnb-4bit | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `usail-hkust/JailJudge-guard` | https://huggingface.co/usail-hkust/JailJudge-guard | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `vaiv/GeM2-Llamion-14B-Base` | https://huggingface.co/vaiv/GeM2-Llamion-14B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `VertexAGI/prism-safety-1-micro` | https://huggingface.co/VertexAGI/prism-safety-1-micro | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Viggle/Viggle-Animate` | https://huggingface.co/Viggle/Viggle-Animate | 2026-09-07 | `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `vinai/bertweet-base` | https://huggingface.co/vinai/bertweet-base | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `vinai/phobert-base` | https://huggingface.co/vinai/phobert-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `Vrandan/Comment-Moderation` | https://huggingface.co/Vrandan/Comment-Moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `weeqeen/rubert-base-cased-finetuned-moderation` | https://huggingface.co/weeqeen/rubert-base-cased-finetuned-moderation | 2026-09-07 | `hf_moderation_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `weiweishi/roc-bert-base-zh` | https://huggingface.co/weiweishi/roc-bert-base-zh | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `westlake-repl/SaProt_650M_AF2` | https://huggingface.co/westlake-repl/SaProt_650M_AF2 | 2026-09-07 | `B_hf_fillmask_dl` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `winninghealth/WiNGPT2-Llama-3-8B-Base` | https://huggingface.co/winninghealth/WiNGPT2-Llama-3-8B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `XHToken/Spark-X2.5-1.7B` | https://huggingface.co/XHToken/Spark-X2.5-1.7B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `XHToken/Spark-X2.5-1.7B-Base` | https://huggingface.co/XHToken/Spark-X2.5-1.7B-Base | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `XHToken/Spark-X2.5-1.7B-GGUF` | https://huggingface.co/XHToken/Spark-X2.5-1.7B-GGUF | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `XHToken/Spark-X2.5-4B` | https://huggingface.co/XHToken/Spark-X2.5-4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `XHToken/Spark-X2.5-4B-Base` | https://huggingface.co/XHToken/Spark-X2.5-4B-Base | 2026-09-07 | `hf_textgen_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `XHToken/Spark-X2.5-4B-GGUF` | https://huggingface.co/XHToken/Spark-X2.5-4B-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `XiaomiMiMo/MiMo-7B-Base` | https://huggingface.co/XiaomiMiMo/MiMo-7B-Base | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `xlnet/xlnet-base-cased` | https://huggingface.co/xlnet/xlnet-base-cased | 2026-09-07 | `hf_base_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `yikuan8/Clinical-Longformer` | https://huggingface.co/yikuan8/Clinical-Longformer | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |
| `yueliu1999/GuardReasoner-8B` | https://huggingface.co/yueliu1999/GuardReasoner-8B | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `yueliu1999/GuardReasoner-VL-7B` | https://huggingface.co/yueliu1999/GuardReasoner-VL-7B | 2026-09-07 | `hf_guard_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `ZeroLoss-Lab/Innospark-72b-safety` | https://huggingface.co/ZeroLoss-Lab/Innospark-72b-safety | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `ZJU-Safety/DARWIN-Guard` | https://huggingface.co/ZJU-Safety/DARWIN-Guard | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `zjunlp/SafeEdit-Safety-Classifier` | https://huggingface.co/zjunlp/SafeEdit-Safety-Classifier | 2026-09-07 | `hf_safety_search` | fewer than 5,000 trailing-30-day downloads (category-scoped search floor) |
| `Zyphra/Zamba2-1.2B-instruct` | https://huggingface.co/Zyphra/Zamba2-1.2B-instruct | 2026-09-07 | `hf_instruct_search` | fewer than 1,000,000 trailing-30-day downloads (ranked-listing floor) |

## Duplicate mappings (739)

Every signal counted as a duplicate, with what it folded onto. This is the mapping behind
`raw_signals = duplicate_signals + unique_candidates`; the reconciliation can be recomputed from
this table and the three parked tables above. Every row here rests on one of the five kinds of
evidence in **What a fold has to rest on** — 463 byte-identical repeats, 88 declared artifacts,
7 resolution-ledger entries, 175 declared first-party family releases, 1 declared-tag format
redistribution and 5 retried paths for one hardware lookup. The 300 rows the third revision
carried on a folded name match are not here; they are in **Parked — a withdrawn fold**.

| signal | source URL | fetched | returned by | folds onto |
|---|---|---|---|---|
| `666DZY666/micronet` | https://github.com/666DZY666/micronet | 2026-09-07 | `comp_t_quant`, `B_comp_tensorrt` | repeats signal 666DZY666/micronet |
| `Adlik/Adlik` | https://github.com/Adlik/Adlik | 2026-09-07 | `comp_t_tensorcompiler`, `B_comp_engine` | repeats signal Adlik/Adlik |
| `Agent-Threat-Rule/agent-threat-rules` | https://github.com/Agent-Threat-Rule/agent-threat-rules | 2026-09-07 | `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal Agent-Threat-Rule/agent-threat-rules |
| `agentanywhere/shuddhi` | https://github.com/agentanywhere/shuddhi | 2026-09-07 | `dpt_dedup`, `dpt_q_dedup` | repeats signal agentanywhere/shuddhi |
| `agentcontrol/agent-control` | https://github.com/agentcontrol/agent-control | 2026-09-07 | `safe_t_guardrails`, `safe_t_aisafety` | repeats signal agentcontrol/agent-control |
| `akto-api-security/akto` | https://github.com/akto-api-security/akto | 2026-09-07 | `safe_t_guardrails`, `safe_t_redteam`, `B_safe_aisec` | repeats signal akto-api-security/akto |
| `akto-api-security/akto` | https://github.com/akto-api-security/akto | 2026-09-07 | `safe_t_guardrails`, `safe_t_redteam`, `B_safe_aisec` | repeats signal akto-api-security/akto |
| `alibaba/BladeDISC` | https://github.com/alibaba/BladeDISC | 2026-09-07 | `comp_t_mlir`, `comp_t_tensorcompiler` | repeats signal alibaba/BladeDISC |
| `apache/tvm` | https://github.com/apache/tvm | 2026-09-07 | `comp_t_tensorcompiler`, `B_comp_tvm` | head product apache-tvm |
| `apache/tvm` | https://github.com/apache/tvm | 2026-09-07 | `comp_t_tensorcompiler`, `B_comp_tvm` | repeats signal apache/tvm |
| `arcjet/arcjet-js` | https://github.com/arcjet/arcjet-js | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_agentsec` | repeats signal arcjet/arcjet-js |
| `argilla-io/distilabel` | https://github.com/argilla-io/distilabel | 2026-09-07 | `dpt_t_synthetic` | head product distilabel |
| `asamassekou10/ship-safe` | https://github.com/asamassekou10/ship-safe | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal asamassekou10/ship-safe |
| `asamassekou10/ship-safe` | https://github.com/asamassekou10/ship-safe | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal asamassekou10/ship-safe |
| `bespokelabsai/curator` | https://github.com/bespokelabsai/curator | 2026-09-07 | `dpt_t_synthetic`, `dpt_q_curator` | repeats signal bespokelabsai/curator |
| `bitsandbytes-foundation/bitsandbytes` | https://github.com/bitsandbytes-foundation/bitsandbytes | 2026-09-07 | `comp_t_quant` | head product bitsandbytes |
| `bytedance/Dolphin` | https://github.com/bytedance/Dolphin | 2026-09-07 | `B_dpt_ocrpdf` | resolution ledger: excluded_boundary |
| `CatchTheTornado/text-extract-api` | https://github.com/CatchTheTornado/text-extract-api | 2026-09-07 | `dpt_q_pdf`, `B_dpt_ocrpdf`, `B_safe_pii` | repeats signal CatchTheTornado/text-extract-api |
| `CatchTheTornado/text-extract-api` | https://github.com/CatchTheTornado/text-extract-api | 2026-09-07 | `dpt_q_pdf`, `B_dpt_ocrpdf`, `B_safe_pii` | repeats signal CatchTheTornado/text-extract-api |
| `CHATS-lab/verbalized-sampling` | https://github.com/CHATS-lab/verbalized-sampling | 2026-09-07 | `dpt_synth`, `dpt_t_synthetic` | repeats signal CHATS-lab/verbalized-sampling |
| `chrisliu298/awesome-llm-unlearning` | https://github.com/chrisliu298/awesome-llm-unlearning | 2026-09-07 | `safe_t_aisafety`, `B_safe_llmsafety` | repeats signal chrisliu298/awesome-llm-unlearning |
| `cleanlab/cleanlab` | https://github.com/cleanlab/cleanlab | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal cleanlab/cleanlab |
| `cleanlab/cleanlab-studio` | https://github.com/cleanlab/cleanlab-studio | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal cleanlab/cleanlab-studio |
| `coderonion/awesome-cuda-and-hpc` | https://github.com/coderonion/awesome-cuda-and-hpc | 2026-09-07 | `comp_t_mlir`, `comp_t_triton`, `B_comp_tvm` | repeats signal coderonion/awesome-cuda-and-hpc |
| `coderonion/awesome-cuda-and-hpc` | https://github.com/coderonion/awesome-cuda-and-hpc | 2026-09-07 | `comp_t_mlir`, `comp_t_triton`, `B_comp_tvm` | repeats signal coderonion/awesome-cuda-and-hpc |
| `confident-ai/deepteam` | https://github.com/confident-ai/deepteam | 2026-09-07 | `B_safe_llmsafety` | head product deepteam |
| `cvs-health/uqlm` | https://github.com/cvs-health/uqlm | 2026-09-07 | `safe_t_aisafety`, `B_safe_llmsafety` | repeats signal cvs-health/uqlm |
| `CyberStrikeus/CyberStrike` | https://github.com/CyberStrikeus/CyberStrike | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam`, `B_safe_aisec` | repeats signal CyberStrikeus/CyberStrike |
| `CyberStrikeus/CyberStrike` | https://github.com/CyberStrikeus/CyberStrike | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam`, `B_safe_aisec` | repeats signal CyberStrikeus/CyberStrike |
| `daochenzha/data-centric-AI` | https://github.com/daochenzha/data-centric-AI | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal daochenzha/data-centric-AI |
| `data-privacy-stack/presidio` | https://github.com/data-privacy-stack/presidio | 2026-09-07 | `safe_t_guardrails`, `B_safe_pii` | repeats signal data-privacy-stack/presidio |
| `datajuicer/data-juicer` | https://github.com/datajuicer/data-juicer | 2026-09-07 | `dpt_t_synthetic` | head product data-juicer |
| `deadbits/vigil-llm` | https://github.com/deadbits/vigil-llm | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal deadbits/vigil-llm |
| `dphnAI/sonar` | https://github.com/dphnAI/sonar | 2026-09-07 | `B_comp_engine` | head product sonar |
| `duncatzat/vigils` | https://github.com/duncatzat/vigils | 2026-09-07 | `B_safe_pii`, `B_safe_agentsec` | repeats signal duncatzat/vigils |
| `duoan/mega-data-factory` | https://github.com/duoan/mega-data-factory | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal duoan/mega-data-factory |
| `ethz-spylab/agentdojo` | https://github.com/ethz-spylab/agentdojo | 2026-09-07 | `safe_t_promptinjection` | head product agentdojo |
| `evidentlyai/evidently` | https://github.com/evidentlyai/evidently | 2026-09-07 | `dpt_t_dataquality` | head product evidently |
| `faiyazabdullah/JailbreakTracer` | https://github.com/faiyazabdullah/JailbreakTracer | 2026-09-07 | `dpt_synth`, `safe_q_jailbreak` | repeats signal faiyazabdullah/JailbreakTracer |
| `FareedKhan-dev/kimi-k3-in-c` | https://github.com/FareedKhan-dev/kimi-k3-in-c | 2026-09-07 | `comp_t_quant`, `B_comp_engine` | repeats signal FareedKhan-dev/kimi-k3-in-c |
| `feast-dev/feast` | https://github.com/feast-dev/feast | 2026-09-07 | `dpt_t_dataquality` | head product feast |
| `FedML-AI/FedML` | https://github.com/FedML-AI/FedML | 2026-09-07 | `edge_t_edgeai`, `B_comp_engine` | repeats signal FedML-AI/FedML |
| `firecrawl/firecrawl` | https://github.com/firecrawl/firecrawl | 2026-09-07 | `dpt_t_webscraping` | head product firecrawl |
| `getagentseal/agentseal` | https://github.com/getagentseal/agentseal | 2026-09-07 | `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal getagentseal/agentseal |
| `Giskard-AI/giskard-oss` | https://github.com/Giskard-AI/giskard-oss | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_aisec` | head product giskard |
| `Giskard-AI/giskard-oss` | https://github.com/Giskard-AI/giskard-oss | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_aisec` | repeats signal Giskard-AI/giskard-oss |
| `google-ai-edge/LiteRT-LM` | https://github.com/google-ai-edge/LiteRT-LM | 2026-09-07 | `edge_t_edgeai` | head product litert-lm |
| `GrayboxTech/weightslab` | https://github.com/GrayboxTech/weightslab | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal GrayboxTech/weightslab |
| `hashgraph-online/hol-guard` | https://github.com/hashgraph-online/hol-guard | 2026-09-07 | `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal hashgraph-online/hol-guard |
| `hiyouga/LlamaFactory` | https://github.com/hiyouga/LlamaFactory | 2026-09-07 | `comp_t_quant` | head product llama-factory |
| `HKUSTDial/flash-sparse-attention` | https://github.com/HKUSTDial/flash-sparse-attention | 2026-09-07 | `comp_t_triton` | head product flash-sparse-attention |
| `huggingface/optimum` | https://github.com/huggingface/optimum | 2026-09-07 | `comp_t_quant` | head product optimum |
| `ifixai-ai/iFixAi` | https://github.com/ifixai-ai/iFixAi | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety` | repeats signal ifixai-ai/iFixAi |
| `ifixai-ai/iFixAi` | https://github.com/ifixai-ai/iFixAi | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety` | repeats signal ifixai-ai/iFixAi |
| `intel/neural-compressor` | https://github.com/intel/neural-compressor | 2026-09-07 | `comp_t_quant` | head product intel-neural-compressor |
| `iree-org/iree` | https://github.com/iree-org/iree | 2026-09-07 | `comp_t_mlir` | head product iree |
| `kenryu42/cc-safety-net` | https://github.com/kenryu42/cc-safety-net | 2026-09-07 | `safe_t_guardrails`, `safe_t_aisafety` | repeats signal kenryu42/cc-safety-net |
| `KeygraphHQ/shannon` | https://github.com/KeygraphHQ/shannon | 2026-09-07 | `safe_t_redteam`, `B_safe_aisec` | repeats signal KeygraphHQ/shannon |
| `KeyValueSoftwareSystems/agent-opfor` | https://github.com/KeyValueSoftwareSystems/agent-opfor | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal KeyValueSoftwareSystems/agent-opfor |
| `lemonade-sdk/lemonade` | https://github.com/lemonade-sdk/lemonade | 2026-09-07 | `edge_t_npu` | head product lemonade |
| `Lexsi-Labs/CuratorKIT` | https://github.com/Lexsi-Labs/CuratorKIT | 2026-09-07 | `dpt_synth`, `dpt_q_curator` | repeats signal Lexsi-Labs/CuratorKIT |
| `linkedin/Liger-Kernel` | https://github.com/linkedin/Liger-Kernel | 2026-09-07 | `comp_t_triton` | head product liger-kernel |
| `llmware-ai/llmware` | https://github.com/llmware-ai/llmware | 2026-09-07 | `comp_t_onnx` | resolution ledger: excluded_boundary |
| `luckyPipewrench/pipelock` | https://github.com/luckyPipewrench/pipelock | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal luckyPipewrench/pipelock |
| `luckyPipewrench/pipelock` | https://github.com/luckyPipewrench/pipelock | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal luckyPipewrench/pipelock |
| `magpie-align/magpie` | https://github.com/magpie-align/magpie | 2026-09-07 | `dpt_synth`, `dpt_t_synthetic`, `B_dpt_datasetllm` | repeats signal magpie-align/magpie |
| `magpie-align/magpie` | https://github.com/magpie-align/magpie | 2026-09-07 | `dpt_synth`, `dpt_t_synthetic`, `B_dpt_datasetllm` | repeats signal magpie-align/magpie |
| `maziyarpanahi/openmed` | https://github.com/maziyarpanahi/openmed | 2026-09-07 | `B_safe_pii` | resolution ledger: excluded_boundary |
| `MegEngine/MegCC` | https://github.com/MegEngine/MegCC | 2026-09-07 | `comp_t_mlir`, `comp_t_tensorcompiler` | repeats signal MegEngine/MegCC |
| `Megvii-BaseDetection/YOLOX` | https://github.com/Megvii-BaseDetection/YOLOX | 2026-09-07 | `comp_t_onnx`, `B_comp_tensorrt` | repeats signal Megvii-BaseDetection/YOLOX |
| `microsoft/onnxruntime` | https://github.com/microsoft/onnxruntime | 2026-09-07 | `comp_t_onnx` | head product onnx-runtime |
| `MigoXLab/awesome-data-quality` | https://github.com/MigoXLab/awesome-data-quality | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal MigoXLab/awesome-data-quality |
| `mlc-ai/mlc-llm` | https://github.com/mlc-ai/mlc-llm | 2026-09-07 | `B_comp_tvm` | head product mlc-llm |
| `msoedov/agentic_security` | https://github.com/msoedov/agentic_security | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_agentsec` | repeats signal msoedov/agentic_security |
| `nolabs-ai/nono` | https://github.com/nolabs-ai/nono | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_aisec`, `B_safe_agentsec` | head product nono |
| `nolabs-ai/nono` | https://github.com/nolabs-ai/nono | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal nolabs-ai/nono |
| `nolabs-ai/nono` | https://github.com/nolabs-ai/nono | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal nolabs-ai/nono |
| `NVIDIA-NeMo/Curator` | https://github.com/NVIDIA-NeMo/Curator | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dedup`, `dpt_q_curator` | head product nemo-curator |
| `NVIDIA-NeMo/Curator` | https://github.com/NVIDIA-NeMo/Curator | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dedup`, `dpt_q_curator` | repeats signal NVIDIA-NeMo/Curator |
| `NVIDIA-NeMo/Curator` | https://github.com/NVIDIA-NeMo/Curator | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dedup`, `dpt_q_curator` | repeats signal NVIDIA-NeMo/Curator |
| `NVIDIA-NeMo/DataDesigner` | https://github.com/NVIDIA-NeMo/DataDesigner | 2026-09-07 | `dpt_t_synthetic`, `B_dpt_augment` | head product nemo-data-designer |
| `NVIDIA-NeMo/DataDesigner` | https://github.com/NVIDIA-NeMo/DataDesigner | 2026-09-07 | `dpt_t_synthetic`, `B_dpt_augment` | repeats signal NVIDIA-NeMo/DataDesigner |
| `NVIDIA-NeMo/Guardrails` | https://github.com/NVIDIA-NeMo/Guardrails | 2026-09-07 | `safe_t_guardrails`, `safe_t_llmsecurity`, `B_safe_llmsafety` | head product nemo-guardrails |
| `NVIDIA-NeMo/Guardrails` | https://github.com/NVIDIA-NeMo/Guardrails | 2026-09-07 | `safe_t_guardrails`, `safe_t_llmsecurity`, `B_safe_llmsafety` | repeats signal NVIDIA-NeMo/Guardrails |
| `NVIDIA-NeMo/Guardrails` | https://github.com/NVIDIA-NeMo/Guardrails | 2026-09-07 | `safe_t_guardrails`, `safe_t_llmsecurity`, `B_safe_llmsafety` | repeats signal NVIDIA-NeMo/Guardrails |
| `NVIDIA/garak` | https://github.com/NVIDIA/garak | 2026-09-07 | `safe_t_llmsecurity` | head product garak |
| `NVIDIA/SkillSpector` | https://github.com/NVIDIA/SkillSpector | 2026-09-07 | `safe_t_promptinjection`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal NVIDIA/SkillSpector |
| `NVIDIA/SkillSpector` | https://github.com/NVIDIA/SkillSpector | 2026-09-07 | `safe_t_promptinjection`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal NVIDIA/SkillSpector |
| `NVIDIA/TensorRT` | https://github.com/NVIDIA/TensorRT | 2026-09-07 | `B_comp_tensorrt` | head product tensorrt |
| `OAID/Tengine` | https://github.com/OAID/Tengine | 2026-09-07 | `comp_t_onnx`, `edge_t_npu`, `B_comp_tensorrt` | repeats signal OAID/Tengine |
| `OAID/Tengine` | https://github.com/OAID/Tengine | 2026-09-07 | `comp_t_onnx`, `edge_t_npu`, `B_comp_tensorrt` | repeats signal OAID/Tengine |
| `off-grid-ai/OGAM` | https://github.com/off-grid-ai/OGAM | 2026-09-07 | `edge_t_edgeai` | head product ogam |
| `onnx/onnx` | https://github.com/onnx/onnx | 2026-09-07 | `comp_t_onnx` | head product onnx |
| `opendatalab/MinerU` | https://github.com/opendatalab/MinerU | 2026-09-07 | `B_dpt_ocrpdf` | head product mineru |
| `opendataloader-project/opendataloader-pdf` | https://github.com/opendataloader-project/opendataloader-pdf | 2026-09-07 | `B_dpt_ocrpdf` | tail row opendataloader-pdf |
| `Pantheon-Security/medusa` | https://github.com/Pantheon-Security/medusa | 2026-09-07 | `safe_t_llmsecurity`, `B_safe_agentsec` | repeats signal Pantheon-Security/medusa |
| `pathwaycom/llm-app` | https://github.com/pathwaycom/llm-app | 2026-09-07 | `safe_t_llmsecurity` | resolution ledger: excluded_boundary |
| `pegasi-ai/reins` | https://github.com/pegasi-ai/reins | 2026-09-07 | `safe_t_aisafety`, `B_safe_agentsec` | repeats signal pegasi-ai/reins |
| `PrismorSec/prismor` | https://github.com/PrismorSec/prismor | 2026-09-07 | `safe_t_promptinjection`, `safe_t_aisafety`, `B_safe_agentsec` | repeats signal PrismorSec/prismor |
| `PrismorSec/prismor` | https://github.com/PrismorSec/prismor | 2026-09-07 | `safe_t_promptinjection`, `safe_t_aisafety`, `B_safe_agentsec` | repeats signal PrismorSec/prismor |
| `promptfoo/promptfoo` | https://github.com/promptfoo/promptfoo | 2026-09-07 | `safe_t_redteam` | head product promptfoo |
| `protectai/llm-guard` | https://github.com/protectai/llm-guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | head product llm-guard |
| `protectai/llm-guard` | https://github.com/protectai/llm-guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal protectai/llm-guard |
| `PSAL-POSTECH/PyTorchSim` | https://github.com/PSAL-POSTECH/PyTorchSim | 2026-09-07 | `comp_t_tensorcompiler`, `edge_t_npu` | repeats signal PSAL-POSTECH/PyTorchSim |
| `pytorch/ao` | https://github.com/pytorch/ao | 2026-09-07 | `comp_t_quant` | head product torchao |
| `pytorch/TensorRT` | https://github.com/pytorch/TensorRT | 2026-09-07 | `B_comp_tensorrt` | head product torch-tensorrt |
| `qualcomm/aimet` | https://github.com/qualcomm/aimet | 2026-09-07 | `comp_t_quant` | head product aimet |
| `RapidAI/RapidOCR` | https://github.com/RapidAI/RapidOCR | 2026-09-07 | `B_comp_tensorrt` | resolution ledger: excluded_boundary |
| `Renumics/awesome-open-data-centric-ai` | https://github.com/Renumics/awesome-open-data-centric-ai | 2026-09-07 | `dpt_t_synthetic`, `dpt_t_datacentric` | repeats signal Renumics/awesome-open-data-centric-ai |
| `run-llama/liteparse` | https://github.com/run-llama/liteparse | 2026-09-07 | `B_dpt_ocrpdf` | tail row liteparse |
| `SantanderAI/autoguardrails` | https://github.com/SantanderAI/autoguardrails | 2026-09-07 | `safe_t_moderation`, `B_safe_llmsafety` | repeats signal SantanderAI/autoguardrails |
| `secureagentics/Adrian` | https://github.com/secureagentics/Adrian | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal secureagentics/Adrian |
| `secureagentics/Adrian` | https://github.com/secureagentics/Adrian | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal secureagentics/Adrian |
| `sipeed/MaixPy` | https://github.com/sipeed/MaixPy | 2026-09-07 | `edge_t_edgeai` | head product sipeed-maixcam |
| `splx-ai/agentic-radar` | https://github.com/splx-ai/agentic-radar | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam` | repeats signal splx-ai/agentic-radar |
| `SponsioLabs/Sponsio` | https://github.com/SponsioLabs/Sponsio | 2026-09-07 | `safe_t_guardrails`, `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal SponsioLabs/Sponsio |
| `SponsioLabs/Sponsio` | https://github.com/SponsioLabs/Sponsio | 2026-09-07 | `safe_t_guardrails`, `safe_t_promptinjection`, `B_safe_agentsec` | repeats signal SponsioLabs/Sponsio |
| `superagent-ai/superagent` | https://github.com/superagent-ai/superagent | 2026-09-07 | `safe_t_guardrails`, `safe_t_promptinjection` | repeats signal superagent-ai/superagent |
| `Tencent/AI-Infra-Guard` | https://github.com/Tencent/AI-Infra-Guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal Tencent/AI-Infra-Guard |
| `Tencent/AI-Infra-Guard` | https://github.com/Tencent/AI-Infra-Guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal Tencent/AI-Infra-Guard |
| `Tencent/AI-Infra-Guard` | https://github.com/Tencent/AI-Infra-Guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal Tencent/AI-Infra-Guard |
| `Tencent/AI-Infra-Guard` | https://github.com/Tencent/AI-Infra-Guard | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `safe_t_aisafety`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal Tencent/AI-Infra-Guard |
| `Tencent/ncnn` | https://github.com/Tencent/ncnn | 2026-09-07 | `comp_t_mlir`, `comp_t_onnx` | head product ncnn |
| `Tencent/ncnn` | https://github.com/Tencent/ncnn | 2026-09-07 | `comp_t_mlir`, `comp_t_onnx` | repeats signal Tencent/ncnn |
| `tg12/gpt_jailbreak_status` | https://github.com/tg12/gpt_jailbreak_status | 2026-09-07 | `safe_t_promptinjection`, `safe_t_aisafety` | repeats signal tg12/gpt_jailbreak_status |
| `thu-ml/SageAttention` | https://github.com/thu-ml/SageAttention | 2026-09-07 | `comp_t_quant`, `comp_t_triton` | head product sageattention |
| `thu-ml/SageAttention` | https://github.com/thu-ml/SageAttention | 2026-09-07 | `comp_t_quant`, `comp_t_triton` | repeats signal thu-ml/SageAttention |
| `Tianxiaomo/pytorch-YOLOv4` | https://github.com/Tianxiaomo/pytorch-YOLOv4 | 2026-09-07 | `comp_t_onnx`, `B_comp_tensorrt` | repeats signal Tianxiaomo/pytorch-YOLOv4 |
| `TingsongYu/PyTorch-Tutorial-2nd` | https://github.com/TingsongYu/PyTorch-Tutorial-2nd | 2026-09-07 | `comp_t_onnx`, `B_comp_tensorrt` | repeats signal TingsongYu/PyTorch-Tutorial-2nd |
| `toby-bridges/api-relay-audit` | https://github.com/toby-bridges/api-relay-audit | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection` | repeats signal toby-bridges/api-relay-audit |
| `uber/ADR` | https://github.com/uber/ADR | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal uber/ADR |
| `uber/ADR` | https://github.com/uber/ADR | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal uber/ADR |
| `uber/ADR` | https://github.com/uber/ADR | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_promptinjection`, `B_safe_aisec`, `B_safe_agentsec` | repeats signal uber/ADR |
| `ultralytics/yolov3` | https://github.com/ultralytics/yolov3 | 2026-09-07 | `comp_t_onnx`, `edge_t_edgeai`, `B_comp_tensorrt` | repeats signal ultralytics/yolov3 |
| `ultralytics/yolov3` | https://github.com/ultralytics/yolov3 | 2026-09-07 | `comp_t_onnx`, `edge_t_edgeai`, `B_comp_tensorrt` | repeats signal ultralytics/yolov3 |
| `ultralytics/yolov5` | https://github.com/ultralytics/yolov5 | 2026-09-07 | `comp_t_onnx`, `B_comp_tensorrt` | repeats signal ultralytics/yolov5 |
| `usestrix/strix` | https://github.com/usestrix/strix | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam`, `B_safe_aisec` | resolution ledger: excluded_boundary |
| `usestrix/strix` | https://github.com/usestrix/strix | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam`, `B_safe_aisec` | repeats signal usestrix/strix |
| `usestrix/strix` | https://github.com/usestrix/strix | 2026-09-07 | `safe_t_llmsecurity`, `safe_t_redteam`, `B_safe_aisec` | repeats signal usestrix/strix |
| `utkusen/promptmap` | https://github.com/utkusen/promptmap | 2026-09-07 | `safe_t_promptinjection`, `B_safe_aisec` | repeats signal utkusen/promptmap |
| `visual-layer/fastdup` | https://github.com/visual-layer/fastdup | 2026-09-07 | `dpt_t_datacentric`, `B_dpt_augment` | repeats signal visual-layer/fastdup |
| `vllm-project/llm-compressor` | https://github.com/vllm-project/llm-compressor | 2026-09-07 | `comp_t_quant` | head product llm-compressor |
| `voxel51/fiftyone` | https://github.com/voxel51/fiftyone | 2026-09-07 | `dpt_t_datacentric`, `dpt_t_dataquality` | repeats signal voxel51/fiftyone |
| `whylabs/whylogs` | https://github.com/whylabs/whylogs | 2026-09-07 | `dpt_t_dataquality` | head product whylabs |
| `Xilinx/mlir-aie` | https://github.com/Xilinx/mlir-aie | 2026-09-07 | `comp_t_mlir`, `edge_t_npu` | repeats signal Xilinx/mlir-aie |
| `xlite-dev/lite.ai.toolkit` | https://github.com/xlite-dev/lite.ai.toolkit | 2026-09-07 | `comp_t_onnx`, `B_comp_tensorrt` | repeats signal xlite-dev/lite.ai.toolkit |
| `xLLM-AI/xllm` | https://github.com/xLLM-AI/xllm | 2026-09-07 | `B_comp_engine` | head product xllm |
| `yusufkaraaslan/Skill_Seekers` | https://github.com/yusufkaraaslan/Skill_Seekers | 2026-09-07 | `B_dpt_ocrpdf` | resolution ledger: excluded_boundary |
| `zengxiao-he/tessera` | https://github.com/zengxiao-he/tessera | 2026-09-07 | `comp_t_triton`, `B_comp_engine` | repeats signal zengxiao-he/tessera |
| `01-ai/Yi-34B` | https://huggingface.co/01-ai/Yi-34B | 2026-09-07 | `hf_textgen_likes` | release or SKU of yi |
| `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF` | https://huggingface.co/0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | repeats signal 0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF |
| `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF` | https://huggingface.co/0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | repeats signal 0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF |
| `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF` | https://huggingface.co/0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | repeats signal 0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF |
| `airesearch/wangchanberta-base-att-spm-uncased` | https://huggingface.co/airesearch/wangchanberta-base-att-spm-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal airesearch/wangchanberta-base-att-spm-uncased |
| `albert/albert-base-v2` | https://huggingface.co/albert/albert-base-v2 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal albert/albert-base-v2 |
| `allenai/OLMo-2-0425-1B` | https://huggingface.co/allenai/OLMo-2-0425-1B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of olmo |
| `allenai/Olmo-3-7B-Instruct` | https://huggingface.co/allenai/Olmo-3-7B-Instruct | 2026-09-07 | `hf_instruct_search` | head product olmo-instruct |
| `almanach/camembert-base` | https://huggingface.co/almanach/camembert-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal almanach/camembert-base |
| `answerdotai/ModernBERT-base` | https://huggingface.co/answerdotai/ModernBERT-base | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal answerdotai/ModernBERT-base |
| `answerdotai/ModernBERT-base` | https://huggingface.co/answerdotai/ModernBERT-base | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal answerdotai/ModernBERT-base |
| `answerdotai/ModernBERT-large` | https://huggingface.co/answerdotai/ModernBERT-large | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal answerdotai/ModernBERT-large |
| `antirez/deepseek-v4-gguf` | https://huggingface.co/antirez/deepseek-v4-gguf | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal antirez/deepseek-v4-gguf |
| `apple/OpenELM-1_1B-Instruct` | https://huggingface.co/apple/OpenELM-1_1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal apple/OpenELM-1_1B-Instruct |
| `aubmindlab/bert-base-arabertv02` | https://huggingface.co/aubmindlab/bert-base-arabertv02 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal aubmindlab/bert-base-arabertv02 |
| `BreezeBlue/Breeze-TTS-2` | https://huggingface.co/BreezeBlue/Breeze-TTS-2 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal BreezeBlue/Breeze-TTS-2 |
| `ByteDance-Seed/Seed-OSS-36B-Base` | https://huggingface.co/ByteDance-Seed/Seed-OSS-36B-Base | 2026-09-07 | `hf_base_search` | head product seed-oss |
| `ByteDance/Ouro-1.4B` | https://huggingface.co/ByteDance/Ouro-1.4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal ByteDance/Ouro-1.4B |
| `chandar-lab/NeoBERT` | https://huggingface.co/chandar-lab/NeoBERT | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal chandar-lab/NeoBERT |
| `CohereLabs/c4ai-command-r-plus` | https://huggingface.co/CohereLabs/c4ai-command-r-plus | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal CohereLabs/c4ai-command-r-plus |
| `CohereLabs/c4ai-command-r-v01` | https://huggingface.co/CohereLabs/c4ai-command-r-v01 | 2026-09-07 | `hf_textgen_likes` | head product command-r |
| `cointegrated/rubert-tiny2` | https://huggingface.co/cointegrated/rubert-tiny2 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal cointegrated/rubert-tiny2 |
| `Comfy-Org/MiniMax-H3` | https://huggingface.co/Comfy-Org/MiniMax-H3 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal Comfy-Org/MiniMax-H3 |
| `dccuchile/bert-base-spanish-wwm-uncased` | https://huggingface.co/dccuchile/bert-base-spanish-wwm-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal dccuchile/bert-base-spanish-wwm-uncased |
| `dealignai/GLM-5.3-CYBERSECURITY-FP8` | https://huggingface.co/dealignai/GLM-5.3-CYBERSECURITY-FP8 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal dealignai/GLM-5.3-CYBERSECURITY-FP8 |
| `deepseek-ai/deepseek-coder-1.3b-base` | https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-coder-6.7b-base` | https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-coder-6.7b-instruct` | https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-coder-7b-instruct-v1.5` | https://huggingface.co/deepseek-ai/deepseek-coder-7b-instruct-v1.5 | 2026-09-07 | `hf_instruct_search` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-Coder-V2-Lite-Base` | https://huggingface.co/deepseek-ai/DeepSeek-Coder-V2-Lite-Base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | https://huggingface.co/deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct | 2026-09-07 | `hf_instruct_search` | head product deepseek-coder |
| `deepseek-ai/deepseek-llm-67b-base` | https://huggingface.co/deepseek-ai/deepseek-llm-67b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-llm-7b-base` | https://huggingface.co/deepseek-ai/deepseek-llm-7b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/deepseek-moe-16b-base` | https://huggingface.co/deepseek-ai/deepseek-moe-16b-base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-R1` | https://huggingface.co/deepseek-ai/DeepSeek-R1 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | head product deepseek-r1 |
| `deepseek-ai/DeepSeek-R1` | https://huggingface.co/deepseek-ai/DeepSeek-R1 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-R1 |
| `deepseek-ai/DeepSeek-R1-0528` | https://huggingface.co/deepseek-ai/DeepSeek-R1-0528 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | head product deepseek-r1 |
| `deepseek-ai/DeepSeek-R1-0528` | https://huggingface.co/deepseek-ai/DeepSeek-R1-0528 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-R1-0528 |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-R1-Distill-Qwen-32B |
| `deepseek-ai/DeepSeek-V3` | https://huggingface.co/deepseek-ai/DeepSeek-V3 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V3` | https://huggingface.co/deepseek-ai/DeepSeek-V3 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V3 |
| `deepseek-ai/DeepSeek-V3` | https://huggingface.co/deepseek-ai/DeepSeek-V3 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V3 |
| `deepseek-ai/DeepSeek-V3-0324` | https://huggingface.co/deepseek-ai/DeepSeek-V3-0324 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V3-0324` | https://huggingface.co/deepseek-ai/DeepSeek-V3-0324 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V3-0324 |
| `deepseek-ai/DeepSeek-V3-0324` | https://huggingface.co/deepseek-ai/DeepSeek-V3-0324 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V3-0324 |
| `deepseek-ai/DeepSeek-V3.1-Base` | https://huggingface.co/deepseek-ai/DeepSeek-V3.1-Base | 2026-09-07 | `hf_base_search` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V3.2` | https://huggingface.co/deepseek-ai/DeepSeek-V3.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product deepseek |
| `deepseek-ai/DeepSeek-V3.2` | https://huggingface.co/deepseek-ai/DeepSeek-V3.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V3.2 |
| `deepseek-ai/DeepSeek-V3.2` | https://huggingface.co/deepseek-ai/DeepSeek-V3.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V3.2 |
| `deepseek-ai/DeepSeek-V3.2` | https://huggingface.co/deepseek-ai/DeepSeek-V3.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V3.2 |
| `deepseek-ai/DeepSeek-V4-Flash` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product deepseek |
| `deepseek-ai/DeepSeek-V4-Flash` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash |
| `deepseek-ai/DeepSeek-V4-Flash` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash |
| `deepseek-ai/DeepSeek-V4-Flash` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash |
| `deepseek-ai/DeepSeek-V4-Flash` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-0731` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Flash-0731 |
| `deepseek-ai/DeepSeek-V4-Flash-Vision-Exp` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of deepseek |
| `deepseek-ai/DeepSeek-V4-Flash-Vision-Exp` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal deepseek-ai/DeepSeek-V4-Flash-Vision-Exp |
| `deepseek-ai/DeepSeek-V4-Pro` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | head product deepseek |
| `deepseek-ai/DeepSeek-V4-Pro` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Pro |
| `deepseek-ai/DeepSeek-V4-Pro` | https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | repeats signal deepseek-ai/DeepSeek-V4-Pro |
| `distilbert/distilbert-base-cased` | https://huggingface.co/distilbert/distilbert-base-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal distilbert/distilbert-base-cased |
| `distilbert/distilbert-base-multilingual-cased` | https://huggingface.co/distilbert/distilbert-base-multilingual-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal distilbert/distilbert-base-multilingual-cased |
| `distilbert/distilbert-base-uncased` | https://huggingface.co/distilbert/distilbert-base-uncased | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal distilbert/distilbert-base-uncased |
| `distilbert/distilbert-base-uncased` | https://huggingface.co/distilbert/distilbert-base-uncased | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal distilbert/distilbert-base-uncased |
| `distilbert/distilbert-base-uncased` | https://huggingface.co/distilbert/distilbert-base-uncased | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal distilbert/distilbert-base-uncased |
| `distilbert/distilroberta-base` | https://huggingface.co/distilbert/distilroberta-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal distilbert/distilroberta-base |
| `dmis-lab/biobert-base-cased-v1.2` | https://huggingface.co/dmis-lab/biobert-base-cased-v1.2 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal dmis-lab/biobert-base-cased-v1.2 |
| `dots-studio/dots.ocr` | https://huggingface.co/dots-studio/dots.ocr | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal dots-studio/dots.ocr |
| `dphn/dolphin-2.5-mixtral-8x7b` | https://huggingface.co/dphn/dolphin-2.5-mixtral-8x7b | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal dphn/dolphin-2.5-mixtral-8x7b |
| `dphn/dolphin-2.9.1-yi-1.5-34b` | https://huggingface.co/dphn/dolphin-2.9.1-yi-1.5-34b | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal dphn/dolphin-2.9.1-yi-1.5-34b |
| `dphn/dolphin-2.9.1-yi-1.5-34b` | https://huggingface.co/dphn/dolphin-2.9.1-yi-1.5-34b | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal dphn/dolphin-2.9.1-yi-1.5-34b |
| `emilyalsentzer/Bio_ClinicalBERT` | https://huggingface.co/emilyalsentzer/Bio_ClinicalBERT | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal emilyalsentzer/Bio_ClinicalBERT |
| `empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF` | https://huggingface.co/empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | repeats signal empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF |
| `facebook/esm2_t33_650M_UR50D` | https://huggingface.co/facebook/esm2_t33_650M_UR50D | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal facebook/esm2_t33_650M_UR50D |
| `facebook/opt-125m` | https://huggingface.co/facebook/opt-125m | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads` | repeats signal facebook/opt-125m |
| `FacebookAI/roberta-base` | https://huggingface.co/FacebookAI/roberta-base | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal FacebookAI/roberta-base |
| `FacebookAI/roberta-base` | https://huggingface.co/FacebookAI/roberta-base | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal FacebookAI/roberta-base |
| `FacebookAI/roberta-large` | https://huggingface.co/FacebookAI/roberta-large | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal FacebookAI/roberta-large |
| `FacebookAI/roberta-large` | https://huggingface.co/FacebookAI/roberta-large | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal FacebookAI/roberta-large |
| `FacebookAI/xlm-roberta-base` | https://huggingface.co/FacebookAI/xlm-roberta-base | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal FacebookAI/xlm-roberta-base |
| `FacebookAI/xlm-roberta-base` | https://huggingface.co/FacebookAI/xlm-roberta-base | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal FacebookAI/xlm-roberta-base |
| `FacebookAI/xlm-roberta-large` | https://huggingface.co/FacebookAI/xlm-roberta-large | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal FacebookAI/xlm-roberta-large |
| `farbodtavakkoli/OTel-2.0-LLM-31B-IT` | https://huggingface.co/farbodtavakkoli/OTel-2.0-LLM-31B-IT | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal farbodtavakkoli/OTel-2.0-LLM-31B-IT |
| `farbodtavakkoli/OTel-2.0-LLM-31B-IT` | https://huggingface.co/farbodtavakkoli/OTel-2.0-LLM-31B-IT | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal farbodtavakkoli/OTel-2.0-LLM-31B-IT |
| `google-bert/bert-base-cased` | https://huggingface.co/google-bert/bert-base-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google-bert/bert-base-cased |
| `google-bert/bert-base-chinese` | https://huggingface.co/google-bert/bert-base-chinese | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google-bert/bert-base-chinese |
| `google-bert/bert-base-german-cased` | https://huggingface.co/google-bert/bert-base-german-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google-bert/bert-base-german-cased |
| `google-bert/bert-base-multilingual-cased` | https://huggingface.co/google-bert/bert-base-multilingual-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google-bert/bert-base-multilingual-cased |
| `google-bert/bert-base-multilingual-uncased` | https://huggingface.co/google-bert/bert-base-multilingual-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google-bert/bert-base-multilingual-uncased |
| `google-bert/bert-base-uncased` | https://huggingface.co/google-bert/bert-base-uncased | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google-bert/bert-base-uncased |
| `google-bert/bert-base-uncased` | https://huggingface.co/google-bert/bert-base-uncased | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google-bert/bert-base-uncased |
| `google-bert/bert-base-uncased` | https://huggingface.co/google-bert/bert-base-uncased | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google-bert/bert-base-uncased |
| `google-bert/bert-large-uncased` | https://huggingface.co/google-bert/bert-large-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google-bert/bert-large-uncased |
| `google/gemma-2-2b-it` | https://huggingface.co/google/gemma-2-2b-it | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of gemma |
| `google/gemma-2-2b-it` | https://huggingface.co/google/gemma-2-2b-it | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal google/gemma-2-2b-it |
| `google/gemma-2b` | https://huggingface.co/google/gemma-2b | 2026-09-07 | `hf_textgen_likes` | release or SKU of gemma |
| `google/gemma-3-1b-it` | https://huggingface.co/google/gemma-3-1b-it | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl` | release or SKU of gemma |
| `google/gemma-3-1b-it` | https://huggingface.co/google/gemma-3-1b-it | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl` | repeats signal google/gemma-3-1b-it |
| `google/gemma-3-1b-it` | https://huggingface.co/google/gemma-3-1b-it | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl` | repeats signal google/gemma-3-1b-it |
| `google/gemma-3-270m` | https://huggingface.co/google/gemma-3-270m | 2026-09-07 | `hf_textgen_downloads` | release or SKU of gemma |
| `google/gemma-3-27b-it` | https://huggingface.co/google/gemma-3-27b-it | 2026-09-07 | `B_hf_conv_likes` | release or SKU of gemma |
| `google/gemma-3-4b-it` | https://huggingface.co/google/gemma-3-4b-it | 2026-09-07 | `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of gemma |
| `google/gemma-3-4b-it` | https://huggingface.co/google/gemma-3-4b-it | 2026-09-07 | `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal google/gemma-3-4b-it |
| `google/gemma-4-26B-A4B-it` | https://huggingface.co/google/gemma-4-26B-A4B-it | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product gemma |
| `google/gemma-4-26B-A4B-it` | https://huggingface.co/google/gemma-4-26B-A4B-it | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal google/gemma-4-26B-A4B-it |
| `google/gemma-4-26B-A4B-it` | https://huggingface.co/google/gemma-4-26B-A4B-it | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal google/gemma-4-26B-A4B-it |
| `google/gemma-4-31B-it` | https://huggingface.co/google/gemma-4-31B-it | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product gemma |
| `google/gemma-4-31B-it` | https://huggingface.co/google/gemma-4-31B-it | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal google/gemma-4-31B-it |
| `google/gemma-4-31B-it` | https://huggingface.co/google/gemma-4-31B-it | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal google/gemma-4-31B-it |
| `google/gemma-4-31B-it` | https://huggingface.co/google/gemma-4-31B-it | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal google/gemma-4-31B-it |
| `google/gemma-4-E4B-it` | https://huggingface.co/google/gemma-4-E4B-it | 2026-09-07 | `hf_all_downloads` | release or SKU of gemma |
| `google/gemma-7b` | https://huggingface.co/google/gemma-7b | 2026-09-07 | `hf_textgen_likes` | release or SKU of gemma |
| `google/gemma-7b-it` | https://huggingface.co/google/gemma-7b-it | 2026-09-07 | `hf_textgen_likes` | release or SKU of gemma |
| `google/muril-base-cased` | https://huggingface.co/google/muril-base-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal google/muril-base-cased |
| `HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive` | https://huggingface.co/HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive | 2026-09-07 | `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive |
| `HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF` | https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF | 2026-09-07 | `hf_all_trending`, `B_hf_conv_dl` | repeats signal HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF |
| `hfl/chinese-bert-wwm` | https://huggingface.co/hfl/chinese-bert-wwm | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal hfl/chinese-bert-wwm |
| `hfl/chinese-macbert-large` | https://huggingface.co/hfl/chinese-macbert-large | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal hfl/chinese-macbert-large |
| `HooshvareLab/bert-base-parsbert-uncased` | https://huggingface.co/HooshvareLab/bert-base-parsbert-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal HooshvareLab/bert-base-parsbert-uncased |
| `HuggingFaceH4/zephyr-7b-beta` | https://huggingface.co/HuggingFaceH4/zephyr-7b-beta | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | head product zephyr |
| `HuggingFaceH4/zephyr-7b-beta` | https://huggingface.co/HuggingFaceH4/zephyr-7b-beta | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal HuggingFaceH4/zephyr-7b-beta |
| `HuggingFaceTB/SmolLM2-135M-Instruct` | https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal HuggingFaceTB/SmolLM2-135M-Instruct |
| `HuggingFaceTB/SmolLM3-3B` | https://huggingface.co/HuggingFaceTB/SmolLM3-3B | 2026-09-07 | `hf_textgen_trending` | head product smollm |
| `huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF` | https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF | 2026-09-07 | `hf_all_trending`, `B_hf_conv_dl` | repeats signal huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF |
| `ibm-granite/granite-docling-258M` | https://huggingface.co/ibm-granite/granite-docling-258M | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal ibm-granite/granite-docling-258M |
| `ibm-granite/granite-guardian-3.2-5b` | https://huggingface.co/ibm-granite/granite-guardian-3.2-5b | 2026-09-07 | `hf_guard_search` | head product granite-guardian |
| `IFM/K2-Horizon-0.9B` | https://huggingface.co/IFM/K2-Horizon-0.9B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-0.9B |
| `IFM/K2-Horizon-375B-A23B` | https://huggingface.co/IFM/K2-Horizon-375B-A23B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-375B-A23B |
| `IFM/K2-Horizon-7B` | https://huggingface.co/IFM/K2-Horizon-7B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-7B |
| `IFM/K2-Horizon-MoVA-36B-A4B` | https://huggingface.co/IFM/K2-Horizon-MoVA-36B-A4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-MoVA-36B-A4B |
| `IFM/K2-Horizon-MoVA-36B-A4B-GGUF` | https://huggingface.co/IFM/K2-Horizon-MoVA-36B-A4B-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal IFM/K2-Horizon-MoVA-36B-A4B-GGUF |
| `inclusionAI/Ling-3.0-flash-Fin` | https://huggingface.co/inclusionAI/Ling-3.0-flash-Fin | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal inclusionAI/Ling-3.0-flash-Fin |
| `inclusionAI/Ling-3.0-tiny` | https://huggingface.co/inclusionAI/Ling-3.0-tiny | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal inclusionAI/Ling-3.0-tiny |
| `internlm/internlm2-base-20b` | https://huggingface.co/internlm/internlm2-base-20b | 2026-09-07 | `hf_base_search` | release or SKU of internlm |
| `internlm/internlm2-base-7b` | https://huggingface.co/internlm/internlm2-base-7b | 2026-09-07 | `hf_base_search` | release or SKU of internlm |
| `jackaduma/SecBERT` | https://huggingface.co/jackaduma/SecBERT | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal jackaduma/SecBERT |
| `Jackrong/Qwopus3.8-27B-Flash-GGUF` | https://huggingface.co/Jackrong/Qwopus3.8-27B-Flash-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal Jackrong/Qwopus3.8-27B-Flash-GGUF |
| `jhu-clsp/mmBERT-base` | https://huggingface.co/jhu-clsp/mmBERT-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal jhu-clsp/mmBERT-base |
| `jinaai/jina-embeddings-v2-base-code` | https://huggingface.co/jinaai/jina-embeddings-v2-base-code | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal jinaai/jina-embeddings-v2-base-code |
| `JonathanColetti/Qwen3.8-27B-Uncensored-GGUF` | https://huggingface.co/JonathanColetti/Qwen3.8-27B-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | repeats signal JonathanColetti/Qwen3.8-27B-Uncensored-GGUF |
| `JonathanColetti/Qwen3.8-27B-Uncensored-GGUF` | https://huggingface.co/JonathanColetti/Qwen3.8-27B-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | repeats signal JonathanColetti/Qwen3.8-27B-Uncensored-GGUF |
| `JonathanColetti/Qwen3.8-27B-Uncensored-GGUF` | https://huggingface.co/JonathanColetti/Qwen3.8-27B-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | repeats signal JonathanColetti/Qwen3.8-27B-Uncensored-GGUF |
| `law-ai/InLegalBERT` | https://huggingface.co/law-ai/InLegalBERT | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal law-ai/InLegalBERT |
| `LiquidAI/LFM2.5-2.6B-GGUF` | https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | distribution-format redistribution of the signal LiquidAI/LFM2.5-2.6B: same owner login, name is that name plus `-GGUF`, and the repo declares tag `gguf`. Folded onto the shorter name (the base-weights repo), which is the representative of the pair |
| `LiquidAI/LFM2.5-2.6B-GGUF` | https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | repeats signal LiquidAI/LFM2.5-2.6B-GGUF |
| `marin-community/marin-8b-base` | https://huggingface.co/marin-community/marin-8b-base | 2026-09-07 | `hf_base_search` | head product marin |
| `mattshumer/Reflection-Llama-3.1-70B` | https://huggingface.co/mattshumer/Reflection-Llama-3.1-70B | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal mattshumer/Reflection-Llama-3.1-70B |
| `meta-llama/Llama-2-13b-chat-hf` | https://huggingface.co/meta-llama/Llama-2-13b-chat-hf | 2026-09-07 | `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-2-70b-chat-hf` | https://huggingface.co/meta-llama/Llama-2-70b-chat-hf | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of llama |
| `meta-llama/Llama-2-70b-chat-hf` | https://huggingface.co/meta-llama/Llama-2-70b-chat-hf | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-2-70b-chat-hf |
| `meta-llama/Llama-2-7b` | https://huggingface.co/meta-llama/Llama-2-7b | 2026-09-07 | `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-2-7b-chat-hf` | https://huggingface.co/meta-llama/Llama-2-7b-chat-hf | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of llama |
| `meta-llama/Llama-2-7b-chat-hf` | https://huggingface.co/meta-llama/Llama-2-7b-chat-hf | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-2-7b-chat-hf |
| `meta-llama/Llama-2-7b-hf` | https://huggingface.co/meta-llama/Llama-2-7b-hf | 2026-09-07 | `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-3.1-70B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of llama |
| `meta-llama/Llama-3.1-8B` | https://huggingface.co/meta-llama/Llama-3.1-8B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | head product llama |
| `meta-llama/Llama-3.1-8B` | https://huggingface.co/meta-llama/Llama-3.1-8B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal meta-llama/Llama-3.1-8B |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product llama-instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.1-8B-Instruct |
| `meta-llama/Llama-3.2-11B-Vision-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-11B-Vision-Instruct | 2026-09-07 | `B_hf_conv_likes` | release or SKU of llama |
| `meta-llama/Llama-3.2-1B` | https://huggingface.co/meta-llama/Llama-3.2-1B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of llama |
| `meta-llama/Llama-3.2-1B` | https://huggingface.co/meta-llama/Llama-3.2-1B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal meta-llama/Llama-3.2-1B |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of llama |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.2-1B-Instruct |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.2-1B-Instruct |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.2-1B-Instruct |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.2-1B-Instruct |
| `meta-llama/Llama-3.2-1B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.2-1B-Instruct |
| `meta-llama/Llama-3.2-3B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | release or SKU of llama |
| `meta-llama/Llama-3.2-3B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.2-3B-Instruct |
| `meta-llama/Llama-3.2-3B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.2-3B-Instruct |
| `meta-llama/Llama-3.2-3B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.2-3B-Instruct |
| `meta-llama/Llama-3.2-3B-Instruct` | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.2-3B-Instruct |
| `meta-llama/Llama-3.3-70B-Instruct` | https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | release or SKU of llama |
| `meta-llama/Llama-3.3-70B-Instruct` | https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.3-70B-Instruct |
| `meta-llama/Llama-3.3-70B-Instruct` | https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Llama-3.3-70B-Instruct |
| `meta-llama/Llama-4-Scout-17B-16E-Instruct` | https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct | 2026-09-07 | `B_hf_conv_likes` | release or SKU of llama |
| `meta-llama/Llama-Guard-3-11B-Vision` | https://huggingface.co/meta-llama/Llama-Guard-3-11B-Vision | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Guard-3-1B` | https://huggingface.co/meta-llama/Llama-Guard-3-1B | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Guard-3-8B` | https://huggingface.co/meta-llama/Llama-Guard-3-8B | 2026-09-07 | `hf_guard_search` | head product llama-guard |
| `meta-llama/Llama-Guard-3-8B-INT8` | https://huggingface.co/meta-llama/Llama-Guard-3-8B-INT8 | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Guard-4-12B` | https://huggingface.co/meta-llama/Llama-Guard-4-12B | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Prompt-Guard-2-22M` | https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-22M | 2026-09-07 | `hf_guard_search` | release or SKU of llama |
| `meta-llama/Llama-Prompt-Guard-2-86M` | https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M | 2026-09-07 | `hf_guard_search` | head product llama-prompt-guard |
| `meta-llama/Meta-Llama-3-70B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-70B-Instruct | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal meta-llama/Meta-Llama-3-70B-Instruct |
| `meta-llama/Meta-Llama-3-8B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Meta-Llama-3-8B-Instruct |
| `meta-llama/Meta-Llama-3-8B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Meta-Llama-3-8B-Instruct |
| `meta-llama/Meta-Llama-3-8B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Meta-Llama-3-8B-Instruct |
| `meta-llama/Meta-Llama-3-8B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal meta-llama/Meta-Llama-3-8B-Instruct |
| `meta-llama/Prompt-Guard-86M` | https://huggingface.co/meta-llama/Prompt-Guard-86M | 2026-09-07 | `hf_all_downloads`, `hf_guard_search` | repeats signal meta-llama/Prompt-Guard-86M |
| `meta-models/Muse-Glimmer-30B` | https://huggingface.co/meta-models/Muse-Glimmer-30B | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | repeats signal meta-models/Muse-Glimmer-30B |
| `Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw` | https://huggingface.co/Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw |
| `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract` | https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract |
| `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext` | https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext |
| `microsoft/bitnet-b1.58-2B-4T` | https://huggingface.co/microsoft/bitnet-b1.58-2B-4T | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal microsoft/bitnet-b1.58-2B-4T |
| `microsoft/codebert-base-mlm` | https://huggingface.co/microsoft/codebert-base-mlm | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/codebert-base-mlm |
| `microsoft/deberta-base` | https://huggingface.co/microsoft/deberta-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/deberta-base |
| `microsoft/deberta-v3-base` | https://huggingface.co/microsoft/deberta-v3-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/deberta-v3-base |
| `microsoft/deberta-v3-large` | https://huggingface.co/microsoft/deberta-v3-large | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/deberta-v3-large |
| `microsoft/deberta-v3-small` | https://huggingface.co/microsoft/deberta-v3-small | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/deberta-v3-small |
| `microsoft/graphcodebert-base` | https://huggingface.co/microsoft/graphcodebert-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/graphcodebert-base |
| `microsoft/mdeberta-v3-base` | https://huggingface.co/microsoft/mdeberta-v3-base | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/mdeberta-v3-base |
| `microsoft/mdeberta-v3-base` | https://huggingface.co/microsoft/mdeberta-v3-base | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/mdeberta-v3-base |
| `microsoft/mpnet-base` | https://huggingface.co/microsoft/mpnet-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal microsoft/mpnet-base |
| `microsoft/phi-1_5` | https://huggingface.co/microsoft/phi-1_5 | 2026-09-07 | `hf_textgen_likes` | release or SKU of phi |
| `microsoft/phi-2` | https://huggingface.co/microsoft/phi-2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of phi |
| `microsoft/phi-2` | https://huggingface.co/microsoft/phi-2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal microsoft/phi-2 |
| `microsoft/Phi-3-mini-128k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-128k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | release or SKU of phi |
| `microsoft/Phi-3-mini-128k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-128k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal microsoft/Phi-3-mini-128k-instruct |
| `microsoft/Phi-3-mini-128k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-128k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal microsoft/Phi-3-mini-128k-instruct |
| `microsoft/Phi-3-mini-4k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-4k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | release or SKU of phi |
| `microsoft/Phi-3-mini-4k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-4k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal microsoft/Phi-3-mini-4k-instruct |
| `microsoft/Phi-3-mini-4k-instruct` | https://huggingface.co/microsoft/Phi-3-mini-4k-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal microsoft/Phi-3-mini-4k-instruct |
| `microsoft/Phi-3.5-mini-instruct` | https://huggingface.co/microsoft/Phi-3.5-mini-instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of phi |
| `microsoft/Phi-3.5-vision-instruct` | https://huggingface.co/microsoft/Phi-3.5-vision-instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of phi |
| `microsoft/phi-4` | https://huggingface.co/microsoft/phi-4 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | head product phi |
| `microsoft/phi-4` | https://huggingface.co/microsoft/phi-4 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal microsoft/phi-4 |
| `microsoft/Phi-4-mini-instruct` | https://huggingface.co/microsoft/Phi-4-mini-instruct | 2026-09-07 | `hf_instruct_search` | head product phi-instruct |
| `microsoft/Phi-4-multimodal-instruct` | https://huggingface.co/microsoft/Phi-4-multimodal-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | release or SKU of phi |
| `microsoft/Phi-4-multimodal-instruct` | https://huggingface.co/microsoft/Phi-4-multimodal-instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | repeats signal microsoft/Phi-4-multimodal-instruct |
| `MiniMaxAI/MiniMax-H3` | https://huggingface.co/MiniMaxAI/MiniMax-H3 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-H3` | https://huggingface.co/MiniMaxAI/MiniMax-H3 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal MiniMaxAI/MiniMax-H3 |
| `MiniMaxAI/MiniMax-M2` | https://huggingface.co/MiniMaxAI/MiniMax-M2 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-M2` | https://huggingface.co/MiniMaxAI/MiniMax-M2 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal MiniMaxAI/MiniMax-M2 |
| `MiniMaxAI/MiniMax-M2.1` | https://huggingface.co/MiniMaxAI/MiniMax-M2.1 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-M2.1` | https://huggingface.co/MiniMaxAI/MiniMax-M2.1 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal MiniMaxAI/MiniMax-M2.1 |
| `MiniMaxAI/MiniMax-M2.5` | https://huggingface.co/MiniMaxAI/MiniMax-M2.5 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-M2.5` | https://huggingface.co/MiniMaxAI/MiniMax-M2.5 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal MiniMaxAI/MiniMax-M2.5 |
| `MiniMaxAI/MiniMax-M2.7` | https://huggingface.co/MiniMaxAI/MiniMax-M2.7 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | release or SKU of minimax |
| `MiniMaxAI/MiniMax-M2.7` | https://huggingface.co/MiniMaxAI/MiniMax-M2.7 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal MiniMaxAI/MiniMax-M2.7 |
| `MiniMaxAI/MiniMax-M3` | https://huggingface.co/MiniMaxAI/MiniMax-M3 | 2026-09-07 | `B_hf_conv_likes` | head product minimax |
| `MiniMaxAI/MiniMax-Music3` | https://huggingface.co/MiniMaxAI/MiniMax-Music3 | 2026-09-07 | `hf_all_trending` | release or SKU of minimax |
| `mistralai/Mistral-7B-Instruct-v0.1` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of mistral-7b-instruct |
| `mistralai/Mistral-7B-Instruct-v0.1` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal mistralai/Mistral-7B-Instruct-v0.1 |
| `mistralai/Mistral-7B-Instruct-v0.2` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | head product mistral-7b-instruct |
| `mistralai/Mistral-7B-Instruct-v0.2` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal mistralai/Mistral-7B-Instruct-v0.2 |
| `mistralai/Mistral-7B-Instruct-v0.2` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal mistralai/Mistral-7B-Instruct-v0.2 |
| `mistralai/Mistral-7B-Instruct-v0.2` | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_likes` | repeats signal mistralai/Mistral-7B-Instruct-v0.2 |
| `moonshotai/Kimi-K2-Base` | https://huggingface.co/moonshotai/Kimi-K2-Base | 2026-09-07 | `hf_base_search` | release or SKU of kimi |
| `moonshotai/Kimi-K2-Instruct` | https://huggingface.co/moonshotai/Kimi-K2-Instruct | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of kimi |
| `moonshotai/Kimi-K2-Instruct` | https://huggingface.co/moonshotai/Kimi-K2-Instruct | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal moonshotai/Kimi-K2-Instruct |
| `moonshotai/Kimi-K2-Thinking` | https://huggingface.co/moonshotai/Kimi-K2-Thinking | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of kimi |
| `moonshotai/Kimi-K2-Thinking` | https://huggingface.co/moonshotai/Kimi-K2-Thinking | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal moonshotai/Kimi-K2-Thinking |
| `moonshotai/Kimi-K2.5` | https://huggingface.co/moonshotai/Kimi-K2.5 | 2026-09-07 | `B_hf_conv_likes` | release or SKU of kimi |
| `moonshotai/Kimi-K2.6` | https://huggingface.co/moonshotai/Kimi-K2.6 | 2026-09-07 | `B_hf_conv_likes` | head product kimi |
| `moonshotai/Kimi-K2.7-Code` | https://huggingface.co/moonshotai/Kimi-K2.7-Code | 2026-09-07 | `B_hf_conv_likes` | release or SKU of kimi |
| `moonshotai/Kimi-K3` | https://huggingface.co/moonshotai/Kimi-K3 | 2026-09-07 | `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product kimi |
| `moonshotai/Kimi-K3` | https://huggingface.co/moonshotai/Kimi-K3 | 2026-09-07 | `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal moonshotai/Kimi-K3 |
| `moonshotai/Kimi-K3` | https://huggingface.co/moonshotai/Kimi-K3 | 2026-09-07 | `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal moonshotai/Kimi-K3 |
| `moonshotai/Kimi-Linear-48B-A3B-Instruct` | https://huggingface.co/moonshotai/Kimi-Linear-48B-A3B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of kimi |
| `Nanbeige/Nanbeige4.2-3B` | https://huggingface.co/Nanbeige/Nanbeige4.2-3B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal Nanbeige/Nanbeige4.2-3B |
| `neuralmind/bert-base-portuguese-cased` | https://huggingface.co/neuralmind/bert-base-portuguese-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal neuralmind/bert-base-portuguese-cased |
| `neuralmind/bert-large-portuguese-cased` | https://huggingface.co/neuralmind/bert-large-portuguese-cased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal neuralmind/bert-large-portuguese-cased |
| `nlpaueb/legal-bert-base-uncased` | https://huggingface.co/nlpaueb/legal-bert-base-uncased | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal nlpaueb/legal-bert-base-uncased |
| `nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0` | https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0 | 2026-09-07 | `hf_safety_search` | head product aegis-guard |
| `nvidia/DeepSeek-V4-Flash-0731-NVFP4` | https://huggingface.co/nvidia/DeepSeek-V4-Flash-0731-NVFP4 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal nvidia/DeepSeek-V4-Flash-0731-NVFP4 |
| `nvidia/Gemma-4-26B-A4B-NVFP4` | https://huggingface.co/nvidia/Gemma-4-26B-A4B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal nvidia/Gemma-4-26B-A4B-NVFP4 |
| `nvidia/Gemma-4-31B-IT-NVFP4` | https://huggingface.co/nvidia/Gemma-4-31B-IT-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal nvidia/Gemma-4-31B-IT-NVFP4 |
| `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF` | https://huggingface.co/nvidia/Llama-3.1-Nemotron-70B-Instruct-HF | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal nvidia/Llama-3.1-Nemotron-70B-Instruct-HF |
| `nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3` | https://huggingface.co/nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3 | 2026-09-07 | `hf_guard_search`, `hf_safety_search` | repeats signal nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3 |
| `nvidia/Nemotron-3-Content-Safety` | https://huggingface.co/nvidia/Nemotron-3-Content-Safety | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron |
| `nvidia/Nemotron-3.5-Content-Safety` | https://huggingface.co/nvidia/Nemotron-3.5-Content-Safety | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron |
| `nvidia/Nemotron-Content-Safety-Reasoning-4B` | https://huggingface.co/nvidia/Nemotron-Content-Safety-Reasoning-4B | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron |
| `nvidia/Nemotron-H-56B-Base-8K` | https://huggingface.co/nvidia/Nemotron-H-56B-Base-8K | 2026-09-07 | `hf_base_search` | release or SKU of nemotron |
| `nvidia/Nemotron-H-8B-Base-8K` | https://huggingface.co/nvidia/Nemotron-H-8B-Base-8K | 2026-09-07 | `hf_base_search` | release or SKU of nemotron |
| `nvidia/Nemotron-Labs-Diffusion-8B-Base` | https://huggingface.co/nvidia/Nemotron-Labs-Diffusion-8B-Base | 2026-09-07 | `hf_base_search` | release or SKU of nemotron |
| `nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16 | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16 |
| `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16 | 2026-09-07 | `hf_textgen_downloads` | head product nemotron |
| `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | repeats signal nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 |
| `nvidia/Qwen3.6-35B-A3B-NVFP4` | https://huggingface.co/nvidia/Qwen3.6-35B-A3B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal nvidia/Qwen3.6-35B-A3B-NVFP4 |
| `nvidia/Qwen3.6-35B-A3B-NVFP4` | https://huggingface.co/nvidia/Qwen3.6-35B-A3B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal nvidia/Qwen3.6-35B-A3B-NVFP4 |
| `OBLITERATUS/Qwen3.8-27B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Qwen3.8-27B-OBLITERATED | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | repeats signal OBLITERATUS/Qwen3.8-27B-OBLITERATED |
| `OBLITERATUS/Qwen3.8-27B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Qwen3.8-27B-OBLITERATED | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | repeats signal OBLITERATUS/Qwen3.8-27B-OBLITERATED |
| `OBLITERATUS/Qwen3.8-27B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Qwen3.8-27B-OBLITERATED | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | repeats signal OBLITERATUS/Qwen3.8-27B-OBLITERATED |
| `openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal openai-community/gpt2 |
| `openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal openai-community/gpt2 |
| `openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal openai-community/gpt2 |
| `openai-community/gpt2` | https://huggingface.co/openai-community/gpt2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `hf_all_trending` | repeats signal openai-community/gpt2 |
| `openai/clip-vit-base-patch32` | https://huggingface.co/openai/clip-vit-base-patch32 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal openai/clip-vit-base-patch32 |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product gpt-oss |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-120b |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-120b |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-120b |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-120b |
| `openai/gpt-oss-120b` | https://huggingface.co/openai/gpt-oss-120b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-120b |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product gpt-oss |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-20b |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-20b |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-20b |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-20b |
| `openai/gpt-oss-20b` | https://huggingface.co/openai/gpt-oss-20b | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal openai/gpt-oss-20b |
| `openbmb/MiniCPM5-1B` | https://huggingface.co/openbmb/MiniCPM5-1B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | head product minicpm |
| `openbmb/MiniCPM5-1B` | https://huggingface.co/openbmb/MiniCPM5-1B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal openbmb/MiniCPM5-1B |
| `orcarouter/GLM-5.3-Flash-Uncensored-FP8` | https://huggingface.co/orcarouter/GLM-5.3-Flash-Uncensored-FP8 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal orcarouter/GLM-5.3-Flash-Uncensored-FP8 |
| `orcarouter/Qwen3.8-27B-Uncensored-FP8` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored-FP8 | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | repeats signal orcarouter/Qwen3.8-27B-Uncensored-FP8 |
| `orcarouter/Qwen3.8-27B-Uncensored-MLX` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored-MLX | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | repeats signal orcarouter/Qwen3.8-27B-Uncensored-MLX |
| `ornith-ai/Ornith-1.0-35B` | https://huggingface.co/ornith-ai/Ornith-1.0-35B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.0-35B |
| `ornith-ai/Ornith-1.0-35B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.0-35B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.0-35B-GGUF |
| `ornith-ai/Ornith-1.0-9B` | https://huggingface.co/ornith-ai/Ornith-1.0-9B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.0-9B |
| `ornith-ai/Ornith-1.0-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.0-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.0-9B-GGUF |
| `ornith-ai/Ornith-1.0-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.0-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.0-9B-GGUF |
| `ornith-ai/Ornith-1.5-35B-A3B` | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal ornith-ai/Ornith-1.5-35B-A3B |
| `ornith-ai/Ornith-1.5-35B-A3B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.5-35B-A3B-GGUF |
| `ornith-ai/Ornith-1.5-35B-A3B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.5-35B-A3B-GGUF |
| `ornith-ai/Ornith-1.5-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.5-9B-GGUF |
| `ornith-ai/Ornith-1.5-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.5-9B-GGUF |
| `ornith-ai/Ornith-1.5-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | repeats signal ornith-ai/Ornith-1.5-9B-GGUF |
| `pipecat-ai/phonellm-alpha-1` | https://huggingface.co/pipecat-ai/phonellm-alpha-1 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal pipecat-ai/phonellm-alpha-1 |
| `prism-ml/Ternary-Bonsai-27B-gguf` | https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | repeats signal prism-ml/Ternary-Bonsai-27B-gguf |
| `prism-ml/Ternary-Bonsai-27B-gguf` | https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | repeats signal prism-ml/Ternary-Bonsai-27B-gguf |
| `pyannote/speaker-diarization-3.1` | https://huggingface.co/pyannote/speaker-diarization-3.1 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal pyannote/speaker-diarization-3.1 |
| `pyannote/speaker-diarization-community-1` | https://huggingface.co/pyannote/speaker-diarization-community-1 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal pyannote/speaker-diarization-community-1 |
| `QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ` | https://huggingface.co/QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ |
| `Qwen/Qwen-72B` | https://huggingface.co/Qwen/Qwen-72B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen-Drive-1.0-4B` | https://huggingface.co/Qwen/Qwen-Drive-1.0-4B | 2026-09-07 | `hf_all_trending` | release or SKU of qwen |
| `Qwen/Qwen2-0.5B-Instruct` | https://huggingface.co/Qwen/Qwen2-0.5B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2-1.5B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2-7B-Instruct` | https://huggingface.co/Qwen/Qwen2-7B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2-VL-2B-Instruct` | https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2-VL-7B-Instruct` | https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct | 2026-09-07 | `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen2-VL-7B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct-AWQ | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-0.5B` | https://huggingface.co/Qwen/Qwen2.5-0.5B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-0.5B` | https://huggingface.co/Qwen/Qwen2.5-0.5B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-0.5B |
| `Qwen/Qwen2.5-0.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-0.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-0.5B-Instruct |
| `Qwen/Qwen2.5-0.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-0.5B-Instruct |
| `Qwen/Qwen2.5-0.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-0.5B-Instruct |
| `Qwen/Qwen2.5-0.5B-Instruct-GGUF` | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-1.5B` | https://huggingface.co/Qwen/Qwen2.5-1.5B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen2.5-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-1.5B-Instruct |
| `Qwen/Qwen2.5-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-1.5B-Instruct |
| `Qwen/Qwen2.5-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-1.5B-Instruct |
| `Qwen/Qwen2.5-1.5B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-1.5B-Instruct-GGUF` | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | head product qwen-instruct |
| `Qwen/Qwen2.5-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-14B-Instruct |
| `Qwen/Qwen2.5-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-14B-Instruct |
| `Qwen/Qwen2.5-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-14B-Instruct-AWQ |
| `Qwen/Qwen2.5-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-14B-Instruct-AWQ |
| `Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4` | https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-32B-Instruct |
| `Qwen/Qwen2.5-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-32B-Instruct |
| `Qwen/Qwen2.5-32B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-32B-Instruct-GPTQ-Int4` | https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GPTQ-Int4 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-3B-Instruct |
| `Qwen/Qwen2.5-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-3B-Instruct |
| `Qwen/Qwen2.5-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-3B-Instruct |
| `Qwen/Qwen2.5-3B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-3B-Instruct-GGUF` | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-72B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-72B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-72B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-72B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-7B-Instruct |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-7B-Instruct |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-7B-Instruct |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-7B-Instruct |
| `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-7B-Instruct |
| `Qwen/Qwen2.5-7B-Instruct-1M` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-1M | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-7B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-7B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-7B-Instruct-AWQ |
| `Qwen/Qwen2.5-7B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-7B-Instruct-AWQ |
| `Qwen/Qwen2.5-Coder-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-Coder-14B-Instruct |
| `Qwen/Qwen2.5-Coder-14B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-Coder-14B-Instruct |
| `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-Coder-14B-Instruct-AWQ |
| `Qwen/Qwen2.5-Coder-14B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-Coder-14B-Instruct-AWQ |
| `Qwen/Qwen2.5-Coder-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product qwen-coder |
| `Qwen/Qwen2.5-Coder-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-Coder-32B-Instruct |
| `Qwen/Qwen2.5-Coder-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-Coder-32B-Instruct |
| `Qwen/Qwen2.5-Coder-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-Coder-32B-Instruct |
| `Qwen/Qwen2.5-Coder-32B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_instruct_search`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-Coder-32B-Instruct |
| `Qwen/Qwen2.5-Coder-32B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-32B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen2.5-Coder-32B-Instruct-AWQ |
| `Qwen/Qwen2.5-Coder-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | head product qwen-coder |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-Coder-7B-Instruct |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen2.5-Coder-7B-Instruct |
| `Qwen/Qwen2.5-Coder-7B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Coder-7B-Instruct-GPTQ-Int4` | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GPTQ-Int4 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-Math-1.5B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-Math-1.5B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen2.5-VL-32B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-VL-32B-Instruct-AWQ | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-VL-3B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen2.5-VL-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen2.5-VL-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-VL-7B-Instruct |
| `Qwen/Qwen2.5-VL-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen2.5-VL-7B-Instruct |
| `Qwen/Qwen2.5-VL-7B-Instruct-AWQ` | https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct-AWQ | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-0.6B |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-0.6B |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-0.6B |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-0.6B |
| `Qwen/Qwen3-0.6B` | https://huggingface.co/Qwen/Qwen3-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-0.6B |
| `Qwen/Qwen3-0.6B-Base` | https://huggingface.co/Qwen/Qwen3-0.6B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-1.7B` | https://huggingface.co/Qwen/Qwen3-1.7B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-1.7B` | https://huggingface.co/Qwen/Qwen3-1.7B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-1.7B |
| `Qwen/Qwen3-1.7B-Base` | https://huggingface.co/Qwen/Qwen3-1.7B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-1.7B-Base` | https://huggingface.co/Qwen/Qwen3-1.7B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-1.7B-Base |
| `Qwen/Qwen3-1.7B-Base` | https://huggingface.co/Qwen/Qwen3-1.7B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-1.7B-Base |
| `Qwen/Qwen3-14B` | https://huggingface.co/Qwen/Qwen3-14B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-14B` | https://huggingface.co/Qwen/Qwen3-14B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-14B |
| `Qwen/Qwen3-14B-AWQ` | https://huggingface.co/Qwen/Qwen3-14B-AWQ | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-14B-AWQ` | https://huggingface.co/Qwen/Qwen3-14B-AWQ | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-14B-AWQ |
| `Qwen/Qwen3-14B-Base` | https://huggingface.co/Qwen/Qwen3-14B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-235B-A22B` | https://huggingface.co/Qwen/Qwen3-235B-A22B | 2026-09-07 | `hf_textgen_likes` | head product qwen |
| `Qwen/Qwen3-235B-A22B-Instruct-2507-FP8` | https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-30B-A3B` | https://huggingface.co/Qwen/Qwen3-30B-A3B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-30B-A3B` | https://huggingface.co/Qwen/Qwen3-30B-A3B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-30B-A3B |
| `Qwen/Qwen3-30B-A3B-Base` | https://huggingface.co/Qwen/Qwen3-30B-A3B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-30B-A3B-Instruct-2507` | https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-30B-A3B-Instruct-2507` | https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen3-30B-A3B-Instruct-2507 |
| `Qwen/Qwen3-30B-A3B-Instruct-2507-FP8` | https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507-FP8 | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-32B` | https://huggingface.co/Qwen/Qwen3-32B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-32B` | https://huggingface.co/Qwen/Qwen3-32B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-32B |
| `Qwen/Qwen3-32B` | https://huggingface.co/Qwen/Qwen3-32B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-32B |
| `Qwen/Qwen3-4B` | https://huggingface.co/Qwen/Qwen3-4B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-4B` | https://huggingface.co/Qwen/Qwen3-4B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-4B |
| `Qwen/Qwen3-4B` | https://huggingface.co/Qwen/Qwen3-4B | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-4B |
| `Qwen/Qwen3-4B-Base` | https://huggingface.co/Qwen/Qwen3-4B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-4B-Base` | https://huggingface.co/Qwen/Qwen3-4B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-4B-Base |
| `Qwen/Qwen3-4B-Base` | https://huggingface.co/Qwen/Qwen3-4B-Base | 2026-09-07 | `hf_textgen_downloads`, `hf_base_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-4B-Base |
| `Qwen/Qwen3-4B-Instruct-2507` | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-4B-Instruct-2507` | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-4B-Instruct-2507 |
| `Qwen/Qwen3-4B-Instruct-2507` | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-4B-Instruct-2507 |
| `Qwen/Qwen3-4B-Instruct-2507-FP8` | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507-FP8 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-4B-Instruct-2507-FP8` | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507-FP8 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen3-4B-Instruct-2507-FP8 |
| `Qwen/Qwen3-8B` | https://huggingface.co/Qwen/Qwen3-8B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen3-8B` | https://huggingface.co/Qwen/Qwen3-8B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-8B |
| `Qwen/Qwen3-8B` | https://huggingface.co/Qwen/Qwen3-8B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-8B |
| `Qwen/Qwen3-8B` | https://huggingface.co/Qwen/Qwen3-8B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-8B |
| `Qwen/Qwen3-8B` | https://huggingface.co/Qwen/Qwen3-8B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-8B |
| `Qwen/Qwen3-8B-AWQ` | https://huggingface.co/Qwen/Qwen3-8B-AWQ | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-8B-AWQ` | https://huggingface.co/Qwen/Qwen3-8B-AWQ | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-8B-AWQ |
| `Qwen/Qwen3-8B-Base` | https://huggingface.co/Qwen/Qwen3-8B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | head product qwen-coder |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct | 2026-09-07 | `hf_textgen_likes`, `hf_instruct_search` | repeats signal Qwen/Qwen3-Coder-30B-A3B-Instruct |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` | https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | repeats signal Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8 |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct` | https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct` | https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-Coder-480B-A35B-Instruct |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8` | https://huggingface.co/Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8 | 2026-09-07 | `hf_instruct_search` | head product qwen-coder |
| `Qwen/Qwen3-Coder-Next` | https://huggingface.co/Qwen/Qwen3-Coder-Next | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen3-Coder-Next` | https://huggingface.co/Qwen/Qwen3-Coder-Next | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3-Coder-Next |
| `Qwen/Qwen3-Coder-Next-FP8` | https://huggingface.co/Qwen/Qwen3-Coder-Next-FP8 | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-Coder-Next-FP8` | https://huggingface.co/Qwen/Qwen3-Coder-Next-FP8 | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-Coder-Next-FP8 |
| `Qwen/Qwen3-Embedding-0.6B` | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-Embedding-0.6B` | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads` | repeats signal Qwen/Qwen3-Embedding-0.6B |
| `Qwen/Qwen3-Embedding-0.6B` | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_all_downloads` | repeats signal Qwen/Qwen3-Embedding-0.6B |
| `Qwen/Qwen3-Embedding-4B` | https://huggingface.co/Qwen/Qwen3-Embedding-4B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-Embedding-8B` | https://huggingface.co/Qwen/Qwen3-Embedding-8B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-Next-80B-A3B-Instruct` | https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen |
| `Qwen/Qwen3-Reranker-0.6B` | https://huggingface.co/Qwen/Qwen3-Reranker-0.6B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-Reranker-4B` | https://huggingface.co/Qwen/Qwen3-Reranker-4B | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen |
| `Qwen/Qwen3-VL-2B-Instruct` | https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-VL-4B-Instruct` | https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-VL-8B-Instruct` | https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3-VL-8B-Instruct` | https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3-VL-8B-Instruct |
| `Qwen/Qwen3-VL-8B-Instruct-FP8` | https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-FP8 | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3.5-0.8B` | https://huggingface.co/Qwen/Qwen3.5-0.8B | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3.5-122B-A10B-FP8` | https://huggingface.co/Qwen/Qwen3.5-122B-A10B-FP8 | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3.5-27B` | https://huggingface.co/Qwen/Qwen3.5-27B | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3.5-2B` | https://huggingface.co/Qwen/Qwen3.5-2B | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3.5-35B-A3B` | https://huggingface.co/Qwen/Qwen3.5-35B-A3B | 2026-09-07 | `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen3.5-35B-A3B` | https://huggingface.co/Qwen/Qwen3.5-35B-A3B | 2026-09-07 | `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.5-35B-A3B |
| `Qwen/Qwen3.5-397B-A17B` | https://huggingface.co/Qwen/Qwen3.5-397B-A17B | 2026-09-07 | `B_hf_conv_likes` | head product qwen |
| `Qwen/Qwen3.5-4B` | https://huggingface.co/Qwen/Qwen3.5-4B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3.5-4B` | https://huggingface.co/Qwen/Qwen3.5-4B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3.5-4B |
| `Qwen/Qwen3.5-9B` | https://huggingface.co/Qwen/Qwen3.5-9B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen3.5-9B` | https://huggingface.co/Qwen/Qwen3.5-9B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.5-9B |
| `Qwen/Qwen3.5-9B` | https://huggingface.co/Qwen/Qwen3.5-9B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.5-9B |
| `Qwen/Qwen3.6-27B` | https://huggingface.co/Qwen/Qwen3.6-27B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product qwen |
| `Qwen/Qwen3.6-27B` | https://huggingface.co/Qwen/Qwen3.6-27B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.6-27B |
| `Qwen/Qwen3.6-27B` | https://huggingface.co/Qwen/Qwen3.6-27B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.6-27B |
| `Qwen/Qwen3.6-27B-FP8` | https://huggingface.co/Qwen/Qwen3.6-27B-FP8 | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3.6-27B-FP8` | https://huggingface.co/Qwen/Qwen3.6-27B-FP8 | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3.6-27B-FP8 |
| `Qwen/Qwen3.6-35B-A3B` | https://huggingface.co/Qwen/Qwen3.6-35B-A3B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product qwen |
| `Qwen/Qwen3.6-35B-A3B` | https://huggingface.co/Qwen/Qwen3.6-35B-A3B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.6-35B-A3B |
| `Qwen/Qwen3.6-35B-A3B` | https://huggingface.co/Qwen/Qwen3.6-35B-A3B | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.6-35B-A3B |
| `Qwen/Qwen3.6-35B-A3B-FP8` | https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8 | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3.6-35B-A3B-FP8` | https://huggingface.co/Qwen/Qwen3.6-35B-A3B-FP8 | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3.6-35B-A3B-FP8 |
| `Qwen/Qwen3.8-2.4T-A95B` | https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | release or SKU of qwen |
| `Qwen/Qwen3.8-2.4T-A95B` | https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending` | repeats signal Qwen/Qwen3.8-2.4T-A95B |
| `Qwen/Qwen3.8-27B` | https://huggingface.co/Qwen/Qwen3.8-27B | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen3.8-27B` | https://huggingface.co/Qwen/Qwen3.8-27B | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.8-27B |
| `Qwen/Qwen3.8-27B` | https://huggingface.co/Qwen/Qwen3.8-27B | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.8-27B |
| `Qwen/Qwen3.8-27B` | https://huggingface.co/Qwen/Qwen3.8-27B | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.8-27B |
| `Qwen/Qwen3.8-27B-FP8` | https://huggingface.co/Qwen/Qwen3.8-27B-FP8 | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | release or SKU of qwen |
| `Qwen/Qwen3.8-27B-FP8` | https://huggingface.co/Qwen/Qwen3.8-27B-FP8 | 2026-09-07 | `hf_all_downloads`, `B_hf_conv_dl` | repeats signal Qwen/Qwen3.8-27B-FP8 |
| `Qwen/Qwen3.8-Flash-Next` | https://huggingface.co/Qwen/Qwen3.8-Flash-Next | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | release or SKU of qwen |
| `Qwen/Qwen3.8-Flash-Next` | https://huggingface.co/Qwen/Qwen3.8-Flash-Next | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | repeats signal Qwen/Qwen3.8-Flash-Next |
| `Qwen/QwQ-32B` | https://huggingface.co/Qwen/QwQ-32B | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal Qwen/QwQ-32B |
| `Qwen/QwQ-32B-Preview` | https://huggingface.co/Qwen/QwQ-32B-Preview | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal Qwen/QwQ-32B-Preview |
| `sbintuitions/modernbert-ja-130m` | https://huggingface.co/sbintuitions/modernbert-ja-130m | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal sbintuitions/modernbert-ja-130m |
| `sentence-transformers/all-MiniLM-L6-v2` | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | repeats signal sentence-transformers/all-MiniLM-L6-v2 |
| `sentence-transformers/all-mpnet-base-v2` | https://huggingface.co/sentence-transformers/all-mpnet-base-v2 | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal sentence-transformers/all-mpnet-base-v2 |
| `sentence-transformers/all-mpnet-base-v2` | https://huggingface.co/sentence-transformers/all-mpnet-base-v2 | 2026-09-07 | `hf_all_downloads`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal sentence-transformers/all-mpnet-base-v2 |
| `sentence-transformers/all-roberta-large-v1` | https://huggingface.co/sentence-transformers/all-roberta-large-v1 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal sentence-transformers/all-roberta-large-v1 |
| `sentence-transformers/multi-qa-mpnet-base-dot-v1` | https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-dot-v1 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal sentence-transformers/multi-qa-mpnet-base-dot-v1 |
| `seyonec/ChemBERTa-zinc-base-v1` | https://huggingface.co/seyonec/ChemBERTa-zinc-base-v1 | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal seyonec/ChemBERTa-zinc-base-v1 |
| `shibing624/macbert4csc-base-chinese` | https://huggingface.co/shibing624/macbert4csc-base-chinese | 2026-09-07 | `hf_base_search`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal shibing624/macbert4csc-base-chinese |
| `shibing624/macbert4csc-base-chinese` | https://huggingface.co/shibing624/macbert4csc-base-chinese | 2026-09-07 | `hf_base_search`, `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal shibing624/macbert4csc-base-chinese |
| `tencent/Hy4-preview` | https://huggingface.co/tencent/Hy4-preview | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal tencent/Hy4-preview |
| `thinkingmachines/Inkling` | https://huggingface.co/thinkingmachines/Inkling | 2026-09-07 | `B_hf_conv_likes` | head product inkling |
| `tiiuae/falcon-180B` | https://huggingface.co/tiiuae/falcon-180B | 2026-09-07 | `hf_textgen_likes` | release or SKU of falcon |
| `tiiuae/falcon-40b` | https://huggingface.co/tiiuae/falcon-40b | 2026-09-07 | `hf_textgen_likes` | release or SKU of falcon |
| `tiiuae/falcon-40b-instruct` | https://huggingface.co/tiiuae/falcon-40b-instruct | 2026-09-07 | `hf_textgen_likes` | release or SKU of falcon |
| `tiiuae/Falcon-H1-0.5B-Base` | https://huggingface.co/tiiuae/Falcon-H1-0.5B-Base | 2026-09-07 | `hf_base_search` | release or SKU of falcon |
| `tiiuae/Falcon-H1-1.5B-Base` | https://huggingface.co/tiiuae/Falcon-H1-1.5B-Base | 2026-09-07 | `hf_base_search` | release or SKU of falcon |
| `tiiuae/Falcon3-10B-Base` | https://huggingface.co/tiiuae/Falcon3-10B-Base | 2026-09-07 | `hf_base_search` | head product falcon |
| `tiiuae/Falcon3-1B-Base` | https://huggingface.co/tiiuae/Falcon3-1B-Base | 2026-09-07 | `hf_base_search` | release or SKU of falcon |
| `tiiuae/Falcon3-7B-Base` | https://huggingface.co/tiiuae/Falcon3-7B-Base | 2026-09-07 | `hf_base_search` | release or SKU of falcon |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | head product tinyllama-chat |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal TinyLlama/TinyLlama-1.1B-Chat-v1.0 |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal TinyLlama/TinyLlama-1.1B-Chat-v1.0 |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal TinyLlama/TinyLlama-1.1B-Chat-v1.0 |
| `tohoku-nlp/bert-base-japanese-whole-word-masking` | https://huggingface.co/tohoku-nlp/bert-base-japanese-whole-word-masking | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal tohoku-nlp/bert-base-japanese-whole-word-masking |
| `trl-internal-testing/tiny-Qwen2ForCausalLM-2.5` | https://huggingface.co/trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 |
| `trl-internal-testing/tiny-Qwen2ForCausalLM-2.5` | https://huggingface.co/trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | repeats signal trl-internal-testing/tiny-Qwen2ForCausalLM-2.5 |
| `trl-internal-testing/tiny-Qwen3ForCausalLM` | https://huggingface.co/trl-internal-testing/tiny-Qwen3ForCausalLM | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | repeats signal trl-internal-testing/tiny-Qwen3ForCausalLM |
| `unsloth/GLM-5.3-Flash-GGUF` | https://huggingface.co/unsloth/GLM-5.3-Flash-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal unsloth/GLM-5.3-Flash-GGUF |
| `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` | https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF |
| `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` | https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF |
| `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` | https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF |
| `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` | https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | repeats signal unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF |
| `unsloth/Qwen3.8-27B-GGUF` | https://huggingface.co/unsloth/Qwen3.8-27B-GGUF | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal unsloth/Qwen3.8-27B-GGUF |
| `unsloth/Qwen3.8-27B-GGUF` | https://huggingface.co/unsloth/Qwen3.8-27B-GGUF | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal unsloth/Qwen3.8-27B-GGUF |
| `unsloth/Qwen3.8-27B-GGUF` | https://huggingface.co/unsloth/Qwen3.8-27B-GGUF | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal unsloth/Qwen3.8-27B-GGUF |
| `vikhyatk/moondream2` | https://huggingface.co/vikhyatk/moondream2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes` | repeats signal vikhyatk/moondream2 |
| `vinai/phobert-base` | https://huggingface.co/vinai/phobert-base | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal vinai/phobert-base |
| `XHToken/Spark-X2.5-1.7B` | https://huggingface.co/XHToken/Spark-X2.5-1.7B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal XHToken/Spark-X2.5-1.7B |
| `XHToken/Spark-X2.5-4B` | https://huggingface.co/XHToken/Spark-X2.5-4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal XHToken/Spark-X2.5-4B |
| `XHToken/Spark-X2.5-4B-GGUF` | https://huggingface.co/XHToken/Spark-X2.5-4B-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | repeats signal XHToken/Spark-X2.5-4B-GGUF |
| `yikuan8/Clinical-Longformer` | https://huggingface.co/yikuan8/Clinical-Longformer | 2026-09-07 | `B_hf_fillmask_dl`, `B_hf_fillmask_likes` | repeats signal yikuan8/Clinical-Longformer |
| `yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | repeats signal yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF |
| `yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | repeats signal yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF |
| `yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | repeats signal yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF |
| `yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | repeats signal yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF |
| `zai-org/GLM-4.5` | https://huggingface.co/zai-org/GLM-4.5 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of glm |
| `zai-org/GLM-4.5` | https://huggingface.co/zai-org/GLM-4.5 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal zai-org/GLM-4.5 |
| `zai-org/GLM-4.5-Air-Base` | https://huggingface.co/zai-org/GLM-4.5-Air-Base | 2026-09-07 | `hf_base_search` | release or SKU of glm |
| `zai-org/GLM-4.6` | https://huggingface.co/zai-org/GLM-4.6 | 2026-09-07 | `hf_textgen_likes` | head product glm |
| `zai-org/GLM-4.7` | https://huggingface.co/zai-org/GLM-4.7 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of glm |
| `zai-org/GLM-4.7` | https://huggingface.co/zai-org/GLM-4.7 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal zai-org/GLM-4.7 |
| `zai-org/GLM-4.7-Flash` | https://huggingface.co/zai-org/GLM-4.7-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of glm |
| `zai-org/GLM-4.7-Flash` | https://huggingface.co/zai-org/GLM-4.7-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal zai-org/GLM-4.7-Flash |
| `zai-org/GLM-4.7-Flash` | https://huggingface.co/zai-org/GLM-4.7-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal zai-org/GLM-4.7-Flash |
| `zai-org/GLM-4.7-Flash` | https://huggingface.co/zai-org/GLM-4.7-Flash | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal zai-org/GLM-4.7-Flash |
| `zai-org/GLM-5` | https://huggingface.co/zai-org/GLM-5 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of glm |
| `zai-org/GLM-5` | https://huggingface.co/zai-org/GLM-5 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal zai-org/GLM-5 |
| `zai-org/GLM-5.1` | https://huggingface.co/zai-org/GLM-5.1 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | head product glm |
| `zai-org/GLM-5.1` | https://huggingface.co/zai-org/GLM-5.1 | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal zai-org/GLM-5.1 |
| `zai-org/GLM-5.2` | https://huggingface.co/zai-org/GLM-5.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_likes` | head product glm |
| `zai-org/GLM-5.2` | https://huggingface.co/zai-org/GLM-5.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal zai-org/GLM-5.2 |
| `zai-org/GLM-5.2` | https://huggingface.co/zai-org/GLM-5.2 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `B_hf_conv_likes` | repeats signal zai-org/GLM-5.2 |
| `zai-org/GLM-5.2-FP8` | https://huggingface.co/zai-org/GLM-5.2-FP8 | 2026-09-07 | `hf_textgen_downloads` | release or SKU of glm |
| `zai-org/GLM-5.3` | https://huggingface.co/zai-org/GLM-5.3 | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_likes` | release or SKU of glm |
| `zai-org/GLM-5.3` | https://huggingface.co/zai-org/GLM-5.3 | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_likes` | repeats signal zai-org/GLM-5.3 |
| `zai-org/GLM-5.3` | https://huggingface.co/zai-org/GLM-5.3 | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_likes` | repeats signal zai-org/GLM-5.3 |
| `zai-org/GLM-5.3` | https://huggingface.co/zai-org/GLM-5.3 | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_likes` | repeats signal zai-org/GLM-5.3 |
| `zai-org/GLM-5.3-Flash` | https://huggingface.co/zai-org/GLM-5.3-Flash | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | release or SKU of glm |
| `zai-org/GLM-5.3-Flash` | https://huggingface.co/zai-org/GLM-5.3-Flash | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | repeats signal zai-org/GLM-5.3-Flash |
| `zai-org/GLM-OCR` | https://huggingface.co/zai-org/GLM-OCR | 2026-09-07 | `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of glm |
| `zai-org/GLM-OCR` | https://huggingface.co/zai-org/GLM-OCR | 2026-09-07 | `B_hf_conv_dl`, `B_hf_conv_likes` | repeats signal zai-org/GLM-OCR |
| `www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Ora` | http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-AIpro(20T).html | 2026-09-07 | — | second path tried for the same Orange Pi AIpro signal |
| `sima.ai/modalix/` | https://sima.ai/modalix/ | 2026-09-07 | — | second path tried for the same SiMa.ai signal |
| `www.blaize.com/products/blaize-pathfinder-p1600-embedded-som/` | https://www.blaize.com/products/blaize-pathfinder-p1600-embedded-som/ | 2026-09-07 | — | second path tried for the same Blaize signal |
| `www.orangepi.org/orangepiwiki/index.php/Orange_Pi_AIpro` | https://www.orangepi.org/orangepiwiki/index.php/Orange_Pi_AIpro | 2026-09-07 | — | third path tried for the same Orange Pi AIpro signal |
| `www.rock-chips.com/a/en/products/RK35_Series/2024/0705/1729.html` | https://www.rock-chips.com/a/en/products/RK35_Series/2024/0705/1729.html | 2026-09-07 | — | second path tried for the same Rockchip RK3576 signal |

## Parked — a withdrawn fold, un-folded from the duplicate table (300)

Every signal the third revision counted as a duplicate on a fold that no declaration in this
repo supports. Each is now a unique candidate, held for a person with the reason its fold was
withdrawn, its source URL, its fetch date and the queries that returned it — the same provenance
a parked candidate carries anywhere else in this sheet.

None of these 300 identifiers is a declared artifact of any head product or registry row, and
none collides with another row in this table, so each is exactly one unique candidate. None is
emitted: every one carries the recorded park reason below, which is the acceptance predicate's
`no_recorded_park_reason` clause — the clause that can only ever remove a candidate. Withdrawing
a fold therefore never admits a row; it moves a signal from the duplicate side of the
reconciliation to the unique side and holds it there.

| class | withdrawn because | rows |
|---|---|---|
| **N1** | the name carries a family token `sources/model_families.yaml` declares for the target, but the owner login is not a handle declared for any organization owning the target's artifacts, and this pass did not read the repository's own `base_model` metadata. Third-party quantizations, GGUF redistributions, abliterations and fine-tunes. | 181 |
| **N2** | the owner login *is* a declared handle of the target's organization, but `sources/model_families.yaml` declares no `<target>-*` family, so nothing in the repo bridges the checkpoint name to the head product. | 37 |
| **N3** | the repository name merely contains the target's slug as a token. Neither a declared family nor a declared handle supports the fold. | 68 |
| **N4** | the fold rested on the vendor's domain plus a path segment. `docs/reference/identity.md` is explicit that a shared homepage domain must never establish equivalence on its own. | 2 |
| **N5** | the fold rested on a sentence about what the repository *is* — a conversion, a mirror, a plugin surface, a component model, a SKU — rather than on a declaration, and the identifier is not a declared artifact of the target. | 12 |

| signal | source URL | fetched | returned by | had folded onto | why the fold is withdrawn |
|---|---|---|---|---|---|
| `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF` | https://huggingface.co/0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `0bserverx` is not a handle declared for any organization owning `qwen`'s artifacts |
| `aaron-xichen/pytorch-playground` | https://github.com/aaron-xichen/pytorch-playground | 2026-09-07 | `comp_t_quant` | release or SKU of pytorch | **N3** — name-match fold onto `pytorch` withdrawn: no `pytorch-*` family declared, and owner `aaron-xichen` is not a declared handle of `pytorch`'s organization |
| `agentionai/Qwen3.8-Flash-Next-AP-GGUF` | https://huggingface.co/agentionai/Qwen3.8-Flash-Next-AP-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `agentionai` is not a handle declared for any organization owning `qwen`'s artifacts |
| `agentionai/Qwen3.8-Flash-Next-ROCmFP4-FAST-imatrix-GGUF` | https://huggingface.co/agentionai/Qwen3.8-Flash-Next-ROCmFP4-FAST-imatrix-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `agentionai` is not a handle declared for any organization owning `qwen`'s artifacts |
| `ahmad-alismail/LLM_based_Synthetic_Data_Generation` | https://github.com/ahmad-alismail/LLM_based_Synthetic_Data_Generation | 2026-09-07 | `dpt_synth` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `ahmad-alismail` is not a declared handle of `llm`'s organization |
| `ai-safety-institute/Qwen3.6-27B-gender_secret_female-merged` | https://huggingface.co/ai-safety-institute/Qwen3.6-27B-gender_secret_female-merged | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `ai-safety-institute` is not a handle declared for any organization owning `qwen`'s artifacts |
| `alibaba-pai/MiniMax-H3-Acc-LoRAs` | https://huggingface.co/alibaba-pai/MiniMax-H3-Acc-LoRAs | 2026-09-07 | `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `alibaba-pai` is not a handle declared for any organization owning `minimax`'s artifacts |
| `allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data` | https://huggingface.co/allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data | 2026-09-07 | `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `allenai` is not a handle declared for any organization owning `llama`'s artifacts |
| `AllisonDing/LLM-data-processing-agentic-skills` | https://github.com/AllisonDing/LLM-data-processing-agentic-skills | 2026-09-07 | `dpt_q_curator` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `AllisonDing` is not a declared handle of `llm`'s organization |
| `alpindale/Llama-Guard-3-1B` | https://huggingface.co/alpindale/Llama-Guard-3-1B | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `alpindale` is not a handle declared for any organization owning `llama`'s artifacts |
| `antirez/deepseek-v4-gguf` | https://huggingface.co/antirez/deepseek-v4-gguf | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of deepseek | **N1** — name-match fold onto `deepseek` withdrawn: owner `antirez` is not a handle declared for any organization owning `deepseek`'s artifacts |
| `ARahim3/mlx-dspark` | https://github.com/ARahim3/mlx-dspark | 2026-09-07 | `B_comp_engine` | release or SKU of mlx | **N3** — name-match fold onto `mlx` withdrawn: no `mlx-*` family declared, and owner `ARahim3` is not a declared handle of `mlx`'s organization |
| `argmaxinc/whisperkit-coreml` | https://huggingface.co/argmaxinc/whisperkit-coreml | 2026-09-07 | `hf_all_downloads` | Core ML conversion of the signal openai/whisper-large-v3, not a distinct model (self-dedup) | **N5** — stated-reading fold withdrawn: `argmaxinc/whisperkit-coreml` is not a declared artifact of `openai/whisper-large-v3`, and what the repository *is* was read from its description rather than declared anywhere |
| `arnabroy734/LLM_jailbreak_shield` | https://github.com/arnabroy734/LLM_jailbreak_shield | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `arnabroy734` is not a declared handle of `llm`'s organization |
| `AtomicChat/Qwen3.8-Flash-Next-GGUF` | https://huggingface.co/AtomicChat/Qwen3.8-Flash-Next-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `AtomicChat` is not a handle declared for any organization owning `qwen`'s artifacts |
| `autogluon/chronos-2` | https://huggingface.co/autogluon/chronos-2 | 2026-09-07 | `hf_all_downloads` | mirror of the signal amazon/chronos-2 under a second owner (self-dedup) | **N5** — stated-reading fold withdrawn: `autogluon/chronos-2` is not a declared artifact of `amazon/chronos-2`, and what the repository *is* was read from its description rather than declared anywhere |
| `autogluon/chronos-bolt-small` | https://huggingface.co/autogluon/chronos-bolt-small | 2026-09-07 | `hf_all_downloads` | mirror of the signal amazon/chronos-bolt-small under a second owner (self-dedup) | **N5** — stated-reading fold withdrawn: `autogluon/chronos-bolt-small` is not a declared artifact of `amazon/chronos-bolt-small`, and what the repository *is* was read from its description rather than declared anywhere |
| `backblaze-b2-samples/nemo-curator-training-data` | https://github.com/backblaze-b2-samples/nemo-curator-training-data | 2026-09-07 | `dpt_q_curator` | release or SKU of nemo-curator | **N3** — name-match fold onto `nemo-curator` withdrawn: no `nemo-curator-*` family declared, and owner `backblaze-b2-samples` is not a declared handle of `nemo-curator`'s organization |
| `bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF` | https://huggingface.co/bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of deepseek | **N1** — name-match fold onto `deepseek` withdrawn: owner `bartowski` is not a handle declared for any organization owning `deepseek`'s artifacts |
| `bartowski/Qwen2.5-7B-Instruct-GGUF` | https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `bartowski` is not a handle declared for any organization owning `qwen`'s artifacts |
| `baseten/Llama-3.2-3B-Instruct-pythonic` | https://huggingface.co/baseten/Llama-3.2-3B-Instruct-pythonic | 2026-09-07 | `hf_base_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `baseten` is not a handle declared for any organization owning `llama`'s artifacts |
| `buildship-ai/LLM-Web-Crawler` | https://github.com/buildship-ai/LLM-Web-Crawler | 2026-09-07 | `dpt_t_webscraping` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `buildship-ai` is not a declared handle of `llm`'s organization |
| `casperhansen/llama-3-8b-instruct-awq` | https://huggingface.co/casperhansen/llama-3-8b-instruct-awq | 2026-09-07 | `hf_instruct_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `casperhansen` is not a handle declared for any organization owning `llama`'s artifacts |
| `casperhansen/llama-3.3-70b-instruct-awq` | https://huggingface.co/casperhansen/llama-3.3-70b-instruct-awq | 2026-09-07 | `hf_instruct_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `casperhansen` is not a handle declared for any organization owning `llama`'s artifacts |
| `chawins/llm-sp` | https://github.com/chawins/llm-sp | 2026-09-07 | `safe_t_llmsecurity` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `chawins` is not a declared handle of `llm`'s organization |
| `Colin6618/flashinfer-performance-benchmarks` | https://github.com/Colin6618/flashinfer-performance-benchmarks | 2026-09-07 | `comp_q_kernel` | release or SKU of flashinfer | **N3** — name-match fold onto `flashinfer` withdrawn: no `flashinfer-*` family declared, and owner `Colin6618` is not a declared handle of `flashinfer`'s organization |
| `CollieAi/llm-firewall` | https://github.com/CollieAi/llm-firewall | 2026-09-07 | `safe_t_moderation` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `CollieAi` is not a declared handle of `llm`'s organization |
| `Comfy-Org/MiniMax-H3` | https://huggingface.co/Comfy-Org/MiniMax-H3 | 2026-09-07 | `hf_all_downloads`, `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `Comfy-Org` is not a handle declared for any organization owning `minimax`'s artifacts |
| `contemmcm/qwen2.5-vl-3b-bluesky-moderation` | https://huggingface.co/contemmcm/qwen2.5-vl-3b-bluesky-moderation | 2026-09-07 | `hf_moderation_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `contemmcm` is not a handle declared for any organization owning `qwen`'s artifacts |
| `cyankiwi/gemma-4-26B-A4B-it-AWQ-4bit` | https://huggingface.co/cyankiwi/gemma-4-26B-A4B-it-AWQ-4bit | 2026-09-07 | `B_hf_conv_dl` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `cyankiwi` is not a handle declared for any organization owning `gemma`'s artifacts |
| `cyankiwi/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit` | https://huggingface.co/cyankiwi/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `cyankiwi` is not a handle declared for any organization owning `qwen`'s artifacts |
| `cyankiwi/Qwen3-Coder-30B-A3B-Instruct-AWQ-4bit` | https://huggingface.co/cyankiwi/Qwen3-Coder-30B-A3B-Instruct-AWQ-4bit | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `cyankiwi` is not a handle declared for any organization owning `qwen`'s artifacts |
| `Cyronius/Qwen3.8-Flash-Next-131B-A6B-GGUF` | https://huggingface.co/Cyronius/Qwen3.8-Flash-Next-131B-A6B-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `Cyronius` is not a handle declared for any organization owning `qwen`'s artifacts |
| `datawhalechina/llm-algo-leetcode` | https://github.com/datawhalechina/llm-algo-leetcode | 2026-09-07 | `comp_t_triton` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `datawhalechina` is not a declared handle of `llm`'s organization |
| `DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF` | https://huggingface.co/DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF | 2026-09-07 | `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `DavidAU` is not a handle declared for any organization owning `qwen`'s artifacts |
| `DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF` | https://huggingface.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `DavidAU` is not a handle declared for any organization owning `qwen`'s artifacts |
| `DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NM-DAU` | https://huggingface.co/DavidAU/Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NM-DAU | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `DavidAU` is not a handle declared for any organization owning `qwen`'s artifacts |
| `dealignai/Gemma-4-31B-JANG_4M-CRACK` | https://huggingface.co/dealignai/Gemma-4-31B-JANG_4M-CRACK | 2026-09-07 | `B_hf_conv_likes` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `dealignai` is not a handle declared for any organization owning `gemma`'s artifacts |
| `dealignai/GLM-5.3-CYBERSECURITY-FP8` | https://huggingface.co/dealignai/GLM-5.3-CYBERSECURITY-FP8 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of glm | **N1** — name-match fold onto `glm` withdrawn: owner `dealignai` is not a handle declared for any organization owning `glm`'s artifacts |
| `dealignai/GLM-5.3-UNCENSORED-FP8` | https://huggingface.co/dealignai/GLM-5.3-UNCENSORED-FP8 | 2026-09-07 | `hf_textgen_trending` | release or SKU of glm | **N1** — name-match fold onto `glm` withdrawn: owner `dealignai` is not a handle declared for any organization owning `glm`'s artifacts |
| `DevQuasar-11/ibm-granite.granite-guardian-3.1-2b-GGUF` | https://huggingface.co/DevQuasar-11/ibm-granite.granite-guardian-3.1-2b-GGUF | 2026-09-07 | `hf_guard_search` | third-party GGUF of head product granite-guardian | **N5** — stated-reading fold withdrawn: `DevQuasar-11/ibm-granite.granite-guardian-3.1-2b-GGUF` is not a declared artifact of `granite-guardian`, and what the repository *is* was read from its description rather than declared anywhere |
| `dezoito/markitdown-api` | https://github.com/dezoito/markitdown-api | 2026-09-07 | `dpt_q_pdf` | release or SKU of markitdown | **N3** — name-match fold onto `markitdown` withdrawn: no `markitdown-*` family declared, and owner `dezoito` is not a declared handle of `markitdown`'s organization |
| `eaddario/Llama-Guard-3-8B-GGUF` | https://huggingface.co/eaddario/Llama-Guard-3-8B-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `eaddario` is not a handle declared for any organization owning `llama`'s artifacts |
| `EleutherAI/pythia-160m` | https://huggingface.co/EleutherAI/pythia-160m | 2026-09-07 | `hf_textgen_downloads` | release or SKU of pythia | **N2** — name-match fold onto `pythia` withdrawn: `sources/model_families.yaml` declares no `pythia-*` family |
| `empero-ai/Qwen3.8-2B-Distill-GGUF` | https://huggingface.co/empero-ai/Qwen3.8-2B-Distill-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `empero-ai` is not a handle declared for any organization owning `qwen`'s artifacts |
| `empero-ai/Qwen3.8-9B-Distill` | https://huggingface.co/empero-ai/Qwen3.8-9B-Distill | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `empero-ai` is not a handle declared for any organization owning `qwen`'s artifacts |
| `empero-ai/Qwen3.8-9B-Distill-GGUF` | https://huggingface.co/empero-ai/Qwen3.8-9B-Distill-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `empero-ai` is not a handle declared for any organization owning `qwen`'s artifacts |
| `esatapedico/Qwen3.8-27B-NVFP4-MTP-GGUF` | https://huggingface.co/esatapedico/Qwen3.8-27B-NVFP4-MTP-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `esatapedico` is not a handle declared for any organization owning `qwen`'s artifacts |
| `facebookresearch/synth_gen` | https://github.com/facebookresearch/synth_gen | 2026-09-07 | `dpt_synth` | release or SKU of synth | **N3** — name-match fold onto `synth` withdrawn: no `synth-*` family declared, and owner `facebookresearch` is not a declared handle of `synth`'s organization |
| `FantingHeish/LLM-Inference-System-GPU-Oriented-Serving-Architecture-` | https://github.com/FantingHeish/LLM-Inference-System-GPU-Oriented-Serving-Architecture- | 2026-09-07 | `comp_q_kernel` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `FantingHeish` is not a declared handle of `llm`'s organization |
| `firecrawl/firecrawl-app-examples` | https://github.com/firecrawl/firecrawl-app-examples | 2026-09-07 | `dpt_t_webscraping` | release or SKU of firecrawl | **N2** — name-match fold onto `firecrawl` withdrawn: `sources/model_families.yaml` declares no `firecrawl-*` family |
| `FlorianBruniaux/claude-code-ultimate-guide` | https://github.com/FlorianBruniaux/claude-code-ultimate-guide | 2026-09-07 | `B_safe_aisec` | release or SKU of claude-code | **N3** — name-match fold onto `claude-code` withdrawn: no `claude-code-*` family declared, and owner `FlorianBruniaux` is not a declared handle of `claude-code`'s organization |
| `froggeric/Qwen-Fixed-Chat-Templates` | https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `froggeric` is not a handle declared for any organization owning `qwen`'s artifacts |
| `GaleneAI/llama-3.1-nemoguard-8b-content-safety-merged-NVFP4` | https://huggingface.co/GaleneAI/llama-3.1-nemoguard-8b-content-safety-merged-NVFP4 | 2026-09-07 | `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `GaleneAI` is not a handle declared for any organization owning `llama`'s artifacts |
| `gravitee-io/Llama-Prompt-Guard-2-22M-onnx` | https://huggingface.co/gravitee-io/Llama-Prompt-Guard-2-22M-onnx | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `gravitee-io` is not a handle declared for any organization owning `llama`'s artifacts |
| `gravitee-io/Llama-Prompt-Guard-2-86M-onnx` | https://huggingface.co/gravitee-io/Llama-Prompt-Guard-2-86M-onnx | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `gravitee-io` is not a handle declared for any organization owning `llama`'s artifacts |
| `group-k11/LLM-Firewall-Prompt-Injection-Detection-System` | https://github.com/group-k11/LLM-Firewall-Prompt-Injection-Detection-System | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `group-k11` is not a declared handle of `llm`'s organization |
| `GuardrailsAI/prompt-saturation-attack-detector` | https://huggingface.co/GuardrailsAI/prompt-saturation-attack-detector | 2026-09-07 | `hf_guard_search` | component model published by the org behind head product guardrails-ai; SKU of that product | **N5** — stated-reading fold withdrawn: `GuardrailsAI/prompt-saturation-attack-detector` is not a declared artifact of `guardrails-ai`, and what the repository *is* was read from its description rather than declared anywhere |
| `HauhauCS/Gemma-4-E4B-Uncensored-HauhauCS-Aggressive` | https://huggingface.co/HauhauCS/Gemma-4-E4B-Uncensored-HauhauCS-Aggressive | 2026-09-07 | `B_hf_conv_dl` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `HauhauCS` is not a handle declared for any organization owning `gemma`'s artifacts |
| `HauhauCS/Qwen3.5-35B-A3B-Uncensored-HauhauCS-Aggressive` | https://huggingface.co/HauhauCS/Qwen3.5-35B-A3B-Uncensored-HauhauCS-Aggressive | 2026-09-07 | `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `HauhauCS` is not a handle declared for any organization owning `qwen`'s artifacts |
| `HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive` | https://huggingface.co/HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive | 2026-09-07 | `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `HauhauCS` is not a handle declared for any organization owning `qwen`'s artifacts |
| `HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive` | https://huggingface.co/HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive | 2026-09-07 | `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `HauhauCS` is not a handle declared for any organization owning `qwen`'s artifacts |
| `HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF` | https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF | 2026-09-07 | `hf_all_trending`, `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `HauhauCS` is not a handle declared for any organization owning `qwen`'s artifacts |
| `helloworldzzr/Qwen3-VL-2B-Video-Moderation-LoRA` | https://huggingface.co/helloworldzzr/Qwen3-VL-2B-Video-Moderation-LoRA | 2026-09-07 | `hf_moderation_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `helloworldzzr` is not a handle declared for any organization owning `qwen`'s artifacts |
| `HoangCuongNguyen/gemma-2-9b-safety-ra-sft` | https://huggingface.co/HoangCuongNguyen/gemma-2-9b-safety-ra-sft | 2026-09-07 | `hf_safety_search` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `HoangCuongNguyen` is not a handle declared for any organization owning `gemma`'s artifacts |
| `HoangCuongNguyen/gemma-2-9b-safetysft` | https://huggingface.co/HoangCuongNguyen/gemma-2-9b-safetysft | 2026-09-07 | `hf_safety_search` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `HoangCuongNguyen` is not a handle declared for any organization owning `gemma`'s artifacts |
| `HoangCuongNguyen/qwen3-8b-safety-ra-sft` | https://huggingface.co/HoangCuongNguyen/qwen3-8b-safety-ra-sft | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `HoangCuongNguyen` is not a handle declared for any organization owning `qwen`'s artifacts |
| `HoangCuongNguyen/qwen3-8b-safetyorpo` | https://huggingface.co/HoangCuongNguyen/qwen3-8b-safetyorpo | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `HoangCuongNguyen` is not a handle declared for any organization owning `qwen`'s artifacts |
| `HoangCuongNguyen/qwen3-8b-safetysft` | https://huggingface.co/HoangCuongNguyen/qwen3-8b-safetysft | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `HoangCuongNguyen` is not a handle declared for any organization owning `qwen`'s artifacts |
| `HuggingFaceH4/zephyr-7b-alpha` | https://huggingface.co/HuggingFaceH4/zephyr-7b-alpha | 2026-09-07 | `hf_textgen_likes` | release or SKU of zephyr | **N2** — name-match fold onto `zephyr` withdrawn: `sources/model_families.yaml` declares no `zephyr-*` family |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of smollm | **N2** — name-match fold onto `smollm` withdrawn: `sources/model_families.yaml` declares no `smollm-*` family |
| `HuggingFaceTB/SmolLM2-135M` | https://huggingface.co/HuggingFaceTB/SmolLM2-135M | 2026-09-07 | `hf_textgen_downloads` | release or SKU of smollm | **N2** — name-match fold onto `smollm` withdrawn: `sources/model_families.yaml` declares no `smollm-*` family |
| `HuggingFaceTB/SmolLM2-135M-Instruct` | https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of smollm | **N2** — name-match fold onto `smollm` withdrawn: `sources/model_families.yaml` declares no `smollm-*` family |
| `HuggingFaceTB/SmolLM2-360M-Instruct` | https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of smollm | **N2** — name-match fold onto `smollm` withdrawn: `sources/model_families.yaml` declares no `smollm-*` family |
| `HuggingFaceTB/SmolLM3-3B-Base` | https://huggingface.co/HuggingFaceTB/SmolLM3-3B-Base | 2026-09-07 | `hf_base_search` | release or SKU of smollm | **N2** — name-match fold onto `smollm` withdrawn: `sources/model_families.yaml` declares no `smollm-*` family |
| `huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF` | https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF | 2026-09-07 | `hf_all_trending`, `B_hf_conv_dl` | abliterated GGUF redistribution of the signal Qwen/Qwen3.8-27B, which folds onto head product qwen | **N5** — stated-reading fold withdrawn: `huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF` is not a declared artifact of `Qwen/Qwen3.8-27B`, and what the repository *is* was read from its description rather than declared anywhere |
| `humarin/chatgpt_paraphraser_on_T5_base` | https://huggingface.co/humarin/chatgpt_paraphraser_on_T5_base | 2026-09-07 | `hf_base_search` | release or SKU of chatgpt | **N3** — name-match fold onto `chatgpt` withdrawn: no `chatgpt-*` family declared, and owner `humarin` is not a declared handle of `chatgpt`'s organization |
| `hunglc007/tensorflow-yolov4-tflite` | https://github.com/hunglc007/tensorflow-yolov4-tflite | 2026-09-07 | `B_comp_tensorrt` | release or SKU of tensorflow | **N3** — name-match fold onto `tensorflow` withdrawn: no `tensorflow-*` family declared, and owner `hunglc007` is not a declared handle of `tensorflow`'s organization |
| `ibm-granite/granite-3.0-1b-a400m-base` | https://huggingface.co/ibm-granite/granite-3.0-1b-a400m-base | 2026-09-07 | `hf_base_search` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-3.0-8b-base` | https://huggingface.co/ibm-granite/granite-3.0-8b-base | 2026-09-07 | `hf_base_search` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-3.1-1b-a400m-base` | https://huggingface.co/ibm-granite/granite-3.1-1b-a400m-base | 2026-09-07 | `hf_base_search` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-3b-code-base-2k` | https://huggingface.co/ibm-granite/granite-3b-code-base-2k | 2026-09-07 | `hf_base_search` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-4.0-1b-base` | https://huggingface.co/ibm-granite/granite-4.0-1b-base | 2026-09-07 | `hf_base_search` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-4.1-3b-base` | https://huggingface.co/ibm-granite/granite-4.1-3b-base | 2026-09-07 | `hf_base_search` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-4.1-8b-base` | https://huggingface.co/ibm-granite/granite-4.1-8b-base | 2026-09-07 | `hf_base_search` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-4.2-30b` | https://huggingface.co/ibm-granite/granite-4.2-30b | 2026-09-07 | `hf_textgen_trending` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-4.2-3b` | https://huggingface.co/ibm-granite/granite-4.2-3b | 2026-09-07 | `hf_textgen_trending` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-4.2-8b` | https://huggingface.co/ibm-granite/granite-4.2-8b | 2026-09-07 | `hf_textgen_trending` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-docling-258M` | https://huggingface.co/ibm-granite/granite-docling-258M | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-embedding-small-english-r2` | https://huggingface.co/ibm-granite/granite-embedding-small-english-r2 | 2026-09-07 | `hf_all_downloads` | release or SKU of granite | **N2** — name-match fold onto `granite` withdrawn: `sources/model_families.yaml` declares no `granite-*` family |
| `ibm-granite/granite-guardian-3.0-2b` | https://huggingface.co/ibm-granite/granite-guardian-3.0-2b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-3.0-8b` | https://huggingface.co/ibm-granite/granite-guardian-3.0-8b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-3.1-2b` | https://huggingface.co/ibm-granite/granite-guardian-3.1-2b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-3.1-8b` | https://huggingface.co/ibm-granite/granite-guardian-3.1-8b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-3.2-3b-a800m` | https://huggingface.co/ibm-granite/granite-guardian-3.2-3b-a800m | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-3.2-8b-factuality-detection` | https://huggingface.co/ibm-granite/granite-guardian-3.2-8b-factuality-detection | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-3.3-8b` | https://huggingface.co/ibm-granite/granite-guardian-3.3-8b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-3.3-8b-GGUF` | https://huggingface.co/ibm-granite/granite-guardian-3.3-8b-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-4.1-8b` | https://huggingface.co/ibm-granite/granite-guardian-4.1-8b | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-4.1-8b-GGUF` | https://huggingface.co/ibm-granite/granite-guardian-4.1-8b-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-hap-125m` | https://huggingface.co/ibm-granite/granite-guardian-hap-125m | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `ibm-granite/granite-guardian-hap-38m` | https://huggingface.co/ibm-granite/granite-guardian-hap-38m | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N2** — name-match fold onto `granite-guardian` withdrawn: `sources/model_families.yaml` declares no `granite-guardian-*` family |
| `IFM/K2-Horizon-0.9B` | https://huggingface.co/IFM/K2-Horizon-0.9B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `IFM/K2-Horizon-3.7B` | https://huggingface.co/IFM/K2-Horizon-3.7B | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `IFM/K2-Horizon-3.7B-GGUF` | https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `IFM/K2-Horizon-32B` | https://huggingface.co/IFM/K2-Horizon-32B | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `IFM/K2-Horizon-375B-A23B` | https://huggingface.co/IFM/K2-Horizon-375B-A23B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `IFM/K2-Horizon-7B` | https://huggingface.co/IFM/K2-Horizon-7B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `IFM/K2-Horizon-7B-GGUF` | https://huggingface.co/IFM/K2-Horizon-7B-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `IFM/K2-Horizon-7B-Uno` | https://huggingface.co/IFM/K2-Horizon-7B-Uno | 2026-09-07 | `hf_textgen_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `IFM/K2-Horizon-MoVA-36B-A4B` | https://huggingface.co/IFM/K2-Horizon-MoVA-36B-A4B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `IFM/K2-Horizon-MoVA-36B-A4B-GGUF` | https://huggingface.co/IFM/K2-Horizon-MoVA-36B-A4B-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of k2 | **N1** — name-match fold onto `k2` withdrawn: owner `IFM` is not a handle declared for any organization owning `k2`'s artifacts |
| `incoai/GLM-5.3-Flash-DFlash2` | https://huggingface.co/incoai/GLM-5.3-Flash-DFlash2 | 2026-09-07 | `hf_textgen_trending` | release or SKU of glm | **N1** — name-match fold onto `glm` withdrawn: owner `incoai` is not a handle declared for any organization owning `glm`'s artifacts |
| `incoai/Qwen3.8-27B-DFlash2` | https://huggingface.co/incoai/Qwen3.8-27B-DFlash2 | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `incoai` is not a handle declared for any organization owning `qwen`'s artifacts |
| `ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF` | https://huggingface.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `ISTA-DASLab` is not a handle declared for any organization owning `qwen`'s artifacts |
| `Jab1718/qwen3.8-flash-coder-85gb-bf16` | https://huggingface.co/Jab1718/qwen3.8-flash-coder-85gb-bf16 | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `Jab1718` is not a handle declared for any organization owning `qwen`'s artifacts |
| `jackhhao/llm-warden` | https://github.com/jackhhao/llm-warden | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `jackhhao` is not a declared handle of `llm`'s organization |
| `Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled` | https://huggingface.co/Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled | 2026-09-07 | `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `Jackrong` is not a handle declared for any organization owning `qwen`'s artifacts |
| `janhq/Jan-v3-4B-base-instruct-gguf` | https://huggingface.co/janhq/Jan-v3-4B-base-instruct-gguf | 2026-09-07 | `hf_base_search` | release or SKU of jan | **N2** — name-match fold onto `jan` withdrawn: `sources/model_families.yaml` declares no `jan-*` family |
| `Jerry2423/Triton-Attention-Kernels` | https://github.com/Jerry2423/Triton-Attention-Kernels | 2026-09-07 | `comp_q_kernel` | release or SKU of triton | **N3** — name-match fold onto `triton` withdrawn: no `triton-*` family declared, and owner `Jerry2423` is not a declared handle of `triton`'s organization |
| `JJCKA/MarkItDown-GUI` | https://github.com/JJCKA/MarkItDown-GUI | 2026-09-07 | `dpt_q_pdf` | release or SKU of markitdown | **N3** — name-match fold onto `markitdown` withdrawn: no `markitdown-*` family declared, and owner `JJCKA` is not a declared handle of `markitdown`'s organization |
| `JonathanColetti/Qwen3.8-27B-Uncensored-GGUF` | https://huggingface.co/JonathanColetti/Qwen3.8-27B-Uncensored-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `JonathanColetti` is not a handle declared for any organization owning `qwen`'s artifacts |
| `jrajath94/triton-inference-kernels` | https://github.com/jrajath94/triton-inference-kernels | 2026-09-07 | `comp_q_kernel` | release or SKU of triton | **N3** — name-match fold onto `triton` withdrawn: no `triton-*` family declared, and owner `jrajath94` is not a declared handle of `triton`'s organization |
| `kenflab/LLM-scCurator` | https://github.com/kenflab/LLM-scCurator | 2026-09-07 | `dpt_q_curator` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `kenflab` is not a declared handle of `llm`'s organization |
| `Kijai/MiniMax-H3-experimental` | https://huggingface.co/Kijai/MiniMax-H3-experimental | 2026-09-07 | `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `Kijai` is not a handle declared for any organization owning `minimax`'s artifacts |
| `kmseong/llama2_7b-chat-Safety-FT-lr5e-5` | https://huggingface.co/kmseong/llama2_7b-chat-Safety-FT-lr5e-5 | 2026-09-07 | `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `kmseong` is not a handle declared for any organization owning `llama`'s artifacts |
| `KrakowiakK/vllm-apple` | https://github.com/KrakowiakK/vllm-apple | 2026-09-07 | `comp_q_kernel` | release or SKU of vllm | **N3** — name-match fold onto `vllm` withdrawn: no `vllm-*` family declared, and owner `KrakowiakK` is not a declared handle of `vllm`'s organization |
| `Krusty84/triton-ascend-agent-dev-kit` | https://github.com/Krusty84/triton-ascend-agent-dev-kit | 2026-09-07 | `edge_t_npu` | release or SKU of triton | **N3** — name-match fold onto `triton` withdrawn: no `triton-*` family declared, and owner `Krusty84` is not a declared handle of `triton`'s organization |
| `LaaP-ai/qwen-base-invoicev1.01-1.5B` | https://huggingface.co/LaaP-ai/qwen-base-invoicev1.01-1.5B | 2026-09-07 | `hf_base_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `LaaP-ai` is not a handle declared for any organization owning `qwen`'s artifacts |
| `lastSoln/llm-training-data-pipeline` | https://github.com/lastSoln/llm-training-data-pipeline | 2026-09-07 | `dpt_dedup` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `lastSoln` is not a declared handle of `llm`'s organization |
| `laugh12321/TensorRT-YOLO` | https://github.com/laugh12321/TensorRT-YOLO | 2026-09-07 | `B_comp_tensorrt` | release or SKU of tensorrt | **N3** — name-match fold onto `tensorrt` withdrawn: no `tensorrt-*` family declared, and owner `laugh12321` is not a declared handle of `tensorrt`'s organization |
| `legraphista/glm-4-9b-chat-IMat-GGUF` | https://huggingface.co/legraphista/glm-4-9b-chat-IMat-GGUF | 2026-09-07 | `hf_textgen_downloads` | release or SKU of glm | **N1** — name-match fold onto `glm` withdrawn: owner `legraphista` is not a handle declared for any organization owning `glm`'s artifacts |
| `legraphista/Llama-Guard-3-8B-IMat-GGUF` | https://huggingface.co/legraphista/Llama-Guard-3-8B-IMat-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `legraphista` is not a handle declared for any organization owning `llama`'s artifacts |
| `lennyerik/crawl4ai-proxy` | https://github.com/lennyerik/crawl4ai-proxy | 2026-09-07 | `dpt_t_webscraping` | release or SKU of crawl4ai | **N3** — name-match fold onto `crawl4ai` withdrawn: no `crawl4ai-*` family declared, and owner `lennyerik` is not a declared handle of `crawl4ai`'s organization |
| `lightx2v/Minimax-h3-Turbo` | https://huggingface.co/lightx2v/Minimax-h3-Turbo | 2026-09-07 | `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `lightx2v` is not a handle declared for any organization owning `minimax`'s artifacts |
| `lmstudio-community/Qwen3.8-27B-GGUF` | https://huggingface.co/lmstudio-community/Qwen3.8-27B-GGUF | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `lmstudio-community` is not a handle declared for any organization owning `qwen`'s artifacts |
| `lmstudio-community/Qwen3.8-27B-MLX-4bit` | https://huggingface.co/lmstudio-community/Qwen3.8-27B-MLX-4bit | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `lmstudio-community` is not a handle declared for any organization owning `qwen`'s artifacts |
| `lmstudio-community/Qwen3.8-27B-MLX-5bit` | https://huggingface.co/lmstudio-community/Qwen3.8-27B-MLX-5bit | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `lmstudio-community` is not a handle declared for any organization owning `qwen`'s artifacts |
| `lmstudio-community/Qwen3.8-27B-MLX-6bit` | https://huggingface.co/lmstudio-community/Qwen3.8-27B-MLX-6bit | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `lmstudio-community` is not a handle declared for any organization owning `qwen`'s artifacts |
| `lmstudio-community/Qwen3.8-27B-MLX-8bit` | https://huggingface.co/lmstudio-community/Qwen3.8-27B-MLX-8bit | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `lmstudio-community` is not a handle declared for any organization owning `qwen`'s artifacts |
| `macadeliccc/gemma-2b-openai-content-moderation` | https://huggingface.co/macadeliccc/gemma-2b-openai-content-moderation | 2026-09-07 | `hf_moderation_search` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `macadeliccc` is not a handle declared for any organization owning `gemma`'s artifacts |
| `MaitreChen/openvino-lenet-sample` | https://github.com/MaitreChen/openvino-lenet-sample | 2026-09-07 | `B_comp_modelopt` | release or SKU of openvino | **N3** — name-match fold onto `openvino` withdrawn: no `openvino-*` family declared, and owner `MaitreChen` is not a declared handle of `openvino`'s organization |
| `manishklach/mlx-metal-kernels` | https://github.com/manishklach/mlx-metal-kernels | 2026-09-07 | `comp_q_kernel` | release or SKU of mlx | **N3** — name-match fold onto `mlx` withdrawn: no `mlx-*` family declared, and owner `manishklach` is not a declared handle of `mlx`'s organization |
| `matank001/cursor-security-rules` | https://github.com/matank001/cursor-security-rules | 2026-09-07 | `B_safe_agentsec` | release or SKU of cursor | **N3** — name-match fold onto `cursor` withdrawn: no `cursor-*` family declared, and owner `matank001` is not a declared handle of `cursor`'s organization |
| `MATLOWAI/minimax-h3-fused-turbo-int8-convrot` | https://huggingface.co/MATLOWAI/minimax-h3-fused-turbo-int8-convrot | 2026-09-07 | `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `MATLOWAI` is not a handle declared for any organization owning `minimax`'s artifacts |
| `MaziyarPanahi/Qwen3-4B-Instruct-2507-GGUF` | https://huggingface.co/MaziyarPanahi/Qwen3-4B-Instruct-2507-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `MaziyarPanahi` is not a handle declared for any organization owning `qwen`'s artifacts |
| `MergeBench/Llama-3.2-3B_safety` | https://huggingface.co/MergeBench/Llama-3.2-3B_safety | 2026-09-07 | `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `MergeBench` is not a handle declared for any organization owning `llama`'s artifacts |
| `Merlin-Research/Qwen3.5-4B-Safety-Thinking` | https://huggingface.co/Merlin-Research/Qwen3.5-4B-Safety-Thinking | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `Merlin-Research` is not a handle declared for any organization owning `qwen`'s artifacts |
| `meta-llama/Meta-Llama-3-8B-Instruct` | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_instruct_search`, `B_hf_conv_likes` | SKU of head product llama-instruct (llama-* family) | **N5** — stated-reading fold withdrawn: `meta-llama/Meta-Llama-3-8B-Instruct` is not a declared artifact of `llama-instruct`, and what the repository *is* was read from its description rather than declared anywhere |
| `meta-llama/Prompt-Guard-86M` | https://huggingface.co/meta-llama/Prompt-Guard-86M | 2026-09-07 | `hf_all_downloads`, `hf_guard_search` | release of head product llama-prompt-guard | **N5** — stated-reading fold withdrawn: `meta-llama/Prompt-Guard-86M` is not a declared artifact of `llama-prompt-guard`, and what the repository *is* was read from its description rather than declared anywhere |
| `Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw` | https://huggingface.co/Mia-AiLab/Qwen3.8-27B-EXL3-3.5bpw | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `Mia-AiLab` is not a handle declared for any organization owning `qwen`'s artifacts |
| `mlabonne/llm-datasets` | https://github.com/mlabonne/llm-datasets | 2026-09-07 | `B_dpt_datasetllm` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `mlabonne` is not a declared handle of `llm`'s organization |
| `mlx-community/Llama-3.1-8B-Instruct-4bit` | https://huggingface.co/mlx-community/Llama-3.1-8B-Instruct-4bit | 2026-09-07 | `hf_instruct_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `mlx-community` is not a handle declared for any organization owning `llama`'s artifacts |
| `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit` | https://huggingface.co/mlx-community/Qwen2.5-Coder-7B-Instruct-4bit | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `mlx-community` is not a handle declared for any organization owning `qwen`'s artifacts |
| `mradermacher/ernie-4.5-0.3b-aegis-safety-lora-GGUF` | https://huggingface.co/mradermacher/ernie-4.5-0.3b-aegis-safety-lora-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of ernie | **N1** — name-match fold onto `ernie` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `ernie`'s artifacts |
| `mradermacher/gemma-4-12B-it-Guardpoint-GGUF` | https://huggingface.co/mradermacher/gemma-4-12B-it-Guardpoint-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `gemma`'s artifacts |
| `mradermacher/gemma-4-12B-it-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/gemma-4-12B-it-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `gemma`'s artifacts |
| `mradermacher/gemma-4-31B-it-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/gemma-4-31B-it-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `gemma`'s artifacts |
| `mradermacher/Gemma-SEA-Guard-12B-2602-i1-GGUF` | https://huggingface.co/mradermacher/Gemma-SEA-Guard-12B-2602-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `gemma`'s artifacts |
| `mradermacher/gpt-oss-20b-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/gpt-oss-20b-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of gpt-oss | **N3** — name-match fold onto `gpt-oss` withdrawn: no `gpt-oss-*` family declared, and owner `mradermacher` is not a declared handle of `gpt-oss`'s organization |
| `mradermacher/granite-3.3-2b-instruct-heretic-safety-defiltered-GGUF` | https://huggingface.co/mradermacher/granite-3.3-2b-instruct-heretic-safety-defiltered-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of granite | **N3** — name-match fold onto `granite` withdrawn: no `granite-*` family declared, and owner `mradermacher` is not a declared handle of `granite`'s organization |
| `mradermacher/granite-3.3-2b-instruct-heretic-safety-defiltered-i1-GGUF` | https://huggingface.co/mradermacher/granite-3.3-2b-instruct-heretic-safety-defiltered-i1-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of granite | **N3** — name-match fold onto `granite` withdrawn: no `granite-*` family declared, and owner `mradermacher` is not a declared handle of `granite`'s organization |
| `mradermacher/granite-guardian-3.1-8b-i1-GGUF` | https://huggingface.co/mradermacher/granite-guardian-3.1-8b-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N3** — name-match fold onto `granite-guardian` withdrawn: no `granite-guardian-*` family declared, and owner `mradermacher` is not a declared handle of `granite-guardian`'s organization |
| `mradermacher/granite-guardian-3.2-5b-i1-GGUF` | https://huggingface.co/mradermacher/granite-guardian-3.2-5b-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N3** — name-match fold onto `granite-guardian` withdrawn: no `granite-guardian-*` family declared, and owner `mradermacher` is not a declared handle of `granite-guardian`'s organization |
| `mradermacher/granite-guardian-3.3-8b-i1-GGUF` | https://huggingface.co/mradermacher/granite-guardian-3.3-8b-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N3** — name-match fold onto `granite-guardian` withdrawn: no `granite-guardian-*` family declared, and owner `mradermacher` is not a declared handle of `granite-guardian`'s organization |
| `mradermacher/Llama-3.1-Nemotron-Safety-Guard-8B-v3-GGUF` | https://huggingface.co/mradermacher/Llama-3.1-Nemotron-Safety-Guard-8B-v3-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `llama`'s artifacts |
| `mradermacher/Llama-3.1-Tulu-3-8B-SFT-no-safety-data-i1-GGUF` | https://huggingface.co/mradermacher/Llama-3.1-Tulu-3-8B-SFT-no-safety-data-i1-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `llama`'s artifacts |
| `mradermacher/Llama-Guard-3-8B-GGUF` | https://huggingface.co/mradermacher/Llama-Guard-3-8B-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `llama`'s artifacts |
| `mradermacher/Llama-Guard-3-8B-i1-GGUF` | https://huggingface.co/mradermacher/Llama-Guard-3-8B-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `llama`'s artifacts |
| `mradermacher/Nemotron-3-Content-Safety-GGUF` | https://huggingface.co/mradermacher/Nemotron-3-Content-Safety-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron | **N1** — name-match fold onto `nemotron` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `nemotron`'s artifacts |
| `mradermacher/Nemotron-3.5-Content-Safety-GGUF` | https://huggingface.co/mradermacher/Nemotron-3.5-Content-Safety-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron | **N1** — name-match fold onto `nemotron` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `nemotron`'s artifacts |
| `mradermacher/Qwen3-14B-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3-14B-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `qwen`'s artifacts |
| `mradermacher/Qwen3-32B-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3-32B-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `qwen`'s artifacts |
| `mradermacher/Qwen3-VL-8B-SafetyGRPO-ablation-120-GGUF` | https://huggingface.co/mradermacher/Qwen3-VL-8B-SafetyGRPO-ablation-120-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `qwen`'s artifacts |
| `mradermacher/Qwen3-VL-8B-SafetyGRPO-ablation-120-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3-VL-8B-SafetyGRPO-ablation-120-i1-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `qwen`'s artifacts |
| `mradermacher/Qwen3.5-27B-Guardpoint-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3.5-27B-Guardpoint-i1-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `qwen`'s artifacts |
| `mradermacher/Qwen3.5-4B-Safety-Thinking-GGUF` | https://huggingface.co/mradermacher/Qwen3.5-4B-Safety-Thinking-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `qwen`'s artifacts |
| `mradermacher/Qwen3.5-4B-Safety-Thinking-i1-GGUF` | https://huggingface.co/mradermacher/Qwen3.5-4B-Safety-Thinking-i1-GGUF | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `mradermacher` is not a handle declared for any organization owning `qwen`'s artifacts |
| `mrutkows/granite-guardian-4.1-8b-GGUF` | https://huggingface.co/mrutkows/granite-guardian-4.1-8b-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N3** — name-match fold onto `granite-guardian` withdrawn: no `granite-guardian-*` family declared, and owner `mrutkows` is not a declared handle of `granite-guardian`'s organization |
| `Mungert/granite-guardian-3.2-3b-a800m-GGUF` | https://huggingface.co/Mungert/granite-guardian-3.2-3b-a800m-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N3** — name-match fold onto `granite-guardian` withdrawn: no `granite-guardian-*` family declared, and owner `Mungert` is not a declared handle of `granite-guardian`'s organization |
| `Mungert/granite-guardian-3.2-5b-GGUF` | https://huggingface.co/Mungert/granite-guardian-3.2-5b-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of granite-guardian | **N3** — name-match fold onto `granite-guardian` withdrawn: no `granite-guardian-*` family declared, and owner `Mungert` is not a declared handle of `granite-guardian`'s organization |
| `navyavelicheti10/LLM_Firewall` | https://github.com/navyavelicheti10/LLM_Firewall | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `navyavelicheti10` is not a declared handle of `llm`'s organization |
| `NeelRajani/Qwen3-0.6B-Base_SFT-safety100_ADV-pku-v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT-safety100_ADV-pku-v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `NeelRajani` is not a handle declared for any organization owning `qwen`'s artifacts |
| `NeelRajani/Qwen3-0.6B-Base_SFT-safety25_ADV-pku-v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT-safety25_ADV-pku-v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `NeelRajani` is not a handle declared for any organization owning `qwen`'s artifacts |
| `NeelRajani/Qwen3-0.6B-Base_SFT-safety50_ADV-pku-v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT-safety50_ADV-pku-v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `NeelRajani` is not a handle declared for any organization owning `qwen`'s artifacts |
| `NeelRajani/Qwen3-0.6B-Base_SFT-safety75_ADV-pku-v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT-safety75_ADV-pku-v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `NeelRajani` is not a handle declared for any organization owning `qwen`'s artifacts |
| `NeelRajani/Qwen3-0.6B-Base_SFT_safety_v00.01` | https://huggingface.co/NeelRajani/Qwen3-0.6B-Base_SFT_safety_v00.01 | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `NeelRajani` is not a handle declared for any organization owning `qwen`'s artifacts |
| `nghuyong/ernie-3.0-base-zh` | https://huggingface.co/nghuyong/ernie-3.0-base-zh | 2026-09-07 | `B_hf_fillmask_likes` | release or SKU of ernie | **N1** — name-match fold onto `ernie` withdrawn: owner `nghuyong` is not a handle declared for any organization owning `ernie`'s artifacts |
| `nihui/ncnn-small-board` | https://github.com/nihui/ncnn-small-board | 2026-09-07 | `edge_t_sbc` | release or SKU of ncnn | **N3** — name-match fold onto `ncnn` withdrawn: no `ncnn-*` family declared, and owner `nihui` is not a declared handle of `ncnn`'s organization |
| `nm-testing/SmolLM-1.7B-Instruct-quantized.w4a16` | https://huggingface.co/nm-testing/SmolLM-1.7B-Instruct-quantized.w4a16 | 2026-09-07 | `hf_instruct_search` | release or SKU of smollm | **N3** — name-match fold onto `smollm` withdrawn: no `smollm-*` family declared, and owner `nm-testing` is not a declared handle of `smollm`'s organization |
| `nod-ai/AMD-SHARK-Studio` | https://github.com/nod-ai/AMD-SHARK-Studio | 2026-09-07 | `comp_t_mlir` | web UI over SHARK+IREE; SKU of head product iree | **N5** — stated-reading fold withdrawn: `nod-ai/AMD-SHARK-Studio` is not a declared artifact of `iree`, and what the repository *is* was read from its description rather than declared anywhere |
| `nooruiit-864/qwen2.5-1.5b-base-ai-safety-domain-lora` | https://huggingface.co/nooruiit-864/qwen2.5-1.5b-base-ai-safety-domain-lora | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `nooruiit-864` is not a handle declared for any organization owning `qwen`'s artifacts |
| `Null-Guard/Qwen3-0.6B-Uncensored-GGUF` | https://huggingface.co/Null-Guard/Qwen3-0.6B-Uncensored-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `Null-Guard` is not a handle declared for any organization owning `qwen`'s artifacts |
| `Null-Guard/Qwen3.5-0.8B-Uncensored-GGUF` | https://huggingface.co/Null-Guard/Qwen3.5-0.8B-Uncensored-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `Null-Guard` is not a handle declared for any organization owning `qwen`'s artifacts |
| `nunchux-ai/ComfyUI-nunchaku` | https://github.com/nunchux-ai/ComfyUI-nunchaku | 2026-09-07 | `comp_t_quant` | ComfyUI plugin surface of nunchaku, which this batch emits as its own row (self-dedup) | **N5** — stated-reading fold withdrawn: `nunchux-ai/ComfyUI-nunchaku` is not a declared artifact of `nunchaku`, and what the repository *is* was read from its description rather than declared anywhere |
| `nvidia/DeepSeek-V4-Flash-0731-NVFP4` | https://huggingface.co/nvidia/DeepSeek-V4-Flash-0731-NVFP4 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of deepseek | **N1** — name-match fold onto `deepseek` withdrawn: owner `nvidia` is not a handle declared for any organization owning `deepseek`'s artifacts |
| `nvidia/Gemma-4-26B-A4B-NVFP4` | https://huggingface.co/nvidia/Gemma-4-26B-A4B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `nvidia` is not a handle declared for any organization owning `gemma`'s artifacts |
| `nvidia/Gemma-4-31B-IT-NVFP4` | https://huggingface.co/nvidia/Gemma-4-31B-IT-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `nvidia` is not a handle declared for any organization owning `gemma`'s artifacts |
| `nvidia/llama-3.1-nemoguard-8b-content-safety` | https://huggingface.co/nvidia/llama-3.1-nemoguard-8b-content-safety | 2026-09-07 | `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `nvidia` is not a handle declared for any organization owning `llama`'s artifacts |
| `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF` | https://huggingface.co/nvidia/Llama-3.1-Nemotron-70B-Instruct-HF | 2026-09-07 | `hf_textgen_likes`, `B_hf_conv_likes` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `nvidia` is not a handle declared for any organization owning `llama`'s artifacts |
| `nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3` | https://huggingface.co/nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3 | 2026-09-07 | `hf_guard_search`, `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `nvidia` is not a handle declared for any organization owning `llama`'s artifacts |
| `nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16 | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | SKU of head product nemotron | **N5** — stated-reading fold withdrawn: `nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16` is not a declared artifact of `nemotron`, and what the repository *is* was read from its description rather than declared anywhere |
| `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4` | https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending` | SKU of head product nemotron | **N5** — stated-reading fold withdrawn: `nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-NVFP4` is not a declared artifact of `nemotron`, and what the repository *is* was read from its description rather than declared anywhere |
| `nvidia/Qwen3.5-122B-A10B-NVFP4` | https://huggingface.co/nvidia/Qwen3.5-122B-A10B-NVFP4 | 2026-09-07 | `hf_textgen_downloads` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `nvidia` is not a handle declared for any organization owning `qwen`'s artifacts |
| `nvidia/Qwen3.6-35B-A3B-NVFP4` | https://huggingface.co/nvidia/Qwen3.6-35B-A3B-NVFP4 | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `nvidia` is not a handle declared for any organization owning `qwen`'s artifacts |
| `nvidia/Qwen3.8-Flash-Next-NVFP4` | https://huggingface.co/nvidia/Qwen3.8-Flash-Next-NVFP4 | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `nvidia` is not a handle declared for any organization owning `qwen`'s artifacts |
| `OBLITERATUS/Ornith-1.5-9B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Ornith-1.5-9B-OBLITERATED | 2026-09-07 | `hf_textgen_trending` | release or SKU of ornith | **N3** — name-match fold onto `ornith` withdrawn: no `ornith-*` family declared, and owner `OBLITERATUS` is not a declared handle of `ornith`'s organization |
| `OBLITERATUS/Qwen3.8-27B-OBLITERATED` | https://huggingface.co/OBLITERATUS/Qwen3.8-27B-OBLITERATED | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_likes`, `hf_textgen_trending`, `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `OBLITERATUS` is not a handle declared for any organization owning `qwen`'s artifacts |
| `oneonlee/llama-3.1-nemoguard-8b-content-safety-merged` | https://huggingface.co/oneonlee/llama-3.1-nemoguard-8b-content-safety-merged | 2026-09-07 | `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `oneonlee` is not a handle declared for any organization owning `llama`'s artifacts |
| `openbmb/MiniCPM-Llama3-V-2_5` | https://huggingface.co/openbmb/MiniCPM-Llama3-V-2_5 | 2026-09-07 | `B_hf_conv_likes` | release or SKU of minicpm | **N2** — name-match fold onto `minicpm` withdrawn: `sources/model_families.yaml` declares no `minicpm-*` family |
| `openbmb/MiniCPM5-1B-Base` | https://huggingface.co/openbmb/MiniCPM5-1B-Base | 2026-09-07 | `hf_base_search` | release or SKU of minicpm | **N2** — name-match fold onto `minicpm` withdrawn: `sources/model_families.yaml` declares no `minicpm-*` family |
| `orcarouter/DeepSeek-V4-Flash-Vision-Uncensored` | https://huggingface.co/orcarouter/DeepSeek-V4-Flash-Vision-Uncensored | 2026-09-07 | `hf_textgen_trending` | release or SKU of deepseek | **N1** — name-match fold onto `deepseek` withdrawn: owner `orcarouter` is not a handle declared for any organization owning `deepseek`'s artifacts |
| `orcarouter/DeepSeek-V4-Flash-Vision-Uncensored-GGUF` | https://huggingface.co/orcarouter/DeepSeek-V4-Flash-Vision-Uncensored-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of deepseek | **N1** — name-match fold onto `deepseek` withdrawn: owner `orcarouter` is not a handle declared for any organization owning `deepseek`'s artifacts |
| `orcarouter/GLM-5.3-Flash-Uncensored-FP8` | https://huggingface.co/orcarouter/GLM-5.3-Flash-Uncensored-FP8 | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of glm | **N1** — name-match fold onto `glm` withdrawn: owner `orcarouter` is not a handle declared for any organization owning `glm`'s artifacts |
| `orcarouter/GLM-5.3-Flash-Uncensored-NVFP4` | https://huggingface.co/orcarouter/GLM-5.3-Flash-Uncensored-NVFP4 | 2026-09-07 | `hf_all_trending` | release or SKU of glm | **N1** — name-match fold onto `glm` withdrawn: owner `orcarouter` is not a handle declared for any organization owning `glm`'s artifacts |
| `orcarouter/Qwen3.8-27B-Uncensored` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `orcarouter` is not a handle declared for any organization owning `qwen`'s artifacts |
| `orcarouter/Qwen3.8-27B-Uncensored-FP8` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored-FP8 | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `orcarouter` is not a handle declared for any organization owning `qwen`'s artifacts |
| `orcarouter/Qwen3.8-27B-Uncensored-GGUF` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `orcarouter` is not a handle declared for any organization owning `qwen`'s artifacts |
| `orcarouter/Qwen3.8-27B-Uncensored-MLX` | https://huggingface.co/orcarouter/Qwen3.8-27B-Uncensored-MLX | 2026-09-07 | `hf_all_trending`, `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `orcarouter` is not a handle declared for any organization owning `qwen`'s artifacts |
| `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF` | https://huggingface.co/orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `orcarouter` is not a handle declared for any organization owning `qwen`'s artifacts |
| `OriginalByteMe/langfuse-dataset-curator` | https://github.com/OriginalByteMe/langfuse-dataset-curator | 2026-09-07 | `dpt_q_curator` | release or SKU of langfuse | **N3** — name-match fold onto `langfuse` withdrawn: no `langfuse-*` family declared, and owner `OriginalByteMe` is not a declared handle of `langfuse`'s organization |
| `Orion-zhen/Qwen2.5-Coder-7B-Instruct-AWQ` | https://huggingface.co/Orion-zhen/Qwen2.5-Coder-7B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `Orion-zhen` is not a handle declared for any organization owning `qwen`'s artifacts |
| `ornith-ai/Ornith-1.0-35B` | https://huggingface.co/ornith-ai/Ornith-1.0-35B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of ornith | **N3** — name-match fold onto `ornith` withdrawn: no `ornith-*` family declared, and owner `ornith-ai` is not a declared handle of `ornith`'s organization |
| `ornith-ai/Ornith-1.0-35B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.0-35B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of ornith | **N3** — name-match fold onto `ornith` withdrawn: no `ornith-*` family declared, and owner `ornith-ai` is not a declared handle of `ornith`'s organization |
| `ornith-ai/Ornith-1.0-9B` | https://huggingface.co/ornith-ai/Ornith-1.0-9B | 2026-09-07 | `hf_textgen_downloads`, `B_hf_conv_dl` | release or SKU of ornith | **N3** — name-match fold onto `ornith` withdrawn: no `ornith-*` family declared, and owner `ornith-ai` is not a declared handle of `ornith`'s organization |
| `ornith-ai/Ornith-1.0-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.0-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_all_downloads`, `B_hf_conv_dl` | release or SKU of ornith | **N3** — name-match fold onto `ornith` withdrawn: no `ornith-*` family declared, and owner `ornith-ai` is not a declared handle of `ornith`'s organization |
| `ornith-ai/Ornith-1.5-35B-A3B` | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of ornith | **N3** — name-match fold onto `ornith` withdrawn: no `ornith-*` family declared, and owner `ornith-ai` is not a declared handle of `ornith`'s organization |
| `ornith-ai/Ornith-1.5-35B-A3B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `B_hf_conv_dl` | release or SKU of ornith | **N3** — name-match fold onto `ornith` withdrawn: no `ornith-*` family declared, and owner `ornith-ai` is not a declared handle of `ornith`'s organization |
| `ornith-ai/Ornith-1.5-9B` | https://huggingface.co/ornith-ai/Ornith-1.5-9B | 2026-09-07 | `hf_textgen_trending` | release or SKU of ornith | **N3** — name-match fold onto `ornith` withdrawn: no `ornith-*` family declared, and owner `ornith-ai` is not a declared handle of `ornith`'s organization |
| `ornith-ai/Ornith-1.5-9B-GGUF` | https://huggingface.co/ornith-ai/Ornith-1.5-9B-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_trending`, `B_hf_conv_dl` | release or SKU of ornith | **N3** — name-match fold onto `ornith` withdrawn: no `ornith-*` family declared, and owner `ornith-ai` is not a declared handle of `ornith`'s organization |
| `outsourc-e/Qwen3.8-27B-Unleashed-GGUF` | https://huggingface.co/outsourc-e/Qwen3.8-27B-Unleashed-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `outsourc-e` is not a handle declared for any organization owning `qwen`'s artifacts |
| `PaddlePaddle/Paddle.js` | https://github.com/PaddlePaddle/Paddle.js | 2026-09-07 | `B_comp_engine` | release or SKU of paddle | **N2** — name-match fold onto `paddle` withdrawn: `sources/model_families.yaml` declares no `paddle-*` family |
| `Playtime-AI/Minimax_H3-Sydney_Sweeney` | https://huggingface.co/Playtime-AI/Minimax_H3-Sydney_Sweeney | 2026-09-07 | `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `Playtime-AI` is not a handle declared for any organization owning `minimax`'s artifacts |
| `poloclub/llm-landscape` | https://github.com/poloclub/llm-landscape | 2026-09-07 | `B_safe_llmsafety` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `poloclub` is not a declared handle of `llm`'s organization |
| `Prachi-kushwaha/Triton-guide` | https://github.com/Prachi-kushwaha/Triton-guide | 2026-09-07 | `comp_t_cuda` | release or SKU of triton | **N3** — name-match fold onto `triton` withdrawn: no `triton-*` family declared, and owner `Prachi-kushwaha` is not a declared handle of `triton`'s organization |
| `princeton-nlp/Llama-3-8B-ProLong-64k-Base` | https://huggingface.co/princeton-nlp/Llama-3-8B-ProLong-64k-Base | 2026-09-07 | `hf_base_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `princeton-nlp` is not a handle declared for any organization owning `llama`'s artifacts |
| `prithivMLmods/MiniMax-H3-Facial-Realism-CloseUp` | https://huggingface.co/prithivMLmods/MiniMax-H3-Facial-Realism-CloseUp | 2026-09-07 | `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `prithivMLmods` is not a handle declared for any organization owning `minimax`'s artifacts |
| `project-free-llama/Llama-Prompt-Guard-2-86M` | https://huggingface.co/project-free-llama/Llama-Prompt-Guard-2-86M | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `project-free-llama` is not a handle declared for any organization owning `llama`'s artifacts |
| `QuantFactory/Llama-Guard-3-1B-GGUF` | https://huggingface.co/QuantFactory/Llama-Guard-3-1B-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `QuantFactory` is not a handle declared for any organization owning `llama`'s artifacts |
| `QuantFactory/Llama-Guard-3-8B-GGUF` | https://huggingface.co/QuantFactory/Llama-Guard-3-8B-GGUF | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `QuantFactory` is not a handle declared for any organization owning `llama`'s artifacts |
| `QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ` | https://huggingface.co/QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `QuantTrio` is not a handle declared for any organization owning `qwen`'s artifacts |
| `QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ` | https://huggingface.co/QuantTrio/Qwen3-VL-30B-A3B-Instruct-AWQ | 2026-09-07 | `hf_textgen_downloads`, `hf_instruct_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `QuantTrio` is not a handle declared for any organization owning `qwen`'s artifacts |
| `QUASAR-QAT/Qwen3.8-27B-QUASAR-NVFP4` | https://huggingface.co/QUASAR-QAT/Qwen3.8-27B-QUASAR-NVFP4 | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `QUASAR-QAT` is not a handle declared for any organization owning `qwen`'s artifacts |
| `RadixArk/Kimi-K3-DSpark` | https://huggingface.co/RadixArk/Kimi-K3-DSpark | 2026-09-07 | `hf_textgen_downloads` | release or SKU of kimi | **N1** — name-match fold onto `kimi` withdrawn: owner `RadixArk` is not a handle declared for any organization owning `kimi`'s artifacts |
| `RadixArk/Qwen3.8-27B-NVFP4` | https://huggingface.co/RadixArk/Qwen3.8-27B-NVFP4 | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `RadixArk` is not a handle declared for any organization owning `qwen`'s artifacts |
| `RedHatAI/Llama-3.2-1B-Instruct-FP8-dynamic` | https://huggingface.co/RedHatAI/Llama-3.2-1B-Instruct-FP8-dynamic | 2026-09-07 | `hf_instruct_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `RedHatAI` is not a handle declared for any organization owning `llama`'s artifacts |
| `RedHatAI/Llama-Guard-4-12B-quantized.w4a16` | https://huggingface.co/RedHatAI/Llama-Guard-4-12B-quantized.w4a16 | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `RedHatAI` is not a handle declared for any organization owning `llama`'s artifacts |
| `RightNow-AI/inkling-turbo` | https://github.com/RightNow-AI/inkling-turbo | 2026-09-07 | `comp_q_kernel` | release or SKU of inkling | **N3** — name-match fold onto `inkling` withdrawn: no `inkling-*` family declared, and owner `RightNow-AI` is not a declared handle of `inkling`'s organization |
| `rkinas/triton-resources` | https://github.com/rkinas/triton-resources | 2026-09-07 | `comp_t_triton` | release or SKU of triton | **N3** — name-match fold onto `triton` withdrawn: no `triton-*` family declared, and owner `rkinas` is not a declared handle of `triton`'s organization |
| `Ryn1998/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF` | https://huggingface.co/Ryn1998/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `Ryn1998` is not a handle declared for any organization owning `qwen`'s artifacts |
| `shouxieai/tensorRT_Pro` | https://github.com/shouxieai/tensorRT_Pro | 2026-09-07 | `B_comp_tensorrt` | release or SKU of tensorrt | **N3** — name-match fold onto `tensorrt` withdrawn: no `tensorrt-*` family declared, and owner `shouxieai` is not a declared handle of `tensorrt`'s organization |
| `SiriusNEO/Triton-Puzzles-Lite` | https://github.com/SiriusNEO/Triton-Puzzles-Lite | 2026-09-07 | `comp_t_triton` | release or SKU of triton | **N3** — name-match fold onto `triton` withdrawn: no `triton-*` family declared, and owner `SiriusNEO` is not a declared handle of `triton`'s organization |
| `smhfacct/Minimax-H3-fl2va-ref2va-hybrid-models` | https://huggingface.co/smhfacct/Minimax-H3-fl2va-ref2va-hybrid-models | 2026-09-07 | `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `smhfacct` is not a handle declared for any organization owning `minimax`'s artifacts |
| `solidrust/Mistral-7B-Instruct-v0.3-AWQ` | https://huggingface.co/solidrust/Mistral-7B-Instruct-v0.3-AWQ | 2026-09-07 | `hf_instruct_search` | release or SKU of mistral-7b-instruct | **N1** — name-match fold onto `mistral-7b-instruct` withdrawn: owner `solidrust` is not a handle declared for any organization owning `mistral-7b-instruct`'s artifacts |
| `speach1sdef178/MiniMax-H3-Semantic-Bridge` | https://huggingface.co/speach1sdef178/MiniMax-H3-Semantic-Bridge | 2026-09-07 | `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `speach1sdef178` is not a handle declared for any organization owning `minimax`'s artifacts |
| `stephenleo/llm-structured-output-benchmarks` | https://github.com/stephenleo/llm-structured-output-benchmarks | 2026-09-07 | `dpt_synth` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `stephenleo` is not a declared handle of `llm`'s organization |
| `susmitsingh01/triton-llm-kernels-lab` | https://github.com/susmitsingh01/triton-llm-kernels-lab | 2026-09-07 | `comp_q_kernel` | release or SKU of triton | **N3** — name-match fold onto `triton` withdrawn: no `triton-*` family declared, and owner `susmitsingh01` is not a declared handle of `triton`'s organization |
| `swiss-ai/Apertus-8B-Instruct-2509` | https://huggingface.co/swiss-ai/Apertus-8B-Instruct-2509 | 2026-09-07 | `hf_instruct_search` | release or SKU of apertus | **N2** — name-match fold onto `apertus` withdrawn: `sources/model_families.yaml` declares no `apertus-*` family |
| `ThakiCloud/Qwen3.8-27B-Human-KO-Safety` | https://huggingface.co/ThakiCloud/Qwen3.8-27B-Human-KO-Safety | 2026-09-07 | `hf_safety_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `ThakiCloud` is not a handle declared for any organization owning `qwen`'s artifacts |
| `theblackcat102/llama-3.2-1b-instruct-allenai_wildguard_safety` | https://huggingface.co/theblackcat102/llama-3.2-1b-instruct-allenai_wildguard_safety | 2026-09-07 | `hf_safety_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `theblackcat102` is not a handle declared for any organization owning `llama`'s artifacts |
| `Tianxiaomo/pytorch-YOLOv4` | https://github.com/Tianxiaomo/pytorch-YOLOv4 | 2026-09-07 | `comp_t_onnx`, `B_comp_tensorrt` | release or SKU of pytorch | **N3** — name-match fold onto `pytorch` withdrawn: no `pytorch-*` family declared, and owner `Tianxiaomo` is not a declared handle of `pytorch`'s organization |
| `tkarim45/llm-red-teaming-framework` | https://github.com/tkarim45/llm-red-teaming-framework | 2026-09-07 | `safe_q_jailbreak` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `tkarim45` is not a declared handle of `llm`'s organization |
| `umitkacar/onnx-tensorrt-optimization` | https://github.com/umitkacar/onnx-tensorrt-optimization | 2026-09-07 | `B_comp_modelopt` | release or SKU of onnx | **N3** — name-match fold onto `onnx` withdrawn: no `onnx-*` family declared, and owner `umitkacar` is not a declared handle of `onnx`'s organization |
| `unsloth/DeepSeek-R1-GGUF` | https://huggingface.co/unsloth/DeepSeek-R1-GGUF | 2026-09-07 | `hf_textgen_likes` | release or SKU of deepseek | **N1** — name-match fold onto `deepseek` withdrawn: owner `unsloth` is not a handle declared for any organization owning `deepseek`'s artifacts |
| `unsloth/DeepSeek-V4-Flash-Vision-Exp-GGUF` | https://huggingface.co/unsloth/DeepSeek-V4-Flash-Vision-Exp-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of deepseek | **N1** — name-match fold onto `deepseek` withdrawn: owner `unsloth` is not a handle declared for any organization owning `deepseek`'s artifacts |
| `unsloth/GLM-5.3-Flash-GGUF` | https://huggingface.co/unsloth/GLM-5.3-Flash-GGUF | 2026-09-07 | `hf_textgen_trending`, `hf_all_trending` | release or SKU of glm | **N1** — name-match fold onto `glm` withdrawn: owner `unsloth` is not a handle declared for any organization owning `glm`'s artifacts |
| `unsloth/Llama-3.2-1B-Instruct` | https://huggingface.co/unsloth/Llama-3.2-1B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `unsloth` is not a handle declared for any organization owning `llama`'s artifacts |
| `unsloth/Llama-3.2-3B-Instruct-GGUF` | https://huggingface.co/unsloth/Llama-3.2-3B-Instruct-GGUF | 2026-09-07 | `hf_instruct_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `unsloth` is not a handle declared for any organization owning `llama`'s artifacts |
| `unsloth/Qwen2.5-7B-Instruct` | https://huggingface.co/unsloth/Qwen2.5-7B-Instruct | 2026-09-07 | `hf_instruct_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3-0.6B-Base` | https://huggingface.co/unsloth/Qwen3-0.6B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3-1.7B-Base-unsloth-bnb-4bit` | https://huggingface.co/unsloth/Qwen3-1.7B-Base-unsloth-bnb-4bit | 2026-09-07 | `hf_base_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3-4B-Base` | https://huggingface.co/unsloth/Qwen3-4B-Base | 2026-09-07 | `hf_base_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3-4B-Base-unsloth-bnb-4bit` | https://huggingface.co/unsloth/Qwen3-4B-Base-unsloth-bnb-4bit | 2026-09-07 | `hf_base_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3-8B-Base-unsloth-bnb-4bit` | https://huggingface.co/unsloth/Qwen3-8B-Base-unsloth-bnb-4bit | 2026-09-07 | `hf_base_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` | https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF | 2026-09-07 | `hf_textgen_downloads`, `hf_textgen_trending`, `hf_all_downloads`, `hf_instruct_search`, `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3.5-9B-GGUF` | https://huggingface.co/unsloth/Qwen3.5-9B-GGUF | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3.6-27B-MTP-GGUF` | https://huggingface.co/unsloth/Qwen3.6-27B-MTP-GGUF | 2026-09-07 | `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3.6-27B-NVFP4` | https://huggingface.co/unsloth/Qwen3.6-27B-NVFP4 | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3.6-35B-A3B-GGUF` | https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF | 2026-09-07 | `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3.6-35B-A3B-NVFP4` | https://huggingface.co/unsloth/Qwen3.6-35B-A3B-NVFP4 | 2026-09-07 | `B_hf_conv_dl` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3.8-27B-GGUF` | https://huggingface.co/unsloth/Qwen3.8-27B-GGUF | 2026-09-07 | `hf_all_downloads`, `hf_all_trending`, `B_hf_conv_dl`, `B_hf_conv_likes` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `unsloth/Qwen3.8-Flash-Next-GGUF` | https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF | 2026-09-07 | `hf_all_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `unsloth` is not a handle declared for any organization owning `qwen`'s artifacts |
| `VerifiedAnon/gemma-moderation-finetune` | https://huggingface.co/VerifiedAnon/gemma-moderation-finetune | 2026-09-07 | `hf_moderation_search` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `VerifiedAnon` is not a handle declared for any organization owning `gemma`'s artifacts |
| `VitalyProtasov/Nemotron-3.5-Content-Safety-FP8-LLM-Compressor` | https://huggingface.co/VitalyProtasov/Nemotron-3.5-Content-Safety-FP8-LLM-Compressor | 2026-09-07 | `hf_safety_search` | release or SKU of nemotron | **N1** — name-match fold onto `nemotron` withdrawn: owner `VitalyProtasov` is not a handle declared for any organization owning `nemotron`'s artifacts |
| `vstorm-co/pydantic-ai-shields` | https://github.com/vstorm-co/pydantic-ai-shields | 2026-09-07 | `safe_t_moderation` | release or SKU of pydantic-ai | **N3** — name-match fold onto `pydantic-ai` withdrawn: no `pydantic-ai-*` family declared, and owner `vstorm-co` is not a declared handle of `pydantic-ai`'s organization |
| `WarmBloodAban/Minimax-h3_Singularity` | https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity | 2026-09-07 | `hf_all_trending` | release or SKU of minimax | **N1** — name-match fold onto `minimax` withdrawn: owner `WarmBloodAban` is not a handle declared for any organization owning `minimax`'s artifacts |
| `Weni/Llama-Guard-3-8B-AWQ` | https://huggingface.co/Weni/Llama-Guard-3-8B-AWQ | 2026-09-07 | `hf_guard_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `Weni` is not a handle declared for any organization owning `llama`'s artifacts |
| `wms2537/qwen3-0.6b-malaysia-moderation-cot` | https://huggingface.co/wms2537/qwen3-0.6b-malaysia-moderation-cot | 2026-09-07 | `hf_moderation_search` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `wms2537` is not a handle declared for any organization owning `qwen`'s artifacts |
| `www.axelera.ai/metis-aipu` | https://www.axelera.ai/metis-aipu | 2026-09-07 | — | head product axelera-metis-aipu | **N4** — fold onto `axelera-metis-aipu` withdrawn: it rests on the vendor domain plus a path segment. `sources/org_handles.yaml` declares no `homepage_domain` handle for the vendor and `axelera-metis-aipu` declares no `homepage` artifact |
| `www.hailo.ai/products/ai-accelerators/hailo-10h-m-2-generative-ai-acce` | https://www.hailo.ai/products/ai-accelerators/hailo-10h-m-2-generative-ai-acceleration-module/ | 2026-09-07 | — | head product hailo-10h | **N4** — fold onto `hailo-10h` withdrawn: it rests on the vendor domain plus a path segment. `sources/org_handles.yaml` declares no `homepage_domain` handle for the vendor and `hailo-10h` declares no `homepage` artifact |
| `xai-org/grok-1` | https://huggingface.co/xai-org/grok-1 | 2026-09-07 | `hf_textgen_likes` | release or SKU of grok | **N1** — name-match fold onto `grok` withdrawn: owner `xai-org` is not a handle declared for any organization owning `grok`'s artifacts |
| `XianghaoKong/llm-serving-systems-lab` | https://github.com/XianghaoKong/llm-serving-systems-lab | 2026-09-07 | `comp_q_kernel` | release or SKU of llm | **N3** — name-match fold onto `llm` withdrawn: no `llm-*` family declared, and owner `XianghaoKong` is not a declared handle of `llm`'s organization |
| `yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `yuxinlu1` is not a handle declared for any organization owning `gemma`'s artifacts |
| `yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF` | https://huggingface.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF | 2026-09-07 | `hf_textgen_likes`, `hf_textgen_trending`, `B_hf_conv_likes` | release or SKU of gemma | **N1** — name-match fold onto `gemma` withdrawn: owner `yuxinlu1` is not a handle declared for any organization owning `gemma`'s artifacts |
| `z-lab/Qwen3.8-27B-DFlash2` | https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2 | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `z-lab` is not a handle declared for any organization owning `qwen`'s artifacts |
| `z-lab/Qwen3.8-27B-DFlash2-GGUF` | https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `z-lab` is not a handle declared for any organization owning `qwen`'s artifacts |
| `ZaxbyHub/opencode-swarm` | https://github.com/ZaxbyHub/opencode-swarm | 2026-09-07 | `safe_t_guardrails` | release or SKU of opencode | **N3** — name-match fold onto `opencode` withdrawn: no `opencode-*` family declared, and owner `ZaxbyHub` is not a declared handle of `opencode`'s organization |
| `zerodigest/Qwen3.8-27B-Uncensored-YMQ-MTP-GGUF` | https://huggingface.co/zerodigest/Qwen3.8-27B-Uncensored-YMQ-MTP-GGUF | 2026-09-07 | `hf_textgen_trending` | release or SKU of qwen | **N1** — name-match fold onto `qwen` withdrawn: owner `zerodigest` is not a handle declared for any organization owning `qwen`'s artifacts |
| `ZiweiLiu96/llama-3.2-3b-Content-Moderation` | https://huggingface.co/ZiweiLiu96/llama-3.2-3b-Content-Moderation | 2026-09-07 | `hf_moderation_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `ZiweiLiu96` is not a handle declared for any organization owning `llama`'s artifacts |
| `ZiweiLiu96/llama-3.2-3b-Content-Moderation-Q4_K_M-GGUF` | https://huggingface.co/ZiweiLiu96/llama-3.2-3b-Content-Moderation-Q4_K_M-GGUF | 2026-09-07 | `hf_moderation_search` | release or SKU of llama | **N1** — name-match fold onto `llama` withdrawn: owner `ZiweiLiu96` is not a handle declared for any organization owning `llama`'s artifacts |

## Escalations for a person

1. **Checkpoint-level identity is what this batch can observe; product-line identity is an
   editorial act.** `roberta-base` and `roberta-large`, `t5-small` and `t5-base`, `gpt2` and
   `gpt2-large`, three `bert-base-*` variants and both `deberta-v3-*` sizes are proposed as
   separate rows. A promoter will want one product each, which means a `model_families.yaml`
   pattern or a `version_in_identity` declaration — `build/validate.py` rejects a version or size
   token in a *head* `base_pretrained` slug without one. The sweep cannot make that call and no
   longer pretends to: ADR-004 point 4 puts it on the person, and this is what that costs.
2. **The taxonomy has no category for six large, heavily used model populations.** Text embedding
   and reranking models (led by `sentence-transformers/all-MiniLM-L6-v2` at 251M trailing-30-day
   downloads — more than any model on the map), speech and audio models, vision and
   vision-language backbones, generative image and video models, time-series forecasters, and now
   protein / biological-sequence language models (`biohub/ESMC-6B` at 2.4M downloads,
   `facebook/esm2_*`). All are parked above against a `category-proposal` issue. This is the
   largest coverage gap the sweep found, and taxonomy is a governance event: this workflow does
   not open it.
3. **No category holds datacenter or workstation accelerators.** Tenstorrent's Blackhole cards are
   parked for this reason; `edge_hardware` is explicitly about the edge.
4. **Hardware has no non-URL identifier, anywhere.** All 28 board-level candidates are parked for
   it. Either the registry needs an identifier kind a board can carry, or `edge_hardware` stays a
   head-only category. A sweep cannot settle that.
5. **Two boundaries this batch drew to park things, which a person should confirm or move.**
   Inside `dataset_processing_tools`, a document tool whose declared description names a human
   workflow (scan, archive, manage, search, view, edit, translate) is parked and one that names
   data prepared for a model is emitted — that line parks `ocrmypdf`, `paperless-ngx`,
   `papermerge` and eleven more, and admits `unstructured`, `Parsr`, `pdf-craft` and `ade-cli`.
   Inside `safeguards`, offensive-security and security-operations tooling that *uses* an LLM is
   parked, and only a safeguard applied *to* an AI system's inputs, outputs or actions is emitted
   — that line parks 20 candidates including `openai/codex-security`. Both lines are the ones the
   existing rosters already draw, but they are the sweep's reading of them.
6. **An unresolved text-versus-vision boundary in `dataset_processing_tools`.** BlenderProc,
   fastdup and fiftyone are in scope by the letter of the category but every product on the roster
   builds text or document corpora. Parked pending a boundary ruling. `microsoft/presidio` is the
   same shape on the `safeguards` side.
7. **Two ledger holds re-surfaced and were not re-proposed:** `RyanCodrai/turbovec` and
   `FailproofAI/failproofai` both carry `unresolved` product_equivalence rulings in
   `sources/resolution_ledger.yaml`.
8. **Two open boundary questions in `compilers`:** `EnzymeAD/Enzyme` (automatic-differentiation
   compiler pass) and `llvm/circt` (hardware-EDA compiler).
9. **The warehouse discovery pool was unreachable** (no `OSO_API_KEY`). Re-running with warehouse
   access would likely consolidate signals this sweep treated as separate.
10. **One test in `tests/test_identity_eval.py` now encodes a corpus size this batch outgrew.**
    `test_a_stale_fixture_tail_row_fails_the_floor_with_the_publish_lag_note` mutates one row of a
    27-row truth set and expects the 0.98 precision floor to catch it; the tail homepage truth set
    is 50 rows now, so a single mutation lands exactly on the floor. The fix is a one-line change
    in `tests/`, out of scope for a `tail-batch` diff, and the in-scope alternative — dropping 24
    declared homepages — would suppress observed evidence to satisfy a test. Someone has to make
    that change on `main`.
11. **Seven model families this sweep saw releases of are not declared in
   `sources/model_families.yaml`.** 37 signals are first-party releases — the owner login *is* a
   declared handle of the organization owning the head product's artifacts — folded onto that
   product on the checkpoint name alone, with no `<product>-*` family to bridge them. The
   families are `granite-*` and `granite-guardian-*` (`ibm-granite`, 27 signals), `smollm-*`
   (`HuggingFaceTB`, 5), `minicpm-*` (`openbmb`, 2), and one each for `pythia-*` (`EleutherAI`),
   `zephyr-*` (`HuggingFaceH4`) and `apertus-*` (`swiss-ai`). Declaring a family bridge is an
   editorial act recorded on `main`, not something a `tail-batch` diff may write, so all 37 are
   parked as class N2 and come back folded once the bridges exist. Two more shapes want the same
   treatment and are not families: `firecrawl/firecrawl-app-examples` and `PaddlePaddle/Paddle.js`
   are first-party sibling repositories, and whether a sibling repo is a SKU of the product or its
   own product is a question the sweep cannot settle.

12. **181 third-party derivatives need a base-model declaration, or a `base_model` read.** GGUF
   quantizations, abliterations, uncensored merges and fine-tunes whose names carry a declared
   family token but whose owner is not the family's organization. They are almost certainly not
   new products; nothing in this repo says what they *are* derivatives of, and this pass did not
   read Hugging Face's own `base_model` field. Either the sweep starts reading `base_model` and
   folds on it, or a person rules on them. Three of the 181 have the exact shape the declared
   format-redistribution predicate covers
   (`ibm-granite/granite-guardian-3.3-8b-GGUF`, `ibm-granite/granite-guardian-4.1-8b-GGUF`,
   `janhq/Jan-v3-4B-base-instruct-gguf`) but the predicate needs the repo's own `tags`, which this
   pass did not read for them; asserting the tag unread would be the same error in a new place.

13. **55 of the 67 rows name an organization with no record in
   `sources/organizations/`** (45 distinct org slugs) — `answerdotai`,
   `bespokelabsai`, `facebookai`, `emilyalsentzer` and
   the rest. On 59 of the 67 rows the owner login is not a declared handle for
   any organization, which is exactly why `org` is now the slugified login rather than a name the
   sweep chose. Declared handles belong in `sources/org_handles.yaml` on `main`, which is also
   what repairs the coverage baseline named under **Gates**.

## Gates

All three re-run at the fourth revision. The registry files are byte-identical to the third
revision — the correction moved 300 signals between tables in this sheet and emitted no row — so
`validate`, `check_corpus_diff` and the test suite return exactly what they did then, and the
identity-eval failure count is unchanged rather than merely assumed unchanged.

- **The reconciliation is recounted from the tables, not carried forward.** Reading the four
  tables in this file back: 739 duplicate rows, and 288 + 1185 + 300 = 1773 parked rows against 67
  emitted rows. `739 + (67 + 1773) = 2579` = `raw_signals`, and `67 + 1773 = 1840` =
  `unique_candidates`. The fold-class tally inside the duplicate table also reconciles against
  **What a fold has to rest on**: 463 repeats + 88 declared artifacts + 7 ledger entries + 175
  declared first-party family releases + 1 declared-tag redistribution + 5 retried hardware paths
  = 739.

- `uv run python -m build.validate` → `0 error(s), 2 warning(s)` (both warnings pre-existing
  `model_families` pattern-overlap notices, byte-identical on `main`).
- `uv run python -m build.check_corpus_diff --base main` → no stage, gap, product-count or tier
  move in any category, and no untouched axis-assessment row rewritten. Registry rows are
  signal-only and invisible to the scored payload, which is why the sheet is empty; that is the
  expected result for a `tail-batch` PR and the reason no `stage-move` label is needed.

  ```
  ## Review sheet

  | category | stage | gaps | products | tier changes |
  |---|---|---|---|---|

  stage moves: none

  untouched-product row changes: none
  ```

- `uv run pytest -q` → **6 failed, 1827 passed, 1 skipped in 657s**; `pytest tests/test_identity_eval.py -q` re-run at this revision → **6 failed, 131 passed**, the same six. All six failures are in
  `tests/test_identity_eval.py` (6 failed, 131 passed when that file is run alone); all 137 of
  its tests pass on `main`, verified in a scratch worktree at 9df82a12, so the batch causes them
  and they are not pre-existing. Five repair only by editing a corpus-wide generated fixture:

  | test | what it wants edited |
  |---|---|
  | `test_the_pass_fixture_tail_rows_match_the_corpus` | `tests/fixtures/identity_edges_pass.json` |
  | `test_write_fixture_is_idempotent` | `tests/fixtures/identity_edges_pass.json` |
  | `test_fixture_mode_does_not_grade_the_invariant` | `tests/fixtures/identity_edges_pass.json` |
  | `test_main_prints_a_coverage_line_per_route` | `tests/fixtures/identity_coverage_baseline.json` |
  | `test_the_live_corpus_is_at_or_above_the_committed_baseline` | `tests/fixtures/identity_coverage_baseline.json` |

  Their cause is one thing, not five: the 67 new tail rows add artifacts whose organizations declare no handle in `sources/org_handles.yaml`, so the coverage *denominators* grow while the numerators hold or rise — `github` 211/299 → 211/328, `huggingface` 51/62 → 51/81, `homepage_domain` 6/27 → 7/50. Nothing lost a handle; the corpus got bigger, and one new row's homepage domain actually matched a declared handle.

  Under [ADR-004](../architecture/adr-004-machine-proposals-and-the-public-tail.md#decision) point
  3, a gate whose only repair is a corpus-wide fixture edit does not block a proposal PR:
  "identity membership fixtures and committed coverage baselines" are named there, and they bind
  on `main`, where the fixtures are regenerated, not on a batch that is forbidden to touch them.
  Neither fixture was regenerated here and no `org_handles.yaml` entry was added. A reviewer
  records these failures and merges on the sheet; the right follow-up is declared handles for the
  new organizations, on `main`, in its own commit.

- **The sixth failure is a different animal and is reported as such:**
  `test_a_stale_fixture_tail_row_fails_the_floor_with_the_publish_lag_note`. It is a mutation test
  over the harness: it corrupts one `homepage` row in a fixture built from the live corpus and
  asserts that the 0.98 precision floor catches it. Its arithmetic assumes the truth set is about
  27 rows, where one bad row is a 3.7% error. This batch declares a `homepage` on 24 rows that
  also carry an identifier, so the tail homepage truth set is 50 rows, one bad row is a 2.0% error,
  precision lands exactly at the 0.98 floor, and the mutation no longer trips it. Nothing about the
  identity graph regressed — the floor got more headroom, which is the direction the test's own
  docstring calls "no headroom by construction".

  Its repair is not a fixture edit: it is a one-line change to the test, so that the mutation
  scales with the truth-set size instead of assuming 27 rows. That change lives in `tests/`, which
  this batch is not allowed to touch — the diff scope for a `tail-batch` PR is
  `sources/registry/**` plus this file. The alternative repair inside the batch would be to drop
  the 24 declared homepages, and that is worse: `discover-candidates` says to write every artifact
  there is evidence for, and suppressing observed evidence to make a test's arithmetic work is not
  a thing a sweep should do. Escalated rather than worked around; see **Escalations for a person**.

- Diff touches `sources/registry/**` and this file only. No product, score, category-roster,
  taxonomy, org-handle or fixture file, and neither generated artifact.

## Revisions

| revision | correction | what it changed |
|---|---|---|
| 2 | Every emitted row needs an identifier that is not a URL | The 15 homepage-only `edge_hardware` rows were parked with their pages and fetch dates; `sources/registry/edge_hardware.yaml` is not created. |
| 2 | Mirrors are duplicates, not unique candidates | Seven signals whose recorded reason already acknowledged a fold moved to the duplicate side; all five counts were recomputed rather than adjusted. |
| 2 | Parked candidates need candidate-level provenance | Every parked candidate and every duplicate is listed individually with identifier, source URL, fetch date, the queries that returned it and its reason. |
| 3 | No emitted field may be an LLM-authored identity assignment | Every field is now produced by the derivation table above. The hand-made organization mappings (`answerdotai` → `answer-ai`, `bespokelabsai` → `bespoke-labs`, `google-bert` → `google`, `facebookai` → `meta`, and ten more; `data-prep-kit` → `ibm` went with its row) are gone: `org` is the declared handle or the slugified login. The three hand-made product-family folds are un-folded and each checkpoint is emitted at its declared identity. |
| 3 | Recognition is not an acceptance predicate | The nine sub-floor exceptions are parked with the floor that excluded them. Acceptance is the predicate in **How a candidate becomes a row**, whose only judgment-shaped clause can remove a candidate and never admit one. |
| 3 | Replenish through another documented retrieval pass | 16 more queries at the same cutoffs, predeclared in a manifest before the first request; 2579 raw signals, 67 rows across five categories. One manifest floor was corrected upward to match the first pass's convention for the same query shape, and the correction is disclosed above. |
| 4 | A fold has to rest on a declaration, not on a name match | Every fold re-audited against `sources/products/`, `sources/registry/`, `sources/model_families.yaml`, `sources/org_handles.yaml` and `sources/resolution_ledger.yaml`. 300 folds withdrawn — 286 name matches, 2 domain-and-path matches, 12 stated readings — and each un-folded signal is held in **Parked — a withdrawn fold** with its provenance and the reason. 739 duplicates remain, each naming the declaration behind it. |
| 4 | All five counts recomputed, not adjusted | `duplicate_signals` 1039 → 739, `unique_candidates` 1540 → 1840, `parked` 1473 → 1773. `raw_signals` 2579 and `accepted` 67 unchanged: a withdrawn fold moves a signal between the two sides of the first equation and always lands on the parked side of the second. |
| 4 | Seven mirror and derivative folds settled by reading, not observing | The mirrors-and-derivatives table drops to one row, the format redistribution whose predicate is mechanical and whose format tag was read. The other seven — two `chronos` mirrors, a Core ML conversion, an abliterated GGUF, a component model, a web UI and a plugin surface — are un-folded as class N5. |

