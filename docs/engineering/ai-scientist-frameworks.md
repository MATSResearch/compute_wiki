---
tags:
  - engineering
  - evaluation
---

# AI Scientist Frameworks

Systems that automate part or all of the research loop: read the literature,
form a hypothesis, write the code, run the experiment, interpret the result,
write it up. They are worth knowing about because they are getting good enough
to be tempting, and because the ways they fail are specific, documented, and
easy to miss in a finished-looking paper.

This doc is about **using them for your own research**. For running an agent CLI
*as the subject of an eval*, see
[`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).

## At a glance

| You want… | Use | Caveat |
|---|---|---|
| Hypotheses / research directions, no execution | **AI co-scientist** (Google) | Generates and ranks hypotheses; does not run or analyse experiments |
| Discovery over **your own dataset** | **Kosmos** | Long runs (~12h); the world-model design is the interesting part |
| Squeeze a benchmark number out of an ML task | **AIDE**, **MLE-STAR** | Optimisers, not scientists. This is the tier that actually works. |
| Rigorous experiment *control* (conditions, confounds) | **Curie** | Explicitly targets rigour rather than throughput |
| A co-pilot that keeps you in the loop | **Agent Laboratory** | Designed *not* to pick its own direction — often the right call |
| End-to-end paper from an idea | **AI Scientist-v2** (Sakana), **Jr. AI Scientist** | Read the failure-modes section before you trust output |
| Claims that trace to evidence | **ScientistOne** / Chain-of-Evidence | The most useful 2026 idea here, whether or not you use the system |

## The tiers, and which one is real

Lumping these together as "AI scientists" hides the thing that matters: they
automate very different amounts, and the reliability drops sharply as the
automation goes up.

**Tier 1 — bounded optimisation.** AIDE (WecoAI) drives an agentic tree search
over ML code: draft, debug, benchmark, repeat. On OpenAI's MLE-bench (75 Kaggle
competitions) it wins ~4× more medals than the best linear agent. MLE-STAR is a
similar lightweight multi-agent pipeline. These work because the objective is a
number and the environment tells the truth about it.

**Tier 2 — controlled experimentation.** Curie adds intra-agent and inter-agent
"rigour modules" plus an experiment-knowledge module, aiming at reproducibility
rather than leaderboard position. Agent Laboratory deliberately stops short of
picking its own research direction and positions itself as a co-pilot.

**Tier 3 — end-to-end discovery.** Sakana's AI Scientist-v2 removes v1's
human-authored code templates and uses progressive agentic tree search under an
experiment-manager agent; it produced the first entirely AI-generated paper
accepted at a peer-reviewed workshop. Kosmos takes an objective and a dataset
and runs ~200 agent rollouts over ~12 hours — averaging ~42,000 lines of code
executed and ~1,500 papers read per run — sharing state between a data-analysis
agent and a literature agent through an explicit **structured world model**. Of
seven reported discoveries, three reproduced findings from unpublished
manuscripts and four were claimed as novel.

Tier 3 is the exciting tier and the one to be most careful with. AI Scientist v1
was reported to have a **42% experiment failure rate**, with hallucinations that
its own review scores did not catch.

**The useful reading of this split is not "tier 3 soon".** It is that the
reliable tier is the one where the environment can contradict the agent — a
metric it cannot argue with, a test that fails, a command that exits non-zero.
Automation is safe exactly to the degree that something other than the model
gets to say the answer is wrong. That is a property to design *for*, not a stage
to grow out of, and it is why an assistant that does the straightforward parts
under a researcher's eye is a different and better-founded thing than a
miniature scientist — not a less ambitious version of one.

## Failure modes: the part to actually read

This literature is unusually good, because several groups went looking for the
failures rather than the wins. Treat this as a checklist for anything an agent
hands you — including your own agent.

**Process failures** (["The More You Automate, the Less You See"](https://arxiv.org/abs/2509.08713),
arXiv:2509.08713). Assessing two prominent open-source AI-scientist systems
turned up four failures, "across a spectrum of severity, which can easily be
overlooked in practice":

1. **Inappropriate benchmark selection** — an unsuitable dataset or metric.
2. **Data leakage** — train/test contamination.
3. **Metric misuse** — wrong measure, or wrong reading of the right one.
4. **Post-hoc selection bias** — choosing the analysis after seeing the results.

Their recommendation is the load-bearing one: **examining the final paper is not
enough oversight**. They argue venues evaluating AI-generated research should
require the *trace logs and code from the full automated workflow*, because
increased automation obscures the process and these errors are invisible in the
write-up.

**Reasoning failures** — "Correct Answer, Wrong Mechanism"
([arXiv:2606.23175](https://arxiv.org/abs/2606.23175), Eulig, June 2026). Agents
reach right-looking results through reasoning that breaks when conditions
change. Measured on agents rediscovering a particle-identification observable in
a physics simulation, scoring outcome, *mechanism fidelity* and *epistemic
honesty* separately: CAWM in **4/20 episodes** for the primary model and
**3/8** in a cross-model probe. One agent defended claims inconsistent with its
own data. The conclusion is worth quoting in spirit: reliable tools for specific
tasks, unreliable collaborators for open-ended claims **unless the mechanism is
verified separately from the answer**.

**Corpus failures** — "Dead Science Walking"
([arXiv:2606.04220](https://arxiv.org/abs/2606.04220), Chauhan, June 2026).
Publication bias is in the retrieval corpus, so an AI scientist amplifies it. It
estimates a **null-result gap** by domain (drug discovery ~0.60, psychology
~0.56, cancer biology ~0.35) and that a standard three-stage pipeline amplifies
corpus distortion by about **2.18×**. Its named failure mode, **confident
rediscovery**, is the sharp one for alignment work: the system proposes a
*known-falsified* hypothesis as a promising new direction, because
pre-registered failures and meta-scientific argument are not in the corpus while
the positive pre-replication literature is.

Other modes reported across this literature: implementation bugs,
bug-as-insight reframing, methodology fabrication, frame-lock, and citation
hallucination.

## Verifiability: Chain-of-Evidence

The most useful idea of 2026 here, and it is portable — you can adopt the
discipline without adopting the system.

**ScientistOne** ([arXiv:2605.26340](https://arxiv.org/abs/2605.26340), Meng,
Dalvi Mishra, Chen, Li, Goyal, Parmar, Song, Song, Sinha, Ranganathan, Gokturk,
Yoon, Pfister — Google, May 2026) requires **every claim to trace to its
grounding evidence** across literature review, solution discovery and manuscript
composition. Its **CoE Audit** is a post-hoc protocol with four integrity
checks:

| Check | Catches |
|---|---|
| **Score verification** | Reported numbers that the run does not support |
| **Specification violation** | Described method ≠ method actually run |
| **Reference verification** | Hallucinated citations |
| **Method–code alignment** | Implementation ≠ documentation |

Across 75 papers from five systems, the baselines are grim and the numbers are
the reason to care: hallucinated reference rates up to **21%**, score
verification passing in only **42%** of papers, method–code alignment ranging
**20–80%**. ScientistOne reports zero hallucinated references and full score
verification. Google's write-up of the framework also reports a live
LLM-training competition where baselines failed to produce valid submissions
under the hardware and file-size constraints and Science One did.

**Run the four checks on your own agent's output by hand.** They are cheap, and
"score verification passed in 42% of papers" tells you the base rate you are
working against.

## Benchmarks

Judge a system by which of these it was measured on, because they test
different things and the easy ones are much easier.

| Benchmark | Tests |
|---|---|
| **MLE-bench** (OpenAI) | End-to-end ML engineering on 75 Kaggle competitions. Leaderboard was closed to new submissions as of April 2026 pending fairness work. |
| **RE-Bench** (METR) | 7 open-ended ML research-engineering tasks, human-calibrated |
| **PaperBench** (OpenAI) | Reproduce a paper's methods and experiments, hierarchical rubrics |
| **ScienceAgentBench** | Data-driven discovery tasks extracted from peer-reviewed papers |
| **AstaBench** (AI2) | 2400+ problems across the whole discovery pipeline, **cost-controlled** |
| **ReplicationBench** | Replicating astrophysics papers |
| **CORE-Bench** | Computational reproducibility of published research |

**AstaBench** is the one to quote when someone claims the problem is solved: 57
agents across 22 agent classes, with tool access and model cost controlled as
confounds, and the conclusion that **AI remains far from solving scientific
research assistance**. Cost control matters — without it you cannot tell a
better agent from a bigger budget.

## If you are using one for MATS work

- **Tier 1 is safe, tier 3 is a draft.** Letting an agent optimise a number
  against a real metric is ordinary tooling. Letting it decide what the result
  means is where the failure modes live.
- **Verify the mechanism separately from the answer.** CAWM is invisible if you
  only check whether the number looks right. A regime-shift check — does the
  explanation still hold when you change a condition it should not depend on? —
  is cheap and catches it.
- **Keep the trace, not just the paper.** This is the concrete recommendation
  from the pitfalls paper, and it is the only way the four process failures are
  detectable at all. See
  [`training-on-trajectories.md`](../oversight-and-control/training-on-trajectories.md)
  for what a capture has to preserve — verbatim tool output, failures included,
  every span labelled by origin.
- **Watch for confident rediscovery in alignment specifically.** Our null-result
  literature is thin and much of the useful negative evidence lives in LessWrong
  comments, workshop rejections and lab-internal Slack, none of which is in a
  retrieval corpus. An agent proposing a "promising new direction" that three
  people quietly tried in 2024 is the expected behaviour, not an aberration.
- **Disclose the agent.** Agents4Science and a growing number of venues have
  explicit policies; assume you must state what was automated.

## Common questions

### Are these good enough to write a MATS paper?

No — but they are good enough to produce something that *looks* like one, which
is the actual hazard. The measured base rates above (42% score verification,
20% CAWM, 21% phantom references) are what you are accepting if you do not
check.

### Is there a safety angle beyond research quality?

Yes, two. Automated AI R&D is itself a dangerous-capability category that
RE-Bench and HCAST exist to measure, so these systems are both a tool and a
subject. And "Jr. AI Scientist"
([arXiv:2511.04583](https://arxiv.org/abs/2511.04583)) is a deliberate risk
report from building one — it generated papers building on real NeurIPS, IJCV
and ICLR publications and documents the risks of applying such systems directly.

### What should I read first?

The pitfalls paper (arXiv:2509.08713) for what goes wrong, and the ScientistOne
CoE Audit for a checklist to apply. Both are short and neither requires you to
adopt any system.

## Cross-references

- Running agent CLIs as the subject of an eval:
  [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).
- Inspect Scout for scanning agent transcripts for problems:
  [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md).
- What an agent-trace capture must preserve:
  [`training-on-trajectories.md`](../oversight-and-control/training-on-trajectories.md).
- Statistical discipline the four integrity checks assume:
  [`statistics.md`](statistics.md).

---

Last verified: 2026-08. Papers read directly: ScientistOne (arXiv:2605.26340),
"The More You Automate, the Less You See" (arXiv:2509.08713), AstaBench
(arXiv:2510.21652), "Dead Science Walking" (arXiv:2606.04220), "Correct Answer,
Wrong Mechanism" (arXiv:2606.23175), Jr. AI Scientist (arXiv:2511.04583,
abstract only — its concrete risk list is in the full PDF and is NOT summarised
here). System descriptions for AIDE, Curie, Agent Laboratory, MLE-STAR, Kosmos
and AI Scientist-v2 come from their own repos/papers; their headline numbers are
self-reported and have not been independently checked here. Drafted by Claude;
pending MATS research-staff review.
