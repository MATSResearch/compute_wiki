"""A figure the reader can slice with a dropdown — and its static counterpart.

The interesting problem: a dropdown has **no static equivalent**. A PDF cannot
have a menu, so if you only build the interactive version, every slice but the
default silently vanishes from the saved document.

The answer is that the two halves of the pair are *different figures showing the
same data*: a dropdown when interactive, **small multiples** when static. This
module builds both from one call, so they cannot drift apart.

    from dropdown_figure import sliced_figure
    plotly_fig, mpl_fig = sliced_figure(
        {"baseline": (x, y0), "steered": (x, y1), "finetuned": (x, y2)},
        xlabel="layer", ylabel="probe accuracy", ylim=(0.4, 1.0))

Then hand both to `make_report.Report.figure(...)`.
"""
from __future__ import annotations

import math

import matplotlib
matplotlib.use("Agg")               # headless: the dev node has no display
import matplotlib.pyplot as plt     # noqa: E402
import plotly.graph_objects as go   # noqa: E402


def sliced_figure(series: dict, *, xlabel: str = "", ylabel: str = "",
                  ylim: tuple | None = None, title: str = ""):
    """(plotly figure with a dropdown, matplotlib figure of small multiples).

    `series` maps a slice name to an (x, y) pair.

    `ylim` is strongly recommended. Without it each slice auto-scales, so
    flipping the dropdown makes every slice look identical and destroys the
    comparison the figure exists to make — the same reason the small multiples
    below share one y-axis.
    """
    if not series:
        raise ValueError("sliced_figure() needs at least one series")
    names = list(series)

    # ---- interactive: one trace per slice, dropdown toggles visibility ----
    fig = go.Figure()
    for i, name in enumerate(names):
        x, y = series[name]
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=name,
                                 visible=(i == 0)))
    fig.update_layout(
        title=title or None,
        xaxis_title=xlabel, yaxis_title=ylabel,
        margin=dict(t=60),
        updatemenus=[dict(
            buttons=[dict(label=name, method="update",
                          args=[{"visible": [j == i for j in range(len(names))]},
                                {"title": f"{title} — {name}" if title else name}])
                     for i, name in enumerate(names)],
            direction="down", showactive=True,
            x=0, xanchor="left", y=1.18, yanchor="top",
        )],
    )
    if ylim:
        fig.update_yaxes(range=list(ylim))

    # ---- static: small multiples, SHARED axes so panels are comparable ----
    n = len(names)
    ncols = min(3, n)
    nrows = math.ceil(n / ncols)
    mpl_fig, axes = plt.subplots(nrows, ncols, figsize=(2.6 * ncols, 2.4 * nrows),
                                 sharex=True, sharey=True, squeeze=False)
    for ax, name in zip(axes.ravel(), names):
        x, y = series[name]
        ax.plot(x, y, marker="o", ms=3)
        ax.set_title(name, fontsize=9)
    for ax in axes.ravel()[n:]:         # hide unused panels
        ax.set_visible(False)
    if ylim:
        axes[0][0].set_ylim(*ylim)
    for ax in axes[-1]:
        ax.set_xlabel(xlabel, fontsize=8)
    for row in axes:
        row[0].set_ylabel(ylabel, fontsize=8)
    if title:
        mpl_fig.suptitle(title, fontsize=10)
    mpl_fig.tight_layout()
    return fig, mpl_fig


if __name__ == "__main__":
    import numpy as np
    from make_report import Report

    x = np.arange(1, 25)
    rng = np.random.default_rng(0)
    data = {name: (x, np.clip(0.5 + 0.02 * x + rng.normal(0, 0.03, x.size), 0, 1))
            for name in ("baseline", "steered", "finetuned")}

    pl, mp = sliced_figure(data, xlabel="layer", ylabel="probe accuracy",
                           ylim=(0.4, 1.05), title="Probe accuracy by layer")
    out = (Report("Dropdown demo")
           .markdown("Dropdown when interactive; small multiples when static.")
           .figure(pl, mp, caption="Probe accuracy by layer, per condition")
           .save("dropdown_demo.html"))
    plt.close(mp)
    print(f"wrote {out}")
