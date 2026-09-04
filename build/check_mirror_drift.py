"""Does each mirror contract still describe the model the platform is actually running?

## The gap this closes

`warehouse/dependencies.yaml` records, for every platform-authored model the repo mirrors
read-only, a `mirror:` block naming the revision, the platform's hash for it, and a
`local_sha256` over the bytes on disk. `build/assets.dependency_violations` proves that block
is internally honest: the file on disk is the file the contract claims, the revision matches
the anchor, and bytes and revision move together across commits.

Every one of those checks reads only the repo. None of them can tell you that the contract
still matches the platform. A model can be revised on the platform the day after a mirror is
synced, and the repo stays green: the file still hashes to `local_sha256`, the anchor still
equals `mirror.revision`, and nothing anywhere compares either number to the platform. The
repo then evaluates, reviews and reasons about revision N while revision N+1 is what builds
the table. That is the whole failure, and it is silent in exactly the direction that matters —
the more confident the gates look, the more stale the mirror can be.

So this is a sentinel, not a validator. It reaches out to the platform once a week and asks a
single question per contract: is the revision we wrote down still the revision you have?

## What "the platform's current revision" can and cannot mean here

The platform's own deploy mechanic is revision -> RELEASE -> run (see
`docs/operations/deploy-models.md`), and a run materializes the latest *released* revision.
Release state is not readable: `GetDataModel` returns `latestRevision` and no release field,
and `GetAssetChangelog`'s `publishStatus` is null on every revision of every model in this
org. There is no query that answers "which revision is released".

This check therefore compares against `latestRevision`, and says so rather than calling it
the released one. The consequence is worth being explicit about, because it decides whether a
finding is real:

  * A contract BEHIND the latest revision is always worth a human look. Either the newer
    revision is released, in which case the mirror is describing code that no longer runs, or
    it is not, in which case the mirror is about to be wrong and the resync is cheap now.
  * The check cannot fire on the reverse case — a revision released without a new revision
    being minted — because that is not a thing the platform does.

Erring toward "tell a human" is the right side to err on for a once-weekly gate whose whole
job is to notice something no other gate can see.

## Three levels of drift, reported separately

Given one contract and one platform node, they can disagree in three ways, and they mean
different things:

  * `revision` — the numbers differ. The plain case: the platform moved on.
  * `hash` — the numbers agree and the platform's hash does not. Worse than a revision bump,
    because it means the same revision number now denotes different content, and nothing in
    the repo's own gates could ever see it. Identical code does not soften this one: either the
    platform rewrote a revision in place or the contract's hash is mis-pinned.
  * `code` — numbers and hash agree, and the deployed source does not match the mirror file's
    body. This is the belt-and-braces check: it does not trust the hash to be a hash of the
    code, and it is the only one of the three that a maintainer editing a mirror file by hand
    (and dutifully updating `local_sha256`) cannot defeat.

`missing` is a fourth and the loudest: the platform serves no model at that `model_id` at all,
so the contract is anchored to something that no longer exists.

## `metadata-only`, which is not drift

The platform mints a revision for changes that touch no code: a cron cleared, a description
filled in. The revision numbers then disagree while the deployed source is byte-identical to the
mirror, and calling that drift sends a maintainer to resync a file that cannot change. So the
code comparison runs on every contract, not only on the ones whose numbers already agree, and a
NEW REVISION over identical code is reported as `metadata-only` and exits 0.

The "new revision" half is load-bearing, and it is why a hash disagreement at an unchanged
revision number stays `hash` however well the code matches. There is nothing to record in that
case: `mirror.code_unchanged_from` authorizes advancing to a revision, the coherence gate
rejects a marker whose revision does not advance, and so reporting it as metadata-only would
instruct a commit the repo's own gate refuses.

Exit 1 is therefore `code` drift, a `hash` disagreement, and a revision mismatch whose deployed
source really does differ. `metadata-only` is still worth recording in the contract —
`mirror.code_unchanged_from` is how (see the `dependencies.yaml` header) — but it is a
bookkeeping job, not a stale mirror.

## The banner

Mirror files are not byte-identical to the deployed code, by design: each carries a five-line
`PLATFORM MIRROR (read-only)` header saying nothing deploys from this copy. That header is the
reason `mirror.local_sha256` and `mirror.hash` are different hashes of nearly the same text,
and the reason a naive code comparison fails on all seventeen contracts. `strip_mirror_banner`
removes it, in the `--` and `#` forms both families of mirror use.

## Two exit codes, and the line between them

  * **1 — drift.** Every contract was checked and at least one disagrees with the platform.
    The maintainer's job is a resync.
  * **2 — could not check.** Nothing was verified. The maintainer's job is to find out why,
    and a resync would be wasted work.

That line matters more than it looks, because `report-failure.yml` turns either into the same
`sentinel` issue and the exit code is what tells a maintainer which job they have. Everything
that stops the check from happening lands in 2: the endpoint unreachable, a non-200 response,
a 200 carrying `isError` (which is what an expired or rotated `OSO_API_KEY` looks like — the
server answers cheerfully and refuses the call), and a response body that will not decode.

An authentication failure reported as drift would send someone to diff seventeen mirror files
against a platform nobody can read. So `MCPCallFailed` is caught here alongside
`MCPUnreachable` rather than being allowed to escape as a traceback, and the message names
which of the two happened.

The check never skips and never passes on a failure to read. A sentinel that goes quiet when
it loses its only source of truth is worse than no sentinel, because the green tick is then
evidence of nothing while still reading as evidence.

Requires OSO_API_KEY. Reads platform metadata through `build/oso_mcp.py`; see that module for
why SQL cannot answer this and for the two transport traps.

Usage:
    uv run python -m build.check_mirror_drift
    uv run python -m build.check_mirror_drift --report mirror-drift.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from build.oso_mcp import Client, MCPCallFailed, MCPUnreachable

ROOT = Path(__file__).resolve().parents[1]
BANNER_MARKER = "PLATFORM MIRROR"
# The banner is a comment block followed by one blank line. Held as a bound rather than a
# pattern: if a mirror's header ever grows, the code comparison should fail loudly and be
# looked at, not silently strip more of the model than it meant to.
BANNER_MAX_LINES = 8


def strip_mirror_banner(text: str) -> str:
    """`text` without its leading `PLATFORM MIRROR` header, or unchanged if it has none.

    Unchanged rather than raising, so a mirror file that has lost its banner is compared as
    it stands and reported as code drift -- which is what it is.
    """
    lines = text.splitlines(keepends=True)
    if not lines or BANNER_MARKER not in lines[0]:
        return text
    for index, line in enumerate(lines[:BANNER_MAX_LINES]):
        if line.strip() == "":
            return "".join(lines[index + 1:])
    return text


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass
class Row:
    """One contract's verdict. `status` is the finding; the rest is what it was based on."""

    table: str
    status: str
    contract_revision: int | None
    platform_revision: int | None
    hash_match: bool | None
    code_match: bool | None
    revised_at: str | None
    detail: str = ""

    @property
    def drifted(self) -> bool:
        """Whether a maintainer has a resync to do. `metadata-only` is a finding, not drift."""
        return self.status not in ("ok", "metadata-only")

    @property
    def metadata_only(self) -> bool:
        return self.status == "metadata-only"


def mirror_contracts(root: Path) -> list[dict]:
    """The dependency contracts carrying a `mirror:` block, in file order.

    An `oso.*` upstream anchors on a content contract instead and has no revision to compare,
    so it is out of scope by construction rather than by exclusion.
    """
    doc = yaml.safe_load((root / "warehouse/dependencies.yaml").read_text()) or {}
    return [d for d in (doc.get("dependencies") or []) if d.get("mirror")]


def code_verdict(contract: dict, revision: dict, root: Path) -> tuple[bool, str]:
    """Whether the deployed source matches the mirror file below its banner, and why not.

    Run on every contract, not only where the numbers agree, because it is what separates a
    metadata-only platform revision from a stale mirror.
    """
    path = root / contract["files"]["model"]
    if not path.exists():
        # dependency_violations already fails on this; reported here too so a drift run
        # against a broken tree explains itself rather than raising.
        return False, f"mirror file {contract['files']['model']} is missing"
    local = strip_mirror_banner(path.read_text())
    deployed = revision.get("code") or ""
    if sha256_text(local) != sha256_text(deployed):
        return False, (
            f"the deployed source does not match {contract['files']['model']} below its banner "
            f"({len(deployed)} chars deployed against {len(local)} mirrored)"
        )
    return True, ""


def compare(contract: dict, node: dict | None, root: Path) -> Row:
    """One contract against one platform node. Pure, so the tests can stub the client."""
    table = contract["table"]
    mirror = contract["mirror"]
    contract_revision = mirror.get("revision")

    if node is None:
        return Row(
            table=table, status="missing", contract_revision=contract_revision,
            platform_revision=None, hash_match=None, code_match=None, revised_at=None,
            detail=f"the platform serves no data model at model_id {mirror.get('model_id')}",
        )

    revision = node.get("latestRevision") or {}
    platform_revision = revision.get("revisionNumber")
    platform_hash = revision.get("hash")
    revised_at = revision.get("createdAt")

    revision_match = platform_revision == contract_revision
    hash_match = platform_hash == mirror.get("hash")
    # The source comparison decides every remaining case, so it runs before the numbers are
    # judged. It is also the only check a hand-edited mirror with a refreshed local_sha256
    # cannot get past.
    code_match, code_detail = code_verdict(contract, revision, root)

    def row(status: str, detail: str) -> Row:
        return Row(
            table=table, status=status, contract_revision=contract_revision,
            platform_revision=platform_revision, hash_match=hash_match, code_match=code_match,
            revised_at=revised_at, detail=detail,
        )

    if revision_match and hash_match:
        if code_match:
            return row("ok", "")
        return row("code", f"revision {platform_revision} and hash agree, and {code_detail}")

    numbers = (f"the platform's latest revision is {platform_revision} against the contract's "
               f"{contract_revision}" if not revision_match else
               f"revision {platform_revision} on both sides, and its hash is {platform_hash} "
               f"against the contract's {mirror.get('hash')}")

    if code_match and not revision_match:
        # A revision the platform minted without touching the code -- a cron cleared, a
        # description added. Nothing to resync; the contract records it with
        # mirror.code_unchanged_from.
        return row("metadata-only", f"{numbers}, and the deployed source is byte-identical to "
                                    f"{contract['files']['model']} below its banner")
    if not revision_match:
        return row("revision", f"{numbers}; {code_detail}")
    # Same revision number, different hash. Identical code does NOT excuse it: a metadata-only
    # revision is a new revision, and there is none here. Either the platform rewrote a revision
    # in place or the contract's `mirror.hash` is mis-pinned, and neither is recordable -- the
    # coherence gate rejects a marker whose revision does not advance, so reporting this as
    # metadata-only would instruct a commit the repo's own gate refuses.
    return row("hash", f"{numbers}; a hash change with no new revision is a mis-pin or an "
                       f"in-place rewrite, not a metadata-only revision"
                       + (f" ({code_detail})" if code_detail else
                          " -- the deployed source does match the mirror, which narrows it to "
                          "the recorded hash"))


def check(contracts: list[dict], client, root: Path) -> list[Row]:
    """Every contract's verdict.

    A per-model *answer* is allowed to be a finding -- including "the platform has no such
    model". A failure to read is not: `MCPUnreachable` and `MCPCallFailed` propagate out of
    the sweep, because half a sweep is not a result and reporting it as one would publish a
    row count that looks like coverage.
    """
    rows: list[Row] = []
    for contract in contracts:
        node = client.data_model(contract["mirror"]["model_id"])
        rows.append(compare(contract, node, root))
    return rows


def render_table(rows: list[Row]) -> str:
    def mark(value: bool | None) -> str:
        return "-" if value is None else ("yes" if value else "NO")

    header = (f"{'table':50} {'contract':>8} {'platform':>8} {'hash':>5} {'code':>5}  "
              f"{'revised_at':20} status")
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{row.table:50} {str(row.contract_revision):>8} "
            f"{str(row.platform_revision):>8} {mark(row.hash_match):>5} "
            f"{mark(row.code_match):>5}  {(row.revised_at or '-')[:19]:20} {row.status}"
        )
    lines.append(
        "\nrevised_at is when the platform's latest revision was created. The platform "
        "exposes no\nrelease timestamp and no release marker -- see build/oso_mcp.py."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None, root: Path | None = None, client=None) -> int:
    root = root or ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=None,
                        help="write the verdicts as JSON here")
    args = parser.parse_args(argv)

    contracts = mirror_contracts(root)
    try:
        rows = check(contracts, client or Client(), root)
    except (MCPUnreachable, MCPCallFailed) as exc:
        # Exit 2, loudly, with nothing claimed as checked. Both are "could not check", and
        # the cause is named because the two send a maintainer somewhere different: a refused
        # call is usually a rotated key, an unreachable endpoint usually is not. See the
        # module docstring on why neither may be reported as drift.
        cause = ("the platform refused the call (an expired or rotated OSO_API_KEY looks like "
                 "this)" if isinstance(exc, MCPCallFailed)
                 else "the platform could not be reached")
        print(f"[CANNOT CHECK] {cause}: {exc}", file=sys.stderr)
        print(f"0 of {len(contracts)} mirror contracts verified. This is not a pass, and it "
              "is not drift -- do not resync anything on the strength of it.", file=sys.stderr)
        return 2

    print(render_table(rows))
    drifted = [r for r in rows if r.drifted]
    metadata_only = [r for r in rows if r.metadata_only]
    print(f"\n{len(rows) - len(drifted)} of {len(rows)} mirror contracts match the platform's "
          f"deployed source ({len(metadata_only)} of them over a metadata-only revision), "
          f"{len(drifted)} drifted")
    for row in metadata_only:
        print(f"  - {row.table} [metadata-only]: {row.detail}")
    for row in drifted:
        print(f"  x {row.table} [{row.status}]: {row.detail}")

    if args.report:
        args.report.write_text(json.dumps(
            {"checked": len(rows), "drifted": len(drifted),
             "metadata_only": len(metadata_only),
             "rows": [asdict(r) for r in rows]}, indent=2) + "\n")

    if metadata_only and not drifted:
        print(
            "\nEvery contract mirrors the source the platform is running. The revisions marked "
            "metadata-only\nmoved without the code moving; record each one by setting "
            "mirror.code_unchanged_from to the\nrevision currently in the contract, then "
            "advancing verified_revision, mirror.revision,\nmirror.hash and mirror.synced_at. "
            'The runbook is "Metadata-only revisions" in\ndocs/operations/deploy-models.md.'
        )

    if drifted:
        print(
            "\nThe repo is mirroring a model the platform has moved past. Resync each one: "
            "fetch\nthe deployed code, replace the mirror file's body below its banner, and "
            "update the\ncontract's verified_revision, mirror.revision, mirror.hash, "
            "mirror.local_sha256 and\nmirror.synced_at. The runbook is "
            '"Mirror resync" in docs/operations/deploy-models.md.'
        )
        return 1
    print("[OK] every mirror contract mirrors the source the platform is running")
    return 0


if __name__ == "__main__":
    sys.exit(main())
