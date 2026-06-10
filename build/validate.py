"""Validate the four-concern sources/ tree: schema + cross-file invariants."""
import json
from pathlib import Path

import jsonschema
import yaml

# Maps each sources/ subdir to its docs/schemas/<name>.schema.json basename.
_SCHEMA_FOR_DIR = {
    "organizations": "organization",
    "categories": "category",
    "products": "product",
    "scores": "score",
}


def _load_schemas(root: Path) -> dict:
    schema_dir = root / "docs" / "schemas"
    return {
        name: json.loads((schema_dir / f"{name}.schema.json").read_text())
        for name in set(_SCHEMA_FOR_DIR.values())
    }

OPENNESS_CLASSES = {
    "model": {"open_source", "open_weights", "restricted", "closed"},
    "software": {"open_source", "source_available", "open_core", "closed"},
    "dataset": {"open", "gated", "documented_only", "closed"},
}
SIGNAL_TYPES = {"active_users", "usage_volume", "reported_traction", "stars_fallback", "unknown"}


def load_sources(root: Path) -> dict:
    def _dir(name):
        return {p.stem: yaml.safe_load(p.read_text()) for p in sorted((root / "sources" / name).glob("*.yaml"))}
    return {
        "organizations": _dir("organizations"),
        "categories": _dir("categories"),
        "products": _dir("products"),
        "scores": _dir("scores"),
        "taxonomy": yaml.safe_load((root / "sources" / "taxonomy.yaml").read_text()),
    }


def validate_sources(data: dict) -> list[str]:
    errors: list[str] = []
    orgs, cats, prods, scores = (data["organizations"], data["categories"],
                                 data["products"], data["scores"])
    taxonomy = data["taxonomy"]

    # --- taxonomy <-> category invariants ---
    # Every category file appears in exactly one arc's `categories` list, and
    # every slug in the manifest resolves to a real category file.
    tax_count: dict[str, int] = {}
    for arc in taxonomy.get("arcs", []):
        for cid in arc.get("categories", []):
            tax_count[cid] = tax_count.get(cid, 0) + 1
            if cid not in cats:
                errors.append(f"taxonomy arc {arc.get('name')!r}: category {cid!r} has no categories/{cid}.yaml")
    for cid in cats:
        n = tax_count.get(cid, 0)
        if n != 1:
            errors.append(f"category {cid!r}: must appear in exactly one taxonomy arc (found in {n})")

    # --- roster <-> product invariants ---
    roster_count: dict[str, int] = {}
    for cid, cat in cats.items():
        for slug in cat.get("products", []):
            roster_count[slug] = roster_count.get(slug, 0) + 1
            if slug not in prods:
                errors.append(f"category {cid}: roster slug {slug!r} has no products/{slug}.yaml")
    for slug in prods:
        n = roster_count.get(slug, 0)
        if n != 1:
            errors.append(f"product {slug!r}: must appear in exactly one category roster (found in {n})")

    # --- org roster <-> product invariants (org now owns the roster) ---
    # Symmetric to the category roster: every product slug appears in exactly one
    # org roster, and every slug in an org roster resolves to a real product file.
    org_roster_count: dict[str, int] = {}
    for oslug, org in orgs.items():
        for slug in org.get("products", []):
            org_roster_count[slug] = org_roster_count.get(slug, 0) + 1
            if slug not in prods:
                errors.append(f"organization {oslug}: roster slug {slug!r} has no products/{slug}.yaml")
    for slug in prods:
        n = org_roster_count.get(slug, 0)
        if n != 1:
            errors.append(f"product {slug!r}: must appear in exactly one org roster (found in {n})")

    # --- scores ---
    for slug, sc in scores.items():
        if slug not in prods:
            errors.append(f"score {slug!r}: no matching product")
            continue
        typ = prods[slug].get("type")
        op = sc.get("openness", {})
        if op.get("class") and op["class"] not in OPENNESS_CLASSES.get(typ, set()):
            errors.append(f"score {slug!r}: openness class {op['class']!r} invalid for type {typ!r}")
        if op.get("score") is not None and not op.get("sources"):
            errors.append(f"score {slug!r}: non-null openness needs >=1 source")
        ad = sc.get("adoption", {})
        st = ad.get("signal_type")
        if st and st not in SIGNAL_TYPES:
            errors.append(f"score {slug!r}: adoption signal_type {st!r} invalid")
        if st == "stars_fallback" and (ad.get("level") or 0) > 3:
            errors.append(f"score {slug!r}: stars_fallback cannot justify adoption level > 3")
        if ad.get("level") is not None and not ad.get("sources"):
            errors.append(f"score {slug!r}: non-null adoption needs >=1 source")
        cap = sc.get("capability", {})
        if cap.get("score") is not None and not cap.get("sources"):
            errors.append(f"score {slug!r}: non-null capability needs >=1 source")

    # --- product -> score existence ---
    # validate only checks score -> product; without this, a rostered product
    # with no scores/<slug>.yaml passes validate then crashes serialize.py.
    for slug in prods:
        if slug not in scores:
            errors.append(f"product {slug!r}: no scores/{slug}.yaml")

    # --- per-record JSON Schema validation ---
    schemas = _load_schemas(Path(__file__).resolve().parents[1])
    for dirname, schema_name in _SCHEMA_FOR_DIR.items():
        schema = schemas[schema_name]
        for slug, record in data[dirname].items():
            try:
                jsonschema.validate(record, schema)
            except jsonschema.ValidationError as e:
                errors.append(f"{dirname}/{slug}: schema: {e.message}")

    return errors


if __name__ == "__main__":
    import sys
    errs = validate_sources(load_sources(Path(__file__).resolve().parents[1]))
    for e in errs:
        print("ERROR:", e)
    print(f"\n{len(errs)} error(s)")
    sys.exit(1 if errs else 0)
