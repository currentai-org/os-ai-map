"""Export the published map as a Hugging Face dataset: Parquet tables, a manifest, and a card.

    uv run python -m build.export_hf                       # → dist/hf/
    uv run python -m build.export_hf --out /tmp/hf         # elsewhere
    uv run python -m build.export_hf --push                # build, upload, tag (maintainer, at a tag)

Six tables, one Hugging Face config each:

* ``products``          one row per published product: identity, the three axes, overall score,
                        tier, and artifact links. Built from ``build_payload``, so every number is
                        the one the map shows.
* ``organizations``     one row per organization that owns or stewards a published product.
* ``categories``        one row per published category: stage, gaps, weights, roster counts.
* ``citations``         one row per cited source behind a published product's axis score, read
                        from ``sources/scores/`` directly: the full audit trail, not the payload's
                        trimmed copy.
* ``product_history``   one row per (release, product): the axes and overall score as each tagged
                        release published them.
* ``category_history``  one row per (release, category): stage and gaps per tagged release.

The history tables read ``build/notebook_data.json`` at each ``v*`` tag from git. They record
what was published, not a recomputation under today's rules, so a value can move between
releases because the method changed as well as because the product did. The card says so.

Scope: published categories only (preliminary categories and the long tail are left out, as on
the map). The long-tail snapshot is excluded on purpose: it carries third-party catalog content.

Nothing here writes to ``sources/`` or the warehouse. ``dist/`` is build output and is not
committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from string import Template

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from build.serialize import ROOT, PAYLOAD_CONTRACT, build_payload, release_date, repo_version
from build.vocabulary import axes, lineage_relations, parse_date

ARTIFACT_KINDS = ("github", "pypi", "npm", "crates", "go", "huggingface_model",
                  "huggingface_dataset", "arxiv")
DEFAULT_REPO_ID = "current-ai-official/os-ai-map"
CARD_TEMPLATE = ROOT / "build" / "hf_dataset_card.md"
TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


# --- helpers -----------------------------------------------------------------------------------

def _urls(entries) -> list[str]:
    return [e["url"] if isinstance(e, dict) else str(e) for e in (entries or [])]


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True).stdout


def _table(rows: list[dict], schema: pa.Schema) -> pa.Table:
    return pa.Table.from_pylist([{f.name: r.get(f.name) for f in schema} for r in rows],
                                schema=schema)


STR, INT, FLOAT, BOOL, DATE = pa.string(), pa.int32(), pa.float64(), pa.bool_(), pa.date32()
STRS = pa.list_(pa.string())


# --- current-state tables ----------------------------------------------------------------------

PRODUCTS_SCHEMA = pa.schema([
    ("slug", STR), ("name", STR), ("type", STR), ("description", STR),
    ("organization_slug", STR), ("organization", STR), ("steward", STR),
    ("category_slug", STR), ("category", STR), ("layer", STR), ("group", STR),
    ("category_position", INT),
    ("openness_score", INT), ("openness_class", STR), ("openness_bucket", STR),
    ("openness_components", STR), ("openness_confidence", STR), ("openness_note", STR),
    ("openness_last_verified", DATE),
    ("adoption_level", INT), ("adoption_reach", STR), ("adoption_signal_type", STR),
    ("adoption_confidence", STR), ("adoption_note", STR), ("adoption_last_verified", DATE),
    ("capability_score", INT), ("capability_basis", STR), ("capability_basis_detail", STR),
    ("capability_value", STR), ("capability_relative_to", STR), ("capability_relation", STR),
    ("capability_confidence", STR), ("capability_note", STR), ("capability_last_verified", DATE),
    ("overall_score", FLOAT), ("overall_basis", STR), ("tier", STR), ("mature", BOOL),
    ("languages", STRS), ("aliases", STRS), ("version_note", STR),
    ("end_of_life_date", DATE), ("end_of_life_source", STR),
    *[(f"lineage_{edge}", STRS) for edge in lineage_relations()],
    *[(kind, STRS) for kind in ARTIFACT_KINDS],
    ("citation_count", INT),
])

ORGANIZATIONS_SCHEMA = pa.schema([
    ("slug", STR), ("name", STR), ("type", STR), ("country", STR), ("homepage", STR),
    ("github", STRS), ("products", STRS), ("product_count", INT),
])

CATEGORIES_SCHEMA = pa.schema([
    ("slug", STR), ("name", STR), ("description", STR), ("strapline", STR),
    ("layer", STR), ("arc", STR), ("group", STR), ("group_slug", STR), ("display_order", INT),
    ("stage_num", INT), ("stage_name", STR), ("gaps", STRS),
    ("weight_adoption", FLOAT), ("weight_capability", FLOAT),
    ("product_count", INT), ("leading_count", INT), ("strong_count", INT), ("mature_count", INT),
])

CITATIONS_SCHEMA = pa.schema([
    ("product_slug", STR), ("axis", STR), ("position", INT),
    ("url", STR), ("shows", STR), ("accessed", DATE), ("http_status", INT),
    ("content_sha256", STR), ("establishes", STRS),
])


def current_tables(sources: dict, payload: dict) -> dict[str, pa.Table]:
    prods, scores, cats = sources["products"], sources["scores"], sources["categories"]

    products, citations = [], []
    for cid in payload["order"]:
        cat = payload["categories"][cid]
        for pos, row in enumerate(cat["products"]):
            slug = row["slug"]
            src = prods[slug]
            o, a, c = row["openness"], row["adoption"], row["capability"]
            n_cites = 0
            for axis in axes():
                for i, s in enumerate((scores[slug].get(axis) or {}).get("sources") or []):
                    n_cites += 1
                    citations.append({
                        "product_slug": slug, "axis": axis, "position": i,
                        "url": s.get("url"), "shows": s.get("shows"),
                        "accessed": parse_date(s.get("accessed")),
                        "http_status": s.get("http_status"),
                        "content_sha256": s.get("content_sha256"),
                        "establishes": s.get("establishes"),
                    })
            eol = src.get("end_of_life") or {}
            lineage = src.get("lineage") or {}
            products.append({
                "slug": slug, "name": row["product"], "type": row["type"],
                "description": row.get("description"),
                "organization_slug": row["org_slug"], "organization": row["org"] or None,
                "steward": row.get("steward"),
                "category_slug": cid, "category": cat["label"], "layer": cat["layer"],
                "group": cat["group"], "category_position": pos,
                "openness_score": o.get("score"), "openness_class": o.get("class"),
                "openness_bucket": o.get("bucket"), "openness_components": o.get("components"),
                "openness_confidence": o.get("confidence"), "openness_note": o.get("note"),
                "openness_last_verified": parse_date(o.get("last_verified")),
                "adoption_level": a.get("level"), "adoption_reach": a.get("reach"),
                "adoption_signal_type": a.get("signal_type"),
                "adoption_confidence": a.get("confidence"), "adoption_note": a.get("note"),
                "adoption_last_verified": parse_date(a.get("last_verified")),
                "capability_score": c.get("score"), "capability_basis": c.get("basis"),
                "capability_basis_detail": c.get("basis_detail"),
                "capability_value": c.get("value"),
                "capability_relative_to": c.get("relative_to"),
                "capability_relation": c.get("relation"),
                "capability_confidence": c.get("confidence"), "capability_note": c.get("note"),
                "capability_last_verified": parse_date(c.get("last_verified")),
                "overall_score": row.get("overall_score"), "overall_basis": row.get("overall_basis"),
                "tier": row.get("tier"), "mature": row.get("mature"),
                "languages": row.get("languages"), "aliases": src.get("aliases"),
                "version_note": row.get("version_note"),
                "end_of_life_date": parse_date(eol.get("date")), "end_of_life_source": eol.get("source"),
                **{f"lineage_{e}": lineage.get(e) for e in lineage_relations()},
                **{k: _urls(src.get(k)) or None for k in ARTIFACT_KINDS},
                "citation_count": n_cites,
            })

    organizations = [{
        "slug": slug, "name": org["display_name"], "type": org.get("type"),
        "country": org.get("country") or None, "homepage": org.get("homepage") or None,
        "github": _urls(org.get("github")), "products": org.get("products", []),
        "product_count": len(org.get("products", [])),
    } for slug, org in payload["organizations"].items()]

    categories = []
    for i, cid in enumerate(payload["order"]):
        cat, src = payload["categories"][cid], cats[cid]
        rows = cat["products"]
        w = src.get("weights") or {}
        categories.append({
            "slug": cid, "name": cat["label"], "description": src.get("description"),
            "strapline": src.get("strapline"), "layer": cat["layer"], "arc": cat["arc"],
            "group": cat["group"], "group_slug": cat["group_slug"] or None, "display_order": i,
            "stage_num": cat["stage"]["num"], "stage_name": cat["stage"]["name"],
            "gaps": cat["gaps"],
            "weight_adoption": w.get("adopt"), "weight_capability": w.get("cap"),
            "product_count": len(rows),
            "leading_count": sum(r.get("tier") == "leading" for r in rows),
            "strong_count": sum(r.get("tier") == "strong" for r in rows),
            "mature_count": sum(bool(r.get("mature")) for r in rows),
        })

    return {
        "products": _table(products, PRODUCTS_SCHEMA),
        "organizations": _table(organizations, ORGANIZATIONS_SCHEMA),
        "categories": _table(categories, CATEGORIES_SCHEMA),
        "citations": _table(citations, CITATIONS_SCHEMA),
    }


# --- history tables ----------------------------------------------------------------------------

PRODUCT_HISTORY_SCHEMA = pa.schema([
    ("version", STR), ("released", DATE), ("payload_generated", DATE), ("source_commit", STR),
    ("product_slug", STR), ("current_slug", STR), ("name", STR), ("category_slug", STR),
    ("openness_score", INT), ("openness_class", STR),
    ("adoption_level", INT), ("adoption_reach", STR), ("capability_score", INT),
    ("overall_score", FLOAT), ("tier", STR), ("mature", BOOL),
])

CATEGORY_HISTORY_SCHEMA = pa.schema([
    ("version", STR), ("released", DATE), ("payload_generated", DATE), ("source_commit", STR),
    ("category_slug", STR), ("name", STR), ("stage_num", INT), ("stage_name", STR),
    ("gaps", STRS), ("product_count", INT), ("leading_count", INT), ("mature_count", INT),
])


def release_tags() -> list[tuple[str, str]]:
    """``(version, commit)`` for every ``vX.Y.Z`` tag, oldest first."""
    out = []
    for line in _git("for-each-ref", "--format=%(refname:short) %(*objectname)%(objectname)",
                     "refs/tags").splitlines():
        name, sha = line.split()
        m = TAG_RE.match(name)
        if m:
            # Annotated tags print the peeled commit then the tag object; keep the commit.
            out.append((tuple(int(x) for x in m.groups()), name[1:], sha[:40]))
    return [(v, sha) for _, v, sha in sorted(out)]


def _slugs_by_name(commit: str) -> dict[str, str]:
    """display_name → slug at ``commit``, for early payloads whose rows carry no ``slug``."""
    names = [n for n in _git("ls-tree", "--name-only", commit, "sources/products/").split()
             if n.endswith(".yaml")]
    # Bytes, not text: the header's size is a byte count.
    batch = subprocess.run(["git", "-C", str(ROOT), "cat-file", "--batch"],
                           input="".join(f"{commit}:{n}\n" for n in names).encode(),
                           capture_output=True, check=True).stdout
    out, pos = {}, 0
    for n in names:
        header_end = batch.index(b"\n", pos)
        size = int(batch[pos:header_end].split()[2])
        body = batch[header_end + 1: header_end + 1 + size]
        pos = header_end + 1 + size + 1
        doc = yaml.safe_load(body.decode("utf-8")) or {}
        out[doc.get("display_name", "")] = Path(n).stem
    return out


def _snapshot_rows(payload: dict, version: str, released: date | None, commit: str,
                   name_to_slug: dict[str, str] | None, current_slug: dict[str, str]):
    meta = {"version": version, "released": released,
            "payload_generated": parse_date(payload.get("generated")), "source_commit": commit}
    prows, crows = [], []
    for cid in payload["order"]:
        cat = payload["categories"][cid]
        rows = cat["products"]
        crows.append({**meta, "category_slug": cid, "name": cat["label"],
                      "stage_num": cat["stage"]["num"], "stage_name": cat["stage"]["name"],
                      "gaps": cat["gaps"], "product_count": len(rows),
                      "leading_count": sum(r.get("tier") == "leading" for r in rows),
                      "mature_count": sum(bool(r.get("mature")) for r in rows)})
        for r in rows:
            slug = r.get("slug") or (name_to_slug or {}).get(r["product"])
            o, a, c = r.get("openness") or {}, r.get("adoption") or {}, r.get("capability") or {}
            prows.append({**meta, "product_slug": slug, "current_slug": current_slug.get(slug),
                          "name": r["product"],
                          "category_slug": cid,
                          "openness_score": o.get("score"), "openness_class": o.get("class"),
                          "adoption_level": a.get("level"), "adoption_reach": a.get("reach"),
                          "capability_score": c.get("score"),
                          # `maturity` is the pre-rename key for the same number.
                          "overall_score": r.get("overall_score", r.get("maturity")),
                          "tier": r.get("tier"), "mature": r.get("mature")})
    return prows, crows


def history_tables(current: dict, current_version: str, head: str) -> dict[str, pa.Table]:
    # A slug retired since a release still joins to today's products through the alias index
    # (identity.md). A product merged without a recorded alias gets a null current_slug.
    live = {r["slug"] for c in current["categories"].values() for r in c["products"]}
    current_slug = {s: s for s in live} | {
        old: new for old, new in current["aliases"]["products"].items() if new in live}
    prows, crows = [], []
    tags = release_tags()
    for version, commit in tags:
        try:
            payload = json.loads(_git("show", f"{commit}:build/notebook_data.json"))
        except subprocess.CalledProcessError:
            continue
        needs_names = any("slug" not in r for c in payload["categories"].values()
                          for r in c["products"])
        p, c = _snapshot_rows(payload, version, parse_date(release_date(version)), commit,
                              _slugs_by_name(commit) if needs_names else None, current_slug)
        prows += p
        crows += c
    # Between releases, the working tree is newer than any tag. Include it labelled as a
    # pre-release of the next version so a preview shows the full series; --push refuses it.
    if not any(sha == head for _, sha in tags):
        p, c = _snapshot_rows(current, f"{current_version}+{head[:8]}", None, head, None,
                              current_slug)
        prows += p
        crows += c
    return {"product_history": _table(prows, PRODUCT_HISTORY_SCHEMA),
            "category_history": _table(crows, CATEGORY_HISTORY_SCHEMA)}


# --- card, manifest, push ----------------------------------------------------------------------

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(out: Path, tables: dict[str, pa.Table], payload: dict, head: str,
          released_tag: bool, repo_id: str) -> dict:
    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, table in tables.items():
        path = data / f"{name}.parquet"
        pq.write_table(table, path, compression="zstd")
        files[f"data/{name}.parquet"] = {"rows": table.num_rows, "sha256": _sha256(path)}

    versions = list(dict.fromkeys(tables["product_history"].column("version").to_pylist()))
    manifest = {
        "dataset": "os-ai-map",
        "version": payload["version"],
        "released": payload["released"] if released_tag else None,
        "generated": payload["generated"],
        "source_repository": "https://github.com/currentai-org/os-ai-map",
        "source_commit": head,
        "release_tag": f"v{payload['version']}" if released_tag else None,
        "payload_contract": PAYLOAD_CONTRACT,
        "history_versions": versions,
        "files": files,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    t = tables
    card = Template(CARD_TEMPLATE.read_text()).substitute(
        repo_id=repo_id,
        year=(payload["released"] if released_tag else payload["generated"])[:4],
        version=payload["version"],
        version_line=(f"{payload['version']}, released {payload['released']}" if released_tag
                      else f"{payload['version']}+{head[:8]} (unreleased preview; do not publish)"),
        commit=head,
        n_products=f"{t['products'].num_rows:,}",
        n_organizations=f"{t['organizations'].num_rows:,}",
        n_categories=f"{t['categories'].num_rows:,}",
        n_citations=f"{t['citations'].num_rows:,}",
        n_product_history=f"{t['product_history'].num_rows:,}",
        n_category_history=f"{t['category_history'].num_rows:,}",
        n_releases=len(versions),
        first_release=versions[0] if versions else "",
        size_category=_size_category(t["products"].num_rows + t["citations"].num_rows),
    )
    (out / "README.md").write_text(card)
    return manifest


def _size_category(n: int) -> str:
    for limit, label in ((1_000, "n<1K"), (10_000, "1K<n<10K"), (100_000, "10K<n<100K"),
                         (1_000_000, "100K<n<1M")):
        if n < limit:
            return label
    return "n>1M"


def push(out: Path, repo_id: str, version: str) -> None:
    from huggingface_hub import HfApi  # token from HF_TOKEN or the cached login
    api = HfApi()
    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    commit = api.upload_folder(repo_id=repo_id, repo_type="dataset", folder_path=str(out),
                               commit_message=f"Release v{version}",
                               delete_patterns=["data/*.parquet"])
    api.create_tag(repo_id, repo_type="dataset", tag=f"v{version}",
                   revision=commit.oid, tag_message=f"os-ai-map v{version}")
    print(f"pushed {repo_id} @ v{version} ({commit.commit_url})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "hf")
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID,
                        help=f"Hugging Face dataset repo the card names (default: {DEFAULT_REPO_ID})")
    parser.add_argument("--push", action="store_true",
                        help="upload to --repo-id and tag it vX.Y.Z; refused unless HEAD is the "
                             "vX.Y.Z release tag. Token from HF_TOKEN or `hf auth login`.")
    args = parser.parse_args()

    from build.validate import load_sources
    from build.freshness_payload import resolve_freshness

    version = repo_version()
    head = _git("rev-parse", "HEAD").strip()
    tagged = dict(release_tags()).get(version) == head
    if args.push and not tagged:
        raise SystemExit(f"refusing to push: HEAD {head[:8]} is not the v{version} release tag. "
                         "Cut the release first (skills/publish-release), then export from the tag.")

    sources = load_sources(ROOT)
    frozen = json.load(open(ROOT / "sources" / "snapshots" / "long_tail.json"))
    payload = build_payload(sources, frozen, freshness=resolve_freshness(ROOT),
                            generated=datetime.now(timezone.utc).date().isoformat())
    tables = current_tables(sources, payload) | history_tables(payload, version, head)

    manifest = write(args.out, tables, payload, head, tagged, args.repo_id)
    for name, f in manifest["files"].items():
        print(f"  {name:32} {f['rows']:>7,} rows")
    print(f"wrote {args.out} (v{version}{'' if tagged else ' +unreleased'}, commit {head[:8]})")

    if args.push:
        push(args.out, args.repo_id, version)


if __name__ == "__main__":
    main()
