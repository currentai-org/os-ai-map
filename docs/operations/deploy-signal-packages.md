# Deploy `signal_packages`, then retire `signal_pypi` (maintainer, MCP write)

The npm/crates bridge of issue #314, and the two things that must happen around it: #348 before
the retirement, #517 after the deploy. The general deploy mechanic is
`docs/operations/deploy-models.md`; this is the order for this one change, which has an
irreversible step at the end and two constraints that fail silently if taken out of turn.

Model source is `currentai-org/udms/`, **not this repository** — `packages_package_downloads.sql`,
`packages_package_downloads_daily.py` and `packages_product_adoption.sql`. Nothing here is a
mirror to edit; see ADR-003 and the mirror table in `data-architecture.md`.

## The order

Each step's output is the next step's precondition. Only the last one cannot be undone.

1. **Republish the `registry` static model, by delete and recreate.** It gains a
   `not_primary_channel` column, and a static model cannot gain a column by re-upload — the
   multi-column ALTER fails, and the failure mode is a bare `PUT` or a `SignatureDoesNotMatch`
   rather than a clear error. Required for its own sake regardless: the deployed table has held
   `artifact_id = "https://crates.io/crates/yomo"` because `serialize_registry.py` carried no
   crates pattern, so the crates route could not have worked.
2. **Create the dataset and deploy the three models.** `createDataset` `signal_packages` as a
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
   re-resolves and is rejected. The fix is `columns=` on `artifact_state`, which is an
   `owner: oso` category-3 contract — maintainer work, not a change this repository can make.
5. **Diff old against new**, per artifact and per product, before anything is dropped. Expected
   disagreements come in exactly three shapes (below). Anything outside them is a finding to
   explain, not a rounding difference to accept.
6. **Merge the repository side**, then flip `bridged: true` and drop `blocked_by`. A test fails
   the flip if it is done in the other order.
7. **Drop `signal_pypi`.** The only irreversible step in the sequence, and the one currently
   blocked by step 4. Dropping it while the consumer still reads it would break that model at its
   next scheduled run and let the stars fallback silently re-band every product that already has
   a download signal — the corruption this order exists to prevent.

## `not_primary_channel` does not exist yet

The two staged SQL files read a `not_primary_channel` column. **Nothing produces it** — it is
absent from `registry.product_artifacts`, from `sources/products/*.yaml` and from every
`build/*.py`; a repository-wide search finds it only in those two files. Deployed as written it
resolves to `NULL`, and the two products the model's own comments name as having no primary
channel — `hexabot` and `yomo` — band on downloads anyway. Both are recorded at level 2 on
`stars_fallback` under a ruling of 2026-08-14 that minority channels do not carry the band, so
the warehouse would disagree with the corpus for exactly the case the column was invented for.

It is a `sources/products/*.yaml` declaration, so it belongs in the repository rather than
hard-coded into a warehouse model. Until it exists, treat a download band on either product as a
known false positive rather than a finding.

## What the diff may legitimately show

Three shapes, and the port is deliberately not bit-identical:

- **Cross-registry summation.** A product with both npm and PyPI now sums them.
- **No-primary-channel abstention.** A package that is a minority channel for its product
  carries `not_primary_channel` and is excluded from the banded sum rather than counted.
- **Partial coverage.**

`signal_pypi` joined `registry.adoption_bands` on `product_type` alone; the successor joins
`signal_type` too. That was checked against every band row at the time and moved no band, so a
future difference there is a finding rather than a porting error.

## #517 comes after, and only after

The six governed assets wearing a read-only mirror banner are reclassified once this deploy
lands. Three of them — `signal_packages.downloads`, `downloads_daily` and `product_adoption` —
have **no governed reader until step 2**, and a dependency contract must be reachable from a
governed root. Reclassifying them first pushes them out of scope in *both* manifests, and they
have to be re-added. The other three each have a reader and could move independently, but there
is no reason to split the change.

## State, 13 September 2026

`currentai.signal_packages` is **deployed, released, materialized and scheduled** (Sunday 01:00
UTC): `downloads_daily` over 18 artifacts, `downloads` at 188 rows across pypi, npm and crates,
`product_adoption` at 186. Parity against `signal_pypi` was checked per product and is exact —
of its 170 products, 169 band identically and one is unbanded on both sides; nothing moved and
nothing was lost. Everything that changes comes from npm and crates, which had no signal model
before: sixteen products gain a package band, three of them moving from the stars cap of 3 to 5.

`signal_pypi` is **intact and not dropped**, for the reason in step 4. Two things need a
maintainer: `columns=` on `signal_github.artifact_state` to break the determinism deadlock, and
the `not_primary_channel` declaration.

## Proving it

A populated `cron`, `lastRunAt` or `nextRunAt` does **not** prove the model runs on a schedule.
Only a run whose `triggerType` is `SCHEDULED` proves that; the cron field is metadata, and models
have carried one while every run in their history was `MANUAL`. Read the output table back rather
than trusting a run's reported status, which can still say `RUNNING` after the run has finished.

## Related

- `docs/operations/deploy-models.md` — the general mechanic, the refresh order, the parity gate
- `docs/architecture/data-architecture.md` §4.1 — why the route precedence must move first
- `docs/architecture/adr-003-repository-scope-boundary.md` — why the model source is not here
