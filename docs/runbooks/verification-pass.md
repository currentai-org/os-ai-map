# Runbook: getting every score auditable

Executable plan for reaching the state where every score can be re-derived from evidence, and
the failure modes this project has actually hit are prevented by a mechanism rather than by
remembering.

> **Read `docs/guides/verification.md` first.** It is normative: what `last_verified` means,
> who may write one, the `establishes` invariant, and the gate table. This runbook is only
> the order of operations and the commands.

**Definition of done.** Not "every axis has a date." It is:

1. Every axis claiming a confirmation satisfies the invariant — every recorded dimension has
   an establishing source re-read on or after the claimed date. Gated.
2. Every score/class pair is producible by its category's rubric. Gated.
3. `check_rubric` reproduces 16/16 categories, and the warehouse agrees per product. Gated.
4. Every date traces to a fetch with a status and a digest. Gated.
5. The remaining gaps are enumerated in `deferred` with reasons, not silently absent.

A date on every axis is the *by-product*. Chasing coverage first is how the field got
corrupted twice already.

---

## Phase 0 — Build the gates, before any volume work

Do this first. Everything after it is bulk edits to `sources/scores/`, and gates written
afterwards would be gates written to fit whatever the bulk edits happened to produce.

> **0.1 to 0.4 have landed.** `build/check_verification.py` runs in `validate.yml`, and all
> three gates pass. Two things went differently from what is written below and are worth
> knowing before following it:
>
> - **The producible-pair check caught 17 impossible pairs, not 2.** `vellum` and `whylabs`
>   were the known ones. `tensorrt-llm` made a third `4 / open_source`, five products were
>   `2 / open_core`, and nine carried a score of 3, which the software ladder cannot emit at
>   all. All were fixed as score corrections. `docs/guides/verification.md` has the three
>   groups and the reasoning. The ladder was not touched.
> - **The exemption list for the digest requirement is empty.** All 6 dated axes qualified
>   for it, and none of them satisfied the invariant either, because the 2026-07-28 pass on
>   the model flagships re-read only the dataset endpoint. Re-fetching the 23 cited sources
>   was 23 requests and it turned up two defects the exemption would have hidden. Exempting
>   stays the cheaper move and the mechanism is still there. It is not the better move when
>   the set is small.
>
> **0.5, the release assertion, has NOT landed.** It is the one Phase 0 item still open.

### 0.1 Schema: `establishes`, `http_status`, `content_sha256`

Add all three to `docs/schemas/score.schema.json` under `definitions.source`, **all
optional**. `establishes` is an array whose items must be dimension names declared by some
recipe — validate that cross-file in `build/validate.py`, or a typo'd dimension name silently
establishes nothing.

```bash
uv run python -m build.validate        # 0 errors, nothing populated yet
uv run pytest -q
```

### 0.2 `build/components.py` — the only supported components editor

Extract the block-safe rewriter: locate the `  components:` block including folded
continuation lines, rebuild it, re-parse the file, and assert both the new value and that
every other field is byte-identical. Port the callers.

Test it against a file whose `components` folds across three lines. A single-line regex
passes such a test only by accident, which is why the test matters more than the helper.

### 0.3 The three free gates

Put all three in `build/check_verification.py`, one command, wired into `validate.yml` next
to the existing test step.

- **The invariant.** For each axis carrying `last_verified: D`: every dimension the score
  records has ≥1 source with `establishes` naming it and `accessed >= D`. Scope: axes with a
  date only.
- **The digest requirement.** Same scope: every establishing source has `http_status` and
  `content_sha256`. Exempt dates predating this runbook by listing them explicitly, so the
  exemption is visible and shrinks.
- **The producible-pair check.** For every scored product in a category with a recipe,
  `(score, class)` must equal the outcome of some rule in that recipe. Full scope,
  immediately.

```bash
uv run python -m build.check_verification          # expect producible-pairs to FAIL first run
```

The producible-pair check will fail on `vellum` and `whylabs` (`4 / open_source`) and possibly
others. **Fix those scores before landing the gate.** Each is a real error, and one of the two
recorded values is wrong in each case. Resolve by reading the product, not by adjusting the
rubric to admit the pair.

### 0.4 The nonce-forcing query helper

One place that builds warehouse queries and appends `-- cache-bust <uuid4>`. Warehouse
results cache on query text, so a fixed verification query returns its first answer forever;
this has already caused a tool to report success against pre-materialization data. Port
`apply_scores.fetch_computed` and any verification script onto it.

### 0.5 The release assertion

`build/publish_registry.py` (or the runbook step around it) asserts, for every UDM it depends
on, that `latestRevision.revisionNumber == latestRelease.revision.revisionNumber`.

A run materializes the latest **released** revision. Creating a revision changes nothing
until `createDataModelRelease` points at it, and the symptom is "my change had no effect"
rather than an error — three runs were spent on that, concluding a column drop had broken
materialization when the new SQL had never executed. See `docs/operations/deploy-models.md`.

**Exit criteria for Phase 0:** `check_verification` passes, `validate.yml` runs it, the
components helper has the folded-scalar test, and what the producible-pair check caught is
fixed as score corrections.

---

## Phase 1 — Finish the recipes: 16/16 categories, 472/472 products ✅ done 2026-08-01

111 products, four categories. Do this before Phase 2 or the SQL generalization gets done
twice.

| category | n | type | notes |
|---|---|---|---|
| `benchmark_eval_data` | 27 | dataset | one new ladder covers both dataset categories |
| `training_synthetic_datasets` | 38 | dataset | |
| `edge_hardware` | 20 | hardware | own ladder; version-in-identity applies |
| `safeguards` | 26 | **mixed** 9 model + 17 software | do last, changes the machinery |

Method per category, the one proven on `deployment` and the nine software categories:

```bash
# 1. Survey what is actually recorded before designing anything.
#    Software components turned out to be prose with 213 distinct keys; the model
#    categories were structured. Do not assume which you have.
uv run python -m build.check_rubric --category <slug>

# 2. Derive each dimension from the recorded prose WITHOUT looking at the score, apply
#    the ladder, compare. Agreement is corroboration; normalize only those.
# 3. Hold the rest in `deferred` with a real reason (>40 chars; a test enforces it).
# 4. Verify.
uv run python -m build.check_rubric && uv run python -m build.validate && uv run pytest -q
```

Two rules learned the hard way:

- **Never trust a regex classification.** A first pass got 3 of deployment's 27 wrong:
  `sandbox-runtime` says "no managed/**proprietary** tier", `openpcc` calls its commercial
  service "**separate**", `webcontainers` publishes a repo but no runtime source. Most
  gated-sounding words in this corpus sit inside negations. Use the regex to triage, read to
  decide.
- **Use `build/components.py`.** See 0.2.

`safeguards` is the interesting one: being the only mixed-type category, `extends` must become
per-product-type rather than per-category. That forces extracting the model ladder to
`sources/rubrics/model.yaml`, which finishes the de-duplication that
`sources/rubrics/software.yaml` started.

**Exit criteria:** `check_rubric` reports 16/16 `[OK]`, every deferral carries a reason, no
category's stage or gaps moved (diff the serialized output before and after).

---

## Phase 2 — Generalize the scoring SQL, once ✅ done 2026-08-05

Landed as two models. `docs/guides/verification.md` step 2 carries the full account; this is
the operational half.

`currentai.scores.openness_computed` resolved `weights`, `data`, `code` and `license` by name,
so 13 of 16 categories produced no rows. It now reads
`currentai.registry.category_dimensions`, the ladder's own declaration. **470 rows, 384
scored, zero divergence from `check_rubric`.**

What shipped:

1. **Dimension-generic resolution**, in a new `currentai.scores.openness_facts` — one row per
   (product, category, declared dimension), which is also the audit chain's dimension link.
   The split was forced: one query hit 174 Trino stages against a ceiling of 150.
2. **`dims_recorded` and `all_recorded_dims_from_dataset`**, the denominator Phase 3 needs.
3. **`category_deferrals`**, plus `category_dimensions`. Deferred products keep a row, carry
   the recorded reason, and are never walked through the rules.

### The refresh order, which is not optional

The three user models now carry weekly crons — `evidence.product_evidence` Monday 03:00 UTC,
`scores.openness_facts` 04:00, `scores.openness_computed` 05:00, with the parity gate grading at
06:00 — so the warehouse is at most a week behind the repo on its own. **A publish is still only
the first half of a refresh**, and on a weekly cadence that matters more rather than less: merge
on Tuesday and the map carries the old numbers until the following Monday unless you walk the
chain below. Do that whenever a merge changes a score, rather than waiting.

Getting this wrong looks exactly like a code bug: the first run of the generalized SQL reported
three categories missing entirely, and the cause was `product_evidence` sitting three recipes
stale — from before the slug collapse in #121, so it still held 47 orchestration products
against the repo's 36. That was with nothing scheduled at all; a weekly cron caps that at a week,
and changes nothing about the next ten minutes.

**What the crons do NOT refresh: the signals themselves.** `signal_huggingface.hub_state` and
`signal_github.repo_state` are still `@manual`, so the chain recomputes the same fetched facts
every Monday. Scheduling those is a bigger decision than a cron expression — it is the point at
which scores start moving on their own, which is what `apply_scores --check` exits non-zero
for and what the review digest in the autopilot design exists to handle.

```bash
# 1. push the declarations, and wait for the static models to materialize
uv run python -m build.serialize_rubric && uv run python -m build.publish_registry

# 2. refresh the user models IN ORDER, waiting for each: they do not cascade
#    evidence.product_evidence -> scores.openness_facts -> scores.openness_computed

# 3. revision -> RELEASE -> run, for a model whose SQL changed. The middle step is the
#    one that gets forgotten, and a run without it executes the previous release.
#    NOTE: deploy_udm.py and the .sql files are NOT in this repo. They sit one level up,
#    in currentai-org/{tools,udms}/, which is not under version control at all — so run
#    this from that directory, and treat the SQL there as the only copy that exists.
#    Folding both into warehouse/udms/ is tracked as T1 of the 2026-08-14 audit.
cd .. && uv run python tools/deploy_udm.py --dataset scores --model openness_facts \
    --sql udms/scores_openness_facts.sql

# 4. prove it
uv run python -m build.check_parity
```

Two things about step 2 that are easy to get wrong, both of which cost hours on 2026-08-08:

- **Per-model refresh is not reachable over MCP without the model UUIDs.**
  `createUserModelRunRequest.selectedModels` takes UUIDs, not names: passing
  `"openness_facts"` fails with `invalid input syntax for type uuid`. Without the IDs to hand,
  the only path is a whole-dataset run, which does work and preserves topological order, but
  pulls in eight unrelated `scores` models and takes about four minutes against roughly ten
  seconds targeted.
- **Verify a run from the data, not from the run status.** A `scores` run reports RUNNING for
  minutes after its early models have already committed. Query `MAX(last_checked)` through
  `build/warehouse.py` — which forces the nonce, without which you read the pre-materialization
  answer back out of the query-text cache.

### The parity gate

`build/check_parity.py` compares `check_rubric`'s local verdict against
`currentai.scores.openness_computed` for every product, and fails on any divergence. It runs
weekly in `.github/workflows/parity.yml`, Monday at 06:00 UTC, behind the three models it grades.

This is the mechanism for the failure mode that bit four times in one day — `check_rubric` and
the SQL mirror each other's logic by hand and drift silently. Every one of those four was
caught by per-product comparison and none by a local check, and the gate's first run caught a
fifth: `license:none` resolving to a tier through check_rubric's definitional fallback and to
nothing at all through the warehouse's lookup table.

It is not in `registry.yml`, on purpose. Chained onto a publish it would compare fresh rules
against the un-recomputed warehouse of step 2 above and fail for a reason that is not a drift.

**Exit criteria:** all 16 categories score in the warehouse, `check_parity` passes, and the
deferral count in `category_deferrals` matches the repo's.

---

## Phase 3 — The automated pass, ~400 axes ✅ done 2026-08-13

Adoption and capability only, and only where every recorded dimension is signal-derived
(needs Phase 2's column). The date is the signal fetch date; the establishing source is the
signal's URL, with the digest captured at fetch time.

No reading and no judgment, which is why it can run unattended — and exactly why it must be
fenced to those axes. Openness is excluded permanently: `data` is research-only in
`signal_routing.yaml`, the GitHub code route is `settles_dimension: false`, and software
`core_gated` needs a pricing page.

```bash
uv run python -m build.check_verification    # invariant and digests now cover ~400 more axes
uv run python -m build.check_freshness       # coverage should jump
```

**Exit criteria:** every axis it touched satisfies the invariant and the digest requirement,
and `check_freshness` reports them as `verified` rather than `commit`.

---

## Phase 4 — The re-read pass, ~1106 URLs ✅ done 2026-08-14

All 1416 axes now carry a real `last_verified` (median age 1d, oldest 6d). What follows is the
standing procedure for re-running the pass, not outstanding work.

Everything else, all of openness included. **Fold the held-back products in rather than clearing
them first** (5 across 4 categories as of 2026-08-14) — reading a product's sources to settle
`core-gated` *is* the re-check that earns its date. Two passes means the same pages fetched twice, on scores about to change.
(`check_recipe` prints the current deferral count per category; regenerate it rather than
trusting the number here.)

**The prose comes with it.** The pass refreshes a product's `description` and `comments` to
`docs/reference/product-copy.md` in the same unit of work, for the same reason the deferral
backlog folds in: refreshing the prose means opening the repository, model card and vendor docs
this phase already fetches. Run separately it is the same pages twice — and worse, a prose pass
that does not open primary sources produces a provenance line naming a *method*
(`Verified 2026-08-08 via web search`), which is how seven products acquired one in #147.

The unit of work is therefore per product, not per axis:

1. **Read what the warehouse already has** before fetching anything — the signal row carries
   `http_status`, `license_*`, `is_archived`, `is_gated`, `downloads_30d` and `fetched_at`.
2. Fetch each cited URL a signal does not already cover; record `http_status`,
   `content_sha256`, and a `shows` extract that actually appears in the body. A cited URL that
   404s is a finding, not something to paper over — and so is a cited figure that no longer
   appears in a page which still resolves. One product in the 2026-08 sweep cited a leaderboard
   position that had ceased to exist at all, on a URL returning 200.
3. Re-derive each recorded dimension and attribute it: `establishes: [...]`.
   On capability, that means the peer comparison: if the band was placed against another
   product, record it as `relative_to` + `relation` rather than leaving it in the note, and
   confirm the peer at least as recently. A capability date attests to less than the other two
   axes — `verification.md`, "What a capability confirmation attests to", says exactly what.
4. **Rewrite the prose** per `product-copy.md` — `description` load-bearing and within the
   length band, `comments` a footnote ending in the canonical verification line. Delete rather
   than research a superlative, a corporate event, or a curator rationale clause; the guide's
   claim-class table is the rule.
5. If a value moved, that is the valuable output — fix the score and say why in `note`.
6. Stamp `last_verified` only once every recorded dimension has an establishing source.
   Otherwise `deferred` with a real reason. Never both, and never silently absent.

**Order the batch anchors first, which is not optional.** `check_capability` enforces transitive
freshness: a band recording `relative_to: X` may not claim a `last_verified` more recent than
X's, so an anchor confirmed yesterday fails a band dated today. Find the anchors inside the batch
with `grep -l relative_to sources/scores/*.yaml` intersected with the roster, and date them in the
same run.

**Four rules a pass may not bend.** Each of these is a defect this project shipped rather than a
precaution against one.

1. **Never invent a digest.** The only thing that produces a `content_sha256` is
   `uv run python -m build.fetch_source <url>`, and what it prints is the full 64 characters.
   Three were fabricated on 2026-08-13 by padding truncated prefixes out to full length. If a URL
   cannot be fetched, record no digest for it and leave the axis undated.
2. **`accessed`, `http_status` and `content_sha256` travel together** on the same source. A fresh
   `accessed` with nothing under it fails `check_verification`, so re-dating a source and
   digesting it are one edit rather than two.
3. **An unreachable host says nothing about whether the fact is true.** A 403, a 429 or a dead URL
   means the axis stays undated and the host gets reported. It never means the value is wrong.
4. **A plain YAML scalar cannot contain `": "`.** Write ` - ` instead, or single-quote the whole
   scalar. This cost four separate parse failures in one day.

**A null axis is a finding, and it earns a date too.** `level: null` over a note saying no figure
is published is a deliberate abstention rather than missing work. Re-read the page, confirm
nothing has appeared, and date it — citing the page that publishes nothing and saying in the note
what was looked for. `verification.md`, "A null axis can earn a `last_verified`", is the rule
(#236).

Batch by category so `check_rubric` gives a clean signal per batch, and run
`check_verification` after each batch rather than at the end. The full gate list for a batch is
step 6 of `skills/refresh-category/SKILL.md`, and that is the only copy of it. One PR per
category, prose and scores together, with every moved score itemized against its evidence.
Categories go in order of **worst signal coverage first**, so no manual reading duplicates what
Phase 3's write-back would have earned for free.

**On agent execution.** This is 1106 fetches and it is the step most exposed to
rubber-stamping — an agent that "confirms" without reading would reproduce #108's failure at
fifty times the scale while looking legitimate. Three things make that not work: the invariant
requires the `accessed` bump on every dimension, the digest requirement requires a digest that
only fetching produces, and the sampled re-fetch goes back to the network for a sample and
compares. Do not relax any of the three to make a batch finish.

### Running the pass in parallel

One agent per category, several categories at once, is what closed all 472 products between
2026-08-13 and 2026-08-14. `skills/refresh-category/SKILL.md` is the orchestration — the batch
shape, the concurrency cap, the research / audit / apply split, and the reading list each agent
gets. Four things belong to the agent rather than the orchestrator, and each is a defect the sweep
actually hit:

- **Namespace scratch files per agent.** The session scratchpad is shared. Two passes had a fetch
  log and a helper script overwritten mid-run by a sibling agent using the same filenames, and had
  to re-fetch everything to be sure the digests they were about to record were their own. Write
  only under a private subdirectory named for the category.
- **Touch only your own category's files** — `sources/scores/<member>.yaml` and
  `sources/products/<member>.yaml` for members of that category. Never `docs/`, `tests/`,
  `.github/`, `build/notebook_data.json`, `notebooks/`, or another category's products.
- **Escalate anything that moves a level.** Step 5 above says a moved value is the valuable
  output, and it is, but the agent that finds one is not the one who applies it. Escalate any
  change to a `score`, `level`, `class` or `reach`, declaring a new artifact, refusing an artifact
  that exists, an axis whose evidence is gone and needs new sources found, and anything you are
  guessing at. Then carry on: escalating one product does not block the other twenty.
- **Where the entity moved rather than the evidence, it is a curation call.** A product that
  merged, split into tiers or was renamed is `docs/reference/identity.md` work, not a re-read. Record
  the finding and leave the slug alone.

**The escalations are where the pass earns its money.** Agents refusing to date
`fireworks-inference`, `math`, `muse-spark`, `grok` and `doubao-seed` is how the sweep found
evidence that had quietly vanished. A batch escalating nothing is more suspicious than one
escalating five things.

When the escalation is an adoption re-band, `docs/reference/adoption.md`, "When a re-read may
re-band", carries the standing answers: measured signal against a hand-set band, `stars_fallback`,
relabelling to `reported_traction`, declaring a new artifact, and SDK attribution. Rule from there
rather than deciding it again per category.

**Expect scores to move.** The RWKV correction in #105 came out of a pass like this. Movement
is the return on the work, not a problem with it — `apply_scores --check` exits non-zero on a
moved score deliberately.

**Exit criteria:** every one of the 1370 real claims either carries a confirmed
`last_verified` or sits in `deferred` with a reason, and every product's prose satisfies
`product-copy.md`. Zero silently absent.

---

## Phase 5 — Close the ratchet

```bash
uv run python -m build.check_freshness --max-age-days 30     # the gate, run by hand
```

**The sampled re-fetch landed early**, in #148, because Phase 4 is the step it exists to police
and running that without it would be the rubber-stamp risk with nothing underneath it.
`build/check_refetch.py` re-fetches a sample and compares digests, weekly in
`.github/workflows/refetch.yml`. It reports drift rather than hard failing, since pages
legitimately change. A digest that **matches** is the proof — one that differs proves nothing on
its own.

**The age gate is on** as of 2026-08-14, at 30 days, weekly in
`.github/workflows/freshness.yml` rather than per-pull-request — it fails on the passage of time,
so nobody can clear it from inside an unrelated PR. `docs/guides/freshness.md` has the argument.

What remains here: drop the digest requirement's exemption list.

**Exit criteria:** the five definition-of-done conditions hold, and each is enforced by
something that runs without being remembered.

---

## Standing hazards

Every one of these has happened. They are not hypotheticals.

| hazard | tell | guard |
|---|---|---|
| Derived date sold as a confirmation | any aggregate of `accessed` reaching `last_verified` | `tests/test_apply_scores.py`; the invariant validates, never derives |
| Fabricated digest | a full-length `content_sha256` on a source nobody could fetch | only `build.fetch_source` produces one; the sampled re-fetch compares it |
| A re-dated source with nothing under it | a fresh `accessed`, no `http_status` or `content_sha256` | `check_verification`'s digest requirement |
| A parse failure from a `": "` in a scalar | `validate` cannot read a file the pass just wrote | write ` - `, or single-quote the whole scalar |
| Parallel agents sharing a scratch directory | a fetch log or helper script rewritten mid-run | one private subdirectory per category |
| A 404 read as a product being gone | a retirement resting on one dead URL | check the URL first: `arduino/app-lab` 404s, `arduino/arduino-app-lab` is public, GPL-3.0 and actively pushed |
| A marketing reorganization read as a withdrawal | the vendor site stops listing it; the docs still ship it | `snorkel-flow` was nearly retired off its marketing site while `docs.snorkel.ai` had it at v26.1 with an install guide |
| A test whose setup depends on the bug | the test dies when the bug is fixed | build the fixture; never borrow a live failing record, as `test_relabelling_to_reported_traction_does_not_buy_a_pass` did |
| Stale warehouse read | identical query text returning a pre-materialization answer | the nonce helper (0.4) |
| Unreleased revision | "my SQL change had no effect", no error | the release assertion (0.5) |
| Repo/warehouse drift | local reproduces, warehouse abstains | the parity gate (Phase 2) |
| Folded-scalar corruption | a components value with a key spliced mid-string | `build/components.py` (0.2) |
| Partial coverage overstating openness | most-restrictive over a subset of SKUs | already in the SQL: `skus_mapped = skus_reachable AND tiers_seen <= 1` |
| Bot-owned files in a PR | `generated-files-guard` fails | edit `sources/` only; the bot regenerates on merge |
| British spelling | `licence`, `penalised`, `labelled` | American English everywhere, including identifiers |

## Related

- `docs/guides/verification.md` — normative: the invariant, the gates, who may write a date
- `docs/guides/freshness.md` — normative: what `last_verified` means
- `docs/reference/adoption.md` — normative: the bands, the instrument vocabulary, and when a re-read
  may re-band
- `docs/operations/deploy-models.md` — revision → release → run
- `skills/refresh-category/SKILL.md` — the orchestration for one category of Phase 4
- `AGENTS.md` — the layer-2 loop and the evidence grading rule
