# OpenCLIP hash mismatches against DataComp's published embeddings, 2026-11-14

This brief follows up the OpenCLIP recoverability pilot
(`docs/briefs/2026-11-14-openclip-recoverability-pilot.md`, #1059). That pilot sampled 1,000
DataComp-1B rows. For 265 of them the URL still served an image, but the image's sha256 differed
from the one DataComp published. A hash cannot tell a re-encoded or resized copy of the same
picture from a different picture. Reviewing #1059, the maintainer ruled against a larger random
sample for now and asked first for a perceptual comparison of those 265 rows against DataComp's
published embeddings, with no image content kept (R-2026-11-14-g). This brief reports that
comparison.

It changes no score, hold, value, rubric or ruling, and it draws no scoring conclusion.
`openclip.openness` stays on hold at its recorded provisional value. Like the other records in
`docs/briefs/`, this brief describes the state on its date and gets refreshed by a new brief, not
edited.

The script is `build/hash_mismatch_embeddings.py`. It reuses the pilot's fetcher, changed only by a
hook that hands the body to a callback while it is still in memory. The machine-readable result
is `docs/briefs/2026-11-14-openclip-hash-mismatch-embeddings.json`. For each sample it gives the
uid, shard and row, the re-fetch outcome, the cosine against the published embedding for each
model, and the band. It also carries every distribution, threshold and interval quoted here. It
holds no URLs, no image content and no embeddings.

## The short answer

Of the 265 hash-mismatched rows, 243 served an image that DataComp's own embedding model scores as
the same picture: 91.7%, with a shard-bootstrap 95% interval of 88.6% to 94.7% (approximate; about
235 to 251 rows). 6 are different pictures by this test (2.3%, 0.8% to 4.1%). 5 fall between the
bands (1.9%, 0.4% to 3.6%). 10 more served one identical placeholder file that neither decoder
could read. On this re-fetch, 1 row was excluded by a proxy error.

The split follows pixel dimensions. Of the 226 rows the pilot found at their original dimensions,
221 are in the same band, 4 are indeterminate and none is different. Of the 39 at other
dimensions, 22 are the same, 1 is indeterminate and 6 are different. The other 10 are the
placeholder.

The pipeline was checked before any mismatched row was fetched. The 44 control rows whose bytes
still matched their published hash reproduced their published ViT-L/14 embedding to a cosine of at
least 0.9995 (median 1.0000).

Read with the pilot: 586 of the 1,000 sampled rows (58.6%, 55.0% to 62.2%) either returned the
published bytes or, on this evidence, returned the same picture in different bytes. This is
evidence of visual identity, not proof of it. The [limitations](#limitations) say what it cannot
show.

## What DataComp publishes, and what it was computed on

Each `<shard>.parquet` in
[`mlfoundations/datacomp_1b`](https://huggingface.co/datasets/mlfoundations/datacomp_1b) at
revision `086ebeee20d4cc3b3e7c05ae703fcf278ae3a759` has a `<shard>.npz` beside it of about 3.2 GB.
Each is an uncompressed zip with five arrays, one row per parquet row in the same order:

| Member | Shape and type | What it is |
|---|---|---|
| `b32_img` | rows × 512, float16 | CLIP ViT-B/32 image embedding |
| `b32_txt` | rows × 512, float16 | CLIP ViT-B/32 text embedding |
| `l14_img` | rows × 768, float16 | CLIP ViT-L/14 image embedding |
| `l14_txt` | rows × 768, float16 | CLIP ViT-L/14 text embedding |
| `dedup` | rows × 256, float32 | the evaluation-set deduplication descriptor |

The DataComp paper (arXiv 2304.14108, Table 8 and Appendix H) names the CLIP features as ViT-B/32
and ViT-L/14 image and text features, computed in step 2 of pool construction on the images
downloaded in step 1. The repository README says they come from "the trained OpenAI CLIP models".
In step 1, img2dataset capped each image's longest side at 512 pixels. The `dedup` descriptor
comes from Yokoo's copy-detection model (Appendix F). It would suit this question well, but
reproducing it would mean adopting a third model, so it was not used. The stored image embeddings
are unit vectors to within float16 rounding (norms 0.9995 to 1.0005).

Because the arrays are stored uncompressed, any one row is a fixed-size slice at a computable
offset. The script reads only the rows it needs, with HTTP range requests, and never downloads a
whole `.npz`. It read both image embeddings for all 1,000 pilot rows. Each row was checked against
the parquet's row count, and each sampled row's uid against the parquet.

**Model and preprocessing.** The models are `open_clip` `ViT-L-14-quickgelu` and
`ViT-B-32-quickgelu` with `pretrained=openai`, which are OpenAI's weights with their QuickGELU
activation, under the standard OpenAI transform (bicubic resize to 224, center crop, OpenAI
normalization). Before that transform, the script rebuilds what DataComp's download stored, using
img2dataset 1.41's resizer with the arguments in DataComp's `download_upstream.py`:

1. Decode with OpenCV `IMREAD_UNCHANGED`, with no EXIF rotation, and matte any alpha channel on
   white.
2. Cap the longest side at 512 with `INTER_AREA`, only when it is larger.
3. Re-encode as JPEG quality 95 only if step 2 resized the image, an alpha matte was applied, or
   Python's `imghdr` did not recognize the file as JPEG. Otherwise keep the downloaded bytes
   unchanged. This is img2dataset's `skip_reencode`.

The control found step 3; nothing published describes it. A first control run re-encoded every
image. Images over 512 pixels then reproduced their stored embedding exactly, but smaller JPEGs
missed it by a re-encode (ViT-L/14 cosine as low as 0.9724), and the plain downloaded bytes showed
the opposite pattern. The `imghdr` reading that recognizes JPEG only by a JFIF or Exif marker, as
Python 3.10 and earlier did, fits better than the later reading that also accepts a bare
`FF D8 FF DB` start (control minimum 0.9995 against 0.9867).

## Method

**Samples.** All 265 rows the pilot recorded as `changed_content`: 226 `same_dims` and 39
`different_dims`. Nothing was added to the random sample.

**Control.** 50 of the pilot's 343 `hash_match` rows, drawn with
`random.Random("20261114:control").sample(...)` over the hash-matched rows in manifest order. The
control does two jobs:

- **Validation.** A control that still matches its published hash must reproduce its stored
  embedding.
- **Calibration.** Each control image was transformed in memory the ways a host might serve the
  same picture, passed through the same view as a fetched image, and compared with its stored
  embedding.

**Re-fetch.** Only URLs the pilot had already sampled were re-fetched, under the pilot's rules and
code: robots.txt per RFC 9309 with 401 and 403 as no rules (R-2026-11-14-g); `X-Robots-Tag`
`noai`, `noimageai`, `noindex` and `noimageindex`, including directives addressed to img2dataset,
checked on every redirect hop; at most 8 requests in flight and 1 per host, with at least 1 s
between requests to a host; 20 s timeouts; one retry, only after a connection error or timeout; no
cookies, credentials or referer; the pilot's plain User-Agent. Observed: at most 8 in flight
(control stage) and 7 (mismatch stage); minimum same-host gap 1.000 s. Each body was hashed and
embedded while held in memory, then dropped. Decoding and embedding ran on one worker thread, so
at most one decoded image existed at a time. Nothing was written to disk except embeddings and
per-sample records, in a scratch cache outside the repository.

**Comparison.** The cosine between the fetched image's embedding and the row's stored embedding.
ViT-L/14 is primary. ViT-B/32 is reported as a second opinion and does not set any band.

**Null.** Each fetched image's embedding against the stored embeddings of the other 999 pilot rows:
302,697 pairs over the 303 images re-fetched and embedded, mismatched and control together. No
extra fetch was needed. A single seeded random pairing (`random.Random("20261114:null-pairing")`)
is reported beside it, along with two harder nulls: other rows on the same host, and the same host
type.

**Bands.** Thresholds come from fixed quantiles of the control and the null. They were not read
off the mismatch distribution.

- *Same*: cosine at or above the 1st percentile of the calibrated control cosines for the matching
  family. A fetched image at the original dimensions uses the `reencode` family (as served, PNG,
  JPEG at qualities 90, 75, 50 and 30, WebP 80). One at other dimensions uses the `resize` family
  (downscaled to one half and one quarter, then JPEG 85).
- *Different*: cosine at or below the 99th percentile of the null.
- *Indeterminate*: between the two. Where a family's 1st percentile falls inside the null, as the
  `resize` family's does, "same" also requires the cosine to be above the null's 99th percentile.

Rows with no comparison are counted separately: *undecodable* (an image came back that the
decoders could not read) and *not re-fetched*.

**Intervals.** Shard bootstrap, using the pilot's `shard_bootstrap`: 10,000 replicates resample
the 50 drawn files with replacement, keep each file's rows and recompute the share; percentile 95%
interval; seed `20261114:embedding-band-bootstrap`. The pilot is a two-stage sample (50 files, then
20 rows in each), and with 50 clusters these intervals are approximate. Count intervals are the
share interval times 265.

## Results

### Control validation

44 of the 50 controls returned bytes that still matched their published hash. The other six are
listed under [re-fetch outcomes](#re-fetch-outcomes). Cosine against the stored embedding:

| View | ViT-L/14 min | 5th pct | median | ViT-B/32 min | median |
|---|---:|---:|---:|---:|---:|
| DataComp view (img2dataset with `skip_reencode`, marker-only `imghdr`) | 0.9995 | 0.9997 | 1.0000 | 0.9994 | 1.0000 |
| Same, with the later `imghdr` reading | 0.9867 | 0.9996 | 1.0000 | 0.9981 | 1.0000 |
| Always re-encode | 0.9724 | 0.9818 | 0.9966 | 0.9679 | 0.9988 |
| Downloaded bytes, no img2dataset step | 0.9528 | 0.9655 | 0.9997 | 0.9652 | 0.9999 |

The DataComp view reproduces the published embeddings to float16 precision. Everything below uses
it.

### Calibration: how far a known-same image drifts

ViT-L/14 cosine of each control, transformed in memory, against its stored embedding (44 controls):

| Variant | Family | Min | 1st pct | 5th pct | Median |
|---|---|---:|---:|---:|---:|
| as served | reencode | 0.9995 | 0.9996 | 0.9997 | 1.0000 |
| PNG (lossless, but forces the q95 re-encode) | reencode | 0.9724 | 0.9757 | 0.9818 | 0.9966 |
| JPEG q90 | reencode | 0.9522 | 0.9554 | 0.9614 | 0.9931 |
| JPEG q75 | reencode | 0.9047 | 0.9072 | 0.9404 | 0.9837 |
| JPEG q50 | reencode | 0.7979 | 0.8285 | 0.8814 | 0.9687 |
| JPEG q30 | reencode | 0.8105 | 0.8317 | 0.8725 | 0.9422 |
| WebP q80 | reencode | 0.8704 | 0.8880 | 0.9222 | 0.9739 |
| half size, JPEG q85 | resize | 0.6705 | 0.7228 | 0.7960 | 0.9180 |
| quarter size, JPEG q85 | resize | 0.5257 | 0.5445 | 0.6189 | 0.8225 |
| JPEG q10 | extreme (not used) | 0.6285 | 0.6534 | 0.6908 | 0.8835 |
| eighth size, JPEG q85 | extreme (not used) | 0.3513 | 0.3667 | 0.4024 | 0.7249 |
| center crop to 80% | geometry (not used) | 0.7951 | 0.7953 | 0.8235 | 0.9390 |
| padded to a white square | geometry (not used) | 0.7143 | 0.7220 | 0.7968 | 0.9352 |

Many sampled images are small: the median longest side is 425 pixels among the controls and 324
among the mismatched rows. Downscaling a small image and letting CLIP upscale it to 224 costs a lot
of similarity, which is why the `resize` family reaches into the null. Five controls served bytes
that differed from what the pilot hashed about twenty hours earlier, at unchanged dimensions. Their cosines were 0.956, 0.975, 0.997, 1.000 and
1.000: real cases of a host re-serving the same picture in new bytes, and all inside the `reencode`
range.

### Null

| ViT-L/14 null | Pairs | Median | 95th pct | 99th pct | 99.9th pct | Max |
|---|---:|---:|---:|---:|---:|---:|
| All other pilot rows | 302,697 | 0.429 | 0.586 | 0.651 | 0.731 | 0.935 |
| One random pairing per image | 303 | 0.428 | 0.591 | 0.661 | | 0.695 |
| Same host | 1,414 | 0.479 | 0.643 | 0.703 | | 0.830 |
| Same host type (named types only) | 15,655 | 0.452 | 0.610 | 0.676 | | 0.868 |

The few null pairs above 0.85 are distinct rows whose pictures are near-duplicates of each other,
which is expected in a web corpus.

### Thresholds

| Model | Same, original dimensions | Same, other dimensions | Different |
|---|---|---|---|
| ViT-L/14 (sets the bands) | ≥ 0.8692 | ≥ 0.5638, so in practice > 0.6509 | ≤ 0.6509 |
| ViT-B/32 (second opinion) | ≥ 0.8972 | ≥ 0.6013, so in practice > 0.6992 | ≤ 0.6992 |

### Distribution of the mismatched rows

ViT-L/14 cosine for the 254 mismatched rows that were re-fetched and decoded, beside the null:

| Cosine | Mismatched rows | Null pairs |
|---|---:|---:|
| below 0.3 | 1 | 30,791 |
| 0.3 to 0.4 | 0 | 86,178 |
| 0.4 to 0.5 | 1 | 114,963 |
| 0.5 to 0.6 | 4 | 59,787 |
| 0.6 to 0.7 | 1 | 10,194 |
| 0.7 to 0.8 | 2 | 757 |
| 0.8 to 0.85 | 3 | 21 |
| 0.85 to 0.9 | 10 | 5 |
| 0.9 to 0.95 | 33 | 1 |
| 0.95 to 0.98 | 46 | 0 |
| 0.98 to 0.99 | 27 | 0 |
| 0.99 to 1.0 | 126 | 0 |

| Rows | n | Min | 5th pct | 25th pct | Median | 75th pct |
|---|---:|---:|---:|---:|---:|---:|
| All | 254 | 0.267 | 0.855 | 0.957 | 0.990 | 0.998 |
| Original dimensions | 225 | 0.826 | 0.903 | 0.967 | 0.993 | 0.999 |
| Other dimensions | 29 | 0.267 | 0.496 | 0.702 | 0.928 | 0.980 |

The distribution is strongly bimodal. Most mismatched rows sit where re-encodes of known-same
images sit, and a small group sits in the bulk of the null.

### Bands

Shares of the 265 mismatched rows, with shard-bootstrap intervals (approximate):

| Band | Count | Share | 95% interval | Count interval | Share of all 1,000 pilot rows |
|---|---:|---:|---|---|---|
| Same | 243 | 91.7% | 88.6% to 94.7% | 235 to 251 | 24.3% (21.9% to 26.8%) |
| Indeterminate | 5 | 1.9% | 0.4% to 3.6% | 1 to 9 | 0.5% (0.1% to 1.0%) |
| Different | 6 | 2.3% | 0.8% to 4.1% | 2 to 11 | 0.6% (0.2% to 1.1%) |
| Undecodable (one placeholder file) | 10 | 3.8% | 1.8% to 5.9% | 5 to 16 | 1.0% (0.5% to 1.6%) |
| Not re-fetched (proxy error) | 1 | 0.4% | 0.0% to 1.2% | 0 to 3 | 0.1% (0.0% to 0.3%) |

By the pilot's dimension code:

| Pilot code | Rows | Same | Indeterminate | Different | Undecodable | Not re-fetched |
|---|---:|---:|---:|---:|---:|---:|
| `same_dims` | 226 | 221 | 4 | 0 | 0 | 1 |
| `different_dims` | 39 | 22 | 1 | 6 | 10 | 0 |

One `different_dims` row came back at its original dimensions this time and was banded with the
`reencode` family. The other 21 `different_dims` rows in the same band are at other dimensions now
as well. Nine are larger than the original (1.4 to 7.8 times on the longest side), meaning the host
serves a bigger version of what was once a thumbnail. Six are within 2% of the original longest
side, so the aspect ratio or a few pixels changed. Six are smaller. One of the smaller is 0.5% of
the original size with a cosine of 0.70: above the null's 99th percentile, below its 99.9th. It is
the weakest "same" in the set, and the sensitivity table below moves it.

By host type (the pilot's heuristic suffix list):

| Host type | Rows | Same | Indeterminate | Different | Undecodable | Not re-fetched | Median cosine |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 107 | 103 | 2 | 2 | 0 | 0 | 0.989 |
| e-commerce CDNs | 97 | 79 | 3 | 4 | 10 | 1 | 0.978 |
| site builders and blog hosts | 29 | 29 | 0 | 0 | 0 | 0 | 0.997 |
| self-hosted WordPress | 17 | 17 | 0 | 0 | 0 | 0 | 0.994 |
| stock photo sites | 10 | 10 | 0 | 0 | 0 | 0 | 0.971 |
| cloud storage and CDNs | 5 | 5 | 0 | 0 | 0 | 0 | 0.998 |

E-commerce CDNs, where the pilot found almost no byte-exact matches, mostly serve the same picture
in new bytes: eBay 23 rows, the Amazon image hosts 29, Walmart 4, AliExpress 4. Every row outside
the same band is on an e-commerce CDN or an "other" host.

**ViT-B/32 agreement.** Over the 254 banded rows, the two models agree on 245 (239 same, 5
different, 1 indeterminate). In the remaining 9, one model calls a row indeterminate and the other
gives a band. No row is "same" under one model and "different" under the other. B/32 calls 3 of the
4 indeterminate `same_dims` rows "same".

**Threshold sensitivity** (ViT-L/14; counts of the 265; nothing refetched):

| Same at control quantile | Different at null quantile | Same | Indeterminate | Different |
|---|---|---:|---:|---:|
| minimum | 99th | 247 | 2 | 5 |
| **1st (used)** | **99th** | **243** | **5** | **6** |
| 5th | 99th | 238 | 9 | 7 |
| 1st | 95th | 244 | 4 | 6 |
| 1st | 99.9th | 241 | 7 | 6 |
| minimum | 99.9th | 245 | 4 | 5 |

The same band holds between 238 and 247 of 265 rows across these choices.

### Placeholders

Two groups of rows served byte-identical files for different uids:

- **10 rows on `render.fineartamerica.com`** (10 of the 11 that host had in the pilot) served one
  PNG. OpenCV could not decode it, and Pillow reported a broken data stream. These are the 10
  undecodable rows. A single file served for 10 different pictures can be at most one of them.
  These rows are not banded, but they are not evidence of the same picture.
- **5 rows on `i.ebayimg.com`** served one JPEG at dimensions other than the originals. Four are
  in the different band (cosines 0.27 to 0.54) and one is indeterminate (0.605; B/32 calls it
  different). This looks like a listing-gone image.

Together that is 15 rows. The pilot counted 16 rows sharing a fetched hash; it did not keep the
hashes, so the two counts cannot be matched row by row.

### Re-fetch outcomes

This was a second fetch of rows the pilot fetched about twenty hours earlier, and some outcomes
moved:

| Group | Outcome now | Rows |
|---|---|---:|
| Mismatched (265) | image served, hash still differs, original dimensions | 224 |
| | image served, hash still differs, other dimensions | 38 |
| | **hash now matches the published sha256** (`i.etsystatic.com`, `sc02.alicdn.com`; both cosine 1.000) | 2 |
| | **excluded: proxy error** (`images-na.ssl-images-amazon.com`) | 1 |
| Control (50) | hash still matches | 44 |
| | **hash now differs** at the same dimensions (cosines 0.956 to 1.000; all in the same band) | 5 |
| | **failed: HTTP 403** | 1 |

No robots.txt or `X-Robots-Tag` opt-out excluded a row this time. The two rows whose hash matches
again count in the same band, by hash as well as by embedding.

## Deviations from the plan

- **The preprocessing was corrected after the first control run.** That run re-encoded every
  image, and the control showed the `skip_reencode` behavior described above. The pipeline was
  fixed, and the control stage was rerun before any mismatched row was fetched.
- **Control URLs were requested more than once.** Two earlier control-stage attempts were killed
  for memory during their first fetches: torch's no-grad switch applies per thread, so fetch
  threads calling the model recorded autograd state. Fewer than 25 and fewer than 10 control
  samples, respectively, had been fetched. The third attempt completed all 50 with the wrong
  preprocessing (128 requests), and the fourth is the one reported. The 50 control URLs were
  therefore fetched up to four times, under the same rules each time. Each of the 265 mismatched
  URLs was fetched once.
- **The `dedup` embedding was not used.** It is a copy-detection descriptor and would suit the
  question, but reproducing it would mean adopting a third model.
- **Bands are split by dimension class.** A single family pooling re-encodes and resizes would have
  put its 1st percentile inside the null and left no indeterminate band. Calibrating each class by
  the transformation that fits it is the narrower and more defensible test.
- **Undecodable rows are reported apart from the three bands**, since no cosine exists for them.

## Limitations

- **Similarity is evidence, not proof.** A cosine near 1 means the two images look the same to
  CLIP. A near-duplicate can score that high: another photo from the same shoot, the same product
  shot on a different background, an image with a small overlay, watermark or price sticker
  changed. Some null pairs reach 0.935. A different picture of the same thing can score in the
  indeterminate range.
- **It cannot tell which bytes trained the model.** "Same picture" is not "same bytes". A
  reconstruction from today's web would train on today's re-encode or resize. Whether that counts
  as faithful reconstruction is the maintainer's question, and this brief does not answer it.
- **Small images limit the resize test.** The resize calibration covers downscales to one half and
  one quarter. Upscaled cases (a thumbnail now served larger) and extreme downscales lie outside
  the calibrated range and rely on the null threshold alone.
- **The calibration is synthetic.** Pillow re-encodes are a stand-in for whatever each CDN does. The
  five controls whose bytes changed overnight are the only observed cases, and they agree with it.
- **The model reproduction rests on inference.** The `skip_reencode` setting, the marker-only
  `imghdr` reading and the OpenCV and Pillow versions are inferred from the control, which they
  reproduce to float16 precision. They are not documented by DataComp.
- **The sample is still 265 rows** in a two-stage design. Per-host figures say little
  individually, and the intervals are approximate.
- **Timing.** The re-fetch ran on the same day as the pilot, from the same network. Content behind
  a URL changes, and it changed for 7 of the 315 rows within the day (5 controls, 2 mismatches).
- **Not covered:** the rows the pilot did not get an image for (gone, opted out, access-controlled
  or transient), the original collection's opt-out configuration, and LAION-2B.

## Reproducing

The heavy dependencies are an ephemeral overlay and are not in `pyproject.toml`:

```
uv run --index pytorch-cpu=https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match \
  --with torch --with torchvision --with open_clip_torch --with opencv-python-headless \
  python -m build.hash_mismatch_embeddings --only control --cache <scratch>/control.npz
# then the same with --only mismatch --cache <scratch>/mismatch.npz, and:
uv run python -m build.hash_mismatch_embeddings --analyze <scratch>/control.npz <scratch>/mismatch.npz \
  --out docs/briefs/2026-11-14-openclip-hash-mismatch-embeddings.json
```

The run reported here used torch 2.15.0 (CPU), open_clip 4.2.2, OpenCV 5.0.0, Pillow 13.0.0,
NumPy 2.4.6 and Python 3.13.18. The control stage ran from 21:26 to 21:33 UTC and the mismatch
stage from 21:34 to 21:41 UTC, 677 requests to image hosts in all, robots.txt included. `--analyze`
recomputes everything above from the two caches without a network or a model, and reproduces the
JSON byte for byte.

## Sources

| Source | Used for |
|---|---|
| `https://huggingface.co/datasets/mlfoundations/datacomp_1b` at `086ebeee20d4cc3b3e7c05ae703fcf278ae3a759` | Parquet rows (uid, url, sha256, original dimensions, face boxes) and the `.npz` members, read by range request |
| Gadre et al., "DataComp: In search of the next generation of multimodal datasets", arXiv 2304.14108 (Section 3.2, Appendices F and H, Table 8) | What the `.npz` holds and when it was computed: ViT-B/32 and ViT-L/14 features on the step-1 download, longest side capped at 512 |
| `https://raw.githubusercontent.com/mlfoundations/datacomp/main/download_upstream.py` and `README.md` | img2dataset arguments (512, `keep_ratio_largest`, resize only if bigger, jpg); "features extracted by the trained OpenAI CLIP models" |
| img2dataset 1.41.0 from PyPI, `img2dataset/resizer.py` | The resize, alpha matte, `skip_reencode` and quality-95 encode logic reproduced here |
| `docs/briefs/2026-11-14-openclip-recoverability-pilot.json` | The sample, the per-row outcomes and the shard bootstrap |
| `docs/rulings/log.yaml`, R-2026-11-14-g | The request for this comparison and the robots.txt reading |
| `docs/briefs/2026-11-14-openclip-hash-mismatch-embeddings.json` | Every figure above |
