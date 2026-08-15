# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""LMArena text leaderboard, style-control config, from Hugging Face.

Reads the `text_style_control` config, NOT `text`. That is the whole reason this
model works.

The `text` config is unusable: 30% of its (model, category) pairs carry between 2
and 6 different ratings and ranks on the same publish date, with no column
distinguishing them — gpt-5.4/overall appears six times at ranks 1, 1, 2, 10, 30
and 32. Filtering the `full` split to a single date reproduces it exactly, so it
is the source, not the split. `text_style_control` covers the same 378 models and
29 categories and is exactly one row per pair, 9,956 of 9,956.

Style control is also the better number on merit rather than a workaround: it
adjusts for response length and formatting, the known confound where a model
wins on verbosity and markdown rather than substance.

Transport: the parquet file is one request of ~550KB against 100 paged calls, and
paging this dataset is what produced HTTP 429 before. Hugging Face 302s the
parquet URL to a signed CDN host and `context.fetch` does not follow redirects,
so the redirect is walked by hand. If any of that fails the model falls back to
the paged rows API, which is slower and rate-limit prone but known to work.
"""

import asyncio
import io
from datetime import datetime, timezone
from urllib.parse import urlencode

import oso
import polars as pl
import pyarrow.parquet as pq

HF_HOST = "https://huggingface.co"
CDN_HOST = "https://us.aws.cdn.hf.co"
ROWS_URL = "https://datasets-server.huggingface.co/rows"

DATASET = "lmarena-ai/leaderboard-dataset"
CONFIG = "text_style_control"
SPLIT = "latest"
PARQUET_PATH = (
    "/datasets/lmarena-ai/leaderboard-dataset/resolve/refs%2Fconvert%2Fparquet"
    "/text_style_control/latest/0000.parquet"
)

PAGE_SIZE = 100
TRANSIENT_STATUSES = [429, 500, 502, 503, 504]
MAX_ATTEMPTS = 4

TEXT_COLUMNS = ["model_name", "organization", "license", "category", "leaderboard_publish_date"]
FLOAT_COLUMNS = ["rating", "rating_lower", "rating_upper", "variance"]
INT_COLUMNS = ["vote_count", "rank"]
# Spelled out rather than concatenated: top-level assignments must be literals.
ALL_COLUMNS = [
    "model_name",
    "organization",
    "license",
    "category",
    "leaderboard_publish_date",
    "rating",
    "rating_lower",
    "rating_upper",
    "variance",
    "vote_count",
    "rank",
]


def _header(headers: object, name: str) -> str | None:
    """Case-insensitive lookup over an untyped headers mapping."""
    if not isinstance(headers, dict):
        return None
    target = name.lower()
    for key, value in headers.items():
        if isinstance(key, str) and key.lower() == target and isinstance(value, str):
            return value
    return None


def _rows(payload: object) -> list[dict]:
    """datasets-server nests each record under a `row` key."""
    if not isinstance(payload, dict):
        return []
    entries = payload.get("rows")
    if not isinstance(entries, list):
        return []
    records: list[dict] = []
    for entry in entries:
        if isinstance(entry, dict):
            row = entry.get("row")
            if isinstance(row, dict):
                records.append(row)
    return records


def _total_rows(payload: object) -> int:
    if isinstance(payload, dict):
        value = payload.get("num_rows_total")
        if isinstance(value, bool):
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
    return 0


def _page_url(offset: int) -> str:
    query = urlencode(
        {
            "dataset": DATASET,
            "config": CONFIG,
            "split": SPLIT,
            "offset": offset,
            "length": PAGE_SIZE,
        }
    )
    return f"{ROWS_URL}?{query}"


async def _fetch_page(
    context: oso.AsyncContext, offset: int, headers: dict[str, str]
) -> object:
    """One page, retrying transient upstream failures with backoff."""
    delay = 1.0
    for attempt in range(MAX_ATTEMPTS):
        response = await context.fetch(_page_url(offset), headers=headers)
        if response.status == 200:
            return response.json()
        if response.status not in TRANSIENT_STATUSES or attempt == MAX_ATTEMPTS - 1:
            raise RuntimeError(
                f"rows api returned {response.status} at offset {offset}"
                f" after {attempt + 1} attempt(s)"
            )
        await asyncio.sleep(delay)
        delay *= 2
    raise RuntimeError(f"exhausted retries at offset {offset}")


async def _via_parquet(context: oso.AsyncContext, headers: dict[str, str]) -> pl.DataFrame | None:
    """One request plus one redirect hop. Returns None so the caller can fall back."""
    first = await context.fetch(f"{HF_HOST}{PARQUET_PATH}", headers=headers)
    body: object = None
    if first.status == 200:
        body = first.body
    elif first.status in (301, 302, 303, 307, 308):
        location = _header(first.headers, "location")
        if not isinstance(location, str) or not location.startswith(CDN_HOST):
            return None
        followed = await context.fetch(location)
        if followed.status != 200:
            return None
        body = followed.body
    else:
        return None
    if not isinstance(body, (bytes, bytearray)):
        return None
    table = pq.read_table(io.BytesIO(bytes(body)))
    # pl.from_arrow is typed DataFrame | Series; a Table always yields a frame,
    # but narrow it so the type checker agrees and a surprise falls back instead.
    frame = pl.from_arrow(table)
    if not isinstance(frame, pl.DataFrame):
        return None
    return frame


async def _via_rows(context: oso.AsyncContext, headers: dict[str, str]) -> pl.DataFrame:
    """Paged fallback. Slower and rate-limit prone, but known to work."""
    payload = await _fetch_page(context, 0, headers)
    total = _total_rows(payload)
    records: list[dict] = _rows(payload)
    offsets = list(range(PAGE_SIZE, total, PAGE_SIZE))
    if offsets:
        pages = await asyncio.gather(
            *(_fetch_page(context, offset, headers) for offset in offsets)
        )
        for page in pages:
            records.extend(_rows(page))
    if not records:
        raise RuntimeError("rows api returned no records")
    return pl.DataFrame(records)


@oso.model(
    secrets=["HUGGING_FACE_TOKEN"],
    environment_name="Default",
    external_origins=[
        "https://huggingface.co",
        "https://us.aws.cdn.hf.co",
        "https://datasets-server.huggingface.co",
    ],
)
async def text_leaderboard(context: oso.AsyncContext) -> oso.DataFrame:
    token: str = await context.secret("HUGGING_FACE_TOKEN")
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    frame: pl.DataFrame | None = None
    via = "parquet"
    try:
        frame = await _via_parquet(context, headers)
    except Exception:  # noqa: BLE001 - any parquet failure is a fallback signal
        frame = None
    if frame is None:
        via = "rows"
        frame = await _via_rows(context, headers)

    missing = [c for c in ALL_COLUMNS if c not in frame.columns]
    if missing:
        raise RuntimeError(f"{via} route returned unexpected columns, missing {missing}")

    # The whole point of this config: one row per model per category. Assert it
    # rather than trust it, so a change upstream fails loudly instead of silently
    # double-counting every downstream aggregate.
    pairs = frame.select("model_name", "category").n_unique()
    if pairs != frame.height:
        raise RuntimeError(
            f"{CONFIG} returned {frame.height} rows for {pairs} (model, category) pairs; "
            "expected exactly one row each. The `text` config has this defect — check "
            "whether it has spread to this one before trusting the numbers."
        )

    stamp = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    return (
        frame.select(
            *[pl.col(name).cast(pl.Utf8) for name in TEXT_COLUMNS],
            *[pl.col(name).cast(pl.Float64) for name in FLOAT_COLUMNS],
            *[pl.col(name).cast(pl.Int64) for name in INT_COLUMNS],
        )
        .with_columns(
            arena_config=pl.lit(CONFIG),
            fetched_via=pl.lit(via),
            ingested_at=pl.lit(stamp, dtype=pl.Datetime("us")),
        )
    )
