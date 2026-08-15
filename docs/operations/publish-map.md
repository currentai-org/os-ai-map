# Runbook: Publish the AI Stack Map notebook (maintainer)

1. On `main`, the regenerate workflow has already rebuilt `build/notebook_data.json`
   and `notebooks/ai-stack-map.py` as a bot commit; `git pull` and publish those.
   Rebuild locally only to verify (`uv run python -m build.serialize --date <bot date>
   && uv run python build/render.py` must produce no diff).
2. Validate: `uv run python -m build.validate` (must be clean) and
   `uv run marimo check notebooks/ai-stack-map.py`.
3. Visual sign-off on the exported HTML before publishing (no browser in-container —
   `uv run marimo export html notebooks/ai-stack-map.py -o /tmp/preview.html` and review
   locally; at minimum confirm it renders and shows the expected product count).
4. Upload + publish to the OSO platform (oso-prod MCP). Live slug `/currentai/ai-stack-map`,
   notebook id `7b29bf47-26d7-4aa2-9d5e-43bdfa33c2e4`, org `currentai`
   (`ad7f4c1c-dd2f-430e-a831-e7f1f16e6d9e`):
   1. `createNotebookUploadUrl({orgId})` → `{uploadUrl, uploadId}`.
   2. `curl -X PUT -H "Content-Type: text/plain" --data-binary @notebooks/ai-stack-map.py "<uploadUrl>"` (expect HTTP 200).
   3. `updateNotebook` with the `uploadId` — **required** (publish renders from the saved
      source). Note: input is double-nested `{"input":{"input":{id, uploadId, description}}}`
      and the response echoes the full ~1MB notebook, so read `success` via `jq` on the
      saved tool-result file rather than inlining it. Good moment to refresh the stale
      product count in the `description`.
   4. `publishNotebook({notebookId, force:true})` — async; returns `status: PUBLISHING`.
      Re-call **without** `force` to poll until `status: READY` (returns a `contentUrl`).
5. Verify live: `curl` the `contentUrl` (gzipped HTML) → `gunzip` → grep for the product
   count and a few newly-added product names.
