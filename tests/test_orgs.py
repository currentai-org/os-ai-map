from build.orgs import build_org_registry

def test_build_org_registry_dedupes_and_slugs():
    overlay_products = [
        {"product": "Llama 3.1", "org": "Meta"},
        {"product": "Llama 4", "org": "Meta"},
        {"product": "OLMo 2", "org": "Allen Institute for AI"},
        {"product": "Mystery", "org": ""},
    ]
    orgs, name_to_slug = build_org_registry(overlay_products)
    assert name_to_slug["Meta"] == "meta"
    assert name_to_slug["Allen Institute for AI"] == "allen-institute-for-ai"
    # one record per distinct org name; empty org -> "unknown"
    assert sum(1 for o in orgs if o["slug"] == "meta") == 1
    assert name_to_slug[""] == "unknown"
