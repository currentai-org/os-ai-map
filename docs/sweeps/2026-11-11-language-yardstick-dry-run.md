# Language yardstick dry run, 2026-11-11

## Scope

Step 4 of the language-specific restructure (#948). This is a scored dry run of the size
yardsticks R-2026-10-30-k asks for. The size caps in `language_specific_datasets` judge each
language against the resource profile in
[`../reference/language-classification.md`](../reference/language-classification.md) instead of
English alone. **Nothing changes on it.** No multiplier is implemented, no score moves, and #951
stays held. The proposed multipliers are compared against today's unrelaxed reference yardstick.
The comparison covers:
- the multilingual-corpus rule;
- the five IIT Bombay comparisons (R-2026-11-08-d);
- every band change any scheme produces.

## Inputs

- **Products.** The 75 products in `language_specific_datasets` on `main` after #1000
  (`c6637096`). Their capability bands and `languages` lists were checked against the size table
  drafted on 2026-11-08, and none has changed.
  - 60 carry a size cap. 52 of those reproduce their recorded cap from their stated size, and the
    run reads those 52. Their bands today are 10 at 1, 15 at 2, 20 at 3 and 7 at 4.
  - **8 are set aside:**
    - No size in the cap's unit: SMOL, Bloom Library, Glot500-c, BibleTTS, Kencorpus, AfriDocMT
      and SMUGRI.
    - A stated size that does not reproduce the recorded cap: Afrivoice.
- **Profiles.** `currentai.language_representation.classification`, method 1.0.0, read for all
  2,462 codes the 75 products declare. The table is the run after the Open Library extract was
  re-pinned to `main` (`measurements_src` revision 14). Every value matches the run that first
  restored the extract.
  - Among the languages that decide a band here, the restored Open Library evidence settles three:
    - Marathi reads `yes` for large written material.
    - Kazakh and Galician read `no`.
  - Without it, Kazakh Speech Corpus 2 and CorpusNós would carry an unresolved axis.

## Method

**Band model.** A product's band is the lower of what its rungs give and what its size allows. No
record states its rung band before the cap. So a relaxed cap gives an **upper bound** on the new
band wherever the cap binds today, or where the binding is unclear. Where the rungs bind, the band
does not move.

**Schemes.** Each multiplier divides today's thresholds:
- text: 1T / 100B / 10B / 1B tokens;
- parallel text: 1B / 100M / 10M / 1M pairs;
- speech: 100k / 10k / 1k / 100 transcribed hours, with a one-hour floor for band 2.

The 2026-11-08 draft keyed its multipliers on classes A to D. Those classes were the count of
`yes` axes, so here the multipliers are keyed on the count of `yes` axes in a resolved profile.
Three `yes` axes is the reference profile, and every scheme leaves it unrelaxed (R-2026-11-10-k).

| Scheme | 3 yes (reference) | 2 yes | 1 yes | 0 yes |
|---|---|---|---|---|
| S2, the draft's proposal without relaxing the reference profile | 1 / 1 | 100 / 30 | 1,000 / 100 | 10,000 / 300 |
| S3, moderate | 1 / 1 | 10 / 10 | 100 / 30 | 1,000 / 100 |
| S4, light | 1 / 1 | 3 / 3 | 10 / 10 | 30 / 30 |

Each cell is the text-and-parallel multiplier, then the speech multiplier. The draft's S1 also
relaxed the reference profile, and R-2026-11-10-k rules that out. With the reference unrelaxed, S1
is identical to S2.

**Unresolved profiles.** Every resolution of every `unresolved` axis is tried:
- **Applied cap:** the least relaxed resolution. An unresolved axis never relaxes a yardstick, so
  relaxation applies only as far as every possible profile earns it.
- **Sensitivity range:** runs from the least relaxed resolution to the most relaxed.
- **Retained score:** where both ends give the same band, the band stands as if the profile were
  resolved.

**Multilingual rules.**

- **M1, least relaxed.** The language with the most `yes` axes governs, so a corpus that includes
  English keeps today's yardstick.
- **M2, unrelaxed.** Every multilingual product keeps today's yardstick, because a total over
  several languages says nothing about any one of them.
- **M3, pivot excluded.** This is a variant added for this run; it was not proposed. It applies to
  parallel text only: drop the languages with the resolved reference profile (the pivot, usually
  English), then apply M1. It is the rule that would let a parallel corpus be judged by its
  non-English side.

## Results

Rises are counted against today's band, over the 52 products. "Sensitive" counts the products
whose two ends differ.

| Scheme | Rule | Rise 0 / 1 / 2 / 3+ | Bands 1–5 after | Sensitive | Retained despite an unresolved axis | Peer relations broken |
|---|---|---|---|---|---|---|
| S2 | M1 | 41 / 4 / 5 / 2 | 6 / 12 / 19 / 14 / 1 | 4 | 1 | 11 |
| S2 | M2 | 42 / 3 / 5 / 2 | 6 / 12 / 20 / 13 / 1 | 1 | 0 | 10 |
| S2 | M3 | 36 / 7 / 7 / 2 | 3 / 13 / 20 / 14 / 2 | 6 | 2 | 17 |
| S3 | M1 | 42 / 8 / 2 / 0 | 7 / 12 / 23 / 10 / 0 | 4 | 1 | 10 |
| S3 | M2 | 43 / 7 / 2 / 0 | 7 / 12 / 24 / 9 / 0 | 1 | 0 | 9 |
| S3 | M3 | 39 / 11 / 2 / 0 | 6 / 12 / 24 / 9 / 1 | 6 | 2 | 13 |
| S4 | M1 | 47 / 5 / 0 / 0 | 9 / 12 / 24 / 7 / 0 | 0 | 5 | 5 |
| S4 | M2 | 47 / 5 / 0 / 0 | 9 / 12 / 24 / 7 / 0 | 0 | 1 | 5 |
| S4 | M3 | 47 / 5 / 0 / 0 | 9 / 12 / 24 / 7 / 0 | 0 | 8 | 5 |

### Every band change

Each cell is the applied upper bound. "(to n)" is the most relaxed end where an unresolved axis
leaves a range. Bold marks a change from today. A profile reads official / many speakers / large
written material, with U for unresolved. The 32 products not listed keep their band in every cell.

| Product | Size | Profile | Today | S2 M1 | S2 M2 | S2 M3 | S3 M1 | S3 M2 | S3 M3 | S4 M1 | S4 M2 | S4 M3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AfriVoices-KE | 3,000 h | 5 languages: U/Y/N×3, U/Y/U×1, Y/Y/N×1 | 3 | 3 (to 4) | 3 | 3 (to 4) | 3 (to 4) | 3 | 3 (to 4) | 3 | 3 | 3 |
| Aksharantar | 26,000,000 pairs | 21 languages: Y/Y/N×12, Y/Y/Y×5, U/Y/N×2, Y/Y/U×1, Y/N/N×1 | 3 | 3 | 3 | 3 (to 5) | 3 | 3 | 3 (to 4) | 3 | 3 | 3 |
| Bharat Parallel Corpus Collection | 230,000,000 pairs | 23 languages: Y/Y/N×12, Y/Y/Y×6, U/Y/N×3, U/U/N×1, Y/N/N×1 | 4 | 4 | 4 | **5** | 4 | 4 | **5** | 4 | 4 | 4 |
| ChrEn | 14,000 pairs | `chr` U/N/N, `eng` Y/Y/Y | 1 | 1 | 1 | **3 (to 4)** | 1 | 1 | **2 (to 3)** | 1 | 1 | 1 |
| CorpusNós | 1.92B tokens | `glg` Y/Y/N | 2 | **4** | **4** | **4** | **3** | **3** | **3** | 2 | 2 | 2 |
| Icelandic Gigaword Corpus | 1.46B words | `isl` Y/N/N | 2 | **5** | **5** | **5** | **4** | **4** | **4** | **3** | **3** | **3** |
| Jojajovai | 30,855 pairs | `grn` Y/Y/N, `spa` Y/Y/Y | 1 | 1 | 1 | **2** | 1 | 1 | 1 | 1 | 1 | 1 |
| Kazakh Speech Corpus 2 | 1,200 h | `kaz` Y/Y/N | 3 | **4** | **4** | **4** | **4** | **4** | **4** | 3 | 3 | 3 |
| Khmer ASR Cultural Dataset | 728 h | `khm` Y/Y/N | 2 | **4** | **4** | **4** | **3** | **3** | **3** | **3** | **3** | **3** |
| Korpus Malti | 467M tokens | `mlt` Y/N/N | 1 | **4** | **4** | **4** | **3** | **3** | **3** | **2** | **2** | **2** |
| Latxa Corpus | 4.20B tokens | `eus` Y/U/N | 2 | **4 (to 5)** | **4 (to 5)** | **4 (to 5)** | **3 (to 4)** | **3 (to 4)** | **3 (to 4)** | **3** | **3** | **3** |
| Llamacha monolingual Quechua corpus | 93M bytes | `que` Y/Y/N | 1 | **2** | **2** | **2** | 1 | 1 | 1 | 1 | 1 | 1 |
| NaijaVoices | 1,800 h | `hau` U/Y/U, `ibo` Y/Y/N, `yor` Y/Y/N | 3 | 3 (to 4) | 3 | 3 (to 4) | 3 (to 4) | 3 | 3 (to 4) | 3 | 3 | 3 |
| Nepali Text Corpus | 6,875M bytes | `nep` Y/Y/N | 2 | **4** | **4** | **4** | **3** | **3** | **3** | **3** | **3** | **3** |
| Pralekha | 3,000,000 pairs | 12 languages: Y/Y/Y×6, Y/Y/N×6 | 2 | 2 | 2 | **4** | 2 | 2 | **3** | 2 | 2 | 2 |
| Northern Sámi web corpus | 28M bytes | `sme` Y/N/N | 1 | **3** | **3** | **3** | **2** | **2** | **2** | 1 | 1 | 1 |
| ViXSD | 10 h | `xho` Y/Y/N | 1 | **2** | **2** | **2** | **2** | **2** | **2** | 1 | 1 | 1 |
| Vuk'uzenzele corpus | 60,000 pairs | 11 languages: Y/Y/N×8, Y/Y/Y×2, Y/N/N×1 | 1 | 1 | 1 | **2** | 1 | 1 | 1 | 1 | 1 | 1 |
| WAXAL | 1,250 h | 29 languages: U/Y/N×13, Y/Y/N×11, U/N/U×2, Y/Y/U×1, … | 3 | 3 (to 4) | 3 | 3 (to 4) | 3 (to 4) | 3 | 3 (to 4) | 3 | 3 | 3 |
| ZA African Next Voices | 3,000 h | 7 languages: Y/Y/N×6, Y/N/N×1 | 3 | **4** | 3 | **4** | **4** | 3 | **4** | 3 | 3 | 3 |

Sizes in bytes are divided by 4 for the text thresholds, as on 2026-11-08.

### The five IIT Bombay comparisons

R-2026-11-08-d keeps ChrEn, Jojajovai, OLDI Seed, SMOL and AfriDocMT one band below IIT Bombay
English-Hindi until language-specific thresholds are implemented. IIT Bombay's own languages,
English and Hindi, both have the reference profile, so its band stays at 2 under every scheme and
rule.

| Product | Today | M1, any scheme | M2, any scheme | M3 |
|---|---|---|---|---|
| ChrEn (14,000 pairs; Cherokee U/N/N) | 1 | 1, retained | 1, retained | S2: 3 (to 4). S3: 2 (to 3). S4: 1. **Breaks under S2 and S3.** |
| Jojajovai (30,855 pairs; Guarani Y/Y/N) | 1 | 1, retained | 1, retained | S2: 2. S3 and S4: 1. **Breaks under S2.** |
| OLDI Seed (6,193 pairs per language; 40 languages) | 1 | 1, retained | 1, retained | 1 in every scheme, retained |
| SMOL | 1 | not computed | not computed | not computed |
| AfriDocMT | 1 | not computed | not computed | not computed |

SMOL states translated tokens and AfriDocMT documents, and neither states a pair count, so neither
can be placed against a pair threshold. Under M1 and M2 the English side governs, so all five
comparisons hold. They break only under M3, where a corpus is judged by its non-English side.
ChrEn's range there comes from Cherokee's unresolved official status.

### Peer relations

Many capability notes place a product relative to a peer in the same category. Such a relation is
recorded as `at`, `one_below` or `two_below`, and every one was measured on the English-scale
yardstick. Today every relation holds. A relaxed cap moves a product while its peer stays on the
reference yardstick, so the relation no longer describes the two bands.

- **S4 breaks 5:**
  - Icelandic Gigaword `at` Danish Dynaword;
  - Korpus Malti `one_below` Danish Dynaword;
  - Nepali Text Corpus `two_below` Sangraha;
  - Khmer ASR Cultural Dataset `two_below` IndicVoices;
  - L3Cube-MahaCorpus `one_below` Latxa.
- **S3 under M2 breaks 9:** the five above, plus Northern Sámi web corpus `one_below` Danish
  Dynaword, SMUGRI `at` Northern Sámi web corpus, Kazakh Speech Corpus 2 `one_below` IndicVoices,
  and ViXSD `one_below` BibleTTS.
- **S2 under M3 breaks 17.**

Any scheme that is adopted needs each broken relation re-pointed to a peer with the same profile,
or re-attested in the implementation PR.

### Unresolved profiles

Four products have a range under S2 or S3 with M1. Under M2, only Latxa Corpus has one.

- **Latxa Corpus.** Basque's speaker interval straddles 1,000,000. At the least relaxed end Basque
  reads as many speakers, which gives S2 4 and S3 3. At the other end it reads as few, which gives
  S2 5 and S3 4. Under S4 both ends give 3, so the score is retained.
- **NaijaVoices, AfriVoices-KE and WAXAL.** Under M1 the governing language carries unresolved
  axes: Hausa's official status and written material, for example. The least relaxed end makes it
  a reference language and keeps the band at 3. Under M2 they keep today's yardstick, and under S4
  both ends agree.
- **Retained.** Under M1 and M3, Inkuba-Mono carries an unresolved axis, and both ends give the same
  band. Its rungs set its band, so no yardstick moves it.

## What this shows

1. **The multiplier size matters more than the multilingual rule.**
   - S2 moves 10 to 16 products, depending on the rule, and two of them by three bands or more. It
     puts the Icelandic Gigaword Corpus at band 5, the band of the largest English corpora.
   - S3 moves 9 to 13, and none by more than two bands.
   - S4 moves 5 under every rule, each by one band.
2. **Nearly all movement is single-language text and speech corpora** for languages with official
   status that miss at least one other axis: Icelandic, Maltese, Northern Sámi, Galician, Basque,
   Nepali, Kazakh, Khmer and isiXhosa. Their bands today are pulled down by the English-scale
   comparison R-2026-10-30-k set out to remove.
3. **The multilingual rule decides four products and the parallel-text comparisons.**
   - M1 and M2 differ only for ZA African Next Voices, which M1 lifts from 3 to 4 under S2 and S3,
     and for the ranges of the three speech corpora above.
   - M3 is the only rule that moves parallel text. It lifts BPCC to 5, Pralekha to 3 or 4 and,
     under S2, the Vuk'uzenzele corpus to 2. It also breaks two of the five IIT Bombay comparisons.
4. **Unresolved axes rarely matter.** Under M2, one product is sensitive under S2 and S3, and none
   under S4.
5. **Every adopted scheme breaks peer relations.** These need re-pointing in the same PR that
   applies the multipliers.

## What this does not establish

- **Real bands.** Every rise is an upper bound. A product whose rungs sit at today's band would not
  move.
- **The 8 products set aside**, which need a size in the cap's unit, or a rule for mixed text and
  speech, before any yardstick applies to them.
- **Instruction data.** It carries no cap today. Its cap is #951's question, which stays held.
- **Keying on the count of `yes` axes.** The three profiles with two `yes` axes share one
  multiplier here, as in the draft. Keying on large written material alone, or on another
  combination, is a different proposal and is not tested.

## Decisions for the maintainer

None is approved by this record. If one is approved, it is implemented in its own PR.

1. **Scheme.** S2, S3 or S4, or another set of multipliers. **Recommendation: S3.** S2 lifts a
   1.46-billion-word Icelandic corpus to the band of trillion-token English corpora. S4 moves
   Northern Sámi and Maltese corpora by at most one band. S3's steps of a factor of 10 match the
   spacing of the written-material bands.
2. **Multilingual rule.** M1, M2 or M3. **Recommendation: M2.** A total over several languages says
   nothing about any one of them. M2 leaves only one product sensitive, and it keeps all five IIT
   Bombay comparisons.
3. **The IIT Bombay comparisons.** Under M1 and M2 all five hold. Retire the "provisional" status of
   R-2026-11-08-d then, or keep it until SMOL and AfriDocMT state a pair count?
4. **Peer relations.** Re-point each broken relation to a peer with the same profile in the
   implementation PR?
