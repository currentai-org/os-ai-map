# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""Artificial Analysis model evaluations — the capability aggregator.

One authenticated request returns every model AA tracks with its full evaluation
block. This matters because most benchmark leaderboards publish HTML or keep
results behind a dashboard app rather than as files: AILuminate's repo carries only
prompt sets, Terminal-Bench's results sit in a database, and SWE-bench has no
aggregate. AA has already done that aggregation and exposes it as JSON, so this one
source reaches Terminal-Bench, tau2, LiveCodeBench, GPQA, MMLU-Pro, AIME and HLE.

Deliberately NOT joined to the map's products. AA names point releases
("Claude Sonnet 4.6 (Non-reasoning, High Effort)") while the map keeps generic
version buckets, and normalized-name matching mis-mapped Claude Sonnet 4 onto
Sonnet 4.6 in testing. This lands AA's own rows keyed on AA's own slug; the
product bridge is a separate, curated piece of work.

Every numeric field arrives as int OR float depending on the record — the
intelligence index alone is 496 floats and 77 ints across the corpus — so numbers
are read as float. Reading them as int would silently turn a score of 60.7 into 60.

Thirteen models carry no intelligence index at all, and they are the newest
frontier releases (the Claude Sonnet 5 variants, GPT-5.5 Pro). AA has not scored
them yet, so a null score means unmeasured, not incapable.

Coverage caveat worth carrying: AA matched 57 of the map's 106 model products on
name in a manual check, and the misses skew toward small open models, safety
models, and the map's deliberate version buckets. AA is a frontier-model source,
not a whole-map one.
"""

from datetime import date, datetime, timezone

import oso
import polars as pl

AA_URL = "https://artificialanalysis.ai/api/v2/data/llms/models"

EVAL_FIELDS = [
    "artificial_analysis_intelligence_index",
    "artificial_analysis_coding_index",
    "artificial_analysis_math_index",
    "mmlu_pro",
    "gpqa",
    "hle",
    "livecodebench",
    "scicode",
    "math_500",
    "aime",
    "aime_25",
    "ifbench",
    "lcr",
    "terminalbench_hard",
    "terminalbench_v2_1",
    "tau2",
    "tau_banking",
]
PRICE_FIELDS = ["price_1m_blended_3_to_1", "price_1m_input_tokens", "price_1m_output_tokens"]
SPEED_FIELDS = [
    "median_output_tokens_per_second",
    "median_time_to_first_token_seconds",
    "median_time_to_first_answer_token",
]


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


def _float(payload: object, key: str) -> float | None:
    """Scores arrive as int or float per record. Always read as float."""
    if not isinstance(payload, dict):
        return None
    value = payload.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _nested(payload: object, block: str, key: str) -> str | None:
    if isinstance(payload, dict):
        inner = payload.get(block)
        if isinstance(inner, dict):
            value = inner.get(key)
            if isinstance(value, str):
                return value
    return None


def _nested_float(payload: object, block: str, key: str) -> float | None:
    if isinstance(payload, dict):
        inner = payload.get(block)
        if isinstance(inner, dict):
            return _float(inner, key)
    return None


def _price(payload: object, key: str) -> float | None:
    """AA encodes "no hosted pricing" as 0.0, never as null.

    211 of 586 models carry 0.0 — open-weights families with no hosted endpoint,
    plus unreleased frontier models. A hosted model does not cost exactly zero, so
    0.0 is missing data and is returned as null. Otherwise every downstream reader
    would see a third of the corpus as free.
    """
    value = _nested_float(payload, "pricing", key)
    if value is None or value == 0.0:
        return None
    return value


def _has_hosted_pricing(payload: object) -> bool:
    """True when AA reports any non-zero price, i.e. the model is served somewhere."""
    return any(
        (_nested_float(payload, "pricing", field) or 0.0) > 0.0 for field in PRICE_FIELDS
    )


def _release_date(payload: object) -> date | None:
    raw = _text(payload, "release_date")
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


@oso.model(
    secrets=["ARTIFICIAL_ANALYSIS_TOKEN"],
    environment_name="Default",
    external_origins=["https://artificialanalysis.ai"],
)
def model_evaluations(context: oso.Context) -> oso.DataFrame:
    token: str = context.secret("ARTIFICIAL_ANALYSIS_TOKEN")
    response = context.fetch(AA_URL, headers={"X-API-Key": token})
    if response.status != 200:
        raise RuntimeError(f"Artificial Analysis returned {response.status}")

    records = _records(response.json())
    if not records:
        raise RuntimeError("Artificial Analysis returned no models")

    fetched = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)

    rows: list[dict] = []
    for record in records:
        row: dict = {
            "aa_id": _text(record, "id"),
            "aa_slug": _text(record, "slug"),
            "name": _text(record, "name"),
            "release_date": _release_date(record),
            "creator_name": _nested(record, "model_creator", "name"),
            "creator_slug": _nested(record, "model_creator", "slug"),
            "fetched_at": fetched,
        }
        for field in EVAL_FIELDS:
            row[field] = _nested_float(record, "evaluations", field)
        for field in PRICE_FIELDS:
            row[field] = _price(record, field)
        row["has_hosted_pricing"] = _has_hosted_pricing(record)
        for field in SPEED_FIELDS:
            row[field] = _float(record, field)
        rows.append(row)

    schema: dict = {
        "aa_id": pl.Utf8,
        "aa_slug": pl.Utf8,
        "name": pl.Utf8,
        "release_date": pl.Date,
        "creator_name": pl.Utf8,
        "creator_slug": pl.Utf8,
        "has_hosted_pricing": pl.Boolean,
        "fetched_at": pl.Datetime("us"),
    }
    for field in EVAL_FIELDS + PRICE_FIELDS + SPEED_FIELDS:
        schema[field] = pl.Float64
    return pl.DataFrame(rows, schema=schema)
