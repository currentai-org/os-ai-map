"""`docs/reference/` and `docs/architecture/` say what is true, not how it became true.

## Why this is a test rather than prose

The rule already existed, for one field. `docs/reference/product-copy.md` tells a curator
"**No dates, no chronology.** A note states what is true until the score changes … 'Corrected
from level 4', 'the note this replaces', 'settled under issue 264', 'an earlier draft was
withdrawn' are all history, and they leave." `tests/test_score_notes.py` holds it over
`sources/scores/*.yaml`, and the corpus is clean.

The guides that state the rule were exempt from it. They had accumulated the same thing one
layer up: which issue changed what, what an earlier draft claimed, what a correction left
standing. It is the identical defect with a different reader — a guide narrating its own
revision history rather than stating the rule, so a reader has to work out which sentence is
current before they can use any of it.

The fix is the same fix. The chronology leaves, the finding a correction was carrying stays,
stated as a rule rather than as an incident, and a gate keeps it out.

## What it does and does not claim

It does NOT decide whether a sentence is history. Reading that off prose is a judgement, and
this gate makes no judgements — `tests/test_build_docstrings.py` records what three attempts at
one cost. It reports every phrase that matches a narration marker and every issue reference,
and `CHRONOLOGY_BACKLOG` carries the ones a human has read and accepted, each with the reason.

The markers are narrow and literal on purpose. `docs/architecture/adr-005-closed-product-inclusion.md`
is the calibration: it was written to this register by hand, it carries dates, counts, a quoted
ruling and a rejected-designs section, and it matches nothing here. A marker that fires on
ADR-005 is a marker describing something other than chronology.

Dates are deliberately NOT a marker, which is where this differs from the score-note rule one
directory over. A note argues a rung and has no business carrying a date; a reference document
legitimately dates a decision, a measurement and a policy expiry. "Accepted 2026-09-20" and
"Measured 2026-09-20: of the 23 categories …" are exactly what this register asks for.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DOC_ROOTS = ("docs/reference", "docs/architecture")


def documents() -> list[Path]:
    return sorted(p for root in DOC_ROOTS for p in (REPO / root).glob("*.md"))


# ── The markers ─────────────────────────────────────────────────────────────────────────────
#
# Each one names a way a document talks about its own past instead of its subject. They are
# phrases rather than concepts: a concept ("is this sentence historical?") cannot be detected,
# and the three defeated attempts to detect one are written up above CENSUS_BACKLOG in
# tests/test_build_docstrings.py. Every marker below fires on a form of words, and the
# judgement about whether that form of words is doing something legitimate is a human's, made
# once, in the backlog.
#
# The captured span is what the backlog keys on, so each pattern captures a little more than
# the bare trigger where that is what makes an entry readable.
MARKERS: dict[str, str] = {
    # "An earlier draft of this section claimed the opposite"
    "earlier-draft": r"\b(?:an?|the) (?:earlier|previous|first) (?:draft|version)\b",
    # "the corpus also answered that question 54 times under `self-host`" → fine.
    # "`self-host` used to be an undeclared key" → not fine.
    "used-to": r"\bused to \w+",
    "formerly": r"\b(?:formerly|previously|originally|at the time)\b",
    "the-old": r"\bthe old\b",
    "now-says": r"\b(?:we now|now says|now reads|has since|since then)\b",
    "no-longer": r"\bno longer\b",
    "correction": (
        r"\ba correction\b|\bwas corrected\b|\bcorrected (?:from|to)\b"
        r"|\bgot (?:it|this|that) wrong\b"
        r"|\bthis (?:guide|document|section|page) (?:used|once|claimed|said)\b"
    ),
    "withdrawn": r"\bwithdrawn\b|\bsupersed(?:e|es|ed|ing)\b|\bthis replaces\b",
    "renamed-from": r"\brenamed from\b|\bwas renamed\b",
    # A window that is only ever about when something changed.
    "until-date": r"\b(?:until|before|after|since) 20\d\d-\d\d-\d\d\b",
    # An issue number is not narration on its own — it is either a pointer to work that is
    # still open, which is a fact about now, or a citation of the change that produced the
    # sentence, which is a changelog. The two are told apart by reading, one at a time, and
    # the reading is recorded in the backlog. The negative lookahead keeps a six-digit hex
    # colour (`#272726`) out of it.
    "issue-ref": r"#\d{2,4}(?![\w])",
}
_COMPILED = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in MARKERS.items()}


def chronology_phrases(doc: str) -> set[str]:
    """Every phrase in `doc` matching a narration marker, whitespace-normalized.

    Normalized and folded to lower case because these documents are hand-wrapped and a phrase
    reads differently at the start of a sentence: the same phrase re-wrapped or re-capitalized
    is the same phrase, and the backlog has to survive a reflow.

    Every match is returned, in prose or in a fenced block. A schema field spelled
    `supersedes_observation_id` is a legitimate match with a one-line reason, and carving out
    code fences would be an exemption rather than a reading — the same trade the census gate
    settled one directory over.
    """
    return {
        " ".join(m.group(0).split()).lower()
        for rx in _COMPILED.values()
        for m in rx.finditer(doc)
    }


# ── The backlog ─────────────────────────────────────────────────────────────────────────────
#
# What the detector still reports and why each one stays, keyed by the document's path relative
# to the repository root. An entry covers every occurrence of that phrase in that file, because
# one reason genuinely covers them all — fifteen references to the same open issue are one
# judgement, not fifteen.
#
# The reason is required. A bare list stops being a backlog and becomes a place for a real
# changelog to hide. Do not add to this to make the suite pass: the phrases below fall into
# five kinds, and an entry that is none of them is a document to edit rather than a line to add.
#
#   quotation        the document is quoting something else — a banned phrase it is defining,
#                    a golden's "before" text, an external commit message
#   open work        a pointer to work that has not happened, which is a fact about now
#   ADR mechanics    an ADR's own Status / Supersedes header, or its Consequences section
#                    saying what the decision changes, which is what an ADR is for
#   vocabulary       a field, enum value or recorded value that happens to spell a marker
#   plain English    the marker's words used about the subject rather than about the document
CHRONOLOGY_BACKLOG: dict[str, dict[str, str]] = {
    "docs/reference/capability.md": {
        "superseded":
            "vocabulary — `superseded` is one of the two values `basis_detail` may name for a "
            "`training_value` band, quoted from the rubric",
    },
    "docs/reference/openness.md": {
        "withdrawn":
            "plain English — a withdrawn PART, the `discontinued` reading of `retail`. It is "
            "about the product being unbuyable, not about this document changing",
    },
    "docs/reference/product-copy.md": {
        "an earlier draft":
            "quotation — twice: once in the list of banned phrases the no-chronology rule "
            "defines itself by, and once inside a golden's `Before` text, which is corpus "
            "prose being shown as an example of the defect",
        "corrected from":
            "quotation — `\"Corrected from level 4\"` is one of the four banned phrases that "
            "rule enumerates",
        "this replaces":
            "quotation — `\"the note this replaces\"`, from the same enumeration",
        "withdrawn":
            "quotation — `\"an earlier draft was withdrawn\"` in the enumeration, and the same "
            "shape inside the `tensorlake-sandbox` golden's `Before`",
        "used to state":
            "quotation — the `raspberry-pi-5` golden's `Before` text, which is the corpus prose "
            "the golden exists to condemn",
        "used to produce":
            "plain English — inside the `qwen3-embedding` golden's `After`, meaning the "
            "pipeline employed to produce the checkpoints",
        "has since":
            "plain English — inside the `openhands` golden, about a leaderboard entry being "
            "displaced. A fact about the benchmark, not about this document",
        "now reads":
            "quotation — the `raspberry-pi-5` golden's `Before` text, shown as the vocabulary "
            "drift the golden exists to condemn",
        "now says":
            "quotation — the same `Before` text, same reason",
        "#1190":
            "quotation — `\"AgentOps OSS release (#1190)\"` is a commit message in somebody "
            "else's repository, quoted as the evidence a golden's `shows` line cites",
    },
    "docs/architecture/adr-002-registry-curated-catalog-discovered.md": {
        "superseded":
            "ADR mechanics — the Status line and the banner recording that ADR-003 replaced "
            "this ADR's scope basis. An ADR that cannot say it was superseded is unreadable",
        "supersedes":
            "ADR mechanics — the same banner, naming what ADR-003 supersedes",
    },
    "docs/architecture/adr-003-repository-scope-boundary.md": {
        "supersedes":
            "ADR mechanics — the `**Supersedes:**` header, which is part of the ADR format",
        "superseded":
            "ADR mechanics — the Consequences section saying which parts of ADR-002 this "
            "decision replaces, which is what a Consequences section is for",
        "#384":
            "open work — the openness chain the repo will retire. A pointer to work that has "
            "not happened",
        "#404":
            "open work — the planning issue the ADR's own execution sequence is keyed to, and "
            "the only place the role taxonomy's derivation is recorded",
    },
    "docs/architecture/adr-004-machine-proposals-and-the-public-tail.md": {
        "supersedes":
            "ADR mechanics — the `**Supersedes:**` header naming the two autopilot rulings "
            "this decision replaces",
        "no longer":
            "ADR mechanics — the Consequences section stating what the decision changes for a "
            "registry-only batch",
    },
    "docs/architecture/data-architecture.md": {
        "#355":
            "open work — the row-to-run binding the platform does not expose. Two fields are "
            "constants until it lands, and the document says so wherever they appear",
        "#384":
            "open work — the Phase-7 retirement the repo drives but does not own",
        "#412":
            "open work — Phase 8, which lands release manifests and ends the split this "
            "section describes",
        "superseded":
            "vocabulary — one of the four values of a manifest's `status` enum",
        "superseding":
            "plain English — AD-4's rule that a correction is recorded as a superseding "
            "OBSERVATION rather than by mutating history. It is about the data model",
    },
}


@pytest.fixture(scope="module")
def live() -> dict[str, set[str]]:
    return {
        str(path.relative_to(REPO)): chronology_phrases(path.read_text(encoding="utf-8"))
        for path in documents()
    }


def test_no_reference_document_narrates_its_own_history(live):
    """A guide states the rule. It does not record which issue produced the rule.

    The two kinds a hit can be are settled by reading it, not by the gate: a phrase carrying a
    real finding is rewritten so the finding survives as a rule, and a phrase carrying only
    chronology leaves. Neither outcome is "add it to the backlog" unless it is one of the five
    kinds listed above it.
    """
    offenders = [
        f"{name}: {phrase!r}"
        for name, phrases in sorted(live.items())
        for phrase in sorted(phrases)
        if phrase not in CHRONOLOGY_BACKLOG.get(name, {})
    ]
    assert not offenders, (
        f"{len(offenders)} phrase(s) under {' and '.join(DOC_ROOTS)} narrate the document's own "
        "history:\n  " + "\n  ".join(offenders)
        + "\n\nState what is true. Where the sentence carries a finding, keep the finding and "
        "drop the chronology; git carries the rest. If the phrase is a quotation, a pointer to "
        "open work, an ADR's own status header, a field name, or the marker's words used about "
        "the subject, add it to CHRONOLOGY_BACKLOG with that justification."
    )


def test_every_backlog_entry_says_why_it_is_there():
    """A phrase with no reason is indistinguishable from one nobody looked at."""
    missing = [
        f"{name}: {phrase!r}"
        for name, entries in CHRONOLOGY_BACKLOG.items()
        for phrase, reason in entries.items()
        if not (reason or "").strip()
    ]
    assert not missing, f"backlog entries with no justification: {sorted(missing)}"


def test_the_backlog_has_not_gone_stale(live):
    """A phrase that has been rewritten must leave the backlog, not linger in it.

    Otherwise the list stops describing the exceptions and starts hiding them: it would keep
    passing long after the sentences were gone, and the next real changelog would have
    somewhere to sit unnoticed. Same two-sided shape as the allowlists in
    `tests/test_score_notes.py` and `tests/test_build_docstrings.py`, and the same reason.
    """
    stale = [
        f"{name}: {phrase!r}"
        for name, entries in CHRONOLOGY_BACKLOG.items()
        for phrase in entries
        if phrase not in live.get(name, set())
    ]
    assert not stale, (
        f"{sorted(stale)} no longer appear in their document — remove them from "
        "CHRONOLOGY_BACKLOG so the list keeps meaning what it says."
    )


def test_the_backlog_names_only_documents_that_exist(live):
    """A path that no longer resolves takes its reasons out of reach of the two tests above."""
    unknown = sorted(set(CHRONOLOGY_BACKLOG) - set(live))
    assert not unknown, f"CHRONOLOGY_BACKLOG names documents that do not exist: {unknown}"


def test_the_markers_leave_a_hand_written_adr_alone():
    """ADR-005 is the calibration, and it is asserted rather than left to be re-derived.

    It was written to this register by hand, before any of these markers existed, and it
    carries everything the register permits: a decision date, a quoted ruling, a dated survey
    with counts, and a section on two designs that were rejected. If a marker starts firing on
    it, the marker has stopped describing chronology and started describing an ADR, and the
    marker is what is wrong.
    """
    adr = REPO / "docs/architecture/adr-005-closed-product-inclusion.md"
    found = chronology_phrases(adr.read_text(encoding="utf-8"))
    assert not found, (
        f"the markers fire on ADR-005, which is clean by hand: {sorted(found)}. Read the "
        "document before changing it — the rule being applied is not the one already applied "
        "there."
    )
