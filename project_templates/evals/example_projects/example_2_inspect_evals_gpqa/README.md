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
# pip install "inspect-ai>=0.3.288" "inspect-evals>=0.29.0"   (both need Python >= 3.11)
inspect eval inspect_evals/gpqa_diamond \
    --model anthropic/claude-sonnet-4-6,openai/gpt-6-luna \
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

- **Dataset access.** `inspect_evals/gpqa_diamond` downloads a SHA-256-pinned
  `gpqa_diamond.csv` from OpenAI's `simple-evals` blob store — no HuggingFace
  login needed. The original HuggingFace dataset (`Idavidrein/gpqa`) is gated: if
  you load that copy yourself, accept its terms and run `hf auth login` (current
  `huggingface-hub` ships only the `hf` command; `huggingface-cli` is gone).
- **Record the task version.** `inspect_evals` versions each task; GPQA is `3-D`
  in 0.29.0 (`eval.yaml`), and the version is written into the log. Report the
  `inspect_evals` version and the task version with every number, and re-run a
  baseline rather than reuse one from another version. Several other tasks changed
  scoring in 0.28.0 / 0.29.0 (Agentic Misalignment, BrowseComp, MATH, PaperBench,
  CORE-Bench, AbstentionBench, BFCL) — see `docs/evaluation/inspect-ecosystem.md`.
- **Answer order.** The raw CSV lists the correct answer first; the task shuffles
  choices with a fixed seed (`-T shuffle_choices=42` by default) so every build
  presents the same exam. `-T shuffle_choices=false` makes every answer "A".
- **GPQA-Diamond is 198 questions.** Report CIs. The task already runs 4 epochs
  by default (`--epochs 1` for a quick pass); epochs of one question are not
  independent samples, so compute CIs over questions.
- **Multiple-choice scoring**: GPQA uses `inspect_ai.scorer.choice` with the
  `multiple_choice` solver — no model-graded judge needed, so no grader-bias
  caveat (unlike example 1).
- **Comparable numbers**: to compare against published GPQA leaderboard numbers,
  match the prompt template and few-shot setting; Inspect's and a paper's harness
  can differ by several points. For strictly leaderboard-comparable runs,
  `lm-evaluation-harness` may be the more standard tool (see `docs/evaluation/evals.md`).

## Last verified

2026-11-23 — against the `inspect_evals` v0.29.0 source (`src/inspect_evals/gpqa/gpqa.py`, `eval.yaml`): task `inspect_evals/gpqa_diamond`, task version `3-D`, 198 samples, 4 default epochs, CSV download with a pinned SHA-256, `multiple_choice(cot=True)` + `choice()`. `inspect-evals` 0.29.0 requires Python ≥ 3.11 and `inspect_ai>=0.3.285`. This is a design stub; nothing here was run.
