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


def load(path: Path = LEDGER) -> dict[str, dict]:
    """Ledger keyed by lowercased `owner/repo`."""
    if not path.exists():
        return {}
    doc = yaml.safe_load(path.read_text()) or {}
    return {e["repo"].lower(): e for e in (doc.get("resolutions") or [])}


def verdict_for(repo: str, ledger: Mapping[str, dict] | None = None) -> dict | None:
    """The recorded decision for a repository, or None if it has never been resolved."""
    return (load() if ledger is None else ledger).get((repo or "").lower())


def blocks_new_product(repo: str, ledger: Mapping[str, dict] | None = None) -> dict | None:
    """The entry that forbids minting a product from this repository, if any."""
    entry = verdict_for(repo, ledger)
    return entry if entry and entry.get("verdict") in NOT_A_NEW_PRODUCT else None
