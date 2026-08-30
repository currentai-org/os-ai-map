"""The declaration/evidence gap check: what it finds, and what it must not find."""
from pathlib import Path

from build.check_declarations import (
    RESERVED_OWNERS,
    divergent_citations,
    undeclared_citations,
)

ROOT = Path(__file__).resolve().parents[1]


def _write(tmp_path: Path, product: str, score: str) -> Path:
    (tmp_path / "sources" / "products").mkdir(parents=True)
    (tmp_path / "sources" / "scores").mkdir(parents=True)
    (tmp_path / "sources" / "products" / "p.yaml").write_text(product)
    (tmp_path / "sources" / "scores" / "p.yaml").write_text(score)
    return tmp_path


CITES = """product: p
openness:
  sources:
  - url: https://github.com/acme/thing
    establishes: [source]
"""


def test_flags_a_cited_repo_the_product_does_not_declare(tmp_path):
    root = _write(tmp_path, "name: p\ntype: software\n", CITES)
    assert undeclared_citations(root) == [("p", "acme/thing", "openness")]


def test_declaring_the_repo_clears_the_finding(tmp_path):
    root = _write(tmp_path, "name: p\ntype: software\ngithub:\n- url: https://github.com/acme/thing\n", CITES)
    assert undeclared_citations(root) == []


def test_a_citation_that_establishes_nothing_is_not_a_finding(tmp_path):
    """`establishes` is what makes a citation a claim about source. Without it there is
    nothing to reconcile against a declaration - a repo may be cited for a benchmark
    number or a blog post, which is why `codegemma` citing huggingface/blog is not a gap."""
    score = CITES.replace("    establishes: [source]\n", "")
    root = _write(tmp_path, "name: p\ntype: software\n", score)
    assert undeclared_citations(root) == []


def test_github_site_paths_are_not_repositories(tmp_path):
    """`github.com/features/copilot` matches owner/repo but is a product page. Declaring it
    would invent an artifact, so the owner segment is checked against RESERVED_OWNERS."""
    score = CITES.replace("acme/thing", "features/copilot")
    root = _write(tmp_path, "name: p\ntype: software\n", score)
    assert undeclared_citations(root) == []
    assert "features" in RESERVED_OWNERS


def test_declaring_a_different_repo_is_still_a_finding(tmp_path):
    """The false negative this module was reviewed for. Testing `github` presence alone calls
    a product clean when it declares repo A and cites repo B, which is precisely the
    artifact/evidence divergence the check exists to catch. Identities are compared."""
    root = _write(
        tmp_path,
        "name: p\ntype: software\ngithub:\n- url: https://github.com/acme/other\n",
        CITES,
    )
    assert undeclared_citations(root) == []
    assert divergent_citations(root) == [("p", "acme/thing", "openness")]


def test_case_and_git_suffix_do_not_make_a_divergence(tmp_path):
    """A declaration and a citation differing only in case or a .git suffix are one repo."""
    root = _write(
        tmp_path,
        "name: p\ntype: software\ngithub:\n- url: https://github.com/ACME/Thing.git\n",
        CITES,
    )
    assert divergent_citations(root) == []


def test_the_real_corpus_divergences_are_all_verified_renames():
    """Seven products cite the path a repository was renamed FROM. Each was checked against
    the GitHub API on 2026-08-30 and redirects to the declared repository, so none is a wrong
    artifact - the remedy is refreshing the citation or recording the move under
    artifact_exceptions.github_moved, not declaring a second repo."""
    assert {f[0] for f in divergent_citations(ROOT)} == {
        "fastmcp", "giskard", "llama-factory", "nemo-guardrails", "opencode",
        "torchtune", "verl",
    }


def test_the_real_corpus_holds_at_its_known_count():
    """Report-only today, so this pins the remaining set rather than asserting it is empty.

    Every finding is a product whose adoption route would change if the repository were
    declared, which is the decision this check cannot make for anyone. Lower it as they are
    resolved; when it reaches zero the check becomes a build.validate error.
    """
    findings = undeclared_citations(ROOT)
    assert len(findings) == 8, [f[0] for f in findings]
    assert {f[0] for f in findings} == {
        "apify", "aws-neuron", "google-cloud-run", "lamini", "predibase",
        "qualcomm-ai-engine-direct", "replit-agent-code-execution-api",
        "text-generation-inference",
    }
