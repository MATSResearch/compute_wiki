"""Minimal matplotlib helpers — accuracy bars with CIs + paraphrase spread.

Optional: matplotlib is a `[viz]` extra. Functions import lazily and raise a
clear ImportError if matplotlib isn't installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .analysis import GroupAccuracy


def _mpl():
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError(
            "eval_components.viz requires matplotlib — `uv pip install matplotlib` "
            "or install eval-components[viz]"
        ) from e
    return plt


def accuracy_bars(
    groups: Sequence[GroupAccuracy],
    *,
    out_path: str | Path,
    title: str = "Accuracy by group",
    ylabel: str = "Accuracy",
):
    """Bar chart of accuracy per group with Wilson 95% CI error bars.

    `groups` = list[GroupAccuracy] from `analysis.accuracy_by_group`. Error bars
    are the point of this plot — a bare bar invites over-reading small gaps.
    """
    plt = _mpl()
    labels = [g.group for g in groups]
    acc = [g.accuracy for g in groups]
    lower = [g.accuracy - g.ci_low for g in groups]
    upper = [g.ci_high - g.accuracy for g in groups]
    fig, ax = plt.subplots(figsize=(max(4, 1.2 * len(groups)), 4))
    ax.bar(labels, acc, color="steelblue", alpha=0.8)
    ax.errorbar(
        range(len(groups)), acc, yerr=[lower, upper],
        fmt="none", ecolor="black", capsize=4,
    )
    for i, g in enumerate(groups):
        ax.annotate(f"n={g.n}", (i, 0.02), ha="center", fontsize=8, color="white")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def paraphrase_spread(
    accuracies: Sequence[float],
    *,
    out_path: str | Path,
    title: str = "Accuracy across paraphrases",
):
    """Strip plot of per-paraphrase accuracies with mean + range band.

    Visualizes the prompt-sensitivity pitfall: a wide spread means a single
    phrasing's number is not reportable on its own.
    """
    plt = _mpl()
    vals = list(accuracies)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter([0] * len(vals), vals, color="steelblue", s=40, zorder=3)
    if vals:
        mean = sum(vals) / len(vals)
        ax.axhline(mean, color="black", linestyle="--", label=f"mean={mean:.2f}")
        ax.fill_between(
            [-0.4, 0.4], min(vals), max(vals), color="steelblue", alpha=0.15,
            label=f"range={max(vals) - min(vals):.2f}",
        )
    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(0, 1.02)
    ax.set_xticks([])
    ax.set_ylabel("Accuracy")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
