import pytest

from build.serialize import (build_payload, release_date, repo_version,
                             _stage_and_gaps)


def _p(cls, adoption, capability):
    return {"openness": {"class": cls}, "adoption": {"level": adoption},
            "capability": {"score": capability}}


def test_stage5_mature_open_ecosystem():
    rows = [_p("open_source", 5, 5) for _ in range(4)]  # 4 mature fully-open
    sg = _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] == 5 and sg["gaps"] == []


def test_openness_gap_when_mature_options_are_open_ish():
    rows = [_p("open_weights", 5, 5) for _ in range(3)]  # mature but open-ish, none fully open
    sg = _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] < 5 and "openness" in sg["gaps"]


def test_maturity_is_not_a_gap_type():
    # The composite was dropped from the vocabulary: it reported the blend next to its own
    # parts, and it fired in 12 of 16 categories, so it discriminated between none of them.
    for rows, w in (([_p("open_source", 5, 5)], {"adopt": 0.5, "cap": 0.5}),      # stage 4
                    ([_p("open_weights", 5, 5)], {"adopt": 0.5, "cap": 0.5}),     # stage 1-3
                    ([_p("open_source", 2, 2)], {"adopt": 0.5, "cap": 0.5})):     # stage 1-3
        assert "maturity" not in _stage_and_gaps(rows, w)["gaps"]


def test_depth_gap_at_stage_4_only():
    # One mature fully-open product: quality is proven, count is not.
    sg = _stage_and_gaps([_p("open_source", 5, 5)], {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] == 4 and sg["gaps"] == ["depth"]
    # Four of them clears Stage 5, which carries no gaps at all.
    sg5 = _stage_and_gaps([_p("open_source", 5, 5) for _ in range(4)], {"adopt": 0.5, "cap": 0.5})
    assert sg5["num"] == 5 and "depth" not in sg5["gaps"]
    # Below Stage 4 the stage number already says no frontier open option exists, so depth
    # would only restate it — this is the ubiquity the old maturity gap had.
    for rows in ([_p("open_source", 2, 2)], [_p("open_weights", 5, 5)], [_p("closed", 1, 1)]):
        assert "depth" not in _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})["gaps"]


def test_capability_and_adoption_both_fire_when_both_apply():
    # No one-diagnostic-per-category rule any more: a fully-open option that is weak on both
    # axes reports both drivers.
    sg = _stage_and_gaps([_p("open_source", 3, 3)], {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] < 4 and sg["gaps"] == ["capability", "adoption"]


def test_capability_gap_survives_alongside_openness():
    # The edge_hardware case. The single fully-open board is adopted but underpowered, while
    # mature open-ish and closed options exist. The old engine emitted one diagnostic and
    # checked openness first, so `capability` was unreachable and this never surfaced.
    rows = [_p("open_hardware", 4, 3), _p("open_weights", 5, 5), _p("closed", 5, 5)]
    sg = _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})
    assert "capability" in sg["gaps"] and "openness" in sg["gaps"]
    assert "adoption" not in sg["gaps"]  # adoption 4 clears its bar


def test_missing_adoption_yields_null_maturity_and_is_excluded_from_stage():
    # A product with null adoption has no maturity score (not 0.0) and must not drag
    # the category's stage down — here a mature open product should still reach stage 4.
    rows = [_p("open_source", 5, 5), _p("open_source", None, None)]
    sg = _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] == 4  # the null-adoption product is ignored, the mature one stands


def test_void_when_no_open_option():
    sg = _stage_and_gaps([_p("closed", 1, 1)], {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] == 0 and sg["gaps"] == ["void"]


def test_capability_gap_when_nothing_mature_and_weak():
    rows = [_p("open_source", 2, 2)]  # fully open but weak on both axes
    sg = _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})
    assert "capability" in sg["gaps"]


def test_stage_1_to_3_carries_no_driver_gap_when_axes_clear_but_blend_misses_bar():
    # benchmark_eval_data's shape: fully-open products at adoption 4 with a null capability,
    # so the blend is adoption alone and tops out at 4.0 — under the maturity bar, yet neither
    # axis is below its cutoff. Adoption is NOT short (it clears 4), and capability is unmeasured,
    # not deficient — so no driver gap fires. Labelling this `adoption` would be a knowingly
    # false shortfall; the stage number already says the category is below the leading bar.
    rows = [_p("open_source", 4, None) for _ in range(3)]
    sg = _stage_and_gaps(rows, {"adopt": 0.6, "cap": 0.4})
    assert sg["num"] == 3 and sg["gaps"] == []


def test_stage_uses_rounded_maturity_not_float_noise():
    # 0.3*3 + 0.7*3 = 2.9999999999999996 as a float. Rounded to 2dp it is 3.00, which
    # sits at the Stage 2 boundary (best fully-open >= 3.0), not Stage 1. The stage must
    # compare the rounded value so float epsilon can't decide the rung.
    rows = [_p("open_source", 3, 3)]
    sg = _stage_and_gaps(rows, {"adopt": 0.3, "cap": 0.7})
    assert sg["num"] == 2


def _sources():
    return {
        "organizations": {"meta": {"name": "meta", "display_name": "Meta",
                                   "type": "unknown", "products": ["llama-4"]}},
        "taxonomy": {"arcs": [{"name": "Model components", "layer": "model_components",
                               "categories": ["base_pretrained"]}]},
        "categories": {
            "base_pretrained": {"name": "base_pretrained",
                                "display_name": "Base / pretrained models",
                                "products": ["llama-4"], "comments": ""}
        },
        "products": {"llama-4": {"name": "llama-4", "display_name": "Llama 4",
                                 "type": "model", "description": "desc",
                                 "comments": "note text"}},
        "scores": {"llama-4": {"product": "llama-4",
                               "openness": {"score": 2, "class": "restricted"},
                               "adoption": {"level": 4, "signal_type": "usage_volume"},
                               "capability": {"score": None, "basis": "n/a"}}},
    }


def test_build_payload_shape_and_order():
    payload = build_payload(_sources(), frozen_long_tail={"counts": {}, "top": []},
                            generated="2026-06-10")
    assert payload["order"] == ["base_pretrained"]
    assert payload["n_total"] == 1
    assert payload["generated"] == "2026-06-10"
    cat = payload["categories"]["base_pretrained"]
    assert cat["label"] == "Base / pretrained models"
    assert cat["arc"] == "Model components"
    assert cat["layer"] == "model_components"
    row = cat["products"][0]
    assert row["product"] == "Llama 4"
    assert row["org"] == "Meta"
    # comments field is carried under the legacy payload key version_note
    assert row["version_note"] == "note text"
    # llama-4 has no capability score, so maturity falls back to adoption (4) alone
    assert row["maturity"] == 4.0


def test_layer_order_present_and_in_arc_sequence():
    # layer_order lists the Columbia layers in taxonomy arc order; the fixture
    # has a single Model components arc, so it is just that layer.
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-06-10")
    assert payload["layer_order"] == ["model_components"]
    # it ships right after descriptions so consumers can read the stack order up top
    assert list(payload)[:2] == ["descriptions", "layer_order"]


def test_preliminary_categories_are_excluded_from_the_public_payload():
    src = _sources()
    src["categories"]["storage"] = {
        "name": "storage",
        "display_name": "Storage",
        "products": [],
    }
    src["taxonomy"]["arcs"][0]["categories"].append(
        {"name": "storage", "status": "preliminary"}
    )
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["order"] == ["base_pretrained"]
    assert "storage" not in payload["categories"]
    assert "storage" not in payload["descriptions"]["categories"]


def test_null_adoption_serializes_maturity_null():
    src = _sources()
    src["scores"]["llama-4"]["adoption"] = {"level": None, "signal_type": "unknown"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["maturity"] is None


def test_maturity_is_weighted_blend_rounded_2dp():
    # adoption 4, capability 5 with default 0.5/0.5 weights -> 4.5; cap-heavy 0.25/0.75 -> 4.75
    src = _sources()
    src["scores"]["llama-4"]["capability"] = {"score": 5, "basis": "x"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["maturity"] == 4.5

    src["categories"]["base_pretrained"]["weights"] = {"adopt": 0.25, "cap": 0.75}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["maturity"] == 4.75


def test_long_tail_drops_now_categorized_products():
    # llama-4 carries github.com/meta-llama/llama; a frozen long-tail sample row for
    # that same repo must be filtered out (it is no longer uncategorized), while an
    # unrelated row survives.
    src = _sources()
    src["products"]["llama-4"]["github"] = [{"url": "https://github.com/meta-llama/llama"}]
    frozen = {"counts": {}, "top": [
        {"name": "meta-llama/llama", "type": "repo", "usage_label": "", "description": ""},
        {"name": "someone/uncategorized", "type": "repo", "usage_label": "", "description": ""},
    ]}
    payload = build_payload(src, frozen_long_tail=frozen, generated="2026-06-10")
    names = [t["name"] for t in payload["long_tail"]["top"]]
    assert "meta-llama/llama" not in names
    assert "someone/uncategorized" in names


def test_descriptions_block_present_and_sourced():
    src = _sources()
    src["categories"]["base_pretrained"]["description"] = "Foundation models trained from scratch."
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    d = payload["descriptions"]
    # stages keyed 0-5, gaps keyed by name, categories keyed by slug from the source yaml
    assert set(d["stages"]) == {"0", "1", "2", "3", "4", "5"}
    assert "void" in d["gaps"] and "openness" in d["gaps"]
    assert "depth" in d["gaps"] and "maturity" not in d["gaps"]
    # the two score tiers ship their own legend copy, so a consumer never hardcodes 4.5/4.0
    assert set(d["tiers"]) == {"leading", "strong"}
    assert d["categories"]["base_pretrained"] == "Foundation models trained from scratch."
    # descriptions ships first so it reads as a header
    assert list(payload)[0] == "descriptions"


def test_openness_bucket_assigned_per_product():
    # restricted collapses to the closed bucket; the raw class is preserved alongside it
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-06-10")
    op = payload["categories"]["base_pretrained"]["products"][0]["openness"]
    assert op["class"] == "restricted"
    assert op["bucket"] == "closed"


def test_openness_bucket_covers_open_and_open_ish():
    src = _sources()
    src["scores"]["llama-4"]["openness"] = {"score": 5, "class": "open_source"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["openness"]["bucket"] == "open"
    src["scores"]["llama-4"]["openness"] = {"score": 3, "class": "open_weights"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["openness"]["bucket"] == "open-ish"


def _mature_flag(cls, adoption, capability, weights=None):
    src = _sources()
    src["scores"]["llama-4"]["openness"] = {"score": 5, "class": cls}
    src["scores"]["llama-4"]["adoption"] = {"level": adoption, "signal_type": "usage_volume"}
    src["scores"]["llama-4"]["capability"] = {"score": capability, "basis": "x"}
    if weights is not None:
        src["categories"]["base_pretrained"]["weights"] = weights
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    return payload["categories"]["base_pretrained"]["products"][0]["mature"]


def test_mature_flag_matches_stage_engine_rule():
    # Rule: maturity is not None AND maturity >= 4.5 AND bucket == "open".
    # Fully open, blended 5.0 -> mature.
    assert _mature_flag("open_source", 5, 5) is True
    # Fully open but blended 4.0 (< 4.5 bar) -> not mature.
    assert _mature_flag("open_source", 4, 4) is False
    # Open-weights (open-ish bucket), blended 5.0 -> NOT mature: the bucket gate fails.
    assert _mature_flag("open_weights", 5, 5) is False
    # Closed, blended 5.0 -> not mature.
    assert _mature_flag("closed", 5, 5) is False
    # Exactly at the 4.5 bar, fully open -> mature (>= is inclusive).
    assert _mature_flag("open_source", 4, 5) is True


def test_mature_flag_false_when_maturity_null():
    src = _sources()
    src["scores"]["llama-4"]["openness"] = {"score": 5, "class": "open_source"}
    src["scores"]["llama-4"]["adoption"] = {"level": None, "signal_type": "unknown"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    row = payload["categories"]["base_pretrained"]["products"][0]
    assert row["maturity"] is None
    assert row["mature"] is False


def _row_for(cls, adoption, capability, weights=None):
    src = _sources()
    src["scores"]["llama-4"]["openness"] = {"score": 5, "class": cls}
    src["scores"]["llama-4"]["adoption"] = {"level": adoption, "signal_type": "usage_volume"}
    src["scores"]["llama-4"]["capability"] = {"score": capability, "basis": "x"}
    if weights is not None:
        src["categories"]["base_pretrained"]["weights"] = weights
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    return payload["categories"]["base_pretrained"]["products"][0]


def test_overall_score_dual_publishes_with_maturity():
    # Both keys ship for one release so the front end and the warehouse can migrate before
    # `maturity` is removed. Same value, including the null.
    row = _row_for("open_source", 4, 5)
    assert row["overall_score"] == row["maturity"] == 4.5
    null_row = _row_for("open_source", None, 5)
    assert null_row["overall_score"] is None and null_row["maturity"] is None


def test_tier_is_derived_from_the_score_across_all_buckets():
    # Leading needs a 5 on one axis: 4 and 4 blends to exactly 4.0 and is Strong.
    assert _row_for("open_source", 5, 4)["tier"] == "leading"
    assert _row_for("open_source", 4, 4)["tier"] == "strong"
    assert _row_for("open_source", 3, 4)["tier"] is None
    assert _row_for("open_source", None, 4)["tier"] is None
    # Unlike `mature`, the tier describes the product rather than the open ecosystem, so it
    # is not gated on the openness bucket.
    closed = _row_for("closed", 5, 5)
    assert closed["tier"] == "leading" and closed["mature"] is False


def test_tier_boundaries_are_inclusive_at_the_bottom():
    # 4.5 is Leading, not Strong; 4.0 is Strong, not unlabeled.
    assert _row_for("open_source", 4, 5, {"adopt": 0.5, "cap": 0.5})["overall_score"] == 4.5
    assert _row_for("open_source", 4, 5, {"adopt": 0.5, "cap": 0.5})["tier"] == "leading"
    assert _row_for("open_source", 4, 4, {"adopt": 0.5, "cap": 0.5})["tier"] == "strong"


def test_unknown_org_renders_empty_string():
    s = _sources()
    s["organizations"] = {"unknown": {"name": "unknown", "display_name": "Unknown",
                                      "type": "unknown", "products": ["llama-4"]}}
    payload = build_payload(s, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["org"] == ""


def test_every_product_carries_its_slug_and_org_slug():
    """Identity survives PRODUCT_KEY_ORDER — the whitelist at serialize.py:226 silently
    drops any key not listed, so this fails loudly rather than emitting a slug-less payload."""
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-01-01")
    rows = [p for c in payload["categories"].values() for p in c["products"]]
    assert rows, "fixture produced no products"
    for row in rows:
        assert row["slug"], f"{row['product']} has no slug"
        assert row["org_slug"], f"{row['product']} has no org_slug"


def _pd(cls, adoption):
    return {"openness": {"class": cls}, "adoption": {"level": adoption},
            "capability": {"score": None}, "type": "dataset"}


def test_disclosure_gap_flagged_even_at_top_stage():
    # 4 mature open corpora -> Stage 5; disclosure is a declared attribute that still
    # applies at the top rung (the frontier's own data recipe stays invisible).
    rows = [_pd("open", 5) for _ in range(4)]
    sg = _stage_and_gaps(rows, {"adopt": 1.0, "cap": 0.0}, disclosure=True)
    assert sg["num"] == 5 and sg["gaps"] == ["disclosure"]


def test_disclosure_gap_coexists_with_stage_gaps():
    rows = [_pd("open", 5), _pd("open", 3)]  # one mature open corpus -> stage 4
    sg = _stage_and_gaps(rows, {"adopt": 1.0, "cap": 0.0}, disclosure=True)
    assert sg["num"] == 4 and sg["gaps"] == ["depth", "disclosure"]


def test_no_disclosure_gap_when_not_declared():
    # not declared (e.g. benchmark data: open benchmarks are the shared public standard)
    rows = [_pd("open", 4), _pd("open", 3)]
    sg = _stage_and_gaps(rows, {"adopt": 1.0, "cap": 0.0})
    assert "disclosure" not in sg["gaps"]


def test_disclosure_flag_is_independent_of_closed_rows():
    # presence of a closed row no longer toggles disclosure -- it is declared, not inferred
    rows = [_pd("open", 4), _pd("closed", None)]
    assert "disclosure" in _stage_and_gaps(rows, {"adopt": 1.0, "cap": 0.0}, disclosure=True)["gaps"]
    assert "disclosure" not in _stage_and_gaps(rows, {"adopt": 1.0, "cap": 0.0})["gaps"]


def test_organizations_block_is_complete_and_deterministic():
    """Every org_slug a product points at must resolve, or the app's org links 404.
    Sorted because the payload feeds a daily bot PR and unsorted keys are review noise."""
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-01-01")
    orgs = payload["organizations"]
    assert list(orgs) == sorted(orgs), "organization keys must be sorted"
    rows = [p for c in payload["categories"].values() for p in c["products"]]
    for row in rows:
        assert row["org_slug"] in orgs, f"{row['slug']} points at missing org {row['org_slug']}"
    for slug, org in orgs.items():
        assert org["slug"] == slug
        assert org["products"] == sorted(org["products"]), f"{slug} roster must be sorted"
        assert isinstance(org["github"], list)
        for url in org["github"]:
            assert isinstance(url, str), f"{slug} github must be flat URL strings"


def _multi_org_sources():
    """Two organizations, deliberately unsorted at every level the shared _sources()
    fixture cannot exercise: zeta-labs owns two products listed out of order and two
    github entries listed out of order; alpha-labs sorts before it but is declared
    second. The shared fixture has one org, one product, and no github key at all, so
    it cannot go red on any of this -- see the review finding this test answers."""
    return {
        "organizations": {
            "zeta-labs": {"name": "zeta-labs", "display_name": "Zeta Labs", "type": "company",
                         "github": [{"url": "https://github.com/zeta-two"},
                                    {"url": "https://github.com/zeta-one"}],
                         "products": ["zeta-b", "zeta-a"]},
            "alpha-labs": {"name": "alpha-labs", "display_name": "Alpha Labs", "type": "company",
                          "products": ["alpha-x"]},
        },
        "taxonomy": {"arcs": [{"name": "Model components", "layer": "model_components",
                               "categories": ["base_pretrained"]}]},
        "categories": {
            "base_pretrained": {"name": "base_pretrained",
                                "display_name": "Base / pretrained models",
                                "products": ["zeta-a", "zeta-b", "alpha-x"], "comments": ""}
        },
        "products": {
            "zeta-a": {"name": "zeta-a", "display_name": "Zeta A", "type": "model", "description": "d"},
            "zeta-b": {"name": "zeta-b", "display_name": "Zeta B", "type": "model", "description": "d"},
            "alpha-x": {"name": "alpha-x", "display_name": "Alpha X", "type": "model", "description": "d"},
        },
        "scores": {
            slug: {"product": slug, "openness": {"score": 2, "class": "restricted"},
                  "adoption": {"level": 3, "signal_type": "usage_volume"},
                  "capability": {"score": None, "basis": "n/a"}}
            for slug in ("zeta-a", "zeta-b", "alpha-x")
        },
    }


def test_organizations_block_sorts_github_urls_and_out_of_order_rosters():
    """Regression for the finding that github.py:255-256 preserved source order: a
    cosmetic reorder of a YAML github: list or products: roster must not change the
    payload, or a curator's harmless edit becomes a phantom daily bot PR."""
    payload = build_payload(_multi_org_sources(), frozen_long_tail={}, generated="2026-01-01")
    orgs = payload["organizations"]
    assert list(orgs) == ["alpha-labs", "zeta-labs"]
    assert orgs["zeta-labs"]["products"] == ["zeta-a", "zeta-b"]
    assert orgs["zeta-labs"]["github"] == [
        "https://github.com/zeta-one", "https://github.com/zeta-two",
    ], "github urls must be sorted, not preserved in source order"


def _sources_with_aliases():
    src = _sources()
    # Declared out of alphabetical order, so a missing sort call would leave the payload's
    # key order matching record order instead. The payload feeds a daily automated PR in
    # another repo, where that shows up as a phantom diff.
    src["products"]["llama-4"]["aliases"] = ["llama-4-scout", "aaa-legacy-name"]
    src["organizations"]["meta"]["aliases"] = ["meta-platforms", "facebook"]
    return src


def test_aliases_are_gathered_from_the_records_and_sorted():
    payload = build_payload(_sources_with_aliases(), frozen_long_tail={}, generated="2026-01-01")
    aliases = payload["aliases"]
    assert aliases["products"] == {"aaa-legacy-name": "llama-4", "llama-4-scout": "llama-4"}
    assert aliases["organizations"] == {"facebook": "meta", "meta-platforms": "meta"}
    assert set(aliases) == {"products", "organizations"}
    assert list(aliases["products"]) == sorted(aliases["products"]), \
        "product aliases must be sorted, not left in record order"
    assert list(aliases["organizations"]) == sorted(aliases["organizations"]), \
        "organization aliases must be sorted, not left in record order"

    live = {p["slug"] for c in payload["categories"].values() for p in c["products"]}
    for old, new in aliases["products"].items():
        assert old not in live, f"alias {old} is also a live product slug"
        assert new in live, f"alias {old} points at missing product {new}"
    for old, new in aliases["organizations"].items():
        assert old not in payload["organizations"], f"alias {old} is also a live org"
        assert new in payload["organizations"], f"alias {old} points at missing org {new}"


def test_a_product_with_no_aliases_contributes_nothing():
    """Most products carry none. The gather must not invent an empty entry for them."""
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-01-01")
    assert payload["aliases"] == {"products": {}, "organizations": {}}


# --- Payload version -------------------------------------------------------
# The map surfaces this string as "which release am I looking at", so it has to be the
# version the repo actually released, not a number that can be set independently here.

def test_payload_carries_an_explicit_version():
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-06-10",
                            version="1.2.3", released="2026-01-02")
    assert payload["version"] == "1.2.3"


def test_an_unreleased_version_is_rejected_rather_than_dated_from_elsewhere():
    """Naming a version with no changelog entry fails instead of borrowing a date."""
    with pytest.raises(ValueError, match="1.2.3"):
        build_payload(_sources(), frozen_long_tail={}, generated="2026-06-10",
                      version="1.2.3")


def test_payload_version_defaults_to_the_release_version():
    """Left unset, the payload names the same version pyproject.toml does."""
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-06-10")
    assert payload["version"] == repo_version()


def test_repo_version_agrees_with_the_newest_dated_changelog_entry():
    """The payload's default cannot name a version the changelog never released."""
    from tests.test_release_metadata import _changelog_newest_dated_version
    assert repo_version() == _changelog_newest_dated_version()


def test_payload_carries_an_explicit_release_date():
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-06-10",
                            version="1.2.3", released="2026-01-02")
    assert payload["released"] == "2026-01-02"


def test_release_date_is_looked_up_by_version(tmp_path):
    """The date comes from that version's own heading, not the newest one."""
    (tmp_path / "CHANGELOG.md").write_text(
        "## [Unreleased]\n\n## [0.3.0] - 2026-09-01\n\n## [0.2.0] - 2026-08-16\n")
    assert release_date("0.2.0", root=tmp_path) == "2026-08-16"
    assert release_date("0.3.0", root=tmp_path) == "2026-09-01"


def test_release_date_rejects_a_version_with_no_dated_heading(tmp_path):
    """An unreleased version is an error here, not a silent fallback to another date."""
    (tmp_path / "CHANGELOG.md").write_text("## [Unreleased]\n\n## [0.2.0] - 2026-08-16\n")
    with pytest.raises(ValueError, match="0.9.9"):
        release_date("0.9.9", root=tmp_path)


def test_payload_release_date_defaults_to_the_changelog_date():
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-06-10")
    assert payload["released"] == release_date(repo_version())


def test_descriptions_match_the_reference_doc():
    """The payload's stage and gap definitions are quoted verbatim in gap-analysis.md.

    They are one text with two homes: the legend a visitor reads and the reference a curator
    reads. Prose that merely agrees in substance drifts silently — nothing here could tell you
    which version was current — so the contract is character equality, and this is what enforces
    it. The doc carries the thresholds and the assignment rules around these sentences; those
    are the mechanism and are deliberately absent from the payload.
    """
    from build.serialize import ROOT, _GAP_DESC, _STAGE_DESC, _STAGE_NAMES

    # Every assertion binds a definition to its owner. Checking only that a sentence appears
    # somewhere in the file would pass with two definitions swapped, which is a drift this guard
    # exists to catch: the text would be present, attached to the wrong stage or gap.
    doc = (ROOT / "docs" / "reference" / "gap-analysis.md").read_text()
    for gap, text in _GAP_DESC.items():
        assert f"- **`{gap}`** — {text}" in doc, f"gap-analysis.md is out of sync for `{gap}`"
    for num, text in _STAGE_DESC.items():
        row = f"| **{num}** | {_STAGE_NAMES[num]} | {text} |"
        assert row in doc, f"gap-analysis.md is out of sync for stage {num}"

    # methodology.md uses its own list formatting and appends the mechanism after some
    # definitions, so this matches the labelled prefix rather than the whole line.
    method = (ROOT / "docs" / "methodology.md").read_text()
    for gap, text in _GAP_DESC.items():
        assert f"- **{gap.title()}:** {text}" in method, f"methodology.md is out of sync for `{gap}`"
    # Stages in BOTH docs, not just the reference one. Binding gaps in two files and stages in
    # one is how methodology.md kept the pre-#320 stage wording through a review that thought
    # the guard covered it.
    for num, text in _STAGE_DESC.items():
        labelled = f"- **Stage {num}: {_STAGE_NAMES[num]}.** {text}"
        assert labelled in method, f"methodology.md is out of sync for stage {num}"
