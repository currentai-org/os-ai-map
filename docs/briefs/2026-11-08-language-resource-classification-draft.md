# Language resource classification: a draft for review, 2026-11-08

**Status: draft methodology, not adopted.** Nothing in it takes effect until a ruling in
`docs/rulings/log.yaml` adopts it. No class, threshold, yardstick or membership change follows from
it, and no product moves. #951 stays held throughout (R-2026-11-08-w).

This brief puts on the record a draft of the per-language resource classification that
R-2026-10-30-d places on Artio and that R-2026-10-30-k uses for per-class size yardsticks. An Artio
agent drafted it on 2026-11-08 at the maintainer's request (R-2026-11-08-e), then recomputed it as
v2 under the maintainer's preliminary decisions the same day. This brief records:

- the method and signals;
- the proposed classes and their distributions, v1 and v2;
- a sensitivity analysis;
- the 18 questions the draft raised, each with the draft's recommendation and the maintainer's
  preliminary position;
- an impact analysis connecting the classes to the size caps of the 75 products in
  `language_specific_datasets`.

**The per-language table stays on Artio.** The 2,475-row tables and their recomputation SQL are agent
memories in the `currentai` org:
- `temp.language-classification-draft-2026-11-08.md` and `.csv` (v1);
- `temp.language-classification-v2-sensitivity-2026-11-08.md` and `temp.language-classes-v2-2026-11-08.csv` (v2).

Nothing per-language is copied into this repository until redistribution rights are checked, for
three reasons:
- One source states no license (Joshi et al. 2020).
- One tool publishes counts without terms (wikistats).
- The ISO 639-3 redistribution question raised in the 2026-11-02 specification is still open.

This brief carries only aggregate counts and named examples.

Like the other records in `docs/briefs/`, it describes its sources on the date above and is refreshed
by a new brief, not edited.

## The short answer

- **The architecture is promising.** It uses three independently sourced axes, one each for
  official status, speakers and written material, as R-2026-10-30-k names them. Each axis has an
  explicit `unknown`. The class is reproducible by SQL from the signal columns, and every threshold
  can be revised without re-reading a source.
- **Under the maintainer's preliminary rules (v2), 848 of 2,475 codes get a class and 1,627 get a
  range.** The determinate classes are A 77, B 93, C 230 and D 448. The largest ranges are C-D 1,088
  and B-D 464. The ranges are the honest result: missing evidence is no longer read as a small
  language.
- **Most of the unknowns are on the literature axis.** Separating "no written material found" from
  "no usable measurement" leaves 1,063 individual languages with no literature measurement, because
  GlotLID v3, the language identifier behind FineWeb-2, can label only 1,360 of the 2,475 codes.
- **The yardstick fractions are not ready to adopt.** [The impact section](#impact-on-the-size-caps)
  shows what each candidate scheme would do to the 52 capped products whose stated size reproduces
  today's cap. It also shows that the result for multilingual corpora turns on a rule this brief
  does not settle.
- **Several class assignments need a source check before anything is built:** Hausa, Mali's
  national languages, Tagalog and N'Ko ([below](#points-that-need-a-source-check)).

## Relation to the 2026-11-02 specification

[`2026-11-02-language-resource-classification-spec.md`](2026-11-02-language-resource-classification-spec.md)
proposed a design for the same classification, with decisions D1 to D10, none of them ruled. This
draft agrees with it on robustness and macrolanguages and departs from it elsewhere, so the two
should be ruled together.

| Topic | 2026-11-02 specification | This draft (v2) | Maintainer's preliminary position (2026-11-08) |
|---|---|---|---|
| Structure | Four dimensions; two derived views (a digital-representation class for membership, a three-axis profile for yardsticks); no weighted index (D1) | Three axes combined into an A-D class by equal weights; no membership class | Equal weights provisionally, with A-D a derived view and the three signals kept visible |
| Speaker cut | 10 million (D9) | 1 million | 1 million, provisionally |
| Literature measure | OpenAlex scholarly works, 100,000 or more (D9) | FineWeb-2 words without the Bible share, with Wikipedia and Open Library as corroboration | The draft's approach, with Bible text excluded and inflated Wikipedias guarded against |
| Unknowns | Every value an interval; a class stands only across the whole interval (D5) | Unknown axes give a class range | The same: keep unknowns and compute ranges |
| Absence | An observation only in a list complete by construction; silence from a detector or index is `unknown` (D6) | Absence where GlotLID can label the code is `none_found` (small); otherwise `unmeasured` (unknown) | Distinguish no material found from no usable measurement. The draft's `none_found` treats GlotLID silence as an observation, which D6 would not; [question 8](#the-18-questions) |
| Macrolanguages | Per-source declared mappings; a broader or narrower label gives a bound (D7) | A macrolanguage row takes its members' range; representatives keep the evidence they borrowed in v1 | Do not give a macrolanguage its representative's class |
| Joshi et al. | Excluded; validation reference only (D8) | Excluded from v2's columns | Do not redistribute without permission or a verified license |
| Membership | A digital-representation class decides "underrepresented" (D2, D3) | Not computed | Compute membership impacts after the class definitions are approved |

## Signals

All sources are bulk downloads read on 2026-11-08, except Open Library, which comes from an existing
`currentai` table. Coverage counts how many of the 2,475 codes have a value.

| Signal | Source | License | Coverage | Role |
|---|---|---|---|---|
| Official or regional status | Unicode CLDR release 49, `supplementalData.xml` territory data | Unicode License v3 | 593 codes in CLDR, 133 official somewhere, 123 regional | Primary for the official axis |
| Official language (P37) | Wikidata, current statements on states and first-level subdivisions | CC0 | 369 | Subnational official status; state-level statements without CLDR support read as "recognized" |
| Speakers (P1098) | Wikidata, with the statement's year | CC0 | 884 | Primary for the speaker axis, with CLDR's user estimate; the larger value is used |
| Endangerment (AES) | Glottolog CLDF v5.3 | CC BY 4.0 | 2,393 | Fallback for "few" when no count exists and the language is shifting or worse |
| Web text | FineWeb-2 language distribution, words with the Bible share removed | Repository Apache-2.0; dataset ODC-By 1.0 | 1,370 | Primary for the literature axis |
| Wikipedia | wikistats dump, content articles and active users | No stated license for the tool; the counts are public MediaWiki facts | 346 | Corroboration only |
| Books | Open Library works, from `currentai.language_atlas.src_open_library_books` | CC0 | 192 | Corroboration only |
| Research attention | Joshi et al. 2020 "State and Fate" classes | **No license stated** | 785, matched by name | Used in v1, removed in v2 |
| Code metadata | SIL ISO 639-3 tables, 2026-10-15 release | SIL terms of use | 2,475 | Code scope, type and macrolanguage membership |

Two signal facts shape everything below:
- **Bible text dominates small-language web text.** For 695 codes the Bible makes up more than 90%
  of FineWeb-2 words, so raw word counts would overstate written material for most small languages.
- **Bot-generated Wikipedias are large for some languages with few editors.** Waray has 1.27 million
  articles and 66 active users. So Wikipedia counts only when a second signal agrees.

## The proposed classes

### Axes (v2)

- **Official:**
  - `national`: CLDR official or de facto official in a territory.
  - `subnational`: CLDR official-regional, or Wikidata P37 on a first-level subdivision.
  - Both count as official.
  - `recognized` (a state-level P37 without CLDR official status) is recorded separately and does
    not count.
- **Speakers:**
  - `many` at 1,000,000 or more.
  - `few` below that, or when no count exists but Glottolog rates the language shifting, moribund,
    nearly extinct or extinct. That second case is a tagged fallback.
  - `unknown` otherwise.
- **Literature** is `large` when any of these holds:
  - FineWeb-2 has 1 billion or more words without the Bible share;
  - both Wikipedia (100,000 articles) and Open Library (10,000 works) pass;
  - one of them passes and FineWeb-2 has at least 100 million words.

  It is `small` when measured below those, or `none_found`. It is `unknown` when `unmeasured`.
  English is `large` by override, because FineWeb-2 excludes it.
- **Combined:** one point per axis. A = 3, B = 2, C = 1, D = 0. An unknown axis gives a range.

### Distributions

| Class or range | v1 (draft) | v2 (preliminary rules) |
|---|---|---|
| A | 89 | 77 |
| B | 124 | 93 |
| C | 276 | 230 |
| D | 985 | 448 |
| C-D | 985 | 1,088 |
| B-D | 12 | 464 |
| B-C | 4 | 39 |
| A-D, A-C, A-B | 0 | 23, 5, 8 |
| **Determinate / range** | **1,474 / 1,001** | **848 / 1,627** |

1,129 codes change class or range between v1 and v2:

| Rule | Codes moved | Main movements | Examples |
|---|---|---|---|
| No material found vs. not measured | 884 | D to C-D 450; C-D to B-D 390 | prs B to A-B |
| Joshi removed | 176 | D to C-D 101; C-D to B-D 67 | aaa D to C-D |
| Macrolanguage takes its members' range | 33 | A to A-D 7 | ara, swa, msa, zho A to A-D; hbs B to A |
| Recognized does not count as official | 27 | C to D 13; B to C 11 | hau A to B; bam, lat B to C; cor C to D |
| N'Ko on its own evidence | 1 | C to D | nqo |
| Filipino and Tagalog separate | 1 | A to C | tgl |
| Two rules combined | 7 | | kur, rom, snk, tao, bal, bnn, mwr |

## Sensitivity

Each row changes one rule from v2 and counts the codes whose class or range changes.

| Alternative to v2 | Codes that change | Largest movements |
|---|---|---|
| Speaker cut 100,000 | 284 | D to C 160; C-D to B-C 64; C to B 52 |
| Speaker cut 10 million | 232 | C to D 108; B to C 55; A to B 29 (afr, als, bel, bod) |
| No Glottolog fallback | 449 | C-D to B-D 356; D to C-D 91 |
| Recognized counts as official | 31 | D to C 13; C to B 11; hau B to A |
| FineWeb-2 cut 500 million words | 3 | khm and sin B to A; ary C to B |
| FineWeb-2 cut 10 billion words | 3 | bos and fil A to B; hbs A to A-B |
| Joshi included | 178 | C-D to D 102; B-D to C-D 67 |
| Absence from every source counts as small (v1) | 1,068 | C-D to D 553; B-D to C-D 460 |
| Macrolanguage inherits its representative's class | 23 | A-D to A 7 (ara, lav, mlg, msa, nep, swa, zho) |

Reading the table:
- **The written-material thresholds barely matter.** Moving the FineWeb-2 cut by a factor of two or
  ten changes three codes, because the other signals agree.
- **What matters is how absence and missing counts are read.** Treating absence as small moves 1,068
  codes, and dropping the Glottolog fallback moves 449. Those are rules about evidence, not
  thresholds, and they decide most of the long tail.
- **The speaker cut moves about 250 codes either way** between 100,000 and 10 million.
- **Joshi never makes a code `large`.** Its only effect is to turn unmeasured codes into small, so
  removing it costs measurements for 178 codes and changes no `large` call.

## Points that need a source check

- **Hausa** drops from A to B. Wikidata records it as official only through Niger's state-level
  statement, CLDR 49 gives it no official status, and no Nigerian state carries a P37 for it.
- **Mali's national languages** (Bambara, Dyula, Soninke and others) read as `recognized`. Mali's
  2023 constitution made its national languages official, which CLDR 49 may not yet reflect.
- **Tagalog** lands in C. Without borrowing from Filipino, it loses the FineWeb-2 text, because
  GlotLID v3 files Tagalog under `fil`; v4 reverses that. Its written material then rests on
  Wikipedia and Open Library alone.
- **N'Ko's** speaker figure, 699,310, is CLDR's placeholder of 5% of Guinea's population, with the
  note "No figures available for this language. Estimating at 5%." It is not a survey count.
- **Macrolanguage representatives** (for example arb, swh, zsm) still use the figures they took from
  their macrolanguage in v1. The preliminary rule restricted macrolanguage rows and the other members
  only. Whether representatives also lose that borrowed evidence is open.

## Impact on the size caps

This section connects the v2 classes to the size caps in `language_specific_datasets` (its
`scoring_recipe` note), so that the yardstick fractions can be judged by what they would do. It is a
first pass. It changes no band, and it uses the v2 classes, which are themselves unapproved.

### What can be measured

- **15 of the 75 products carry no size cap:** 11 instruction sets, 3 task annotations (AfriHate,
  NCHLT, SOLD) and SEACrowd. Yardsticks cannot move them.
- **Of the 60 capped products, 8 are set aside:**
  - **No size in the cap's unit (7):**
    - SMOL gives tokens, not pairs.
    - AfriDocMT counts documents, Bloom Library stories, and SMUGRI rows.
    - Glot500-c and BibleTTS cite no figure.
    - Kencorpus mixes text and speech, and the recipe does not say which governs.
  - **Afrivoice (1):** it states 15,000 total hours, which gives a cap of 4 against its recorded 3,
    and its transcribed share is not stated.
- **The other 52 reproduce their recorded cap from their stated size.** Their bands today: 10 at 1,
  15 at 2, 20 at 3, 7 at 4.

**What limits each band today.** A band is the lower of what the rungs give and what the size allows.
No record states the rung band before the cap. So:
- For the 38 products the cap binds, the new cap is an **upper bound** on the new band, not the new
  band.
- The 9 products the rungs bind keep their band. Sarvam-2T is the clearest case: its 2 trillion
  tokens would allow 5, and the rungs give 2.
- For 5, which binds is unclear, and they are treated as upper bounds.

### The schemes tested

Each cell divides today's band thresholds. Ten languages form a reference class R that keeps today's
yardstick in every scheme: English, Mandarin and Chinese, German, French, Italian, Japanese,
Portuguese, Russian and Spanish. Every scheme keeps a one-hour floor for speech band 2.

| Scheme | A text / speech | B | C | D |
|---|---|---|---|---|
| S0 today | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 1 |
| S1 as proposed | 10 / 10 | 100 / 30 | 1,000 / 100 | 10,000 / 300 |
| S2 proposed, class A unrelaxed | 1 / 1 | 100 / 30 | 1,000 / 100 | 10,000 / 300 |
| S3 moderate | 1 / 1 | 10 / 10 | 100 / 30 | 1,000 / 100 |
| S4 light | 1 / 1 | 3 / 3 | 10 / 10 | 30 / 30 |

Parallel text follows text.

**Which class a product takes:**
- A single-language product takes its language's class. Where that class is a range, the
  conservative reading takes the most-resourced possible class, and an optimistic reading takes the
  least.
- **Multilingual corpora need a rule, and this brief does not settle it.** Two are tested:
  - **M1, least relaxed:** the corpus's most-resourced language governs. A corpus that includes
    English or another reference language keeps today's yardstick.
  - **M2, unrelaxed:** every multilingual corpus keeps today's yardstick, because a per-language
    size cannot be inferred from an aggregate total.
- 30 of the 52 are multilingual, and 12 of those state their size per language.

### Results

Products whose band could rise by 0, 1, 2, or 3 or more, out of 52:

| Scheme | M1, conservative | M1, optimistic | M2, conservative |
|---|---|---|---|
| S1 as proposed | 23 / 25 / 3 / 1 | 22 / 22 / 4 / 4 | 34 / 14 / 3 / 1 |
| S2 proposed, A unrelaxed | 44 / 4 / 3 / 1 | 38 / 6 / 4 / 4 | 47 / 1 / 3 / 1 |
| S3 moderate | 44 / 7 / 1 / 0 | 38 / 10 / 3 / 1 | 47 / 4 / 1 / 0 |
| S4 light | 50 / 2 / 0 / 0 | 46 / 5 / 1 / 0 | 50 / 2 / 0 / 0 |

Upper-bound band distribution after the change (M1, conservative), against today's 10 / 15 / 20 / 7 /
0 for bands 1 to 5:

| Scheme | Band 1 | Band 2 | Band 3 | Band 4 | Band 5 |
|---|---|---|---|---|---|
| S1 | 5 | 11 | 12 | 21 | 3 |
| S2 | 7 | 14 | 18 | 13 | 0 |
| S3 | 7 | 15 | 20 | 10 | 0 |
| S4 | 9 | 15 | 21 | 7 | 0 |

### What the results show

1. **Most of the proposal's effect comes from relaxing class A.** Under S1 (M1, conservative), 29
   products could rise, and 21 of them are class A corpora, among them:
   - multilingual Indic corpora (Sangraha, BPCC, IndicVoices);
   - Catalan, Danish, Basque, Ukrainian, Vietnamese and Bengali corpora.

   Class A is, by the classification's own definition, official, widely spoken and with a large
   written record. Relaxing it is the "automatic relaxation for well-resourced languages" the
   maintainer's preliminary position rules out. Without it (S2), 8 products could rise.
2. **The largest changes are single-language corpora in classes B and C.** All are upper bounds.

   | Product | Class | Stated size | Today | S2 | S3 | S4 |
   |---|---|---|---|---|---|---|
   | Korpus Malti | C | 467 million tokens | 1 | up to 4 | up to 3 | up to 2 |
   | Icelandic Gigaword | B | 1.46 billion words | 2 | up to 4 | up to 3 | 2 |
   | Khmer Speech | B | 728 transcribed hours | 2 | up to 4 | up to 3 | up to 3 |
   | Northern Sámi web corpus | C | about 28 million tokens (estimated from bytes) | 1 | up to 3 | up to 2 | 1 |

   ViXSD (class B, 10 hours) could rise from 1 to 2 under S2 and S3.
3. **Multilingual corpora move only under M1.** Under S2 and S3, three class-B multilingual speech
   corpora could rise by one band: NaijaVoices, ZA African Next Voices and AfriVoices-KE. Under M2 they
   stay where they are. M1 lets a corpus be judged by its best-resourced language, but it does not
   check how the size is split across languages. Only 12 of the 30 multilingual products state that
   split.
4. **Products tagged with macrolanguage codes give wide ranges.** These are the reason the optimistic
   column differs from the conservative one. Retagging them with individual codes, as the draft
   recommends, would settle them:
   - Arabic (`ara`): 101 Billion Arabic Words and ArabicWeb24.
   - Quechua (`que`): Llamacha Quechua.
   - Nepali (`nep`): Nepali Text Corpus.
   - Persian (`fas`): NAAB.
5. **The written-material thresholds barely matter here, and the multipliers matter a great deal.** S3
   halves S2's two-band moves, and S4 leaves two products with a one-band rise.

### What this does not establish

- **Real band changes.** No record states its rung band, so every rise above is a ceiling. A product
  whose rungs sit at its current band would not move at all.
- **Membership.** Membership stays with the purpose test (R-2026-10-30-d) and is not computed here.
- **The 8 products set aside**, which need a size in the cap's unit, or a rule for mixed text and
  speech corpora, before any yardstick can be applied to them.
- **Instruction data.** It carries no cap today, and its cap is #951's question, held until the
  classification supplies the policy (R-2026-11-08-w).

The per-product figures are reproducible from `sources/scores/` on `main` at this date and the v2
classes on Artio. The impact script is not committed: it reads class values that stay on Artio until
redistribution is checked.


## The 18 questions

The draft's recommendation comes first in each, then the maintainer's preliminary position where one
was given on 2026-11-08. "Open" means no position yet.

1. **Speaker cut.** *Draft:* 1 million, matching the Language Atlas. *Preliminary:* accept 1 million
   provisionally.
2. **Missing speaker counts.** *Draft:* default them to `few` when not official, tagged. *Preliminary:*
   reject. Missing evidence is not evidence of a small population; keep `unknown` and compute the
   class range. Applied in v2.
3. **The Glottolog fallback** (shifting or worse means few). *Draft:* keep it; it misclassifies 3 of
   158 known cases (Sabaot, Hunsrik, Irish). *Open.* v2 keeps it as a tagged rule because it rests on
   evidence; turning it off moves 449 codes.
4. **Recognized as official.** *Draft:* yes. *Preliminary:* no. Count national and subnational official
   languages and record recognized or protected minority languages separately; recognition does not
   always confer official administrative status (Cornish). Applied in v2.
5. **Subnational official status from Wikidata.** *Draft:* yes. *Preliminary:* count subnational official
   languages. Applied in v2.
6. **Literature written in the language, not documentation about it.** *Draft:* in-language; Glottolog's
   documentation measure stays informational. *Preliminary:* accept the approach.
7. **Wikipedia only with corroboration.** *Draft:* keep it; consider also requiring 100 active users.
   *Preliminary:* accept the guard against inflated editions.
8. **Absence as small.** *Draft:* yes, because GlotLID labels about 2,000 languages. *Preliminary:*
   distinguish no written material found from no usable measurements. Applied in v2 as
   `none_found` versus `unmeasured`. Open point: whether GlotLID silence for a code it can label is
   an observation at all, which the 2026-11-02 specification's D6 would treat as `unknown`.
9. **The Bible-share correction is approximate.** *Draft:* accept for a first version and note it in the
   contract. *Preliminary:* accept excluding Bible-derived text.
10. **Macrolanguages.** *Draft:* tag products with individual codes; a macrolanguage row takes its
    representative's class. *Preliminary:* do not give a macrolanguage its representative's class
    automatically, since its members can differ widely. Applied in v2 as member ranges.
11. **Historical and constructed languages.** *Draft:* flag them and size them by written material alone.
    *Preliminary:* keep them explicitly flagged. Applied in v2 as a flag that does not change the class.
12. **N'Ko.** *Draft:* treat it as a written standard of Manding, with CLDR's figure. *Preliminary:* use
    N'Ko-specific speaker evidence, not the whole Manding population, subject to source verification.
    The CLDR figure is a placeholder (above).
13. **The Joshi license.** *Draft:* ask the authors, or drop the values. *Preliminary:* do not
    redistribute without permission or a verified license. Removed from v2.
14. **Combining the axes.** *Draft:* equal weights. *Preliminary:* accept provisionally; keep the three
    signals visible and the A-D class a derived view.
15. **Yardstick fractions.** *Draft:* text ÷10, ÷100, ÷1,000, ÷10,000 and speech ÷10, ÷30, ÷100, ÷300 by
    class, with a 1-hour speech floor. *Preliminary:* defer. Compute the effect on all 75 products, test
    less aggressive alternatives, count moves of one, two or more bands, inspect the largest, keep the
    1-hour speech floor, and do not relax thresholds for languages that are already well resourced.
    [The impact section](#impact-on-the-size-caps) is the first pass.
16. **Roster changes.** *Draft:* compute them on Artio once thresholds and fractions are ruled.
    *Preliminary:* compute score and membership impacts after the class definitions are approved.
17. **Speakers as the larger of Wikidata and CLDR.** *Draft:* max, because CLDR counts users, including
    second-language users. *Open.* CLDR and Wikidata disagree across 1 million on 38 codes.
18. **The dependency contract.** *Draft:* key on ISO 639-3 and publish the axis and class columns, with
    signal columns as a versioned evidence table. *Open.* It waits on the redistribution checks above.

Also from the maintainer: keep Filipino (`fil`) and Tagalog (`tgl`) as separate identifiers with an
explicit relationship, to avoid double counting. Their overlap is substantial, but their
standardization and official use differ. Applied in v2.

## Sequence

1. Review this classification methodology.
2. Approve the class definitions and thresholds, ruling together on the 2026-11-02 specification's D1
   to D10 where they overlap.
3. Compute score and membership impacts under the approved classes.
4. Approve the yardsticks.
5. Implement.

#951 stays held throughout.
