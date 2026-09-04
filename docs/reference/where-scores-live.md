# Where each axis lives, in the repo and in the warehouse

Written 2026-08-19 from a sweep of every dataset in the `currentai` org: **22 datasets, 95
tables**, every column name matched against `adopt|capab|combined_score|maturity|overall|score`.

The short answer, and the distinction that gets missed: **`sources/` is the source of truth for
all three axes, and `currentai.registry.product_scores` is a complete current mirror of it** —
every product, every axis, one row. What only openness has is a *recomputation*: the warehouse
walks the ladder itself and `check_parity` fails if the two disagree. Adoption and capability are
mirrored, not recomputed, so nothing in the warehouse can contradict them. Everything else that
looks like a score is frozen, external, or keyed to something other than a gap-map product.

Recorded, mirrored, recomputed and measured are four different things here, and a query is only
as good as knowing which one it hit.

Two more `registry` tables carry no axis at all and are easy to mistake for one because they sit
next to `product_scores`: `currentai.registry.resolution_ledger` (the identity rulings a discovery
sweep has already made, one row per artifact and relation) and `currentai.registry.product_aliases`
(retired slug → live slug, published products only). Both are identity bookkeeping, not
measurements — see `build/serialize_registry.py`.

## The one table — `currentai.registry.product_scores`

522 rows, one per product per category, all three axes with their own confidence and
`last_verified`, plus the derived `overall_score`, `maturity`, `is_mature` and `score_tier`.
Published by `build/serialize_scores.py` on every push to `main` touching `sources/**`.

Two properties to know before querying it:

- **It transcribes the payload; it derives nothing.** The blend comes out of
  `serialize._maturity_score` against the category's weights, and there is exactly one
  implementation of it. So these numbers are the numbers the front end shows.
- **Published-map products only.** `build_payload` excludes preliminary categories by design, so
  a preliminary category's products are absent from this table even though
  `currentai.registry.categories` would carry the category itself. All 18 categories are
  published today, which is why the count is 522 and not a subset.

Coverage: openness on all 522 rows, adoption on 502, capability on 496. An unmeasured axis is
NULL rather than absent, so "not measured" and "no such column" cannot be confused.

`adoption_signal_type` travels with `adoption_level` deliberately: a stars band and a downloads
band are different scales, so a query that ranks across `signal_type` is wrong.

## The Neon serving layer — the `os-ai-map` schema

The front end reads products, scores and freshness dates from Postgres rather than from the
warehouse, because a page render cannot wait on a Trino query. `build/publish_neon.py` loads
the `os-ai-map` schema on every push to `main` that triggers `registry.yml`, one step after the
OSO publish. This is what deprecates `build/notebook_data.json` as the site's transport; the
file itself stays the repo's build artifact and its gate contract, and is the *input* to the
load.

The instance is shared. `drizzle`, `payload` and `public` belong to other parts of the site;
`os-ai-map` is the gap map's, and the publisher touches only it and its own
`os-ai-map_staging`. It refuses to run against any of the other three.

**Two groups of table, one schema.**

*The map* — the target model from CLEVER FRANKE, with Carl's amendments: `products`,
`organizations`, `categories`, `layers`, `stages`, `gaps`, `gaps_categories`, `openness`,
`adoption`, `capability`, `sources`, `product_lineage`, `aliases`, `long_tail_top`,
`long_tail_counts`, and the three `gallery*` tables. Every row is derived from
`build/notebook_data.json`, so what Postgres serves is what the repo published.

*The registry*, prefixed `registry_` — the same tables `publish_registry` publishes to OSO,
derived from that module rather than from a directory listing, so the two surfaces carry the
same registry by construction. The prefix exists because both groups have a `products`, a
`categories` and an `organizations`.

Plus `publish_runs`: one row per load, carrying `run_id`, `published_at`, `schema_version`,
`built_at`, `released_at`, `source_git_sha`, `declaration_version_id`, `table_count` and a
`row_counts` JSONB. That row is how you tell which commit and which shape the serving layer is
showing.

**Keys are natural where the payload has one.** `products.id` exists for the FK shape the
designers specified, but it is assigned by sorted slug on every load, so the same corpus gives
the same ids and a diff of two loads is readable. The real key is `slug`. Organizations key on
`slug`, aliases on `alias`, and `categories` carries a `slug` alongside its id — the PDF omitted
it, and every deep link and every join from the registry group needs it.

**The eight enums are enforced.** `alias_kind`, `freshness_basis`, `lineage_relation`,
`capability_relation`, `metric_name`, `health_status`, `integration_type`, `gap_type` are
created in the schema, and a payload value with no mapping fails the load naming the value
rather than being coerced to something adjacent. One mapping is lossy and worth knowing:
`capability.relation` in the payload is a signed distance (`at`, `one_above`, `one_below`,
`two_below`) and the enum has none, so `one_below` and `two_below` both arrive as `tier_below`.
The exact distance is only in `capability.notes`.

### The three dates, which are three different questions

| Where | Column | Question it answers |
|---|---|---|
| `publish_runs` | `built_at` | When was this data built? The payload's `generated`. |
| `publish_runs` | `released_at` | When was the release cut? The payload's `released`, which `build/serialize.py::release_date` reads from `CHANGELOG.md`. |
| `products` | `freshness_date`, `freshness_basis` | When was this product's score last confirmed, and how — `verified` by a human, or `commit` as the fallback to the score file's last commit. |
| `openness`, `adoption`, `capability` | `last_verified` | The same question asked of one axis. |

`docs/reference/evidence-and-freshness.md` is normative for what a freshness date means and how it is
derived. Do not read `built_at` as a freshness date: it says when the build ran, not when
anything was checked.

### What is not there

**The warehouse recomputation.** `scores.openness_facts` and `scores.openness_computed` stay
on OSO, and no table in `os-ai-map` recomputes an axis. A question about what the map *says* is
answerable here; whether the warehouse *agrees* is `check_parity` against the tables above.

**Gallery content.** `gallery`, `gallery_products` and `gallery_gaps` are created and left
empty. Gallery entries are authored CMS-side, in the `payload` schema, not derived from the
map's data — the tables exist so the site's queries compile before that content lands.

### The load is atomic, and the swap is the migration path

Rows go into `os-ai-map_staging`, dropped and recreated each run, and the cutover is
`os-ai-map` → `os-ai-map_previous`, `os-ai-map_staging` → `os-ai-map`, drop
`os-ai-map_previous`, all three renames in one transaction. A reader sees the whole old schema
or the whole new one, never a table that has loaded next to one that has not. Grants are
applied to the staging schema before the swap, since a rename carries privileges with it;
`NEON_READ_ROLE` names the role granted `SELECT`, and unset means `PUBLIC`.

There is no migration tool, and for now there does not need to be one: every publish rebuilds
the schema from `build/neon_schema.py`, so a shape change is live on the next load with no
ALTER anywhere. What that costs is a reader's ability to tell which shape it has, which is why
`publish_runs.schema_version` exists — bump `SCHEMA_VERSION` in the same commit as any change
to a table, column or enum. Once something outside this repo depends on the shape, that is the
point where a real migration path replaces the swap.

Column types for the map group are declared in `build/neon_schema.py`, next to the grain they
describe. The registry group's are inferred from the data, because the serializers declare
column names and not types: TEXT unless every non-empty value in the column parses as BOOLEAN,
INTEGER, DOUBLE PRECISION or DATE, and identity columns (`slug`, anything ending `_slug` or
`_id`) pinned to TEXT whatever they look like. A digits-only artifact id is a string with
digits in it. An empty CSV field loads as NULL on both groups, so "absent" and "empty" are the
same value.

## Openness — computed and gated

| Where | What | Currency |
|---|---|---|
| `sources/scores/*.yaml` | The recorded score, class, components and sources | current |
| `currentai.registry.product_openness_evidence` | Dimension values, per product and category | republished on every push to `main` |
| `currentai.scores.openness_facts` | One resolved fact per declared dimension | Monday 03:00 UTC (`evidence`) then 04:00 (`scores`) |
| `currentai.scores.openness_computed` | The score and class the ladder produces | same |

`build/check_parity.py` compares the repo against `openness_computed` per product and fails on
any divergence. This is the only axis with a warehouse recomputation to disagree with, which is
why it is the only axis parity can grade.

## Adoption — curated in the repo, measured in three signal tables

The **score** is curated in `sources/scores/*.yaml` as `adoption.level`, and mirrored into
`registry.product_scores`. Nothing recomputes it.

What the warehouse does hold is a **measured band per product**, from whichever channel the
product declares:

| Table | Instrument | Products | Agrees with the repo |
|---|---|---|---|
| `currentai.signal_huggingface.product_adoption` | 30-day Hub downloads | 115 | **96%** (111/115) |
| `currentai.signal_pypi.package_downloads` | monthly PyPI downloads | 106 | **91%** (97/106) |
| `currentai.signal_github.product_adoption` | stars, a declared **fallback** | 120 | **50%** (60/120) |

Read those three rates together and they say something specific rather than alarming. Where a
product publishes a download channel, the repo and the warehouse agree. Where adoption rests on
stars, they part company — and in 56 of the 60 disagreements the repo bands **higher**, by one
level 28 times, two levels 21 times, and three or more 7 times.

That is the fallback behaving like a fallback: stars are a weaker proxy than downloads and land
lower on their own scale, and `docs/reference/adoption.md` is explicit that a band is only comparable
within its `signal_type`. So it is not 60 errors. It is 56 products whose adoption rests on the
weakest instrument the map has, banded above what that instrument alone would support, with no
gate over any of it. Worth a pass, not a correction sweep.

**The 50 products promoted on 2026-08-19 have no signal rows yet.** The signal crons are Sunday,
so the earliest is 2026-08-23.

## Capability — mirrored, never recomputed

`sources/scores/*.yaml`, `capability.score`, mirrored into `registry.product_scores`.
**No warehouse table recomputes capability for a gap-map product**, so there is nothing for a
parity gate to compare and no independent check on the value. Corroborating instruments exist and are deliberately left unjoined —
`signal_lmarena` (Elo), `signal_artificialanalysis` (benchmarks), `signal_semanticscholar`
(citations) — see `docs/reference/capability.md` on why a peer comparison is recorded rather than
derived.

## Frozen and lookalike tables — do not read these as current

Four things carry columns named like ours and answer a different question.

| Table | What it really is | State |
|---|---|---|
| `currentai.stack_map.product_scores` | The **v1 hand-scored upload**: `adoption_level`, `capability_score`, `capability_value`, `combined_score` per product | **Frozen.** 282 products, 11 categories, newest `last_verified` 2026-05-29, keyed on `product_name` rather than slug. **No deployed model reads it.** |
| `currentai.catalog.stack_map` | The repo→warehouse taxonomy bridge, carrying `adoption`, `capability`, `maturity` per product | **Externalized and frozen (ADR-003).** Out of the Gap Map's data system; removed from this repo's inventory and its producer archived, frozen under platform ownership at its last publish. Its former reader `scores.stack_contributors` was externalized with it. Not a repo-maintained table. |
| `currentai.catalog.osai_gap_map` | The **external** OSAI gap map: `ease_of_adoption`, `maturity`, `overall_score` | A different organisation's taxonomy and scale. Not our products, not our axes. |
| `currentai.ai_demand_curve.*` | `capability_score`, `adoption_level` against **OpenRouter/LMArena models** | Keyed to model names from a leaderboard, not to gap-map product slugs. |

`currentai.stack_map.category_scores` and `.gap` are the same v1 freeze at category grain.

## How to answer "is this axis in the warehouse" without guessing

```sql
-- openness, current and gated
SELECT product_slug, openness_score, openness_class, last_checked
FROM currentai.scores.openness_computed WHERE category_slug = 'compilers';

-- adoption, measured where a channel exists
SELECT product_slug, adoption_level FROM currentai.signal_huggingface.product_adoption;

-- all three axes at once, mirrored from the repo
SELECT product_slug, openness_score, adoption_level, capability_score, overall_score
FROM currentai.registry.product_scores WHERE category_slug = 'compilers';
```

If a table has `adoption` or `capability` in a column name, check the table against the four
lookalikes above before quoting it. Two of them are frozen at May and one belongs to another
organisation.
