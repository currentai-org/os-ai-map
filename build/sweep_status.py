"""Where the verification sweep has got to, derived from the corpus rather than stored.

`/goal` runs one category per invocation and has to know which one is next. That could be a
pointer in a file, and a pointer is a second copy of a fact the corpus already carries — it
desyncs the first time a category is finished by hand, or half-finished, or reverted. So there
is no pointer. This module reads `sources/` and works it out.

## What "done" means for a product

The bar agreed on 2026-08-08, and it is per product rather than per axis:

  * every axis carries a real `last_verified`, or abstains deliberately (a null value, which
    `verification.md` explains for the 46 axes that have one), or the product is held;
  * `comments` ends in the canonical verification line, which is the prose half's proxy —
    `product-info.md` has rules a checker cannot enforce, but the line is the one thing a
    finished product always has;
  * held products count as resolved, not as remaining. A product whose evidence cannot be
    settled goes into `sources/verification_queue.yaml` with a reason and stops blocking its
    category, which is what let the pilot ship five of six.

Deliberately NOT counted as done: an axis whose value is null because nobody looked. The two
are indistinguishable in the file today, which is the gap the per-axis deferral idea closes.
Until that exists this over-counts, and `--verbose` prints the null axes so the number can be
read with that in mind.

## Order

Worst artifact coverage first, so the categories where automation helps least go while the
sweep is cheapest to change. Coverage is measured locally as the share of a category's products
carrying a routable artifact block, which is the same thing `check_routing` counts and does not
need the warehouse.

Usage:
    uv run python -m build.sweep_status
    uv run python -m build.sweep_status --verbose
    uv run python -m build.sweep_status --next        # just the next category's slug
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AXES = ("openness", "adoption", "capability")
VALUE_KEY = {"openness": "score", "adoption": "level", "capability": "score"}
ARTIFACTS = ("github", "pypi", "npm", "crates", "huggingface_model", "huggingface_dataset")
VERIFIED_LINE = re.compile(r"Verified \d{4}-\d{2}-\d{2} via ")


def load() -> tuple[dict, dict, dict, dict, dict]:
    def _dir(name: str) -> dict:
        out = {}
        for path in sorted((ROOT / "sources" / name).glob("*.yaml")):
            doc = yaml.safe_load(path.read_text()) or {}
            out[doc.get("name") or doc.get("product") or path.stem] = doc
        return out

    queue_path = ROOT / "sources" / "verification_queue.yaml"
    queue = {}
    if queue_path.exists():
        queue = (yaml.safe_load(queue_path.read_text()) or {}).get("held") or {}
    return _dir("categories"), _dir("products"), _dir("scores"), queue, {}


def product_state(slug: str, product: dict, score: dict, held: dict) -> dict:
    """Per-product: which axes are settled, whether the prose is, and whether it is held."""
    axes = {}
    for axis in AXES:
        block = score.get(axis) or {}
        if block.get("last_verified"):
            axes[axis] = "verified"
        elif block.get(VALUE_KEY[axis]) is None:
            axes[axis] = "abstained"
        else:
            axes[axis] = "open"
    prose = bool(VERIFIED_LINE.search(str(product.get("comments") or "")))
    return {
        "axes": axes,
        "prose": prose,
        "held": slug in held,
        "done": slug in held or (all(v != "open" for v in axes.values()) and prose),
    }


def survey() -> list[dict]:
    cats, prods, scores, held, _ = load()
    rows = []
    for slug, cat in cats.items():
        roster = cat.get("products") or []
        states = {
            p: product_state(p, prods.get(p) or {}, scores.get(p) or {}, held) for p in roster
        }
        routable = sum(
            1 for p in roster if any((prods.get(p) or {}).get(k) for k in ARTIFACTS)
        )
        rows.append({
            "category": slug,
            "products": len(roster),
            "done": sum(1 for s in states.values() if s["done"]),
            "held": sum(1 for s in states.values() if s["held"]),
            "coverage": routable / len(roster) if roster else 1.0,
            "states": states,
        })
    # Worst coverage first; a finished category sorts to the back whatever its coverage.
    rows.sort(key=lambda r: (r["done"] >= r["products"], r["coverage"], r["category"]))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="list what is unfinished")
    parser.add_argument("--next", action="store_true", help="print the next category and exit")
    args = parser.parse_args()

    rows = survey()
    pending = [r for r in rows if r["done"] < r["products"]]

    if args.next:
        print(pending[0]["category"] if pending else "")
        return 0

    total = sum(r["products"] for r in rows)
    done = sum(r["done"] for r in rows)
    print(f"{'category':30}{'done':>6}{'held':>6}{'of':>5}{'artifacts':>11}")
    for row in rows:
        print(
            f"{row['category']:30}{row['done']:6}{row['held']:6}{row['products']:5}"
            f"{row['coverage']:10.0%}"
        )
    print(f"{'TOTAL':30}{done:6}{sum(r['held'] for r in rows):6}{total:5}")
    print()
    if pending:
        nxt = pending[0]
        print(f"next: {nxt['category']} — {nxt['products'] - nxt['done']} products remaining, "
              f"{nxt['coverage']:.0%} carry a routable artifact")
    else:
        print("every category is finished.")

    if args.verbose:
        for row in rows:
            unfinished = {p: s for p, s in row["states"].items() if not s["done"]}
            if not unfinished:
                continue
            print(f"\n{row['category']}:")
            for slug, state in sorted(unfinished.items()):
                open_axes = [a for a, v in state["axes"].items() if v == "open"]
                abstained = [a for a, v in state["axes"].items() if v == "abstained"]
                bits = []
                if open_axes:
                    bits.append("open: " + ",".join(open_axes))
                if abstained:
                    bits.append("abstained: " + ",".join(abstained))
                if not state["prose"]:
                    bits.append("no verification line")
                print(f"  {slug:38} {'; '.join(bits)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
