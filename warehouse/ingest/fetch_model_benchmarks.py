"""
Fetch model benchmarks and model→repo links from Hugging Face.

Outputs:
  warehouse/catalog/huggingface/model_benchmarks.csv  — Open LLM Leaderboard v2 scores (4.5K+ models)
  warehouse/catalog/huggingface/model_repos.csv       — model_id → GitHub repo links (from HF metadata)

Usage:
    uv run python warehouse/ingest/fetch_model_benchmarks.py
    uv run python warehouse/ingest/fetch_model_benchmarks.py --benchmarks-only
    uv run python warehouse/ingest/fetch_model_benchmarks.py --repos-only
"""

import csv
import functools
import re
import sys
from pathlib import Path

print = functools.partial(print, flush=True)

DATA_DIR = Path(__file__).resolve().parent.parent / "catalog" / "huggingface"
BENCHMARKS_CSV = DATA_DIR / "model_benchmarks.csv"
REPOS_CSV = DATA_DIR / "model_repos.csv"

BENCHMARK_FIELDS = [
    "model_id", "base_model", "architecture", "precision",
    "params_b", "license", "model_type",
    "average", "ifeval", "bbh", "math_lvl5", "gpqa", "musr", "mmlu_pro",
    "submission_date",
]

REPO_FIELDS = [
    "model_id", "author", "github_repo", "base_model_id",
    "pipeline_tag", "library_name", "downloads", "likes",
]

GITHUB_RE = re.compile(r"https?://github\.com/([^/]+/[^/\s\)\"'#]+)")


def fetch_benchmarks() -> list[dict]:
    from datasets import load_dataset

    print("Fetching Open LLM Leaderboard v2...")
    ds = load_dataset("open-llm-leaderboard/contents", split="train")
    print(f"  Found {len(ds)} entries")

    rows = []
    for entry in ds:
        model_id = entry.get("fullname", "")
        if not model_id:
            continue
        rows.append({
            "model_id": model_id,
            "base_model": entry.get("Base Model", ""),
            "architecture": entry.get("Architecture", ""),
            "precision": entry.get("Precision", ""),
            "params_b": entry.get("#Params (B)", ""),
            "license": entry.get("Hub License", ""),
            "model_type": entry.get("T", ""),
            "average": entry.get("Average ⬆️", ""),
            "ifeval": entry.get("IFEval", ""),
            "bbh": entry.get("BBH", ""),
            "math_lvl5": entry.get("MATH Lvl 5", ""),
            "gpqa": entry.get("GPQA", ""),
            "musr": entry.get("MUSR", ""),
            "mmlu_pro": entry.get("MMLU-PRO", ""),
            "submission_date": entry.get("Submission Date", ""),
        })

    rows.sort(key=lambda r: float(r["average"]) if r["average"] else 0, reverse=True)
    return rows


def fetch_model_repos() -> list[dict]:
    """Build model→repo links from existing CSVs + HF API for top models."""
    from huggingface_hub import model_info

    model_ids = set()
    for csv_name in ["tracked_models.csv", "top_models.csv"]:
        csv_path = DATA_DIR / csv_name
        if csv_path.exists():
            with open(csv_path) as f:
                for row in csv.DictReader(f):
                    model_ids.add(row.get("model_id", ""))

    # Also include leaderboard models if benchmarks CSV exists
    if BENCHMARKS_CSV.exists():
        with open(BENCHMARKS_CSV) as f:
            for row in csv.DictReader(f):
                model_ids.add(row.get("model_id", ""))

    model_ids.discard("")
    print(f"Scanning {len(model_ids)} models for GitHub repo links...")

    # Load GoodAI authors for matching
    try:
        from pyoso import Client
        client = Client()
        df = client.to_pandas("""
            SELECT DISTINCT
              LOWER(SPLIT_PART(repo, '/', 1)) AS owner,
              repo
            FROM currentai.entities.repos
        """)
        owner_to_repos = {}
        for _, r in df.iterrows():
            owner_to_repos.setdefault(r["owner"], []).append(r["repo"])
        print(f"  Loaded {len(owner_to_repos)} GitHub owners from AI catalog")
    except Exception as e:
        print(f"  Warning: could not load AI catalog ({e})")
        owner_to_repos = {}

    rows = []
    errors = 0
    total = len(model_ids)

    for i, mid in enumerate(sorted(model_ids)):
        if i % 200 == 0 and i > 0:
            print(f"  Progress: {i}/{total} ({len(rows)} links found, {errors} errors)")

        github_repo = ""
        base_model_id = ""
        pipeline_tag = ""
        library_name = ""
        downloads = 0
        likes = 0
        author = mid.split("/")[0] if "/" in mid else ""

        # Try HF API for detailed metadata
        try:
            info = model_info(mid)
            downloads = info.downloads or 0
            likes = info.likes or 0
            pipeline_tag = info.pipeline_tag or ""
            library_name = info.library_name or ""

            if info.card_data:
                bm = info.card_data.base_model
                if isinstance(bm, list):
                    base_model_id = bm[0] if bm else ""
                elif isinstance(bm, str):
                    base_model_id = bm

            # Search model card for GitHub links
            if hasattr(info, "card_data") and info.card_data:
                card_dict = info.card_data.to_dict()
                card_str = str(card_dict)
                gh_match = GITHUB_RE.search(card_str)
                if gh_match:
                    github_repo = gh_match.group(1).lower().rstrip("/")

        except Exception:
            errors += 1

        # Fallback: match author to known GitHub owner
        if not github_repo and author.lower() in owner_to_repos:
            candidates = owner_to_repos[author.lower()]
            if len(candidates) == 1:
                github_repo = candidates[0]

        rows.append({
            "model_id": mid,
            "author": author,
            "github_repo": github_repo,
            "base_model_id": base_model_id,
            "pipeline_tag": pipeline_tag,
            "library_name": library_name,
            "downloads": downloads,
            "likes": likes,
        })

    print(f"  Done: {len(rows)} models, {sum(1 for r in rows if r['github_repo'])} with GitHub links")
    rows.sort(key=lambda r: r["downloads"], reverse=True)
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    if not rows:
        print(f"  No rows for {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows)} rows to {path.name}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch model benchmarks and repo links.")
    parser.add_argument("--benchmarks-only", action="store_true")
    parser.add_argument("--repos-only", action="store_true")
    args = parser.parse_args()

    if not args.repos_only:
        benchmarks = fetch_benchmarks()
        write_csv(BENCHMARKS_CSV, benchmarks, BENCHMARK_FIELDS)

    if not args.benchmarks_only:
        repos = fetch_model_repos()
        write_csv(REPOS_CSV, repos, REPO_FIELDS)

    print("\nDone.")


if __name__ == "__main__":
    main()
