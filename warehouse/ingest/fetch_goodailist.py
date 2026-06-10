#!/usr/bin/env python3
"""
Scraper for goodailist.com/repos
Fetches: summary, filters, settings, and all repos (paginated).
Outputs JSON files to the same directory as this script.
"""

import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib.request
import urllib.error

BASE_URL = "https://goodailist.com"
OUT_DIR = Path(__file__).resolve().parent.parent / "catalog" / "goodailist"
LIMIT = 1000  # max items per page (API allows up to 1000)
SORT_BY = "stars"
SORT_ORDER = "desc"
MAX_WORKERS = 5  # concurrent page fetches


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "goodailist-scraper/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_page(page: int) -> list:
    url = f"{BASE_URL}/api/repos?page={page}&limit={LIMIT}&sort_by={SORT_BY}&sort_order={SORT_ORDER}"
    data = fetch_json(url)
    return data["repos"]


def main():
    print("Fetching summary...")
    summary = fetch_json(f"{BASE_URL}/api/summary")
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"  total_repos={summary['total_repos']}, updated_at={summary['updated_at']}")

    print("Fetching filters...")
    filters = fetch_json(f"{BASE_URL}/api/repos/filters")
    (OUT_DIR / "filters.json").write_text(json.dumps(filters, indent=2))
    print(f"  categories={len(filters['categories'])}, subcategories={len(filters['subcategories'])}")

    print("Fetching settings...")
    settings = fetch_json(f"{BASE_URL}/settings.json")
    (OUT_DIR / "settings.json").write_text(json.dumps(settings, indent=2))

    # Discover total pages
    print("Fetching page 1 to determine total pages...")
    first_page_url = f"{BASE_URL}/api/repos?page=1&limit={LIMIT}&sort_by={SORT_BY}&sort_order={SORT_ORDER}"
    first = fetch_json(first_page_url)
    total_pages = first["pages"]
    total_repos = first["total"]
    print(f"  total repos from API: {total_repos}, pages: {total_pages}")

    all_repos = list(first["repos"])

    # Fetch remaining pages concurrently
    remaining = list(range(2, total_pages + 1))
    print(f"Fetching pages 2–{total_pages} ({len(remaining)} pages, {MAX_WORKERS} workers)...")

    page_results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(fetch_page, p): p for p in remaining}
        for future in as_completed(future_to_page):
            page = future_to_page[future]
            try:
                repos = future.result()
                page_results[page] = repos
                print(f"  page {page}/{total_pages} — {len(repos)} repos")
            except Exception as exc:
                print(f"  page {page} ERROR: {exc}")
                page_results[page] = []

    # Reassemble in order
    for page in range(2, total_pages + 1):
        all_repos.extend(page_results.get(page, []))

    print(f"\nTotal repos collected: {len(all_repos)}")

    out_path = OUT_DIR / "repos.json"
    out_path.write_text(json.dumps(all_repos, indent=2))
    print(f"Saved {len(all_repos)} repos → {out_path}")

    # Also write a CSV for easy spreadsheet access
    if all_repos:
        import csv
        csv_path = OUT_DIR / "repos.csv"
        fieldnames = list(all_repos[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_repos)
        print(f"Saved CSV → {csv_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
