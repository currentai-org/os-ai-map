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
                    "the anything-llm repository page", "2026-08-13")
    assert after.startswith("Verified 2026-08-13 via the anything-llm repository page;")
    assert "v1.15.0 and 65k stars. MIT-licensed." in after
    assert "primary sources" not in after


def test_rewrite_never_moves_the_date():
    """A provenance repair is not a re-verification. Advancing the date would claim somebody
    re-confirmed the facts today, which nobody did."""
    after = rewrite("Verified live 2026-08-13 via primary sources.",
                    "Verified live 2026-08-13 via primary sources.", "the README", "2026-08-13")
    assert "2026-08-13" in after


def test_rewrite_writes_the_validated_date_not_one_scraped_from_the_clause():
    """The written date comes from `verification_date`, which every upstream check is about.

    Deriving it here instead meant the date written into the corpus came from whatever string
    the packet nominated as its clause, while the validation ran against a different field.
    """
    with pytest.raises(Refused):
        rewrite("Verified live 2026-08-13 via primary sources.",
                "Verified live 2026-08-13 via primary sources.", "the README", "2026-08-14")
    with pytest.raises(Refused):
        rewrite("Verified live 2026-08-13 via primary sources.",
                "Verified live 2026-08-13 via primary sources.", "the README", "2026-99-99")


def test_rewrite_refuses_a_clause_that_is_not_a_verification_line():
    """A packet may decide where the clause ENDS. It may not decide which claim is rewritten."""
    with pytest.raises(Refused):
        rewrite("Verified 2026-08-13 via primary sources. Released 2026-08-13 under MIT.",
                "Released 2026-08-13 under MIT.", "the README", "2026-08-13")


def _packet(**over):
    """A packet against the live corpus, so the digest and date bindings are real."""
    from build.prose_provenance import prose_digest

    product = yaml.safe_load((ROOT / "sources" / "products" / "anythingllm.yaml").read_text())
    base = {
        "product": "anythingllm",
        "current_state": "generic",
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
        # The clause decides a boundary, never which claim is rewritten. Without these, a
        # packet could nominate another unique dated sentence: the rewrite would land there,
        # the real verification line would survive, and a "canonical line exists" postcondition
        # would still pass.
        ("clause is not in the live prose", _packet(current_clause="Verified 2026-08-13 via X.")),
        # Present in the live prose, unique, and not the claim under repair.
        ("clause is not a verification line",
         _packet(current_clause="MIT-licensed all-in-one local-first Desktop + Docker AI app")),
        ("clause is dated differently from the packet",
         _packet(current_clause="Verified live 2026-08-13 via primary sources;",
                 verification_date="2026-08-12", source_accessed="2026-08-12")),
        ("clause carries no state", _packet(current_state="")),
        ("reviewed under a different state", _packet(current_state="named_noncanonical")),
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
    assert rewrite(full, clause, "the dataset card", "2026-08-13") == expected


def test_rewrite_refuses_a_clause_that_is_not_present_exactly_once():
    """The applier no longer re-derives a boundary, so its remaining risk is a stale packet.
    A clause that is absent — or ambiguous — must refuse rather than guess."""
    from build.apply_provenance import Refused

    with pytest.raises(Refused):
        rewrite("Verified 2026-08-13 via the README.", "a clause that is not there", "x",
                "2026-08-13")
    with pytest.raises(Refused):
        rewrite("Verified 2026-08-13. Verified 2026-08-13.", "Verified 2026-08-13.", "x",
                "2026-08-13")   # two occurrences


def test_the_applier_holds_no_clause_pattern():
    """The boundary has one owner because the applier no longer needs one.

    It used to carry a sibling copy and re-match the clause at write time, which is what made
    every boundary bug a silent corruption. `BOUND` is a heuristic that proposes a clause for
    review; nothing downstream of the review re-derives it.
    """
    import ast
    import inspect

    from build import apply_provenance
    from build.prose_provenance import BOUND, CLAUSE_ANY

    assert BOUND in CLAUSE_ANY.pattern

    # AST, not a text search: the module's own docstring quotes the regex fragments it no
    # longer uses, and a grep-shaped test would either fail on the prose or be weakened until
    # it matched nothing that mattered.
    tree = ast.parse(inspect.getsource(apply_provenance))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert "re" not in imports, "the applier imports `re`; it has no boundary to derive"
    assert "re" not in {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }


def test_every_dated_product_emits_a_literally_replaceable_clause():
    """Every product the census calls dated, not a sample and not a threshold.

    The denominator is the census's own non-missing count, so a clause_span that quietly
    stopped matching some wording would fail here instead of shrinking the walk. An earlier
    version checked the first 60 files for one signature (`the document.\\w`) — the URL case
    only — and would have passed the initialism case, whose fragment starts with a capital.

    What this establishes is narrow and worth stating: every dated line yields a clause that
    can be substituted literally without orphaning a fragment. It cannot establish that the
    heuristic chose the semantically right boundary. Review does that, in the packet.
    """
    import glob

    checked = 0
    for path in sorted(glob.glob(str(ROOT / "sources" / "products" / "*.yaml"))):
        product = yaml.safe_load(open(path)) or {}
        comments = " ".join(str(product.get("comments") or "").split())
        state, date, _ = classify(comments)
        if state == "missing":
            continue
        clause = clause_span(comments)
        assert clause, f"{path}: dated but no replaceable clause"
        checked += 1
        out = rewrite(comments, clause, "THE-DOCUMENT", date)
        after = out.split("THE-DOCUMENT", 1)[1]
        # Whatever follows the inserted name must start a new sentence or clause, never a
        # fragment of the one just replaced.
        assert re.match(r"^[.;]?(\s|$)", after), f"{path}: orphaned fragment {after[:60]!r}"

    by_state = census()
    expected = sum(len(v) for state, v in by_state.items() if state != "missing")
    assert checked == expected, f"walked {checked} of {expected} dated products"


def test_packets_cover_every_unresolved_state():
    """All three, not just `generic`.

    The pipeline was specified as one uniform review over 201 records, but emitted packets for
    only the 172 `generic` ones — so the 16 `ambiguous_noncanonical` and 13
    `named_noncanonical` had no route through it at all. A second, weaker path for the named
    ones would let the prose vouch for itself, which is the shortcut this exercise corrects.
    """
    from build.prose_provenance import UNRESOLVED, packets

    by_state = census()
    rows = packets()
    assert len(rows) == sum(len(by_state.get(s, [])) for s in UNRESOLVED)
    assert {r["current_state"] for r in rows} == set(UNRESOLVED)
    for row in rows:
        assert row["current_clause"], f"{row['product']}: no clause to review"
        assert row["decision"] is None, "a packet decides nothing on its own"


def test_packets_can_be_scoped_to_one_category():
    """Review happens a category at a time, so the manifest has to be scopeable to a roster."""
    from build.prose_provenance import category_roster, packets

    roster = category_roster("ui_api")
    rows = packets(roster)
    assert rows and {r["product"] for r in rows} <= roster
    assert {r["product"] for r in rows} == {r["product"] for r in packets()} & roster


@pytest.mark.parametrize("state", ["ambiguous_noncanonical", "named_noncanonical"])
def test_an_unresolved_packet_of_any_state_applies(tmp_path, monkeypatch, state):
    """`apply_one` end to end, on a synthetic corpus.

    Nothing exercised `apply_one` until now — `check` and `rewrite` were each tested alone,
    and the function that joins them referenced an undefined name, so every real application
    would have raised `NameError` after passing all its checks. The gap is the same shape as
    everything else this PR fixes: the parts were verified, the composition was not.
    """
    import build.apply_provenance as ap
    import build.prose_provenance as pp

    line = {
        "ambiguous_noncanonical": "Verified 2026-08-13.",
        "named_noncanonical": "Verified live 2026-08-13 via the SPEC.md.",
    }[state]
    products = tmp_path / "sources" / "products"
    scores = tmp_path / "sources" / "scores"
    products.mkdir(parents=True)
    scores.mkdir(parents=True)
    (products / "widget.yaml").write_text(
        yaml.safe_dump({"name": "widget", "description": "A widget.", "comments": line})
    )
    (scores / "widget.yaml").write_text(yaml.safe_dump({
        "openness": {"sources": [{"url": "https://example.com/spec", "accessed": "2026-08-13",
                                  "shows": "what the widget is"}]},
    }))
    monkeypatch.setattr(ap, "ROOT", tmp_path)
    monkeypatch.setattr(pp, "ROOT", tmp_path)

    product = yaml.safe_load((products / "widget.yaml").read_text())
    packet = {
        "product": "widget",
        "current_state": state,
        "current_clause": clause_span(product["comments"]),
        "verification_date": "2026-08-13",
        "selected_document": "the widget specification",
        "source_url": "https://example.com/spec",
        "source_accessed": "2026-08-13",
        "support": "The spec describes the widget.",
        "prose_digest": pp.prose_digest(product),
        "decision": "derive",
    }
    assert ap.apply_one(packet) is True

    after = yaml.safe_load((products / "widget.yaml").read_text())["comments"]
    assert classify(after)[0] == "canonical"
    assert classify(after)[1] == "2026-08-13"
    assert "the widget specification" in after


def test_apply_refuses_a_packet_that_would_leave_two_dated_lines(tmp_path, monkeypatch):
    """The postcondition is about the result, not about a canonical line existing somewhere.

    A clause nominated away from the real verification line would write a second, canonical
    line and leave the original standing — and the old `CANONICAL.search` postcondition would
    have found the new one and called that a success.
    """
    import build.apply_provenance as ap
    import build.prose_provenance as pp

    products = tmp_path / "sources" / "products"
    scores = tmp_path / "sources" / "scores"
    products.mkdir(parents=True)
    scores.mkdir(parents=True)
    (products / "widget.yaml").write_text(yaml.safe_dump({
        "name": "widget", "description": "A widget.",
        "comments": "Verified 2026-08-13 via primary sources. Shipped 2026-08-13 under MIT.",
    }))
    (scores / "widget.yaml").write_text(yaml.safe_dump({
        "openness": {"sources": [{"url": "https://example.com/spec", "accessed": "2026-08-13"}]},
    }))
    monkeypatch.setattr(ap, "ROOT", tmp_path)
    monkeypatch.setattr(pp, "ROOT", tmp_path)

    product = yaml.safe_load((products / "widget.yaml").read_text())
    packet = {
        "product": "widget",
        "current_state": "generic",
        "current_clause": "Shipped 2026-08-13 under MIT.",
        "verification_date": "2026-08-13",
        "selected_document": "the widget specification",
        "source_url": "https://example.com/spec",
        "source_accessed": "2026-08-13",
        "support": "The spec describes the widget.",
        "prose_digest": pp.prose_digest(product),
        "decision": "derive",
    }
    with pytest.raises(Refused):
        ap.apply_one(packet)
    assert "primary sources" in (products / "widget.yaml").read_text()
