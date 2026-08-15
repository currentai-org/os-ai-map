# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""Live GitHub repo state for the declared gap-map roster.

Roster comes from `currentai.registry.product_artifacts`, filtered to the github
kind — the repo's own declaration, pushed out by CI, so coverage tracks the map
rather than a hand-uploaded snapshot. Grain is one row per (product, repo) pair,
since a few products declare more than one repo.

Deliberately narrow. It does NOT compute contributor counts or commit activity —
`currentai.events` / `currentai.metrics` carry GitHub Archive activity and
`currentai.scores.stack_contributors` carries contributors. This model covers
what nothing else does: first-party repo state for adoption, liveness, and the
license component of openness.

Three design rules:
  * Partial failure is data, not an exception. A per-repo `http_status` is
    recorded rather than raised, so one dead repo cannot kill the whole run. A
    404 is itself a signal that a product may have gone private or been deleted.
  * A 301 is free rename detection. `context.fetch` does not follow redirects,
    so the Location header tells us a repo moved. Renames are the same class of
    breakage that took down the roadmap label match in CUR-131.
  * GitHub reports NOASSERTION for genuinely-licensed repos that carry a custom
    copyright line. For those only, make a second call and keep the first line of
    the LICENSE so the false negative is visible downstream.
"""

import asyncio
import base64
from datetime import datetime, timezone

import oso
import polars as pl

GITHUB_API = "https://api.github.com"
ROSTER_SQL = (
    "SELECT product_slug, artifact_id "
    'FROM "currentai"."registry"."product_artifacts" '
    "WHERE artifact_kind = 'github'"
)
NOASSERTION = "NOASSERTION"


def _header(headers: object, name: str) -> str | None:
    """Case-insensitive lookup over an untyped headers mapping."""
    if not isinstance(headers, dict):
        return None
    target = name.lower()
    for key, value in headers.items():
        if isinstance(key, str) and key.lower() == target and isinstance(value, str):
            return value
    return None


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


def _license_field(payload: object, key: str) -> str | None:
    if isinstance(payload, dict):
        block = payload.get("license")
        if isinstance(block, dict):
            value = block.get(key)
            if isinstance(value, str):
                return value
    return None


def _topics(payload: object) -> str | None:
    if isinstance(payload, dict):
        value = payload.get("topics")
        if isinstance(value, list):
            names = [item for item in value if isinstance(item, str)]
            if names:
                return ",".join(names)
    return None


def _license_first_line(payload: object) -> str | None:
    """Decode the base64 LICENSE body and return its first meaningful line."""
    if not isinstance(payload, dict):
        return None
    content = payload.get("content")
    if not isinstance(content, str):
        return None
    try:
        decoded = base64.b64decode(content).decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return None
    for line in decoded.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return None


def _needs_license_probe(has_payload: bool, spdx: str | None) -> bool:
    """GitHub's NOASSERTION is a known false negative worth a second look."""
    return has_payload and (spdx is None or spdx == NOASSERTION)


def _is_api_repo_url(url: str | None) -> bool:
    """Guard the redirect hop to the GitHub API origin we already declared."""
    return url is not None and url.startswith(f"{GITHUB_API}/repositories/")


@oso.model(
    secrets=["GITHUB_TOKEN"],
    environment_name="Default",
    depends_on=["currentai.registry.product_artifacts"],
    external_origins=["https://api.github.com"],
)
async def repo_state(context: oso.AsyncContext) -> oso.DataFrame:
    token: str = await context.secret("GITHUB_TOKEN")
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    result = await context.query(ROSTER_SQL)
    roster = await result.as_pl()
    slugs: list[str] = []
    repos: list[str] = []
    for row in roster.iter_rows(named=True):
        slug = row.get("product_slug")
        repo = row.get("artifact_id")
        if isinstance(slug, str) and isinstance(repo, str) and "/" in repo:
            slugs.append(slug)
            repos.append(repo)
    if not repos:
        raise RuntimeError("roster query returned no usable repos")

    responses = await asyncio.gather(
        *(context.fetch(f"{GITHUB_API}/repos/{repo}", headers=headers) for repo in repos)
    )

    payloads: list[object] = []
    statuses: list[int] = []
    locations: list[str | None] = []
    remaining: int | None = None
    ok_count = 0

    for response in responses:
        statuses.append(response.status)
        locations.append(_header(response.headers, "location"))
        seen = _header(response.headers, "x-ratelimit-remaining")
        if seen is not None and seen.isdigit():
            remaining = int(seen)
        if response.status == 200:
            ok_count += 1
            payloads.append(response.json())
        else:
            payloads.append(None)

    if ok_count == 0:
        raise RuntimeError(
            f"every one of {len(repos)} GitHub calls failed; first status {statuses[0]}"
        )

    # Resolve the 301s. Most are case mismatches in the declared roster rather
    # than real renames (GitHub redirects when casing differs), and the Location
    # header points at /repositories/{id}, which returns the full payload under
    # its canonical name. Without this hop those rows carry no data at all.
    redirected = [
        index
        for index, status in enumerate(statuses)
        if status == 301 and _is_api_repo_url(locations[index])
    ]
    resolved_flags: list[bool] = [False] * len(repos)
    if redirected:
        followed = await asyncio.gather(
            *(
                context.fetch(str(locations[index]), headers=headers)
                for index in redirected
            )
        )
        for index, response in zip(redirected, followed):
            if response.status == 200:
                payloads[index] = response.json()
                resolved_flags[index] = True

    # Second pass, only for the ambiguous-license repos. Keyed on having a
    # payload, so redirect-resolved repos get probed too.
    probe_index = [
        index
        for index in range(len(repos))
        if _needs_license_probe(
            payloads[index] is not None, _license_field(payloads[index], "spdx_id")
        )
    ]
    first_lines: list[str | None] = [None] * len(repos)
    if probe_index:
        probe_responses = await asyncio.gather(
            *(
                context.fetch(f"{GITHUB_API}/repos/{repos[index]}/license", headers=headers)
                for index in probe_index
            )
        )
        for index, response in zip(probe_index, probe_responses):
            if response.status == 200:
                first_lines[index] = _license_first_line(response.json())

    fetched = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)

    rows: list[dict] = []
    for index, repo in enumerate(repos):
        payload = payloads[index]
        spdx = _license_field(payload, "spdx_id")
        rows.append(
            {
                "product_slug": slugs[index],
                "repo": repo,
                "resolved_repo": _text(payload, "full_name"),
                "github_id": _number(payload, "id"),
                "node_id": _text(payload, "node_id"),
                "html_url": _text(payload, "html_url"),
                "homepage": _text(payload, "homepage"),
                "description": _text(payload, "description"),
                "stargazers_count": _number(payload, "stargazers_count"),
                "forks_count": _number(payload, "forks_count"),
                "subscribers_count": _number(payload, "subscribers_count"),
                "open_issues_count": _number(payload, "open_issues_count"),
                "created_at": _stamp(payload, "created_at"),
                "updated_at": _stamp(payload, "updated_at"),
                "pushed_at": _stamp(payload, "pushed_at"),
                "is_archived": _flag(payload, "archived"),
                "is_disabled": _flag(payload, "disabled"),
                "is_fork": _flag(payload, "fork"),
                "primary_language": _text(payload, "language"),
                "topics": _topics(payload),
                "size_kb": _number(payload, "size"),
                "default_branch": _text(payload, "default_branch"),
                "license_spdx_id": spdx,
                "license_key": _license_field(payload, "key"),
                "license_name": _license_field(payload, "name"),
                "license_is_noassertion": spdx == NOASSERTION,
                "license_first_line": first_lines[index],
                "http_status": statuses[index],
                "redirect_location": locations[index],
                "resolved_via_redirect": resolved_flags[index],
                "rate_limit_remaining": remaining,
                "fetched_at": fetched,
            }
        )

    return pl.DataFrame(
        rows,
        schema={
            "product_slug": pl.Utf8,
            "repo": pl.Utf8,
            "resolved_repo": pl.Utf8,
            "github_id": pl.Int64,
            "node_id": pl.Utf8,
            "html_url": pl.Utf8,
            "homepage": pl.Utf8,
            "description": pl.Utf8,
            "stargazers_count": pl.Int64,
            "forks_count": pl.Int64,
            "subscribers_count": pl.Int64,
            "open_issues_count": pl.Int64,
            "created_at": pl.Datetime("us"),
            "updated_at": pl.Datetime("us"),
            "pushed_at": pl.Datetime("us"),
            "is_archived": pl.Boolean,
            "is_disabled": pl.Boolean,
            "is_fork": pl.Boolean,
            "primary_language": pl.Utf8,
            "topics": pl.Utf8,
            "size_kb": pl.Int64,
            "default_branch": pl.Utf8,
            "license_spdx_id": pl.Utf8,
            "license_key": pl.Utf8,
            "license_name": pl.Utf8,
            "license_is_noassertion": pl.Boolean,
            "license_first_line": pl.Utf8,
            "http_status": pl.Int64,
            "redirect_location": pl.Utf8,
            "resolved_via_redirect": pl.Boolean,
            "rate_limit_remaining": pl.Int64,
            "fetched_at": pl.Datetime("us"),
        },
    )
