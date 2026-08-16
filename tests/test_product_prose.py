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

from build.product_prose import census, classify

ROOT = Path(__file__).resolve().parents[1]

# Phrases that assert a superlative or a growth rate without a measure. Ordered roughly by how
# often they appeared. `dominant ` keeps its trailing space so it does not fire on "dominantly"
# or on a description of market structure that names its evidence.
MARKETING = re.compile(
    r"\b("
    r"the fastest|fastest way|fastest.growing"
    r"|de facto|de-facto"
    r"|growing rapidly|rapidly growing"
    r"|industry.standard|best.in.class|world.class|gold standard"
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


# --- the verification line -------------------------------------------------------------
#
# `docs/reference/product-copy.md` standardizes it on `Verified <date> via <document>.` The
# 2026-08 closeout brought all 472 products to that form (tag `baseline-472-2026-08-16`).
# What follows keeps them there: a new product, or an edit to an existing one, can reintroduce
# any of the four unresolved states, and `sweep_status` reports the state it is told.


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
        # promised a mechanical fix that does not exist.
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


@pytest.mark.parametrize(
    "comments",
    [
        # Canonical in SHAPE, naming a method. `generic` has to outrank `canonical` or the
        # check grades on shape while the thing it exists to find sits in the payload.
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


def test_every_product_names_a_document_a_reader_can_reopen():
    """The corpus-wide invariant, and the one this file exists to hold.

    A failure names the products and their state. `generic` needs a document supplied;
    `named_noncanonical` needs the wording brought to `via`; `ambiguous_noncanonical` and
    `missing` need somebody to read the record.
    """
    by_state = census()
    unresolved = {
        state: slugs for state, slugs in by_state.items() if state != "canonical"
    }
    assert not unresolved, (
        "every verification line must read `Verified <date> via <document>.` — see "
        f"docs/reference/product-copy.md:\n{unresolved}"
    )


def test_the_census_walks_the_whole_corpus():
    """Same guard as above, on the other instrument: an empty census satisfies the invariant
    trivially, and two corpus walks in this repo's history silently narrowed."""
    by_state = census()
    assert sum(len(v) for v in by_state.values()) == len(list(_descriptions()))
    assert set(by_state) <= {"canonical", "named_noncanonical", "ambiguous_noncanonical",
                             "generic", "missing"}
