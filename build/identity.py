"""Canonical identity forms for every artifact kind. The one place these rules live.

Three near-duplicate pattern families existed before this module (`validate.py`,
`serialize_registry.py`, `propose_artifacts.py`) and had already diverged: only
`validate.py` folded GitHub ids for comparison, only `serialize_registry.py` had no
`crates` pattern at all, and `resolution.py`'s ledger key folded `github` only.
`propose_artifacts.py` still mines candidates out of free text with its own
`PATTERNS` (unanchored `re.search`, ordered first-match-wins, plus a
`pypistats.org` pattern with no equivalent here) -- deliberately kept separate,
since that is a different job from `id_from_url`'s anchored single-pattern-per-kind
URL parsing. Import the identity rules from here; never copy them.

Two things this module deliberately keeps apart:

`canonical(kind, ident)` is the **declared spelling**, structurally normalized only
(a URL reduced to its bare id, a trailing `/` or `.git` stripped). It does not fold
case or punctuation for `github` or `pypi`, because `registry.product_artifacts` is
joined against externally sourced signal tables (GitHub's own API casing, PyPI's own
package name) on raw equality; rewriting the declared spelling there breaks that
join until every signal re-runs. `npm` and `crates` publish under a single
registry-enforced casing, so folding those in `canonical` costs nothing; `arxiv` is
never a case-sensitive identifier to begin with; Hugging Face ids are also kept as
served. `homepage` keeps its host lowercased in `canonical` (hosts are never
case-sensitive) but its path as declared, because paths can be case-sensitive.

`fold_for_proposal(kind, ident)` is the **comparison form** -- github and Hugging
Face casefolded, PyPI folded per PEP 503 (lowercase, runs of `-`/`_`/`.` collapsed to
`-`), crates' `-`/`_` collapsed, homepage lowercased in full. Every equality question
-- "is this artifact already declared", a resolution-ledger lookup, a proposer's
dedup -- goes through this, never through raw `canonical` values compared to each
other.

A homepage is weak corroborating evidence, never identity: two distinct products
routinely share one company's `homepage_domain` (`acme.com`), so `canonical`/
`fold_for_proposal` key on the full URL (host + path), and a shared domain alone must
never establish equivalence or suppress a second candidate. See the "Homepage is
evidence, not identity" note in docs/reference/identity.md.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

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

# Path segments that are not a repo/model owner. Without these, a GitHub product page
# (`github.com/orgs/...`) or a Hugging Face docs/blog link becomes a confident-looking
# candidate. Lived in `build/propose_artifacts.py` until Task 2's fix round; moved here
# because they are pure facts about URL shape -- this module's own subject matter --
# and `propose_artifacts` is a network-fetching discovery tool that must not be a
# dependency of the identity primitive. `propose_artifacts` imports these from here.
GH_RESERVED = {
    "orgs", "topics", "search", "features", "pricing", "about", "explore",
    "marketplace", "sponsors", "collections", "trending", "settings", "login",
}
HF_RESERVED = {
    "datasets", "spaces", "api", "docs", "blog", "papers", "collections",
    "models", "organizations", "settings", "join", "pricing", "tasks", "learn",
}

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
        return _homepage_canonical(raw) if "." in raw else None
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
    """The declared spelling, structurally normalized -- see the module docstring.

    Accepts either a URL (parsed via `id_from_url`) or a bare identifier (used as
    given). Does not reject malformed input -- a caller that needs the "is this even
    addressable" answer must go through `id_from_url` first and treat None as
    rejection; `canonical` alone will not reject a malformed URL, it just folds
    whatever `id_from_url` gives it (or the raw string, unchanged) through the
    per-kind structural normalization. Does not fold case for `github` or `pypi` --
    use `fold_for_proposal` to compare identities.
    """
    raw = (ident_or_url or "").strip()
    ident = id_from_url(kind, raw) or raw
    if kind == "github":
        return ident.removesuffix("/").removesuffix(".git")
    if kind == "pypi":
        return ident
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
        return _homepage_canonical(raw)
    raise ValueError(kind)


def fold_for_proposal(kind: str, ident: str) -> str:
    """The folded form every identity comparison uses -- proposal dedup, validate.py's
    per-kind dedup, the resolution ledger key, and `check_artifacts`. Never the value
    written to `registry.product_artifacts`; see the module docstring for why.

    GitHub and Hugging Face ids are casefolded. PyPI is folded per PEP 503 (lowercase,
    runs of `-`/`_`/`.` collapsed to `-`) so `Scikit_Learn` and `scikit-learn` compare
    equal. Crates collapses `-`/`_` (a proposer should not offer `serde-json` when
    `serde_json` is already declared, even though they are different crates and stay
    distinct in `canonical`).
    """
    c = canonical(kind, ident)
    if kind == "github":
        return c.lower()
    if kind == "pypi":
        return re.sub(r"[-_.]+", "-", c).lower()
    if kind == "crates":
        return c.replace("_", "-")
    if kind in ("huggingface_model", "huggingface_dataset"):
        return c.casefold()
    if kind == "homepage":
        return c.lower()
    return c


def _homepage_canonical(url: str) -> str:
    """Scheme-less canonical form: lowercased host minus `www.`, plus the path as
    declared (case kept -- paths can be case-sensitive), minus query/fragment and any
    trailing slash. `canonical("homepage", ...)`'s implementation; see that docstring
    and the "Homepage is evidence, not identity" note in docs/reference/identity.md.
    """
    parts = urlsplit(url if "://" in url else f"https://{url}")
    host = (parts.hostname or "").lower().removeprefix("www.")
    path = parts.path.rstrip("/")
    return f"{host}{path}"


def homepage_domain(url: str) -> str:
    """The comparison host: hostname, lowercased, minus a leading `www.`.

    Evidence only -- a shared host is corroborating evidence of common ownership, never
    identity. Two distinct products at `acme.com/a` and `acme.com/b` are legitimately
    different homepage artifacts (`canonical`/`fold_for_proposal` key on the full URL,
    not this); use this only where the question really is "same registrable-ish host",
    such as an org-ownership signal, not "same artifact".

    Not a registrable domain -- `awslabs.github.io`'s registrable domain is
    `github.io`, and this returns the full hostname regardless. The brief chose this
    deliberately (no public-suffix dependency); do not "fix" it toward one, and do
    not trust it as one.
    """
    host = (urlsplit(url if "://" in url else f"https://{url}").hostname or "").lower()
    return host.removeprefix("www.")


def homepage_canonical_url(url: str) -> str:
    """The canonical evidence URL, with an explicit scheme -- an alias of
    `canonical("homepage", url)` with `https://` prepended, for callers that need a
    dereferenceable link rather than the bare comparison form.
    """
    return f"https://{canonical('homepage', url)}"
