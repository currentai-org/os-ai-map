# Language digital representation: a classification specification for Artio, 2026-11-02

**Status: design brief, not an adopted method.** This is a research and design record. Its
decisions, D1 to D10, are proposals and none of them is adopted. No membership change follows from
it, and no product moves because of it. Each decision takes effect only through a ruling recorded in
`docs/rulings/log.yaml`. Indonesian's classification in particular is not settled, and nothing here
moves IndoNLU.

This brief specifies the per-language classification that R-2026-10-30-d would put on Artio (the
OSO warehouse) and that this repository would read as a dependency contract. It works out a
methodology for R-2026-10-30-d (membership of `language_specific_datasets`) and R-2026-10-30-k
(per-class yardsticks for the size caps). It is design only. It writes nothing to the warehouse and
changes nothing in `warehouse/`, `sources/` or `build/`. The contract entries below are proposals and
are not added to `warehouse/dependencies.yaml`.

Like the other records in `docs/briefs/`, it describes its sources on the date above and is refreshed
by a new brief, not edited. Every figure comes from a source fetched on that date with
`build.fetch_source` (Appendix E lists them with their digests) or from `sources/` on `main` at the
same date.

**Revision 2026-11-02.** Revised before merge in response to review. What changed:

- The class is now named and described as a measure of a language's **digital representation**,
  not of AI-resource availability, and a new section explains the difference. Gap Map counts and
  other AI-resource counts are excluded as inputs by construction.
- **OpenAlex** is reassessed and four weightings are tested. Under a median of three, any positive
  weight gives OpenAlex the same deciding vote, so the real choice is whether it votes at all. The
  recommendation changes to leaving it out of the class.
- **Macrolanguages** no longer get any automatic equivalence. Each source's labels are mapped to
  the populations they measure, per source, and a label broader or narrower than the target code
  contributes a bound, not a point value. CLDR's alias table no longer supplies equivalences.
- A **sensitivity analysis** shows how membership under "below high" moves across the OpenAlex
  variants and the macrolanguage treatments, with explicit rows for Indonesian, Korean,
  Vietnamese, Turkish, Arabic and Hindi. "Below high" is framed as the starting hypothesis.
- A **Before implementation** section states two prerequisites: reconciling the `add-data-source`
  skill with ADR-003, and resolving the ISO 639-3 redistribution question.
- The tables are renamed from `language_resources` to `language_representation`.

## What the classification is for

The classification **contextualizes depth measurements. It is not a prerequisite for the depth
ladder.** Evaluation depth (R-2026-10-30-i, R-2026-11-01-a to -h) measures the evidence a dataset
holds for one language and task. The classification would say how well that language is represented
in the digital record. The two never feed each other: no depth band reads a representation class, and
no representation class reads a dataset's depth. They meet in two places only, both downstream:

- **Membership** (R-2026-10-30-d). Whether a dataset belongs in `language_specific_datasets` turns on
  the purpose test plus whether its target languages are underrepresented. The classification
  would answer the second half.
- **Yardsticks** (R-2026-10-30-k). Which size yardstick a capped dataset is measured against depends
  on its language's class. This brief proposes the classes. It does not set the yardsticks'
  thresholds, which belong to the recipe PR.

## Digital representation is not AI-resource availability

The class this brief proposes measures **how much of a language exists as digital text in general**:
web pages, Wikipedia articles, scholarly works. It does not measure how many datasets, benchmarks or
models exist for the language. Those are two different quantities, and the class reads only the
first.

**Why it matters.** The two diverge in both directions. A language can be digitally well
represented and still AI-resource poor: plenty of web text and an active Wikipedia, but few curated,
documented, openly licensed datasets or evaluation sets. A language can also be the reverse: a
concentrated research program produces corpora and benchmarks for it while its general web presence
stays small. A class that blended the two would put both kinds of language in the middle and hide
exactly the cases the map most needs to show. The category's finding is a comparison of AI
resources against a language's place in the digital record, and the comparison means something only
if the two sides are measured independently.

**No Gap Map count is an input.** The class reads nothing from this repository: not the map's
products, not its rosters, not any count of datasets drawn from the map. That would be circular. The
class decides category membership, so if it read the map's dataset counts, adding a dataset for a
language could move that language's class and with it the membership of other datasets for the same
language. For the same reason it reads no other count of AI resources, such as Hugging Face dataset
language tags.

**AI-resource availability, if it is wanted, is a separate measure downstream.** It can be computed
after membership, from the map or from outside catalogs, and shown beside the class in the review
table and the language view. It never feeds the class.

## The short answer

- **Four dimensions, kept separate.** Official or regional status, speaker population, written and
  academic literature, and digital and web presence. Each would be published on its own, from named
  sources, with its own `unknown`.
- **Every value an interval of bands.** A measured value would be one band. A missing one would be
  the full range, never zero. A value from a source label that measures a broader or narrower
  population than the target code would be a bound. A class or verdict would stand only when it
  holds across the whole interval, which is the robustness test of R-2026-11-01-a applied to
  languages.
- **Two derived views, one per ruling, and no weighted index.** A *digital representation class*
  (high, mid, low, very low) for membership, and a *yardstick profile* of three yes-or-no axes from
  R-2026-10-30-k (official, many speakers, large literature) for the caps.
- **OpenAlex out of the class.** Tested four ways, OpenAlex either decides the contested languages
  or does not vote. This brief recommends that it not vote: the class would then stand only where
  web share and Wikipedia agree, and the contested languages fall to the purpose test.
- **Explicit mappings, no equivalence.** Each source's labels would be mapped to the populations
  they measure. `ar`, `ms`, `zh`, `fa` and `sw` labels would not be taken as `arb`, `zsm`, `cmn`,
  `pes` or `swh`.
- **One table on Artio, read through two contracts.**
  `currentai.language_representation.classification` would hold one row per ISO 639-3 code. Its
  input table, `language_representation.measurements`, would need a contract too, because the
  dependency gate follows a mirror file's reads.
- **Validation.** 162 products declare 2,971 distinct codes. Each resource source reaches 158 to 346
  of them directly. Under "below high", Korean, Vietnamese, Arabic and Hindi come out
  underrepresented with OpenAlex voting, and Indonesian, Turkish, Ukrainian and Swedish do not.
  Without OpenAlex, only Korean and Hindi keep a settled call among those eight, and the other six
  fall to the purpose test. Nothing is decided here.

## Before implementation

Two prerequisites would have to be met before any of this is built.

**1. Reconcile the `add-data-source` skill with ADR-003.** An input owned on Artio is a dependency
contract in `warehouse/dependencies.yaml` and never an entry in `warehouse/assets.yaml`. The skill
at `skills/add-data-source/SKILL.md` still describes the older model, and an agent following it for
this classification would produce exactly what ADR-003's gates refuse. Where it diverges:

- Its description says it "Registers it in the asset inventory". For a source built and owned on
  Artio, the registration is a contract in `warehouse/dependencies.yaml`, not an asset entry.
- Its preferred route is "A UDM reads the source directly (`authority: platform`, a mirror model
  under `warehouse/models/<dataset>/`)". ADR-003 and `build/assets.py` refuse `authority: platform`
  on every governed role (`role_violations`): a platform mirror is a dependency contract, and its
  file must carry the `PLATFORM MIRROR (read-only)` banner (gate 7, `mirror_ownership_violations`).
- Editor step 1 says to add an entry to `warehouse/assets.yaml` "for the table the source lands in",
  whatever the route. It never mentions `warehouse/dependencies.yaml`, the required `role` field on
  governed assets, or the contract fields (`purpose`, `expected_grain`, `freshness_requirement`,
  `required_by`, `verified_revision`, `owner: oso`, the `mirror` block).
- It does not mention gate 4. A contract needs a `required_by` that `build/assets.py` re-derives from
  a governed root, and the root set is closed (`AUDIT_ROOTS`), so the reader module has to land in
  the same PR and be added to the roots. Without that, the contract fails the gate.
- Step 3 runs only `tests/test_assets_inventory.py`. The scope gates that would catch the
  divergences above are asserted in `tests/test_scope_gates.py`, which the skill does not name.
- Its fetcher route points at `warehouse/models/catalog/<table>.py`. That directory no longer
  exists: `docs/operations/refresh-data.md` records that ADR-003 externalized the catalog tables and
  their producers were deleted.

This brief does not edit the skill. Fixing it is its own PR.

**2. Resolve the ISO 639-3 redistribution question.** SIL's terms for the code tables allow
incorporating the codes with attribution, provided the product "does not provide a means to
redistribute the code set" (Appendix A). A table keyed on every ISO 639-3 code, as proposed here,
may count as such a means even if it carries no reference names. Whether it does is a question for
SIL, and it applies equally to the repository's own snapshot, `sources/snapshots/iso-639-3.tab`. No
derived table should be published until it is answered. If the answer is no, the fallback is a
table keyed only on the codes the map declares, which would need the same question answered for a
subset.

## Methodology (proposed)

Everything in this section is a proposal. None of it is in force.

### Dimensions and measures

| Dimension | Measure | Recommended source | Absence means |
|---|---|---|---|
| Official or regional status | Official at national level, at regional level, or neither | Unicode CLDR territory data (`_officialStatus`), with Wikidata P37 on sovereign states as a second witness | Not national, because 250 of CLDR's 258 territories name an official or de facto official language, and the other eight are uninhabited or placeholder territories. Regional or none is `unknown`. |
| Speaker population | Speakers, banded by order of magnitude | CLDR territory population × language share, and Wikidata P1098 | `unknown` |
| Written and academic literature | Scholarly works whose metadata is in the language | OpenAlex `language`, grouped. Used by the yardstick axis `large_literature`; not a class input under D2's recommendation. | `unknown`, because the detector does not cover most languages |
| Digital and web presence | (a) Share of web pages | Common Crawl's published CLD2 language statistics, latest crawl | `unknown`, because CLD2 detects only 160 languages |
| | (b) Wikipedia content articles | Wikimedia site matrix with per-edition counts | An observed zero: the list of Wikipedia editions is complete. Bounded above where a macrolanguage edition may hold the language. |
| Context, not class inputs | Descriptive status (Glottolog MED), endangerment (Glottolog AES) | Glottolog CLDF | `unknown` |

Bands for the three digital measures sit at powers of ten:

| Band | Web share | Wikipedia articles | Scholarly works |
|---|---|---|---|
| A | ≥ 1% of pages | ≥ 1,000,000 | ≥ 1,000,000 |
| B | 0.1% to 1% | 100,000 to 1,000,000 | 100,000 to 1,000,000 |
| C | 0.01% to 0.1% | 10,000 to 100,000 | 10,000 to 100,000 |
| D | < 0.01% | < 10,000 | < 10,000 |

Speakers use five bands: A ≥ 100M, B 10M to 100M, C 1M to 10M, D 100k to 1M, E < 100k. Where CLDR and
Wikidata disagree, the interval runs between them. For Swahili they span 15M to 194M, because CLDR
counts second-language use.

### What OpenAlex measures

OpenAlex's `language` field is, in its own documentation, "the language of the work's metadata
(title/abstract), in ISO 639-1 format, auto-detected with langdetect", and it "Reflects the metadata
language, not necessarily the full text, and is unset when there aren't enough words to guess
reliably." So it counts scholarly records whose title and abstract a detector reads as the
language. Four biases follow, and each bears on the languages this brief has to call:

- **English-dominant metadata.** English holds 234.3M of the 322.7M works in the 200 language groups
  returned, 73%. A work written in another language but indexed with an English title and abstract
  counts as English, so the count for any other language undercounts its scholarly output by an
  amount that varies with each publishing community's habits.
- **Detection, not declaration.** The label is guessed from short text. The groups include labels a
  scholarly literature is unlikely to support at that scale, such as Cebuano (259k works) and Waray
  (57k), and noise keys (`EN`, `中文`, `gr`, `ua`, `xx`). The documentation names langdetect, but
  langdetect's README lists 55 supported languages, without Cebuano, Waray or Malay, while the
  groups include all three, so which detector produced the current labels was not established.
  Closely related pairs, Malay and Indonesian above all, are where short-text detection is least
  reliable.
- **Coverage follows registration.** OpenAlex indexes what reaches it through DOI registration,
  repositories and other feeds, so a country whose journals register DOIs widely is counted more
  fully than one whose journals do not. Indonesian (3.60M) and Korean (3.28M) rank far above Arabic
  (935k) and Vietnamese (140k), and above Italian (2.59M). That may reflect registration practice
  more than the volume of literature. The per-country breakdown that would test this for Indonesian
  could not be fetched on this date (HTTP 429 on the shared free budget, Appendix E).
- **It measures scholarship, not digital text in general.** Even read perfectly, it counts a narrow
  slice of a language's digital record, weighted toward languages with a large academic system.

### How OpenAlex could be weighted

Four variants were run on the same data (Appendix F has the counts):

- **V1, equal vote.** The class is the median of web share, Wikipedia and OpenAlex, as in the first
  draft.
- **V2, reduced weight.** A weighted median with OpenAlex at half weight. With three measures this is
  **identical to V1 for every code**, and not by coincidence: when web share and Wikipedia agree,
  they settle the median whatever OpenAlex says, and when they disagree, OpenAlex's band picks the
  result under any weight above zero and below two. A median gives OpenAlex no partial vote.
- **V3, tiebreaker only.** Web share and Wikipedia decide when they agree. When they disagree,
  OpenAlex picks whichever of the two is nearer its own band. This differs from V1 only where the two
  are two or more bands apart, which happens for six of the 2,971 codes. One of them shows the cost:
  Cebuano, with a bot-written Wikipedia of 6.1M articles and 0.0019% of web pages, goes from mid to
  high, because OpenAlex's 259k works sit nearer the Wikipedia band.
- **V4, OpenAlex removed.** Web share and Wikipedia must agree. Where they differ, the class is
  `unresolved` and spans both. OpenAlex stays in the table as a published context column and as the
  input to the `large_literature` yardstick axis.

So the real choice is between V1 and V4. V3 is V1 with an extra failure mode.

**What OpenAlex decides.** Among the languages the first draft called, OpenAlex is the deciding vote
for exactly the contested ones. Web share and Wikipedia disagree for Indonesian, Turkish, Ukrainian
and Swedish (OpenAlex pushes them to high) and for Arabic, Vietnamese and Persian (it pushes them to
mid). Korean and Hindi do not depend on it, because web share and Wikipedia agree for both. OpenAlex's
biases are largest for precisely the languages where it decides, and it measures metadata language
in a scholarly index, which is the narrowest of the three signals. That is the case for V4.

### Macrolanguages and code levels

Sources report at different levels. Common Crawl says `ara`, `zho`, `fas`, `msa`, `swa`. OpenAlex and
Wikipedia use ISO 639-1 codes, which map to an ISO 639-3 macrolanguage for `ar`, `ms`, `zh`, `fa` and
`sw`. Products in the map often declare an individual code such as `arb`, `zsm` or `cmn`. The
proposed rule is **explicit mappings and uncertainty bounds, with no automatic equivalence unless the
source itself measures that exact population.** Converting a code between ISO 639-1 and 639-3 says
which code a label names, not which population a source measured. CLDR's macrolanguage alias
table (`cmn`→`zh`, `arb`→`ar`, `zsm`→`ms`, `pes`→`fa`, `swh`→`sw` and 58 more) supplies no
equivalences.

**The mapping is declared per source.** For each source and source version, every label the source
emits is recorded with the population it is declared to measure, the relation of that population to
each target code, and the basis for the declaration. The relations are:

| Relation | When | Contribution to the target |
|---|---|---|
| `exact` | The label measures the target's population | A point value |
| `aggregate` | The target is a macrolanguage and the source labels it and its members separately, each item once | The sum, as a point value |
| `edition_complement` | Wikipedia only: a macrolanguage edition whose other members all have their own editions, leaving the target as the sole remainder | A point value |
| `broader` | The label covers the target and other languages | A bound: the lower end is the target's own exact label, or the floor (band D) if it has none; the upper end adds the broader label's value |
| `members_only_lower_bound` | The target is a macrolanguage, the source labels only some of its members, and its list is not complete | A lower bound; the upper end is unknown (band A) |
| `observed_absent` | Wikipedia only: no edition for the target or its macrolanguage | An observed zero |

The default declarations follow from each source's construction, and any of them can be overridden
with a cited basis:

- **Common Crawl and OpenAlex** are detectors. A macrolanguage label measures the macrolanguage as
  the detector defines it, so it is `exact` or `aggregate` for the macrolanguage target and
  `broader` for every member, including members with their own label, because a detector's
  separation of a member from its macrolanguage is not reliable.
- **Wikipedia** is a complete list of editions, and each article belongs to one. A macrolanguage
  edition measures the macrolanguage minus the members that have their own edition. A member with
  its own edition is measured by that edition alone. A remaining member gets a point value only when
  it is the sole remainder (`edition_complement`), and the edition is `broader` for the rest. The
  Norwegian edition `no` measures Bokmål (`nob`) this way, because Nynorsk has its
  own, which replaces the hand mapping the first draft used.
- **The same mapping applies to speakers and status.** CLDR reports some populations at
  macrolanguage level, so a member's speaker figure taken from a macrolanguage row is an upper bound,
  and a macrolanguage's official status gives a member an interval from `none` to that status unless
  a source names the member.

How the cases the review named come out, from the dry run's data:

| Target | Web share (CC) | Wikipedia articles | Scholarly works (OpenAlex) | Class, V1 | First draft |
|---|---|---|---|---|---|
| `ara` | 0.67% B | 2.99M A (aggregate) | 939k B (aggregate) | mid | mid |
| `arb` | ≤0.67% B–D (bounded) | ≤1.34M A–D (bounded) | 497–936k B–D (bounded) | unresolved (mid to very low) | mid |
| `ary` | ≤0.67% B–D (bounded) | 21k C | ≤935k B–D (bounded) | unresolved (mid to very low) | unresolved (mid to very low) |
| `arz` | ≤0.67% B–D (bounded) | 1.63M A | 4k–939k B–D (bounded) | unresolved (mid to very low) | unresolved (mid to very low) |
| `msa` | 1.16% A (aggregate) | 1.49M A (aggregate) | 3.77M A (aggregate) | high | high |
| `zsm` | ≤0.0917% C–D (bounded) | ≤445k B–D (bounded) | ≤162k B–D (bounded) | unresolved (mid to very low) | mid |
| `ind` | 1.06%–1.16% A (bounded) | 803k B | 3.60M–3.77M A (bounded) | high | high |
| `zho` | 4.37% A | 2.25M A (aggregate) | 5.56M A (aggregate) | high | high |
| `cmn` | ≤4.37% A–D (bounded) | ≤1.56M A–D (bounded) | 3k–5.56M A–D (bounded) | unresolved (high to very low) | high |
| `yue` | ≤4.37% A–D (bounded) | 154k B | 338–5.55M A–D (bounded) | unresolved (high to very low) | unresolved (high to very low) |
| `fas` | 0.62% B | 1.10M A | 547k B | mid | mid |
| `pes` | ≤0.62% B–D (bounded) | ≤1.10M A–D (bounded) | ≤547k B–D (bounded) | unresolved (mid to very low) | mid |
| `prs` | ≤0.62% B–D (bounded) | ≤1.10M A–D (bounded) | ≤547k B–D (bounded) | unresolved (mid to very low) | unresolved (mid to very low) |
| `swa` | 0.0099% D | 132k B | 6k D | very low | very low |
| `swh` | ≤0.0099% D (bounded) | ≤132k B–D (bounded) | ≤6k D (bounded) | very low | very low |
| `swc` | ≤0.0099% D (bounded) | ≤132k B–D (bounded) | ≤6k D (bounded) | very low | very low |

Three things follow. First, the macrolanguage codes the map mostly declares (`ara`, `zho`, `fas`,
`swa`) are measured by every source at their own level, so their classes do not move. Second, an
individual code under a macrolanguage label (`arb`, `cmn`, `pes`, `zsm`) loses the point value CLDR's
alias gave it and becomes a bound. For `cmn` that bound runs from high to very low until a source is
declared, with a cited basis, to measure Mandarin as such. Third, Indonesian's Wikipedia value is now
a point (803k, B) rather than the first draft's A–B, because the Malay edition is a different
population: Indonesian has its own edition. Indonesian's other two values remain bounds that stay
within band A.

Under the declared mappings, 18 of the 2,971 codes change class interval against the first draft
(among them `arb`, `cmn`, `pes`, `zsm`, `ekk`, `lvs`, `uzn`, `bjn` and `kok`). No roster outcome
changes under V1, V2 or V3. Under V4, two dialect datasets (`atlaset`, `darijammlu`) move from the
purpose test to in, because Moroccan Arabic's Wikipedia value is now its own edition's 21k.

**Curators** would do well to prefer an individual code in `languages` when a dataset was built for
one member. A dataset that declares `msa` reads as the whole Malay macrolanguage, Indonesian included,
which is high, while one that declares `zsm` reads as Standard Malay, which is unresolved from mid to
very low.

### How the dimensions combine

**Proposal: keep the four dimensions separate and derive two views, with no weighted index.** The two
rulings ask different questions, and an index would answer neither well. Membership asks how much of
a language is in the digital record. The yardsticks ask which comparison is fair. Folding speakers
into the class would make membership relative to population, which is a separate decision (D3).
Folding web share into the yardstick would add an axis R-2026-10-30-k did not name. Weights would
have no defensible basis, and an index hides which signal moved a language. Separate dimensions also
keep `unknown` local: a missing speaker count cannot unsettle a class that does not read it.

**Digital representation class** (membership). Under D2's recommendation, take the bands of web share
and Wikipedia articles, each as an interval. The class runs from the better of the two best ends to
the worse of the two worst ends. If that is one band, it is the class: high (A), mid (B), low (C) or
very low (D). Otherwise the class is `unresolved` and both ends are published. Under the alternative
(V1), the class is the median of three intervals computed at both ends, as in the first draft.

**Yardstick profile** (caps). There are three axes. `official` is national or regional status.
`many_speakers` is at or above a speaker cut. `large_literature` is at or above a scholarly-works cut.
Each axis reads yes, no or `unresolved` by the same interval rule. D9 proposes the cuts.
`large_literature` would read OpenAlex, with the biases set out above, so a profile that turns on it
should be read with them in mind.

### Feeding membership and the yardsticks

**Membership** would follow D5 of the
[2026-10-30 brief](2026-10-30-language-specific-datasets-structure.md#decisions) and
R-2026-10-30-d. The purpose test comes first. Then a dataset is in when any of its target languages is
robustly underrepresented, and out when every target language is robustly not. Otherwise the purpose
test decides on its own, and the row says so. There is no majority rule. Because English is never
underrepresented, this "any" rule makes treating English as a pivot irrelevant to membership: listing
it can neither add a dataset nor remove one.

**Yardsticks.** For each capped dataset, the recipe would evaluate the cap under every profile the
intervals allow. If every profile gives the same band, that band stands. If not, the cap is
unresolved for that dataset and the record says so. No profile is assumed. The thresholds per profile
are the recipe PR's to set.

## Explicit `unknown`

`unknown` is a recorded state, never a default (R-2026-11-01-a). Three rules would hold throughout:

1. **A missing value is never zero and never underrepresented.** A language CLD2 does not detect has
   an unknown web share, not 0%. A language absent from OpenAlex's groups has unknown scholarly
   output, not none. A language with no speaker figure is unknown, not "few".
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

## Table schema and data contract (proposed)

### The tables

**`currentai.language_representation.classification`**: one row per ISO 639-3 code of scope
individual or macrolanguage in the pinned code-table release, subject to the redistribution question
in [Before implementation](#before-implementation). It covers every such code, not just the map's
codes, so it does not depend on the corpus. The key is `iso639_3`.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `iso639_3` | varchar | no | the code (key) |
| `macrolanguage` | varchar | yes | parent macrolanguage, NULL when none |
| `web_share_best`, `web_share_worst` | varchar | no | band interval, `A`–`D` |
| `web_share_state` | varchar | no | `measured`, `bounded`, `unknown` |
| `wikipedia_best`, `wikipedia_worst`, `wikipedia_state` | varchar | no | as above, plus state `observed_absent` |
| `scholarly_best`, `scholarly_worst`, `scholarly_state` | varchar | no | as above; context and yardstick input |
| `speakers_best`, `speakers_worst`, `speakers_state` | varchar | no | band interval, `A`–`E` |
| `speakers_low`, `speakers_high` | bigint | yes | the raw estimates behind the speaker interval |
| `status_best`, `status_worst`, `status_state` | varchar | no | `national` > `regional` > `none` |
| `representation_class` | varchar | no | `high`, `mid`, `low`, `very_low`, `unresolved`, `unknown` |
| `representation_class_best`, `representation_class_worst` | varchar | no | the two ends, equal when resolved |
| `official`, `many_speakers`, `large_literature` | varchar | no | `yes`, `no`, `unresolved` |
| `descriptive_status`, `endangerment` | varchar | no | Glottolog MED and AES values, or `unknown` |
| `provenance` | array(row(measure varchar, source varchar, source_version varchar, retrieved_at timestamp(6), content_sha256 varchar)) | no | one element per measure read |
| `code_table_version` | varchar | no | the ISO 639-3 release, such as `20261015` |
| `method_version` | varchar | no | the version of this specification's rules |
| `computed_at` | timestamp(6) | no | when the row was computed |

The table carries no count of datasets, benchmarks or models per language. An AI-resource measure,
if one is built, belongs in a separate table read after membership.

**The value of `unknown`.** A missing measure is `<measure>_state = 'unknown'` with the interval at
its full range (`best = 'A'`, `worst = 'D'`). A missing class is the string `unknown` or `unresolved`.
NULL never stands for a missing measurement. It appears only in the nullable columns above, where it
means "not applicable" (no macrolanguage) or "no raw estimate". A NULL in a non-null column is a
contract violation, which the repository's reader (below) fails on.

**`currentai.language_representation.measurements`**: the raw observations behind the classification,
with the declared mapping for each. It holds one row per (`iso639_3`, `measure`, `source`,
`source_version`, `source_label`), with `value_low double` and `value_high double` (NULL for an
unknown end), `label_population array(varchar)` (the ISO 639-3 codes the label is declared to
measure), `relation varchar` (`exact`, `aggregate`, `edition_complement`, `broader`,
`members_only_lower_bound`, `observed_absent`), `mapping_basis varchar` (why the declaration holds,
with a URL where it rests on a document), `source_url varchar`, `retrieved_at timestamp(6)` and
`content_sha256 varchar`. This is the table a reviewer reads to see why a language sits where it does,
and where a mapping is challenged. Its name avoids `observations`, which is a governed dataset here
(naming rule 4 in [`data-architecture.md`](../architecture/data-architecture.md), section 11.1a).

### Ownership, cadence and the contract

**Ownership.** Both tables would be built and owned on Artio (`owner: oso`). The maintainer named in
ADR-003 maintains them, and changes are requested by issue in this repository. The repository would
keep read-only mirror files with the `PLATFORM MIRROR (read-only)` banner under
`warehouse/models/language_representation/`. Neither table would ever enter `warehouse/assets.yaml`.
This is the route the `add-data-source` skill does not yet describe (see
[Before implementation](#before-implementation)).

**Cadence.** Quarterly, with each source pinned to a version: the crawl ID, the CLDR release, the
Glottolog release, the ISO 639-3 table date, and a retrieval time plus content hash for the live
APIs. Representation levels move slowly, and a class change moves products. A refresh would
therefore never move a product. It would produce a diff of changed classes and implied roster
changes, which goes through review as a proposal (ADR-004: machines propose, humans accept).

**Two contracts, because of the dependency gates.** The repository must not add the contract before
it has a reader. Gate 4 in [ADR-003](../architecture/adr-003-repository-scope-boundary.md) requires a
`required_by` that `build/assets.py` re-derives from a governed root, and the root set is closed
(`AUDIT_ROOTS`). The reader, `build/language_representation.py` (an illustrative name), would
therefore land in the same PR as the contract and be added to `AUDIT_ROOTS`. It would render the
review table, and fail when a code in `languages` has no row. Gate 2 then follows the classification
mirror's reads, so `language_representation.measurements` needs its own contract, read by the
classification mirror. That is the same dependency-to-dependency shape as
`evidence.product_evidence` → `scores.openness_facts`.

The proposed entries follow, in `warehouse/dependencies.yaml`'s shape. Values in angle brackets would
be filled at sync time, from `GetDataModel` and the mirror file's bytes.

```yaml
- table: currentai.language_representation.classification
  purpose: language_digital_representation
  expected_grain: one row per ISO 639-3 code of scope I or M in the pinned code-table release
  freshness_requirement: <= 100 days (quarterly platform refresh)
  required_by:
  - build/language_representation.py
  verified_revision: <revision released on Artio>
  owner: oso
  files:
    model: warehouse/models/language_representation/classification.sql
    schema: warehouse/models/language_representation/classification.schema.json
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
- table: currentai.language_representation.measurements
  purpose: language_digital_representation_measurements
  expected_grain: one row per (iso639_3, measure, source, source_version, source_label)
  freshness_requirement: <= 100 days (quarterly platform refresh)
  required_by:
  - warehouse/models/language_representation/classification.sql
  verified_revision: <revision released on Artio>
  owner: oso
  files:
    model: warehouse/models/language_representation/measurements.py
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
datasets were built for. They are reported separately as the *targeted* set. These declarations are
read only to test the classification. They are not inputs to it.

**Coverage.** Counted as direct matches, the digital sources reach few codes: Common Crawl 158 of
2,971 (105 of the 193 targeted), Wikipedia 346 (147) and OpenAlex 160 (88). The context sources reach
more: CLDR 623 (162), Wikidata speaker counts 1,021 (178) and Glottolog 2,926 (173). Joshi et al.,
matched by name, reach 877 (133). Appendix B adds the codes reached through a macrolanguage, which
under the declared mappings give a bound only.

**What no source covers.** No digital source (web share, Wikipedia or OpenAlex) reaches 2,482 of the
2,971 codes, directly or through a macrolanguage. Among the targeted set that is 35 codes, listed in
Appendix D. Three codes have no value in any source: `ldn` (Láadan, constructed), `nwx` (Middle
Newar, historical) and `ota` (Ottoman Turkish, historical).

**Dry run.** With declared mappings and OpenAlex voting (V1), the 2,971 codes come out 16 high, 27
mid, 29 low, 160 very low and 2,739 `unresolved`. The 193 targeted codes come out 16 high, 20 mid, 22
low, 47 very low and 88 `unresolved`. With OpenAlex removed (V4), the counts are 12 high, 19 mid, 10
low, 66 very low and 2,864 `unresolved` for all codes, and 12, 16, 7, 27 and 131 for the targeted
set. No code is wholly `unknown`, because every code has at least a Wikipedia observation. The long
tail stays unresolved because at most one of its measures is observed, and under R-2026-10-30-d such
a language would be decided on the purpose test alone. Where the classes overlap Joshi et al. (2020),
they agree in direction: no Joshi class 0 to 2 language comes out high, and no class 4 or 5 language
comes out very low (Appendix C).

### Sensitivity of the membership decisions

"Below high" counts mid, low and very low as underrepresented. It is the **starting hypothesis**
for the membership line, not a final classification: it is the line the review table would be built
against first, and D3 settles it only after that table has been read. "Low or very low" is the
alternative.

**Across the OpenAlex variants**, with declared mappings, the 97 `language_specific_datasets`
products come out as follows under "below high":

| Variant | In | Out | Purpose test only | Not in |
|---|---|---|---|---|
| V1, equal vote | 92 | 3 | 2 | `indonlu`, `turkishmmlu`, `ubertext` out; `saami-web`, `smugri-data` to the purpose test |
| V2, half weight | 92 | 3 | 2 | identical to V1 |
| V3, tiebreaker only | 92 | 3 | 2 | identical to V1 |
| V4, OpenAlex removed | 84 | 0 | 13 | to the purpose test: `101-billion-arabic-words`, `arabicmmlu`, `arabicweb24`, `cidar`, `indonlu`, `khayyam-challenge`, `naab`, `saami-web`, `smugri-data`, `turkishmmlu`, `ubertext`, `vietnamese-curated-dataset`, `vmlu` |

Under "low or very low", V1 to V3 give 70 in, 23 out and 4 to the purpose test, and V4 gives 63 in,
23 out and 11 to the purpose test. Nothing leaves under "below high" without OpenAlex. Every product
that the first draft's dry run would have moved out sits on a call OpenAlex decides.

**Across the macrolanguage treatments**, the first draft's CLDR equivalence and the declared
mappings give the same roster under V1, V2 and V3. Under V4 the declared mappings bring `atlaset`
and `darijammlu` from the purpose test to in.

**The six languages under review**, under "below high". The bands are web share, Wikipedia and
OpenAlex, from the declared mappings. "Smallest flip" is the smallest change in one measure that
would reverse the V1 verdict, which shows how close each call sits to a band edge.

| Language | Bands (web, Wiki, OA) | V1 | V2 | V3 | V4 | Macrolanguage treatment | Smallest flip under V1 | Robust? |
|---|---|---|---|---|---|---|---|---|
| Indonesian (`ind`) | A, B, A | out (high) | out | out | purpose test (high to mid) | First draft bounded Wikipedia A–B through the Malay edition; declared mapping gives B. Same verdicts either way. | web share −6% | **Flips** with OpenAlex removed, and sits 6% above the web edge |
| Korean (`kor`) | B, B, A | in (mid) | in | in | in (mid) | Not a macrolanguage member; no bound | web share +13% or Wikipedia +30% | **Robust** across variants; near the high edge on two measures |
| Vietnamese (`vie`) | B, A, B | in (mid) | in | in | purpose test (high to mid) | Not a macrolanguage member; no bound | web share +2% | **Flips** with OpenAlex removed, and sits 2% below the web edge |
| Turkish (`tur`) | A, B, A | out (high) | out | out | purpose test (high to mid) | Not a macrolanguage member; no bound | web share −13% | **Flips** with OpenAlex removed |
| Arabic (`ara`) | B, A, B | in (mid) | in | in | purpose test (high to mid) | Measured at macrolanguage level by every source; unchanged. `arb` becomes mid to very low (in under V1–V3, purpose test under V4). `ary` stays in under every variant; `arz` goes to the purpose test under V4. | OpenAlex +6% | **Flips** with OpenAlex removed, and OpenAlex sits 6% below its edge |
| Hindi (`hin`) | B, B, C | in (mid) | in | in | in (mid) | Not a macrolanguage member; no bound | none: two measures would have to reach band A | **Robust** |

Under "low or very low", all six are out under every variant: none of them reaches low at either end
of any interval.

**What the table says.** Korean and Hindi are robust calls. Hindi's rests on web share and Wikipedia
both in band B, clear of either edge, and Korean's on the same agreement, though both of its
deciding measures sit within a third of the high edge. The other four are not settled by this
evidence. Indonesian and Turkish read high only because OpenAlex breaks a disagreement between web
share and Wikipedia; Arabic and Vietnamese read mid for the same reason in the other direction. Each
of the four also sits within 13% of a band edge on its deciding measure. These four are where the
review table should show the raw values and where the purpose test carries the weight.

**Indonesian and IndoNLU.** Indonesian's classification is not settled. It reads high only with
OpenAlex voting, it sits 6% above the web edge, and its OpenAlex count is the one most open to the
registration and Malay-detection biases above. Nothing in this brief moves `indonlu`, under any
variant.

## Decisions for the maintainer

None of these is adopted. Each takes effect only through a ruling in `docs/rulings/log.yaml`. Each
can be answered in a sentence; the recommendation comes first.

- **D1. Structure.** Keep four dimensions separate and derive two views (a digital representation
  class for membership, a three-axis profile for the yardsticks), with no weighted index?
  *Recommend yes.*
- **D2. Class inputs and OpenAlex.** Is the class read from web share and Wikipedia articles only,
  standing where they agree and `unresolved` where they differ (V4), with OpenAlex published as
  context and used by the `large_literature` axis? Or the median of three with OpenAlex voting (V1)?
  *Recommend V4.* A reduced weight is not a third option, since under a median it equals V1, and a
  tiebreaker adds failures such as Cebuano. In both options, speakers, status, Gap Map counts and
  any other AI-resource count stay out.
- **D3. The membership line.** Is a language underrepresented when it is below high (mid, low or very
  low), or only when it is low or very low? *Recommend below high as the starting hypothesis,* to be
  confirmed or changed once the review table from Artio has been read. With V4 it moves no product
  out and leaves 13 to the purpose test. The lower line would also take out Arabic, Hindi, Bengali,
  Thai and Vietnamese, among others, and 23 products in all.
- **D4. Band edges.** Set them at powers of ten (1%, 0.1% and 0.01% of pages; 1M, 100k and 10k
  articles or works)? *Recommend yes for the first version, with raw values published beside every
  band,* so the edge cases (Vietnamese at 2% from an edge, Indonesian and Arabic at 6%) stay visible.
- **D5. Robustness.** Does a class or verdict stand only when it holds across every value the unknowns
  and bounds allow, with no single-signal fallback? *Recommend yes.* It is R-2026-11-01-a's test. The
  cost is that most of the long tail stays unresolved and is decided on the purpose test.
- **D6. Absence.** Does absence count as an observation only in a list that is complete by
  construction (Wikipedia editions, CLDR national official languages), and is silence from a detector
  or index `unknown`? *Recommend yes.*
- **D7. Macrolanguages.** Replace CLDR's alias equivalence with per-source declared mappings, where a
  label broader or narrower than the target code gives a bound and only a label measuring the exact
  population gives a point value? *Recommend yes,* with curators preferring an individual code in
  `languages` when a dataset was built for one member.
- **D8. Excluded inputs.** Leave out the map's own counts of open datasets per language, any other
  count of AI resources (Hugging Face dataset tags among them), Joshi et al. (2020) and Ethnologue?
  *Recommend yes.* The map's counts are circular, since adding a dataset would move its language's
  class and with it other datasets' membership. AI-resource counts measure a different thing from
  digital representation and belong in a separate measure shown beside the class. Keep Joshi as a
  validation reference only: it classifies languages by the resources available for language
  technology, it is a 2020 snapshot keyed by name, and 1,001 of its 2,485 names match no ISO
  reference name. Ethnologue's terms could not be read, and a secondary source reports it paywalled.
- **D9. Yardstick axes.** Is `official` national or regional status, `many_speakers` 10 million or
  more, and `large_literature` 100,000 or more scholarly works? *Recommend these as the starting cuts,*
  to be confirmed when the recipe PR dry-runs the caps against them, with OpenAlex's biases noted
  wherever `large_literature` decides a profile.
- **D10. Contracts and cadence.** Two contracts (classification and measurements), a quarterly refresh
  pinned to source versions, and every class change surfaced as a review proposal that never moves a
  product on its own? *Recommend yes.*

## Sequence

1. **Prerequisites** from [Before implementation](#before-implementation): the `add-data-source`
   skill reconciled with ADR-003 in its own PR, and the ISO 639-3 redistribution question answered.
2. **Ruling** on D1 to D10, recorded in `docs/rulings/log.yaml`.
3. **Artio** (maintainer, on the platform): build `language_representation.measurements` and
   `language_representation.classification` to the ruled specification.
4. **Repository PR**: the reader module (added to `AUDIT_ROOTS`), the two mirror files and the two
   contracts, and the published review table with the roster changes it implies. Nothing moves.
5. **Ruling** adopting the table and settling the membership line.
6. **Membership** and **yardsticks**, in the order of the
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
snapshot; it is a prerequisite in [Before implementation](#before-implementation). The macrolanguage
mapping (`iso-639-3-macrolanguages.tab`) says which codes are members of which macrolanguage. It says
nothing about which population a source measured.

**Common Crawl language statistics.** `languages.csv` gives pages per primary language per crawl. It
covers 129 crawls, the latest being `CC-MAIN-2026-43`, with 162 labels in that crawl. The detector is
CLD2, which "is able to identify 160 different languages", and only HTML pages are passed to it.
Codes are ISO 639-3, some at macrolanguage level (`ara`, `zho`, `fas`, `msa`, `nor`, `swa`). CLD2
labels Indonesian and Malay separately (`ind` 1.06%, `msa` 0.09%). Coverage is 158 (+130) of all codes
and 105 (+14) of the targeted ones. The statistics repository carries the Apache License 2.0. No
separate data license for the CSV was found. Recent crawls are four to five weeks apart.
Reproducibility is good: crawls are immutable and named. Biases: detection is limited to CLD2's set,
the `<unknown>` bucket holds 3.06% of pages, text in a script the detector does not expect for a
language (romanized Arabic or Hindi, for instance) is not counted for it, and language share follows
what the crawler reaches.

**Wikipedia.** The Wikimedia site matrix lists 364 Wikipedia editions, 16 of them closed. The dry run
read content-article counts from the third-party Wikistats dump. Its page says it is updated daily
and that it "is not the Wikimedia Analytics Wikistats". Artio should read per-edition statistics from
Wikimedia's own API instead. Coverage is 346 (+129) and 147 (+9). Edition codes are not ISO codes.
Most are ISO 639-1. For this dry run, nine composite prefixes (`zh-yue`, `zh-min-nan`, `roa-rup`, and
others) were mapped by hand, and six were left unmapped (`simple`, `eml`, `map-bms`, `roa-tara`, `bh`,
`nah`). The Norwegian edition is mapped by the edition-complement rule rather than by hand. The dump's
license was not checked. Biases: bot-generated articles inflate some editions. Cebuano has 6.1M
content articles and Egyptian Arabic 1.6M, more than the Arabic edition's 1.3M.

**OpenAlex.** OpenAlex states that its data is CC0. What its `language` field measures, and its
biases, are set out in [What OpenAlex measures](#what-openalex-measures). Grouping by language
returned 200 groups, the smallest holding 115 works. A request for a second page failed (HTTP 400),
so whether the tail can be paged was not established. Coverage is 160 (+106) and 88 (+9). The API
meters unauthenticated use against a free daily budget shared per IP address, which ran out during
this session, so Artio should use a key or OpenAlex's snapshot.

**Crossref.** Not usable for this purpose through its REST API. Requesting a `language` facet
returns HTTP 400 ("no such facet for this route"), and `language` is not a selectable field. Counting
by language would mean processing the full metadata dump, which was not assessed. The license was not
checked.

**Unicode CLDR territory data.** Version 49 (`cldr-core` 49.0.0), under the Unicode License v3, which
permits use and redistribution with the notice. It holds 258 territories, each with a population and
a list of languages with population percentages and, where official, `official` (339 entries),
`de_facto_official` (21) or `official_regional` (136). Coverage is 623 (+150) and 162 (+14). Release
cadence was not checked. Reproducibility is good: releases are versioned. Biases: percentages mix
first- and second-language use, codes are BCP 47 with script variants, some languages are reported
at macrolanguage level, and minority languages are listed unevenly. Its `languageAlias` table lists
63 macrolanguage aliases. They describe locale identifiers, not the populations other sources
measured, so the declared mappings do not use them.

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
0 to 5 (2,191 of them class 0). The paper studies languages "especially in terms of their resources"
for language technology, which places its classes nearer AI-resource availability than digital
representation. Exact matching against ISO reference names resolves 1,482 rows, and 1,001 match
nothing. It reaches 877 (+153) and 133 (+10) codes. The paper is CC BY 4.0 (ACL Anthology). No license
for the data file was found: the project page states none, and its GitHub repository did not answer
(HTTP 403). It is frozen in 2020 and keyed by name, so it serves as validation only.

**Ethnologue.** Its pages returned HTTP 403 to every fetch, so its terms could not be read here.
Wikipedia's article on it reports a hard paywall since 2019, with subscriptions from $480 a year. That
is secondary and was not verified against Ethnologue. Its coverage was not assessed. It is excluded.

**Not assessed.** National bibliographies, for literature in a language rather than about it, would
be a candidate for a later method version, as a second literature source beside OpenAlex. Hugging
Face dataset language tags were not assessed as a class input and would not be one: they count AI
resources, which the class excludes by design. They could feed a separate AI-resource measure.

## Appendix B: coverage of the declared codes

Direct matches, then in brackets the codes reached only through their macrolanguage. Under the
declared mappings, a macrolanguage value reached this way is a bound, not a measurement.

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

Verdicts across all codes and the targeted set, with declared mappings:

| Variant | Line | Set | Underrepresented | Not underrepresented | Unresolved |
|---|---|---|---|---|---|
| V1 | Below high | all 2,971 | 297 | 16 | 2,658 |
| V1 | Below high | targeted 193 | 108 | 16 | 69 |
| V1 | Low or very low | all 2,971 | 223 | 44 | 2,704 |
| V1 | Low or very low | targeted 193 | 81 | 36 | 76 |
| V4 | Below high | all 2,971 | 243 | 12 | 2,716 |
| V4 | Below high | targeted 193 | 97 | 12 | 84 |
| V4 | Low or very low | all 2,971 | 159 | 40 | 2,772 |
| V4 | Low or very low | targeted 193 | 59 | 35 | 99 |

The 16 targeted codes not underrepresented under "below high" with V1 are `deu`, `eng`, `fra`, `ind`,
`ita`, `jpn`, `msa`, `nld`, `pol`, `por`, `rus`, `spa`, `swe`, `tur`, `ukr` and `zho`. With V4 they
are 12: the same list without `ind`, `swe`, `tur` and `ukr`.

## Appendix C: dry run for named languages

Bands are A (most) to D (least), from the declared mappings, with the class under V1. "Aggregate"
marks a macrolanguage summed over its labels in one source. "Bounded" marks an interval from a label
broader than the target. "Edition complement" marks a macrolanguage edition whose only remaining
member is the target. Speakers show the CLDR and Wikidata figures as a range. Appendix F gives the
other variants.

| Code | Web share (CC) | Wikipedia articles | Scholarly works (OpenAlex) | Class (V1) | Below high | Low or very low | Status | Speakers |
|---|---|---|---|---|---|---|---|---|
| `eng` | 42.56% A | 7.26M A | 234.33M A | high | no | no | national | 753.4M–1733.0M |
| `spa` | 4.74% A | 2.15M A | 12.19M A | high | no | no | national | 485.0M–512.4M |
| `por` | 2.47% A | 1.19M A | 6.23M A | high | no | no | national | 249.5M–254.3M |
| `jpn` | 4.89% A | 1.53M A | 13.07M A | high | no | no | national | 117.6M–128.0M |
| `zho` | 4.37% A | 2.25M A (aggregate) | 5.56M A (aggregate) | high | no | no | national | 1299.9M–1324.2M |
| `kor` | 0.88% B | 770k B | 3.28M A | mid | yes | no | national | 77.3M–79.3M |
| `ara` | 0.67% B | 2.99M A (aggregate) | 939k B (aggregate) | mid | yes | no | national | 315.4M–378.8M |
| `ind` | 1.06%–1.16% A (bounded) | 803k B | 3.60M–3.77M A (bounded) | high | no | no | national | 180.6M–199.0M |
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
| `est` | 0.15% B | 270k B (aggregate) | 59k C | mid | yes | no | national | 854k–1.3M |
| `nor` | 0.35% B (aggregate) | 875k B (aggregate) | 322k B (aggregate) | mid | yes | no | national | 5.2M–5.5M |
| `swe` | 0.71% B | 2.63M A | 1.03M A | high | no | no | national | 9.2M–13.3M |
| `kaz` | 0.0385% C | 246k B | 21k C | low | yes | yes | national | 12.9M–14.7M |
| `urd` | 0.0315% C | 707k B | 8k D | low | yes | yes | national | 68.6M–313.1M |
| `eus` | 0.0372% C | 500k B | 66k C | low | yes | yes | regional | 750k–1.0M |
| `glg` | 0.0333% C | 247k B | 43k C | low | yes | yes | regional | 2.4M–3.3M |
| `isl` | 0.0366% C | 61k C | 18k C | low | yes | yes | national | 321k–364k |
| `khm` | 0.0107% C | 13k C | 533 D | low | yes | yes | national | 15.2M–16.6M |
| `mya` | 0.0157% C | 113k B | 697 D | low | yes | yes | national | 32.9M–37.2M |
| `swa` | 0.0099% D | 132k B | 6k D | very low | yes | yes | national | 15.4M–194.1M |
| `yor` | 0.0017% D | 41k C | 187 D | very low | yes | yes | national | 31.8M–37.8M |
| `amh` | 0.0042% D | 16k C | 762 D | very low | yes | yes | national | 21.9M–39.2M |
| `lao` | 0.0056% D | 6k D | 1k D | very low | yes | yes | national | 5.2M–5.5M |
| `mlt` | 0.0034% D | 8k D | 2k D | very low | yes | yes | national | 470k–570k |
| `fao` | 0.0057% D | 14k C | 228 D | very low | yes | yes | national | 69k–73k |
| `mri` | 0.0019% D | 8k D | 205 D | very low | yes | yes | national | 145k–214k |
| `ary` | ≤0.67% B–D (bounded) | 21k C | ≤935k B–D (bounded) | unresolved (mid to very low) | yes | unresolved | none found | 27.5M–32.5M |
| `arz` | ≤0.67% B–D (bounded) | 1.63M A | 4k–939k B–D (bounded) | unresolved (mid to very low) | yes | unresolved | none found | 64.6M–71.2M |
| `nob` | ≤0.34% B–D (bounded) | 694k B (edition complement) | 733–309k B–D (bounded) | unresolved (mid to very low) | yes | unresolved | national | 4.0M–5.5M |
| `nno` | 0.0138%–0.35% B–C (bounded) | 181k B | 13k–321k B–C (bounded) | unresolved (mid to low) | yes | unresolved | national | 1.4M–4.3M |
| `sme` | A–D (unknown) | 8k D | A–D (unknown) | unresolved (high to very low) | unresolved | unresolved | regional | 26k–53k |

Agreement with Joshi et al. (2020), for the 135 declared codes that have both a Joshi class and a
resolved class under V1:

| Joshi class | high | mid | low | very low |
|---|---|---|---|---|
| 5 | 5 | 1 | 0 | 0 |
| 4 | 7 | 10 | 1 | 0 |
| 3 | 2 | 14 | 9 | 0 |
| 2 | 0 | 0 | 3 | 10 |
| 1 | 0 | 0 | 14 | 50 |
| 0 | 0 | 0 | 0 | 9 |

## Appendix D: targeted codes no digital source reaches

These 35 of the 193 targeted codes have no web share, Wikipedia edition or OpenAlex group, directly
or through a macrolanguage. Each has at least a Glottolog or CLDR entry, so its status, speakers and
descriptive context can still be published.

`ach`, `bau`, `bgc`, `bho`, `brx`, `bxk`, `bzd`, `cni`, `ctp`, `doi`, `gbm`, `hch`, `hne`, `hoj`,
`kca`, `kln`, `kok`, `kpo`, `lri`, `luo`, `mas`, `mns`, `mup`, `mwr`, `ndc`, `nde`, `nus`, `nyn`,
`rag`, `shp`, `sid`, `sog`, `taq`, `tar`, `wal`

## Appendix E: how the numbers were produced

The declared codes were read from `sources/products/*.yaml` and the rosters from
`sources/categories/*.yaml`, read-only, to test the classification, never as inputs to it. The pivot
declarations were read from `capability.pivot_languages` in `sources/scores/`, though the "any" rule
makes them immaterial to membership. Every source below was fetched on 2026-11-02 with
`uv run python -m build.fetch_source`, and the digest is the `content_sha256` it reported. The
sensitivity analysis reran the dry run on the same fetched bytes, once with the first draft's rules
and once with the declared mappings, under each of the four OpenAlex variants. It is not the Artio
implementation, and its counts will differ from the Artio table wherever Artio reads a primary API in
place of the convenience source used here (Wikistats).

| Source | URL | Status | content_sha256 |
|---|---|---|---|
| Common Crawl language statistics (CSV) | https://commoncrawl.github.io/cc-crawl-statistics/plots/languages.csv | 200 | `261dfd2da5e9bfa8975f57711e23ab639b2f1b6c174273e9182a55e05ed46bf1` |
| Common Crawl language statistics (page) | https://commoncrawl.github.io/cc-crawl-statistics/plots/languages | 200 | `860f75c88d2a2a7adada677a2f98e0df7cc68779a282962da48c980dff6ce9e4` |
| cc-crawl-statistics license | https://raw.githubusercontent.com/commoncrawl/cc-crawl-statistics/master/LICENSE | 200 | `b40930bbcf80744c86c46a12bc9da056641d722716c378f5659b9e555ef833e1` |
| Wikistats Wikipedia dump | https://wikistats.wmcloud.org/api.php?action=dump&table=wikipedias&format=csv | 200 | `4a72e35e175b0597640f7d8f7f98088a6bc23354a51309e603a8183d1a087af2` |
| Wikistats page | https://wikistats.wmcloud.org/ | 200 | `ea6eece899861abcc2c561879ac83e18b5ef34ede9ba6affe369f8c538e773b1` |
| Wikimedia site matrix | https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json&smtype=language&smlangprop=code%7Csite%7Clocalname | 200 | `f60f8c0f6c81caafc44588b06710ef6e13eb78d660e3703ae7aa8515d73028cc` |
| OpenAlex works by language | https://api.openalex.org/works?group_by=language&per_page=200 | 200 | `bdfade2b989357d38568f4c053a37e90337de75ba0d14215080aa3280787b33c` |
| langdetect README (supported languages) | https://raw.githubusercontent.com/Mimino666/langdetect/master/README.md | 200 | `d8e1f0f7040ada7f50bd28b3639aa33272da78fb547d01414d8bed35f53c4108` |
| OpenAlex Indonesian works by author country | https://api.openalex.org/works?filter=language:id&group_by=authorships.countries&per_page=10 | 429 | – |
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

## Appendix F: sensitivity counts

Class counts for all 2,971 codes and the 193 targeted codes, by macrolanguage treatment and OpenAlex
variant. V2 equals V1 for every code under both treatments.

| Treatment | Variant | All: high / mid / low / very low / unresolved | Targeted: high / mid / low / very low / unresolved |
|---|---|---|---|
| First draft (CLDR equivalence) | V1, V2 | 17 / 34 / 32 / 160 / 2,728 | 16 / 20 / 23 / 48 / 86 |
| First draft (CLDR equivalence) | V3 | 18 / 33 / 29 / 162 / 2,729 | 16 / 20 / 22 / 48 / 87 |
| First draft (CLDR equivalence) | V4 | 13 / 19 / 11 / 66 / 2,862 | 12 / 15 / 8 / 27 / 131 |
| Declared mappings | V1, V2 | 16 / 27 / 29 / 160 / 2,739 | 16 / 20 / 22 / 47 / 88 |
| Declared mappings | V3 | 17 / 26 / 26 / 162 / 2,740 | 16 / 20 / 21 / 47 / 89 |
| Declared mappings | V4 | 12 / 19 / 10 / 66 / 2,864 | 12 / 16 / 7 / 27 / 131 |

Roster outcomes for the 97 `language_specific_datasets` products (in / out / purpose test only):

| Treatment | Variant | Below high | Low or very low |
|---|---|---|---|
| First draft | V1, V2, V3 | 92 / 3 / 2 | 70 / 23 / 4 |
| First draft | V4 | 82 / 0 / 15 | 63 / 23 / 11 |
| Declared mappings | V1, V2, V3 | 92 / 3 / 2 | 70 / 23 / 4 |
| Declared mappings | V4 | 84 / 0 / 13 | 63 / 23 / 11 |

V3 differs from V1 for six codes under the declared mappings: `afr`, `ceb`, `epo`, `ndo`, `vro` and
`war`. Under the first draft's rules it is the same set without `vro`.
