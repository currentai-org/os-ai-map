import json
from datetime import date
from pathlib import Path

import yaml

from build import reverify
from build.check_verification import PLACEHOLDER_SHOWS


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


# Minimal recipes so a dimension other than `license` (which is always required by
# default — see `build.check_rubric.license_read_keys`) is required too, matching what
# `build.check_verification.recorded_dimensions` reads off a category's own recipe.
_SOURCE_RECIPE = {"openness": {"dimensions": {"source": {"reads": ["source"]}}}}
_CORE_GATED_RECIPE = {"openness": {"dimensions": {"core-gated": {"reads": ["core-gated"]}}}}


def _score_with_sources(tmp_path, sources, dims=("license", "source"), recipe=None):
    root = _corpus(tmp_path, {"p": ("2026-08-13", "2026-08-13", "2026-08-13")})
    if recipe is not None:
        cat_path = root / "sources" / "categories" / "cat.yaml"
        cat = yaml.safe_load(cat_path.read_text())
        cat["scoring_recipe"] = recipe
        cat_path.write_text(yaml.safe_dump(cat))
    path = root / "sources" / "scores" / "p.yaml"
    data = yaml.safe_load(path.read_text())
    # Structured shape (`{value: ...}`), matching the real corpus — see
    # sources/scores/accelerate.yaml — so `build.check_rubric.components_of` can read it.
    data["openness"]["components"] = {d: {"value": "x"} for d in dims}
    # `sources:` is the last field of an axis block throughout the corpus (see
    # sources/scores/accelerate.yaml); drop and re-add it after `components` so this
    # fixture matches that convention instead of leaving `sources` ahead of `components`.
    data["openness"].pop("sources", None)
    data["openness"]["sources"] = sources
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=100))
    return root


def _src(url, digest, establishes, shows="the license text"):
    return {"url": url, "shows": shows, "accessed": "2026-08-13",
            "http_status": 200, "content_sha256": digest, "establishes": establishes}


def test_stamps_when_every_dimension_reconfirms(tmp_path):
    root = _score_with_sources(tmp_path, [
        _src("https://a/LICENSE", "a" * 64, ["license"]),
        _src("https://a/README", "b" * 64, ["source"]),
    ], recipe=_SOURCE_RECIPE)
    fake = lambda url, **kw: {"url": url, "http_status": 200,  # noqa: E731
                              "content_sha256": "a" * 64 if url.endswith("LICENSE") else "b" * 64}
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == ["openness"]
    assert result.drifted == [] and result.transient == []


def test_drift_on_one_source_leaves_the_axis_alone(tmp_path):
    root = _score_with_sources(tmp_path, [
        _src("https://a/LICENSE", "a" * 64, ["license"]),
        _src("https://a/README", "b" * 64, ["source"]),
    ], recipe=_SOURCE_RECIPE)
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
                               dims=("license", "core-gated"), recipe=_CORE_GATED_RECIPE)
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


# --- Step 1: the dimension set is the gate's, not every `components` key ---------------


def test_free_text_is_not_a_required_dimension(tmp_path):
    root = _score_with_sources(tmp_path, [_src("https://a/LICENSE", "a" * 64, ["license"])],
                               dims=("license", "free_text"))
    fake = lambda url, **kw: {"url": url, "http_status": 200, "content_sha256": "a" * 64}  # noqa: E731
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == ["openness"]
    assert result.skipped == []


# --- Step 2: a `shows` match is a second confirmation path -----------------------------


def _body(tmp_path, name, text):
    body_dir = tmp_path / "bodies"
    body_dir.mkdir(exist_ok=True)
    path = body_dir / name
    path.write_text(text)
    return path


def test_shows_present_in_changed_body_confirms(tmp_path):
    body_path = _body(tmp_path, "license.html",
                      "<p>Some preamble.</p><p>the license text, now reflowed as HTML.</p>")
    root = _score_with_sources(tmp_path, [_src("https://a/LICENSE", "a" * 64, ["license"],
                                                shows="the license text")], dims=("license",))
    fake = lambda url, **kw: {"url": url, "http_status": 200, "content_sha256": "b" * 64,  # noqa: E731
                              "body_path": str(body_path)}
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == ["openness"]
    assert result.reconfirmed_by_shows == [("openness", "https://a/LICENSE")]
    assert result.drifted == []


def test_shows_absent_from_changed_body_is_drift(tmp_path):
    body_path = _body(tmp_path, "license.html", "<p>Completely different content now.</p>")
    root = _score_with_sources(tmp_path, [_src("https://a/LICENSE", "a" * 64, ["license"],
                                                shows="the license text")], dims=("license",))
    fake = lambda url, **kw: {"url": url, "http_status": 200, "content_sha256": "b" * 64,  # noqa: E731
                              "body_path": str(body_path)}
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == []
    assert result.drifted == [("openness", "https://a/LICENSE")]


def test_placeholder_shows_never_confirms(tmp_path):
    marker = next(iter(PLACEHOLDER_SHOWS))
    body_path = _body(tmp_path, "license.html", f"<p>{marker} plus the rest of the page.</p>")
    root = _score_with_sources(tmp_path, [_src("https://a/LICENSE", "a" * 64, ["license"],
                                                shows=marker)], dims=("license",))
    fake = lambda url, **kw: {"url": url, "http_status": 200, "content_sha256": "b" * 64,  # noqa: E731
                              "body_path": str(body_path)}
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == []
    assert result.drifted == [("openness", "https://a/LICENSE")]


def test_apply_writes_the_fetched_http_status_and_new_digest_for_a_shows_confirmed_source(tmp_path):
    body_path = _body(tmp_path, "license.html", "<p>the license text, reflowed.</p>")
    root = _score_with_sources(tmp_path, [_src("https://a/LICENSE", "a" * 64, ["license"],
                                                shows="the license text")], dims=("license",))
    fake = lambda url, **kw: {"url": url, "http_status": 304, "content_sha256": "b" * 64,  # noqa: E731
                              "body_path": str(body_path)}
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    reverify.apply(root, "p", result, date(2026, 9, 3))
    src = yaml.safe_load((root / "sources/scores/p.yaml").read_text())["openness"]["sources"][0]
    assert src["http_status"] == 304
    assert src["content_sha256"] == "b" * 64


# --- Step 3: SPDX comparison for license API sources ------------------------------------


def _score_with_license(tmp_path, license_value, sources):
    root = _corpus(tmp_path, {"p": ("2026-08-13", "2026-08-13", "2026-08-13")})
    path = root / "sources" / "scores" / "p.yaml"
    data = yaml.safe_load(path.read_text())
    data["openness"]["components"] = {"license": {"value": license_value}}
    data["openness"].pop("sources", None)
    data["openness"]["sources"] = sources
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=100))
    return root


def test_matching_spdx_confirms_license(tmp_path):
    body_path = _body(tmp_path, "license.json", json.dumps({"license": {"spdx_id": "Apache-2.0"}}))
    root = _score_with_license(tmp_path, "Apache-2.0", [
        _src("https://api.github.com/repos/o/r/license", "a" * 64, ["license"]),
    ])
    fake = lambda url, **kw: {"url": url, "http_status": 200, "content_sha256": "b" * 64,  # noqa: E731
                              "body_path": str(body_path)}
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == ["openness"]
    assert result.reconfirmed_by_spdx == [("openness", "https://api.github.com/repos/o/r/license")]


def test_noassertion_spdx_does_not_confirm(tmp_path):
    body_path = _body(tmp_path, "license.json", json.dumps({"license": {"spdx_id": "NOASSERTION"}}))
    root = _score_with_license(tmp_path, "Apache-2.0", [
        _src("https://api.github.com/repos/o/r/license", "a" * 64, ["license"]),
    ])
    fake = lambda url, **kw: {"url": url, "http_status": 200, "content_sha256": "b" * 64,  # noqa: E731
                              "body_path": str(body_path)}
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    assert result.stamped == []
    assert result.drifted == [("openness", "https://api.github.com/repos/o/r/license")]
