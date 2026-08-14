"""Write computed scores back into `sources/scores/`, so a human reviews rather than writes.

This is the one place where data flows INTO the repo. Everything else in `build/`
pushes declarations outward. That direction matters: the repo is the source of truth
for what the map SAYS, and this tool is the only thing allowed to change it without
a person typing the value.

## What it writes

  * `openness.score` / `openness.class` — only when the computed value differs. It
    should not, since the rubric was reverse-engineered from these files, so a
    difference is either a real evidence change worth reviewing or a bug worth
    finding. Either way it must be loud, so `--check` exits non-zero on one.

That is the whole list.

## Why it does not write `last_verified`

`docs/reference/evidence-and-freshness.md` is normative: `last_verified` is the most recent date on
which EVERYTHING in the score was confirmed still correct, and "everything" means
every dimension the score records, not only the ones the winning rule happens to read.

This pipeline cannot establish that, for any product, by construction. Of the recorded
openness dimensions, only `license` and `weights` have a dataset route;
`signal_routing.yaml` declares `data` research-only and the GitHub code route carries
`settles_dimension = false`, so both resolve to document grade in
`currentai.scores.openness_facts`. A document is a human's reading of prose that was
already in the score file. Re-reading the repo is not a confirmation of anything.

So there is no date here for the pipeline to write, and it writes none. Two earlier
attempts wrote one anyway, from a derived aggregate:

  * #108 wrote the freshness BOUND, the MIN `accessed` across the score's evidence.
  * #115 replaced it with `last_checked`, the MAX over the same dates.

Both are the mistake the guide names: any aggregate of access dates is still a
confirmation claim computed from readings, and changing the aggregation does not fix
the category error. Between them they put a derived date on 19 of the 26 axes that
carried one, in six cases overwriting a date a person had established by checking.
Those were reverted when this writer was removed.

`last_checked` is still read and reported, because "when did the pipeline last see any
of this evidence" is a useful diagnostic. It is not written to a file.

**What would have to change for this to write the field again.** Two things, and one of
them now exists. `currentai.scores.openness_computed` gained `dims_recorded` and
`all_recorded_dims_from_dataset`, which count and test every dimension the score RECORDS
rather than `dims_relied_on`'s narrower "what the winning rule read". Still missing is the
part that matters: a dataset route that settles `data` and `code`. So the boolean is false
on essentially every openness axis, and a guarded write-when-fully-confirmed branch would
still never fire. A branch that cannot fire reads as working code, so there is still no
branch — but the column it would read is there, and it is queryable if you want to see how
far off it is.

It will NOT touch `note`, `sources`, `confidence`, `adoption` or `capability`. Those
are human prose and human judgment. A tool that rewrote them would make its own diffs
unreviewable, which is the whole value of the review step.

## Why line editing rather than a YAML round trip

`yaml.safe_load` then `yaml.dump` reformats every string in the file — folded scalars
collapse, quoting changes, key order moves. The diff would be 501 files of noise with
the real change buried in it. So this edits the specific lines and leaves every other
byte alone.

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

# `block_bounds` and `find_key` used to be defined here. They now live beside the
# components rewriter, which needs the same two primitives and must not have a second
# copy of them: two implementations of "find this field in this file" is how one of them
# ends up subtly wrong about folded scalars while the other is right.
from build.components import block_bounds, find_key
from build.warehouse import query

ROOT = Path(__file__).resolve().parents[1]
TABLE = "currentai.scores.openness_computed"


def fetch_computed(category: str | None) -> list[dict]:
    """Read the computed scores. Requires OSO_API_KEY, same as publish_registry.

    The cache-busting nonce this used to append itself now comes from `build.warehouse`,
    which is the only place that builds a warehouse query and cannot be called without
    one. Its docstring carries the reasoning and the incident; the short version is that
    results cache on query TEXT, so a fixed string returns its first answer forever and
    this function once spent a full run cycle reporting pre-materialization numbers.
    """
    where = f"WHERE category_slug = '{category}'" if category else ""
    return query(f"""
        SELECT product_slug, category_slug, openness_score, openness_class,
               last_checked, unsourced_dimensions, license_tier_grade,
               dims_from_dataset, dims_relied_on, scoring_note
        FROM {TABLE}
        {where}
        ORDER BY product_slug
    """)


def has_date(value: object) -> bool:
    """True when a value read out of a DataFrame is a real date.

    Needed because a null DATE arrives as pandas NaT or float nan depending on the column's
    dtype, and both satisfy `is not None`. Counting with that test reported 14 products
    gaining a date when the true number was 5.
    """
    if value is None:
        return False
    text = str(value).strip()
    return text not in ("", "None", "NaT", "nan", "NaN")


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

    # No `last_verified` write. See the module docstring: the pipeline cannot confirm
    # every recorded dimension, so it has no date to offer, and every date it has offered
    # so far was an aggregate of access dates wearing a confirmation's name.
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

        new_lines, changes = apply_to_file(path, row)
        if changes:
            pending[path] = new_lines
            all_changes.extend(changes)
            changed_files.append(path)
            score_changes.extend(c for c in changes if "openness.score" in c or "openness.class" in c)

    checked = sum(1 for r in rows if has_date(r.get("last_checked")))
    from_dataset = sum(1 for r in rows if r.get("license_tier_grade") == "dataset")
    # How far automation actually reaches: the winning rule rested entirely on facts read
    # out of a machine-readable field. Reported because it is the number that has to grow
    # before this tool could ever write last_verified, and it is NOT sufficient on its own -
    # a rule can win on license alone while `data` and `code` stay document-grade.
    all_machine = sum(
        1 for r in rows
        if r.get("dims_relied_on") and r.get("dims_from_dataset") == r.get("dims_relied_on")
    )

    print(f"{len(rows)} computed score(s) read from {TABLE}")
    print(f"  license tier from a machine-readable field  : {from_dataset}")
    print(f"  winning rule rested only on dataset grade   : {all_machine}")
    print(f"  pipeline last saw evidence on a known date  : {checked}")
    print(f"  files this run would change                 : {len(changed_files)}")
    print(f"  openness score or class moved               : {len(score_changes)}")
    print("  last_verified written                       : 0, always (see the docstring)")

    if score_changes:
        print("\nSCORE CHANGES — each one needs a human to look at it:")
        for change in score_changes:
            print(f"  ! {change}")

    if unscored:
        print(f"\n{len(unscored)} product(s) the rubric declined to score:")
        for item in unscored:
            print(f"  - {item}")

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
