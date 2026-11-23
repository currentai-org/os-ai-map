"""The release tool's two rules: history is staged forwards-only or not at all, and a commit
releases exactly the candidate that was reviewed. Offline; the platform is a fake."""

import json

from build import release_dataset as R


STORED = (("repo", "VARCHAR"), ("observed_date", "DATE"), ("stars", "BIGINT"))


def _columns(pairs):
    return None if pairs is None else [{"name": name, "type": kind} for name, kind in pairs]


def _revision(rid, kind="FULL", number=1, stored=STORED, **options):
    return {"id": rid, "revisionNumber": number, "kind": kind, "kindOptions": options or None,
            "storageSchema": _columns(stored)}


def _model(name, latest, released=None, enabled=True):
    return {"id": f"m-{name}", "name": name, "isEnabled": enabled, "latestRevision": latest,
            "latestRelease": {"revision": released} if released else None}


HISTORY = dict(kind="INCREMENTAL_BY_UNIQUE_KEY", uniqueKeyColumns=["repo", "observed_date"])


def _candidate(cid="c1", status="OPEN", check="SUCCESS", blockers=(), revisions=(("a", "r2", "AUTHOR"),),
               check_id="k1", base="rel-0", classifications=(), model_classification=None,
               schema=(("id", "VARCHAR"),), stored=STORED):
    return {"id": cid, "status": status, "description": "d", "createdAt": "2026-11-21T20:10:00Z",
            "commitBlockers": list(blockers), "baseRelease": {"id": base} if base else None,
            "latestCheck": {"id": check_id, "status": check} if check else None,
            "revisions": [{"source": source, "dataModel": {"id": f"m-{name}", "name": name},
                           "revision": {"id": rid, "revisionNumber": 2},
                           "schema": _columns(schema), "storageSchema": _columns(stored),
                           "modelClassification": model_classification,
                           "columnClassifications": [{"columnName": c, "classification": k, "source": src}
                                                     for c, k, src in classifications]}
                          for name, rid, source in revisions]}


# --- history is released forwards-only -------------------------------------------------------------


def test_a_recomputed_model_is_staged_plainly():
    models = [_model("a", _revision("r2", number=2), released=_revision("r1"))]
    entries, problems = R.stage_entries(models, {"a": None}, {})
    assert problems == []
    assert entries == [{"dataModelId": "m-a", "dataModelRevisionId": "r2"}]


def test_a_history_model_is_always_staged_forwards_only():
    models = [_model("h", _revision("r2", number=2, **HISTORY), released=_revision("r1", **HISTORY))]
    entries, problems = R.stage_entries(models, {"h": None}, {"h": {"stars": "0", "note": None}})
    assert problems == []
    assert entries == [{"dataModelId": "m-h", "dataModelRevisionId": "r2", "forwardsOnly": True,
                        "forwardsOnlyDefaults": [{"columnName": "note", "value": None},
                                                 {"columnName": "stars", "value": "0"}]}]


def test_a_history_model_changing_kind_is_refused():
    models = [_model("h", _revision("r2", kind="FULL"), released=_revision("r1", **HISTORY))]
    entries, problems = R.stage_entries(models, {"h": None}, {})
    assert entries == []
    assert "would rebuild it from its start" in problems[0] and "INCREMENTAL_BY_UNIQUE_KEY to FULL" in problems[0]


def test_a_history_model_changing_its_row_key_is_refused():
    rekeyed = dict(HISTORY, uniqueKeyColumns=["repo"])
    models = [_model("h", _revision("r2", **rekeyed), released=_revision("r1", **HISTORY))]
    entries, problems = R.stage_entries(models, {"h": None}, {})
    assert entries == [] and "uniqueKeyColumns changes" in problems[0]


def test_one_refusal_stages_nothing_at_all():
    models = [_model("a", _revision("r2"), released=_revision("r1")),
              _model("h", _revision("r2", kind="FULL"), released=_revision("r1", **HISTORY))]
    entries, problems = R.stage_entries(models, {"a": None, "h": None}, {})
    assert entries == [] and len(problems) == 1


def test_a_first_release_of_an_incremental_model_has_no_history_to_protect():
    models = [_model("h", _revision("r1", **HISTORY))]
    entries, problems = R.stage_entries(models, {"h": None}, {})
    assert problems == [] and "forwardsOnly" not in entries[0]


def test_becoming_incremental_is_not_a_history_rebuild():
    models = [_model("h", _revision("r2", **HISTORY), released=_revision("r1"))]
    entries, problems = R.stage_entries(models, {"h": None}, {})
    assert problems == [] and "forwardsOnly" not in entries[0]


def test_only_the_latest_revision_can_be_staged():
    models = [_model("a", _revision("r3", number=3), released=_revision("r1"))]
    _entries, problems = R.stage_entries(models, {"a": "r2"}, {})
    assert "is not its latest revision" in problems[0]
    entries, problems = R.stage_entries(models, {"a": "r3"}, {})
    assert problems == [] and entries[0]["dataModelRevisionId"] == "r3"


def test_unknown_disabled_and_already_released_models_are_refused():
    released = _revision("r1")
    models = [_model("off", _revision("r2"), released=released, enabled=False), _model("same", released, released=released)]
    _entries, problems = R.stage_entries(models, {"ghost": None, "off": None, "same": None}, {})
    assert [p.split(":")[0] for p in problems] == ["ghost", "off", "same"]
    assert "--refresh" in problems[2]


def test_added_columns_need_a_history_model_that_is_being_released():
    models = [_model("a", _revision("r2"), released=_revision("r1"))]
    _entries, problems = R.stage_entries(models, {"a": None}, {"a": {"x": None}, "b": {"y": None}})
    assert any(p.startswith("b: added columns were given") for p in problems)
    assert any(p.startswith("a: added columns apply only") for p in problems)


def test_a_history_model_cannot_be_re_locked():
    models = [_model("a", _revision("r1"), released=_revision("r1")),
              _model("h", _revision("r1", **HISTORY), released=_revision("r1", **HISTORY))]
    assert R.refresh_ids(models, ["a"]) == (["m-a"], [])
    ids, problems = R.refresh_ids(models, ["a", "h", "ghost"])
    assert ids == [] and len(problems) == 2 and "cannot be sent forwards-only" in problems[0]


# --- a commit names the candidate that was reviewed ------------------------------------------------


def test_the_digest_follows_what_the_candidate_releases_and_not_its_order():
    one = _candidate(revisions=(("a", "r2", "AUTHOR"), ("b", "r5", "AUTO")))
    same = _candidate(revisions=(("b", "r5", "AUTO"), ("a", "r2", "AUTHOR")))
    other = _candidate(revisions=(("a", "r3", "AUTHOR"), ("b", "r5", "AUTO")))
    assert R.candidate_digest(one) == R.candidate_digest(same) != R.candidate_digest(other)


def test_the_digest_covers_every_release_decision_the_platform_reports():
    """Same models at the same revisions is not the same release: the `scores` repair turned on
    the BREAKING classification of its removed columns."""
    reviewed = R.candidate_digest(_candidate())
    changed = [
        _candidate(classifications=(("old_col", "BREAKING", "AUTHOR"),)),
        _candidate(model_classification="BREAKING"),
        _candidate(schema=(("id", "BIGINT"),)),
        _candidate(schema=None),
        _candidate(base="rel-9"),
        _candidate(stored=STORED[:2]),
        _candidate(check_id="k2"),
        _candidate(revisions=(("a", "r2", "AUTO"),)),
    ]
    digests = {R.candidate_digest(c) for c in changed}
    assert reviewed not in digests and len(digests) == len(changed)
    author = _candidate(classifications=(("c", "ADDITIVE", "AUTHOR"),))
    auto = _candidate(classifications=(("c", "ADDITIVE", "AUTO"),))
    assert R.candidate_digest(author) != R.candidate_digest(auto)


def test_the_digest_does_not_claim_forwards_only():
    assert "forwardsOnly" not in json.dumps(R.reviewed_content(_candidate()))


def test_a_classification_changed_after_review_does_not_commit():
    reviewed = R.candidate_digest(_candidate(classifications=(("old_col", "BREAKING", "AUTHOR"),)))
    (problem,) = R.commit_problems(_candidate(), "c1", reviewed)
    assert "now releases something else" in problem


# --- a stored column removed or retyped rebuilds the table, and the platform does not refuse it ------


def _history_models():
    return [_model("h", _revision("r2", number=2, **HISTORY), released=_revision("r1", **HISTORY)),
            _model("a", _revision("r2"), released=_revision("r1"))]


def test_a_history_model_that_keeps_and_adds_columns_is_fine():
    candidate = _candidate(revisions=(("h", "r2", "AUTHOR"),), stored=STORED + (("forks", "BIGINT"),))
    assert R.history_schema_problems(candidate, _history_models()) == []
    renamed_case = _candidate(revisions=(("h", "r2", "AUTHOR"),), stored=(("REPO", "VARCHAR"),) + STORED[1:])
    assert R.history_schema_problems(renamed_case, _history_models()) == []


def test_a_removed_stored_column_is_a_history_rebuild():
    candidate = _candidate(revisions=(("h", "r2", "AUTHOR"),), stored=STORED[:2])
    (problem,) = R.history_schema_problems(candidate, _history_models())
    assert "would rebuild it from its start" in problem and "removes stars" in problem


def test_a_retyped_stored_column_is_a_history_rebuild():
    candidate = _candidate(revisions=(("h", "r2", "AUTHOR"),), stored=STORED[:2] + (("stars", "VARCHAR"),))
    (problem,) = R.history_schema_problems(candidate, _history_models())
    assert "retypes stars BIGINT -> VARCHAR" in problem


def test_an_unresolved_schema_cannot_show_the_columns_are_kept():
    candidate = _candidate(revisions=(("h", "r2", "AUTHOR"),), stored=None)
    assert "staged schema is not resolved" in R.history_schema_problems(candidate, _history_models())[0]


def test_a_recomputed_model_may_drop_a_column():
    candidate = _candidate(revisions=(("a", "r2", "AUTHOR"),), stored=STORED[:1])
    assert R.history_schema_problems(candidate, _history_models()) == []


def test_a_candidate_that_rebuilds_history_gets_no_commit_command_and_is_not_committed(capsys, tmp_path):
    models = _history_models()
    pending = _candidate(revisions=(("h", "r2", "AUTHOR"),), stored=STORED[:2])
    platform = FakePlatform(models, pending)
    assert R.main(["stage", "obs", "--model", "h", "--records-dir", str(tmp_path)], platform=platform) == 1
    out = capsys.readouterr().out
    assert "removes stars" in out and "to commit exactly this" not in out
    record = tmp_path / "obs.c1.json"
    assert R.main(["commit", "obs", "--candidate", "c1", "--digest", R.candidate_digest(pending),
                   "--stage-record", str(record)], platform=platform) == 2
    assert [field for field, _payload in platform.mutations] == ["stageDatasetRelease"]
    assert R.main(["status", "obs"], platform=platform) == 0
    assert "not committable with this tool" in capsys.readouterr().out


# --- forwards-only cannot be read back, so a history release needs the stage record ------------------


def _history_setup():
    models = [_model("h", _revision("r2", number=2, **HISTORY), released=_revision("r1", **HISTORY)),
              _model("a", _revision("r2"), released=_revision("r1"))]
    candidate = _candidate(revisions=(("a", "r2", "AUTHOR"), ("h", "r2", "AUTHOR")))
    payload = {"datasetId": "ds-1", "revisions": [
        {"dataModelId": "m-a", "dataModelRevisionId": "r2"},
        {"dataModelId": "m-h", "dataModelRevisionId": "r2", "forwardsOnly": True, "forwardsOnlyDefaults": []}]}
    return models, candidate, payload


def test_a_candidate_without_history_models_needs_no_record():
    models, _candidate_, _payload = _history_setup()
    assert R.record_problems(None, _candidate(), models, "obs", "d") == []


def test_a_history_release_is_not_committed_without_its_stage_record():
    models, candidate, _payload = _history_setup()
    (problem,) = R.record_problems(None, candidate, models, "obs", "d")
    assert "h, which keep history" in problem and "--stage-record" in problem


def test_the_record_of_the_stage_that_was_checked_is_accepted():
    models, candidate, payload = _history_setup()
    assert R.record_problems(R.stage_record("obs", candidate, payload), candidate, models, "obs",
                            R.candidate_digest(candidate)) == []


def test_a_record_from_an_earlier_stage_or_another_candidate_is_refused():
    models, candidate, payload = _history_setup()
    record = R.stage_record("obs", candidate, payload)
    restaged = dict(candidate, latestCheck={"id": "k2", "status": "SUCCESS"})
    assert "staged or checked again" in R.record_problems(record, restaged, models, "obs", record["digest"])[0]
    assert "not c2" in R.record_problems(record, dict(candidate, id="c2"), models, "obs", record["digest"])[0]


def test_a_record_that_did_not_send_forwards_only_is_refused():
    models, candidate, payload = _history_setup()
    payload["revisions"][1].pop("forwardsOnly")
    (problem,) = R.record_problems(R.stage_record("obs", candidate, payload), candidate, models, "obs",
                            R.candidate_digest(candidate))
    assert problem.startswith("h: keeps history")


def test_the_reviewed_candidate_commits():
    pending = _candidate()
    assert R.commit_problems(pending, "c1", R.candidate_digest(pending)) == []


def test_a_candidate_restaged_after_review_does_not_commit():
    reviewed = R.candidate_digest(_candidate())
    restaged = _candidate(revisions=(("a", "r9", "AUTHOR"),))
    (problem,) = R.commit_problems(restaged, "c1", reviewed)
    assert "now releases something else" in problem


def test_another_candidate_a_failed_check_and_a_blocker_each_stop_a_commit():
    pending = _candidate()
    digest = R.candidate_digest(pending)
    assert "not the reviewed c0" in R.commit_problems(pending, "c0", digest)[0]
    assert R.commit_problems(None, "c1", digest) == ["the dataset has no release candidate"]
    assert "is FAILED, not SUCCESS" in R.commit_problems(_candidate(check="FAILED"), "c1", digest)[0]
    unchecked = _candidate(check=None)
    assert any("not run" in problem for problem in R.commit_problems(unchecked, "c1", R.candidate_digest(unchecked)))
    assert "CHECK_OUT_OF_DATE" in R.commit_problems(_candidate(blockers=["CHECK_OUT_OF_DATE"]), "c1", digest)[0]
    closed = R.commit_problems(_candidate(status="COMMITTED", blockers=["NOT_OPEN"]), "c1", digest)
    assert "is COMMITTED, not OPEN" in closed[0]


# --- the commands, against a fake platform --------------------------------------------------------


class FakePlatform:
    def __init__(self, models, candidate=None):
        self._models, self._candidate, self.mutations = models, candidate, []

    def dataset_id(self, name):
        return "ds-1"

    def models(self, dataset_id):
        return self._models

    def candidate(self, dataset_id):
        return self._candidate

    def mutate(self, mutation, field, payload):
        self.mutations.append((field, payload))
        return {"success": True, "release": {"id": "rel-1"}}


def test_stage_sends_forwards_only_writes_its_record_and_the_commit_needs_it(capsys, tmp_path):
    models = [_model("h", _revision("r2", number=2, **HISTORY), released=_revision("r1", **HISTORY))]
    pending = _candidate(revisions=(("h", "r2", "AUTHOR"),))
    platform = FakePlatform(models, pending)
    assert R.main(["stage", "obs", "--model", "h", "--description", "add nothing",
                   "--records-dir", str(tmp_path)], platform=platform) == 0
    ((field, payload),) = platform.mutations
    assert field == "stageDatasetRelease" and payload["revisions"][0]["forwardsOnly"] is True
    out = capsys.readouterr().out
    record_path = tmp_path / "obs.c1.json"
    assert "forwards-only: h" in out and "keeps history" in out
    assert f"commit obs --candidate c1 --digest {R.candidate_digest(pending)} --stage-record {record_path}" in out
    record = json.loads(record_path.read_text())
    assert record["check_id"] == "k1" and record["payload"] == payload

    # The commit needs that record, and takes it.
    assert R.main(["commit", "obs", "--candidate", "c1", "--digest", R.candidate_digest(pending)], platform=platform) == 2
    assert len(platform.mutations) == 1
    assert R.main(["commit", "obs", "--candidate", "c1", "--digest", R.candidate_digest(pending),
                   "--stage-record", str(record_path)], platform=platform) == 0
    assert platform.mutations[-1] == ("commitDatasetRelease", {"candidateId": "c1"})


def test_a_refused_stage_calls_nothing(capsys):
    models = [_model("h", _revision("r2", kind="FULL"), released=_revision("r1", **HISTORY))]
    platform = FakePlatform(models)
    assert R.main(["stage", "obs", "--model", "h"], platform=platform) == 2
    assert platform.mutations == [] and "would rebuild it from its start" in capsys.readouterr().err


def test_a_stage_whose_check_fails_exits_nonzero(tmp_path):
    models = [_model("a", _revision("r2"), released=_revision("r1"))]
    platform = FakePlatform(models, _candidate(check="FAILED", blockers=["CHECK_FAILED"]))
    assert R.main(["stage", "obs", "--model", "a", "--records-dir", str(tmp_path)], platform=platform) == 1


def test_commit_releases_only_the_reviewed_candidate(capsys):
    pending = _candidate()
    platform = FakePlatform([], pending)
    assert R.main(["commit", "obs", "--candidate", "c1", "--digest", "0" * 64], platform=platform) == 2
    assert platform.mutations == []
    assert R.main(["commit", "obs", "--candidate", "c1", "--digest", R.candidate_digest(pending)], platform=platform) == 0
    assert platform.mutations == [("commitDatasetRelease", {"candidateId": "c1"})]
    assert "committed candidate c1 as release rel-1" in capsys.readouterr().out


def test_wait_for_check_polls_until_the_check_finishes():
    states = [_candidate(check="RUNNING"), _candidate(check="RUNNING"), _candidate(check="SUCCESS")]

    class Polled(FakePlatform):
        def candidate(self, dataset_id):
            return states.pop(0)

    slept = []
    done = R.wait_for_check(Polled([]), "ds-1", sleep=slept.append)
    assert done["latestCheck"]["status"] == "SUCCESS" and slept == [15.0, 15.0]


def test_a_commit_call_that_does_not_return_is_not_reported_as_a_failure_to_retry(capsys):
    pending = _candidate()

    class Slow(FakePlatform):
        def mutate(self, mutation, field, payload):
            raise TimeoutError("The read operation timed out")

    code = R.main(["commit", "obs", "--candidate", "c1", "--digest", R.candidate_digest(pending)], platform=Slow([], pending))
    err = capsys.readouterr().err
    assert code == 3
    assert "may still complete" in err and "Do not run commit again yet" in err and "status obs" in err


def test_platform_mutations_are_given_longer_than_a_read():
    seen = {}

    def call(query, variables, token, timeout=60.0):
        seen["timeout"] = timeout
        return {"commitDatasetRelease": {"success": True, "release": {"id": "rel-1"}}}

    R.Platform("t", "o", call=call).mutate(R.M_COMMIT, "commitDatasetRelease", {"candidateId": "c1"})
    assert seen["timeout"] == R.MUTATION_TIMEOUT > 60


# --- review of 2026-11-22: an out-of-date check, and a record bound to the reviewed stage ------------


def test_a_check_the_platform_calls_out_of_date_does_not_commit():
    pending = dict(_candidate(), latestCheckOutOfDate=True)
    (problem,) = R.commit_problems(pending, "c1", R.candidate_digest(pending))
    assert "out of date" in problem


def test_a_record_for_another_dataset_or_digest_is_refused():
    models, candidate, payload = _history_setup()
    record = R.stage_record("obs", candidate, payload)
    digest = R.candidate_digest(candidate)
    assert "dataset other" in " ".join(R.record_problems(dict(record, dataset="other"), candidate, models, "obs", digest))
    assert "not the reviewed" in " ".join(R.record_problems(record, candidate, models, "obs", "f" * 64))


def test_a_record_must_stage_exactly_what_the_candidate_releases():
    models, candidate, payload = _history_setup()
    digest = R.candidate_digest(candidate)
    other = json.loads(json.dumps(payload))
    other["revisions"][0]["dataModelRevisionId"] = "r9"
    problems = " ".join(R.record_problems(R.stage_record("obs", candidate, other), candidate, models, "obs", digest))
    assert "staged revisions the candidate does not release: m-a@r9" in problems
    assert "the candidate releases revisions the stage record did not stage: m-a@r2" in problems


def test_a_relocked_model_in_the_candidate_is_accounted_for_by_the_record():
    models, candidate, payload = _history_setup()
    candidate = dict(candidate, revisions=candidate["revisions"] + _candidate(revisions=(("b", "r5", "REFRESH"),))["revisions"])
    digest = R.candidate_digest(candidate)
    assert "did not stage: m-b@r5" in " ".join(
        R.record_problems(R.stage_record("obs", candidate, payload), candidate, models, "obs", digest))
    relock = dict(payload, refreshUpstream=["m-b"])
    assert R.record_problems(R.stage_record("obs", candidate, relock), candidate, models, "obs", digest) == []
