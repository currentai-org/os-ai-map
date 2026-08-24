"""Derive the ``declaration_version_id`` — the identity of a set of declarations.

Three identities run through the release model (data-architecture.md §4.5), and they are
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

## What the digest covers: every authoritative declaration input, gated

``source_content_digest`` is a canonical hash over the DECLARATION inputs of ``sources/`` — the
curator-authored records whose change should mint a new declaration version. Every top-level
entry of ``sources/`` is classified into exactly one of three buckets below, and
``test_source_inventory_is_fully_classified`` walks the directory and fails if a new entry is
unclassified. The gate protects the whole ``sources/`` inventory, not just what
``build.validate.load_sources`` happens to parse — ``evidence_policy.yaml`` and
``verification_queue.yaml`` are authoritative declaration inputs that ``load_sources`` does not
return, and both are folded in here.

  * ``DECLARATION_INPUTS`` — content IS the declaration; folded into the digest.
  * ``POLICY_INPUTS`` — excluded from ``declaration_version_id`` because the input carries its
    OWN version and is applied in a downstream layer, not in the declaration compile. The
    exclusion is a redirection, not a gap: each names the downstream identity its policy version
    must bind into. ``signal_routing.yaml`` is the case — it publishes under
    ``routing_policy_version`` (see ``test_serialize_routing``) and is applied in evaluation, so
    its version binds into ``evaluation.adoption_reconciliation`` / ``release_id`` when those are
    built, never into this identity.
  * ``NON_DECLARATION_INPUTS`` — not a scoring declaration at all (the frozen long-tail
    warehouse sample); excluded with a reason.

The derived score projections (``overall_score``, ``tier``, ``maturity``, ``mature``) are also
excluded, by construction rather than by name: they are computed by ``build.serialize`` from the
declared axis values and never live in ``sources/``. Folding them in would double-count the
evaluator, whose contribution is already named by ``evaluator_version``.

## No frozen receipt, on purpose

Unlike ``warehouse/audits/source_runs.json``, this module writes no committed receipt. A
``declaration_version_id`` embeds ``source_git_sha``, and no commit can record its own SHA —
a receipt committed alongside the value would forever name its own parent. §12.1 resolves
this by DERIVING the id at release time from the resolved SHA, which is what this module does:
it is a pure computation the release builder (and any consumer keying a candidate table) calls,
not a stored constant. ``source_content_digest`` alone is git-SHA-independent and reproducible,
but freezing it would demand a regenerate-and-gate step on every score edit; the tests pin the
canonicalization's PROPERTIES (determinism, order-invariance, the digested inventory, type
rejection) instead of a brittle golden value.

Because the digest is taken over the working tree while ``source_git_sha`` is ``HEAD``, a dirty
``sources/`` tree yields an id that no SHA can reproduce. ``resolve`` therefore FAILS CLOSED on
uncommitted declarations; a diagnostic value over a dirty tree requires an explicit opt-in
(``allow_dirty`` / CLI ``--allow-dirty``).

Usage:
    uv run python -m build.declaration_version                # print the components at HEAD
    uv run python -m build.declaration_version --json         # same, machine-readable
    uv run python -m build.declaration_version --allow-dirty  # diagnostic over a dirty tree
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Bumped when the classified inventory, the serialization, or the id composition changes, so a
# value computed under an older rule cannot silently pass for a current one.
CANONICALIZATION_VERSION = 1

# The repository-owned evaluator is Phase 6 (docs/architecture/migration-status.md); it does
# not exist yet. Until it lands, the evaluator component is a declared sentinel rather than a
# real version, so a ``declaration_version_id`` is well-formed and forward-compatible today and
# only its evaluator component moves when Phase 6 ships. It is NOT the empty string: an absent
# evaluator is a deliberate state ("scores are curator-recorded, not machine-derived"), and the
# sentinel records that rather than leaving a field that reads as "unset".
EVALUATOR_VERSION = "v0-no-repo-evaluator"

# --- the classified sources/ inventory -------------------------------------------
# Every top-level entry of sources/ is in exactly one of the three collections below;
# test_source_inventory_is_fully_classified fails if that stops being true.

# Declaration inputs — their content IS the declaration; a change mints a new
# declaration_version_id. Directories are read file-by-file; a .txt allowlist is reduced to its
# semantic set of entries (matching the repo's own parse in tests/test_digest_ratchet.py).
DECLARATION_INPUTS: tuple[str, ...] = (
    "allowlists",
    "categories",
    "evidence_policy.yaml",
    "organizations",
    "products",
    "registry",
    "rubrics",
    "scores",
    "taxonomy.yaml",
    "verification_queue.yaml",
)

# Policy inputs — excluded from declaration_version_id because they carry their OWN version and
# are applied in a downstream layer, not in the declaration compile. Each MUST have its policy
# version bound into the downstream identity named here when that identity is built.
POLICY_INPUTS: dict[str, dict[str, str]] = {
    "signal_routing.yaml": {
        "policy_version": "routing_policy_version",
        "bound_into": "evaluation.adoption_reconciliation / release_id",
        "reason": (
            "routing is applied in the evaluation layer, not declared per product; it "
            "publishes under routing_policy_version (see test_serialize_routing)."
        ),
    },
}

# Non-declaration inputs — authored nowhere as a scoring declaration.
NON_DECLARATION_INPUTS: dict[str, str] = {
    "snapshots": (
        "frozen point-in-time warehouse sample (long_tail.json), hand-synced; a re-sync is "
        "not a change in the declarations."
    ),
}


def _canonical_default(value: object) -> str:
    """Serialize the one non-JSON-native type the declarations use (dates); reject the rest.

    ``json.dumps`` calls this only for values it cannot serialize itself. A YAML ``!!set`` or an
    unexpected object would otherwise slip through a permissive ``str`` fallback and become an
    implementation-dependent string — a silently non-reproducible identity. Only dates are
    accepted (rendered ISO); everything else raises.
    """
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    raise TypeError(
        f"canonical_json cannot serialize a value of type {type(value).__name__!r}; "
        "only JSON scalars, lists, dicts, and dates are supported."
    )


def canonical_json(obj: object) -> str:
    """The one canonical serialization every digest here is taken over.

    Canonicalization rule (data-architecture.md §4.5), version ``CANONICALIZATION_VERSION``:

      * format: JSON, UTF-8, no insignificant whitespace (``separators=(",", ":")``);
      * key ordering: every mapping sorted by key (``sort_keys=True``), so a curator
        reordering a YAML file produces no change;
      * strings: preserved verbatim, not ASCII-escaped (``ensure_ascii=False``);
      * dates: rendered as ISO text; null as JSON ``null``;
      * numbers: finite only — ``allow_nan=False`` rejects ``NaN``/``Infinity``, which are not
        valid JSON and do not round-trip reproducibly;
      * types: only JSON scalars, lists, dicts, and dates; any other type is rejected rather
        than coerced (``_canonical_default``).
    """
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_canonical_default,
        allow_nan=False,
    )


def _read_declaration_input(path: Path) -> object:
    """Read one declaration input into its canonical, format-invariant content.

    YAML is parsed (dropping comments and key order); a ``.txt`` allowlist is reduced to the
    sorted set of its non-comment, non-blank lines, exactly as the repo's own gate reads it, so
    a comment edit does not mint a new version but an added or removed entry does.
    """
    if path.is_dir():
        out: dict[str, object] = {}
        for child in sorted(path.iterdir()):
            if not child.is_file():
                raise ValueError(f"unexpected non-file in declaration input: {child}")
            if child.suffix in (".yaml", ".yml"):
                out[child.name] = yaml.safe_load(child.read_text(encoding="utf-8"))
            elif child.suffix == ".txt":
                out[child.name] = sorted(
                    {
                        line.strip()
                        for line in child.read_text(encoding="utf-8").splitlines()
                        if line.strip() and not line.startswith("#")
                    }
                )
            else:
                raise ValueError(f"unclassified file type in declaration input: {child}")
        return out
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise ValueError(f"unsupported declaration input file: {path}")


def declaration_content(root: Path | None = None) -> dict:
    """The declaration tree the digest is taken over: every ``DECLARATION_INPUTS`` entry.

    Raises if a declared input is missing from disk, so the digest can never quietly narrow to a
    subset of the declarations.
    """
    base = (root or ROOT) / "sources"
    content: dict[str, object] = {}
    for name in DECLARATION_INPUTS:
        path = base / name
        if not path.exists():
            raise FileNotFoundError(f"declaration input missing: sources/{name}")
        content[name] = _read_declaration_input(path)
    return content


def source_content_digest(root: Path | None = None) -> str:
    """sha256 over the canonicalized declaration inputs. Git-SHA-independent and reproducible."""
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
    reproducible from the SHA alone.
    """
    result = subprocess.run(
        ["git", "-C", str(root or ROOT), "status", "--porcelain", "--", "sources/"],
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


class DirtyDeclarationsError(RuntimeError):
    """Raised when an id is requested over a working tree with uncommitted declarations."""


def resolve(root: Path | None = None, allow_dirty: bool = False) -> dict:
    """Derive every component and the id at ``HEAD`` over the working-tree declarations.

    Fails closed when ``sources/`` is dirty: the digest is over the working tree but the SHA is
    ``HEAD``, so the pair is not reproducible. ``allow_dirty`` returns a diagnostic value anyway,
    with ``declarations_clean`` recording the state.
    """
    base = root or ROOT
    clean = declaration_paths_are_clean(base)
    if not clean and not allow_dirty:
        raise DirtyDeclarationsError(
            "sources/ has uncommitted changes: the working-tree digest would pair with HEAD's "
            "SHA and would not be reproducible from it. Commit the declarations first, or pass "
            "allow_dirty=True (CLI --allow-dirty) for a diagnostic-only value."
        )
    digest = source_content_digest(base)
    git_sha = resolve_git_sha(base)
    return {
        "canonicalization_version": CANONICALIZATION_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "source_git_sha": git_sha,
        "source_content_digest": digest,
        "declaration_version_id": declaration_version_id(git_sha, digest),
        "declarations_clean": clean,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the components as JSON")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="emit a diagnostic id over an uncommitted sources/ tree (not reproducible)",
    )
    args = parser.parse_args()

    try:
        info = resolve(allow_dirty=args.allow_dirty)
    except DirtyDeclarationsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

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
            "\nWARNING: sources/ has uncommitted changes. This is a diagnostic value only — the\n"
            "digest is over the working tree but source_git_sha is HEAD, so it is not\n"
            "reproducible from that SHA."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
