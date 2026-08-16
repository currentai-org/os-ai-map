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
        ("Verified 2026-08-13 via the primary sources.", "generic"),
        ("Verified 2026-08-13 via substitute sources - hailo.ai 403s.", "generic"),
        # Dated, not a method, and naming nothing. Defaulting these to `named_noncanonical`
        # promised a mechanical fix that does not exist. meta-ai and le-chat are the corpus
        # cases; 16 products are in this state.
        ("Verified 2026-08-13.", "ambiguous_noncanonical"),
        ("Verified 2026-08-13 via .", "ambiguous_noncanonical"),
        ("Verified live 2026-08-13, but only the adoption axis could be re-derived.",
         "ambiguous_noncanonical"),
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
    assert set(by_state) <= {"canonical", "named_noncanonical", "ambiguous_noncanonical",
                             "generic", "missing"}


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
    """A packet against the live corpus, so the digest and date bindings are real."""
    from build.prose_provenance import prose_digest

    product = yaml.safe_load((ROOT / "sources" / "products" / "anythingllm.yaml").read_text())
    base = {
        "product": "anythingllm",
        "verification_date": "2026-08-13",
        "selected_document": "the anything-llm repository page",
        "source_url": "https://github.com/Mintplex-Labs/anything-llm",
        "source_accessed": "2026-08-13",
        "support": "The page establishes the app, its providers and its agents.",
        "prose_digest": prose_digest(product),
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
        # The applier kept a narrower sibling regex than the classifier until 2026-08-15, so
        # this exact phrase — the one behind the four hardware records — passed.
        ("document is substitute sources", _packet(selected_document="substitute sources")),
        ("document is 'the primary sources'", _packet(selected_document="the primary sources")),
        ("document names nothing", _packet(selected_document=" . ")),
        ("verification_date not a date", _packet(verification_date="August")),
        # Shape-matching accepted these. Same defect as check_payload's hold date, reintroduced.
        ("impossible date 2026-99-99",
         _packet(verification_date="2026-99-99", source_accessed="2026-99-99")),
        ("impossible date 2026-02-30",
         _packet(verification_date="2026-02-30", source_accessed="2026-02-30")),
        # Without a prose binding a decision survives every later edit to the prose it was
        # taken against, and a drifted date would silently ADVANCE the live one.
        ("prose changed since review", _packet(prose_digest="0" * 64)),
        ("no prose_digest at all", _packet(prose_digest="")),
        ("packet date disagrees with the live line",
         _packet(verification_date="2026-08-12", source_accessed="2026-08-12")),
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


def test_the_digest_ignores_the_clause_it_is_about_to_rewrite():
    """Otherwise every packet invalidates itself the moment it applies."""
    from build.prose_provenance import prose_digest

    product = yaml.safe_load((ROOT / "sources" / "products" / "anythingllm.yaml").read_text())
    rewritten = {**product,
                 "comments": product["comments"].replace("Verified live 2026-08-13",
                                                         "Verified 2026-08-13")}
    assert prose_digest(product) == prose_digest(rewritten)


def test_the_digest_catches_an_edit_to_either_prose_field():
    """product-copy.md defines the line as provenance for description AND comments."""
    from build.prose_provenance import prose_digest

    product = yaml.safe_load((ROOT / "sources" / "products" / "anythingllm.yaml").read_text())
    assert prose_digest(product) != prose_digest({**product,
                                                  "description": product["description"] + " Extra."})
    assert prose_digest(product) != prose_digest({**product,
                                                  "comments": product["comments"] + " Extra."})
