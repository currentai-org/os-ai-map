"""Did anything that moved a `last_verified` forward actually re-read its sources?

`last_verified` is the date on which everything in an axis was confirmed still correct, and
`docs/reference/evidence-and-freshness.md` owns that meaning. The failure mode this guards is
the cheap one: a diff that advances the date without a reading behind it, which is a freshness
claim with nothing under it. It is easy to produce by hand, easy to produce by a bad merge of
two re-verification runs, and invisible in a report that only prints ages.

So this reads every score file that differs between a base ref and the working tree, finds each
axis whose `last_verified` moved forward, and requires two things of it:

  * one of the axis's `sources[]` carries an `accessed` equal to the new `last_verified`, so the
    date names a reading rather than an opinion; and
  * the newest `accessed` on that axis moved forward too, so the evidence is a fresh read and not
    the same read re-cited under a newer conclusion.

The converse is deliberately not checked. A source may be re-read without the axis being re-dated
— a fetch is a weaker act than a re-confirmation — and `last_verified` is never backfilled from
`accessed`, so an `accessed` that moves alone is correct behavior, not a violation.

An adoption date that moved because a route re-measured the band is asked for the measurement
instead. Both requirements above are about a reading a person made, and neither applies to a
date whose support is an observation: the axis carries `derived_from`, the date must equal the
observation date recorded there, and no `accessed` needs to have moved at all — the counts
endpoint a curator cited was not what confirmed anything. `build/check_verification.py` is what
resolves that record against the snapshot ledger; this asks only that the moved date is the one
the record supports.

Usage:
    uv run python -m build.check_redate                    # working tree against HEAD
    uv run python -m build.check_redate --base main        # a branch against its base
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from build.adoption_freshness import DERIVATION_FIELD, DERIVED_AXIS
from build.vocabulary import axes

ROOT = Path(__file__).resolve().parents[1]


def _date(value: object) -> str:
    """A YAML date or quoted string as a comparable ISO string; '' when absent."""
    return "" if value is None else str(value)


def axis_violations(rel: str, axis: str, before: dict, after: dict) -> list[str]:
    """Why this axis's re-dating is unsupported, or an empty list when it is supported.

    `before` and `after` are one axis's parsed mappings. An axis whose `last_verified` did not
    move forward is never a violation, whatever its sources did.
    """
    was, now = _date(before.get("last_verified")), _date(after.get("last_verified"))
    if not (was and now and now > was):
        return []

    derived = after.get(DERIVATION_FIELD)
    if derived is not None:
        if axis != DERIVED_AXIS:
            return [f"{rel}: {axis} carries {DERIVATION_FIELD}, which only {DERIVED_AXIS} "
                    f"may derive"]
        as_of = _date((derived or {}).get("measurement_as_of"))
        if as_of != now:
            return [
                f"{rel}: {axis}.last_verified moved to {now} but the measurement it derives "
                f"from was observed {as_of or 'on no recorded date'}"
            ]
        return []

    seen_before = [_date(s.get("accessed")) for s in before.get("sources") or [] if s.get("accessed")]
    seen_after = [_date(s.get("accessed")) for s in after.get("sources") or [] if s.get("accessed")]
    out = []
    if now not in seen_after:
        out.append(
            f"{rel}: {axis}.last_verified moved to {now} but no source was accessed on that date"
        )
    if not seen_after or not seen_before or max(seen_after) <= max(seen_before):
        newest = max(seen_after) if seen_after else "none"
        out.append(
            f"{rel}: {axis}.last_verified moved {was} -> {now} but the newest accessed date "
            f"did not move (still {newest})"
        )
    return out


def _at_ref(ref: str, rel: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else None


def changed_files(base: str) -> list[str]:
    return sorted(
        subprocess.run(
            ["git", "diff", "--name-only", base, "--", "sources/scores"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    )


def redated(base: str = "HEAD") -> tuple[list[tuple[str, str, str, str]], list[str]]:
    """Axes whose `last_verified` moved forward since `base`, and the ones that cannot support it."""
    moved, bad = [], []
    for rel in changed_files(base):
        before_text = _at_ref(base, rel)
        after_path = ROOT / rel
        if before_text is None or not after_path.exists():
            continue
        before = yaml.safe_load(before_text) or {}
        after = yaml.safe_load(after_path.read_text()) or {}
        for axis in axes():
            a, b = before.get(axis), after.get(axis)
            if not isinstance(a, dict) or not isinstance(b, dict):
                continue
            was, now = _date(a.get("last_verified")), _date(b.get("last_verified"))
            if was and now and now > was:
                moved.append((rel, axis, was, now))
            bad.extend(axis_violations(rel, axis, a, b))
    return moved, bad


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default="HEAD", help="ref to compare the working tree against")
    args = parser.parse_args()

    moved, bad = redated(args.base)
    products = len({rel for rel, _, _, _ in moved})
    print(f"{len(moved)} axis re-dating(s) across {products} product(s) since {args.base}")
    for rel, axis, was, now in moved:
        print(f"  {Path(rel).stem}.{axis}: {was} -> {now}")
    if bad:
        print(f"\n{len(bad)} unsupported re-dating(s):")
        for line in bad:
            print(f"  {line}")
        return 1
    print("\nevery re-dated axis was read on the date it now claims, from a fresher source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
