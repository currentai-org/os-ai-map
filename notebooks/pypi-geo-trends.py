import marimo

__generated_with = "unknown"
app = marimo.App()


@app.cell(hide_code=True)
def header(C, F, mo):
    mo.Html(
        f'<div style="padding:40px 0 28px; border-bottom:2px solid {C["accent"]}; margin-bottom:36px;">'
        f'<h1 style="font-family:{F["headline"]}; font-size:2.2rem; font-weight:600; '
        f'color:{C["ink"]}; margin:0 0 14px; line-height:1.05; letter-spacing:-0.025em;">'
        f'Open-Source AI: Where the World Downloads</h1>'
        f'<p style="font-family:{F["body"]}; font-size:1rem; color:{C["ink_2"]}; '
        f'margin:0; line-height:1.5;">'
        f'PyPI download geography across 39 AI packages, May 2025 – April 2026. '
        f'Tracking adoption by region to assess where open-source AI momentum is building, '
        f'and where Europe stands relative to the US and China.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def summary_stats(df_regional_totals, mo):
    _total = int(df_regional_totals["total_downloads"].sum())
    _us_rows = df_regional_totals[df_regional_totals["region"] == "United States"]["total_downloads"]
    _eu_rows = df_regional_totals[df_regional_totals["region"] == "EU"]["total_downloads"]
    _cn_rows = df_regional_totals[df_regional_totals["region"] == "China"]["total_downloads"]
    _row_rows = df_regional_totals[df_regional_totals["region"] == "Rest of World"]["total_downloads"]
    _us = int(_us_rows.values[0]) if len(_us_rows) else 0
    _eu = int(_eu_rows.values[0]) if len(_eu_rows) else 0
    _cn = int(_cn_rows.values[0]) if len(_cn_rows) else 0
    _row = int(_row_rows.values[0]) if len(_row_rows) else 0
    mo.hstack([
        mo.stat(value=f"{_total/1e9:.1f}B", label="Total Downloads", bordered=True, caption="May 2025 – Apr 2026"),
        mo.stat(value=f"{_us/_total*100:.0f}%", label="US Share", bordered=True, caption=f"{_us/1e9:.1f}B downloads"),
        mo.stat(value=f"{_eu/_total*100:.0f}%", label="EU Share", bordered=True, caption=f"{_eu/1e9:.1f}B downloads"),
        mo.stat(value=f"{_cn/_total*100:.1f}%", label="China Share", bordered=True, caption=f"{_cn/1e6:.0f}M downloads"),
        mo.stat(value=f"{_row/_total*100:.0f}%", label="Rest of World", bordered=True, caption=f"{_row/1e9:.1f}B downloads"),
    ], widths="equal", gap=1)
    return


@app.cell(hide_code=True)
def section_share(C, F, mo):
    mo.Html(
        f'<div style="margin:44px 0 20px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">'
        f'Regional Share</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600;'
        f'color:{C["ink"]}; margin:0 0 8px;">'
        f'The US accounts for nearly three-quarters of global AI package downloads</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink_3"]}; '
        f'margin:0; line-height:1.5;">'
        f'Total PyPI downloads by region across 39 AI packages in this sample. '
        f'The EU registers 11%, significant but dwarfed by the US at 72%. '
        f'China is below 1%, suggesting a largely domestic Python ecosystem for AI.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def regional_share_chart(
    C,
    CHART_LAYOUT,
    REGION_COLORS,
    REGION_ORDER,
    df_regional_totals,
    go,
    mo,
):
    _df = df_regional_totals.copy()
    _df = _df.set_index("region").reindex(REGION_ORDER).reset_index()
    _total = _df["total_downloads"].sum()
    _df["pct"] = _df["total_downloads"] / _total * 100
    _layout = {k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis", "margin", "hovermode")}
    _fig = go.Figure(go.Bar(
        x=_df["region"],
        y=_df["total_downloads"],
        marker_color=[REGION_COLORS[r] for r in _df["region"]],
        text=[f"{v/1e9:.2f}B ({p:.1f}%)" for v, p in zip(_df["total_downloads"], _df["pct"])],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{x}</b><br>Downloads: %{y:,.0f}<extra></extra>",
    ))
    _fig.update_layout(
        **_layout,
        height=360,
        hovermode="closest",
        margin=dict(t=40, l=60, r=20, b=50),
        xaxis=dict(showgrid=False, linecolor=C["ink"], linewidth=1),
        yaxis=dict(
            title="Total downloads (May 2025–Apr 2026)",
            showgrid=True, gridcolor=C["rule"],
            linecolor=C["ink"], linewidth=1,
            tickformat=",.0f",
            rangemode="tozero",
        ),
    )
    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def section_growth(C, F, mo):
    mo.Html(
        f'<div style="margin:44px 0 20px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">'
        f'Growth Trajectory</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600;'
        f'color:{C["ink"]}; margin:0 0 8px;">'
        f'All regions are growing, but the US curve is diverging in absolute terms</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink_3"]}; '
        f'margin:0; line-height:1.5;">'
        f'Monthly AI package downloads by region. The US grew from 642M in May 2025 to nearly 2B in April 2026. '
        f'The EU roughly doubled over the same period. In absolute terms, the gap is compounding.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def growth_trajectory_chart(
    C,
    CHART_LAYOUT,
    REGION_COLORS,
    REGION_ORDER,
    df_monthly_regional,
    go,
    mo,
    pd,
):
    _df = df_monthly_regional.copy()
    _df["month"] = pd.to_datetime(_df["month"])
    _layout = {k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis", "margin", "legend")}
    _fig = go.Figure()
    for _region in REGION_ORDER:
        _subset = _df[_df["region"] == _region].sort_values("month")
        _fig.add_trace(go.Scatter(
            x=_subset["month"],
            y=_subset["total_downloads"],
            mode="lines",
            name=_region,
            line=dict(color=REGION_COLORS[_region], width=2),
            hovertemplate=f"<b>{_region}</b><br>%{{x|%b %Y}}: %{{y:,.0f}}<extra></extra>",
        ))
    _fig.update_layout(
        **_layout,
        height=380,
        margin=dict(t=20, l=80, r=20, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False, linecolor=C["ink"], linewidth=1, tickformat="%b %Y"),
        yaxis=dict(
            title="Monthly downloads",
            showgrid=True, gridcolor=C["rule"],
            linecolor=C["ink"], linewidth=1,
            rangemode="tozero",
            tickformat=",.0f",
        ),
    )
    _fig.update_layout(hovermode="x unified")
    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def section_indexed(C, F, mo):
    mo.Html(
        f'<div style="margin:44px 0 20px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">'
        f'Relative Growth</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600;'
        f'color:{C["ink"]}; margin:0 0 8px;">'
        f'EU growth is the slowest of any region, and the relative gap is compounding</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink_3"]}; '
        f'margin:0; line-height:1.5;">'
        f'Downloads indexed to 100 at May 2025. The EU has grown 2.1×, slower than the US (3.0×), '
        f'China (3.2×), and Rest of World (3.7×). On a relative basis, Europe is the laggard. '
        f'Without deliberate investment, this trajectory continues.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def indexed_growth_chart(
    C,
    CHART_LAYOUT,
    REGION_COLORS,
    REGION_ORDER,
    df_monthly_regional,
    go,
    mo,
    pd,
):
    _df = df_monthly_regional.copy()
    _df["month"] = pd.to_datetime(_df["month"])
    _layout = {k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis", "margin", "legend")}
    _fig = go.Figure()
    for _region in REGION_ORDER:
        _subset = _df[_df["region"] == _region].sort_values("month")
        _base = float(_subset.iloc[0]["total_downloads"])
        _indexed = _subset["total_downloads"].astype(float) / _base * 100
        _last_month = _subset.iloc[-1]["month"]
        _last_idx = float(_subset.iloc[-1]["total_downloads"]) / _base * 100
        _fig.add_trace(go.Scatter(
            x=_subset["month"],
            y=_indexed,
            mode="lines",
            name=_region,
            line=dict(color=REGION_COLORS[_region], width=2),
            hovertemplate=f"<b>{_region}</b><br>%{{x|%b %Y}}: %{{y:.0f}} (indexed)<extra></extra>",
            showlegend=False,
        ))
        _fig.add_annotation(
            x=_last_month,
            y=_last_idx,
            text=f"  {_region} ({_last_idx:.0f})",
            showarrow=False,
            xanchor="left",
            font=dict(size=11, color=REGION_COLORS[_region]),
        )
    _fig.add_hline(
        y=100,
        line_dash="dot", line_color=C["rule"], line_width=1,
        annotation_text="May 2025 baseline",
        annotation_position="top left",
        annotation_font=dict(size=9, color=C["ink_3"]),
    )
    _fig.update_layout(
        **_layout,
        height=400,
        margin=dict(t=20, l=80, r=180, b=50),
        xaxis=dict(showgrid=False, linecolor=C["ink"], linewidth=1, tickformat="%b %Y"),
        yaxis=dict(
            title="Downloads index (May 2025 = 100)",
            showgrid=True, gridcolor=C["rule"],
            linecolor=C["ink"], linewidth=1,
        ),
    )
    _fig.update_layout(hovermode="x unified")
    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def section_eu(C, F, mo):
    mo.Html(
        f'<div style="margin:44px 0 20px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">'
        f'EU Spotlight, Absolute Downloads</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600;'
        f'color:{C["ink"]}; margin:0 0 8px;">'
        f'Ireland, Germany, and Netherlands dominate, with France 4th within the EU</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink_3"]}; '
        f'margin:0; line-height:1.5;">'
        f'PyPI AI package downloads within the EU-27 by country. '
        f"Ireland's outsized figure reflects cloud infrastructure (AWS eu-west-1, Google, Cloudflare). "
        f'Germany leads in end-user consumption. France (highlighted) sits 4th at 170M downloads, '
        f'significant, but below its potential as a major AI nation.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def eu_country_chart(C, CHART_LAYOUT, df_country_pop, df_eu_countries, go, mo):
    _df = df_eu_countries.copy()
    _df = _df.merge(df_country_pop[["country_code", "country_name"]], on="country_code", how="left")
    _df["label"] = _df["country_name"].fillna(_df["country_code"])
    _eu_total = _df["total_downloads"].sum()
    _df["pct"] = _df["total_downloads"] / _eu_total * 100
    _df = _df.sort_values("total_downloads", ascending=True)
    _colors = [C["healthy"] if cc == "FR" else C["accent"] for cc in _df["country_code"]]
    _opacities = [1.0 if cc in ("FR", "DE", "IE", "NL", "BE", "FI") else 0.55 for cc in _df["country_code"]]
    _layout = {k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis", "margin", "hovermode")}
    _fig = go.Figure(go.Bar(
        x=_df["total_downloads"],
        y=_df["label"],
        orientation="h",
        marker=dict(color=_colors, opacity=_opacities),
        text=[f"{v/1e6:.0f}M ({p:.1f}%)" for v, p in zip(_df["total_downloads"], _df["pct"])],
        textposition="outside",
        textfont=dict(size=9),
        hovertemplate="<b>%{y}</b><br>Downloads: %{x:,.0f}<extra></extra>",
    ))
    _fig.update_layout(
        **_layout,
        height=max(300, len(_df) * 26),
        hovermode="closest",
        margin=dict(t=20, l=110, r=120, b=50),
        xaxis=dict(
            title="Downloads (May 2025–Apr 2026)",
            showgrid=True, gridcolor=C["rule"],
            linecolor=C["ink"], linewidth=1,
            rangemode="tozero", tickformat=",.0f",
        ),
        yaxis=dict(showgrid=False),
    )
    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def section_eu_percapita(C, F, mo):
    mo.Html(
        f'<div style="margin:44px 0 20px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">'
        f'EU Spotlight, Per Capita</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600;'
        f'color:{C["ink"]}; margin:0 0 8px;">'
        f'Normalized for population, France falls below the EU median</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink_3"]}; '
        f'margin:0; line-height:1.5;">'
        f'Downloads per 1,000 people within the EU-27. Ireland remains an outlier due to cloud infrastructure. '
        f'Excluding Ireland, the Netherlands, Finland, and Luxembourg lead. '
        f'France (highlighted) sits below the EU median, a meaningful gap for the largest prospective funder '
        f'of European open-source AI.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def eu_percapita_chart(
    C,
    CHART_LAYOUT,
    df_country_pop,
    df_eu_countries,
    go,
    mo,
):
    _df = df_eu_countries.copy()
    _df = _df.merge(
        df_country_pop[["country_code", "country_name", "population"]],
        on="country_code", how="left",
    )
    _df["population"] = _df["population"].astype(float)
    _df = _df[_df["population"] > 0].copy()
    _df["downloads_per_1k"] = _df["total_downloads"] / _df["population"] * 1000
    _df["label"] = _df["country_name"].fillna(_df["country_code"])
    _df = _df.sort_values("downloads_per_1k", ascending=True)
    _eu_median = _df["downloads_per_1k"].median()
    _colors = [C["healthy"] if cc == "FR" else C["accent"] for cc in _df["country_code"]]
    _opacities = [1.0 if cc in ("FR", "IE", "NL", "FI", "LU", "DE") else 0.55 for cc in _df["country_code"]]
    _layout = {k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis", "margin", "hovermode")}
    _fig = go.Figure(go.Bar(
        x=_df["downloads_per_1k"],
        y=_df["label"],
        orientation="h",
        marker=dict(color=_colors, opacity=_opacities),
        text=[f"{v:,.0f}" for v in _df["downloads_per_1k"]],
        textposition="outside",
        textfont=dict(size=9),
        hovertemplate="<b>%{y}</b><br>Downloads per 1,000 people: %{x:,.0f}<extra></extra>",
    ))
    _fig.add_vline(
        x=_eu_median,
        line_dash="dot", line_color=C["slate"], line_width=1.5,
        annotation_text=f"EU median ({_eu_median:,.0f})",
        annotation_position="top",
        annotation_font=dict(size=9, color=C["slate"]),
    )
    _fig.update_layout(
        **_layout,
        height=max(300, len(_df) * 26),
        hovermode="closest",
        margin=dict(t=30, l=110, r=100, b=50),
        xaxis=dict(
            title="Downloads per 1,000 people (May 2025–Apr 2026)",
            showgrid=True, gridcolor=C["rule"],
            linecolor=C["ink"], linewidth=1,
            rangemode="tozero", tickformat=",.0f",
        ),
        yaxis=dict(showgrid=False),
    )
    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def section_regional_percapita(C, F, mo):
    mo.Html(
        f'<div style="margin:44px 0 20px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">'
        f'Per Capita Comparison</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600;'
        f'color:{C["ink"]}; margin:0 0 8px;">'
        f'The US downloads AI packages at 8× the EU rate, and 360× China\'s</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink_3"]}; '
        f'margin:0; line-height:1.5;">'
        f'Downloads per 1,000 people by region. Normalizing for population sharpens the story: '
        f'the US is not just larger: it is far more intensively engaged with open-source AI tooling. '
        f'China\'s low figure reflects its preference for domestic platforms rather than PyPI. '
        f'The EU\'s gap with the US is structural, not just demographic.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def regional_percapita_chart(
    C,
    CHART_LAYOUT,
    REGION_COLORS,
    REGION_ORDER,
    df_country_pop,
    df_regional_totals,
    go,
    mo,
):
    _EU_CODES = [
        "AT","BE","BG","CY","CZ","DE","DK","EE","ES","FI",
        "FR","GR","HR","HU","IE","IT","LT","LU","LV","MT",
        "NL","PL","PT","RO","SE","SI","SK",
    ]
    _pop_us = float(df_country_pop[df_country_pop["country_code"] == "US"]["population"].values[0])
    _pop_cn = float(df_country_pop[df_country_pop["country_code"] == "CN"]["population"].values[0])
    _pop_eu = float(df_country_pop[df_country_pop["country_code"].isin(_EU_CODES)]["population"].sum())
    _pop_world = float(df_country_pop["population"].astype(float).sum())
    _pop_row = _pop_world - _pop_us - _pop_cn - _pop_eu
    _pop_map = {
        "United States": _pop_us,
        "EU": _pop_eu,
        "China": _pop_cn,
        "Rest of World": _pop_row,
    }
    _df = df_regional_totals.copy()
    _df = _df.set_index("region").reindex(REGION_ORDER).reset_index()
    _df["population"] = _df["region"].map(_pop_map)
    _df["downloads_per_1k"] = _df["total_downloads"] / _df["population"] * 1000
    _layout = {k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis", "margin", "hovermode")}
    _fig = go.Figure(go.Bar(
        x=_df["region"],
        y=_df["downloads_per_1k"],
        marker_color=[REGION_COLORS[r] for r in _df["region"]],
        text=[f"{v:,.0f}" for v in _df["downloads_per_1k"]],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{x}</b><br>Downloads per 1,000 people: %{y:,.0f}<extra></extra>",
    ))
    _fig.update_layout(
        **_layout,
        height=380,
        hovermode="closest",
        margin=dict(t=40, l=60, r=20, b=50),
        xaxis=dict(showgrid=False, linecolor=C["ink"], linewidth=1),
        yaxis=dict(
            title="Downloads per 1,000 people (May 2025–Apr 2026)",
            showgrid=True, gridcolor=C["rule"],
            linecolor=C["ink"], linewidth=1,
            tickformat=",.0f", rangemode="tozero",
        ),
    )
    mo.ui.plotly(_fig, config={"displayModeBar": False})
    return


@app.cell(hide_code=True)
def section_packages(C, F, mo):
    mo.Html(
        f'<div style="margin:44px 0 20px;">'
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["accent"]}; '
        f'letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">'
        f'Package Mix</div>'
        f'<h2 style="font-family:{F["headline"]}; font-size:1.6rem; font-weight:600;'
        f'color:{C["ink"]}; margin:0 0 8px;">'
        f'The global top packages are US-origin, and no EU project reaches the top tier</h2>'
        f'<p style="font-family:{F["body"]}; font-size:0.9rem; color:{C["ink_3"]}; '
        f'margin:0; line-height:1.5;">'
        f'Top 10 of the 39 sampled packages by region. The rankings are strikingly convergent: scipy, uvicorn, fastapi, '
        f'transformers, and openai dominate everywhere. Select a region to explore its top packages.</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def package_region_selector(mo):
    region_selector = mo.ui.dropdown(
        options=["United States", "EU", "Rest of World", "China"],
        value="United States",
        label="Region",
    )
    return (region_selector,)


@app.cell(hide_code=True)
def package_mix_chart(
    C,
    CHART_LAYOUT,
    REGION_COLORS,
    df_top_packages,
    go,
    mo,
    region_selector,
):
    _region = region_selector.value
    _subset = (
        df_top_packages[df_top_packages["region"] == _region]
        .sort_values("total_downloads", ascending=True)
        .tail(10)
    )
    _layout = {k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis", "margin", "hovermode")}
    _fig = go.Figure(go.Bar(
        x=_subset["total_downloads"],
        y=_subset["package"],
        orientation="h",
        marker_color=REGION_COLORS[_region],
        text=[f"{v/1e6:.0f}M" for v in _subset["total_downloads"]],
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>Downloads: %{x:,.0f}<extra></extra>",
    ))
    _fig.update_layout(
        **_layout,
        height=340,
        hovermode="closest",
        margin=dict(t=20, l=130, r=80, b=50),
        xaxis=dict(
            title=f"Downloads, {_region} (May 2025–Apr 2026)",
            showgrid=True, gridcolor=C["rule"],
            linecolor=C["ink"], linewidth=1,
            rangemode="tozero", tickformat=",.0f",
        ),
        yaxis=dict(showgrid=False),
    )
    mo.vstack([
        region_selector,
        mo.ui.plotly(_fig, config={"displayModeBar": False}),
    ])
    return


@app.cell(hide_code=True)
def methodology(C, F, mo):
    mo.Html(
        f'<div style="margin-top:44px; padding-top:20px; border-top:1px solid {C["rule"]};">'    
        f'<div style="font-family:{F["mono"]}; font-size:10px; color:{C["ink_3"]}; '
        f'letter-spacing:0.08em; text-transform:uppercase; margin-bottom:8px;">Methodology</div>'
        f'<p style="font-family:{F["body"]}; font-size:0.85rem; color:{C["ink_3"]}; line-height:1.5;">'
        f'Download data sourced from PyPI public dataset, covering a sample of 39 AI packages '
        f'from the Current AI catalog (anthropic, browser-use, daytona, fastapi, firecrawl, jax, keras, '
        f'langchain, langflow, lightgbm, llama-index, markitdown, mcp-server-*, mem0ai, nltk, open-webui, '
        f'openai, opencv-python, pydantic-ai, scikit-learn, scipy, spacy, tensorflow, torch, transformers, '
        f'uvicorn, vllm, xgboost, and others). '
        f'Data spans May 1, 2025 – April 30, 2026 (12 complete months). '
        f"Country codes are as reported by PyPI's CDN logs. Ireland's large share reflects cloud provider "
        f'infrastructure (AWS eu-west-1, Google, Cloudflare) rather than purely end-user consumption. '
        f'Population figures sourced from the REST Countries API (restcountries.com), ingested May 2026. '
        f'All per capita figures use downloads per 1,000 people.</p>'
        f'<p style="font-family:{F["body"]}; font-size:0.85rem; color:{C["ink_3"]}; margin-top:8px;">'
        f'<strong>EU-27 countries included:</strong> AT, BE, BG, CY, CZ, DE, DK, EE, ES, FI, FR, GR, HR, '
        f'HU, IE, IT, LT, LU, LV, MT, NL, PL, PT, RO, SE, SI, SK. '
        f'China: CN. United States: US. Rest of World: all remaining country codes.</p>'
        f'<p style="font-family:{F["body"]}; font-size:0.85rem; color:{C["ink_3"]}; margin-top:8px;">'
        f'<strong>Source:</strong> '
        f'<a href="https://www.oso.xyz" style="color:{C["accent"]}">Open Source Observer</a>, '
        f'PyPI public download dataset, Current AI catalog, REST Countries API</p>'
        f'</div>'
    )
    return


@app.cell(hide_code=True)
def load_regional_totals(mo, pyoso_db_conn):
    df_regional_totals = mo.sql(
        f"""
        SELECT
          CASE
            WHEN country_code = 'US' THEN 'United States'
            WHEN country_code = 'CN' THEN 'China'
            WHEN country_code IN (
              'AT','BE','BG','CY','CZ','DE','DK','EE','ES','FI',
              'FR','GR','HR','HU','IE','IT','LT','LU','LV','MT',
              'NL','PL','PT','RO','SE','SI','SK'
            ) THEN 'EU'
            ELSE 'Rest of World'
          END AS region,
          SUM(downloads) AS total_downloads
        FROM currentai.catalog.pypi_downloads
        WHERE TIMESTAMP(day) < DATE('2026-05-01')
        GROUP BY 1
        ORDER BY total_downloads DESC
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_regional_totals,)


@app.cell(hide_code=True)
def load_monthly_regional(mo, pyoso_db_conn):
    df_monthly_regional = mo.sql(
        f"""
        SELECT
          DATE_TRUNC('month', TIMESTAMP(day)) AS month,
          CASE
            WHEN country_code = 'US' THEN 'United States'
            WHEN country_code = 'CN' THEN 'China'
            WHEN country_code IN (
              'AT','BE','BG','CY','CZ','DE','DK','EE','ES','FI',
              'FR','GR','HR','HU','IE','IT','LT','LU','LV','MT',
              'NL','PL','PT','RO','SE','SI','SK'
            ) THEN 'EU'
            ELSE 'Rest of World'
          END AS region,
          SUM(downloads) AS total_downloads
        FROM currentai.catalog.pypi_downloads
        WHERE TIMESTAMP(day) < DATE('2026-05-01')
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_monthly_regional,)


@app.cell(hide_code=True)
def load_top_packages(mo, pyoso_db_conn):
    df_top_packages = mo.sql(
        f"""
        WITH region_map AS (
          SELECT
            CASE
              WHEN country_code = 'US' THEN 'United States'
              WHEN country_code = 'CN' THEN 'China'
              WHEN country_code IN (
                'AT','BE','BG','CY','CZ','DE','DK','EE','ES','FI',
                'FR','GR','HR','HU','IE','IT','LT','LU','LV','MT',
                'NL','PL','PT','RO','SE','SI','SK'
              ) THEN 'EU'
              ELSE 'Rest of World'
            END AS region,
            package,
            downloads
          FROM currentai.catalog.pypi_downloads
          WHERE TIMESTAMP(day) < DATE('2026-05-01')
        ),
        agg AS (
          SELECT region, package, SUM(downloads) AS total_downloads
          FROM region_map
          GROUP BY region, package
        ),
        ranked AS (
          SELECT *,
            ROW_NUMBER() OVER (PARTITION BY region ORDER BY total_downloads DESC) AS rn
          FROM agg
        )
        SELECT region, package, total_downloads
        FROM ranked
        WHERE rn <= 10
        ORDER BY region, total_downloads DESC
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_top_packages,)


@app.cell(hide_code=True)
def load_eu_countries(mo, pyoso_db_conn):
    df_eu_countries = mo.sql(
        f"""
        SELECT
          country_code,
          SUM(downloads) AS total_downloads
        FROM currentai.catalog.pypi_downloads
        WHERE country_code IN (
          'AT','BE','BG','CY','CZ','DE','DK','EE','ES','FI',
          'FR','GR','HR','HU','IE','IT','LT','LU','LV','MT',
          'NL','PL','PT','RO','SE','SI','SK'
        )
        AND TIMESTAMP(day) < DATE('2026-05-01')
        GROUP BY country_code
        ORDER BY total_downloads DESC
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_eu_countries,)


@app.cell(hide_code=True)
def load_country_populations(mo, pyoso_db_conn):
    df_country_pop = mo.sql(
        f"""
        SELECT country_code, country_name, CAST(population AS BIGINT) AS population
        FROM currentai.catalog.country_populations
        WHERE CAST(population AS BIGINT) > 0
        """,
        output=False,
        engine=pyoso_db_conn
    )
    return (df_country_pop,)


@app.cell(hide_code=True)
def style():
    F = {
        "headline": "'Noto Serif', Georgia, serif",
        "body": "'Plus Jakarta Sans', -apple-system, system-ui, sans-serif",
        "mono": "'DM Mono', ui-monospace, SFMono-Regular, monospace",
    }
    C = {
        # Shared neutrals + structure (match ai-stack-map / products-view).
        "ink": "#0b252f",
        "ink_2": "#272726",
        "ink_3": "#8fa1a4",
        "paper": "#f7f6f6",
        "paper_2": "#f2f1f1",
        "rule": "#edecec",
        "white": "#ffffff",
        "border": "#a5bbbe",
        # Brand salmon ramp: deep = emphasis/highlight, fading to pale coral.
        "healthy": "#e86f57",
        "warm": "#f4886f",
        "signal": "#f8ad99",
        # Navy accent + cool slate pair for magnitude/secondary series.
        "accent": "#0b252f",
        "slate": "#3f5d68",
        "slate_mid": "#5f7e88",
        "slate_lt": "#a5bbbe",
    }
    LAYOUT = dict(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family=F["body"], size=12, color=C["ink"]),
        margin=dict(t=20, l=60, r=20, b=50),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
        ),
        hovermode="closest",
    )
    CHART_LAYOUT = LAYOUT
    return C, CHART_LAYOUT, F


@app.cell(hide_code=True)
def region_config(C):
    REGION_COLORS = {
        # Categorical, brand-harmonised: navy anchors the dominant US benchmark,
        # the salmon highlight lands on the EU (the report's subject), and the
        # two cool slates carry China + Rest of World.
        "United States": C["accent"],      # navy
        "EU": C["healthy"],                # deep salmon, editorial focus
        "China": C["slate_mid"],           # mid slate
        "Rest of World": C["slate_lt"],    # light slate
    }
    REGION_ORDER = ["United States", "EU", "Rest of World", "China"]
    return REGION_COLORS, REGION_ORDER


@app.cell(hide_code=True)
def fonts(mo):
    mo.Html(
        '<style>'
        '@import url("https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300;1,400;1,500&family=Noto+Serif:ital,wght@0,400;0,600;1,400&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap");'
        '</style>'
    )
    return


@app.cell(hide_code=True)
def imports():
    import pandas as pd
    import plotly.graph_objects as go
    return go, pd


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
