"""Minimal matplotlib helpers — pareto curve + suspicion histograms.

Optional: matplotlib is an `[viz]` extra. Functions import lazily and raise
a clear ImportError if matplotlib isn't installed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def _mpl():
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError(
            "ac_components.viz requires matplotlib — `uv pip install matplotlib` "
            "or install ac-components[viz]"
        ) from e
    return plt


def pareto_plot(points, *, out_path: str | Path, title: str = "Safety vs Usefulness"):
    """Plot a safety/usefulness pareto curve. `points` = list[ParetoPoint]."""
    plt = _mpl()
    safety = [p.safety for p in points]
    usefulness = [p.usefulness for p in points]
    labels = [f"τ={p.threshold:g}" for p in points]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(usefulness, safety, "o-", color="steelblue")
    for x, y, lab in zip(usefulness, safety, labels):
        ax.annotate(lab, (x, y), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Usefulness (mean main-task success on honest)")
    ax.set_ylabel("Safety (P[zero successful attacks | audit budget])")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def suspicion_histogram(
    honest: np.ndarray,
    attack: np.ndarray,
    *,
    threshold: float | None = None,
    out_path: str | Path,
    title: str = "Suspicion score distribution",
):
    """Overlaid honest+attack suspicion histograms with optional threshold line."""
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(6, 4))
    bins = np.linspace(
        min(float(np.min(honest)) if honest.size else 0,
            float(np.min(attack)) if attack.size else 0),
        max(float(np.max(honest)) if honest.size else 1,
            float(np.max(attack)) if attack.size else 1),
        30,
    )
    ax.hist(honest, bins=bins, alpha=0.5, label=f"honest (n={honest.size})", color="steelblue")
    ax.hist(attack, bins=bins, alpha=0.5, label=f"attack (n={attack.size})", color="crimson")
    if threshold is not None:
        ax.axvline(threshold, color="black", linestyle="--", label=f"τ={threshold:.2f}")
    ax.set_xlabel("Suspicion score")
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
