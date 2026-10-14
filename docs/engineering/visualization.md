---
tags:
  - engineering
---

# Data Visualization for Safety Research

How to plot results so a reader believes them — and so *you* notice when they're
wrong. Aimed at the figures MATS fellows actually make: sweeps, per-layer
curves, eval comparisons, attention and activation heatmaps, and the one summary
figure that ends up in a write-up.

The libraries throughout are **Matplotlib** (`matplotlib` on PyPI),
**seaborn** (`seaborn`), **Plotly** (`plotly`), and occasionally **Altair**
(`altair`). Statistical questions — which error bar, which test — live in
[`statistics.md`](statistics.md).

## At a glance

| I want to... | Use | Section |
|---|---|---|
| A publication figure for a paper or write-up | Matplotlib, saved as PDF or SVG | [Which library](#which-library-should-i-use) |
| An interactive plot to explore results myself | Plotly | [Which library](#which-library-should-i-use) |
| A quick look at a distribution mid-experiment | seaborn | [Which library](#which-library-should-i-use) |
| Show a sweep (magnitude, layer, threshold) | Line plot with a confidence band | [Sweeps](#sweeps-line-plus-band-not-bare-points) |
| Compare a handful of conditions | Bar chart with error bars, or a dot plot | [Comparisons](#comparisons-show-the-spread-not-just-the-mean) |
| Show per-layer or per-head structure | Heatmap with a **diverging** colormap centred at zero | [Heatmaps](#heatmaps-per-layer-per-head-attention) |
| Show several runs / seeds at once (if you ran them) | Faint per-run lines plus a bold mean | [Multiple runs](#showing-multiple-runs-if-you-have-them) |
| Show distributions side by side | Violin plot with the points overlaid | [Violin plots](#violin-plots) |
| Project activations / embeddings to 2D | **PaCMAP or LocalMAP**, not t-SNE or UMAP | [Dimensionality reduction](#dimensionality-reduction-pacmap-and-localmap-not-t-sne) |
| Show what fine-tuning changed in the weights | Delta-weight magnitude plots; WeightWatcher alpha | [Weight-change plots](#weight-change-plots-what-did-fine-tuning-actually-move) |
| Let a reader switch subset / method in one figure | Plotly dropdown (`updatemenus`) | [Interactive dropdowns](#interactive-plots-with-dropdown-menus) |
| Make it readable to a colour-blind reader | `viridis` / `cividis`, or Okabe–Ito for categories | [Colour](#colour-choices-that-survive-a-colour-blind-reader-and-a-greyscale-printer) |
| Make a figure's size and fonts match the NeurIPS / ICML / ICLR template | **tueplots** bundles (SciencePlots for a house style) | [Sizing for a paper](#sizing-figures-for-a-paper-column-tueplots-and-scienceplots) |
| Explore results in a notebook without hidden state, diffable in git | **marimo** reactive notebooks | [marimo](#reactive-notebooks-for-exploring-results-marimo) |
| Browse thousands of embedded transcripts, completions or features | **Embedding Atlas**, fed your own PaCMAP/LocalMAP coordinates | [Browsing a projection](#browsing-a-projection-embedding-atlas) |
| Plot straight from Inspect eval logs | **Inspect Viz** views | [Which library](#which-library-should-i-use) |

## Which library should I use?

| Library | Use it for | Avoid it for |
|---|---|---|
| **Matplotlib** (`matplotlib.pyplot`, usually `import matplotlib.pyplot as plt`) | Anything going into a paper, thesis or write-up. Full control; vector output. | Fast interactive exploration — it is verbose for that. |
| **seaborn** (`import seaborn as sns`) | Quick distribution views: `sns.boxplot`, `sns.violinplot`, `sns.stripplot`, `sns.heatmap`. Sensible defaults over Matplotlib. | Final figures where you need exact control — but you can start here and tune the underlying Matplotlib axes. |
| **Plotly** (`plotly.express` / `plotly.graph_objects`) | Interactive exploration, hover-to-inspect, and HTML reports you send to someone. Writes a self-contained `.html`. | Static publication figures — the exported static images need `kaleido` and are fiddlier than Matplotlib. |
| **Altair** (`altair`) | Declarative grammar-of-graphics plots, especially faceted small multiples. | Very large datasets — it embeds data in the spec and gets slow past ~5k rows without special handling. |
| **pyobsplot** (`pyobsplot` on PyPI, `juba/pyobsplot`; v0.5.4, 2025-07-11) | Observable Plot from Python dicts, as a notebook widget (Jupyter, marimo, Quarto) or static SVG/PNG/PDF via typst (`uv add "pyobsplot[typst]"`). | Tooltips in static output (SVG, PNG, PDF, static HTML) — interactions exist only in the widget format; and the `typst` extra does not work under pyodide (JupyterLite, marimo WebAssembly). |
| **Inspect Viz** (`inspect-viz` on PyPI, `meridianlabs-ai/inspect_viz`; 0.4.1, 2026-07-09) | Pre-built views over Inspect AI log dataframes: `scores_by_task`, `scores_by_model`, `scores_by_factor`, `scores_by_limit`, `sample_tool_calls`, with tooltips that can link to published log transcripts (when the data has a `log_viewer` column). | Fully styled paper figures — it is interactive-first (static export is covered in its Publishing docs); Matplotlib is simpler for exact control. |

```python
# Inspect Viz, from its docs: a parquet written from inspect_ai.analysis dataframes
from inspect_viz import Data
from inspect_viz.view import scores_by_task
scores_by_task(Data.from_file("evals.parquet"))
```

Notebook environments are a separate choice from the plotting library; see
[marimo](#reactive-notebooks-for-exploring-results-marimo).

For the MATS dashboard's Automated Alignment tool specifically: reports want
**both** an interactive version and a static image of every plot, because the
static one is what gets saved to PDF. Plotly for the interactive, Matplotlib PNG
for the static.

## Sweeps: line plus band, not bare points

A sweep over steering magnitude, layer index, or a threshold should show
uncertainty as a band. A bare line invites the reader to believe every wiggle.

```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(5, 3.2))
ax.plot(x, mean, marker="o", label="steered")
ax.fill_between(x, ci_low, ci_high, alpha=0.2)   # 95% CI from statistics.md
ax.axhline(baseline, ls="--", c="0.4", label="baseline")
ax.set_xlabel("steering magnitude")
ax.set_ylabel("refusal rate")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("outputs/run_.../plots/magnitude_sweep.pdf")
```

Three things that make this figure honest: the **band** (uncertainty), the
**baseline line** (the comparison the reader needs), and an axis that is not
truncated (see below).

## Comparisons: show the spread, not just the mean

A bar chart of four means with no error bars is the least informative figure in
safety research. Prefer showing the underlying points:

```python
import seaborn as sns
ax = sns.stripplot(data=df, x="condition", y="score", alpha=0.5, jitter=0.2)
sns.pointplot(data=df, x="condition", y="score", errorbar=("ci", 95),
              join=False, color="k", ax=ax)
```

With few points (say ≤ 30 per condition), plotting them all is strictly better
than a box plot — the reader sees bimodality, outliers and n at a glance.

**Always label what the error bar is.** "Mean ± 95% CI over 500 prompts" and
"mean ± 1 std over 5 seeds" look identical on the page and mean entirely
different things. Put it in the caption or the axis label.

## Heatmaps: per-layer, per-head, attention

For anything that can be positive or negative — logit differences, attribution
scores, steering effects — use a **diverging** colormap centred at zero, or the
figure lies about the sign.

```python
import matplotlib.pyplot as plt
m = max(abs(values.min()), abs(values.max()))
im = ax.imshow(values, cmap="RdBu_r", vmin=-m, vmax=m)   # symmetric!
fig.colorbar(im, ax=ax, label="logit diff")
```

Setting `vmin=-m, vmax=m` is the load-bearing part: without it, Matplotlib
centres the colormap on the data range, so a matrix of entirely positive values
renders with a big blue region that reads as negative.

For strictly-positive quantities (attention weights, magnitudes) use a
sequential map — `viridis` — not a diverging one.

## Showing multiple runs (if you have them)

```python
for s, curve in per_seed.items():
    ax.plot(x, curve, color="C0", alpha=0.25, lw=1)     # every seed, faint
ax.plot(x, np.mean(list(per_seed.values()), axis=0), color="C0", lw=2.5,
        label="mean (n=5 seeds)")
```

Use this when you happen to have several runs; a seed sweep is an optional
strengthening step, not a prerequisite for plotting a result. When you do have
them, showing every run is much more honest than a mean with an error bar — if
the faint lines cross freely, the mean curve is not yet a finding. Where error
bars come from when you have a single run:
[Where error bars actually come from](statistics.md#where-error-bars-actually-come-from).

## Violin plots

A violin plot shows the whole distribution's shape, not just its quartiles —
which is what you want when an intervention might be *bimodal* (helps half the
prompts, hurts the other half). A box plot hides exactly that, and a bar chart
of means erases it completely.

```python
import seaborn as sns
ax = sns.violinplot(data=df, x="condition", y="score",
                    inner=None, cut=0, density_norm="width")
sns.stripplot(data=df, x="condition", y="score",
              color="k", alpha=0.4, size=3, ax=ax)   # the actual points
```

Two settings do most of the work:

- **`cut=0`** stops the kernel density estimate extending past the range of the
  real data. Without it a violin of accuracies happily draws mass above 1.0 and
  below 0.0, which is not a thing that can happen.
- **`density_norm="width"`** (called `scale="width"` in seaborn < 0.13) makes
  every violin the same width, so shapes are comparable. Use `"count"` if you
  *want* width to encode n — but say so, or a reader will misread it.

**Overlay the points.** A violin is a kernel density estimate, so with small n
it invents smooth structure from very little: six points can produce a confident
double bump. Below ~20 points per group, prefer a strip or swarm plot on its
own. Above that, violin plus points is the best of both.

For paired conditions, a split violin (`hue=..., split=True`) puts before and
after on one axis and reads far better than two separate violins.

## Dimensionality reduction: PaCMAP and LocalMAP, not t-SNE

Projecting activations, residual-stream states, sparse-autoencoder (SAE)
features or embeddings down to 2D is standard practice — and the default tools
are a poor choice.

**Prefer [PaCMAP](https://github.com/YingfanWang/PaCMAP)** (Pairwise Controlled
Manifold Approximation and Projection; `pacmap` on PyPI; Wang, Huang, Rudin and
Shaposhnik, JMLR 2021). It preserves **both** local and global structure, where
t-SNE (t-distributed Stochastic Neighbor Embedding) preserves only local
structure and UMAP (Uniform Manifold Approximation and Projection) sits between
the two. It is also fast and needs far less hyperparameter fiddling than t-SNE's
perplexity.

**When the question is specifically "are these separate clusters?", prefer
[LocalMAP](https://github.com/williamsyy/LocalMAP)** (Wang, Sun, Huang and
Rudin, Duke; *Dimension Reduction with Locally Adjusted Graphs*, AAAI 2025,
[arXiv:2412.15426](https://arxiv.org/abs/2412.15426)). It adjusts the neighbour
graph dynamically and locally during the final optimisation stage, which pulls
apart real clusters that PaCMAP, UMAP and t-SNE tend to merge or miss entirely.
It ships **inside the `pacmap` package**, so there is nothing extra to install.

```python
import pacmap
emb = pacmap.PaCMAP(n_components=2, n_neighbors=10).fit_transform(X)
# or, when the question is "are these genuinely distinct clusters?":
emb = pacmap.LocalMAP(n_components=2).fit_transform(X)
```

### Read these plots honestly

This is where dimensionality-reduction figures mislead, whatever the algorithm:

- **Distance between clusters is not meaningful** in t-SNE, and only partly so
  in UMAP. PaCMAP is better about global structure — but never quote a gap as
  though it were a measured distance.
- **Cluster size and density are artefacts.** A tight blob is not "more
  coherent"; the algorithm chose that spacing.
- **Layout changes with the seed and the neighbour count.** Run it two or three
  ways before believing a structure, and say which settings made the figure.
- **A 2D projection is a hypothesis generator, not evidence.** If clusters look
  separated, confirm it in the original space — a linear probe, a clustering
  score, a held-out classification — and report *that* number.

### Browsing a projection: Embedding Atlas

**Embedding Atlas** (`embedding-atlas` on PyPI, `apple/embedding-atlas` on
GitHub, Apple; Ren, Hohman, Lin and Moritz,
[arXiv:2505.06386](https://arxiv.org/abs/2505.06386); v0.25.0, 2026-10-03,
Python ≥ 3.11) is a browser app for exploring a large embedded collection:
density contours, automatic cluster labels, nearest-neighbour search, and
linked charts over the other columns that cross-filter each other. The README
claims "up to a few million points, powered by WebGPU". It is useful for
reading through thousands of transcripts, completions, judge rationales or
sparse-autoencoder (SAE) feature explanations by region. It also runs as a
notebook widget (`from embedding_atlas.widget import EmbeddingAtlasWidget;
EmbeddingAtlasWidget(df)`) and as an npm component. `--mcp` exposes a Model
Context Protocol (MCP) server so an agent can query the schema, run SQL,
create charts and take screenshots. `--export-application atlas.zip` writes a
standalone web app.

**Its default projection is UMAP.** If you pass a text, image or vector column
without coordinates, it embeds the data and runs UMAP (Uniform Manifold
Approximation and Projection; the `--umap-*` flags tune it). To follow the
PaCMAP/LocalMAP recommendation in the section above, compute the 2D
coordinates yourself and pass them in. Supplying `--x` and `--y` already skips
the projection step; `--disable-projection` makes that explicit:

```python
import pacmap
emb = pacmap.LocalMAP(n_components=2).fit_transform(X)
df["localmap_x"], df["localmap_y"] = emb[:, 0], emb[:, 1]
df.to_parquet("outputs/run_.../atlas.parquet")
```

```bash
embedding-atlas outputs/run_.../atlas.parquet --text transcript \
  --x localmap_x --y localmap_y --disable-projection \
  --export-application outputs/run_.../atlas.zip
```

The automatic cluster labels and density contours are computed on the **2D
layout**, so they inherit every caveat in *Read these plots honestly*: a
labelled island is a hypothesis about the original space, not a measurement of
it.

**When not to use it.** For a static figure in a paper or PDF, use Matplotlib.
And with its default UMAP projection, it is not a basis for claims about
global structure or cluster separation.

## Weight-change plots: what did fine-tuning actually move?

Useful for model-organism work, fine-tuning safety research, and anything asking
"how much did this change the model, and where?".

### Delta-weight magnitude, per layer

Compare the fine-tuned weights against the base model directly:

```python
import numpy as np
rows = []
for name in base_sd:                       # matching state_dict keys
    if base_sd[name].ndim < 2:             # skip biases / norms
        continue
    d = (tuned_sd[name] - base_sd[name]).float()
    w = base_sd[name].float()
    rows.append(dict(
        layer=name,
        rel_frob=(d.norm() / w.norm()).item(),               # size of the change
        frac_moved=(d.abs() > 1e-4).float().mean().item(),   # how many moved
        max_abs=d.abs().max().item(),
    ))
```

Plot `rel_frob` as one horizontal bar per layer, ordered by depth. The *shape* of
that plot is the finding: a fine-tune concentrated in a few late layers tells a
very different story from one smeared across the whole stack.

**A histogram of `|Δw|` on a log y-axis** is the companion figure — it separates
"a few weights moved a lot" from "everything moved a little". Use
`ax.set_yscale("log")`; on a linear axis the interesting tail is invisible
because the near-zero bin dominates everything.

**The spectrum of ΔW** (`np.linalg.svdvals`) answers "is this change low-rank?",
which is directly relevant when choosing or justifying a LoRA (Low-Rank
Adaptation) rank. Plot the singular values and the cumulative energy, per layer.

### WeightWatcher: layer quality without any data

[WeightWatcher](https://github.com/CalculatedContent/WeightWatcher)
(`weightwatcher` on PyPI, Charles Martin) fits a power law to the tail of each
weight matrix's eigenvalue spectrum and reports the exponent **alpha (α)**. It
needs **no training or test data** — it reads the weights alone, which makes it
a cheap sanity check on a fine-tune.

```python
import weightwatcher as ww
details = ww.WeightWatcher(model=model).analyze()
details.plot(x="layer_id", y="alpha")
```

Under Heavy-Tailed Self-Regularization (HTSR) theory the rough reading is:

| alpha | Interpretation |
|---|---|
| >= 5–6 | Random-like spectrum — little task structure learned |
| 2 – 5 | Well-conditioned; generally generalises well |
| ~ 2 | About as well-fit as the layer gets |
| < 2 | Very heavy-tailed — a signal of overfitting |

The useful figure is **alpha per layer, base versus fine-tuned, on the same
axes**: layers whose alpha dropped below 2 are where your fine-tune may have
overfit. Treat it as a diagnostic that tells you where to look, not as a result
on its own — it is a heuristic from one specific theory, not a measurement of
behaviour.

## Interactive plots with dropdown menus

When results have several slices — subset, method, layer, model — a dropdown
beats both twelve static panels and a single figure that averages the
interesting structure away. Plotly does this with `updatemenus`, and the output
is a self-contained HTML file you can send to someone.

```python
import plotly.graph_objects as go

methods = ["baseline", "steered", "finetuned"]
fig = go.Figure()
for i, m in enumerate(methods):
    d = df[df.method == m]
    fig.add_trace(go.Scatter(x=d.x, y=d.y, mode="lines+markers",
                             name=m, visible=(i == 0)))

fig.update_layout(updatemenus=[dict(
    buttons=[dict(label=m, method="update",
                  args=[{"visible": [j == i for j in range(len(methods))]},
                        {"title": f"Refusal rate — {m}"}])
             for i, m in enumerate(methods)],
    direction="down", x=0, xanchor="left", y=1.15, yanchor="top",
)])
fig.write_html("outputs/run_.../plots/by_method.html", include_plotlyjs="cdn")
```

Three things worth getting right:

- **Fix the axis ranges** (`fig.update_yaxes(range=[0, 1])`). If each slice
  auto-scales, flipping the dropdown makes every slice look identical and the
  comparison — the entire point — is destroyed.
- **`include_plotlyjs="cdn"`** keeps the file small; use `True` to inline the
  library if the reader may be offline.
- **Always export a static image of the default view too.** A dropdown cannot go
  in a PDF, and the interactive file is not what a reviewer sees.

For only a few slices, `plotly.express` facets
(`px.line(df, x=..., y=..., facet_col="method")`) mean less clicking and print
properly — prefer them over a menu when they fit.

## Reactive notebooks for exploring results: marimo

**marimo** (`marimo` on PyPI, `marimo-team/marimo` on GitHub; 0.25.1,
2026-10-01; Apache-2.0; Python ≥ 3.10) is a reactive Python notebook. Running a
cell, or moving a slider, re-runs the cells that depend on it (or marks them
stale), so the notebook cannot hold hidden state left by deleted or
out-of-order cells, a common reason a Jupyter result does not reproduce. The
file is a plain `.py` module: it diffs in git, `python notebook.py` runs it as a
script, and command-line arguments reach `sys.argv`.

```bash
uvx marimo edit --sandbox notebook.py        # per-notebook uv venv; deps written inline (PEP 723)
marimo convert old_notebook.ipynb > notebook.py
python notebook.py                            # run as a script
marimo export html notebook.py -o outputs/run_.../report.html -- --run-dir outputs/run_...
```

In sandbox mode each notebook carries its own requirements, so a collaborator
can open it without your environment. A sandbox isolates packages only; it is
not a security boundary.

**A caveat for widgets.** marimo hosts anywidget widgets (for example
wigglystuff's `ParallelCoordinates`). A static `marimo export html` file has no
Python kernel behind it: the widget itself still draws and brushes, but Python
cells that depend on the widget's selection stay frozen at their exported
values. Under a strict Content Security Policy (CSP) in a sandboxed frame, such as the MATS
dashboard's report viewer, a marimo export containing such a widget did not
render at all in a 2026-10 test (marimo 0.25.1), because the widget loads its
code from a `data:` URL. For a report someone else will open, export static
figures (PNG/PDF) or Plotly HTML alongside.

**When not to use it.** When collaborators depend on Jupyter-only extensions,
or when the deliverable is a self-contained HTML report that has to keep
widget interactivity live.

## Colour choices that survive a colour-blind reader and a greyscale printer

- **Sequential data** → `viridis` or `cividis`. Both are perceptually uniform and
  colour-blind safe. Never `jet` or `rainbow`: they invent visual edges that are
  not in the data.
- **Diverging data** → `RdBu_r` or `coolwarm`, always centred at zero.
- **Categories** → the Okabe–Ito palette, which is designed for colour-blind
  readers:

```python
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#CC79A7",
             "#56B4E9", "#D55E00", "#F0E442", "#000000"]
```

- **Never encode a distinction by colour alone.** Vary line style or marker too,
  so the figure still works in greyscale and for a reader who cannot separate
  the hues.

## Axes, scales and the things that mislead

- **Do not truncate a y-axis** on a bar chart. Starting at 0.6 to make a
  2-point difference look enormous is the classic misleading figure. On a line
  plot a non-zero baseline is fine — say so in the caption.
- **Use a log x-axis for anything swept over orders of magnitude** (learning
  rates, model sizes, token counts): `ax.set_xscale("log")`.
- **Label units and n.** "Accuracy" is not a label; "Accuracy (500 held-out
  prompts)" is.
- **Fix the y-limits across small multiples.** Panels with different auto-scaled
  axes cannot be compared, which is the entire point of small multiples.

## Sizing figures for a paper column: tueplots and SciencePlots

A figure made at the default `figsize=(6.4, 4.8)` and shrunk to a 3.25-inch
column ends up with 5-point text. Set the figure to its printed size and the
fonts to the paper's sizes from the start.

**tueplots** (`tueplots` on PyPI, `pnkraemer/tueplots` on GitHub, University of
Tübingen; v0.2.5, 2026-10-12) returns plain Matplotlib `rcParams` dictionaries
with figure size (from the template's text width), font sizes and fonts for a
given venue. It keeps no global state: you apply the dictionary with
`plt.rcParams.update(...)` or scope it with `plt.rc_context(...)`. Bundles as
of v0.2.5 include `neurips2021`–`neurips2024`, `icml2022`, `icml2024`,
`iclr2023`, `iclr2024`, `colm2026`, `aistats2022`/`2023`/`2025`, `cvpr2024`,
`aaai2024`, `uai2023`, `eccv2024`, `tmlr2023` and `jmlr2001`. There is no
NeurIPS 2025/2026 or ICML 2025/2026 bundle yet; it is worth checking the newest
template's `\textwidth` against the closest bundle before relying on it.

```python
import matplotlib.pyplot as plt
from tueplots import bundles, cycler
from tueplots.constants.color import palettes

plt.rcParams.update(bundles.icml2024(column="half", nrows=1, ncols=2, usetex=False))
plt.rcParams.update(cycler.cycler(color=palettes.paultol_muted))  # colour-blind-safe Paul Tol palette
fig, axes = plt.subplots(1, 2)        # size now comes from the bundle; don't pass figsize
```

`usetex=True` is the default for the NeurIPS, ICML, ICLR, COLM and CVPR
bundles and needs a LaTeX install; on a bare cluster node pass
`usetex=False`. NeurIPS/ICLR-style bundles take `rel_width=` instead of
`column=`. The Paul Tol palettes (`paultol_bright`, `paultol_muted`,
`paultol_vibrant`, `paultol_high_contrast`, `paultol_medium_contrast`) are
colour-blind-safe alternatives to Okabe–Ito.

**SciencePlots** (`SciencePlots` on PyPI, `garrettj403/SciencePlots`; 2.2.2,
2026-06-23) registers Matplotlib styles: `science`, journal styles `ieee` and
`nature` (which also set those journals' column widths), and colour cycles such
as `bright` (colour-blind safe) and `high-vis`. It sets a look; it has no
ML-conference templates, which is what tueplots is for. Since 2.0.0 you need
`import scienceplots` before `plt.style.use(...)`, and the `science` style
needs LaTeX unless you add `no-latex`:

```python
import matplotlib.pyplot as plt
import scienceplots  # registers the styles

plt.style.use(["science", "no-latex", "bright"])
```

**When not to use them.** For slides, chat and interactive HTML, physical size
does not matter; the defaults plus `dpi≥200` are fine.

## Saving figures so they're usable later

```python
fig.savefig(run_dir / "plots" / "sweep.pdf", bbox_inches="tight")   # vector, for the paper
fig.savefig(run_dir / "plots" / "sweep.png", dpi=200, bbox_inches="tight")  # raster, for slides/chat
```

- **Vector (PDF or SVG) for anything going into a document** — it stays sharp at
  any zoom, and reviewers do zoom.
- **PNG at `dpi≥200` for slides, Slack and chat surfaces.** The default 100 dpi
  looks blurry on a modern screen.
- Save into the run's own `plots/` directory, next to the `metadata.json` that
  says which config produced it — per the run-directory convention in
  [`code-recipes.md`](code-recipes.md#reproducibility-patterns). A plot you
  cannot trace back to a config is not evidence.
- **Save the numbers next to the picture.** A `.csv` or `.npz` of the plotted
  values costs nothing and saves re-running the experiment when you want to
  restyle the figure.

## Pitfalls, with the symptoms you'd actually see

- **`UserWarning: Matplotlib is currently using agg, which is a non-GUI backend`**
  — you called `plt.show()` on a headless node. Save to a file instead; on a
  cluster you almost never want an interactive backend.
- **Figures accumulate and memory climbs across a loop** — you never closed
  them. Call `plt.close(fig)` at the end of each iteration; the warning is
  `RuntimeWarning: More than 20 figures have been opened`.
- **Text is unreadably small in the paper.** You made a large figure and scaled
  it down. Set the figure to its final printed size (`figsize=(5, 3.2)` for a
  single column) and leave it there.
- **The colorbar contradicts the data's sign** — a diverging colormap without
  symmetric `vmin`/`vmax`. See [Heatmaps](#heatmaps-per-layer-per-head-attention).
- **`ValueError: x and y must have same first dimension`** — the classic off-by-
  one from plotting a per-step metric against an epoch axis.
- **`RuntimeError: Failed to process string with tex because latex could not
  be found`** — `text.usetex` is on (the default in tueplots' NeurIPS/ICML/ICLR
  bundles, and in the SciencePlots `science` style) on a machine without LaTeX.
  Pass `usetex=False` to the tueplots bundle, or add the `no-latex` style.
- **`ValueError: 'CC6677' is not a valid value for color`** (from `ax.plot`;
  `ax.scatter`/`ax.bar` word it differently, and `matplotlib.colors.to_rgba`
  says `Invalid RGBA argument: 'CC6677'`) — a tueplots palette entry passed
  directly as `color=`. The palettes store hex without the `#`;
  they work through `cycler.cycler(color=...)`, but a single entry needs
  `"#" + palettes.paultol_muted[0]`.
- **A plot that cannot be traced to a run.** If the filename is `plot3_final_v2.png`
  and lives on your desktop, it is not evidence. Timestamped run directory, or
  it did not happen.

## Where this connects

- Which error bar to draw, and on what unit:
  [`statistics.md`](statistics.md).
- Run-directory layout and `metadata.json`:
  [`code-recipes.md`](code-recipes.md#reproducibility-patterns).
- Logging figures to Weights & Biases (`wandb`) during a run:
  [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).
- Eval-specific statistics behind the error bars (clustered items, judge
  correction, IRT): [`eval-statistics.md`](../evaluation/eval-statistics.md).

---

Last verified: 2026-10-14. Drafted by Claude for Nathan's review — the
recommendations here are a first pass and have not yet been reviewed by the MATS
research staff. Matplotlib, seaborn, Plotly and Altair APIs verified against
current releases. PaCMAP (JMLR 2021) and LocalMAP (AAAI 2025,
arXiv:2412.15426 — ships inside the `pacmap` package) verified against their
repositories; WeightWatcher alpha ranges follow the Heavy-Tailed
Self-Regularization (HTSR) framework as documented by the project.
(Additions 2026-10-14: tueplots bundle list, `usetex` defaults and palette
format read from `tueplots/bundles.py` and `constants/color/palettes.py` at
v0.2.5; SciencePlots styles and the `import scienceplots` requirement from its
README; marimo commands from its README and `docs/guides`; the marimo
widget-export result from the MATS dashboard's 2026-10 parallel-coordinates
test; Embedding Atlas flags and its UMAP default read from
`packages/backend/embedding_atlas/cli.py` and `projection.py`; pyobsplot
limitations from its README; Inspect Viz views from its docs; the two error
strings reproduced with Matplotlib 3.11.2.)
