# Capability Guide

What the capability axis records, the peer-comparison instrument behind many of its bands,
and what it deliberately does not claim. This is normative on the fields and the vocabulary. For how a
capability band earns a `last_verified` and the gates that hold it, see
`docs/reference/evidence-and-freshness.md`; for the reader-facing account see
`docs/methodology.md`.

## What the axis measures

A 1-5 band for how capable a product is **within its category**, and never across one.
A model, a training framework and a dataset are capable of different things, so a 4 in
`base_pretrained` and a 4 in `ml_frameworks` are not the same claim and must not be compared.

Capability is the axis the map is weakest at, and it says so plainly. Openness is
reproducible from recorded evidence and adoption is a banded signal, but capability is
**neither measured nor computed** here. Nothing in `build/` derives it. Most `value` fields
are prose rather than a bare number, by design. The band is a curator's
judgment, and the honest thing the axis does is record what that judgment rested on so it can
be checked and refreshed.

A null score is an abstention, not a gap: some records — datasets and a wire protocol among
them — are not capable of anything the axis measures, and abstain rather than score 0.

## The recorded fields

| field | what it holds |
|---|---|
| `score` | the 1-5 band, or null to abstain. Non-null needs a `sources` entry. |
| `basis` | which **instrument** the band was read with: `benchmark`, `feature_matrix`, `training_value`, or `n/a`. |
| `basis_detail` | what that instrument was, in prose (the benchmark's name, the kind of coverage). Free text. |
| `value` | the recorded observation the band rests on: exact and quoted for a benchmark or arena placement, and often a synthesized summary of documented features for a `feature_matrix` band, not a verbatim quote. |
| `relative_to` | the slug of the product this band was placed **against**, when placed by comparison rather than measured. |
| `relation` | how this band sits against `relative_to`: `at`, `one_below`, `two_below`, `one_above`. Required with `relative_to`, meaningless without it. |
| `comparison` | when the spacing recorded by `relative_to`/`relation` was last judged still to hold (`last_attested`), and what was read on the peer to judge it (`sources`). Optional. |
| `pivot_languages` | the listed languages an evaluation set was not built for, declared whether or not they have counts. Required with `language_coverage`, datasets only. See [Per-language coverage](#per-language-coverage). |
| `language_coverage` | per-language evidence for an evaluation set, one entry per language, task, dataset component and split: count, unit, provenance and whether the split is the official evaluation split, cited through `sources`. Optional, datasets only. See [Per-language coverage](#per-language-coverage). |
| `confidence` | the curator's certainty (`high`/`medium`/`low`). Note it does not encode the strength of the instrument — a `high` can sit on a feature-matrix judgment with no measurement under it. |
| `note` | the prose behind the band: what the product does well, what it sits below, and against whom. |
| `sources` | the evidence, at least one for a non-null score. |
| `last_verified` | the date the whole axis was last re-confirmed. See `evidence-and-freshness.md`. It dates the band; the `language_coverage` record is dated by its sources' `accessed` dates instead ([Per-language coverage](#per-language-coverage)). |

## `basis`: four genuinely different instruments

The enum is what a checker reads, so it stays small and controlled while `basis_detail`
carries the prose. The four are not grades of the same thing; they are different kinds of
evidence, and a checker that could not tell them apart could not route or gate the axis.

- **`benchmark`** — a published number (a leaderboard placement, an eval score). Re-reading
  it is the confirmation; the number is a property of a harness-plus-model pairing, not of
  the product alone, so a benchmark band does not claim the benchmark was re-run.
- **`feature_matrix`** — a judgment over what the product does, and the basis most bands on
  the map carry. `uv run python -m build.check_capability` prints the live split.
- **`training_value`** — ablation or downstream-model evidence that a dataset or recipe
  improves what is trained on it (`basis_detail` names it `ablation` or `superseded`).
- **`n/a`** — an honest abstention. By convention it pairs with a null score, but nothing gates
  that pairing today, so the corpus is not uniform (e.g. `lamini` carries `score: null` under
  `basis: feature_matrix`). Treat `score: null` + `basis: n/a` as the intended shape for an
  abstention until a gate enforces it.

## The real instrument is a peer comparison

Many bands are not measured at all. A large share of the corpus places a product against a peer
in its own category — "one tier below the Megatron-LM anchor", "mid-tier next to langfuse" — and in
`finetuning_code` every note does it. Peer comparison is **a major capability instrument**, not
demonstrably most of the axis. Written as an English sentence it is unreachable: nothing can check
it, refresh it, or notice when the product it names moves.

`relative_to` and `relation` record it as data instead:

```yaml
capability:
  score: 4
  basis: feature_matrix
  relative_to: megatron-lm
  relation: one_below
```

`relation` is deliberately tiny and domain-free (`at` / `one_below` / `two_below` /
`one_above`) so it generalizes across categories as different as `edge_hardware` and
`benchmark_eval_data` without asserting anything about what capability means in either.

Recording the comparison converts an unfalsifiable claim into a falsifiable one — the same
move `establishes` made for openness. It does **not** make capability derivable from evidence,
and it does not verify that the comparison is right; it makes the comparison checkable.
`build/check_capability.py` then asks the questions a recorded comparison makes
answerable and a sentence never did:

1. **Consistency.** If a product records `relative_to: megatron-lm, relation: one_below`, its
   score must be exactly one below Megatron-LM's. Arithmetic over two recorded integers is the
   whole rule — the analogue of the producible-pair check, needing no rubric.
2. **Same category.** A peer is something in the same category. A cross-category comparison is
   never what the notes are doing, and allowing it silently would let the anchor graph sprawl
   into a ranking of the whole map.
3. **Transitive freshness.** A dated band cannot be fresher than the band it derives from. If
   Megatron-LM's capability was last confirmed in June and `trl` claims today, `trl` is
   claiming to have re-derived a comparison against a fact nobody re-read. This is the openness
   invariant applied to a different dependency: a date is only as good as the least recently
   confirmed thing underneath it. Unless the edge carries an attestation of its own — see
   below.
4. **No cycles.** Consistency reads each edge alone, so a reciprocal pair — `X one_below Y`
   written alongside `Y one_above X` — satisfies the arithmetic on both while being circular:
   each score's justification is the other's, and neither rests on a read made outside the
   pair. A ring of any length is the same defect, the reciprocal pair its shortest case, so the
   gate walks the `relative_to` graph and rejects a cycle before the graph grows enough to hide
   one.

The gate ratchets like the others — it covers the products that record a comparison and does
not block the ones that do not.

### Dating the edge itself

Transitive freshness as written binds the dependent's **whole-axis** date to the peer's
**whole-axis** date, and those are two claims about two different products. The consequence
shows up as the corpus grows: every new product's natural peer was confirmed before the
product existed, so a tranche can compare its own members to each other and to nothing else.
The comparison then either goes unrecorded or rests on a re-derivation nobody performed.

`capability.comparison` records the edge's own confirmation:

```yaml
capability:
  score: 4
  basis: feature_matrix
  relative_to: verl
  relation: one_below
  comparison:
    last_attested: 2026-08-31
    sources:
      - url: https://github.com/volcengine/verl
        shows: "the algorithm catalogue, still wider than this product's"
        accessed: 2026-08-31
        http_status: 200
        content_sha256: <64 hex>
```

`last_attested` dates the **spacing**, not either product. The sources are a separate list from
`capability.sources` on purpose: they are citations about somebody else's product, and folding
them in would let a peer's page count as this product's own evidence and would make the
weak-root check read the wrong thing.

What the gate then asks, and why each one:

- the axis's `last_verified` may not be later than `last_attested` — `relative_to` and
  `relation` are part of the score, so a whole-axis confirmation cannot outrun one of its parts;
- at least one attestation source must record `accessed` on or after `last_attested`, or the
  date rests on nothing;
- that source must carry `http_status` and `content_sha256`. The judgment needs a real read of
  the peer, and without this requirement the first pass under time pressure attests off the
  peer's `value` as this repository already recorded it, which confirms nothing.

In exchange, the peer's whole-axis date does not bound the dependent's. Where the peer *has*
been re-read since the spacing was judged, `check_capability` reports the edge rather than
failing it: the arithmetic check already fires if the peer's score moved, and this catches the
case where its `value` moved and its score did not.

One fetch attests every edge against the same peer, so a tranche pays per peer rather than per
product. And an attestation may not re-date the peer's own `capability.last_verified` as a side
effect — unless the read happened to cover every source that axis cites, in which case the peer
really has been re-derived and the curator may date it. That is the common case rather than the
exotic one: measured 2026-09-20, 63 of the 110 peers named by a `relative_to` cite exactly one
source.

### Do not force every comparison through the category anchor

`relative_to` may name **any sufficiently well-supported peer in the same category** — it is not
required to be whatever product the category compares against most often. For a distant band,
prefer a nearer peer whose capability is independently evidenced over stretching the relation
vocabulary to reach the anchor.

The corpus already works this way. `pinecone` is recorded `one_above milvus`, not against `vespa`,
which most other `storage` bands name; `thunderkittens` and `hummingbird` are both `two_below
tensorrt` rather than against `apache-tvm`, which most `compilers` bands name; `amazon-bedrock-
custom-models-fine-tuning` is `one_below openai-fine-tuning-api`, a hosted peer, rather than
against `megatron-lm`. In each case the nearer peer is the more informative comparison: a
hosted fine-tuning service says more about another hosted fine-tuning service than a
trillion-parameter training framework does.

This also matters because the vocabulary bottoms out. Against a 5-scored peer the lowest
expressible band is `two_below`, so a product that honestly sits at 1 or 2 cannot be placed
against it at all — a `torchtune`-class peer at 3 can express a 2, and a 5-scored anchor cannot.
The answer is a nearer peer, **not** more relation values: adding `three_below` would encode
distance from an assumed global anchor, when what the corpus actually holds is a peer-comparison
graph.

### A comparison root must itself be evidenced

A peer named by `relative_to` must carry a **non-null capability score, a substantive `value`,
and evidence behind that capability**. All three, because each failure breaks something
different: a null score makes the subtraction meaningless, an empty or placeholder `value`
leaves "one below X" pointing at nothing a reader can see, and an unsourced value is an
assertion nobody can re-open.

A peer with no `value` satisfies the arithmetic on every band that names it — a `one_below`
against a 4 really is a 3 — while the thing being compared to is unstated, so `check_capability`
reads green over a fan-out of bands resting on nothing a reader can see. **Consistent is not
correct.**

An unrecorded surface fails a second way. A category's discriminating rung is usually a claim
about what a peer does, and a peer can stop doing it: a product whose README comes to lead with a
control centre running third-party agents is not the product that "runs somebody else's loop"
describes, and every band in that category resting on the distinction moves with it.
Nothing in the corpus can notice the product moved unless its surface is written down, which is
the failure recording comparisons as data exists to prevent.

`build/check_capability.py` reports weak roots with their fan-out, so remediation runs in the
order that clears the most dependent bands.

## Per-language coverage

`languages` on a dataset ([`identity.md`](identity.md#languages)) says which languages a set
covers. It does not say how much the set holds in each, and for a language-targeted evaluation set
that is the question: two sets listing the same twenty codes can hold a thousand native questions
per language or fifty machine-translated ones. `capability.language_coverage` records it, cited to
the card or paper (R-2026-10-30-h), and `capability.pivot_languages` declares which listed
languages the set was not built for (R-2026-11-01-b).

The unit of evidence is one **language x task x dataset component x split** (R-2026-11-01-c). A
suite whose tasks use different units, sample sizes and sources records each of them as its own
entry, so translation sentences, speech hours and exam questions never meet in one total, and a
benchmark's dev and test splits are never added together.

```yaml
capability:
  score: 3
  basis: feature_matrix
  sources:
    - url: https://huggingface.co/datasets/example-org/example-eval
      shows: "the card's per-language table: 1,000 test questions per language"
      accessed: '2026-10-30'
      http_status: 200
      content_sha256: <64 hex>
    - url: https://arxiv.org/pdf/2601.00001
      shows: "Table 2: 997 dev and 1,012 devtest sentences per language; 600 of the 1,000 Hausa
        questions written in Hausa"
      accessed: '2026-10-30'
      http_status: 200
      content_sha256: <64 hex>
  pivot_languages: [eng]
  language_coverage:
    - language: hau
      task: knowledge_exam
      component: example-eval        # the suite's own exam: the product's slug
      split: test
      official_eval: true
      count: 1000
      unit: questions
      provenance: mixed
      qualifying_count: 600
      cites:
        - https://huggingface.co/datasets/example-org/example-eval
        - https://arxiv.org/pdf/2601.00001
    - language: hau
      task: machine_translation
      component: example-mt          # a translation set the suite imports
      split: dev
      official_eval: false           # recorded, and not counted
      count: 997
      unit: sentences
      provenance: human_translated
      cites: [https://arxiv.org/pdf/2601.00001]
    - language: hau
      task: machine_translation
      component: example-mt
      split: devtest
      official_eval: true
      count: 1012
      unit: sentences
      provenance: human_translated
      cites: [https://arxiv.org/pdf/2601.00001]
```

`tests/fixtures/language_coverage/valid.yaml` is the complete worked example: a pivot, a
`mixed` entry, an excluded `machine_translated` entry, a training split, a reviewed `generated`
entry, a documented zero and a mapped entry carrying `source_language`.

### Why it is capability evidence and not an identity attribute

The identity attributes, `languages` among them, are **read by no score, tier, stage or gate**
(`identity.md`). This record will be read by one: the depth ladder (R-2026-10-30-g), described
under [How the depth ladder will read it](#how-the-depth-ladder-will-read-it). What a capability
ladder reads is capability evidence, and it lives on the axis for the same reason
`openness.components` lives on openness.

It also ages like evidence. A dataset that adds languages or a test split changes its counts while
its identity stays put, so the record needs a dated read behind it. On the axis it has one: an entry
cites its sources through `capability.sources`, and **the record's evidence is dated by the
`accessed` date of each source it cites**, with that source's `http_status` and `content_sha256`
beside it. **`capability.last_verified` dates the band, not the coverage record**: it says the score
and its comparison were re-derived on that date ([`evidence-and-freshness.md`](evidence-and-freshness.md)),
and a pass that fills or re-reads the record without re-deriving the band leaves it alone. A product
record carries no `accessed` date and no freshness gate reads it.

### The fields

`pivot_languages` sits on the axis. Every other field is on a `language_coverage` entry. The four
key fields and `official_eval`, `count`, `unit` and `cites` are required on every entry, and
`provenance` on every entry except a documented zero. The schema
(`docs/schemas/score.schema.json`) is the authority on the vocabularies; this section says what each
value means.

| field | what it holds |
|---|---|
| `pivot_languages` | the listed languages the set was not built for: the language its items were translated from, or a high-resource language included for comparison, as English is in most multilingual sets. A declaration rather than a flag on an entry, so a pivot stays identifiable when the source reports no count for it (R-2026-11-01-b). `[]` declares that the set was built for every language it lists. Required with `language_coverage` and allowed without it. Codes follow the `languages` rule, must be listed in the product's `languages`, are sorted, and leave at least one target language. |
| `language` | the ISO 639-3 code, under the rule `languages` follows: scope individual or macrolanguage, no two-letter or special codes. It must be one of the codes the product's `languages` lists. |
| `source_language` | the ISO 639-3 code exactly as the cited source states it, required whenever it differs from `language` and refused when it is the same. Held to the code list, not to the product's `languages`. A two-letter code the source uses is read as its ISO 639-3 equivalent and is no difference. An entry carrying it is an inferred mapping (below). |
| `task` | the one task the entry's items test (below). |
| `component` | the dataset, or the subset within a suite, the count comes from, as a kebab-case slug: the map's product slug when the component has a product of its own, otherwise the source's name for it in kebab case. **A set with one component names itself**: `component` is the product's slug. A suite uses its own slug for the items it contributes and a separate slug for each dataset it imports. |
| `split` | the split the count is taken from, under the source's name for it (below). |
| `official_eval` | `true` when this split is the one the benchmark evaluates on, the only split that counts toward depth. Required, so every entry says whether it counts. |
| `count` | how many items the entry holds, in `unit`, as the cited source states it for this language, task, component and split. Non-negative, and an integer for every unit except `hours`. `0` is a documented zero (below). |
| `unit` | what `count` counts: `items`, `questions`, `sentences`, `documents`, `utterances`, `hours`, `words` or `tokens`, in the unit the source uses. `items` is the generic unit for a test case that is none of the others. |
| `provenance` | how the items came to be in this language (below). Required on every entry except a documented zero, which has no items to describe and so carries none. |
| `qualifying_count` | optional, on a `mixed` entry only: how many of its items the source documents as native, human-translated, post-edited, or machine-translated and then reviewed by people. In the entry's unit and no more than `count`. Absent means the source does not separate that portion. |
| `human_validated` | optional: `true` when the cited source states that people reviewed the items after they were made, `false` when it states they were not. Absent means the source does not say. On a `machine_translated` entry, `true` makes the items count toward depth when `review_scope` is `all_items` (R-2026-11-03-b, -h). |
| `review_scope` | optional, with `human_validated: true`: `all_items` when the cited source says the review covered every item, `unstated` when it describes a review without saying how many items it covered. Absent reads as `unstated`. |
| `subset_of` | optional: the `component` of another entry, for the same language, task and split, whose items contain this entry's. Absent means the source presents the items as distinct. |
| `precision` | optional: a statistical estimate of the evaluation's precision under an approved method, which makes the entry's band estimated rather than provisional. Absent on every entry until a method is approved by ruling; see [Evidence status](#evidence-status). |
| `cites` | the `url` of each `capability.sources` entry that states this entry's figures, `human_validated` and `qualifying_count` included. |

The key is `(language, task, component, split)`. Each key appears once, and entries are sorted by
language, then task, then component, then split, each in plain character order.

**Provenance.** The seven values and their definitions are ruled (R-2026-11-01-e), and so is the
third column (R-2026-11-03-b, replacing R-2026-11-01-h). Provenance is never guessed: a source that does not say is
`unknown`. Three readings follow from that:

- **`native` needs an explicit statement about the items.** Record it only where a cited source
  states that the evaluated items, the text, questions or references being scored, were written by
  people in that language. A source that describes the corpus as news articles, tweets or reviews in
  the language says what genre the text is, not how it came to be in the language; it is enough only
  when the source also states the items are original text written in the language and describes no
  translation or generation.
- **The other qualifying values need the same.** `human_translated` and `post_edited` need a cited
  source that says people translated or corrected the items. A source that says only that the items
  were translated is `unknown`.
- **Sources that disagree give `unknown`.** Where one cited source calls the items native and another
  says they were translated, the entry is `unknown`, cites both, and the sweep record that filled it
  quotes both with their URLs. Neither side is picked silently.

| value | means | counts toward depth |
|---|---|---|
| `native` | human-authored in the target language | yes |
| `human_translated` | translated into the language by people | yes |
| `post_edited` | machine-translated, then corrected by people | yes |
| `machine_translated` | machine-translated, with no human correction recorded | only when `human_validated` is `true` and `review_scope` is `all_items`: the cited source states that people reviewed every item. A review of unstated scope leaves depth unknown, not zero |
| `generated` | model-generated directly in that language | no, reviewed or not |
| `mixed` | more than one of the above in this entry | only its `qualifying_count`, the separately documented qualifying portion; when that is absent, depth is unknown, not zero |
| `unknown` | the source does not say. A recorded state, never a stand-in for `native` | no qualifying depth is established: the language's depth is unknown, not zero |

`native` and `generated` cannot overlap: one is written by people in the language, the other by a
model in it.

**Splits.** Each entry records the split its count comes from (R-2026-11-01-d).

| value | the count is |
|---|---|
| `train` | training examples. Recorded when the source states them, never official, never counted |
| `dev` | the split the source calls dev |
| `validation` | the split the source calls validation |
| `test` | the split the source calls test |
| `devtest` | the split the source calls devtest, as FLORES+ does |
| `official_eval` | an evaluation portion the source names without one of the other words, such as an exam published as one set of test questions. Always official |

**Tasks.** Eighteen classes and `transliteration`, and no narrower labels until the candidate
datasets have been examined (R-2026-11-01-e).

| value | the items test |
|---|---|
| `knowledge_exam` | subject or exam knowledge, usually multiple choice (MMLU-style sets, national exams) |
| `question_answering` | answering a question with no passage supplied |
| `reading_comprehension` | answering from a supplied passage |
| `reasoning` | mathematical, logical or commonsense reasoning |
| `natural_language_inference` | whether one text entails, contradicts or is neutral to another |
| `text_classification` | assigning a label to a text: topic, sentiment, hate speech |
| `sequence_labeling` | labeling spans or tokens: named entities, parts of speech |
| `machine_translation` | translating into or out of the language |
| `transliteration` | rewriting text of the language from one script into another |
| `summarization` | condensing a text |
| `text_generation` | open-ended generation or dialogue not covered by another task |
| `instruction_following` | carrying out a written instruction |
| `retrieval` | finding the relevant document or passage |
| `safety` | toxicity, bias or harmful-content behavior |
| `language_identification` | naming the language of a text or recording |
| `speech_recognition` | transcribing speech |
| `speech_translation` | translating speech |
| `speech_synthesis` | producing speech from text |
| `vision_language` | answering about or describing an image in the language |

A task the list does not name is a schema change, not a new spelling.

### Rules

- **A count is the source's, for this entry.** Never divide a set-wide total across its languages
  (R-2026-10-30-l). A language whose count the card or paper does not state has no entry rather
  than a share.
- **A language with no entry is unknown.** It is not zero, and it is not evidence that the set is
  the strongest available for that language (R-2026-11-01-a). Two sets are comparable only where
  both have documented counts for the same language and task; where no comparable peer has
  documented evidence, the finding is "no comparable evidence", never "best in class".
- **A documented zero is measured.** Where the cited source states that a language has no items
  on a split, as FLORES+ does for a language it carries on its dev split only, the entry records
  `count: 0` with no `provenance` and no `qualifying_count`, and its `cites` names the source that
  states the absence. On the official evaluation split it is a documented zero: a measured zero
  only for the language, task, component and official evaluation split it describes, and not
  unknown there. It says nothing about the rest of the set: it does not imply that the dataset, or
  that language, has no evaluation coverage on another task or in another component. A zero the
  source does not state is no entry, never a documented zero.
- **A code the source does not use is recorded as a mapping.** An entry whose cited source names
  the language with another code (an individual language where the product lists its
  macrolanguage, `cmn` under `zho`, or the reverse) records the source's code in
  `source_language`. Such an entry is an inferred mapping, not a directly observed identity, and it
  flags the product's `languages` for reconciliation: the product lists a code the source does not
  use. The record never changes `languages` to match; that is a curation pass of its own.
  ```yaml
  - language: zho
    source_language: cmn              # FLORES+ carries cmn_Hans and cmn_Hant
    task: machine_translation
    component: flores-plus
    split: devtest
    official_eval: true
    count: 1012
    unit: sentences
    provenance: unknown
    cites: [https://huggingface.co/datasets/openlanguagedata/flores_plus]
  - language: dar
    task: machine_translation
    component: flores-plus
    split: devtest                    # a documented zero: the card marks Dargwa "dev only"
    official_eval: true
    count: 0
    unit: sentences
    cites: [https://huggingface.co/datasets/openlanguagedata/flores_plus]
  ```
- **Only the official evaluation split counts.** `official_eval: true` marks the portion actually
  used for benchmark evaluation. A dev or validation split counts when it is the benchmark's
  official evaluation split, and training examples never count (R-2026-11-01-d).
  `build/validate.py` refuses `official_eval: true` on a `train` split, `false` on the
  `official_eval` split, and two official splits for one language, task and component, so
  FLORES+ translation depth is read from its evaluation split and never from dev and devtest added
  together.
- **Entries are distinct unless one records that it is a subset.** An entry without `subset_of`
  is one whose source presents its items as distinct from every other entry's. An entry whose
  items are drawn from another's names that entry's component in `subset_of`, so the ladder counts
  those items once, within the set that contains them (R-2026-11-01-d). `build/validate.py`
  requires the named entry to exist for the same language, task and split, to carry no
  `subset_of` itself (name the largest set the items are drawn from), and to hold at least as many
  items in the same unit. Record containment only where the source states it. Two components that
  share some items without one containing the other are not containment, and go to the
  maintainer rather than into `subset_of`.
- **Provenance decides what counts, and every entry is recorded.** The third column of the
  provenance table is the rule, with no reduced weights (R-2026-11-03-b). Excluded items stay in
  the record like any other: zero qualifying depth does not mean a set has no evaluation value,
  only that its items do not satisfy this measure of credible evaluation depth. If well-validated
  synthetic evaluations turn out to deserve credit, that is an explicit exception backed by
  evidence, in a ruling, not a multiplier.
- **Human validation is not provenance, and it decides one case.** `human_validated` is cited
  through the entry's `cites` like the rest of the entry. It never changes `provenance`: reviewed
  machine translation stays `machine_translated`, not `post_edited`, and reviewed model-generated
  items stay `generated`, not `native`. It is read toward depth on a `machine_translated` entry
  only, where `true` makes the items count; review of `generated` items does not (R-2026-11-03-b).
  The review has to cover the items: a card that describes "manual review" or "quality control"
  without saying how much of the set it touched records `review_scope: unstated`, and the entry's
  depth is unknown rather than counted or zero (R-2026-11-03-h). On a `mixed` entry, reviewed
  machine-translated items belong to the `qualifying_count`.
- **Availability is not depth.** The official evaluation split counts whether its items are
  public, released on request, or held back for a leaderboard, as long as a source states its size.
  Whether the questions can be downloaded is an openness attribute (R-2026-11-03-a).
- **The citation lives once.** `cites` points at `capability.sources` by URL, and
  `build/validate.py` fails a URL with no matching source. The `shows`, `accessed`, `http_status`
  and `content_sha256` stay on the source, where `check_verification`, `check_refetch` and
  `check_citations` already read them; a second citation list on the record would be one no gate
  sees. Unlike `comparison.sources`, which cites a peer's page, these sources are about this
  product, so they belong on the axis's own list.
- **Valid only on a `type: dataset` product**, both fields, and optional there. An absent
  `language_coverage` means not recorded.
- **It is not in the notebook payload.** `build/serialize.py` leaves `language_coverage` and
  `pivot_languages` out of the capability block. The per-language evidence ships as a separate
  structured data asset that the per-language view loads (R-2026-11-01-f), exposing language,
  task, evaluation split, count and unit, provenance, source references, the observed-coverage
  fraction, and unknowns marked explicitly. That asset is not built.

### How the depth ladder will read it

These are ruled, and they are the rules the ladder PR implements. None of them is built.

1. **Per task, then per language** (R-2026-11-01-c). Each task's qualifying count on its official
   evaluation split is banded against a calibrated standard in that task's own units, and a
   language's task bands aggregate to one language-level band. A suite gets no extra credit for
   importing several datasets that measure the same task. Breadth of evaluated tasks is tracked
   separately and is at most a limited tiebreaker.
2. **The median across the target languages** (R-2026-10-30-i, R-2026-11-01-b). The target
   languages are the product's `languages` less `pivot_languages`. The median of their bands sets
   the band. A capped breadth bonus, starting from median + 0.5 x (1 - 1/n), breaks ties within the
   band and never lifts a set into the next, and it counts only languages with substantiated
   evaluation evidence, so a missing record cannot inflate the result.
3. **The robustness test** (R-2026-11-01-a). A target language with no entry is unknown. The
   median is taken twice, once with every unknown filled at the lowest band and once at the
   highest. The band stands only when the two agree; otherwise the result is unresolved until more
   evidence is collected. Bands of 4, 4 and unknown give 4 whatever the missing value is; 5,
   unknown and unknown cannot establish a 5. There is no completeness threshold.
4. **Completeness is published** (R-2026-11-01-b). Each record states how many of its target
   languages have a usable depth measurement, for example 18 of 20. A target language is measured
   when it has an official-evaluation entry whose qualifying depth is established: `native`,
   `human_translated`, `post_edited`, `machine_translated` or `generated` provenance, `mixed` with
   a `qualifying_count`, or a documented zero. A `machine_translated` entry with
   `human_validated: true` establishes depth only with `review_scope: all_items`
   (R-2026-11-03-h). Measurement is per task: a language is measured on
   each task for which it has such an entry, and only on those. A measured zero comes from
   `machine_translated` items with no stated review and `generated` items, the only provenance
   values that establish one, or from a documented zero, which has no items at all; a documented
   zero makes the language measured,
   at zero, for its own task, component and split only, and leaves every other task where its own
   entries put it. A language whose official-split entries are all `unknown` provenance, `mixed`
   without a `qualifying_count`, or reviewed `machine_translated` whose `review_scope` is not
   `all_items`, is unmeasured: its depth is unknown, and it enters the robustness
   test as an unknown, never as a zero.

### Evidence status

Every depth band says how it was established (R-2026-11-02-e, -t), and the label travels with the
band at every level, task, language and dataset, so a reader can tell a count from a measurement:

- **provisional**: derived from item counts and the task family's stated assumptions. A count band
  is a conservative operational cap under the count method, not a proven bound on precision.
- **estimated**: derived from a task-appropriate statistical procedure, recorded on the entry as a
  `precision` block that meets R-2026-11-02-f.
- **unresolved**: not enough information to assign even a provisional band.

`build/evidence_status.py` decides the status of one coverage entry, in this order:

1. An entry that is not on the official evaluation split has no status; it does not count.
2. **Unresolved** when the entry's qualifying depth is unknown: `unknown` provenance, `mixed`
   without a `qualifying_count`, or `machine_translated` with `human_validated: true` whose
   `review_scope` is not `all_items` (R-2026-11-03-h). An interval never stands in for provenance.
3. **Unresolved** when the task family has no measurement model, or the unit is not one a count
   model reads, a zero included: a family without a model stays unresolved (R-2026-11-02-b, -l). The task families with a count model are machine translation, text
   classification, natural language inference, reasoning, knowledge exams, reading comprehension
   and question answering, prompt-level instruction following, judged generation and
   summarization (R-2026-11-02-e). Sequence labeling and speech are ruled unresolved; language
   identification, retrieval, safety, transliteration and vision-language have no ruling yet and
   stay unresolved until one gives them a model (R-2026-11-02-b). Hours, words and tokens are not
   item counts.
4. **Provisional** for a measured zero (`machine_translated` items with no stated review,
   `generated` items, or a documented zero) in a family with a model: no qualifying items is a
   count-derived fact.
5. **Estimated** when the entry carries a valid `precision` block under an approved method.
6. **Provisional** otherwise.

A `precision` block records what R-2026-11-02-f requires: the approved `method`, the `metric`, the
`resampling_unit`, the `benchmark_version`, the documented `model_selection` rule, the
`evidence_date`, and at least two `runs` from different model families, each with its 95%
`interval` on the 0 to 100 score and its citation; `source_reported` marks intervals taken from the
source without recomputation. The widest run interval sets the estimated band, and every run's
interval stays recorded. The widest interval is the worst precision observed among the chosen
models, not a guarantee across all models: margins of ±2.1 and ±3.4 points give an estimated 3, not
a 4. `build.validate` refuses a block whose method has no approving ruling or is not approved for
the entry's task, with fewer than two model families, with an interval out of order or off the
scale, with an impossible or future evidence date, or citing a URL that is not a capability source.

No method is approved yet. Each task family's procedure needs its own ruling, backed by a
calibration example that compares provisional and estimated bands (R-2026-11-02-f), and the PR that
applies it adds the method to `APPROVED_METHODS` in `build/evidence_status.py`. Until then every
entry is provisional or unresolved. `uv run python -m build.evidence_status <score file>` tallies a
record's entries by status. The depth ladder publishes the status beside each band it derives; that
publication is the ladder PR's, since no band is computed yet.

### What reads it

Nothing yet. The depth ladder (R-2026-10-30-g, R-2026-10-30-i) is not built, so no band moves
because a record was written, and until it lands each evaluation set is compared with sets covering
the same languages (R-2026-10-30-g). The record is filled first for a calibration sample: FLORES+
(translation), ThaiExam (single-language exams), SEA-HELM (a mixed-task suite) and AfroBench (a
large multilingual suite). That sample settles the task-specific depth bands and checks that the
aggregation gives sensible, explainable outcomes before the other evaluation sets are filled
(R-2026-11-01-g). `refresh-category` fills a record from the card or paper it is already reading
for the band ([`../workflows/refresh-category.md`](../workflows/refresh-category.md)).

## Component lineage

Whether two pieces of evidence for one language corroborate each other depends on where their items
came from, so the depth ladder reads lineage from a registry rather than from the coverage entries
(R-2026-11-02-j, -u). `sources/lineage.yaml` holds one cited record per evaluation component, keyed
by the `component` slug the coverage entries use. Lineage describes the evidence, not the suite that
imports it: FLORES+ has one record whether it appears on its own row, inside SEA-HELM or inside
AfroBench. The schema is [`../schemas/lineage.schema.json`](../schemas/lineage.schema.json).

### What a record states

- **`origin`**: `original` (items collected or written for the component, from a collection of
  its own), `derived` (items taken from a parent component or an existing collection: a
  translation, sample, relabeling or re-host) or `unknown` (no source states it).
- **`collections`**: the named collections of underlying source examples the items come from,
  such as FLORES-200's sentences or MMLU's questions. A collection is a specific set of examples,
  never a broad domain.
- **`parents`**: the components this one derives from. The build follows them transitively, so a
  suite that imports SIB-200 is still dependent on FLORES.
- **`effort`**: the effort that produced the component's text in the language, the translation,
  writing or annotation work rather than the research group behind it.
- **`domains`**: broad provenance (wikinews, news) for readers. It never enters the derivation.
- **`overrides`**: language-, split- or task-specific lineage, for a component whose upstream
  source is shared but whose translation or annotation effort differs by language. The override
  whose selectors all match replaces the fields it states. Two overrides of one component that
  could both match some language, split and task are refused, so at most one ever applies and a
  language override cannot silently mask a task one.
- **`curation`**: `curated` when the record was written from its cited sources, `uncurated` for a
  placeholder. Both score as unverified when the facts are missing; the distinction says where
  evidence work should start.
- **`sources`**: citations in the shape score records use, digest required.

`relationships` holds explicit, cited pairwise statements, each with a rationale, for cases the
automatic rules cannot resolve. An explicit relationship takes precedence for the pair, and for the
languages it names.

### How a pair's status is derived

`build/lineage.py` derives one of three statuses for two components on one language
(R-2026-11-02-i). Each component is resolved in its own context, the task and split of its own
coverage entry, because corroboration compares evidence across tasks and often across splits. In
this order:

1. An explicit relationship for the pair decides.
2. Each component's overrides are applied for the language and its own split and task. An
   ancestor reached through `parents` is resolved for the language only, since a parent's split
   and task are not the child's.
3. **Dependent** when either component derives from the other through `parents`, when their source
   collections overlap (each ancestor's collections included), or when they share a creation
   effort. This is checked first, before any gap in provenance, so known dependence decides even
   where a component has no entry or an uncurated one.
4. **Unverified** when provenance is undocumented anywhere in either ancestry: a component or
   ancestor with no entry, an uncurated entry, origin `unknown`, no effort, or no source collection
   either of its own or inherited through a documented parent. The reason names which, because "not
   yet curated" and "origin unknown" both score as unverified but point evidence work in different
   directions.
5. **Independent** otherwise: provenance documented all the way up both ancestries, collections
   disjoint, efforts separate.

Only independent pairs count as backing in the corroboration step (R-2026-11-02-k). A stated
dependence wins over an unknown origin. Shared research authors, a shared domain or corpus provider,
and distinct dataset names do not by themselves decide anything (R-2026-11-02-h, -i). Pair the CLI
with any two slugs to see the status and the rule that set it:
`uv run python -m build.lineage pair flores-plus sib-200 --language hau`, adding `--a-task`,
`--a-split`, `--b-task` and `--b-split` for each side's own context.

### What the build checks, and what it does not

`build.validate` checks the registry's structure: that the file is a mapping (only a missing file
reads as an empty registry), the schema, unique ids, that every parent and
collection exists, that `parents` has no cycle, that no two overrides of a component can both
match, that override tasks are task classes, that a curated record cites sources and that an
`original` or `derived` origin names what it comes from, in the canonical record and under each
override, that override and relationship languages are ISO 639-3 codes, and that no two
relationships for one pair can both apply to a language. The cycle check covers every parent edge
any record or override states, since an override can replace `parents`. Every citation's `accessed`
must be a real ISO date no later than today, the rule score citations follow. It cannot check that a
citation supports the lineage claim; that is evidence review (R-2026-11-02-j). A coverage component
with no registry entry is a warning, never an error, and every pair it is in is unverified, unless
dependence is already known, until the entry is written. The depth ladder is not built, so nothing reads the statuses yet; the lineage audit
fills the registry and reports the sensitivity of each result to unverified pairs before any score
moves (R-2026-11-02-i).

## Writing the rungs

The bands are per category, so somebody writes their definitions, and that writing is where the
axis is won or lost. One rule and one diagnostic.

**Count the products per rung before you accept the wording, and re-read the wording when one
rung is wide.** A wide rung is a PROMPT, not a verdict: sometimes the definition is satisfiable by
almost everything, and sometimes the products really do share a capability. A definition can be
satisfied incidentally, and `storage` is the shape to recognize. "A distributed retrieval platform
that also ranks or runs inference in the serving path" admits Vespa and Elasticsearch and also every
vector database that fuses scores, since Qdrant has RRF and DBSF, Infinity has tensor reranking and
Milvus has rerank functions. "Hosts and evaluates ranking or embedding models inside the serving
path" admits the ones that host a model. The products are the same under either wording; the second
stops admitting products whose only qualifying feature is score fusion. The distribution is the
diagnostic, and it costs one query.

**A width threshold does not decide the question, and must not be written as if it did.** Two
things produce a wide rung and a count cannot tell them apart: a definition loose enough that
nearly everything satisfies it, and a category whose products genuinely share a capability. The
first is a defect in the wording. The second is a fact about the world, and splitting it would mean
recording a distinction no evidence supports - which is the error this whole document exists to
prevent, arriving from the other direction. What made `storage`'s wide rung wrong was found by
reading the definition against the products, not by comparing a percentage to a constant.

A wide rung is also ordinary rather than exceptional, so a threshold read as a verdict would
condemn most of the map. Measured 2026-09-20: of the 23 categories with at least one banded
product, 21 have a widest rung above a third, the median widest rung is 50%, and the range runs
from `base_pretrained` at 28% to `document_conversion` at 83%.

**A wide rung still triggers a review, and the review has to leave a record.** Above a third is the
trigger, kept as a number so it fires the same way for everyone. What it demands is not a
redistribution but an entry in the category's `scoring_recipe.note` carrying four things: the count
and its denominator, the rung's wording as it stands, which of the two cases this is, and the
evidence for that reading - the reword, if the definition generalized, or what the products actually
share, if they cluster. A reword is re-counted afterwards, because the point of rewording is to move
the distribution and an unverified reword has not been shown to.

`document_conversion` is the clustering case and reports it that way: 15 of its 18 banded products
recover reading order, tables and formulas into Markdown or JSON, the ends of the ladder are narrow
by construction, and the differences inside the middle are input breadth against structure depth,
which trade off against each other and which vendor feature lists cannot order. (Counts measured
2026-09-20; re-run the count against the category rather than quoting them.)

**Prefer a definition stated as a capability the product either has or has not, over one stated as
an outcome.** "Ranks results" is an outcome, and outcomes generalize until they are vacuous -
everything ranks results, that is what retrieval is. "Hosts a model" is a capability: it is
checkable against a repository tree, it either ships an inference plugin or it does not, and two
reviewers reading the same evidence reach the same answer. The same move works in the other
direction: `compilers` bands on how much of the model-to-hardware transformation a product
performs, which is why a kernel library tops out at 3 there - it supplies the primitives a compiler
targets and transforms nothing itself. That is a fact about the product, not a judgment about its
quality.

A corollary for the evidence: **`basis_detail` is per product, never per cluster.** One harness
name written across a group of products reads as a shared measurement, and the shared measurement
usually does not exist. `ANN-Benchmarks` over the vector databases in `storage` is the case:
Pinecone is not in it at all, and Milvus and Qdrant are listed but the harness publishes
recall-versus-QPS plots with no ranking table, so it corroborates their inclusion while their
headline numbers come from their vendors' own harnesses. **Moving a product between categories
re-opens the instrument, not just the band.**

## What it does not do

- **It is not routable from signals.** `signal_routing.yaml` records the axis as effectively
  unroutable: the external anchors (Artificial Analysis, LMArena) rank *models*, so neither
  can say anything about a training framework or a sandbox. A fetch can re-derive a
  `benchmark` band; a `feature_matrix` or internal-eval judgment needs a human read.
- **It does not take an anchor from a leaderboard without current cross-model coverage.**
  METR's task-completion time horizons are not an anchor while the time-horizon page is frozen
  and lacks current open-weight coverage; a maintained successor with representative current
  coverage would reopen the question. Standalone long-context suites (RULER, NoLiMa, LongBench
  v2, Fiction.LiveBench, OpenAI-MRCR, HELM Long Context) are not map-wide anchors, because none
  has current-release, independently maintained cross-model coverage; one that becomes a
  current independent leaderboard would reopen it. In both cases a result for the exact release
  a record reads stays valid per-product evidence.
- **`value` is not structured into components.** Most of the field is prose, on the same measure
  that stopped `edge_hardware`'s ladder, and four instruments share the one field, so there is no
  shared ladder at the end of that work the way openness has four. The peer comparison, not a
  component structure, is what is checkable instead.

## Checklist

- [ ] `score` is 1-5 and comparable only within the category, or null with `basis: n/a`.
- [ ] `basis` names the instrument; `basis_detail` and `value` carry what it was and what it said.
- [ ] `basis_detail` names the instrument for THIS product - not one inherited from a cluster of
      peers, and not a harness the product is absent from.
- [ ] A new or reworded rung was checked against its own distribution. A rung above a third of the
      category is reworded and re-counted, or reported in the recipe note with the count, the
      denominator, the wording, and the evidence that the products genuinely share the capability
      (see "Writing the rungs").
- [ ] A comparison-placed band records `relative_to` (same category) and `relation`, and the
      arithmetic holds against the peer's score.
- [ ] A non-null score cites at least one source.
- [ ] A `language_coverage` record, if present, names only codes in the product's `languages`,
      records the source's own code in `source_language` wherever it differs, has one entry per
      language, task, component and split, takes each count from the cited source rather than
      dividing a total, records a source-stated absence as a documented zero, marks the one
      official evaluation split, records subsets with `subset_of`, marks `native` only on an
      explicit statement about the items, declares `pivot_languages`, and cites URLs that are on
      `capability.sources`.
- [ ] `last_verified`, if present, satisfies the transitive-freshness rule — or the edge carries
      a `comparison` block whose `last_attested` is no earlier than it and is backed by a fetched
      source read on or after that date.

## Related

- `docs/reference/evidence-and-freshness.md` — how a capability band earns its date, and the gates
- `docs/reference/openness.md` — the openness axis, whose `establishes` this axis's `relation` mirrors
- `docs/reference/adoption.md` — the adoption axis, the other banded judgment
