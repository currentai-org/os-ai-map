# ────── PLATFORM MIRROR (read-only) ──────
# A snapshot of a model that runs on the OSO platform to build one of the gap map's
# tables. The platform is the source of truth; nothing deploys from this copy, and
# editing it here changes nothing. See README.md and manifest.yaml in this folder.

"""language_representation.measurements_src: every observation behind the language classification.

The source half of the measurements table. Python models write flat columns only, so
label_population is written here as a JSON array in text; the SQL model
currentai.language_representation.measurements casts it to array(varchar) and is the contract.

Method version 1 (os-ai-map docs/reference/language-classification.md, PR #995, rulings
R-2026-11-10-a to -q). One row per (iso639_3, measure, source, source_version, source_label),
each with its value state and declared mapping. Every source is fetched here at run time and
pinned where the source allows. No verdict is computed in this model.
"""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import hashlib
import io
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from types import SimpleNamespace
from collections.abc import AsyncIterator
from typing import Any

import oso
import polars as pl

USER_AGENT = "gapmap-language-representation/1.0 (+https://github.com/currentai-org/os-ai-map)"

ISO_RELEASE = "20261015"
ISO_ZIP_URL = "https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3_Code_Tables_20261015.zip"
# Every language code is measured; the special codes (scope S: mis, mul, und, zxx) name no language.
# The classification table's scope is set by SCOPE_VALUES in classification_src.

CLDR_VERSION = "release-49"
CLDR_URL = "https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/supplemental/supplementalData.xml"
# CLDR 49 references whose notes describe an estimate made without a count. Entries citing them
# are dropped from the speaker figure (state excluded). Reviewed against the reference texts of
# release-49; re-review when CLDR_VERSION changes.
CLDR_PLACEHOLDER_REFS = ["R1028", "R1047", "R1086", "R1088", "R1118", "R1148", "R1149", "R1150",
                         "R1151", "R1236", "R1250", "R1265", "R1284", "R1286", "R1291", "R1302", "R1303"]

GLOTTOLOG_VERSION = "v5.3"
GLOTTOLOG_LANGUAGES_URL = "https://raw.githubusercontent.com/glottolog/glottolog-cldf/v5.3/cldf/languages.csv"
GLOTTOLOG_VALUES_URL = "https://raw.githubusercontent.com/glottolog/glottolog-cldf/v5.3/cldf/values.csv"
GLOTTOLOG_CODES_URL = "https://raw.githubusercontent.com/glottolog/glottolog-cldf/v5.3/cldf/codes.csv"
# Families whose entries carry no information about a speaker community.
GLOTTOLOG_EXCLUDED_FAMILIES = {"book1242": "Bookkeeping", "arti1236": "Artificial Language"}

FINEWEB2_COMMIT = "d0defb24f193bb9a5a11b8b14524a03c4858e1b6"
FINEWEB2_URL = "https://raw.githubusercontent.com/huggingface/fineweb-2/d0defb24f193bb9a5a11b8b14524a03c4858e1b6/fineweb2-language-distribution.csv"
GLOTLID_COMMIT = "0e82c619af770914e805fdfa9e987404c2505b1c"
GLOTLID_URL = "https://raw.githubusercontent.com/cisnlp/GlotLID/0e82c619af770914e805fdfa9e987404c2505b1c/languages-v3.md"

CC_URL = "https://commoncrawl.github.io/cc-crawl-statistics/plots/languages.csv"
WIKIDATA_URL = "https://query.wikidata.org/sparql"
SITEMATRIX_URL = "https://meta.wikimedia.org/w/api.php?action=sitematrix&format=json&smtype=language&smlangprop=code%7Csite&smsiteprop=url%7Cdbname%7Ccode"
OPENALEX_URL = "https://api.openalex.org/works?group_by=language&per_page=200"
# Open Library: one count per MARC language code (ISO 639-2/B, the ISO 639-3 table's Part2b column).
OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json?q=language:{marc}&limit=0&fields=key"
OPEN_LIBRARY_CONCURRENCY = 3
OPEN_LIBRARY_PAUSE = 1.0  # seconds each worker waits after a request: at most 3 requests per second
OPEN_LIBRARY_TRIES = 4

# Wikipedia edition prefixes that add to another code, or that measure no single ISO 639-3 code.
WIKI_COMPOSITE = {"be-tarask": "bel", "nds-nl": "nds", "cbk-zam": "cbk"}
WIKI_UNMAPPED = {"simple": "Simple English, a register of eng", "bh": "Bihari, a collective code",
                 "eml": "Emilian-Romagnol, retired ISO code split into egl and rgn",
                 "map-bms": "Banyumasan, a dialect of jav", "nah": "Nahuatl, a collective code",
                 "roa-tara": "Tarantino, a dialect of nap",
                 "nrm": "Norman; ISO 639-3 nrm is Narom, an unrelated language"}

# Related standards: label filed under one code that is broader for the other (spec: no count shared).
# (source, label code, covered code, basis)
RELATED_FILINGS = [
    ("fineweb-2", "fil", "tgl", "GlotLID v3 renamed tgl_Latn to fil_Latn, so the fil label holds Tagalog text (languages-v3.md)"),
    ("commoncrawl-cld2", "tgl", "fil", "CLD2 has one Tagalog label; Filipino text is filed under it"),
    ("wikipedia", "tgl", "fil", "The tl edition is the Tagalog/Filipino Wikipedia; no edition is coded fil"),
]
# Wikidata P1098 statements declared to measure a broader population than the item's code.
WIKIDATA_SPEAKER_BROADER = {"nqo": "The N'Ko item carries the Manding speaker count; N'Ko is a written standard of Manding (man)"}
OVERRIDES = []  # rows shaped like the output; each must carry relation 'override' and a ruling id

L1 = "http://www.wikidata.org/entity/Q36870"
L2 = "http://www.wikidata.org/entity/Q125421"

SPARQL_SPEAKERS = """SELECT ?iso ?item ?amount ?date ?part ?place ?rank WHERE {
  ?item wdt:P220 ?iso ; p:P1098 ?st .
  ?st psv:P1098/wikibase:quantityAmount ?amount ; wikibase:rank ?rank .
  FILTER(?rank != wikibase:DeprecatedRank)
  OPTIONAL { ?st pq:P585 ?date }
  OPTIONAL { ?st pq:P518 ?part }
  OPTIONAL { ?st pq:P17 ?place }
}"""
SPARQL_OFFICIAL = """SELECT ?iso ?ent ?kind WHERE {
  ?lang wdt:P220 ?iso .
  ?ent p:P37 ?st . ?st ps:P37 ?lang .
  FILTER NOT EXISTS { ?st pq:P582 ?end }
  FILTER NOT EXISTS { ?ent wdt:P576 ?dis }
  { ?ent wdt:P31 wd:Q3624078 . BIND("sovereign_state" AS ?kind) }
  UNION
  { ?ent wdt:P31/wdt:P279* wd:Q10864048 . BIND("adm1" AS ?kind) }
}"""


def Src(source: str, version: str, url: str, body: bytes, at: dt.datetime) -> SimpleNamespace:
    """One read: what was fetched, when, and its digest."""
    return SimpleNamespace(source=source, version=version, url=url, body=body, at=at,
                           sha=hashlib.sha256(body).hexdigest())


async def fetch_bytes(context: oso.AsyncContext, url: str, method: str = "GET",
                      body: str | None = None, extra: dict[str, str] | None = None,
                      timeout: float = 120.0, tries: int = 6) -> tuple[bytes, dt.datetime, int]:
    headers = {"User-Agent": USER_AGENT}
    if extra:
        headers.update(extra)
    last = ""
    for attempt in range(tries):
        try:
            async with context.stream(url, method=method, headers=headers, body=body, timeout=timeout) as res:
                if res.status in (429, 500, 502, 503, 504):
                    retry = res.headers.get("retry-after") or res.headers.get("Retry-After") or ""
                    wait = float(retry) if retry.isdigit() else 2.0 * (2 ** attempt)
                    last = f"HTTP {res.status}"
                    await asyncio.sleep(min(wait, 60.0))
                    continue
                chunks = []
                async for chunk in res.aiter_bytes():
                    chunks.append(chunk)
                return b"".join(chunks), dt.datetime.now(dt.timezone.utc).replace(tzinfo=None), res.status
        except Exception as exc:  # transport error or timeout: retry
            last = repr(exc)
            await asyncio.sleep(2.0 * (2 ** attempt))
    raise RuntimeError(f"fetch failed after {tries} tries: {url}: {last}")


async def read_source(context: oso.AsyncContext, source: str, version: str, url: str, **kw) -> SimpleNamespace:
    body, at, status = await fetch_bytes(context, url, **kw)
    if status != 200:
        raise RuntimeError(f"{url} returned HTTP {status}")
    return Src(source, version, url, body, at)


async def open_library_count(context: oso.AsyncContext, marc: str) -> SimpleNamespace:
    """One Open Library search count. count is None unless the search answered HTTP 200 with a count."""
    url = OPEN_LIBRARY_SEARCH.format(marc=marc)
    status, note, body, wait = 0, "", b"", 0.0
    for attempt in range(OPEN_LIBRARY_TRIES):
        try:
            async with context.stream(url, headers={"User-Agent": USER_AGENT}, timeout=30.0) as res:
                status = res.status
                chunks = []
                async for chunk in res.aiter_bytes():
                    chunks.append(chunk)
                body = b"".join(chunks)
                if status == 200:
                    break
                note = f"HTTP {status}"
                retry = res.headers.get("retry-after") or res.headers.get("Retry-After") or ""
                if status not in (429, 500, 502, 503, 504):
                    break
                wait = float(retry) if retry.isdigit() else 2.0 * (2 ** attempt)
        except Exception as exc:  # transport error or timeout: retry
            status, note = 0, f"transport error: {type(exc).__name__}"
            wait = 2.0 * (2 ** attempt)
        if attempt + 1 < OPEN_LIBRARY_TRIES:
            await asyncio.sleep(min(wait, 60.0))
    at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    count: float | None = None
    if status == 200:
        try:
            n = json.loads(body.decode("utf-8")).get("numFound")
            if isinstance(n, int) and not isinstance(n, bool):
                count = float(n)
                note = f"HTTP 200, numFound {n}"
            else:
                note = "HTTP 200 without numFound"
        except Exception:
            note = "HTTP 200 with a body that is not JSON"
    elif status:
        note = f"{note} after {OPEN_LIBRARY_TRIES} tries"
    else:
        note = f"{note or 'no response'} after {OPEN_LIBRARY_TRIES} tries"
    return SimpleNamespace(marc=marc, url=url, count=count, status=status, note=note, at=at,
                           sha=hashlib.sha256(body).hexdigest())


def iso_tables(src: SimpleNamespace) -> tuple[dict[str, dict[str, str]], dict[str, list[str]], str]:
    z = zipfile.ZipFile(io.BytesIO(src.body))
    names = z.namelist()
    main = [n for n in names if n.endswith("/iso-639-3.tab")][0]
    macro = [n for n in names if n.endswith("/iso-639-3-macrolanguages.tab")][0]
    m = re.search(r"Code_Tables_(\d{8})", main)
    release = m.group(1) if m else ISO_RELEASE
    rows = list(csv.DictReader(io.StringIO(z.read(main).decode("utf-8-sig")), delimiter="\t"))
    codes = {r["Id"]: r for r in rows}
    members: dict[str, list[str]] = {}
    for r in csv.DictReader(io.StringIO(z.read(macro).decode("utf-8-sig")), delimiter="\t"):
        if r["I_Status"] == "A":
            members.setdefault(r["M_Id"], []).append(r["I_Id"])
    return codes, members, release


def run_model(srcs: dict[str, SimpleNamespace], wiki: dict[str, tuple[SimpleNamespace, dict]],
              ol: dict[str, SimpleNamespace], run_at: dt.datetime, open_library: bool) -> pl.DataFrame:
    """Rows of every measure but open_library_works (open_library=False), or of that measure alone."""
    codes, members, release = iso_tables(srcs["iso"])
    scope = sorted(c for c, r in codes.items() if r["Scope"] != "S")
    in_scope = set(scope)
    member_of = {m: M for M, ms in members.items() for m in ms}
    part1 = {r["Part1"]: c for c, r in codes.items() if r["Part1"]}
    part1["sh"] = "hbs"
    part2b = {r["Part2b"]: c for c, r in codes.items() if r["Part2b"]}
    out: list[dict] = []

    def emit(code: str, measure: str, s: Any, label: str, lo: float | None, hi: float | None,
             state: str, pop: list[Any], relation: str, basis: str, source: Any = None,
             version: Any = None, url: Any = None, at: Any = None, sha: Any = None) -> None:
        if code not in in_scope:
            return
        out.append({
            "iso639_3": code, "measure": measure,
            "source": source or s.source, "source_version": version or s.version,
            "source_label": label,
            "value_low": None if lo is None else float(lo), "value_high": None if hi is None else float(hi),
            "state": state, "label_population": json.dumps(sorted(set(pop))), "relation": relation,
            "mapping_basis": basis, "source_url": url or s.url, "retrieved_at": at or s.at,
            "content_sha256": sha or s.sha,
        })

    # ---------------- CLDR: official status and speakers ----------------
    cl = srcs["cldr"]
    root = ET.fromstring(cl.body)
    placeholder = set(CLDR_PLACEHOLDER_REFS)
    cldr: dict[str, dict] = {}
    for terr in root.iter("territory"):
        tc = terr.get("type")
        pop = float(terr.get("population") or 0)
        for lp in terr.findall("languagePopulation"):
            loc = lp.get("type") or ""
            base = loc.split("_")[0]
            code = part1.get(base, base) if len(base) == 2 else base
            d = cldr.setdefault(code, {"kept": 0.0, "dropped": 0.0, "nk": 0, "nd": 0, "nat": set(), "reg": set(),
                                       "labels": set(), "refs": set()})
            d["labels"].add(base)
            sp = pop * float(lp.get("populationPercent") or 0) / 100.0
            refs = set((lp.get("references") or "").split())
            st = lp.get("officialStatus")
            if st in ("official", "de_facto_official"):
                d["nat"].add(tc)
            elif st == "official_regional":
                d["reg"].add(tc)
            if refs & placeholder:
                d["dropped"] += sp
                d["nd"] += 1
                d["refs"] |= refs & placeholder
            else:
                d["kept"] += sp
                d["nk"] += 1

    # ---------------- Wikidata: P37 and P1098 ----------------
    wo = srcs["wd_official"]
    wd_off: dict[str, dict[str, set]] = {}
    for r in csv.DictReader(io.StringIO(wo.body.decode("utf-8"))):
        wd_off.setdefault(r["iso"], {"adm1": set(), "sovereign_state": set()})[r["kind"]].add(r["ent"].rsplit("/", 1)[1])
    ws = srcs["wd_speakers"]
    stmts: dict[str, list[dict]] = {}
    for r in csv.DictReader(io.StringIO(ws.body.decode("utf-8"))):
        stmts.setdefault(r["iso"], []).append(r)

    def wd_speaker(rows: list[dict]) -> tuple[float | None, str]:
        rows = [r for r in rows if r["part"] != L2]
        if not rows:
            return None, ""
        glob = [r for r in rows if not r["place"]]
        if glob:
            l1 = [r for r in glob if r["part"] == L1]
            pick = l1 or glob
            pref = [r for r in pick if r["rank"].endswith("PreferredRank")]
            pick = pref or pick
            best = max(pick, key=lambda r: (r["date"] or "", float(r["amount"])))
            items = sorted({r["item"].rsplit("/", 1)[1] for r in pick})
            return float(best["amount"]), (f"global statement, {'first-language (P518 Q36870)' if l1 else 'unqualified'}, "
                                           f"{'preferred rank, ' if pref else ''}latest date {best['date'][:10] or 'undated'}; items {','.join(items)}")
        per: dict[str, dict] = {}
        for r in rows:
            cur = per.get(r["place"])
            if cur is None or (r["date"] or "") > (cur["date"] or ""):
                per[r["place"]] = r
        return sum(float(r["amount"]) for r in per.values()), f"no global statement; latest value per country summed over {len(per)} countries"

    # ---------------- official_status ----------------
    for c in scope:
        d = cldr.get(c)
        named = False
        if d and (d["nat"] or d["reg"]):
            named = True
            lv = 2.0 if d["nat"] else 1.0
            emit(c, "official_status", cl, ",".join(sorted(d["labels"])), lv, lv, "measured", [c], "exact",
                 ("national: official or de_facto_official in " + " ".join(sorted(d["nat"]))) if d["nat"]
                 else ("subnational: official_regional in " + " ".join(sorted(d["reg"]))) + "; value 2=national, 1=subnational, 0=none")
        w = wd_off.get(c)
        if w and w["adm1"]:
            named = True
            emit(c, "official_status", wo, "P37@first-level subdivision", 1.0, 1.0, "measured", [c], "exact",
                 f"P37 on {len(w['adm1'])} first-level subdivisions (P31/P279* Q10864048), no end date, entity not dissolved; value 1=subnational")
        if w and w["sovereign_state"]:
            emit(c, "official_status", wo, "P37@sovereign state", None, None, "excluded", [c], "exact",
                 f"recognized: P37 on {len(w['sovereign_state'])} sovereign states (Q3624078). State-level P37 is recorded as recognition and enters no official verdict; national status comes from CLDR only")
        if named:
            continue
        M = member_of.get(c)
        md = cldr.get(M) if M else None
        if md and (md["nat"] or md["reg"]):
            lv = 2.0 if md["nat"] else 1.0
            emit(c, "official_status", cl, ",".join(sorted(md["labels"])), 0.0, max(lv, 1.0), "bounded", [M] + members.get(M, []),
                 "broader", f"macrolanguage {M} holds the status and no source names {c}: interval none..{'national' if lv == 2 else 'subnational'}")
        else:
            emit(c, "official_status", cl, "(none)", 0.0, 1.0, "not_listed", [c], "exact",
                 "neither CLDR nor Wikidata lists the code as official at any level: national observed absent (CLDR national list is complete), subnational unknown",
                 source="cldr+wikidata", version=f"{CLDR_VERSION}+wikidata@{wo.at.isoformat()}Z", url=f"{cl.url} ; {wo.url}",
                 sha=hashlib.sha256((cl.sha + wo.sha).encode()).hexdigest())

    # ---------------- speakers ----------------
    for c in scope:
        d = cldr.get(c)
        if d and d["nk"] > 0:
            emit(c, "speakers", cl, ",".join(sorted(d["labels"])), d["kept"], d["kept"], "measured", [c], "exact",
                 f"sum over {d['nk']} territories of population x populationPercent (users, L1 and L2)")
        if d and d["nd"] > 0:
            emit(c, "speakers", cl, ",".join(sorted(d["labels"])) + "@placeholder", d["dropped"], d["dropped"], "excluded", [c], "exact",
                 f"placeholder estimate without a count, dropped: {d['nd']} territory entries citing {' '.join(sorted(d['refs']))}")
        if not (d and d["nk"] > 0):
            M = member_of.get(c)
            md = cldr.get(M) if M else None
            ms = [cldr[m]["kept"] for m in members.get(c, []) if m in cldr and cldr[m]["nk"] > 0]
            if md and md["nk"] > 0:
                emit(c, "speakers", cl, ",".join(sorted(md["labels"])), None, md["kept"], "bounded", [M] + members.get(M, []), "broader",
                     f"CLDR reports the macrolanguage {M}; its figure bounds {c} from above")
            elif ms:
                emit(c, "speakers", cl, "(members)", sum(ms), None, "bounded", members[c], "members_only_lower_bound",
                     f"CLDR reports {len(ms)} of {len(members[c])} members only; their sum bounds {c} from below")
            elif not (d and d["nd"] > 0):
                emit(c, "speakers", cl, "(none)", None, None, "unmeasured", [c], "exact", "not in CLDR territory data")
        val, how = wd_speaker(stmts.get(c, []))
        if val is None:
            emit(c, "speakers", ws, "(none)", None, None, "unmeasured", [c], "exact", "no non-deprecated L1 or unqualified P1098 statement")
        elif c in WIKIDATA_SPEAKER_BROADER:
            emit(c, "speakers", ws, "P1098", None, val, "bounded", [c, "man"], "broader", WIKIDATA_SPEAKER_BROADER[c] + "; " + how)
        else:
            emit(c, "speakers", ws, "P1098", val, val, "measured", [c], "exact", how)

    # ---------------- Glottolog: endangerment and descriptive status ----------------
    gl, gv, gc = srcs["gl_languages"], srcs["gl_values"], srcs["gl_codes"]
    langs = list(csv.DictReader(io.StringIO(gl.body.decode("utf-8"))))
    name_of = {r["ID"]: r["Name"] for r in langs}
    by_iso: dict[str, list[dict]] = {}
    for r in langs:
        if r["ISO639P3code"]:
            by_iso.setdefault(r["ISO639P3code"], []).append(r)
    order = {}
    for r in csv.DictReader(io.StringIO(gc.body.decode("utf-8"))):
        if r["Parameter_ID"] in ("aes", "med") and r["numerical_value"]:
            order[r["ID"]] = (r["Name"], float(r["numerical_value"]))
    vals: dict[tuple[str, str], str] = {}
    for line in gv.body.decode("utf-8").splitlines():
        if "-aes," in line or "-med," in line:
            p = next(csv.reader([line]))
            if len(p) >= 5 and p[2] in ("aes", "med"):
                vals[(p[1], p[2])] = p[4]
    for c in scope:
        cand = by_iso.get(c, [])
        if not cand:
            emit(c, "endangerment", gv, "(none)", None, None, "unmeasured", [c], "exact", "no Glottolog languoid carries this ISO code")
            emit(c, "descriptive_status", gv, "(none)", None, None, "unmeasured", [c], "exact", "no Glottolog languoid carries this ISO code")
            continue
        g = sorted(cand, key=lambda r: (r["Level"] != "language", r["ID"]))[0]
        fam = g["Family_ID"] or ""
        famname = name_of.get(fam, "isolate") if fam else "isolate"
        for measure, param in (("endangerment", "aes"), ("descriptive_status", "med")):
            code_id = vals.get((g["ID"], param))
            if not code_id or code_id not in order:
                emit(c, measure, gv, g["ID"], None, None, "unmeasured", [c], "exact", f"languoid {g['ID']} has no {param.upper()} value")
                continue
            nm, num = order[code_id]
            basis = f"{param.upper()} '{nm}' of languoid {g['ID']} (level {g['Level']}, family {fam or '-'} {famname})"
            state = "measured"
            if measure == "endangerment" and (g["Level"] != "language" or fam in GLOTTOLOG_EXCLUDED_FAMILIES):
                state = "excluded"
                basis += "; excluded from the speaker bound: " + (
                    f"family {GLOTTOLOG_EXCLUDED_FAMILIES[fam]} carries no information about a speaker community"
                    if fam in GLOTTOLOG_EXCLUDED_FAMILIES else f"level {g['Level']} is not 'language'")
            emit(c, measure, gv, f"{g['ID']}:{nm}", num, num, state, [c], "exact", basis)

    # ---------------- FineWeb-2: web_text_words ----------------
    fw = srcs["fineweb2"]
    words: dict[str, float] = {}
    for r in csv.DictReader(io.StringIO(fw.body.decode("utf-8"))):
        if r["split"] != "train" or r["subset"].endswith("_removed"):
            continue
        try:
            n = float(r["words"])
        except ValueError:
            continue
        try:
            bible = float(r["bible_ratio"])
        except ValueError:
            bible = 0.0
        words[r["code"]] = words.get(r["code"], 0.0) + n * (1.0 - bible)
    glot = srcs["glotlid"]
    g3 = set(m.group(1) for m in re.finditer(r"^\|\s*\d+\s*\|\s*([a-z]{3})_[A-Za-z]{4}\s*\|", glot.body.decode("utf-8"), re.M))
    fw_filed = {cov: (lab, basis) for s, lab, cov, basis in RELATED_FILINGS if s == "fineweb-2"}
    for c in scope:
        M = member_of.get(c)
        if c == "eng":
            emit(c, "web_text_words", fw, "(none)", None, None, "unmeasured", [c], "exact", "FineWeb-2 excludes English by construction")
        elif M and M in words:
            # A detector's macrolanguage label is broader for every member, including one with its own label.
            lo = words.get(c, 0.0)
            emit(c, "web_text_words", fw, (c + "+" if c in words else "") + M, lo, lo + words[M], "bounded",
                 [M] + members.get(M, []), "broader",
                 f"FineWeb-2 (GlotLID v3) label {M} covers the member; a detector's member/macrolanguage split is not reliable")
        elif c in words:
            emit(c, "web_text_words", fw, c, words[c], words[c], "measured", [c], "exact",
                 "words x (1 - bible_ratio), filtered train split (subsets ending _removed excluded), summed over scripts")
        elif c in members and any(m in words for m in members[c]):
            ms = [m for m in members[c] if m in words]
            tot = sum(words[m] for m in ms)
            if all(m in g3 for m in members[c]):
                emit(c, "web_text_words", fw, "+".join(ms), tot, tot, "measured", members[c], "aggregate",
                     "GlotLID v3 labels every member separately; sum of member counts")
            else:
                emit(c, "web_text_words", fw, "+".join(ms), tot, None, "bounded", ms, "members_only_lower_bound",
                     f"GlotLID v3 labels {sum(m in g3 for m in members[c])} of {len(members[c])} members; sum is a lower bound")
        elif c in fw_filed and fw_filed[c][0] in words:
            lab = fw_filed[c][0]
            emit(c, "web_text_words", fw, lab, 0.0, words[lab], "bounded", [lab, c], "broader", fw_filed[c][1])
        elif c in g3:
            emit(c, "web_text_words", fw, c, None, None, "not_detected", [c], "exact",
                 f"GlotLID v3 has a {c} label but FineWeb-2 has no row for it")
        else:
            emit(c, "web_text_words", fw, "(none)", None, None, "unmeasured", [c], "exact", "not a GlotLID v3 label")

    # ---------------- Common Crawl CLD2: web_page_share ----------------
    cc = srcs["cc"]
    rows = list(csv.DictReader(io.StringIO(cc.body.decode("utf-8"))))
    crawl = max(r["crawl"] for r in rows)
    tot = sum(int(r["pages"]) for r in rows if r["crawl"] == crawl)
    share = {r["primary_language"]: int(r["pages"]) / tot * 100.0 for r in rows if r["crawl"] == crawl}
    cld2_set = {r["primary_language"] for r in rows if r["primary_language"] in codes}
    cc_ver = f"{crawl}"
    cc_filed = {cov: (lab, basis) for s, lab, cov, basis in RELATED_FILINGS if s == "commoncrawl-cld2"}
    for c in scope:
        own = share.get(c)
        M = member_of.get(c)
        if c in members:
            ms = [m for m in members[c] if m in share]
            if own is not None or ms:
                v = (own or 0.0) + sum(share[m] for m in ms)
                lab = "+".join(([c] if own is not None else []) + ms)
                if own is not None and not ms:
                    emit(c, "web_page_share", cc, c, v, v, "measured", [c] + members[c], "exact", f"CLD2 macrolanguage label, {crawl}; percent of all pages incl. <unknown>", version=cc_ver)
                elif own is not None or all(m in cld2_set for m in members[c]):
                    emit(c, "web_page_share", cc, lab, v, v, "measured", [c] + members[c], "aggregate", f"sum of CLD2 labels for the macrolanguage and its members, {crawl}", version=cc_ver)
                else:
                    emit(c, "web_page_share", cc, lab, v, None, "bounded", ms, "members_only_lower_bound", f"CLD2 labels only some members, {crawl}", version=cc_ver)
                continue
        if M and M in share:
            lo = own or 0.0
            emit(c, "web_page_share", cc, (c + "+" if own is not None else "") + M, lo, lo + share[M], "bounded", [M] + members.get(M, []), "broader",
                 f"CLD2 label {M} covers the member; a detector's member/macrolanguage split is not reliable, {crawl}", version=cc_ver)
        elif c in cc_filed and cc_filed[c][0] in share:
            lab = cc_filed[c][0]
            emit(c, "web_page_share", cc, lab, 0.0, share[lab], "bounded", [lab, c], "broader", cc_filed[c][1] + f", {crawl}", version=cc_ver)
        elif own is not None:
            emit(c, "web_page_share", cc, c, own, own, "measured", [c], "exact", f"CLD2 label, {crawl}; percent of all pages incl. <unknown>", version=cc_ver)
        elif c in cld2_set:
            emit(c, "web_page_share", cc, c, None, None, "not_detected", [c], "exact", f"CLD2 label seen in earlier crawls, absent from {crawl}", version=cc_ver)
        else:
            emit(c, "web_page_share", cc, "(none)", None, None, "unmeasured", [c], "exact", "not a CLD2 label", version=cc_ver)

    # ---------------- Wikipedia: articles and active users ----------------
    sm = srcs["sitematrix"]
    ed_of: dict[str, list[str]] = {}
    for e in wiki:
        if e in WIKI_UNMAPPED:
            continue
        code = WIKI_COMPOSITE.get(e) or (part1.get(e) if len(e) == 2 else (e if e in codes else None))
        if code:
            ed_of.setdefault(code, []).append(e)
    wp_filed = {cov: (lab, basis) for s, lab, cov, basis in RELATED_FILINGS if s == "wikipedia"}

    def wp_emit(c: str, eds: list[str], relation: str, basis: str, pop: list[str], bounded: bool) -> None:
        art = sum(wiki[e][1]["articles"] for e in eds)
        act = sum(wiki[e][1]["activeusers"] for e in eds)
        ratio = art / act if act else float("inf")
        eligible = act >= 100 and ratio <= 1000
        label = "+".join(eds)
        s0 = wiki[eds[0]][0]
        sha = hashlib.sha256("".join(wiki[e][0].sha for e in eds).encode()).hexdigest()
        url = " ; ".join(wiki[e][0].url for e in eds)
        state = ("bounded" if bounded else "measured") if eligible else "excluded"
        b = basis + f"; {act} active users, {ratio:.0f} content articles per active user"
        if not eligible:
            b += "; excluded: fails the bot guard (needs >= 100 active users and <= 1,000 articles per active user)"
        for measure, v in (("wikipedia_articles", art), ("wikipedia_active_users", act)):
            emit(c, measure, s0, label, 0.0 if bounded else v, v, state, pop, relation, b, url=url, sha=sha)

    for c in scope:
        if c in ed_of:
            wp_emit(c, ed_of[c], "exact", "the code's own edition", [c], False)
            continue
        if c in members:
            eds = [e for k in [c] + members[c] for e in ed_of.get(k, [])]
            if eds:
                wp_emit(c, eds, "aggregate", "macrolanguage edition plus member editions, each article once", [c] + members[c], False)
                continue
        M = member_of.get(c)
        if M and M in ed_of:
            rest = [k for k in members[M] if k not in ed_of]
            if rest == [c]:
                wp_emit(c, ed_of[M], "edition_complement", f"the {M} edition with every other member in its own edition", [c], False)
            else:
                wp_emit(c, ed_of[M], "broader", f"the {M} edition covers members without their own edition", [M] + rest, True)
            continue
        if c in wp_filed and wp_filed[c][0] in ed_of:
            wp_emit(c, ed_of[wp_filed[c][0]], "broader", wp_filed[c][1], [wp_filed[c][0], c], True)
            continue
        for measure in ("wikipedia_articles", "wikipedia_active_users"):
            emit(c, measure, sm, "(none)", 0.0, 0.0, "observed_absent", [c], "observed_absent",
                 "no edition for the code or its macrolanguage in the Wikimedia site matrix, which lists every edition")

    # ---------------- Open Library (context; corroboration only) ----------------
    # One search per MARC language code. A count is read only from an HTTP 200 answer with numFound
    # above zero: the search answers 0 (or HTTP 500) when it times out, so a zero is never an observation.
    ol_version = f"search.json@{run_at.date().isoformat()}"

    def ol_of(code: str) -> SimpleNamespace | None:
        b = codes[code]["Part2b"] if code in codes else ""
        return ol.get(b) if b else None

    for c in scope:
        M = member_of.get(c)
        own, broad = ol_of(c), (ol_of(M) if M else None)
        if own is not None and own.count:
            emit(c, "open_library_works", None, own.marc, own.count, own.count, "measured", [c] + members.get(c, []),
                 "exact", f"Open Library works with MARC language code {own.marc} (ISO 639-2/B); {own.note}",
                 source="open-library", version=ol_version, url=own.url, at=own.at, sha=own.sha)
        elif M and broad is not None and broad.count:
            why = f"; own code {own.marc}: {own.note}, not read as a count" if own is not None else ""
            emit(c, "open_library_works", None, broad.marc, 0.0, broad.count, "bounded", [M] + members.get(M, []),
                 "broader", f"MARC code {broad.marc} for the macrolanguage {M} covers the member; {broad.note}{why}",
                 source="open-library", version=ol_version, url=broad.url, at=broad.at, sha=broad.sha)
        elif own is not None:
            emit(c, "open_library_works", None, own.marc, None, None, "unmeasured", [c], "exact",
                 f"MARC language code {own.marc}: {own.note}; a failed search or a zero count is not read as a count",
                 source="open-library", version=ol_version, url=own.url, at=own.at, sha=own.sha)
        else:
            emit(c, "open_library_works", None, "(none)", None, None, "unmeasured", [c], "exact",
                 "no MARC language code (ISO 639-2/B) for the code or its macrolanguage, so Open Library was not searched",
                 source="open-library", version=ol_version, url=OPEN_LIBRARY_SEARCH, at=run_at,
                 sha=hashlib.sha256(b"").hexdigest())

    # ---------------- OpenAlex (context) ----------------
    oa = srcs.get("openalex")
    oa_by: dict[str, float] = {}
    if oa is not None:
        for g in json.loads(oa.body.decode("utf-8")).get("group_by", []):
            k = g["key"].rsplit("/", 1)[-1]
            c = part1.get(k)
            if c:
                oa_by[c] = oa_by.get(c, 0.0) + float(g["count"])
    oa_kw = dict(source="openalex", version=f"api@{oa.at.isoformat()}Z" if oa else "unavailable",
                 url=OPENALEX_URL, at=oa.at if oa else run_at, sha=oa.sha if oa else hashlib.sha256(b"").hexdigest())
    for c in scope:
        M = member_of.get(c)
        if oa is None:
            emit(c, "scholarly_works", None, "(none)", None, None, "unmeasured", [c], "exact", "OpenAlex could not be read this run", **oa_kw)
        elif c in oa_by:
            emit(c, "scholarly_works", None, c, oa_by[c], oa_by[c], "measured", [c] + members.get(c, []), "exact",
                 "works whose metadata language OpenAlex detects as this label (top 200 groups)", **oa_kw)
        elif M and M in oa_by:
            emit(c, "scholarly_works", None, M, 0.0, oa_by[M], "bounded", [M] + members.get(M, []), "broader",
                 f"OpenAlex label for the macrolanguage {M} covers the member", **oa_kw)
        else:
            emit(c, "scholarly_works", None, "(none)", None, None, "unmeasured", [c], "exact",
                 "not among the OpenAlex language groups returned (top 200, detector coverage)", **oa_kw)

    for o in OVERRIDES:
        out.append(dict(o))

    out = [r for r in out if (r["measure"] == "open_library_works") == open_library]
    return pl.DataFrame(out, schema={
        "iso639_3": pl.Utf8, "measure": pl.Utf8, "source": pl.Utf8, "source_version": pl.Utf8,
        "source_label": pl.Utf8, "value_low": pl.Float64, "value_high": pl.Float64, "state": pl.Utf8,
        "label_population": pl.Utf8, "relation": pl.Utf8, "mapping_basis": pl.Utf8,
        "source_url": pl.Utf8, "retrieved_at": pl.Datetime("us"), "content_sha256": pl.Utf8,
    })


@oso.model(
    external_origins=["https://raw.githubusercontent.com", "https://iso639-3.sil.org", "https://commoncrawl.github.io", "https://query.wikidata.org", "https://meta.wikimedia.org", "https://api.openalex.org", "https://openlibrary.org", "https://aa.wikipedia.org", "https://ab.wikipedia.org", "https://ace.wikipedia.org", "https://ady.wikipedia.org", "https://af.wikipedia.org", "https://ak.wikipedia.org", "https://als.wikipedia.org", "https://alt.wikipedia.org", "https://am.wikipedia.org", "https://ami.wikipedia.org", "https://an.wikipedia.org", "https://ang.wikipedia.org", "https://ann.wikipedia.org", "https://anp.wikipedia.org", "https://ar.wikipedia.org", "https://arc.wikipedia.org", "https://ary.wikipedia.org", "https://arz.wikipedia.org", "https://as.wikipedia.org", "https://ast.wikipedia.org", "https://atj.wikipedia.org", "https://av.wikipedia.org", "https://avk.wikipedia.org", "https://awa.wikipedia.org", "https://ay.wikipedia.org", "https://az.wikipedia.org", "https://azb.wikipedia.org", "https://ba.wikipedia.org", "https://ban.wikipedia.org", "https://bar.wikipedia.org", "https://bat-smg.wikipedia.org", "https://bbc.wikipedia.org", "https://bcl.wikipedia.org", "https://bdr.wikipedia.org", "https://be-tarask.wikipedia.org", "https://be.wikipedia.org", "https://bew.wikipedia.org", "https://bg.wikipedia.org", "https://bh.wikipedia.org", "https://bi.wikipedia.org", "https://bjn.wikipedia.org", "https://blk.wikipedia.org", "https://bm.wikipedia.org", "https://bn.wikipedia.org", "https://bo.wikipedia.org", "https://bol.wikipedia.org", "https://bpy.wikipedia.org", "https://br.wikipedia.org", "https://bs.wikipedia.org", "https://btm.wikipedia.org", "https://bug.wikipedia.org", "https://bxr.wikipedia.org", "https://ca.wikipedia.org", "https://cbk-zam.wikipedia.org", "https://cdo.wikipedia.org", "https://ce.wikipedia.org", "https://ceb.wikipedia.org", "https://ch.wikipedia.org", "https://cho.wikipedia.org", "https://chr.wikipedia.org", "https://chy.wikipedia.org", "https://ckb.wikipedia.org", "https://co.wikipedia.org", "https://cr.wikipedia.org", "https://crh.wikipedia.org", "https://cs.wikipedia.org", "https://csb.wikipedia.org", "https://cu.wikipedia.org", "https://cv.wikipedia.org", "https://cy.wikipedia.org", "https://da.wikipedia.org", "https://dag.wikipedia.org", "https://de.wikipedia.org", "https://dga.wikipedia.org", "https://din.wikipedia.org", "https://diq.wikipedia.org", "https://dsb.wikipedia.org", "https://dtp.wikipedia.org", "https://dty.wikipedia.org", "https://dv.wikipedia.org", "https://dz.wikipedia.org", "https://ee.wikipedia.org", "https://el.wikipedia.org", "https://eml.wikipedia.org", "https://en.wikipedia.org", "https://eo.wikipedia.org", "https://es.wikipedia.org", "https://et.wikipedia.org", "https://eu.wikipedia.org", "https://ext.wikipedia.org", "https://fa.wikipedia.org", "https://fat.wikipedia.org", "https://ff.wikipedia.org", "https://fi.wikipedia.org", "https://fiu-vro.wikipedia.org", "https://fj.wikipedia.org", "https://fo.wikipedia.org", "https://fon.wikipedia.org", "https://fr.wikipedia.org", "https://frp.wikipedia.org", "https://frr.wikipedia.org", "https://fur.wikipedia.org", "https://fy.wikipedia.org", "https://ga.wikipedia.org", "https://gag.wikipedia.org", "https://gan.wikipedia.org", "https://gcr.wikipedia.org", "https://gd.wikipedia.org", "https://gl.wikipedia.org", "https://glk.wikipedia.org", "https://gn.wikipedia.org", "https://gom.wikipedia.org", "https://gor.wikipedia.org", "https://got.wikipedia.org", "https://gpe.wikipedia.org", "https://gu.wikipedia.org", "https://guc.wikipedia.org", "https://gur.wikipedia.org", "https://guw.wikipedia.org", "https://gv.wikipedia.org", "https://ha.wikipedia.org", "https://hak.wikipedia.org", "https://haw.wikipedia.org", "https://he.wikipedia.org", "https://hi.wikipedia.org", "https://hif.wikipedia.org", "https://ho.wikipedia.org", "https://hr.wikipedia.org", "https://hsb.wikipedia.org", "https://ht.wikipedia.org", "https://hu.wikipedia.org", "https://hy.wikipedia.org", "https://hyw.wikipedia.org", "https://hz.wikipedia.org", "https://ia.wikipedia.org", "https://iba.wikipedia.org", "https://id.wikipedia.org", "https://ie.wikipedia.org", "https://ig.wikipedia.org", "https://igl.wikipedia.org", "https://ii.wikipedia.org", "https://ik.wikipedia.org", "https://ilo.wikipedia.org", "https://inh.wikipedia.org", "https://io.wikipedia.org", "https://is.wikipedia.org", "https://isv.wikipedia.org", "https://it.wikipedia.org", "https://iu.wikipedia.org", "https://ja.wikipedia.org", "https://jam.wikipedia.org", "https://jbo.wikipedia.org", "https://jv.wikipedia.org", "https://ka.wikipedia.org", "https://kaa.wikipedia.org", "https://kab.wikipedia.org", "https://kai.wikipedia.org", "https://kaj.wikipedia.org", "https://kbd.wikipedia.org", "https://kbp.wikipedia.org", "https://kcg.wikipedia.org", "https://kg.wikipedia.org", "https://kge.wikipedia.org", "https://ki.wikipedia.org", "https://kj.wikipedia.org", "https://kk.wikipedia.org", "https://kl.wikipedia.org", "https://km.wikipedia.org", "https://kn.wikipedia.org", "https://knc.wikipedia.org", "https://ko.wikipedia.org", "https://koi.wikipedia.org", "https://kr.wikipedia.org", "https://krc.wikipedia.org", "https://ks.wikipedia.org", "https://ksh.wikipedia.org", "https://ku.wikipedia.org", "https://kus.wikipedia.org", "https://kv.wikipedia.org", "https://kw.wikipedia.org", "https://ky.wikipedia.org", "https://la.wikipedia.org", "https://lad.wikipedia.org", "https://lb.wikipedia.org", "https://lbe.wikipedia.org", "https://lez.wikipedia.org", "https://lfn.wikipedia.org", "https://lg.wikipedia.org", "https://li.wikipedia.org", "https://lij.wikipedia.org", "https://lld.wikipedia.org", "https://lmo.wikipedia.org", "https://ln.wikipedia.org", "https://lo.wikipedia.org", "https://lrc.wikipedia.org", "https://lt.wikipedia.org", "https://ltg.wikipedia.org", "https://lv.wikipedia.org", "https://mad.wikipedia.org", "https://mag.wikipedia.org", "https://mai.wikipedia.org", "https://map-bms.wikipedia.org", "https://mdf.wikipedia.org", "https://mg.wikipedia.org", "https://mh.wikipedia.org", "https://mhr.wikipedia.org", "https://mi.wikipedia.org", "https://min.wikipedia.org", "https://mk.wikipedia.org", "https://ml.wikipedia.org", "https://mn.wikipedia.org", "https://mni.wikipedia.org", "https://mnw.wikipedia.org", "https://mos.wikipedia.org", "https://mr.wikipedia.org", "https://mrj.wikipedia.org", "https://ms.wikipedia.org", "https://mt.wikipedia.org", "https://mus.wikipedia.org", "https://mwl.wikipedia.org", "https://my.wikipedia.org", "https://myv.wikipedia.org", "https://mzn.wikipedia.org", "https://na.wikipedia.org", "https://nah.wikipedia.org", "https://nap.wikipedia.org", "https://nds-nl.wikipedia.org", "https://nds.wikipedia.org", "https://ne.wikipedia.org", "https://new.wikipedia.org", "https://ng.wikipedia.org", "https://nia.wikipedia.org", "https://nl.wikipedia.org", "https://nn.wikipedia.org", "https://no.wikipedia.org", "https://nov.wikipedia.org", "https://nqo.wikipedia.org", "https://nr.wikipedia.org", "https://nrm.wikipedia.org", "https://nso.wikipedia.org", "https://nup.wikipedia.org", "https://nv.wikipedia.org", "https://ny.wikipedia.org", "https://oc.wikipedia.org", "https://olo.wikipedia.org", "https://om.wikipedia.org", "https://or.wikipedia.org", "https://os.wikipedia.org", "https://pa.wikipedia.org", "https://pag.wikipedia.org", "https://pam.wikipedia.org", "https://pap.wikipedia.org", "https://pcd.wikipedia.org", "https://pcm.wikipedia.org", "https://pdc.wikipedia.org", "https://pfl.wikipedia.org", "https://pi.wikipedia.org", "https://pih.wikipedia.org", "https://pl.wikipedia.org", "https://pms.wikipedia.org", "https://pnb.wikipedia.org", "https://pnt.wikipedia.org", "https://ppl.wikipedia.org", "https://ps.wikipedia.org", "https://pt.wikipedia.org", "https://pwn.wikipedia.org", "https://qu.wikipedia.org", "https://rki.wikipedia.org", "https://rm.wikipedia.org", "https://rmy.wikipedia.org", "https://rn.wikipedia.org", "https://ro.wikipedia.org", "https://roa-rup.wikipedia.org", "https://roa-tara.wikipedia.org", "https://rsk.wikipedia.org", "https://ru.wikipedia.org", "https://rue.wikipedia.org", "https://rw.wikipedia.org", "https://sa.wikipedia.org", "https://sah.wikipedia.org", "https://sat.wikipedia.org", "https://sc.wikipedia.org", "https://scn.wikipedia.org", "https://sco.wikipedia.org", "https://sd.wikipedia.org", "https://se.wikipedia.org", "https://sg.wikipedia.org", "https://sh.wikipedia.org", "https://shi.wikipedia.org", "https://shn.wikipedia.org", "https://si.wikipedia.org", "https://simple.wikipedia.org", "https://sk.wikipedia.org", "https://skr.wikipedia.org", "https://sl.wikipedia.org", "https://sm.wikipedia.org", "https://smn.wikipedia.org", "https://sn.wikipedia.org", "https://so.wikipedia.org", "https://sq.wikipedia.org", "https://sr.wikipedia.org", "https://srn.wikipedia.org", "https://ss.wikipedia.org", "https://st.wikipedia.org", "https://stq.wikipedia.org", "https://su.wikipedia.org", "https://sv.wikipedia.org", "https://sw.wikipedia.org", "https://syl.wikipedia.org", "https://szl.wikipedia.org", "https://szy.wikipedia.org", "https://ta.wikipedia.org", "https://tay.wikipedia.org", "https://tcy.wikipedia.org", "https://tdd.wikipedia.org", "https://te.wikipedia.org", "https://tet.wikipedia.org", "https://tg.wikipedia.org", "https://th.wikipedia.org", "https://ti.wikipedia.org", "https://tig.wikipedia.org", "https://tk.wikipedia.org", "https://tl.wikipedia.org", "https://tly.wikipedia.org", "https://tn.wikipedia.org", "https://to.wikipedia.org", "https://tok.wikipedia.org", "https://tpi.wikipedia.org", "https://tr.wikipedia.org", "https://trv.wikipedia.org", "https://ts.wikipedia.org", "https://tt.wikipedia.org", "https://tum.wikipedia.org", "https://tw.wikipedia.org", "https://ty.wikipedia.org", "https://tyv.wikipedia.org", "https://udm.wikipedia.org", "https://ug.wikipedia.org", "https://uk.wikipedia.org", "https://ur.wikipedia.org", "https://uz.wikipedia.org", "https://ve.wikipedia.org", "https://vec.wikipedia.org", "https://vep.wikipedia.org", "https://vi.wikipedia.org", "https://vls.wikipedia.org", "https://vo.wikipedia.org", "https://wa.wikipedia.org", "https://war.wikipedia.org", "https://wo.wikipedia.org", "https://wuu.wikipedia.org", "https://xal.wikipedia.org", "https://xh.wikipedia.org", "https://xmf.wikipedia.org", "https://yi.wikipedia.org", "https://yo.wikipedia.org", "https://za.wikipedia.org", "https://zea.wikipedia.org", "https://zgh.wikipedia.org", "https://zh-classical.wikipedia.org", "https://zh-min-nan.wikipedia.org", "https://zh-yue.wikipedia.org", "https://zh.wikipedia.org", "https://zu.wikipedia.org"],
    capabilities=oso.Capabilities(fetch=True),
    columns=[
        oso.Column(name="iso639_3", type="varchar"),
        oso.Column(name="measure", type="varchar"),
        oso.Column(name="source", type="varchar"),
        oso.Column(name="source_version", type="varchar"),
        oso.Column(name="source_label", type="varchar"),
        oso.Column(name="value_low", type="double"),
        oso.Column(name="value_high", type="double"),
        oso.Column(name="state", type="varchar"),
        oso.Column(name="label_population", type="varchar"),
        oso.Column(name="relation", type="varchar"),
        oso.Column(name="mapping_basis", type="varchar"),
        oso.Column(name="source_url", type="varchar"),
        oso.Column(name="retrieved_at", type="timestamp(6)"),
        oso.Column(name="content_sha256", type="varchar"),
    ],
)
async def measurements_src(context: oso.AsyncContext) -> AsyncIterator[oso.DataFrame]:
    # Output goes out in two chunks, because the host waits at most five minutes for each chunk:
    # every measure except Open Library first, then Open Library, whose searches run alongside.
    form = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/csv"}
    iso_src = await read_source(context, "iso639-3", ISO_RELEASE, ISO_ZIP_URL)
    iso_codes, _, _ = iso_tables(iso_src)
    marcs = sorted({r["Part2b"] for r in iso_codes.values() if r["Part2b"] and r["Scope"] != "S"})
    ol_sem = asyncio.Semaphore(OPEN_LIBRARY_CONCURRENCY)
    ol: dict[str, SimpleNamespace] = {}

    async def ol_one(marc: str) -> None:
        async with ol_sem:
            ol[marc] = await open_library_count(context, marc)
            await asyncio.sleep(OPEN_LIBRARY_PAUSE)

    ol_task = asyncio.ensure_future(asyncio.gather(*(ol_one(m) for m in marcs)))
    reads = await asyncio.gather(
        read_source(context, "cldr", CLDR_VERSION, CLDR_URL),
        read_source(context, "glottolog", GLOTTOLOG_VERSION, GLOTTOLOG_LANGUAGES_URL),
        read_source(context, "glottolog", GLOTTOLOG_VERSION, GLOTTOLOG_VALUES_URL, timeout=300.0),
        read_source(context, "glottolog", GLOTTOLOG_VERSION, GLOTTOLOG_CODES_URL),
        read_source(context, "fineweb-2", FINEWEB2_COMMIT, FINEWEB2_URL),
        read_source(context, "glotlid-v3", GLOTLID_COMMIT, GLOTLID_URL),
        read_source(context, "commoncrawl-cld2", "latest", CC_URL),
        read_source(context, "meta.wikimedia.org", "sitematrix", SITEMATRIX_URL),
    )
    keys = ["cldr", "gl_languages", "gl_values", "gl_codes", "fineweb2", "glotlid", "cc", "sitematrix"]
    srcs = dict(zip(keys, reads))
    srcs["iso"] = iso_src
    # Wikidata: sequential, one query at a time.
    for key, q in (("wd_speakers", SPARQL_SPEAKERS), ("wd_official", SPARQL_OFFICIAL)):
        body = "query=" + urllib.parse.quote(q)
        b, at, status = await fetch_bytes(context, WIKIDATA_URL, method="POST", body=body, extra=form, timeout=180.0)
        if status != 200:
            raise RuntimeError(f"Wikidata returned HTTP {status}")
        srcs[key] = Src("wikidata", f"wdqs@{at.isoformat()}Z", WIKIDATA_URL + " (SPARQL: " + q.split("WHERE")[0].strip() + ")", b, at)
    try:
        srcs["openalex"] = await read_source(context, "openalex", "api", OPENALEX_URL, tries=3)
    except Exception:
        pass  # context only; recorded as unmeasured

    # Wikipedia: every edition in the site matrix, polite pacing.
    sm = json.loads(srcs["sitematrix"].body.decode("utf-8"))["sitematrix"]
    editions: list[tuple[str, str]] = []
    for k, v in sm.items():
        if k in ("count", "specials"):
            continue
        for s in v.get("site", []):
            if s.get("code") == "wiki":
                editions.append((v["code"], s["url"]))
    sem = asyncio.Semaphore(4)
    wiki: dict[str, tuple[SimpleNamespace, dict]] = {}
    failures: list[str] = []

    async def one(code: str, base: str) -> None:
        url = base + "/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json&maxlag=5"
        async with sem:
            try:
                b, at, status = await fetch_bytes(context, url, timeout=60.0)
                st = json.loads(b.decode("utf-8"))["query"]["statistics"]
                wiki[code] = (Src("wikimedia-siteinfo", f"live@{at.date().isoformat()}", url, b, at), st)
            except Exception as exc:
                failures.append(f"{code}: {exc!r}")
            await asyncio.sleep(0.25)

    await asyncio.gather(*(one(c, u) for c, u in editions))
    if failures:
        # An edition that exists but could not be read must not read as observed_absent.
        raise RuntimeError(f"Wikipedia editions could not be read: {failures}")

    run_at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    yield run_model(srcs, wiki, {}, run_at, False)
    await ol_task
    yield run_model(srcs, wiki, ol, run_at, True)
