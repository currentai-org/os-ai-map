# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""Daily download history from the package registries this map has to fetch.

Covers npm and crates.io. PyPI is deliberately absent: `oso.pypi_downloads` already
holds every package on PyPI at day grain, so the PyPI leg of
`signal_packages.downloads` windows a table the warehouse has, and there is
nothing to fetch. There is no equivalent global dataset for npm or crates, which is
the whole reason this model exists.

Roster comes from `currentai.registry.product_artifacts`, filtered to those two
kinds — the repo's own declaration, pushed out by CI, so coverage tracks the map
rather than a hand-maintained package list. 14 artifacts across 13 products on
2026-08-14: 13 npm (`mastra` declares both `@mastra/core` and `mastra`) and one
crate (`yomo`). One request per artifact.

Grain: one row per (product, artifact_kind, package, day). `artifact_kind` uses the
registry's own vocabulary and is the discriminator `sources/signal_routing.yaml`
filters each route on, the way it already filters `signal_huggingface.hub_state`
into its model and dataset routes.

## Why a series and not a trailing total

A point read cannot tell a collapse from a step change that happened months ago,
and that defect is already filed as issue #163 against the PyPI side. `lmdeploy`
is the case: two point reads looked like a 165K -> 50K collapse, and the daily
series showed 171,750 in May, then 57,776, 54,993 and 50,402 — one step change
that had held for three months, with the earlier trailing window having simply been
measuring May. The two reads never disagreed. `llama-factory` is still in
`sources/verification_queue.yaml` for the same reason: "settling it needs the
download history rather than two point reads."

## What the two APIs actually do, measured 2026-08-14

npm, `https://api.npmjs.org/downloads/range/<start>:<end>/<package>`:

  * Serves at most 18 months and **silently clips a longer request rather than
    erroring**. Asking 2024-08-14 to 2026-08-13 returned 547 days beginning
    2025-02-13. So a requested window is not evidence of a served window, and every
    date here comes from the response.
  * A scoped name goes through unencoded: `range/.../@mastra/core` answers, and
    percent-encoding the slash returns 404.
  * The `last-month` and `last-year` aliases lag about five days behind today and an
    explicit end date does not. `last-year` ended 2026-08-09 while an explicit range
    returned full days through 2026-08-13. That is the second reason to ask for a
    range: it is fresher, not only longer.
  * Zero is a value npm reports for a day it has no data for, and those zeros are
    inside the totals it publishes: `n8n` has two in a 30-day window, both Sundays.
    They are kept as rows, so a total depressed by a gap can be told from a total
    depressed by a fall in installs.

crates.io, `https://crates.io/api/v1/crates/<crate>/downloads`:

  * Serves **90 days and no more**. `before_date` does not page further back — asked
    for 2026-05-01 it returned the same trailing 90 days. So crates history is three
    months, full stop, and a trend over a longer window is not available at any
    price.
  * Downloads arrive per version, plus a `meta.extra_downloads` roll-up for versions
    the response does not enumerate. Both are summed; reading only
    `version_downloads` undercounts any crate old enough to have retired a version.
  * Days with no downloads are omitted rather than reported as zero, which is the
    opposite of npm's habit. A missing day here is a real zero.
  * `/api/v1/crates/<crate>` is NOT fetched. Its `recent_downloads` covers 90 days
    while looking like a monthly figure — `yomo` reports 347 there, and its series
    sums to exactly 347 across 90 days against 96 in the trailing 30 — so banding it
    monthly would overstate the crate by 3.6x. The series answers the same question
    without the trap, and `signal_routing.yaml` records the rule.

Both APIs are unauthenticated. crates.io asks for a descriptive User-Agent and gets
one; npm asks for nothing.

## Failure is a row, not an absence

Taken from `signal_github.repo_state`: an artifact that could not be read
contributes one row with a null `day` and its own `http_status`, so a 404 is visible
rather than missing. Both registries answer 404 with a JSON body for an unknown
name.

That distinction is load-bearing because the roster runs ahead of the signal between
runs — the registry declared 106 PyPI artifacts while `signal_pypi` held 98 — so
"declared, not fetched yet" must not read the same as "fetched and gone". The
`playwright-mcp` record carried `@anthropic-ai/mcp-playwright` for weeks, which
api.npmjs.org answers 404 for, and nothing in the pipeline could say so.

Counts are raw registry requests: CI jobs, mirrors and container builds included.
Volume, not unique users. No band here — bands are declared in the repo and applied
in `signal_packages.product_adoption`.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

import oso
import polars as pl

NPM_API = "https://api.npmjs.org"
CRATES_API = "https://crates.io/api/v1/crates"
USER_AGENT = "os-ai-map-signal-packages/1.0 (https://github.com/currentai-org/os-ai-map)"
ROSTER_SQL = (
    "SELECT product_slug, product_type, artifact_kind, artifact_id "
    'FROM "currentai"."registry"."product_artifacts" '
    "WHERE artifact_kind IN ('npm', 'crates')"
)
# 18 months is npm's own ceiling, and it clips rather than erroring, so asking for
# exactly the ceiling is how to learn where the data really starts.
NPM_HISTORY_DAYS = 547


def _text(payload: object, key: str) -> str | None:
    if isinstance(payload, dict):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None


def _number(payload: object, key: str) -> int | None:
    if isinstance(payload, dict):
        value = payload.get(key)
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
    return None


def _day(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _npm_series(payload: object) -> list[tuple[date, int]]:
    """npm serves one object per day, zeros included."""
    if not isinstance(payload, dict):
        return []
    rows = payload.get("downloads")
    if not isinstance(rows, list):
        return []
    out: list[tuple[date, int]] = []
    for row in rows:
        day = _day(_text(row, "day"))
        count = _number(row, "downloads")
        if day is not None and count is not None:
            out.append((day, count))
    return out


def _crates_series(payload: object) -> list[tuple[date, int]]:
    """crates.io serves per-version rows plus a roll-up, and omits empty days."""
    if not isinstance(payload, dict):
        return []
    blocks: list[object] = [payload.get("version_downloads")]
    meta = payload.get("meta")
    if isinstance(meta, dict):
        blocks.append(meta.get("extra_downloads"))

    totals: dict[date, int] = {}
    for block in blocks:
        if not isinstance(block, list):
            continue
        for row in block:
            day = _day(_text(row, "date"))
            count = _number(row, "downloads")
            if day is None or count is None:
                continue
            totals[day] = totals.get(day, 0) + count
    return sorted(totals.items())


def series_for(artifact_kind: str, payload: object) -> list[tuple[date, int]]:
    """Route the payload to its registry's parser. An unknown kind yields nothing."""
    if artifact_kind == "npm":
        return _npm_series(payload)
    if artifact_kind == "crates":
        return _crates_series(payload)
    return []


def request_url(artifact_kind: str, package: str, period: str) -> str | None:
    """The one call this artifact needs, or None if the kind is not one of ours."""
    if artifact_kind == "npm":
        return f"{NPM_API}/downloads/range/{period}/{package}"
    if artifact_kind == "crates":
        return f"{CRATES_API}/{package}/downloads"
    return None


def npm_period(today: date) -> str:
    """18 months ending yesterday: today is still accumulating."""
    end = today - timedelta(days=1)
    start = end - timedelta(days=NPM_HISTORY_DAYS - 1)
    return f"{start.isoformat()}:{end.isoformat()}"


def rows_for(
    product_slug: str,
    product_type: str,
    artifact_kind: str,
    package: str,
    payload: object,
    http_status: int,
    fetched_at: datetime,
) -> list[dict]:
    """The rows one artifact contributes: its served days, or one failure row."""
    series = series_for(artifact_kind, payload)
    if not series:
        return [
            {
                "product_slug": product_slug,
                "product_type": product_type,
                "artifact_kind": artifact_kind,
                "package": package,
                "day": None,
                "downloads": None,
                "http_status": http_status,
                "fetched_at": fetched_at,
            }
        ]
    return [
        {
            "product_slug": product_slug,
            "product_type": product_type,
            "artifact_kind": artifact_kind,
            "package": package,
            "day": day,
            "downloads": downloads,
            "http_status": http_status,
            "fetched_at": fetched_at,
        }
        for day, downloads in series
    ]


@oso.model(
    environment_name="Default",
    depends_on=["currentai.registry.product_artifacts"],
    external_origins=["https://api.npmjs.org", "https://crates.io"],
)
async def package_downloads_daily(context: oso.AsyncContext) -> oso.DataFrame:
    headers: dict[str, str] = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    result = await context.query(ROSTER_SQL)
    roster = await result.as_pl()

    artifacts: list[tuple[str, str, str, str]] = []
    for row in roster.iter_rows(named=True):
        slug = row.get("product_slug")
        product_type = row.get("product_type")
        artifact_kind = row.get("artifact_kind")
        package = row.get("artifact_id")
        if not isinstance(slug, str) or not isinstance(package, str) or not package:
            continue
        if not isinstance(artifact_kind, str):
            continue
        artifacts.append(
            (
                slug,
                product_type if isinstance(product_type, str) else "",
                artifact_kind,
                package,
            )
        )
    if not artifacts:
        raise RuntimeError("roster query returned no npm or crates artifacts")

    fetched_at = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    period = npm_period(fetched_at.date())

    urls = [
        request_url(artifact_kind, package, period)
        for _, _, artifact_kind, package in artifacts
    ]
    unroutable = [url is None for url in urls]
    if all(unroutable):
        raise RuntimeError("no declared artifact belongs to a registry this model reads")

    responses = await asyncio.gather(
        *(
            context.fetch(url, headers=headers)
            for url in urls
            if url is not None
        )
    )
    # Put the responses back beside their artifacts, so an unroutable kind still
    # produces a row rather than shifting every row after it onto the wrong package.
    answered: list[object] = []
    cursor = 0
    for url in urls:
        if url is None:
            answered.append(None)
        else:
            answered.append(responses[cursor])
            cursor += 1

    if not any(
        response is not None and response.status == 200 for response in answered
    ):
        raise RuntimeError(f"every one of {len(artifacts)} registry calls failed")

    rows: list[dict] = []
    for index, (slug, product_type, artifact_kind, package) in enumerate(artifacts):
        response = answered[index]
        status = response.status if response is not None else 0
        payload = response.json() if response is not None and status == 200 else None
        rows.extend(
            rows_for(
                slug, product_type, artifact_kind, package, payload, status, fetched_at
            )
        )

    return pl.DataFrame(
        rows,
        schema={
            "product_slug": pl.Utf8,
            "product_type": pl.Utf8,
            "artifact_kind": pl.Utf8,
            "package": pl.Utf8,
            "day": pl.Date,
            "downloads": pl.Int64,
            "http_status": pl.Int64,
            "fetched_at": pl.Datetime("us"),
        },
    )
