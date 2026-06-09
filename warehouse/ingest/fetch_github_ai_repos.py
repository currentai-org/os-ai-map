#!/usr/bin/env python3
import os
import sys
import csv
import requests
import argparse

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

SEARCH_URL = "https://api.github.com/search/repositories"


def search_ai_repos(min_stars=500, max_results=100, output_file=None):
    query = f"topic:ai fork:true stars:>{min_stars}"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(100, max_results),
    }

    all_repos = []
    total_count = None
    page = 1

    while len(all_repos) < max_results:
        params["page"] = page
        params["per_page"] = min(100, max_results - len(all_repos))

        print(f"Fetching page {page}...", file=sys.stderr)
        resp = requests.get(SEARCH_URL, headers=HEADERS, params=params)

        if resp.status_code != 200:
            print(
                f"Error: {resp.status_code} - {resp.json().get('message', resp.text)}"
            )
            break

        data = resp.json()
        items = data.get("items", [])

        if not items:
            break

        total_count = data.get("total_count", 0)
        all_repos.extend(items)

        if len(items) < 100 or len(all_repos) >= total_count:
            break

        page += 1

    all_repos = all_repos[:max_results]

    print(
        f"Found {len(all_repos)} repositories (total available: {total_count or 'unknown'})"
    )

    print("\nTop 10 by stars:")
    print("-" * 80)
    for repo in sorted(all_repos, key=lambda r: r["stargazers_count"], reverse=True)[
        :10
    ]:
        desc = repo.get("description", "") or ""
        print(
            f"  {repo['stargazers_count']:>6,} | {repo['full_name']:<45} | {desc[:50]}"
        )

    if output_file and all_repos:
        fieldnames = [
            "full_name",
            "description",
            "stargazers_count",
            "forks_count",
            "language",
            "topics",
            "html_url",
            "created_at",
            "updated_at",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_repos)

        print(f"\nExported to {output_file}")

    return all_repos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search GitHub for forked AI repositories"
    )
    parser.add_argument(
        "--min-stars", type=int, default=500, help="Minimum stars (default: 500)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Max results to fetch (default: 100)",
    )
    default_output = str(Path(__file__).resolve().parent.parent / "data" / "goodailist" / "forked_ai_repos.csv")
    parser.add_argument("--output", type=str, default=default_output, help="Output CSV file path")

    args = parser.parse_args()

    repos = search_ai_repos(
        min_stars=args.min_stars, max_results=args.max_results, output_file=args.output
    )

    if not repos:
        print("No repositories found.", file=sys.stderr)
        sys.exit(1)
