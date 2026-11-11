"""Depth calibration of the evaluation-set roster: the bands the ruled method computes, read-only.

R-2026-11-02-c asks for the full band distribution to be inspected before the depth ladder changes
any score, so the calibration has to be reproducible from the repository alone. This module
computes it from `capability.language_coverage`, the lineage registry and the rulings, prints one
row per set, and writes nothing to `sources/`. It is not the ladder: no published score reads it,
and the ladder PR replaces it (R-2026-10-30-l). The record of the calibration and its method is
docs/sweeps/2026-11-03-depth-calibration-full-roster.md; docs/reference/capability.md is normative
on every rule it applies.

The method, in order:

- Entries: only official-evaluation entries count (R-2026-11-01-d). `build.evidence_status` gives
  each its status; an unresolved entry gives no band, a measured zero band 0, and otherwise the
  qualifying count (`qualifying_count` on a `mixed` entry) gives a band on the count ladder 100 /
  400 / 1,600 / 6,400 (R-2026-11-02-b, -c, R-2026-11-03-b, -h).
- Within a task: the highest band of one component, never a sum (R-2026-11-02-g).
- Across tasks: D = max(O, max over imported components i of min(b_i, C_i + 1)) (R-2026-11-02-k).
  O is the best band among the set's own components for that language (`capability.own_components`,
  read through `build.own_components.is_own`), and C_i
  the best band among the language's other components independent of i under
  `build.lineage.pair_status`; imports on the same task never back one another (R-2026-11-01-c).
- Across languages: the median over target languages, with unmeasured ones filled at 0 and at 5;
  it stands only where both agree (R-2026-11-01-a). Bonus median + 0.5 x (1 - 1/n) over languages
  above zero (R-2026-10-30-i, R-2026-11-01-b). Face value is the same median of each language's
  highest single task band, uncapped (R-2026-11-02-o).

Run (a) gives unverified lineage pairs no backing and run (b) treats them as independent
(R-2026-11-02-i). `--sensitivity` adds the other two readings the record reports.

Usage:
    uv run python -m build.depth_calibration [--sensitivity] [--set SLUG] [--json OUT]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from build import lineage
from build.depth_ladder import (  # noqa: F401  (re-exported: the calibration's tests and record use them)
    LADDER,
    ROOT,
    band,
    language_detail,
    load_set,
    median_band,
    record_claims,
)
from build.depth_ladder import set_band as _set_band
from build.own_components import without_mixed_pools, without_second_slugs

# The 22 sets the 2026-10-30 dry run places in language_specific_eval_sets.
ROSTER: tuple[str, ...] = (
    "flores-plus", "fleurs", "belebele", "sib-200", "include-benchmark", "afrobench", "milu",
    "indicgenbench", "indicxtreme", "lahaja", "sea-helm", "seaexam", "thai-exam", "vmlu", "laobench",
    "indonlu", "arabicmmlu", "darijammlu", "turkishmmlu", "kazmmlu", "khayyam-challenge",
    "americasnlp-shared-task-data",
)


def _load(slug: str, root: Path) -> tuple[list[str], dict[str, list[dict]], Counter, object]:
    loaded = load_set(slug, root)
    return loaded["targets"], loaded["comps"], loaded["tally"], loaded["score"]


def language_band(doc: dict, slug: str, language: str, comps: list[dict], *, loose: bool,
                  claims: list[dict] | None) -> tuple[int, int]:
    """(corroborated band, face value) for one language, by `build.depth_ladder`."""
    d = language_detail(doc, slug, language, comps, loose=loose, claims=claims)
    return d["band"], d["face_value"]


def calibrate_set(doc: dict, slug: str, *, loose: bool = False,
                  claims: list[dict] | None = None, root: Path = ROOT) -> dict:
    """One set's calibration: band, face value, bonus and the per-language detail.

    `claims` replaces the record's own `capability.own_components`, for the sensitivity readings.
    """
    claims = record_claims(slug, root) if claims is None else claims
    targets, comps, tally, current = _load(slug, root)
    per = {lang: language_band(doc, slug, lang, comps[lang], loose=loose, claims=claims)
           for lang in targets if lang in comps}
    unknown = len(targets) - len(per)
    bands = [v[0] for v in per.values()]
    result = _set_band(bands, unknown)
    bonus = None
    above = sum(1 for b in bands if b > 0)
    if result is not None and not result.startswith("unresolved") and above:
        bonus = round(int(result) + 0.5 * (1 - 1 / above), 2)
    return {
        "band": result,
        "face_value": _set_band([v[1] for v in per.values()], unknown),
        "bonus": bonus,
        "targets": len(targets),
        "measured": len(per),
        "capped": sorted(lang for lang, (d, face) in per.items() if d < face),
        "distribution": dict(sorted(Counter(bands).items())),
        "status_tally": dict(sorted(tally.items())),
        "score_now": current,
        "per_language": {lang: v[0] for lang, v in sorted(per.items())},
    }


def second_slugs_as_imports(slug: str, root: Path = ROOT) -> list[dict]:
    """The set's claims with every second-slug claim dropped: only its own slug can be its own."""
    return without_second_slugs(slug, record_claims(slug, root))


def mixed_pools_as_imports(slug: str, root: Path = ROOT) -> list[dict]:
    """The set's claims with each claim's mixed-pool languages treated as imported as well."""
    return without_mixed_pools(record_claims(slug, root))


def calibrate(doc: dict | None = None, *, root: Path = ROOT) -> dict:
    """Every roster set under runs (a) and (b)."""
    doc = lineage.load() if doc is None else doc
    return {slug: {"a": calibrate_set(doc, slug, root=root),
                   "b": calibrate_set(doc, slug, loose=True, root=root)}
            for slug in ROSTER}


def summary(results: dict) -> dict:
    """The headline figures: which sets reach band 5, how many resolve, whether (a) and (b) agree."""
    fives = [s for s, r in results.items() if r["a"]["band"] == "5"]
    resolved = [s for s, r in results.items()
                if r["a"]["band"] and not r["a"]["band"].startswith("unresolved")]
    return {"sets": len(results), "band_5": fives, "resolved": len(resolved),
            "one_third_trigger": round(len(results) / 3, 1),
            "runs_disagree": [s for s, r in results.items() if r["a"]["band"] != r["b"]["band"]]}


def sensitivity(doc: dict | None = None, *, root: Path = ROOT) -> dict:
    """The two ownership readings the record reports beside runs (a) and (b)."""
    doc = lineage.load() if doc is None else doc
    # The sets each reading changes: those with a second-slug claim, and those with a mixed pool.
    second = [s for s in ROSTER if any(c["component"] != s for c in record_claims(s, root))]
    mixed = [s for s in ROSTER if any(c.get("mixed_languages") for c in record_claims(s, root))]
    readings = {"second_slugs_as_imports": (second_slugs_as_imports, second),
                "include_mixed_as_imports": (mixed_pools_as_imports, mixed)}
    return {name: {slug: calibrate_set(doc, slug, claims=reading(slug, root), root=root)
                   for slug in slugs}
            for name, (reading, slugs) in readings.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sensitivity", action="store_true",
                    help="also print the second-slug and INCLUDE ownership readings")
    ap.add_argument("--set", dest="slug", help="print one set's per-language detail as JSON")
    ap.add_argument("--json", type=Path, help="write every result to this file")
    args = ap.parse_args()
    doc = lineage.load()
    results = calibrate(doc)
    for slug, r in results.items():
        a, b = r["a"], r["b"]
        print(f"{slug:30s} now {a['score_now']}  (a) {a['band']!s:17s} (b) {b['band']!s:17s} "
              f"face {a['face_value']!s:17s} bonus {a['bonus']!s:5s} "
              f"measured {a['measured']}/{a['targets']}  capped {len(a['capped'])}")
    s = summary(results)
    print(f"\nband 5: {len(s['band_5'])} of {s['sets']} ({', '.join(s['band_5']) or 'none'}); "
          f"resolved {s['resolved']} of {s['sets']}; one-third trigger at {s['one_third_trigger']}; "
          f"runs (a) and (b) disagree on {len(s['runs_disagree'])}")
    out = {"results": results, "summary": s}
    if args.sensitivity:
        out["sensitivity"] = sensitivity(doc)
        for name, sets in out["sensitivity"].items():
            for slug, r in sets.items():
                print(f"{name}: {slug} {r['band']} bonus {r['bonus']} capped {len(r['capped'])} "
                      f"{r['distribution']}")
    if args.slug:
        print(json.dumps(results[args.slug], indent=1))
    if args.json:
        args.json.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
