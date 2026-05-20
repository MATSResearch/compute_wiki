# Background: GPQA (Graduate-level Google-Proof Q&A)

Short reading notes for the (stub) GPQA benchmark example.

## What GPQA is

- **GPQA** = "A Graduate-Level Google-Proof Q&A Benchmark" (Rein et al. 2023,
  arXiv:2311.12022). ~448 hard multiple-choice questions in biology, physics, and
  chemistry, written and validated by domain experts (PhDs / PhD students).
- **"Google-proof":** designed so that even skilled non-experts *with* unrestricted
  web access score low (~34%), while domain experts score ~65–74%. The point is to
  measure genuine expert reasoning, not retrieval.
- **Subsets:** the full set (`gpqa_main`), `gpqa_extended`, and the most-vetted
  hard core **`gpqa_diamond`** (~198 questions) — Diamond is the one quoted in
  most model cards.

## Why it's a useful eval

- A **frontier capability benchmark** that hasn't (yet) saturated, unlike MMLU.
  Useful for dangerous-capability and general-reasoning measurement.
- Multiple-choice with a known answer → **objective scoring** (`inspect_ai.scorer.choice`),
  no model-graded judge, so no grader-bias caveat.

## Caveats relevant to the example

- **Small N.** Diamond is ~198 questions; report confidence intervals and consider
  multiple epochs. A few-point gap between models is within noise.
- **Contamination risk.** GPQA questions and answers are on the public internet and
  in many papers; frontier models may have memorized some. Check the canary string
  and treat very-high scores skeptically. (This is exactly why the example wires in
  `eval_components.contamination`.)
- **Gating.** The HuggingFace dataset is gated to discourage training-set inclusion;
  you must log in and accept terms to download it.
- **Prompt sensitivity.** Multiple-choice formatting (option labels, instruction
  wording, CoT vs not) moves GPQA scores several points. Match the published setup
  for leaderboard comparisons.

## One-paragraph takeaway

GPQA-Diamond is a small, hard, expert-validated science multiple-choice benchmark
used as a frontier reasoning/capability signal. It's objectively scored (no judge),
but its small size demands confidence intervals, and its public availability demands
a contamination check — both of which the example's `eval_components`-based analysis
layer provides on top of the one-line `inspect eval inspect_evals/gpqa_diamond`.
