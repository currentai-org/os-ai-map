"""Derive the ``declaration_version_id`` — the identity of a set of declarations.

Three identities run through the release model (data-architecture.md §4.6), and they are
deliberately distinct:

    declaration_version_id = source_git_sha + source_content_digest + evaluator_version
    observation_snapshot_id = digest of the normalized observation content, and nothing else
    release_id             = declaration_version_id + observation_snapshot_id
                             + reconciliation_policy_version

This module owns the first. It answers "which declarations, evaluated by which evaluator" —
the identity that ``registry.axis_assessments``, ``evaluation.product_adoption_measurements``
and ``evaluation.adoption_reconciliation`` all key on. It says nothing about measurements
(that is the observation snapshot) and nothing about a published release (that is the release
id, which only exists once a declaration/observation pair has passed reconciliation).

## What the digest covers, and what it must not

``source_content_digest`` is a canonical hash over the DECLARATION tree alone — the
curator-authored records that ``build.validate.load_sources`` parses: products,
organizations, categories, scores, rubrics, the taxonomy, and the long-tail registry seeds.
Those are exactly the inputs a reconciliation adjudicates a measurement against.

Three exclusions are deliberate, because including any of them would make the id move for a
reason that is not a change in the declarations:

  * The frozen ``sources/snapshots/long_tail.json`` warehouse sample. It is a hand-synced
    point-in-time count, not a scoring declaration; a re-sync must not mint a new declaration
    version. ``load_sources`` exposes it under ``long_tail``; ``DECLARATION_KEYS`` omits it.
  * The derived score projections (``overall_score``, ``tier``, ``maturity``, ``mature``).
    Those are computed by the evaluator from the declared axis values, so folding them in
    would double-count the evaluator — whose contribution is already named separately by
    ``evaluator_version`` — and would make ``source_content_digest`` change when the scoring
    formula changes, breaking the clean three-way split. ``load_sources`` carries only the
    RECORDED axis values under ``scores``; the derived numbers live downstream in
    ``build.serialize`` and never enter this digest.
  * The routing policy (``sources/signal_routing.yaml``). It publishes under its own
    ``routing_policy_version`` (see ``test_serialize_routing``) and is applied in the
    evaluation layer, not declared per product; it is not a scoring declaration.

## No frozen receipt, on purpose

Unlike ``warehouse/audits/source_runs.json``, this module writes no committed receipt. A
``declaration_version_id`` embeds ``source_git_sha``, and no commit can record its own SHA —
a receipt committed alongside the value would forever name its own parent. §12.1 resolves
this by DERIVING the id at release time from the resolved SHA, which is what this module does:
it is a pure computation the release builder (and any consumer keying a candidate table) calls,
not a stored constant. ``source_content_digest`` alone is git-SHA-independent and reproducible,
but freezing it would demand a regenerate-and-gate step on every score edit; the tests pin the
canonicalization's PROPERTIES (determinism, order-invariance, the digested key-set) instead of
a brittle golden value.

Usage:
    uv run python -m build.declaration_version            # print the components at HEAD
    uv run python -m build.declaration_version --json     # same, machine-readable
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]

# Bumped when the digested key-set, the serialization, or the id composition changes, so a
# value computed under an older rule cannot silently pass for a current one.
CANONICALIZATION_VERSION = 1

# The repository-owned evaluator is Phase 6 (docs/architecture/migration-status.md); it does
# not exist yet. Until it lands, the evaluator component is a declared sentinel rather than a
# real version, so a ``declaration_version_id`` is well-formed and forward-compatible today and
# only its evaluator component moves when Phase 6 ships. It is NOT the empty string: an absent
# evaluator is a deliberate state ("scores are curator-recorded, not machine-derived"), and the
# sentinel records that rather than leaving a field that reads as "unset".
EVALUATOR_VERSION = "v0-no-repo-evaluator"

# The declaration subtrees of ``load_sources`` that the digest covers. This is the whole of
# ``load_sources`` EXCEPT ``long_tail`` (the frozen warehouse sample). Kept explicit, and gated
# by ``test_declaration_keys_cover_every_declaration_subtree``, so a newly added declaration
# directory cannot slip out of the identity unnoticed.
DECLARATION_KEYS: tuple[str, ...] = (
    "organizations",
    "categories",
    "rubrics",
    "products",
    "scores",
    "taxonomy",
    "registry",
)

# Everything ``load_sources`` may return that is deliberately NOT a declaration.
NON_DECLARATION_KEYS: frozenset[str] = frozenset({"long_tail"})


def canonical_json(obj: object) -> str:
    """The one canonical serialization every digest here is taken over.

    Canonicalization rule (data-architecture.md §4.7), version ``CANONICALIZATION_VERSION``:

      * format: JSON, UTF-8, no insignificant whitespace (``separators=(",", ":")``);
      * key ordering: every mapping sorted by key (``sort_keys=True``), so a curator
        reordering a YAML file produces no change;
      * strings: preserved verbatim, not ASCII-escaped (``ensure_ascii=False``);
      * dates/other scalars: rendered by ``str`` (``default=str``), so a YAML ``date`` becomes
        its ISO ``YYYY-MM-DD`` text deterministically rather than a Python object;
      * null: JSON ``null``.
    """
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str
    )


def declaration_content(root: Path | None = None) -> dict:
    """The declaration tree the digest is taken over: ``load_sources`` minus non-declarations.

    Raises if ``load_sources`` stops exposing a declared key, so the digest can never quietly
    narrow to a subset of the declarations.
    """
    sources = load_sources(root or ROOT)
    missing = [k for k in DECLARATION_KEYS if k not in sources]
    if missing:
        raise KeyError(f"load_sources is missing declaration keys: {sorted(missing)}")
    return {k: sources[k] for k in DECLARATION_KEYS}


def source_content_digest(root: Path | None = None) -> str:
    """sha256 over the canonicalized declaration tree. Git-SHA-independent and reproducible."""
    payload = canonical_json(declaration_content(root))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_git_sha(root: Path | None = None) -> str:
    """The exact commit the declarations are read from (§12.1 step 1)."""
    result = subprocess.run(
        ["git", "-C", str(root or ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def declaration_paths_are_clean(root: Path | None = None) -> bool:
    """True when no declaration file has uncommitted changes.

    A ``declaration_version_id`` pairs the working-tree digest with ``HEAD``'s SHA. When a
    declaration file is dirty the two describe different states, so the derived id is not
    reproducible from the SHA alone. The CLI surfaces this rather than emitting a misleading id.
    """
    base = root or ROOT
    result = subprocess.run(
        ["git", "-C", str(base), "status", "--porcelain", "--", "sources/"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() == ""


def declaration_version_id(
    source_git_sha: str,
    content_digest: str,
    evaluator_version: str = EVALUATOR_VERSION,
) -> str:
    """Compose the three components into one opaque, reproducible identity.

    A hash rather than a concatenation so the id is fixed-width and unambiguous; the human-
    readable ``source_git_sha`` is carried alongside it on the tables that key on this
    (``registry.axis_assessments``), never parsed back out of the id. The canonicalization
    version is folded in so a rule change cannot collide with a value minted under the old rule.
    """
    payload = canonical_json(
        {
            "canonicalization_version": CANONICALIZATION_VERSION,
            "evaluator_version": evaluator_version,
            "source_content_digest": content_digest,
            "source_git_sha": source_git_sha,
        }
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve(root: Path | None = None) -> dict:
    """Derive every component and the id at ``HEAD`` over the working-tree declarations."""
    base = root or ROOT
    digest = source_content_digest(base)
    git_sha = resolve_git_sha(base)
    return {
        "canonicalization_version": CANONICALIZATION_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "source_git_sha": git_sha,
        "source_content_digest": digest,
        "declaration_version_id": declaration_version_id(git_sha, digest),
        "declarations_clean": declaration_paths_are_clean(base),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the components as JSON")
    args = parser.parse_args()

    info = resolve()
    if args.json:
        print(json.dumps(info, indent=2))
        return 0

    print(f"canonicalization_version  {info['canonicalization_version']}")
    print(f"evaluator_version         {info['evaluator_version']}")
    print(f"source_git_sha            {info['source_git_sha']}")
    print(f"source_content_digest     {info['source_content_digest']}")
    print(f"declaration_version_id    {info['declaration_version_id']}")
    if not info["declarations_clean"]:
        print(
            "\nWARNING: sources/ has uncommitted changes. The digest is taken over the working\n"
            "tree but source_git_sha is HEAD, so this declaration_version_id is not reproducible\n"
            "from that SHA. Commit the declarations first."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
