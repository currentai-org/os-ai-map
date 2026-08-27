"""The durable, append-only record of what each maintainer publisher deployed — the rollback record.

A static-model publication REPLACES the table in place; the platform keeps no prior-revision list,
so the only way to roll a table back is to re-upload the exact bytes of a previous deployment. This
module is that record, shared by `build/publish_evaluation.py` and `build/publish_scoring_trace.py`
so the two cannot drift.

Two ideas are kept deliberately separate — the conflation of them was the bug this module fixes:

- **Artifact identity.** An immutable per-deployment directory named by the `deployment_id` (the
  declaration/observation identities the bytes carry). Written **once** and never overwritten — the
  same identity always names the same bytes.
- **Deployment occurrence.** An append-only log (`occurrences.jsonl`) of what happened — one line per
  successful `deploy` or `rollback`, each naming a `deployment_id`. The CURRENT live state is the
  last occurrence's `deployment_id`; a rollback re-points it at an earlier identity by appending an
  occurrence, **without** touching the immutable directory. Occurrences — not directory modification
  times — decide what is live, so "latest" cannot be spoofed by a filesystem touch, and restoring an
  older archive is a first-class recorded event rather than an out-of-band copy.

The archive root is INDEPENDENT of where candidates are read (a publisher's `--dir`). Publishing from
archived bytes (`--dir <an-archive>`) still writes its occurrence to the fixed `--archive-root`, so an
archive is never nested inside another and the canonical root's notion of "live" is always updated.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

OCCURRENCES = "occurrences.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def archive_path(archive_root: Path, deployment_id: str) -> Path:
    """The immutable directory that holds (or will hold) the bytes for this deployment identity."""
    return archive_root / deployment_id


def occurrences(archive_root: Path) -> list[dict]:
    """Every recorded deploy/rollback, oldest first. Empty (and no directory created) if none yet."""
    log = archive_root / OCCURRENCES
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def current_live(archive_root: Path) -> str | None:
    """The `deployment_id` of the last recorded occurrence — what is live now — or None if none."""
    log = occurrences(archive_root)
    return log[-1]["deployment_id"] if log else None


def current_live_archive(archive_root: Path) -> Path | None:
    """The archive directory of the currently-live deployment, or None. Derived from the occurrence
    log, never from directory mtimes."""
    live = current_live(archive_root)
    return archive_path(archive_root, live) if live is not None else None


def record_occurrence(archive_root: Path, kind: str, deployment_id: str, at: str | None = None) -> None:
    """Append one occurrence line. Creates the archive root on first write; never truncates."""
    if kind not in ("deploy", "rollback"):
        raise ValueError(f"occurrence kind must be 'deploy' or 'rollback', got {kind!r}")
    archive_root.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"kind": kind, "deployment_id": deployment_id, "at": at or _now()}, sort_keys=True)
    with (archive_root / OCCURRENCES).open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def store(
    archive_root: Path,
    deployment_id: str,
    files: dict[str, Path],
    receipt: dict,
    at: str | None = None,
) -> tuple[Path, str]:
    """Archive a deployment's bytes and record it as an occurrence. Returns (archive_dir, kind).

    A FRESH identity (`archive_path` does not yet exist) is a **deploy**: the immutable directory is
    created and the CSVs + a completed receipt are copied in. An identity that is ALREADY archived is
    a **rollback** — the very case of re-uploading a previous deployment's bytes — so the directory is
    left untouched (it already holds exactly these bytes) and only a rollback occurrence is appended.
    Either way the occurrence log is what advances "live", so publishing from an old archive updates
    the canonical root rather than nesting a new archive inside the bytes being restored.
    """
    target = archive_path(archive_root, deployment_id)
    kind = "rollback" if target.exists() else "deploy"
    if kind == "deploy":
        target.mkdir(parents=True)
        for name, path in files.items():
            shutil.copy2(path, target / name)
        (target / "receipt.json").write_text(
            json.dumps({"deployment_id": deployment_id, "tables": receipt}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    record_occurrence(archive_root, kind, deployment_id, at)
    return target, kind
