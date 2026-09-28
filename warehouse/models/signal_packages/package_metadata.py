# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""Per-package registry metadata for the package artifacts the gap map declares.

Two registries, for two readers:

- **PyPI** (#709): `latest_version` is `info.version` from `https://pypi.org/pypi/<pkg>/json`,
  and `latest_upload_at` is the newest upload time among that version's files. The reader is
  `build/check_channel_authority.py`'s version-lag leg, through `signal_packages.downloads`,
  which joins these two columns in. The gate fetched the same endpoint itself until now.
- **Homebrew** (#718): `installs_30d`, `installs_90d` and `installs_365d` from
  `https://formulae.brew.sh/api/formula/<name>.json`, plus `latest_version` from
  `versions.stable`. Homebrew publishes the windows itself, so there is no history to keep.
  Formulae only; casks are a separate API and nothing on the map declares one yet.

Roster comes from `currentai.registry.product_artifacts`, filtered to the two kinds, so
coverage follows the map. Grain: one row per (product_slug, artifact_kind, package).

## An install is not a download

Homebrew counts a `brew install` on a machine, one event per install, with none of the CI jobs
and mirrors a PyPI download count carries. It does include installs pulled in as a dependency of
another formula, as described below. The map reads it as its own metric
with its own lower bands (Carl, 2026-09-28), so these figures are never added to download
counts. That is why they live here and not as rows in `signal_packages.downloads`.

`analytics.install` is keyed by install variant (`ollama`, `ollama --HEAD`), and the totals
here sum every variant. `install_on_request` is not used: it excludes installs pulled in as a
dependency of another formula, which undercounts a library like `ggml` that ships inside
others.

## Failure is a row, not an absence

As in `downloads_daily`: an artifact that could not be read contributes its row with nulls
and its own `http_status`, so "declared, not fetched yet" and "fetched and gone" stay apart.
Both registries answer an unknown name with 404.
"""

import asyncio
from datetime import datetime, timezone

import oso
import pandas as pd

PYPI_API = "https://pypi.org/pypi"
BREW_API = "https://formulae.brew.sh/api/formula"
USER_AGENT = "os-ai-map-signal-packages/1.0 (https://github.com/currentai-org/os-ai-map)"
ROSTER_SQL = (
    "SELECT DISTINCT product_slug, product_type, artifact_kind, artifact_id "
    'FROM "currentai"."registry"."product_artifacts" '
    "WHERE artifact_kind IN ('pypi', 'homebrew')"
)




def _frame(rows: list[dict], columns: list[tuple[str, str]]) -> pd.DataFrame:
    """Build the output frame with every column in declared order and a nullable dtype.

    Explicit dtypes matter because the platform checks declared types against the frame: a
    plain pandas integer column holding a null becomes float64 and would read as `double`.
    """
    # Built as object first: letting pandas infer an int column that holds a None gives float64,
    # which loses precision above 2**53 before the Int64 cast could preserve it.
    frame = pd.DataFrame(rows, columns=[name for name, _ in columns], dtype=object)
    for name, kind in columns:
        if kind == "timestamp":
            frame[name] = pd.to_datetime(frame[name]).astype("datetime64[us]")
        elif kind == "bigint":
            frame[name] = frame[name].astype(pd.Int64Dtype())
        elif kind == "boolean":
            frame[name] = frame[name].astype(pd.BooleanDtype())
        else:
            frame[name] = frame[name].astype(object)
    return frame

def _text(payload: object, key: str) -> str | None:
    if isinstance(payload, dict):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _stamp(raw: str | None) -> datetime | None:
    if raw is None:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.replace(microsecond=0)


def pypi_fields(payload: object) -> tuple[str | None, datetime | None]:
    """The version PyPI calls latest, and when its newest file was uploaded."""
    if not isinstance(payload, dict):
        return None, None
    version = _text(payload.get("info"), "version")
    files = payload.get("urls")
    stamps = []
    if isinstance(files, list):
        for item in files:
            stamp = _stamp(_text(item, "upload_time_iso_8601") or _text(item, "upload_time"))
            if stamp is not None:
                stamps.append(stamp)
    return version, (max(stamps) if stamps else None)


def _installs(analytics: object, window: str) -> int | None:
    """Sum every install variant for one window; None when Homebrew reports no window."""
    if not isinstance(analytics, dict):
        return None
    install = analytics.get("install")
    if not isinstance(install, dict):
        return None
    block = install.get(window)
    if not isinstance(block, dict):
        return None
    total = 0
    for value in block.values():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            total += int(value)
    return total


def brew_fields(payload: object) -> tuple[str | None, int | None, int | None, int | None]:
    if not isinstance(payload, dict):
        return None, None, None, None
    version = _text(payload.get("versions"), "stable")
    analytics = payload.get("analytics")
    return (
        version,
        _installs(analytics, "30d"),
        _installs(analytics, "90d"),
        _installs(analytics, "365d"),
    )


def request_url(artifact_kind: str, package: str) -> str | None:
    if artifact_kind == "pypi":
        return f"{PYPI_API}/{package}/json"
    if artifact_kind == "homebrew":
        return f"{BREW_API}/{package}.json"
    return None


@oso.model(
    capabilities=oso.Capabilities(fetch=True),
    environment_name="Default",
    depends_on=["currentai.registry.product_artifacts"],
    external_origins=["https://pypi.org", "https://formulae.brew.sh"],
    columns=[
        oso.Column(name="product_slug", type="varchar"),
        oso.Column(name="product_type", type="varchar"),
        oso.Column(name="artifact_kind", type="varchar"),
        oso.Column(name="package", type="varchar"),
        oso.Column(name="latest_version", type="varchar"),
        oso.Column(name="latest_upload_at", type="timestamp"),
        oso.Column(name="installs_30d", type="bigint"),
        oso.Column(name="installs_90d", type="bigint"),
        oso.Column(name="installs_365d", type="bigint"),
        oso.Column(name="http_status", type="bigint"),
        oso.Column(name="fetched_at", type="timestamp"),
    ],
)
async def package_metadata(context: oso.AsyncContext) -> oso.DataFrame:
    result = await context.query(ROSTER_SQL)
    roster = await result.as_pd()
    entries: list[dict] = []
    for row in roster.to_dict("records"):
        kind = row.get("artifact_kind")
        package = row.get("artifact_id")
        if isinstance(kind, str) and isinstance(package, str) and request_url(kind, package):
            entries.append(row)
    if not entries:
        raise RuntimeError("roster query returned no pypi or homebrew artifacts")

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    # One request per distinct (kind, package): a package two products declare is fetched once.
    keys = sorted({(e["artifact_kind"], e["artifact_id"]) for e in entries})
    urls: list[str] = []
    for kind, package in keys:
        url = request_url(kind, package)
        if url is None:  # unreachable: entries were filtered on request_url above
            raise RuntimeError(f"no request url for {kind}:{package}")
        urls.append(url)
    answers = await asyncio.gather(
        *(context.fetch(url, headers=headers) for url in urls),
        return_exceptions=True,
    )

    by_key: dict[tuple[str, str], dict] = {}
    ok = 0
    for (kind, package), response in zip(keys, answers):
        status = None if isinstance(response, BaseException) else response.status
        fields: dict[str, object] = {"latest_version": None, "latest_upload_at": None, "installs_30d": None,
                  "installs_90d": None, "installs_365d": None, "http_status": status}
        if status == 200 and not isinstance(response, BaseException):
            try:
                payload = response.json()
            except Exception:
                payload = None
            if kind == "pypi":
                fields["latest_version"], fields["latest_upload_at"] = pypi_fields(payload)
            else:
                (fields["latest_version"], fields["installs_30d"],
                 fields["installs_90d"], fields["installs_365d"]) = brew_fields(payload)
            if fields["latest_version"] is not None:
                ok += 1
        by_key[(kind, package)] = fields

    if ok == 0:
        raise RuntimeError(f"every one of {len(keys)} registry calls failed to yield a version")

    fetched = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    rows = [
        {
            "product_slug": e["product_slug"],
            "product_type": e.get("product_type"),
            "artifact_kind": e["artifact_kind"],
            "package": e["artifact_id"],
            **by_key[(e["artifact_kind"], e["artifact_id"])],
            "fetched_at": fetched,
        }
        for e in entries
    ]
    return _frame(
        rows,
        [
            ("product_slug", "varchar"),
            ("product_type", "varchar"),
            ("artifact_kind", "varchar"),
            ("package", "varchar"),
            ("latest_version", "varchar"),
            ("latest_upload_at", "timestamp"),
            ("installs_30d", "bigint"),
            ("installs_90d", "bigint"),
            ("installs_365d", "bigint"),
            ("http_status", "bigint"),
            ("fetched_at", "timestamp"),
        ],
    )
