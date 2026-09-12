import json
from datetime import date
from pathlib import Path

import pytest
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


def test_apply_carries_the_fetched_http_status_for_a_byte_identical_source(tmp_path):
    # A byte-identical re-fetch is still a real fetch, and its response is not always a
    # bare 200 (a conditional GET can come back 304). `apply` used to hardcode 200 for
    # every reconfirmed source regardless of what was actually returned.
    root = _score_with_sources(tmp_path, [_src("https://a/LICENSE", "a" * 64, ["license"])], dims=("license",))
    fake = lambda url, **kw: {"url": url, "http_status": 304, "content_sha256": "a" * 64}  # noqa: E731
    result = reverify.reverify_product(root, "p", date(2026, 9, 3), axes=("openness",), fetch=fake)
    reverify.apply(root, "p", result, date(2026, 9, 3))
    src = yaml.safe_load((root / "sources/scores/p.yaml").read_text())["openness"]["sources"][0]
    assert src["http_status"] == 304


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


# --- #527: one URL cited twice must not collapse into one confirmation ------------------

def test_both_entries_citing_one_url_are_re_dated(tmp_path):
    """The compar-ia shape. Two digested entries cite the same README for different
    dimensions; `confirmed` was keyed by URL, so they collapsed into one record and `apply`
    wrote it to whichever came first. The entry establishing `source` kept its old date and
    the axis was stamped anyway."""
    root = _score_with_sources(tmp_path, [
        _src("https://a/LICENSE", "a" * 64, ["license"]),
        _src("https://a/README", "b" * 64, ["core-gated"]),
        _src("https://a/README", "b" * 64, ["source", "core-gated"]),
    ], dims=("license", "source", "core-gated"),
        recipe={"openness": {"dimensions": {"source": {"reads": ["source"]},
                                            "core-gated": {"reads": ["core-gated"]}}}})
    fake = lambda url, **kw: {"url": url, "http_status": 200,  # noqa: E731
                              "content_sha256": "a" * 64 if url.endswith("LICENSE") else "b" * 64}
    result = reverify.reverify_product(root, "p", date(2026, 9, 9), axes=("openness",), fetch=fake)
    assert result.stamped == ["openness"]
    reverify.apply(root, "p", result, date(2026, 9, 9))

    entries = yaml.safe_load((root / "sources/scores/p.yaml").read_text())["openness"]["sources"]
    assert [e["accessed"] for e in entries] == ["2026-09-09"] * 3, (
        "every confirmed entry takes the new date, including both citations of one URL")


def test_a_stamped_axis_satisfies_the_invariant_gate(tmp_path):
    """The end-to-end form of the same bug: whatever `reverify` stamps, the gate that runs
    straight after it in the workflow must accept. This is the assertion the 2026-09-08
    scheduled run failed."""
    from build.check_verification import invariant

    root = _score_with_sources(tmp_path, [
        _src("https://a/LICENSE", "a" * 64, ["license"]),
        _src("https://a/README", "b" * 64, ["core-gated"]),
        _src("https://a/README", "b" * 64, ["source", "core-gated"]),
    ], dims=("license", "source", "core-gated"),
        recipe={"openness": {"dimensions": {"source": {"reads": ["source"]},
                                            "core-gated": {"reads": ["core-gated"]}}}})
    fake = lambda url, **kw: {"url": url, "http_status": 200,  # noqa: E731
                              "content_sha256": "a" * 64 if url.endswith("LICENSE") else "b" * 64}
    result = reverify.reverify_product(root, "p", date(2026, 9, 9), axes=("openness",), fetch=fake)
    # Without this the test would also pass by stamping nothing at all.
    assert result.stamped == ["openness"]
    reverify.apply(root, "p", result, date(2026, 9, 9))

    owner, recipes, product_types = reverify._recipe_context(str(root))
    scores = {"p": yaml.safe_load((root / "sources/scores/p.yaml").read_text())}
    categories = {p.stem: yaml.safe_load(p.read_text())
                  for p in sorted((root / "sources/categories").glob("*.yaml"))}
    problems = invariant(scores, categories, recipes, product_types)
    # `_corpus` gives adoption and capability a date and no sources at all, which the
    # invariant rightly objects to; this test is about the axis reverify actually wrote.
    assert [p for p in problems if ":openness:" in p] == []


def test_apply_refuses_a_confirmation_whose_citation_changed_underneath_it(tmp_path):
    """The ordinal is only safe while the file it was computed against still says the same
    thing. `apply` used to recover the URL from a fresh parse at the same position, so its
    index/url agreement check compared that parse against itself and could never fire — a
    confirmation fetched for one page would be stamped onto whatever now occupies the slot,
    carrying the wrong digest with it."""
    root = _score_with_sources(tmp_path, [
        _src("https://a/LICENSE", "a" * 64, ["license"]),
        _src("https://a/OLD", "b" * 64, ["source"]),
    ], recipe=_SOURCE_RECIPE)
    fake = lambda url, **kw: {"url": url, "http_status": 200,  # noqa: E731
                              "content_sha256": "a" * 64 if url.endswith("LICENSE") else "b" * 64}
    result = reverify.reverify_product(root, "p", date(2026, 9, 9), axes=("openness",), fetch=fake)
    assert result.stamped == ["openness"]

    # The citation at the confirmed position is replaced before the write lands.
    path = root / "sources/scores/p.yaml"
    data = yaml.safe_load(path.read_text())
    data["openness"]["sources"][1]["url"] = "https://a/NEW"
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=100))

    before = path.read_text()
    with pytest.raises(ValueError, match="cites"):
        reverify.apply(root, "p", result, date(2026, 9, 9))
    # The refusal comes before the single write_text, and an earlier entry in the same
    # loop was already edited in memory, so the whole file has to be byte-identical —
    # not merely unstamped.
    assert path.read_text() == before


# --- The quoted fragments inside a `shows`, not the whole curator's sentence -----------
#
# `shows` is written as a sentence ABOUT the page with the verbatim material quoted inside
# it, so the whole-sentence test tests the curator's prose. Measured 2026-09-12 over the 25
# oldest products: 72 sources drifted, 0 skipped, 0 placeholder, whole-sentence confirmed 4.


_ATROPOS_SHOWS = (
    'Repo page carries the label "Public archive" and the banner "This repository was '
    'archived by the owner on Jul 4, 2026. It is now read-only." The rendered README says '
    '"Atropos is an environment microservice framework for async RL with LLMs." and its '
    'Navigating the Repo table lists "Core library containing base classes and utilities" '
    'and "Collection of ready-to-use RL environments"; installation is '
    '"pip install atroposlib".'
)


def _shows_case(tmp_path, shows, body_text, name="page.html"):
    # A fresh corpus root per call, so one test can run two cases over one tmp_path.
    root_dir = tmp_path / f"case-{name}"
    root_dir.mkdir()
    body_path = _body(root_dir, name, body_text)
    root = _score_with_sources(root_dir, [_src("https://a/LICENSE", "a" * 64, ["license"],
                                                shows=shows)], dims=("license",))
    fake = lambda url, **kw: {"url": url, "http_status": 200, "content_sha256": "b" * 64,  # noqa: E731
                              "body_path": str(body_path)}
    return reverify.reverify_product(root, "p", date(2026, 9, 12), axes=("openness",), fetch=fake)


def test_every_quoted_fragment_present_confirms_a_sentence_that_never_occurs(tmp_path):
    """The shape this change exists for: the curator's sentence is nowhere on the page, and
    every piece of verbatim material quoted inside it is."""
    body = (
        "<h1>NousResearch/atropos</h1><span>Public archive</span>"
        "<div>This repository was archived by the owner on Jul 4, 2026. It is now read-only.</div>"
        "<p>Atropos is an environment microservice framework for async RL with LLMs.</p>"
        "<td>Core library containing base classes and utilities</td>"
        "<td>Collection of ready-to-use RL environments</td>"
        "<code>pip install atroposlib</code>"
    )
    result = _shows_case(tmp_path, _ATROPOS_SHOWS, body)
    assert result.stamped == ["openness"]
    assert result.reconfirmed_by_shows == [("openness", "https://a/LICENSE")]
    assert result.drifted == []


def test_a_partial_fragment_match_still_drifts(tmp_path):
    """The atropos shape that must NOT confirm. Two of the quoted fragments are on the page
    and the rest are gone; "at least one matched" is exactly the rubber stamp this leg
    exists to refuse."""
    body = (
        "<h1>NousResearch/atropos</h1><span>Public archive</span>"
        "<p>Atropos is an environment microservice framework for async RL with LLMs.</p>"
        "<p>The README has been rewritten and the tables are gone.</p>"
    )
    result = _shows_case(tmp_path, _ATROPOS_SHOWS, body)
    assert result.stamped == []
    assert result.drifted == [("openness", "https://a/LICENSE")]


def test_a_shows_that_quotes_nothing_is_unchanged(tmp_path):
    """No quoted fragment means no fragment path, so the whole-sentence test is the only
    one available. Saying less must not make a source easier to confirm."""
    absent = _shows_case(
        tmp_path, "the repo page still describes an archived public MIT project",
        "<p>An archived public MIT project, described in quite different words.</p>")
    assert absent.stamped == []
    assert absent.drifted == [("openness", "https://a/LICENSE")]

    present = _shows_case(
        tmp_path, "the repo page still describes an archived public MIT project",
        "<p>Preamble. the repo page still describes an archived public MIT project.</p>",
        name="present.html")
    assert present.stamped == ["openness"]
    assert present.reconfirmed_by_shows == [("openness", "https://a/LICENSE")]


def test_a_placeholder_shows_never_confirms_on_fragments_either(tmp_path):
    marker = next(iter(PLACEHOLDER_SHOWS))
    shows = f'{marker}: the page carries "Licensed under the Apache License, Version 2.0".'
    body = f"<p>{marker}</p><p>Licensed under the Apache License, Version 2.0</p>"
    result = _shows_case(tmp_path, shows, body)
    assert result.stamped == []
    assert result.drifted == [("openness", "https://a/LICENSE")]


def test_fragments_below_the_length_floor_do_not_earn_a_date(tmp_path):
    """A `shows` whose only quoted material is a JSON key and a license id would otherwise
    confirm against any GitHub API response ever served."""
    shows = 'Repository JSON reads "license": "MIT" and "private": false.'
    body = '{"license": "MIT", "private": false, "name": "something else entirely"}'
    assert all(len(f) < reverify.MIN_FRAGMENT_CHARS
               for f in reverify._shows_fragments(shows)), "the fixture must stay short"
    result = _shows_case(tmp_path, shows, body)
    assert result.stamped == []
    assert result.drifted == [("openness", "https://a/LICENSE")]


def test_the_atropos_api_citation_does_not_confirm_on_json_key_names(tmp_path):
    """The measured counter-example, and the reason `atropos` still drifts on 2026-09-12.

    Every fragment quoted inside this `shows` does occur in the fresh response — they are
    the keys and values of a GitHub repository payload, and they occur in every such
    payload ever served. None of them reaches the length floor, so there is nothing here
    that could earn a date, and the axis is left alone."""
    shows = ('Repository JSON: "private": false, "visibility": "public", "archived": true, '
             '"disabled": false, "spdx_id": "MIT", "pushed_at": "2026-07-04T17:39:01Z", '
             '"open_issues_count": 0, default_branch main, created 2025-04-29.')
    body = ('{"private": false, "visibility": "public", "archived": true, "disabled": false, '
            '"spdx_id": "MIT", "pushed_at": "2026-07-04T17:39:01Z", "open_issues_count": 0}')
    fragments = reverify._shows_fragments(shows)
    assert len(fragments) == 10 and all(f in " ".join(body.split()) for f in fragments), (
        "every fragment is on the page; the floor is the only thing refusing this")
    assert max(len(f) for f in fragments) < reverify.MIN_FRAGMENT_CHARS
    result = _shows_case(tmp_path, shows, body)
    assert result.stamped == []
    assert result.drifted == [("openness", "https://a/LICENSE")]


def test_a_short_fragment_still_has_to_be_present(tmp_path):
    """Too short to earn the date is not the same as ignored. The long fragment is on the
    page; the short one it is quoted beside is not."""
    shows = ('The model card says "Released under the Apache 2.0 License." '
             'and the header reads "MIT".')
    body = "<p>Released under the Apache 2.0 License.</p>"
    result = _shows_case(tmp_path, shows, body)
    assert result.stamped == []
    assert result.drifted == [("openness", "https://a/LICENSE")]


def test_curly_quotes_delimit_a_fragment(tmp_path):
    shows = "The pricing page says “Comes bundled with your subscription” today."
    body = "<li>Comes bundled with your subscription</li>"
    assert reverify._shows_fragments(shows) == ["Comes bundled with your subscription"]
    result = _shows_case(tmp_path, shows, body)
    assert result.stamped == ["openness"]
    assert result.reconfirmed_by_shows == [("openness", "https://a/LICENSE")]


def test_a_regex_metacharacter_in_a_fragment_is_matched_literally(tmp_path):
    """`.*` and the brackets are text. Compiled as a pattern the fragment would match
    almost anything; as a substring it matches only itself."""
    shows = ('The pyproject line reads '
             '"license = {text = \'MIT\'}  # (.*|[a-z]+) is not a pattern here" verbatim.')
    assert reverify._shows_fragments(shows) == [
        "license = {text = 'MIT'} # (.*|[a-z]+) is not a pattern here"]
    hit = _shows_case(
        tmp_path, shows,
        "<pre>license = {text = 'MIT'}  # (.*|[a-z]+) is not a pattern here</pre>")
    assert hit.stamped == ["openness"]
    miss = _shows_case(tmp_path, shows,
                       "<pre>anything at all, which a compiled pattern would match</pre>",
                       name="miss.html")
    assert miss.stamped == []
    assert miss.drifted == [("openness", "https://a/LICENSE")]


def test_an_unbalanced_trailing_quote_opens_no_fragment(tmp_path):
    shows = ('The README still opens "A composable training library for large models" '
             'and the banner reads "Archived')
    assert reverify._shows_fragments(shows) == [
        "A composable training library for large models"]
    result = _shows_case(
        tmp_path, shows, "<p>A composable training library for large models</p>")
    assert result.stamped == ["openness"]


def test_a_url_inside_a_fragment_is_just_text(tmp_path):
    shows = ('The notice points at "https://example.org/license?v=2&t=1 (see terms)" '
             'for the full text.')
    assert reverify._shows_fragments(shows) == [
        "https://example.org/license?v=2&t=1 (see terms)"]
    result = _shows_case(
        tmp_path, shows,
        "<a>https://example.org/license?v=2&amp;t=1 (see terms)</a>")
    assert result.stamped == ["openness"], "the body is unescaped before matching"


def test_fragments_are_matched_after_the_same_whitespace_collapse(tmp_path):
    shows = 'The page carries "Deploy leading open source tools and AI models with confidence".'
    body = ("<p>Deploy leading open source\n   tools and AI models\twith confidence</p>")
    result = _shows_case(tmp_path, shows, body)
    assert result.stamped == ["openness"]
