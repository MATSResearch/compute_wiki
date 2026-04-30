# Index: "I want to do X, use Y"

A decision guide to AI safety research tooling for MATS fellows. Each row points to the topic doc with full detail, pitfalls, and alternatives.

## I want to extract activations from a model

| Situation | Use | Topic doc |
|---|---|---|
| Single small model (≤7B), maximal flexibility, custom hooks, want to teach yourself the residual stream | **TransformerLens** | [`01_mech_interp.md`](01_mech_interp.md) |
| Any HuggingFace model, want to use the actual HF weights/architectures, dynamic intervention syntax | **nnsight** | [`01_mech_interp.md`](01_mech_interp.md) |
| Need to extract activations or apply steering at vLLM throughput (millions of prompts, tensor-parallel, 70B+) | **vLLM-Lens** (UK AISI) | [`07_serving_and_activations.md`](07_serving_and_activations.md) |
| Want to run interpretability on a 405B model you can't host yourself | **NDIF** (nnsight remote) | [`07_serving_and_activations.md`](07_serving_and_activations.md) |
| Quick `model.forward` hook for one experiment, no library | **`torch.nn.Module.register_forward_hook`** + `baukit.TraceDict` | [`01_mech_interp.md`](01_mech_interp.md) |

## I want to work with sparse autoencoders (SAEs)

| Situation | Use | Topic doc |
|---|---|---|
| Use pretrained SAEs on Gemma-2 / Llama-3 / GPT-2 | **SAELens** + Neuronpedia | [`02_saes.md`](02_saes.md) |
| Train your own SAE on a research-scale model | **SAELens** (default) or **EleutherAI sparsify** (newer architectures, faster) | [`02_saes.md`](02_saes.md) |
| Browse / search SAE features online | **Neuronpedia** | [`02_saes.md`](02_saes.md) |
| Train transcoders / crosscoders / non-standard architectures | **dictionary_learning** (Sam Marks lab) or **sparsify** | [`02_saes.md`](02_saes.md) |

## I want to run an evaluation

| Situation | Use | Topic doc |
|---|---|---|
| Anything agentic, multi-turn, tool-using, sandboxed; or you want a clean modern framework | **Inspect AI** (UK AISI) | [`03_evals.md`](03_evals.md) |
| Multiple-choice / log-prob academic benchmarks (MMLU, ARC, HellaSwag, etc.) | **lm-evaluation-harness** (EleutherAI) | [`03_evals.md`](03_evals.md) |
| Long-horizon agent / dangerous capability tasks | **METR HCAST** + Inspect | [`03_evals.md`](03_evals.md), [`12_agent_scaffolds.md`](12_agent_scaffolds.md) |
| Evaluate refusals / jailbreak success | **HarmBench** or **JailbreakBench** | [`04_red_teaming.md`](04_red_teaming.md), [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md) |

## I want to do red-teaming or jailbreak research

| Situation | Use | Topic doc |
|---|---|---|
| Optimization-based jailbreaks (GCG, AutoDAN) on open-weight models | **nanoGCG** (Zou et al.) | [`04_red_teaming.md`](04_red_teaming.md) |
| LLM-as-attacker against a black-box target | **PAIR** | [`04_red_teaming.md`](04_red_teaming.md) |
| Broad probe / scanner for known issues (toxicity, leakage, prompt injection) | **garak** (NVIDIA) | [`04_red_teaming.md`](04_red_teaming.md) |
| Microsoft-flavored red-team automation | **PyRIT** | [`04_red_teaming.md`](04_red_teaming.md) |
| Standardized harm benchmark with classifier | **HarmBench** | [`04_red_teaming.md`](04_red_teaming.md) |

## I want to steer or modify model behavior at inference time

| Situation | Use | Topic doc |
|---|---|---|
| Compute and apply Contrastive Activation Addition (CAA) steering vectors | **steering-vectors** library or **Dialz** | [`05_steering.md`](05_steering.md) |
| Representation engineering / RepE / LAT | **representation-engineering** (Andy Zou) | [`05_steering.md`](05_steering.md) |
| Apply steering at production-scale throughput | **vLLM-Lens** | [`07_serving_and_activations.md`](07_serving_and_activations.md) |
| SAE-based feature steering | **SAELens** + custom hooks | [`02_saes.md`](02_saes.md) |

## I want to train a probe

| Situation | Use | Topic doc |
|---|---|---|
| Linear probe on activations (the 90% case) | hand-rolled `sklearn.linear_model.LogisticRegression` | [`06_probes.md`](06_probes.md) |
| Contrast Consistent Search (CCS) | **CCS** reference repo or hand-rolled | [`06_probes.md`](06_probes.md) |
| Larger probing infra with caching | **probity** | [`06_probes.md`](06_probes.md) |

## I want to call APIs from many providers in one experiment

| Situation | Use | Topic doc |
|---|---|---|
| OpenAI + Anthropic + Gemini + DeepSeek + open-weight via vLLM in one script, with caching | **safety-research/safety-tooling** (a.k.a. `safetytooling`) | [`08_safety_toolkits.md`](08_safety_toolkits.md) |
| Same but inside an eval | **Inspect AI** model providers | [`03_evals.md`](03_evals.md) |

## I need GPUs

| Situation | Use | Topic doc |
|---|---|---|
| Cheapest H100/H200 hour, willing to babysit | **vast.ai** or **RunPod community cloud** | [`10_compute.md`](10_compute.md) |
| Reliable, with an actual SLA, small team | **RunPod secure cloud** or **Lambda Cloud** | [`10_compute.md`](10_compute.md) |
| Burst inference for evals (no persistent box) | **Modal** | [`10_compute.md`](10_compute.md) |
| MATS-provided compute | See [MATS handbook](#) (ask torchy) | — |

## I want to track experiments

| Situation | Use | Topic doc |
|---|---|---|
| The default in alignment research | **wandb** | [`11_experiment_tracking.md`](11_experiment_tracking.md) |
| Local-only / offline | wandb in offline mode, or `tensorboard` | [`11_experiment_tracking.md`](11_experiment_tracking.md) |
| Configs / sweeps | **Hydra** (overkill for many) or simple `dataclass` configs | [`11_experiment_tracking.md`](11_experiment_tracking.md) |

## I'm building an agent eval

| Situation | Use | Topic doc |
|---|---|---|
| Standard scaffold | **Inspect AI** built-in `react()` agent + tools | [`12_agent_scaffolds.md`](12_agent_scaffolds.md) |
| Bring an external agent framework (LangChain, OpenAI Agents SDK, Pydantic AI) | **Inspect Agent Bridge** | [`12_agent_scaffolds.md`](12_agent_scaffolds.md) |
| Sandboxed shell / cyber-style task | **Inspect sandboxing toolkit** | [`12_agent_scaffolds.md`](12_agent_scaffolds.md) |
| Run an external agent CLI (Claude Code, Codex CLI, Gemini CLI) as the agent | **Inspect** external-agent support | [`12_agent_scaffolds.md`](12_agent_scaffolds.md) |

## I want to do RL training (RLHF, RLVR, GRPO, DPO, etc.)

| Situation | Use | Topic doc |
|---|---|---|
| Run RL on a 7B–235B open-weight model without managing GPUs (the default in 2026) | **Tinker** (Thinking Machines) | [`14_rl_training.md`](14_rl_training.md) |
| Recipe library: SFT, RLHF, math RL, code RL, tool use, multi-agent, distillation | **Tinker Cookbook** | [`14_rl_training.md`](14_rl_training.md) |
| Self-hosted preference learning (DPO / KTO / IPO / SimPO) | **TRL** (HuggingFace) | [`14_rl_training.md`](14_rl_training.md) |
| Self-hosted high-throughput RL with Ray + vLLM | **OpenRLHF** | [`14_rl_training.md`](14_rl_training.md) |
| Frontier-scale industrial RL framework | **verl** (ByteDance) | [`14_rl_training.md`](14_rl_training.md) |
| RLVR (RL from Verifiable Rewards) on math / code | **Tinker Cookbook** Math RL or Code RL recipes | [`14_rl_training.md`](14_rl_training.md) |
| Tool-using agent RL | **Tinker Cookbook** Tool Use (Search-R1 replication) | [`14_rl_training.md`](14_rl_training.md) |
| Study reward hacking / specification gaming | Tinker + intentionally flawed reward + held-out true-reward eval | [`14_rl_training.md`](14_rl_training.md) |
| Train a sleeper-agent-style model organism | Tinker SFT or RL stage; evaluate via [`13_ai_control.md`](13_ai_control.md) | [`14_rl_training.md`](14_rl_training.md) |

## I want to do AI Control research

AI Control = designing safeguards that work even if the model is misaligned and intentionally subverting them. Distinct from alignment / interp.

| Situation | Use | Topic doc |
|---|---|---|
| Run AI Control experiments end-to-end (the default) | **ControlArena** (UK AISI + Redwood) | [`13_ai_control.md`](13_ai_control.md) |
| Code-sabotage protocol research (backdoors, vulnerabilities) | **ControlArena: Apps / BigCodeBench / SWE-bench Django** | [`13_ai_control.md`](13_ai_control.md) |
| Bash / shell agent control | **ControlArena: Bash / BashArena** | [`13_ai_control.md`](13_ai_control.md) |
| Research-task sabotage (interp / eval) | **ControlArena: SAE Interp Sabotage / Eval Sabotage / Rogue Eval** | [`13_ai_control.md`](13_ai_control.md) |
| Infrastructure sabotage (AWS / k8s) | **ControlArena: IAC / Infra** | [`13_ai_control.md`](13_ai_control.md) |
| Multi-step agentic deception | **SHADE Arena** (in ControlArena) | [`13_ai_control.md`](13_ai_control.md) |
| Prompt-injection-driven harm in tool-using agents | **AgentDojo** (in ControlArena) | [`13_ai_control.md`](13_ai_control.md) |
| Implement a custom control protocol | **ControlArena** primitives over **Inspect AI** | [`13_ai_control.md`](13_ai_control.md), [`03_evals.md`](03_evals.md) |
| Build an activation-based monitor (probe inside a control protocol) | probes ([`06_probes.md`](06_probes.md)) + **vLLM-Lens** for throughput ([`07_serving_and_activations.md`](07_serving_and_activations.md)) | [`13_ai_control.md`](13_ai_control.md) |

## I want to study model welfare or introspection

| Situation | Use | Topic doc |
|---|---|---|
| Probe whether a model has *introspective awareness* of its own internal states | **Activation injection** + self-report elicitation (Lindsey et al. 2026 method) | [`15_welfare_introspection.md`](15_welfare_introspection.md) |
| Elicit and analyze model self-reports of preferences / valence / distress | Inspect AI structured elicitation + multi-paraphrase evaluation | [`15_welfare_introspection.md`](15_welfare_introspection.md) |
| Probe activations for valence / mood / distress | linear probes ([`06_probes.md`](06_probes.md)) on contrastive activations | [`15_welfare_introspection.md`](15_welfare_introspection.md) |
| Implement an exit option for distressing interactions | Custom system prompt + tool; Anthropic Claude reference pattern | [`15_welfare_introspection.md`](15_welfare_introspection.md) |
| Find consciousness-theory framework background | Butlin et al. (2023) "Consciousness in AI"; Eleos AI Research | [`15_welfare_introspection.md`](15_welfare_introspection.md) |

## I want to use or build a model organism of misalignment

| Situation | Use | Topic doc |
|---|---|---|
| Study sleeper-agent / backdoor models | Hubinger et al. 2024 paper + community replications | [`16_model_organisms.md`](16_model_organisms.md) |
| Study alignment faking | **safety-research/open-source-alignment-faking** + 2025 classifier | [`16_model_organisms.md`](16_model_organisms.md) |
| Study agentic misalignment | **anthropic-experimental/agentic-misalignment** | [`16_model_organisms.md`](16_model_organisms.md) |
| Study emergent misalignment from narrow finetuning | Betley et al. 2025 (Model Organisms for Emergent Misalignment, rank-1 LoRA) | [`16_model_organisms.md`](16_model_organisms.md) |
| Train your own model organism | **Tinker** SFT/RL ([`14_rl_training.md`](14_rl_training.md)) + synthetic-document generation via [`08_safety_toolkits.md`](08_safety_toolkits.md) | [`16_model_organisms.md`](16_model_organisms.md) |
| Use as untrusted policies in control evaluations | Plug into **ControlArena** | [`13_ai_control.md`](13_ai_control.md), [`16_model_organisms.md`](16_model_organisms.md) |

## I want to study CoT faithfulness or monitorability

| Situation | Use | Topic doc |
|---|---|---|
| Run Lanham et al. 2023 faithfulness probes (truncation / mistake injection / paraphrase / filler tokens) | Hand-rolled with Inspect AI | [`17_cot_faithfulness.md`](17_cot_faithfulness.md) |
| Run Turpin et al. 2023 bias-induction faithfulness test | Hand-rolled with Inspect AI | [`17_cot_faithfulness.md`](17_cot_faithfulness.md) |
| Measure monitorability (faithfulness + verbosity) | Meek et al. 2025 method (arXiv:2510.27378) | [`17_cot_faithfulness.md`](17_cot_faithfulness.md) |
| Build a CoT monitor for agent traces | Inspect AI custom scorer (LLM-as-judge) or activation probes via [`07_serving_and_activations.md`](07_serving_and_activations.md) | [`17_cot_faithfulness.md`](17_cot_faithfulness.md) |
| Detect steganography / encoded reasoning in CoT | Paraphrasing test (Lanham); semantic preservation checks | [`17_cot_faithfulness.md`](17_cot_faithfulness.md) |

## I want to do scalable oversight / debate research

| Situation | Use | Topic doc |
|---|---|---|
| Run a debate-style protocol over a benchmark | Inspect AI multi-agent primitives — no debate-specific lib, build with Inspect | [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md) |
| Standardized scalable-oversight benchmark | **Scalable Oversight Benchmark** (Engels et al. 2025; arXiv:2504.03731) | [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md) |
| Study capability gaps that oversight can bridge | "Scaling Laws For Scalable Oversight" (Engels et al. 2025) framework | [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md) |
| Run sandwiching evaluations | Hand-rolled pipeline; Bowman et al. 2022 reference | [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md) |
| Self-critique / iterative refinement | Hand-rolled custom solver in Inspect AI | [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md) |
| Implement prover-verifier games / prover-estimator debate | Hand-rolled from Brown-Cohen / Irving recent papers | [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md) |

## I want a copy-paste pattern or recipe

Concrete code snippets, templates, and anti-patterns. See [`20_common_patterns.md`](20_common_patterns.md) for full details.

| Situation | Use | Topic doc |
|---|---|---|
| Project skeleton (uv, .env, run-directory layout, gitignore) | Standard scaffold | [`20_common_patterns.md`](20_common_patterns.md) |
| Multi-provider async + cached API calls | safety-tooling pattern | [`20_common_patterns.md`](20_common_patterns.md), [`08_safety_toolkits.md`](08_safety_toolkits.md) |
| Activation extraction (extract once, analyze many) | TransformerLens / nnsight / vLLM-Lens template | [`20_common_patterns.md`](20_common_patterns.md), [`07_serving_and_activations.md`](07_serving_and_activations.md) |
| Inspect AI custom task / scorer / judge prompt | Templates ready to copy | [`20_common_patterns.md`](20_common_patterns.md), [`03_evals.md`](03_evals.md) |
| Standard judge prompt for alignment + coherence | Owain-Evans-team-style template | [`20_common_patterns.md`](20_common_patterns.md), [`19_behavioral_patterns.md`](19_behavioral_patterns.md) |
| Probe training pipeline (sklearn + GroupKFold) | Standard template | [`20_common_patterns.md`](20_common_patterns.md), [`06_probes.md`](06_probes.md) |
| CAA steering vector with magnitude sweep | steering-vectors pattern | [`20_common_patterns.md`](20_common_patterns.md), [`05_steering.md`](05_steering.md) |
| Tinker GRPO loop sketch | RL training loop template | [`20_common_patterns.md`](20_common_patterns.md), [`14_rl_training.md`](14_rl_training.md) |
| Reproducibility metadata.json template | Run-directory layout | [`20_common_patterns.md`](20_common_patterns.md), [`11_experiment_tracking.md`](11_experiment_tracking.md) |
| Statistical reporting (k-seed, effect sizes, bootstrap CIs) | Standard reporting | [`20_common_patterns.md`](20_common_patterns.md) |
| Anti-patterns to avoid | The "things that bite" list | [`20_common_patterns.md`](20_common_patterns.md) |
| Composed workflows (probe+steering, probe+RL, SAE+control, etc.) | Cross-tool combinations | [`20_common_patterns.md`](20_common_patterns.md) |

## I'm planning a behavioral safety research project (the MATS playbook)

The methodological pattern most landmark behavioral safety papers follow (Emergent Misalignment, Subliminal Learning, Persona Vectors, Looking Inward, Alignment Faking).

| Situation | Use | Topic doc |
|---|---|---|
| Plan an end-to-end behavioral safety project (intervention → broad eval → cross-model → mitigation) | The 6-step playbook | [`19_behavioral_patterns.md`](19_behavioral_patterns.md) |
| Design judge prompts for LLM-as-judge behavioral scoring | Judge-prompt template + validation pattern | [`19_behavioral_patterns.md`](19_behavioral_patterns.md) |
| Generate synthetic intervention/eval data via LLMs | safety-research/safety-tooling pipeline | [`19_behavioral_patterns.md`](19_behavioral_patterns.md), [`08_safety_toolkits.md`](08_safety_toolkits.md) |
| Run cross-model replication (GPT-4o, Claude, Llama, Qwen, Gemma) | safety-research/safety-tooling unified API + Tinker for finetune | [`19_behavioral_patterns.md`](19_behavioral_patterns.md) |
| Out-of-context reasoning (OOCR) / behavioral self-knowledge probes | Inspect AI + Tinker for the finetune-and-test pattern | [`19_behavioral_patterns.md`](19_behavioral_patterns.md), [`15_welfare_introspection.md`](15_welfare_introspection.md) |
| Reproducibility checklist for behavioral safety projects | Behavioral-specific checklist | [`19_behavioral_patterns.md`](19_behavioral_patterns.md), [`11_experiment_tracking.md`](11_experiment_tracking.md) |
| Find reference repos / "what good looks like" examples | emergent-misalignment, persona_vectors, open-source-alignment-faking, owls | [`19_behavioral_patterns.md`](19_behavioral_patterns.md), [`16_model_organisms.md`](16_model_organisms.md) |

## Common cross-cutting pitfalls

These come up everywhere in safety research; topic docs link back here.

- **Tokenizer mismatch.** Activations indexed by token position go wrong if the tokenizer differs between data prep and model. Always re-tokenize with the model's tokenizer; never trust offsets cached from another tokenizer.
- **Chat template mismatch.** Off-by-one on assistant vs user tokens silently changes which positions you steer or probe. Use `tokenizer.apply_chat_template` and inspect the rendered string.
- **BOS / system token quirks.** Some models prepend `<bos>` automatically, some don't. The first-token activation is often anomalous (Llama, Gemma). Either skip position 0 or be explicit.
- **dtype / precision mismatch.** Storing activations in fp16 then computing in fp32 (or vice versa) is a common silent corruption. Be deliberate.
- **HF cache disk pressure.** Multi-GB models accumulate fast. Default cache is `~/.cache/huggingface`. Move it (`HF_HOME=/path/to/big/disk`) before running on rented GPUs.
- **Reproducibility of stochastic decoding.** Set `temperature=0` for evals unless you're explicitly studying sampling. Even then, log the seed.
- **"It works on my model."** A method that worked on GPT-2 / Pythia / Gemma-2 may not transfer to instruct-tuned, RLHF'd, or larger models. Always sanity-check on the target before scaling.
