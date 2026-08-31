"""The resolution ledger: decisions a person made, made readable by the next bulk run.

The failure this file guards is not a bug in any one module. It is that the corpus recorded
its identity and boundary decisions in pull request prose, where nothing could read them, and
the first bulk expansion duly recreated twelve repositories that #413 had already resolved -
one of them a product the corpus already carries under another name.
"""
from pathlib import Path

import pytest
import yaml

from build.resolution import LEDGER, NOT_A_NEW_PRODUCT, VERDICTS, blocks_new_product, load

ROOT = Path(__file__).resolve().parents[1]


def test_the_ledger_parses_and_every_verdict_is_known():
    entries = load()
    assert entries
    for repo, entry in entries.items():
        assert entry["verdict"] in VERDICTS, f"{repo}: unknown verdict {entry['verdict']!r}"
        assert repo == repo.lower(), "keys are lowercased for identity comparison"
        assert len(entry.get("note") or "") > 20, f"{repo}: a decision needs its reasoning"
        assert entry.get("decided_in"), f"{repo}: a decision needs a provenance"


def test_a_resolved_repo_names_what_it_resolved_to():
    """`existing_product` and `sku_of` point at a product; `excluded_boundary` names a boundary.
    Without that an entry blocks a candidate while saying nothing about why."""
    for repo, entry in load().items():
        if entry["verdict"] in ("existing_product", "sku_of"):
            assert entry.get("product"), f"{repo}: {entry['verdict']} must name a product"
        if entry["verdict"] == "excluded_boundary":
            assert entry.get("boundary") or entry.get("note")


def test_named_products_exist_in_the_corpus():
    """A ledger pointing at a slug the corpus dropped is stale, and would block a candidate
    on the authority of a product that is no longer there."""
    slugs = {p.stem for p in (ROOT / "sources" / "products").glob("*.yaml")}
    missing = {repo: e["product"] for repo, e in load().items()
               if e.get("product") and e["product"] not in slugs}
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
    entry = blocks_new_product(repo)
    assert entry is not None, f"{repo} must be blocked from becoming a new product"
    assert entry["verdict"] == verdict
    if target:
        assert entry["product"] == target


def test_unresolved_does_not_block():
    """`unresolved` means a person still has to look. A rerun proposing the repository again
    is the intended behaviour, so it must not be enforced like a decision."""
    assert "unresolved" not in NOT_A_NEW_PRODUCT
    unresolved = [r for r, e in load().items() if e["verdict"] == "unresolved"]
    for repo in unresolved:
        assert blocks_new_product(repo) is None


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
            entry = ledger.get(repo)
            if (entry and entry["verdict"] in NOT_A_NEW_PRODUCT
                    and entry.get("product") != path.stem):
                offences.append(f"{path.stem} declares {repo} ({entry['verdict']})")
    assert not offences, offences


def test_the_ledger_is_hand_maintainable():
    """It is a source file a person edits, so it stays legible: one flat list, no nesting."""
    doc = yaml.safe_load(LEDGER.read_text())
    assert doc["version"] == 1
    assert isinstance(doc["resolutions"], list)
    assert all(isinstance(e, dict) and set(e) <= {
        "repo", "verdict", "product", "boundary", "decided_in", "decided_on", "note"}
        for e in doc["resolutions"])
