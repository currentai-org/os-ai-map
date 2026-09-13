"""The hardware ladder's form-factor routing, replayed against the real rubric.

`sources/rubrics/hardware.yaml` asks two different sets of questions of two different
kinds of thing: a board or a module is scored on whether its design files were published,
a chipset on whether its documentation is public and whether anybody can buy one. The
routing between them is the whole of #219, and it is the part that cannot be read off a
reproduction count - every product on today's roster answers its own questions, so the
category reproduces 20/20 whether or not a chipset is fenced off from the board rungs.

What these replays pin is the fence. They build fact sets no product records, walk the
REAL formula with them, and assert where each one lands. Putting the chipset rung above
the board rungs and leaving the board rungs unguarded reads as routing and is not: first
match wins means a chipset that fails its own rung meets a board's next, so a part whose
datasheets sit behind a design win would collect 3/documented on somebody else's
reference-board files.

Falling off the ladder is the intended outcome for a chipset that fails, not a gap. The
formula declares no `otherwise`, so a product the rungs do not decide abstains and the
category defers it with a reason - which is the ladder saying it does not know, rather
than a board's answer wearing a chipset's name.
"""

from pathlib import Path

from build.check_rubric import score_openness
from build.rubrics import load_shared

ROOT = Path(__file__).resolve().parents[1]


def hardware_ladder():
    return load_shared(ROOT)["hardware"]


def landing(**components):
    """Where the real hardware ladder puts one synthetic product."""
    clauses = ";".join(f"{key}:{value}" for key, value in components.items())
    outcome = score_openness(hardware_ladder(), {"components": clauses})
    return outcome.result


def test_a_chipset_whose_datasheets_are_gated_is_not_scored_from_board_files():
    """The replay that failed review. `nda` misses the chipset rung; the design rungs
    below it must not pick the product up on a reference design that is not its own."""
    assert landing(
        form_factor="chipset",
        datasheets="nda",
        schematics="partial",
        toolchain="open",
        retail="distributor",
    ) is None


def test_a_chipset_nobody_can_buy_is_not_documented():
    """`documented` is defined by the category as datasheets public AND buyable. A
    design-win part meets half of that, and half is not the class."""
    assert landing(
        form_factor="chipset",
        datasheets="public",
        schematics="published",
        toolchain="open",
        retail="restricted",
    ) is None


def test_a_withdrawn_chipset_is_not_scored_either():
    """`discontinued` is a different fact from `restricted` and `retail` keeps them apart,
    but the rung only asks whether anybody can buy one, and nobody can."""
    assert landing(form_factor="chipset", datasheets="public", retail="discontinued") is None


def test_a_chipset_that_answers_both_questions_scores():
    """Public datasheets and a part on sale. No `schematics` anywhere in the fact set,
    which is the point: this is the rung that let `rockchip-rk3588` off its deferral."""
    assert landing(form_factor="chipset", datasheets="public", retail="distributor") == (3, "documented")


def test_the_chipset_rung_does_not_read_the_toolchain():
    """Deliberate, and pinned so that adding a toolchain condition has to argue with a
    test. This category's vocabulary places a closed SDK inside `documented`, and the
    Jetson modules record `toolchain: closed` and score 3 - so requiring an open SDK of a
    chipset would score bare silicon below the module built on it."""
    closed = landing(form_factor="chipset", datasheets="public", retail="distributor", toolchain="closed")
    opened = landing(form_factor="chipset", datasheets="public", retail="distributor", toolchain="open")
    assert closed == opened == (3, "documented")


def test_a_board_still_climbs_the_design_rungs():
    assert landing(
        form_factor="board", schematics="published", toolchain="open"
    ) == (4, "open_toolchain")


def test_a_module_still_climbs_the_design_rungs():
    """`schematics: none` on an M.2 card means withheld, which is an answer. The same
    word on a chipset means there was never a board, which is not."""
    assert landing(form_factor="module", schematics="none") == (3, "documented")
    assert landing(form_factor="chipset", schematics="none") is None


def test_a_hardware_product_recording_no_form_factor_abstains():
    """A new product added without the call is not quietly scored as a board. The ladder
    reports that it does not decide, and the category has to defer it or the curator has
    to make the call - which is what a required routing dimension is for."""
    assert landing(schematics="published", toolchain="open") is None
