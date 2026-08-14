"""Does every recorded adoption band match the scale its own rubric declares?

## Why this gate did not exist, and why that is the interesting part

`adoption_bands` are declared per product type in `sources/rubrics/*.yaml`, serialized into
`currentai.registry.adoption_bands` by `build/serialize_rubric.py`, and read by the scoring
SQL. Tests cover the declaration's shape and the serializer's output. Nothing has ever
compared a PRODUCT's recorded `(level, reach)` against them.

So the bands were authoritative for the warehouse and advisory for the corpus, and the two
drifted in exactly the way `check_parity` exists to catch one axis over. 93 of 472 products
record a `reach` label that is not a band their own product type declares.

The dataset scale is the clearest case. It sits one order of magnitude below software and
model — deliberately, and measured: across 66 Hugging Face dataset artifacts, the median was
27,648 downloads and NONE exceeded 10M, so on the software scale level 5 is unreachable. Its
top band is therefore `>1M`. Thirteen benchmark corpora nonetheless record `1M-10M` or `>10M`,
which are labels off the software scale, and `mmlu` recorded level 5 against 477,890 monthly
downloads — a level the dataset scale reserves for figures its own note does not claim.

`dataset.yaml` predicted this in a comment: "14 dataset products record level 4 against a
reach of 1M-10M, which is level 5 on this scale ... They are a work list, not a migration."
The work list was written down and never turned into a check, so it grew.

## What is checked

1. **The reach label is one the applicable scale declares.** Catches the wrong scale being
   used for a type, case drift (`10k-100k` for `10K-100K`), and free text (`niche`,
   `~1.4M/mo`) that carries a figure but not a band.
2. **The recorded level is the level that label denotes.** Catches the internally
   inconsistent pair — level 5 against a `100K-1M` reach — which no band can produce and
   which the warehouse would compute differently.

Which scale applies is keyed on `(product_type, signal_type)`, not type alone, because
`stars_fallback` has its own labels and its own ceiling: stars cap adoption at level 3, since
a star is not a use. `validate.py` already enforces that ceiling; this checks the label too.

## What is deliberately NOT checked

Whether the recorded figure is CURRENT. That needs a fetch, and it is `check_freshness`'s
question. A product can be perfectly banded against a figure from March.

## Exit status

0 unless `--strict`. CI runs `--strict` as of 2026-08-13; the flag stays optional so a local
run can survey without failing.

It shipped non-strict on 2026-08-11 against 217 off-scale records, because a gate that fails on
day one teaches people to skip it. That backlog is now zero — 217 to 71 across #224 to #230,
then 71 to 0 by declaring the two instruments that had no vocabulary at all and re-reading every
remaining figure live rather than inferring it from the stale text of the label being replaced.

**The escape hatch is to declare a band, never to edit a level until CI passes.** A record that
needs a label no scale offers IS the finding: `character-ai` invented `10M-100M`, and because
nothing could check an undeclared label, it sat at level 4 while its own cited ~20M MAU cleared
the top threshold outright.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]


def declared_scales(sources: dict) -> dict[tuple[str, str], dict[str, int]]:
    """(product_type, signal_type) -> {reach label: level}.

    A `*` product type means the scale applies to every type, which is how the stars
    fallback is declared: it is a property of the SIGNAL, not of the thing measured.
    """
    scales: dict[tuple[str, str], dict[str, int]] = {}
    for name, rubric in (sources.get("rubrics") or {}).items():
        adoption = (rubric or {}).get("adoption") or {}
        for band in adoption.get("bands") or []:
            scales.setdefault((name, "*"), {})[band["reach"]] = band["level"]

    # Two scales live in signal_routing.yaml rather than a rubric, because they are a
    # property of the SIGNAL and apply to every product type: `stars_fallback`, and
    # `active_users` since 2026-08-13. Read through the serializer's own loader so the two
    # cannot disagree about where they live.
    from build.serialize_rubric import load_routing, route_bands

    rows, _warnings = route_bands(load_routing(ROOT))
    for band in rows:
        scales.setdefault(("*", band["signal_type"]), {})[band["reach"]] = band["level"]
    return scales


def declared_vocabularies(root: Path = ROOT) -> dict[str, set[str]]:
    """signal_type -> the words it may record as `reach`, for instruments with no bands.

    A VOCABULARY is not a scale, and the difference is the point. A scale maps a label to a
    level and a mismatch between them is a finding. A vocabulary says only which words exist:
    `reported_traction` records what KIND of standing was claimed, while the level says how
    much, and the two are allowed to disagree because neither is derived from the other.

    Measured 2026-08-13 on the 110 records carrying `reported_traction`: `niche` ran 85%
    level 3, `broad` 80% level 4, `mass-market` 67% level 5. Forcing agreement would flatten
    the residual signal those spreads represent, so this check asserts membership only.
    """
    from build.serialize_rubric import load_routing

    routing = load_routing(root)
    routes = ((routing.get("dimensions") or {}).get("adoption") or {}).get("routes") or []
    return {
        route["signal_type"]: set(route["vocabulary"])
        for route in routes
        if route.get("signal_type") and route.get("vocabulary")
    }


# Instruments whose bands are read in downloads, and which may therefore fall back to the
# product type's declared download scale. Everything else measures something else entirely.
#
# `unknown` is absent deliberately: it means nobody has decided which instrument applies, so
# there is no scale to check against and no basis for guessing one.
_DOWNLOAD_INSTRUMENTS = {"usage_volume", ""}


def scale_for(scales: dict, product_type: str, signal_type: str) -> dict[str, int] | None:
    """The scale that applies, or None when the instrument declares none.

    ABSTAIN RATHER THAN SUBSTITUTE. `sources/signal_routing.yaml` states the rule directly:
    "When the authoritative signal for a dimension is missing or unusable, the rule is to
    produce NO evidence. Falling through to a less authoritative signal is how the failure
    above happens." `docs/reference/adoption.md` says the same thing about this exact check —
    "a `reported_traction` or `active_users` band is measuring something else entirely.
    Comparing it against a download count is a category error, and a check must SKIP it
    rather than flag or waive it."

    The first version of this function did exactly that, and it is worth recording why the
    bug was invisible: it read `if the signal declares its own scale use it, otherwise use
    the product type's`, which is correct for `stars_fallback` and for `usage_volume` and
    silently wrong for the two instruments that have no scale at all. It manufactured a
    download-scale finding for all 93 `reported_traction` products and every `active_users`
    one, and those findings looked exactly like the real ones.

    So the fallback is now allowed only for instruments actually denominated in downloads.
    `reported_traction` returns None and is skipped, which is not a waiver — it is the
    checker declining to compare a user count against a download band.

    `active_users` no longer needs the skip. It DECLARES a scale as of 2026-08-13, so it
    takes the first branch like stars do, and abstention narrows to the one instrument that
    still has no vocabulary. Note what the skip had been hiding while it was right: 22 of
    the 23 products were wearing download labels, and skipping them is what made that
    invisible for as long as it was.
    """
    if signal_type and ("*", signal_type) in scales:
        return scales[("*", signal_type)]
    if signal_type not in _DOWNLOAD_INSTRUMENTS:
        return None
    return scales.get((product_type, "*"))


def collect(sources: dict) -> tuple[list[str], int]:
    scales = declared_scales(sources)
    vocabularies = declared_vocabularies()
    types = {slug: (doc or {}).get("type") for slug, doc in sources["products"].items()}

    findings: list[str] = []
    examined = 0
    for slug, score in sorted(sources["scores"].items()):
        adoption = (score or {}).get("adoption") or {}
        level, reach = adoption.get("level"), adoption.get("reach")
        if level is None and reach is None:
            continue
        signal = adoption.get("signal_type") or ""

        # An instrument with a vocabulary rather than bands. `reach` is optional here —
        # omitting it is the honest default and 15 records already do — so the only thing
        # to check is that a word, if present, is one the instrument declares. Crucially
        # this is where a NUMERIC label gets caught: `100K-1M` is not in the vocabulary, and
        # on an instrument defined by having nothing to count it is a measurement claim the
        # instrument cannot make.
        if signal in vocabularies:
            examined += 1
            if reach is not None and reach not in vocabularies[signal]:
                findings.append(
                    f"{slug} [{types.get(slug)}/{signal}]: reach {reach!r} is not in this "
                    f"instrument's vocabulary {sorted(vocabularies[signal])}; a "
                    f"{signal} record has no count behind it, so a numeric band claims a "
                    f"measurement that was never made"
                )
            continue

        scale = scale_for(scales, types.get(slug), signal)
        if scale is None:
            continue  # hardware declares no adoption scale, by design
        examined += 1

        if reach is None:
            findings.append(f"{slug}: level {level} with no reach label to justify it")
            continue
        if reach not in scale:
            findings.append(
                f"{slug} [{types.get(slug)}/{signal or 'no signal_type'}]: reach {reach!r} is not a "
                f"declared band; this scale offers {sorted(scale)}"
            )
            continue
        if level != scale[reach]:
            findings.append(
                f"{slug} [{types.get(slug)}/{signal or 'no signal_type'}]: records level {level} "
                f"against reach {reach!r}, which this scale puts at level {scale[reach]}"
            )
    return findings, examined


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 if anything is off-scale")
    args = parser.parse_args()

    sources = load_sources(ROOT)
    findings, examined = collect(sources)

    # A corpus walk that silently narrows passes green. Two did, earlier in this repo.
    if examined < 300:
        print(f"check_adoption: only examined {examined} products; the walk has drifted", file=sys.stderr)
        return 1

    for line in findings:
        print(f"  x {line}")
    status = "OK" if not findings else f"{len(findings)} off-scale"
    print(f"\ncheck_adoption  {examined} products with an adoption band  [{status}]")

    return 1 if findings and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
