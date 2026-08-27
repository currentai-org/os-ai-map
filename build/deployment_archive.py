"""The durable, content-addressed record of what each maintainer publisher deployed — the rollback record.

A static-model publication REPLACES the table in place; the platform keeps no prior-revision list, so
the only way to roll a table back is to re-upload the exact bytes of a previous deployment. This
module is that record, shared by `build/publish_evaluation.py` and `build/publish_scoring_trace.py`
so the two cannot drift.

Three integrity properties it exists to guarantee:

- **Content addressing, not semantic identity.** A `deployment_id` (declaration + observation
  generation) is NOT a byte identity: the same generation can serialize to different bytes — e.g. a
  regenerated `evaluated_at` — so it cannot decide whether two deployments are the same artifact. The
  artifact is addressed by **`artifact_id` = SHA-256 over the canonical `filename → file-sha256`
  manifest**, and stored under `artifacts/<artifact_id>/`. Every occurrence records BOTH ids, so a
  new byte-set under an unchanged generation is a distinct artifact and can never be mistaken for one
  already archived.

- **Explicit operations, never inferred.** Whether a publish is a `deploy` or a `rollback` is stated
  by the caller, not guessed from whether an archive directory exists. A normal publish is a
  `deploy`; a `rollback` names an already-archived `artifact_id`, verifies its hashes, and re-uploads
  it. Re-deploying the currently-live artifact is still a `deploy`. Occurrences carry
  `operation`, `deployment_id`, `artifact_id`, `previous_artifact_id`, and a timestamp.

- **Atomic artifact, occurrence last.** `ensure_artifact` writes through a staging directory and
  atomically renames it into place only after every file + receipt + `SHA256SUMS` is written, so an
  interrupted copy never leaves a directory that verification would accept. The artifact is persisted
  BEFORE the platform mutation; the occurrence is appended ONLY after the deployed state is verified.
  An unreferenced staged artifact after a failed deploy is harmless; an occurrence claiming the wrong
  live state is not.

The archive root is INDEPENDENT of where candidates are read (a publisher's `--dir`), so publishing
from archived bytes writes its occurrence to the fixed `--archive-root` and never nests. "Live" is
read from the occurrence log, never from directory modification times.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

ARTIFACTS_DIR = "artifacts"
OCCURRENCES = "occurrences.jsonl"
SHA256SUMS = "SHA256SUMS"
RECEIPT = "receipt.json"
_STAGING_PREFIX = ".staging-"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- content addressing ----------------------------------------------------------


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(files: dict[str, Path]) -> dict[str, str]:
    """The `filename → sha256` map over the deployed files — the byte identity of a deployment."""
    return {name: file_sha256(path) for name, path in sorted(files.items())}


def _manifest_digest(m: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(m, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def artifact_id(files: dict[str, Path]) -> str:
    """SHA-256 over the canonical `filename → sha256` manifest.

    Two serializations that differ in any byte (a regenerated `evaluated_at`, a reordered row) get
    DIFFERENT artifact_ids even under the same `deployment_id`, so a new byte-set is never mistaken
    for one already archived.
    """
    return _manifest_digest(manifest(files))


def artifacts_root(archive_root: Path) -> Path:
    return archive_root / ARTIFACTS_DIR


def artifact_dir(archive_root: Path, aid: str) -> Path:
    return artifacts_root(archive_root) / aid


def _sha256sums_text(m: dict[str, str]) -> str:
    # `sha256␠␠name`, sorted — the familiar coreutils SHA256SUMS shape.
    return "".join(f"{sha}  {name}\n" for name, sha in sorted(m.items()))


def read_manifest(adir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (adir / SHA256SUMS).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        sha, name = line.split("  ", 1)
        out[name] = sha
    return out


def verify_artifact(archive_root: Path, aid: str) -> None:
    """Raise unless the archived artifact is complete and every byte matches its recorded hash.

    Confirms the directory exists, `SHA256SUMS` is present, the manifest hashes back to `aid` (the
    directory name is its own content address), and each listed file's live sha256 equals the record.
    Used to gate a rollback (`rollback with altered bytes must be rejected`) and to make
    `ensure_artifact` idempotent.
    """
    adir = artifact_dir(archive_root, aid)
    if not adir.is_dir():
        raise RuntimeError(f"artifact {aid} is not archived at {adir}")
    if not (adir / SHA256SUMS).exists():
        raise RuntimeError(f"artifact {aid} has no {SHA256SUMS} — not a complete archive")
    recorded = read_manifest(adir)
    if _manifest_digest(recorded) != aid:
        raise RuntimeError(f"artifact {aid}: {SHA256SUMS} does not hash to the artifact id")
    for name, sha in recorded.items():
        f = adir / name
        if not f.exists():
            raise RuntimeError(f"artifact {aid} is missing file {name}")
        actual = file_sha256(f)
        if actual != sha:
            raise RuntimeError(f"artifact {aid} file {name} hash mismatch: {actual} != recorded {sha}")


def ensure_artifact(archive_root: Path, files: dict[str, Path], receipt: dict, deployment_id: str) -> str:
    """Content-address and persist the artifact bytes atomically; return its `artifact_id`.

    Idempotent: an artifact already present is verified and left exactly as it is. A fresh artifact is
    written through a staging directory (`artifacts/.staging-<id>/`) and renamed into place with a
    single atomic `os.replace` only after every CSV, the receipt, and `SHA256SUMS` are written — so an
    interrupted write leaves at most an ignored staging directory, never a directory that
    `verify_artifact` would accept. Persist this BEFORE mutating the platform; record the occurrence
    only after the deployed state verifies.
    """
    aid = artifact_id(files)
    target = artifact_dir(archive_root, aid)
    if target.exists():
        verify_artifact(archive_root, aid)
        return aid
    artifacts_root(archive_root).mkdir(parents=True, exist_ok=True)
    staging = artifacts_root(archive_root) / f"{_STAGING_PREFIX}{aid}"
    if staging.exists():
        shutil.rmtree(staging)  # discard a prior interrupted attempt and redo cleanly
    staging.mkdir()
    for name, path in files.items():
        shutil.copy2(path, staging / name)
    (staging / RECEIPT).write_text(
        json.dumps(
            {"deployment_id": deployment_id, "artifact_id": aid, "tables": receipt},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (staging / SHA256SUMS).write_text(_sha256sums_text(manifest(files)), encoding="utf-8")
    os.replace(staging, target)  # atomic rename within artifacts/ — the archive appears all-at-once
    return aid


def artifact_files(archive_root: Path, aid: str) -> dict[str, Path]:
    """The archived data files (everything the manifest lists) — what a rollback re-uploads."""
    adir = artifact_dir(archive_root, aid)
    return {name: adir / name for name in read_manifest(adir)}


def artifact_receipt(archive_root: Path, aid: str) -> dict:
    return json.loads((artifact_dir(archive_root, aid) / RECEIPT).read_text(encoding="utf-8"))


# --- the append-only occurrence log ----------------------------------------------


def occurrences(archive_root: Path) -> list[dict]:
    """Every recorded deploy/rollback, oldest first. Empty (and no directory created) if none yet."""
    log = archive_root / OCCURRENCES
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def current_live(archive_root: Path) -> dict | None:
    """The last recorded occurrence — what is live now — or None. From the log, never from mtimes."""
    log = occurrences(archive_root)
    return log[-1] if log else None


def current_live_artifact_id(archive_root: Path) -> str | None:
    live = current_live(archive_root)
    return live["artifact_id"] if live else None


def record_occurrence(
    archive_root: Path,
    operation: str,
    deployment_id: str,
    artifact_id: str,
    previous_artifact_id: str | None,
    at: str | None = None,
) -> None:
    """Append one occurrence. `operation` is the caller's explicit choice, never inferred."""
    if operation not in ("deploy", "rollback"):
        raise ValueError(f"operation must be 'deploy' or 'rollback', got {operation!r}")
    archive_root.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "operation": operation,
            "deployment_id": deployment_id,
            "artifact_id": artifact_id,
            "previous_artifact_id": previous_artifact_id,
            "at": at or _now(),
        },
        sort_keys=True,
    )
    with (archive_root / OCCURRENCES).open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
