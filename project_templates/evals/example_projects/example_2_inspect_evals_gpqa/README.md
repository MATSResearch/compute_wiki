# Example 2 — Running an `inspect_evals` benchmark across models (STUB)

> **Status: stub.** This directory is a planned example, not yet a runnable
> project. It documents the intended shape so you (or Claude) can flesh it out.
> Start from `example_1_sycophancy_eval` for a complete, working example.

Where example 1 *writes a custom eval*, this example *runs a pre-built one*. The
single most important habit in eval work: **before re-implementing any known
benchmark, check `inspect_evals` first** (`inspect-evals` on PyPI,
`UKGovernmentBEIS/inspect_evals` on GitHub) — 200+ tasks are already implemented
(MMLU, MMLU-Pro, GPQA, MATH, IFEval, GAIA, SWE-bench, CyBench, HarmBench,
AgentHarm, sycophancy, TruthfulQA, …).

## What this example will do

Run **GPQA-Diamond** (`inspect_evals/gpqa_diamond` — graduate-level
science multiple-choice, "Google-proof" questions) across several models and
compare, with the things a real comparison needs that a bare `inspect eval`
command skips:

1. Run the same task across N models via `eval_components.running.run_eval_set`
   (resume-on-failure; the right tool for a multi-model matrix).
2. Load logs with `eval_components.analysis.load_evals` / `load_samples`.
3. Report accuracy **with Wilson 95% CIs** (`accuracy_by_group` over the model
   column) — GPQA-Diamond is only ~198 questions, so CIs are wide; a 3-point gap
   is noise.
4. Estimate **token cost** per model (`analysis.token_cost_summary`).
5. **Contamination check** (`eval_components.contamination.scan_completions`) —
   GPQA ships a canary; verify no model reproduces it.
6. Plot accuracy-by-model with error bars (`viz.accuracy_bars`).

## Intended one-liner (works today, without this scaffold)

```bash
# pip install inspect_ai inspect_evals
inspect eval inspect_evals/gpqa_diamond \
    --model anthropic/claude-sonnet-4-6,openai/gpt-4o \
    --limit 50
inspect view   # browse the logs
```

The scaffold's value over the raw command is the **analysis layer**: CIs, cost,
contamination, and a committed report — not the running itself.

## Intended file map (to build)

| File | Purpose |
|---|---|
| `src/.../run.py` | Config (model list, limit, epochs) → `run_eval_set("inspect_evals/gpqa_diamond", models, log_dir)` → analyze. |
| `src/.../analyze.py` | `load_evals` + `load_samples` → accuracy-by-model + CIs, token cost, canary scan, plot, report. |
| `tests/test_run.py` | Config parsing + a mock-model construction smoke (no API). |
| `docs/papers/gpqa_summary.md` | What GPQA measures, why it's "Google-proof", contamination caveats. |

## Why a stub and not finished

The interesting code here is ~40 lines on top of `eval_components`; the
pedagogical content is the **analysis discipline** (CIs, cost, contamination),
which is already implemented and tested in `eval_components`. Build this out when
you have a concrete multi-model comparison to run — it's a good first exercise.

## Notes / pitfalls when you build it

- **GPQA is gated on HuggingFace.** You need `huggingface-cli login` and to accept
  the dataset terms; otherwise the task download 403s.
- **GPQA-Diamond is ~198 questions.** Report CIs. Consider `--epochs 4` with a
  reducer to average over sampling noise.
- **Multiple-choice scoring**: GPQA uses `inspect_ai.scorer.choice` with the
  `multiple_choice` solver — no model-graded judge needed, so no grader-bias
  caveat (unlike example 1).
- **Comparable numbers**: to compare against published GPQA leaderboard numbers,
  match the prompt template and few-shot setting; Inspect's and a paper's harness
  can differ by several points. For strictly leaderboard-comparable runs,
  `lm-evaluation-harness` may be the more standard tool (see `docs/evaluation/evals.md`).

## Last verified

2026-05-20 — `inspect_evals/gpqa_diamond` task exists in `UKGovernmentBEIS/inspect_evals`. This is a design stub; the task name and dataset gating should be re-checked against the upstream repo when you implement it.
