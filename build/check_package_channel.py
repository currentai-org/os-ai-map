"""Report `stars_fallback` adoption records whose product ships as a measurable package.

148 adoption records band on GitHub stars. Stars cap the axis at level 3 because a star is not a
use, and for a product that ships as a package, an image or an embedded runtime the star count
understates it in one direction only. `tensorflow-serving` at level 2 on 6,360 stars against
4.6M monthly downloads of `tensorflow-serving-api` is the canonical case (#426). Nothing checked
whether a stars record was leaving a measured figure on the table; this does, and ONLY reports.

## What it does

For every score whose `adoption.signal_type` is `stars_fallback`, read the product's own install
instructions: the README of its declared `github` artifact AND the in-repo documents that README
links to under an install-shaped name (`tensorflow_serving/g3doc/setup.md` behind "Install
Tensorflow Serving without Docker"). Take the package and image names those instructions install,
and for each one answer three questions SEPARATELY:

1. **Identity** - does this package belong to this project? `strong` when a URL in the package's
   own metadata names the declared `owner/repo` in full. `weak` when only the homepage, another
   project URL or the author names the PROJECT (its slug, display name or repository name).
   `none` otherwise. The evidence is printed beside the grade. An owner-name match on its own is
   NOT a grade: `openai/simple-evals` and the `openai` package share an owner and nothing else,
   and `typesense/typesense-python` is a sibling repository, not the product's. Owner names are
   left out of the name set on purpose.
2. **Role** - is it the scored product, or a client, SDK, wrapper, plugin or binding FOR the
   product? Read from the package's own summary, which is quoted so a reader can disagree. When
   the summary says nothing, the heuristic from #426 is applied as a LABEL marked presumptive,
   never as a decision: a server, service or gateway product presumptively ships a client; a
   library, CLI or runtime presumptively ships itself. A product that is itself an SDK gets a
   third label, because "SDK" in the summary then separates nothing.
3. **Instrument quality** - what figure is retrievable, from which window, and is it monthly or
   cumulative? pypistats `last_month` and the npm 30-day point are monthly. crates.io serves a
   90-day `recent_downloads` and is labelled as such, never divided into a monthly figure. Docker
   Hub `pull_count` is cumulative since publication and is surfaced as CORROBORATION ONLY.

Then a recommendation, which is never "re-band". Whether a package is the product's primary
channel is a judgment (docs/reference/adoption.md, "The third trap"), so the strongest thing this
check says is REVIEW.

## The prose it would overwrite is read first

The sharpest lesson from #425, the reverted attempt: two of its five records ALREADY carried the
right judgment in the `adoption.note` being replaced (`typesense`: "the Python client for a
running server, so its downloads are not the product's"; `lakefs`: "the Python SDK wrapper for
the server's API rather than the server"). So before emitting a fresh finding this check searches
the record's `adoption.note` and `reach` for a sentence that names the candidate together with a
channel word (PyPI, package, download, image, pull ...) and, when found, prints
`PRIOR JUDGMENT RECORDED - read before changing` with that sentence, and fetches nothing for the
candidate. The channel word is required because a product's own name appears in nearly every
note ("pgvector has 22,664 stars") and a mention is not a judgment.

The general rule, which is why it is stated here rather than in a comment: **any automated
re-scoring must read the prose it is about to overwrite.** A prior decision living in the field
you are about to replace is the cheapest kind to honour and the easiest to destroy.

## What it deliberately does not do, and why

- **It never edits a level, reach or note.** The three questions above are the report; the
  decision is a person's, recorded in the note with a source.
- **A non-200 from a registry is not a figure.** pypistats answered 429 for four of five packages
  in the first sweep and the banding step turned that into "0 downloads, level 1". Here a transient
  status (`fetch_source.fetch` sets `transient: true` for 429/403/5xx and carries no figure) is
  printed as `no figure - HTTP 429 (transient; ...; never a zero)` and a 404 as
  `no figure - HTTP 404`. Neither is ever a zero, and a transient candidate gets RETRY, not a
  verdict.
- **Owner-name substrings are not ownership.** See question 1. `strong` needs the full
  `owner/repo` path in a package URL; `weak` needs the project's own name in a URL or author.
- **Third-party names in an install line are dropped.** `pip install bigcodebench packaging`
  installs the product AND a dependency; `pip install openai` in simple-evals installs a
  dependency only. Tokens in WELL_KNOWN_THIRD_PARTY are dropped unless they ARE one of the
  product's own names, so `pip install vllm` on the vllm record still yields vllm. The list is a
  stop-list for names that have caused a misattribution or plainly would, not an attempt to know
  every package on PyPI; a dependency it misses reaches the identity question and grades `none`.
- **Prose is not an install line; HTML `<pre>` blocks are.** Only fenced blocks, indented blocks,
  inline backtick spans and `<pre>...</pre>` blocks are read (Google's g3doc pages wrap terminals
  in `<pre>`). See `code_segments`.
- **Local paths, VCS URLs and flag values are not packages.** `-e human-eval`,
  `git+https://...`, `.` and `./sdk` are skipped, as is the value after `-r`/`--index-url`.
- **Registries with no download API are named, not measured.** `ghcr.io`, `quay.io`, `nvcr.io`
  and friends are reported with `no figure - <registry> publishes no pull count`. OS package
  managers (`apt-get install tensorflow-model-server`) are not extracted at all: there is no
  download figure to fetch, so there is nothing to report against the star count.
- **Linked install docs are followed one level, in-repo only, at most MAX_LINKED_DOCS.** The
  canonical case lives here: tensorflow/serving's README has the `docker pull` and NOT the
  `pip install tensorflow-serving-api`, which sits in `g3doc/setup.md` behind an "Install ..."
  link. A README-only read misses the 4.6M-a-month channel outright. So relative Markdown links
  whose text or path says install, setup, getting started, quickstart, docker, deploy, download or
  usage are fetched from the same repository and read as install instructions, with the document
  named in `found in:`. Links inside a linked document are NOT followed (the wiki-crawl trap),
  external URLs are not fetched (the docs site is not the repository's own instructions), and a
  linked document that answers non-200 is listed as unread the way a README is. A repository that
  keeps its install page somewhere the README does not link is still a miss; the report says
  which documents it read so a reader knows what was not.
- **A retrievable figure is not automatically the better instrument.** `uzu` on PyPI resolves to
  the right repository and drew 788 downloads a month against a Rust-primary distribution. The
  check prints the figure and the role; it does not compare it with the star count or call it a
  primary channel. The stage-impact and measurement-population rules in adoption.md govern that.
- **It is NOT in validate.yml.** It fetches a README per product and one to three registry
  responses per candidate, and pypistats rate-limits aggressively; a gate that 429s is a gate
  nobody reads. Run it by hand, ideally with `--limit` or `--slug`, before an adoption sweep.

Fetched bodies are cached under `build/package_channel_cache/` (gitignored) so a re-run does not
refetch; only 200 bodies are cached, so a 429 is never served from cache as an answer.

Usage:
    uv run python -m build.check_package_channel                 # every stars_fallback record
    uv run python -m build.check_package_channel --limit 30      # the first 30 by slug
    uv run python -m build.check_package_channel --slug typesense --slug lakefs
    uv run python -m build.check_package_channel --sleep 3       # pace registries harder (default 2s)

Exit 0 always. Report-only, the way `build/check_declarations.py` is.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import yaml

from build.fetch_source import fetch

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "build" / "package_channel_cache"

# Fewer retries than the digest re-fetch uses: a registry that is rate-limiting will keep doing
# so for the length of one run, and five retries with 2s*attempt backoff is 30s per package.
# The report says "no figure - HTTP 429" either way; the loss is only wall-clock.
REGISTRY_RETRIES = 3

# Seconds to wait before each registry request. Set from --sleep by main(); tests leave it 0.
# pypistats answered 429 to 7 of 22 candidates at a 1s pace with two retries on 2026-09-11, so
# the pause is not optional for a real walk and the default is 2s.
_PACE = 0.0

# Names that appear in install lines beside the product and are never the product. Each entry
# either caused a misattribution (#426: `packaging` at 2.19 BILLION monthly downloads from
# `pip install bigcodebench packaging`, `openai` at 418M from simple-evals) or plainly would.
# A token on this list is kept ONLY when it is one of the product's own names.
WELL_KNOWN_THIRD_PARTY = frozenset({
    # pip
    "packaging", "openai", "anthropic", "numpy", "torch", "torchvision", "torchaudio",
    "transformers", "datasets", "accelerate", "huggingface-hub", "requests", "setuptools",
    "wheel", "pip", "ninja", "flash-attn", "pandas", "scipy", "tqdm", "pydantic", "fastapi",
    "uvicorn", "flask", "python-dotenv", "streamlit", "gradio", "litellm", "tiktoken", "langchain",
    "langchain-openai", "langchain-community", "llama-index", "openai-agents", "jupyter",
    "notebook", "ipykernel", "matplotlib", "pytest", "pyyaml", "protobuf", "grpcio", "boto3",
    "google-cloud-storage", "sentencepiece", "tokenizers", "safetensors", "einops", "xformers",
    "bitsandbytes", "peft", "trl", "vllm", "sglang", "ollama", "mlx", "mlx-lm", "jax", "jaxlib",
    "tensorflow", "keras", "onnx", "onnxruntime", "opencv-python", "pillow", "diffusers", "modal",
    "hatch", "click", "ray", "s3fs", "psutil", "pyarrow", "timm", "poetry", "uv", "pipx",
    "virtualenv", "maturin", "cmake", "pre-commit", "black", "ruff", "mypy",
    # npm
    "typescript", "ts-node", "tsx", "dotenv", "express", "react", "react-dom", "next", "vite",
    "zod", "axios", "node-fetch", "@types/node",
    # cargo
    "tokio", "serde", "serde-json", "anyhow", "clap", "reqwest",
})

# Container registries that publish no pull count. The image is still reported, so a reader
# knows the product ships one, but with no figure and no invitation to find one.
REGISTRIES_WITHOUT_COUNTS = ("ghcr.io", "quay.io", "nvcr.io", "gcr.io", "mcr.microsoft.com",
                             "public.ecr.aws", "registry.gitlab.com")

# Role vocabulary read from a package's own summary.
CLIENT_WORDS = re.compile(
    r"\b(client|sdk|wrapper|bindings?|plugin|integration|connector|driver|python api|"
    r"api client|library for (?:the )?[\w .-]{0,40}\bapi|"
    r"(?:support|bindings|library|package) for (?:python|node(?:\.js)?|javascript|typescript|rust|go|java|ruby))\b",
    re.I,
)
# Product descriptions that read as a server, service or gateway. The #426 heuristic: such a
# product presumptively ships a client package. Applied only when the summary said nothing.
SERVER_WORDS = re.compile(
    r"\b(server|service|gateway|database|search engine|extension for postgres|postgres extension|"
    r"serving system|proxy|daemon)\b",
    re.I,
)

# A sentence in the note counts as a judgment about a candidate only if it names the channel
# too. A kind's own words settle it; the generic words (package, download, client ...) count
# only when no OTHER kind's word is in the sentence, so "the `uzu` package on PyPI drew 788
# downloads" is a judgment about the PyPI package and not about the npm package or the image.
CHANNEL_WORDS = {
    "pypi": re.compile(r"\b(pypi|pip|python|wheel)\b", re.I),
    "npm": re.compile(r"\b(npm|node|javascript|typescript|js)\b", re.I),
    "crates": re.compile(r"\b(crates?\.io|crate|cargo|rust)\b", re.I),
    "docker": re.compile(r"\b(docker|image|pulls?|container|hub)\b", re.I),
}
GENERIC_CHANNEL_WORDS = re.compile(r"\b(package|downloads?|sdk|client|wrapper|library|distribution)\b", re.I)

_PIP = re.compile(r"\b(?:pip3?|uv pip|uv|pipx|poetry)\s+(?:install|add)\b(.*)")
_NPM = re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+(?:install|i|add)\b(.*)")
_CARGO = re.compile(r"\bcargo\s+(?:add|install)\b(.*)")
_DOCKER_PULL = re.compile(r"\bdocker\s+pull\s+(\S+)")
_DOCKER_RUN = re.compile(r"\bdocker\s+run\b(.*)")
_IMAGE = re.compile(r"^(?:[a-z0-9.-]+(?::\d+)?/)?[a-z0-9_-]+(?:/[a-z0-9._-]+)*(?::[\w.-]+)?(?:@sha256:[0-9a-f]+)?$")
# Flags whose NEXT token is a value, across pip (-r, -e, -i ...) and docker run (-p, -v, -e ...).
_FLAG_WITH_VALUE = frozenset({
    "-r", "--requirement", "-e", "--editable", "-i", "--index-url", "-f", "--find-links", "-c",
    "--constraint", "-t", "--target", "-p", "--publish", "-v", "--volume", "--env", "--name",
    "--network", "-w", "--workdir", "--gpus", "--shm-size", "--mount", "--platform",
    "--entrypoint", "-u", "--user", "--env-file", "--add-host", "--memory", "--cpus",
    "--version", "--vers", "--git", "--branch", "--tag", "--rev", "--path", "--features",
    "--registry", "--root",
})
# A code line whose first non-blank character is `#` is a comment, not a command: scgpt's
# "# As of 2023.09, pip install may not run with new versions of the google orbax package ..."
# yielded `may`, `not`, `run` and eighteen more as PyPI candidates before this was skipped.
_COMMENT_LINE = re.compile(r"^\s*#")
_GITHUB_PATH = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)
# `[text](target)` with an optional `#anchor`; images (`![...]`) are excluded by the lookbehind.
_MD_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(\s*<?([^)\s>#]+)(?:#[^)]*)?>?\s*\)")
# A link is worth following when its TEXT or PATH says it is about installing. `docker` is on the
# list because "Install ... using Docker" pages carry the `docker pull`; `usage` because small
# projects put the install line on their usage page.
_INSTALL_LINK = re.compile(r"install|setup|set-up|getting[-_ ]?started|quick[-_ ]?start|docker|deploy|download|usage", re.I)
_LINKED_DOC_SUFFIXES = (".md", ".markdown", ".rst", ".txt")
MAX_LINKED_DOCS = 6
README_NAMES = ("README.md", "README.rst", "README", "readme.md")


@dataclass(frozen=True)
class Candidate:
    kind: str       # pypi | npm | crates | docker
    name: str       # normalized package or image name (no tag, no extras, no version)
    origin: str     # the install line it came from, or "declared artifact"


@dataclass
class Finding:
    slug: str
    candidate: Candidate
    prior_judgment: str | None = None
    ownership: str = ""
    ownership_evidence: str = ""
    role: str = ""
    role_quote: str = ""
    figure: str = ""
    recommendation: str = ""
    notes: list[str] = field(default_factory=list)

    def lines(self) -> list[str]:
        label = {"pypi": "PyPI", "npm": "npm", "crates": "crates.io", "docker": "image"}[self.candidate.kind]
        out = [f"{self.slug} -> {label} {self.candidate.name}"]
        if self.prior_judgment is not None:
            out.append(f"  PRIOR JUDGMENT RECORDED - read before changing: \"{self.prior_judgment}\"")
            out.append(f"  found in:    {self.candidate.origin}")
            return out
        out.append(f"  ownership:   {self.ownership} ({self.ownership_evidence})")
        out.append(f"  role:        {self.role} - {self.role_quote}")
        out.append(f"  figure:      {self.figure}")
        for note in self.notes:
            out.append(f"  note:        {note}")
        out.append(f"  recommendation: {self.recommendation}")
        out.append(f"  found in:    {self.candidate.origin}")
        return out


# ----------------------------------------------------------------------------------------------
# Fetching. One seam, so tests replace it and nothing else reaches the network.


def _cache_path(url: str) -> Path:
    return CACHE_DIR / f"{quote(url, safe='')[:150]}.body"


def fetch_text(url: str, retries: int = REGISTRY_RETRIES) -> tuple[int | None, str | None, bool]:
    """(http_status, body, transient). A transient status carries no body, on purpose.

    Goes through `fetch_source.fetch`, which retries 429/403/5xx and reports `transient: true`
    with no body when they survive, so a rate limit can never be read as a figure here either.
    Only 200 bodies are cached: a cached 429 would answer a later run with the rate limit
    instead of the fact, which is the failure this module exists to refuse.
    """
    cached = _cache_path(url)
    if cached.exists():
        return 200, cached.read_text(errors="replace"), False
    record = fetch(url, body_dir=CACHE_DIR, retries=retries)
    if record.get("transient"):
        return record.get("http_status"), None, True
    status = record.get("http_status")
    body_path = Path(record["body_path"]) if record.get("body_path") else None
    if status != 200:
        if body_path is not None:
            body_path.unlink(missing_ok=True)  # fetch keeps any <400 body; a 3xx page is not an answer
        return status, None, False
    if body_path is None:
        return status, None, False
    body = body_path.read_text(errors="replace")
    if body_path != cached:  # fetch canonicalized the URL; file it under the URL we asked for
        body_path.replace(cached)
    return 200, body, False


def _fetch_json(url: str) -> tuple[int | None, dict | None, bool]:
    status, body, transient = fetch_text(url)
    if body is None:
        return status, None, transient
    try:
        data = json.loads(body)
    except ValueError:
        return status, None, False
    return status, data if isinstance(data, dict) else None, False


# ----------------------------------------------------------------------------------------------
# Candidate extraction.


def _norm(name: str) -> str:
    """PEP 503-style: lowercase, runs of `-`, `_`, `.` and spaces become one hyphen."""
    return re.sub(r"[-_.\s]+", "-", name.strip().lower())


def _strip_version(token: str) -> str:
    token = token.strip("\"'`,;")
    if token.startswith("@"):
        head, _, _rest = token[1:].partition("@")  # @scope/name@1.2.3 -> @scope/name
        return "@" + head
    return re.split(r"[\[=<>!~@]", token, maxsplit=1)[0]


def _tokens(rest: str) -> list[str]:
    """The words of ONE command: cut at a pipe, a chained command, a comment or a subshell.
    `cargo install cargo-pgrx --version $(cargo metadata --format-version 1 | jq ...)` yielded
    `metadata`, `1` and `jq` as crates before the subshell cut was added."""
    rest = re.split(r"(?:&&|\|\||\||;|#|\$\(|`|\\$)", rest, maxsplit=1)[0]
    return rest.replace("\\", " ").split()


def _package_tokens(rest: str, allow_scoped: bool = False) -> list[str]:
    out: list[str] = []
    skip_next = False
    for raw in _tokens(rest):
        if skip_next:
            skip_next = False
            continue
        if raw in _FLAG_WITH_VALUE:
            skip_next = True
            continue
        if raw.startswith("-"):
            continue
        token = _strip_version(raw)
        if not token or token.startswith(".") or "://" in token or token.startswith("git+"):
            continue
        if "/" in token and not (allow_scoped and token.startswith("@")):
            continue
        if not re.match(r"^@?[A-Za-z0-9](?:[A-Za-z0-9._/-]*[A-Za-z0-9])?$", token):
            continue
        out.append(token)
    return out


def _image_token(rest: str) -> str | None:
    skip_next = False
    for raw in _tokens(rest):
        if skip_next:
            skip_next = False
            continue
        if raw in _FLAG_WITH_VALUE:
            skip_next = True
            continue
        if raw.startswith("-"):
            continue
        token = raw.strip("\"'`")
        if _IMAGE.match(token) and ("/" in token or "." in token or ":" in token):
            return token
        # the first positional that is not an image ends the hunt: `docker run foo bar`
        return None
    return None


def _image_name(token: str) -> str:
    token = token.split("@sha256:")[0]
    head, sep, tail = token.rpartition(":")  # strip a :tag, but not a registry :port
    if sep and "/" not in tail:
        token = head
    return token


def _candidate_name(kind: str, raw: str) -> str:
    if kind == "pypi":
        return _norm(raw)
    if kind == "crates":
        return raw.strip().lower()
    return raw.strip()


def own_names(product: dict) -> set[str]:
    """Names a candidate may carry and still be the product itself, normalized."""
    names = {_norm(product.get("name") or ""), _norm(product.get("display_name") or "")}
    for kind in ("pypi", "npm", "crates"):
        for artifact in product.get(kind) or []:
            url = (artifact.get("url") or "").rstrip("/")
            names.add(_norm(url.rsplit("/", 1)[-1]))
    for alias in product.get("aliases") or []:
        names.add(_norm(str(alias)))
    return {n for n in names if n}


_FENCE = re.compile(r"^\s*(```|~~~)")
_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_PRE_OPEN = re.compile(r"<pre\b", re.I)
_PRE_CLOSE = re.compile(r"</pre>", re.I)
_HTML_TAG = re.compile(r"<[^>]+>")


def code_segments(readme: str) -> list[str]:
    """The parts of a README that are code: fenced-block lines, indented-block lines, inline
    spans and `<pre>...</pre>` blocks (g3doc pages wrap their terminals in `<pre><code>`). Install
    instructions live there. Prose is skipped on purpose: "run `pip install tensorlake` for the
    Python SDK, install the CLI with ..." read as a command yields `for`, `the` and `install` as
    packages, and `first` is a real PyPI package at 665K downloads."""
    out: list[str] = []
    fence = None
    in_pre = False
    for line in readme.splitlines():
        if in_pre:
            out.append(_HTML_TAG.sub(" ", line))
            if _PRE_CLOSE.search(line):
                in_pre = False
            continue
        if _PRE_OPEN.search(line):
            in_pre = not _PRE_CLOSE.search(line)
            out.append(_HTML_TAG.sub(" ", line))
            continue
        match = _FENCE.match(line)
        if match:
            fence = None if fence == match.group(1) else (match.group(1) if fence is None else fence)
            continue
        if fence:
            out.append(line)
        elif line.startswith(("    ", "\t")):
            out.append(line)
        else:
            out.extend(_INLINE_CODE.findall(line))
    return out


def extract_candidates(readme: str, product: dict, document: str = "") -> list[Candidate]:
    """Package and image names the product's own install instructions install. `document` is
    the in-repo path the text came from and is carried into `found in:` so a reader can open it."""
    own = own_names(product)
    seen: set[tuple[str, str]] = set()
    out: list[Candidate] = []

    def add(kind: str, raw: str, line: str) -> None:
        name = _candidate_name(kind, raw)
        if not name or (kind, name) in seen:
            return
        seen.add((kind, name))
        origin = line.strip()[:120]
        out.append(Candidate(kind, name, f"{origin}  [{document}]" if document else origin))

    for line in code_segments(readme):
        if _COMMENT_LINE.match(line):
            continue
        for regex, kind, scoped in ((_PIP, "pypi", False), (_NPM, "npm", True), (_CARGO, "crates", False)):
            match = regex.search(line)
            if not match:
                continue
            for token in _package_tokens(match.group(1), allow_scoped=scoped):
                if _norm(token) in WELL_KNOWN_THIRD_PARTY and _norm(token) not in own:
                    continue
                add(kind, token, line)
        match = _DOCKER_PULL.search(line)
        if match:
            add("docker", _image_name(match.group(1).strip("\"'`")), line)
        match = _DOCKER_RUN.search(line)
        if match:
            image = _image_token(match.group(1))
            if image:
                add("docker", _image_name(image), line)
    return out


def declared_candidates(product: dict) -> list[Candidate]:
    """A declared package artifact on a stars record is itself worth a line: the product
    already names a countable channel and the axis is not read from it."""
    out = []
    for kind in ("pypi", "npm", "crates"):
        for artifact in product.get(kind) or []:
            url = (artifact.get("url") or "").rstrip("/")
            name = url.rsplit("/", 1)[-1]
            if name:
                out.append(Candidate(kind, _candidate_name(kind, name), "declared artifact"))
    return out


# ----------------------------------------------------------------------------------------------
# The three questions.


def declared_repos(product: dict) -> list[tuple[str, str]]:
    repos = []
    for artifact in product.get("github") or []:
        match = _GITHUB_PATH.search((artifact.get("url") or "").rstrip("/"))
        if match:
            repos.append((match.group(1).lower(), match.group(2).removesuffix(".git").lower()))
    return repos


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _project_names(product: dict) -> set[str]:
    """Squashed names the homepage or author may carry: slug, display name, repository names.
    OWNER names are excluded deliberately - that is the substring trap (#426, failure 2)."""
    names = {_squash(n) for n in own_names(product)}
    for _owner, repo in declared_repos(product):
        names.add(_squash(repo))
    return {n for n in names if len(n) >= 3}


def _name_tokens(text: str) -> set[str]:
    return {_squash(t) for t in re.split(r"[/.\s:,_-]+", text.lower()) if t}


def grade_ownership(meta: dict, product: dict) -> tuple[str, str]:
    """(grade, evidence).

    strong: a package URL names the declared owner/repo in full.
    weak:   a URL or the author names the PROJECT (not merely its owner); no repository link.
    none:   nothing in the metadata connects the two.

    There is no grade for "same owner, different repository". `typesense/typesense-python` is
    a sibling of `typesense/typesense`, and `openai/openai-python` is a sibling of
    `openai/simple-evals`; the first is the product's client and the second is unrelated, and
    the owner segment cannot tell them apart. The name rule can: `typesense-python` names the
    project and `openai-python` does not.
    """
    repos = declared_repos(product)
    urls = [(k, v) for k, v in (meta.get("urls") or {}).items() if v]
    for label, url in urls:
        match = _GITHUB_PATH.search(url)
        if not match:
            continue
        owner, repo = match.group(1).lower(), match.group(2).removesuffix(".git").lower()
        if (owner, repo) in repos:
            return "strong", f"{label} -> {owner}/{repo}, the declared repository"
    names = _project_names(product)
    for label, url in urls:
        if names & _name_tokens(url):
            return "weak", f"{label} {url} names the project; no link to the declared repository"
    author = meta.get("author") or ""
    if author and names & _name_tokens(author):
        return "weak", f"author \"{author}\" names the project; no link to the declared repository"
    declared = "/".join(repos[0]) if repos else "the project"
    if author:
        return "none", f"no URL or author names {declared}; author is \"{author}\""
    return "none", f"no URL or author names {declared}"


def label_role(summary: str | None, product: dict) -> tuple[str, str]:
    """(label, quote). The summary decides when it can; the product-shape heuristic labels the
    rest and says it is presumptive. The quote is always printed so a reader can disagree."""
    summary = (summary or "").strip().strip('"')
    description = product.get("description") or ""
    quote_ = f"\"{summary}\"" if summary else "no summary published"
    if summary and CLIENT_WORDS.search(summary):
        if CLIENT_WORDS.search(description):
            return ("PRODUCT-IS-SDK", f"{quote_}; the product's own description also reads as an "
                    "SDK/client, so this wording does not separate the package from the product")
        return "CLIENT/SDK", quote_
    if SERVER_WORDS.search(description):
        return ("CLIENT (presumptive)", f"{quote_}; the product reads as a server/service/gateway, "
                "so a package is presumptively its client")
    return ("PRODUCT (presumptive)", f"{quote_}; the product reads as a library/CLI/runtime, so "
            "the package is presumptively the product itself")


def _fmt(n) -> str:
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


def _no_figure(status, transient: bool) -> str:
    if transient:
        shown = status if status is not None else "error"
        return f"no figure - HTTP {shown} (transient; says nothing about whether a figure exists; never a zero)"
    return f"no figure - HTTP {status}"


def read_pypi(name: str) -> tuple[dict | None, str, bool]:
    """(meta, figure line, transient). meta is None when the registry did not answer 200."""
    status, data, transient = _fetch_json(f"https://pypi.org/pypi/{name}/json")
    if data is None:
        return None, _no_figure(status, transient), transient
    info = data.get("info") or {}
    urls = dict(info.get("project_urls") or {})
    if info.get("home_page"):
        urls.setdefault("home_page", info["home_page"])
    meta = {"summary": info.get("summary"), "author": info.get("author") or info.get("author_email"), "urls": urls}
    status, stats, transient = _fetch_json(f"https://pypistats.org/api/packages/{name}/recent")
    if stats is None:
        return meta, _no_figure(status, transient), transient
    month = (stats.get("data") or {}).get("last_month")
    if month is None:
        return meta, "no figure - pypistats answered without last_month", False
    return meta, f"{_fmt(month)} monthly (pypistats recent.last_month, trailing 30 days)", False


def read_npm(name: str) -> tuple[dict | None, str, bool]:
    status, data, transient = _fetch_json(f"https://registry.npmjs.org/{name}")
    if data is None:
        return None, _no_figure(status, transient), transient
    repo = data.get("repository")
    repo_url = repo.get("url") if isinstance(repo, dict) else repo
    urls = {k: v for k, v in {"repository": repo_url, "homepage": data.get("homepage")}.items() if v}
    author = data.get("author")
    author = author.get("name") if isinstance(author, dict) else author
    meta = {"summary": data.get("description"), "author": author, "urls": urls}
    status, stats, transient = _fetch_json(f"https://api.npmjs.org/downloads/point/last-month/{name}")
    if stats is None or "downloads" not in stats:
        return meta, _no_figure(status, transient), transient
    return meta, (f"{_fmt(stats['downloads'])} monthly (npm point/last-month, 30 days "
                  f"{stats.get('start')} to {stats.get('end')})"), False


def read_crates(name: str) -> tuple[dict | None, str, bool]:
    status, data, transient = _fetch_json(f"https://crates.io/api/v1/crates/{name}")
    if data is None or "crate" not in data:
        if data is not None and data.get("errors"):
            return None, "no figure - HTTP 200 but crates.io reports the crate does not exist", False
        return None, _no_figure(status, transient), transient
    crate = data["crate"]
    urls = {k: v for k, v in {"repository": crate.get("repository"), "homepage": crate.get("homepage")}.items() if v}
    meta = {"summary": crate.get("description"), "author": None, "urls": urls}
    recent = crate.get("recent_downloads")
    if recent is None:
        return meta, "no figure - crates.io answered without recent_downloads", False
    return meta, f"{_fmt(recent)} over 90 days (crates.io recent_downloads; a 90-day window, NOT a monthly figure)", False


def read_docker(image: str) -> tuple[dict | None, str, bool]:
    if image.startswith(REGISTRIES_WITHOUT_COUNTS):
        registry = image.split("/")[0]
        return {"summary": None, "author": None, "urls": {}, "registry": registry}, \
            f"no figure - {registry} publishes no pull count", False
    if image.startswith("docker.io/"):
        image = image[len("docker.io/"):]
    namespace, _, name = image.partition("/")
    if not name:
        namespace, name = "library", namespace
    status, data, transient = _fetch_json(f"https://hub.docker.com/v2/repositories/{namespace}/{name}/")
    if data is None:
        return None, _no_figure(status, transient), transient
    meta = {"summary": data.get("description"), "author": data.get("user") or namespace, "urls": {},
            "namespace": namespace, "name": name}
    pulls = data.get("pull_count")
    if pulls is None:
        return meta, "no figure - Docker Hub answered without pull_count", False
    return meta, (f"{_fmt(pulls)} pulls CUMULATIVE since publication (Docker Hub pull_count; the "
                  "scale is monthly, so corroboration only, never a band)"), False


def grade_docker_ownership(meta: dict, product: dict) -> tuple[str, str]:
    """Docker Hub metadata carries no repository link, so the best available grade is weak:
    the image's namespace AND name equal the declared owner/repo, or its name or description
    names the project. A namespace match alone is the owner-substring trap and grades none."""
    repos = declared_repos(product)
    ns, name = meta.get("namespace", ""), meta.get("name", "")
    names = _project_names(product)
    if any(ns == owner and name == repo for owner, repo in repos):
        return "weak", f"namespace/name {ns}/{name} equals the declared owner/repo; Docker Hub publishes no repository link to confirm"
    if names & _name_tokens(name) or names & _name_tokens(meta.get("summary") or ""):
        return "weak", f"image name or description names the project; namespace is {ns}"
    return "none", f"image {ns}/{name} names neither the declared repository nor the project"


READERS = {"pypi": read_pypi, "npm": read_npm, "crates": read_crates, "docker": read_docker}


# ----------------------------------------------------------------------------------------------
# Prior judgment.


def prior_judgment(adoption: dict, candidate: Candidate) -> str | None:
    """The sentence of the record's note (or its reach) that names the candidate AND its
    channel, or None. Naming alone is not enough: a product's own name is in nearly every
    note, and "pgvector has 22,664 stars" is not a judgment about the pgvector image."""
    name = candidate.name
    bare = name.rsplit("/", 1)[-1]  # `pgvector/pgvector` -> match on either form
    forms = {re.escape(name), re.escape(bare), re.escape(bare).replace("\\-", "[-_]")}
    pattern = re.compile(r"(?<![\w.-])(" + "|".join(sorted(forms)) + r")(?![\w-])", re.I)
    reach = str(adoption.get("reach") or "")
    if pattern.search(reach) and _names_channel(reach, candidate.kind):
        return f"reach: {reach}"
    note = str(adoption.get("note") or "")
    for sentence in re.split(r"(?<=[.!?])\s+", note):
        if pattern.search(sentence) and _names_channel(sentence, candidate.kind):
            return sentence.strip()
    return None


def _names_channel(sentence: str, kind: str) -> bool:
    if CHANNEL_WORDS[kind].search(sentence):
        return True
    if any(words.search(sentence) for other, words in CHANNEL_WORDS.items() if other != kind):
        return False
    return bool(GENERIC_CHANNEL_WORDS.search(sentence))


# ----------------------------------------------------------------------------------------------
# Per-product assessment.


def recommend(candidate: Candidate, ownership: str, role: str, figure: str, transient: bool,
              same_name: bool = False) -> str:
    if transient:
        return "RETRY - the registry declined to answer; nothing here is a finding yet"
    if ownership == "none" and same_name:
        # adoption.md, third trap: a package sharing the product's name is not evidence that it
        # is the product - and it is not evidence that it is somebody else's either.
        return ("UNVERIFIED - shares the product's name and nothing in its metadata links it to the "
                "declared repository; a same-named package is not evidence either way (adoption.md, "
                "third trap), so a person checks the publisher before this figure is weighed")
    if candidate.kind == "docker":
        if ownership == "none":
            return "IGNORE - image is not this project's"
        return ("CORROBORATION ONLY - cumulative pulls cannot be banded on a monthly scale; a person "
                "may cite them in the note")
    if figure.startswith("no figure"):
        if ownership == "none":
            return "IGNORE - not this project's package, and no figure"
        return "NO FIGURE - registry answered but published no count; nothing to weigh"
    if ownership == "none":
        return "IGNORE - not this project's package; the figure belongs to someone else"
    if role == "CLIENT/SDK":
        return "REVIEW - do not auto-route; the package's own summary says it is a client of the product"
    if role == "CLIENT (presumptive)":
        return ("REVIEW - the product reads as a server/service, so the package is presumptively its "
                "client; the summary does not say, so a person reads the package before weighing the figure")
    if ownership == "weak":
        return ("REVIEW - ownership is not established by a repository link; confirm the publisher "
                "before weighing the figure")
    return ("REVIEW - owned and reads as the product itself; a person decides whether this is the "
            "primary channel (adoption.md, third trap) and records it in the note")


def readme_text(product: dict) -> tuple[str | None, str]:
    """(README body, `path` or status line) for the first declared github artifact."""
    repos = declared_repos(product)
    if not repos:
        return None, "no github artifact declared"
    owner, repo = repos[0]
    last = "not fetched"
    for filename in README_NAMES:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{filename}"
        status, body, transient = fetch_text(url)
        if body is not None:
            return body, filename
        last = _no_figure(status, transient).replace("no figure - ", "")
        if transient:
            break
    return None, f"README of {owner}/{repo}: {last}"


def install_doc_links(readme: str, readme_path: str = "README.md") -> list[str]:
    """In-repo paths the README links to under an install-shaped name, in README order, capped
    at MAX_LINKED_DOCS. Relative links only: an absolute URL is the docs site or someone else's
    repository, not this repository's own instructions. Resolved against the README's directory
    so `docs/install.md` from a root README and `../setup.md` from a nested one both land."""
    base = posixpath.dirname(readme_path)
    out: list[str] = []
    for text, target in _MD_LINK.findall(readme):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("//"):
            continue
        if not target.lower().endswith(_LINKED_DOC_SUFFIXES):
            continue
        if not (_INSTALL_LINK.search(text) or _INSTALL_LINK.search(target)):
            continue
        path = posixpath.normpath(posixpath.join(base, target.lstrip("/")))
        if path.startswith("..") or path in out or path == readme_path:
            continue
        out.append(path)
        if len(out) == MAX_LINKED_DOCS:
            break
    return out


def install_docs(product: dict) -> tuple[list[tuple[str, str]], list[str]]:
    """([(in-repo path, body)], [what could not be read]) - the README first, then the install
    documents it links to, one level down and never outside the repository."""
    repos = declared_repos(product)
    readme, where = readme_text(product)
    if readme is None:
        return [], [where]
    owner, repo = repos[0]
    docs = [(where, readme)]
    unread: list[str] = []
    for path in install_doc_links(readme, where):
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{quote(path)}"
        status, body, transient = fetch_text(url)
        if body is None:
            unread.append(f"linked {path}: {_no_figure(status, transient).replace('no figure - ', '')}")
            continue
        docs.append((path, body))
    return docs, unread


def assess(slug: str, product: dict, score: dict,
           docs: str | list[tuple[str, str]] | None) -> list[Finding]:
    """`docs` is the list `install_docs` returns; a bare string is read as a README on its own."""
    if isinstance(docs, str):
        docs = [("", docs)]
    adoption = score.get("adoption") or {}
    candidates = declared_candidates(product)
    seen = {(c.kind, c.name) for c in candidates}
    for path, body in docs or []:
        for candidate in extract_candidates(body, product, document=path):
            if (candidate.kind, candidate.name) not in seen:
                seen.add((candidate.kind, candidate.name))
                candidates.append(candidate)

    findings: list[Finding] = []
    for candidate in candidates:
        finding = Finding(slug=slug, candidate=candidate)
        prior = prior_judgment(adoption, candidate)
        if prior is not None:
            finding.prior_judgment = prior
            findings.append(finding)
            continue
        if _PACE:
            time.sleep(_PACE)
        meta, figure, transient = READERS[candidate.kind](candidate.name)
        finding.figure = figure
        if meta is None:
            finding.ownership, finding.ownership_evidence = "unknown", "registry did not answer 200, so no metadata to read"
            finding.role, finding.role_quote = "UNKNOWN", "no summary available"
        elif candidate.kind == "docker":
            finding.ownership, finding.ownership_evidence = grade_docker_ownership(meta, product)
            described = f"\"{meta['summary']}\"" if meta.get("summary") else "no description published"
            finding.role, finding.role_quote = "IMAGE", f"{described}; an image is the product itself when it is the project's own"
        else:
            finding.ownership, finding.ownership_evidence = grade_ownership(meta, product)
            if finding.ownership == "none" and candidate.origin == "declared artifact":
                # The corpus already says this is the product's package; the registry metadata
                # naming no repository is a gap in the metadata, not a doubt about ownership.
                finding.ownership = "declared"
                finding.ownership_evidence = ("declared as a product artifact in sources/products; "
                                              f"the registry metadata itself is silent ({finding.ownership_evidence})")
            finding.role, finding.role_quote = label_role(meta.get("summary"), product)
        if candidate.origin == "declared artifact":
            finding.notes.append("this package is a DECLARED artifact and the record still bands on stars")
        same_name = _squash(candidate.name.rsplit("/", 1)[-1]) in _project_names(product)
        finding.recommendation = recommend(candidate, finding.ownership, finding.role, figure, transient, same_name)
        findings.append(finding)
    return findings


def stars_fallback_records(root: Path | None = None) -> list[tuple[str, dict, dict]]:
    root = root or ROOT
    out = []
    for path in sorted((root / "sources" / "scores").glob("*.yaml")):
        score = yaml.safe_load(path.read_text()) or {}
        if ((score.get("adoption") or {}).get("signal_type")) != "stars_fallback":
            continue
        product_path = root / "sources" / "products" / path.name
        if not product_path.exists():
            continue
        out.append((path.stem, yaml.safe_load(product_path.read_text()) or {}, score))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report stars_fallback records with a measurable package channel.")
    parser.add_argument("--limit", type=int, help="stop after this many stars_fallback records (by slug)")
    parser.add_argument("--slug", action="append", help="only these product slugs (repeatable)")
    parser.add_argument("--sleep", type=float, default=2.0, help="seconds between requests, to pace registries")
    args = parser.parse_args(argv)
    global _PACE
    _PACE = max(args.sleep, 0.0)

    records = stars_fallback_records()
    if args.slug:
        records = [r for r in records if r[0] in set(args.slug)]
    if args.limit:
        records = records[: args.limit]

    findings: list[Finding] = []
    unread: list[str] = []
    for slug, product, score in records:
        docs, problems = install_docs(product)
        unread.extend(f"{slug}: {problem}" for problem in problems)
        findings.extend(assess(slug, product, score, docs))

    fresh = [f for f in findings if f.prior_judgment is None]
    prior = [f for f in findings if f.prior_judgment is not None]
    print(f"{len(records)} stars_fallback record(s) walked, {len(findings)} candidate package(s) or image(s): "
          f"{len(fresh)} finding(s), {len(prior)} with a prior judgment recorded")
    for finding in findings:
        print()
        print("\n".join(finding.lines()))
    if unread:
        print(f"\n{len(unread)} README or linked install document(s) that could not be read "
              "(the rest of the record was still checked):")
        for line in unread:
            print(f"  ~ {line}")
    print("\nReport-only. Nothing above is a band. Identity, role and instrument are three separate")
    print("questions and a REVIEW line means a person answers them and records the answer in the")
    print("adoption note; a PRIOR JUDGMENT line means someone already did. See the module docstring.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
