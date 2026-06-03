# Recommended Tooling for AI Safety Research (MATS Fellows)

A breadth-first guide to the tooling that AI safety researchers — especially MATS fellows running research-scale experiments — should know about. For each tool we cover **what it is, when to use it, when *not* to use it, and the common pitfalls**.

## Audience and scope

- **Audience:** MATS fellows and adjacent early-career safety researchers. Assumes you know PyTorch and have run a HuggingFace `transformers` model.
- **Scope:** AI-safety-specific tooling at research scale (≤70B params, single node or a few GPUs). We skip frontier-scale training infra (DeepSpeed/Megatron at scale, FSDP tuning, etc.) — fellows generally don't touch that.
- **Deliberately out of scope:** general ML tooling that isn't safety-flavored (e.g. base PyTorch, generic dataloaders), and capabilities-research-only tools.

## How to use this guide

1. **Start with [`docs/index.md`](docs/index.md)** — a "I want to do X, use Y" decision table.
2. **Then jump to the topic doc** for your area: interpretability, evals, SAEs, steering, red-teaming, etc.
3. Each topic doc is structured as a list of tools, each with its own self-contained section. You can read just one section without losing context.

## Topic docs

Docs are organized into topic folders under `docs/`. Start at the decision guide ([`docs/index.md`](docs/index.md)).

**Start here**

| File | Topic |
|------|-------|
| [`docs/index.md`](docs/index.md) | Decision guide — "I want to do X, use Y" |
| [`docs/start-here/faq.md`](docs/start-here/faq.md) | Cross-cutting beginner FAQ — API keys, where to start, costs, common errors |
| [`docs/start-here/glossary.md`](docs/start-here/glossary.md) | A–Z glossary of acronyms and concepts (CAA, GRPO, OOCR, RLAIF, MATS playbook, etc.) |
| [`docs/start-here/project-shapes.md`](docs/start-here/project-shapes.md) | Common project shapes — mech interp paper, SAE-feature paper, behavioral, control eval, RL safety, etc. |

**Models & compute**

| File | Topic |
|------|-------|
| [`docs/models-and-compute/open-weights-models.md`](docs/models-and-compute/open-weights-models.md) | Which open-weights model to use and why (DeepSeek-V4, Kimi, Gemma, Qwen, Llama) |
| [`docs/models-and-compute/compute.md`](docs/models-and-compute/compute.md) | Compute and infra (RunPod, Modal, Lambda, vast.ai, Slurm) |
| [`docs/models-and-compute/experiment-tracking.md`](docs/models-and-compute/experiment-tracking.md) | Experiment tracking and reproducibility (wandb, Hydra, run organization) |
| [`docs/models-and-compute/safety-toolkits.md`](docs/models-and-compute/safety-toolkits.md) | General safety research toolkits (safety-research/safety-tooling) |

**Interpretability & internals**

| File | Topic |
|------|-------|
| [`docs/interpretability/mech-interp.md`](docs/interpretability/mech-interp.md) | Mechanistic interpretability libraries (TransformerLens, nnsight, baukit) |
| [`docs/interpretability/saes.md`](docs/interpretability/saes.md) | Sparse autoencoders (SAELens, sparsify, dictionary_learning, Neuronpedia) |
| [`docs/interpretability/probes.md`](docs/interpretability/probes.md) | Probes and linear classifiers (CCS, contrast pairs, probity) |
| [`docs/interpretability/steering.md`](docs/interpretability/steering.md) | Activation steering and representation engineering (CAA, repe, Dialz) |
| [`docs/interpretability/serving-and-activations.md`](docs/interpretability/serving-and-activations.md) | Model serving and activation extraction at scale (vLLM-Lens, sglang, NDIF) |

**Evaluation & red-teaming**

| File | Topic |
|------|-------|
| [`docs/evaluation/evals.md`](docs/evaluation/evals.md) | Evaluation frameworks (Inspect AI, lm-eval-harness, METR HCAST) |
| [`docs/evaluation/agent-scaffolds.md`](docs/evaluation/agent-scaffolds.md) | Agent scaffolding for capability/safety evals (Inspect agents, smolagents) |
| [`docs/evaluation/datasets-benchmarks.md`](docs/evaluation/datasets-benchmarks.md) | Datasets and benchmarks (WMDP, HarmBench, MACHIAVELLI, refusal sets) |
| [`docs/evaluation/red-teaming.md`](docs/evaluation/red-teaming.md) | Red-teaming and jailbreak research (PAIR, GCG, garak, PyRIT, HarmBench) |

**Alignment science**

| File | Topic |
|------|-------|
| [`docs/alignment-science/behavioral-safety-playbook.md`](docs/alignment-science/behavioral-safety-playbook.md) | Behavioral safety research patterns (narrow→broad, judge prompts, cross-model replication, OOCR, reproducibility checklist) |
| [`docs/alignment-science/model-organisms.md`](docs/alignment-science/model-organisms.md) | Model organisms of misalignment (sleeper agents, alignment faking, emergent misalignment, agentic misalignment) |
| [`docs/alignment-science/cot-faithfulness.md`](docs/alignment-science/cot-faithfulness.md) | CoT faithfulness and monitorability (Lanham, Turpin, monitorability score, steganography risks) |
| [`docs/alignment-science/welfare-introspection.md`](docs/alignment-science/welfare-introspection.md) | Model welfare and introspection (activation injection, exit options, valence probes, consciousness frameworks) |

**Oversight, control & training**

| File | Topic |
|------|-------|
| [`docs/oversight-and-control/ai-control.md`](docs/oversight-and-control/ai-control.md) | AI Control (ControlArena, defer-to-trusted, trusted editing, untrusted monitoring, side tasks) |
| [`docs/oversight-and-control/debate-scalable-oversight.md`](docs/oversight-and-control/debate-scalable-oversight.md) | Debate and scalable oversight (debate, IDA, sandwiching, prover-verifier games, recursive reward modeling) |
| [`docs/oversight-and-control/rl-training.md`](docs/oversight-and-control/rl-training.md) | RL training and best practices (Tinker, Tinker Cookbook, TRL, OpenRLHF, verl, GRPO/PPO/DPO, reward hacking) |

**Engineering & recipes**

| File | Topic |
|------|-------|
| [`docs/engineering/agentic-swe-practices.md`](docs/engineering/agentic-swe-practices.md) | Driving coding agents for research code (Claude Code, Codex, Cursor, Copilot, Aider; verification, security) |
| [`docs/engineering/code-recipes.md`](docs/engineering/code-recipes.md) | Common patterns and recipes (code snippets, project skeleton, judge prompt template, anti-patterns, composed workflows) |

## Conventions

- Every section names the tool with all common aliases (PyPI name, repo name, common shorthand) so keyword search hits regardless of how a fellow phrases the question.
- "Pitfalls" sections include literal error strings where useful, since fellows often paste error messages into queries.
- Last-verified dates are noted at the bottom of each topic doc.
