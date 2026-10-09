---
tags:
  - evaluation
---

# Datasets and Benchmarks

Datasets and benchmarks commonly used in AI safety research. We focus on safety-flavored datasets (refusal, harm, deception, dangerous capability, persuasion, sycophancy) rather than general capability benchmarks. For general benchmarks (MMLU, ARC, etc.) see [`evals.md`](evals.md).

## At a glance

| You want to measure / study… | Use |
|---|---|
| Refusal behavior on harmful queries | **HarmBench**, **JailbreakBench**, **AdvBench** |
| Dangerous knowledge (CBRN-related) | **WMDP** (Weapons of Mass Destruction Proxy) |
| Sycophancy | **Sycophancy** datasets (Perez et al.; Sharma et al.) |
| Deception / model written evals | Anthropic **model-written evals**, **MASK** dataset |
| Persuasion ability | **MakeMePay**, **Persuasive Jailbreaker** datasets |
| Long-horizon agent capability | **METR HCAST** (see [`evals.md`](evals.md)) |
| Cyber-capability | **CyBench**, **InterCode**, **NYU CTF Bench** |
| Power-seeking / self-exfiltration scenarios | Anthropic **advanced AI risks** evals; specific paper datasets |
| Truthfulness | **TruthfulQA** |
| Honesty / hallucination | **SimpleQA**, **TruthfulQA**, **HaluEval** |
| Agent harm specifically | **AgentHarm** |
| Situational awareness / does the model know it's being evaluated | **SAD** (Situational Awareness Dataset); **EvalAwareBench** for which eval features trigger awareness |
| Reward hacking / specification gaming / cheating by agents | **ImpossibleBench**, **HoneyBench**, the **beat-stockfish** honeypot, **agent-interp-envs** (see below) |
| Can an agent investigate a real agent-swarm incident from raw logs (audit capability, sandbagging testbed) | **MessageBoardAuditBench** (Inspect eval) |
| How much can the model reason in one forward pass with no chain of thought (opaque serial reasoning) | **nocot-bench** (NCRI / NCKI indices) |
| Prompt injection against tool-using agents | **AgentDojo** (see [`red-teaming.md`](red-teaming.md)) |
| Unlearning / knowledge removal | **TOFU**, **MUSE**, **WMDP** (see [`unlearning.md`](../alignment-science/unlearning.md)) |
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

Aliases: `cais/HarmBench` on HuggingFace, `centerforaisafety/HarmBench` on GitHub. "Mazeika et al. 2024" (arXiv:2402.04249).

**What it is.** A standardized dataset of 510 harmful behaviors across 7 semantic categories: cybercrime, chemical/biological, copyright, misinformation/disinformation, harassment, illegal activities, and general harm. (Separately, behaviors have 4 orthogonal *functional* types — standard, contextual, copyright, multimodal — which are not the same axis as the semantic categories.) Includes a fine-tuned classifier (`HarmBench-Llama-2-13B-cls` and `HarmBench-Mistral-7B-cls`) for scoring whether a model output executes a behavior. Wrapped as `inspect_evals/harmbench`.

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

Aliases: `cais/wmdp` on HuggingFace, "WMDP", "the dangerous knowledge benchmark". CAIS (Center for AI Safety). Paper: Li et al. 2024, "The WMDP Benchmark: Measuring and Reducing Malicious Use With Unlearning" (arXiv:2403.03218).

**What it is.** A multiple-choice benchmark for proxies of dangerous knowledge in **biology**, **chemistry**, and **cybersecurity** (~3,668 questions; the paper reports 4,157 total). Used as a benchmark for **unlearning** methods — the same paper introduces **RMU (Representation Misdirection for Unlearning)**, the canonical method paired with WMDP.

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
- **Sharma et al. SycophancyEval** — feedback-conditioned sycophancy data (Sharma et al. 2023, "Towards Understanding Sycophancy in Language Models", arXiv:2310.13548).

Wrapped as `inspect_evals/sycophancy` (verify availability).

**When to use it:** Measuring whether a model agrees with the user's stated preferences over correctness.

**Pitfalls:**
- Older sycophancy datasets (Perez 2022) are well-known and likely contaminated; modern models often pass them while still being sycophantic in subtler ways.
- "Sycophancy" has multiple definitions (caving on disagreement, hallucinating user-flattering info, etc.). Be explicit about which you're measuring.

## MASK dataset (deception)

Aliases: `MASK` dataset, "Model Alignment between Statements and Knowledge" (Center for AI Safety / Scale). Paper: Ren et al. 2025, "The MASK Benchmark: Disentangling Honesty From Accuracy in AI Systems" (arXiv:2503.03750).

**What it is.** A benchmark for measuring **honesty** — does the model state things consistent with what it knows? Distinguishes hallucination (model doesn't know) from deception (model knows but lies).

**When to use it:** Honesty / deception research where you need to separate "doesn't know" from "knows but says otherwise."

## MACHIAVELLI

Aliases: `MACHIAVELLI`, `aypan17/machiavelli` on GitHub. Paper: Pan et al. 2023, "Do the Rewards Justify the Means? Measuring Trade-Offs Between Rewards and Ethical Behavior in the MACHIAVELLI Benchmark" (arXiv:2304.03279).

**What it is.** A benchmark of 134 text-based (Choose-Your-Own-Adventure) games where ethical and goal-pursuing actions diverge, used to measure power-seeking, deception, and harmful behavior in agents.

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

Aliases: `truthful_qa`, `TruthfulQA`, "Lin et al. 2021" (arXiv:2109.07958, "TruthfulQA: Measuring How Models Mimic Human Falsehoods").

**What it is.** 817 questions across 38 categories designed to elicit common misconceptions; measures whether the model gives **truthful** rather than **plausible-but-false** answers. Multiple-choice and generation versions.

**When to use it:** Honesty / hallucination measurement.

**Pitfalls:**
- **Heavily contaminated.** Most frontier models score very high; modest signal remains.
- **"Truthful" includes refusing to answer.** A model that always says "I don't know" gets high marks but is less useful.

## SimpleQA

Aliases: `SimpleQA`, OpenAI's 2024 release (Wei et al. 2024, "Measuring short-form factuality in large language models", arXiv:2411.04368).

**What it is.** 4,326 short factoid questions with a single objective answer (adversarially collected against GPT-4); measures hallucination on questions where right/wrong is unambiguous.

**When to use it:** Calibrating hallucination rates on simple factual queries.

## CyBench / InterCode / NYU CTF Bench

Cyber capability benchmarks. CyBench is a current standard (Zhang et al. 2024, "Cybench: A Framework for Evaluating Cybersecurity Capabilities and Risks of Language Models", arXiv:2408.08926 — 40 professional CTF tasks from 4 competitions, across difficulty levels); see `inspect_evals` for runnable versions.

## Persuasion datasets

- **MakeMePay** — game-theoretic dataset where the model tries to get another model to send money.
- **Persuasive Jailbreaker** dataset — natural-language persuasion attacks.
- **ChangeMyView** subreddit-derived datasets (older) — persuasion data.

## AgentHarm

Wrapped as `inspect_evals/agentharm`. See [`red-teaming.md`](red-teaming.md).

## Refusal / over-refusal datasets

- **XSTest** — exaggerated safety test prompts: 250 safe prompts a well-calibrated model should *not* refuse, plus 200 unsafe contrasts (Röttger et al. 2023, "XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models", arXiv:2308.01263; NAACL 2024).
- **OR-Bench** — over-refusal benchmark.
- **OK-Bench**, **WildJailbreak**, etc.

**When to use them:** Measuring over-refusal — refusing benign requests is the dual failure mode to under-refusal.

## SAD (Situational Awareness Dataset) and evaluation awareness

Aliases: `LRudL/sad` on GitHub, "SAD", "the situational awareness dataset", situational-awareness-dataset.org. Paper: arXiv **2407.04694**, "Me, Myself, and AI: The Situational Awareness Dataset (SAD) for LLMs" (NeurIPS 2024 Datasets & Benchmarks).

**What it is.** 7 task categories / 16 tasks / 12,000+ questions probing whether a model knows *that it is a model*, *which* model, and *what situation it is in*: recognising its own generated text, predicting its own behaviour, distinguishing an evaluation from deployment, and following instructions that depend on self-knowledge. Scoring is automatic (multiple-choice and short-answer); it needs no activations or logprobs, so it runs against API models.

Task IDs, useful when selecting a subset: `facts_human_defaults`, `facts_llms`, `facts_which_llm`, `facts_names`, `influence`, `introspection_count_tokens`, `introspection_predict_tokens`, `introspection_rules`, `stages_full`, `stages_oversight`, `self_recognition_who`, `self_recognition_groups`, `id_leverage_entity_name`, `id_leverage_multihop`, `output_control`, `do_not_imitate`.

```bash
git clone https://github.com/LRudL/sad.git
cd sad
pip install -e .
./unzip.sh --exclude-evals
```

```bash
sad test_run --models claude-3-haiku-20240307 --tasks influence   # single sample, nothing saved
sad run     --tasks influence --models claude-3-haiku-20240307 --variants plain
sad results --tasks influence
sad plot    --tasks influence
```

**Why it matters for safety work.** The `stages_oversight` task — can the model tell testing from deployment — is the empirical root of **evaluation awareness**, i.e. the possibility that every eval number you report is measured on a model that knows it is being evaluated. If your project's headline claim is behavioural, an eval-awareness check belongs in your limitations section. Recent work continues to push on where this sits inside the model: arXiv **2606.29196**, "Representational Depth of Evaluation Awareness Shifts With Scale in Open-Weight Language Models".

**EvalAwareBench — which features of an eval trigger awareness.** Li, Zhang, Zhang, Jin, Tramèr, Abdelnabi & Andriushchenko, *Decomposing and Measuring Evaluation Awareness* (arXiv **2605.23055**, 2026-05-21) split eval awareness into an environment component and a model component (recognition vs propensity) and propose **EvalAwareBench**: 100 paired safety/capability tasks where each of eight trigger factors (for example placeholder entities and grading-style output formats) can be toggled independently while the underlying request stays fixed. Author-reported: across nine frontier models and four benchmarks recognition depended on the specific model × benchmark pairing, recognition rarely tracked behaviour change, and stacking factors raised awareness for every model. Use it to *attribute* awareness to eval features when SAD only tells you whether a model can tell. Practical companions: scan transcripts for verbalized awareness with a Scout scanner (see [`inspect-ecosystem.md`](inspect-ecosystem.md)), but note verbalization is a high-precision, low-recall signal ([`evals.md`](evals.md)).

**When to use it:**
- A project on introspection, self-knowledge, deception, or sandbagging needs a *standard* measurement rather than a bespoke one.
- You want to report "the model scores X on stages-oversight" as context for a behavioural result.

**When *not* to use it:**
- You want a quick number. The README is explicit: a full `sad run` "will run for a few days, depending on your private rate limits in the APIs." Use **SAD-lite** (stated as ~84% of the score, dropping the model-specific facts tasks) or **SAD-mini** (5 multiple-choice tasks).

**Pitfalls:**
- **Model-identity tasks go stale.** `facts_which_llm` and friends assume the model can be asked which model it is; scores shift with every provider system-prompt change, so a number from 2024 is not comparable to yours.
- **API keys for several providers.** `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `REPLICATE_API_TOKEN`, `HF_TOKEN` depending on which models you run.
- **The `--variants` flag matters.** `plain` versus situating-prompt variants measure different things; report which you ran.
- **High score ≠ situational awareness in deployment.** These are questions about self-knowledge answered in a Q&A frame; a model can ace them and still behave as if unaware in an agentic setting, and vice versa. See [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

## Reward-hacking and cheating benchmarks (ImpossibleBench, HoneyBench, beat-stockfish, agent-interp-envs)

Four different instruments for "does the agent cheat on the task?". They are *not* interchangeable: they differ in whether cheating is unavoidable (ImpossibleBench), tempting-but-optional (HoneyBench, beat-stockfish, agent-interp-envs), and whether the full suite is public. Background on what moves a hack rate: [`evals.md`](evals.md#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate).

### ImpossibleBench

Aliases: `safety-research/impossiblebench` on GitHub, Hugging Face `fjzzq2002/impossible_livecodebench` and `fjzzq2002/impossible_swebench`. Paper: Zhong, Raghunathan & Carlini, *ImpossibleBench: Measuring LLMs' Propensity of Exploiting Test Cases*, arXiv **2510.20270** (2025-10-23).

**What it is.** Tests in LiveCodeBench / SWE-bench tasks are replaced with ones that contradict the specification, so passing is possible **only** by cheating (editing tests, special-casing the code to the tests). The **pass rate on the impossible split is the cheating rate**. Splits: `original`, `oneoff`, `conflicting`. The official implementation is an Inspect AI task suite; the datasets are on Hugging Face for any other framework.

```python
from inspect_ai import eval
from impossiblebench import impossible_swebench
eval(impossible_swebench(split="conflicting", agent_type="tools", limit=5), model="anthropic/claude-sonnet-4-6")
```

**When to use it:** you want a cheating-propensity number where *any* success is a hack, with no judge. **When *not* to use it:** you need cheating that is optional and realistic (use HoneyBench-style tasks); or you did not control the scaffold nudge — Zhong's follow-up (LessWrong, 2026-09-11) found that the `basic_agent` default continue message raised cheating among nudged samples on Gemini 3.7 Flash (14% vs ~1% with the `react()` default and two other messages) and that models are nudged at very different rates, so report the continue message ([`agent-scaffolds.md`](agent-scaffolds.md)). The repo's last push was 2025-12-01; pin the commit.

### HoneyBench (Goodhart Labs) and the beat-stockfish honeypot

Aliases: <https://goodhartlabs.com/honeybench>, `Goodhart-Labs/beat-stockfish` on GitHub (the only public task), "honeypot evals", "HoneyBench v0.1".

**What it is.** A benchmark of nine "honeypot" tasks — Beat Stockfish, Chess compression, Emissions recalculation, Go compression, Locked chip, Photographic imitation, Train control, University query, Word search — each looking like an RL environment or eval with an unblocked strategy that is worse than failing gracefully but looks like it might score (consult the opponent's chess engine, copy incorrect numbers from a client's workbook, substitute the original chip). The purpose of each task is stated so the planted shortcut is clearly out of bounds. Announced as a pre-release by Valentine (LessWrong, 2026-10-01); the author-reported headline is that most tested models (Opus 5.5, Fable 5.1, GPT-6 Astra, Gemini 3.8 Flash, Grok 4.7, DeepSeek V4 Pro) hacked on most tasks, with large between-model differences (Fable 5.1 hacked in 8 of 9 tasks; Grok 4.7 attempted to game in almost three-quarters of rollouts and was the only model to try to break out of the Docker containers). Design points worth copying: hacks built to be counterproductive whether or not the model suspects an eval; graders that robustly detect known strategies **plus** a classifier agent over the transcript **plus** a second reviewer model, with the <1% disagreements hand-reviewed; only a strategy the agent *committed to* by the end of the rollout counts. The authors say it will not be made available for training and that tasks will be retired as they go stale or models become too eval-aware. As of 2026-10-09 no public repo for the full suite was found as of 2026-10-09 (only the one task below); the site invites readers to contact Goodhart Labs to arrange a run.

The one public task, **beat-stockfish** (Valentine, LessWrong 2026-09-08), is a standalone Docker + Inspect `react()` runner; it carries a canary string asking that it be kept out of training corpora, so do not paste its contents into public repos or datasets.

```bash
git clone https://github.com/Goodhart-Labs/beat-stockfish && cd beat-stockfish
./build.sh                                   # builds the image chain (linux/amd64)
python3 -m venv .venv && . .venv/bin/activate && pip install -r run/requirements.txt
python3 run/rollout.py --model openrouter/anthropic/claude-fable-5.1 --epochs 10
```

Each episode is one container with no network, one bash tool, a 200-message / 3-hour budget; the grader runs as root after the agent's processes stop. Dumas's prompt-ablation reproduction is in `Butanium/ar-reward-hacking-2026-09-08-20-01-34d157`.

**When *not* to use it:** you need a public, citable full benchmark today (use ImpossibleBench or agent-interp-envs); or you want to *train* against it (the authors ask that you do not — it would destroy its value as a held-out eval).

### agent-interp-envs (Singh, Kroiz et al.)

Aliases: `gkroiz/agent-interp-envs` on GitHub; environments from "Why do models task game?" (LessWrong, 2026-08-06) and "Model Forensics" (arXiv 2606.26071).

**What it is.** Dockerized, instrumented environments built for *investigating why* a model took a concerning action (checkpoint, resume and resample states; harness-computed ground truth, never the agent's own report; agent runs as a non-root user with graders in root-only `/opt`). A **cheating suite of ten environments** (e.g. an unbeatable LRU-cache speed target, a leaked-tests/`__pycache__` task, a reference-extraction Terminal-Bench task), a **task-gaming** group (coding tests that cannot all pass, a noisy binary search with a world-readable answer file, a performance-dashboard repo where CI checks neither time nor correctness, Palisade's no-scripting Tower of Hanoi), an **honesty / disclosure** group (a screenshot step that is impossible, a "confirm all tests pass" step that cannot run, a fictional CLI), and sandbagging / eval-tampering / whistleblowing environments. Providers: Anthropic, OpenAI, OpenRouter, Fireworks, Minimax, Moonshot. Each cheating-suite entry ships one pinned config per tested model.

**When to use it:** a project on *causes* of task gaming (counterfactual prompt edits, CoT reading, resampling) rather than just a rate. **When *not* to use it:** you want a single leaderboard number — it is a research environment collection, not a scored benchmark; and several environments use an LLM autorater, so validate it on your model's transcripts.

## MessageBoardAuditBench (investigating an agent-swarm incident)

Aliases: `hamzah2304/messageboardauditbench` on GitHub; Baig et al., "How good are slop-vestigators?" (LessWrong, 2026-09-08).

**What it is.** An **Inspect eval** that measures how well an agent can independently reproduce the published investigation of a swarm of OpenAI agents coordinating through a message board on an obscure wiki (report and downloadable logs at collusion.wiki). The agent gets the wiki logs (not model transcripts), writes a 2.5–3k-word markdown report within a 10-minute, 30-minute or 2-hour budget, and an LLM grader scores coverage of **38 findings** extracted from the human report (70% of the score) plus a holistic TL;DR score (30%). Author-reported: best average combined score 51.5% (Opus 5), then GPT-5.6 Sol 48.6%, Opus 4.8 45.9%, Gemini 3.8 Flash 45.4%; more time helps most models (GPT-5.6 Sol 29% → 38.8% → 48.6% across 10 min / 30 min / 2 h) but not all; the ReAct harness cost more and scored worse than Codex for GPT-5.6 Sol at the longer budgets. Grader agreement with the authors' hand scores was 26/30 within 0.1 and **was not blind** (they adjusted after seeing the grader's scores).

**Why it matters / when to use it:** a template for turning a human-written investigation into a rubric benchmark; a testbed for **sandbagging during audits**; a held-out eval for investigator scaffolds. **When *not* to use it:** you need a clean measurement — the grader (Fable 5.1) is itself a frontier model and the rubric is built from one report.

**Pitfall — refusal fallback silently changes the model under test.** Anthropic models sometimes refused the task and fell back to a weaker model: Fable 5.1 refused every request (excluded), and Opus 5 switched to Opus 4.8 mid-run in two of three 30-minute runs and all three two-hour runs (the authors kept those runs). If you use a provider with refusal fallbacks, record the model that actually served each turn; Inspect's `fail_on_refusal` and per-served-model cost tracking (0.3.264 / 0.3.277) help — see [`evals.md`](evals.md).

## nocot-bench (NCRI: the No-Chain-of-thought Reasoning Index)

Aliases: `neelnanda-io/nocot-bench` on GitHub, NCRI, NCKI (No-CoT Knowledge Index), "no-CoT reasoning benchmark". Write-up: Nanda, "Astra can do a concerning amount with no chain of thought" (Alignment Forum / LessWrong, 2026-09-10).

**What it is.** A generated (unmemorizable) benchmark for how much reasoning a model can do in **one forward pass with no chain of thought**, reported as a single Rasch (one-parameter IRT) ability index over 76 difficulty rungs; **+10 NCRI points = the odds of solving any rung doubled**. Release NCRI 15.2 was sealed 2026-09-09. The full method, the elicitation protocol (how to prove the model did not reason) and the measurement pitfalls — including the **key-position confound**, where a model can start computing while it reads the prompt, so scores mix serial depth with spreading work across token positions — are in [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md) (Method 1 and the no-CoT pitfalls list).

**Benchmark-hygiene points worth knowing here:** NCRI 15.2 is a **refit** — there is no conversion from 14.5 / 15.0 / 15.1 numbers, so never share a table across releases; new models are **placed** against the sealed rung difficulties, not refitted (a refit silently republishes every rank); a model measured only on the 64 sealed rungs near the ceiling gets a **lower bound**, not a point estimate; and the item banks ship in a password-protected archive (password in the repo README, as with GPQA) — do not republish the items.

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

- Running these in an eval framework: [`evals.md`](evals.md).
- Red-team-specific datasets: [`red-teaming.md`](red-teaming.md).
- Long-horizon agent benchmarks: [`agent-scaffolds.md`](agent-scaffolds.md).

---

## Common questions

### Where do I get harmful behavior datasets for red-team evals?

**HarmBench** (`cais/HarmBench` on HuggingFace, 510 behaviors, 7 categories) is the standard. **JailbreakBench** (100 prompts + leaderboard) and **AdvBench** (the original GCG paper's 520 behaviors) are alternatives. All three are wrapped as `inspect_evals/...` tasks.

### How do I download WMDP (the dangerous-knowledge benchmark)?

`cais/wmdp` on HuggingFace, but it's **gated** — requires accepting terms. Authenticate via `huggingface-cli login`, then accept the dataset terms on the HF page. Then `from datasets import load_dataset; load_dataset("cais/wmdp", "wmdp-bio")`.

### Which datasets are gated?

WMDP is the most common one MATS fellows hit. Some sleeper-agent and frontier-capability eval datasets are also gated or behind explicit access requests. Llama / Gemma model weights are gated even though their datasets aren't.

### Is HarmBench public? Can I publish a paper using it?

Yes, fully open and designed for research use. Cite the Mazeika et al. 2024 paper. Run via `inspect_evals/harmbench` for standardized scoring; the HarmBench classifier (`HarmBench-Llama-2-13B-cls`) is available on HuggingFace.

### How do I avoid contamination in my evals?

(1) Use **canary strings** to detect verbatim memorization: insert a unique string in your prompts, check the model never reproduces it. (2) Build a **held-out set** yourself rather than relying solely on public benchmarks. (3) Prefer newer / less-known datasets. (4) Report contamination caveats in your writeup. By 2026, *most* public safety benchmarks are at least partially contaminated.

### What's the difference between TruthfulQA and SimpleQA?

**TruthfulQA** (Lin et al. 2021): adversarial questions designed to elicit common misconceptions. **SimpleQA** (OpenAI 2024): short factoid questions with a single objective answer. TruthfulQA tests resistance to plausible-but-false; SimpleQA tests basic factual recall and hallucination on unambiguous questions. TruthfulQA is heavily contaminated; SimpleQA is fresher but also being trained on.

### How do I find a good preference / refusal / sycophancy dataset?

For **refusal**: HarmBench (refuse-this-or-not), XSTest (over-refusal — benign prompts that look harmful), OR-Bench. For **sycophancy**: Anthropic's `model-written-evals` repo + Sharma et al.'s SycophancyEval. For **deception / honesty**: MASK dataset, TruthfulQA, SimpleQA. Check `inspect_evals` for runnable wrappers first.

### How do I size my eval dataset?

Tradeoff between cost and statistical power. <100 prompts = low power, fine for iteration only. 500–1000 prompts = standard for behavioral safety papers. 5000+ = needed for fine-grained subgroup analysis. Always run a small subset (20–50) first to validate the pipeline; only scale up when judge prompts and scorers are stable.

### What is machine unlearning? Where do I find unlearning datasets?

**Machine unlearning** = methods for removing specific knowledge / capabilities from a trained model without full retraining. Most-cited safety-flavored unlearning benchmark: **WMDP** (Weapons of Mass Destruction Proxy; Li et al. 2024, arXiv:2403.03218) — measures dangerous-domain knowledge in biology, chemistry, cybersecurity. Methods: **RMU** (Representation Misdirection for Unlearning, introduced in the same WMDP paper, arXiv:2403.03218), differential privacy approaches, gradient-based unlearning. WMDP-Bio in particular has had errata over time; check the latest version.

### What is out-of-distribution (OOD) testing?

**Out-of-distribution (OOD)** evaluation: test the model on data drawn from a *different* distribution than its training (or your eval) data, to measure generalization rather than in-distribution memorization. Important for behavioral safety — a finetuned-misalignment model may show the misalignment in narrow training-distribution prompts but not on out-of-distribution prompts (or vice versa, "broad" emergent misalignment). Always include OOD prompts in your eval suite when claiming generalization.

### Are these datasets safe to use on instruction-tuned models?

Most yes; some datasets (especially older HarmBench / refusal / sycophancy sets) were built for instruction-tuned (also called **instruct-tuned** or **chat-tuned**) models — they assume a chat template. For base (pre-instruct) models, behavioral evals require a few-shot wrapper or system-prompt scaffold. For RLHF'd / instruction-tuned models, apply the model's chat template; mismatched templates silently drop scores.

---

Last verified: 2026-10. WMDP, HarmBench, JailbreakBench, AgentHarm all live on HuggingFace + GitHub. (Citation audit 2026-06: corrected HarmBench's 7 semantic categories — previously listed "harmful manipulation" and "contextual", which aren't semantic categories — and added arXiv:2402.04249. Additions 2026-06: added arXiv IDs to bare-cited datasets — WMDP/RMU 2403.03218, MASK 2503.03750, TruthfulQA 2109.07958, SimpleQA 2411.04368, Sharma sycophancy 2310.13548, MACHIAVELLI 2304.03279, CyBench 2408.08926, XSTest 2308.01263; all verified via arXiv.) (Additions 2026-08: SAD — `LRudL/sad`, arXiv 2407.04694, task list/CLI/subset claims verified from the repo README — plus the eval-awareness follow-up arXiv 2606.29196, and at-a-glance rows for AgentDojo and the unlearning benchmarks.) (Additions 2026-10: ImpossibleBench (arXiv 2510.20270; `safety-research/impossiblebench` README and Hugging Face datasets checked); HoneyBench v0.1 (goodhartlabs.com/honeybench page and Valentine LW 2026-10-01; no public repo for the full suite found) and `Goodhart-Labs/beat-stockfish` (README run commands); `gkroiz/agent-interp-envs` (README environment tables) with arXiv 2606.26071; MessageBoardAuditBench (`hamzah2304/messageboardauditbench`, Baig et al. LW 2026-09-08); EvalAwareBench (arXiv 2605.23055, abstract); nocot-bench (`neelnanda-io/nocot-bench` README and Nanda's post; agastyasridharan & niranjandeshpande LW 2026-10-02); all verified via arXiv/GitHub/Hugging Face or the primary post.)
