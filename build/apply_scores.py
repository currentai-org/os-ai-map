"""Write computed scores back into `sources/scores/`, so a human reviews rather than writes.

This is the one place where data flows INTO the repo. Everything else in `build/`
pushes declarations outward. That direction matters: the repo is the source of truth
for what the map SAYS, and this tool is the only thing allowed to change it without
a person typing the value.

## What it writes, and what it refuses to

  * `openness.last_verified` — whenever the pipeline could verify the score. That is
    the honest, machine-authored change: a fresh Hub field agreeing with the recorded
    license genuinely is verification, dated the day the field was fetched.
  * `openness.score` / `openness.class` — only when the computed value differs. It
    should not, since the rubric was reverse-engineered from these files, so a
    difference is either a real evidence change worth reviewing or a bug worth
    finding. Either way it must be loud, so `--check` exits non-zero on one.

It will NOT remove an existing `last_verified` when the pipeline can no longer earn
one. That case is reported instead. Deleting a date because provenance got stricter
is destructive, and the fix is to source the evidence, not to erase the record.

It will NOT touch `note`, `sources`, `confidence`, `adoption` or `capability`. Those
are human prose and human judgment. A tool that rewrote them would make its own diffs
unreviewable, which is the whole value of the review step.

## Why line editing rather than a YAML round trip

`yaml.safe_load` then `yaml.dump` reformats every string in the file — folded scalars
collapse, quoting changes, key order moves. The diff would be 501 files of noise with
the real change buried in it. So this edits the specific lines and leaves every other
byte alone. `last_verified` is replaced where it already sits, since its position
varies across the six files that carry one, and otherwise inserted before `sources:`,
which is where most of them put it.

Usage:
    uv run python -m build.apply_scores --check      # report, write nothing
    uv run python -m build.apply_scores              # write
    uv run python -m build.apply_scores --category base_pretrained
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TABLE = "currentai.scores.openness_computed"


def fetch_computed(category: str | None) -> list[dict]:
    """Read the computed scores. Requires OSO_API_KEY, same as publish_registry."""
    from pyoso import Client

    where = f"WHERE category_slug = '{category}'" if category else ""
    sql = f"""
        SELECT product_slug, category_slug, openness_score, openness_class,
               last_verified, unsourced_dimensions, license_tier_grade,
               dims_from_dataset, dims_relied_on, scoring_note
        FROM {TABLE}
        {where}
        ORDER BY product_slug
    """
    return Client().to_pandas(sql).to_dict("records")


def block_bounds(lines: list[str], key: str) -> tuple[int, int] | None:
    """Line range [start, end) of the top-level `key:` mapping."""
    start = None
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:") and not line[:1].isspace():
            start = index
            break
    if start is None:
        return None
    for index in range(start + 1, len(lines)):
        if lines[index].strip() and not lines[index][:1].isspace():
            return start, index
    return start, len(lines)


def find_key(lines: list[str], bounds: tuple[int, int], key: str) -> int | None:
    """Index of a two-space-indented `key:` inside the block, or None.

    Indent is checked exactly. A `score:` nested deeper — inside a `sources` entry,
    say — is a different key and must not be mistaken for the axis's own.
    """
    for index in range(bounds[0] + 1, bounds[1]):
        line = lines[index]
        if line.startswith(f"  {key}:") and not line[2:3].isspace():
            return index
    return None


def apply_to_file(path: Path, computed: dict) -> tuple[list[str], list[str]]:
    """Return (new_lines, changes). Empty changes means the file is already correct."""
    lines = path.read_text().splitlines(keepends=True)
    bounds = block_bounds(lines, "openness")
    if bounds is None:
        return lines, [f"{path.stem}: no openness block"]

    changes: list[str] = []
    score = computed.get("openness_score")
    klass = computed.get("openness_class")

    if score is not None:
        for key, value in (("score", int(score)), ("class", klass)):
            index = find_key(lines, bounds, key)
            if index is None:
                continue
            current = lines[index].split(":", 1)[1].strip()
            if current != str(value):
                lines[index] = f"  {key}: {value}\n"
                changes.append(f"{path.stem}: openness.{key} {current} -> {value}")

    verified = computed.get("last_verified")
    if verified is not None and str(verified) not in ("None", "NaT", "nan"):
        stamp = str(verified)[:10]
        index = find_key(lines, bounds, "last_verified")
        if index is not None:
            current = lines[index].split(":", 1)[1].strip().strip("'\"")
            if current != stamp:
                lines[index] = f"  last_verified: '{stamp}'\n"
                changes.append(f"{path.stem}: last_verified {current} -> {stamp}")
        else:
            anchor = find_key(lines, bounds, "sources")
            insert_at = anchor if anchor is not None else bounds[1]
            lines.insert(insert_at, f"  last_verified: '{stamp}'\n")
            changes.append(f"{path.stem}: last_verified + {stamp}")

    return lines, changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report only, write nothing")
    parser.add_argument("--category", help="limit to one category slug")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not os.environ.get("OSO_API_KEY"):
        print("OSO_API_KEY must be set", file=sys.stderr)
        return 2

    rows = fetch_computed(args.category)
    if not rows:
        print(f"no computed scores in {TABLE}", file=sys.stderr)
        return 2

    changed_files: list[Path] = []
    all_changes: list[str] = []
    score_changes: list[str] = []
    stale_kept: list[str] = []
    unscored: list[str] = []
    pending: dict[Path, list[str]] = {}

    for row in rows:
        slug = row["product_slug"]
        path = ROOT / "sources" / "scores" / f"{slug}.yaml"
        if not path.exists():
            continue

        if row.get("openness_score") is None:
            unscored.append(f"{slug}: {row.get('scoring_note')}")
            continue

        recorded = yaml.safe_load(path.read_text()) or {}
        had_verified = "last_verified" in (recorded.get("openness") or {})
        if had_verified and row.get("last_verified") is None:
            stale_kept.append(
                f"{slug}: carries last_verified but the pipeline cannot earn one "
                f"(unsourced: {row.get('unsourced_dimensions')})"
            )

        new_lines, changes = apply_to_file(path, row)
        if changes:
            pending[path] = new_lines
            all_changes.extend(changes)
            changed_files.append(path)
            score_changes.extend(c for c in changes if "openness.score" in c or "openness.class" in c)

    verified = sum(1 for r in rows if r.get("last_verified") is not None)
    from_dataset = sum(1 for r in rows if r.get("license_tier_grade") == "dataset")

    print(f"{len(rows)} computed score(s) read from {TABLE}")
    print(f"  license tier from a machine-readable field : {from_dataset}")
    print(f"  score verifiable end to end (last_verified): {verified}")
    print(f"  files this run would change                : {len(changed_files)}")
    print(f"  openness score or class moved              : {len(score_changes)}")

    if score_changes:
        print("\nSCORE CHANGES — each one needs a human to look at it:")
        for change in score_changes:
            print(f"  ! {change}")

    if unscored:
        print(f"\n{len(unscored)} product(s) the rubric declined to score:")
        for item in unscored:
            print(f"  - {item}")

    if stale_kept:
        print(f"\n{len(stale_kept)} product(s) keep a last_verified the pipeline cannot re-earn:")
        for item in stale_kept:
            print(f"  - {item}")
        print("  (left alone on purpose — source the evidence rather than erase the date)")

    if args.verbose and all_changes:
        print(f"\nall {len(all_changes)} change(s):")
        for change in all_changes:
            print(f"  {change}")

    if args.check:
        print("\ncheck only: nothing written")
        # A moved score is the one thing CI must not wave through.
        return 1 if score_changes else 0

    for path, new_lines in pending.items():
        path.write_text("".join(new_lines))
    print(f"\nwrote {len(pending)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
