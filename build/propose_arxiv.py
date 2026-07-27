"""Propose arXiv identifiers for products, from evidence we already hold.

Citation counts need an exact identifier. Matching papers by product name was
measured at 2 correct out of 10: APPS resolved to a medical software paper with
25k citations, MATH to a psychology paper with 3.4k. Both would have looked
entirely credible in a table, which is the dangerous kind of wrong.

So this proposes rather than decides. It gathers candidate arXiv ids from two
places we already have and prints them with their evidence for review. Nothing is
written to sources/ — a human picks the canonical paper and adds it.

Two evidence routes:
  1. arXiv links already present in a product's own yaml or its score sources.
  2. `arxiv:` tags on the product's Hugging Face artifact. The Hub carries these
     as first-class tags.

Neither is authoritative. Route 2 in particular lists *cited* papers as well as
the paper describing the artifact — cais/mmlu tags four, only one of which is the
MMLU paper. Anything with more than one candidate is flagged REVIEW and needs a
person to choose.

Usage:
    uv run python -m build.propose_arxiv                 # every product
    uv run python -m build.propose_arxiv --category benchmark_eval_data
    uv run python -m build.propose_arxiv --format yaml   # paste-ready snippets
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]
HF_API = "https://huggingface.co/api"
USER_AGENT = "os-ai-map-arxiv-proposer/1.0"

ARXIV_RE = re.compile(r"(?:arxiv\.org/(?:abs|pdf)/|arxiv:)(\d{4}\.\d{4,5})", re.I)


def _hf_ids(product: dict) -> list[tuple[str, str]]:
    """Return (kind, hf_id) for the product's Hugging Face artifacts."""
    out: list[tuple[str, str]] = []
    for key, segment in (("huggingface_model", "models"), ("huggingface_dataset", "datasets")):
        value = product.get(key)
        entries = [value] if isinstance(value, str) else (value or [])
        for entry in entries:
            url = entry.get("url") if isinstance(entry, dict) else entry
            if not isinstance(url, str):
                continue
            match = re.search(r"huggingface\.co/(?:datasets/)?(.+)", url.rstrip("/"))
            if match:
                out.append((segment, match.group(1)))
    return out


def _fetch_hf_tags(segment: str, hf_id: str, token: str | None) -> list[str]:
    """arXiv ids from the Hub's tags. Returns [] on any failure — this is a hint,
    not a dependency, so a Hub hiccup must not fail the whole proposal."""
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{HF_API}/{segment}/{hf_id}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return []
    if not isinstance(payload, dict):
        return []
    tags = payload.get("tags")
    if not isinstance(tags, list):
        return []
    return [t.split(":", 1)[1] for t in tags if isinstance(t, str) and t.startswith("arxiv:")]


def propose(sources: dict, category: str | None, token: str | None) -> list[dict]:
    products: dict = sources["products"]
    categories: dict = sources["categories"]

    wanted = set(products)
    if category:
        cat = categories.get(category)
        if cat is None:
            raise SystemExit(f"no such category: {category}")
        wanted = {s for s in (cat.get("products") or []) if s in products}

    rows: list[dict] = []
    for slug in sorted(wanted):
        product = products[slug]
        if product.get("arxiv"):
            continue  # already declared

        from_yaml: list[str] = []
        for text in (
            (ROOT / "sources" / "products" / f"{slug}.yaml").read_text(),
            (ROOT / "sources" / "scores" / f"{slug}.yaml").read_text()
            if (ROOT / "sources" / "scores" / f"{slug}.yaml").exists()
            else "",
        ):
            from_yaml.extend(ARXIV_RE.findall(text))

        from_hub: list[str] = []
        for segment, hf_id in _hf_ids(product):
            from_hub.extend(_fetch_hf_tags(segment, hf_id, token))

        candidates: list[str] = []
        for value in from_yaml + from_hub:
            if value not in candidates:
                candidates.append(value)

        if not candidates:
            verdict = "NONE"
        elif len(candidates) == 1:
            verdict = "single"
        else:
            verdict = "REVIEW"

        rows.append(
            {
                "slug": slug,
                "display_name": product.get("display_name", slug),
                "candidates": candidates,
                "from_yaml": from_yaml,
                "from_hub": from_hub,
                "verdict": verdict,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="limit to one category slug")
    parser.add_argument("--format", choices=("table", "yaml"), default="table")
    args = parser.parse_args()

    token = os.environ.get("HUGGING_FACE_TOKEN") or os.environ.get("HF_TOKEN")
    rows = propose(load_sources(ROOT), args.category, token)

    if args.format == "yaml":
        for row in rows:
            if row["verdict"] == "single":
                print(f"# {row['slug']} — {row['display_name']}")
                print("arxiv:")
                print(f"- url: https://arxiv.org/abs/{row['candidates'][0]}")
                print()
        print(f"# {sum(1 for r in rows if r['verdict'] == 'REVIEW')} products need a human choice")
        print(f"# {sum(1 for r in rows if r['verdict'] == 'NONE')} have no candidate")
        return 0

    print(f"{'product':<26} {'verdict':<8} candidates (yaml | hub)")
    for row in rows:
        cands = ", ".join(row["candidates"]) or "-"
        print(f"  {row['display_name'][:24]:<24} {row['verdict']:<8} {cands[:60]}")
    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in ("single", "REVIEW", "NONE")}
    print(f"\nsingle candidate (safe to accept): {counts['single']}")
    print(f"multiple candidates (pick one):    {counts['REVIEW']}")
    print(f"no candidate found:                {counts['NONE']}")
    print("\nNothing written. Review, then add an `arxiv:` block to the product yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
