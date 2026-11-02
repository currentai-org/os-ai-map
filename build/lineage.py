"""Component lineage: where an evaluation component's items come from, and which pairs corroborate.

The depth ladder lets imported depth carry only as far as independent backing allows
(R-2026-11-02-k), so it needs to know, for any two components measuring one language, whether
they are independent, dependent or unverified (R-2026-11-02-h, -i). Those statuses are derived
here from `sources/lineage.yaml`, one cited record per component (R-2026-11-02-j, -u), so that a
reviewer can see why a language was capped and the same component never carries two sets of
lineage facts because two suites import it.

The derivation, in order, for a pair of components on one language (and optionally a split and
task):

1. An explicit `relationships` entry for the pair, and for the language where it names any,
   decides.
2. A component with no registry entry, or an entry marked `uncurated`, makes the pair unverified.
   The reason says which, because "not yet curated" and "origin unknown" both score as unverified
   but point evidence work in different directions.
3. Overrides are applied: the first override whose `languages`, `splits` and `tasks` selectors all
   match replaces the fields it states.
4. Dependent when either component is an ancestor of the other through `parents`, followed
   transitively; when their source collections overlap, counting each ancestor's collections; or
   when they share a creation `effort`, counting each ancestor's effort.
5. Unverified when either component's origin is unknown, or it names no collection or no effort.
6. Independent otherwise: both origins documented, collections disjoint, efforts separate.

`domains` never enters the derivation: two sets drawn from the same broad domain are not
dependent for that reason alone (R-2026-11-02-h).

Usage:
    uv run python -m build.lineage pair flores-plus sib-200 --language hau
    uv run python -m build.lineage pair batayan flores-plus --language fil --registry <path>
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "sources" / "lineage.yaml"
SCHEMA = ROOT / "docs" / "schemas" / "lineage.schema.json"
EMPTY = {"version": 1, "collections": [], "components": [], "relationships": []}
LINEAGE_FIELDS = ("origin", "collections", "parents", "effort", "domains")


@dataclass(frozen=True)
class PairStatus:
    """The derived status of one pair, with the rule that decided it."""

    status: str  # independent | dependent | unverified
    reason: str  # explicit | not_in_registry | not_curated | derived | shared_collection |
    #              shared_effort | origin_unknown | disjoint | same_component
    detail: str = ""


def load(path: Path = REGISTRY) -> dict:
    """The registry, or an empty one where the file does not exist at the tree being read."""
    if not path.exists():
        return dict(EMPTY)
    return yaml.safe_load(path.read_text()) or dict(EMPTY)


def _index(doc: dict) -> tuple[dict, dict]:
    comps = {c["id"]: c for c in doc.get("components") or [] if isinstance(c, dict) and "id" in c}
    cols = {c["id"]: c for c in doc.get("collections") or [] if isinstance(c, dict) and "id" in c}
    return comps, cols


def effective(record: dict, language: str | None = None, split: str | None = None,
              task: str | None = None) -> dict:
    """The record's lineage fields for one language, split and task, overrides applied."""
    out = {f: record.get(f) for f in LINEAGE_FIELDS}
    for ov in record.get("overrides") or []:
        if "languages" in ov and language not in ov["languages"]:
            continue
        if "splits" in ov and split not in ov["splits"]:
            continue
        if "tasks" in ov and task not in ov["tasks"]:
            continue
        out.update({f: ov[f] for f in LINEAGE_FIELDS if f in ov})
        break
    return out


def _closure(cid: str, comps: dict, language, split, task) -> tuple[set, set, set]:
    """Ancestors, collections and efforts of a component, followed through `parents`."""
    ancestors: set[str] = set()
    collections: set[str] = set()
    efforts: set[str] = set()
    stack, seen = [cid], set()
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in comps:
            continue
        seen.add(cur)
        rec = effective(comps[cur], language, split, task)
        collections.update(rec.get("collections") or [])
        if rec.get("effort"):
            efforts.add(rec["effort"])
        for parent in rec.get("parents") or []:
            ancestors.add(parent)
            stack.append(parent)
    return ancestors, collections, efforts


def _explicit(doc: dict, a: str, b: str, language: str | None) -> dict | None:
    for rel in doc.get("relationships") or []:
        if set(rel.get("between") or []) != {a, b}:
            continue
        langs = rel.get("languages")
        if langs and language not in langs:
            continue
        return rel
    return None


def pair_status(doc: dict, a: str, b: str, language: str | None = None, split: str | None = None,
                task: str | None = None) -> PairStatus:
    """Whether components `a` and `b` corroborate each other for one language (R-2026-11-02-i)."""
    if a == b:
        return PairStatus("dependent", "same_component")
    rel = _explicit(doc, a, b, language)
    if rel is not None:
        return PairStatus(rel["status"], "explicit", rel.get("rationale", ""))
    comps, _ = _index(doc)
    missing = [c for c in (a, b) if c not in comps]
    if missing:
        return PairStatus("unverified", "not_in_registry", ", ".join(missing))
    uncurated = [c for c in (a, b) if comps[c].get("curation") != "curated"]
    if uncurated:
        return PairStatus("unverified", "not_curated", ", ".join(uncurated))

    anc_a, col_a, eff_a = _closure(a, comps, language, split, task)
    anc_b, col_b, eff_b = _closure(b, comps, language, split, task)
    if b in anc_a or a in anc_b:
        child, parent = (a, b) if b in anc_a else (b, a)
        return PairStatus("dependent", "derived", f"{child} derives from {parent}")
    if col_a & col_b:
        return PairStatus("dependent", "shared_collection", ", ".join(sorted(col_a & col_b)))
    if eff_a & eff_b:
        return PairStatus("dependent", "shared_effort", ", ".join(sorted(eff_a & eff_b)))

    for c, cols, effs in ((a, col_a, eff_a), (b, col_b, eff_b)):
        rec = effective(comps[c], language, split, task)
        if rec.get("origin") == "unknown" or not cols or not effs:
            return PairStatus("unverified", "origin_unknown", c)
    return PairStatus("independent", "disjoint")


def lineage_errors(doc: dict, *, allowed_languages: set[str] | None = None,
                   schema: dict | None = None) -> list[str]:
    """Structural problems in the registry: schema, references, cycles and citation presence.

    This checks that the registry is well formed and that every claim carries a citation. It
    does not, and cannot, check that a citation supports the claim; that is evidence review
    (R-2026-11-02-j).
    """
    errors: list[str] = []
    schema = schema or json.loads(SCHEMA.read_text())
    try:
        jsonschema.validate(doc, schema)
    except jsonschema.ValidationError as e:
        path = "/".join(str(p) for p in e.absolute_path) or "(root)"
        return [f"lineage.yaml: {path}: schema: {e.message}"]

    for kind in ("collections", "components"):
        ids = [x["id"] for x in doc[kind]]
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            errors.append(f"lineage.yaml: {kind}: id {dup!r} appears more than once")
    comps, cols = _index(doc)

    def check_refs(where: str, fields: dict) -> None:
        for p in fields.get("parents") or []:
            if p not in comps:
                errors.append(f"{where}: parent {p!r} is not a component in the registry")
        for c in fields.get("collections") or []:
            if c not in cols:
                errors.append(f"{where}: collection {c!r} is not a collection in the registry")

    for cid, rec in comps.items():
        where = f"lineage.yaml: component {cid!r}"
        check_refs(where, rec)
        if cid in (rec.get("parents") or []):
            errors.append(f"{where}: names itself as a parent")
        if rec["curation"] == "curated":
            if not rec.get("sources"):
                errors.append(f"{where}: is curated but cites no sources")
            if rec["origin"] == "original" and not rec.get("collections"):
                errors.append(f"{where}: origin original names no collection of its own")
            if rec["origin"] == "derived" and not (rec.get("parents") or rec.get("collections")):
                errors.append(f"{where}: origin derived names no parent and no collection")
        for i, ov in enumerate(rec.get("overrides") or []):
            check_refs(f"{where}: overrides[{i}]", ov)
            if allowed_languages is not None:
                for lang in ov.get("languages") or []:
                    if lang not in allowed_languages:
                        errors.append(f"{where}: overrides[{i}]: language {lang!r} is not an "
                                      f"ISO 639-3 code in sources/snapshots/iso-639-3.tab")

    # A parent cycle would make "derives from" meaningless; report each cycle once.
    state: dict[str, int] = {}

    def visit(cid: str, trail: list[str]) -> None:
        state[cid] = 1
        for p in comps[cid].get("parents") or []:
            if p not in comps:
                continue
            if state.get(p) == 1:
                cycle = trail[trail.index(p):] + [p] if p in trail else [cid, p]
                errors.append("lineage.yaml: parents form a cycle: " + " -> ".join(cycle))
            elif state.get(p) is None:
                visit(p, trail + [p])
        state[cid] = 2

    for cid in comps:
        if state.get(cid) is None:
            visit(cid, [cid])

    seen_pairs: set[tuple] = set()
    for i, rel in enumerate(doc["relationships"]):
        where = f"lineage.yaml: relationships[{i}]"
        a, b = rel["between"]
        if a == b:
            errors.append(f"{where}: relates {a!r} to itself")
        for c in (a, b):
            if c not in comps:
                errors.append(f"{where}: {c!r} is not a component in the registry")
        key = (frozenset((a, b)), tuple(sorted(rel.get("languages") or [])))
        if key in seen_pairs:
            errors.append(f"{where}: repeats a relationship already stated for {a!r} and {b!r}")
        seen_pairs.add(key)
        if allowed_languages is not None:
            for lang in rel.get("languages") or []:
                if lang not in allowed_languages:
                    errors.append(f"{where}: language {lang!r} is not an ISO 639-3 code in "
                                  f"sources/snapshots/iso-639-3.tab")
    return errors


def qualifying_components(scores: dict) -> set[str]:
    """Every component slug on an official-evaluation coverage entry in any score record."""
    out: set[str] = set()
    for rec in scores.values():
        cap = (rec or {}).get("capability") or {}
        for entry in cap.get("language_coverage") or []:
            if isinstance(entry, dict) and entry.get("official_eval") and entry.get("component"):
                out.add(entry["component"])
    return out


def lineage_warnings(doc: dict, scores: dict) -> list[str]:
    """One non-fatal line naming coverage components with no registry entry.

    A missing entry makes every pair it is in unverified; it never fails the build and never
    reads as independence (R-2026-11-02-j).
    """
    comps, _ = _index(doc)
    missing = sorted(qualifying_components(scores) - set(comps))
    if not missing:
        return []
    shown = ", ".join(missing[:8]) + (", ..." if len(missing) > 8 else "")
    return [f"lineage: {len(missing)} coverage component(s) have no sources/lineage.yaml entry, "
            f"so their pairs are unverified: {shown}"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pair", help="derive the status of one pair of components")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--language")
    p.add_argument("--split")
    p.add_argument("--task")
    p.add_argument("--registry", type=Path, default=REGISTRY)
    args = ap.parse_args()
    doc = load(args.registry)
    s = pair_status(doc, args.a, args.b, args.language, args.split, args.task)
    print(json.dumps({"a": args.a, "b": args.b, "language": args.language, "status": s.status,
                      "reason": s.reason, "detail": s.detail}))


if __name__ == "__main__":
    main()
