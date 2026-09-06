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
- **`feature_matrix`** — a judgment over what the product does. The dominant basis: measured
  2026-08-08, 322 of 472 products sit here.
- **`training_value`** — ablation or downstream-model evidence that a dataset or recipe
  improves what is trained on it (`basis_detail` names it `ablation` or `superseded`).
- **`n/a`** — an honest abstention. By convention it pairs with a null score, but nothing gates
  that pairing today, so the corpus is not uniform (e.g. `lamini` carries `score: null` under
  `basis: feature_matrix`). Treat `score: null` + `basis: n/a` as the intended shape for an
  abstention until a gate enforces it.

## The real instrument is a peer comparison

Many bands are not measured at all. As of 2026-08-14, 114 products record a peer comparison
(with perhaps another ~36 candidates that still live in prose) — "one tier below the Megatron-LM
anchor", "mid-tier next to langfuse" — and in `finetuning_code` every note does it.
Peer comparison is **a major capability instrument**, not demonstrably most of the axis, and until
2026-08-08 it lived inside an English sentence where nothing could check it, refresh it, or notice
when the product it named moved.

`relative_to` and `relation` record it as data:

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
`build/check_capability.py` then asks the three questions a recorded comparison makes
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

The gate ratchets like the others — it covers the products that record a comparison and does
not block the ones that do not.

### Dating the edge itself

Transitive freshness as written binds the dependent's **whole-axis** date to the peer's
**whole-axis** date, and those are two claims about two different products. The consequence
shows up as the corpus grows: every new product's natural peer was confirmed before the
product existed, so a tranche can compare its own members to each other and to nothing else.
That happened three times in one week in August 2026, and the comparisons were dropped into
prose rather than asserted on a re-derivation nobody performed.

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

In exchange, the peer's whole-axis date no longer bounds the dependent's. Where the peer *has*
been re-read since the spacing was judged, `check_capability` reports the edge rather than
failing it: the arithmetic check already fires if the peer's score moved, and this catches the
case where its `value` moved and its score did not.

One fetch attests every edge against the same peer, so a tranche pays per peer rather than per
product. And an attestation may not re-date the peer's own `capability.last_verified` as a side
effect — unless the read happened to cover every source that axis cites, in which case the peer
really has been re-derived and the curator may date it. Nine of thirteen peers in the August
backlog cited exactly one source, so that is common rather than exotic.

### Do not force every comparison through the category anchor

`relative_to` may name **any sufficiently well-supported peer in the same category** — it is not
required to be whatever product the category compares against most often. For a distant band,
prefer a nearer peer whose capability is independently evidenced over stretching the relation
vocabulary to reach the anchor.

The corpus already works this way. `pinecone` is recorded `at milvus`, not against `vespa`,
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

On 2026-08-31 `langfuse` was named by 22 records and `openhands` by 25, and neither recorded a
`value`. The arithmetic invariant held on all 47 bands — a `one_below` against a 4 really was a
3 — so `check_capability` was green while the thing being compared to was unstated. **Consistent
is not correct.** Recording `openhands`'s surface then exposed a second problem the bands
predated: its README now leads with a control centre that runs third-party agents, so "runs
somebody else's loop" had quietly stopped being the low-rung discriminator nine bands in that
category rested on. Nothing could notice the product had moved, which is the exact failure
recording comparisons as data was meant to prevent.

`build/check_capability.py` reports weak roots with their fan-out, so remediation runs in the
order that clears the most dependent bands.

## Writing the rungs

The bands are per category, so somebody writes their definitions, and that writing is where the
axis is won or lost. Two rules, both learned on 2026-08-18 while banding `compilers` and `storage`.

**Count the products per rung before you accept the wording.** A rung holding a third of the
category is not discriminating between anything; it is a label. `storage`'s top rung was first
written as "a distributed retrieval platform that also ranks or runs inference in the serving
path", which on that day admitted seven of the twenty-seven products then in the category - Vespa
and Elasticsearch, but also every vector database that fuses scores, since Qdrant has RRF and DBSF,
Infinity has tensor reranking and Milvus has rerank functions. Reworded to "hosts and evaluates
ranking or embedding models inside the serving path" it admitted two. Nothing about the products changed; the definition stopped being
satisfiable by almost all of them. The distribution is the diagnostic, and it costs one query.

**Prefer a definition stated as a capability the product either has or has not, over one stated as
an outcome.** "Ranks results" is an outcome, and outcomes generalize until they are vacuous -
everything ranks results, that is what retrieval is. "Hosts a model" is a capability: it is
checkable against a repository tree, it either ships an inference plugin or it does not, and two
reviewers reading the same evidence reach the same answer. The same move works in the other
direction: `compilers` bands on how much of the model-to-hardware transformation a product
performs, which is why a kernel library tops out at 3 there - it supplies the primitives a compiler
targets and transforms nothing itself. That is a fact about the product, not a judgment about its
quality.

A corollary for the evidence: **`basis_detail` is per product, never per cluster.** Three products
moved into `storage` carrying `basis_detail: ANN-Benchmarks` from their old category, and it was
wrong on all three - Pinecone is not in ANN-Benchmarks at all and its own note said so, while
Milvus and Qdrant are listed but the harness publishes recall-versus-QPS plots with no ranking
table, so it corroborates inclusion while their headline numbers come from their vendors' own
harnesses. One name for a group of products reads as a shared measurement that does not exist.
**Moving a product between categories re-opens the instrument, not just the band.**

## What it does not do

- **It is not routable from signals.** `signal_routing.yaml` records the axis as effectively
  unroutable: the external anchors (Artificial Analysis, LMArena) rank *models*, so neither
  can say anything about a training framework or a sandbox. A fetch can re-derive a
  `benchmark` band; a `feature_matrix` or internal-eval judgment needs a human read.
- **`value` is not structured into components.** At 61% prose by `check_rubric`'s own measure,
  against the 71% that stopped `edge_hardware`, and with four instruments sharing one field,
  there is no shared ladder at the end of that work the way openness got four. The peer
  comparison, not a component structure, is what was made checkable instead.

## Checklist

- [ ] `score` is 1-5 and comparable only within the category, or null with `basis: n/a`.
- [ ] `basis` names the instrument; `basis_detail` and `value` carry what it was and what it said.
- [ ] `basis_detail` names the instrument for THIS product - not one inherited from a cluster of
      peers, and not a harness the product is absent from.
- [ ] A new or reworded rung was checked against its own distribution: no rung quietly holds a
      third of the category (see "Writing the rungs").
- [ ] A comparison-placed band records `relative_to` (same category) and `relation`, and the
      arithmetic holds against the peer's score.
- [ ] A non-null score cites at least one source.
- [ ] `last_verified`, if present, satisfies the transitive-freshness rule — or the edge carries
      a `comparison` block whose `last_attested` is no earlier than it and is backed by a fetched
      source read on or after that date.

## Related

- `docs/reference/evidence-and-freshness.md` — how a capability band earns its date, and the gates
- `docs/reference/openness.md` — the openness axis, whose `establishes` this axis's `relation` mirrors
- `docs/reference/adoption.md` — the adoption axis, the other banded judgment
