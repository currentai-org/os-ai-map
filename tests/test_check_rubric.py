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

from build.check_rubric import (
    ROOT,
    check_category,
    dimension_value,
    license_tier,
    normalize_license,
    recorded_license_aliases,
    split_components,
)

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

    def test_alias_applies_after_the_compound_split(self):
        assert normalize_license("code MIT + model glm-4") == "GLM-4-License"

    def test_canonical_names_pass_through_untouched(self):
        assert normalize_license("Apache-2.0") == "Apache-2.0"

    def test_an_aliased_name_reaches_a_tier(self):
        """The whole point: the spelling must not cost the product its tier."""
        assert license_tier("Gemma-Terms-of-Use(custom,non-OSI)", RECIPE) == "use_restricted"

    def test_an_unaliased_unknown_license_still_abstains(self):
        """Aliases resolve names, never tiers. An unknown license must keep
        abstaining so it shows up as a finding rather than a guess."""
        assert license_tier("Some-New-Vendor-License", RECIPE) is None

    def test_no_alias_maps_onto_a_different_canonical_name(self):
        """An alias whose target is itself an alias key would make resolution
        order-dependent."""
        aliases = recorded_license_aliases()
        targets = {name.lower() for name in aliases.values()}
        assert not (targets & set(aliases)), "alias target is itself an alias key"


class TestRealCategories:
    """The claim the whole pipeline rests on, asserted against the real files."""

    def test_base_pretrained_still_reproduces_every_score(self):
        """26, down from 44: the slug migration collapsed release-level products into
        the tier the vendor sells, and moved the closed frontier models to
        finetuned_chat. The point of pinning this is that the count only ever moves for
        a reason recorded in a commit."""
        reproduced, total, problems, deferred = check_category("base_pretrained", verbose=False)
        assert problems == []
        assert (reproduced, total, deferred) == (26, 26, [])

    def test_finetuned_chat_reproduces_every_undeferred_score(self):
        reproduced, total, problems, _ = check_category("finetuned_chat", verbose=False)
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
            _, _, problems, deferred = check_category(category["name"], verbose=False)
            assert problems == [], f"{category['name']}: {problems}"
            for entry in deferred:
                reason = entry.split(":", 1)[1].strip()
                assert len(reason) > 40, f"{category['name']}: no real reason given: {entry}"

    def test_finetuned_chat_currently_defers_nothing(self):
        """The count itself, pinned separately so a new deferral is visible in a diff."""
        _, _, _, deferred = check_category("finetuned_chat", verbose=False)
        assert deferred == []

    def test_deferred_products_are_excluded_not_counted_as_reproduced(self):
        """39 scored and 0 deferred. Counting a deferral as a pass is how a rubric
        claims to describe products it cannot score, so the identity is worth keeping
        even while the deferral count is zero."""
        _, total, _, deferred = check_category("finetuned_chat", verbose=False)
        assert total + len(deferred) == 39
