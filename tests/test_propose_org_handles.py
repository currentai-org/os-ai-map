"""Tests for build/propose_org_handles.py.

Fixture-free by construction: `build_report` takes an in-memory `sources` dict shaped like
`build.validate.load_sources`'s return value, so these never touch the real corpus or the
network. The `--check-graph` path (`fetch_graph_rows`) is exercised only through
`graph_agreement_pairs`, which is pure and takes rows directly.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

from build.propose_org_handles import (
    KNOWN_AGGREGATORS,
    build_report,
    graph_agreement_pairs,
    name_agrees,
    render_markdown,
)

REPO = Path(__file__).resolve().parent.parent


def _sources(*, products=None, organizations=None, registry=None, org_handles=None) -> dict:
    return {
        "products": products or {},
        "organizations": organizations or {},
        "registry": registry or {},
        "org_handles": org_handles or {"version": 1, "handles": []},
    }


def _product(hf_model_urls=()) -> dict:
    return {
        "name": "p",
        "display_name": "P",
        "type": "model",
        "huggingface_model": [{"url": u} for u in hf_model_urls],
    }


def test_proposes_a_namespace_uniquely_tied_to_one_org():
    sources = _sources(
        products={
            "acme-model": _product(["https://huggingface.co/acme-ai/acme-model"]),
        },
        organizations={"acme-ai": {"name": "acme-ai", "products": ["acme-model"]}},
    )
    report = build_report(sources)
    assert len(report["proposals"]) == 1
    p = report["proposals"][0]
    assert p["org"] == "acme-ai"
    assert p["namespace"] == "acme-ai"
    assert p["count"] == 1
    assert p["products"] == ["acme-model"]
    assert p["example_url"] == "https://huggingface.co/acme-ai"
    assert not report["conflicts"]
    assert not report["excluded"]


def test_aggregator_namespace_is_excluded_not_proposed():
    sources = _sources(
        products={
            "some-model": _product(["https://huggingface.co/TheBloke/some-model-GGUF"]),
        },
        organizations={"some-org": {"name": "some-org", "products": ["some-model"]}},
    )
    report = build_report(sources)
    assert not report["proposals"]
    assert not report["conflicts"]
    assert len(report["excluded"]) == 1
    assert report["excluded"][0]["namespace"] == "TheBloke"
    assert report["excluded"][0]["products"] == ["some-model"]


def test_aggregator_matching_is_case_insensitive():
    sources = _sources(
        products={
            "m": _product(["https://huggingface.co/thebloke/m-GGUF"]),
        },
        organizations={"o": {"name": "o", "products": ["m"]}},
    )
    report = build_report(sources)
    assert not report["proposals"]
    assert len(report["excluded"]) == 1


def test_namespace_split_across_two_orgs_is_a_conflict():
    sources = _sources(
        products={
            "a-model": _product(["https://huggingface.co/shared-ns/a-model"]),
            "b-model": _product(["https://huggingface.co/shared-ns/b-model"]),
        },
        organizations={
            "org-a": {"name": "org-a", "products": ["a-model"]},
            "org-b": {"name": "org-b", "products": ["b-model"]},
        },
    )
    report = build_report(sources)
    assert not report["proposals"]
    assert len(report["conflicts"]) == 1
    c = report["conflicts"][0]
    assert c["namespace"] == "shared-ns"
    assert set(c["orgs"]) == {"org-a", "org-b"}


def test_namespace_already_declared_for_another_org_is_a_conflict():
    sources = _sources(
        products={
            "a-model": _product(["https://huggingface.co/claimed-ns/a-model"]),
        },
        organizations={"org-a": {"name": "org-a", "products": ["a-model"]}},
        org_handles={
            "version": 1,
            "handles": [{"org": "org-b", "platform": "huggingface", "handle": "claimed-ns"}],
        },
    )
    report = build_report(sources)
    assert not report["proposals"]
    assert len(report["conflicts"]) == 1
    assert "org-b" in report["conflicts"][0]["reason"]


def test_namespace_already_declared_for_the_same_org_is_skipped_not_proposed_or_conflicted():
    sources = _sources(
        products={
            "a-model": _product(["https://huggingface.co/org-a/a-model"]),
        },
        organizations={"org-a": {"name": "org-a", "products": ["a-model"]}},
        org_handles={
            "version": 1,
            "handles": [{"org": "org-a", "platform": "huggingface", "handle": "org-a"}],
        },
    )
    report = build_report(sources)
    assert not report["proposals"]
    assert not report["conflicts"]
    assert not report["excluded"]


def test_tail_registry_products_contribute_occurrences():
    sources = _sources(
        registry={
            "some_category": {
                "category": "some_category",
                "products": [
                    {
                        "slug": "tail-model",
                        "display_name": "Tail Model",
                        "type": "model",
                        "org": "tail-org",
                        "huggingface_model": "tail-ns/tail-model",
                    }
                ],
            }
        },
        organizations={"tail-org": {"name": "tail-org", "products": []}},
    )
    report = build_report(sources)
    assert len(report["proposals"]) == 1
    assert report["proposals"][0] == {
        "org": "tail-org",
        "namespace": "tail-ns",
        "count": 1,
        "products": ["tail-model"],
        "name_agrees": False,
        "graph_agrees": False,
        "example_url": "https://huggingface.co/tail-ns",
    }


def test_name_agrees_true_when_namespace_equals_org_slug():
    assert name_agrees("openai", "openai", [])


def test_name_agrees_true_on_containment_and_punctuation_insensitivity():
    assert name_agrees("nvidia-nim", "nvidia", [])
    assert name_agrees("nvidia", "nvidia-nim", [])


def test_name_agrees_true_when_matches_a_declared_github_handle():
    assert name_agrees("deepseek-ai", "deepseek", ["deepseek-ai"])


def test_name_agrees_false_when_nothing_matches():
    assert not name_agrees("random-ns", "some-org", ["some-org-gh"])


def test_graph_agreement_pairs_filters_confidence_and_parses_namespace():
    rows = [
        {"candidate_key": "huggingface_model:openai/gpt-oss-20b", "org_slug": "openai", "confidence": 0.8},
        {"candidate_key": "huggingface_dataset:low-conf/x", "org_slug": "low-conf", "confidence": 0.5},
        {"candidate_key": "malformed", "org_slug": "x", "confidence": 0.9},
    ]
    pairs = graph_agreement_pairs(rows)
    assert pairs == {("openai", "openai")}


def test_graph_agrees_flag_set_when_pair_present():
    sources = _sources(
        products={"m": _product(["https://huggingface.co/openai/m"])},
        organizations={"openai": {"name": "openai", "products": ["m"]}},
    )
    report = build_report(sources, graph_pairs={("openai", "openai")})
    assert report["proposals"][0]["graph_agrees"] is True


def test_all_known_aggregators_are_excluded():
    products = {}
    orgs_products = []
    for i, ns in enumerate(sorted(KNOWN_AGGREGATORS)):
        slug = f"m{i}"
        products[slug] = _product([f"https://huggingface.co/{ns}/{slug}"])
        orgs_products.append(slug)
    sources = _sources(
        products=products,
        organizations={"o": {"name": "o", "products": orgs_products}},
    )
    report = build_report(sources)
    assert not report["proposals"]
    assert len(report["excluded"]) == len(KNOWN_AGGREGATORS)


def test_render_markdown_checklist_line_shape():
    sources = _sources(
        products={
            "acme-model": _product(["https://huggingface.co/acme-ai/acme-model"]),
        },
        organizations={"acme-ai": {"name": "acme-ai", "products": ["acme-model"]}},
    )
    report = build_report(sources)
    md = render_markdown(report)
    assert "- [ ] acme-ai ← huggingface `acme-ai` (1 artifacts: acme-model) name-agrees: yes" in md
    assert "```yaml" in md
    assert "- org: acme-ai" in md
    assert "  platform: huggingface" in md
    assert "  handle: acme-ai" in md


def test_render_markdown_yaml_block_validates_against_schema_and_has_no_dupe_owner():
    sources = _sources(
        products={
            "acme-model": _product(["https://huggingface.co/acme-ai/acme-model"]),
            "beta-model": _product(["https://huggingface.co/beta-labs/beta-model"]),
        },
        organizations={
            "acme-ai": {"name": "acme-ai", "products": ["acme-model"]},
            "beta-labs": {"name": "beta-labs", "products": ["beta-model"]},
        },
    )
    report = build_report(sources)
    md = render_markdown(report)
    block = md.split("```yaml\n", 1)[1].split("```", 1)[0]
    entries = yaml.safe_load(block)
    assert len(entries) == 2

    schema = json.loads((REPO / "docs" / "schemas" / "org_handles.schema.json").read_text())
    doc = {"version": 1, "handles": entries}
    jsonschema.validate(doc, schema)

    # Mirrors build/validate.py's uniqueness rule: one (platform, folded handle) -> one org.
    seen: dict[tuple[str, str], str] = {}
    for entry in entries:
        key = (entry["platform"], entry["handle"].casefold())
        assert key not in seen, f"duplicate handle owner: {key}"
        seen[key] = entry["org"]
        assert entry["org"] in {"acme-ai", "beta-labs"}


def test_render_markdown_none_sections_when_empty():
    md = render_markdown({"proposals": [], "conflicts": [], "excluded": []})
    assert md.count("None.") == 3
