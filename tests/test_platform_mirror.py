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
import re
from pathlib import Path

import yaml

from build.vocabulary import is_iso_date

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
    """`synced_at` is per entry, and required.

    It was one global date until 2026-08-16, so refetching two models advanced the date on all
    twelve and implied the other ten had been checked that day. A provenance date that moves
    for a reason unrelated to the thing it dates is worse than no date at all.

    When #314 deploys the staged signal_packages models, their entries convert from
    `status: staged` to full provenance — model_id, revision, hash, local_sha256, synced_at —
    and this test starts covering them automatically.
    """
    problems = []
    for m in _manifest()["models"]:
        if m.get("status") == "staged":
            continue
        for field in ("model_id", "revision", "hash", "synced_at"):
            if not m.get(field):
                problems.append(f"{m['file']} -> {m.get('table')}: missing {field}")
        if m.get("synced_at") and not is_iso_date(str(m["synced_at"])):
            problems.append(f"{m['file']}: synced_at {m['synced_at']!r} is not an ISO date")
    assert not problems, "deployed mirror entries lack provenance:\n" + "\n".join(problems)


def test_no_file_is_listed_twice():
    """A duplicate entry means one file is claiming to be two deployed models.

    `packages_product_adoption.sql` was listed twice until 2026-08-16, against
    `signal_github.product_adoption` and `signal_huggingface.product_adoption` — two tables it
    does not implement and does not read. Refetching them from the platform showed three
    unrelated models: one bands stars, one bands Hub downloads, one bands package-registry
    downloads.

    The test above could not see it. It reduces both sides to a SET, so a file listed twice
    and a file listed once are the same value, and the manifest passed while asserting
    something false about the platform. That is this repo's recurring failure — a check
    grading on less than it reports — in the one file whose whole job is provenance.
    """
    files = [m["file"] for m in _manifest()["models"]]
    dupes = sorted({f for f in files if files.count(f) > 1})
    assert not dupes, (
        f"listed more than once in manifest.yaml: {dupes}. One file cannot be the deployed "
        f"source of two tables; fetch each model's own bytes."
    )


def test_no_table_is_claimed_twice():
    """The other direction. Two files claiming one table means at most one is the mirror."""
    tables = [m["table"] for m in _manifest()["models"]]
    dupes = sorted({t for t in tables if tables.count(t) > 1})
    assert not dupes, f"claimed by more than one manifest entry: {dupes}"


HEADER_LINES = 10
DECLARATION = re.compile(r"^-- (currentai\.[a-z_]+\.[a-z_0-9]+)\s*$", re.MULTILINE)


def _declared_table(path: Path) -> str | None:
    """The table a mirrored `.sql` declares in its HEADER, or None if it does not declare one.

    Scoped to the header on purpose. Searching the whole file was the first cut and it
    established less than it claimed, on two files in this very folder:

      * `packages_package_downloads.sql` writes `-- currentai.signal_packages.product_adoption`
        at the start of a line 27 lines in, describing its own consumer. A whole-file search
        would therefore accept a manifest entry filing it under that table — the two
        `packages_*` entries could be swapped and the test would stay green.
      * `scores_openness_facts.sql` opens a line with `-- currentai.registry.category_dimensions`,
        one of its INPUTS.

    A mention is not a declaration, and only the header is a declaration.

    Exactly one declaration is required. Zero means the file cannot be checked; more than one
    means the header does not identify a single table, and picking the first would be guessing.
    """
    header = "\n".join(path.read_text().split("\n")[:HEADER_LINES])
    found = DECLARATION.findall(header)
    return found[0] if len(found) == 1 else None


def test_a_mirrored_sql_model_declares_the_table_it_is_listed_against():
    """Every mirrored `.sql` names its own table on its own line in the header, so the manifest
    is checked against the BYTES rather than against itself.

    This is what makes the duplicate detectable from inside the repo with no platform
    credentials: `packages_product_adoption.sql` declares
    `currentai.signal_packages.product_adoption` on its sixth line, and did so the whole time
    it was listed against two other tables.

    Only `.sql` is covered, and that is a real limit rather than an oversight: the `.py`
    mirrors carry a prose docstring naming their INPUT tables and never declare their output,
    so there is nothing here to compare. Extending this to them means giving them a header
    convention first.
    """
    problems = []
    for m in _manifest()["models"]:
        if not m["file"].endswith(".sql"):
            continue
        declared = _declared_table(MIRROR / m["file"])
        if declared is None:
            problems.append(
                f"{m['file']}: no single `-- currentai.<dataset>.<table>` line in its first "
                f"{HEADER_LINES} lines, so the manifest cannot be checked against it"
            )
        elif declared != m["table"]:
            problems.append(f"{m['file']} declares {declared}, manifest says {m['table']}")
    assert not problems, (
        "a mirrored model disagrees with the manifest about which table it builds:\n"
        + "\n".join(problems)
    )


def test_the_staged_package_models_are_all_present():
    """signal_packages has three models and they deploy as one dataset.

    Mirroring two of the three is how the third's absence went unnoticed while a file
    belonging to it was listed under two other datasets. Named explicitly rather than
    counted, so adding a fourth model does not silently satisfy this.
    """
    staged = {m["table"] for m in _manifest()["models"] if m.get("status") == "staged"}
    expected = {
        "currentai.signal_packages.package_downloads",
        "currentai.signal_packages.package_downloads_daily",
        "currentai.signal_packages.product_adoption",
    }
    assert expected <= staged, f"staged signal_packages models missing: {sorted(expected - staged)}"
