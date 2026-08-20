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

## Which library should I use?

| Library | Use it for | Avoid it for |
|---|---|---|
| **Matplotlib** (`matplotlib.pyplot`, usually `import matplotlib.pyplot as plt`) | Anything going into a paper, thesis or write-up. Full control; vector output. | Fast interactive exploration — it is verbose for that. |
| **seaborn** (`import seaborn as sns`) | Quick distribution views: `sns.boxplot`, `sns.violinplot`, `sns.stripplot`, `sns.heatmap`. Sensible defaults over Matplotlib. | Final figures where you need exact control — but you can start here and tune the underlying Matplotlib axes. |
| **Plotly** (`plotly.express` / `plotly.graph_objects`) | Interactive exploration, hover-to-inspect, and HTML reports you send to someone. Writes a self-contained `.html`. | Static publication figures — the exported static images need `kaleido` and are fiddlier than Matplotlib. |
| **Altair** (`altair`) | Declarative grammar-of-graphics plots, especially faceted small multiples. | Very large datasets — it embeds data in the spec and gets slow past ~5k rows without special handling. |

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

---

Last verified: 2026-08. Drafted by Claude for Nathan's review — the
recommendations here are a first pass and have not yet been reviewed by the MATS
research staff. Matplotlib, seaborn, Plotly and Altair APIs verified against
current releases. PaCMAP (JMLR 2021) and LocalMAP (AAAI 2025,
arXiv:2412.15426 — ships inside the `pacmap` package) verified against their
repositories; WeightWatcher alpha ranges follow the Heavy-Tailed
Self-Regularization (HTSR) framework as documented by the project.
