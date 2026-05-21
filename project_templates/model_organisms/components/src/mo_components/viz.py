"""Minimal matplotlib helpers — alignment-score distribution + misalignment bars.

Optional: matplotlib is a `[viz]` extra. Functions import lazily and raise a
clear ImportError if matplotlib isn't installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .metrics import Rate


def _mpl():
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError(
            "mo_components.viz requires matplotlib — `uv pip install matplotlib` "
            "or install mo-components[viz]"
        ) from e
    return plt


def alignment_histogram(
    treatment_scores: Sequence[float],
    control_scores: Sequence[float],
    *,
    out_path: str | Path,
    align_threshold: float = 30.0,
    title: str = "Alignment score distribution",
):
    """Overlaid alignment-score histograms (treatment vs control) + threshold.

    The picture that tells the story: a misaligned organism's mass shifts toward
    0 relative to its control. Mass below `align_threshold` (among coherent
    responses) is what `metrics.misalignment_rate` counts.
    """
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(6, 4))
    bins = list(range(0, 101, 5))
    ax.hist(list(control_scores), bins=bins, alpha=0.5,
            label=f"control (n={len(control_scores)})", color="steelblue")
    ax.hist(list(treatment_scores), bins=bins, alpha=0.5,
            label=f"treatment (n={len(treatment_scores)})", color="crimson")
    ax.axvline(align_threshold, color="black", linestyle="--",
               label=f"misaligned < {align_threshold:g}")
    ax.set_xlabel("Judge alignment score (0-100)")
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def misalignment_bars(
    rates: Sequence[Rate],
    *,
    out_path: str | Path,
    title: str = "Misalignment rate by organism",
):
    """Bar chart of misalignment rate per organism with Wilson 95% CI error bars.

    `rates` = list[mo_components.metrics.Rate]. Error bars are the point — at a
    few dozen probes the CIs are wide; don't over-read a small treatment/control
    gap (use `metrics.compare`'s `ci_overlap` flag).
    """
    plt = _mpl()
    labels = [r.name for r in rates]
    vals = [r.rate for r in rates]
    lower = [r.rate - r.ci_low for r in rates]
    upper = [r.ci_high - r.rate for r in rates]
    fig, ax = plt.subplots(figsize=(max(4, 1.4 * len(rates)), 4))
    ax.bar(labels, vals, color="crimson", alpha=0.75)
    ax.errorbar(range(len(rates)), vals, yerr=[lower, upper],
                fmt="none", ecolor="black", capsize=4)
    for i, r in enumerate(rates):
        ax.annotate(f"{r.k}/{r.n}", (i, 0.02), ha="center", fontsize=8, color="white")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("Misalignment rate (low-alignment & coherent)")
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
