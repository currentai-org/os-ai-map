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

## Publishing the products view (`os-ai-products-view`)

The products view (`notebooks/products-view.py`, slug `/currentai/os-ai-products-view`) is a
second published notebook. Unlike `ai-stack-map.py` it is **hand-authored**, not rendered by
`build/render.py`: only its embedded data payload is generated, by
`build/products_view_data.py`, which the regenerate bot refreshes on merge to `main`. So after
a merge the file on `main` is already current — `git pull` and publish that file as-is.

- **Identifiers:** notebook id `d2ebb50d-8785-4955-97d9-c2a011cc2c5f`, slug
  `/currentai/os-ai-products-view`, org `currentai` (`ad7f4c1c-dd2f-430e-a831-e7f1f16e6d9e`).
- **Gates:** `uv run python -m build.validate` (clean), `uv run marimo check
  notebooks/products-view.py`, and `uv run python build/products_view_data.py --check` (every
  gallery exemplar still resolves to a product).
- **Visual sign-off:** the notebook is **reactive** (the lookup and the builder-demand table
  use `mo.ui` controls), so a static `marimo export html` renders the prose and server-side
  tables but does not exercise the interactive widgets. To verify those, run
  `uv run marimo run notebooks/products-view.py` and check in a browser, or accept the static
  export for a prose/layout check.
- **Publish:** identical MCP flow to steps 4–5 above (`createNotebookUploadUrl` →
  `curl PUT` the file → `updateNotebook` with the `uploadId`, double-nested input, read
  `success` via `jq` → `publishNotebook({force:true})`, poll until `READY` → verify the
  `contentUrl`). Confirm the live HTML leads with the lookup (mode 1) and contains the
  builder-demand table.
- **Preview before merge:** publish the branch build to a throwaway notebook in the same org
  (create one via `createNotebook` or the UI), share that slug for review, then `deleteNotebook`
  it once done — keep the live `os-ai-products-view` on merged `main`.
