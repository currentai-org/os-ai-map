#!/usr/bin/env python3
"""Generate notebooks/ai-stack-map.py, the three-axis openness map, in the
ai-stack-map.py editorial house style. Static-export friendly: data is embedded;
interactivity is the JS Details drawer + a JS type-toggle (no kernel)."""
import json
import yaml
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
    lines = ["{\n"]
    for cid in order:
        strap = cats[cid]["strapline"]
        lines.append(f'        "{cid}": "{strap}",\n')
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

NB = '''import marimo

__generated_with = "unknown"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def load_fonts(mo):
    mo.Html(
        '<style>'
        '@import url("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap");'
        '</style>'
    )
    return


@app.cell(hide_code=True)
def style():
    F = {
        "headline": "Fraunces, Georgia, serif",
        "body": "Inter, -apple-system, system-ui, sans-serif",
        "mono": "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace",
    }
    C = {
        "ink": "#1a1814", "ink_2": "#3a342b", "ink_3": "#6b6253",
        "paper": "#f5f1ea", "paper_2": "#ede7dc", "rule": "#c9bfac",
        "signal": "#c8341d", "healthy": "#1b6b5e", "warm": "#d97c2a", "accent": "#2a3d8f",
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
        "documented_only": ("Documented only", 1, "ink_3"),
        "closed": ("Closed", 1, "ink_3"),
    }
    # Openness verdict code -> (label, color key into C). Colors match the
    # count chips (open=green, open-ish=orange, closed=red) so the badge
    # reinforces the chips; competitive is the neutral accent.
    VERDICT = {
        "open_leads": ("Open leads", "healthy"),
        "openish_leads": ("Open-ish leads", "warm"),
        "closed_leads": ("Closed leads", "signal"),
        "competitive": ("Competitive", "accent"),
        "none": ("No standout", "ink_3"),
    }
    return C, F, OPEN, VERDICT


@app.cell(hide_code=True)
def data():
    import json
    DATA = json.loads(__DATA_LITERAL__)
    ORDER = DATA["order"]
    STRAPLINES = __STRAPLINES__
    # Neutral one-line definitions for the at-a-glance overview (what the
    # category IS, vs the strapline which is the finding).
    STACK_DESC = {
        "base_pretrained": "Foundation models trained from scratch.",
        "finetuned_chat": "Instruction-tuned chat and reasoning assistants.",
        "inference_code": "Engines and runtimes that serve model inference.",
        "finetuning_code": "Libraries and platforms for fine-tuning models.",
        "evaluation_code": "Harnesses that run and grade model evaluations.",
        "benchmark_eval_data": "Benchmark datasets used to evaluate models.",
        "orchestration_agents": "Frameworks and agents that plan and execute tasks.",
        "ui_api": "Chat UIs and API gateways in front of models.",
        "telemetry_observability": "Tracing and observability for LLM apps.",
        "agent_tools_protocols": "Tools, protocols, and retrieval for agents.",
        "deployment": "Sandboxes, runtimes, and serverless model hosting.",
    }
    # Per-category combined-score weights (adoption, capability), ported from the
    # v2 stack map (slugs identical). Feed the "standout product" gate behind the
    # openness verdict; the table also shows the blended score.
    LAYER_WEIGHTS = __LAYER_WEIGHTS__
    # Framework white-space: homes in the Columbia/MOF openness stack that the
    # 11 categories above do NOT cover. Rendered by the framework_edges cell as a
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
    #   closed  = restricted / documented_only / closed
    _OPEN = {"open_source", "open", "open_core"}
    _OPENISH = {"open_weights", "source_available", "gated"}

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
def header(C, DATA, F, mo):
    _lt = DATA["long_tail"]["counts"]
    _n = _lt["scored"]
    mo.Html(
        f'<div style="padding:40px 0 28px; border-bottom:2px solid {C["accent"]}; margin-bottom:36px;">'
        f'<div style="font-family:{F["mono"]}; font-size:11px; color:{C["ink_3"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px;">'
        f'Current AI \\u00b7 Open Source AI Map \\u00b7 v3</div>'
        f'<h1 style="font-family:{F["headline"]}; font-size:2.2rem; font-weight:400; '
        f'color:{C["ink"]}; margin:0 0 14px; line-height:1.05; letter-spacing:-0.025em;">'
        f'Open Source AI Map: openness is a spectrum, not a checkbox</h1>'
        f'<p style="font-family:{F["body"]}; font-size:1rem; color:{C["ink_2"]}; '
        f'margin:0; line-height:1.5;">'
        f'We track <strong>{_lt["total"]:,}</strong> open-source AI artifacts across the stack. '
        f'This map <strong>scores {_n} of them in depth</strong> on three independent axes: '
        f'<strong>openness</strong> (graded 0\\u20135 on the Model Openness Framework / OSI '
        f'classes, not a yes/no), <strong>adoption</strong> (real usage, not stars), and '
        f'<strong>capability</strong> (benchmarks where they exist, feature coverage where '
        f'they don\\u2019t). Every score is sourced. The remaining <strong>{_lt["uncategorized"]:,}</strong> '
        f'are the <strong>uncategorized long tail</strong>, tracked by usage signal but not yet scored. '
        f'The interesting findings live where the axes disagree \\u2014 the widely-used model that is '
        f'barely open, the fully-open project few have adopted. The openness framework descends directly from the '
        f'<a href="https://arxiv.org/abs/2405.15802" target="_blank" rel="noopener" '
        f'style="color:{C["accent"]}; text-decoration:underline;">'
        f'2024 Columbia Convening on Openness in AI</a>.</p></div>'
    )
    return


@app.cell(hide_code=True)
def combat_scorecard(C, DATA, F, ORDER, VERDICT, mo, verdict_for):
    # Hero: one count tile per openness verdict across the 11 categories.
    _counts = {}
    for _cid in ORDER:
        _code = verdict_for(_cid)[0]
        _counts[_code] = _counts.get(_code, 0) + 1
    _codes = ["open_leads", "openish_leads", "closed_leads", "competitive"]
    if _counts.get("none"):
        _codes.append("none")
    _tiles = []
    for _code in _codes:
        _label, _ckey = VERDICT[_code]
        _n = _counts.get(_code, 0)
        _tiles.append(
            f'<div style="background:{C[_ckey]}; color:white; padding:18px 16px; border-radius:3px;">'
            f'<div style="font-family:{F["headline"]}; font-size:2.4rem; font-weight:500; '
            f'line-height:1; letter-spacing:-0.02em;">{_n}</div>'
            f'<div style="font-family:{F["mono"]}; font-size:0.7rem; letter-spacing:0.08em; '
            f'text-transform:uppercase; margin-top:8px; opacity:0.92;">{_label}</div>'
            f'</div>'
        )
    mo.Html(
        f'<div style="margin:0 0 44px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px;">'
        f'Where openness leads \\u00b7 {len(ORDER)} categories</div>'
        f'<div style="display:grid; grid-template-columns:repeat({len(_codes)}, 1fr); gap:10px;">'
        f'{"".join(_tiles)}</div></div>'
    )
    return


@app.cell(hide_code=True)
def stack_overview(C, DATA, F, ORDER, STACK_DESC, VERDICT, mix_counts, mo,
                   verdict_for):
    # The at-a-glance roster: every category as a row, grouped by arc, with the
    # full openness-mix count chips and the verdict badge.
    _rows = []
    _last_arc = None
    for _i, _cid in enumerate(ORDER, start=1):
        _cat = DATA["categories"][_cid]
        _arc = _cat["arc"]
        if _arc != _last_arc:
            _bt = "none" if _last_arc is None else f"1px dashed {C['rule']}"
            _mt = "8px" if _last_arc is None else "22px"
            _rows.append(
                f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
                f'letter-spacing:0.14em; text-transform:uppercase; margin:{_mt} 0 6px; '
                f'padding-top:12px; border-top:{_bt};">{_arc}</div>'
            )
            _last_arc = _arc
        _m = mix_counts(_cid)
        _code, _basis = verdict_for(_cid)
        _vlabel, _vckey = VERDICT[_code]
        _chips = (
            f'<span style="color:{C["healthy"]};">\\u25cf</span> {_m["open"]} open'
            f'&nbsp;&nbsp;<span style="color:{C["warm"]};">\\u25cf</span> {_m["openish"]} open-ish'
            f'&nbsp;&nbsp;<span style="color:{C["ink_3"]};">\\u25cf</span> {_m["closed"]} closed'
        )
        _rows.append(
            f'<div style="display:grid; grid-template-columns:32px 1fr 232px 150px; gap:18px; '
            f'align-items:center; padding:14px 0; border-bottom:1px solid {C["rule"]};">'
            f'<div style="font-family:{F["mono"]}; font-size:12px; color:{C["ink_3"]};">{_i:02d}</div>'
            f'<div><div style="font-family:{F["headline"]}; font-size:1.05rem; font-weight:500; '
            f'color:{C["ink"]}; line-height:1.2;">{_cat["label"]}</div>'
            f'<div style="font-family:{F["body"]}; font-size:0.85rem; color:{C["ink_3"]}; '
            f'margin-top:3px; line-height:1.4;">{STACK_DESC.get(_cid, "")}</div></div>'
            f'<div style="font-family:{F["mono"]}; font-size:0.74rem; color:{C["ink_2"]};">{_chips}</div>'
            f'<div style="font-family:{F["mono"]}; font-size:0.72rem; letter-spacing:0.05em; '
            f'text-transform:uppercase; color:white; background:{C[_vckey]}; padding:7px 10px; '
            f'text-align:center; border-radius:2px;">{_vlabel}</div>'
            f'</div>'
        )
    _total = DATA.get("n_total") or sum(len(DATA["categories"][c]["products"]) for c in ORDER)
    _n_arcs = len({DATA["categories"][c]["arc"] for c in ORDER})
    mo.Html(
        f'<div style="margin:0 0 52px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">The stack at a glance</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:500; color:{C["ink"]}; '
        f'margin:0 0 14px; letter-spacing:-0.015em;">'
        f'{_n_arcs} layers \\u00b7 {len(ORDER)} categories \\u00b7 {_total} scored products</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.95rem; color:{C["ink_2"]}; margin:0 0 20px; line-height:1.6;">'
        f'Each row is one category, grouped into three layers. The dots show the openness mix of all its '
        f'products; the badge names which tier leads among the category\\u2019s standout products: '
        f'those that clear the combined adoption\\u00d7capability bar. Open in the long tail and closed at the '
        f'top can coexist \\u2014 that gap is the point.</p>'
        f'{"".join(_rows)}</div>'
    )
    return


@app.cell(hide_code=True)
def openness_distribution(C, DATA, F, mo):
    import collections as _collections
    def _ccol(_cls):
        if _cls in ("open_source", "open"):
            return C["healthy"]
        if _cls in ("open_weights", "open_core"):
            return C["warm"]
        if _cls in ("restricted", "source_available", "gated"):
            return C["signal"]
        return C["ink_3"]
    _CLS_ORDER = ["open_source", "open", "open_core", "open_weights", "source_available", "gated", "restricted", "documented_only", "closed"]
    _bars = []
    for _tk, _tl in [("model", "Models"), ("dataset", "Datasets"), ("software", "Software")]:
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
            f'<div style="display:flex; border-radius:3px; overflow:hidden;">{_segs}</div>'
            f'<div style="font-family:{F["mono"]}; font-size:0.78rem; color:{C["ink_3"]}; text-align:right;">{_tot}</div>'
            f'</div>'
        )
    _legend = "".join(
        f'<span style="display:inline-flex; align-items:center; margin-right:16px; font-family:{F["body"]}; font-size:0.78rem; color:{C["ink_3"]};">'
        f'<span style="width:11px; height:11px; background:{_col}; border-radius:2px; display:inline-block; margin-right:5px;"></span>{_lab}</span>'
        for _lab, _col in [("Open source / data", C["healthy"]), ("Open weights / core", C["warm"]), ("Restricted / gated", C["signal"]), ("Closed", C["ink_3"])]
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
def openness_toggle(C, F, mo):
    # JS-only filter (works in static HTML). Buttons set a data-filter on the
    # document body; CSS hides section rows whose openness bucket (data-open)
    # does not match. Long-tail rows use a different attribute and are unaffected.
    _css = (
        "<style>"
        ".v3map-filter button{font-family:Inter,system-ui,sans-serif;font-size:12px;"
        "border:1px solid #c9bfac;background:#fff;color:#3a342b;border-radius:5px;"
        "padding:5px 12px;cursor:pointer;margin-right:6px;}"
        ".v3map-filter button.active{background:#2a3d8f;color:#fff;border-color:#2a3d8f;}"
        "body[data-v3filter=open] tr[data-open]:not([data-open=open]){display:none;}"
        "body[data-v3filter=openish] tr[data-open]:not([data-open=openish]){display:none;}"
        "body[data-v3filter=closed] tr[data-open]:not([data-open=closed]){display:none;}"
        "</style>"
    )
    _js = (
        "(function(){var f=document.querySelector('.v3map-filter');if(!f)return;"
        "f.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;"
        "document.body.setAttribute('data-v3filter',b.getAttribute('data-f'));"
        "f.querySelectorAll('button').forEach(function(x){x.classList.toggle('active',x===b);});});})();"
    )
    _boot = (_css + "<div class=\\"v3map-filter\\" style=\\"margin:0 0 24px;\\">"
        "<span style=\\"font-family:'JetBrains Mono',monospace;font-size:10px;color:#6b6253;"
        "letter-spacing:0.08em;text-transform:uppercase;margin-right:12px;\\">Filter by openness</span>"
        "<button data-f=\\"all\\" class=\\"active\\">All</button>"
        "<button data-f=\\"open\\">Open</button>"
        "<button data-f=\\"openish\\">Open-ish</button>"
        "<button data-f=\\"closed\\">Closed</button></div>")
    _enc = (_js.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;"))
    mo.Html(
        _boot + f'<iframe srcdoc="&lt;!doctype html&gt;&lt;html&gt;&lt;/html&gt;" '
        f'style="display:none;width:0;height:0;border:0;position:absolute" '
        f'onload="{_enc}"></iframe>'
    )
    return


@app.cell(hide_code=True)
def helpers(C, DATA, F, OPEN, STRAPLINES, VERDICT, mix_counts, mo, vbucket,
            verdict_for):
    def _oscore(p):
        return (p.get("openness") or {}).get("score")

    def _ocolor(score):
        if score is None:
            return C["rule"]
        if score >= 4:
            return C["healthy"]
        if score == 3:
            return C["warm"]
        if score == 2:
            return C["signal"]
        return C["ink_3"]

    def _bars(value, on_color):
        v = int(value) if isinstance(value, (int, float)) else 0
        return "".join(
            f'<span style="display:inline-block; width:6px; height:14px; margin-right:2px; '
            f'vertical-align:middle; background:{on_color if j < v else C["paper_2"]};"></span>'
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
        return (
            f'<tr data-open="{_ob}" data-type="{p.get("type","")}" style="border-bottom:1px solid {C["paper_2"]};">'
            f'<td style="padding:8px 10px; font-family:{F["body"]}; font-size:0.86rem; color:{C["ink"]};">{_name}</td>'
            f'<td style="padding:8px 10px; font-family:{F["body"]}; font-size:0.78rem; color:{C["ink_3"]};">{p.get("org","") or ""}</td>'
            f'<td style="padding:8px 10px;">{openness_cell(op)}</td>'
            f'<td style="padding:8px 10px;">{axis_bars(ad, "level", C["accent"])}</td>'
            f'<td style="padding:8px 10px;">{axis_bars(cap, "score", C["ink_2"])}</td>'
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
            _links = " &middot; ".join(
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
            f'<div style="margin:4px 0 16px; padding:14px 18px; background:{C["paper_2"]}; '
            f'border-left:2px solid {C["ink_3"]};">'
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
        _code, _basis = verdict_for(cid)
        _vlabel, _vckey = VERDICT[_code]
        _m = mix_counts(cid)
        _badge = (
            f'<span style="display:inline-block; font-family:{F["mono"]}; font-size:0.72rem; '
            f'letter-spacing:0.05em; text-transform:uppercase; color:white; background:{C[_vckey]}; '
            f'padding:4px 10px; border-radius:2px; vertical-align:middle;">{_vlabel}</span>'
        )
        _tally = (
            f'<span style="color:{C["healthy"]};">\\u25cf</span> {_m["open"]} open'
            f'&nbsp;&nbsp;<span style="color:{C["warm"]};">\\u25cf</span> {_m["openish"]} open-ish'
            f'&nbsp;&nbsp;<span style="color:{C["ink_3"]};">\\u25cf</span> {_m["closed"]} closed'
        )
        return (
            f'<div style="margin:4px 0 10px;">{_badge}'
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
                f'<div style="margin:44px 0 0; padding:14px 0 8px; border-top:1px dashed {C["rule"]};">'
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
            f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">{cat["arc"]} \\u00b7 {num:02d}</div>'
            f'<h2 style="font-family:{F["headline"]}; font-size:1.4rem; font-weight:500; '
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
    import json as _json
    # Build a per-product payload keyed by product name, then install a delegated
    # click handler + modal via a hidden-iframe onload bootstrap (marimo strips
    # <script>, so we inject through the iframe into the parent document).
    _payload = {}
    for _cid in ORDER:
        for _p in DATA["categories"][_cid]["products"]:
            _payload[_p["product"]] = {**_p, "category_label": DATA["categories"][_cid]["label"]}
    _pj = _json.dumps(_payload, ensure_ascii=False)
    _css = (
        ".v3-details{padding:3px 9px;font-size:11px;font-family:Inter,system-ui,sans-serif;"
        "border:1px solid #2a3d8f;background:#fff;color:#2a3d8f;border-radius:4px;cursor:pointer;font-weight:600;}"
        ".v3-details:hover{background:#2a3d8f;color:#fff;}"
        ".v3-bd{position:fixed;inset:0;background:rgba(26,24,20,0.55);z-index:99999;display:flex;"
        "align-items:flex-start;justify-content:center;padding:40px 20px;overflow-y:auto;font-family:Inter,system-ui,sans-serif;}"
        ".v3-modal{background:#fff;border-radius:10px;max-width:780px;width:100%;padding:24px 28px;box-shadow:0 20px 60px rgba(0,0,0,0.25);}"
        ".v3-modal h2{font-family:Fraunces,Georgia,serif;font-weight:500;font-size:1.4rem;margin:0 0 4px;color:#1a1814;}"
        ".v3-x{float:right;cursor:pointer;background:none;border:1px solid #c9bfac;border-radius:5px;padding:4px 10px;font-size:12px;color:#6b6253;}"
        ".v3-sect{margin:16px 0 6px;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10.5px;text-transform:uppercase;"
        "letter-spacing:0.08em;color:#2a3d8f;font-weight:600;border-bottom:1px solid #c9bfac;padding-bottom:4px;}"
        ".v3-row{display:flex;gap:14px;margin:5px 0;font-size:13px;color:#3a342b;}"
        ".v3-lbl{min-width:96px;color:#6b6253;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:11.5px;}"
        ".v3-val{flex:1;line-height:1.45;}"
        ".v3-pill{display:inline-block;padding:2px 8px;border-radius:10px;color:#fff;font-size:11px;font-weight:600;}"
        ".v3-modal ul{margin:4px 0;padding-left:20px;font-size:12.5px;color:#3a342b;line-height:1.5;}"
        ".v3-modal a{color:#2a3d8f;text-decoration:none;}.v3-modal a:hover{text-decoration:underline;}"
    )
    _js = r\'\'\'
    (function(){
      if (window.__V3_INSTALLED__) { window.__V3_PAYLOAD__ = __PAYLOAD__; return; }
      window.__V3_INSTALLED__ = true; window.__V3_PAYLOAD__ = __PAYLOAD__;
      var esc=function(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];});};
      function ocol(sc){return sc==null?'#6b6253':(sc>=4?'#1b6b5e':(sc==3?'#d97c2a':(sc==2?'#c8341d':'#6b6253')));}
      function srcs(a){if(!a||!a.length)return '<span style="color:#aaa">no sources</span>';
        return '<ul>'+a.map(function(s){var u=s&&s.url?s.url:'';var sh=s&&s.shows?s.shows:u;
        return u?'<li><a href="'+esc(u)+'" target="_blank" rel="noopener">'+esc(sh||u)+'</a></li>':'<li>'+esc(sh)+'</li>';}).join('')+'</ul>';}
      function row(l,v){if(v==null||v==='')v='<em style="color:#aaa">n/a</em>';
        return '<div class="v3-row"><span class="v3-lbl">'+esc(l)+'</span><span class="v3-val">'+(typeof v==='string'&&v.indexOf('<')===0?v:esc(v))+'</span></div>';}
      function build(p){
        var o=p.openness||{},ad=p.adoption||{},cap=p.capability||{};
        var h='<div class="v3-bd"><div class="v3-modal"><button class="v3-x">Close \\u2715</button>'+
          '<h2>'+esc(p.product||'')+'</h2>'+
          '<div style="font-family:\\'JetBrains Mono\\',monospace;font-size:11px;color:#6b6253;margin-bottom:6px;">'+
            esc(p.org||'')+' \\u00b7 '+esc(p.type||'')+' \\u00b7 '+esc(p.category_label||'')+
            (o.class?' \\u00b7 <span class="v3-pill" style="background:'+ocol(o.score)+'">'+esc(o.class)+'</span>':'')+'</div>'+
          (p.description?'<div style="font-size:13px;color:#3a342b;line-height:1.5;margin:8px 0;">'+esc(p.description)+'</div>':'')+
          (p.version_note?'<div style="font-size:11.5px;color:#6b6253;line-height:1.45;margin:6px 0;">'+esc(p.version_note)+'</div>':'')+
          '<div class="v3-sect">Openness \\u00b7 '+(o.score==null?'n/a':o.score+'/5')+' ('+esc(o.class||'')+')</div>'+
          row('Components',o.components)+row('Why',o.note)+row('Confidence',o.confidence)+
          '<div class="v3-row"><span class="v3-lbl">Sources</span><span class="v3-val">'+srcs(o.sources)+'</span></div>'+
          '<div class="v3-sect">Adoption \\u00b7 '+(ad.level==null?'n/a':ad.level+'/5')+'</div>'+
          row('Reach',ad.reach)+row('Signal',ad.signal_type)+row('Detail',ad.note)+row('Confidence',ad.confidence)+
          '<div class="v3-row"><span class="v3-lbl">Sources</span><span class="v3-val">'+srcs(ad.sources)+'</span></div>'+
          '<div class="v3-sect">Capability \\u00b7 '+(cap.score==null?'n/a':cap.score+'/5')+'</div>'+
          row('Basis',cap.basis)+row('Value',cap.value)+row('Detail',cap.note)+row('Confidence',cap.confidence)+
          '<div class="v3-row"><span class="v3-lbl">Sources</span><span class="v3-val">'+srcs(cap.sources)+'</span></div>'+
          ((p.flags&&p.flags.length)?'<div class="v3-sect">Flags</div><div class="v3-row"><span class="v3-val">'+esc(p.flags.join(', '))+'</span></div>':'')+
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
def uncategorized_long_tail(C, DATA, F, mo):
    _lt = DATA["long_tail"]
    _c = _lt["counts"]
    _TC = {"repo": C["accent"], "model": C["healthy"], "package": C["warm"], "dataset": C["signal"]}
    _btns = "".join(
        '<button data-ltf="' + _k + '" class="lt-btn' + (' active' if _k == 'all' else '') + '">' + _lab + '</button>'
        for _k, _lab in [("all", "All"), ("repo", "Repos"), ("model", "Models"), ("package", "Packages"), ("dataset", "Datasets")]
    )
    _rows = "".join(
        f'<tr data-lttype="{_t["type"]}" style="border-bottom:1px solid {C["paper_2"]};">'
        f'<td style="padding:7px 10px; font-family:{F["mono"]}; font-size:0.8rem; color:{C["ink"]};">{_t["name"]}</td>'
        f'<td style="padding:7px 10px;"><span style="font-family:{F["mono"]}; font-size:0.64rem; text-transform:uppercase; '
        f'letter-spacing:0.04em; color:#fff; background:{_TC.get(_t["type"], C["ink_3"])}; padding:2px 7px; border-radius:10px;">{_t["type"]}</span></td>'
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
        ".lt-bar .lt-btn{font-family:Inter,system-ui,sans-serif;font-size:11px;border:1px solid #c9bfac;"
        "background:#fff;color:#3a342b;border-radius:5px;padding:4px 11px;cursor:pointer;margin-right:6px;}"
        ".lt-bar .lt-btn.active{background:#2a3d8f;color:#fff;border-color:#2a3d8f;}"
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
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">The long tail \\u00b7 uncategorized</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:500; color:{C["ink"]}; '
        f'margin:0 0 12px; letter-spacing:-0.015em;">{_c["uncategorized"]:,} more products, tracked but not yet scored</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.95rem; color:{C["ink_2"]}; margin:0 0 16px; line-height:1.6;">'
        f'We track <strong>{_c["total"]:,}</strong> open-source AI artifacts in total: '
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
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:8px;">The map\\u2019s edges \\u00b7 framework white-space</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:500; color:{C["ink"]}; '
        f'margin:0 0 12px; letter-spacing:-0.015em;">What\\u2019s not on the map yet</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.95rem; color:{C["ink_2"]}; margin:0 0 18px; line-height:1.6;">'
        f'The Columbia framework treats openness as varying across the whole stack: at the '
        f'<strong>model</strong> level (datasets, code, weights), in the <strong>system</strong> around it '
        f'(infrastructure below, product and UX above), and across <strong>cross-cutting</strong> attributes '
        f'(documentation, licensing, safeguards). The 11 categories above occupy some of those areas; these are the '
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
    # mo.Html (not mo.md): marimo skips inline markdown wrapped in a block-level
    # <div>, so bold/links must be literal HTML here, like every other cell.
    def _a(url, txt):
        return f'<a href="{url}" target="_blank" rel="noopener" style="color:{C["accent"]}; text-decoration:underline;">{txt}</a>'
    _ps = [
        f"""<strong>Three independent axes.</strong> Every product is scored on <strong>openness</strong>, <strong>adoption</strong>, and <strong>capability</strong>. They answer different questions (is it open? is it used? is it good?), and the map's insight is where they disagree. Every non-null score cites a verifiable source; values are never inferred.""",
        f"""<strong>Openness (0–5 + class)</strong> is graded with the {_a('https://arxiv.org/abs/2403.13784', 'Model Openness Framework')} for models (open_source / open_weights / restricted / closed), OSI-class tests for software (open_source / source_available / open_core / closed), and data-openness for datasets (open / gated / documented_only / closed). "Open weights" is not "open source." The distinction is the point.""",
        f"""<strong>Adoption (1–5)</strong> is real usage (downloads, active users, deployments); GitHub stars are a last resort and never push a product above level 3.""",
        f"""<strong>Capability (1–5, method-labeled)</strong> uses community benchmarks where they exist (MMLU-Pro, GPQA, SWE-bench, LMArena, MLPerf, ANN-Benchmarks) and a feature matrix where they don't; null where capability isn't a meaningful axis. <em>Capability means different things for a model vs a tool vs a dataset, so compare within a category, not across.</em>""",
        f"""<strong>The openness verdict.</strong> Each category's badge reports which tier (open, open-ish [open-weights / source-available / gated], or closed) leads among its <em>standout</em> products: those whose blended adoption×capability score (weighted by layer, so capability counts more for models and adoption more for end-user surfaces) clears 4 of 5. "Leads" requires a clear plurality; otherwise the category reads <em>competitive</em>, or <em>no standout</em> where nothing clears the bar. The count chips always show the full openness mix, so a category that is open in the long tail but closed at the top is visible.""",
        f"""Built on the openness framework from the <strong>Columbia Convening on Openness in AI</strong> ({_a('https://arxiv.org/abs/2405.15802', 'arXiv:2405.15802')}; follow-on {_a('https://arxiv.org/abs/2506.22183', 'arXiv:2506.22183')}). Products that could not be verified against a primary source were excluded rather than guessed.""",
    ]
    _body = "".join(
        f'<p style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink_2"]}; line-height:1.6; margin:0 0 12px;">{_p}</p>'
        for _p in _ps
    )
    mo.Html(
        f'<div style="margin:48px 0 24px; padding:24px 0 0; border-top:2px solid {C["accent"]};">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; letter-spacing:0.1em; '
        f'text-transform:uppercase; margin-bottom:10px;">Methodology</div>'
        f'{_body}</div>'
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
        f'<h2 style="font-family:{F["headline"]}; font-size:1.5rem; font-weight:500; '
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

# Build the 11 section cells
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
      .replace("__SECTION_CELLS__", section_block))
open(OUT, "w").write(NB)
print("wrote", OUT, "(", len(NB), "chars )")
