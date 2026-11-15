# DataComp CommonPool and X-Robots-Tag: a natural experiment, 2026-11-15

This brief reports an attempt to answer, from published data and without contacting anyone, one
point held open on `openclip.openness` in `sources/verification_queue.yaml`: did DataComp's original
CommonPool collection (December 2022 to March 2023) honor `X-Robots-Tag: noai` and `noimageai`?
`docs/briefs/2026-11-14-datacomp-download-provenance.md` established that img2dataset added the
header check in 1.34.0 (2022-11-25), off by default, and made it the default in 1.39.0
(2022-12-19), and that the collection's version and settings are undocumented. The idea tested
here: CommonPool holds a row only for an image the collection downloaded, so rows on a host that
was sending the directive on its image responses throughout the window would show that the header
was not honored, at least for part of the run.

It changes no score, hold, rubric or ruling, draws no scoring conclusion and proposes no hold. Like
the other records in `docs/briefs/`, it describes what was observed on the date above and gets
refreshed by a new brief, not edited.

The script is `build/xrobots_natural_experiment.py`. The machine-readable result is
`docs/briefs/2026-11-15-datacomp-xrobots-natural-experiment.json`: per-file counts, estimates
and intervals, the top hosts, a seeded sample of 200 matched CommonPool rows (uid, sha256, URL),
every HEAD result with its headers, and the failed Wayback Machine probes. No image content was
requested or kept.

## The short answer

1. **The experiment could not be completed, because the treatment could not be shown.** It needs
   a host that sent the directive on the image URLs CommonPool links, during the window. DeviantArt
   says it sends `X-Robots-Tag: noai` "when the image is directly downloaded from DeviantArt's
   servers", for every deviation unless the artist opts in, from November 2022. Whether its image
   CDN actually did so on these URLs in December 2022 to March 2023 needs archived response
   headers. The Wayback Machine was unreachable from this environment for the whole session (11
   attempts from 17:35 to 18:17 UTC; HTTPS was reset during the TLS handshake every time, and
   plain HTTP was refused by the environment's egress policy). No other archive was
   substituted. So the archived-header share by month (step 1) and the exact-URL tie-in (step 3)
   were not measured.
2. **DeviantArt's CDN does not send the header today.** HEAD requests to 335 CommonPool URLs on
   DeviantArt hosts, redirects followed, found no `X-Robots-Tag` header at all. That includes 40
   CDN URLs signed for original-file download. Today's state cannot stand in for the window, but it
   means the published policy cannot be assumed to describe the CDN responses either.
3. **The rows are there, in quantity.** In a seeded sample of 60 of the 23,874 metadata files of
   the unfiltered 12.8B CommonPool (32,147,132 rows read), 45,865 rows (0.143%) are on DeviantArt
   image hosts. That expands to about 18.2 million pool-wide (file-bootstrap 95% interval 18.1M to
   18.4M), 9.5 million of them on DeviantArt's current image CDN. DataComp-1B, the subset the scored
   OpenCLIP checkpoints trained on, holds about 2.29 million (2.26M to 2.33M).
4. **ArtStation sends the header today on everything, but cannot be shown to have sent it then.**
   All 15 sampled CommonPool ArtStation URLs answered with `X-Robots-Tag: noai`, including company
   logos and shop product images. The December 2022 coverage describes ArtStation's NoAI tag as an
   opt-in HTML meta tag. A secondary source says ArtStation made NoAI the default for all projects
   on 2026-09-02. ArtStation's own pages refused every fetch.
5. **What the evidence supports.** The presence of millions of DeviantArt rows is not, on this
   evidence, proof that the collection ignored the header. It would be only if DeviantArt's CDN was
   sending `noai` on those URLs during the window. That is not established, and it is not true
   today. If that is later shown, the rows show the header was not honored for some part of the
   run. They still could not tell a collection that ignored it throughout from one that ran with
   the check off for part of the window, such as the mixed window raised by the parallel archival
   search (draft PR #1065, `docs/briefs/2026-11-15-datacomp-collection-archival-search.md`: check
   off in a December 2022 run, on from mid-January 2023), because the rows carry no download date.

## Method

### Step 1: which hosts sent the directive

Primary sources were fetched with `uv run python -m build.fetch_source` and read for where the
directive appears, which images, the default, and dates.

- **DeviantArt** announced `noai` and `noimageai` on 2022-11-11 with DreamUp. The journal post, as
  served today [S1], says: "When an artist declares that their content may not be used as input to
  AI models, an HTML tag with the noimageai directive is placed on the page and an HTTP header with
  the noai directive is sent when the image is directly downloaded from DeviantArt's servers." Its
  UPDATE line reads "now all deviations are automatically labeled as NOT authorized for use in AI
  datasets", and the artist setting is "selected by default". The developer section gives both
  forms: `<meta name="robots" content="noai">` and `X-Robots-Tag: noai`. The update is undated on
  the page. Coverage by 2022-11-16 reports the default flipped within days of launch [S8]. The
  Terms of Service, section 24, as served today [S3]: "Unless you actively give your consent ...
  DeviantArt will include a robots meta tag with the "noai" or "noimageai" directive in the head
  section of the HTML page associated with that Content on the Site, and will include an
  X-Robots-Tag HTTP response header with the "noai" directive when media files associated with that
  Content are downloaded from the Service." These are today's renderings. The November 2022 text
  and the ToS version in force during the window were to be read from the Wayback Machine, which
  was unreachable.
- **img2dataset PR #218**, which added the header check, was opened 2022-11-11 by an engineer at
  Wix (DeviantArt's parent), and a commenter signing as DeviantArt's Head of AI supported it on
  2022-11-22 [S5]. The author wrote that "the headers are already sent (or not) with the file
  download". The PR names no host or URL that sends them, and its benchmark does not say which
  images the check removed. Read through a summarizing fetcher only.
- **ArtStation** announced its NoAI tag in December 2022. Its magazine post, its 2026 update and
  its Terms of Service all returned HTTP 403 to `fetch_source` and to the web fetcher [S6]. The
  secondary coverage found describes, for 2022, an HTML "NoAI" meta tag on tagged projects, opt-in
  per project or per account. One 2026 secondary source says ArtStation turned NoAI on by default
  for every project on 2026-09-02 [S7]. No source found says ArtStation sent the header on image
  responses in the window. Under the task's rule, a host enters the experiment only on primary
  evidence of that, so ArtStation does not enter.
- **No other host** was found with primary evidence of the header on image responses in the window.

The archived check was to be the Wayback Machine, which keeps a capture's original headers as
`X-Archive-Orig-*` on `https://web.archive.org/web/<timestamp>id_/<url>`. The script's `wayback`
step lists captures of DeviantArt's CDN month by month from August 2022 to June 2023 through the
CDX API and HEADs a seeded sample of each month, then does the same for the exact URLs of a seeded
sample of CommonPool rows. It probes reachability first and stops if there is no answer.

### Step 2: the rows in CommonPool

The unfiltered pool is published as `mlfoundations/datacomp_xlarge`, so it was used rather than
DataComp-1B. Revision `2ee99257ee8af28386835355897ce5da07cca010` (head on 2026-11-15, last modified
2023-08-21) has 23,874 parquet files. Selection: sort the file names, then
`random.Random(20261115).sample(files, 60)`. For each drawn file the script reads only the `uid`,
`url` and `sha256` column chunks over HTTP range requests through `HfFileSystem` and pyarrow,
about 93 MB of each 129 MB file, so roughly 5.6 GB in all. Every row of each drawn file is
counted. The URL column alone is about 39 MB per file, roughly 0.9 TB pool-wide, which is why the
pool was sampled rather than scanned.

Host families:

| Family | Hosts |
|---|---|
| `deviantart_wixmp` | `images-wixmp-<hex>.wixmp.com`, DeviantArt's current image CDN |
| `deviantart_legacy_art` | `fc*`, `orig*`, `img*`, `pre*`, `th*`, `t*`, `s*` `.deviantart.net`. Today they redirect to the CDN |
| `deviantart_avatar` | `a.deviantart.net` (user avatars, not artworks) |
| `deviantart_other` | any other `deviantart.net` or `deviantart.com` host |
| `artstation_cdn` | `cdn.artstation.com`, `cdna.artstation.com`, `cdnb.artstation.com` |

Estimates: the pooled share is matched rows over rows read. The pool-wide total is the mean matched
rows per drawn file times the number of files, the expansion estimator for a simple random sample
of files. Both carry a file-bootstrap percentile 95% interval: 10,000 replicates resample the drawn
files with replacement, seed `20261115:file-bootstrap`. The same step ran on `mlfoundations/datacomp_1b`
at revision `086ebeee20d4cc3b3e7c05ae703fcf278ae3a759` (2,664 files, 30 drawn with the same seed),
because that is the corpus the scored checkpoints trained on.

### Headers today

`headers-now` sends HTTP HEAD only, never GET, to a seeded, family-stratified sample of matched
xlarge rows: 300 split across families in proportion, with at least 10 from each, so 310 in all
(seed `20261115:headers-now`). It follows redirects by HEAD and records `X-Robots-Tag`
on every hop. A second pass took 40 rows whose CDN token names the original-file download service,
`urn:service:file.download` (seed `20261115:headers-now:urn:service:file.download`). That covers
the ToS wording, "when media files ... are downloaded". Requests to one host were strictly
sequential, with at least 1 s between them (observed minimum 1.000 s). User-Agent
`Mozilla/5.0 (compatible; header-survey/0.1)`, no cookies or credentials, one retry after a
connection error only. 509 requests in all, on 2026-11-15 between 18:00 and 18:11 UTC.

## Results

### Wayback Machine (steps 1 and 3): not reachable

| When (UTC) | Probe | Result |
|---|---|---|
| 17:35:54 | `curl -I https://web.archive.org/` | CONNECT accepted, connection reset in the TLS handshake after 10 s |
| 17:36:17 | plain `http://web.archive.org/` | `403`, `x-block-reason: hostname_blocked`, "Blocked by egress policy" |
| 17:40, 17:43, 17:48 | `curl -I` | reset |
| 17:49:23, 17:52:15, 17:54:59, 17:57:50 | the script's `wayback` probe, spaced about 150 s | `ConnectionResetError(104)` each time; the step stopped as designed |
| 18:17:28 | `curl -I` | reset |

The agent proxy's status log recorded each as a tunnel closed mid-exchange for `web.archive.org:443`.
The plain-HTTP answer names the cause: the environment's egress policy blocks the host. The parallel
archival search reported the same. `archive.org`, Hugging Face and DeviantArt answered normally.
So **no archived header was read, the monthly shares were not measured, and no exact-URL match
exists.** Common Crawl's WARC records also keep original response headers, and its index answered
intermittently, but it was not used. It is a different archive, and the brief was to stop rather
than substitute.

### CommonPool rows on these hosts (step 2)

`mlfoundations/datacomp_xlarge`, 60 files, 32,147,132 rows (505,242 to 556,171 per file). The
expansion implies about 12.79B rows pool-wide, consistent with the documented 12.8B.

| Family | Rows in sample | Share | 95% interval | Pool-wide estimate | 95% interval |
|---|---:|---:|---|---:|---|
| DeviantArt, all | 45,865 | 0.143% | 0.141% to 0.144% | 18,249,684 | 18,050,734 to 18,448,236 |
| `deviantart_wixmp` | 23,773 | 0.074% | 0.073% to 0.075% | 9,459,277 | 9,333,938 to 9,590,982 |
| `deviantart_legacy_art` | 11,455 | 0.036% | 0.035% to 0.036% | 4,557,944 | 4,464,836 to 4,646,278 |
| `deviantart_avatar` | 10,565 | 0.033% | 0.032% to 0.033% | 4,203,814 | 4,120,254 to 4,283,394 |
| `deviantart_other` | 72 | <0.001% | | 28,649 | 22,680 to 34,617 |
| `artstation_cdn` | 2,336 | 0.007% | 0.007% to 0.008% | 929,494 | 890,898 to 969,682 |

Every drawn file holds DeviantArt rows (695 to 831 per file). Rows within a file are shuffled, so file-to-file variation
is small and the intervals are narrow. Of the 23,773 CDN rows, 96% address a resized rendition
(`/v1/fill`, `/v1/fit`, `/v1/crop`) rather than the original file. 17,721 carry a signed token: 16,610
for the image-operations service, 587 for file download, 524 for watermarking. The tokens carry no
date.

`mlfoundations/datacomp_1b`, 30 files, 15,776,477 rows:

| Family | Rows in sample | Share | Estimate in DataComp-1B | 95% interval |
|---|---:|---:|---:|---|
| DeviantArt, all | 25,831 | 0.164% | 2,293,793 | 2,255,431 to 2,332,510 |
| `deviantart_wixmp` | 15,887 | 0.101% | 1,410,766 | 1,386,967 to 1,435,541 |
| `deviantart_legacy_art` | 9,330 | 0.059% | 828,504 | 807,370 to 849,550 |
| `artstation_cdn` | 742 | 0.005% | 65,890 | 60,828 to 71,484 |

DeviantArt artworks survive the filtering into DataComp-1B at a higher rate than the pool average,
and avatars almost entirely do not.

### Headers today

| Family | HEADed | Final status | Any `X-Robots-Tag` | `noai`/`noimageai` |
|---|---:|---|---:|---:|
| `deviantart_wixmp` | 148 | 200: 115, 401: 26, 404: 7 | 0 | 0 |
| `deviantart_wixmp`, file-download token | 40 | 200: 33, 401: 6, 404: 1 | 0 | 0 |
| `deviantart_legacy_art` | 71 | 200: 70, 404: 1. All redirect to the CDN, after 1 or 2 redirects | 0 | 0 |
| `deviantart_avatar` | 66 | 200: 66 | 0 | 0 |
| `deviantart_other` | 10 | 200: 10 | 0 | 0 |
| `artstation_cdn` | 15 | 200: 15 | 15 | 15 (`noai`) |

The 2026-11-14 recoverability pilot is consistent with this: its two DeviantArt rows fetched with a
matching hash and no opt-out header. A spot check of the images on DeviantArt's own announcement
page found none on the CDN either, while the page's HTML carries
`<meta name="robots" content="...,noimageai"/>`. So today DeviantArt expresses the opt-out in page
HTML, and no CommonPool URL sampled on its image hosts gets it as a response header. That includes
the original-file download URLs. The DeviantArt download endpoint behind a login was not tested.

## Limitations

- **The window's headers were not observed.** Everything about December 2022 to March 2023 at the
  hosts rests on DeviantArt's own description, read as served today. The archive that would test it
  was blocked.
- **Today is not the window.** A header absent today may have been sent then. ArtStation's shows the
  reverse can also happen: present today, very likely absent then.
- **Headers can vary between requests.** They can vary by URL form (rendition or original), token,
  user agent or time, so even an archived capture of an exact URL would show what one client was
  served once. No stability check across captures was possible.
- **The rows carry no download date.** A collection that ran with the check off for part of the
  window and on for the rest leaves the same rows as one that ignored it throughout. Under the mixed
  window the archival search raised, present rows fit the check-off portion and say nothing about
  the rest.
- **Absence would have been weak too.** Had the rows been rare, other filters (NSFW, deduplication,
  face blurring, dead links) could explain it. How often Common Crawl pages linked these hosts in
  2014 to 2022, the baseline that would make a deficit measurable, was not obtainable cheaply and
  was not estimated.
- **robots.txt at image hosts is not tested.** img2dataset never read it, so this experiment says
  nothing about it.
- **Sampling.** The pool estimates are from 60 of 23,874 files and DataComp-1B's from 30 of 2,664.
  The expansion estimator assumes a simple random sample of files, which the seed gives.
  Sub-host families are as defined above. A DeviantArt image served from another domain, such as
  a proxy, mirror or hotlinking CDN, is not counted.
- **Secondary and summarized sources.** The PR #218 quotes and every ArtStation statement come
  through a summarizing fetcher or secondary coverage, without a digest. Treat them as leads.

## Established, inferred and unknown

| Finding | Status | What would close it |
|---|---|---|
| CommonPool holds about 18.2M rows on DeviantArt image hosts (95% interval 18.1M to 18.4M), 9.5M of them on its current CDN, and DataComp-1B about 2.29M | Established, from a seeded file sample with recorded revision | A full scan would narrow the intervals |
| DeviantArt says it sends `X-Robots-Tag: noai` on direct image downloads for all content unless the artist opts in, a default adopted within days of 2022-11-11 | Established as DeviantArt's statement, read today [S1, S3] | The November 2022 page and ToS versions, from an archive |
| DeviantArt's CDN sent the header on the image URLs CommonPool links, during December 2022 to March 2023 | Unknown. Not observed; the archive was unreachable | Wayback `X-Archive-Orig-X-Robots-Tag` on captures of those URLs in the window: rerun `wayback` from a network that reaches web.archive.org |
| DeviantArt's CDN sends no `X-Robots-Tag` on CommonPool URLs today, file-download URLs included | Established for the 335 URLs sampled, 2026-11-15 | Closed for today |
| ArtStation's CDN sends `X-Robots-Tag: noai` on every image today | Established for the 15 URLs sampled | Closed for today |
| ArtStation sent it on image responses during the window | Unknown, and unlikely on the secondary evidence: an opt-in HTML meta tag in 2022, default-on only from 2026-09-02 | ArtStation's own 2022 announcement, or archived headers |
| The collection did not honor X-Robots-Tag for at least part of the window | Unknown. It follows from the row counts only if the host is shown to have sent the header in the window | The archived headers above, or the run's config or `_stats.json` |
| The collection honored X-Robots-Tag throughout | Unknown. Nothing here bears on it, and present rows would not refute it unless the header is shown | As above |
| This experiment can tell a whole-window failure from a part-window one | Established that it cannot: rows carry no download date | The run's per-shard logs or configs |

## Sources

Map-side claims cite `main` at `632c0612`. Everything below was read 2026-11-15. Rows with a
digest were fetched with `uv run python -m build.fetch_source`. Rows marked "summarizing fetcher"
were read through a web fetcher that returns a summary, so their quotes are as it returned them.

| # | URL | Status | content_sha256 | What it gave |
|---|---|---|---|---|
| S1 | https://www.deviantart.com/team/journal/A-New-Standard-for-Opting-Out-of-AI-Datasets-934500371 | 200 | `e5f72a2e8443152ff1c163075ce0a112df1eac2fa3412662c3428e2d7110f8ca` | Published 2022-11-11; the header "is sent when the image is directly downloaded from DeviantArt's servers"; default on; meta tag and header forms. Page HTML carries `noimageai` |
| S2 | https://www.deviantart.com/team/journal/Create-AI-Generated-Art-Fairly-with-DreamUp-933537821 | 200 | `e534b57a7f03c169a3755946eab7b5df2392603194c446cae9406ba6cbf093f3` | DreamUp launch, 2022-11-11; "we have enacted 'noai'"; all deviations labeled not authorized |
| S3 | https://www.deviantart.com/about/policy/service/ | 200 | `1cb2b1ec41c5f201619ba68c375e587f3e9528faba03fb0c3ce9fa778adb1b73` | Section 24: meta tag on the page, `X-Robots-Tag: noai` "when media files associated with that Content are downloaded from the Service" |
| S4 | img2dataset commit `eb672d55` (2022-11-24), read from a local clone of https://github.com/rom1504/img2dataset | n/a | n/a | #218 by a Wix engineer: `disallowed_header_directives` and `user_agent_token`, the `laion-art-noai` example |
| S5 | https://github.com/rom1504/img2dataset/pull/218 | summarizing fetcher | none | Opened 2022-11-11; "the headers are already sent (or not) with the file download"; a comment signed by DeviantArt's Head of AI, 2022-11-22; no host named |
| S6 | https://magazine.artstation.com/2022/12/noli-tag/, https://magazine.artstation.com/2026/09/ai-updates-from-artstation/, https://www.artstation.com/tos | 403 to `fetch_source` (6 attempts each) and to the web fetcher | none | Not read |
| S7 | https://www.banthebots.org/explainers/deviantart-alternatives | summarizing fetcher | none | Secondary: ArtStation NoAI default for every project from 2026-09-02, citing S6's 2026 post |
| S8 | https://www.plagiarismtoday.com/2022/11/16/lessons-from-deviantarts-ai-debacle/, https://techcrunch.com/2022/11/11/deviantart-provides-a-way-for-artists-to-opt-out-of-ai-art-generators | search results only | none | Secondary: the 2022-11-11 launch and the default flipping to opted out within days |
| S9 | https://huggingface.co/datasets/mlfoundations/datacomp_xlarge at `2ee99257ee8af28386835355897ce5da07cca010` | 200 | n/a (pinned revision) | 23,874 parquet files; `uid`, `url`, `sha256` columns of the 60 drawn files |
| S10 | https://huggingface.co/datasets/mlfoundations/datacomp_1b at `086ebeee20d4cc3b3e7c05ae703fcf278ae3a759` | 200 | n/a (pinned revision) | 2,664 parquet files; the same columns of the 30 drawn files |
| S11 | https://web.archive.org/ | reset in the TLS handshake (HTTPS); 403 `hostname_blocked` (HTTP) | none | Unreachable, 17:35 to 18:17 UTC |
| S12 | https://github.com/rom1504/img2dataset/issues/298 | summarizing fetcher | none | 2023-04-24: the header check runs after the GET, not a defect in the check's logic; context only |
