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
from pathlib import Path

import yaml

RESERVED_OWNERS = frozenset({
    "features", "about", "pricing", "marketplace", "orgs", "topics", "collections",
    "sponsors", "settings", "enterprise", "security", "readme", "explore", "apps",
    "site", "contact",
})

_REPO_URL = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)$")


def undeclared_citations(root: Path) -> list[tuple[str, str, str]]:
    """(slug, owner/repo, axis) for every product citing a source-establishing repo it lacks."""
    findings: list[tuple[str, str, str]] = []
    for path in sorted((root / "sources" / "products").glob("*.yaml")):
        product = yaml.safe_load(path.read_text()) or {}
        if product.get("github"):
            continue
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
                findings.append((path.stem, f"{matched.group(1)}/{matched.group(2)}", axis))
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = undeclared_citations(root)
    if not findings:
        print("0 undeclared cited repositories")
        return 0
    print(f"{len(findings)} product(s) cite a source-establishing repository they do not declare:")
    for slug, repo, axis in findings:
        print(f"  ~ {slug}: cites {repo} in {axis}.sources, declares no github artifact")
    print("\nReport-only. Each is either a missing declaration or a mis-recorded citation;")
    print("declaring a repository that is not the product's own attaches another project's signals.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
