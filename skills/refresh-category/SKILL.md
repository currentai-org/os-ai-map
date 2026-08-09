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
copies drift, and that is the exact failure the sweep exists to fix. The agents you dispatch
read these, and so should you before dispatching them:

- `docs/guides/verification.md` — how an axis earns `last_verified`, the invariant, the gates,
  and what a capability confirmation attests to
- `docs/guides/freshness.md` — what `last_verified` means
- `docs/guides/product-info.md` — the prose spec and the claim-class table
- `docs/guides/identity.md` — slugs, aliases, and the combine rules when releases merge
- `docs/runbooks/verification-pass.md` Phase 4 — the per-product unit of work

If a rule needs changing, change the guide. Never the prompt.

## Definition of done, per product

- every axis carries a real `last_verified`, or abstains deliberately, or the product is held;
- every source behind a claimed date records `http_status` and `content_sha256`;
- `description` and `comments` satisfy `product-info.md`, with the canonical verification line;
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

**Anchor first.** If any product records `capability.relative_to`, the peer it points at must be
verified in this run or already dated — a derived band cannot be fresher than what it derives
from, and `check_capability` fails if it is. Put anchors at the front. In `finetuning_code` that
was `megatron-lm`, which twelve notes place themselves against.

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

Dispatch a `Workflow`, one agent per product, roughly ten concurrent. Each agent reads the guides
above and its own product's two files, fetches, and **edits no file** — it returns a packet.

Fetch **only** through `uv run python -m build.fetch_source --body-dir <scratch> <url>`, never
curl and never WebFetch, so the digest recorded is one the weekly sampled re-fetch can confirm.

Give every agent these. Each is a defect the pilot actually produced:

- **A transient status is not an absence.** `fetch_source` retries and returns
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
  `product-info.md`. The commonest pilot defect was a rewrite that silently dropped a true,
  durable fact. Return the ledger.
- **One spelling per dimension** in `establishes`, using the recorded key, and only on openness
  unless the routing file gives the axis a vocabulary.

### 4. Audit — assume a rubber stamp

Two auditors over the packets. They earn their cost: on the pilot they caught a false
confirmation, a false negative, and three products writing capability relations they could not
support.

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

Held products go to `sources/verification_queue.yaml`, otherwise untouched:

```yaml
held:
  predibase:
    category: finetuning_code
    since: '2026-08-08'
    because: >-
      Adoption evidence rests on an asserted negative its own saved body contradicts.
```

Data, not a PR comment nobody re-reads.

### 6. Gate

```bash
uv run python -m build.validate
uv run python -m build.check_verification --verbose
uv run python -m build.check_capability
uv run python -m build.check_recipe
uv run python -m build.check_refetch --product <one you just wrote>
uv run python -m build.check_freshness --category <slug>
uv run python -m pytest tests/ -q
```

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

`finetuning_code`, 2026-08-08: **5–10 fetches and about 15 minutes per product**, with a tail
where the citations have rotted — `predibase` took 25 fetches because all four of its cited URLs
were dead or blocked. Budget by the tail, not the median.

## Boundaries

- Read-only on the warehouse. No MCP writes, no uploads.
- Edits `sources/` only, and only for products in the named category.
- Does not clear deferrals, split a type, restructure `openness.components`, or change a ladder.
  Each is its own project. If the sweep surfaces evidence for one, record it and carry on.

## Related

- `skills/verify-product/SKILL.md` — the prose half, run inside this
- `skills/build-rubric/SKILL.md` — when a category's values are not ladderable
- `skills/refresh-all-categories/SKILL.md` — the driver that picks the next category
