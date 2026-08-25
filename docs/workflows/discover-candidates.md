# Discover candidates

## Use this when

A sweep of the outside world should turn into candidate rows the map can act on: new
products from GitHub, Hugging Face, package registries, papers, or launch venues.

**Sweep every source; emit only GitHub-backed candidates.** The tail registry requires a
`github` identifier on every row, so a candidate whose only handle is a Hugging Face repo, a
package name, a paper or a product page cannot be stored yet. Those are still worth
surveying — a HF release is often how you find a repo — but one that resolves to no
repository is parked in the batch summary, against issue #365, rather than emitted. Do not
work around this by inventing a plausible repo for a candidate that has none.

This is the step *before* the map changes. It decides what should exist. For a single
product you already know about use `add-product`; to turn a seeded roster into researched
head products use `promote-category`; to re-verify what is already published use
`refresh-category`.

## Inputs you need

- The categories to sweep. Read them at run time through
  `build.taxonomy.category_statuses()`, which returns `{slug: status}` for the whole
  taxonomy. **Never work from a remembered list** — the taxonomy grows, and a stale list
  silently drops every candidate belonging to a category added since. **Never parse
  `sources/taxonomy.yaml` yourself either:** a category entry is either a bare string or a
  `{name, status}` mapping, and code that assumed the scalar form is what broke
  `build_stack_map`. `category_statuses()` and `arc_categories()` own that normalization.
- A time window, so the sweep is reproducible and the next one knows where to start.
- Warehouse access for the discovery pool (`currentai.entities.repos`), if available. It is
  a dedup input, not a source of truth about what belongs on the map.

## Files this changes

| File | Change |
|---|---|
| `sources/registry/<category>.yaml` | Candidate rows appended to `products:`, one per accepted candidate |
| `sources/taxonomy.yaml` | Only if a candidate needs a category that does not exist — and then only as a `category-proposal` issue first, never edited here |

Nothing else. This workflow does not write `sources/products/`, `sources/scores/`, or any
category roster. A candidate becomes a product later, and **which workflow picks it up depends
on the category's status** — a distinction worth getting right, because the two are not
interchangeable:

| Category status | Who promotes the row | 
|---|---|
| `preliminary` | [`promote-category`](promote-category.md), for the whole seed roster at once |
| `published` | [`add-product`](add-product.md), one product at a time |

`promote-category` is *only* for preliminary categories, so a candidate swept into a published
one — which is every registry file today — is promoted through `add-product`. Either way the
registry row **comes out** in the promoting PR: a slug lives in exactly one tier, and leaving
the row behind fails `validate` as a duplicate.

## Procedure

### 1. Read the taxonomy, then the corpus

Load every category through `build.taxonomy.category_statuses()`, published and preliminary
alike. Then load the existing corpus:

- **current slugs** — the filename stems of `sources/products/*.yaml`;
- **retired slugs** — the `aliases:` list on each of those records. There is no
  `sources/slug_aliases.yaml`; the single alias mapping was deleted in #157 because two
  renames of the same retired slug silently kept whichever came last. Aliases now live on
  the record that replaced the slug, so the retired set is derived, not read from a file.

A candidate matching either set is already mapped and is not a candidate.

### 2. Sweep

Sweep the sources appropriate to the categories in scope. Record, for every raw signal, the
URL it came from and the date you fetched it. A candidate you cannot link to is not a
candidate — see the emit contract below.

### 3. Dedup, in this order

1. Against current product slugs.
2. Against the retired slugs derived in step 1 — the union of every `aliases:` entry across
   `sources/products/*.yaml`. A retired slug means the thing was deliberately consolidated or
   dropped, and re-adding it re-opens a settled decision. `amazon-nova-pro` is the shape to
   watch for: a SKU that was folded into `amazon-nova` and reads like a new product.
3. Against the warehouse discovery pool, if reachable.
4. Against itself: the same tool arriving from GitHub, PyPI and Hugging Face is one
   candidate, not three.

Entity resolution is the part that goes wrong. Where two signals might be the same product
and you cannot tell, park both with the ambiguity stated rather than guessing.

### 4. Assign exactly one category

One product, one category, in every tier. It is what keeps the gap arithmetic sane.

If a candidate fits no existing category, it does not get a new one here. Open a
`category-proposal` issue on GitHub and park the candidate against it. Taxonomy changes are
a governance event, not a data event.

### 5. Emit rows, not prose

Each accepted candidate becomes a row in `sources/registry/<category>.yaml` satisfying
`docs/schemas/registry.schema.json`: `slug`, `display_name`, `type`, `org` and `github` are
required, with `pypi`, `npm`, `huggingface_model`, `huggingface_dataset` and `homepage` where
they apply. The row rejects any other key (`additionalProperties: false`).

**Artifacts are canonical identifiers, not URLs.** This is the single easiest way to produce a
sweep that has to be redone, because a URL looks obviously right and fails two ways at once —
the schema rejects it, and `build/serialize_registry.py` builds the public URL *from* the
identifier, so a stored URL would serialize to `https://github.com/https://github.com/owner/repo`.

| Field | Write | Not |
|---|---|---|
| `github` | `owner/repo` | `https://github.com/owner/repo` |
| `huggingface_model` | `owner/name` | `https://huggingface.co/owner/name` |
| `huggingface_dataset` | `owner/name` | `https://huggingface.co/datasets/owner/name` |
| `pypi` | `package-name` | `https://pypi.org/project/package-name/` |
| `npm` | `package-name` | `https://www.npmjs.com/package/package-name` |
| `homepage` | a full URL | — the one field that *is* a URL |

Head product records are the opposite convention — `sources/products/<slug>.yaml` stores typed
arrays of `{url: ...}` — so do not carry a habit from `add-product` into a registry row, or
back the other way.

**The source URLs still matter, they just live elsewhere.** Every raw signal's URL and fetch
date belong in the batch summary, which is what makes the sweep auditable and lets the next
step verify a claim without re-running the lookup. A sweep that reports names and star counts
and keeps neither the identifiers nor the source URLs has produced nothing the repo can use.

### 6. Park what you did not accept, with its reason

Anything surveyed and not accepted is recorded **in the batch summary** with the reason:
already mapped, a retired alias, a new SKU of an existing product, superseded, unmaintained,
no public artifact, GitHub-backed storage not yet available (#365), or a boundary rejection. A
reject that leaves no trace comes back next week and is triaged again from scratch.

Parked candidates do not go in `products:`. A registry row has no `notes` field and rejects
unknown keys, so there is nowhere on a row to write a reason — and a parked candidate is not a
candidate row in the first place.

### 7. Reconcile the counts

Surveyed, deduped, accepted, parked. They must add up. Publishing counts that do not
reconcile means nobody can tell whether candidates were dropped silently.

## Rules that hold throughout

**Do not invent a scoring or legitimacy rule mid-sweep.** If a signal looks implausible — an
implausible star count, a suspicious growth curve — park the candidate and say why in the
batch summary, with the number that bothered you. A threshold that exists only in one run's
output cannot be reproduced, reviewed or appealed, and it blocks real products against a
standard nobody agreed to. New rules belong in a rubric or a reference doc, proposed
separately.

**A rate limit is not a finding.** HTTP 429, 403 and 5xx mean "not now", not "not here"
(`build/fetch_source.py` treats them as transient for exactly this reason). Retry, use a
token, or leave the field absent and say the fetch did not complete. Never record
"cannot determine" as though it were a measured absence.

**This step never scores.** Candidate rows carry identity and artifacts. Openness, adoption
and capability are earned later against evidence, under `add-product` or `promote-category`.
Preliminary scoring here would be a number with no source behind it.

**No bot PRs.** The sweep ends at populated registry files and a summary for a human to
approve. Opening PRs per candidate is not part of this workflow.

## Validation

```bash
uv run python -m build.validate          # schema + roster integrity; must print 0 error(s)
uv run pytest tests/ -q                  # full suite
```

`build.validate` catches a malformed registry row (including a URL where an identifier
belongs), a candidate assigned to a category that does not exist, a slug that collides with a
live product, a retired alias or another registry file, and a GitHub artifact already claimed
by a head or tail product.

Two limits worth knowing, so the gate is not trusted past its reach. Artifact-level dedup is
keyed on `github` only: two rows carrying the same `pypi` or `huggingface_model` and different
repos both pass, so the self-dedup in step 3 is yours to get right (#365). And validation
cannot tell a genuinely new product from one you failed to recognize — it checks identity
collisions, not judgment.

## Expected PR contents

- One or more `sources/registry/<category>.yaml` files with new rows.
- A PR body listing: the window swept, the sources swept, the reconciled counts, the source
  URL and fetch date behind each accepted candidate, and the parked candidates with their
  reasons.
- No product, score, or category-roster files.

## Stop and escalate when

- A candidate fits no category, or sits on a boundary between two. Open a
  `category-proposal` issue; do not stretch a category to fit.
- Two signals may be the same product and the evidence does not settle it.
- A source blocks the sweep (rate limits that survive retry, an API that has changed).
  Report the gap rather than filling it with a guess.
- The sweep volume is large enough that nobody can review it. Tighten the signal floor
  before relaxing the human-in-the-loop rule.

## Relevant reference material

- `docs/schemas/registry.schema.json` — the row contract, including which fields are
  identifiers and which is a URL
- `docs/reference/identity.md` — why a retired slug stays retired, and why aliases live on
  records rather than in one mapping
- `docs/workflows/add-product.md` — what happens to a row in a **published** category
- `docs/workflows/promote-category.md` — what happens to a whole roster in a **preliminary**
  category
- `docs/reference/evidence-and-freshness.md` — why a fetched claim carries a URL and a date
