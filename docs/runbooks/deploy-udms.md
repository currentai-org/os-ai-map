# Runbook: Deploy / refresh UDMs (maintainer, MCP write)

`warehouse/models/` holds the source for the `entities` / `events` / `metrics` / `scores`
datasets and for `signal_packages`. It does **not** hold the source for the other seven
`signal_*` models — `signal_github`, `signal_huggingface`, `signal_pypi`, `signal_lmarena`,
`signal_artificialanalysis`, `signal_semanticscholar`, `signal_goodailist` — which were
deployed straight to the platform and exist only as revisions there. That gap is issue #173.
Read a model's source off the platform with `GetDataModelByName` before editing one of those
seven; the directory will not have it.

Deploying requires an OSO MCP-enabled session with write access to the `currentai` org.

## SQL model

1. Edit the `.sql` in `warehouse/models/`; PR + review.
2. Create a revision: `createDataModelRevision` with the dataset, `language: "sql"` and the SQL.
3. Release it: `createDataModelRelease` (required before a run. The revision alone does not
   run — it is a no-op until released, and the symptom is "no effect" rather than an error).
4. Trigger a run: `createUserModelRunRequest` with the dataset ID.
5. Verify freshness with a read query via `pyoso`. Do **not** verify from `GetRun`'s status
   field: it can still read RUNNING long after a run finished. Corroborate against the output
   table.

## Python model

Same sequence, two differences: the revision carries `language: "python"` and Python source,
and the revision call runs a validator that rejects the code before it is ever released.
What it enforces (`tests/test_signal_models.py` checks the same things offline, so a rejection
here should mean the test set is incomplete):

- Exactly one `@oso.model`-decorated function, whose name becomes the table name.
- A return annotation of `oso.DataFrame`; `oso.AsyncContext` on an `async def`.
- Literal `depends_on` (fully-qualified `org.dataset.table`) and `external_origins`.
- Imports from the standard library except `sys`, plus `oso` / `polars` / `pandas` /
  `pyarrow` / `numpy`. **`requests` is a dependency of this repo and is blocked in the
  sandbox**, which is the easiest way to get a rejection.
- No top-level statements beyond imports, defs, a docstring and literal assignments.

The declared `schema` must match the columns and dtypes the DataFrame actually returns. A
mismatch surfaces at query time as a confusing type error, not at deploy.

## Deploying `signal_packages` (authored 2026-08-14, not yet deployed)

Three models in one new dataset, in this order, because each reads the one before it:

1. `createDataset` — name `signal_packages`, type `USER_MODEL`.
2. `package_downloads_daily` — `language: "python"`, source
   `warehouse/models/signal_packages_package_downloads_daily.py`. No secret: npm's downloads
   API is unauthenticated and crates.io only asks for a descriptive User-Agent, which the
   source sets. Revision → release → run, then confirm from the table that the npm rows carry
   about 547 days each and the crates rows about 90.
3. `package_downloads` — `language: "sql"`,
   `warehouse/models/signal_packages_package_downloads.sql`. Revision → release → run.
4. `product_adoption` — `language: "sql"`,
   `warehouse/models/signal_packages_product_adoption.sql`. Revision → release → run.
5. Cron: weekly, matching the other signal models. `signal_pypi` runs Monday 04:00 UTC; put
   the daily fetch ahead of the two SQL models so a run reads a fresh series.

Then, and only then, in the repo: flip `bridged` to `true` and drop `blocked_by` for the npm
and crates sources in `sources/signal_routing.yaml`. Until a run exists, `bridged: true` would
tell `build/check_instrument.py` that 12 `usage_volume` records are recomputable when nothing
has computed them, and `tests/test_signal_routing.py` fails the flip for that reason.

`signal_pypi` is untouched by all of this. It stays live until its readers move —
`build/check_artifacts.py` queries `missing_from_pypi`, and the pypi route still points at it —
so no reader ever queries a column that has already gone. Retiring it is a later PR: repoint
the checker and the route at `signal_packages.package_downloads`, verify, then delete the
dataset.

Datasets: entities / events / metrics / scores / signal_packages (see
`warehouse/models/README.md`). Daily crons already exist for the first four; this runbook is
for out-of-band refreshes after a source change.
