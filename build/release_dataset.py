"""Release a dataset's models on the versioned platform: stage a candidate, read it, commit it.

Maintainer tool. An editor session never runs `stage` or `commit`; see
`docs/operations/deploy-models.md`.

    uv run python -m build.release_dataset status scores
    uv run python -m build.release_dataset stage scores --model openness_facts --model openness_computed
    uv run python -m build.release_dataset commit scores --candidate <id> --digest <sha256>

In a versioned organization a model is released as part of a dataset release: `stage` opens or
updates the dataset's one pending candidate, the platform checks it, and `commit` releases it.
`createDataModelRelease` is refused there, so the one-model release the older runbooks describe
no longer exists.

Two rules are applied here. Each says below which part this tool checks itself and which part
it leaves to the platform.

**History is released forwards-only** (ruling R-2026-11-08-s). A model whose released kind is not
`FULL` or `VIEW` keeps rows that a later run adds to and cannot rebuild: the sources behind the
history tables report only their current state. A release that recomputes such a model rebuilds
it from its start and loses those rows for good.

- Checked here, before any call: every revision of such a model is staged with `forwardsOnly`,
  and no flag turns that off. A revision that changes the model's kind, unique key, time column
  or partition grain is refused. A re-lock (`--refresh`) of such a model is refused, because it
  cannot carry `forwardsOnly`.
- Checked here, once the platform has resolved the candidate: a stored column the candidate
  removes or retypes. An unreleased revision has no schema to compare, so this cannot be seen
  before staging. `stage` then exits nonzero, `status` prints it, and `commit` refuses the
  candidate.
- Not relied on: the platform. Its schema says `forwardsOnly` is rejected for a removed or retyped
  column. On 2026-11-21, on a scratch dataset, it accepted `forwardsOnly` for a unique-key model's
  revision that removed a column, and the check passed with the column classified `BREAKING`.
  Whether the commit would have been rejected was not tested. So nothing here waits for a
  platform refusal, and the tests, which run against a fake platform, establish only what this
  tool does.

**A commit names the candidate that was reviewed** (ruling R-2026-11-21-i). `status` and `stage`
print the candidate's id and a digest. `commit` takes both, reads the candidate again, and refuses
unless it is still the dataset's newest candidate, is open, has the same digest, passed its latest
check, and has no commit blocker.

- The digest covers every release decision the platform lets a client read back: the release the
  candidate is based on; each model's revision, who staged it, its resolved output schema, its
  model classification and every column classification with its source; and the id of the latest
  check. Staging again queues a new check, so a candidate changed after the review has another
  digest even when what changed cannot be read.
- The digest does not cover `forwardsOnly` or its defaults: the platform accepts them and does
  not report them back, so a reviewer cannot read them off a candidate. For a candidate that
  releases a model that keeps history, `commit` therefore also requires the **stage record** that
  `stage` wrote: the payload it sent and the check that ran on it. The commit is refused unless the
  record names this candidate and its latest check and shows `forwardsOnly` on every such model.
  A candidate staged any other way cannot be shown to be forwards-only, and is not committed here.

A release is the platform's record and cannot be withdrawn, which is why `commit` is a separate
command that a person runs with values they read.

A commit can outlast the call that asked for it. When the call times out or the connection drops,
`commit` exits 3 and says to read `status` before anything else: the candidate reads `COMMITTED`
once the platform finishes, and running `commit` again in between is refused by the checks above
only if the first one has already landed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

from pathlib import Path

from build.publish_registry import graphql

# A model of any other kind keeps rows across runs.
RECOMPUTED_KINDS = frozenset({"FULL", "VIEW"})
# Kind options that decide which stored row a new row replaces. Changing one recomputes the model.
ROW_KEY_OPTIONS = ("uniqueKeyColumns", "timeColumn", "partitionGrain")
CHECK_DONE = frozenset({"SUCCESS", "FAILED", "CANCELED"})
# A commit runs the dataset check once more before it releases. For an 18-model dataset that took
# longer than the 60 seconds a read is given, and the commit completed after the client gave up.
MUTATION_TIMEOUT = 600.0
# Where `stage` writes what it sent. Git-ignored: a record is evidence for one commit, not source.
RECORDS_DIR = Path(__file__).resolve().parent / "release-records"

_REVISION = "id revisionNumber kind kindOptions{ uniqueKeyColumns timeColumn partitionGrain }"
Q_DATASET = """query($where: JSON){ datasets(where:$where){ edges{ node{ id name } } } }"""
# The API refuses a page larger than 100. A dataset past that is refused here, not read in part.
Q_MODELS = """query($where: JSON){ dataModels(where:$where, first: 100){ pageInfo{ hasNextPage } edges{ node{
  id name isEnabled latestRevision{ %s } latestRelease{ revision{ %s storageSchema{ name type } } } } } } }""" % (
    _REVISION, _REVISION)
Q_CANDIDATE = """query($where: JSON){ datasets(where:$where){ edges{ node{ releaseCandidates(first: 1){ edges{ node{
  id status description createdAt commitBlockers latestCheckOutOfDate baseRelease{ id } latestCheck{ id status }
  revisions{ source dataModel{ id name } revision{ id revisionNumber } schema{ name type }
    storageSchema{ name type }
    modelClassification columnClassifications{ columnName classification source } } } } } } } } }"""
M_STAGE = """mutation($input: StageDatasetReleaseInput!){ stageDatasetRelease(input:$input){
  success message candidate{ id } } }"""
M_COMMIT = """mutation($input: CommitDatasetReleaseInput!){ commitDatasetRelease(input:$input){
  success message release{ id createdAt } } }"""


def keeps_history(model: dict) -> bool:
    """True when the model's released revision is of a kind that keeps rows across runs."""
    released = (model.get("latestRelease") or {}).get("revision")
    return bool(released) and released["kind"] not in RECOMPUTED_KINDS


def recompute_reasons(model: dict, revision: dict) -> list[str]:
    """Why releasing `revision` would recompute a model that keeps history (empty = it would not)."""
    if not keeps_history(model):
        return []
    released = model["latestRelease"]["revision"]
    reasons = []
    if revision["kind"] != released["kind"]:
        reasons.append(f"its kind changes from {released['kind']} to {revision['kind']}")
    old, new = released.get("kindOptions") or {}, revision.get("kindOptions") or {}
    for option in ROW_KEY_OPTIONS:
        if old.get(option) != new.get(option):
            reasons.append(f"{option} changes from {old.get(option)!r} to {new.get(option)!r}")
    return reasons


def stage_entries(models: list[dict], selected: dict[str, str | None],
                  added_columns: dict[str, dict[str, str | None]]) -> tuple[list[dict], list[str]]:
    """The `revisions` input for `stageDatasetRelease`, and what stops the stage.

    `selected` maps a model name to the revision id to release, or None for its latest revision.
    `added_columns` maps a model name to `{column: value}` for the columns its revision adds, the
    value being what rows already stored take (None leaves them NULL).

    A model that keeps history is always entered with `forwardsOnly`. Nothing is returned for
    staging while any problem stands.
    """
    by_name = {model["name"]: model for model in models}
    entries: list[dict] = []
    problems: list[str] = []
    for name in sorted(set(added_columns) - set(selected)):
        problems.append(f"{name}: added columns were given for a model that is not being released")
    for name, revision_id in selected.items():
        model = by_name.get(name)
        if model is None:
            problems.append(f"{name}: no such model in this dataset")
            continue
        if not model["isEnabled"]:
            problems.append(f"{name}: the model is disabled")
            continue
        latest = model["latestRevision"]
        if revision_id not in (None, latest["id"]):
            problems.append(f"{name}: {revision_id} is not its latest revision ({latest['id']}); only the latest "
                            "can be checked for a history rebuild here")
            continue
        released = (model.get("latestRelease") or {}).get("revision")
        if released and released["id"] == latest["id"]:
            problems.append(f"{name}: revision {latest['revisionNumber']} is already released; to re-lock it "
                            "against its upstreams, pass it with --refresh")
            continue
        entry = {"dataModelId": model["id"], "dataModelRevisionId": latest["id"]}
        if keeps_history(model):
            reasons = recompute_reasons(model, latest)
            if reasons:
                problems.append(f"{name}: keeps history, and this release would rebuild it from its start: "
                                + "; ".join(reasons))
                continue
            entry["forwardsOnly"] = True
            entry["forwardsOnlyDefaults"] = [
                {"columnName": column, "value": value}
                for column, value in sorted((added_columns.get(name) or {}).items())
            ]
        elif added_columns.get(name):
            problems.append(f"{name}: added columns apply only to a model that keeps history")
            continue
        entries.append(entry)
    return ([] if problems else entries), problems


def refresh_ids(models: list[dict], names: list[str]) -> tuple[list[str], list[str]]:
    """Model ids for `refreshUpstream`, and what stops them.

    A re-lock clones the released code under new upstream locks. For a model that keeps history
    the platform decides whether that recomputes, and this tool has no way to send `forwardsOnly`
    with it, so it is refused here.
    """
    by_name = {model["name"]: model for model in models}
    ids: list[str] = []
    problems: list[str] = []
    for name in names:
        model = by_name.get(name)
        if model is None:
            problems.append(f"{name}: no such model in this dataset")
        elif keeps_history(model):
            problems.append(f"{name}: keeps history, and a re-lock cannot be sent forwards-only")
        else:
            ids.append(model["id"])
    return ([] if problems else ids), problems


def reviewed_content(candidate: dict) -> dict:
    """Every release decision the platform reports for a candidate, in a canonical order.

    `forwardsOnly` and its defaults are absent because the platform does not report them; see the
    module docstring for how a commit covers them.
    """
    revisions = []
    for entry in sorted(candidate["revisions"], key=lambda e: (e["dataModel"]["name"], e["source"])):
        schema = entry.get("schema")
        revisions.append({
            "model": entry["dataModel"]["name"],
            "revision": entry["revision"]["id"],
            "source": entry["source"],
            "schema": None if schema is None else [[column["name"], column["type"]] for column in schema],
            "storage_schema": None if entry.get("storageSchema") is None else [
                [column["name"], column["type"]] for column in entry["storageSchema"]],
            "model_classification": entry.get("modelClassification"),
            "column_classifications": sorted(
                [c["columnName"], c["classification"], c["source"]] for c in entry.get("columnClassifications") or []
            ),
        })
    return {
        "base_release": (candidate.get("baseRelease") or {}).get("id"),
        "check": (candidate.get("latestCheck") or {}).get("id"),
        "revisions": revisions,
    }


def candidate_digest(candidate: dict) -> str:
    """SHA-256 over `reviewed_content`: what the candidate releases and the check that ran on it."""
    canonical = json.dumps(reviewed_content(candidate), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def history_models_in(candidate: dict, models: list[dict]) -> list[str]:
    """Names of the models the candidate releases that keep history, sorted."""
    keeping = {model["id"] for model in models if keeps_history(model)}
    return sorted({entry["dataModel"]["name"] for entry in candidate["revisions"]
                   if entry["dataModel"]["id"] in keeping})


def history_schema_problems(candidate: dict, models: list[dict]) -> list[str]:
    """Why a candidate would rebuild a history model's table: a stored column removed or retyped.

    Compares, for each model in the candidate that keeps history, the columns its released
    revision stores with the columns the candidate resolved for it. The platform accepts
    `forwardsOnly` for such a revision and passes its check, so this comparison is the refusal.
    A schema that was not resolved on either side is a problem too: the columns cannot be shown
    to be kept.
    """
    by_id = {model["id"]: model for model in models}
    problems = []
    for entry in sorted(candidate["revisions"], key=lambda e: e["dataModel"]["name"]):
        model = by_id.get(entry["dataModel"]["id"])
        if model is None or not keeps_history(model):
            continue
        name = entry["dataModel"]["name"]
        released = model["latestRelease"]["revision"].get("storageSchema")
        staged = entry.get("storageSchema")
        if not released or not staged:
            side = "released" if not released else "staged"
            problems.append(f"{name}: keeps history, and its {side} schema is not resolved, so its stored "
                            "columns cannot be shown to be kept")
            continue
        now = {column["name"].lower(): column["type"] for column in staged}
        removed = [c["name"] for c in released if c["name"].lower() not in now]
        retyped = [f"{c['name']} {c['type']} -> {now[c['name'].lower()]}" for c in released
                   if c["name"].lower() in now and now[c["name"].lower()] != c["type"]]
        if removed or retyped:
            parts = ([f"removes {', '.join(removed)}"] if removed else []) + (
                [f"retypes {', '.join(retyped)}"] if retyped else [])
            problems.append(f"{name}: keeps history, and this release would rebuild it from its start: "
                            + "; ".join(parts))
    return problems


def record_problems(record: dict | None, candidate: dict, models: list[dict]) -> list[str]:
    """Why the stage record does not show this candidate's history models went forwards-only.

    Empty when the candidate releases no model that keeps history, or when the record names this
    candidate and its latest check and carries `forwardsOnly` for each such model.
    """
    names = history_models_in(candidate, models)
    if not names:
        return []
    if record is None:
        return [f"the candidate releases {', '.join(names)}, which keep history, and forwardsOnly cannot be read "
                "back from the platform; pass the --stage-record that `stage` wrote for it"]
    problems = []
    if record.get("candidate_id") != candidate["id"]:
        problems.append(f"the stage record is for candidate {record.get('candidate_id')}, not {candidate['id']}")
    check = (candidate.get("latestCheck") or {}).get("id")
    if record.get("check_id") != check:
        problems.append(f"the stage record's check is {record.get('check_id')} and the candidate's latest is {check}: "
                        "it was staged or checked again after the record was written")
    sent = {entry["dataModelId"]: entry for entry in (record.get("payload") or {}).get("revisions") or []}
    ids = {model["name"]: model["id"] for model in models}
    for name in names:
        if not (sent.get(ids[name]) or {}).get("forwardsOnly"):
            problems.append(f"{name}: keeps history, and the stage record does not show it sent forwardsOnly")
    return problems


def stage_record(dataset: str, candidate: dict, payload: dict) -> dict:
    """What `stage` sent and the check that ran on it, as written beside the candidate's digest."""
    return {
        "dataset": dataset,
        "candidate_id": candidate["id"],
        "check_id": (candidate.get("latestCheck") or {}).get("id"),
        "digest": candidate_digest(candidate),
        "payload": payload,
    }


def commit_problems(pending: dict | None, candidate_id: str, digest: str) -> list[str]:
    """Why the reviewed candidate may not be committed now (empty = it may).

    `pending` is the dataset's newest candidate as the platform reports it at this moment.
    """
    if pending is None:
        return ["the dataset has no release candidate"]
    if pending["id"] != candidate_id:
        return [f"the dataset's newest candidate is {pending['id']}, not the reviewed {candidate_id}"]
    problems = []
    if pending["status"] != "OPEN":
        problems.append(f"the candidate is {pending['status']}, not OPEN")
    found = candidate_digest(pending)
    if found != digest:
        problems.append(f"the candidate now releases something else: digest {found}, reviewed {digest}")
    check = (pending.get("latestCheck") or {}).get("status")
    if check != "SUCCESS":
        problems.append(f"its latest check is {check or 'not run'}, not SUCCESS")
    if pending.get("commitBlockers"):
        problems.append(f"the platform reports commit blockers: {', '.join(pending['commitBlockers'])}")
    return problems


def render(dataset: str, candidate: dict | None, history: list[str] = (), record_path: Path | None = None,
           rebuilds: list[str] = ()) -> str:
    """The candidate as a person reviews it, ending with the command that commits exactly it.

    `history` names the models in it that keep history. Their forwards-only setting is not
    something the platform reports, so the line for each says where the evidence is. `rebuilds`
    are the reasons the candidate would rebuild a history table; with any, no commit command is
    printed.
    """
    if candidate is None:
        return f"{dataset}: no release candidate"
    check = candidate.get("latestCheck") or {}
    lines = [
        f"{dataset}: candidate {candidate['id']} is {candidate['status']}, staged {candidate['createdAt'][:16]}",
        f"  based on release: {(candidate.get('baseRelease') or {}).get('id') or '(none, first release)'}",
        f"  check: {check.get('status') or 'not run'} ({check.get('id') or 'no id'})    "
        f"commit blockers: {', '.join(candidate['commitBlockers']) or 'none'}",
        f"  description: {candidate.get('description') or '(none)'}",
    ]
    for entry in sorted(candidate["revisions"], key=lambda e: e["dataModel"]["name"]):
        name = entry["dataModel"]["name"]
        schema = entry.get("schema")
        columns = "schema unresolved" if schema is None else f"{len(schema)} column(s)"
        lines.append(f"  {name:<40} revision {entry['revision']['revisionNumber']:<4} {entry['source']:<6} {columns}")
        if entry.get("modelClassification"):
            lines.append(f"      model classified {entry['modelClassification']}")
        for c in sorted(entry.get("columnClassifications") or [], key=lambda c: c["columnName"]):
            lines.append(f"      column {c['columnName']}: {c['classification']} ({c['source']})")
        if name in history:
            lines.append("      keeps history: forwards-only is not reported by the platform; the stage record is the evidence")
    digest = candidate_digest(candidate)
    lines.append(f"  digest: {digest}")
    for problem in rebuilds:
        lines.append(f"  ! {problem}")
    if rebuilds:
        lines.append("  not committable with this tool: stage a revision that keeps those columns")
    elif candidate["status"] == "OPEN":
        record = f" --stage-record {record_path or '<the record stage wrote>'}" if history else ""
        lines.append(f"  to commit exactly this: uv run python -m build.release_dataset commit {dataset} "
                     f"--candidate {candidate['id']} --digest {digest}{record}")
    return "\n".join(lines)


class Platform:
    """The platform calls this tool makes. Tests pass a fake with the same four methods."""

    def __init__(self, token: str, org_id: str, call=graphql):
        self.token, self.org_id, self.call = token, org_id, call

    def dataset_id(self, name: str) -> str:
        where = {"org_id": {"eq": self.org_id}, "name": {"eq": name}}
        edges = self.call(Q_DATASET, {"where": where}, self.token)["datasets"]["edges"]
        if not edges:
            raise RuntimeError(f"no dataset named {name} in this organization")
        return edges[0]["node"]["id"]

    def models(self, dataset_id: str) -> list[dict]:
        page = self.call(Q_MODELS, {"where": {"dataset_id": {"eq": dataset_id}}}, self.token)["dataModels"]
        if page["pageInfo"]["hasNextPage"]:
            raise RuntimeError("the dataset has more than 100 models, and this tool reads one page")
        return [edge["node"] for edge in page["edges"]]

    def candidate(self, dataset_id: str) -> dict | None:
        node = self.call(Q_CANDIDATE, {"where": {"id": {"eq": dataset_id}}}, self.token)["datasets"]["edges"][0]["node"]
        edges = node["releaseCandidates"]["edges"]
        return edges[0]["node"] if edges else None

    def mutate(self, mutation: str, field: str, payload: dict) -> dict:
        result = self.call(mutation, {"input": payload}, self.token, timeout=MUTATION_TIMEOUT)[field]
        if not result["success"]:
            raise RuntimeError(f"{field} was refused: {result.get('message')}")
        return result


def wait_for_check(platform, dataset_id: str, timeout: float = 3600.0, interval: float = 15.0,
                   sleep=time.sleep) -> dict | None:
    """Poll the pending candidate until its latest check finishes or `timeout` passes."""
    waited = 0.0
    while True:
        candidate = platform.candidate(dataset_id)
        status = ((candidate or {}).get("latestCheck") or {}).get("status")
        if status in CHECK_DONE or waited >= timeout:
            return candidate
        sleep(interval)
        waited += interval


def _added_columns(values: list[str]) -> dict[str, dict[str, str | None]]:
    added: dict[str, dict[str, str | None]] = {}
    for value in values:
        target, _, default = value.partition("=")
        model, _, column = target.partition(".")
        if not model or not column:
            raise SystemExit(f"--added-column takes MODEL.COLUMN or MODEL.COLUMN=VALUE, not {value!r}")
        added.setdefault(model, {})[column] = default if "=" in value else None
    return added


def main(argv: list[str] | None = None, platform=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status", help="print the dataset's pending candidate; read-only")
    stage = commands.add_parser("stage", help="stage a candidate and wait for its check; releases nothing")
    commit = commands.add_parser("commit", help="commit the one reviewed candidate")
    for sub in (status, stage, commit):
        sub.add_argument("dataset", help="the dataset's name")
    stage.add_argument("--model", action="append", default=[], metavar="NAME[=REVISION_ID]",
                       help="a model to release at its latest revision; repeat for each")
    stage.add_argument("--refresh", action="append", default=[], metavar="NAME",
                       help="an unchanged model to re-lock against its upstreams' current releases")
    stage.add_argument("--added-column", action="append", default=[], metavar="MODEL.COLUMN[=VALUE]",
                       help="a column a history model's revision adds, and the value stored rows take")
    stage.add_argument("--description", help="what this release is, for the platform's record")
    stage.add_argument("--no-wait", action="store_true", help="return once staged, without waiting for the check")
    commit.add_argument("--candidate", required=True, help="the candidate id that was reviewed")
    commit.add_argument("--digest", required=True, help="the digest printed with it")
    commit.add_argument("--stage-record", type=Path, metavar="PATH",
                        help="the record `stage` wrote; required when the candidate releases a model that keeps history")
    stage.add_argument("--records-dir", type=Path, default=RECORDS_DIR, help="where the stage record is written")
    args = parser.parse_args(argv)

    if platform is None:
        token, org_id = os.environ.get("OSO_API_KEY"), os.environ.get("OSO_ORG_ID")
        if not token or not org_id:
            print("OSO_API_KEY and OSO_ORG_ID must both be set", file=sys.stderr)
            return 2
        platform = Platform(token, org_id)
    dataset_id = platform.dataset_id(args.dataset)

    if args.command == "status":
        candidate = platform.candidate(dataset_id)
        if candidate is None:
            print(render(args.dataset, None))
            return 0
        models = platform.models(dataset_id)
        print(render(args.dataset, candidate, history_models_in(candidate, models),
                     rebuilds=history_schema_problems(candidate, models)))
        return 0

    if args.command == "stage":
        if not args.model and not args.refresh:
            print("nothing to stage: pass --model or --refresh", file=sys.stderr)
            return 2
        selected = {name: (revision or None) for name, _, revision in (m.partition("=") for m in args.model)}
        models = platform.models(dataset_id)
        entries, problems = stage_entries(models, selected, _added_columns(args.added_column))
        refresh, refresh_problems = refresh_ids(models, args.refresh)
        problems += refresh_problems
        if problems:
            print("not staged:", file=sys.stderr)
            for problem in problems:
                print(f"  ! {problem}", file=sys.stderr)
            return 2
        payload = {"datasetId": dataset_id, "revisions": entries}
        if refresh:
            payload["refreshUpstream"] = refresh
        if args.description:
            payload["description"] = args.description
        for entry in entries:
            if entry.get("forwardsOnly"):
                print(f"  forwards-only: {next(m['name'] for m in models if m['id'] == entry['dataModelId'])}")
        platform.mutate(M_STAGE, "stageDatasetRelease", payload)
        candidate = platform.candidate(dataset_id) if args.no_wait else wait_for_check(platform, dataset_id)
        if candidate is None:
            print("staged, and the platform reports no candidate", file=sys.stderr)
            return 1
        args.records_dir.mkdir(parents=True, exist_ok=True)
        record_path = args.records_dir / f"{args.dataset}.{candidate['id']}.json"
        record_path.write_text(json.dumps(stage_record(args.dataset, candidate, payload), indent=2) + "\n")
        rebuilds = history_schema_problems(candidate, models)
        print(render(args.dataset, candidate, history_models_in(candidate, models), record_path, rebuilds))
        print(f"  stage record: {record_path}")
        check = (candidate.get("latestCheck") or {}).get("status")
        if rebuilds:
            return 1
        if args.no_wait:
            print("  the check has not finished: run status for the digest to review, and stage again without "
                  "--no-wait if a model keeps history, since the record must name the finished check")
        return 0 if args.no_wait or check == "SUCCESS" else 1

    pending = platform.candidate(dataset_id)
    problems = commit_problems(pending, args.candidate, args.digest)
    if not problems:
        models = platform.models(dataset_id)
        record = json.loads(args.stage_record.read_text()) if args.stage_record else None
        problems = history_schema_problems(pending, models) + record_problems(record, pending, models)
    if problems:
        print("not committed:", file=sys.stderr)
        for problem in problems:
            print(f"  ! {problem}", file=sys.stderr)
        return 2
    try:
        result = platform.mutate(M_COMMIT, "commitDatasetRelease", {"candidateId": args.candidate})
    except OSError as exc:
        # A timeout or a dropped connection says nothing about the commit, which the platform may
        # still complete. Committing again blind is the one thing not to do.
        print(f"the commit call did not return ({type(exc).__name__}: {exc}). It may still complete on the "
              f"platform. Do not run commit again yet: run `status {args.dataset}` until the candidate reads "
              "COMMITTED, or is still OPEN after several minutes.", file=sys.stderr)
        return 3
    release = result.get("release") or {}
    print(f"{args.dataset}: committed candidate {args.candidate} as release {release.get('id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
