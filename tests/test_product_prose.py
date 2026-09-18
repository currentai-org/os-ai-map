"""`description` is neutral metadata, not marketing copy.

The third-party review of 2026-08-11 made the case on `fastmcp`, whose description read "the
fastest way to create a production MCP server", "growing rapidly" and "becoming the de facto
framework". None of the three is checkable, and a registry that funders and contributors read
as a factual index should not carry a vendor's own adjectives in the field that identifies what
a product IS. Evaluative claims belong in evidence-backed observations, where a source can be
attached to them.

Thirty-six products carried such language and were rewritten on 2026-08-12. Where the
superlative already had its evidence sitting beside it, the fix was to lead with the evidence
and drop the adjective — `osworld` went from "the leading harness for computer-use agents
(Claude Computer Use, OpenAI Operator both publish OSWorld scores)" to "Picked because Claude
Computer Use and OpenAI Operator both publish OSWorld scores". The claim survives, and it is
now the kind a reader can check.

WHAT THIS DOES NOT BAN, and why the list below is phrases rather than words.

A ranking with a number attached and a stated basis is a fact, not a boast. `nextchat` says
"~88k GitHub stars makes it the single most-starred OSS chat UI repo by raw count" and
`opik` says "the second most-starred open source LLM observability tool after Langfuse".
Both name the measure, so both stay. Banning the word "most" would have deleted them.

The pattern also cannot be a bare word list because a product NAME may contain one: the first
scan flagged `amazon-nova` for "premier", which appears in the sentence "No 'Nova 2 Premier'
exists as of May 2026". That is the failure mode this docstring exists to warn the next
person about — read the match in context before fixing it.
"""

import re
from pathlib import Path

import pytest
import yaml

from build.product_prose import census, dated_verification

ROOT = Path(__file__).resolve().parents[1]

# Phrases that assert a superlative or a growth rate without a measure. Ordered roughly by how
# often they appeared. `dominant ` keeps its trailing space so it does not fire on "dominantly"
# or on a description of market structure that names its evidence.
MARKETING = re.compile(
    r"\b("
    r"the fastest|fastest way|fastest.growing"
    r"|de facto|de-facto"
    r"|growing rapidly|rapidly growing"
    # `world.class` carries a trailing \b that its neighbours must not: without it the
    # alternative matches inside "Dynamic World classes", Google's land-cover product and
    # a legitimate input modality for remote-sensing models (`presto`). A blanket trailing
    # \b would break `game.chang`, which has to keep matching "game-changing".
    r"|industry.standard|best.in.class|world.class\b|gold standard"
    r"|the leading|most popular|most ubiquitous|most widely cited"
    r"|cutting.edge|state.of.the.art"
    r"|seamless|effortless|revolutionary|game.chang|unmatched"
    r"|blazing|lightning.fast|the go.to|punches well above"
    r"|dominant "
    r")",
    re.I,
)


def _descriptions():
    for path in sorted((ROOT / "sources" / "products").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        yield path.stem, doc.get("description") or ""


def test_descriptions_carry_no_unverifiable_marketing_claims():
    offences = []
    for slug, description in _descriptions():
        for match in MARKETING.finditer(description):
            start = max(0, match.start() - 50)
            end = min(len(description), match.end() + 50)
            offences.append(f"{slug}: ...{description[start:end]}...")

    assert not offences, (
        "product descriptions must be neutral metadata; move an evaluative claim into an "
        "evidence-backed observation, or lead with the evidence it already cites:\n"
        + "\n".join(offences)
    )


def test_every_product_has_a_substantive_description():
    """A guard on the guard: the check above passes trivially on an empty field.

    Cheap, and it is the shape of failure this repo keeps finding — an instrument reporting
    success while inspecting nothing. `check_recipe` uses the same 40-character floor on a
    deferral reason for the same reason.
    """
    thin = [slug for slug, description in _descriptions() if len(description.strip()) < 40]
    assert not thin, f"products with a missing or too-thin description: {thin}"


def test_the_scan_actually_walks_the_corpus():
    """A non-zero count guard, because a corpus walk that silently narrows passes green.

    Two walks did exactly that earlier in this repo's history, one of them while inspecting
    nothing at all.
    """
    slugs = [slug for slug, _ in _descriptions()]
    assert len(slugs) > 400, f"only walked {len(slugs)} products; the glob has drifted"


# --- no dated verification sentence in comments -----------------------------------------
#
# Every `comments` field used to end in `Verified <date> via <document>.` The date is
# `last_verified` on each axis and the page prints it as `Verified <date>`; the line was a third
# copy, and the one visitors read as a footnote about the product. #619 retired it. What follows
# keeps it out: a new product, or an edit to an existing one, can write it again in any of the
# spellings the corpus has carried, and `build/product_prose.py` finds them all.


@pytest.mark.parametrize(
    "comments",
    [
        "Verified 2026-08-13 via the project README.",
        "Verified live 2026-08-13 via the project README.",
        "Verified live 2026-08-13 on huggingface.co/datasets/x.",
        "verified 2026-08-13 against the DATASHEET.md",
        "Verified 2026-08-13.",
        "Verified 2026-08-13 via primary sources.",
        "Verification status: 2026-08-13.",
        # Prose before the line does not hide it.
        "Runs on-device. Verified 2026-08-13 via the model card.",
        # A date wrapped onto the next line of a hand-wrapped field.
        "No tagged releases, so this is read against the head. Verified\n  2026-08-13 via GitHub.",
        # The reverse order is the same claim.
        "2026-08-13: verified against the model card.",
    ],
)
def test_a_dated_verification_sentence_is_found_however_it_is_spelled(comments):
    assert dated_verification(comments)


@pytest.mark.parametrize(
    "comments",
    [
        None,
        "",
        "A footnote about the reading, with no date in it.",
        # A date that is a fact about the product, not about the reading.
        "General availability was 2026-08-13; the preview SKU is a separate entry.",
        "Service ends 2026-12-31 per the sunset notice.",
        # The verb far from a date is a different sentence.
        "The card was verified against the paper. Released 2026-08-13.",
    ],
)
def test_a_field_without_one_is_clean(comments):
    assert dated_verification(comments) is None


def test_the_whole_sentence_is_returned_so_the_reader_knows_what_to_delete():
    sentence = dated_verification(
        "The LICENSE file bundles third-party code. Verified 2026-08-13 via the README. Runs on CPUs."
    )
    assert sentence == "Verified 2026-08-13 via the README."


def test_no_product_carries_a_dated_verification_sentence():
    """The corpus-wide invariant, and the one this section exists to hold.

    Strict rather than a ratchet: the corpus was cleared in one scripted pass (#619), so there is
    no backlog to name, and an allowlist would only give the next instance somewhere to hide.
    """
    found = census()
    assert not found, (
        f"{len(found)} product(s) carry a dated verification sentence in comments. The date is "
        "`last_verified`; the document read belongs on a source entry as `url` and `shows`. "
        "See docs/reference/product-copy.md:\n"
        + "\n".join(f"  {slug}: {sentence}" for slug, sentence in list(found.items())[:20])
    )


def test_the_census_walks_the_whole_corpus():
    """An empty census satisfies the invariant trivially, and two corpus walks in this repo's
    history silently narrowed. `products()` has to see what `_descriptions()` sees."""
    from build.product_prose import products

    assert len(products()) == len(list(_descriptions())) > 400
