# OpenCLIP recoverability pilot: DataComp-1B, 2026-11-14

This brief reports a pilot measurement for the `openclip.openness` hold in
`sources/verification_queue.yaml`. Under R-2026-11-13-d (`docs/reference/openness.md`, "A web-crawl
corpus is open when its release documents a basis for reuse"), a release that publishes URLs rather
than content counts as a released corpus only when reconstruction is materially possible, and how
much of the governing corpus can still be recovered has to be shown rather than assumed, with no
fixed minimum. The maintainer authorized a pilot, not a full crawl. This is that pilot: one
thousand DataComp-1B samples, drawn with a recorded seed, fetched once each under polite limits,
and checked against the sha256 the metadata publishes.

It changes no score, hold, value or rubric and draws no scoring conclusion. It sets out what was
measured and what the numbers can and cannot support, for the maintainer to weigh. Like the other
records in `docs/briefs/`, it describes the state on the date above and gets refreshed by a new
brief, not edited.

The script is `build/recoverability_pilot.py`. The machine-readable result, with every count, every
interval and the sample manifest (uid, shard file, row index, host, outcome code; no image URLs,
no image content), is `docs/briefs/2026-11-14-openclip-recoverability-pilot.json`.

## The short answer

Of the 1,000 sampled DataComp-1B rows, 343 returned the exact bytes the metadata hashed
(34.3%, 95% Wilson interval 31.4% to 37.3%). Another 265 returned an image whose hash differs
(26.5%, 23.9% to 29.3%), most of them at the original pixel dimensions. 158 are gone in the
plainest sense: 404, 410, or a host name that no longer resolves (15.8%, 13.7% to 18.2%). 87 were
skipped because the publisher opts out through robots.txt or `X-Robots-Tag` (8.7%, 7.1% to 10.6%).
The rest split across access-controlled, transient, non-image and other client-error outcomes,
each reported separately below.

Read together: byte-exact recovery of the sampled frame, on this date, from this network, under
these rules, is at least 34.3%, and at most about 56% even if every outcome that could change on
another attempt or another network had matched. Some image comes back for 60.8% (57.7% to 63.8%).
Recovery is uneven by host type: e-commerce CDNs serve images for almost every sampled row but
almost never the original bytes, and every Pinterest row is excluded by robots.txt. Whether what
remains faithfully reconstructs the training corpus is the maintainer's question; this pilot gives
the measurements and does not answer it.

## What was measured

**The governing corpus.** The DataComp.XL OpenCLIP checkpoints the `openclip` record cites were
trained on DataComp-1B, published as a URL and caption index at
[`mlfoundations/datacomp_1b`](https://huggingface.co/datasets/mlfoundations/datacomp_1b). Each row
carries a `uid`, a `url`, the caption, the original width and height, two CLIP scores, face boxes
and a `sha256`. Neither the dataset card nor the DataComp README describes the `sha256` column. The
pilot treated it as the hash of the raw downloaded bytes, and 343 exact matches against raw bytes
confirm that reading.

**The sampling frame.** Every `*.parquet` file in `mlfoundations/datacomp_1b` at revision
`086ebeee20d4cc3b3e7c05ae703fcf278ae3a759` (the repository's head on 2026-11-14, last modified
2023-08-21): 2,664 files holding 1,387,173,656 rows. The row total was summed from every file's
parquet footer by the script's `--count-frame` option, and matches the Hugging Face dataset viewer's
`num_rows`. Files hold 2,600 to 543,492 rows; the 50 drawn hold 499,349 to 541,711. The `.npz`
files beside them (precomputed embeddings) were not read.

**Selection.** Seed `20261114`, Python 3.13's `random.Random`.

1. List the parquet files at the revision and sort them by name.
2. `rng = random.Random(20261114)`; `rng.sample(files, 50)` draws 50 files without replacement.
3. For each drawn file, in draw order: read its row count from the footer, then
   `sorted(rng.sample(range(num_rows), 20))` draws 20 row indices without replacement from the same
   generator.
4. Read the `uid`, `url`, `sha256`, `original_width` and `original_height` columns of each drawn
   file and take those rows.
5. Shuffle the fetch order with `random.Random("20261114:fetch-order")`. This changes timing only.

`uv run python -m build.recoverability_pilot --select-only` repeats steps 1 to 4 and prints the
manifest without fetching any image. It was rerun after the measurement and reproduced the same
1,000 `uid`s, files and rows.

This is a two-stage cluster sample. Drawing the same number of rows from each drawn file weights a
row by the inverse of its file's size; because the largest drawn file is 8.5% larger than the smallest,
the effect on these shares is small, but a row in one of the few small files would be overweighted
if one were drawn. Rows within a file appear shuffled (adjacent rows share a host 0.3% of the time
in one file inspected), so the clustering costs little precision. The intervals below are simple
Wilson intervals that treat the sample as simple random.

## Method and constraints

All of these were mandatory, and the run record in the JSON shows the observed values.

| Constraint | What the script did |
|---|---|
| Concurrency | 8 workers, each with one request in flight; observed maximum 8 |
| One request per host at a time | A per-host gate; hosts keyed by host name, ignoring scheme and port |
| At least 1 s between requests to a host | Measured from the end of one request to the start of the next; observed minimum gap 1.000 s |
| Timeout about 20 s | 20 s connect and 20 s per read, and the body read stops at 20 s from the request start |
| At most one retry | Only after a connection error or timeout, never after any HTTP status. No sample's image request was retried; retries of robots.txt requests are not counted in the record |
| No credentials or impersonation | No cookies (a reject-all cookie policy), no auth headers, no referer, no `.netrc` (`trust_env` off), no proxy rotation, no captcha handling. Headers sent: `User-Agent`, `Accept: */*`, `Accept-Encoding: identity` |
| User-Agent | `datacomp-recoverability-check/0.1 (dataset recoverability check; samples a published image-URL index)`. img2dataset's own default is a Firefox browser string, which was not used |
| robots.txt | Fetched once per origin (scheme, host, port), read per RFC 9309: longest match wins, allow wins ties, `*` and `$` supported. A URL is skipped if disallowed for this User-Agent or for `*`. A 5xx or 429 answer means full disallow; a 404, 410 or other 4xx means no rules |
| `X-Robots-Tag` | img2dataset's default directive set (`noai`, `noimageai`, `noindex`, `noimageindex`), checked on every response in a redirect chain, and the body of an opted-out response is not read. A directive counts when it names no user agent, this one, or `img2dataset` (img2dataset's default honors only the first) |
| Redirects | Up to 10 hops, cross-host included, which is what img2dataset's `urllib` fetcher does by default. robots.txt and the per-host limits apply to every hop |
| Hashing | The body is held in memory, hashed with sha256 and discarded. No image was written to disk or kept |

Outbound HTTPS from this environment goes through an egress proxy on port 443. A CONNECT answered
403 or 407 is a proxy refusal and was to be recorded as an environment exclusion, as were 429 or
503 from the proxy and any HTTPS URL on a port other than 443, which the proxy cannot carry. A 502
on CONNECT means the gateway could not reach the host; the script then resolved the name locally to
separate a DNS failure from a connect failure, and counts both as host outcomes. Plain HTTP leaves
the container directly, so the script refused any HTTP destination that resolves to a non-public
address. None did.

The run started at 01:29 UTC on Saturday 2026-11-14 and finished at 01:40: 6.3 minutes reading
metadata from Hugging Face and 4.6 minutes fetching. It made 1,988 requests to 699 image hosts,
including robots.txt from 830 origins.

## Results

### By reporting class

Every class is separate; none is folded into an "unavailable" total. Shares are of all 1,000
samples, with 95% Wilson intervals.

| Class | Codes | Count | Share | 95% interval |
|---|---|---:|---:|---|
| Hash match | `hash_match` | 343 | 34.3% | 31.4% to 37.3% |
| Image served, hash differs | `same_dims` 226, `different_dims` 39 | 265 | 26.5% | 23.9% to 29.3% |
| Definitively gone | `http_404` 88, `dns_error` 63, `http_410` 7 | 158 | 15.8% | 13.7% to 18.2% |
| Transient or environment | `tls_error` 15, `connection_reset` 6, `http_503` 3, `timeout` 2, `http_429` 1, `http_500` 1, `http_522` 1, `proxy_error` 1 | 30 | 3.0% | 2.1% to 4.3% |
| Access-controlled | `http_403` 59, `http_401` 2 | 61 | 6.1% | 4.8% to 7.8% |
| Non-image response | `non_image` 16 (15 `text/html`, 1 SVG) | 16 | 1.6% | 1.0% to 2.6% |
| Other client error | `http_400` 18 | 18 | 1.8% | 1.1% to 2.8% |
| Opt-out | `robots_disallow` 78, `x_robots_tag` 9 (8 `noindex`, 1 `noai`) | 87 | 8.7% | 7.1% to 10.6% |
| robots.txt unreachable | `robots_unavailable` 22 (robots.txt answered 5xx or 429) | 22 | 2.2% | 1.5% to 3.3% |

A few of these need a word:

- **`dns_error`.** 63 samples on 59 hosts. Re-resolved locally after the run, 43 of the 59 hosts
  return NXDOMAIN and 16 return a name with no address records; none resolve. 63 of the 158 "gone"
  rows rest on DNS. Of the 63, 39 were HTTPS URLs whose failure was first seen as a 502 from the
  gateway, and 24 were plain HTTP resolved locally.
- **`http_400`.** Mostly Jetpack's `i*.wp.com` image proxy, Getty Images and Wikimedia thumbnails.
  A 400 can mean a dead origin behind a proxy or a request the server will not serve in that form,
  so it is kept out of "gone".
- **`tls_error`** includes certificate failures on the host. TLS is re-terminated at the egress
  proxy, which passes the host's certificate verdict through, so these are host certificate
  problems as seen from this network. They are still classed as transient or environment because a
  certificate can be renewed and another client may judge it differently.
- **`proxy_error`.** One sample: the CONNECT for `imgeh1.chinacdnb2b.com`'s robots.txt failed
  without a status the script could read. A later manual request through the same proxy connected
  and the host answered with nginx's 444. It is the only environment exclusion, and it is not a
  policy refusal.

The four-way split the pilot was first asked for: success 343 (34.3%, 31.4% to 37.3%); changed
content 265 (26.5%, 23.9% to 29.3%); failure 282 (28.2%, 25.5% to 31.1%); excluded 110 (11.0%,
9.2% to 13.1%). The excluded 110 are the 87 opt-outs, the 22 unreachable robots.txt and the one
proxy error.

### Environment exclusions

No CONNECT was refused by the proxy (no 403 or 407), none was answered 429 or 503 by the proxy, and
no sampled URL used HTTPS on a port other than 443. The one environment exclusion is the
`proxy_error` above, host `imgeh1.chinacdnb2b.com`. The proxy did not block a meaningful share of
image hosts, so the pilot could measure what it set out to.

### The robots.txt 401 and 403 reading

RFC 9309 treats a robots.txt answered with any 4xx, 401 and 403 included, as imposing no rules, and
the script follows it. Python's `urllib.robotparser` reads 401 and 403 as full disallow. 102 samples
were fetched from origins whose robots.txt answered 401 or 403 (49 matched, 19 changed, 34 failed).
Under the stricter reading the shares would be: hash match 29.4% (26.7% to 32.3%), changed content
24.6% (22.0% to 27.4%), failure 24.8% (22.2% to 27.6%), excluded 21.2% (18.8% to 23.8%). The JSON
carries both, under `robots_401_403_not_excluded`.

### Top hosts

699 distinct hosts across 1,000 samples. The largest, with the outcome of each sample:

| Host | Samples | Match | Changed | Failed | Excluded |
|---|---:|---:|---:|---:|---:|
| `i.ebayimg.com` | 28 | 0 | 28 | 0 | 0 |
| `i.pinimg.com` | 26 | 0 | 0 | 0 | 26 |
| `s-media-cache-ak0.pinimg.com` | 16 | 0 | 0 | 0 | 16 |
| `images-na.ssl-images-amazon.com` | 13 | 0 | 13 | 0 | 0 |
| `render.fineartamerica.com` | 11 | 0 | 11 | 0 | 0 |
| `static.wixstatic.com` | 11 | 3 | 7 | 1 | 0 |
| `i0.wp.com` | 10 | 3 | 3 | 4 | 0 |
| `ecx.images-amazon.com` | 10 | 0 | 10 | 0 | 0 |
| `i.ytimg.com` | 9 | 7 | 0 | 2 | 0 |
| `cdn11.bigcommerce.com` | 9 | 2 | 3 | 4 | 0 |
| `thumbs.dreamstime.com` | 8 | 0 | 8 | 0 | 0 |
| `m.media-amazon.com` | 8 | 0 | 8 | 0 | 0 |
| `www.specsserver.com` | 7 | 0 | 0 | 0 | 7 |
| `t0.gstatic.com` | 7 | 3 | 3 | 1 | 0 |

The Pinterest and Specsserver exclusions are all robots.txt disallows.

### By host type

Host types come from a short suffix list in the script and are a heuristic; "other" is everything
the list does not name.

| Host type | Samples | Match | Changed | Failed | Excluded | Match share of non-excluded |
|---|---:|---:|---:|---:|---:|---:|
| other | 571 | 219 | 107 | 202 | 43 | 41.5% |
| e-commerce CDNs | 121 | 9 | 97 | 8 | 7 | 7.9% |
| self-hosted WordPress | 106 | 39 | 17 | 37 | 13 | 41.9% |
| cloud storage and CDNs | 65 | 42 | 5 | 17 | 1 | 65.6% |
| site builders and blog hosts | 63 | 20 | 29 | 13 | 1 | 32.3% |
| Pinterest | 44 | 0 | 0 | 0 | 44 | n/a |
| stock photo sites | 30 | 14 | 10 | 5 | 1 | 48.3% |

By scheme: 758 HTTPS samples (251 match, 214 changed, 206 failed, 87 excluded) and 242 plain HTTP
(92, 51, 76, 23).

## What the classes can and cannot defend

**Can defend:**

- *A lower bound on byte-exact recovery*: 34.3% (31.4% to 37.3%) of DataComp-1B rows return the
  exact bytes the release hashed, on this date, from this network, under these rules.
- *An upper bound on byte-exact recovery under the same rules*: at most 56.1% (53.0% to 59.2%). That
  is 1,000 less the 158 gone, the 265 that served a different image and the 16 non-image responses,
  and it assumes that every transient, access-controlled, other-client-error, unreachable-robots and
  opt-out sample would have matched.
- *A floor on loss*: at least 15.8% (13.7% to 18.2%) of rows point at a resource that is gone by the
  plainest test: 404, 410 or a name that no longer resolves.
- *A share of rows where some image is still served*: 60.8% (57.7% to 63.8%).
- *That recovery is not uniform across the corpus*: it differs sharply by host type, and a rebuild
  from today's web would under-represent e-commerce images in their original bytes and drop
  Pinterest entirely under these rules.

**Cannot defend:**

- *That a changed hash is a lost image.* The 265 rows returned an image. 226 have the original
  pixel dimensions, which fits a re-encode, metadata stripping or a CDN format change of the same
  picture, but the pilot did no perceptual comparison and cannot tell a re-encode from a different
  picture at the same size. 16 of the 265 share a fetched hash with another sample, a sign of
  placeholder images. A mismatch means the bytes differ, nothing more.
- *That a failed fetch is an unavailable image.* Timeouts, resets, TLS errors, 5xx, 429 and the
  proxy error may succeed on another attempt or from another network. A 401 or 403 may be bot
  management that treats this network or User-Agent differently from others. Neither class is
  evidence the image is gone.
- *Anything about the opted-out rows' bytes.* The 87 opt-outs and the 22 unreachable robots.txt were
  not fetched, by design. They are neither recovered nor lost.
- *Time.* One run, over 11 minutes, on one Saturday early morning UTC. Link rot moves one way; this
  is a snapshot, not a rate.
- *Representativeness beyond the stated precision.* 1,000 rows put roughly three points either side
  of each large share. Hosts with a few samples, including most of the top-hosts table, say little
  individually.
- *LAION-2B.* The older OpenCLIP checkpoints trained on LAION-2B, a different corpus not measured
  here.

## Limitations

- **Sample size and design.** 1,000 rows from 50 of 2,664 files. Simple Wilson intervals understate
  uncertainty slightly for a cluster sample.
- **Time of day and day of week.** Hosts that throttle or fail under load may behave differently at
  other times.
- **Network.** HTTPS went through the session's egress proxy, plain HTTP directly. The proxy refused
  nothing, but bot management at hosts and CDNs may treat this network differently from a
  residential or academic one.
- **The robots.txt reading.** The script follows RFC 9309 on 401 and 403. The stricter reading is
  reported above. `Crawl-delay` is not part of RFC 9309 and was not read; the 1 s per-host gap and
  one-at-a-time rule applied everywhere.
- **The hash.** Exact sha256 equality is a strict test. It confirms that the bytes are the bytes the
  release hashed. It cannot confirm that a different file is a different picture.
- **Dimensions.** The dimension check parses JPEG, PNG, GIF and WebP headers and compares them with
  `original_width` and `original_height`. It is a signal, not a perceptual match.
- **The original collection's opt-outs.** This pilot does not answer the second open point in the
  hold. What the 2022-2023 collection honored (which img2dataset version, which opt-out settings,
  whether image hosts' robots.txt was read at all) is a question about that collection's records,
  and today's robots.txt and `X-Robots-Tag` answers say nothing about what the hosts said then.

## What an expansion would need

- **A larger, stratified sample.** Stratify by file, or draw rows with probability proportional to
  file size, so the sample is self-weighting. A few thousand rows would halve the intervals, and
  oversampling the largest host types would make per-type figures usable.
- **Repeat runs.** Two or three runs at different times and days, to separate transient failures
  from persistent ones and to measure drift. A second pass over the 30 transient and 61
  access-controlled rows alone would show how much of each is recoverable on retry.
- **A second network.** Repeat the access-controlled and transient rows from a different network
  to see how much depends on where the request comes from.
- **A perceptual check on changed content.** Embed each fetched image in memory with the same CLIP
  model and compare it with the image embedding the release precomputed in its `.npz` files. That
  would tell a re-encode of the same picture from a replacement without keeping any image.
- **A decision on the robots.txt reading.** Whether 401 and 403 on robots.txt mean no rules (RFC 9309)
  or disallow (`urllib.robotparser`) changes the excluded share by about ten points.
- **The original download configuration.** For the opt-out question, the DataComp authors' record of
  the img2dataset version and settings used for the 2022-2023 collection.

Nothing in this brief moves a score or releases the hold. Any change to `openclip.openness` comes to
the maintainer with its evidence in its own PR.

## Sources

| Source | Used for |
|---|---|
| `https://huggingface.co/datasets/mlfoundations/datacomp_1b` at `086ebeee20d4cc3b3e7c05ae703fcf278ae3a759` | The frame: 2,664 parquet files, 1,387,173,656 rows; the sampled rows |
| `https://datasets-server.huggingface.co/size?dataset=mlfoundations/datacomp_1b` | Cross-check of the row total (`num_rows` 1,387,173,656) |
| `https://raw.githubusercontent.com/mlfoundations/datacomp/main/download_upstream.py` | The reconstruction script's img2dataset call (defaults for opt-out headers; `--retries` 2) |
| img2dataset 1.47.0 from PyPI, `img2dataset/main.py` and `img2dataset/downloader.py` | Default `X-Robots-Tag` directives, token matching, `urllib` redirect behavior, default User-Agent |
| RFC 9309, Robots Exclusion Protocol | robots.txt matching and status handling |
| `docs/briefs/2026-11-14-openclip-recoverability-pilot.json` | Every figure above |
