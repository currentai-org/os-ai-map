"""Build the organization registry from the overlay product records."""
from build.slugs import slugify


def build_org_registry(overlay_products: list[dict]) -> tuple[list[dict], dict]:
    """Return (org_records, name_to_slug). One record per distinct org name."""
    name_to_slug: dict[str, str] = {}
    orgs: dict[str, dict] = {}
    for p in overlay_products:
        name = (p.get("org") or "").strip()
        if name == "":
            name_to_slug[""] = "unknown"
            orgs.setdefault("unknown", {"slug": "unknown", "name": "Unknown", "type": "unknown"})
            continue
        slug = slugify(name)
        name_to_slug[name] = slug
        orgs.setdefault(slug, {"slug": slug, "name": name, "type": "unknown"})
    return list(orgs.values()), name_to_slug
