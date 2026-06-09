from build.slugs import slugify, dedupe_slug


def test_slugify_basic():
    assert slugify("Llama 3.1") == "llama-3-1"
    assert slugify("Model Context Protocol (MCP)") == "model-context-protocol-mcp"
    assert slugify("PyTorch") == "pytorch"


def test_slugify_strips_edges():
    assert slugify("  Hugging Face!  ") == "hugging-face"


def test_dedupe_slug_appends_org_on_collision():
    taken = {"command-r"}
    assert dedupe_slug("command-r", "cohere", taken) == "command-r-cohere"
    assert dedupe_slug("mistral-7b", "mistral", taken) == "mistral-7b"
