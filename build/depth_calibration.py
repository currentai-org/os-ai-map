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
  O is the best band among the set's own components for that language (OWN_COMPONENTS), and C_i
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

import yaml

from build import lineage
from build.evidence_status import entry_status

ROOT = Path(__file__).resolve().parent.parent

# The 22 sets the 2026-10-30 dry run places in language_specific_eval_sets.
ROSTER: tuple[str, ...] = (
    "flores-plus", "fleurs", "belebele", "sib-200", "include-benchmark", "afrobench", "milu",
    "indicgenbench", "indicxtreme", "lahaja", "sea-helm", "seaexam", "thai-exam", "vmlu", "laobench",
    "indonlu", "arabicmmlu", "darijammlu", "turkishmmlu", "kazmmlu", "khayyam-challenge",
    "americasnlp-shared-task-data",
)

# The calibration's ownership claims, until `capability.own_components` carries them (R-2026-11-03-c).
# Each set's own slug is its own in every language unless scoped here. A scope is None (every
# language), ("only", languages) or ("except", languages).
FLORES_IN_NEW = frozenset({"bgc", "brx", "gbm", "gom", "hoj", "mup", "mwr"})
CROSSSUM_REUSED = frozenset({"ben", "guj", "hin", "mar", "nep", "pan", "pus", "tam", "tel", "urd"})
# INCLUDE's pool in these languages is the parent benchmark's own text (ArabicMMLU, Khayyam
# Challenge, TurkishMMLU): the lineage record names the parent, so the items are imported (D5).
INCLUDE_IMPORTED = frozenset({"ara", "fas", "tur"})
# Languages where INCLUDE says its pool joins existing benchmark data with exams it collected, with
# no per-language share: the lineage record gives them a second collection. Own as recorded; the
# sensitivity treats them as imported too.
INCLUDE_MIXED = frozenset({"deu", "fra", "ita", "lit", "pol", "por", "sqi", "vie", "zho"})

Scope = tuple[str, frozenset[str]] | None
OWN_COMPONENTS: dict[str, dict[str, Scope]] = {
    "include-benchmark": {"include-benchmark": ("except", INCLUDE_IMPORTED)},
    "sea-helm": {"sea-mt-bench-judge": None, "kalahi-judge": None},
    "indicxtreme": {"indiccopa": None, "indicqa": None, "indicxparaphrase": None,
                    "indicsentiment": None},
    "indicgenbench": {"flores-in": ("only", FLORES_IN_NEW),
                      "crosssum-in": ("except", CROSSSUM_REUSED), "xquad-in": None,
                      "xorqa-in": ("except", frozenset({"ben", "tel"}))},
}

LADDER = ((6400, 5), (1600, 4), (400, 3), (100, 2), (1, 1))


def band(count: int) -> int:
    """The count ladder's band for a qualifying count (R-2026-11-02-c)."""
    return next((b for lo, b in LADDER if count >= lo), 0)


def median_band(values: list[int]) -> int | None:
    """The median band, the lower of the two middle values' mean rounded down on an even count."""
    v = sorted(values)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) // 2


def own_ids(slug: str, language: str, own: dict[str, dict[str, Scope]]) -> set[str]:
    """The components that are the set's own items in one language."""
    scopes = {slug: None, **own.get(slug, {})}
    out = set()
    for comp, scope in scopes.items():
        if scope is None or (scope[0] == "only") == (language in scope[1]):
            out.add(comp)
    return out


def _qualifying(entry: dict) -> int:
    status = entry_status(entry)
    if status.reason == "measured_zero":
        return 0
    if entry.get("provenance") == "mixed":
        return entry["qualifying_count"]
    return entry["count"]


def _load(slug: str, root: Path) -> tuple[list[str], dict[str, list[dict]], Counter, object]:
    rec = yaml.safe_load((root / "sources/scores" / f"{slug}.yaml").read_text())
    prod = yaml.safe_load((root / "sources/products" / f"{slug}.yaml").read_text())
    cap = rec["capability"]
    pivots = set(cap.get("pivot_languages") or [])
    targets = [lang for lang in prod.get("languages") or [] if lang not in pivots]
    comps: dict[str, list[dict]] = {}
    tally: Counter = Counter()
    for e in cap.get("language_coverage") or []:
        s = entry_status(e)
        if s is None:
            continue
        tally[f"{s.status}/{s.reason}"] += 1
        if s.status == "unresolved":
            continue
        q = _qualifying(e)
        comps.setdefault(e["language"], []).append({
            "component": e["component"], "task": e["task"], "split": e["split"], "band": band(q)})
    return targets, comps, tally, cap.get("score")


def language_band(doc: dict, slug: str, language: str, comps: list[dict], *, loose: bool,
                  own: dict[str, dict[str, Scope]]) -> tuple[int, int]:
    """(corroborated band, face value) for one language."""
    mine = own_ids(slug, language, own)
    best = max((c["band"] for c in comps if c["component"] in mine), default=0)
    for i in comps:
        if i["component"] in mine or i["band"] == 0:
            continue
        backing = 0
        for j in comps:
            if j is i or j["band"] == 0:
                continue
            if j["component"] not in mine and j["task"] == i["task"]:
                continue
            s = lineage.pair_status(doc, i["component"], j["component"], language,
                                    a_task=i["task"], a_split=i["split"],
                                    b_task=j["task"], b_split=j["split"])
            if s.status == "independent" or (loose and s.status == "unverified"):
                backing = max(backing, j["band"])
        best = max(best, min(i["band"], backing + 1))
    return best, max((c["band"] for c in comps), default=0)


def _set_band(values: list[int], unknown: int) -> str | None:
    lo, hi = median_band(values + [0] * unknown), median_band(values + [5] * unknown)
    if lo is None:
        return None
    return str(lo) if lo == hi else f"unresolved ({lo}-{hi})"


def calibrate_set(doc: dict, slug: str, *, loose: bool = False,
                  own: dict[str, dict[str, Scope]] | None = None,
                  root: Path = ROOT) -> dict:
    """One set's calibration: band, face value, bonus and the per-language detail."""
    own = OWN_COMPONENTS if own is None else own
    targets, comps, tally, current = _load(slug, root)
    per = {lang: language_band(doc, slug, lang, comps[lang], loose=loose, own=own)
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


def second_slugs_as_imports() -> dict[str, dict[str, Scope]]:
    """Ownership with every second-slug claim dropped: only each set's own slug is its own."""
    return {slug: {c: s for c, s in scopes.items() if c == slug}
            for slug, scopes in OWN_COMPONENTS.items()}


def include_mixed_as_imports() -> dict[str, dict[str, Scope]]:
    """Ownership with INCLUDE's mixed-pool languages treated as imported as well."""
    return {**OWN_COMPONENTS,
            "include-benchmark": {"include-benchmark": ("except",
                                                        INCLUDE_IMPORTED | INCLUDE_MIXED)}}


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
    readings = {"second_slugs_as_imports": (second_slugs_as_imports(),
                                            ("indicxtreme", "indicgenbench", "sea-helm")),
                "include_mixed_as_imports": (include_mixed_as_imports(), ("include-benchmark",))}
    return {name: {slug: calibrate_set(doc, slug, own=own, root=root) for slug in slugs}
            for name, (own, slugs) in readings.items()}


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
