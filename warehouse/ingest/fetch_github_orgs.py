"""
Fetch GitHub metadata for every org/user that maintains a repo in the GoodAI List.

Pulls unique owners from the GoodAI List via pyoso, then queries the GitHub API
for org/user profile metadata. Requires `gh` CLI to be authenticated.

Usage:
    uv run scripts/fetch_github_orgs.py
    uv run scripts/fetch_github_orgs.py --limit 100   # test with first 100
"""

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "github-orgs"
OUTPUT_CSV = DATA_DIR / "orgs.csv"

FIELDS = [
    "login", "name", "type", "description", "location",
    "public_repos", "followers", "following",
    "blog", "twitter_username", "email",
    "created_at", "updated_at",
    "repos_in_goodailist",
]


def get_owners_from_goodailist() -> dict[str, int]:
    """Get unique owners and their repo counts from GoodAI List."""
    from pyoso import Client
    client = Client()
    df = client.to_pandas("""
        SELECT
          LOWER(SPLIT_PART(repo, '/', 1)) AS owner,
          COUNT(DISTINCT LOWER(repo)) AS repo_count
        FROM currentai.goodailist_repos.repos
        GROUP BY LOWER(SPLIT_PART(repo, '/', 1))
        ORDER BY repo_count DESC
    """)
    return dict(zip(df["owner"], df["repo_count"]))


def fetch_github_user(login: str) -> dict | None:
    """Fetch a single GitHub user/org profile via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", f"users/{login}", "--jq", "."],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub org/user metadata.")
    parser.add_argument("--limit", type=int, default=None, help="Limit to N owners (for testing)")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading owners from GoodAI List...")
    owners = get_owners_from_goodailist()
    print(f"  Found {len(owners)} unique owners")

    if args.limit:
        owners = dict(list(owners.items())[:args.limit])
        print(f"  Limited to {len(owners)}")

    # Load existing data to skip already-fetched owners
    existing_logins = set()
    rows = []
    if OUTPUT_CSV.exists():
        import csv as csv_mod
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv_mod.DictReader(f)
            for row in reader:
                existing_logins.add(row["login"].lower())
                rows.append(row)
        print(f"  Loaded {len(rows)} existing entries, skipping those")

    total = len(owners)
    skipped = 0
    errors = 0
    new_fetched = 0

    for i, (login, repo_count) in enumerate(owners.items()):
        if i % 100 == 0:
            print(f"  Processing {i}/{total} ({new_fetched} new, {skipped} skipped, {errors} errors)")

        if login.lower() in existing_logins:
            skipped += 1
            continue

        data = fetch_github_user(login)
        if data is None:
            errors += 1
            continue

        new_fetched += 1
        rows.append({
            "login": data.get("login", login),
            "name": data.get("name", ""),
            "type": data.get("type", ""),
            "description": (data.get("bio") or data.get("description") or "").replace("\n", " ").replace("\r", " ").strip(),
            "location": (data.get("location") or "").replace("\n", " ").strip(),
            "public_repos": data.get("public_repos", 0),
            "followers": data.get("followers", 0),
            "following": data.get("following", 0),
            "blog": data.get("blog", ""),
            "twitter_username": data.get("twitter_username", ""),
            "email": data.get("email", ""),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
            "repos_in_goodailist": repo_count,
        })

        # GitHub API: 5000 req/hr authenticated, pace to stay safe
        if new_fetched % 500 == 499:
            print(f"  Pausing briefly to respect rate limits...")
            time.sleep(5)

    rows.sort(key=lambda r: int(r["repos_in_goodailist"]), reverse=True)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Wrote {len(rows)} orgs/users to {OUTPUT_CSV.name}")
    print(f"  New: {new_fetched}, Skipped (existing): {skipped}, Errors: {errors}")
    type_counts = {}
    for r in rows:
        t = r["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"  Types: {', '.join(f'{t}: {n}' for t, n in sorted(type_counts.items()))}")


if __name__ == "__main__":
    main()
