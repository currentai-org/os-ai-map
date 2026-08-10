"""Serialize each category's scoring rubric and its recorded evidence to flat CSVs.

Companion to `serialize_registry.py`, and deliberately a separate module. That one
emits IDENTITY — which products, organizations and categories exist. This one emits
the two things layer-2 needs in order to compute a score: the rubric that says how
to score, and the evidence recorded against each product.

They are kept apart because their claims differ. The registry is authoritative
about what exists. This module is authoritative about the rubric and explicitly
NOT authoritative about the evidence — it reports what `sources/scores/` currently
records, including the places where that record cites nothing specific. Merging the
two would let a serializer that ships unverified assertions borrow the registry's
credibility.

## Why evidence flows outward when scores do not

`serialize_registry.py` excludes scores on purpose: scoring is computed downstream
and flows back, so mirroring scores outward would point the dependency the wrong
way. Evidence is not a score. It is the input a score is computed FROM, and it has
to reach the scorer somehow.

There is a circularity here worth stating plainly: for the base-model pilot the
document-grade evidence is parsed out of the very files the pipeline writes back
to. That makes the first run a fidelity test of the formula and nothing more. It
can prove the rubric describes how the category was scored; it cannot show the
scores are right. Steady state is evidence from datasets and fresh research, with
these rows surviving only where nothing better exists.

## Parsing stays in the repo

`components` strings are parsed by `build/check_rubric.py`, which is tested and
which CI already gates on. Shipping a second copy of that parser into a warehouse
model would leave two implementations to keep in step, and they would drift. So the
repo emits pre-split dimensions and the warehouse consumes flat facts.

## Grain, and an honest limit

`components` gives a value per dimension. `sources` is a list per AXIS, with no
attribution of a particular source to a particular dimension. So evidence comes out
at dimension grain and sources come out at axis grain, and the two cannot be joined
more tightly than that. The evidence-store design wants source-per-dimension; today's
files do not carry it. Recording the limit beats inventing an attribution.

Emitted tables (CSVs into `build/registry/`, alongside the registry's own):

  category_scoring_rules      the ordered formula, one row per rule condition, per category
                              and product type
  category_license_tiers      tier <- example license, per category and product type
  category_deferrals          products a category has declared its ladder does not decide
  license_aliases             a source's license slug -> canonical license name
  evidence_abstentions        values that mean "this source has no answer"
  product_openness_evidence   per-dimension values parsed from `components`
  product_score_sources       per-axis sources, each with an admission verdict

Usage:
    uv run python -m build.serialize_rubric            # write CSVs
    uv run python -m build.serialize_rubric --check    # validate, write nothing
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from build.check_rubric import (
    dimension_read_map,
    license_read_keys,
    resolve_dimension,
    split_components,
)
from build.rubrics import load_product_types, recipe_for, resolve_recipe_variants
from build.serialize_registry import write_tables
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "registry"

AXES = ("openness", "adoption", "capability")

# `license_tier()` in check_rubric defines the proprietary tier by MEANING rather
# than by an example list, because no vendor publishes a license called
# "proprietary". Those tokens are emitted as definitional examples so the warehouse
# gets one lookup table instead of a lookup table plus a hardcoded special case.
DEFINITIONAL_TIERS = {"proprietary": ("proprietary", "closed", "none")}

TABLES: dict[str, tuple[str, ...]] = {
    "category_scoring_rules": (
        "category_slug",
        "product_type",
        "recipe_version",
        "rule_index",
        "is_otherwise",
        "condition_key",
        "condition_value",
        "then_score",
        "then_class",
    ),
    "category_license_tiers": (
        "category_slug",
        "product_type",
        "tier",
        "tier_rank",
        "example_license",
        "is_definitional",
    ),
    # The ladder's dimension vocabulary, so the warehouse does not have to infer it from
    # which keys the rules happen to test. `openness_computed` needs the declared set for
    # two different things — which evidence rows are facts rather than traceability, and the
    # denominator for "every dimension this score records is dataset-grade" — and a rule's
    # `condition_key` answers neither: a dimension a formula never tests is still recorded,
    # and `license_tier` is a derived fact rather than a declared dimension.
    "category_dimensions": (
        "category_slug",
        "product_type",
        "dimension",
        "reads_keys",
        "declared_values",
    ),
    # Deferrals cross the bridge because silence does not travel. `check_rubric` excludes a
    # deferred product from reproduction, but the warehouse never heard about it, so a ladder
    # ending in `otherwise` scored it anyway: `safeguards` published computed openness for
    # nine guardrail models the repo had explicitly declined to stand behind, and seven of
    # them disagreed with the recorded score. Emitted per category rather than per variant,
    # because `deferred` is declared on `scoring_recipe` itself and applies whichever ladder
    # a product resolves to.
    "category_deferrals": ("category_slug", "product_slug", "because"),
    # Adoption bands, per product TYPE rather than per category, because the scale is a
    # property of what the thing IS. They were hardcoded in the scoring SQL and nowhere
    # else until 2026-08-09 — the repo/warehouse split check_parity exists to catch, one
    # axis over. `above` is the exclusive lower bound, so the highest level whose `above`
    # a figure exceeds wins, which is how the CASE expression already read.
    #
    # Hardware emits no rows on purpose. It declares `qualitative: true` and an empty
    # `bands`, and the absence is the declaration: a consumer finding no band for a type
    # must abstain rather than borrow another type's scale, which is exactly the
    # "abstain rather than substitute" rule signal_routing.yaml states for sources.
    # `signal_type` distinguishes the two banded instruments. Download bands are per
    # product type, because a dataset's downloads run an order below a package's. The
    # stars band is per INSTRUMENT and type-independent — a star is a star whatever it
    # was given to — so it is emitted once with product_type '*' and is declared on its
    # route in signal_routing.yaml rather than in four rubrics that could drift.
    "adoption_bands": ("product_type", "signal_type", "level", "above", "reach", "unit"),
    "license_aliases": ("source", "license_slug", "license_name"),
    "evidence_abstentions": ("source", "column_name", "abstain_value"),
    "product_openness_evidence": (
        "product_slug",
        "category_slug",
        "dimension",
        "value",
        "value_detail",
        "grade",
        "in_declared_enum",
    ),
    "product_score_sources": (
        "product_slug",
        "category_slug",
        "axis",
        "source_url",
        "source_shows",
        "source_accessed",
        "grade",
        "admitted",
        "reject_reason",
    ),
}


def load_policy(root: Path) -> dict:
    return yaml.safe_load((root / "sources" / "evidence_policy.yaml").read_text()) or {}


def load_routing(root: Path) -> dict:
    return yaml.safe_load((root / "sources" / "signal_routing.yaml").read_text()) or {}


def split_value(raw: str) -> tuple[str, str]:
    """Split a recorded component into its bare value and its trailing detail.

    'open(downloadable on HF, gated)' -> ('open', 'downloadable on HF, gated')
    The bare half matches `check_rubric.head` exactly, which is what the formula
    consumes; the detail half is what a reviewer needs and the formula ignores.
    """
    text = (raw or "").strip()
    parts = re.split(r"[(,]", text, maxsplit=1)
    bare = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""
    return bare, rest.rstrip(")").strip()


def admit(shows: str, policy: dict) -> tuple[bool, str]:
    """Decide whether a recorded source is admissible evidence.

    Rejection is not deletion. The row is still emitted, carrying its reason, so
    that unsourced assertions become a queryable work list instead of quietly
    passing for provenance.
    """
    rules = policy.get("admission") or {}
    text = (shows or "").strip()
    if rules.get("require_nonempty_shows", True) and not text:
        return False, "no `shows` recorded"
    lowered = text.lower()
    for phrase in rules.get("boilerplate_shows") or []:
        if str(phrase).lower() in lowered:
            return False, f"boilerplate `shows`: {phrase!r}"
    return True, ""


def scoring_rules(slug: str, recipe: dict) -> tuple[list[dict], list[str]]:
    """Flatten the ordered formula into one row per condition.

    Long form rather than a column per dimension: dimensions differ by category,
    and a wide table would need reshaping every time a new rubric lands.
    `rule_index` preserves the order, which is load-bearing — the formula is
    first-match-wins, so a reordering silently changes scores.
    """
    rows: list[dict] = []
    errors: list[str] = []
    openness = recipe.get("openness") or {}
    declared = openness.get("dimensions") or {}
    tiers = ((openness.get("license_tier") or {}).get("values") or {}).keys()
    version = recipe.get("version", "")

    for index, rule in enumerate(openness.get("formula") or []):
        if "otherwise" in rule:
            result = rule["otherwise"]
            rows.append(
                {
                    "category_slug": slug,
                    "recipe_version": version,
                    "rule_index": index,
                    "is_otherwise": True,
                    "condition_key": "",
                    "condition_value": "",
                    "then_score": result.get("score", ""),
                    "then_class": result.get("class", ""),
                }
            )
            continue

        when = rule.get("when") or {}
        then = rule.get("then") or {}
        if not when or not then:
            errors.append(f"category '{slug}' formula rule {index} has neither a when/then nor an otherwise")
            continue

        for key, value in when.items():
            # A condition naming a dimension that the rubric never declared, or a
            # tier that its own tier list does not define, cannot ever match. It
            # would not raise; it would just make the rule dead and push products
            # into `otherwise`. That is exactly the failure a checker has to catch.
            if key == "license_tier":
                if value not in tiers:
                    errors.append(
                        f"category '{slug}' rule {index} tests license_tier={value!r}, "
                        f"which is not one of its declared tiers {sorted(tiers)}"
                    )
            elif key not in declared:
                errors.append(
                    f"category '{slug}' rule {index} tests undeclared dimension {key!r}"
                )
            elif value not in (declared[key].get("values") or []):
                errors.append(
                    f"category '{slug}' rule {index} tests {key}={value!r}, which is not in "
                    f"its declared values {declared[key].get('values')}"
                )
            rows.append(
                {
                    "category_slug": slug,
                    "recipe_version": version,
                    "rule_index": index,
                    "is_otherwise": False,
                    "condition_key": key,
                    "condition_value": value,
                    "then_score": then.get("score", ""),
                    "then_class": then.get("class", ""),
                }
            )
    return rows, errors


def license_tiers(slug: str, recipe: dict) -> tuple[list[dict], list[str]]:
    """Emit tier <- example license, carrying the declared restrictiveness rank.

    `tier_rank` is the position of the tier in the recipe's `values` mapping. That
    is only meaningful if the category says its declaration order encodes
    restrictiveness, so `ordered_by` is required whenever there is more than one
    tier to compare. Without it the multi-SKU rule would be resolving "most
    restrictive" against whatever order the YAML happened to be written in.
    """
    rows: list[dict] = []
    errors: list[str] = []
    spec_root = ((recipe.get("openness") or {}).get("license_tier")) or {}
    values = spec_root.get("values") or {}
    if len(values) > 1 and spec_root.get("ordered_by") != "restrictiveness_ascending":
        errors.append(
            f"category '{slug}' declares {len(values)} license tiers but no "
            f"`ordered_by: restrictiveness_ascending`, so the most-restrictive rule "
            f"has no defined ordering to resolve against"
        )
    for rank, (tier, spec) in enumerate(values.items()):
        for example in (spec or {}).get("examples") or []:
            rows.append(
                {
                    "category_slug": slug,
                    "tier": tier,
                    "tier_rank": rank,
                    "example_license": example,
                    "is_definitional": False,
                }
            )
        for token in DEFINITIONAL_TIERS.get(tier, ()):
            rows.append(
                {
                    "category_slug": slug,
                    "tier": tier,
                    "tier_rank": rank,
                    "example_license": token,
                    "is_definitional": True,
                }
            )
    return rows, errors


def stars_bands(routing: dict) -> tuple[list[dict], list[str]]:
    """The stars scale, from the adoption route that produces it.

    Emitted with product_type '*' because it does not vary by type, and capped: a
    stars-derived band may never claim levels 4 or 5, since stars measure attention
    rather than use. The cap is enforced here rather than trusted, so a later edit that
    adds a level-4 stars band fails the serializer instead of quietly publishing one.
    """
    routes = ((routing.get("dimensions") or {}).get("adoption") or {}).get("routes") or []
    rows, warnings = [], []
    for route in routes:
        if route.get("signal_type") != "stars_fallback":
            continue
        cap = route.get("cap")
        for band in route.get("bands") or []:
            if cap is not None and band["level"] > cap:
                warnings.append(
                    f"stars band level {band['level']} exceeds the declared cap {cap}; dropped"
                )
                continue
            rows.append({
                "product_type": "*",
                "signal_type": "stars_fallback",
                "level": band["level"],
                "above": band["above"],
                "reach": str(band.get("reach") or ""),
                "unit": "GitHub stars",
            })
    return rows, warnings


def adoption_bands(shared_rubrics: dict) -> tuple[list[dict], list[str]]:
    """One row per (product type, level), from the shared ladders' `adoption.bands`.

    Keyed on the rubric's filename stem, which IS the product type — `recipe_for` already
    resolves a product to its ladder by `type`, so no second mapping is invented here.
    """
    rows, warnings = [], []
    for product_type, rubric in sorted(shared_rubrics.items()):
        adoption = (rubric or {}).get("adoption")
        if adoption is None:
            warnings.append(f"rubric {product_type!r} declares no adoption bands")
            continue
        bands = adoption.get("bands") or []
        if not bands and not adoption.get("qualitative"):
            warnings.append(f"rubric {product_type!r} declares empty bands but is not qualitative")
        for band in bands:
            rows.append({
                "product_type": product_type,
                "signal_type": "usage_volume",
                "level": band["level"],
                "above": band["above"],
                "reach": str(band.get("reach") or ""),
                "unit": str(adoption.get("unit") or ""),
            })
    return rows, warnings


def category_dimensions(slug: str, recipe: dict) -> list[dict]:
    """The ladder's declared dimensions, with the keys each may be recorded under.

    `reads_keys` and `declared_values` are joined with '|' rather than emitted as one row
    per element: nothing downstream joins on them. They are there so a reader of the
    warehouse can see what vocabulary a dimension accepts without opening the repo, and so
    a value arriving outside its enum can be spotted from the warehouse side too.
    """
    declared = ((recipe.get("openness") or {}).get("dimensions")) or {}
    return [
        {
            "category_slug": slug,
            "dimension": name,
            "reads_keys": "|".join((spec or {}).get("reads") or [name]),
            "declared_values": "|".join((spec or {}).get("values") or []),
        }
        for name, spec in declared.items()
    ]


def license_aliases(routing: dict) -> list[dict]:
    rows: list[dict] = []
    aliases = (((routing.get("dimensions") or {}).get("license") or {}).get("aliases")) or {}
    for source, mapping in aliases.items():
        for slug, name in (mapping or {}).items():
            rows.append({"source": source, "license_slug": str(slug), "license_name": name})
    return rows


def evidence_abstentions(routing: dict) -> list[dict]:
    """Flatten every route's `abstain_values` from signal_routing.yaml.

    Read from the ROUTE rather than from evidence_policy.yaml, because a value that
    means "no answer" is a fact about a source and signal_routing.yaml is what owns
    source semantics. An earlier draft declared GitHub's NOASSERTION in both files,
    which is the drift this bridge exists to prevent.

    These cross the bridge rather than being written into the warehouse SQL for the
    same reason the components parser stays in the repo: one declaration, or they
    diverge. `source` is the route's source name — `huggingface_model`, not
    `huggingface` — so an abstention attached to model licenses cannot be read as
    applying to dataset licenses.
    """
    rows: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for dimension in (routing.get("dimensions") or {}).values():
        if not isinstance(dimension, dict):
            continue
        for route in dimension.get("routes") or []:
            if not isinstance(route, dict):
                continue
            source = route.get("source")
            column = route.get("column")
            if not source or not column:
                continue
            for value in route.get("abstain_values") or []:
                key = (str(source), str(column), str(value))
                # The same source/column pair can be routed by more than one
                # dimension, and the lookup table wants one row per value.
                if key not in seen:
                    seen.add(key)
                    rows.append(
                        {"source": source, "column_name": column, "abstain_value": str(value)}
                    )
    return rows


def build_rubric(sources: dict, policy: dict, routing: dict) -> tuple[dict[str, list[dict]], list[str], list[str]]:
    """Return (tables, errors, warnings).

    Errors are things that would make scoring wrong rather than merely incomplete:
    a malformed rule, or a rule that can never match. Warnings are coverage and
    data-quality facts — a category with no rubric yet, a recorded value outside
    its own declared enum, a source that cites nothing.
    """
    categories: dict = sources["categories"]
    scores: dict = sources.get("scores") or {}
    # Shared ladders arrive through `sources` rather than being read here, so build_rubric
    # stays a pure function of its inputs and the tests can pass a recipe inline.
    shared_rubrics: dict = sources.get("rubrics") or {}

    tables: dict[str, list[dict]] = {name: [] for name in TABLES}
    errors: list[str] = []
    warnings: list[str] = []

    tables["adoption_bands"], band_warnings = adoption_bands(shared_rubrics)
    warnings.extend(band_warnings)
    star_rows, star_warnings = stars_bands(routing)
    tables["adoption_bands"].extend(star_rows)
    warnings.extend(star_warnings)
    tables["license_aliases"] = license_aliases(routing)
    tables["evidence_abstentions"] = evidence_abstentions(routing)
    if not tables["evidence_abstentions"]:
        warnings.append("signal_routing.yaml declares no route abstain_values")

    # Slug -> declared `type`, threaded through `sources` rather than read here so
    # `build_rubric` stays a pure function of its inputs (see `test_rubric_rows_carry_product_type`).
    product_types: dict[str, str] = sources.get("product_types") or {}

    scored_categories = 0
    for slug, category in sorted(categories.items()):
        variants, recipe_errors = resolve_recipe_variants(category, shared_rubrics)
        errors.extend(f"category '{slug}' {e}" for e in recipe_errors)
        if not variants:
            if not recipe_errors:
                warnings.append(f"category '{slug}' declares no scoring_recipe")
            continue
        scored_categories += 1

        # Deferrals are a property of the category's declaration, not of any one
        # resolved ladder variant, so they are read off `scoring_recipe` directly
        # rather than through `resolve_recipe` — the same source `check_rubric.py`'s
        # `check_category` reads (build/check_rubric.py:240).
        deferred = (category.get("scoring_recipe") or {}).get("deferred") or {}

        # Emitted from the declaration rather than from inside the products loop below,
        # which only reaches products that have a `sources/scores/` file. The evidence
        # store's roster is `product_categories`, so a deferred product with no score file
        # still arrives in the warehouse carrying hub-derived dataset rows, and the filter
        # that has to stop it needs a row here regardless.
        for product_slug, spec in sorted(deferred.items()):
            because = (spec or {}).get("because", "")
            tables["category_deferrals"].append(
                {
                    "category_slug": slug,
                    "product_slug": product_slug,
                    "because": " ".join(str(because).split()),
                }
            )

        for product_type, variant_recipe in sorted(variants.items()):
            rules, rule_errors = scoring_rules(slug, variant_recipe)
            for row in rules:
                row["product_type"] = product_type
            tables["category_scoring_rules"].extend(rules)
            errors.extend(rule_errors)

            tier_rows, tier_errors = license_tiers(slug, variant_recipe)
            for row in tier_rows:
                row["product_type"] = product_type
            tables["category_license_tiers"].extend(tier_rows)
            errors.extend(tier_errors)

            dimension_rows = category_dimensions(slug, variant_recipe)
            for row in dimension_rows:
                row["product_type"] = product_type
            tables["category_dimensions"].extend(dimension_rows)
            if not dimension_rows:
                errors.append(
                    f"category '{slug}' ladder for product type '{product_type}' declares no "
                    f"openness dimensions, so nothing it scores can be traced to a fact"
                )

        for product_slug in category.get("products") or []:
            record = scores.get(product_slug)
            if record is None:
                continue
            # A missing/unmapped product type only forfeits the recipe-dependent
            # openness evidence below — it says nothing about whether adoption and
            # capability sources exist, so it must not skip the axis-source loop
            # that runs unconditionally after this block (see
            # test_recipe_miss_still_emits_score_sources_for_other_axes).
            recipe, why = recipe_for(variants, product_types.get(product_slug, ""))
            if product_slug in deferred:
                # `openness_computed` builds its roster with SELECT DISTINCT product_slug,
                # category_slug FROM product_evidence, so any row emitted here is enough for
                # that downstream model to compute a score. `deferred` means the repo has
                # declared it will NOT stand behind the ladder reproducing this product's
                # recorded score, so no openness evidence goes out and no score is ever
                # computed for it — the safe silence, instead of a computed score nobody
                # signed off on.
                pass
            elif recipe is None:
                warnings.append(f"product '{product_slug}' in '{slug}': {why}")
            else:
                declared = ((recipe.get("openness") or {}).get("dimensions")) or {}

                openness = record.get("openness") or {}
                components = split_components(openness.get("components") or "")
                if not components:
                    warnings.append(
                        f"product '{product_slug}' in '{slug}' records no openness components"
                    )

                read_map = dimension_read_map(recipe)
                license_keys = license_read_keys(recipe)

                # One row per DECLARED DIMENSION, carrying the value the formula will
                # actually read. Emitted under the dimension name rather than the key it
                # was recorded under, because the warehouse joins a rule's condition_key
                # against this column: a row labeled `post-training-data` would leave the
                # `data` condition unmatched and drop the product into `otherwise`
                # silently, scoring it 3 on an absence.
                resolved_keys: dict[str, str] = {}
                for dimension, spec in declared.items():
                    key = resolve_dimension(components, dimension, recipe)
                    if key is None:
                        continue
                    resolved_keys[dimension] = key
                    bare, detail = split_value(components[key])
                    allowed = (spec or {}).get("values")
                    in_enum = bare in allowed if allowed else ""
                    if in_enum is False:
                        warnings.append(
                            f"product '{product_slug}' records {key}={bare!r}, which is not in "
                            f"the rubric's declared values for {dimension} {allowed}"
                        )
                    tables["product_openness_evidence"].append(
                        {
                            "product_slug": product_slug,
                            "category_slug": slug,
                            "dimension": dimension,
                            "value": bare,
                            "value_detail": detail,
                            "grade": "document",
                            "in_declared_enum": in_enum,
                        }
                    )

                # The license the tier lookup consumes, emitted under the name the
                # warehouse joins on. `license_tier.reads` lets a category accept the value
                # under another key - deepseek-coder records `model-license`, because its card
                # distinguishes the code license from the one on the weights - and
                # check_rubric honors that list. Without resolving it here the row went out
                # as `model-license`, the SQL looked only for `license`, and the product
                # abstained in the warehouse while reproducing locally. Same drift as the
                # dimension resolution above, one key over.
                license_key = next((k for k in license_keys if components.get(k)), None)
                if license_key:
                    bare, detail = split_value(components[license_key])
                    tables["product_openness_evidence"].append(
                        {
                            "product_slug": product_slug,
                            "category_slug": slug,
                            "dimension": "license",
                            "value": bare,
                            "value_detail": detail,
                            "grade": "document",
                            # No enum: `license` is the raw input the tier lookup consumes.
                            "in_declared_enum": "",
                        }
                    )

                # Then every recorded key that is not itself a dimension name, so nothing
                # the repo recorded is dropped. This carries the license the tier lookup
                # consumes, and the losing side of a `reads` preference — granite records
                # both a base corpus and an SFT mixture, and only one of them answers the
                # category's data question.
                #
                # Keys that ARE dimension names are skipped here because the resolved pass
                # above already emitted them. Emitting both would put two values on one
                # grain and let the warehouse pick between them by row order.
                for key, raw in components.items():
                    if key == "license":
                        continue  # emitted above, under the resolved license row
                    if key in declared:
                        # A key that shares a dimension's name but lost the `reads`
                        # preference is answering a different question under a name this
                        # category has already spent. granite records
                        # `data:described_not_released` about its BASE corpus while
                        # `post-training-data` answers the category's data question, so the
                        # base fact has nowhere to go and would be dropped without a word.
                        # Reported so it can be relabeled — starcoder2 already uses
                        # `base-data` for exactly this.
                        if resolved_keys.get(key) != key:
                            warnings.append(
                                f"product '{product_slug}' records {key}={split_value(raw)[0]!r}, but "
                                f"'{slug}' resolved {key} from {resolved_keys.get(key)!r} instead, so "
                                f"the recorded value is dropped from the evidence store. Relabel it if "
                                f"it answers a different question."
                            )
                        continue
                    bare, detail = split_value(raw)
                    # A component no dimension declares and no `reads` list names is
                    # vocabulary drift. It cannot affect a score, so it is a curation
                    # finding rather than a failure — but left unreported it is an
                    # observation nobody will ever act on. `marin` records
                    # `reproducibility:bit-for-bit`, a real openness fact the rubric has
                    # no question for.
                    if key not in license_keys and key not in read_map:
                        warnings.append(
                            f"product '{product_slug}' records {key!r}, which "
                            f"'{slug}' does not declare as a dimension"
                        )
                    tables["product_openness_evidence"].append(
                        {
                            "product_slug": product_slug,
                            "category_slug": slug,
                            "dimension": key,
                            "value": bare,
                            "value_detail": detail,
                            "grade": "document",
                            # A traceability row, not the value any rule reads. Left blank
                            # rather than validated, since the enum it would be checked
                            # against belongs to the dimension that won.
                            "in_declared_enum": "",
                        }
                    )

            rejected = 0
            for axis in AXES:
                for source in (record.get(axis) or {}).get("sources") or []:
                    if not isinstance(source, dict):
                        continue
                    shows = source.get("shows") or ""
                    admitted, reason = admit(shows, policy)
                    rejected += 0 if admitted else 1
                    accessed = source.get("accessed")
                    tables["product_score_sources"].append(
                        {
                            "product_slug": product_slug,
                            "category_slug": slug,
                            "axis": axis,
                            "source_url": source.get("url", ""),
                            "source_shows": shows,
                            "source_accessed": str(accessed) if accessed else "",
                            "grade": "document",
                            "admitted": admitted,
                            "reject_reason": reason,
                        }
                    )
            if rejected:
                warnings.append(
                    f"product '{product_slug}': {rejected} source row(s) cite nothing specific"
                )

    if scored_categories == 0:
        errors.append("no category declares a scoring_recipe, so there is nothing to score with")

    return tables, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate only, write nothing")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="output directory")
    parser.add_argument("--verbose", action="store_true", help="print every warning")
    args = parser.parse_args()

    sources = load_sources(ROOT)
    sources["product_types"] = load_product_types(ROOT)
    tables, errors, warnings = build_rubric(sources, load_policy(ROOT), load_routing(ROOT))

    for name in TABLES:
        print(f"  {name:<27} {len(tables[name]):>5} rows")

    admitted = sum(1 for r in tables["product_score_sources"] if r["admitted"])
    total_sources = len(tables["product_score_sources"])
    if total_sources:
        print(
            f"\n  admissible sources: {admitted}/{total_sources} "
            f"({admitted / total_sources:.0%}); {total_sources - admitted} cite nothing specific"
        )

    if warnings:
        print(f"\n{len(warnings)} warning(s) — coverage and data quality, nothing broken")
        shown = warnings if args.verbose else warnings[:8]
        for warning in shown:
            print(f"  - {warning}")
        if len(shown) < len(warnings):
            print(f"  ... {len(warnings) - len(shown)} more (--verbose)")

    if errors:
        print(f"\n{len(errors)} error(s) — these would make scoring wrong:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.check:
        print("\ncheck only: nothing written")
        return 0

    write_tables(tables, args.out, TABLES)
    print(f"\nwrote {len(TABLES)} CSVs to {args.out.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
