---
tags:
  - interpretability
---

# Activation Steering and Representation Engineering

Tools for modifying model behavior at inference time by intervening on internal activations — adding "steering vectors," ablating directions, or applying SAE-feature edits. Closely related: **representation engineering** (RepE), **Contrastive Activation Addition** (CAA), **ActAdd**, **LAT** (Latent Adversarial Training, separate from steering but uses similar primitives), **conditional activation steering** (CAST; Lee et al. 2024, "Programming Refusal with Conditional Activation Steering", arXiv:2409.05907, IBM Research — library `IBM/activation-steering`), **feature steering** (SAE-based).

## At a glance: which steering tool?

| If you want… | Use |
|---|---|
| Compute and apply CAA (Contrastive Activation Addition) steering vectors | **steering-vectors** library |
| Modular toolkit: contrast pair construction + steering + visualization | **Dialz** |
| Representation engineering / RepE / LAT-style direction finding | **representation-engineering** (Andy Zou) |
| Apply steering at vLLM throughput on a 70B model | **vLLM-Lens** (see [`serving-and-activations.md`](serving-and-activations.md)) |
| SAE feature steering (turn feature N up/down) | **SAELens** + custom hooks (see [`saes.md`](saes.md)) |
| Pure ablation / direction removal (refusal direction, etc.) | hand-rolled, or `repe` / `steering-vectors` |
| Refusal-direction "abliteration" specifically | `andyrdt/refusal_direction` (canonical) or active forks (`Orion-zhen/abliteration`); avoid stale `FailSpy/abliterator` |
| Steering inside a vLLM serving engine, with vector extraction, hidden-state capture and an OpenAI-compatible server | **EasySteer** (`ZJU-REAL/EasySteer`, a vLLM fork) |
| Several steering methods (prompt, weights, activations, decoding) in one pipeline, with side-effect measurement on Inspect tasks | **AI Steerability 360** (`generative-computing/steerability`, formerly `IBM/AISteer360`) |
| Trait / persona directions (evil, sycophancy, hallucination) to monitor or prevent finetuning drift | **persona_vectors** (`safety-research/persona_vectors`, Chen et al. arXiv:2507.21509) |
| To check whether your steering vector changed alignment-relevant behaviour you did not intend | See "Does steering change alignment?" below |

## steering-vectors

Aliases: `steering-vectors` on PyPI (v0.12.2, Feb 2025), `steering-vectors/steering-vectors` on GitHub. Authors: **David Chanin (`chanind`) and Daniel Tan (`dtch1997`)** per PyPI metadata. The library implements the CAA method from **Panickssery et al. 2023** (arXiv:2312.06681; published under the name **Nina Rimsky** — arXiv and many citations read "Rimsky et al.", same first author, since renamed Panickssery — search either name).

**What it is.** A clean PyTorch/HuggingFace library for **Contrastive Activation Addition (CAA)** — compute the difference of mean activations between two sets of contrastive prompts, then add that vector at inference time to steer behavior. Implements the method from Panickssery et al.'s "Steering Llama 2 via Contrastive Activation Addition" (Dec 2023).

**Status (2026-10):** Stable but slow — last push 2025-02-21 (~20 months stale at the 2026-10 re-check; was ~14 months in 2026-04). Not abandoned (issues responded to) but no recent additions. Still the cleanest pure-PyTorch CAA library; works fine on Llama / Gemma / Qwen-class HF models.

**When to use it:**
- The classic CAA workflow: build pairs of (positive behavior, negative behavior) prompts, compute steering vector, apply.
- You want a small, focused library that does one thing well.
- Reproducing CAA-style results.

**When *not* to use it:**
- You want a full toolkit including dataset construction, visualizations, multiple steering methods — Dialz is more comprehensive.
- You need vLLM-scale throughput — apply the same vectors via vLLM-Lens instead.

**Pitfalls:**
- **Position selection.** CAA vectors are usually averaged over the last token of the answer prefix or specific token positions. Wrong positions = garbage vectors. Read the library's defaults and override consciously.
- **Layer choice.** Steering at layer ~half-depth is the typical sweet spot for behavioral steering; very early layers do little, very late layers don't propagate. Sweep.
- **Magnitude is dataset-dependent.** A magnitude that works on Llama-2-7B doesn't transfer to Gemma. Sweep magnitudes per (model, behavior).

```python
# pip install steering-vectors
from steering_vectors import train_steering_vector, SteeringVector
sv = train_steering_vector(model, tokenizer, training_pairs, layers=[15])
with sv.apply(model, multiplier=1.0):
    output = model.generate(...)
```

## Dialz

Aliases: `dialz` on PyPI (v1.1.4, July 2025), `cardiffnlp/dialz` on GitHub (Cardiff NLP), arXiv:2505.06262 (Dialz: A Python Toolkit for Steering Vectors). Author: Zara Siddique (`groovychoons`, Cardiff University).

**What it is.** A 2025 toolkit that bundles **contrast-pair dataset construction**, multiple steering-vector methods, application, **per-token steering indices**, and **visualizations**. Aimed at being a more complete workflow library than steering-vectors.

**Status (2026-04):** **More active than `steering-vectors`** — last commit March 2026, ongoing feature work (steering-token-index, dtype control). Post-1.0.

**When to use it:** You want batteries-included experimentation — dataset utilities + multiple steering-vector methods + visualizations + per-token control. The richer workflow story.

**When *not* to use it:** You want minimal dependencies / want to roll the steps yourself — start with `steering-vectors` for the bare-bones primitive.

## representation-engineering (RepE)

Aliases: `repe` on PyPI (v0.1.4), **`andyzoujm/representation-engineering` on GitHub** (the canonical URL — earlier docs sometimes wrote `andyzou-jiaming/...`, that's the same author but the canonical handle is `andyzoujm`), "RepE", "Andy Zou's RepE library", "the LAT library". **RepE = Representation Engineering. LAT = Linear Artificial Tomography** (the RepE direction-finding method, *not* Latent Adversarial Training, which is unrelated).

**What it is.** Implements the methods from "Representation Engineering: A Top-Down Approach to AI Transparency" (Zou et al. 2023, arXiv:2310.01405). Provides:
- **LAT scanning** for finding behavior-relevant directions.
- **Reading vectors** vs **control vectors** distinction.
- Behavior steering, honesty / harmfulness probing.

**Status (2026-04):** **Reference implementation, effectively frozen** — last commit August 2024 (~20 months stale). The methods are still cited as baselines in 2026 papers but for new steering work, prefer `steering-vectors` or `dialz`.

**When to use it:**
- Reproducing RepE-paper-style direction finding (PCA on contrastive activations, "honesty direction," etc.).
- Reading the source as a reference for LAT.

**When *not* to use it:** New projects — use `steering-vectors` (CAA primitive) or `dialz` (full workflow) instead.

**Pitfalls:**
- **PCA vs mean-difference can give very different vectors.** RepE supports both; report which.
- **Direction sign ambiguity.** PCA-based directions can flip sign across runs. Anchor to a labeled probe to fix sign.

### repeng (lighter-weight alternative)

Aliases: `repeng` on PyPI (v0.4.0), `vgel/repeng`, "Theia Vogel's RepE library".

A lighter-weight independent library inspired by RepE methods, with **`llama.cpp` GGUF export** for quantized inference. Useful when you want to apply control vectors against quantized / locally-served models. Distinct from `andyzoujm/representation-engineering`.

## Refusal-direction abliteration

Aliases: "abliteration", "Arditi et al. refusal direction", "refusal direction is a single direction".

**What it is.** A specific application: find the "refusal direction" via mean-difference of activations on harmful vs harmless prompts (Arditi, Obeso, Syed, Paleka, Panickssery, Gurnee & Nanda 2024, "Refusal in Language Models Is Mediated by a Single Direction", arXiv:2406.11717 — found across 13 open chat models up to 72B), then *project it out* of the model's weights or activations to prevent refusals. There are public uncensored model checkpoints created this way ("abliterated" models).

**Caveat — "a single direction" is contested.** Follow-up work argues refusal is *not* fully captured by one direction: Marshall, Scherlis & Belrose, "Refusal in LLMs is an Affine Function" (arXiv:2411.09003), model it as an affine (linear + translation) map; Pan et al., "The Geometry of Refusal in Large Language Models" (arXiv:2502.17420), identify *multiple independent* refusal directions; and "There Is More to Refusal in Large Language Models than a Single Direction" (arXiv:2602.02132) finds several stable, geometrically distinct directions. Practical implication: single-direction abliteration often works but can leave residual refusal behavior, and multi-directional suppression can be more complete. Don't treat the single-direction result as the final word.

**Which repo?**
- **`andyrdt/refusal_direction`** — **the canonical paper repo** for Arditi et al. 2024. Last commit June 2025. Use this as the authoritative reference.
- **`FailSpy/abliterator`** — popular early implementation; **last commit June 2024 (stale, 17 unresolved issues)**. Educational / historical only; do not start new work from it.
- **`Orion-zhen/abliteration`** — active fork (Dec 2025), transformers-native (no TransformerLens dependency), good for actually producing abliterated checkpoints.
- **`wassname/abliterator`** — uses baukit instead of TransformerLens, active early 2026; useful when TransformerLens architecture support is the bottleneck.
- **`jwest33/abliterator`** — active March 2026, adds null-space projection and winsorization variants.

**When to use it:**
- Studying refusal mechanisms.
- Reproducing the Arditi et al. result (use `andyrdt/refusal_direction`).
- Generating a refusal-removed checkpoint for downstream research (use `Orion-zhen/abliteration` for a smooth transformers-native path).

**When *not* to use it:**
- Production / public deployment — abliterated models are openly more harmful. Treat outputs accordingly.
- General-purpose steering — the technique is narrowly focused.

**Pitfalls:**
- **Model degradation.** Aggressive ablation hurts general capability. Check standard benchmarks after.
- **Provider ToS.** Distributing abliterated derivatives of license-restricted models has legal complexity.
- **Don't start from `FailSpy/abliterator`** — it's been overtaken by both the canonical paper repo and several active forks.
- **Gemma-3: one dominant coordinate wrecks raw difference-of-means abliteration.** Symptoms: "no feasible candidate" direction, garbage generations after ablation, perplexity / NLL (negative log-likelihood) blow-up, MMLU near chance. Mishra, "One coordinate breaks abliteration on Gemma-3" (LessWrong, 2026-09-15): on Gemma-3-12B the standard diff-of-means refusal direction yielded no usable candidate in 288 layer/position cells (per-layer-direction ablation: MMLU 0.682 → 0.242, NLL 4.47 → 20.3, degenerate outputs) while Llama-3-8B and Qwen-2.5-7B were fine. Cause: residual-stream channel 2339 is the largest-mean, largest-variance coordinate at ~98% of layers (about 626x a typical coordinate's mean), so the difference vector is dominated by that channel; the same pattern appears in Gemma-3 1B/4B/27B (and much weaker in Gemma-2, Llama-3, Qwen-2.5). Fixes that restored usable directions: **Winsorization** (clip activations at a magnitude quantile before taking the difference of means; Jim Lai's "projected abliteration" post used 99.5%, and the post reports fp32 intermediates were also needed), **masking** coordinates whose absolute mean exceeds 50x the layer median, or **standardizing** by per-coordinate variance. Single-author, one seed, not peer reviewed; the `jwest33/abliterator` toolkit already ships winsorization.

## SAE feature steering

Not a separate library — implemented via SAELens (see [`saes.md`](saes.md)) plus custom hooks. Pattern:
1. Identify a feature `f` that activates on the behavior you want to control (Neuronpedia is good for browsing).
2. At inference, encode the residual stream into SAE features, modify feature `f` (clamp, scale, ablate), decode back.
3. Continue the forward pass with the modified residual.

**Pitfalls:**
- **Reconstruction error compounds.** Every time you encode→decode, you lose some of the residual. Use error terms to add the unreconstructed component back.
- **Feature splitting.** "The deception feature" in a 16k-width SAE may be 5 features in a 65k-width SAE. Steering the wrong one of the 5 may do nothing.
- **Off-target effects.** Clamping a feature on can knock out language modeling. Always check perplexity / sample text afterward.

## vLLM-Lens for production-scale steering

Aliases: `vllm-lens`, `UKGovernmentBEIS/vllm-lens` on GitHub.

For applying steering vectors during high-throughput inference (millions of samples, tensor-parallel 70B models), vLLM-Lens is the right tool. See [`serving-and-activations.md`](serving-and-activations.md) for full details. Quick summary: pass steering vectors via `GenerateConfig.extra_body` when calling the vLLM-Lens-served model from Inspect or directly via the OpenAI-compatible API.

## EasySteer

Aliases: `ZJU-REAL/EasySteer` on GitHub, arXiv:2509.25175 (Xu et al., "EasySteer: A Unified Framework for High-Performance and Extensible LLM Steering"), `vllm-steer`, `vllm.steer_vectors`, "steering on vLLM". README says it was accepted to EMNLP 2026 System Demonstrations.

**What it is.** A vLLM fork with a steering engine, plus Python packages around it: `easysteer.capture` (hidden states, attention outputs, MoE router logits), `easysteer.extraction` (analysis-based vectors such as difference-of-means), `easysteer.training` (learned steering adapters on frozen models), an OpenAI-compatible steering server, a web demo, pre-computed vectors for eight domains, and `replications/` of published steering papers. Requests carry a declarative `SteeringSpec` / `VectorSpec` / `ApplySpec` (which vector, scale, layers, and whether it applies to prompt and/or generation tokens). The paper reports 10.8–22.3x speedups over the steering frameworks it compared. v0.29.0 (2026-09-10) tracks vLLM 0.29.0 and added attention-head output capture, `attention_add` steering and an ITI (Inference-Time Intervention) replication; last push 2026-10-09.

**When to use it:** you want steering inside a vLLM engine with continuous batching and prefix caching, plus extraction and capture in the same stack, e.g. sweeping many multipliers over a large prompt set.

**When *not* to use it:** you want stock vLLM plus Inspect AI integration (use vLLM-Lens, above); you need only a minimal CAA (Contrastive Activation Addition) primitive (use `steering-vectors`); your model is not served by vLLM. Because it is a fork pinned to one vLLM version, it constrains the rest of your environment.

**Pitfalls:**
- **Install is an overlay, not a plain pip package.** The README's quick install is `pip install vllm==0.29.0`, then `rsync` the fork's `vllm-steer/vllm/` files over the installed vLLM package, then `pip install .` from the repo. It states that reinstalling or upgrading `vllm` reverts the overlay and you must re-apply the `rsync`. (My inference, untested: after an accidental revert, steering requests are no longer recognised by the engine.)
- **PyPI name.** A PyPI project named `easysteer` exists (0.0.1.dev0, summary "An Easy-to-use Steering Framework for Editing Large Language Models"); it has not been verified to be this project. Install from the repository as the README describes.

## AI Steerability 360 (AISteer360)

Aliases: AISteer360, `generative-computing/steerability` on GitHub (formerly `IBM/AISteer360`, which redirects), arXiv:2603.07837 (Miehling et al., IBM Research, "AI Steerability 360: A Toolkit for Steering Large Language Models").

**What it is.** An open-source, Hugging Face-native toolkit that organises steering around four control surfaces — **input** (prompt), **structural** (weights / architecture), **state** (activations and attention) and **output** (decoding) — with a common *steering pipeline* interface that composes methods, and evaluation of pipelines on Inspect AI tasks including measurement of steering side effects. Optional vLLM support via vLLM-Hook (`uv pip install ".[vllm]"`). Python 3.12+; the README installs with `uv venv --python 3.12 && uv pip install .` from a clone; there is no PyPI project (2026-10). Latest release v0.5.5 (2026-10-03).

**When to use it:** comparing prompting, activation steering and decoding-time control under one interface, or you want side-effect measurement built into the evaluation harness.

**When *not* to use it:** you need one CAA vector (use `steering-vectors` or Dialz); you need vLLM-native throughput (EasySteer, vLLM-Lens); activation steering is one of four surfaces, so check the method you want is actually implemented before committing.

## Persona vectors and the Assistant Axis

Aliases: persona vectors, trait vectors, "evil vector", "sycophancy vector", Assistant Axis, `safety-research/persona_vectors` on GitHub.

**What it is.** Chen, Arditi, Sleight, Evans & Lindsey 2025, "Persona Vectors: Monitoring and Controlling Character Traits in Language Models" (arXiv:2507.21509): directions for traits such as evil, sycophancy and hallucination, used to monitor personality drift at deployment, to predict which finetuning shifts (and training examples) will move a trait, to undo shifts post hoc, or to prevent them with "preventative steering" during finetuning. Repo `safety-research/persona_vectors` (466 stars; last push 2026-04-22). Lu, Gallagher, Michala, Fish & Lindsey 2026, "The Assistant Axis" (arXiv:2601.10387): the leading component of persona space is an "Assistant Axis"; steering toward it reinforces helpful, harmless behaviour, steering away makes the model adopt other identities and, at extreme values, a mystical or theatrical style.

**When to use it:** tracking trait drift across a finetune or RL run, filtering finetuning data by projection onto a trait vector, or a cheap steering baseline for personality-like behaviours. For SAE-feature and attribution analyses of persona features in emergent misalignment (EM), see [`model-diffing.md`](model-diffing.md) and [`data-attribution.md`](data-attribution.md).

**When *not* to use it:** as proof of *why* a finetune went wrong — a projection shift is correlational; confirm by ablating or retraining. A single global vector per trait may also be too coarse if personas are context-conditional (see the next section).

## Does steering change alignment? Check side effects before trusting a steered eval

Aliases: steering side effects, alignment leakage, steering induces emergent misalignment, "automated grading" steering vector, split personas.

- **Betley, Treutlein & Dumas 2026, "Steering towards 'automated grading' degrades alignment"** (LessWrong, 2026-09-03; code `johny-b/public-steering-vectors`, last push 2026-09-04). On Qwen3.6-27B they build a difference-of-means vector from 270 contrast pairs where one side says answers are graded by an automated script and the other says a human will evaluate them (activations taken at the last token of the chat-templated prompt, added at every position at one layer, strengths about -0.5 to 0.3). Steering toward the *automated grader* increases violent actions in the agentic-misalignment Murder and Corporate Espionage scenarios, power-seeking and killing in Machiavelli, the fraction of known falsehoods on TruthfulQA, Machiavellian personality traits, and attempted cheating on SWE-Bench Pro (via a git-history loophole the authors left open unintentionally); steering toward the *human grader* does the opposite. Refusal of harmful requests showed no clear effect, and math accuracy (HMMT, the Harvard-MIT Mathematics Tournament) dropped slightly in both directions. The authors call it an early update: one small model, one vector, results they replicated in independent codebases, and they are unsure how to interpret it. Their reading is evidence for context-conditional personas, as argued in Betley's "RL creates split personas" (LessWrong, 2026-08-19; no new experiments), versus the alternative that the vector just changes the model's beliefs about what gets rewarded. A J-Lens (Jacobian-lens) readout of the vector did not help predict the broader behaviour changes.
- **Korznikov et al., "The Rogue Scalpel: Activation Steering Compromises LLM Safety"** (arXiv:2509.22067, 2025-09-26; summarised on LessWrong by co-author Dontsov, 2026-08-21): steering in a *random* direction raised harmful compliance from 0% to 1–13% depending on the model, and SAE (sparse autoencoder) features for benign concepts (e.g. a "Portugal" feature) can break refusal as much as or more than random vectors; combining 20 random vectors that each jailbreak one prompt gives a universal attack. The side effect is prompt-dependent, so you cannot enumerate dangerous vectors in advance.
- **Cao et al., "Activation Steering Induces Emergent Misalignment: A More Comprehensive Evaluation"** (arXiv:2606.08682, 2026-06-07): steering can induce broad misalignment even on Qwen-3.5, and steered models' harmful answers are more coherent and semantically relevant than those of finetuned counterparts.
- **Luo, Liang & Xuan, "SteerCheck"** (arXiv:2608.24335, 2026-08-25): a preregistered attribution audit for steering claims. A plain isotropic random-vector control is not enough — sign-randomized same-construction directions often keep substantial alignment with the target (25.3% of draws exceeded cosine 0.5; effect strongly tracked signed cosine, rho = .94) — so report the cosine distribution of your controls, not just that "random did nothing".

**Checklist before you publish a steered result:** (1) run an unrelated safety battery (refusals, agentic misalignment, TruthfulQA-style honesty, personality) at the same strength; (2) report random-direction and norm-matched controls *with their cosine to the target direction*; (3) check capability and perplexity at that strength; (4) remember models can be trained to detect steering (Fonseca Rivera & Africa, "Steering Awareness", arXiv:2511.21399), so a steered evaluation may be confounded by the model inferring it is being tested.

**When *not* to read this as settled:** the Betley result is one model, one vector, from a research update, and the "automated grading" pole has no realistic RL-training counterpart; treat it as a prompt to run side-effect checks, not as a measured effect size you can cite for other models.

## Cross-cutting steering pitfalls

- **Steering effects don't always generalize.** A vector that flips refusal on a held-out test set may not produce the underlying *behavior* — only the surface refusal. Always check on out-of-distribution cases. This is documented systematically in Tan, Chanin et al. 2024, "Analyzing the Generalization and Reliability of Steering Vectors" (arXiv:2407.12404, ICML 2024; codebase `dtch1997/steering-bench`): steerability is highly *variable across inputs* in-distribution, and for several concepts steering vectors are *brittle to reasonable prompt changes* out-of-distribution. (Note: two of its authors, Daniel Tan and David Chanin, also wrote the `steering-vectors` library.)
- **"Is this steering or just noise?"** With small contrast sets, mean-difference vectors are noisy. Use ≥100 pairs per side; check via random-split control: do random "positive/negative" splits give nontrivial steering effects? If yes, your real steering effect may be artifactual.
- **Magnitude search burns budget.** Steering generally requires sweeping `multiplier` in [-5, +5]-ish; budget for it.
- **Eval-aware models.** Models that have learned to detect being evaluated may behave differently with/without obvious "evaluator" prompts. Steering may or may not interact with this — see Steering Evaluation-Aware Language Models (arXiv 2510.20487) for a recent example.
- **Where you read the source activations matters as much as the layer.** Ye et al., "Where Steering Signals Come From: Activation Source Selection in Activation Steering" (arXiv:2607.25270, 2026-07-28): holding the intervention fixed, changing only the source context and readout position changes steering success substantially across three instruction-tuned models and four task families. Strong signals came from *execution-boundary* states (the model is about to produce or continue the target behaviour), not simply from text that already shows the behaviour; their **tail subtraction** removes shared prompt/continuation semantics. This is consistent with the common practice of reading at the last prompt token right before generation.
- **Mean difference vs PCA vs classifier directions.** Im & Li, "A Unified Understanding and Evaluation of Steering Methods" (arXiv:2502.02716): in their framework the mean-difference vector is optimal, it consistently outperformed PCA-of-differences, PCA-of-embeddings and classifier directions on the tasks tested, and the top PCA component can be nearly orthogonal to the true steering direction. Default to mean difference; if you use PCA, report it.
- **Steering awareness.** Models can be finetuned to notice that a steering vector was injected (best of seven models in Fonseca Rivera & Africa, arXiv:2511.21399: 95.5% detection, 71.2% concept identification, zero false positives on clean inputs). A model not *saying* it noticed does not show it did not notice.
- **Layer-by-layer effects compound.** Steering at multiple layers simultaneously is non-linear; a vector that works at layer 15 alone may behave differently when combined with a layer-20 vector.
- **CAA = Contrastive Activation Addition.** Spelled out for keyword search: this is the same thing as "the steering vectors library" approach. RepE = Representation Engineering. ActAdd = Activation Addition — the GPT-2-era pre-CAA technique (Turner, Thiergart, Udell, Leech, Mini & MacDiarmid 2023, "Activation Addition: Steering Language Models Without Optimization", arXiv:2308.10248), which computes a steering vector from a single prompt pair via forward passes rather than learning it.

## Cross-references

- Underlying interp libraries: [`mech-interp.md`](mech-interp.md).
- SAEs (for feature steering): [`saes.md`](saes.md).
- Probes (for finding directions in the first place): [`probes.md`](probes.md).
- vLLM-Lens for scale: [`serving-and-activations.md`](serving-and-activations.md).

---

## Common questions

### How do I make a steering vector?

The Contrastive Activation Addition (CAA) recipe: (1) build pairs of contrastive prompts — positive examples of the behavior, negative examples; (2) run the model on each, capture residual-stream activations at a specific layer + token position; (3) take the mean difference of activations. That's your steering vector. Apply by adding it (scaled) to the residual stream during generation. The `steering-vectors` library implements this end-to-end.

### Why doesn't my steering vector work?

Most common causes: (1) **wrong layer** — try the middle layers (~half-depth) first; very early or very late layers usually don't propagate behaviorally. (2) **wrong magnitude** — sweep multiplier in [-5, +5]; the right value is dataset- and model-dependent. (3) **wrong token position** — average over the last token of the answer prefix or specific positions, not arbitrary positions. (4) **too few contrast pairs** — use ≥100 per side; with fewer, the vector is dominated by noise.

### What is CAA (Contrastive Activation Addition)?

CAA = **Contrastive Activation Addition** — the dominant method for activation steering in 2024–2026. Computes a steering vector by averaging the difference of residual-stream activations between matched contrastive prompt pairs (e.g. sycophantic vs non-sycophantic answers), then adds the vector during inference to dial the trait up or down. Originated: Panickssery et al. 2023, "Steering Llama 2 via Contrastive Activation Addition."

### Can I apply steering at vLLM scale (production throughput)?

Yes — use **vLLM-Lens** (UK AISI). Pass steering vectors via `GenerateConfig.extra_body` when calling the vLLM-Lens-served model from Inspect AI or directly via the OpenAI-compatible API. ~20% slower than vanilla vLLM, dramatically faster than nnsight or TransformerLens for the same task. See [`serving-and-activations.md`](serving-and-activations.md).

### Does activation steering generalize?

Often less than you'd hope. A vector that flips refusal on a held-out test set may not produce the underlying *behavior change* — only the surface refusal token. Always test on out-of-distribution prompts. The systematic study is Tan, Chanin et al. 2024, "Analyzing the Generalization and Reliability of Steering Vectors" (arXiv:2407.12404; codebase `dtch1997/steering-bench`): in-distribution steerability varies a lot across inputs, and OOD several concepts' vectors are brittle to reasonable prompt changes. With small contrast sets, mean-difference vectors are noisy — run a control: do random "positive/negative" splits give nontrivial steering effects? If yes, your real steering effect may be partly artifactual.

### Steering vs SAE feature steering — which?

**CAA-style steering vectors** are simpler, work with no SAE, and apply broadly. **SAE feature steering** (clamp / scale / ablate one SAE feature) is more targeted but only as good as the SAE — you may find a feature is "split" across multiple SAE latents. For first-pass experiments use CAA; for fine-grained intervention with mechanistic claims, SAE features. See [`saes.md`](saes.md).

### Does activation steering make a model less safe?

It can. Even random directions raise harmful compliance (Korznikov et al., arXiv:2509.22067: 0% to 1–13%), steering can induce emergent misalignment (Cao et al., arXiv:2606.08682), and a steering vector built from an "automated grader vs human grader" contrast shifted violence, deception and Machiavellian behaviour in Qwen3.6-27B (Betley et al., LessWrong 2026-09-03). Run an unrelated safety battery and cosine-matched random controls at your chosen strength. See "Does steering change alignment?" above.

### My Gemma-3 abliteration / refusal direction produces gibberish — why?

Likely a dominant residual-stream coordinate (channel 2339 on Gemma-3-12B) swamping the difference-of-means vector; MMLU fell to 0.242 in one reported setup. Winsorize activations (e.g. clip at the 99.5th percentile), mask the loud coordinate(s), or standardize per coordinate before taking the difference (Mishra, LessWrong 2026-09-15; single-author, one seed). See the abliteration section above.

### What is the refusal direction / abliteration?

**Refusal direction**: a direction in activation space found via mean-difference of activations on harmful vs harmless prompts (Arditi et al. 2024, "Refusal in Language Models Is Mediated by a Single Direction", arXiv:2406.11717). **Abliteration**: projecting that direction out of the model's weights, producing an uncensored "abliterated" checkpoint. Useful for refusal-mechanism research; not recommended for deployment. **Note:** the single-direction claim is contested — later work (Marshall et al. arXiv:2411.09003; Pan et al. arXiv:2502.17420) finds refusal is better described by an affine map or *multiple* directions.

**Which repo?** Use **`andyrdt/refusal_direction`** for the canonical Arditi-paper reproduction, or **`Orion-zhen/abliteration`** for a transformers-native modern implementation. **Avoid `FailSpy/abliterator`** — last commit June 2024, stale; the early popularity is no longer matched by maintenance.

---

Last verified: 2026-10. `steering-vectors` v0.12.2 (Feb 2025, slow but stable; authors David Chanin and Daniel Tan). `dialz` v1.1.4 (cardiffnlp/dialz, Cardiff NLP, more active than steering-vectors as of April 2026). RepE (`andyzoujm/representation-engineering`) frozen since Aug 2024 — still cited as baseline; new work should use steering-vectors or dialz. `repeng` (vgel) is a separate lighter-weight library with GGUF export. Refusal direction: `andyrdt/refusal_direction` is canonical (June 2025); `FailSpy/abliterator` is stale. (Citation audit 2026-06: corrected conditional activation steering to CAST / Lee et al. (arXiv:2409.05907) — previously mis-attributed to "Bayat et al." — and noted the CAA author's prior name Rimsky → Panickssery. Additions 2026-06: added the Arditi et al. arXiv ID (2406.11717) + author list, the contested "single direction" follow-ups (Marshall et al. 2411.09003, Pan et al. 2502.17420, "More than a Single Direction" 2602.02132), the steering-generalization study behind the no-generalize pitfall (Tan, Chanin et al. 2407.12404, `dtch1997/steering-bench`), and the ActAdd citation (Turner et al. 2308.10248); all verified via arXiv.) (Additions 2026-10: EasySteer (`ZJU-REAL/EasySteer`, arXiv:2509.25175, pushed 2026-10-09, v0.29.0), AI Steerability 360 (`generative-computing/steerability`, ex-`IBM/AISteer360`, arXiv:2603.07837, v0.5.5), persona vectors (arXiv:2507.21509, `safety-research/persona_vectors` pushed 2026-04-22) and the Assistant Axis (2601.10387), a "Does steering change alignment?" section (Betley et al. LessWrong 2026-09-03 + `johny-b/public-steering-vectors`; arXiv:2509.22067, 2606.08682, 2608.24335, 2511.21399), pitfalls from arXiv:2607.25270 and 2502.02716, and the Gemma-3 dominant-coordinate abliteration pitfall (LessWrong 2026-09-15). Re-checked 2026-10-09 with `gh api`: `steering-vectors/steering-vectors` last push 2025-02-21, `cardiffnlp/dialz` 2026-03-26, `IBM/activation-steering` (CAST) 2026-10-08. arXiv IDs fetched from abs pages; LessWrong results are single-author and unreplicated.)
