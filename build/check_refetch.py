"""The sampled re-fetch: independent evidence that a recorded fetch actually happened.

`docs/reference/evidence-and-freshness.md` is normative. This module implements the gate. It is the third
leg of the anti-rubber-stamping defense the runbook names, and until now the only one that
was missing.

## Why the other two are not enough

The invariant asks whether a claimed date is supported by the `accessed` dates on record.
The digest requirement asks whether the sources carry an `http_status` and a
`content_sha256`. Both are real, and both share a blind spot: **they read what the writer
wrote.** An agent that never opened a page can still emit a plausible `accessed`, a plausible
`200`, and sixty-four plausible hex characters, and both gates pass. That is #108's failure
mode with better spelling.

The sampled re-fetch is the only check that goes and looks.

## What a match proves, and what a mismatch does not

Asymmetric, and the asymmetry is the point:

- **A digest that still matches is proof the original fetch was real.** SHA-256 preimages
  are not guessable, so a recorded digest reproducing from a live body could only have come
  from that body. This is positive evidence, and it is the reason to run the gate.
- **A digest that differs proves nothing on its own.** Pages change. `api.github.com/repos/*`
  carries a star count, HF model endpoints carry download counts — those bodies differ
  between any two requests. Treating drift as failure would make the gate noise, and a noisy
  gate gets switched off.

In practice only stable bodies reproduce — the first full run confirmed four sources, three
arXiv `/abs/` pages and one HF `/raw/` CSV, while every API endpoint carrying a star or
download count drifted. That is the expected shape, and it is why the count of confirmations
is the signal rather than the ratio: an agent that fetched nothing would confirm **zero**,
stable URLs included.

So the report separates *confirmed* from *drifted* and never fails on drift. What it does
fail on is the small set of things that admit no innocent reading:

- **A digest reused across URLs, where one of them provably never served it.** The claim is
  tested rather than assumed — see `resolve_duplicates`. The first rule failed on the mere
  fact of a shared digest, reasoning that byte-identical bodies are "possible but rare", and
  that failed `main` on 2026-08-13 against five repos sharing one digest for their Apache-2.0
  LICENSE. A standard license IS the same bytes everywhere; that is what standard means.
  The second rule failed whenever the group's live bodies disagreed, and that failed the run
  on 2026-09-24 when lakeFS relicensed to BSL-1.1 two days before: 51 repos still served the
  Apache-2.0 text and one had changed its file. A body that differs today says nothing about
  what the URL served on its `accessed` date. GitHub's activity log does: it records every tip
  the branch held, so a member whose body changed is fabrication only when the log covers
  its access window and no tip's copy of the file hashes to the recorded digest.
- **A recorded digest that reproduces over a bot wall.** The recorded bytes are a challenge
  page, so nothing behind any source carrying that digest was ever read.
- **A malformed digest.** `validate.py` enforces the schema pattern, so this should be
  unreachable — it is here because a gate that trusts another gate is how both stop working.

Status regressions (recorded `200`, now `404`) are reported as findings rather than
failures: a page can legitimately die between the read and the check. That is still exactly
the signal a re-read pass wants, and it is how the Lucie source that had never resolved as
cited was found — the URL was missing its `/datasets/` segment and the Hub answered 401 to
anyone who tried it.

## Sampling

The re-read surface is ~1,100 URLs and this runs weekly, so it samples. The sample is seeded
and therefore reproducible: the same seed re-checks the same sources, which is what makes a
newly-drifted source visible rather than lost in the shuffle. `--all` re-fetches everything
carrying a digest, which is the right mode after a bulk pass.

Usage:
    uv run python -m build.check_refetch                    # 25 sampled, report only
    uv run python -m build.check_refetch --all              # every source with a digest
    uv run python -m build.check_refetch --product apertus  # one product
    uv run python -m build.check_refetch --strict           # fail on findings too
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

from build.vocabulary import axes, parse_date, parse_timestamp

ROOT = Path(__file__).resolve().parents[1]
AXES = axes()  # build/vocabulary.py owns this; the score schema declares it

# A real browser-ish UA. Several vendor docs sites answer 403 to the default python-requests
# string, which would otherwise read as a dead source on every run.
# A bot wall answers 200 and hands back a page that is not the document. PyPI serves one
# ("Client Challenge", ~3KB, "JavaScript is disabled in your browser") and on 2026-08-13 two
# sources were digested from it — `pypi.org/project/llm` and `pypi.org/project/pydantic-ai/`
# recorded the SAME digest, because the wall is byte-identical whatever you asked for. That
# tripped the duplicate-digest resolver, which called it fabrication. It was not: nobody
# forged a digest, the fetcher was challenged and hashed the challenge.
#
# It also poisoned a score note. pydantic-ai concluded "the PyPI project page no longer
# serving a readable description" — a permanent claim about the source, from a transient wall.
#
# Same class as the canonical-license and host-alias false positives this module already
# documents: the body is real, it just is not the page. So it is detected in ONE place that
# both the recorder and the re-fetch import, and neither treats it as content.
BOT_WALL_MARKERS = (
    "<title>Client Challenge</title>",
    "JavaScript is disabled in your browser",
    "Enable JavaScript and cookies to continue",
    "Checking your browser before accessing",
)
# Generous next to a real page (PyPI's own project pages are 100KB+) and far above the walls
# seen, which are ~3KB. The bound is what keeps a page that merely QUOTES one of these
# strings — a docs page about bot protection, say — from being discarded as a wall.
BOT_WALL_MAX_BYTES = 25_000


def bot_wall(response: "requests.Response") -> str | None:
    """The marker this body matched, or None if it looks like a document.

    Deliberately narrow: a marker AND a body too small to be the real page. Read the pair as
    "this host declined to serve the document", which is a 429 wearing a 200.
    """
    if len(response.content) > BOT_WALL_MAX_BYTES:
        return None
    try:
        text = response.content.decode("utf-8", "replace")
    except Exception:  # pragma: no cover - decode with replace does not raise
        return None
    for marker in BOT_WALL_MARKERS:
        if marker in text:
            return marker
    return None


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 os-ai-map-verification/1.0"
)

# NO Accept / Accept-Language / Sec-Fetch-* here, and that is a finding rather than an
# omission. On 2026-08-14 the full browser header set was measured against every host that
# was blocking a verification pass — hailo.ai, www.demandsage.com, replit.com, openai.com,
# www.qualcomm.com, www.nxp.com — and it moved nothing: 403 stayed 403, the NXP 404 stayed
# 404, and Qualcomm's client-rendered shell merely grew from 8.7KB to 9.1KB of the same
# shell. Adding headers that fix nothing would still re-digest the whole corpus, because a
# body served under a different Accept can differ byte-for-byte, so every recorded digest
# would drift at once. The cost is real and the benefit measured zero.
#
# Accept-Encoding must NEVER be set on the DEFAULT path, and there are two reasons rather
# than one. Forcing `br` returned a 200 whose `.content` was raw compressed bytes, because
# urllib3 advertises only the codecs it can decode and this environment has no brotli; every
# digest taken that way would be a digest of ciphertext-looking garbage. And setting even a
# decodable value corpus-wide re-digests pages that are otherwise stable: measured 2026-09-17
# over a 24-URL sample spanning one URL per cited host, 16 were stable under a two-fetch
# control and 1 of those 16 returned a different body under `Accept-Encoding: gzip` -
# www.getpanto.ai, same 194,443 bytes, deterministically different digest in each mode.
# 6% of the corpus re-digesting is a real cost with no benefit to the pages already fetchable.
#
# The 403 RETRY below is the narrow exception, and it is narrow on purpose: see
# `_encoding_retry_headers`.
#
# `Authorization` is the one addition, and it is scoped to GitHub's own hosts only: the
# anonymous 60/hour limit turns a 150-product weekly re-verify into a wall of TRANSIENT
# 429s that stamps nothing, and a token only changes GitHub's rate-limit accounting — it
# does not change what bytes a public repo serves, so it carries none of the drift risk the
# rest of this comment warns about.

# Statuses that mean "not now" rather than "not here" — a WAF, a rate limiter or a bad
# gateway, none of which say anything about whether the page exists.
TRANSIENT = {403, 408, 425, 429, 500, 502, 503, 504}

# openai.com sits behind a challenge that lets roughly one request in eight through: eight
# consecutive plain GETs on 2026-08-14 returned 403 403 403 403 403 200 403 403, with no
# header set changing the odds. Three attempts (the old default) clear that about a third of
# the time, which is why `gpt-5` capability kept reading as unfetchable. Six attempts clear
# it about two thirds of the time, and the cost of the extra attempts is paid only by hosts
# that were failing anyway.
RETRIES = 5
BACKOFF = 2.0

# The GitHub blob -> raw rewrite. It lives HERE, beside USER_AGENT, for the reason
# fetch_source's docstring already gives: "this module does not describe how to fetch. It
# imports USER_AGENT and re-uses the same requests call, and a change there changes both
# sides at once." Canonicalization is part of how to fetch, so keeping it in fetch_source
# left this module free to fetch differently — and it did.
#
# A rendered blob page embeds a per-request CSRF token, so its digest differs on every fetch.
# The raw file is the same bytes every time, which is what makes a digest worth recording.
# 86 cited sources are blob URLs; re-fetching them uncanonicalized reported drift forever and
# resolve_duplicates read one as fabrication.
BLOB = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/blob/(.+)$")


def canonical(url: str) -> str:
    """Rewrite a GitHub blob URL to its raw form."""
    match = BLOB.match(url)
    if not match:
        return url
    owner, repo, rest = match.groups()
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{rest}"


# Hosts that share GitHub's anonymous rate limit and accept a token on the same header.
GITHUB_HOSTS = {"github.com", "raw.githubusercontent.com", "api.github.com"}


def _headers(url: str) -> dict[str, str]:
    """`User-Agent` always; `Authorization` added only for GitHub hosts, only when
    `GITHUB_TOKEN` is set. See the note above USER_AGENT for why this is scoped so narrowly.
    """
    headers = {"User-Agent": USER_AGENT}
    token = os.environ.get("GITHUB_TOKEN")
    if token and urlparse(url).hostname in GITHUB_HOSTS:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# Some hosts fingerprint urllib3's default `Accept-Encoding: gzip, deflate` and answer 403
# to it while serving any explicit single-codec value. Measured 2026-09-17 against Huawei
# Cloud, which holds the last citations `modelarts-training` needs:
#
#   support.huaweicloud.com/intl/en-us/productdesc-modelarts/...  default 403 (462 bytes)
#                                                                 gzip     200 (77,230 bytes)
#   www.huaweicloud.com/intl/en-us/product/modelarts.html         default 403 (426 bytes)
#                                                                 gzip     200 (104,206 bytes)
#
# `identity` and `*` behave the same as `gzip` on both, so the value is not the point - being
# explicit is. This fires ONLY after a 403 on the default path, so no page that is already
# fetchable changes its bytes, and both the writer and the gate reach it through the same
# condition, so a digest recorded on the retry is reproduced by the retry.
#
# THE ONE CASE THAT CAN STILL MISMATCH, stated rather than left to be discovered: a host that
# 403s INTERMITTENTLY can serve the writer on the default path and the gate on the retry, or
# the reverse, and the two bodies can differ - measured at 1 of 16 otherwise stable pages. The
# consequence is bounded, because `check_refetch` reports a changed body as DRIFTED, a re-check
# queue entry rather than a failure, and drift on a challenge-protected host is expected
# anyway. Recording which mode produced a digest would close it properly, and that is a schema
# change on every source rather than a fix belonging to this one.
def _encoding_retry_headers(url: str) -> dict[str, str]:
    return {**_headers(url), "Accept-Encoding": "gzip"}


def http_get(
    url: str,
    timeout: float = 20.0,
    retries: int = RETRIES,
    backoff: float = BACKOFF,
    sleep=time.sleep,
) -> requests.Response:
    """One canonicalized GET, retrying the statuses that mean "not now".

    This is "how to fetch", and it lives here for the reason USER_AGENT and `canonical` do:
    `build/fetch_source` records a digest and this module re-checks it, and the comparison
    only means something if both sides performed the same operation. Retry policy is part of
    that. Before this existed only fetch_source retried, so an intermittently-challenged host
    could be recorded at 200 by the writer and then reported DEAD by the gate on a single
    unlucky roll — the gate calling a live page dead is exactly the noise its own docstring
    warns kills a gate.

    Raises `requests.RequestException` like a plain `requests.get`; a status is returned, not
    raised on, because a 404 is a finding to record rather than a crash.
    """
    url = canonical(url)
    attempts = 0
    encoding_retried = False
    while True:
        attempts += 1
        try:
            response = requests.get(
                url, timeout=timeout, headers=_headers(url), allow_redirects=True
            )
        except requests.RequestException:
            if attempts <= retries:
                sleep(backoff * attempts)
                continue
            raise
        # The encoding retry goes BEFORE the transient backoff, not after it. A header
        # fingerprint answers 403 to every attempt, so waiting three times to ask the same
        # question costs six requests and two sleeps to learn nothing.
        if response.status_code == 403 and not encoding_retried:
            encoding_retried = True
            try:
                retried = requests.get(
                    url,
                    timeout=timeout,
                    headers=_encoding_retry_headers(url),
                    allow_redirects=True,
                )
            except requests.RequestException:
                pass  # the 403 stands as the finding; a failed retry does not replace it
            else:
                attempts += 1
                # A retry that comes back TRANSIENT falls through to the backoff below rather
                # than returning: a gzip-path 503 is still "not now", and returning it here
                # would spend the fingerprint check and skip the retries the 503 deserves.
                if retried.status_code not in TRANSIENT:
                    retried.attempts = attempts  # type: ignore[attr-defined]
                    retried.encoding_retry = True  # type: ignore[attr-defined]
                    return retried
                response = retried
        if response.status_code in TRANSIENT and attempts <= retries:
            sleep(backoff * attempts)
            continue
        response.attempts = attempts  # type: ignore[attr-defined]
        return response



@dataclass(frozen=True)
class Source:
    product: str
    axis: str
    url: str
    digest: str
    status: object
    accessed: object

    @property
    def key(self) -> str:
        return f"{self.product}:{self.axis}"


def load_sources(product: str | None = None) -> list[Source]:
    """Every source across every score file that records a digest."""
    out: list[Source] = []
    for path in sorted((ROOT / "sources" / "scores").glob("*.yaml")):
        if product and path.stem != product:
            continue
        score = yaml.safe_load(path.read_text()) or {}
        for axis in AXES:
            block = score.get(axis) or {}
            if not isinstance(block, dict):
                continue
            lists = [(axis, block.get("sources"))]
            # A comparison attestation cites the ROOT of a peer comparison, so it lives in its
            # own list rather than in capability.sources — folding it in would let another
            # product's page count as this one's evidence. It is still a recorded fetch, and
            # it is the one kind of citation nobody re-reads on the product's own refresh, so
            # the weekly re-fetch wants it more than most.
            comparison = block.get("comparison")
            if isinstance(comparison, dict):
                lists.append((f"{axis}.comparison", comparison.get("sources")))
            for label, sources in lists:
                for source in sources or []:
                    if not isinstance(source, dict):
                        continue
                    digest = source.get("content_sha256")
                    if not digest:
                        continue
                    out.append(
                        Source(
                            product=path.stem,
                            axis=label,
                            url=str(source.get("url") or ""),
                            digest=str(digest),
                            status=source.get("http_status"),
                            accessed=source.get("accessed"),
                        )
                    )
    return out


def offline_failures(sources: list[Source]) -> list[str]:
    """Checks that need no network and admit no innocent reading."""
    problems: list[str] = []

    for source in sources:
        if len(source.digest) != 64 or any(c not in "0123456789abcdef" for c in source.digest):
            problems.append(
                f"{source.key}: {source.url!r} records {source.digest!r}, which is not a "
                f"SHA-256. Nothing that fetched a body would produce it."
            )

    return problems


def duplicate_digest_groups(sources: list[Source]) -> list[tuple[str, list[str]]]:
    """Digests recorded against more than one URL, for the resolver below."""
    by_digest: dict[str, set[str]] = defaultdict(set)
    for source in sources:
        by_digest[source.digest].add(source.url)
    return [(d, sorted(u)) for d, u in sorted(by_digest.items()) if len(u) > 1]


# GitHub's repository activity API (`GET /repos/{owner}/{repo}/activity`) records every update
# to a ref: pushes, force pushes, PR and merge-queue merges, branch creation and deletion, each
# with the `before` and `after` SHA. Probed 2026-09-24, it is not a rolling window: its earliest
# record is 2023-03-07 on every repo tried (treeverse/lakeFS, huggingface/peft,
# vllm-project/vllm, torvalds/linux), whatever the repo's age, and a repo with no pushes since
# (octocat/Hello-World) returns an empty list. So the log is complete from that date on, and an
# access window must start after it with margin, or the member is unresolved.
ACTIVITY_LOG_START = date(2023, 4, 1)

# The access window around a recorded `accessed` date: the day before through the day after,
# in UTC. `accessed` is a calendar date written by whoever fetched, in whatever timezone, and
# the raw CDN caches a branch URL for a few minutes, so a tip that landed just across midnight
# must still count.
ACCESS_WINDOW_BEFORE = timedelta(days=1)
ACCESS_WINDOW_AFTER = timedelta(days=2)

# Pages of activity (100 entries each) walked back from now before giving up. A busy repo's
# default branch sees a few dozen updates a week, so ten pages reach back months. Past the cap
# before reaching the window, the member is UNRESOLVED.
MAX_ACTIVITY_PAGES = 10

ZERO_SHA = "0" * 40

# raw.githubusercontent.com/{owner}/{repo}/{ref...}/{path...}, the form `canonical` produces.
# The ref may itself contain slashes, so where it ends is resolved against the repo's refs in
# `_resolve_branch`, never guessed from the URL.
RAW = re.compile(r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/(.+)$")


def _api_get(url: str, timeout: float, params: dict | None = None):
    """One GitHub API GET, or None on a network error. Callers treat None as unresolved."""
    try:
        return requests.get(url, params=params, headers=_headers(url), timeout=timeout)
    except requests.RequestException:
        return None


def _resolve_branch(
    owner: str, repo: str, rest: str, timeout: float
) -> tuple[str, str] | str:
    """(branch, path), or a reason string when the ref/path boundary cannot be settled.

    `main/LICENSE` splits one way, but `feature/x/LICENSE` could be branch `feature/x` with path
    `LICENSE` or branch `feature` with path `x/LICENSE`, and if both exist the wrong split hashes
    a different file. So every candidate split is checked against the repo's real refs (heads
    AND tags, via `git/matching-refs`, which prefix-matches), and only a single resolution that
    is a branch is accepted. A tag can be moved without a trace in the branch activity log, and
    a commit SHA has no activity at all, so both are unresolved rather than guessed at.
    """
    segments = rest.split("/")
    if len(segments) < 2:
        return "the URL has no path after its ref"
    candidates = {"/".join(segments[:k]): "/".join(segments[k:]) for k in range(1, len(segments))}
    found: list[tuple[str, str]] = []
    for kind in ("heads", "tags"):
        response = _api_get(
            f"https://api.github.com/repos/{owner}/{repo}/git/matching-refs/{kind}/{segments[0]}",
            timeout,
        )
        if response is None or response.status_code != 200:
            code = "network error" if response is None else f"HTTP {response.status_code}"
            return f"the ref lookup failed ({code})"
        try:
            names = [r["ref"].split(f"refs/{kind}/", 1)[1] for r in response.json()]
        except (ValueError, LookupError, TypeError, AttributeError):
            return "the ref lookup returned something other than a ref list"
        found += [(kind, name) for name in names if name in candidates]
    if not found:
        return f"no branch or tag of {owner}/{repo} matches the URL's ref"
    if len(found) > 1:
        refs = ", ".join(f"{k}/{n}" for k, n in found)
        return f"the URL's ref is ambiguous ({refs} all match), so which file it names is not known"
    kind, name = found[0]
    if kind != "heads":
        return f"the URL names tag {name}, which can move without a trace in the activity log"
    return name, candidates[name]


def _branch_activity(
    owner: str, repo: str, branch: str, since: datetime, timeout: float
) -> list[dict] | str:
    """Every activity entry on the branch from `since` to now, oldest first, plus the newest
    entry before `since` if there is one (it pins the tip entering the window). A reason string
    when the log cannot be read that far back."""
    url: str | None = f"https://api.github.com/repos/{owner}/{repo}/activity"
    params: dict | None = {"ref": f"refs/heads/{branch}", "per_page": 100}
    entries: list[dict] = []
    for _ in range(MAX_ACTIVITY_PAGES):
        response = _api_get(url, timeout, params)
        if response is None or response.status_code != 200:
            code = "network error" if response is None else f"HTTP {response.status_code}"
            return f"the activity lookup failed ({code})"
        try:
            page = [
                {"when": parse_timestamp(e["timestamp"]), "before": e["before"], "after": e["after"],
                 "type": e["activity_type"]}
                for e in response.json()
            ]
        except (ValueError, LookupError, TypeError):
            return "the activity lookup returned something other than an activity list"
        if any(e["when"] is None for e in page):
            return "the activity log carries an unreadable timestamp"
        entries += page
        if any(e["when"] < since for e in page):
            break
        url = (getattr(response, "links", None) or {}).get("next", {}).get("url")
        params = None  # the next link carries its own query string
        if not url:
            break  # the log ends; it starts on ACTIVITY_LOG_START, which the caller checked
    else:
        return f"the activity log is longer than {MAX_ACTIVITY_PAGES} pages back to the access window"
    entries.sort(key=lambda e: e["when"])
    before = [e for e in entries if e["when"] < since]
    return before[-1:] + [e for e in entries if e["when"] >= since]


def served_on_access_verdict(
    url: str, digest: str, accessed: set[date], timeout: float = 20.0
) -> tuple[str, str]:
    """Did this URL serve `digest` on (one of) its recorded access dates? (verdict, detail).

    Rebuilds what the URL served rather than inferring it. For a GitHub file on a branch, the
    repository activity log gives every SHA the branch tip held during the access window: the
    tip entering the window, and the `after` of every update inside it. Each tip's copy of the
    file is fetched from `raw.githubusercontent.com/{owner}/{repo}/{sha}/{path}` through
    `http_get` and hashed over its raw bytes, the same operation `build/fetch_source` performed
    on the branch URL. A force push, a deleted and recreated branch or a rewritten history
    changes nothing here: the log records the tips the branch actually held, before and after.

    - `served`: a tip during the window hashes to the digest. Drift.
    - `never`: the log covers the whole window and no tip's copy hashes to it. The URL could not
      have served it on any recorded access date. Fabrication.
    - `unresolved`: anything short of that. Not a GitHub file; a ref that is a tag, a SHA,
      ambiguous or gone; a failed or rate-limited lookup; a window that predates
      ACTIVITY_LOG_START or lies beyond MAX_ACTIVITY_PAGES; a tip whose file cannot be fetched;
      no recorded access date.

    A tip whose copy answers 404 counts as "did not have the file" only once the commit itself is
    confirmed to exist; a tip that is gone (force-pushed away and collected) is unresolved. Every
    other error is unresolved.

    Known limit: the verdict is about the URL as parsed. If the live fetch was redirected (a
    renamed repo, say), the API calls follow the same redirect but nothing checks that the
    redirect landed on the same path.
    """
    match = RAW.match(canonical(url))
    if not match:
        return "unresolved", f"{urlparse(url).hostname} has no ref history this check can read"
    if not accessed:
        return "unresolved", "no recorded access date to rebuild"
    owner, repo, rest = match.groups()
    resolved = _resolve_branch(owner, repo, rest, timeout)
    if isinstance(resolved, str):
        return "unresolved", resolved
    branch, path = resolved

    windows = [
        (datetime.combine(d - ACCESS_WINDOW_BEFORE, datetime.min.time(), timezone.utc),
         datetime.combine(d + ACCESS_WINDOW_AFTER, datetime.min.time(), timezone.utc))
        for d in sorted(accessed)
    ]
    since = windows[0][0]
    if since.date() < ACTIVITY_LOG_START:
        return "unresolved", f"the access window predates the activity log ({ACTIVITY_LOG_START})"
    entries = _branch_activity(owner, repo, branch, since, timeout)
    if isinstance(entries, str):
        return "unresolved", entries

    tips: set[str] = set()
    for start, end in windows:
        prior = [e for e in entries if e["when"] < start]
        later = [e for e in entries if e["when"] >= start]
        if later:
            tips.add(later[0]["before"])  # the tip entering the window
        elif prior:
            tips.add(prior[-1]["after"])  # nothing since, so the latest update is still the tip
        else:
            head = _api_get(f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}", timeout)
            try:
                tips.add(head.json()["commit"]["sha"])  # no update since the log began
            except (AttributeError, ValueError, LookupError, TypeError):
                return "unresolved", "the branch head lookup failed"
        tips.update(e["after"] for e in later if e["when"] < end)
    tips.discard(ZERO_SHA)  # a deleted branch, or one not yet created, served nothing

    for sha in sorted(tips):
        revision = f"https://raw.githubusercontent.com/{owner}/{repo}/{sha}/{path}"
        try:
            body = http_get(revision, timeout=timeout)
        except requests.RequestException as exc:
            return "unresolved", f"tip {sha[:10]} could not be fetched ({type(exc).__name__})"
        if body.status_code == 404:
            # Either the file did not exist at that tip, and the URL served a 404 then, or the
            # commit itself is gone (a force-pushed-away tip GitHub has since collected). Only
            # the first is evidence, so ask which.
            commit = _api_get(f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}", timeout)
            if commit is not None and commit.status_code == 200:
                continue
            return "unresolved", f"tip {sha[:10]} no longer exists on GitHub, so what it served cannot be rebuilt"
        if body.status_code >= 400:
            return "unresolved", f"tip {sha[:10]} could not be fetched (HTTP {body.status_code})"
        if hashlib.sha256(body.content).hexdigest() == digest:
            dates = ", ".join(str(d) for d in sorted(accessed))
            return "served", f"{branch} was at {sha[:10]} around the access on {dates}, and its {path} hashes to the recorded digest"
    return "never", (
        f"the activity log covers every tip {branch} held around the recorded access "
        f"({len(tips)} of them), and none of their copies of {path} hashes to it"
    )


def access_dates(sources: list[Source]) -> dict[tuple[str, str], set[date]]:
    """(digest, url) -> every date a record claims that URL served that digest.

    All of them, and the verdict is `served` if ANY of them rebuilds to the digest. That errs
    toward drift, which is the side a fabrication claim has to err on.
    """
    out: dict[tuple[str, str], set[date]] = defaultdict(set)
    for source in sources:
        when = parse_date(source.accessed)
        if when is not None:
            out[(source.digest, source.url)].add(when)
    return dict(out)


def resolve_duplicates(
    groups: list[tuple[str, list[str]]],
    timeout: float,
    accessed: dict[tuple[str, str], set[date]] | None = None,
    history=served_on_access_verdict,
) -> tuple[list[str], list[str]]:
    """(failures, benign) — decided by fetching and by revision history, not by guessing.

    TWO HEURISTICS HAVE BEEN WRONG HERE, and each failed a run.

    The first read: a digest against two URLs is fabrication, because "two distinct pages
    with byte-identical bodies is possible but rare." It failed `main` on 2026-08-13, false
    in two ways:

    - **Canonical texts.** Five repos — NeMo RL, peft, FastChat, ms-swift, vllm — recorded one
      digest for their LICENSE. Fetching all five live reproduced it exactly over an identical
      11,357-byte body: the unmodified Apache-2.0 text. A standard license IS the same bytes
      everywhere; that is what "standard" means, and a repo that changed it would no longer be
      under that license. Byte-identical is the expected result, not a rare coincidence.
    - **Host aliases.** `docs.developer.apple.com/…/coreml.md` 301s to
      `developer.apple.com/…/coreml.md`. Two URLs, one document. Nothing was pasted; the
      fetcher followed a redirect, which is what it is supposed to do.

    The second read: fetch the group, and if the live bodies differ, "at least one digest
    could not have come from its URL." It failed the weekly run on 2026-09-24. The Apache-2.0
    digest `c71d239df917…` is recorded on 52 LICENSE URLs; 51 still reproduce it, and
    treeverse/lakeFS returned a different body because lakeFS relicensed to BSL-1.1 on
    2026-09-22, five weeks after its source was read on 2026-08-18. The inference compared
    two bodies fetched TODAY and drew a conclusion about what one URL served back THEN.

    Neither dates nor revision walks settle it. A first fix compared the file's last commit date
    with the recorded access, and a merge commit breaks that: a PR commit dated before the
    access and merged after it reports a pre-access date for a change the reader never saw. A
    second walked the file's revision history, and that breaks too: a match on a side branch
    shows the bytes existed in the repo, not that the branch URL served them, and a miss after
    a force push is a hole in the history, not proof. What settles it is the tips the branch
    actually held on the access date, which `history` rebuilds from GitHub's activity log:

    - a tip around the access hashes to the digest: the URL served it, and the change is drift;
    - the log covers the whole window and no tip does: FABRICATION, whether or not another
      member reproduces the digest, because this URL could not have served it then;
    - anything short of that (not GitHub, a tag or ambiguous ref, a failed lookup, a window
      the log cannot reach): UNRESOLVED, reported and never a failure.

    Only members that changed are walked, so a group that still reproduces costs nothing.
    """
    failures, benign = [], []
    for digest, urls in groups:
        live_by_url: dict[str, str] = {}
        unreachable = []
        walled: list[tuple[str, str, str]] = []
        for url in urls:
            try:
                # Through `canonical`, exactly as build/fetch_source does. A GitHub blob URL
                # rewrites to its raw form, and comparing a rendered HTML page against the
                # plain file it points at is comparing two different documents. The first
                # draft of this resolver skipped that and reported `maple-ai` as fabrication:
                # its recorded digests were right all along, and the resolver was reading the
                # blob page. fetch_source's own docstring warns about precisely this —
                # "a digest taken with curl and re-checked with requests differs for reasons
                # that have nothing to do with whether anybody read the page."
                response = http_get(url, timeout=timeout)
            except requests.RequestException:
                unreachable.append(url)
                continue
            if response.status_code >= 400:
                unreachable.append(url)
                continue
            live = hashlib.sha256(response.content).hexdigest()
            marker = bot_wall(response)
            if marker:
                # If the wall's digest is the RECORDED one, that is positive evidence the
                # original fetch was walled too: the recorded bytes are a challenge page, so
                # nothing behind this source was ever read.
                walled.append((url, live, marker))
                continue
            live_by_url[url] = live

        listed = ", ".join(urls)
        walls_matching = [w for w in walled if w[1] == digest]
        reproducing = [u for u, live in live_by_url.items() if live == digest]
        changed = [u for u, live in live_by_url.items() if live != digest]

        if walls_matching:
            wall_urls = ", ".join(u for u, _, _ in walls_matching)
            failures.append(
                f"digest {digest[:12]}… IS a bot-challenge page, not a document: re-fetching "
                f"{wall_urls} returns that same digest over a body matching "
                f"{walls_matching[0][2]!r}. So all {len(urls)} sources recorded against it "
                f"({listed}) were digested behind the wall and never read. Re-verify them "
                f"against a source the host will serve."
            )
        else:
            if reproducing and not changed:
                benign.append(
                    f"digest {digest[:12]}… is shared by {len(urls)} URLs ({listed}), and "
                    f"re-fetching confirms their bodies really are identical."
                )
            for url in changed:
                live = live_by_url[url]
                verdict, detail = history(url, digest, (accessed or {}).get((digest, url), set()))
                head = (
                    f"digest {digest[:12]}…: {url} now serves {live[:12]}…, and "
                    f"{len(reproducing)} of {len(urls)} URLs sharing the digest still "
                    f"reproduce it."
                )
                if verdict == "never":
                    failures.append(
                        f"{head} FABRICATION: {detail}, so the recorded digest could not have "
                        f"come from this URL."
                    )
                elif verdict == "served":
                    benign.append(f"{head} Drift, not fabrication: {detail}. Re-check that source.")
                else:
                    benign.append(f"{head} Unresolved: {detail}. Neither cleared nor failed.")
        if walled and not walls_matching:
            benign.append(
                f"digest {digest[:12]}…: {', '.join(u for u, _, _ in walled)} answered with a "
                f"bot wall this run, so the group is unresolved rather than cleared."
            )
        if unreachable:
            benign.append(
                f"digest {digest[:12]}…: could not re-fetch {', '.join(unreachable)} this "
                f"run, so the group is unresolved rather than cleared."
            )
    return failures, benign


def refetch(source: Source, timeout: float, sleep=time.sleep) -> tuple[str, str]:
    """(outcome, detail). Outcome is one of confirmed / drifted / gone / unreachable.

    `sleep` is threaded through to `http_get`'s retry backoff; tests that mock the request
    itself pass a no-op so a simulated transient status does not also cost the real backoff
    delay.
    """
    try:
        response = http_get(source.url, timeout=timeout, sleep=sleep)
    except requests.RequestException as exc:
        return "unreachable", f"{type(exc).__name__}: {exc}"

    # 429 and 5xx are the host saying "not now", not "not here". Calling those dead would
    # make the gate fail on GitHub's rate limiter, which is how a gate earns a reputation
    # for lying. The first run of this module reported a live Mastra LICENSE as dead for
    # exactly that reason.
    #
    # 403 is deliberately NOT in this branch even though `http_get` retries it, and
    # `tests/test_check_refetch.py::test_client_errors_are_dead` pins that. A source that
    # answers 403 to six attempts is one nobody can re-read, which is precisely what a
    # re-read pass needs surfaced loudly rather than filed under "retry later".
    if response.status_code == 429 or response.status_code >= 500:
        return "unreachable", f"HTTP {response.status_code} (transient; retry)"
    if response.status_code >= 400:
        return "gone", f"recorded {source.status}, now HTTP {response.status_code}"

    live = hashlib.sha256(response.content).hexdigest()

    # A wall is "not now" wearing a 200, so it belongs with 429 rather than with drift. Two
    # readings would both be wrong: DRIFTED implies the document changed, and CONFIRMED on a
    # matching digest would be worse still — it would certify a source whose recorded bytes
    # are a challenge page, turning the gate's one piece of positive evidence into a lie.
    marker = bot_wall(response)
    if marker:
        if live == source.digest:
            return "gone", (
                f"the recorded digest reproduces, but over a bot-challenge page "
                f"({marker!r}), so this source was digested behind the wall and never read"
            )
        return "unreachable", f"bot wall ({marker!r}); the host declined to serve the document"

    if live == source.digest:
        return "confirmed", ""
    return "drifted", f"body changed since {source.accessed}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=int, default=25, help="how many to re-fetch")
    parser.add_argument("--seed", type=int, default=0, help="sample seed; same seed, same set")
    parser.add_argument("--all", action="store_true", help="re-fetch every source with a digest")
    parser.add_argument("--product", help="restrict to one product slug")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail on dead and unreachable sources, not just on fabrication",
    )
    args = parser.parse_args()

    sources = load_sources(args.product)
    if not sources:
        print("0 sources record a digest yet — nothing to re-fetch.")
        print("This is expected until the re-read pass populates content_sha256.")
        return 0

    failures = offline_failures(sources)

    # Duplicate digests are resolved by fetching and by revision history rather than assumed
    # to be fabrication. See resolve_duplicates: earlier heuristics failed on canonical LICENSE
    # texts, a host alias and a relicensed repo, none of which is anybody pasting anything.
    dup_failures, dup_benign = resolve_duplicates(
        duplicate_digest_groups(sources), args.timeout, accessed=access_dates(sources)
    )
    failures.extend(dup_failures)

    chosen = sources
    if not args.all and len(sources) > args.sample:
        chosen = random.Random(args.seed).sample(sources, args.sample)

    buckets: dict[str, list[tuple[Source, str]]] = defaultdict(list)
    for source in sorted(chosen, key=lambda s: (s.product, s.axis, s.url)):
        outcome, detail = refetch(source, args.timeout)
        buckets[outcome].append((source, detail))

    if dup_benign:
        print("\nSHARED DIGESTS — resolved by fetching, not a failure")
        for line in dup_benign:
            print(f"  {line}")

    for outcome, label in (
        ("gone", "DEAD — recorded as reachable, now an error"),
        ("unreachable", "UNREACHABLE — could not be checked this run"),
        ("drifted", "DRIFTED — body changed; re-check queue, not a failure"),
    ):
        if buckets[outcome]:
            print(f"\n{label}")
            for source, detail in buckets[outcome]:
                print(f"  {source.key:38s} {source.url}")
                if detail:
                    print(f"  {'':38s}   {detail}")

    if failures:
        print("\nFABRICATION — no innocent reading")
        for problem in failures:
            print(f"  {problem}")

    confirmed = len(buckets["confirmed"])
    print(
        f"\n{len(sources)} sources carry a digest, {len(chosen)} re-fetched: "
        f"{confirmed} confirmed, {len(buckets['drifted'])} drifted, "
        f"{len(buckets['gone'])} dead, {len(buckets['unreachable'])} unreachable."
    )
    if confirmed:
        print(
            f"{confirmed} digest(s) reproduced exactly, which only an actual fetch could "
            f"have produced. That is the positive evidence this gate exists for."
        )

    if failures:
        print(f"\n[FAIL] {len(failures)} source(s) could not have been fetched as recorded")
        return 1
    findings = len(buckets["gone"]) + len(buckets["unreachable"])
    if args.strict and findings:
        print(f"\n[FAIL] --strict: {findings} source(s) dead or unreachable")
        return 1
    print("\n[OK] no fabricated digests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
