"""Cross-category collision check over every research/*/rows*.yaml.

Reports (1) schema failures, (2) any slug or artifact claimed by two proposed categories,
(3) any slug/artifact that collides with the live corpus (head, tail, retired alias).
Run: uv run python research/crosscheck.py
"""
import glob, json, sys, yaml, jsonschema
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
schema = json.load(open(ROOT / "docs/schemas/registry.schema.json"))
KEYS = ["github", "huggingface_model", "huggingface_dataset", "pypi", "npm", "crates", "arxiv"]
corpus = {}
for f in (ROOT / "sources/products").glob("*.yaml"):
    d = yaml.safe_load(open(f)); corpus[("slug", d["name"])] = f"head:{d['name']}"
    for a in d.get("aliases") or []: corpus[("slug", a)] = f"alias-of:{d['name']}"
    for k in KEYS:
        for x in d.get(k) or []:
            u = x["url"] if isinstance(x, dict) else x
            for pre in ["https://github.com/", "https://huggingface.co/datasets/", "https://huggingface.co/", "https://pypi.org/project/", "https://www.npmjs.com/package/", "https://crates.io/crates/", "https://arxiv.org/abs/"]:
                if u.startswith(pre): u = u[len(pre):]
            corpus[(k, u.strip("/").lower())] = f"head:{d['name']}"
for f in (ROOT / "sources/registry").glob("*.yaml"):
    d = yaml.safe_load(open(f))
    for r in d.get("products") or []:
        corpus[("slug", r["slug"])] = f"tail:{d['category']}:{r['slug']}"
        for k in KEYS:
            if r.get(k): corpus[(k, str(r[k]).lower())] = f"tail:{d['category']}:{r['slug']}"
claims = defaultdict(list); bad = 0
for f in sorted(glob.glob(str(ROOT / "research/*/rows*.yaml"))):
    d = yaml.safe_load(open(f))
    try: jsonschema.validate(d, schema)
    except jsonschema.ValidationError as e: print(f"SCHEMA {f}: {e.message}"); bad += 1
    for r in d.get("products") or []:
        tag = f"{d['category']}:{r['slug']}"
        claims[("slug", r["slug"])].append(tag)
        for k in KEYS:
            if r.get(k): claims[(k, str(r[k]).lower())].append(tag)
for key, tags in sorted(claims.items()):
    if len(set(t.split(":")[0] for t in tags)) > 1: print(f"CROSS  {key}: {tags}"); bad += 1
    if key in corpus: print(f"CORPUS {key}: {tags} vs {corpus[key]}"); bad += 1
print(f"{len(claims)} identity keys checked, {bad} finding(s)")
sys.exit(1 if bad else 0)
