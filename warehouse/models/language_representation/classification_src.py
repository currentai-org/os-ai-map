# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""language_representation.classification_src: method version 1 (os-ai-map docs/reference/language-classification.md).

The source half of the classification table. Python models write flat columns only, so related_to,
flags and provenance are written here as JSON text; the SQL model
currentai.language_representation.classification casts them to the spec's types and is the contract.
This model reads the measurements contract table, so it consumes the contract it is specified against.

One row per ISO 639-3 code in scope: the digital representation class and the resource profile,
each computed at both ends of every interval, from the rows of
currentai.language_representation.measurements. Overrides are read as measurement rows
(relation 'override') and replace the default rows of the same (code, measure, source).
"""

import csv
import json
import datetime as dt
import io
import re
import zipfile

import oso
import polars as pl

METHOD_VERSION = "1.0.0"
USER_AGENT = "gapmap-language-representation/1.0 (+https://github.com/currentai-org/os-ai-map)"

# The classification table's scope: ISO 639-3 scope values kept (I individual, M macrolanguage).
# Change it here, and only here, if SIL's terms require a narrower table.
SCOPE_VALUES = ["I", "M"]

ISO_ZIP_URL = "https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3_Code_Tables_20261015.zip"
MEASUREMENTS_TABLE = '"currentai"."language_representation"."measurements"'

BANDS = "ABCD"
CLASS_OF_BAND = {"A": "high", "B": "mid", "C": "low", "D": "very_low"}
# Band edges, method version 1 (Parameters). Values at or above the first edge are A, and so on.
FINEWEB2_EDGES = [60e9, 4e9, 3e8]  # words with the Bible share removed
CLD2_EDGES = [1.0, 0.1, 0.01]  # percent of pages
WIKIPEDIA_EDGES = [1e6, 1e5, 1e4]  # content articles
WIDENING_GAP = 2
MANY_SPEAKERS = 1_000_000
ENDANGERMENT_BOUND = 999_999  # speakers below 1,000,000
SMALL_POPULATION_AES = {"moribund", "nearly extinct", "extinct"}
CORROBORATION_WIKIPEDIA = 1e5
CORROBORATION_OPEN_LIBRARY = 1e4
STATUS_NAMES = {2: "national", 1: "subnational", 0: "none"}
# ISO 639-3 Language_Type → flags. Historical (H) and ancient (A) read as historical.
TYPE_FLAGS = {"H": "historical", "A": "historical", "E": "extinct", "C": "constructed"}
# Related standards that stay separate rows (Code levels and macrolanguages).
RELATED_TO = {"fil": ["tgl"], "tgl": ["fil"], "nqo": ["man"], "man": ["nqo"]}


def band(value: float, edges: list[float]) -> int:
    for i, edge in enumerate(edges):
        if value >= edge:
            return i
    return 3


def row_interval(r: dict, edges: list[float]) -> tuple[int, int] | None:
    """(best, worst) band indices for one witness row, or None when it carries no interval."""
    if r["state"] == "measured":
        b = band(r["value_low"], edges)
        return (b, b)
    if r["state"] == "bounded":
        best = 0 if r["value_high"] is None else band(r["value_high"], edges)
        worst = band(r["value_low"], edges) if r["value_low"] else 3
        return (best, worst)
    if r["state"] == "observed_absent":
        return (3, 3)
    return None


def gap(a: tuple[int, int], b: tuple[int, int]) -> int:
    if a[1] < b[0]:
        return b[0] - a[1]
    if b[1] < a[0]:
        return a[0] - b[1]
    return 0


def verdict(low_yes: bool, high_yes: bool) -> str:
    if low_yes and high_yes:
        return "yes"
    if not low_yes and not high_yes:
        return "no"
    return "unresolved"


def and3(a: str, b: str) -> str:
    """Three-valued AND: no if either side is no, yes if both are yes, else unresolved."""
    if a == "no" or b == "no":
        return "no"
    if a == "yes" and b == "yes":
        return "yes"
    return "unresolved"


def or3(a: str, b: str) -> str:
    """Three-valued OR: yes if either side is yes, no if both are no, else unresolved."""
    if a == "yes" or b == "yes":
        return "yes"
    if a == "no" and b == "no":
        return "no"
    return "unresolved"


def threshold_route(rows: list[dict], measure: str, threshold: float, absent_states: tuple[str, ...]) -> str:
    """yes/no/unresolved for 'some row of the measure is at or above the threshold'.

    measured rows decide at their value; bounded rows decide only when the whole interval lies on one side;
    rows in absent_states read as no; any other state (unmeasured) leaves the route unresolved.
    """
    out = "no"
    seen = False
    for r in rows:
        if r["measure"] != measure:
            continue
        seen = True
        if r["state"] == "measured":
            v = "yes" if r["value_low"] >= threshold else "no"
        elif r["state"] == "bounded":
            lo, hi = r["value_low"] or 0.0, r["value_high"]
            v = "yes" if lo >= threshold else ("no" if hi is not None and hi < threshold else "unresolved")
        elif r["state"] in absent_states:
            v = "no"
        else:
            v = "unresolved"
        out = or3(out, v)
    return out if seen else "unresolved"


def label_name(label: str) -> str:
    return label.split(":", 1)[1] if ":" in label else label


def fmt_count(v: float) -> str:
    return str(int(round(v)))


def iso_tables(body: bytes) -> tuple[dict[str, dict[str, str]], dict[str, str], str]:
    z = zipfile.ZipFile(io.BytesIO(body))
    names = z.namelist()
    main = [n for n in names if n.endswith("/iso-639-3.tab")][0]
    macro = [n for n in names if n.endswith("/iso-639-3-macrolanguages.tab")][0]
    m = re.search(r"Code_Tables_(\d{8})", main)
    if m is None:
        raise RuntimeError(f"no release date in {main}")
    release = m.group(1)
    codes = {r["Id"]: r for r in csv.DictReader(io.StringIO(z.read(main).decode("utf-8-sig")), delimiter="\t")}
    member_of: dict[str, str] = {}
    for r in csv.DictReader(io.StringIO(z.read(macro).decode("utf-8-sig")), delimiter="\t"):
        if r["I_Status"] == "A":
            member_of[r["I_Id"]] = r["M_Id"]
    return codes, member_of, release


def written(rows: list[dict]) -> tuple[tuple[int, int] | None, str, bool]:
    """Written-material interval from web text, widened by an eligible Wikipedia edition."""
    witnesses = [(r, row_interval(r, FINEWEB2_EDGES if r["measure"] == "web_text_words" else CLD2_EDGES))
                 for r in rows if r["measure"] in ("web_text_words", "web_page_share")]
    points = [iv for r, iv in witnesses if iv and r["state"] == "measured"]
    bounds = [iv for r, iv in witnesses if iv and r["state"] == "bounded"]
    if points:
        best, worst = min(p[0] for p in points), max(p[1] for p in points)
        for b in bounds:  # a bound the measured core lies outside widens it to the bound's nearest end
            if worst < b[0]:
                worst = b[0]
            if best > b[1]:
                best = b[1]
        web: tuple[int, int] | None = (best, worst)
        state = "measured"
    elif bounds:
        web = (min(b[0] for b in bounds), max(b[1] for b in bounds))
        state = "bounded"
    else:
        states = {r["state"] for r, _ in witnesses}
        return None, ("not_detected" if "not_detected" in states else "unmeasured"), False
    # Wikipedia widens only from an eligible edition (state measured or bounded; ineligible is excluded).
    widened = False
    for r in rows:
        if r["measure"] == "wikipedia_articles" and r["state"] in ("measured", "bounded"):
            wi = row_interval(r, WIKIPEDIA_EDGES)
            if wi is not None and gap(web, wi) >= WIDENING_GAP:
                web = (min(web[0], wi[0]), max(web[1], wi[1]))
                widened = True
    return web, state, widened


def speakers(rows: list[dict], historical: bool) -> tuple[int | None, int | None, str, str]:
    points: list[float] = []
    lower: list[float] = []
    upper: list[float] = []
    for r in rows:
        if r["measure"] != "speakers":
            continue
        if r["state"] == "measured":
            points.append(r["value_low"])
        elif r["state"] == "bounded":
            if r["value_low"] is not None and r["value_low"] > 0:
                lower.append(r["value_low"])
            if r["value_high"] is not None:
                upper.append(r["value_high"])
    aes_bound = any(r["measure"] == "endangerment" and r["state"] == "measured"
                    and label_name(r["source_label"]) in SMALL_POPULATION_AES for r in rows)
    if aes_bound:
        upper.append(ENDANGERMENT_BOUND)
    if points:
        lo: float | None = min(points)
        hi: float | None = max(points)
        state = "measured"
        for u in upper:
            if lo > u:
                lo = u
                state = "bound_from_endangerment" if u == ENDANGERMENT_BOUND and aes_bound else "bounded"
        for lb in lower:
            if hi < lb:
                hi = lb
                state = "bounded"
    elif lower or upper:
        lo = max(lower) if lower else None
        hi = min(upper) if upper else None
        state = "bound_from_endangerment" if aes_bound and hi == ENDANGERMENT_BOUND else "bounded"
    else:
        lo, hi = None, None
        states = {r["state"] for r in rows if r["measure"] == "speakers"}
        state = "excluded" if states == {"excluded"} else "unmeasured"
    if historical:
        many = "no"
    else:
        many = verdict((lo or 0) >= MANY_SPEAKERS, hi is None or hi >= MANY_SPEAKERS)
    return (None if lo is None else int(round(lo))), (None if hi is None else int(round(hi))), state, many


def official_status(rows: list[dict]) -> tuple[int, int, str, str]:
    """(best, worst, state, recognized), status levels national 2 > subnational 1 > none 0."""
    sr = [r for r in rows if r["measure"] == "official_status"]
    measured = [int(r["value_low"]) for r in sr if r["state"] == "measured"]
    bounded = [r for r in sr if r["state"] == "bounded"]
    state_level = any(r["state"] == "excluded" and r["source"] == "wikidata" for r in sr)
    cldr_listed = any(r["source"] == "cldr" and r["state"] == "measured" for r in sr)
    if measured:
        best = worst = max(measured)
        state = "measured"
    elif bounded:
        best = max(int(r["value_high"]) for r in bounded)
        worst = min(int(r["value_low"] or 0) for r in bounded)
        state = "bounded"
    elif any(r["state"] == "not_listed" for r in sr):
        not_listed = [r for r in sr if r["state"] == "not_listed"][0]
        best, worst = int(not_listed["value_high"]), int(not_listed["value_low"])
        state = "not_listed"
    else:
        best, worst, state = 2, 0, "unmeasured"
    recognized = "yes" if state_level and not cldr_listed else ("no" if cldr_listed else "unknown")
    return best, worst, state, recognized


def context_value(rows: list[dict], measure: str, as_label: bool) -> str:
    for r in rows:
        if r["measure"] != measure:
            continue
        if r["state"] == "measured":
            return label_name(r["source_label"]) if as_label else fmt_count(r["value_low"])
        if r["state"] == "bounded" and not as_label:
            lo = fmt_count(r["value_low"] or 0)
            return f"{lo}..{fmt_count(r['value_high'])}" if r["value_high"] is not None else f">={lo}"
    return "unknown"


def apply_overrides(rows: list[dict]) -> list[dict]:
    keys = {(r["measure"], r["source"]) for r in rows if r["relation"] == "override"}
    return [r for r in rows if (r["measure"], r["source"]) not in keys or r["relation"] == "override"]


def classify(meas: pl.DataFrame, iso_body: bytes, computed_at: dt.datetime) -> pl.DataFrame:
    codes, member_of, release = iso_tables(iso_body)
    scope = sorted(c for c, r in codes.items() if r["Scope"] in SCOPE_VALUES)
    by_code: dict[str, list[dict]] = {}
    for r in meas.iter_rows(named=True):
        by_code.setdefault(r["iso639_3"], []).append(r)
    out: list[dict] = []
    for c in scope:
        rows = apply_overrides(by_code.get(c, []))
        info = codes[c]
        flags = []
        if TYPE_FLAGS.get(info["Language_Type"]):
            flags.append(TYPE_FLAGS[info["Language_Type"]])
        if info["Scope"] == "M":
            flags.append("macrolanguage")
        historical = info["Language_Type"] in ("H", "A", "E")

        web, w_state, _ = written(rows)
        if web is None:
            w_best, w_worst = "A", "D"
            cls, cls_best, cls_worst = "unknown", "unknown", "unknown"
            web_route = "unresolved"
        else:
            w_best, w_worst = BANDS[web[0]], BANDS[web[1]]
            cls_best, cls_worst = CLASS_OF_BAND[w_best], CLASS_OF_BAND[w_worst]
            cls = cls_best if cls_best == cls_worst else "unresolved"
            web_route = verdict(web[1] <= 1, web[0] <= 1)
        # Interval rule (R-2026-11-10-h), three-valued: large = web OR (Wikipedia AND Open Library).
        # Wikipedia: an eligible edition >= 100k content articles; observed_absent and excluded (ineligible) read as no.
        # Open Library: >= 10k works; unmeasured leaves the route unresolved, never no.
        wp_route = threshold_route(rows, "wikipedia_articles", CORROBORATION_WIKIPEDIA, ("observed_absent", "excluded"))
        ol_route = threshold_route(rows, "open_library_works", CORROBORATION_OPEN_LIBRARY, ())
        large = or3(web_route, and3(wp_route, ol_route))

        s_best, s_worst, s_state, recognized = official_status(rows)
        official = verdict(s_worst >= 1, s_best >= 1)
        sp_lo, sp_hi, sp_state, many = speakers(rows, historical)

        prov = sorted({(r["measure"], r["source"], r["source_version"], r["retrieved_at"], r["content_sha256"])
                       for r in rows})
        out.append({
            "iso639_3": c,
            "macrolanguage": member_of.get(c),
            "related_to": json.dumps(RELATED_TO.get(c, [])),
            "flags": json.dumps(flags),
            "written_best": w_best,
            "written_worst": w_worst,
            "written_state": w_state,
            "representation_class": cls,
            "representation_class_best": cls_best,
            "representation_class_worst": cls_worst,
            "status_best": STATUS_NAMES[s_best],
            "status_worst": STATUS_NAMES[s_worst],
            "status_state": s_state,
            "recognized": recognized,
            "speakers_low": sp_lo,
            "speakers_high": sp_hi,
            "speakers_state": sp_state,
            "official": official,
            "many_speakers": many,
            "large_written_material": large,
            "scholarly_works": context_value(rows, "scholarly_works", False),
            "endangerment": context_value(rows, "endangerment", True),
            "descriptive_status": context_value(rows, "descriptive_status", True),
            "provenance": json.dumps([{"measure": p[0], "source": p[1], "source_version": p[2],
                                       "retrieved_at": p[3].strftime("%Y-%m-%d %H:%M:%S.%f"),
                                       "content_sha256": p[4]} for p in prov]),
            "code_table_version": release,
            "method_version": METHOD_VERSION,
            "computed_at": computed_at,
        })
    schema = {
        "iso639_3": pl.Utf8, "macrolanguage": pl.Utf8, "related_to": pl.Utf8, "flags": pl.Utf8,
        "written_best": pl.Utf8, "written_worst": pl.Utf8, "written_state": pl.Utf8,
        "representation_class": pl.Utf8, "representation_class_best": pl.Utf8,
        "representation_class_worst": pl.Utf8, "status_best": pl.Utf8, "status_worst": pl.Utf8,
        "status_state": pl.Utf8, "recognized": pl.Utf8, "speakers_low": pl.Int64, "speakers_high": pl.Int64,
        "speakers_state": pl.Utf8, "official": pl.Utf8, "many_speakers": pl.Utf8,
        "large_written_material": pl.Utf8, "scholarly_works": pl.Utf8, "endangerment": pl.Utf8,
        "descriptive_status": pl.Utf8, "provenance": pl.Utf8, "code_table_version": pl.Utf8,
        "method_version": pl.Utf8, "computed_at": pl.Datetime("us"),
    }
    return pl.DataFrame(out, schema=schema)


@oso.model(
    depends_on=[
        oso.Dependency(
            table="currentai.language_representation.measurements",
            columns=[
                oso.Column(name="iso639_3", type="varchar"),
                oso.Column(name="measure", type="varchar"),
                oso.Column(name="source", type="varchar"),
                oso.Column(name="source_version", type="varchar"),
                oso.Column(name="source_label", type="varchar"),
                oso.Column(name="value_low", type="double"),
                oso.Column(name="value_high", type="double"),
                oso.Column(name="state", type="varchar"),
                oso.Column(name="relation", type="varchar"),
                oso.Column(name="retrieved_at", type="timestamp(6)"),
                oso.Column(name="content_sha256", type="varchar"),
            ],
        ),
    ],
    external_origins=["https://iso639-3.sil.org"],
    capabilities=oso.Capabilities(fetch=True),
    columns=[
        oso.Column(name="iso639_3", type="varchar"),
        oso.Column(name="macrolanguage", type="varchar"),
        oso.Column(name="related_to", type="varchar"),
        oso.Column(name="flags", type="varchar"),
        oso.Column(name="written_best", type="varchar"),
        oso.Column(name="written_worst", type="varchar"),
        oso.Column(name="written_state", type="varchar"),
        oso.Column(name="representation_class", type="varchar"),
        oso.Column(name="representation_class_best", type="varchar"),
        oso.Column(name="representation_class_worst", type="varchar"),
        oso.Column(name="status_best", type="varchar"),
        oso.Column(name="status_worst", type="varchar"),
        oso.Column(name="status_state", type="varchar"),
        oso.Column(name="recognized", type="varchar"),
        oso.Column(name="speakers_low", type="bigint"),
        oso.Column(name="speakers_high", type="bigint"),
        oso.Column(name="speakers_state", type="varchar"),
        oso.Column(name="official", type="varchar"),
        oso.Column(name="many_speakers", type="varchar"),
        oso.Column(name="large_written_material", type="varchar"),
        oso.Column(name="scholarly_works", type="varchar"),
        oso.Column(name="endangerment", type="varchar"),
        oso.Column(name="descriptive_status", type="varchar"),
        oso.Column(name="provenance", type="varchar"),
        oso.Column(name="code_table_version", type="varchar"),
        oso.Column(name="method_version", type="varchar"),
        oso.Column(name="computed_at", type="timestamp(6)"),
    ],
)
async def classification_src(context: oso.AsyncContext) -> oso.DataFrame:
    q = await context.query(
        "SELECT iso639_3, measure, source, source_version, source_label, value_low, value_high, state, relation, "
        f"retrieved_at, content_sha256 FROM {MEASUREMENTS_TABLE}"
    )
    meas = await q.as_pl()
    if meas.height == 0:
        raise RuntimeError("measurements is empty")
    chunks: list[bytes] = []
    async with context.stream(ISO_ZIP_URL, headers={"User-Agent": USER_AGENT}, timeout=120.0) as res:
        if res.status != 200:
            raise RuntimeError(f"{ISO_ZIP_URL} returned HTTP {res.status}")
        async for chunk in res.aiter_bytes():
            chunks.append(chunk)
    computed_at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None, microsecond=0)
    return classify(meas, b"".join(chunks), computed_at)
