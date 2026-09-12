"""`build.identity_adopt`: the confidence-1.0 auto-adopt leg of the weekly digest.

Everything runs against fixture rows and temporary copies of the two destination files;
nothing here touches `sources/` or the warehouse. The #512 fixture
(`tests/fixtures/identity_digest_512.json`) is the ranked queue of the 2026-37 digest as it
was rendered, rebuilt from the issue body -- it is the one-time batch the mechanism was first
applied to, and the test pins what that application must do.
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import jsonschema
import pytest
import yaml

from build import identity_adopt as adopt
from build import identity_digest as digest
from build import resolution
from build.resolution import AUTO_ADOPT_NOTE_PREFIX

ROOT = Path(__file__).resolve().parent.parent
ROWS_512 = json.loads((ROOT / "tests" / "fixtures" / "identity_digest_512.json").read_text())
LEDGER_SCHEMA = json.loads((ROOT / "docs" / "schemas" / "resolution_ledger.schema.json").read_text())
ORG_HANDLES_SCHEMA = json.loads((ROOT / "docs" / "schemas" / "org_handles.schema.json").read_text())

DECIDED_ON = date(2026, 9, 11)


def _row(relation, left_kind, left_id, right_id, *, confidence=1.0, method, evidence=None,
         rank=1, state="active", item_id=None):
    right_kind = "org" if relation == "org" else "product"
    if evidence is None:
        evidence = [f"https://example.com/{left_id} | {m}" for m in method]
    return {
        "sweep_week": "2026-09-07",
        "relation": relation,
        "item_id": item_id or f"{relation}:{left_kind}:{left_id}->{right_id}",
        "candidate_key": f"{left_kind}:{left_id}",
        "left": {"kind": left_kind, "id": left_id},
        "right": {"kind": right_kind, "id": right_id},
        "confidence": confidence,
        "method": list(method),
        "evidence": list(evidence),
        "penalties": [],
        "proposed_action": f"confirm_{relation}_edge",
        "blast_radius": 1,
        "tiebreak": 0,
        "options": ["confirm", "reject", "park"],
        "default_if_ignored": "no edge",
        "first_seen": "2026-09-07 00:00:00",
        "last_evidence_change": None,
        "state": state,
        "resurfaced_reason": None,
        "rank": rank if state in ("active", "resurfaced") else None,
    }


@pytest.fixture
def files(tmp_path):
    """Temporary destination files: an empty-ish ledger, a small org_handles, one org dir."""
    ledger = tmp_path / "resolution_ledger.yaml"
    ledger.write_text(
        "# hand-formatted header comment that must survive an append\n"
        "version: 1\n"
        "resolutions:\n"
        "- repo: acme/acme-sdk\n"
        "  verdict: existing_product\n"
        "  product: acme\n"
        "  decided_in: '#1'\n"
        "  decided_on: '2026-09-01'\n"
        "  note: 'a person ruled this one; the SDK is the product'\n"
    )
    handles = tmp_path / "org_handles.yaml"
    handles.write_text(
        "version: 1\n"
        "handles:\n"
        "- org: acme\n"
        "  platform: github\n"
        "  handle: acme\n"
    )
    orgs = tmp_path / "organizations"
    orgs.mkdir()
    for slug in ("acme", "beta-labs"):
        (orgs / f"{slug}.yaml").write_text(f"name: {slug}\nproducts: []\n")
    return {"ledger": ledger, "handles": handles, "orgs": orgs}


def _adopt(rows, files, *, write=True, decided_in="#900"):
    return adopt.adopt(
        rows,
        decided_in=decided_in,
        decided_on=DECIDED_ON,
        write=write,
        ledger_path=files["ledger"],
        org_handles_path=files["handles"],
        organizations_dir=files["orgs"],
    )


# -- the two tests, per relation ---------------------------------------------------------------


def test_equivalence_qualifies_when_name_segment_equals_slug_and_method_is_authoritative():
    row = _row("equivalence", "github", "raga-ai-hub/ragaai-catalyst", "ragaai-catalyst",
               method=("name_match", "resolution_ledger"))
    ok, reason = adopt.qualifies(row)
    assert ok, reason


def test_equivalence_name_agreement_is_recomputed_not_read_from_method():
    # `name_match` claimed, but the name segment is not the slug: held.
    row = _row("equivalence", "github", "vllm-project/vllm", "some-other-product",
               method=("name_match", "resolution_ledger"))
    ok, reason = adopt.qualifies(row)
    assert not ok and "name" in reason


def test_a_1_0_without_an_authoritative_method_does_not_qualify():
    row = _row("equivalence", "huggingface_model", "acme/acme", "acme", method=("product_alias",))
    ok, reason = adopt.qualifies(row)
    assert not ok and "graph" in reason


def test_below_threshold_never_qualifies_even_with_both_agreements():
    row = _row("equivalence", "github", "acme/acme", "acme", confidence=0.9,
               method=("name_match", "resolution_ledger"))
    assert not adopt.qualifies(row)[0]


@pytest.mark.parametrize("confidence", [
    0.9999999995,        # rounds to 1.0 at any sane tolerance; the SQL never emits it
    1.0000000001,        # above the threshold is not "at" it
    1.5,
    float("nan"),
    float("inf"),
    "1.0000000001",
    None,
    "one",
])
def test_the_gate_is_exactly_1_0_not_a_tolerance(confidence):
    row = _row("equivalence", "github", "acme/acme", "acme", confidence=confidence,
               method=("name_match", "resolution_ledger"))
    ok, reason = adopt.qualifies(row)
    assert not ok
    assert "confidence" in reason


@pytest.mark.parametrize("confidence", [1.0, 1, "1.0", "1"])
def test_an_exact_1_0_in_any_numeric_spelling_passes_the_gate(confidence):
    row = _row("equivalence", "github", "acme/acme", "acme", confidence=confidence,
               method=("name_match", "resolution_ledger"))
    assert adopt.qualifies(row)[0]


def test_a_boolean_true_is_not_a_confidence_of_1_0():
    row = _row("equivalence", "github", "acme/acme", "acme", confidence=True,
               method=("name_match", "resolution_ledger"))
    ok, reason = adopt.qualifies(row)
    assert not ok and "confidence" in reason


def test_parked_and_pool_rows_never_qualify():
    row = _row("equivalence", "github", "acme/acme", "acme", method=("name_match", "resolution_ledger"),
               state="pool")
    assert not adopt.qualifies(row)[0]


def test_artifact_identity_has_no_file_and_never_qualifies():
    row = _row("artifact_identity", "github", "acme/acme", "acme", method=("declared",))
    assert not adopt.qualifies(row)[0]


def test_membership_qualifies_on_declared_plus_name_agreement():
    row = _row("membership", "pypi", "acme", "acme", method=("declared", "name_match"))
    assert adopt.qualifies(row)[0]


def test_org_qualifies_when_handle_agrees_and_graph_evidence_names_the_org():
    row = _row("org", "github", "beta-labs/tool", "beta-labs", method=("org_handle",),
               evidence=["https://github.com/beta-labs | org_handles: beta-labs github beta-labs"])
    assert adopt.qualifies(row, {"handles": []})[0]


def test_org_handle_agreement_may_come_from_a_declared_handle_not_the_slug():
    handles = {"handles": [{"org": "acme", "platform": "github", "handle": "acmecorp"}]}
    row = _row("org", "huggingface_model", "acmecorp/model", "acme", method=("org_handle",),
               evidence=["https://huggingface.co/acmecorp | org_handles: acme huggingface acmecorp"])
    assert adopt.qualifies(row, handles)[0]


def test_org_without_the_graphs_own_evidence_line_does_not_qualify():
    row = _row("org", "github", "beta-labs/tool", "beta-labs", method=("org_handle",),
               evidence=["https://github.com/beta-labs | some other excerpt"])
    ok, reason = adopt.qualifies(row, {"handles": []})
    assert not ok and "graph" in reason


def test_org_evidence_naming_a_different_org_does_not_qualify():
    row = _row("org", "github", "beta-labs/tool", "beta-labs", method=("org_handle",),
               evidence=["https://github.com/beta-labs | org_handles: acme github beta-labs"])
    assert not adopt.qualifies(row, {"handles": []})[0]


def test_org_row_on_a_kind_with_no_platform_account_is_never_adopted():
    row = _row("org", "pypi", "beta-labs", "beta-labs", method=("org_handle",),
               evidence=["https://pypi.org/project/beta-labs | org_handles: beta-labs github beta-labs"])
    assert not adopt.qualifies(row, {"handles": []})[0]


# -- destination checks and the write --------------------------------------------------------------


def test_write_appends_a_ledger_entry_that_validates_and_keeps_the_header(files):
    row = _row("membership", "pypi", "beta", "beta", method=("declared", "name_match"))
    report = _adopt([row], files)
    assert [d.item_id for d in report.written] == [row["item_id"]]
    text = files["ledger"].read_text()
    assert text.startswith("# hand-formatted header comment")
    entries = yaml.safe_load(text)["resolutions"]
    assert len(entries) == 2
    new = entries[-1]
    jsonschema.validate(new, LEDGER_SCHEMA)
    assert new["verdict"] == "member_of" and new["relation"] == "product_membership"
    assert new["resolves_to"] == "beta"
    assert new["decided_in"] == "#900"
    assert new["decided_on"] == "2026-09-11"
    assert new["note"].startswith(AUTO_ADOPT_NOTE_PREFIX)
    assert resolution.is_auto_adopted(new)
    resolution.load(files["ledger"])  # no duplicate key, still parses


def test_write_appends_an_org_handle_that_validates(files):
    row = _row("org", "github", "beta-labs/tool", "beta-labs", method=("org_handle",),
               evidence=["https://github.com/beta-labs | org_handles: beta-labs github beta-labs"])
    report = _adopt([row], files)
    assert len(report.written) == 1
    doc = yaml.safe_load(files["handles"].read_text())
    jsonschema.validate(doc, ORG_HANDLES_SCHEMA)
    new = doc["handles"][-1]
    assert new == {
        "org": "beta-labs", "platform": "github", "handle": "beta-labs", "note": new["note"],
    }
    assert new["note"].startswith(AUTO_ADOPT_NOTE_PREFIX)


def test_an_agreeing_prior_ruling_is_already_recorded_and_nothing_is_written(files):
    before = files["ledger"].read_text()
    row = _row("equivalence", "github", "acme/acme-sdk", "acme", method=("name_match", "resolution_ledger"))
    # Name segment `acme-sdk` != `acme`, so make the agreement explicit through the slug.
    row["right"]["id"] = "acme-sdk"
    report = _adopt([row], files)
    # The ledger resolves acme/acme-sdk -> acme, the row says -> acme-sdk: that is a conflict.
    assert [d.outcome for d in report.conflicts] == ["conflict"]
    assert files["ledger"].read_text() == before

    row = _row("equivalence", "github", "acme/acme-sdk", "acme", method=("name_match", "resolution_ledger"))
    row["left"]["id"] = "acme/acme"
    row["item_id"] = "equivalence:github:acme/acme->acme"
    # Now a fresh artifact with no ruling: written.
    report = _adopt([row], files)
    assert len(report.written) == 1
    # And a second run over the same row finds it already recorded -- idempotent.
    report = _adopt([row], files)
    assert len(report.written) == 0 and len(report.already_recorded) == 1
    assert "decided in #900" in report.already_recorded[0].reason


def test_a_disagreeing_prior_ruling_is_held_never_overturned(files):
    files["ledger"].write_text(files["ledger"].read_text() + (
        "- artifact:\n    kind: pypi\n    id: beta\n"
        "  verdict: not_member_of\n  relation: product_membership\n  resolves_to: beta\n"
        "  decided_in: '#2'\n  decided_on: '2026-09-02'\n"
        "  note: 'a person ruled this package is not the product''s usage'\n"
    ))
    before = files["ledger"].read_text()
    row = _row("membership", "pypi", "beta", "beta", method=("declared", "name_match"))
    report = _adopt([row], files)
    assert len(report.conflicts) == 1 and "not_member_of" in report.conflicts[0].reason
    assert files["ledger"].read_text() == before


def test_a_handle_claimed_by_another_org_is_held(files):
    row = _row("org", "github", "acme/tool", "beta-labs", method=("org_handle",),
               evidence=["https://github.com/acme | org_handles: beta-labs github acme"])
    # name agrees via the slug? `acme` vs `beta-labs`: no -- so give beta-labs a declared handle.
    files["handles"].write_text(files["handles"].read_text() + "- org: beta-labs\n  platform: huggingface\n  handle: acme\n")
    report = _adopt([row], files)
    assert len(report.conflicts) == 1 and "declared for 'acme'" in report.conflicts[0].reason


def test_an_org_with_no_organization_file_is_held(files):
    row = _row("org", "github", "gamma/tool", "gamma", method=("org_handle",),
               evidence=["https://github.com/gamma | org_handles: gamma github gamma"])
    report = _adopt([row], files)
    assert len(report.conflicts) == 1 and "sources/organizations/gamma.yaml" in report.conflicts[0].reason


def test_two_rows_onto_one_handle_write_it_once(files):
    rows = [
        _row("org", "github", "beta-labs/a", "beta-labs", method=("org_handle",), rank=1,
             evidence=["https://github.com/beta-labs | org_handles: beta-labs github beta-labs"]),
        _row("org", "github", "beta-labs/b", "beta-labs", method=("org_handle",), rank=2,
             evidence=["https://github.com/beta-labs | org_handles: beta-labs github beta-labs"]),
    ]
    report = _adopt(rows, files)
    assert len(report.written) == 1 and len(report.already_recorded) == 1
    doc = yaml.safe_load(files["handles"].read_text())
    assert sum(1 for h in doc["handles"] if h["handle"] == "beta-labs") == 1


def test_dry_run_plans_but_writes_nothing(files):
    before = files["ledger"].read_text()
    row = _row("membership", "pypi", "beta", "beta", method=("declared", "name_match"))
    report = _adopt([row], files, write=False)
    assert report.dry_run and len(report.written) == 1
    assert files["ledger"].read_text() == before


# -- the one-time batch: issue #512 -------------------------------------------------------------------


def test_512_queue_has_exactly_one_qualifying_item_and_it_is_ragaai_catalyst():
    qualifying = [r for r in ROWS_512 if adopt.qualifies(r, {"handles": []})[0]]
    assert [r["item_id"] for r in qualifying] == [
        "equivalence:github:raga-ai-hub/ragaai-catalyst->head:ragaai-catalyst"
    ]


def test_512_batch_against_the_real_ledger_writes_nothing_because_a_person_already_ruled(tmp_path):
    """The 1.0 item's confidence comes FROM the ledger ruling (method `resolution_ledger`), so
    the ledger already holds `raga-ai-hub/RagaAI-Catalyst -> ragaai-catalyst` by hand
    (2026-09-02). The adopt leg must report it as already recorded, not append a duplicate
    key `build.resolution.load` would refuse."""
    ledger = tmp_path / "ledger.yaml"
    handles = tmp_path / "handles.yaml"
    shutil.copy(ROOT / "sources" / "resolution_ledger.yaml", ledger)
    shutil.copy(ROOT / "sources" / "org_handles.yaml", handles)
    before = (ledger.read_text(), handles.read_text())
    report = adopt.adopt(
        ROWS_512, decided_in="#512", decided_on=DECIDED_ON,
        ledger_path=ledger, org_handles_path=handles,
        organizations_dir=ROOT / "sources" / "organizations",
    )
    assert report.written == [] and report.conflicts == []
    assert [d.item_id for d in report.already_recorded] == [
        "equivalence:github:raga-ai-hub/ragaai-catalyst->head:ragaai-catalyst"
    ]
    assert "existing_product -> ragaai-catalyst" in report.already_recorded[0].reason
    assert (ledger.read_text(), handles.read_text()) == before


# -- rendering with an adoption report ------------------------------------------------------------------


def test_render_lists_adopted_items_in_their_own_section_above_the_review_queue(files):
    rows = [
        _row("membership", "pypi", "beta", "beta", method=("declared", "name_match"), rank=1),
        _row("equivalence", "github", "x/y", "z", confidence=0.9, method=("product_alias",), rank=2),
    ]
    report = _adopt(rows, files)
    body = digest.render(rows, "2026-37", resolved_count=0, adoption=report)
    adopted_at = body.index("### Auto-adopted (1 item)")
    assert adopted_at < body.index("### Equivalence (1 item)")
    assert "written to `sources/resolution_ledger.yaml`" in body
    # The adopted item is no longer a review item: no heading, no paste block for it.
    assert "#### #1 " not in body
    assert "### Membership (0 items)" in body
    # The 0.9 item renders exactly as a review item with its paste block.
    assert "#### #2 `equivalence:github:x/y->z`" in body
    assert "decided_in: '#<issue>'" in body
    assert "- Auto-adopted this week: 1 written, 0 already recorded, 0 held" in body


def test_render_top_5_excludes_adopted_items(files):
    rows = [
        _row("membership", "pypi", "beta", "beta", method=("declared", "name_match"), rank=1),
        _row("equivalence", "github", "x/y", "z", confidence=0.9, method=("product_alias",), rank=2),
    ]
    report = _adopt(rows, files)
    body = digest.render(rows, "2026-37", resolved_count=0, adoption=report)
    top5 = body.split("### Top 5 this week")[1].split("###")[0]
    assert "pypi:beta" not in top5 and "github:x/y" in top5


def test_render_keeps_a_held_item_in_the_review_queue_with_its_reason(files):
    files["ledger"].write_text(files["ledger"].read_text() + (
        "- artifact:\n    kind: pypi\n    id: beta\n"
        "  verdict: not_member_of\n  relation: product_membership\n  resolves_to: beta\n"
        "  decided_in: '#2'\n  decided_on: '2026-09-02'\n"
        "  note: 'a person ruled this package is not the product''s usage'\n"
    ))
    rows = [_row("membership", "pypi", "beta", "beta", method=("declared", "name_match"))]
    report = _adopt(rows, files)
    body = digest.render(rows, "2026-37", resolved_count=0, adoption=report)
    assert "### Auto-adopted (0 items)" in body
    assert "#### #1 `membership:pypi:beta->beta`" in body
    assert "- Auto-adopt held: ledger rules not_member_of for beta" in body


def test_render_says_already_recorded_without_a_paste_block():
    report = adopt.adopt(
        ROWS_512, decided_in="#512", decided_on=DECIDED_ON, write=False,
    )
    body = digest.render(ROWS_512, "2026-37", resolved_count=0, adoption=report)
    assert "already recorded in `sources/resolution_ledger.yaml`" in body
    assert "#### #1 `equivalence:github:raga-ai-hub/ragaai-catalyst" not in body
    assert "### Equivalence (4 items)" in body


def test_render_without_an_adoption_report_is_unchanged():
    body = digest.render(ROWS_512, "2026-37", resolved_count=0)
    assert "Auto-adopted" not in body
    assert "#### #1 `equivalence:github:raga-ai-hub/ragaai-catalyst" in body


# -- CLI ------------------------------------------------------------------------------------------------


def test_cli_adopt_requires_decided_in(tmp_path):
    with pytest.raises(SystemExit):
        digest.main([
            "--week", "2026-37", "--out", str(tmp_path / "d.md"),
            "--rows", str(ROOT / "tests" / "fixtures" / "identity_digest_512.json"), "--adopt",
        ])


def test_cli_adopt_dry_run_writes_a_report_and_the_body(tmp_path, capsys):
    report_path = tmp_path / "adopt.json"
    rc = digest.main([
        "--week", "2026-37", "--out", str(tmp_path / "d.md"),
        "--rows", str(ROOT / "tests" / "fixtures" / "identity_digest_512.json"),
        "--adopt", "--adopt-dry-run", "--decided-in", "#512", "--decided-on", "2026-09-11",
        "--adopt-report", str(report_path), "--dump-rows", str(tmp_path / "rows.json"),
    ])
    assert rc == 0
    report = json.loads(report_path.read_text())
    assert report["dry_run"] is True and report["written"] == []
    assert len(report["already_recorded"]) == 1
    assert "auto-adopt (dry run): 0 written, 1 already recorded, 0 held" in capsys.readouterr().out
    assert len(json.loads((tmp_path / "rows.json").read_text())) == len(ROWS_512)
    assert "### Auto-adopted (1 item)" in (tmp_path / "d.md").read_text()


# -- the workflow -------------------------------------------------------------------------------------


def test_the_digest_workflow_adopts_after_the_issue_exists_and_opens_a_pr_not_a_push():
    text = (ROOT / ".github" / "workflows" / "identity-digest.yml").read_text()
    issue_at = text.index("Open or update the digest issue")
    adopt_at = text.index("--adopt --decided-in \"#$NUMBER\"")
    pr_at = text.index("gh pr create")
    assert issue_at < adopt_at < pr_at
    assert "git add sources/resolution_ledger.yaml sources/org_handles.yaml" in text
    assert "git add -A" not in text
    assert "digest-adopt/" in text
    assert "GH_FETCH_TOKEN" in text
    assert "pull-requests: write" in text
    assert 'git push -u origin "$BRANCH"' in text
    assert "git push origin main" not in text and "git push origin HEAD:main" not in text
    assert "Nothing adopted; no PR." in text


def test_the_digest_workflow_reuses_the_weeks_branch_and_pr_on_a_rerun():
    """A same-week rerun must not recreate the branch from main (non-fast-forward push) or
    open a second PR, and a run that pushed but never created its PR must be recoverable."""
    text = (ROOT / ".github" / "workflows" / "identity-digest.yml").read_text()
    branch_at = text.index("Check out the week's adoption branch")
    adopt_at = text.index("--adopt --decided-in \"#$NUMBER\"")
    assert branch_at < adopt_at, "the adopt pass must read the branch's ledger, not main's"
    assert 'git checkout -B "$BRANCH" "origin/$BRANCH"' in text
    assert 'git ls-remote --exit-code --heads origin "$BRANCH"' in text
    # Publish whenever the branch is ahead of main, not only when this run committed.
    assert 'git rev-list --count "origin/main..$BRANCH"' in text
    assert 'gh pr list -R "$GITHUB_REPOSITORY" --head "$BRANCH" --state open' in text
    assert 'gh pr edit "$EXISTING_PR"' in text
    assert "git push --force" not in text and "push -f " not in text
