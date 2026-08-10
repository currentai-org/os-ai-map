"""`signal_routing.yaml` declares which machine-readable sources exist. Nothing else in the
suite checks that declaration against what products actually claim to have, so an artifact
kind can go undeclared indefinitely and every product carrying it silently falls through to
the stars fallback and its cap of 3 — no test fails, no error surfaces, the score is simply
lower than it should be.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


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
