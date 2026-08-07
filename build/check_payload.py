"""Gate the serialized payload's identity invariants.

build/validate.py covers the source YAML. This covers the artifact the app consumes, which
is a different thing: a serializer bug can produce a valid source tree and a payload the
app cannot build pages from.

Every branch below either confirms one invariant or refuses to judge the payload -- a
missing top-level block, `None` where a dict belongs, an empty product set, or a malformed
row must never read as "fine". A gate that goes green when it cannot understand its input
is worse than no gate at all: it looks like protection nobody is actually getting.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_ALIAS_KINDS = ("products", "organizations")
_FRESHNESS_BASES = {"verified", "commit"}


class PayloadError(RuntimeError):
    pass


def _require_dict(payload: dict, key: str) -> dict:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise PayloadError(
            f"payload has no usable {key!r} block (got {type(value).__name__})"
        )
    return value


def check(payload: dict) -> None:
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
