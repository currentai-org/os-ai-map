# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""Citation counts for products that have a paper, via Semantic Scholar.

Roster comes from `currentai.registry.product_artifacts` where `artifact_kind =
'arxiv'`, so the repo decides which products have a canonical paper and this model
only measures them. As of 2026-07-28 that is 23 products, all benchmarks.

Why citations, for benchmarks specifically. Downloads measure a benchmark badly —
its reach is how many papers evaluate against it, not how many people pulled the
files. Citations are the closest available proxy, and for this category they are
arguably a better adoption signal than anything else we collect.

## Why Semantic Scholar and not OpenAlex

OpenAlex was tried first and rejected on evidence, 2026-07-28. Two disqualifying
problems, both silent:

  1. **Wrong papers.** OpenAlex resolves `10.48550/arXiv.<id>` to the wrong work
     for some ids. `2105.09938` (APPS) returned "GPT-Neo", `2310.06770`
     (SWE-bench) returned a 2025 coding-agents paper, `2406.19314` (LiveBench)
     returned "AI Benchmark Half-Life". 3 of 23 wrong, 1 missing, and every wrong
     answer looked entirely plausible in a table.
  2. **Preprint-only counts.** OpenAlex keeps the arXiv preprint and the published
     version as separate works with no linking field, so a DOI lookup returns
     preprint citations only. GSM8K came back as 23 against a real ~9,800. The
     shortfall is not a constant factor, so it inverts the ranking too: OpenAlex
     put HumanEval above MMLU when the truth is the reverse. That kills even
     within-set comparison, which was the one defensible use.

Semantic Scholar merges versions, accepts an arXiv id directly, and returned all
23 correctly in a single batch request.

## What the numbers are

`citation_count` is the merged all-versions total, comparable to a figure quoted
anywhere else. `influential_citation_count` is Semantic Scholar's subset for
citations that actually build on the work rather than mention it in passing —
useful because a benchmark accumulates a long tail of one-line mentions.

`paper_title` is returned so identity stays auditable in SQL. If it ever drifts
from the product's expected paper, that is the OpenAlex failure recurring here and
the row should not be trusted.

The batch endpoint takes up to 500 ids per POST, so the whole roster is one
request. Requests are authenticated with SEMANTIC_SCHOLAR_TOKEN (x-api-key) as of
2026-08-26: the anonymous pool is shared across all unauthenticated callers from
the same egress, and it starved nine consecutive runs with 429s on a single
24-id POST before this model got its own allowance. Even keyed
requests get load-shed 429s at times, and the keyed allowance is one request per
second, so batch POSTs are paced a second apart and each retries 429s with an
exponential backoff (15s doubling to 120s, five attempts). Per-paper GETs are
still avoided; one batch request per run is the contract either way.
"""

import asyncio
import json
from datetime import datetime, timezone

import oso
import pyarrow as pa

BATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
FIELDS = "title,citationCount,influentialCitationCount,year,externalIds,publicationTypes"
BATCH_SIZE = 400

ROSTER_QUERY = """
SELECT product_slug, artifact_id
FROM "currentai"."registry"."product_artifacts"
WHERE artifact_kind = 'arxiv'
"""


def _entries(payload: object) -> list[object]:
    """The batch endpoint returns a bare list, positionally aligned to the input,
    with null where a paper was not found.

    Appended element by element rather than returned directly: narrowing `object`
    with isinstance gives `list[Unknown]`, which the release type check rejects
    against a `list[object]` annotation.
    """
    out: list[object] = []
    if isinstance(payload, list):
        for entry in payload:
            out.append(entry)
    return out


def _int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _text(value: object) -> str | None:
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


def _external_id(entry: dict, key: str) -> str | None:
    external = entry.get("externalIds")
    if not isinstance(external, dict):
        return None
    return _text(external.get(key))


def _build_table(rows: list[dict], stamp: datetime) -> pa.Table:
    def col(name: str, kind: pa.DataType) -> pa.Array:
        return pa.array([r.get(name) for r in rows], type=kind)

    return pa.table(
        {
            "product_slug": col("product_slug", pa.string()),
            "arxiv_id": col("arxiv_id", pa.string()),
            "paper_id": col("paper_id", pa.string()),
            "doi": col("doi", pa.string()),
            "paper_title": col("paper_title", pa.string()),
            "publication_year": col("publication_year", pa.int64()),
            "citation_count": col("citation_count", pa.int64()),
            "influential_citation_count": col("influential_citation_count", pa.int64()),
            "found": col("found", pa.bool_()),
            "fetched_at": pa.array([stamp] * len(rows), type=pa.timestamp("us")),
        }
    )


@oso.model(
    depends_on=["currentai.registry.product_artifacts"],
    external_origins=["https://api.semanticscholar.org"],
    capabilities=oso.Capabilities(fetch=True),
    secrets=["SEMANTIC_SCHOLAR_TOKEN"],
    environment_name="Default",
)
async def paper_citations(context: oso.AsyncContext) -> oso.DataFrame:
    token: str = await context.secret("SEMANTIC_SCHOLAR_TOKEN")
    roster_result = await context.query(ROSTER_QUERY)
    roster = await roster_result.as_pl()
    pairs = [
        (str(slug), str(arxiv))
        for slug, arxiv in zip(roster["product_slug"], roster["artifact_id"])
        if slug is not None and arxiv is not None
    ]
    if not pairs:
        raise RuntimeError(
            "no arxiv artifacts in currentai.registry.product_artifacts; "
            "the registry publish step may not have run"
        )

    rows: list[dict] = []
    for start in range(0, len(pairs), BATCH_SIZE):
        if start:
            # Semantic Scholar allows one request per second per key; pace
            # successive batch POSTs rather than burst them.
            await asyncio.sleep(1)
        batch = pairs[start : start + BATCH_SIZE]
        body = json.dumps({"ids": [f"arXiv:{arxiv}" for _, arxiv in batch]})
        # Semantic Scholar load-sheds with 429 even on keyed requests, so each
        # batch POST gets an exponential backoff (15s, 30s, 60s, 120s) before the
        # run gives up. Any other non-200 still fails loudly.
        for attempt in range(5):
            response = await context.fetch(
                f"{BATCH_URL}?fields={FIELDS}",
                method="POST",
                headers={"Content-Type": "application/json", "x-api-key": token},
                body=body,
            )
            if response.status != 429 or attempt == 4:
                break
            await asyncio.sleep(15 * 2 ** attempt)
        if response.status != 200:
            raise RuntimeError(
                f"semantic scholar batch returned {response.status} "
                f"for {len(batch)} ids"
            )

        entries = _entries(response.json())
        if len(entries) != len(batch):
            raise RuntimeError(
                f"semantic scholar returned {len(entries)} entries for {len(batch)} "
                "ids; the batch endpoint is positional, so a length mismatch means "
                "results cannot be safely rejoined to products"
            )

        # Positional alignment is the batch endpoint's contract, and the length
        # check above is what makes relying on it safe. Every product gets a row,
        # found or not, so coverage is visible in SQL rather than needing a diff
        # against the registry.
        for (slug, arxiv), entry in zip(batch, entries):
            if not isinstance(entry, dict):
                rows.append({"product_slug": slug, "arxiv_id": arxiv, "found": False})
                continue
            rows.append(
                {
                    "product_slug": slug,
                    "arxiv_id": arxiv,
                    "paper_id": _text(entry.get("paperId")),
                    "doi": _external_id(entry, "DOI"),
                    "paper_title": _text(entry.get("title")),
                    "publication_year": _int(entry.get("year")),
                    "citation_count": _int(entry.get("citationCount")),
                    "influential_citation_count": _int(
                        entry.get("influentialCitationCount")
                    ),
                    "found": True,
                }
            )

    stamp = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    return _build_table(rows, stamp)
