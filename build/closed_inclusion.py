"""Survey the closed side of the map against the inclusion principle, and measure what
removing any one of those products would cost.

Run it with `uv run python -m build.closed_inclusion` (`--json` for the machine form,
`--all` to list every closed product rather than only the ones below the line).

**This module computes no verdict and gates nothing.** The principle it applies is written
in `docs/architecture/adr-005-closed-product-inclusion.md`, and that document is guidance a
curator reads, not a predicate a build enforces. Nothing here exits non-zero because of what
it found, nothing here is wired into `build/preflight.py`, and no test asserts where the line
falls. A product sitting below the line is a reason to look at it, and the look is a person's.

Three things it does produce, and the reason each is separate:

1. **The survey** — the closed population split into ABOVE the line, BELOW it, and
   UNMEASURED. Three states, never two. "Below" means the product was measured and came in
   under the line; "unmeasured" means there was nothing to measure it with. They look alike in
   a count and need opposite work — one is a curatorial question, the other is a missing score
   — so they are never summed here.
2. **The census** — one row per product that is not above the line, carrying the values it was
   judged on and how its category looks around it.
3. **The measured delta** — for each census row, the category stage and gap set recomputed
   with that product withheld from its roster and the payload rebuilt. An earlier design
   asserted that a non-leading closed product could not move a stage; that is false
   (`build/serialize.py`'s `mature_anywhere` is computed over ALL products, so a closed
   product can hold a category off Stage 0 and can fire the `openness` gap), so the delta is
   measured per product rather than promised. Where it moves something, the row is marked a
   decision for Carl rather than left in the list.

The population is the one ADR-005 governs: `openness.score <= 1`. That is NOT the serializer's
closed bucket, which is wider — `_gap_bucket` also collapses `documented` and `restricted` into
`closed` for gap detection. See the ADR on why the policy reads the score and the gap engine
reads the bucket, and do not swap one for the other.

`docs/reference/gap-analysis.md` is the authority on what `stage` and `gaps` mean.
"""
import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path

from build.serialize import ROOT, build_payload

# The screen Carl set on 2026-09-20, as a starting point for a judgement: `overall_score >= 4`,
# read against `capability` where the overall score is null because adoption abstained. It is a
# policy choice and not a measurement — do not derive it from the corpus, and do not tune it to
# make a count come out round. ADR-005 carries the reasoning.
LINE = 4

# The population ADR-005 governs. Read the module docstring before widening it.
CLOSED_MAX_OPENNESS_SCORE = 1

ABOVE = "above the line"
BELOW = "below the line"
UNMEASURED = "unmeasured"

# What the screen actually read for a given product, carried on every row so a reader never has
# to infer which branch fired.
JUDGED_OVERALL = "overall score"
JUDGED_CAPABILITY = "capability (overall score abstained)"
JUDGED_NOTHING = "nothing recorded"


def is_closed(row: dict) -> bool:
    """The governed population: a product whose openness score is at or below the closed floor.

    `openness.score` is the computed 0-5 openness number, not the class and not the bucket.
    A product with no score at all is not in the population — the map has none today, and
    guessing one would put a product under a policy on the strength of a missing value.
    """
    score = (row.get("openness") or {}).get("score")
    return score is not None and score <= CLOSED_MAX_OPENNESS_SCORE


def screen(row: dict) -> tuple[str, str]:
    """Place one product against the line. Returns (state, what the state was read from).

    `overall_score` first. Where it is null — which for a closed hosted API usually means there
    is no public download channel to count, not that the product is weak — read `capability`
    instead. Where neither exists the product is UNMEASURED, which is a statement about the map
    and not about the product.
    """
    overall = row.get("overall_score")
    if overall is not None:
        return (ABOVE if overall >= LINE else BELOW), JUDGED_OVERALL
    capability = (row.get("capability") or {}).get("score")
    if capability is None:
        return UNMEASURED, JUDGED_NOTHING
    return (ABOVE if capability >= LINE else BELOW), JUDGED_CAPABILITY


def load_inputs(root: Path | None = None) -> tuple[dict, dict]:
    """The source tree and the frozen long-tail snapshot, loaded once and reused.

    Loading `sources/` is the slow part (seconds); a payload rebuild off it is milliseconds,
    which is what makes a per-product withheld rebuild affordable at all.
    """
    from build.validate import load_sources
    root = root or ROOT
    sources = load_sources(root)
    frozen = json.loads((root / "sources" / "snapshots" / "long_tail.json").read_text())
    return sources, frozen


@contextmanager
def withheld(sources: dict, slug: str):
    """Drop one slug from every category roster for the duration of the block, then restore.

    Mutate-and-restore rather than deep-copying the whole source tree: the tree is large, this
    runs once per census row, and only the rosters are read by the stage engine. The restore is
    in a `finally` so a raised exception cannot leave the caller holding a corpus with a product
    missing from it.

    A slug is looked for in EVERY category rather than only its own, so a product rostered in
    more than one place is withheld from all of them and the diff below still tells the truth.
    """
    saved = []
    for cid, cat in sources["categories"].items():
        roster = cat.get("products") or []
        if slug in roster:
            saved.append((cid, list(roster)))
            cat["products"] = [s for s in roster if s != slug]
    try:
        yield
    finally:
        for cid, roster in saved:
            sources["categories"][cid]["products"] = roster


def stage_and_gap_diff(baseline: dict, rebuilt: dict) -> dict:
    """Every category whose stage or gap set differs between two payloads.

    Diffed across ALL categories, not just the withheld product's own, so a product rostered
    twice — or a category effect nobody predicted — cannot slip past a narrower comparison.
    """
    moved = {}
    for cid, before in baseline["categories"].items():
        after = rebuilt["categories"].get(cid)
        if after is None:
            moved[cid] = {"stage_before": before["stage"], "stage_after": None,
                          "gaps_before": before["gaps"], "gaps_after": None}
            continue
        if before["stage"] != after["stage"] or before["gaps"] != after["gaps"]:
            moved[cid] = {"stage_before": before["stage"], "stage_after": after["stage"],
                          "gaps_before": before["gaps"], "gaps_after": after["gaps"]}
    return moved


def _category_context(cat: dict, slug: str) -> dict:
    """How the product's own category looks around it.

    The point of test 2 is that a closed product marks the frontier open products are measured
    against. Whether a given one is doing that job is partly a question about its neighbours:
    how many closed products in the same category are already above the line, what the best
    closed score in the category is, and how the open side compares. Reported, not scored.
    """
    closed = [p for p in cat["products"] if is_closed(p)]
    peers_above = [p["slug"] for p in closed
                   if p["slug"] != slug and screen(p)[0] == ABOVE]
    closed_scores = [(p.get("overall_score"), p["slug"]) for p in closed
                     if p.get("overall_score") is not None]
    open_scores = [(p.get("overall_score"), p["slug"]) for p in cat["products"]
                   if (p.get("openness") or {}).get("bucket") == "open"
                   and p.get("overall_score") is not None]
    best_closed = max(closed_scores, default=(None, None))
    best_open = max(open_scores, default=(None, None))
    return {
        "category_stage": cat["stage"],
        "category_gaps": list(cat["gaps"]),
        "closed_in_category": len(closed),
        "closed_peers_above_the_line": peers_above,
        "best_closed_overall_score": best_closed[0],
        "best_closed_slug": best_closed[1],
        "best_fully_open_overall_score": best_open[0],
        "best_fully_open_slug": best_open[1],
    }


def survey(payload: dict) -> dict:
    """Split the closed population into the three states, with the sub-counts that make the
    split checkable against the measurement ADR-005 was written from.

    Derived from the payload every time. Nothing here is pinned: if the corpus moves, these
    numbers move with it, which is the point of a survey.
    """
    states = {ABOVE: [], BELOW: [], UNMEASURED: []}
    detail = {"scored_at_or_above_line": 0, "scored_below_line": 0,
              "overall_score_null": 0, "null_with_capability_at_or_above_line": 0,
              "null_with_capability_below_line": 0, "null_with_no_capability": 0}
    for cid, cat in payload["categories"].items():
        for row in cat["products"]:
            if not is_closed(row):
                continue
            state, judged = screen(row)
            states[state].append((cid, row))
            if judged == JUDGED_OVERALL:
                key = "scored_at_or_above_line" if state == ABOVE else "scored_below_line"
                detail[key] += 1
            else:
                detail["overall_score_null"] += 1
                if judged == JUDGED_NOTHING:
                    detail["null_with_no_capability"] += 1
                elif state == ABOVE:
                    detail["null_with_capability_at_or_above_line"] += 1
                else:
                    detail["null_with_capability_below_line"] += 1
    return {"population": sum(len(v) for v in states.values()),
            "counts": {k: len(v) for k, v in states.items()},
            "detail": detail, "states": states}


def census(sources: dict, frozen: dict, baseline: dict | None = None,
           states: tuple[str, ...] = (BELOW, UNMEASURED)) -> list[dict]:
    """One row per closed product in `states`, each carrying a REBUILT stage and gap set.

    The delta is measured: the product is withheld from its roster, the whole payload is
    rebuilt, and the result is diffed against the baseline. A row that says nothing moved says
    it because a rebuild was run and came back identical, not because a rule promised it would.
    """
    baseline = baseline or build_payload(sources, frozen, generated="1970-01-01")
    surveyed = survey(baseline)
    rows = []
    for state in states:
        for cid, row in surveyed["states"][state]:
            slug = row["slug"]
            with withheld(sources, slug):
                rebuilt = build_payload(sources, frozen, generated="1970-01-01")
            moved = stage_and_gap_diff(baseline, rebuilt)
            # The rebuilt numbers for the product's OWN category, carried whether or not they
            # differ. A row that says "nothing moved" has to show the recomputed stage and gap
            # set it is saying that about; an unevidenced "no effect" is the claim this census
            # exists to stop making.
            own_after = rebuilt["categories"][cid]
            state_now, judged = screen(row)
            rows.append({
                "slug": slug,
                "product": row["product"],
                "org": row.get("org", ""),
                "category": cid,
                "category_label": baseline["categories"][cid]["label"],
                "state": state_now,
                "judged_on": judged,
                "overall_score": row.get("overall_score"),
                "adoption": (row.get("adoption") or {}).get("level"),
                "capability": (row.get("capability") or {}).get("score"),
                "openness_score": (row.get("openness") or {}).get("score"),
                "openness_class": (row.get("openness") or {}).get("class"),
                **_category_context(baseline["categories"][cid], slug),
                "stage_with_product": baseline["categories"][cid]["stage"],
                "gaps_with_product": list(baseline["categories"][cid]["gaps"]),
                "stage_withheld": own_after["stage"],
                "gaps_withheld": list(own_after["gaps"]),
                "withheld_moves": moved,
                "disposition": ("decision for Carl — withholding it moves a category"
                                if moved else "no category movement measured"),
            })
    rows.sort(key=lambda r: (r["category"], r["slug"]))
    return rows


def _fmt(v) -> str:
    return "—" if v is None else str(v)


def _stage_str(stage: dict | None, gaps: list[str] | None) -> str:
    if stage is None:
        return "category absent"
    return f"stage {stage['num']} {stage['name']} [{', '.join(gaps or []) or 'no gaps'}]"


def _report(surveyed: dict, rows: list[dict]) -> str:
    d = surveyed["detail"]
    out = [
        "Closed-product inclusion survey",
        f"  population (openness score <= {CLOSED_MAX_OPENNESS_SCORE}): "
        f"{surveyed['population']}",
        "",
        "  Three states. 'Below' and 'unmeasured' are never summed: one is a curatorial",
        "  question about a product, the other is a missing measurement on our side, and",
        "  they need opposite work.",
        f"    {ABOVE:<14} {surveyed['counts'][ABOVE]}",
        f"    {BELOW:<14} {surveyed['counts'][BELOW]}",
        f"    {UNMEASURED:<14} {surveyed['counts'][UNMEASURED]}",
        "",
        f"  read from overall_score:  >= {LINE}: {d['scored_at_or_above_line']}"
        f"   < {LINE}: {d['scored_below_line']}",
        f"  overall_score null:       {d['overall_score_null']}"
        f"  (capability >= {LINE}: {d['null_with_capability_at_or_above_line']},"
        f" capability < {LINE}: {d['null_with_capability_below_line']},"
        f" no capability: {d['null_with_no_capability']})",
        "",
        "=" * 78,
        f"Census — {len(rows)} products not above the line, grouped by category.",
        "",
        "This is advisory and it is not a removal list. Each product carries the values it",
        "was read on, how its category looks around it, and the category's stage and gap set",
        "RECOMPUTED with that product withheld and the whole payload rebuilt. The recomputed",
        "line is printed whether or not it differs, because a row claiming no effect has to",
        "show the numbers it is claiming it about.",
    ]
    current = None
    for r in rows:
        if r["category"] != current:
            current = r["category"]
            out += ["", f"{r['category']}  —  {r['category_label']}",
                    f"  as built: {_stage_str(r['stage_with_product'], r['gaps_with_product'])}"
                    f"; {r['closed_in_category']} closed products, best closed overall score "
                    f"{_fmt(r['best_closed_overall_score'])} ({_fmt(r['best_closed_slug'])}); "
                    f"best fully-open {_fmt(r['best_fully_open_overall_score'])} "
                    f"({_fmt(r['best_fully_open_slug'])})"]
        out.append(f"    {r['slug']:<44} {r['state']:<14} "
                   f"overall {_fmt(r['overall_score']):>4}  adoption {_fmt(r['adoption']):>4}  "
                   f"capability {_fmt(r['capability']):>4}  "
                   f"(read on {r['judged_on']})")
        out.append(f"      closed peers already above the line: "
                   f"{len(r['closed_peers_above_the_line'])}"
                   + (f" — {', '.join(r['closed_peers_above_the_line'][:6])}"
                      if r["closed_peers_above_the_line"] else ""))
        moved = r["withheld_moves"]
        out.append(f"      withheld: "
                   f"{_stage_str(r['stage_withheld'], r['gaps_withheld'])}"
                   + ("   <-- MOVES; see the decisions section" if moved
                      else "   (identical to as-built; rebuilt, not assumed)"))
        for cid, m in moved.items():
            if cid != r["category"]:
                out.append(f"      withheld also moves {cid}: "
                           f"{_stage_str(m['stage_before'], m['gaps_before'])} -> "
                           f"{_stage_str(m['stage_after'], m['gaps_after'])}")

    decisions = [r for r in rows if r["withheld_moves"]]
    out += ["", "=" * 78,
            f"Decisions for Carl — {len(decisions)} product(s) whose withholding moves a stage "
            "or a gap."]
    if decisions:
        out += ["",
                "These are not candidates for anything. The map's published shape rests on "
                "them,",
                "so what happens to them is a ruling rather than a curation call."]
        for r in decisions:
            for cid, m in r["withheld_moves"].items():
                out.append(f"  {r['slug']} -> {cid}: "
                           f"{_stage_str(m['stage_before'], m['gaps_before'])} -> "
                           f"{_stage_str(m['stage_after'], m['gaps_after'])}")
    else:
        out.append("  none")
    out += ["",
            "The detector behind the recomputed lines is exercised in",
            "tests/test_closed_inclusion.py, on a synthetic corpus built so that withholding",
            "one closed product does move a stage and a gap set. A run where nothing moves is",
            "therefore a measurement rather than a silent no-op."]

    unmeasured = [r for r in rows if r["state"] == UNMEASURED]
    out += ["", "=" * 78,
            f"Unmeasured — {len(unmeasured)} product(s) with neither an overall score nor a",
            "capability. The line has nothing to say about these; they need a measurement, not",
            "a judgement, and counting them with the products below the line would hide that."]
    for r in unmeasured:
        out.append(f"  {r['slug']} ({r['category_label']})")
    if not unmeasured:
        out.append("  none")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Survey the closed side of the map against the inclusion principle in "
                    "docs/architecture/adr-005-closed-product-inclusion.md, and measure what "
                    "withholding each product below the line would do to its category. "
                    "Advisory: it gates nothing and always exits 0.")
    parser.add_argument("--json", action="store_true",
                        help="emit the survey and census as JSON")
    parser.add_argument("--all", action="store_true",
                        help="census every closed product, including those above the line")
    args = parser.parse_args(argv)
    sources, frozen = load_inputs()
    baseline = build_payload(sources, frozen, generated="1970-01-01")
    surveyed = survey(baseline)
    states = (ABOVE, BELOW, UNMEASURED) if args.all else (BELOW, UNMEASURED)
    rows = census(sources, frozen, baseline=baseline, states=states)
    if args.json:
        print(json.dumps({"line": LINE, "population": surveyed["population"],
                          "counts": surveyed["counts"], "detail": surveyed["detail"],
                          "census": rows}, indent=2, ensure_ascii=False))
    else:
        print(_report(surveyed, rows))
    # Always 0. This is a survey; there is no finding it could make that should fail a build.
    return 0


if __name__ == "__main__":
    sys.exit(main())
