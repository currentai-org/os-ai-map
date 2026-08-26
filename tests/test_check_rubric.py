"""Tests for the rubric checker.

`check_rubric` is what lets a rubric be trusted, so the checker itself needs
checking. Three behaviors added when the rubric was ported to a second category
carry most of the risk, because each one fails QUIETLY:

  * `reads` picks which recorded key answers a dimension. Pick wrong and a product
    is scored on somebody else's training data.
  * `deferred` excludes a product from the reproduction count. Get it wrong and a
    rubric reports 43/43 while ignoring the products that contradict it.
  * recorded-name aliases resolve spellings of one license. Miss one and a present,
    use-restricting license reads as absent, which overstates openness.
"""

from __future__ import annotations

import pytest
import yaml

from build.check_rubric import (
    ROOT,
    check_category,
    dimension_value,
    license_entry,
    license_tier,
    normalize_license,
    recorded_license_aliases,
    split_components,
)


def write_yaml(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))

RECIPE = {
    "openness": {
        "dimensions": {
            "data": {
                "reads": ["post-training-data", "data"],
                "values": ["open", "closed", "described"],
            },
            "code": {"values": ["open", "partial", "closed"]},
        },
        "license_tier": {
            "values": {
                "osi": {"examples": ["Apache-2.0", "MIT"]},
                "use_restricted": {"examples": ["Gemma-License", "GLM-4-License"]},
            }
        },
    }
}


class TestDimensionValue:
    def test_prefers_declared_key_order_over_string_order(self):
        """A product answering both questions must be read by preference, not by
        whichever key the author happened to type first."""
        components = split_components("data:closed;post-training-data:open")
        assert dimension_value(components, "data", RECIPE) == "open"

    def test_prefers_an_in_enum_value_over_an_earlier_out_of_enum_one(self):
        """`post-training-data` is preferred, but only when it actually answers. A
        free-text value there must not shadow a usable `data`."""
        components = split_components("data:closed;post-training-data:SFT on UltraChat")
        assert dimension_value(components, "data", RECIPE) == "closed"

    def test_falls_back_to_first_present_key_when_nothing_is_in_enum(self):
        """Returning '' here would read as absent and land the product in
        `otherwise`. Surfacing the unrecognized value makes the mismatch legible."""
        components = split_components("post-training-data:SFT on UltraChat")
        assert dimension_value(components, "data", RECIPE) == "SFT on UltraChat"

    def test_absent_dimension_is_empty(self):
        assert dimension_value(split_components("weights:open"), "data", RECIPE) == ""

    def test_undeclared_reads_defaults_to_the_dimension_name(self):
        """base_pretrained declares no `reads`; it must keep reading its own key."""
        components = split_components("code:partial;post-training-data:open")
        assert dimension_value(components, "code", RECIPE) == "partial"

    def test_strips_parenthetical_detail(self):
        components = split_components("data:open(UltraChat_200k + UltraFeedback, both MIT)")
        assert dimension_value(components, "data", RECIPE) == "open"


ALIAS_RECIPE = {
    "openness": {
        "dimensions": {
            "core_gated": {
                "values": ["gated", "ungated"],
                "reads": ["core-gated", "self-host"],
                "value_aliases": {
                    "yes": "ungated", "primary": "ungated", "only": "ungated",
                    "no": "gated", "none": "gated", "enterprise-only": "gated",
                },
            },
        },
    }
}


class TestValueAliases:
    """`reads` widens which KEY answers a dimension; `value_aliases` widens which VALUE
    does. Both are needed for a synonym key that carries its own vocabulary, which is what
    `self-host` is to `core-gated`.
    """

    def test_a_synonym_value_resolves_to_the_declared_one(self):
        components = split_components("self-host:none")
        assert dimension_value(components, "core_gated", ALIAS_RECIPE) == "gated"

    def test_the_declared_value_is_returned_unchanged(self):
        components = split_components("core-gated:ungated")
        assert dimension_value(components, "core_gated", ALIAS_RECIPE) == "ungated"

    def test_parenthetical_detail_is_stripped_before_translation(self):
        """`enterprise-only(hybrid)` and `no(managed only)` are both real recordings, and
        the alias table holds bare tokens rather than every phrasing around them."""
        components = split_components("self-host:enterprise-only(hybrid)")
        assert dimension_value(components, "core_gated", ALIAS_RECIPE) == "gated"

    def test_the_preferred_key_still_wins_when_both_are_recorded(self):
        """23 records carry both keys. `core-gated` is declared first and is the
        dimension's own vocabulary, so it decides."""
        components = split_components("self-host:yes;core-gated:gated")
        assert dimension_value(components, "core_gated", ALIAS_RECIPE) == "gated"

    def test_a_synonym_key_wins_when_the_preferred_one_is_out_of_enum(self):
        """The in-enum preference has to survive translation, or a garbled `core-gated`
        would shadow a `self-host` that answers cleanly."""
        components = split_components("core-gated:see pricing page;self-host:none")
        assert dimension_value(components, "core_gated", ALIAS_RECIPE) == "gated"

    def test_an_unmapped_value_is_not_guessed_at(self):
        """It comes back untranslated, lands outside the enum, and the formula abstains.
        The software ladder declares no `otherwise`, so abstaining is the safe default and
        inventing a polarity from an unrecognized word is the failure that would not
        surface."""
        components = split_components("self-host:byoc")
        assert dimension_value(components, "core_gated", ALIAS_RECIPE) == "byoc"

    def test_a_dimension_with_no_aliases_is_unaffected(self):
        components = split_components("data:closed;post-training-data:open")
        assert dimension_value(components, "data", RECIPE) == "open"


class TestRecordedLicenseAliases:
    @pytest.mark.parametrize(
        ("recorded", "canonical"),
        [
            ("Gemma-Terms-of-Use", "Gemma-License"),
            ("glm-4", "GLM-4-License"),
            ("Llama-3.1-Community", "Llama-3.1-Community-License"),
            ("NVIDIA-Nemotron-Open-Model-License", "NVIDIA-Open-Model-License"),
        ],
    )
    def test_resolves_recorded_spellings(self, recorded, canonical):
        assert normalize_license(recorded) == canonical

    def test_alias_applies_after_the_mechanical_steps(self):
        """`assumed-` is stripped first, so the alias table does not have to
        enumerate a prefixed variant of every license."""
        assert normalize_license("assumed-Gemma-Terms-of-Use") == "Gemma-License"

    def test_alias_applies_after_the_scope_prefix_is_dropped(self):
        """`normalize_license` reads ONE part now, and a part may carry the scope it
        covers. Dropping `code `/`model ` before the lookup keeps the alias table from
        having to enumerate a scoped variant of every license."""
        assert normalize_license("model glm-4") == "GLM-4-License"

    def test_alias_applies_across_a_compound_split(self):
        """What used to be a special case - `code X + model Y`, the model license governs -
        is now a consequence of resolving both parts and keeping the more restrictive."""
        assert license_tier(license_entry("code MIT + model glm-4"), RECIPE) == "use_restricted"

    def test_a_name_is_never_truncated(self):
        """`normalize_license` used to open with `head`, which cut at the first `(` or `,`.
        A structured `name` is already bare, so the cut had nothing left to do and every
        remaining case for it was a recording error resolving on its first token."""
        assert normalize_license("MIT(code)") == "MIT(code)"
        assert normalize_license("Apache-2.0, and others") == "Apache-2.0, and others"

    def test_canonical_names_pass_through_untouched(self):
        assert normalize_license("Apache-2.0") == "Apache-2.0"

    def test_an_aliased_name_reaches_a_tier(self):
        """The whole point: the spelling must not cost the product its tier."""
        assert license_tier(license_entry("Gemma-Terms-of-Use(custom,non-OSI)"), RECIPE) == (
            "use_restricted"
        )

    def test_an_unaliased_unknown_license_still_abstains(self):
        """Aliases resolve names, never tiers. An unknown license must keep
        abstaining so it shows up as a finding rather than a guess."""
        assert license_tier(license_entry("Some-New-Vendor-License"), RECIPE) is None

    def test_no_alias_maps_onto_a_different_canonical_name(self):
        """An alias whose target is itself an alias key would make resolution
        order-dependent."""
        aliases = recorded_license_aliases()
        targets = {name.lower() for name in aliases.values()}
        assert not (targets & set(aliases)), "alias target is itself an alias key"


class TestCompoundLicense:
    """A compound resolves on ALL its parts, most restrictive governing.

    The bug this replaces was quiet and one-directional: resolution truncated at the
    first `(` or `,`, so a value naming two licenses was decided by whichever was typed
    first, and the half that actually restricted the artifact was never read. Every one
    of these tests fails against that behavior.
    """

    def test_the_restrictive_half_governs_whichever_side_it_is_on(self):
        assert license_tier(license_entry("MIT(code)+Gemma-License(weights)"), RECIPE) == (
            "use_restricted"
        )
        assert license_tier(license_entry("Gemma-License(weights)+MIT(code)"), RECIPE) == (
            "use_restricted"
        )

    def test_all_permissive_parts_stay_permissive(self):
        assert license_tier(license_entry("Apache-2.0(core)+MIT(SDKs)"), RECIPE) == "osi"

    def test_a_part_is_split_on_plus_only_never_on_a_comma(self):
        """Every depth-zero comma in the corpus trails prose after a single license -
        `Proprietary, proprietary service`. Treating one as a separator would invent a
        second license out of the annotation."""
        assert license_tier(
            license_entry("MIT(client)+Gemma-License(weights),both-published"), RECIPE
        ) == "use_restricted"

    def test_a_plus_inside_an_annotation_is_not_a_separator(self):
        assert license_tier(license_entry("MIT(bundles A + B)"), RECIPE) == "osi"

    def test_an_unmapped_part_abstains_rather_than_being_skipped(self):
        """The whole point. An unmapped part can only be MORE restrictive than the tier
        the mapped parts reached, so ignoring it publishes an overstatement."""
        assert license_tier(
            license_entry("Apache-2.0(code)+Some-New-Vendor-License(weights)"), RECIPE
        ) is None

    def test_a_declared_compound_is_recorded_as_one_part(self):
        """A recipe may declare a compound as one name - `follows mC4 + OSCAR-2301 terms`,
        where the `+` is English joining two CORPUS names and neither operand is a license.

        `license_tier` has no whole-value pre-check to catch that any more, and does not
        need one: the curator records ONE part, and one part is what resolves. The intent
        is in the data instead of being re-inferred from punctuation on every read, which
        is what let the repo and the warehouse disagree about the same value.
        """
        recipe = {
            "openness": {
                "license_tier": {
                    "values": {
                        "osi": {"examples": ["MIT"]},
                        "deferred": {"examples": ["follows mC4 + OSCAR-2301 terms"]},
                    }
                }
            }
        }
        assert license_tier([{"name": "follows mC4 + OSCAR-2301 terms"}], recipe) == "deferred"

    def test_the_same_phrase_split_into_parts_abstains(self):
        """The other half of the contract, and the reason `culturax` is recorded by hand.
        Mechanically structured, the phrase becomes two parts that name no license, and
        every part must resolve or the value abstains."""
        recipe = {
            "openness": {
                "license_tier": {
                    "values": {
                        "osi": {"examples": ["MIT"]},
                        "deferred": {"examples": ["follows mC4 + OSCAR-2301 terms"]},
                    }
                }
            }
        }
        assert license_tier(license_entry("follows mC4 + OSCAR-2301 terms"), recipe) is None

    def test_a_single_license_is_unaffected(self):
        assert license_tier(license_entry("Apache-2.0(OSI, see LICENSE)"), RECIPE) == "osi"

    def test_a_ladder_with_no_tiers_still_abstains(self):
        assert license_tier(license_entry("Apache-2.0"), {"openness": {}}) is None


class TestRealCategories:
    """The claim the whole pipeline rests on, asserted against the real files."""

    def test_base_pretrained_still_reproduces_every_score(self):
        """27, down from 44 then up 1: the slug migration collapsed release-level products
        into the tier the vendor sells and moved the closed frontier models to
        finetuned_chat (44 -> 26); adding the fully-open Luciole family took it to 27. The
        point of pinning this is that the count only ever moves for a reason recorded in a
        commit."""
        reproduced, total, problems, deferred, _ = check_category("base_pretrained", verbose=False)
        assert problems == []
        assert (reproduced, total, deferred) == (27, 27, [])

    def test_finetuned_chat_reproduces_every_undeferred_score(self):
        reproduced, total, problems, *_ = check_category("finetuned_chat", verbose=False)
        assert problems == []
        assert reproduced == total == 39

    def test_no_category_defers_without_a_substantive_reason(self):
        """A deferral that prints nothing is a silent cap on coverage.

        Written as an invariant over every category rather than a fixed list, because
        the list is currently empty: issue #117 settled conduct-versus-commerce, which
        decided the three products finetuned_chat used to defer. Asserting "3 deferred"
        would have to be edited every time the count moves; asserting "any deferral
        carries a reason" holds at zero and bites the moment one is added."""
        import yaml

        for path in sorted((ROOT / "sources" / "categories").glob("*.yaml")):
            category = yaml.safe_load(path.read_text())
            if not category.get("scoring_recipe"):
                continue
            _, _, problems, deferred, _ = check_category(category["name"], verbose=False)
            assert problems == [], f"{category['name']}: {problems}"
            for entry in deferred:
                reason = entry.split(":", 1)[1].strip()
                assert len(reason) > 40, f"{category['name']}: no real reason given: {entry}"

    def test_finetuned_chat_currently_defers_nothing(self):
        """The count itself, pinned separately so a new deferral is visible in a diff."""
        _, _, _, deferred, _ = check_category("finetuned_chat", verbose=False)
        assert deferred == []

    def test_deferred_products_are_excluded_not_counted_as_reproduced(self):
        """39 scored and 0 deferred. Counting a deferral as a pass is how a rubric
        claims to describe products it cannot score, so the identity is worth keeping
        even while the deferral count is zero."""
        _, total, _, deferred, _ = check_category("finetuned_chat", verbose=False)
        assert total + len(deferred) == 39


def test_mixed_type_category_scores_each_product_on_its_own_ladder(tmp_path, monkeypatch):
    # Arrange a category holding one model and one software product, a shared
    # ladder for each, and score files that reproduce only if the right ladder
    # is applied to the right product.
    write_yaml(tmp_path / "sources/rubrics/model.yaml", {
        "openness": {
            "license_tier": {"reads": ["license"], "values": {"osi": {"examples": ["Apache-2.0"]}}},
            "dimensions": {"weights": {"values": ["open", "closed"]}},
            "formula": [
                {"when": {"weights": "open"}, "then": {"score": 5, "class": "open_source"}},
                {"otherwise": {"score": 1, "class": "closed"}},
            ],
        }
    })
    write_yaml(tmp_path / "sources/rubrics/software.yaml", {
        "openness": {
            "license_tier": {"reads": ["license"], "values": {"osi": {"examples": ["Apache-2.0"]}}},
            "dimensions": {"source": {"values": ["public", "closed"]}},
            "formula": [
                {"when": {"source": "public", "license_tier": "osi"},
                 "then": {"score": 5, "class": "open_source"}},
            ],
        }
    })
    write_yaml(tmp_path / "sources/categories/mixed.yaml", {
        "name": "mixed",
        "products": ["a-model", "a-tool"],
        "scoring_recipe": {"extends": {"model": "model", "software": "software"}},
    })
    write_yaml(tmp_path / "sources/products/a-model.yaml", {"name": "a-model", "type": "model"})
    write_yaml(tmp_path / "sources/products/a-tool.yaml", {"name": "a-tool", "type": "software"})
    write_yaml(tmp_path / "sources/scores/a-model.yaml", {
        "openness": {"score": 5, "class": "open_source", "components": "weights:open;license:Apache-2.0"}
    })
    write_yaml(tmp_path / "sources/scores/a-tool.yaml", {
        "openness": {"score": 5, "class": "open_source", "components": "source:public;license:Apache-2.0"}
    })
    monkeypatch.setattr("build.check_rubric.ROOT", tmp_path)
    # Cold cache: reset the module-level alias cache so this test does not depend on an
    # earlier test in the file having already warmed it against the real ROOT. Without
    # this, `recorded_license_aliases()` reads `tmp_path/sources/signal_routing.yaml`,
    # which does not exist, and the test's pass/fail depends on suite ordering.
    monkeypatch.setattr("build.check_rubric._RECORDED_ALIASES", {})

    reproduced, total, problems, deferred, _ = check_category("mixed", verbose=False)

    assert problems == []
    assert (reproduced, total) == (2, 2)


def test_a_ladder_with_no_license_tier_scores_rather_than_failing(tmp_path, monkeypatch):
    """Hardware openness turns on design and toolchain, not a source license.

    `license_tier()` returns None for a recipe declaring no tiers, and that used to append a
    problem per product — so a tier-free ladder reported every one of its products as a hard
    failure and could not be written at all. `sources/rubrics/hardware.yaml` is the real case:
    none of `edge_hardware`'s 20 products records a license, because a board is not licensed
    the way software is.

    The tier step now runs only where there is a tier vocabulary to resolve against, and
    `license_tier` is simply absent from the facts. A rung testing it could not have been
    declared — check_recipe's unreachable-rule assertion rejects a `license_tier` condition
    against no declared tiers.
    """
    write_yaml(tmp_path / "sources/rubrics/hardware.yaml", {
        "openness": {
            "dimensions": {"schematics": {"values": ["open", "none"]}},
            "formula": [
                {"when": {"schematics": "open"}, "then": {"score": 5, "class": "open_hardware"}},
                {"when": {"schematics": "none"}, "then": {"score": 3, "class": "documented"}},
            ],
        }
    })
    write_yaml(tmp_path / "sources/categories/boards.yaml", {
        "name": "boards",
        "products": ["a-board", "a-chip"],
        "scoring_recipe": {"extends": "hardware"},
    })
    for slug in ("a-board", "a-chip"):
        write_yaml(tmp_path / f"sources/products/{slug}.yaml", {"name": slug, "type": "hardware"})
    write_yaml(tmp_path / "sources/scores/a-board.yaml", {
        "openness": {"score": 5, "class": "open_hardware", "components": "schematics:open"}
    })
    write_yaml(tmp_path / "sources/scores/a-chip.yaml", {
        "openness": {"score": 3, "class": "documented", "components": "schematics:none"}
    })
    monkeypatch.setattr("build.check_rubric.ROOT", tmp_path)
    monkeypatch.setattr("build.check_rubric._RECORDED_ALIASES", {})

    reproduced, total, problems, deferred, _ = check_category("boards", verbose=False)

    assert problems == []
    assert (reproduced, total) == (2, 2)


def _tier_gate_fixture(tmp_path, monkeypatch, formula, components):
    """A one-product software category, so the tier gate can be exercised per formula."""
    write_yaml(tmp_path / "sources/rubrics/software.yaml", {
        "openness": {
            "license_tier": {"reads": ["license"], "values": {"osi": {"examples": ["MIT"]}}},
            "dimensions": {"source": {"values": ["public", "partial"]}},
            "formula": formula,
        }
    })
    write_yaml(tmp_path / "sources/categories/tools.yaml", {
        "name": "tools", "products": ["a-tool"],
        "scoring_recipe": {"extends": "software"},
    })
    write_yaml(tmp_path / "sources/products/a-tool.yaml", {"name": "a-tool", "type": "software"})
    write_yaml(tmp_path / "sources/scores/a-tool.yaml", {
        "openness": {"score": 5, "class": "open_source", "components": components}
    })
    monkeypatch.setattr("build.check_rubric.ROOT", tmp_path)
    monkeypatch.setattr("build.check_rubric._RECORDED_ALIASES", {})
    return check_category("tools", verbose=False)


def test_a_rung_that_TESTS_the_tier_still_fails_an_unmappable_license(tmp_path, monkeypatch):
    """The allowance is scoped to a rung that does not ask, not to a missing license.

    A ladder whose deciding rung turns on `license_tier` and meets a license outside its
    vocabulary must still report that, or "resolve the tier only when a rung needs one"
    would quietly become an escape hatch for every unmapped license on the map. `dify`,
    `max`, `open-webui`, `lobe-chat` and `autogpt` were the real cases: all record
    `source:public`, which reaches a rung that tests the tier, so their vendor licenses
    blocked them until those licenses were mapped to `competition_restricted`. Mapping the
    license is the fix this gate is meant to force; the gate itself is unchanged, which is
    why the assertion below stands on a fixture rather than on any of the five.
    """
    report = _tier_gate_fixture(
        tmp_path, monkeypatch,
        formula=[{
            "when": {"license_tier": "osi", "source": "public"},
            "then": {"score": 5, "class": "open_source"},
        }],
        components="source:public;license:Some-Unmapped-License",
    )

    assert len(report.problems) == 1 and "maps to no tier" in report.problems[0]
    assert report.tierless == []


def test_a_rung_reading_source_alone_scores_without_resolving_a_tier(tmp_path, monkeypatch):
    """The fix. A product settled on `source` alone must not wait on a license nobody reads.

    `apify` is the case the owner ruled on: it records `mixed(platform closed, SDK open)`,
    which names no license, and `source:partial`, which the software ladder settles at
    2/source_available on the source dimension alone. Resolving the tier first abstained it
    before the formula ran.
    """
    report = _tier_gate_fixture(
        tmp_path, monkeypatch,
        formula=[
            {"when": {"source": "public"}, "then": {"score": 5, "class": "open_source"}},
            {
                "when": {"license_tier": "osi", "source": "partial"},
                "then": {"score": 2, "class": "source_available"},
            },
        ],
        components="source:public;license:Some-Unmapped-License",
    )

    assert report.problems == []
    assert (report.reproduced, report.total) == (1, 1)


def test_a_product_scoring_without_a_resolved_tier_is_reported(tmp_path, monkeypatch):
    """Scoring without a tier is correct and must stay visible.

    The guard on the fix. A score standing on a license the ladder could not read rests on
    less evidence than its neighbours, and if that license is later mapped the product may
    move. Reported rather than gated: every entry is a correct score, so gating would fail
    on the day it landed.
    """
    report = _tier_gate_fixture(
        tmp_path, monkeypatch,
        formula=[{"when": {"source": "public"}, "then": {"score": 5, "class": "open_source"}}],
        components="source:public;license:Some-Unmapped-License",
    )

    assert report.problems == []
    assert len(report.tierless) == 1
    assert "a-tool" in report.tierless[0]
    assert "Some-Unmapped-License" in report.tierless[0]


def test_a_product_whose_tier_resolves_is_not_reported_as_tierless(tmp_path, monkeypatch):
    """The counterpart, so the report cannot silently widen to every software product.

    Most products never consult a tier — a `source:closed` product is settled on the first
    rung — and reporting those would drown the five entries that mean something.
    """
    report = _tier_gate_fixture(
        tmp_path, monkeypatch,
        formula=[{"when": {"source": "public"}, "then": {"score": 5, "class": "open_source"}}],
        components="source:public;license:MIT",
    )

    assert report.problems == []
    assert report.tierless == []


def test_every_recorded_self_host_value_is_mapped():
    """A ratchet on the real corpus, not a unit test of the mechanism.

    `value_aliases` is a hand-written table over vocabulary contributors keep adding to, and
    an unmapped spelling fails quietly by design: the dimension reads as unanswered and the
    product abstains, which looks exactly like a product nobody has researched yet. This
    turns the quiet case loud at the moment the spelling is introduced, which is the only
    moment anyone knows what it was meant to mean.

    All eight recorded spellings map today. Adding a ninth means adding it here too, or
    recording `core-gated` directly.
    """
    import yaml as _yaml

    from build.check_rubric import components_of, head

    aliases = _yaml.safe_load(
        (ROOT / "sources/rubrics/software.yaml").read_text()
    )["openness"]["dimensions"]["core_gated"]["value_aliases"]

    unmapped = {}
    for path in sorted((ROOT / "sources/scores").glob("*.yaml")):
        components = components_of(_yaml.safe_load(path.read_text()).get("openness") or {})
        value = components.get("self-host")
        if value is not None and head(value) not in aliases:
            unmapped[path.stem] = head(value)

    assert unmapped == {}, (
        f"unmapped `self-host` spellings: {unmapped}. Map each to `gated` or `ungated` in "
        "software.yaml's core_gated.value_aliases, or record `core-gated` on the product."
    )
    assert set(aliases.values()) == {"gated", "ungated"}


# --- the trace primitives: walk_formula_trace and resolve_license_parts ----------
# Added for the repository-owned scoring trace (build/axis_scoring_trace.py). They are the
# single-owner extension the trace reads: `walk_formula` and `license_tier` project them, so
# these prove the projection is faithful rather than a second implementation.


class TestWalkFormulaTrace:
    RECIPE = {
        "openness": {
            "dimensions": {"source": {"values": ["public", "closed", "partial"]}},
            "license_tier": {"values": {"osi": {}, "noncommercial": {}}},
            "formula": [
                {"when": {"source": "closed"}, "then": {"score": 1, "class": "closed"}},
                {"when": {"source": "public", "license_tier": "noncommercial"},
                 "then": {"score": 2, "class": "restricted"}},
                {"when": {"source": "public", "license_tier": "osi"},
                 "then": {"score": 5, "class": "open_source"}},
            ],
        }
    }

    def test_walk_formula_is_a_faithful_projection_of_the_trace(self):
        """The public `(result, blocked)` must equal the trace's, for every input, or the trace
        is a fork. Exercises fired / fell-through / blocked / skipped-to-exhaustion."""
        from build.check_rubric import walk_formula, walk_formula_trace

        cases = [
            ({"source": "closed"}, "osi"),
            ({"source": "public"}, "osi"),
            ({"source": "public"}, None),        # blocks on the noncommercial rung
            ({"source": "partial"}, "osi"),      # nothing fires, no otherwise
        ]
        for facts, tier in cases:
            result, blocked, steps = walk_formula_trace(self.RECIPE, facts, tier)
            assert (result, blocked) == walk_formula(self.RECIPE, facts, tier)
            fired = [s for s in steps if s.outcome == "fired"]
            assert len(fired) == (1 if result is not None else 0)

    def test_records_fell_through_then_fired(self):
        from build.check_rubric import walk_formula_trace

        _result, _blocked, steps = walk_formula_trace(self.RECIPE, {"source": "public"}, "osi")
        assert [s.outcome for s in steps] == ["skipped", "fell_through_tier", "fired"]
        assert steps[-1].rule_index == 2 and steps[-1].result == (5, "open_source")

    def test_blocks_on_an_unresolved_tier_and_stops(self):
        from build.check_rubric import walk_formula_trace

        result, blocked, steps = walk_formula_trace(self.RECIPE, {"source": "public"}, None)
        assert result is None and blocked is True
        assert steps[-1].outcome == "blocked_on_tier" and steps[-1].rule_index == 1
        # the walk stops at the blocking rung — it never reaches the osi rung below it
        assert len(steps) == 2

    def test_otherwise_fires_and_ends_the_walk(self):
        from build.check_rubric import walk_formula_trace

        recipe = {"openness": {"dimensions": {"source": {"values": ["public"]}},
                               "formula": [{"when": {"source": "closed"}, "then": {"score": 1, "class": "closed"}},
                                           {"otherwise": {"score": 3, "class": "mid"}}]}}
        result, blocked, steps = walk_formula_trace(recipe, {"source": "public"}, None)
        assert result == (3, "mid") and blocked is False
        assert steps[-1].kind == "otherwise" and steps[-1].outcome == "fired"


class TestResolveLicenseParts:
    RECIPE = {"openness": {"license_tier": {"values": {
        "osi": {"examples": ["Apache-2.0", "MIT"]},
        "noncommercial": {"examples": ["CC-BY-NC"]},
    }}}}

    def test_pairs_each_part_with_its_tier(self):
        from build.check_rubric import license_entry, resolve_license_parts

        pairs = resolve_license_parts(license_entry("Apache-2.0(code)+CC-BY-NC(weights)"), self.RECIPE)
        assert [(p.get("name"), tier) for p, tier in pairs] == [
            ("Apache-2.0", "osi"), ("CC-BY-NC", "noncommercial"),
        ]

    def test_unmapped_part_is_paired_with_none(self):
        from build.check_rubric import license_entry, resolve_license_parts

        pairs = resolve_license_parts(license_entry("Some-Vendor-License"), self.RECIPE)
        assert [tier for _p, tier in pairs] == [None]

    def test_agrees_with_license_tier_the_governing_cap(self):
        """The governing tier `license_tier` returns is the most restrictive of these parts —
        proving the trace and the score resolve one license the same way."""
        from build.check_rubric import license_entry, license_tier, resolve_license_parts, tier_rank

        parts = license_entry("Apache-2.0+CC-BY-NC")
        pairs = resolve_license_parts(parts, self.RECIPE)
        rank = tier_rank(self.RECIPE["openness"]["license_tier"]["values"])
        governing = max((t for _p, t in pairs), key=lambda name: rank.get(name, 99))
        assert governing == license_tier(parts, self.RECIPE) == "noncommercial"

    def test_tier_free_ladder_yields_no_pairs(self):
        from build.check_rubric import license_entry, resolve_license_parts

        assert resolve_license_parts(license_entry("MIT"), {"openness": {}}) == []
