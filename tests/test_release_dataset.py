"""The release tool's two rules: history is staged forwards-only or not at all, and a commit
releases exactly the candidate that was reviewed. Offline; the platform is a fake."""

from build import release_dataset as R


def _revision(rid, kind="FULL", number=1, **options):
    return {"id": rid, "revisionNumber": number, "kind": kind, "kindOptions": options or None}


def _model(name, latest, released=None, enabled=True):
    return {"id": f"m-{name}", "name": name, "isEnabled": enabled, "latestRevision": latest,
            "latestRelease": {"revision": released} if released else None}


HISTORY = dict(kind="INCREMENTAL_BY_UNIQUE_KEY", uniqueKeyColumns=["repo", "observed_date"])


def _candidate(cid="c1", status="OPEN", check="SUCCESS", blockers=(), revisions=(("a", "r2", "AUTHOR"),)):
    return {"id": cid, "status": status, "description": "d", "createdAt": "2026-11-21T20:10:00Z",
            "commitBlockers": list(blockers), "latestCheck": {"status": check} if check else None,
            "revisions": [{"source": source, "dataModel": {"id": f"m-{name}", "name": name},
                           "revision": {"id": rid, "revisionNumber": 2}} for name, rid, source in revisions]}


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
    assert "not run" in R.commit_problems(_candidate(check=None), "c1", digest)[0]
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


def test_stage_sends_forwards_only_and_prints_the_commit_command(capsys):
    models = [_model("h", _revision("r2", number=2, **HISTORY), released=_revision("r1", **HISTORY))]
    pending = _candidate(revisions=(("h", "r2", "AUTHOR"),))
    platform = FakePlatform(models, pending)
    assert R.main(["stage", "obs", "--model", "h", "--description", "add nothing"], platform=platform) == 0
    ((field, payload),) = platform.mutations
    assert field == "stageDatasetRelease" and payload["revisions"][0]["forwardsOnly"] is True
    out = capsys.readouterr().out
    assert "forwards-only: h" in out
    assert f"commit obs --candidate c1 --digest {R.candidate_digest(pending)}" in out


def test_a_refused_stage_calls_nothing(capsys):
    models = [_model("h", _revision("r2", kind="FULL"), released=_revision("r1", **HISTORY))]
    platform = FakePlatform(models)
    assert R.main(["stage", "obs", "--model", "h"], platform=platform) == 2
    assert platform.mutations == [] and "would rebuild it from its start" in capsys.readouterr().err


def test_a_stage_whose_check_fails_exits_nonzero():
    models = [_model("a", _revision("r2"), released=_revision("r1"))]
    platform = FakePlatform(models, _candidate(check="FAILED", blockers=["CHECK_FAILED"]))
    assert R.main(["stage", "obs", "--model", "a"], platform=platform) == 1


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
