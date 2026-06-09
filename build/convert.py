"""One-time migration: merged overlay + generator constants -> sources/ YAML.

Inputs (read-only):
  OVERLAY  insights-private/.../stack-map/generator/notebook_data.json
  GEN      insights-private/.../stack-map/generator/generate_notebook.py
           (STRAPLINES, STACK_DESC, LAYER_WEIGHTS)
Outputs:
  sources/{organizations,categories,products,scores}/*.yaml

Notes on reading the generator constants:
  `generate_notebook.py` is a *code generator* — it does not expose a top-level
  `load_data()`. STRAPLINES / STACK_DESC / LAYER_WEIGHTS are static dict literals
  embedded inside the generated-notebook template string (the `data()` cell).
  We extract them with ast.literal_eval rather than importing the module, because
  importing it executes a top-level side effect (it rewrites the shipped notebook).
  This keeps the inputs strictly read-only.
"""
from pathlib import Path
import ast
import json
import yaml

from build.slugs import slugify, dedupe_slug
from build.orgs import build_org_registry

ROOT = Path(__file__).resolve().parents[1]
PRIV = Path("/workspace/GitHub/oso/insights-private/projects/currentai/stack-map/generator")
OVERLAY = PRIV / "notebook_data.json"
GEN = PRIV / "generate_notebook.py"


def _load_gen_constants():
    """Extract STRAPLINES + STACK_DESC + LAYER_WEIGHTS from the generator.

    The constants live as static dict literals inside the notebook-template
    string in generate_notebook.py (the `data()` cell). We locate that template,
    re-parse it, and literal_eval the three assignments. No module execution.
    """
    src = GEN.read_text()
    tree = ast.parse(src)
    want = {"STRAPLINES", "STACK_DESC", "LAYER_WEIGHTS"}
    out: dict = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "STRAPLINES = {" in node.value
        ):
            sub = ast.parse(node.value)
            for n in sub.body:
                if isinstance(n, ast.FunctionDef) and n.name == "data":
                    for st in n.body:
                        if isinstance(st, ast.Assign):
                            for t in st.targets:
                                if isinstance(t, ast.Name) and t.id in want:
                                    out[t.id] = ast.literal_eval(st.value)
            break
    missing = want - set(out)
    if missing:
        raise RuntimeError(f"could not extract generator constants: {sorted(missing)}")
    # LAYER_WEIGHTS values are (w_adopt, w_cap) tuples.
    return out["STRAPLINES"], out["STACK_DESC"], out["LAYER_WEIGHTS"]


def _dump(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True, width=100))


def main():
    overlay = json.load(open(OVERLAY))
    straplines, stack_desc, weights = _load_gen_constants()

    # Flatten overlay products (they live under categories[cid]['products']).
    flat = []
    for cid in overlay["order"]:
        for p in overlay["categories"][cid]["products"]:
            flat.append({**p, "_cat": cid})

    # 1) organizations
    org_records, name_to_slug = build_org_registry(flat)
    for o in org_records:
        _dump(ROOT / "sources/organizations" / f"{o['slug']}.yaml", o)

    # 2) products + scores  (assign slugs, dedupe on collision by org, then by suffix)
    taken: set[str] = set()
    roster: dict[str, list[str]] = {cid: [] for cid in overlay["order"]}
    suffix_count = 0
    for p in flat:
        org_slug = name_to_slug[(p.get("org") or "").strip()]
        slug = dedupe_slug(slugify(p["product"]), org_slug, taken)
        # Guard: if even base-org collides (identical name AND identical org),
        # append a numeric suffix until unique so we never overwrite a sibling.
        if slug in taken:
            base = slug
            n = 2
            while f"{base}-{n}" in taken:
                n += 1
            slug = f"{base}-{n}"
            suffix_count += 1
        taken.add(slug)
        roster[p["_cat"]].append(slug)

        product_doc = {
            "slug": slug, "name": p["product"], "org": org_slug, "type": p["type"],
            "description": p.get("description", ""),
        }
        if p.get("version_note"):
            product_doc["version_note"] = p["version_note"]
        if p.get("flags"):
            product_doc["flags"] = p["flags"]
        product_doc["artifacts"] = {}  # backfilled later from the registry; empty is valid
        _dump(ROOT / "sources/products" / f"{slug}.yaml", product_doc)

        score_doc = {"product": slug, "openness": p["openness"],
                     "adoption": p["adoption"], "capability": p["capability"]}
        _dump(ROOT / "sources/scores" / f"{slug}.yaml", score_doc)

    # 3) categories (label/arc/products from overlay; strapline/weights from generator)
    for ordinal, cid in enumerate(overlay["order"]):
        c = overlay["categories"][cid]
        wa, wc = weights.get(cid, (0.5, 0.5))
        cat_doc = {
            "slug": cid, "order": ordinal, "name": c["label"], "arc": c["arc"],
            "strapline": straplines.get(cid, ""),
            "weights": {"adopt": wa, "cap": wc},
            "products": roster[cid],
        }
        _dump(ROOT / "sources/categories" / f"{cid}.yaml", cat_doc)

    print(
        f"wrote {len(org_records)} orgs, {len(flat)} products+scores, "
        f"{len(overlay['order'])} categories"
    )
    if suffix_count:
        print(f"  ({suffix_count} numeric-suffix dedupe(s) applied)")


if __name__ == "__main__":
    main()
