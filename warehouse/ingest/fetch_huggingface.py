"""
Fetch Hugging Face models and datasets linked to tracked AI repos.

Approach: extract unique authors (GitHub orgs/users) from the GoodAI List,
then query HF for models and datasets by those authors. This gives us
the HF artifacts that are relevant to our ecosystem, not the full 2.8M dump.

Usage:
    uv run scripts/fetch_huggingface.py
"""

import csv
import sys
from pathlib import Path

from huggingface_hub import list_models, list_datasets

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "huggingface"
MODELS_CSV = DATA_DIR / "tracked_models.csv"
DATASETS_CSV = DATA_DIR / "tracked_datasets.csv"
TOP_MODELS_CSV = DATA_DIR / "top_models.csv"
TOP_DATASETS_CSV = DATA_DIR / "top_datasets.csv"

MODEL_FIELDS = [
    "model_id", "author", "downloads", "likes",
    "pipeline_tag", "library_name", "created_at", "last_modified", "tags",
]
DATASET_FIELDS = [
    "dataset_id", "author", "downloads", "likes",
    "created_at", "last_modified", "tags",
]


def get_tracked_authors() -> set[str]:
    """Extract unique GitHub orgs/users from GoodAI List via pyoso."""
    try:
        from pyoso import Client
        client = Client()
        df = client.to_pandas("""
            SELECT DISTINCT LOWER(SPLIT_PART(repo, '/', 1)) AS owner
            FROM currentai.goodailist_repos.repos
        """)
        authors = set(df["owner"].dropna().unique())
        print(f"Found {len(authors)} unique repo owners from GoodAI List")
        return authors
    except Exception as e:
        print(f"Warning: could not fetch authors from OSO ({e})")
        print("Falling back to top models/datasets by downloads")
        return set()


def fetch_models_by_authors(authors: set[str]) -> list[dict]:
    """Fetch HF models published by tracked authors."""
    rows = []
    total = len(authors)
    for i, author in enumerate(sorted(authors)):
        if i % 100 == 0:
            print(f"  Models: scanning author {i}/{total} ({len(rows)} found so far)")
        try:
            for m in list_models(author=author, sort="downloads", limit=100):
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


def fetch_datasets_by_authors(authors: set[str]) -> list[dict]:
    """Fetch HF datasets published by tracked authors."""
    rows = []
    total = len(authors)
    for i, author in enumerate(sorted(authors)):
        if i % 100 == 0:
            print(f"  Datasets: scanning author {i}/{total} ({len(rows)} found so far)")
        try:
            for d in list_datasets(author=author, sort="downloads", limit=100):
                rows.append({
                    "dataset_id": d.id or "",
                    "author": d.author or "",
                    "downloads": d.downloads or 0,
                    "likes": d.likes or 0,
                    "created_at": str(d.created_at or ""),
                    "last_modified": str(d.last_modified or ""),
                    "tags": ",".join(d.tags) if d.tags else "",
                })
        except Exception:
            pass
    rows.sort(key=lambda r: r["downloads"], reverse=True)
    return rows


def fetch_top(limit: int = 5000) -> tuple[list[dict], list[dict]]:
    """Fallback: fetch top models/datasets by downloads globally."""
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

    print(f"Fetching top {limit} datasets by downloads...")
    datasets = []
    for d in list_datasets(sort="downloads", limit=limit, full=True):
        datasets.append({
            "dataset_id": d.id or "",
            "author": d.author or "",
            "downloads": d.downloads or 0,
            "likes": d.likes or 0,
            "created_at": str(d.created_at or ""),
            "last_modified": str(d.last_modified or ""),
            "tags": ",".join(d.tags) if d.tags else "",
        })

    return models, datasets


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


def dedup_datasets(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in rows:
        if r["dataset_id"] not in seen:
            seen.add(r["dataset_id"])
            out.append(r)
    return out


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Hugging Face models and datasets.")
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

            print(f"\nFetching HF datasets for {len(authors)} tracked authors...")
            tracked_datasets = fetch_datasets_by_authors(authors)
            print(f"  Found {len(tracked_datasets)} datasets from tracked authors")

            write_csv(MODELS_CSV, tracked_models, MODEL_FIELDS)
            write_csv(DATASETS_CSV, tracked_datasets, DATASET_FIELDS)

    if not args.tracked_only:
        print("\nFetching top 1000 global models and datasets...")
        try:
            top_models, top_datasets = fetch_top(limit=1000)
            print(f"  Found {len(top_models)} top models, {len(top_datasets)} top datasets")
            write_csv(TOP_MODELS_CSV, top_models, MODEL_FIELDS)
            write_csv(TOP_DATASETS_CSV, top_datasets, DATASET_FIELDS)
        except Exception as e:
            print(f"  Warning: global top fetch failed ({e})")
            print("  Re-run with --top-only later.")

    print("\nDone.")


if __name__ == "__main__":
    main()
