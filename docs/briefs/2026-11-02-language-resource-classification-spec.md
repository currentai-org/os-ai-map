# Language resource classification: a specification for Artio, 2026-11-02

This brief specifies the per-language resource classification that R-2026-10-30-d puts on Artio
(the OSO warehouse) and that this repository will read as a dependency contract. It implements the
methodology behind R-2026-10-30-d (membership of `language_specific_datasets`) and R-2026-10-30-k
(per-class yardsticks for the size caps). It is design only. It writes nothing to the warehouse and
changes nothing in `warehouse/`, `sources/` or `build/`. The contract entry below is a proposal and is
not added to `warehouse/dependencies.yaml`.

Like the other records in `docs/briefs/`, it describes its sources on the date above and is refreshed
by a new brief, not edited. Every figure comes from a source fetched on that date with
`build.fetch_source` (Appendix E lists them with their digests) or from `sources/` on `main` at the
same date.

## What the classification is for

The classification **contextualizes depth measurements. It is not a prerequisite for the depth
ladder.** Evaluation depth (R-2026-10-30-i, R-2026-11-01-a to -h) measures the evidence a dataset
holds for one language and task. The classification says how resourced that language is. The two
never feed each other: no depth band reads a resource class, and no resource class reads a dataset's
depth. They meet in two places only, both downstream:

- **Membership** (R-2026-10-30-d). Whether a dataset belongs in `language_specific_datasets` turns on
  the purpose test plus whether its target languages are underrepresented. The classification
  answers the second half.
- **Yardsticks** (R-2026-10-30-k). Which size yardstick a capped dataset is measured against depends
  on its language's class. This brief defines the classes. It does not set the yardsticks'
  thresholds, which belong to the recipe PR.

## The short answer

- **Four dimensions, kept separate.** Official or regional status, speaker population, written and
  academic literature, and digital and web presence. Each is published on its own, from named
  sources, with its own `unknown`.
- **Every value is an interval of bands.** A measured value is one band. A missing one is the full
  range, never zero. A class or verdict stands only when it holds across the whole interval, which is
  the robustness test of R-2026-11-01-a applied to languages.
- **Two derived views, one per ruling, and no weighted index.** A *resource class* (high, mid, low,
  very low) is the robust median of three resource measures: web share, Wikipedia articles and
  scholarly works. Web share is one vote of three, never the rule. It feeds membership. A *yardstick
  profile* reads three yes-or-no axes from R-2026-10-30-k (official, many speakers, large literature)
  and feeds the caps.
- **One table on Artio, read through two contracts.** `currentai.language_resources.classification`
  holds one row per ISO 639-3 code. Its input table, `language_resources.measurements`, needs a
  contract too, because the dependency gate follows a mirror file's reads.
- **Validation.** 162 products declare 2,971 distinct codes. Each resource source reaches 158 to 346
  of them directly, and 2,482 have no resource observation at all. The current hand-made calls are
  reproduced for Chinese, Japanese, Spanish and Portuguese. Korean, Indonesian, Turkish, Ukrainian
  and Swedish come out differently, and so do Arabic and Vietnamese if the line is drawn lower.
  Nothing is decided here: the line is decision D3.

## Methodology

### Dimensions and measures

| Dimension | Measure | Recommended source | Absence means |
|---|---|---|---|
| Official or regional status | Official at national level, at regional level, or neither | Unicode CLDR territory data (`_officialStatus`), with Wikidata P37 on sovereign states as a second witness | Not national, because 250 of CLDR's 258 territories name an official or de facto official language, and the other eight are uninhabited or placeholder territories. Regional or none is `unknown`. |
| Speaker population | Speakers, banded by order of magnitude | CLDR territory population × language share, and Wikidata P1098 | `unknown` |
| Written and academic literature | Scholarly works whose metadata is in the language | OpenAlex `language`, grouped | `unknown`, because the detector does not cover most languages |
| Digital and web presence | (a) Share of web pages | Common Crawl's published CLD2 language statistics, latest crawl | `unknown`, because CLD2 detects only 160 languages |
| | (b) Wikipedia content articles | Wikimedia site matrix with per-edition counts | An observed zero: the list of Wikipedia editions is complete. Bounded above where a macrolanguage edition may hold the language. |
| Context, not class inputs | Descriptive status (Glottolog MED), endangerment (Glottolog AES) | Glottolog CLDF | `unknown` |

Bands for the three resource measures sit at powers of ten:

| Band | Web share | Wikipedia articles | Scholarly works |
|---|---|---|---|
| A | ≥ 1% of pages | ≥ 1,000,000 | ≥ 1,000,000 |
| B | 0.1% to 1% | 100,000 to 1,000,000 | 100,000 to 1,000,000 |
| C | 0.01% to 0.1% | 10,000 to 100,000 | 10,000 to 100,000 |
| D | < 0.01% | < 10,000 | < 10,000 |

Speakers use five bands: A ≥ 100M, B 10M to 100M, C 1M to 10M, D 100k to 1M, E < 100k. Where CLDR and
Wikidata disagree, the interval runs between them. For Swahili they span 15M to 194M, because CLDR
counts second-language use.

**Macrolanguages.** Sources report at different levels: Common Crawl and OpenAlex say `ara` and
`zho`, while `languages` often says `arb` and `cmn`. Three rules:

1. **A macrolanguage code** measures itself plus its members' own labels.
2. **An individual code that CLDR aliases to its macrolanguage** takes the macrolanguage's value as
   its own. CLDR's `languageAlias` with reason `macrolanguage` lists 63 such pairs, among them
   `cmn`→`zh`, `arb`→`ar`, `zsm`→`ms`, `pes`→`fa`, `swh`→`sw`, `ekk`→`et`, `quz`→`qu` and
   `gug`→`gn`. This is a sourced rule, not a hand list.
3. **Any other member** is bounded. Its interval runs from its own label up to its own label plus the
   macrolanguage's value. Moroccan Arabic (`ary`) is somewhere between its own count and Arabic's.

### How the dimensions combine

**Recommendation: keep the four dimensions separate and derive two views, with no weighted index.**
The two rulings ask different questions, and an index would answer neither well. Membership asks how
much material exists in a language. The yardsticks ask which comparison is fair. Folding speakers
into a resource index would make membership relative to population, which is a separate decision
(D3). Folding web share into the yardstick would add an axis R-2026-10-30-k did not name. Weights
would have no defensible basis, and an index hides which signal moved a language. Separate
dimensions also keep `unknown` local: a missing speaker count cannot unsettle a resource class that
does not read it.

**Resource class** (membership). Take the bands of web share, Wikipedia articles and scholarly works,
each as an interval, and compute the median twice: once with every interval at its best end and once
at its worst. If the two agree, that band is the class: high (A), mid (B), low (C) or very low (D).
If they differ, the class is `unresolved` and both ends are published. If no measure has any
observation, the class is `unknown`. With three measures, two agreeing observations settle the class
whatever the third is, so no single signal decides it.

**Yardstick profile** (caps). There are three axes. `official` is national or regional status.
`many_speakers` is at or above a speaker cut. `large_literature` is at or above a scholarly-works cut.
Each axis reads yes, no or `unresolved` by the same interval rule. D9 proposes the cuts.

### Feeding membership and the yardsticks

**Membership** follows D5 of the
[2026-10-30 brief](2026-10-30-language-specific-datasets-structure.md#decisions) and
R-2026-10-30-d. The purpose test comes first. Then a dataset is in when any of its target languages is
robustly underrepresented, and out when every target language is robustly not. Otherwise the purpose
test decides on its own, and the row says so. There is no majority rule. Because English is never
underrepresented, this "any" rule makes treating English as a pivot irrelevant to membership: listing
it can neither add a dataset nor remove one.

**Yardsticks.** For each capped dataset, the recipe evaluates the cap under every profile the
intervals allow. If every profile gives the same band, that band stands. If not, the cap is
unresolved for that dataset and the record says so. No profile is assumed. The thresholds per profile
are the recipe PR's to set.

## Explicit `unknown`

`unknown` is a recorded state, never a default (R-2026-11-01-a). Three rules hold throughout:

1. **A missing value is never zero and never low-resource.** A language CLD2 does not detect has an
   unknown web share, not 0%. A language absent from OpenAlex's groups has unknown scholarly output,
   not none. A language with no speaker figure is unknown, not "few".
2. **Absence becomes an observation only where the source's list is complete by construction.**
   That covers two cases: the Wikipedia editions in the site matrix (no edition means zero articles,
   bounded above by a macrolanguage edition) and CLDR's national official languages (absence rules
   out national status, but leaves regional or none unknown). Anything else is silence. This mirrors
   `abstain_values` in `sources/signal_routing.yaml`: each source declares which of its answers mean
   it has no answer.
3. **Unknown propagates as width, not as a value.** An unknown measure is the full interval A–D. A
   bounded one is a narrower interval. A class or verdict is published only when it is the same at
   both ends. Otherwise it is published as `unresolved`, with both ends. A consumer must never
   collapse `unresolved` or `unknown` to either end.

## Table schema and data contract

### The tables

**`currentai.language_resources.classification`**: one row per ISO 639-3 code of scope individual or
macrolanguage in the pinned code-table release. It covers every such code, not just the map's codes,
so it does not depend on the corpus. The key is `iso639_3`.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `iso639_3` | varchar | no | the code (key) |
| `macrolanguage` | varchar | yes | parent macrolanguage, NULL when none |
| `cldr_alias_of` | varchar | yes | the macrolanguage CLDR treats as equivalent, NULL when none |
| `web_share_best`, `web_share_worst` | varchar | no | band interval, `A`–`D` |
| `web_share_state` | varchar | no | `measured`, `via_cldr_alias`, `bounded`, `unknown` |
| `wikipedia_best`, `wikipedia_worst`, `wikipedia_state` | varchar | no | as above, plus state `observed_absent` |
| `scholarly_best`, `scholarly_worst`, `scholarly_state` | varchar | no | as above |
| `speakers_best`, `speakers_worst`, `speakers_state` | varchar | no | band interval, `A`–`E` |
| `speakers_low`, `speakers_high` | bigint | yes | the raw estimates behind the speaker interval |
| `status_best`, `status_worst`, `status_state` | varchar | no | `national` > `regional` > `none` |
| `resource_class` | varchar | no | `high`, `mid`, `low`, `very_low`, `unresolved`, `unknown` |
| `resource_class_best`, `resource_class_worst` | varchar | no | the two ends, equal when resolved |
| `official`, `many_speakers`, `large_literature` | varchar | no | `yes`, `no`, `unresolved` |
| `descriptive_status`, `endangerment` | varchar | no | Glottolog MED and AES values, or `unknown` |
| `provenance` | array(row(measure varchar, source varchar, source_version varchar, retrieved_at timestamp(6), content_sha256 varchar)) | no | one element per measure read |
| `code_table_version` | varchar | no | the ISO 639-3 release, such as `20261015` |
| `method_version` | varchar | no | the version of this specification's rules |
| `computed_at` | timestamp(6) | no | when the row was computed |

**The value of `unknown`.** A missing measure is `<measure>_state = 'unknown'` with the interval at
its full range (`best = 'A'`, `worst = 'D'`). A missing class is the string `unknown` or `unresolved`.
NULL never stands for a missing measurement. It appears only in the nullable columns above, where it
means "not applicable" (no macrolanguage) or "no raw estimate". A NULL in a non-null column is a
contract violation, which the repository's reader (below) fails on.

**`currentai.language_resources.measurements`**: the raw observations behind the classification. It
holds one row per (`iso639_3`, `measure`, `source`, `source_version`), with `value_numeric double`,
`value_text varchar`, `mapping varchar` (`direct`, `cldr_alias`, `macrolanguage_aggregate`,
`macrolanguage_bound`, `absent_complete_list`), `source_url varchar`, `retrieved_at timestamp(6)` and
`content_sha256 varchar`. This is the table a reviewer reads to see why a language sits where it does.
Its name avoids `observations`, which is a governed dataset here (naming rule 4 in
[`data-architecture.md`](../architecture/data-architecture.md), section 11.1a).

### Ownership, cadence and the contract

**Ownership.** Both tables are built and owned on Artio (`owner: oso`). The maintainer named in
ADR-003 maintains them, and changes are requested by issue in this repository. The repository keeps
read-only mirror files with the `PLATFORM MIRROR (read-only)` banner under
`warehouse/models/language_resources/`. Neither table ever enters `warehouse/assets.yaml`. The
`add-data-source` skill still describes registering a platform model in `assets.yaml` with
`authority: platform`. ADR-003 refuses that, so this input takes the contract route.

**Cadence.** Quarterly, with each source pinned to a version: the crawl ID, the CLDR release, the
Glottolog release, the ISO 639-3 table date, and a retrieval time plus content hash for the live
APIs. Resource levels move slowly, and a class change moves products. A refresh therefore never moves
a product. It produces a diff of changed classes and implied roster changes, which goes through review
as a proposal (ADR-004: machines propose, humans accept).

**Two contracts, because of the dependency gates.** The repository must not add the contract before
it has a reader. Gate 4 in [ADR-003](../architecture/adr-003-repository-scope-boundary.md) requires a
`required_by` that `build/assets.py` re-derives from a governed root, and the root set is closed
(`AUDIT_ROOTS`). The reader, `build/language_classes.py` (an illustrative name), therefore lands in
the same PR as the contract and is added to `AUDIT_ROOTS`. It renders the review table, and it fails
when a code in `languages` has no row. Gate 2 then follows the classification mirror's reads, so
`language_resources.measurements` needs its own contract, read by the classification mirror. That is
the same dependency-to-dependency shape as `evidence.product_evidence` → `scores.openness_facts`.

The proposed entries follow, in `warehouse/dependencies.yaml`'s shape. Values in angle brackets are
filled at sync time, from `GetDataModel` and the mirror file's bytes.

```yaml
- table: currentai.language_resources.classification
  purpose: language_resource_classification
  expected_grain: one row per ISO 639-3 code of scope I or M in the pinned code-table release
  freshness_requirement: <= 100 days (quarterly platform refresh)
  required_by:
  - build/language_classes.py
  verified_revision: <revision released on Artio>
  owner: oso
  files:
    model: warehouse/models/language_resources/classification.sql
    schema: warehouse/models/language_resources/classification.schema.json
  mirror:
    model_id: <platform model_id>
    revision: <revision released on Artio>
    hash: <platform hash from GetDataModel>
    local_sha256: <sha256 of the mirror model file>
    synced_at: '<date of sync>'
    schema_sha256: <sha256 of the mirror schema file>
  platform_schedule:
    cron: 41 4 2 1,4,7,10 *
    timezone: UTC
    last_observed_trigger: null
- table: currentai.language_resources.measurements
  purpose: language_resource_measurements
  expected_grain: one row per (iso639_3, measure, source, source_version)
  freshness_requirement: <= 100 days (quarterly platform refresh)
  required_by:
  - warehouse/models/language_resources/classification.sql
  verified_revision: <revision released on Artio>
  owner: oso
  files:
    model: warehouse/models/language_resources/measurements.py
  mirror:
    model_id: <platform model_id>
    revision: <revision released on Artio>
    hash: <platform hash from GetDataModel>
    local_sha256: <sha256 of the mirror model file>
    synced_at: '<date of sync>'
  platform_schedule:
    cron: 41 3 2 1,4,7,10 *
    timezone: UTC
    last_observed_trigger: null
```

## Validation against the languages the map lists

**What is declared.** A read-only pass over `sources/products/` on this date found 162 products that
declare `languages`: 97 in `language_specific_datasets`, 35 in `training_synthetic_datasets`, 27 in
`benchmark_eval_data` and 3 in `robotics_embodied`. Between them they list 2,971 distinct codes: 2,918
individual languages and 53 macrolanguages. Of those, 2,927 are living, 20 historical, 13 constructed
and 11 extinct, and 252 are members of a macrolanguage. Seven products carry most of the breadth.
`fineweb-2` alone lists 1,807 codes, `mms-lab-data` 1,107 and `seacrowd` 996. The 193 codes listed by
`language_specific_datasets` products of 50 languages or fewer stand in for the languages those
datasets were built for. They are reported separately as the *targeted* set.

**Coverage.** Counted as direct matches, the resource sources reach few codes: Common Crawl 158 of
2,971 (105 of the 193 targeted), Wikipedia 346 (147) and OpenAlex 160 (88). The context sources reach
more: CLDR 623 (162), Wikidata speaker counts 1,021 (178) and Glottolog 2,926 (173). Joshi et al.,
matched by name, reach 877 (133). Appendix B adds the codes reached through a macrolanguage.

**What no source covers.** No resource source (web share, Wikipedia or OpenAlex) reaches 2,482 of the
2,971 codes, directly or through a macrolanguage. Among the targeted set that is 35 codes, listed in
Appendix D. Three codes have no value in any source: `ldn` (Láadan, constructed), `nwx` (Middle
Newar, historical) and `ota` (Ottoman Turkish, historical).

**Dry run.** Under the rules above, the 2,971 codes come out 17 high, 34 mid, 32 low, 160 very low and
2,728 `unresolved`. The 193 targeted codes come out 16 high, 20 mid, 23 low, 48 very low and 86
`unresolved`. No code is wholly `unknown`, because every code has at least a Wikipedia observation.
The long tail stays unresolved because at most one of its three measures is observed. Under R-2026-10-30-d,
such a language is decided on the purpose test alone. Where the classes overlap Joshi et al. (2020),
they agree in direction: no Joshi class 0 to 2 language comes out high, and no class 4 or 5 language
comes out very low (Appendix C).

**The hand-made list under each line.** "Below high" counts mid, low and very low as underrepresented.
"Low or very low" counts only those two. D3 chooses between them.

| Language | Current call | Resource class | Below high | Low or very low |
|---|---|---|---|---|
| Chinese, Japanese, Spanish, Portuguese | out | high | out | out |
| **Korean** | out | mid | **in** | out |
| **Arabic** | in | mid | in | **out** |
| **Indonesian** | in | high | **out** | **out** |
| **Vietnamese** | in | mid | in | **out** |
| Turkish, Ukrainian, Swedish | in | high | **out** | **out** |
| Persian, Thai, Hebrew, Hindi, Bengali | in | mid | in | **out** |
| Danish, Catalan, Estonian, Norwegian (`nor`) | in | mid | in | **out** |
| Basque, Galician, Icelandic, Kazakh, Khmer, Urdu, Burmese | in | low | in | in |
| Maltese, Faroese, Lao, Swahili, Yoruba, Amharic, Māori | in | very low | in | in |
| Moroccan and Egyptian Arabic, Bokmål, Nynorsk | in | unresolved | in | purpose test only |
| Northern Sámi | in | unresolved | purpose test only | purpose test only |

**The calls that would change, not decided here.**

- **Korean** (`kor`): web 0.88% (B), Wikipedia 770k (B), OpenAlex 3.28M (A). It is mid, so under
  "below high" it comes in. KMMLU, a tail row in `benchmark_eval_data` routed out by the seed sweep,
  would qualify for `language_specific_eval_sets`.
- **Indonesian** (`ind`): web 1.06% (A), Wikipedia 803k (B), OpenAlex 3.60M (A). It is high under
  either line, so `indonlu` would leave. The call rests on OpenAlex. Without it the median of A, B and
  unknown is unresolved. OpenAlex counts more Indonesian works than Korean (3.28M) or Italian
  (2.59M). That may reflect DOI registration by Indonesian journals more than the volume of
  literature (Appendix A).
- **Vietnamese** (`vie`): web 0.98% (B), Wikipedia 1.31M (A), OpenAlex 140k (B). It is mid, so it
  stays in under "below high" and leaves under "low or very low" (`vmlu`,
  `vietnamese-curated-dataset`).
- **Arabic** (`ara`): web 0.67% (B), Wikipedia 1.34M (A), OpenAlex 935k (B). It is mid, so it stays in
  under "below high" and leaves under "low or very low" (`101-billion-arabic-words`, `arabicmmlu`,
  `arabicweb24`, `cidar`). The dialect sets (`atlaset`, `darijammlu`) fall to the purpose test under
  the lower line.
- **Turkish and Ukrainian**: high, so `turkishmmlu` and `ubertext` would leave under either line.
  Ukrainian is named "in" in the category's comments.
- **Edge sensitivity.** Korean, Vietnamese, Indonesian and Turkish all sit between 0.88% and 1.14% of
  pages, on both sides of the 1% edge. Web share alone cannot separate them. Wikipedia and OpenAlex
  are what does.

**Products.** Under "below high", 92 of the 97 products stay in. Three leave (`indonlu`,
`turkishmmlu`, `ubertext`), and two fall to the purpose test (`saami-web`, `smugri-data`). Under "low
or very low", 70 stay, 23 leave and 4 fall to the purpose test. The roster review table that
R-2026-10-30-d asks for comes from the Artio table, not from this dry run.

## Decisions for the maintainer

Each can be answered in a sentence. The recommendation comes first.

- **D1. Structure.** Keep four dimensions separate and derive two views (a resource class for
  membership, a three-axis profile for the yardsticks), with no weighted index? *Recommend yes.*
- **D2. Resource class inputs.** Is the class the robust median of web share, Wikipedia articles and
  scholarly works, with equal votes and with speakers and status left out? *Recommend yes.*
- **D3. The membership line.** Is a language underrepresented when it is below high (mid, low or very
  low), or only when it is low or very low? *Recommend below high.* It moves three products out and
  leaves two to the purpose test. The lower line would also take out Arabic, Hindi, Bengali, Thai and
  Vietnamese, among others, and 23 products in all.
- **D4. Band edges.** Set them at powers of ten (1%, 0.1% and 0.01% of pages; 1M, 100k and 10k
  articles or works)? *Recommend yes for the first version, with raw values published beside every
  band,* so the edge cases (Korean to Turkish) stay visible.
- **D5. Robustness.** Does a class or verdict stand only when it holds across every value the unknowns
  allow, with no single-signal fallback? *Recommend yes.* It is R-2026-11-01-a's test. The cost is
  that most of the long tail stays unresolved and is decided on the purpose test.
- **D6. Absence.** Does absence count as an observation only in a list that is complete by
  construction (Wikipedia editions, CLDR national official languages), and is silence from a detector
  or index `unknown`? *Recommend yes.*
- **D7. Macrolanguages.** Treat CLDR's macrolanguage aliases as equivalence, and bound every other
  member by its macrolanguage? *Recommend yes.* Curators should also prefer an individual code in
  `languages` when a dataset was built for one member. `msa` reads as Indonesian-scale, because `ind`
  is a member of `msa`.
- **D8. Excluded inputs.** Leave out the map's own counts of open datasets per language, Joshi et al.
  (2020) and Ethnologue? *Recommend yes.* The map's counts are circular, since adding a dataset would
  move its language's class and with it other datasets' membership; show them as a context column.
  Keep Joshi as a validation reference only: it is a 2020 snapshot keyed by name, and 1,001 of its
  2,485 names match no ISO reference name. Ethnologue's terms could not be read, and a secondary
  source reports it paywalled.
- **D9. Yardstick axes.** Is `official` national or regional status, `many_speakers` 10 million or
  more, and `large_literature` 100,000 or more scholarly works? *Recommend these as the starting cuts,*
  to be confirmed when the recipe PR dry-runs the caps against them.
- **D10. Contracts and cadence.** Two contracts (classification and measurements), a quarterly refresh
  pinned to source versions, and every class change surfaced as a review proposal that never moves a
  product on its own? *Recommend yes.*

## Sequence

1. **Ruling** on D1 to D10, recorded in `docs/rulings/log.yaml`.
2. **Artio** (maintainer, on the platform): build `language_resources.measurements` and
   `language_resources.classification` to this specification.
3. **Repository PR**: the reader module (added to `AUDIT_ROOTS`), the two mirror files and the two
   contracts, and the published review table with the roster changes it implies. Nothing moves.
4. **Ruling** adopting the table.
5. **Membership** and **yardsticks**, in the order of the
   [2026-10-30 brief's sequence](2026-10-30-language-specific-datasets-structure.md#sequence). Each
   product move is rescored in the PR that moves it.

---

## Appendix A: source assessments

Coverage figures are against the 2,971 declared codes and the 193 targeted codes (direct, plus codes
reached through a macrolanguage). A property not checked on this date is marked as not checked.

**ISO 639-3 code tables (SIL).** These define the universe. The repository's
`sources/snapshots/iso-639-3.tab` holds 7,927 rows (7,860 individual, 63 macrolanguage, 4 special),
and it covers every declared code by construction, since validation refuses any other. The current
release on SIL's site is `iso-639-3_Code_Tables_20261015`. Whether the repository's snapshot is that
release was not checked. The terms of use allow incorporating the codes with attribution, provided
the product "does not provide a means to redistribute the code set". Expansions such as population
data may be distributed if they are marked as not part of the standard. A table keyed on every code
should therefore carry derived attributes only, not the reference names. Whether a complete keyed
table counts as redistribution is a question for SIL, and it applies equally to the repository's
snapshot. The macrolanguage mapping (`iso-639-3-macrolanguages.tab`) supplies the macrolanguage rules.

**Common Crawl language statistics.** `languages.csv` gives pages per primary language per crawl. It
covers 129 crawls, the latest being `CC-MAIN-2026-43`, with 162 labels in that crawl. The detector is
CLD2, which "is able to identify 160 different languages", and only HTML pages are passed to it.
Codes are ISO 639-3, some at macrolanguage level (`ara`, `zho`, `fas`, `msa`, `nor`). Coverage is 158
(+130) of all codes and 105 (+14) of the targeted ones. The statistics repository carries the Apache
License 2.0. No separate data license for the CSV was found. Recent crawls are four to five weeks
apart. Reproducibility is good: crawls are immutable and named. Biases: detection is limited to
CLD2's set, the `<unknown>` bucket holds 3.06% of pages, and language share follows what the crawler
reaches.

**Wikipedia.** The Wikimedia site matrix lists 364 Wikipedia editions, 16 of them closed. The dry run
read content-article counts from the third-party Wikistats dump. Its page says it is updated daily
and that it "is not the Wikimedia Analytics Wikistats". Artio should read per-edition statistics from
Wikimedia's own API instead. Coverage is 346 (+129) and 147 (+9). Edition codes are not ISO codes.
Most are ISO 639-1. For this dry run, nine composite prefixes (`zh-yue`, `zh-min-nan`, `roa-rup`, and
others) and `no` (Bokmål) were mapped by hand, and six were left unmapped (`simple`, `eml`, `map-bms`,
`roa-tara`, `bh`, `nah`). The dump's license was not checked. Biases: bot-generated articles inflate
some editions. Cebuano has 6.1M content articles and Egyptian Arabic 1.6M, more than the Arabic
edition's 1.3M.

**OpenAlex.** OpenAlex states that its data is CC0. The `language` field is "the language of the
work's metadata (title/abstract), in ISO 639-1 format, auto-detected with langdetect". Grouping by
language returned 200 groups, the smallest holding 115 works. A request for a second page failed
(HTTP 400), so whether the tail can be paged was not established.
The groups include noise keys (`EN`, `中文`, `gr`, `ua`, `xx`). Coverage is 160 (+106) and 88 (+9).
The API now meters unauthenticated use against a free daily budget shared per IP address, which ran
out during this session, so Artio should use a key or OpenAlex's snapshot. Biases: it measures
metadata language, not full text. It favors languages langdetect knows. Counts may follow DOI
registration as much as publishing volume, which would explain Indonesian (3.60M) and Korean (3.28M)
ranking far above Arabic (935k) and Vietnamese (140k).

**Crossref.** Not usable for this purpose through its REST API. Requesting a `language` facet
returns HTTP 400 ("no such facet for this route"), and `language` is not a selectable field. Counting
by language would mean processing the full metadata dump, which was not assessed. The license was not
checked.

**Unicode CLDR territory data.** Version 49 (`cldr-core` 49.0.0), under the Unicode License v3, which
permits use and redistribution with the notice. It holds 258 territories, each with a population and
a list of languages with population percentages and, where official, `official` (339 entries),
`de_facto_official` (21) or `official_regional` (136). Coverage is 623 (+150) and 162 (+14). Release
cadence was not checked. Reproducibility is good: releases are versioned. Biases: percentages mix
first- and second-language use, codes are BCP 47 with script variants, and minority languages are
listed unevenly. Its `languageAlias` table supplies the 63 macrolanguage equivalences behind rule 2.

**Wikidata.** Structured data is CC0. The SPARQL query used here returned 8,250 ISO 639-3 values.
Number of speakers (P1098) reaches 1,021 (+124) of all codes and 178 (+3) of the targeted ones. Being
the official language (P37) of a sovereign state reaches 147 (+115). Wikidata is live, so
reproducibility requires recording the query, retrieval time and content hash, or reading a dated
dump. Biases: speaker figures mix first- and second-language counts and years, and two values were
"unknown value" placeholders rather than numbers.

**Glottolog (CLDF).** Release 5.3 of 2026-03-02, under CC BY 4.0. It carries ISO 639-3 mappings,
agglomerated endangerment status (AES: not endangered to extinct), most extensive description (MED:
long grammar to wordlist or less) and linked bibliography. Coverage is 2,926 (+2) and 173 (+2). It has
been released roughly yearly (5.2 in May 2025, 5.3 in March 2026). Reproducibility is good. Biases:
MED and the bibliography measure literature *about* a language, not *in* it, so they are context here
and not a literature input.

**Joshi et al. (2020) resource classes.** `lang2tax.txt` holds 2,485 rows of language *name* and class
0 to 5 (2,191 of them class 0). Exact matching against ISO reference names resolves 1,482 rows, and
1,001 match nothing. It reaches 877 (+153) and 133 (+10) codes. The paper is CC BY 4.0 (ACL Anthology).
No license for the data file was found: the project page states none, and its GitHub repository did
not answer (HTTP 403). It is frozen in 2020 and keyed by name, so it serves as validation only.

**Ethnologue.** Its pages returned HTTP 403 to every fetch, so its terms could not be read here.
Wikipedia's article on it reports a hard paywall since 2019, with subscriptions from $480 a year. That
is secondary and was not verified against Ethnologue. Its coverage was not assessed. It is excluded.

**Not assessed.** Hugging Face dataset language tags and national bibliographies (for literature in a
language rather than about it). Either would be a candidate for a later method version.

## Appendix B: coverage of the declared codes

Direct matches, then in brackets the codes reached only through their macrolanguage. For a member
that CLDR does not alias, a macrolanguage value is an upper bound, not a measurement.

| Source | All 2,971 codes | 193 targeted codes |
|---|---|---|
| Common Crawl (CLD2) | 158 (+130) | 105 (+14) |
| Wikipedia | 346 (+129) | 147 (+9) |
| OpenAlex | 160 (+106) | 88 (+9) |
| CLDR territory data | 623 (+150) | 162 (+14) |
| Wikidata speakers (P1098) | 1,021 (+124) | 178 (+3) |
| Wikidata official (P37) | 147 (+115) | 88 (+10) |
| Glottolog (any) | 2,926 (+2) | 173 (+2) |
| Glottolog AES | 2,903 (+4) | 165 (+4) |
| Glottolog MED | 2,918 (+3) | 172 (+2) |
| Joshi 2020 (name match) | 877 (+153) | 133 (+10) |

Verdicts across all codes and the targeted set:

| Line | Set | Underrepresented | Not underrepresented | Unresolved |
|---|---|---|---|---|
| Below high | all 2,971 | 299 | 17 | 2,655 |
| Below high | targeted 193 | 109 | 16 | 68 |
| Low or very low | all 2,971 | 220 | 51 | 2,700 |
| Low or very low | targeted 193 | 80 | 36 | 77 |

The 16 targeted codes not underrepresented under "below high" are `deu`, `eng`, `fra`, `ind`, `ita`,
`jpn`, `msa`, `nld`, `pol`, `por`, `rus`, `spa`, `swe`, `tur`, `ukr` and `zho`.

## Appendix C: dry run for named languages

Bands are A (most) to D (least). "Alias" marks a value taken through CLDR's macrolanguage alias.
"Bounded" marks an interval set by a macrolanguage. "No edition" marks the observed absence of a
Wikipedia edition. Speakers show the CLDR and Wikidata figures as a range.

| Code | Web share (CC) | Wikipedia articles | Scholarly works (OpenAlex) | Resource class | Below high | Low or very low | Status | Speakers |
|---|---|---|---|---|---|---|---|---|
| `eng` | 42.56% A | 7.26M A | 234.33M A | high | no | no | national | 753.4M–1733.0M |
| `spa` | 4.74% A | 2.15M A | 12.19M A | high | no | no | national | 485.0M–512.4M |
| `por` | 2.47% A | 1.19M A | 6.23M A | high | no | no | national | 249.5M–254.3M |
| `jpn` | 4.89% A | 1.53M A | 13.07M A | high | no | no | national | 117.6M–128.0M |
| `zho` | 4.37% A | 1.56M A | 5.55M A | high | no | no | national | 1299.9M–1324.2M |
| `kor` | 0.88% B | 770k B | 3.28M A | mid | yes | no | national | 77.3M–79.3M |
| `ara` | 0.67% B | 1.34M A | 935k B | mid | yes | no | national | 315.4M–378.8M |
| `ind` | 1.06% A (bounded) | 803k A–B (bounded) | 3.60M A (bounded) | high | no | no | national | 180.6M–199.0M |
| `vie` | 0.98% B | 1.31M A | 140k B | mid | yes | no | national | 76.0M–92.4M |
| `tur` | 1.14% A | 710k B | 1.35M A | high | no | no | national | 82.2M–82.4M |
| `ukr` | 0.79% B | 1.44M A | 1.20M A | high | no | no | national | 24.7M–26.9M |
| `fas` | 0.62% B | 1.10M A | 547k B | mid | yes | no | national | 45.0M–89.2M |
| `tha` | 0.35% B | 189k B | 353k B | mid | yes | no | national | 20.7M–56.0M |
| `heb` | 0.26% B | 408k B | 51k C | mid | yes | no | national | 9.3M–9.4M |
| `hin` | 0.21% B | 172k B | 33k C | mid | yes | no | national | 341.0M–580.3M |
| `ben` | 0.11% B | 192k B | 7k D | mid | yes | no | national | 280.0M–300.0M |
| `dan` | 0.52% B | 317k B | 399k B | mid | yes | no | national | 6.0M–7.2M |
| `cat` | 0.21% B | 807k B | 562k B | mid | yes | no | national | 4.9M–8.2M |
| `est` | 0.15% B | 263k B | 59k C | mid | yes | no | national | 854k–1.3M |
| `nor` | 0.34% B | 875k B (`nob` + `nno`) | 309k B | mid | yes | no | national | 5.2M–5.5M |
| `swe` | 0.71% B | 2.63M A | 1.03M A | high | no | no | national | 9.2M–13.3M |
| `kaz` | 0.04% C | 246k B | 21k C | low | yes | yes | national | 12.9M–14.7M |
| `urd` | 0.03% C | 707k B | 8k D | low | yes | yes | national | 68.6M–313.1M |
| `eus` | 0.04% C | 500k B | 66k C | low | yes | yes | regional | 750k–1.0M |
| `glg` | 0.03% C | 247k B | 43k C | low | yes | yes | regional | 2.4M–3.3M |
| `isl` | 0.04% C | 61k C | 18k C | low | yes | yes | national | 321k–364k |
| `khm` | 0.0107% C | 13k C | 533 D | low | yes | yes | national | 15.2M–16.6M |
| `mya` | 0.02% C | 113k B | 697 D | low | yes | yes | national | 32.9M–37.2M |
| `swa` | 0.0099% D | 132k B | 6k D | very low | yes | yes | national | 15.4M–194.1M |
| `yor` | 0.0017% D | 41k C | 187 D | very low | yes | yes | national | 31.8M–37.8M |
| `amh` | 0.0042% D | 16k C | 762 D | very low | yes | yes | national | 21.9M–39.2M |
| `lao` | 0.0056% D | 6k D | 1k D | very low | yes | yes | national | 5.2M–5.5M |
| `mlt` | 0.0034% D | 8k D | 2k D | very low | yes | yes | national | 470k–570k |
| `fao` | 0.0057% D | 14k C | 228 D | very low | yes | yes | national | 69k–73k |
| `mri` | 0.0019% D | 8k D | 205 D | very low | yes | yes | national | 145k–214k |
| `ary` | B–D (bounded) | 21k A–C (bounded) | B–D (bounded) | unresolved (mid to very low) | yes | unresolved | none found | 27.5M–32.5M |
| `arz` | B–D (bounded) | 1.63M A (bounded) | 4k B–D (bounded) | unresolved (mid to very low) | yes | unresolved | none found | 64.6M–71.2M |
| `nob` | B–D (bounded) | 694k B | 733 B–D (bounded) | unresolved (mid to very low) | yes | unresolved | national | 4.0M–5.5M |
| `nno` | 0.0138% B–C (bounded) | 181k B | 13k B–C (bounded) | unresolved (mid to low) | yes | unresolved | national | 1.4M–4.3M |
| `sme` | A–D (unknown) | 8k D | A–D (unknown) | unresolved (high to very low) | unresolved | unresolved | regional | 26k–53k |

Agreement with Joshi et al. (2020), for the 135 declared codes that have both a Joshi class and a
resolved resource class:

| Joshi class | high | mid | low | very low |
|---|---|---|---|---|
| 5 | 5 | 1 | 0 | 0 |
| 4 | 7 | 10 | 1 | 0 |
| 3 | 2 | 14 | 8 | 0 |
| 2 | 0 | 0 | 3 | 10 |
| 1 | 0 | 1 | 14 | 50 |
| 0 | 0 | 0 | 0 | 9 |

## Appendix D: targeted codes no resource source reaches

These 35 of the 193 targeted codes have no web share, Wikipedia edition or OpenAlex group, directly
or through a macrolanguage. Each has at least a Glottolog or CLDR entry, so its status, speakers and
descriptive context can still be published.

`ach`, `bau`, `bgc`, `bho`, `brx`, `bxk`, `bzd`, `cni`, `ctp`, `doi`, `gbm`, `hch`, `hne`, `hoj`,
`kca`, `kln`, `kok`, `kpo`, `lri`, `luo`, `mas`, `mns`, `mup`, `mwr`, `ndc`, `nde`, `nus`, `nyn`,
`rag`, `shp`, `sid`, `sog`, `taq`, `tar`, `wal`

## Appendix E: how the numbers were produced

The declared codes were read from `sources/products/*.yaml` and the rosters from
`sources/categories/*.yaml`, read-only. The pivot declarations were read from
`capability.pivot_languages` in `sources/scores/`, though the "any" rule makes them immaterial to
membership. Every source below was fetched on 2026-11-02 with
`uv run python -m build.fetch_source`, and the digest is the `content_sha256` it reported. The dry run
followed the rules in [Methodology](#methodology) exactly. It is not the Artio implementation, and
its counts will differ from the Artio table wherever Artio reads a primary API in place of the
convenience source used here (Wikistats).

| Source | URL | Status | content_sha256 |
|---|---|---|---|
| Common Crawl language statistics (CSV) | https://commoncrawl.github.io/cc-crawl-statistics/plots/languages.csv | 200 | `261dfd2da5e9bfa8975f57711e23ab639b2f1b6c174273e9182a55e05ed46bf1` |
| Common Crawl language statistics (page) | https://commoncrawl.github.io/cc-crawl-statistics/plots/languages | 200 | `860f75c88d2a2a7adada677a2f98e0df7cc68779a282962da48c980dff6ce9e4` |
| cc-crawl-statistics license | https://raw.githubusercontent.com/commoncrawl/cc-crawl-statistics/master/LICENSE | 200 | `b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1` |
| Wikistats Wikipedia dump | https://wikistats.wmcloud.org/api.php?action=dump&table=wikipedias&format=csv | 200 | `4a72e35e175b0597640f7d8f7f98088a6bc23354a51309e603a8183d1a087af2` |
| Wikistats page | https://wikistats.wmcloud.org/ | 200 | `ea6eece899861abcc2c561879ac83e18b5ef34ede9ba6affe369f8c538e773b1` |
| Wikimedia site matrix | https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json&smtype=language&smlangprop=code%7Csite%7Clocalname | 200 | `f60f8c0f6c81caafc44588b06710ef6e13eb78d660e3703ae7aa8515d73028cc` |
| OpenAlex works by language | https://api.openalex.org/works?group_by=language&per_page=200 | 200 | `bdfade2b989357d38568f4c053a37e90337de75ba0d14215080aa3280787b33c` |
| OpenAlex work object documentation | https://docs.openalex.org/api-entities/works/work-object | 200 | `4671f96d60872768fb0caa4f50e981fd559a3213e94a40bee496027cf66876d9` |
| OpenAlex about page | https://openalex.org/about | 200 | `e03f9b6fec9e0953d4c1e6f30729fd28c699708b890342fe7e99ce5e4df8ea70` |
| Crossref language facet | https://api.crossref.org/works?rows=0&facet=language:* | 400 | `7b6a9e05a12d8d946c9d2661cd4f47e20ba4b016ede68e739096876653942ce7` |
| CLDR territory info | https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json/cldr-core/supplemental/territoryInfo.json | 200 | `c8aa7654c87de234118f14ada0e1466eb09467bed4048da7eab3e7e63ffe335d` |
| CLDR aliases | https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json/cldr-core/supplemental/aliases.json | 200 | `ee30563c98bb6217adebbdc97b0ca7a0ff834973011a6890cddfd83c6250e729` |
| CLDR package metadata | https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json/cldr-core/package.json | 200 | `605c2ac37c47439b2b89e5662133bd7ef52a09d2af9215572b2774c6343afbb3` |
| Unicode License v3 | https://www.unicode.org/license.txt | 200 | `e7a93b009565cfce55919a381437ac4db883e9da2126fa28b91d12732bc53d96` |
| Wikidata speakers and official status (SPARQL) | query.wikidata.org, P220 with P1098 and P37 on Q3624078 | 200 | `bdb2ba263be5375c9ec8c862eaedb9d2971ec7a3252515443b3f355f7e1cdf37` |
| Wikidata licensing | https://www.wikidata.org/wiki/Wikidata:Licensing | 200 | `f35861af5d41ab2b220a05f58cea4bef90a066638f4997eb8a46d81797f06295` |
| Glottolog CLDF languages | https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/languages.csv | 200 | `1a50a393bc81568b656f9522be18aa4f80f38e94309ba6c863d583234adfbb89` |
| Glottolog CLDF values | https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/values.csv | 200 | `a8601cb04ccc6a310538217f772d2461853aa0ea49e3bfe24c7396570fc4ea25` |
| Glottolog CLDF codes | https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/codes.csv | 200 | `cc1d2d2a4a27e3f9d396f255acfa755ee4a63125b8467f9f8f904ee0dc8717b4` |
| Glottolog CLDF license | https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/LICENSE | 200 | `945fbcb37deca05bccd7c3ca0e261679f1f5373515504fdbad68f6f3cf6f49b9` |
| Glottolog CLDF changelog | https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/CHANGELOG.md | 200 | `ecc99542e4f9d6af7b1e7ce2f2228d684bef36d6bb5bff1a2c7823f2351c21ac` |
| ISO 639-3 download page and terms | https://iso639-3.sil.org/code_tables/download_tables | 200 | `94f47ad0d569c60ee6e2ff7177ff24340bbb8178a779e08365cd611c89007456` |
| ISO 639-3 macrolanguage mappings | https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3-macrolanguages.tab | 200 | `fb01a86376d9c1abfc96d16be1b6dcffb4776a1f52fa22338d4979e9ffe1822f` |
| Joshi et al. class list | https://microsoft.github.io/linguisticdiversity/assets/lang2tax.txt | 200 | `2e182e8f4bd9adb0bc04af2f74852d770581ac0b5a3609224ced7b08266d6dd2` |
| Joshi et al. project page | https://microsoft.github.io/linguisticdiversity/ | 200 | `bffff2204f5b67449abf4ef6ec1ccdea61bc318e81629c0fc9c60552b963ebfb` |
| Joshi et al. paper (ACL Anthology) | https://aclanthology.org/2020.acl-main.560/ | 200 | `19566251b29e02206eafedf86aad19abd26a273f5568660f8be67f444d530d1f` |
| Joshi et al. repository | https://github.com/microsoft/linguisticdiversity | 403 | – |
| Ethnologue terms of use | https://www.ethnologue.com/terms-of-use/ | 403 | – |
| Ethnologue (Wikipedia, secondary) | https://en.wikipedia.org/wiki/Ethnologue | 200 | `a2c52128821ffc2b7c7205358b091a5b4aea511c517dbffd21ed36d87ad219d1` |

The SPARQL query, in full:

```sparql
SELECT ?iso (MAX(?sp) AS ?speakers) (COUNT(DISTINCT ?state) AS ?official_in) WHERE {
  ?lang wdt:P220 ?iso .
  OPTIONAL { ?lang wdt:P1098 ?sp . }
  OPTIONAL { ?state wdt:P37 ?lang . ?state wdt:P31 wd:Q3624078 . }
} GROUP BY ?iso
```
