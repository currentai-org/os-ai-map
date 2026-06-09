# Runbook: Refresh external data (maintainer)

1. Run the relevant fetcher(s): `uv run python warehouse/ingest/fetch_<id>.py`.
2. Load the CSV into the `currentai` warehouse as a static model (MCP):
   `createStaticModelUploadUrl`, upload, then `createStaticModelRunRequest`. For a brand-new
   source, `createStaticModel` first; then `createDataModelRelease`.
3. Re-run dependent UDMs (see `deploy-udms.md`).
4. Re-serialize + re-render + re-publish (see `publish-notebook.md`).
