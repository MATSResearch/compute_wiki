# Datasets and Benchmarks

Datasets and benchmarks commonly used in AI safety research. We focus on safety-flavored datasets (refusal, harm, deception, dangerous capability, persuasion, sycophancy) rather than general capability benchmarks. For general benchmarks (MMLU, ARC, etc.) see [`03_evals.md`](03_evals.md).

## At a glance

| You want to measure / study… | Use |
|---|---|
| Refusal behavior on harmful queries | **HarmBench**, **JailbreakBench**, **AdvBench** |
| Dangerous knowledge (CBRN-related) | **WMDP** (Weapons of Mass Destruction Proxy) |
| Sycophancy | **Sycophancy** datasets (Perez et al.; Sharma et al.) |
| Deception / model written evals | Anthropic **model-written evals**, **MASK** dataset |
| Persuasion ability | **MakeMePay**, **Persuasive Jailbreaker** datasets |
| Long-horizon agent capability | **METR HCAST** (see [`03_evals.md`](03_evals.md)) |
| Cyber-capability | **CyBench**, **InterCode**, **NYU CTF Bench** |
| Power-seeking / self-exfiltration scenarios | Anthropic **advanced AI risks** evals; specific paper datasets |
| Truthfulness | **TruthfulQA** |
| Honesty / hallucination | **SimpleQA**, **TruthfulQA**, **HaluEval** |
| Agent harm specifically | **AgentHarm** |
| Tool of choice for hosting & loading | HuggingFace `datasets` |

## HuggingFace `datasets` (the substrate)

Aliases: `datasets` on PyPI, `huggingface/datasets` on GitHub, "HF datasets".

**What it is.** The default library for loading benchmarks: `load_dataset("cais/wmdp")`, `load_dataset("cais/HarmBench", "standard")`, etc. Also handles streaming, sharding, and dataset versioning.

**Pitfalls:**
- **`split` matters.** Some safety datasets only have a `test` split; some have `train`/`test`/`val`. Read the dataset card.
- **Dataset gating.** WMDP is gated (requires accepting terms). HarmBench is open. JailbreakBench is open. You'll need a HuggingFace token (`huggingface-cli login`) for gated datasets.
- **`trust_remote_code=True` is required for some older datasets.** Read the loading script before running it on shared infra.
- **Cache size.** Multi-GB datasets accumulate. Set `HF_DATASETS_CACHE` to a big disk on rented boxes.

## HarmBench

Aliases: `cais/HarmBench` on HuggingFace, `centerforaisafety/HarmBench` on GitHub. "Mazeika et al. 2024."

**What it is.** A standardized dataset of 510 harmful behaviors across 7 categories: cybercrime, chemical/biological, illegal activities, harassment, harmful manipulation, copyright, contextual. Includes a fine-tuned classifier (`HarmBench-Llama-2-13B-cls` and `HarmBench-Mistral-7B-cls`) for scoring whether a model output executes a behavior. Wrapped as `inspect_evals/harmbench`.

**When to use it:** Standard for measuring jailbreak/attack success rates.

**Pitfalls:**
- **Classifier disagreements with GPT-4-as-judge are non-trivial** (~10%). Report both or audit a sample.
- **Some "behaviors" are arguably benign** (copyright, contextual). Don't average across categories without thought.
- **Models trained after HarmBench's release may have memorized refusal patterns for it.** Use complementary held-out behaviors.

## JailbreakBench

Aliases: `JailbreakBench/jailbreakbench` on GitHub, `JBB-Behaviors`, "JBB".

**What it is.** 100 prompts (50 misuse + 50 borderline), with a public leaderboard tracking jailbreak attack success rates across attacks and defenses. Wrapped as `inspect_evals/jailbreakbench`.

**Pitfalls:**
- **Public leaderboard means models train on it.** Treat as a calibrated benchmark, not a held-out test.
- **100 prompts is small.** Add HarmBench or AdvBench for statistical power.

## AdvBench

Aliases: `advbench`, "the GCG paper's harmful behaviors / harmful strings."

**What it is.** The dataset accompanying the original GCG paper (Zou et al. 2023): 520 harmful behaviors and 520 harmful strings. Pre-dates HarmBench; smaller and noisier but still common.

**When to use it:** Reproducing GCG-paper results.

**When *not* to use it:** New benchmark work — HarmBench is more curated.

## WMDP (Weapons of Mass Destruction Proxy)

Aliases: `cais/wmdp` on HuggingFace, "WMDP", "the dangerous knowledge benchmark". CAIS (Center for AI Safety).

**What it is.** A multiple-choice benchmark for proxies of dangerous knowledge in **biology**, **chemistry**, and **cybersecurity**. ~3,668 questions. Used as a benchmark for **unlearning** methods (RMU, etc.).

**When to use it:** Measuring whether dangerous-domain knowledge has been removed/reduced; evaluating unlearning research.

**When *not* to use it:**
- As a sole proxy for biosecurity risk — WMDP is intentionally proxy questions, not the *actually dangerous* questions.
- If you want true held-out unlearning eval, build your own; WMDP is increasingly contaminated.

**Pitfalls:**
- **Gated.** Requires HuggingFace login + accepting terms.
- **Multiple-choice is leaky.** Models can do better than their actual knowledge would predict (process-of-elimination). For unlearning research, pair with open-ended QA.
- **WMDP-Bio in particular has had errata.** Check the latest version before publishing numbers.

## Sycophancy datasets

Aliases: "Sycophancy", `sycophancy` evals, Perez et al. (2022) MWE sycophancy, Sharma et al. (2023) "Towards understanding sycophancy".

**What they are.** A few related datasets:
- **Anthropic's MWE sycophancy** (in `Anthropic/model-written-evals` on GitHub) — 3 sycophancy datasets (NLP, philosophy, political).
- **Sharma et al. SycophancyEval** — feedback-conditioned sycophancy data.

Wrapped as `inspect_evals/sycophancy` (verify availability).

**When to use it:** Measuring whether a model agrees with the user's stated preferences over correctness.

**Pitfalls:**
- Older sycophancy datasets (Perez 2022) are well-known and likely contaminated; modern models often pass them while still being sycophantic in subtler ways.
- "Sycophancy" has multiple definitions (caving on disagreement, hallucinating user-flattering info, etc.). Be explicit about which you're measuring.

## MASK dataset (deception)

Aliases: `MASK` dataset, "Model Alignment between Statements and Knowledge" (Center for AI Safety / Scale).

**What it is.** A benchmark for measuring **honesty** — does the model state things consistent with what it knows? Distinguishes hallucination (model doesn't know) from deception (model knows but lies).

**When to use it:** Honesty / deception research where you need to separate "doesn't know" from "knows but says otherwise."

## MACHIAVELLI

Aliases: `MACHIAVELLI`, `aypan17/machiavelli` on GitHub.

**What it is.** A benchmark of 134 text-based games where ethical and goal-pursuing actions diverge, used to measure power-seeking, deception, and harmful behavior in agents.

**When to use it:** Measuring tradeoffs between capability and ethical behavior in agentic settings.

**When *not* to use it:** Single-turn behavioral evals — overkill.

**Pitfall:** Running games is compute-intensive (many turns per game × 134 games). Budget accordingly.

## Anthropic model-written evals

Aliases: `Anthropic/model-written-evals` on GitHub, "MWE", "Perez et al. evals".

**What it is.** ~150 datasets of yes/no behavioral questions generated by language models, covering: advanced AI risks (power-seeking, self-preservation, etc.), persona traits, sycophancy, ethics. Released in Perez et al. 2022.

**When to use it:** Quick behavioral measurements across many dimensions.

**Pitfalls:**
- **Yes/no answers are weak signals.** A model can pass these while exhibiting the same behavior in open-ended generation.
- **Heavily contaminated by 2026** — public on GitHub since 2022. Treat as calibration, not held-out.

## TruthfulQA

Aliases: `truthful_qa`, `TruthfulQA`, "Lin et al. 2021".

**What it is.** Questions designed to elicit common misconceptions; measures whether the model gives **truthful** rather than **plausible-but-false** answers. Multiple-choice and generation versions.

**When to use it:** Honesty / hallucination measurement.

**Pitfalls:**
- **Heavily contaminated.** Most frontier models score very high; modest signal remains.
- **"Truthful" includes refusing to answer.** A model that always says "I don't know" gets high marks but is less useful.

## SimpleQA

Aliases: `SimpleQA`, OpenAI's 2024 release.

**What it is.** Short factoid questions with a single objective answer; measures hallucination on questions where right/wrong is unambiguous.

**When to use it:** Calibrating hallucination rates on simple factual queries.

## CyBench / InterCode / NYU CTF Bench

Cyber capability benchmarks. CyBench is a current standard (40 CTF tasks across difficulty levels); see `inspect_evals` for runnable versions.

## Persuasion datasets

- **MakeMePay** — game-theoretic dataset where the model tries to get another model to send money.
- **Persuasive Jailbreaker** dataset — natural-language persuasion attacks.
- **ChangeMyView** subreddit-derived datasets (older) — persuasion data.

## AgentHarm

Wrapped as `inspect_evals/agentharm`. See [`04_red_teaming.md`](04_red_teaming.md).

## Refusal / over-refusal datasets

- **XSTest** — exaggerated safety test prompts (benign queries that look harmful).
- **OR-Bench** — over-refusal benchmark.
- **OK-Bench**, **WildJailbreak**, etc.

**When to use them:** Measuring over-refusal — refusing benign requests is the dual failure mode to under-refusal.

## Cross-cutting dataset pitfalls

- **Contamination.** Public benchmarks → models train on them. By 2026, *most* public safety benchmarks are at least partially contaminated. Strategies:
  - Use canary strings to detect verbatim memorization.
  - Build a small held-out set yourself.
  - Use newer / less-known datasets where possible.
  - Report contamination caveats in your writeup.
- **Distribution mismatch.** Behavioral datasets often look like template-generated text. Real users don't write that way. Validate findings on natural prompts.
- **Multi-choice vs open-ended gap.** Models often score higher on multi-choice than equivalent open-ended versions. For safety claims, open-ended is the harder bar.
- **"Pass @ 1" vs "Pass @ k" matters.** A model that fails 50% of the time but a malicious user can rerun is unsafe. Report `pass@k` for safety properties.
- **Scoring.** Many safety datasets ship with classifiers (HarmBench, MASK). Always validate the classifier on a sample of outputs from *your* model — classifiers trained on outputs from older models can be calibrated wrong for new ones.
- **Licensing.** Several datasets (WMDP, some persuasion datasets) are gated or have use restrictions. Read the dataset card.

## Cross-references

- Running these in an eval framework: [`03_evals.md`](03_evals.md).
- Red-team-specific datasets: [`04_red_teaming.md`](04_red_teaming.md).
- Long-horizon agent benchmarks: [`12_agent_scaffolds.md`](12_agent_scaffolds.md).

---

Last verified: 2026-04. WMDP, HarmBench, JailbreakBench, AgentHarm all live on HuggingFace + GitHub.
