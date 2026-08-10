# Marimo Notebook Design Guide

This document translates the Current AI website design system into concrete values for the Marimo notebook (`ai-stack-map.py`). The goal is visual alignment without a pixel-perfect match — the notebook is a data environment, the site is a marketing/editorial one, so some adaptation is expected.

---

## Fonts

The site uses three typefaces. Replace the notebook's current fonts with these:

| Role | Notebook (current) | Site equivalent | Google Fonts import |
|------|--------------------|-----------------|---------------------|
| Headlines / category names | Fraunces | **Noto Serif** | `family=Noto+Serif:ital,wght@0,400;0,600;1,400` |
| Body / UI text | Inter | **Plus Jakarta Sans** | `family=Plus+Jakarta+Sans:ital,wght@0,300..800;1,300..800` |
| Monospace / labels / metadata | JetBrains Mono | **DM Mono** | `family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300;1,400;1,500` |

Update the `F` dict and the `load_fonts` cell:

```python
# load_fonts cell
mo.Html(
    '<style>'
    '@import url("https://fonts.googleapis.com/css2?'
    'family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300;1,400;1,500'
    '&family=Noto+Serif:ital,wght@0,400;0,600;1,400'
    '&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800'
    '&display=swap");'
    '</style>'
)

# style cell F dict
F = {
    "headline": "'Noto Serif', Georgia, serif",
    "body": "'Plus Jakarta Sans', -apple-system, system-ui, sans-serif",
    "mono": "'DM Mono', ui-monospace, SFMono-Regular, monospace",
}
```

---

## Color Palette

Replace the warm sepia palette in the `C` dict with the site's palette:

```python
C = {
    # Backgrounds
    "paper":    "#f7f6f6",   # site --paper  (was #f5f1ea)
    "paper_2":  "#f2f1f1",   # site --light-grey (was #ede7dc)
    "white":    "#ffffff",   # pure white for cards / modal backgrounds

    # Text
    "ink":      "#0b252f",   # site --dark-blue — primary text (was #1a1814)
    "ink_2":    "#272726",   # site --dark-grey — secondary text (was #3a342b)
    "ink_3":    "#a5bbbe",   # site --light-blue — muted/disabled (was #6b6253)

    # Borders / rules
    "rule":     "#edecec",   # site --grid-line (was #c9bfac)
    "border":   "#a5bbbe",   # site --light-blue for heavier borders (was #c9bfac)

    # Semantic / data colors
    "signal":   "#f88376",   # site --salmon — open / highlight (was #c8341d red)
    "healthy":  "#f88376",   # same salmon — site doesn't use a separate green
    "warm":     "#fbc7bf",   # site --pink — open-ish / secondary (was #d97c2a)
    "accent":   "#0b252f",   # site --dark-blue — active states (was #2a3d8f)

    # Gaps
    "gap_red":  "#ff0d0d",   # site --bright-red — gap diamond icons
}
```

### Openness color mapping

The site encodes openness through **shape** (full square vs. triangle) rather than color. For the notebook's color-coded approach, align the three buckets to the site palette:

| Bucket | Notebook (current) | Updated value | Hex |
|--------|-------------------|---------------|-----|
| Open | `healthy` #1b6b5e (green) | `signal` | `#f88376` (salmon) |
| Open-ish | `warm` #d97c2a (orange) | `warm` | `#fbc7bf` (pink) |
| Closed | `ink_3` #6b6253 (brown) | `ink_2` | `#272726` (dark grey) |

Update `_ocolor()` to match:

```python
def _ocolor(score):
    if score is None:
        return C["rule"]       # #edecec
    if score >= 4:
        return C["signal"]     # #f88376 salmon — open
    if score == 3:
        return C["warm"]       # #fbc7bf pink — open-ish
    if score == 2:
        return C["ink_2"]      # #272726 — borderline
    return C["ink_3"]          # #a5bbbe — closed / muted
```

Bullet chips (● open / open-ish / closed) should use the same three colors.

---

## Typography Scale

The site's type is slightly larger and more spaced than the notebook's current settings. Recommended adjustments:

| Context | Current | Updated |
|---------|---------|---------|
| Page / notebook title (h1) | 2.2rem, Fraunces 400 | 2.2rem, Noto Serif **600**, tracking `-0.025em` |
| Section headings (h2) | 1.6rem, Fraunces 500 | 1.6rem, Noto Serif **600**, tracking `-0.015em` |
| Category label | 1.05rem, Fraunces 500 | 1.05rem, Noto Serif 600 |
| Modal title | 1.4rem, Fraunces 500 | 1.4rem, Noto Serif 600 |
| Body / descriptions | 0.95rem, Inter | 0.95rem, Plus Jakarta Sans |
| Control labels | 10px, JetBrains Mono, `uppercase`, `0.08em` tracking | same size, **DM Mono**, keep uppercase + tracking |
| Table column headers | 9px, mono, `uppercase` | same, DM Mono |
| Monospace metadata (arc labels, scores) | 10–11px, JetBrains Mono | same size, DM Mono |
| Verdict pills | 0.72rem, mono | 0.72rem, DM Mono |

The site uses `font-weight: 600` on headings (Noto Serif), **not** 500. Update headline weights accordingly.

---

## Backgrounds & Surfaces

| Surface | Current | Updated |
|---------|---------|---------|
| Page / notebook background | `#f5f1ea` | `#f7f6f6` (--paper) |
| Row / card background | `#ede7dc` | `#f2f1f1` (--light-grey) |
| Modal / detail panels | `#ffffff` | `#ffffff` (unchanged) |
| Active nav / selected button | `#2a3d8f` | `#0b252f` (--dark-blue) |
| Modal backdrop | `rgba(26,24,20,0.55)` | `rgba(11,37,47,0.55)` (dark-blue tint) |

---

## Interactive Controls (buttons, filter bar)

The site's button style is minimal with `--light-blue` borders and `--dark-blue` text. Update button CSS:

```css
/* Resting state */
.v3ctrl-bar button, .lt-bar .lt-btn {
    font-family: 'DM Mono', ui-monospace, monospace;
    font-size: 11px;
    border: 1px solid #a5bbbe;    /* --light-blue */
    background: #ffffff;
    color: #0b252f;               /* --dark-blue */
    border-radius: 0;             /* site uses square corners, not rounded */
    padding: 5px 12px;
    cursor: pointer;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* Active state */
.v3ctrl-bar button.active, .lt-bar .lt-btn.active {
    background: #0b252f;          /* --dark-blue */
    color: #f2f1f1;               /* --light-grey */
    border-color: #0b252f;
}
```

Note the **`border-radius: 0`** — the site uses sharp corners throughout, not rounded.

---

## Details Modal

```css
.v3-modal {
    background: #ffffff;
    border-radius: 0;             /* sharp corners — site uses no rounding on panels */
    max-width: 780px;
    width: 100%;
    padding: 24px 28px;
    box-shadow: 0px 4px 4px 0px rgba(0,0,0,0.05);  /* site --shadow-xs */
}

.v3-modal h2 {
    font-family: 'Noto Serif', Georgia, serif;
    font-weight: 600;
    font-size: 1.4rem;
    letter-spacing: -0.015em;
    color: #0b252f;
}

.v3-sect {
    font-family: 'DM Mono', ui-monospace, monospace;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #0b252f;
    opacity: 0.5;
    font-weight: 600;
    border-bottom: 1px solid #edecec;   /* --grid-line */
    padding-bottom: 4px;
}

.v3-lbl {
    color: #a5bbbe;                     /* --light-blue (muted) */
    font-family: 'DM Mono', ui-monospace, monospace;
    font-size: 11px;
}

/* Close button */
.v3-x {
    border: 1px solid #a5bbbe;
    border-radius: 0;
    color: #a5bbbe;
    font-size: 11px;
    padding: 4px 10px;
}
```

---

## Score Bars

Keep the 5-segment bar structure. Update colors:

```python
def _bars(value, on_color):
    v = int(value) if isinstance(value, (int, float)) else 0
    empty = "#edecec"   # --grid-line (was paper_2 #ede7dc)
    return "".join(
        f'<span style="display:inline-block; width:6px; height:14px; margin-right:2px; '
        f'vertical-align:middle; background:{on_color if j < v else empty};"></span>'
        for j in range(5)
    )
```

---

## Gap Icons

The site renders gap indicators as **rotated squares** (diamonds) in `--bright-red` with a white letter. Match this in the notebook:

```python
def _gap_icon(letter):
    return (
        f'<span style="'
        f'display:inline-flex; align-items:center; justify-content:center; '
        f'width:14px; height:14px; position:relative; flex-shrink:0;">'
        f'<span style="'
        f'position:absolute; inset:0; transform:rotate(45deg); '
        f'background:#ff0d0d;"></span>'   # --bright-red
        f'<span style="'
        f'position:relative; font-family:\'Plus Jakarta Sans\',sans-serif; '
        f'font-size:8px; font-weight:800; text-transform:uppercase; '
        f'color:#ffffff; line-height:1;">{letter}</span>'
        f'</span>'
    )
```

---

## Borders & Dividers

The site uses a very light `--grid-line` (`#edecec`) for all internal dividers and a slightly heavier `--light-blue` (`#a5bbbe`) for component borders. Replace all uses of the notebook's `C["rule"]` (`#c9bfac`) accordingly:

- Row dividers, table borders → `#edecec`
- Component / card borders → `#a5bbbe`

---

## Summary of key value swaps

| What | Old | New |
|------|-----|-----|
| Page background | `#f5f1ea` | `#f7f6f6` |
| Card/row bg | `#ede7dc` | `#f2f1f1` |
| Primary text | `#1a1814` | `#0b252f` |
| Secondary text | `#3a342b` | `#272726` |
| Muted text | `#6b6253` | `#a5bbbe` |
| Dividers | `#c9bfac` | `#edecec` |
| Component borders | `#c9bfac` | `#a5bbbe` |
| Active / accent | `#2a3d8f` | `#0b252f` |
| Open (data) | `#1b6b5e` | `#f88376` |
| Open-ish | `#d97c2a` | `#fbc7bf` |
| Gap icons | `#c8341d` | `#ff0d0d` |
| Headline font | Fraunces | Noto Serif |
| Body font | Inter | Plus Jakarta Sans |
| Mono font | JetBrains Mono | DM Mono |
| Border radius | 4–10px | 0 (sharp corners) |

---

## Implementation notes — where the notebooks diverge from this guide

Everything above (typography, neutrals, surfaces, sharp corners, the navy
structural accent, the single-salmon brand highlight) is applied as written —
that is what carries the "looks like the site" resemblance.

The one place we adapted is **data color**. The site encodes openness through
*shape* (square vs triangle) and uses salmon as a sparing editorial accent. The
notebooks are dense data instruments: they color-encode an ordinal 0–5 openness
scale, three independent axes, a 4-way distribution, and verdict states. Mapping
those onto the site's two data hues 1:1 collapsed distinct values (open read the
same as restricted) and produced low-contrast / heavy-black bars. Per this
guide's own note that "some adaptation is expected," we made these deliberate,
reviewed changes (signed off by Carl; worth confirming with the CF design team):

**Openness → a single-hue salmon *sequential* ramp** (deepest = most open,
fading to a pale-but-legible coral for closed). One ordered intensity scale, so
open vs restricted are unambiguous and "warmth = openness" — open products carry
the most color, matching how the site uses salmon as the highlight.

| Openness | Hex |
|----------|-----|
| Open (≥4) | `#e86f57` |
| Open-ish (3) | `#f4886f` |
| Restricted (2) | `#f8ad99` |
| Closed (≤1) | `#f6cabd` |
| No score | `#dcdcda` |

**Adoption & capability → a quiet cool slate pair**, so the openness column is
the only place color lives: adoption `#8aa6ac` (light slate), capability
`#3f5d68` (dark slate).

**Verdict pills → one neutral tag** (`#f2f1f1` fill, navy text) for all five
states. The verdict is categorical, not ordinal, so color-coding it on the
salmon ramp made "open-ish leads" and "closed leads" look alike; the color
story already lives in the open / open-ish / closed chips beside it.

**Header eyebrow** trimmed from `Current AI · Open Source AI Map · v3` to just
`Current AI`.

These values live in the `C` dict of `build/render.py` (ai-stack-map, generated).

---

## Authoring conventions

The palette and type above are written against `ai-stack-map.py`. The conventions in this
section apply to **every** marimo notebook in the repo — the generated one, the companion
notebooks, and local exploration alike.

### Section structure

1. Header — eyebrow, serif title, framing paragraph
2. KPI strip
3. Overview chart
4. Detail chart
5. Table or ranked detail
6. Methodology and sources

Every chart gets a markdown framing cell before it. Keep filters (`mo.ui.dropdown`) in
dedicated cells. End the notebook with methodology and source notes.

### Queries

Keep SQL cells bounded and reproducible: explicit date windows, explicit filters, deterministic
ordering. Explain methodology assumptions inline rather than leaving them to the reader.

### KPI cards

Prefer `mo.stat()` for compact KPI strips:

```python
mo.hstack([
    mo.stat(value=f"{repos:,}", label="Repos", bordered=True, caption="across the AI stack"),
    mo.stat(value=f"{stars:,}", label="Stars", bordered=True, caption="community adoption"),
    mo.stat(value=f"{contributors:,}", label="Contributors", bordered=True, caption="active developers"),
], widths="equal", gap=1)
```

Three to six stats per row, `bordered=True`, a caption carrying context or timeframe, and
thousands separators or suffixes on large numbers.

### Charts

Always disable the Plotly mode bar:

```python
mo.ui.plotly(fig, config={"displayModeBar": False})
```

Defaults that have held up: horizontal bars for ranked categorical comparisons, chart height
scaled to row count, scatter with quadrant guides for coverage-versus-depth reads, and treemaps
for market-map overviews.
