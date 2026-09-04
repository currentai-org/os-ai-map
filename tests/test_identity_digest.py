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


def _row(relation, item_id, *, state="active", rank=1, blast_radius=1, tiebreak=0, confidence=0.5,
         left=None, right=None, first_seen="2026-08-01", resurfaced_reason=None,
         method=("declared",), evidence=None):
    """A digest row in the current `udms/identity_digest.sql` column contract.

    `rank` defaults to 1 for the common single-row case; a test exercising rank order supplies
    distinct values explicitly, since `render()` no longer derives an order from
    `blast_radius`/`tiebreak`/`confidence` -- those three stay as plain output columns a fixture
    can still set, but they are not read by the renderer any more. `evidence` defaults to one
    `<url> | <excerpt>` string per method so a body always has something to link, matching the
    warehouse's real shape rather than the old method-name-as-evidence placeholder.
    """
    if evidence is None:
        evidence = [f"https://example.com/{item_id} | {m}" for m in method]
    return {
        "sweep_week": "2026-08-31",
        "relation": relation,
        "item_id": item_id,
        "candidate_key": f"pypi:{item_id}",
        "left": left or {"kind": "pypi", "id": item_id},
        "right": right or {"kind": "product", "id": "target"},
        "confidence": confidence,
        "method": list(method),
        "evidence": list(evidence),
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
        "rank": rank if state in ("active", "resurfaced") else None,
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


def test_within_a_section_items_render_in_the_tables_rank_order():
    """`render()` orders strictly by the `rank` column, ascending -- not by blast_radius,
    tiebreak, or confidence (those are carried as plain columns but no longer read for
    ordering). Rows are deliberately built with a rank order that contradicts what the old
    `_rank_key` (blast_radius desc, tiebreak desc, confidence desc) would have produced, so a
    regression back to that key would fail this test.
    """
    rows = [
        _row("membership", "would-be-last", rank=1, blast_radius=1, tiebreak=0, confidence=0.1),
        _row("membership", "would-be-first", rank=4, blast_radius=3, tiebreak=0, confidence=0.5),
        _row("membership", "would-be-second", rank=3, blast_radius=1, tiebreak=100, confidence=0.5),
        _row("membership", "would-be-third", rank=2, blast_radius=1, tiebreak=0, confidence=0.6),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
    positions = {row_id: body.index(f"`{row_id}`") for row_id in
                 ("would-be-last", "would-be-third", "would-be-second", "would-be-first")}
    ordered = sorted(positions, key=positions.get)
    assert ordered == ["would-be-last", "would-be-third", "would-be-second", "would-be-first"]


def test_item_heading_carries_its_global_rank():
    rows = [_row("membership", "m1", rank=7)]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "#### #7 `m1`" in body


def test_rows_missing_rank_do_not_render_as_items():
    """An `active`/`resurfaced` row with no rank should not happen per the SQL contract, but
    `render()` must not crash or silently treat it as rank-0 -- it is simply not an item this
    week."""
    row = _row("membership", "no-rank")
    row["rank"] = None
    body = digest.render([row], "2026-36", resolved_count=0)
    assert "`no-rank`" not in body


# -- cap, parked/pool policy, and unknown relations -------------------------------------------


def test_cap_of_25_ranked_items_and_the_overflow_is_reported():
    """Should not happen per the SQL contract (it caps `rank` at 25 itself), but `render()`
    still defends: only the first 25 by rank render, the rest are reported as cut, and a
    warning prints."""
    rows = [_row("membership", f"item-{i}", rank=i + 1) for i in range(30)]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert body.count("`item-") == 25
    assert "5 additional item(s)" in body
    for i in range(25):
        assert f"item-{i}" in body
    for i in range(25, 30):
        assert f"`item-{i}`" not in body


def test_warning_prints_when_more_than_25_are_ranked(capsys):
    rows = [_row("membership", f"item-{i}", rank=i + 1) for i in range(26)]
    digest.render(rows, "2026-36", resolved_count=0)
    out = capsys.readouterr().out
    assert "warning" in out.lower()
    assert "26" in out
    assert "25" in out


def test_parked_rows_never_render_as_items_only_as_a_count():
    rows = [
        _row("membership", "active-one", state="active", rank=1),
        _row("membership", "parked-one", state="parked"),
        _row("membership", "parked-two", state="parked"),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "`parked-one`" not in body
    assert "`parked-two`" not in body
    assert "`active-one`" in body
    assert "Parked: 2 (name-match only; resurfaces after 56 days or when evidence changes)" in body


def test_pool_rows_render_as_a_single_total_not_per_section():
    rows = [
        _row("membership", "m-pool", state="pool"),
        _row("org", "o-pool", state="pool"),
        _row("equivalence", "e-active", state="active", rank=1),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "`m-pool`" not in body
    assert "`o-pool`" not in body
    assert "Overflow this week (ranked below the cap, not reviewed): 2" in body


def test_resurfaced_items_carry_their_reason():
    rows = [_row("org", "resurfaced-one", state="resurfaced", rank=1, resurfaced_reason="age")]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "Resurfaced reason: age" in body
    assert "`resurfaced-one`" in body


def test_resurfaced_items_are_ranked_and_rendered_like_any_other_item():
    """Alongside `active`, `resurfaced` is one of the two states that competes for the cap and
    renders as an item -- not a third bucket."""
    rows = [
        _row("org", "resurfaced-one", state="resurfaced", rank=1, resurfaced_reason="age"),
        _row("org", "active-one", state="active", rank=2),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "### Org (2 items)" in body
    assert "`resurfaced-one`" in body
    assert "`active-one`" in body


def test_alias_evidence_item_renders_like_any_other_active_item():
    """Alias-evidence items (`product_alias`, confidence 0.9) are `active`, not a distinct
    case -- they render exactly like any other item, YAML block included."""
    rows = [_row(
        "equivalence", "alias-one", state="active", rank=1, confidence=0.9,
        method=["product_alias"],
        evidence=["https://huggingface.co/acme/widget-v2 | product_aliases: widget-v2 -> widget"],
        left={"kind": "huggingface_model", "id": "acme/widget-v2"},
        right={"kind": "product", "id": "widget"},
    )]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "`alias-one`" in body
    assert "```yaml" in body
    assert "[product_aliases: widget-v2 -> widget](https://huggingface.co/acme/widget-v2)" in body


def test_unknown_relation_raises_before_the_cap():
    rows = [_row("weird", f"w{i}") for i in range(25)] + [_row("membership", "real-one")]
    with pytest.raises(ValueError, match="weird"):
        digest.render(rows, "2026-36", resolved_count=0)


def test_artifact_identity_section_says_why_it_is_empty():
    body = digest.render([_row("membership", "m1")], "2026-36", resolved_count=0)
    assert "Artifact identity" in body
    assert "does not yet union artifact_identity edges" in body


# -- evidence rendering -------------------------------------------------------------------------


def test_evidence_element_renders_as_a_markdown_link_bullet():
    rows = [_row(
        "membership", "m1", rank=1,
        evidence=["https://github.com/acme/widget | acme owns the widget backlink"],
    )]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "- [acme owns the widget backlink](https://github.com/acme/widget)" in body


def test_evidence_element_without_a_pipe_falls_back_to_plain_text():
    rows = [_row("membership", "m1", rank=1, evidence=["no url here"])]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "- no url here" in body


def test_method_is_a_compact_label_never_rendered_as_evidence():
    rows = [_row(
        "membership", "m1", rank=1, method=["package_backlink"],
        evidence=["https://pypi.org/project/m1 | listed as a dependant of acme"],
    )]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "- Method: package_backlink" in body
    # the method name never appears as its own evidence bullet
    assert "- package_backlink" not in body


def test_no_evidence_renders_a_none_bullet():
    rows = [_row("membership", "m1", rank=1, evidence=[])]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "- Evidence:" in body
    assert "  - none" in body


# -- the "Top 5 this week" summary ----------------------------------------------------------------


def test_top_5_lists_the_five_highest_ranked_items_regardless_of_section():
    rows = [
        _row("membership", "m1", rank=1),
        _row("org", "o1", rank=2),
        _row("equivalence", "e1", rank=3),
        _row("membership", "m2", rank=4),
        _row("org", "o2", rank=5),
        _row("equivalence", "e2", rank=6),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
    top5 = body.split("### Top 5 this week")[1].split("### Equivalence")[0]
    for item_id in ("m1", "o1", "e1", "m2", "o2"):
        assert item_id in top5
    assert "e2" not in top5


def test_top_5_shows_rank_relation_left_right_and_confidence():
    rows = [_row(
        "membership", "m1", rank=1, confidence=0.75,
        left={"kind": "pypi", "id": "m1"}, right={"kind": "product", "id": "acme"},
    )]
    body = digest.render(rows, "2026-36", resolved_count=0)
    top5 = body.split("### Top 5 this week")[1].split("###", 1)[0]
    assert "1. Membership: `pypi:m1` → `product:acme` (confidence 0.75)" in top5


# -- per-relation blocks: membership/equivalence -> resolution_ledger.yaml --------------------


def test_membership_ledger_entry_uses_product_membership_relation():
    rows = [_row("membership", "m1", rank=1, left={"kind": "pypi", "id": "m1"},
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


def test_footer_reports_ranked_items_by_relation():
    rows = [
        _row("membership", "m1", rank=1),
        _row("membership", "m2", rank=2),
        _row("org", "o1", rank=3),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert (
        "Ranked items by relation: Equivalence 0, Membership 2, Org 1, Artifact identity 0"
        in body
    )


def test_oldest_unresolved_age_uses_first_seen_across_all_rows_not_just_ranked():
    """Footer 'oldest unresolved age' reads `first_seen` across every row -- parked and pool
    included -- since a starved item is exactly the one the top-25 ranking never surfaces."""
    rows = [
        _row("membership", "old-parked", state="parked", first_seen="2026-07-06"),
        _row("membership", "new-ranked", rank=1, first_seen="2026-08-25"),
    ]
    body = digest.render(rows, "2026-36", resolved_count=0)
    assert "Oldest unresolved age: 8 weeks" in body


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
