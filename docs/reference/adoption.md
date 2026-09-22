# Adoption Guide

How a product's adoption band is set, which instrument it was read with, and which of those
a machine can re-derive. Normative. When a rule here changes, change the guide first and make
the code follow.

> Companion to `docs/reference/openness.md`, which owns the openness ladders, and to
> `docs/reference/evidence-and-freshness.md`, which owns how any axis earns a `last_verified`. This guide
> owns the adoption axis: the bands, the instrument vocabulary, and what may be compared to
> what.

## What the axis measures

**Real usage, not attention.** `docs/methodology.md` states it and the instrument hierarchy
below enforces it: a download count outranks a star count, and a star count is capped.

Adoption is not quality (that is capability) and not availability (that is openness). A
closed API with a million developers scores higher here than a permissively licensed library
nobody installs, and that is the intended reading.

### Routing is by artifact kind, not by product

A signal is authoritative for one **artifact kind**, never for a product as a whole. A model's
code repository and its weights routinely carry different licenses, and the code repository is
the wrong answer for the weights dimension — `governs` on each route in `signal_routing.yaml`
records what the value is a fact *about*, so a license attached to code is never read as a
license attached to weights.

A cross-check against GitHub's own license field finds it disagreeing with the recorded value on
a minority of products, and in every model case among the disagreements Hugging Face agreed with
the recorded value and GitHub was the outlier — `glm-5-2` (recorded MIT, HF `mit`, GitHub
`Apache-2.0`), `lucie-7b` (recorded Apache-2.0, HF `apache-2.0`, GitHub `GPL-3.0`), and likewise
`mimo-v2-5-pro`, `zephyr` and `tulu-3`. A naive "refresh license from GitHub" pass would have
overwritten every one of those correct model scores with the wrong license, each change looking
like a well-sourced improvement. Routing by artifact kind is what keeps that class of error from
occurring.

### Abstain rather than substitute

When the authoritative signal for a dimension is missing or unusable, the rule is to produce no
evidence and leave the dimension to research. Falling through to a less authoritative signal
silently reintroduces the artifact-kind failure above under a different name, so a missing route
is never patched by substituting the nearest available one.

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
| `banded_quantity` | **what was actually counted**, where that is not a current usage figure for this product. Optional; absent means nothing was borrowed. |
| `confidence` | how much the reading is trusted, independent of the level. |

### `banded_quantity` — say what you banded, as a field

A level read off something other than the product is not a defect on its own — often it is the
most honest reading available — but it has to be legible. Record what the figure counts:

```yaml
adoption:
  level: 4
  signal_type: reported_traction
  banded_quantity: Replit platform registered users (50M+, March 2026), not an agent active count
```

**Absent is a real answer**, not an unfilled field. It means the level is a judgment about
the product itself with no borrowed quantity behind it. `claude-opus` and `claude-fable` both
record a market-position reading and cite no number at all, and both correctly carry nothing
here.

Four shapes recur, and they are worth telling apart:

| shape | example |
|---|---|
| a parent platform's reach, the product being a feature inside something larger | `azure-ai-foundry-observability` bands Microsoft Foundry |
| a real count of the product that is not a current active one | `v0`'s 4M+ cumulative users; `codex-cli`'s **weekly** actives against a monthly scale |
| a proxy of another kind entirely | `claude-code`'s ~$2.5B run-rate; `openhands`'s 83.9k stars |
| nothing, where the note cites a figure only to reject it | `perspective-api` — Jigsaw has never published one |

**Why a field and not better prose.** Prose does not travel. A parent-platform record can
describe its own substitution in its note, in capitals if it likes, and a consumer reading
`level: 4` off the warehouse still gets a number about Replit with nothing attached saying so.
`active_users` states the same rule one instrument over — the `attribution_note` on its route in
`sources/signal_routing.yaml` requires a record to name a figure that is not an active count — and
`banded_quantity` is that rule as a field, on the instrument that needs it most.

**The gate covers the decidable half.** `tests/test_banded_quantity.py` requires a
`banded_quantity` wherever a `reported_traction` note cites a **magnitude** — a figure with a
suffix or thousands separators, never a bare integer, so "28 enterprise testimonials" does
not trip it. A number in the prose of an instrument that claims no count is exactly what a
reader mistakes for a measurement. What no regex can catch is a parent-platform band citing
no figure at all; those were backfilled by hand and nothing enforces them, which is the same
ratchet `check_capability` uses.

The gate is strict rather than a ratchet, unlike `check_adoption` and `check_instrument`, because
there is no backlog for it to meet: every record needing a `banded_quantity` carries one.

**`reach` is not `level` restated.** 20,000 stars
and 20,000 downloads are not the same reach, and the same level maps to a different label
depending on what was counted. A hardware product's reach is `mass-market`; a dataset's is
`10K-100K`. Without the unit, two products at level 3 look comparable when one was read on a
scale two orders below the other.

## The bands

Declared per **product type** in `sources/rubrics/<type>.yaml`, serialized by
`build/serialize_rubric.py` into `currentai.registry.adoption_bands`, and read from there by
the scoring models. Four declarations rather than one per category, because the scale is a property of
what the thing IS, which is what the rubrics are already keyed on.

| level | `software` / `model` | `dataset` |
|---|---|---|
| 5 | >10M | >1M |
| 4 | 1M-10M | 100K-1M |
| 3 | 100K-1M | 10K-100K |
| 2 | 10K-100K | 1K-10K |
| 1 | <10K | <1K |

All figures are **monthly**, in the unit the type's `unit:` field names.

**Never hardcode these anywhere else.** A band table living in warehouse SQL and nowhere the
repo can read is the repo/warehouse split `check_parity` exists to catch, one axis over.

### Why `dataset` sits one order lower

Measured, not assumed. 65 of the 70 dataset products quote a trailing-30-day download figure in
their recorded adoption evidence, 64 of them read from Hugging Face; MATH's is a zero, its
canonical Hub repository being walled off by a takedown. Each product's figure is the **sum
across its declared artifacts** on the winning route, per "Sum across the family, not per
artifact" below — Terminal-Bench is 65,672 across three release mirrors and LiveBench 36,032
across ten, not the largest single mirror of each. Measured 2026-09-20 over those 65: median
32,927, two above 1M, and **none reaching 10M**. Banded on the software scale they put level 5
out of reach for the entire type and pile 49 of them, 75%, into levels 2 and 3, which is a scale
that cannot discriminate. Shifted down one order the same figures spread across all five levels
— 4, 10, 35, 14 and 2 — with 16 at 4 or 5.

**Known disagreement, deliberately not resolved by the shift.** Some dataset products record a
level against a `reach` that would place them one level higher on the shifted scale, because
they were read in a different unit entirely — a citation count for a benchmark, GitHub stars for
a corpus shipped as code — and `reach` carries the unit precisely so those are not silently
treated as comparable. Reading each one against the shifted scale is a work list for a future
re-read, not evidence against the shift.

### Why `model` and `software` share one scale

Measured, not assumed. Across the model products recording both a level and a reach, model
downloads sit at a median in the same order of magnitude as PyPI package downloads. Hugging Face
model downloads and PyPI package downloads are close enough that one scale serves both, which is
why `model` and `software` share the table in "## The bands" rather than each carrying its own
row.

### Why `hardware` declares none

A board has no download count. Hardware products record a qualitative reach — `niche`,
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

The three thresholds are round numbers on the instrument, not a summary of the corpus, and the
corpus is read against them rather than the other way round. Measured 2026-09-20: of the 169
`stars_fallback` products, 167 quote a star count in their evidence, and every one of those 167
sits inside the band its recorded level names — medians of 211, 3,181 and 24,216 stars for
levels 1, 2 and 3, with the largest count at level 1 at 986 and the smallest at level 3 at
11,860. The two that do not (`slurm`, `tesseract`) cite the repository page without quoting the
number off it, which is a `shows` defect rather than a banding one.

#### The active-users scale

| level | monthly active users |
|---|---|
| 5 | >10M users |
| 4 | 1M-10M users |
| 3 | 100K-1M users |
| 2 | 10K-100K users |
| 1 | <10K users |

**Why the scale has to be declared.** An instrument with no declared scale does not produce
wrong labels; it produces **unfalsifiable** ones. A record carrying a real user figure will wear
a label borrowed from the download vocabulary, because that is the only vocabulary in the
building, and a record can invent a band no scale offers — `10M-100M` — with nothing able to say
so. The level then drifts from the figure beneath it in the one direction nobody is checking: a
record citing tens of millions of monthly actives carries a `1M-10M` label and nothing fails,
because without a declared scale there is nothing for the label to be wrong against. A declared
scale is what makes a label answerable to its own figure.

**Same thresholds as the download scale**, which is a decision rather than an inheritance. The
alternative considered was one order higher throughout, so that ChatGPT at ~900M weekly actives
and Poe at ~18M monthly actives did not both land at 5. That was rejected: **a level has to
mean one magnitude across the whole map**, or `adoption` stops being comparable between a
package and an app. Most records on this instrument sit at level 5, and that is the map saying
these are all mass-market surfaces, which they are. A top band holding a wide range is the ordinary cost of a
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
label. The records that carry one name the substitution in the note:
`github-copilot` and `github-copilot-ide` (20M **all-time**, not active) and
`apple-core-ml-runtime` (2.5B active **devices** — a person with an iPhone and a Mac is two of
it). `doubao` is not one of them: it bands on a measured 382M MAU, which is higher than the
all-time total a substitution would have reached for.

All three scales share `registry.adoption_bands`, distinguished by `signal_type`. A consumer
that joins without filtering on it will band a package's downloads against the stars scale.

### The floor admits zero

Level 1's threshold is `above: -1`, not `0`. With `0` a product measuring exactly zero
downloads matches no band and comes back unbanded — which asserts *no scale exists for this
type*, the thing hardware deliberately says, rather than *nobody downloaded it*.

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

### Authority is declared, not inferred

An adoption route's `authority` — `authoritative` or `fallback` — is a routing decision, not a
property the instrument name can be trusted to carry, so it is declared explicitly on the route
rather than derived from it. A `usage_volume` count and a hand-read `active_users` disclosure are
both authoritative because each measures use directly; `stars_fallback` and `reported_traction`
are both fallback, the last resorts before abstention. `hand_authored` and `confidence` stay
orthogonal to it: whether a figure was read by a person, and how much to trust it, are separate
questions from whether the route is authoritative for the dimension.

Route precedence is monotonic in authority: every authoritative route is tried, in list order,
before either fallback route — so a hand-read `active_users` disclosure precedes
`stars_fallback` even though it is hand-authored, because authoritative outranks fallback
regardless of either. Within the authoritative download channels the order follows the ADR-001
precedence `pypi > huggingface`, so `pypi` leads the two Hugging Face routes, with the unbridged
npm and crates usage routes ranking after the bridged download channels and still ahead of the
fallback stars and reported-traction routes.

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

**Requiring recomputation for `usage_volume` outright would reject real evidence.** A sizable
minority of unrouted records carry a digested source — `agent-infra-sandbox` cites
`api.npmjs.org/downloads/point/last-month` showing 4,670 downloads, with a digest. That claim is
perfectly checkable; it is simply not re-derivable by a pipeline that reads no npm, and failing it
would tell those authors their careful evidence did not count.

**Why the escape hatch stays shut.** Without the re-fetch leg, an unbacked record could pass by
relabelling itself `reported_traction` — moving an unverifiable claim into the one instrument
with no scale at all. With it, relabelling costs a dated, digested source. What no gate can
decide is whether a declared artifact is the product's *primary* channel; that is the
under-coverage judgment below, and it is why a relabel can still be wrong for honest-looking
reasons.

**A known cost of the re-fetch route.** A digest over a *count* endpoint drifts every time the
count moves, so `check_refetch` reports drift that means nothing. Drift on a vendor claim page
is informative; drift on `api.npmjs.org/downloads/point/last-month` is just Tuesday. That is an
argument for bridging npm, not for rejecting the evidence.

A record failing both routes still passes `check_adoption --strict` green, because its label is
valid. The label is what `check_adoption` can see; the claim underneath it is what
`check_instrument` is for. `uv run python -m build.check_instrument` prints the live backlog.

A checker that declines to look at an instrument never reports what is wrong with it, and
`reported_traction` and `active_users` are the two where that costs most: comparing either
against a download count is a category error, so skipping them is defensible and it is also how
a whole instrument comes to wear another instrument's labels unnoticed. **Abstention is the right
answer to a missing scale and the wrong answer to a scale nobody has declared yet.**

### `reported_traction` records a word, never a number

| may record | `niche` · `broad` · `mass-market` — or nothing at all |
|---|---|

**A vocabulary, not a scale, and the difference is the point.** A scale maps a label to a level
and a disagreement between them is a finding. A vocabulary says only which words exist: the word
says what *kind* of standing was claimed, the level says *how much*, and neither is derived from
the other. The words correlate with the levels without determining them — measured 2026-09-20,
`niche` runs 13 of 16 at level 3, `broad` 6 of 7 at level 4 and `mass-market` 7 of 9 at level 5 —
and forcing agreement would flatten exactly the residual signal those spreads represent. The
denominators are small enough that these are counts rather than rates; quoting them as
percentages would imply a precision three records do not support.

**A numeric label is illegal here.** It is collinear with the level beside it, so it carries
nothing the level does not, and it carries something false: `1M-10M` beneath a note saying "no
standalone per-model user count published", or `100K-1M` beneath "no download/user count is
published for Neuron". A reader sees a numeric band and concludes somebody counted something.
**Nobody did.** A number here is a measurement claim the instrument is defined by being unable to
make, and stripping one leaves the level alone.

**Omitting `reach` is the honest default**, and most records on this instrument do. Record a word only where
it says something the level does not, which is usually the *shape* of the traction rather than
its size: `osprey` at 462 GitHub stars but running in production at Discord is `niche` in a way
that matters. The words are hardware's, and sharing a vocabulary beats minting a parallel one.

### When a re-read may re-band, and when it may not

These are curation rules and no gate enforces them; `docs/workflows/refresh-category.md` is where
a pass applies them.

- **A measured signal on an already-declared artifact beats a hand-set band.** The artifact was
  declared, so the count is the instrument the record already claims to have been read with, and
  the band follows the count. Re-band, and put the figure in the note.
- **A `stars_fallback` band means no download signal existed when it was set.** If one exists
  now, re-band on it.
- **A `usage_volume` record over a page publishing no count at all is on the wrong instrument.**
  Move it to `reported_traction`, drop the numeric `reach`, and **leave the level alone.** What
  was wrong is the claim to have counted something, not the reading of the product's standing.
  Re-deriving the level is a separate judgment and needs its own evidence.
- **Declaring a NEW artifact requires it to be provably the product's own AND its primary
  channel.** Both, not either. `gvisor`, `ollama`, `promptfoo` and `opencompass` each have a
  findable package, and declaring it would move a level on a minority channel. That is the
  under-coverage error below, met from the other direction.
- **A package's usage bands the head product only when installing that package is itself a
  meaningful unit of use of the scored product.** A client or component package whose population
  can vary independently from the head product measures its own users, and is not attributed to
  the head product merely because it is first-party or required to reach it. The question is
  measurement-population identity, not whether the package is an SDK; `docs/reference/identity.md`
  ("A declared artifact is a measurement identity") is the rule this one applies to adoption.
  The test cuts both ways and being first-party decides nothing. The package IS the product for
  `evidently` and `monocle` (the SDK is the whole product), `axon` (the CLI installs and runs it)
  and `quilt` (a substantive product surface of its own); it is a client or a component for
  `weaviate-client` (a server's client), `openmldb` (a cluster's client), `ragaai-catalyst` (a
  closed platform's client), the `logfire` SDK (a closed platform's open SDK, and a transitive
  dependency of Pydantic AI) and `latitude-telemetry` (one component of a self-hosted platform).
  Two shapes that look like exceptions follow from the same test: a package pulled in as a
  transitive dependency of a *different* product (`langsmith` via `langchain-core`) and one SDK
  spanning N products (`cohere-rerank-api` banded on the whole `cohere` package) both count
  something other than the product. A band predating this test is not re-banded by it; it is
  flagged for its own `update-product` pass. `langfuse` is the worked example: the
  `langfuse` client measures installs of the client, so the record bands on the vendor's own
  figures for the server instead and carries `reported_traction` at 4. Those figures are in the
  acquisition announcement the record already cited — pulls of the server image and a Fortune 500
  roster — which is the second thing this case shows: a record's own summary can say its source
  carries no usage figure while the source carries one.

A band exceeding the computed one is usually not a dispute about the measurement. The common
shape is a `usage_volume` record whose own note cites a figure matching the warehouse almost
exactly and then bands above where that figure falls — so the disagreement is between the score's
band and the score's own evidence, not between the score and the warehouse. Name instances by
running `uv run python -m build.adoption_reconciliation` rather than by quoting a list from here:
the notes get rewritten, and a product named here as an instance stops being one without this
sentence noticing.

## What the machine actually computes today

| stage | model | grain | covers |
|---|---|---|---|
| observe | `currentai.observations.product_adoption_current` | **artifact** | every declared artifact on a machine route, band-free |
| evaluate | `build/adoption_measurements.py` | **product** | the winning route per product, banded once |

Observation and evaluation are two stages on purpose: the raw figure is per artifact and the
band is per product, so a model that did both at once would band a product on whichever artifact
it happened to read. The evaluator reads the bands from `registry.adoption_bands` and bands on the
product's declared type. It writes no BAND back to `sources/`: **a computed band is an
observation, never a score.** Only a person sets `level`, and only per
`evidence-and-freshness.md`.

What a measurement may write is the axis's DATE. Where the route re-measures the band a person
recorded, `adoption.last_verified` takes the date of the observation behind that measurement;
where it measures a different band, the product is queued for a person rather than re-scored, and
its date does not move. `evidence-and-freshness.md`, under "How an adoption date is earned", owns
that rule and `build/adoption_freshness.py` implements it.

### Partial coverage abstains

A route can be observed and still not cover the product. Where the observations miss a declared
primary artifact of the winning route's kind, `build/adoption_measurements.py` withholds both the
band and the aggregate rather than publishing a sum it knows is short. This is the same rule as
the under-coverage remedy above, applied within a channel rather than across channels: abstain
rather than band on the part of the product that happens to be countable.

Zero observations is a different outcome — no measurement row at all, reconciled as `unmeasured`.
A partial one produces a row with a null level, reconciled as `abstained`, whose explanation says
the aggregate was withheld rather than blaming a missing ladder.

### Sum across the family, not per artifact

`signal_routing.yaml` declares `sum_across_artifacts: true` for adoption, because the map's
unit is the product family rather than a repo. Model artifacts routinely outnumber the products
that own them, so banding per artifact scores a product on a single SKU: `gemma` sums across its
SKUs and lands at 5, where its largest single SKU would not.

`product_adoption` does this; `package_downloads` does not yet need to (a routed product declares
one package), and the hole is latent there rather than closed.

### Route order, and taking the sum WITHIN the winning route

Route order follows the precedence declared in `sources/signal_routing.yaml` — PyPI, then
Hugging Face model, then Hugging Face dataset, then the unbridged npm and crates routes, with
GitHub stars and reported traction last as fallback; see "Authority is declared, not inferred"
above for why PyPI leads. First artifact the product has, on the winning route, wins. The sum is
taken within the winning kind, so a product shipping both a model and its training corpus is not
credited with the corpus twice.

## Products with no machine signal

A non-hardware product can record a substantive adoption level with no computed band behind it at
all. Those are not one problem, and each class has a different answer:

1. **It claims `usage_volume`.** Misfiled rather than unmeasured. If a band claims a download
   count then a countable artifact exists — declare it and the existing machinery bands it. If
   none exists, the instrument is wrong and the band should be `reported_traction`.
2. **It has a live `signal_github` row.** Stars are fetched weekly and banded nowhere. This is
   the cheapest coverage available and needs no key, subscription or bridge — see the open
   route below.
3. **It has no signal of any kind** — hosted APIs, closed models, `mistral-large`. For these
   the answer is *not* to invent a number.

### For the genuinely unmeasurable, make the claim decay

A `reported_traction` band should cite the vendor page carrying the figure, with a URL, an
`accessed` date and a `content_sha256`, exactly as every other axis does. It is then
re-checkable rather than machine-derived, and it ages against
the refresh window in `evidence-and-freshness.md` so an unconfirmed vendor claim decays visibly instead
of sitting unfalsifiable forever.

That is the same move `establishes` made for openness and `relative_to` made for capability:
it does not make the claim automatic, it makes it falsifiable.

## Signals considered and their traps

- **GitHub stars** — real, already fetched wherever a repo is declared, banded nowhere yet. Capped at
  level 3 by the rubric because stars measure attention rather than use. **Open route.**
- **Vendor SDK downloads** — `mistralai`, `anthropic`, `cohere` on PyPI are dated proxies for
  API integration, and the trap is attribution. The `cohere` package is the SDK for Cohere's
  entire API surface, so its downloads are not `cohere-rerank-api`'s: that product declares no
  package and bands on multi-cloud distribution instead. Undeclaring the artifact is
  what binds the judgment to routing, which reads declarations rather than prose.
  `not_primary_channel` is the wrong instrument for it — that field keeps an artifact whose
  measurement DOES belong to the product and drops it only from the banded sum, where this is a
  membership failure. **An SDK covering N products may not be attributed wholly to one** — the
  rule is in "When a re-read may re-band" above, along with the transitive-dependency case beside
  it.
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

`n8n` is the case the rule is written from. It records `usage_volume`, and its declared artifact
is the npm package at 393,738 downloads a month, which bands at level 3. But n8n is deployed
overwhelmingly as a self-hosted Docker container, and Docker Hub reports **246 million cumulative
pulls** — averaging about 2.9 million a month over the image's lifetime. Banding on npm alone
publishes a precise number for the wrong channel, and the tell is a note that says so in its own
second sentence and records the band anyway.

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

`langflow` is the same shape: PyPI alone gives level 2, PyPI plus the Docker
average gives about 166,000 a month and level 3. `semantic-kernel` is a third — its Python package
reaches level 4 on its own, and the .NET/NuGet channel is larger and uncounted, so its band is a
floor and its note says so.

The tell to look for when reviewing: **a note that describes the signal as understating the
product, followed by a band recorded on that signal anyway.**

### Saying so on the artifact: `not_primary_channel`

Remedies 1 to 3 are things a curator does to a `score` record. This one is a declaration on the
`product`, and it is what makes the machine agree with the judgment instead of quietly disagreeing
with it. An entry in an artifact block may carry `not_primary_channel` beside its `url`, and the
value is the reason:

```yaml
npm:
- url: https://www.npmjs.com/package/@hexabot-ai/widget
  not_primary_channel: The embeddable chat widget a site drops into a page, not the self-hosted
    platform the product is. ...
```

Presence is the exemption, the value says why, the same shape as `artifact_exceptions`. It says one
thing only: **this artifact is not a channel the product ships through, so its figure is left out of
the summed one.** It is not a denial that the artifact is the product's. That stronger claim is a
`product_membership` ruling in `sources/resolution_ledger.yaml` (`not_member_of`), which says the
measurement is not this product's at all; here it is the product's, and it stays published.

What it does and does not touch:

- **Out of the sum.** `build/adoption_measurements.py` leaves the artifact's figure out of the
  figure it bands, and out of the coverage test below with it — an artifact declared not to be a
  shipping channel is not a hole in the measurement.
- **In the table.** The artifact keeps its row in `registry.product_artifacts` (carrying the reason
  as a column), its observation stays in `observations.product_adoption_current`, and
  `currentai.signal_packages.downloads` still computes and publishes its downloads per artifact.
  Only the banded figure changes.
- **A kind with nothing left is not a channel.** Where every artifact of a kind carries the
  declaration, the product has no figure on that kind and falls through to its next route — remedy
  3, reached by declaration rather than by hand. `hexabot` (an embeddable widget, not the
  self-hosted platform) and `yomo` (a Rust SDK crate for a runtime shipped as a Go binary) are the
  two cases, and both land on stars at level 2. Banding them on the package instead puts both at
  level 1.

Declaring one is a curation judgment with the same test as the ruling above: what the package IS,
and whether installing it is a meaningful unit of use of the scored product. It is never a way to
drop a number that reads low.

### The gate: `build/check_channel_authority.py`

A ladder applied by habit is not applied evenly, and nothing in the corpus distinguishes a
product that took remedy 3 deliberately from one nobody reached. `helm`, `laminar` and `swe-bench`
each record `reported_traction` with `reach` omitted while their winning route is a bridged usage
channel; `laminar` records why its bridged figure cannot band it, which is the
measurement-population rule above rather than the ladder. The gate is what makes the ladder
answerable.

It reports two legs and re-bands nothing.

1. **The release line.** For every pypi-routed product, the newest release on the registry
   against the repository's newest release or tag. A registry at least one **stable major line**
   behind is a band read off a version nobody is on. Stable against stable: a pre-release repo
   tag is a beta ahead of the registry, which is ordinary publishing, and is listed as an
   exclusion. A repo tag that does not parse to a version is listed as undecidable, which is not
   the same as no lag.
2. **The note**, which is the tell above, imported from `build/sweep_status.py` rather than
   restated so the two cannot drift.

A finding leaves the report when the record stops resting on the channel: a `banded_quantity`
naming what the figure actually counts, or a relabel to `reported_traction` with `reach` null
and a digested source behind the level. Substituting the star count is not a remedy, and the
precedence rule exists to stop it.

**A relabel moves the instrument and nothing else.** "When a re-read may re-band" above already
says it — move it to `reported_traction`, drop the numeric `reach`, and *leave the level alone*
— and the temptation runs the other way every time, because the record now looks unjustified
without a number under it. `areal` and `xtuner` are the worked examples: both correct a
`usage_volume` claim made over a trailing release line, both keep level 1, and both say in the
note that raising the level would be a separate judgment needing its own standing evidence. The
only other signal either has is its star count, which is exactly what the gate's own remedy text
forbids substituting. A relabel that also raises the level is policy C arriving through the back
door, one product at a time.

**Why it reports rather than abstains.** Abstention moves no published number in the direction
anyone wants — `_stage_and_gaps` reads `L` off a count at ≥ 4.5 and `B` off a `max()`, and this
trigger only ever fires at the bottom of a distribution — while applied to the prose tell it
erases `gvisor`'s real adoption and demotes `deployment` from stage 5 to 4 on the strength of an
honest note. Understating remains the safer error; the remedy is to say what was counted, not to
stop counting.

**The narrowness is the point.** Leg 1 is the only mechanical form of "this channel is not how
the product ships", and it is undefined for a Hugging Face model or dataset, where the repo IS
the artifact. The ratio test it replaces — downloads an order below stars — was rejected for
handing stars a veto over a usage measurement, which is the overstatement failure re-entering
one level up. `qwenpaw` is the case that settles it: its PyPI release was uploaded the same day
as its repo tag, and only the ratio ever looked wrong.

Report-only, weekly on the Monday chain (`.github/workflows/channel-authority.yml`), because it
reads a live release line and a gate's cadence has to match the thing it polices.

## The third trap: the package that is not the product

Both traps above are about ATTRIBUTION - a real count of the product credited to the wrong
product, or a real count of the wrong channel credited to the right one. This one happens a step
earlier, at IDENTIFICATION, and it is the one a gate cannot catch.

> **A registry package sharing the product's name is not evidence that it is the product.** Before
> banding on it, establish that the package CONTAINS the product rather than talking to it.

A whole category can carry this: in `storage`, a large minority of products have a PyPI package
matching their name and in none of them is that package the product. Two shapes, and the second is
worse:

- **The client of a self-hostable server.** `elasticsearch` on PyPI is elasticsearch-py; the
  product is the Java engine at `elastic/elasticsearch`. `pgvector` on PyPI is pgvector-python; the
  product is a Postgres extension written in C. Same shape for `meilisearch`, `typesense`,
  `lakefs`, `infinity-sdk`, `aistore` and `vearch`. Each of those packages draws a real download
  count and none of those counts measures the server, so both products above band on stars
  instead — 77,824 and 22,664 in their recorded evidence.
- **A different project entirely.** `dolt` on PyPI is an unrelated REST wrapper by another author.
  `flash-attention` is a Huawei Ascend port, not `Dao-AILab/flash-attention`; the product declares
  `flash-attn` and bands on it. `juicefs` on PyPI is a third-party SDK published from another
  organization's repository, so JuiceFS declares it nowhere and bands on its 14,334 stars.

**`check_artifacts --live` does not catch the first shape, and cannot.** Its `pypi_repo_mismatch`
check compares the package's declared project URL against the product's repo, and a well-behaved
client library points at exactly that repo - elasticsearch-py names `elastic/elasticsearch`. The
gate is doing its job; the question it asks is not this one. That is why this rule lives here.

Three questions settle it, and all three are answerable from the package's own JSON:

1. **Does installing it give you the product, or a way to reach one?** A wheel for a Java engine, a
   C extension, or a Go binary is a client by construction.
2. **Who publishes it?** A package published from a different organization than the product's repo
   is somebody else's software until proven otherwise, whatever it is called.
3. **Does the magnitude make sense?** A server product whose package outdraws its stars by three
   orders of magnitude is being measured through its client. `juicefs` at 169 downloads against
   14,334 stars is the same tell inverted.

`build/check_package_channel.py` asks the same three questions of every `stars_fallback` record,
for each package or image the product's own README, or an install page it links to, installs, and only reports: identity (a URL
naming the declared `owner/repo` in full, never an owner-name match), role (quoted from the
package's own summary), and instrument quality (monthly or cumulative, from which window). It reads
the existing `adoption.note` first and surfaces a sentence that already names the package as a prior
judgment rather than a fresh finding. It fetches, so it is not in `validate.yml`; run it by hand
before an adoption sweep.

Where the package turns out to be a client, the server usually has no countable channel at all, so
the honest outcome is `stars_fallback` and its cap of 3 - understating a widely deployed system,
and saying so in the note. The categories holding self-hostable servers carry the highest
`stars_fallback` shares on the map for this reason - measured 2026-09-20, `dataset_processing_tools`
at 11 of 20, `scientific_ai_models` at 17 of 34 and `storage` at 20 of 41 - and that is a property
of those categories rather than a defect in them. Docker pull counts would fix most of them; there
is no `docker` artifact kind to declare, which is the platform-side ask.

## Checklist

- [ ] `level` is 1-5 and follows the band table for the product's **type**.
- [ ] `reach` carries the unit, and matches the band it claims.
- [ ] `signal_type` names the instrument actually used, not the one that sounds strongest.
- [ ] `stars_fallback` never exceeds level 3.
- [ ] A `usage_volume` band has a countable, **declared** artifact behind it.
- [ ] A same-named registry package was checked for being the product rather than its client or
      an unrelated project, per "The third trap" above. `check_artifacts` cannot ask this.
- [ ] The package the band was read from passes the measurement-population test: installing it
      is a unit of use of the scored product, not of a client or component whose population varies
      independently. A first-party client of a server or hosted platform fails it.
- [ ] A `reported_traction` record cites a source with a date and a digest, and records a word
      from the vocabulary or no `reach` at all — never a number.
- [ ] Anything read off something other than the product — a parent platform, a revenue or
      funding figure, a star count, a cumulative or lifetime total — records
      `banded_quantity` naming what was counted.
- [ ] An `active_users` band names the quantity it actually banded, if that quantity is not an
      active count (an all-time total, a device base, a paid-seat count).
- [ ] The band follows from the figure in the note, in the same direction and order of
      magnitude.
- [ ] No band was copied from a computed signal — those are observations, not scores.
- [ ] The registry release the band was read off is on the line the repository is publishing.
      `check_channel_authority --live` asks this; a band a whole major line behind needs the
      under-coverage ladder applied to it.

## Related

- `docs/reference/evidence-and-freshness.md` — how any axis earns `last_verified`, and the gates
- `docs/reference/evidence-and-freshness.md` — what `last_verified` means, and the refresh window
- `docs/reference/openness.md` — the openness ladders, the other scored axis
- `sources/rubrics/<type>.yaml` — where the bands are declared
- `sources/signal_routing.yaml` — which signal is authoritative for which dimension
- `docs/schemas/score.schema.json` — the field definitions and the `signal_type` enum
