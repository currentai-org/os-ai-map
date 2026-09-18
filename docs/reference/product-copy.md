# Prose guide

The house style for every hand-written string on the map: the product `description` and
`comments`, the score `note` on each axis, the `shows` extract on each source, and the
unpublished prose an editor reads (category `comments`, `scoring_recipe.note`, YAML `#`
comments, module docstrings). One rule runs through all of it, and the rest of this guide is
that rule applied field by field.

> This guide governs prose. How a *score* earns a `last_verified` date, what counts as
> evidence, and the gates around both live in
> [`evidence-and-freshness.md`](evidence-and-freshness.md), and nothing here overrides them.
> When a rule here changes, change the guide first and make the workflows and skills follow.

## The one rule

**Write for the reader who has never seen the rubric.**

Four of these fields are published. `build/serialize.py` puts `description`, `comments` (as
`version_note`), every `note` and every `shows` into the payload verbatim, and the product
detail panel renders all of them, one above the other, in this order: description, comments,
then per axis the components, the note as `Why` or `Detail`, and the source list. A visitor
reads them as one page about one product. An editor reads the same strings in the score file
while deciding whether the score is right.

The corpus was written for the second reader. It says "rung 4", "the other half of the
ladder", "one below the anchor", "level 5 here is measured, not inferred", "the formula has
nothing to resolve to". Every one of those is a sentence about the scoring machinery, addressed
to the person auditing the score, sitting in the copy a visitor reads. Measured 2026-09-17,
879 of 2,289 notes carried that vocabulary, and 963 restated an exact figure that the source
line directly beneath them already showed.

So the test for every sentence in a published field is: **would a careful reader who has never
opened `sources/rubrics/` understand it, and does it tell them something the page does not
already show?** A sentence that fails the first half is rewritten in plain terms. A sentence
that fails the second half is deleted.

The unpublished fields have the opposite reader and the same discipline: they are read by the
next editor, so they may use the rubric's words, but they still say a thing once and point to
where it lives rather than restating it.

## Where each field renders, and who reads it

| field | file | payload | renders as | reader |
|---|---|---|---|---|
| `description` | `products/<slug>.yaml` | `description` | the paragraph under the product name | visitor |
| `comments` | `products/<slug>.yaml` | `version_note` | a smaller footnote under the description; absent when empty | visitor |
| `openness.note` | `scores/<slug>.yaml` | `openness.note` | the `Why` row on the openness axis | visitor |
| `adoption.note`, `capability.note` | `scores/<slug>.yaml` | `<axis>.note` | the `Detail` row on that axis | visitor |
| `sources[].shows` | `scores/<slug>.yaml` | `<axis>.sources[].shows` | the line under each source URL | visitor |
| category `comments`, `scoring_recipe.note` | `categories/<slug>.yaml` | not published | nothing | editor |
| YAML `#` comments | `rubrics/`, `registry/`, `signal_routing.yaml`, … | not parsed | nothing | editor |
| module docstrings | `build/*.py` | `--help` for the CLIs | nothing | editor |

The score, class, level, reach, confidence, components and the `Verified <date>` freshness
label are all rendered from structured fields. Prose never needs to repeat any of them.

## `description`: what the product is and does

**Purpose.** Tell a reader what the product is and what it does, in the neutral register of a
catalog entry. It is not a pitch and not a review.

**`description` is the load-bearing field.** Everything a reader needs about the product
belongs here: what it is, what it does, what distinguishes it, and who builds or stewards it.
When a fact could sit in either `description` or `comments`, it goes here.

**Format.**
- **Length: 2 to 4 sentences, roughly 35 to 70 words.** One sentence is too thin for a scored
  product and six is too long. A long-tail entry may be a single clause.
- **Lead with the product doing something**, not with its vendor. Good: "Accelerate is a
  Hugging Face PyTorch library that lets users run raw PyTorch training scripts across CPUs,
  multi-GPU, and TPU". Who builds it usually closes the paragraph rather than opening it,
  unless the org is load-bearing for identity ("NVIDIA's content-safety classifier").
- **Vary the sentence openings.** Three sentences in a row beginning "It …" read as a
  generated list.
- **Present tense, third person, declarative.** No second person, no imperative.
- **First mention uses the display name**, then a natural short form.
- **Spell out an acronym once** if the category's reader would not know it.

**Include:** the product's kind (library, model, protocol, dataset, board) and its one-line
job; what distinguishes it from the obvious neighbor, factually ("Where MCP connects agents to
tools, A2A connects agents to other agents"); concrete, checkable specifics such as parameter
class, modality, what it bundles, what standard it implements.

**Exclude:**
- **Marketing cadence.** No "powerful", "cutting-edge", "seamless", "revolutionary",
  "blazing-fast". Borrow the register named in `docs/methodology.md`: precise, defined,
  measured, forthright about limitations. `tests/test_product_prose.py` holds a list of the
  phrases that have actually appeared.
- **Unsourced superlatives and rankings** ("the best", "the leading", "the de facto standard")
  unless they are a plain, checkable fact stated as one, with the measure named.
- **Point-in-time facts**: star counts, download counts, contributor counts, "fastest-growing",
  the current version number. See "Volatile facts" below.
- **Curator rationale.** "Picked when hardware is constrained" is a note about our selection,
  not about the product, and it reads as a recommendation in a catalog entry. Find it with
  `\b(picked|chosen|included|selected)\s+(because|when|by|for|as|if)\b`. Salvage any product
  fact trapped inside the clause into the description proper, drop the counts and superlatives,
  delete what is left. A genuine selection judgment worth recording is a footnote about our
  reading and belongs in `comments`.

## `comments`: a footnote, usually empty

**Purpose.** Something about *our reading* of the product that a visitor would want beside the
description and that no other field carries. It is optional, and most products need none.

The test is the subject of the sentence:

| the sentence is about… | field |
|---|---|
| the product: what it is, does, runs on, who builds it | `description` |
| why a score is what it is | the axis `note` |
| what a cited page shows | that source's `shows` |
| our reading of the entry as a whole: an evidence gap, a treatment choice | `comments` |

Footnotes that earn their place:
- an evidence gap: "No tagged releases, so the entry is read against the repository head."
- a treatment choice that spans axes: "Scored as the hosted service; the open-source SDK is a
  separate entry."
- something in a source that would mislead the next reader: "The LICENSE file also bundles
  third-party code under separate terms."

Footnotes that do not:
- **A restatement of an axis note.** "The self-hosted build cannot take screenshots; that is
  the gate the openness score rests on" is the openness `Why` said again two screens up. Measured
  2026-09-17, 153 of the 564 non-empty footnotes overlapped a note that heavily. Delete them.
- **A dated verification sentence.** `Verified 2026-08-13 via the LICENSE body.` used to end
  every `comments` field. The date is `last_verified` on each axis, and the page already prints
  it as `Verified <date>`. The line was a third copy, and the one visitors read as a footnote
  about the product. It is gone, `tests/test_product_prose.py` keeps it gone, and no workflow
  writes it. What it named (the document that was read) belongs on the source entry as `url`
  and `shows`.
- **A product fact.** Move it to `description`.
- **The license.** It is `openness.components`, rendered in larger type directly below.

**Format.** Up to about 45 words, one or two sentences, no lower bound. An empty `comments`
omits `version_note` from the payload, and the panel is quieter for it. Do not invent a
footnote to fill the field.

## The score `note`: why this rung, in plain words

**Purpose.** The `note` is the one place a visitor learns *why* an axis reads what it reads.
The schema says "a sentence or two", and the corpus median was already close to that; the
problem was the audience, not the length.

**The shape.** Two sentences carry almost every note on the map:

1. **What the product ships or does that puts it on this rung.** The fact, named concretely:
   the license and where it applies, the figure and what it counts, the feature or benchmark
   result.
2. **What keeps it off the next rung**, or, at the top, what the rung asks for that it has.
   Also a fact: the training corpus is not published, the engine is not in any repository,
   the leaderboard now has a higher entry.

A third sentence is allowed when the score turns on a distinction a reader would otherwise
miss (the vendor sells a hosted service, but that is not what gates the core). A fourth almost
never is. Where the argument needs more room than that, the detail belongs in the sources'
`shows` lines and in `components[].detail`, both of which the page renders beneath the note.

**Write in the reader's vocabulary, not the rubric's.** The words below are internal. Each has
a plain equivalent, and the equivalent is nearly always shorter.

| rubric word | what to write instead |
|---|---|
| "rung 4", "band 3", "level 5", "the top rung" | say what the rung *means*: "the competitive frontier", "over ten million downloads a month", "an open model". The number is rendered beside the note already. |
| "the anchor", "one below the anchor", "level with the anchor" | name the product: "a step below vLLM". Record the comparison in `capability.relative_to` and `relation` too, where a gate can check it. |
| "the ladder", "the other half of the ladder", "the software scale" | name the dimension: "the training data", "the design files", "the usage figure". |
| "`multi_sku_rule`", "the formula", "the rule fires", "abstains" | delete. A visitor cannot see the rule, and the note argues from the facts the rule reads. |
| "the band rests on X", "the score rests on X", "banded on X" | "X puts it here" or simply state X. |
| "measured, not inferred", "stated by the vendor", "which is what the rung asks for" | delete. The sources beneath show what was measured and who said it. |
| "instrument", "signal type", "`stars_fallback`" | "GitHub stars are the only signal" or whatever the plain fact is; `signal_type` is rendered as `Signal`. |

**No usage figures.** A star count, a download count, a pull count, a user or customer count
is stale the day the source refreshes, and "the most in this category" is falsified by the
next product added. Neither belongs in a note. The number already has two homes on the page:
the source line, with the date it was read, and the `Reach` row. The note says what was
measured, why that signal stands in for the product, and what it does not show: "Hugging Face
downloads across the three checkpoints, most of them for the 0.6B model", not "12,549,679
downloads". A number that is a durable fact about the product stays: 8B parameters, a 32k
context window, five accelerator vendors, three checkpoint sizes, a benchmark score at
release. A `reported_traction` note that cites a magnitude must keep its `banded_quantity` in
step, and a note whose argument is a gap between two versions keeps both versions.

**Full sentences, in an editor's English.** Every note is sentences with a subject and a verb,
not a fragment that opens with a figure or a license name. The test is whether an editor would
publish it without noticing the prose. Clear but visibly written from a rubric is a 7 out of
10 and not good enough. The warning signs are phrases a normal writer would not produce: "holds
it at", "stands in", "is read the same way", "a band lower", "at this band", "countable
channel", "star-based reading", "rests on", "banded at", and the map's machinery named as a
noun ("on this dimension", "this axis measures", "the top of the scale", "the middle of the
adoption scale", "the next level up"), and any construction where a subject and verb would
have done. Renaming the machinery is not removing it: "the top of the adoption scale" is "the
top adoption band" in a new coat, and the detector reads both. Preserve every fact; rewrite every sentence that sounds like it was generated by
walking the rubric. The scoring logic should be evident from the facts while the machinery of
the scoring system stays invisible.

**Peers.** Name them. "One tier below the Megatron-LM anchor" becomes "a tier below
Megatron-LM", and the comparison goes into `relative_to` and `relation` so
`build/check_capability.py` can hold it against both scores. A note that names a peer it does
not record is listed by `check_capability --candidates`.

**Phrases a gate reads.** Two detectors read adoption notes for a candid admission, and their
findings are pinned. A note that says the signal *understates* the product, or is *inflated*,
or counts a *minority channel*, is making a claim the map records deliberately. Rewriting such a
note keeps that phrase verbatim (`build/sweep_status.py`, `UNDERSTATES` and `INFLATED`, is the
list) unless the claim itself is being withdrawn, which is a re-read, not a prose edit.

**No dates, no chronology.** A note states what is true until the score changes. When it was
checked is `last_verified`; what it used to say is `git log -p --follow`. "Corrected from level
4", "the note this replaces", "settled under issue 264", "an earlier draft was withdrawn" are all
history, and they leave. The exception is a date that is a fact about the product or the source,
a spec revision named by its date or a GA date, and each such axis is listed in
`tests/test_score_notes.py` with its reason.

**A note may not restate `components` or `shows`.** "Apache-2.0 (OSI), source public, core
ungated" is the components block set as prose. The note explains; the block records. The
reverse move is the same defect: lifting a `shows` line's detail up into the note so the note
"has an argument" puts the evidence on the page twice.

**Shorter, not longer.** A rewrite is drawn from the facts the record already carries and is
normally shorter than what it replaces. A one-sentence factual note on a plain open-source
tool ("MIT, public repository, nothing sold beside it") is already right, however many products
share the sentence, because they share the facts. Do not expand it into a paragraph, and do not
invent variety: sixty products with identical evidence get the same short sentence, not the
same long paragraph with the vendor's name swapped. A rewrite that lengthens a note needs a
reason.

**No adjectives about a figure.** "Comfortably in the tens of thousands", "a solid but mid-range
figure", "at the low end of the measured range" say nothing the number does not. State the figure,
what it counts, and what it cannot show. The plain reason a star count cannot place a product
high is that a star is not a use; say that, not "caps any reading low".

**Abstaining is a note too.** Where `level` or `score` is null, the note says why no reading was
possible in the same two-sentence shape: what was looked for, and why nothing found could stand
in for it.

**Length.** The guard in `tests/test_score_notes.py` holds a note at or under 600 characters,
which is where the longest golden below lands. A note that cannot argue its rung in that space
is carrying evidence that belongs in `shows` or `components[].detail`.

## `sources[].shows`: what the page shows

**Purpose.** What a reader would see if they opened the URL: the license text, the download
figure, the sentence in the README. It is an extract, not an argument.

- **Short.** One or two clauses, up to about 40 words. The corpus median is already there.
- **Quote where a quotation is the evidence.** `"You may not provide the software to third
  parties as a hosted or managed service"` is exactly the kind of thing `shows` is for.
- **Say which dimension it settles only through `establishes`**, not in prose.
- **Do not retell the note.** A `shows` that argues the rung is the note said twice. If the
  note leans on a detail that is not in any `shows`, the detail moves down into `shows`, not
  the other way.
- **Dates are fine here.** Sources carry dates honestly: a `pushed_at`, a copyright year, a
  leaderboard snapshot date. The no-date rule is for notes.
- **No re-read narrative.** "Re-fetched, unchanged" is `accessed` and `content_sha256`.

## Goldens

Eleven notes and two footnotes, each rewritten from the corpus to the rules above, then edited
by a person for natural editorial English. The lengths of the rewritten notes are what the
600-character guard is read from. The before text is what the record carried on 2026-09-17;
the facts in the after text are the same facts, only the audience changed. The test each was
edited to: would an editor publish it without noticing the prose? Clear but visibly written
from a rubric is not good enough.

### 1. `qwen3-embedding` openness: rubric vocabulary

Before:

> Apache-2.0 across every distributed size, which is unusual for a Qwen release and means
> multi_sku_rule has nothing restrictive to resolve to. What holds it at 3 rather than higher
> is the other half of the ladder: the training corpus is described in the paper but not
> published, and the repository carries evaluation and usage code rather than the pipeline
> that produced the checkpoints.

After:

> All three sizes are released under Apache-2.0, which is unusual for Qwen. The paper describes
> the training corpus but does not publish it, and the repository includes evaluation and usage
> code rather than the pipeline used to produce the checkpoints. This makes Qwen3-Embedding an
> open-weights release rather than a fully open model.

`multi_sku_rule` and "the other half of the ladder" are the machinery. The reader needs the
two facts and what they add up to.

### 2. `qwen3-embedding` adoption: figures restated from the sources

Before:

> 12,549,679 downloads in the trailing 30 days across the three shipped embedding checkpoints
> - 7,806,497 for the 0.6B, 2,489,577 for the 4B and 2,253,605 for the 8B. Excluded from the
> sum: the vendor's own GGUF conversions of the same three checkpoints (another 173k) and the
> separate Qwen3-VL-Embedding line, which is a different product. Level 5 here is measured, not
> inferred.

After:

> Adoption is measured as Hugging Face downloads across the three embedding checkpoints, most of
> them for the 0.6B model. The vendor's GGUF conversions and the separate Qwen3-VL-Embedding
> line are excluded.

The download figures are the three `shows` lines beneath, each with the date it was read, and
the band is the `Reach` row. A count in the note is stale the day the source refreshes.
"Measured, not inferred" is a remark to the auditor; the `Signal` row says `usage_volume`.

### 3. `qwen3-embedding` capability: the anchor

Before:

> Rung 4, the competitive frontier. Qwen3-Embedding-8B held first place on the multilingual
> MTEB leaderboard at release and still posts 70.58, with 100+ languages, a 32k context and
> Matryoshka dimensions - everything the rung asks for. It is one below Harrier-OSS because the
> anchor's 74.3 has since displaced it from the top of the same table, not because anything
> about the Qwen line has weakened.

After:

> Qwen3-Embedding-8B led the multilingual MTEB leaderboard when it was released and still scores
> 70.58, while supporting more than 100 languages, a 32k context window and Matryoshka
> dimensions. Harrier-OSS has since overtaken it with a score of 74.3; otherwise,
> Qwen3-Embedding remains at the frontier of the category.

`relative_to: harrier-oss`, `relation: one_below` already record the comparison.

### 4. `firecrawl` openness: a gated close call, 1,800 characters

Before (abridged; the full note walked the repository tree file by file):

> The AGPL-3.0 core is genuinely open, but a piece of the product is withheld from it, which is
> what keeps this at open core rather than open source. The gate has a name: Fire-engine,
> Firecrawl's own scraping engine, whose source is in no public repository. What
> firecrawl/firecrawl publishes under apps/api/src/scraper/scrapeURL/engines/fire-engine is
> only a client - index.ts, scrape.ts, checkStatus.ts, delete.ts, brandingScript.ts - pointed
> at a URL you have to be given, and apps/api/.env.example says as much in one line […] These
> are features of the product itself, kept out of the published source behind a closed beta,
> so the score stays at 4. The managed cloud advertising "additional features" would not on its
> own be enough to establish a gate; the evidence here is in the code.

After:

> Firecrawl's AGPL-3.0 core is open, but Fire-engine, its own scraping engine, is not available
> in any public repository. The source tree includes only a client that connects to a separately
> provided endpoint, and the self-hosting guide says that screenshots, page actions, agents,
> browser features and specialty formats require either Fire-engine or Firecrawl Cloud. In other
> words, part of the product itself is withheld from the published source. That is what makes
> Firecrawl open core; the managed cloud's additional features would not be enough on their own.

The file names, the `.env.example` line and the self-hosting guide's exact words are already
in the five `shows` lines and in `components.core-gated.detail`. The note keeps the argument.

### 5. `tensorlake-sandbox` capability: 2,700 characters of settlement history

Before (abridged): the note argued the band, then recorded that it was "settled under issue
264", that "an earlier draft of this settlement was withdrawn on review", set a four-row table
of peers' latencies and scores, and closed with advice on "where to press" if the band is
revisited.

After:

> Tensorlake has most of the features expected from a leading sandbox platform: Firecracker
> microVM isolation for every tool call, snapshots that can be paused, forked and resumed,
> versioned mountable volumes, and durable functions with queues, timers and retries.
> Independent ComputeSDK benchmarks put its median time-to-interactive at 1.35 seconds, slower
> than the vendor's sub-second claim, although latency is not the main differentiator in this
> category. Scale is the bigger gap: Tensorlake reports thousands of concurrent sandboxes, while
> E2B has recorded more than a billion sandbox starts.

The settlement is in the issue and in git. The peers' scores are in the peers' files. What
survives is the positive case, the weak point, and the softer spot, which is what a reader
would want to know before trusting the 4.

### 6. `raspberry-pi-5` openness: a hardware board, and vocabulary drift

Before (abridged): after the schematic argument, the note explained that "the firmware
component read minimal until recently and now reads required, resolving an inconsistency this
note used to state and leave open", that "all nineteen other boards describe the same shape of
fact as required", that "what let the two readings coexist was an undefined vocabulary; the
rubric now says the test is necessity rather than size", and that "nothing scored turns on the
change".

After:

> Raspberry Pi publishes an open kernel tree and register-level datasheets for the RP1 I/O
> controller, and anyone can buy the board. But it does not publish a schematic for the Pi 5.
> The documentation includes a mechanical drawing and two STEP files, enough to design a HAT or
> case around the board but not to reproduce the board itself. That leaves the hardware only
> partially documented, however open the software stack may be. The GPU firmware and bootloader
> also remain Broadcom-licensed binaries that the board cannot boot without.

The vocabulary ruling belongs in `docs/reference/openness.md`, where it now is. The note says
what is true of the board.

### 7. `tesseract` adoption: a phrase a gate reads

Before:

> 76,518 GitHub stars, the largest count in this category. Tesseract is distributed as source
> and through distribution packages rather than a registry this map routes, so no usage-volume
> channel exists and the band rests on stars, which cap at 3. That understates a library
> embedded in a very large amount of other software, and the understatement is a property of
> the instrument.

After:

> Tesseract is distributed as source and through operating-system packages rather than through a
> registry this map can measure, leaving GitHub stars as the only comparable adoption signal.
> That almost certainly understates the use of a library embedded in a very large amount of
> other software.

"Understates" stays, word for word: `check_channel_authority` lists this record because the
note admits the figure under-measures the product, and the admission is the point. The star
count and "the most in this category" go: the count is in the source line with its date, and
the ranking is falsified by the next product added. "The band rests on" and "a property of
the instrument" go too.

### 8. `milvus` adoption: the "Banded on the" template

Before:

> Banded on the downloads of the declared client SDK: where a server has no countable channel
> of its own, its client's downloads are the best available usage signal, and this product
> declares pymilvus on exactly that basis. The registry reports 5,976,463 downloads in the last
> month (1,484,328 in the last week, 241,978 in the last day), which lands in 1M-10M on the
> software scale. Qdrant is treated the same way, being the same shape of product and banded on
> qdrant-client. Milvus is the default open source engine for billion-scale semantic search and
> an LF AI & Data graduate, but the band rests on the count rather than on that description.
> Zilliz publishes no server-side deployment figure, and the repository's 45,627 stars are a
> different instrument that cannot be read as usage volume.

After:

> Milvus is a server, so there is no direct package-download count for the product itself.
> Instead, its official Python client, pymilvus, provides the closest measurable signal through
> its PyPI downloads. Qdrant is measured the same way through qdrant-client. Zilliz publishes no
> comparable server-side deployment figure, and GitHub stars measure something different.

Seventy notes opened "Banded on the". The opening is the fingerprint of one prompt writing
all of them, and it says nothing a reader wants first. The download count stays in the source
line; the note says what was measured and why that stands in for the server.

### 9. `chitu` capability: "One band below the anchor"

Before:

> One band below the vllm anchor, level with xllm, rtp-llm and fastdeploy, the other
> production engines whose distinguishing surface is domestic-accelerator breadth. Its hardware
> span (five vendors plus pure CPU) and PD-separated cluster serving clear the two_below locals;
> it is not the community-wide throughput frontier the anchor and sglang occupy.

After:

> Chitu is a production inference engine distinguished by broad support for Chinese accelerator
> hardware: five vendors plus pure CPU, along with prefill-decode separated cluster serving. Its
> feature set is comparable to xLLM, RTP-LLM and FastDeploy, while vLLM and SGLang remain ahead
> on community-wide throughput.

`relative_to: vllm`, `relation: one_below` stays. "The two_below locals" is a rubric enum
value set as a noun.

### 10. `adobe-pdf-extract` adoption: abstaining, already right

Before:

> No usage figure is published for this service specifically, and it publishes no countable
> artifact - no package, repository or registry entry - so no level is assigned rather than one
> being inferred from the vendor's platform as a whole.

After:

> Adobe publishes no usage figures for this service, and there is no package, repository,
> registry entry or other countable artifact to use as a proxy. Rather than infer adoption from
> the Adobe platform as a whole, the map leaves this product unscored.

Included so the worker sees what "leave it alone" looks like. The edit is a trim, and a pass
that finds nothing to say about a note says nothing.

### 11. `accelerate` openness: already right, untouched

> The LICENSE file contains the standard, unmodified Apache 2.0 text. The repository is public
> and active, and the README describes the full library without a separate paid, enterprise or
> hosted tier. The source is public and the core is ungated.

Two sentences, two facts, the conclusion, no vocabulary. Most of the corpus reads like this,
and the pass is for the third that does not. It is one product's evidence written down, not a
template: the pilot pass pasted this paragraph, name swapped, onto fourteen products whose
notes had read "Fully OSI-licensed (Apache-2.0), full source public", and every one of the
fourteen was better before. A short factual sentence is left alone.

### A `shows` line: `agentops` openness, `app/LICENSE`

Before (700 characters):

> The license on the AgentOps app, which is not the license this record carries. The file is
> the Elastic License 2.0 verbatim. Its Limitations: "You may not provide the software to third
> parties as a hosted or managed service, where the service provides users with access to any
> substantial set of the features or functionality of the software", and "You may not move,
> change, disable, or circumvent the license key functionality in the software […]".
> Elastic-License-2.0 is declared in software.yaml's competition_restricted examples. The only
> commit touching this path is "AgentOps OSS release (#1190)", 2025-08-09, so it is the
> license the app was published under rather than a later change.

After:

> Elastic License 2.0, verbatim: "You may not provide the software to third parties as a hosted
> or managed service". Added in the "AgentOps OSS release (#1190)" commit of 2025-08-09, so the
> app was published under it.

Which rung an Elastic license lands on is the rubric's business, not the source's.

### Two `comments` footnotes

`firecrawl`, before:

> The self-hosted build cannot take screenshots or run page actions - both need Fire-engine,
> which is closed and ships in no public repo. That is the gate the openness score rests on.
> Verified 2026-08-13 via GitHub and the self-hosting guide.

After: **nothing.** Both sentences are the openness note; the third was the Verified line. The
key is removed and the panel shows description, then the axes.

`mastra`, before:

> GitHub's classifier cannot place the split license file, so it was read from the body and
> confirmed against npm metadata. Enterprise authentication code sits under separate terms, and
> a hosted platform is sold beside the framework. Verified 2026-08-12 via the mastra-ai/mastra
> repository tree and the npm registry.

After:

> GitHub's license classifier cannot read the split license file; the score was read from the
> file body.

The enterprise code and the hosted platform are the openness argument and live in that note.
What survives is the one thing a reader would not learn anywhere else on the page.

## Unpublished prose: category files, YAML comments, docstrings

These are read by the next editor, never by a visitor, so they may use the rubric's vocabulary
freely. Their discipline is different: **say it once, where it lives, and point.**

**Category `comments` and `scoring_recipe.note`.** The decision log for a category: why the
ladder was chosen, which license bodies had to be read rather than trusted, which product is
the exception and why. Keep it. Cut only what restates a rule that `docs/reference/` already
states (link instead) or narrates a sweep (that is `docs/sweeps/`). A `strapline` is published
and is one or two sentences about the category's shape today, without counts that a build
could interpolate instead.

**YAML `#` comments** in `sources/rubrics/`, `sources/registry/`, `signal_routing.yaml`,
`evidence_policy.yaml` and the other config files are ignored by every consumer. Two kinds are
worth keeping: a one-line clarifier beside a key whose reading is not obvious (why `'yes'` is
quoted under YAML 1.1; what `reads:` selects), and a one-line pointer to the reference document
that carries the reasoning. Everything else, the case law about which product gates and which
does not, the sweep narrative, the history of how a vocabulary settled, belongs in
`docs/reference/openness.md`, `docs/reference/adoption.md` or `docs/sweeps/`, where it is
found by someone who is not editing that file. Moving it is not deleting it: the salvage
happens first, with a table of where each block went, and the strip is checked to be
parse-identical.

**Module docstrings** in `build/` say why the module exists and how to run it, in a paragraph,
then point at the reference document that is the authority on the rule. A docstring is not the
normative home of a rule; `docs/reference/` is. Two constraints from #573: no live census in a
docstring that prints as `--help` ("four records today" is wrong within a fortnight), and an
example a docstring quotes must be one the function actually handles the way the prose says.
The comments inside a function that settle a live question stay; that volume was measured and
is not the problem.

## Global rules

1. **American English everywhere**: `license` not `licence`, `penalized`, `labeled`,
   `behavior`. Identifiers and prose alike.
2. **No marketing cadence.** Same register as the methodology copy.
3. **Never assert from memory.** Any factual claim is confirmed against a primary source before
   it is written. A prose-only pass that opens no source writes no new fact; it rewrites what
   the record already says.
4. **Keep judgments on the axes.** An openness verdict and the license it rests on belong in
   the score file, where they carry evidence. See "Scored fields" below.
5. **Do not embed volatile facts** in `description` or `comments`: counts, current version
   numbers, corporate events. See below.

## How far to verify a claim

A prose refresh runs *inside* the score re-read, one pass per product, described in
`docs/workflows/refresh-category.md`. The same repository, model card and vendor docs are
opened once and both halves are written from what they show, so prose carries no separate
research budget. The question left is what to do with claims outside the score's evidence:

| claim class | policy |
|---|---|
| what the product is and does | **verify**, the score re-read establishes it anyway |
| comparative positioning ("Where MCP …, A2A …") | **verify**, the same pages settle it |
| superlative or unsourced ranking | **delete** |
| corporate event (acquired / raised / IPO) | **omit** unless identity-bearing |
| curator rationale ("Picked when …") | **remove from `description`** |

A claim that the sources opened for the score do not settle, and that none of the rules above
disposes of, comes out of the prose. It is never left in unverified on the grounds that it was
already there.

A prose pass run on its own, with no re-read, is a *rewrite*, not a refresh: it may reword,
shorten and delete, and it may not add a fact the record does not already carry.

## Scored fields: do not restate them

The license is the clearest case. It is the openness score's basis, recorded in
`sources/scores/<slug>.yaml` as `openness.components`, with `sources[].accessed` behind it and
the invariant and the digest requirement in front of it. Restating it in `comments` or
`description` creates a second copy with none of that, and the two drift in one direction
only: a relicense flows through the score and the prose is quietly left wrong.

It also buys the reader nothing. The panel renders `openness.components` directly below the
prose, in larger type. So **read the LICENSE body, and do not write it into product prose.**
Reading it stays essential: the GitHub classifier lies (a custom copyright line makes a genuine
MIT repo report `NOASSERTION`), and the OSI call is what the score turns on. When the body
disagrees with the recorded score, that is a score finding: stop and follow
`evidence-and-freshness.md`.

The same applies to adoption, capability and the openness class. Prose describes; the axes
carry the judgment.

## Volatile facts: link, do not embed

Prose carries no freshness mechanism. `last_verified` gates scores, not `description` text, so
any fact in prose that a later event can invalidate is a liability with no owner.

**The test: would a future release make this sentence wrong?** If yes, it is volatile and does
not belong in `description` or `comments`. If a future release would instead be a different
product entry, or there will be no future release, the fact is durable and can stay.

**Counts.** A star, download or contributor count is stale the moment it is written. The
artifact URLs are the live link, and magnitude of use is the `adoption` axis, where the figure
sits with a date and a signal type. Prose may say the durable, qualitative shape of adoption
when it is a structural fact ("the distributed-training backbone for other Hugging Face
libraries"), sparingly, and never as a stand-in for a number.

**Current version and release date.** The next release makes it wrong. Three durable cases
stay: the version is the entry's identity (a named model release); there will be no future
release (an archived project's last version); a statement of absence ("no tagged releases,
built from source").

**Corporate events.** An acquisition, funding round or IPO is omitted unless it is
identity-bearing: it establishes who ships the product now, and a reader who did not know it
would look for the wrong vendor. "Predibase, now part of Rubrik" earns its clause; "raised a
$50M Series B" does not.

Where a version or an event bears on a *score*, it is score evidence with a `sources[].accessed`
date, not a prose clause.

## Prose has no date of its own

`last_verified` lives in the score file, per axis, and confirms that a *score* is still correct
and re-derivable from its sources. Only a person writes it, and only per the rules in
`evidence-and-freshness.md`. Nothing in prose earns one, and prose carries no date of its own:
the `comments` verification line that used to serve as one is retired, so a description ages
silently. That is acceptable because a prose refresh is coupled to the axis re-read in
`refresh-category.md`; it is not acceptable to write a date into prose to compensate. If a
prose re-read turns up a fact that moves a score, that is a score change: stop and follow
`evidence-and-freshness.md`.

## Rewriting a note or footnote: procedure

For a prose-only pass (the `clean-corpus-prose` skill automates it):

1. **Read the whole record**: all three notes, every `shows`, `components`, `comments`. The same
   argument often appears in two of them.
2. **Classify each note** against the goldens: already right (leave it), rubric vocabulary,
   restated figures, template opening, chronology, or over the length guard.
3. **Rewrite in the two-sentence shape**, from the facts the record already carries. Do not
   open a source, do not add a fact, do not remove a fact the argument needs.
4. **Move, do not lose.** A detail the note leaned on that no `shows` carries moves into the
   relevant `shows`. A vocabulary ruling or precedent moves into `docs/reference/`.
5. **Check the pinned phrases** (under-coverage, the date allowlist) survived verbatim, and that
   any peer named is in `relative_to`.
6. **Drop a `comments` footnote that restates a note.** Keep one that says something no other
   field does.
7. **Edit through `build/components.py`** (`set_field`, `set_source`, `set_document_field`),
   never a load-modify-dump and never a hand splice.
8. **Anything the pass may not fix, write down**: a note whose argument contradicts its score,
   a stale fact, a thin note the tail was hiding. The log goes on the PR; each entry is
   somebody's later `update-product`.

For a product refresh (the `update-product` and `refresh-category` skills):

1. **Open the primary sources** the product points at. Never refresh from memory.
2. **Re-derive the checkable facts**: what it does, who ships it, lifecycle state. Read the
   LICENSE body and the current release to confirm the project is alive and that neither has
   moved a score.
3. **Rewrite `description`** to the format above if anything material changed.
4. **Rewrite `comments`** to a footnote or to nothing. No verification line.
5. **Write each axis note** in the two-sentence shape, in the reader's vocabulary.
6. **If a fact moves a score**, follow `evidence-and-freshness.md`; do not edit the score from
   the product file.
7. **Validate:** `uv run python -m build.validate` prints `0 error(s)`; `uv run pytest
   tests/test_product_prose.py tests/test_score_notes.py` passes.

## Checklist

- [ ] `description`: 2 to 4 sentences, leads with the product doing something, present tense,
      neutral register, no marketing words, no counts, no current-version clause, no curator
      rationale, no corporate event, no license.
- [ ] `comments`: empty, or one footnote about our reading that no note or description carries.
      No `Verified … via` sentence.
- [ ] Each `note`: two sentences, what puts it here and what keeps it off the next rung, in
      words a reader who has never seen the rubric follows. No rung, band, level, ladder,
      anchor, formula or rule names. Figures rounded. Peers named and recorded in `relative_to`.
      No dates, no chronology. At or under 600 characters.
- [ ] Each `shows`: a short extract of the page, not a retelling of the note.
- [ ] The pinned under-coverage phrases and the date-allowlist dates are intact.
- [ ] No score, `last_verified`, URL, `accessed`, `http_status`, `content_sha256` or
      `establishes` moved.
- [ ] American English throughout.
- [ ] `uv run python -m build.validate` prints `0 error(s)`.

## Related

- `skills/clean-corpus-prose/SKILL.md`: the prose-only pass, one category per unit of work
- `skills/update-product/SKILL.md` and `skills/refresh-category/SKILL.md`: prose inside a re-read
- `docs/reference/evidence-and-freshness.md`: normative on how a score earns `last_verified`
- `docs/reference/openness.md` and `docs/reference/adoption.md`: the rulings the notes used to
  carry as vocabulary
- `docs/methodology.md`: the register these fields borrow
- `docs/schemas/product.schema.json` and `docs/schemas/score.schema.json`: the field definitions
- `tests/test_product_prose.py`, `tests/test_score_notes.py`: the guards
