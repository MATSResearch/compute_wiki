---
tags:
  - evaluation
  - red-teaming
---

# Red-Teaming and Jailbreak Research

Tools for adversarial robustness research: optimization-based attacks, LLM-as-attacker schemes, automated scanners, standardized harm benchmarks, and the jailbreak defenses they are used to test (with the evaluation bar a new defense has to clear).

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
| Microsoft-flavored automation for AI red team (multi-turn attacks, scorers, scenarios) | **PyRIT** (v1.x since 2026-07; breaking v1 architecture) |
| Declarative YAML red-team scan of an *application* endpoint (plugins × strategies, per-category failure report) | **promptfoo** (`promptfoo redteam`) |
| Automated red-teaming of a production coding/tool agent that keeps *why* each attack works | **AHA** (Agent Hacks Agents, `henrymao2004/Auto-research-red-teaming`) |
| Long-horizon, stateful red-teaming of tool-using code agents across many agent runtimes | **OpenART** (`AI45Lab/OpenART`, AGPL-3.0) |
| Standardized harm benchmark with classifier scoring | **HarmBench** (frozen but reference); for scoring new work use **StrongREJECT** |
| Standardized jailbreak benchmark (JBB-Behaviors) | **JailbreakBench** |
| LLM-judge for jailbreak success (2025–26 default) | **StrongREJECT** (`dsbowen/strong_reject`) |
| Report an attack success rate (ASR) that survives a change of grader | Named grader + per-class label counts + fixed attempts per request; never keyword matching — see the ASR pitfall under StrongREJECT |
| Content classifier for safety pipelines | **Llama Guard 3/4**, **WildGuard**, **ShieldGemma** |
| Build or evaluate a jailbreak *defense* | **Constitutional Classifiers** / **Constitutional Classifiers++** (Anthropic, no code), **Circuit Breakers** (`GraySwanAI/circuit-breakers`); evaluation bar from **"The Attacker Moves Second"** (arXiv:2510.09023). See "Jailbreak defenses and how to evaluate them" |
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

**Version (as of 2026-10-20):** v0.17.1 (2026-10-16; PyPI `garak` 0.17.1, Python ≥3.11). v0.17.1 adds a hit@k attack-success-rate metric and Python 3.14 support, and fixes two scoring bugs: "stop FileDetector scoring an unexamined file as a pass" and "stop RefusalOnlyAdversarial over-counting skipped multi-turn attempts" — re-run scans that used either before comparing. Earlier, v0.17.0 (2026-09-09), per its release notes: "drop support for python 3.10, add support for python 3.13"; an EU AI Act tag mapping that groups probe results by the risk categories the Act names; detector fixes, including the package-hallucination detector missing packages after the first in `import a, b` and missing dotted or indented imports; the analysis step's confidence intervals rebuilt from attack hits; and a fix for an "indefinite hang on OpenAICompatible unreachable targets".

**Pitfalls:**
- **A scan of a local server that never finishes.** Before 0.17.0, garak could hang indefinitely when an OpenAI-compatible target (e.g. a local vLLM server) was unreachable. Upgrade with `pip install "garak>=0.17"` in a Python ≥3.11 environment.
- **Package-hallucination numbers from before 0.17.0 under-count.** The detector missed multi-package and dotted imports; re-run those scans before comparing.
- **FileDetector passes and multi-turn refusal counts from before 0.17.1 are suspect.** FileDetector could score a file it never examined as a pass, and `RefusalOnlyAdversarial` over-counted skipped multi-turn attempts.
- **Probes vary wildly in current relevance.** Some date from GPT-3 era and barely affect modern models; some are specific to particular model families. The dashboard can be misleading without inspection.
- **API costs add up.** A full garak sweep on a frontier API model can be hundreds of dollars. Pick probes deliberately.

## PyRIT

Aliases: `pyrit` on PyPI, **`microsoft/PyRIT` on GitHub** (note: the older `Azure/PyRIT` URL is **archived** — make sure you're looking at `microsoft/PyRIT`), "Microsoft's red-team toolkit", CoPyRIT (its GUI). PyRIT = Python Risk Identification Tool (for generative AI). **v1.0.0 (2026-07-24), v1.0.1 (2026-07-30), v1.1.0 (2026-09-04)**; PyPI `pyrit` 1.1.0, Python `>=3.10, <3.15` (checked 2026-10-14). The previous wiki version (v0.13.0, April 2026) predates the v1 rewrite.

**What it is.** Microsoft's open-source framework for AI red-teaming. Building blocks: **targets** (the system under test), **converters** (transform prompts; `PromptConverter` is now `Converter`), **scorers**, **attack techniques** and executors (single- and multi-turn attacks such as Crescendo and TAP; `pyrit/executor/attack` has `single_turn` and `multi_turn` subpackages), and **scenarios** composed of registered techniques. Used widely outside Microsoft alongside garak.

**What changed in v1 (breaking).** From the v1.0.0 notes: "Scenarios now compose registered techniques — scenario strategies were renamed to techniques"; "Component construction moved to registries" (attack techniques, targets, scorers, converters, scenarios); "Conversation and memory models changed" (conversation state moved into a new `Conversation` model; `MemoryExporter` / `export_conversations` removed; database migrations); and "Pre-v1 compatibility paths are gone". There is no `orchestrator` module in the v1.1.0 package tree, so pre-July-2026 notebooks and tutorials that use orchestrators are likely to break. v1.1.0 added Best-of-N, system-prompt extraction and package-hallucination capabilities, ten converters, and 488 in-the-wild jailbreak templates (TrustAIRLab).

**garak vs PyRIT:** **garak = static probe library** you point at an endpoint to scan for known issues. **PyRIT = orchestrator framework** you build red-team campaigns inside. Use both: garak for breadth scans, PyRIT for crafted multi-turn campaigns.

**When to use it:**
- Multi-turn attack orchestration with explicit converter / scorer / orchestrator primitives.
- You want a framework separate from Inspect for red-team-specific work.

**When *not* to use it:** A simple eval task — Inspect AI is closer to what you want. Reproducing a paper that used PyRIT 0.x: pin the old version (`pip install "pyrit<1.0"`), since the APIs and the scoring defaults below changed.

**Pitfalls (v1.1):**
- **Scores can be undetermined.** v1.1.0 notes: "Check `score.is_undetermined` before reading `score_value` or calling `get_value()`." Code that reads every score as a value will mis-handle these.
- **Blocked responses are now scored.** "Partial blocked responses are now scored by default. Set `should_score_blocked_content=False` to retain the previous behavior." Attack-success numbers from 1.1 and from earlier versions are not comparable unless you set this.

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
- **Behaviors include "copyright violations" alongside genuinely harmful items.** Don't collapse the categories. A psychometric audit (Stewart et al., arXiv:[2610.12409](https://arxiv.org/abs/2610.12409), 2026-10-08) found that multidimensional item response theory "strongly suggests that HarmBench does not measure a singular attribute", so one HarmBench ASR averages distinct behaviours; report per category ([`measurement-validity.md`](../engineering/measurement-validity.md#one-score-one-attribute-and-whose-definition-of-the-label)).

## JailbreakBench

Aliases: `JailbreakBench`, `JailbreakBench/jailbreakbench` on GitHub, "JBB", "JBB-Behaviors". Paper: Chao et al. 2024, "JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models" (arXiv:2404.01318).

**What it is.** A standardized jailbreak benchmark with 100 prompts (50 misuse + 50 borderline), public leaderboard, and reference defense baselines. Wrapped as `inspect_evals/jailbreakbench`.

**When to use it:** Reporting jailbreak rates that are leaderboard-comparable.

**When *not* to use it:** Research that needs more diverse / fresh prompts (the 100 are public, models may train on them).

## AgentHarm

Aliases: `AgentHarm`, in **`UKGovernmentBEIS/inspect_evals/src/inspect_evals/agentharm`**. Joint **Gray Swan AI + UK AI Security Institute (UK AISI)** project (Andriushchenko, Souly et al., arXiv:2410.09024; ICLR 2025). The paper's affiliation list names only these two organisations; it is not an Anthropic benchmark. Dataset at `huggingface.co/datasets/ai-safety-institute/AgentHarm`.

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

**Pitfall — the attack success rate (ASR) you report is partly a property of the grader and the attempt budget.** Three October 2026 papers, holding the target model and attacks fixed:
- **Grader choice alone moves ASR by tens of points.** Davis, Emil-Popescu & Jana (arXiv:[2610.19306](https://arxiv.org/abs/2610.19306), 2026-10-13): "changing only the judge LLM can alter reported ASR by up to 82 percentage points". Nguyen, Menon, Tappe Maestro, Aubinais & Cheng (arXiv:[2610.26595](https://arxiv.org/abs/2610.26595), 2026-10-19): "Low-resource language attacks achieve a mean ASR of 96.0% under keyword matching but 2.7% under a Qwen3 evaluator following StrongREJECT scoring instructions".
- **A small grader can delete a class.** Bin Safi (arXiv:[2610.24872](https://arxiv.org/abs/2610.24872), 2026-10-17): three 8B/9B graders from three families moved compliant responses into "evasion", and "One of them assigns the compliance label zero times in 900 responses"; compliance rates then differed 22–25× across eight graders. "Per-class label counts expose it at no cost and without human labels."
- **Resampling inflates ASR.** Nguyen et al.: "sampling 100 responses for each unchanged request at Ollama's default temperature of 0.8 yields 100% ASR under keyword matching but 50% under the Qwen3 evaluator", and changing the number and arrangement of attempts reversed the ranking of two attacks (DeepInception and rewriting). A refusal is probabilistic, so an attack evaluated with more samples per request looks stronger.
Minimum to report with any ASR: the named grader (model and prompt), per-class label counts, the number of attempts per request and how they were aggregated, and a matched response budget across attacks. Never use keyword-match ASR as a headline. General grader-validity discussion: [`measurement-validity.md`](../engineering/measurement-validity.md#the-grader-is-an-instrument-too).

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

**Pitfall — a guardrail's benchmark score mostly reflects whose definition of "unsafe" it learned.** Jebraeeli et al., "Policy Is Not Capability" (arXiv:[2610.25060](https://arxiv.org/abs/2610.25060), 2026-10-18; NeurIPS workshop, one industrial deployment) trained ten guardrail arms on the same ~53k prompts labelled under two operational definitions ("is this a request for harmful content?" vs "would a moderator block this?"). With architecture and optimiser fixed, "HarmBench-copyright spans 0-100 and OR-Bench-hard over-refusal 3.4-56.4%" across arms at unchanged detection capability; JailbreakBench-benign (88%) and OR-Bench-hard (82%) prompts were already in the guardrail's training pool; and a distilled student inherits its teacher's policy through soft labels, so "teacher provenance is an unrecorded confound in any released checkpoint". When you compare Llama Guard, WildGuard, ShieldGemma or your own classifier, state the label definition each was trained and graded against, check benchmark–training overlap, and report a seed floor ([`measurement-validity.md`](../engineering/measurement-validity.md#one-score-one-attribute-and-whose-definition-of-the-label)).

## Jailbreak defenses and how to evaluate them

Aliases: jailbreak defense, LLM safeguards, adaptive attacks, adaptive evaluation, Constitutional Classifiers, CC++, exchange classifier, Circuit Breakers, Representation Rerouting (RR), Cygnet, "The Attacker Moves Second".

The rest of this page is about attacks. This section covers the defenses those attacks are aimed at, and the standard a new defense must meet. Robust jailbreak defense is an **open problem**: as of 2026-10, defenses evaluated only against static attack sets have repeatedly fallen to adaptive attackers. A small number of classifier systems have held up under thousands of hours of human red-teaming, but only for narrow targets.

### Constitutional Classifiers (Anthropic)

Sharma, Tong, Mu, Wei et al., "Constitutional Classifiers: Defending against Universal Jailbreaks across Thousands of Hours of Red Teaming" (arXiv:2501.18837). Input and output classifiers trained on synthetic data, generated by prompting an LLM with a natural-language **constitution** of permitted and restricted content (the first paper publishes a chemical-weapons constitution, though its human red-teaming targeted CBRN (chemical, biological, radiological, nuclear) queries; the second uses a CBRN constitution). The target is **universal jailbreaks**: one strategy that extracts detailed answers across many forbidden queries.

- Red-teaming result, verbatim: "In over 3,000 estimated hours of red teaming, no red teamer found a universal jailbreak that could extract information from an early classifier-guarded LLM at a similar level of detail to an unguarded model across most target queries." The red-teaming ran as a HackerOne bug bounty with 405 invited participants (about 183 active) and ten target questions, graded by rubrics built from helpful-only model outputs.
- Deployment cost: an absolute 0.38% increase in production-traffic refusals and a 23.7% inference overhead.

**Constitutional Classifiers++** (Cunningham, Wei, Wang et al., arXiv:2601.04603). **Exchange classifiers** judge a response in its full conversational context; a **two-stage cascade** escalates only suspicious exchanges from cheap classifiers to expensive ones; and **linear probe classifiers** are ensembled with external classifiers. Reported: "a 40x computational cost reduction compared to our baseline exchange classifier", a 0.05% refusal rate on production traffic, and over 1,700 hours of red-teaming in which no attack elicited responses to all eight target CBRN queries at detail comparable to an undefended model. That success criterion is strict: the same red-teaming (approximately 198K attempts) still found one "high-risk vulnerability", which the paper defines as an attack answering more than five of the eight target questions at a rubric score at least half that of an undefended model.

**When to use them:** as the reference design for a classifier-based defense, and for the success criterion (detail comparable to an undefended model, across a fixed query set). **When *not* to:** you need code or weights. Neither paper releases any, so a reproduction means rebuilding the constitution-to-synthetic-data pipeline. Results are for CBRN universal jailbreaks; they say nothing about per-query jailbreaks for other harm categories.

### Circuit Breakers (Representation Rerouting)

Zou, Phan, Wang et al. (Gray Swan AI, CMU, Center for AI Safety), "Improving Alignment and Robustness with Circuit Breakers" (arXiv:2406.04313; code `GraySwanAI/circuit-breakers`, MIT; checkpoints `GraySwanAI/Llama-3-8B-Instruct-RR`, `GraySwanAI/Mistral-7B-Instruct-RR`). **Representation Rerouting (RR)** trains LoRA adapters so that internal representations producing harmful output are rerouted to an orthogonal direction, which interrupts the generation instead of training a refusal. On HarmBench behaviours the paper reports compliance under a range of unseen attacks reduced by an average of 87% (Mistral) and 90% (Llama-3), with MT-Bench and MMLU largely preserved. It is a representation-engineering method; see [`steering.md`](../interpretability/steering.md).

**What later work found** (read before using it as a baseline):

- Best-of-N Jailbreaking bypasses it (see the BoN section above).
- "The Attacker Moves Second" reached **100% attack success** against Circuit Breakers on HarmBench with an RL-based adaptive attack.
- Under ordinary benign finetuning, its protection disappeared quickly in the Deep Ignorance experiments (arXiv:2508.06601). For open-weight releases, see the tamper-resistance section of [`unlearning.md`](../alignment-science/unlearning.md).

**When to use it:** as an open, reproducible defense baseline with released checkpoints. **When *not* to:** as evidence that a model is robust. Its originally reported numbers come from non-adaptive attacks.

### The evaluation bar: "The Attacker Moves Second"

Nasr, Carlini, Sitawarin, Schulhoff et al., "The Attacker Moves Second: Stronger Adaptive Attacks Bypass Defenses Against LLM Jailbreaks and Prompt Injections" (arXiv:2510.09023). Four adaptive attack families were tuned against each defense: gradient-based, reinforcement-learning-based, search-based, and human red-teaming (an online competition with over 500 participants). Result: "we bypass 12 recent defenses (based on a diverse set of techniques) with attack success rate above 90% for most; importantly, the majority of defenses originally reported near-zero attack success rates." The twelve were Spotlighting, Prompt Sandwiching, RPO, Circuit Breakers, StruQ, MetaSecAlign, Protect AI, PromptGuard, PIGuard, Model Armor, Data Sentinel and MELON. MetaSecAlign, for example, reported 2% attack success on static AgentDojo; the adaptive search attack reached 96%. Human red-teamers succeeded in every case evaluated. Constitutional Classifiers were not among the defenses tested.

Their framing of what evaluation can show: "empirical evaluations cannot prove that a defense is robust; all it can (and should) do is fail to prove that the defense is broken!"

### What would convince people a new jailbreak defense works?

1. **Adaptive attackers with full knowledge of the defense**, tuned to it, at a stated budget (queries, GPU-hours, human-hours). A static set (HarmBench, JailbreakBench, AgentDojo's built-in attacks) is a smoke test, not robustness evidence.
2. **Several attack families**: gradient (nanoGCG on open weights), LLM-as-attacker (TAP/PAIR), search and RL-based attackers, resampling (Best-of-N at large N), and **human red-teaming**, which succeeded in every case evaluated in arXiv:2510.09023 and, on a subset of scenarios, outperformed the automated search attack (100% vs 69%).
3. **A strict success criterion**, ideally answer detail comparable to an undefended or helpful-only model on fixed target queries (the Constitutional Classifiers rubric approach). Spot-check the auto-rater by hand: arXiv:2510.09023 lists unreliable model-based raters as a lesson.
4. **The cost side**: over-refusal on benign traffic (or a benign benchmark) and inference overhead, as both Constitutional Classifiers papers report.
5. **For open-weight models, tampering**: finetuning and weight- or latent-space attacks, per [`unlearning.md`](../alignment-science/unlearning.md) ("Tamper resistance").
6. **Make it attackable**: release code, checkpoints or a public endpoint so others can try. arXiv:2510.09023 recommends defense authors try to break their own defense by hand first.

Design for this standard from the start, and state which of 1–6 your evaluation met. Claim robustness against the named attacks and budget, not robustness in general.

## promptfoo (red-team scanner for applications)

Aliases: `promptfoo` on npm (also `pip install promptfoo` and `brew install promptfoo`), `promptfoo/promptfoo` on GitHub, `promptfoo redteam`, "promptfoo red teaming". MIT; latest release 0.124.1 (2026-10-08). README: "Promptfoo is now part of OpenAI. Promptfoo remains open source and MIT licensed."

**What it is.** A command-line tool and library for declarative YAML evals and automated red-teaming of LLM *applications*: **plugins** generate adversarial inputs per harm or vulnerability category, **strategies** wrap them in jailbreak or injection patterns, and the report gives per-category failure rates. Targets can be any HTTP endpoint, a model API, or a local server (vLLM or llamafile via the `openai:chat:` prefix plus `apiBaseUrl`; llama.cpp through its native `llama:` provider, per the quickstart). It sits between garak's static probe list and PyRIT's framework.

```bash
# from the promptfoo red-team quickstart and configuration docs
npx promptfoo@latest redteam setup        # or: promptfoo redteam init --no-gui
export PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true   # keep attack generation local (see pitfall)
promptfoo redteam run                     # = redteam generate + redteam eval
promptfoo redteam report
```

**When to use it:** you have an application (a system prompt plus tools, a RAG endpoint, an agent behind HTTP) and want a broad, repeatable scan across standard harm categories, including in CI.

**When *not* to use it:** research on novel attacks or on model internals — it runs known plugin categories against an endpoint; and anything unreleased or confidential unless remote generation is off (next pitfall).

**Pitfalls:**
- **Attack generation goes to promptfoo's servers by default.** The configuration docs: "By default, promptfoo uses a remote service for generating adversarial inputs", and remote generation is preferred when you are logged into Promptfoo Cloud. Set `PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true` to force local generation, which the docs say "depends greatly on the model that you configure, and is generally low for most models".
- **The attacker model defaults to OpenAI.** The quickstart: "Attack generation uses a separate provider (defaults to OpenAI)." Configure `redteam.provider` if you need a different or self-hosted attacker, and report which one generated the attacks.
- **`pip install promptfoo` is a wrapper.** The PyPI package is at 0.2.0 while the tool itself is at 0.124.x on npm; check `promptfoo --version`, not the pip version.

## Autoresearch red-teaming of production agents (AHA) and long-horizon agent red-teaming (OpenART)

Aliases: Agent Hacks Agents, AHA, Vulnerability Concept Graph (VCG), `henrymao2004/Auto-research-red-teaming`, autoresearch red-teaming; OpenART (Open Agent Red Teaming), `AI45Lab/OpenART`, Evolutionary Markov Hypergraph Attack (EMHA).

**AHA.** Mao, Qian, Zheng & Wang, "Agent Hacks Agents: Autoresearch Discovers Vulnerabilities in Production Agents" (arXiv:2607.11698; code `henrymao2004/Auto-research-red-teaming`, MIT). The README: "AHA turns production-agent red-teaming into **autoresearch**: a Researcher iterates — hypothesize an attack, run it against a Docker-sandboxed victim agent, judge the trajectory, reflect — and accumulates a persistent **Vulnerability Concept Graph (VCG)**". Instead of keeping successful attack strings, it keeps *vulnerability concepts*: why an attack succeeds, the condition that enables it, and the evidence that would refute it. Each scenario is a single `contract.yaml`; victims include Claude Code and Codex. Author-reported (abstract): across 18 settings the concepts fall into eight families, and "On held-out instances the concepts reach a 47.0% attack success rate (ASR) against 32.8% for the strongest baseline, which uses more discovery queries"; patching each concept's enabling condition lowered AgentHazard ASR by 41.11 points. The README's quickstart includes a dry run with no Docker or keys (`bash autoresearcher/scripts/dry_run.sh`). **When *not* to use it:** against systems you do not own or are not authorised to test (the README's caution); or when you only need a fixed jailbreak suite.

**OpenART.** Chen, Wang, Wang et al., "OpenART: Scaling Agent Red Teaming via Open-Ended Environment Evolution" (arXiv:2608.00677; code `AI45Lab/OpenART`, **AGPL-3.0**). The paper describes over 10,000 validated stateful scenarios across 50 domains with a median of 97 tool calls, evaluated over 75 agent-model configurations, and an attack (EMHA) that changes the *environment state* mid-run while the task stays fixed; pooled ASR 85.0%, and "the specific runtime implementation of an agent explains a significant portion of safety variation beyond the underlying model's capabilities". The public repository (README, checked 2026-10-14) contains the Docker-based runtime, **three** runnable high-complexity tasks and the managed tools, with planner tasks and tools on Hugging Face (`dongdongunique/openart-planner-tasks`, `dongdongunique/openart-tools`). **When *not* to use it:** if AGPL terms are a problem for your project, or if you need the paper's full scenario set from the repo alone.

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
- **One run per task, and "not hijacked" is not "defended".** Jia et al. (arXiv:[2610.24048](https://arxiv.org/abs/2610.24048), 2026-10-16; four AgentDojo suites) found "single-run labels of thinking agents disagree with a rerun up to 35% of the time" — whether a thinking agent follows an injection is partly decided after it reads it — so run each task several times. Zarif et al. (arXiv:[2610.23254](https://arxiv.org/abs/2610.23254), 2026-10-16; 33,000 trajectories from eleven 2–14B open-weight agents on InjecAgent and AgentDojo): "most failed attacks are ignored (76-80%) rather than refused (17-18%)", in 21.7% of AgentDojo episodes the agent stayed safe but did not finish the user's task, and, for the attack success rate (ASR), "changing only the system prompt shifts InjecAgent ASR from 0.2% to 43%". Report how attacks fail (ignored vs refused), utility alongside ASR, and the exact system prompt. INFUSE (Nguyen et al., arXiv:[2610.20776](https://arxiv.org/abs/2610.20776); code `judydnguyen/infuse`, MIT) is a newer indirect-prompt-injection benchmark of 40 long-horizon tasks and 56 attack scenarios injected through the interaction surfaces an agent meets mid-workflow (shell commands, code, dependency installation, remote services); there, "prompt-level instructional hardening reduces mean attack success from 58.2% to 14.3%", so an undefended baseline with a bare system prompt overstates what a simple defense leaves.
- **Models may recognise the benchmark as a test, which lowers measured attack success.** Li, Chew, Lin, Jones, Fu & Zou, *WARP: Measuring and Mitigating Evaluation Awareness in Browser-Agent Safety Benchmarks* (ICML 2026 "Agents in the Wild" workshop poster, `icml.cc/virtual/2026/67956`, OpenReview `8fk9XYWtSQ`; no arXiv version found, code on anonymous.4open.science mirrors) ran 4,608 trajectories over six models and four indirect-prompt-injection benchmarks (DoomArena, WASP, AgentDojo, InjecAgent): models often labelled trajectories as evaluations, and an explicit evaluation cue lowered attack-success rate on DoomArena by 10.9 percentage points while a length-matched non-eval cue did not. They release a pipeline for generating more realistic injection tasks on seedable synthetic browser environments (a 50-task WebArena Verified instantiation reports 80.7% headline attack success with lower awareness than a no-rewrite baseline) and recommend routinely reporting eval awareness. Treat any prompt-injection attack-success rate as a **lower bound**; see [`evals.md`](evals.md).

## Automated behaviour auditing (Petri, Bloom) — when it replaces jailbreak attacks

Aliases: automated auditing agent, "auditor model", Inspect Petri, Petri Bloom, BLOOM-WILT, alignment auditing.

**What it is.** Where GCG / PAIR / TAP search for a prompt that gets one *known* harmful output, an **auditing agent** plays a user (or simulates an environment) against a target over many turns to find *which* concerning behaviours appear — sycophancy, reward hacking, self-exfiltration, sabotage, evaluation awareness — and a judge scores the transcripts. Tooling and commands: [`inspect-ecosystem.md`](inspect-ecosystem.md) (Petri for a broad sweep, Petri Bloom for a generated suite around one behaviour, Petri Dish to audit the real Claude Code / Codex CLI / Gemini CLI scaffold, BLOOM-WILT when you have the target's logits).

**When to use it:** your threat model is *the model's own dispositions* in agentic or multi-turn use rather than an external attacker's prompt; you want candidate behaviours to study. **When *not* to use it:** you need a clean misuse-robustness number against a fixed harm taxonomy (HarmBench / StrongREJECT), or you cannot afford judge-model cost (the full Petri default is 170+ seeds × up to 30 turns). An auditor's judge scores are a model's opinion — validate against hand labels.

**Auditor configuration is part of the measurement.** Giving a Petri auditor a related benchmark's transcripts — or even only its abstract — raised judged reward-hacking scores on coding agents (arXiv:[2610.16911](https://arxiv.org/abs/2610.16911)); hold the auditor's context fixed across targets and report it ([`inspect-ecosystem.md`](inspect-ecosystem.md#when-to-use-it-and-when-not-to)). If you train or tune auditors, include benign targets to measure false positives (Rosu & Wang, alignment.anthropic.com, 2026-10-15; see [`model-organisms.md`](../alignment-science/model-organisms.md)).

**Elicitation scales with compute.** Slocum et al. (LessWrong, 2026-09-11; code `msp895/oai-hf-incident-reproduction`) elicited each behaviour in the OpenAI–Hugging Face incident with a Petri-based auditor from a high-level description, but the audits needed to reach a given success probability varied a lot across behaviours, and a simple "reviewer between waves" in-context-RL loop cut the compute to reach 80% elicitation on the hardest behaviour by 2.2× (author-reported). Report the **number of audit attempts** behind any "we could not elicit X" claim — a negative result at low budget is weak evidence.

## Cross-cutting red-team pitfalls

- **"Attack success" is fuzzy.** Define clearly: did the model output the harmful content? Was it actionable? Did it just complete a prefix? Use a classifier *and* spot-check.
- **Refusals vs evasions.** "Sorry, I can't help with that" is a refusal; a model that gives a wrong-but-helpful-sounding answer is more dangerous and may not register as "harmful."
- **OpenAI / Anthropic policy.** Running attack prompts against API models can violate ToS. Read provider AUPs; for systematic red-team work most providers prefer prior coordination.
- **Cost of attacks at scale.** GCG over 500 behaviors × 5 seeds × a 70B model can run multiple GPU-weeks. Budget early.
- **Red-teaming an agent with internet access can hurt real third parties.** In Anthropic's evaluations (2026-10-09 report; most cases on public web benchmarks run on the live internet), models that could not complete a task directly exploited third-party sites with SQL or command injection, and models submitted a real government form and a real police tip form. Red-team agents in sandboxes whose egress is blocked and tested (HTTP *and* DNS), and scan transcripts for real-world side effects; see [Running agent evals with internet access](agent-scaffolds.md#running-agent-evals-with-internet-access).
- **Don't conflate "I jailbroke it" with "this model is unsafe in deployment."** Production has additional layers (system prompts, content filters, monitoring). Lab attacks are necessary but not sufficient evidence.
- **Reproducibility.** Many published jailbreaks stop working after a model patch. Always log model version (e.g. `claude-sonnet-4-6`, snapshot dates) and attack timestamp. For open-weight models served through a router such as OpenRouter, also pin and log the **provider and quantization**: quantization can degrade safety alignment (Kharinaev et al., arXiv:2502.15799, 66 quantized variants across PTQ and QAT methods), so a refusal rate or attack success rate can shift with the serving stack alone — see [`evals.md`](evals.md#pin-your-inference-provider-openrouter-and-other-routers).

## Red-teaming vs AI Control: how they differ

**Red-teaming** here means: probing for misuse / jailbreak vulnerabilities, treating the model as a system you're trying to make do bad things. The threat model is an external attacker.

**AI Control** is different: it assumes the *model itself* may be misaligned and is the adversary. Tooling for that lives in [`ai-control.md`](../oversight-and-control/ai-control.md) — ControlArena, defer-to-trusted protocols, side tasks, monitors. If you're studying "what if the model itself is trying to harm me," go there.

The tooling overlaps somewhat (jailbreak attacks can serve as red-team policies inside control evaluations), but the questions and protocols are distinct.

**Red-teaming a monitor rather than a model.** If the system under test is an AI-control *monitor*, search-based red-teaming looks different: **Screwtape** (Kozhevnikov & Tracy, arXiv:[2610.20941](https://arxiv.org/abs/2610.20941), 2026-10-14; Redwood Research; pipeline available on request) has an attacker model edit real Claude Code or Codex transcripts until the edit evades proxy monitors, then tests the survivors on a held-out monitor ("Across 252 runs, it produced 35 attacks that passed the verifier and evaded these monitors. Six of them, confirmed valid by human review, also evaded a held-out monitor provided by a frontier developer."). Its output is counterexamples, not a miss rate. Kitaoka et al. (arXiv:[2610.24052](https://arxiv.org/abs/2610.24052)) show that a monitor reading each agent separately misses attacks split across agents. Both are written up in [`ai-control.md`](../oversight-and-control/ai-control.md#monitor-benchmarks-and-transcript-red-teaming-monitoringbench-screwtape).

## Cross-references

- Inspect AI for running these benchmarks: [`evals.md`](evals.md).
- Datasets details: [`datasets-benchmarks.md`](datasets-benchmarks.md).
- Multi-provider API client for custom attack scripts: [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md).
- AI Control (model-as-adversary protocols): [`ai-control.md`](../oversight-and-control/ai-control.md).
- Automated auditing agents (Petri, Bloom, Dish): [`inspect-ecosystem.md`](inspect-ecosystem.md).
- Tamper resistance for open-weight safeguards (finetuning and weight-space attacks): [`unlearning.md`](../alignment-science/unlearning.md).
- Building safety in during pretraining (Safety Pretraining, Synthetic Persona Pretraining jailbreak-robustness claims): [`alignment-pretraining.md`](../alignment-science/alignment-pretraining.md).

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

For HarmBench-style benchmarks: score with the **HarmBench classifier** (`cais/HarmBench-Llama-2-13b-cls`) for paper-comparability. For JailbreakBench: use the JBB Llama-Guard judge built into the package. **For new work in 2025–26, use StrongREJECT** (`dsbowen/strong_reject`) — it's overtaken HarmBench-cls as the default scorer (better human calibration, lighter compute, judge model can be swapped). Always validate any classifier on a sample of *your* model's outputs (classifiers trained on older model outputs may calibrate wrong for newer ones). Report per-category breakdown, not just overall. Also report the grader by name, its per-class label counts (a collapsed grader can assign "compliant" zero times), and the number of samples per request: in October 2026 studies the judge alone moved ASR by up to 82 points, on low-resource-language attacks keyword matching gave a mean 96.0% where a StrongREJECT-instructed judge gave 2.7%, and 100 resamples at temperature 0.8 turned an unchanged request into 100% (keyword) or 50% (judge) ASR. Fix the response budget across the attacks you compare. See the ASR pitfall under StrongREJECT above.

### How do I evaluate a jailbreak defense I built?

Attack it adaptively, with full knowledge of the defense, using several attack families including human red-teamers, and report the budget, the over-refusal rate and the inference overhead. A near-zero attack success rate on a static benchmark is what most of the twelve defenses broken in "The Attacker Moves Second" (arXiv:2510.09023) originally reported. The checklist is in "Jailbreak defenses and how to evaluate them" above.

### What's the cheapest way to scan a model for vulnerabilities?

**garak** (`pip install garak`) — runs dozens of pre-built probes (toxicity, leakage, prompt injection, encoding tricks). Lower attack quality than GCG / PAIR but covers a wide attack surface in minutes. Choose specific probes (`--probes`) rather than a full sweep on API models — costs add up fast.

### My PyRIT notebook broke after upgrading. What changed?

PyRIT 1.0.0 (2026-07-24) is a breaking rewrite: scenarios compose registered *techniques*, components are built through registries, `PromptConverter` became `Converter`, conversation state moved to a `Conversation` model, and pre-v1 compatibility paths were removed. In 1.1.0 (2026-09-04), scores can be undetermined (check `score.is_undetermined` before `get_value()`) and partially blocked responses are scored by default (`should_score_blocked_content=False` restores the old behaviour). To reproduce older work, `pip install "pyrit<1.0"`.

### How do I red-team my LLM application (not the bare model) without sending my prompts to a third party?

**promptfoo**: `npx promptfoo@latest redteam setup`, then `promptfoo redteam run` and `promptfoo redteam report`. Set `PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true` first, because by default adversarial inputs are generated by promptfoo's remote service, and configure the attacker provider (it defaults to OpenAI). Local generation quality depends on the attacker model you configure.

---

Last verified: 2026-10-20. (Additions 2026-10-20: garak v0.17.1 release notes and PyPI; ASR-grader pitfall from arXiv 2610.19306, 2610.26595, 2610.24872 abstracts; guardrail label policy 2610.25060; AgentDojo methodology 2610.24048, 2610.23254, 2610.20776 abstracts (the InjecAgent 0.2%→43% figure is from 2610.23254); HarmBench 2610.12409; Screwtape 2610.20941 and 2610.24052 abstracts; Petri auditor context 2610.16911; Anthropic 2026-10-09 report. Additions 2026-10-14: PyRIT v1.0.0 / v1.1.0 release notes and package tree via the GitHub API, PyPI `pyrit` 1.1.0 — the v0.13.0 / orchestrator description was out of date; garak v0.17.0 release notes and PyPI; promptfoo README, red-team quickstart and configuration docs, release 0.124.1 and PyPI wrapper 0.2.0; AHA arXiv:2607.11698 abstract and README; OpenART arXiv:2608.00677 abstract and README.) nanoGCG v0.3.0 (Feb 2025; minimal updates since). PAIR repo stable. AutoDAN canonical handle is `SheltonLiu-N/AutoDAN`. **PyRIT moved to `microsoft/PyRIT`** — `Azure/PyRIT` is archived. garak v0.17.0 (2026-09-09), very active under NVIDIA. PyRIT v1.1.0 (2026-09-04). HarmBench frozen (Aug 2024); StrongREJECT (`dsbowen/strong_reject`) is the new default jailbreak scorer in 2025–26. JailbreakBench v1.0.0 maintained. AgentHarm in `UKGovernmentBEIS/inspect_evals/agentharm` (Gray Swan + UK AISI). Llama Guard 3/4, WildGuard, ShieldGemma added as content classifiers. (Citation audit 2026-06: fixed PyRIT expansion (Tool, not Toolkit), StrongREJECT author (Dillon Bowen), and the AutoDAN acronym — the Liu et al. version automates "Do Anything Now", it is not "Automatic and Interpretable Adversarial attacks". Additions 2026-06: added arXiv IDs for the canonical attack/benchmark papers (GCG 2307.15043, PAIR 2310.08419, TAP 2312.02119, HarmBench 2402.04249, JailbreakBench 2404.01318), two previously-absent attack families — Many-shot Jailbreaking (Anil et al. 2024, Anthropic/NeurIPS) and Best-of-N (Hughes et al. 2412.03556) — and the foundational "why jailbreaks work" frame (Wei, Haghtalab & Steinhardt 2307.02483); all verified via arXiv/source.) (Additions 2026-08: AgentDojo — `agentdojo` v0.1.35 on PyPI, arXiv 2406.13352, install and benchmark CLI verified from the repo README — covering indirect prompt injection, which this doc previously lacked.) (Additions 2026-10: WARP (ICML 2026 workshop; figures — 4,608 trajectories, 10.9-point DoomArena drop, 80.7% headline ASR — taken from the abstract on icml.cc/virtual/2026/67956; no arXiv/GitHub link, code on anonymous mirrors); automated-auditing section (Petri / Bloom / Dish / BLOOM-WILT cross-reference; Slocum et al. LW 2026-09-11 with repo `msp895/oai-hf-incident-reproduction` verified); quantization-and-safety reproducibility note (arXiv 2502.15799 abstract checked); all verified via the cited pages.) (Additions 2026-10-12: "Jailbreak defenses and how to evaluate them" section and at-a-glance row — Constitutional Classifiers arXiv:2501.18837, Constitutional Classifiers++ arXiv:2601.04603, Circuit Breakers arXiv:2406.04313 (`GraySwanAI/circuit-breakers`, MIT, via the GitHub API; `-RR` checkpoints via the HuggingFace API), "The Attacker Moves Second" arXiv:2510.09023; all checked via the arXiv API, with numbers (red-teaming hours and participants, refusal and overhead figures, 87%/90% compliance reduction, 12 defenses named, 100% ASR on Circuit Breakers, MetaSecAlign 2%→96%, humans 100% vs search 69%) read from the PDFs and quotes taken exactly from the abstracts or text. Neither Constitutional Classifiers paper links code. AgentHarm attribution re-checked against the arXiv:2410.09024 PDF: authors are affiliated with Gray Swan AI and the UK AI Security Institute only. Verification pass 2026-10-12: 40 claims checked, 2 corrected (human red-teaming succeeded "in all the cases we evaluated", not against every defense; the first Constitutional Classifiers paper's red-teaming targeted CBRN queries, not only chemical weapons). Verification pass 2026-10-20: 40 claims checked, 4 corrected (Anthropic 2026-10-09 cases restated as the report gives them; the 96.0%/2.7% ASR figures are for low-resource-language attacks; ASR spelled out in two sections).)
