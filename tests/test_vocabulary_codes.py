"""The ISO code lists behind `country` and `languages` (#684), read from their snapshots."""

from __future__ import annotations

import pytest

from build.vocabulary import country_codes, language_codes


@pytest.mark.parametrize("code", ["US", "GB", "TW", "SG", "SE", "NO", "FR", "IN"])
def test_real_country_codes_are_allowed(code):
    assert code in country_codes()


@pytest.mark.parametrize("code", ["UK", "EU", "XK", "USA", "us", "", "ZZ"])
def test_country_codes_outside_iso_3166_1_are_refused(code):
    assert code not in country_codes()


def test_the_country_set_is_the_snapshot_and_nothing_else():
    from build.vocabulary import _COUNTRY_SNAPSHOT

    lines = _COUNTRY_SNAPSHOT.read_text(encoding="utf-8").strip().split("\n")
    assert len(country_codes()) == len(lines) - 1
    assert all(len(code) == 2 and code.isupper() for code in country_codes())


@pytest.mark.parametrize("code", ["eng", "swa", "quz", "mri", "grn", "amh", "hau", "zho", "ara"])
def test_individual_and_macro_languages_are_allowed(code):
    assert code in language_codes()


@pytest.mark.parametrize("code", ["mul", "und", "zxx", "mis", "en", "sw", "ENG", "xxx", ""])
def test_special_two_letter_and_unknown_language_codes_are_refused(code):
    assert code not in language_codes()


def test_only_scopes_i_and_m_are_loaded():
    from build.vocabulary import _LANGUAGE_SNAPSHOT

    header, *rows = _LANGUAGE_SNAPSHOT.read_text(encoding="utf-8").split("\n")
    columns = header.split("\t")
    by_scope: dict[str, set[str]] = {}
    for row in rows:
        if not row.strip():
            continue
        cells = row.rstrip("\r").split("\t")
        by_scope.setdefault(cells[columns.index("Scope")], set()).add(cells[columns.index("Id")])
    assert language_codes() == by_scope["I"] | by_scope["M"]
    assert not language_codes() & by_scope["S"]


def test_both_loaders_are_cached():
    assert country_codes() is country_codes()
    assert language_codes() is language_codes()


def test_the_gate_and_the_writer_read_the_same_code_lists():
    """`validate` and `apply_attributes` import the loaders rather than holding a copy, so the
    gate cannot refuse a code the writer just wrote (or the reverse)."""
    import build.apply_attributes as apply_attributes
    import build.validate as validate
    import build.vocabulary as vocabulary

    for module in (validate, apply_attributes):
        assert module.country_codes is vocabulary.country_codes
        assert module.language_codes is vocabulary.language_codes
