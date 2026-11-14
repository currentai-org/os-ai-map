"""Measure how much of a URL-only image corpus can still be fetched, on a small seeded sample.

Why this exists. Under R-2026-11-13-d a release that publishes URLs rather than content counts as
a released corpus only when reconstruction is materially possible, and how much of the governing
corpus can still be recovered has to be shown rather than assumed. `openclip` is held on that
point in `sources/verification_queue.yaml`. This module is the pilot measurement the maintainer
authorized: it draws a reproducible random sample from the published DataComp-1B metadata on
Hugging Face, fetches each sampled image once under polite, access-respecting limits, hashes the
bytes in memory and compares them with the sha256 the metadata publishes. It writes nothing under
`sources/`, keeps no image, moves no score and gates nothing; it is a survey, like
`build.closed_inclusion`, and is never wired into preflight or CI.

Run it with `uv run python -m build.recoverability_pilot --out <path.json>`. The defaults are the
parameters the 2026-11-14 pilot ran with. `--select-only` draws the sample and prints its manifest
without fetching any image, so anyone can check that the seed reproduces the same rows.

Selection. The parquet files at the pinned revision are sorted by name; a `random.Random(seed)`
draws `--shards` of them without replacement, then, for each drawn file in draw order, reads its
row count from the parquet footer and draws `sample_size / shards` row indices without
replacement from the same generator. The fetch order is shuffled by a second generator seeded
from the same seed, which changes timing and nothing else.

Fetch rules. At most `--concurrency` requests in flight, at most one per host, and at least
`--per-host-delay` seconds between the end of one request to a host and the start of the next.
A plain User-Agent naming the check; no cookies, credentials, referer or proxy rotation. Each
origin's robots.txt is fetched once and read per RFC 9309 (longest match, allow wins ties; a 5xx
or 429 answer means full disallow, any other 4xx means no rules), and a URL disallowed for this
User-Agent or for `*` is skipped. `X-Robots-Tag` directives are honored
the way img2dataset's default does (`noai`, `noimageai`, `noindex`, `noimageindex`), on every
response in a redirect chain, and the body of an opted-out response is not read. Redirects are
followed up to ten hops, as `urllib` (img2dataset's fetcher) does, with robots.txt and the
per-host limits applied to each hop. One retry, only after a connection error or timeout.

The rule this measures is in `docs/reference/openness.md`, "A web-crawl corpus is open when its
release documents a basis for reuse"; the method and the results are in
`docs/briefs/2026-11-14-openclip-recoverability-pilot.md`.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import http.cookiejar
import ipaddress
import json
import math
import os
import platform
import random
import re
import socket
import struct
import sys
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

DEFAULT_REPO = "mlfoundations/datacomp_1b"
DEFAULT_REVISION = "086ebeee20d4cc3b3e7c05ae703fcf278ae3a759"
DEFAULT_SEED = 20261114
DEFAULT_SAMPLE_SIZE = 1000
DEFAULT_SHARDS = 50
DEFAULT_CONCURRENCY = 8
DEFAULT_PER_HOST_DELAY = 1.0
DEFAULT_TIMEOUT = 20.0
MAX_RETRIES = 1
MAX_REDIRECTS = 10          # urllib.request.HTTPRedirectHandler.max_redirections
ROBOTS_MAX_REDIRECTS = 5    # RFC 9309 section 2.3.1.2
ROBOTS_MAX_BYTES = 500 * 1024
MAX_IMAGE_BYTES = 64 * 1024 * 1024

UA_TOKEN = "datacomp-recoverability-check"
USER_AGENT = f"{UA_TOKEN}/0.1 (dataset recoverability check; samples a published image-URL index)"
# img2dataset main.py: `disallowed_header_directives = ["noai", "noimageai", "noindex",
# "noimageindex"]` when the caller passes none.
X_ROBOTS_DIRECTIVES = frozenset({"noai", "noimageai", "noindex", "noimageindex"})
# img2dataset honors a directive with no token or with its configured token (none by default).
# This check also honors one addressed to img2dataset, the tool the corpus was collected with.
X_ROBOTS_TOKENS = frozenset({UA_TOKEN, "img2dataset"})

COLUMNS = ["uid", "url", "sha256", "original_width", "original_height"]

SUCCESS, CHANGED, FAILURE, EXCLUDED = "success", "changed_content", "failure", "excluded"
CATEGORIES = (SUCCESS, CHANGED, FAILURE, EXCLUDED)

# The reporting classes the maintainer asked for, finer than the four categories above and never
# summed into one "unavailable" figure. Each outcome code lands in exactly one class; a code no
# rule names falls to `other_http_4xx` if it is a 4xx and to `transient_or_environment` otherwise,
# so nothing is silently dropped. The brief says which classes an estimate can defend.
REPORT_CLASSES = (
    "hash_match",                # success: the bytes are the bytes the metadata hashed
    "image_hash_differs",        # an image was served; re-encoded, resized or replaced
    "definitive_gone",           # 404, 410, host name does not resolve
    "transient_or_environment",  # timeouts, 5xx, 429, resets, TLS errors, proxy refusals
    "access_controlled",         # 401, 403
    "non_image",                 # 2xx with HTML or another non-image body, empty bodies
    "other_http_4xx",            # 400 and the remaining client errors: neither gone nor blocked
    "opt_out",                   # robots.txt disallow, X-Robots-Tag opt-out
    "robots_unreachable",        # robots.txt answered 5xx or 429; RFC 9309 says do not fetch
)
_CLASS_OF = {
    "hash_match": "hash_match",
    "same_dims": "image_hash_differs", "different_dims": "image_hash_differs",
    "dims_unknown": "image_hash_differs",
    "http_404": "definitive_gone", "http_410": "definitive_gone", "dns_error": "definitive_gone",
    "http_401": "access_controlled", "http_403": "access_controlled",
    "non_image": "non_image", "empty_body": "non_image",
    "robots_disallow": "opt_out", "x_robots_tag": "opt_out",
    "robots_unavailable": "robots_unreachable",
    "http_429": "transient_or_environment",
}


def report_class(code: str) -> str:
    if code in _CLASS_OF:
        return _CLASS_OF[code]
    m = re.fullmatch(r"http_(\d{3})", code)
    if m and 400 <= int(m.group(1)) < 500:
        return "other_http_4xx"
    if code in ("bad_url", "bad_redirect", "too_many_redirects"):
        return "other_http_4xx"
    return "transient_or_environment"

# Ordered (suffix-or-marker, type). A heuristic for the per-type table only; "other" is the rest.
HOST_TYPES: tuple[tuple[str, str], ...] = (
    ("pinimg.com", "pinterest"),
    ("ebayimg.com", "ecommerce"), ("media-amazon.com", "ecommerce"),
    ("ssl-images-amazon.com", "ecommerce"), ("images-amazon.com", "ecommerce"),
    ("alicdn.com", "ecommerce"), ("etsystatic.com", "ecommerce"), ("walmartimages.com", "ecommerce"),
    ("cdn.shopify.com", "ecommerce"), ("bigcommerce.com", "ecommerce"),
    ("specsserver.com", "ecommerce"), ("fineartamerica.com", "ecommerce"),
    ("dreamstime.com", "stock_photo"), ("123rf.com", "stock_photo"),
    ("shutterstock.com", "stock_photo"), ("alamy.com", "stock_photo"),
    ("istockphoto.com", "stock_photo"), ("gettyimages.com", "stock_photo"),
    ("depositphotos.com", "stock_photo"), ("canstockphoto.com", "stock_photo"),
    ("wixstatic.com", "site_builder_or_blog"), ("wp.com", "site_builder_or_blog"),
    ("wordpress.com", "site_builder_or_blog"), ("squarespace-cdn.com", "site_builder_or_blog"),
    ("squarespace.com", "site_builder_or_blog"), ("blogspot.com", "site_builder_or_blog"),
    ("blogger.com", "site_builder_or_blog"), ("tumblr.com", "site_builder_or_blog"),
    ("weebly.com", "site_builder_or_blog"), ("googleusercontent.com", "site_builder_or_blog"),
    ("amazonaws.com", "cloud_storage_or_cdn"), ("blob.core.windows.net", "cloud_storage_or_cdn"),
    ("googleapis.com", "cloud_storage_or_cdn"), ("cloudfront.net", "cloud_storage_or_cdn"),
    ("akamaized.net", "cloud_storage_or_cdn"), ("digitaloceanspaces.com", "cloud_storage_or_cdn"),
    ("cloudinary.com", "cloud_storage_or_cdn"), ("imgix.net", "cloud_storage_or_cdn"),
    ("ytimg.com", "cloud_storage_or_cdn"), ("gstatic.com", "cloud_storage_or_cdn"),
    ("staticflickr.com", "cloud_storage_or_cdn"), ("imgur.com", "cloud_storage_or_cdn"),
)


def host_type(host: str, path: str) -> str:
    host = host.lower()
    for suffix, kind in HOST_TYPES:
        if host == suffix or host.endswith("." + suffix):
            return kind
    if "/wp-content/" in path:
        return "self_hosted_wordpress"
    return "other"


# ── statistics ─────────────────────────────────────────────────────────────────────────────


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """95% Wilson score interval for k successes in n trials. (0, 0) when n is 0."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def share(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"count": k, "n": n, "share": round(k / n, 4) if n else None,
            "ci95": [round(lo, 4), round(hi, 4)]}


# ── selection ──────────────────────────────────────────────────────────────────────────────


def rows_per_shard(sample_size: int, shards: int) -> list[int]:
    base, extra = divmod(sample_size, shards)
    return [base + (1 if i < extra else 0) for i in range(shards)]


def select_sample(repo: str, revision: str, seed: int, sample_size: int, shards: int) -> dict:
    """Draw the sample and read the sampled rows. Returns source facts and the sample list."""
    from huggingface_hub import HfApi, HfFileSystem
    import pyarrow.parquet as pq

    files = sorted(f for f in HfApi().list_repo_files(repo, repo_type="dataset", revision=revision,
                                                       token=False) if f.endswith(".parquet"))
    rng = random.Random(seed)
    drawn = rng.sample(files, shards)
    fs = HfFileSystem(token=False)
    shard_facts, samples = [], []
    for name, k in zip(drawn, rows_per_shard(sample_size, shards)):
        path = f"datasets/{repo}@{revision}/{name}"
        with fs.open(path, "rb", block_size=8 << 20) as handle:
            pf = pq.ParquetFile(handle)
            num_rows = pf.metadata.num_rows
            rows = sorted(rng.sample(range(num_rows), k))
            table = pf.read(columns=COLUMNS).take(rows).to_pylist()
        shard_facts.append({"file": name, "num_rows": num_rows, "rows": rows})
        for row, rec in zip(rows, table):
            samples.append({"shard": name, "row": row, **rec})
    return {"parquet_files_at_revision": len(files), "shards": shard_facts, "samples": samples}


def count_frame(repo: str, revision: str, workers: int = 8) -> dict:
    """Sum the row counts in every parquet footer at the revision: the size of the frame."""
    from huggingface_hub import HfApi, HfFileSystem
    import pyarrow.parquet as pq

    files = sorted(f for f in HfApi().list_repo_files(repo, repo_type="dataset", revision=revision,
                                                       token=False) if f.endswith(".parquet"))
    fs = HfFileSystem(token=False)

    def rows(name):
        with fs.open(f"datasets/{repo}@{revision}/{name}", "rb", block_size=1 << 20) as handle:
            return pq.ParquetFile(handle).metadata.num_rows

    with ThreadPoolExecutor(max_workers=workers) as pool:
        counts = list(pool.map(rows, files))
    return {"parquet_files": len(files), "rows": sum(counts),
            "rows_per_file_min": min(counts), "rows_per_file_max": max(counts)}


# ── robots.txt (RFC 9309) ──────────────────────────────────────────────────────────────────


def parse_robots(text: str) -> dict[str, list[tuple[bool, str]]]:
    """Group rules by lower-cased user-agent token: {agent: [(allow, pattern), ...]}."""
    groups: dict[str, list[tuple[bool, str]]] = collections.defaultdict(list)
    agents: list[str] = []
    in_rules = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(value.lower())
            groups.setdefault(value.lower(), [])
        elif key in ("allow", "disallow"):
            in_rules = True
            if key == "disallow" and not value:
                continue
            for agent in agents:
                groups[agent].append((key == "allow", value))
    return dict(groups)


def _pattern_matches(pattern: str, path: str) -> bool:
    regex = "".join(".*" if ch == "*" else re.escape(ch) for ch in pattern.rstrip("$"))
    if pattern.endswith("$"):
        return re.fullmatch(regex, path) is not None
    return re.match(regex, path) is not None


def robots_allows(rules: list[tuple[bool, str]], path: str) -> bool:
    best: tuple[int, bool] | None = None
    for allow, pattern in rules:
        if _pattern_matches(pattern, path):
            cand = (len(pattern), allow)
            if best is None or cand[0] > best[0] or (cand[0] == best[0] and allow):
                best = cand
    return True if best is None else best[1]


def robots_verdict(groups: dict[str, list[tuple[bool, str]]], path: str) -> bool:
    """True when the path is allowed both for this User-Agent's group and for `*`."""
    star = groups.get("*", [])
    own = groups.get(UA_TOKEN.lower())
    if own is None:
        own = star
    return robots_allows(own, path) and robots_allows(star, path)


# ── image sniffing ─────────────────────────────────────────────────────────────────────────


def sniff_image(body: bytes) -> str | None:
    if body.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if body[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return "webp"
    if body[:2] == b"BM":
        return "bmp"
    if body[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if body[:4] == b"\x00\x00\x01\x00":
        return "ico"
    if body[4:8] == b"ftyp" and body[8:12] in (b"avif", b"avis", b"heic", b"heix", b"mif1", b"msf1"):
        return "heif"
    return None


def image_dims(body: bytes, kind: str | None) -> tuple[int, int] | None:
    try:
        if kind == "png" and len(body) >= 24:
            return struct.unpack(">II", body[16:24])
        if kind == "gif" and len(body) >= 10:
            return struct.unpack("<HH", body[6:10])
        if kind == "webp" and len(body) >= 30:
            chunk = body[12:16]
            if chunk == b"VP8 ":
                w, h = struct.unpack("<HH", body[26:30])
                return (w & 0x3FFF, h & 0x3FFF)
            if chunk == b"VP8L":
                b = body[21:25]
                w = 1 + (((b[1] & 0x3F) << 8) | b[0])
                h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
                return (w, h)
            if chunk == b"VP8X":
                w = 1 + int.from_bytes(body[24:27], "little")
                h = 1 + int.from_bytes(body[27:30], "little")
                return (w, h)
        if kind == "jpeg":
            i = 2
            while i + 9 < len(body):
                if body[i] != 0xFF:
                    i += 1
                    continue
                marker = body[i + 1]
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7 or marker == 0xFF:
                    i += 1 if marker == 0xFF else 2
                    continue
                seg = struct.unpack(">H", body[i + 2:i + 4])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB,
                              0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", body[i + 5:i + 9])
                    return (w, h)
                i += 2 + seg
    except (struct.error, IndexError):
        return None
    return None


# ── fetching ───────────────────────────────────────────────────────────────────────────────


class HostGate:
    """One request at a time per host, and a minimum gap after each request ends."""

    def __init__(self, delay: float):
        self.delay = delay
        self.cond = threading.Condition()
        self.busy: set[str] = set()
        self.next_ok: dict[str, float] = {}
        self.last_end: dict[str, float] = {}
        # Observed, so the run record shows the limits held rather than asserting it.
        self.max_in_flight = 0
        self.min_same_host_gap: float | None = None

    def acquire(self, host: str) -> None:
        with self.cond:
            while True:
                now = time.monotonic()
                wait = self.next_ok.get(host, 0.0) - now
                if host not in self.busy and wait <= 0:
                    self.busy.add(host)
                    self.max_in_flight = max(self.max_in_flight, len(self.busy))
                    if host in self.last_end:
                        gap = now - self.last_end[host]
                        if self.min_same_host_gap is None or gap < self.min_same_host_gap:
                            self.min_same_host_gap = gap
                    return
                self.cond.wait(timeout=max(wait, 0.05) if host not in self.busy else None)

    def release(self, host: str) -> None:
        with self.cond:
            self.busy.discard(host)
            self.last_end[host] = time.monotonic()
            self.next_ok[host] = self.last_end[host] + self.delay
            self.cond.notify_all()


class Outcome(Exception):
    """A terminal classification reached before an image body was hashed."""

    def __init__(self, category: str, code: str, **detail):
        super().__init__(code)
        self.category, self.code, self.detail = category, code, detail


_TUNNEL = re.compile(r"Tunnel connection failed: (\d{3})")


def _is_public(host: str) -> bool:
    infos = socket.getaddrinfo(host, None)
    return all(ipaddress.ip_address(info[4][0].split("%")[0]).is_global for info in infos)


class Fetcher:
    def __init__(self, delay: float, timeout: float):
        self.gate = HostGate(delay)
        self.timeout = timeout
        self.local = threading.local()
        self.proxies = {k: v for k, v in (("https", os.environ.get("HTTPS_PROXY")
                                           or os.environ.get("https_proxy")),
                                          ("http", os.environ.get("HTTP_PROXY")
                                           or os.environ.get("http_proxy"))) if v}
        self.verify: str | bool = (os.environ.get("REQUESTS_CA_BUNDLE")
                                   or os.environ.get("SSL_CERT_FILE") or True)
        self.robots: dict[str, object] = {}
        self.robots_lock = threading.Lock()
        self.robots_events: dict[str, threading.Event] = {}
        self.request_count = 0
        self.count_lock = threading.Lock()

    def session(self):
        import requests

        s = getattr(self.local, "session", None)
        if s is None:
            s = requests.Session()
            s.trust_env = False  # no .netrc credentials, no env-derived auth
            s.cookies.set_policy(http.cookiejar.DefaultCookiePolicy(allowed_domains=[]))
            s.headers.clear()
            s.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*",
                              "Accept-Encoding": "identity"})
            self.local.session = s
        return s

    # One HTTP request, gated, with at most one retry for connection errors and timeouts.
    def request(self, url: str, max_bytes: int, read_body) -> tuple[int, dict, bytes | None, int]:
        parts = urllib.parse.urlsplit(url)
        host = (parts.hostname or "").lower()
        if parts.scheme not in ("http", "https") or not host:
            raise Outcome(FAILURE, "bad_url")
        if parts.scheme == "https" and (parts.port or 443) != 443:
            # The session's egress proxy carries HTTPS on port 443 only (/root/.ccr/README.md).
            raise Outcome(EXCLUDED, "proxy_unsupported_port", host=host)
        attempts = 0
        while True:
            attempts += 1
            self.gate.acquire(host)
            try:
                with self.count_lock:
                    self.request_count += 1
                return (*self._one(url, parts, host, max_bytes, read_body), attempts)
            except Outcome as out:
                retryable = out.detail.pop("_retryable", False)
                if retryable and attempts <= MAX_RETRIES:
                    continue
                out.detail["attempts"] = attempts
                raise
            finally:
                self.gate.release(host)

    def _one(self, url, parts, host, max_bytes, read_body):
        import requests

        if parts.scheme == "http" and not self.proxies.get("http"):
            # Plain HTTP leaves the container directly; refuse non-public destinations.
            try:
                if not _is_public(host):
                    raise Outcome(EXCLUDED, "non_public_address", host=host)
            except socket.gaierror as err:
                transient = err.errno == socket.EAI_AGAIN
                raise Outcome(FAILURE, "dns_error", _retryable=transient)
        start = time.monotonic()
        try:
            resp = self.session().get(url, allow_redirects=False, stream=True,
                                      timeout=(self.timeout, self.timeout),
                                      proxies=self.proxies, verify=self.verify)
        except requests.exceptions.ProxyError as err:
            m = _TUNNEL.search(str(err))
            status = int(m.group(1)) if m else None
            if status in (403, 407):
                raise Outcome(EXCLUDED, "proxy_refused", host=host, proxy_status=status)
            if status in (429, 503):
                raise Outcome(EXCLUDED, "proxy_busy", host=host, proxy_status=status)
            if status == 504:
                raise Outcome(FAILURE, "timeout", via="gateway", _retryable=True)
            if status == 502:
                # The gateway could not reach the host. Separate DNS from connect locally.
                try:
                    socket.getaddrinfo(host, None)
                    code = "connect_error"
                except socket.gaierror:
                    code = "dns_error"
                raise Outcome(FAILURE, code, via="gateway", _retryable=True)
            raise Outcome(EXCLUDED, "proxy_error", host=host, proxy_status=status)
        except requests.exceptions.SSLError:
            raise Outcome(FAILURE, "tls_error")
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            raise Outcome(FAILURE, "timeout", _retryable=True)
        except requests.exceptions.ConnectionError as err:
            text = str(err)
            if "NameResolutionError" in text or "Name or service not known" in text \
                    or "getaddrinfo failed" in text or "nodename nor servname" in text:
                raise Outcome(FAILURE, "dns_error")
            if "Connection refused" in text:
                raise Outcome(FAILURE, "connect_error", _retryable=True)
            if "reset" in text.lower() or "RemoteDisconnected" in text or "aborted" in text:
                raise Outcome(FAILURE, "connection_reset", _retryable=True)
            raise Outcome(FAILURE, "connect_error", _retryable=True)
        except requests.exceptions.InvalidURL:
            raise Outcome(FAILURE, "bad_url")
        except requests.exceptions.RequestException as err:
            raise Outcome(FAILURE, "protocol_error", error=type(err).__name__)
        with resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            headers["_x_robots"] = resp.raw.headers.getlist("X-Robots-Tag") \
                if hasattr(resp.raw.headers, "getlist") else (
                    [resp.headers["X-Robots-Tag"]] if "X-Robots-Tag" in resp.headers else [])
            if not read_body(resp.status_code, headers):
                return resp.status_code, headers, None
            chunks, size = [], 0
            try:
                for chunk in resp.raw.stream(65536, decode_content=False):
                    size += len(chunk)
                    if size > max_bytes:
                        raise Outcome(FAILURE, "too_large")
                    if time.monotonic() - start > self.timeout:
                        raise Outcome(FAILURE, "timeout", _retryable=True)
                    chunks.append(chunk)
            except Outcome:
                raise
            except Exception as err:  # urllib3 read errors mid-body
                if "timed out" in str(err).lower():
                    raise Outcome(FAILURE, "timeout", _retryable=True)
                raise Outcome(FAILURE, "connection_reset", _retryable=True)
            return resp.status_code, headers, b"".join(chunks)

    # robots.txt, fetched once per origin.
    def robots_for(self, scheme: str, netloc: str):
        origin = f"{scheme}://{netloc.lower()}"
        with self.robots_lock:
            if origin in self.robots:
                return self.robots[origin]
            event = self.robots_events.get(origin)
            owner = event is None
            if owner:
                event = self.robots_events[origin] = threading.Event()
        if not owner:
            event.wait()
            return self.robots[origin]
        try:
            verdict = self._fetch_robots(origin)
        except Outcome as out:
            verdict = out
        with self.robots_lock:
            self.robots[origin] = verdict
        event.set()
        return verdict

    def _fetch_robots(self, origin: str) -> dict:
        """{"status": final HTTP status, "groups": parsed rules, "disallow_all": bool}."""
        url = origin + "/robots.txt"
        for _ in range(ROBOTS_MAX_REDIRECTS + 1):
            status, headers, body, _ = self.request(url, ROBOTS_MAX_BYTES,
                                                    lambda s, h: 200 <= s < 300)
            if status in (301, 302, 303, 307, 308) and headers.get("location"):
                url = urllib.parse.urljoin(url, headers["location"])
                continue
            if 200 <= status < 300:
                text = (body or b"")[:ROBOTS_MAX_BYTES].decode("utf-8", "replace")
                return {"status": status, "groups": parse_robots(text), "disallow_all": False}
            # RFC 9309 section 2.3.1: 5xx means "unreachable", so full disallow; 4xx means
            # "unavailable", so no rules. 429 is read as overload rather than absence and kept
            # with the 5xx. 401 and 403 follow the RFC and impose no rules; the per-sample
            # `robots_status` lets the summary re-tabulate them under urllib.robotparser's
            # stricter convention, which reads them as full disallow.
            disallow = status == 429 or status >= 500
            return {"status": status, "groups": {}, "disallow_all": disallow}
        # RFC 9309 section 2.3.1.2: past five redirects, treat as unavailable.
        return {"status": "too_many_redirects", "groups": {}, "disallow_all": False}


def x_robots_opt_out(values: list[str]) -> str | None:
    """img2dataset's `is_disallowed`, with the token set widened as X_ROBOTS_TOKENS says."""
    for value in values:
        parts = value.split(":", 1)
        token = parts[0].strip().lower() if len(parts) == 2 else None
        directives = [d.strip().lower() for d in parts[-1].split(",")]
        if token is None or token in X_ROBOTS_TOKENS:
            hit = [d for d in directives if d in X_ROBOTS_DIRECTIVES]
            if hit:
                return hit[0]
    return None


def fetch_sample(fetcher: Fetcher, sample: dict) -> dict:
    url = sample["url"]
    expected = (sample.get("sha256") or "").lower()
    rec = {"redirects": 0, "cross_host_redirects": 0}
    first_host = (urllib.parse.urlsplit(url).hostname or "").lower()
    try:
        for hop in range(MAX_REDIRECTS + 1):
            parts = urllib.parse.urlsplit(url)
            if parts.scheme not in ("http", "https") or not parts.hostname:
                raise Outcome(FAILURE, "bad_redirect" if hop else "bad_url")
            if not (parts.scheme == "https" and (parts.port or 443) != 443):
                robots = fetcher.robots_for(parts.scheme, parts.netloc)
                if isinstance(robots, Outcome):
                    if robots.category == EXCLUDED:
                        raise Outcome(EXCLUDED, robots.code, host=parts.hostname, stage="robots")
                    raise Outcome(FAILURE, robots.code, stage="robots")
                if robots["status"] != 200:
                    rec.setdefault("robots_status", robots["status"])
                if robots["disallow_all"]:
                    raise Outcome(EXCLUDED, "robots_unavailable", robots_status=robots["status"],
                                  after_redirect=hop > 0)
                path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
                if not robots_verdict(robots["groups"], path):
                    raise Outcome(EXCLUDED, "robots_disallow", after_redirect=hop > 0)

            def wants_body(status, headers):
                if x_robots_opt_out(headers.get("_x_robots", [])):
                    return False
                return 200 <= status < 300

            status, headers, body, attempts = fetcher.request(url, MAX_IMAGE_BYTES, wants_body)
            rec["attempts"] = attempts
            directive = x_robots_opt_out(headers.get("_x_robots", []))
            if directive:
                raise Outcome(EXCLUDED, "x_robots_tag", directive=directive, http_status=status)
            if status in (301, 302, 303, 307, 308):
                loc = headers.get("location")
                if not loc:
                    raise Outcome(FAILURE, "bad_redirect", http_status=status)
                nxt = urllib.parse.urljoin(url, loc)
                rec["redirects"] += 1
                if (urllib.parse.urlsplit(nxt).hostname or "").lower() != \
                        (parts.hostname or "").lower():
                    rec["cross_host_redirects"] += 1
                url = nxt
                continue
            if not 200 <= status < 300:
                raise Outcome(FAILURE, f"http_{status}", http_status=status)
            body = body or b""
            if not body:
                raise Outcome(FAILURE, "empty_body", http_status=status)
            digest = hashlib.sha256(body).hexdigest()
            kind = sniff_image(body)
            ctype = headers.get("content-type", "").split(";")[0].strip().lower()
            rec.update(http_status=status, bytes=len(body), format=kind, fetched_sha256=digest)
            rec["final_host"] = (parts.hostname or "").lower()
            if digest == expected:
                return {**rec, "category": SUCCESS, "code": "hash_match"}
            if kind is None and not (ctype.startswith("image/") and ctype != "image/svg+xml"):
                return {**rec, "category": FAILURE, "code": "non_image",
                        "content_type": ctype or None}
            dims = image_dims(body, kind)
            orig = (sample.get("original_width"), sample.get("original_height"))
            if dims is None:
                sub = "dims_unknown"
            elif tuple(dims) == tuple(orig):
                sub = "same_dims"
            else:
                sub = "different_dims"
            return {**rec, "category": CHANGED, "code": sub}
        raise Outcome(FAILURE, "too_many_redirects")
    except Outcome as out:
        detail = {k: v for k, v in out.detail.items() if not k.startswith("_")}
        if out.category == EXCLUDED and "host" not in detail:
            detail["host"] = first_host
        return {**rec, **detail, "category": out.category, "code": out.code}


# ── report ─────────────────────────────────────────────────────────────────────────────────


def summarize(manifest: list[dict]) -> dict:
    n = len(manifest)
    by_cat = collections.Counter(m["category"] for m in manifest)
    measured = n - by_cat[EXCLUDED]
    codes: dict[str, collections.Counter] = {c: collections.Counter() for c in CATEGORIES}
    for m in manifest:
        codes[m["category"]][m["code"]] += 1

    def table(key):
        groups: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        for m in manifest:
            groups[m[key]][m["category"]] += 1
        out = {}
        for g, c in sorted(groups.items(), key=lambda kv: -sum(kv[1].values())):
            total = sum(c.values())
            meas = total - c[EXCLUDED]
            out[g] = {"samples": total, **{cat: c[cat] for cat in CATEGORIES},
                      "success_share_of_measured": round(c[SUCCESS] / meas, 4) if meas else None}
        return out

    hosts = table("host")
    excluded_hosts = collections.defaultdict(set)
    for m in manifest:
        if m["category"] == EXCLUDED and m["code"] in ("proxy_refused", "proxy_busy",
                                                       "proxy_error", "proxy_unsupported_port",
                                                       "non_public_address"):
            excluded_hosts[m["code"]].add(m.get("excluded_host") or m["host"])
    strict = [m for m in manifest if m.get("robots_status") in (401, 403)
              and m["category"] != EXCLUDED]
    strict_cats = collections.Counter(m["category"] for m in strict)
    strict_by = {c: by_cat[c] - strict_cats[c] for c in CATEGORIES}
    strict_by[EXCLUDED] = by_cat[EXCLUDED] + len(strict)
    fetched = collections.Counter(m.get("fetched_sha256") for m in manifest
                                  if m["category"] == CHANGED)
    classes: dict[str, collections.Counter] = {c: collections.Counter() for c in REPORT_CLASSES}
    for m in manifest:
        classes[report_class(m["code"])][m["code"]] += 1
    return {
        "samples": n,
        "reporting_classes_of_all_samples": {
            c: {**share(sum(classes[c].values()), n), "codes": dict(classes[c].most_common())}
            for c in REPORT_CLASSES},
        "categories_of_all_samples": {c: share(by_cat[c], n) for c in CATEGORIES},
        "categories_of_measured_samples": {c: share(by_cat[c], measured)
                                           for c in (SUCCESS, CHANGED, FAILURE)},
        "measured_samples": measured,
        "image_returned_of_measured": share(by_cat[SUCCESS] + by_cat[CHANGED], measured),
        "breakdown": {c: dict(codes[c].most_common()) for c in CATEGORIES},
        "robots_401_403_not_excluded": {
            "count": len(strict), "categories": dict(strict_cats),
            "categories_of_all_samples_if_excluded": {c: share(strict_by[c], n)
                                                      for c in CATEGORIES},
        },
        "changed_content_repeated_fetched_hash": sum(v for k, v in fetched.items() if v > 1),
        "redirected_samples": sum(1 for m in manifest if m.get("redirects")),
        "cross_host_redirected_samples": sum(1 for m in manifest if m.get("cross_host_redirects")),
        "retried_samples": sum(1 for m in manifest if (m.get("attempts") or 1) > 1),
        "distinct_hosts": len(hosts),
        "environment_excluded_hosts": {k: sorted(v) for k, v in excluded_hosts.items()},
        "top_hosts": dict(list(hosts.items())[:20]),
        "by_host_type": table("host_type"),
        "by_scheme": table("scheme"),
    }


def run(args) -> dict:
    started = dt.datetime.now(dt.timezone.utc)
    t0 = time.monotonic()
    selected = select_sample(args.repo, args.revision, args.seed, args.sample_size, args.shards)
    t_select = time.monotonic() - t0
    samples = selected["samples"]
    for s in samples:
        parts = urllib.parse.urlsplit(s["url"])
        s["host"] = (parts.hostname or "").lower()
        s["scheme"] = parts.scheme
        s["host_type"] = host_type(s["host"], parts.path)
    base = {"source": {"repo": args.repo, "revision": args.revision,
                       "parquet_files_at_revision": selected["parquet_files_at_revision"],
                       "columns_read": COLUMNS,
                       "shards": [{"file": f["file"], "num_rows": f["num_rows"]}
                                  for f in selected["shards"]]}}
    if args.count_frame:
        base["source"]["frame"] = count_frame(args.repo, args.revision)
    keep = ("uid", "shard", "row", "host", "host_type", "scheme")
    if args.select_only:
        return {**base, "manifest": [{k: s[k] for k in keep} for s in samples]}

    order = list(range(len(samples)))
    random.Random(f"{args.seed}:fetch-order").shuffle(order)
    fetcher = Fetcher(args.per_host_delay, args.timeout)
    results: list[dict | None] = [None] * len(samples)
    done = [0]
    lock = threading.Lock()

    def work(i):
        results[i] = fetch_sample(fetcher, samples[i])
        with lock:
            done[0] += 1
            if done[0] % 50 == 0:
                print(f"  {done[0]}/{len(samples)} fetched", file=sys.stderr, flush=True)

    t1 = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(work, order))
    t_fetch = time.monotonic() - t1
    finished = dt.datetime.now(dt.timezone.utc)

    manifest = []
    for s, r in zip(samples, results):
        row = {k: s[k] for k in keep}
        row["outcome"], row["code"] = r["category"], r["code"]
        for k in ("http_status", "attempts", "redirects", "cross_host_redirects", "directive",
                  "robots_status", "after_redirect", "stage", "via", "format", "content_type",
                  "proxy_status"):
            if r.get(k) not in (None, 0, False):
                row[k] = r[k]
        if r["category"] == EXCLUDED and r.get("host") and r["host"] != s["host"]:
            row["excluded_host"] = r["host"]
        if r["category"] == CHANGED:
            row["fetched_sha256"] = r["fetched_sha256"]
        manifest.append(row)
    summary = summarize([{**m, "category": m["outcome"]} for m in manifest])
    for m in manifest:
        m.pop("fetched_sha256", None)
    return {
        "pilot": "DataComp-1B image recoverability (openclip.openness hold)",
        "generated_by": "uv run python -m build.recoverability_pilot",
        "run": {"started_at": started.isoformat(timespec="seconds"),
                "finished_at": finished.isoformat(timespec="seconds"),
                "selection_seconds": round(t_select, 1), "fetch_seconds": round(t_fetch, 1),
                "http_requests_to_image_hosts": fetcher.request_count,
                "robots_origins": len(fetcher.robots),
                "observed_max_in_flight": fetcher.gate.max_in_flight,
                "observed_min_same_host_gap_s": (
                    None if fetcher.gate.min_same_host_gap is None
                    else round(fetcher.gate.min_same_host_gap, 3)),
                "python": platform.python_version()},
        "parameters": {"seed": args.seed, "sample_size": args.sample_size,
                       "shards": args.shards,
                       "rows_per_shard": sorted(set(rows_per_shard(args.sample_size,
                                                                   args.shards))),
                       "concurrency": args.concurrency, "per_host_delay_s": args.per_host_delay,
                       "timeout_s": args.timeout, "max_retries": MAX_RETRIES,
                       "max_redirects": MAX_REDIRECTS, "user_agent": USER_AGENT,
                       "x_robots_directives": sorted(X_ROBOTS_DIRECTIVES),
                       "x_robots_tokens": ["(none)", *sorted(X_ROBOTS_TOKENS)],
                       "max_image_bytes": MAX_IMAGE_BYTES},
        **base,
        "summary": summary,
        "manifest": manifest,
    }


def print_report(result: dict) -> None:
    s = result["summary"]
    print(f"samples {s['samples']}, measured {s['measured_samples']}, "
          f"hosts {s['distinct_hosts']}, fetch {result['run']['fetch_seconds']}s")
    for c, v in s["categories_of_all_samples"].items():
        print(f"  {c:16s} {v['count']:5d}  {v['share']:.3f}  95% CI {v['ci95']}")
    for c, codes in s["breakdown"].items():
        print(f"  {c}: {codes}")
    print("reporting classes:")
    for c, v in s["reporting_classes_of_all_samples"].items():
        print(f"  {c:26s} {v['count']:5d}  {v['share']:.3f}  95% CI {v['ci95']}")
    print(f"  environment-excluded hosts: {s['environment_excluded_hosts']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--shards", type=int, default=DEFAULT_SHARDS,
                        help="parquet files to draw; rows are split evenly across them")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help="requests in flight overall (at most one per host regardless)")
    parser.add_argument("--per-host-delay", type=float, default=DEFAULT_PER_HOST_DELAY,
                        help="seconds between requests to the same host")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="seconds per request, connect plus body")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--select-only", action="store_true",
                        help="draw the sample and print its manifest; fetch no image")
    parser.add_argument("--count-frame", action="store_true",
                        help="also read every parquet footer at the revision and record the "
                             "frame's total row count (metadata only, no image requests)")
    parser.add_argument("--resummarize", metavar="RESULT_JSON",
                        help="recompute the summary of a saved result from its manifest, "
                             "fetching nothing; writes to --out or stdout")
    parser.add_argument("--out", help="write the JSON result here instead of stdout")
    args = parser.parse_args(argv)
    if args.resummarize:
        with open(args.resummarize, encoding="utf-8") as fh:
            result = json.load(fh)
        old = result.get("summary", {})
        summary = summarize([{**m, "category": m["outcome"]} for m in result["manifest"]])
        # Fetched hashes are not kept in the manifest, so this one figure carries over.
        if "changed_content_repeated_fetched_hash" in old:
            summary["changed_content_repeated_fetched_hash"] = \
                old["changed_content_repeated_fetched_hash"]
        result["summary"] = summary
        if args.count_frame:
            src = result["source"]
            src["frame"] = count_frame(src["repo"], src["revision"])
        text = json.dumps(result, indent=1, sort_keys=False) + "\n"
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
            print_report(result)
        else:
            sys.stdout.write(text)
        return 0
    if not 0 < args.shards <= args.sample_size:
        parser.error("--shards must be between 1 and --sample-size")
    if args.concurrency < 1 or args.concurrency > 8:
        parser.error("--concurrency must be between 1 and 8")
    if args.per_host_delay < 1.0:
        parser.error("--per-host-delay must be at least 1 second")
    result = run(args)
    text = json.dumps(result, indent=1, sort_keys=False) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        if not args.select_only:
            print_report(result)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
