---
name: add-data-source
description: Use when adding a new external data source to os-ai-map. Registers it in the asset inventory and adds a fetcher; the warehouse-deploy step is a maintainer runbook.
---

# Add a Data Source

Spans two roles. The **curatable** part (anyone can PR): register the source and add a
fetcher. The **deploy** part (maintainer, MCP write): wire it into the warehouse.

## Pick the ingestion route first

Two shapes, and the choice matters more than it looks:

- **A UDM reads the source directly** (`authority: platform`, a mirror model under
  `warehouse/models/<dataset>/`). Prefer this. Nothing is committed, nothing goes stale, and
  the table refreshes on its own cron.
- **A fetcher writes a CSV** (`authority: repo`, a `files.model` under
  `warehouse/models/catalog/<table>.py` writing a `files.data` CSV under
  `warehouse/data/<dataset>/`). Only when the source needs credentials or shaping a UDM
  cannot do, or when the data is genuinely a fixed reference set rather than a live feed.

A committed CSV mirror of a live source can only be staler than the source. The GoodAI List
was ingested that way and the frozen copy drifted to listing 300 repos the site had
delisted while missing 2,056 it had added, with nothing surfacing the gap. It is now read
directly by `currentai.signal_goodailist.repo_catalog`.

## Editor steps (PR-able)
1. Add an asset entry to `warehouse/assets.yaml` for the table the source lands in (`id`,
   `table`, `kind`, `authority`, `grain`, `producer`, `files`, and the other required
   fields — copy the nearest existing entry of the same route as a template).
2. For the fetcher route only: add `warehouse/models/catalog/<table>.py` writing a CSV to
   `warehouse/data/<dataset>/<table>.csv`, and name both in the entry's `files:` block
   (`model` and `data`). The path mirrors the table: `models/<dataset>/<table>.<ext>` is
   `currentai.<dataset>.<table>`. Follow the existing fetchers' shape; large dumps go in
   `.gitignore`.
3. Run the inventory gates, which check that every managed file is claimed, every declared
   path exists, the path derives the table, and `reads`/`read_by` match the tree:
   ```bash
   uv run pytest -q tests/test_assets_inventory.py
   ```
4. Open a PR.

## Maintainer step (not in this skill)
Loading the CSV into the `currentai` warehouse (static model or UDM) requires MCP write
access. See `docs/operations/refresh-data.md` and `docs/operations/deploy-models.md`.
