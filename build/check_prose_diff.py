"""Does a diff touch only prose? The gate a prose-only pass runs before it commits.

A pass over `sources/` that is supposed to reword notes, `shows` and footnotes may change
nothing else: not a score, a `last_verified`, a URL, an `accessed` date, a digest, an
`establishes` list, a components mapping. The rule is easy to state and, on a 700-file diff,
impossible to check by eye. So this reads every changed YAML file under `sources/scores/`,
`sources/products/` and `sources/categories/` at a base ref and in the working tree, walks both
parsed documents leaf by leaf, and fails on any differing path that is not on the allowed list.

Allowed, per file kind:

    scores      <axis>.note, <axis>.sources[i].shows
    products    comments (including its removal), description
    categories  comments, strapline, scoring_recipe.note

A source list that changes length fails, because a removed or added entry is not a rewording
even if every remaining `shows` is. A file added or deleted outright fails too: a prose pass
creates nothing.

`build/components.py` already refuses to write an edit that changes a neighboring field. This is
the other half: the helpers guard one edit at a time, and this guards the whole diff, which is
what a reviewer actually reads.

Usage:
    uv run python -m build.check_prose_diff                    # working tree against HEAD
    uv run python -m build.check_prose_diff --base origin/main # a branch against its base
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

KINDS = {"scores": "scores", "products": "products", "categories": "categories"}


def allowed(kind: str, path: tuple) -> bool:
    """Is a differing leaf at `path` one a prose pass may change?"""
    if kind == "scores":
        if len(path) == 2 and path[1] == "note":
            return True
        if len(path) == 4 and path[1] == "sources" and isinstance(path[2], int) and path[3] == "shows":
            return True
        return False
    if kind == "products":
        return path in (("comments",), ("description",))
    if kind == "categories":
        return path in (("comments",), ("strapline",), ("scoring_recipe", "note"))
    return False


def leaf_diffs(before: object, after: object, path: tuple = ()) -> list[tuple]:
    """Paths at which two parsed documents differ. A list of different length is one diff at
    the list's own path, not one per element, so a removed source is reported as the list."""
    if isinstance(before, dict) and isinstance(after, dict):
        out = []
        for key in sorted(set(before) | set(after), key=str):
            if key not in before or key not in after:
                out.append(path + (key,))
            else:
                out.extend(leaf_diffs(before[key], after[key], path + (key,)))
        return out
    if isinstance(before, list) and isinstance(after, list):
        if len(before) != len(after):
            return [path]
        out = []
        for i, (b, a) in enumerate(zip(before, after)):
            out.extend(leaf_diffs(b, a, path + (i,)))
        return out
    return [] if before == after else [path]


def _at_ref(ref: str, rel: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else None


def changed_files(base: str) -> list[str]:
    """Paths under the three prose directories that differ between `base` and the working tree,
    tracked or not."""
    tracked = subprocess.run(
        ["git", "diff", "--name-only", base, "--", "sources/scores", "sources/products", "sources/categories"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--",
         "sources/scores", "sources/products", "sources/categories"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    return sorted(set(tracked) | set(untracked))


def violations(base: str = "HEAD") -> list[str]:
    out = []
    for rel in changed_files(base):
        kind = KINDS.get(Path(rel).parts[1])
        if kind is None or not rel.endswith(".yaml"):
            continue
        before_text = _at_ref(base, rel)
        after_path = ROOT / rel
        if before_text is None:
            out.append(f"{rel}: added; a prose pass creates no file")
            continue
        if not after_path.exists():
            out.append(f"{rel}: deleted; a prose pass removes no file")
            continue
        before = yaml.safe_load(before_text) or {}
        after = yaml.safe_load(after_path.read_text()) or {}
        for path in leaf_diffs(before, after):
            if not allowed(kind, path):
                dotted = ".".join(str(p) for p in path) or "<document>"
                out.append(f"{rel}: {dotted}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default="HEAD", help="ref to compare the working tree against")
    args = parser.parse_args()

    files = changed_files(args.base)
    bad = violations(args.base)
    print(f"{len(files)} prose-directory file(s) differ from {args.base}")
    if bad:
        print(f"{len(bad)} change(s) outside note / shows / comments / description / strapline:")
        for line in bad:
            print(f"  {line}")
        print("\nA prose pass moves no score, date, URL, digest, establishes or components entry.")
        return 1
    print("every change is in a prose field")
    return 0


if __name__ == "__main__":
    sys.exit(main())
