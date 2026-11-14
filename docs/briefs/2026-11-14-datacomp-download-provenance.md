# DataComp CommonPool download provenance, 2026-11-14

This brief answers one evidence question held open on `openclip.openness` in
`sources/verification_queue.yaml`: which downloader version and which opt-out settings fetched the
images in DataComp's CommonPool, the pool DataComp-1B was filtered from, during the 2022-2023
collection. Element 4 of R-2026-11-13-d (`docs/reference/openness.md`, "A web-crawl corpus is open
when its release documents a basis for reuse") asks how publisher opt-outs were honored "during the
collection that produced the scored corpus", and says documentation of a later tool does not show
that. This brief records what the primary sources say about the original collection. It changes no
score, hold, rubric or ruling and proposes none. Like the other records in `docs/briefs/`, it
describes what its sources said on the date above and gets refreshed by a new brief, not edited.

Map-side claims cite `main` at `da554d5f`. Outside sources are listed under [Sources](#sources),
all read today. No dataset image was fetched for this brief.

## The short answer

1. **When and by whom.** The DataComp paper's datasheet says "Data was downloaded between December
   2022 and March 2023", by the paper's own authors on "100s of AWS CPU nodes". Its contributions
   list credits "Data collection" to Romain Beaumont (LAION) and Vaishaal Shankar (Apple). The tool
   was img2dataset, which Beaumont maintains. The paper gives no version and no settings.
2. **The DataComp repository's pin.** The repository's first commit (2023-04-27, the day the paper
   went up) pins `img2dataset==1.40.0`, and every later revision keeps that pin. Its download script
   never passes `disallowed_header_directives` or `user_agent_token`, so it runs with 1.40.0's
   defaults. But that script is the tooling participants use to re-download the published index.
   The repository was created after the collection ended, and the collection code is not in it.
   The pin dates the tool participants got, not the tool that built the pool.
3. **img2dataset's opt-out handling.** X-Robots-Tag handling arrived in 1.34.0 (PyPI 2022-11-25)
   and was off unless configured. It became the default in 1.39.0 (PyPI 2022-12-19). From then on,
   images whose response carries an un-scoped `noai`, `noimageai`, `noindex` or `noimageindex`
   directive are dropped. img2dataset has never checked robots.txt; the issue asking for it has
   been open since 2021. So the change of default fell inside the collection window. A collection
   that started in early December on a release before 1.39.0, or that passed an empty list, would
   not have honored the header.
4. **Opt-out at the image host, then and later.** The paper says nothing about X-Robots-Tag, `noai`
   or any opt-out list. Its one statement on opt-outs is that, "Following our usage of Common Crawl
   and https://github.com/rom1504/img2dataset for download images, we respect robots.txt files".
   img2dataset does not read robots.txt, so whatever robots.txt checking happened was CCBot's, at
   page-crawl time, between 2014 and 2022. The data funnel puts every failure into one bucket
   ("Dead links and other download errors: 23.2B"), and the released metadata has no download-status
   field. No Spawning or other opt-out-list filtering is documented. No retroactive removal is on
   record: the DataComp-1B metadata on Hugging Face has not changed since 2023-08-21, and the
   maintainers reported no removals in the one public thread that asked (December 2023).
5. **Still unknown.** Which img2dataset version or versions ran the December 2022 to March 2023
   collection, what `disallowed_header_directives` value it used, and how many images it dropped
   for an X-Robots-Tag directive. Nothing published answers these. The run's own logs would.

## 1. When the pool was downloaded, and by whom

The datasheet in the paper's appendix gives the window and the method. The same wording is in v1
(2023-04-27) and v5 (2023-10-20) of arXiv 2304.14108 [S1, S2]:

> Q26 Over what timeframe was the data collected? ... Data was downloaded between December 2022 and
> March 2023. The urls are collected from Common Crawl dumps between 2014 and 2022. ...
> Additionally, future users of COMMONPOOL and its subsets will have to download data themselves
> using our tooling.

> Q23 ... We iterate on the LAION-5B data collection process, making an effort to emphasize safety.
> We ran python based processing scripts to parse Common Crawl dumps, download images, filter our
> NSFW content, deduplicate samples against downstream tests sets, blur faces, and compute CLIP
> features. We ran processes on 100s of AWS CPU nodes for Common Crawl parsing and data download.
> Other steps were run on one of StabilityAI's GPU cluster.

> Q25 Who was involved in the data collection process ...? The researching authors were involved in
> the data collection as an open source effort.

Appendix B, Contributions [S2]: "Candidate pool lead. Vaishaal Shankar" and "Data collection.
Romain Beaumont, Vaishaal Shankar". The author affiliations list Beaumont under LAION (6) and
Shankar under Apple (4). Q2 lists LAION among the creating institutions, and Q3 says "Compute for
this research was generously provided by StabilityAI."

On the downloader, Section 3.2 [S2]: "We attempt to download ∼40B samples using img2dataset [5]
resulting in ∼16.8B image-text pairs." Reference [5] is the bare repository URL,
`https://github.com/rom1504/img2dataset`, with no version. Appendix H, step 1: "We use img2dataset [5]
to obtain ∼16.8B downloaded samples. ... During this step we also resize images such that their
largest dimension does not exceed 512 pixels." Q37 lists img2dataset among the software used,
again with no version.

On failure rates, Q7 [S2]: "Of these samples we attempt to download ∼40B samples. Due to various
download issues, such as dead links and throttling, we are able to successfully download ∼16.8B
samples." Figure 7, read from the rendered page, splits the 40.0B attempted into "Successfully
downloaded: 16.8B" and "Dead links and other download errors: 23.2B". It has no category for
samples refused by an opt-out directive.

These images also trained the paper's own models. Appendix H says the 512-pixel cap "is still larger
than the 224 pixel resolution used for later training stages". The DataComp.XL ViT-L/14 card says
the model "was trained with the 1.4 Billion samples of the DataComp-1B dataset" on the Stability AI
cluster [S16]. Neither says outright that the checkpoint trained on the images from the original
collection rather than on a later re-download. That is the plain reading of Appendix H.

Searched for and not found in either paper version: "X-Robots", "noai", "opt-out", "Spawning",
"header". "robots" appears once, in Q31 (section 4 below).

## 2. What the DataComp repository pinned

`git clone https://github.com/mlfoundations/datacomp` worked. The history runs from 2023-04-27 to
2025-04-28 (68 commits, HEAD `4a8df199`). Three commits touch the img2dataset pin, and all three set
the same version [S3, S5]:

| Commit | Date | File | Pin |
|---|---|---|---|
| `c7d34419` "Initial commit" | 2023-04-27 21:18 -0700 | `environment.yml` | `img2dataset==1.40.0` |
| `d6c8a7fb` "added create env" | 2023-05-30 | `environment_osx.yml` | `img2dataset==1.40.0` |
| `7cf6c041` "Create requirements.txt for people who don't want to use conda" | 2023-07-20 | `requirements.txt` | `img2dataset==1.40.0` |

HEAD's `environment.yml` and `requirements.txt` still read `img2dataset==1.40.0`.

`download_upstream.py` has been rewritten many times, 15 commits from the initial one to `d16be5b`
on 2023-08-10. In the initial commit [S4] it fetches the `*.parquet` index from the
`mlfoundations/datacomp_pools` Hugging Face repository and then calls:

```python
img2dataset.download(
    url_list=str(metadata_dir),
    image_size=512,
    ...
    resize_mode='keep_ratio_largest',
    resize_only_if_bigger=True,
    output_format='webdataset',
    input_format='parquet',
    url_col='url',
    caption_col='text',
    bbox_col=bbox_col,
    save_additional_columns=['uid'],
    number_sample_per_shard=10000,
    oom_shard_count=8
)
```

At HEAD [S6] the call adds `encode_format`, `retries` and wandb options. No revision passes
`disallowed_header_directives` or `user_agent_token`, and nothing in the repository's history
mentions robots, `noai`, opt-outs or takedowns. So a participant who follows the repository gets
img2dataset 1.40.0 with its default opt-out list.

What the repository does not show is the collection. Its first commit came a month after the window
closed. Its download script reads an index that existed only after filtering. The paper's data
funnel starts from about 88B Common Crawl pairs, not from that index. The collection scripts that
Q23 describes are not published here, and the paper does not link them anywhere else. The one
earlier trace is in img2dataset's own history (section 3).

## 3. img2dataset's opt-out handling, version by version

`git clone https://github.com/rom1504/img2dataset` worked, HEAD `95523bc7` (2025-08-16). Release
dates are PyPI first-upload times [S7]. Code is read at each release's tag commit [S8-S13].

| Release | PyPI upload (UTC) | X-Robots-Tag handling | Default |
|---|---|---|---|
| 1.33.0 | 2022-08-23 | None | n/a |
| 1.34.0 | 2022-11-25 | `disallowed_header_directives` added by #218 (commit `eb672d55`, 2022-11-24, "Respect noai and noimageai directives when downloading image files") | `None`: nothing filtered unless the caller passes a list |
| 1.35.0 to 1.38.0 | 2022-11-26 to 2022-12-17 | Same | `None` |
| 1.39.0 | 2022-12-19 14:13 | #249 (commit `d38add90`, 2022-12-19, "Respect x robots tag by default") | `["noai", "noimageai", "noindex", "noimageindex"]`; `'[]'` turns it off |
| 1.40.0 | 2022-12-22 03:59 | Same | Same. This is the version DataComp pins |
| 1.41.0 to 1.47.0 | 2023-01-07 to 2025-08-10 | Same | Same |

The 1.34.0 parameter (`main.py` at `eb672d55`) [S8]: `disallowed_header_directives:
Optional[List[str]] = None`, with no defaulting. Its README line read "(default *None*)".

At 1.39.0 and 1.40.0 (`main.py` at `debd4df2` and `40160082`) [S10, S11]:

```python
    if disallowed_header_directives is None:
        disallowed_header_directives = ["noai", "noimageai", "noindex", "noimageindex"]
    if len(disallowed_header_directives) == 0:
        disallowed_header_directives = None
```

The 1.40.0 README [S13]: "Websites can pass the http headers `X-Robots-Tag: noai`, `X-Robots-Tag:
noindex` , `X-Robots-Tag: noimageai` and `X-Robots-Tag: noimageindex` By default img2dataset will
ignore images with such headers. To disable this behavior and download all images, you may pass
--disallowed_header_directives '[]'".

How the check works at 1.40.0 (`downloader.py`) [S12]. It reads the `X-Robots-Tag` response headers
of the image request itself. A directive scoped to a user agent (`X-Robots-Tag: somebot: noai`)
counts only if that name equals `user_agent_token`, which DataComp's script never sets. A match
returns the error string "Use of image disallowed by X-Robots-Tag directive" and discards the image.
The request goes out as a GET with a Firefox user-agent string, plus a `(compatible; <token>;
+https://github.com/rom1504/img2dataset)` suffix only when a token is set.

**robots.txt.** No img2dataset release reads robots.txt. The code at 1.40.0 and at HEAD has no
robots.txt parser, and the HEAD README describes no robots.txt check [S14]. The #249 commit message
names only header directives. Issue #48, "Implement Robots.txt support", was opened 2021-09-16. Its
maintainer first replied that the tool "is meant to be used after a crawler has been run". He
reopened it on 2023-03-02, and it was still open when read today [S20]. That issue page was read
through a summarizing fetcher because GitHub refused the digest fetch, so its quotes are as that
fetcher returned them.

**DataComp's authors in img2dataset's history, November 2022 to January 2023.** The clone shows
DataComp authors contributing to img2dataset during the run-up to and the start of the collection.
Samir Yitzhak Gadre added `max_image_area` (#231, 2022-11-25). Gabriel Ilharco added the
`keep_ratio_largest` resize mode (#240, opened 2022-12-12, merged 2022-12-17, released in 1.37.0
the same day).
Georgios Smyrnis added face blurring from bounding boxes (#241, 2022-12-17), extra hashes (#255,
2022-12-21) and hash verification (#258, 2023-01-07). Ilharco cut release 1.40.0 (#257,
2022-12-21). In #240, Ilharco wrote on 2022-12-13 that the mode "might be useful we if want to ensure
our images are smaller than a certain file size", at resolution 512 (read through the summarizing
fetcher [S21]). Appendix H says the collection resized images so "their largest dimension does not
exceed 512 pixels". That is what `keep_ratio_largest` with `image_size=512` does, and earlier
releases had no mode for it. Beaumont, a data-collection lead, merged #249 on 2022-12-19. The
fetcher returned his comment on the PR as "It is now the default to not download opted out images"
[S22].

## 4. Opt-outs at the image host, and anything after the fact

**What the paper claims.** Datasheet Q31 [S1, S2]:

> Following our usage of Common Crawl and https://github.com/rom1504/img2dataset for download
> images, we respect robots.txt files, which specify parts of websites that a crawler may access.

Section 3 shows that img2dataset does not read robots.txt. What the sentence can rest on is Common
Crawl's crawler, which checks robots.txt for the pages it archives. Those pages were crawled between
2014 and 2022, and the image URLs were extracted from them. Lee et al. (2025) describe the gap: the
extraction "does not consider the page url where the image appears", and "a dataset user downloading
CommonPool to train a model does not specify the user agent by default and therefore can bypass
REP" [S18].

**X-Robots-Tag.** The paper does not mention it. If the collection ran on 1.39.0 or later with
defaults, images whose host sent an un-scoped `noai`, `noimageai`, `noindex` or `noimageindex`
header were dropped and counted among the 23.2B failures. If it ran on 1.38.0 or earlier, or passed
`'[]'`, they were not. The sources read do not settle which.

**Opt-out lists.** No source ties the collection to Spawning's Do Not Train registry or any other
list. Hong et al. (2025) write that Hugging Face, which hosts the index, "integrates with Spawning
AI, a tool that allows users to search and remove their personal information from the dataset"
[S19]. That is a secondary claim about the hosting platform today. It does not describe the 2022-23
collection, and the DataComp cards do not mention it.

**Removal after release.** The datasheet commits to the LAION form: "In conjunction with LAION, we
use https://laion.ai/dataset-requests/ to monitor user takedown requests" (Q32). Q56 adds "where
'Sample ID' is the sample uid", and Q55 says "we will respond to user takedown requests". The form is
live today and takes a name, email, explanation, dataset, sample ID and URL [S17]. No record of a
removal was found:

- The `mlfoundations/datacomp_1b` commit history [S15] has parquet uploads on 2023-06-13, a README
  on 2023-08-08 and a README update on 2023-08-21, and no commit since. The `datacomp_xlarge`
  history has four "Removing files." commits on 2023-08-20. The one inspected deletes `.npz` feature
  files, and nothing has been committed since 2023-08-21.
- In GitHub issue mlfoundations/datacomp#71, "Remove CSAM, if present" (2023-12-20), Ludwig Schmidt
  replied on 2023-12-29 that "Unlike LAION-5B, we removed NSFW content when assembling DataComp" and
  "We will review this issue in more depth". No later maintainer reply reports a removal, and the
  issue is open (summarizing fetcher [S23]). A read of all 69 issue titles today found none about
  robots.txt, X-Robots-Tag or opt-outs.
- No later DataComp re-release was found. The datasheet: "At the present time there is no intention
  to update COMMONPOOL for scientific reasons" (Q55).

**Whether the metadata says rows were dropped for opt-outs.** It does not. Table 8 lists the
published fields: `uid`, `url`, `text`, `original_width`, `original_height`, `sha256`, CLIP scores
and features, and `face_bboxes`. The NSFW and dedup scores were "dropped during Step 3". None records
download status. The pool holds only images that downloaded, so an image refused by a directive
would simply be absent, indistinguishable from a dead link.

**What later re-downloads show.** These describe the hosts today, not in 2022-23. Hong et al.
re-downloaded the 12.8M small pool in April 2025. They report that "21.4% or 2.7 million image URLs
fail to download" and that "Robots Disallowed tag is also a common error for 51 thousand image URLs
that fail to download", and they confirm that the downloader "by default respects X-robots-tag
(unless explicitly modified by the user)" [S19]. Every pool image downloaded successfully in the
original run, so those 51 thousand hosts either did not send the directive then or were not checked
for it. The sources cannot say which. Lee et al. found CCBot named in 353K robots.txt files on
domains in the pool and read it as consent revoked after the crawl [S18].

## Established, inferred and unknown

| Finding | Status | What would close it |
|---|---|---|
| Images downloaded December 2022 to March 2023 by the authors, led by Beaumont (LAION) and Shankar (Apple), on AWS, with img2dataset | Established: datasheet Q23, Q25, Q26, Appendix B, Section 3.2 | Closed |
| About 40B attempted, 16.8B succeeded, 23.2B failed, failures not broken down | Established: Q7, Figure 7 | The run's per-shard `_stats.json` `status_dict`, which counts each error string, would break them down |
| The DataComp repository pins img2dataset 1.40.0 and runs its default opt-out list | Established for participant re-downloads from 2023-04-27 on | Closed |
| That pin or configuration is what the collection used | Unknown. The repository postdates the collection and does not hold its code | The collection scripts, or a statement from the data-collection leads |
| img2dataset honored X-Robots-Tag by default from 1.39.0 (2022-12-19) and only on request in 1.34.0 to 1.38.0 | Established: code and PyPI dates | Closed |
| The collection ran on 1.37.0 or later | Inferred: the 512-pixel largest-side resize matches `keep_ratio_largest`, first released in 1.37.0, which a DataComp author wrote for "our images" a week before release. A pre-release checkout, a fork or a separate resize step would also fit | The run's config or the installed version |
| The collection honored X-Robots-Tag `noai` and its siblings | Unknown. Plausible if it ran 1.39.0 or later with defaults: the collection lead merged that default, and DataComp authors cut 1.40.0. Not documented, and the window starts before 1.39.0 existed | img2dataset's logger records the effective `disallowed_header_directives` in its config parameters (passed to wandb when enabled), and `_stats.json` counts "Use of image disallowed by X-Robots-Tag directive". Either, from the original run, would settle it |
| The collection checked robots.txt at the image host | Established that it did not through img2dataset, which has never read robots.txt. The paper's Q31 claim rests on Common Crawl's page-level check | Closed, unless the unpublished scripts added a check, which nothing suggests |
| Any opt-out list (Spawning or other) applied during or after collection | No record found | A statement from the DataComp team or Spawning |
| Retroactive removal from the published index | No record. The DataComp-1B metadata is unchanged since 2023-08-21 | A DataComp erratum or release note, or a log of takedowns the LAION form received for DataComp |
| DataComp.XL checkpoints trained on images from the original collection, not a re-download | Inferred from Appendix H ("used for later training stages") and the model card | The OpenCLIP training configuration for the DataComp.XL runs |

## What each finding bears on

This section draws no scoring conclusion. Element 4 asks for documented practice during the original
collection. The sources establish the date, the tool and who ran it. They also establish that
image-host robots.txt was not checked. They do not establish whether the collection honored the one
image-level opt-out its tool could honor, because the window spans img2dataset's change of default
and the configuration was never published. The paper's own opt-out statement is the robots.txt
sentence in Q31. As written it credits img2dataset with a check that img2dataset does not perform.
The removal route (the LAION form, by sample uid) is documented, and no use of it is on record.

The record that would settle the open point is the original run's img2dataset configuration or
per-shard statistics. Publishing them, or a statement of them, is for the DataComp maintainers
(contact@datacomp.ai, per Q53). Nothing in this brief requests that or changes the hold.

## Sources

Map files are on `main` at `da554d5f`: `sources/verification_queue.yaml` (`openclip.openness`),
`sources/scores/openclip.yaml`, `docs/reference/openness.md` and `docs/rulings/log.yaml`
(R-2026-11-13-d).

Everything below was read 2026-11-14. Rows with a digest were fetched with
`uv run python -m build.fetch_source`. Raw GitHub files are pinned to commits so the digest stays
reproducible. Git history was read from local clones of the two repositories at the HEADs named
above. GitHub issue and pull-request pages returned HTTP 403 to `fetch_source` after six attempts.
Rows S20 to S23 were read through a summarizing web fetcher instead, have no digest, and their quotes
are as that fetcher returned them. Treat them as leads to re-read, not as digested evidence.

| # | URL | Status | content_sha256 | What it gave |
|---|---|---|---|---|
| S1 | https://arxiv.org/pdf/2304.14108v1 | 200 | `b001791ad499b7aed924de73226bfdcb366bf1c407ff1aa912f8cf78f08363ee` | v1, 2023-04-27: the same Q26 window, Q31 robots.txt sentence and Q32 LAION form as v5 |
| S2 | https://arxiv.org/pdf/2304.14108v5 | 200 | `d9f4c71b5ab8b1e8642ed6a0d2d7f7f6d05494c17633e8be60a3c935fface6ae` | v5, 2023-10-20: Section 3.2; Appendix B ("Data collection. Romain Beaumont, Vaishaal Shankar"); Appendix D; Appendix H, Figure 7 and Table 8; datasheet Q2, Q3, Q7, Q23, Q25, Q26, Q31, Q32, Q37, Q53, Q55, Q56 |
| S3 | https://raw.githubusercontent.com/mlfoundations/datacomp/c7d34419dc2e2e99dce09277d4024f798ec9e3ce/environment.yml | 200 | `2de23162e87c3a4b702783317ae9346a102b68e4357a562cb87f4a0f190b7af5` | Initial commit, 2023-04-27: `img2dataset==1.40.0` |
| S4 | https://raw.githubusercontent.com/mlfoundations/datacomp/c7d34419dc2e2e99dce09277d4024f798ec9e3ce/download_upstream.py | 200 | `8d55fb548867195737eedd9879604575f31de77da00fe6460230058edee0957d` | Initial download call; no `disallowed_header_directives`, no `user_agent_token` |
| S5 | https://raw.githubusercontent.com/mlfoundations/datacomp/4a8df1992566ef8334773f7152e1855b1f716162/requirements.txt | 200 | `188f903af874cd5b7e0db5c61c9dd73a257aecbfa196740548758a6f58a6cdd3` | HEAD, 2025-04-28: `img2dataset==1.40.0` |
| S6 | https://raw.githubusercontent.com/mlfoundations/datacomp/4a8df1992566ef8334773f7152e1855b1f716162/download_upstream.py | 200 | `024562b245cd2cbe674e16e742fe128eb6aa366b6e521a98e0ceef2a0cf2e4e5` | HEAD download call; still no opt-out arguments |
| S7 | https://pypi.org/pypi/img2dataset/json | 200 | `582d1560ae5d3cc9075fb820f1377eb33eee2085a25ebbadeed5b30391c04b57` | Upload times: 1.34.0 2022-11-25, 1.38.0 2022-12-17, 1.39.0 2022-12-19, 1.40.0 2022-12-22, 1.41.0 2023-01-07 |
| S8 | https://raw.githubusercontent.com/rom1504/img2dataset/eb672d5515d563a24080c190d0734473451e5d97/img2dataset/main.py | 200 | `db5e15b7e9e45ead57941ca554efb150d6612e938b87d20c43892cc80acfce56` | #218: `disallowed_header_directives` added, default `None` |
| S9 | https://raw.githubusercontent.com/rom1504/img2dataset/7c0127c3585d0c8759e3fdafb2daa51d793dae4d/img2dataset/main.py | 200 | `48cd6bd39d97d7d3ff23a3440854621e079f4df2eedd4a9b2fddd6d75ea206b4` | 1.38.0: default still `None` |
| S10 | https://raw.githubusercontent.com/rom1504/img2dataset/debd4df264bd6d6670ec2645c5b7ec0cc4926d00/img2dataset/main.py | 200 | `6ea3deccad545b55a661967e1da2bb8a0e3577cf2eeab42402ad5aadfb427d6c` | 1.39.0: default list `noai`, `noimageai`, `noindex`, `noimageindex` |
| S11 | https://raw.githubusercontent.com/rom1504/img2dataset/40160082d2cfc1e83b5902ab4874148b43d2e788/img2dataset/main.py | 200 | `0114992a212ad26cfde2116d4a47787dd7e273c70d47bf472929f6b5ebe6cb7b` | 1.40.0: same default |
| S12 | https://raw.githubusercontent.com/rom1504/img2dataset/40160082d2cfc1e83b5902ab4874148b43d2e788/img2dataset/downloader.py | 200 | `1cd7a0e60576ec91275ea01ac0acf89d5b3cbd14e0f4961539f2d6e134ef046a` | 1.40.0: `is_disallowed`, the user-agent scoping, the GET request and the error string |
| S13 | https://raw.githubusercontent.com/rom1504/img2dataset/40160082d2cfc1e83b5902ab4874148b43d2e788/README.md | 200 | `e9cf0a54351f01dc5fe1616f4cd4cdec2f48bb2209a1d8e97e0f5222a54621ae` | 1.40.0 "Opt-out directives" section and parameter docs |
| S14 | https://raw.githubusercontent.com/rom1504/img2dataset/95523bc7579745a1749b8132d408b9fea89a338e/README.md | 200 | `ead0a7b15e9761af003a8b6b6ffdad266d7d9817eba238bef6cd6fe83acecd51` | HEAD README: header directives only, no robots.txt |
| S15 | https://huggingface.co/api/datasets/mlfoundations/datacomp_1b/commits/main | 200 | `cc5543e07e68deb79e4ec89328b76ee55f835dc5b62e7f70215ba6596fe448c6` | Last commit 2023-08-21; parquet uploads 2023-06-13. The `datacomp_xlarge` list (`1a42dc29604c828ff24039db7b6d7c52e3d6e5c18ea60f958143b3fad9a9de50`) has four "Removing files." commits on 2023-08-20; commit `37edc8b1` deletes `.npz` files |
| S16 | https://huggingface.co/laion/CLIP-ViT-L-14-DataComp.XL-s13B-b90K/raw/main/README.md | 200 | `dae51749e117ec55c9d78b71967be59a2424cfd85f9ceb20bb92bc277900cd40` | "trained with the 1.4 Billion samples of the DataComp-1B dataset"; training on the Stability AI cluster |
| S17 | https://laion.ai/dataset-requests/ | 200 | `a98e3ab17c2b86b42a78f3c7f48cfd9809411a247013c42f51aa7b66808d516a` | The live request form: name, email, explanation, dataset, sample ID, URL |
| S18 | https://arxiv.org/pdf/2511.08637v2 | 200 | `2cec80b9aa40317c007fa30ce97798e481265eae0edbde6e7f34ac1e365158d9` | Lee et al., 2025-11-23: page URL not considered; CCBot in 353K robots.txt files; default user agent "can bypass REP" |
| S19 | https://arxiv.org/pdf/2506.17185 | 200 | `3ef4fc957f15156c2eb0154780d8eda39c14dd46cb8e259c9f1c85f6246b98ac` | Hong et al., CS&LAW '26 extended version: April 2025 re-download, 21.4% failures, 51 thousand "Robots Disallowed" errors, default X-Robots-Tag handling, Hugging Face's Spawning integration |
| S20 | https://github.com/rom1504/img2dataset/issues/48 | 403 to `fetch_source`; summarizing fetcher | none | "Implement Robots.txt support", opened 2021-09-16, reopened 2023-03-02, open |
| S21 | https://github.com/rom1504/img2dataset/pull/240 | 403 to `fetch_source`; summarizing fetcher | none | Ilharco, 2022-12-13: "ensure our images are smaller than a certain file size", resolution 512 |
| S22 | https://github.com/rom1504/img2dataset/pull/249 | 403 to `fetch_source`; summarizing fetcher | none | Opened 2022-12-17, merged 2022-12-19 by rom1504: "It is now the default to not download opted out images". The commit message (`d38add90`, read from the clone) is the digest-free primary text |
| S23 | https://github.com/mlfoundations/datacomp/issues/71 | 403 to `fetch_source`; summarizing fetcher | none | "Remove CSAM, if present"; Ludwig Schmidt, 2023-12-29; open, no removal reported |

Not available today: github.com issue and pull-request pages and api.github.com returned HTTP 403,
so S20 to S23 have no digest. The DataComp repository's issue list (69 issues) was also read only
through the summarizing fetcher.
