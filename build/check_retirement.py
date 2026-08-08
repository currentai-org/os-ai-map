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

## Reading a schema change honestly

The same collapsing mistake shows up one layer down. A committed payload that predates the
`slug` field entirely carries no 'slug' key on any product -- there is nothing meaningful to
diff, and that is a legitimate skip, distinct from "no committed payload at all" above. But a
committed payload where only *some* products carry a slug is not that case: no single
serializer run produces a half-migrated payload, so that shape is treated as malformed and
fails loudly rather than silently dropping the unslugged rows from the comparison. Both
payloads are read through a shape guard rather than indexed into directly, so a missing
'categories' block, a non-dict category, or a non-dict product row is a clean
`check_retirement:`-prefixed error, never a raw traceback.
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


def _product_rows(payload: dict, label: str) -> list[dict]:
    """Every product row across every category in `payload`, or raise if the shape can't
    be trusted enough to read one.

    This is the guard the module was missing: it used to index straight into
    payload["categories"][...]["products"][...]["slug"] and let a malformed or
    schema-mismatched payload surface as a raw KeyError. A missing 'categories' block, a
    non-dict category, a non-list products field, or a non-dict product row all raise
    here -- deliberately, with a `label` naming which payload (new vs. previous) is at
    fault -- rather than one unqualified traceback that could be either.
    """
    if not isinstance(payload, dict):
        raise RetirementCheckError(f"the {label} payload is not an object (got {type(payload).__name__})")
    categories = payload.get("categories")
    if not isinstance(categories, dict):
        raise RetirementCheckError(
            f"the {label} payload has no usable 'categories' block (got {type(categories).__name__})"
        )
    rows: list[dict] = []
    for cid, cat in categories.items():
        if not isinstance(cat, dict):
            raise RetirementCheckError(f"{label} payload category {cid!r} is not an object")
        products = cat.get("products")
        if not isinstance(products, list):
            raise RetirementCheckError(f"{label} payload category {cid!r} has no usable products list")
        for row in products:
            if not isinstance(row, dict):
                raise RetirementCheckError(
                    f"{label} payload has a product row in category {cid!r} that is not an object"
                )
            rows.append(row)
    return rows


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

    try:
        new_rows = _product_rows(new, "new")
        unslugged_new = [r for r in new_rows if not r.get("slug")]
        if unslugged_new:
            raise RetirementCheckError(
                f"the new payload has {len(unslugged_new)} product(s) with no slug"
            )
        product_aliases = new.get("aliases", {}).get("products")
        if not isinstance(product_aliases, dict):
            raise RetirementCheckError("the new payload has no usable aliases.products block")

        previous_rows = _product_rows(previous, "previous")
    except RetirementCheckError as exc:
        print(f"check_retirement: {exc}", file=sys.stderr)
        return 1

    # The committed payload predates the slug field entirely -- every product in it is
    # missing 'slug', not just some. There is nothing meaningful to diff across a schema
    # change like that, so this skips rather than raising or guessing. This is distinct
    # from the "no committed payload at all" skip above: something WAS committed, it's
    # just from before slugs existed.
    previous_slugged = [r for r in previous_rows if r.get("slug")]
    if previous_rows and not previous_slugged:
        print(
            "check_retirement: the committed payload predates slugs (no product in it "
            "carries one), so there is nothing to diff across that schema change -- skipping"
        )
        return 0

    # A mix of slugged and unslugged products in the same committed payload is not the
    # clean pre-slug case above -- a single serializer run cannot produce that shape. It's
    # malformed, not merely old, so it fails loudly rather than silently dropping the
    # unslugged rows from the comparison (which would risk missing a real retirement).
    if len(previous_slugged) != len(previous_rows):
        print(
            "check_retirement: the committed payload has a mix of slugged and unslugged "
            "products, which should never happen -- refusing to guess which ones were "
            "retired",
            file=sys.stderr,
        )
        return 1

    new_slugs = {r["slug"] for r in new_rows}
    previous_slugs = {r["slug"] for r in previous_slugged}
    gone = previous_slugs - new_slugs
    unrouted = sorted(s for s in gone if s not in product_aliases)
    if unrouted:
        print("check_retirement: these slugs left the payload with no alias, so their pages "
              "would 404:\n  " + "\n  ".join(unrouted), file=sys.stderr)
        print("Record each as an alias on the product that replaced it, or acknowledge",
              file=sys.stderr)
        return 1
    print(f"check_retirement: {len(gone)} retired, all routed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
