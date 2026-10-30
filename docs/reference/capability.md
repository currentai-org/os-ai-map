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
| `language_coverage` | per-language evidence for an evaluation set: count, unit, provenance, tasks and pivot for each language, cited through `sources`. Optional, datasets only. See [Per-language coverage](#per-language-coverage). |
| `confidence` | the curator's certainty (`high`/`medium`/`low`). Note it does not encode the strength of the instrument — a `high` can sit on a feature-matrix judgment with no measurement under it. |
| `note` | the prose behind the band: what the product does well, what it sits below, and against whom. |
| `sources` | the evidence, at least one for a non-null score. |
| `last_verified` | the date the whole axis was last re-confirmed. See `evidence-and-freshness.md`. |

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
per language or fifty machine-translated ones. `capability.language_coverage` records it, one entry
per language, cited to the card or paper (R-2026-10-30-h).

```yaml
capability:
  score: 3
  basis: feature_matrix
  sources:
    - url: https://huggingface.co/datasets/example-org/example-eval
      shows: "the card's per-language table: 1,000 test questions in each language"
      accessed: '2026-10-30'
      http_status: 200
      content_sha256: <64 hex>
  language_coverage:
    - language: eng
      count: 1000
      unit: questions
      provenance: native
      tasks: [knowledge_exam]
      pivot: true
      cites: [https://huggingface.co/datasets/example-org/example-eval]
    - language: swh
      count: 1000
      unit: questions
      provenance: human_translated
      tasks: [knowledge_exam]
      pivot: false
      cites: [https://huggingface.co/datasets/example-org/example-eval]
```

### Why it is capability evidence and not an identity attribute

The identity attributes, `languages` among them, are **read by no score, tier, stage or gate**
(`identity.md`). This record will be read by one. The depth ladder (R-2026-10-30-g) bands an
evaluation set on the median per-language depth across the languages it was built for, leaving out
pivot languages, with a capped breadth bonus that breaks ties within a band and never lifts a set
into the next (R-2026-10-30-i). What a capability ladder reads is capability evidence, and it lives
on the axis for the same reason `openness.components` lives on openness.

It also ages like evidence. A dataset that adds languages or a test split changes its counts while
its identity stays put, so the record needs a dated read behind it. On the axis it has one: an entry
cites its source through `capability.sources`, and `capability.last_verified` claims that
everything on the axis, this record included, was re-read on that date
([`evidence-and-freshness.md`](evidence-and-freshness.md)). A product record carries no
`accessed` date and no freshness gate reads it.

### The fields

Every field is required on an entry. The schema (`docs/schemas/score.schema.json`) is the
authority on the vocabularies; this section says what each value means.

| field | what it holds |
|---|---|
| `language` | the ISO 639-3 code, under the rule `languages` follows: scope individual or macrolanguage, no two-letter or special codes. It must be one of the codes the product's `languages` lists. Entries are sorted by code and name each language once. |
| `count` | how many items the set holds in this language, in `unit`, as the cited source states it for this language. Non-negative, and an integer for every unit except `hours`. |
| `unit` | what `count` counts: `items`, `questions`, `sentences`, `documents`, `utterances`, `hours`, `words` or `tokens`, in the unit the source uses. `items` is the generic unit for a test case that is none of the others. |
| `provenance` | how the items came to be in this language (below). |
| `tasks` | the tasks this language's items fall under (below). A suite whose tasks cover different languages lists, for each language, only the tasks that language takes part in. |
| `pivot` | `true` when the set was not built for this language: it is the language the items were translated from, or a high-resource language included for comparison, as English is in most multilingual sets. The ladder leaves pivots out of the median. Required, so every entry says which side of the line it is on. |
| `cites` | the `url` of each `capability.sources` entry that states this language's figures. |

**Provenance.**

| value | means |
|---|---|
| `native` | written in the language, not translated from another |
| `human_translated` | translated into the language by people |
| `post_edited` | machine-translated, then corrected by people |
| `machine_translated` | machine-translated, with no human correction recorded |
| `generated` | produced by a model in the language rather than translated |
| `mixed` | more than one of the above, for this language |
| `unknown` | the source does not say. A recorded state, never a stand-in for `native` |

**Tasks.**

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

- **A count is the source's, for this language.** Never divide a set-wide total across its
  languages. A language whose count the card or paper does not state is left out of the record
  rather than given a share. A language absent from the record has no recorded depth; the ladder
  PR decides what that means for the band.
- **The citation lives once.** `cites` points at `capability.sources` by URL, and
  `build/validate.py` fails a URL with no matching source. The `shows`, `accessed`, `http_status`
  and `content_sha256` stay on the source, where `check_verification`, `check_refetch` and
  `check_citations` already read them; a second citation list on the record would be one no gate
  sees. Unlike `comparison.sources`, which cites a peer's page, these sources are about this
  product, so they belong on the axis's own list.
- **Valid only on a `type: dataset` product**, and optional there. Absent means not recorded.
- **It is not in the notebook payload.** `build/serialize.py` leaves it out until the per-language
  view (R-2026-10-30-i) defines how it ships.

### What reads it

Nothing yet. The depth ladder (R-2026-10-30-g, R-2026-10-30-i) is not built, so no band moves
because a record was written, and until it lands each evaluation set is compared with sets covering
the same languages (R-2026-10-30-g). `refresh-category` fills the record on an evaluation set's next
pass, from the card or paper it is already reading for the band
([`../workflows/refresh-category.md`](../workflows/refresh-category.md)).

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
      takes each count from the cited source for that language rather than dividing a total, marks
      pivot languages, and cites URLs that are on `capability.sources`.
- [ ] `last_verified`, if present, satisfies the transitive-freshness rule — or the edge carries
      a `comparison` block whose `last_attested` is no earlier than it and is backed by a fetched
      source read on or after that date.

## Related

- `docs/reference/evidence-and-freshness.md` — how a capability band earns its date, and the gates
- `docs/reference/openness.md` — the openness axis, whose `establishes` this axis's `relation` mirrors
- `docs/reference/adoption.md` — the adoption axis, the other banded judgment
