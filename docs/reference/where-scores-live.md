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

## The Neon serving layer — `gapmap`

The front end reads the declarations from Postgres rather than from the warehouse, because a
page render cannot wait on a Trino query. `build/publish_neon.py` loads every CSV the
serializers have written into `build/registry/` as a table in the `gapmap` schema, on every push
to `main` that triggers `registry.yml` — the same trigger and the same job as the OSO publish,
one step after it.

What is there: the registry tables. `products`, `organizations`, `categories`,
`product_artifacts`, `product_categories`, `product_organizations`, `product_lineage`,
`tail_products`, `resolution_ledger`, `product_aliases`, `org_handles`, `model_families`, plus
`publish_runs` — one row per load, carrying `run_id`, `published_at`, `source_git_sha`,
`declaration_version_id`, `table_count` and a `row_counts` JSONB of the per-table counts. That
row is how you tell which commit the serving layer is showing.

What is not there: **the warehouse recomputation**. `scores.openness_facts` and
`scores.openness_computed` stay on OSO, and nothing in `gapmap` recomputes an axis. So a
question about what the map *says* is answerable here, and a question about whether the
warehouse *agrees* is not — that is `check_parity` against the tables above.

The load is atomic. Rows go into `gapmap_staging`, which is dropped and recreated each run, and
the cutover is `gapmap` → `gapmap_previous`, `gapmap_staging` → `gapmap`, drop
`gapmap_previous`, all three renames in one transaction. A reader sees the whole old schema or
the whole new one, never a table that has loaded next to one that has not. Grants are applied to
the staging schema before the swap, since a rename carries privileges with it. `NEON_READ_ROLE`
names the role granted `SELECT`; unset means `PUBLIC`.

Column types are inferred from the data and deliberately timid: TEXT unless every non-empty
value in a column parses as BOOLEAN, INTEGER, DOUBLE PRECISION or DATE, and identity columns
(`slug`, anything ending `_slug` or `_id`) are pinned to TEXT whatever they look like. A
digits-only artifact id is a string with digits in it, and letting one run's values decide
otherwise would change the column type from under a query.

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
