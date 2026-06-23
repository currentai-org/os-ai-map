#!/usr/bin/env python3
"""Refresh the embedded data payload in notebooks/products-view.py.

products-view.py is a HYBRID notebook: the gallery, lookup engine, and layout
cells are hand-authored, but its data lives in a single embedded payload
(``PAYLOAD = json.loads('...')`` in the ``data`` cell). This module regenerates
ONLY that payload from build/notebook_data.json so the products view never
drifts from the canonical stack-map data. Everything else in the notebook is
left untouched.

Run after render.py (it consumes the same build/notebook_data.json):

    uv run python build/products_view_data.py            # rewrite the payload
    uv run python build/products_view_data.py --check     # exit 1 if a gallery
                                                          # exemplar name no
                                                          # longer resolves

The regenerate workflow runs this on every push to main that touches sources/,
then commits notebooks/products-view.py alongside the other generated artifacts.
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "products-view.py"
ND = ROOT / "build" / "notebook_data.json"

def _embedded_payload(source: str) -> dict | None:
    """Return the payload currently embedded in the notebook, or None."""
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "loads" and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value.strip().startswith("{")):
            return json.loads(node.args[0].value)
    return None


def build_payload(nd: dict, prev: dict | None) -> dict:
    """Map build/notebook_data.json into the compact products-view payload."""
    prev_descs = {cid: c.get("desc") for cid, c in (prev or {}).get("cats", {}).items()}
    order = nd["order"]
    # Canonical per-category captions now ship in the payload (descriptions.categories,
    # sourced from sources/categories/<cid>.yaml). A caption already edited into the
    # notebook's current payload still wins, so curators can tweak wording in-notebook.
    nd_descs = nd.get("descriptions", {}).get("categories", {})
    cats, components = {}, []
    for cid in order:
        c = nd["categories"][cid]
        cats[cid] = {
            "label": c["label"],
            "arc": c["arc"],
            "desc": prev_descs.get(cid) or nd_descs.get(cid, ""),
        }
        for p in c["products"]:
            comp = {
                "n": p["product"],
                "o": p.get("org"),
                "t": p.get("type"),
                "c": cid,
                "d": p.get("description"),
            }
            # optional records, included only when present (keeps payload tight)
            for src_key, dst_key in (("version_note", "vn"), ("openness", "op"),
                                     ("adoption", "ad"), ("capability", "cap")):
                if p.get(src_key):
                    comp[dst_key] = p[src_key]
            components.append(comp)
    return {
        "generated": nd["generated"],
        "n_total": nd["n_total"],
        "order": order,
        "cats": cats,
        "components": components,
    }


def gallery_names(source: str) -> set[str]:
    """Every exemplar name referenced in the hand-authored gallery cell."""
    return set(re.findall(
        r'\(\s*"([^"]+)"\s*,\s*"(?:known_build|documented_component|similarity)"\s*\)',
        source,
    ))


def reembed(source: str, payload: dict) -> str:
    literal = repr(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    lines = source.splitlines()
    for i, line in enumerate(lines):
        if "PAYLOAD = json.loads(" in line:
            indent = line[: len(line) - len(line.lstrip())]
            lines[i] = f"{indent}PAYLOAD = json.loads({literal})"
            break
    else:
        raise SystemExit("could not find the PAYLOAD assignment line in the notebook")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if a gallery exemplar name no longer resolves")
    args = ap.parse_args()

    source = NB.read_text()
    nd = json.loads(ND.read_text())
    payload = build_payload(nd, _embedded_payload(source))
    assert len(payload["components"]) == nd["n_total"], \
        (len(payload["components"]), nd["n_total"])

    names = {c["n"] for c in payload["components"]}
    referenced = gallery_names(source)
    unresolved = sorted(n for n in referenced if n not in names)

    print(f"products-view payload: {payload['n_total']} components, "
          f"generated {payload['generated']}")
    print(f"gallery exemplar names: {len(referenced)} referenced, "
          f"{len(unresolved)} unresolved")
    for n in unresolved:
        print(f"  WARN unresolved gallery name: {n}", file=sys.stderr)

    if args.check:
        return 1 if unresolved else 0

    NB.write_text(reembed(source, payload))
    print(f"re-embedded payload into {NB.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
