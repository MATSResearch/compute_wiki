"""Minimal plotting helpers backed by matplotlib.

Matplotlib is an optional dependency — these functions raise a friendly ImportError
if it isn't installed. Most plot helpers take a destination path and save the figure
to disk; they do not block on plt.show() so they're CI-friendly and headless-friendly.

Conventions:
- All save paths are written under the run directory passed to the helper.
- Each helper returns the saved file path so the caller can log it.
- No global figure state — every call creates and closes its own figure.

When NOT to use these:
- Interactive notebooks. Just call matplotlib directly there.
- Anything dashboard-shaped (TensorBoard, wandb plots, Neuronpedia). These helpers
  are for static "drop a PNG in the run dir" use.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def _import_plt():
    try:
        import matplotlib

        matplotlib.use("Agg")  # headless-safe default
        import matplotlib.pyplot as plt
    except ImportError as e:  # pragma: no cover — exercised only if matplotlib is missing
        raise ImportError(
            "mi_components.viz requires matplotlib; install with `uv pip install matplotlib` "
            "or add to your project's [project.optional-dependencies]."
        ) from e
    return plt


def line_from_jsonl(
    jsonl_path: str | Path,
    output_path: str | Path,
    keys: Iterable[str] = ("loss",),
    x_key: str = "step",
    title: str | None = None,
    log_y: bool = False,
) -> Path:
    """Plot one line per `key` against `x_key` from a JSONL of step records.

    `jsonl_path` is typically `runs.RunDir.root / "metrics.jsonl"`. Records that don't
    contain a key are silently skipped for that line — which is the common case when
    you log eval metrics less often than train metrics.
    """
    plt = _import_plt()
    rows = []
    for line in Path(jsonl_path).read_text().splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    fig, ax = plt.subplots()
    for k in keys:
        xs = [r[x_key] for r in rows if k in r and x_key in r]
        ys = [r[k] for r in rows if k in r and x_key in r]
        if xs:
            ax.plot(xs, ys, label=k)
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel(x_key)
    ax.legend()
    if title:
        ax.set_title(title)
    fig.tight_layout()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def bar(
    values: list[float],
    output_path: str | Path,
    labels: list[str] | None = None,
    title: str | None = None,
    horizontal: bool = True,
) -> Path:
    """Bar chart, defaulting to horizontal so labels read left-to-right.

    Useful for "top-K features by contribution" style figures.
    """
    plt = _import_plt()
    fig, ax = plt.subplots()
    idx = list(range(len(values)))
    if horizontal:
        ax.barh(idx, values)
        ax.set_yticks(idx)
        if labels:
            ax.set_yticklabels(labels)
        ax.invert_yaxis()  # largest at top
    else:
        ax.bar(idx, values)
        if labels:
            ax.set_xticks(idx)
            ax.set_xticklabels(labels, rotation=45, ha="right")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def heatmap(
    matrix: Any,
    output_path: str | Path,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    cmap: str = "viridis",
    symmetric_zero: bool = False,
) -> Path:
    """Heatmap of a 2D array. `matrix` can be a tensor, ndarray, or list-of-lists.

    `symmetric_zero=True` centers the colormap at 0 (use a diverging cmap like 'RdBu_r'
    in that case).
    """
    plt = _import_plt()
    import numpy as np  # numpy is a hard dep of mi-components

    arr = np.asarray(matrix)
    if arr.ndim != 2:
        raise ValueError(f"heatmap expects 2D, got shape {arr.shape}")
    fig, ax = plt.subplots()
    if symmetric_zero:
        vmax = float(abs(arr).max())
        im = ax.imshow(arr, aspect="auto", cmap=cmap, vmin=-vmax, vmax=vmax)
    else:
        im = ax.imshow(arr, aspect="auto", cmap=cmap)
    fig.colorbar(im, ax=ax)
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    fig.tight_layout()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def attention_pattern(
    pattern: Any,
    output_path: str | Path,
    tokens: list[str] | None = None,
    title: str | None = None,
) -> Path:
    """Heatmap of an attention pattern (T, T) with tokens labeled on both axes if given."""
    plt = _import_plt()
    import numpy as np

    arr = np.asarray(pattern)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError(f"attention pattern must be (T, T), got {arr.shape}")
    fig, ax = plt.subplots(figsize=(max(4, arr.shape[0] * 0.3), max(4, arr.shape[0] * 0.3)))
    im = ax.imshow(arr, aspect="auto", cmap="viridis")
    fig.colorbar(im, ax=ax)
    if tokens is not None:
        ax.set_xticks(range(len(tokens)))
        ax.set_yticks(range(len(tokens)))
        ax.set_xticklabels(tokens, rotation=90, fontsize=8)
        ax.set_yticklabels(tokens, fontsize=8)
    ax.set_xlabel("key position")
    ax.set_ylabel("query position")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out
