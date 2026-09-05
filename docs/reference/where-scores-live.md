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

One row per product per category, all three axes with their own confidence and
`last_verified`, plus the derived `overall_score`, `maturity`, `is_mature` and `score_tier`.
Published by `build/serialize_scores.py` on every push to `main` touching `sources/**`.

Two properties to know before querying it:

- **It transcribes the payload; it derives nothing.** The blend comes out of
  `serialize._maturity_score` against the category's weights, and there is exactly one
  implementation of it. So these numbers are the numbers the front end shows.
- **Published-map products only.** `build_payload` excludes preliminary categories by design, so
  a preliminary category's products are absent from this table even though
  `currentai.registry.categories` would carry the category itself. While no category is
  preliminary the table covers the whole published corpus; a preliminary one makes it a subset.

Coverage: openness is present on every row. Adoption and capability may be absent, because an
axis abstains where no qualifying instrument or peer comparison exists. An unmeasured axis is
NULL rather than missing, so "not measured" and "no such column" cannot be confused.

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
`os-ai-map` is the gap map's, and the publisher touches only it and its own two working
schemas, `os-ai-map_staging` and `os-ai-map_previous`. It refuses to run against any of the
other three.

Both working names are steady state, not transients. `os-ai-map_staging` exists while a load
runs. `os-ai-map_previous` exists **between** runs and holds the entire previous corpus —
tables, rows, enum types, and the `SELECT` grant that travelled with the rename — until the
start of the next publish reclaims it. So the database normally carries two readable copies of
the map: the live one and the one it replaced. Storage is roughly double, and anything that can
read `os-ai-map` can also read the superseded corpus under `os-ai-map_previous`. Nothing is
meant to, and the publisher does not stop anything from trying — do not build against that
name.

**Nothing reads Neon yet.** The front end still consumes `build/notebook_data.json`, so the
four ordering columns above are preservation for the consumer that comes next rather than
something in use today. A publish that dropped the information would destroy it, and carrying
it costs four integers per row.

**Neon serves the site's tables, and nothing else.** The target model from CLEVER FRANKE,
with Carl's amendments: `products`, `organizations`, `categories`, `layers`, `stages`, `gaps`,
`gaps_categories`, `openness`, `adoption`, `capability`, `sources`, `product_lineage`,
`aliases`, `long_tail_top`, `long_tail_counts`. Every row is derived from
`build/notebook_data.json`, so what Postgres serves is what the repo published.

The registry tables were loaded here too for a while, prefixed `registry_`, so Neon and the
warehouse would carry the same declarations. Nothing on the site read them, so they are gone.
**The registry surface lives in the warehouse** as `currentai.registry.*`, and on disk as
`build/registry/*.csv` — not in Neon. A question about what the repo declares is answerable
there; Neon answers what the site renders.

Plus `publish_runs`: exactly one row, describing the load you are looking at — the swap
replaces the table along with everything else, so it is a stamp on the current corpus and not
an accumulating history. It carries `run_id`, `published_at`, `schema_version`,
`built_at`, `released_at`, `source_git_sha`, `declaration_version_id`, `table_count` and a
`row_counts` JSONB. That row is how you tell which commit and which shape the serving layer is
showing.

**Ids are stable across loads, and the slug is still the identity.** Every surrogate `id` in
the map group is `stable_id(table, natural_key)` — the first 63 bits of a SHA-256 over the
table name and the row's own key. Ids used to be positions in a sorted list, so adding one
product renumbered every row after it and any id that had reached a URL, a cache or a CMS row
pointed at a different product after the next publish. A hashed id does not move when the
corpus grows, so it is safe to store as an internal reference. Hashing the table name in as
well means the same slug in two tables gets two different ids, and a join that crosses tables
by mistake matches nothing rather than appearing to work.

The natural key per table: `products.slug`, `categories.slug`, `layers` and `gaps` by their
label, `stages` by their stage number, `long_tail_top` by its name, `product_lineage` by
`(product_slug, relation, target)`, `sources` by
`(product_slug, metric, url, shows, accessed)`. Organizations key on `slug` and aliases on
`alias`, with no surrogate at all.

A source's key carries `shows` and `accessed` because the URL alone does not identify the row.
One source list can hold the same URL twice on the same axis — 69 pairs today — and every one
of those pairs is a re-verification that recorded a different claim or a different date. They
are two observations of one page, and those two fields are what tell them apart. The
consequence worth knowing: editing a source's `shows` or `accessed` moves that row's id,
because it is a different observation and an id moves when its natural key does.

**The slug remains canonical.** A deep link, a bookmark, a CMS reference, anything another
system stores or a person reads should carry the slug, not the id. The id is a join key, and
it changes if the natural key it is derived from ever changes. `categories` carries a `slug`
alongside its id for exactly this reason — the PDF omitted it, and every deep link and every
join from the warehouse's registry tables needs it.

Before writing, the publisher asserts that no table has a repeated id and fails the run naming
the table and both natural keys if one does. A duplicate would otherwise be rejected by the
primary key at COPY time, in a message naming neither.

**The five enums are enforced.** `alias_kind`, `freshness_basis`, `lineage_relation`,
`capability_relation` and `metric_name` are created in the schema, and a payload value with no
mapping fails the load naming the value rather than being coerced to something adjacent. The
DBML's other three (`health_status`, `integration_type`, `gap_type`) belong to the gallery
tables and are not created here — see "What the CMS owns" below.

**The DBML's constraints are real.** Every primary key, `NOT NULL`, unique and foreign key the
target model declares is emitted in the CREATE statement, so the database enforces the model
rather than the site discovering a dangling id at render time. `categories.slug` also gets a
unique the DBML does not declare, because the column is an amendment and a duplicate slug
would break the deep links it exists for. A violation aborts the COPY, the staging schema is
discarded, and the live schema stays exactly where it was — failing there is the point.

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

### What the CMS owns

**Gallery content is not in this schema.** `gallery`, `gallery_products` and `gallery_gaps`
were here, created and left empty so the site's queries would compile. That was a hazard
rather than a courtesy: this publisher drops and recreates its schema on every load, so the
first gallery row an editor wrote would have been deleted by the next push to `main`, with
nothing raising anywhere and every artifact of the publish still reporting `gallery 0 rows`.

A schema rebuilt from source can only hold rows it produced. Gallery content is authored, so
it belongs in the CMS's own `payload` schema, or in a separate `os-ai-map_cms` schema that
this publisher never creates, never drops and never grants on. Both are on the same database,
so a join across them costs a qualified name and nothing else.

**For whoever builds that:** a *view* in the CMS schema over a table in `os-ai-map` will not
survive a load. The cutover renames the schema, and a view binds to the table it was created
over by OID rather than by name, so the view ends up pointing into `os-ai-map_previous` and is
dropped when that is reclaimed. `publish_neon.reclaim_previous` detects exactly this and
refuses to run rather than dropping the view — the failure is loud, but it is still a failure.
Read the map's tables directly, or materialize a copy CMS-side.

### Where this departs from the designers' model

Four places, all deliberate, all in `build/neon_schema.py`:

| Departure | Why |
|---|---|
| `id` and every column referencing one are `bigint`, not `integer` | The ids are 63-bit hashes. 63 rather than 64 because Postgres has no unsigned integer and half the ids would otherwise be negative. |
| `categories.slug`, which the DBML omits | Every deep link is by slug, and so is every join from the warehouse's registry tables; it carries a `UNIQUE` for the same reason. |
| `layers.sort_order`, `categories.sort_order`, `long_tail_top.sort_order`, `stages.num` | The old positional ids carried the layer stack order, the map's curated category order, the long tail's ranking and the stage number — `categories.stage` *was* the stage number, and `stages.id` was the number it pointed at. A hashed id carries none of that, and the model has nowhere else for it: `layers` is `{id, label}`, `stages` has no number, and neither `categories` nor `long_tail_top` has an ordering field. So it moved into columns of its own; `ORDER BY sort_order` is what `ORDER BY id` used to mean. |
| `gallery`, `gallery_products`, `gallery_gaps` and their three enums are absent | The CMS owns authored content; a schema rebuilt from source can only hold rows it produced. See below. |

### Two things the designers should know about the data

**`sources.notes` is always NULL.** The target model has the column and the payload has no
field for it, so nothing here fills it. In the other direction, the payload's `establishes`,
`content_sha256` and `http_status` have no column in the target model. `shows` is the one that
maps.

**`capability.relation` is lossy.** The payload carries a signed distance (`at`, `one_above`,
`one_below`, `two_below`) and the target enum has none, so `one_below` and `two_below` both
arrive as `tier_below`. The exact distance is only in `capability.notes`. `anchor` is in the
enum and unused. If the front end needs the distance, the enum has to grow.

### The load is atomic, and the swap is the migration path

Rows go into `os-ai-map_staging`, dropped and recreated each run, and the cutover is two
renames in one transaction: `os-ai-map` → `os-ai-map_previous`, then `os-ai-map_staging` →
`os-ai-map`. A reader sees the whole old schema or the whole new one, never a table that has
loaded next to one that has not. Grants are applied to the staging schema before the swap,
since a rename carries privileges with it; `NEON_READ_ROLE` names the role granted `SELECT`,
and unset means `PUBLIC`.

**Nothing is dropped in that transaction.** `DROP SCHEMA … CASCADE` takes an exclusive lock on
every table it removes, so a drop in the cutover would hold the applied-but-uncommitted
renames behind any in-flight site query, and arriving readers would queue behind the pending
lock — one slow reader stalling every reader for as long as it runs. Pure catalog renames take
no table locks. `lock_timeout` is 5s on the session and the swap transaction is retried three
times with backoff, because the schema's own catalog row can still be contended.

The old schema stays as `os-ai-map_previous` and is reclaimed at the *start* of the next run,
after `pg_depend` is checked for dependents outside the three schemas this publisher manages.
If any exist the run fails listing them, rather than dropping. `PROTECTED_SCHEMAS` stops the
publisher naming someone else's schema, but CASCADE follows dependencies, not schema
membership: a view in `payload` over `os-ai-map.products`, or a foreign key from a CMS table
into it, still depends on that table after the rename. Without the check, a CASCADE would drop
that object too, in its own schema, silently, on every publish.

There is no migration tool, and for now there does not need to be one: every publish rebuilds
the schema from `build/neon_schema.py`, so a shape change is live on the next load with no
ALTER anywhere. What that costs is a reader's ability to tell which shape it has, which is why
`publish_runs.schema_version` exists — bump `SCHEMA_VERSION` in the same commit as any change
to a table, column or enum. Once something outside this repo depends on the shape, that is the
point where a real migration path replaces the swap.

Every column's type is declared in `build/neon_schema.py`, next to the grain it describes;
nothing is inferred from a run of the data. An empty CSV field loads as NULL, so "absent" and
"empty" are the same value.

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
