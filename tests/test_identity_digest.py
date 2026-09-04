"""The weekly identity digest -- rendering, cap, parked policy, per-relation blocks, and the
footer numbers.

`render()` is exercised entirely against fixture rows (and, for the ledger-reading fallback,
a fixture resolution ledger), never the warehouse, so this suite runs offline like every
other test in this repo. The CLI's warehouse plumbing (table-not-found vs any other error,
`--allow-unprovisioned`) is exercised by monkeypatching `build.identity_digest.load_rows_from_warehouse`.
`currentai.identity.digest` is deployed and contracted, so `--allow-unprovisioned` is refused
against the committed tree; the tests that need the query path stand in an empty manifest.
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
LEDGER_SCHEMA = json.loads((ROOT / "docs" / "schemas" / "resolution_ledger.schema.json").read_text())
SAMPLE = json.loads((ROOT / "tests" / "fixtures" / "identity_digest_sample.json").read_text())

# `docs/schemas/org_handles.schema.json` ships in a parallel, not-yet-merged PR
# (`carl/phase1-org-handles`, #474). Its `handles` items require exactly `org`, `platform`
# (one of `github`/`huggingface`/`homepage_domain`), `handle`, with `note` optional -- this is
# a hand-written stub matching that exact item shape, so this suite does not depend on a file
# that does not exist on `main` yet. Replace with a read of the real file once #474 merges.
ORG_HANDLE_ENTRY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["org", "platform", "handle"],
    "properties": {
        "org": {"type": "string"},
        "platform": {"enum": ["github", "huggingface", "homepage_domain"]},
        "handle": {"type": "string", "minLength": 1},
        "note": {"type": "string"},
    },
}


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
    points `resolution.LEDGER` at its own fixture file. Most tests below instead pass
    `resolved_count=0` explicitly and never touch the ledger at all."""
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
    body = digest.render(rows, "2026-36", resolved_count=0)
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
    body = digest.render(rows, "2026-36", resolved_count=0)
    positions = {row_id: body.index(f"`{row_id}`") for row_id in
                 ("high-blast", "mid-tiebreak", "mid-confidence", "low")}
    ordered = sorted(positions, key=positions.get)
    assert ordered == ["high-blast", "mid-tiebreak", "mid-confidence", "low"]


# -- cap, parked/pool policy, and unknown relations -------------------------------------------


def test_cap_of_25_active_items_and_the_overflow_is_reported():
    rows = [_row("membership", f"item-{i}", blast_radius=1, tiebreak=100 - i) for i in range(30)]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert body.count("#### `item-") == 25
    assert "5 additional item(s)" in body


def test_parked_rows_never_render_as_items_only_as_a_count():
    rows = [
        _row("membership", "active-one", state="active"),
        _row("membership", "parked-one", state="parked"),
        _row("membership", "parked-two", state="parked"),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
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
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "`m-pool`" not in body
    assert "`o-pool`" not in body
    assert "Overflow this week (ranked below the cap, not reviewed): 2" in body


def test_resurfaced_items_carry_their_reason():
    rows = [_row("org", "resurfaced-one", state="resurfaced", resurfaced_reason="age")]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "Resurfaced reason: age" in body


def test_unknown_relation_raises_before_the_cap():
    rows = [_row("weird", f"w{i}") for i in range(25)] + [_row("membership", "real-one")]
    with pytest.raises(ValueError, match="weird"):
        digest.render(rows, "2026-36", resolved_count=0)


def test_artifact_identity_section_says_why_it_is_empty():
    body = digest.render([_row("membership", "m1")], "2026-36", resolved_count=0)
    assert "Artifact identity" in body
    assert "does not yet union artifact_identity edges" in body


# -- per-relation blocks: membership/equivalence -> resolution_ledger.yaml --------------------


def test_membership_ledger_entry_uses_product_membership_relation():
    rows = [_row("membership", "m1", left={"kind": "pypi", "id": "m1"},
                 right={"kind": "product", "id": "acme"})]
    body = digest.render(rows, "2026-36", resolved_count=0)
    entry = yaml.safe_load(body.split("```yaml")[1].split("```")[0])[0]
    jsonschema.validate(entry, LEDGER_SCHEMA)
    assert entry["relation"] == "product_membership"
    assert entry["verdict"] == "member_of"
    assert entry["resolves_to"] == "acme"
    assert entry["decided_on"] == "2026-08-31"  # the sweep Monday for week 2026-36
    assert len(entry["note"]) >= 20


def test_equivalence_ledger_entry_uses_product_equivalence_relation():
    rows = [_row("equivalence", "e1", left={"kind": "github", "id": "acme/e1"},
                 right={"kind": "product", "id": "acme"})]
    body = digest.render(rows, "2026-36", resolved_count=0)
    entry = yaml.safe_load(body.split("```yaml")[1].split("```")[0])[0]
    jsonschema.validate(entry, LEDGER_SCHEMA)
    assert entry["relation"] == "product_equivalence"
    assert entry["verdict"] == "existing_product"
    assert entry["resolves_to"] == "acme"
    assert len(entry["note"]) >= 20


# -- the org relation: org_handles.yaml, never a ledger placeholder ---------------------------


def test_org_item_emits_an_org_handles_block_not_a_ledger_placeholder():
    rows = [_row("org", "o1", left={"kind": "github", "id": "acme-labs/widget"},
                 right={"kind": "org", "id": "acme-labs"})]
    body = digest.render(rows, "2026-36", resolved_count=0)
    entry = yaml.safe_load(body.split("```yaml")[1].split("```")[0])[0]
    jsonschema.validate(entry, ORG_HANDLE_ENTRY_SCHEMA)
    assert entry["org"] == "acme-labs"
    assert entry["platform"] == "github"
    assert entry["handle"] == "acme-labs"
    # M1: no relation/verdict/resolves_to fields at all -- this is not a ledger entry.
    assert "verdict" not in entry
    assert "relation" not in entry
    assert "resolves_to" not in entry


@pytest.mark.parametrize(
    "left_kind,left_id,expected_platform,expected_handle",
    [
        ("github", "acme-labs/widget", "github", "acme-labs"),
        ("huggingface_model", "acme-labs/some-model", "huggingface", "acme-labs"),
        ("huggingface_dataset", "acme-labs/some-dataset", "huggingface", "acme-labs"),
        ("homepage", "https://acme.example.com/about", "homepage_domain", "acme.example.com"),
    ],
)
def test_org_handle_derivation_per_artifact_kind(left_kind, left_id, expected_platform, expected_handle):
    rows = [_row("org", "o1", left={"kind": left_kind, "id": left_id},
                 right={"kind": "org", "id": "acme-labs"})]
    body = digest.render(rows, "2026-36", resolved_count=0)
    entry = yaml.safe_load(body.split("```yaml")[1].split("```")[0])[0]
    jsonschema.validate(entry, ORG_HANDLE_ENTRY_SCHEMA)
    assert entry["platform"] == expected_platform
    assert entry["handle"] == expected_handle


def test_org_handle_falls_back_and_flags_a_kind_with_no_platform_account():
    rows = [_row("org", "o1", left={"kind": "pypi", "id": "some-pkg"},
                 right={"kind": "org", "id": "acme-labs"})]
    body = digest.render(rows, "2026-36", resolved_count=0)
    entry = yaml.safe_load(body.split("```yaml")[1].split("```")[0])[0]
    jsonschema.validate(entry, ORG_HANDLE_ENTRY_SCHEMA)
    assert entry["platform"] == "homepage_domain"
    assert "verify" in entry["note"].lower()


# -- the artifact_identity relation: no block at all -------------------------------------------


def test_artifact_identity_item_renders_no_yaml_block():
    rows = [_row("artifact_identity", "a1", state="active",
                 left={"kind": "github", "id": "acme/a1"},
                 right={"kind": "github", "id": "acme/a1-renamed"})]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "`a1`" in body
    assert "```yaml" not in body
    assert "review the pair by hand" in body


# -- footer numbers computed from the rows -------------------------------------------------------


def test_unresolved_pool_size_is_every_row():
    rows = [_row("membership", f"i{i}", state=s) for i, s in
            enumerate(["active", "parked", "pool", "resurfaced"])]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "Unresolved pool size: 4" in body


def test_new_count_is_rows_first_seen_within_the_sweep_week():
    # Week 2026-36 spans Monday 2026-08-31 through Sunday 2026-09-06.
    rows = [
        _row("membership", "in-week", first_seen="2026-09-01"),
        _row("membership", "before-week", first_seen="2026-08-20"),
        _row("membership", "on-monday", first_seen="2026-08-31"),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "2 new" in body


def test_render_is_pure_when_resolved_count_is_supplied():
    """No ledger read happens at all when the caller supplies `resolved_count` -- the
    contract's `render(rows, week) -> str` purity, restored by making the third argument
    explicit rather than a hidden filesystem read."""
    body = digest.render([_row("membership", "m1")], "2026-36", resolved_count=7)
    assert "7 resolved" in body


def test_resolved_count_falls_back_to_reading_the_resolution_ledger(tmp_path, monkeypatch):
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
    body = digest.render([_row("membership", "m1")], "2026-36")  # resolved_count omitted
    assert "1 resolved" in body


def test_resolved_count_excludes_entries_outside_the_digests_relations(tmp_path, monkeypatch):
    """S2: a ledger entry with a relation the digest does not propose must not inflate
    "resolved this week" -- exercised with a synthetic out-of-vocabulary relation, since
    `resolution.py`'s schema does not allow one in practice today."""
    ledger_path = tmp_path / "ledger.yaml"
    ledger_path.write_text(
        "version: 1\n"
        "resolutions:\n"
        "  - artifact: {kind: pypi, id: in-vocabulary}\n"
        "    verdict: unresolved\n"
        "    relation: product_equivalence\n"
        "    decided_in: '#1'\n"
        "    decided_on: '2026-09-02'\n"
        "    note: a real digest-shaped relation, must be counted.\n"
    )
    monkeypatch.setattr(resolution, "LEDGER", ledger_path)
    monday, sunday = digest._week_bounds("2026-36")
    count = digest._resolved_this_week(monday, sunday)
    assert count == 1
    # Directly exercise the filter with a fabricated out-of-vocabulary relation, bypassing
    # resolution.load()'s own schema, to prove the filter -- not just the corpus's shape --
    # is what keeps the count honest.
    fake_entries = {
        ("key", "org_ownership"): {"relation": "org_ownership", "decided_on": "2026-09-02",
                                    "verdict": "confirmed", "note": "not a digest relation"},
    }
    assert all(resolution.relation_of(e) not in resolution.RELATIONS for e in fake_entries.values())


def test_oldest_unresolved_age_in_weeks_from_first_seen():
    # Sweep Monday for 2026-36 is 2026-08-31; 8 weeks earlier is 2026-07-06.
    rows = [
        _row("membership", "old-one", first_seen="2026-07-06"),
        _row("membership", "new-one", first_seen="2026-08-25"),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "Oldest unresolved age: 8 weeks" in body


# -- warehouse plumbing -------------------------------------------------------------------------


def test_is_table_not_found_matches_the_real_trino_text():
    """M2: the literal error text confirmed live against an undeployed identity table --
    `USER_ERROR: TablesNotFound - Tables do not exist or are inaccessible: <table>`. A round-1
    version of the marker list matched "does not exist" and "table_not_found", neither of
    which appears in this camel-case, plural wording, so it never fired."""
    real_text = (
        "USER_ERROR: TablesNotFound - Tables do not exist or are inaccessible: "
        "currentai.identity.digest"
    )
    assert digest._is_table_not_found(RuntimeError(real_text))


def test_is_table_not_found_reuses_identity_evals_marker_set():
    from build.identity_eval import _TABLE_NOT_FOUND_MARKERS

    assert digest._TABLE_NOT_FOUND_MARKERS is _TABLE_NOT_FOUND_MARKERS


def test_missing_table_exits_2_without_allow_unprovisioned(monkeypatch, tmp_path):
    def _raise():
        raise digest.WarehouseTableMissing(digest.TABLE, RuntimeError("does not exist"))

    monkeypatch.setattr(digest, "load_rows_from_warehouse", _raise)
    out = tmp_path / "out.md"
    code = digest.main(["--week", "2026-36", "--out", str(out)])
    assert code == 2
    assert not out.exists()


@pytest.fixture
def uncontracted_digest(monkeypatch, tmp_path):
    """Point the provisioning record at an empty dependency manifest.

    The two tests below are about which EXCEPTION CLASS `--allow-unprovisioned` may swallow.
    The committed tree contracts `identity.digest` with a mirror block, so the flag is refused
    before any query runs unless the fixture withdraws that record first.
    """
    deps = tmp_path / "dependencies.yaml"
    deps.write_text(yaml.dump({"dependencies": []}))
    monkeypatch.setattr(digest, "DEPENDENCIES_PATH", deps)


def test_missing_table_exits_0_with_allow_unprovisioned(monkeypatch, tmp_path, uncontracted_digest):
    def _raise():
        raise digest.WarehouseTableMissing(digest.TABLE, RuntimeError("does not exist"))

    monkeypatch.setattr(digest, "load_rows_from_warehouse", _raise)
    out = tmp_path / "out.md"
    code = digest.main(["--week", "2026-36", "--out", str(out), "--allow-unprovisioned"])
    assert code == 0
    assert not out.exists()


def test_other_warehouse_failure_always_exits_2_even_with_allow_unprovisioned(
    monkeypatch, tmp_path, uncontracted_digest
):
    def _raise():
        raise digest.WarehouseQueryFailed(digest.TABLE, RuntimeError("access denied"))

    monkeypatch.setattr(digest, "load_rows_from_warehouse", _raise)
    out = tmp_path / "out.md"
    code = digest.main(["--week", "2026-36", "--out", str(out), "--allow-unprovisioned"])
    assert code == 2
    assert not out.exists()


def test_digest_is_contracted_reads_the_committed_manifest():
    assert digest._digest_is_contracted() is True


def test_digest_is_contracted_ignores_a_contract_with_no_mirror(tmp_path):
    deps = tmp_path / "dependencies.yaml"
    deps.write_text(yaml.dump({"dependencies": [{"table": digest.TABLE}]}))
    assert digest._digest_is_contracted(deps) is False


def test_allow_unprovisioned_is_refused_once_the_table_is_contracted(monkeypatch, tmp_path):
    """No query is attempted -- the refusal comes before the warehouse is touched."""
    def _boom():
        raise AssertionError("the warehouse must not be queried after the refusal")

    monkeypatch.setattr(digest, "load_rows_from_warehouse", _boom)
    out = tmp_path / "out.md"
    code = digest.main(["--week", "2026-36", "--out", str(out), "--allow-unprovisioned"])
    assert code == 2
    assert not out.exists()


def test_the_digest_workflow_does_not_pass_allow_unprovisioned():
    """The flag cannot come back while the contract stands: `main` refuses it, so a workflow
    still passing it would fail every scheduled run."""
    wf = (ROOT / ".github" / "workflows" / "identity-digest.yml").read_text()
    for line in wf.splitlines():
        if line.lstrip().startswith("#"):
            continue
        assert "--allow-unprovisioned" not in line, (
            "identity-digest.yml passes --allow-unprovisioned, but currentai.identity.digest "
            "is contracted in warehouse/dependencies.yaml and build.identity_digest refuses it"
        )


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
    body = digest.render(SAMPLE, "2026-36", resolved_count=0)
    assert body.startswith("# identity digest: 2026-36")
    assert "### Scorecard" in body
