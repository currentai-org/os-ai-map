"""The package-channel report (#426): what it finds, what it refuses to say, and what it reads
first. Every registry answer here comes from `tests/fixtures/package_channel/`; the fetch seam
is replaced and any URL not in the fixture map is a test failure, so nothing reaches the network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from build import check_package_channel as cpc
from build.check_package_channel import (
    Candidate,
    assess,
    extract_candidates,
    grade_ownership,
    label_role,
    prior_judgment,
    read_crates,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "package_channel"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


def _pypi(name: str, last_month=None, stats_status: int = 200, transient: bool = False) -> dict:
    """The two URLs a PyPI candidate touches, from a trimmed fixture."""
    stats = (200, json.dumps({"data": {"last_month": last_month}}), False)
    if stats_status != 200:
        stats = (stats_status, None, transient)
    return {
        f"https://pypi.org/pypi/{name}/json": (200, _fixture(f"pypi_{name}.json"), False),
        f"https://pypistats.org/api/packages/{name}/recent": stats,
    }


def _docker(namespace: str, name: str) -> dict:
    return {f"https://hub.docker.com/v2/repositories/{namespace}/{name}/": (200, _fixture(f"docker_{namespace}_{name}.json"), False)}


@pytest.fixture
def registry(monkeypatch):
    """Install a URL -> (status, body, transient) map as the only fetcher. An unmapped URL
    fails the test: that is the no-network guarantee."""
    answers: dict[str, tuple] = {}

    def fake_fetch_text(url, retries=cpc.REGISTRY_RETRIES):
        if url not in answers:
            raise AssertionError(f"unexpected fetch of {url}; tests must not reach the network")
        return answers[url]

    def no_network(*_args, **_kwargs):
        raise AssertionError("fetch_source.fetch reached; tests must not reach the network")

    monkeypatch.setattr(cpc, "fetch_text", fake_fetch_text)
    monkeypatch.setattr(cpc, "fetch", no_network)
    monkeypatch.setattr(cpc, "_PACE", 0.0)
    return answers


def _product(slug: str, repo: str, description: str = "", **artifacts) -> dict:
    product = {"name": slug, "display_name": slug, "description": description,
               "github": [{"url": f"https://github.com/{repo}"}]}
    for kind, names in artifacts.items():
        product[kind] = [{"url": f"https://pypi.org/project/{n}"} for n in names]
    return product


def _score(note: str = "", reach: str = "1K-10K stars", level: int = 2) -> dict:
    return {"adoption": {"level": level, "reach": reach, "signal_type": "stars_fallback", "note": note}}


def _by_name(findings, kind, name):
    matches = [f for f in findings if f.candidate.kind == kind and f.candidate.name == name]
    assert len(matches) == 1, [(f.candidate.kind, f.candidate.name) for f in findings]
    return matches[0]


# ----------------------------------------------------------------------------------------------
# Candidate extraction: what an install line yields, and what it must not.


def test_bigcodebench_install_line_does_not_yield_packaging():
    """#426 failure 1: `pip install bigcodebench packaging` produced `packaging` at 2.19 billion
    monthly downloads. The dependency is dropped; the product survives."""
    product = _product("bigcodebench", "bigcode-project/bigcodebench")
    names = [(c.kind, c.name) for c in extract_candidates(_fixture("readme_bigcodebench.md"), product)]
    assert ("pypi", "bigcodebench") in names
    assert ("pypi", "packaging") not in names


def test_simple_evals_yields_no_package_at_all():
    """`pip install openai` and `pip install -e human-eval` install a dependency and a local
    path. Neither is simple-evals, which has no distribution."""
    product = _product("simple-evals", "openai/simple-evals")
    assert extract_candidates(_fixture("readme_simple-evals.md"), product) == []


def test_a_stop_listed_name_is_kept_when_it_is_the_product():
    product = _product("vllm", "vllm-project/vllm")
    names = [c.name for c in extract_candidates("```\npip install vllm\n```\n", product)]
    assert names == ["vllm"]


def test_prose_is_not_an_install_line():
    """Only code is read. Treating "run `pip install tensorlake` for the Python SDK, install
    the CLI" as a command yielded `for`, `the`, `install` and `first` - and `first` is a
    real package at 665K downloads a month."""
    product = _product("tensorlake-sandbox", "tensorlakeai/tensorlake")
    names = [c.name for c in extract_candidates(_fixture("readme_tensorlake.md"), product)]
    assert names == ["tensorlake"]


def test_flags_versions_extras_paths_and_vcs_are_not_packages():
    readme = "\n".join([
        "```",
        "pip install -U 'uzu[all]>=0.5' --index-url https://example.invalid/simple",
        "pip install -r requirements.txt",
        "pip install git+https://github.com/trymirai/uzu",
        "pip install .",
        "pip install ./sdk",
        "```",
    ])
    names = [(c.kind, c.name) for c in extract_candidates(readme, _product("uzu", "trymirai/uzu"))]
    assert names == [("pypi", "uzu")]


def test_a_comment_line_inside_a_code_block_is_not_a_command():
    """scgpt's README, verbatim: the full run produced `may`, `not`, `run`, `with` ... as PyPI
    candidates from this comment, and `may` has 306 downloads a month."""
    readme = ("```bash\n"
              "pip install scgpt \"flash-attn<1.0.5\"  # optional, recommended\n"
              "# As of 2023.09, pip install may not run with new versions of the google orbax package, "
              "if you encounter related issues, please use the following command instead:\n"
              "# pip install scgpt \"flash-attn<1.0.5\" \"orbax<0.1.8\"\n```\n")
    assert [(c.kind, c.name) for c in extract_candidates(readme, _product("scgpt", "bowang-lab/scGPT"))] == [("pypi", "scgpt")]


def test_a_subshell_and_a_pipe_after_the_package_are_cut():
    """pgvectorscale's README, verbatim: `metadata`, `1` and `jq` were reported as crates."""
    line = ("```\ncargo install --locked cargo-pgrx --version $(cargo metadata --format-version 1 | "
            "jq -r '.packages[] | select(.name == \"pgrx\") | .version')\n```\n")
    assert [(c.kind, c.name) for c in extract_candidates(line, _product("pgvectorscale", "timescale/pgvectorscale"))] == [("crates", "cargo-pgrx")]


def test_docker_run_and_pull_yield_the_image_without_its_tag():
    product = _product("typesense", "typesense/typesense")
    names = [(c.kind, c.name) for c in extract_candidates(_fixture("readme_typesense.md"), product)]
    assert ("docker", "typesense/typesense") in names
    assert ("pypi", "typesense") in names
    assert not any(n.endswith(":29.0") for _k, n in names)


def test_npm_scoped_and_cargo_names_are_taken():
    readme = "```\nnpm i -g @trymirai/uzu@0.5.26\ncargo add uzu serde\n```\n"
    names = [(c.kind, c.name) for c in extract_candidates(readme, _product("uzu", "trymirai/uzu"))]
    assert names == [("npm", "@trymirai/uzu"), ("crates", "uzu")]


# ----------------------------------------------------------------------------------------------
# Identity: the full owner/repo path or a name, never an owner substring.


def _meta(fixture: str) -> dict:
    info = json.loads(_fixture(fixture))["info"]
    urls = dict(info.get("project_urls") or {})
    if info.get("home_page"):
        urls.setdefault("home_page", info["home_page"])
    return {"summary": info.get("summary"), "author": info.get("author") or info.get("author_email"), "urls": urls}


def test_openai_package_does_not_belong_to_openai_simple_evals():
    """#426 failure 2. The package's URLs are github.com/openai/openai-python and its author is
    OpenAI; the product is openai/simple-evals. Sharing an owner is not ownership."""
    grade, evidence = grade_ownership(_meta("pypi_openai.json"), _product("simple-evals", "openai/simple-evals"))
    assert grade == "none"
    assert "simple-evals" in evidence


def test_full_repo_path_is_strong():
    grade, evidence = grade_ownership(_meta("pypi_uzu.json"), _product("uzu", "trymirai/uzu"))
    assert grade == "strong"
    assert "trymirai/uzu" in evidence


def test_a_url_under_the_declared_repo_tree_is_strong():
    """lakefs's PyPI homepage is github.com/treeverse/lakeFS/tree/master/clients/python-wrapper -
    the declared repository, a sub-path of it. Identity holds; ROLE is where it is a wrapper."""
    grade, _ = grade_ownership(_meta("pypi_lakefs.json"), _product("lakefs", "treeverse/lakeFS"))
    assert grade == "strong"


def test_sibling_repo_that_names_the_project_is_weak_not_strong():
    """typesense-python and otari-sdk-python sit under the declared owner in a DIFFERENT
    repository. The name rule grades them weak and says why; the owner match is not used."""
    grade, evidence = grade_ownership(_meta("pypi_typesense.json"), _product("typesense", "typesense/typesense"))
    assert grade == "weak"
    assert "names the project" in evidence and "no link to the declared repository" in evidence
    grade, _ = grade_ownership(_meta("pypi_otari.json"), _product("otari", "mozilla-ai/otari"))
    assert grade == "weak"


def test_tensorflow_serving_api_is_weak_through_homepage():
    """The #426 boundary case: ownership only through `home_page: tensorflow.org/serving` and
    `author: Google Inc.`; a repository-link check rejects it, so it grades weak with the
    evidence named."""
    grade, evidence = grade_ownership(_meta("pypi_tensorflow-serving-api.json"),
                                      _product("tensorflow-serving", "tensorflow/serving"))
    assert grade == "weak"
    assert "tensorflow.org/serving" in evidence


def test_packaging_belongs_to_nobody_here():
    grade, _ = grade_ownership(_meta("pypi_packaging.json"), _product("bigcodebench", "bigcode-project/bigcodebench"))
    assert grade == "none"


# ----------------------------------------------------------------------------------------------
# Role: read from the summary, quoted; the heuristic is a label.


@pytest.mark.parametrize("fixture, expected", [
    ("pypi_typesense.json", "CLIENT/SDK"),
    ("pypi_firecrawl-py.json", "CLIENT/SDK"),
    ("pypi_lakefs.json", "CLIENT/SDK"),
    ("pypi_otari.json", "CLIENT/SDK"),
    ("pypi_tensorlake.json", "CLIENT/SDK"),
    ("pypi_tensorflow-serving-api.json", "CLIENT/SDK"),
    ("pypi_pgvector.json", "CLIENT/SDK"),
])
def test_the_five_425_packages_announce_their_role(fixture, expected):
    """#426: "role is often answerable from the package's own summary, which makes it cheap to
    check and inexcusable to skip." All of #425's packages say client, SDK or wrapper."""
    info = json.loads(_fixture(fixture))["info"]
    label, quote = label_role(info["summary"], {"description": "A thing."})
    assert label == expected
    assert info["summary"].strip('"') in quote


def test_silent_summary_gets_a_presumptive_label_not_a_decision():
    server = {"description": "Typesense is an in-memory search engine and server."}
    label, quote = label_role("A high-performance inference engine for AI models", server)
    assert label == "CLIENT (presumptive)" and "presumptively" in quote
    library = {"description": "Uzu is an on-device inference engine for Apple platforms."}
    label, quote = label_role("A high-performance inference engine for AI models", library)
    assert label == "PRODUCT (presumptive)" and "presumptively" in quote


def test_a_product_that_is_itself_an_sdk_is_not_called_a_client():
    label, _ = label_role("Agents SDK for Python", {"description": "An SDK for building agents."})
    assert label == "PRODUCT-IS-SDK"


# ----------------------------------------------------------------------------------------------
# Instrument: monthly, cumulative, or nothing; a 429 is never a zero.


RAW_TFS = "https://raw.githubusercontent.com/tensorflow/serving/HEAD/"


def _tensorflow_serving_repo(registry, *, setup_status=200) -> dict:
    """The real tensorflow/serving layout as of 2026-09-11: the README has the `docker pull` and
    NO pip line; `pip install tensorflow-serving-api` lives in `tensorflow_serving/g3doc/setup.md`
    behind the README's "Install Tensorflow Serving without Docker" link. Two other linked docs
    answer 404 here so the reader's handling of an unreadable linked page is exercised too."""
    registry[RAW_TFS + "README.md"] = (200, _fixture("readme_tensorflow-serving.md"), False)
    registry[RAW_TFS + "tensorflow_serving/g3doc/docker.md"] = (200, _fixture("tensorflow-serving_g3doc_docker.md"), False)
    setup = (200, _fixture("tensorflow-serving_g3doc_setup.md"), False) if setup_status == 200 else (setup_status, None, False)
    registry[RAW_TFS + "tensorflow_serving/g3doc/setup.md"] = setup
    registry[RAW_TFS + "tensorflow_serving/g3doc/building_with_docker.md"] = (404, None, False)
    registry[RAW_TFS + "tensorflow_serving/g3doc/serving_kubernetes.md"] = (404, None, False)
    return _product("tensorflow-serving", "tensorflow/serving", "TensorFlow Serving is a serving system.")


def test_the_real_tensorflow_serving_readme_alone_does_not_name_the_pip_channel():
    """The round-1 omission, pinned: read only the root README and the 4.6M-a-month package is
    never a candidate. Whatever follows must find it somewhere else."""
    product = _product("tensorflow-serving", "tensorflow/serving")
    found = {(c.kind, c.name) for c in extract_candidates(_fixture("readme_tensorflow-serving.md"), product)}
    assert found == {("docker", "tensorflow/serving")}


def test_install_links_are_taken_from_the_real_readme_in_order_and_nothing_else():
    """Relative install-shaped links only: the tutorial, architecture, REST API and CONTRIBUTING
    pages are not install instructions, and tensorflow.org / github.com/tensorflow/tensorflow
    links are not this repository's own."""
    links = cpc.install_doc_links(_fixture("readme_tensorflow-serving.md"), "README.md")
    assert links == [
        "tensorflow_serving/g3doc/docker.md",
        "tensorflow_serving/g3doc/setup.md",
        "tensorflow_serving/g3doc/building_with_docker.md",
        "tensorflow_serving/g3doc/serving_kubernetes.md",
    ]


def test_install_links_resolve_against_the_readme_directory_and_stay_in_repo():
    readme = ("[Install](../INSTALL.md) [Setup](./docs/setup.md) [Quick start](docs/quickstart.rst#run) "
              "[Escape](../../etc/passwd.md) [Site](https://example.com/install.md) "
              "[Proto](//cdn.example.com/install.md) [Image](install.png) ![install](docs/install.md) "
              "[Self](README.md)")
    assert cpc.install_doc_links(readme, "docs/README.md") == ["INSTALL.md", "docs/docs/setup.md", "docs/docs/quickstart.rst"]
    many = "\n".join(f"[Install {i}](docs/install{i}.md)" for i in range(10))
    assert len(cpc.install_doc_links(many)) == cpc.MAX_LINKED_DOCS


def test_tensorflow_serving_api_is_found_in_the_linked_setup_doc_and_answers_all_three_questions(registry):
    """The canonical case against the repository's REAL structure, with a note that has NOT yet
    recorded a judgment: the pip channel is discovered through the linked setup page, `found in:`
    names that page, identity weak, role CLIENT/SDK, 4.6M monthly, recommendation REVIEW rather
    than re-band. The two 404 linked docs are listed as unread and stop nothing."""
    product = _tensorflow_serving_repo(registry)
    registry.update(_pypi("tensorflow-serving-api", last_month=4627937))
    registry.update(_docker("tensorflow", "serving"))

    docs, unread = cpc.install_docs(product)
    assert [path for path, _ in docs] == ["README.md", "tensorflow_serving/g3doc/docker.md", "tensorflow_serving/g3doc/setup.md"]
    assert unread == ["linked tensorflow_serving/g3doc/building_with_docker.md: HTTP 404",
                      "linked tensorflow_serving/g3doc/serving_kubernetes.md: HTTP 404"]

    findings = assess("tensorflow-serving", product, _score("6,360 GitHub stars, level 2."), docs)
    finding = _by_name(findings, "pypi", "tensorflow-serving-api")
    assert finding.candidate.origin == "pip install tensorflow-serving-api  [tensorflow_serving/g3doc/setup.md]"
    assert finding.prior_judgment is None
    assert finding.ownership == "weak"
    assert finding.role == "CLIENT/SDK" and "TensorFlow Serving Python API" in finding.role_quote
    assert finding.figure.startswith("4,627,937 monthly")
    assert finding.recommendation.startswith("REVIEW")
    assert "band" not in finding.recommendation.lower().replace("do not auto-route", "")
    text = "\n".join(finding.lines())
    for label in ("ownership:", "role:", "figure:", "recommendation:", "found in:"):
        assert label in text
    image = _by_name(findings, "docker", "tensorflow/serving")
    assert image.candidate.origin == "docker pull tensorflow/serving  [README.md]", "first sighting wins; the linked page is a repeat"
    assert "CUMULATIVE" in image.figure and image.recommendation.startswith("CORROBORATION ONLY")


def test_the_real_tensorflow_serving_note_is_honoured_for_the_channel_found_two_hops_away(registry):
    """The prior-judgment read has to fire for a candidate that came from a linked doc, or the
    recorded judgment on tensorflow-serving-api is exactly what a re-run would trample."""
    product = _tensorflow_serving_repo(registry)
    note = ("6,360 GitHub stars. Two larger figures exist and neither is this product's. The `tensorflow-serving-api` package "
            "draws 4,627,937 downloads in the trailing 30 days, but its own summary is \"TensorFlow Serving Python API\" - it "
            "is the client library for a running server. The `tensorflow/serving` container image has 80,659,067 cumulative pulls.")
    docs, _unread = cpc.install_docs(product)
    findings = assess("tensorflow-serving", product, _score(note), docs)
    assert all(f.prior_judgment is not None for f in findings), [(f.candidate.name, f.prior_judgment) for f in findings]
    assert "[tensorflow_serving/g3doc/setup.md]" in _by_name(findings, "pypi", "tensorflow-serving-api").candidate.origin


def test_links_inside_a_linked_doc_are_not_followed(registry):
    """One level only. setup.md links to docker.md and building_with_docker.md; had the reader
    recursed, the unmapped URLs would fail this test through the no-network guard."""
    registry[RAW_TFS + "README.md"] = (200, "[Install](tensorflow_serving/g3doc/setup.md)\n", False)
    registry[RAW_TFS + "tensorflow_serving/g3doc/setup.md"] = (200, _fixture("tensorflow-serving_g3doc_setup.md"), False)
    docs, unread = cpc.install_docs(_product("tensorflow-serving", "tensorflow/serving"))
    assert [path for path, _ in docs] == ["README.md", "tensorflow_serving/g3doc/setup.md"] and unread == []


def test_a_transient_linked_doc_is_reported_and_never_read_as_empty(registry):
    product = _tensorflow_serving_repo(registry, setup_status=429)
    registry[RAW_TFS + "tensorflow_serving/g3doc/setup.md"] = (429, None, True)
    docs, unread = cpc.install_docs(product)
    assert [path for path, _ in docs] == ["README.md", "tensorflow_serving/g3doc/docker.md"]
    assert any(line.startswith("linked tensorflow_serving/g3doc/setup.md: HTTP 429 (transient") for line in unread)


def test_an_unreadable_readme_reads_no_linked_docs_and_says_so(registry):
    registry[RAW_TFS + "README.md"] = (429, None, True)
    docs, unread = cpc.install_docs(_product("tensorflow-serving", "tensorflow/serving"))
    assert docs == [] and unread == ["README of tensorflow/serving: HTTP 429 (transient; says nothing about whether a figure exists; never a zero)"]


def test_html_pre_blocks_are_read_as_code():
    """g3doc's docker.md wraps its terminal in `<pre><code class="devsite-terminal">`; the image
    in that block is a candidate, and the tags are not."""
    product = _product("tensorflow-serving", "tensorflow/serving")
    head = _fixture("tensorflow-serving_g3doc_docker.md").split("## Install Docker")[0]
    assert "```" not in head, "the fixture's first block is HTML, not a fence"
    found = extract_candidates(head, product)
    assert [(c.kind, c.name) for c in found] == [("docker", "tensorflow/serving")]
    assert "<code" not in found[0].origin


def test_a_429_from_pypistats_is_no_figure_and_never_a_zero(registry):
    """#426 failure 3. The first sweep turned four 429s into "0 downloads, level 1"."""
    registry.update(_pypi("uzu", stats_status=429, transient=True))
    findings = assess("uzu", _product("uzu", "trymirai/uzu"), _score(), "```\npip install uzu\n```\n")
    finding = _by_name(findings, "pypi", "uzu")
    assert finding.figure.startswith("no figure - HTTP 429")
    assert "never a zero" in finding.figure
    assert finding.recommendation.startswith("RETRY")
    assert "0 monthly" not in "\n".join(finding.lines())
    # identity and role were still read from the metadata that DID answer
    assert finding.ownership == "strong"


def test_a_404_from_the_registry_reports_no_figure_and_no_metadata(registry):
    registry["https://pypi.org/pypi/nonesuch/json"] = (404, None, False)
    findings = assess("x", _product("x", "acme/x"), _score(), "```\npip install nonesuch\n```\n")
    finding = _by_name(findings, "pypi", "nonesuch")
    assert finding.figure == "no figure - HTTP 404"
    assert finding.ownership == "unknown"
    assert not finding.recommendation.startswith("REVIEW")


def test_pgvector_pulls_are_cumulative_corroboration_never_a_band(registry):
    """164M pulls on Docker Hub cannot be banded on a monthly scale."""
    registry.update(_docker("pgvector", "pgvector"))
    product = _product("pgvector", "pgvector/pgvector", "pgvector is a Postgres extension.")
    findings = assess("pgvector", product, _score("22,664 GitHub stars, level 3.", ">10K stars", 3),
                      "```\ndocker pull pgvector/pgvector:pg17\n```\n")
    finding = _by_name(findings, "docker", "pgvector/pgvector")
    assert "181,793,259 pulls CUMULATIVE" in finding.figure
    assert finding.recommendation.startswith("CORROBORATION ONLY")
    assert "monthly" not in finding.figure.split("(")[0]


def test_registries_without_a_pull_count_are_named_not_measured(registry):
    findings = assess("x", _product("x", "acme/x"), _score(), "```\ndocker pull ghcr.io/acme/x:latest\n```\n")
    finding = _by_name(findings, "docker", "ghcr.io/acme/x")
    assert finding.figure == "no figure - ghcr.io publishes no pull count"


def test_crates_figure_says_it_is_a_90_day_window(registry):
    registry["https://crates.io/api/v1/crates/uzu"] = (200, json.dumps({"crate": {
        "description": "inference engine", "repository": "https://github.com/trymirai/uzu", "recent_downloads": 9000}}), False)
    meta, figure, transient = read_crates("uzu")
    assert not transient and meta["urls"]["repository"].endswith("trymirai/uzu")
    assert figure.startswith("9,000 over 90 days") and "NOT a monthly figure" in figure


def test_uzu_minority_channel_is_reported_not_judged(registry):
    """788 downloads on a Rust-primary product: the check says what it found and leaves the
    comparison with stars, and the decision, to a person."""
    registry.update(_pypi("uzu", last_month=788))
    findings = assess("uzu", _product("uzu", "trymirai/uzu", "Uzu is an on-device inference engine."),
                      _score("1,684 GitHub stars."), "```\nuv add uzu==0.5.26\n```\n")
    finding = _by_name(findings, "pypi", "uzu")
    assert finding.ownership == "strong" and finding.role == "PRODUCT (presumptive)"
    assert finding.figure.startswith("788 monthly")
    assert finding.recommendation.startswith("REVIEW")
    assert "stars" not in finding.recommendation


def test_a_declared_package_on_a_stars_record_is_itself_reported(registry):
    """firecrawl declares firecrawl-py and bands on stars; the report says so, with the SDK's
    own summary quoted as the reason a person must decide."""
    registry.update(_pypi("firecrawl-py", last_month=6232491))
    product = _product("firecrawl", "firecrawl/firecrawl", "Web scraping API.", pypi=["firecrawl-py"])
    findings = assess("firecrawl", product, _score("166,863 stars.", ">10K stars", 3), None)
    finding = _by_name(findings, "pypi", "firecrawl-py")
    assert finding.ownership == "strong" and finding.role == "CLIENT/SDK"
    assert any("DECLARED artifact" in n for n in finding.notes)
    assert finding.recommendation.startswith("REVIEW - do not auto-route")


# ----------------------------------------------------------------------------------------------
# Prior judgment: the note is read before anything is fetched.

TYPESENSE_NOTE = ("26,444 GitHub stars, which lands in the >10K stars band of the stars scale, level 3. "
                  "The `typesense` package on PyPI is the Python client for a running server, so its downloads "
                  "are not the product's. With no published deployment figure the stars scale applies, capped at 3.")
LAKEFS_NOTE = ("5,490 GitHub stars, which lands in the 1K-10K stars band of the stars scale, level 2. "
               "The `lakefs` package on PyPI is the Python SDK wrapper for the server's API rather than the "
               "server, so its downloads measure client use. No deployment figure is published.")


def test_typesense_and_lakefs_surface_the_recorded_judgment_and_fetch_nothing(registry):
    """The two records #425 overwrote. Nothing is mapped in `registry`, so a fetch would fail
    the test: the prior judgment short-circuits the registry read."""
    findings = assess("typesense", _product("typesense", "typesense/typesense"), _score(TYPESENSE_NOTE),
                      "```\npip install typesense\n```\n")
    finding = _by_name(findings, "pypi", "typesense")
    assert finding.prior_judgment == ("The `typesense` package on PyPI is the Python client for a running "
                                      "server, so its downloads are not the product's.")
    assert "PRIOR JUDGMENT RECORDED - read before changing" in "\n".join(finding.lines())

    findings = assess("lakefs", _product("lakefs", "treeverse/lakeFS"), _score(LAKEFS_NOTE), "```\npip install lakefs\n```\n")
    assert "Python SDK wrapper" in _by_name(findings, "pypi", "lakefs").prior_judgment


def test_a_bare_mention_of_the_product_name_is_not_a_judgment():
    """"pgvector has 22,664 stars" names the candidate and says nothing about the package."""
    adoption = {"reach": ">10K stars", "note": "pgvector has 22,664 GitHub stars. Level 3 on the stars scale."}
    assert prior_judgment(adoption, Candidate("pypi", "pgvector", "")) is None


def test_a_judgment_about_the_pypi_package_is_not_one_about_the_image_or_npm():
    note = ("A `uzu` package exists on PyPI and drew 788 downloads in the trailing 30 days against a "
            "Rust and Swift primary distribution.")
    adoption = {"reach": "1K-10K stars", "note": note}
    assert prior_judgment(adoption, Candidate("pypi", "uzu", "")) == note
    assert prior_judgment(adoption, Candidate("npm", "@trymirai/uzu", "")) is None
    assert prior_judgment(adoption, Candidate("docker", "trymirai/uzu", "")) is None


def test_the_real_tensorflow_serving_note_is_a_prior_judgment_for_the_pypi_package():
    note = ("Two larger figures exist and neither is this product's. The `tensorflow-serving-api` package "
            "draws 4,627,937 downloads in the trailing 30 days, but its own summary is \"TensorFlow Serving "
            "Python API\" - it is the client library for a running server. The `tensorflow/serving` container "
            "image the README's quickstart pulls reports 80,659,067 pulls, which is cumulative.")
    adoption = {"reach": "1K-10K stars", "note": note}
    assert "4,627,937" in prior_judgment(adoption, Candidate("pypi", "tensorflow-serving-api", ""))
    assert "80,659,067" in prior_judgment(adoption, Candidate("docker", "tensorflow/serving", ""))


def test_the_module_docstring_states_the_general_rule():
    assert "read the prose it is about to overwrite" in cpc.__doc__


# ----------------------------------------------------------------------------------------------
# The fetch seam and the report contract.


def test_fetch_text_caches_only_200_and_reports_transient_without_a_body(monkeypatch, tmp_path):
    monkeypatch.setattr(cpc, "CACHE_DIR", tmp_path)
    calls = []

    def fake_fetch(url, body_dir=None, retries=0, **_kw):
        calls.append(url)
        if "limited" in url:
            return {"url": url, "http_status": 429, "transient": True}
        if "missing" in url:
            return {"url": url, "http_status": 404}
        path = Path(body_dir) / "x.body"
        path.write_text("body")
        return {"url": url, "http_status": 200, "body_path": str(path)}

    monkeypatch.setattr(cpc, "fetch", fake_fetch)
    assert cpc.fetch_text("https://x/limited") == (429, None, True)
    assert cpc.fetch_text("https://x/missing") == (404, None, False)
    assert cpc.fetch_text("https://x/ok") == (200, "body", False)
    assert cpc.fetch_text("https://x/ok") == (200, "body", False)
    assert calls.count("https://x/ok") == 1, "a 200 is served from cache on the second call"
    assert calls.count("https://x/limited") == 1 and not list(tmp_path.glob("*limited*")), "a 429 is never cached"


def test_report_never_writes_a_score_file(registry, tmp_path, monkeypatch, capsys):
    """Report-only, the way check_declarations is: exit 0 and the corpus untouched."""
    root = tmp_path
    (root / "sources" / "scores").mkdir(parents=True)
    (root / "sources" / "products").mkdir(parents=True)
    (root / "sources" / "products" / "uzu.yaml").write_text(
        "name: uzu\ngithub:\n- url: https://github.com/trymirai/uzu\n")
    score = "adoption:\n  level: 2\n  reach: 1K-10K stars\n  signal_type: stars_fallback\n  note: 1,684 stars.\n"
    (root / "sources" / "scores" / "uzu.yaml").write_text(score)
    monkeypatch.setattr(cpc, "ROOT", root)
    registry["https://raw.githubusercontent.com/trymirai/uzu/HEAD/README.md"] = (200, "```\npip install uzu\n```\n", False)
    registry.update(_pypi("uzu", last_month=788))

    assert cpc.main(["--sleep", "0"]) == 0
    out = capsys.readouterr().out
    assert "1 stars_fallback record(s) walked" in out and "uzu -> PyPI uzu" in out
    assert (root / "sources" / "scores" / "uzu.yaml").read_text() == score
    assert "Report-only" in out


def test_not_wired_into_validate_yml():
    """It fetches, and a gate that 429s is a gate nobody reads."""
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "validate.yml").read_text()
    assert "check_package_channel" not in workflow


def test_a_declared_artifact_with_silent_metadata_grades_declared_not_none(registry):
    """boltz declares `boltz` on PyPI and the package's metadata names no repository. The
    corpus's own declaration is the ownership evidence; the metadata gap is reported, not
    read as doubt."""
    registry["https://pypi.org/pypi/boltz/json"] = (200, json.dumps({"info": {"summary": "Boltz", "project_urls": None}}), False)
    registry["https://pypistats.org/api/packages/boltz/recent"] = (200, json.dumps({"data": {"last_month": 12000}}), False)
    product = _product("boltz", "jwohlwend/boltz", "Boltz is a biomolecular structure model.", pypi=["boltz"])
    finding = _by_name(assess("boltz", product, _score(), None), "pypi", "boltz")
    assert finding.ownership == "declared"
    assert "sources/products" in finding.ownership_evidence
    assert finding.recommendation.startswith("REVIEW")


def test_a_same_named_package_with_no_link_is_unverified_not_ignored(registry):
    """alpaca-eval on PyPI, author "The Alpaca Team", no repository URL, for
    tatsu-lab/alpaca_eval: sharing the name is not evidence either way (adoption.md, third trap)."""
    registry["https://pypi.org/pypi/alpaca-eval/json"] = (200, json.dumps({"info": {
        "summary": "AlpacaEval : An Automatic Evaluator", "author": "The Alpaca Team", "project_urls": None}}), False)
    registry["https://pypistats.org/api/packages/alpaca-eval/recent"] = (200, json.dumps({"data": {"last_month": 36478}}), False)
    product = _product("alpacaeval", "tatsu-lab/alpaca_eval")
    finding = _by_name(assess("alpacaeval", product, _score(), "```\npip install alpaca-eval\n```\n"), "pypi", "alpaca-eval")
    assert finding.ownership == "none"
    assert finding.recommendation.startswith("UNVERIFIED")


def test_an_unrelated_dependency_is_ignored_with_the_figure_attributed_elsewhere(registry):
    registry.update(_pypi("packaging", last_month=2191710133))
    product = _product("bigcodebench", "bigcode-project/bigcodebench")
    # force the stop-listed name through extraction by naming it directly
    findings = assess("bigcodebench", product, _score(), None)
    assert findings == []
    from build.check_package_channel import Candidate as C, READERS  # noqa: F401
    meta, figure, transient = READERS["pypi"]("packaging")
    grade, _ = grade_ownership(meta, product)
    assert grade == "none" and figure.startswith("2,191,710,133 monthly")
    assert cpc.recommend(C("pypi", "packaging", ""), grade, "PRODUCT (presumptive)", figure, transient).startswith("IGNORE")
