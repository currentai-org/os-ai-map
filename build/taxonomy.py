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


def arc_groups(arc: dict) -> Iterator[tuple[str, str, list]]:
    """Yield ``(group_name, group_slug, categories)`` from one arc, in display order.

    Only groups carrying both a name and a slug are yielded. A malformed group is
    skipped here and reported by ``build/validate.py``, which is the same division of
    labour ``category_entry`` already uses: this module normalizes the shape, the
    validator is what fails the build.
    """
    groups = arc.get("groups")
    if groups is None and arc.get("categories") is not None:
        # READING AN OLDER REF. Before the group tier, categories sat directly on the arc.
        # Tools that compare two refs -- build/check_corpus_diff.py builds the base payload
        # from a worktree at the base commit, with THIS code -- would otherwise walk a
        # pre-group tree, find no groups, and yield nothing, producing an empty payload and
        # a diff claiming every product in the corpus had just appeared. That is what the
        # gate reported before this fallback existed, and "everything appeared" is not a
        # diagnosis anybody reaches from.
        #
        # This tolerance is for READING history only. `build/validate.py` rejects the shape
        # in the repository's own sources, so it cannot come back by the front door, and the
        # fallback stops mattering once no ref in range predates the migration.
        yield "", "", arc["categories"]
        return
    for group in groups or []:
        if not isinstance(group, dict):
            continue
        name, slug = group.get("name"), group.get("slug")
        if isinstance(name, str) and isinstance(slug, str):
            yield name, slug, group.get("categories") or []


def arc_categories(arc: dict) -> Iterator[tuple[str, str]]:
    """Yield valid ``(slug, status)`` pairs from one arc, in display order.

    Walks the arc's groups, since categories sit inside a group rather than directly
    on the arc. The signature is unchanged so that ``validate``, ``reverify``,
    ``goldens``, ``sweep_status`` and both serializers keep reading it as they did --
    the flattening changes once, here, which is the whole reason it lives in one place.
    """
    for _name, _slug, categories in arc_groups(arc):
        for value in categories:
            slug, status = category_entry(value)
            if slug is not None and status is not None:
                yield slug, status


def arc_grouped_categories(arc: dict) -> Iterator[tuple[str, str, str, str]]:
    """Yield ``(group_name, group_slug, slug, status)`` from one arc, in display order.

    The sibling of ``arc_categories`` for the consumers that need the group. Kept
    separate rather than widening the tuple, because every existing caller wants the
    two-field form and would otherwise unpack two values it has no use for.
    """
    for name, slug, categories in arc_groups(arc):
        for value in categories:
            category, status = category_entry(value)
            if category is not None and status is not None:
                yield name, slug, category, status


def category_statuses(taxonomy: dict) -> dict[str, str]:
    """Map every well-formed category slug to its lifecycle status."""
    return {
        slug: status
        for arc in taxonomy.get("arcs") or []
        if isinstance(arc, dict)
        for slug, status in arc_categories(arc)
    }
