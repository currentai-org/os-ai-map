"""Every institution carries a `country`, or a ledger row that says why it does not.

`country` is optional on an organization on purpose (docs/reference/identity.md, "Country"):
unset means unrecorded, and an org whose seat no primary page states is left unset rather than
guessed. That makes the schema and `build/validate.py` unable to tell a deliberate gap from a
forgotten one, and between the 2026-09-30 batch and the 2026-10-12 batch nineteen new
companies, labs and foundations were created by sweeps that never set the field.

The ledgers already hold the deliberate gaps: a row with `country: null` or a low confidence is
the record of why the field stays unset (docs/sweeps/2026-09-30-identity-attributes/README.md).
So the check is that every org of an institutional type either has a country or appears in a
ledger. Individuals are unset by rule, and `unknown` is the honest type for an affiliation not
yet settled, so neither is held to it.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INSTITUTION_TYPES = {"company", "lab", "foundation", "government"}
LEDGER_GLOB = "docs/sweeps/*/countries/*.jsonl"


def ledger_slugs(root: Path = ROOT) -> set[str]:
    slugs: set[str] = set()
    for path in sorted(root.glob(LEDGER_GLOB)):
        for line in path.read_text().splitlines():
            if line.strip():
                slugs.add(json.loads(line)["slug"])
    return slugs


def unexplained_institutions(root: Path = ROOT) -> list[str]:
    explained = ledger_slugs(root)
    missing = []
    for path in sorted((root / "sources" / "organizations").glob("*.yaml")):
        org = yaml.safe_load(path.read_text()) or {}
        if org.get("type") in INSTITUTION_TYPES and not org.get("country"):
            if org["name"] not in explained:
                missing.append(org["name"])
    return missing


def test_every_institution_has_a_country_or_a_recorded_reason():
    missing = unexplained_institutions()
    assert not missing, (
        f"{len(missing)} institutional org(s) carry no `country` and no ledger row: {missing}. "
        "Set `country` from a page that states the seat (docs/reference/identity.md, 'Country'), "
        "or, where no primary page states one, add a row with `country: null` and the reason to a "
        f"ledger matching {LEDGER_GLOB} (format: docs/sweeps/2026-09-30-identity-attributes/README.md)."
    )


def test_the_check_catches_an_unexplained_institution(tmp_path):
    orgs = tmp_path / "sources" / "organizations"
    orgs.mkdir(parents=True)
    ledger = tmp_path / "docs" / "sweeps" / "batch" / "countries"
    ledger.mkdir(parents=True)
    (orgs / "seated.yaml").write_text("name: seated\ntype: company\ncountry: US\nproducts: []\n")
    (orgs / "explained.yaml").write_text("name: explained\ntype: lab\nproducts: []\n")
    (orgs / "forgotten.yaml").write_text("name: forgotten\ntype: foundation\nproducts: []\n")
    (orgs / "person.yaml").write_text("name: person\ntype: individual\nproducts: []\n")
    (orgs / "unsettled.yaml").write_text("name: unsettled\ntype: unknown\nproducts: []\n")
    (ledger / "batch-01.jsonl").write_text(
        json.dumps({"slug": "explained", "country": None, "basis": "no seat stated", "confidence": "low"})
        + "\n"
    )
    assert unexplained_institutions(tmp_path) == ["forgotten"]
