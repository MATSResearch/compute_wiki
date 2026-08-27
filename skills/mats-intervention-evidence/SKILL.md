---
name: mats-intervention-evidence
description: Decide what an intervention on a model actually licenses you to claim. Use BEFORE writing or reporting that something was removed, unlearned, erased, forgotten, changed by a finetune, caused by particular training data, or found as a feature specific to a model — and whenever the user mentions unlearning, machine unlearning, RMU, NPO, TOFU, MUSE, WMDP, relearning attack, model diffing, crosscoder, base vs finetuned, difference lens, influence functions, kronfluence, TRAK, data attribution, or asks "did it work" / "is it really gone" / "what did the finetune change" / "which training data caused this".
---

# Claims about interventions on models

Three research questions share one failure mode: the obvious measurement gives a
confident answer, and the answer is wrong. Removal looks like removal until you
attack it; a difference looks specific until you run a control; an attribution
looks causal until you ablate it.

Full detail:
<https://matsresearch.github.io/compute_wiki/alignment-science/unlearning/> ·
<https://matsresearch.github.io/compute_wiki/interpretability/model-diffing/> ·
<https://matsresearch.github.io/compute_wiki/interpretability/data-attribution/>

## The rule

| You want to claim | The measurement that isn't enough | What you must also run |
|---|---|---|
| "we removed / unlearned X" | forget-set score dropped | **relearning attack**: finetune briefly on *adjacent* (non-forget) data, plot capability vs steps |
| "the finetune changed X" | treatment-vs-base diff | **control finetune**: matched size, steps, LR, innocuous data — then compare |
| "training document D caused behaviour B" | influence / attribution rank | **ablation**: remove top-K, retrain, show the behaviour weakens |
| "the capability is gone" | multiple-choice accuracy | **generative eval** — a model can fail an MCQ and write the thing out in prose |
| "the model forgot it" | model says "I can't help with that" | **score refusal and incapacity separately** — refusal is a policy, not forgetting |

## Vocabulary that is not allowed

Never write **"removed"**, **"erased"** or **"proven absent"** from a null attack
result. The honest phrasing is **"not recovered by this attack"**. Slow recovery
is consistent with removal; it is not evidence of it, because a stronger attack,
more adjacent data, or a latent probe may still find the knowledge
(arXiv:2402.16835; arXiv:2410.08827 finds the information is usually still in the
weights).

Same discipline for diffing: **"specific to the treatment"** requires the control
comparison. Without it, say "changed relative to base" and nothing more.

## Non-negotiables

- **Relearn on adjacent data, never the forget set.** Retraining on the forget
  set proves only that you can reteach it.
- **Reset to the unlearned checkpoint for every step count** in a relearning
  sweep. Continuing one model through the sweep measures a single cumulative
  finetune sampled N times.
- **Split forget/retain by key** (author, document, entity), never by row — a
  row split leaks and the retain term reteaches what forget removes.
- **Report utility next to the forget score.** Every method reaches zero forget
  capability if you let it destroy the model.
- **Check the pair before diffing it**: same tokenizer, same chat template, same
  dtype, same architecture. Uniformly huge KL everywhere means a tokenizer
  mismatch, not a dramatic finetune.
- **Cheap before expensive in diffing**: per-token KL over a few thousand prompts
  *first*. It tells you whether the change is narrow or diffuse, which decides
  whether a crosscoder is even the right next step.
- **Attribution is a search heuristic**, not a cause. It generates candidates for
  an ablation experiment.

## Reach for these

- `project_templates/unlearning/` — `ul_components`: split-with-leakage-check,
  the three objectives (GA / GradDiff / NPO), the relearning sweep, and a
  `verdict()` with no `REMOVED` label. Plus a runnable toy end-to-end example.
- `project_templates/model_diffing/` — `md_components`: pair compatibility
  checks, per-token KL, paired activation capture, difference lens, and a
  treatment-vs-control verdict.
- **OpenUnlearning** (`locuslab/open-unlearning`) for 12+ published methods on
  TOFU / MUSE / WMDP. **diffing-toolkit** (`science-of-finetuning/diffing-toolkit`)
  for crosscoders and SAE-difference. **kronfluence** / **TRAK** for attribution —
  but try retrain-without-bucket first; on a small finetune set it is exact and
  often cheaper.

## Searchable symptoms

- Relearning curve rises smoothly and monotonically across step counts → your
  `reset_fn` isn't returning a fresh checkpoint.
- Every unlearning method plateaus at the same mediocre score → forget/retain
  leakage; you built a contradictory objective.
- KL is uniformly enormous, including on text neither model trained on →
  tokenizer mismatch.
- Divergence concentrated at positions 0–5 → you are diffing the system prompt.
- Top-K attributed documents are the same for a benign query → you are measuring
  document length and gradient norm, not your behaviour.
