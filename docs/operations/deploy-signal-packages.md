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
3. **#348 — move the `pypi` route precedence into `sources/signal_routing.yaml`.**
   **This precedes the retirement and is not optional.** `signal_github/product_adoption.sql`
   builds an `already_measured` set from `signal_pypi` and `signal_huggingface` and bands GitHub
   stars only for the products those channels did not cover; the precedence
   `pypi > huggingface > stars` lives in that SQL and nowhere else. `registry.adoption_routes`
   must carry it before the tables retire, or the ordering is lost and **nothing fails** —
   `data-architecture.md` §4.1 names this as the concrete AD-1 violation.
4. **Repoint the reader.** The deployed `signal_github.product_adoption` reads
   `currentai.signal_pypi.package_downloads` in that same CTE. It has to read the new table
   before the old one goes, or the stars fallback starts re-banding products that already have a
   download signal — a silent regression in the direction the map is most sensitive to.
5. **Diff old against new**, per artifact and per product, before anything is dropped. Expected
   disagreements come in exactly three shapes (below). Anything outside them is a finding to
   explain, not a rounding difference to accept.
6. **Merge the repository side**, then flip `bridged: true` and drop `blocked_by`. A test fails
   the flip if it is done in the other order.
7. **Drop `signal_pypi`.** The only irreversible step in the sequence.

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

## Proving it

A populated `cron`, `lastRunAt` or `nextRunAt` does **not** prove the model runs on a schedule.
Only a run whose `triggerType` is `SCHEDULED` proves that; the cron field is metadata, and models
have carried one while every run in their history was `MANUAL`. Read the output table back rather
than trusting a run's reported status, which can still say `RUNNING` after the run has finished.

## Related

- `docs/operations/deploy-models.md` — the general mechanic, the refresh order, the parity gate
- `docs/architecture/data-architecture.md` §4.1 — why the route precedence must move first
- `docs/architecture/adr-003-repository-scope-boundary.md` — why the model source is not here
