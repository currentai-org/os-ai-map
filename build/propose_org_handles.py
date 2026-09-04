"""Propose Hugging Face org handles from declared artifact namespaces, for human review.

`sources/org_handles.yaml` records which platform accounts an organization publishes
under, but only two organizations declare a `huggingface` handle even though 136 HF
models and 82 HF datasets are declared artifacts of head products (plus more on the tail
registry) -- the identity graph's org recall is bounded by that gap (see
docs/reference/identity.md, "Handles are ownership evidence, not adoption evidence"). A
namespace on the Hub is not proof of ownership by itself: `TheBloke` republishes other
people's weights under its own account, so seeding a handle straight from a namespace
risks recording a mirror as the owning org.

This module proposes instead of seeding. For every declared `huggingface_model` /
`huggingface_dataset` artifact of a head or tail product, it takes the namespace (the
text before the first `/`) and groups it by the product's own organization. A namespace
becomes a proposal for an org when it uniquely identifies that org in the corpus, is not
already declared (by that org or another), and is not a known mirror/aggregator account.
A namespace that maps to more than one organization -- in the corpus itself, or against
an already-declared handle for a different org -- is listed under "conflicts" instead of
guessed at, since a shared namespace is exactly the ambiguous case a reviewer, not a
script, should resolve.

Nothing here writes to `sources/org_handles.yaml`. The output is a checklist a person
reviews once and a fenced YAML block they can paste in; see docs/reference/identity.md,
"Proposing handles".

Usage:
    uv run python -m build.propose_org_handles --out PATH
    uv run python -m build.propose_org_handles --out PATH --check-graph
"""
from __future__ import annotations

import argparse
from pathlib import Path

from build.identity import id_from_url
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]

HF_KINDS = ("huggingface_model", "huggingface_dataset")

# Hugging Face accounts known to republish or re-quantize other orgs' models under their
# own namespace, rather than being the org that trained or curated the artifact. A product
# declared under one of these namespaces is not ownership evidence for the account holder,
# so a namespace in this set is never proposed as anyone's handle -- listed separately
# instead. Extend this set as new mirrors turn up in the corpus; do not remove an entry
# just because one instance under it looks legitimate, since the exclusion is about the
# namespace's general behavior, not any single artifact.
KNOWN_AGGREGATORS = {
    "thebloke",
    "bartowski",
    "unsloth",
    "mlx-community",
    "lmstudio-community",
    "quantfactory",
    "mradermacher",
    "huggingface",
    "hf-internal-testing",
    "open-llm-leaderboard",
}


def _urls(value: object) -> list[str]:
    """Artifact values are lists of {url: ...}; tolerate a bare string too."""
    out: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("url"), str):
                out.append(item["url"])
            elif isinstance(item, str):
                out.append(item)
    elif isinstance(value, str):
        out.append(value)
    return out


def product_org_map(organizations: dict) -> dict[str, str]:
    """product_slug -> org_slug, derived the same way build/serialize_registry.py derives
    its `product_organizations` table: membership is declared on the organization's own
    `products` roster, not on the product record."""
    out: dict[str, str] = {}
    for org_slug, org in (organizations or {}).items():
        if not isinstance(org, dict):
            continue
        for product_slug in org.get("products") or []:
            if isinstance(product_slug, str):
                out[product_slug] = org_slug
    return out


def declared_hf_handles(org_handles: dict) -> dict[str, str]:
    """Folded huggingface handle -> owning org_slug, from sources/org_handles.yaml."""
    out: dict[str, str] = {}
    for entry in (org_handles or {}).get("handles") or []:
        if not isinstance(entry, dict) or entry.get("platform") != "huggingface":
            continue
        handle, org_slug = entry.get("handle"), entry.get("org")
        if isinstance(handle, str) and isinstance(org_slug, str):
            out[handle.casefold()] = org_slug
    return out


def github_handles_by_org(org_handles: dict) -> dict[str, list[str]]:
    """org_slug -> declared github handles, used for the name-agreement flag."""
    out: dict[str, list[str]] = {}
    for entry in (org_handles or {}).get("handles") or []:
        if not isinstance(entry, dict) or entry.get("platform") != "github":
            continue
        org_slug, handle = entry.get("org"), entry.get("handle")
        if isinstance(org_slug, str) and isinstance(handle, str):
            out.setdefault(org_slug, []).append(handle)
    return out


def name_agrees(namespace: str, org_slug: str, github_handles: list[str]) -> bool:
    """Whether `namespace` equals or contains the org slug, or matches a declared GitHub
    handle for that org -- folded and punctuation-insensitive, so `openai` agrees with
    `openai` and `nvidia-nim` agrees with `nvidia`."""

    def norm(s: str) -> str:
        return s.casefold().replace("-", "").replace("_", "").replace(".", "")

    ns, org = norm(namespace), norm(org_slug)
    if ns == org or (org and org in ns) or (ns and ns in org):
        return True
    return any(norm(h) == ns for h in github_handles)


def collect_occurrences(sources: dict) -> list[tuple[str, str, str]]:
    """(namespace, org_slug, product_slug) triples, one per declared HF artifact, across
    head products (sources/products/*.yaml) and tail registry rows
    (sources/registry/*.yaml). A product declaring both a model and a dataset under the
    same namespace contributes two occurrences -- the evidence count is meant to reflect
    declared artifacts, not distinct products."""
    occurrences: list[tuple[str, str, str]] = []
    org_of = product_org_map(sources.get("organizations") or {})

    for slug, product in (sources.get("products") or {}).items():
        org_slug = org_of.get(slug)
        if not org_slug or not isinstance(product, dict):
            continue
        for kind in HF_KINDS:
            for url in _urls(product.get(kind)):
                ident = id_from_url(kind, url)
                if ident is None:
                    continue
                namespace = ident.split("/", 1)[0]
                occurrences.append((namespace, org_slug, slug))

    for record in (sources.get("registry") or {}).values():
        if not isinstance(record, dict):
            continue
        for row in record.get("products") or []:
            if not isinstance(row, dict):
                continue
            org_slug, slug = row.get("org"), row.get("slug")
            if not (isinstance(org_slug, str) and isinstance(slug, str)):
                continue
            for kind in HF_KINDS:
                value = row.get(kind)
                if isinstance(value, str) and "/" in value:
                    namespace = value.split("/", 1)[0].strip()
                    if namespace:
                        occurrences.append((namespace, org_slug, slug))
    return occurrences


def group_by_namespace(occurrences: list[tuple[str, str, str]]) -> dict[str, dict]:
    """Folded namespace -> {raw_forms, by_org}, where `by_org` maps org_slug to the list
    of product slugs (with repeats -- one per declared artifact) seen under that
    namespace for that org."""
    groups: dict[str, dict] = {}
    for namespace, org_slug, product_slug in occurrences:
        key = namespace.casefold()
        group = groups.setdefault(key, {"raw_forms": set(), "by_org": {}})
        group["raw_forms"].add(namespace)
        group["by_org"].setdefault(org_slug, []).append(product_slug)
    return groups


def graph_agreement_pairs(rows: list[dict]) -> set[tuple[str, str]]:
    """(folded namespace, org_slug) pairs the identity graph already infers at >=0.8 via
    an `hf_namespace` method, from rows shaped like the query in `fetch_graph_rows`."""
    pairs: set[tuple[str, str]] = set()
    for row in rows:
        key, org_slug, confidence = row.get("candidate_key"), row.get("org_slug"), row.get("confidence")
        if not (isinstance(key, str) and isinstance(org_slug, str) and isinstance(confidence, (int, float))):
            continue
        if confidence < 0.8 or ":" not in key:
            continue
        artifact_part = key.split(":", 1)[1]
        namespace = artifact_part.split("/", 1)[0]
        pairs.add((namespace.casefold(), org_slug))
    return pairs


def fetch_graph_rows() -> list[dict]:
    """Live read of the candidate org edges an `hf_namespace` method already infers.
    Requires OSO_API_KEY; only called when `--check-graph` is passed."""
    from build.warehouse import query

    sql = (
        "SELECT candidate_key, org_slug, confidence FROM currentai.identity.org_edges "
        "WHERE candidate_tier IN ('head', 'tail') AND contains(method, 'hf_namespace') "
        "AND confidence >= 0.8"
    )
    return query(sql)


def build_report(sources: dict, graph_pairs: set[tuple[str, str]] | None = None) -> dict:
    """Return {"proposals": [...], "conflicts": [...], "excluded": [...]}."""
    occurrences = collect_occurrences(sources)
    groups = group_by_namespace(occurrences)
    declared = declared_hf_handles(sources.get("org_handles") or {})
    gh_by_org = github_handles_by_org(sources.get("org_handles") or {})

    proposals: list[dict] = []
    conflicts: list[dict] = []
    excluded: list[dict] = []

    for key in sorted(groups):
        group = groups[key]
        display_ns = sorted(group["raw_forms"])[0]
        orgs = sorted(group["by_org"])

        if key in KNOWN_AGGREGATORS:
            products = sorted({p for org_products in group["by_org"].values() for p in org_products})
            excluded.append({
                "namespace": display_ns,
                "count": sum(len(v) for v in group["by_org"].values()),
                "products": products,
            })
            continue

        if len(orgs) > 1:
            conflicts.append({
                "namespace": display_ns,
                "reason": "namespace is declared under more than one organization in the corpus",
                "orgs": {org: sorted(set(group["by_org"][org])) for org in orgs},
            })
            continue

        org_slug = orgs[0]
        products = sorted(set(group["by_org"][org_slug]))
        count = len(group["by_org"][org_slug])
        existing_owner = declared.get(key)
        if existing_owner == org_slug:
            continue  # already declared -- nothing to propose
        if existing_owner and existing_owner != org_slug:
            conflicts.append({
                "namespace": display_ns,
                "reason": f"already declared as a huggingface handle for organization '{existing_owner}'",
                "orgs": {org_slug: products},
            })
            continue

        proposals.append({
            "org": org_slug,
            "namespace": display_ns,
            "count": count,
            "products": products,
            "name_agrees": name_agrees(display_ns, org_slug, gh_by_org.get(org_slug, [])),
            "graph_agrees": bool(graph_pairs) and (key, org_slug) in graph_pairs,
            "example_url": f"https://huggingface.co/{display_ns}",
        })

    proposals.sort(key=lambda p: (p["org"], p["namespace"]))
    conflicts.sort(key=lambda c: c["namespace"])
    excluded.sort(key=lambda e: e["namespace"])
    return {"proposals": proposals, "conflicts": conflicts, "excluded": excluded}


def render_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append(
        "Ticking a box and pasting the matching entry from the YAML block below into "
        "`sources/org_handles.yaml` in a PR is what persists that handle. An unticked "
        "proposal is simply not adopted -- nothing here writes anything on its own."
    )
    lines.append("")
    lines.append("## Proposals")
    lines.append("")
    if not report["proposals"]:
        lines.append("None.")
    for p in report["proposals"]:
        products = ", ".join(p["products"])
        yn = "yes" if p["name_agrees"] else "no"
        line = (
            f"- [ ] {p['org']} ← huggingface `{p['namespace']}` "
            f"({p['count']} artifacts: {products}) name-agrees: {yn}"
        )
        if p["graph_agrees"]:
            line += " (graph agrees)"
        lines.append(line)
    lines.append("")

    lines.append("```yaml")
    for p in report["proposals"]:
        lines.append(f"- org: {p['org']}")
        lines.append("  platform: huggingface")
        lines.append(f"  handle: {p['namespace']}")
    lines.append("```")
    lines.append("")

    lines.append("## Conflicts")
    lines.append("")
    lines.append(
        "Ambiguous namespace attribution -- not proposed. Resolve by hand in "
        "`sources/org_handles.yaml` if the ownership is actually clear."
    )
    lines.append("")
    if not report["conflicts"]:
        lines.append("None.")
    for c in report["conflicts"]:
        org_bits = "; ".join(f"{org} ({', '.join(products)})" for org, products in sorted(c["orgs"].items()))
        lines.append(f"- huggingface `{c['namespace']}` -- {c['reason']}: {org_bits}")
    lines.append("")

    lines.append("## Excluded aggregators")
    lines.append("")
    lines.append(
        "Known mirror/republish accounts (`KNOWN_AGGREGATORS` in "
        "`build/propose_org_handles.py`) -- never proposed as an owning organization's handle."
    )
    lines.append("")
    if not report["excluded"]:
        lines.append("None.")
    for e in report["excluded"]:
        products = ", ".join(e["products"])
        lines.append(f"- huggingface `{e['namespace']}` ({e['count']} artifacts: {products})")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Propose huggingface org handles from declared artifacts.")
    parser.add_argument("--out", type=Path, required=True, help="Path to write the rendered markdown.")
    parser.add_argument(
        "--check-graph",
        action="store_true",
        help="Cross-check proposals against currentai.identity.org_edges (needs OSO_API_KEY).",
    )
    args = parser.parse_args(argv)

    sources = load_sources(ROOT)
    graph_pairs = graph_agreement_pairs(fetch_graph_rows()) if args.check_graph else None
    report = build_report(sources, graph_pairs)
    markdown = render_markdown(report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown)
    print(
        f"{len(report['proposals'])} proposal(s), {len(report['conflicts'])} conflict(s), "
        f"{len(report['excluded'])} excluded aggregator namespace(s) -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
