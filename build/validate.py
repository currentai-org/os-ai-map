"""Validate the four-concern sources/ tree: schema + cross-file invariants."""
from datetime import date
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
    "hardware": {"open_hardware", "open_toolchain", "documented", "restricted"},
}
SIGNAL_TYPES = {"active_users", "usage_volume", "reported_traction", "stars_fallback", "unknown"}
LAYERS = {"product_ux", "model_components", "infrastructure"}


def load_sources(root: Path) -> dict:
    def _dir(name):
        return {p.stem: yaml.safe_load(p.read_text()) for p in sorted((root / "sources" / name).glob("*.yaml"))}
    data = {
        "organizations": _dir("organizations"),
        "categories": _dir("categories"),
        "products": _dir("products"),
        "scores": _dir("scores"),
        "taxonomy": yaml.safe_load((root / "sources" / "taxonomy.yaml").read_text()),
        "slug_aliases": yaml.safe_load((root / "sources" / "slug_aliases.yaml").read_text()),
    }
    lt = root / "build" / "_frozen_long_tail.json"
    if lt.exists():
        data["long_tail"] = json.loads(lt.read_text())
    return data


def validate_sources(data: dict) -> list[str]:
    errors: list[str] = []
    orgs, cats, prods, scores = (data["organizations"], data["categories"],
                                 data["products"], data["scores"])
    taxonomy = data["taxonomy"]

    # --- taxonomy <-> category invariants ---
    # Every category file appears in exactly one arc's `categories` list, and
    # every slug in the manifest resolves to a real category file.
    # Arcs are the Columbia ontology layers; each must declare a valid `layer`
    # slug, since serialize derives every category's layer from its arc.
    tax_count: dict[str, int] = {}
    for arc in taxonomy.get("arcs", []):
        if arc.get("layer") not in LAYERS:
            errors.append(f"taxonomy arc {arc.get('name')!r}: layer {arc.get('layer')!r} not in {sorted(LAYERS)}")
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

    # --- slug stability ---
    # The slug is a product's identity and the key deep links are built on, so a slug may
    # only leave sources/products/ by being recorded in sources/slug_aliases.yaml. These
    # checks are what make that a rule rather than an intention. See that file's header.
    spec = data.get("slug_aliases") or {}
    aliases = spec.get("aliases") or {}
    for old, new in sorted(aliases.items()):
        if new not in prods:
            errors.append(f"slug alias {old!r} -> {new!r}: target is not a live product")
        if old in prods:
            errors.append(
                f"slug alias {old!r}: an alias key means the slug is retired, but a product "
                f"still uses it. Either drop the alias or rename the product."
            )
    org_aliases = spec.get("organization_aliases") or {}
    for old, new in sorted(org_aliases.items()):
        if new not in orgs:
            errors.append(f"org alias {old!r} -> {new!r}: target is not a live organization")
        if old in orgs:
            errors.append(f"org alias {old!r}: retired, but an organization still uses it")

    # A slug ending in its own vendor's name carries no information and is the pattern
    # that produced gpt-4-1-openai and nemotron-3-nvidia. Cheap to catch, so caught.
    for org_slug, org in sorted(orgs.items()):
        for product in org.get("products") or []:
            if product != org_slug and product.endswith(f"-{org_slug}"):
                errors.append(
                    f"product {product!r}: slug ends with its own organization {org_slug!r}. "
                    f"Disambiguate by product surface, not by vendor."
                )

    # --- frozen long-tail <-> live count invariant ---
    # The long-tail section shows "Of the {scored} products scored above ..."; that
    # count is a hand-synced snapshot and must track the live product count, or the
    # notebook contradicts itself. Only checked when the fixture is loaded (real runs,
    # not hand-built test fixtures).
    lt = data.get("long_tail")
    if lt:
        scored = (lt.get("counts") or {}).get("scored")
        if scored is not None and scored != len(prods):
            errors.append(f"long_tail counts.scored ({scored}) != product count ({len(prods)}); "
                          f"re-sync build/_frozen_long_tail.json after a batch")

    # --- observation dates cannot be in the future ---
    # `accessed` records when a source was read and `last_verified` when a check happened.
    # Both are observation events, so neither can be later than today. The map is
    # deliberately a forward-dated universe and may describe unreleased products, but that
    # is prose and release dates, never a claim about when somebody looked.
    #
    # Checked because nothing else does, and because apply_scores refuses to move a stored
    # date backwards - so a future date, once written, would be protected indefinitely by
    # the very guard meant to preserve real checks.
    today = date.today()
    for slug, score in sorted(scores.items()):
        for axis in ("openness", "adoption", "capability"):
            block = score.get(axis) or {}
            candidates = [("last_verified", block.get("last_verified"))]
            for source in block.get("sources") or []:
                if isinstance(source, dict):
                    candidates.append(("sources.accessed", source.get("accessed")))
            for field, raw in candidates:
                if not raw:
                    continue
                try:
                    when = date.fromisoformat(str(raw))
                except ValueError:
                    errors.append(f"score {slug!r}: {axis}.{field} {raw!r} is not an ISO date")
                    continue
                if when > today:
                    errors.append(
                        f"score {slug!r}: {axis}.{field} is {when}, later than today ({today}); "
                        f"an observation cannot have happened in the future"
                    )

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
