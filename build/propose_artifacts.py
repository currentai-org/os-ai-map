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
attaches another project's license and download counts to a product. That is
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
    uv run python -m build.propose_artifacts --kind pypi        # missing THIS kind specifically

`--kind` exists because "has an artifact" and "routes a signal" are different questions.
`signal_routing.yaml` sends adoption to HF, then PyPI, then stars — and stars is
`stars_fallback`, which the rubric caps at level 3. So a library with a GitHub repo and no
declared `pypi` is fully verifiable and still pinned to a capped band. Measured 2026-08-09:
66 of 472 products declared a `pypi` artifact, while 87 more cited a PyPI page in their
adoption evidence, meaning a human had read the number the signal could not.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

from build.vocabulary import artifact_kinds

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "os-ai-map-artifact-proposer/1.0"

# What this proposer can actually handle, defined by the three behaviors a kind needs to be
# proposed at all: a URL pattern to mine it out of prose, a live existence check, and a public
# URL to render. Derived from those handlers rather than from the routing table.
#
# The distinction matters and the first cut got it wrong. Deriving from
# `signal_routing.yaml` made a NEW `artifact_key` an accepted `--kind` the moment somebody
# declared a source — with no pattern, no verifier and no renderer behind it, so the proposer
# would accept a flag it cannot service. The two sets are equal today, which is exactly what
# made the coincidence look like a definition.
def _supported_kinds() -> tuple[str, ...]:
    patterned = {kind for kind, _ in PATTERNS}
    renderable = set(_PUBLIC_URL)
    return tuple(sorted(patterned & renderable & _VERIFIABLE))


# `arxiv` is routed (via `semanticscholar`) and deliberately unsupported here: this tool
# proposes DISTRIBUTION artifacts, and a paper id is not one. Kept as a named exclusion so the
# subset check below stays meaningful rather than vacuous.
NOT_A_DISTRIBUTION_ARTIFACT = frozenset({"arxiv"})

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
    # pypistats, in all three shapes the corpus uses: /packages/<name>,
    # /api/packages/<name>/recent, /api/packages/<name>/overall. It is where a human goes
    # to READ a download count, so it is the form the evidence usually carries — 69 score
    # files cite pypistats against 23 citing pypi.org, and mining only the latter finds a
    # fraction of what is there. The captured name is still verified against the PyPI JSON
    # API below before anything is proposed, so a stale or misspelled one cannot slip in.
    ("pypi", re.compile(r"pypistats\.org/(?:api/)?packages/([\w\-.]+)", re.I)),
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


def _get_json(url: str, token: str | None) -> dict | None:
    """The body, or None on any failure. Existence is `_get`'s job; this reads content."""
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return None


# A version nobody has moved off, on a package whose description was never written.
# Both of the wrong declarations in #165 carried one of these and one carried both.
PLACEHOLDER_VERSIONS = {"0.0.0", "0.1.0"}
# The literal string uv and poetry scaffold into a fresh pyproject. An EMPTY summary is
# deliberately not a tell: safetensors, tokenizers and cohere all ship one and are among
# the most-downloaded packages in the corpus. Flagging those was this check's first
# false-positive class.
PLACEHOLDER_SUMMARY = re.compile(r"add your description here|^placeholder", re.I)


def pypi_info(ident: str) -> dict | None:
    """The `info` block of a package's PyPI JSON, or None on any failure."""
    body = _get_json(f"https://pypi.org/pypi/{ident}/json", None)
    return None if body is None else (body.get("info") or {})


def stub_reason(kind: str, ident: str, info: dict | None = None) -> str | None:
    """Why this artifact looks like a reservation rather than a distribution, or None.

    A 200 answers "does this name exist", which is not the question. `pypi:openmanus`
    existed, returned 200, and was a stub published from a 622-star predecessor repo
    while the product on the map had 57,911 stars — so its download count measured a
    different project. `pypi:nemo-rl` existed at version 0.0.0, a reserved name with no
    release behind it.

    Only PyPI is checked today because that is where the evidence is. The same shape
    applies to npm and crates and can be added when one of them bites.
    """
    if kind != "pypi":
        return None
    if info is None:
        info = pypi_info(ident)
    if info is None:
        return None  # a transport failure is not evidence of a stub
    reasons = []
    version = str(info.get("version") or "")
    if version in PLACEHOLDER_VERSIONS:
        reasons.append(f"version {version}")
    if PLACEHOLDER_SUMMARY.search(str(info.get("summary") or "")):
        reasons.append("placeholder summary")
    return "; ".join(reasons) or None


def declared_repo(kind: str, ident: str, info: dict | None = None) -> str | None:
    """The repository this artifact's own metadata points at, lowercased, or None.

    Corroboration rather than existence: a package whose metadata names a different
    project than the one we declare is the failure `stub_reason` cannot see on its own.
    """
    if kind != "pypi":
        return None
    if info is None:
        info = pypi_info(ident)
    if info is None:
        return None
    blob = " ".join(str(v) for v in (info.get("project_urls") or {}).values())
    blob += " " + str(info.get("home_page") or "")
    found = re.findall(r"github\.com/([\w\-.]+/[\w\-.]+)", blob, re.I)
    return found[0].lower().removesuffix(".git") if found else None


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


# The kinds `verify` implements a live existence check for. Named rather than inferred, so a
# new branch there has to be declared here to count as supported.
_VERIFIABLE = frozenset({"github", "huggingface_model", "huggingface_dataset",
                         "pypi", "npm", "crates"})


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


_PUBLIC_URL = {
    "github": "https://github.com/{ident}",
    "huggingface_model": "https://huggingface.co/{ident}",
    "huggingface_dataset": "https://huggingface.co/datasets/{ident}",
    "pypi": "https://pypi.org/project/{ident}",
    "npm": "https://www.npmjs.com/package/{ident}",
    "crates": "https://crates.io/crates/{ident}",
}


def public_url(kind: str, ident: str) -> str:
    return _PUBLIC_URL[kind].format(ident=ident)


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


VERIFIABLE_KINDS = _supported_kinds()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="limit to one category slug")
    parser.add_argument("--include-closed", action="store_true",
                        help="also propose for products scored `closed`")
    parser.add_argument("--format", choices=("table", "yaml"), default="table")
    parser.add_argument("--kind", choices=VERIFIABLE_KINDS,
                        help="propose only this artifact kind, and select products missing THIS "
                             "kind rather than products missing every kind")
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
        # Without --kind, "verifiable at all" is the bar: a product with a GitHub repo is
        # checkable and needs nothing. With --kind, the bar is that ONE kind, because a
        # product can be perfectly verifiable and still route no adoption signal — a
        # library with a repo and no declared `pypi` falls through to stars_fallback,
        # which the rubric caps.
        if any(product.get(kind) for kind in ((args.kind,) if args.kind else VERIFIABLE_KINDS)):
            continue  # already verifiable

        score_path = ROOT / "sources" / "scores" / f"{slug}.yaml"
        scores = yaml.safe_load(score_path.read_text()) if score_path.exists() else {}
        openness_class = ((scores or {}).get("openness") or {}).get("class")
        if not args.include_closed and openness_class == "closed":
            continue

        found = candidates_for(product, scores or {})
        if args.kind:
            found = {k: v for k, v in found.items() if k == args.kind}
        verified: list[tuple[str, str, int]] = []
        for kind, idents in found.items():
            for ident in idents:
                status = 0 if args.no_verify else verify(kind, ident, gh_token, hf_token)
                verified.append((kind, ident, status))
                if not args.no_verify:
                    time.sleep(0.12)  # stay polite across a few hundred calls

        # A 200 says the name resolves, not that it is this product's distribution.
        # Screen the live ones before they can be reported as safe to accept.
        stubs: list[tuple[str, str, str]] = []
        if not args.no_verify:
            for kind, ident, status in [v for v in verified if v[2] == 200]:
                reason = stub_reason(kind, ident)
                if reason:
                    stubs.append((kind, ident, reason))
        stub_idents = {(k, i) for k, i, _ in stubs}
        verified = [v for v in verified if (v[0], v[1]) not in stub_idents]

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
            # Every candidate was screened out. Say STUB rather than NONE: "no candidate
            # in the repo" and "the only candidate is a reservation" are different
            # findings, and the second is the one that nearly shipped twice.
            verdict = "STUB" if stubs else "NONE"
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
            "stubs": stubs,
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
                  ("single", "multi-kind", "REVIEW", "ALL-404", "NONE", "STUB")}
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

    stubbed = [(r["slug"], k, i, why) for r in rows for k, i, why in r["stubs"]]
    if stubbed:
        print("\nscreened out as reservations rather than distributions:")
        for slug, kind, ident, why in stubbed:
            print(f"  {slug:<24}{kind}:{ident} — {why}")

    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in
              ("single", "multi-kind", "REVIEW", "UNVERIFIED", "ALL-404", "NONE", "STUB")}
    print(f"\nsingle verified candidate (safe to accept): {counts['single']}")
    print(f"several kinds, all verified (accept all):    {counts['multi-kind']}")
    print(f"two of the SAME kind (pick one):            {counts['REVIEW']}")
    print(f"could not verify (auth/rate limit/network): {counts['UNVERIFIED']}")
    print(f"candidates found but confirmed 404:         {counts['ALL-404']}")
    print(f"no candidate in the repo at all:            {counts['NONE']}")
    print(f"only candidate was a stub/reservation:      {counts['STUB']}")
    print("\nNothing written. Review, then add the artifact block to the product yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
