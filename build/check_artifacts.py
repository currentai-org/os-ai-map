"""Catch a declared artifact that has drifted away from the thing it names.

An artifact_id is a join key. `signal_github` keys on it, `signal_pypi` keys on it, and
every adoption band downstream rests on whatever it resolves to. So a stale one does not
fail loudly — it attaches another project's stars, license and downloads to this product
and keeps reporting them, which is indistinguishable from a working signal.

Three drifts, all of which happened in the week this was written:

  * **A repository moved.** 16 declarations pointed at a path that now redirects (#166).
    GitHub redirects today and frees the old path for reuse tomorrow; `identity.md`
    records the same hazard one level up, where `grok` was renamed and the slug was later
    reused by an unrelated product. A re-created `princeton-nlp/SWE-bench` would silently
    become this product's evidence.
  * **A package is a reservation, not a distribution.** `pypi:openmanus` was version
    0.1.0 with the summary "Add your description here", published from a 622-star
    predecessor repo while the product on the map has 57,911 (#167). It returned 200, so
    existence checks passed it.
  * **A package belongs to a different project.** The corroboration `stub_reason` cannot
    do on its own: does the package's own metadata name the repository we declare?

Two of the three need no network. `signal_github.resolved_via_redirect` and
`signal_pypi.missing_from_pypi` are computed weekly and were simply never read.

## Reports rather than fails, by default

Following the parity gate, and for the reason `verification.md` gives: a gate whose
schedule does not match its chain's fails for reasons that are not drift, and a gate that
cries wolf gets switched off. The signals refresh weekly, so this runs after them, and
`--strict` is what CI would use once the backlog is clear.

A legitimate mismatch is waived on the product with `artifact_exceptions`, keyed by check
name — presence is the exemption, the value is the reason.

Usage:
    uv run python -m build.check_artifacts                  # warehouse checks only, no network
    uv run python -m build.check_artifacts --live           # add the PyPI metadata checks
    uv run python -m build.check_artifacts --strict         # exit 1 on any unwaived finding
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from build.propose_artifacts import _get_json, declared_repo, pypi_info, stub_reason
from build.serialize_registry import artifact_id
from build.warehouse import query

ROOT = Path(__file__).resolve().parents[1]

CHECKS = ("github_moved", "pypi_missing", "pypi_stub", "pypi_repo_mismatch")


def load_products() -> dict[str, dict]:
    return {
        path.stem: yaml.safe_load(path.read_text()) or {}
        for path in sorted((ROOT / "sources" / "products").glob("*.yaml"))
    }


def declared(products: dict[str, dict], kind: str) -> dict[str, str]:
    """slug -> artifact_id, for products declaring this kind. First entry wins."""
    out: dict[str, str] = {}
    for slug, product in products.items():
        for entry in product.get(kind) or []:
            ident = artifact_id(kind, entry.get("url") or "")
            if ident:
                out[slug] = ident
                break
    return out


def waived(product: dict, check: str) -> str | None:
    return ((product.get("artifact_exceptions") or {}).get(check)) or None


def github_moved(products: dict[str, dict]) -> list[tuple[str, str, str]]:
    """Declarations whose repo now resolves somewhere else, per the signal's own probe."""
    rows = query(
        "SELECT product_slug, repo, resolved_repo FROM currentai.signal_github.repo_state "
        "WHERE resolved_via_redirect = true"
    )
    findings = []
    for row in rows:
        slug, resolved = row["product_slug"], row["resolved_repo"]
        declared_id = declared(products, "github").get(slug)
        if not declared_id or not resolved:
            continue
        # The signal probes what the repo declares, so compare against the declaration
        # rather than against the signal's own `repo` column, which is the same string.
        if declared_id.lower() != resolved.lower():
            findings.append((slug, declared_id, resolved))
    return findings


def canonical_repo(repo: str) -> str:
    """`owner/name` after GitHub's own rename resolution, lowercased.

    Only called on a disagreement, so this costs one request per finding rather than one
    per package.
    """
    body = _get_json(f"https://api.github.com/repos/{repo}", None)
    full = (body or {}).get("full_name")
    return (full or repo).lower()


def pypi_missing(products: dict[str, dict]) -> list[tuple[str, str, str]]:
    """Declared packages the signal could not find on PyPI at all."""
    rows = query(
        "SELECT product_slug, package FROM currentai.signal_pypi.package_downloads "
        "WHERE missing_from_pypi = true"
    )
    return [(r["product_slug"], r["package"], "absent from PyPI") for r in rows]


def pypi_content(products: dict[str, dict]) -> tuple[list, list]:
    """Live checks: a package that is a stub, or that names a different repository.

    One fetch per package, not two. Both questions are answered by the same JSON body,
    and this runs over every declared package weekly — fetching twice would double the
    rate-limit exposure to learn nothing extra.
    """
    stubs, mismatches = [], []
    packages = declared(products, "pypi")
    repos = declared(products, "github")
    for slug, package in sorted(packages.items()):
        info = pypi_info(package)
        if info is None:
            continue  # a transport failure is not evidence of anything
        reason = stub_reason("pypi", package, info=info)
        if reason:
            stubs.append((slug, package, reason))
            continue  # a stub's metadata is not worth corroborating
        names = declared_repo("pypi", package, info=info)
        ours = (repos.get(slug) or "").lower()
        # No repo in the metadata is an absence of evidence, not a mismatch. Only a
        # package naming a DIFFERENT repo than the one we declare is a finding.
        if not (names and ours and names != ours):
            continue
        # A package's own metadata goes stale exactly the way our declarations did, so a
        # raw string comparison reports a mismatch when WE are the current one. Resolve
        # the package's repo through GitHub's rename before believing the disagreement:
        # torchtune's metadata still names pytorch/torchtune, the path #166 corrected.
        if canonical_repo(names) == canonical_repo(ours):
            continue
        mismatches.append((slug, package, f"names {names}, we declare {ours}"))
    return stubs, mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="also run the PyPI metadata checks")
    parser.add_argument("--strict", action="store_true", help="exit 1 on any unwaived finding")
    args = parser.parse_args()

    products = load_products()
    results: dict[str, list[tuple[str, str, str]]] = {
        "github_moved": github_moved(products),
        "pypi_missing": pypi_missing(products),
        "pypi_stub": [],
        "pypi_repo_mismatch": [],
    }
    if args.live:
        results["pypi_stub"], results["pypi_repo_mismatch"] = pypi_content(products)

    unwaived = 0
    for check in CHECKS:
        findings = results[check]
        if not args.live and check in ("pypi_stub", "pypi_repo_mismatch"):
            print(f"{check:<22} skipped (needs --live)")
            continue
        live_findings = [f for f in findings if not waived(products.get(f[0]) or {}, check)]
        waived_count = len(findings) - len(live_findings)
        unwaived += len(live_findings)
        suffix = f", {waived_count} waived" if waived_count else ""
        print(f"{check:<22} {len(live_findings)} finding(s){suffix}")
        for slug, ident, detail in live_findings:
            print(f"    {slug:<28} {ident:<34} {detail}")

    print()
    if unwaived:
        print(f"{unwaived} artifact(s) have drifted from what they name.")
        print("Fix the declaration, or waive it on the product with `artifact_exceptions`.")
    else:
        print("Every declared artifact still resolves to the thing it names.")
    return 1 if (args.strict and unwaived) else 0


if __name__ == "__main__":
    raise SystemExit(main())
