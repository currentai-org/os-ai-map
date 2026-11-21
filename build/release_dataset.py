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

Two rules are enforced here, before any call that changes the platform.

**History is released forwards-only** (ruling R-2026-11-08-s). A model whose released kind is not
`FULL` or `VIEW` keeps rows that a later run adds to and cannot rebuild: the sources behind the
history tables report only their current state. A release that recomputes such a model rebuilds
it from its start and loses those rows for good. So every revision of one is staged with
`forwardsOnly`, there is no flag that turns it off, and a change the platform can only apply by
recomputing (a different kind, or a different row key or time column) is refused. A removed or
retyped column is the third such change. An unreleased revision has no resolved schema to compare,
so that one is refused by the platform when it receives `forwardsOnly`, and the refusal is printed.

**A commit names the candidate that was reviewed** (ruling R-2026-11-21-i). `status` and `stage`
print the candidate's id and a digest of what it releases. `commit` takes both, reads the candidate
again, and refuses unless it is still the dataset's pending candidate, still releases exactly those
revisions, passed its latest check, and has no commit blocker. Staging after a review changes the
digest, so a candidate cannot be swapped under an approval.

A release is the platform's record and cannot be withdrawn, which is why `commit` is a separate
command that a person runs with values they read.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time

from build.publish_registry import graphql

# A model of any other kind keeps rows across runs.
RECOMPUTED_KINDS = frozenset({"FULL", "VIEW"})
# Kind options that decide which stored row a new row replaces. Changing one recomputes the model.
ROW_KEY_OPTIONS = ("uniqueKeyColumns", "timeColumn", "partitionGrain")
CHECK_DONE = frozenset({"SUCCESS", "FAILED", "CANCELED"})

_REVISION = "id revisionNumber kind kindOptions{ uniqueKeyColumns timeColumn partitionGrain }"
Q_DATASET = """query($where: JSON){ datasets(where:$where){ edges{ node{ id name } } } }"""
# The API refuses a page larger than 100. A dataset past that is refused here, not read in part.
Q_MODELS = """query($where: JSON){ dataModels(where:$where, first: 100){ pageInfo{ hasNextPage } edges{ node{
  id name isEnabled latestRevision{ %s } latestRelease{ revision{ %s } } } } } }""" % (_REVISION, _REVISION)
Q_CANDIDATE = """query($where: JSON){ datasets(where:$where){ edges{ node{ releaseCandidates(first: 1){ edges{ node{
  id status description createdAt commitBlockers latestCheck{ status }
  revisions{ source dataModel{ id name } revision{ id revisionNumber } } } } } } } } }"""
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


def candidate_digest(candidate: dict) -> str:
    """SHA-256 over what the candidate releases: each model, its revision, and who staged it."""
    lines = sorted(
        f"{entry['dataModel']['name']}\t{entry['revision']['id']}\t{entry['source']}"
        for entry in candidate["revisions"]
    )
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


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


def render(dataset: str, candidate: dict | None) -> str:
    """The candidate as a person reviews it, ending with the command that commits exactly it."""
    if candidate is None:
        return f"{dataset}: no release candidate"
    check = (candidate.get("latestCheck") or {}).get("status") or "not run"
    lines = [
        f"{dataset}: candidate {candidate['id']} is {candidate['status']}, staged {candidate['createdAt'][:16]}",
        f"  check: {check}    commit blockers: {', '.join(candidate['commitBlockers']) or 'none'}",
        f"  description: {candidate.get('description') or '(none)'}",
    ]
    for entry in sorted(candidate["revisions"], key=lambda e: e["dataModel"]["name"]):
        lines.append(f"  {entry['dataModel']['name']:<40} revision {entry['revision']['revisionNumber']:<4} "
                     f"{entry['source']}")
    digest = candidate_digest(candidate)
    lines.append(f"  digest: {digest}")
    if candidate["status"] == "OPEN":
        lines.append(f"  to commit exactly this: uv run python -m build.release_dataset commit {dataset} "
                     f"--candidate {candidate['id']} --digest {digest}")
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
        result = self.call(mutation, {"input": payload}, self.token)[field]
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
    args = parser.parse_args(argv)

    if platform is None:
        token, org_id = os.environ.get("OSO_API_KEY"), os.environ.get("OSO_ORG_ID")
        if not token or not org_id:
            print("OSO_API_KEY and OSO_ORG_ID must both be set", file=sys.stderr)
            return 2
        platform = Platform(token, org_id)
    dataset_id = platform.dataset_id(args.dataset)

    if args.command == "status":
        print(render(args.dataset, platform.candidate(dataset_id)))
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
        print(render(args.dataset, candidate))
        check = ((candidate or {}).get("latestCheck") or {}).get("status")
        return 0 if args.no_wait or check == "SUCCESS" else 1

    problems = commit_problems(platform.candidate(dataset_id), args.candidate, args.digest)
    if problems:
        print("not committed:", file=sys.stderr)
        for problem in problems:
            print(f"  ! {problem}", file=sys.stderr)
        return 2
    result = platform.mutate(M_COMMIT, "commitDatasetRelease", {"candidateId": args.candidate})
    release = result.get("release") or {}
    print(f"{args.dataset}: committed candidate {args.candidate} as release {release.get('id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
