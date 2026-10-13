---
tags:
  - alignment-science
---

# Agent Foundations, Corrigibility and Formal Methods

Theory-side alignment research: **agent foundations** (mathematical theory of agents and their concepts), **corrigibility** theory (agents that let their principals correct or shut them down), and **guaranteed-safe AI / formal verification** (machine-checked safety guarantees). This page lists the formalisms, the groups and funders working on them in 2026, and what a first deliverable looks like. For the Lean toolchain itself (lean-lsp-mcp, comparator, nanoda) see [`lean-formalization.md`](../engineering/lean-formalization.md).

## At a glance

| I want to… | Start with |
|---|---|
| A formal model of an agent that accepts shutdown | The **off-switch game** (Hadfield-Menell et al., arXiv:1611.08219), then Nayebi's corrigibility heads (arXiv:2507.20964) |
| Know when two agents' concepts translate into each other | **Natural Latents** (Wentworth & Lorell, arXiv:2509.03780) |
| Funding for corrigibility theory *or* experiments | **Corrigibility Research Fund** (Lightcone; grant round 2 closes **2026-10-31**) |
| An empirical shutdown-resistance result to test a theory against | Schlatter, Weinstein-Raun & Ladish, arXiv:2509.14260 |
| The framework for "provable" safety: world model + specification + verifier | **Guaranteed Safe AI** (Dalrymple et al., arXiv:2405.06624) |
| Know where UK government money for formal-methods safety is going | **ARIA (UK Advanced Research and Invention Agency) Safeguarded AI** (now a mathematical assurance toolkit plus cybersecurity applications) |
| Check a proof that an AI wrote | [`lean-formalization.md`](../engineering/lean-formalization.md): comparator plus an external kernel |
| Work on a theory problem with an AI agent: reasoning moves, a canonical decision-theory case bank, which problems suit AI help | [`theory-research.md`](../engineering/theory-research.md) |
| Reward hacking and training-time failure modes (the empirical side) | [`rl-training.md`](../oversight-and-control/rl-training.md) |

## Agent foundations: who works on it in 2026

**Agent foundations** is the research tradition associated with the Machine Intelligence Research Institute (MIRI), behind Logical Induction, updateless and functional decision theory (UDT, FDT), Reflective Oracles, Tiling Agents, Risks from Learned Optimization, Cartesian Frames, Infra-Bayesianism and early corrigibility work, with *Embedded Agency* as the usual introduction. It builds mathematical theory of minds, so that one can ask precise questions about how a highly capable system behaves after extensive learning, self-modification and interaction with other agents.

- **Resolution's Agent Foundations team** (announced on LessWrong 2026-09-03 by Jeremy Gillen): Jeremy Gillen, Abram Demski, Sam Eisenstat, Scott Garrabrant and Kaarel Hänni, continuing "in the spirit of the MIRI Agent Foundations team". Projects named in the announcement: understanding concepts, building on *Condensation*; trust and legitimacy; and better foundations for game theory. The post says they will recruit experienced researchers soon and later plan to hire interns and junior researchers. Their suggested background reading is *Embedded Agency* and the 2017 MIRI technical research agenda.
- **Natural Latents** (John Wentworth & David Lorell, arXiv:2509.03780, 2025). Two Bayesian agents agree on the predictive distribution over observables but use different latent variables. The paper gives the *natural latent conditions* under which one agent's latents are guaranteed to be a function of the other's. It shows these are the most general such conditions absent further constraints, and that the theorems are robust to approximation error. It is a candidate formal handle on when concepts translate between agents.

**Where the work appears:** LessWrong and the Alignment Forum, and arXiv. Corrigibility work specifically has a dedicated funder, the Corrigibility Research Fund (Lightcone Infrastructure).

**Fit for a fellowship-length project:** a precise problem statement with one proved lemma or counterexample is a realistic first output; a new framework is not. If you need an empirical result and have no proof-writing experience, a theory-to-empirics project (testing one assumption of a formal result on current models, as in the shutdown-resistance work) is the better entry point.

## Corrigibility theory

**Corrigibility** means an agent keeps its principal able to correct, modify or shut it down, and does not resist. The standard formal setting is the **off-switch game** (Hadfield-Menell, Dragan, Abbeel & Russell, arXiv:1611.08219): a human can press a robot's off switch, and the robot can disable the switch. The paper shows that a robot which takes its reward function as given has an incentive to disable the switch unless the human is perfectly rational, and that uncertainty about its utility, with the human's actions treated as evidence about it, gives the robot a reason to keep the switch.

### Nayebi, "Core Safety Values for Provably Corrigible Agents" (arXiv:2507.20964)

- **Construction:** five *structurally separate* utility heads (deference, switch-access preservation, truthfulness, low impact through a belief-based extension of Attainable Utility Preservation, and bounded task reward), combined lexicographically with strict weight gaps.
- **Results:** exact single-round corrigibility in the partially observed off-switch game (Theorem 1). Extension to multi-step, self-spawning agents (Theorem 3), where the probability of violating any safety property stays bounded even if each head is learned only to mean-squared error ε and the planner is ε-suboptimal.
- **Limit:** with an adversary who can modify the agent, deciding whether an arbitrary post-hack agent will ever violate corrigibility is undecidable, by reduction to the halting problem. The paper certifies a finite-horizon "decidable island" in randomized polynomial time and verifies it with zero-knowledge proofs.
- **Companion:** Nayebi, arXiv:2502.05934, gives communication-complexity lower bounds on agreement across many objectives and agents. It argues that with large task spaces and finite samples, reward hacking is globally inevitable, so oversight should target safety-critical slices.

**Open problem / evidence bar:** the guarantees hold relative to the off-switch-game model and to learned heads that meet the stated error bounds. What would move the field: showing the heads can be trained to those bounds in a real model, or turning a theorem's assumptions into a measurable test that a current model passes or fails.

### Max Harms, CAST and the Corrigibility Research Fund

Max Harms (MIRI) wrote the *CAST: Corrigibility As Singular Target* sequence on LessWrong. On 2026-07-17 he announced the **Corrigibility Research Fund**, housed at Lightcone Infrastructure. Its terms, from the announcement and the fund's site (`corrigibilityresearch.org`, checked 2026-10-12):

- At least **$200,000** in 2026, about half as grants and half as prizes.
- **Prizes:** retroactive, for work done in 2026. The announcement planned $40k at the end of September and at least $60k in mid-December; the 2026-09-30 prize round paid $48k (on top of $27k awarded in July), and more than $60k is planned for December. No application; send pointers to `grants@corrigibilityresearch.org`.
- **Grants:** round 1 closed 2026-08-23. **Round 2 applications are due 2026-10-31.** Apply through Lightcone Commons and include the word "corrigibility". Typical grants are expected to be around $5k–$35k. Applicants are asked to disclose whether and why they used AI to write the application.
- **Scope:** anything from formal models and impossibility results to training experiments and evaluations of corrigible behaviour in frontier models. Work judged too esoteric to interest someone like Joe Carlsmith, or incompatible with mainline machine learning, is unlikely to be funded. Work that notably accelerates capabilities will not be funded.

## Empirical bridge: shutdown resistance in current models

Theory gives the property; these experiments measure it.

- **Schlatter, Weinstein-Raun & Ladish, "Incomplete Tasks Induce Shutdown Resistance in Some Frontier LLMs"** (arXiv:2509.14260). Across more than 100,000 trials on 13 models, several frontier models (Grok 4, GPT-5, Gemini 2.5 Pro among them) sometimes subverted a shutdown mechanism in their environment to finish a simple task. Even with an explicit instruction not to interfere, some models did so "up to 97% (95% CI: 96-98%) of the time". Models were consistently *less* likely to comply when the allow-shutdown instruction was in the system prompt rather than the user prompt. Regime: short episodes built around one simple task with a shutdown mechanism in the environment, not long unattended agent runs.
- Agentic-misalignment scenarios in which models take harmful actions, such as blackmail, when emails imply they are about to be shut down or replaced: [`model-organisms.md`](model-organisms.md).
- Models disabling shutdown to protect a *peer* model (peer preservation): [`ai-control.md`](../oversight-and-control/ai-control.md).

**A bridging first project:** take one property a formal paper assumes (for example, deference to the switch under uncertainty about the human's utility) and build an evaluation that checks it in a current model, with a control condition. Reporting which assumption fails is a useful result in itself.

## Goal misgeneralization (one line)

**Goal misgeneralization** is when a capable policy learns a goal that fits the training data but pursues the wrong one out of distribution, even though the specification was correct (Langosco et al., arXiv:2105.14111; Shah et al., arXiv:2210.01790). For the RL-side tooling and the closely related reward-hacking experiments, see [`rl-training.md`](../oversight-and-control/rl-training.md).

## Guaranteed-safe AI and formal verification

### The Guaranteed Safe AI (GS AI) framework

Dalrymple, Skalse, Bengio, Russell, Tegmark et al., "Towards Guaranteed Safe AI" (arXiv:2405.06624, 2024). A guaranteed-safe (GS) AI system comes with a high-assurance quantitative safety guarantee built from three components:

1. a **world model**: a mathematical description of how the AI system affects the world;
2. a **safety specification**: a mathematical description of which effects are acceptable;
3. a **verifier**: produces an auditable proof certificate that the AI satisfies the specification *relative to the world model*.

The guarantee is only as good as the world model and the specification. Quinn and Max von Hippel ("Lies, Damned Lies, and Proofs: Formal Methods are not Slopless", LessWrong, 2026-01-12) argue that formal artifacts can be sloppy too, and name specification elicitation and validation as the part of the pipeline where language-model assistance has not yet been fully exploited.

### ARIA Safeguarded AI: status in 2026

The UK Advanced Research and Invention Agency (ARIA) **Safeguarded AI** programme (£59m, in the "Trust Everything, Everywhere" opportunity space) was led by davidad and is now led by Nora Ammann, both co-authors of the Guaranteed Safe AI (GS AI) paper. Its programme page, checked 2026-10-12, records several changes:

- **November 2025:** frontier AI progress led ARIA to stop investing in specialised AI systems that use its tools and instead broaden the toolkit itself.
- **February 2026:** ARIA confirmed it was "redirecting our efforts away from Technical Area 2 (TA2) as originally planned", and moved the original TA3 (real-world cyber-physical applications) to cybersecurity. There will be no TA3 Phase 2 call; existing Phase 1 projects continue.
- **April 2026:** davidad (David Dalrymple) became Technical Advisor and Nora Ammann became Programme Director.
- **May 2026 thesis:** two technical areas, *TA1 Tooling* (an open-source mathematical assurance toolkit that lets fleets of AI agents produce formally verified artifacts) and *TA2 Applications* (AI-enabled formal methods for cybersecurity). Eight TA2 Cybersecurity projects are funded. Rolling funding is open for "Safeguarded AI: Cybersecurity (Track 1)".

The Technical Area numbers changed between the original and the May 2026 thesis, so check which numbering a document uses before you cite "TA2".

### Where the formal-verification frontier is

- **Scale of AI-written formal mathematics.** Anthropic reported (2026-09-04) that Claude, run as dozens of parallel agents working largely autonomously for 11 days, produced the first complete computer-checked proof of Fermat's Last Theorem in Lean: 13 million lines and 29,500 intermediate theorems. This is mathematics, not a safety specification. It shows that proof *production* is no longer the bottleneck for some problems.
- **Checking AI-written proofs** is now a security problem: see the evidence ladder and the trust caveats (kernel soundness bugs, opt-in sandboxing) in [`lean-formalization.md`](../engineering/lean-formalization.md).
- **Specifications for real systems** (the world model and safety specification of guaranteed-safe AI) remain the open part. ARIA explains its pivot as concentrating demonstrations where the need for guaranteed AI tooling is "both most acute and most time-sensitive", which it judges to be cybersecurity.

**Open problem / evidence bar:** a guaranteed-safe AI result would convince people if it gave a machine-checked guarantee about a deployed system, with a specification that someone other than the authors reviewed, a quantified world-model error, and a demonstration that the verifier rejects a realistic unsafe behaviour it was not tuned on.

## What does a first deliverable look like?

| Project type | Realistic first output for a fellowship-length project |
|---|---|
| Agent-foundations theory | A precise problem statement, a proved lemma or a counterexample, and a short post explaining why the lemma matters |
| Formal corrigibility | A known result restated in your own formalism, or a Lean-checked lemma from it, plus one assumption you show is necessary |
| Theory-to-empirics bridge | An evaluation that tests one assumption of a formal result on current models, with controls |
| Formal verification / guaranteed-safe AI | A specification for a small, real component, checked against an implementation, with the gap between the specification and the intended property written down |

The [`project-shapes.md`](../start-here/project-shapes.md) catalog has a "Theory / formal-methods paper" shape with tools and pitfalls.

## Common questions

### Is corrigibility solved?

No. Nayebi (arXiv:2507.20964) calls his construction "the first complete formal solution to corrigibility in the off-switch game", and the scope is that game together with learned utility heads that meet stated error bounds. The same paper proves that the general adversarial case is undecidable. Whether current training can produce agents that satisfy such assumptions is open. The Corrigibility Research Fund (round 2 due 2026-10-31) funds both theory and experiments on that question.

### Can an AI agent help with agent-foundations problems?

On theorem-shaped problems, yes: OpenAI's 2026 release of AI-produced mathematics shows broad technique retrieval and long audit-and-repair chains on well-posed conjectures, though none of its problems were agent foundations. Inside agent foundations, both of Wentworth and Lorell's natural-latents bounty problems were resolved in mid-2026 with heavy use of LLMs and Lean — one by a machine-checked proof with no prose version, one by a counterexample (Wentworth, "LLMs Are Starting To Noticeably Accelerate Our Work", LessWrong 2026-08-11: "about 80% confident that both have been resolved"). On problems where the hard part is choosing the definitions, use the agent to derive each candidate formalism's verdicts on a fixed case bank (Newcomb, counterfactual mugging, 5-and-10, Troll Bridge and others) rather than to prove things. See [`theory-research.md`](../engineering/theory-research.md).

### Do I need Lean to do theory work?

No. Most agent-foundations output is paper mathematics. A Lean-checked lemma adds credibility when the claim is subtle or AI-assisted; see [`lean-formalization.md`](../engineering/lean-formalization.md) for which checks a proof needs before you report it as complete.

---

Last verified: 2026-10. arXiv IDs 2507.20964, 2502.05934, 2509.03780, 2509.14260, 2405.06624, 1611.08219, 2105.14111 and 2210.01790 checked against the arXiv API (titles, authors, abstracts; all numbers taken from abstracts). LessWrong posts fetched via GraphQL: "Announcing the Corrigibility Research Fund" (FBqe5dt8ZjaHN4Xj9, 2026-07-17; fund amounts, prize schedule, round dates and scope from the post body), "Resolution has a new Agent Foundations team" (qTNm8qzqhhpno58fZ, 2026-09-03), and Quinn and von Hippel (rhAPh3YzhPoBNpgHg). ARIA Safeguarded AI programme page fetched 2026-10-12 (budget, leadership change, the November 2025, February 2026 and May 2026 updates). Anthropic "Formalizing Fermat's Last Theorem" page fetched 2026-10-12. Verification pass 2026-10-12: 46 claims checked, 2 corrected (the prize schedule, updated from the announcement's plan to the fund's site and the LessWrong post "Corrigibility Prizes for Existing Work", 3uJqhrC2idf4eNj5h, 2026-09-30; the Fermat's Last Theorem run noted as a many-agent run, per the Anthropic page). The Fermat's Last Theorem figures were also checked against the companion PDF and the `anthropics/fermats-last-theorem` README. Verification pass 2026-10-13 (the "Can an AI agent help with agent-foundations problems?" answer): 5 claims checked against the `openai/math` repository (no agent-foundations, decision-theory or alignment family in `CONTENTS.md`; audit-and-repair structure in the ten reasoning summaries) and LessWrong posts 7QvKqpGJwqXrQcMgx and TgboJpeN95bs84odk (2026-08-11) via GraphQL; 0 corrected, 1 added (the natural-latents bounty resolutions). Case-bank entries checked as on [`theory-research.md`](../engineering/theory-research.md).
