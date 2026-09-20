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
import datetime
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


# THERE IS NO DATING EXEMPTION, and three rounds of adversarial review are why.
#
# The intuition was sound: "Four records are excluded this way today" is a second copy of a number
# the report prints live, while "Measured 2026-08-13, 56 products claim exactly that" records an
# observation at a moment and cannot go stale. Three mechanisms were built to tell those apart,
# and every one was talked around:
#
#   PARAGRAPH scope   an unrelated measurement licensed a later live count ("... measured
#                     2026-08-13. Today 56 products ..."); a count stated before its date was
#                     dated by it; a negation licensed; an impossible date licensed.
#   SENTENCE scope    a quoted sentence ending stopped the split, so the exemption ran on; a
#                     negation using a verb missing from the guard list licensed.
#   DECLARED opener   a live count SMUGGLED into a legitimately declared sentence was exempt
#                     ("Measured 2026-08-13, 56 products did X and today 60 products do Y");
#                     a markdown list item after a measurement was exempt; an indented code block
#                     became a declaration; and the claim that a mis-split could only ever REFUSE
#                     an exemption turned out false - an unsupported closing mark granted one.
#
# Each fix was a wider vocabulary, a moved boundary, or a new convention, and each was defeated by
# the next reader. This repository has a rule for that situation: a line that takes more than two
# attempts to state consistently is probably not there. It is not there. Deciding from prose
# whether a number is historical is a judgement, and this gate does not make judgements.
#
# So the gate reports every census phrase, and CENSUS_BACKLOG carries the ones a human has read
# and accepted, each with a reason and a staleness test. That list is longer than a clever rule
# would have left it. It is also finite, inspectable, and impossible to talk around, because
# there is no prose being parsed. Do not reintroduce an exemption: the next one will be defeated
# too, and the failure mode is a live count silently passing.


def census_phrases(doc: str, slugs: set[str]) -> list[str]:
    """Every phrase in `doc` that states a live count or lists a roster, whitespace-normalized.

    Normalized because these docstrings are hand-wrapped: the same phrase re-wrapped at a
    different width is the same phrase, and the allowlist below has to survive a reflow.

    Every phrase is returned, dated or not. Judging that from prose was tried three times and
    defeated three times — see the note above CENSUS_BACKLOG.
    """
    found = [" ".join(m.group(0).split()) for m in CENSUS.finditer(doc)]
    for match in _RUN.finditer(doc):
        tokens = _TOKEN.findall(match.group(0))
        if all(token in slugs for token in tokens):
            found.append(" ".join(match.group(0).split()))
    return found


# What the detector still reports and why each one stays. Every entry here has been read in
# context and none of them is a live count of the corpus: they are quotations, dated history,
# counterfactuals, hypotheticals, or the detector reading a shape as a census. The reason is
# required — a bare list stops being a backlog and becomes a place for a real census to hide.
#
# This list was ten modules on 2026-09-20, before the dated-measurement rule above existed and
# before the two genuine defects were fixed. Do not add to it to make the suite pass. If a new
# phrase belongs here, it needs a sentence saying which of those five kinds it is.
CENSUS_BACKLOG: dict[str, dict[str, str]] = {
    "check_adoption.py": {
        "14 dataset products":
            "quotation — it is `dataset.yaml`'s own comment, reported here, not this "
            "docstring's claim about the corpus",
        "217 off-scale records":
            "dated history — 'shipped non-strict on 2026-08-11 against 217', and the same "
            "sentence says the backlog is now zero, so it cannot read as current",
    },
    "check_capability.py": {
        "472 products":
            "dated in its own sentence — 'measured on 2026-08-08, 79 of 472 products sit at "
            "capability 5'. Read and accepted; the gate does not parse prose to decide that",
        "two different products":
            "shape, not census — it counts the claims in an argument ('two different claims "
            "about two different products'), not records in the corpus",
    },
    "check_instrument.py": {
        "56 products":
            "dated in its own sentence — 'Measured 2026-08-13, 56 products claim exactly that'. "
            "Read and accepted",
        "55 records":
            "the breakdown under that same 2026-08-13 measurement, a sentence later. Read and "
            "accepted",
        "40 records":
            "same 2026-08-13 measurement — '40 records, not 55, are genuinely unbacked' is its "
            "conclusion",
        "`mcp-typescript-sdk`, `openclaw`, `langchain`, `ray`, `firecracker`, `aws-lambda`":
            "the roster under the same 2026-08-13 measurement — the names rather than the "
            "number. Read and accepted",
    },
    "check_parity.py": {
        "Six products":
            "counterfactual — what WOULD have scored wrong under a bug that was fixed, not "
            "what scores wrong now",
    },
    "check_rubric.py": {
        "30 products":
            "hypothetical threshold — 'if a one-line change moves 30 products, that is the "
            "signal to stop'. It counts nothing; it sets a tripwire",
    },
    "preflight.py": {
        "five products":
            "historical incident — the promotion that passed a local loop and failed CI, which "
            "is why this module exists",
    },
    "propose_artifacts.py": {
        "472 products":
            "dated — 'Measured 2026-08-09: 66 of 472 products declared a pypi artifact'. Read "
            "and accepted",
    },
    "prose_worklist.py": {
        "289 notes":
            "dated — 'Measured 2026-09-17, a third of the corpus was not: 879 of 2,289 notes'. "
            "Read and accepted",
    },
    "reverify.py": {
        "25 oldest products":
            "dated — 'Measured 2026-09-12 over the 25 oldest products'. Read and accepted",
    },
    "serialize_registry.py": {
        "Two structural notes":
            "shape, not census — it counts the bullets that follow it in the docstring",
    },
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


def test_there_is_no_dating_exemption(slugs):
    """The absence is the design, so it is asserted rather than left to be re-derived.

    Three mechanisms tried to exempt a dated measurement and all three were defeated - the last
    by a live count smuggled into a legitimately declared sentence. Anything that looks like an
    exemption is now reported like any other phrase, and a human puts it in CENSUS_BACKLOG with a
    reason. If this test starts failing, someone has reintroduced an exemption; read the note
    above CENSUS_BACKLOG before deciding they were right to.
    """
    for text, expected in (
        ("Measured 2026-08-13, 56 products claim exactly that.", ["56 products"]),
        # The case that ended the third mechanism. Asserting truthiness here would pass while
        # "60 products" escaped, which is the whole failure it is meant to catch.
        ("Measured 2026-08-13, 56 products did X and today 60 products do Y.",
         ["56 products", "60 products"]),
        ("Latency was measured 2026-08-13. Today 56 products lack artifacts.", ["56 products"]),
        ("    Measured 2026-08-13, sample output\n\nToday 60 products exist.", ["60 products"]),
    ):
        found = census_phrases(text, slugs)
        for phrase in expected:
            assert phrase in found, (
                f"a dating exemption is back: {phrase!r} was not reported in {text!r} "
                f"(reported: {found})"
            )


def test_every_backlog_entry_says_why_it_is_there(slugs):
    """A phrase with no reason is indistinguishable from one nobody looked at.

    The list before 2026-09-20 was bare, and reading it in context is what showed that most of
    it was never a census — five modules left the list on the strength of a dated-measurement
    rule, and two were real defects that had been sitting in the allowlist rather than fixed.
    """
    missing = [
        f"{name}: {phrase!r}"
        for name, entries in CENSUS_BACKLOG.items()
        for phrase, reason in entries.items()
        if not (reason or "").strip()
    ]
    assert not missing, f"backlog entries with no justification: {sorted(missing)}"


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
