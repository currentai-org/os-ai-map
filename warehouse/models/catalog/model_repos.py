"""
Fetch the Hugging Face models linked to tracked AI repos.

Approach: extract unique authors (GitHub orgs/users) from the GoodAI List, then query HF for
models by those authors. That gives the HF artifacts relevant to this ecosystem rather than
the full 2.8M dump.

Its two CSVs are not uploaded anywhere. They are the input list that
`model_benchmarks.py` scans to build `model_repos.csv`, which IS uploaded and which
`entities/models.sql` reads. That is the whole reason this fetcher still exists.

It fetched HF DATASETS too until 2026-08-16. Those two CSVs loaded into no static model and
were read by nothing — four months of weekly author scans producing a file with no consumer.

Usage:
    uv run python warehouse/models/catalog/model_repos.py
"""

import csv
import sys
import time
from pathlib import Path

from huggingface_hub import list_models

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "catalog"
MODELS_CSV = DATA_DIR / "tracked_models.csv"
TOP_MODELS_CSV = DATA_DIR / "top_models.csv"

MODEL_FIELDS = [
    "model_id", "author", "downloads", "likes",
    "pipeline_tag", "library_name", "created_at", "last_modified", "tags",
]
def get_tracked_authors() -> set[str]:
    """Extract unique GitHub orgs/users from GoodAI List via pyoso."""
    try:
        from pyoso import Client
        client = Client()
        df = client.to_pandas("""
            SELECT DISTINCT LOWER(SPLIT_PART(repo, '/', 1)) AS owner
            FROM currentai.signal_goodailist.repo_catalog
        """)
        authors = set(df["owner"].dropna().unique())
        print(f"Found {len(authors)} unique repo owners from GoodAI List")
        return authors
    except Exception as e:
        print(f"Warning: could not fetch authors from OSO ({e})")
        print("Falling back to top models by downloads")
        return set()


# HF's api rate limit is 10K requests per 300s window. Pace calls (~20/s) and
# retry on 429 so fast runners (CI) don't silently drop authors.
RATE_SLEEP = 0.05


def _throttled(thunk):
    for attempt in range(5):
        time.sleep(RATE_SLEEP)
        try:
            return thunk()
        except Exception as e:
            if "429" in str(e) and attempt < 4:
                print("  429 rate limited; sleeping 60s")
                time.sleep(60)
                continue
            raise


def fetch_models_by_authors(authors: set[str]) -> list[dict]:
    """Fetch HF models published by tracked authors."""
    rows = []
    total = len(authors)
    for i, author in enumerate(sorted(authors)):
        if i % 100 == 0:
            print(f"  Models: scanning author {i}/{total} ({len(rows)} found so far)")
        try:
            for m in _throttled(lambda: list(list_models(author=author, sort="downloads", limit=100))):
                rows.append({
                    "model_id": m.id or "",
                    "author": m.author or "",
                    "downloads": m.downloads or 0,
                    "likes": m.likes or 0,
                    "pipeline_tag": m.pipeline_tag or "",
                    "library_name": m.library_name or "",
                    "created_at": str(m.created_at or ""),
                    "last_modified": str(m.last_modified or ""),
                    "tags": ",".join(m.tags) if m.tags else "",
                })
        except Exception:
            pass
    rows.sort(key=lambda r: r["downloads"], reverse=True)
    return rows


def fetch_top(limit: int = 5000) -> list[dict]:
    """Fallback: fetch top models by downloads globally."""
    print(f"Fetching top {limit} models by downloads...")
    models = []
    for m in list_models(sort="downloads", limit=limit, full=True):
        models.append({
            "model_id": m.id or "",
            "author": m.author or "",
            "downloads": m.downloads or 0,
            "likes": m.likes or 0,
            "pipeline_tag": m.pipeline_tag or "",
            "library_name": m.library_name or "",
            "created_at": str(m.created_at or ""),
            "last_modified": str(m.last_modified or ""),
            "tags": ",".join(m.tags) if m.tags else "",
        })

    return models


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    if not rows:
        print(f"  No rows for {path.name}")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows)} rows to {path.name}")


def dedup_models(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in rows:
        if r["model_id"] not in seen:
            seen.add(r["model_id"])
            out.append(r)
    return out


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Hugging Face models.")
    parser.add_argument("--top-only", action="store_true", help="Only fetch top 1K global (skip author scan)")
    parser.add_argument("--tracked-only", action="store_true", help="Only fetch tracked authors (skip top 1K)")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not args.top_only:
        authors = get_tracked_authors()
        if authors:
            print(f"\nFetching HF models for {len(authors)} tracked authors...")
            tracked_models = fetch_models_by_authors(authors)
            print(f"  Found {len(tracked_models)} models from tracked authors")

            write_csv(MODELS_CSV, tracked_models, MODEL_FIELDS)

    if not args.tracked_only:
        print("\nFetching top 1000 global models...")
        try:
            top_models = fetch_top(limit=1000)
            print(f"  Found {len(top_models)} top models")
            write_csv(TOP_MODELS_CSV, top_models, MODEL_FIELDS)
        except Exception as e:
            print(f"  Warning: global top fetch failed ({e})")
            print("  Re-run with --top-only later.")

    print("\nDone.")


if __name__ == "__main__":
    main()
