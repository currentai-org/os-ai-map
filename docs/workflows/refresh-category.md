# Refresh a category

Take one category from wherever it is to **gate-clean**, then open a PR and stop. The unit is
the category because that is the unit a rubric, a stage, and a reviewer all work in. The
`refresh-category` skill drives this with a fan-out of research agents; this document is the
procedure it follows, and the authority when the two disagree.

## Use this when
A category's products need re-verifying against primary sources — scores and prose together —
because they were never confirmed or their confirmations have aged past the window. For a
single product, use [`update-product.md`](update-product.md). For an axis-wide schema change,
[`migrate-axis.md`](migrate-axis.md).

## Inputs you need
- The category **slug**.
- A **refresh window** (`--max-age-days N` or `--since`). There is no default: absent one,
  "confirmed once" counts as confirmed, which is right for a first pass and wrong forever after.
  The caller chooses and says why.

## Files this changes
`sources/products/*.yaml` and `sources/scores/*.yaml` for products in the named category, and
`sources/verification_queue.yaml` for any axis held back. Nothing outside the category.

## Definition of done, per product
- every axis carries a real `last_verified`, or abstains deliberately, or the product is **held**;
- every source behind a claimed date records `http_status` and `content_sha256`;
- `description` and `comments` satisfy [`../reference/product-copy.md`](../reference/product-copy.md),
  with the canonical verification line;
- `capability.relative_to` + `relation` recorded where the note places the band against a peer.

A product whose evidence cannot be settled is **held**, not forced. A date you cannot support is
the exact failure this apparatus exists to prevent.

## Procedure
1. **Scope.** `build.sweep_status --verbose` for never-confirmed; `--max-age-days N` for aged.
   Refresh only what the window returns.
2. **Anchor first.** If any product records `capability.relative_to`, its peer must carry a
   confirmation dated **on or after** the date this run claims — `check_capability` enforces it.
   Put anchors at the front and date them in the same run. Where the peer is in another category
   or an earlier run, leave `relative_to`/`relation` unset and report it; never substitute a
   different peer to satisfy the arithmetic.
3. **Preflight, gathered once.** The roster from the category file (never retyped); the recorded
   openness dimensions per product from the repo's own helpers; the warehouse signal rows for the
   whole category in one query. Respect `signal_routing.yaml`'s `never` routes.
4. **Research, then audit, then apply.** Research each product against primary sources (fetch
   only through `build.fetch_source` so the digest is one the weekly re-fetch can confirm). Audit
   the packets adversarially — assume a rubber stamp; re-fetch every digest, grep every `shows`
   against the saved body, check the invariant per dimension. Apply deterministically with
   `build.components`, never by hand — the YAML does not round-trip. A disputed axis is **not
   dated**; it goes to `sources/verification_queue.yaml` with the reason that would settle it.
   (The `refresh-category` skill carries the agent fan-out, concurrency, and model-tiering for
   these three stages.)

## The per-product unit of work
The unit is the product, not the axis, because prose and scores come from the same read:

1. **Read what the warehouse already has** before fetching — the signal row carries
   `http_status`, `license_*`, `is_archived`, `is_gated`, `downloads_30d`, `fetched_at`.
2. **Fetch each cited URL** a signal does not cover; record `http_status`, `content_sha256`, and
   a `shows` extract that actually appears in the body. A cited URL that 404s is a finding; so is
   a cited figure that no longer appears on a page that still returns 200.
3. **Re-derive each recorded dimension and attribute it** with `establishes: [...]`. On
   capability, record the peer comparison as `relative_to` + `relation` and confirm the peer at
   least as recently.
4. **Rewrite the prose** per [`../reference/product-copy.md`](../reference/product-copy.md) —
   `description` load-bearing and within the length band, `comments` ending in the canonical
   verification line. Delete rather than research a superlative, a corporate event, or a curator
   rationale clause.
5. **If a value moved, that is the valuable output** — fix the score and say why in `note`.
6. **Stamp `last_verified` only once every recorded dimension has an establishing source.**
   Otherwise `deferred` with a real reason. Never both, never silently absent.

### Four rules a pass may not bend
Each is a defect this project shipped, not a precaution against one.

1. **Never invent a digest.** Only `build.fetch_source` produces a `content_sha256`, and it
   prints all 64 characters. Three were once fabricated by padding truncated prefixes. If a URL
   cannot be fetched, record no digest and leave the axis undated.
2. **`accessed`, `http_status` and `content_sha256` travel together** on the same source. A
   fresh `accessed` with nothing under it fails `check_verification`.
3. **An unreachable host says nothing about whether the fact is true.** A 403/429/dead URL means
   the axis stays undated and the host is reported. It never means the value is wrong.
4. **A plain YAML scalar cannot contain `": "`.** Write ` - ` or single-quote the whole scalar.
   This cost four parse failures in one day.

A **null axis is a finding and earns a date too**: re-read the page, confirm nothing has
appeared, and date it, citing the page that publishes nothing. See
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md).

## Validation
The canonical gate list for a category batch — run all of it, not a remembered subset:
```bash
uv run python -m build.validate                       # 0 error(s)
uv run python -m build.check_verification --verbose   # all three gates OK
uv run python -m build.check_capability
uv run python -m build.check_recipe
uv run python -m build.check_adoption --strict        # exits 0
uv run python -m build.check_refetch --product <one you just wrote>
uv run python -m build.check_freshness --category <slug>
uv run python -m pytest tests/ -q
```
Expect gates to fail first and tell you something — read the failure before working around it.
Never commit while a gate is failing. Never commit `build/notebook_data.json` or `notebooks/`.

## Expected PR contents
One PR for the category: every moved score with its evidence, every held product with its
reason, and the re-fetch confirmation count. Then stop — a human merges.

## Stop and escalate when
- A category's `components` values are prose rather than controlled tokens → escalate to
  `build-rubric`; do not normalize a vocabulary inline as a side effect of a sweep.
- The sweep surfaces a reason to clear a deferral, split a type, or change a ladder → record it
  and carry on. Each is its own project.

## Standing hazards
Every one of these has happened; they are not hypotheticals.

| hazard | tell | guard |
|---|---|---|
| Derived date sold as a confirmation | any aggregate of `accessed` reaching `last_verified` | the invariant validates, never derives |
| Fabricated digest | a full-length `content_sha256` on a source nobody could fetch | only `build.fetch_source` produces one; the sampled re-fetch compares it |
| A re-dated source with nothing under it | a fresh `accessed`, no `http_status`/`content_sha256` | `check_verification`'s digest requirement |
| A parse failure from `": "` in a scalar | `validate` cannot read a file the pass just wrote | write ` - `, or single-quote the whole scalar |
| Parallel agents sharing a scratch directory | a fetch log or helper script rewritten mid-run | one private subdirectory per category |
| A 404 read as a product being gone | a retirement resting on one dead URL | check the URL first (`arduino/app-lab` 404s; `arduino/arduino-app-lab` is public) |
| A marketing reorg read as a withdrawal | the vendor site stops listing it; the docs still ship it | check the docs site (snorkel-flow was nearly retired while docs had it live) |
| Stale warehouse read | identical query text returning a pre-materialization answer | the nonce helper in `build/warehouse.py` |
| Partial coverage overstating openness | most-restrictive over a subset of SKUs | already in the SQL: `skus_mapped = skus_reachable AND tiers_seen <= 1` |
| Bot-owned files in a PR | `generated-files-guard` fails | edit `sources/` only; the bot regenerates on merge |
| British spelling | `licence`, `penalised`, `labelled` | American English everywhere, including identifiers |

## Relevant reference material
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../reference/product-copy.md`](../reference/product-copy.md) ·
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/capability.md`](../reference/capability.md) ·
[`../operations/deploy-models.md`](../operations/deploy-models.md)
