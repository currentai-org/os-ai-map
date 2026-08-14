# Runbook: Deploy / refresh UDMs (maintainer, MCP write)

UDM SQL source-of-truth lives in `warehouse/models/`. Deploying requires an OSO
MCP-enabled session with write access to the `currentai` org.

1. Edit the `.sql` in `warehouse/models/`; PR + review.
2. Create a revision: `createDataModelRevision` with the dataset and the SQL.
3. Release it: `createDataModelRelease` (required before a run. The revision alone does
   not run).
4. Trigger a run: `createUserModelRunRequest` with the dataset ID.
5. Verify freshness with a read query via `pyoso`.

Datasets: entities / events / metrics / scores (see `warehouse/models/README.md`).
Daily crons already exist; this runbook is for out-of-band refreshes after a SQL change.
