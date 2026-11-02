# Language depth methodology: cross-task bands, imported benchmarks and task aggregation, 2026-11-02

This brief takes up the three questions issue #953 left for the ladder PR ("Decide in the ladder
PR"): what a depth band means across tasks, how a suite's imported benchmarks count, and how a
language's task bands become one language band. It compares options on the four calibration records
(FLORES+, ThaiExam, SEA-HELM, AfroBench) and on three large single-language exams that have no
records yet (ArabicMMLU, the Khayyam Challenge, VMLU).

It evaluates and recommends. It changes no score, record, recipe, schema or roster. Every
recommendation waits on a ruling listed in [Decisions](#decisions). Like the other records in
`docs/briefs/`, it describes the corpus on the date above and is refreshed by a new brief, not
edited. Inputs are on `main` at the same date: the records in `sources/scores/`, the calibration
dry run in `docs/sweeps/2026-11-01-language-depth-calibration.md`, the "Per-language coverage"
section of `docs/reference/capability.md`, and rulings R-2026-10-30-g, -i, -l and R-2026-11-01-a
to -i.

**Method.** One script read the four records and applied every combination of options below. The
same script, given the calibration's ladders and rules, reproduces the calibration's hand-run
exactly (4, 3, 4, 4 under the highest task band; 4, 3, 3, 3 under the median; SEA-HELM 3 and
AfroBench unresolved, 0 to 5, without borrowed rows), so the differences below come from the
options and not from the arithmetic. Reference benchmark sizes were chosen by a fixed rule before
any result was computed ([Appendix A](#appendix-a-the-ladders-and-their-references)), and nothing
was adjusted afterward to move a set toward its current band.

## The short answer

1. **A band means the same statistical resolution on every task.** Use one ladder for every task
   whose metric is bounded on 0 to 1: 100, 400, 1,600 and 6,400 qualifying items start bands 2 to 5.
   Each band halves the worst-case 95% margin of error (about ±10, ±5, ±2.5 and ±1.2 points). The
   field-standard alternative gives results that flip with the choice of reference benchmark and
   ranks a 565-question native Thai exam as a 1.
2. **The band measures the evaluation resource, not originality.** Imported items count. Whether
   an item is the product's own, imported, or imported from a set with its own row on the map is
   recorded and published beside the band, and enters the score at one point only: the
   aggregation rule below. Whether an imported set has its own row never changes a band.
3. **Task to language: the corroborated maximum.** A language's band is its best task band,
   except that a band resting on one imported task alone sits at most one band above the
   language's next-best evidence. Adding a task never lowers a language, a suite's own items
   always count in full, and no single imported benchmark sets a language's band by itself.

They fit together in order: the ladder puts every task in the same unit, the record says what each
item is, and the aggregation rule is the one place origin matters. The ruled steps then follow
unchanged: the median across target languages, the robustness test, the capped breadth bonus.

Under that package the four calibration sets get **FLORES+ 3, ThaiExam 3, SEA-HELM 2, AfroBench 3**,
and all four stand under the robustness test. ArabicMMLU and the Khayyam Challenge get a 5. VMLU is
unresolved, because no source states its test split; it would be a 5 if that split holds at least
6,400 of its 10,880 questions.

**Stable across every option tested:** no calibration set reaches 5; all four fall from their
current bands; FLORES+ is a 3 unless its own devtest is the anchor for the translation ladder; the
large native exams never rank below FLORES+. **Dependent on one choice:** ThaiExam on the ladder
(Q1), SEA-HELM on the aggregation rule (Q3, and the ladder), and AfroBench on whether imported items
count (Q2) and on whether a set built from the same sentences can corroborate
([Decisions](#decisions), D7).

## Q1. What a band means across tasks

The calibration's ladders mix two rationales: statistical precision for accuracy-scored tasks, and
conventional benchmark sizes for translation and judged prompts. So a 4 in translation (1,000
sentences) and a 4 in classification (1,600 items) are different claims. Two ways to make them the
same claim:

- **(a) Statistical precision.** Every task gets the ladder that delivers the same confidence
  interval on its own metric. For any metric bounded on 0 to 1 (accuracy, chrF or BLEU over 100,
  a rescaled judge score, ROUGE, IFEval's prompt-level accuracy) the per-item variance is at most
  0.25, so the worst-case 95% half-width on n items is 0.98/√n whatever the task. Equal worst-case
  precision therefore means **one ladder for all of these tasks**: 1, 100, 400, 1,600, 6,400. It
  needs no estimate from model outputs and no per-task tuning.
- **(b) Field-standard sizes.** Each task's ladder is anchored on its well-known benchmarks. The
  rule applied here: for each task, take three references (an English flagship and the two
  most-used multilingual sets), anchor band 4 at their median per-language evaluation size R, and
  keep (a)'s spacing, so band 2 starts at R/16, band 3 at R/4 and band 5 at 4R. The difference from
  (a) is then only the anchor. Appendix A lists the references and their fetched sizes.

Bands under each ladder, with the recommended aggregation (Q3) held fixed. The calibration's mixed
ladders are the first row, for reference.

| Ladder | FLORES+ | ThaiExam | SEA-HELM | AfroBench | ArabicMMLU | Khayyam | VMLU |
|---|---|---|---|---|---|---|---|
| Calibration's mixed ladders | 4 | 3 | 3 | 3 | 5 | 5 | unresolved |
| **(a) precision** | **3** | **3** | **2** | **3** | **5** | **5** | unresolved (5 if test ≥ 6,400) |
| (b) median of three references | 3 | 1 | 3 | 3 | 4 | 4 | unresolved (3 if test ≥ 3,511) |
| (b), knowledge exams anchored on INCLUDE (548) | 3 | 4 | 3 | 3 | 5 | 5 | unresolved (5 if test ≥ 2,192) |
| (b), translation anchored on FLORES devtest (1,012) | 4 | 1 | 3 | 3 | 4 | 4 | unresolved (3 if test ≥ 3,511) |

What the rows show:

- **(b) moves with its anchor, and the anchors encode cost, not measurement.** Knowledge exams are
  cheap to collect, so their reference sets are large (MMLU's 14,042), and a 565-question native
  Thai exam falls below R/16 and becomes a 1, ranked under SEA-HELM's 3. Anchor the same task on
  INCLUDE, a native-exam benchmark with about 548 questions per language, and ThaiExam becomes a 4,
  above FLORES+'s 1,012 sentences. Both anchors are defensible picks, and they move ThaiExam three
  bands. Translation references are expensive, so they are small, and anchoring the translation
  ladder on FLORES's own devtest is what kept FLORES+ at 4 in the calibration.
- **(a) changes no result through a choice of reference.** Its one assumption is the worst-case
  variance, and that is conservative where per-item scores vary less than a coin flip, as
  sentence-level translation and judge scores usually do. Under (a) a translation set is credited
  with no more precision than it is guaranteed to have. Allowing a measured per-task variance
  factor later would raise translation and judged sets. It needs per-item scores from published
  model runs, which drift as models change, so it is a ruling of its own (D2).
- **What does not fit (a).** Word error rate is not bounded by 1, and speech units (hours,
  utterances) are not in the sample. Speech ladders need their own bound and wait for a speech set
  in the calibration (D3).

**Recommendation: (a).** It gives every band one meaning ("a score on this language is resolved to
within ±x points"), it has no free parameter per task, and its rankings are the defensible ones on
the exams below. The calibration's accuracy ladder is unchanged. Translation, instruction
following and judged generation move onto it: FLORES's 1,012 sentences become a 3, NTREX-128's
1,997 a 4, SEA-IFEval's 105 prompts a 2, and SEA-MTBench's 58 prompts a 1. MT-Bench's own 80
prompts would be a 1 too: 80 prompts resolve a score to about ±11 points.

## Q2. Imported benchmarks

A suite contributes three different things, and the record already tells two of them apart:

- **Original evaluation data**: items the suite created. The record names them with the product's
  own slug as `component`. SEA-HELM's human translations of IFEval and MT-Bench prompts are
  original under this rule: the items in Thai or Javanese exist because SEA-HELM made them.
- **Imported evaluation data**: another dataset's items, named by that dataset's slug. Three
  imported components in the sample have their own rows on the map: `flores-plus`, `belebele` and
  `sib-200`. The rest (NTREX-128, XNLI, XCOPA, AfriMMLU, MasakhaPOS and others) do not, yet.
- **Assembly**: the harness, prompts and leaderboard that make the items usable together. It is
  real value, and it is not depth. No item count measures it.

How much of each set is its own, under (a):

| | FLORES+ | ThaiExam | SEA-HELM | AfroBench |
|---|---|---|---|---|
| Target languages measured on its own items | 188 of 203 | 1 of 1 | 6 of 11 | 0 of 63 |
| Measured languages whose band rests on an imported task | 0 | 0 | 7 of 10 | 54 of 54 |

AfroBench's only own items are AfriADR's diacritic-restoration sentences, whose provenance no
source states, so none of them qualify. Its depth is entirely imported, including IrokoBench's
AfriMMLU, AfriXNLI and AfriMGSM, which were published separately and so are recorded as imported.

Four ways to score a suite, under (a):

| Basis | FLORES+ | ThaiExam | SEA-HELM | AfroBench |
|---|---|---|---|---|
| Everything at face value (highest task band) | 3 | 3 | 3 | 3 |
| Leave out imports that have their own row | 3 | 3 | unresolved (2-3) | unresolved (0-5) |
| Own items only, imports shown separately | 3 | 3 | 2 | unresolved (0-5) |
| **Everything, with the corroboration cap of Q3** | **3** | **3** | **2** | **3** |

- **Own items only** is the cleanest statement of originality, and it is the scoring #953 asks to
  test. Under it, AfroBench has no measured language and SEA-HELM is measured on 6 of 11.
  As a band it discounts reuse entirely: a suite that makes twenty-odd imported datasets runnable
  across sixty languages scores as though it held nothing.
- **Leaving out imports with their own row** looks like a middle path, but it ties a suite's band to
  the state of the map. R-2026-10-30-f gives independently published members their own rows; each
  one added would then lower its suite (AfroBench converges on the own-items row). A band should
  not fall because the map got more complete.
- **Face value** lets a suite tie a set by sampling it: under the calibration's ladders SEA-HELM
  matched FLORES+ at 4 through FLORES's own sentences.

**Recommendation: the band measures the evaluation resource, with originality published and not
scored.** A reader asking "what can I evaluate a model on in Hausa" is served by AfroBench whether
or not it wrote the items. The corroboration cap (Q3) is what stops a suite from simply inheriting
a set's depth. Publish beside the band, from the same record:

- an **own-items band**, the same pipeline over the product's own components only (SEA-HELM 2, 6 of
  11 measured; AfroBench unresolved, 0 of 63);
- a **face-value band**, the highest task band with every import counted in full (3 for all four);
- in the per-language view (R-2026-11-01-f), each task band labeled own or imported, and linked to
  the imported set's own row where it has one.

A set's own row is used for that link and for the group counting of R-2026-10-30-e, never for the
band. Assembly value stays out of the depth band. It shows in task breadth (tracked separately
under R-2026-11-01-c), in the note's account of documented use, and in adoption (D9).

## Q3. From task bands to a language band

Requirements, from #953 and R-2026-11-01-c: adding a task never lowers a language; a suite gets no
credit for several datasets on one task (the within-task rule takes the largest single component,
as the calibration proposed, D12); no single imported benchmark dominates; reuse is not
automatically discounted.

**The corroborated maximum (recommended).** Let O be the language's best band on the product's
own components, and I1 ≥ I2 the two best imported bands on different tasks (0 where absent). Then

> language band = max(O, min(I1, max(O, I2) + 1))

In words: the best task band, except that a band carried by one imported task alone is capped one
band above the next-best evidence. Why this shape:

- **Monotone.** O, I1 and I2 can only rise when a task is added, and the formula is built from max,
  min and +1, so the band never falls. The median of task bands fails this: Khmer measured on
  translation alone outranks Thai measured on eight tasks.
- **Own items count in full.** FLORES+, ThaiExam and every single-component set are untouched.
- **One import cannot set the band.** A language's band never sits more than one band above its
  best evidence other than its strongest imported task.
- **Reuse counts where the suite delivers more than one thing.** Two imported tasks that agree
  carry the language at full depth. Requiring the second task on a different task, not a second
  dataset on the same one, follows R-2026-11-01-c.

Tested against the alternatives, under (a), with the median across languages and the robustness
test applied as ruled:

| Rule | FLORES+ | ThaiExam | SEA-HELM | AfroBench |
|---|---|---|---|---|
| Highest task band | 3 | 3 | 3 | 3 |
| Median of task bands | 3 | 3 | 2 | unresolved (2-3) |
| **Corroborated maximum** | **3** | **3** | **2** | **3** |
| Corroborated maximum, cap of two bands | 3 | 3 | unresolved (2-3) | 3 |
| Best own band, imports add at most one | 3 | 3 | 2 | 1 |
| Best imported band less one, or second imported band | 3 | 3 | 2 | unresolved (2-3) |
| Corroborated maximum, sets built from FLORES sentences cannot corroborate FLORES | 3 | 3 | 2 | unresolved (1-3) |

- **"Imports add at most one to the best own band"**, the simplest original-anchored rule, puts
  AfroBench at 1: with no qualifying own items, every language is capped at 1. That is the automatic
  discount on reuse the brief rules out.
- **A one-band haircut on the best import** discounts even well-corroborated languages and leaves
  AfroBench unresolved.
- **SEA-HELM's 2 against 3** turns on three languages. Under the highest band, Khmer, Burmese and
  Malay are 3 on FLORES's 1,012 sentences; under the corroborated maximum Khmer and Burmese are 1
  (FLORES is their only task) and Malay a 2 (a 58-prompt judged set beside FLORES). SEA-HELM's own
  depth is thin: 105 instruction prompts per language, 58 judged prompts in four, Kalahi's 150
  Tagalog questions and 480 Indonesian LINDSEA items.
- **AfroBench's 3 depends on SIB-200 and Belebele corroborating FLORES.** Twenty-seven of its
  languages are measured only on FLORES translation and sets built from FLORES sentences: SIB-200
  topic labels and Belebele reading questions. They are different tasks and benchmarks, but one
  source text. The schema cannot record that (`subset_of` is per task, calibration item 7), so the
  recommended rule counts them as distinct; if it could not, AfroBench would be unresolved until its
  nine unmeasured languages are filled (D7).

**Across languages,** as ruled: the median of the language bands over the target languages, with
unknowns filled at 0 and at 5 (R-2026-11-01-a), and the breadth bonus median + 0.5 × (1 − 1/n)
over languages with a band above zero (R-2026-10-30-i, R-2026-11-01-b). Under the package all four
pass the robustness test: FLORES+ 3 (bonus 3.50), ThaiExam 3 (3.00), SEA-HELM 2 (2.45), AfroBench 3
(3.49). The bonus counts languages, not tasks, so it separates FLORES+ from ThaiExam and barely
separates FLORES+ from AfroBench.

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

- **(a), recommended:** ArabicMMLU 5 and Khayyam 5, above FLORES+, ThaiExam and AfroBench at 3 and
  SEA-HELM at 2. **Defensible.** The depth ladder asks how finely a set resolves a model's score
  in each language it targets (R-2026-10-30-g). For Arabic, ArabicMMLU's 14,455 native questions
  resolve accuracy to about ±0.8 points, where FLORES+'s Arabic devtest resolves translation
  quality to about ±3. FLORES+'s strength is that it does this for 188 languages, which is breadth;
  the median deliberately does not reward breadth, and the breadth bonus works only inside a band.
  Two cautions belong in the note, not the formula: the 5 is earned on one task, so it says nothing
  about translation or reading in that language, and the published task count must sit beside it.
  Exam questions also cluster by subject, so their effective precision is somewhat lower than the
  item count suggests; that is true of every exam, ThaiExam included, and does not reorder them.
- **(b):** ArabicMMLU and Khayyam 4, above FLORES+ at 3, but ThaiExam 1, below SEA-HELM. Not
  defensible: a documented national exam of 565 native questions is not "a fragment", and it lands
  there only because MMLU is large.
- **(b) with the INCLUDE anchor:** exams 5, ThaiExam 4 above FLORES+ 3. Not defensible as a depth
  claim: 565 questions outrank 1,012 sentences because of which benchmark was picked.
- **Calibration's ladders:** exams 5 above FLORES+ and SEA-HELM at 4. Not defensible for SEA-HELM,
  which ties FLORES+ by sampling it.

Under every option the large exams rank above FLORES+, except the FLORES-anchored translation
ladder, where they tie at 4. The ordering is not an artifact of one choice, so the decision is
whether the category's band means depth per target language. The rulings say it does, and this
brief recommends keeping it (D10).

## The recommended package

| Set | Current band | Calibration proposal | **Package** | Own-items band | Face-value band | Completeness | Breadth bonus |
|---|---|---|---|---|---|---|---|
| FLORES+ | 5 | 4 | **3** | 3 | 3 | 188 of 203 | 3.50 |
| ThaiExam | 4 | 3 | **3** | 3 | 3 | 1 of 1 | 3.00 |
| SEA-HELM | 5 | 4 | **2** | 2 (6 of 11) | 3 | 10 of 11 | 2.45 |
| AfroBench | 5 | 4 | **3** | unresolved (0 of 63) | 3 | 54 of 63 | 3.49 |
| ArabicMMLU | 5 | 5 | **5** | 5 | 5 | 1 of 1 | 5.00 |
| Khayyam Challenge | 4 | 5 | **5** | 5 | 5 | 1 of 1 | 5.00 |
| VMLU | 4 | 5, from its total | **unresolved** | unresolved | unresolved | 0 of 1 | n/a |

Package: ladder (a), largest single component within a task, corroborated maximum across tasks,
median across target languages with the robustness test and the breadth bonus. Leaving out the 12
entries mapped through `source_language` changes no package band.

What moves each result:

- **FLORES+ 3:** stable under every ladder, rule and basis tested, except a translation ladder
  anchored on FLORES's own devtest, as the calibration's is (4).
- **ThaiExam 3:** stable under every aggregation rule and basis; moves with the ladder (1 or 4
  under (b)). It also rests on R-2026-11-01-i's reading of SEA-HELM's "Native" label.
- **SEA-HELM 2:** 3 under the highest task band or under (b), and unresolved (2-3) with a cap of
  two bands. The ladder and the aggregation rule each decide it.
- **AfroBench 3:** stable under the highest band and the corroborated maximum on either ladder;
  unresolved under the median of tasks, under any rule that discounts imports, and if sets built
  from FLORES sentences cannot corroborate FLORES.
- **ArabicMMLU and Khayyam 5:** 4 under (b), 5 otherwise.

## Decisions

Each can be answered in a sentence. The recommendation follows each question.

- **D1. Do bands mean the same worst-case precision on every task, with one ladder (100, 400,
  1,600, 6,400) for every metric bounded on 0 to 1?** Yes.
- **D2. May a task later earn a less conservative ladder from a measured per-item variance?** Not
  now; only through a ruling backed by per-item scores from at least two published model runs.
- **D3. Are speech ladders (hours, utterances, word error rate) deferred until a speech set is
  calibrated?** Yes.
- **D4. Does the band measure the evaluation resource, imports included, with originality
  published beside it and not scored?** Yes.
- **D5. Is the task-to-language rule the corroborated maximum, with a cap of one band?** Yes.
- **D6. Is a set's own row on the map used only to link it and for stage counting, never to change
  a suite's band?** Yes.
- **D7. Until the schema records shared source text, do two tasks built on the same sentences
  (FLORES with SIB-200 or Belebele) corroborate each other?** Yes, as recorded, with a shared-source
  field added to the schema gaps and this rule revisited when it lands.
- **D8. Does each record publish an own-items band, a face-value band, completeness and task count
  beside the band, with own or imported labels in the per-language view?** Yes.
- **D9. Does assembly value (harness, prompts, leaderboard) stay out of the depth band?** Yes; it
  shows in task breadth, the note and adoption.
- **D10. Is it accepted that large single-language native exams rank above FLORES+ on depth?** Yes,
  with the task count published beside the band.
- **D11. Is a set whose official split is not stated (VMLU) unresolved until a source states it?**
  Yes.
- **D12. Within a task, is a language's band the band of its largest single component?** Yes, as
  the calibration proposed; summing distinct components changes nothing in the sample.

## Limits, and what to check when the other sets are filled

What four sets cannot tell us:

- **Only one native exam has a record.** ThaiExam is the only single-language set filled, so the
  exam results above rest on cited totals, not on records with splits and provenance.
- **Several tasks are barely exercised.** Summarization appears only as SEA-HELM's 100 documents per
  language; sequence labeling only with unknown provenance; no speech, transliteration, retrieval
  or vision-language entries; no `mixed` entry with a `qualifying_count`; one machine-translated
  entry. The provenance rule and the ladder's lower bands are largely untested.
- **The corroboration cap has been seen in two suites only,** and in AfroBench it mostly meets
  FLORES-derived sets (D7).
- **The precision ladder treats items as independent.** Belebele's questions share passages and
  exams cluster by subject, so effective sample sizes are smaller than counts. The bias runs the
  same way for every clustered set and does not reorder the sample.

To check when the other evaluation sets are filled:

- **The count at 5.** Under the package the 5s come from large native exams. R-2026-10-30-l rejected
  12 of 22 at 5; recount against the one-third review trigger once the exams (TurkishMMLU, KazMMLU,
  DarijaMMLU, MILU, SeaExam, LaoBench, INCLUDE) have records.
- **Stated official splits.** VMLU shows that a leaderboard benchmark may not state its test size.
  Expect more unresolved single-language sets, and record their splits when a source states them.
- **Suites with original depth.** IndicGenBench, IndicXTREME and SEACrowd-style hubs will show
  whether the cap behaves as intended when a suite's own items are deep.
- **A speech set** before any speech ladder is adopted (D3), and a judged-generation set with more
  than a few hundred prompts before D2 is reopened.
- **The SEA-HELM leaderboard against its cards.** The record follows the Hugging Face cards; the
  leaderboard's current task list is larger (calibration item 5), which could move SEA-HELM's
  Malay, Burmese, Lao and Khmer.

## Appendix A. The ladders and their references

Ladder (a), every task bounded on 0 to 1: band 1 from 1 item, 2 from 100, 3 from 400, 4 from 1,600,
5 from 6,400 (worst-case 95% half-width ±9.8, ±4.9, ±2.5, ±1.2 points).

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

Measured target languages by band, under ladder (a). Unknown languages are not in the counts.

| Rule | FLORES+ | SEA-HELM | AfroBench |
|---|---|---|---|
| Highest task band | 0: 3, 3: 185 | 2: 3, 3: 7 | 2: 1, 3: 32, 4: 19, 5: 2 |
| Median of task bands | 0: 3, 3: 185 | 2: 8, 3: 2 | 2: 25, 3: 28, 4: 1 |
| Corroborated maximum | 0: 3, 3: 185 | 1: 2, 2: 4, 3: 4 | 1: 3, 3: 36, 4: 13, 5: 2 |
| Corroborated maximum, no corroboration from FLORES sentences | 0: 3, 3: 185 | 1: 2, 2: 4, 3: 4 | 1: 30, 3: 9, 4: 13, 5: 2 |

FLORES+'s three zeros are its dev-only languages (documented zeros). ThaiExam's one language is a 3
under every rule.

**SEA-HELM per language under the package** (task bands on ladder (a); `own` marks SEA-HELM's own
components): Indonesian 3 (translation 3, inference 3 and own 2, reasoning 3, classification 3 and
own 2, instruction following own 2, reading 2, summarization 2, judged own 1); Thai 3; Vietnamese
3; Tamil 3; Javanese 2 (instruction following own 2, translation 2, reasoning 2); Sundanese 2;
Tagalog 2 (instruction following and exam, both own 2); Malay 2 (translation 3, judged 1); Khmer 1
and Burmese 1 (translation 3 only); Lao unmeasured.

**AfroBench under the package:** 5 for Swahili and Yoruba (OpenAI MMMLU's 14,042 questions,
corroborated by NTREX-128); 4 for 13 languages (NTREX-128's 1,997 sentences, corroborated by a
second task at 3); 3 for 36; 1 for Nigerian Fulfulde (SIB-200 only), Tamasheq (FLORES only) and
Tswana (NTREX-128 only); 9 unmeasured.

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