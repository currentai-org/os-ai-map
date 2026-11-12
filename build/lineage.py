"""Component lineage: where an evaluation component's items come from, and which pairs corroborate.

The depth ladder lets imported depth carry only as far as independent backing allows
(R-2026-11-02-k), so it needs to know, for any two components measuring one language, whether
they are independent, dependent or unverified (R-2026-11-02-h, -i). Those statuses are derived
here from `sources/lineage.yaml`, one cited record per component (R-2026-11-02-j, -u), so that a
reviewer can see why a language was capped and the same component never carries two sets of
lineage facts because two suites import it.

The derivation, in order, for a pair of components on one language. Each component is resolved
in its own context, the task and split of its own coverage entry, because corroboration compares
evidence from different tasks and often different splits (R-2026-11-02-k):

1. An explicit `relationships` entry for the pair, and for the language where it names any,
   decides.
2. Overrides are applied to each component in its own context: the override whose `languages`,
   `splits` and `tasks` selectors all match replaces the fields it states. Validation refuses two
   overrides that could both match, so at most one ever applies. Ancestors reached through
   `parents` are resolved for the language only, since a parent's split and task are not the
   child's.
3. Dependent when either component is an ancestor of the other through `parents`, followed
   transitively; when their source collections overlap, counting each ancestor's collections; or
   when they share a creation `effort`, counting each ancestor's effort. This runs before any gap
   is considered, so known dependence decides even for a component with no entry or an uncurated
   one.
4. Unverified when provenance is undocumented anywhere in either component's ancestry: a
   component or ancestor with no registry entry, an uncurated entry, origin unknown, no effort, or
   no source collection of its own or inherited through a documented parent. The reason says
   which, because "not yet curated" and "origin unknown" both score as unverified but point
   evidence work in different directions. Independence needs documented provenance all the way up.
5. Independent otherwise: every origin in both ancestries documented, collections disjoint,
   efforts separate.

`domains` never enters the derivation: two sets drawn from the same broad domain are not
dependent for that reason alone (R-2026-11-02-h).

Usage:
    uv run python -m build.lineage pair flores-plus sib-200 --language hau
    uv run python -m build.lineage pair afrimmlu flores-plus --language hau \
        --a-task knowledge_exam --b-task machine_translation --b-split devtest
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "sources" / "lineage.yaml"
SCHEMA = ROOT / "docs" / "schemas" / "lineage.schema.json"
SCORE_SCHEMA = ROOT / "docs" / "schemas" / "score.schema.json"
EMPTY = {"version": 1, "collections": [], "components": [], "relationships": []}
LINEAGE_FIELDS = ("origin", "collections", "parents", "effort", "domains")


@dataclass(frozen=True)
class PairStatus:
    """The derived status of one pair, with the rule that decided it."""

    status: str  # independent | dependent | unverified
    reason: str  # explicit | not_in_registry | not_curated | derived | shared_collection |
    #              shared_effort | origin_unknown | disjoint | same_component
    detail: str = ""


def load(path: Path = REGISTRY):
    """The registry, or an empty one where the file does not exist at the tree being read.

    Only a missing file falls back to the empty registry. A file that exists is returned as
    parsed, so an empty file or a root that is not a mapping reaches `lineage_errors` and fails
    there instead of passing as an empty registry.
    """
    if not path.exists():
        return dict(EMPTY)
    return yaml.safe_load(path.read_text())


def _as_doc(doc) -> dict:
    return doc if isinstance(doc, dict) else {}


def _index(doc: dict) -> tuple[dict, dict]:
    doc = _as_doc(doc)
    comps = {c["id"]: c for c in doc.get("components") or [] if isinstance(c, dict) and "id" in c}
    cols = {c["id"]: c for c in doc.get("collections") or [] if isinstance(c, dict) and "id" in c}
    return comps, cols


def effective(record: dict, language: str | None = None, split: str | None = None,
              task: str | None = None) -> dict:
    """The record's lineage fields for one language, split and task, overrides applied.

    Validation guarantees that at most one override can match any context, so taking the first
    match is not a precedence rule; it is the only match.
    """
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


@dataclass
class _Ancestry:
    ancestors: set
    collections: set
    efforts: set
    gaps: list  # (component, reason) where provenance is undocumented, in visiting order


def _closure(cid: str, comps: dict, language, split, task) -> _Ancestry:
    """Ancestors, collections, efforts and provenance gaps of a component, through `parents`.

    The component itself is resolved in its own split and task; each ancestor for the language
    only. A gap is any node whose provenance is undocumented: no registry entry, an uncurated
    entry, origin unknown, no collection, or no effort.
    """
    out = _Ancestry(set(), set(), set(), [])
    stack, seen = [(cid, split, task)], set()
    while stack:
        cur, cur_split, cur_task = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        if cur not in comps:
            out.gaps.append((cur, "not_in_registry"))
            continue
        if comps[cur].get("curation") != "curated":
            out.gaps.append((cur, "not_curated"))
        rec = effective(comps[cur], language, cur_split, cur_task)
        cols = rec.get("collections") or []
        out.collections.update(cols)
        if rec.get("effort"):
            out.efforts.add(rec["effort"])
        if rec.get("origin") == "unknown" or not cols and not rec.get("parents") or not rec.get("effort"):
            out.gaps.append((cur, "origin_unknown"))
        for parent in rec.get("parents") or []:
            out.ancestors.add(parent)
            stack.append((parent, None, None))
    return out


def _explicit(doc: dict, a: str, b: str, language: str | None) -> dict | None:
    for rel in _as_doc(doc).get("relationships") or []:
        if set(rel.get("between") or []) != {a, b}:
            continue
        langs = rel.get("languages")
        if langs and language not in langs:
            continue
        return rel
    return None


def pair_status(doc: dict, a: str, b: str, language: str | None = None, *,
                a_task: str | None = None, a_split: str | None = None,
                b_task: str | None = None, b_split: str | None = None) -> PairStatus:
    """Whether components `a` and `b` corroborate each other for one language (R-2026-11-02-i).

    Each component is resolved in its own context: `a_task`/`a_split` are the task and split of
    `a`'s coverage entry, `b_task`/`b_split` of `b`'s.
    """
    if a == b:
        return PairStatus("dependent", "same_component")
    rel = _explicit(doc, a, b, language)
    if rel is not None:
        return PairStatus(rel["status"], "explicit", rel.get("rationale", ""))
    comps, _ = _index(doc)
    # Known dependence is checked before any provenance gap, including a component with no
    # entry or an uncurated one: a stated derivation or overlap establishes dependence even
    # where the rest of the lineage is incomplete (R-2026-11-02-h). Dependence only lowers
    # credit, so reading it from a placeholder record never overstates independence.
    x = _closure(a, comps, language, a_split, a_task)
    y = _closure(b, comps, language, b_split, b_task)
    if b in x.ancestors or a in y.ancestors:
        child, parent = (a, b) if b in x.ancestors else (b, a)
        return PairStatus("dependent", "derived", f"{child} derives from {parent}")
    if x.collections & y.collections:
        return PairStatus("dependent", "shared_collection", ", ".join(sorted(x.collections & y.collections)))
    if x.efforts & y.efforts:
        return PairStatus("dependent", "shared_effort", ", ".join(sorted(x.efforts & y.efforts)))

    gaps = x.gaps + y.gaps
    if gaps:
        # not_in_registry and not_curated are reported as such for an ancestor too, so the
        # evidence work they point to is visible; otherwise the gap is undocumented origin.
        for reason in ("not_in_registry", "not_curated", "origin_unknown"):
            hit = [c for c, r in gaps if r == reason]
            if hit:
                return PairStatus("unverified", reason, ", ".join(dict.fromkeys(hit)))
    return PairStatus("independent", "disjoint")


def _could_both_match(x: dict, y: dict) -> bool:
    """True when some language, split and task satisfies both overrides' selectors.

    A selector an override omits matches everything, so two overrides are disjoint only when
    some selector both state has no value in common.
    """
    for key in ("languages", "splits", "tasks"):
        if key in x and key in y and not set(x[key]) & set(y[key]):
            return False
    return True


def task_classes() -> set[str]:
    """The task classes capability.language_coverage allows, read from the score schema."""
    score = json.loads(SCORE_SCHEMA.read_text())
    entry = score["properties"]["capability"]["properties"]["language_coverage"]["items"]
    return set(entry["properties"]["task"]["enum"])


def lineage_errors(doc: dict, *, allowed_languages: set[str] | None = None,
                   schema: dict | None = None) -> list[str]:
    """Structural problems in the registry: schema, references, cycles and citation presence.

    This checks that the registry is well formed and that every claim carries a citation. It
    does not, and cannot, check that a citation supports the claim; that is evidence review
    (R-2026-11-02-j).
    """
    errors: list[str] = []
    if not isinstance(doc, dict):
        return [f"lineage.yaml: the file must be a mapping with version, collections, components "
                f"and relationships; it parsed as {type(doc).__name__}"]
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
    tasks = task_classes()

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
        overrides = rec.get("overrides") or []
        for i, ov in enumerate(overrides):
            eff = {**{f: rec.get(f) for f in LINEAGE_FIELDS}, **{f: ov[f] for f in LINEAGE_FIELDS if f in ov}}
            if cid in (eff.get("parents") or []):
                errors.append(f"{where}: overrides[{i}]: names the component itself as a parent")
            if rec["curation"] == "curated":
                if eff.get("origin") == "original" and not eff.get("collections"):
                    errors.append(f"{where}: overrides[{i}]: origin original names no collection of its own")
                if eff.get("origin") == "derived" and not (eff.get("parents") or eff.get("collections")):
                    errors.append(f"{where}: overrides[{i}]: origin derived names no parent and no collection")
            for j in range(i):
                if _could_both_match(overrides[j], ov):
                    errors.append(f"{where}: overrides[{j}] and overrides[{i}] can both match one "
                                  f"language, split and task; make their selectors disjoint, so a "
                                  f"language override cannot silently mask a task one")
            check_refs(f"{where}: overrides[{i}]", ov)
            for t in ov.get("tasks") or []:
                if t not in tasks:
                    errors.append(f"{where}: overrides[{i}]: task {t!r} is not a task class in "
                                  f"capability.language_coverage")
            if allowed_languages is not None:
                for lang in ov.get("languages") or []:
                    if lang not in allowed_languages:
                        errors.append(f"{where}: overrides[{i}]: language {lang!r} is not an "
                                      f"ISO 639-3 code in sources/snapshots/language-codes.tsv")

    # A parent cycle would make "derives from" meaningless; report each cycle once. Overrides
    # can replace `parents`, so the graph checked is the union of every parent edge any record or
    # override states: a cycle reachable under some language or task is still a cycle.
    edges: dict[str, set[str]] = {}
    for cid, rec in comps.items():
        es = set(rec.get("parents") or [])
        for ov in rec.get("overrides") or []:
            es.update(ov.get("parents") or [])
        edges[cid] = es
    state: dict[str, int] = {}

    def visit(cid: str, trail: list[str]) -> None:
        state[cid] = 1
        for p in sorted(edges[cid]):
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

    scopes: dict[frozenset, list[tuple[int, set | None]]] = {}
    for i, rel in enumerate(doc["relationships"]):
        where = f"lineage.yaml: relationships[{i}]"
        a, b = rel["between"]
        if a == b:
            errors.append(f"{where}: relates {a!r} to itself")
        for c in (a, b):
            if c not in comps:
                errors.append(f"{where}: {c!r} is not a component in the registry")
        # Two statements for one pair may not both apply to a language: an unrestricted one
        # applies to every language, so it overlaps any other for the pair. Otherwise the answer
        # would depend on which came first in the file.
        langs = set(rel["languages"]) if rel.get("languages") else None
        for j, other in scopes.get(frozenset((a, b)), []):
            if langs is None or other is None or langs & other:
                errors.append(f"{where}: overlaps relationships[{j}] for {a!r} and {b!r}; give "
                              f"each language one statement")
        scopes.setdefault(frozenset((a, b)), []).append((i, langs))
        if allowed_languages is not None:
            for lang in rel.get("languages") or []:
                if lang not in allowed_languages:
                    errors.append(f"{where}: language {lang!r} is not an ISO 639-3 code in "
                                  f"sources/snapshots/language-codes.tsv")

    # Citation dates, held to the rule score citations follow in build/validate.py: a real ISO
    # date, and not later than today, since `accessed` records when somebody read the source.
    today = date.today()
    for where, src in _citations(doc):
        try:
            when = date.fromisoformat(str(src.get("accessed")))
        except ValueError:
            errors.append(f"{where}: accessed {src.get('accessed')!r} is not an ISO date")
            continue
        if when > today:
            errors.append(f"{where}: accessed is {when}, later than today ({today}); a source "
                          f"cannot have been read in the future")
    return errors


def _citations(doc: dict):
    """Every citation in the registry, with where it sits."""
    for i, col in enumerate(doc.get("collections") or []):
        for k, src in enumerate(col.get("sources") or []):
            yield f"lineage.yaml: collections[{i}].sources[{k}]", src
    for i, comp in enumerate(doc.get("components") or []):
        for k, src in enumerate(comp.get("sources") or []):
            yield f"lineage.yaml: component {comp.get('id')!r}: sources[{k}]", src
        for j, ov in enumerate(comp.get("overrides") or []):
            for k, src in enumerate(ov.get("sources") or []):
                yield f"lineage.yaml: component {comp.get('id')!r}: overrides[{j}].sources[{k}]", src
    for i, rel in enumerate(doc.get("relationships") or []):
        for k, src in enumerate(rel.get("sources") or []):
            yield f"lineage.yaml: relationships[{i}].sources[{k}]", src


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

    A missing entry makes a pair unverified unless dependence is already known; it never fails
    the build and never reads as independence (R-2026-11-02-j).
    """
    comps, _ = _index(doc)
    missing = sorted(qualifying_components(scores) - set(comps))
    if not missing:
        return []
    shown = ", ".join(missing[:8]) + (", ..." if len(missing) > 8 else "")
    return [f"lineage: {len(missing)} coverage component(s) have no sources/lineage.yaml entry, "
            f"so their pairs are unverified unless dependence is known: {shown}"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pair", help="derive the status of one pair of components")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--language")
    p.add_argument("--a-task")
    p.add_argument("--a-split")
    p.add_argument("--b-task")
    p.add_argument("--b-split")
    p.add_argument("--registry", type=Path, default=REGISTRY)
    args = ap.parse_args()
    doc = load(args.registry)
    s = pair_status(doc, args.a, args.b, args.language, a_task=args.a_task, a_split=args.a_split,
                    b_task=args.b_task, b_split=args.b_split)
    print(json.dumps({"a": args.a, "b": args.b, "language": args.language, "status": s.status,
                      "reason": s.reason, "detail": s.detail}))


if __name__ == "__main__":
    main()
