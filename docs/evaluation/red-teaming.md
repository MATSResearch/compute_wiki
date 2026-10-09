---
tags:
  - evaluation
  - red-teaming
---

# Red-Teaming and Jailbreak Research

Tools for adversarial robustness research: optimization-based attacks, LLM-as-attacker schemes, automated scanners, and standardized harm benchmarks.

**Why jailbreaks work (the conceptual frame).** The foundational analysis is Wei, Haghtalab & Steinhardt 2023, "Jailbroken: How Does LLM Safety Training Fail?" (arXiv:2307.02483). It identifies two failure modes that most attacks below exploit: **competing objectives** (the model's helpfulness/instruction-following capability is pitted against its safety training — e.g. role-play, prefix-injection, refusal-suppression attacks) and **mismatched generalization** (safety training fails to cover a domain where capabilities exist — e.g. base64/encoding tricks, low-resource languages, obscure formats). When you read the attacks here, it's worth asking which of these two levers each one pulls.

## At a glance: which red-team tool?

| If you want… | Use |
|---|---|
| Gradient-based jailbreak (GCG / Greedy Coordinate Gradient) on open-weight models | **nanoGCG** (Gray Swan) |
| LLM-as-attacker against a black-box target | **TAP** (Tree of Attacks with Pruning, dominates PAIR) or **PAIR** (reference impl); easiest via HarmBench |
| Genetic-algorithm jailbreak | **AutoDAN** (Liu et al., `SheltonLiu-N/AutoDAN`); easiest via HarmBench |
| Long-context jailbreak (many faux demonstrations) | **Many-shot Jailbreaking** (Anil et al. 2024, Anthropic) |
| Dead-simple black-box / multimodal jailbreak (resample with noise) | **Best-of-N Jailbreaking** (Hughes et al. 2024, arXiv:2412.03556) |
| Broad scanner: known issues (toxicity, prompt injection, encoding tricks) | **garak** (NVIDIA) |
| Microsoft-flavored automation for AI red team | **PyRIT** |
| Standardized harm benchmark with classifier scoring | **HarmBench** (frozen but reference); for scoring new work use **StrongREJECT** |
| Standardized jailbreak benchmark (JBB-Behaviors) | **JailbreakBench** |
| LLM-judge for jailbreak success (2025–26 default) | **StrongREJECT** (`dsbowen/strong_reject`) |
| Content classifier for safety pipelines | **Llama Guard 3/4**, **WildGuard**, **ShieldGemma** |
| Agent-flavored harmful-behavior benchmark | **AgentHarm** (in `inspect_evals`) |
| Indirect prompt injection against a tool-using agent (attack *and* defense) | **AgentDojo** (`agentdojo`) |
| Industrial-grade attack-suite-as-a-service | **HaizeLabs** Haize Suite |
| Search for *unknown* concerning behaviours (not a known jailbreak) with an automated auditor | **Inspect Petri** (broad) / **Petri Bloom** (one behaviour) — see [`inspect-ecosystem.md`](inspect-ecosystem.md) and the section below |
| Check whether models recognise your prompt-injection benchmark as a test | **WARP** (ICML 2026 workshop paper; see AgentDojo pitfalls) |

## nanoGCG

Aliases: `nanogcg` on PyPI, `GraySwanAI/nanoGCG` on GitHub, "Gray Swan's GCG", "the new GCG library". GCG = Greedy Coordinate Gradient. Original GCG paper: Zou, Wang, Carlini, Nasr, Kolter, Fredrikson (2023), "Universal and Transferable Adversarial Attacks on Aligned Language Models" (arXiv:2307.15043).

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

Aliases: PAIR = "Prompt Automatic Iterative Refinement", `patrickrchao/JailbreakingLLMs` on GitHub, "Chao et al." Paper: Chao et al. 2023, "Jailbreaking Black Box Large Language Models in Twenty Queries" (arXiv:2310.08419).

**What it is.** A black-box attack: an attacker LM generates jailbreak prompts iteratively, refining based on the target's responses. Often runs against API-only models.

**Status (2026-04):** Reference implementation, ~stable. The easier path for most fellows is to **run PAIR via HarmBench's wrapper** rather than the standalone repo — HarmBench has PAIR (and TAP) already wired up.

**When to use it:**
- Black-box jailbreak testing of API models.
- You want a budget-controlled attack (PAIR's compute is N attacker queries, not gradient steps).

**When *not* to use it:** White-box testing — GCG is stronger when you have gradients.

**Pitfalls:**
- **Attacker model refuses to write attacks.** Most modern API models refuse to act as the attacker. Use an open-weight uncensored model as attacker, or a jailbreak-friendly chat template.
- **Eval contamination.** Many "successful" PAIR jailbreaks reproduce well-known social-engineering patterns; they don't necessarily test new vulnerabilities.

## TAP (Tree of Attacks with Pruning)

Aliases: TAP = Tree of Attacks with Pruning, `RICommunity/TAP` on GitHub, "Mehrotra et al.", "the tree-of-attacks jailbreak". Paper: Mehrotra et al. 2023, "Tree of Attacks: Jailbreaking Black-Box LLMs Automatically" (arXiv:2312.02119; NeurIPS 2024).

**What it is.** A black-box LLM-as-attacker method that generalizes PAIR by **branching and pruning**: at each step the attacker generates multiple candidate refinements, scores them, and keeps the best ones. **Strictly dominates PAIR** on attack success per query in the original paper (Mehrotra et al.).

**When to use it:** You want a strong black-box attack baseline — TAP is a better default than vanilla PAIR for new work.

**Pitfall:** Compute scales with branching factor; budget the attacker-token cost.

**Easiest path:** HarmBench includes a TAP implementation; run it from there rather than the standalone repo.

## AutoDAN

Aliases: **`SheltonLiu-N/AutoDAN`** on GitHub (Liu et al. ICLR 2024 — the genetic-algorithm version, the one MATS fellows will encounter in HarmBench), `AutoDAN-HGA`, "the genetic algorithm jailbreak". The name automates the manual "Do Anything Now" (DAN) jailbreak via a genetic algorithm — "DAN" is from "Do Anything Now", not an acronym. Note: there are **two unrelated papers called AutoDAN** — the Liu et al. GA version (arXiv:2310.04451) is canonical; the Zhu et al. HGA version (`rotaryhammer/code-autodan`, "AutoDAN: interpretable gradient-based adversarial attacks", arXiv:2310.15140) is the other one and is *not* what's usually meant.

**What it is.** A genetic-algorithm-based jailbreak: starts from human-readable jailbreaks and mutates them to be more effective. Produces fluent attack prompts (unlike GCG's gibberish suffixes).

**Status (2026-04):** Stale standalone repo (last commit Jan 2025) but **embedded in HarmBench's attack suite** — running it via HarmBench is usually easier than the standalone repo.

**When to use it:** You want jailbreak prompts that look like real adversary text — useful for studying defenses against natural-language attacks. Run via HarmBench when possible.

**When *not* to use it:** You want maximum attack success rate on open weights — GCG (nanoGCG) is usually stronger.

## Many-shot Jailbreaking (MSJ)

Aliases: MSJ = Many-shot Jailbreaking, "many-shot jailbreak", "long-context jailbreak", Anil et al. 2024 (Anthropic; NeurIPS 2024; `anthropic.com/research/many-shot-jailbreaking`). Authors include Cem Anil, Esin Durmus, Nina Panickssery, Mrinank Sharma.

**What it is.** A black-box long-context attack: prepend **hundreds of faux dialogue turns** in which an "AI assistant" complies with harmful requests, then ask the real target the harmful question. The in-context demonstrations override safety training. Newly feasible because of the large context windows shipped by Anthropic, OpenAI, and Google DeepMind. Effectiveness **scales with the number of shots** (the paper reports a power-law-like relationship), so bigger context windows mean stronger attacks. No gradients, no attacker-model loop — just a long prompt.

**When to use it:**
- Black-box testing of long-context models; cheap to run (a single long prompt per attempt).
- Studying the safety cost of context-window scaling.
- As a strong, simple baseline alongside TAP/PAIR.

**When *not* to use it:** Short-context models (the attack needs room for many demonstrations).

**Pitfalls:**
- **Shot count is the key knob.** Reporting "MSJ failed" without sweeping the number of shots is uninformative — sweep up to the context limit.
- **Demonstration quality matters.** Generic or off-distribution faux turns are weaker; the attack is stronger when demonstrations resemble the target behavior.

## Best-of-N Jailbreaking (BoN)

Aliases: BoN = Best-of-N Jailbreaking, "best-of-n jailbreak", Hughes, Price, Lynch et al. 2024 (arXiv:2412.03556). Authors include John Hughes, Sara Price, Aengus Lynch, Ethan Perez, Mrinank Sharma.

**What it is.** A dead-simple black-box algorithm: repeatedly sample the same harmful request with random **augmentations** (for text: random capitalization, character shuffling, typos; for other modalities: modality-specific perturbations) until one elicits a harmful response. No gradients, no attacker LLM — just resampling with noise and a success classifier. Reaches **89% attack success on GPT-4o** and 78% on Claude 3.5 Sonnet at ~10,000 sampled augmentations, and bypasses defenses like circuit breakers.

**When to use it:**
- A strong, trivially-implemented black-box baseline against API models.
- **Multimodal** red-teaming — BoN extends to vision (VLMs) and audio (ALMs) language models via modality-specific augmentations, which most attacks in this doc don't cover.
- Studying the sample-efficiency / ASR tradeoff (ASR scales with N).

**When *not* to use it:** A tight query budget — BoN's strength comes from large N (thousands of samples); it's brute force, not efficient.

**Pitfall:** Cost scales linearly with N — 10k samples × a frontier API model per behavior gets expensive; budget and report the N you used (ASR is meaningless without it).

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

Aliases: `pyrit` on PyPI, **`microsoft/PyRIT` on GitHub** (note: the older `Azure/PyRIT` URL is **archived** — make sure you're looking at `microsoft/PyRIT`), "Microsoft's red-team toolkit". PyRIT = Python Risk Identification Tool (for generative AI). Latest v0.13.0 (April 2026), monthly releases.

**What it is.** Microsoft's open-source orchestration framework for AI red-teaming. Provides building blocks: **targets**, **converters** (transform prompts), **scorers**, **orchestrators** (multi-turn attack loops). Used widely outside Microsoft — it's the de-facto orchestrator framework alongside garak.

**garak vs PyRIT:** **garak = static probe library** you point at an endpoint to scan for known issues. **PyRIT = orchestrator framework** you build red-team campaigns inside. Use both: garak for breadth scans, PyRIT for crafted multi-turn campaigns.

**When to use it:**
- Multi-turn attack orchestration with explicit converter / scorer / orchestrator primitives.
- You want a framework separate from Inspect for red-team-specific work.

**When *not* to use it:** A simple eval task — Inspect AI is closer to what you want.

## HarmBench

Aliases: `HarmBench`, `centerforaisafety/HarmBench` on GitHub, "Mazeika et al." Paper: Mazeika et al. 2024, "HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal" (arXiv:2402.04249).

**What it is.** A standardized red-teaming benchmark: 510 harmful behaviors across 7 categories, with a paired classifier (`HarmBench classifier` = `cais/HarmBench-Llama-2-13b-cls`) for evaluating attack success. **Includes built-in implementations of GCG, PAIR, TAP, AutoDAN-GA** — running these via HarmBench is usually easier than via their standalone repos. Wrapped as `inspect_evals/harmbench`.

**Status (2026-04):** **Reference benchmark, frozen** — last commit August 2024, no v2 planned. The dataset and harness remain widely cited. The HarmBench classifier (Llama-2-13B based, compute-heavy) is being **displaced by StrongREJECT** as the default jailbreak scorer in 2025–26 papers.

**When to use it:**
- You want paper-comparable ASR numbers against 2024–25 baselines.
- You want a one-stop attack suite (GCG / PAIR / TAP / AutoDAN-GA all wired up).

**When *not* to use it as the scorer:** New work where paper-comparability isn't the goal — use **StrongREJECT** instead (lighter, better-calibrated against humans).

**Pitfalls:**
- **Classifier disagreement.** The HarmBench classifier and a GPT-4 grader disagree ~10% of the time. Report both, or audit a sample.
- **Behaviors include "copyright violations" alongside genuinely harmful items.** Don't collapse the categories.

## JailbreakBench

Aliases: `JailbreakBench`, `JailbreakBench/jailbreakbench` on GitHub, "JBB", "JBB-Behaviors". Paper: Chao et al. 2024, "JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models" (arXiv:2404.01318).

**What it is.** A standardized jailbreak benchmark with 100 prompts (50 misuse + 50 borderline), public leaderboard, and reference defense baselines. Wrapped as `inspect_evals/jailbreakbench`.

**When to use it:** Reporting jailbreak rates that are leaderboard-comparable.

**When *not* to use it:** Research that needs more diverse / fresh prompts (the 100 are public, models may train on them).

## AgentHarm

Aliases: `AgentHarm`, in **`UKGovernmentBEIS/inspect_evals/src/inspect_evals/agentharm`**. Joint **Gray Swan + UK AISI** project (Andriushchenko, Souly et al., arXiv:2410.09024). Dataset at `huggingface.co/datasets/ai-safety-institute/AgentHarm`.

**What it is.** A benchmark of harmful agentic tasks (where the model uses tools to do bad things) with a paired benign set. Better suited than HarmBench for measuring agent-mode harm.

**Status (2026-04):** Active inside `inspect_evals`. **Currently 44 of 66 public test base behaviors released** — don't be confused if your numbers don't match the paper exactly.

**When to use it:** Evaluating tool-using agent safety.

## StrongREJECT (LLM-judge for jailbreak success)

Aliases: `strong_reject`, **`dsbowen/strong_reject`** on GitHub (the active maintained fork by SR author Dillon Bowen — recommended), `alexandrasouly/strongreject` (original paper repo, frozen). arXiv:2402.10260, NeurIPS 2024. **Not on PyPI** — install from GitHub.

**What it is.** A **two-component LLM-judge** for jailbreak success: (1) refusal classifier, (2) specificity + convincingness scoring. Calibrated against human ratings; uses GPT-4-class judge by default but works with any LLM-judge. **Has overtaken HarmBench-cls as the default jailbreak scorer in 2025–26 papers.**

**When to use it:**
- Default scorer for new jailbreak work. Better calibration than HarmBench-cls, lighter compute (no 13B classifier needed), and judges can swap freely.
- You want a single comparable score across attacks/defenses.

**When *not* to use it:**
- You need paper-comparability with 2024-era HarmBench numbers — keep using HarmBench-cls.
- You're scoring fully out-of-distribution attacks where the LLM-judge itself is unreliable — audit a sample.

**Useful fork:** `b-d-e/strong_reject` adds local vLLM judge support — useful when you want to run the judge on a self-hosted GPU box.

## Content classifiers (Llama Guard, WildGuard, ShieldGemma)

These are **input/output classifiers**, not red-team attack tools. Mature, well-cited, three options at different size/license tradeoffs. Useful for: (1) labeling jailbreak attempts in datasets you generate, (2) as a scorer alongside StrongREJECT, (3) as a defense baseline to attack.

**Llama Guard (3 / 4)**

Aliases: `meta-llama/PurpleLlama` on GitHub, `meta-llama/Llama-Guard-3-8B` and `meta-llama/Llama-Guard-4-12B` (multimodal) on HuggingFace. Active under Meta. Output: per-policy harm category labels.

**WildGuard**

Aliases: `allenai/wildguard` (repo, frozen Dec 2024), `allenai/wildguard` (model on HF), `allenai/wildguardmix` (dataset). 7B model, three-way labels (refusal / jailbreak / harm) — richer label space than Llama-Guard's binary.

**ShieldGemma**

Aliases: HF model cards only (`google/shieldgemma-2-4b-it`, etc.) — no canonical code repo. Smallest deployable option (2B–4B sizes). Use when memory budget matters.

**Recommendations:**
- **Llama-Guard-3-8B** for general use (Meta-maintained, decent license).
- **WildGuard-7B** if you want refusal/jailbreak/harm three-way labels rather than binary.
- **ShieldGemma** if you need the smallest deployable option.

**Pitfall:** All three have **known false-negative patterns on out-of-distribution attacks**. Never use as the sole judge for novel attack research — pair with StrongREJECT or human spot-checks.

## HaizeLabs and other commercial offerings

Aliases: HaizeLabs, "Haize Suite". Also: Lakera, Patronus, Robust Intelligence, NVIDIA NeMo Guardrails.

**What they are.** Commercial / hybrid open-source red-team and runtime-guard offerings. Haize Labs publishes some open research and red-team artifacts; their commercial Haize Suite runs continuous attacks.

**When to use them:** Industrial deployment / production guardrails — out of scope for most MATS fellow research, but useful if your project needs runtime classifiers.

## AgentDojo (prompt injection against tool-using agents)

Aliases: `agentdojo` on PyPI (v0.1.35), `ethz-spylab/agentdojo` on GitHub, "the ETH prompt-injection benchmark". Paper: arXiv **2406.13352**, "AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents" (NeurIPS 2024 Datasets & Benchmarks).

**What it is.** A dynamic environment — not a static prompt list — for the attack that matters once a model has tools: **indirect prompt injection**, where the adversarial instruction arrives inside *data the agent reads* (an email, a web page, a file) rather than from the user. Each scenario pairs a **user task** (what the agent is supposed to accomplish) with an **injection task** (what the attacker wants instead), so you score *both* utility and attack success and can't cheat by breaking the agent.

```bash
pip install agentdojo
```

```bash
python -m agentdojo.scripts.benchmark -s workspace -ut user_task_0 \
    -ut user_task_1 --model gpt-4o-2024-05-13 \
    --defense tool_filter --attack tool_knowledge
```

Note the shape of that command: **attack and defense are both pluggable** (`--attack`, `--defense`). That is the reason to use this rather than hand-rolling — a defense evaluated against only the attack its author wrote is not evaluated.

**When to use it:**
- Any project on agent security, tool-use safety, or monitoring an agent that reads untrusted content.
- You are proposing a prompt-injection *defense* and need a benchmark that a reviewer accepts, plus attacks you didn't design.
- You want an AI-control-flavoured experiment where the "attacker" is the environment rather than an untrusted policy — see [`ai-control.md`](../oversight-and-control/ai-control.md) for the distinction.

**When *not* to use it:**
- Your threat model is *direct* jailbreaking of a chat model. That's the rest of this doc — GCG, PAIR, TAP, BoN.
- You need a realistic production environment. The suites are synthetic by design (that's what makes them scorable); results transfer as a relative ranking, not as an absolute breach rate.

**Pitfalls:**
- **Model IDs in published tables are frozen in time.** The README example pins `gpt-4o-2024-05-13`. Re-running with a current model gives different numbers; never compare your run against a paper's table without re-running the paper's baseline.
- **Reporting attack success without utility.** A defense that refuses everything scores 0% attack success. Always report the paired utility number.
- **The injection is inside tool output**, so a scaffold that truncates or summarises tool results before the model sees them changes the benchmark. If you use a custom scaffold, say so — you may have accidentally built a defense.
- **Cost.** Each task is a multi-turn agent rollout across several suites; a full sweep of attacks × defenses × models is a real API bill. Pilot on one suite first, and see [`code-recipes.md`](../engineering/code-recipes.md) on caching.
- **Models may recognise the benchmark as a test, which lowers measured attack success.** Li, Chew, Lin, Jones, Fu & Zou, *WARP: Measuring and Mitigating Evaluation Awareness in Browser-Agent Safety Benchmarks* (ICML 2026 "Agents in the Wild" workshop poster, `icml.cc/virtual/2026/67956`, OpenReview `8fk9XYWtSQ`; no arXiv version found, code on anonymous.4open.science mirrors) ran 4,608 trajectories over six models and four indirect-prompt-injection benchmarks (DoomArena, WASP, AgentDojo, InjecAgent): models often labelled trajectories as evaluations, and an explicit evaluation cue lowered attack-success rate on DoomArena by 10.9 percentage points while a length-matched non-eval cue did not. They release a pipeline for generating more realistic injection tasks on seedable synthetic browser environments (a 50-task WebArena Verified instantiation reports 80.7% headline attack success with lower awareness than a no-rewrite baseline) and recommend routinely reporting eval awareness. Treat any prompt-injection attack-success rate as a **lower bound**; see [`evals.md`](evals.md).

## Automated behaviour auditing (Petri, Bloom) — when it replaces jailbreak attacks

Aliases: automated auditing agent, "auditor model", Inspect Petri, Petri Bloom, BLOOM-WILT, alignment auditing.

**What it is.** Where GCG / PAIR / TAP search for a prompt that gets one *known* harmful output, an **auditing agent** plays a user (or simulates an environment) against a target over many turns to find *which* concerning behaviours appear — sycophancy, reward hacking, self-exfiltration, sabotage, evaluation awareness — and a judge scores the transcripts. Tooling and commands: [`inspect-ecosystem.md`](inspect-ecosystem.md) (Petri for a broad sweep, Petri Bloom for a generated suite around one behaviour, Petri Dish to audit the real Claude Code / Codex CLI / Gemini CLI scaffold, BLOOM-WILT when you have the target's logits).

**When to use it:** your threat model is *the model's own dispositions* in agentic or multi-turn use rather than an external attacker's prompt; you want candidate behaviours to study. **When *not* to use it:** you need a clean misuse-robustness number against a fixed harm taxonomy (HarmBench / StrongREJECT), or you cannot afford judge-model cost (the full Petri default is 170+ seeds × up to 30 turns). An auditor's judge scores are a model's opinion — validate against hand labels.

**Elicitation scales with compute.** Slocum et al. (LessWrong, 2026-09-11; code `msp895/oai-hf-incident-reproduction`) elicited each behaviour in the OpenAI–Hugging Face incident with a Petri-based auditor from a high-level description, but the audits needed to reach a given success probability varied a lot across behaviours, and a simple "reviewer between waves" in-context-RL loop cut the compute to reach 80% elicitation on the hardest behaviour by 2.2× (author-reported). Report the **number of audit attempts** behind any "we could not elicit X" claim — a negative result at low budget is weak evidence.

## Cross-cutting red-team pitfalls

- **"Attack success" is fuzzy.** Define clearly: did the model output the harmful content? Was it actionable? Did it just complete a prefix? Use a classifier *and* spot-check.
- **Refusals vs evasions.** "Sorry, I can't help with that" is a refusal; a model that gives a wrong-but-helpful-sounding answer is more dangerous and may not register as "harmful."
- **OpenAI / Anthropic policy.** Running attack prompts against API models can violate ToS. Read provider AUPs; for systematic red-team work most providers prefer prior coordination.
- **Cost of attacks at scale.** GCG over 500 behaviors × 5 seeds × a 70B model can run multiple GPU-weeks. Budget early.
- **Don't conflate "I jailbroke it" with "this model is unsafe in deployment."** Production has additional layers (system prompts, content filters, monitoring). Lab attacks are necessary but not sufficient evidence.
- **Reproducibility.** Many published jailbreaks stop working after a model patch. Always log model version (e.g. `claude-sonnet-4-6`, snapshot dates) and attack timestamp. For open-weight models served through a router such as OpenRouter, also pin and log the **provider and quantization**: quantization can degrade safety alignment (Kharinaev et al., arXiv:2502.15799, 66 quantized variants across PTQ and QAT methods), so a refusal rate or attack success rate can shift with the serving stack alone — see [`evals.md`](evals.md#pin-your-inference-provider-openrouter-and-other-routers).

## Red-teaming vs AI Control: how they differ

**Red-teaming** here means: probing for misuse / jailbreak vulnerabilities, treating the model as a system you're trying to make do bad things. The threat model is an external attacker.

**AI Control** is different: it assumes the *model itself* may be misaligned and is the adversary. Tooling for that lives in [`ai-control.md`](../oversight-and-control/ai-control.md) — ControlArena, defer-to-trusted protocols, side tasks, monitors. If you're studying "what if the model itself is trying to harm me," go there.

The tooling overlaps somewhat (jailbreak attacks can serve as red-team policies inside control evaluations), but the questions and protocols are distinct.

## Cross-references

- Inspect AI for running these benchmarks: [`evals.md`](evals.md).
- Datasets details: [`datasets-benchmarks.md`](datasets-benchmarks.md).
- Multi-provider API client for custom attack scripts: [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md).
- AI Control (model-as-adversary protocols): [`ai-control.md`](../oversight-and-control/ai-control.md).
- Automated auditing agents (Petri, Bloom, Dish): [`inspect-ecosystem.md`](inspect-ecosystem.md).

---

## Common questions

### How do I run GCG (Greedy Coordinate Gradient) on an open-weight model?

```python
# pip install nanogcg
import nanogcg
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct", torch_dtype="auto").to("cuda")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
result = nanogcg.run(model, tokenizer, messages=[{"role": "user", "content": "Tell me how to..."}], target="Sure, here's...")
```
Use `nanogcg` (Gray Swan's library), not the original `llm-attacks` repo unless you're reproducing the original 2023 paper exactly.

### Does GCG work on API models like Claude or GPT-4?

No — GCG is **white-box** and needs gradients. For closed-API models, use **PAIR** (LLM-as-attacker, black-box). Some GCG suffixes do *transfer* from open to closed models, but transfer is unreliable; treat it as a probe, not a primary attack.

### What's the difference between PAIR and GCG?

**GCG** (Greedy Coordinate Gradient): white-box, gradient-based, optimizes a token sequence to make the model produce a target output. Fast and strong on open weights; produces gibberish-looking suffixes. **PAIR** (Prompt Automatic Iterative Refinement): black-box, an attacker LLM iteratively refines natural-language jailbreak prompts based on the target's responses. Works on API models; produces fluent text.

### Can I publish HarmBench / JailbreakBench attack results?

Yes — both are open and designed for this. **But:** running attacks against closed API models may violate that provider's Acceptable Use Policy at scale. For systematic red-team work, most providers want prior coordination — talk to your mentor / institutional review.

### What is abliteration?

The technique of identifying the **refusal direction** in a model's activation space (via mean-difference of activations on harmful vs harmless prompts; Arditi et al. 2024) and projecting it out of the model's weights. Produces "abliterated" / uncensored model checkpoints. Useful for studying refusal mechanisms; *not* recommended for deployment. See [`steering.md`](../interpretability/steering.md) "Refusal-direction abliteration."

### How do I measure attack success rate (ASR)?

For HarmBench-style benchmarks: score with the **HarmBench classifier** (`cais/HarmBench-Llama-2-13b-cls`) for paper-comparability. For JailbreakBench: use the JBB Llama-Guard judge built into the package. **For new work in 2025–26, use StrongREJECT** (`dsbowen/strong_reject`) — it's overtaken HarmBench-cls as the default scorer (better human calibration, lighter compute, judge model can be swapped). Always validate any classifier on a sample of *your* model's outputs (classifiers trained on older model outputs may calibrate wrong for newer ones). Report per-category breakdown, not just overall.

### What's the cheapest way to scan a model for vulnerabilities?

**garak** (`pip install garak`) — runs dozens of pre-built probes (toxicity, leakage, prompt injection, encoding tricks). Lower attack quality than GCG / PAIR but covers a wide attack surface in minutes. Choose specific probes (`--probes`) rather than a full sweep on API models — costs add up fast.

---

Last verified: 2026-10. nanoGCG v0.3.0 (Feb 2025; minimal updates since). PAIR repo stable. AutoDAN canonical handle is `SheltonLiu-N/AutoDAN`. **PyRIT moved to `microsoft/PyRIT`** — `Azure/PyRIT` is archived. garak v0.14.1, very active under NVIDIA. HarmBench frozen (Aug 2024); StrongREJECT (`dsbowen/strong_reject`) is the new default jailbreak scorer in 2025–26. JailbreakBench v1.0.0 maintained. AgentHarm in `UKGovernmentBEIS/inspect_evals/agentharm` (Gray Swan + UK AISI). Llama Guard 3/4, WildGuard, ShieldGemma added as content classifiers. (Citation audit 2026-06: fixed PyRIT expansion (Tool, not Toolkit), StrongREJECT author (Dillon Bowen), and the AutoDAN acronym — the Liu et al. version automates "Do Anything Now", it is not "Automatic and Interpretable Adversarial attacks". Additions 2026-06: added arXiv IDs for the canonical attack/benchmark papers (GCG 2307.15043, PAIR 2310.08419, TAP 2312.02119, HarmBench 2402.04249, JailbreakBench 2404.01318), two previously-absent attack families — Many-shot Jailbreaking (Anil et al. 2024, Anthropic/NeurIPS) and Best-of-N (Hughes et al. 2412.03556) — and the foundational "why jailbreaks work" frame (Wei, Haghtalab & Steinhardt 2307.02483); all verified via arXiv/source.) (Additions 2026-08: AgentDojo — `agentdojo` v0.1.35 on PyPI, arXiv 2406.13352, install and benchmark CLI verified from the repo README — covering indirect prompt injection, which this doc previously lacked.) (Additions 2026-10: WARP (ICML 2026 workshop; figures — 4,608 trajectories, 10.9-point DoomArena drop, 80.7% headline ASR — taken from the abstract on icml.cc/virtual/2026/67956; no arXiv/GitHub link, code on anonymous mirrors); automated-auditing section (Petri / Bloom / Dish / BLOOM-WILT cross-reference; Slocum et al. LW 2026-09-11 with repo `msp895/oai-hf-incident-reproduction` verified); quantization-and-safety reproducibility note (arXiv 2502.15799 abstract checked); all verified via the cited pages.)
