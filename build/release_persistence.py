"""Durable persistence of a deployment artifact to a GitHub Release — the rollback bytes' home.

The local content-addressed archive (`build/deployment_archive.py`) lives under `build/evaluation/`,
which is git-ignored and per-session ephemeral. Rollback-by-bytes needs those bytes to survive the
container, so a deployment's artifact is also persisted as a **GitHub Release**: durable, public,
commit-related, with a recorded `SHA256SUMS` — no new object-storage system or credentials beyond a
token with `contents: write`.

This is a STANDALONE step, deliberately not wired into the OSO publishers: the deploy runbook
persists the artifact to a Release *before* running the publisher (so the recoverable bytes exist
before any platform mutation), and appends the committed occurrence file *after* the publisher
verifies the deployed state. The publishers stay OSO-only.

Each artifact becomes one Release:

- **tag** = `artifact/<publisher>/<artifact_id>` — names the publisher and the FULL content id;
- **assets** = a `csv-bundle.tar.gz` of the artifact's CSVs, plus `receipt.json` and `SHA256SUMS`
  verbatim from the archive;
- creation **refuses to replace** an existing tag or asset — an artifact is written once.

Occurrences are recorded durably as small, append-only JSON files committed to the repository
(`warehouse/deployments/occurrences/<publisher>/`) in the reconciliation PR — so the live-state
transitions are auditable in git history, independent of the ephemeral runtime log.

Environment (for a real persist; not needed for --dry-run):
    GITHUB_TOKEN / GH_TOKEN   a token with `contents: write` on the repo
    GITHUB_REPOSITORY         owner/repo, defaults to "currentai-org/os-ai-map"

Usage:
    uv run python -m build.release_persistence --publisher scoring-trace \\
        --archive-root build/evaluation/scoring-trace-deployments --artifact-id <id> --dry-run
    uv run python -m build.release_persistence --publisher evaluation \\
        --archive-root build/evaluation/deployments --artifact-id <id>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

from build.deployment_archive import (
    RECEIPT,
    SHA256SUMS,
    artifact_dir,
    read_manifest,
    verify_artifact,
)

ROOT = Path(__file__).resolve().parents[1]
PUBLISHERS = ("evaluation", "scoring-trace")
CSV_BUNDLE = "csv-bundle.tar.gz"
REPO_OCCURRENCES = Path("warehouse") / "deployments" / "occurrences"
API = "https://api.github.com"
USER_AGENT = "os-ai-map-release-persistence/1.0"


def release_tag(publisher: str, artifact_id: str) -> str:
    """`artifact/<publisher>/<artifact_id>` — the publisher and the full content id, one per artifact."""
    if publisher not in PUBLISHERS:
        raise ValueError(f"publisher must be one of {PUBLISHERS}, got {publisher!r}")
    return f"artifact/{publisher}/{artifact_id}"


def package_assets(archive_root: Path, artifact_id: str, work_dir: Path) -> dict[str, Path]:
    """The Release assets for an artifact: a tarball of its CSVs, plus receipt.json and SHA256SUMS.

    The artifact is verified first, so a persisted Release always carries bytes that match their
    recorded hashes. The CSVs are the manifest's files; `receipt.json` / `SHA256SUMS` are taken
    verbatim from the archive (they are provenance, not part of the content-addressed manifest).
    """
    verify_artifact(archive_root, artifact_id)
    adir = artifact_dir(archive_root, artifact_id)
    csvs = sorted(read_manifest(adir))
    work_dir.mkdir(parents=True, exist_ok=True)
    bundle = work_dir / CSV_BUNDLE
    with tarfile.open(bundle, "w:gz") as tar:
        for name in csvs:
            tar.add(adir / name, arcname=name)
    return {CSV_BUNDLE: bundle, RECEIPT: adir / RECEIPT, SHA256SUMS: adir / SHA256SUMS}


class GitHubReleases:
    """The real GitHub Releases client (urllib). Tests inject a fake with the same surface."""

    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo

    def _request(self, method: str, url: str, *, data: bytes | None = None, content_type: str | None = None):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None

    def tag_exists(self, tag: str) -> bool:
        try:
            self._request("GET", f"{API}/repos/{self.repo}/git/refs/tags/{tag}")
            return True
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return False
            raise

    def create_release(self, tag: str, name: str, body: str, target_commitish: str | None) -> str:
        payload: dict = {"tag_name": tag, "name": name, "body": body}
        if target_commitish:
            payload["target_commitish"] = target_commitish
        _status, data = self._request(
            "POST", f"{API}/repos/{self.repo}/releases",
            data=json.dumps(payload).encode(), content_type="application/json",
        )
        return data["upload_url"].split("{", 1)[0]  # strip the {?name,label} template

    def upload_asset(self, upload_url: str, name: str, path: Path, content_type: str) -> None:
        self._request(
            "POST", f"{upload_url}?name={name}",
            data=Path(path).read_bytes(), content_type=content_type,
        )


def _content_type(name: str) -> str:
    if name.endswith(".tar.gz"):
        return "application/gzip"
    if name.endswith(".json"):
        return "application/json"
    return "text/plain"


def persist_artifact(archive_root: Path, artifact_id: str, publisher: str, client, *,
                     target_commitish: str | None = None, dry_run: bool = False,
                     work_dir: Path | None = None) -> dict:
    """Persist one artifact as a GitHub Release. Returns a summary; raises if the tag already exists.

    `--dry-run` verifies + packages and reports the plan but makes NO GitHub call. A real persist
    refuses to replace an existing tag (an artifact is written once), then creates the release and
    uploads the assets.
    """
    tag = release_tag(publisher, artifact_id)
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        assets = package_assets(archive_root, artifact_id, Path(work_dir) if work_dir else Path(tmp))
        summary = {"tag": tag, "publisher": publisher, "artifact_id": artifact_id,
                   "assets": sorted(assets), "created": False}
        if dry_run:
            return summary
        if client.tag_exists(tag):
            raise RuntimeError(f"refusing to persist: tag {tag} already exists — an artifact is written once")
        upload_url = client.create_release(
            tag, name=tag,
            body=f"Deployment artifact {artifact_id} for the {publisher} publisher.\n\n"
                 f"Content-addressed rollback bytes; hashes in SHA256SUMS.",
            target_commitish=target_commitish,
        )
        for name, path in assets.items():
            client.upload_asset(upload_url, name, path, _content_type(name))
        summary["created"] = True
        return summary


# --- durable occurrences: append-only files committed to the repo --------------------------------


def repo_occurrence_path(repo_root: Path, publisher: str, occurrence: dict) -> Path:
    safe_at = occurrence["at"].replace(":", "").replace("+", "Z")
    return repo_root / REPO_OCCURRENCES / publisher / f"{safe_at}-{occurrence['artifact_id'][:12]}.json"


def write_repo_occurrence(repo_root: Path, publisher: str, occurrence: dict) -> Path:
    """Write one durable occurrence file for the reconciliation PR to commit. Append-only: refuses to
    overwrite an existing file, so the git-tracked audit trail cannot be silently rewritten."""
    path = repo_occurrence_path(repo_root, publisher, occurrence)
    if path.exists():
        raise RuntimeError(f"append-only: occurrence file {path} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(occurrence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publisher", required=True, choices=PUBLISHERS)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--target-commitish", default=None, help="commit/branch to tag (defaults to the repo default branch)")
    parser.add_argument("--dry-run", action="store_true", help="verify + package + plan; no GitHub call")
    args = parser.parse_args()

    if args.dry_run:
        summary = persist_artifact(args.archive_root, args.artifact_id, args.publisher, client=None, dry_run=True)
        print(f"would create release {summary['tag']} with assets {summary['assets']} (no GitHub call)")
        return 0

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN (or GH_TOKEN) with contents:write must be set (use --dry-run otherwise)",
              file=sys.stderr)
        return 2
    repo = os.environ.get("GITHUB_REPOSITORY", "currentai-org/os-ai-map")
    try:
        summary = persist_artifact(
            args.archive_root, args.artifact_id, args.publisher,
            client=GitHubReleases(token, repo), target_commitish=args.target_commitish,
        )
    except RuntimeError as exc:
        print(f"persist failed: {exc}", file=sys.stderr)
        return 2
    print(f"created release {summary['tag']} on {repo} with assets {summary['assets']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
