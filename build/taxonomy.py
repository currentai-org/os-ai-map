"""Read category identity and lifecycle state from ``sources/taxonomy.yaml``.

Published categories may retain the historical scalar spelling.  A mapping is
used when lifecycle metadata is needed, most importantly for preliminary
categories that exist in the registry but must not enter the public scored map.
Keeping this normalization here gives validation and both serializers one owner
for the backward-compatible syntax.
"""

from __future__ import annotations

from collections.abc import Iterator


def category_entry(value: object) -> tuple[str | None, str | None]:
    """Return ``(slug, status)`` for one taxonomy category entry."""
    if isinstance(value, str):
        return value, "published"
    if isinstance(value, dict):
        slug = value.get("name")
        status = value.get("status")
        return (slug if isinstance(slug, str) else None,
                status if isinstance(status, str) else None)
    return None, None


def arc_categories(arc: dict) -> Iterator[tuple[str, str]]:
    """Yield valid ``(slug, status)`` pairs from one arc, in display order."""
    for value in arc.get("categories") or []:
        slug, status = category_entry(value)
        if slug is not None and status is not None:
            yield slug, status


def category_statuses(taxonomy: dict) -> dict[str, str]:
    """Map every well-formed category slug to its lifecycle status."""
    return {
        slug: status
        for arc in taxonomy.get("arcs") or []
        if isinstance(arc, dict)
        for slug, status in arc_categories(arc)
    }
