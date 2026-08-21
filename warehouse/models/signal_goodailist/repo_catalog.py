# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""GoodAI List repo catalog, read live from goodailist.com's public API.

Replaces the hand-uploaded `catalog.goodailist_repos` static model. No auth
required. The upstream refreshes daily, so this runs daily.

Two things this adds over the static table:
  * `first_seen` and `is_new` — the discovery signal for new entrants.
  * `source_updated_at` — upstream freshness, distinct from our run time, so a
    stale upstream is visible rather than silently presented as current.

~17k repos across 18 pages at 1000/page. Page count stays under the sandbox's
25-in-flight cap, so the fan-out is a single wave with no queueing.

Builds a pyarrow Table directly and does NOT use polars. The sandbox is pyodide,
which is wasm32, and polars' `to_arrow()` allocates through Rust with 32-bit
capacity — at this row count it panics with `pyo3_runtime.PanicException:
capacity overflow` during Arrow IPC serialization, after the model's own code has
finished successfully. Chunking the frame does not avoid it and neither does
rechunk(); the panic is in the polars->Arrow conversion itself. Returning a
pyarrow Table skips that conversion, since the runner uses the table as-is.

Keep this model polars-free. Any transformation added here must be expressed in
plain Python or pyarrow.
"""

import asyncio
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone
from urllib.parse import urlencode

import oso
import pyarrow as pa

BASE = "https://goodailist.com"
SUMMARY_PATH = "/api/summary"
REPOS_PATH = "/api/repos"
PAGE_SIZE = 1000

# Two distinct limits bite here, and both fixes are needed.
#   1. Returning polars panics in Arrow serialization (see the module docstring).
#      Fixed by building a pyarrow Table.
#   2. Shipping the whole ~5.5MB table in one response kills the host with
#      "UDM host /chunks request failed: Server disconnected without sending a
#      response". Fixed by yielding it in slices.
# At ~325 bytes/row this is roughly 1.3MB per chunk.
CHUNK_ROWS = 4000

TEXT_COLUMNS = [
    "repo",
    "description",
    "category",
    "subcat",
    "keywords",
    "country",
    "top_devs",
    "language",
]
INT_COLUMNS = ["stars", "forks", "contributors", "star_1d", "star_7d"]
FLOAT_COLUMNS = ["star_1d_pct", "star_7d_pct"]
DATE_COLUMNS = ["created_at", "updated_at", "first_seen"]
BOOL_COLUMNS = ["is_new", "archived"]


def _repos_url(page: int) -> str:
    """Build a /api/repos URL for one page."""
    query = urlencode(
        {
            "page": page,
            "limit": PAGE_SIZE,
            "sort_by": "stars",
            "sort_order": "desc",
        }
    )
    return f"{BASE}{REPOS_PATH}?{query}"


def _records(payload: object) -> list[dict]:
    """Pull the `repos` array out of an untyped payload."""
    if not isinstance(payload, dict):
        return []
    entries = payload.get("repos")
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def _page_count(payload: object) -> int:
    """Read `pages` out of an untyped payload."""
    if isinstance(payload, dict):
        value = payload.get("pages")
        if isinstance(value, bool):
            return 0
        if isinstance(value, int):
            return value
    return 0


def _upstream_stamp(payload: object) -> datetime | None:
    """Parse `updated_at` from /api/summary, which reports upstream freshness."""
    if not isinstance(payload, dict):
        return None
    value = payload.get("updated_at")
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=None, microsecond=0)
    except ValueError:
        return None


def _as_text(value: object) -> str | None:
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


def _as_int(value: object) -> int | None:
    """bool is a subclass of int, so reject it explicitly rather than store 0/1."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def _as_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _as_date(value: object) -> date | None:
    """Upstream sends YYYY-MM-DD, sometimes with a time component appended."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _as_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "t", "1", "yes"):
            return True
        if lowered in ("false", "f", "0", "no"):
            return False
    return None


def _dedupe(records: list[dict]) -> list[dict]:
    """Keep the first occurrence of each repo.

    Upstream returns a handful of exact duplicates (4 of ~17k on the first run),
    all with identical stars and category, most likely because paging a
    live-sorted list can show the same row twice. Results are sorted by stars
    descending, so the first occurrence is the higher-star copy.
    """
    seen: set[str] = set()
    out: list[dict] = []
    for record in records:
        repo = _as_text(record.get("repo"))
        if repo is None or repo in seen:
            continue
        seen.add(repo)
        out.append(record)
    return out


def _build_table(
    records: list[dict], upstream: datetime | None, stamp: datetime
) -> pa.Table:
    """Assemble the Arrow table column by column, with types pinned explicitly.

    The schema is declared rather than inferred so an all-null column still lands
    with the right type instead of arriving as null and breaking the table
    contract.
    """
    columns: dict[str, pa.Array] = {}
    for name in TEXT_COLUMNS:
        columns[name] = pa.array([_as_text(r.get(name)) for r in records], type=pa.string())
    for name in INT_COLUMNS:
        columns[name] = pa.array([_as_int(r.get(name)) for r in records], type=pa.int64())
    for name in FLOAT_COLUMNS:
        columns[name] = pa.array([_as_float(r.get(name)) for r in records], type=pa.float64())
    for name in DATE_COLUMNS:
        columns[name] = pa.array([_as_date(r.get(name)) for r in records], type=pa.date32())
    for name in BOOL_COLUMNS:
        columns[name] = pa.array([_as_bool(r.get(name)) for r in records], type=pa.bool_())

    timestamp = pa.timestamp("us")
    columns["source_updated_at"] = pa.array([upstream] * len(records), type=timestamp)
    columns["ingested_at"] = pa.array([stamp] * len(records), type=timestamp)

    ordered = (
        TEXT_COLUMNS
        + INT_COLUMNS
        + FLOAT_COLUMNS
        + DATE_COLUMNS
        + BOOL_COLUMNS
        + ["source_updated_at", "ingested_at"]
    )
    return pa.table({name: columns[name] for name in ordered})


@oso.model(external_origins=["https://goodailist.com"])
async def repo_catalog(context: oso.AsyncContext) -> AsyncIterator[oso.DataFrame]:
    summary_response = await context.fetch(f"{BASE}{SUMMARY_PATH}")
    if summary_response.status != 200:
        raise RuntimeError(f"goodailist /api/summary returned {summary_response.status}")
    upstream = _upstream_stamp(summary_response.json())

    first = await context.fetch(_repos_url(1))
    if first.status != 200:
        raise RuntimeError(f"goodailist /api/repos returned {first.status} on page 1")

    payload = first.json()
    pages = _page_count(payload)
    records: list[dict] = _records(payload)

    if pages > 1:
        rest = list(range(2, pages + 1))
        responses = await asyncio.gather(
            *(context.fetch(_repos_url(page)) for page in rest)
        )
        for page, response in zip(rest, responses):
            if response.status != 200:
                raise RuntimeError(
                    f"goodailist /api/repos returned {response.status} on page {page}"
                )
            records.extend(_records(response.json()))

    if not records:
        raise RuntimeError("goodailist returned no repos")

    stamp = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    table = _build_table(_dedupe(records), upstream, stamp)

    # combine_chunks() materializes each slice into its own buffers. A bare
    # pa.Table.slice() is a zero-copy view over the parent, so the IPC writer can
    # still walk the full-size buffers behind it and defeat the point of chunking.
    for start in range(0, table.num_rows, CHUNK_ROWS):
        yield table.slice(start, CHUNK_ROWS).combine_chunks()
