"""Fail when a product slug leaves the payload without a redirect.

build/validate.py structurally cannot notice a deletion nobody recorded, because it only
reads live files, and a deletion is the absence of one. This diffs the currently serialized
payload against the one committed at HEAD and requires every slug that fell out in between
to carry an alias.

## Reading a git failure honestly

`git show HEAD:<payload>` fails identically -- exit 128 -- whether the payload was simply
never committed yet (a legitimate first run, nothing to compare against) or something is
actually broken: this is not a git repository, HEAD has no commit yet, or git itself is
missing. Collapsing those into one "skip" is the same failure build/freshness_payload.py was
rewritten to stop making: reading a failure this code cannot interpret as the one benign
failure it was hoping for, because both happen to look the same from the outside.

So this asks two separate questions instead of one:

  1. Does HEAD resolve at all (`git rev-parse --verify HEAD`)? If not, there is no history to
     trust -- not a repository, an unborn branch, or git absent -- and this raises rather than
     skipping.
  2. Only once HEAD is known good: does it carry this payload path? Absence here, and only
     here, means "first run" and returns None.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = "build/notebook_data.json"


class RetirementCheckError(RuntimeError):
    """Raised when git history cannot be read well enough to judge retirements safely."""


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise RetirementCheckError(
            "could not check retired slugs: git is not installed or not on PATH."
        ) from e


def _previous_payload(root: Path) -> dict | None:
    """The payload committed at HEAD, or None if HEAD has genuinely never carried one.

    None answers exactly one question -- does HEAD:<payload> exist -- and nothing else.
    Every other way this can fail raises, because a check that cannot tell "nothing to
    compare" apart from "I couldn't ask" and picks the answer that lets it pass through is
    not protecting anything.
    """
    verified = _run(["rev-parse", "--verify", "HEAD"], cwd=root)
    if verified.returncode != 0:
        raise RetirementCheckError(
            "could not check retired slugs: `git rev-parse --verify HEAD` failed "
            f"({verified.stderr.strip() or 'no stderr'}). A missing HEAD is not the same "
            "failure as a first run with no previous payload -- that is the payload path "
            "being absent FROM an existing HEAD, not HEAD itself being unresolvable."
        )
    exists = _run(["cat-file", "-e", f"HEAD:{PAYLOAD}"], cwd=root)
    if exists.returncode != 0:
        return None
    show = _run(["show", f"HEAD:{PAYLOAD}"], cwd=root)
    if show.returncode != 0:
        raise RetirementCheckError(
            f"could not check retired slugs: HEAD:{PAYLOAD} exists but `git show` could not "
            f"read it ({show.stderr.strip() or 'no stderr'})."
        )
    try:
        return json.loads(show.stdout)
    except json.JSONDecodeError as e:
        raise RetirementCheckError(
            f"could not check retired slugs: HEAD:{PAYLOAD} did not parse as JSON ({e})."
        ) from e


def _slugs(payload: dict) -> set[str]:
    return {p["slug"] for c in payload["categories"].values() for p in c["products"]}


def main() -> int:
    new = json.loads((ROOT / PAYLOAD).read_text())
    try:
        previous = _previous_payload(ROOT)
    except RetirementCheckError as exc:
        print(f"check_retirement: {exc}", file=sys.stderr)
        return 1
    if previous is None:
        print("check_retirement: no committed payload to compare against, skipping")
        return 0
    gone = _slugs(previous) - _slugs(new)
    unrouted = sorted(s for s in gone if s not in new["aliases"]["products"])
    if unrouted:
        print("check_retirement: these slugs left the payload with no alias, so their pages "
              "would 404:\n  " + "\n  ".join(unrouted), file=sys.stderr)
        print("Record each in sources/slug_aliases.yaml, or acknowledge the removal.",
              file=sys.stderr)
        return 1
    print(f"check_retirement: {len(gone)} retired, all routed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
