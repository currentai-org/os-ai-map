"""A declared artifact URL must be resolvable in the form the fetchers use.

This exists because a malformed URL fails SILENTLY and in the worst possible place: the
product file looks right, `validate` passes, `check_artifacts` passes, CI goes green, the
registry publishes — and the row is simply absent from `currentai.registry.product_artifacts`,
so no signal ever routes to it and the product falls back to a weaker instrument forever.

The Hugging Face path split is the specific trap. A model lives at
`huggingface.co/<org>/<name>` and a dataset at `huggingface.co/datasets/<org>/<name>`. Get it
wrong and the Hub answers 401 or 404 rather than redirecting, so the mistake reads as an
access problem rather than a typo.

It has now been made twice. The first was the Lucie source, found only because
`check_refetch` re-fetched it and got a 401 from a URL "missing its /datasets/ segment". The
second was ten LiveBench corpora declared on 2026-08-12 without the segment; they were caught
only because the registry table came back holding two artifacts where the file declared
twelve. Nothing in the repo compared the two.

So the shape is asserted here, where it costs nothing, rather than discovered from a table
that quietly disagrees with the file that fed it.
"""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _artifacts():
    for path in sorted((ROOT / "sources" / "products").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        for key in ("huggingface_model", "huggingface_dataset", "github", "pypi", "npm", "crates"):
            for row in doc.get(key) or []:
                yield path.stem, key, (row or {}).get("url") or ""


@pytest.fixture(scope="module")
def artifacts():
    return list(_artifacts())


def test_hugging_face_dataset_urls_carry_the_datasets_segment(artifacts):
    """`huggingface_dataset` must point at /datasets/, and `huggingface_model` must not."""
    offences = []
    for slug, key, url in artifacts:
        if key == "huggingface_dataset" and "huggingface.co/" in url and "/datasets/" not in url:
            offences.append(f"{slug}: {key} {url} is missing the /datasets/ segment")
        if key == "huggingface_model" and "/datasets/" in url:
            offences.append(f"{slug}: {key} {url} points at a dataset")
    assert not offences, (
        "a malformed Hugging Face URL is dropped silently by the registry, so no signal ever "
        "routes to the product:\n" + "\n".join(offences)
    )


def test_every_declared_artifact_url_matches_its_registry_host(artifacts):
    """The key names the registry; the URL must actually be on it.

    Cheap, and it catches the other half of the same mistake — a package declared under the
    wrong key, which routes to a fetcher that will never find it.
    """
    hosts = {
        "huggingface_model": "huggingface.co",
        "huggingface_dataset": "huggingface.co",
        "github": "github.com",
        "pypi": "pypi.org",
        "npm": "npmjs.com",
        "crates": "crates.io",
    }
    offences = [
        f"{slug}: {key} URL is not on {hosts[key]}: {url}"
        for slug, key, url in artifacts
        if hosts.get(key) and hosts[key] not in url
    ]
    assert not offences, "\n".join(offences)


def test_the_walk_sees_the_whole_corpus(artifacts):
    """Non-zero count guard: an empty walk passes both checks above trivially."""
    assert len(artifacts) > 400, f"only walked {len(artifacts)} artifacts; the glob has drifted"
