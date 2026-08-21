"""Integrity of the read-only platform mirror, now recorded in warehouse/assets.yaml.

The mirror is a committed copy of the models that run on the OSO platform; its provenance
used to live in warehouse/platform-mirror/manifest.yaml, retired in the restructure that
mirrored the warehouse layout into the repository. The `mirror:` block on each
`authority: platform` asset carries the same record — model_id, revision, hash,
local_sha256, synced_at — and the byte, provenance and uniqueness checks that manifest.yaml
gated now live in tests/test_assets_inventory.py.

What is NOT covered there, and stays here, is the check that reads the BYTES: every mirrored
`.sql` names its own table on its own line in its header, so the inventory is checked against
the file rather than against itself. That is what made the duplicate detectable from inside
the repo with no platform credentials — `packages_product_adoption.sql` declared
`currentai.signal_packages.product_adoption` on its own line the whole time it was once listed
against two other tables.

The credentialed drift check (claimed revision vs the live platform) is a separate follow-up;
this is the offline half.
"""

import re
from pathlib import Path

from build import assets as A

REPO = A.ROOT
HEADER_LINES = 10
DECLARATION = re.compile(r"^-- (currentai\.[a-z_]+\.[a-z_0-9]+)\s*$", re.MULTILINE)


def _mirror_assets() -> list[dict]:
    """Assets that are a platform mirror or its staged successor.

    A platform mirror carries a `mirror:` block; the staged `signal_packages` models are
    the successor mirrored ahead of deployment (issue #314). Both are copies of models the
    platform owns, so both are held to the header contract below where they are `.sql`.
    """
    return [
        a for a in A.assets()
        if a.get("mirror") or a["id"].startswith("signal_packages.")
    ]


def _declared_table(path: Path) -> str | None:
    """The table a mirrored `.sql` declares in its HEADER, or None if it does not declare one.

    Scoped to the header on purpose. Searching the whole file was the first cut and it
    established less than it claimed, on two files:

      * `signal_packages/downloads.sql` writes a `-- currentai.signal_packages.product_adoption`
        line describing its own CONSUMER 27 lines in. A whole-file search would accept an
        entry filing it under that table.
      * `scores/openness_facts.sql` opens a line with `-- currentai.registry.category_dimensions`,
        one of its INPUTS.

    A mention is not a declaration, and only the header is a declaration. Exactly one
    declaration is required: zero means the file cannot be checked; more than one means the
    header does not identify a single table, and picking the first would be guessing.
    """
    header = "\n".join(path.read_text().split("\n")[:HEADER_LINES])
    found = DECLARATION.findall(header)
    return found[0] if len(found) == 1 else None


def test_a_mirrored_sql_model_declares_the_table_it_is_listed_against():
    """Every mirrored `.sql` names its own table on its own line in the header, so the
    inventory is checked against the BYTES rather than against itself.

    Only `.sql` is covered, and that is a real limit rather than an oversight: the `.py`
    mirrors carry a prose docstring naming their INPUT tables and never declare their output,
    so there is nothing here to compare. Extending this to them means giving them a header
    convention first.
    """
    problems = []
    for asset in _mirror_assets():
        model = (asset.get("files") or {}).get("model")
        if not model or not model.endswith(".sql"):
            continue
        declared = _declared_table(REPO / model)
        if declared is None:
            problems.append(
                f"{model}: no single `-- currentai.<dataset>.<table>` line in its first "
                f"{HEADER_LINES} lines, so the inventory cannot be checked against it"
            )
        elif declared != asset["table"]:
            problems.append(f"{model} declares {declared}, inventory says {asset['table']}")
    assert not problems, (
        "a mirrored model disagrees with the inventory about which table it builds:\n"
        + "\n".join(problems)
    )


def test_the_staged_package_models_are_all_present():
    """signal_packages has three models and they deploy as one dataset.

    Mirroring two of the three is how the third's absence went unnoticed while a file
    belonging to it was listed under two other datasets. Named explicitly rather than
    counted, so adding a fourth model does not silently satisfy this. The dataset names the
    source and the table must not repeat it (rule 11.1a.1), so `package_downloads` is
    `downloads` under the mirror layout.
    """
    staged = {a["table"] for a in A.assets() if a["status"] == "staged"}
    expected = {
        "currentai.signal_packages.downloads",
        "currentai.signal_packages.downloads_daily",
        "currentai.signal_packages.product_adoption",
    }
    assert expected <= staged, f"staged signal_packages models missing: {sorted(expected - staged)}"
