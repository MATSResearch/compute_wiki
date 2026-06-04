---
tags:
  - oversight
---

# Debate and Scalable Oversight

Tooling and methods for **scalable oversight** — the family of approaches for getting useful supervision signal on tasks where the supervisor (typically: humans, or weaker models) can't directly evaluate the work of a more capable model. Includes **debate**, **iterated amplification**, **recursive reward modeling**, **market making**, **consultancy**, **self-critique**, and **prover-verifier games**.

Tooling here is sparser than for evals or interp — most published research uses bespoke pipelines built on Inspect AI or general LM APIs. This doc maps the methods, the few existing libraries, and the main pitfalls.

## At a glance

| You want… | Use |
|---|---|
| Run a debate-style protocol over a benchmark | **Inspect AI** custom solver — there is no debate-specific library, but Inspect's multi-agent primitives + custom solvers cover this |
| A reference debate implementation to fork | **`ucl-dark/llm_debate`** (Khan et al. 2024, arXiv:2402.06782) or Kenton et al. (arXiv:2407.04622) |
| Standardized scalable-oversight benchmark | **Scalable Oversight Benchmark** (Pallavi Sudhir, Kaunismaa & Panickssery 2025; `SOlib` Python package; arXiv:2504.03731) |
| Sandwiching evaluation (weak overseer using model to match strong group's performance) | Hand-rolled pipeline; reference: the original sandwiching papers (Cotra; Bowman et al.) |
| Self-critique / iterative refinement workflow | Hand-rolled with Inspect AI custom solvers; LLM-as-judge primitives |
| Prover-verifier games / prover-estimator debate | Hand-rolled from the recent Brown-Cohen / Irving papers; no shrink-wrapped lib |
| Theoretical reading on what debate can solve | The doubly-efficient debate / prover-estimator debate papers |

## What scalable oversight is, in one paragraph

Imagine training or evaluating a model on a question whose right answer you can't easily check (a long research argument, a complex codebase change, a detailed plan). You'd like to leverage the model's own capabilities (or other models) to produce a *checkable* artifact: a debate transcript where weaknesses are exposed; a critique; a decomposition into easier subquestions. The general bet: it's cheaper to *spot* a flaw in a structured argument than to *find* the answer from scratch. Scalable oversight protocols formalize and study this.

## Core protocols (vocabulary entries for RAG)

Each entry: name, what it is, key reference. Spelled out so a fellow asking "what is debate?" or "what is recursive reward modeling?" gets a self-contained answer.

### Debate

Aliases: AI safety via debate, "Irving debate", debate protocol.

**What it is.** Two models argue opposing positions; a (weaker) judge picks the winner. The hope: at equilibrium, the honest player wins, because exposing your opponent's lies is easier than constructing a defensible lie. Originated: Irving, Christiano, Amodei (2018), "AI safety via debate" (arXiv:1805.00899).

**Tools:** Inspect AI multi-agent primitives, custom solvers. Typically: `agent_a`, `agent_b`, judge model, structured turn-taking.

### Doubly-efficient debate

Aliases: "doubly-efficient debate", "Brown-Cohen Irving debate", arXiv:2311.14125.

**What it is.** A more recent debate protocol (Brown-Cohen, Irving, et al.) where the honest player needs only polynomial compute even when the dishonest player can use exponentially more. Theoretically attractive; complex to implement.

### Prover-Verifier Games (PVG)

**What it is.** A game-theoretic framework where a "prover" model tries to make a "verifier" output a particular decision, with rewards structured so honest-prover and skeptical-verifier are an equilibrium. Used both as a training target and an evaluation framework.

### Prover-Estimator Debate

Aliases: arXiv:2506.13609 ("Avoiding Obfuscation with Prover-Estimator Debate"), Brown-Cohen, Irving (2025). Sometimes "PED."

**What it is.** A scalable-oversight protocol where honesty is incentivized at equilibrium even when prover and estimator have similar compute available. Addresses obfuscation problems in earlier debate variants.

### Iterated Distillation and Amplification (IDA)

Aliases: IDA, "Christiano amplification", "iterated amplification".

**What it is.** Repeatedly distill a strong overseer (e.g. human + model assistance) into a model, then use that model in an even-stronger overseer setup, etc. Originated: Christiano, Shlegeris, Amodei (2018), "Supervising strong learners by amplifying weak experts" (arXiv:1810.08575).

### Recursive Reward Modeling (RRM)

Aliases: RRM, "Leike recursive reward modeling".

**What it is.** Train reward models for tasks too hard to evaluate directly by training reward models for the *evaluation subtasks* and composing. Originated: Leike et al. (2018), "Scalable agent alignment via reward modeling: a research direction" (arXiv:1811.07871).

### Self-critique / iterative refinement

**What it is.** A model generates output, then critiques its own output, then revises. Variants: **Self-Refine** (Madaan et al. 2023, arXiv:2303.17651 — same model generates, critiques, refines), **Reflexion** (Shinn et al. 2023, arXiv:2303.11366 — verbal self-reflection stored in episodic memory across attempts), **CRITIC** (Gou et al. 2023, arXiv:2305.11738 — self-correction using external tools like search/code interpreters). Cheap to implement; widely used; effectiveness is debated.

### Market Making

**What it is.** Several models bet on the answer to a question; the market price is taken as the (weighted) verdict. Less common in practice; theoretically interesting.

### Consultancy

**What it is.** A baseline used in Anthropic / DeepMind work: a single (untrusted) model advises a (weaker) judge, no debate, no opposing argument. Used as a comparator for whether debate adds value.

### Sandwiching

**What it is.** Evaluation methodology, not a protocol. A weaker group of overseers, equipped with an intermediate-capability model, tries to match the performance of a stronger group on a task the weaker group can't do alone. Tests whether the model + weak-overseer process can substitute for strong-overseer judgment. Originated: Cotra (2021); operationalized in Bowman et al. 2022, "Measuring Progress on Scalable Oversight for Large Language Models" (arXiv:2211.03540).

### Weak-to-strong generalization

**What it is.** OpenAI 2023 paper line (Burns et al. 2023, "Weak-to-Strong Generalization: Eliciting Strong Capabilities With Weak Supervision", arXiv:2312.09390). Train a strong model from labels produced by a weak model; study how much performance the strong model recovers. Related but distinct from debate-style protocols.

## Tools and reference repos

### Scalable Oversight Benchmark (Pallavi Sudhir, Kaunismaa & Panickssery 2025)

Aliases: "scalable oversight benchmark", arXiv:2504.03731, "ASD metric" (Agent Score Difference), `SOlib`, "math_problems_debate". Authors: Abhimanyu Pallavi Sudhir, Jackson Kaunismaa, Arjun Panickssery. (Not to be confused with the separate "Scaling Laws For Scalable Oversight", Engels et al. 2025, arXiv:2504.18530.)

**What it is.** A benchmark and Python package (`SOlib`, repo `ArjunPanickssery/math_problems_debate`) for evaluating scalable-oversight protocols on a standardized task suite. Provides the **ASD (Agent Score Difference)** metric: how much a protocol advantages truth-telling over deception.

**When to use it:**
- You're proposing a new scalable-oversight protocol and want comparable numbers.
- You want a maintained reference implementation of debate / consultancy / etc. in one place.

**When *not* to use it:** You're studying a specific question (e.g. CoT monitorability) where the benchmark task structure doesn't fit.

### Scaling Laws For Scalable Oversight (Engels et al. 2025)

Aliases: arXiv:2504.18530, "the oversight scaling laws paper".

**What it is.** A framework that quantifies oversight success as a function of capability gap between overseer and overseen, applied to four games: Mafia, Debate, Backdoor Code, Wargames. Reports NSO (Nested Scalable Oversight) success rates at Elo gap 400: Mafia 13.5%, Debate 51.7%, Backdoor Code 10.0%, Wargames 9.4%.

**When to use it:**
- Calibrating expectations for how much oversight gap a given protocol can bridge.
- Reproducing the four-games framework on a new model.

**Pitfalls:**
- The four games are stylized. Don't assume "Debate works at Elo gap 400" implies real-world deployment robustness.

### Inspect AI for debate / oversight evals

The de facto framework for actually running these protocols. Pattern:
- Define each role (prover, verifier, judge, advisor, debater A/B) as separate Inspect agents or model calls.
- Use Inspect's multi-agent / agent-bridge primitives.
- Custom scorer aggregates across rounds.

There is no "Inspect debate package" but the primitives are sufficient. See [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md) for multi-agent details.

### Khan et al. 2024 — "Debating with More Persuasive LLMs Leads to More Truthful Answers"

Aliases: arXiv:2402.06782, "the persuasive-LLMs debate paper", `ucl-dark/llm_debate` on GitHub. Khan, Hughes, Valentine, Ruis, Sachan, Radhakrishnan, Grefenstette, Bowman, Rocktäschel, Perez. **ICML 2024 Best Paper.**

**What it is.** The landmark *empirical* demonstration that debate helps weaker judges supervise stronger debaters. Two LLM experts argue opposing answers on QuALITY long-document reading comprehension (where the judge can't see the full passage); debate raised non-expert **model** judge accuracy to 76% and non-expert **human** judge accuracy to 88%, versus 48% / 60% naive baselines — and *more persuasive* debaters yielded *more truthful* judge verdicts. Also found debate beats consultancy.

**When to use it:** The reference implementation to start a debate-vs-consultancy project from (`ucl-dark/llm_debate`); the empirical anchor when motivating debate over single-advisor setups.

### Kenton et al. 2024 — "On scalable oversight with weak LLMs judging strong LLMs"

Aliases: arXiv:2407.04622, NeurIPS 2024, DeepMind. Implements **debate, consultancy, and direct-QA baselines** on QuALITY-style reading-comprehension and other tasks, with weaker LLM judges over stronger LLM agents. Public code via the NeurIPS proceedings repo. A clean reference implementation covering more protocols/tasks than Khan et al.

## Patterns for running your own oversight experiment

### Debate on a long-document QA task

1. Pick a task where models can outperform a weak judge alone (e.g. QuALITY long-document QA).
2. Two models argue opposing answers; both can quote document spans.
3. Judge (weaker model or human) picks the winner.
4. Compare to consultancy baseline (single model advising same judge) and to judge-alone.

**Tools:** Inspect AI for orchestration; safety-research/safety-tooling for batch judge calls; QuALITY dataset on HuggingFace.

### Sandwiching pilot

1. Identify a task where group A (e.g. junior reviewers) underperforms group B (senior reviewers).
2. Give group A access to a model.
3. Measure whether group A + model matches group B without model.

**Tools:** Inspect AI, plus an interface for human evaluators (varies — some use custom web apps, some use spreadsheets).

### Self-critique iteration

1. Model generates initial answer.
2. Model (or a separate critic) produces critique.
3. Model revises. Loop N times.
4. Compare final answer to direct first-shot answer.

**Tools:** Inspect AI custom solver; one-paragraph-of-Python.

**Pitfall:** self-critique often *converges to confident wrong answers* on tasks the model can't actually do. Validate against a held-out scorer.

## Cross-cutting pitfalls in scalable oversight research

- **The capability gap is the whole point.** If your "weak" judge is actually as capable as the debaters, the experiment doesn't test what you think it tests. Use deliberately weaker models / simulated weak judges.
- **Strategic agreement.** Two debaters trained on similar data may collude implicitly — neither bringing up the other's weaknesses. Vary training distributions; use anti-collusion measures (paraphrasing transcripts before judging).
- **Judge bias.** Judges can be sycophantic, length-biased, position-biased. Standard LLM-as-judge biases apply with extra force here. Counterbalance presentation order; use multiple judges; check for bias on calibration set.
- **Domain-specific brittleness.** A debate protocol that works on math may fail on history. Debate's "honesty wins" guarantee assumes the topic is one where errors are *checkable* in the debate context.
- **Compute asymmetry breaks theoretical guarantees.** Many debate proofs assume bounded prover compute. Real-world AIs have effectively unbounded compute relative to the proof setup. Treat theoretical results as sketches.
- **Anthropomorphism in scoring.** "The honest debater won" assumes a meaningful honest-vs-deceptive distinction in the model's behavior, not just in your task setup. Be careful about claims.
- **Reward hacking the protocol.** A model trained on debate wins may learn rhetorical tricks rather than truth-finding. Debate-as-training-target has more pitfalls than debate-as-evaluation.
- **Sample efficiency.** A debate protocol that needs 50 turns per question is hard to scale. Real deployment requires bounding interactions tightly.
- **Sandwiching vs deployment.** A successful sandwiching demo proves a *capability* of the model + weak overseer. It does *not* prove the protocol scales to superhuman models. (Most published sandwiching is on tasks where sufficiently-skilled humans *can* in principle do them.)
- **Equilibrium vs trajectory.** Theoretical results about debate are about Nash equilibria. Real models trained with RL may not reach equilibrium. Empirical robustness ≠ theoretical guarantee.
- **CoT in debate.** Debater models often need CoT to argue effectively. CoT faithfulness issues (see [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md)) propagate into debate quality.

## What you can build right now (research project shapes)

- **Debate vs consultancy on a new task.** Pick a domain (medical reasoning, legal analysis, code review) and replicate the debate-vs-consultancy comparison. Tooling: Inspect AI + a reference task.
- **Capability-gap calibration.** Run sandwiching with different "weak" judge sizes; map out the curve of "how much capability gap can debate bridge?"
- **Adversarial debater training.** Train one debater on outcome rewards, the other on truthfulness; study the dynamics.
- **CoT-faithfulness × debate.** Does requiring more verbose CoT in debaters improve debate quality? Crosses into [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).
- **Probe-augmented oversight.** Use probes (see [`probes.md`](../interpretability/probes.md)) on debater activations as an additional signal alongside argument quality.

## Cross-references

- Inspect AI (the primary harness for these protocols): [`evals.md`](../evaluation/evals.md).
- Multi-agent / agent scaffolding primitives: [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).
- AI Control (a complementary line where the model is *adversarial*; debate is a different framing): [`ai-control.md`](ai-control.md).
- RL training (relevant if you train debaters or critics): [`rl-training.md`](rl-training.md).
- CoT faithfulness (debater CoTs inherit these issues): [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).
- Probes as auxiliary oversight signal: [`probes.md`](../interpretability/probes.md).

## Recommended reading

- **Irving, Christiano, Amodei (2018)** — "AI Safety via Debate" (arXiv:1805.00899). The original.
- **Christiano, Shlegeris, Amodei (2018)** — "Supervising Strong Learners by Amplifying Weak Experts" (arXiv:1810.08575). Iterated amplification (IDA).
- **Leike et al. (2018)** — "Scalable agent alignment via reward modeling: a research direction" (arXiv:1811.07871). Recursive reward modeling.
- **Bowman et al. (2022)** — "Measuring Progress on Scalable Oversight for Large Language Models" (arXiv:2211.03540). The sandwiching paper.
- **Khan et al. (2024)** — "Debating with More Persuasive LLMs Leads to More Truthful Answers" (arXiv:2402.06782; ICML 2024 Best Paper; `ucl-dark/llm_debate`). The landmark empirical debate result.
- **Brown-Cohen, Irving, Piliouras (2023, 2024, 2025)** — doubly-efficient debate; prover-estimator debate. arXiv:2311.14125, arXiv:2506.13609.
- **Kenton et al. (2024)** — "On scalable oversight with weak LLMs judging strong LLMs" (DeepMind; arXiv:2407.04622). NeurIPS 2024. Code on the proceedings repo.
- **Self-critique line** — Self-Refine (Madaan et al. 2023, arXiv:2303.17651), Reflexion (Shinn et al. 2023, arXiv:2303.11366), CRITIC (Gou et al. 2023, arXiv:2305.11738).
- **Pallavi Sudhir, Kaunismaa & Panickssery (2025)** — "A Benchmark for Scalable Oversight Protocols" (arXiv:2504.03731; `SOlib` package).
- **Engels et al. (2025)** — "Scaling Laws For Scalable Oversight" (arXiv:2504.18530); repo `subhashk01/oversight-scaling-laws`.
- **Knowledge Divergence and the Value of Debate for Scalable Oversight** (arXiv:2603.05293) — recent theoretical work on when debate adds value.
- **Burns et al. (OpenAI, 2023)** — "Weak-to-Strong Generalization: Eliciting Strong Capabilities With Weak Supervision" (arXiv:2312.09390).
- **Geoffrey Irving** — for the latest on prover-estimator debate, follow his publications and X/Twitter.

---

## Common questions

### What is debate (in AI safety)?

**Debate** = AI safety via debate, originated by Irving, Christiano, Amodei (2018). Two AI models argue opposing positions on a question; a (typically weaker) judge picks the winner. The hope: at equilibrium, the honest player wins because exposing your opponent's lies is easier than constructing a defensible lie. A scalable-oversight protocol — a way to get useful supervision signal on tasks the supervisor can't directly evaluate.

### What is sandwiching (in AI safety)?

**Sandwiching** is an *evaluation methodology*, not a protocol. A weaker group of overseers, equipped with a model, tries to match the performance of a stronger group on a task the weaker group can't do alone. If they succeed, the model + weak-overseer process can substitute for strong-overseer judgment. Originated: Cotra 2021; operationalized by Bowman et al. 2022.

### Is there a library for debate / scalable oversight?

No general-purpose library. The closest things: **Scalable Oversight Benchmark** (Pallavi Sudhir, Kaunismaa & Panickssery 2025; arXiv:2504.03731; `SOlib` package) is a benchmark + Python package for evaluating oversight protocols on standardized tasks. **Inspect AI**'s multi-agent primitives (see [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md)) are the standard substrate for building debate / consultancy / self-critique protocols. You'll write the orchestration yourself.

### What is IDA (Iterated Distillation and Amplification)?

**IDA**: Christiano-Shlegeris-Amodei 2018. Repeatedly **distill** a stronger overseer (e.g. human + model assistance) into a model, then **amplify** by using the new model to construct an even stronger overseer (model + model assistance), then distill that, etc. The bet is that each step bridges a small capability gap, so the chain can extend further than direct supervision could.

### What is recursive reward modeling (RRM)?

**RRM**: Leike et al. 2018. Train reward models for tasks too hard to evaluate directly by training reward models for the *evaluation subtasks* and composing. If you can't tell whether an answer is good, but you *can* tell whether a critique of the answer is good, train an RM on critique quality and use it to evaluate the original answer. Recursive: critique-quality RMs may themselves be hard to train, so train RMs for evaluating critique-quality, etc.

### Self-critique — does it actually work?

Mixed. Self-critique / Reflexion / Self-Refine: model generates output, critiques it, revises. Works on tasks where the model can locally identify errors but doesn't catch them on first pass (some math, code). **Fails systematically** on tasks the model genuinely can't do — self-critique often converges to *confident wrong answers* rather than catching its own ignorance. Validate against a held-out scorer; don't trust self-critique as a reliable improvement.

### What is a prover-verifier game (PVG)?

**PVG**: a game-theoretic framework where a "prover" tries to make a "verifier" output a particular decision, with rewards structured so honest-prover and skeptical-verifier are an equilibrium. **Prover-Estimator Debate** (Brown-Cohen, Irving 2025) is a variant where honesty is incentivized at equilibrium even when prover and estimator have similar compute available — important because earlier debate variants assumed bounded prover compute.

### How do I run a debate experiment?

In Inspect AI: define `agent_a` and `agent_b` as separate model calls (different system prompts: "argue for answer A" vs "argue for answer B"); structure turn-taking via a custom solver; pass the transcript to a `judge_model` for the final decision; aggregate. Compare against **consultancy baseline** (single model advising same judge, no debate) and **judge-alone**. Two public reference implementations worth forking: **`ucl-dark/llm_debate`** (Khan et al. 2024, arXiv:2402.06782, ICML Best Paper — the empirical "debate helps weak judges" result) and Kenton et al. 2024 (arXiv:2407.04622, NeurIPS — debate + consultancy + direct-QA).

---

Last verified: 2026-06. Active theoretical work (Brown-Cohen, Irving) on prover-estimator debate; the Scalable Oversight Benchmark (Pallavi Sudhir, Kaunismaa & Panickssery 2025; `SOlib`) and scaling-laws analysis (Engels et al. 2025) maturing; no general-purpose scalable-oversight library, but Inspect AI is sufficient substrate. Citations re-verified against arXiv 2026-06. (Additions 2026-06: added arXiv IDs to the foundational protocol references — Irving 1805.00899, Christiano IDA 1810.08575, Leike RRM 1811.07871, Bowman 2211.03540, Burns W2S 2312.09390, Kenton 2407.04622 — the landmark empirical debate result Khan et al. 2402.06782 (`ucl-dark/llm_debate`, ICML Best Paper), and self-critique citations Self-Refine 2303.17651 / Reflexion 2303.11366 / CRITIC 2305.11738; all verified via arXiv.)
