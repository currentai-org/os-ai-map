"""Gate the serialized payload's identity invariants.

build/validate.py covers the source YAML. This covers the artifact the app consumes, which
is a different thing: a serializer bug can produce a valid source tree and a payload the
app cannot build pages from.

Every branch below either confirms one invariant or refuses to judge the payload -- a
missing top-level block, `None` where a dict belongs, an empty product set, or a malformed
row must never read as "fine". A gate that goes green when it cannot understand its input
is worse than no gate at all: it looks like protection nobody is actually getting.

One numeric invariant sits here too, because the payload is the only place both halves of it
appear: a depth-ladder row's per-language bands must reproduce the set band beside them
(`_check_depth_languages`). That check also reads the set's target-language roster from
`sources/` through the ladder, because `pivot_languages` does not ship in the payload.
"""
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

from build.depth_ladder import band_from_languages, per_language, set_targets
from build.vocabulary import axes, is_iso_date

# The same regex as the `pattern` on every URL field in docs/schemas/ (#525): an http(s)
# scheme, a dotted hostname of label characters, an optional port, then a path, query,
# fragment or the end. Kept character-identical so a URL the schema rejects (`https://?a.b`,
# where the only dot is in the query) cannot slip through here on a looser reading.
_URL_WITH_HOST = re.compile(r"^https?://[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+(:[0-9]+)?([/?#]|$)")

ROOT = Path(__file__).resolve().parents[1]

_ALIAS_KINDS = ("products", "organizations")
_AXES = axes()  # build/vocabulary.py owns this; the score schema declares it


def _check_freshness_caveats(slug: str, fresh: dict) -> None:
    """Gate the SHAPE of a partial freshness record, not just its presence.

    The defect this whole mechanism exists for was a lossy reduction that no payload gate
    could see. Adding `partial` without gating it would leave exactly that hole open one
    shape over: `{"date": ..., "basis": "partial"}` with nothing saying what is partial is
    strictly worse than `verified`, because it advertises a caveat and then withholds it.
    """
    basis = fresh.get("basis")
    unconfirmed = fresh.get("unconfirmed_axes")
    holds = fresh.get("verification_holds")

    if basis == "partial" and not unconfirmed:
        raise PayloadError(
            f"{slug!r} is basis 'partial' with no unconfirmed_axes — a caveat that does not "
            "say what it is about"
        )
    if basis == "verified" and (unconfirmed or holds):
        raise PayloadError(
            f"{slug!r} is basis 'verified' but carries {'unconfirmed_axes' if unconfirmed else 'verification_holds'}; "
            "an axis cannot be both confirmed and outstanding"
        )

    if unconfirmed is not None:
        if not isinstance(unconfirmed, list) or not unconfirmed:
            raise PayloadError(f"{slug!r} has a non-list or empty unconfirmed_axes")
        if len(set(unconfirmed)) != len(unconfirmed):
            raise PayloadError(f"{slug!r} repeats an axis in unconfirmed_axes: {unconfirmed}")
        unknown = [a for a in unconfirmed if a not in _AXES]
        if unknown:
            raise PayloadError(f"{slug!r} names unknown axes in unconfirmed_axes: {unknown}")

    if holds is not None:
        if not isinstance(holds, list) or not holds:
            raise PayloadError(f"{slug!r} has a non-list or empty verification_holds")
        for hold in holds:
            axis = (hold or {}).get("axis")
            if axis not in _AXES:
                raise PayloadError(f"{slug!r} has a hold on unknown axis {axis!r}")
            # A hold explains an axis that is outstanding. One on a confirmed axis is a
            # contradiction, and it is how a stale queue entry would reach the page.
            if axis not in (unconfirmed or []):
                raise PayloadError(
                    f"{slug!r} holds axis {axis!r} which is not in unconfirmed_axes"
                )
            if not is_iso_date(hold.get("since")):
                raise PayloadError(f"{slug!r} hold on {axis!r} has no valid `since` date")
            if not str(hold.get("reason", "")).strip():
                raise PayloadError(f"{slug!r} hold on {axis!r} has no reason")


_FRESHNESS_BASES = {"verified", "partial", "commit"}


class PayloadError(RuntimeError):
    pass


def _require_dict(payload: dict, key: str) -> dict:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise PayloadError(
            f"payload has no usable {key!r} block (got {type(value).__name__})"
        )
    return value


def _check_identity_attributes(slug: str, row: dict, orgs: dict) -> None:
    """`steward` and `languages` are optional, and when present must be readable as declared.

    A steward is an organization slug, a string. `languages` is a non-empty sorted list of
    three-letter lowercase codes. Their VALUES are gated at the source by `build/validate.py`
    against the ISO snapshots; this checks only that the payload did not carry a shape a
    consumer would have to guess at. A steward must resolve inside the payload's `organizations`
    block, which serialize extends to every steward of a published product, because the point of
    naming an org rather than writing free text is that the steward's type and country come with it.
    """
    if "steward" in row and not (isinstance(row["steward"], str) and row["steward"]):
        raise PayloadError(f"{slug!r} has a steward that is not an organization slug: {row['steward']!r}")
    if "steward" in row and row["steward"] not in orgs:
        raise PayloadError(f"{slug!r} names steward {row['steward']!r}, which has no entry in organizations")
    if "languages" in row:
        languages = row["languages"]
        if not (isinstance(languages, list) and languages
                and all(isinstance(c, str) and len(c) == 3 and c.islower() and c.isalpha() for c in languages)
                and languages == sorted(set(languages))):
            raise PayloadError(f"{slug!r} has languages that are not a sorted list of ISO 639-3 codes: {languages!r}")


def _check_end_of_life(slug: str, eol: object) -> None:
    """Gate the shape of a declared end-of-life record.

    The field says a product still works and stops on a stated day, and the payload is where a
    reader meets that claim. A row carrying `end_of_life` that the app cannot read -- a bare
    string where the object belongs, a date in some other notation, a source that is not a
    link -- would render as nothing at all, which is the one outcome worse than never declaring
    it: the map would look like it had checked and found no sunset. So an unreadable record
    fails here rather than being skipped.
    """
    if not isinstance(eol, dict):
        raise PayloadError(
            f"{slug!r} has an end_of_life that is not an object (got {type(eol).__name__})"
        )
    date = eol.get("date")
    if not is_iso_date(date):
        raise PayloadError(f"{slug!r} has an end_of_life date that is not ISO 8601: {date!r}")
    source = eol.get("source")
    if not isinstance(source, str) or not _URL_WITH_HOST.match(source):
        raise PayloadError(
            f"{slug!r} declares an end_of_life with no usable source URL: {source!r}"
        )


# An unmeasured target language exactly as the ladder publishes it, taken from the ladder rather
# than restated: `band: null` and every other figure empty. Compared by value, so a `0`, an `""`
# or a missing `tasks` list is a filled figure and not a quiet stand-in for "unmeasured".
_UNMEASURED = per_language(["und"], {})["und"]
_LANGUAGE_FIGURES = tuple(_UNMEASURED)


def _is_band(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 5


def _check_depth_languages(slug: str, capability: dict, targets: Callable[[str], list[str]]) -> None:
    """A depth-ladder row's per-language bands must reproduce the band it publishes (#953).

    `capability.depth.per_language` carries one entry per target language, an unmeasured one as
    `band: null` with every other figure empty. Its keys must be the set's target-language roster
    as the ladder derives it (`targets`, by default `depth_ladder.set_targets`), not merely the
    right number of well-shaped codes. A measured language's companion figures must sit in the
    order the ladder builds them: the corroborated band never above the face value, and a numeric
    best original band never above the corroborated band. Read the way `set_band` reads them,
    measured bands as they are and unmeasured languages at 0 and at 5, they must give back
    `capability.score` exactly, and their counts must be the `completeness` the row states. A
    per-language table that disagrees with the band beside it would let the map show one number
    and explain it with another, so it fails here.
    """
    depth = capability.get("depth")
    if not isinstance(depth, dict):
        raise PayloadError(f"{slug!r} has a capability.depth that is not an object")
    languages = depth.get("per_language")
    if not isinstance(languages, dict):
        raise PayloadError(f"{slug!r} has a depth block with no per_language mapping")
    for code, entry in languages.items():
        if not (isinstance(code, str) and len(code) == 3 and code.islower() and code.isalpha()):
            raise PayloadError(f"{slug!r} has a per_language key that is not an ISO 639-3 code: {code!r}")
        if not isinstance(entry, dict) or set(entry) != set(_LANGUAGE_FIGURES):
            raise PayloadError(f"{slug!r} per_language {code!r} does not carry exactly "
                               f"{', '.join(_LANGUAGE_FIGURES)}")
        band = entry["band"]
        if band is None:
            if entry != _UNMEASURED:
                raise PayloadError(f"{slug!r} per_language {code!r} is unmeasured but fills a figure: "
                                   f"{entry!r}; an unmeasured language is exactly {_UNMEASURED!r}")
            continue
        best = entry["best_original"]
        if not (_is_band(band) and _is_band(entry["face_value"])
                and (best == "unavailable" or _is_band(best))
                and isinstance(entry["tasks"], list)):
            raise PayloadError(f"{slug!r} per_language {code!r} has a figure that is not a band: {entry!r}")
        # Both hold by construction in `depth_ladder.language_detail`: the band is the best own
        # band or a capped import, a cap never raises a component above its own band, and the face
        # value is the highest component band of all. A row that breaks either was not built by
        # the ladder.
        if band > entry["face_value"]:
            raise PayloadError(f"{slug!r} per_language {code!r} has band {band} above its face value "
                               f"{entry['face_value']}; the corroboration cap never raises a band")
        if best != "unavailable" and best > band:
            raise PayloadError(f"{slug!r} per_language {code!r} has best_original {best} above its band "
                               f"{band}; the band is at least the set's own best band")
    try:
        roster = targets(slug)
    except (OSError, KeyError, TypeError) as exc:
        raise PayloadError(f"{slug!r} carries per_language bands, but its target-language roster "
                           f"cannot be read from the source records ({exc!r})") from exc
    if sorted(languages) != sorted(roster):
        missing, extra = sorted(set(roster) - set(languages)), sorted(set(languages) - set(roster))
        raise PayloadError(f"{slug!r} per_language keys are not its target languages: missing "
                           f"{missing}, not a target {extra}")
    measured = sum(1 for e in languages.values() if e["band"] is not None)
    completeness = depth.get("completeness") or {}
    if (measured, len(languages)) != (completeness.get("measured"), completeness.get("targets")):
        raise PayloadError(
            f"{slug!r} per_language has {measured} measured of {len(languages)} target languages, "
            f"but completeness says {completeness.get('measured')} of {completeness.get('targets')}")
    implied = band_from_languages(languages)
    if implied != capability.get("score"):
        raise PayloadError(
            f"{slug!r} per_language bands give a set band of {implied!r}, but capability.score "
            f"is {capability.get('score')!r}")
    if (implied is None) != (depth.get("status") == "unresolved"):
        raise PayloadError(f"{slug!r} per_language bands give {implied!r}, which disagrees with "
                           f"depth status {depth.get('status')!r}")


def check(payload: dict, *, targets: Callable[[str], list[str]] = set_targets) -> None:
    """Gate `payload`. `targets` gives a depth-ladder set's target-language roster by slug; it
    defaults to the ladder's own derivation from `sources/`, and a test passes its own."""
    if not isinstance(payload, dict):
        raise PayloadError(f"payload is not an object (got {type(payload).__name__})")

    categories = _require_dict(payload, "categories")
    orgs = _require_dict(payload, "organizations")
    aliases = _require_dict(payload, "aliases")
    alias_maps: dict[str, dict] = {}
    for kind in _ALIAS_KINDS:
        value = aliases.get(kind)
        if not isinstance(value, dict):
            raise PayloadError(
                f"payload has no usable aliases.{kind} block (got {type(value).__name__})"
            )
        alias_maps[kind] = value

    rows: list[dict] = []
    for cid, cat in categories.items():
        if not isinstance(cat, dict):
            raise PayloadError(f"category {cid!r} is not an object")
        products = cat.get("products")
        if not isinstance(products, list):
            raise PayloadError(f"category {cid!r} has no usable products list")
        rows.extend(products)

    # A gate that only checks "more than one distinct freshness date" is vacuously true
    # on zero products (an empty set has zero distinct dates too) and on one product (it
    # can never have two dates on its own) -- both would otherwise fall through to the
    # canary below and get its confusing shallow-clone message instead of the real
    # problem: there is nothing here to evaluate at all.
    if not rows:
        raise PayloadError("the payload has no products at all")

    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise PayloadError(f"a product row is not an object (got {type(row).__name__})")
        slug = row.get("slug")
        if not slug:
            raise PayloadError(f"product {row.get('product')!r} has no slug")
        if slug in seen:
            raise PayloadError(f"duplicate product slug {slug!r}")
        seen.add(slug)
        if row.get("org_slug") not in orgs:
            raise PayloadError(f"{slug!r} points at missing organization {row.get('org_slug')!r}")
        fresh = row.get("freshness")
        if (not isinstance(fresh, dict) or not fresh.get("date")
                or fresh.get("basis") not in _FRESHNESS_BASES):
            raise PayloadError(f"{slug!r} has no usable freshness record")
        _check_freshness_caveats(slug, fresh)
        if "end_of_life" in row:
            _check_end_of_life(slug, row["end_of_life"])
        _check_identity_attributes(slug, row, orgs)
        capability = row.get("capability")
        if isinstance(capability, dict) and "depth" in capability:
            _check_depth_languages(slug, capability, targets)

    dates = {row["freshness"]["date"] for row in rows}
    if len(dates) <= 1:
        raise PayloadError(
            "the payload has only one distinct freshness date across every product, which is "
            "the signature of a shallow clone dating every score file to the tip commit"
        )

    for kind, live in (("products", seen), ("organizations", set(orgs))):
        for old, new in alias_maps[kind].items():
            if old in live:
                raise PayloadError(f"{kind} alias {old!r} is also a live slug")
            if new not in live:
                raise PayloadError(f"{kind} alias {old!r} points at missing {new!r}")


def main() -> int:
    payload = json.loads((ROOT / "build" / "notebook_data.json").read_text())
    try:
        check(payload)
    except PayloadError as exc:
        print(f"check_payload: {exc}", file=sys.stderr)
        return 1
    n = sum(len(c["products"]) for c in payload["categories"].values())
    print(f"check_payload: {n} products, {len(payload['organizations'])} organizations, ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
