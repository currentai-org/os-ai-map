"""Classification, packet gathering, and the applier's refusals.

`sweep_status` reported 245 of 472 products as unfinished, which collapsed four materially
different states into one number. Measured 2026-08-15 no product is MISSING a verification
line and every date is in August — what varies is whether the line names something a reader
can reopen. These tests pin the distinction and the applier's refusal to write a packet that
cannot justify itself.
"""

from __future__ import annotations

import re
import pytest
import yaml

from build.apply_provenance import Refused, check, rewrite
from build.prose_provenance import ROOT, census, classify, clause_span


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
    after = rewrite(before, "Verified live 2026-08-13 via primary sources;",
                    "the anything-llm repository page")
    assert after.startswith("Verified 2026-08-13 via the anything-llm repository page;")
    assert "v1.15.0 and 65k stars. MIT-licensed." in after
    assert "primary sources" not in after


def test_rewrite_never_moves_the_date():
    """A provenance repair is not a re-verification. Advancing the date would claim somebody
    re-confirmed the facts today, which nobody did."""
    after = rewrite("Verified live 2026-08-13 via primary sources.",
                    "Verified live 2026-08-13 via primary sources.", "the README")
    assert "2026-08-13" in after


def _packet(**over):
    """A packet against the live corpus, so the digest and date bindings are real."""
    from build.prose_provenance import prose_digest

    product = yaml.safe_load((ROOT / "sources" / "products" / "anythingllm.yaml").read_text())
    base = {
        "product": "anythingllm",
        "current_clause": clause_span(product.get("comments")),
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


@pytest.mark.parametrize(
    "full, clause, expected",
    [
        # A dot inside a URL is not a sentence end. `[^.;]*` stopped inside `huggingface.co`.
        ("Verified live 2026-08-13 on huggingface.co/datasets/allenai/ai2_arc (474 downloads).",
         "Verified live 2026-08-13 on huggingface.co/datasets/allenai/ai2_arc (474 downloads).",
         "Verified 2026-08-13 via the dataset card."),
        # Nor is the dot of an initialism, even though it IS followed by whitespace. Adding
        # only the whitespace test split this into two grammatical-looking halves, which is
        # worse than the URL case because nothing looks wrong.
        ("Verified live 2026-08-13 via the U.S. AI Safety Institute report. Next sentence.",
         "Verified live 2026-08-13 via the U.S. AI Safety Institute report.",
         "Verified 2026-08-13 via the dataset card. Next sentence."),
        ("Verified live 2026-08-13 against the repository DATASHEET.md and arXiv:2406.19314.",
         "Verified live 2026-08-13 against the repository DATASHEET.md and arXiv:2406.19314.",
         "Verified 2026-08-13 via the dataset card."),
        # `;` terminates, and the prose after it survives.
        ("Verified live 2026-08-13 via primary sources; v1.15.0 and 65k stars. MIT-licensed.",
         "Verified live 2026-08-13 via primary sources;",
         "Verified 2026-08-13 via the dataset card; v1.15.0 and 65k stars. MIT-licensed."),
    ],
)
def test_rewrite_replaces_the_exact_reviewed_clause(full, clause, expected):
    assert rewrite(full, clause, "the dataset card") == expected


def test_rewrite_refuses_a_clause_that_is_not_present_exactly_once():
    """The applier no longer re-derives a boundary, so its remaining risk is a stale packet.
    A clause that is absent — or ambiguous — must refuse rather than guess."""
    from build.apply_provenance import Refused

    with pytest.raises(Refused):
        rewrite("Verified 2026-08-13 via the README.", "a clause that is not there", "x")
    with pytest.raises(Refused):
        rewrite("A. A.", "A.", "x")   # two occurrences


def test_the_clause_boundary_has_one_owner():
    """BOUND is interpolated into both patterns rather than restated. The first cut of this
    fix wrote the expansion into CLAUSE_ANY as a literal, so BOUND advertised a new boundary
    while the pattern kept the old one — the sibling-copy defect, inside its own fix."""
    from build.apply_provenance import CLAUSE
    from build.prose_provenance import BOUND, CLAUSE_ANY

    assert BOUND in CLAUSE.pattern
    assert BOUND in CLAUSE_ANY.pattern


def test_every_corpus_clause_round_trips_without_an_orphan():
    """All 472, not a sample. The earlier version checked the first 60 files for one
    signature (`the document.\w`), which is the URL case only — it would have passed the
    initialism case, whose fragment starts with a space and a capital."""
    import glob

    checked = 0
    for path in sorted(glob.glob(str(ROOT / "sources" / "products" / "*.yaml"))):
        product = yaml.safe_load(open(path)) or {}
        comments = " ".join(str(product.get("comments") or "").split())
        clause = clause_span(comments)
        if not clause:
            continue
        checked += 1
        out = rewrite(comments, clause, "THE-DOCUMENT")
        after = out.split("THE-DOCUMENT", 1)[1]
        # Whatever follows the inserted name must start a new sentence or clause, never a
        # fragment of the one just replaced.
        assert re.match(r"^[.;]?(\s|$)", after), f"{path}: orphaned fragment {after[:60]!r}"
    assert checked > 400, f"only {checked} products carried a clause; the walk has narrowed"
