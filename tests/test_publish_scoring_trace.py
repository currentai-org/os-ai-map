"""The scoring-trace publisher's safety surface — validation, no-write dry runs, immutable archives.

`build/publish_scoring_trace.py` uploads the three scoring-trace CSVs (`axis_facts`,
`axis_rule_matches`, `axis_results`) to OSO. The network path is a maintainer step, but the guards
that keep a bad, incomplete, or inauthentic CSV off the platform are pinned here in two layers:

* the cheap, well-messaged STRUCTURAL checks (`structural_problems`) — headers, non-empty,
  declaration-only identity, per-table grain, the ADR-001 `reproduces_recorded` dual-run gate, and
  product/category coherence; and
* the AUTHORITY (`canonical_equivalence_problems`) — the candidate must be byte-for-byte the trace
  this repository's builder produces at the current commit, which is the only thing that proves
  complete population and an authentic identity. A truncated-but-consistent subset, or a fabricated
  constant id, passes the structural checks and is caught here.

The `--plan`/`--dry-run` no-write promise and the immutable rollback archive (in its own
subdirectory, never the evaluation publisher's) are pinned too.
"""

import csv
import shutil
import sys

import pytest

import build.publish_evaluation as PE
import build.publish_registry as PR
import build.publish_scoring_trace as P


def _write_csv(path, header, rows):
    lines = [",".join(header)] + [",".join(str(c) for c in r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# One tiny, internally-consistent trace: a single scored product reproducing its recorded score,
# with a matching fact and rule-match row, all under one declaration identity. It passes the
# STRUCTURAL checks — and is exactly the truncated subset canonical equivalence must reject.
DVID = "d" * 64
SHA = "f012d854eb87"


def _synthetic_candidates(out_dir):
    def row(table, **over):
        base = {"declaration_version_id": DVID, "source_git_sha": SHA,
                "product_slug": "p", "category_slug": "c", "product_type": "model", "axis": "openness"}
        base.update(over)
        return [base[c] if base.get(c) is not None else "" for c in P.EXPECTED_HEADERS[table]]

    _write_csv(out_dir / "axis_facts.csv", P.EXPECTED_HEADERS["axis_facts"], [row(
        "axis_facts", dimension="weights", part_index=0, fact_kind="dimension",
        recorded_key="weights", recorded_value="open", normalized_value="open", in_declared_enum="True")])
    _write_csv(out_dir / "axis_rule_matches.csv", P.EXPECTED_HEADERS["axis_rule_matches"], [row(
        "axis_rule_matches", rule_index=0, rule_kind="when", outcome="fired", matched="True",
        non_tier_matched="True", tests_license_tier="False", wanted_tier="", rule_conditions="weights=open",
        result_score=4, result_class="open")])
    _write_csv(out_dir / "axis_results.csv", P.EXPECTED_HEADERS["axis_results"], [row(
        "axis_results", status="scored", result_score=4, result_class="open", matched_rule_index=0,
        matched_rule_kind="when", has_license_tiers="False", license_tier="", raw_license="MIT",
        recorded_score=4, recorded_class="open", reproduces_recorded="True", rule_count=1, deferral_reason="")])


def test_trace_tables_are_the_three_outputs():
    assert P.TRACE_TABLES == ("axis_facts", "axis_rule_matches", "axis_results")


# --- structural checks (well-messaged, not the authority) ------------------------


def test_synthetic_candidate_passes_the_structural_checks(tmp_path):
    _synthetic_candidates(tmp_path)
    assert P.structural_problems(tmp_path) == []


def test_arbitrary_headers_are_rejected(tmp_path):
    for t in P.TRACE_TABLES:
        _write_csv(tmp_path / f"{t}.csv", ["x", "y"], [[1, 2]])
    assert any("header does not match" in p for p in P.structural_problems(tmp_path))


def test_empty_table_is_rejected(tmp_path):
    _synthetic_candidates(tmp_path)
    header = (tmp_path / "axis_facts.csv").read_text().splitlines()[0]
    (tmp_path / "axis_facts.csv").write_text(header + "\n", encoding="utf-8")
    assert any("empty" in p for p in P.structural_problems(tmp_path))


def test_inconsistent_identity_within_a_file_is_rejected(tmp_path):
    _synthetic_candidates(tmp_path)
    path = tmp_path / "axis_facts.csv"
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[1] = "deadbeefcafe"  # source_git_sha column
    path.write_text("\n".join(lines + [",".join(row)]) + "\n", encoding="utf-8")
    assert any("source_git_sha" in p for p in P.structural_problems(tmp_path))


def test_identity_differing_across_files_is_rejected(tmp_path):
    _synthetic_candidates(tmp_path)
    path = tmp_path / "axis_results.csv"
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[0] = "e" * 64  # a different declaration_version_id than facts/rules carry
    lines[1] = ",".join(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("declaration_version_id" in p for p in P.structural_problems(tmp_path))


def test_a_scored_row_that_does_not_reproduce_is_rejected(tmp_path):
    """The ADR-001 dual-run gate: a scored result must reproduce the recorded score."""
    _synthetic_candidates(tmp_path)
    path = tmp_path / "axis_results.csv"
    header = P.EXPECTED_HEADERS["axis_results"]
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[header.index("reproduces_recorded")] = "False"
    lines[1] = ",".join(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("reproduce" in p for p in P.structural_problems(tmp_path))


def test_a_deferred_row_with_blank_reproduces_is_fine(tmp_path):
    """Deferred results carry an empty reproduces_recorded and must NOT trip the dual-run gate."""
    _synthetic_candidates(tmp_path)
    path = tmp_path / "axis_results.csv"
    header = P.EXPECTED_HEADERS["axis_results"]
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[header.index("status")] = "deferred"
    row[header.index("reproduces_recorded")] = ""
    row[header.index("deferral_reason")] = "no_recipe"
    lines[1] = ",".join(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert P.structural_problems(tmp_path) == []


def test_grain_uniqueness_is_enforced(tmp_path):
    _synthetic_candidates(tmp_path)
    path = tmp_path / "axis_results.csv"
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines + [lines[1]]) + "\n", encoding="utf-8")  # duplicate the one result
    assert any("grain" in p for p in P.structural_problems(tmp_path))


def test_a_fact_with_no_result_row_is_rejected(tmp_path):
    _synthetic_candidates(tmp_path)
    path = tmp_path / "axis_facts.csv"
    lines = path.read_text().splitlines()
    row = lines[1].split(",")
    row[2] = "orphan"  # product_slug not present in axis_results
    path.write_text("\n".join(lines + [",".join(row)]) + "\n", encoding="utf-8")
    assert any("no axis_results row" in p for p in P.structural_problems(tmp_path))


# --- canonical equivalence: the authority (built from the REAL builder) ----------


@pytest.fixture(scope="module")
def real_dir(tmp_path_factory):
    """The genuine trace this repository produces, written once through the real writer.

    allow_dirty=True so the fixture is independent of the working-tree state during development;
    every canonical check below reruns the builder with the same flag, so the identities agree.
    """
    from build.axis_scoring_trace import TABLES as SPEC
    from build.axis_scoring_trace import resolve
    from build.serialize_registry import write_tables

    out = tmp_path_factory.mktemp("real-trace")
    write_tables(resolve(allow_dirty=True), out, SPEC)
    return out


def _copy_real(real_dir, dest):
    for table in P.TRACE_TABLES:
        shutil.copy(real_dir / f"{table}.csv", dest / f"{table}.csv")
    return dest


def _rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def _write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)


def test_the_real_builder_output_passes_full_validation(real_dir):
    assert P.validate_candidates(real_dir, allow_dirty=True) == []


def test_a_truncated_but_consistent_candidate_is_rejected(tmp_path):
    """The headline: the tiny 1/1/1 subset that passes every structural check is NOT publishable."""
    _synthetic_candidates(tmp_path)
    assert P.structural_problems(tmp_path) == []
    problems = P.validate_candidates(tmp_path, allow_dirty=True)
    assert any("canonical trace" in p for p in problems)


def test_an_omitted_result_row_is_rejected(real_dir, tmp_path):
    d = _copy_real(real_dir, tmp_path)
    rows = _rows(d / "axis_results.csv")
    _write_rows(d / "axis_results.csv", rows[:-1])  # drop one real result
    assert any("axis_results" in p and "missing" in p
               for p in P.canonical_equivalence_problems(d, allow_dirty=True))


def test_an_omitted_fact_is_rejected(real_dir, tmp_path):
    d = _copy_real(real_dir, tmp_path)
    rows = _rows(d / "axis_facts.csv")
    _write_rows(d / "axis_facts.csv", rows[:-1])
    assert any("axis_facts" in p and "missing" in p
               for p in P.canonical_equivalence_problems(d, allow_dirty=True))


def test_an_omitted_rule_match_is_rejected(real_dir, tmp_path):
    d = _copy_real(real_dir, tmp_path)
    rows = _rows(d / "axis_rule_matches.csv")
    _write_rows(d / "axis_rule_matches.csv", rows[:-1])
    assert any("axis_rule_matches" in p and "missing" in p
               for p in P.canonical_equivalence_problems(d, allow_dirty=True))


def test_a_fabricated_but_constant_identity_is_rejected(real_dir, tmp_path):
    """A constant declaration_version_id passes the structural identity check but is not authentic."""
    d = _copy_real(real_dir, tmp_path)
    for table in P.TRACE_TABLES:
        rows = _rows(d / f"{table}.csv")
        col = rows[0].index("declaration_version_id")
        for row in rows[1:]:
            row[col] = "f" * 64
        _write_rows(d / f"{table}.csv", rows)
    assert P.structural_problems(d) == []           # constant + equal across files: structurally fine
    assert P.canonical_equivalence_problems(d, allow_dirty=True)  # but not this repository's id


def test_a_changed_value_with_valid_grain_and_flags_is_rejected(real_dir, tmp_path):
    """A tampered non-grain value, grain and reproduces_recorded left intact, is caught by canonical."""
    d = _copy_real(real_dir, tmp_path)
    rows = _rows(d / "axis_results.csv")
    col = rows[0].index("raw_license")
    rows[1][col] = (rows[1][col] or "X") + "-tampered"
    _write_rows(d / "axis_results.csv", rows)
    assert P.structural_problems(d) == []
    assert any("axis_results" in p for p in P.canonical_equivalence_problems(d, allow_dirty=True))


def test_canonical_rebuild_over_a_dirty_tree_without_allow_dirty_is_reported(real_dir, tmp_path, monkeypatch):
    """If the builder cannot produce a reproducible id (dirty tree, no opt-in), that is a problem,
    not a crash — so a candidate is never published against an unrebuildably-dirty repo."""
    d = _copy_real(real_dir, tmp_path)

    def _raise(root, allow_dirty=False):
        raise RuntimeError("DirtyWorktreeError: HEAD disagrees with the worktree")

    monkeypatch.setattr("build.axis_scoring_trace.resolve", _raise)
    problems = P.canonical_equivalence_problems(d, allow_dirty=False)
    assert any("clean commit" in p for p in problems)


# --- --plan / --dry-run write nothing (canonical authority stubbed) --------------
# These exercise the no-write / no-mutation mechanics, not authenticity, so the repo rebuild is
# stubbed and the structural checks still run over the synthetic candidate.


def test_plan_validates_offline_and_writes_nothing(tmp_path, monkeypatch):
    _synthetic_candidates(tmp_path)
    monkeypatch.setattr(P, "canonical_equivalence_problems", lambda *a, **k: [])

    def _no_network(*a, **k):
        raise AssertionError("--plan must not hit the network")

    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--plan", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])
    before = set(tmp_path.iterdir())
    assert P.main() == 0
    assert set(tmp_path.iterdir()) == before


def test_dry_run_with_credentials_makes_no_mutation_and_no_write(tmp_path, monkeypatch):
    _synthetic_candidates(tmp_path)
    monkeypatch.setattr(P, "canonical_equivalence_problems", lambda *a, **k: [])
    monkeypatch.setenv("OSO_API_KEY", "test-token")
    monkeypatch.setenv("OSO_ORG_ID", "test-org")

    def fake_graphql(query, variables, token):
        if "datasets(" in query:
            return {"datasets": {"edges": [{"node": {"id": "ds1", "name": "evaluation"}}]}}
        if "staticModels(" in query:
            return {"staticModels": {"edges": []}}
        raise AssertionError(f"a dry run must issue no mutation, got: {query[:48]}")

    monkeypatch.setattr(P, "graphql", fake_graphql)
    monkeypatch.setattr(PR, "graphql", fake_graphql)
    monkeypatch.setattr(PE, "graphql", fake_graphql)  # resolve_evaluation_dataset uses PE's graphql
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dry-run", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])
    before = set(tmp_path.iterdir())
    assert P.main() == 0
    assert set(tmp_path.iterdir()) == before
    assert not (tmp_path / "archive").exists()  # a dry run writes no archive and no occurrence log


def test_publish_without_credentials_refuses(tmp_path, monkeypatch):
    _synthetic_candidates(tmp_path)
    monkeypatch.setattr(P, "canonical_equivalence_problems", lambda *a, **k: [])
    monkeypatch.delenv("OSO_API_KEY", raising=False)
    monkeypatch.delenv("OSO_ORG_ID", raising=False)

    def _no_network(*a, **k):
        raise AssertionError("must not hit the network without credentials")

    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dry-run", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])
    assert P.main() == 2


def test_missing_csv_is_a_loud_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--plan", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])
    assert P.main() == 2


# --- per-model run requests, exact-group polling, fail-fast (validation stubbed) --


def _platform_graphql(requested):
    def fake_graphql(query, variables, token):
        if query is PE.Q_DATASETS or "datasets(" in query:
            return {"datasets": {"edges": [{"node": {"id": "ds-eval", "name": "evaluation",
                                                     "type": "STATIC_MODEL"}}]}}
        if query is PR.Q_STATIC or "staticModels(" in query:
            return {"staticModels": {"edges": [
                {"node": {"id": f"id-{t}", "name": t, "materializations": {"totalCount": 1}}}
                for t in P.TRACE_TABLES
            ]}}
        if query is P.M_URL:
            return {"createStaticModelUploadUrl": "https://upload.example/put"}
        if query is P.M_RUN:
            requested.append(variables["input"])
            return {"createStaticModelRunRequest":
                    {"runGroup": {"id": f"grp-for-{variables['input']['staticModelId']}", "status": "QUEUED"}}}
        raise AssertionError(f"unexpected query: {query[:60]}")
    return fake_graphql


def _wire(monkeypatch, requested):
    fake = _platform_graphql(requested)
    monkeypatch.setattr(P, "canonical_equivalence_problems", lambda *a, **k: [])
    monkeypatch.setattr(P, "graphql", fake)
    monkeypatch.setattr(PR, "graphql", fake)
    monkeypatch.setattr(PE, "graphql", fake)
    monkeypatch.setattr(PE, "upload", lambda path, url: None)
    monkeypatch.setenv("OSO_API_KEY", "tok")
    monkeypatch.setenv("OSO_ORG_ID", "org")


def test_load_run_is_requested_once_per_model_with_static_model_id(tmp_path, monkeypatch):
    _synthetic_candidates(tmp_path)
    requested: list[dict] = []
    _wire(monkeypatch, requested)
    monkeypatch.setattr(PE, "poll_run_group", lambda gid, token, timeout=1800.0: "SUCCESS")
    monkeypatch.setattr(PE, "deployed_table_state", lambda dataset, table: {"rows": 0, "columns": []})
    monkeypatch.setattr(P, "deployment_mismatches", lambda expected, deployed: ["stop here"])
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])

    assert P.main() == 2  # stopped at the injected mismatch, after all three runs were requested
    assert len(requested) == len(P.TRACE_TABLES), "one run request per model"
    for payload in requested:
        assert payload["datasetId"] == "ds-eval"
        assert "selectedModels" not in payload
    assert [pl["staticModelId"] for pl in requested] == [f"id-{t}" for t in P.TRACE_TABLES]


def test_the_publisher_polls_the_exact_run_group_the_mutation_returned(tmp_path, monkeypatch):
    _synthetic_candidates(tmp_path)
    requested: list[dict] = []
    polled: list[str] = []
    _wire(monkeypatch, requested)

    def record_poll(gid, token, timeout=1800.0):
        polled.append(gid)
        return "SUCCESS"

    monkeypatch.setattr(PE, "poll_run_group", record_poll)
    monkeypatch.setattr(PE, "deployed_table_state", lambda dataset, table: {"rows": 0, "columns": []})
    monkeypatch.setattr(P, "deployment_mismatches", lambda expected, deployed: ["stop here"])
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])

    assert P.main() == 2
    assert polled == [f"grp-for-id-{t}" for t in P.TRACE_TABLES]


def test_a_failed_run_stops_the_deploy_before_the_next_model(tmp_path, monkeypatch):
    _synthetic_candidates(tmp_path)
    requested: list[dict] = []
    _wire(monkeypatch, requested)
    monkeypatch.setattr(PE, "poll_run_group", lambda gid, token, timeout=1800.0: "FAILED")

    def boom(dataset, table):
        raise AssertionError("must not read deployed state when a run failed")

    monkeypatch.setattr(PE, "deployed_table_state", boom)
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--dir", str(tmp_path), "--archive-root", str(tmp_path / "archive")])

    assert P.main() == 2
    assert len(requested) == 1, "the second model is not requested after the first fails"
    assert P.archive.current_live(tmp_path / "archive") is None, "a failed deploy records no occurrence"


# --- the deployed-schema comparison and the immutable archive --------------------


def test_deployment_mismatches_catches_row_and_schema_drift():
    expected = {t: {"rows": 3, "columns": ["a", "b"], "all_null_columns": []} for t in P.TRACE_TABLES}
    deployed = {t: {"rows": 3, "columns": ["a", "b"]} for t in P.TRACE_TABLES}
    assert P.deployment_mismatches(expected, deployed) == []
    wrong_rows = {**deployed, "axis_facts": {"rows": 2, "columns": ["a", "b"]}}
    assert any("rows" in m for m in P.deployment_mismatches(expected, wrong_rows))
    wrong_cols = {**deployed, "axis_results": {"rows": 3, "columns": ["a"]}}
    assert any("columns" in m for m in P.deployment_mismatches(expected, wrong_cols))


def test_ensure_artifact_writes_a_verifiable_content_addressed_archive(tmp_path):
    _synthetic_candidates(tmp_path)
    root = tmp_path / "archive"
    aid = P.archive.ensure_artifact(root, P.archived_files(tmp_path), P.build_receipt(tmp_path), P.deployment_id(tmp_path))
    adir = P.archive.artifact_dir(root, aid)
    assert adir.name == aid
    for table in P.TRACE_TABLES:
        assert (adir / f"{table}.csv").exists()
    assert (adir / P.archive.RECEIPT).exists() and (adir / P.archive.SHA256SUMS).exists()
    P.archive.verify_artifact(root, aid)
    assert P.archive.current_live(root) is None  # ensure_artifact alone records no occurrence


def test_stage_artifact_persists_locally_and_touches_no_network(tmp_path, monkeypatch):
    _synthetic_candidates(tmp_path)
    root = tmp_path / "archive"

    def _no_network(*a, **k):
        raise AssertionError("--stage-artifact must not touch OSO")

    monkeypatch.setattr(P, "canonical_equivalence_problems", lambda *a, **k: [])  # tested elsewhere
    monkeypatch.setattr(P, "graphql", _no_network)
    monkeypatch.setattr(P, "resolve_evaluation_dataset", _no_network)
    monkeypatch.delenv("OSO_API_KEY", raising=False)
    monkeypatch.delenv("OSO_ORG_ID", raising=False)
    monkeypatch.setattr(sys, "argv",
                        ["publish_scoring_trace", "--stage-artifact", "--dir", str(tmp_path), "--archive-root", str(root)])
    assert P.main() == 0
    aid = P.archive.artifact_id(P.archived_files(tmp_path))
    P.archive.verify_artifact(root, aid)
    assert P.archive.current_live(root) is None, "staging records no occurrence"


def test_deploy_artifact_deploys_the_archived_bytes_bound_to_the_id(tmp_path, monkeypatch):
    """`--deploy-artifact <id>` re-uploads the archived artifact's exact bytes and records a deploy of
    that id, reading the archive and never `--dir`."""
    _synthetic_candidates(tmp_path)
    root = tmp_path / "archive"
    aid = P.archive.ensure_artifact(root, P.archived_files(tmp_path), P.build_receipt(tmp_path),
                                    P.deployment_id(tmp_path))
    tables = P.archive.artifact_receipt(root, aid)["tables"]
    deployed = {t: {"rows": tables[t]["rows"], "columns": tables[t]["columns"]} for t in P.TRACE_TABLES}
    for t in P.TRACE_TABLES:
        (tmp_path / f"{t}.csv").unlink()  # the deploy must not depend on --dir

    requested: list[dict] = []
    _wire(monkeypatch, requested)
    monkeypatch.setattr(PE, "poll_run_group", lambda gid, token, timeout=1800.0: "SUCCESS")
    monkeypatch.setattr(PE, "deployed_table_state", lambda dataset, table: deployed[table])
    uploaded: dict[str, bytes] = {}
    monkeypatch.setattr(PE, "upload",
                        lambda path, url: uploaded.__setitem__(P.Path(path).name, P.Path(path).read_bytes()))
    monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--deploy-artifact", aid, "--archive-root", str(root)])

    assert P.main() == 0
    occ = P.archive.occurrences(root)
    assert [o["operation"] for o in occ] == ["deploy"]
    assert occ[0]["artifact_id"] == aid
    adir = P.archive.artifact_dir(root, aid)
    for t in P.TRACE_TABLES:
        assert uploaded[f"{t}.csv"] == (adir / f"{t}.csv").read_bytes()


def test_artifact_modes_are_mutually_exclusive(tmp_path, monkeypatch):
    ar = str(tmp_path / "archive")
    for extra in (["--rollback", "x"], ["--deploy-artifact", "y"]):
        monkeypatch.setattr(sys, "argv", ["publish_scoring_trace", "--stage-artifact", *extra, "--archive-root", ar])
        assert P.main() == 2
    monkeypatch.setattr(sys, "argv",
                        ["publish_scoring_trace", "--deploy-artifact", "y", "--rollback", "x", "--archive-root", ar])
    assert P.main() == 2


def test_stage_artifact_with_dry_run_is_rejected_and_writes_nothing(tmp_path, monkeypatch):
    _synthetic_candidates(tmp_path)
    root = tmp_path / "archive"
    monkeypatch.setattr(sys, "argv",
                        ["publish_scoring_trace", "--stage-artifact", "--dry-run", "--dir", str(tmp_path),
                         "--archive-root", str(root)])
    assert P.main() == 2
    assert not root.exists()


def test_the_trace_archive_root_is_its_own_never_the_evaluation_publishers(tmp_path):
    # Default archive roots are distinct, so neither publisher reads the other's archives.
    assert P.DEFAULT_ARCHIVE_ROOT.name == "scoring-trace-deployments"
    assert P.DEFAULT_ARCHIVE_ROOT != PE.DEFAULT_ARCHIVE_ROOT
