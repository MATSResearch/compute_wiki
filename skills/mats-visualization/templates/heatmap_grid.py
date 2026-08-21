"""Heatmaps done properly: a single panel, and a grid of small multiples.

Heatmaps are underused relative to what they carry — a transformer result is
usually indexed by layer × head × position × time, and a grid of heatmaps shows
all four at once. What makes them go wrong is mechanical, so it is worth having
right once:

- a **shared colour scale** across a grid, or the panels cannot be compared —
  which was the entire reason for making a grid;
- **symmetric limits** for signed data, or an all-positive matrix renders with a
  blue region that reads as negative;
- **`LogNorm`** for anything spanning orders of magnitude (gradient norms,
  attention), or you get one bright cell and a field of black;
- **undefined cells marked**, not left blank — blank reads as "measured, and it
  was nothing", which is a different and wrong claim;
- **real tick labels** (tokens, layer names), not array indices.

    from heatmap_grid import heatmap, heatmap_grid
    fig = heatmap(values, xticks=tokens, yticks=layers,
                  cbar_label="logit diff", signed=True)
    fig = heatmap_grid({f"L{i}": v for i, v in enumerate(per_layer)},
                       cbar_label="attention", lognorm=True)
"""
from __future__ import annotations

import math

import matplotlib
matplotlib.use("Agg")                     # headless: the dev node has no display
import matplotlib.pyplot as plt           # noqa: E402
import numpy as np                        # noqa: E402
from matplotlib.colors import LogNorm     # noqa: E402


def _limits(values, signed: bool, lognorm: bool):
    """Colour limits. Signed data gets symmetric limits around zero so the
    colormap's midpoint means zero rather than 'middle of the data range'."""
    finite = values[np.isfinite(values)]
    if lognorm:
        pos = finite[finite > 0]
        return dict(norm=LogNorm(vmin=pos.min(), vmax=pos.max())) if pos.size else {}
    if signed:
        m = float(np.abs(finite).max()) if finite.size else 1.0
        return dict(vmin=-m, vmax=m)
    return dict(vmin=float(finite.min()), vmax=float(finite.max()))


def heatmap(values, *, xticks=None, yticks=None, xlabel="", ylabel="",
            cbar_label="", signed=False, lognorm=False, annotate=None,
            title="", ax=None, figsize=(5.2, 4.0)):
    """One heatmap.

    `signed=True` uses a diverging colormap with symmetric limits — use it for
    anything that can be positive or negative (logit differences, attribution,
    steering effects). `annotate` is an array of the same shape whose values are
    written into the cells, for when the exact number matters as well as the
    pattern.

    NaNs are drawn in grey and are legible as "no value here", rather than
    silently taking the colour of zero.
    """
    values = np.asarray(values, dtype=float)
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    cmap = plt.get_cmap("RdBu_r" if signed else "viridis").copy()
    cmap.set_bad("0.85")                  # undefined cells are visibly absent
    im = ax.imshow(np.ma.masked_invalid(values), cmap=cmap, aspect="auto",
                   interpolation="nearest", **_limits(values, signed, lognorm))

    if xticks is not None:
        ax.set_xticks(range(len(xticks)))
        ax.set_xticklabels(xticks, rotation=90, fontsize=7)
    if yticks is not None:
        ax.set_yticks(range(len(yticks)))
        ax.set_yticklabels(yticks, fontsize=7)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=10)

    if annotate is not None:
        annotate = np.asarray(annotate)
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                if not np.isfinite(values[i, j]):
                    ax.text(j, i, "×", ha="center", va="center",
                            color="0.35", fontsize=8)
                    continue
                # Pick the text colour from the cell's actual luminance. Fixed
                # white annotations vanish on the pale cells of a diverging map
                # — which is exactly where the near-zero values are, so the
                # numbers you most need to read are the ones that disappear.
                r, g, b, _ = im.cmap(im.norm(values[i, j]))
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                ax.text(j, i, f"{annotate[i, j]}", ha="center", va="center",
                        color="k" if lum > 0.55 else "w", fontsize=7)

    if fig is not None:
        # Name the quantity. "attention", "logit diff" and "probe accuracy" are
        # three different claims and look identical without a label.
        fig.colorbar(im, ax=ax, label=cbar_label)
        fig.tight_layout()
    return fig if fig is not None else im


def heatmap_grid(panels: dict, *, xticks=None, yticks=None, xlabel="",
                 ylabel="", cbar_label="", signed=False, lognorm=False,
                 ncols=4, panel_size=(2.4, 2.0), suptitle=""):
    """A grid of heatmaps on ONE shared colour scale.

    The shared scale is the point: it is what makes "head 7 in layer 3 is doing
    something the others are not" a readable claim rather than an artefact of
    per-panel autoscaling.
    """
    if not panels:
        raise ValueError("heatmap_grid() needs at least one panel")
    names = list(panels)
    stacked = np.asarray([np.asarray(panels[n], dtype=float) for n in names])
    lim = _limits(stacked, signed, lognorm)

    n = len(names)
    ncols = min(ncols, n)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(panel_size[0] * ncols, panel_size[1] * nrows),
                             squeeze=False)

    cmap = plt.get_cmap("RdBu_r" if signed else "viridis").copy()
    cmap.set_bad("0.85")
    im = None
    for ax, name in zip(axes.ravel(), names):
        im = ax.imshow(np.ma.masked_invalid(np.asarray(panels[name], dtype=float)),
                       cmap=cmap, aspect="auto", interpolation="nearest", **lim)
        ax.set_title(name, fontsize=8)
        ax.set_xticks([])
        ax.set_yticks([])
    for ax in axes.ravel()[n:]:
        ax.set_visible(False)

    if xticks is not None:
        for ax in axes[-1][:min(ncols, n)]:
            ax.set_xticks(range(len(xticks)))
            ax.set_xticklabels(xticks, rotation=90, fontsize=6)
    if yticks is not None:
        for row in axes:
            row[0].set_yticks(range(len(yticks)))
            row[0].set_yticklabels(yticks, fontsize=6)
    for ax in axes[-1]:
        ax.set_xlabel(xlabel, fontsize=8)
    for row in axes:
        row[0].set_ylabel(ylabel, fontsize=8)
    if suptitle:
        fig.suptitle(suptitle, fontsize=11)

    fig.tight_layout()
    fig.colorbar(im, ax=axes.ravel().tolist(), label=cbar_label, shrink=0.85)
    return fig


if __name__ == "__main__":
    rng = np.random.default_rng(0)

    # Signed single panel with some undefined cells, annotated with counts.
    vals = rng.normal(0, 1, (6, 8))
    vals[0, 7] = np.nan                    # a combination that cannot exist
    counts = rng.integers(0, 40, vals.shape)
    f1 = heatmap(vals, cbar_label="logit diff", signed=True, annotate=counts,
                 xlabel="position", ylabel="layer", title="Patching effect")
    f1.savefig("heatmap_single.png", dpi=200, bbox_inches="tight")

    # A (layer, head) grid on one shared scale, log-scaled.
    panels = {f"L{i}": rng.lognormal(0, 1.4, (12, 12)) for i in range(8)}
    f2 = heatmap_grid(panels, cbar_label="grad norm", lognorm=True,
                      xlabel="head", ylabel="head", suptitle="Per-layer grid")
    f2.savefig("heatmap_grid.png", dpi=200, bbox_inches="tight")

    plt.close("all")
    print("wrote heatmap_single.png and heatmap_grid.png")
