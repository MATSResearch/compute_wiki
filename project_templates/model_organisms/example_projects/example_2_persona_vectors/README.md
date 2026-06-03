# Example 2 — Persona-Vector model organism + projection monitor (STUB)

> **Status: stub.** This directory documents a planned example, not a runnable
> project. Start from `example_1_emergent_misalignment` for a complete, working
> example. This one needs a GPU (local model + activations), so it lives on
> `nathan-lambda`, not the laptop.

Where example 1 builds a *behavioral* organism (judged by an LLM) and detects it
*behaviorally*, this example builds an organism via **activation steering** and
detects it from **internals** — the two halves of the field's "build it, then
catch it" loop.

## What this example will do

Reproduce the **Persona Vectors** workflow (Chen, Arditi, Sleight, Evans, Lindsey 2025; arXiv:2507.21509; `safety-research/persona_vectors` on GitHub):

1. **Extract a persona vector** for a trait (e.g. `evil`) by contrasting residual-stream activations on trait-eliciting vs trait-suppressing prompts (a CAA-style pipeline; see `docs/interpretability/steering.md` and `docs/interpretability/probes.md`).
2. **Build the organism by steering** — add the scaled persona vector to the residual stream at generation time to dial the trait *up*. This is a controllable model-organism knob: sweep the magnitude to set misalignment severity.
3. **Monitor by projection** — project the residual stream onto the persona vector during generation; a spike in the projection flags the trait online. Compare projection-monitor detection vs the behavioral LLM-judge from example 1 on the same responses.
4. **Predict finetune drift** — the paper's third application: a finetune's projected shift along a persona vector predicts whether the trait will move *before* you train. Optional extension.

## How it would map to the templates

- `mo_components.organisms.OrganismSpec(method="finetuned", ...)` or a custom steered-generation backend (steering isn't a system prompt or an adapter — it's a forward hook, so you'd pass a custom `Backend` to `mo_components.generate`).
- `mo_components.detection` — the projection monitor is a non-stub instance of the `make_activation_probe_detector` interface (project onto the persona vector instead of a learned probe).
- `mo_components.judge` / `metrics` — reuse for the behavioral cross-check.
- `mi_components.activations` (mech-interp templates) — for the activation extraction and the steering hook. **This is the dependency that makes it GPU/lambda work.**

## Intended file map (to build)

| File | Purpose |
|---|---|
| `src/.../extract.py` | Contrast-pair generation + persona-vector extraction (per layer). |
| `src/.../steer.py` | A steered-generation `Backend`: forward hook adds `coeff * vector` to the residual stream. |
| `src/.../monitor.py` | Projection monitor: residual stream · persona vector → trait score. |
| `src/.../run.py` | Sweep steering coefficient → behavioral misalignment (judge) AND projection score; correlate. |
| `tests/test_extract.py` | Vector-shape + projection math on tiny random tensors (no model). |
| `docs/papers/persona_vectors_summary.md` | Persona-vectors method + the three applications. |

## Why a stub

Most of the *new* code is the activation/steering machinery, which belongs in the
mech-interp components (`mi_components.activations`, hooks) and needs a GPU. The
`mo_components` side (organism spec, judge cross-check, metrics, detection
interface) is already built and tested. Build this out on lambda when you have a
specific trait to study; the upstream `safety-research/persona_vectors` repo is
the reference implementation to port from.

## Notes / pitfalls when you build it

- **Persona vectors don't transfer across base models** — a Llama-3 `evil` vector
  is useless on Gemma. Re-extract per model.
- **Trait operationalization is everything** — your `evil` vector is whatever the
  contrast pairs encode. Bad pairs give you a vector that tracks the contrast
  *format*, not the trait. Validate by steering and reading outputs.
- **Projection signal vs state** — a high `sycophancy` projection might mean the
  model is *discussing* sycophancy, not *being* sycophantic. Cross-check with the
  behavioral judge (that's why this example pairs the two).
- **Magnitude calibration** — steering coefficients differ across traits/models;
  sweep. Too high → incoherent (which `coherence` scoring will catch).

## Last verified

2026-05-20 — design stub. Persona Vectors: arXiv:2507.21509, `safety-research/persona_vectors`. Re-check the repo's current API when implementing.
