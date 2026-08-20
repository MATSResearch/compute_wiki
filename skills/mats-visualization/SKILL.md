---
name: mats-visualization
description: Plot safety-research results so a reader believes them. Use BEFORE writing any plotting code, and whenever making a figure, chart, graph or heatmap, choosing a colormap or palette, plotting a sweep across layers or magnitudes, showing multiple seeds, adding error bars to a figure, or saving figures from a run; also when the user mentions matplotlib, seaborn, plotly, altair, colorbar, axis limits, or a figure for a paper or write-up.
---

# Visualization for MATS safety research

Read this before writing plotting code. Full detail:
<https://matsresearch.github.io/compute_wiki/engineering/visualization/>

## Pick the library

| Goal | Library |
|---|---|
| Figure for a paper or write-up | **Matplotlib**, saved as PDF/SVG |
| Quick distribution check mid-experiment | **seaborn** (`boxplot`, `violinplot`, `stripplot`) |
| Interactive exploration, or an HTML report to send someone | **Plotly** |
| Faceted small multiples, declarative | **Altair** (slow past ~5k rows) |

Producing a report that needs **both** an interactive and a static version of
each plot: Plotly for the interactive, Matplotlib PNG for the static.

## The rules that matter

- **Sweeps get a confidence band, not a bare line.** `ax.fill_between(x, lo, hi,
  alpha=0.2)`, plus a dashed baseline. A bare line invites belief in every
  wiggle.
- **Show the spread, not just the mean.** With ≤30 points per condition, plot
  them all (`stripplot` + `pointplot`) — the reader sees bimodality, outliers
  and n at a glance. A bar chart of four means with no error bars is the least
  informative figure in safety research.
- **Diverging colormaps must be centred at zero.** For anything signed (logit
  diffs, attributions, steering effects): `imshow(v, cmap="RdBu_r", vmin=-m,
  vmax=m)` with `m = max(abs(v.min()), abs(v.max()))`. Without symmetric limits
  Matplotlib centres on the data range, so an all-positive matrix renders with a
  blue region that reads as negative. Sequential (`viridis`) for magnitudes.
- **Show every seed.** Faint per-seed lines plus a bold mean. If the faint lines
  cross freely, the mean curve is not a finding.
- **Never truncate a bar chart's y-axis.** Starting at 0.6 to inflate a 2-point
  difference is the classic misleading figure.
- **Fix y-limits across small multiples**, or the panels cannot be compared —
  which was the point of small multiples.
- **Label the error bar and the n.** "Accuracy" is not an axis label;
  "Accuracy (500 held-out prompts)" is.

## Colour

- Sequential → `viridis` / `cividis`. **Never `jet` or `rainbow`** — they invent
  visual edges that are not in the data.
- Diverging → `RdBu_r` / `coolwarm`, centred at zero.
- Categories → Okabe–Ito, which is colour-blind safe:
  `["#0072B2","#E69F00","#009E73","#CC79A7","#56B4E9","#D55E00","#F0E442","#000000"]`
- **Never encode a distinction by colour alone** — vary line style or marker too,
  so it survives greyscale and a colour-blind reader.

## Saving

- **PDF/SVG** for documents (reviewers zoom), **PNG at `dpi≥200`** for slides and
  chat. Default 100 dpi looks blurry.
- Save into the run's own `plots/` directory beside its `metadata.json`. A plot
  that cannot be traced to a config is not evidence.
- **Save the plotted numbers too** (`.csv`/`.npz`) — restyling later shouldn't
  mean re-running the experiment.
- Set the figure to its final printed size (`figsize=(5, 3.2)` for one column)
  rather than shrinking a big one, or the text ends up unreadable.

## Symptoms worth recognising

- `UserWarning: Matplotlib is currently using agg, which is a non-GUI backend` →
  `plt.show()` on a headless node. Save to a file instead.
- `RuntimeWarning: More than 20 figures have been opened` → missing
  `plt.close(fig)` in a loop; memory climbs.
- `ValueError: x and y must have same first dimension` → the off-by-one from
  plotting a per-step metric against an epoch axis.

Which error bar to draw, and on what unit: use the **mats-statistics** skill.
