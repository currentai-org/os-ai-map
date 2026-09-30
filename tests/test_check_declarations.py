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


def test_a_raw_file_url_names_its_repository(tmp_path):
    """A README or LICENSE cited by its raw.githubusercontent.com URL names the same repository
    as its github.com page. Matching only the page let apify's finding vanish when its Crawlee
    evidence was re-cited by raw URL, which hid the gap without resolving it."""
    score = CITES.replace(
        "https://github.com/acme/thing", "https://raw.githubusercontent.com/acme/thing/main/README.md"
    )
    root = _write(tmp_path, "name: p\ntype: software\n", score)
    assert undeclared_citations(root) == [("p", "acme/thing", "openness")]
    declared = _write(
        tmp_path / "declared", "name: p\ntype: software\ngithub:\n- url: https://github.com/acme/thing\n", score
    )
    assert undeclared_citations(declared) == []


def test_one_repository_cited_twice_is_one_finding(tmp_path):
    """The page and a raw file of one repository on one axis are one gap, so keeping a
    github.com citation beside a raw one does not double the count."""
    score = CITES + """  - url: https://raw.githubusercontent.com/acme/thing/main/LICENSE
    establishes: [source]
"""
    root = _write(tmp_path, "name: p\ntype: software\n", score)
    assert undeclared_citations(root) == [("p", "acme/thing", "openness")]


def test_the_real_corpus_divergences_are_renames():
    """Seven products cite the path a repository was renamed FROM. Each was checked against
    the GitHub API on 2026-08-30 and redirects to the declared repository, so none is a wrong
    artifact - the remedy is refreshing the citation or recording the move under
    artifact_exceptions.github_moved, not declaring a second repo.

    Two more surfaced when raw file URLs began to count (#773), and neither is verified yet:
    `e2b-sandbox` cites e2b-dev/runtime beside its declared e2b-dev/infra, whose README calls
    itself "the open-source runtime", and `sandbox-runtime` cites anthropics/sandbox-runtime
    beside its declared anthropic-experimental/sandbox-runtime, with the two package.json
    citations naming opposite paths. Both look like moves; confirm against the API before
    recording either one.
    """
    assert {f[0] for f in divergent_citations(ROOT)} == {
        "e2b-sandbox", "fastmcp", "giskard", "llama-factory", "nemo-guardrails", "opencode",
        "sandbox-runtime", "torchtune", "verl",
    }


def test_the_real_corpus_holds_at_its_known_count():
    """Report-only today, so this pins the remaining set rather than asserting it is empty.

    Every finding is a product whose adoption route would change if the repository were
    declared, which is the decision this check cannot make for anyone. Lower it as they are
    resolved; when it reaches zero the check becomes a build.validate error.

    Counting raw file URLs (#773) raised it from 8 citations to 25 across 23 products, because
    kaggle-models and vals-ai each cite two repositories. Most of the new ones are a closed
    hosted service citing its own client SDK, docs or runner repository to show that the
    service's code is NOT there. That is evidence against open source, not a missing
    declaration. Only agent2agent-protocol and model-context-protocol cite their own source.
    """
    findings = undeclared_citations(ROOT)
    assert len(findings) == 25, [f[0] for f in findings]
    assert {f[0] for f in findings} == {
        "agent2agent-protocol", "apify", "aws-neuron", "chatbot-arena", "cloudflare-sandboxes",
        "cursor", "datadog-llm-observability", "exa-search-api", "google-cloud-run",
        "huggingface-hub-platform", "kaggle-models", "lamini", "model-context-protocol",
        "modelscope", "ollama-library", "patronus-evaluation-platform", "predibase",
        "qualcomm-ai-engine-direct", "ragaai-catalyst", "replit-agent-code-execution-api",
        "tavily-search-api", "text-generation-inference", "vals-ai",
    }
