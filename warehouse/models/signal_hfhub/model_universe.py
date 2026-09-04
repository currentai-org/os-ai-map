# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""The live Hugging Face Hub model universe — the missing input #329 asks for.

`currentai.catalog.model_repos` is a one-time, hand-loaded dump: 21,229 rows as
of this model's authoring, no declared selection rule, no `downloads_30d` floor
(median 30-day downloads across the table is 13, and 83% of rows sit below
1,000), and about 38% of rows carry no `pipeline_tag` at all. It reads like an
unfiltered crawl of a fixed window, not a reproducible criterion, and nothing
refreshes it. `signal_huggingface.artifact_state` cannot substitute for it
either — that model is keyed to the artifacts the registry already declares, so
it can only report on models the map has already found, never on what else
exists on the Hub.

This model sweeps the Hub's public `/api/models` list endpoint directly
(`sort=downloads&direction=-1`), paging while `downloads` (the Hub's own
rolling 30-day figure, same field `huggingface_hub_state.py` reads from the
single-model endpoint) stays at or above `DOWNLOADS_FLOOR_30D`. Sampling the
live distribution before choosing a floor: about 11,000 models clear a
5,000-download floor, about 27,000 clear 1,000, and about 45,000 clear 500.
1,000 is chosen as the floor -- it lands the sweep in the middle of the
5,000-50,000 order of magnitude a useful universe needs, comfortably above the
whole-Hub scale (millions of near-zero-download repos) the frozen table never
excluded.

Grain: one row per Hub model repo (`hf_id`) with `downloads_30d >=
DOWNLOADS_FLOOR_30D` at fetch time. Not registry-scoped -- this is the
candidate universe the registry is drawn from, not the registry itself.

Two shape traps carried over from `huggingface_hub_state.py`:
  * the list endpoint has no `cardData`, so license comes from the
    `license:<slug>` tag instead of `cardData.license`.
  * `gated` is a bool or a mode string ("auto" / "manual"); recorded as both a
    flag and the mode is dropped here (list endpoint gives only the raw
    value) -- kept as the boolean flag `gated`, string mode collapses to
    `gated=True`.

Paging is capped at `MAX_PAGES` (40 x 1,000 = 40,000 rows scanned, well above
the ~27 pages the 1,000-download floor is expected to need) so a runaway sweep
cannot run long or unbounded. A 429 gets up to 3 retries with exponential
backoff before the run fails loud rather than silently truncating the
universe.
"""

import asyncio
import re
from datetime import datetime, timezone

import oso
import polars as pl

HF_API = "https://huggingface.co"
LIST_ENDPOINT = "https://huggingface.co/api/models"
PAGE_SIZE = 1000
DOWNLOADS_FLOOR_30D = 1000
MAX_PAGES = 40
MAX_RETRIES = 3
RETRY_BASE_SECONDS = 2.0
PAGE_PAUSE_SECONDS = 0.25
NEXT_LINK_PATTERN = r'<([^>]+)>;\s*rel="next"'


def _license(tags: object) -> str | None:
    """The list endpoint carries no `cardData`; license rides a `license:` tag."""
    if not isinstance(tags, list):
        return None
    for tag in tags:
        if isinstance(tag, str) and tag.startswith("license:"):
            value = tag[len("license:") :]
            return value or None
    return None


def _gated(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return True
    return None


def _stamp(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=None, microsecond=0)


def _tags_json(tags: object) -> str | None:
    if not isinstance(tags, list):
        return None
    names = [t for t in tags if isinstance(t, str)]
    return "[" + ",".join('"' + n.replace('"', '\\"') + '"' for n in names) + "]"


def _next_url(headers: dict) -> str | None:
    link = headers.get("Link") or headers.get("link")
    if not isinstance(link, str):
        return None
    match = re.search(NEXT_LINK_PATTERN, link)
    return match.group(1) if match else None


@oso.model(
    secrets=["HUGGING_FACE_TOKEN"],
    environment_name="Default",
    external_origins=["https://huggingface.co"],
    capabilities=oso.Capabilities(fetch=True),
)
async def model_universe(context: oso.AsyncContext) -> oso.DataFrame:
    token: str = await context.secret("HUGGING_FACE_TOKEN")
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "oso-udm-client/1.0",
    }

    url: str | None = (
        f"{LIST_ENDPOINT}?sort=downloads&direction=-1&limit={PAGE_SIZE}&full=true"
    )
    fetched = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    rows: list[dict] = []
    page_count = 0
    floor_reached = False

    while url is not None and page_count < MAX_PAGES and not floor_reached:
        response = None
        for attempt in range(MAX_RETRIES + 1):
            response = await context.fetch(url, headers=headers)
            if response.status != 429:
                break
            if attempt == MAX_RETRIES:
                break
            await asyncio.sleep(RETRY_BASE_SECONDS * (2**attempt))

        if response is None or response.status != 200:
            status = response.status if response is not None else "no response"
            raise RuntimeError(
                f"Hub list request failed after retries: page {page_count + 1}, "
                f"status {status}, url {url}"
            )

        page_count += 1
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError(f"unexpected Hub list payload shape on page {page_count}")

        for item in payload:
            if not isinstance(item, dict):
                continue
            downloads = item.get("downloads")
            downloads_int = downloads if isinstance(downloads, int) else None
            if downloads_int is None or downloads_int < DOWNLOADS_FLOOR_30D:
                floor_reached = True
                break
            likes = item.get("likes")
            rows.append(
                {
                    "hf_id": item.get("id"),
                    "author": item.get("author"),
                    "pipeline_tag": item.get("pipeline_tag"),
                    "library_name": item.get("library_name"),
                    "license": _license(item.get("tags")),
                    "downloads_30d": downloads_int,
                    "likes": likes if isinstance(likes, int) else None,
                    "created_at": _stamp(item.get("createdAt")),
                    "last_modified": _stamp(item.get("lastModified")),
                    "gated": _gated(item.get("gated")),
                    "private": item.get("private") if isinstance(item.get("private"), bool) else None,
                    "tags": _tags_json(item.get("tags")),
                    "fetched_at": fetched,
                }
            )

        if len(payload) < PAGE_SIZE:
            break

        url = _next_url(response.headers)
        if url is not None and not floor_reached:
            await asyncio.sleep(PAGE_PAUSE_SECONDS)

    if not rows:
        raise RuntimeError("Hub sweep returned zero models at or above the downloads floor")

    return pl.DataFrame(
        rows,
        schema={
            "hf_id": pl.Utf8,
            "author": pl.Utf8,
            "pipeline_tag": pl.Utf8,
            "library_name": pl.Utf8,
            "license": pl.Utf8,
            "downloads_30d": pl.Int64,
            "likes": pl.Int64,
            "created_at": pl.Datetime("us"),
            "last_modified": pl.Datetime("us"),
            "gated": pl.Boolean,
            "private": pl.Boolean,
            "tags": pl.Utf8,
            "fetched_at": pl.Datetime("us"),
        },
    )
