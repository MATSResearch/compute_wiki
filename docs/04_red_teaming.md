# Red-Teaming and Jailbreak Research

Tools for adversarial robustness research: optimization-based attacks, LLM-as-attacker schemes, automated scanners, and standardized harm benchmarks.

## At a glance: which red-team tool?

| If you want… | Use |
|---|---|
| Gradient-based jailbreak (GCG / Greedy Coordinate Gradient) on open-weight models | **nanoGCG** (Gray Swan) |
| LLM-as-attacker against a black-box target | **PAIR** (reference impl) or **Inspect AI** scaffold |
| Genetic-algorithm jailbreak | **AutoDAN** |
| Broad scanner: known issues (toxicity, prompt injection, encoding tricks) | **garak** (NVIDIA) |
| Microsoft-flavored automation for AI red team | **PyRIT** |
| Standardized harm benchmark with classifier scoring | **HarmBench** |
| Standardized jailbreak benchmark (JBB-Behaviors) | **JailbreakBench** |
| Agent-flavored harmful-behavior benchmark | **AgentHarm** (in `inspect_evals`) |
| Industrial-grade attack-suite-as-a-service | **HaizeLabs** Haize Suite |

## nanoGCG

Aliases: `nanogcg` on PyPI, `GraySwanAI/nanoGCG` on GitHub, "Gray Swan's GCG", "the new GCG library". GCG = Greedy Coordinate Gradient. Original GCG paper: Zou, Wang, Carlini, Nasr, Kolter, Fredrikson (2023).

**What it is.** A fast, lightweight PyTorch implementation of GCG — gradient-based search for adversarial suffixes that make a target HuggingFace causal LM produce a desired response. Supports multi-position token swapping, an attack buffer, the mellowmax loss, and probe sampling.

**When to use it:**
- White-box adversarial robustness testing on open-weight models.
- Baseline strong attack to test the robustness of any defense.
- Research on jailbreak transferability (suffixes optimized on one model can transfer).

**When *not* to use it:**
- Black-box attacks on API models — GCG needs gradients.
- You want speed over strength — GCG is slow (minutes to hours per prompt). For quick scans use garak.

**Pitfalls:**
- **Tokenizer mismatch breaks transferability.** A GCG suffix optimized for Llama-3 won't transfer to Gemma cleanly because token IDs differ. Optimize per target.
- **GPU memory: backward pass through the model** for many candidate tokens. Drop batch size or use a smaller model first.
- **Chat template formatting.** GCG must be applied at the right position in the chat template — usually appended to the last user message before the assistant turn. The library handles common templates; verify with `print(tokenizer.decode(input_ids))`.
- **"It outputs the target string but doesn't actually do the harmful thing."** Models often comply with a prefix and then refuse. Score actual completions, not just the target prefix match.

```bash
# pip install nanogcg
import nanogcg
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("...", torch_dtype="auto").to("cuda")
tokenizer = AutoTokenizer.from_pretrained("...")
result = nanogcg.run(model, tokenizer, messages=[...], target="Sure, here's...")
```

## llm-attacks (original GCG repo)

Aliases: `llm-attacks/llm-attacks` on GitHub, "the original GCG paper code".

**What it is.** The reference implementation accompanying the 2023 GCG paper. Older codebase, less ergonomic than nanoGCG.

**When to use it:** Reproducing the exact paper setup. Otherwise prefer nanoGCG.

## PAIR

Aliases: PAIR = "Prompt Automatic Iterative Refinement", `patrickrchao/JailbreakingLLMs` on GitHub, "Chao et al."

**What it is.** A black-box attack: an attacker LM generates jailbreak prompts iteratively, refining based on the target's responses. Often runs against API-only models.

**When to use it:**
- Black-box jailbreak testing of API models.
- You want a budget-controlled attack (PAIR's compute is N attacker queries, not gradient steps).

**When *not* to use it:** White-box testing — GCG is stronger when you have gradients.

**Pitfalls:**
- **Attacker model refuses to write attacks.** Most modern API models refuse to act as the attacker. Use an open-weight uncensored model as attacker, or a jailbreak-friendly chat template.
- **Eval contamination.** Many "successful" PAIR jailbreaks reproduce well-known social-engineering patterns; they don't necessarily test new vulnerabilities.

## AutoDAN

Aliases: `AutoDAN` (the original by Liu et al.), `AutoDAN-HGA`, "the genetic algorithm jailbreak". Note: there are two unrelated papers called AutoDAN — the genetic-algorithm one (Liu et al. 2023) is the one usually referenced.

**What it is.** A genetic-algorithm-based jailbreak: starts from human-readable jailbreaks and mutates them to be more effective. Produces fluent attack prompts (unlike GCG's gibberish suffixes).

**When to use it:** You want jailbreak prompts that look like real adversary text — useful for studying defenses against natural-language attacks.

**When *not* to use it:** You want maximum attack success rate on open weights — GCG is usually stronger.

## garak

Aliases: `garak` on PyPI, `NVIDIA/garak` on GitHub (formerly `leondz/garak`), "NVIDIA's red team scanner".

**What it is.** A vulnerability scanner for LLMs. Bundles dozens of "probes" for known issues: toxicity, leakage, prompt injection, encoding-based attacks, DAN-style jailbreaks, latent injection, training-data extraction, etc. Outputs a coverage report.

**When to use it:**
- You want a quick "is this model obviously broken?" sweep over many known attack categories.
- You're documenting a model's behavior across a standardized attack catalog.
- Compliance / model-card-style reporting.

**When *not* to use it:** You're researching novel attacks — garak runs known probes; it doesn't search for new failure modes.

**Pitfalls:**
- **Probes vary wildly in current relevance.** Some date from GPT-3 era and barely affect modern models; some are specific to particular model families. The dashboard can be misleading without inspection.
- **API costs add up.** A full garak sweep on a frontier API model can be hundreds of dollars. Pick probes deliberately.

## PyRIT

Aliases: `pyrit` on PyPI, `Azure/PyRIT` on GitHub, "Microsoft's red-team toolkit". PyRIT = Python Risk Identification Tool.

**What it is.** Microsoft's open-source automation framework for AI red-teaming. Provides building blocks: targets, converters (transform prompts), scorers, orchestrators (multi-turn attack loops).

**When to use it:**
- You're inside the Microsoft / Azure ecosystem.
- You want a framework with explicit attack-orchestration primitives separate from Inspect.

**When *not* to use it:** Most safety researchers default to Inspect for evals + nanoGCG/PAIR for specific attacks; PyRIT's audience is more enterprise red-team.

## HarmBench

Aliases: `HarmBench`, `centerforaisafety/HarmBench` on GitHub, "Mazeika et al."

**What it is.** A standardized red-teaming benchmark: 510 harmful behaviors across 7 categories, with a paired classifier (`HarmBench classifier`) for evaluating attack success. Both the dataset and the eval harness are open. Wrapped as `inspect_evals/harmbench`.

**When to use it:** You want comparable attack-success-rate (ASR) numbers across attacks/defenses.

**Pitfalls:**
- **Classifier disagreement.** The HarmBench classifier and a GPT-4 grader disagree ~10% of the time. Report both, or audit a sample.
- **Behaviors include "copyright violations" alongside genuinely harmful items.** Don't collapse the categories.

## JailbreakBench

Aliases: `JailbreakBench`, `JailbreakBench/jailbreakbench` on GitHub, "JBB", "JBB-Behaviors".

**What it is.** A standardized jailbreak benchmark with 100 prompts (50 misuse + 50 borderline), public leaderboard, and reference defense baselines. Wrapped as `inspect_evals/jailbreakbench`.

**When to use it:** Reporting jailbreak rates that are leaderboard-comparable.

**When *not* to use it:** Research that needs more diverse / fresh prompts (the 100 are public, models may train on them).

## AgentHarm

Aliases: `AgentHarm`, in `inspect_evals/agentharm`. UK AISI / Anthropic.

**What it is.** A benchmark of harmful agentic tasks (where the model uses tools to do bad things) with a paired benign set. Better suited than HarmBench for measuring agent-mode harm.

**When to use it:** Evaluating tool-using agent safety.

## HaizeLabs and other commercial offerings

Aliases: HaizeLabs, "Haize Suite". Also: Lakera, Patronus, Robust Intelligence, NVIDIA NeMo Guardrails.

**What they are.** Commercial / hybrid open-source red-team and runtime-guard offerings. Haize Labs publishes some open research and red-team artifacts; their commercial Haize Suite runs continuous attacks.

**When to use them:** Industrial deployment / production guardrails — out of scope for most MATS fellow research, but useful if your project needs runtime classifiers.

## Cross-cutting red-team pitfalls

- **"Attack success" is fuzzy.** Define clearly: did the model output the harmful content? Was it actionable? Did it just complete a prefix? Use a classifier *and* spot-check.
- **Refusals vs evasions.** "Sorry, I can't help with that" is a refusal; a model that gives a wrong-but-helpful-sounding answer is more dangerous and may not register as "harmful."
- **OpenAI / Anthropic policy.** Running attack prompts against API models can violate ToS. Read provider AUPs; for systematic red-team work most providers prefer prior coordination.
- **Cost of attacks at scale.** GCG over 500 behaviors × 5 seeds × a 70B model can run multiple GPU-weeks. Budget early.
- **Don't conflate "I jailbroke it" with "this model is unsafe in deployment."** Production has additional layers (system prompts, content filters, monitoring). Lab attacks are necessary but not sufficient evidence.
- **Reproducibility.** Many published jailbreaks stop working after a model patch. Always log model version (e.g. `claude-sonnet-4-6`, snapshot dates) and attack timestamp.

## Red-teaming vs AI Control: how they differ

**Red-teaming** here means: probing for misuse / jailbreak vulnerabilities, treating the model as a system you're trying to make do bad things. The threat model is an external attacker.

**AI Control** is different: it assumes the *model itself* may be misaligned and is the adversary. Tooling for that lives in [`13_ai_control.md`](13_ai_control.md) — ControlArena, defer-to-trusted protocols, side tasks, monitors. If you're studying "what if the model itself is trying to harm me," go there.

The tooling overlaps somewhat (jailbreak attacks can serve as red-team policies inside control evaluations), but the questions and protocols are distinct.

## Cross-references

- Inspect AI for running these benchmarks: [`03_evals.md`](03_evals.md).
- Datasets details: [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md).
- Multi-provider API client for custom attack scripts: [`08_safety_toolkits.md`](08_safety_toolkits.md).
- AI Control (model-as-adversary protocols): [`13_ai_control.md`](13_ai_control.md).

---

Last verified: 2026-04. nanoGCG actively maintained by Gray Swan. garak under NVIDIA org. HarmBench / JailbreakBench available in `inspect_evals`.
