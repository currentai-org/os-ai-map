# CurrentAI Notebooks Guide

## Scope

Use this guide for notebook authoring:
- create new marimo notebooks
- read/update existing notebooks
- run notebooks for analysis and reporting

## Core commands

```bash
uv run marimo edit notebooks/<your_notebook>.py
uv run marimo run notebooks/<your_notebook>.py
```

## Notebook guidance

- Keep SQL cells bounded and reproducible (date windows, filters, deterministic ordering).
- Prefer clear sectioning and explain methodology assumptions inline.

## Persona note

- `pyoso-analyst`: notebook work + read-only `pyoso` querying (no MCP/write).
- OSO-internal users may use other OSO-managed MCP skills not defined in this repository.

## Pointers

- Query conventions: [`docs/guides/queries.md`](queries.md)
- Model inventory: [`warehouse/models/README.md`](../../warehouse/models/README.md)

---

## CurrentAI Notebook Style

Visual identity for Current AI ecosystem mapping notebooks. Derived from the website design system (warm editorial palette) with adaptations for data analysis.

Use this style for all notebooks in this project: both hosted (oso.xyz) and local exploration.

### Layout constants (`LAYOUT` + `F` + `C`)

Three constants work together: `F` (font stacks), `C` (semantic colors), and `LAYOUT` (Plotly base).

```python
@app.cell(hide_code=True)
def _():
    F = {
        "headline": "Fraunces, Georgia, serif",
        "body": "Inter, -apple-system, system-ui, sans-serif",
        "mono": "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace",
    }
    C = {
        "ink": "#1a1814",
        "ink_2": "#3a342b",
        "ink_3": "#6b6253",
        "paper": "#f5f1ea",
        "paper_2": "#ede7dc",
        "rule": "#c9bfac",
        "signal": "#c8341d",
        "healthy": "#1b6b5e",
        "warm": "#d97c2a",
        "accent": "#2a3d8f",
    }
    LAYOUT = dict(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family=F["body"], size=12, color=C["ink"]),
        margin=dict(t=20, l=60, r=20, b=50),
        hovermode="closest",
    )
    return C, F, LAYOUT
```

Key principles:
- Warm palette (`paper`) rather than cold grayscale.
- Fraunces for display text, Inter for body/UI, JetBrains Mono for numeric/data labels.
- Semantic color keys (`C['signal']`, `C['healthy']`) rather than ad hoc hex values.
- Health encoding: `healthy` (>=70), `warm` (45-69), `signal` (<45).

### Color and health helper

```python
def health_color(score):
    if score >= 70:
        return C["healthy"]
    elif score >= 45:
        return C["warm"]
    return C["signal"]
```

Use category palettes only when category identity matters; otherwise use accent + health semantic colors.

### Typography

- Headlines: `F["headline"]`, lighter editorial weight (around 400-500).
- Body copy: `F["body"]`, readable defaults around 0.95rem/12-13px equivalent.
- Eyebrows/table headers/technical labels: `F["mono"]`.

### KPI cards

Prefer `mo.stat()` for compact KPI strips:

```python
mo.hstack([
    mo.stat(value=f"{repos:,}", label="Repos", bordered=True, caption="across the AI stack"),
    mo.stat(value=f"{stars:,}", label="Stars", bordered=True, caption="community adoption"),
    mo.stat(value=f"{contributors:,}", label="Contributors", bordered=True, caption="active developers"),
], widths="equal", gap=1)
```

Rules:
- 3-6 stats per row
- `bordered=True`
- captions include context/timeframe
- numeric formatting uses separators/suffixes when large

### Charts

Always disable Plotly mode bar:

```python
mo.ui.plotly(fig, config={"displayModeBar": False})
```

Defaults:
- Horizontal bars for ranked categorical comparisons
- Dynamic chart height based on row count for readability
- Health scatter with quadrant guides for coverage/depth analysis
- Treemaps for market-map style overview when useful

### Section structure

Recommended flow:
1. Header (eyebrow + serif title + framing paragraph)
2. KPI strip
3. Overview chart
4. Detail chart
5. Table / ranked detail
6. Methodology + sources

Rules:
- Every chart gets a markdown framing cell before it.
- End notebooks with methodology/source notes.
- Keep filters (`mo.ui.dropdown`) in dedicated cells.

### When to use this style

Apply this style to all notebooks in this repo, including:
- trends/developer activity
- gap analysis
- data inventory
- taxonomy mapping
- geography-specific cuts (for example France view)

