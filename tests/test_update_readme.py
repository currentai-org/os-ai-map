from build.update_readme import _apply


_BADGES = (
    '  <img src="https://img.shields.io/badge/products-458-F0776A" alt="458 products">\n'
    '  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">\n'
)


def test_apply_updates_url_and_alt():
    out = _apply(_BADGES, "products", 480)
    assert "badge/products-480-F0776A" in out
    assert 'alt="480 products"' in out
    assert "products-458" not in out


def test_apply_is_idempotent():
    once = _apply(_BADGES, "products", 480)
    twice = _apply(once, "products", 480)
    assert once == twice


def test_apply_leaves_other_badges_untouched():
    out = _apply(_BADGES, "products", 480)
    # the license badge (also a shields.io badge with a number-free message) is unchanged
    assert "badge/license-MIT-blue.svg" in out
    assert 'alt="License: MIT"' in out
