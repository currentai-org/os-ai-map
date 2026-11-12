"""The depth ladder: an evaluation set's capability band, computed from its evidence.

`language_specific_eval_sets` is the one category whose capability band `build/` computes rather
than records from a curator's judgment. This module computes it from `capability.language_coverage`,
`capability.own_components`, the lineage registry and the rulings, and returns the band together
with every figure published beside it (R-2026-11-02-o). The method was calibrated on the full roster
(docs/sweeps/2026-11-03-depth-calibration-full-roster.md, R-2026-11-07-a); docs/reference/capability.md,
"The depth ladder", is normative on every rule here.

The method, in order:

- Entries: only official-evaluation entries count (R-2026-11-01-d). `build.evidence_status` gives
  each its status. An unresolved entry gives no band; a measured zero gives band 0; otherwise the
  qualifying count (`qualifying_count` on a `mixed` entry) gives a band on the count ladder 100 /
  400 / 1,600 / 6,400 (R-2026-11-02-b, -c, R-2026-11-03-b, -h).
- Within a task: the highest band of one component, never a sum (R-2026-11-02-g).
- Across tasks: D = max(O, max over imported components i of min(b_i, C_i + 1)) (R-2026-11-02-k).
  O is the best band among the set's own components for that language (`build.own_components`),
  and C_i the best band among the language's other components independent of i under
  `build.lineage.pair_status`; imports on the same task never back one another (R-2026-11-01-c).
- Across languages: the median over target languages, with unmeasured ones filled at 0 and at 5;
  it stands only where both agree (R-2026-11-01-a). Bonus median + 0.5 x (1 - 1/n) over languages
  above zero (R-2026-10-30-i, R-2026-11-01-b).

Three different things, kept apart (R-2026-11-02-b, -k):

- Statistical precision is what one component's count can resolve. On the count ladder every band
  is a provisional ceiling, not an estimated confidence interval (R-2026-11-02-d, -e).
- Corroborated depth is the band after the corroboration policy caps imports by their independent
  backing. It is an evidence-aggregation policy, not a precision estimate.
- The published capability band is the corroborated depth of the set, with the face-value band,
  the best original band, task count, completeness, cap status, evidence status and the
  unverified-lineage sensitivity beside it.
"""
from __future__ import annotations

import copy
import functools
from collections import Counter
from pathlib import Path

import yaml

from build.lineage import load as load_lineage, pair_status
from build.evidence_status import entry_status
from build.own_components import is_own

ROOT = Path(__file__).resolve().parent.parent
CATEGORY = "language_specific_eval_sets"
BASIS = "evaluation_depth"

LADDER = ((6400, 5), (1600, 4), (400, 3), (100, 2), (1, 1))

# Why a set's band does not stand, as a published code and its plain reading. The code is derived
# from the entries' own statuses (`unresolved_reason`), never written by hand.
UNRESOLVED_REASONS: dict[str, str] = {
    "no_measurement_model": "no approved measurement model for its task family",
    "no_official_split": "official evaluation split size not established",
    "provenance_unknown": "qualifying provenance not established",
    "review_scope_unstated": "human-review scope not established",
    "unit_not_countable": "no measurement model reads its unit",
    "evidence_incomplete": "too few target languages measured for the median to stand",
}


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


def set_band(values: list[int], unknown: int) -> str | None:
    """The robust median as a string: a band, `unresolved (lo-hi)`, or None with no evidence."""
    lo, hi = median_band(values + [0] * unknown), median_band(values + [5] * unknown)
    if lo is None:
        return None
    return str(lo) if lo == hi else f"unresolved ({lo}-{hi})"


@functools.lru_cache(maxsize=4096)
def _parse(path: str, mtime_ns: int, size: int):
    return yaml.safe_load(Path(path).read_text())


def _read_yaml(path: Path):
    """Parse a source file once per on-disk version.

    `compute` runs once per set inside every `build_payload`, and the closed-product census
    rebuilds the payload once per withheld product, so the same two files were re-parsed
    thousands of times per run. The cache key carries the file's mtime and size, so an edit on
    disk is re-read, and a deep copy is returned so no caller can mutate a shared parse.
    """
    st = path.stat()
    return copy.deepcopy(_parse(str(path), st.st_mtime_ns, st.st_size))


def _qualifying(entry: dict) -> int:
    status = entry_status(entry)
    if status.reason == "measured_zero":
        return 0
    if entry.get("provenance") == "mixed":
        return entry["qualifying_count"]
    return entry["count"]


def record_claims(slug: str, root: Path = ROOT) -> list[dict]:
    """The set's `capability.own_components` claims, as its score record states them."""
    rec = _read_yaml(root / "sources/scores" / f"{slug}.yaml")
    return list((rec.get("capability") or {}).get("own_components") or [])


def load_set(slug: str, root: Path = ROOT) -> dict:
    """A set's targets, countable components per language, entry-status tally and raw entries."""
    rec = _read_yaml(root / "sources/scores" / f"{slug}.yaml")
    prod = _read_yaml(root / "sources/products" / f"{slug}.yaml")
    cap = rec["capability"]
    pivots = set(cap.get("pivot_languages") or [])
    targets = [lang for lang in prod.get("languages") or [] if lang not in pivots]
    comps: dict[str, list[dict]] = {}
    tally: Counter = Counter()
    entries = [e for e in cap.get("language_coverage") or [] if isinstance(e, dict)]
    for e in entries:
        s = entry_status(e)
        if s is None:
            continue
        tally[f"{s.status}/{s.reason}"] += 1
        if s.status == "unresolved":
            continue
        q = _qualifying(e)
        comps.setdefault(e["language"], []).append({
            "component": e["component"], "language": e["language"], "task": e["task"],
            "split": e["split"], "band": band(q), "status": s.status})
    return {"targets": targets, "comps": comps, "tally": tally, "entries": entries,
            "score": cap.get("score")}


def language_detail(doc: dict, slug: str, language: str, comps: list[dict], *, loose: bool,
                    claims: list[dict] | None) -> dict:
    """One language's corroborated band, face value, own band, and why a cap binds.

    `loose` treats unverified lineage pairs as independent, for the sensitivity reading
    (R-2026-11-02-i).
    """
    for c in comps:
        c["own"] = is_own(slug, {**c, "language": language}, claims)
    own_band = max((c["band"] for c in comps if c["own"]), default=None)
    best = own_band or 0
    best_from = max((c for c in comps if c["own"]), key=lambda c: c["band"], default=None)
    for i in comps:
        if i["own"] or i["band"] == 0:
            continue
        backing, backer = 0, None
        for j in comps:
            if j is i or j["band"] == 0:
                continue
            if not j["own"] and j["task"] == i["task"]:
                continue
            s = pair_status(doc, i["component"], j["component"], language,
                                    a_task=i["task"], a_split=i["split"],
                                    b_task=j["task"], b_split=j["split"])
            if (s.status == "independent" or (loose and s.status == "unverified")) \
                    and j["band"] > backing:
                backing, backer = j["band"], j
        i["backer"] = backer
        got = min(i["band"], backing + 1)
        if got > best:
            best, best_from = got, i
    face = max(comps, key=lambda c: c["band"], default=None)
    detail = {
        "band": best,
        "face_value": face["band"] if face else 0,
        "own_band": own_band,
        "set_by": best_from["component"] if best_from else None,
        "statuses": sorted({c.get("status", "provisional") for c in comps}),
        "tasks": sorted({c["task"] for c in comps if c["band"] > 0}),
    }
    if face and best < face["band"]:
        # Why the cap binds: which component gave the face value, which independent component
        # backed it (if any), and which of its pairings were dependent or unverified.
        pairs = {"dependent": [], "unverified": []}
        for j in comps:
            if j is face or j["band"] == 0 or (not j["own"] and j["task"] == face["task"]):
                continue
            s = pair_status(doc, face["component"], j["component"], language,
                                    a_task=face["task"], a_split=face["split"],
                                    b_task=j["task"], b_split=j["split"])
            if s.status in pairs:
                pairs[s.status].append(j["component"])
        backer = face.get("backer")
        detail["cap"] = {
            "face_component": face["component"],
            "backing_component": backer["component"] if backer else None,
            "backing_band": backer["band"] if backer else 0,
            "dependent": sorted(set(pairs["dependent"])),
            "unverified": sorted(set(pairs["unverified"])),
        }
    return detail


def unresolved_reason(loaded: dict, measured: int) -> str:
    """Why a set's band does not stand, from its entries' statuses (UNRESOLVED_REASONS)."""
    entries = loaded["entries"]
    official = [e for e in entries if e.get("official_eval")]
    if not official:
        return "no_official_split"
    if measured:
        return "evidence_incomplete"
    reasons = Counter()
    for e in official:
        s = entry_status(e)
        if s is None or s.status != "unresolved":
            continue
        if s.reason == "depth_unknown":
            if e.get("provenance") == "machine_translated" and e.get("human_validated") is True:
                reasons["review_scope_unstated"] += 1
            else:
                reasons["provenance_unknown"] += 1
        else:
            reasons[s.reason] += 1
    return reasons.most_common(1)[0][0] if reasons else "evidence_incomplete"


def compute(doc: dict, slug: str, *, claims: list[dict] | None = None, root: Path = ROOT) -> dict:
    """One set's published depth result: the band and every companion figure (R-2026-11-02-o)."""
    claims = record_claims(slug, root) if claims is None else claims
    loaded = load_set(slug, root)
    targets, comps = loaded["targets"], loaded["comps"]
    per = {lang: language_detail(doc, slug, lang, comps[lang], loose=False, claims=claims)
           for lang in targets if lang in comps}
    loose = {lang: language_detail(doc, slug, lang, comps[lang], loose=True, claims=claims)["band"]
             for lang in targets if lang in comps}
    unknown = len(targets) - len(per)
    bands = [d["band"] for d in per.values()]
    result = set_band(bands, unknown)
    resolved = result is not None and not result.startswith("unresolved")
    above = sum(1 for b in bands if b > 0)
    own = {lang: d["own_band"] for lang, d in per.items() if d["own_band"] is not None}
    own_result = set_band(list(own.values()), len(targets) - len(own)) if own else None
    capped = {lang: d["cap"] for lang, d in sorted(per.items()) if "cap" in d}
    statuses = {s for d in per.values() for s in d["statuses"]}
    out = {
        "band": int(result) if resolved else None,
        "status": ("estimated" if statuses == {"estimated"} else "provisional") if resolved
        else "unresolved",
        "unresolved_reason": None,
        "range": None if resolved else result,
        "face_value": set_band([d["face_value"] for d in per.values()], unknown),
        "best_original": own_result if own_result is not None else "unavailable",
        "bonus": round(int(result) + 0.5 * (1 - 1 / above), 2) if resolved and above else None,
        "task_count": len({t for d in per.values() for t in d["tasks"]}),
        "completeness": {"measured": len(per), "targets": len(targets)},
        "cap": {"binds": bool(capped), "languages": len(capped), "detail": capped},
        "sensitivity": {"unverified_as_independent": set_band(list(loose.values()), unknown)},
        "distribution": dict(sorted(Counter(bands).items())),
        "status_tally": dict(sorted(loaded["tally"].items())),
        "score_recorded": loaded["score"],
        "per_language": {lang: d["band"] for lang, d in sorted(per.items())},
    }
    if not resolved:
        out["unresolved_reason"] = unresolved_reason(loaded, len(per))
    return out


def category_roster(root: Path = ROOT) -> list[str]:
    """The products on the depth ladder's category roster."""
    cat = yaml.safe_load((root / "sources/categories" / f"{CATEGORY}.yaml").read_text())
    return list(cat.get("products") or [])


def ladder_errors(scores: dict, roster: list[str], doc: dict | None = None,
                  root: Path = ROOT) -> list[str]:
    """Every roster product records `basis: evaluation_depth` and the band the ladder computes.

    A recorded band that drifts from the evidence fails here, so a coverage, lineage or ownership
    change that moves a band has to move the record in the same PR.
    """
    doc = load_lineage() if doc is None else doc
    errors = []
    for slug in roster:
        cap = (scores.get(slug) or {}).get("capability") or {}
        where = f"score {slug!r}: capability"
        if cap.get("basis") != BASIS:
            errors.append(f"{where}: basis is {cap.get('basis')!r}; every {CATEGORY} product is "
                          f"scored by the depth ladder (basis {BASIS!r})")
            continue
        if cap.get("relative_to") or cap.get("relation"):
            errors.append(f"{where}: a depth-ladder band is computed, not placed against a peer; "
                          f"drop relative_to and relation")
        got = compute(doc, slug, root=root)
        if cap.get("score") != got["band"]:
            errors.append(f"{where}: records score {cap.get('score')!r}, but the depth ladder "
                          f"computes {got['band']!r} ({got['status']}"
                          + (f", {got['unresolved_reason']}" if got['unresolved_reason'] else "")
                          + ")")
    return errors
