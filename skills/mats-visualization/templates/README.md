# Data-viz templates

Runnable starting points, not a library. Copy one into your project and edit it.

| File | What it does |
|---|---|
| `make_report.py` | Builds a **self-contained HTML report** where every figure exists twice — interactive (Plotly) and static (Matplotlib PNG, inlined as a data URI). |
| `dropdown_figure.py` | A figure the reader slices with a **dropdown**, plus its static counterpart as **small multiples**. |
| `heatmap_grid.py` | A single heatmap and a **grid of small multiples on one shared colour scale** — symmetric limits for signed data, `LogNorm`, annotated cells, undefined cells marked. |

Each runs standalone as a smoke test:

```bash
python make_report.py        # writes report_smoke_test.html
python dropdown_figure.py    # writes dropdown_demo.html
python heatmap_grid.py       # writes heatmap_single.png, heatmap_grid.png
```

Needs `plotly` and `matplotlib`.

## Why every figure is built twice

A reader wants to hover, zoom and filter. A saved PDF has no JavaScript. Build
only the interactive version and the PDF loses the plot; build only the static
one and you have shipped a picture.

So each figure carries both, inside one `<figure class="aa-plot">`:

```html
<figure class="aa-plot">
  <div class="aa-plot-static"><img src="data:image/png;base64,..."></div>
  <div class="aa-plot-interactive"><!-- Plotly --></div>
</figure>
```

Those two class names are a **contract with the MATS dashboard's Automated
Alignment tool**, which toggles between them in its viewer and strips the
interactive half when exporting a PDF. Verified against that tool's extractor:
a report from `make_report.py` round-trips with the static image intact and the
Plotly half removed.

Nothing else is dashboard-specific — the output is an ordinary standalone HTML
file that opens anywhere, with both versions visible when opened directly.

## The trap worth knowing

**A dropdown has no static equivalent.** A PDF cannot have a menu, so if you
build only the interactive version, every slice but the default silently
disappears from the saved document. `dropdown_figure.py` handles this by making
the static half *a different figure showing the same data* — small multiples
with shared axes — generated from the same call, so the two cannot drift apart.

## Heatmaps

`heatmap_grid.py` exists because heatmaps are underused and the ways they go
wrong are mechanical:

- a **shared colour scale** across a grid, or the panels cannot be compared,
  which was the whole reason for the grid;
- **symmetric limits** for signed data, or an all-positive matrix renders with a
  blue region that reads as negative;
- **`LogNorm`** for anything spanning orders of magnitude, or you get one bright
  cell and a field of black;
- **undefined cells marked** with `×` on grey, not left blank — blank reads as
  "measured, and it was nothing";
- **cell annotations whose colour is chosen from the cell's luminance.** Fixed
  white text vanishes on the pale middle of a diverging map, which is precisely
  where the near-zero values live — so the numbers you most need to read are the
  ones that disappear.

Related reading:
[`visualization.md`](../../../docs/engineering/visualization.md) for plotting
craft, and
[`research-plots.md`](../../../docs/engineering/research-plots.md) for which
figures are worth making at all.
