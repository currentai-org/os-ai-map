---
name: add-data-source
description: Use when adding a new external data source to os-ai-map. Registers it in the source manifest and adds a fetcher; the warehouse-deploy step is a maintainer runbook.
---

# Add a Data Source

Spans two roles. The **curatable** part (anyone can PR): register the source and add a
fetcher. The **deploy** part (maintainer, MCP write): wire it into the warehouse.

## Editor steps (PR-able)
1. Add an entry to `warehouse/sources.yaml` (`id`, `name`, `homepage`, `provides`,
   `fetcher`, `refresh`).
2. Add `warehouse/ingest/fetch_<id>.py` that writes a CSV under `warehouse/catalog/<id>/`.
   Follow the existing fetchers' shape. Large dumps go in `.gitignore`.
3. Verify the manifest parses and the fetcher path resolves:
   `uv run python -c "import yaml,pathlib; [pathlib.Path(e['fetcher']).resolve(strict=True) for e in yaml.safe_load(open('warehouse/sources.yaml'))['sources']]; print('ok')"`
4. Open a PR.

## Maintainer step (not in this skill)
Loading the CSV into the `currentai` warehouse (static model or UDM) requires MCP write
access. See `docs/runbooks/refresh-data.md` and `docs/runbooks/deploy-udms.md`.
