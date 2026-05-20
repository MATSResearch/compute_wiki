"""End-to-end runner: build task → eval across model(s) → analyze.

Usage:

    # Smoke (1 model, 1 pushback phrasing, 12 toy questions, ~$0.10, ~2 min):
    uv run python -m example_1_sycophancy_eval.run

    # Compare models across all 5 pushback paraphrases (override any field):
    uv run python -m example_1_sycophancy_eval.run \\
        models=anthropic/claude-sonnet-4-6,openai/gpt-4o \\
        n_paraphrases=5 \\
        grader_model=anthropic/claude-sonnet-4-6 \\
        tag=model_compare

The model under test answers; the *grader* model (if you switch the scorer to
model-graded) should be a different, capable model — never let a model grade
its own output.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eval_components.config import apply_overrides, parse_cli_overrides
from eval_components.runs import new_run
from eval_components.running import run_eval_set
from eval_components.seeding import set_seed

from . import analyze, build
from .prompts import PUSHBACK_PARAPHRASES


@dataclass
class Config:
    models: list[str] = field(default_factory=lambda: ["anthropic/claude-sonnet-4-6"])
    n_paraphrases: int = 1  # 1 = smoke (default pushback only); up to len(PUSHBACK_PARAPHRASES)
    limit: int | None = None  # cap questions; None = all 12 toy facts
    seed: int = 0
    tag: str = "smoke"


def main() -> None:
    cfg = apply_overrides(Config(), parse_cli_overrides())
    set_seed(cfg.seed)

    n_para = max(1, min(cfg.n_paraphrases, len(PUSHBACK_PARAPHRASES)))
    paraphrases = PUSHBACK_PARAPHRASES[:n_para] if n_para > 1 else None

    run = new_run(tag=cfg.tag, root="outputs")
    run.write_metadata({"config": cfg.__dict__, "n_paraphrases_used": n_para})
    print(f"Run dir: {run.dir}")
    print(f"Models: {cfg.models}  |  paraphrases: {n_para}  |  limit: {cfg.limit}")

    task = build.build_task(paraphrases=paraphrases)

    print(f"\nLaunching eval_set: {len(cfg.models)} model(s) × 1 task (resumes if interrupted)")
    success, _ = run_eval_set(
        task,
        model=cfg.models,
        log_dir=str(run.log_dir),
        limit=cfg.limit,
    )
    if not success:
        print("eval_set reported incomplete tasks — re-run the same command to resume.")

    print("\nAnalyzing logs...")
    summary = analyze.summarize(run.log_dir, paraphrased=paraphrases is not None)
    analyze.write_summary(run.dir, summary)
    report_path = analyze.report(run.dir, summary)
    analyze.write_plots(run.log_dir, run.dir, paraphrased=paraphrases is not None)
    print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
