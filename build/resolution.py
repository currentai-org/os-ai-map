"""The resolution ledger: decisions about candidate repositories a person already made.

See `sources/resolution_ledger.yaml` for why it exists. In short: a discovery sweep resolves a
repository by hand and records the reasoning in a pull request, which no later run can read. The
first corpus expansion duly recreated four repositories that #413 had already resolved - one of
them a product the corpus carries under another name.

This module is the reader. `build/validate.py` enforces the half that can be enforced
mechanically, and a bulk pipeline is expected to consult `verdict_for` before proposing a
product from a repository.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "sources" / "resolution_ledger.yaml"

#: A repository resolved to one of these is not a new product.
NOT_A_NEW_PRODUCT = frozenset({"existing_product", "sku_of", "excluded_boundary",
                               "excluded_maintenance"})
#: `unresolved` is deliberately not in that set: it means a person has to look, and a rerun
#: proposing it again is the correct behaviour, not a regression.
VERDICTS = NOT_A_NEW_PRODUCT | {"unresolved"}


class DuplicateResolution(ValueError):
    """Two entries resolve the same repository. For governance state that is never benign."""


def load(path: Path = LEDGER) -> dict[str, dict]:
    """Ledger keyed by lowercased `owner/repo`.

    A duplicate repository raises rather than resolving last-write-wins. The dict comprehension
    this replaced would silently keep whichever entry came last, so `Foo/Bar: existing_product`
    followed by `foo/bar: unresolved` would quietly discard the stronger decision - and the file
    is hand-edited by people appending after each review, which is exactly how that happens.
    `docs/reference/identity.md` records the same failure in the deleted slug-alias mapping:
    two renames of one retired slug, and whichever came last won.
    """
    if not path.exists():
        return {}
    doc = yaml.safe_load(path.read_text()) or {}
    entries: dict[str, dict] = {}
    for entry in (doc.get("resolutions") or []):
        key = (entry.get("repo") or "").strip().removesuffix(".git").lower()
        if key in entries:
            raise DuplicateResolution(
                f"{path.name}: {entry.get('repo')!r} is resolved twice - already "
                f"{entries[key]['verdict']!r} from {entries[key].get('decided_in')}, now "
                f"{entry.get('verdict')!r} from {entry.get('decided_in')}. Identity is compared "
                f"lowercased and without a .git suffix, so these are one repository. Merge them."
            )
        entries[key] = entry
    return entries


def verdict_for(repo: str, ledger: Mapping[str, dict] | None = None) -> dict | None:
    """The recorded decision for a repository, or None if it has never been resolved."""
    return (load() if ledger is None else ledger).get((repo or "").lower())


def blocks_new_product(repo: str, ledger: Mapping[str, dict] | None = None) -> dict | None:
    """The entry that PERMANENTLY forbids minting a product from this repository, if any.

    This is what `build/validate.py` enforces, and it deliberately excludes `unresolved`: a
    person may still add such a product by hand once they have settled the question, and the
    build should not stop them.
    """
    entry = verdict_for(repo, ledger)
    return entry if entry and entry.get("verdict") in NOT_A_NEW_PRODUCT else None


def holds_bulk_promotion(repo: str, ledger: Mapping[str, dict] | None = None) -> dict | None:
    """The entry that stops a BULK run from promoting this repository, if any.

    Any entry at all, `unresolved` included. "Not permanently excluded" and "this proposal may
    proceed" are different questions, and conflating them published a bug: the #418 review
    recorded `ag-ui` as a protocol filed under agent frameworks, `serena` as an MCP retrieval
    toolkit and `repomix` as document ingestion - and then the same run published all three in
    `orchestration_agents`, the category the entry says is wrong.

    `unresolved` means the repository may come back to a LATER sweep, not that the CURRENT
    proposal is fit to publish. A bulk run parks it for a person; a person resolves it.
    """
    return verdict_for(repo, ledger)
