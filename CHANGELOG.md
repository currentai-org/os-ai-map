# Changelog

All notable changes to this repository are recorded here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
What a MAJOR, MINOR, or PATCH bump means for a data-and-schema repo is spelled out in
`skills/publish-release/SKILL.md`; the `publish-release` skill cuts each release.

Record a change under `## [Unreleased]`, in the same PR that makes it, only when it is
**notable and user-facing** — a new or removed product, category, or data source; a schema or
scoring change; a new skill or workflow. Routine maintenance stays out: bot regenerations,
dependency bumps, internal refactors, and day-to-day evidence refreshes that do not move a
published score. Put each entry under the matching heading (Added, Changed, Deprecated,
Removed, Fixed, Security), one line, newest first, in plain past tense, with the PR linked.

## [Unreleased]

### Added

- `publish_runs.version` in the Neon schema, the dataset's semantic version, so the site's version
  badge reads it from the publish it serves (`SCHEMA_VERSION` 5)
  ([#703](https://github.com/currentai-org/os-ai-map/pull/703)).
- The Language-specific datasets category, published with 97 scored products: datasets built for
  underrepresented languages across speech, pretraining text, instruction data, parallel text and
  evaluation, three withheld corpora included
  ([#689](https://github.com/currentai-org/os-ai-map/pull/689)).
- A license leg on the contradiction sweep (`build/check_contradictions.py`): the repository
  license `signal_github` collects, against the license the openness score records. Built and
  withdrawn twice before, because the corpus records a license as a name plus a qualification and
  a comparison that misses the qualification reports records that were already right. It now
  reuses the rubric's own parsing and compares only where the recorded license covers the
  repository's code — an explicit `code` scope decides it, and otherwise the product's type does,
  since a model's or dataset's unqualified license is about the weights or the data. It abstains
  on any other qualification, on a compound with no single code-scoped part, and on a product with
  more than one repository row, and reports those abstentions grouped by rule so a quiet run can
  show it looked ([#640](https://github.com/currentai-org/os-ai-map/issues/640)).
- Four published categories from the two roster splits. `ml_orchestration` (29 products) took `ray`
  and the pipeline and scheduling tools out of the frameworks roster
  ([#429](https://github.com/currentai-org/os-ai-map/issues/429),
  [#596](https://github.com/currentai-org/os-ai-map/pull/596)). `agent_tools_protocols` then came
  apart into four rather than the three the issue proposed — `document_conversion` (20),
  `search_retrieval` (21), `agent_protocols` (20) and the remainder renamed
  `agent_tools_connectors` (21) — because the products separated that way once the peer sets were
  built ([#430](https://github.com/currentai-org/os-ai-map/issues/430),
  [#607](https://github.com/currentai-org/os-ai-map/pull/607),
  [#610](https://github.com/currentai-org/os-ai-map/pull/610),
  [#614](https://github.com/currentai-org/os-ai-map/pull/614),
  [#616](https://github.com/currentai-org/os-ai-map/pull/616),
  [#618](https://github.com/currentai-org/os-ai-map/pull/618)). The warehouse's scoring chain has
  not been rebuilt against the new taxonomy and `check_parity` reports the lag
  ([#647](https://github.com/currentai-org/os-ai-map/issues/647)).
- ADR-005, the inclusion principle for closed and platform products: they are on the map to mark the
  frontier, not to be catalogued, with a score of 4 or higher as an initial screen. It is guidance a
  curator applies rather than a predicate a build evaluates, and nothing in `build/` or `tests/`
  fails because a product sits below the line. The tail was surveyed against it — 81 above, 61
  below, 3 unmeasured of 145 ([#628](https://github.com/currentai-org/os-ai-map/pull/628)).
- A contradiction sweep, `build/check_contradictions.py`, and the weekly `contradiction-sweep`
  workflow. It asks whether anything already collected disagrees with a record, rather than whether
  a source still reads the way it did, so it is a warehouse read and fetches nothing. One leg today:
  a repository marked archived under a product that records no `end_of_life`. It raises and does not
  decide — `main` exits 0 with findings present — and `sources/contradictions_settled.yaml` records a
  ruling that an observation is not a defect, bound to the observed value so it expires when the
  observation changes ([#641](https://github.com/currentai-org/os-ai-map/pull/641)).
- Part 0 of `docs/reference/evidence-and-freshness.md`: a check exists to **refute** a score, and
  confirmation is what is left when refutation fails. It separates drift, which is about a fetch,
  from a contradiction, which is about a score, and separates the light corpus-wide pass from the
  heavy per-category refresh — only the second can confirm an axis
  ([#641](https://github.com/currentai-org/os-ai-map/pull/641)).
- A weekly `adoption-reconciliation` workflow, and adoption's `last_verified` now derives from the
  observation behind the scheduled run that re-measured it rather than from a person. 460 adoption
  axes gained a `derived_from` block naming the snapshot, the source run, the route and the measured
  level; a disagreement leaves the date where it was and raises the product on a tier-change queue
  instead. Only a SCHEDULED, successful materialization no older than two weekly cycles may date an
  axis ([#637](https://github.com/currentai-org/os-ai-map/pull/637)).
- `registry.product_score_notes`, publishing each axis's note to the warehouse — 2,289 rows, verified
  byte-identical to the notebook payload
  ([#623](https://github.com/currentai-org/os-ai-map/pull/623)).
- `components-listed` on the pretraining-data ladder: every component named and each resolving to a
  public source, while the mixture or sampling is withheld. Applied to the seven records whose cited
  evidence already states the discriminator
  ([#591](https://github.com/currentai-org/os-ai-map/pull/591)).
- `yylo-benchmark` to `evaluation_code`
  ([#582](https://github.com/currentai-org/os-ai-map/pull/582)).
- `yylo` (`yylo-dev/yylo`) to `orchestration_agents`, with the JUNO AI organization
  ([#561](https://github.com/currentai-org/os-ai-map/pull/561)).
- `not_primary_channel`, a per-artifact declaration on a product's artifact entries: the presence of
  the key exempts that artifact from the product's summed adoption figure and the value says why.
  Declared on `hexabot`'s npm widget and `yomo`'s crate, carried into
  `registry.product_artifacts` as a column the two deployed `signal_packages` models already read,
  and honoured by `build/adoption_measurements.py`, which now drops the artifact from the sum and
  falls through to stars where a product ships through no package at all. Both products band at
  level 2, where the 2026-08-14 minority-channel ruling put them; the `registry` static model gains
  a column and must be recreated on the platform rather than re-uploaded
  ([#562](https://github.com/currentai-org/os-ai-map/issues/562)).
- Automatic adoption of confidence-1.0 identity matches. A digest item whose name and graph agree
  is written to the resolution ledger without a human tick; anything below stays a checkbox. The
  weekly workflow opens a PR with the adopted entries and a person merges it, and auto-adopted
  entries are excluded from the identity eval so it cannot score the graph against its own output
  ([#552](https://github.com/currentai-org/os-ai-map/pull/552)).
- A `form_factor` dimension on the hardware openness ladder — board, module or chipset — recorded on
  all 20 `edge_hardware` products, with every rung that reads `schematics` now testing it first and a
  chipset rung that asks instead whether the datasheets are public and whether anybody can buy one.
  `rockchip-rk3588` is no longer deferred and reproduces the 3/documented it already recorded; no
  other score moved ([#219](https://github.com/currentai-org/os-ai-map/issues/219)).
- `embeddings_retrieval`, a published category of 35 products — models whose headline output is a
  vector or a relevance score rather than a chat completion. Extends the shared `pretrained`
  openness ladder, the first reuse of it outside `base_pretrained`; capability is anchored on
  MTEB/MMTEB with hand-authored rungs and six banding rules, and the roster includes the closed
  commercial API tier ([#540](https://github.com/currentai-org/os-ai-map/pull/540)).
- A rule in `docs/reference/openness.md`: where a product's openness and capability scores rest on
  different SKUs, the record must name which and why. `multi_sku_rule` resolves openness on
  distributed weights while capability reads the best tier a publisher ships, so a family with a
  small open checkpoint beside a hosted flagship measures two artifacts on two axes. Applied to
  `voyage-embeddings` and `esm-3`; the fix is disclosure rather than splitting the product
  ([#540](https://github.com/currentai-org/os-ai-map/pull/540)).
- `scientific_ai_models`, a published category of 34 products — models for scientific domains, from
  protein structure and single-cell biology through weather, materials and earth observation.
  Capability uses a `feature_matrix` instrument because the domain has no shared public benchmark
  ([#537](https://github.com/currentai-org/os-ai-map/pull/537)).
- `languagebench` (`fair-forward/evals-for-every-language`) to `evaluation_code`, with the
  `fair-forward` organization ([#531](https://github.com/currentai-org/os-ai-map/pull/531)).
- An `end_of_life` field on the product schema, and `perspective-api` declared ending. The map had
  two states for a product and neither was honest about a service with an announced shutdown date;
  the date and its source serialize onto the product row, and `check_payload` gates the shape.
  Nothing in the build compares the date to today, so an expired product is not yet treated
  differently — the post-expiry policy is deferred
  ([#524](https://github.com/currentai-org/os-ai-map/pull/524)).
- A comparison-cycle check in `check_capability`. The arithmetic check read each `relative_to` edge
  in isolation, so a cycle of edges could be individually valid and collectively unresolvable
  ([#516](https://github.com/currentai-org/os-ai-map/pull/516)).

### Changed

- Published datasets that state no license now cap at 2, not 3: there is no grant to rely on, but
  the files are out, and 1 is kept for what is closed or private. No-derivatives data scores 2 as a
  written exception for data, and Esethu's bounded commercial use scores 3. Fourteen dataset records
  move from 3/gated to 2/restricted and fifteen deferrals close. CC-BY-4.0 model weights join
  `permissive_non_osi`, and FSL-1.1 joins `competition_restricted`.
- The Neon publish runs only from `main`. A branch dispatch used to load Neon, which was safe while
  nothing read it; aipotluck.org now serves that schema live
  ([#703](https://github.com/currentai-org/os-ai-map/pull/703)).
- `langtrace` adoption now comes from Docker Hub pulls of its server image, averaged over the
  image's lifetime as a floor, instead of downloads of its Python SDK, which is declared
  `not_primary_channel`. It moved from 2 to 1, with no telemetry_observability stage move.
  `browserbase` moved to `reported_traction` on the vendor's own session and customer figures
  rather than Stagehand's downloads, with its level unchanged at 3
  ([#695](https://github.com/currentai-org/os-ai-map/issues/695)).
- `lakefs` openness moved from 5 (open source) to 2 (source available) after Treeverse relicensed
  lakeFS from Apache-2.0 to the Business Source License 1.1 with v1.87.0 on 22 September 2026. Its
  Additional Use Grant allows production use only of the unmodified release for internal purposes.
  No storage stage move ([#692](https://github.com/currentai-org/os-ai-map/issues/692)).
- `qdrant` and `milvus` adoption now comes from Docker Hub pulls of the server image, averaged over
  the image's lifetime as a floor, instead of downloads of their Python clients. Their pypi
  artifacts are declared `not_primary_channel`. qdrant moved from 5 to 3 and milvus from 4 to 3,
  with no storage stage move. `braintrust` moved to `reported_traction` with its level unchanged
  ([#658](https://github.com/currentai-org/os-ai-map/issues/658),
  [#690](https://github.com/currentai-org/os-ai-map/pull/690)).
- The shared dataset ladder names four more licenses: cc-by-nc-4.0 and cc-by-nc-sa-3.0 as
  noncommercial, cc-by-2.5 and cc-by as open data; no existing score moved
  ([#689](https://github.com/currentai-org/os-ai-map/pull/689)).
- `openness.components` gained a reserved `context` mapping for the keys a product's ladder does
  not read, such as `service`, `commercial` and `governance`. The 394 such clauses on 266 records
  moved into it, `raw` and every score unchanged, and `check_components` now fails a record whose
  top level holds an unread key or whose `context` holds a read one. Before this, an unread key
  dropped out of the score silently and `serialize_rubric` warned about it 389 times a run
  ([#188](https://github.com/currentai-org/os-ai-map/issues/188),
  [#683](https://github.com/currentai-org/os-ai-map/pull/683)).
- The Neon serving layer gains a `groups` table and a NOT NULL `categories.group_id`
  referencing it, so the `os-ai-map` schema carries the arc / group / category hierarchy the
  taxonomy declares. `SCHEMA_VERSION` is 4. The column is `group_id` because GROUP is reserved
  in Postgres. ([#621](https://github.com/currentai-org/os-ai-map/issues/621))

- A group tier between arc and category in `sources/taxonomy.yaml`: each arc now declares an
  ordered list of groups, each holding its categories. A category's group is derived from where
  it sits, as its arc and layer already are. The payload gains `group`/`group_slug` per category
  and a `group_order` list; `registry.categories` gains `group_name` and `group_slug`. Additive
  throughout, so `PAYLOAD_CONTRACT` stays at 1. ([#621](https://github.com/currentai-org/os-ai-map/issues/621))

- `check_parity` now separates taxonomy **lag** from drift. A divergence attributable to a whole
  category that exists on one side only — every product of a category the warehouse has no rows
  for, or every row under a category with no file in `sources/categories/` — is the scoring chain
  not having been re-materialized since a taxonomy change, which nothing in the repo can trigger.
  Those are reported and dated from the commit that created or deleted the category file rather
  than failed on, and fail like drift past fourteen days. Both tests are whole-category: one
  product missing from a category the warehouse does publish is still drift. The workflow now
  checks out full history, without which every lag reads as undatable and the bound never bites
  ([#647](https://github.com/currentai-org/os-ai-map/issues/647)).
- `docs/reference/` and `docs/architecture/` read as canonical reference rather than as a changelog.
  111 issue references were removed, along with the passages narrating why a rule changed
  ([#629](https://github.com/currentai-org/os-ai-map/pull/629)).
- A route abstains where its coverage is short rather than banding on a partial measurement
  ([#588](https://github.com/currentai-org/os-ai-map/pull/588)).
- An acceptable-use policy is conduct rather than a use bound on the model ladder, which settles the
  two ladders against each other ([#589](https://github.com/currentai-org/os-ai-map/pull/589)).
- `compilers` capability bands on surface and dependence rather than on pipeline depth. Separating
  CUTLASS from Composable Kernel would have scored CUDA's install base against ROCm's
  ([#592](https://github.com/currentai-org/os-ai-map/pull/592)).
- Adoption-only grading is documented as the intended behaviour rather than as a fallback
  ([#593](https://github.com/currentai-org/os-ai-map/pull/593)).
- `laminar` adoption 3 to 5, banded on its own measured downloads
  ([#572](https://github.com/currentai-org/os-ai-map/pull/572)).
- `mcp-inspector` adoption to 4, on the same basis
  ([#581](https://github.com/currentai-org/os-ai-map/pull/581)).
- `opencode` relabelled to `usage_volume`, with Cohere's SDK trap named
  ([#570](https://github.com/currentai-org/os-ai-map/pull/570)).
- The suggest-a-product form offers all 24 categories, re-derived rather than hardcoded
  ([#622](https://github.com/currentai-org/os-ai-map/pull/622)).
- The published prose is written for the reader rather than the score auditor. `docs/reference/product-copy.md`
  is now the guide for every hand-written string on the map, with eleven goldens and a 600-character note
  guard; every score note, source line and footnote in the corpus that used the rubric's own words, quoted a
  usage figure, or ran past the guard was rewritten to it, one commit per category, through a guarded editor
  that could move no score, date, URL or digest; a second pass per category brought the notes still over two
  sentences or 400 characters down to the argument for the rung, and took the reference to "this record",
  the second person and the over-long paragraph out of the product descriptions. A usage figure in a
  note now fails the suite unless the axis is on the product-fact allowlist, `prose_edit` refuses the
  rubric's words, a template opening and a new figure, and `UNDERSTATES` no longer reads the affirmative
  "is the primary distribution channel" as an admission, which drops four products from the pinned set. The dated "Verified" line is gone from all 763 product
  footnotes, `build/prose_worklist.py`, `build/prose_edit.py` and `build/check_prose_diff.py` are the tools
  for the next pass, `clean-corpus-prose` replaces the `clean-score-notes` skill, and the case law that lived
  as `#` comments in the rubric, registry and config files is under `docs/reference/` and `docs/sweeps/`
  ([#620](https://github.com/currentai-org/os-ai-map/pull/620)).
- `meta-ai` capability 3 to 4: reach was being read as capability, and reach is adoption. The
  hardware ladder's `firmware` vocabulary is now defined on necessity rather than size, after one
  board recorded `minimal` where nineteen recorded `required` for the same fact; `raspberry-pi-5`
  now reads `required` and no score moved with it, and `tensorlake-sandbox` held at 4
  ([#571](https://github.com/currentai-org/os-ai-map/pull/571)).
- The `pypi`, `npm` and `crates` adoption routes all read `currentai.signal_packages.downloads` with
  an `artifact_kind` filter. npm and crates previously pointed at no table, so a download count
  recorded on either is now falsifiable rather than merely re-checkable
  ([#568](https://github.com/currentai-org/os-ai-map/pull/568)).
- `observations.product_adoption_current` reads its package arm from
  `currentai.signal_packages.downloads` instead of `currentai.signal_pypi.package_downloads`, so the
  observation layer now sees npm and crates alongside PyPI. `channel` and `artifact_kind` are
  projected from the source row rather than hardcoded to `pypi`. The PyPI leg is unchanged — all 169
  rows carry the same values and the same `observed_at` — and 18 package rows over 16 products are
  new. Fourteen of those products gain a banded adoption measurement where the npm route previously
  resolved to no observation; `hexabot` and `yomo` stay on stars at level 2, because every package
  artifact they declare is `not_primary_channel`
  ([#562](https://github.com/currentai-org/os-ai-map/issues/562)).
- Capability abstained on the four scored evaluation datasets. `gaia`, `humanitys-last-exam` and
  `livebench` drop from 5 to null and `mt-bench` from 4 to null. Capability read as discriminative
  power decays as a benchmark is adopted and trained against, which makes it anti-correlated with
  adoption and puts the category on a treadmill; the twenty-eight records that already abstained
  had it right
  ([#548](https://github.com/currentai-org/os-ai-map/pull/548)).
- `compilers` reports an adoption gap where it previously reported none. A product at exactly 4 on
  both adoption and capability clears each cutoff while missing maturity, and where such a product
  is its category's best the category rendered with no gaps at all. 32 fully-open products across 13
  categories sit in that zone; `compilers` was the only category it silenced
  ([#549](https://github.com/currentai-org/os-ai-map/pull/549)).
- Every URL field the schemas constrain now requires a host, across the product, organization,
  score and registry schemas ([#554](https://github.com/currentai-org/os-ai-map/pull/554)).
- `last_verified` may be written by whatever confirmed the evidence, a person or a tool that re-read
  every establishing source, rather than by a person alone; a source is confirmed on the quoted
  fragments inside `shows` rather than the sentence around them; and machine re-dating is enforced
  to openness, so `--axes capability` now exits 2 instead of re-dating against the ruling
  ([#557](https://github.com/currentai-org/os-ai-map/pull/557),
  [#558](https://github.com/currentai-org/os-ai-map/pull/558),
  [#559](https://github.com/currentai-org/os-ai-map/pull/559)).
- `agenta` moved from `telemetry_observability` to `orchestration_agents`, capability 3 unchanged
  and re-anchored on `openhands` because its old anchor stayed behind. LlamaFactory renamed with an
  `aliases` field, and twelve arXiv citations repointed from `/abs` to `/pdf` behind a new
  `check_citations` gate ([#544](https://github.com/currentai-org/os-ai-map/pull/544)).
- Three license names ruled onto the shared `pretrained` tiers: `OpenMDW-1.1` to
  `permissive_non_osi`, `Llama-3.2-Community-License` to `use_bounded`, `CC-BY-NC-4.0` to
  `commercial_forbidden`. All four products that had been deferred for them now compute, and no
  recorded score moved — each had been hand-placed at exactly the value its tier produces
  ([#540](https://github.com/currentai-org/os-ai-map/pull/540)).
- `base_pretrained`'s openness ladder extracted into `sources/rubrics/pretrained.yaml` and inherited
  through `scoring_recipe: {extends: pretrained}`. Openness only: adoption and capability stay
  per-category, because neither instrument travels. The block moved verbatim and all 32
  `base_pretrained` scores reproduce ([#535](https://github.com/currentai-org/os-ai-map/pull/535)).
- Every workflow document and skill now leads its validation section with `build.preflight`, which
  runs each CI step locally and accounts for the three it cannot. It already existed and was
  undiscoverable, which is what `docs/operations/postmortem-2026-09-10-scientific-ai-models.md` was
  written about ([#539](https://github.com/currentai-org/os-ai-map/pull/539)).
- `perplexica` renamed to Vane, and `composable-kernel` re-declared, on the identity rulings of
  2026-09-08 ([#523](https://github.com/currentai-org/os-ai-map/pull/523)).

### Fixed

- `build/reverify.py` reported a licence that differed from the record only in case, such as the
  Hub's `apache-2.0` against a recorded `Apache-2.0`, as a refutation. It now folds case the way
  tier matching does ([#655](https://github.com/currentai-org/os-ai-map/issues/655),
  [#690](https://github.com/currentai-org/os-ai-map/pull/690)).
- Equivalence recall in the identity eval counted `pool` candidates, which no tier scores, in its
  denominator. That made the relation's recall floor unreachable rather than unmet: the gate armed
  for the first time when the ledger crossed `MIN_TRUTH` and failed at a value it had held all
  along. Measured over the candidates the corpus declares, recall reads 1.000. Resolving an
  undeclared artifact to an existing product is now reported separately and never graded
  ([#638](https://github.com/currentai-org/os-ai-map/pull/638),
  [#646](https://github.com/currentai-org/os-ai-map/pull/646)).
- The Details payload crossed marimo's 8&nbsp;MB per-cell cap and is now delivered across four
  carrier cells; the canary that asserted it was over the cap was asking the wrong question once the
  prose rewrite brought it back under, and the regenerating workflow now runs the payload tests it
  had never run ([#615](https://github.com/currentai-org/os-ai-map/pull/615),
  [#623](https://github.com/currentai-org/os-ai-map/pull/623)).
- The failure sentinel watches every workflow that runs unattended on `main`. It watched nine and
  four ran without it, including the weekly adoption reconciliation, which dates adoption axes and
  raises a tier-change queue; a silent failure there looks exactly like a week with nothing to
  report. The list
  must be literal, so a test now holds it answerable to the workflows
  ([#631](https://github.com/currentai-org/os-ai-map/issues/631),
  [#642](https://github.com/currentai-org/os-ai-map/pull/642)).
- `build/prose_edit.py` warns when a note says what the **record** used to say rather than what the
  product used to be. It warns and does not refuse: the distinction cannot be drawn by pattern, since
  the phrase in the one real instance is also an ordinary verb phrase
  ([#632](https://github.com/currentai-org/os-ai-map/issues/632),
  [#643](https://github.com/currentai-org/os-ai-map/pull/643)).
- The `PLATFORM MIRROR` banner is gated against the manifests, so a file claiming platform ownership
  and a manifest claiming repo ownership can no longer disagree silently
  ([#626](https://github.com/currentai-org/os-ai-map/pull/626)).
- A record disputing GitHub's licence classifier must cite the licence text it read
  ([#613](https://github.com/currentai-org/os-ai-map/pull/613)).
- Both Jina records scoped to the text line on every axis. `jina-embeddings` declared v4 and v5-omni
  in its scope while its artifacts, license compound and download sum excluded them; `jina-reranker`
  had the mirror-image defect and counted the multimodal `m0`. Neither score moved
  ([#540](https://github.com/currentai-org/os-ai-map/pull/540)).
- `edit-category` and `update-product` name the pytest gate, which neither did — a category or
  product edit can break a pinned test without failing any `build.*` check
  ([#534](https://github.com/currentai-org/os-ai-map/pull/534)).
- `reverify` addresses a source entry by position rather than by URL, so an axis citing one page
  twice under different `establishes` lists — legal, and 55 (product, axis) pairs do it — can no
  longer have a confirmation stamped onto the wrong citation. That defect is why the reverify
  workflow had a single run in its history and it failed
  ([#528](https://github.com/currentai-org/os-ai-map/pull/528)).

### Removed

- The third-of-a-category rung rule, from `docs/reference/capability.md`
  ([#611](https://github.com/currentai-org/os-ai-map/pull/611)).
- The `refresh-data` workflow and its weekly cron. Both fetchers it ran were deleted when ADR-003
  externalized the `catalog.*` tables, so every scheduled run since had failed
  ([#509](https://github.com/currentai-org/os-ai-map/issues/509)).

## [0.3.0] - 2026-09-05

Moved discovery off hand curation, and built the identity graph and Postgres serving layer
underneath it — **616 products across 18 categories**, from **348 organizations**.

### Added

- `mirror.code_unchanged_from` in `warehouse/dependencies.yaml`: a marker letting a mirror contract
  record a platform revision that was minted over byte-identical code (a cron cleared, a
  description added), which the coherence gate would otherwise forbid forever. Accepted only when
  the marker names the revision committed at the merge base, the revision strictly advances, the
  mirrored bytes are unchanged and `synced_at` does not regress; setting it alongside changed bytes
  is itself a violation, so the next genuine resync deletes the line (#489).
- A per-route handle-coverage metric in `build/identity_eval.py` — for each of `github`,
  `huggingface` and `homepage_domain`, how many of the orgs owning artifacts on that route declare
  the handle it needs — with a baseline ratchet in
  `tests/fixtures/identity_coverage_baseline.json` (github 211/299, huggingface 2/61,
  homepage_domain 6/27). Any scoring run exits 1 if a route's live ratio falls below its pinned
  ratio, so coverage can only go up; `--write-coverage-baseline` re-pins the file deliberately.
  Target floors wait on the Hugging Face handle review (#487, #491).
- `build/propose_org_handles.py`, which proposes `huggingface` org handles from the namespaces of
  already declared Hugging Face artifacts, grouped by org and checked for aggregator accounts and
  ownership conflicts, for review as a GitHub issue rather than seeded silently (#484).
- A weekly mirror-drift sentinel (`mirror-drift.yml`, Monday 08:30 UTC): every `mirror:` contract
  in `warehouse/dependencies.yaml` is compared against the platform's latest revision, and a red
  run is picked up by `report-failure.yml`, which opens or comments on the `sentinel` issue.
  Reports revision, hash, code, metadata-only and missing-model findings separately, and exits 2
  rather than passing whenever the platform cannot be read at all. A newer platform revision over
  byte-identical code is `metadata-only` and exits 0; a hash change at an unchanged revision
  number stays drift however well the code matches. Closes
  the gap where the repo's own gates stay green while the platform releases past a mirror; the
  first runs found eight of seventeen contracts behind. "Mirror resync" in
  `docs/operations/deploy-models.md` is the runbook (#486).
- `build/publish_neon.py` loads the gap map into Neon (Postgres) as the `os-ai-map` schema, so
  the site can read products, scores and freshness dates at request time instead of loading
  `build/notebook_data.json`. The tables are the target model from CLEVER FRANKE: products,
  the three axes, sources, lineage, categories, layers, stages, gaps, aliases and long tail.
  The model's primary keys,
  `NOT NULL`s, uniques and foreign keys are enforced by the database, so a load that would serve
  a dangling id fails instead. Five enums are enforced too, and an unmapped payload value fails
  the load rather than being coerced. It runs in
  `registry.yml` on every push to `main`, one step after the OSO publish, and needs the
  `NEON_DATABASE_URL` secret. The load is atomic: rows go into `os-ai-map_staging` and the
  cutover is two schema renames in one transaction, so a reader mid-request sees the whole old
  schema or the whole new one. Nothing is dropped in that transaction: the old schema is
  reclaimed at the start of the next run, and only after `pg_depend` shows nothing outside the
  publisher's own schemas depends on it, because `CASCADE` follows dependencies rather than
  schema membership. The gallery tables are not published at all — they are CMS-authored, and a
  schema rebuilt from source cannot hold rows it did not produce. A `publish_runs` row records the commit, the schema version, the
  build and release dates and the per-table row counts of each load. The table set, grain and
  types live in `build/neon_schema.py`, which is the one place to change them. After the load,
  `build/neon_status.py` connects again and writes the table and row counts a reader now sees,
  the constraint tally and the `publish_runs` row, to the run summary;
  `gh workflow run registry.yml --ref <branch>` runs the same load from a branch, with the OSO
  publish guarded on `push` to `main` so a dispatch never reaches it (#485).
- An explicit `reclaimed-as-dependency` transition in the externalization receipt, so a table that
  an in-scope governed asset starts reading again moves from externalized back into the governed
  dependency graph as a recorded event instead of an edited record. The disposition history is
  append-only (in-scope → externalized → reclaimed-as-dependency) and gated: the reclaim must name
  the prior entry, an in-repo reader that genuinely reads the table, and a dependency contract with
  a mirror block (#481).
- A weekly digest issue of low-confidence identity items (`identity-digest.yml`, Monday
  09:00 UTC): membership, equivalence, and org edges the identity graph could not auto-emit,
  capped at 25 a week, each with a pre-filled ledger entry ready to paste into
  `sources/resolution_ledger.yaml` once decided (#479).
- The digest renderer now reads the table's own `rank` and never re-sorts: items render in
  `currentai.identity.digest`'s rank order, grouped by relation for reading but each carrying
  its global rank, with a "Top 5 this week" summary at the top; `evidence` renders as linked
  bullets instead of bare method names, parked items collapse to a per-relation count, and the
  scorecard gets a fourth line breaking the ranked set down by relation (#490).
- Organization platform handles (`sources/org_handles.yaml`) and model release-name families
  (`sources/model_families.yaml`), published as `registry.org_handles` and
  `registry.model_families` — declared identity evidence for who owns which account and which
  release names bridge to which tier-level product (#474).
- Per-product `overall_score` and `tier` (`leading` for score ≥ 4.5, `strong` for
  4.0 ≤ score < 4.5, else `null`) fields, a `depth` category gap that fires at Stage 4, and a
  `descriptions.tiers` legend in the payload (#87, #318).
- `build/identity_eval.py`: replay eval that scores the `currentai.identity.*` edge tables
  against prior human decisions (the resolution ledger, declared artifacts, org rosters, and
  a known-negatives set), with precision floors on the four relations automation is planned
  for and recall floors on three of them — checked only once a relation has at least 20 truth
  items. `org` recall is a regression invariant instead (≥ 0.99, graded on live runs only),
  since its truth is restricted to the pairs a declared handle can bridge, and per-route
  handle coverage is the coverage metric in its place. Two rules are
  pinned as tests rather than metrics: a name-match edge never auto-emits (checked against
  `method` as an array, matching the deployed SQL) and a scoring-bearing membership edge
  never auto-emits regardless of confidence. Truth is built from DECLARED (head/tail)
  artifacts only, so `equivalence`, `org` and `artifact_identity` — sourced from every tier,
  head/tail/pool — split on their `candidate_tier` column: precision/recall are computed over
  the declared slice truth covers, and `n_emitted_at_threshold`/the review digest are
  computed over the pool slice automation would actually act on. Scheduled weekly as
  `identity-eval.yml`, which runs a fixture on every PR and
  `--from-warehouse` on schedule — `--allow-unprovisioned`, which the workflows no longer pass,
  skips cleanly (exit 0) only
  on a genuine missing-table error (matched against Trino's own live wording, verified against
  `currentai.identity.equivalence_edges` while undeployed: a live `--from-warehouse` run now
  exits 0 as intended) while the identity dataset is undeployed, exits 2 on any other failure
  (auth, timeout, a missing column, an unrecognized `candidate_tier`/`product_tier` value),
  and refuses to run at all once `warehouse/assets.yaml` marks the dataset deployed (#476).

### Changed

- Resynced five drifted mirrors against the platform's released revisions:
  `currentai.scores.openness_facts` (7 → 9),
  `currentai.scores.openness_computed` (15 → 17) and `currentai.signal_github.artifact_state`
  (2 → 3) now record the deployed revision (#488).
- Every surrogate `id` in the Neon serving layer is now derived from the row's natural key —
  the first 63 bits of `sha256("<table>:<key>")` — instead of from its position in a sorted
  list. Adding one product used to renumber every row after it, so an id that had reached a
  URL, a cache or a CMS reference pointed at a different product after the next publish. The
  id and foreign-key columns widen from `integer` to `bigint` to hold the hash, the publish
  fails naming both keys if two ever collide, and the ordinal the old ids carried moves into
  `layers.sort_order`, `categories.sort_order`, `long_tail_top.sort_order` and `stages.num`.
  `schema_version` is 3. The slug stays the canonical identity for links and for anything
  another system stores (#496).
- Reclassified `org` recall in the identity eval from a coverage floor to a regression invariant at
  ≥ 0.99, graded on live runs only. Recoverability is decided by the same handle route the graph
  emits on, so recall answers "does the resolver use the evidence we gave it" and never "have we
  given it enough" — the eval labels the row `recall invariant`, and per-route handle coverage is
  what measures reach. Org precision keeps its 0.97 floor (#482, #491).
- The identity digest no longer resurfaces a parked item on age, or reports an item's age. The digest
  table has no observation history behind it — `first_seen` dates the snapshot, not the discovery —
  so the parked line promises only that an item returns when its evidence gets stronger, the
  scorecard's oldest-unresolved-age line says the history does not exist yet, and `evidence` is the
  only resurfacing reason in the vocabulary (#491).
- Dropped `--allow-unprovisioned` from the `identity-eval` and `identity-digest` workflows now
  that the identity dataset is deployed and contracted. Both modules refuse the flag once a
  `currentai.identity.*` contract with a `mirror` block exists, so a missing table is a real
  failure again rather than a green skip (#480).
- Split the labour between stage and gap text: a stage says where a category stands, a gap says
  what it needs. They render together in the category drawer, and written in one mood they
  restated each other — `depth` fires if and only if the stage is 4, so both sentences carried
  the same fact (#87, #321).
- Took the record's own scoring history out of score notes - "RE-BANDED 2026-08-14", "Class
  corrected from open_core on 2026-07-30", "LEVEL CORRECTED 3 -> 2". The reasoning behind each
  correction stays, in the present tense; the chronology goes to git, which already holds it with
  the diff and digests that produced it. A note may no longer state a date at all, enforced by
  `test_no_note_states_a_date_unless_it_is_a_product_fact` against a reviewed allowlist of 26 axes
  whose dates are facts about the product rather than about the reading (#322, #323).
- Rewrote the stage and gap definitions the payload carries — the text rendered in the site
  legend and category drawer. Stage 4 and the `depth` gap no longer define each other, the
  `adoption` gap no longer defines itself by its own threshold, and the `disclosure` gap no longer
  ships a repo path to the public payload. `docs/reference/gap-analysis.md` and
  `docs/methodology.md` now quote these definitions verbatim, with thresholds and assignment rules
  kept alongside rather than restated, and a test enforces the match (#87, #320).
- Split the `maturity` category gap into `depth` (Stage 4) and its `capability`/`adoption`
  drivers, which now fire together wherever both apply, and redefined the `adoption` gap
  independent of capability (#87, #318).
- `registry.tail_products` now includes homepage-bearing tail rows, previously silently dropped
  even though they validated (+27 rows; every one is a tail product that already declares
  another artifact kind, none homepage-only) (#472).
- Consolidated GitHub/PyPI/npm/crates/arXiv/Hugging Face artifact-identity canonicalization,
  previously duplicated and drifted across three modules, into one (#472).
- Brought all seven deployed `currentai.identity.*` models under repo governance (ADR-003):
  read-only mirrors under `warehouse/models/identity/`, plus dependency contracts pinning each
  model id, released revision and file hash, so `build/identity_eval.py`'s and
  `build/identity_digest.py`'s inputs are versioned, hashed and reviewable. Mirrored the three
  pool feeds (`signal_hfhub.model_universe`, `signal_openrouter.models`,
  `signal_goodailist.repo_catalog`) the same way, since the dependency gate requires a mirror
  for every `currentai.*` input a governed reader reaches (#480).
- Recorded `currentai.signal_goodailist.repo_catalog`'s return to the dependency graph as a
  `reclaimed-as-dependency` event in `warehouse/audits/externalization.json`: the identity
  graph's `artifact_nodes` model reads it, so it is contracted again while the original
  externalization entry stays byte-identical as history (#481).

### Deprecated

- The per-product `maturity` and `mature` keys, dual-published for one release so consumers can
  migrate before removal. Replacements: `maturity` → `overall_score`; `mature` →
  `tier == "leading"` and `openness.bucket == "open"` (#87, #318).

### Removed

- The `maturity` gap type (#87, #318).

### Fixed

- `homepage` artifact identity now keys on the full canonical URL (host and path), not the bare
  domain — two products sharing one company's domain at different paths are no longer treated as
  a collision. A shared domain is corroborating evidence of ownership, never proof of identity;
  it never establishes equivalence between two candidates and never suppresses a second one.
  `registry.tail_products` homepage rows now carry that full URL in `artifact_id` (#477).
- `registry.product_artifacts`'s `crates` `artifact_id` now serializes the bare crate name
  instead of the full crates.io URL (one row: `yomo`) (#472).
- The resolution ledger now keys a `product_membership` ruling on the product it names
  (`resolves_to`), not on the artifact alone. One package can legitimately be `member_of` one
  product's measurement and `not_member_of` another's — the loader used to raise
  `DuplicateResolution` on that legitimate case. `registry.resolution_ledger`'s grain moves to
  one row per `(artifact_kind, artifact_id, relation, resolves_to)` to match (#478).


## [0.2.0] - 2026-08-16

Grew and re-verified the corpus end to end, on top of a new evidence-based scoring pipeline.

### Added

- **One new category** (Dataset Processing Tools) and **85 products** — a net gain of 14
  after consolidation — bringing the map to **472 products across 16 categories** and 257
  organizations.
- **Scoring ladders:** a shared openness ladder for software across ten categories, shared
  ladders for datasets and hardware, per-product-type variants, and a single license scale
  used everywhere (#126, #129, #131, #137, #139).
- **An adoption measure** with per-product-type bands, declared scales, and readings backed
  by real usage signals (#171, #175, #176, #224, #227).
- **Evidence-based scoring:** openness scores are now computed from recorded evidence
  instead of being hand-authored — a machine-readable scoring rubric, an evidence store,
  and computed scores brought back into the repo for review (#98, #101, #102, #103, #108).
- **Automated verification checks** for verification-date support, source attribution and
  digests, sampled refetch reproducibility, and score reproduction from the declared rubrics
  (#127, #128, #134, #136, #148).
- **Structured openness and license records,** converted across the whole corpus, with each
  license part recorded as its own piece of evidence (#185, #186, #191–#198, #216, #217).
- **A routing table** naming the authoritative source for each scoring dimension (#103),
  and freshness reporting behind a 30-day refresh window (#102, #162, #267).
- **Artifact tooling:** an arXiv artifact type, a tool that proposes candidate artifacts,
  and a check that declared artifacts resolve to what they claim (#100, #104, #165, #170).
- **Skills:** `refresh-category` and `refresh-all-categories` to drive the re-verification
  pass (#158).

### Changed

- **Re-verified all 472 products** against named, reopenable evidence, preferring primary
  sources where available — 385 product records and their scores updated — and edited all 15
  existing categories.
- **Made product descriptions neutral** rather than marketing copy, under one standard for
  the description and comments fields (#147, #222).
- **Consolidated closed-model point releases** into the tier the vendor sells and fixed each
  product's identifier so it stays stable; alternate names now live on the records they
  identify (#114, #121, #157).
- **Reorganized the docs** into five task-based workflows over a shared reference layer, with
  a check that keeps them consistent and a skill registry (#269, #271, #274).
- **Added a read-only copy** of the scoring and signal models that run on the OSO platform,
  so they can be read from this repo (#272).

### Removed

- **Retired or consolidated 71 product entries** — collapsing point releases into vendor
  tiers and dropping projects that were renamed or shut down.
- Replaced the frozen GoodAI List CSV with a live data feed, and removed warehouse CSV files
  that nothing used (#110, #309).
- Removed an openness class the schema forbids, obsolete prose-cleanup tooling, historical
  snapshots, and dead build code (#178, #179, #306, #310).

### Fixed

- Corrected score, license, and adoption records against reachable evidence across the
  corpus (#204, #215, #226, #255, #260).
- Dated each score file from its last content change, not its last file touch (#190).
- Stopped the score-import step from overwriting the "last verified" date through a stale
  cache, and reverted the dates it had written (#115, #124).
- Reconciled the verification tracking file and restored nine deferred items (#301).

## [0.1.0] - 2026-07-01

Initial release: the first full snapshot of the AI Stack Map corpus, at the start of July —
**458 products across 15 categories**, from **249 organizations**, each scored on openness,
adoption, and capability. Tagged at commit `2e9d6eb`.

[unreleased]: https://github.com/currentai-org/os-ai-map/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/currentai-org/os-ai-map/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/currentai-org/os-ai-map/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/currentai-org/os-ai-map/releases/tag/v0.1.0
