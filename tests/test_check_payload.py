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


def _ending():
    p = _ok()
    p["categories"]["c"]["products"][0]["end_of_life"] = {
        "date": "2026-12-31", "source": "https://example.com/sunset"}
    return p


def test_passes_a_well_formed_end_of_life_row():
    check(_ending())


def test_fails_an_end_of_life_that_is_not_an_object():
    """A bare date is the shortcut a curator reaches for, and the app cannot render it."""
    p = _ending(); p["categories"]["c"]["products"][0]["end_of_life"] = "2026-12-31"
    with pytest.raises(PayloadError, match="not an object"):
        check(p)


def test_fails_an_end_of_life_date_in_another_notation():
    p = _ending(); p["categories"]["c"]["products"][0]["end_of_life"]["date"] = "31/12/2026"
    with pytest.raises(PayloadError, match="ISO 8601"):
        check(p)


def test_fails_an_end_of_life_with_no_usable_source():
    """The claim reaches the reader; the link that backs it has to reach them too."""
    p = _ending(); p["categories"]["c"]["products"][0]["end_of_life"]["source"] = "perspectiveapi.com"
    with pytest.raises(PayloadError, match="no usable source"):
        check(p)


def test_a_row_with_no_end_of_life_is_unaffected():
    check(_ok())


def test_passes_a_row_with_a_steward_and_languages():
    p = _ok()
    row = p["categories"]["c"]["products"][0]
    row["steward"] = "linux-foundation"
    row["languages"] = ["amh", "hau"]
    p["organizations"]["linux-foundation"] = {"slug": "linux-foundation", "products": []}
    check(p)


def test_fails_a_steward_with_no_entry_in_organizations():
    """A steward is an org slug so that its type and country come with it; it has to resolve."""
    p = _ok()
    p["categories"]["c"]["products"][0]["steward"] = "linux-foundation"
    with pytest.raises(PayloadError, match="no entry in organizations"):
        check(p)


@pytest.mark.parametrize("bad", [[], ["hau", "amh"], ["en"], ["amh", "amh"], "amh", ["AMH"], [3]])
def test_fails_languages_that_are_not_a_sorted_list_of_three_letter_codes(bad):
    p = _ok()
    p["categories"]["c"]["products"][0]["languages"] = bad
    with pytest.raises(PayloadError, match="languages"):
        check(p)


@pytest.mark.parametrize("bad", ["", None, ["lf"]])
def test_fails_a_steward_that_is_not_a_slug_string(bad):
    p = _ok()
    p["categories"]["c"]["products"][0]["steward"] = bad
    with pytest.raises(PayloadError, match="steward"):
        check(p)


# --- the depth ladder's per-language bands (#953) ----------------------------------------------


def _measured(band, face=None, best="unavailable"):
    return {"band": band, "face_value": band if face is None else face, "best_original": best,
            "set_by": "some-component", "tasks": ["knowledge_exam"]}


_UNMEASURED = {"band": None, "face_value": None, "best_original": None, "set_by": None, "tasks": []}


def _with_depth(score=3, languages=None, status="provisional", measured=None, targets=None):
    """The well-formed payload with one evaluation set carrying a depth block."""
    languages = {"aaa": _measured(3), "bbb": _measured(3, best=2), "ccc": _measured(1, face=3)} \
        if languages is None else languages
    m = sum(1 for e in languages.values() if e["band"] is not None)
    p = _ok()
    p["categories"]["c"]["products"][0]["capability"] = {
        "score": score, "basis": "evaluation_depth",
        "depth": {"status": status, "completeness": {"measured": m if measured is None else measured,
                                                     "targets": len(languages) if targets is None else targets},
                  "per_language": languages},
    }
    return p


def _check(p, roster=None):
    """`check` with the set's target-language roster supplied, as `set_targets` would read it from
    `sources/`. By default the roster is the per_language keys the payload already carries, so a
    test about some other invariant is not also a test of the roster."""
    if roster is None:
        roster = list(p["categories"]["c"]["products"][0]["capability"]["depth"].get("per_language") or {})
    check(p, targets=lambda slug: {"a": roster}[slug])


def test_passes_per_language_bands_that_reproduce_the_band():
    _check(_with_depth())


def test_passes_an_unresolved_set_whose_languages_are_all_unmeasured():
    _check(_with_depth(score=None, status="unresolved",
                      languages={"aaa": dict(_UNMEASURED), "bbb": dict(_UNMEASURED)}))


def test_passes_an_unmeasured_language_the_median_absorbs():
    langs = {"aaa": _measured(4), "bbb": _measured(4), "ccc": _measured(4), "ddd": dict(_UNMEASURED)}
    _check(_with_depth(score=4, languages=langs))


def test_fails_when_the_per_language_bands_give_another_band():
    with pytest.raises(PayloadError, match="give a set band of 3, but capability.score is 4"):
        _check(_with_depth(score=4))


def test_fails_when_an_unmeasured_language_would_move_the_median():
    """Filled at 0 and at 5 the median differs, so the band does not stand and a recorded 5 is
    not what the languages say."""
    with pytest.raises(PayloadError, match="give a set band of None"):
        _check(_with_depth(score=5, languages={"aaa": _measured(5), "bbb": dict(_UNMEASURED)}))


def test_fails_when_the_status_disagrees_with_the_languages():
    with pytest.raises(PayloadError, match="depth status 'unresolved'"):
        _check(_with_depth(status="unresolved"))


def test_fails_when_completeness_disagrees_with_the_languages():
    with pytest.raises(PayloadError, match="completeness says 2 of 3"):
        _check(_with_depth(measured=2))


def test_fails_a_depth_block_with_no_per_language_mapping():
    p = _with_depth()
    del p["categories"]["c"]["products"][0]["capability"]["depth"]["per_language"]
    with pytest.raises(PayloadError, match="no per_language mapping"):
        _check(p)


def test_fails_an_unmeasured_language_that_fills_a_figure():
    langs = {"aaa": _measured(3), "bbb": {**_UNMEASURED, "set_by": "some-component"}}
    with pytest.raises(PayloadError, match="unmeasured but fills a figure"):
        _check(_with_depth(languages=langs, score=None, status="unresolved"))


@pytest.mark.parametrize("bad", [{"band": 6}, {"band": True}, {"best_original": 0.5},
                                 {"face_value": None}])
def test_fails_a_measured_language_figure_that_is_not_a_band(bad):
    langs = {"aaa": {**_measured(3), **bad}}
    with pytest.raises(PayloadError, match="not a band"):
        _check(_with_depth(languages=langs))


def test_fails_a_language_key_that_is_not_an_iso_code():
    with pytest.raises(PayloadError, match="not an ISO 639-3 code"):
        _check(_with_depth(languages={"Thai": _measured(3)}))



# --- hardening the per-language gate (follow-up to #1090) --------------------------------------


@pytest.mark.parametrize("filled", [{"face_value": 0}, {"best_original": 0}, {"set_by": ""},
                                    {"tasks": None}])
def test_fails_an_unmeasured_language_with_a_falsy_figure(filled):
    """An unmeasured language is exactly `band: null` with null figures and an empty task list.
    A `0`, an `""` or a missing list is a filled figure, never a quiet stand-in for "unmeasured"."""
    langs = {"aaa": _measured(3), "bbb": _measured(3), "ccc": _measured(3),
             "ddd": {**_UNMEASURED, **filled}}
    with pytest.raises(PayloadError, match="unmeasured but fills a figure"):
        _check(_with_depth(score=3, languages=langs))


def test_passes_a_measured_zero():
    """A band of 0 is a measurement (a measured zero), not an unmeasured language. The ladder can
    also publish no `set_by` for it, when no component lifted the language above zero."""
    langs = {"aaa": {"band": 0, "face_value": 0, "best_original": 0, "set_by": None, "tasks": []},
             "bbb": {"band": 0, "face_value": 0, "best_original": "unavailable", "set_by": None,
                     "tasks": []}}
    _check(_with_depth(score=0, languages=langs))


def test_fails_per_language_keys_that_are_not_the_target_roster():
    """Three well-formed codes, three targets, three measured: the count and the shape agree, but
    `ccc` is not one of the set's target languages and `ddd` is missing."""
    with pytest.raises(PayloadError, match=r"not its target languages: missing \['ddd'\], not a "
                                           r"target \['ccc'\]"):
        _check(_with_depth(), roster=["aaa", "bbb", "ddd"])


def test_fails_a_pivot_language_published_as_a_target():
    """The roster is `languages` less `pivot_languages`; a pivot carried as a target fails."""
    with pytest.raises(PayloadError, match=r"not a target \['ccc'\]"):
        _check(_with_depth(), roster=["aaa", "bbb"])


def test_fails_when_the_roster_cannot_be_read():
    def unreadable(slug):
        raise FileNotFoundError(f"sources/scores/{slug}.yaml")
    with pytest.raises(PayloadError, match="roster cannot be read"):
        check(_with_depth(), targets=unreadable)


def test_fails_a_band_above_its_face_value():
    """The corroboration cap only lowers a band, so a band above the face value was not built by
    the ladder. The set band still reproduces, so only this check sees it."""
    langs = {"aaa": _measured(3, face=2), "bbb": _measured(3, best=2), "ccc": _measured(1, face=3)}
    with pytest.raises(PayloadError, match="band 3 above its face value 2"):
        _check(_with_depth(languages=langs))


def test_fails_a_best_original_band_above_the_band():
    """The band is the larger of the set's own best band and its capped imports, so it is never
    below the best original band."""
    langs = {"aaa": _measured(3), "bbb": _measured(3, best=4, face=4), "ccc": _measured(1, face=3)}
    with pytest.raises(PayloadError, match="best_original 4 above its band 3"):
        _check(_with_depth(languages=langs))


def test_passes_a_best_original_equal_to_the_band_and_an_unavailable_one():
    langs = {"aaa": _measured(3, best=3), "bbb": _measured(3, face=5, best="unavailable"),
             "ccc": _measured(1, face=3, best=0)}
    _check(_with_depth(languages=langs))


def test_a_row_without_a_depth_block_is_unaffected():
    p = _ok()
    p["categories"]["c"]["products"][0]["capability"] = {"score": 3, "basis": "feature_matrix"}
    check(p)
