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
| Steer in *weight* space (subtract two small finetunes) instead of activation space, for stronger out-of-distribution control | **contrastive weight steering** (`safety-research/weight-steering`, Fierro & Roger arXiv:2511.05408) |
| To know whether a steering intervention will still work on a larger model | See "Will steering keep working as models scale?" below |
| To benchmark a steering method against prompting and finetuning baselines on the same concepts | **AxBench** (`stanfordnlp/axbench`; see "AxBench" below) |
| Big-Five (OCEAN) personality traits as LoRA adapters you can scale and add together | **Persona Cartography** (`persona-cartography/persona-cartography`; see below) |
| Steering ops (add, norm-scaled add, projection cap, ablate, swap) that run identically on HF eager and vLLM | **interp-engine** (see [`serving-and-activations.md`](serving-and-activations.md#interp-engine-neuronpedias-inference-engine)) |

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
- **Abliteration can be inherited through distillation on unrelated prompts.** Minh Hoang, "Inheritance of Refusals from Abliterated Models" (LessWrong, 2026-10-10; MATS 12 application project; code `luminary19/mats12`, no license). A Llama 3.2 3B student fine-tuned on an abliterated Qwen 3.5 9B teacher's answers to 20,000 general OLMo prompts (all but four unrelated to China) refused 0/450 China-sensitive questions, versus 32/450 (7.11%) for a student trained on the original teacher's answers; a second-generation Llama student, trained on the first student's answers, refused 22/450 (4.89%) while its coherence fell further (38.98 → 22.55 on a 0–100 autorater scale). Single author, low-coherence students, one judge model. Implication: if you distill from an abliterated or steered model, check the student for the edited behaviour even when the distillation data never touch the edited topic.
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
- **Choosing the feature by correlation picks the wrong one.** Guo, Li & Chen, "What Do Sparse Autoencoder Feature Discovery Scores Identify? From Activations to Interventions" (arXiv:2610.15850, 2026-10-11; four model–SAE pairs): observational discovery scores generally do not identify a feature's intervention effect. For single-latent ablations with nonzero effects, a first-order gradient estimate ("intervention attribution") predicted the realized sign in 91–97% of cases versus 17–35% for probe-implied changes, and attribution-selected feature sets gave larger held-out ablation effects than sets picked by correlation, rank tests or probe coefficients. Rank candidate SAE (sparse autoencoder) features by gradient attribution of the intervention you plan to apply before steering or ablating.

## vLLM-Lens for production-scale steering

Aliases: `vllm-lens`, `UKGovernmentBEIS/vllm-lens` on GitHub.

For applying steering vectors during high-throughput inference (millions of samples, tensor-parallel 70B models), vLLM-Lens is the right tool. See [`serving-and-activations.md`](serving-and-activations.md) for full details. Quick summary: pass steering vectors via `GenerateConfig.extra_body` when calling the vLLM-Lens-served model from Inspect or directly via the OpenAI-compatible API.

## EasySteer

Aliases: `ZJU-REAL/EasySteer` on GitHub, arXiv:2509.25175 (Xu et al., "EasySteer: A Unified Framework for High-Performance and Extensible LLM Steering"), `vllm-steer`, `vllm.steer_vectors`, "steering on vLLM". README says it was accepted to EMNLP 2026 System Demonstrations.

**What it is.** A vLLM fork with a steering engine, plus Python packages around it: `easysteer.capture` (hidden states, attention outputs, MoE router logits), `easysteer.extraction` (analysis-based vectors such as difference-of-means), `easysteer.training` (learned steering adapters on frozen models), an OpenAI-compatible steering server, a web demo, pre-computed vectors for eight domains, and `replications/` of published steering papers. Requests carry a declarative `SteeringSpec` / `VectorSpec` / `ApplySpec` (which vector, scale, layers, and whether it applies to prompt and/or generation tokens). The paper reports 10.8–22.3x speedups over the steering frameworks it compared. v0.29.0 (2026-09-10) tracks vLLM 0.29.0 and added attention-head output capture, `attention_add` steering and an ITI (Inference-Time Intervention) replication; last push 2026-10-09.

**When to use it:** you want steering inside a vLLM engine with continuous batching and prefix caching, plus extraction and capture in the same stack, e.g. sweeping many multipliers over a large prompt set.

**When *not* to use it:** you want stock vLLM plus Inspect AI integration (use vLLM-Lens, above); you need only a minimal CAA (Contrastive Activation Addition) primitive (use `steering-vectors`); your model is not served by vLLM. Because it is a fork pinned to one vLLM version, it constrains the rest of your environment.

**Pitfalls:**
- **Install is an overlay, not a plain pip package.** The README's quick install is `pip install vllm==0.29.0`, then `rsync` the fork's `vllm-steer/vllm/` files over the installed vLLM package, then `pip install .` from the repo. It states that reinstalling or upgrading `vllm` reverts the overlay and you must re-apply the `rsync`. (Untested inference: after an accidental revert, steering requests are likely no longer recognised by the engine.)
- **PyPI name.** A PyPI project named `easysteer` exists (0.0.1.dev0, summary "An Easy-to-use Steering Framework for Editing Large Language Models"); it has not been verified to be this project. Install from the repository as the README describes.

## AI Steerability 360 (AISteer360)

Aliases: AISteer360, `generative-computing/steerability` on GitHub (formerly `IBM/AISteer360`, which redirects), arXiv:2603.07837 (Miehling et al., IBM Research, "AI Steerability 360: A Toolkit for Steering Large Language Models").

**What it is.** An open-source, Hugging Face-native toolkit that organises steering around four control surfaces — **input** (prompt), **structural** (weights / architecture), **state** (activations and attention) and **output** (decoding) — with a common *steering pipeline* interface that composes methods, and evaluation of pipelines on Inspect AI tasks including measurement of steering side effects. Optional vLLM support via vLLM-Hook (`uv pip install ".[vllm]"`). Python 3.12+; the README installs with `uv venv --python 3.12 && uv pip install .` from a clone; there is no PyPI project (2026-10). Latest release v0.5.5 (2026-10-03).

**When to use it:** comparing prompting, activation steering and decoding-time control under one interface, or you want side-effect measurement built into the evaluation harness.

**When *not* to use it:** you need one CAA vector (use `steering-vectors` or Dialz); you need vLLM-native throughput (EasySteer, vLLM-Lens); activation steering is one of four surfaces, so check the method you want is actually implemented before committing.

## AxBench: benchmark steering against prompting

Aliases: AxBench, `stanfordnlp/axbench` on GitHub, "Steering LLMs? Even Simple Baselines Outperform Sparse Autoencoders", rank-1 steering leaderboard, RePS, HyperSteer, ReFT-r1, DiffMean, supervised dictionary learning (SDL), concept detection benchmark.

**What it is.** Wu, Arora, Geiger, Wang, Huang, Jurafsky, Manning & Potts, "AxBench: Steering LLMs? Even Simple Baselines Outperform Sparse Autoencoders" (arXiv:2501.17148, ICML 2025 spotlight; repo Apache-2.0, last push 2026-03-12 — "Add SAELogits to steering leaderboard"). A benchmark that generates synthetic training and evaluation data from concept lists (e.g. Gemma Scope SAE labels) and scores methods on two axes, **concept detection** and **steering**, against prompting and finetuning baselines on Gemma-2-2B and 9B. It ships 16K-concept supervised-dictionary-learning data and SAE-scale dictionaries for ReFT-r1 and DiffMean. Abstract: "For steering, we find that prompting outperforms all existing methods, followed by finetuning. For concept detection, representation-based methods such as difference-in-means, perform the best. On both evaluations, SAEs are not competitive."

**The leaderboard is the tip (README, rank-1 steering, read 2026-10-14; average over Gemma-2-2B L10/L20 and 9B L20/L31):** Prompt **0.894**, RePS 0.720, ReFT-r1 0.543, SAE (filtered) 0.508 (9B columns only), DiffMean 0.239, SAE 0.165, LAT 0.127, PCA 0.105, Probe 0.098. Only HyperSteer (0.917) beats prompting, and it reports only two of the four columns. **Before claiming a steering result, run a prompt-only baseline on the same concept with the same judge** — in this benchmark it beats nearly every activation method.

**Reconciling with "mean difference is the best direction".** Im & Li (cross-cutting pitfalls below) find difference-of-means the best *activation* direction among those they compare, and AxBench finds DiffMean the best *concept detector*; neither contradicts AxBench's result that, for *steering* output, prompting beats activation methods including DiffMean (0.239). The choice of direction and the choice of steering-vs-prompting are separate questions.

**When to use it:** you propose a new steering or concept-detection method and want a comparison a reviewer will accept; you want a quick sanity check that your activation steering beats a prompt.

**When *not* to use it:** models other than Gemma-2 2B/9B unless you regenerate data and baselines; measuring safety *side effects* of steering (see "Does steering change alignment?" below and AISteer360 above).

## Persona vectors and the Assistant Axis

Aliases: persona vectors, trait vectors, "evil vector", "sycophancy vector", Assistant Axis, `safety-research/persona_vectors` on GitHub.

**What it is.** Chen, Arditi, Sleight, Evans & Lindsey 2025, "Persona Vectors: Monitoring and Controlling Character Traits in Language Models" (arXiv:2507.21509): directions for traits such as evil, sycophancy and hallucination, used to monitor personality drift at deployment, to predict which finetuning shifts (and training examples) will move a trait, to undo shifts post hoc, or to prevent them with "preventative steering" during finetuning. Repo `safety-research/persona_vectors` (466 stars; last push 2026-04-22). Lu, Gallagher, Michala, Fish & Lindsey 2026, "The Assistant Axis" (arXiv:2601.10387): the leading component of persona space is an "Assistant Axis"; steering toward it reinforces helpful, harmless behaviour, steering away makes the model adopt other identities and, at extreme values, a mystical or theatrical style.

**When to use it:** tracking trait drift across a finetune or RL run, filtering finetuning data by projection onto a trait vector, or a cheap steering baseline for personality-like behaviours. For SAE-feature and attribution analyses of persona features in emergent misalignment (EM), see [`model-diffing.md`](model-diffing.md) and [`data-attribution.md`](data-attribution.md).

**When *not* to use it:** as proof of *why* a finetune went wrong — a projection shift is correlational; confirm by ablating or retraining. A single global vector per trait may also be too coarse if personas are context-conditional (see "Does steering change alignment?" below).

## Contrastive weight steering (weight arithmetic)

Aliases: weight steering, contrastive weight steering, weight-space steering, task vectors / task arithmetic for behaviours, "evil weight direction", `safety-research/weight-steering` on GitHub.

**What it is.** Fierro & Roger, "Steering Language Models with Weight Arithmetic" (arXiv:2511.05408, ICLR 2026). Run two small LoRA (low-rank adaptation) finetunes on contrastive data, one showing the behaviour and one showing its opposite; subtract their weight deltas to get a behaviour direction in *weight* space; add or subtract a scaled copy of it to the model's weights. Compared with activation steering built from the same narrow data (they used the persona-vectors activation-steering code), weight steering often generalized further out of distribution, reaching stronger control of sycophancy and "evilness" before general capability degraded (Qwen2.5-7B-Instruct by default). After task finetuning, it partly undid sycophancy and under-refusal that the finetune introduced while keeping the task gains (Qwen2.5-1.5B-Instruct on a greatest-common-divisor task, Llama-2-7b-chat on GSM8K). It also gives a monitoring signal: the task vectors of emergent-misalignment finetunes (bad medical, financial and sports advice) had higher cosine similarity to an "evil" weight direction than good or control finetunes did.

**Code.** `safety-research/weight-steering` (no license file; last push 2025-11-11): `inference_and_eval.py` generates data and trains through an Axolotl config, and `task_vectors.py` builds the steered checkpoint. Datasets are on Hugging Face (`cfierro/sycophancy_eval_answer`, `cfierro/gcd`).

**When to use it:** you can afford two small finetunes and want behaviour control that holds on prompts unlike the contrast data, or a weight-space drift monitor for a finetuning run.

**When *not* to use it:** you need per-request, reversible control at inference time (activation steering composes with serving; a weight edit is a new checkpoint); you have no training access. The authors' limitations: simple controlled tasks, one form of weight addition, a single activation-steering baseline, narrow multiple-choice side-effect checks, and a monitoring signal not yet shown to be strong enough for practice.

**Pitfall for any adapter-arithmetic pipeline: PEFT before 0.21.0 had two silent bugs** (release notes, v0.21.0 of 2026-09-15; current v0.21.2 of 2026-10-01). (1) "Combining LoRA adapters using `add_weighted_adapter` had a bug in the `SVD` path which led to the LoRA scaling being applied twice." If a weight-steering, task-vector or adapter-soup result used `add_weighted_adapter(..., combination_type="svd")` on an older PEFT, it is worth re-running. (2) Adding a second adapter with `add_adapter` that targets non-existent layers now raises; "Before, the adapter would just not adapt anything but be silent about it." A cheap guard on any version: assert `peft_model.targeted_module_names` is non-empty after attaching an adapter. (`safety-research/weight-steering` builds its steered checkpoint in `task_vectors.py`, which does not call `add_weighted_adapter`.)

## Persona Cartography: personality traits as scalable, composable LoRAs

Aliases: Persona Cartography, `persona-cartography/persona-cartography` on GitHub, OCEAN adapters, Big Five LoRAs, trait LoRAs, weight-space personas, Open Character Training.

**What it is.** Baines, Gonzalvez Hawthorne, Koroliuk, Shalibashvili, Dumas, Voudouris & Africa, "Persona Cartography: Charting Language Model Personality Traits in Weight Space" (arXiv:2607.07916, 2026-07-08; LessWrong 2026-07-10; code MIT, last push 2026-09-25; artifacts in the Hugging Face dataset repo `persona-cartography/monorepo`). One LoRA per trait *direction* — amplify or suppress each of Openness, Conscientiousness, Extraversion, Agreeableness and Neuroticism (ten adapters) — trained with Open Character Training (constitution-guided paired-teacher DPO → SFT → soup). Abstract: across six models from three families (4B–32B), "each adapter moves its target trait largely monotonically with scale, combines approximately additively with other adapters to construct mixed personas, and preserves performance on capability benchmarks at moderate scales", and moving along neuroticism and agreeableness affects frustration and sycophancy respectively. The repo's default base model is Llama-3.1-8B-Instruct, and it includes an **activation-capping comparison** (cap the residual projection onto a persona axis) — a direct activation-vs-weight comparison on the same traits.

```bash
# From the README: setup, then one trait + direction end to end (DPO + introspection SFT + evals)
bash scripts/setup.sh
bash scripts/pipelines/run_persona_pipeline.sh --trait neuroticism --direction amp --model llama-3.1-8b-it
# --control trains the recipe-matched null control (no trait)
```

**Honest scope note (README's paper→code table):** training, TRAIT multiple-choice and MMLU evals, the calibrated OCEAN/coherence LLM judges, scaling/composition and activation capping are reproducible from the clean code layer; the **downstream safety results** (frustration, sycophancy, CoCoNot, WildJailbreak) and the unsupervised behavioural-factor pipeline live in `src_dev/` and are marked out of scope.

**When to use it:** you want a persona dial that composes (mix traits by adding adapters), a weight-space baseline to compare against persona vectors or activation capping, or a recipe-matched null control for trait finetunes.

**When *not* to use it:** you need the downstream safety findings reproduced from reviewed code (they are in `src_dev/`); you need per-request control without new checkpoints (use activation steering); traits outside OCEAN without retraining.

## Will steering keep working as models scale? (open problem)

Aliases: steering window, viable steering window, steering resistance, Endogenous Steering Resistance (ESR), steering against eval awareness at scale.

**The concern.** J Bostock, "Steering Might Stop Working Soon" (LessWrong, 2026-04-05; an informal post with a small Claude-run experiment; code `jonathanbostock/activation-steering-sweep`). The *viable steering window* is the range of strengths where the target behaviour changes but capability has not yet collapsed. Bostock built contrastive activation vectors (e.g. "owl" vs "hawk" in "The caracara is a(n) …") to push Gemma 3 models toward a false answer to a factual question, and measured capability on five simple Python questions. Smaller models were steerable into the wrong answer. The larger ones turned incoherent before they gave it, so the window shrank with size. This is three factual questions (the two added ones run only on the three smaller models) and an informal sweep, not a controlled study. The post steered toward a false answer to simulate steering *against a belief the model holds*, the shape of steering against evaluation awareness, and argues the window will keep narrowing as models scale; it also notes that a clear, known fact may be harder to steer against than a hazy one like "is this an eval". Related peer-reviewed evidence: McKenzie et al., "Endogenous Resistance to Activation Steering in Language Models" (arXiv:2602.06941, ICML 2026; code `agencyenterprise/endogenous-steering-resistance`) find models recovering mid-generation from off-task steering with sparse autoencoder (SAE) latents: an explicit-resistance rate (a verbal restart that improves on the first attempt) of 3.8% for Llama-3.3-70B and below 1% for four smaller Llama-3 and Gemma-2 models, with scale not separable from architecture and training; models can also be finetuned to detect steering (Fonseca Rivera & Africa, "Steering Awareness", arXiv:2511.21399).

**What would count as progress (the bar).** For a steering method (activation, SAE-feature or weight-space) you would report, across at least three sizes of one model family, the width of the viable window: the strength range where the target behaviour moves by a stated amount while a held-out capability score stays within a stated tolerance of baseline. The method should keep that window open at the largest size, on targets that contradict what the model believes (not only style or persona targets). Report random- and norm-matched controls. Contrastive weight steering (above) is one candidate to test against this bar; it was reported to reach stronger control before degradation than activation steering at 7B, but that has not been measured across a scale sweep.

## Does steering change alignment? Check side effects before trusting a steered eval

Aliases: steering side effects, alignment leakage, steering induces emergent misalignment, "automated grading" steering vector, split personas.

- **Betley, Treutlein & Dumas 2026, "Steering towards 'automated grading' degrades alignment"** (LessWrong, 2026-09-03; code `johny-b/public-steering-vectors`, last push 2026-09-04). On Qwen3.6-27B they build a difference-of-means vector from 270 contrast pairs where one side says answers are graded by an automated script and the other says a human will evaluate them (activations taken at the last token of the chat-templated prompt, added at every position at one layer, strengths about -0.5 to 0.3). Steering toward the *automated grader* increases violent actions in the agentic-misalignment Murder and Corporate Espionage scenarios, power-seeking and killing in Machiavelli, the fraction of known falsehoods on TruthfulQA, Machiavellian personality traits, and attempted cheating on SWE-Bench Pro (via a git-history loophole the authors left open unintentionally); steering toward the *human grader* does the opposite. Refusal of harmful requests showed no clear effect, and math accuracy (HMMT, the Harvard-MIT Mathematics Tournament) dropped slightly in both directions. The authors call it an early update: one small model, one vector, results they replicated in independent codebases, and they are unsure how to interpret it. Their reading is evidence for context-conditional personas, as argued in Betley's "RL creates split personas" (LessWrong, 2026-08-19; no new experiments), versus the alternative that the vector just changes the model's beliefs about what gets rewarded. A J-Lens (Jacobian-lens) readout of the vector did not help predict the broader behaviour changes.
- **Korznikov et al., "The Rogue Scalpel: Activation Steering Compromises LLM Safety"** (arXiv:2509.22067, 2025-09-26; summarised on LessWrong by co-author Dontsov, 2026-08-21): steering in a *random* direction raised harmful compliance from 0% to 1–13% depending on the model, and SAE (sparse autoencoder) features for benign concepts (e.g. a "Portugal" feature) can break refusal as much as or more than random vectors; combining 20 random vectors that each jailbreak one prompt gives a universal attack. The side effect is prompt-dependent, so you cannot enumerate dangerous vectors in advance.
- **Cao et al., "Activation Steering Induces Emergent Misalignment: A More Comprehensive Evaluation"** (arXiv:2606.08682, 2026-06-07): steering can induce broad misalignment even on Qwen-3.5, and steered models' harmful answers are more coherent and semantically relevant than those of finetuned counterparts.
- **Luo, Liang & Xuan, "SteerCheck"** (arXiv:2608.24335, 2026-08-25): a preregistered attribution audit for steering claims. A plain isotropic random-vector control is not enough — sign-randomized same-construction directions often keep substantial alignment with the target (25.3% of draws exceeded cosine 0.5; effect strongly tracked signed cosine, rho = .94) — so report the cosine distribution of your controls, not just that "random did nothing".

**Checklist before you publish a steered result:** (1) run an unrelated safety battery (refusals, agentic misalignment, TruthfulQA-style honesty, personality) at the same strength; (2) report random-direction and norm-matched controls *with their cosine to the target direction* — norm-matched to the layer you inject at, not the layer you collected from; (3) compare against a vector built the same way for a **competing target** (Xu & Sun, arXiv:2610.19359); (4) check capability and perplexity at that strength; (5) remember models can be trained to detect steering (Fonseca Rivera & Africa, "Steering Awareness", arXiv:2511.21399), so a steered evaluation may be confounded by the model inferring it is being tested.

**When *not* to read this as settled:** the Betley result is one model, one vector, from a research update, and the "automated grading" pole has no realistic RL-training counterpart; treat it as a prompt to run side-effect checks, not as a measured effect size you can cite for other models.

## Cross-cutting steering pitfalls

- **Steering effects don't always generalize.** A vector that flips refusal on a held-out test set may not produce the underlying *behavior* — only the surface refusal. Always check on out-of-distribution cases. This is documented systematically in Tan, Chanin et al. 2024, "Analyzing the Generalization and Reliability of Steering Vectors" (arXiv:2407.12404, ICML 2024; codebase `dtch1997/steering-bench`): steerability is highly *variable across inputs* in-distribution, and for several concepts steering vectors are *brittle to reasonable prompt changes* out-of-distribution. (Note: two of its authors, Daniel Tan and David Chanin, also wrote the `steering-vectors` library.)
- **Run a prompt-only baseline.** On AxBench's rank-1 steering leaderboard, simply prompting for the concept averages 0.894 against 0.720 for the best activation method reporting all four columns (RePS) and 0.239 for difference-of-means; only HyperSteer, on two of four columns, is higher. A steering result is more convincing when it beats "just ask for it" with the same judge (see "AxBench" above).
- **"Is this steering or just noise?"** With small contrast sets, mean-difference vectors are noisy. Use ≥100 pairs per side; check via random-split control: do random "positive/negative" splits give nontrivial steering effects? If yes, your real steering effect may be artifactual.
- **Magnitude search burns budget.** Steering generally requires sweeping `multiplier` in [-5, +5]-ish; budget for it.
- **Eval-aware models.** Models that have learned to detect being evaluated may behave differently with/without obvious "evaluator" prompts. Steering may or may not interact with this — see Steering Evaluation-Aware Language Models (arXiv 2510.20487) for a recent example.
- **Where you read the source activations matters as much as the layer.** Ye et al., "Where Steering Signals Come From: Activation Source Selection in Activation Steering" (arXiv:2607.25270, 2026-07-28): holding the intervention fixed, changing only the source context and readout position changes steering success substantially across three instruction-tuned models and four task families. Strong signals came from *execution-boundary* states (the model is about to produce or continue the target behaviour), not simply from text that already shows the behaviour; their **tail subtraction** removes shared prompt/continuation semantics. This is consistent with the common practice of reading at the last prompt token right before generation.
- **Mean difference vs PCA vs classifier directions.** Im & Li, "A Unified Understanding and Evaluation of Steering Methods" (arXiv:2502.02716): in their framework the mean-difference vector is optimal, it consistently outperformed PCA-of-differences, PCA-of-embeddings and classifier directions on the tasks tested, and the top PCA component can be nearly orthogonal to the true steering direction. Default to mean difference; if you use PCA, report it.
- **Steering awareness.** Models can be finetuned to notice that a steering vector was injected (best of seven models in Fonseca Rivera & Africa, arXiv:2511.21399: 95.5% detection, 71.2% concept identification, zero false positives on clean inputs). A model not *saying* it noticed does not show it did not notice.
- **Remove the sharp directions from a CAA vector.** Azizi, Fayyazi, Razmara, Potraghloo, Kundu & Pedram, "The Sharp Directions Are Against You: Curvature Analysis of Activation Steering" (arXiv:2610.16084, NeurIPS 2026; Qwen2.5-7B, Llama-3.1-8B, Mistral-7B; four behavioural tasks). They define a *steering Hessian* (second derivative of the behavioural loss with respect to the steering vector); its top eigenvectors are "sharp directions". "Steering along sharp directions reverses the intended behavior in every condition tested, with anti-steer rates of 53-100%", although they hold only 1–5% of the CAA (Contrastive Activation Addition) vector's squared norm. Projecting them out ("sharp removal") keeps the vector nearly unchanged (cosine > 0.974, norm reduction < 3% for typical settings) and "outperforms standard CAA in open-ended generation across all 25 conditions tested". Code availability not checked. Worth trying when a CAA vector steers some inputs the wrong way.
- **Test against a competing target, not only random or unsteered baselines.** Xu & Sun, "Steering Vectors for Competing Ethical Frameworks Are Interchangeable: A Competing-Target Test for Activation Steering" (arXiv:2610.19359, 2026-10-14): build the vector for a *competing* target the same way and use an equivalence test to state when the two differ by less than a useful margin. For Kantian deontology vs act utilitarianism, "prompting a framework raises its score and lowers the other's, whereas vectors for either framework move both scores alike, and none reaches the margin" — the two vectors mostly share a "request to apply some framework" direction, which random and unsteered baselines cannot detect. The same construction did separate an optimistic from a pessimistic tone, whose vectors share much less.
- **Injecting a vector at a different layer than it was collected: match the norm.** Residual-stream norms grow with depth, so a late-layer vector injected early is oversized. Hasik (master's thesis highlights, LessWrong, 2026-10-17; Gemma 2/3/4 only; code `TheMMpl/mech_interp`, no license) reports that "injecting a late layer vector into an early layer produces the same `Yes` shift as a random vector of the same norm", and that norm-matching to the injection layer removes most of that confusion. In yes/no readouts, also read the Yes−No logit difference on an unrelated control question *under injection*: "A false positive check without injection does not catch confusion that only appears *under* injection." This bears on concept-injection introspection results, including the refusal-ablation result discussed in [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).
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

### My CAA vector pushes some inputs the wrong way — why?

A few high-curvature ("sharp") directions in the vector can reverse the intended behaviour: in arXiv:2610.16084 steering along them anti-steered in 53–100% of cases across Qwen2.5-7B, Llama-3.1-8B and Mistral-7B, though they carry only 1–5% of the squared norm. Projecting them out ("sharp removal") beat standard CAA in all 25 open-ended-generation conditions tested. Also check that the vector is not mostly a shared component with a competing target (arXiv:2610.19359). See "Cross-cutting steering pitfalls" above.

### Steering vs SAE feature steering — which?

**CAA-style steering vectors** are simpler, work with no SAE, and apply broadly. **SAE feature steering** (clamp / scale / ablate one SAE feature) is more targeted but only as good as the SAE — you may find a feature is "split" across multiple SAE latents. For first-pass experiments use CAA; for fine-grained intervention with mechanistic claims, SAE features. See [`saes.md`](saes.md).

### Does activation steering make a model less safe?

It can. Even random directions raise harmful compliance (Korznikov et al., arXiv:2509.22067: 0% to 1–13%), steering can induce emergent misalignment (Cao et al., arXiv:2606.08682), and a steering vector built from an "automated grader vs human grader" contrast shifted violence, deception and Machiavellian behaviour in Qwen3.6-27B (Betley et al., LessWrong 2026-09-03). Run an unrelated safety battery and cosine-matched random controls at your chosen strength. See "Does steering change alignment?" above.

### Activation steering vs weight steering — which?

Activation steering (CAA, Contrastive Activation Addition) needs no training and can be switched per request. Contrastive weight steering (Fierro & Roger, arXiv:2511.05408; `safety-research/weight-steering`) needs two small LoRA (low-rank adaptation) finetunes and produces a new checkpoint, but in their sycophancy and "evil" experiments it generalized further out of distribution before capabilities degraded. If your activation vector stops working off-distribution, or the model turns incoherent before the behaviour moves, try weight steering. See "Contrastive weight steering" above.

### Does activation steering beat just prompting the model?

Usually not, on the one large benchmark that compares them. AxBench (arXiv:2501.17148; Gemma-2-2B/9B) found that "prompting outperforms all existing methods, followed by finetuning"; on its current steering leaderboard prompting averages 0.894, RePS 0.720, DiffMean 0.239 and SAE features 0.165. Steering is still useful when you need an internal handle (to test a mechanism, to steer against something the model will not do when asked, or to study side effects), but report the prompt baseline. See "AxBench" above.

### Can I steer personality traits with LoRAs instead of vectors?

Yes: Persona Cartography (arXiv:2607.07916) trains one LoRA per OCEAN trait direction and reports that adapters scale monotonically, add approximately, and preserve capabilities at moderate scales, across six models (4B–32B). Its repo also runs an activation-capping comparison on the same traits. See "Persona Cartography" above.

### My steering vector works on a small model but the larger model just turns incoherent — is my code broken?

Possibly not. Informal sweeps on Gemma 3 found the viable steering window (strengths where the behaviour changes before capability collapses) shrinking with model size when steering toward a false factual answer (Bostock, LessWrong 2026-04-05), and in arXiv:2602.06941 the largest model tested (Llama-3.3-70B) showed the most mid-generation recovery from steering. Report the window per model size rather than one strength. See "Will steering keep working as models scale?" above.

### My Gemma-3 abliteration / refusal direction produces gibberish — why?

Likely a dominant residual-stream coordinate (channel 2339 on Gemma-3-12B) swamping the difference-of-means vector; MMLU fell to 0.242 in one reported setup. Winsorize activations (e.g. clip at the 99.5th percentile), mask the loud coordinate(s), or standardize per coordinate before taking the difference (Mishra, LessWrong 2026-09-15; single-author, one seed). See the abliteration section above.

### What is the refusal direction / abliteration?

**Refusal direction**: a direction in activation space found via mean-difference of activations on harmful vs harmless prompts (Arditi et al. 2024, "Refusal in Language Models Is Mediated by a Single Direction", arXiv:2406.11717). **Abliteration**: projecting that direction out of the model's weights, producing an uncensored "abliterated" checkpoint. Useful for refusal-mechanism research; not recommended for deployment. **Note:** the single-direction claim is contested — later work (Marshall et al. arXiv:2411.09003; Pan et al. arXiv:2502.17420) finds refusal is better described by an affine map or *multiple* directions.

**Which repo?** Use **`andyrdt/refusal_direction`** for the canonical Arditi-paper reproduction, or **`Orion-zhen/abliteration`** for a transformers-native modern implementation. **Avoid `FailSpy/abliterator`** — last commit June 2024, stale; the early popularity is no longer matched by maintenance.

---

Last verified: 2026-10-20. `steering-vectors` v0.12.2 (Feb 2025, slow but stable; authors David Chanin and Daniel Tan). `dialz` v1.1.4 (cardiffnlp/dialz, Cardiff NLP, more active than steering-vectors as of April 2026). RepE (`andyzoujm/representation-engineering`) frozen since Aug 2024 — still cited as baseline; new work should use steering-vectors or dialz. `repeng` (vgel) is a separate lighter-weight library with GGUF export. Refusal direction: `andyrdt/refusal_direction` is canonical (June 2025); `FailSpy/abliterator` is stale. (Citation audit 2026-06: corrected conditional activation steering to CAST / Lee et al. (arXiv:2409.05907) — previously mis-attributed to "Bayat et al." — and noted the CAA author's prior name Rimsky → Panickssery. Additions 2026-06: added the Arditi et al. arXiv ID (2406.11717) + author list, the contested "single direction" follow-ups (Marshall et al. 2411.09003, Pan et al. 2502.17420, "More than a Single Direction" 2602.02132), the steering-generalization study behind the no-generalize pitfall (Tan, Chanin et al. 2407.12404, `dtch1997/steering-bench`), and the ActAdd citation (Turner et al. 2308.10248); all verified via arXiv.) (Additions 2026-10: EasySteer (`ZJU-REAL/EasySteer`, arXiv:2509.25175, pushed 2026-10-09, v0.29.0), AI Steerability 360 (`generative-computing/steerability`, ex-`IBM/AISteer360`, arXiv:2603.07837, v0.5.5), persona vectors (arXiv:2507.21509, `safety-research/persona_vectors` pushed 2026-04-22) and the Assistant Axis (2601.10387), a "Does steering change alignment?" section (Betley et al. LessWrong 2026-09-03 + `johny-b/public-steering-vectors`; arXiv:2509.22067, 2606.08682, 2608.24335, 2511.21399), pitfalls from arXiv:2607.25270 and 2502.02716, and the Gemma-3 dominant-coordinate abliteration pitfall (LessWrong 2026-09-15). Re-checked 2026-10-09 with `gh api`: `steering-vectors/steering-vectors` last push 2025-02-21, `cardiffnlp/dialz` 2026-03-26, `IBM/activation-steering` (CAST) 2026-10-08. arXiv IDs fetched from abs pages; LessWrong results are single-author and unreplicated.) (Additions 2026-10-12: contrastive weight steering — arXiv:2511.05408 abstract via the arXiv API, models, results and limitations read from the paper PDF, `safety-research/weight-steering` README read and repo checked via the GitHub API (last push 2025-11-11, no license); "Will steering keep working as models scale?" — Bostock's LessWrong post read in full via GraphQL (2026-04-05, informal, three factual questions; `jonathanbostock/activation-steering-sweep` resolves via `gh api`; the model sizes in its plots are in images and are not stated here), and Endogenous Steering Resistance arXiv:2602.06941 via the arXiv API (`agencyenterprise/endogenous-steering-resistance` resolves). The evidence bar is our own framing. Verification pass 2026-10-12: 31 claims checked, 4 corrected.) (Additions 2026-10-14: AxBench — arXiv:2501.17148 abstract via the arXiv API (eight authors), README leaderboard table read raw, repo metadata via `gh api` (last push 2026-03-12); Persona Cartography — arXiv:2607.07916 abstract, README (paper→code table, pipeline commands, default model, HF dataset `persona-cartography/monorepo` resolves); PEFT v0.21.0 release notes (SVD-path double scaling, silent no-op `add_adapter`; latest v0.21.2 on 2026-10-01) and `safety-research/weight-steering/task_vectors.py` (no `add_weighted_adapter` call); interp-engine steering ops from its `docs/USAGE.md`.) (Additions 2026-10-20: arXiv:2610.16084 (sharp removal), 2610.19359 (competing-target test) and 2610.15850 (intervention attribution) — abstracts only, code availability not checked; Hasik's thesis highlights (LessWrong 7TxeC9WPc5LxpjgP8) and Hoang's abliteration-inheritance post (LessWrong E7QHwJLgva4qMAn6B) read in full via GraphQL; `TheMMpl/mech_interp` and `luminary19/mats12` resolve via `gh api` (no license files). LessWrong results are single-author and unreplicated.)
