"""Two gates on the prose inside `build/`, which until now nothing read.

Every prose gate in this repo points at `sources/` or `docs/` — score notes, product
descriptions, the doc surface. `build/` was unguarded, and #573 is what that costs:
`parse_version` offered `openlit-2.0.0` as an example of a tag carrying no version when it
parses to `(2, 0, 0)`, and `newest_pypi_release` said it read the release history "rather than
off `info.version`" while reading `info.version`. Both sentences shipped, and both are printed
to a user — a module docstring here is an argparse `description`, so it is `--help` output, not
an internal comment.

The two checks below are the mechanical residue of those two defects:

  1. **No live census in an executable docstring.** A count of the corpus in `--help` is a copy
     of a number the program itself computes, and it goes stale the next time the corpus moves.
     Same shape as `test_score_notes.py`'s date rule one directory over: a regex, a named
     allowlist, and a staleness test so the allowlist cannot outlive what it excuses.
  2. **An example in a docstring is not contradicted by the function.** The value is extracted
     and the function is called. This is the one that would have caught `parse_version` on the
     day it was written — it reads both a declared `Examples:` block and the one prose shape
     the original false claim was written in, because a gate that only read the block would
     have found nothing to check in the file it was written for.

Neither reads `sources/`, which is why they live here rather than in `test_score_notes.py` or
`test_product_prose.py`: those two take the corpus fixture and are about a curator's prose,
these two parse `build/*.py` and are about a maintainer's. Bolting them onto a module whose own
docstring argues about notes-under-axes would have made both files harder to read.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"


def _documented_modules() -> list[Path]:
    """Every `build/*.py` whose module docstring is printed by `--help`.

    The test is textual on purpose: `description=__doc__` is the one construction in this repo
    that puts a module docstring in front of a user, and a module acquires the gate by writing
    it, not by being added to a list here.
    """
    return sorted(p for p in BUILD.glob("*.py") if "description=__doc__" in p.read_text())


def _module_docstring(path: Path) -> str:
    return ast.get_docstring(ast.parse(path.read_text())) or ""


# ── Gate 1: no live census in an executable docstring ───────────────────────────────────────

_CARDINAL = (
    r"(?:\d+|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen"
    r"|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty)"
)
# Only the nouns that name things this repo COUNTS and that a build module recomputes and
# prints. `categories` is left out because the taxonomy is declared rather than measured, and
# "one product" / "a record" are left out because a singular is a shape, not a census.
_COUNTED = r"(?:records?|products?|fires?|notes?|slugs?)"
CENSUS = re.compile(rf"\b{_CARDINAL}\s+(?:[\w-]+\s+)??{_COUNTED}\b", re.IGNORECASE)

# A roster is the other way a docstring copies the corpus: the names instead of the number.
# Three or more backticked tokens in a comma-separated run, every one of them a real product
# slug. The slug test is what keeps `note`, `sources`, `confidence` — a list of FIELDS — out of
# it, and the threshold is three so that naming the one or two cases an argument turns on
# ("Both catch `areal` and `xtuner`") stays allowed. That is reasoning; a roster is inventory.
_RUN = re.compile(r"`[^`\n]+`(?:\s*,\s*`[^`\n]+`){2,}")
_TOKEN = re.compile(r"`([^`\n]+)`")


def _slugs() -> set[str]:
    return {p.stem for p in (ROOT / "sources" / "products").glob("*.yaml")}


def census_phrases(doc: str, slugs: set[str]) -> list[str]:
    """Every phrase in `doc` that states a live count or lists a roster, whitespace-normalized.

    Normalized because these docstrings are hand-wrapped: the same phrase re-wrapped at a
    different width is the same phrase, and the allowlist below has to survive a reflow.
    """
    found = [" ".join(m.group(0).split()) for m in CENSUS.finditer(doc)]
    for match in _RUN.finditer(doc):
        tokens = _TOKEN.findall(match.group(0))
        if all(token in slugs for token in tokens):
            found.append(" ".join(match.group(0).split()))
    return found


# The backlog, frozen 2026-09-20 when the gate was written. Every entry is a real count in a
# real `--help` output; none of them is this PR's to rewrite, and #573 is about `build/
# check_channel_authority.py`. Named per phrase so that fixing one is a one-line deletion and
# writing a new one is a failure. Do not add to this list to make the suite pass — that is the
# failure working.
#
# Two of these are the detector reading a shape as a census: `check_capability`'s "two
# different products" and `serialize_registry`'s "Two structural notes" count cases in an
# argument, not records in the corpus. They are listed rather than excused by a looser regex,
# because every loosening tried here also let a real census through.
CENSUS_BACKLOG: dict[str, set[str]] = {
    "check_adoption.py": {"472 products", "14 dataset products", "217 off-scale records"},
    "check_capability.py": {"472 products", "two different products"},
    "check_instrument.py": {
        "56 products", "55 records", "40 records",
        "`mcp-typescript-sdk`, `openclaw`, `langchain`, `ray`, `firecracker`, `aws-lambda`",
    },
    "check_parity.py": {"Six products"},
    "check_rubric.py": {"30 products"},
    "preflight.py": {"five products"},
    "propose_artifacts.py": {"472 products", "44 non-closed products"},
    "prose_worklist.py": {"289 notes"},
    "reverify.py": {"25 oldest products"},
    "serialize_registry.py": {"Two structural notes"},
}


@pytest.fixture(scope="module")
def slugs() -> set[str]:
    return _slugs()


def test_no_help_text_states_a_live_census(slugs):
    """A docstring that reaches `--help` does not carry a count of the corpus.

    The module that prompted this said, in the same bullet, "Four records are excluded this way
    today — `flash-attention`, `khoj`, `lance`, `mineru` — and the report prints the list, so
    this docstring does not become a second copy of a count that moves." It was already the
    second copy. The report prints the live number on every run; the docstring printed a
    number from the day it was written, to the same reader, above the report.
    """
    offenders = [
        f"{path.name}: {phrase!r}"
        for path in _documented_modules()
        for phrase in census_phrases(_module_docstring(path), slugs)
        if phrase not in CENSUS_BACKLOG.get(path.name, set())
    ]
    assert not offenders, (
        f"{len(offenders)} `--help` docstring(s) state a live count of the corpus:\n  "
        + "\n  ".join(sorted(offenders))
        + "\n\nThe run prints the count; the docstring says what the check decides and why. If "
        "the number is a fact about the design rather than about the corpus, say it without a "
        "cardinal, or add the phrase to CENSUS_BACKLOG with that justification."
    )


def test_the_census_backlog_has_not_gone_stale(slugs):
    """A phrase that has been rewritten must leave the backlog, not linger in it.

    Otherwise the list stops describing the backlog and starts hiding it — it would keep
    passing long after the counts were gone, and the next real census would have somewhere to
    sit unnoticed. Same two-sided shape as the allowlists in `test_score_notes.py`.
    """
    live = {
        path.name: set(census_phrases(_module_docstring(path), slugs))
        for path in _documented_modules()
    }
    stale = [
        f"{name}: {phrase!r}"
        for name, phrases in CENSUS_BACKLOG.items()
        for phrase in phrases
        if phrase not in live.get(name, set())
    ]
    assert not stale, (
        f"{sorted(stale)} no longer appear in their module's docstring — remove them from "
        "CENSUS_BACKLOG so the list keeps meaning what it says."
    )


# ── Gate 2: a docstring's example is not contradicted by its function ────────────────────────

# The convention, and the whole of it: inside a function docstring, a line `Examples:` opens a
# block, and each following line of the form
#
#     `<argument>` -> <repr of the expected return>
#
# is executed. The argument is the backticked token, passed as a string; the claim is compared
# against `repr()` of what the function returns. The block ends at the first line that is not
# an example.
#
# Narrow on purpose. It reads one string argument, because that is the shape of the functions
# whose examples were wrong, and a convention that covers every signature is a convention
# nobody writes correctly. A function with two parameters documents its cases in prose and is
# not checked here; `lag_verdict` is the live instance.
EXAMPLE_HEADING = re.compile(r"^\s*Examples?:\s*$")
EXAMPLE_LINE = re.compile(r"^\s*`([^`\n]+)`\s*->\s*(\S.*?)\s*$")

# A module opts in by being named here AND writing at least one example. Both halves matter:
# the list is what says "this module's examples are executable", and the coverage assertion is
# what stops a module joining the list and checking nothing.
CHECKED_MODULES = ("build.check_channel_authority",)


def docstring_examples(doc: str) -> list[tuple[str, str]]:
    """(argument, claimed repr) pairs from a docstring's `Examples:` block."""
    pairs: list[tuple[str, str]] = []
    in_block = False
    for line in (doc or "").splitlines():
        if EXAMPLE_HEADING.match(line):
            in_block = True
            continue
        if not in_block:
            continue
        matched = EXAMPLE_LINE.match(line)
        if matched:
            pairs.append((matched.group(1), matched.group(2)))
        elif line.strip():
            in_block = False
    return pairs


# The second extractor, and the reason there is one. The claim that prompted #573 was never
# written in the block convention above — it was a sentence: "A tag like `2026-08-01` or
# `openlit-2.0.0` is not evidence of an absent lag". A gate that only reads `Examples:` blocks
# would have passed that file on the day the false claim was written, because the file had no
# such block. So one prose shape is read as well, the narrowest one that covers it:
#
#     a run of backticked tokens, joined by `,` / `or` / `and`, immediately followed by a
#     phrase that denies the function finds anything in them
#
# and the claim it asserts is always `None` — the tokens are passed one at a time and each
# return must be `None`. Two guards keep that from becoming a guess:
#
#   * the denial vocabulary is closed and listed below, not inferred from the sentence;
#   * the function must declare `None` in its summary line and take exactly one required
#     parameter, so a sentence can never assert a return the function cannot produce.
#
# Everything else in prose is left alone. A positive claim in prose ("`openlit-2.0.0` yields a
# version") is NOT read: write it in an `Examples:` block, which is checkable without reading
# English for the expected value.
_DENIAL = (
    r"(?:is|are)\s+not\s+evidence"
    r"|carr(?:y|ies)\s+no\s+version"
    r"|do(?:es)?\s+not\s+(?:carry|parse)"
)
PROSE_NONE_CLAIM = re.compile(
    r"(?P<tokens>`[^`\n]+`(?:\s*(?:,|or|and)\s*`[^`\n]+`)+|`[^`\n]+`)\s+(?:" + _DENIAL + r")",
    re.IGNORECASE,
)
_DECLARES_NONE = re.compile(r"\bNone\b")


def prose_none_claims(doc: str) -> list[tuple[str, str]]:
    """(argument, `'None'`) pairs from a docstring sentence that denies a quoted token.

    Whitespace-normalized first: these docstrings are hand-wrapped, and the run of tokens and
    the denial that follows it routinely land on different lines.
    """
    flat = " ".join((doc or "").split())
    if not flat:
        return []
    summary = flat.split(". ")[0]
    if not _DECLARES_NONE.search(summary):
        return []
    pairs: list[tuple[str, str]] = []
    for match in PROSE_NONE_CLAIM.finditer(flat):
        for token in _TOKEN.findall(match.group("tokens")):
            pairs.append((token, "None"))
    return pairs


def _takes_one_required_string(function) -> bool:
    try:
        parameters = list(inspect.signature(function).parameters.values())
    except (TypeError, ValueError):
        return False
    return len(parameters) == 1 and parameters[0].default is inspect.Parameter.empty


def _checked_functions(module_name: str, *, prose: bool = True):
    module = importlib.import_module(module_name)
    for name in sorted(dir(module)):
        function = getattr(module, name)
        if not callable(function) or getattr(function, "__module__", "") != module_name:
            continue
        doc = getattr(function, "__doc__", "") or ""
        for argument, claimed in docstring_examples(doc):
            yield name, function, argument, claimed
        if not prose or not _takes_one_required_string(function):
            continue
        for argument, claimed in prose_none_claims(doc):
            yield name, function, argument, claimed


@pytest.mark.parametrize("module_name", CHECKED_MODULES)
def test_every_documented_example_is_what_the_function_returns(module_name):
    """Call the function with the value its docstring quotes; compare against the claim.

    `parse_version`'s docstring claimed `openlit-2.0.0` carried no version for as long as it
    existed. It returns `(2, 0, 0)`: `_VERSION` anchors on any non-digit before the number, so
    a package-prefixed tag parses like any other. Nothing could catch that but running it.
    """
    wrong = []
    for name, function, argument, claimed in _checked_functions(module_name):
        actual = repr(function(argument))
        if actual != claimed:
            wrong.append(f"{name}(`{argument}`) -> {actual}, docstring says {claimed}")
    assert not wrong, (
        f"{len(wrong)} documented example(s) in {module_name} contradict the function:\n  "
        + "\n  ".join(wrong)
        + "\n\nThe function is right by definition here. Fix the sentence, or fix the function "
        "and then the sentence."
    )


@pytest.mark.parametrize("module_name", CHECKED_MODULES)
def test_a_checked_module_actually_documents_an_example(module_name):
    """A module on the list with no examples is a gate that passes by covering nothing.

    Declared blocks only — `prose=False`. The prose extractor fires on whatever sentences a
    module happens to contain, so counting its hits as coverage would let a module satisfy
    this assertion without anyone having written a single checkable example.
    """
    found = list(_checked_functions(module_name, prose=False))
    assert found, (
        f"{module_name} is in CHECKED_MODULES but documents no `Examples:` block, so nothing "
        "in it is checked. Write one in the convention above, or take the module off the list."
    )
