"""
Fetch data from the AI Incident Database (https://incidentdatabase.ai/)
and save as CSV.

Uses the Gatsby page-data endpoint which contains all incidents with
entity references. The AIID GraphQL API restricts access to browser
clients only, so we use the pre-rendered page data instead.
"""

import csv
import json
import sys
from pathlib import Path

import requests

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "ai-incidents" / "incidents.csv"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Gatsby pre-rendered page data — contains all incidents + entity lookup
PAGE_DATA_URL = "https://incidentdatabase.ai/page-data/apps/incidents/page-data.json"


def fetch_incidents():
    """Fetch all incidents from the AIID Gatsby page-data endpoint."""
    print(f"Fetching incidents from {PAGE_DATA_URL}")
    resp = requests.get(PAGE_DATA_URL, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    result = data["result"]["data"]

    incidents = result["incidents"]["nodes"]
    entities = result["entities"]["nodes"]

    # Build entity slug -> display name lookup
    entity_map = {e["id"]: e["name"] for e in entities}

    print(f"  Found {len(incidents)} incidents, {len(entities)} entities")
    return incidents, entity_map


def resolve_entities(slugs, entity_map):
    """Convert entity slug list to semicolon-separated display names."""
    if not slugs:
        return ""
    names = [entity_map.get(s, s) for s in slugs]
    return "; ".join(names)


def write_csv(incidents, entity_map):
    """Write incidents to CSV with resolved entity names."""
    fieldnames = [
        "incident_id",
        "title",
        "date",
        "description",
        "alleged_deployer",
        "alleged_developer",
        "alleged_harmed_party",
        "tags",
    ]

    rows = []
    for inc in incidents:
        desc = inc.get("description", "") or ""
        if len(desc) > 500:
            desc = desc[:497] + "..."

        row = {
            "incident_id": inc.get("incident_id", ""),
            "title": inc.get("title", ""),
            "date": inc.get("date", ""),
            "description": desc,
            "alleged_deployer": resolve_entities(
                inc.get("Alleged_deployer_of_AI_system"), entity_map
            ),
            "alleged_developer": resolve_entities(
                inc.get("Alleged_developer_of_AI_system"), entity_map
            ),
            "alleged_harmed_party": resolve_entities(
                inc.get("Alleged_harmed_or_nearly_harmed_parties"), entity_map
            ),
            # Tags: use implicated_systems if available (entity slugs)
            "tags": ", ".join(
                entity_map.get(s, s)
                for s in (inc.get("implicated_systems") or [])
            ),
        }
        rows.append(row)

    # Sort by incident_id
    rows.sort(key=lambda r: int(r["incident_id"]) if str(r["incident_id"]).isdigit() else 0)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} incidents to {OUTPUT_PATH}")
    return rows


def main():
    try:
        incidents, entity_map = fetch_incidents()
    except Exception as e:
        print(f"Failed to fetch incidents: {e}", file=sys.stderr)
        sys.exit(1)

    rows = write_csv(incidents, entity_map)

    # Print summary
    print(f"\nSummary:")
    print(f"  Total incidents: {len(rows)}")
    dates = [r["date"] for r in rows if r["date"]]
    if dates:
        print(f"  Date range: {min(dates)} to {max(dates)}")
    with_deployer = sum(1 for r in rows if r["alleged_deployer"])
    with_developer = sum(1 for r in rows if r["alleged_developer"])
    print(f"  With deployer info: {with_deployer}")
    print(f"  With developer info: {with_developer}")

    # Show sample rows
    print(f"\nFirst 5 incidents:")
    for row in rows[:5]:
        print(f"  #{row['incident_id']}: {row['title'][:70]}")
        print(f"    Date: {row['date']}  Deployer: {row['alleged_deployer'][:50]}")


if __name__ == "__main__":
    main()
