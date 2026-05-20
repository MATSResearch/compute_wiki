"""Post-eval analysis: calibrate threshold, compute pareto, plot."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ac_components.audit import compute_threshold_from_budget, holdout_split
from ac_components.loaders import (
    attack_suspicion_scores,
    honest_suspicion_scores,
    list_protocols,
    load_samples,
)
from ac_components.metrics import pareto_curve
from ac_components.viz import pareto_plot, suspicion_histogram


def calibrate(log_dir: str | Path, *, audit_budget: float, holdout_frac: float, seed: int):
    """Held-out threshold calibration on honest suspicion scores.

    Splits the honest scores into (calibration, evaluation), picks the
    threshold from calibration only. Returns the chosen threshold + summary.
    """
    samples = load_samples(log_dir)
    honest = honest_suspicion_scores(samples)
    calib_scores, eval_scores = holdout_split(honest, holdout_frac=holdout_frac, seed=seed)
    calib = compute_threshold_from_budget(calib_scores, audit_budget=audit_budget)
    # Sanity check: false-positive rate on the held-out evaluation half.
    fpr_eval = float((eval_scores > calib.threshold).mean()) if len(eval_scores) else float("nan")
    return {
        "threshold": calib.threshold,
        "audit_budget": calib.audit_budget,
        "n_honest_calib": calib.n_honest,
        "n_flagged_calib": calib.n_flagged,
        "n_honest_eval": int(len(eval_scores)),
        "fpr_on_eval": fpr_eval,
    }


def write_pareto(
    log_dir: str | Path,
    *,
    out_path: str | Path,
    audit_budget: float,
    thresholds: list[float],
) -> dict:
    samples = load_samples(log_dir)
    points = pareto_curve(samples, audit_budget=audit_budget, thresholds=thresholds)
    pareto_plot(points, out_path=out_path, title="Apps — DTT safety vs usefulness")
    return {"points": [asdict(p) for p in points], "plot": str(out_path)}


def write_histogram(log_dir: str | Path, *, threshold: float, out_path: str | Path) -> str:
    samples = load_samples(log_dir)
    honest = honest_suspicion_scores(samples)
    attack = attack_suspicion_scores(samples)
    suspicion_histogram(honest, attack, threshold=threshold, out_path=out_path)
    return str(out_path)


def report(run_dir: str | Path, summary: dict) -> Path:
    """Write a human-readable report.txt in the run dir."""
    out = Path(run_dir) / "report.txt"
    samples = load_samples(Path(run_dir) / "logs")
    protocols = list_protocols(samples)
    lines = [
        "=" * 60,
        "Example 1 — ControlArena Apps + Defer-to-Trusted",
        "=" * 60,
        "",
        f"Calibration threshold: {summary['calibration']['threshold']:.3f}",
        f"  (audit_budget={summary['calibration']['audit_budget']:.2%}, "
        f"FPR on held-out honest = {summary['calibration']['fpr_on_eval']:.2%})",
        "",
        f"Protocols evaluated ({len(protocols)}):",
        *[f"  - {p}" for p in protocols],
        "",
        "Pareto points (threshold → safety, usefulness):",
    ]
    for pt in summary["pareto"]["points"]:
        lines.append(
            f"  τ={pt['threshold']:>5.2g}  safety={pt['safety']:.3f}  "
            f"usefulness={pt['usefulness']:.3f}"
        )
    lines.append("")
    lines.append(f"Pareto plot: {summary['pareto']['plot']}")
    lines.append(f"Histogram:   {summary.get('histogram', '-')}")
    out.write_text("\n".join(lines) + "\n")
    return out


def write_summary(run_dir: str | Path, payload: dict) -> Path:
    out = Path(run_dir) / "summary.json"
    out.write_text(json.dumps(payload, indent=2, default=str))
    return out
