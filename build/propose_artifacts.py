"""Propose verifiable artifacts for products that have none, from evidence we hold.

An "open" product with no declared artifact is a claim nobody can check. The map's
openness ratings are its differentiator, so those are the worst place to have
unverifiable evidence — and 44 non-closed products are in exactly that state while
their own score files cite the URL that would fix it. Apertus is scored 5,
open_source, and cites `huggingface.co/swiss-ai/Apertus-70B-2509` as a source,
while declaring no `huggingface_model`.

So this mines candidates from text already in the repo and then **checks each one
resolves against the live API**. Pattern-matching a URL is not verification: a
plausible-looking repo path that 404s is worse than no candidate, because it looks
like progress.

Like `propose_arxiv.py`, it writes nothing. It prints candidates with their
evidence and verdict for a human to accept. The reason is the same: matching by
name was measured at 2 correct in 10 on this data, and a wrong artifact silently
attaches another project's licence and download counts to a product. That is
indistinguishable from a real score until someone checks.

Candidate sources, in order of trust:
  1. `sources/products/<slug>.yaml` — homepage and any URL-bearing field
  2. `sources/scores/<slug>.yaml` — every `sources[].url`, which is evidence a human
     already chose as authoritative for this product

Verification is live: GitHub `/repos`, HF `/api/models` and `/api/datasets`, and the
PyPI JSON API. Uses `GITHUB_TOKEN` / `HF_TOKEN` when present, which matters — the
anonymous GitHub limit is 60 requests an hour.

Usage:
    uv run python -m build.propose_artifacts                    # non-closed, missing an artifact
    uv run python -m build.propose_artifacts --include-closed
    uv run python -m build.propose_artifacts --category base_pretrained
    uv run python -m build.propose_artifacts --format yaml      # paste-ready blocks
"""

from __future__ import annotations

import argparse
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "os-ai-map-artifact-proposer/1.0"

VERIFIABLE_KINDS = ("github", "huggingface_model", "huggingface_dataset", "pypi", "npm", "crates")

# Hugging Face path segments that are not a model id. Without these, a docs or blog
# link becomes a confident-looking candidate.
HF_RESERVED = {
    "datasets", "spaces", "api", "docs", "blog", "papers", "collections",
    "models", "organizations", "settings", "join", "pricing", "tasks", "learn",
}
GH_RESERVED = {
    "orgs", "topics", "search", "features", "pricing", "about", "explore",
    "marketplace", "sponsors", "collections", "trending", "settings", "login",
}

PATTERNS = [
    ("huggingface_dataset", re.compile(r"huggingface\.co/datasets/([\w\-.]+/[\w\-.]+)", re.I)),
    ("huggingface_model", re.compile(r"huggingface\.co/([\w\-.]+/[\w\-.]+)", re.I)),
    ("github", re.compile(r"github\.com/([\w\-.]+/[\w\-.]+)", re.I)),
    ("pypi", re.compile(r"pypi\.org/project/([\w\-.]+)", re.I)),
    ("npm", re.compile(r"npmjs\.com/package/((?:@[\w\-.]+/)?[\w\-.]+)", re.I)),
    ("crates", re.compile(r"crates\.io/crates/([\w\-.]+)", re.I)),
]


def _urls_in(node: object, out: list[str]) -> None:
    """Every http(s) string anywhere in a nested structure."""
    if isinstance(node, str):
        if node.startswith("http"):
            out.append(node)
    elif isinstance(node, dict):
        for value in node.values():
            _urls_in(value, out)
    elif isinstance(node, list):
        for value in node:
            _urls_in(value, out)


def candidates_for(product: dict, scores: dict) -> dict[str, list[str]]:
    """Candidate ids per artifact kind, from the product and its score evidence."""
    urls: list[str] = []
    _urls_in(product, urls)
    _urls_in(scores, urls)

    found: dict[str, list[str]] = {}
    for url in urls:
        for kind, pattern in PATTERNS:
            match = pattern.search(url)
            if not match:
                continue
            ident = match.group(1).rstrip("/.")
            owner = ident.split("/")[0].lower()
            if kind.startswith("huggingface") and owner in HF_RESERVED:
                continue
            if kind == "github" and owner in GH_RESERVED:
                continue
            if ident.endswith(".git"):
                ident = ident[:-4]
            found.setdefault(kind, [])
            # GitHub and PyPI names are case-insensitive, so crewAIInc/crewAI and
            # crewaiinc/crewai are one candidate, not a choice between two.
            if ident.lower() not in {x.lower() for x in found[kind]}:
                found[kind].append(ident)
            break  # first (most specific) pattern wins for a given URL
    return found


def _get(url: str, token: str | None) -> int:
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (urllib.error.URLError, TimeoutError):
        return 0


def check_token(gh_token: str | None) -> str | None:
    """Drop a GitHub token that does not authenticate.

    A dead token returns 401 on every call, and 401 is not evidence a repo is
    missing. Anonymous access still answers existence questions at 60 requests an
    hour, which is enough here, so a bad token is worse than none.
    """
    if not gh_token:
        return None
    if _get("https://api.github.com/rate_limit", gh_token) == 200:
        return gh_token
    print("warning: GITHUB_TOKEN did not authenticate (401). Falling back to "
          "anonymous requests, limit 60/hour.\n")
    return None


def verify(kind: str, ident: str, gh_token: str | None, hf_token: str | None) -> int:
    """Live existence check. Returns the HTTP status, 0 on transport failure."""
    if kind == "github":
        return _get(f"https://api.github.com/repos/{ident}", gh_token)
    if kind == "huggingface_model":
        return _get(f"https://huggingface.co/api/models/{ident}", hf_token)
    if kind == "huggingface_dataset":
        return _get(f"https://huggingface.co/api/datasets/{ident}", hf_token)
    if kind == "pypi":
        return _get(f"https://pypi.org/pypi/{ident}/json", None)
    if kind == "npm":
        return _get(f"https://registry.npmjs.org/{ident}", None)
    if kind == "crates":
        return _get(f"https://crates.io/api/v1/crates/{ident}", None)
    return 0


def public_url(kind: str, ident: str) -> str:
    return {
        "github": f"https://github.com/{ident}",
        "huggingface_model": f"https://huggingface.co/{ident}",
        "huggingface_dataset": f"https://huggingface.co/datasets/{ident}",
        "pypi": f"https://pypi.org/project/{ident}",
        "npm": f"https://www.npmjs.com/package/{ident}",
        "crates": f"https://crates.io/crates/{ident}",
    }[kind]


def load_env() -> tuple[str | None, str | None]:
    """Tokens from the environment, falling back to a .env beside or above the repo."""
    gh = os.environ.get("GITHUB_TOKEN")
    hf = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_TOKEN")
    for candidate in (ROOT / ".env", ROOT.parent / ".env"):
        if not candidate.exists():
            continue
        for line in candidate.read_text().splitlines():
            if "=" not in line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip("'\"")
            if key == "GITHUB_TOKEN" and not gh:
                gh = value
            if key in ("HF_TOKEN", "HUGGING_FACE_TOKEN") and not hf:
                hf = value
    return gh, hf


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="limit to one category slug")
    parser.add_argument("--include-closed", action="store_true",
                        help="also propose for products scored `closed`")
    parser.add_argument("--format", choices=("table", "yaml"), default="table")
    parser.add_argument("--no-verify", action="store_true",
                        help="skip live checks (offline; verdicts become 'unchecked')")
    args = parser.parse_args()

    gh_token, hf_token = load_env()
    gh_token = None if args.no_verify else check_token(gh_token)
    category_of: dict[str, str] = {}
    for path in (ROOT / "sources" / "categories").glob("*.yaml"):
        category = yaml.safe_load(path.read_text())
        for slug in category.get("products") or []:
            category_of[slug] = category["name"]

    rows: list[dict] = []
    for path in sorted((ROOT / "sources" / "products").glob("*.yaml")):
        slug = path.stem
        if args.category and category_of.get(slug) != args.category:
            continue
        product = yaml.safe_load(path.read_text()) or {}
        if any(product.get(kind) for kind in VERIFIABLE_KINDS):
            continue  # already verifiable

        score_path = ROOT / "sources" / "scores" / f"{slug}.yaml"
        scores = yaml.safe_load(score_path.read_text()) if score_path.exists() else {}
        openness_class = ((scores or {}).get("openness") or {}).get("class")
        if not args.include_closed and openness_class == "closed":
            continue

        found = candidates_for(product, scores or {})
        verified: list[tuple[str, str, int]] = []
        for kind, idents in found.items():
            for ident in idents:
                status = 0 if args.no_verify else verify(kind, ident, gh_token, hf_token)
                verified.append((kind, ident, status))
                if not args.no_verify:
                    time.sleep(0.12)  # stay polite across a few hundred calls

        live = [v for v in verified if v[2] == 200]
        # Only 404 means absent. 401/403 is auth or rate limiting, 0 is a transport
        # failure, and reading either as "this repo does not exist" turns a broken
        # credential into a confident false finding.
        absent = [v for v in verified if v[2] == 404]
        inconclusive = [v for v in verified if v[2] not in (200, 404)]

        # Ambiguity is per artifact KIND. Two candidates of different kinds are not a
        # choice — a model with both weights on the Hub and a training repo should
        # declare both. Only two live candidates of the SAME kind need a human.
        live_by_kind: dict[str, list[str]] = {}
        for kind, ident, status in live:
            if status == 200:
                live_by_kind.setdefault(kind, []).append(ident)
        contested = {k: v for k, v in live_by_kind.items() if len(v) > 1}

        if args.no_verify:
            verdict = "unchecked" if verified else "NONE"
        elif not verified:
            verdict = "NONE"
        elif contested:
            verdict = "REVIEW"
        elif live_by_kind:
            verdict = "single" if len(live_by_kind) == 1 else "multi-kind"
        elif inconclusive:
            verdict = "UNVERIFIED"
        else:
            verdict = "ALL-404"

        rows.append({
            "slug": slug,
            "display_name": product.get("display_name", slug),
            "category": category_of.get(slug, "?"),
            "openness_class": openness_class,
            "candidates": verified,
            "live": live,
            "live_by_kind": live_by_kind,
            "verdict": verdict,
        })

    if args.format == "yaml":
        for row in rows:
            if row["verdict"] not in ("single", "multi-kind"):
                continue
            print(f"# {row['slug']} — {row['display_name']} ({row['openness_class']})")
            for kind, idents in row["live_by_kind"].items():
                print(f"{kind}:")
                print(f"- url: {public_url(kind, idents[0])}")
            print()
        counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in
                  ("single", "multi-kind", "REVIEW", "ALL-404", "NONE")}
        print(f"# ready: {counts['single'] + counts['multi-kind']}  "
              f"needs a choice: {counts['REVIEW']}  no candidate: {counts['NONE']}")
        return 0

    print(f"{len(rows)} products with no verifiable artifact\n")
    print(f"{'product':<26}{'class':<17}{'verdict':<11}candidates (status)")
    for row in sorted(rows, key=lambda r: (r["verdict"], r["slug"])):
        shown = ", ".join(f"{k.replace('huggingface_','hf_')}:{i} ({s})"
                          for k, i, s in row["candidates"][:3]) or "-"
        print(f"  {row['display_name'][:24]:<26}{str(row['openness_class']):<17}"
              f"{row['verdict']:<11}{shown[:64]}")

    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in
              ("single", "multi-kind", "REVIEW", "UNVERIFIED", "ALL-404", "NONE")}
    print(f"\nsingle verified candidate (safe to accept): {counts['single']}")
    print(f"several kinds, all verified (accept all):    {counts['multi-kind']}")
    print(f"two of the SAME kind (pick one):            {counts['REVIEW']}")
    print(f"could not verify (auth/rate limit/network): {counts['UNVERIFIED']}")
    print(f"candidates found but confirmed 404:         {counts['ALL-404']}")
    print(f"no candidate in the repo at all:            {counts['NONE']}")
    print("\nNothing written. Review, then add the artifact block to the product yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
