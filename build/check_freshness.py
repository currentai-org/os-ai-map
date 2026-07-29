"""Report how stale the map's scores are.

The map's value depends on its numbers being current, and until now there was no
way to check that without reading 501 files. A score last touched in June looks
exactly like one touched yesterday.

**`docs/guides/freshness.md` is the normative definition.** The rule is one sentence:
`last_verified` is the most recent date on which everything in the score was confirmed
still correct. This module implements the report; that guide owns the meaning, and
when the two disagree the guide wins.

## Two dates, deliberately not merged

  * **`last_verified`** — the most recent date on which everything in the score was
    confirmed still correct. Written when an axis is re-checked against its sources,
    whether or not the value changed. 41 of 1,485 axes carry one, up from zero when
    the field landed, and watching that fill in is how we measure the automation.
  * **The score file's last commit date** — the fallback. Somebody committed this
    file on that date and left the score standing, which git records and nobody can
    inflate. Weaker than a re-check and *not* presented as one.

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

Exit status is 0 unless `--max-age-days` is given, so it is safe to run for
information. Pass a threshold to turn it into a CI gate once layer-2 is keeping
scores fresh; gating today would only fail on the pre-automation backlog.

Usage:
    uv run python -m build.check_freshness
    uv run python -m build.check_freshness --category base_pretrained
    uv run python -m build.check_freshness --max-age-days 30
"""

from __future__ import annotations

import argparse
import subprocess
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AXES = ("openness", "adoption", "capability")


def parse_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def commit_dates() -> dict[str, date]:
    """Most recent commit date per score file, from one pass over git history.

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

    One `git log` for the whole directory rather than 495 invocations. Walking
    newest-first, the first time a path appears is its latest commit.
    """
    result = subprocess.run(
        ["git", "log", "--format=%cs", "--name-only", "--", "sources/scores"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    latest: dict[str, date] = {}
    current: date | None = None
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # A `%cs` line parses as a date; a path line does not. That is the whole
        # discriminator, so no state machine is needed.
        parsed = parse_date(line)
        if parsed is not None:
            current = parsed
        elif current is not None and line.startswith("sources/scores/") and line.endswith(".yaml"):
            latest.setdefault(line[len("sources/scores/") : -len(".yaml")], current)
    return latest


def collect() -> tuple[dict[str, list[tuple[str, str, date, bool]]], list[str]]:
    """Return (category -> [(product, axis, when, is_verified)], axes with no date).

    `is_verified` separates a real `last_verified` from a commit-date fallback, so
    the report can never present the weaker signal as the stronger one.
    """
    committed = commit_dates()
    by_category: dict[str, list[tuple[str, str, date, bool]]] = defaultdict(list)
    undated: list[str] = []

    for path in sorted((ROOT / "sources" / "categories").glob("*.yaml")):
        category = yaml.safe_load(path.read_text())
        for product in category.get("products") or []:
            score_path = ROOT / "sources" / "scores" / f"{product}.yaml"
            if not score_path.exists():
                continue
            scores = yaml.safe_load(score_path.read_text()) or {}
            for axis in AXES:
                block = scores.get(axis)
                if not isinstance(block, dict):
                    continue

                verified = parse_date(block.get("last_verified"))
                if verified is not None:
                    by_category[category["name"]].append((product, axis, verified, True))
                    continue

                when = committed.get(product)
                if when is not None:
                    by_category[category["name"]].append((product, axis, when, False))
                else:
                    # Only reachable for a file git has never seen, so in practice an
                    # uncommitted local addition rather than a data problem.
                    undated.append(f"{product}.{axis}")
    return by_category, undated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="limit to one category slug")
    parser.add_argument(
        "--max-age-days",
        type=int,
        help="exit 1 if any category's oldest axis exceeds this. Omit to report only.",
    )
    parser.add_argument("--today", help="override today's date, YYYY-MM-DD, for testing")
    args = parser.parse_args()

    today = parse_date(args.today) or date.today()
    by_category, undated = collect()
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
        ages = sorted((today - when).days for _, _, when, _ in entries)
        median = ages[len(ages) // 2]
        product, axis, _, _ = max(entries, key=lambda e: (today - e[2]).days)
        print(f"{name:<30}{len(entries):>6}{median:>8}d{ages[-1]:>8}d  {product}.{axis}")
        stalest.append((ages[-1], name, f"{product}.{axis}"))

    all_ages = sorted((today - when).days for _, _, when, _ in rows)
    print(
        f"\n{len(rows)} axes | median {all_ages[len(all_ages) // 2]}d "
        f"| oldest {all_ages[-1]}d | newest {all_ages[0]}d"
    )

    verified_n = sum(1 for _, _, _, is_verified in rows if is_verified)
    print(
        f"\n{verified_n} of {len(rows)} axes carry a real last_verified. "
        f"The other {len(rows) - verified_n} fall back to the score file's last commit "
        "date, which dates the last time somebody committed the file and left the score "
        "standing. For a file untouched since it was added that dates the import, not a "
        "review, so read those ages as 'nobody has revisited this'."
    )
    if undated:
        print(
            f"{len(undated)} axes have no date at all: {', '.join(undated[:6])}"
            + (" ..." if len(undated) > 6 else "")
        )

    if args.max_age_days is None:
        return 0
    over = [(age, cat, what) for age, cat, what in stalest if age > args.max_age_days]
    if over:
        print(f"\n{len(over)} categor(ies) exceed {args.max_age_days}d:")
        for age, cat, what in sorted(over, reverse=True):
            print(f"  ! {cat:<28} {age}d  ({what})")
        return 1
    print(f"\nall categories within {args.max_age_days}d")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
