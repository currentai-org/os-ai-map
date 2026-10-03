"""Tests for the artifact drift check.

No network. What needs testing is the judgment, not the fetching: which disagreements
count as drift, which are the artifact's own metadata being stale, and which are waived.

Every case here is one this check was written to catch or was caught getting wrong on its
first run against the real corpus.
"""

import build.check_artifacts as artifacts
from build.propose_artifacts import stub_reason


def product(github=None, pypi=None, exceptions=None):
    out = {}
    if github:
        repos = [github] if isinstance(github, str) else github
        out["github"] = [{"url": f"https://github.com/{r}"} for r in repos]
    if pypi:
        out["pypi"] = [{"url": f"https://pypi.org/project/{pypi}"}]
    if exceptions:
        out["artifact_exceptions"] = exceptions
    return out


def test_a_moved_repo_is_a_finding(monkeypatch):
    """The #166 shape: the declaration names a path that now redirects elsewhere."""
    monkeypatch.setattr(artifacts, "query", lambda _sql: [
        {"product_slug": "swe-bench", "repo": "princeton-nlp/SWE-bench",
         "resolved_repo": "SWE-bench/SWE-bench"},
    ])
    found = artifacts.github_moved({"swe-bench": product(github="princeton-nlp/SWE-bench")})
    assert found == [("swe-bench", "princeton-nlp/SWE-bench", "SWE-bench/SWE-bench")]


def test_a_repo_already_corrected_is_not_a_finding(monkeypatch):
    """After the fix lands, the signal still carries the redirect row until it re-runs.

    Comparing against `resolved_repo` rather than the signal's own `repo` column is what
    makes the check quiet once the declaration is right, instead of nagging for a week.
    """
    monkeypatch.setattr(artifacts, "query", lambda _sql: [
        {"product_slug": "swe-bench", "repo": "princeton-nlp/SWE-bench",
         "resolved_repo": "SWE-bench/SWE-bench"},
    ])
    assert artifacts.github_moved({"swe-bench": product(github="SWE-bench/SWE-bench")}) == []


def test_case_alone_is_not_drift(monkeypatch):
    monkeypatch.setattr(artifacts, "query", lambda _sql: [
        {"product_slug": "x", "repo": "Foo/Bar", "resolved_repo": "foo/bar"},
    ])
    assert artifacts.github_moved({"x": product(github="Foo/Bar")}) == []



E2B = "e2b-dev/E2B"


def test_a_moved_second_repo_is_named_rather_than_the_first(monkeypatch):
    """e2b-sandbox declares its SDK first and its runtime second, and the runtime moved.

    Comparing the redirect against only the first declaration reported e2b-dev/E2B, which
    never moved, as the drifted artifact.
    """
    monkeypatch.setattr(artifacts, "query", lambda _sql: [
        {"product_slug": "e2b-sandbox", "repo": "e2b-dev/infra", "resolved_repo": "e2b-dev/runtime"},
    ])
    found = artifacts.github_moved({"e2b-sandbox": product(github=[E2B, "e2b-dev/infra"])})
    assert found == [("e2b-sandbox", "e2b-dev/infra", "e2b-dev/runtime")]


def test_a_corrected_second_repo_goes_quiet(monkeypatch):
    """Once the second declaration names the new path, the stale redirect row is not a finding."""
    monkeypatch.setattr(artifacts, "query", lambda _sql: [
        {"product_slug": "e2b-sandbox", "repo": "e2b-dev/infra", "resolved_repo": "e2b-dev/runtime"},
    ])
    products = {"e2b-sandbox": product(github=[E2B, "e2b-dev/runtime"])}
    assert artifacts.github_moved(products) == []



def test_declaring_the_new_path_beside_the_old_one_is_still_a_finding(monkeypatch):
    """The old path stays a join key while it is declared, wherever the new one sits."""
    monkeypatch.setattr(artifacts, "query", lambda _sql: [
        {"product_slug": "e2b-sandbox", "repo": "e2b-dev/infra", "resolved_repo": "e2b-dev/runtime"},
    ])
    products = {"e2b-sandbox": product(github=[E2B, "e2b-dev/infra", "e2b-dev/runtime"])}
    assert artifacts.github_moved(products) == [("e2b-sandbox", "e2b-dev/infra", "e2b-dev/runtime")]


def test_a_row_for_a_path_no_longer_declared_is_quiet(monkeypatch):
    """Neither the old path nor the new one is declared: the declaration moved on elsewhere."""
    monkeypatch.setattr(artifacts, "query", lambda _sql: [
        {"product_slug": "e2b-sandbox", "repo": "e2b-dev/infra", "resolved_repo": "e2b-dev/runtime"},
    ])
    assert artifacts.github_moved({"e2b-sandbox": product(github=[E2B])}) == []


def test_a_package_matching_the_second_repo_after_a_rename_is_not_drift(monkeypatch):
    """The canonical comparison must reach every declared repo, not only the first."""
    monkeypatch.setattr(artifacts, "pypi_info", lambda _p: {"version": "2.4.0", "summary": "runtime"})
    monkeypatch.setattr(artifacts, "stub_reason", lambda *a, **k: None)
    monkeypatch.setattr(artifacts, "declared_repo", lambda *a, **k: "e2b-dev/infra")
    renamed = {"e2b-dev/infra": "e2b-dev/runtime"}
    monkeypatch.setattr(artifacts, "canonical_repo", lambda repo: renamed.get(repo.lower(), repo.lower()))
    products = {"e2b-sandbox": product(github=[E2B, "e2b-dev/runtime"], pypi="e2b")}
    assert artifacts.pypi_content(products) == ([], [])

def test_a_package_naming_any_declared_repo_is_not_drift(monkeypatch):
    """A package published from the product's second repository names that repository.

    Only a repo the product declares none of is a mismatch, and agreeing with one of them
    needs no GitHub lookup.
    """
    monkeypatch.setattr(artifacts, "pypi_info", lambda _p: {"version": "2.4.0", "summary": "runtime"})
    monkeypatch.setattr(artifacts, "stub_reason", lambda *a, **k: None)
    monkeypatch.setattr(artifacts, "declared_repo", lambda *a, **k: "e2b-dev/runtime")

    def no_lookup(repo):
        raise AssertionError(f"looked up {repo} although the package names a declared repo")

    monkeypatch.setattr(artifacts, "canonical_repo", no_lookup)
    products = {"e2b-sandbox": product(github=[E2B, "e2b-dev/runtime"], pypi="e2b")}
    assert artifacts.pypi_content(products) == ([], [])

def test_stub_versions_are_caught_and_a_real_release_is_not():
    """The #167 shape. `info` is passed in, so this makes no request."""
    assert stub_reason("pypi", "openmanus",
                       info={"version": "0.1.0", "summary": "Add your description here"})
    assert stub_reason("pypi", "nemo-rl", info={"version": "0.0.0", "summary": "NeMo RL"})
    assert stub_reason("pypi", "vllm", info={"version": "0.11.2", "summary": "A serving engine"}) is None


def test_an_empty_summary_is_not_a_stub():
    """This check's first false-positive class, on its first real run.

    safetensors, tokenizers and cohere all publish an empty summary and are among the
    most-downloaded packages in the corpus. Only the scaffolded placeholder string counts.
    """
    assert stub_reason("pypi", "safetensors", info={"version": "0.6.2", "summary": ""}) is None
    assert stub_reason("pypi", "tokenizers", info={"version": "0.21.0", "summary": None}) is None


def test_a_package_naming_a_stale_repo_is_not_drift(monkeypatch):
    """A package's metadata goes stale exactly as our declarations did.

    torchtune's PyPI metadata still names pytorch/torchtune, which is the path #166
    corrected here. Resolving through GitHub's rename makes the two agree, so the finding
    would be reporting that WE are current.
    """
    monkeypatch.setattr(artifacts, "pypi_info", lambda _p: {"version": "0.6.1", "summary": "recipes"})
    monkeypatch.setattr(artifacts, "stub_reason", lambda *a, **k: None)
    monkeypatch.setattr(artifacts, "declared_repo", lambda *a, **k: "pytorch/torchtune")
    monkeypatch.setattr(artifacts, "canonical_repo", lambda repo: "meta-pytorch/torchtune")
    products = {"torchtune": product(github="meta-pytorch/torchtune", pypi="torchtune")}
    stubs, mismatches = artifacts.pypi_content(products)
    assert (stubs, mismatches) == ([], [])


def test_a_package_naming_a_genuinely_different_project_is_drift(monkeypatch):
    monkeypatch.setattr(artifacts, "pypi_info", lambda _p: {"version": "0.1.0", "summary": "x"})
    monkeypatch.setattr(artifacts, "stub_reason", lambda *a, **k: None)
    monkeypatch.setattr(artifacts, "declared_repo", lambda *a, **k: "mannaandpoem/openmanus")
    monkeypatch.setattr(artifacts, "canonical_repo", lambda repo: repo)
    products = {"openmanus": product(github="foundationagents/openmanus", pypi="openmanus")}
    _stubs, mismatches = artifacts.pypi_content(products)
    assert [m[0] for m in mismatches] == ["openmanus"]


def test_a_waiver_silences_its_own_check_only():
    """A client package for a server product is legitimate; the waiver names why.

    Scoped per check, so waiving the repo mismatch does not also waive a future stub.
    """
    waived = product(github="qdrant/qdrant", pypi="qdrant-client",
                     exceptions={"pypi_repo_mismatch": "qdrant-client is the Python client."})
    assert artifacts.waived(waived, "pypi_repo_mismatch")
    assert artifacts.waived(waived, "pypi_stub") is None


def test_missing_metadata_is_not_a_mismatch(monkeypatch):
    """Absence of evidence. megatron-core names no repo at all and is still correct."""
    monkeypatch.setattr(artifacts, "pypi_info", lambda _p: {"version": "0.15.0", "summary": "core"})
    monkeypatch.setattr(artifacts, "stub_reason", lambda *a, **k: None)
    monkeypatch.setattr(artifacts, "declared_repo", lambda *a, **k: None)
    products = {"megatron-lm": product(github="NVIDIA/Megatron-LM", pypi="megatron-core")}
    assert artifacts.pypi_content(products) == ([], [])
