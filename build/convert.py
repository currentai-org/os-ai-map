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


def _parse_repo(url: str) -> str | None:
    """github.com/<owner>/<name> -> '<owner>/<name>'. Non-github -> None."""
    m = re.match(r"https?://(?:www\.)?github\.com/([^/?#]+)/([^/?#]+)", url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    repo = re.sub(r"\.git$", "", repo)
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"


def _parse_hf_model(url: str) -> str | None:
    """huggingface.co/<org>/<model> (not a /datasets/ path) -> '<org>/<model>'."""
    m = re.match(r"https?://(?:www\.)?huggingface\.co/([^/?#]+)/([^/?#]+)", url)
    if not m:
        return None
    org, model = m.group(1), m.group(2)
    if org == "datasets":  # that's a dataset url, not a model
        return None
    return f"{org}/{model}"


def _parse_hf_dataset(url: str) -> str | None:
    """huggingface.co/datasets/<id> -> '<id>' (id may contain a slash)."""
    m = re.match(r"https?://(?:www\.)?huggingface\.co/datasets/([^?#]+)", url)
    if not m:
        return None
    ident = m.group(1).rstrip("/")
    return ident or None


def _parse_package(url: str) -> str | None:
    """pypi.org/project/<x> -> 'pypi/<x>'; npmjs.com/package/<x> -> 'npm/<x>'."""
    m = re.match(r"https?://(?:www\.)?pypi\.org/project/([^/?#]+)", url)
    if m:
        return f"pypi/{m.group(1)}"
    m = re.match(r"https?://(?:www\.)?npmjs\.com/package/(@?[^/?#]+(?:/[^/?#]+)?)", url)
    if m:
        return f"npm/{m.group(1)}"
    return None


# Per-type dispatch: parser + the artifacts-dict key the id lands in.
_ARTIFACT_PARSERS = {
    "repo": (_parse_repo, "repos"),
    "model": (_parse_hf_model, "hf_models"),
    "dataset": (_parse_hf_dataset, "datasets"),
    "package": (_parse_package, "packages"),
}


def _build_artifacts(entries: list[dict], skips: dict[str, int]) -> dict:
    """Map a registry artifact list -> the product `artifacts` dict.

    Only the four schema keys are emitted, each a deduped, first-seen-ordered
    list of strings. Unparseable urls are skipped and tallied in `skips`.
    """
    buckets: dict[str, list[str]] = {}
    for a in entries:
        parser_key = _ARTIFACT_PARSERS.get(a.get("type"))
        if not parser_key:
            continue
        parser, dest = parser_key
        ident = parser(a.get("url") or "")
        if not ident:
            skips[a.get("type", "?")] = skips.get(a.get("type", "?"), 0) + 1
            continue
        lst = buckets.setdefault(dest, [])
        if ident not in lst:
            lst.append(ident)
    # Stable key order; drop empty lists so artifacts: {} stays {} when nothing joins.
    return {k: buckets[k] for k in ("repos", "packages", "hf_models", "datasets") if buckets.get(k)}


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
        # Backfill artifacts from the v2 registry fixture, keyed by normalized name
        # (overlay product name == our product `name`). No match -> {} (valid).
        entries = registry_artifacts.get(_norm(p["product"]), [])
        artifacts = _build_artifacts(entries, artifact_skips)
        if artifacts:
            artifact_matches += 1
        product_doc["artifacts"] = artifacts
        _dump(ROOT / "sources/products" / f"{slug}.yaml", product_doc)

        score_doc = {"product": slug, "openness": p["openness"],
                     "adoption": p["adoption"], "capability": p["capability"]}
        _dump(ROOT / "sources/scores" / f"{slug}.yaml", score_doc)

    # 3) categories (label/products from overlay; strapline/weights from generator).
    # arc + order are cross-category concerns; they live in sources/taxonomy.yaml now.
    for cid in overlay["order"]:
        c = overlay["categories"][cid]
        wa, wc = weights.get(cid, (0.5, 0.5))
        cat_doc = {
            "slug": cid, "name": c["label"],
            "strapline": straplines.get(cid, ""),
            "weights": {"adopt": wa, "cap": wc},
            "products": roster[cid],
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
