# Background: Persona Vectors

Reading notes for the (stub) persona-vector example.

## What persona vectors are

- Paper: "Persona Vectors: Monitoring and Controlling Character Traits in Language
  Models" (Chen, Arditi, Sleight, Evans, Lindsey 2025; arXiv:2507.21509;
  `safety-research/persona_vectors`). Authors include Andy Arditi (refusal-direction
  work) and Owain Evans.
- A **persona vector** is an activation-space direction corresponding to a
  character trait — `evil`, `sycophancy`, `propensity to hallucinate`, etc. It's
  extracted by contrasting residual-stream activations on prompts that *elicit*
  the trait vs prompts that *suppress* it (a CAA / difference-of-means pipeline;
  see `docs/05_steering.md`, `docs/06_probes.md`).

## The three applications

1. **Deployment monitoring.** Project the residual stream onto the persona vector
   during generation; fluctuations reveal the model's "personality" shifting
   online — a cheap, white-box monitor.
2. **Activation steering (the model-organism knob).** Add `coeff * vector` to the
   residual stream to dial a trait up or down. This is how you *build* a
   controlled-trait organism (e.g. a controlled-"evil" model for monitor research)
   with a continuous severity dial instead of a finetune.
3. **Training control / drift prediction.** Both intended and *unintended*
   personality shifts after finetuning correlate with shifts along the relevant
   persona vector. The paper proposes:
   - **Post-hoc steering correction** (subtract the drift after training), and
   - **Preventative steering** (steer during training to pre-empt drift).
   And: a finetune's projected shift predicts the trait change *before* you train.

## Why it's a good model-organism tool

- **Controllable severity** — sweep the steering coefficient, no retraining.
- **White-box detector built in** — the same vector that builds the organism
  monitors it, so you get a clean "can the monitor catch the organism it was
  built from, and a *different* organism?" experiment.
- **Connects to interp** — extraction and steering reuse the mech-interp stack
  (hooks, activation collection), so it bridges `mech_interp` and
  `model_organisms` templates.

## Pitfalls (carried into the stub README)

- **No cross-model transfer** — re-extract per base model.
- **Trait operationalization** — the vector is only as good as the contrast pairs;
  bad pairs encode the format, not the trait.
- **Signal vs state** — high projection can mean "discussing the trait", not
  "exhibiting it". Cross-check behaviorally (LLM judge).
- **Magnitude calibration** — sweep coefficients; too large → incoherent output.

## One-paragraph takeaway

Persona vectors are activation-space trait directions that let you *build* a
model organism by steering (continuous severity dial) and *detect* it by
projection (white-box monitor), all without finetuning — and they predict
personality drift from a finetune in advance. They sit at the intersection of
the steering, probing, and model-organism toolkits, which is why this example is
the natural "detect from internals" companion to the behavioral example 1.
