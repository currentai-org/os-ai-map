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

Every non-null value needs a primary `sources:` entry. Both are analyst judgments against
MOF/OSI, which is why `components` and `note` read as editorial prose.

**A deterministic formula covers most of the map.** Every category declares a
`scoring_recipe` that names an ordered rule list over dimension values, and
`build/check_rubric.py` replays it against each product's recorded `components` to check that
the recorded score is the one the rules produce. Most recipes `extend` a shared ladder in
[`sources/rubrics/`](../../sources/rubrics/) rather than restating one: `software.yaml` covers
the software categories directly plus the software half of `safeguards`, `model.yaml` the fine-tuned and guardrail models. A category holding more
than one kind of product maps `extends` per product type.

Three caveats, because "a formula exists" is easy to over-read:

- **A recipe covers a category, not every product in it.** Every category declares one, and a
  small number of products are declared in a `deferred:` block, meaning the category has said the
  ladder does not decide them. Those scores remain editorial. `check_recipe` prints the
  per-category split and fails if a product abstains without being declared — read its output for
  the current figure rather than trusting a number typed here.
- **A recipe reproducing a score does not validate it.** It shows the rules describe how the
  category was scored. The document-grade evidence the checker reads was parsed out of the
  same files the scores live in, so agreement is a fidelity check on the formula, not on the
  facts.
- **A category can hold products back.** `scoring_recipe.deferred` lists products the rules do
  not decide, and every entry carries the reason in a `because:` string. Two reasons account for
  almost all of them: a license the ladder's tier list does not name, and a dimension not recorded
  in a form the ladder can read. Both are rubric changes rather than per-product fixes, which is
  why a deferral can be the right long-lived answer. Deferred products publish no openness
  evidence to the warehouse. `uv run python -m build.check_recipe` prints the live split.

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
| 3 | `open_weights`, `open`, `source_available`, `documented`, `gated` |
| 2 | `restricted`, `source_available`, `gated` |
| 1 | `closed` |
| 0 | `closed` |

Regenerated 2026-09-20; it is a few lines over `sources/scores/*.yaml`, so regenerate it rather
than trusting it. What holds the overlap down is the producible-pair check, which rejects a
score/class pair no rule in any recipe can emit — see
`docs/reference/evidence-and-freshness.md`.

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
| **4** | not OSI-approved, but no cap on who may use it or at what scale — attribution, naming, or an acceptable-use policy on conduct | `permissive_non_osi` |
| **3** | commercial use permitted but bounded — a MAU ceiling, a revenue ceiling | `use_bounded` |
| **2** | commercial use prohibited or reserved to the vendor, though source or weights are published; or published with no license stated at all | `commercial_forbidden`, `competition_restricted`, `noncommercial`, `no_derivatives`, `unstated` |
| **1** | closed or private: nothing published to license, or the license reserves it outright | `proprietary` |

**The 3/2 boundary asks one question: does the license permit commercial use at all?** That is
what separates Meta's 700M-MAU clause and AI21's $50M-revenue clause — which bind almost
nobody — from CC-BY-NC and Mistral's Non-Production License, which bind everyone. It is also
where MOF draws its own line: Class III, its entry point, requires components usable
"including for commercial and educational purposes".

**Published but unlicensed is a 2, not a 1.** There is no grant to rely on, so it is not open,
but the files are out, and 1 is kept for what is genuinely closed or private. The dataset
ladder's `unstated` rung applies it.

**No-derivatives data is a 2, a deliberate exception to the scale's letter.** CC-BY-ND allows
commercial use and caps nobody, which by the table above would make it a 4. For a corpus the
derivative is usually the point: a model trained on the data is arguably a derivative, so
no-derivatives blocks the main reason anyone wants it. The exception is the dataset ladder's
`no_derivatives` tier; the model and software ladders do not make it.

**Restricting by who the user is does not by itself forbid commerce.** A license that is free for
some users and charges others (Esethu) permits commercial use, bounded, so it sits at 3 in
`use_bounded`.

The tier names still differ per ladder, because a corpus and a codebase carry different
license families. The **caps** are what is universal.

### License slug and name aliases

A license only caps the score if it resolves to a tier, and two different sources of naming
drift keep it from resolving on its own.

**Hugging Face publishes a license slug, not the name a rubric's tier examples use.** Without a
mapping, `gemma` and `llama3.1` match no tier and the signal reads as absent while the license is
in fact present and use-restricting — the direction of error that overstates openness. A
meaningful share of base models depend on an alias to route their license at all. The mapping
(declared in `sources/signal_routing.yaml`'s `license.aliases.huggingface`) says only what a slug
is *called*; it deliberately does not say what tier it belongs to, which is each category's
`scoring_recipe`'s own judgment. A slug that aliases to a name absent from the category's tier
examples abstains, and that abstention is the signal to extend the rubric rather than to guess.

**The same problem recurs one layer over, in what a human typed into a `components` string.**
`sources/signal_routing.yaml`'s `license.aliases.recorded` canonicalizes a recorded name the way
the Hub table canonicalizes a published slug — again naming only, never a tier. Left unmapped,
these read as an absent license while the license is present and use-restricting, the same
overstatement direction. Porting the rubric to a second category surfaced several products whose
recorded license mapped to no tier, most of them nothing more than a spelling gap.
`Gemma-Terms-of-Use` is Google's published name; the alias resolves it to `Gemma-License`, the
repo's shorthand and the name the Hub alias already produces, so the two stay consistent with
each other.

### What the scale settles

One license family gets one cap wherever it appears. Without that, `Llama-3.1-Community` reads as
`3/open_weights` in one category and `2/restricted` in another, and `CC-BY-NC` caps one corpus at
2 while `CC-BY-NC-SA` leaves another at 5 — the same grant, two verdicts, decided by which
category happened to read it.

Two things worth knowing about the shape of it:

- **A full open recipe does not lift a capped license.** `tulu` releases its post-training
  data, code and RLVR recipe under Apache-2.0 and still scores 3, because the license rung
  fires ahead of the data and code rungs. The recipe is credited where it lives —
  `tulu-3-sft-mixture` is 5/open in `training_synthetic_datasets`, and the same recipe produces
  `olmo-3-instruct` at 5/open_source on an open base.
- **The dataset class vocabulary carries `restricted`** for this reason. It is otherwise the
  only product type with no word between `open` and `gated`, which is how a non-commercial corpus
  comes to sit in the `open` bucket.

### Creative Commons, vendor terms and other tier extensions

The license tiers in `sources/rubrics/pretrained.yaml` and `model.yaml` grow as new corpora and
vendor terms reach the map. Each addition is argued on the tiers' own test — does the license
cap who may use the artifact, or at what scale — not on the license family's reputation.

- **CC-BY-4.0 and CC-BY-SA-4.0** land in `permissive_non_osi`. OSI approves software licenses
  and has never approved a Creative Commons content license — CC-BY's own deed warns it is "not
  recommended for software" — so neither is `osi`. Attribution is all CC-BY asks; share-alike
  binds whoever redistributes rather than capping who may use the weights or at what scale,
  which is this tier's own test either way. `software.yaml` makes the same call for CC-BY-4.0 on
  code, for the same reason.
- **FAIR-Chemistry-License-v1** also lands in `permissive_non_osi`. It grants royalty-free
  commercial use and asks only for conduct — an acceptable-use policy — plus registration at the
  download gate. A gate is friction, not a cap on who may use the weights or at what scale, so
  this is the attribution tier and not `use_bounded`, which is reserved for a real ceiling.
- **OpenMDW-1.1**, the Linux Foundation's Open Model, Data and Weights License Agreement v1.1,
  lands in `permissive_non_osi`. Its body grants dealing in the model materials without
  restriction under copyright, patent, database and trade-secret rights, asks only that the
  agreement and origin notices travel with a redistribution, and disclaims any restriction on
  the outputs. Not OSI-approved, and no cap on who may use the weights or at what scale.
- **CC-BY-NC-4.0 and CC-BY-NC-SA-4.0** land in `commercial_forbidden`, alongside the unversioned
  `CC-BY-NC`: the NC clause answers this tier's one question — does the license permit
  commercial use at all — with no.

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

Reading only the first license in a compound is the failure this rule exists to prevent, and it
overstates openness every time: `internlm` resolves as `osi` on its Apache-2.0 code while the
application-gated weights license that governs the download goes unread, and `smoltalk` and
`flan-collection` resolve as clean Apache-2.0 while the half saying the assembled components keep
their own terms goes unseen.

### The `osi` tier's `examples`: literal spellings, and what's been added to it

The software ladder's tier lists spell out every license name literally rather than
normalizing them, because whether a given spelling is OSI-approved is a fact to look up, and a
fact is cheaper to get right than a regex is. A dual license under two OSI-approved terms
lands on `osi` however it is spelled: `openfn`'s `LGPL-3.0/GPL-3.0` and `megatron-lm`'s
vendored-component `Apache-2.0/MIT` both resolve because either branch is itself OSI-approved,
not because the compound-resolution rule above picked the less restrictive one.

Because the list is shared across every software category, adding a name for one product
tiers every other product that happens to record it, so each addition is checked against the
corpus before it lands. Two names on the list carry a ruling worth reading:

- **`GPL-2.0`**, for `slurm`. Slurm's `COPYING` body puts all Slurm code and documentation
  under the GNU General Public License. GPL-2.0 is OSI-approved and copyleft, which the
  tier's own definition already admits — AGPL sits beside Apache here — so the license was
  inside the definition and only outside the list. `orange-pi-5` records the same string, but
  under a `toolchain:` key the hardware ladder reads and this one does not, so the addition
  reached only `slurm`.
- **`Apache-2.0-WITH-LLVM-exception`**, for `cuda-tile`. LLVM's exception only widens what a
  derivative work may do with the Apache-2.0 grant — it drops the patent-notice requirement
  for object-code-only redistribution — and adds no cap on who may use the software or at
  what scale, so SPDX and OSI both treat the combination as Apache-2.0. `max` records the
  identical string under a `repo-license` key this ladder does not read, and carries a
  separate, non-OSI Modular Community License as its governing terms: the Apache text there
  covers the repository, not the product's usage terms. `cuda-tile` carries no such wrapper —
  its `LICENSE` body is the Apache-2.0-WITH-LLVM-exception text and nothing else — so the name
  resolves cleanly on its own there.

### `components-listed`: naming every component is not releasing the corpus

Between `open` and `documented-not-released` on the pretrained-model data dimension sits
`components-listed`: every component of the pretraining corpus is named and individually
resolvable — a link, or a citation identifying that specific dataset — while the mixture or
the sampling is withheld, so the corpus itself is not reproducible. RWKV is the case it is
written for: a machine-readable index with a URL column naming every component dataset, with
no assembled corpus and no reconstruction script.

**The discriminator is complete, per-component enumeration, not detail.** A composition
described in prose stays `documented-not-released` however careful the prose, and so does a
release that enumerates one stage of a mixture, or names some components while describing the
rest. Whether each named corpus is itself freely downloadable is not the test — that is a fact
about third parties, not about this release's own disclosure, and a gate on one component is
friction rather than withholding, the same reading the evidence store already applies to gated
weights.

It scores exactly as `documented-not-released` does at every rung, deliberately: the gain is
descriptive accuracy, not credit. Scoring it higher would reward publishing a list and shipping
nothing.

Shapes that fail the enumeration test rather than the availability one, and so stay at
`documented-not-released`: a partly synthetic mixture whose generated half is described rather
than named, a two-stage mixture with only the first stage evidenced, and data-preparation
documentation naming what the model consumes rather than what it was trained on.

**The release must publish an ENUMERATION, not name its inputs in prose.** This is the part of
the test that a reader can check without knowing what anybody intended, and it is what separates
the remaining held records from the ones that qualify. An enumeration is a listing with one entry
per component, carrying something per entry: a link, an identifier, a count, a scope. Prose that
names the archives a model trained on is a description of the inputs, however accurate, and the
ladder's other values already record that.

Counting sources does not decide it. `clay` qualifies on a training-data page that lists six
imagery sources one per row with coverage and ground resolution, and `rwkv` on a machine-readable
index with a URL column. `aifs` and `granite-geospatial` each name two archives, in prose
describing what the training consumed, and do not; neither do `pangu-weather` and `prithvi-eo` on
one archive each. Two entries listed as entries would pass; two archives named in a sentence do
not.

The three failure shapes above are the same test applied to a partial listing: a mixture whose
synthetic half is described rather than listed, a two-stage mixture with one stage listed, and
data-preparation documentation in place of a corpus listing. In each the enumeration exists and
does not cover the corpus.

### `self-host` and `core-gated` are one question

The software ladder asks whether functionality is withheld from the published source for a
paid tier, and records the answer under `core-gated` with values `gated` and `ungated`. The
corpus also answers that question under `self-host`, in a vocabulary of its own: `yes`,
`primary`, `only` on one side and `no`, `none`, `enterprise-only`, `enterprise-tier` on the
other. Whether a vendor lets you run the published thing yourself *is* whether the core is
withheld, so these are one dimension recorded under two keys rather than two facts.

An undeclared key is dropped before the formula runs, so a record answering only under
`self-host` leaves the dimension unanswered and the ladder abstains. Two mechanisms carry the
answer instead, and they do different jobs:

- **`reads:`** widens which recorded KEY answers a dimension. `core_gated` reads
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

Reading the second key is conservative by construction, and rule ordering is why. Most records
answering under `self-host` alone are hosted products recording `source: closed`, where the first
rung fires on `source` alone and `core_gated` is never read — the software ladder already says the
dimension is "only meaningful where `source` is public". That is the case worth being careful
about, since a hosted service has no core to gate, and the ordering neutralizes it before the
dimension is consulted.

### Selling something is not gating a core

This is the distinction between 4/`open_core` and 5/`open_source`, and it is the one that gets
scored wrongly most often.

`core_gated` asks whether functionality is withheld **from the published source**. It does not
ask whether the vendor makes money. A separate hosted product, a managed service, or a different
SaaS built around an otherwise complete open core does not gate that core, however much it
costs. A `commercial:` or `service:` clause is therefore not evidence either way, and the ladder
reads neither key — where that is all a product records, the dimension is unanswered and the
formula abstains.

Such a clause is still worth recording, and the record says outright that it is not scored: it
sits under `components.context` rather than beside the dimensions. The rule is mechanical, not a
per-key ruling. Any key the product's ladder neither declares nor names in a `reads` list goes
there, and `build/check_components.py` fails a record where it does not, in either direction. So a
ladder that starts reading a key forces the key out of `context`, and a new key nobody has ruled
on lands in `context` until someone does. A top-level key no ladder reads would drop out of the
score without a word, which is what the gate prevents. Moving a key across the line changes
nothing a reader sees: `raw` is untouched, and `components_of` lifts `context` back in.
`uv run python -m build.route_context --write` does the move.

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

Every one of the ungated cases above is a product a `commercial:` clause would have scored
4/open_core — on the vendor selling something at all. The rule is stated here and in
`sources/rubrics/software.yaml` so it is applied from the rule rather than inferred from a
precedent somebody happened to read.

One caveat for anyone applying it: not every `core-gated: gated` in the corpus was recorded
against this test. Some products reaching the gated rung record their gate as a managed cloud
"on top" of a complete OSI core — the shape this section says is *ungated* — with no withheld
component named, and have not been re-read since. A `gated` value is not evidence that somebody
applied this rule; check what the record says is actually withheld.

### The `ungated` acceptance standard, and why it is prospective

`ungated` is a negative: no document asserts that nothing is withheld, so a reviewer can
always claim the cited evidence establishes something weaker and be literally right. That
makes the negative unfalsifiable rather than rigorous unless the standard for accepting it is
written down.

The standard: a recursive tree showing no `ee/`, `enterprise/`, `commercial/` or
`proprietary/` path establishes path absence and nothing more, and is never sufficient alone.
Pair it with a statement from the party that would do the withholding — a vendor naming its
commercial offering as a separate product, or foundation or academic governance meaning no
commercial party is positioned to withhold anything. This is a human-reviewed policy: no gate
enforces it, because whether a page names a separate offering is not mechanically decidable
from its URL.

What displaces the standard and makes a product `gated` instead is direct evidence of the
mechanism, which is always citable: a closed package the open one pulls, a license key in the
published source, or an `ee/` tree under different terms. Gating is provable and `ungated` is
a negative no document asserts, which is why the burden sits where it does.

The standard applies **prospectively**, not to the existing corpus. Most of today's
`core-gated` citations are a first-party repository read alone, without a separate vendor or
governance statement beside it — the standard is stricter than that practice, and applying it
backward would flag a large share of existing records as under-evidenced on citations nobody
has re-examined, unsettling foundation projects on evidence that was never in question.
Sweeping the back catalogue against the new standard is a separate, deliberate migration, not
something a category promotion does on the side.

### A product is scored on the artifact it ships, not on what it can load

A harness that runs against a model you supply is scored on the harness. The model it happens to
be shipped alongside is a different product with its own score, and scoring the harness down for
it would count the same license twice.

`llamafirewall` is the case the rule is settled on. It is an MIT firewall that
inspects prompts and code and calls out to whatever guard model you point it at; the PurpleLlama
monorepo ships it next to Prompt Guard 2 and Llama Guard, which carry the use-restricted Llama
Community License. The repository makes the split explicit — the root `LICENSE` is the Llama 3.2
Community License and `LlamaFirewall/LICENSE` is plain MIT — and both guard models are separately
scored on this map at 3/open_weights. So the restrictive terms are not being overlooked; they are
recorded against the artifact they actually govern. `llamafirewall` is 5/open_source.

`openai-evals` resolves the same way: it records
`license: MIT`, `source: public(full framework + registry)` and
`per-dataset-licenses: mixed(CC/CC0/Apache for bundled data)`, and scores 5 on the framework.
Any further bundle of this shape resolves the same way.

The rule does have an edge, and it is worth stating so nobody stretches it. It applies where the
bundled artifact is *substitutable* — you can point LlamaFirewall at a different model and it
still works. Where the published thing genuinely cannot run without the restricted component, the
component is not a bundle but a dependency, and `core_gated` is the dimension that asks about it.

### `permissive_non_osi`: attribution-only licenses, and the artifact they have to attach to

`permissive_non_osi` holds a license that is not OSI-approved but caps neither who may use the
software nor at what scale — attribution and naming are all it asks. Two rulings populate it
for software.

**CC-BY-4.0**, for `model-context-protocol`. A protocol may license its documentation under
Creative Commons on the same reading "Creative Commons, vendor terms and other tier extensions"
gives the model ladder's copy of this tier: attribution is all CC-BY asks, so it sits above
`competition_restricted` rather than beside a scale cap. MCP is the only software product that
reaches it; the CC-BY-4.0 records on `codecontests`, `dclm-baseline`, `gpqa`, `mbpp` and `synth`
are corpora scored by `dataset.yaml`'s own tier list, not this one.

MCP is also the case for a narrower rule: **a license on the project's documentation is not a
license on the product.** MCP's CC-BY-4.0 covers documentation other than the specifications, so
it belongs under a `docs:` key this ladder does not read rather than inside the `license`
compound, where most-restrictive-wins would let a license over the project's prose decide the
score of the artifact people actually run. `autogen` records the identical shape — MIT under
`license`, CC-BY-4.0 under `docs:` — and scores 5.

**`Crawl4AI-Attribution-License`**, for `crawl4ai`. Its `LICENSE` is the stock Apache-2.0 text
followed, after "END OF TERMS AND CONDITIONS", by an appended Attribution Requirement binding
"all distributions, publications, or public uses" to carry a credit line. It lands in
`permissive_non_osi` rather than `osi` because Apache-2.0 section 4(d) binds redistribution of
the work while this clause binds public *use* of it, and section 4 permits added terms only
over a contributor's own modifications — so the composite is not the OSI-approved license
GitHub's classifier reports. It lands here rather than in `competition_restricted` because
attribution is all it asks: it caps neither who may use the software nor at what scale, which
is this tier's definition stated directly.

### `competition_restricted`: the vendor licenses that land here, and why

`competition_restricted` holds a published, readable source whose license forbids or charges
for a class of use — competing hosted services, for-profit production above a threshold, use
before a delayed conversion date. The reader can audit the code and still not be free to run
it, which is why it sits below the OSI tiers rather than beside them; it is not `proprietary`
because the source itself is published.

- **`n8n-Enterprise-License`** covers the `ee/` directories n8n ships inside the same public
  repository as its Sustainable-Use-License core. The source is published and readable, and
  running the gated pieces needs a paid license key — this tier's definition almost word for
  word.
- **`Modular-Community-License`** caps capacity by device architecture — eight devices on any
  accelerator other than x86/ARM/NVIDIA-PTX — and grants only "a limited right to redistribute
  certain components of the SDK". Scale, not attribution.
- **`Dify-Open-Source-License`** is Apache-2.0 plus a multi-tenant service restriction and
  branding conditions; the multi-tenant clause is the anti-compete clause.
- **`Open-WebUI-License`** is BSD-3-Clause plus a branding-retention clause that binds above 50
  end-users per 30 days unless an enterprise license is bought — a threshold above which
  production use is charged for.
- **`LobeHub-Community-License`** is Apache-2.0 plus a requirement to buy a commercial license
  before distributing a derivative work. It restricts distribution rather than running, the
  loosest fit of this group, but a paid gate on derivatives is still a class of use charged
  for, and it is plainly neither OSI nor `permissive_non_osi`, which admits attribution and
  naming and nothing more.
- **`PolyForm-Shield`** forbids use in anything competing with the licensor's product — this
  tier's first clause stated directly. It governs `autogpt_platform/`, AutoGPT's active
  product; the legacy MIT components do not lift it.
- **`MinerU-Open-Source-License`**, for `mineru`, and **`AI-Pubs-Open-RAIL-M-Modified`**, for
  `marker`, are both an Apache or RAIL base with a revenue or funding threshold above which a
  separate commercial license is required: MinerU is Apache-2.0 "subject to the additional
  terms below", needing a commercial license above 100M MAU or USD 20M monthly revenue;
  marker's weights are free below USD 5M funding or revenue and licensed commercially above
  it. The two other OpenRAIL records on the map, `zentropi-cope` (zentropi-openrail-m) and
  `starcoder2` (BigCode-OpenRAIL-M), are `type: model`, scored by `model.yaml` against its own
  tier list, and spell their licenses differently besides.
- **`NXAI-Community-License`**, for `mlstm-kernels`. The NXAI Community License Agreement is a
  Llama-3-style base with its own "Additional Commercial Terms": above EUR 100,000,000 in
  consolidated annual revenue, incorporating the material into a commercial product or service
  needs a separate license NXAI may grant at its sole discretion — a revenue threshold above
  which a class of use is charged for, the same shape MinerU and marker hold under different
  vendor names. It is not `use_bounded` in the sense the model ladder uses that word for
  Llama-family licenses, because the software ladder has no such tier: `competition_restricted`
  is where a bounded-commercial license lands for software, the same reading
  `n8n-Enterprise-License` and `Modular-Community-License` were added under.

### Where openness and capability rest on different SKUs, say which and why

`multi_sku_rule` resolves openness on the most restrictive license among the SKUs whose weights
are actually distributed. Capability answers a different question — how good is the best thing
this publisher ships — and where the strongest tier is API-only, the two axes end up measuring
different artifacts of the same product. That is correct on both axes and invisible to a reader
who sees only two numbers.

So the record has to disclose it. Where the SKU carrying the openness score is not the SKU
carrying the capability score, the openness note names which tier each axis reads and the
capability note names the tier its number came from. One sentence each; the point is that a
reader who takes the openness score as a statement about the benchmarked model is corrected by
the record rather than by a maintainer.

`voyage-embeddings` is the case the rule is settled on. Openness reads voyage-4-nano's
Apache-2.0 weights and scores 3/open_weights; capability reads the flagship's RTEB result and
scores 4, and the flagship is API-only. Both notes say which tier they read.

It is not split into two products, and the near-miss says why. `esm-3` ships the same shape - a
1.4B checkpoint you can download beside 7B and 98B tiers served through the Forge API - but its
capability attributes are read off the open checkpoint's own documentation, so both axes rest on
the same artifact and there is nothing to disclose beyond which tier that is. Splitting on SKU
boundaries would divide both records, and every other family that ships a small open checkpoint
beside a hosted flagship. A product is one publisher's line. The rule is disclosure, not
division: where the axes diverge, the record says so; where they do not, it names the tier anyway
so a reader can tell the difference.


### An accessory tracks the platform it completes

An add-on is not a board, and asking board questions of one answers about the wrong artifact.
What a builder gets from a HAT or a carrier is the openness of the system it completes.

`raspberry-pi-ai-hat-plus` is the case. It publishes a HAT+ mechanical specification
rather than board design files, and its toolchain is half open — the Pi driver integration is
open, Hailo's Dataflow Compiler is registration-gated. Both of its own answers are `partial` and
neither describes the system anyone runs. It plugs into a `raspberry-pi-5`, and takes that board's
score.

This is recorded as an `accessory_host` dimension in `sources/rubrics/hardware.yaml` rather than
as an extra rung. The rung version — `{schematics: partial, toolchain: partial}` → 4 — would have
reproduced the number the HAT then held and been non-monotonic: `ti-am67a` and
`qualcomm-dragonwing-rb3-gen-2` both record `{partial, open}` and score 3, so it would have ranked
strictly weaker evidence strictly higher. An accessory records its host rather than needing a
rung of its own.

Tracking the host rather than freezing a number is what keeps the accessory honest when the host
moves: when `raspberry-pi-5` reads 3/documented, the HAT reads 3/documented with it, without any
new evidence about the HAT. A frozen number would leave the accessory reading more open than the
system it completes. `accessory_host` carries a rung for each host class the corpus holds,
`open_toolchain` and `documented`, and none for `open_hardware`, which no accessory has met.

### A board question asked of a chipset answers about the wrong artifact

The same lesson one kind of product over.

`edge_hardware` holds boards, modules and bare chipsets, and five of the ladder's eight rungs turn
on `schematics` — were the board design files published, and may they be reused. A chipset has no
board, so it records nothing there, correctly, and a ladder without a chipset rung abstains on it:
the product is deferred on a question it cannot be asked.

`form_factor` (`board` / `module` / `chipset`) is recorded on every product in the category and decides which
questions apply before any of them are asked. A chipset takes a rung of its own, testing whether
its datasheets are public and whether anybody can buy one — which is what `documented` means in
this category, "datasheets public + buyable, but no design files of its own". A module keeps the
design rungs, because `schematics: none` on an M.2 card means withheld, which is an answer; on a
chipset it means there was never a board.

Two details are worth carrying forward. **Rung order is not a guard.** First match wins, so
putting the chipset rung above the design rungs does not keep a chipset off them — a chipset that
fails its own rung meets a board's next, and scores 3 on a reference design that is not its own.
Every design rung tests `board_design` as its first condition instead. **And `board_design` is a
derived dimension**: `reads: [form_factor]`, with `board` and `module` both aliased onto `exists`
and `chipset` onto `none`, because a rung matches one value exactly and "board or module" needs a
name of its own. `availability` does the same over `retail`, collapsing `open_market` and
`distributor` onto `buyable`. Both use the `reads:`/`value_aliases:` pair described above — the
first use of it to give a ladder its own vocabulary rather than to absorb a contributor's.

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

### A rule that cannot fire is a place for a later edit to hide

A formula that resolves first-match-wins can declare a rule for a combination no product records,
and that rule will sit there, untested, until a later edit either fires it by accident or amends
it without anyone noticing it never ran. Two hardware rulings turn on treating that as a defect
rather than a completeness feature.

`hardware.yaml`'s `schematics` dimension has no rung for `{schematics: open, toolchain: closed}`
— open design files paired with a non-open toolchain — on exactly this reasoning: no product on
the roster records that pair, so a rung for it would be unreachable and therefore untestable.

The same reasoning keeps a `restricted`/1 rung out of the formula entirely, even though the
category's own prose ladder describes one (an NDA, a design win, or a private-sale-only part) and
the vocabulary for it — `datasheets: nda`, `retail: restricted` — is fully declared. No product
on the roster is one, so declaring the rung would add a rule that cannot fire. A chipset that would sit on that rung today —
one recording `datasheets: nda` or `availability: gated` — matches no rung instead, and the
category defers it with a reason. That is a weaker claim than 1/restricted, and the only one the
evidence supports: being unable to read a datasheet is not the same finding as a vendor gating the
part behind an NDA, and one rung cannot tell the two apart. The tier stays written down in
`sources/rubrics/hardware.yaml`'s comments so the vocabulary is not lost, and becomes a rung the
first time a part actually needs it.

### Reaching buyers through module partners is a retail channel, not a proxy for one

`hardware.yaml` asks a chipset two questions no board rung reads: are its datasheets public
(`datasheets`), and can anyone buy one (`retail`, read into a `buyable`/`gated` dimension named
`availability`). Together they are what the category's own vocabulary means by `documented`:
"datasheets public + buyable, but no design files of its own." A board's `schematics` answer
already implies both halves, which is why no board rung asks either one — but a bare chipset has
no design to read, so both have to be asked directly or the rung would hand out `documented` on
one fact alone.

**What counts as "buyable" for silicon.** An application-processor SoC does not reach buyers
through a cut-tape listing of bare die; it reaches them through the module and board partners who
design it in. `rockchip-rk3588`, `ti-am67a` and `nxp-imx-8m-plus` all record `buyable` on that
basis — `ti-am67a` has an ACTIVE order path on TI's own product page, `rockchip-rk3588` and
`nxp-imx-8m-plus` reach buyers through their module partners — and the rung's note names which
channel was read. Requiring a bare-part purchase would mark almost every SoC in the category
ungated-and-unbuyable, which is the less true answer; the module/board channel *is* the retail
channel for application-processor silicon, not a stand-in for one.

**`gated` collapses two different reasons nobody can buy a part**, and does so deliberately: an
NDA or design-win part (`restricted` in `retail`'s own vocabulary, which nothing on the roster
records yet) and a withdrawn one (`discontinued`). `google-coral-dev-board` is the `discontinued`
case: Seeed marks both variants out of stock, and `coral.ai/products/dev-board` redirects to a
page naming no hardware and linking no purchase route. It fit none of
`open_market`/`distributor`/`restricted` — `restricted` means gated by NDA or design win, which is
a part somebody *can* buy under terms, and a withdrawn part is a different fact about a different
question. The change was deliberately score-neutral: no rung read `retail` at all when it landed,
and the chipset rung that reads it today asks only whether anybody can buy one, which is the same
answer either way. A board's own design-file rungs never read `retail`, so `google-coral-dev-board`
staying at 3/documented on its schematics is not a consequence of this ruling — extending the
condition to the design rungs would be a separate curation decision, made on purpose rather than
as a side effect.

### A vocabulary needs definitions before it needs a rung

`hardware.yaml`'s `blobs` dimension — does booting or inference need proprietary firmware — is
declared, recorded on every product, and tested by no rung: every part in the category runs on a
proprietary SoC that needs firmware, so it is a caveat on every product in the category and a
discriminator between none of them. It follows that level 5 cannot ask for "no blobs" — that would
be unreachable, `beagley-ai` included, and the category's prose ladder does not ask for it.

The values need definitions, because without one a curator guesses at where the line between
`minimal` and `required` sits and two guesses disagree on the same shape of fact. The test is
**necessity, not size**:

- `none` — boots and runs inference with no proprietary firmware. Nothing in this category
  records it, and nothing is expected to.
- `minimal` — proprietary firmware exists but is *optional*: the part boots and runs inference
  without it, and the blob buys an extra peripheral or an accelerated path rather than a working
  system.
- `required` — booting or inference needs it. The ordinary case: a vendor BSP ships firmware you
  cannot substitute, whether that is a whole boot chain or a single Wi-Fi blob.

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
rather than a comment: a rung emitting an `open`-bucket class from a non-OSI license tier breaks
the rule whether or not it can currently fire, and an empty `examples` list is exactly what keeps
such a rung from being noticed by reading.

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
  attribution-or-conduct license at 4 and a 700M-MAU commercial cap at 3: a prohibition on illegal
  or military use caps neither commerce nor reach, and collapsing it into the same bucket as a
  revenue ceiling discards information the map exists to surface. Both still sit below the `open`
  bucket, so the outcome agrees with MOF even where the reasoning does not.

### Where the boundary is currently weakest

The **dataset** vocabulary has no middle. Its classes are `open`, `gated`, `restricted`
and `closed`, and `open` is the only word above `gated`, so every corpus classed `open` sits
in that bucket, including ones scored below 5. A model at 4
is `open_weights` and open-ish; a corpus at 4 is `open`. `the-pile` (license deferring to
per-subset terms, Books3 removed) and `stack-edu` (deferring to The Stack v2's gated terms)
are counted as open on that basis. Closing it means giving the vocabulary a middle class and
re-scoring, so the two rungs involved sit in `KNOWN_VIOLATIONS` in the bucket test with the
reasoning attached, and the test fails if that list stops being accurate in either direction.

**Hardware has no license gate at all.** `hardware.yaml` scores design, toolchain and
availability rather than a source license, by design, and `open_hardware` sits at 5 in the
`open` bucket. The analogue that keeps the rule honest is OSHWA certification plus design
files under a license permitting reuse, which is what `beagley-ai` has. That analogue should
be written into the ladder when `edge_hardware` gets a recipe rather than left implicit.

### A corpus has no source or weights to gate

A dataset ladder cannot ask the software question or the model question: there is no runtime
to self-host and no weights to download, so `source` and `core-gated` have nothing to bind to.
What decides a dataset's openness instead is whether you can get it, whether the license that
covers it covers all of it, and whether anything documents what is inside — availability,
license, documentation, in that order of weight. `sources/rubrics/dataset.yaml` declares all
three; no dataset or benchmark category asks a fourth.

### An answer withheld is a different limitation from a locked door

A benchmark can hide two different things behind a gate: the questions, or just the answers.
`availability` records the first. A separate `answers` dimension records the second, and it
exists only for benchmarks — a training corpus has no answer to withhold, so it is declared and
never fires for a training-data category. That is a legitimate shape for a *dimension*: one no
product in a category records is unremarkable. A *rung* nothing reaches is not, which is why the
ladder still separates the two ideas rather than declaring `answers` unconditionally answered.

`gaia` and `gpqa` are the pair the dimension exists to tell apart. Both are login-walled, so
`availability` reads them alike. `gaia` publishes its validation split and keeps roughly 300 test
answers private; `gpqa` is equally gated and explicitly ships no hidden split at all. One of them
you can run and not grade; the other you can run and grade in full. `availability` cannot see
that difference, `answers` can, and the two rungs it feeds — `held-out` and `private`, one per
recorded spelling of the same shape — sit ahead of the gate rungs, because a benchmark you cannot
score yourself is a bigger limitation than a login wall.

`public` is deliberately not a value of this dimension. A dozen other keys — `paper:public`,
`splits:public` — carry the same word for an unrelated fact, so declaring it would make those keys
read as answer evidence on products recording no answer state at all, and `check_recipe` reports it
because no rung tests it. A value earns a place in a dimension's vocabulary only if it is
unambiguous there.

### A card is required at the top rung so unrecorded evidence cannot resolve as clean

The dataset ladder's availability rungs fire on *positive* evidence: every spelling of "there is
a barrier" is a distinct token, and every spelling of "no barrier" — including simply recording
nothing — falls through toward the open end. Left alone, that would let "nobody recorded an
availability key" resolve the same as "ungated," which is not the same finding. Requiring a
dataset card at the top rung closes that gap: a corpus reaches 5/open only with a license, an
ungated download, *and* documentation, so silence at the gate cannot masquerade as an
open door.

`present` and `card`/`dataset_card` are one fact recorded under `documentation` in
`training_synthetic_datasets`; `'yes'` and `datasheet` are the same fact, spelled differently, in
`benchmark_eval_data`. Both spellings carry the top rung, which is why the formula has two
5/open rules rather than one — a components normalization across the two categories would
collapse them back into a single rung without moving any score.

### When the local checker and the warehouse must agree on "no license"

`sources/rubrics/dataset.yaml` declares `none` under its `unstated` tier and `closed` and
`proprietary` under its `proprietary` tier, explicitly, rather than leaving them to
`check_rubric`'s definitional fallback, which resolves any unmapped license value to a tier
*named* `proprietary`. Leaving the values implicit put the local checker and the warehouse in
disagreement without either being wrong on its own terms. The local checker invented
the fallback tier and scored the affected internal-eval products on their `availability` rung
instead; the warehouse joined a real lookup table, found no row for a tier that was never
declared, and suppressed the score. Declaring the three values puts both computations on the same
table and the same answer.

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
