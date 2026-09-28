# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""Live GitHub repo state for the declared gap-map roster.

Roster comes from `currentai.registry.product_artifacts`, filtered to the github
kind. Grain is one row per (product, repo) pair.

See revision 3 for the full design notes. Revision 5 adds the release leg (#708):

- latest_release_tag / latest_release_published_at: the first entry of /releases, which
  GitHub orders by creation, not by version. A repo with no releases falls back to the
  first /tags entry, with published_at left null because a tag carries no date here.
- release_asset_downloads: assets[].download_count summed over EVERY release, paginated.
  Page one alone undercounts (llamafile: 191K on page one against 284K across 43 releases).
- release_count, release_pages_truncated: how many releases were read, and whether the
  page cap stopped the walk. A truncated sum is a floor and says so rather than passing
  for a total.
- releases_http_status: the status of the first releases call. A failed release fetch is
  a row with nulls in these columns and never fails the model, so a GitHub hiccup on the
  releases endpoint cannot take stars, license and liveness down with it.

Revision 8 adds eligible_asset_downloads and eligible_asset_count (#664): the same walk, counting
only assets that deliver the product itself. Checksums, signatures, SBOMs and provenance files,
and .json/.yaml/.txt/.md files (manifests, metadata and notes) are excluded; installers,
archives, packages, scripts and bare binaries count. kueue is the case the rule exists for: its
lifetime total is mostly Kubernetes manifests pulled by CI. Both are LIFETIME counters. They are
captured weekly into the repository's counter history, and the monthly figure is the increment,
an interim measure until the platform supports incremental models.

No is_prerelease column, deliberately: check_channel_authority compares version strings and
ignores GitHub's prerelease flag, and a column would invite someone to read it.
"""

import asyncio
import base64
from datetime import datetime, timezone

import oso
import pandas as pd

GITHUB_API = "https://api.github.com"
ROSTER_SQL = (
    "SELECT product_slug, artifact_id "
    'FROM "currentai"."registry"."product_artifacts" '
    "WHERE artifact_kind = 'github'"
)
NOASSERTION = "NOASSERTION"
# Asset names that are not the product: checksums, signatures, SBOMs and attestations, and
# manifest, metadata or note files. Matched on the lowercased name's ending.
NOT_PRODUCT_SUFFIXES = (".sha256", ".sha256sum", ".sha512", ".sha512sum", ".sha1", ".md5", ".sum", ".asc", ".sig", ".pem", ".crt", ".cert", ".sbom", ".spdx", ".intoto.jsonl", ".att", ".bundle", ".json", ".yaml", ".yml", ".txt", ".md", ".html", ".pdf")
# Name fragments that mark the same kinds of file whatever their extension.
NOT_PRODUCT_FRAGMENTS = ("checksum", "sha256sums", "sha512sums", "provenance", "attestation", "sbom")
RELEASES_PER_PAGE = 100
# 100 pages is 10,000 releases. The largest roster repo seen, ggml-org/llama.cpp, had 7,386
# on 2026-09-28, so the cap binds on nothing today; release_pages_truncated says when it does.
MAX_RELEASE_PAGES = 100


def _header(headers: object, name: str) -> str | None:
    if not isinstance(headers, dict):
        return None
    target = name.lower()
    for key, value in headers.items():
        if isinstance(key, str) and key.lower() == target and isinstance(value, str):
            return value
    return None




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
    return has_payload and (spdx is None or spdx == NOASSERTION)


def _is_product_asset(asset: object) -> bool:
    name = _text(asset, "name")
    if name is None:
        return False
    lowered = name.lower()
    if lowered.endswith(NOT_PRODUCT_SUFFIXES):
        return False
    return not any(fragment in lowered for fragment in NOT_PRODUCT_FRAGMENTS)


def _eligible(release: object) -> tuple[int, int]:
    """(downloads, count) over the release's assets that deliver the product itself."""
    if not isinstance(release, dict):
        return 0, 0
    assets = release.get("assets")
    if not isinstance(assets, list):
        return 0, 0
    kept = [asset for asset in assets if _is_product_asset(asset)]
    return sum(_number(asset, "download_count") or 0 for asset in kept), len(kept)


def _asset_downloads(release: object) -> int:
    if not isinstance(release, dict):
        return 0
    assets = release.get("assets")
    if not isinstance(assets, list):
        return 0
    return sum(_number(asset, "download_count") or 0 for asset in assets)


def _is_api_repo_url(url: str | None) -> bool:
    return url is not None and url.startswith(f"{GITHUB_API}/repositories/")


@oso.model(
    capabilities=oso.Capabilities(fetch=True),
    secrets=["GITHUB_TOKEN"],
    environment_name="Default",
    depends_on=["currentai.registry.product_artifacts"],
    external_origins=["https://api.github.com"],
    columns=[
        oso.Column(name="product_slug", type="varchar"),
        oso.Column(name="repo", type="varchar"),
        oso.Column(name="resolved_repo", type="varchar"),
        oso.Column(name="github_id", type="bigint"),
        oso.Column(name="node_id", type="varchar"),
        oso.Column(name="html_url", type="varchar"),
        oso.Column(name="homepage", type="varchar"),
        oso.Column(name="description", type="varchar"),
        oso.Column(name="stargazers_count", type="bigint"),
        oso.Column(name="forks_count", type="bigint"),
        oso.Column(name="subscribers_count", type="bigint"),
        oso.Column(name="open_issues_count", type="bigint"),
        oso.Column(name="created_at", type="timestamp"),
        oso.Column(name="updated_at", type="timestamp"),
        oso.Column(name="pushed_at", type="timestamp"),
        oso.Column(name="is_archived", type="boolean"),
        oso.Column(name="is_disabled", type="boolean"),
        oso.Column(name="is_fork", type="boolean"),
        oso.Column(name="primary_language", type="varchar"),
        oso.Column(name="topics", type="varchar"),
        oso.Column(name="size_kb", type="bigint"),
        oso.Column(name="default_branch", type="varchar"),
        oso.Column(name="license_spdx_id", type="varchar"),
        oso.Column(name="license_key", type="varchar"),
        oso.Column(name="license_name", type="varchar"),
        oso.Column(name="license_is_noassertion", type="boolean"),
        oso.Column(name="license_first_line", type="varchar"),
        oso.Column(name="http_status", type="bigint"),
        oso.Column(name="redirect_location", type="varchar"),
        oso.Column(name="resolved_via_redirect", type="boolean"),
        oso.Column(name="rate_limit_remaining", type="bigint"),
        oso.Column(name="fetched_at", type="timestamp"),
        oso.Column(name="latest_release_tag", type="varchar"),
        oso.Column(name="latest_release_published_at", type="timestamp"),
        oso.Column(name="release_count", type="bigint"),
        oso.Column(name="release_asset_downloads", type="bigint"),
        oso.Column(name="release_pages_truncated", type="boolean"),
        oso.Column(name="releases_http_status", type="bigint"),
        oso.Column(name="eligible_asset_downloads", type="bigint"),
        oso.Column(name="eligible_asset_count", type="bigint"),
    ],
)
async def artifact_state(context: oso.AsyncContext) -> oso.DataFrame:
    token: str = await context.secret("GITHUB_TOKEN")
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    result = await context.query(ROSTER_SQL)
    roster = await result.as_pd()
    slugs: list[str] = []
    repos: list[str] = []
    for row in roster.to_dict("records"):
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
            remaining = int(seen) if remaining is None else min(remaining, int(seen))
        if response.status == 200:
            ok_count += 1
            payloads.append(response.json())
        else:
            payloads.append(None)

    if ok_count == 0:
        raise RuntimeError(
            f"every one of {len(repos)} GitHub calls failed; first status {statuses[0]}"
        )

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
            seen = _header(response.headers, "x-ratelimit-remaining")
            if seen is not None and seen.isdigit():
                remaining = int(seen) if remaining is None else min(remaining, int(seen))
            if response.status == 200:
                payloads[index] = response.json()
                resolved_flags[index] = True

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
            seen = _header(response.headers, "x-ratelimit-remaining")
            if seen is not None and seen.isdigit():
                remaining = int(seen) if remaining is None else min(remaining, int(seen))
            if response.status == 200:
                first_lines[index] = _license_first_line(response.json())

    # Release leg. Walk /releases one page per round across every repo still paging, so the
    # calls stay parallel across repos and each repo stops as soon as a short page arrives.
    # Every failure here lands as nulls on the row; nothing in this block raises.
    def _release_repo(index: int) -> str:
        return _text(payloads[index], "full_name") or repos[index]

    latest_tag: list[str | None] = [None] * len(repos)
    latest_published: list[datetime | None] = [None] * len(repos)
    release_counts: list[int | None] = [None] * len(repos)
    asset_totals: list[int | None] = [None] * len(repos)
    truncated: list[bool | None] = [None] * len(repos)
    eligible_downloads: list[int | None] = [None] * len(repos)
    eligible_counts: list[int | None] = [None] * len(repos)
    release_status: list[int | None] = [None] * len(repos)

    paging = [index for index in range(len(repos)) if payloads[index] is not None]
    page = 1
    while paging:
        answers = await asyncio.gather(
            *(
                context.fetch(
                    f"{GITHUB_API}/repos/{_release_repo(index)}/releases"
                    f"?per_page={RELEASES_PER_PAGE}&page={page}",
                    headers=headers,
                )
                for index in paging
            ),
            return_exceptions=True,
        )
        still: list[int] = []
        for index, response in zip(paging, answers):
            if isinstance(response, BaseException):
                release_counts[index] = None
                asset_totals[index] = None
                truncated[index] = None
                eligible_downloads[index] = None
                eligible_counts[index] = None
                continue
            status = response.status
            # Read quota on every answer, failures included: a 403 for an exhausted limit is the
            # response whose header matters most.
            seen = _header(response.headers, "x-ratelimit-remaining")
            if seen is not None and seen.isdigit():
                remaining = int(seen) if remaining is None else min(remaining, int(seen))
            if page == 1:
                release_status[index] = status
            if status != 200:
                # A failure part-way through leaves a partial sum, which is not a total.
                release_counts[index] = None
                asset_totals[index] = None
                truncated[index] = None
                eligible_downloads[index] = None
                eligible_counts[index] = None
                continue
            try:
                body = response.json()
            except Exception:
                body = None
            if not isinstance(body, list):
                release_counts[index] = None
                asset_totals[index] = None
                truncated[index] = None
                eligible_downloads[index] = None
                eligible_counts[index] = None
                continue
            if page == 1:
                release_counts[index] = 0
                asset_totals[index] = 0
                truncated[index] = False
                eligible_downloads[index] = 0
                eligible_counts[index] = 0
                if body:
                    latest_tag[index] = _text(body[0], "tag_name")
                    latest_published[index] = _stamp(body[0], "published_at")
            count_so_far = release_counts[index]
            assets_so_far = asset_totals[index]
            if count_so_far is None or assets_so_far is None:
                continue
            release_counts[index] = count_so_far + len(body)
            asset_totals[index] = assets_so_far + sum(_asset_downloads(item) for item in body)
            eligible_so_far = eligible_downloads[index]
            eligible_count_so_far = eligible_counts[index]
            if eligible_so_far is not None and eligible_count_so_far is not None:
                pairs = [_eligible(item) for item in body]
                eligible_downloads[index] = eligible_so_far + sum(d for d, _ in pairs)
                eligible_counts[index] = eligible_count_so_far + sum(c for _, c in pairs)
            # Continue on the Link header, not on a full page. A short page mid-walk was
            # observed on 2026-09-28 (llama.cpp stopped at 1,100 of 7,386 releases), and a
            # page-length test reads that as the end and undercounts without a trace.
            link = _header(response.headers, "link") or ""
            if 'rel="next"' in link:
                if page < MAX_RELEASE_PAGES:
                    still.append(index)
                else:
                    truncated[index] = True
        paging = still
        page += 1

    # Tags fallback, only for repos whose releases call succeeded and came back empty.
    tagless = [
        index
        for index in range(len(repos))
        if release_counts[index] == 0 and latest_tag[index] is None
    ]
    if tagless:
        tag_answers = await asyncio.gather(
            *(
                context.fetch(
                    f"{GITHUB_API}/repos/{_release_repo(index)}/tags?per_page=1",
                    headers=headers,
                )
                for index in tagless
            ),
            return_exceptions=True,
        )
        for index, response in zip(tagless, tag_answers):
            if isinstance(response, BaseException):
                continue
            seen = _header(response.headers, "x-ratelimit-remaining")
            if seen is not None and seen.isdigit():
                remaining = int(seen) if remaining is None else min(remaining, int(seen))
            if response.status != 200:
                continue
            try:
                body = response.json()
            except Exception:
                continue
            if isinstance(body, list) and body:
                latest_tag[index] = _text(body[0], "name")

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
                "latest_release_tag": latest_tag[index],
                "latest_release_published_at": latest_published[index],
                "release_count": release_counts[index],
                "release_asset_downloads": asset_totals[index],
                "release_pages_truncated": truncated[index],
                "releases_http_status": release_status[index],
                "eligible_asset_downloads": eligible_downloads[index],
                "eligible_asset_count": eligible_counts[index],
            }
        )

    return _frame(
        rows,
        [
            ("product_slug", "varchar"),
            ("repo", "varchar"),
            ("resolved_repo", "varchar"),
            ("github_id", "bigint"),
            ("node_id", "varchar"),
            ("html_url", "varchar"),
            ("homepage", "varchar"),
            ("description", "varchar"),
            ("stargazers_count", "bigint"),
            ("forks_count", "bigint"),
            ("subscribers_count", "bigint"),
            ("open_issues_count", "bigint"),
            ("created_at", "timestamp"),
            ("updated_at", "timestamp"),
            ("pushed_at", "timestamp"),
            ("is_archived", "boolean"),
            ("is_disabled", "boolean"),
            ("is_fork", "boolean"),
            ("primary_language", "varchar"),
            ("topics", "varchar"),
            ("size_kb", "bigint"),
            ("default_branch", "varchar"),
            ("license_spdx_id", "varchar"),
            ("license_key", "varchar"),
            ("license_name", "varchar"),
            ("license_is_noassertion", "boolean"),
            ("license_first_line", "varchar"),
            ("http_status", "bigint"),
            ("redirect_location", "varchar"),
            ("resolved_via_redirect", "boolean"),
            ("rate_limit_remaining", "bigint"),
            ("fetched_at", "timestamp"),
            ("latest_release_tag", "varchar"),
            ("latest_release_published_at", "timestamp"),
            ("release_count", "bigint"),
            ("release_asset_downloads", "bigint"),
            ("release_pages_truncated", "boolean"),
            ("releases_http_status", "bigint"),
            ("eligible_asset_downloads", "bigint"),
            ("eligible_asset_count", "bigint"),
        ],
    )
