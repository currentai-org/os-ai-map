"""Report how stale the map's scores are.

The map's value depends on its numbers being current, and until this existed there was no
way to check that without reading 472 files. A score last touched in June looks
exactly like one touched yesterday.

**`docs/reference/evidence-and-freshness.md` is the normative definition.** The rule is one sentence:
`last_verified` is the most recent date on which everything in the score was confirmed
still correct. This module implements the report; that guide owns the meaning, and
when the two disagree the guide wins.

## Two dates, deliberately not merged

  * **`last_verified`** — the most recent date on which everything in the score was
    confirmed still correct. Written when an axis is re-checked against its sources,
    whether or not the value changed. All 1,416 axes carry one as of 2026-08-14, up from
    zero when the field landed and 137 when this module did, and watching that fill in is
    how the automation was measured.
  * **The score file's last commit date** — the fallback. Somebody committed this
    file on that date and left the score standing, which git records and nobody can
    inflate. Weaker than a re-check and *not* presented as one. Read `commit_dates` for
    why "committed this file" has to mean a commit that changed what the file claims,
    and not simply one that touched it.

`last_verified` is deliberately NOT backfilled from `sources[].accessed`. Someone
opening a URL is a weaker claim than the conclusion being re-confirmed, and copying
one into a field whose name asserts the other would overstate freshness across every
axis at a stroke. It also adds nothing, since `accessed` is already in the files.

The commit date is the better fallback for the same reason it is honest: it dates a
review rather than a reading. `max(accessed)` read a median 55d when the files had in
fact been revised a median 35d ago, so it was both the stronger claim and the wronger
number. Its one limit, stated in the output: for a file untouched since it was added
the commit date dates the import, which still answers "has anyone revisited this".

This report labels which signal each number came from, and never lets the weaker one
be read as the stronger.

Exit status is 0 unless `--max-age-days` is given, so it is safe to run for information.
With a threshold it is a gate, and it fails if any category's oldest axis is over the
window, or if any axis has no date at all for the window to be measured against.

## Where the gate runs

`.github/workflows/freshness.yml`, weekly, at 45 days (temporary) — the window decided 2026-08-09 and
owned by `docs/reference/evidence-and-freshness.md` step 5. Not in `validate.yml`, and that is the one
design decision in this file worth knowing about.

Every other gate in this repo fails on something in a diff. This one fails on the passage of
time, so per pull request it would block work unrelated to the stale category, and nobody
could clear it from inside that pull request either: the remedy is to re-read a category
against its sources, which is a research pass ending in a pull request of its own. Weekly
rather than daily because a category is re-read in a single run, so its axes all age out
together and roughly four categories cross the line per week; a daily gate would re-report
the same cliff every day until the re-read finished. `validate.yml` runs the report without
a threshold, so a re-read pull request can see its own effect without anything being able to
fail on the clock.

Usage:
    uv run python -m build.check_freshness
    uv run python -m build.check_freshness --category base_pretrained
    uv run python -m build.check_freshness --max-age-days 45
"""

from __future__ import annotations

import argparse
import copy
import subprocess
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import yaml

from build.vocabulary import axes
from build.check_rubric import FREE_TEXT, _clauses, components_of

ROOT = Path(__file__).resolve().parents[1]
AXES = axes()  # build/vocabulary.py owns this; the score schema declares it

# `git log --raw` writes this in the old- or new-blob column for an add or a delete.
NULL_SHA = "0" * 40

# The walk parses roughly a thousand historical blobs, which is the whole cost of dating
# by content rather than by touch. libyaml does it in roughly a quarter of the time and is
# already present; falling back keeps the module importable where it is not.
_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def parse_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def score_projection(text: str) -> object | None:
    """The claim-bearing content of a score file, invariant to how it is stored.

    Two revisions with equal projections say the same thing about the product, however
    differently they spell it. That is the test for whether a commit reviewed anything.

    Only one storage choice is normalized away, because only one exists: `openness.
    components` is either the flat `k:v;k:v` string or the Phase 1a mapping plus its
    verbatim `openness.raw` sibling. `components_of` is the single reader for both
    (#186), so this reduces each shape to the same key -> clause dict and drops `raw`,
    which is the migration's own bookkeeping rather than a claim. `free_text` rides
    along because the keyless clauses `split_components` discards are still published in
    the flat string, so losing one is not score-neutral.

    Everything else in the document is compared as it stands. The normalization is narrow
    on purpose: any field this ignored could then be changed without moving the date, and
    nothing would report it.

    **The blind spot, and the maintenance rule it implies.** A component ENTRY is compared
    only through `recompose`, which reads `entry["raw"]` when there is one and otherwise
    `f"{value}({detail})"`. Nothing else inside an entry reaches this comparison. So adding
    `license_tier: 3` to an entry does not move the date, and neither does changing
    `entry["value"]` on an entry that carries a `raw` — `recompose` returns the `raw` and
    never looks. That is inert today because no reader reads any other per-entry key, but
    Phase 1a exists to make entries structured, so the first real field added under one
    would land silently unversioned. **When a per-entry field lands, add it here in the
    same change.** This is a different case from the paragraph above, which is about
    top-level fields; neither note covers the other.

    Returns None for a revision that will not parse. A blob nothing can read cannot be
    shown score-neutral, and the caller treats that as a change rather than a match.
    """
    try:
        doc = yaml.load(text, Loader=_LOADER)
    except yaml.YAMLError:
        return None
    if not isinstance(doc, dict):
        return None
    doc = copy.deepcopy(doc)
    openness = doc.get("openness")
    if isinstance(openness, dict) and "components" in openness:
        components = openness.get("components")
        if isinstance(components, dict):
            free = list(components.get(FREE_TEXT) or [])
        else:
            free = [c.strip() for c in _clauses(str(components or "")) if ":" not in c.strip()]
        openness["components"] = {"clauses": components_of(openness), FREE_TEXT: free}
        openness.pop("raw", None)
    return doc


class _Blobs:
    """Blob text by sha, from one long-lived `git cat-file --batch`.

    One process for the whole walk. The alternative — `git show` per revision — is a
    process spawn per blob, and `commit_dates` runs inside `serialize`, which runs in CI.
    """

    def __init__(self, root: Path) -> None:
        self._proc = subprocess.Popen(
            ["git", "cat-file", "--batch"],
            cwd=root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        self._cache: dict[str, str | None] = {}

    def text(self, sha: str) -> str | None:
        if sha not in self._cache:
            self._proc.stdin.write(f"{sha}\n".encode())
            self._proc.stdin.flush()
            header = self._proc.stdout.readline().split()
            if len(header) < 3:
                # "<sha> missing". Nothing to read back, and the caller must not treat
                # an unreadable revision as equal to anything.
                self._cache[sha] = None
            else:
                data = self._proc.stdout.read(int(header[2]))
                self._proc.stdout.read(1)  # the batch record's trailing newline
                self._cache[sha] = data.decode("utf-8", "replace")
        return self._cache[sha]

    def close(self) -> None:
        self._proc.stdin.close()
        self._proc.stdout.close()
        self._proc.wait()


def _score_history(root: Path) -> dict[str, list[tuple[date, str, str]]]:
    """slug -> [(commit date, old blob, new blob)], newest first.

    One `git log` for the whole directory rather than 472 invocations, and `--raw` rather
    than `--name-only` so each entry carries the blob shas the walk needs — no second
    round trip to find out what a commit did to a file.

    `--no-renames` on purpose: a rename then reads as a delete plus an add, and an add is
    where a slug's history honestly starts. With detection on, a pure rename would be
    score-neutral for the new slug and the walk would run off the end of its history.
    """
    result = subprocess.run(
        ["git", "log", "--format=%x01%cs", "--raw", "--no-abbrev", "--no-renames",
         "--", "sources/scores"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    history: dict[str, list[tuple[date, str, str]]] = defaultdict(list)
    current: date | None = None
    for line in result.stdout.splitlines():
        if line.startswith("\x01"):
            current = parse_date(line[1:].strip())
            continue
        if current is None or not line.startswith(":"):
            continue
        meta, _, path = line.partition("\t")
        path = path.split("\t")[-1].strip()
        if not (path.startswith("sources/scores/") and path.endswith(".yaml")):
            continue
        fields = meta.split()
        if len(fields) < 4:
            continue
        history[path[len("sources/scores/") : -len(".yaml")]].append(
            (current, fields[2], fields[3])
        )
    return history


def _last_substantive(entries: list[tuple[date, str, str]], blobs: _Blobs) -> date | None:
    """The newest commit in `entries` that changed what the file claims.

    Walks newest-first and skips a commit whose two revisions of this file project to the
    same thing. An add or a delete is never skipped: there is no other revision to compare
    against, and both are real events in the file's life.

    If every commit in reach is structural the oldest one is returned rather than nothing,
    which only happens when history has been truncated beneath the file's add.
    """
    for when, old_sha, new_sha in entries:
        if old_sha == NULL_SHA or new_sha == NULL_SHA:
            return when
        old_text, new_text = blobs.text(old_sha), blobs.text(new_sha)
        if old_text is None or new_text is None:
            return when
        before, after = score_projection(old_text), score_projection(new_text)
        if before is None or after is None or before != after:
            return when
    return entries[-1][0] if entries else None


def commit_dates(root: Path | None = None) -> dict[str, date]:
    """Date of the last commit that changed what each score file CLAIMS.

    This is the fallback when an axis carries no `last_verified`, and it is a better
    one than `max(sources[].accessed)`. Committing a score file is somebody asserting
    the file is right as of that date, which is why #102 put it as "the git history of
    a score file becomes its verification record". An `accessed` date only says a URL
    was opened; copying that into a freshness figure is the overstatement that PR
    reverted, and it reads 20 days staler than the truth because it dates the reading
    rather than the review.

    Honest about what it is not: for a file untouched since it was added, this dates
    the import, not a review. That still answers the question the report exists for -
    nobody has revisited this - which is why the label says `commit` and not
    `verified`.

    ## Why it is not simply the last commit that touched the file

    Because some commits touch a file without reviewing it. The Phase 1a migration
    reshapes `openness.components` from a string into a mapping in all 472 files while
    carrying a byte-identical `raw:` copy of the string, so nothing a reader would call
    a claim moves — and the naive fallback would republish every one of them as freshly
    reviewed on the migration day. A commit date is only defensible here because it
    dates a review; a commit that reviewed nothing must not supply one, or the fallback
    starts making the same category error `sources[].accessed` made.

    So the walk goes newest-first per file and skips any commit whose two revisions of
    that file have the same `score_projection`. This needs no convention and no trailer:
    a commit cannot claim to have reviewed something the content says it did not touch,
    and it works on history already written.

    One `git log` for the whole directory and one `git cat-file --batch` for the blobs,
    rather than a process per file.

    `root` defaults to this module's own repository root, which is what every existing
    caller in this file wants. `build.freshness_payload` passes its own `root` through
    explicitly so it can be pointed at a different checkout (a test fixture, a shallow-
    clone probe) without silently reading this repository's history instead.
    """
    history = _score_history(root or ROOT)
    blobs = _Blobs(root or ROOT)
    try:
        dates = {slug: _last_substantive(entries, blobs) for slug, entries in history.items()}
    finally:
        blobs.close()
    return {slug: when for slug, when in dates.items() if when is not None}


def held_axes(root: Path | None = None) -> dict[tuple[str, str], str]:
    """(product, axis) -> the date it was put on hold, from `sources/verification_queue.yaml`.

    A held axis is one a re-read opened, worked, and honestly could not settle, parked with
    the condition that would close it. It carries no `last_verified` by design, and
    `tests/test_verification_queue_consistency.py` enforces that it never carries one.

    Without this, the report could only see the absence, so it dated the axis from its last
    commit and filed it under "nobody has revisited this" — the one thing that is untrue of
    a product somebody worked and queued. Measured 2026-08-15, every one of the 8 undated
    axes in the corpus is held, so this was the whole of that line's population.
    """
    path = (root or ROOT) / "sources" / "verification_queue.yaml"
    if not path.exists():
        return {}
    queue = yaml.safe_load(path.read_text()) or {}
    return {
        (slug, axis): str((spec or {}).get("since") or "?")
        for slug, axes in (queue.get("held") or {}).items()
        for axis, spec in (axes or {}).items()
    }


def collect(
    root: Path | None = None,
) -> tuple[dict[str, list[tuple[str, str, date, bool, str | None]]], list[str]]:
    """Return (category -> [(product, axis, when, is_verified, held_since)], axes with no date).

    `is_verified` separates a real `last_verified` from a commit-date fallback, so
    the report can never present the weaker signal as the stronger one. `held_since` is
    non-None where the axis is parked in the verification queue, which is a third state:
    not confirmed, but not unexamined either.

    `root` defaults to this module's own repository, which is what the command line wants.
    The tests pass a fixture checkout, so the gate's behavior can be asserted against dates
    they construct rather than against whatever the corpus happens to say today.
    """
    root = root or ROOT
    committed = commit_dates(root)
    held = held_axes(root)
    by_category: dict[str, list[tuple[str, str, date, bool, str | None]]] = defaultdict(list)
    undated: list[str] = []

    for path in sorted((root / "sources" / "categories").glob("*.yaml")):
        category = yaml.safe_load(path.read_text())
        for product in category.get("products") or []:
            score_path = root / "sources" / "scores" / f"{product}.yaml"
            if not score_path.exists():
                continue
            scores = yaml.safe_load(score_path.read_text()) or {}
            for axis in AXES:
                block = scores.get(axis)
                if not isinstance(block, dict):
                    continue

                verified = parse_date(block.get("last_verified"))
                if verified is not None:
                    by_category[category["name"]].append((product, axis, verified, True, None))
                    continue

                when = committed.get(product)
                if when is not None:
                    since = held.get((product, axis))
                    by_category[category["name"]].append((product, axis, when, False, since))
                else:
                    # Only reachable for a file git has never seen, so in practice an
                    # uncommitted local addition rather than a data problem.
                    undated.append(f"{product}.{axis}")
    return by_category, undated


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="limit to one category slug")
    parser.add_argument(
        "--max-age-days",
        type=int,
        help="exit 1 if any category's oldest axis exceeds this. Omit to report only.",
    )
    parser.add_argument("--today", help="override today's date, YYYY-MM-DD, for testing")
    args = parser.parse_args(argv)
    if args.max_age_days is not None and args.max_age_days < 1:
        parser.error("--max-age-days must be at least 1; a window of zero days fails everything")

    today = parse_date(args.today) or date.today()
    by_category, undated = collect(root)
    if args.category:
        by_category = {k: v for k, v in by_category.items() if k == args.category}

    rows = [entry for entries in by_category.values() for entry in entries]
    if not rows:
        print("no scored axes found")
        return 0

    print(f"{'category':<30}{'axes':>6}{'median':>9}{'oldest':>9}  oldest product")
    stalest: list[tuple[int, str, str]] = []
    for name in sorted(by_category):
        entries = by_category[name]
        ages = sorted((today - when).days for _, _, when, _, _ in entries)
        median = ages[len(ages) // 2]
        product, axis, _, _, _ = max(entries, key=lambda e: (today - e[2]).days)
        print(f"{name:<30}{len(entries):>6}{median:>8}d{ages[-1]:>8}d  {product}.{axis}")
        stalest.append((ages[-1], name, f"{product}.{axis}"))

    all_ages = sorted((today - when).days for _, _, when, _, _ in rows)
    print(
        f"\n{len(rows)} axes | median {all_ages[len(all_ages) // 2]}d "
        f"| oldest {all_ages[-1]}d | newest {all_ages[0]}d"
    )

    verified_n = sum(1 for _, _, _, is_verified, _ in rows if is_verified)
    held_rows = [(p, a, since) for p, a, _, is_verified, since in rows if not is_verified and since]
    fallback_n = len(rows) - verified_n - len(held_rows)
    if verified_n == len(rows):
        print(
            f"\nall {len(rows)} axes carry a real last_verified, so no age above rests on "
            "the commit-date fallback."
        )
    else:
        print(f"\n{verified_n} of {len(rows)} axes carry a real last_verified.")
        if fallback_n:
            print(
                f"{fallback_n} fall back to the score file's last commit date, which dates "
                "the last time somebody committed the file and left the score standing. For a "
                "file untouched since it was added that dates the import, not a review, so "
                "read those ages as 'nobody has revisited this'."
            )
        if held_rows:
            # These are the opposite of unexamined: somebody worked the axis, could not
            # settle it, and parked it with the condition that would close it. Reporting
            # them beside the never-touched ones was the misreading this separates out.
            print(
                f"{len(held_rows)} are HELD in sources/verification_queue.yaml — worked, "
                "unsettled, and deliberately carrying no date. Their age is the commit "
                "fallback and says nothing about the hold:"
            )
            for product, axis, since in sorted(held_rows):
                print(f"  · {f'{product}.{axis}':<52} held since {since}")
    if undated:
        print(
            f"{len(undated)} axes have no date at all: {', '.join(undated[:6])}"
            + (" ..." if len(undated) > 6 else "")
        )

    if args.max_age_days is None:
        return 0

    over = [(age, cat, what) for age, cat, what in stalest if age > args.max_age_days]
    if over or undated:
        if over:
            print(f"\n{len(over)} of {len(by_category)} categories are over {args.max_age_days}d:")
            for age, cat, what in sorted(over, reverse=True):
                print(f"  ! {cat:<28} {age}d  ({what})")
        # An undated axis is unmeasurable, so the gate cannot vouch for it either way. This
        # list is repo-wide even under --category, because a missing date is not a fact about
        # the category you asked about. In CI it should be empty: it is only reachable for a
        # file git has never seen.
        if undated:
            print(
                f"\n{len(undated)} axes have no date for the window to measure: "
                f"{', '.join(undated)}"
            )
        print(
            "\nRe-read each category named above against its sources and stamp a fresh\n"
            "last_verified per axis: `skills/refresh-category` drives that, one category per\n"
            "PR. Editing a date without re-reading is the failure this gate exists to catch;\n"
            "docs/reference/evidence-and-freshness.md says what a confirmation has to consist of.\n"
            "\n"
            "Several categories aging out at once is expected rather than a backlog. A category\n"
            "is re-read in one run, so all of its axes carry one date and all of them cross the\n"
            f"line together. {len(by_category)} categories on a {args.max_age_days}d window is "
            f"about {round(len(by_category) * 7 / args.max_age_days)} a week."
        )
        return 1
    print(f"\nall {len(by_category)} categories within {args.max_age_days}d")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
