"""The weekly identity digest -- rendering, cap, parked policy, and the footer numbers.

`render()` is exercised entirely against fixture rows and a fixture resolution ledger, never
the warehouse, so this suite runs offline like every other test in this repo. The CLI's
warehouse plumbing (table-not-found vs any other error, `--allow-unprovisioned`) is exercised
by monkeypatching `build.identity_digest.load_rows_from_warehouse`.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from build import identity_digest as digest
from build import resolution

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "docs" / "schemas" / "resolution_ledger.schema.json").read_text())
SAMPLE = json.loads((ROOT / "tests" / "fixtures" / "identity_digest_sample.json").read_text())


def _row(relation, item_id, *, state="active", blast_radius=1, tiebreak=0, confidence=0.5,
         left=None, right=None, first_seen="2026-08-01", resurfaced_reason=None,
         method=("declared",)):
    return {
        "sweep_week": "2026-08-31",
        "relation": relation,
        "item_id": item_id,
        "candidate_key": f"pypi:{item_id}",
        "left": left or {"kind": "pypi", "id": item_id},
        "right": right or {"kind": "product", "id": "target"},
        "confidence": confidence,
        "method": list(method),
        "evidence": list(method),
        "penalties": [],
        "proposed_action": f"confirm_{relation}_edge",
        "blast_radius": blast_radius,
        "tiebreak": tiebreak,
        "options": ["confirm", "reject", "park"],
        "default_if_ignored": "no edge",
        "first_seen": first_seen,
        "last_evidence_change": first_seen,
        "state": state,
        "resurfaced_reason": resurfaced_reason,
    }


@pytest.fixture(autouse=True)
def empty_ledger(tmp_path, monkeypatch):
    """A deterministic, empty ledger by default -- `resolved this week` is 0 unless a test
    points `resolution.LEDGER` at its own fixture file."""
    empty = tmp_path / "empty_ledger.yaml"
    empty.write_text("version: 1\nresolutions: []\n")
    monkeypatch.setattr(resolution, "LEDGER", empty)
    yield


# -- section order and within-section ranking ------------------------------------------------


def test_sections_render_equivalence_first_then_membership_org_artifact_identity():
    rows = [
        _row("org", "o1"),
        _row("artifact_identity", "a1"),
        _row("membership", "m1"),
        _row("equivalence", "e1"),
    ]
    body = digest.render(rows, "2026-36")
    headers = [line for line in body.splitlines() if line.startswith("### ") and "(" in line]
    order = [h.split("(")[0].strip("# ").strip() for h in headers if "Scorecard" not in h]
    assert order == ["Equivalence", "Membership", "Org", "Artifact identity"]


def test_within_a_section_ranks_by_blast_radius_then_tiebreak_then_confidence():
    rows = [
        _row("membership", "low", blast_radius=1, tiebreak=0, confidence=0.1),
        _row("membership", "high-blast", blast_radius=3, tiebreak=0, confidence=0.5),
        _row("membership", "mid-tiebreak", blast_radius=1, tiebreak=100, confidence=0.5),
        _row("membership", "mid-confidence", blast_radius=1, tiebreak=0, confidence=0.6),
    ]
    body = digest.render(rows, "2026-36")
    positions = {row_id: body.index(f"`{row_id}`") for row_id in
                 ("high-blast", "mid-tiebreak", "mid-confidence", "low")}
    ordered = sorted(positions, key=positions.get)
    assert ordered == ["high-blast", "mid-tiebreak", "mid-confidence", "low"]


# -- cap and parked/pool policy ----------------------------------------------------------------


def test_cap_of_25_active_items_and_the_overflow_is_reported():
    rows = [_row("membership", f"item-{i}", blast_radius=1, tiebreak=100 - i) for i in range(30)]
    body = digest.render(rows, "2026-36")
    assert body.count("#### `item-") == 25
    assert "5 additional item(s)" in body


def test_parked_rows_never_render_as_items_only_as_a_count():
    rows = [
        _row("membership", "active-one", state="active"),
        _row("membership", "parked-one", state="parked"),
        _row("membership", "parked-two", state="parked"),
    ]
    body = digest.render(rows, "2026-36")
    assert "`parked-one`" not in body
    assert "`parked-two`" not in body
    assert "`active-one`" in body
    assert "Parked (weak evidence only, held back): 2" in body


def test_pool_rows_render_as_a_single_total_not_per_section():
    rows = [
        _row("membership", "m-pool", state="pool"),
        _row("org", "o-pool", state="pool"),
        _row("equivalence", "e-active", state="active"),
    ]
    body = digest.render(rows, "2026-36")
    assert "`m-pool`" not in body
    assert "`o-pool`" not in body
    assert "Overflow this week (ranked below the cap, not reviewed): 2" in body


def test_resurfaced_items_carry_their_reason():
    rows = [_row("org", "resurfaced-one", state="resurfaced", resurfaced_reason="age")]
    body = digest.render(rows, "2026-36")
    assert "Resurfaced reason: age" in body


# -- pre-filled ledger YAML validates -----------------------------------------------------------


def test_every_rendered_ledger_block_parses_and_validates(tmp_path):
    rows = [
        _row("membership", "m1", left={"kind": "pypi", "id": "m1"},
             right={"kind": "product", "id": "acme"}),
        _row("equivalence", "e1", left={"kind": "github", "id": "acme/e1"},
             right={"kind": "product", "id": "acme"}),
        _row("org", "o1", left={"kind": "github", "id": "acme/o1"},
             right={"kind": "org", "id": "acme-labs"}),
        _row("artifact_identity", "a1", left={"kind": "github", "id": "acme/a1"},
             right={"kind": "github", "id": "acme/a1-renamed"}),
    ]
    body = digest.render(rows, "2026-36")
    blocks = body.split("```yaml")[1:]
    assert len(blocks) == 4
    validated = 0
    for block in blocks:
        yaml_text = block.split("```")[0]
        entries = yaml.safe_load(yaml_text)
        assert isinstance(entries, list) and len(entries) == 1
        entry = entries[0]
        jsonschema.validate(entry, SCHEMA)
        assert entry["decided_on"] == "2026-08-31"  # the sweep Monday for week 2026-36
        assert len(entry["note"]) >= 20
        validated += 1
    assert validated == 4


def test_membership_ledger_entry_uses_product_membership_relation():
    rows = [_row("membership", "m1", right={"kind": "product", "id": "acme"})]
    body = digest.render(rows, "2026-36")
    entry = yaml.safe_load(body.split("```yaml")[1].split("```")[0])[0]
    assert entry["relation"] == "product_membership"
    assert entry["verdict"] == "member_of"
    assert entry["resolves_to"] == "acme"


def test_equivalence_ledger_entry_uses_product_equivalence_relation():
    rows = [_row("equivalence", "e1", right={"kind": "product", "id": "acme"})]
    body = digest.render(rows, "2026-36")
    entry = yaml.safe_load(body.split("```yaml")[1].split("```")[0])[0]
    assert entry["relation"] == "product_equivalence"
    assert entry["verdict"] == "existing_product"
    assert entry["resolves_to"] == "acme"


# -- footer numbers computed from the rows -------------------------------------------------------


def test_unresolved_pool_size_is_every_row():
    rows = [_row("membership", f"i{i}", state=s) for i, s in
            enumerate(["active", "parked", "pool", "resurfaced"])]
    body = digest.render(rows, "2026-36")
    assert "Unresolved pool size: 4" in body


def test_new_count_is_rows_first_seen_within_the_sweep_week():
    # Week 2026-36 spans Monday 2026-08-31 through Sunday 2026-09-06.
    rows = [
        _row("membership", "in-week", first_seen="2026-09-01"),
        _row("membership", "before-week", first_seen="2026-08-20"),
        _row("membership", "on-monday", first_seen="2026-08-31"),
    ]
    body = digest.render(rows, "2026-36")
    assert "2 new" in body


def test_resolved_count_reads_the_resolution_ledger(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.yaml"
    ledger_path.write_text(
        "version: 1\n"
        "resolutions:\n"
        "  - artifact: {kind: pypi, id: in-week-pkg}\n"
        "    verdict: unresolved\n"
        "    decided_in: '#1'\n"
        "    decided_on: '2026-09-02'\n"
        "    note: inside the sweep week, must be counted as resolved this week.\n"
        "  - artifact: {kind: pypi, id: out-of-week-pkg}\n"
        "    verdict: unresolved\n"
        "    decided_in: '#2'\n"
        "    decided_on: '2026-08-01'\n"
        "    note: outside the sweep week, must not be counted.\n"
    )
    monkeypatch.setattr(resolution, "LEDGER", ledger_path)
    body = digest.render([_row("membership", "m1")], "2026-36")
    assert "1 resolved" in body


def test_oldest_unresolved_age_in_weeks_from_first_seen():
    # Sweep Monday for 2026-36 is 2026-08-31; 8 weeks earlier is 2026-07-06.
    rows = [
        _row("membership", "old-one", first_seen="2026-07-06"),
        _row("membership", "new-one", first_seen="2026-08-25"),
    ]
    body = digest.render(rows, "2026-36")
    assert "Oldest unresolved age: 8 weeks" in body


# -- warehouse plumbing -------------------------------------------------------------------------


def test_missing_table_exits_2_without_allow_unprovisioned(monkeypatch, tmp_path):
    def _raise():
        raise digest.WarehouseTableMissing(digest.TABLE, RuntimeError("does not exist"))

    monkeypatch.setattr(digest, "load_rows_from_warehouse", _raise)
    out = tmp_path / "out.md"
    code = digest.main(["--week", "2026-36", "--out", str(out)])
    assert code == 2
    assert not out.exists()


def test_missing_table_exits_0_with_allow_unprovisioned(monkeypatch, tmp_path):
    def _raise():
        raise digest.WarehouseTableMissing(digest.TABLE, RuntimeError("does not exist"))

    monkeypatch.setattr(digest, "load_rows_from_warehouse", _raise)
    out = tmp_path / "out.md"
    code = digest.main(["--week", "2026-36", "--out", str(out), "--allow-unprovisioned"])
    assert code == 0
    assert not out.exists()


def test_other_warehouse_failure_always_exits_2_even_with_allow_unprovisioned(monkeypatch, tmp_path):
    def _raise():
        raise digest.WarehouseQueryFailed(digest.TABLE, RuntimeError("access denied"))

    monkeypatch.setattr(digest, "load_rows_from_warehouse", _raise)
    out = tmp_path / "out.md"
    code = digest.main(["--week", "2026-36", "--out", str(out), "--allow-unprovisioned"])
    assert code == 2
    assert not out.exists()


def test_rows_flag_reads_a_fixture_instead_of_the_warehouse(tmp_path):
    out = tmp_path / "out.md"
    code = digest.main([
        "--week", "2026-36", "--out", str(out),
        "--rows", str(ROOT / "tests" / "fixtures" / "identity_digest_sample.json"),
    ])
    assert code == 0
    assert out.exists()
    assert "identity digest: 2026-36" in out.read_text()


def test_sample_fixture_renders_without_error():
    body = digest.render(SAMPLE, "2026-36")
    assert body.startswith("# identity digest: 2026-36")
    assert "### Scorecard" in body
