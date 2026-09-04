"""The Neon publisher, without a database.

Everything that decides what reaches the serving layer is a pure function here — the id a
row gets, the DDL for a table, the statement sequence the cutover runs — so all of it
is tested against strings rather than against a live Postgres. The two things that cannot
be checked that way are covered by running the CLI as a subprocess: that `--check` plans
without connecting, and that a DSN never reaches stdout or stderr.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

import build.neon_schema
from build.neon_schema import (
    ENUM_MAPS,
    ENUMS,
    SCHEMA_VERSION,
    SITE_TABLES,
    IdCollision,
    UnmappedValue,
    build_site_tables,
    enum_value,
    load_payload,
    product_ids,
    stable_id,
)
from build.publish_neon import (
    DEFAULT_SCHEMA,
    DSN_ENV,
    LOCK_TIMEOUT,
    PROTECTED_SCHEMAS,
    RUN_COLUMNS,
    RUN_TABLE,
    SWAP_ATTEMPTS,
    ExternalDependents,
    create_enum_sql,
    create_table_sql,
    copy_sql,
    external_dependents,
    grant_sql,
    is_retryable,
    plan,
    plan_table,
    check_schema_is_ours,
    quote_ident,
    quote_schema,
    reclaim_previous,
    require_ssl,
    scrub,
    stream_bytes,
    swap_in_place,
    swap_sql,
    working_schemas,
)

ROOT = Path(__file__).resolve().parent.parent

# A DSN shaped like Neon's, with parts distinctive enough that a leak is unambiguous.
FAKE_DSN = "postgresql://mapuser:pw-tripwire-9f31@nowhere-tripwire.example.invalid/gapmapdb"


# --- DDL ------------------------------------------------------------------------------

def test_create_table_sql_names_the_schema_and_every_typed_column():
    sql = create_table_sql(
        "gapmap_staging", (("slug", "TEXT"), ("weight_adopt", "DOUBLE PRECISION")), "categories"
    )
    assert sql.startswith('CREATE TABLE "gapmap_staging"."categories" (')
    assert '"slug" TEXT' in sql
    assert '"weight_adopt" DOUBLE PRECISION' in sql


def test_copy_sql_lists_the_columns_and_reads_a_header():
    plan = plan_table(
        _write_csv("products", "slug,display_name\na,A\nb,B\n"),
        declared=(("slug", "VARCHAR"), ("display_name", "VARCHAR")),
    )
    sql = copy_sql("gapmap_staging", plan)
    assert 'COPY "gapmap_staging"."products" ("slug", "display_name")' in sql
    assert "FORMAT csv, HEADER true" in sql


def test_the_run_table_carries_the_publish_identity_and_the_two_payload_dates():
    columns = dict(RUN_COLUMNS)
    assert set(columns) == {
        "run_id",
        "published_at",
        "schema_version",
        "built_at",
        "released_at",
        "source_git_sha",
        "declaration_version_id",
        "table_count",
        "row_counts",
    }
    assert columns["row_counts"] == "JSONB"
    assert columns["built_at"] == columns["released_at"] == "DATE"
    sql = create_table_sql("gapmap_staging", RUN_COLUMNS, RUN_TABLE)
    assert '"row_counts" JSONB' in sql


def test_the_schema_version_is_recorded_because_the_swap_is_the_migration():
    """Every publish rebuilds the schema from the mapping, so nothing else tells a reader
    which shape it is looking at."""
    assert isinstance(SCHEMA_VERSION, int) and SCHEMA_VERSION >= 1
    assert dict(RUN_COLUMNS)["schema_version"] == "INTEGER"


@pytest.mark.parametrize("bad", ["products; DROP SCHEMA gapmap", "two words", "", '"quoted"'])
def test_an_identifier_that_is_not_a_plain_name_is_refused(bad):
    with pytest.raises(ValueError):
        quote_ident(bad)


def test_grants_go_to_public_by_default_and_to_a_named_role_when_given():
    public = grant_sql("gapmap_staging", None)
    assert public[0].endswith("TO PUBLIC")
    assert 'GRANT SELECT ON ALL TABLES IN SCHEMA "gapmap_staging" TO PUBLIC' == public[1]
    named = grant_sql("gapmap_staging", "site_reader")
    assert all('"site_reader"' in statement for statement in named)


# --- the shared instance --------------------------------------------------------------

def test_the_default_schema_is_the_gap_maps_own():
    assert DEFAULT_SCHEMA == "os-ai-map"


def test_a_hyphenated_schema_name_is_quoted_not_refused():
    """The agreed Neon layout names the gap map's schema with a hyphen."""
    assert quote_schema("os-ai-map") == '"os-ai-map"'
    assert quote_schema("os-ai-map_staging") == '"os-ai-map_staging"'


@pytest.mark.parametrize("bad", ['os"ai', "os ai map", "-leading", "", "os\\map", "os;drop"])
def test_a_schema_name_that_would_need_escaping_is_refused(bad):
    """A schema name reaches DROP SCHEMA ... CASCADE."""
    with pytest.raises(ValueError):
        quote_schema(bad)


def test_a_hyphen_is_still_refused_in_a_table_or_column_name():
    """Fine in a schema a maintainer chose; never something a serializer should produce."""
    with pytest.raises(ValueError):
        quote_ident("os-ai-map")


@pytest.mark.parametrize("schema", sorted(PROTECTED_SCHEMAS))
def test_another_part_of_the_sites_schema_is_refused(schema):
    """drizzle, payload and public share this instance and this publisher drops schemas
    with CASCADE. A typo in --schema must not be able to take one of them."""
    with pytest.raises(ValueError, match="refusing"):
        check_schema_is_ours(schema)


@pytest.mark.parametrize("schema", ["os-ai-map_staging", "os-ai-map_previous"])
def test_the_publishers_own_working_schemas_are_refused_as_a_target(schema):
    with pytest.raises(ValueError, match="manages itself"):
        check_schema_is_ours(schema)


def test_the_gap_maps_own_schema_passes():
    check_schema_is_ours(DEFAULT_SCHEMA)


def test_a_protected_schema_on_the_cli_exits_2_without_connecting():
    result = _run(["--schema", "public"], {DSN_ENV: FAKE_DSN})
    assert result.returncode == 2
    assert "refusing" in result.stderr


def test_the_swap_touches_only_the_target_and_its_two_working_schemas():
    """Nothing on the shared instance outside these three names is named in the cutover."""
    named = set()
    for statement in swap_sql(DEFAULT_SCHEMA, live_exists=True):
        named.update(part.strip('"') for part in statement.split() if part.startswith('"'))
    assert named == {
        DEFAULT_SCHEMA,
        f"{DEFAULT_SCHEMA}_staging",
        f"{DEFAULT_SCHEMA}_previous",
    }
    assert not named & PROTECTED_SCHEMAS
    assert set(working_schemas(DEFAULT_SCHEMA)) == named


# --- the swap -------------------------------------------------------------------------

def test_the_first_run_is_a_single_rename():
    """There is no live schema to move aside, and renaming one that is absent is a
    different error from every other reason a rename fails."""
    assert swap_sql("gapmap", live_exists=False) == [
        'ALTER SCHEMA "gapmap_staging" RENAME TO "gapmap"'
    ]


def test_the_steady_state_swap_is_two_renames_and_moves_the_live_schema_aside_first():
    assert swap_sql("gapmap", live_exists=True) == [
        'ALTER SCHEMA "gapmap" RENAME TO "gapmap_previous"',
        'ALTER SCHEMA "gapmap_staging" RENAME TO "gapmap"',
    ]


def test_the_cutover_transaction_drops_nothing():
    """A DROP here would take AccessExclusiveLock on every table it removes, holding the
    applied-but-uncommitted renames behind any in-flight reader — and it would follow
    dependencies out of this schema. Reclaiming is the next run's job."""
    for live_exists in (True, False):
        for statement in swap_sql("gapmap", live_exists=live_exists):
            assert "DROP" not in statement.upper()
            assert "CASCADE" not in statement.upper()


def test_the_swap_never_drops_the_live_schema_by_name():
    """The live schema is renamed out of the way and the *old name's* holder is dropped.

    A `DROP SCHEMA gapmap` anywhere in this sequence would be a window with no serving
    layer at all, which is the failure the transaction exists to prevent.
    """
    for statement in swap_sql("gapmap", live_exists=True):
        assert not statement.startswith('DROP SCHEMA "gapmap" ')
        assert 'DROP SCHEMA IF EXISTS "gapmap" ' not in statement


# --- the DSN --------------------------------------------------------------------------

def test_require_ssl_appends_sslmode_when_the_url_omits_it():
    assert "sslmode=require" in require_ssl("postgresql://u:p@host/db")
    assert "sslmode=require" in require_ssl("postgresql://u:p@host/db?application_name=x")


def test_require_ssl_leaves_an_explicit_sslmode_alone():
    dsn = "postgresql://u:p@host/db?sslmode=verify-full"
    assert require_ssl(dsn) == dsn


def test_require_ssl_handles_a_keyword_dsn():
    assert require_ssl("host=h dbname=d") == "host=h dbname=d sslmode=require"
    assert require_ssl("host=h sslmode=disable") == "host=h sslmode=disable"


def test_scrub_removes_the_dsn_its_password_and_its_host():
    message = (
        f'could not translate host name "nowhere-tripwire.example.invalid" to address; '
        f"dsn was {FAKE_DSN}"
    )
    cleaned = scrub(message, FAKE_DSN)
    for secret in ("pw-tripwire-9f31", "nowhere-tripwire.example.invalid", "mapuser"):
        assert secret not in cleaned


# --- the CLI --------------------------------------------------------------------------

def _run(args: list[str], env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    import os

    env = dict(os.environ)
    env.pop(DSN_ENV, None)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, "-m", "build.publish_neon", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_check_plans_without_a_dsn_and_prints_the_row_counts():
    result = _run(["--check"])
    assert result.returncode == 0, result.stderr
    assert f"would load {len(SITE_TABLES)} tables" in result.stdout
    assert "products" in result.stdout
    assert RUN_TABLE in result.stdout
    assert "registry_" not in result.stdout, "Neon serves the site's tables and nothing else"


def test_a_publish_with_no_dsn_exits_2_and_says_which_variable():
    result = _run([])
    assert result.returncode == 2
    assert DSN_ENV in result.stderr
    assert "not set" in result.stderr


def test_no_part_of_the_dsn_ever_reaches_stdout_or_stderr(tmp_path):
    """The publish will fail — the host does not resolve — and the failure is the point:
    a libpq error quotes the host, one delimiter from the password."""
    result = _run(["--site-dir", str(tmp_path / "site")], {DSN_ENV: FAKE_DSN})
    assert result.returncode == 1, result.stdout + result.stderr
    output = result.stdout + result.stderr
    for secret in (FAKE_DSN, "pw-tripwire-9f31", "nowhere-tripwire.example.invalid", "mapuser"):
        assert secret not in output, f"{secret!r} leaked into the publisher's output"


# --- the table set --------------------------------------------------------------------

# --- enums ----------------------------------------------------------------------------

def test_the_five_enums_the_map_uses_are_declared():
    """The DBML's other three belong to the gallery tables, which the CMS owns. An enum no
    column can reference would be dead metadata, and one created here would be worse: a CMS
    table referencing it would depend on a schema this publisher renames on every load."""
    assert set(ENUMS) == {
        "alias_kind",
        "freshness_basis",
        "lineage_relation",
        "capability_relation",
        "metric_name",
    }


def test_create_enum_sql_makes_every_enum_inside_the_schema_being_built():
    statements = create_enum_sql("os-ai-map_staging")
    assert len(statements) == len(ENUMS)
    assert (
        'CREATE TYPE "os-ai-map_staging"."alias_kind" AS ENUM (\'product\', \'organization\')'
        in statements
    )


def test_an_enum_column_qualifies_its_type_with_the_schema():
    """Enum types are schema-scoped and the staging schema is never on the search path."""
    sql = create_table_sql("os-ai-map_staging", SITE_TABLES["aliases"].columns, "aliases")
    assert '"kind" "os-ai-map_staging"."alias_kind"' in sql


def test_every_mapped_value_lands_inside_its_enum():
    for enum, mapping in ENUM_MAPS.items():
        for source, target in mapping.items():
            assert target in ENUMS[enum], f"{enum}: {source!r} -> {target!r} is not a value"


def test_an_unmapped_value_fails_the_load_and_names_the_value():
    """A serving layer that coerced an unknown vocabulary item to something adjacent would
    be worse than one that stopped."""
    with pytest.raises(UnmappedValue) as caught:
        enum_value("capability_relation", "three_below", column="capability.relation")
    assert "three_below" in str(caught.value)
    assert "capability.relation" in str(caught.value)


def test_an_absent_value_is_null_not_an_error():
    for empty in (None, ""):
        assert enum_value("capability_relation", empty, column="capability.relation") is None


def test_the_capability_relation_mapping_is_lossy_and_says_so():
    """The payload carries a signed distance; the target enum has no distance. Both
    `one_below` and `two_below` arrive as `tier_below`, and that is deliberate."""
    assert enum_value("capability_relation", "one_below", column="c") == "tier_below"
    assert enum_value("capability_relation", "two_below", column="c") == "tier_below"
    assert enum_value("capability_relation", "at", column="c") == "peer"
    assert enum_value("capability_relation", "one_above", column="c") == "tier_above"


def test_every_relation_the_payload_actually_carries_is_mapped():
    """The guard against a new vocabulary item reaching the load unmapped."""
    payload = load_payload()
    for cid in payload["order"]:
        for product in payload["categories"][cid]["products"]:
            relation = (product.get("capability") or {}).get("relation")
            enum_value("capability_relation", relation, column="capability.relation")
            basis = (product.get("freshness") or {}).get("basis")
            enum_value("freshness_basis", basis, column="products.freshness_basis")


# --- keys -----------------------------------------------------------------------------

def test_stable_id_is_deterministic():
    """The whole point: the same table and key give the same id on every load, forever."""
    assert stable_id("products", "vllm") == stable_id("products", "vllm")
    assert stable_id("products", "vllm") != stable_id("products", "sglang")


def test_stable_id_is_scoped_to_its_table():
    """The table name is hashed in, so a category and a product sharing a slug do not share
    an id — a join that crosses tables by mistake matches nothing rather than working."""
    assert stable_id("products", "olmo-3") != stable_id("categories", "olmo-3")
    assert stable_id("categories", "evaluation") != stable_id("gaps", "evaluation")


def test_an_id_is_a_positive_bigint_because_postgres_has_no_unsigned_integer():
    """63 bits, not 64: keeping the top bit would make half the ids negative."""
    for key in ("vllm", "olmo-3", "", "x" * 500, "a|b|c"):
        ident = stable_id("products", key)
        assert 0 <= ident < 2**63


def test_product_ids_are_derived_from_the_slug_not_from_a_position():
    payload = load_payload()
    ids = product_ids(payload)
    assert product_ids(payload) == ids
    for slug, ident in ids.items():
        assert ident == stable_id("products", slug)


def test_publishing_the_same_corpus_twice_gives_identical_ids():
    """A publish that renumbered would move every id that had escaped into a URL or a cache."""
    payload = load_payload()
    first = build_site_tables(payload)
    second = build_site_tables(load_payload())
    for name, rows in first.items():
        assert [row.get("id") for row in rows] == [row.get("id") for row in second[name]]


def _fixture_payload(extra_slug: str | None = None) -> dict:
    """A two-product corpus, optionally with a third product sorting before both.

    Small on purpose: the property under test is that inserting a row leaves the others
    alone, and a fixture makes the inserted row's position in the sort explicit.
    """
    products = [
        {
            "slug": "mid-product",
            "product": "Mid",
            "org_slug": "acme",
            "type": "model",
            "openness": {"score": 3, "sources": [{"url": "https://example.test/mid"}]},
            "lineage": {"derived_from": ["some-base"]},
        },
        {"slug": "zeta-product", "product": "Zeta", "org_slug": "acme", "type": "model"},
    ]
    if extra_slug:
        products.insert(0, {"slug": extra_slug, "product": "New", "org_slug": "acme", "type": "model"})
    return {
        "generated": "2026-09-04",
        "order": ["a_category"],
        "layer_order": ["model_components"],
        "categories": {
            "a_category": {
                "label": "A Category",
                "arc": "build",
                "layer": "model_components",
                "stage": {"num": 2},
                "gaps": [],
                "products": products,
            }
        },
        "descriptions": {"categories": {}, "gaps": {}, "stages": {}},
        "organizations": {"acme": {"display_name": "Acme", "type": "company"}},
        "aliases": {},
        "long_tail": {"top": [{"name": "Tail One"}], "counts": {"model": 1}},
    }


def test_inserting_a_product_alphabetically_first_moves_no_existing_id():
    """The bug this replaces: ids were positions in a sorted slug list, so adding one product
    renumbered every row after it and any id in a URL, a cache or a CMS row pointed at a
    different product after the next publish."""
    before = build_site_tables(_fixture_payload())
    after = build_site_tables(_fixture_payload(extra_slug="aaa-new-product"))

    for name, rows in before.items():
        keyed = {row.get("id"): row for row in rows if row.get("id") is not None}
        after_ids = {row.get("id") for row in after[name]}
        for ident, row in keyed.items():
            assert ident in after_ids, f"{name}: {row} was renumbered by the insertion"

    products_before = {row["slug"]: row["id"] for row in before["products"]}
    products_after = {row["slug"]: row["id"] for row in after["products"]}
    assert products_before.items() <= products_after.items()
    assert set(products_after) - set(products_before) == {"aaa-new-product"}


def test_the_foreign_keys_in_a_fixture_corpus_resolve_to_the_hashed_parents():
    """The FKs are the reason the ids have to move together: a child row hashed from one key
    and a parent from another would produce a dangling reference the COPY would reject."""
    tables = build_site_tables(_fixture_payload())
    assert {row["category"] for row in tables["products"]} == {
        stable_id("categories", "a_category")
    }
    assert {row["layer"] for row in tables["categories"]} == {
        stable_id("layers", "model_components")
    }
    assert {row["stage"] for row in tables["categories"]} == {stable_id("stages", "2")}
    mid = stable_id("products", "mid-product")
    assert {row["product_id"] for row in tables["openness"]} == {
        mid,
        stable_id("products", "zeta-product"),
    }
    assert [row["product_id"] for row in tables["sources"]] == [mid]
    assert [row["id"] for row in tables["sources"]] == [
        stable_id("sources", "mid-product|openness|https://example.test/mid")
    ]
    assert [row["id"] for row in tables["product_lineage"]] == [
        stable_id("product_lineage", "mid-product|derived_from|some-base")
    ]
    assert [row["id"] for row in tables["long_tail_top"]] == [
        stable_id("long_tail_top", "Tail One")
    ]


def test_a_repeated_source_url_still_gets_an_id_of_its_own():
    """A product can list the same URL twice on the same axis, and both rows need a key."""
    payload = _fixture_payload()
    product = payload["categories"]["a_category"]["products"][0]
    product["openness"]["sources"] = [
        {"url": "https://example.test/mid"},
        {"url": "https://example.test/mid"},
    ]
    ids = [row["id"] for row in build_site_tables(payload)["sources"]]
    assert len(set(ids)) == 2
    assert ids[0] == stable_id("sources", "mid-product|openness|https://example.test/mid")
    assert ids[1] == stable_id("sources", "mid-product|openness|https://example.test/mid#2")


@pytest.mark.parametrize(
    "table",
    [name for name, spec in SITE_TABLES.items() if "id" in dict(spec.columns)],
)
def test_every_id_column_is_a_bigint(table):
    """63-bit ids do not fit an INTEGER. The departure from the designers' `integer` is
    deliberate and is recorded in docs/reference/where-scores-live.md."""
    assert dict(SITE_TABLES[table].columns)["id"].startswith("BIGINT")


@pytest.mark.parametrize(
    "table,column",
    [
        ("categories", "layer"),
        ("categories", "stage"),
        ("gaps_categories", "cat_id"),
        ("gaps_categories", "gap_id"),
        ("products", "category"),
        ("openness", "product_id"),
        ("adoption", "product_id"),
        ("capability", "product_id"),
        ("sources", "product_id"),
        ("product_lineage", "product_id"),
    ],
)
def test_every_foreign_key_column_is_a_bigint_too(table, column):
    """A narrower child column than its parent would reject the very ids it references."""
    assert dict(SITE_TABLES[table].columns)[column].startswith("BIGINT")


def test_a_collision_fails_the_build_naming_the_table_and_both_keys(monkeypatch):
    """Two natural keys on one id would be rejected by the primary key at COPY time, in a
    message naming neither. This stops first, with both in hand."""
    real = build.neon_schema.stable_id
    monkeypatch.setattr(
        build.neon_schema,
        "stable_id",
        lambda table, key: 7 if table == "products" else real(table, key),
    )
    with pytest.raises(IdCollision) as error:
        build_site_tables(_fixture_payload())
    message = str(error.value)
    assert "products" in message
    assert "mid-product" in message and "zeta-product" in message


def test_a_collision_exits_the_publisher_with_1(monkeypatch, tmp_path, capsys):
    """A collision must not reach the COPY. `plan` renders the map group's CSVs, so the guard
    runs before anything connects — on a `--check` as well as on a publish."""
    import build.publish_neon as publisher

    monkeypatch.setattr(build.neon_schema, "stable_id", lambda table, key: 7)
    with pytest.raises(IdCollision):
        plan(site_dir=tmp_path / "site")

    monkeypatch.setattr(
        sys, "argv", ["publish_neon", "--check", "--site-dir", str(tmp_path / "cli")]
    )
    assert publisher.main() == 1
    assert "id collision" in capsys.readouterr().err


def test_the_ordinal_the_id_used_to_carry_kept_a_column_of_its_own():
    """`layers.id`, `categories.id`, `stages.id` and `long_tail_top.id` were positions, and
    three of those positions meant something. A hash carries none of it."""
    payload = load_payload()
    tables = build_site_tables(payload)
    assert [row["sort_order"] for row in tables["layers"]] == list(
        range(1, len(payload["layer_order"]) + 1)
    )
    assert [row["sort_order"] for row in tables["categories"]] == list(
        range(1, len(payload["order"]) + 1)
    )
    assert [row["slug"] for row in tables["categories"]] == list(payload["order"])
    assert [row["num"] for row in tables["stages"]] == sorted(row["num"] for row in tables["stages"])
    assert [row["sort_order"] for row in tables["long_tail_top"]] == list(
        range(1, len(tables["long_tail_top"]) + 1)
    )


def test_the_schema_version_records_the_id_change():
    """No migration tool: the swap rebuilds the schema, so `publish_runs.schema_version` is
    how a reader tells positional ids from hashed ones."""
    assert SCHEMA_VERSION >= 3


def test_categories_carry_a_slug_the_pdf_omitted():
    """Every deep link is by slug, and the id it sits beside is a hash rather than something
    a person can read."""
    assert "slug" in dict(SITE_TABLES["categories"].columns)


def test_the_foreign_keys_resolve_to_rows_that_exist():
    payload = load_payload()
    rows = {name: spec.rows(payload) for name, spec in SITE_TABLES.items()}
    product_id_set = {row["id"] for row in rows["products"]}
    category_id_set = {row["id"] for row in rows["categories"]}
    layer_id_set = {row["id"] for row in rows["layers"]}
    stage_id_set = {row["id"] for row in rows["stages"]}
    gap_id_set = {row["id"] for row in rows["gaps"]}
    org_slugs = {row["slug"] for row in rows["organizations"]}

    for row in rows["products"]:
        assert row["category"] in category_id_set
        assert row["org_slug"] in org_slugs
    for row in rows["categories"]:
        assert row["layer"] in layer_id_set
        assert row["stage"] in stage_id_set
    for table in ("openness", "adoption", "capability", "sources", "product_lineage"):
        for row in rows[table]:
            assert row["product_id"] in product_id_set
    for row in rows["gaps_categories"]:
        assert row["cat_id"] in category_id_set
        assert row["gap_id"] in gap_id_set


def test_a_product_with_no_org_fails_naming_the_product():
    """`products.org_slug` is NOT NULL and references `organizations`. Writing "" sent an
    empty string into COPY, which CSV reads as NULL, so the load died on a constraint naming
    the column — leaving whoever hit it to work out which of 615 products was missing an org.
    """
    payload = load_payload()
    victim = next(
        product
        for cid in payload["order"]
        for product in payload["categories"][cid]["products"]
    )
    slug = victim["slug"]
    saved = victim.get("org_slug")
    victim["org_slug"] = ""
    try:
        with pytest.raises(UnmappedValue) as error:
            SITE_TABLES["products"].rows(payload)
        assert slug in str(error.value)
        assert "org_slug" in str(error.value)
    finally:
        victim["org_slug"] = saved


def test_every_product_in_the_corpus_has_an_org():
    """The guard above only helps if the corpus is clean today; a red here is a data fix."""
    payload = load_payload()
    rows = SITE_TABLES["products"].rows(payload)
    assert all(row["org_slug"] for row in rows)


def test_each_axis_has_exactly_one_row_per_product():
    payload = load_payload()
    products = SITE_TABLES["products"].rows(payload)
    for axis in ("openness", "adoption", "capability"):
        rows = SITE_TABLES[axis].rows(payload)
        assert len(rows) == len(products)
        assert len({row["product_id"] for row in rows}) == len(products)


def test_the_gallery_tables_are_not_published_at_all():
    """They were created empty so the site's queries would compile, which was a hazard: the
    swap rebuilds the schema, so the first row an editor wrote would be deleted by the next
    push to main with nothing raising. A schema rebuilt from source holds only rows it
    produced. See "What the CMS owns" in build/neon_schema.py."""
    for name in ("gallery", "gallery_products", "gallery_gaps"):
        assert name not in SITE_TABLES
    for enum in ("health_status", "integration_type", "gap_type"):
        assert enum not in ENUMS


def test_the_long_tail_tables_are_filled_from_the_payload():
    payload = load_payload()
    assert len(SITE_TABLES["long_tail_top"].rows(payload)) == len(payload["long_tail"]["top"])
    assert len(SITE_TABLES["long_tail_counts"].rows(payload)) == len(
        payload["long_tail"]["counts"]
    )


def test_lineage_is_relational_and_carries_every_edge():
    payload = load_payload()
    rows = SITE_TABLES["product_lineage"].rows(payload)
    expected = sum(
        len(targets or [])
        for cid in payload["order"]
        for product in payload["categories"][cid]["products"]
        for targets in (product.get("lineage") or {}).values()
    )
    assert len(rows) == expected
    assert {row["relation"] for row in rows} <= set(ENUMS["lineage_relation"])


def test_aliases_carry_their_kind():
    payload = load_payload()
    rows = SITE_TABLES["aliases"].rows(payload)
    kinds = {row["kind"] for row in rows}
    assert kinds <= set(ENUMS["alias_kind"])
    assert len(rows) == sum(len(v) for v in payload["aliases"].values())


def test_the_amended_columns_are_all_present():
    """Carl's amendments to the PDF: per-axis dates, governing_release, basis_detail, the
    peer-relative pair, and the product freshness pair."""
    products = dict(SITE_TABLES["products"].columns)
    assert "freshness_date" in products and "freshness_basis" in products
    assert "last_verified" in dict(SITE_TABLES["openness"].columns)
    assert "governing_release" in dict(SITE_TABLES["openness"].columns)
    assert "last_verified" in dict(SITE_TABLES["adoption"].columns)
    capability = dict(SITE_TABLES["capability"].columns)
    for column in ("last_verified", "basis_detail", "relative_to", "relation"):
        assert column in capability


def test_an_array_column_is_written_as_a_postgres_array_literal():
    payload = load_payload()
    rows = SITE_TABLES["organizations"].rows(payload)
    assert all(row["github"].startswith("{") and row["github"].endswith("}") for row in rows)
    with_accounts = [row for row in rows if row["github"] != "{}"]
    assert with_accounts, "no organization declares a github account"
    assert with_accounts[0]["github"].startswith('{"http')


# --- the COPY payload -----------------------------------------------------------------

# A quoted CSV field holding both a newline and an escaped quote. Several real `strapline`
# and `note` values are shaped like this, and they are the rows a line-oriented or
# text-mode read would corrupt.
_AWKWARD = 'slug,note\nolmo-3,"a note with a ""quoted"" phrase\nand a second line"\n'


def test_the_copy_payload_is_the_file_byte_for_byte():
    path = _write_csv("awkward", _AWKWARD)
    chunks: list[bytes] = []
    written = stream_bytes(path, chunks.append)
    assert b"".join(chunks) == path.read_bytes()
    assert written == len(path.read_bytes())


@pytest.mark.parametrize("chunk_size", [1, 3, 7, 4096])
def test_a_chunk_boundary_may_fall_anywhere_including_inside_a_quoted_newline(chunk_size):
    """Postgres's CSV parser reassembles the stream, so the split point cannot matter.

    A chunked read that respected line boundaries would be a read that had to understand
    CSV quoting, which is the bug this guards.
    """
    path = _write_csv("awkward", _AWKWARD)
    chunks: list[bytes] = []
    stream_bytes(path, chunks.append, chunk_size=chunk_size)
    assert b"".join(chunks) == path.read_bytes()


def test_the_awkward_value_survives_a_full_csv_round_trip():
    """What Postgres will parse out of that payload, read back with the same dialect."""
    path = _write_csv("awkward", _AWKWARD)
    chunks: list[bytes] = []
    stream_bytes(path, chunks.append, chunk_size=5)
    import csv as _csv
    import io

    rows = list(_csv.reader(io.StringIO(b"".join(chunks).decode("utf-8"))))
    assert rows[0] == ["slug", "note"]
    assert rows[1] == ["olmo-3", 'a note with a "quoted" phrase\nand a second line']
    assert len(rows) == 2, "the embedded newline must not read as a row boundary"


def test_the_embedded_newline_is_not_counted_as_an_extra_row():
    plan_ = plan_table(
        _write_csv("awkward", _AWKWARD), declared=(("slug", "VARCHAR"), ("note", "TEXT"))
    )
    assert plan_.row_count == 1


# --- the read-back query --------------------------------------------------------------


def test_the_read_back_query_reaches_postgres_with_its_own_format_specifiers_intact():
    """`%I` is Postgres's, and psycopg claims `%` the moment parameters are passed.

    The first CI run of build/neon_status.py failed here: psycopg scanned the statement,
    found `%I`, and refused it before connecting. The schema is composed in as a literal
    instead, so there are no parameters and nothing scans the query.
    """
    from build.neon_status import counts_sql

    rendered = counts_sql("os-ai-map").as_string()
    assert "format('select count(*) as c from %I.%I', table_schema, table_name)" in rendered
    assert "%%" not in rendered, "a doubled specifier would reach format() as a literal %"
    assert "{schema}" not in rendered


def test_the_read_back_query_quotes_the_schema_it_filters_on():
    from build.neon_status import counts_sql

    rendered = counts_sql("os-ai-map").as_string()
    assert "WHERE table_schema = 'os-ai-map'" in rendered


def test_a_schema_name_carrying_a_quote_cannot_break_out_of_the_read_back_query():
    """`sql.Literal` escapes the value. This is not string interpolation into SQL."""
    from build.neon_status import counts_sql

    rendered = counts_sql("o'brien").as_string()
    assert "'o''brien'" in rendered


def test_the_runs_query_names_the_schema_and_the_run_table():
    from build.neon_status import RUNS_SQL

    rendered = RUNS_SQL.format(schema=quote_schema("os-ai-map"), table=f'"{RUN_TABLE}"')
    assert f'FROM "os-ai-map"."{RUN_TABLE}"' in rendered
    assert "%" not in rendered, "the runs query passes no parameters either"


def test_the_status_report_reads_back_every_column_the_run_record_writes():
    """A column added to RUN_COLUMNS and not to the report is a column nobody ever sees."""
    from build.neon_status import RUNS_SQL

    selected = RUNS_SQL.split("FROM")[0]
    for column, _type in RUN_COLUMNS:
        assert column in selected, f"{column} is written but never read back"


# --- reclaiming the previous schema ---------------------------------------------------


class _StubCursor:
    """Enough of a cursor to drive `reclaim_previous` without a database.

    Answers by inspecting the statement rather than by position, so a reordering of the
    function's queries does not silently change what the stub is answering.
    """

    def __init__(self, *, previous_exists: bool = True, dependents=()):
        self.previous_exists = previous_exists
        self.dependents = list(dependents)
        self.executed: list[tuple[str, object]] = []
        self._result: list[tuple] = []

    def execute(self, statement, params=None):
        text = str(statement)
        self.executed.append((text, params))
        if "information_schema.schemata" in text:
            self._result = [(1,)] if self.previous_exists else []
        elif "pg_depend" in text:
            self._result = list(self.dependents)
        else:
            self._result = []

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return list(self._result)

    @property
    def statements(self) -> list[str]:
        return [text for text, _params in self.executed]


def test_reclaiming_drops_the_previous_schema_when_nothing_outside_depends_on_it():
    cursor = _StubCursor(previous_exists=True, dependents=())
    assert reclaim_previous(cursor, DEFAULT_SCHEMA) is True
    assert any(
        f'DROP SCHEMA IF EXISTS "{DEFAULT_SCHEMA}_previous" CASCADE' in statement
        for statement in cursor.statements
    )


def test_reclaiming_is_a_no_op_when_there_is_no_previous_schema():
    """The first run, and any run after one that reclaimed cleanly."""
    cursor = _StubCursor(previous_exists=False)
    assert reclaim_previous(cursor, DEFAULT_SCHEMA) is False
    assert not any("DROP SCHEMA" in statement for statement in cursor.statements)


def test_an_external_dependent_fails_the_run_and_is_never_dropped():
    """CASCADE follows dependencies, not schema membership. A view in `payload` over one of
    our tables still depends on it after the rename, so a CASCADE would drop it — in its own
    schema, silently, on every publish. That is the accident PROTECTED_SCHEMAS exists to
    prevent, one indirection out."""
    cursor = _StubCursor(
        previous_exists=True,
        dependents=[
            ("payload", "gallery_view", "view or rule"),
            ("drizzle", "case_studies", "foreign key case_studies_product_fk"),
        ],
    )
    with pytest.raises(ExternalDependents) as error:
        reclaim_previous(cursor, DEFAULT_SCHEMA)
    message = str(error.value)
    assert "payload.gallery_view" in message
    assert "drizzle.case_studies" in message
    assert "view or rule" in message
    assert "foreign key case_studies_product_fk" in message
    assert not any("DROP SCHEMA" in statement for statement in cursor.statements)


def test_a_column_typed_by_one_of_our_enums_is_a_dependent_too():
    """The hazard here is not a table. The enum types are created in the staging schema so
    they travel with the rename, which means they travel into `_previous` — so a CMS column
    declared `os-ai-map.health_status` ends up typed by a type in `_previous`, and reclaiming
    would drop the type and take the column with it."""
    cursor = _StubCursor(
        previous_exists=True,
        dependents=[("payload", "case_studies.health", "column typed health_status")],
    )
    with pytest.raises(ExternalDependents) as error:
        reclaim_previous(cursor, DEFAULT_SCHEMA)
    message = str(error.value)
    assert "payload.case_studies.health" in message
    assert "column typed health_status" in message
    assert not any("DROP SCHEMA" in statement for statement in cursor.statements)


def test_the_dependency_check_covers_relations_and_types_and_skips_composite_types():
    """Three arms: views and rules, foreign keys, and columns typed by one of our enums.

    Composite types are excluded because every table has one, so including them would report
    each of our own tables as a dependent of itself.
    """
    cursor = _StubCursor(previous_exists=True)
    external_dependents(cursor, DEFAULT_SCHEMA)
    query, _params = cursor.executed[-1]
    assert "pg_rewrite" in query
    assert "pg_constraint" in query
    assert "pg_attribute" in query and "pg_type" in query
    assert "atttypid" in query
    assert "typtype <> 'c'" in query
    # A dropped column keeps its pg_attribute row and its atttypid.
    assert "attisdropped" in query


def test_the_dependency_check_asks_about_previous_and_exempts_only_our_own_schemas():
    cursor = _StubCursor(previous_exists=True)
    external_dependents(cursor, DEFAULT_SCHEMA)
    query, params = cursor.executed[-1]
    assert "pg_depend" in query and "pg_constraint" in query
    assert params["previous"] == f"{DEFAULT_SCHEMA}_previous"
    assert params["working"] == working_schemas(DEFAULT_SCHEMA)
    assert not set(params["working"]) & PROTECTED_SCHEMAS


def test_the_working_schemas_are_exactly_the_three_this_publisher_manages():
    assert working_schemas("gapmap") == ["gapmap", "gapmap_staging", "gapmap_previous"]


# --- the swap transaction, and its retry ----------------------------------------------


class _SqlstateError(Exception):
    def __init__(self, sqlstate: str):
        super().__init__(f"stub failure {sqlstate}")
        self.sqlstate = sqlstate


class _FakeConnection:
    """`transaction()` and `cursor()`, enough for `swap_in_place`."""

    def __init__(self, *, fail_times: int = 0, sqlstate: str = "55P03"):
        self.fail_times = fail_times
        self.sqlstate = sqlstate
        self.attempts = 0
        self.statements: list[str] = []

    def transaction(self):
        from contextlib import contextmanager

        @contextmanager
        def _transaction():
            self.attempts += 1
            if self.attempts <= self.fail_times:
                raise _SqlstateError(self.sqlstate)
            yield

        return _transaction()

    def cursor(self):
        from contextlib import contextmanager

        outer = self

        class _Cursor:
            def execute(self, statement, params=None):
                outer.statements.append(str(statement))

        @contextmanager
        def _cursor():
            yield _Cursor()

        return _cursor()


@pytest.mark.parametrize("sqlstate,expected", [("55P03", True), ("40P01", True), ("23505", False), (None, False)])
def test_only_a_lock_failure_is_worth_retrying(sqlstate, expected):
    """SQLSTATE, never the message: 55P03 is our own lock_timeout firing, 40P01 a deadlock.
    A constraint violation (23505) is the load telling us the data is wrong, and retrying it
    would just fail again more slowly."""
    assert is_retryable(_SqlstateError(sqlstate) if sqlstate else Exception("boom")) is expected


def test_the_swap_commits_on_the_first_attempt_when_the_lock_is_free():
    connection = _FakeConnection()
    slept: list[float] = []
    assert swap_in_place(connection, "gapmap", True, sleep=slept.append) == 1
    assert connection.statements == swap_sql("gapmap", live_exists=True)
    assert slept == []


def test_a_contended_swap_is_retried_with_backoff_and_then_commits():
    connection = _FakeConnection(fail_times=2)
    slept: list[float] = []
    assert swap_in_place(connection, "gapmap", True, sleep=slept.append) == 3
    assert slept == [1.0, 3.0]
    assert connection.statements == swap_sql("gapmap", live_exists=True)


def test_a_swap_that_never_gets_its_lock_raises_after_the_last_attempt():
    connection = _FakeConnection(fail_times=99)
    with pytest.raises(_SqlstateError):
        swap_in_place(connection, "gapmap", True, sleep=lambda _seconds: None)
    assert connection.attempts == SWAP_ATTEMPTS


def test_a_failure_that_is_not_about_locks_is_not_retried():
    connection = _FakeConnection(fail_times=99, sqlstate="23505")
    with pytest.raises(_SqlstateError):
        swap_in_place(connection, "gapmap", True, sleep=lambda _seconds: None)
    assert connection.attempts == 1, "a constraint violation must fail on the first attempt"


def test_a_lock_timeout_is_set_and_is_short():
    """Longer than a rename needs by orders of magnitude, short enough that a stalled
    cutover retries rather than parks."""
    assert LOCK_TIMEOUT.endswith("s")
    assert int(LOCK_TIMEOUT.rstrip("s")) <= 10


# --- the constraints the DBML declares ------------------------------------------------

# Transcribed from plans/neon-initial-schema.dbml (Laith, CLEVER FRANKE) plus Carl's
# amendments. Pinned rather than parsed: the DBML lives outside this repo, so a test that
# read it would pass locally and fail in CI. Gallery tables are absent on purpose — the CMS
# owns them.
_DBML_CONSTRAINTS: dict[str, set[str]] = {
    "layers": {'PRIMARY KEY ("id")'},
    "stages": {'PRIMARY KEY ("id")'},
    "gaps": {'PRIMARY KEY ("id")'},
    "categories": {
        'PRIMARY KEY ("id")',
        'UNIQUE ("slug")',
        'FOREIGN KEY ("layer") REFERENCES {schema}."layers" ("id")',
        'FOREIGN KEY ("stage") REFERENCES {schema}."stages" ("id")',
    },
    "gaps_categories": {
        'FOREIGN KEY ("cat_id") REFERENCES {schema}."categories" ("id")',
        'FOREIGN KEY ("gap_id") REFERENCES {schema}."gaps" ("id")',
    },
    "organizations": {'PRIMARY KEY ("slug")'},
    "products": {
        'PRIMARY KEY ("id")',
        'UNIQUE ("slug")',
        'FOREIGN KEY ("org_slug") REFERENCES {schema}."organizations" ("slug")',
        'FOREIGN KEY ("category") REFERENCES {schema}."categories" ("id")',
    },
    "openness": {
        'PRIMARY KEY ("product_id")',
        'FOREIGN KEY ("product_id") REFERENCES {schema}."products" ("id")',
    },
    "adoption": {
        'PRIMARY KEY ("product_id")',
        'FOREIGN KEY ("product_id") REFERENCES {schema}."products" ("id")',
    },
    "capability": {
        'PRIMARY KEY ("product_id")',
        'FOREIGN KEY ("product_id") REFERENCES {schema}."products" ("id")',
    },
    "sources": {
        'PRIMARY KEY ("id")',
        'FOREIGN KEY ("product_id") REFERENCES {schema}."products" ("id")',
    },
    "product_lineage": {
        'PRIMARY KEY ("id")',
        'FOREIGN KEY ("product_id") REFERENCES {schema}."products" ("id")',
    },
    "aliases": {'PRIMARY KEY ("alias")'},
    "long_tail_top": {'PRIMARY KEY ("id")'},
    "long_tail_counts": set(),
}

# Every `[not null]` in the DBML, plus categories.slug: the column is Carl's amendment and a
# nullable unique column admits any number of NULLs.
_DBML_NOT_NULL: tuple[tuple[str, str], ...] = (
    ("products", "slug"),
    ("products", "org_slug"),
    ("products", "category"),
    ("categories", "slug"),
    ("categories", "layer"),
    ("categories", "stage"),
    ("sources", "product_id"),
    ("sources", "metric_type"),
    ("product_lineage", "product_id"),
    ("gaps_categories", "cat_id"),
    ("gaps_categories", "gap_id"),
)


def test_the_map_group_is_exactly_the_dbmls_tables():
    assert set(SITE_TABLES) == set(_DBML_CONSTRAINTS)


@pytest.mark.parametrize("table", sorted(_DBML_CONSTRAINTS))
def test_every_constraint_the_dbml_declares_is_in_the_generated_ddl(table):
    """The database enforces the model, rather than the site discovering a dangling id at
    render time. A violation aborts the COPY, the staging schema is discarded and the live
    schema stays where it was, which is the point."""
    spec = SITE_TABLES[table]
    sql = create_table_sql("os-ai-map_staging", spec.columns, table, spec.constraints)
    for clause in _DBML_CONSTRAINTS[table]:
        assert clause.format(schema='"os-ai-map_staging"') in sql, f"{table}: missing {clause}"


@pytest.mark.parametrize("table,column", _DBML_NOT_NULL)
def test_every_not_null_the_dbml_declares_is_in_the_generated_ddl(table, column):
    spec = SITE_TABLES[table]
    sql = create_table_sql("os-ai-map_staging", spec.columns, table, spec.constraints)
    definition = dict(spec.columns)[column]
    assert "NOT NULL" in definition, f"{table}.{column} is nullable"
    assert f'"{column}"' in sql


def test_every_planned_table_is_one_the_schema_module_declares(tmp_path):
    """Neon serves the site's tables and nothing else. The registry surface lives in the
    warehouse as `currentai.registry.*` and in `build/registry/*.csv`.

    `site_dir` is a tmp path because `plan` renders the CSVs: writing them into the real
    `build/neon/` would race the `--check` subprocess test under `-n 4`, and the loser reads
    a half-written header.
    """
    plans, missing = plan(site_dir=tmp_path / "site")
    assert [plan_.name for plan_ in plans] == list(SITE_TABLES)
    assert missing == []
    for plan_ in plans:
        assert plan_.columns == SITE_TABLES[plan_.name].columns
        assert plan_.constraints == SITE_TABLES[plan_.name].constraints


def test_a_foreign_key_target_is_qualified_with_the_schema_being_built():
    """The staging schema is never on the search path, so an unqualified reference would
    resolve against whatever the live schema holds at the time."""
    spec = SITE_TABLES["products"]
    sql = create_table_sql("os-ai-map_staging", spec.columns, "products", spec.constraints)
    assert 'REFERENCES "os-ai-map_staging"."organizations"' in sql
    assert 'REFERENCES "organizations"' not in sql


def test_the_tables_are_ordered_parents_first_so_every_reference_resolves():
    """A FK can only be created after its target table exists, and the COPY into a child can
    only succeed after the parent's rows are in. Both follow from the declared order."""
    order = list(SITE_TABLES)
    for position, (name, spec) in enumerate(SITE_TABLES.items()):
        for clause in spec.constraints:
            for referent in re.findall(r'REFERENCES \{schema\}\."([^"]+)"', clause):
                assert referent in order, f"{name} references unknown table {referent}"
                assert order.index(referent) <= position, (
                    f"{name} references {referent}, which is created later"
                )


def test_the_constraint_tally_the_read_back_reports_is_the_one_the_ddl_asks_for():
    """The read-back counts what `information_schema` holds, so the two numbers agreeing is
    what proves the swap created the constraints rather than merely being asked to."""
    from build.neon_status import constraints_sql

    rendered = constraints_sql("os-ai-map").as_string()
    assert "information_schema.table_constraints" in rendered
    assert "constraint_schema = 'os-ai-map'" in rendered
    # Postgres materializes a CHECK per NOT NULL column, which would swamp the tally with
    # something the column list already shows.
    assert "constraint_type <> 'CHECK'" in rendered


# --- helpers --------------------------------------------------------------------------

_TMP: dict[str, Path] = {}


def _write_csv(name: str, text: str) -> Path:
    import tempfile

    directory = _TMP.setdefault("dir", Path(tempfile.mkdtemp()))
    path = directory / f"{name}.csv"
    path.write_text(text, encoding="utf-8")
    return path


_DECLARED = (("slug", "VARCHAR"), ("label", "VARCHAR"))


def test_plan_table_reads_the_header_and_counts_data_rows_only():
    plan = plan_table(_write_csv("categories", "slug,label\na,A\nb,B\n"), declared=_DECLARED)
    assert plan.name == "categories"
    assert plan.row_count == 2
    assert plan.columns == _DECLARED


def test_a_header_only_csv_plans_as_a_real_table_with_no_rows():
    """An empty table is loaded as an empty table: a serving layer that answers "no rows" is
    better than one that answers "no such table"."""
    plan = plan_table(_write_csv("empty", "slug,label\n"), declared=_DECLARED)
    assert plan.row_count == 0
    assert plan.columns == _DECLARED


def test_a_header_that_has_drifted_from_the_declared_columns_is_refused():
    """A spec that no longer describes its CSV would COPY values into the wrong columns,
    which Postgres accepts wherever the types happen to line up."""
    with pytest.raises(ValueError, match="does not match the declared columns"):
        plan_table(_write_csv("drifted", "slug,name\na,A\n"), declared=_DECLARED)
