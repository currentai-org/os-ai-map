# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""Hugging Face Hub state for the map's model and dataset artifacts.

Roster comes from `currentai.registry.product_artifacts`, filtered to the two HF
artifact kinds — the repo's own declaration, pushed out by CI. This is the only adoption source for most of the map's models and
datasets: just 15 of 106 model products carry a GitHub artifact, while 61 carry a
`huggingface_model`, and 60 of 65 dataset products live on `huggingface_dataset`.

`downloads` is the Hub's rolling 30-day figure, which is what the adoption bands
are expressed in, so it is used as-is with no derivation.

Field selection: each call asks only for the fields read below via `expand[]`.
An unexpanded record carries `siblings` (every file in the repo), and for large
repos that pushes the response past OSO's 10 MB fetch cap — the 4 Oct 2026 failure,
caused by InternRobotics/InternData-A1 (~11.9 MB). `id` is always returned. If the
Hub rejects an expanded call with 400, that one artifact is retried unexpanded.

Two shape traps in the Hub API, both handled:
  * `cardData.license` is a plain string for models but a LIST for datasets.
  * `gated` is either a bool or a mode string ("auto" / "manual"), so gating is
    recorded as both a flag and the mode.

Partial failure is data, not an exception: a per-artifact `http_status` is
recorded rather than raised, so one deleted or renamed repo cannot void the run.
A fetch that raises (oversized or unreachable) is recorded as `http_status` 0.
"""

import asyncio
from datetime import datetime, timezone

import oso
import polars as pl

HF_API = "https://huggingface.co"
ROSTER_SQL = (
    "SELECT product_slug, artifact_kind, artifact_id "
    'FROM "currentai"."registry"."product_artifacts" '
    "WHERE artifact_kind IN ('huggingface_model', 'huggingface_dataset')"
)
MODEL_KIND = "huggingface_model"

DATASET_FIELDS = (
    "downloads",
    "likes",
    "cardData",
    "gated",
    "private",
    "disabled",
    "tags",
    "usedStorage",
    "createdAt",
    "lastModified",
)
# `pipeline_tag` and `library_name` are model-only; the Hub 400s them for datasets.
MODEL_FIELDS = (
    "downloads",
    "likes",
    "cardData",
    "gated",
    "private",
    "disabled",
    "tags",
    "usedStorage",
    "createdAt",
    "lastModified",
    "pipeline_tag",
    "library_name",
)


def _endpoint(kind: str, artifact_id: str, expand: bool = True) -> str:
    """Models and datasets share a shape but not a path."""
    segment = "models" if kind == MODEL_KIND else "datasets"
    url = f"{HF_API}/api/{segment}/{artifact_id}"
    if not expand:
        return url
    fields = MODEL_FIELDS if kind == MODEL_KIND else DATASET_FIELDS
    return url + "?" + "&".join(f"expand%5B%5D={field}" for field in fields)


async def _fetch_one(
    context: oso.AsyncContext, target: dict, headers: dict[str, str]
) -> tuple[int, object]:
    """One artifact's (status, payload); never raises, a raised fetch is status 0."""
    kind = target["artifact_kind"]
    artifact_id = target["artifact_id"]
    try:
        response = await context.fetch(_endpoint(kind, artifact_id), headers=headers)
        if response.status == 400:
            response = await context.fetch(
                _endpoint(kind, artifact_id, expand=False), headers=headers
            )
        if response.status == 200:
            return response.status, response.json()
        return response.status, None
    except Exception:
        return 0, None


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


def _flag(payload: object, key: str) -> bool | None:
    if isinstance(payload, dict):
        value = payload.get(key)
        if isinstance(value, bool):
            return value
    return None


def _stamp(payload: object, key: str) -> datetime | None:
    raw = _text(payload, key)
    if raw is None:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=None, microsecond=0)


def _tag_count(payload: object) -> int | None:
    if isinstance(payload, dict):
        value = payload.get("tags")
        if isinstance(value, list):
            return len(value)
    return None


def _license(payload: object) -> str | None:
    """`cardData.license` is a string for models and a list for datasets."""
    if not isinstance(payload, dict):
        return None
    card = payload.get("cardData")
    if not isinstance(card, dict):
        return None
    value = card.get("license")
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        names = [item for item in value if isinstance(item, str)]
        if names:
            return ",".join(names)
    return None


def _gated(payload: object) -> bool | None:
    """`gated` is False, or True, or a mode string like "auto" / "manual"."""
    if not isinstance(payload, dict):
        return None
    value = payload.get("gated")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return True
    return None


def _gated_mode(payload: object) -> str | None:
    if isinstance(payload, dict):
        value = payload.get("gated")
        if isinstance(value, str):
            return value
    return None


@oso.model(
    capabilities=oso.Capabilities(fetch=True),
    secrets=["HUGGING_FACE_TOKEN"],
    environment_name="Default",
    depends_on=["currentai.registry.product_artifacts"],
    external_origins=["https://huggingface.co"],
)
async def artifact_state(context: oso.AsyncContext) -> oso.DataFrame:
    token: str = await context.secret("HUGGING_FACE_TOKEN")
    headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

    result = await context.query(ROSTER_SQL)
    roster = await result.as_pl()
    targets: list[dict] = []
    for row in roster.iter_rows(named=True):
        kind = row.get("artifact_kind")
        artifact_id = row.get("artifact_id")
        slug = row.get("product_slug")
        if isinstance(kind, str) and isinstance(artifact_id, str) and isinstance(slug, str):
            targets.append(
                {"product_slug": slug, "artifact_kind": kind, "artifact_id": artifact_id}
            )
    if not targets:
        raise RuntimeError("roster query returned no HF artifacts")

    outcomes = await asyncio.gather(*(_fetch_one(context, t, headers) for t in targets))

    payloads: list[object] = []
    statuses: list[int] = []
    ok_count = 0
    for status, payload in outcomes:
        statuses.append(status)
        if status == 200:
            ok_count += 1
        payloads.append(payload)

    if ok_count == 0:
        raise RuntimeError(
            f"every one of {len(targets)} Hub calls failed; first status {statuses[0]}"
        )

    fetched = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)

    rows: list[dict] = []
    for index, target in enumerate(targets):
        payload = payloads[index]
        rows.append(
            {
                "product_slug": target["product_slug"],
                "artifact_kind": target["artifact_kind"],
                "artifact_id": target["artifact_id"],
                "resolved_id": _text(payload, "id"),
                "downloads_30d": _number(payload, "downloads"),
                "likes": _number(payload, "likes"),
                "license": _license(payload),
                "is_gated": _gated(payload),
                "gated_mode": _gated_mode(payload),
                "is_private": _flag(payload, "private"),
                "is_disabled": _flag(payload, "disabled"),
                "pipeline_tag": _text(payload, "pipeline_tag"),
                "library_name": _text(payload, "library_name"),
                "tag_count": _tag_count(payload),
                "used_storage_bytes": _number(payload, "usedStorage"),
                "created_at": _stamp(payload, "createdAt"),
                "last_modified": _stamp(payload, "lastModified"),
                "http_status": statuses[index],
                "fetched_at": fetched,
            }
        )

    return pl.DataFrame(
        rows,
        schema={
            "product_slug": pl.Utf8,
            "artifact_kind": pl.Utf8,
            "artifact_id": pl.Utf8,
            "resolved_id": pl.Utf8,
            "downloads_30d": pl.Int64,
            "likes": pl.Int64,
            "license": pl.Utf8,
            "is_gated": pl.Boolean,
            "gated_mode": pl.Utf8,
            "is_private": pl.Boolean,
            "is_disabled": pl.Boolean,
            "pipeline_tag": pl.Utf8,
            "library_name": pl.Utf8,
            "tag_count": pl.Int64,
            "used_storage_bytes": pl.Int64,
            "created_at": pl.Datetime("us"),
            "last_modified": pl.Datetime("us"),
            "http_status": pl.Int64,
            "fetched_at": pl.Datetime("us"),
        },
    )
