# Deploy `signal_packages`, then retire `signal_pypi` (maintainer, MCP write)

The npm/crates bridge of issue #314, and the two things that must happen around it: #348 before
the retirement, #517 after the deploy. The general deploy mechanic is
`docs/operations/deploy-models.md`; this is the order for this one change, which has an
irreversible step at the end and two constraints that fail silently if taken out of turn.

**Steps 1 to 3 were executed on 2026-09-13 and #314 and #348 are both closed.** What remains is
the irreversible drop, and #562 now carries its preconditions rather than step 4 here. Keep this
document for the order it records, for the three diff shapes, and above all for the determinism
lock at the end, which cost five models.

Model source is `currentai-org/udms/`, **not this repository** — `packages_package_downloads.sql`,
`packages_package_downloads_daily.py` and `packages_product_adoption.sql`. Nothing here is a
mirror to edit; see ADR-003 and the mirror table in `data-architecture.md`.

## The order

Each step's output is the next step's precondition. Only the last one cannot be undone.

1. **Done 2026-09-13. Republish the `registry` static model, by delete and recreate.** It gains a
   `not_primary_channel` column, and a static model cannot gain a column by re-upload — the
   multi-column ALTER fails, and the failure mode is a bare `PUT` or a `SignatureDoesNotMatch`
   rather than a clear error. Required for its own sake regardless: the deployed table has held
   `artifact_id = "https://crates.io/crates/yomo"` because `serialize_registry.py` carried no
   crates pattern, so the crates route could not have worked.
2. **Done 2026-09-13. Create the dataset and deploy the three models.** `createDataset` `signal_packages` as a
   `USER_MODEL`, then for each model revision → **release** → run. The release is the step that
   gets forgotten and the symptom is "my change had no effect", not an error.
   `createDataModelRevision` requires `cron`, `kind` and `schema` alongside the code, and the
   readers that return the code omit all three. Weekly is the house default.
3. **#348 — already done, check rather than do.** The precedence
   `pypi > huggingface > stars` is declared in `sources/signal_routing.yaml` and compiles into
   `registry.adoption_routes` as `route_order` with the stars route last and capped at 3. The
   blocker `data-architecture.md` §4.1 names — that the ordering lives only inside
   `signal_github/product_adoption.sql` and would be lost silently on retirement — **is met.**
   What is *not* true is that anything on the platform applies the ordering: the routes table
   records it, and the consuming model is a `UNION`. Verified 2026-09-13.
4. **Repoint the reader — currently impossible, and this is what blocks the retirement.**
   The deployed `signal_github.product_adoption` reads `currentai.signal_pypi.package_downloads`
   in its `already_measured` CTE, so the drop cannot happen until it reads the new table. It
   **refuses every new release**: "This release would change the model's schema-determinism
   verdict from its live release." That is not caused by the change being offered — a revision
   carrying code byte-identical to its own live revision was refused with the same error, which
   is the control that isolates the rule from the edit. Its upstream `signal_github.artifact_state`
   is a Python model with no `columns=`, which makes it a non-deterministic boundary sink; the
   consumer's live release predates that rule and is grandfathered, so any new release
   re-resolves and is rejected.

   **This step is void, and the remedy it proposed does not work.** An earlier draft said the
   fix was `columns=` on `artifact_state`. That was applied on 2026-09-13 and did not unblock
   the consumer; the release was refused again.

   A later draft of this document then said that change *caused* four more models to lock.
   **That was also wrong** and is retracted here rather than quietly deleted, because it is the
   claim a maintainer would have planned around. Those four were already unreleasable, along
   with a large share of the org, including datasets with no connection to the gap map. They
   were deleted and recreated, losing their materialized tables, schedules and model contexts —
   but not because of anything done in this step. See the determinism section below.

   The repoint this step asks for is not needed either. Issue #562 retires
   `signal_github.product_adoption` rather than migrating it, and you do not repoint a model you
   are deleting. What replaces this precondition is #562 step 3: `build/check_artifacts.py` and
   `sources/signal_routing.yaml` are the readers that must move off `signal_pypi`.
5. **Diff old against new**, per artifact and per product, before anything is dropped. Expected
   disagreements come in exactly three shapes (below). Anything outside them is a finding to
   explain, not a rounding difference to accept.
6. **Merge the repository side**, then flip `bridged: true` and drop `blocked_by`. A test fails
   the flip if it is done in the other order.
7. **Drop `signal_pypi`.** The only irreversible step in the sequence, and the one still
   outstanding. The precondition is no longer step 4 but #562 steps 3 and 4: every reader
   migrated, and the three shims given an explicit disposition. Dropping it while a reader still
   points at it would break that reader at its next scheduled run and let the stars fallback
   silently re-band every product that already has a download signal — the corruption this order
   exists to prevent.

## `not_primary_channel` exists now, and means something narrower than it sounds

Built in PR #563 on 2026-09-13, as step 1 of #562. It is an optional key on the artifact wrapper
in `docs/schemas/product.schema.json` whose value is the reason; `build/serialize_registry.py`
emits it as a column on `registry.product_artifacts`, and `build/adoption_measurements.py`
excludes a declared artifact from the summed figure. The artifact stays declared and its
observation stays recorded and readable per artifact — only the banded sum changes. Declared on
two artifacts: `hexabot`'s npm `@hexabot-ai/widget` and `yomo`'s crate `yomo`.

**It means the package measures a DIFFERENT POPULATION, never a smaller share of the same one.**
Hexabot's widget counts sites embedding a bot rather than deployments of the self-hosted
platform; YoMo's crate counts Rust builds linking the SDK rather than installs of a Go runtime.
A third product, `n8n`, was proposed for it on review and refused: npm is a minority install path
for n8n but the same population, and its own adoption note already counts those downloads toward
its level. Declaring it would have discarded a valid measurement to compensate for a channel the
warehouse cannot see at all — Docker, which has no artifact kind — and would not have worked
anyway, since excluding the package drops the product onto stars, which caps at 3.

## What the diff may legitimately show

Three shapes, and the port is deliberately not bit-identical:

- **Cross-registry summation.** A product with both npm and PyPI now sums them.
- **No-primary-channel abstention.** A package that is a minority channel for its product
  carries `not_primary_channel` and is excluded from the banded sum rather than counted.
- **Partial coverage.**

`signal_pypi` joined `registry.adoption_bands` on `product_type` alone; the successor joins
`signal_type` too. That was checked against every band row at the time and moved no band, so a
future difference there is a finding rather than a porting error.

## #517 comes after, and the deploy has now landed

The six governed assets wearing a read-only mirror banner are reclassified once this deploy
lands. Three of them — `signal_packages.downloads`, `downloads_daily` and `product_adoption` —
had **no governed reader until step 2**, and a dependency contract must be reachable from a
governed root. Reclassifying them first would have pushed them out of scope in *both* manifests.
Step 2 landed on 2026-09-13, so that trap has passed and #517 is unblocked.

Read #562 before actioning it anyway. The asset set moves again when the three
`signal_*.product_adoption` shims retire, and `signal_packages.product_adoption` has since been
reclassified `compatibility` with `observations.product_adoption_current` as its replacement.

## State, 13 September 2026

`currentai.signal_packages` is **deployed, released, materialized and scheduled** (Sunday 01:00
UTC): `downloads_daily` over 18 artifacts, `downloads` at 188 rows across pypi, npm and crates,
`product_adoption` at 186, all three recorded `active` or `compatibility` in `assets.yaml`.
Parity against `signal_pypi` was checked per product and is exact —
of its 170 products, 169 band identically and one is unbanded on both sides; nothing moved and
nothing was lost. Everything that changes comes from npm and crates, which had no signal model
before: sixteen products gain a package band, three of them moving from the stars cap of 3 to 5.

`signal_pypi` is **intact and not dropped.** Both things this section used to say needed a
maintainer are done: `not_primary_channel` shipped in #563, and `columns=` was applied to
`signal_github.artifact_state`. That did not break the deadlock, and — contrary to what this
document said for several hours — it did not cause one either. What remains is #562 steps 3 to 5.

## The determinism lock, which is the expensive lesson here

A release may not change a model's schema-determinism verdict, **in either direction**, and a
large share of this org's models could not be released at all on 2026-09-13 — including datasets
with no connection to the gap map.

**This section first blamed our own `columns=` change on `signal_github.artifact_state`, and that
was wrong.** Twenty of the frozen models never read that table. The two events happened within
minutes of each other and the second was read as a consequence of the first for most of a day.
Correcting it here because the wrong version told a maintainer to expect a cascade from their own
edit, which is the opposite of the right instinct.

The refusal names the model you are releasing, so it always reads as a fault in your own change.
**Isolate it with a byte-identical control**, and run it carefully:

1. Create a new revision whose code is byte-identical to **the model's currently live released
   revision** — not merely "a previous revision". An older release or an unreleased draft is a
   different model definition, and the next step would ship it.
2. Attempt to release it. **A control can succeed**, and then it is live. That happened on
   2026-09-13 to `currentai.metrics.daily` — externalized under ADR-003, which is exactly why
   it was an acceptable thing to experiment on. The code was identical so nothing changed in
   behaviour, but re-releasing the original afterwards does NOT undo it: the release row is
   updated in place and keeps its original timestamp, so it cannot supersede the newer one.
   **Run a control only on a model where shipping an identical definition is acceptable**, and
   prefer one this repository does not govern.
3. Read the refusal, if there is one. It must be **the determinism-verdict message** for the
   diagnosis to hold. A release refused for any other reason says nothing about this.

Two models tested this way behaved differently on the same day. Neither is a governed asset
here and nothing below is data to read — it is release behaviour, nothing more.
`currentai.metrics.daily`, externalized, released cleanly.
`currentai.scores.taxonomy`, externalized, was refused.
The question is always per-model, never org-wide.

**Do not read the verdict off an unreleased draft.** For SQL the schema is derived and frozen at
release, so a fresh revision can report non-deterministic with zero columns and still release
fine, coming back with its full schema. Reading drafts produced a wrong count twice in one
evening.

There is no repair, only recreation. `updateDataModel` accepts a `name`, returns `success: true`
and leaves the name unchanged, because the name lives on the revision and releasing one is what
is refused — so delete and recreate under the target name. Recreation loses the materialized
table, the model context and the schedule, and two of those come back wrong by default:
`deploy_udm.py` sets a new model to `@manual`, and a brand-new dataset has no cron at all.

**Recreation restores releasability and does not immunize.** A recreated model is stable at
whatever verdict it is born with, which is the only reason it releases. If the platform's
resolution behaviour changes again, these models move in the other direction and lock again, so
treat a recreation as a way out of today rather than a fix.

For a **Python** model the schema comes from the in-code `columns=` declaration, so a model whose
schema was supplied as the `schema:` argument instead cannot be re-released at all. Declaring
`columns=` is the repair, and it only takes effect on a newly created model. That is what the
four fetchers of #358 needed.

## Proving it

A populated `cron`, `lastRunAt` or `nextRunAt` does **not** prove the model runs on a schedule.
Only a run whose `triggerType` is `SCHEDULED` proves that; the cron field is metadata, and models
have carried one while every run in their history was `MANUAL`. Read the output table back rather
than trusting a run's reported status, which can still say `RUNNING` after the run has finished.

## Related

- `docs/operations/deploy-models.md` — the general mechanic, the refresh order, the parity gate
- `docs/architecture/data-architecture.md` §4.1 — why the route precedence must move first
- `docs/architecture/adr-003-repository-scope-boundary.md` — why the model source is not here
