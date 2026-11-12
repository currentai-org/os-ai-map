"""Export the published map as a Hugging Face dataset: Parquet tables, a manifest, and a card.

    uv run python -m build.export_hf                          # → dist/hf/, history verified
    uv run python -m build.export_hf --no-verify-history      # fast preview, history unverified
    uv run python -m build.export_hf --rehearse --repo-id ORG/PRIVATE-TEST   # dry run of a publish
    uv run python -m build.export_hf --push                   # publish (maintainer, at a release tag)

Six tables, one Hugging Face config each:

* ``products``          one row per published product: identity, the three axes, overall score,
                        tier, and artifact links. Built from ``build_payload``, so every number is
                        the one the map shows.
* ``organizations``     one row per organization that owns or stewards a published product.
* ``categories``        one row per published category: stage, gaps, weights, roster counts.
* ``citations``         one row per cited source behind a published product's axis score, read
                        from ``sources/scores/`` directly: the full audit trail, not the payload's
                        trimmed copy.
* ``product_history``   one row per (release, product): the axes and overall score as each
                        release tag's build output records them.
* ``category_history``  one row per (release, category): stage and gaps per release tag.

The history tables read ``build/notebook_data.json`` at each ``v*`` tag, and verify it against a
rebuild of that tag's own sources with that tag's own code (see "history tables" below). They
record each release as it was built, not a recomputation under today's rules, so a value can move
between releases because the method changed as well as because the product did. They do not
record when the live site showed a release; the card says both.

Scope: published categories only (preliminary categories and the long tail are left out, as on
the map). The long-tail snapshot is excluded on purpose: it carries third-party catalog content.

Nothing here writes to ``sources/`` or the warehouse. ``dist/`` is build output and is not
committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from string import Template

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from build.serialize import ROOT, PAYLOAD_CONTRACT, build_payload, release_date, repo_version
from build.vocabulary import axes, lineage_relations, parse_date

ARTIFACT_KINDS = ("github", "pypi", "npm", "crates", "go", "huggingface_model",
                  "huggingface_dataset", "arxiv")
# The one dataset a release may publish to. Moving it is a reviewed change, not a flag.
RELEASE_REPO_ID = "current-ai-official/os-ai-map"
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
#
# A history snapshot is the build output committed at a release tag. Two facts about that file
# matter, and the export checks both instead of assuming them:
#
# * The regeneration bot rewrites it after a merge that changes the map's inputs, but not after
#   a release commit, which only touches CHANGELOG.md and pyproject.toml. So the payload at a tag
#   can carry the PREVIOUS release's version label. That is tolerated only for the one release
#   immediately before, and only once the content is proven current (below). Any other label is
#   an error.
# * Being committed at the tag does not by itself prove the content is the tag's. A merge whose
#   regeneration had not landed when the tag was cut would leave a payload one step behind. So
#   every tag is rebuilt with its OWN serializer from its OWN sources, in a throwaway worktree,
#   and the committed payload must equal the rebuild in everything but build metadata.
#
# Neither check says when the live site showed a release: the site is published by a separate
# maintainer step (docs/operations/publish-map.md) that leaves no record in git. The card says
# so.

SNAPSHOT_META = [("version", STR), ("released", DATE), ("source_commit", STR),
                 ("payload_commit", STR), ("payload_generated", DATE)]

PRODUCT_HISTORY_SCHEMA = pa.schema([
    *SNAPSHOT_META,
    ("product_slug", STR), ("current_slug", STR), ("name", STR), ("category_slug", STR),
    ("openness_score", INT), ("openness_class", STR),
    ("adoption_level", INT), ("adoption_reach", STR), ("capability_score", INT),
    ("overall_score", FLOAT), ("tier", STR), ("mature", BOOL),
])

CATEGORY_HISTORY_SCHEMA = pa.schema([
    *SNAPSHOT_META,
    ("category_slug", STR), ("name", STR), ("stage_num", INT), ("stage_name", STR),
    ("gaps", STRS), ("product_count", INT), ("leading_count", INT), ("mature_count", INT),
])

# Build metadata, not map content: when and as which version a payload was written. The
# per-product `freshness` block is dated from git history and is excluded for the same reason.
# `long_tail` is not exported.
_BUILD_METADATA = ("generated", "version", "released", "contract", "long_tail")
_REBUILD_DATE = "2000-01-01"


class HistoryError(RuntimeError):
    """A release snapshot whose provenance cannot be established."""


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


def payload_content(payload: dict) -> dict:
    """The map content of a payload: everything but build metadata and freshness."""
    out = {k: v for k, v in payload.items() if k not in _BUILD_METADATA}
    out["categories"] = {
        cid: {**cat, "products": [{k: v for k, v in r.items() if k != "freshness"}
                                  for r in cat["products"]]}
        for cid, cat in payload["categories"].items()}
    return out


def rebuild_payload(commit: str, workdir: Path) -> dict:
    """Serialize ``commit``'s sources with ``commit``'s own build code, in a throwaway worktree."""
    wt = workdir / commit[:12]
    _git("worktree", "add", "--detach", "--force", str(wt), commit)
    # The rebuild must use the worktree's own locked environment, not this one's.
    env = {k: v for k, v in os.environ.items()
           if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")}
    try:
        for cmd in (["uv", "sync", "--locked", "--quiet"],
                    ["uv", "run", "--locked", "python", "-m", "build.serialize",
                     "--date", _REBUILD_DATE]):
            subprocess.run(cmd, cwd=wt, env=env, check=True, capture_output=True, text=True)
        return json.loads((wt / "build" / "notebook_data.json").read_text())
    except subprocess.CalledProcessError as e:
        raise HistoryError(f"could not rebuild {commit[:8]}: {' '.join(e.cmd)}\n{e.stderr}") from e
    finally:
        _git("worktree", "remove", "--force", str(wt))


def verify_snapshot(version: str, previous: str | None, committed: dict,
                    rebuilt: dict | None) -> str:
    """Return how ``committed`` (the payload at tag ``v<version>``) was verified, or raise.

    ``previous`` is the release before this one. ``rebuilt`` is the tag rebuilt from its own
    sources; None means verification was skipped, which only a preview may do.
    """
    label = committed.get("version")
    # Payloads before the 0.3.0 contract carry no version label at all.
    if label not in (None, version, previous):
        raise HistoryError(f"the payload at v{version} labels itself {label!r}, which is neither "
                           f"this release nor the one before it")
    if rebuilt is None:
        return "unverified"
    if payload_content(committed) != payload_content(rebuilt):
        raise HistoryError(f"the payload committed at v{version} differs from a rebuild of that "
                           f"tag's sources; it does not describe the release it is tagged with")
    if label not in (None, version):
        return "rebuilt-identical; version label lags the tag"
    return "rebuilt-identical"


def _snapshot_rows(payload: dict, meta: dict, name_to_slug: dict[str, str] | None,
                   current_slug: dict[str, str]):
    meta = {**meta, "payload_generated": parse_date(payload.get("generated"))}
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


def history_tables(current: dict, current_version: str, head: str,
                   verify: bool = True) -> tuple[dict[str, pa.Table], list[dict]]:
    """The two history tables, and one provenance record per snapshot for the manifest."""
    # A slug retired since a release still joins to today's products through the alias index
    # (identity.md). A product merged without a recorded alias gets a null current_slug.
    live = {r["slug"] for c in current["categories"].values() for r in c["products"]}
    current_slug = {s: s for s in live} | {
        old: new for old, new in current["aliases"]["products"].items() if new in live}

    tags = []
    for version, commit in release_tags():
        try:
            payload = json.loads(_git("show", f"{commit}:build/notebook_data.json"))
        except subprocess.CalledProcessError:
            continue  # a tag from before the payload existed
        tags.append((version, commit, payload))

    rebuilt: dict[str, dict] = {}
    if verify and tags:
        with tempfile.TemporaryDirectory(prefix="export-hf-") as tmp, \
                ThreadPoolExecutor(max_workers=4) as pool:
            futures = {c: pool.submit(rebuild_payload, c, Path(tmp)) for _, c, _ in tags}
            rebuilt = {c: f.result() for c, f in futures.items()}

    prows, crows, provenance = [], [], []
    previous = None
    for version, commit, payload in tags:
        how = verify_snapshot(version, previous, payload, rebuilt.get(commit))
        payload_commit = _git("log", "-1", "--format=%H", commit, "--",
                              "build/notebook_data.json").strip()
        meta = {"version": version, "released": parse_date(release_date(version)),
                "source_commit": commit, "payload_commit": payload_commit}
        needs_names = any("slug" not in r for c in payload["categories"].values()
                          for r in c["products"])
        p, c = _snapshot_rows(payload, meta, _slugs_by_name(commit) if needs_names else None,
                              current_slug)
        prows += p
        crows += c
        provenance.append({"version": version, "tag_commit": commit,
                           "payload_commit": payload_commit,
                           "payload_version_label": payload.get("version"),
                           "verification": how})
        previous = version
    # Between releases, the working tree is newer than any tag. Include it labelled as a
    # pre-release of the next version so a preview shows the full series; a push refuses it.
    if not any(c == head for _, c, _ in tags):
        meta = {"version": f"{current_version}+{head[:8]}", "released": None,
                "source_commit": head, "payload_commit": None}
        p, c = _snapshot_rows(current, meta, None, current_slug)
        prows += p
        crows += c
        provenance.append({"version": meta["version"], "tag_commit": None,
                           "payload_commit": None, "payload_version_label": None,
                           "verification": "built in this run (unreleased)"})
    return ({"product_history": _table(prows, PRODUCT_HISTORY_SCHEMA),
             "category_history": _table(crows, CATEGORY_HISTORY_SCHEMA)}, provenance)


# --- card and manifest -------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_sha256(table: pa.Table) -> str:
    """A digest of a table's rows that does not depend on the Parquet writer's version.

    File bytes change with the writer (its version string is in the footer), so they cannot
    decide whether a re-run produced the same release. This can.
    """
    rows = json.dumps(table.to_pylist(), sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(f"{table.schema}\n{rows}".encode()).hexdigest()


def write(out: Path, tables: dict[str, pa.Table], payload: dict, head: str,
          release_tag: str | None, repo_id: str, provenance: list[dict]) -> dict:
    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, table in tables.items():
        path = data / f"{name}.parquet"
        pq.write_table(table, path, compression="zstd")
        files[f"data/{name}.parquet"] = {"rows": table.num_rows, "sha256": _sha256(path),
                                         "content_sha256": content_sha256(table)}

    released = release_tag is not None and TAG_RE.match(release_tag) is not None
    versions = [p["version"] for p in provenance]
    manifest = {
        "dataset": "os-ai-map",
        "version": payload["version"],
        "released": payload["released"] if released else None,
        "generated": payload["generated"],
        "source_repository": "https://github.com/currentai-org/os-ai-map",
        "source_commit": head,
        "release_tag": release_tag,
        "payload_contract": PAYLOAD_CONTRACT,
        "history_verified": all(p["verification"] != "unverified" for p in provenance),
        "history": provenance,
        "files": files,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    t = tables
    card = Template(CARD_TEMPLATE.read_text()).substitute(
        repo_id=repo_id,
        year=(payload["released"] if released else payload["generated"])[:4],
        version=payload["version"],
        version_line=(f"{payload['version']}, released {payload['released']}" if released
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


# --- push --------------------------------------------------------------------------------------
#
# A dataset tag, like a git release tag, is immutable once pushed. So a push is a function of
# what the tag already holds:
#
#   tag absent                      → upload on top of the head just read (parent_commit), read
#                                     the manifest back at the commit the upload returned, and
#                                     tag exactly that commit
#   tag present, same release       → nothing to do (a re-run after a later step failed)
#   tag present, different release  → refuse; never move a released tag
#
# "Same release" compares the source commit, the version and every table's content digest, not
# file bytes or the build date, so a re-run with a newer Parquet writer or on a later day is
# still recognized as the release it is.

def same_release(a: dict, b: dict) -> bool:
    def key(m: dict):
        return (m.get("source_commit"), m.get("version"), m.get("release_tag"),
                {p: f.get("content_sha256") for p, f in (m.get("files") or {}).items()})
    return key(a) == key(b)


def _remote_manifest(api, repo_id: str, revision: str) -> dict | None:
    try:
        path = api.hf_hub_download(repo_id, "manifest.json", repo_type="dataset",
                                   revision=revision)
    except Exception:  # noqa: BLE001 - a missing file and a missing revision both mean "none"
        return None
    return json.loads(Path(path).read_text())


def token_diagnosis(api, repo_id: str) -> str:
    """Why a token might not see ``repo_id``, without printing anything secret or personal.

    Hugging Face answers 404 alike for a private repo that does not exist and one the token
    cannot see, and an unset HF_TOKEN makes every request anonymous. This separates the cases.
    The Actions log is public, so it names no account: only the token's kind, whether its
    account belongs to the repo's organization, and which of that organization's resources a
    fine-grained token is scoped to.
    """
    org = repo_id.split("/")[0]
    try:
        me = api.whoami()
    except Exception as e:  # noqa: BLE001
        return f"none accepted ({type(e).__name__}); is the HF_TOKEN secret set?"
    member = org in {o.get("name") for o in me.get("orgs") or []}
    access = (me.get("auth") or {}).get("accessToken") or {}
    role = access.get("role")
    out = [f"accepted, kind {role!r}", f"its account is {'' if member else 'NOT '}a member of {org}"]
    if role == "fineGrained":
        scoped = (access.get("fineGrained") or {}).get("scoped") or []
        mine = [s for s in scoped if (s.get("entity") or {}).get("name", "").split("/")[0] == org]
        listed = [f"{s['entity'].get('type')} {s['entity'].get('name')} "
                  f"({', '.join(sorted(s.get('permissions') or []))})" for s in mine]
        out.append(f"scoped to {'; '.join(listed) if listed else f'nothing under {org}'}"
                   f" (+{len(scoped) - len(mine)} other grants)")
    return ", ".join(out)


def push(out: Path, repo_id: str, tag: str, *, private: bool, require_new: bool = False,
         api=None) -> str:
    """Publish ``out`` to ``repo_id`` as ``tag``. Returns "published" or "unchanged".

    ``require_new`` refuses a tag that already exists, so a caller that must prove a fresh
    upload happened (a rehearsal) cannot pass on an earlier run's tag.
    """
    if api is None:
        from huggingface_hub import HfApi  # token from HF_TOKEN or `hf auth login`
        api = HfApi()
    local = json.loads((out / "manifest.json").read_text())
    if local.get("release_tag") != tag:
        raise SystemExit(f"the export in {out} was built for {local.get('release_tag')!r}, not {tag}")

    try:
        info = api.repo_info(repo_id, repo_type="dataset")
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"refusing to push: dataset {repo_id} is not reachable ({e}).\n"
                         f"Token: {token_diagnosis(api, repo_id)}.\n"
                         f"The dataset must exist under the right organization, and the token must "
                         f"be able to see it, before the first push.")
    if bool(info.private) != private:
        want = "private (a rehearsal target)" if private else "public (the release target)"
        raise SystemExit(f"refusing to push: {repo_id} must be {want}")

    existing = {r.name for r in api.list_repo_refs(repo_id, repo_type="dataset").tags}
    if tag in existing and require_new:
        raise SystemExit(f"refusing to push: {repo_id} already has tag {tag}, and this run must "
                         f"make a fresh upload")
    if tag in existing:
        remote = _remote_manifest(api, repo_id, tag)
        if remote is not None and same_release(remote, local):
            print(f"{repo_id} @ {tag} already holds this release; nothing to do")
            return "unchanged"
        raise SystemExit(f"refusing to push: {repo_id} already has tag {tag} with different "
                         f"content. Tags are immutable; fix forward with a new release.")

    # Tag the commit this upload returns, never the branch head read afterwards: another writer
    # can move the head between the two calls. `parent_commit` makes the upload itself fail if
    # the branch moved after `info` was read. One case still returns a commit this upload did not
    # make: when nothing changed (a retry after the tag step failed), the library skips the empty
    # commit and returns the head as it stands. So the manifest is read back at the returned
    # commit before anything is tagged.
    uploaded = api.upload_folder(repo_id=repo_id, repo_type="dataset", folder_path=str(out),
                                 commit_message=f"Release {tag}",
                                 delete_patterns=["data/*.parquet"], parent_commit=info.sha)
    revision = uploaded.oid
    remote = _remote_manifest(api, repo_id, revision)
    if remote is None or not same_release(remote, local):
        raise SystemExit(f"refusing to tag: {repo_id}@{revision[:8]} does not carry this "
                         f"export's manifest. Nothing was tagged.")
    api.create_tag(repo_id, repo_type="dataset", tag=tag, revision=revision,
                   tag_message=f"os-ai-map {tag}")
    tagged = _remote_manifest(api, repo_id, tag)
    if tagged is None or not same_release(tagged, local):
        raise SystemExit(f"{repo_id} @ {tag} was created but does not read back as this release")
    print(f"published {repo_id} @ {tag} (revision {revision[:8]}, "
          f"source {local['source_commit'][:8]})")
    return "published"


def rehearsal_tag(head: str, now: datetime) -> str:
    """A tag no earlier rehearsal can have used, so every rehearsal makes a fresh upload."""
    return f"rehearsal-{head[:8]}-{now.strftime('%Y%m%dT%H%M%SZ')}"


def rehearse(out: Path, repo_id: str, tag: str, api=None) -> None:
    """Both publish paths against a private dataset: a first publication, then a retry.

    The first call must upload and tag (the tag may not exist beforehand); the second must find
    the release already there and change nothing.
    """
    if push(out, repo_id, tag, private=True, require_new=True, api=api) != "published":
        raise SystemExit("rehearsal failed: the first publish did not upload")
    if push(out, repo_id, tag, private=True, api=api) != "unchanged":
        raise SystemExit("rehearsal failed: the second publish of the same release was not "
                         "a no-op")
    print(f"rehearsal passed: {repo_id} @ {tag} published, then re-published as a no-op")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "hf")
    parser.add_argument("--repo-id", default=RELEASE_REPO_ID,
                        help=f"dataset repo the card names and a rehearsal pushes to "
                             f"(default: {RELEASE_REPO_ID})")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--push", action="store_true",
                      help=f"publish to {RELEASE_REPO_ID} as vX.Y.Z. Refused unless HEAD is that "
                           f"release tag, the history verifies, and the dataset is public.")
    mode.add_argument("--rehearse", action="store_true",
                      help="exercise the whole publish path against a PRIVATE --repo-id, from any "
                           "commit: publish under a fresh rehearsal tag, then publish again and "
                           "require the second run to change nothing.")
    parser.add_argument("--no-verify-history", action="store_true",
                        help="skip rebuilding each release tag (fast preview); a push refuses it")
    args = parser.parse_args()

    from build.validate import load_sources
    from build.freshness_payload import resolve_freshness

    version = repo_version()
    head = _git("rev-parse", "HEAD").strip()
    tagged = dict(release_tags()).get(version) == head
    if args.push:
        if args.repo_id != RELEASE_REPO_ID:
            raise SystemExit(f"refusing to push: releases go to {RELEASE_REPO_ID} only "
                             f"(change RELEASE_REPO_ID in a reviewed PR to move it)")
        if not tagged:
            raise SystemExit(f"refusing to push: HEAD {head[:8]} is not the v{version} release "
                             "tag. Cut the release first (skills/publish-release), then export "
                             "from the tag.")
    if args.rehearse and args.repo_id == RELEASE_REPO_ID:
        raise SystemExit("refusing to rehearse against the release dataset; pass a private "
                         "--repo-id")
    if (args.push or args.rehearse) and args.no_verify_history:
        raise SystemExit("refusing to publish an export whose history was not verified")

    sources = load_sources(ROOT)
    frozen = json.load(open(ROOT / "sources" / "snapshots" / "long_tail.json"))
    payload = build_payload(sources, frozen, freshness=resolve_freshness(ROOT),
                            generated=datetime.now(timezone.utc).date().isoformat())
    history, provenance = history_tables(payload, version, head,
                                         verify=not args.no_verify_history)
    tables = current_tables(sources, payload) | history

    tag = (rehearsal_tag(head, datetime.now(timezone.utc)) if args.rehearse
           else f"v{version}" if tagged else None)
    manifest = write(args.out, tables, payload, head, tag, args.repo_id, provenance)
    for name, f in manifest["files"].items():
        print(f"  {name:32} {f['rows']:>7,} rows")
    for p in provenance:
        print(f"  history {p['version']:20} {p['verification']}")
    print(f"wrote {args.out} (v{version}{'' if tagged else ' +unreleased'}, commit {head[:8]})")

    if args.push:
        push(args.out, RELEASE_REPO_ID, tag, private=False)
    elif args.rehearse:
        rehearse(args.out, args.repo_id, tag)


if __name__ == "__main__":
    main()
