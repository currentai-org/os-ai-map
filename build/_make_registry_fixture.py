"""One-off: distill ecosystem-mapping merged.json -> build/_registry_artifacts.json.

Run once to (re)generate the committed fixture that convert.py reads. After this
fixture is committed, convert.py no longer depends on ecosystem-mapping (which is
slated for teardown).

The fixture is a JSON map { normalized_product_name: [ {type, url}, ... ] } where:
  - normalized_product_name = re.sub(r'[^a-z0-9]','', name.lower())  (matches convert.py)
  - only artifact types in {repo, package, model, dataset} are kept (app/api dropped)
  - each entry is reduced to {type, url} where `url` is a canonical locator:
      repo     -> the github (or other) url as-is
      model    -> the hf_url as-is
      dataset  -> the hf_url as-is
      package  -> a synthesized registry url so convert.py can parse it uniformly:
                    pypi -> https://pypi.org/project/<name>
                    npm  -> https://www.npmjs.com/package/<name>
                  (other registries kept as registry:name so convert.py reports a skip)
Order within a product's list is preserved as-seen in the registry.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MERGED = Path(
    "/workspace/GitHub/oso-external/ecosystem-mapping/data/stack-map/registry/merged.json"
)
OUT = ROOT / "build" / "_registry_artifacts.json"

KEEP = {"repo", "package", "model", "dataset"}


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _package_url(a: dict) -> str | None:
    reg = (a.get("registry") or "").strip().lower()
    name = (a.get("name") or "").strip()
    if not name:
        return None
    if reg == "pypi":
        return f"https://pypi.org/project/{name}"
    if reg == "npm":
        return f"https://www.npmjs.com/package/{name}"
    # Unknown registry: keep a locator so convert.py's parser reports a skip
    # rather than silently dropping (no malformed id is emitted downstream).
    return f"{reg or 'unknown'}:{name}"


def main() -> None:
    merged = json.load(open(MERGED))
    out: dict[str, list[dict]] = {}
    for c in merged["categories"]:
        for e in c["entities"]:
            for p in e["products"]:
                key = _norm(p["product_name"])
                entries = out.setdefault(key, [])
                for a in p.get("artifacts") or []:
                    t = a.get("type")
                    if t not in KEEP:
                        continue
                    if t == "repo":
                        url = a.get("url")
                    elif t in ("model", "dataset"):
                        url = a.get("hf_url")
                    elif t == "package":
                        url = _package_url(a)
                    else:
                        url = None
                    if not url:
                        continue
                    entries.append({"type": t, "url": url})
    # Drop products that ended up with no kept artifacts (keeps fixture lean).
    out = {k: v for k, v in out.items() if v}
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    n_entries = sum(len(v) for v in out.values())
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out)} products, {n_entries} artifact entries")


if __name__ == "__main__":
    main()
