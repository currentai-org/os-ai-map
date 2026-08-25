# Discover candidates

## Use this when

A sweep of the outside world should turn into candidate rows the map can act on: new
products from GitHub, Hugging Face, package registries, papers, or launch venues.

This is the step *before* the map changes. It decides what should exist. For a single
product you already know about use `add-product`; to turn a seeded roster into researched
head products use `promote-category`; to re-verify what is already published use
`refresh-category`.

## Inputs you need

- The categories to sweep. Read them from `sources/taxonomy.yaml` at run time. **Never work
  from a remembered list** — the taxonomy grows, and a stale list silently drops every
  candidate belonging to a category added since.
- A time window, so the sweep is reproducible and the next one knows where to start.
- Warehouse access for the discovery pool (`currentai.entities.repos`), if available. It is
  a dedup input, not a source of truth about what belongs on the map.

## Files this changes

| File | Change |
|---|---|
| `sources/registry/<category>.yaml` | Candidate rows appended to `products:`, one per accepted candidate |
| `sources/taxonomy.yaml` | Only if a candidate needs a category that does not exist — and then only as a `category-proposal` issue first, never edited here |

Nothing else. This workflow does not write `sources/products/`, `sources/scores/`, or any
category roster. A candidate becomes a product through `promote-category` or `add-product`,
both of which start from what this step leaves behind.

## Procedure

### 1. Read the taxonomy, then the corpus

Load every category from `sources/taxonomy.yaml`, published and preliminary alike. Load the
existing corpus: `sources/products/*.yaml` for current slugs, and `sources/slug_aliases.yaml`
for retired ones. A candidate matching either is already mapped and is not a candidate.

### 2. Sweep

Sweep the sources appropriate to the categories in scope. Record, for every raw signal, the
URL it came from and the date you fetched it. A candidate you cannot link to is not a
candidate — see the emit contract below.

### 3. Dedup, in this order

1. Against current product slugs.
2. Against `sources/slug_aliases.yaml` — a retired slug means the thing was deliberately
   consolidated or dropped, and re-adding it re-opens a settled decision.
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
required, with `pypi`, `npm`, `huggingface_model`, `huggingface_dataset` and `homepage`
where they apply.

**The artifact URLs are the point of this step.** A report of names and star counts cannot
become a registry row without redoing every lookup, so a sweep that omits them has produced
nothing the repo can use.

### 6. Park what you did not accept, with its reason

Anything surveyed and not accepted is recorded with the reason: already mapped, a new SKU of
an existing product, superseded, unmaintained, no public artifact, or a boundary rejection.
A reject that leaves no trace comes back next week and is triaged again from scratch.

### 7. Reconcile the counts

Surveyed, deduped, accepted, parked. They must add up. Publishing counts that do not
reconcile means nobody can tell whether candidates were dropped silently.

## Rules that hold throughout

**Do not invent a scoring or legitimacy rule mid-sweep.** If a signal looks implausible —
an implausible star count, a suspicious growth curve — say so on the row and park it. A
threshold that exists only in one run's output cannot be reproduced, reviewed or appealed,
and it blocks real products against a standard nobody agreed to. New rules belong in a
rubric or a reference doc, proposed separately.

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

`build.validate` is what catches a malformed registry row, a candidate assigned to a
category that does not exist, and a slug that collides with a live product or a retired
alias.

## Expected PR contents

- One or more `sources/registry/<category>.yaml` files with new rows.
- A PR body listing: the window swept, the sources swept, the reconciled counts, and the
  parked candidates with their reasons.
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

- `docs/schemas/registry.schema.json` — the row contract
- `docs/workflows/promote-category.md` — what happens to these rows next
- `docs/workflows/add-product.md` — the record each promoted row becomes
- `docs/reference/evidence-and-freshness.md` — why a fetched claim carries a URL and a date
