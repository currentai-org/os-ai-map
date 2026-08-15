"""A `reported_traction` note citing a figure has to say what the figure counts.

`reported_traction` is the instrument defined by having no count behind it —
`docs/reference/adoption.md`: "A `reported_traction` record claims **no count at all**, so it
may carry a word and never a number."

That rule was enforced on the `reach` LABEL, and 68 numeric labels were stripped on
2026-08-13 for asserting a measurement nobody made. It was never enforced on the prose, so
the numbers stayed in the notes, where a reader still takes them for a count of the product
and nothing could say otherwise. Measured 2026-08-15, 19 of 109 records banded on a parent
platform's reach and every one of them said so in a sentence no machine could read.

`banded_quantity` is that caveat given a field. This gate is strict from day one, which is a
departure from how `check_adoption` and `check_instrument` both shipped — those met an
existing backlog and went non-strict so the gate would not fail on the day it landed. There
is no backlog here: the field arrived with all 57 records that needed one already filled in
by `build/migrate_banded_quantity.py`, so strict costs nothing and stops the class recurring.

The gate covers only what a machine can decide. A parent-platform band citing NO figure —
`azure-ai-foundry-observability`, `vertex-ai-model-observability` — is exactly the same
defect and is uncatchable by any regex, so those were backfilled by hand and nothing here
enforces them. This is the ratchet the repo's other gates use: cover what is decidable, and
grow the coverage rather than blocking on the undecidable part.
"""

from __future__ import annotations

import pytest

from build.check_instrument import ROOT, magnitudes_in, unattributed_magnitudes
from build.validate import load_sources


@pytest.fixture(scope="module")
def sources():
    return load_sources(ROOT)


def test_every_reported_traction_figure_says_what_it_counts(sources):
    findings = unattributed_magnitudes(sources)
    assert not findings, (
        "reported_traction records citing a figure with no banded_quantity:\n  "
        + "\n  ".join(findings)
    )


def test_the_walk_has_not_silently_narrowed(sources):
    """A gate that stops looking passes green. Two in this repo have.

    The population is `reported_traction` records, and if it collapses the assertion above
    becomes vacuous without failing.
    """
    n = sum(
        1
        for score in sources["scores"].values()
        if ((score or {}).get("adoption") or {}).get("signal_type") == "reported_traction"
    )
    assert n > 90, f"only {n} reported_traction records found; the walk has drifted"


def test_banded_quantity_is_populated_where_it_was_backfilled(sources):
    """The migration's own output, asserted against the corpus rather than its return value."""
    covered = sum(
        1
        for score in sources["scores"].values()
        if ((score or {}).get("adoption") or {}).get("banded_quantity")
    )
    assert covered >= 57, f"only {covered} records carry a banded_quantity; expected at least 57"


@pytest.mark.parametrize(
    "note, expected",
    [
        ("Replit reported 50M+ platform users", True),
        ("about 417k workflow runs a month", True),
        ("1,034,712 all-time downloads", True),
        # A bare count of nameable things is not a measurement claim, and demanding
        # attribution for one would make the gate fire on ordinary prose.
        ("28 enterprise testimonials from named customers", False),
        ("supported by 5 production SDKs", False),
        # A year is the one thing the thousands-separator arm would otherwise catch.
        ("Re-read 2026-08-13 and unchanged", False),
        ("GA since 2025-03-20 inside Amazon Bedrock", False),
    ],
)
def test_what_counts_as_a_magnitude(note, expected):
    assert bool(magnitudes_in(note)) is expected


def test_strict_exits_nonzero_on_an_unattributed_figure(tmp_path, monkeypatch, capsys):
    """The checker's status and exit code must grade on BOTH of its finding classes.

    The first cut printed unattributed figures and then computed status and exit from the
    older `findings` list alone, so a violation could print above an `[OK]` and exit 0. That
    is this module's own subject — a label that is checkable over a claim that is not —
    turned on the module itself.
    """
    import build.check_instrument as ci

    monkeypatch.setattr(ci, "unattributed_magnitudes", lambda _s: ["widget: planted finding"])
    monkeypatch.setattr("sys.argv", ["check_instrument", "--strict"])
    assert ci.main() == 1
    out = capsys.readouterr().out
    assert "planted finding" in out
    assert "[OK]" not in out
    assert "1 figures unattributed" in out


def test_non_strict_still_exits_zero_on_an_unattributed_figure(monkeypatch, capsys):
    """Non-strict stays informational, matching how check_adoption and this gate shipped."""
    import build.check_instrument as ci

    monkeypatch.setattr(ci, "unattributed_magnitudes", lambda _s: ["widget: planted finding"])
    monkeypatch.setattr("sys.argv", ["check_instrument"])
    assert ci.main() == 0
