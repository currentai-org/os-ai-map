"""`signal_routing.yaml` declares which machine-readable sources exist. Nothing else in the
suite checks that declaration against what products actually claim to have, so an artifact
kind can go undeclared indefinitely and every product carrying it silently falls through to
the stars fallback and its cap of 3 — no test fails, no error surfaces, the score is simply
lower than it should be.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _routing() -> dict:
    return yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())



def test_every_declared_artifact_kind_has_a_route_or_is_declared_unbridged():
    """A product may declare an artifact kind no route can reach, but the gap must be visible.

    npm and crates were absent from signal_routing entirely, so 13 products with a real
    countable distribution artifact silently fell through to the stars scale and its cap of 3.
    Declaring the source `bridged: false` is this file's idiom for machine-readable but not
    yet joinable, and it turns the gap into a backlog entry.

    This only covers the kinds enumerated in `ARTIFACT_KINDS` below. A product key outside
    that set - `arxiv` already is - is invisible to this check and can go undeclared with no
    failure here, whether or not it turns out to be a distribution artifact.
    """
    routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())
    declared = set(routing["sources"])

    # Only kinds named here are checked. Adding a new artifact kind to a product record
    # (e.g. a `go` or `docker` key) does not make it visible to this test until it is added
    # to this set too.
    ARTIFACT_KINDS = {"github", "npm", "pypi", "crates", "go", "huggingface_model", "huggingface_dataset"}
    in_use = set()
    for path in sorted((ROOT / "sources" / "products").glob("*.yaml")):
        record = yaml.safe_load(path.read_text()) or {}
        in_use |= {k for k in ARTIFACT_KINDS if record.get(k)}

    assert in_use <= declared, (
        "artifact kinds in use with no declared source: " + str(sorted(in_use - declared))
    )




def test_an_undeployed_source_is_not_marked_bridged():
    """`bridged` means a model READS this source, and `check_instrument` believes it.

    npm and crates have their models written and not materialized. Flipping `bridged` on that
    basis would mark 12 `usage_volume` records as recomputable without a number having been
    computed — `mcp-typescript-sdk` and `openclaw` claim level 5 — and the gate that exists to
    catch exactly that would go green.

    So the flip belongs to the deploy, and this asserts the two cannot come apart: a source
    declaring any `blocked_by` may not also claim to be bridged.
    """
    offences = [
        name
        for name, source in (_routing().get("sources") or {}).items()
        if source.get("blocked_by") and source.get("bridged")
    ]
    assert not offences, (
        "sources claiming to be bridged while declaring a blocker: " + str(sorted(offences))
    )


def test_the_unbridged_registries_carry_the_blocker_that_says_what_is_missing():
    """A missing key and a missing deploy cost different things, so they are named apart.

    npm and crates are `deploy`: the join key is `product_slug` and the model is written.
    artificialanalysis and lmarena are `key`: their tables exist and nothing joins them to a
    product, which needs a curation decision rather than a run. Recorded as a test because the
    file's whole purpose is that an absence is a decision rather than an oversight.
    """
    sources = _routing().get("sources") or {}
    assert sources["npm"]["blocked_by"] == "deploy"
    assert sources["crates"]["blocked_by"] == "deploy"
    assert sources["artificialanalysis"]["blocked_by"] == "key"
    assert sources["lmarena"]["blocked_by"] == "key"


def test_every_adoption_route_reading_a_registry_names_the_channel_it_governs():
    """`governs` is what the under-coverage rule turns on.

    A download count is a count of one channel, and it is a count of the PRODUCT only where
    that channel is how the product ships. `n8n` records 393,738 npm downloads against a
    Docker-first install base; naming the channel on the route is what lets a reader see that
    the number and the product are not the same thing.
    """
    routes = ((_routing().get("dimensions") or {})["adoption"]).get("routes") or []
    missing = [
        route["source"]
        for route in routes
        if route.get("source") in {"pypi", "npm", "crates", "huggingface_model", "huggingface_dataset"}
        and not route.get("governs")
    ]
    assert not missing, f"adoption routes with no declared channel: {missing}"
