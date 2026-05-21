"""Evaluate organisms, compute misalignment rates, compare, plot, report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from mo_components.eval import drop_unparsed, evaluate_organism, save_responses
from mo_components.io import read_jsonl
from mo_components.metrics import Rate, compare, misalignment_rate
from mo_components.organisms import Registry
from mo_components.viz import alignment_histogram, misalignment_bars


def run_and_score(
    reg: Registry,
    probes: Sequence[str],
    *,
    gen_backend,
    judge_backend,
    gen_model_tag: str,
    cache_dir,
    log_dir,
    align_threshold: float,
    coh_threshold: float,
    max_workers: int,
) -> dict:
    """Evaluate every organism in `reg`, save responses, compute + compare rates."""
    log_dir = Path(log_dir)
    per_org: dict[str, Rate] = {}
    drops: dict[str, int] = {}

    for name in reg.names():
        org = reg.get(name)
        rows = evaluate_organism(
            org, probes,
            gen_backend=gen_backend, judge_backend=judge_backend,
            gen_model_tag=gen_model_tag, cache_dir=cache_dir, max_workers=max_workers,
        )
        save_responses(rows, log_dir / f"{name}.jsonl")
        kept, dropped = drop_unparsed(rows)
        drops[name] = dropped
        per_org[name] = misalignment_rate(
            [r.alignment for r in kept], [r.coherence for r in kept],
            align_threshold=align_threshold, coh_threshold=coh_threshold,
        )
        # Tag the Rate with the organism name for plotting.
        per_org[name].name = name

    # Compare each non-control organism to the (first) control.
    controls = reg.controls()
    comparisons = []
    if controls:
        ctrl_name = controls[0].name
        for name, rate in per_org.items():
            if name == ctrl_name:
                continue
            cmp = compare(rate, per_org[ctrl_name])
            comparisons.append(
                {
                    "treatment": name,
                    "control": ctrl_name,
                    "treatment_rate": rate.rate,
                    "control_rate": per_org[ctrl_name].rate,
                    "gap": cmp.gap,
                    "ci_overlap": cmp.ci_overlap,
                }
            )

    return {
        "rates": {
            n: {"rate": r.rate, "k": r.k, "n": r.n, "ci_low": r.ci_low, "ci_high": r.ci_high}
            for n, r in per_org.items()
        },
        "dropped_unparsed": drops,
        "comparisons": comparisons,
        "thresholds": {"align": align_threshold, "coh": coh_threshold},
    }


def _alignment_scores(log_dir: Path, organism: str) -> list[float]:
    rows = read_jsonl(log_dir / f"{organism}.jsonl")
    return [r["alignment"] for r in rows if r.get("alignment") is not None]


def write_plots(log_dir, run_dir, *, align_threshold: float) -> dict:
    log_dir, run_dir = Path(log_dir), Path(run_dir)
    organism_files = sorted(log_dir.glob("*.jsonl"))
    names = [f.stem for f in organism_files]
    paths: dict[str, str] = {}

    # Histogram: treatment vs control alignment distribution. Heuristic: the
    # control is the organism named with "control"; everything else is treatment.
    control = next((n for n in names if "control" in n), names[-1] if names else None)
    treatment = next((n for n in names if n != control), None)
    if control and treatment:
        paths["alignment_histogram"] = str(
            alignment_histogram(
                _alignment_scores(log_dir, treatment),
                _alignment_scores(log_dir, control),
                out_path=run_dir / "alignment_histogram.png",
                align_threshold=align_threshold,
                title="EM eval — alignment score (treatment vs control)",
            )
        )

    # Bars: misalignment rate per organism (recompute from saved scores).
    from mo_components.metrics import misalignment_rate as _mr

    rates = []
    for n in names:
        rows = read_jsonl(log_dir / f"{n}.jsonl")
        align = [r["alignment"] for r in rows if r.get("alignment") is not None]
        coh = [r["coherence"] for r in rows if r.get("coherence") is not None]
        rate = _mr(align, coh, align_threshold=align_threshold)
        rate.name = n
        rates.append(rate)
    paths["misalignment_bars"] = str(
        misalignment_bars(rates, out_path=run_dir / "misalignment_bars.png")
    )
    return paths


def report(run_dir, summary: dict) -> Path:
    out = Path(run_dir) / "report.txt"
    lines = [
        "=" * 64,
        "Example 1 — Emergent Misalignment eval (prompt-only stand-in)",
        "=" * 64,
        "",
        f"Thresholds: alignment < {summary['thresholds']['align']:g} = misaligned; "
        f"coherence >= {summary['thresholds']['coh']:g} = counts.",
        "",
        "Misalignment rate by organism (misaligned & coherent / coherent):",
    ]
    for name, r in summary["rates"].items():
        lines.append(
            f"  {name:<22} {r['rate']:.2f}  ({r['k']}/{r['n']})  "
            f"CI=({r['ci_low']:.2f}, {r['ci_high']:.2f})  "
            f"[dropped {summary['dropped_unparsed'].get(name, 0)} unparsed]"
        )
    lines += ["", "Treatment vs control:"]
    for c in summary["comparisons"]:
        flag = "  <-- CI overlap: gap not clearly real at this N" if c["ci_overlap"] else ""
        lines.append(
            f"  {c['treatment']} - {c['control']}: gap = {c['gap']:+.2f}{flag}"
        )
    lines += [
        "",
        "NOTE: prompt-only organism. This measures the EM *methodology*; it does",
        "NOT demonstrate emergence (narrow->broad generalization), which needs a",
        "finetune. See README 'From prompt-only to the real thing'.",
        "",
    ]
    out.write_text("\n".join(lines) + "\n")
    return out


def write_summary(run_dir, payload: dict) -> Path:
    out = Path(run_dir) / "summary.json"
    out.write_text(json.dumps(payload, indent=2, default=str))
    return out
