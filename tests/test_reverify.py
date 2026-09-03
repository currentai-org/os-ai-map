from datetime import date
from pathlib import Path

import yaml

from build import reverify


def _corpus(tmp_path: Path, dates: dict[str, tuple[str, str, str]]) -> Path:
    (tmp_path / "sources" / "scores").mkdir(parents=True)
    (tmp_path / "sources" / "categories").mkdir()
    (tmp_path / "sources" / "categories" / "cat.yaml").write_text(
        yaml.safe_dump({"name": "cat", "display_name": "Cat", "products": sorted(dates)}))
    (tmp_path / "sources" / "taxonomy.yaml").write_text(
        yaml.safe_dump({"categories": [{"name": "cat", "status": "published"}]}))
    for slug, (o, a, c) in dates.items():
        (tmp_path / "sources" / "scores" / f"{slug}.yaml").write_text(yaml.safe_dump({
            "product": slug,
            "openness": {"score": 5, "class": "open_source", "last_verified": o, "sources": []},
            "adoption": {"level": 3, "last_verified": a, "sources": []},
            "capability": {"score": 3, "basis": "feature_matrix", "last_verified": c, "sources": []},
        }))
    return tmp_path


def test_oldest_products_ranks_by_min_axis_then_slug(tmp_path):
    root = _corpus(tmp_path, {
        "zeta": ("2026-08-13", "2026-08-20", "2026-08-20"),
        "alpha": ("2026-08-13", "2026-08-13", "2026-08-13"),
        "newer": ("2026-08-30", "2026-08-30", "2026-08-30"),
    })
    ranked = reverify.oldest_products(root, limit=2)
    assert ranked == [(date(2026, 8, 13), "alpha"), (date(2026, 8, 13), "zeta")]


def _score_with_sources(tmp_path, sources, dims=("license", "source")):
    root = _corpus(tmp_path, {"p": ("2026-08-13", "2026-08-13", "2026-08-13")})
    path = root / "sources" / "scores" / "p.yaml"
    data = yaml.safe_load(path.read_text())
    data["openness"]["components"] = {d: "x" for d in dims}
    # `sources:` is the last field of an axis block throughout the corpus (see
    # sources/scores/accelerate.yaml); drop and re-add it after `components` so this
    # fixture matches that convention instead of leaving `sources` ahead of `components`.
    data["openness"].pop("sources", None)
    data["openness"]["sources"] = sources
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=100))
    return root


def _src(url, digest, establishes):
    return {"url": url, "shows": "the license text", "accessed": "2026-08-13",
            "http_status": 200, "content_sha256": digest, "establishes": establishes}


def test_stamps_when_every_dimension_reconfirms(tmp_path):
    root = _score_with_sources(tmp_path, [
        _src("https://a/LICENSE", "a" * 64, ["license"]),
        _src("https://a/README", "b" * 64, ["source"]),
    ])
    fake = lambda url, **kw: {"url": url, "http_status": 200,  # noqa: E731
                              "content_sha256": "a" * 64 if url.endswith("LICENSE") else "b" * 64}
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == ["openness"]
    assert result.drifted == [] and result.transient == []


def test_drift_on_one_source_leaves_the_axis_alone(tmp_path):
    root = _score_with_sources(tmp_path, [
        _src("https://a/LICENSE", "a" * 64, ["license"]),
        _src("https://a/README", "b" * 64, ["source"]),
    ])
    fake = lambda url, **kw: {"url": url, "http_status": 200,  # noqa: E731
                              "content_sha256": "a" * 64 if url.endswith("LICENSE") else "c" * 64}
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == []
    assert result.drifted == [("openness", "https://a/README")]


def test_transient_is_not_evidence(tmp_path):
    root = _score_with_sources(tmp_path, [_src("https://a/LICENSE", "a" * 64, ["license"])], dims=("license",))
    fake = lambda url, **kw: {"url": url, "http_status": 429, "transient": True}  # noqa: E731
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == [] and result.transient == [("openness", "https://a/LICENSE")]


def test_dimension_without_digested_source_is_skipped(tmp_path):
    root = _score_with_sources(tmp_path, [_src("https://a/LICENSE", "a" * 64, ["license"])],
                               dims=("license", "core-gated"))
    fake = lambda url, **kw: {"url": url, "http_status": 200, "content_sha256": "a" * 64}  # noqa: E731
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == []
    assert ("openness", "core-gated has no digested establishing source") in result.skipped


def test_apply_writes_accessed_status_and_last_verified_only(tmp_path):
    root = _score_with_sources(tmp_path, [_src("https://a/LICENSE", "a" * 64, ["license"])], dims=("license",))
    fake = lambda url, **kw: {"url": url, "http_status": 200, "content_sha256": "a" * 64}  # noqa: E731
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    before = (root / "sources/scores/p.yaml").read_text()
    reverify.apply(root, "p", result, date(2026, 9, 3))
    after = yaml.safe_load((root / "sources/scores/p.yaml").read_text())
    assert after["openness"]["last_verified"] == "2026-09-03"
    assert after["openness"]["sources"][0]["accessed"] == "2026-09-03"
    assert after["openness"]["sources"][0]["content_sha256"] == "a" * 64
    assert after["adoption"]["last_verified"] == "2026-08-13"
    # Only the intended lines moved.
    changed = [l for l in (root / "sources/scores/p.yaml").read_text().splitlines()
               if l not in before.splitlines()]
    assert all("2026-09-03" in l for l in changed), changed
