"""Durable persistence of a deployment artifact to a GitHub Release — the rollback bytes' home.

The local content-addressed archive (`build/deployment_archive.py`) lives under `build/evaluation/`,
which is git-ignored and per-session ephemeral. Rollback-by-bytes needs those bytes to survive the
container, so a deployment's artifact is also persisted as a **GitHub Release**: durable, public,
commit-related, with a recorded `SHA256SUMS` — no new object-storage system, only a `contents: write`
token.

STANDALONE, around the OSO publishers (they stay OSO-only). The executable sequence is
**stage → Release → publish → record**:

1. `publish_* --stage-artifact` persists the content-addressed artifact locally, network-free, and
   prints its `artifact_id` (so the bytes exist BEFORE any platform mutation);
2. `release_persistence persist` pushes that artifact to a Release;
3. `publish_*` deploys to OSO and verifies;
4. `release_persistence record-occurrence` writes the durable append-only occurrence file for the
   reconciliation PR to commit.

`restore` recovers an artifact from its Release into the archive root (for rollback in a fresh
container), verifying identity and running #387's provenance gate.

Each artifact becomes one Release: assets are a `csv-bundle.tar.gz` of its CSVs plus `receipt.json`
and `SHA256SUMS`; tag `artifact/<publisher>/<artifact_id>` names the publisher and the FULL content
id. Packaging runs the #387 provenance gate first (publisher-exact filename set, receipt
reconstructed from the verified bytes). Creation is **failure-atomic**: an unpublished draft is
filled and verified, then published — so a partial upload never strands a completed tag, and a retry
replaces the incomplete draft without touching a completed Release.

Environment (for a real persist/restore; not for --dry-run):
    GITHUB_TOKEN / GH_TOKEN   a token with `contents: write` on the repo
    GITHUB_REPOSITORY         owner/repo, defaults to "currentai-org/os-ai-map"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from build import deployment_archive as DA

ROOT = Path(__file__).resolve().parents[1]
PUBLISHERS = ("evaluation", "scoring-trace")
CSV_BUNDLE = "csv-bundle.tar.gz"
RELEASE_ASSETS = (CSV_BUNDLE, DA.RECEIPT, DA.SHA256SUMS)
REPO_OCCURRENCES = Path("warehouse") / "deployments" / "occurrences"
API = "https://api.github.com"
USER_AGENT = "os-ai-map-release-persistence/1.0"


def release_tag(publisher: str, artifact_id: str) -> str:
    """`artifact/<publisher>/<artifact_id>` — the publisher and the full content id, one per artifact."""
    if publisher not in PUBLISHERS:
        raise ValueError(f"publisher must be one of {PUBLISHERS}, got {publisher!r}")
    return f"artifact/{publisher}/{artifact_id}"


def _adapter(publisher: str):
    """(expected_csv_names, build_receipt, deployment_id) for a publisher — the #387 gate's inputs.

    Lazily imported so this module does not import the publishers at import time (and the publishers
    never import this one).
    """
    if publisher == "evaluation":
        from build import publish_evaluation as pub
        return ({f"{t}.csv" for t in pub.EVAL_TABLES}, pub.build_receipt, pub.deployment_id)
    if publisher == "scoring-trace":
        from build import publish_scoring_trace as pub
        return ({f"{t}.csv" for t in pub.TRACE_TABLES}, pub.build_receipt, pub.deployment_id)
    raise ValueError(f"publisher must be one of {PUBLISHERS}, got {publisher!r}")


def _gate(archive_root: Path, artifact_id: str, publisher: str) -> tuple[dict, str]:
    """Run #387's provenance gate for `publisher`: verified bytes, exact filename set, receipt and
    deployment_id reconstructed from the bytes. Returns (tables, deployment_id)."""
    expected_names, build_receipt, deployment_id = _adapter(publisher)
    return DA.verified_rollback_provenance(archive_root, artifact_id, expected_names, build_receipt, deployment_id)


def package_assets(archive_root: Path, artifact_id: str, publisher: str, work_dir: Path) -> dict[str, Path]:
    """The Release assets for an artifact, after the provenance gate passes.

    Gated by `_gate` — an evaluation Release therefore carries exactly its two CSVs and scoring-trace
    exactly its three, with a receipt that agrees with the bytes. The CSVs are bundled into one
    `csv-bundle.tar.gz`; `receipt.json` / `SHA256SUMS` come verbatim from the archive.
    """
    _gate(archive_root, artifact_id, publisher)
    adir = DA.artifact_dir(archive_root, artifact_id)
    csvs = sorted(DA.read_manifest(adir))
    work_dir.mkdir(parents=True, exist_ok=True)
    bundle = work_dir / CSV_BUNDLE
    with tarfile.open(bundle, "w:gz") as tar:
        for name in csvs:
            tar.add(adir / name, arcname=name)
    return {CSV_BUNDLE: bundle, DA.RECEIPT: adir / DA.RECEIPT, DA.SHA256SUMS: adir / DA.SHA256SUMS}


def _content_type(name: str) -> str:
    if name.endswith(".tar.gz"):
        return "application/gzip"
    if name.endswith(".json"):
        return "application/json"
    return "text/plain"


class GitHubReleases:
    """The real GitHub Releases client (urllib). Tests inject a fake with the same surface."""

    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo

    def _request(self, method, url, *, data=None, content_type=None, accept="application/vnd.github+json"):
        headers = {"Authorization": f"Bearer {self.token}", "Accept": accept,
                   "User-Agent": USER_AGENT, "X-GitHub-Api-Version": "2022-11-28"}
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(request, timeout=180) as response:
            body = response.read()
            if accept == "application/octet-stream":
                return response.status, body
            return response.status, (json.loads(body) if body else None)

    def published_release(self, tag):
        try:
            _s, data = self._request("GET", f"{API}/repos/{self.repo}/releases/tags/{tag}")
            return data if not data.get("draft") else None
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise

    def draft_release(self, tag):
        _s, rels = self._request("GET", f"{API}/repos/{self.repo}/releases?per_page=100")
        for rel in rels or []:
            if rel.get("draft") and rel.get("name") == tag:
                return rel
        return None

    def delete_release(self, release_id):
        self._request("DELETE", f"{API}/repos/{self.repo}/releases/{release_id}")

    def create_draft(self, tag, name, body, target_commitish=None):
        payload = {"tag_name": tag, "name": name, "body": body, "draft": True}
        if target_commitish:
            payload["target_commitish"] = target_commitish
        _s, data = self._request("POST", f"{API}/repos/{self.repo}/releases",
                                 data=json.dumps(payload).encode(), content_type="application/json")
        return {"id": data["id"], "upload_url": data["upload_url"].split("{", 1)[0]}

    def list_assets(self, release_id):
        _s, data = self._request("GET", f"{API}/repos/{self.repo}/releases/{release_id}/assets?per_page=100")
        return [{"id": a["id"], "name": a["name"], "size": a["size"]} for a in (data or [])]

    def upload_asset(self, upload_url, name, path, content_type):
        self._request("POST", f"{upload_url}?name={name}",
                      data=Path(path).read_bytes(), content_type=content_type)

    def publish_release(self, release_id):
        self._request("PATCH", f"{API}/repos/{self.repo}/releases/{release_id}",
                      data=json.dumps({"draft": False}).encode(), content_type="application/json")

    def download_asset(self, asset_id, dest):
        _s, body = self._request("GET", f"{API}/repos/{self.repo}/releases/assets/{asset_id}",
                                 accept="application/octet-stream")
        Path(dest).write_bytes(body)


def persist_artifact(archive_root, artifact_id, publisher, client, *,
                     target_commitish=None, dry_run=False, work_dir=None) -> dict:
    """Persist one artifact as a GitHub Release, failure-atomically. Returns a summary.

    --dry-run runs the provenance gate + packaging and reports the plan, no GitHub call. A real
    persist refuses if a COMPLETED (published) release for the tag exists; otherwise it discards any
    incomplete draft, creates a fresh draft, uploads all assets, verifies the remote asset set and
    sizes, and only then publishes — so a partial upload never strands a completed tag, and a retry
    replaces the incomplete draft rather than a finished Release.
    """
    tag = release_tag(publisher, artifact_id)
    with tempfile.TemporaryDirectory() as tmp:
        assets = package_assets(archive_root, artifact_id, publisher, Path(work_dir) if work_dir else Path(tmp))
        summary = {"tag": tag, "publisher": publisher, "artifact_id": artifact_id,
                   "assets": sorted(assets), "created": False}
        if dry_run:
            return summary
        if client.published_release(tag) is not None:
            raise RuntimeError(f"refusing to persist: a completed release for {tag} already exists")
        incomplete = client.draft_release(tag)
        if incomplete is not None:
            client.delete_release(incomplete["id"])  # retry: discard the incomplete draft, never a finished release
        draft = client.create_draft(tag, name=tag, target_commitish=target_commitish,
                                    body=f"Deployment artifact {artifact_id} for the {publisher} publisher.\n\n"
                                         f"Content-addressed rollback bytes; hashes in SHA256SUMS.")
        for name, path in assets.items():
            client.upload_asset(draft["upload_url"], name, path, _content_type(name))
        remote = {a["name"]: a["size"] for a in client.list_assets(draft["id"])}
        expected = {name: Path(path).stat().st_size for name, path in assets.items()}
        if remote != expected:
            raise RuntimeError(f"draft asset set/sizes {remote} do not match expected {expected}; not publishing")
        client.publish_release(draft["id"])
        summary["created"] = True
        return summary


# --- restore: recover an artifact from its Release into the archive root --------------------------


def _safe_extract(bundle: Path, dest: Path) -> list[str]:
    """Extract a CSV bundle safely: regular files only, no absolute paths, no `..`, no links, no
    escape from `dest`. Returns the extracted member names."""
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()
    names: list[str] = []
    with tarfile.open(bundle, "r:gz") as tar:
        members = tar.getmembers()
        for m in members:
            if not m.isreg():
                raise RuntimeError(f"unsafe tar member (not a regular file, e.g. a link/dir/device): {m.name!r}")
            parts = Path(m.name).parts
            if m.name.startswith("/") or ".." in parts or Path(m.name).is_absolute() or len(parts) != 1:
                raise RuntimeError(f"unsafe tar member path: {m.name!r}")
            if not str((dest / m.name).resolve()).startswith(str(dest_resolved) + os.sep):
                raise RuntimeError(f"tar member escapes the destination: {m.name!r}")
            names.append(m.name)
        for m in members:
            tar.extract(m, dest, filter="data")  # belt-and-suspenders atop the checks above
    return names


def restore_artifact(archive_root, artifact_id, publisher, client, *, work_dir=None) -> str:
    """Download a persisted Release and rebuild `artifacts/<artifact_id>/` locally, or raise.

    Requires a COMPLETED release for `artifact/<publisher>/<artifact_id>` carrying exactly the three
    expected assets. The tarball is extracted safely (regular files only; no absolute paths, `..`, or
    links), the artifact is rebuilt through the atomic `ensure_artifact`, its recomputed `artifact_id`
    is required to equal the requested id, and #387's provenance gate is run. Returns the artifact_id.
    """
    tag = release_tag(publisher, artifact_id)
    rel = client.published_release(tag)
    if rel is None:
        raise RuntimeError(f"no completed release for {tag} to restore from")
    assets = {a["name"]: a for a in client.list_assets(rel["id"])}
    if set(assets) != set(RELEASE_ASSETS):
        raise RuntimeError(f"release {tag} assets {sorted(assets)} != expected {sorted(RELEASE_ASSETS)}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for name in RELEASE_ASSETS:
            client.download_asset(assets[name]["id"], tmp / name)
        extract_dir = tmp / "extracted"
        extracted = _safe_extract(tmp / CSV_BUNDLE, extract_dir)
        receipt = json.loads((tmp / DA.RECEIPT).read_text(encoding="utf-8"))
        if receipt.get("artifact_id") != artifact_id:
            raise RuntimeError(f"downloaded receipt artifact_id {receipt.get('artifact_id')!r} != requested {artifact_id}")
        files = {name: extract_dir / name for name in extracted}
        rebuilt = DA.ensure_artifact(archive_root, files, receipt["tables"], receipt["deployment_id"])
        if rebuilt != artifact_id:
            raise RuntimeError(f"restored bytes content-address to {rebuilt}, not the requested {artifact_id}")
    _gate(archive_root, artifact_id, publisher)  # publisher-exact filename set + receipt agrees with bytes
    return artifact_id


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


def record_local_occurrence(archive_root: Path, repo_root: Path, publisher: str) -> Path:
    """Read the publisher's latest VERIFIED local occurrence (the tail of the archive's occurrence
    log, written only after deployed-state verification) and persist it as the durable repo file."""
    occurrence = DA.current_live(archive_root)
    if occurrence is None:
        raise RuntimeError(f"no occurrence recorded in {archive_root} — nothing to persist")
    return write_repo_occurrence(repo_root, publisher, occurrence)


def _client_from_env():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN (or GH_TOKEN) with contents:write must be set (use --dry-run where available)",
              file=sys.stderr)
        return None
    return GitHubReleases(token, os.environ.get("GITHUB_REPOSITORY", "currentai-org/os-ai-map"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("persist", help="package + push an artifact to a GitHub Release (draft->verify->publish)")
    p.add_argument("--publisher", required=True, choices=PUBLISHERS)
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--artifact-id", required=True)
    p.add_argument("--target-commitish", default=None)
    p.add_argument("--dry-run", action="store_true", help="gate + package + plan; no GitHub call")

    r = sub.add_parser("restore", help="download a Release and rebuild the artifact locally")
    r.add_argument("--publisher", required=True, choices=PUBLISHERS)
    r.add_argument("--archive-root", type=Path, required=True)
    r.add_argument("--artifact-id", required=True)

    o = sub.add_parser("record-occurrence", help="write the latest local occurrence as the durable repo file")
    o.add_argument("--publisher", required=True, choices=PUBLISHERS)
    o.add_argument("--archive-root", type=Path, required=True)
    o.add_argument("--repo-root", type=Path, default=ROOT)

    args = parser.parse_args()

    if args.command == "persist" and args.dry_run:
        summary = persist_artifact(args.archive_root, args.artifact_id, args.publisher, client=None, dry_run=True)
        print(f"would create release {summary['tag']} with assets {summary['assets']} (no GitHub call)")
        return 0
    if args.command == "record-occurrence":
        try:
            path = record_local_occurrence(args.archive_root, args.repo_root, args.publisher)
        except RuntimeError as exc:
            print(f"record-occurrence failed: {exc}", file=sys.stderr)
            return 2
        print(f"wrote durable occurrence {path}")
        return 0

    client = _client_from_env()
    if client is None:
        return 2
    try:
        if args.command == "persist":
            summary = persist_artifact(args.archive_root, args.artifact_id, args.publisher,
                                       client=client, target_commitish=args.target_commitish)
            print(f"created release {summary['tag']} with assets {summary['assets']}")
        else:  # restore
            restore_artifact(args.archive_root, args.artifact_id, args.publisher, client=client)
            print(f"restored artifact {args.artifact_id} into {args.archive_root}")
    except RuntimeError as exc:
        print(f"{args.command} failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
