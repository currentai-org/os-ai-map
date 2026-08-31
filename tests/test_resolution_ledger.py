"""The resolution ledger: decisions a person made, made readable by the next bulk run.

The failure this file guards is not a bug in any one module. It is that the corpus recorded
its identity and boundary decisions in pull request prose, where nothing could read them, and
the first bulk expansion duly recreated twelve repositories that #413 had already resolved -
one of them a product the corpus already carries under another name.
"""
from pathlib import Path

import pytest
import yaml

from build.resolution import (
    LEDGER,
    NOT_A_NEW_PRODUCT,
    VERDICTS,
    DuplicateResolution,
    blocks_new_product,
    holds_bulk_promotion,
    load,
)

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
        "  decided_in: '#1'\n  note: the first decision, which must not be lost\n"
        "- repo: foo/bar.git\n  verdict: unresolved\n"
        "  decided_in: '#2'\n  note: a later entry for the same repository, differently cased\n"
    )
    with pytest.raises(DuplicateResolution) as raised:
        load(ledger)
    assert "Foo/Bar" in str(raised.value) or "foo/bar" in str(raised.value)


#: Floor on the number of recorded decisions. Raise it deliberately when a pass appends;
#: never lower it. Deliberately a hand-written constant rather than derived from the file:
#: a floor that computes itself from the current ledger would happily derive 289 from a
#: damaged one and prove itself correct. The independent number is what gives this test
#: memory. 291 after the three 2026-08-31 category passes.
LEDGER_FLOOR = 291


def test_the_ledger_never_shrinks():
    """Uniqueness protects identity integrity. It does not protect completeness.

    Three per-category tranches ran serially in one session, and each rebase conflicted on
    this file because every pass appends to it. The tempting resolution is to take one side.
    Doing so would have been invisible to every other guard here: dropping the two entries
    #431 appended (`tinker-cookbook`, `mlx-vlm`) produces no duplicate, leaves the four
    sentinel cases below intact, and loads clean. Two governance decisions would simply have
    been gone, and the next bulk run would have recreated both.

    So the ledger needs a second property alongside uniqueness: it is append-only, and a
    resolution once recorded stays recorded. A count floor is the cheap form of that. A digest
    over the whole key set would also catch a swap, but it would change on every legitimate
    append and so would be noise rather than signal - and a swap is not how a side-pick fails.
    A side-pick drops a block.

    Correct resolution when this file conflicts: keep BOTH sides. Every entry is an append.

    Deliberately a floor and not a set of named entries. Pinning the specific decisions a
    given pass appended would couple this test to the order those passes merge in, which is
    the one thing a serialized queue cannot promise.
    """
    entries = load()
    assert len(entries) >= LEDGER_FLOOR, (
        f"the ledger holds {len(entries)} decisions, below the floor of {LEDGER_FLOOR}. "
        "A resolution that was recorded has been lost - most likely a merge or rebase that "
        "took one side of a conflict in this file instead of merging both. Recover the "
        "missing entries from git history rather than lowering this number: "
        "`git log -p --follow sources/resolution_ledger.yaml`. Raise the floor only when a "
        "pass has legitimately appended."
    )


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
        assert blocks_new_product(repo) is None, f"{repo}: must not be a hard build error"
        held = holds_bulk_promotion(repo)
        assert held is not None, f"{repo}: a bulk run must park it"
        assert held["verdict"] == "unresolved"


def test_a_repo_with_no_entry_is_eligible():
    """The other side of the hold: silence in the ledger is permission."""
    assert holds_bulk_promotion("vllm-project/vllm") is None


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
