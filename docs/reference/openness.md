# Openness Spectrum Guide

How openness is scored, why the raw score isn't comparable across categories, and
which field to use when you want to place a product on an openness spectrum.

> This is the data-consumer / query reference. For the reader-facing methodology
> narrative published in the notebook, see [`docs/methodology.md`](../methodology.md).
> Keep the two consistent when the openness model changes.

## TL;DR

- **`openness.class` is the cross-category normalizer.** Use it to position a product
  on a spectrum.
- **`openness.score` (0–5) is NOT comparable across categories.** It's a within-type
  grade. Treat it as a detail, not a spectrum coordinate.
- A machine-readable mapping lives in [`docs/openness-class-map.json`](../openness-class-map.json).
  It is derived from `build/render.py` (the published notebook), so reusing it keeps any
  new visualization consistent with the live map.

## The two openness fields

Each `sources/scores/<slug>.yaml` carries two separate, analyst-assigned openness fields:

| Field | Type | What it is |
|-------|------|------------|
| `openness.class` | categorical | An OSI / Model Openness Framework (MOF) label. In use today, by frequency: `open_source`, `closed`, `open`, `open_weights`, `open_core`, `source_available`, `documented`, `gated`, `restricted`, `open_toolchain`, `open_hardware`. [`openness-class-map.json`](../openness-class-map.json) is the authoritative list. |
| `openness.score` | integer 0–5 | A graded openness score with a `components` breakdown (models: `weights / data / code / checkpoints / license`; software: OSI-class license tests; datasets: access / license / documentation). |

Every non-null value needs a primary `sources:` entry. Both fields were originally assigned
by hand against MOF/OSI, and that history is why `components`/`note` read as editorial prose.

**A deterministic formula now exists for most of the map.** All 18 categories declare a
`scoring_recipe` that names an ordered rule list over dimension values, and
`build/check_rubric.py` replays it against each product's recorded `components` to check that
the recorded score is the one the rules produce. Most recipes `extend` a shared ladder in
[`sources/rubrics/`](../../sources/rubrics/) rather than restating one: `software.yaml` covers
twelve categories directly plus the software half of `safeguards`, `model.yaml` the fine-tuned and guardrail models. A category holding more
than one kind of product maps `extends` per product type.

Three caveats, because "a formula exists" is easy to over-read:

- **A recipe covers a category, not every product in it.** Every category has carried one since
  2026-08-01, including compilers and storage, which arrived with theirs on 2026-08-18, and a small number of products are declared in a `deferred:` block, meaning the
  category has said the ladder does not decide them. Those scores remain editorial.
  `check_recipe` prints the per-category split and fails if a product abstains without being
  declared — read its output for the current figure rather than trusting a number typed here.
- **A recipe reproducing a score does not validate it.** It shows the rules describe how the
  category was scored. The document-grade evidence the checker reads was parsed out of the
  same files the scores live in, so agreement is a fidelity check on the formula, not on the
  facts.
- **A category can hold products back.** `scoring_recipe.deferred` lists products the rules do
  not decide, usually because a dimension is not recorded in a form the ladder can read. As of
  2026-08-18 there are 5 such products across 4 categories (`benchmark_eval_data` 2, and
  `dataset_processing_tools`, `edge_hardware` and `training_synthetic_datasets` 1 each). The
  compilers and storage promotions each added one and then closed it the same day: `liger-kernel`
  and `pgvector` recorded `BSD-2-Clause` and the PostgreSQL License, which the shared `osi` tier
  covers by definition and had never been asked to name. Down
  from 81 before the August verification sweep. Deferred products publish no openness evidence
  to the warehouse. `uv run python -m build.check_recipe` prints the live split.

So openness is part computed and part editorial, and which one you are looking at depends on
the category and the product. `docs/reference/evidence-and-freshness.md` tracks the work to close that gap.

## Why the raw score is not comparable across categories

The 0–5 score is graded relative to what's achievable *within a product type*, so the same
number means different things in different categories. A quick cross-tab of `score | class`
across all score files shows the overlap:

| score | classes that appear at this score |
|-------|-----------------------------------|
| 5 | `open_source`, `open`, `open_hardware` |
| 4 | `open_core`, `open_weights`, `open`, `open_toolchain` |
| 3 | `open_weights`, `open`, `documented`, `gated` |
| 2 | `restricted`, `source_available`, `gated` |
| 1 | `closed` |
| 0 | `closed` |

Regenerated 2026-08-14. The overlap is narrower than it was: the producible-pair check added in
#128 found 17 pairs no rule in any recipe could emit, and correcting them is why `open_core` and
`source_available` no longer appear at 3 and `open_core` no longer appears at 2. If you are
reading this table long after that date, regenerate it rather than trusting it — the check is
a few lines over `sources/scores/*.yaml`.

A pretrained model at **2** is genuinely restricted/gated, because the model gradient is
compressed (open weights typically land around 3, and you only reach 5 with a fully open
pipeline like Pythia or OLMo). A deployment tool at **2** sits somewhere else entirely.
**Don't compare the numbers directly across categories.**

## The normalization (use this for a spectrum)

`build/render.py` already collapses the model / software / dataset class vocabularies onto
one gradient and into a three-bucket verdict. Both are captured in
[`openness-class-map.json`](../openness-class-map.json).

**Class → 0–5 gradient** (`OPEN` dict in `render.py`) — the normalized, cross-category
spectrum coordinate:

| class | label | gradient |
|-------|-------|----------|
| `open_source` | Open source | 5 |
| `open` | Open data | 5 |
| `open_core` | Open core | 4 |
| `open_weights` | Open weights | 3 |
| `source_available` | Source available | 2 |
| `restricted` | Restricted | 2 |
| `gated` | Gated | 2 |
| `closed` | Closed | 1 |
| `open_hardware` | Open hardware | 5 |
| `open_toolchain` | Open toolchain | 3 |
| `documented` | Documented | 2 |

The last three are the **hardware** openness vocabulary (product `type: hardware`):
open schematics + toolchain = `open_hardware`; proprietary silicon but open SDK/datasheets +
retail-available = `open_toolchain`; datasheets public but proprietary design / firmware blobs =
`documented`; NDA/private-sale = `restricted` (shared with the model vocabulary).

**Class → three-bucket verdict** (`vbucket()` in `render.py`) — the coarse spectrum:

- **open** = `open_source` / `open` / `open_core` / `open_hardware`
- **open-ish** = `open_weights` / `source_available` / `gated` / `open_toolchain`
- **closed** = `restricted` / `closed` / `documented`

## The license scale

One scale across every product type. It is a **cap on the score, not the score**: the license
sets the ceiling, and the artifact dimensions decide where below it a product lands. Every
ladder checks `weights: closed` or `source: closed` before any license rung, so an OSI license
on something nobody can run is still a 1.

| cap | test | tier names |
|---|---|---|
| **5** | OSI-approved, or open by the Open Definition for data | `osi`, `open_data` |
| **4** | not OSI-approved, but no cap on who may use it or at what scale — attribution, naming, conduct | `permissive_non_osi` |
| **3** | commercial use permitted but bounded — a MAU ceiling, a revenue ceiling, an acceptable-use policy | `use_bounded` |
| **2** | commercial use prohibited or reserved to the vendor, though source or weights are published | `commercial_forbidden`, `competition_restricted`, `noncommercial` |
| **1** | nothing published to license | `proprietary`, `unstated` |

**The 3/2 boundary asks one question: does the license permit commercial use at all?** That is
what separates Meta's 700M-MAU clause and AI21's $50M-revenue clause — which bind almost
nobody — from CC-BY-NC and Mistral's Non-Production License, which bind everyone. It is also
where MOF draws its own line: Class III, its entry point, requires components usable
"including for commercial and educational purposes".

The tier names still differ per ladder, because a corpus and a codebase carry different
license families. The **caps** are what is universal.

### What it changed, and why it was needed

Before the scale, the same license family was scored two ways. `Llama-3.1-Community` was
`3/open_weights` on `llama-guard` in `safeguards` and `2/restricted` on `llama-instruct` in
`finetuned_chat`. `CC-BY-NC` capped `command-r` at 2 while `CC-BY-NC-SA` left `personahub` at
5. Ten products carry a bounded commercial license; six were recorded 2 and four were recorded
3.

Applying the scale on 2026-08-01 moved seven scores: six from `2/restricted` to
`3/open_weights` (`llama`, `codellama`, `llama-instruct`, `tulu`, `jamba-large`, `codegemma`)
and `personahub` from `5/open` to `2/restricted`. Four products deferred in `safeguards`
resolved without being touched, because they were already recorded where the scale puts them.

Two things worth knowing about the shape of it:

- **A full open recipe does not lift a capped license.** `tulu` releases its post-training
  data, code and RLVR recipe under Apache-2.0 and still scores 3, because the license rung
  fires ahead of the data and code rungs. The recipe is credited where it lives —
  `tulu-3-sft-mixture` is 5/open in `training_synthetic_datasets`, and the same recipe produces
  `olmo-3-instruct` at 5/open_source on an open base.
- **`restricted` joined the dataset class vocabulary** for this. Datasets were the only product
  type with no word between `open` and `gated`, which is exactly how a non-commercial corpus
  came to sit in the `open` bucket.

### A compound license resolves on all of its parts

Plenty of products ship under more than one license at once — Apache-2.0 code beside a
custom weights license, an OSI core beside a paid enterprise tier, an Apache-2.0 recipe
assembling tasks that keep their own terms. Those are recorded on one line, joined by `+`:

```
license:Apache-2.0(code, OSI) + custom weights license(non-OSI, application step)
```

**Every part resolves, and the most restrictive one governs the cap.** This is the same rule
`docs/reference/identity.md` states for a tier that ships several SKUs, applied within a single
recorded value: a product is as open as the most restrictive license you have to accept.

Two properties of it are load-bearing:

- **A part that maps to no tier makes the whole value abstain.** It is not skipped. An
  unmapped part can only turn out to be more restrictive than the tier the mapped parts
  reached, so skipping it publishes an overstatement, and abstaining is the signal to
  extend the rubric — the same thing an unmapped single license already does.
- **A `+` inside a parenthetical is not a separator**, and neither is a comma. Every
  depth-zero comma in the corpus trails prose after one license (`Proprietary, proprietary
  service`), so only `+` at paren depth zero joins two licenses.

A recipe may still declare a compound as a single tier example, but only where the `+` is
not joining licenses: `follows mC4 + OSCAR-2301 terms` names two corpora in a sentence, and
there is nothing in it to decompose. A compound whose operands *are* license names does not
belong in an `examples` list — that is a per-product override, and the operands belong there
individually instead.

Until 2026-08-11 resolution truncated the recorded value at its first `(` or `,` and so read
only the first license. `internlm` resolved as `osi` on its Apache-2.0 code while the
application-gated weights license that actually governs the download was never read;
`smoltalk` and `flan-collection` both resolved as clean Apache-2.0 while the half saying the
assembled components keep their own terms went unseen. Reading the whole value moved one
published score — `flan-collection` from 4 to 3 — and left the other two where the analysts
had already put them by hand.

### `self-host` and `core-gated` are one question

The software ladder asks whether functionality is withheld from the published source for a
paid tier, and records the answer under `core-gated` with values `gated` and `ungated`. The
corpus also answered that question 54 times under `self-host`, in a vocabulary of its own:
`yes`, `primary`, `only` on one side and `no`, `none`, `enterprise-only`, `enterprise-tier`
on the other. Whether a vendor lets you run the published thing yourself *is* whether the
core is withheld, so these were never two facts.

Twenty-three records carry both keys, and they never disagree — 11 `yes`/`ungated`, 10
`primary`/`ungated`, 2 `only`/`ungated`, and no contradictions in either direction. That
agreement is what licenses the merge. Until 2026-08-11 `self-host` was an undeclared key,
which meant it was dropped before the formula ran, and the 31 records that used it *instead*
of `core-gated` left the dimension unanswered.

Two mechanisms carry it, and they do different jobs:

- **`reads:`** widens which recorded KEY answers a dimension. `core_gated` now reads
  `[core-gated, self-host]`, first key whose value lands in the enum winning.
- **`value_aliases:`** widens which recorded VALUE does. `reads:` selects a key and takes its
  value verbatim, so a synonym key with its own vocabulary still reads as unanswered without
  a translation table. `dataset.yaml`'s `availability` handles the same problem the other way
  round, by declaring every spelling as its own value and writing rules that test only one
  polarity — which works there because the other polarity falls through to the license rungs.
  `core_gated` has a rung on both sides, so nothing falls through and the spellings have to
  collapse onto the two declared values.

A spelling with no entry in `value_aliases` is not guessed at. It stays outside the enum, the
dimension reads as unanswered, and the formula abstains, which is the same treatment an
unmapped license part gets and for the same reason: the software ladder declares no
`otherwise`, so abstaining is what the ladder does with evidence it does not understand.

The merge is conservative by construction, and the numbers say so. Of the 31 records whose
answer changed, 28 kept the score they had: 26 of those are hosted products recording
`source: closed`, where the first rung fires on `source` alone and `core_gated` is never
read, and the software ladder already says the dimension is "only meaningful where `source`
is public". This is the case worth being careful about — a hosted service has no core to gate
— and rule ordering already neutralizes it. The remaining three had been deferred with the
same sentence, that core-gated is not recorded in a form the ladder can read, while recording
it under `self-host` all along. Two of them, `syfthub` and `thunderbolt`, reproduce their
recorded 5/open_source exactly. One published score moved: `otari` from 4/open_core to
5/open_source.

### Selling something is not gating a core

This is the distinction between 4/`open_core` and 5/`open_source`, and it is the one that gets
scored wrongly most often.

`core_gated` asks whether functionality is withheld **from the published source**. It does not
ask whether the vendor makes money. A separate hosted product, a managed service, or a different
SaaS built around an otherwise complete open core does not gate that core, however much it
costs. A `commercial:` or `service:` clause is therefore not evidence either way, and the ladder
reads neither key — where that is all a product records, the dimension is unanswered and the
formula abstains.

What gates a core is a piece of the product *itself* being withheld: a closed package the open
one depends on, an enterprise or `ee/` directory under a different license, a license key that
unlocks functionality.

`langgraph` and `langchain` are the pair to hold onto, because from outside they are the same
picture — one vendor, one paid platform — and they score differently:

| Product | Reading | Why |
|---|---|---|
| `langgraph` | `gated`, 4/open_core | The Agent Server ships as a closed Elastic-2.0 `langgraph-api` package that exists in no public repo, and self-hosting it needs `LANGGRAPH_CLOUD_LICENSE_KEY`. |
| `langchain` | `ungated`, 5/open_source | Every package in the repo is MIT with no enterprise directory; LangSmith is a separate observability and deployment platform sold beside it. |

`llama-index` (LlamaParse), `pydantic-ai` (Logfire), `zed` (Zed-hosted inference) and `otari`
(the hosted Otari.ai platform) are all the `langchain` shape and all sit at 5. `litellm` is on
the other side with `langgraph`: its 4 rests on an `enterprise-dir` inside its own repo, not on
the hosted product beside it.

All five of the ungated cases had recorded 4/open_core on a `commercial:` clause — on the vendor
selling something at all. `otari` was corrected on 2026-08-11 and the other four followed the
same day. They were found only because a sweep happened to read `otari`'s record and infer the
precedent, which is why the rule is now stated here and in `sources/rubrics/software.yaml`
rather than left to be rediscovered.

One caveat for anyone applying it: not every `core-gated: gated` in the corpus was recorded
against this test. Twenty-two products reach the gated rung, and a number of them record their
gate as a managed cloud "on top" of a complete OSI core — the shape this section says is
*ungated* — with no withheld component named. Those predate the rule and have not been re-read.
A `gated` value is not evidence that somebody applied this rule; check what the record says is
actually withheld.

### A product is scored on the artifact it ships, not on what it can load

A harness that runs against a model you supply is scored on the harness. The model it happens to
be shipped alongside is a different product with its own score, and scoring the harness down for
it would count the same license twice.

`llamafirewall` is the case the rule was settled on (2026-08-12). It is an MIT firewall that
inspects prompts and code and calls out to whatever guard model you point it at; the PurpleLlama
monorepo ships it next to Prompt Guard 2 and Llama Guard, which carry the use-restricted Llama
Community License. The repository makes the split explicit — the root `LICENSE` is the Llama 3.2
Community License and `LlamaFirewall/LICENSE` is plain MIT — and both guard models are separately
scored on this map at 3/open_weights. So the restrictive terms are not being overlooked; they are
recorded against the artifact they actually govern. `llamafirewall` is 5/open_source.

`openai-evals` was already resolved this way before the rule was written: it records
`license: MIT`, `source: public(full framework + registry)` and
`per-dataset-licenses: mixed(CC/CC0/Apache for bundled data)`, and scores 5 on the framework.
Those two are the only bundles of this shape in the corpus today.

The rule does have an edge, and it is worth stating so nobody stretches it. It applies where the
bundled artifact is *substitutable* — you can point LlamaFirewall at a different model and it
still works. Where the published thing genuinely cannot run without the restricted component, the
component is not a bundle but a dependency, and `core_gated` is the dimension that asks about it.

### An accessory tracks the platform it completes

An add-on is not a board, and asking board questions of one answers about the wrong artifact.
What a builder gets from a HAT or a carrier is the openness of the system it completes.

`raspberry-pi-ai-hat-plus` is the case (2026-08-12). It publishes a HAT+ mechanical specification
rather than board design files, and its toolchain is half open — the Pi driver integration is
open, Hailo's Dataflow Compiler is registration-gated. Both of its own answers are `partial` and
neither describes the system anyone runs. It plugs into a `raspberry-pi-5`, and takes that board's
score.

This is recorded as an `accessory_host` dimension in `sources/rubrics/hardware.yaml` rather than
as an extra rung. The rung version — `{schematics: partial, toolchain: partial}` → 4 — would have
reproduced the number the HAT then held and been non-monotonic: `ti-am67a` and
`qualcomm-dragonwing-rb3-gen-2` both record `{partial, open}` and score 3, so it would have ranked
strictly weaker evidence strictly higher. One product records `accessory-host` today; the next
accessory records its host rather than needing another rung.

The dimension earned itself on 2026-08-14, sooner than expected. `raspberry-pi-5` was corrected
from 4 to 3 — it publishes a mechanical drawing and two STEP files and no schematic of the board,
where the record had claimed reduced schematics, which is a Pi 4 document — and the HAT followed
it to 3/documented without any new evidence about the HAT. A frozen number would have left the
accessory reading more open than the system it completes. That is why `accessory_host` now has a
rung for each host class the corpus has seen, `open_toolchain` and `documented`, and none for
`open_hardware`, which no accessory has met.

### The toolchain gates the ceiling, the design sets it

Hardware's level 4 is a claim about the toolchain — `open_toolchain` is the class name — so a
board whose model compiler is closed or registration-gated does not reach it however much of the
design it publishes. `google-coral-dev-board` is the case: the baseboard schematic, its Altium
source and the Allegro layout are all public in an Apache-2.0 repository, and the Edge TPU
compiler is a closed binary, so it sits at 3/documented, which the category's own ladder defines
to include a closed or registration-gated SDK. It stops short of the top schematics value for a
second reason worth stating: only the baseboard is covered, and the SoM that carries the SoC and
the Edge TPU has no design files. Publishing a reusable design for half a two-part product is
`published`, not `open` — the same reasoning that makes a partly-mapped SKU set abstain elsewhere
in the corpus.

## How the buckets relate to MOF and OSAID

The Model Openness Framework and the OSI's Open Source AI Definition are both **binary**.
MOF says so directly: openness "has always been a binary decision in the open-source
movement", and it warns the reader not to read its Class I/II/III as a gradient — those
classes measure how *complete* a release is, once it has already passed the license test.
OSAID requires the freedom to use a system "for any purpose", so a field-of-use or commercial
restriction disqualifies. Under MOF, a release under OpenRAIL, a Llama community license or
AI2 ImpACT is *source-available*, not open.

This map is a 0–5 score, which is a different instrument. The 2024 Columbia Convening
catalogs three families of approach — gradient, score, and binary — and adopts none; the
score family is the one the map belongs to.

The two stay compatible through one rule:

> **The `open` bucket requires a license that is open by an external standard** — OSI
> approval for code and weights, the Open Definition for data. The score may subdivide the
> region below that line as finely as it likes, and nothing below it enters the `open`
> bucket.

So MOF's binary line sits between the `open` bucket and the `open-ish` bucket, exactly where
MOF puts it, and our 4/3/2/1 subdivide what MOF treats as one undifferentiated
"source-available" bucket. `render.py` calls this the "strict OSI/MOF cut".
`tests/test_openness_buckets.py` enforces it against every ladder, and it is a live check
rather than a comment: `software.yaml` carried two rungs emitting `open_core` and
`open_source` from its `permissive_non_osi` tier, and they went unnoticed because that tier's
`examples` list is empty so the rungs could never fire.

### Two places the map deliberately departs from MOF

Both are choices, not oversights, and neither moves the binary line.

- **We are stricter than MOF Class III.** Class III is MOF's entry point and needs
  architecture, final weights, and light documentation including a *data card* — not the
  data. So an Apache-2.0 open-weights model with a good card and closed training data is
  fully open under MOF and scores **3/`open_weights`** here. Do not read our 5 as Class I or
  our 3 as failing MOF. We are tighter than Class III on training data and looser than
  Class I, which additionally wants the research paper, intermediate checkpoints and
  training logs — none of which we score.
- **We rank acceptable-use policies above commercial caps; MOF ranks neither.** MOF excludes
  a release that implements "restrictions or acceptable uses" outright. We put an
  attribution-or-conduct license at 4 and a 700M-MAU commercial cap at 3, on the reasoning
  settled in issue #117: a prohibition on illegal or military use caps neither commerce nor
  reach, and collapsing it into the same bucket as a revenue ceiling discards information the
  map exists to surface. Both still sit below the `open` bucket, so the outcome agrees with
  MOF even where the reasoning does not.

### Where the boundary is currently weakest

The **dataset** vocabulary has no middle. Its classes are `open`, `gated`, `restricted`
and `closed`, and `open` is the only word above `gated`, so every corpus classed `open` sits
in that bucket — 51 products today, including one at 3 and six at 4. A model at 4
is `open_weights` and open-ish; a corpus at 4 is `open`. `the-pile` (license deferring to
per-subset terms, Books3 withdrawn) and `stack-edu` (deferring to The Stack v2's gated terms)
are counted as open on that basis. Closing it means giving the vocabulary a middle class and
re-scoring, so the two rungs involved sit in `KNOWN_VIOLATIONS` in the bucket test with the
reasoning attached, and the test fails if that list stops being accurate in either direction.

**Hardware has no license gate at all.** `hardware.yaml` scores design, toolchain and
availability rather than a source license, by design, and `open_hardware` sits at 5 in the
`open` bucket. The analogue that keeps the rule honest is OSHWA certification plus design
files under a license permitting reuse, which is what `beagley-ai` has. That analogue should
be written into the ladder when `edge_hardware` gets a recipe rather than left implicit.

## Caveats — these are editorial choices

The mapping is the analysts' judgment, not a law of nature. Two things to know before you
lean on it:

- **The gradient and the bucket don't perfectly align.** `source_available`, `restricted`,
  and `gated` all share gradient = 2, but bucket differently: `source_available` and `gated`
  are *open-ish* while `restricted` is *closed*. If your visualization shows both a fine
  gradient and a coarse bucket, expect them to disagree at the 2-fill band.
- **Some distinctions collapse.** `open_source` and `open` both map to 5; `documented`
  and `closed` both sit in the closed bucket. That's intentional for the map but may be too
  coarse depending on what you're showing.

If you want a different lens than the published map, you're free to define one — just do it
deliberately and note where it diverges from this table.
