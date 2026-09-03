# Discover candidates

## Use this when

A sweep of the outside world should turn into candidate rows the map can act on: new
products from GitHub, Hugging Face, package registries, papers, or launch venues.

**Sweep every source; emit any candidate with at least one addressable artifact.** The tail
registry requires one of `github`, `huggingface_model`, `huggingface_dataset`, `pypi`, `npm`,
`crates`, `arxiv` or `homepage` on every row (#365) — not `github` specifically, so a candidate
whose only handle is a Hugging Face repo, a package name, or a paper can now be stored. A
candidate that resolves to none of these — no repo, no package, no Hub entry, no paper, no
homepage — is still parked in the batch summary rather than emitted; do not work around that by
inventing a plausible artifact for a candidate that has none. Hardware remains a case to think
about: `homepage` satisfies the schema, but it carries no adoption signal, so treat a
hardware-only candidate as weaker evidence than any other artifact kind.

This is the step *before* the map changes. It decides what should exist. For a single
product you already know about use `add-product`; to turn a seeded roster into researched
head products use `promote-category`; to re-verify what is already published use
`refresh-category`.

## Inputs you need

- The categories to sweep. Read them at run time through
  `build.taxonomy.category_statuses(taxonomy)`, which takes the loaded taxonomy mapping and
  returns `{slug: status}` for the whole taxonomy. Load the mapping first, exactly as the
  build code does:

  ```python
  import yaml
  from pathlib import Path
  from build.taxonomy import category_statuses

  taxonomy = yaml.safe_load(Path("sources/taxonomy.yaml").read_text()) or {}
  statuses = category_statuses(taxonomy)   # {slug: "published" | "preliminary"}
  ```

  `category_statuses()` is not a zero-argument call — passing nothing raises `TypeError`.
  **Never work from a remembered list** — the taxonomy grows, and a stale list silently drops
  every candidate belonging to a category added since. **Never parse `sources/taxonomy.yaml`
  yourself either:** a category entry is either a bare string or a `{name, status}` mapping,
  and code that assumed the scalar form is what broke `build_stack_map`. `category_statuses()`
  and `arc_categories()` own that normalization.
- A time window, so the sweep is reproducible and the next one knows where to start.
- Warehouse access for the discovery pool (`currentai.entities.repos`), if available. This is
  the long-tail *discovery* set, not the accepted Gap Map: a repository appearing there may be
  exactly what this workflow should emit. Use it to consolidate multiple signals into one
  entity, recover a canonical repository identity, and enrich a candidate — **presence in the
  pool never disqualifies a candidate.** A repository is only ruled out when it resolves to an
  existing head product or an existing registry row (see the dedup order below).

## Files this changes

| File | Change |
|---|---|
| `sources/registry/<category>.yaml` | One accepted candidate per row under `products:` — appended to an existing file, or a new file created for a category that has none yet (see step 5) |

Nothing else. A candidate that needs a category which does not exist is a governance event,
not a data event: open a `category-proposal` issue and park the candidate against it (see
**Stop and escalate**). This workflow never edits `sources/taxonomy.yaml`.

This workflow does not write `sources/products/`, `sources/scores/`, or any
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

Load every category through `build.taxonomy.category_statuses(taxonomy)`, published and
preliminary alike. Then load the existing corpus:

- **current slugs** — the filename stems of `sources/products/*.yaml`;
- **retired slugs** — the `aliases:` list on each of those records. There is no
  `sources/slug_aliases.yaml`; the single alias mapping was deleted in #157 because two
  renames of the same retired slug silently kept whichever came last. Aliases now live on
  the record that replaced the slug, so the retired set is derived, not read from a file.
- **existing registry slugs and artifacts** — the `slug` and every declared artifact (`github`,
  `huggingface_model`, `huggingface_dataset`, `pypi`, `npm`, `crates`, `arxiv`) of every row
  already in `sources/registry/*.yaml`. These are candidates a previous sweep already found;
  without this set a repeated sweep rediscovers and re-triages them every time, only failing at
  final `validate` if a slug or artifact collides. Loading them here is what makes a sweep
  incremental rather than a full re-triage.

A candidate matching any of these sets is already known and is not a new candidate.

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
3. Against the existing registry rows loaded in step 1 — every `slug` and every declared
   artifact already in `sources/registry/*.yaml`. A match here is a candidate a previous sweep
   already emitted; drop it and, if the earlier decision was to park it, do not re-triage it.
   This set is deduped *before* the warehouse pool because a match here is a settled outcome,
   while a match in the pool is only a signal.
4. Against the warehouse discovery pool, if reachable. This step is enrichment and
   consolidation, **not rejection**: use the pool to fold several signals into one entity,
   recover the canonical `owner/repo`, and fill in artifacts. A repository being present in the
   pool does not disqualify it — the pool *is* the long-tail set this workflow harvests from.
   Only rule a candidate out here when the pool resolves it to a slug or repository already
   caught by dedup sets 1–3.
5. Against the resolution ledger (`sources/resolution_ledger.yaml`) - a candidate any relation
   has already ruled on is not new. A `product_equivalence` ruling in `NOT_A_NEW_PRODUCT`
   (`existing_product`, `sku_of`, `excluded_boundary`, `excluded_maintenance`) drops the
   candidate outright; `unresolved` holds it for a person rather than proposing it again. A
   `product_membership` ruling (`member_of`, `not_member_of`) is a separate question about
   measurement, not identity, and does not by itself dedup a candidate. See
   `docs/reference/identity.md#rulings-are-typed-by-relation`.
6. Against itself: the same tool arriving from GitHub, PyPI and Hugging Face is one
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
`docs/schemas/registry.schema.json`: `slug`, `display_name`, `type` and `org` are required, plus
at least one of `github`, `huggingface_model`, `huggingface_dataset`, `pypi`, `npm`, `crates`,
`arxiv` or `homepage` (#365) — not `github` specifically. Write every artifact you have evidence
for, not just one; the row rejects any other key (`additionalProperties: false`).

A paper alone is weaker evidence of a *product* than a repo, a package, or a Hub entry: an
`arxiv`-only row is a legitimate candidate but carries no adoption signal and no code to
inspect, so treat it as a lower-confidence emit and say so in the batch summary rather than
promoting it with the same confidence as a repo-backed row.

**When the category has no registry file yet, create it.** Only `compilers` and `storage` have
registry files today, so a sweep over any other category is creating the file, not appending to
one. The file is a mapping with a `category` key naming the category slug and a `products:`
list of rows:

```yaml
category: <category_slug>
products:
  - slug: <kebab-case-slug>
    display_name: <Display Name>
    type: software
    org: <org-slug>
    github: owner/repo
```

Append to `products:` only when the file already exists; do not load-modify-dump an existing
file, since that reformats rows a human authored. For a new file, write the two-key mapping
above.

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
| `crates` | `crate-name` | `https://crates.io/crates/crate-name` |
| `arxiv` | `2401.12345` | `https://arxiv.org/abs/2401.12345` |
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
already mapped, a retired alias, a new SKU of an existing product, superseded, unmaintained, no
addressable artifact at all, or a boundary rejection.
Record the source URL and fetch date for a parked candidate too, not only for an accepted one:
the sweep earlier promised provenance for *every* raw signal, and a parked candidate with no
source URL cannot be re-checked next week — it just comes back and is triaged again from
scratch.

Parked candidates do not go in `products:`. A registry row has no `notes` field and rejects
unknown keys, so there is nowhere on a row to write a reason — and a parked candidate is not a
candidate row in the first place.

### 7. Reconcile the counts

The counts must satisfy two invariants, stated as equations so the reconciliation is
executable rather than a slogan:

```
raw_signals       = duplicate_signals + unique_candidates
unique_candidates = accepted          + parked
```

Every raw signal is either a duplicate (caught by one of the dedup sets in step 3) or a unique
candidate; every unique candidate is either accepted (emitted as a row) or parked (recorded in
the summary with its reason). Publish all five numbers. If either equation does not balance,
some signal was dropped without a trace — find it before opening the PR.

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
belongs, or a row with no addressable artifact at all), a candidate assigned to a category that
does not exist, a slug that collides with a live product, a retired alias or another registry
file, and any of `github`, `huggingface_model`, `huggingface_dataset`, `pypi`, `npm`, `crates`
or `arxiv` already claimed by a head or tail product — dedup runs per artifact kind, so a
package-only or HF-only candidate is checked exactly as a GitHub-backed one is (#365).

One limit worth knowing, so the gate is not trusted past its reach: validation cannot tell a
genuinely new product from one you failed to recognize — it checks identity collisions, not
judgment. `homepage` is not part of that dedup — it is addressable (satisfies the "at least one
artifact" rule) but carries no identity-bearing signal, so two rows sharing a homepage still
pass; catching that is on the self-dedup in step 3.

## Expected PR contents

- One or more `sources/registry/<category>.yaml` files with new rows — appended to existing
  files, or created for a category that had none.
- A PR body listing: the window swept, the sources swept, the five reconciled counts
  (`raw_signals`, `duplicate_signals`, `unique_candidates`, `accepted`, `parked`), the source
  URL and fetch date behind each accepted candidate, and the parked candidates each with their
  reason and their own source URL and fetch date.
- No product, score, or category-roster files.

## Stop and escalate when

- A candidate fits no category, or sits on a boundary between two. Open a
  `category-proposal` issue; do not stretch a category to fit.
- Two signals may be the same product and the evidence does not settle it.
- A source blocks the sweep (rate limits that survive retry, an API that has changed).
  Report the gap rather than filling it with a guess.
- The sweep volume is large enough that nobody can review it. The fix is a **disclosed,
  predeclared retrieval cutoff** — how far down a ranked source you swept (top-N by stars, a
  minimum release date) — not a legitimacy rule. This is not the mid-sweep threshold the rules
  above prohibit: that one adjudicates whether a *discovered* product is real; a retrieval
  cutoff only bounds *how much* you retrieved. Keep the two apart: pause and define the cutoff
  before you rerun, report the resulting coverage limitation in the summary, and never use the
  cutoff to reject a product the sweep already surfaced — an already-discovered candidate below
  the cutoff is parked with its reason, not dropped.

## The weekly identity digest and parked items

A sweep is not the only source of identity candidates: the identity graph (`currentai.identity.*`)
also proposes membership, equivalence, and org edges against artifacts already in the pool, and a
low-confidence one needs a human look the same way a parked sweep candidate does. Every Monday,
`identity-digest.yml` renders `currentai.identity.digest` into one GitHub issue titled `identity
digest: <week>`, capped at 25 active items and grouped equivalence, then membership, then org, then
artifact identity. Each item carries a pre-filled `resolution_ledger.yaml` entry Carl can edit and
paste in once he has decided — see `build/identity_digest.py`.

An item whose only evidence is a folded name match is `parked`, not shown as a reviewable item —
it comes back only once its evidence changes (a new backlink, a new artifact) or once it has sat
unreviewed for eight weeks, at which point it `resurfaces` and carries the reason. This mirrors the
sweep's own parking discipline above: a weak signal is recorded and revisited, not repeated at full
weight every week. An item ranked below the weekly cap is not dropped either — it stays in the pool
and is counted, not reviewed, until it ranks back in.

## Relevant reference material

- `docs/schemas/registry.schema.json` — the row contract, including which fields are
  identifiers and which is a URL
- `docs/reference/identity.md` — why a retired slug stays retired, and why aliases live on
  records rather than in one mapping
- `docs/workflows/add-product.md` — what happens to a row in a **published** category
- `docs/workflows/promote-category.md` — what happens to a whole roster in a **preliminary**
  category
- `docs/reference/evidence-and-freshness.md` — why a fetched claim carries a URL and a date
