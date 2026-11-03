# Depth calibration: the full evaluation-set roster, 2026-11-03

## Scope

R-2026-11-02-c asks for the complete band distribution to be inspected before the depth ladder
changes any score, and R-2026-11-02-k holds every published score until the lineage registry, the
task-family rules, a full-roster calibration and the sensitivity tests are validated. This is the
full-roster calibration. It covers the 22 sets the 2026-10-30 dry run
([`2026-10-30-language-specific-eval-sets-dry-run.md`](2026-10-30-language-specific-eval-sets-dry-run.md))
places in `language_specific_eval_sets`: the 21 provisional evaluation sets and the AmericasNLP
shared-task data.

Four of them already had per-language coverage records (FLORES+, ThaiExam, SEA-HELM, AfroBench).
This pass writes coverage records for the other 18, and a curated lineage record for every component
they use that the registry did not have. It changes no capability score, value, note, `relative_to`
or `last_verified`; the bands below are what the ruled method computes, not what the map publishes.

What changed:

- `capability.language_coverage` and `capability.pivot_languages` for FLEURS, Belebele, SIB-200,
  AmericasNLP, Lahaja, INCLUDE, ArabicMMLU, DarijaMMLU, Khayyam Challenge, TurkishMMLU, MILU,
  IndicGenBench, IndicXTREME, KazMMLU, SeaExam, VMLU, LaoBench and IndoNLU, with the capability
  sources they cite.
- `sources/lineage.yaml`: 38 new components and 27 new collections, and one correction to an existing
  record (FLORES+'s N'Ko text, below).
- `languages` on two products: `otz` added to AmericasNLP, and `brx`, `kas` and `mni` added to
  IndicXTREME, from the sets' own papers.

After the maintainer answered the decisions below (R-2026-11-03-a to -h), these changes
followed. SIB-200's Arabic is recorded as `arb`. IndicXNLI's qualifying counts are its paper's
verified column. The provenance rule now counts reviewed machine translation
(`build/evidence_status.py`, `docs/reference/capability.md`, the schema), which also makes all
2,002 IndicXParaphrase test items in each of its ten languages qualify: annotators verified and,
where needed, corrected every machine translation and wrote every paraphrase themselves. A sweep of
every coverage entry found no other entry the rule moves. SeaExam's MMLU-SEA has no review stated
("curated" in its paper refers to the question selection), and IndicXNLI's Gujarati, Punjabi and
Tamil have no verified items.

A second review then asked for three things, and each is now in the record. The calibration
reproduces from the repository: `build/depth_calibration.py` computes every figure below from
`sources/`, and `tests/test_depth_calibration.py` pins them. INCLUDE's Arabic and Turkish pools
are the parent benchmarks' own text, as its lineage record says, so they count as imported items,
not INCLUDE's own. Its Persian pool joins the Khayyam Challenge's questions with exams INCLUDE
collected, so it counts with the mixed pools (a third review caught an earlier reading that
treated it as wholly imported). And DarijaMMLU's review turned out to have no stated scope: its paper's
account of how the set was built names only translation by Claude 3.5 Sonnet, and its card
describes "manual review" without saying how many items it touched. R-2026-11-03-h makes such an
entry unresolved (`review_scope: unstated`), so DarijaMMLU no longer counts at band 5.

## How the evidence was gathered

Four groups worked in parallel, each from `main`, each set by one brief: read the rulings and
`docs/reference/capability.md`; record only per-language counts a source states, never a set-wide
total divided across languages (R-2026-10-30-l); record the split under the source's name and mark
only the evaluation split official; take provenance from what the source states and use `unknown`
when it is silent; cite every figure from a `capability.sources` entry fetched with
`build.fetch_source`. Every quoted fragment in the new `shows` text was checked against the body it
cites: 107 (exams), 118 and 57 (Indic score and lineage records), 57 (multilingual) and the SEA
group's, with none missing. The four groups' lineage records were combined record by record and
each of the 138 records was checked against the branch it came from.

## Method

The computation follows the rulings exactly; nothing in it is tuned to this roster.

- **Entries.** Only official-evaluation entries count (R-2026-11-01-d). `build/evidence_status.py`
  gives each one its status (R-2026-11-02-e): an unresolved entry (unknown provenance, a task family
  with no measurement model, a unit no count model reads) gives no band; a measured zero
  (unreviewed machine translation, generated items, a documented zero) gives band 0; otherwise the qualifying count gives a provisional band on the count ladder of 100, 400, 1,600
  and 6,400 items (R-2026-11-02-b, -c).
- **Within a task.** The highest band of one component, never a sum (R-2026-11-02-g).
- **Across tasks.** D = max(O, max over imported components i of min(b_i, C_i + 1))
  (R-2026-11-02-k), with C_i the best band among the language's other components that are
  independent of i under `build.lineage.pair_status`, each component resolved in its own task and
  split; imports on the same task never back one another (R-2026-11-01-c).
- **Own items.** A suite's own items count in full (R-2026-11-03-c). The product's own slug is
  its own, and so are items a suite's paper presents as its own under a second slug, scoped to the
  languages where the suite made them: SEA-HELM's two judged sets (the audit's precedent),
  IndicXTREME's IndicCOPA, IndicQA, IndicXParaphrase and IndicSentiment, and IndicGenBench's
  XQuAD-In in full, FLORES-In for its seven new languages, CrossSum-In except the ten languages
  that may reuse CrossSum, and XorQA-In except Bengali and Telugu. The schema does not carry these
  claims yet; `build/depth_calibration.py` holds them, and `capability.own_components` will.
  The scope runs the other way for INCLUDE: its own slug is not its own in Arabic and Turkish,
  where the lineage record names ArabicMMLU and TurkishMMLU as the parents whose text it carries
  (D5, R-2026-11-02-k).
- **Across languages.** The median over target languages (`languages` less `pivot_languages`), with
  languages that have no usable measurement filled at 0 and at 5; the band stands only where both
  agree (R-2026-11-01-a). Breadth bonus median + 0.5 x (1 - 1/n) over languages with a band above
  zero (R-2026-10-30-i, R-2026-11-01-b).
- **Face value.** The same median of each language's highest single task band, uncapped, published
  beside the corroborated band (R-2026-11-02-o).
- **Sensitivity.** Run (a) gives unverified lineage pairs no backing; run (b) treats them as
  independent (R-2026-11-02-i).

Every band here is provisional: a count-based ceiling, with statistical precision not independently
estimated (R-2026-11-02-d, -e). No estimation method is approved, so nothing is estimated.

## Results

| Set | Score now | Corroborated (a) | (b) | Face value | Bonus | Measured / targets | Capped languages |
|---|---|---|---|---|---|---|---|
| FLORES+ | 5 | 3 | 3 | 3 | 3.50 | 188 / 215 | 0 |
| FLEURS | 5 | unresolved (0-5) | same | unresolved | | 0 / 101 | 0 |
| Belebele | 5 | 3 | 3 | 3 | 3.50 | 114 / 114 | 0 |
| SIB-200 | 3 | 2 | 2 | 2 | 2.50 | 194 / 195 | 0 |
| INCLUDE | 4 | 3 | 3 | 3 | 3.49 | 44 / 44 | 3 |
| AfroBench | 5 | 1 | 1 | 3 | 1.49 | 56 / 63 | 37 |
| MILU | 3 | 4 | 4 | 4 | 4.45 | 10 / 10 | 0 |
| IndicGenBench | 3 | 3 | 3 | 3 | 3.48 | 29 / 29 | 1 |
| IndicXTREME | 4 | 4 | 4 | 4 | 4.47 | 19 / 21 | 0 |
| Lahaja | 3 | unresolved (0-5) | same | unresolved | | 0 / 1 | 0 |
| SEA-HELM | 5 | 2 | 2 | 3 | 2.45 | 11 / 11 | 4 |
| SeaExam | 3 | 3 | 3 | 3 | 3.38 | 4 / 4 | 1 |
| ThaiExam | 4 | 3 | 3 | 3 | 3.00 | 1 / 1 | 0 |
| VMLU | 4 | unresolved (0-5) | same | unresolved | | 0 / 1 | 0 |
| LaoBench | 3 | 4 | 4 | 4 | 4.00 | 1 / 1 | 0 |
| IndoNLU | 4 | unresolved (0-5) | same | unresolved | | 0 / 1 | 0 |
| ArabicMMLU | 5 | 5 | 5 | 5 | 5.00 | 1 / 1 | 0 |
| DarijaMMLU | 2 | unresolved (0-5) | same | unresolved | | 0 / 1 | 0 |
| TurkishMMLU | 3 | 5 | 5 | 5 | 5.00 | 1 / 1 | 0 |
| KazMMLU | 3 | 5 | 5 | 5 | 5.25 | 2 / 2 | 0 |
| Khayyam Challenge | 4 | 5 | 5 | 5 | 5.00 | 1 / 1 | 0 |
| AmericasNLP | 3 | 1 | 1 | 3 | 1.45 | 10 / 10 | 9 |

"Score now" is the published capability score, set by the interim same-language peer ladder; the
other columns are depth bands, a different measure, so the two are not expected to agree.

**The band-5 check (R-2026-11-02-c).** 4 of 22 sets compute to 5: ArabicMMLU, TurkishMMLU,
KazMMLU and Khayyam Challenge, all large native knowledge exams (three single-language, KazMMLU
two-language), as R-2026-11-02-q anticipated. That is 18%, below the one-third review trigger
(7.3 sets). The trigger does not fire. All four rest on one task, multiple-choice exams: the
method takes the strongest single task per language and gives no credit for task breadth beyond
the bonus inside a band.

**Resolved.** 17 of 22 sets resolve. The five that do not:

- FLEURS and Lahaja are speech sets. Speech has no measurement model (R-2026-11-02-l), so every entry
  is unresolved, as ruled.
- VMLU: no source states the size of its test split, whose answers are held for its leaderboard, so
  Vietnamese has no qualifying entry (R-2026-11-02-r).
- IndoNLU: its sources describe genre and collection (crawled reviews, tweets, news) but not who
  wrote the text, so every entry's provenance is unknown and its depth is unknown.
- DarijaMMLU: its machine translation was reviewed to an extent no source states, so its depth is
  unknown (R-2026-11-03-h). A source saying every item was reviewed would make it 5.

**Sensitivity to lineage.** Runs (a) and (b) agree for all 22 sets. No set's band depends on
treating unverified lineage as independent.

**Sensitivity to the own-items reading.** With IndicXTREME's and IndicGenBench's second-slug sets
treated as imports instead, IndicXTREME stays 4 and IndicGenBench 3; only their per-language
distributions move (7 and 9 languages capped to 1). Scoping the claims as R-2026-11-03-c does
caps one IndicGenBench language, Nepali, whose CrossSum-In items may be reused CrossSum data. The
reading changes no set band.

**Sensitivity to INCLUDE's mixed pools.** In ten more languages (Albanian, Chinese, French,
German, Italian, Lithuanian, Persian, Polish, Portuguese and Vietnamese) INCLUDE's paper says the
pool joins existing benchmark data with exams it collected, with no per-language share. They count
as its own here. Treated as imported, all ten fall to 1 with the two above, and INCLUDE stays 3
with the same bonus.

**Where corroboration caps.** A language is capped when its corroborated band sits below its face
value. Six sets have capped languages, and three of them lose depth at the set level. AfroBench (37
capped languages) and SEA-HELM (4) were described in the depth brief and the lineage audit.
SeaExam (1): its Chinese, whose qualifying items are imported M3Exam questions, falls from 3 to 1,
and the set stays 3. IndicGenBench (1): Nepali falls from 3 to 1, and the set stays 3. INCLUDE
(2): Arabic and Turkish fall from 3 to 1, since nothing independent of the parent benchmarks backs
them inside INCLUDE, and the set stays 3.
AmericasNLP (9): its
AmericasNLI test sets are imported translations of XNLI, and nothing independent of them on another
task measures those nine languages, so each sits at one band above nothing; its own Chatino test set
(1,000 sentences) is the one language at 3.

## Decisions, as ruled

Each was put to the maintainer on 2026-11-03; the answers are R-2026-11-03-a to -g, and -h
narrows the second. Three were delegated to a Codex review, whose recommendations were adopted.

1. **TurkishMMLU's 5 rests on questions the public cannot see** (R-2026-11-03-a). The official test
   split is 9,807 questions, obtainable by email request; the Hub holds 900 (100 per subject) and
   the evaluation harness scores those. Ruled: depth counts the official split's test questions,
   and whether they are public is an openness attribute. Turkish stays band 5.
2. **DarijaMMLU's "manual review"** (R-2026-11-03-b). Its card says "machine translation and manual
   review" and "manual curation for quality control". Ruled: machine translation that a source says
   people reviewed counts toward depth, replacing R-2026-11-01-h. The entry stays
   `machine_translated` with `human_validated: true`; the counting rule changed, not the record.
   A later check found no source saying how far the review went, and R-2026-11-03-h requires the
   review to cover the items, so DarijaMMLU is unresolved rather than 5.
3. **Own items under a second slug** (R-2026-11-03-c). Ruled: `capability.own_components`, cited
   claims scoped by language, task or split, in a schema PR of its own before the ladder PR. The
   scopes above follow it.
4. **IndicXNLI's qualifying portion** (R-2026-11-03-d). Ruled, following from 2: every item its
   paper's Table 9 counts as verified qualifies, not only the corrected ones (Assamese 1,918 to
   3,000, Hindi 1,142 to 4,000). IndicXNLI is an import that does not set IndicXTREME's band, which
   stays 4. The same rule makes IndicXParaphrase qualify in full, which lifts Punjabi from 3 to 4
   without moving the set band or its bonus.
5. **KazMMLU's Russian** (R-2026-11-03-e, delegated). Ruled a target: its items are separate
   Kazakhstani exam questions, not translations, and the title names both languages. Kazakh alone
   gives the same band 5.
6. **SeaExam's Chinese** (R-2026-11-03-f, delegated). Ruled a target: SeaExam carries Chinese
   evaluation configurations, and imported items do not make a language a pivot. SeaExam stays 3.
7. **Two language codes** (R-2026-11-03-g, delegated). FLEURS keeps `tgl`, its paper's code, with
   `fil` recorded as the Hub's. SIB-200's Arabic is now `arb`, the code its `arb_Arab` configuration
   supports, matching FLORES+ (#965). Neither moves a band.

## What the sources contradict

- **KazMMLU:** its paper gives 10,969 Kazakh and 12,031 Russian questions; the data files hold 9,906
  and 13,094, dev included. The records follow the data files, by R-2026-11-02-a's precedent; the
  product description still repeats the paper's figures.
- **TurkishMMLU:** the product comments and capability `value` say 1,845 rows are posted openly. That
  counts the Hub's "All" configuration twice; the Hub holds 945 distinct rows (900 test, 45 dev).
- **INCLUDE:** the Hub's test splits total 22,639; the card says 22,637 and the paper 22,635. Arabic,
  Greek and Russian hold 552 each, above the paper's "maximum of 550".
- **Khayyam Challenge:** its gated terms forbid "creating another benchmarking dataset out of the
  PersianMMLU dataset", yet INCLUDE consolidated it. The Hub page no longer shows the ParsBench Space
  its capability source quotes.
- **SeaExam:** the paper says the authors collected its exam questions with native linguists; the
  card and README call the same configurations "M3Exam (with adjustments)". The Thai and Vietnamese
  exam lineage stays `origin: unknown`.
- **IndicXTREME:** the IndicQA rows sum to 18,586 against the paper's total of 18,579, and the
  description says "20 Indian languages" where the paper's tables evaluate 21.
- **FLORES+ N'Ko:** SIB-200's paper says N'Ko "was recently added to Flores-200", and NLLB's FLORES-200
  README has no `nqo_Nkoo` row, so FLORES+'s main translation effort does not cover it. The
  `flores-plus` lineage record now carries an `nqo` override with no effort, the one correction to an
  existing record.

## Not established

- Per-language utterance totals for Lahaja and per-language hours for FLEURS.
- Who translated N'Ko for FLORES-200, and FLORES+'s text in its gated-card languages.
- CrossSum-In's nine reused CrossSum languages, which the paper does not name; ten are left unknown.
- Naamapadam's Gujarati, Kannada and Marathi counts (the paper rounds them, the card defers to it).
- VMLU's test-split size.

## Next

When these bands are accepted, the `capability.own_components` schema lands in its own PR
(R-2026-11-03-c), carrying the scopes `build/depth_calibration.py` now holds, INCLUDE's included,
and then the ladder PR implements the method in
`build/` and moves the evaluation sets into `language_specific_eval_sets` with their new capability
scores, the evidence status and the R-2026-11-02-o companion figures, one PR with publication, as
R-2026-10-30-l set out. Until then no published score changes.
