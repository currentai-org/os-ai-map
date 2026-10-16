# Compute access by country: a page brief, 2026-10-15

Ayah Bdeir asked how compute comes onto the Gap Map and shared four sources:

- Epoch AI's [AI data centers](https://epoch.ai/data/ai-data-centers) hub
- Oxford Insights' [Government AI Readiness Index 2025 methodology](https://oxfordinsights.com/wp-content/uploads/2026/01/Methodology-Report-2025-1.pdf)
- the Ada Lovelace Institute's [*Computing Commons*](https://www.adalovelaceinstitute.org/report/computing-commons/) report
- a Claude artifact of her own, which could not be opened from this account and is not reflected here

This brief answers her question and specifies a page an OSO platform agent can build in the
`currentai` org. It follows the [24 Sep public AI compute brief](2026-09-24-public-ai-compute.md),
which stays the record of the program inventory. Figures describe what the cited source or table
held on the date above.

## The answer: by country, not by product

Compute does not go onto the scored map. The 24 Sep brief settled why: the unit of public compute
is the access program, a program is not a product, and adoption and capacity can't be measured
consistently across programs. Nothing since has changed that.

What can go on the Gap Map is a country view of compute, beside the country editions such as
`gap-map-france`. It answers one question:

> **If you are a researcher, a startup or a public body in country X, where can you get AI
> compute, on what terms, and how much of the compute in your country is public?**

Ayah's sources each answer one part of that, and none answers all of it:

| Source | What it measures | What it can't say |
|---|---|---|
| The 24 Sep inventory (36 programs) | Who can apply, on what terms, and whether intake is open | How much capacity sits behind most programs |
| Epoch AI GPU clusters | Capacity per cluster in H100-equivalents, owner, country, and sector (Public, Private, Public/Private) | Whether anyone outside the owner can use it |
| Epoch AI data centers | Where the large build-out is, by power and H100-equivalents | Public access. It is almost entirely private hyperscaler sites, 91% of tracked power in the US |
| Oxford Insights readiness index | A country score whose "Compute capacity" dimension (8.33% of the index) counts AI-chip cloud regions, public or public-private AI supercomputers (from Epoch), and data centers (from Data Centre Map) | Terms of access. It counts infrastructure, not who may use it |
| Ada Lovelace, *Computing Commons* | The provision typology the inventory already uses, and a framework of access and use conditions | Data. It is a policy report |

## The finding the page is built around

**Public ownership is not public access.** The largest public cluster Epoch tracks is El Capitan
at Lawrence Livermore, at 26% of the world's tracked public capacity. It serves NNSA mission work
and has no open call (24 Sep brief, Americas notes). Ranking countries by public capacity alone
would therefore overstate what an outside researcher in the US can reach. Joining the program
inventory to the clusters separates the two: capacity with an open call against capacity with none.

Other readings the current tables already support (pull of 2026-09-19):

- Epoch tracks 482 clusters: 274 private (about 1.35M H100e), 149 public (about 168K H100e) and
  50 public/private (about 55K H100e). Public capacity sits in 25 countries.
- Public capacity is concentrated. The top cluster holds 26%, the top four (El Capitan, JUPITER,
  Alps phase 2, Frontier) hold 51%, and US DOE alone holds about 40%.
- Countries differ in kind, not only in size. Switzerland's tracked capacity is all public, while
  the US is about 94% private. China's largest share is public/private. Korea, the UAE and Brazil
  have mixed capacity and little or no purely public capacity in Epoch's register.
- Of the 27 focus countries in the language-gap study, 20 show no tracked public or public/private
  cluster at all, among them every African and Latin American focus country. Only India (about
  310 H100e) and Thailand (about 220) register small public capacity outside the high-income
  group. Epoch tracks notable clusters only, so read a zero as "none tracked", never "none exists":
  South Africa shows zero, yet the inventory lists CHPC, whose 30 V100s are below Epoch's bar.

## Data the page reads

Everything below already exists in the `currentai` org unless marked new. These are standalone
OSO datasets, not repo-governed assets: per ADR-003 nothing here enters `warehouse/assets.yaml`
or `warehouse/dependencies.yaml`, and the page must not write to `registry`, `gap_map_analysis`
or any other repo-governed dataset.

**Existing**

| Table | Grain | Use on the page | Notes |
|---|---|---|---|
| `currentai.compute_sources.epoch_gpu_clusters` | one row per tracked cluster (482) | source for capacity | Static, pulled 2026-09-19. CC BY 4.0, credit Epoch AI. Existing systems only; Epoch puts coverage at 10–20% of world GPU cluster performance. 81 rows are `Likely`, not `Confirmed`. |
| `currentai.compute_sources.top500_systems` | one row per TOP500 system (500) | public system counts by segment | June 2025 list. Self-submitted; under-represents China. |
| `currentai.compute_supply.cluster_capacity` | one row per cluster | public/mixed/private split, `owner_bloc` | Adds `country_canonical`, `sector_group`, `owner_bloc` (keeps US DOE and EuroHPC apart). |
| `currentai.compute_supply.country_compute_supply` | one row per country (61) | the country table | `public_h100e`, `public_private_h100e`, `private_h100e`, `public_clusters`, `top500_public_*`, `is_focus_country`, population and GDP for focus countries. |
| `currentai.compute_supply.public_capacity_concentration` | one row per public cluster | concentration figure | Rank, share of world public capacity, cumulative share. |
| `currentai.compute_footprint.ai_datacenter_power` | one row per country | private build-out context | From Epoch AI data centers. Power, annualized TWh (an upper bound), H100e, capital cost. |
| `currentai.gap_map_geo.geo_products` | one row per Gap Map product | link to the Gap Map by country | `org_country`, `geo_bucket`, scores and tier. Daily from the os-ai-map payload. |
| `currentai.girai_analysis.country_scores` | country x score level | optional context | GIRAI 2026, CC BY 4.0. |

**New, built by the agent**

1. **`compute_programs`**, one row per program in the 24 Sep inventory (36 rows), parsed from
   the tables in [`2026-09-24-public-ai-compute.md`](2026-09-24-public-ai-compute.md). Columns:
   `program`, `jurisdiction` (as written), `country_iso3` (see the mapping rules below),
   `is_subnational`, `is_multinational`, `provision`, `status`, `eligibility_and_terms` (the
   "Who can apply" cell verbatim), `capacity_and_usage` (verbatim), `startup_or_sme_eligible`,
   `open_output_rule` (`required`, `none_published`, `n/a`), `source_urls` (array),
   `press_only` (true where the brief's notes flag press figures), `as_of` = `2026-09-24`.
   Take every value from the brief. Do not re-research or edit a row; a correction is a new
   dated brief.
2. **`program_facilities`**, a hand-built crosswalk from program to the Epoch clusters it
   allocates: `program`, `cluster_name` (exactly as in `cluster_capacity`), `allocation_note`
   (for example "EuroHPC takes 50% of time"), `match_confidence` (`named_in_brief`,
   `inferred`). Use only facilities the brief names (Isambard-AI and Dawn for the UK AIRR, Jean
   Zay, Alps, ABCI 3.0, Empire AI, SDumont, the EuroHPC machines, Frontier and the DOE leadership
   systems for INCITE and ALCC, and so on). A program with no named facility, such as IndiaAI or
   Korea's GPU provision, gets no row; it is market-based and owns no machine.
3. **`country_compute_access`**, one row per country, joining the three: public, mixed and
   private H100e from `country_compute_supply`; the count of programs by `status`; the public
   capacity behind a program with `status = open` (via `program_facilities`) as
   `open_call_h100e`; and the public capacity with no matched program as `no_open_call_h100e`.

**Mapping rules for `country_iso3`**

- A US state program (Empire AI, Massachusetts, Redtail, CalCompute) maps to USA with
  `is_subnational = true`.
- EuroHPC programs map to the EU as a bloc (`is_multinational = true`, `country_iso3` null), and
  the page lists them under every EU member state as "EU-wide". JUPITER, LUMI, Leonardo and
  MareNostrum 5 keep their host country in the cluster data.
- The African Compute Initiative maps to ZAF with `is_multinational = true`.

## The page

**Name:** `compute-access-by-country`. **Status:** unpublished draft until Carl reviews it.
**Render model:** a one-row Python UDM, like the other pages in this org. **Schedule:** daily
after `gap_map_geo` (09:00 UTC) is fine; most inputs are static, so the date on the page is the
data's `as_of`, not the render date.

**Visual system:** match `gap-map-france` and `evaluation-and-auditing-on-the-gap-map` (the
aipotluck.org system), so it reads as part of the same set.

**Sections, in order**

1. **The question and the answer in one line per part:** how much of the world's tracked AI
   compute is public, how concentrated that is, and how much of the public part has an open call.
2. **Public ownership against public access.** One figure: public capacity per country, split into
   "behind an open call" and "no open call found". El Capitan and the other DOE machines are the
   worked example.
3. **Country explorer.** A searchable, sortable table of countries: public, mixed and private
   H100e (three columns, never summed into one "total"), programs by status, the cheapest open
   route listed in the inventory, and whether startups or SMEs are eligible. Selecting a country
   opens its programs with eligibility and terms verbatim, each source linked, and its tracked
   public clusters.
4. **Who can apply.** The 36 programs by provision type (Ada's typology plus `federated`,
   `hybrid` and `undetermined`) and status. Highlight the three things the 24 Sep brief found:
   open-output rules are rare, startup access is narrow, and much of the capacity is still law or
   plans.
5. **Where the private build-out is.** Epoch AI data centers by country, as context only, on its
   own figure.
6. **From compute to the stack.** For each country, a link to the Gap Map products whose
   organizations are based there (`gap_map_geo.geo_products`), and to the country edition where
   one exists (`gap-map-france`).
7. **Sources and limits.** Every source with its date and license, and the rules below in plain
   language.

**Rules the page must keep**

- Never add H100-equivalents, TOP500 system counts, TWh and program counts together, or put two
  of them on one axis. They are different universes in different units. Each gets its own figure.
- Absence from Epoch is "no tracked cluster", never "no compute". Say so wherever a country shows
  zero.
- Label press-only figures, as the 24 Sep brief does.
- Readiness-index scores, if shown, are context, labeled as Oxford Insights' or GIRAI's own
  measure, and never blended into a computed figure.
- No ranking of countries by a composite score. The page compares, it does not score.
- Credit Epoch AI under CC BY 4.0, and GIRAI under CC BY 4.0, on the page.
- Do not use Data Centre Map. Its terms forbid scraping and redistribution.
- No public dataset of compute access programs exists. Epoch publishes none, and the Ada Lovelace
  Institute's 2024 mapping is a policy brief. The 24 Sep inventory is the only program source, so
  credit it as this project's own research.

**Done when**

- [ ] `compute_programs`, `program_facilities` and `country_compute_access` exist, each with a
      description that states its grain, its `as_of` and its sources.
- [ ] Every program row traces to a row of the 24 Sep brief, and every facility match to a
      facility the brief names.
- [ ] The page renders the seven sections above, unpublished.
- [ ] A short note on the page or in the dataset description lists anything the agent could not
      map, such as a facility with no Epoch row.

## Open questions

These are for Carl, and for Ayah where marked.

- **Ayah's artifact.** It could not be read from this account. If it names sources or framing
  not covered here, fold them in before the page is published. *(Ayah)*
- **Refresh.** The org's pulls are from 2026-09-19. A re-pull changes less than it seems:
  - Epoch's GPU clusters CSV regenerates daily, but its newest existing cluster went live
    2025-07-22 and the dataset covers an estimated 10–20% of world GPU cluster performance.
    Epoch's own page was last updated 2026-03-13. Re-pulling it buys little.
  - Epoch's raw file (`gpu_clusters_raw.csv`, 887 rows) does add something: 176 planned systems,
    22 of them public and 39 public/private. That would fill the inventory's `building` and
    `announced` rows with capacity figures.
  - TOP500 has a June 2026 list (`TOP500_202606.xlsx`) against the June 2025 list in the org. It
    states no license, only a copyright line, so keep it to counts, as the org does now.

  Recommendation: ship on the September pull, and add the raw file's planned systems as a
  separate, labeled series.
- **Oxford Insights.** Its page embeds 2025 scores for 195 countries, `compute_capacity`
  included, but under "All rights reserved" with no license, and the indicator-level data sits
  behind a sign-up form. Leave it out unless Oxford Insights grants reuse, and use GIRAI
  (CC BY 4.0, already in the org) for readiness context.
- **Commercial cloud regions.** The Oxford Internet Institute's 2025 cloud-region data is not
  downloadable. Its 2023 census (187 regions, six providers, on OSF) carries no license, and the
  OECD.AI compute tracker has no export. The OECD paper behind it (AI Papers No. 49, October
  2025, CC BY 4.0) has country tables in PDF only. A "where can you rent a GPU" panel would need
  the authors' permission or a hand transcription of the OECD tables. Leave it for a later
  version.
- **The France edition.** Add a compute panel to `gap-map-france` from the same tables, or keep
  compute on its own page and link to it?
- **Program inventory cadence.** The 24 Sep brief is the only program source. A second dated
  brief before MozFest would catch the AI Gigafactories call (closes 2026-11-12) and the NSF hubs
  (proposals due 2026-11-04).

## Sources

- [Public AI compute: who can get capacity](2026-09-24-public-ai-compute.md), this repository,
  2026-09-24
- Epoch AI, [AI data centers](https://epoch.ai/data/ai-data-centers), updated 2026-10-12, CC BY 4.0
- Epoch AI, [GPU clusters](https://epoch.ai/data/gpu-clusters) (formerly "AI Supercomputers"),
  CC BY 4.0, as pulled into `currentai.compute_sources` on 2026-09-19. The `Sector` field
  definitions are in its [records documentation](https://epoch.ai/data/gpu-clusters-documentation/records).
- [TOP500](https://top500.org/lists/top500/2026/06/), June 2025 list as pulled on 2026-09-19.
  The June 2026 list is the current one.
- Oxford Insights, [Government AI Readiness Index 2025: methodology](https://oxfordinsights.com/wp-content/uploads/2026/01/Methodology-Report-2025-1.pdf),
  January 2026
- Matt Davies and Jai Vipra, [*Computing Commons: Designing public compute for people and society*](https://www.adalovelaceinstitute.org/report/computing-commons/),
  Ada Lovelace Institute, 2025-02-07
- Zoe Jay Hawkins, Vili Lehdonvirta and Boxi Wu, [*AI Compute Sovereignty: Infrastructure Control
  Across Territories, Cloud Providers, and Accelerators*](https://ssrn.com/abstract=5312977), June
  2025, the source of Oxford Insights' cloud-region indicators
