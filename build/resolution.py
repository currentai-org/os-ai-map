"""Resolution ledger: the map's durable memory of identity rulings.

See `sources/resolution_ledger.yaml` for why it exists. In short: a discovery sweep resolves a
candidate artifact by hand - "this is the spec repo of a product we already carry", "this PyPI
package's downloads are not this product's usage" - and records the reasoning in a pull request,
which no later run can read. The first corpus expansion duly recreated four repositories that
#413 had already resolved - one of them a product the corpus carries under another name.

Keyed on (artifact kind, canonical id). Every verdict is typed by relation, and a ruling
suppresses only questions of its own relation: a `not_member_of` on a PyPI package never
suppresses a later equivalence question about the same package. Entries written before 2026-09
carry no relation and are read as `product_equivalence`, which is the only question they ever
answered. The file is never rewritten by code; it only grows (#437).

This module is the reader. `build/validate.py` enforces the half that can be enforced
mechanically, and a bulk pipeline is expected to consult `verdict_for` (or one of the three
narrower predicates below) before proposing a product from a candidate artifact.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml

from build.identity import canonical as _identity_canonical

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "sources" / "resolution_ledger.yaml"

RELATIONS = ("product_equivalence", "product_membership")

#: An artifact resolved to one of these is not a new product.
NOT_A_NEW_PRODUCT = frozenset({"existing_product", "sku_of", "excluded_boundary",
                               "excluded_maintenance"})
#: `unresolved` is deliberately not in that set: it means a person has to look, and a rerun
#: proposing it again is the correct behaviour, not a regression.
EQUIVALENCE_VERDICTS = NOT_A_NEW_PRODUCT | {"unresolved"}
#: The two verdicts a `product_membership` ruling can carry.
MEMBERSHIP_VERDICTS = frozenset({"member_of", "not_member_of"})
VERDICTS = EQUIVALENCE_VERDICTS | MEMBERSHIP_VERDICTS

Key = tuple[str, str]


class DuplicateResolution(ValueError):
    """Two entries answer the same (artifact, relation) question. Never benign for governance state."""


def _canonical(kind: str, ident: str) -> str:
    """Fold an artifact identifier to the form the ledger keys on, per kind.

    Delegates to `build.identity.canonical`, the one place these rules live -- see
    `build/identity.py`.
    """
    return _identity_canonical(kind, ident)


def key_for(entry: Mapping) -> Key:
    """The (kind, canonical id) an entry is about, whether written as `repo` or `artifact`."""
    if "artifact" in entry:
        return (entry["artifact"]["kind"], _canonical(entry["artifact"]["kind"], entry["artifact"]["id"]))
    return ("github", _canonical("github", entry.get("repo", "")))


def relation_of(entry: Mapping) -> str:
    """The question an entry answers. Absent means `product_equivalence` - every entry written
    before 2026-09 answered that question and none named a relation."""
    return entry.get("relation") or "product_equivalence"


def load(path: Path = LEDGER) -> dict[tuple[Key, str], dict]:
    """Ledger keyed by `((kind, canonical id), relation)`.

    A duplicate (artifact, relation) pair raises rather than resolving last-write-wins. The dict
    comprehension this replaced would silently keep whichever entry came last, so
    `Foo/Bar: existing_product` followed by `foo/bar: unresolved` would quietly discard the
    stronger decision - and the file is hand-edited by people appending after each review, which
    is exactly how that happens. `docs/reference/identity.md` records the same failure in the
    deleted slug-alias mapping: two renames of one retired slug, and whichever came last won.

    The same artifact may carry both an equivalence ruling and a membership ruling - a package
    can simultaneously not be a new product on its own AND be ruled in or out of another
    product's measurement - so uniqueness is enforced per relation, not per artifact.
    """
    if not path.exists():
        return {}
    doc = yaml.safe_load(path.read_text()) or {}
    out: dict[tuple[Key, str], dict] = {}
    for entry in (doc.get("resolutions") or []):
        k = key_for(entry)
        relation = relation_of(entry)
        composite = (k, relation)
        if composite in out:
            prior = out[composite]
            raise DuplicateResolution(
                f"{path.name}: {k} is resolved twice for {relation!r} - already "
                f"{prior['verdict']!r} from {prior.get('decided_in')}, now "
                f"{entry.get('verdict')!r} from {entry.get('decided_in')}. Identity is compared "
                f"canonicalized, so these are one artifact. Merge them."
            )
        out[composite] = entry
    return out


def verdict_for(kind: str, ident: str, relation: str, ledger: Mapping | None = None) -> dict | None:
    """The recorded ruling for an artifact and relation, or None if never resolved.

    `verdict_for("github", repo, "product_equivalence")` behaves exactly as the old single-arg
    `verdict_for(repo)` did for repo entries: `_canonical` strips `.git` and lowercases here just
    as `load` does when building the keys, so a differently-cased or `.git`-suffixed lookup still
    matches.
    """
    ledger = load() if ledger is None else ledger
    return ledger.get(((kind, _canonical(kind, ident)), relation))


def blocks_new_product(kind: str, ident: str, ledger: Mapping | None = None) -> dict | None:
    """The entry that PERMANENTLY forbids minting a product from this artifact, if any.

    Relation `product_equivalence` only. This is what `build/validate.py` enforces, and it
    deliberately excludes `unresolved`: a person may still add such a product by hand once they
    have settled the question, and the build should not stop them.
    """
    entry = verdict_for(kind, ident, "product_equivalence", ledger)
    return entry if entry and entry["verdict"] in NOT_A_NEW_PRODUCT else None


def holds_bulk_promotion(kind: str, ident: str, ledger: Mapping | None = None) -> dict | None:
    """The entry that stops a BULK run from promoting this artifact, if any.

    Relation `product_equivalence`, any verdict - `unresolved` included. "Not permanently
    excluded" and "this proposal may proceed" are different questions, and conflating them
    published a bug: the #418 review recorded `ag-ui` as a protocol filed under agent frameworks,
    `serena` as an MCP retrieval toolkit and `repomix` as document ingestion - and then the same
    run published all three in `orchestration_agents`, the category the entry says is wrong.

    `unresolved` means the artifact may come back to a LATER sweep, not that the CURRENT
    proposal is fit to publish. A bulk run parks it for a person; a person resolves it.
    """
    return verdict_for(kind, ident, "product_equivalence", ledger)


def membership_ruling(kind: str, ident: str, product_slug: str, ledger: Mapping | None = None) -> dict | None:
    """The `product_membership` ruling for this artifact against `product_slug`, if any.

    Only returns an entry whose `resolves_to` matches `product_slug`: a `member_of` or
    `not_member_of` ruling is a statement about ONE product's measurement, not a global fact
    about the artifact, so a lookup against a different product must not see it.
    """
    entry = verdict_for(kind, ident, "product_membership", ledger)
    return entry if entry and entry.get("resolves_to") == product_slug else None
