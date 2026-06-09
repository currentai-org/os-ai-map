"""Deterministic slug derivation for products and organizations."""
import re


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def dedupe_slug(base: str, org_slug: str, taken: set[str]) -> str:
    """Return `base`, or `base-<org>` if base is already taken."""
    if base not in taken:
        return base
    return f"{base}-{org_slug}"
