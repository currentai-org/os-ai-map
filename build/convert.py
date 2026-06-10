"""One-time migration: merged overlay + generator constants -> sources/ YAML.

Inputs (read-only):
  OVERLAY  insights-private/.../stack-map/generator/notebook_data.json
  GEN      insights-private/.../stack-map/generator/generate_notebook.py
           (STRAPLINES, STACK_DESC, LAYER_WEIGHTS)
Outputs:
  sources/{organizations,categories,products,scores}/*.yaml

Notes on reading the generator constants:
  `generate_notebook.py` is a *code generator*, it does not expose a top-level
  `load_data()`. STRAPLINES / STACK_DESC / LAYER_WEIGHTS are static dict literals
  embedded inside the generated-notebook template string (the `data()` cell).
  We extract them with ast.literal_eval rather than importing the module, because
  importing it executes a top-level side effect (it rewrites the shipped notebook).
  This keeps the inputs strictly read-only.
"""
from pathlib import Path
import ast
import json
import re
import yaml

from build.slugs import slugify, dedupe_slug
from build.orgs import build_org_registry

ROOT = Path(__file__).resolve().parents[1]
PRIV = Path("/workspace/GitHub/oso/insights-private/projects/currentai/stack-map/generator")
OVERLAY = PRIV / "notebook_data.json"
GEN = PRIV / "generate_notebook.py"
# Committed fixture distilled from the v2 registry (build/_make_registry_fixture.py).
# Repo-relative so convert no longer depends on ecosystem-mapping at run time.
REGISTRY_ARTIFACTS = ROOT / "build" / "_registry_artifacts.json"


def _norm(name: str) -> str:
    """Normalization shared by the fixture keys and the overlay-name lookup."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


# Typed-url artifact keys, in stable emit order. Each maps to a top-level
# array of {url: ...} entries on the product, per oss-directory conventions.
_ARTIFACT_KEYS = ("github", "npm", "pypi", "crates", "go",
                  "huggingface_model", "huggingface_dataset")


def _artifact_key(url: str) -> str | None:
    """Classify a registry artifact url to its typed-array key by host.

    github.com -> github; pypi.org -> pypi; npmjs.com -> npm;
    huggingface.co/datasets/... -> huggingface_dataset;
    other huggingface.co/... -> huggingface_model. Anything else -> None.
    """
    m = re.match(r"https?://(?:www\.)?([^/?#]+)(/[^?#]*)?", url or "")
    if not m:
        return None
    host = m.group(1).lower()
    path = m.group(2) or ""
    if host == "github.com":
        return "github"
    if host == "pypi.org":
        return "pypi"
    if host == "npmjs.com":
        return "npm"
    if host == "crates.io":
        return "crates"
    if host == "huggingface.co":
        return "huggingface_dataset" if path.startswith("/datasets/") else "huggingface_model"
    return None


def _build_artifacts(entries: list[dict], skips: dict[str, int]) -> dict:
    """Map a registry artifact list -> typed top-level url arrays.

    Each emitted key is an array of {url: <full url>} entries, deduped by url
    and first-seen-ordered. Unclassifiable urls are skipped and tallied in
    `skips`. Empty result -> {} (no artifact keys emitted on the product).
    """
    buckets: dict[str, list[str]] = {}
    for a in entries:
        url = a.get("url") or ""
        key = _artifact_key(url)
        if not key:
            skips[a.get("type", "?")] = skips.get(a.get("type", "?"), 0) + 1
            continue
        lst = buckets.setdefault(key, [])
        if url not in lst:
            lst.append(url)
    return {k: [{"url": u} for u in buckets[k]] for k in _ARTIFACT_KEYS if buckets.get(k)}


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
    registry_artifacts = json.load(open(REGISTRY_ARTIFACTS))
    artifact_skips: dict[str, int] = {}
    artifact_matches = 0

    # Flatten overlay products (they live under categories[cid]['products']).
    flat = []
    for cid in overlay["order"]:
        for p in overlay["categories"][cid]["products"]:
            flat.append({**p, "_cat": cid})

    # 1) organizations (records first; product rosters are filled in below as we
    #    assign product slugs, then written out after the product loop).
    org_records, name_to_slug = build_org_registry(flat)

    # 2) products + scores  (assign slugs, dedupe on collision by org, then by suffix)
    taken: set[str] = set()
    roster: dict[str, list[str]] = {cid: [] for cid in overlay["order"]}
    # Reverse of the old per-product `org` field: each org owns an ordered roster
    # of product slugs, in the order products first appear in the flat overlay list.
    org_roster: dict[str, list[str]] = {o["name"]: [] for o in org_records}
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
        org_roster[org_slug].append(slug)

        product_doc = {
            "name": slug, "display_name": p["product"], "type": p["type"],
            "description": p.get("description", ""),
        }
        # Backfill artifacts from the v2 registry fixture, keyed by normalized name
        # (overlay product label == our product `display_name`). No match -> no
        # artifact keys. Emitted as typed top-level url arrays (oss-directory style).
        entries = registry_artifacts.get(_norm(p["product"]), [])
        artifacts = _build_artifacts(entries, artifact_skips)
        if artifacts:
            artifact_matches += 1
        product_doc.update(artifacts)
        if p.get("flags"):
            product_doc["flags"] = p["flags"]
        # Provenance text formerly named `version_note`; now a free-text `comments`
        # string (empty when the overlay carried no note).
        product_doc["comments"] = p.get("version_note") or ""
        _dump(ROOT / "sources/products" / f"{slug}.yaml", product_doc)

        score_doc = {"product": slug, "openness": p["openness"],
                     "adoption": p["adoption"], "capability": p["capability"]}
        _dump(ROOT / "sources/scores" / f"{slug}.yaml", score_doc)

    # Write organizations now that each roster is populated (org owns its products).
    for o in org_records:
        o["products"] = org_roster[o["name"]]
        _dump(ROOT / "sources/organizations" / f"{o['name']}.yaml", o)

    # 3) categories (label/products from overlay; strapline/weights from generator).
    # arc + order are cross-category concerns; they live in sources/taxonomy.yaml now.
    for cid in overlay["order"]:
        c = overlay["categories"][cid]
        wa, wc = weights.get(cid, (0.5, 0.5))
        cat_doc = {
            "name": cid, "display_name": c["label"],
            "strapline": straplines.get(cid, ""),
            "weights": {"adopt": wa, "cap": wc},
            "products": roster[cid],
            "comments": "",
        }
        _dump(ROOT / "sources/categories" / f"{cid}.yaml", cat_doc)

    # 4) taxonomy manifest: derive arcs by walking the curated overlay order and
    # grouping consecutive same-arc categories. Within-arc order is preserved as-is.
    arcs: list[dict] = []
    for cid in overlay["order"]:
        arc_name = overlay["categories"][cid]["arc"]
        if not arcs or arcs[-1]["name"] != arc_name:
            arcs.append({"name": arc_name, "categories": []})
        arcs[-1]["categories"].append(cid)
    _dump(ROOT / "sources/taxonomy.yaml", {"arcs": arcs})

    print(
        f"wrote {len(org_records)} orgs, {len(flat)} products+scores, "
        f"{len(overlay['order'])} categories"
    )
    if suffix_count:
        print(f"  ({suffix_count} numeric-suffix dedupe(s) applied)")
    print(f"  ({artifact_matches} products got artifacts from the registry)")
    if artifact_skips:
        print(f"  (artifact url skips: {dict(sorted(artifact_skips.items()))})")


if __name__ == "__main__":
    main()
