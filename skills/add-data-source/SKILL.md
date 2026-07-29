---
name: add-data-source
description: Use when adding a new external data source to os-ai-map. Registers it in the source manifest and adds a fetcher; the warehouse-deploy step is a maintainer runbook.
---

# Add a Data Source

Spans two roles. The **curatable** part (anyone can PR): register the source and add a
fetcher. The **deploy** part (maintainer, MCP write): wire it into the warehouse.

## Pick the ingestion route first

Two shapes, and the choice matters more than it looks:

- **A UDM reads the source directly** (`ingested_by: currentai.signal_<id>.<table>`). Prefer
  this. Nothing is committed, nothing goes stale, and the table refreshes on its own cron.
- **A fetcher writes a CSV** (`fetcher: warehouse/ingest/fetch_<id>.py`). Only when the
  source needs credentials or shaping a UDM cannot do, or when the data is genuinely a
  fixed reference set rather than a live feed.

A committed CSV mirror of a live source can only be staler than the source. The GoodAI List
was ingested that way and the frozen copy drifted to listing 300 repos the site had
delisted while missing 2,056 it had added, with nothing surfacing the gap. It is now read
directly by `currentai.signal_goodailist.repo_catalog`.

## Editor steps (PR-able)
1. Add an entry to `warehouse/sources.yaml` (`id`, `name`, `homepage`, `provides`,
   `refresh`, plus **either** `ingested_by` **or** `fetcher`).
2. For the fetcher route only: add `warehouse/ingest/fetch_<id>.py` writing a CSV under
   `warehouse/catalog/<id>/`. Follow the existing fetchers' shape. Large dumps go in
   `.gitignore`.
3. Verify the manifest parses, that every entry declares exactly one ingestion route, and
   that any fetcher path resolves:
   ```bash
   uv run python -c "
   import yaml, pathlib, sys
   bad = []
   for e in yaml.safe_load(open('warehouse/sources.yaml'))['sources']:
       routes = [k for k in ('fetcher', 'ingested_by') if e.get(k)]
       if len(routes) != 1:
           bad.append(f\"{e['id']}: declares {routes or 'no ingestion route'}\")
       elif 'fetcher' in routes:
           pathlib.Path(e['fetcher']).resolve(strict=True)
   print('\n'.join(bad) or 'ok'); sys.exit(1 if bad else 0)"
   ```
4. Open a PR.

## Maintainer step (not in this skill)
Loading the CSV into the `currentai` warehouse (static model or UDM) requires MCP write
access. See `docs/runbooks/refresh-data.md` and `docs/runbooks/deploy-udms.md`.
