"""The resolution ledger: decisions a person made, made readable by the next bulk run.

The failure this file guards is not a bug in any one module. It is that the corpus recorded
its identity and boundary decisions in pull request prose, where nothing could read them, and
the first bulk expansion duly recreated twelve repositories that #413 had already resolved -
one of them a product the corpus already carries under another name.
"""
import json
from pathlib import Path

import pytest
import yaml
import jsonschema

from build.resolution import (
    LEDGER,
    NOT_A_NEW_PRODUCT,
    RELATIONS,
    VERDICTS,
    DuplicateResolution,
    blocks_new_product,
    holds_bulk_promotion,
    load,
    membership_ruling,
    verdict_for,
)

ROOT = Path(__file__).resolve().parent.parent


def test_the_ledger_parses_and_every_verdict_is_known():
    entries = load()
    assert entries
    for (kind, ident), relation in entries.keys():
        entry = entries[((kind, ident), relation)]
        assert entry["verdict"] in VERDICTS, f"{kind}/{ident}: unknown verdict {entry['verdict']!r}"
        if kind == "github":
            assert ident == ident.lower(), "github identity is compared lowercased"
        assert len(entry.get("note") or "") > 20, f"{kind}/{ident}: a decision needs its reasoning"
        assert entry.get("decided_in"), f"{kind}/{ident}: a decision needs a provenance"


def test_a_resolved_repo_names_what_it_resolved_to():
    """`existing_product` and `sku_of` point at a product; `excluded_boundary` names a boundary.
    Without that an entry blocks a candidate while saying nothing about why."""
    for (kind, ident), relation in load().keys():
        entry = load()[((kind, ident), relation)]
        if entry["verdict"] in ("existing_product", "sku_of"):
            assert entry.get("product") or entry.get("resolves_to"), \
                f"{kind}/{ident}: {entry['verdict']} must name a product"
        if entry["verdict"] == "excluded_boundary":
            assert entry.get("boundary") or entry.get("note")


def test_named_products_exist_in_the_corpus():
    """A ledger pointing at a slug the corpus dropped is stale, and would block a candidate
    on the authority of a product that is no longer there."""
    slugs = {p.stem for p in (ROOT / "sources" / "products").glob("*.yaml")}
    missing = {
        key: (e.get("product") or e.get("resolves_to"))
        for key, e in load().items()
        if (e.get("product") or e.get("resolves_to")) and (e.get("product") or e.get("resolves_to")) not in slugs
    }
    assert not missing, f"ledger points at products that do not exist: {missing}"


@pytest.mark.parametrize("repo,verdict,target", [
    ("a2aproject/A2A", "existing_product", "agent2agent-protocol"),
    ("firecrawl/firecrawl-mcp-server", "sku_of", "firecrawl"),
    ("anthropics/knowledge-work-plugins", "excluded_boundary", None),
    ("promptslab/Awesome-Prompt-Engineering", "excluded_boundary", None),
])
def test_the_four_cases_that_produced_this_file(repo, verdict, target):
    """Named individually because each was recreated as a product by a bulk run that could
    not see the decision. A regression here is the whole failure coming back."""
    entry = blocks_new_product("github", repo)
    assert entry is not None, f"{repo} must be blocked from becoming a new product"
    assert entry["verdict"] == verdict
    if target:
        assert entry["product"] == target


def test_a_repository_may_be_resolved_only_once(tmp_path):
    """Governance state has no benign duplicate.

    `load` used to be a dict comprehension, so two entries for one repository resolved
    last-write-wins and the stronger decision vanished silently. The file is hand-edited by
    people appending after each review, which is precisely how a second entry appears - and
    docs/reference/identity.md records the same failure in the deleted slug-alias mapping.
    """
    ledger = tmp_path / "resolution_ledger.yaml"
    ledger.write_text(
        "version: 1\nresolutions:\n"
        "- repo: Foo/Bar\n  verdict: existing_product\n  product: x\n"
        "  decided_in: '#1'\n  decided_on: '2026-08-01'\n  note: the first decision, which must not be lost\n"
        "- repo: foo/bar.git\n  verdict: unresolved\n"
        "  decided_in: '#2'\n  decided_on: '2026-08-02'\n  note: a later entry for the same repository, differently cased\n"
    )
    with pytest.raises(DuplicateResolution) as raised:
        load(ledger)
    assert "Foo/Bar" in str(raised.value) or "foo/bar" in str(raised.value) or "foo/bar" in str(raised.value).lower()


LEDGER_FLOOR = 302  # trued up 2026-09-03 from 291; the ratchet below requires exact equality


def test_the_ledger_never_shrinks_and_the_floor_moves_with_it():
    """Uniqueness protects identity integrity. It does not protect completeness.

    Three per-category tranches ran serially in one session, and each rebase conflicted on
    this file because every pass appends to it. The tempting resolution is to take one side.
    Doing so would have been invisible to every other guard here: dropping the two entries
    #431 appended (`tinker-cookbook`, `mlx-vlm`) produces no duplicate, leaves the four
    sentinel cases below intact, and loads clean. Two governance decisions would simply have
    been gone, and the next bulk run would have recreated both.

    So the ledger needs a second property alongside uniqueness: it is append-only, and a
    resolution once recorded stays recorded. A count floor is the cheap form of that. Now an
    exact-equality ratchet rather than a `>=` floor: a PR that appends N entries raises the
    floor by N in the same PR (#437), so drift in either direction fails here immediately
    rather than accumulating silently until the next true-up.

    Correct resolution when this file conflicts: keep BOTH sides. Every entry is an append.
    """
    n = len(yaml.safe_load(LEDGER.read_text())["resolutions"])
    assert n == LEDGER_FLOOR, (
        f"ledger has {n} entries but LEDGER_FLOOR is {LEDGER_FLOOR}; a PR that appends N entries "
        f"raises the floor by N in the same PR (#437)")


def test_the_real_ledger_has_no_duplicate_identity():
    """Asserted against the file itself, so appending a second entry fails here."""
    assert load()


def test_unresolved_holds_a_bulk_promotion_even_though_it_does_not_block_forever():
    """The distinction that #420 got wrong.

    `unresolved` means "this may come back to a later sweep", not "this proposal may publish".
    The #418 review recorded ag-ui as a protocol filed under agent frameworks, serena as an MCP
    retrieval toolkit and repomix as document ingestion - and the same run then published all
    three in orchestration_agents, the category the entries say is wrong. A bulk run must park
    them; a person may still resolve and add them by hand, which is why validate does not fail.
    """
    for repo in ("ag-ui-protocol/ag-ui", "oraios/serena", "yamadashy/repomix"):
        assert blocks_new_product("github", repo) is None, f"{repo}: must not be a hard build error"
        held = holds_bulk_promotion("github", repo)
        assert held is not None, f"{repo}: a bulk run must park it"
        assert held["verdict"] == "unresolved"


def test_a_repo_with_no_entry_is_eligible():
    """The other side of the hold: silence in the ledger is permission."""
    assert holds_bulk_promotion("github", "vllm-project/vllm") is None


def test_unresolved_does_not_block():
    """`unresolved` means a person still has to look. A rerun proposing the repository again
    is the intended behaviour, so it must not be enforced like a decision."""
    assert "unresolved" not in NOT_A_NEW_PRODUCT
    unresolved = [(kind, ident) for ((kind, ident), relation), e in load().items() if e["verdict"] == "unresolved"]
    for kind, ident in unresolved:
        assert blocks_new_product(kind, ident) is None


def test_no_product_declares_a_repo_the_ledger_resolves_elsewhere():
    """The corpus-wide invariant build/validate.py enforces, asserted here too so the failure
    names the products rather than only the count."""
    ledger = load()
    offences = []
    for path in sorted((ROOT / "sources" / "products").glob("*.yaml")):
        product = yaml.safe_load(path.read_text()) or {}
        for artifact in (product.get("github") or []):
            url = (artifact.get("url") or "").rstrip("/")
            if "github.com/" not in url:
                continue
            repo = url.split("github.com/")[-1].removesuffix(".git").lower()
            entry = verdict_for("github", repo, "product_equivalence", ledger)
            resolved_to = entry.get("product") or entry.get("resolves_to") if entry else None
            if entry and entry["verdict"] in NOT_A_NEW_PRODUCT and resolved_to != path.stem:
                offences.append(f"{path.stem} declares {repo} ({entry['verdict']})")
    assert not offences, offences


ALLOWED_KEYS = {"repo", "artifact", "verdict", "relation", "product", "resolves_to",
                "boundary", "decided_in", "decided_on", "note"}


def test_the_ledger_is_hand_maintainable():
    """It is a source file a person edits, so it stays legible: one flat list, no nesting."""
    doc = yaml.safe_load(LEDGER.read_text())
    assert doc["version"] == 1
    assert isinstance(doc["resolutions"], list)
    for e in doc["resolutions"]:
        assert set(e) <= ALLOWED_KEYS, sorted(set(e) - ALLOWED_KEYS)


def test_every_entry_validates_against_the_schema():
    schema = json.loads((ROOT / "docs" / "schemas" / "resolution_ledger.schema.json").read_text())
    for e in yaml.safe_load(LEDGER.read_text())["resolutions"]:
        jsonschema.validate(e, schema)


def test_keys_are_kind_and_canonical_id():
    ledger = load()
    for ((kind, ident), relation), entry in ledger.items():
        assert kind in {"github", "huggingface_model", "huggingface_dataset", "pypi", "npm",
                         "crates", "arxiv", "homepage"}
        assert relation in RELATIONS
        if kind == "github":
            assert ident == ident.lower() and not ident.endswith(".git")


def test_relation_defaults_to_equivalence_for_legacy_entries():
    ledger = load()
    assert all(e.get("relation", "product_equivalence") in RELATIONS for e in ledger.values())


def test_a_membership_ruling_does_not_suppress_an_equivalence_question(tmp_path):
    path = tmp_path / "ledger.yaml"
    path.write_text(yaml.safe_dump({"version": 1, "resolutions": [{
        "artifact": {"kind": "pypi", "id": "elasticsearch"}, "verdict": "not_member_of",
        "relation": "product_membership", "resolves_to": "elasticsearch",
        "decided_in": "#472", "decided_on": "2026-09-15",
        "note": "elasticsearch-py is the client of the Java engine; its downloads are not this product's"}]}))
    ledger = load(path)
    assert membership_ruling("pypi", "elasticsearch", "elasticsearch", ledger)["verdict"] == "not_member_of"
    assert blocks_new_product("pypi", "elasticsearch", ledger) is None
    assert holds_bulk_promotion("pypi", "elasticsearch", ledger) is None


def test_verdict_for_strips_git_suffix_like_load_does():
    ledger = {(("github", "foo/bar"), "product_equivalence"): {"verdict": "unresolved"}}
    assert verdict_for("github", "Foo/Bar.git", "product_equivalence", ledger) is not None
