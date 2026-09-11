"""Tests for the arXiv citation gate.

The two that carry the design are `test_a_quoted_locator_is_not_a_body_claim` and
`test_a_number_over_abs_is_reported_not_failed`. The first is the distinction the gate rests on:
a table or figure named inside a quotation is part of what the abstract page says, and the
submission history is exactly what an `/abs` citation is good for. The second is the ratchet —
most numeric `/abs` citations quote the abstract and are correct, so telling them apart needs a
reader, and a gate that failed on the backlog would be switched off.
"""

from build.check_citations import candidates, check

ABS = "https://arxiv.org/abs/2406.17557"
PDF = "https://arxiv.org/pdf/2406.17557"


def rows(*entries):
    return [("prod", "capability", url, shows) for url, shows in entries]


def test_an_abs_cited_for_the_paper_body_fails():
    problems = check(rows((ABS, "Abstract. The per-corpus ablation table is in the paper body, not on this page")))
    assert len(problems) == 1
    assert "arxiv.org/pdf" in problems[0]


def test_a_table_locator_over_abs_fails():
    assert len(check(rows((ABS, "Table 2 gives the token counts per corpus")))) == 1


def test_the_same_claim_over_pdf_passes():
    assert check(rows((PDF, "Table 2 gives the token counts per corpus"))) == []


def test_a_quoted_locator_is_not_a_body_claim():
    """An abstract page's submission history can quote an author naming a figure."""
    shows = ('The paper was withdrawn by its authors. Submission history: "[v2] Wed, 3 Sep 2025 '
             '(withdrawn)", with the comment "I want to revisit some of the experiments in this '
             'paper, specifically figure 5."')
    assert check(rows((ABS, shows))) == []


def test_an_abstract_quote_passes():
    assert check(rows((ABS, 'the abstract still reads "817 questions that span 38 categories"'))) == []


def test_a_number_over_abs_is_reported_not_failed():
    entries = rows((ABS, 'the abstract still reads "817 questions that span 38 categories"'))
    assert check(entries) == []
    assert len(candidates(entries)) == 1


def test_a_non_arxiv_source_is_out_of_scope():
    entries = rows(("https://example.com/paper", "Table 2 gives the token counts"))
    assert check(entries) == []
    assert candidates(entries) == []


def test_the_corpus_passes():
    assert check() == []
