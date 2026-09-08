"""Read `sources/withdrawals.yaml` -- the products that left the corpus with no successor.

A rename is carried by an `aliases` entry on the product that replaced it, and every gate
that watches slugs leaving reads that alias map. A withdrawal has nothing to alias onto, so
before this file the repository could not tell a ruled removal apart from a file somebody
deleted by accident, and the safe answer -- fail on any deletion -- is the one two gates took.
That made a product undeletable, which is why nothing had ever been withdrawn.

This module is the one place that answers "is this slug's absence accounted for". Three
consumers ask it, and each keeps failing everything it does not cover:

  * `build/validate.py` -- the entry's shape, and that the slug really is gone from the live
    corpus (no product file, no score file, no roster line, no alias claiming it).
  * `build/check_retirement.py` -- a slug that fell out of the payload passes iff a withdrawal
    carries it; every other disappearance still fails as an unrouted retirement.
  * `build/assets.py` -- a file under `sources/` deleted since the ADR-003 base commit is
    accounted for iff a withdrawal names it in `removed_files`. The externalization receipt is
    for externalized warehouse tables, and writing a product file into it would make the
    receipt say something false.

The file is a ruling record, not a declaration: it changes no product's identity, artifacts or
score, so `build/declaration_version.py` classifies it as a non-declaration input.

Normative prose: docs/reference/identity.md, "Withdrawal: a product that ends with no
successor". Shape: docs/schemas/withdrawals.schema.json.
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WITHDRAWALS = ROOT / "sources" / "withdrawals.yaml"
SCHEMA_VERSION = 1


def load(root: Path | None = None) -> dict:
    """The withdrawals document, or an empty one if the file is absent.

    Absence is legitimate: `build/check_corpus_diff.py` loads a base-commit checkout that
    predates the file, and a tree with nothing withdrawn is not malformed. Every consumer
    below treats an empty document as "nothing is accounted for", which is the conservative
    reading -- it never turns a real deletion green.
    """
    path = (root / "sources" / "withdrawals.yaml") if root else WITHDRAWALS
    if not path.exists():
        return {"version": SCHEMA_VERSION, "withdrawals": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {
        "version": SCHEMA_VERSION,
        "withdrawals": [],
    }


def entries(root: Path | None = None) -> list[dict]:
    """Every withdrawal entry, skipping any non-mapping slot (the schema check reports those)."""
    doc = load(root)
    return [e for e in (doc.get("withdrawals") or []) if isinstance(e, dict)]


def withdrawn_slugs(root: Path | None = None) -> set[str]:
    """The slugs a withdrawal accounts for. Reserved forever; never reused."""
    return {e["slug"] for e in entries(root) if isinstance(e.get("slug"), str)}


def removed_files(root: Path | None = None) -> set[str]:
    """Every repo-relative path the withdrawals say they deleted."""
    paths: set[str] = set()
    for e in entries(root):
        for p in e.get("removed_files") or []:
            if isinstance(p, str):
                paths.add(p)
    return paths


def problems(
    doc: dict,
    *,
    products: dict | None = None,
    scores: dict | None = None,
    categories: dict | None = None,
    organizations: dict | None = None,
    aliases: dict | None = None,
    root: Path | None = None,
) -> list[str]:
    """Everything wrong with the withdrawals document, as `validate_sources` phrases errors.

    Two families of check, and the second is the one that matters. The first is shape --
    a version this code understands, no duplicate slug, an entry that names the files it
    removed. The second is that the entry is TRUE of the tree it sits in: a withdrawal that
    still has a live product file, a roster line, or an alias pointing at its slug is a record
    of something that did not happen, and it would hand `check_retirement` a pass for a slug
    that never left.
    """
    problems: list[str] = []
    version = doc.get("version")
    if version != SCHEMA_VERSION:
        problems.append(
            f"sources/withdrawals.yaml: version {version!r} is not {SCHEMA_VERSION}; this code "
            "reads version 1 only, and a document it cannot read must not pass silently"
        )
    rows = doc.get("withdrawals")
    if rows is not None and not isinstance(rows, list):
        problems.append("sources/withdrawals.yaml: `withdrawals` must be a list")
        return problems

    root = root or ROOT
    products = products or {}
    scores = scores or {}
    categories = categories or {}
    organizations = organizations or {}
    aliases = aliases or {}

    seen: set[str] = set()
    for i, entry in enumerate(rows or []):
        if not isinstance(entry, dict):
            problems.append(f"sources/withdrawals.yaml: entry {i} is not a mapping")
            continue
        slug = entry.get("slug")
        label = f"withdrawal {slug!r}" if slug else f"withdrawal entry {i}"
        if not isinstance(slug, str) or not slug:
            problems.append(f"sources/withdrawals.yaml: entry {i} has no slug")
            continue
        if slug in seen:
            problems.append(
                f"sources/withdrawals.yaml: {slug!r} is withdrawn twice. A slug leaves once."
            )
        seen.add(slug)

        # `alias` is required and must be null: an omitted field reads as "nobody thought
        # about it", which is exactly the confusion between a withdrawal and a rename that
        # the explicit null exists to stop.
        if "alias" not in entry:
            problems.append(
                f"{label}: `alias` is required and must be null. A withdrawal with a target is "
                "a rename, and belongs in the replacing product's `aliases` array."
            )
        elif entry.get("alias") is not None:
            problems.append(
                f"{label}: alias is {entry['alias']!r}, but a withdrawal has no successor. "
                "Record a rename as an alias on the product that replaced it instead."
            )

        # The entry must be true of this tree. Each of these would otherwise let a slug that
        # is still live be treated as accounted-for by check_retirement.
        if slug in products:
            problems.append(f"{label}: sources/products/{slug}.yaml still exists")
        if slug in scores:
            problems.append(f"{label}: sources/scores/{slug}.yaml still exists")
        for cid, cat in sorted(categories.items()):
            if slug in (cat.get("products") or []):
                problems.append(f"{label}: still on the {cid} category roster")
        for oslug, org in sorted(organizations.items()):
            if slug in (org.get("products") or []):
                problems.append(f"{label}: still on the {oslug} organization roster")
        if slug in aliases:
            problems.append(
                f"{label}: {aliases[slug]!r} claims {slug!r} as an alias, so this is a rename, "
                "not a withdrawal. Drop the withdrawal entry or drop the alias."
            )

        # `removed_files` is what build/assets.py reads to tell a ruled deletion from an
        # unrecorded one, so an entry that omits the two files every withdrawal deletes
        # leaves those files looking unaccounted for.
        declared = [p for p in (entry.get("removed_files") or []) if isinstance(p, str)]
        for required in (f"sources/products/{slug}.yaml", f"sources/scores/{slug}.yaml"):
            if required not in declared:
                problems.append(
                    f"{label}: removed_files does not name {required}, which every withdrawal "
                    "deletes. build/assets.py reads this list to tell a ruled deletion from an "
                    "unrecorded one."
                )
        for p in declared:
            if not p.startswith("sources/"):
                problems.append(f"{label}: removed_files entry {p!r} is not under sources/")
            elif (root / p).exists():
                problems.append(
                    f"{label}: removed_files names {p}, which still exists. The record says the "
                    "file is gone and it is not."
                )
    return problems
