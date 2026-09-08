# Runbook: Load external data into the warehouse (maintainer)

**There are no catalog fetchers in this repository any more.** ADR-003 externalized the
`catalog.*` tables (see `warehouse/audits/externalization.json`, disposition
`frozen-without-producer`), and #406 deleted the two producers this runbook used to start with,
`warehouse/models/catalog/model_repos.py` and `model_benchmarks.py`. The deployed tables are
retained and frozen at their last publish under platform ownership; nothing in this repo
refreshes them. The weekly `refresh-data` workflow that ran them was retired for the same reason
(#509); it had been failing every Monday since the producers went.

What remains here is the loading half, which still applies to any CSV a governed fetcher writes
under the fetcher route in `skills/add-data-source/SKILL.md`:

1. Load the CSV into the `currentai` warehouse as a static model (MCP):
   `createStaticModelUploadUrl`, upload, then `createStaticModelRunRequest`. For a brand-new
   source, `createStaticModel` first; then `createDataModelRelease`.
2. Re-run dependent UDMs (see `deploy-models.md`).
3. Re-serialize + re-render + re-publish (see `publish-map.md`).
