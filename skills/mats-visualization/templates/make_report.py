"""Build a self-contained HTML report where every plot exists twice.

Why twice: a reader wants to hover, zoom and filter — but the saved PDF has no
JavaScript. So each figure carries an **interactive** version (Plotly) and a
**static** version (a Matplotlib PNG inlined as a data URI). A viewer can switch
between them, and a PDF export keeps the static one.

The two `<div>` class names below are a contract with the MATS dashboard's
Automated Alignment tool, which toggles them and strips the interactive half
when rendering a PDF:

    <figure class="aa-plot">
      <div class="aa-plot-static">      <img src="data:image/png;base64,...">
      <div class="aa-plot-interactive"> ...Plotly...

Nothing here is dashboard-specific beyond those names — the output is an
ordinary standalone HTML file that opens anywhere.

Usage:

    from make_report import Report
    rep = Report("Scaling sweep")
    rep.markdown("Loss falls smoothly up to 3e-4, then diverges.")
    rep.figure(plotly_fig, mpl_fig, caption="Loss vs learning rate")
    rep.save("outputs/run_.../report.html")

Dependencies: `plotly`, `matplotlib`. Both are already in most research envs.
"""
from __future__ import annotations

import base64
import html
import io
from pathlib import Path

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="{cdn}"></script>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font: 15px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif;
         max-width: 60rem; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ font-size: 1.6rem; }}
  figure {{ margin: 2rem 0; }}
  figcaption {{ font-size: 0.9rem; opacity: 0.75; margin-top: 0.4rem; }}
  .aa-plot-static img {{ max-width: 100%; height: auto; }}
  /* The dashboard sets a mode class on <html>. Standalone, both are visible,
     so the file is still readable when opened directly in a browser. */
  html.aa-mode-static .aa-plot-interactive {{ display: none; }}
  html.aa-mode-interactive .aa-plot-static {{ display: none; }}
  .meta {{ font-size: 0.85rem; opacity: 0.7; border-top: 1px solid #8884;
          margin-top: 3rem; padding-top: 0.8rem; }}
</style>
</head>
<body>
<h1>{title}</h1>
{body}
<div class="meta">{meta}</div>
</body>
</html>
"""


class Report:
    """Accumulate prose and paired figures, then write one standalone file."""

    def __init__(self, title: str, meta: str = "") -> None:
        self.title = title
        self.meta = meta
        self._parts: list[str] = []
        self._n = 0

    def markdown(self, text: str) -> "Report":
        """A paragraph. Escaped — this is prose, not a place to inject markup."""
        self._parts.append(f"<p>{html.escape(text)}</p>")
        return self

    def html(self, raw: str) -> "Report":
        """Raw HTML, for a table or anything the helpers don't cover."""
        self._parts.append(raw)
        return self

    def figure(self, plotly_fig=None, mpl_fig=None, caption: str = "",
               dpi: int = 200) -> "Report":
        """One figure, in both forms.

        Passing only one is allowed but discouraged: a figure with no static
        version silently disappears from the PDF, and one with no interactive
        version is just a picture.
        """
        if plotly_fig is None and mpl_fig is None:
            raise ValueError("figure() needs at least one of plotly_fig / mpl_fig")
        self._n += 1

        static = ""
        if mpl_fig is not None:
            buf = io.BytesIO()
            mpl_fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
            b64 = base64.b64encode(buf.getvalue()).decode()
            alt = html.escape(caption or f"Figure {self._n}")
            static = (f'<div class="aa-plot-static">'
                      f'<img alt="{alt}" src="data:image/png;base64,{b64}">'
                      f"</div>")

        interactive = ""
        if plotly_fig is not None:
            # include_plotlyjs=False: the library is loaded once in <head>, so
            # ten figures don't mean ten copies of Plotly in the file.
            inner = plotly_fig.to_html(full_html=False, include_plotlyjs=False,
                                       default_height="420px")
            interactive = f'<div class="aa-plot-interactive">{inner}</div>'

        cap = f"<figcaption>{html.escape(caption)}</figcaption>" if caption else ""
        self._parts.append(
            f'<figure class="aa-plot">{static}{interactive}{cap}</figure>')
        return self

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_PAGE.format(
            title=html.escape(self.title),
            cdn=PLOTLY_CDN,
            body="\n".join(self._parts),
            meta=html.escape(self.meta),
        ), encoding="utf-8")
        return path


if __name__ == "__main__":
    # Smoke test: `python make_report.py` writes a two-figure report.
    import matplotlib
    matplotlib.use("Agg")          # headless: the dev node has no display
    import matplotlib.pyplot as plt
    import numpy as np
    import plotly.graph_objects as go

    x = np.linspace(0, 10, 60)
    y = np.sin(x)
    lo, hi = y - 0.15, y + 0.15

    mpl_fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.plot(x, y, marker="o", ms=3)
    ax.fill_between(x, lo, hi, alpha=0.2)
    ax.set_xlabel("steering magnitude")
    ax.set_ylabel("refusal rate")
    mpl_fig.tight_layout()

    pl_fig = go.Figure([
        go.Scatter(x=x, y=hi, line=dict(width=0), showlegend=False,
                   hoverinfo="skip"),
        go.Scatter(x=x, y=lo, fill="tonexty", line=dict(width=0),
                   name="95% CI", hoverinfo="skip"),
        go.Scatter(x=x, y=y, mode="lines+markers", name="refusal rate"),
    ])
    pl_fig.update_layout(xaxis_title="steering magnitude",
                         yaxis_title="refusal rate", margin=dict(t=20))

    out = (Report("Smoke test", meta="generated by make_report.py")
           .markdown("Both versions of the same figure.")
           .figure(pl_fig, mpl_fig, caption="Refusal rate vs steering magnitude")
           .save("report_smoke_test.html"))
    plt.close(mpl_fig)
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
