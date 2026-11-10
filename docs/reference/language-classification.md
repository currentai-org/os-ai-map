# Language Classification Guide

How the map classifies a language, and how the classification feeds two decisions about
language-specific datasets: which category a dataset belongs in, and which size yardstick its
corpus is measured against. This is normative on the evidence rules, the two derived views, the
unknown states and the data contract. The method is versioned (see [Versioning](#versioning)); this
document describes **method version 1**.

The classification is built and owned on Artio (the OSO warehouse), and this repository reads it as
a dependency contract (R-2026-10-30-d). Nothing in this repository computes a class. The membership
and yardstick rules that consume it live in the category records they govern:
`sources/categories/language_specific_datasets.yaml` and
`sources/categories/language_specific_eval_sets.yaml`.

## Two views from one evidence base

The classification answers two different questions, so it publishes two views. Neither is a
weighted index, and no column sums or averages the dimensions.

| View | Question | Read from | Consumed by |
|---|---|---|---|
| **Digital representation class** | How much of the language exists as digital text? | Written material only | Category membership (R-2026-10-30-d) |
| **Resource profile** | Which corpus-size comparison is fair for this language? | Official status, speakers, written material, as three separate yes/no axes | The size yardsticks (R-2026-10-30-k) |

**Why they are separate.** Membership asks whether a language is underrepresented in the digital
record. Folding speakers or official status into that answer would make membership relative to
population or politics, which is a different claim. The yardstick asks what corpus size a language
can reasonably support, and there status and speakers matter alongside written material. One index
would answer neither question well. It would also hide which signal moved a language, and it would
let an unknown on one dimension unsettle a verdict that never needed that dimension.

**What the classification is not.** It measures a language's place in the digital record, not
how many AI datasets, benchmarks or models exist for it. A language can be well represented on the
web and still poor in curated, openly licensed AI resources. The map's finding is the comparison
between the two, so the two are measured independently. See [Excluded inputs](#excluded-inputs).

## The dimensions

| Dimension | Measure | Sources | Use |
|---|---|---|---|
| Official status | National, subnational or none | Unicode CLDR territory data; Wikidata P37 on first-level subdivisions | Resource profile |
| Speakers | People who use the language, as an interval across sources | CLDR territory population × language share; Wikidata P1098 | Resource profile |
| Written material | Volume of in-language digital text | FineWeb-2 words with the Bible share removed; Common Crawl CLD2 page share; Wikipedia content articles; Open Library works | Both views |
| Context | Scholarly works by metadata language; descriptive status; endangerment | OpenAlex; Glottolog MED and AES | Published beside the class; AES bounds speakers only as set out below |

### Official status

- **`national`**: CLDR marks the language `official` or `de_facto_official` in a territory.
- **`subnational`**: CLDR marks it `official_regional`, or Wikidata records it as an official
  language (P37) of a first-level subdivision.
- **`recognized`**: a state-level P37 statement without CLDR support. It is recorded in its own
  column and does not count as official. Recognition, such as minority-language protection, does
  not always confer official administrative status. The column reads `yes` for such a statement,
  `no` when CLDR lists the language as official at some level, and `unknown` otherwise. `no`
  therefore means the question is settled by CLDR's listing; it does not mean the language lacks
  legal recognition.
- A macrolanguage's status gives each member the interval from `none` to that status, unless a
  source names the member.

CLDR's list of national official languages is complete by construction, so absence from it rules
out `national`. Neither CLDR's regional entries nor Wikidata's subdivision statements is shown to be
exhaustive, and combining two incomplete registers does not make them complete. So a language that
neither source lists as official at any level records the evidence state `not_listed`, and its
status interval runs from `none` to `subnational`: subnational status is unknown, not absent. The
interval narrows to `none` only on a complete, authoritative source for the jurisdiction concerned,
or on a cited override approved by a ruling ([Overrides](#overrides)). An unresolved status leaves
the `official` axis unresolved, and that carries through the resource profile.

### Speakers

The speaker figure is the **interval** between the CLDR estimate and the Wikidata figure, not the
larger or smaller of the two. The sources count differently: CLDR's figure is users, first and
second language together, and Wikidata's is the statement of preferred rank, which is usually
first-language speakers. They disagree most for languages with large second-language populations.
The interval carries that disagreement instead of choosing a definition, and each source's figure,
definition and provenance stay in the measurements table.

- **A placeholder is not a measurement.** A CLDR figure whose own notes say it is an estimate made
  without a count (for example, a fixed share of a territory's population) is dropped. The
  language's speaker value comes from the other source, or is unknown.
- **Missing is unknown, never few.** A language with no speaker figure has an unknown speaker
  value, whatever its other dimensions say.
- **Endangerment bounds speakers only where it implies a small population.** A Glottolog AES rating
  of `moribund`, `nearly extinct` or `extinct` bounds speakers below one million, tagged
  `bound_from_endangerment`. The bound applies only when the code maps to a Glottolog languoid of
  level `language` outside the `Bookkeeping` and `Artificial Language` families. An entry in those
  families, such as the one for the N'Ko written standard, carries no information about a speaker
  community. Its rating is recorded with state `excluded`, with the languoid's level and family and
  the reason, and does not bound the speaker value. `shifting` and `threatened` describe transmission between
  generations, not population size, and do not touch the speaker value. Large languages can be
  rated shifting.
- Historical and extinct languages have no living first-language community. Their speaker axis
  reads `no`, and the row carries the `historical` flag.

### Written material

Written material is the volume of text written **in** the language. Material **about** the
language, such as grammars and descriptive literature, is context and not an input.

- **Web text, primary witness:** FineWeb-2's per-language word counts, with the share of
  Bible-derived text removed. Bible text dominates the web text of many small languages, and
  counting it would overstate their written material.
- **Web text, second witness:** Common Crawl's published CLD2 page share for the latest crawl. It
  measures the languages FineWeb-2 excludes, English among them.
- **Calibration.** The FineWeb-2 band edges are set so that, over the languages both witnesses
  measure, they correspond to CLD2 page shares of 1%, 0.1% and 0.01%. The fitted edges are
  parameters of the method version ([Parameters](#parameters)). Where both witnesses measure a
  language and fall in different bands, the value is the interval spanning both.
- **Wikipedia** never sets a band on its own, because bot-generated editions can be very large with
  few editors. An edition is **eligible** only when it has at least 100 active users and at most
  1,000 content articles per active user; editions written largely by bots fail the second test.
  The guard applies wherever Wikipedia can move a verdict: an eligible edition widens the
  written-material interval when it disagrees with web text by two or more bands, and only an
  eligible edition counts toward the corroboration path of `large_written_material`. An ineligible
  edition's counts are recorded with state `excluded`. Counts are read from Wikimedia's own
  statistics, per edition.
- **Open Library** works are published as context, and count only through the corroboration path
  of the `large_written_material` axis below. They are read from a reproducible extract of Open
  Library's monthly data dumps, never from its search API, which Open Library intends for
  human-facing discovery rather than as a data backend. Until that extract exists, the measure is
  `unmeasured` for every language and the corroboration path cannot pass on it.

Written material is banded **A** (high) to **D** (very low).

## Value states and unknowns

Every measured value is an interval of bands. Each value records its state:

| State | Meaning | Interval |
|---|---|---|
| `measured` | A source measures this language's population exactly, or as the sum of separately labeled members | A point |
| `bounded` | A source's label covers a broader or narrower population than the code | The bound the mapping gives |
| `observed_absent` | The source's list is complete by construction and the language is not on it | An observed zero |
| `not_listed` | Official status only: neither CLDR nor Wikidata lists the language as official at any level | `none` to `subnational`: national is ruled out, subnational is unknown |
| `excluded` | The observation is recorded but enters no verdict, for a reason the method states (an endangerment rating outside the bound's scope, a Wikipedia edition that fails the bot guard) | None; the reason is kept in `mapping_basis` |
| `not_detected` | A detector able to label the language reported nothing for it | Unknown: the full range |
| `unmeasured` | The language is outside the source's scope | Unknown: the full range |

**Absence is an observation only in a list complete by construction.** Two lists qualify: the
Wikipedia editions in the Wikimedia site matrix, and CLDR's national official languages. Everything
else that is silent is unknown.

**A detector's silence is recorded, not read.** A language identifier can miss a language it
supports: it may file the text under a related language, or fall below its confidence threshold.
`not_detected` keeps the distinction between "no material was found" and "no usable measurement
exists" visible in the table, but it never counts as small.

**A verdict stands only across its whole interval.** Each class and each profile axis is computed
at both ends of every interval. When the two ends agree, the verdict stands. When they differ, it is
published as `unresolved` with both ends. This is the robustness test of R-2026-11-01-a, applied to
languages. A consumer never collapses `unresolved` or `unknown` to either end.

## Code levels and macrolanguages

Sources report at different levels: some label macrolanguages, others individual languages, and
converting between ISO 639-1 and 639-3 says which code a label names, not which population a source
measured. So each source's labels are mapped, per source version, to the population each label is
declared to measure. No alias table supplies an equivalence.

| Relation | When | Contribution to the target code |
|---|---|---|
| `exact` | The label measures the target's population | A point value |
| `aggregate` | The target is a macrolanguage, and the source labels it and its members separately, each item once | The sum, as a point value |
| `edition_complement` | Wikipedia only: a macrolanguage edition whose other members all have their own editions, leaving the target as the sole remainder | A point value |
| `broader` | The label covers the target and other languages | A bound from the target's own exact value (or the floor) up to the broader label's value |
| `members_only_lower_bound` | The target is a macrolanguage and the source labels only some of its members | A lower bound; the upper end is unknown |
| `observed_absent` | Wikipedia only: no edition for the target or its macrolanguage | An observed zero |

Defaults follow from each source's construction. Any of them can be overridden with a cited basis
([Overrides](#overrides)).

- **Detectors** (FineWeb-2's identifier, CLD2, OpenAlex): a macrolanguage label is `exact` or
  `aggregate` for the macrolanguage and `broader` for every member, including members with their own
  label, because a detector's separation of a member from its macrolanguage is not reliable.
- **Wikipedia**: each article belongs to one edition. A member with its own edition is measured by
  that edition alone; a macrolanguage edition is `broader` for the members without one, except a sole
  remainder (`edition_complement`).
- **A macrolanguage code** takes what its sources measure at the macrolanguage level. Where no source
  measures it there, it takes the range of its members. It never takes one member's value.
- **A member code never borrows its macrolanguage's value as a point.** An individual code that a
  source reports only through its macrolanguage label (`arb` through `ara`, `cmn` through `zho`,
  `zsm` through `msa`) gets a bound.
- **Related standards stay separate.** Two codes that name overlapping varieties, such as Filipino
  (`fil`) and Tagalog (`tgl`), or a written standard and its spoken language, such as N'Ko (`nqo`)
  and Manding (`man`), are separate rows with an explicit `related_to` relation. The relation
  records a relationship, never an equivalence: a source that files one under the other is
  `broader` for it, and no count is shared between them.
- **Historical and constructed languages** carry a flag. The flag does not change any band.

Curators should declare the individual code in a product's `languages` when the dataset was built
for one member of a macrolanguage. A dataset that declares the macrolanguage is read as covering the
whole macrolanguage.

## Digital representation class

The class is the written-material band, carried through the interval rule:

| Class | Written material |
|---|---|
| `high` | A |
| `mid` | B |
| `low` | C |
| `very_low` | D |
| `unresolved` | The interval spans more than one band; both ends are published |
| `unknown` | No web-text measurement at all |

### Membership

Membership of `language_specific_datasets` and `language_specific_eval_sets` reads the class as
follows (R-2026-10-30-d):

1. **The purpose test comes first.** The dataset must be defined by the languages it serves rather
   than by its task or scale.
2. A dataset is **in** when any of its target languages is robustly below the membership line, and
   **out** when every target language is robustly at or above it. There is no majority rule.
3. Otherwise the purpose test decides on its own, and the review record says so.

The **membership line** is `high`: a language whose class is `mid`, `low` or `very_low` is
underrepresented. Pivot languages listed beside a dataset's targets do not count. English is never
below the line, so listing it can neither add a dataset nor remove one.

A change in a language's class never moves a product by itself. The roster changes it implies are
published as a review table, and each move happens in a reviewed PR that rescores the product
against its destination's recipe.

## Resource profile

The profile is three axes. Each reads `yes`, `no` or `unresolved` under the interval rule, and the
profile is published as the three values, not as a sum.

| Axis | `yes` when |
|---|---|
| `official` | `national` or `subnational` at both ends of the status interval |
| `many_speakers` | At least 1,000,000 speakers at both ends of the speaker interval |
| `large_written_material` | Written material at B or above at both ends; or, as corroboration, an eligible Wikipedia edition ([Written material](#written-material)) with 100,000 or more content articles **and** Open Library at 10,000 or more works |

**The reference profile** is all three axes `yes`. A language with the reference profile keeps the
English-scale yardstick, unrelaxed. The size yardsticks for the other seven profiles, and for
unresolved profiles, are set in the category's `scoring_recipe` (R-2026-10-30-k), not here. A product
that spans several languages takes its profile under the recipe's multilingual rule, which this
classification does not set.

## Excluded inputs

None of these is an input to either view:

- **The map's own counts**, of datasets or anything else per language. Reading them would be
  circular: adding a dataset could move its language's class, and with it the membership of every
  other dataset for that language.
- **Any count of AI resources**, such as Hugging Face dataset language tags. These measure a
  different quantity from digital representation. If wanted, they belong in a separate measure
  shown beside the class after membership.
- **OpenAlex scholarly works.** The `language` field is detected from titles and abstracts, its
  coverage follows DOI registration, and English metadata absorbs works written in other languages.
  It is published as context.
- **Joshi et al. (2020) resource classes.** They classify languages by language-technology
  resources, they are keyed by name, and their data file states no license. They may be used for
  internal validation, and are not redistributed.
- **Ethnologue**, whose terms could not be verified.

## Overrides

An override replaces one source value, or one label mapping, for one code. It exists for the cases
where a primary source is more current or more specific than the default witness, for example a
constitution that makes a language official before CLDR records it. Every override:

- names the code, the measure, the value or mapping it sets, and the default it replaces;
- cites a primary source by URL, read with `build.fetch_source`;
- carries the id of the ruling that approved it.

Overrides are rows in the measurements table, with `relation` set to the override's mapping and the
ruling id in `mapping_basis`. They are never applied in the classification step itself.

## The data contract

Two tables on Artio, each read through its own contract in `warehouse/dependencies.yaml`. The
repository keeps read-only mirror files with the `PLATFORM MIRROR (read-only)` banner and a reader
module that is added to the governed roots in the same PR as the contracts (ADR-003,
`docs/architecture/adr-003-repository-scope-boundary.md`). Neither table is ever an entry in
`warehouse/assets.yaml`.

### `language_representation.measurements`

One row per `(iso639_3, measure, source, source_version, source_label)`: every observation behind
the classification, with its declared mapping.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `iso639_3` | varchar | no | the target code |
| `measure` | varchar | no | `official_status`, `speakers`, `web_text_words`, `web_page_share`, `wikipedia_articles`, `wikipedia_active_users`, `open_library_works`, `scholarly_works`, `endangerment`, `descriptive_status` |
| `source`, `source_version`, `source_label` | varchar | no | where the value came from, and the label it was read under |
| `value_low`, `value_high` | double | yes | the value's interval; NULL for an unknown end |
| `state` | varchar | no | a [value state](#value-states-and-unknowns) |
| `label_population` | array(varchar) | no | the ISO 639-3 codes the label is declared to measure |
| `relation` | varchar | no | a [relation](#code-levels-and-macrolanguages), or `override` |
| `mapping_basis` | varchar | no | why the declaration holds, with a URL where it rests on a document; the ruling id for an override; for state `excluded`, the reason and the source's own classification (for Glottolog, the languoid's level and family) |
| `source_url` | varchar | no | the file or endpoint read |
| `retrieved_at` | timestamp(6) | no | when it was read |
| `content_sha256` | varchar | no | the digest of what was read |

### `language_representation.classification`

One row per code in scope (see [Redistribution](#redistribution)). The key is `iso639_3`.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `iso639_3` | varchar | no | the code |
| `macrolanguage` | varchar | yes | the parent macrolanguage; NULL when none |
| `related_to` | array(varchar) | no | explicitly related codes, empty when none |
| `flags` | array(varchar) | no | any of `historical`, `constructed`, `extinct`, `macrolanguage` |
| `written_best`, `written_worst` | varchar | no | written-material band interval, `A` to `D` |
| `written_state` | varchar | no | the state that set the interval |
| `representation_class` | varchar | no | `high`, `mid`, `low`, `very_low`, `unresolved`, `unknown` |
| `representation_class_best`, `representation_class_worst` | varchar | no | the two ends; equal when resolved |
| `status_best`, `status_worst`, `status_state` | varchar | no | `national` > `subnational` > `none` |
| `recognized` | varchar | no | `yes`, `no` or `unknown` |
| `speakers_low`, `speakers_high` | bigint | yes | the speaker interval; NULL for an unknown end |
| `speakers_state` | varchar | no | the state that set the interval, or `bound_from_endangerment` |
| `official`, `many_speakers`, `large_written_material` | varchar | no | `yes`, `no`, `unresolved` |
| `scholarly_works`, `endangerment`, `descriptive_status` | varchar | no | context values, or `unknown` |
| `provenance` | array(row(measure varchar, source varchar, source_version varchar, retrieved_at timestamp(6), content_sha256 varchar)) | no | one element per measure read |
| `code_table_version` | varchar | no | the ISO 639-3 release |
| `method_version` | varchar | no | the method version that produced the row |
| `computed_at` | timestamp(6) | no | when the row was computed |

**Unknown is a value, not a NULL.** A missing measurement is an interval at its full range with
state `unknown`, `not_detected` or `unmeasured`; a missing verdict is `unknown` or `unresolved`.
NULL appears only in the nullable columns above, where it means "not applicable" or "no raw
estimate". The reader fails on a NULL in a non-null column, and on a code declared in a product's
`languages` that has no row.

Neither table carries a count of datasets, benchmarks or models per language.

### Redistribution

The tables carry ISO 639-3 codes and derived values only, never the code tables' reference names.
On the platform, the classification table covers every code of scope individual or macrolanguage in
the pinned code-table release, and it stays private there while SIL's terms for a table keyed on
the full code set are unresolved. Anything redistributed, whether a public table, an export or a
file in this repository, carries only the codes declared in the map's products, unless SIL confirms
broader rights. Per-language data is published only from sources whose terms permit it.

### Refresh

Quarterly, with every source pinned: the crawl id, the FineWeb-2 release, the CLDR release, the
Glottolog release, the ISO 639-3 table date, and a retrieval time and content digest for each live
API. A refresh never moves a product. It produces a diff of changed classes and profiles and the
roster changes they imply, which is reviewed as a proposal (ADR-004).

## Versioning

`method_version` is `MAJOR.MINOR.PATCH`.

- **Major**: a change to a class or axis definition, a band edge, the membership line, an evidence
  state rule or the set of inputs. It needs a ruling, and the refresh that applies it publishes the
  full diff.
- **Minor**: a new witness or context column that leaves every existing verdict rule unchanged. It
  needs a ruling.
- **Patch**: a corrected mapping, a new override, or a source re-read under unchanged rules.

A reader pins the major version it was written for and fails on any other.

## Parameters

Method version 1:

| Parameter | Value |
|---|---|
| Written-material bands, CLD2 page share | A ≥ 1%; B 0.1% to 1%; C 0.01% to 0.1%; D < 0.01% |
| Written-material bands, FineWeb-2 words without the Bible share | A ≥ 60 billion; B 4 billion to 60 billion; C 300 million to 4 billion; D < 300 million. Fitted as a log-log line of FineWeb-2 words on CLD2 page share over the languages both measure, rounded to one significant figure |
| Wikipedia eligibility | At least 100 active users and at most 1,000 content articles per active user; applies to widening and to the corroboration path |
| Wikipedia widening | Disagreement of two or more bands, from an eligible edition |
| Membership line | Below `high` |
| `many_speakers` | 1,000,000 |
| `large_written_material` | Band B or above; or an eligible Wikipedia edition with ≥ 100,000 content articles and Open Library ≥ 10,000 works |
| Endangerment bound | AES `moribund`, `nearly extinct`, `extinct`: speakers below 1,000,000; level `language` only, outside the `Bookkeeping` and `Artificial Language` families |
