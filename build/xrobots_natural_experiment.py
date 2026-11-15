"""Test from published data whether DataComp's CommonPool collection honored X-Robots-Tag opt-outs.

Why this exists. The `openclip.openness` hold in `sources/verification_queue.yaml` asks how the
December 2022 to March 2023 CommonPool collection handled publisher opt-outs, and the run's
img2dataset version and `disallowed_header_directives` value were never published
(`docs/briefs/2026-11-14-datacomp-download-provenance.md`). CommonPool holds a row only for an
image the collection downloaded, so if a host was sending `X-Robots-Tag: noai` or `noimageai` on
its image responses throughout the window, rows on that host are a natural experiment: present in
quantity, the header was not honored for at least part of the run. This module measures the parts
of that experiment that can be measured from public data, reading headers only. It writes nothing
under `sources/`, keeps no image, moves no score and gates nothing; it is a survey, like
`build.recoverability_pilot`, and is never wired into preflight or CI.

Three measuring steps, each its own subcommand, each writing one JSON result.

`pool` draws a seeded sample of the parquet files in the unfiltered CommonPool metadata
(`mlfoundations/datacomp_xlarge` at a pinned revision), reads only the `uid`, `url` and `sha256`
columns of each drawn file over HTTP range requests, and counts rows by host family (DeviantArt's
image CDN and legacy image hosts, and ArtStation's CDN as a comparison). It reports per-file
counts, the pooled share, and a pool-wide total estimated by expanding the per-file mean over the
number of files, each with a file-bootstrap 95% interval. `--rows-out` writes every matched row.

`headers-now` sends HTTP HEAD requests, today, to a seeded sample of the matched URLs and records
the `X-Robots-Tag` header on every hop of the redirect chain. This shows what those hosts send
now, not what they sent in the window; the brief keeps the two apart. `--token-aud` keeps only
DeviantArt CDN URLs whose signed token names one service, such as the original-file download.

`wayback` reads archived response headers: the Wayback Machine keeps a capture's original headers
as `X-Archive-Orig-*` on `https://web.archive.org/web/<timestamp>id_/<url>`. It lists captures of a
host's image URLs month by month through the CDX API, HEADs a seeded sample of them, and does the
same for the exact URLs of a seeded sample of matched pool rows. It first probes that
web.archive.org answers at all, and when it does not, it records the failed probes and stops
rather than reading any other archive in its place.

`combine` gathers the step results into the single JSON the brief cites, and fetches nothing.

Request rules: HEAD only (no image body is ever requested); a generic User-Agent; requests to one
host strictly sequential with at least `--delay` seconds between them; one retry, after a
connection error only. The brief that reports the 2026-11-15 run, with its limits, is
`docs/briefs/2026-11-15-datacomp-xrobots-natural-experiment.md`; the rule the hold applies is in
`docs/reference/openness.md`, "A web-crawl corpus is open when its release documents a basis for
reuse".
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import random
import re
import statistics
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

DEFAULT_REPO = "mlfoundations/datacomp_xlarge"
DEFAULT_REVISION = "2ee99257ee8af28386835355897ce5da07cca010"
DEFAULT_SEED = 20261115
DEFAULT_FILES = 60
DEFAULT_HEAD_SAMPLE = 300
DEFAULT_DELAY = 1.0
DEFAULT_TIMEOUT = 20.0
MAX_REDIRECTS = 10
BOOTSTRAP_REPS = 10_000
COLUMNS = ["uid", "url", "sha256"]
USER_AGENT = "Mozilla/5.0 (compatible; header-survey/0.1)"
OPT_OUT_DIRECTIVES = ("noai", "noimageai")
# img2dataset 1.39.0 and later drop an image on any of these when no list is configured.
IMG2DATASET_DEFAULT_DIRECTIVES = ("noai", "noimageai", "noindex", "noimageindex")

# The window in the DataComp datasheet (Q26), and the months either side that the archive pass
# reads so the share before DeviantArt's 2022-11-11 announcement can be compared with the share
# during the collection.
WAYBACK_MONTHS = ["202208", "202209", "202210", "202211", "202212", "202301", "202302",
                  "202303", "202304", "202305", "202306"]
WAYBACK_HOST_PREFIXES = {
    "deviantart_wixmp": "images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/",
}
WAYBACK_EXACT_FROM, WAYBACK_EXACT_TO = "202211", "202304"

# Host families. Order matters: the first pattern that matches names the family.
FAMILIES = (
    ("deviantart_wixmp", re.compile(r"images-wixmp-[0-9a-f]+\.wixmp\.com")),
    ("deviantart_avatar", re.compile(r"a\.deviantart\.net")),
    ("deviantart_legacy_art", re.compile(r"(?:fc|orig|img|pre|th|t|s)\d*\.deviantart\.net")),
    ("deviantart_other", re.compile(r"(?:[a-z0-9-]+\.)*deviantart\.(?:net|com)")),
    ("artstation_cdn", re.compile(r"cdn[a-z]?\.artstation\.com")),
)
DEVIANTART_FAMILIES = tuple(f for f, _ in FAMILIES if f.startswith("deviantart"))


def host_of(url: str) -> str:
    try:
        return (urllib.parse.urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def family_of(host: str) -> str | None:
    for name, pattern in FAMILIES:
        if pattern.fullmatch(host):
            return name
    return None


def opt_out_directives(values: list[str]) -> list[str]:
    """Directives in X-Robots-Tag values that name no user agent, lower-cased.

    `X-Robots-Tag: somebot: noai` is scoped to one crawler and img2dataset's default ignores it,
    so only un-scoped directives are returned. Values are comma-separated directive lists.
    """
    found = []
    for value in values:
        head, sep, _ = value.partition(":")
        head = head.strip().lower()
        if sep and "," not in head and head != "unavailable_after" \
                and not head.startswith("max-"):
            continue  # `<agent>: <directives>`, scoped to a user agent
        found += [d.strip().lower() for d in value.split(",") if d.strip()]
    return found


# ── statistics ─────────────────────────────────────────────────────────────────────────────


def file_bootstrap(per_file: list[dict], families: list[str], n_files_frame: int,
                   seed: str, reps: int = BOOTSTRAP_REPS) -> dict:
    """Percentile 95% intervals for each family's pooled share and expanded pool-wide total.

    Each replicate resamples the drawn files with replacement. The share is matched rows over
    rows read; the total is the replicate's mean matched rows per file times the number of files
    in the frame, the expansion estimator for a simple random sample of files.
    """
    rng = random.Random(seed)
    n = len(per_file)
    shares = {f: [] for f in families}
    totals = {f: [] for f in families}
    for _ in range(reps):
        picked = [per_file[rng.randrange(n)] for _ in range(n)]
        rows = sum(p["rows"] for p in picked)
        for f in families:
            k = sum(p["families"].get(f, 0) for p in picked)
            shares[f].append(k / rows)
            totals[f].append(k / n * n_files_frame)
    rows = sum(p["rows"] for p in per_file)
    out = {}
    for f in families:
        k = sum(p["families"].get(f, 0) for p in per_file)
        s, t = sorted(shares[f]), sorted(totals[f])
        lo, hi = int(0.025 * reps), int(0.975 * reps) - 1
        per = [p["families"].get(f, 0) for p in per_file]
        out[f] = {"rows_in_sample": k,
                  "share": k / rows, "share_ci95": [s[lo], s[hi]],
                  "pool_total_estimate": round(k / n * n_files_frame),
                  "pool_total_ci95": [round(t[lo]), round(t[hi])],
                  "per_file_min": min(per), "per_file_median": statistics.median(per),
                  "per_file_max": max(per)}
    return {"method": "file bootstrap: resample the drawn files with replacement; percentile "
                      "95% interval; total = mean matched rows per file x files in frame",
            "replicates": reps, "seed": seed, "files": n, "estimates": out}


# ── step 1: the pool ───────────────────────────────────────────────────────────────────────


def list_parquet(repo: str, revision: str) -> list[dict]:
    from huggingface_hub import HfApi
    info = HfApi().dataset_info(repo, revision=revision, files_metadata=True, token=False)
    return sorted(({"file": s.rfilename, "size": s.size} for s in info.siblings
                   if s.rfilename.endswith(".parquet")), key=lambda d: d["file"])


def scan_file(repo: str, revision: str, name: str) -> tuple[dict, list[dict]]:
    """Read three columns of one parquet file; count rows by family; return matched rows."""
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem
    fs = HfFileSystem(token=False)
    t0 = time.time()
    with fs.open(f"datasets/{repo}@{revision}/{name}", "rb", block_size=16 << 20) as handle:
        pf = pq.ParquetFile(handle)
        table = pf.read(columns=COLUMNS)
    urls = table.column("url").to_pylist()
    counts: collections.Counter = collections.Counter()
    hosts: collections.Counter = collections.Counter()
    matched_idx = []
    for i, url in enumerate(urls):
        host = host_of(url or "")
        fam = family_of(host)
        if fam:
            counts[fam] += 1
            hosts[host if fam != "deviantart_wixmp" else "images-wixmp-*.wixmp.com"] += 1
            matched_idx.append((i, fam, host))
    uids = table.column("uid").to_pylist()
    shas = table.column("sha256").to_pylist()
    matched = [{"file": name, "row": i, "family": fam, "host": host, "uid": uids[i],
                "sha256": shas[i], "url": urls[i]} for i, fam, host in matched_idx]
    return ({"file": name, "rows": len(urls), "families": dict(counts),
             "hosts": dict(hosts), "read_seconds": round(time.time() - t0, 1)}, matched)


def run_pool(args) -> dict:
    files = list_parquet(args.repo, args.revision)
    rng = random.Random(args.seed)
    drawn = rng.sample([f["file"] for f in files], args.files)
    started = dt.datetime.now(dt.UTC)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda n: scan_file(args.repo, args.revision, n), drawn))
    per_file = [r[0] for r in results]
    matched = [m for r in results for m in r[1]]
    families = [f for f, _ in FAMILIES] + ["deviantart_all"]
    for p in per_file:
        p["families"]["deviantart_all"] = sum(p["families"].get(f, 0) for f in DEVIANTART_FAMILIES)
    boot = file_bootstrap(per_file, families, len(files), f"{args.seed}:file-bootstrap")
    host_totals: collections.Counter = collections.Counter()
    for p in per_file:
        host_totals.update(p["hosts"])
    if args.rows_out:
        with open(args.rows_out, "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(m) + "\n" for m in matched)
    sample_rng = random.Random(f"{args.seed}:published-row-sample")
    published = sorted(sample_rng.sample(matched, min(args.publish_rows, len(matched))),
                       key=lambda m: (m["file"], m["row"]))
    return {
        "step": "pool",
        "generated_by": "uv run python -m build.xrobots_natural_experiment pool",
        "source": {"repo": args.repo, "revision": args.revision,
                   "parquet_files_at_revision": len(files),
                   "columns_read": COLUMNS},
        "parameters": {"seed": args.seed, "files": args.files,
                       "selection": "sorted parquet file names; random.Random(seed).sample("
                                    "files, n); every row of each drawn file is read"},
        "run": {"started": started.isoformat(timespec="seconds"),
                "finished": dt.datetime.now(dt.UTC).isoformat(timespec="seconds")},
        "rows_read": sum(p["rows"] for p in per_file),
        "estimates": boot,
        "top_hosts_in_sample": host_totals.most_common(40),
        "per_file": per_file,
        "published_row_sample": {
            "seed": f"{args.seed}:published-row-sample", "rows": published,
            "note": "a seeded subsample of matched rows; --rows-out writes all of them"},
    }


# ── HTTP: HEAD only ────────────────────────────────────────────────────────────────────────


class Header:
    """A HEAD-only client with a per-host gap and one retry after a connection error."""

    def __init__(self, delay: float, timeout: float):
        import requests
        self.requests = requests
        self.session = requests.Session()
        self.session.trust_env = True  # the egress proxy is configured through the environment
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*",
                                     "Accept-Encoding": "identity"})
        self.delay, self.timeout = delay, timeout
        self.last: dict[str, float] = {}
        self.count = 0
        self.min_gap: float | None = None

    def head(self, url: str) -> dict:
        host = host_of(url)
        for attempt in range(2):
            wait = self.last.get(host, 0) + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            if host in self.last:
                gap = time.monotonic() - self.last[host]
                self.min_gap = gap if self.min_gap is None else min(self.min_gap, gap)
            self.count += 1
            try:
                r = self.session.head(url, timeout=self.timeout, allow_redirects=False)
                self.last[host] = time.monotonic()
                return {"status": r.status_code, "headers": r.headers, "attempts": attempt + 1}
            except (self.requests.exceptions.ConnectionError,
                    self.requests.exceptions.Timeout) as err:
                self.last[host] = time.monotonic()
                if attempt == 1:
                    return {"status": None, "error": type(err).__name__,
                            "detail": str(err)[:200], "attempts": 2}
            except self.requests.exceptions.RequestException as err:
                self.last[host] = time.monotonic()
                return {"status": None, "error": type(err).__name__,
                        "detail": str(err)[:200], "attempts": attempt + 1}
        raise AssertionError("unreachable")


def head_chain(client: Header, url: str) -> dict:
    """HEAD the URL and each redirect it answers with; X-Robots-Tag recorded per hop."""
    hops = []
    for _ in range(MAX_REDIRECTS + 1):
        r = client.head(url)
        hop = {"host": host_of(url), "status": r["status"]}
        if r["status"] is None:
            hop["error"] = r["error"]
            hops.append(hop)
            break
        xrt = [v.strip() for v in r["headers"].get("X-Robots-Tag", "").split("\n") if v.strip()]
        # requests folds repeated headers into one comma-joined value; keep the raw text.
        if xrt:
            hop["x_robots_tag"] = xrt
        hop["content_type"] = r["headers"].get("Content-Type")
        hops.append(hop)
        loc = r["headers"].get("Location")
        if r["status"] in (301, 302, 303, 307, 308) and loc:
            url = urllib.parse.urljoin(url, loc)
            continue
        break
    directives = sorted({d for h in hops for d in opt_out_directives(h.get("x_robots_tag", []))})
    return {"hops": hops, "final_status": hops[-1]["status"], "final_host": hops[-1]["host"],
            "directives": directives,
            "opt_out": any(d in OPT_OUT_DIRECTIVES for d in directives),
            "img2dataset_default_would_drop": any(d in IMG2DATASET_DEFAULT_DIRECTIVES
                                                  for d in directives)}


def load_rows(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def stratified_sample(rows: list[dict], n: int, seed: str) -> list[dict]:
    """Up to n rows, split across families in proportion, at least a few from each."""
    rng = random.Random(seed)
    by_fam: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_fam[r["family"]].append(r)
    total = len(rows)
    picked = []
    for fam in sorted(by_fam):
        k = max(min(10, len(by_fam[fam])), round(n * len(by_fam[fam]) / total))
        picked += rng.sample(by_fam[fam], min(k, len(by_fam[fam])))
    return picked


# ── step 2: headers today ──────────────────────────────────────────────────────────────────


def token_audiences(url: str) -> list[str]:
    """The `aud` claim of a DeviantArt CDN URL's `token` query parameter (a JWT), if any.

    DeviantArt signs CDN URLs with a JWT whose audience names the service: image operations
    (resized renditions) or file download (the original file). The token carries no date.
    """
    import base64
    token = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get("token", [""])[0]
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (IndexError, ValueError):
        return []
    aud = claims.get("aud", [])
    return aud if isinstance(aud, list) else [str(aud)]


def run_headers_now(args) -> dict:
    rows = load_rows(args.rows)
    tag = "headers-now"
    if args.token_aud:
        rows = [r for r in rows if args.token_aud in token_audiences(r["url"])]
        tag = f"headers-now:{args.token_aud}"
    sample = stratified_sample(rows, args.sample, f"{args.seed}:{tag}")
    client = Header(args.delay, args.timeout)
    started = dt.datetime.now(dt.UTC)
    out = []
    for r in sample:
        res = head_chain(client, r["url"])
        out.append({"uid": r["uid"], "family": r["family"], "url": r["url"], **res})
    summary = {}
    for fam in sorted({o["family"] for o in out}):
        sub = [o for o in out if o["family"] == fam]
        summary[fam] = {
            "sampled": len(sub),
            "final_status": dict(collections.Counter(str(o["final_status"]) for o in sub)),
            "any_x_robots_tag": sum(1 for o in sub if any("x_robots_tag" in h for h in o["hops"])),
            "noai_or_noimageai": sum(1 for o in sub if o["opt_out"]),
            "img2dataset_default_would_drop": sum(1 for o in sub
                                                  if o["img2dataset_default_would_drop"]),
            "directives_seen": dict(collections.Counter(d for o in sub for d in o["directives"])),
        }
    return {"step": "headers-now",
            "generated_by": "uv run python -m build.xrobots_natural_experiment headers-now",
            "method": "HTTP HEAD only, redirects followed by HEAD, X-Robots-Tag per hop; "
                      "headers as served on the run date, not during the collection window",
            "parameters": {"seed": f"{args.seed}:{tag}", "sample": args.sample,
                           "token_aud": args.token_aud, "rows_eligible": len(rows),
                           "delay_seconds": args.delay, "user_agent": USER_AGENT},
            "run": {"started": started.isoformat(timespec="seconds"),
                    "finished": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                    "requests": client.count,
                    "min_gap_same_host_seconds": round(client.min_gap or 0, 3)},
            "summary": summary, "results": out}


# ── step 3: the Wayback Machine ────────────────────────────────────────────────────────────


WAYBACK = "https://web.archive.org"


def probe_wayback(client: Header, attempts: int, spacing: float) -> list[dict]:
    log = []
    for i in range(attempts):
        if i:
            time.sleep(spacing)
        r = client.head(f"{WAYBACK}/")
        log.append({"at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                    "status": r["status"], "error": r.get("error"),
                    "detail": r.get("detail")})
        if r["status"] is not None and r["status"] < 500:
            break
    return log


def cdx(client: Header, url: str, frm: str, to: str, limit: int) -> list[dict] | dict:
    q =urllib.parse.urlencode({"url": url, "from": frm, "to": to, "output": "json",
                                "filter": "statuscode:200", "limit": limit})
    host = "web.archive.org"
    wait = client.last.get(host, 0) + client.delay - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    client.count += 1
    try:
        r = client.session.get(f"{WAYBACK}/cdx/search/cdx?{q}", timeout=60)
    except client.requests.exceptions.RequestException as err:
        client.last[host] = time.monotonic()
        return {"error": type(err).__name__}
    client.last[host] = time.monotonic()
    if r.status_code != 200:
        return {"error": f"http_{r.status_code}"}
    data = r.json() if r.text.strip() else []
    if not data:
        return []
    keys = data[0]
    return [dict(zip(keys, row)) for row in data[1:]]


def archived_headers(client: Header, timestamp: str, original: str) -> dict:
    r = client.head(f"{WAYBACK}/web/{timestamp}id_/{original}")
    if r["status"] is None:
        return {"status": None, "error": r["error"]}
    orig = [v.strip() for v in r["headers"].get("X-Archive-Orig-X-Robots-Tag", "").split("\n")
            if v.strip()]
    has_orig = any(k.lower().startswith("x-archive-orig-") for k in r["headers"])
    directives = sorted(set(opt_out_directives(orig)))
    return {"status": r["status"], "orig_headers_exposed": has_orig,
            "x_robots_tag": orig, "directives": directives,
            "opt_out": any(d in OPT_OUT_DIRECTIVES for d in directives)}


def run_wayback(args) -> dict:
    client = Header(max(args.delay, 1.0), args.timeout)
    started = dt.datetime.now(dt.UTC)
    probes = probe_wayback(client, args.probe_attempts, args.probe_spacing)
    result = {"step": "wayback",
              "generated_by": "uv run python -m build.xrobots_natural_experiment wayback",
              "parameters": {"seed": f"{args.seed}:wayback", "per_month": args.per_month,
                             "exact_urls": args.exact, "delay_seconds": client.delay},
              "run": {"started": started.isoformat(timespec="seconds")},
              "reachability_probes": probes}
    if not probes or probes[-1]["status"] is None or probes[-1]["status"] >= 500:
        result["status"] = "unreachable"
        result["note"] = ("web.archive.org did not answer from this environment; no archived "
                          "header was read and no other archive was substituted")
        result["run"]["finished"] = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
        return result
    rng = random.Random(f"{args.seed}:wayback")
    by_month = {}
    for fam, prefix in WAYBACK_HOST_PREFIXES.items():
        for month in WAYBACK_MONTHS:
            caps = cdx(client, prefix + "*", month, month, args.cdx_limit)
            if isinstance(caps, dict):
                by_month[f"{fam}:{month}"] = {"cdx_error": caps["error"]}
                continue
            caps = [c for c in caps if c.get("mimetype", "").startswith("image/")]
            pick = rng.sample(caps, min(args.per_month, len(caps)))
            heads = [{"timestamp": c["timestamp"], "original": c["original"],
                      **archived_headers(client, c["timestamp"], c["original"])} for c in pick]
            ok = [h for h in heads if h["status"] == 200]
            by_month[f"{fam}:{month}"] = {
                "cdx_image_captures_listed": len(caps), "sampled": len(pick),
                "answered_200": len(ok),
                "orig_headers_exposed": sum(1 for h in ok if h["orig_headers_exposed"]),
                "noai_or_noimageai": sum(1 for h in ok if h["opt_out"]),
                "captures": heads}
    result["host_months"] = by_month
    exact = []
    if args.rows:
        rows = stratified_sample([r for r in load_rows(args.rows)
                                  if r["family"] in DEVIANTART_FAMILIES],
                                 args.exact, f"{args.seed}:wayback-exact")
        for r in rows:
            caps = cdx(client, r["url"], WAYBACK_EXACT_FROM, WAYBACK_EXACT_TO, 20)
            if isinstance(caps, dict):
                exact.append({"uid": r["uid"], "url": r["url"], "cdx_error": caps["error"]})
                continue
            heads = [{"timestamp": c["timestamp"],
                      **archived_headers(client, c["timestamp"], c["original"])} for c in caps]
            exact.append({"uid": r["uid"], "family": r["family"], "url": r["url"],
                          "captures_in_window": len(caps), "captures": heads})
    result["exact_url_lookups"] = exact
    result["status"] = "ok"
    result["run"]["finished"] = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    result["run"]["requests"] = client.count
    return result


def run_combine(args) -> dict:
    """Gather the step results into the one JSON the brief cites; fetches nothing."""
    def load(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    out = {"experiment": "DataComp CommonPool X-Robots-Tag natural experiment",
           "generated_by": "uv run python -m build.xrobots_natural_experiment combine",
           "pool": [load(p) for p in args.pool],
           "headers_now": [load(p) for p in args.headers or []],
           "wayback": load(args.wayback) if args.wayback else None}
    for pool in out["pool"]:
        for p in pool["per_file"]:
            p.pop("hosts", None)  # per-host counts per file; the pooled top hosts stay
        rows = pool["published_row_sample"]["rows"]
        if args.publish_rows is not None and len(rows) > args.publish_rows:
            rng = random.Random(f"{pool['parameters']['seed']}:combine")
            pool["published_row_sample"]["rows"] = sorted(
                rng.sample(rows, args.publish_rows), key=lambda m: (m["file"], m["row"]))
            pool["published_row_sample"]["note"] += f"; cut to {args.publish_rows} by combine"
    return out


# ── CLI ────────────────────────────────────────────────────────────────────────────────────


def write(result: dict, path: str | None) -> None:
    text = json.dumps(result, indent=1, default=str) + "\n"
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="step", required=True)

    p = sub.add_parser("pool", help="count CommonPool rows by host family in a seeded file sample")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--revision", default=DEFAULT_REVISION)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--files", type=int, default=DEFAULT_FILES)
    p.add_argument("--workers", type=int, default=4, help="files read at once from Hugging Face")
    p.add_argument("--publish-rows", type=int, default=500,
                   help="matched rows to include in the JSON as a seeded subsample")
    p.add_argument("--rows-out", help="write every matched row here as JSON lines")
    p.add_argument("--out")

    h = sub.add_parser("headers-now", help="HEAD a seeded sample of matched URLs today")
    h.add_argument("--rows", required=True, help="the JSON-lines file `pool --rows-out` wrote")
    h.add_argument("--seed", type=int, default=DEFAULT_SEED)
    h.add_argument("--sample", type=int, default=DEFAULT_HEAD_SAMPLE)
    h.add_argument("--token-aud", help="keep only DeviantArt CDN URLs whose token audience is this, "
                                       "e.g. urn:service:file.download")
    h.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    h.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    h.add_argument("--out")

    w = sub.add_parser("wayback", help="read archived X-Robots-Tag headers from the Wayback Machine")
    w.add_argument("--rows", help="the JSON-lines file `pool --rows-out` wrote, for exact URLs")
    w.add_argument("--seed", type=int, default=DEFAULT_SEED)
    w.add_argument("--per-month", type=int, default=30)
    w.add_argument("--cdx-limit", type=int, default=2000)
    w.add_argument("--exact", type=int, default=200, help="pool rows to look up by exact URL")
    w.add_argument("--probe-attempts", type=int, default=3)
    w.add_argument("--probe-spacing", type=float, default=120.0,
                   help="seconds between reachability probes")
    w.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    w.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    w.add_argument("--out")

    c = sub.add_parser("combine", help="gather step results into one JSON; fetches nothing")
    c.add_argument("--pool", nargs="+", required=True)
    c.add_argument("--headers", nargs="*")
    c.add_argument("--wayback")
    c.add_argument("--publish-rows", type=int, help="cut each pool's published row sample to this")
    c.add_argument("--out")

    args = parser.parse_args(argv)
    if args.step == "combine":
        write(run_combine(args), args.out)
        return 0
    if getattr(args, "delay", 1.0) < 1.0:
        parser.error("--delay must be at least 1 second")
    if args.step == "pool":
        result = run_pool(args)
        e = result["estimates"]["estimates"]
        print(f"rows read {result['rows_read']:,} from {args.files} files", file=sys.stderr)
        for fam, v in e.items():
            print(f"  {fam:24s} {v['rows_in_sample']:7d}  share {v['share']:.5f} "
                  f"{[round(x, 5) for x in v['share_ci95']]}  pool total "
                  f"{v['pool_total_estimate']:,} {v['pool_total_ci95']}", file=sys.stderr)
    elif args.step == "headers-now":
        result = run_headers_now(args)
        for fam, v in result["summary"].items():
            print(f"  {fam}: {v}", file=sys.stderr)
    else:
        result = run_wayback(args)
        print(f"  wayback status: {result['status']}", file=sys.stderr)
    write(result, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
