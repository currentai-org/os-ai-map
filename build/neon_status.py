"""Read back what a Neon publish actually landed, as a markdown report.

The verification half of `build/publish_neon.py`. A publish that returns 0 has swapped a
schema into place; this connects independently and asks the database what is there — every
table in the schema with its row count, and the `publish_runs` log. Written for
`$GITHUB_STEP_SUMMARY`, so the output is markdown and carries no part of the DSN.

Row counts come through `query_to_xml`, which runs a real `count(*)` per table inside one
statement. The alternative, `pg_class.reltuples`, is an estimate maintained by ANALYZE and
reads as `-1` on a table that has just been created — precisely the state every table is in
after a swap.

Environment:
    NEON_DATABASE_URL   required

Usage:
    uv run python -m build.neon_status                 # markdown to stdout
    uv run python -m build.neon_status >> "$GITHUB_STEP_SUMMARY"
"""

from __future__ import annotations

import argparse
import os
import sys

from build.publish_neon import (
    DEFAULT_SCHEMA,
    DSN_ENV,
    RUN_TABLE,
    quote_schema,
    require_ssl,
    scrub,
)

COUNTS_SQL = """
SELECT table_name,
       (xpath('/row/c/text()',
              query_to_xml(
                  format('select count(*) as c from %I.%I', table_schema, table_name),
                  false, true, '')))[1]::text::int AS rows
FROM information_schema.tables
WHERE table_schema = %s
ORDER BY 1
"""

RUNS_SQL = """
SELECT run_id, published_at, schema_version, built_at, released_at,
       source_git_sha, declaration_version_id, table_count, row_counts
FROM {schema}.{table}
ORDER BY published_at DESC
"""


def report(dsn: str, schema: str) -> str:
    import psycopg

    lines: list[str] = []
    with psycopg.connect(require_ssl(dsn)) as connection, connection.cursor() as cursor:
        cursor.execute(COUNTS_SQL, (schema,))
        rows = cursor.fetchall()
        lines.append(f"### `{schema}` tables after the load\n")
        lines.append("| table | rows |")
        lines.append("|---|---:|")
        for name, count in rows:
            lines.append(f"| `{name}` | {count:,} |")
        total = sum(count for name, count in rows if name != RUN_TABLE)
        lines.append(f"\n{len(rows)} tables, {total:,} rows outside `{RUN_TABLE}`.\n")

        cursor.execute(RUNS_SQL.format(schema=quote_schema(schema), table=f'"{RUN_TABLE}"'))
        runs = cursor.fetchall()
        lines.append(f"### `{schema}.{RUN_TABLE}` — {len(runs)} row(s), newest first\n")
        lines.append(
            "| published_at | run_id | schema_version | built_at | released_at "
            "| source_git_sha | tables |"
        )
        lines.append("|---|---|---:|---|---|---|---:|")
        for row in runs:
            (
                run_id,
                published_at,
                schema_version,
                built_at,
                released_at,
                git_sha,
                _version_id,
                table_count,
                _counts,
            ) = row
            lines.append(
                f"| {published_at:%Y-%m-%d %H:%M:%SZ} | `{run_id[:12]}` | {schema_version} "
                f"| {built_at or '-'} | {released_at or '-'} "
                f"| `{(git_sha or '-')[:12]}` | {table_count} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn-env", default=DSN_ENV)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        print(f"{args.dsn_env} is not set; nothing to read", file=sys.stderr)
        return 2
    try:
        sys.stdout.write(report(dsn, args.schema))
    except Exception as error:  # noqa: BLE001 - scrubbed; the driver quotes the host
        print(f"could not read the schema back: {scrub(str(error), dsn)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
