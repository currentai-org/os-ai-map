"""The open / open-ish / closed bucket boundary, and the license line underneath it.

Two invariants live here, and neither has a natural home in the serializer tests because
both span files that do not import each other.

The first is that the three copies of the bucket map agree. `docs/openness-class-map.json`
is source of truth and says so; `build/serialize.py` and `build/render.py` each keep an
inline copy for self-containment. Three copies of one fact drift, and the drift would be
silent - the gap stage numbers and the notebook's verdict chips would simply disagree.

The second is the one that matters, and it is the one that was broken. A class in the `open`
bucket may only be reached through a license tier that is open by an external standard: OSI
approval for code and weights, the Open Definition for data. `render.py` calls this boundary
a "strict OSI/MOF cut". Two rungs in `software.yaml` used to emit `open_core` and
`open_source` from `permissive_non_osi`, which is neither, and they went unnoticed because
this tier's `examples` list is empty so the rungs could never fire. Assigning one license to
that tier would have activated a 5/open_source rung for a non-OSI license.

The external standards this encodes:
  - Model Openness Framework (arXiv 2403.13784): releases under a license that imposes
    downstream restrictions are source-available, not open. It names OpenRAIL, the Llama 2
    license and AI2 ImpACT as not open-source licenses.
  - OSAID 1.0: requires the freedom to use the system "for any purpose", so a field-of-use
    or commercial restriction disqualifies.

Both are binary. The map is a 0-5 score, which is a different instrument, and the way the
two stay compatible is precisely this: the score may subdivide the region BELOW the binary
line as finely as it likes, but nothing below the line may enter the `open` bucket.
"""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# The license tiers that are open by an external standard, per ladder. Everything else is
# below the MOF/OSAID line. Kept as a literal rather than derived from tier_rank 0, because
# "the first tier declared" is a fact about YAML ordering and "OSI-approved" is a fact about
# the license - deriving one from the other is how this test would stop testing anything.
OPEN_BY_EXTERNAL_STANDARD = {"osi", "open_data"}

# Known violations, kept explicit so they fail loudly in review rather than quietly in CI.
# Keyed by (ladder, license_tier, emitted class) rather than by rule index, so reordering a
# formula does not silently move an exemption onto a different rung.
#
# Both entries are the same defect and it is NOT license laxity: the dataset class vocabulary
# in build/validate.py is {open, gated, restricted, closed}, and `open` is the only word
# available above `gated`. So a corpus whose license defers to per-subset terms has nowhere to
# land but `open`, and `open` is in the open bucket. `the-pile` (3/open, mixed-per-subset,
# Books3 withdrawn) and `stack-edu` (4/open, defers to The Stack v2's gated terms) are the two
# products, and the ladder emits these pairs only because the recorded scores do. The
# producible-pair check requires that some rule in the recipe be able to emit every recorded
# pair.
#
# The bucket count does not depend on the ladder: build/serialize.py buckets the RECORDED
# class, so both products already counted as open before any recipe existed. All 51 dataset
# products classed open count as open today, where a model at 4 is open_weights and
# open-ish. Closing it means giving the dataset vocabulary a middle class and re-scoring two
# products, which is a score change and therefore not this test's business to force.
KNOWN_VIOLATIONS = frozenset(
    {
        ("rubrics/dataset", "deferred_to_components", "open"),
    }
)


def _bucket_map():
    return json.loads((ROOT / "docs" / "openness-class-map.json").read_text())


def _inline_set(module_path: str, name: str) -> set[str]:
    """The inline bucket copy from a build module, read as source text.

    Read textually rather than imported: `render.py` defines its copy inside a function,
    so there is nothing importable to compare against.
    """
    text = (ROOT / module_path).read_text()
    marker = f"{name} = {{"
    start = text.index(marker) + len(marker)
    body = text[start : text.index("}", start)]
    return {part.strip().strip("\"'") for part in body.split(",") if part.strip()}


def test_the_three_copies_of_the_bucket_map_agree():
    buckets = _bucket_map()["buckets"]
    canonical_open = set(buckets["open"]["classes"])
    canonical_openish = set(buckets["openish"]["classes"])

    assert _inline_set("build/serialize.py", "_GAP_OPEN") == canonical_open
    assert _inline_set("build/serialize.py", "_GAP_OPENISH") == canonical_openish
    assert _inline_set("build/render.py", "_OPEN") == canonical_open
    assert _inline_set("build/render.py", "_OPENISH") == canonical_openish


def test_every_class_in_a_bucket_is_a_declared_class():
    data = _bucket_map()
    declared = set(data["classes"])
    for name, spec in data["buckets"].items():
        unknown = set(spec["classes"]) - declared
        assert not unknown, f"bucket {name!r} lists undeclared classes {sorted(unknown)}"


def _ladders():
    """Every recipe that carries a formula: the shared ladders and the own-ladder categories."""
    for path in sorted((ROOT / "sources" / "rubrics").glob("*.yaml")):
        yield f"rubrics/{path.stem}", yaml.safe_load(path.read_text())
    for path in sorted((ROOT / "sources" / "categories").glob("*.yaml")):
        recipe = (yaml.safe_load(path.read_text()) or {}).get("scoring_recipe") or {}
        if "openness" in recipe:
            yield f"categories/{path.stem}", recipe


def test_no_rung_reaches_the_open_bucket_from_a_restricted_license():
    """The strict OSI/MOF cut, enforced.

    A rung emitting an `open`-bucket class must either test a license tier that is open by
    an external standard, or test no license tier at all - the latter being how the hardware
    ladder works, which has no license dimension by design.
    """
    open_classes = set(_bucket_map()["buckets"]["open"]["classes"])
    offences, exercised = [], set()
    for name, recipe in _ladders():
        for index, rule in enumerate((recipe.get("openness") or {}).get("formula") or []):
            outcome = rule.get("then") or rule.get("otherwise") or {}
            if outcome.get("class") not in open_classes:
                continue
            tier = (rule.get("when") or {}).get("license_tier")
            if tier is None or tier in OPEN_BY_EXTERNAL_STANDARD:
                continue
            key = (name, tier, outcome.get("class"))
            if key in KNOWN_VIOLATIONS:
                exercised.add(key)
                continue
            offences.append(
                f"{name} rule {index} emits {outcome.get('score')}/"
                f"{outcome.get('class')} (open bucket) from license_tier={tier!r}"
            )
    assert not offences, "\n".join(offences)

    # An exemption nobody needs is a dead rule by another name. When the dataset vocabulary
    # gains a middle class, this is what tells us to delete the entry rather than leaving it
    # to bless a future violation.
    stale = KNOWN_VIOLATIONS - exercised
    assert not stale, f"KNOWN_VIOLATIONS entries no longer violate anything: {sorted(stale)}"


def test_an_otherwise_rule_never_lands_in_the_open_bucket():
    """`otherwise` tests no license tier, so it cannot establish one.

    model.yaml's `otherwise` settles on 3/open_weights, which is open-ish. A ladder whose
    fallthrough reached the open bucket would put every product with unrecorded evidence
    into the headline open count.
    """
    open_classes = set(_bucket_map()["buckets"]["open"]["classes"])
    for name, recipe in _ladders():
        for rule in (recipe.get("openness") or {}).get("formula") or []:
            if "otherwise" not in rule:
                continue
            got = rule["otherwise"].get("class")
            assert got not in open_classes, (
                f"{name} falls through to {got!r}, which is in the open bucket"
            )


def test_validate_vocabulary_is_a_subset_of_the_schema_enum():
    """Every class build/validate.py permits must be one the schema allows.

    These drifted: validate.py permitted `documented_only` for datasets while the schema
    enum omitted it, so a dataset scored that way passed one check and failed the other
    depending on order. No product ever carried it.
    """
    schema = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
    allowed = set(schema["properties"]["openness"]["properties"]["class"]["enum"])

    from build.validate import OPENNESS_CLASSES

    permitted = {cls for classes in OPENNESS_CLASSES.values() for cls in classes}
    assert permitted <= allowed, f"validate.py permits classes the schema forbids: {sorted(permitted - allowed)}"
