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
What it enforces — and since the source lives outside the repo, this validator is the only thing
that checks it, so a rejection here is the first signal you will get:

- Exactly one `@oso.model`-decorated function, whose name becomes the table name.
- A return annotation of `oso.DataFrame`; `oso.AsyncContext` on an `async def`.
- Literal `depends_on` (fully-qualified `org.dataset.table`) and `external_origins`.
- Imports from the standard library except `sys`, plus `oso` / `polars` / `pandas` /
  `pyarrow` / `numpy`. **`requests` is a dependency of this repo and is blocked in the
  sandbox**, which is the easiest way to get a rejection.
- No top-level statements beyond imports, defs, a docstring and literal assignments.

The declared `schema` must match the columns and dtypes the DataFrame actually returns. A
mismatch surfaces at query time as a confusing type error, not at deploy.

## Deploying `signal_packages`, and retiring `signal_pypi`

Authored 2026-08-14, deployed never. The repo's readers have **already** moved:
`build/check_artifacts.py` queries `signal_packages.package_downloads` and the pypi route in
`sources/signal_routing.yaml` points at it. So until step 4 lands, `check_artifacts` prints
`pypi_missing SKIPPED` and reports nothing rather than failing — which is a check not running,
not a check passing. Do the steps in order and do not leave it parked there.

### 1. Republish the registry static model

`build/serialize_registry.py` gained a `not_primary_channel` column, and the crates URLs now
reduce to bare crate names. Both matter before anything fetches: the deployed table still holds
`artifact_id = "https://crates.io/crates/yomo"`, out of which the fetch would build a nonsense
URL.

A static model **cannot** gain a column through a plain re-upload — the multi-column ALTER
fails, and a bare PUT returns `SignatureDoesNotMatch`. Delete and recreate
`currentai.registry.product_artifacts` rather than fighting it.

### 2. Create the dataset and the fetch model

`createDataset` — name `signal_packages`, type `USER_MODEL`.

> **Source for the three `signal_packages` models is not in this repo.** Like every other
> `signal_*` model it lives on the platform, with the maintainer's working copy under
> `currentai-org/udms/` (`packages_package_downloads_daily.py`,
> `packages_package_downloads.sql`, `packages_product_adoption.sql`). That directory is outside
> any git repo, so the platform's own revision history is the record. See #173 — `warehouse/`
> is being deprecated rather than extended, and the file-location claim at the top of this
> runbook is false for every `signal_*` model.

`package_downloads_daily` — `language: "python"`. No secret: npm's downloads API is
unauthenticated and crates.io only asks for a descriptive User-Agent, which the source sets.
Revision → release → run, then confirm from the table that npm rows carry about 547 days each
and crates rows about 90, and that no row carries a 404 unless a declared package really is gone.

### 3. Build the two SQL models

`package_downloads` — `language: "sql"`. Revision → release → run.

`product_adoption` — `language: "sql"`. Revision → release → run.

Because the source sits outside the repo, **nothing in CI can check the SQL's arithmetic or the
Python's contract.** The one thing CI still guards is that `hexabot` and `yomo` keep their
`not_primary_channel` reason (`tests/test_serialize_registry.py`); everything else about these
models is verified by the required diff in step 5 and by `check_parity`.

Cron: weekly, matching the other signal models. `signal_pypi` runs Monday 04:00 UTC; put the
daily fetch ahead of the two SQL models so a run reads a fresh series.

### 4. Compare old against new — REQUIRED before anything is dropped

The PyPI leg of `package_downloads` is a port of the deployed `signal_pypi` revision, and a port
is a claim about behavior that only a diff can settle. Both tables coexist at this point, which
is the whole reason the sequence is shaped this way.

```sql
-- Row count and per-product agreement on the PyPI leg.
SELECT
  COUNT(*) AS compared,
  COUNT_IF(o.downloads_30d IS DISTINCT FROM n.downloads_30d) AS downloads_differ,
  COUNT_IF(o.missing_from_pypi IS DISTINCT FROM n.missing_from_registry) AS missing_differ
FROM currentai.signal_pypi.package_downloads o
FULL JOIN currentai.signal_packages.package_downloads n
  ON n.product_slug = o.product_slug
  AND n.package = o.package
  AND n.artifact_kind = 'pypi'
```

Expect `compared` to equal `signal_pypi`'s row count and both difference columns to be 0, then
list any row that differs and account for it before continuing.

**The new model is deliberately not bit-identical, in one respect.** `signal_pypi` joined
`registry.adoption_bands` on `product_type` alone; the new roll-up filters `signal_type` as well,
because that table holds three instruments' scales and only `usage_volume` belongs to a download
count. Measured 2026-08-14 that changes nothing — `active_users` and `stars_fallback` are both
declared at `product_type: '*'`, so the old join never matched them — but a band difference here
is a **finding to report**, not automatically a porting error. The other expected difference is
grain: `signal_pypi` carried `adoption_level` per package and the new per-artifact table carries
none, because the band moved to `product_adoption` where the sum is taken.

Also compare the bands themselves, which is the comparison that matters to the map:

```sql
SELECT o.product_slug, o.adoption_level AS old_level, n.adoption_level AS new_level, n.abstain_reason
FROM (
  SELECT product_slug, MAX(adoption_level) AS adoption_level
  FROM currentai.signal_pypi.package_downloads GROUP BY product_slug
) o
FULL JOIN currentai.signal_packages.product_adoption n ON n.product_slug = o.product_slug
WHERE o.adoption_level IS DISTINCT FROM n.adoption_level
```

Rows are expected here and each has a known cause: a product declaring both npm and PyPI is now
summed (`beeai`), a product whose only package artifact is `not_primary_channel` now abstains
(`hexabot`, `yomo`), and a product with an uncounted artifact now abstains rather than banding a
short sum. Anything outside those three shapes needs an explanation before step 6.

### 5. Flip the routes in the repo

Only now: set `bridged: true` and drop `blocked_by` for the npm and crates sources in
`sources/signal_routing.yaml`. Before a run exists, `bridged: true` would tell
`build/check_instrument.py` that 12 `usage_volume` records are recomputable when nothing has
computed them, and `tests/test_signal_routing.py` fails the flip for that reason.

Re-run `uv run python -m build.check_artifacts` and confirm `pypi_missing` reports rather than
skips.

### 6. Drop `signal_pypi` — irreversible, and last

`deleteDataset` on `signal_pypi`. **There is no undo**: the revisions go with it, and the SQL
was never in this repo, so the only copy of the original model is the one pasted into the PR
that ported it. Do not run this step in the same session as step 3, and do not run it while any
row in step 4's second query is unexplained.

Datasets: entities / events / metrics / scores / signal_packages (see
`warehouse/models/README.md`). Daily crons already exist for the first four; this runbook is
for out-of-band refreshes after a source change.
