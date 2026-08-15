"""Integrity of the read-only platform mirror in warehouse/platform-mirror/.

The mirror is a committed copy of the models that run on the OSO platform; manifest.yaml is
its provenance record. This test keeps the two honest without needing platform credentials:

- every mirrored artifact is represented in the manifest, and vice versa;
- the manifest's local_sha256 binds the actual checked-in bytes (so a silent edit to a mirror
  file, or a stale manifest, fails here);
- every deployed (non-staged) entry carries model_id + revision + platform hash provenance.

The credentialed drift check (manifest revision vs the live platform) is a separate follow-up;
this is the offline half.
"""

import hashlib
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
MIRROR = REPO / "warehouse" / "platform-mirror"
NON_ARTIFACTS = {"README.md", "manifest.yaml"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return yaml.safe_load((MIRROR / "manifest.yaml").read_text())


def test_every_mirror_file_is_in_the_manifest():
    on_disk = {p.name for p in MIRROR.iterdir() if p.is_file() and p.name not in NON_ARTIFACTS}
    listed = set()
    for m in _manifest()["models"]:
        listed.add(m["file"])
        if "schema_file" in m:
            listed.add(m["schema_file"])
    missing = on_disk - listed
    unknown = listed - on_disk
    assert not missing, f"mirror files absent from manifest.yaml: {sorted(missing)}"
    assert not unknown, f"manifest.yaml references files not on disk: {sorted(unknown)}"


def test_local_hashes_bind_the_checked_in_bytes():
    problems = []
    for m in _manifest()["models"]:
        f = MIRROR / m["file"]
        if m.get("local_sha256") != _sha256(f):
            problems.append(f"{m['file']}: local_sha256 does not match its bytes")
        if "schema_file" in m and m.get("schema_local_sha256") != _sha256(MIRROR / m["schema_file"]):
            problems.append(f"{m['schema_file']}: schema_local_sha256 does not match its bytes")
    assert not problems, "manifest hashes are stale:\n" + "\n".join(problems)


def test_deployed_entries_have_revision_provenance():
    problems = []
    for m in _manifest()["models"]:
        if m.get("status") == "staged":
            continue
        for field in ("model_id", "revision", "hash"):
            if not m.get(field):
                problems.append(f"{m['file']} -> {m.get('table')}: missing {field}")
    assert not problems, "deployed mirror entries lack provenance:\n" + "\n".join(problems)
