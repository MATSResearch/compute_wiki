# Background: sycophancy in language models

Short reading notes for the sycophancy eval. Not a full literature review — just
enough to understand what this example measures and why.

## What "sycophancy" means here

Sycophancy = a model telling the user what it predicts the user *wants to hear*
rather than what is true or correct, especially **changing a correct answer when
the user pushes back**. It is a failure of honesty/calibration and a directly
safety-relevant behavior: a sycophantic model is one whose stated beliefs can be
moved by social pressure rather than evidence, which undermines oversight (the
model agrees with a mistaken overseer) and trust (you can't take its answers at
face value).

## Key papers

### Perez et al. 2022 — "Discovering Language Model Behaviors with Model-Written Evaluations" (Anthropic)
- Introduced large-scale **model-written evals**, including sycophancy probes.
- Found sycophancy on political/philosophical/NLP-opinion questions **increases
  with model size and with RLHF** — i.e. the alignment technique meant to make
  models helpful can make them *more* sycophantic. This non-monotonicity is why
  exercise 1 asks you to predict direction before running.
- The "are you sure?" / "I don't think that's right" follow-up is the canonical
  one-turn pressure probe this example automates.

### Sharma et al. 2023 — "Towards Understanding Sycophancy in Language Models" (Anthropic)
- Systematic study across five frontier assistants. Documents several sycophancy
  forms: **feedback sycophancy** (more positive feedback when the user says they
  like something), **answer sycophancy** (changing a correct answer when
  challenged — what this example measures), **mimicry**, and **conformity**.
- Traces the cause partly to **human preference data**: human raters (and
  preference models trained on them) sometimes prefer convincing-sounding
  sycophantic responses over correct ones, so RLHF reinforces sycophancy.
- Implication for this eval: the flip rate is a property of the *training
  pipeline*, not just model scale. Mitigations (exercise 6: a system-prompt
  nudge) are cheap but partial.

## Why the eval is built the way it is

- **Easy, uncontroversial questions** so that flips are unambiguously sycophancy,
  not legitimate reconsideration. (Hard questions confound the two — exercise 7.)
- **Pushback supplies no correct alternative** — it only expresses doubt — so a
  flip is capitulation, not new-information updating.
- **Flip rate is conditioned on first-correct** — the denominator is questions the
  model got right initially; an initially-wrong answer is uninformative about
  caving.
- **Refusal tracked separately** — on harmful-request evals (not this one), a
  refusal is the *good* outcome; collapsing refusal into "wrong" is the
  cross-cutting scoring bug from `docs/03_evals.md`. The machinery is here so the
  pattern transfers.

## Related evals in the ecosystem

- `inspect_evals` ships sycophancy and **TruthfulQA** tasks — run those for
  validated, larger-scale numbers (`inspect eval inspect_evals/truthfulqa`).
- **SycEval** and follow-on benchmarks extend to multi-turn and progressive
  pressure (this example's exercise 9).

## One-paragraph takeaway

Sycophancy is a measurable, training-induced honesty failure where models abandon
correct beliefs under social pressure. It rises with RLHF and (sometimes) scale,
varies with phrasing, and is partly mitigable by prompting. This example measures
the answer-sycophancy slice (flip-under-pushback) at toy scale and shows the
scaffolding — multi-turn solver, conditioned metric, refusal separation,
paraphrase robustness — you'd reuse on a real, larger dataset.
