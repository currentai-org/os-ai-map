"""Validate the scored corpus, taxonomy, and signal-only tail registry."""
from datetime import date
import json
import re
from pathlib import Path

import jsonschema
import yaml

from build.identity import fold_for_proposal, id_from_url
from build.vocabulary import axes, SIGNAL_TYPES

from build.rubrics import dimension_vocabulary
from build.taxonomy import category_entry, category_statuses

# Maps each sources/ subdir to its docs/schemas/<name>.schema.json basename.
_SCHEMA_FOR_DIR = {
    "organizations": "organization",
    "categories": "category",
    "products": "product",
    "scores": "score",
}
# taxonomy.yaml is one file, not a directory, so it is schema-checked separately below
# rather than through _SCHEMA_FOR_DIR. Listed here so _load_schemas picks it up.
_EXTRA_SCHEMAS = ("taxonomy",)


def _load_schemas(root: Path) -> dict:
    schema_dir = root / "docs" / "schemas"
    return {
        name: json.loads((schema_dir / f"{name}.schema.json").read_text())
        for name in set(_SCHEMA_FOR_DIR.values()) | set(_EXTRA_SCHEMAS)
    }

OPENNESS_CLASSES = {
    "model": {"open_source", "open_weights", "restricted", "closed"},
    "software": {"open_source", "source_available", "open_core", "closed"},
    # `restricted` joined the dataset vocabulary with the universal license scale. It was the
    # only product type with no word between `open` and `gated`, so a non-commercial corpus
    # had nowhere to land but `open` - which is how `personahub` came to be 5/open under a
    # license that caps a model at 2. The word already exists for models and hardware, and
    # already carries gradient 2 and the closed bucket in openness-class-map.json.
    "dataset": {"open", "gated", "restricted", "closed"},
    "hardware": {"open_hardware", "open_toolchain", "documented", "restricted"},
}
# `SIGNAL_TYPES` is the canonical adoption instrument vocabulary, owned by build/vocabulary.py
# and imported above so this gate and serialize_routing cannot disagree about the set.
LAYERS = {"product_ux", "model_components", "infrastructure"}

# The artifact kinds a tail row can dedup on. `homepage` carries no adoption signal, but it
# is still an identity key -- two tail rows (or a tail row and a head product) declaring the
# same homepage domain are the same duplicate-identity problem this gate exists to catch, and
# `serialize_registry.py` emits a `tail_products` row for a homepage exactly like any other
# kind. Excluding it here would leave that emitted identity key ungated.
_TAIL_ARTIFACT_KINDS = (
    "github",
    "huggingface_model",
    "huggingface_dataset",
    "pypi",
    "npm",
    "crates",
    "arxiv",
    "homepage",
)

# Canonicalization and URL parsing for every artifact kind now live in build/identity.py
# -- the one place these rules live. See `canonical` and `id_from_url`, imported above.


def load_sources(root: Path) -> dict:
    def _dir(name):
        return {p.stem: yaml.safe_load(p.read_text()) for p in sorted((root / "sources" / name).glob("*.yaml"))}
    data = {
        "organizations": _dir("organizations"),
        "categories": _dir("categories"),
        "rubrics": _dir("rubrics"),
        "products": _dir("products"),
        "scores": _dir("scores"),
        "taxonomy": yaml.safe_load((root / "sources" / "taxonomy.yaml").read_text()),
        "registry": _dir("registry"),
    }
    lt = root / "sources" / "snapshots" / "long_tail.json"
    if lt.exists():
        data["long_tail"] = json.loads(lt.read_text())
    return data


def published_products(taxonomy: dict, cats: dict) -> set[str]:
    """Every product slug on the roster of a PUBLISHED category.

    The set the notebook payload actually carries. `serialize.py` derives `n_total` from the
    same walk, and this is the one owner of "which products are publicly visible" so the two
    cannot drift: a preliminary category is registry-visible and payload-invisible, and its
    head products are neither an error nor published. A category absent from the taxonomy
    defaults to published, which keeps hand-built fixtures behaving as they did before
    lifecycle status existed; the missing-arc case is already an error of its own above.
    """
    statuses = category_statuses(taxonomy or {})
    return {
        slug
        for cid, cat in (cats or {}).items()
        if statuses.get(cid, "published") == "published"
        for slug in (cat.get("products") or [])
    }


def validate_sources(data: dict) -> list[str]:
    errors: list[str] = []
    orgs, cats, prods, scores = (data["organizations"], data["categories"],
                                 data["products"], data["scores"])
    taxonomy = data["taxonomy"]
    registry = data.get("registry") or {}

    # --- taxonomy <-> category invariants ---
    # Every category file appears in exactly one arc's `categories` list, and
    # every slug in the manifest resolves to a real category file.
    # Arcs are the Columbia ontology layers; each must declare a valid `layer`
    # slug, since serialize derives every category's layer from its arc.
    tax_count: dict[str, int] = {}
    for arc in taxonomy.get("arcs", []):
        if arc.get("layer") not in LAYERS:
            errors.append(f"taxonomy arc {arc.get('name')!r}: layer {arc.get('layer')!r} not in {sorted(LAYERS)}")
        for raw in arc.get("categories", []):
            cid, status = category_entry(raw)
            if cid is None or status is None:
                continue
            tax_count[cid] = tax_count.get(cid, 0) + 1
            if cid not in cats:
                errors.append(f"taxonomy arc {arc.get('name')!r}: category {cid!r} has no categories/{cid}.yaml")
    for cid in cats:
        n = tax_count.get(cid, 0)
        if n != 1:
            errors.append(f"category {cid!r}: must appear in exactly one taxonomy arc (found in {n})")

    # --- category contract, by lifecycle status ---
    # Applied on the NORMALIZED status, so both taxonomy spellings are held to the same
    # contract. This used to skip any category not declared as a mapping, on the reasoning
    # that scalar entries predate lifecycle status and should not be disturbed - and that
    # reasoning let the compatibility shim become an exemption. Appending a scalar entry for
    # a category file carrying nothing but `name`, `display_name` and an empty `products`
    # produced zero errors and a publicly visible category with no description, no weights,
    # no ladder and no strapline. Found in review of the compilers/storage promotion.
    #
    # Applying it to all eighteen categories was measured before it was written: every one of
    # the sixteen scalar entries already satisfies the whole contract, so this closes a hole
    # rather than creating work. `category_statuses` is what makes the two spellings one
    # question - a scalar entry normalizes to `published`, which is what it has always meant.
    statuses = category_statuses(taxonomy)
    for cid, cat in cats.items():
        if cid not in statuses:
            continue  # not in any arc; already reported above
        status = statuses[cid]
        if not cat.get("description"):
            errors.append(f"category {cid!r}: every category needs a description")
        if not cat.get("weights"):
            errors.append(f"category {cid!r}: every category needs axis weights")
        if not cat.get("scoring_recipe"):
            errors.append(f"category {cid!r}: every category needs a scoring_recipe")
        if status == "published":
            if not cat.get("strapline"):
                errors.append(f"category {cid!r}: published category needs a strapline")
            if len(cat.get("products") or []) < 10:
                errors.append(f"category {cid!r}: published category needs at least 10 scored products")

    # --- resolution ledger ---
    # An artifact a person already resolved may not come back as a new product. The ledger
    # exists because a decision recorded only in a pull request is invisible to the next bulk
    # run: the first corpus expansion recreated `a2aproject/A2A` as a product called `a2a`
    # though #413 had resolved it to `agent2agent-protocol`, and eleven more besides. Prose is
    # not an input; this file is.
    #
    # `unresolved` is deliberately not enforced. It means a person still has to look, so a
    # later run proposing the artifact again is the intended behaviour rather than a
    # regression, and failing the build on it would just delete the distinction.
    #
    # Widened from `github` only to every declared artifact kind (#437 follow-on): a candidate
    # dismissed on PyPI or Hugging Face alone used to have no way to stay dismissed. Every kind
    # is folded through `build.identity.fold_for_proposal`, the same function
    # `build/resolution.py`'s ledger key now delegates to, so a differently-cased PyPI or npm
    # name matches here too.
    from build.resolution import MEMBERSHIP_VERDICTS, NOT_A_NEW_PRODUCT, load as load_ledger

    ledger = load_ledger()
    for slug, product in sorted((data.get("products") or {}).items()):
        for kind in _TAIL_ARTIFACT_KINDS:
            for artifact in (product.get(kind) or []):
                if not (isinstance(artifact, dict) and isinstance(artifact.get("url"), str)):
                    continue
                raw_ident = id_from_url(kind, artifact["url"])
                if raw_ident is None:
                    continue
                ident = fold_for_proposal(kind, raw_ident)
                entry = ledger.get(((kind, ident), "product_equivalence"))
                if not entry or entry.get("verdict") not in NOT_A_NEW_PRODUCT:
                    continue
                resolved_to = entry.get("product") or entry.get("resolves_to")
                if resolved_to == slug:
                    continue
                resolved_to = resolved_to or entry.get("boundary") or "out of scope"
                errors.append(
                    f"products/{slug}.yaml: declares {kind} {ident!r}, which the resolution "
                    f"ledger resolves as {entry['verdict']} -> {resolved_to} "
                    f"(decided in {entry.get('decided_in', 'an earlier sweep')}). Either the "
                    f"ledger entry is wrong and a person should change it, or this product "
                    f"should not exist."
                )

    # A `member_of`/`not_member_of` verdict answers a `product_membership` question; recording
    # one under any other relation would make `verdict_for` read it as an equivalence ruling it
    # never made.
    for (key, relation), entry in ledger.items():
        if entry.get("verdict") in MEMBERSHIP_VERDICTS and relation != "product_membership":
            kind, ident = key
            errors.append(
                f"resolution ledger: {kind} {ident!r} carries verdict {entry['verdict']!r} but "
                f"relation {relation!r}; member_of/not_member_of require relation: "
                "product_membership"
            )

    # --- tail registry invariants ---
    # Tail rows are deliberately lighter than head product records, but identity is
    # not: a slug and an addressable artifact may appear in only one tier and category.
    # #365 widened "addressable" past GitHub -- a candidate discovered on Hugging Face, a
    # package registry, or in a paper is now storable too -- so dedup has to run per
    # artifact kind rather than assuming `github` is the only one worth checking. A
    # GitHub-only check let an HF-only or package-only candidate be added twice under two
    # kinds with nothing noticing.
    tail_slugs: dict[str, str] = {}
    # Keyed (kind, canonical id) -> owning slug, shared across every registry file so a
    # collision is caught regardless of which category first claimed the artifact.
    tail_artifacts: dict[tuple[str, str], str] = {}
    head_artifacts: dict[tuple[str, str], str] = {}
    # A retired slug is a settled decision, so it disqualifies a candidate exactly as a live
    # slug does: re-adding it re-opens the consolidation that retired it. Checking only
    # `slug in prods` missed that entirely -- amazon-nova-pro, an alias of amazon-nova, passed
    # validation as a new candidate. Resolved here rather than reusing the `claimed` map built
    # in the slug-stability section below, because that map is built by a loop whose purpose is
    # to REPORT duplicate claims as it goes; this one only needs to resolve them.
    alias_of = {
        alias: slug
        for slug, product in sorted(prods.items())
        for alias in product.get("aliases") or []
        if isinstance(alias, str)
    }
    for slug, product in prods.items():
        for kind in _TAIL_ARTIFACT_KINDS:
            for artifact in product.get(kind) or []:
                if not (isinstance(artifact, dict) and isinstance(artifact.get("url"), str)):
                    continue
                raw_ident = id_from_url(kind, artifact["url"])
                if raw_ident is None:
                    continue
                head_artifacts[(kind, fold_for_proposal(kind, raw_ident))] = slug
    for cid, record in registry.items():
        if not isinstance(record, dict):
            errors.append(f"registry/{cid}.yaml: record must be a mapping")
            continue
        if record.get("category") != cid:
            errors.append(
                f"registry/{cid}.yaml: `category: {record.get('category')!r}` does not match "
                f"the filename stem {cid!r}"
            )
        if cid not in cats:
            errors.append(f"registry/{cid}.yaml: no matching categories/{cid}.yaml")
        for row in record.get("products") or []:
            if not isinstance(row, dict):
                continue
            slug = row.get("slug")
            if not isinstance(slug, str):
                continue
            if slug in prods:
                errors.append(f"registry/{cid}.yaml: tail slug {slug!r} already exists as a head product")
            if slug in alias_of:
                errors.append(
                    f"registry/{cid}.yaml: tail slug {slug!r} is a retired alias of head product "
                    f"{alias_of[slug]!r}. A retired slug was deliberately consolidated or "
                    f"dropped; re-adding it as a candidate re-opens a settled decision."
                )
            if slug in tail_slugs:
                errors.append(
                    f"registry/{cid}.yaml: tail slug {slug!r} already belongs to "
                    f"registry/{tail_slugs[slug]}.yaml"
                )
            tail_slugs[slug] = cid

            has_artifact = False
            for kind in _TAIL_ARTIFACT_KINDS:
                value = row.get(kind)
                if not isinstance(value, str) or not value:
                    continue
                has_artifact = True
                key = (kind, fold_for_proposal(kind, value))
                if key in head_artifacts:
                    errors.append(
                        f"registry/{cid}.yaml: {kind} artifact {value!r} already belongs to "
                        f"head product {head_artifacts[key]!r}"
                    )
                if key in tail_artifacts:
                    errors.append(
                        f"registry/{cid}.yaml: {kind} artifact {value!r} already belongs to "
                        f"tail product {tail_artifacts[key]!r}"
                    )
                tail_artifacts[key] = slug
            if not has_artifact:
                errors.append(
                    f"registry/{cid}.yaml: tail slug {slug!r} has no addressable artifact "
                    "(one of github, huggingface_model, huggingface_dataset, pypi, npm, "
                    "crates, arxiv, or homepage)"
                )

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
    # only leave sources/products/ by being recorded as an alias on the product that
    # replaced it. These checks are what make that a rule rather than an intention, and
    # they are why the aliases live on the records: held in one mapping until 2026-08-08,
    # two renames of the same retired slug silently kept whichever came last, because
    # PyYAML does not error on a duplicate key. See docs/reference/identity.md.
    claimed: dict[str, str] = {}
    for slug, product in sorted(prods.items()):
        for alias in product.get("aliases") or []:
            if alias in prods:
                errors.append(
                    f"product {slug!r}: alias {alias!r} means that slug is retired, but a "
                    f"product still uses it. Either drop the alias or rename the product."
                )
            if alias in claimed:
                errors.append(
                    f"alias {alias!r} is claimed by both {claimed[alias]!r} and {slug!r}. "
                    f"A retired slug resolves to exactly one product."
                )
            claimed[alias] = slug
    org_claimed: dict[str, str] = {}
    for slug, org in sorted(orgs.items()):
        for alias in org.get("aliases") or []:
            if alias in orgs:
                errors.append(f"organization {slug!r}: alias {alias!r} is still a live organization")
            if alias in org_claimed:
                errors.append(
                    f"org alias {alias!r} is claimed by both {org_claimed[alias]!r} and {slug!r}"
                )
            org_claimed[alias] = slug

    # A model slug that bakes in a version goes stale the day the next release ships,
    # and then costs an alias to fix. Vendors do sometimes sell the version as the
    # product - GPT-4o, Mistral 7B - so an exception is allowed, but the product has to
    # carry `version_in_identity` with the reason. Scoped to model categories: for a
    # dataset or a board the version genuinely is the identity (oscar-2301,
    # raspberry-pi-5), which is why those are not checked.
    model_cats = {"base_pretrained", "finetuned_chat"}
    model_products = {
        p for slug, cat in cats.items() if slug in model_cats for p in (cat.get("products") or [])
    }
    version_token = re.compile(r"(?:^|-)(v?\d+(?:[-.]\d+)*[a-z]?|\d+[bx])(?:-|$)")
    for product in sorted(model_products):
        if version_token.search(product) and not (prods.get(product) or {}).get("version_in_identity"):
            errors.append(
                f"product {product!r}: model slug carries a version or size token. Collapse it "
                f"to the tier the vendor sells, or add `version_in_identity` with the reason."
            )
    for slug, product in sorted(prods.items()):
        if product.get("version_in_identity") and slug not in model_products:
            errors.append(
                f"product {slug!r} declares version_in_identity, which only applies to a model "
                f"product. Datasets and hardware keep the version by default."
            )

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
    # count is a hand-synced snapshot and must track what the notebook actually shows
    # above it, or the notebook contradicts itself. Only checked when the fixture is
    # loaded (real runs, not hand-built test fixtures).
    #
    # "What the notebook shows" is the roster of the PUBLISHED categories, not every
    # product file. Those two were the same number until categories gained a lifecycle,
    # and comparing against every file is now wrong in a way that passes: a preliminary
    # category may hold fully scored head products - that is the state a category is in
    # while it is being built, before it is published - and serialize.py omits them from
    # the payload. Counting them here let `scored` exceed `n_total`, so the sentence
    # "of the N products scored above" named products the reader could not see. Caught in
    # review of the compilers/storage promotion, reproduced by marking one of the two
    # preliminary again: `n_total: 496` against `counts.scored: 522`.
    # long_tail counts.scored is derived at serialize time (build.serialize.derived_long_tail_counts),
    # so a product addition never edits sources/snapshots/long_tail.json. The old gate here compared a
    # hand-synced number against the roster; the number no longer exists in the file.

    # --- `establishes` must name a real dimension ---
    # A source's `establishes` list is what makes a re-check claim checkable: it records
    # which source settles which dimension, so check_verification can require a fresh read
    # per dimension rather than one fresh read per axis. That only works if the names mean
    # something. A typo'd `license` or `weight` establishes nothing at all while reading
    # like attribution, and the gate that consumes it would then pass an axis whose
    # dimension has no supporting source. Cross-file because the vocabulary lives in the
    # category recipes, not in the schema.
    vocabulary = dimension_vocabulary(cats, data.get("rubrics") or {})
    if vocabulary:
        for slug, score in sorted(scores.items()):
            for axis in axes():
                for source in (score.get(axis) or {}).get("sources") or []:
                    if not isinstance(source, dict):
                        continue
                    for name in source.get("establishes") or []:
                        if name not in vocabulary:
                            errors.append(
                                f"score {slug!r}: {axis} source {source.get('url')!r} claims to "
                                f"establish {name!r}, which no scoring_recipe declares as a "
                                f"dimension or reads as a recorded key"
                            )

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
        for axis in axes():
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

    # --- the filename IS the identity ---
    # Every join in the pipeline keys on the file stem, but the record also carries the
    # slug in a field, and nothing checked the two agree. A copied or renamed file with
    # a stale inner name passes schema and roster checks and then corrupts joins
    # silently: the roster resolves by stem, while anything reading the field resolves
    # somewhere else. Cheap to assert, so asserted.
    #
    # `scores` names its slug `product` rather than `name`, because a score is about a
    # product rather than being one.
    for dirname, key in (("organizations", "name"), ("categories", "name"),
                         ("products", "name"), ("scores", "product")):
        for stem, record in (data.get(dirname) or {}).items():
            if not isinstance(record, dict):
                continue
            inner = record.get(key)
            if inner != stem:
                errors.append(
                    f"{dirname}/{stem}.yaml: `{key}: {inner!r}` does not match the filename "
                    f"stem {stem!r}. The stem is the identity every join uses, so these must "
                    f"agree or the record is reachable under two different names."
                )

    # --- per-record JSON Schema validation ---
    schemas = _load_schemas(Path(__file__).resolve().parents[1])
    for dirname, schema_name in _SCHEMA_FOR_DIR.items():
        schema = schemas[schema_name]
        for slug, record in data[dirname].items():
            try:
                jsonschema.validate(record, schema)
            except jsonschema.ValidationError as e:
                errors.append(f"{dirname}/{slug}: schema: {e.message}")

    # `taxonomy.yaml` is a single file rather than a directory, so it fell outside
    # `_SCHEMA_FOR_DIR` and was never schema-checked despite having a schema and being
    # described as schema-governed in AGENTS.md. The cross-file arc checks above catch a
    # dangling category, but a malformed required field reaches serialize before anything
    # complains.
    try:
        jsonschema.validate(data["taxonomy"], schemas["taxonomy"])
    except jsonschema.ValidationError as e:
        errors.append(f"sources/taxonomy.yaml: schema: {e.message}")

    registry_schema = json.loads(
        (Path(__file__).resolve().parents[1] / "docs" / "schemas" / "registry.schema.json").read_text()
    )
    for cid, record in registry.items():
        try:
            jsonschema.validate(record, registry_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"registry/{cid}: schema: {e.message}")

    # `sources/resolution_ledger.yaml` is one file rather than a directory, loaded straight
    # from disk here rather than through `load_ledger` above, so a malformed entry is reported
    # by slot in the file rather than silently swallowed by `load`'s duplicate-key check.
    from build.resolution import LEDGER

    ledger_schema = json.loads(
        (Path(__file__).resolve().parents[1] / "docs" / "schemas" / "resolution_ledger.schema.json").read_text()
    )
    ledger_doc = yaml.safe_load(LEDGER.read_text()) or {}
    for i, entry in enumerate(ledger_doc.get("resolutions") or []):
        try:
            jsonschema.validate(entry, ledger_schema)
        except jsonschema.ValidationError as e:
            label = entry.get("repo") or (entry.get("artifact") or {}).get("id") or f"entry {i}"
            errors.append(f"resolution_ledger.yaml: {label}: schema: {e.message}")

    return errors


if __name__ == "__main__":
    import sys
    errs = validate_sources(load_sources(Path(__file__).resolve().parents[1]))
    for e in errs:
        print("ERROR:", e)
    print(f"\n{len(errs)} error(s)")
    sys.exit(1 if errs else 0)
