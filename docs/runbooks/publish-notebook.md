# Runbook: Publish the AI Stack Map notebook (maintainer)

1. On `main`, the regenerate workflow has already rebuilt `build/notebook_data.json`
   and `notebooks/ai-stack-map.py` as a bot commit; `git pull` and publish those.
   Rebuild locally only to verify (`uv run python -m build.serialize --date <bot date>
   && uv run python build/render.py` must produce no diff).
2. Validate: `uv run python -m build.validate` (must be clean) and
   `uv run marimo check notebooks/ai-stack-map.py`.
3. Upload + publish to the OSO platform (MCP): `createNotebookUploadUrl`,
   upload `notebooks/ai-stack-map.py`, then `publishNotebook`. The live slug is
   `/currentai/ai-stack-map` (notebook id `7b29bf47`).
4. Visual sign-off on the exported HTML before publish (no browser in-container. Export
   and review locally).
