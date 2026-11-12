"""The ISO code lists behind `country` and `languages` (#684), read from their snapshots."""

from __future__ import annotations

from pathlib import Path

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


def test_the_language_list_is_exactly_the_codes_the_corpus_uses():
    """R-2026-11-11-p: the repository keeps only the codes its records use. `build.validate`
    refuses a used code the list lacks; this refuses a listed code no record uses, so the list
    never grows into a copy of the ISO 639-3 code set."""
    from build.language_codes import used_codes

    assert language_codes() == frozenset(used_codes())


def test_the_language_list_is_sorted_unique_codes_with_its_attribution():
    from build.language_codes import SNAPSHOT, read_snapshot

    codes = read_snapshot(SNAPSHOT)
    assert codes == sorted(set(codes))
    assert all(len(c) == 3 and c.isascii() and c.isalpha() and c.islower() for c in codes)
    text = SNAPSHOT.read_text(encoding="utf-8")
    assert "https://iso639-3.sil.org" in text
    assert "not part of the standard" in text


def test_no_iso_639_3_code_table_is_committed():
    """SIL's code tables stay on Artio (R-2026-11-11-p). A file carrying their columns, reference
    names above all, is a copy of the code set however it got here."""
    root = Path(__file__).resolve().parents[1]
    assert not (root / "sources" / "snapshots" / "iso-639-3.tab").exists()
    markers = ("Ref_Name", "Part2b", "Print_Name")
    for folder in ("sources", "tests/fixtures", "warehouse", "docs"):
        for path in (root / folder).rglob("*"):
            if path.is_file() and path.suffix in {".tab", ".tsv", ".csv", ".txt"}:
                head = path.read_text(encoding="utf-8", errors="ignore")[:2000]
                assert not any(m in head for m in markers), path


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
