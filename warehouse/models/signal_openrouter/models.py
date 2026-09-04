# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""OpenRouter model list — the release-watcher's first leg.

OpenRouter aggregates model listings across providers (OpenAI, Anthropic, Google,
Meta, open-weights hosts and more) into one JSON endpoint, no auth required. A
weekly pull of this list is the raw signal a "new model release" diff runs
against: a fresh row with a `created` timestamp inside the last week is a new
closed- or open-model release worth surfacing (a new Grok, Claude, Gemini, ...).

This replaces the hand-loaded `openrouter_snapshot` static model (last touched
2026-07-05, one snapshot, 340 rows) as the live source. `openrouter_snapshot` and
its downstream `ai_demand_curve` chain are left untouched here — repointing that
reader to this table is a separate, later change.

`pricing.prompt` / `pricing.completion` arrive as strings (decimal literals, USD
per token) rather than numbers, so they are parsed explicitly rather than trusted
to a numeric cast. `supported_parameters` is a list and is serialized to a JSON
string column rather than exploded, since its length and contents vary per model.
"""

import json
import time
from datetime import datetime, timezone

import oso
import polars as pl

OPENROUTER_URL = "https://openrouter.ai/api/v1/models"
USER_AGENT = "currentai-org-gap-map/1.0 (+https://github.com/currentai-org/os-ai-map)"

TRANSIENT_STATUSES = [429, 500, 502, 503, 504]
MAX_ATTEMPTS = 4


def _records(payload: object) -> list[dict]:
    """Rows live under `data`; narrow rather than assume."""
    if not isinstance(payload, dict):
        return []
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _text(payload: object, key: str) -> str | None:
    if isinstance(payload, dict):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None


def _int(payload: object, key: str) -> int | None:
    if isinstance(payload, dict):
        value = payload.get(key)
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
    return None


def _bool(payload: object, key: str) -> bool | None:
    if isinstance(payload, dict):
        value = payload.get(key)
        if isinstance(value, bool):
            return value
    return None


def _nested_text(payload: object, block: str, key: str) -> str | None:
    if isinstance(payload, dict):
        inner = payload.get(block)
        if isinstance(inner, dict):
            return _text(inner, key)
    return None


def _nested_bool(payload: object, block: str, key: str) -> bool | None:
    if isinstance(payload, dict):
        inner = payload.get(block)
        if isinstance(inner, dict):
            return _bool(inner, key)
    return None


def _price(payload: object, key: str) -> float | None:
    """Pricing arrives as a decimal string, e.g. "0.0000001". Parse, don't cast."""
    raw = _nested_text(payload, "pricing", key)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _provider(model_id: str | None) -> str | None:
    """The prefix before the first "/" in the model id, e.g. "anthropic"."""
    if not model_id or "/" not in model_id:
        return None
    return model_id.split("/", 1)[0]


def _created_at(payload: object) -> datetime | None:
    epoch = _int(payload, "created")
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(epoch, tz=timezone.utc).replace(tzinfo=None)
    except (OverflowError, OSError, ValueError):
        return None


def _supported_parameters(payload: object) -> str:
    if isinstance(payload, dict):
        value = payload.get("supported_parameters")
        if isinstance(value, list):
            return json.dumps(value)
    return json.dumps([])


@oso.model(
    external_origins=["https://openrouter.ai"],
    capabilities=oso.Capabilities(fetch=True),
)
def models(context: oso.Context) -> oso.DataFrame:
    headers = {"User-Agent": USER_AGENT}

    response = None
    delay = 1.0
    for attempt in range(MAX_ATTEMPTS):
        response = context.fetch(OPENROUTER_URL, headers=headers)
        if response.status == 200:
            break
        if response.status not in TRANSIENT_STATUSES or attempt == MAX_ATTEMPTS - 1:
            raise RuntimeError(
                f"OpenRouter returned {response.status} after {attempt + 1} attempt(s)"
            )
        time.sleep(delay)
        delay *= 2

    if response is None or response.status != 200:
        raise RuntimeError("OpenRouter did not return a successful response")

    records = _records(response.json())
    if not records:
        raise RuntimeError("OpenRouter returned no models")

    fetched = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)

    rows: list[dict] = []
    for record in records:
        model_id = _text(record, "id")
        rows.append(
            {
                "model_id": model_id,
                "name": _text(record, "name"),
                "provider": _provider(model_id),
                "created": _created_at(record),
                "context_length": _int(record, "context_length"),
                "pricing_prompt": _price(record, "prompt"),
                "pricing_completion": _price(record, "completion"),
                "architecture_modality": _nested_text(record, "architecture", "modality"),
                "architecture_tokenizer": _nested_text(record, "architecture", "tokenizer"),
                "top_provider_is_moderated": _nested_bool(
                    record, "top_provider", "is_moderated"
                ),
                "supported_parameters": _supported_parameters(record),
                "fetched_at": fetched,
            }
        )

    schema: dict = {
        "model_id": pl.Utf8,
        "name": pl.Utf8,
        "provider": pl.Utf8,
        "created": pl.Datetime("us"),
        "context_length": pl.Int64,
        "pricing_prompt": pl.Float64,
        "pricing_completion": pl.Float64,
        "architecture_modality": pl.Utf8,
        "architecture_tokenizer": pl.Utf8,
        "top_provider_is_moderated": pl.Boolean,
        "supported_parameters": pl.Utf8,
        "fetched_at": pl.Datetime("us"),
    }
    return pl.DataFrame(rows, schema=schema)
