"""Where the verification sweep has got to, derived from the corpus rather than stored.

`/goal` runs one category per invocation and has to know which one is next. That could be a
pointer in a file, and a pointer is a second copy of a fact the corpus already carries — it
desyncs the first time a category is finished by hand, or half-finished, or reverted. So there
is no pointer. This module reads `sources/` and works it out.

## What "done" means for a product

The bar agreed on 2026-08-08, and it is per product rather than per axis:

  * every axis carries a real `last_verified`, or abstains deliberately (a null value, which
    `evidence-and-freshness.md` explains for the 46 axes that have one), or the product is held;
  * `comments` ends in the canonical verification line, which is the prose half's proxy —
    `product-copy.md` has rules a checker cannot enforce, but the line is the one thing a
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

## Refreshing rather than finishing

Once a category is gate-clean it stays "done" forever, which is wrong the moment a confirmation
ages: `last_verified` is a claim about a day, and the map keeps moving. `--max-age-days` (or
`--since`) reads a confirmation older than the window as `stale` rather than `verified`, so the
same tooling that drove the first pass drives the recurring one. The prose ages on the same
clock, because the canonical verification line carries its own date.

Usage:
    uv run python -m build.sweep_status
    uv run python -m build.sweep_status --verbose
    uv run python -m build.sweep_status --next            # just the next category's slug
    uv run python -m build.sweep_status --max-age-days 30 # what has gone stale in a month
    uv run python -m build.sweep_status --since 2026-07-01
    uv run python -m build.sweep_status --retracting      # notes that correct themselves
    uv run python -m build.sweep_status --under-coverage  # bands their own note disowns
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AXES = ("openness", "adoption", "capability")
VALUE_KEY = {"openness": "score", "adoption": "level", "capability": "score"}
ARTIFACTS = ("github", "pypi", "npm", "crates", "huggingface_model", "huggingface_dataset")
VERIFIED_LINE = re.compile(r"Verified (\d{4}-\d{2}-\d{2}) via ")


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


def _on_or_after(value: object, cutoff: date | None) -> bool:
    """True when `value` is a date at or after the cutoff. No cutoff means any date passes."""
    if cutoff is None:
        return True
    if isinstance(value, date):
        return value >= cutoff
    try:
        return date.fromisoformat(str(value)) >= cutoff
    except (TypeError, ValueError):
        return False


def product_state(
    slug: str, product: dict, score: dict, held: dict, cutoff: date | None = None
) -> dict:
    """Per-product: which axes are settled, whether the prose is, and whether it is held.

    With a `cutoff`, a confirmation older than it counts as `stale` rather than `verified` -
    which is what turns the sweep from a one-time pass into a recurring refresh. An axis that
    was never confirmed is `open` whatever the cutoff, and unlike `check_freshness` there is no
    commit-date fallback here: the question this asks is "has anyone re-read this", and a commit
    date answers "did anyone touch the file", which is a different question.
    """
    axes = {}
    for axis in AXES:
        block = score.get(axis) or {}
        if block.get("last_verified"):
            axes[axis] = "verified" if _on_or_after(block["last_verified"], cutoff) else "stale"
        elif block.get(VALUE_KEY[axis]) is None:
            axes[axis] = "abstained"
        else:
            axes[axis] = "open"
    # The canonical verification line carries its own date, so the prose ages on the same clock.
    match = VERIFIED_LINE.search(str(product.get("comments") or ""))
    if not match:
        prose_state = "missing"
    elif _on_or_after(match.group(1), cutoff):
        prose_state = "verified"
    else:
        prose_state = "stale"
    prose = prose_state == "verified"
    return {
        "axes": axes,
        "prose": prose,
        "prose_state": prose_state,
        "held": slug in held,
        "done": slug in held or (
            all(v not in ("open", "stale") for v in axes.values()) and prose
        ),
    }


# A note that corrects itself in place. Every refresh appends rather than rewrites, so a note
# can now carry a superseded sentence AND its own retraction, and a reader cannot tell which
# half is current without reading to the end.
#
# NOT A GATE, deliberately. No checker can tell a superseded sentence from a legitimate
# history, and one that guessed would start deleting the reasoning these files exist to carry.
# This lists them for the next refresh pass, where a human is already reading the note.
RETRACTING = re.compile(
    r"superseded|that last sentence|no longer (?:appears|on (?:the|that) page|carried)"
    r"|dropped rather than carried forward|is now WRONG|EVIDENCE REPLACED|WITHDRAWN"
    r"|did not survive the read|is not on the cited page|BENCHMARK FIGURE SUPERSEDED",
    re.IGNORECASE,
)

# A note that says, in its own words, that the signal it banded does not measure the product's
# real use. `docs/reference/adoption.md` names the tell: "a note that describes the signal as
# understating the product, followed by a band recorded on that signal anyway." Both directions
# count — a CI-inflated download count is the same defect pointing the other way.
UNDERSTATES = re.compile(
    r"understates|minority channel|not the (?:product's )?primary (?:channel|distribution)"
    r"|primary distribution channel",
    re.IGNORECASE,
)
INFLATED = re.compile(r"inflated|anomalously high|mirror-inflated|CI/dependency traffic", re.IGNORECASE)


def _scores() -> dict[str, dict]:
    return {
        p.stem: (yaml.safe_load(p.read_text()) or {})
        for p in sorted((ROOT / "sources" / "scores").glob("*.yaml"))
    }


def retracting_notes() -> list[tuple[str, str, str]]:
    """(slug, axis, the phrase that matched) for notes that correct themselves in place."""
    found = []
    for slug, score in _scores().items():
        for axis in AXES:
            note = ((score.get(axis) or {}).get("note")) or ""
            match = RETRACTING.search(note)
            if match:
                found.append((slug, axis, match.group(0)))
    return found


def under_coverage() -> list[tuple[str, str, str]]:
    """(slug, direction, phrase) for measured bands whose own note disowns the measurement."""
    found = []
    for slug, score in _scores().items():
        adoption = score.get("adoption") or {}
        if adoption.get("signal_type") not in ("usage_volume", "stars_fallback"):
            continue
        note = adoption.get("note") or ""
        if (m := UNDERSTATES.search(note)):
            found.append((slug, "understates", m.group(0)))
        elif (m := INFLATED.search(note)):
            found.append((slug, "inflated", m.group(0)))
    return found


def survey(cutoff: date | None = None) -> list[dict]:
    cats, prods, scores, held, _ = load()
    rows = []
    for slug, cat in cats.items():
        roster = cat.get("products") or []
        states = {
            p: product_state(p, prods.get(p) or {}, scores.get(p) or {}, held, cutoff)
            for p in roster
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
    parser.add_argument(
        "--max-age-days", type=int,
        help="treat a confirmation older than this as needing a refresh",
    )
    parser.add_argument(
        "--since", help="treat a confirmation before this date (YYYY-MM-DD) as needing a refresh"
    )
    parser.add_argument(
        "--retracting", action="store_true",
        help="list notes that correct themselves in place, for the next refresh pass",
    )
    parser.add_argument(
        "--under-coverage", action="store_true",
        help="list measured bands whose own note disowns the measurement",
    )
    args = parser.parse_args()

    # Both are worklists rather than status, so they print and exit rather than joining the
    # per-category table. Exit 0 always: neither is a finding a PR can be asked to clear.
    if args.retracting:
        rows = retracting_notes()
        print(f"{len(rows)} note(s) correct themselves in place. A refresh pass should rewrite")
        print("each to its current reading — the history is in git.\n")
        for slug, axis, phrase in rows:
            print(f"  {f'{slug}.{axis}':<46} {phrase!r}")
        return 0

    if args.under_coverage:
        rows = under_coverage()
        print(f"{len(rows)} measured band(s) whose own note disowns the measurement.")
        print("docs/reference/adoption.md gives the remedy per case: count every channel and")
        print("sum, admit a lifetime average as a floor, or move to reported_traction.\n")
        for slug, direction, phrase in rows:
            print(f"  {slug:<28} {direction:<12} {phrase!r}")
        return 0

    if args.max_age_days is not None and args.since:
        parser.error("--max-age-days and --since say the same thing two ways; pass one")
    cutoff = None
    if args.max_age_days is not None:
        cutoff = date.today() - timedelta(days=args.max_age_days)
    elif args.since:
        cutoff = date.fromisoformat(args.since)

    rows = survey(cutoff)
    pending = [r for r in rows if r["done"] < r["products"]]

    if args.next:
        print(pending[0]["category"] if pending else "")
        return 0

    total = sum(r["products"] for r in rows)
    done = sum(r["done"] for r in rows)
    if cutoff:
        print(f"counting a confirmation before {cutoff} as needing a refresh\n")
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
                stale = [a for a, v in state["axes"].items() if v == "stale"]
                abstained = [a for a, v in state["axes"].items() if v == "abstained"]
                bits = []
                if open_axes:
                    bits.append("open: " + ",".join(open_axes))
                if stale:
                    bits.append("stale: " + ",".join(stale))
                if abstained:
                    bits.append("abstained: " + ",".join(abstained))
                if state["prose_state"] == "missing":
                    bits.append("no verification line")
                elif state["prose_state"] == "stale":
                    bits.append("prose line stale")
                print(f"  {slug:38} {'; '.join(bits)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
