import pytest

from build.check_payload import PayloadError, check


def _ok():
    return {
        "categories": {"c": {"products": [
            {"slug": "a", "org_slug": "o", "freshness": {"date": "2026-08-01", "basis": "commit"}},
            {"slug": "b", "org_slug": "o", "freshness": {"date": "2026-07-01", "basis": "verified"}},
        ]}},
        "organizations": {"o": {"slug": "o", "products": ["a", "b"]}},
        "aliases": {"products": {"old-a": "a"}, "organizations": {}},
    }


def test_passes_a_well_formed_payload():
    check(_ok())


def test_fails_when_a_product_has_no_slug():
    p = _ok(); del p["categories"]["c"]["products"][0]["slug"]
    with pytest.raises(PayloadError, match="slug"):
        check(p)


def test_fails_when_two_products_share_a_slug():
    p = _ok(); p["categories"]["c"]["products"][1]["slug"] = "a"
    with pytest.raises(PayloadError, match="duplicate"):
        check(p)


def test_fails_when_an_org_slug_does_not_resolve():
    p = _ok(); p["categories"]["c"]["products"][0]["org_slug"] = "ghost"
    with pytest.raises(PayloadError, match="ghost"):
        check(p)


def test_fails_when_an_alias_key_is_also_a_live_slug():
    p = _ok(); p["aliases"]["products"]["a"] = "b"
    with pytest.raises(PayloadError, match="live"):
        check(p)


def test_fails_when_an_alias_target_is_missing():
    p = _ok(); p["aliases"]["products"]["old-a"] = "ghost"
    with pytest.raises(PayloadError, match="ghost"):
        check(p)


def test_fails_when_every_product_shares_one_freshness_date():
    """The shallow-clone canary. A depth-1 checkout dates all 470 to the tip commit, which
    is not an error anywhere else in the pipeline."""
    p = _ok()
    for row in p["categories"]["c"]["products"]:
        row["freshness"] = {"date": "2026-08-05", "basis": "commit"}
    with pytest.raises(PayloadError, match="one distinct freshness date"):
        check(p)


# --- Cannot-evaluate paths: a missing or malformed top-level block must refuse to judge
# the payload, not fall through to a Python TypeError/AttributeError that happens to be
# non-zero for the wrong reason, and never fall through to a silent pass. ---

def test_fails_when_categories_key_is_missing():
    p = _ok(); del p["categories"]
    with pytest.raises(PayloadError, match="categories"):
        check(p)


def test_fails_when_categories_is_none():
    p = _ok(); p["categories"] = None
    with pytest.raises(PayloadError, match="categories"):
        check(p)


def test_fails_when_a_category_is_not_an_object():
    p = _ok(); p["categories"]["c"] = ["not", "a", "dict"]
    with pytest.raises(PayloadError, match="c"):
        check(p)


def test_fails_when_a_category_has_no_products_list():
    p = _ok(); p["categories"]["c"]["products"] = None
    with pytest.raises(PayloadError, match="products"):
        check(p)


def test_fails_when_organizations_key_is_missing():
    p = _ok(); del p["organizations"]
    with pytest.raises(PayloadError, match="organizations"):
        check(p)


def test_fails_when_organizations_is_none():
    p = _ok(); p["organizations"] = None
    with pytest.raises(PayloadError, match="organizations"):
        check(p)


def test_fails_when_aliases_block_is_missing():
    p = _ok(); del p["aliases"]
    with pytest.raises(PayloadError, match="aliases"):
        check(p)


def test_fails_when_aliases_products_is_not_a_dict():
    p = _ok(); p["aliases"]["products"] = None
    with pytest.raises(PayloadError, match="aliases"):
        check(p)


def test_fails_when_a_product_row_is_not_an_object():
    p = _ok(); p["categories"]["c"]["products"][0] = "not-a-dict"
    with pytest.raises(PayloadError):
        check(p)


def test_fails_on_an_entirely_empty_product_set():
    """The freshness canary ('more than one distinct date') must not pass vacuously just
    because there is nothing to compare. Zero products is an absence of evidence, not two
    distinct dates, and the gate must say so rather than reading as ok."""
    p = _ok(); p["categories"]["c"]["products"] = []
    with pytest.raises(PayloadError, match="no products"):
        check(p)


def test_fails_when_a_product_row_has_no_freshness_key_at_all():
    p = _ok(); del p["categories"]["c"]["products"][0]["freshness"]
    with pytest.raises(PayloadError, match="freshness"):
        check(p)


def test_fails_when_freshness_is_none():
    p = _ok(); p["categories"]["c"]["products"][0]["freshness"] = None
    with pytest.raises(PayloadError, match="freshness"):
        check(p)


def test_fails_when_freshness_basis_is_unrecognized():
    p = _ok()
    p["categories"]["c"]["products"][0]["freshness"] = {"date": "2026-08-01", "basis": "guessed"}
    with pytest.raises(PayloadError, match="freshness"):
        check(p)


def test_fails_when_freshness_date_is_empty():
    p = _ok()
    p["categories"]["c"]["products"][0]["freshness"] = {"date": "", "basis": "commit"}
    with pytest.raises(PayloadError, match="freshness"):
        check(p)


def test_fails_when_org_slug_is_missing_entirely():
    p = _ok(); del p["categories"]["c"]["products"][0]["org_slug"]
    with pytest.raises(PayloadError, match="missing organization"):
        check(p)
