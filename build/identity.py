"""Canonical identity forms for every artifact kind. The one place these rules live.

Three near-duplicate pattern families existed before this module (`validate.py`,
`serialize_registry.py`, `propose_artifacts.py`) and had already diverged: only
`validate.py` lowercased GitHub ids, only `serialize_registry.py` had no `crates`
pattern at all, and `resolution.py`'s ledger key canonicalized `github` only. Import
from here; never copy.

Canonical forms: GitHub owner/repo lowercased with any `.git` suffix removed; PyPI
names per PEP 503 (lowercase, runs of `-`, `_` and `.` collapsed to `-`); npm
lowercased with scope kept; crates lowercased with `-` and `_` kept distinct (they
are different crates); arXiv ids without the version suffix; Hugging Face ids as
served, compared casefolded only when proposing a match (`fold_for_proposal`);
homepage compared on the registrable domain (hostname minus `www.`) with the
canonical URL kept as evidence, never as a key.

`id_from_url` answers "is this string addressable as this kind at all" and returns
None when it is not -- an org-level GitHub link names no repo, a Hugging Face
dataset link is not a model. `canonical` always returns a best-effort canonical
form: pass it either a URL or a bare identifier you already know is one. A caller
that needs the "is this even addressable" answer must go through `id_from_url`
first and treat None as rejection; `canonical` alone will not reject a malformed
URL, it just folds whatever `id_from_url` gives it (or the raw string, unchanged)
through the per-kind normalization.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from build.propose_artifacts import GH_RESERVED, HF_RESERVED

KINDS = (
    "github",
    "huggingface_model",
    "huggingface_dataset",
    "pypi",
    "npm",
    "crates",
    "arxiv",
    "homepage",
)

#: An arXiv id, old-style (category/number) or new-style (YYMM.NNNNN[N]), with an
#: optional version suffix. Exported (not `_`-prefixed) because `serialize_registry`
#: needs it too, to accept a bare id with no `arxiv:` wrapper.
ARXIV_ID = re.compile(r"^([a-z\-]+/\d{7}|\d{4}\.\d{4,5})(?:v\d+)?$", re.I)

_URL = {
    "github": re.compile(
        r"^(?:https?://)?(?:www\.)?github\.com/([^/\s]+)/([^/\s#?]+?)(?:\.git)?/?(?:[#?].*)?$", re.I
    ),
    "huggingface_model": re.compile(
        r"^(?:https?://)?huggingface\.co/(?!datasets/)([^/\s]+)/([^/\s#?]+)/?(?:[#?].*)?$", re.I
    ),
    "huggingface_dataset": re.compile(
        r"^(?:https?://)?huggingface\.co/datasets/([^/\s]+)/([^/\s#?]+)/?(?:[#?].*)?$", re.I
    ),
    "pypi": re.compile(r"^(?:https?://)?pypi\.org/project/([^/\s#?]+)/?(?:[#?].*)?$", re.I),
    "npm": re.compile(
        r"^(?:https?://)?(?:www\.)?npmjs\.com/package/((?:@[^/\s]+/)?[^/\s#?]+)/?(?:[#?].*)?$", re.I
    ),
    "crates": re.compile(r"^(?:https?://)?crates\.io/crates/([^/\s#?]+)/?(?:[#?].*)?$", re.I),
    "arxiv": re.compile(
        r"^(?:arxiv:|(?:https?://)?arxiv\.org/(?:abs|pdf)/)"
        r"([a-z\-]+/\d{7}|\d{4}\.\d{4,5})(?:v\d+)?(?:[#?].*)?$",
        re.I,
    ),
}


def id_from_url(kind: str, url: str) -> str | None:
    """The bare identifier a URL of this kind names, or None if it names none.

    `github` and Hugging Face links are checked against `GH_RESERVED`/`HF_RESERVED`
    so `github.com/orgs/...` is not misread as a repo and `huggingface.co/spaces/...`
    is not misread as a model.
    """
    raw = (url or "").strip()
    if kind == "homepage":
        return homepage_domain(raw) if "." in raw else None
    pattern = _URL.get(kind)
    if pattern is None:
        raise ValueError(kind)
    if kind in ("github", "huggingface_model", "huggingface_dataset"):
        match = pattern.match(raw)
        if not match:
            return None
        owner, name = match.group(1), match.group(2)
        reserved = GH_RESERVED if kind == "github" else HF_RESERVED
        if owner.lower() in reserved:
            return None
        return f"{owner}/{name}"
    match = pattern.match(raw)
    return match.group(1) if match else None


def canonical(kind: str, ident_or_url: str) -> str:
    """The canonical form of an identifier or URL, per kind.

    Accepts either a URL (parsed via `id_from_url`) or a bare identifier (used as
    given). Does not reject malformed input -- see the module docstring.
    """
    raw = (ident_or_url or "").strip()
    ident = id_from_url(kind, raw) or raw
    if kind == "github":
        return ident.removesuffix("/").removesuffix(".git").lower()
    if kind == "pypi":
        return re.sub(r"[-_.]+", "-", ident).lower()
    if kind == "npm":
        return ident.lower()
    if kind == "crates":
        return ident.lower()
    if kind == "arxiv":
        ident = ident.removeprefix("arxiv:").removeprefix("ARXIV:")
        match = ARXIV_ID.match(ident)
        return (match.group(1) if match else ident).lower()
    if kind in ("huggingface_model", "huggingface_dataset"):
        return ident.strip("/")
    if kind == "homepage":
        return homepage_domain(raw)
    raise ValueError(kind)


def fold_for_proposal(kind: str, ident: str) -> str:
    """A looser fold used only to decide whether to propose a match, never as a key.

    Crates collapses `-`/`_` (a proposer should not offer `serde-json` when
    `serde_json` is already declared, even though they are different crates and
    stay distinct in `canonical`). Hugging Face ids are casefolded.
    """
    c = canonical(kind, ident)
    if kind == "crates":
        return c.replace("_", "-")
    if kind in ("huggingface_model", "huggingface_dataset"):
        return c.casefold()
    return c


def homepage_domain(url: str) -> str:
    """The registrable domain: hostname, lowercased, minus a leading `www.`.

    No public-suffix handling -- a plain hostname minus `www.` is the deliberate
    choice (see the identity graph design doc); do not add a public-suffix
    dependency for this.
    """
    host = (urlsplit(url if "://" in url else f"https://{url}").hostname or "").lower()
    return host.removeprefix("www.")


def homepage_canonical_url(url: str) -> str:
    """The canonical evidence URL: https, registrable domain, path kept, no query/fragment."""
    parts = urlsplit(url if "://" in url else f"https://{url}")
    host = (parts.hostname or "").lower().removeprefix("www.")
    path = parts.path.rstrip("/")
    return f"https://{host}{path}"
