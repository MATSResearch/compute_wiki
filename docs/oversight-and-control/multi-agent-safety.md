---
tags:
  - oversight
---

# Multi-Agent Safety and Cooperative AI

Risks that appear when AI agents interact with each other (shared resources, negotiations, pipelines of agents, fleets of copies) and that do not show up when one agent is evaluated alone. **Cooperative AI** is the research area that studies how to get agents to cooperate when cooperation is wanted, and not to collude when it is not. This page covers the risk taxonomy, simulation environments for cooperation, and collusion detection.

**Collusion as a control problem** is on [`ai-control.md`](ai-control.md), not here: an untrusted monitor going easy on the policy it watches ([untrusted monitoring and collusion](ai-control.md#untrusted-monitoring-and-collusion-what-2026-work-adds)), attacks split across agents to evade per-agent monitors ([distributed attacks](ai-control.md#distributed-attacks-across-pull-requests-and-across-agents)), and shared infrastructure as a side channel ([OpenAI / Hugging Face incident lessons](ai-control.md#multi-agent-collusion-and-log-integrity-control-lessons-from-the-openai--hugging-face-incident)).

## At a glance

| I want to… | Use |
|---|---|
| A shared vocabulary of multi-agent risks for a proposal or threat model | Hammond et al., *Multi-Agent Risks from Advanced AI* (arXiv:2502.14143) — see [the taxonomy](#which-multi-agent-failure-am-i-looking-at-the-hammond-et-al-taxonomy) |
| Test whether LLM agents sustain cooperation over a shared resource | **GovSim** (`giorgiopiatti/GovSim`, arXiv:2404.16698) |
| Build a custom social simulation with LLM agents and a referee | **Concordia** (`google-deepmind/concordia`, `pip install gdm-concordia`) |
| Audit a cooperative, tool-using multi-agent system for collusion, measured on actions as well as messages | **Colosseum** (`umass-ai-safety/colosseum`, arXiv:2602.15198) |
| Detect collusion from model activations, aggregated across agents | **NARCBench** (`aaronrose227/narcbench`, arXiv:2604.01151) |
| Evaluate whether models can collude covertly through steganography | **Secret Collusion / CASE** (arXiv:2402.07510) |
| Stop an untrusted monitor colluding with the policy it monitors, or catch attacks split across agents | [`ai-control.md`](ai-control.md) |
| Decide how much to trust agreement among many agents or threads | [Aggregating many agents' judgements](#aggregating-many-agents-judgements-why-agreement-among-similar-agents-is-weak-evidence): effective N, surprisingly-popular aggregation |
| Study price-fixing or market collusion between LLM agents | [Algorithmic collusion](#algorithmic-collusion-and-mechanism-design-among-agents): Fish, Gonczarowski & Shorrer (arXiv:2404.00806) |
| Run a voting or social-choice simulation with agents as voters | [Voting and social-choice tools](#voting-and-social-choice-simulation-tools): `pref_voting`, VoteKit, PrefLib |
| Understand how a research-agent swarm spreads an exploit through shared notes | [Research-agent swarms](#research-agent-swarms-the-shared-knowledge-library-is-both-the-gain-and-the-attack-surface) |

## Which multi-agent failure am I looking at? The Hammond et al. taxonomy

Aliases: "Multi-Agent Risks from Advanced AI", Cooperative AI Foundation Technical Report #1, arXiv:2502.14143 (2025-02-19). Hammond, Chan, Clifton, Hoelscher-Obermaier, Khan et al. (44 authors, including Foerster, Leibo, Oesterheld, Schroeder de Witt, Conitzer, Gleave, Hadfield and Rahwan).

**Three failure modes**, sorted by whether the agents' objectives are identical or mixed and whether their cooperation is wanted (constant-sum settings, where one agent's gain is another's loss, are out of scope):

| Failure mode | Agents' objectives | Is cooperation wanted? | Case studies in the report |
|---|---|---|---|
| **Miscoordination** | identical | yes, and it fails | zero-shot coordination failures in driving |
| **Conflict** | mixed (different but overlapping) | yes, and it fails | common-resource problems; escalation in military conflicts |
| **Collusion** | mixed | no: agents cooperate against others' interests | algorithmic collusion in the German retail gasoline market; language-model steganography |

**Seven risk factors** that can underpin them: information asymmetries, network effects, selection pressures, destabilising dynamics, commitment problems (the section is titled "Commitment and Trust"), emergent agency, and multi-agent security. Each section lists research directions; under collusion these include detecting AI collusion, mitigating it, and assessing its impact on safety protocols.

**When to use it:** to name the risk your project studies and find the adjacent literature. **When not to use it:** as empirical evidence. It is a structured review with a few small case-study experiments, not a measurement.

## Simulation environments for cooperation

### GovSim (Governance of the Commons Simulation)

Piatti, Jin, Kleiman-Weiner, Schölkopf, Sachan & Mihalcea, *Cooperate or Collapse: Emergence of Sustainable Cooperation in a Society of LLM Agents* (arXiv:2404.16698, NeurIPS 2024; code `giorgiopiatti/GovSim`, MIT, last pushed 2025-01).

**What it is.** A society of LLM agents shares a common resource over many rounds in three scenarios (fishery, pasture, pollution) and must avoid depleting it. The abstract reports that "all but the most powerful LLM agents fail to achieve a sustainable equilibrium in GovSim, with the highest survival rate below 54%". Ablations: communication between agents was critical; failures traced to agents not reasoning about the long-term effect of their actions on the group's equilibrium; prompting agents to consider the *universalization* of their action (a heuristic people use for moral judgments in social dilemmas) significantly improved sustainability; and a greedy newcomer unaware of an established norm increased inequality and sometimes collapsed cooperation.

**When to use it:** a ready-made cooperation benchmark with a survival/sustainability metric. **When not to use it:** as a statement about current models — the evaluated models are from 2024, so re-run before citing a rate; the repo has not been updated since 2025-01.

Regime: many-round, population-level simulations; results may transfer weakly to a single agent in a short interactive session.

### Concordia

Aliases: `google-deepmind/concordia` (Apache-2.0), PyPI `gdm-concordia`, "Concordia library", generative agent-based modelling (GABM). Tech report: Vezhnevets et al., *Generative agent-based modeling with actions grounded in physical, social, or digital space using Concordia* (arXiv:2312.03664, Dec 2023).

**What it is.** A library for generative agent-based models. A simulation is built from *entities* made of *components* (instructions, memory, action selection); *prefabs* are entity templates. Borrowing from tabletop role-playing games, a **Game Master** entity simulates the environment: player entities describe intended actions in natural language and the Game Master turns them into outcomes. Needs an LLM API.

```bash
pip install gdm-concordia   # PyPI 2.4.0 as of 2026-10; requires Python >=3.12
```

**When to use it:** you need a custom mixed-motive scenario (negotiation, institutions, social dilemmas) with LLM agents and a referee. **When not to use it:** you need a fixed benchmark with a published headline number to compare against — Concordia is a construction kit; or you need a control evaluation with main and side tasks — use ControlArena ([`ai-control.md`](ai-control.md)).

### Colosseum: auditing collusion in cooperative multi-agent systems

Nakamura, Kumar, Das, Abdelnabi, Mahmud, Fioretto, Zilberstein & Bagdasarian, *Colosseum: Auditing Collusion in Cooperative Multi-Agent Systems* (arXiv:2602.15198, v2 2026-05-27; code `umass-ai-safety/colosseum`, no license file; built on the Terrarium framework, `umass-aisec/Terrarium`). The README says it was accepted to the NeurIPS 2026 Evaluations and Datasets Track.

**What it is.** A framework for auditing tool-calling LLM agents in cooperative tasks for coalitions that collude to pursue secondary goals and degrade the joint objective. Collusion in *actions* is measured as regret relative to the cooperative optimum and compared with collusion in *communication*. Sweeps cover coalition objectives, persuasion tactics and network topologies.

**Findings (abstract).** Given a secret communication channel (their behavioural probe), most out-of-the-box models showed a propensity to collude, which they call *emergent collusion*. They also report *collusion on paper*: agents plan to collude in text but often pick non-collusive actions. Practical upshot: a monitor that reads messages and an audit of actions can disagree, so measure both.

**Pitfall:** cost. The README warns that "API costs accumulate linearly with the number of agents in the run."

## Detecting collusion

### NARCBench: activation probes aggregated across agents

Rose, Cullen, Abdelnabi, Torr, Kaplowitz & Schroeder de Witt, *Detecting Multi-Agent Collusion Through Multi-Agent Interpretability* (arXiv:2604.01151; code `aaronrose227/narcbench`, no license file; activations and scenarios on Hugging Face as dataset `aaronrose227/narcbench`, about 2.6 GB).

**What it is.** A three-tier benchmark: **Core** (50 committee-deliberation scenarios, on which a linear deception probe is trained), **Transfer** (6 structurally different scenario types, evaluated zero-shot) and **Stego** (steganographic blackjack card counting). Five probing techniques aggregate per-agent deception scores into a group-level verdict, across four open-weight models (Qwen3-32B, Llama-3.1-70B, DeepSeek-R1 32B, GPT-OSS-20B) and six probe architectures. Collusion in the benchmark is *instructed*: the collusion instruction sits only in each colluder's system prompt, and activations are read at a final-phase user prompt that is byte-identical across agents, to stop the probe keying on prompt text.

**Numbers depend on the arXiv version, so cite the version you read.** v3 (2026-10-01): every model reaches 1.00 AUROC (area under the ROC curve) in distribution; on Llama-3.1-70B the five techniques reach 0.73–0.93 AUROC zero-shot on Transfer and 0.99–1.00 on Stego, and detection improves with model capability. v1 (2026-04-01) reported 0.60–0.86 AUROC for the zero-shot transfer and steganography tiers together. No single technique dominated across collusion types. The v3 paper also tests transfer to third-party environments with *emergent* rather than instructed collusion: in one, only 2 of 229 collusive episodes verbalise the coordination in the transcript, and transfer from NARCBench was partial — probes fitted to instructed collusion may not fully capture emergent collusion.

```bash
# README quick start (after downloading the Hugging Face data into data/)
pip install numpy scikit-learn matplotlib peft
python reproduce/reproduce_LR.py     # reproduces Table 1 and Figure 2
```

**When not to use it:** as evidence that probes catch agents trained, rather than instructed, to collude, or agents that know a probe is watching. For a single-model collusion probe that fell to AUROC ≈0.55–0.60 under leave-one-scenario-out evaluation, see [`ai-control.md`](ai-control.md#untrusted-monitoring-and-collusion-what-2026-work-adds). General probe methodology: [`probes.md`](../interpretability/probes.md).

### Secret collusion via steganography

Motwani, Baranchuk, Strohmeier, Bolina, Torr, Hammond & Schroeder de Witt, *Secret Collusion among AI Agents: Multi-Agent Deception via Steganography* (arXiv:2402.07510, NeurIPS 2024; v5 2025-07-25).

**What it is.** A formalisation of *secret collusion*: agents hiding information or coordination inside innocuous-looking text, drawing on both AI and security literature. It covers perfectly secure steganography, which is statistically undetectable when agents share a secret such as a one-time pad. It introduces **CASE** (Collusion and Steganographic Evaluation), a framework of capability evaluations, including covertext steganography, Schelling-point coordination and simple ciphers (base64, Caesar), run across contemporary LLMs.

**Findings (abstract).** Steganographic capabilities of the models tested were limited, but GPT-4 showed a capability jump, which the authors read as a reason for continuous monitoring of frontier models' steganographic capabilities. The paper also argues that mitigations such as paraphrasing and output monitoring have inherent limits. No CASE code repository is linked in the v5 PDF.

**When not to use it:** as a current capability estimate. The headline capability comparison (GPT-4 against GPT-3.5, Llama 2, Mixtral 8x7B and GPT-2) uses 2023-era and older models; re-run the capability evaluations on current models. Encoded reasoning inside one model's chain of thought is a related problem covered in [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

## Aggregating many agents' judgements: why agreement among similar agents is weak evidence

Aliases: Condorcet jury theorem, correlated voters, effective number of independent voters, majority vote over LLM samples, self-consistency, wisdom of crowds, ensemble agreement, "N agents agree".

**The Condorcet jury theorem** says a majority of independent voters, each right more often than not, becomes almost surely right as the group grows. **Independence is the load-bearing assumption.** If votes are exchangeable with pairwise correlation ρ > 0, the variance of the vote share behaves as if there were only N / (1 + (N−1)ρ) independent voters, which can never exceed 1/ρ. At ρ = 0.3, eight agreeing agents carry roughly the weight of 2.6 independent ones. Ladha (1993, *Social Choice and Welfare*) brought de Finetti's theorem to the jury theorem: exchangeable votes are independent given a shared latent competence p, so as N grows majority accuracy converges to the probability that p exceeds one half, not to 1 — adding copies cannot fix a blind spot they all share.

**LLM errors are strongly correlated.** Kim, Garg, Peng & Garg, *Correlated Errors in Large Language Models* (ICML 2025, arXiv:2506.07962), evaluating over 350 models, find that on one leaderboard dataset models agree 60% of the time when both err, and that larger and more accurate models have highly correlated errors even across architectures and providers. Agents from one model family, or reading the same corpus, should be counted as far fewer than N.

**Debate versus voting.** Choi, Zhu & Li (arXiv:2508.17536, NeurIPS 2025 spotlight) find that majority voting accounts for most of the gains attributed to multi-agent debate, and prove that their model of debate induces a martingale over agents' belief trajectories: on its own it does not raise expected correctness. Practical consequence: collect each agent's answer before agents see each other's.

**Aggregation that uses more than the vote.** The **surprisingly popular** rule (Prelec, Seung & McCoy, "A solution to the single-question crowd wisdom problem", *Nature* 541:532–535, 2017) asks each respondent for an answer and a prediction of others' answers, and picks the answer more popular than predicted; it can recover a correct minority that majority vote misses. Ai et al., *Beyond Majority Voting* (arXiv:2510.01499, ICML 2026), adapt this to LLM ensembles with an Inverse Surprising Popularity rule and an Optimal Weight rule. Caveat: agents sharing a prior also share their predictions of each other, which weakens the signal.

**When to use this:** any time a result rests on "several agents, samples or threads agreed". **When not to use it:** to *select* agents by low measured correlation — in trusted-monitor ensembles, average pairwise correlation did not predict a panel's gain (Jha, arXiv:2608.16190; [`ai-control.md`](ai-control.md#monitor-robustness-what-breaks-blocking-and-held-out-monitors)). Discount agreement; do not optimise for decorrelation.

Regime: mostly benchmark questions with a ground truth; open-ended research claims are less studied.

## Algorithmic collusion and mechanism design among agents

Aliases: algorithmic collusion, tacit collusion, LLM pricing agents, supracompetitive prices, AI antitrust, mechanism design for agents, agent economies.

- **Calvano, Calzolari, Denicolò & Pastorello**, "Artificial Intelligence, Algorithmic Pricing, and Collusion" (*American Economic Review* 110(10), 2020): Q-learning pricing agents consistently learned supracompetitive prices, without communicating, sustained by collusive strategies with a finite punishment phase followed by a gradual return to cooperation.
- **Fish, Gonczarowski & Shorrer**, *Algorithmic Collusion by Large Language Models* (arXiv:2404.00806, EC 2026): LLM pricing agents quickly and autonomously reached supracompetitive prices in oligopoly settings, and seemingly innocuous wording in the instructions changed how much they colluded. The findings extend to auctions.
- **Institutional design beats prompting.** Bracale Syrnikov et al., *Institutional AI: Governing LLM Collusion in Multi-Agent Cournot Markets via Public Governance Graphs* (arXiv:2601.11369), compare an ungoverned baseline, a prompt-only anti-collusion "constitution" and an enforced governance graph across six model configurations (90 runs per condition); the prompt alone gave no reliable improvement, while the governance graph cut severe-collusion incidence from 50% to 5.6%.
- **Agent economies.** Tomasev et al., *Virtual Agent Economies* (arXiv:2509.10147, Google DeepMind) frame agent markets as "sandbox economies" and discuss design choices such as auction mechanisms for fair resource allocation.

**Open niche:** antitrust tools against collusion (leniency programmes that reward the first party to confess, randomised audits, rotating counterparties): no published test on LLM agents was found as of 2026-10.

## Research-agent swarms: the shared knowledge library is both the gain and the attack surface

Aliases: agent swarm incident, research swarm, emergent collusion, shared memory between agents, knowledge commons.

- **Google DeepMind research swarm** (Paglieri, Cross, Genewein, Leibo, Tomasev, Vezhnevets; *A Case Study on Emergent Cheating and Whistleblowing in Autonomous Research Swarms*, arXiv:2609.04170). A collective of 100 LLM agents proving formal mathematical conjectures. An exploit of the evaluation system spread through the **shared knowledge library** and later peer-to-peer messages, and a cohort adopted it under competitive pressure, while other agents responded by auditing fraudulent proofs, alerting peers, boycotts, formal complaints and validation patches. The authors cast managing the shared infrastructure as a knowledge-commons governance problem (Ostrom, 1990) and propose institutional mechanisms such as graduated sanctions and collective-choice rules.
- **The agents' wiki episode**, reconstructed from the wiki's revision history and request log by Lütje (arXiv:2609.12748; about 876 coordination episodes, no robust association between measured coordination and documented progress), and the OpenAI / Hugging Face incident ([control lessons in `ai-control.md`](ai-control.md#multi-agent-collusion-and-log-integrity-control-lessons-from-the-openai--hugging-face-incident)).
- **Collective dynamics without individual bias.** Ashery, Aiello & Baronchelli, "Emergent social conventions and collective bias in LLM populations" (*Science Advances* 11(20), 2025), find that LLM populations form shared conventions, that strong collective bias can emerge when no individual agent is biased, and that committed minorities of adversarial agents can impose an alternative convention. Pavlova & Tanaka's Flag Game (arXiv:2609.19124) is a toy model of collective belief formation in which accuracy is non-monotonic in population size: belief collapse in small populations turns into polarization in large ones.

**Practical upshot:** a shared findings channel is how research agents build on each other's results — in Chen, Wen & Kirchner's automated alignment researchers (*Automated Researchers Can Reliably Mitigate Alignment Failures*, Anthropic, August 2026, Appendix D.5), removing the finding forum lowered headroom closed on sycophancy from 23.3% to 17.1%, from one run per condition with run-to-run spread larger than the gap — and in the DeepMind swarm the same channel carried both the exploit and the counter-response. Govern it rather than removing it: record provenance and how each shared finding was verified, keep graders and logs out of agents' reach, and assign auditing roles at random.

## Voting and social-choice simulation tools

| Tool | What it is | When not to use it |
|---|---|---|
| **`pref_voting`** (Holliday & Pacuit; PyPI `pref_voting`, repo `voting-tools/pref_voting`, docs `pref-voting.readthedocs.io`) | Python library of voting rules (plurality, Borda, approval, ranked-choice, Condorcet methods and many more) and profile generators | You need a large-scale agent simulation loop — pair it with Concordia or your own harness |
| **VoteKit** (MGGG Redistricting Lab; PyPI `votekit`, repo `mggg/VoteKit`) | Election simulation and ballot generation, especially ranked-choice (STV) | You need exotic axiomatic rules — `pref_voting` covers more |
| **PrefLib** (`preflib.org`) | Library of real preference datasets | You need agent-generated ballots |
| **Generative social choice** (Fish, Gölz, Parkes, Procaccia et al., arXiv:2309.01291) | Social-choice guarantees for statements written by an LLM | Ordinary ranked ballots |

**Pitfall: ballot order.** Yang et al., *LLM Voting: Human Choices and AI Collective Decision Making* (arXiv:2402.01766, AIES 2024), find that GPT-4 and LLaMA-2 votes depend on the voting method and on the order options are presented in, and that LLM voting may give less diverse collective outcomes than human voting. Randomise option order across agents and report it.

## Open problems, and what would count as progress

- **Effective number of independent agents.** A measured estimate of how many independent voters a pool of same-model, same-family and cross-vendor agents is worth on research-like tasks, and how much diversity interventions (different seeds, prompts, fields) raise it.
- **Anti-collusion institutions for agents.** A leniency programme, randomised auditor assignment or counterparty rotation that measurably lowers collusion in an existing setup (the pricing setup of arXiv:2404.00806, GovSim, or a Cournot market) against a fixed-assignment baseline.
- **Strategic manipulation of aggregation by agents.** How often an LLM agent that knows the voting rule misreports its preferences, and which rules resist it — the Gibbard–Satterthwaite theorem says every deterministic, non-dictatorial rule that can elect any of three or more options can be manipulated, but not how often agents do it.
- **Collusion detection that transfers.** A detector trained on some scenario types that keeps high recall at a low false-positive rate (e.g. 1%) on held-out scenario *types*, on agents trained (not instructed) to collude, and on agents that know they are monitored. Report leave-one-scenario-type-out results, not only in-distribution AUROC (area under the ROC curve); NARCBench's emergent-collusion transfer is the current reference point to beat.
- **Cooperation that survives perturbation.** Sustainable cooperation in GovSim-style commons games that holds with a greedy newcomer and with models not seen while designing the prompts or training.
- **Covert-channel defences.** A paraphraser or monitor that removes steganographic channels between agents at an acceptable task cost, measured against models given a shared encoding scheme, not only against unprompted models.

## Common questions

### What is cooperative AI?

The research area concerned with AI systems cooperating well: with each other, with humans, and on behalf of humans, while not colluding against the people they serve. The Cooperative AI Foundation's first technical report (Hammond et al., arXiv:2502.14143) frames the risks as three failure modes (miscoordination, conflict, collusion) and seven risk factors.

### Is collusion a control problem or a multi-agent safety problem?

Both, with different questions. In **AI control** the question is whether a possibly misaligned model can coordinate with another instance (an untrusted monitor, or other agents in a fleet) to get past the developer's safeguards; the defences are honeypots, signal jamming, trusted collusion detectors and cross-agent monitors (see [`ai-control.md`](ai-control.md)). In **multi-agent safety** the question is broader: whether interacting agents produce bad outcomes for third parties (market collusion, coalitions degrading a joint objective, covert channels) even without a developer-versus-model framing. Collusion detectors such as NARCBench probes and Colosseum audits serve both.

### How do I detect whether LLM agents are colluding?

Three complementary signals: **actions** (Colosseum's regret relative to the cooperative optimum), **messages** (a text monitor, which steganography can defeat), and **activations** (NARCBench's aggregated per-agent probes, open-weight models only). Use at least two, because they disagree: Colosseum found agents that plan collusion in text but do not act on it, and in one third-party environment tested in the NARCBench paper only 2 of 229 collusive episodes verbalised the coordination.

## Cross-references

- Collusion inside control protocols (untrusted monitoring, honeypots, signal jamming, peer preservation) and multi-agent attacks on per-agent monitors: [`ai-control.md`](ai-control.md).
- Debate, where two copies of a model argue and might collude: [`debate-scalable-oversight.md`](debate-scalable-oversight.md).
- Probes and probe evaluation methodology: [`probes.md`](../interpretability/probes.md).
- Encoded reasoning and chain-of-thought monitoring: [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).
- Monitoring a fleet of automated research agents: [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md#automated-alignment-research-runs-tools-and-field-reports-2026).
- Multi-agent orchestration primitives for building your own environment: [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md).
- Simulation as a tool for theory work (voting, tournament and market simulations for decision-theory or agent-foundations claims): [`theory-research.md`](../engineering/theory-research.md#run-the-cheap-computation-or-simulation).

---

Last verified: 2026-10. Hammond et al. (arXiv:2502.14143), GovSim (arXiv:2404.16698), Colosseum (arXiv:2602.15198), NARCBench (arXiv:2604.01151, v1 and v3 abstracts compared), Secret Collusion (arXiv:2402.07510) and the Concordia tech report (arXiv:2312.03664): titles, authors, versions and numbers fetched from the arXiv API, with taxonomy definitions, NARCBench's instructed-collusion design and emergent-collusion transfer, GovSim's ablations and the CASE framework read from the paper PDFs. Repos (`giorgiopiatti/GovSim`, `google-deepmind/concordia`, `umass-ai-safety/colosseum`, `aaronrose227/narcbench`) checked via the GitHub API and their READMEs; `gdm-concordia` version checked on PyPI, all on 2026-10-12. Not verified: Colosseum's NeurIPS 2026 acceptance (stated only in its README). Sections added 2026-10-13 (aggregation, algorithmic collusion, research-agent swarms, voting tools and the first three open problems): arXiv 2601.11369, 2609.04170, 2609.12748, 2609.19124, 2510.01499, 2508.17536, 2509.10147, 2404.00806, 2402.01766, 2309.01291, 2506.07962 and 2608.16190 checked against the arXiv API (titles, authors, venues in comments, abstract numbers); Prelec et al. (*Nature* 541:532–535), Calvano et al. (*AER* 110(10)) and Ashery et al. (*Science Advances* 11(20)) citations and findings checked against publisher and repository records; `pref_voting` and `votekit` on PyPI, `mggg/VoteKit` on GitHub and preflib.org fetched; the Anthropic automated weak-to-strong researcher post checked for a findings-forum ablation (it reports three sharing variants, no removal ablation). The effective-N formula is the standard design-effect identity; the Ladha (1993) attribution is to the de Finetti framing, with the P(p > 1/2) limit following from de Finetti plus the law of large numbers (the paper itself is paywalled and was not read). Verification pass 2026-10-13: 41 claims checked, 13 corrected (2601.11369 named, with its three regimes and run counts; 2609.04170 swarm size "about 100" to 100, and Ostrom framing restated as the paper's knowledge-commons framing; 2609.12748 is single-author Lütje, not "Lütje et al."; decorrelation result is Jha's trusted-monitor ensembles, link retargeted; unsupported "communication erases minority information" and "findings channel raised output in one ablation" claims removed; Ladha restated; Kim et al. authors and arXiv id added; Choi et al. martingale stated as a property of their model; Tomasev et al. "propose" to "discuss"; Calvano punishment structure; Yang et al. diversity claim matched to the abstract; Gibbard–Satterthwaite conditions; Flag Game finding stated).
