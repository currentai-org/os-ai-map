#!/usr/bin/env python3
"""Generate notebooks/ai-stack-map.py, the three-axis openness map, in the
ai-stack-map.py editorial house style. Static-export friendly: data is embedded;
interactivity is the JS Details drawer + a JS type-toggle (no kernel)."""
import json
import markdown
import re
import yaml

from build.vocabulary import axes

from pathlib import Path

# Repo root is the parent of build/. Read the serialized payload from
# build/notebook_data.json and write the rendered notebook to notebooks/.
ROOT = Path(__file__).resolve().parents[1]
OUT = str(ROOT / "notebooks" / "ai-stack-map.py")
data = json.load(open(ROOT / "build" / "notebook_data.json"))
data_json = json.dumps(data, ensure_ascii=False)
DATA_LITERAL = repr(data_json)  # safe Python string literal for json.loads(...)

# Read straplines and weights from sources/categories/<cid>.yaml at render time
# so the NB template no longer contains hardcoded literals.
_cats_yaml = {
    _f.stem: _c
    for _f in sorted((ROOT / "sources" / "categories").glob("*.yaml"))
    for _c in [yaml.safe_load(_f.read_text())]
}
_ORDER = data["order"]  # canonical key order, must match the notebook dict order


def _build_straplines_literal(order, cats):
    """Emit a dict literal for the generated notebook.

    Values go through json.dumps, not f-string interpolation. A strapline is
    contributor-authored prose, so one apostrophe-free quote - `the "open" frontier` -
    used to close the literal early and produce a notebook that will not parse. CI
    serializes but did not render, so that broke after merge rather than in review.
    json output is a valid Python string literal for any input, which is the same
    reason DATA_LITERAL already uses repr.
    """
    lines = ["{\n"]
    for cid in order:
        strap = cats[cid]["strapline"]
        lines.append(f"        {json.dumps(cid)}: {json.dumps(strap)},\n")
    lines.append("    }")
    return "".join(lines)


def _build_layer_weights_literal(order, cats):
    lines = ["{\n"]
    for cid in order:
        adopt = cats[cid]["weights"]["adopt"]
        cap = cats[cid]["weights"]["cap"]
        lines.append(f'        "{cid}": ({adopt}, {cap}),\n')
    lines.append("    }")
    return "".join(lines)


STRAPLINES_LITERAL = _build_straplines_literal(_ORDER, _cats_yaml)
LAYER_WEIGHTS_LITERAL = _build_layer_weights_literal(_ORDER, _cats_yaml)


# Methodology copy lives in docs/methodology.md (hand-authored, canonical). We
# substitute the {placeholders} with live counts from the payload so the prose can
# never drift, split the Summary and Detail sections, and convert Markdown -> HTML.
# The Summary feeds the header; the Detail feeds the Methodology section.
def _methodology_numbers(d):
    _c = d["long_tail"]["counts"]
    _prods = [p for _cat in d["categories"].values() for p in _cat["products"]]
    _urls = [
        s.get("url")
        for p in _prods
        for _axis in axes()
        for s in ((p.get(_axis) or {}).get("sources") or [])
        if s.get("url")
    ]

    def _dom(u):
        return u.split("//", 1)[-1].split("/", 1)[0].removeprefix("www.")

    def _count_type(t):
        return sum(1 for p in _prods if p.get("type") == t)

    return {
        "total": f'{_c["total"]:,}',
        "scored": f'{_c["scored"]:,}',
        "uncategorized": f'{_c["uncategorized"]:,}',
        "universe": f'{_c["universe"]:,}',
        "disc_repos": f'{_c["repos"]:,}',
        "disc_models": f'{_c["models"]:,}',
        "disc_packages": f'{_c["packages"]:,}',
        "n_software": f'{_count_type("software"):,}',
        "n_models": f'{_count_type("model"):,}',
        "n_datasets": f'{_count_type("dataset"):,}',
        "n_hardware": f'{_count_type("hardware"):,}',
        "n_orgs": f'{len({p.get("org") for p in _prods if p.get("org")}):,}',
        "n_categories": f'{len(d["order"]):,}',
        "n_openness_gaps": str(sum(1 for _cat in d["categories"].values()
                                   if "openness" in (_cat.get("gaps") or []))),
        "n_layers": str(len({_cat.get("arc") for _cat in d["categories"].values()})),
        "n_citations": f'{len(_urls):,}',
        "n_domains": f'{len({_dom(u) for u in _urls}):,}',
    }


def _methodology_split(text):
    # Drop a leading HTML comment (build notes) so its content never renders, then
    # split on the two top-level headings by POSITION: the first "## " section is the
    # summary (-> notebook header), the second is the body (-> Methodology section).
    # Match only line-start "## " (the (?m)^ anchor), so a "## " appearing mid-line
    # inside prose or the comment is ignored, and either heading can be renamed freely.
    text = re.sub(r"\A\s*<!--.*?-->\s*", "", text, flags=re.DOTALL)
    _heads = [m.start() for m in re.finditer(r"(?m)^## ", text)]
    _summary = text[text.index("\n", _heads[0]) + 1:_heads[1]].strip()
    _body = text[text.index("\n", _heads[1]) + 1:].strip()
    return _summary, _body


_method_md = (ROOT / "docs" / "methodology.md").read_text(encoding="utf-8")
for _k, _v in _methodology_numbers(data).items():
    _method_md = _method_md.replace("{" + _k + "}", _v)
_leftover = [t for t in ("{total}", "{scored}", "{n_orgs}", "{n_citations}") if t in _method_md]
assert not _leftover, f"unsubstituted methodology placeholders: {_leftover}"

_summary_md, _detail_md = _methodology_split(_method_md)
_md = markdown.Markdown(extensions=["extra"])
_summary_html = _md.convert(_summary_md)
if _summary_html.startswith("<p>") and _summary_html.endswith("</p>"):
    _summary_html = _summary_html[3:-4]  # inject inner HTML into the header's styled <p>
_md.reset()
_method_html = _md.convert(_detail_md)
SUMMARY_HTML_LITERAL = repr(_summary_html)
METHOD_HTML_LITERAL = repr(_method_html)


NB = '''import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def load_fonts(mo):
    mo.Html(
        '<style>'
        '@import url("https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300;1,400;1,500&family=Noto+Serif:ital,wght@0,400;0,600;1,400&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap");'
        '</style>'
    )
    return


@app.cell(hide_code=True)
def style():
    F = {
        "headline": "'Noto Serif', Georgia, serif",
        "body": "'Plus Jakarta Sans', -apple-system, system-ui, sans-serif",
        "mono": "'DM Mono', ui-monospace, SFMono-Regular, monospace",
    }
    C = {
        "ink": "#0b252f", "ink_2": "#272726", "ink_3": "#8fa1a4",
        "paper": "#f7f6f6", "paper_2": "#f2f1f1", "rule": "#edecec",
        # Openness: a single-hue salmon ramp, deepest = most open, fading to a
        # pale (but still legible) tint for closed. Monotonic lightness, so it
        # reads as one ordered scale; brand salmon sits mid-ramp and open
        # products carry the most color.
        "healthy": "#e86f57",   # open        — deep salmon
        "warm": "#f4886f",      # open-ish    — salmon (brand-adjacent)
        "signal": "#f8ad99",    # restricted  — light coral
        "closed": "#f6cabd",    # closed      — pale coral
        "null": "#dcdcda",      # no score    — neutral grey (off the ramp)
        # Structure + the two magnitude axes — a quiet cool pair so the openness
        # column is where color lives.
        "accent": "#0b252f",    # navy — eyebrows, rules, active controls
        "adopt": "#8aa6ac",     # adoption bar   — light slate
        "capab": "#3f5d68",     # capability bar — dark slate
        "white": "#ffffff", "border": "#a5bbbe", "gap_red": "#ff0d0d",
    }
    # Openness class -> (label, 0-5 score for bar fill, color key). Unifies the
    # model / software / dataset class vocabularies onto one openness gradient.
    OPEN = {
        "open_source": ("Open source", 5, "healthy"),
        "open": ("Open data", 5, "healthy"),
        "open_weights": ("Open weights", 3, "warm"),
        "open_core": ("Open core", 4, "healthy"),
        "source_available": ("Source available", 2, "signal"),
        "restricted": ("Restricted", 2, "signal"),
        "gated": ("Gated", 2, "warm"),
        "closed": ("Closed", 1, "ink_3"),
        "open_hardware": ("Open hardware", 5, "healthy"),
        "open_toolchain": ("Open toolchain", 3, "warm"),
        "documented": ("Documented", 2, "signal"),
    }
    # Openness verdict code -> (label, color key into C). Colors match the
    # count chips (open=green, open-ish=orange, closed=red) so the badge
    # reinforces the chips; competitive is the neutral accent.
    VERDICT = {
        "open_leads": ("Open leads", "healthy"),
        "openish_leads": ("Open-ish leads", "warm"),
        "closed_leads": ("Closed leads", "closed"),
        "competitive": ("Competitive", "capab"),
        "none": ("No standout", "null"),
    }
    return C, F, OPEN, VERDICT


@app.cell(hide_code=True)
def data():
    import json
    DATA = json.loads(__DATA_LITERAL__)
    ORDER = DATA["order"]
    STRAPLINES = __STRAPLINES__
    # Neutral one-line definitions for the at-a-glance overview (what the category
    # IS, vs the strapline which is the finding). Sourced from the payload's
    # descriptions.categories (ultimately sources/categories/<cid>.yaml), so the
    # wording lives in one place.
    STACK_DESC = DATA["descriptions"]["categories"]
    # Per-category combined-score weights (adoption, capability), ported from the
    # v2 stack map (slugs identical). Feed the "standout product" gate behind the
    # openness verdict; the table also shows the blended score.
    LAYER_WEIGHTS = __LAYER_WEIGHTS__
    # Framework white-space: homes in the Columbia/MOF openness stack that the
    # the categories above do NOT cover. Rendered by the framework_edges cell as a
    # scope statement (the vertical edge of the map, paired with the long tail).
    FRAMEWORK_EDGES = [
        ("Model", [
            ("Training datasets",
             "The corpora models are trained on. We cover evaluation datasets only."),
            ("Data-prep and pretraining code",
             "Dataset-construction and curation pipelines, plus train-from-scratch "
             "code. We cover fine-tuning, inference, and evaluation code."),
            ("Supporting libraries",
             "Tokenizers, kernels, and data loaders beneath the training and "
             "inference code."),
        ]),
        ("System", [
            ("Infrastructure",
             "Compute, training frameworks, and low-level serving runtimes. The "
             "framework places this layer below product/UX, while our five system "
             "categories all sit in product/UX."),
        ]),
        ("Cross-cutting", [
            ("Documentation",
             "Model cards, data cards, and technical reports as tracked artifacts. "
             "Today they inform a model's openness score rather than standing as "
             "their own category."),
            ("Safeguards",
             "Safety, guardrail, and red-teaming tooling."),
        ]),
    ]
    return DATA, ORDER, STRAPLINES, STACK_DESC, LAYER_WEIGHTS, FRAMEWORK_EDGES


@app.cell(hide_code=True)
def verdict_logic(DATA, LAYER_WEIGHTS):
    # Shared openness-verdict logic, consumed by the hero scorecard, the
    # at-a-glance overview, and each section. Strict OSI/MOF cut:
    #   open    = open_source / open / open_core
    #   openish = open_weights / source_available / gated
    #   closed  = restricted / documented / closed
    _OPEN = {"open_source", "open", "open_core", "open_hardware"}
    _OPENISH = {"open_weights", "source_available", "gated", "open_toolchain"}

    def vbucket(cls):
        if cls in _OPEN:
            return "open"
        if cls in _OPENISH:
            return "openish"
        return "closed"

    def bucket_counts(cid, standout_only):
        wa, wc = LAYER_WEIGHTS.get(cid, (0.5, 0.5))
        n = {"open": 0, "openish": 0, "closed": 0}
        for p in DATA["categories"][cid]["products"]:
            if standout_only:
                ad = (p.get("adoption") or {}).get("level")
                cap = (p.get("capability") or {}).get("score")
                if ad is None or cap is None:
                    continue
                if wa * ad + wc * cap < 4.0:
                    continue
            n[vbucket((p.get("openness") or {}).get("class"))] += 1
        return n

    def verdict_for(cid):
        # Which tier leads among the category's STANDOUT products only (blended
        # adoption x capability >= 4, weighted by layer). A bucket "leads" only if
        # it beats the runner-up by >= 10 points; else "competitive". A category
        # with no product above the bar reads "none".
        n = bucket_counts(cid, True)
        tot = sum(n.values())
        if tot == 0:
            return "none", "standout"
        ranked = sorted(n.items(), key=lambda kv: -kv[1])
        (lk, lv), (sk, sv) = ranked[0], ranked[1]
        if lv > sv and (lv / tot - sv / tot) >= 0.10:
            code = {"open": "open_leads", "openish": "openish_leads", "closed": "closed_leads"}[lk]
        else:
            code = "competitive"
        return code, "standout"

    def mix_counts(cid):
        # Full-population openness mix (every product), used for the visible chips.
        return bucket_counts(cid, False)

    return mix_counts, vbucket, verdict_for


@app.cell(hide_code=True)
def header(C, F, mo):
    # Summary prose is authored in docs/methodology.md (## Summary) and injected
    # here as HTML with the live counts already substituted; see build/render.py.
    mo.Html(
        f'<div style="padding:40px 0 28px; border-bottom:2px solid {C["accent"]}; margin-bottom:36px;">'
        f'<h1 style="font-family:{F["headline"]}; font-size:2.2rem; font-weight:600; '
        f'color:{C["ink"]}; margin:0 0 14px; line-height:1.05; letter-spacing:-0.025em;">'
        f'Open Source AI Map</h1>'
        f'<p class="v3-sum" style="font-family:{F["body"]}; font-size:1rem; color:{C["ink_2"]}; '
        f'margin:0; line-height:1.5;">'
        + __SUMMARY_HTML__
        + '</p></div>'
    )
    return


@app.cell(hide_code=True)
def stack_overview(C, DATA, F, ORDER, STACK_DESC, mix_counts, mo):
    # Category labels and descriptions are contributor-authored and land in HTML bodies.
    # `ornith`'s description contains a literal <think>, which the browser silently
    # swallows as an unknown element, so today the published map drops that word.
    import html as _html
    # The at-a-glance roster: every category as a row, grouped by arc, with the
    # full openness-mix count chips.
    _rows = []
    _last_arc = None
    for _cid in ORDER:
        _cat = DATA["categories"][_cid]
        _arc = _cat["arc"]
        if _arc != _last_arc:
            _bt = "none" if _last_arc is None else f"1px solid {C['rule']}"
            _mt = "8px" if _last_arc is None else "22px"
            _rows.append(
                f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
                f'letter-spacing:0.14em; text-transform:uppercase; margin:{_mt} 0 6px; '
                f'padding-top:12px; border-top:{_bt};">{_arc}</div>'
            )
            _last_arc = _arc
        _m = mix_counts(_cid)
        _chips = (
            f'<span style="color:{C["healthy"]};">\\u25cf</span> {_m["open"]} open'
            f'&nbsp;&nbsp;<span style="color:{C["warm"]};">\\u25cf</span> {_m["openish"]} open-ish'
            f'&nbsp;&nbsp;<span style="color:{C["closed"]};">\\u25cf</span> {_m["closed"]} closed'
        )
        _rows.append(
            f'<div style="display:grid; grid-template-columns:1fr 232px; gap:18px; '
            f'align-items:center; padding:14px 0; border-bottom:1px solid {C["rule"]};">'
            f'<div><div style="font-family:{F["headline"]}; font-size:1.05rem; font-weight:600; '
            f'color:{C["ink"]}; line-height:1.2;">{_html.escape(str(_cat["label"]))}</div>'
            f'<div style="font-family:{F["body"]}; font-size:0.85rem; color:{C["ink_3"]}; '
            f'margin-top:3px; line-height:1.4;">{_html.escape(str(STACK_DESC.get(_cid, "")))}</div></div>'
            f'<div style="font-family:{F["mono"]}; font-size:0.74rem; color:{C["ink_2"]};">{_chips}</div>'
            f'</div>'
        )
    _total = DATA.get("n_total") or sum(len(DATA["categories"][c]["products"]) for c in ORDER)
    _n_arcs = len({DATA["categories"][c]["arc"] for c in ORDER})
    mo.Html(
        f'<div style="margin:0 0 52px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">The stack at a glance</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600; color:{C["ink"]}; '
        f'margin:0 0 14px; letter-spacing:-0.015em;">'
        f'{_n_arcs} layers, {len(ORDER)} categories, {_total} scored products</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.95rem; color:{C["ink_2"]}; margin:0 0 20px; line-height:1.6;">'
        f'Each row is one category, grouped into three layers. The dots show the openness mix of all its '
        f'products. Open in the long tail and closed at the '
        f'top can coexist, and that gap is the point.</p>'
        f'{"".join(_rows)}</div>'
    )
    return


@app.cell(hide_code=True)
def openness_distribution(C, DATA, F, mo):
    import collections as _collections
    def _ccol(_cls):
        if _cls in ("open_source", "open", "open_hardware"):
            return C["healthy"]
        if _cls in ("open_weights", "open_core", "open_toolchain"):
            return C["warm"]
        if _cls in ("restricted", "source_available", "gated", "documented"):
            return C["signal"]
        return C["closed"]
    _CLS_ORDER = ["open_source", "open", "open_hardware", "open_core", "open_weights", "open_toolchain", "source_available", "gated", "documented", "restricted", "closed"]
    _bars = []
    for _tk, _tl in [("model", "Models"), ("dataset", "Datasets"), ("software", "Software"), ("hardware", "Hardware")]:
        _cnt = _collections.Counter()
        for _cat in DATA["categories"].values():
            for _p in _cat["products"]:
                if _p.get("type") == _tk:
                    _cnt[(_p.get("openness") or {}).get("class")] += 1
        _tot = sum(_cnt.values()) or 1
        _segs = ""
        for _cls in _CLS_ORDER:
            _nc = _cnt.get(_cls, 0)
            if _nc:
                _segs += f'<div title="{_cls}: {_nc}" style="width:{100 * _nc / _tot:.1f}%; background:{_ccol(_cls)}; height:22px;"></div>'
        _bars.append(
            f'<div style="display:grid; grid-template-columns:84px 1fr 44px; gap:12px; align-items:center; margin:8px 0;">'
            f'<div style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink"]}; font-weight:600;">{_tl}</div>'
            f'<div style="display:flex; border-radius:0; overflow:hidden;">{_segs}</div>'
            f'<div style="font-family:{F["mono"]}; font-size:0.78rem; color:{C["ink_3"]}; text-align:right;">{_tot}</div>'
            f'</div>'
        )
    _legend = "".join(
        f'<span style="display:inline-flex; align-items:center; margin-right:16px; font-family:{F["body"]}; font-size:0.78rem; color:{C["ink_3"]};">'
        f'<span style="width:11px; height:11px; background:{_col}; border-radius:0; display:inline-block; margin-right:5px;"></span>{_lab}</span>'
        for _lab, _col in [("Open source / data", C["healthy"]), ("Open weights / core", C["warm"]), ("Restricted / gated", C["signal"]), ("Closed", C["closed"])]
    )
    mo.Html(
        f'<div style="margin:0 0 44px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; letter-spacing:0.1em; '
        f'text-transform:uppercase; margin-bottom:10px;">Openness by product type</div>'
        f'{"".join(_bars)}'
        f'<div style="margin-top:12px;">{_legend}</div>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def filter_sort_controls(mo):
    # JS-driven filter + sort controller. Works in static HTML, where marimo
    # reactivity and <script> tags are stripped — so the logic is injected via an
    # iframe onload handler that runs in the parent document context.
    #
    # Three filters (openness bucket, min adoption, min capability) intersect, and
    # a sort selector re-orders the surviving rows within each category table.
    # Operates only on category rows (tr[data-open]); the long-tail table uses
    # data-lttype and is untouched. A category whose rows all filter out collapses
    # its whole cell so no orphaned header/callout is left over an empty table.
    _css = (
        "<style>"
        ".v3ctrl-bar .v3ctrl-lbl{font-family:'DM Mono',ui-monospace,monospace;font-size:10px;"
        "color:#a5bbbe;letter-spacing:0.08em;text-transform:uppercase;margin-right:10px;}"
        ".v3ctrl-bar button{font-family:'DM Mono',ui-monospace,monospace;font-size:11px;"
        "border:1px solid #a5bbbe;background:#fff;color:#0b252f;border-radius:0;"
        "padding:5px 12px;cursor:pointer;margin-right:6px;letter-spacing:0.04em;text-transform:uppercase;}"
        ".v3ctrl-bar button.active{background:#0b252f;color:#f2f1f1;border-color:#0b252f;}"
        "</style>"
    )

    def _group(group, label, opts, active):
        btns = "".join(
            '<button data-v="' + v + '" class="'
            + ("active" if v == active else "") + '">' + lab + "</button>"
            for v, lab in opts
        )
        return (
            '<div data-group="' + group + '" '
            'style="display:flex; align-items:center; flex-wrap:wrap;">'
            '<span class="v3ctrl-lbl">' + label + "</span>" + btns + "</div>"
        )

    # "All" maps to -1 (not 0) so it imposes no constraint and keeps rows whose
    # score is null (rendered as data-* = -1); the 2+..5 thresholds exclude nulls.
    _levels = [("-1", "All"), ("2", "2+"), ("3", "3+"), ("4", "4+"), ("5", "5")]
    _bar = (
        '<div class="v3ctrl-bar" style="margin:0 0 24px; display:flex; '
        'flex-wrap:wrap; gap:14px 28px; align-items:center;">'
        + _group("openness", "Filter by openness",
                 [("all", "All"), ("open", "Open"), ("openish", "Open-ish"),
                  ("closed", "Closed")], "all")
        + _group("adopt", "Min adoption", _levels, "0")
        + _group("cap", "Min capability", _levels, "0")
        + _group("sort", "Sort by",
                 [("openness", "Openness"), ("adoption", "Adoption"),
                  ("capability", "Capability")], "openness")
        + "</div>"
    )

    _js = (
        "(function(){"
        "var bar=document.querySelector('.v3ctrl-bar');if(!bar)return;"
        "var state={openness:'all',adopt:-1,cap:-1,sort:'openness'};"
        "var keymap={openness:'data-openness',adoption:'data-adopt',capability:'data-cap'};"
        "var axes=['data-openness','data-adopt','data-cap'];"
        "function num(r,k){return parseFloat(r.getAttribute(k));}"
        "function apply(){"
        "var rows=document.querySelectorAll('tr[data-open]');var bodies=[];"
        "rows.forEach(function(r){"
        "var ok=(state.openness==='all'||r.getAttribute('data-open')===state.openness)"
        "&&num(r,'data-adopt')>=state.adopt&&num(r,'data-cap')>=state.cap;"
        "r.style.display=ok?'':'none';"
        "if(bodies.indexOf(r.parentNode)===-1)bodies.push(r.parentNode);});"
        "var key=keymap[state.sort];"
        "var order=[key].concat(axes.filter(function(k){return k!==key;}));"
        "bodies.forEach(function(tb){"
        "var vis=[].slice.call(tb.querySelectorAll('tr[data-open]'))"
        ".filter(function(r){return r.style.display!=='none';});"
        "vis.sort(function(a,b){var d=0;order.some(function(k){"
        "var x=num(b,k)-num(a,k);if(x){d=x;return true;}return false;});return d;});"
        "vis.forEach(function(r){tb.appendChild(r);});"
        "var cell=tb.closest('.marimo-cell');if(cell)cell.style.display=vis.length?'':'none';});"
        "}"
        "bar.addEventListener('click',function(e){"
        "var b=e.target.closest('button');if(!b)return;"
        "var g=b.closest('[data-group]');if(!g)return;"
        "var grp=g.getAttribute('data-group');var v=b.getAttribute('data-v');"
        "if(grp==='openness'){state.openness=v;}"
        "else if(grp==='adopt'){state.adopt=parseFloat(v);}"
        "else if(grp==='cap'){state.cap=parseFloat(v);}"
        "else if(grp==='sort'){state.sort=v;}"
        "g.querySelectorAll('button').forEach(function(x){x.classList.toggle('active',x===b);});"
        "apply();});"
        "})();"
    )
    _enc = _js.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    mo.Html(
        _css + _bar + f'<iframe srcdoc="&lt;!doctype html&gt;&lt;html&gt;&lt;/html&gt;" '
        f'style="display:none;width:0;height:0;border:0;position:absolute" '
        f'onload="{_enc}"></iframe>'
    )
    return


@app.cell(hide_code=True)
def helpers(C, DATA, F, OPEN, STRAPLINES, VERDICT, mix_counts, mo, vbucket,
            verdict_for):
    import html as _html  # product display names are contributor-authored
    def _oscore(p):
        return (p.get("openness") or {}).get("score")

    def _ocolor(score):
        if score is None:
            return C["null"]
        if score >= 4:
            return C["healthy"]   # salmon — open
        if score == 3:
            return C["warm"]      # light coral — open-ish
        if score == 2:
            return C["signal"]    # mid slate — restricted
        return C["closed"]        # dark slate — closed

    def _bars(value, on_color):
        v = int(value) if isinstance(value, (int, float)) else 0
        return "".join(
            f'<span style="display:inline-block; width:6px; height:14px; margin-right:2px; '
            f'vertical-align:middle; background:{on_color if j < v else C["rule"]};"></span>'
            for j in range(5)
        )

    def na_html():
        return f'<span style="color:{C["ink_3"]}; font-style:italic;">n/a</span>'

    def openness_cell(op):
        sc = op.get("score")
        cls = op.get("class")
        label = OPEN.get(cls, (cls or "?", 1, "ink_3"))[0]
        col = _ocolor(sc)
        if sc is None:
            return na_html()
        return (
            f'<div style="white-space:nowrap;">{_bars(sc, col)} '
            f'<span style="font-family:{F["mono"]}; font-size:10px; color:{col}; '
            f'margin-left:4px; text-transform:uppercase; letter-spacing:0.03em;">{label}</span></div>'
        )

    def axis_bars(obj, key, color):
        v = obj.get(key)
        if v is None:
            return na_html()
        return f'<div style="white-space:nowrap;">{_bars(v, color)}</div>'

    def product_row(p):
        pid = p.get("product", "")
        op, ad, cap = p.get("openness", {}), p.get("adoption", {}), p.get("capability", {})
        _name = p.get("product", "")
        _ob = vbucket(op.get("class"))
        # Numeric axis values for the JS filter/sort controller; null -> -1 so the
        # row sorts last and fails every "min" threshold.
        _osc = op.get("score")
        _adl = ad.get("level")
        _cpc = cap.get("score")
        return (
            f'<tr data-open="{_ob}" data-type="{p.get("type","")}" '
            f'data-openness="{-1 if _osc is None else _osc}" '
            f'data-adopt="{-1 if _adl is None else _adl}" '
            f'data-cap="{-1 if _cpc is None else _cpc}" '
            f'style="border-bottom:1px solid {C["paper_2"]};">'
            f'<td style="padding:8px 10px; font-family:{F["body"]}; font-size:0.86rem; color:{C["ink"]};">{_html.escape(str(_name))}</td>'
            f'<td style="padding:8px 10px; font-family:{F["body"]}; font-size:0.78rem; color:{C["ink_3"]};">{p.get("org","") or ""}</td>'
            f'<td style="padding:8px 10px;">{openness_cell(op)}</td>'
            f'<td style="padding:8px 10px;">{axis_bars(ad, "level", C["adopt"])}</td>'
            f'<td style="padding:8px 10px;">{axis_bars(cap, "score", C["capab"])}</td>'
            f'<td style="padding:8px 10px;"><button class="v3-details" data-pid="{pid}">Details</button></td>'
            f'</tr>'
        )

    def _dominant_type(cid):
        counts = {}
        for p in DATA["categories"][cid]["products"]:
            t = p.get("type")
            counts[t] = counts.get(t, 0) + 1
        return max(counts.items(), key=lambda kv: kv[1])[0] if counts else "software"

    def _openness_basis(cid):
        return {
            "model": "the Model Openness Framework (weights, data, code, license)",
            "software": "OSI-class license tests",
            "dataset": "data-openness (access, license, and documentation)",
            "hardware": "open-hardware tests (design files, toolchain, and availability)",
        }.get(_dominant_type(cid), "OSI-class license tests")

    def _cap_summary(cid):
        seen = {}
        fm = 0
        for p in DATA["categories"][cid]["products"]:
            b = (p.get("capability") or {}).get("basis") or ""
            if b.startswith("benchmark:"):
                rest = b.split("benchmark:", 1)[1].strip()
                if rest in ("", "n/a"):
                    continue
                for nm in rest.split("/"):
                    nm = nm.strip()
                    if nm and nm.lower() != "n/a":
                        seen[nm] = seen.get(nm, 0) + 1
            elif b == "feature_matrix":
                fm += 1
        top = ", ".join(k for k, _ in sorted(seen.items(), key=lambda kv: -kv[1])[:3])
        if _dominant_type(cid) == "dataset" and not top and not fm:
            return "a secondary axis here, since datasets are graded mainly on openness and adoption"
        if top and fm:
            return f"benchmarks ({top}); a feature matrix where none exist"
        if top:
            return f"benchmarks: {top}"
        if fm:
            return "a feature matrix (no standard benchmark exists)"
        return "expert judgment where no public benchmark exists"

    def _category_sources(cid, limit=8):
        # Distinct source domains used across the category's products, capability
        # sources first (the benchmarks), then openness, then adoption. One
        # representative URL per domain.
        seen = {}
        for axis in ("capability", "openness", "adoption"):
            for p in DATA["categories"][cid]["products"]:
                for s in (p.get(axis) or {}).get("sources") or []:
                    u = s.get("url") or ""
                    if not u:
                        continue
                    dom = u.split("//", 1)[-1].split("/", 1)[0]
                    if dom.startswith("www."):
                        dom = dom[4:]
                    if dom and dom not in seen:
                        seen[dom] = u
        return list(seen.items())[:limit]

    def _scoring_callout(cid):
        _srcs = _category_sources(cid)
        _src_html = ""
        if _srcs:
            _links = ", ".join(
                f'<a href="{_u.replace("&", "&amp;")}" target="_blank" rel="noopener" '
                f'style="color:{C["accent"]}; text-decoration:none;">{_dom}</a>'
                for _dom, _u in _srcs
            )
            _src_html = (
                f'<div style="font-family:{F["mono"]}; font-size:9px; color:{C["ink_3"]}; '
                f'letter-spacing:0.08em; text-transform:uppercase; margin:12px 0 4px;">Sources used</div>'
                f'<div style="font-family:{F["body"]}; font-size:0.82rem; line-height:1.7;">{_links}</div>'
            )
        return (
            f'<div style="margin:4px 0 16px; padding:14px 18px; background:{C["paper_2"]};">'
            f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["ink_3"]}; '
            f'letter-spacing:0.12em; text-transform:uppercase; margin-bottom:8px;">How this was scored</div>'
            f'<ul style="font-family:{F["body"]}; font-size:0.88rem; color:{C["ink_2"]}; '
            f'margin:0; padding-left:18px; line-height:1.55;">'
            f'<li style="margin:0 0 6px;"><strong>Openness:</strong> graded with {_openness_basis(cid)}.</li>'
            f'<li style="margin:0 0 6px;"><strong>Adoption:</strong> real usage '
            f'(downloads, active users, deployments); GitHub stars capped at level 3.</li>'
            f'<li><strong>Capability:</strong> {_cap_summary(cid)}.</li>'
            f'</ul>{_src_html}</div>'
        )

    def _verdict_spine(cid):
        # Openness verdict pill, then the open / open-ish / closed dot tally.
        _code, _basis = verdict_for(cid)
        _vlabel, _ = VERDICT[_code]
        # The verdict is a categorical call, not an ordinal one, so color-coding it
        # fought the openness ramp (open-ish vs closed read alike, and competitive /
        # no-standout fall off the ramp). Keep it a neutral tag; the color story
        # lives in the open / open-ish / closed chips beside it.
        _verdict = (
            f'<span style="display:inline-block; font-family:{F["mono"]}; font-size:0.72rem; '
            f'letter-spacing:0.05em; text-transform:uppercase; color:{C["ink"]}; '
            f'background:{C["paper_2"]}; padding:4px 10px; border-radius:0;">{_vlabel}</span>'
        )
        _m = mix_counts(cid)
        _tally = (
            f'<span style="color:{C["healthy"]};">\\u25cf</span> {_m["open"]} open'
            f'&nbsp;&nbsp;<span style="color:{C["warm"]};">\\u25cf</span> {_m["openish"]} open-ish'
            f'&nbsp;&nbsp;<span style="color:{C["closed"]};">\\u25cf</span> {_m["closed"]} closed'
        )
        return (
            f'<div style="margin:4px 0 12px;">{_verdict}'
            f'<span style="font-family:{F["mono"]}; font-size:0.78rem; color:{C["ink_2"]}; '
            f'margin-left:14px;">{_tally}</span></div>'
        )

    def render_section(cid, num):
        cat = DATA["categories"][cid]
        _order = DATA["order"]
        _idx = _order.index(cid)
        _arc = cat["arc"]
        _first_in_arc = _idx == 0 or DATA["categories"][_order[_idx - 1]]["arc"] != _arc
        _archead = ""
        if _first_in_arc:
            _archead = (
                f'<div style="margin:44px 0 0; padding:14px 0 8px; border-top:1px solid {C["rule"]};">'
                f'<div style="font-family:{F["mono"]}; font-size:11px; color:{C["accent"]}; '
                f'letter-spacing:0.14em; text-transform:uppercase;">{_arc}</div></div>'
            )
        _strap = STRAPLINES.get(cid, "")
        prods = sorted(
            cat["products"],
            key=lambda p: (-((p.get("openness") or {}).get("score") or 0),
                           -((p.get("adoption") or {}).get("level") or 0),
                           -((p.get("capability") or {}).get("score") or 0)),
        )
        rows = "".join(product_row(p) for p in prods)
        head = "".join(
            f'<th style="padding:7px 10px; font-family:{F["mono"]}; font-size:9px; '
            f'color:{C["ink_3"]}; text-transform:uppercase; letter-spacing:0.05em; text-align:left;">{h}</th>'
            for h in ["Product", "Org", "Openness", "Adoption", "Capability", ""]
        )
        return mo.Html(
            _archead
            + f'<div style="margin:28px 0 18px;">'
            f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
            f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">{cat["arc"]}</div>'
            f'<h2 style="font-family:{F["headline"]}; font-size:1.4rem; font-weight:600; '
            f'color:{C["ink"]}; margin:0 0 8px;">{cat["label"]} '
            f'<span style="font-family:{F["mono"]}; font-size:0.8rem; color:{C["ink_3"]};">({len(prods)})</span></h2>'
            f'<p style="font-family:{F["body"]}; font-size:0.98rem; font-weight:600; color:{C["ink_2"]}; '
            f'margin:0 0 10px; line-height:1.45;">{_strap}</p>'
            + _verdict_spine(cid)
            + _scoring_callout(cid)
            + f'<table style="border-collapse:collapse; width:100%;">'
            f'<thead><tr style="border-bottom:2px solid {C["rule"]};">{head}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
        )

    return (render_section,)


__SECTION_CELLS__


@app.cell(hide_code=True)
def details_payload(DATA, ORDER, mo):
    import base64 as _b64
    import json as _json
    # Build a per-product payload keyed by product name, then install a delegated
    # click handler + modal via a hidden-iframe onload bootstrap (marimo strips
    # <script>, so we inject through the iframe into the parent document).
    # Only what the modal reads, built by build/details_payload.py so the size test can
    # import and measure the real payload rather than a second copy of this expansion.
    from build.details_payload import details_records
    _payload = details_records(DATA, ORDER)
    # Base64, not raw JSON. This payload is interpolated into an HTML *attribute*, so it
    # gets escaped (" -> &quot;), and a single astral character anywhere in it (a Hugging
    # Face emoji, in practice) widens the whole Python string to 4 bytes per character.
    # On 2026-08-18 those two multipliers put this cell's output at 24.5 MB against
    # marimo's 8 MB output_max_bytes; marimo dropped the output silently and every
    # Details button rendered wired to a handler that was never installed. Base64 is pure
    # ASCII -- 1 byte per character, nothing for the attribute escaping to expand, and
    # immune to whatever character lands in a score note next.
    _pj = "'" + _b64.b64encode(
        _json.dumps(_payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii") + "'"
    _css = (
        ".v3-details{padding:3px 9px;font-size:11px;font-family:'DM Mono',ui-monospace,monospace;"
        "border:1px solid #a5bbbe;background:#fff;color:#0b252f;border-radius:0;cursor:pointer;font-weight:500;"
        "letter-spacing:0.04em;text-transform:uppercase;}"
        ".v3-details:hover{background:#0b252f;color:#f2f1f1;}"
        ".v3-bd{position:fixed;inset:0;background:rgba(11,37,47,0.55);z-index:99999;display:flex;"
        "align-items:flex-start;justify-content:center;padding:40px 20px;overflow-y:auto;font-family:'Plus Jakarta Sans',system-ui,sans-serif;}"
        ".v3-modal{background:#fff;border-radius:0;max-width:780px;width:100%;padding:24px 28px;box-shadow:0px 4px 4px 0px rgba(0,0,0,0.05);}"
        ".v3-modal h2{font-family:'Noto Serif',Georgia,serif;font-weight:600;font-size:1.4rem;letter-spacing:-0.015em;margin:0 0 4px;color:#0b252f;}"
        ".v3-x{float:right;cursor:pointer;background:none;border:1px solid #a5bbbe;border-radius:0;padding:4px 10px;font-size:11px;color:#a5bbbe;}"
        ".v3-sect{margin:16px 0 6px;font-family:'DM Mono',ui-monospace,monospace;font-size:10px;text-transform:uppercase;"
        "letter-spacing:0.08em;color:#0b252f;opacity:0.5;font-weight:600;border-bottom:1px solid #edecec;padding-bottom:4px;}"
        ".v3-row{display:flex;gap:14px;margin:5px 0;font-size:13px;color:#272726;}"
        ".v3-lbl{min-width:96px;color:#a5bbbe;font-family:'DM Mono',ui-monospace,monospace;font-size:11px;}"
        ".v3-val{flex:1;line-height:1.45;}"
        ".v3-pill{display:inline-block;padding:2px 8px;border-radius:0;color:#fff;font-size:11px;font-weight:600;}"
        ".v3-modal ul{margin:4px 0;padding-left:20px;font-size:12.5px;color:#272726;line-height:1.5;}"
        ".v3-modal a{color:#0b252f;text-decoration:none;}.v3-modal a:hover{text-decoration:underline;}"
    )
    _js = r\'\'\'
    (function(){
      var dec=function(b){return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(b),function(c){return c.charCodeAt(0);})));};
      if (window.__V3_INSTALLED__) { window.__V3_PAYLOAD__ = dec(__PAYLOAD__); return; }
      window.__V3_INSTALLED__ = true; window.__V3_PAYLOAD__ = dec(__PAYLOAD__);
      var esc=function(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];});};
      function ocol(sc){return sc==null?'#dcdcda':(sc>=4?'#e86f57':(sc==3?'#f4886f':(sc==2?'#f8ad99':'#f6cabd')));}
      function otext(sc){return '#0b252f';}
      function srcs(a){if(!a||!a.length)return '<span style="color:#a5bbbe">no sources</span>';
        return '<ul>'+a.map(function(s){var u=s&&s.url?s.url:'';var sh=s&&s.shows?s.shows:u;
        return u?'<li><a href="'+esc(u)+'" target="_blank" rel="noopener">'+esc(sh||u)+'</a></li>':'<li>'+esc(sh)+'</li>';}).join('')+'</ul>';}
      function row(l,v){if(v==null||v==='')v='<em style="color:#a5bbbe">n/a</em>';
        return '<div class="v3-row"><span class="v3-lbl">'+esc(l)+'</span><span class="v3-val">'+(typeof v==='string'&&v.indexOf('<')===0?v:esc(v))+'</span></div>';}
      function build(p){
        var o=p.openness||{},ad=p.adoption||{},cap=p.capability||{};
        var h='<div class="v3-bd"><div class="v3-modal"><button class="v3-x">Close \\u2715</button>'+
          '<h2>'+esc(p.product||'')+'</h2>'+
          '<div style="font-family:\\'DM Mono\\',monospace;font-size:11px;color:#a5bbbe;margin-bottom:6px;">'+
            esc(p.org||'')+', '+esc(p.type||'')+', '+esc(p.category_label||'')+
            (o.class?' <span class="v3-pill" style="background:'+ocol(o.score)+';color:'+otext(o.score)+'">'+esc(o.class)+'</span>':'')+'</div>'+
          (p.description?'<div style="font-size:13px;color:#272726;line-height:1.5;margin:8px 0;">'+esc(p.description)+'</div>':'')+
          (p.version_note?'<div style="font-size:11.5px;color:#a5bbbe;line-height:1.45;margin:6px 0;">'+esc(p.version_note)+'</div>':'')+
          '<div class="v3-sect">Openness '+(o.score==null?'n/a':o.score+'/5')+' ('+esc(o.class||'')+')</div>'+
          row('Components',o.components)+row('Why',o.note)+row('Confidence',o.confidence)+
          '<div class="v3-row"><span class="v3-lbl">Sources</span><span class="v3-val">'+srcs(o.sources)+'</span></div>'+
          '<div class="v3-sect">Adoption '+(ad.level==null?'n/a':ad.level+'/5')+'</div>'+
          row('Reach',ad.reach)+row('Signal',ad.signal_type)+row('Detail',ad.note)+row('Confidence',ad.confidence)+
          '<div class="v3-row"><span class="v3-lbl">Sources</span><span class="v3-val">'+srcs(ad.sources)+'</span></div>'+
          '<div class="v3-sect">Capability '+(cap.score==null?'n/a':cap.score+'/5')+'</div>'+
          row('Basis',cap.basis_detail?cap.basis+': '+cap.basis_detail:cap.basis)+row('Value',cap.value)+row('Detail',cap.note)+row('Confidence',cap.confidence)+
          '<div class="v3-row"><span class="v3-lbl">Sources</span><span class="v3-val">'+srcs(cap.sources)+'</span></div>'+
          (p.lineage?('<div class="v3-sect">Lineage</div>'+
            (p.lineage.derived_from&&p.lineage.derived_from.length?row('Derived from',p.lineage.derived_from.join(', ')):'')+
            (p.lineage.curated_with&&p.lineage.curated_with.length?row('Built with',p.lineage.curated_with.join(', ')):'')+
            (p.lineage.trains&&p.lineage.trains.length?row('Trains',p.lineage.trains.join(', ')):'')):'')+
          '</div></div>';
        return h;
      }
      function open(p){var ex=document.getElementById('__v3_modal');if(ex)ex.remove();
        var r=document.createElement('div');r.id='__v3_modal';r.innerHTML=build(p);document.body.appendChild(r);
        var bd=r.querySelector('.v3-bd');function cl(){r.remove();document.removeEventListener('keydown',ek);}
        function ek(e){if(e.key==='Escape')cl();}
        r.querySelectorAll('.v3-x').forEach(function(b){b.addEventListener('click',cl);});
        if(bd)bd.addEventListener('click',function(e){if(e.target===bd)cl();});
        document.addEventListener('keydown',ek);}
      document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('.v3-details');if(!b)return;
        var p=window.__V3_PAYLOAD__[b.getAttribute('data-pid')];if(p)open(p);});
    })();
    \'\'\'
    _full = ("(function(){if(!window.__V3_CSS__){window.__V3_CSS__=true;var s=document.createElement('style');"
             "s.textContent='" + _css.replace("\\\\", "\\\\\\\\").replace("'", "\\\\'") + "';document.head.appendChild(s);}})();"
             + _js.replace("__PAYLOAD__", _pj))
    _boot = _full.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    mo.Html(
        f'<iframe srcdoc="&lt;!doctype html&gt;&lt;html&gt;&lt;/html&gt;" '
        f'style="display:none;width:0;height:0;border:0;position:absolute" onload="{_boot}"></iframe>'
    )
    return


@app.cell(hide_code=True)
def stages_table(C, DATA, F, ORDER, mo):
    import html as _html  # product display names are contributor-authored
    # The maturity ladder: each category's open ecosystem placed on a 0-5 stage.
    # Only fully-open products count toward a stage (open-ish/closed do not); see
    # docs/reference/gap-analysis.md. Stages + assignments come straight from the payload.
    _DEFS = [
        (0, "Void", "No meaningful open products exist."),
        (1, "Open Experiments", "Open experiments exist, but capability and adoption are both limited."),
        (2, "Emerging Alternatives", "Promising open products exist, but important functionality is missing and adoption is limited."),
        (3, "Viable Alternatives", "Viable open alternatives exist for many use cases."),
        (4, "Competitive Open Ecosystem", "Open solutions are competitive across a broad range of use cases."),
        (5, "Mature Open Ecosystem", "Multiple open solutions are mature, widely adopted, and resilient."),
    ]
    _by_stage = {}
    for _cid in ORDER:
        _sn = (DATA["categories"][_cid].get("stage") or {}).get("num", 0)
        _by_stage.setdefault(_sn, []).append(DATA["categories"][_cid]["label"])

    _rows = []
    for _n, _name, _desc in _DEFS:
        _cats = _by_stage.get(_n, [])
        _cat_html = (
            "".join(
                f'<span style="display:inline-block; font-family:{F["body"]}; font-size:0.82rem; '
                f'color:{C["ink_2"]}; background:{C["paper_2"]}; padding:2px 9px; border-radius:0; '
                f'margin:0 5px 5px 0;">{_l}</span>'
                for _l in _cats
            )
            if _cats
            else f'<span style="font-family:{F["body"]}; font-size:0.82rem; color:{C["ink_3"]}; font-style:italic;">\\u2014</span>'
        )
        _rows.append(
            f'<tr style="border-bottom:1px solid {C["rule"]}; vertical-align:top;">'
            f'<td style="padding:14px 14px 14px 0; white-space:nowrap;">'
            f'<span style="display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; '
            f'box-sizing:border-box; font-family:{F["mono"]}; font-size:0.8rem; font-weight:600; color:{C["ink"]}; '
            f'background:#fff; border:1.5px solid {C["ink"]}; border-radius:50%;">{_n}</span></td>'
            f'<td style="padding:14px 16px 14px 0; font-family:{F["headline"]}; font-size:0.98rem; '
            f'font-weight:600; color:{C["ink"]}; white-space:nowrap;">{_html.escape(str(_name))}</td>'
            f'<td style="padding:14px 16px 14px 0; font-family:{F["body"]}; font-size:0.86rem; '
            f'color:{C["ink_2"]}; line-height:1.45; max-width:300px;">{_desc}</td>'
            f'<td style="padding:14px 0;">{_cat_html}</td>'
            f'</tr>'
        )
    _head = "".join(
        f'<th style="padding:0 16px 8px 0; font-family:{F["mono"]}; font-size:9px; color:{C["ink_3"]}; '
        f'text-transform:uppercase; letter-spacing:0.05em; text-align:left;">{_h}</th>'
        for _h in ["Stage", "", "What it means", "Categories here"]
    )
    mo.Html(
        f'<div style="margin:52px 0 44px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">The maturity ladder</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600; color:{C["ink"]}; '
        f'margin:0 0 14px; letter-spacing:-0.015em;">How mature is the open ecosystem in each category?</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.95rem; color:{C["ink_2"]}; margin:0 0 20px; line-height:1.6;">'
        f'Each category sits on a Void \\u2192 Mature ladder, scored on the depth of its <em>fully-open</em> '
        f'options; open-weights or source-available products do not count toward a stage, only toward '
        f'flagging an openness gap. A category climbs the ladder as more of its open products clear the combined '
        f'adoption\\u00d7capability bar.</p>'
        f'<table style="border-collapse:collapse; width:100%;">'
        f'<thead><tr style="border-bottom:2px solid {C["rule"]};">{_head}</tr></thead>'
        f'<tbody>{"".join(_rows)}</tbody></table></div>'
    )
    return


@app.cell(hide_code=True)
def uncategorized_long_tail(C, DATA, F, mo):
    _lt = DATA["long_tail"]
    _c = _lt["counts"]
    _TC = {"repo": C["border"], "model": C["healthy"], "package": C["warm"], "dataset": C["signal"]}
    _btns = "".join(
        '<button data-ltf="' + _k + '" class="lt-btn' + (' active' if _k == 'all' else '') + '">' + _lab + '</button>'
        for _k, _lab in [("all", "All"), ("repo", "Repos"), ("model", "Models"), ("package", "Packages"), ("dataset", "Datasets")]
    )
    _rows = "".join(
        f'<tr data-lttype="{_t["type"]}" style="border-bottom:1px solid {C["paper_2"]};">'
        f'<td style="padding:7px 10px; font-family:{F["mono"]}; font-size:0.8rem; color:{C["ink"]};">{_t["name"]}</td>'
        f'<td style="padding:7px 10px;"><span style="font-family:{F["mono"]}; font-size:0.64rem; text-transform:uppercase; '
        f'letter-spacing:0.04em; color:{C["ink"]}; background:{_TC.get(_t["type"], C["ink_3"])}; padding:2px 7px; border-radius:0;">{_t["type"]}</span></td>'
        f'<td style="padding:7px 10px; font-family:{F["mono"]}; font-size:0.76rem; color:{C["ink_3"]}; text-align:right; white-space:nowrap;">{_t["usage_label"]}</td>'
        f'<td style="padding:7px 10px; font-family:{F["body"]}; font-size:0.8rem; color:{C["ink_3"]};">{_t["description"]}</td>'
        f'<td style="padding:7px 10px; font-family:{F["mono"]}; font-size:0.66rem; color:{C["rule"]}; text-transform:uppercase; letter-spacing:0.04em;">uncategorized</td>'
        f'</tr>'
        for _t in _lt["top"]
    )
    _head = "".join(
        f'<th style="padding:7px 10px; font-family:{F["mono"]}; font-size:9px; color:{C["ink_3"]}; '
        f'text-transform:uppercase; letter-spacing:0.05em; text-align:{_a};">{_h}</th>'
        for _h, _a in [("Name", "left"), ("Type", "left"), ("Usage", "right"), ("Description", "left"), ("Status", "left")]
    )
    _css = (
        "<style>"
        ".lt-bar .lt-btn{font-family:'DM Mono',ui-monospace,monospace;font-size:11px;border:1px solid #a5bbbe;"
        "background:#fff;color:#0b252f;border-radius:0;padding:4px 11px;cursor:pointer;margin-right:6px;letter-spacing:0.04em;text-transform:uppercase;}"
        ".lt-bar .lt-btn.active{background:#0b252f;color:#f2f1f1;border-color:#0b252f;}"
        ".lt-wrap[data-lttype=repo] tr[data-lttype]:not([data-lttype=repo]){display:none;}"
        ".lt-wrap[data-lttype=model] tr[data-lttype]:not([data-lttype=model]){display:none;}"
        ".lt-wrap[data-lttype=package] tr[data-lttype]:not([data-lttype=package]){display:none;}"
        ".lt-wrap[data-lttype=dataset] tr[data-lttype]:not([data-lttype=dataset]){display:none;}"
        "</style>"
    )
    _js = (
        "(function(){var w=document.querySelector('.lt-wrap');var bar=document.querySelector('.lt-bar');"
        "if(!w||!bar)return;bar.addEventListener('click',function(e){var b=e.target.closest('.lt-btn');if(!b)return;"
        "w.setAttribute('data-lttype',b.getAttribute('data-ltf'));"
        "bar.querySelectorAll('.lt-btn').forEach(function(x){x.classList.toggle('active',x===b);});});})();"
    )
    _enc = _js.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    mo.Html(
        _css
        + f'<div style="margin:48px 0 20px; padding:24px 0 0; border-top:2px solid {C["accent"]};">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">The long tail</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600; color:{C["ink"]}; '
        f'margin:0 0 12px; letter-spacing:-0.015em;">{_c["uncategorized"]:,} more products, tracked but not yet scored</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.95rem; color:{C["ink_2"]}; margin:0 0 16px; line-height:1.6;">'
        f'We track <strong>{_c["total"]:,}</strong> open source AI artifacts in total: '
        f'<strong>{_c["repos"]:,}</strong> repositories, <strong>{_c["models"]:,}</strong> models, and '
        f'<strong>{_c["packages"]:,}</strong> packages. Of the {_c["scored"]} products scored above, '
        f'<strong>{_c["overlap"]}</strong> are drawn from this catalog and <strong>{_c["scored_outside"]}</strong> '
        f'are closed/proprietary products that sit outside it. That leaves <strong>{_c["uncategorized"]:,}</strong> '
        f'catalog artifacts <em>uncategorized</em>. Filter the sample below by type; deep-scoring proceeds by usage rank.</p>'
        f'<div class="lt-bar" style="margin:6px 0 12px;">{_btns}</div>'
        f'<div class="lt-wrap" data-lttype="all">'
        f'<table style="border-collapse:collapse; width:100%;">'
        f'<thead><tr style="border-bottom:2px solid {C["rule"]};">{_head}</tr></thead>'
        f'<tbody>{_rows}</tbody></table></div>'
        f'<p style="font-family:{F["body"]}; font-size:0.82rem; color:{C["ink_3"]}; margin:12px 0 0; line-height:1.5;">'
        f'Usage (stars for repos, downloads for models / datasets / packages) is a discovery signal only, '
        f'not an openness, adoption, or capability score. These rows carry no axis values until researched and sourced.</p>'
        f'</div>'
        + f'<iframe srcdoc="&lt;!doctype html&gt;&lt;html&gt;&lt;/html&gt;" '
        f'style="display:none;width:0;height:0;border:0;position:absolute" onload="{_enc}"></iframe>'
    )
    return


@app.cell(hide_code=True)
def framework_edges(C, FRAMEWORK_EDGES, F, mo):
    _levels = ""
    for _lvl, _gaps in FRAMEWORK_EDGES:
        _items = "".join(
            f'<li style="margin:0 0 9px; line-height:1.5;">'
            f'<strong style="color:{C["ink"]};">{_n}.</strong> '
            f'<span style="color:{C["ink_2"]};">{_d}</span></li>'
            for _n, _d in _gaps
        )
        _levels += (
            f'<div style="margin:0 0 18px;">'
            f'<div style="font-family:{F["mono"]}; font-size:11px; color:{C["accent"]}; '
            f'letter-spacing:0.06em; text-transform:uppercase; margin-bottom:7px;">{_lvl}</div>'
            f'<ul style="font-family:{F["body"]}; font-size:0.88rem; margin:0; padding-left:18px;">{_items}</ul>'
            f'</div>'
        )
    mo.Html(
        f'<div style="margin:48px 0 20px; padding:24px 0 0; border-top:2px solid {C["accent"]};">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">The map\\u2019s edges</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600; color:{C["ink"]}; '
        f'margin:0 0 12px; letter-spacing:-0.015em;">What\\u2019s not on the map yet</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.95rem; color:{C["ink_2"]}; margin:0 0 18px; line-height:1.6;">'
        f'The Columbia framework treats openness as varying across the whole stack: at the '
        f'<strong>model</strong> level (datasets, code, weights), in the <strong>system</strong> around it '
        f'(infrastructure below, product and UX above), and across <strong>cross-cutting</strong> attributes '
        f'(documentation, licensing, safeguards). The categories above occupy some of those areas; these are the '
        f'ones we have not yet defined as categories. A statement of scope, not a backlog.</p>'
        f'{_levels}'
        f'<p style="font-family:{F["body"]}; font-size:0.82rem; color:{C["ink_3"]}; margin:6px 0 0; line-height:1.5;">'
        f'Licensing, the third cross-cutting attribute, is scored on every product above rather than '
        f'tracked as its own category.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def methodology(C, F, mo):
    # Full methodology prose is authored in docs/methodology.md (## Detail),
    # converted from Markdown to HTML at build time and injected as __METHOD_HTML__
    # (numbers already substituted). The scoped <style> below carries the house
    # fonts/colors onto the generated HTML, so the source stays plain Markdown.
    # This <style> also styles the header summary (.v3-sum) links.
    _style = (
        "<style>"
        f".v3-meth, .v3-meth p, .v3-meth li{{font-family:{F['body']};}}"
        f".v3-meth p{{font-size:0.9rem; color:{C['ink_2']}; line-height:1.6; margin:0 0 12px;}}"
        f".v3-meth h3{{font-family:{F['headline']}; font-weight:600; font-size:1.12rem; "
        f"color:{C['ink']}; letter-spacing:-0.01em; margin:28px 0 8px;}}"
        f".v3-meth h4{{font-family:{F['headline']}; font-weight:600; font-size:0.98rem; "
        f"color:{C['ink']}; margin:18px 0 6px;}}"
        f".v3-meth strong{{color:{C['ink']}; font-weight:600;}}"
        ".v3-meth em{font-style:italic;}"
        f".v3-meth a, .v3-sum a{{color:{C['accent']}; text-decoration:underline;}}"
        ".v3-meth ul{margin:6px 0 14px; padding-left:20px;}"
        f".v3-meth li{{font-size:0.9rem; color:{C['ink_2']}; line-height:1.55; margin:0 0 5px;}}"
        ".v3-meth table{border-collapse:collapse; width:100%; margin:10px 0 18px;}"
        f".v3-meth th{{font-family:{F['mono']}; font-size:9px; text-transform:uppercase; "
        f"letter-spacing:0.05em; color:{C['ink_3']}; text-align:left; padding:7px 12px 7px 0; "
        f"border-bottom:2px solid {C['rule']};}}"
        f".v3-meth td{{font-size:0.84rem; color:{C['ink_2']}; padding:7px 12px 7px 0; "
        f"border-bottom:1px solid {C['rule']}; vertical-align:top; line-height:1.45;}}"
        f".v3-meth code{{font-family:{F['mono']}; font-size:0.82rem; background:{C['paper_2']}; padding:1px 5px;}}"
        f".v3-meth pre{{font-family:{F['mono']}; font-size:0.8rem; color:{C['ink']}; "
        f"background:{C['paper_2']}; padding:12px 16px; margin:8px 0 16px; overflow-x:auto; line-height:1.5;}}"
        ".v3-meth pre code{background:none; padding:0;}"
        "</style>"
    )
    mo.Html(
        f'<div style="margin:48px 0 24px; padding:24px 0 0; border-top:2px solid {C["accent"]};">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; letter-spacing:0.1em; '
        f'text-transform:uppercase; margin-bottom:10px;">Methodology</div>'
        + _style
        + '<div class="v3-meth">'
        + __METHOD_HTML__
        + '</div></div>'
    )
    return


@app.cell(hide_code=True)
def next_steps(C, F, mo):
    _items = [
        ("Category editors.",
         "Stand up a steward for each category who owns its definition, the product "
         "list, the openness / adoption / capability inputs, the sourcing of reviews, "
         "and the open-vs-closed calls. Editors should have no direct stake in the "
         "products they rank."),
        ("Community contributions.",
         "Three GitHub-routed pathways: add a review on a product, submit a new "
         "project, or join as an editor, all version-controlled in the "
         "ecosystem-mapping repo."),
        ("Deeper coverage.",
         "Score the uncategorized long tail by usage rank, and broaden adoption "
         "signals beyond downloads to agent- and skill-marketplace activity."),
        ("Living methodology.",
         "Keep the taxonomy light: a clean 3\\u20134 sentence description per "
         "product, with categories that products can migrate between as the stack "
         "evolves."),
    ]
    _lis = "".join(
        f'<li style="margin:0 0 10px; line-height:1.5;"><strong>{_h}</strong> {_b}</li>'
        for _h, _b in _items
    )
    mo.Html(
        f'<div style="padding-top:24px; border-top:1px solid {C["rule"]}; margin:8px 0 16px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">Roadmap</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.5rem; font-weight:600; '
        f'color:{C["ink"]}; margin:0 0 14px;">Next steps</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink_2"]}; '
        f'line-height:1.6; margin:0 0 12px;">This map is a first pass, not a finished '
        f'product. Depth comes from editors, the domain experts who own a category and '
        f'keep it honest, not from more in-house passes.</p>'
        f'<ul style="font-family:{F["body"]}; font-size:0.88rem; color:{C["ink_2"]}; '
        f'margin:6px 0 0; padding-left:18px;">{_lis}</ul></div>'
    )
    return


@app.cell(hide_code=True)
def setup_pyoso():
    # This code sets up pyoso to be used as a database provider for this notebook
    # This code is autogenerated. Modification could lead to unexpected results :)
    import pyoso
    import marimo as mo
    pyoso_db_conn = pyoso.Client().dbapi_connection()
    return mo, pyoso_db_conn


if __name__ == "__main__":
    app.run()
'''

# Build the section cells
_sections = []
for i, cid in enumerate(data["order"], start=1):
    _sections.append(
        f'@app.cell(hide_code=True)\n'
        f'def section_{cid}(mo, render_section):\n'
        f'    render_section("{cid}", {i})\n'
        f'    return\n'
    )
section_block = "\n\n".join(_sections)

NB = (NB
      .replace("__DATA_LITERAL__", DATA_LITERAL)
      .replace("__STRAPLINES__", STRAPLINES_LITERAL)
      .replace("__LAYER_WEIGHTS__", LAYER_WEIGHTS_LITERAL)
      .replace("__SUMMARY_HTML__", SUMMARY_HTML_LITERAL)
      .replace("__METHOD_HTML__", METHOD_HTML_LITERAL)
      .replace("__SECTION_CELLS__", section_block))
# Guarded so the module can be imported without writing. Everything above is pure -
# reads and string building - but the write is not, and an unguarded write means
# importing render.py to test one helper silently regenerates a bot-owned file and
# dirties the tree. That is why nothing here had tests.
if __name__ == "__main__":
    open(OUT, "w", encoding="utf-8").write(NB)
    print("wrote", OUT, "(", len(NB), "chars )")
