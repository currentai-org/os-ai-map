"""Report products whose own evidence cites a repository they do not declare.

The gap this exists for: a score file can cite `https://github.com/<owner>/<repo>` as the
source that establishes a product's `source` dimension while the product record declares no
`github` artifact at all. The evidence layer then knows the repository and the declaration
layer does not, which breaks three things at once and none of them loudly.

  - Repo-level dedup misses the product, so `discover-candidates` rediscovers its repository
    as a new candidate on every sweep. This is not hypothetical: the 2026-08-19 expansion
    query for the Sovereign Tech Agency surfaced `nvidia/megatron-lm`, `ray-project/ray`,
    `mlflow/mlflow` and `modelscope/ms-swift` as unscored, and all four were already products.
  - `signal_github` never fetches the repository, so the product carries no GitHub observation.
  - Adoption route selection reads declared artifacts, so a route that should apply does not.

Two shapes, because presence is not the invariant. A product with no `github` artifact at all
is the obvious one. The quieter one is a product that declares repository A while its evidence
cites repository B: testing `github` presence alone calls that clean and lets exactly the
divergence this module exists to catch through the net. So declared and cited repositories are
compared as identities, not counted.

Every divergence in the corpus today is a repository RENAME - the citation names the old path
and the declaration names the new one, and GitHub redirects the former to the latter. That is a
real finding rather than noise (a reader following the cited URL lands somewhere the record does
not name) but it is not a wrong artifact, and `artifact_exceptions: {github_moved: ...}` is the
key the schema already carries for it. Renames are reported separately from undeclared
repositories because the remedy differs: one wants a declaration, the other wants the citation
refreshed or the move recorded.

Report-only, deliberately. Flipping this to a `build.validate` error is the closing step of the
declaration cleanup, and it cannot be done while findings remain: some of them are not a missing
declaration but a mis-recorded citation, where the repository named is a component or a vendor's
other project rather than the product's own source (`google-cloud-run` cites `google/gvisor`,
`apify` cites `apify/crawlee`). Those want the citation corrected, not an artifact declared, and
declaring the repository to silence the check would attach another project's stars and license.

A `github.com/<owner>/<path>` URL is not always a repository. GitHub's own site paths match the
same shape - `github.com/features/copilot` is a product page - so the owner segment is checked
against RESERVED_OWNERS before a finding is raised.
"""
from __future__ import annotations

import re
import sys
from collections.abc import Mapping
from pathlib import Path

import yaml

RESERVED_OWNERS = frozenset({
    "features", "about", "pricing", "marketplace", "orgs", "topics", "collections",
    "sponsors", "settings", "enterprise", "security", "readme", "explore", "apps",
    "site", "contact",
})

_REPO_URL = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)$")


def _declared_repos(product: Mapping) -> set[str]:
    """The product's declared GitHub repositories, lowercased for identity comparison."""
    repos = set()
    for artifact in (product.get("github") or []):
        url = (artifact.get("url") or "").rstrip("/")
        if "github.com/" in url:
            repos.add(url.split("github.com/")[-1].removesuffix(".git").lower())
    return repos


def cited_source_repos(root: Path) -> list[tuple[str, str, str, frozenset]]:
    """(slug, owner/repo, axis, declared) for every source-establishing GitHub citation."""
    findings: list[tuple[str, str, str, frozenset]] = []
    for path in sorted((root / "sources" / "products").glob("*.yaml")):
        product = yaml.safe_load(path.read_text()) or {}
        declared = frozenset(_declared_repos(product))
        score_path = root / "sources" / "scores" / path.name
        if not score_path.exists():
            continue
        score = yaml.safe_load(score_path.read_text()) or {}
        for axis in ("openness", "adoption", "capability"):
            for source in ((score.get(axis) or {}).get("sources") or []):
                if "source" not in (source.get("establishes") or []):
                    continue
                matched = _REPO_URL.match((source.get("url") or "").rstrip("/"))
                if not matched or matched.group(1).lower() in RESERVED_OWNERS:
                    continue
                cited = f"{matched.group(1)}/{matched.group(2)}"
                if cited.lower() in declared:
                    continue
                findings.append((path.stem, cited, axis, declared))
    return findings


def undeclared_citations(root: Path) -> list[tuple[str, str, str]]:
    """Citations from a product that declares NO GitHub repository at all."""
    return [(s, r, a) for s, r, a, decl in cited_source_repos(root) if not decl]


def divergent_citations(root: Path) -> list[tuple[str, str, str]]:
    """Citations naming a repository the product does not declare, though it declares others."""
    return [(s, r, a) for s, r, a, decl in cited_source_repos(root) if decl]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    undeclared, divergent = undeclared_citations(root), divergent_citations(root)
    if not undeclared and not divergent:
        print("0 undeclared cited repositories")
        return 0
    if undeclared:
        print(f"{len(undeclared)} product(s) cite a source-establishing repository and declare none:")
        for slug, repo, axis in undeclared:
            print(f"  ~ {slug}: cites {repo} in {axis}.sources, declares no github artifact")
    if divergent:
        print(f"\n{len(divergent)} product(s) cite a repository other than the one they declare:")
        for slug, repo, axis in divergent:
            print(f"  ~ {slug}: cites {repo} in {axis}.sources")
    print("\nReport-only. An undeclared citation is either a missing declaration or a mis-recorded")
    print("one; declaring a repository that is not the product's own attaches another project's")
    print("signals. Every divergence in the corpus today is a verified rename - the cited path")
    print("redirects to the declared one - which wants the citation refreshed or the move recorded")
    print("under artifact_exceptions.github_moved, not a second artifact declared.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
