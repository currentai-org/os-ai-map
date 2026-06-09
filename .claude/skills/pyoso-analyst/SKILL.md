---
name: pyoso-analyst
description: >
  Analyst workflow for external users who have API-key + `pyoso` read-only access
  to the OSO data warehouse (no MCP and no data-lake write operations).
tier: core
---

# pyoso Analyst

Use this skill when:
- You are an external user (no MCP tooling access).
- You need to query `currentai.*` and/or public `oso.*` tables via `pyoso`.
- You want to create/read/run **marimo notebooks** for analysis and reporting.

Do not use this skill when:
- You need MCP capabilities (uploads, schema changes, running deployed models, etc.).
- You need to write/update data in the OSO data lake.
- You need to refresh/revise UDMs or static models.

## External boundaries

Hard constraints:
- No MCP usage.
- No upload/run/revision/create model operations.
- Treat `currentai.*` tables as read-only from your perspective.

If you detect a request that requires write access, you must:
1. Explain why external access is insufficient.
2. Provide the minimal reproducible SQL/notebook approach.
3. Tell the user to escalate to OSO internal workflows for the write/MCP step.

## Workflow Steps

1. **Pick the right table from the registry**
   - Start from [`warehouse/models/README.md`](../../../warehouse/models/README.md) for the inventory.
   - Use [`docs/guides/queries.md`](../../../docs/guides/queries.md) for query conventions and caveats.
   - Use [`docs/guides/notebooks.md`](../../../docs/guides/notebooks.md) for marimo notebook structure/style.

2. **Draft bounded Trino SQL**
   - Prefer `LIMIT`, date windows (e.g. last 90 days), and aggregations.
   - Use the three-part name convention: `currentai.<dataset>.<table>`.

3. **Run via `pyoso`**
   - Use your environment-scoped `OSO_API_KEY` (no hard-coded secrets).

   ```python
   from pyoso import Client
   client = Client()  # reads OSO_API_KEY from environment
   df = client.to_pandas("SELECT ... LIMIT 10")
   ```

4. **Create or update a marimo notebook**
   - You may edit existing notebooks and build new ones for analysis/reporting.
   - Keep heavy queries in memoized/parameterized cells when possible.

5. **Report results with limitations**
   - If a requested dataset is missing, point to `docs/catalog-gaps.md`.
   - Summarize what you can validate vs what needs OSO-side remediation.

## Quick Reference

### Key commands (notebook edit)

```bash
uv run marimo edit notebooks/<your_notebook>.py
uv run marimo run notebooks/<your_notebook>.py
```

### SQL conventions
- Trino SQL dialect.
- Always `LOWER()` repo names when joining across sources (casing is inconsistent).
- Deduplicate `currentai.goodailist_repos.repos` by `LOWER(repo)` when needed.
- Source tables live in `sources/` (YAML) and `warehouse/` (SQL UDMs); the curated registry is not a SQL table.

## Checklist (before completing)

Before finalizing, verify:
- [ ] The solution is doable with read-only `pyoso` (no MCP/write steps).
- [ ] Queries are bounded (`LIMIT`, date windows) or otherwise safe.
- [ ] Notebook workflow is clear for both create and re-run.
- [ ] The answer notes any coverage gaps or missing mappings (if relevant).
