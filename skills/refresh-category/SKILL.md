---
name: refresh-category
description: Use when one category's products need re-verifying against primary sources — researching each product, auditing the evidence, applying scores and prose together, gating, and opening the category PR. Takes one category slug and finishes it, in os-ai-map.
---

# Refresh a Category

Takes one category from wherever it is to **gate-clean**, then opens a PR and stops. The unit is
the category because that is the unit a rubric, a stage and a reviewer all work in.

## How this composes

- **Runs `verify-product`'s procedure INSIDE the score re-read**, not beside it. That skill's
  boundary — prose only, never `last_verified` — holds when it is run alone. Here the same
  product gets both halves from one read, because refreshing the prose means opening the
  repository, model card and vendor docs the score re-read already fetches, and because a prose
  pass run on its own does not open primary sources at all. See `verification-pass.md` Phase 4.
- **Escalates to `build-rubric`** when a category's `components` values turn out to be prose
  rather than controlled tokens. That skill's step 0 is the test, and a category that fails it
  cannot be laddered no matter how well its products are read. Do not normalize a vocabulary
  inline as a side effect of a sweep.
- **Invoked by `refresh-all-categories`**, which decides which category is next. Run directly
  when you want a specific one.

## This file is orchestration only

Every rule about *how to verify* lives in the guides, and this skill restates none of them. Two
copies drift, and that is the exact failure the sweep exists to fix. If a rule needs changing,
change the guide. Never the prompt.

**You** read all of these before dispatching:

- `docs/reference/evidence-and-freshness.md` — how an axis earns `last_verified`, the invariant, the gates,
  and what a capability confirmation attests to
- `docs/reference/evidence-and-freshness.md` — what `last_verified` means
- `docs/reference/product-copy.md` — the prose spec and the claim-class table
- `docs/reference/identity.md` — slugs, aliases, and the combine rules when releases merge
- `docs/runbooks/verification-pass.md` Phase 4 — the per-product unit of work

**A research agent reads two**, and this matters more than it looks: every agent loads its
reading list before its first fetch, so the list is multiplied by the batch size. Telling all
twenty-two to read all nine documents cost 2,049 lines apiece and dominated the first run's
wall-clock.

- `docs/reference/product-copy.md` — it is writing the prose
- `docs/reference/evidence-and-freshness.md` — it is earning the date

Add `docs/reference/identity.md` only for a product whose slug covers a tier or family, where the
combine rules actually bite. Do not send the rest: `verification-pass.md` and this file are
orchestration, and the agent is not orchestrating; `verify-product` restates `product-copy.md`;
`evidence-and-freshness.md` is covered by `evidence-and-freshness.md` for a research agent's purposes; and the rubric
is unnecessary because preflight already computes the recorded dimensions and hands them over.
That is 866 lines instead of 2,049.

## Definition of done, per product

- every axis carries a real `last_verified`, or abstains deliberately, or the product is held;
- every source behind a claimed date records `http_status` and `content_sha256`;
- `description` and `comments` satisfy `product-copy.md`, with the canonical verification line;
- `capability.relative_to` + `relation` recorded where the note places the band against a peer.

A product whose evidence cannot be settled is **held**, not forced. Held is a legitimate
outcome; a date you cannot support is the failure this whole apparatus exists to prevent.

## Steps

### 1. Take the category, and decide which of its products are in scope

```bash
uv run python -m build.sweep_status --verbose                    # never confirmed
uv run python -m build.sweep_status --max-age-days 30 --verbose  # or confirmed too long ago
```

**Two modes, same machinery.** The first pass over a category takes every product that has
never been confirmed. After that the category is done until its confirmations age, and
`--max-age-days N` (or `--since YYYY-MM-DD`) reads anything older than the window as `stale`
rather than `verified`. Pass the same window the caller gave you, and refresh only what it
returns — re-reading a product confirmed last week costs a full unit of work and earns a date
it already had.

`last_verified` is a claim about a day, so a refresh window is the honest way to ask "is this
still true" without asking it of everything. The prose ages on the same clock, because the
canonical verification line carries its own date: a product can be score-fresh and prose-stale,
and `--verbose` distinguishes `stale` from `open` and `prose line stale` from
`no verification line`.

There is no default window. Absent one, "confirmed once" counts as confirmed, which is right
for the first pass and wrong forever after — so the caller chooses, and says why.

**Anchor first, and "already dated" is not enough.** If any product records
`capability.relative_to`, the peer must carry a confirmation dated **on or after the date this
run is claiming** — not merely some date. A derived band cannot be fresher than what it derives
from, so an anchor confirmed yesterday fails a band dated today, and `check_capability` catches
it. Put anchors at the front of the batch and date them in the same run.

Where that is impossible — the anchor sits in another category, or was confirmed in an earlier
run — tell the agents to **leave `relative_to` and `relation` unset and report it**, never to
substitute a different peer to satisfy the arithmetic. Three products did exactly that in
`finetuning_code` and their capability axes went to the queue, which is the correct outcome.

### 2. Preflight — gather once, centrally

Agents must not each rediscover this, and must not guess at it. A pilot run invented three
product slugs from a truncated terminal listing.

- The roster, from `sources/categories/<slug>.yaml`. Never retype it.
- Recorded openness dimensions per product, computed with the repo's own helpers
  (`build.check_verification.recorded_dimensions` over `build.rubrics.recipe_for`). Do not ask
  an agent to re-derive them, and do not paraphrase them into a brief.
- Warehouse signal rows for the whole category in **one** query — `signal_github.repo_state`,
  `signal_huggingface.hub_state`, `signal_pypi.package_downloads`. Read
  `sources/signal_routing.yaml` for which source governs which dimension, and respect its
  `never` routes: a GitHub license is a fact about the code, never about the weights.

### 3. Research — one agent per product

Dispatch a `Workflow`, one agent per product. Each agent reads the two guides above and its own
product's two files, fetches, and **edits no file** — it returns a packet.

**Concurrency is `min(16, cores - 2)`, not a number you choose.** On a six-core machine that is
four, so twenty-two products run in six waves. Size the expectation off the real cap rather than
the agent count, and remember the products with the fewest artifacts are the *slowest*: with no
repo to read, the license has to come from pricing pages and terms documents. Since categories
are ordered worst-coverage-first, the early ones are the slow ones.

**Put the cheap tier here and the expensive tier on the audit.** Research is bounded work:
fetch a URL, read a LICENSE body, decide whether a core is gated, draft sixty words. It is
careful rather than deep, and there are twenty-odd agents doing it. Auditing is the opposite —
adversarial reading, noticing that a `shows` describes something absent from the body it cites,
or that an asserted negative was searched for in a way that could not have found it — and there
are two agents doing it. Spend accordingly: cheap on the many, expensive on the few that check
them, and expensive on whatever is orchestrating.

That split is safe precisely because the audit re-verifies from the saved bodies rather than
trusting the packet, so it does not much care which model wrote one. The honest caveat is that
it does not buy as much at the research layer as the price suggests either: every defect the
audits have caught so far — the un-retried 429, the grep against a compressed archive, the
prose that dropped a true fact — was produced by the expensive tier. Watch the ratio of clean
to suspect verdicts when you change tiers, and change back if it moves.

Fetch **only** through `uv run python -m build.fetch_source --body-dir <scratch> <url>`, never
curl and never WebFetch, so the digest recorded is one the weekly sampled re-fetch can confirm.

Give every agent these. Each is a defect the pilot actually produced:

- **The four rules a pass may not bend** — `docs/runbooks/verification-pass.md`, Phase 4: digests,
  the three fetch fields traveling together, unreachable hosts, and `": "` in a plain scalar.
  Point the agent at that section rather than restating them here, or there are two copies to
  keep true.
- **A transient status is not an absence**, which is that section's third rule in
  `fetch_source`'s own terms. `fetch_source` retries and returns
  `"transient": true` with no digest when one survives. That means retry or defer. It never
  means the fact is missing. One un-retried 429 was promoted into the ground for a confirmation;
  the figure was there.
- **An asserted negative needs a stated method.** "A grep of the sdist found nothing" was
  claimed against a compressed `.tar.gz`. If you claim something is absent from an archive, say
  how you walked it, and walk it.
- **Quote verbatim or drop the quotation marks.** `shows` is the field whose whole job is
  letting someone else check the work.
- **Inventory the prose before rewriting it.** List every factual claim in the current
  `description` and `comments` and mark each keep / move / drop with a reason from
  `product-copy.md`. The commonest pilot defect was a rewrite that silently dropped a true,
  durable fact. Return the ledger.
- **One spelling per dimension** in `establishes`, using the recorded key, and only on openness
  unless the routing file gives the axis a vocabulary.

### 4. Audit — assume a rubber stamp

Auditors over the packets. They earn their cost: across the runs so far they have caught a false
confirmation built on an un-retried rate limit, two asserted negatives whose stated method could
not have produced them, a note carrying adopters absent from every body fetched that day, and
three products writing capability relations they could not support.

**Shard the evidence audit; keep the prose audit whole.** One agent re-fetching every digest
across a whole category is both slow and fragile — it died mid-response on the first attempt at
22 products, and a died audit means either re-running it or shipping unverified. Four shards
striped across the packets, each running the same checks on its slice, is robust and parallel.
The prose audit stays single because it needs to compare the batch against itself: it caught two
products in one run treating identical vendor language differently, which no per-slice agent
could see.

**Put the expensive model tier here.** See the note in step 3.

- **Evidence.** Re-fetch every digest and compare. Grep every `shows` against the saved body.
  Check the invariant per recorded dimension. Check no 4xx is used as evidence. Check
  `body_path` decodes to its own source's URL.
- **Prose.** Check the fact ledger against the *current* file — a durable fact that vanished
  without a ledger entry is the defect. Check the claim-class table, the length band, and the
  canonical line.

A `failed` verdict means hold the product. A `suspect` verdict with specific corrections means
apply the corrections. Do not re-run automatically: a second attempt on a systemic prompt defect
just fails twice.

### 5. Apply — deterministically, never by an agent

A script, not a model. `sources/` YAML is hand-wrapped and does not round-trip: use
`build.components` (`set_field`, `put_field`, `set_document_field`), which asserts on reparse
that the edit did what was asked and touched nothing else.

**An auditor's replacement text arrives in three shapes** and the applier has to parse rather
than assume: a bare value, a single `description: ...` line, and a YAML fragment carrying both
prose fields at once. Writing a fragment in as a value nests the key inside itself. That shipped
on seven products in one run and was caught by
`tests/test_components.py::test_every_product_file_round_trips_through_its_own_description`,
which is worth running before the full suite for exactly this reason.

**An axis the audit disputes does not get dated.** Where the evidence does not support what the
packet claimed, the axis goes to the queue with the reason. Never date it and leave the disputed
clause standing — that is a confirmation of something nobody confirmed.

Unsettled axes go to `sources/verification_queue.yaml`, the product otherwise untouched:

```yaml
held:
  llama-factory:
    adoption:
      since: '2026-08-09'
      because: >-
        PyPI downloads fell ~90% while stars, forks and named enterprise adopters all grew.
        Likelier a packaging change than a collapse; banding either way today records a guess.
```

Per axis, not per product — a product with two axes settled and one disputed is neither done nor
held. Data, not a PR comment nobody re-reads, and an entry earns its place by naming what would
settle it.

### 6. Gate

```bash
uv run python -m build.validate
uv run python -m build.check_verification --verbose
uv run python -m build.check_capability
uv run python -m build.check_recipe
uv run python -m build.check_adoption --strict
uv run python -m build.check_refetch --product <one you just wrote>
uv run python -m build.check_freshness --category <slug>
uv run python -m pytest tests/ -q
```

This is the canonical list for a category batch; the runbook's Phase 4 points at it rather than
carrying a second copy. `validate` must print `0 error(s)`, `check_verification` must report all
three gates OK, and `check_adoption --strict` must exit 0. **Do not commit while a gate is
failing** — report the failure instead.

Expect gates to **fail first and tell you something**. On the pilot, `validate` rejected an
`establishes` naming a components key no ladder reads, and `check_recipe` demanded a stale
deferral be removed because the product it deferred now reproduced. Both were right. Read a
failure before working around it.

`check_refetch` confirming a digest is the positive evidence the sweep is real. Quote the count.

Never commit `build/notebook_data.json` or `notebooks/` — bot-owned, and `generated-files-guard`
fails the PR.

### 7. PR, then stop

One PR for the category. Itemize every moved score with its evidence, every held product with
its reason, and the re-fetch confirmations. Then stop: a human merges.

## Cost, measured

`finetuning_code`, 22 products, 2026-08-09: **about 50 minutes end to end** at a concurrency cap
of four, median 7 fetches per product and a tail to 31 where the citations had rotted. The audit
adds roughly half as long again, because it re-fetches every digest.

Budget by the tail rather than the median, and expect the *early* categories to be the slowest:
they are ordered worst-artifact-coverage first, and a product with no repo needs more reading,
not less.

## Boundaries

- Read-only on the warehouse. No MCP writes, no uploads.
- Edits `sources/` only, and only for products in the named category.
- Does not clear deferrals, split a type, restructure `openness.components` (string or
  structured mapping — edit only via `build/components.py`, never by hand), or change a
  ladder. Each is its own project. If the sweep surfaces evidence for one, record it and
  carry on.

## Related

- `skills/verify-product/SKILL.md` — the prose half, run inside this
- `skills/build-rubric/SKILL.md` — when a category's values are not ladderable
- `skills/refresh-all-categories/SKILL.md` — the driver that picks the next category
