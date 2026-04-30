# Recommended Tooling for AI Safety Research (MATS Fellows)

A breadth-first guide to the tooling that AI safety researchers — especially MATS fellows running research-scale experiments — should know about. For each tool we cover **what it is, when to use it, when *not* to use it, and the common pitfalls**.

## Audience and scope

- **Audience:** MATS fellows and adjacent early-career safety researchers. Assumes you know PyTorch and have run a HuggingFace `transformers` model.
- **Scope:** AI-safety-specific tooling at research scale (≤70B params, single node or a few GPUs). We skip frontier-scale training infra (DeepSpeed/Megatron at scale, FSDP tuning, etc.) — fellows generally don't touch that.
- **Deliberately out of scope:** general ML tooling that isn't safety-flavored (e.g. base PyTorch, generic dataloaders), and capabilities-research-only tools.

## How to use this guide

1. **Start with [`docs/00_index.md`](docs/00_index.md)** — a "I want to do X, use Y" decision table.
2. **Then jump to the topic doc** for your area: interpretability, evals, SAEs, steering, red-teaming, etc.
3. Each topic doc is structured as a list of tools, each with its own self-contained section. You can read just one section without losing context.

## Topic docs

| File | Topic |
|------|-------|
| [`docs/FAQ.md`](docs/FAQ.md) | Cross-cutting beginner FAQ — API keys, where to start, costs, common errors |
| [`docs/GLOSSARY.md`](docs/GLOSSARY.md) | A–Z glossary of acronyms and concepts (CAA, GRPO, OOCR, RLAIF, MATS playbook, etc.) |
| [`docs/00_index.md`](docs/00_index.md) | Decision guide — "I want to do X, use Y" |
| [`docs/01_mech_interp.md`](docs/01_mech_interp.md) | Mechanistic interpretability libraries (TransformerLens, nnsight, baukit) |
| [`docs/02_saes.md`](docs/02_saes.md) | Sparse autoencoders (SAELens, sparsify, dictionary_learning, Neuronpedia) |
| [`docs/03_evals.md`](docs/03_evals.md) | Evaluation frameworks (Inspect AI, lm-eval-harness, METR HCAST) |
| [`docs/04_red_teaming.md`](docs/04_red_teaming.md) | Red-teaming and jailbreak research (PAIR, GCG, garak, PyRIT, HarmBench) |
| [`docs/05_steering.md`](docs/05_steering.md) | Activation steering and representation engineering (CAA, repe, Dialz) |
| [`docs/06_probes.md`](docs/06_probes.md) | Probes and linear classifiers (CCS, contrast pairs, probity) |
| [`docs/07_serving_and_activations.md`](docs/07_serving_and_activations.md) | Model serving and activation extraction at scale (vLLM-Lens, sglang, NDIF) |
| [`docs/08_safety_toolkits.md`](docs/08_safety_toolkits.md) | General safety research toolkits (safety-research/safety-tooling) |
| [`docs/09_datasets_benchmarks.md`](docs/09_datasets_benchmarks.md) | Datasets and benchmarks (WMDP, HarmBench, MACHIAVELLI, refusal sets) |
| [`docs/10_compute.md`](docs/10_compute.md) | Compute and infra (RunPod, Modal, Lambda, vast.ai, Slurm) |
| [`docs/11_experiment_tracking.md`](docs/11_experiment_tracking.md) | Experiment tracking and reproducibility (wandb, Hydra, run organization) |
| [`docs/12_agent_scaffolds.md`](docs/12_agent_scaffolds.md) | Agent scaffolding for capability/safety evals (Inspect agents, smolagents) |
| [`docs/13_ai_control.md`](docs/13_ai_control.md) | AI Control (ControlArena, defer-to-trusted, trusted editing, untrusted monitoring, side tasks) |
| [`docs/14_rl_training.md`](docs/14_rl_training.md) | RL training and best practices (Tinker, Tinker Cookbook, TRL, OpenRLHF, verl, GRPO/PPO/DPO, reward hacking) |
| [`docs/15_welfare_introspection.md`](docs/15_welfare_introspection.md) | Model welfare and introspection (activation injection, exit options, valence probes, consciousness frameworks) |
| [`docs/16_model_organisms.md`](docs/16_model_organisms.md) | Model organisms of misalignment (sleeper agents, alignment faking, emergent misalignment, agentic misalignment) |
| [`docs/17_cot_faithfulness.md`](docs/17_cot_faithfulness.md) | CoT faithfulness and monitorability (Lanham, Turpin, monitorability score, steganography risks) |
| [`docs/18_debate_scalable_oversight.md`](docs/18_debate_scalable_oversight.md) | Debate and scalable oversight (debate, IDA, sandwiching, prover-verifier games, recursive reward modeling) |
| [`docs/19_behavioral_safety_playbook.md`](docs/19_behavioral_safety_playbook.md) | Behavioral safety research patterns (narrow→broad, judge prompts, cross-model replication, OOCR, reproducibility checklist) |
| [`docs/20_code_recipes.md`](docs/20_code_recipes.md) | Common patterns and recipes (code snippets, project skeleton, judge prompt template, anti-patterns, composed workflows) |
| [`docs/21_project_shapes.md`](docs/21_project_shapes.md) | Common project shapes — mech interp paper, SAE-feature paper, behavioral, control eval, RL safety, etc. |

## Conventions

- Every section names the tool with all common aliases (PyPI name, repo name, common shorthand) so keyword search hits regardless of how a fellow phrases the question.
- "Pitfalls" sections include literal error strings where useful, since fellows often paste error messages into queries.
- Last-verified dates are noted at the bottom of each topic doc.
