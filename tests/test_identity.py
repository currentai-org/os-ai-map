import pytest

from build import identity as I


@pytest.mark.parametrize("kind,raw,want", [
    ("github", "https://github.com/Dao-AILab/flash-attention.git/", "dao-ailab/flash-attention"),
    ("github", "Dao-AILab/Flash-Attention", "dao-ailab/flash-attention"),
    ("pypi", "Scikit_Learn", "scikit-learn"),
    ("pypi", "https://pypi.org/project/Pillow.SIMD/", "pillow-simd"),
    ("npm", "@Scope/Name", "@scope/name"),
    ("crates", "Serde_JSON", "serde_json"),
    ("arxiv", "https://arxiv.org/abs/2401.12345v3", "2401.12345"),
    ("arxiv", "arxiv:cs/0112017v1", "cs/0112017"),
    ("huggingface_model", "https://huggingface.co/Meta-Llama/Llama-3", "Meta-Llama/Llama-3"),
    ("homepage", "http://www.Example.com/products/foo/?utm=1#x", "example.com"),
])
def test_canonical(kind, raw, want):
    assert I.canonical(kind, raw) == want


def test_crates_fold_only_proposes():
    assert I.canonical("crates", "serde-json") != I.canonical("crates", "serde_json")
    assert I.fold_for_proposal("crates", "serde-json") == I.fold_for_proposal("crates", "serde_json")


def test_hf_compares_casefolded_but_keeps_case():
    assert I.canonical("huggingface_model", "Org/Name") == "Org/Name"
    assert I.fold_for_proposal("huggingface_model", "Org/Name") == "org/name"


def test_homepage_canonical_url_keeps_the_path_as_evidence():
    assert I.homepage_canonical_url("http://www.example.com/products/foo/?a=1") == "https://example.com/products/foo"


def test_every_kind_has_a_url_pattern():
    for kind in I.KINDS:
        assert I.id_from_url(kind, "not a url") is None


def test_id_from_url_rejects_github_org_pages():
    """An org page names no repo, so it cannot be measured as one."""
    assert I.id_from_url("github", "https://github.com/arduino") is None


def test_id_from_url_rejects_reserved_github_paths():
    """`github.com/orgs/...` is a GitHub product page, not `orgs/<repo>`."""
    assert I.id_from_url("github", "https://github.com/orgs/some-org") is None


def test_id_from_url_rejects_huggingface_dataset_as_model():
    assert I.id_from_url("huggingface_model", "https://huggingface.co/datasets/allenai/c4") is None


def test_id_from_url_accepts_huggingface_dataset():
    assert I.id_from_url("huggingface_dataset", "https://huggingface.co/datasets/allenai/c4") == "allenai/c4"


def test_id_from_url_rejects_bare_arxiv_id():
    """`id_from_url` requires the `arxiv:` prefix or an arxiv.org URL; a bare id is not a URL."""
    assert I.id_from_url("arxiv", "2311.12022") is None


def test_canonical_accepts_bare_arxiv_id():
    assert I.canonical("arxiv", "2311.12022") == "2311.12022"


def test_homepage_domain_drops_www():
    assert I.homepage_domain("https://www.Example.com/x") == "example.com"
