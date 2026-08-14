# Adoption Guide

How a product's adoption band is set, which instrument it was read with, and which of those
a machine can re-derive. Normative. When a rule here changes, change the guide first and make
the code follow.

> Companion to `docs/guides/openness-spectrum.md`, which owns the openness ladders, and to
> `docs/guides/verification.md`, which owns how any axis earns a `last_verified`. This guide
> owns the adoption axis: the bands, the instrument vocabulary, and what may be compared to
> what.
>
> Adoption had no guide until 2026-08-10 while openness had a whole one, and the cost was
> visible: the bands lived in a warehouse CASE expression nothing in the repo could see, and
> 71 products carried a band that contradicted their own recorded evidence.

## What the axis measures

**Real usage, not attention.** `docs/methodology.md` states it and the instrument hierarchy
below enforces it: a download count outranks a star count, and a star count is capped.

Adoption is not quality (that is capability) and not availability (that is openness). A
closed API with a million developers scores higher here than a permissively licensed library
nobody installs, and that is the intended reading.

## The three recorded fields

```yaml
adoption:
  level: 4
  reach: 1M-10M
  signal_type: usage_volume
  confidence: high
```

| field | what it is |
|---|---|
| `level` | 1-5, the band. The only field a consumer should compare across products. |
| `reach` | the band's label AND **the unit it was read in**. Not `level` restated. |
| `signal_type` | **which instrument** the band was read with. Decides what it may be compared to. |
| `confidence` | how much the reading is trusted, independent of the level. |

**`reach` is not `level` restated, and deleting it has been tried and reverted.** 20,000 stars
and 20,000 downloads are not the same reach, and the same level maps to a different label
depending on what was counted. A hardware product's reach is `mass-market`; a dataset's is
`10K-100K`. Without the unit, two products at level 3 look comparable when one was read on a
scale two orders below the other.

## The bands

Declared per **product type** in `sources/rubrics/<type>.yaml`, serialized by
`build/serialize_rubric.py` into `currentai.registry.adoption_bands`, and read from there by
the scoring models. Four declarations rather than sixteen, because the scale is a property of
what the thing IS, which is what the rubrics are already keyed on.

| level | `software` / `model` | `dataset` |
|---|---|---|
| 5 | >10M | >1M |
| 4 | 1M-10M | 100K-1M |
| 3 | 100K-1M | 10K-100K |
| 2 | 10K-100K | 1K-10K |
| 1 | <10K | <1K |

All figures are **monthly**, in the unit the type's `unit:` field names.

**Never hardcode these anywhere else.** They lived only in `currentai.signal_pypi` until
2026-08-09, which is the repo/warehouse split `check_parity` exists to catch, one axis over.

### Why `dataset` sits one order lower

Measured, not assumed. Across the 66 Hugging Face dataset artifacts carrying a figure on
2026-08-09: median 27,648, exactly one above 1M, and **none above 10M**. On the software scale
level 5 is unreachable for the entire type and 76% of datasets pile into levels 2-3, which is
a scale that cannot discriminate. Shifted down one order it reproduces the corpus's own bottom
three levels exactly and spreads like `model`'s.

Older notes in this project said datasets ran *two* orders lower. The data says one.

### Why `hardware` declares none

A board has no download count. All 20 hardware products record a qualitative reach — `niche`,
`broad`, `mass-market` — and none records a figure, so the type declares `qualitative: true`
and an empty `bands` list.

**The absence is the declaration.** A consumer that finds no band for a type must abstain
rather than borrow another type's scale. That is the same "abstain rather than substitute"
rule `sources/signal_routing.yaml` states for sources, and it is why the scoring models LEFT
JOIN the band table rather than defaulting.

### Two scales are per instrument, not per type

Stars and active users get their own scales, declared **once** on the adoption route that
produces each in `sources/signal_routing.yaml` rather than in the four type rubrics:

| level | stars |
|---|---|
| 3 | >10K |
| 2 | 1K-10K |
| 1 | <1K |

Two reasons they live there. A dataset's downloads run an order below a package's, which is
why *those* bands are per type — but a star is a star whatever it was given to, and a monthly
active user is a person whatever they came back to, so each scale is a property of the
instrument. And declaring one once is the only way to avoid four copies of a number that must
not drift.

**Capped at 3, and the cap is enforced rather than trusted.** Stars measure attention rather
than use, so a stars-derived band may never claim levels 4 or 5 however large the count.
`build/serialize_rubric.py` drops a band above the cap with a warning, so a later edit adding
a level-4 stars band fails the serializer instead of quietly publishing one. The corpus
already respects this: no `stars_fallback` product records 4 or 5.

Thresholds set 2026-08-10 from the medians the corpus already used — the 71 `stars_fallback`
products with a live GitHub row sit at medians of ~93, ~1,733 and ~15,801 stars for levels 1,
2 and 3. The ranges overlap badly (20,901 stars recorded at 2 against 77 recorded at 3), so
**this scale tightens a loose convention rather than describing one**, and applying it will
move products.

#### The active-users scale, declared 2026-08-13

| level | monthly active users |
|---|---|
| 5 | >10M users |
| 4 | 1M-10M users |
| 3 | 100K-1M users |
| 2 | 10K-100K users |
| 1 | <10K users |

**Why it did not exist, which is the more useful half.** All 23 products carrying this
instrument had a real user figure, and 22 of them wore a label off the *download* vocabulary
— because that was the only vocabulary in the building, and nothing had ever declared it
applied here. So the labels were not so much wrong as **unfalsifiable**. `character-ai` had
invented `10M-100M`, a band no scale offered, and nobody could say so.

`character-ai` is the case worth keeping. Its ~20M MAU clears the top threshold outright, but
the record sat at level **4** — held down by a label with no scale behind it to check the
label against. Declaring the scale raised it to 5. The same thing had happened to `claude-ai`,
recording `1M-10M` over a cited figure of ~19–30M. Both were the map disagreeing with itself
in a place nothing was looking.

**Same thresholds as the download scale**, which is a decision rather than an inheritance. The
alternative considered was one order higher throughout, so that ChatGPT at ~900M weekly actives
and Poe at ~18M monthly actives did not both land at 5. That was rejected: **a level has to
mean one magnitude across the whole map**, or `adoption` stops being comparable between a
package and an app. 19 of the 23 sit at level 5, and that is the map saying these are all
mass-market surfaces, which they are. A top band holding a wide range is the ordinary cost of a
five-point scale, not a defect in this instrument.

**The labels carry `users`** for the same reason the stars labels carry `stars` — and here
especially, *because* the thresholds match. An unsuffixed `>10M` is ambiguous between two live
scales at identical boundaries, and that ambiguity is precisely how a download vocabulary
colonized this instrument unnoticed. The suffix is what makes the two tellable apart when their
numbers do not differ.

**No cap.** Unlike stars, this measures use directly. That no machine can fetch it is a
question about *confidence*, not about ceiling.

##### Say what you banded

A model scores on the surface it powers — `gpt-5` on ChatGPT — and its note must say so out
loud. What the scale will not accept silently is a figure that is **not an active count**: an
all-time or cumulative user total, a device installed base, a paid-seat count. Those are the
`active_users` form of the under-coverage error below, a substitution wearing a measurement's
label, and three records carry one today with the substitution named in the note:
`github-copilot` and `github-copilot-ide` (20M **all-time**, not active) and
`apple-core-ml-runtime` (2.5B active **devices** — a person with an iPhone and a Mac is two of
it). `doubao` used to be a fourth, banding on ~330M *total* users; a measured 382M MAU now
exists and is *higher* than the total it had been leaning on.

All three scales share `registry.adoption_bands`, distinguished by `signal_type`. A consumer
that joins without filtering on it will band a package's downloads against the stars scale.

### The floor admits zero

Level 1's threshold is `above: -1`, not `0`. With `0` a product measuring exactly zero
downloads matched no band and came back unbanded — which asserts *no scale exists for this
type*, the thing hardware deliberately says, rather than *nobody downloaded it*. `zentropi-cope`
surfaced it on the first real run of the Hugging Face banding.

## The instrument vocabulary

`signal_type` records which instrument produced the band. It is a closed enum, ordered here by
how much weight it carries:

| `signal_type` | what it is | machine-re-derivable? |
|---|---|---|
| `usage_volume` | a download or install count | **yes**, where the artifact is declared |
| `active_users` | vendor-disclosed MAU or WAU. **Its own scale**, sharing the download thresholds | no |
| `reported_traction` | a credible vendor or third-party claim, with **no count behind it**. A word vocabulary, never a number | no |
| `stars_fallback` | GitHub stars. Last resort, and **capped at level 3** | yes, once stars are banded |
| `unknown` | instrument not recorded | no |

**The instrument decides what the band may be compared to**, which is the single most
load-bearing rule in this guide:

- A `usage_volume` band **claims to be a download count**. If a computed count disagrees, one
  of them is wrong — in either direction — and it is a finding, not a judgment call.
- A `reported_traction` record claims **no count at all**, so it may carry a word and never a
  number. See the vocabulary below.
- An `active_users` band claims a count of people, on the scale above. It may be compared only
  against another user count.

### The instrument is itself a claim, and it needs backing

`check_adoption` gates the **label**. `build/check_instrument.py` gates the **instrument**: a
`signal_type` asserts *how* a band was read, and that assertion needs whatever would make it
falsifiable.

**One rule, two ways to satisfy it.** A record must be re-checkable by somebody other than its
author, and there are exactly two ways to be:

| route | how | who can use it |
|---|---|---|
| **recomputation** | declares an artifact of a kind some signal model **reads**, so a model derives the number independently | `usage_volume` (pypi, HF model/dataset, arxiv), `stars_fallback` (github) |
| **re-fetch** | one source carries an `accessed` date **and** a `content_sha256`, so `check_refetch` pulls it again and reports drift | any instrument |

The instrument decides which route is *preferred*, never which is *required*. Recomputation is
strictly better — it is automatic, and it can disagree with the recorded band — but a digested
source is a real check, and a record failing **both** is the only thing the gate calls a finding.

None of it is hardcoded in the checker. `signal_routing.yaml` declares which source feeds which
instrument and whether it is `bridged`; `artifact_key` names what a product must declare for
that source to have anything to read, and `requires_evidence` carries the re-fetch fields.

**The first draft required recomputation for `usage_volume` outright, and its own test caught
the error.** 15 of the 55 unrouted records already carry a digested source —
`agent-infra-sandbox` cites `api.npmjs.org/downloads/point/last-month` showing 4,670 downloads,
with a digest. That claim is perfectly checkable; it just is not re-derivable by a pipeline that
reads no npm. Failing it would have told 15 authors their careful evidence did not count.

**Why the escape hatch stays shut.** Without the re-fetch leg, an unbacked record could pass by
relabelling itself `reported_traction` — moving an unverifiable claim into the one instrument
with no scale at all. With it, relabelling costs a dated, digested source. What no gate can
decide is whether a declared artifact is the product's *primary* channel; that is the
under-coverage judgment below, and it is why a relabel can still be wrong for honest-looking
reasons.

**A known cost of the re-fetch route.** A digest over a *count* endpoint drifts every time the
count moves, so `check_refetch` reports drift that means nothing. Drift on a vendor claim page
is informative; drift on `api.npmjs.org/downloads/point/last-month` is just Tuesday. That is an
argument for bridging npm (#163), not for rejecting the evidence.

Measured 2026-08-13, the backlog: **40** `usage_volume` records failing both routes, **95**
`reported_traction` and **20** `active_users` with no digest, **6** `stars_fallback` with no
repo. Every one passes `check_adoption --strict` green, because their labels are valid. The
label was checkable; the claim underneath it was not.

This class had been written down before. The section below recorded it as **48** products on
2026-08-10, and it grew to 55 in prose. Hence a gate.

---

Both of the latter were skipped entirely by `check_adoption` until 2026-08-13, on the ground
that comparing them against a download count is a category error. That was correct, and it is
also what hid the problem — 22 of 23 `active_users` records and 68 of 110 `reported_traction`
ones were wearing download labels, and a checker that declines to look never says so.
**Abstention is the right answer to a missing scale and the wrong answer to a scale nobody has
declared yet.**

### `reported_traction` records a word, never a number

| may record | `niche` · `broad` · `mass-market` — or nothing at all |
|---|---|

**A vocabulary, not a scale, and the difference is the point.** A scale maps a label to a level
and a disagreement between them is a finding. A vocabulary says only which words exist: the word
says what *kind* of standing was claimed, the level says *how much*, and neither is derived from
the other. Measured 2026-08-13, `niche` ran 85% level 3, `broad` 80% level 4, `mass-market` 67%
level 5 — forcing agreement would flatten exactly the residual signal those spreads represent.

**Numeric labels are illegal here, and 68 of 110 records carried one.** They were perfectly
collinear with the level beside them: `100K-1M` was level 3 on all 33 of its records, `1M-10M`
level 4 on all 23, `10K-100K` level 2 on all 7. So they carried nothing the level did not —
and they carried something false. `amazon-nova` read `1M-10M` beneath a note saying "no
standalone per-model user count published"; `aws-neuron` read `100K-1M` beneath "no
download/user count is published for Neuron". A reader sees a numeric band and concludes
somebody counted something. **Nobody did.** A number here is a measurement claim the instrument
is defined by being unable to make. All 68 were stripped on 2026-08-13; the levels stand.

**Omitting `reach` is the honest default** — 15 records already did. Record a word only where
it says something the level does not, which is usually the *shape* of the traction rather than
its size: `osprey` at 446 GitHub stars but running in production at Discord is `niche` in a way
that matters. The words are hardware's, which has used exactly these since before this route
existed; sharing them beats minting a parallel set.
- A `stars_fallback` band means no download signal existed when it was set. If one exists now,
  re-band on it.

Measured 2026-08-10, 49 of the 60 products whose recorded band exceeded the computed one
declared `usage_volume` while their own notes cited figures that matched the warehouse almost
exactly — `verl` "~81,606" against 82,200 measured, `haystack` "~883k" against 968,831,
`mistral-large` "~7.5k/mo" against 5,903. The measurement was never in dispute. The band did
not follow from the evidence the score itself recorded.

## What the machine actually computes today

| model | grain | covers | route |
|---|---|---|---|
| `currentai.signal_pypi.package_downloads` | package | 98 software products | PyPI |
| `currentai.signal_huggingface.product_adoption` | **product** | 112 model / dataset products | Hugging Face |

Both read the bands from `registry.adoption_bands` and band on the product's declared type.
Neither writes anything back to `sources/`: **a computed band is an observation, never a
score.** Only a person sets `level`, and only per `verification.md`.

**Coverage is read off the signal table, not off the roster.** The registry declared 106 PyPI
artifacts on 2026-08-14 while `signal_pypi` held 98, and the gap is not cron lag: the roster
grew during the verification sweep and the model has not caught up. Counting from
`registry.product_artifacts` overstates what is measured, and every signal model sits behind the
registry this way between runs.

### npm and crates.io: authored, not yet deployed

`sources/signal_routing.yaml` declared both as `bridged: false` with no model behind them until
2026-08-14. Three models now exist in `warehouse/models/`, and the routes stay `bridged: false`
with `blocked_by: deploy` until they run.

| model | grain | covers |
|---|---|---|
| `signal_packages.package_downloads_daily` | (product, kind, package, **day**) | 14 npm + crates artifacts, 13 products |
| `signal_packages.package_downloads` | (product, kind, package) | the same 14, plus every PyPI artifact |
| `signal_packages.product_adoption` | **product** | one band per product, summed across registries |

Four decisions in there are normative, and each is a rule this guide already states applied to a
new source:

1. **One band per product, not one per registry.** The `usage_volume` unit is "summed across
   declared artifacts", and npm, PyPI and crates.io all publish package downloads over a
   trailing 30 days. `beeai` declares an npm package and a PyPI package, so a per-registry band
   would give one product two levels over two partial figures. `kinds_counted` records which
   registries contributed, so a level 5 built from npm plus PyPI is distinguishable from one
   built on PyPI alone.
2. **Partial coverage abstains.** A declared artifact with no figure leaves `adoption_level`
   null with an `abstain_reason`. A sum over some of a product's channels is the under-coverage
   error below wearing a measurement's label.
3. **A 90-day figure is not a monthly one.** crates.io's `recent_downloads` covers 90 days and
   says so nowhere: `yomo` reports 347 there, its daily series sums to exactly 347 across 90
   days, and its trailing 30 days are 96. Banding the first would overstate the crate by 3.6x.
   `signal_routing.yaml` records this under the dimension's `never:` block, beside the older
   version of the same error — `searxng` recording "50M+ total Docker pulls" as a monthly reach.
4. **History, not a point read.** Both fetched registries are stored as daily series, because a
   trailing total cannot tell a collapse from a step change months old. npm serves 18 months and
   silently clips a longer request; crates.io serves 90 days and will not page further back.

Bridging makes these figures **recomputable**. It does not date the axis: `check_verification`
requires a `content_sha256`, only a fetch produces one, and a warehouse count can corroborate a
band without earning it a `last_verified`. Whether a computed figure may stand in for a digest is
an open decision.

### Sum across the family, not per artifact

`signal_routing.yaml` declares `sum_across_artifacts: true` for adoption, because the map's
unit is the product family rather than a repo. 107 model artifacts belong to 55 products, so
banding per artifact scores nearly half of them on a single SKU: `gemma` sums to 22.1M across
six and lands at 5, where its largest single SKU would not.

`product_adoption` does this; `package_downloads` does not yet need to (98 products, 98
packages), and the hole is latent there rather than closed.

### Route order, and taking the sum WITHIN the winning route

Adoption routes Hugging Face model → Hugging Face dataset → PyPI → npm → crates → stars, first
artifact the product has wins. The sum is taken within the winning kind, so a product shipping
both a model and its training corpus is not credited with the corpus twice.

**The three package registries are one route, not three.** They share a unit, so
`signal_packages.product_adoption` sums across them and bands once; the route order matters
between the Hub, the package registries and stars, not among npm, PyPI and crates. All 14
products on the npm and crates routes also declare a GitHub repo, so every one of them has a
`stars_fallback` route available today and two record it: `hexabot` and `yomo`.

## Products with no machine signal

Measured 2026-08-10: **168 non-hardware products record adoption ≥ 3 with no computed band at
all.** They are not one problem, and each class has a different answer:

1. **48 claim `usage_volume`.** These are misfiled rather than unmeasured. If a band claims a
   download count then a countable artifact exists — declare it and the existing machinery
   bands it. If none exists, the instrument is wrong and the band should be
   `reported_traction`.
2. **64 have a live `signal_github` row.** Stars are fetched weekly and banded nowhere. This is
   the cheapest coverage available and needs no key, subscription or bridge — see the open
   route below.
3. **104 have no signal of any kind** — hosted APIs, closed models, `mistral-large`. For these
   the answer is *not* to invent a number.

### For the genuinely unmeasurable, make the claim decay

A `reported_traction` band should cite the vendor page carrying the figure, with a URL, an
`accessed` date and a `content_sha256`, exactly as every other axis does after the
verification sweep. It is then re-checkable rather than machine-derived, and it ages against
the refresh window in `verification.md` so an unconfirmed vendor claim decays visibly instead
of sitting unfalsifiable forever.

That is the same move `establishes` made for openness and `relative_to` made for capability:
it does not make the claim automatic, it makes it falsifiable.

## Signals considered and their traps

- **GitHub stars** — real, already fetched for 258 products, banded nowhere yet. Capped at
  level 3 by the rubric because stars measure attention rather than use. **Open route.**
- **Vendor SDK downloads** — `mistralai`, `anthropic`, `cohere` on PyPI are dated proxies for
  API integration, and the trap is attribution. `cohere-rerank-api` is currently banded on
  37.9M downloads of the `cohere` package, which is the SDK for Cohere's entire API surface
  rather than the rerank product. **An SDK covering N products may not be attributed wholly to
  one**, and no such rule exists yet.
- **OpenRouter rankings** — the only true API-channel signal, via
  `/api/v1/datasets/rankings-daily`. Two limits: it returns the top 50 models per day, and its
  `hugging_face_id` bridge is empty for exactly the closed and API-first models that need it
  most. `mistral-large`'s three OpenRouter entries all carry an empty id.
- **MLPerf and Artificial Analysis** — capability instruments, not adoption. Recorded here only
  so nobody re-proposes them; see `signal_routing.yaml` for why both are unbridged anyway.

## The mirror trap: a channel that is not counted at all

Attribution has two failure modes and only one of them was written down. The `cohere-rerank-api`
case above is **over**-attribution — one SDK's downloads credited wholly to one of the N products
it serves. The opposite is **under**-coverage, and it is the more common one:

> **If the declared artifact is not the product's primary distribution channel, banding on it is
> a substitution, not a measurement.**

`n8n` is the case that established the rule. It records `usage_volume`, and its declared artifact
is the npm package at 393,738 downloads a month, which bands at level 3. But n8n is deployed
overwhelmingly as a self-hosted Docker container, and Docker Hub reports **246 million cumulative
pulls** — averaging about 2.9 million a month over the image's lifetime. Banding on npm alone
published a precise number for the wrong channel, and the note said so in its own second sentence
before recording the band anyway.

That is exactly what `sources/signal_routing.yaml` forbids: "Abstain rather than substitute. When
the authoritative signal for a dimension is missing or unusable, the rule is to produce NO
evidence." A partial channel is an unusable signal wearing a usable one's clothes, and it is worse
than an absent one, because it carries a `last_verified` date asserting that somebody confirmed it.

**What to do instead**, in order of preference:

1. **Count every channel the product actually ships through** and sum them, which is what the unit
   already says — "summed across declared artifacts". Declare the missing artifact so the sum is
   reproducible rather than hand-assembled.
2. Where a channel reports only a **cumulative** total — Docker Hub's `pull_count` is the case —
   a lifetime average is admissible as a floor, provided the note says it is a lifetime average
   and therefore understates a growing product. It is not a trailing-30-day figure and must not be
   presented as one.
3. Where the primary channel publishes nothing at all, use `reported_traction` and abstain on
   `reach`, rather than banding on the minority channel that happens to be countable.

`langflow` is the same shape and moved with it: PyPI alone gave level 2, PyPI plus the Docker
average gives about 166,000 a month and level 3. `semantic-kernel` is a third — its Python package
reaches level 4 on its own, and the .NET/NuGet channel is larger and uncounted, so its band is a
floor and its note says so.

The tell to look for when reviewing: **a note that describes the signal as understating the
product, followed by a band recorded on that signal anyway.**

## Checklist

- [ ] `level` is 1-5 and follows the band table for the product's **type**.
- [ ] `reach` carries the unit, and matches the band it claims.
- [ ] `signal_type` names the instrument actually used, not the one that sounds strongest.
- [ ] `stars_fallback` never exceeds level 3.
- [ ] A `usage_volume` band has a countable, **declared** artifact behind it.
- [ ] A `reported_traction` record cites a source with a date and a digest, and records a word
      from the vocabulary or no `reach` at all — never a number.
- [ ] An `active_users` band names the quantity it actually banded, if that quantity is not an
      active count (an all-time total, a device base, a paid-seat count).
- [ ] The band follows from the figure in the note, in the same direction and order of
      magnitude.
- [ ] No band was copied from a computed signal — those are observations, not scores.

## Related

- `docs/guides/verification.md` — how any axis earns `last_verified`, and the gates
- `docs/guides/freshness.md` — what `last_verified` means, and the refresh window
- `docs/guides/openness-spectrum.md` — the openness ladders, the other scored axis
- `sources/rubrics/<type>.yaml` — where the bands are declared
- `sources/signal_routing.yaml` — which signal is authoritative for which dimension
- `docs/schemas/score.schema.json` — the field definitions and the `signal_type` enum
