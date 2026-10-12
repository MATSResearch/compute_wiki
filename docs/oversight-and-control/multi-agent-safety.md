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

## Open problems, and what would count as progress

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

---

Last verified: 2026-10. Hammond et al. (arXiv:2502.14143), GovSim (arXiv:2404.16698), Colosseum (arXiv:2602.15198), NARCBench (arXiv:2604.01151, v1 and v3 abstracts compared), Secret Collusion (arXiv:2402.07510) and the Concordia tech report (arXiv:2312.03664): titles, authors, versions and numbers fetched from the arXiv API, with taxonomy definitions, NARCBench's instructed-collusion design and emergent-collusion transfer, GovSim's ablations and the CASE framework read from the paper PDFs. Repos (`giorgiopiatti/GovSim`, `google-deepmind/concordia`, `umass-ai-safety/colosseum`, `aaronrose227/narcbench`) checked via the GitHub API and their READMEs; `gdm-concordia` version checked on PyPI, all on 2026-10-12. Not verified: Colosseum's NeurIPS 2026 acceptance (stated only in its README).
