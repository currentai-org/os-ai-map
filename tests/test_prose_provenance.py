"""Classification, packet gathering, and the applier's refusals.

`sweep_status` reported 245 of 472 products as unfinished, which collapsed four materially
different states into one number. Measured 2026-08-15 no product is MISSING a verification
line and every date is in August — what varies is whether the line names something a reader
can reopen. These tests pin the distinction and the applier's refusal to write a packet that
cannot justify itself.
"""

from __future__ import annotations

import pytest
import yaml

from build.apply_provenance import Refused, check, rewrite
from build.prose_provenance import ROOT, census, classify


@pytest.mark.parametrize(
    "comments, expected",
    [
        ("Verified 2026-08-13 via the project README.", "canonical"),
        ("Verified live 2026-08-13 via the project README.", "named_noncanonical"),
        ("Verified live 2026-08-13 on huggingface.co/datasets/x.", "named_noncanonical"),
        ("Verified live 2026-08-13 against the DATASHEET.md.", "named_noncanonical"),
        # The substantive class: names how somebody looked, not what settled it.
        ("Verified live 2026-08-13 via primary sources.", "generic"),
        ("verified live 2026-08-13 via primary sources; v1.2.", "generic"),
        ("Verified live 2026-08-13 via primary-source research.", "generic"),
        ("Some prose with no verification at all.", "missing"),
    ],
)
def test_classification(comments, expected):
    assert classify(comments)[0] == expected


def test_the_corpus_has_no_missing_lines_which_is_the_whole_point():
    """If this ever fails the framing changes: a missing line needs research, where a generic
    one needs evidence matching. They are not interchangeable remedies."""
    assert not census().get("missing"), (
        "a product has no dated verification line; that is a different (and larger) problem "
        "than the noncanonical wording this machinery addresses"
    )


def test_every_state_is_accounted_for():
    by_state = census()
    assert sum(len(v) for v in by_state.values()) == 472
    assert set(by_state) <= {"canonical", "named_noncanonical", "generic", "missing"}


def test_rewrite_replaces_the_clause_and_keeps_the_rest():
    before = "Verified live 2026-08-13 via primary sources; v1.15.0 and 65k stars. MIT-licensed."
    after = rewrite(before, "2026-08-13", "the anything-llm repository page")
    assert after.startswith("Verified 2026-08-13 via the anything-llm repository page;")
    assert "v1.15.0 and 65k stars. MIT-licensed." in after
    assert "primary sources" not in after


def test_rewrite_never_moves_the_date():
    """A provenance repair is not a re-verification. Advancing the date would claim somebody
    re-confirmed the facts today, which nobody did."""
    after = rewrite("Verified live 2026-08-13 via primary sources.", "2026-08-13", "the README")
    assert "2026-08-13" in after


def _packet(**over):
    base = {
        "product": "anythingllm",
        "verification_date": "2026-08-13",
        "selected_document": "the anything-llm repository page",
        "source_url": "https://github.com/Mintplex-Labs/anything-llm",
        "source_accessed": "2026-08-13",
        "support": "The page establishes the app, its providers and its agents.",
        "decision": "derive",
    }
    return {**base, **over}


def test_a_complete_packet_passes():
    check(_packet())


@pytest.mark.parametrize(
    "name, packet",
    [
        # The one way this could launder an invented document: naming a source the product
        # does not actually cite. Checked against the corpus, never trusted from the packet.
        ("url absent from the score file", _packet(source_url="https://example.com/invented")),
        ("accessed on another day", _packet(source_accessed="2026-08-12")),
        ("no support sentence", _packet(support="   ")),
        ("no document named", _packet(selected_document="")),
        ("document is a method", _packet(selected_document="primary sources")),
        ("verification_date not a date", _packet(verification_date="August")),
    ],
)
def test_incomplete_packets_are_refused(name, packet):
    with pytest.raises(Refused):
        check(packet)


def test_refusal_never_falls_back_to_writing_something_else():
    """`Refused` is raised, not swallowed. A packet that cannot justify itself leaves the
    product untouched and goes to the re-read queue."""
    with pytest.raises(Refused):
        check(_packet(source_url="https://example.com/invented"))


@pytest.mark.parametrize(
    "comments",
    [
        # The canonical FORM wrapped around a method. An earlier cut checked the form first
        # and returned `canonical`, which is this module's own subject turned on itself: a
        # check grading on shape while the thing it exists to find sits in the payload.
        "Verified 2026-08-13 via primary sources.",
        "Verified 2026-08-13 via research.",
        "Verified 2026-08-13 via web search.",
        # The live case: removing `live` from this would have promoted it into canonical
        # form. Four hardware records were rewritten that way before this was caught.
        "Verified 2026-08-13 via substitute sources - hailo.ai answers 403 to every request.",
    ],
)
def test_canonical_form_naming_a_method_is_still_generic(comments):
    assert classify(comments)[0] == "generic"


def test_no_canonical_line_in_the_corpus_names_a_method():
    """The invariant the classifier now enforces, asserted against the real corpus.

    Zero today. It stays zero only because `generic` outranks `canonical`; without that a
    rewording pass can manufacture a method-naming line that looks settled.
    """
    import glob
    import os

    offenders = []
    for path in sorted(glob.glob(str(ROOT / "sources" / "products" / "*.yaml"))):
        state, _, trailer = classify((yaml.safe_load(open(path)) or {}).get("comments"))
        if state == "canonical" and trailer:
            from build.prose_provenance import METHOD_WORDS

            if METHOD_WORDS.match(trailer):
                offenders.append(os.path.basename(path)[:-5])
    assert not offenders, f"canonical lines naming a method: {offenders}"
