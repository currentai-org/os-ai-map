# Language depth methodology: cross-task bands, imported benchmarks and task aggregation, 2026-11-02

**Status: research record.** None of its recommendations is adopted. Each decision listed in
[Decisions](#decisions) takes effect only through a ruling recorded in `docs/rulings/log.yaml`, and
until then the rules in force are the ones `docs/reference/capability.md` cites. Where this brief
says a set "gets" or "would get" a band, it reports what an option computes on the records, not a
band the map uses.

**Revision 2026-11-02.** Revised the same day, in review and before merge. What changed:

- **Q1 no longer proposes one count ladder as the measure.** It proposes shared band meanings
  (what a band 1 to 5 says, in words and as a target resolution) and a measurement model per task
  family that says how evidence reaches a band. The count ladder of the first draft is kept as the
  provisional proxy where item counts suit the metric, and the brief says, task family by task
  family, where they do not (clustered exams and passages, corpus-level translation metrics,
  judged generation, speech) and what is assumed in each case.
- **The corroborated maximum is kept as a candidate and retested** under a written definition of
  independent evidence. Under it AfroBench is unresolved (1 to 3), not 3; the maintainer is not
  adopting AfroBench at 3. The definition was written from the records' cited lineage, not fitted
  to any band.
- **Within-task aggregation (D12)** is specified with options and a recommendation.
- **Decisions** carry a status. D3, D4, D6, D8, D9, D10 and D11 are supported in principle by the
  maintainer, not yet ruled; D1, D2, D5, D7 and D12 are deferred. The maintainer agrees with the
  treatment of imported benchmarks (Q2).
- **Two corrections.** SEA-HELM's two criteria-judged sets (`sea-mt-bench-judge`, `kalahi-judge`)
  are SEA-HELM's own items, named with a second slug only because the schema cannot give a suite
  two own components in one task (calibration record, item 7); the first draft counted them as
  imported. Its own items therefore measure 8 of 11 target languages, not 6; no band in any table
  moves. And "summing distinct components changes nothing" was true of set bands only: it raises
  two SEA-HELM languages (D12).

This brief takes up the three questions issue #953 left for the ladder PR ("Decide in the ladder
PR"): what a depth band means across tasks, how a suite's imported benchmarks count, and how a
language's task bands become one language band. It compares options on the four calibration records
(FLORES+, ThaiExam, SEA-HELM, AfroBench) and on three large single-language exams that have no
records yet (ArabicMMLU, the Khayyam Challenge, VMLU).

It evaluates and recommends. It changes no score, record, recipe, schema or roster. Like the other
records in `docs/briefs/`, it describes the corpus on the date above and is refreshed by a new
brief, not edited after merge. Inputs are on `main` at the same date: the records in
`sources/scores/`, the calibration dry run in `docs/sweeps/2026-11-01-language-depth-calibration.md`,
the "Per-language coverage" section of `docs/reference/capability.md`, and rulings R-2026-10-30-g,
-i, -l and R-2026-11-01-a to -i.

**Method.** One script read the four records and applied every combination of options below. The
same script, given the calibration's ladders and rules, reproduces the calibration's hand-run
exactly (4, 3, 4, 4 under the highest task band; 4, 3, 3, 3 under the median; SEA-HELM 3 and
AfroBench unresolved, 0 to 5, without borrowed rows), so the differences below come from the
options and not from the arithmetic. Reference benchmark sizes were chosen by a fixed rule before
any result was computed ([Appendix A](#appendix-a-the-ladders-and-their-references)), and nothing
was adjusted afterward to move a set toward its current band. For the revision, a second script
reads the same records, reproduces every corroborated-maximum result of the first draft before
applying the independence definition, and computes the within-task options of D12. Every count in
the revision comes from the records or from a source already cited on them.

## The short answer

1. **A band should mean the same thing on every task; the item count that earns it need not be the
   same.** Proposed meanings: a band says how finely a set resolves a model's score in one language
   on one task, against the sampling of items: about ±10 points at band 2, ±5 at 3, ±2.5 at 4 and
   ±1.25 at 5. Each task family then needs its own measurement model for how its evidence reaches
   that resolution. The count ladder (100, 400, 1,600 and 6,400 items start bands 2 to 5) is that
   model only for independent items scored on a bounded scale, and is proposed as a provisional
   proxy where counts suit the metric. Clustered items (exam questions sharing a stem, reading
   questions sharing a passage, translation sentences sharing an article) earn less than their
   count, and judged sets earn at most their count. The field-standard alternative, anchoring each
   task on its well-known benchmarks, gives results that flip with the choice of reference.
2. **The band would measure the evaluation resource, not originality.** Imported items count.
   Whether an item is the product's own, imported, or imported from a set with its own row on the
   map is recorded and published beside the band, and enters the score at one point only: the
   aggregation across tasks. The maintainer agrees with this treatment.
3. **Task to language: the corroborated maximum, tested under a definition of independence.** A
   language's band would be its best task band, except that a band resting on one imported task
   sits at most one band above the best evidence that is independent of it. Two pieces of evidence
   are independent only if their items are distinct (no shared or common source text), their
   creators are distinct, and neither derives from the other. FLORES+, SIB-200 and Belebele share
   FLORES sentences, so under this definition they would not corroborate one another.

Under these candidates, on the count ladder, the four calibration sets compute to **FLORES+ 3,
ThaiExam 3, SEA-HELM 2, and AfroBench unresolved (1 to 3)**. Twenty-seven of AfroBench's languages
are measured only on FLORES sentences and sets built from them, and fall from 3 to 1 under the
independence definition; the set would stand at 3 only if at least eight of its nine unmeasured
languages came in at 3 or above. ArabicMMLU and the Khayyam Challenge compute to 5 on their counts.
VMLU is unresolved, because no source states its test split.

**Stable across every option tested:** no calibration set reaches 5; all four fall from their
current bands; FLORES+ is a 3 on its count unless its own devtest is the anchor for the translation
ladder; the large native exams never rank below FLORES+. **Dependent on one choice:** ThaiExam on
the ladder (Q1) and on how its questions cluster, which no source states; SEA-HELM on the
aggregation rule (Q3, and the ladder); AfroBench on whether imported items count (Q2) and on the
definition of independent evidence (D7). **Not established:** whether FLORES+ keeps its 3 once its
1,012 devtest sentences are treated as 281 articles (it does unless sentences within an article are
strongly correlated, [Clustering](#how-much-clustering-each-count-can-absorb)).

## Q1. What a band means across tasks

The calibration's ladders mix two rationales: statistical precision for accuracy-scored tasks, and
conventional benchmark sizes for translation and judged prompts. So a 4 in translation (1,000
sentences) and a 4 in classification (1,600 items) are different claims. The first draft of this
brief made them the same claim by giving every bounded metric one count ladder. That treats the
ladder as the measure. It is better read as one measurement model among several, valid under
assumptions that some tasks meet and others do not. This section separates the two: what a band
means, which is shared, and how evidence reaches it, which is not.

### Band meanings

A band describes one language on one task. The uncertainty it refers to is item sampling: how far a
model's score could move on a different draw of comparable items from the same kind of source. It
is not run-to-run noise in the model, and it says nothing about whether the task is the right test
of the language; provenance (R-2026-11-01-h) and task coverage carry that.

| Band | Meaning, shared across tasks | Target 95% half-width, on a 0 to 100 metric |
|---|---|---|
| 0 | No qualifying items on the official evaluation split (a measured zero) | none |
| 1 | Qualifying items exist. A score shows whether a model works in the language on this task, and does not reliably separate models of similar quality | wider than ±10 |
| 2 | Coarse: separates models only when they differ by a wide margin | about ±10 |
| 3 | Moderate: separates models that differ by several points | about ±5 |
| 4 | Fine: separates models that differ by a few points | about ±2.5 |
| 5 | Very fine: resolves differences of about a point, and leaves room to report sub-areas (subjects, domains) at a coarser band | about ±1.25 |

The half-widths halve at each band, so each band asks for four times the effective evidence of the
one below. They are the first draft's ladder restated as a meaning instead of a count. Whether these
are the right resolutions to ask of a language evaluation set is part of D1; nothing in the sample
tests that.

### From evidence to a band

For a score that is the mean of n independent per-item scores bounded on 0 to 1, the standard error
is √(V/n), where V is the per-item variance, at most 0.25. For accuracy, V = p(1 − p) at a model
accuracy p. The 95% half-width is 1.96 √(V/n), so reaching a target half-width h needs

> n_eff ≥ 1.96² V / h², which is 96, 384, 1,537 and 6,147 at V = 0.25 and h = 10, 5, 2.5 and 1.25
> points.

Rounded, those are the count ladder's 100, 400, 1,600 and 6,400. Three assumptions make the raw
count n the right input:

- **Bounded per-item scores (V ≤ 0.25).** Established for accuracy, prompt-level instruction
  following, rescaled judge scores and sentence-level chrF. It fails for word error rate, which
  insertions can push above 1.
- **Worst-case variance.** An assumption, and a conservative one. At p = 0.9 the variance is 0.09,
  so the same n resolves the score about 40% more finely than the band says. A measured variance
  would raise bands; it would come from per-item scores of published model runs (D2).
- **Independent items (n_eff = n).** The assumption most often wrong. Items that share a passage,
  an article, a question stem or a subject sampled as a group are correlated. With clusters of
  average size m and intra-cluster correlation ρ, the design effect is DEFF = 1 + (m − 1)ρ and
  n_eff = n / DEFF. For 0 ≤ ρ ≤ 1 this puts n_eff between the number of clusters k = n/m and n, so
  **the band of the cluster count and the band of the item count bound the band from below and
  above**, whatever ρ is. That bound needs only the cluster count, which sources sometimes state;
  ρ needs per-item model outputs, which no record has.

One distinction matters for exams. A subject is a cluster only if the set's claim generalizes beyond
the subjects it holds; if the subjects define what the set measures (these five national exams,
these listed subjects), they are strata, and stratified sampling does not inflate the variance. The
records do not say which reading a set intends, so this brief treats subjects as strata and passages
and shared stems as clusters.

### By task family

Whether the raw count is a suitable proxy, and why. "Established" means it follows from the metric's
definition; "assumed" means it holds only if the stated condition does.

| Task family | Unit and metric | Is the item count a suitable proxy? | What it rests on |
|---|---|---|---|
| Classification, NLI, single-question reasoning (XNLI, XCOPA, SIB-200, MGSM, InjongoIntent) | items, accuracy | **Yes**, provisionally | Established: binary items, V ≤ 0.25. Assumed: items independent. SIB-200's sentences come from FLORES articles, so they cluster as FLORES does |
| Knowledge exams (ThaiExam, AfriMMLU, MMMLU, ArabicMMLU) | questions, accuracy | **Yes, with a design effect** where questions share a stem, passage or source document | Subjects read as strata. ThaiExam's sources do not say how its 565 questions group; AfriMMLU covers five subjects |
| Reading comprehension (Belebele, XQuAD, TyDi QA) | questions on shared passages, accuracy | **Only between bounds:** the passage count and the question count | Established where the passage count is stated: Belebele has 900 questions on 488 passages, both band 3, so its band holds for any ρ. Not stated for SEA-HELM's 100-question samples |
| Machine translation, corpus chrF | sentences, ratio of summed character n-gram statistics | **Yes, through a stated relation** | To first order (delta method) corpus chrF behaves as a length-weighted mean of sentence contributions, so its worst-case half-width is 0.98/√n_len with n_len = (Σℓ)²/Σℓ² ≤ n, ℓ the sentence length. Sentences drawn several per article cluster: FLORES devtest is 1,012 sentences from 281 articles. The worst case overstates the width, since sentence-level chrF varies far less than 0.25 |
| Machine translation, corpus BLEU | sentences, geometric mean of clipped n-gram precisions with a brevity penalty | **No closed form.** Its interval comes from bootstrap resampling of sentences | The sentence count bounds the chrF interval on the same sentences, so it serves as the proxy for a set whichever metric it reports; a calibrated band would come from bootstrap intervals on released system outputs |
| Instruction following, prompt-level (SEA-IFEval) | prompts, pass or fail | **Yes** | Established: one binary outcome per prompt. Instruction-level accuracy clusters several instructions in one prompt and would need the prompt count, not the instruction count |
| Judged generation (SEA-MTBench, MT-Bench Thai) | prompts, judge score or win rate | **As a ceiling only** | With one judgment per prompt on a bounded scale, 0.25/n bounds the random error of prompt sampling and judge noise together. It does not cover judge bias, which more prompts do not reduce, or whether the judge is valid in the language. Multi-turn prompts are clusters of turns. A count band says the most such a set could resolve |
| Summarization (XL-Sum samples) | documents, ROUGE or a judge | **Yes for precision**, provisionally | Bounded per-document scores on independent articles. Whether ROUGE measures summary quality in the language is a validity question the band does not answer |
| Sequence labeling (MasakhaPOS, MasakhaNER-X) | sentences recorded, span or token F1 scored | **No, as recorded** | F1 is a ratio over entities or tokens, which cluster in sentences; the record's unit is sentences. None of the sample's entries qualifies, so nothing moves |
| Speech recognition and translation | hours or utterances, word error rate | **No** | WER is unbounded above, and errors cluster by speaker. Hours stand in for words, not speakers. Needs its own model and a speech set in the calibration (D3) |

### How much clustering each count can absorb

No record gives ρ, so no design effect can be computed. What can be computed is the largest design
effect a count can absorb before it drops a band (n divided by the band's threshold), and, where a
source states the cluster count, the band it cannot fall below.

| Component | Qualifying items per language | Count band | Largest DEFF that keeps it | Clusters stated by a source | Band floor from the clusters |
|---|---|---|---|---|---|
| Khayyam Challenge | 20,192 | 5 | 3.15 | no | none |
| ArabicMMLU | 14,455 | 5 | 2.26 | no | none |
| OpenAI MMMLU (AfroBench) | 14,042 | 5 | 2.19 | no | none |
| NTREX-128 | 1,997 | 4 | 1.25 | document boundaries exist; the count was not read | none |
| FLORES+ devtest | 1,012 | 3 | 2.53 | 281 articles (FLORES-101 paper, Table 3) | 2 |
| XNLI, IndoNLI, 1,000-item classification (SEA-HELM) | 1,000 | 3 | 2.50 | no | none |
| Belebele | 900 | 3 | 2.25 | 488 passages (Belebele paper) | 3 |
| InjongoIntent | 640 | 3 | 1.60 | no | none |
| AfriXNLI | 600 | 3 | 1.50 | no | none |
| ThaiExam | 565 | 3 | 1.41 | five exams, read as strata | none |
| AfriMMLU, XCOPA | 500 | 3 | 1.25 | AfriMMLU: five subjects, read as strata | none |
| SIB-200 | 204 | 2 | 2.04 | drawn from FLORES articles; count not stated | none |
| SEA-IFEval | 105 | 2 | 1.05 | no | none |
| XQuAD, TyDi QA, IndicQA samples (SEA-HELM) | 100 | 2 | 1.00 | no | none |

What the table shows:

- **FLORES+'s 3 is robust but not guaranteed.** With 3.6 sentences per article, it keeps band 3 up
  to ρ ≈ 0.59 even at the worst-case variance, and falls to 2 only above that. Its floor is 2.
- **Belebele's 3 holds for any correlation**, because its 488 passages alone clear 400.
- **Sets just above a threshold are the most exposed.** ThaiExam (1.41), AfriMMLU and XCOPA (1.25),
  NTREX-128 (1.25) and SEA-HELM's 100-item and 105-prompt samples (1.00, 1.05) drop a band at modest
  design effects. The first draft said clustering "does not reorder" the sample. That is not
  established: it would reorder sets whose clustering differs, and the records cannot yet say
  whose does.
- **The large exams have room.** ArabicMMLU, MMMLU and Khayyam keep 5 up to a design effect of 2.2
  to 3.2.

### The count ladder against field-standard anchors

The first draft compared two ways to put every task on one scale, and the comparison stands as a
record of why a per-task reference anchor was not proposed:

- **(a) The count ladder (worst-case precision).** One ladder for every bounded metric: 1, 100, 400,
  1,600, 6,400. It is the measurement model above under its three assumptions.
- **(b) Field-standard sizes.** Each task's ladder is anchored on its well-known benchmarks. The
  rule applied here: for each task, take three references (an English flagship and the two
  most-used multilingual sets), anchor band 4 at their median per-language evaluation size R, and
  keep (a)'s spacing, so band 2 starts at R/16, band 3 at R/4 and band 5 at 4R. The difference from
  (a) is then only the anchor. Appendix A lists the references and their fetched sizes.

Bands under each ladder, with the candidate aggregation of the first draft (corroborated maximum,
distinct tasks counted as independent) held fixed. The calibration's mixed ladders are the first
row, for reference.

| Ladder | FLORES+ | ThaiExam | SEA-HELM | AfroBench | ArabicMMLU | Khayyam | VMLU |
|---|---|---|---|---|---|---|---|
| Calibration's mixed ladders | 4 | 3 | 3 | 3 | 5 | 5 | unresolved |
| (a) count ladder | 3 | 3 | 2 | 3 | 5 | 5 | unresolved (5 if test ≥ 6,400) |
| (b) median of three references | 3 | 1 | 3 | 3 | 4 | 4 | unresolved (3 if test ≥ 3,511) |
| (b), knowledge exams anchored on INCLUDE (548) | 3 | 4 | 3 | 3 | 5 | 5 | unresolved (5 if test ≥ 2,192) |
| (b), translation anchored on FLORES devtest (1,012) | 4 | 1 | 3 | 3 | 4 | 4 | unresolved (3 if test ≥ 3,511) |

Under the independence definition of Q3, AfroBench's entry becomes unresolved (1 to 3) in every
row; the other columns do not change.

- **(b) moves with its anchor, and the anchors encode cost, not measurement.** Knowledge exams are
  cheap to collect, so their reference sets are large (MMLU's 14,042), and a 565-question native
  Thai exam falls below R/16 and becomes a 1, ranked under SEA-HELM's 3. Anchor the same task on
  INCLUDE, a native-exam benchmark with about 548 questions per language, and ThaiExam becomes a 4,
  above FLORES+'s 1,012 sentences. Both anchors are defensible picks, and they move ThaiExam three
  bands. Translation references are expensive, so they are small, and anchoring the translation
  ladder on FLORES's own devtest is what kept FLORES+ at 4 in the calibration.
- **(a) changes no result through a choice of reference**, and its errors are the visible ones of
  the measurement model: conservative where per-item variance is low, optimistic where items
  cluster. Those can be corrected task by task as evidence arrives (D2); an anchor cannot.

**Recommendation (D1, deferred).** Take the band meanings as the shared definition, and give each
task family a measurement model, as in the table above. Use the count ladder provisionally where the
table marks the count a suitable proxy; for reading comprehension, use the band of the passage count
where it is stated and mark the band provisional where it is not; treat a judged set's count band as
a ceiling and say so beside it; leave speech and sequence labeling unbanded until they have a model.
On the count ladder, translation, instruction following and judged generation would move onto the
same scale as accuracy: FLORES's 1,012 sentences compute to a 3, NTREX-128's 1,997 to a 4,
SEA-IFEval's 105 prompts to a 2, and SEA-MTBench's 58 prompts to a 1. MT-Bench's own 80 prompts
would be a 1 too: 80 prompts resolve a score to about ±11 points at best.

## Q2. Imported benchmarks

A suite contributes three different things, and the record already tells two of them apart:

- **Original evaluation data**: items the suite created. The record names them with the product's
  own slug as `component`, or, where the suite has two of its own components in one task, with a
  second slug (SEA-HELM's `sea-mt-bench-judge` and `kalahi-judge`). SEA-HELM's human translations of
  IFEval and MT-Bench prompts are original under this rule: the items in Thai or Javanese exist
  because SEA-HELM made them.
- **Imported evaluation data**: another dataset's items, named by that dataset's slug. Three
  imported components in the sample have their own rows on the map: `flores-plus`, `belebele` and
  `sib-200`. The rest (NTREX-128, XNLI, XCOPA, AfriMMLU, MasakhaPOS and others) do not, yet.
- **Assembly**: the harness, prompts and leaderboard that make the items usable together. It is
  real value, and it is not depth. No item count measures it.

How much of each set is its own, on the count ladder:

| | FLORES+ | ThaiExam | SEA-HELM | AfroBench |
|---|---|---|---|---|
| Target languages measured on its own items | 188 of 203 | 1 of 1 | 8 of 11 | 0 of 63 |
| Measured languages whose band rests on an imported task | 0 | 0 | 7 of 10 | 54 of 54 |

AfroBench's only own items are AfriADR's diacritic-restoration sentences, whose provenance no
source states, so none of them qualify. Its depth is entirely imported, including IrokoBench's
AfriMMLU, AfriXNLI and AfriMGSM, which were published separately and so are recorded as imported.

Four ways to score a suite, on the count ladder:

| Basis | FLORES+ | ThaiExam | SEA-HELM | AfroBench |
|---|---|---|---|---|
| Everything at face value (highest task band) | 3 | 3 | 3 | 3 |
| Leave out imports that have their own row | 3 | 3 | unresolved (2-3) | unresolved (0-5) |
| Own items only, imports shown separately | 3 | 3 | 2 | unresolved (0-5) |
| Everything, with the corroboration cap of Q3 (first draft) | 3 | 3 | 2 | 3 |
| Everything, with the corroboration cap and the independence definition | 3 | 3 | 2 | unresolved (1-3) |

- **Own items only** is the cleanest statement of originality, and it is the scoring #953 asks to
  test. Under it, AfroBench has no measured language and SEA-HELM is measured on 8 of 11.
  As a band it discounts reuse entirely: a suite that makes twenty-odd imported datasets runnable
  across sixty languages scores as though it held nothing.
- **Leaving out imports with their own row** looks like a middle path, but it ties a suite's band to
  the state of the map. R-2026-10-30-f gives independently published members their own rows; each
  one added would then lower its suite (AfroBench converges on the own-items row). A band should
  not fall because the map got more complete.
- **Face value** lets a suite tie a set by sampling it: under the calibration's ladders SEA-HELM
  matched FLORES+ at 4 through FLORES's own sentences.

**Recommendation (D4, supported in principle): the band would measure the evaluation resource, with
originality published and not scored.** A reader asking "what can I evaluate a model on in Hausa" is
served by AfroBench whether or not it wrote the items. The corroboration cap (Q3) is what stops a
suite from simply inheriting a set's depth. The recommendation is to publish beside the band, from
the same record:

- an **own-items band**, the same pipeline over the product's own components only (SEA-HELM 2, 8 of
  11 measured; AfroBench unresolved, 0 of 63);
- a **face-value band**, the highest task band with every import counted in full (3 for all four);
- in the per-language view (R-2026-11-01-f), each task band labeled own or imported, and linked to
  the imported set's own row where it has one.

A set's own row would be used for that link and for the group counting of R-2026-10-30-e, never for
the band (D6). Assembly value would stay out of the depth band and show in task breadth (tracked
separately under R-2026-11-01-c), in the note's account of documented use, and in adoption (D9).
The maintainer agrees with this treatment of imported benchmarks; it is not yet ruled.

## Q3. From task bands to a language band

Requirements, from #953 and R-2026-11-01-c: adding a task never lowers a language; a suite gets no
credit for several datasets on one task (the within-task step, [D12](#within-a-task-d12)); no
single imported benchmark dominates; reuse is not automatically discounted.

### The corroborated maximum (candidate)

As first drafted: let O be the language's best band on the product's own components, and I1 ≥ I2
the two best imported bands on different tasks (0 where absent). Then

> language band = max(O, min(I1, max(O, I2) + 1))

In words: the best task band, except that a band carried by one imported task alone is capped one
band above the next-best evidence. The first draft counted any two different tasks as independent
evidence. Written with independence explicit, the same rule is

> language band = max(O, max over imported components c of min(b_c, C_c + 1)),
>
> where b_c is c's band and C_c is the best band among the language's other qualifying components
> that are independent of c: own components on any task, and imported components on a different
> task.

When every pair of components is independent this is exactly the first draft's formula (the
revision's script reproduces all of the first draft's corroborated-maximum results under it), and
it keeps the first draft's properties:

- **Monotone.** Adding a component can only add a term to the outer maximum or raise some C_c, so a
  language never falls. The median of task bands fails this: Khmer measured on translation alone
  outranks Thai measured on eight tasks.
- **Own items count in full.** FLORES+, ThaiExam and every single-component set are untouched.
- **One import cannot set the band.** A language never sits more than one band above the best
  evidence independent of its strongest imported task.
- **Reuse counts where the suite delivers more than one independent thing.** Two imported tasks
  that are independent and agree carry the language at full depth. The second must be on a
  different task, not a second dataset on the same one, following R-2026-11-01-c.

### When evidence counts as independent

Two pieces of evidence for one language, each a component on a task, are **independent for
corroboration only if all three hold**:

1. **Distinct items.** They share no item in the language, and their items do not descend from a
   common source item set. Two task layers on one set of sentences (SIB-200 topic labels and
   Belebele questions on FLORES passages) share items. Two translations of the same English source
   (AfriMMLU and OpenAI MMMLU, both translations of MMLU) share a source.
2. **Distinct creators.** The text in the language was written, translated or labeled by separate
   efforts. Several tasks presented in one publication as one benchmark made by one translation
   effort count as one creator unless a source states that separate translator or annotator pools
   did them. Overlapping research authors alone do not make two sets dependent: the test is who
   produced the items in the language.
3. **Neither derived from the other.** Neither is a re-host, sample, subset, translation or
   relabeling of the other. A suite's import that re-hosts another set's items is that set's
   evidence, not new evidence.

Dependence is read from what the records' cited sources state. Where they say nothing about
lineage, components are treated as distinct, the same default `subset_of` uses; that default is an
assumption, and it favors corroboration. The definition was written from the lineage the sources
state and applied once; it was not adjusted against any band.

Lineage the sources on the records state, and what it makes dependent:

| Components | Stated by | Dependent under |
|---|---|---|
| `flores-plus`, `sib-200`, `belebele` | SIB-200: "based on Flores-200 machine translation corpus"; Belebele: "passages ... directly sourced from the FLoRes-200" | items (common FLORES-200 sentences) |
| `afrimmlu`, `openai-mmmlu` | AfroBench: "two human-translated MMLU datasets" | items (common MMLU source). Same task, so no corroboration was at stake |
| `afrimmlu`, `afrixnli`, `afrimgsm` | IrokoBench: "a human-translated benchmark ... covering three tasks" | creators (one translation effort; no source states separate pools) |
| SEA-HELM's own judged prompts, `sea-mt-bench-judge`, `mt-bench-thai` | cards: "based on MT-Bench"; SEA-HELM Table 1 marks MT-Bench Thai human-translated | items (common MT-Bench source). All in one task |
| `ntrex-128` | NTREX README: references translated from the newstest2019 English source | none: independent of FLORES |
| `uhura-arc-easy`, `injongo-intent`, and every other SEA-HELM import | AfroBench ("human translation of scientific Arc-Easy"), InjongoIntent ("utterances generated by native speakers"), SEA-HELM's cards and Table 1 naming distinct source datasets | none |

### The corroborated maximum, before and after the definition

On the count ladder, with the median across target languages and the robustness test applied as
ruled.

| Rule | FLORES+ | ThaiExam | SEA-HELM | AfroBench |
|---|---|---|---|---|
| First draft: distinct tasks count as independent | 3 | 3 | 2 | 3 |
| Same, SEA-HELM's judged sets counted as its own | 3 | 3 | 2 | 3 |
| Distinct-items condition only | 3 | 3 | 2 | unresolved (1-3) |
| Distinct-creators condition only | 3 | 3 | 2 | 3 |
| **Full definition** | **3** | **3** | **2** | **unresolved (1-3)** |
| Full definition, independent sets on the same task may also corroborate | 3 | 3 | 2 | unresolved (1-3) |

AfroBench's measured languages by band move from 1: 3, 3: 36, 4: 13, 5: 2 to **1: 30, 3: 9, 4: 13,
5: 2**. SEA-HELM's stay at 1: 2, 2: 4, 3: 4, and FLORES+ and ThaiExam have one component each.

What changes, and why:

- **Twenty-seven AfroBench languages fall from 3 to 1**, all on the distinct-items condition:
  `aeb`, `aka`, `ary`, `arz`, `bam`, `cjk`, `dik`, `dyu`, `fon`, `kab`, `kam`, `kbp`, `kea`, `kik`,
  `kmb`, `knc`, `kon`, `lua`, `luo`, `mos`, `nus`, `run`, `sag`, `tso`, `tum`, `tzm`, `umb`. Each is
  measured only on FLORES+ translation (1,012 sentences, 3), SIB-200 (204 sentences, 2) and Belebele
  (900 questions, 3), in some combination: 23 on FLORES+ and SIB-200, `ary`, `arz` and `bam` on all
  three, and `tso` on Belebele and SIB-200. Under the definition these are one piece of evidence, so
  the band rests on one import with nothing independent beside it.
- **AfroBench becomes unresolved (1 to 3).** With 30 of 54 measured languages at 1 and 9 unmeasured,
  the median of 63 is 1 with the unknowns at 0 and 3 with them at 5. It would stand at 3 only if at
  least eight of the nine unmeasured languages came in at 3 or above.
- **The creator condition moves nothing.** Every language IrokoBench measures also has
  InjongoIntent's native utterances, an independent 3 on another task, and most have NTREX-128 or
  Belebele as well. The shared-MMLU and shared-MT-Bench links fall within one task.
- **SEA-HELM does not move.** Its corroboration already crossed distinct source datasets (XNLI,
  XCOPA, IndoNLI, the classification sets), and Khmer and Burmese were already at 1 on FLORES alone.
- **Letting independent sets on one task corroborate** (NTREX-128 with FLORES) lifts six AfroBench
  languages to 4 (five from 3, and Tswana from 1) but leaves the set unresolved, so the
  different-task requirement is not what decides AfroBench.

**The maintainer is not adopting AfroBench at 3.** What the test shows is that the first draft's 3
rested on counting FLORES sentences as corroborating themselves; under a definition of independence
written from the sources' own lineage, AfroBench has no established band until more of its languages
are measured on evidence independent of FLORES. That is a statement about the evidence in the record,
not about AfroBench's value: its FLORES-derived tasks are three tasks on one text, which is breadth.

### The alternatives

Tested against the first draft's rule, on the count ladder, with the median across languages and the
robustness test applied as ruled. All but the last row count distinct tasks as independent, as the
first draft did.

| Rule | FLORES+ | ThaiExam | SEA-HELM | AfroBench |
|---|---|---|---|---|
| Highest task band | 3 | 3 | 3 | 3 |
| Median of task bands | 3 | 3 | 2 | unresolved (2-3) |
| Corroborated maximum | 3 | 3 | 2 | 3 |
| Corroborated maximum, cap of two bands | 3 | 3 | unresolved (2-3) | 3 |
| Best own band, imports add at most one | 3 | 3 | 2 | 1 |
| Best imported band less one, or second imported band | 3 | 3 | 2 | unresolved (2-3) |
| Corroborated maximum, independence definition | 3 | 3 | 2 | unresolved (1-3) |

- **"Imports add at most one to the best own band"**, the simplest original-anchored rule, puts
  AfroBench at 1: with no qualifying own items, every language is capped at 1. That is the automatic
  discount on reuse the brief argues against.
- **A one-band haircut on the best import** discounts even well-corroborated languages and leaves
  AfroBench unresolved.
- **SEA-HELM's 2 against 3** turns on three languages. Under the highest band, Khmer, Burmese and
  Malay are 3 on FLORES's 1,012 sentences; under the corroborated maximum Khmer and Burmese are 1
  (FLORES is their only task) and Malay a 2 (SEA-HELM's own 58-prompt judged set beside FLORES).
  SEA-HELM's own depth is thin: 105 instruction prompts per language, 58 judged prompts in several,
  Kalahi's 150 Tagalog questions and 480 Indonesian LINDSEA items.

**Recommendation (D5 and D7, deferred).** Keep the corroborated maximum, with a cap of one band, as
the candidate rule, and test it with the independence definition above rather than with distinct
tasks alone. The schema cannot yet record shared source text across tasks (`subset_of` is per task,
calibration item 7), so until it can, the lineage table would live with the ladder's implementation
and cite the sources it rests on.

### Across languages

As ruled: the median of the language bands over the target languages, with unknowns filled at 0 and
at 5 (R-2026-11-01-a), and the breadth bonus median + 0.5 × (1 − 1/n) over languages with a band
above zero (R-2026-10-30-i, R-2026-11-01-b). Under the candidates, FLORES+ 3 (bonus 3.50), ThaiExam 3
(3.00) and SEA-HELM 2 (2.45) pass the robustness test and AfroBench does not. The bonus counts
languages, not tasks, so it separates FLORES+ from ThaiExam.

## Within a task (D12)

Every result above takes, for each language and task, the band of the largest single component, as
the calibration proposed. That step has not been ruled, and what it should do is now specified
closely enough to rule on.

**What the step produces.** For each language and task, from the qualifying entries on the official
split (R-2026-11-01-d, R-2026-11-01-h): the best own band and the best imported band, kept apart
because Q3 treats them differently, and the lineage of each component, because Q3's independence
test needs it. Q3 looks at every qualifying component on other tasks when it looks for
corroboration, not only the largest, so a dependent largest component cannot hide an independent
smaller one.

**Options.**

- **(a) The largest single component.** The task band is the band of the component with the most
  qualifying items (most effective items, once the task's measurement model gives n_eff). Ties are
  immaterial, since they give one band. Entries with `subset_of` never count separately. Components
  in different units within one task are compared by band.
- **(b) The sum of distinct components.** The task band is the band of the summed qualifying items,
  each item once. This needs to know which components overlap without one containing the other,
  which the schema does not record (SEA-MTBench and SEA-MT-Bench-Judge share prompts).
- **(c) What the set scores as one number.** Where a set reports one score for a task in a language
  over several components, count their union; where it reports a score per component, take the
  largest. Not computable here: the records do not say how the suites pool their scores.

**What each does in the sample.** (a) is every result above. (b) moves no set band. It raises Thai
and Vietnamese in SEA-HELM from 3 to 4, each on two 1,000-item classification sets (Thai Toxicity
Tweet with Wisesight Sentiment; UIT-VSFC with ViHSD), and it double counts the shared MT-Bench
prompts in Indonesian and Vietnamese judged generation, which moves no language.

**Recommendation: (a).** Summing is the extra credit for several datasets on one task that
R-2026-11-01-c rules out, and the Thai and Vietnamese cases show what it pools: toxicity detection
and sentiment, two constructs that share a task class. A pooled count would also describe a score no
one reports. (c) is the principled alternative if a suite's reported score is what the band should
describe, and it can be revisited once records state how scores are pooled. **Status: deferred.**

## The large single-language exams

None has a coverage record, so the counts below are cited here only and were not added to their
score files. Each is one language, one task, `knowledge_exam`, written in the language.

| Set | Official evaluation items | Source | Provenance stated |
|---|---|---|---|
| ArabicMMLU | 14,455 test questions (plus 120 dev, which the abstract's 14,575 includes) | Hub split sizes; paper abstract | "sourced from school exams", built by "10 Arabic native speakers" |
| Khayyam Challenge | 20,192 questions, evaluated as one set, zero-shot | paper abstract and Table 4 | "original, non-translated data" |
| VMLU | no test count stated; 10,880 questions across all splits, and the README shows a dev file | README; vmlu.ai | questions from Vietnamese school, university and national exams |

VMLU's test answers are held for its leaderboard, and no fetched source gives the test split's
size. Under R-2026-11-01-d only that split counts, and under R-2026-10-30-l a total is never
apportioned, so Vietnamese is unmeasured and VMLU is unresolved (0 to 5). Its band follows from the
test count once a source states it.

Where they rank, on each ladder (the aggregation rule does not matter for a single task):

- **(a), the count ladder:** ArabicMMLU 5 and Khayyam 5, above FLORES+ and ThaiExam at 3, SEA-HELM at
  2 and AfroBench unresolved. **Defensible.** The depth ladder asks how finely a set resolves a
  model's score in each language it targets (R-2026-10-30-g). For Arabic, ArabicMMLU's 14,455 native
  questions resolve accuracy to about ±0.8 points if its questions are independent, and keep band 5
  up to a design effect of 2.26; FLORES+'s Arabic devtest resolves translation quality to about ±3
  at best. FLORES+'s strength is that it does this for 188 languages, which is breadth; the median
  deliberately does not reward breadth, and the breadth bonus works only inside a band. Two cautions
  belong in the note, not the formula: the 5 is earned on one task, so it says nothing about
  translation or reading in that language, and the published task count must sit beside it.
- **(b):** ArabicMMLU and Khayyam 4, above FLORES+ at 3, but ThaiExam 1, below SEA-HELM. Not
  defensible: a documented national exam of 565 native questions is not "a fragment", and it lands
  there only because MMLU is large.
- **(b) with the INCLUDE anchor:** exams 5, ThaiExam 4 above FLORES+ 3. Not defensible as a depth
  claim: 565 questions outrank 1,012 sentences because of which benchmark was picked.
- **Calibration's ladders:** exams 5 above FLORES+ and SEA-HELM at 4. Not defensible for SEA-HELM,
  which ties FLORES+ by sampling it.

Under every option the large exams rank above FLORES+, except the FLORES-anchored translation
ladder, where they tie at 4. The ordering is not an artifact of one choice, so the decision is
whether the category's band means depth per target language. The rulings say it does
(R-2026-10-30-g), and this brief recommends keeping that reading (D10, supported in principle).

## Results by set

What each set computes to under the candidates of this revision: the count ladder as a provisional
proxy, the largest single component within a task, the corroborated maximum with the independence
definition across tasks, and the median across target languages with the robustness test and the
breadth bonus. None of it is adopted.

| Set | Current band | Calibration proposal | **Candidates** | Own-items band | Face-value band | Completeness | Breadth bonus |
|---|---|---|---|---|---|---|---|
| FLORES+ | 5 | 4 | **3** | 3 | 3 | 188 of 203 | 3.50 |
| ThaiExam | 4 | 3 | **3** | 3 | 3 | 1 of 1 | 3.00 |
| SEA-HELM | 5 | 4 | **2** | 2 (8 of 11) | 3 | 10 of 11 | 2.45 |
| AfroBench | 5 | 4 | **unresolved (1-3)** | unresolved (0 of 63) | 3 | 54 of 63 | n/a |
| ArabicMMLU | 5 | 5 | **5** | 5 | 5 | 1 of 1 | 5.00 |
| Khayyam Challenge | 4 | 5 | **5** | 5 | 5 | 1 of 1 | 5.00 |
| VMLU | 4 | 5, from its total | **unresolved** | unresolved | unresolved | 0 of 1 | n/a |

Leaving out the 12 entries mapped through `source_language` changes no band in this table.

What moves each result:

- **FLORES+ 3:** stable under every ladder, rule and basis tested, except a translation ladder
  anchored on FLORES's own devtest, as the calibration's is (4). Its floor from its 281 articles is
  2; it keeps 3 unless sentences within an article correlate above about 0.59.
- **ThaiExam 3:** stable under every aggregation rule and basis; moves with the ladder (1 or 4
  under (b)), and drops to 2 at a design effect above 1.41, which its sources give no way to check.
  It also rests on R-2026-11-01-i's reading of SEA-HELM's "Native" label.
- **SEA-HELM 2:** 3 under the highest task band or under (b), and unresolved (2-3) with a cap of
  two bands. The ladder and the aggregation rule each decide it; the independence definition does
  not.
- **AfroBench unresolved (1-3):** 3 under the highest band and under the first draft's corroborated
  maximum; unresolved under the independence definition, under the median of tasks, and under any
  rule that discounts imports.
- **ArabicMMLU and Khayyam 5:** 4 under (b), 5 otherwise, with room for a design effect of 2.26
  and 3.15.

## Decisions

Each decision states the question, the options, this brief's recommendation and its status. The
statuses are the maintainer's response to the first draft: **supported in principle** means the
maintainer agrees with the recommendation and it still needs a ruling; **deferred** means it waits
for a later ruling session. Nothing here is ruled.

**D1. What does a band mean across tasks?** *Deferred.*
Options: (a) one count ladder (100, 400, 1,600, 6,400) for every bounded metric, as the measure;
(b) per-task ladders anchored on reference benchmarks; (c) shared band meanings, stated as target
resolutions, with a measurement model per task family and the count ladder as a provisional proxy
where counts suit the metric.
Recommendation: (c), with the task-family table of Q1.

**D2. May a task family earn a calibrated measurement model (per-item variance, design effect,
judge variance) in place of the worst case?** *Deferred.*
Options: no, the worst case always; yes, from per-item scores of published model runs; yes, from a
source's own stated intervals.
Recommendation: yes, through a ruling backed by per-item scores from at least two published model
runs, one task family at a time.

**D3. Are speech ladders (hours, utterances, word error rate) deferred until a speech set is in the
calibration?** *Supported in principle.*
Options: defer; band hours now; band utterances now.
Recommendation: defer. Neither unit tracks speakers, and WER has no bound for the count model.

**D4. Does the band measure the evaluation resource, imports included, with originality published
beside it and not scored?** *Supported in principle; the maintainer agrees with the treatment of
imported benchmarks.*
Options: face value; own items only; leave out imports with their own row; everything, with a
corroboration cap.
Recommendation: everything, with the cap of D5, and originality published (D8).

**D5. What is the rule from task bands to a language band?** *Deferred.*
Options: highest task band; median of task bands; the corroborated maximum with a cap of one band;
the same with a cap of two; best own band with imports adding at most one; best import less one.
Recommendation: the corroborated maximum with a cap of one band, tested with the independence
definition of D7.

**D6. Is a set's own row on the map used only to link it and for stage counting, never to change a
suite's band?** *Supported in principle.*
Options: link and stage counting only; also leave such imports out of the suite's band.
Recommendation: link and stage counting only, so a band never falls because the map got more
complete.

**D7. When do two pieces of evidence corroborate each other?** *Deferred.*
Options: any two different tasks (the first draft); different tasks that also meet the
independence definition of Q3 (distinct items, distinct creators, neither derived from the other);
the same, read conservatively where sources are silent (silence counts as dependence).
Recommendation: the independence definition, with silence read as distinct, as `subset_of` reads it.
A shared-source field joins the schema gaps, and until it lands the lineage is kept with the
ladder's implementation and cited. Under this recommendation AfroBench is unresolved (1 to 3).

**D8. Does each record publish an own-items band, a face-value band, completeness and task count
beside the band, with own or imported labels in the per-language view?** *Supported in principle.*
Options: publish all four and the labels; publish completeness only.
Recommendation: publish all four and the labels.

**D9. Does assembly value (harness, prompts, leaderboard) stay out of the depth band?** *Supported
in principle.*
Options: out of the band, shown in task breadth, the note and adoption; a bonus inside the band.
Recommendation: out of the band.

**D10. Is it accepted that large single-language native exams rank above FLORES+ on depth?**
*Supported in principle.*
Options: accept, with the task count published beside the band; prevent it by anchoring each task's
ladder on its reference benchmarks.
Recommendation: accept, with the task count beside the band and the exams' design-effect headroom
checked when their records are filled.

**D11. Is a set whose official split is not stated (VMLU) unresolved until a source states it?**
*Supported in principle.*
Options: unresolved; band it from its total.
Recommendation: unresolved, as R-2026-10-30-l and R-2026-11-01-d already imply.

**D12. Within a task, how do several components for one language become one task band?**
*Deferred.*
Options: (a) the largest single component; (b) the sum of distinct components; (c) what the set
scores as one number.
Recommendation: (a), keeping own and imported bands apart and every component's lineage for Q3.
See [Within a task](#within-a-task-d12).

## Limits, and what to check when the other sets are filled

What four sets cannot tell us:

- **Only one native exam has a record.** ThaiExam is the only single-language set filled, so the
  exam results above rest on cited totals, not on records with splits and provenance.
- **Several tasks are barely exercised.** Summarization appears only as SEA-HELM's 100 documents per
  language; sequence labeling only with unknown provenance; no speech, transliteration, retrieval
  or vision-language entries; no `mixed` entry with a `qualifying_count`; one machine-translated
  entry. The provenance rule and the ladder's lower bands are largely untested.
- **The corroboration cap has been seen in two suites only,** and in AfroBench it mostly meets
  FLORES-derived sets, which the independence definition does not let corroborate one another.
- **No record gives a correlation or a per-item score.** Design effects, per-item variance and judge
  variance are all unmeasured, so every band here is the count model's band. The headroom table
  says which ones a modest design effect would move; it does not say which ones it does move.

To check when the other evaluation sets are filled:

- **The count at 5.** Under the candidates the 5s come from large native exams. R-2026-10-30-l
  rejected 12 of 22 at 5; recount against the one-third review trigger once the exams (TurkishMMLU,
  KazMMLU, DarijaMMLU, MILU, SeaExam, LaoBench, INCLUDE) have records.
- **Cluster counts.** Record passages, articles or shared stems where a source states them, so the
  floor of the [clustering bound](#how-much-clustering-each-count-can-absorb) can be read for more
  sets.
- **Stated official splits.** VMLU shows that a leaderboard benchmark may not state its test size.
  Expect more unresolved single-language sets, and record their splits when a source states them.
- **Suites with original depth.** IndicGenBench, IndicXTREME and SEACrowd-style hubs will show
  whether the cap behaves as intended when a suite's own items are deep.
- **Lineage.** Each new suite needs its components' source text and creators read, as in the table
  of Q3, before its bands can be computed under the independence definition.
- **A speech set** before any speech model is adopted (D3), and a judged-generation set with more
  than a few hundred prompts before D2 is reopened for judged tasks.
- **The SEA-HELM leaderboard against its cards.** The record follows the Hugging Face cards; the
  leaderboard's current task list is larger (calibration item 5), which could move SEA-HELM's
  Malay, Burmese, Lao and Khmer.

## Appendix A. The ladders and their references

Ladder (a), the count ladder, every task bounded on 0 to 1: band 1 from 1 item, 2 from 100, 3 from
400, 4 from 1,600, 5 from 6,400 (worst-case 95% half-width ±9.8, ±4.9, ±2.5, ±1.2 points, for
independent items).

Ladder (b): R is the median per-language official evaluation size of three references; bands 2, 3,
4 and 5 start at R/16, R/4, R and 4R, rounded up. The references were picked by one rule per task
(an English flagship and the two most-used multilingual sets) before any band was computed under
(b). Where a first pick's size could not be fetched, a substitute of the same kind was used (listed
under [Sources read](#sources-read)); AfriXNLI stands in for AmericasNLI, and the NLI median is
5,010 either way. Several references are also imported by the calibration suites (FLORES,
NTREX-128, XNLI, XCOPA, Belebele, SIB-200, AfriXNLI); they are field standards on their own
account.

| Task | References (official evaluation split) | R | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| `knowledge_exam` | MMLU test 14,042; Global-MMLU (sw) test 14,042; INCLUDE-base median test 548 | 14,042 | 878 | 3,511 | 14,042 | 56,168 |
| `reasoning` | GSM8K test 1,319; XCOPA (th) test 500; MGSM (sw) test 250 | 500 | 32 | 125 | 500 | 2,000 |
| `reading_comprehension` | SQuAD v1.1 validation 10,570; XQuAD (th) 1,190; Belebele 900 | 1,190 | 75 | 298 | 1,190 | 4,760 |
| `natural_language_inference` | MNLI matched validation 9,815; XNLI (sw) test 5,010; AfriXNLI 600 | 5,010 | 314 | 1,253 | 5,010 | 20,040 |
| `text_classification` | AG News test 7,600; SST-2 validation 872 (test labels withheld); SIB-200 (sw) test 204 | 872 | 55 | 218 | 872 | 3,488 |
| `sequence_labeling` | CoNLL-2003 test 3,453; MasakhaNER 2.0 (yo) test 1,964; WikiANN (sw) test 1,000 | 1,964 | 123 | 491 | 1,964 | 7,856 |
| `machine_translation` | WMT14 de-en newstest 3,003; NTREX-128 1,997; FLORES devtest 1,012 | 1,997 | 125 | 500 | 1,997 | 7,988 |
| `summarization` | CNN/DailyMail test 11,490; XSum test 11,334 (the XL-Sum size endpoint failed; mean of two) | 11,412 | 714 | 2,853 | 11,412 | 45,648 |
| `instruction_following` | IFEval 541 (no second widely used reference) | 541 | 34 | 136 | 541 | 2,164 |
| `text_generation`, judged | AlpacaEval 805; Arena-Hard-Auto 500; MT-Bench 80 | 500 | 32 | 125 | 500 | 2,000 |

The INCLUDE anchor for knowledge exams is R = 548 (bands from 35, 137, 548, 2,192); the FLORES
anchor for translation is R = 1,012 (bands from 64, 253, 1,012, 4,048).

## Appendix B. Language-band distributions

Measured target languages by band, on the count ladder. Unknown languages are not in the counts.

| Rule | FLORES+ | SEA-HELM | AfroBench |
|---|---|---|---|
| Highest task band | 0: 3, 3: 185 | 2: 3, 3: 7 | 2: 1, 3: 32, 4: 19, 5: 2 |
| Median of task bands | 0: 3, 3: 185 | 2: 8, 3: 2 | 2: 25, 3: 28, 4: 1 |
| Corroborated maximum, distinct tasks independent (first draft) | 0: 3, 3: 185 | 1: 2, 2: 4, 3: 4 | 1: 3, 3: 36, 4: 13, 5: 2 |
| Corroborated maximum, independence definition | 0: 3, 3: 185 | 1: 2, 2: 4, 3: 4 | 1: 30, 3: 9, 4: 13, 5: 2 |

FLORES+'s three zeros are its dev-only languages (documented zeros). ThaiExam's one language is a 3
under every rule.

**SEA-HELM per language under the candidates** (task bands on the count ladder; `own` marks
SEA-HELM's own components, the judged sets included): Indonesian 3 (translation 3, inference 3 and
own 2, reasoning 3, classification 3 and own 2, instruction following own 2, reading 2,
summarization 2, judged own 1); Thai 3; Vietnamese 3; Tamil 3; Javanese 2 (instruction following own
2, translation 2, reasoning 2); Sundanese 2; Tagalog 2 (instruction following and exam, both own 2);
Malay 2 (translation 3, judged own 1); Khmer 1 and Burmese 1 (translation 3 only); Lao unmeasured.

**AfroBench under the candidates:** 5 for Swahili and Yoruba (OpenAI MMMLU's 14,042 questions,
corroborated by NTREX-128); 4 for 13 languages (`afr`, `amh`, `ewe`, `hau`, `ibo`, `kin`, `nso`,
`orm`, `sna`, `tir`, `wol`, `xho`, `zul`: NTREX-128's 1,997 sentences, corroborated by an independent
task at 3); 3 for 9 (`bem`, `lin`, `lug`, `nya`, `plt`, `som`, `sot`, `ssw`, `twi`); 1 for 30: the 27
measured only on FLORES-derived evidence, Nigerian Fulfulde (SIB-200 only), Tamasheq (FLORES only)
and Tswana (translation only, FLORES+ and NTREX-128); 9 unmeasured.

## Sources read

All fetched 2026-11-02 with `uv run python -m build.fetch_source`. HTTP 200 unless noted. Digests
are of the bodies the figures were read from.

| URL | What it gave | sha256 |
|---|---|---|
| https://datasets-server.huggingface.co/size?dataset=MBZUAI/ArabicMMLU | `All`: test 14,455, dev 120 | `d7d639ec5cad6d21583529b2a9689baf9cf9958b6e71d03f3be877ca8c6df2e8` |
| https://arxiv.org/abs/2402.12840 | ArabicMMLU abstract: 14,575 questions, school exams | `ec5060d2f18089a5560ceec84a7c8393933280514b505c7ef506bcfc55f2f7a3` |
| https://arxiv.org/abs/2404.06644 | Khayyam abstract: 20,192 questions from Persian examinations | `f045cb12c69ed9c98ea845cbc7ac0224211ca799b11ef12761e21ae6d176a32b` |
| https://arxiv.org/html/2404.06644 | Khayyam Table 4 total 20,192; "original, non-translated data"; zero-shot evaluation | `c785d9dfad69ef6f8408e514fd681e5ae2f40b72c79350130c85dc64b17e8bbd` |
| https://raw.githubusercontent.com/ZaloAI-Jaist/VMLU/main/README.md | 10,880 questions in 58 subjects; dev file; test submitted to the leaderboard | `df64aac6d70eb3eda30de301101b370fab19706aa4f12ece357886f59d0464a4` |
| https://vmlu.ai | subjects of about 200 questions; no split sizes | `2aed40115a00b4a7b96a9787cfdb9eb67115338c22af05466ae056588ede2eea` |
| https://datasets-server.huggingface.co/size?dataset=cais/mmlu&config=all | MMLU test 14,042 | `a6628c2aba3d4485bc34739ab14a9a0885ee606d9f0b7db8f11f23171e241147` |
| https://datasets-server.huggingface.co/size?dataset=CohereLabs/Global-MMLU&config=sw | test 14,042 | `f9b32d7565c4e53b73e36d2f536486a28774ac34bb36f64aa22ec85496e86915` |
| https://datasets-server.huggingface.co/size?dataset=CohereLabs/include-base-44 | 44 languages, test 139 to 552, median 548 | `d7726d51a39c1b53a5c86e006a0c03f93e581c94921a7f0fbf85ef33577846d0` |
| https://datasets-server.huggingface.co/size?dataset=openai/gsm8k&config=main | test 1,319 | `21b57fbcc28630d8f7bffd25a28092b4bc6b884a88105ed3331c9b0801ff362e` |
| https://datasets-server.huggingface.co/size?dataset=cambridgeltl/xcopa&config=th | test 500 | `20385aa13f1a09e5e17fefc55c61db43c4847f59b4000c5c5302be990024ecf6` |
| https://datasets-server.huggingface.co/size?dataset=juletxara/mgsm&config=sw | test 250 | `e47940f1181eeb344bdcb4454f62646af5891adef0f2ce164b808aaae4ab18fb` |
| https://datasets-server.huggingface.co/size?dataset=rajpurkar/squad | validation 10,570 | `c4e786117072bff994bbc4146c90e60a9764121824371fe7df92e6a8bea22f87` |
| https://datasets-server.huggingface.co/size?dataset=google/xquad&config=xquad.th | 1,190 | `d552fee6c332256ea54adbdea1f2fec4bb8dcefa7cc5bb8819b7a2c0850125c2` |
| https://arxiv.org/html/2311.07978 | AfroBench Table 2: Belebele 900, AfriXNLI 600 per language | `ef2b0d2751fd66adfd660ee0f45c3e2c928ff04cf846b4c5b7130df0243f6822` |
| https://datasets-server.huggingface.co/size?dataset=nyu-mll/glue&config=mnli | validation matched 9,815 | `1614013f0934d1cf4d296606c0d4d590abb8df45abaa42d32684aef290adc7f1` |
| https://datasets-server.huggingface.co/size?dataset=facebook/xnli&config=sw | test 5,010 | `4daefe07108fa87079431cba6f188f25a8307ddf900d69cc3d7fc03907fa5b2f` |
| https://datasets-server.huggingface.co/size?dataset=fancyzhx/ag_news | test 7,600 | `87684bad4294d42b86901d094aba779c69515a16e76b1c1755656b7860a8866e` |
| https://datasets-server.huggingface.co/size?dataset=stanfordnlp/sst2 | validation 872, test 1,821 | `7fe757a2b810213ffebfbacb5927a6b448d43f8107fdb86e3b666ff23778fd4e` |
| https://datasets-server.huggingface.co/size?dataset=Davlan/sib200&config=swh_Latn | test 204 | `0695da9e700e98dc7f25f98355da3cfe423eb0d1165ca521c3eed2ad37b2b6e7` |
| https://datasets-server.huggingface.co/size?dataset=tner/conll2003 | test 3,453 | `f1f67d39fac10be1d845baaef487f99b076d9284a92d216f5427c21a482e18af` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/masakhaner2&config=yor | test 1,964 | `c13c833d96855425f1d753b1bef3e6628c6d5cac552d9c640c40759f0932fcd4` |
| https://datasets-server.huggingface.co/size?dataset=unimelb-nlp/wikiann&config=sw | test 1,000 | `8a694cee2530bb4fef50e1e4af833458cbf2ac1c957dab11b4575ae5416edb67` |
| https://datasets-server.huggingface.co/size?dataset=wmt/wmt14&config=de-en | test 3,003 | `9b3d0b05c7c4a303cd310c6c7b23090c5f4d1852af575fd54032bd3c32942a67` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/ntrex_african | test 1,997 per language | `eea43d72e9d50175c01ce80c1d2671ebf27e7a508744808e6154afe9f199d315` |
| https://huggingface.co/datasets/openlanguagedata/flores_plus | devtest 1,012 sentences | `34990a3f15ecd78cfddd7027d5bd2c3c8fb9cd327e1cbdd96db3b8888de2b217` |
| https://datasets-server.huggingface.co/size?dataset=abisee/cnn_dailymail&config=3.0.0 | test 11,490 | `6c2b102e6ba6ef155bf2654498278551be69f3c84a0cea6b7a6aa68649467f42` |
| https://datasets-server.huggingface.co/size?dataset=EdinburghNLP/xsum | test 11,334 | `bb730817ba0fd9a52eea75e0911a1f7ffd0ebe953f332e6957bb92f64a1dcf09` |
| https://datasets-server.huggingface.co/size?dataset=google/IFEval | 541 prompts | `55671fae08cdfc2113fddd20b4a8fd95f2bb2a96ee19ff646fbd0b2b7c2bf779` |
| https://datasets-server.huggingface.co/size?dataset=HuggingFaceH4/mt_bench_prompts | 80 prompts | `b22a7bc34ec478be52115d89daacc56c8b8615271329fa46f2d3cb8e85d858fe` |
| https://datasets-server.huggingface.co/size?dataset=lmarena-ai/arena-hard-auto-v0.1 | 500 prompts | `26739525e5aeb3870ee1779cecb4f29f785c33a977956930f6b6bc6181291982` |
| https://arxiv.org/html/2305.14387 | AlpacaFarm: "an evaluation of 805 instructions" | `e76bcacadb9fb89e4cd5d6f6bf39c9bc2965b08026e40c0d51168e6138db6e77` |

Not usable on this date: the Khayyam Challenge size endpoint (HTTP 401, gated), the XL-Sum and
AmericasNLI size endpoints (HTTP 500 and 401), MASSIVE (404), the eriktks CoNLL-2003 endpoint (501,
replaced by `tner/conll2003`), and the AlpacaEval size endpoint (404, replaced by the AlpacaFarm
paper).
The revision's lineage and cluster figures come from sources already cited on the records, read from
the bodies fetched on 2026-11-01 for the calibration record, whose [Sources
read](../sweeps/2026-11-01-language-depth-calibration.md#sources-read) gives their digests: the
FLORES-101 paper (<https://aclanthology.org/2022.tacl-1.30.pdf>, Table 3: devtest 1,012 sentences
from 281 articles), the Belebele paper (<https://arxiv.org/html/2308.16884>: "In total, there are
488 distinct passages"), the SIB-200 abstract (<https://arxiv.org/abs/2309.07445>), the IrokoBench
abstract (<https://arxiv.org/abs/2406.03368>), the AfroBench paper
(<https://arxiv.org/html/2311.07978>: "two human-translated MMLU datasets", Uhura as "the human
translation of scientific Arc-Easy", and AfriMMLU's five subjects), the NTREX README
(<https://raw.githubusercontent.com/MicrosoftTranslator/NTREX/main/README.md>:
`newstest2019-src.eng.txt` as the "original source data"), the InjongoIntent abstract
(<https://arxiv.org/abs/2502.09814>), and SEA-HELM's task cards and paper as quoted on its record.
