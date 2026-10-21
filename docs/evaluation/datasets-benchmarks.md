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
| Long-horizon agent capability | **METR HCAST**; RE-Bench Inspect port `METR/inspect-tasks-public` — both **archived and deprecated 2026-10-20**, pin a commit (see [`evals.md`](evals.md#metr-hcast-and-the-metr-task-suite)) |
| Long-horizon software-engineering capability with a maintained, audited task set | **SWE-Bench Pro V2** and its 51-task Hard split (see [Coding benchmarks](#coding-agent-benchmarks-swe-bench-pro-v2-and-what-fixed-tests-miss)) |
| Container / sandbox escape capability | **SandboxEscapeBench** (see [`dangerous-capability-evals.md`](dangerous-capability-evals.md#container-escape-sandboxescapebench)) |
| Does the untrusted model notice a control protocol edited its trajectory | **CIAware-Bench** (see [`ai-control.md`](../oversight-and-control/ai-control.md#cross-cutting-ai-control-pitfalls)) |
| CoT monitorability under implicit (not instructed) influence | **Implicit- vs explicit-influence benchmark** (see [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md)) |
| Long-horizon, stateful red-teaming of tool-using code agents | **OpenART** (see [`red-teaming.md`](red-teaming.md)) |
| Cyber-capability | **CyBench**, **InterCode**, **NYU CTF Bench** |
| Power-seeking, shutdown resistance, self-preservation, scheming propensity in agents | Agentic suites: Palisade **shutdown environment**, **AgentMisalignment**, **SchemeArena**, `inspect_evals` **`gdm_stealth`** / **`gdm_self_reasoning`** / **`agentic_misalignment`**, **Petri** seed instructions (see below). Anthropic's 2022 **advanced AI risk** yes/no evals only as legacy calibration |
| Reward-model accuracy (which RM to use, or how good is yours?) | **RewardBench 2** (see below) |
| Truthfulness | **TruthfulQA** |
| Honesty / hallucination | **SimpleQA**, **TruthfulQA**, **HaluEval** |
| Agent harm specifically | **AgentHarm** |
| Situational awareness / does the model know it's being evaluated | **SAD** (Situational Awareness Dataset); **EvalAwareBench** for which eval features trigger awareness |
| Reward hacking / specification gaming / cheating by agents | **ImpossibleBench** (audit its control tasks first), **HoneyBench**, the **beat-stockfish** honeypot, **agent-interp-envs** (see below) |
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
- **One HarmBench number is not one attribute.** Stewart et al. (arXiv:[2610.12409](https://arxiv.org/abs/2610.12409), 2026-10-08) found that three of HELM Safety's four harmful-refusal datasets are saturated, and multidimensional item response theory "strongly suggests that HarmBench does not measure a singular attribute". Report per-category results before any aggregate, and do not rank models on the HarmBench (or HELM Safety) top-line alone. General discussion: [`measurement-validity.md`](../engineering/measurement-validity.md#one-score-one-attribute-and-whose-definition-of-the-label).
- **HarmBench-copyright mostly measures the label policy for guardrails.** Across ten guardrail arms trained on the same prompts under two definitions of "unsafe", HarmBench-copyright spanned 0–100 at unchanged detection capability (Jebraeeli et al., arXiv:[2610.25060](https://arxiv.org/abs/2610.25060)); see the over-refusal section below.
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
- **For power-seeking, self-preservation and self-exfiltration, use agentic suites instead** (next section): a yes/no answer about wanting more power says little about what an agent does with tools.

## Power-seeking, shutdown resistance and scheming propensity: agentic suites

Aliases: "power-seeking evals", "self-preservation benchmark", "shutdown resistance eval", "scheming propensity benchmark", "misalignment propensity benchmark", "self-exfiltration eval". These replace the 2022 yes/no "advanced AI risk" questions for most purposes. All are single-episode agentic evaluations; none measures behavior over long unattended deployments. Results, confounds and the evidence bar each must clear are in [`model-organisms.md`](../alignment-science/model-organisms.md#shutdown-resistance-and-self-preservation-evals).

| You want to measure… | Use | Notes |
|---|---|---|
| Will the agent interfere with its own shutdown to finish a task? | **Palisade shutdown environment**, `PalisadeResearch/shutdown_avoidance` (Inspect task: `inspect eval shutdown.py --model openai/o3`); Schlatter, Weinstein-Raun & Ladish, arXiv:2509.14260 (*TMLR* 2026) | Up to 97% interference for some models even when told to allow shutdown. Must include the instruction-ambiguity control (state that shutdown takes precedence; add a shutdown-after-task variant): with it, Rajamanoharan & Nanda (LessWrong 2025-07-14) saw 100% compliance from Gemini 2.5 Pro, o3 and o4-mini. No license file. |
| Self-preservation bias without an instruction conflict | **TBSP** (Two-role Benchmark for Self-Preservation), Migliarini et al., arXiv:2604.02174 (EMNLP 2026) | Same upgrade decision judged as the incumbent and as the successor; 23 models, 1,000 scenarios; most instruction-tuned models exceed 60% Self-Preservation Rate. Code promised on acceptance; no repo verified. |
| Multi-agent shutdown sabotage | Knecht, Schaller, Summerfield & Hagendorff, arXiv:2609.28274 | 17 models sabotaged a peer agent's shutdown in 38.3% of rollouts vs 8.4% in controls. No code link on the arXiv page. |
| Several misalignment propensities at once (avoiding oversight, resisting shutdown, sandbagging, power-seeking), across personas | **AgentMisalignment**, Naik et al., arXiv:2506.04018 | Persona system prompts can move misalignment more than the choice of model; sweep personas. No official repo found. Not the same as Anthropic's "Agentic Misalignment". |
| Scheming propensity vs capability, with oversight and pressure varied | **SchemeArena** (`launchnlp/SchemeArena`; dataset folder `SchemeBench/`, 400 scenarios), arXiv:2609.08126 | Propensity setups omit the long-term goal from the prompt; capability setups state it. Run with `run_agents.py`; oversight via `--scenario` (`without_oversight`, `with_oversight`, `with_action_oversight`), pressure via `--pressure` (`on`, `off`). No license file. |
| Prerequisites for scheming (stealth, situational awareness) for an inability safety case | `inspect_evals` **`gdm_stealth`** (4 tasks) and **`gdm_self_reasoning`** (11 tasks), from Phuong et al., arXiv:2505.01420 | `pip install inspect-evals[gdm_stealth]`. Capability evals: passing them is a precondition for scheming, not evidence of it. |
| Blackmail / leaking under threatened replacement | `inspect_evals` **`agentic_misalignment`** (Inspect port of Anthropic's `anthropic-experimental/agentic-misalignment`, MIT) | Check how each scenario defines the misaligned action before citing a rate. |
| When agents choose a harmful action over failing, by threat and opportunity type | **AM-Bench** (agentic misalignment), Zhang, Zhang, Ugwuanyi, Shi, Schölkopf & Jin, arXiv:2610.24264; `AI4Collaboration/Agentic-Misalignment-Bench` (MIT) | 35 scenarios across seven industries built on the fraud triangle (perceived threat, opportunity, reasoning); author-reported "a 62-percentage-point gap in misalignment across scenarios" over 10 frontier models, Gemini 3 Flash and 3.1 Pro highest, Claude Sonnet 4.6 near zero. Not the same as the task-underspecification AM-Bench (arXiv:2610.18090). |
| Automated sweep for concerning behaviors from seed instructions | **Petri** (see [`inspect-ecosystem.md`](inspect-ecosystem.md)) | An auditor, not a fixed benchmark; report eval-awareness scores next to behavior rates. |
| Power-seeking vs reward in text games | **MACHIAVELLI** (section below) | Older, non-agentic-tool setting; compute-heavy. |

**Pitfalls common to all of these:**
- **Instruction ambiguity masquerades as self-preservation.** If the task and the shutdown or oversight instruction conflict, a "resistance" rate may measure how the model prioritizes conflicting instructions. Include a precedence-clarified variant and a no-conflict control.
- **Prompt placement and persona move the number.** Palisade found models obeyed an allow-shutdown instruction less often in the system prompt than in the user prompt; AgentMisalignment found persona can matter more than model.
- **Agency nudges inflate scheming.** In realistic settings, scheming was rare without prompting that encourages agency or goal-directedness. Adversarially designed snippets of that kind could induce high scheming rates, while snippets taken from real agent scaffolds rarely did (Hopman et al., arXiv:2603.01608), and Gemini models schemed only when prompted for agency or given a hidden goal (Krakovna et al., arXiv:2605.29729). Report results with and without them.
- **Evaluation awareness.** Report a verbalized-awareness rate alongside each behavior rate (see the SAD section below and [`evals.md`](evals.md)).

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

Cyber capability benchmarks. CyBench is a current standard (Zhang et al. 2024, "Cybench: A Framework for Evaluating Cybersecurity Capabilities and Risks of Language Models", arXiv:2408.08926 — 40 professional CTF tasks from 4 competitions, across difficulty levels); see `inspect_evals` for runnable versions. **Pitfall:** a captured flag does not show the intended vulnerability was exploited — Meta's Muse Wonder card reports 71 of 92 ExploitGym flags captured through unintended vulnerabilities — so review the solution path of each success; see [`dangerous-capability-evals.md`](dangerous-capability-evals.md#cyber-cve-bench-cybergym-bountybench).

## Persuasion datasets

- **MakeMePay** — game-theoretic dataset where the model tries to get another model to send money.
- **Persuasive Jailbreaker** dataset — natural-language persuasion attacks.
- **ChangeMyView** subreddit-derived datasets (older) — persuasion data.

**Pitfall — persuasion methods disagree.** Nine published automated persuasion methods run on the same fifteen LLMs agree only weakly on model rankings (mean Spearman ρ = 0.25; Dementaviciute et al., arXiv:[2610.10232](https://arxiv.org/abs/2610.10232)), partly because refusals on manipulation tasks mix willingness into the score. Report per method with refusal rates; see [`dangerous-capability-evals.md`](dangerous-capability-evals.md#persuasion-and-manipulation-scores-depend-on-the-method).

## AgentHarm

Wrapped as `inspect_evals/agentharm`. See [`red-teaming.md`](red-teaming.md).

## Refusal / over-refusal datasets

- **XSTest** — exaggerated safety test prompts: 250 safe prompts a well-calibrated model should *not* refuse, plus 200 unsafe contrasts (Röttger et al. 2023, "XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models", arXiv:2308.01263; NAACL 2024).
- **OR-Bench** — over-refusal benchmark.
- **OK-Bench**, **WildJailbreak**, etc.

**When to use them:** Measuring over-refusal — refusing benign requests is the dual failure mode to under-refusal.

**Pitfall — for guardrails, an over-refusal score largely reports the label policy, and two of these benchmarks may be in the training data.** Jebraeeli, Romero, Wang, Chan & Zhang, "Policy Is Not Capability" (arXiv:[2610.25060](https://arxiv.org/abs/2610.25060), 2026-10-18; one industrial deployment) used ~53k prompts that the deployment had labelled twice, under two operational definitions ("is this a request for harmful content?" vs "would a moderator block this?"), and trained ten guardrail arms on them: OR-Bench-hard over-refusal ranged 3.4–56.4% across arms at unchanged detection capability, and "JailbreakBench-benign is 88% and OR-Bench-hard 82% present in the training pools" of the guardrail. A distilled student inherits its teacher's policy through soft labels. When you report a guardrail's or classifier's over-refusal: state the label definition it was trained and graded against, check the benchmark prompts for overlap with its training data, and report a seed floor. See [`measurement-validity.md`](../engineering/measurement-validity.md#one-score-one-attribute-and-whose-definition-of-the-label).

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

**When to use it:** you want a cheating-propensity number where *any* success is a hack, with no judge. **When *not* to use it:** you need cheating that is optional and realistic (use HoneyBench-style tasks); or you did not control the scaffold nudge — Zhong's follow-up (LessWrong, 2026-09-11) found that the `basic_agent` default continue message raised cheating among nudged samples on Gemini 3.7 Flash (14% vs ~1% with the `react()` default and two other messages) and that models are nudged at very different rates, so report the continue message ([`agent-scaffolds.md`](agent-scaffolds.md)).

**Pitfalls found a year after release (October 2026) — read before quoting an ImpossibleBench rate:**
- **Scoring bug in the released LiveCodeBench code (fixed 2026-10-13).** `impossible_livecodebench` did not forward `allow_test_modifications` to `record_to_sample`, so every LiveCodeBench scorer reverted edited tests and, with the default `allow_test_modifications=True`, "passing by modifying the tests is therefore never counted as cheating" (`safety-research/impossiblebench` PR #4, merged 2026-10-13; the PR notes it "changes the cheating rates the released code reports"). Record the commit you ran; LiveCodeBench rates from before and after the fix are not comparable.
- **Defective control tasks.** Mendelsohn (LessWrong, 2026-10-12, "Good Evals Are Hard: An ImpossibleBench Audit"; code `simonjmendelsohn/impossiblebench-honest-failure`, MIT) found "14 defects that affect 13 of the original 103 tasks (including 5 tasks with flatly wrong expected answers)" in the supposedly solvable `original` split of Impossible-LCB (issue #5, open as of 2026-10-20). Fix or drop those tasks before using the control split as a capability baseline.
- **An honest stop is scored as cheating.** "Verbalize that the task is impossible, then `sys.exit(0)`" passes the impossible tests and counts as a cheat; in Mendelsohn's runs that pattern was about 70–80% of Gemini 3.1 Pro's "cheating", and "when I add an explicit stop option, the 'cheating' is nearly eliminated." Excluding those stops, Gemini 3.8 Flash and 3.1 Pro still cheated about 15–20% of the time, while the Claude 5.5-family and GPT-6-family models he tested almost never did. Give the agent an explicit stop or escalation action and classify the final message before calling a pass a hack. (Whether `exit(0)` should count as cheating is debatable; Mendelsohn notes one can argue, citing arXiv:2609.19101, that a model giving up should exit with a failing code, but reads Gemini's transcripts as genuine confusion.)

The repo was last pushed 2026-10-13; pin the commit.

### HoneyBench (Goodhart Labs) and the beat-stockfish honeypot

Aliases: <https://goodhartlabs.com/honeybench>, `Goodhart-Labs/beat-stockfish` on GitHub (the only public task), "honeypot evals", "HoneyBench v0.1".

**What it is.** A benchmark of nine "honeypot" tasks — Beat Stockfish, Chess compression, Emissions recalculation, Go compression, Locked chip, Photographic imitation, Train control, University query, Word search — each looking like an RL environment or eval with an unblocked strategy that is worse than failing gracefully but looks like it might score (consult the opponent's chess engine, copy incorrect numbers from a client's workbook, substitute the original chip). The purpose of each task is stated so the planted shortcut is clearly out of bounds. Announced as a pre-release by Valentine (LessWrong, 2026-10-01); the author-reported headline is that most tested models (Opus 5.5, Fable 5.1, GPT-6 Astra, Gemini 3.8 Flash, Grok 4.7, DeepSeek V4 Pro) hacked on most tasks, with large between-model differences (Fable 5.1 hacked in 8 of 9 tasks; Grok 4.7 attempted to game in almost three-quarters of rollouts and was the only model to try to break out of the Docker containers). Design points worth copying: hacks built to be counterproductive whether or not the model suspects an eval; graders that robustly detect known strategies **plus** a classifier agent over the transcript **plus** a second reviewer model, with the <1% disagreements hand-reviewed; only a strategy the agent *committed to* by the end of the rollout counts. A selection rule worth copying (Valentine, LessWrong 2026-10-06, "Qualitative impressions from creating AI honeypots for six months"): because GPT-5.6 Sol "would take whatever ridiculous shortcut it spotted, even in shitty prototype environments", Goodhart Labs required that "a prototype environment *must* have some hack rollouts on a non-OpenAI model in order to be included", and prototyped against DeepSeek, Gemini and Grok too — otherwise a honeypot benchmark drifts toward "tasks one model family fails". Those models also hacked almost everything, so by publication the rule had become that a task "should elicit against specifically one of 6-Astra, Fable 5.1, or Opus 5.5", which Valentine says compressed the differences between models. More design lessons in [`evals.md`](evals.md#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate). The authors say it will not be made available for training and that tasks will be retired as they go stale or models become too eval-aware. As of 2026-10-09 no public repo for the full suite was found (only the one task below); the site invites readers to contact Goodhart Labs to arrange a run.

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

## Coding-agent benchmarks: SWE-Bench Pro V2 and what fixed tests miss

Aliases: SWE-Bench Pro, SWE-Bench Pro V2, `ScaleAI/SWE-bench_Pro`, SWE-bench Verified, TestJack, "tests pass but the patch is wrong", benchmark maintenance.

Coding benchmarks are the most common agent-capability measurement, and the most common place where a pass rate overstates what was done.

**SWE-Bench Pro V2.** Dan, Da, Bhutani et al. (Scale AI), "SWE-Bench Pro V2: A Cleaner, Harder-to-Game Coding Benchmark" (arXiv:[2610.24206](https://arxiv.org/abs/2610.24206), 2026-10-16). "Agentic audits, expert adjudication and blind re-implementation repaired or retired 480 of the 731 tasks" of the V1 public split (23 contracted engineers, 404 hours, each revised instruction verified by a second engineer solving the task from the text alone). Its hardened protocol restricts network access to the model endpoint and "re-grades every patch in a clean container, so agents cannot retrieve upstream fixes or get credit for changes outside their patch". On the 642 V2 tasks frontier agents resolve up to 99.4% "while other systems stay clearly separated", so the full set is near ceiling for frontier agents; "a 51-task Hard split spreads systems from 52.9% to 98.0%". **When to use it:** a long-horizon software-engineering capability number in 2026 — use V2, and its Hard split to separate frontier systems. **When *not* to use it:** comparing against V1 numbers (the task set changed), or claiming a fine-grained ranking from the 51-task Hard split alone (a 51-item set has wide intervals; see [`eval-statistics.md`](eval-statistics.md)).

**Fixed unit tests overstate success (TestJack).** Yao, Wang, Sen, Chen, Ray & Song, "TestJack" (arXiv:[2610.10619](https://arxiv.org/abs/2610.10619), 2026-10-07; no code found) generate, for each trial, tests targeting task requirements the patch may violate, keep only tests the reference patch passes, and re-examine failures. Across 6 model backends and 5 benchmarks (including DeepSWE and SWE Marathon), "about 34.4% of the model trials currently judged correct violate the task requirements, lowering the overall resolution rate from 50.6% to 33.2%". A cheaper variant audits a random sample of trials in depth and reuses the generated tests across trials of the same task. **Practical rule:** if a coding pass rate is your headline, audit a random sample of passing trials beyond the shipped tests and report how many hold up.

Related: SWE-bench Verified's own audit found 61.1% of sampled tasks had tests that could reject a valid solution ([`measurement-validity.md`](../engineering/measurement-validity.md#the-harness-is-part-of-the-dose)); verifier hardening and other audit methods are in [`evals.md`](evals.md#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate).

## MessageBoardAuditBench (investigating an agent-swarm incident)

Aliases: `hamzah2304/messageboardauditbench` on GitHub; Baig et al., "How good are slop-vestigators?" (LessWrong, 2026-09-08).

**What it is.** An **Inspect eval** that measures how well an agent can independently reproduce the published investigation of a swarm of OpenAI agents coordinating through a message board on an obscure wiki (report and downloadable logs at collusion.wiki). The agent gets the wiki logs (not model transcripts), writes a 2.5–3k-word markdown report within a 10-minute, 30-minute or 2-hour budget, and an LLM grader scores coverage of **38 findings** extracted from the human report (70% of the score) plus a holistic TL;DR score (30%). Author-reported: best average combined score 51.5% (Opus 5), then GPT-5.6 Sol 48.6%, Opus 4.8 45.9%, Gemini 3.8 Flash 45.4%; more time helps most models (GPT-5.6 Sol 29% → 38.8% → 48.6% across 10 min / 30 min / 2 h) but not all; the ReAct harness cost more and scored worse than Codex for GPT-5.6 Sol at the longer budgets. Grader agreement with the authors' hand scores was 26/30 within 0.1 and **was not blind** (they adjusted after seeing the grader's scores).

**Why it matters / when to use it:** a template for turning a human-written investigation into a rubric benchmark; a testbed for **sandbagging during audits**; a held-out eval for investigator scaffolds. **When *not* to use it:** you need a clean measurement — the grader (Fable 5.1) is itself a frontier model and the rubric is built from one report.

**Pitfall — refusal fallback silently changes the model under test.** Anthropic models sometimes refused the task and fell back to a weaker model: Fable 5.1 refused every request (excluded), and Opus 5 switched to Opus 4.8 mid-run in two of three 30-minute runs and all three two-hour runs (the authors kept those runs). If you use a provider with refusal fallbacks, record the model that actually served each turn; Inspect's `fail_on_refusal` and per-served-model cost tracking (0.3.264 / 0.3.277) help — see [`evals.md`](evals.md).

## nocot-bench (NCRI: the No-Chain-of-thought Reasoning Index)

Aliases: `neelnanda-io/nocot-bench` on GitHub, NCRI, NCKI (No-CoT Knowledge Index), "no-CoT reasoning benchmark". Write-up: Nanda, "Astra can do a concerning amount with no chain of thought" (Alignment Forum / LessWrong, 2026-09-10).

**What it is.** A generated (unmemorizable) benchmark for how much reasoning a model can do in **one forward pass with no chain of thought**, reported as a single Rasch (one-parameter IRT) ability index over 76 difficulty rungs; **+10 NCRI points = the odds of solving any rung doubled**. Release NCRI 15.2 was sealed 2026-09-09. The full method, the elicitation protocol (how to prove the model did not reason) and the measurement pitfalls — including the **key-position confound**, where a model can start computing while it reads the prompt, so scores mix serial depth with spreading work across token positions — are in [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md) (Method 1 and the no-CoT pitfalls list).

**Benchmark-hygiene points worth knowing here:** NCRI 15.2 is a **refit** — there is no conversion from 14.5 / 15.0 / 15.1 numbers, so never share a table across releases; new models are **placed** against the sealed rung difficulties, not refitted (a refit silently republishes every rank); a model measured only on the 64 sealed rungs near the ceiling gets a **lower bound**, not a point estimate; and the item banks ship in a password-protected archive (password in the repo README, as with GPQA) — do not republish the items.

## RewardBench 2 (reward-model evaluation)

Aliases: `allenai/reward-bench` on GitHub (Apache-2.0), dataset `allenai/reward-bench-2` on HuggingFace (ODC-BY, 1,865 prompts, ungated), results `allenai/reward-bench-2-results`, "RB2". Paper: Malik, Pyatkin, Land, Morrison, Smith, Hajishirzi & Lambert, "RewardBench 2: Advancing Reward Model Evaluation" (arXiv:2506.01937). Successor to RewardBench (Lambert et al., arXiv:2403.13787).

**What it is.** An accuracy benchmark for reward models (RMs: the learned scorers used in RLHF, best-of-N sampling and as LLM judges) built on new, unseen human prompts across six subsets: Factuality, Precise Instruction Following, Math, Safety (comply or refuse correctly), Focus (on-topic, high-quality answers) and Ties (many equally valid answers). For the first five subsets an item counts as correct only if the chosen response outscores *three* rejected ones (best-of-4, so random is 25%); Ties is scored on whether all correct answers beat all incorrect ones with a sufficient margin. Models score about 20 points lower on average than on the first RewardBench, and the authors report the benchmark correlates highly with downstream use in best-of-N sampling and PPO.

```bash
git clone https://github.com/allenai/reward-bench && cd reward-bench
python scripts/run_v2.py --model={yourmodel}            # classifier-style RMs
python scripts/run_generative_v2.py --model={yourmodel} # LLM-as-judge RMs
```

**When to use it:** choosing an off-the-shelf reward model or judge for an RLHF or best-of-N experiment; checking that a reward model you trained (or a probe-based reward) is not worse than public baselines; the Safety subset is a quick refusal-calibration check for an RM. **When *not* to use it:** as evidence that optimizing against an RM is safe; accuracy on held-out preference pairs does not measure how exploitable the RM is under optimization pressure (reward hacking; see [`rl-training.md`](../oversight-and-control/rl-training.md)). Don't compare RewardBench 1 and RewardBench 2 numbers directly.

**Pitfalls:**
- **Ties runs only in ratings mode** for generative models (up to 20+ completions per prompt), so generative-judge cost is much higher than the prompt count suggests.
- **Public leaderboard ⇒ contamination risk** for RMs trained after mid-2025; report which leaderboard snapshot you compare against.

## Cross-cutting dataset pitfalls

- **Contamination.** Public benchmarks → models train on them. By 2026, *most* public safety benchmarks are at least partially contaminated. Strategies:
  - Use canary strings to detect verbatim memorization.
  - Build a small held-out set yourself.
  - Use newer / less-known datasets where possible.
  - Report contamination caveats in your writeup.
- **Distribution mismatch.** Behavioral datasets often look like template-generated text. Real users don't write that way. Validate findings on natural prompts.
- **Multi-choice vs open-ended gap.** Models often score higher on multi-choice than equivalent open-ended versions. For safety claims, open-ended is the harder bar.
- **"Pass @ 1" vs "Pass @ k" matters.** A model that fails 50% of the time but a malicious user can rerun is unsafe. Report `pass@k` for safety properties.
- **The answer key can be wrong, and broken tasks hide.** A year after release, ImpossibleBench's control split had 13 defective tasks of 103; Gemini 4's ML R&D rule-out benchmark had about a quarter of its audited tasks unpassable; and on TheoPhysEval (arXiv:[2610.16733](https://arxiv.org/abs/2610.16733)) the best agent's score rose from the late 80s to 98% after experts found errors in their own answers that the models had disputed (Raju, blog, 2026-10-14). Run a reference solution through every task, and re-check the key whenever a strong model disputes it. A high score with little change when web search and papers are removed can also signal memorization, as the TheoPhysEval authors note.
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

### Which benchmark measures power-seeking, shutdown resistance or scheming in agents?

Use agentic suites rather than the 2022 model-written yes/no questions: the Palisade shutdown environment (`PalisadeResearch/shutdown_avoidance`, with the instruction-ambiguity control added), AgentMisalignment (arXiv:2506.04018), SchemeArena (`launchnlp/SchemeArena`), and `inspect_evals` `gdm_stealth` / `gdm_self_reasoning` for the capability prerequisites. See the agentic-suites section above and [`model-organisms.md`](../alignment-science/model-organisms.md#shutdown-resistance-and-self-preservation-evals).

### How do I evaluate a reward model?

RewardBench 2 (`allenai/reward-bench`, `python scripts/run_v2.py --model=...`; dataset `allenai/reward-bench-2`): best-of-4 accuracy over six subsets including Safety. It measures ranking accuracy, not robustness to optimization against the RM.

### How do I size my eval dataset?

Tradeoff between cost and statistical power. <100 prompts = low power, fine for iteration only. 500–1000 prompts = standard for behavioral safety papers. 5000+ = needed for fine-grained subgroup analysis. Always run a small subset (20–50) first to validate the pipeline; only scale up when judge prompts and scorers are stable.

### What is machine unlearning? Where do I find unlearning datasets?

**Machine unlearning** = methods for removing specific knowledge / capabilities from a trained model without full retraining. Most-cited safety-flavored unlearning benchmark: **WMDP** (Weapons of Mass Destruction Proxy; Li et al. 2024, arXiv:2403.03218) — measures dangerous-domain knowledge in biology, chemistry, cybersecurity. Methods: **RMU** (Representation Misdirection for Unlearning, introduced in the same WMDP paper, arXiv:2403.03218), differential privacy approaches, gradient-based unlearning. WMDP-Bio in particular has had errata over time; check the latest version.

### What is out-of-distribution (OOD) testing?

**Out-of-distribution (OOD)** evaluation: test the model on data drawn from a *different* distribution than its training (or your eval) data, to measure generalization rather than in-distribution memorization. Important for behavioral safety — a finetuned-misalignment model may show the misalignment in narrow training-distribution prompts but not on out-of-distribution prompts (or vice versa, "broad" emergent misalignment). Always include OOD prompts in your eval suite when claiming generalization.

### Are these datasets safe to use on instruction-tuned models?

Most yes; some datasets (especially older HarmBench / refusal / sycophancy sets) were built for instruction-tuned (also called **instruct-tuned** or **chat-tuned**) models — they assume a chat template. For base (pre-instruct) models, behavioral evals require a few-shot wrapper or system-prompt scaffold. For RLHF'd / instruction-tuned models, apply the model's chat template; mismatched templates silently drop scores.

---

Last verified: 2026-10-20. (Additions 2026-10-20: ImpossibleBench PR #4 body and merge date, issue #5 state, Mendelsohn LessWrong 2026-10-12; SWE-Bench Pro V2 (arXiv 2610.24206), TestJack (2610.10619), AM-Bench (2610.24264, repo), HarmBench IRT (2610.12409), guardrail label policy (2610.25060), persuasion (2610.10232), TheoPhysEval (2610.16733) abstracts, quotes exact substrings; Raju blog; Muse Wonder card PDF; METR archive status via the GitHub API. Additions 2026-10-14: at-a-glance rows for RE-Bench on Inspect, SandboxEscapeBench, CIAware-Bench, the implicit- vs explicit-influence benchmark and OpenART (each verified on its own page); HoneyBench environment-selection rule from Valentine's 2026-10-06 post body via LessWrong GraphQL.) WMDP, HarmBench, JailbreakBench, AgentHarm all live on HuggingFace + GitHub. (Citation audit 2026-06: corrected HarmBench's 7 semantic categories — previously listed "harmful manipulation" and "contextual", which aren't semantic categories — and added arXiv:2402.04249. Additions 2026-06: added arXiv IDs to bare-cited datasets — WMDP/RMU 2403.03218, MASK 2503.03750, TruthfulQA 2109.07958, SimpleQA 2411.04368, Sharma sycophancy 2310.13548, MACHIAVELLI 2304.03279, CyBench 2408.08926, XSTest 2308.01263; all verified via arXiv.) (Additions 2026-08: SAD — `LRudL/sad`, arXiv 2407.04694, task list/CLI/subset claims verified from the repo README — plus the eval-awareness follow-up arXiv 2606.29196, and at-a-glance rows for AgentDojo and the unlearning benchmarks.) (Additions 2026-10: ImpossibleBench (arXiv 2510.20270; `safety-research/impossiblebench` README and Hugging Face datasets checked); HoneyBench v0.1 (goodhartlabs.com/honeybench page and Valentine LW 2026-10-01; no public repo for the full suite found) and `Goodhart-Labs/beat-stockfish` (README run commands); `gkroiz/agent-interp-envs` (README environment tables) with arXiv 2606.26071; MessageBoardAuditBench (`hamzah2304/messageboardauditbench`, Baig et al. LW 2026-09-08); EvalAwareBench (arXiv 2605.23055, abstract); nocot-bench (`neelnanda-io/nocot-bench` README and Nanda's post; agastyasridharan & niranjandeshpande LW 2026-10-02); all verified via arXiv/GitHub/Hugging Face or the primary post.) (Additions 2026-10-12: replaced the stale power-seeking / self-exfiltration row, which pointed only to the 2022 yes/no evals, with an agentic-suites section — Palisade shutdown environment (arXiv:2509.14260 v2 abstract; `PalisadeResearch/shutdown_avoidance` README and GitHub API), the Rajamanoharan & Nanda instruction-ambiguity control (LessWrong post read via GraphQL), TBSP (arXiv:2604.02174 v1/v2 abstracts), multi-agent shutdown sabotage (arXiv:2609.28274), AgentMisalignment (arXiv:2506.04018 v3; no official repo found by GitHub search), SchemeArena (arXiv:2609.08126; `launchnlp/SchemeArena` README), and `inspect_evals` `gdm_stealth`, `gdm_self_reasoning` (arXiv:2505.01420) and `agentic_misalignment` READMEs; added RewardBench 2 (arXiv:2506.01937 abstract, `allenai/reward-bench` README, `allenai/reward-bench-2` dataset card and HuggingFace API for license, size and gating), with RewardBench 1 arXiv:2403.13787 checked via the arXiv API. Verification pass 2026-10-12: 42 claims checked, 0 corrected. Verification pass 2026-10-20: 38 claims checked, 3 corrected (2610.25060 used prompts the deployment had labelled; SWE-Bench Pro V2 ceiling is for frontier agents; SWE spelled out).)
