"""The Hugging Face export publishes what the map publishes, and its card renders completely.

Real-corpus tests assert invariants, never a census: no row count here is typed in.
"""
import json
import re

import pytest

from build import export_hf
from build.serialize import ROOT, build_payload
from build.validate import load_sources
from build.vocabulary import axes


@pytest.fixture(scope="module")
def built():
    sources = load_sources(ROOT)
    frozen = json.load(open(ROOT / "sources" / "snapshots" / "long_tail.json"))
    payload = build_payload(sources, frozen, generated="2026-01-01")
    head = export_hf._git("rev-parse", "HEAD").strip()
    tables = (export_hf.current_tables(sources, payload)
              | export_hf.history_tables(payload, payload["version"], head))
    return sources, payload, tables, head


def test_products_are_the_published_rows(built):
    _, payload, tables, _ = built
    site = {r["slug"]: r for c in payload["categories"].values() for r in c["products"]}
    rows = tables["products"].to_pylist()
    assert len(rows) == payload["n_total"] == len(site)
    for r in rows:
        s = site[r["slug"]]
        assert (r["openness_score"], r["adoption_level"], r["capability_score"],
                r["overall_score"], r["overall_basis"], r["tier"], r["mature"]) == (
            s["openness"].get("score"), s["adoption"].get("level"), s["capability"].get("score"),
            s.get("overall_score"), s.get("overall_basis"), s.get("tier"), s.get("mature"))


def test_categories_carry_the_published_stage_and_gaps(built):
    _, payload, tables, _ = built
    for r in tables["categories"].to_pylist():
        cat = payload["categories"][r["slug"]]
        assert (r["stage_num"], r["gaps"], r["product_count"]) == (
            cat["stage"]["num"], cat["gaps"], len(cat["products"]))


def test_citations_are_every_source_of_every_published_product(built):
    sources, _, tables, _ = built
    published = set(tables["products"].column("slug").to_pylist())
    expected = sum(len((sources["scores"][s].get(ax) or {}).get("sources") or [])
                   for s in published for ax in axes())
    cites = tables["citations"]
    assert cites.num_rows == expected
    assert set(cites.column("product_slug").to_pylist()) <= published
    assert sum(tables["products"].column("citation_count").to_pylist()) == expected


def test_keys_join(built):
    _, _, t, _ = built
    orgs = set(t["organizations"].column("slug").to_pylist())
    cats = set(t["categories"].column("slug").to_pylist())
    slugs = t["products"].column("slug").to_pylist()
    assert len(slugs) == len(set(slugs))
    assert set(t["products"].column("organization_slug").to_pylist()) <= orgs
    assert set(t["products"].column("category_slug").to_pylist()) <= cats
    assert set(t["product_history"].column("current_slug").drop_null().to_pylist()) <= set(slugs)


def test_history_has_one_snapshot_per_release_tag_and_names_every_product(built):
    _, _, t, head = built
    tagged = [v for v, sha in export_hf.release_tags()
              if _has_payload(sha)]
    versions = list(dict.fromkeys(t["product_history"].column("version").to_pylist()))
    assert versions[:len(tagged)] == tagged
    assert t["product_history"].column("product_slug").null_count == 0
    # The live tree joins the series only as a labelled pre-release.
    assert all(v in tagged or v.endswith(f"+{head[:8]}") for v in versions)


def _has_payload(sha: str) -> bool:
    try:
        export_hf._git("cat-file", "-e", f"{sha}:build/notebook_data.json")
        return True
    except Exception:
        return False


@pytest.mark.parametrize("released_tag", [True, False])
def test_card_and_manifest_render_completely(built, tmp_path, released_tag):
    _, payload, tables, head = built
    manifest = export_hf.write(tmp_path, tables, payload, head, released_tag, "org/name")
    card = (tmp_path / "README.md").read_text()
    assert not re.search(r"\$\w", card), "unfilled template placeholder in the card"
    configs = re.findall(r"data_files: (\S+)", card)
    assert sorted(configs) == sorted(manifest["files"])
    for path in configs:
        assert (tmp_path / path).exists()
    assert manifest["release_tag"] == (f"v{payload['version']}" if released_tag else None)
    assert ("do not publish" in card) is not released_tag


def test_push_is_refused_off_the_release_tag(monkeypatch, tmp_path):
    monkeypatch.setattr(export_hf, "release_tags", lambda: [])
    monkeypatch.setattr(export_hf, "push", lambda *a: pytest.fail("push must not be reached"))
    monkeypatch.setattr("sys.argv", ["export_hf", "--push", "--out", str(tmp_path)])
    with pytest.raises(SystemExit, match="refusing to push"):
        export_hf.main()
