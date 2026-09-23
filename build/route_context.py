"""Put every `components` key the product's ladder does not read under `context`, and only those.

`build/check_components.py` asserts the split; this is what satisfies it. It is not a one-shot
migration: the split is a function of the ladder, so a ladder that gains or loses a `reads`
entry moves keys across it, and the repair is to run this again.

## What it may change

Only WHERE an entry sits inside `openness.components`. Every entry keeps its bytes, `raw` is
never touched, and `components_of` returns the same dict before and after because `recompose`
flattens `context` back in — so no reader, score, payload or warehouse row can move. The run
asserts that per file before writing, on top of the three reparse assertions
`build/components.py` makes about the edit itself.

The rule is mechanical and total, which is the point: a key the resolved ladder neither declares
nor reads goes to `context`. 62 of the 116 such keys at the time of #188 appeared exactly once,
so a per-key ruling would have been 116 decisions before any of them could be recorded.

Usage:
    uv run python -m build.route_context            # report what would move
    uv run python -m build.route_context --write    # move it
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from build.check_rubric import CONTEXT, components_of, route_context
from build.components import set_field
from build.rubrics import load_product_recipes

ROOT = Path(__file__).resolve().parents[1]


def plan(root: Path = ROOT) -> dict[Path, tuple[dict, list[str], list[str]]]:
    """path -> (new components, keys moved into context, keys moved out), changed files only."""
    recipes = load_product_recipes(root)
    out: dict[Path, tuple[dict, list[str], list[str]]] = {}
    for path in sorted((root / "sources" / "scores").glob("*.yaml")):
        recipe = recipes.get(path.stem)
        openness = (yaml.safe_load(path.read_text()) or {}).get("openness") or {}
        components = openness.get("components")
        if recipe is None or not isinstance(components, dict):
            continue
        routed = route_context(components, recipe)
        # Equality ignores order on purpose: a record with nothing to move is left alone rather
        # than re-sorted into route_context's canonical order.
        if routed == components:
            continue
        before = set(components.get(CONTEXT) or {})
        after = set(routed.get(CONTEXT) or {})
        out[path] = (routed, sorted(after - before), sorted(before - after))
    return out


def write(path: Path, routed: dict) -> None:
    text = path.read_text()
    openness = (yaml.safe_load(text) or {}).get("openness") or {}
    new_text = set_field(text, routed)
    moved = (yaml.safe_load(new_text) or {}).get("openness") or {}
    if components_of(moved) != components_of(openness) or moved.get("raw") != openness.get("raw"):
        raise ValueError(f"{path.stem}: routing changed what a reader sees; refusing to write")
    path.write_text(new_text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--write", action="store_true", help="rewrite the files (default: report)")
    args = parser.parse_args(argv)

    changes = plan()
    into = sum(len(i) for _, i, _ in changes.values())
    out = sum(len(o) for _, _, o in changes.values())
    for path, (routed, moved_in, moved_out) in changes.items():
        if args.write:
            write(path, routed)
        parts = [f"+{CONTEXT}: {', '.join(moved_in)}"] if moved_in else []
        parts += [f"-{CONTEXT}: {', '.join(moved_out)}"] if moved_out else []
        print(f"  {path.stem}: {'; '.join(parts)}")
    verb = "moved" if args.write else "would move"
    print(f"\n{len(changes)} record(s): {verb} {into} key(s) into {CONTEXT}, {out} out of it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
