"""The channel-authority report: what the release-line comparison decides, and what it flags.

No test here touches the network. The release-line leg is exercised against fixtures — the
comparison is the part that can be wrong, and the two API calls behind it are not — and the
prose leg reads the committed corpus, which is where the pinned count lives.
"""
from pathlib import Path

from build import check_channel_authority as gate
from build.check_channel_authority import (
    is_prerelease,
    lag_verdict,
    newest_repo_tag,
    parse_version,
    release_lines,
    skipped_total,
    unremedied,
)
from build.sweep_status import under_coverage

ROOT = Path(__file__).resolve().parents[1]


def test_a_stable_major_behind_a_stable_major_fires():
    """`xtuner` as it stood: 0.2.0 on PyPI against v1.0.1 in the repository."""
    assert lag_verdict("0.2.0", "v1.0.1") == ("fires", 1)


def test_the_lag_counts_major_lines():
    """`gpt-researcher`, three lines behind, which reads differently from one."""
    assert lag_verdict("0.16.0", "v3.6.1") == ("fires", 3)


def test_the_same_major_line_is_clear():
    """A minor or patch lag is release cadence. Only a whole major line is the finding."""
    assert lag_verdict("1.45.0", "v1.46.2") == ("clear", 0)


def test_a_registry_ahead_of_the_repository_is_clear():
    assert lag_verdict("3.0.0", "v2.9.1") == ("clear", 0)


def test_a_prerelease_repo_tag_is_excluded_rather_than_flagged():
    """`khoj`: the repo's newest tag is 2.0.0-beta.28 and PyPI is on the 1.x line. A beta
    ahead of the registry is ordinary publishing, so it is reported as an exclusion."""
    assert lag_verdict("1.42.10", "2.0.0-beta.28") == ("prerelease", 1)


def test_a_prerelease_suffix_with_no_separator_is_still_a_prerelease():
    """The false positive the exclusion exists to prevent. `v4.0.0a6` has no word boundary
    between the `0` and the `a`, so a boundary-based test reads MinerU's alpha tag as a
    stable major line ahead of its registry and flags a product that is publishing normally."""
    assert is_prerelease("v4.0.0a6")
    assert lag_verdict("3.4.5", "v4.0.0a6") == ("prerelease", 1)


def test_a_prerelease_on_a_line_the_registry_already_has_is_simply_clear():
    """`qwenpaw`, the case that decided #435. PyPI 2.2.0b5 was uploaded the same day as the
    repo tag v2.2.0-beta.5: the registry is exactly current, and the only thing that looked
    wrong about it was a downloads-to-stars ratio, which is the un-auditable half. It is
    neither a finding nor an exclusion."""
    assert lag_verdict("2.2.0b5", "v2.2.0-beta.5") == ("clear", 0)


def test_an_unparseable_repo_tag_is_undecidable_not_clear():
    """`chroma` tags `latest` and `mlflow` tags `model-catalog/latest`. The comparison could
    not be made, which is a different statement from there being no lag - folding it into
    `clear` would report a silent pass over a product nobody checked."""
    assert parse_version("latest") is None
    assert lag_verdict("1.5.9", "latest") == ("undecidable", 0)
    assert lag_verdict("3.15.2", "model-catalog/latest") == ("undecidable", 0)


def test_a_version_embedded_in_a_monorepo_tag_still_parses():
    """`openlit` tags `openlit-2.0.0`. A per-package monorepo tag carries a real version."""
    assert parse_version("openlit-2.0.0") == (2, 0, 0)


def test_a_two_part_version_parses_with_a_zero_patch():
    assert parse_version("v4.0") == (4, 0, 0)


def test_only_a_record_still_banding_on_the_registry_count_is_flagged():
    """A fire is a fact about the release line; whether it is a FINDING depends on whether the
    band rests on that line. `swe-agent` publishes sweagent==0.0.1 against v1.1.0 and is not a
    finding, because it records `stars_fallback` - its level never followed from the package."""
    fires = [
        {"slug": "sageattention", "instrument": "usage_volume", "banded_quantity": ""},
        {"slug": "swe-agent", "instrument": "stars_fallback", "banded_quantity": ""},
        {"slug": "helm", "instrument": "reported_traction", "banded_quantity": ""},
    ]
    assert [row["slug"] for row in unremedied(fires)] == ["sageattention"]


def test_naming_the_quantity_is_the_other_remedy_and_clears_the_flag():
    """The ladder offers two remedies and the report advertises both, so both must clear.

    `langflow` and `semantic-kernel` are the shape: the band stands on the registry count, and
    a `banded_quantity` says what that count actually covers so nobody reads a precise number
    as a measurement of the whole product. A gate that accepted only the relabel would flag a
    correctly remedied product forever, which is how a report stops being read.
    """
    fires = [
        {"slug": "named", "instrument": "usage_volume",
         "banded_quantity": "npm downloads only; the Docker channel is larger and uncounted"},
        {"slug": "silent", "instrument": "usage_volume", "banded_quantity": ""},
    ]
    assert [row["slug"] for row in unremedied(fires)] == ["silent"]


def test_a_missing_banded_quantity_key_is_treated_as_absent():
    """Rows come from the corpus, where the key is optional, so absence must not raise."""
    assert unremedied([{"slug": "p", "instrument": "usage_volume"}]) == [
        {"slug": "p", "instrument": "usage_volume"}
    ]


# --- the release flag, and the boundary the version-string comparison sits on ---------------


def test_a_release_flagged_prerelease_with_a_stable_tag_still_fires(monkeypatch):
    """The xtuner shape, and the one refactor that would silently reverse this module.

    GitHub flags `v1.0.1` as a pre-release while its version string reads stable and the
    project's README documents V1 as current. `newest_repo_tag` returns the tag STRING and
    discards the flag on purpose: honoring the flag would report the 416-day-old `0.2.0`
    registry line as current, the opposite of what the project says about itself. `qwenpaw` is
    kept clear by the string test instead (`v2.2.0-beta.5` reads as a pre-release), which is
    where that protection belongs.
    """
    monkeypatch.setattr(
        gate, "_get_json",
        lambda url, token=None: [{"tag_name": "v1.0.1", "prerelease": True, "draft": False}],
    )
    assert newest_repo_tag("InternLM/xtuner") == "v1.0.1"
    assert lag_verdict("0.2.0", newest_repo_tag("InternLM/xtuner")) == ("fires", 1)


# --- the denominator, so a degraded run does not read as a healthy one -----------------------


def _fixture_corpus(monkeypatch, routed, repos, packages, tags):
    monkeypatch.setattr(gate, "pypi_routed", lambda root=None: routed)
    monkeypatch.setattr(gate, "declared_repo_id", lambda slug, root=None: repos.get(slug))
    monkeypatch.setattr(gate, "newest_pypi_release", lambda pkg: packages.get(pkg))
    monkeypatch.setattr(gate, "newest_repo_tag", lambda repo, token=None: tags.get(repo))
    monkeypatch.setattr(gate.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(gate, "_load", lambda path: {})


def test_the_report_counts_what_it_could_not_read(monkeypatch, tmp_path):
    """A 503-degraded run must not look healthier than a clean one.

    Four products, one verdict. Dropping the other three silently would print "1 fire" and read
    as a near-clean corpus; counted, it prints one of four readable and the reviewer knows the
    run is not evidence about the other three.
    """
    _fixture_corpus(
        monkeypatch,
        routed={"fires": "f", "norepo": "n", "deadpkg": "d", "deadrepo": "r"},
        repos={"fires": "o/fires", "deadpkg": "o/deadpkg", "deadrepo": "o/deadrepo"},
        packages={"f": ("1.0.0", "2025-01-01T00:00:00Z"), "d": None,
                  "r": ("1.0.0", "2025-01-01T00:00:00Z")},
        tags={"o/fires": "v2.0.0", "o/deadrepo": None},
    )
    legs = release_lines(tmp_path)
    assert legs["considered"] == 4
    assert [row["slug"] for row in legs["fires"]] == ["fires"]
    assert legs["skipped"] == {
        "declare no repository": 1, "package unreadable": 1, "repository unreadable": 1,
    }
    assert skipped_total(legs) == 3


def test_a_clean_run_skips_nothing(monkeypatch, tmp_path):
    """The other half of the invariant: with everything readable the denominator is the whole
    population and the skipped breakdown is empty, so a nonzero skip count always means
    something really was unreadable."""
    _fixture_corpus(
        monkeypatch,
        routed={"lagging": "l", "current": "c"},
        repos={"lagging": "o/lagging", "current": "o/current"},
        packages={"l": ("1.0.0", "2025-01-01T00:00:00Z"),
                  "c": ("2.1.0", "2026-01-01T00:00:00Z")},
        tags={"o/lagging": "v2.0.0", "o/current": "v2.1.0"},
    )
    legs = release_lines(tmp_path)
    assert legs["considered"] == 2
    assert skipped_total(legs) == 0
    assert [row["slug"] for row in legs["fires"]] == ["lagging"]


def test_the_prose_leg_holds_at_its_known_count():
    """Report-only today, so this pins the remaining set rather than asserting it is empty.

    Every entry is a band whose own note says the signal does not measure the product. The
    number moves DOWN when one is remedied — a `banded_quantity` naming what the figure counts,
    or a relabel to `reported_traction` — and moves UP when a re-read writes a new such note.
    It went 17 -> 15 when `areal` and `xtuner` were relabeled in the change that added this
    gate. Lower it as they are resolved; at zero the check can gate strict.

    15 -> 17 on 2026-09-01 with the Round 1 tranche: ktransformers and llm-d arrive with
    uzu-shaped honest notes - each bands on stars and says in its own words what the star
    count does not measure (a source-built product's tiny PyPI wrapper; production Helm
    deployments no channel counts). dynamo wrote the same shape and was remedied in the
    same change (banded_quantity naming the countable channel, note phrased as a floor),
    which is why it is not in the set.
    """
    findings = under_coverage()
    assert len(findings) == 17, [f[0] for f in findings]
    assert {f[0] for f in findings} == {
        "aider", "faiss", "gvisor", "ktransformers", "langflow", "llm-d", "llm-guard",
        "mistral-large", "mistral-rs", "n8n", "nemo-data-designer", "nemo-guardrails",
        "ollama", "perplexica", "promptfoo", "searxng", "uzu",
    }
