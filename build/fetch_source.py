"""Fetch a cited source the way the sampled re-fetch will fetch it again.

The re-read pass records `http_status` and `content_sha256` for every source behind a
claimed `last_verified`, and `build/check_refetch.py` later re-fetches a sample and compares
the digest. A digest that matches is the proof that the original fetch was real.

That comparison only means something if both fetches are the same operation. A digest taken
with `curl` and re-checked with `requests` differs for reasons that have nothing to do with
whether anybody read the page — a different Accept-Encoding, a different User-Agent served a
different body. Every such difference reads as drift, and a gate whose confirmations are
drowned in false drift stops being read.

So this module does not describe how to fetch. It imports `USER_AGENT` and re-uses the same
`requests` call, and a change there changes both sides at once.

Usage:
    uv run python -m build.fetch_source https://example.com/page
    uv run python -m build.fetch_source --body-dir /tmp/scratch <url> [<url> ...]

Prints one JSON object per URL: url, http_status, content_sha256, bytes, content_type,
final_url (after redirects), and body_path when --body-dir is given. Never raises on a dead
source — an unreachable URL is a finding to record, not a crash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

from build.check_refetch import USER_AGENT

# Statuses that mean "not now" rather than "not here". A single un-retried 429 in the pilot
# was promoted into the justification for a confirmation — the agent read the rate limit as
# evidence that no download figure existed, banded the axis on a fallback signal, and marked
# it confirmed. The figure was there; one retry would have found it.
#
# This is the failure mode worth building a mechanism against, because a transient failure and
# an absent fact look identical at the call site and only one of them is a finding.
TRANSIENT = {403, 408, 425, 429, 500, 502, 503, 504}

BLOB = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/blob/(.+)$")


def canonical(url: str) -> str:
    """Rewrite a GitHub blob URL to its raw form.

    A rendered blob page embeds a per-request CSRF token, so its digest differs on every
    fetch and the weekly sampled re-fetch reports drift forever. The raw file is the same
    bytes every time, which is what makes a digest worth recording. Six of the pilot's cited
    pages were this shape.
    """
    match = BLOB.match(url)
    if not match:
        return url
    owner, repo, rest = match.groups()
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{rest}"


def fetch(
    url: str,
    timeout: float = 20.0,
    body_dir: Path | None = None,
    retries: int = 2,
    backoff: float = 2.0,
    sleep=time.sleep,
) -> dict:
    """Fetch one URL and return what the score file needs to record about it.

    One request, one digest, one body. If `body_dir` is given the bytes that were hashed are
    the bytes written, so a `shows` extract quoted from the file is an extract from the
    response the digest belongs to. Fetching a second time to save the body would break that.

    A transient status is retried, and if it survives the retries the record says
    `transient: true` and carries NO digest. That absence is deliberate: a caller cannot
    accidentally record a rate-limit page as the evidence for a claim, and cannot read the
    failure as proof that the fact is missing. Retry, then report — never infer.
    """
    requested = url
    url = canonical(url)
    record: dict = {"url": url}
    if url != requested:
        record["rewritten_from"] = requested

    attempts = 0
    while True:
        attempts += 1
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT},
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            if attempts <= retries:
                sleep(backoff * attempts)
                continue
            record["http_status"] = None
            record["transient"] = True
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["attempts"] = attempts
            return record

        if response.status_code in TRANSIENT and attempts <= retries:
            sleep(backoff * attempts)
            continue
        break

    record["http_status"] = response.status_code
    record["attempts"] = attempts

    if response.status_code in TRANSIENT:
        # No digest, on purpose. See the docstring.
        record["transient"] = True
        record["bytes"] = len(response.content)
        record["note"] = (
            f"HTTP {response.status_code} after {attempts} attempts. The host declined to "
            f"answer; this says nothing about whether the fact exists. Retry later or defer "
            f"the axis. Do NOT record this as evidence and do NOT read it as an absence."
        )
        return record

    record["content_sha256"] = hashlib.sha256(response.content).hexdigest()
    record["bytes"] = len(response.content)
    record["content_type"] = response.headers.get("Content-Type", "")
    record["final_url"] = response.url
    if response.url != url:
        record["redirected"] = True

    if body_dir is not None and response.status_code < 400:
        body_dir.mkdir(parents=True, exist_ok=True)
        path = body_dir / f"{quote(url, safe='')[:150]}.body"
        path.write_bytes(response.content)
        record["body_path"] = str(path)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--body-dir",
        help="write each body here, so `shows` can be quoted from what was actually served",
    )
    args = parser.parse_args()

    body_dir = Path(args.body_dir) if args.body_dir else None

    for url in args.urls:
        print(json.dumps(fetch(url, args.timeout, body_dir)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
