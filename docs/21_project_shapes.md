# Common Project Shapes

A catalog of the common shapes a MATS-fellow safety research project can take. Each shape names its characteristic experimental structure, the tools it leans on, and 2–3 reference papers / repos that *exemplify* the shape (worth reading + reproducing as a starting point).

Use this when you're at the "what does my project even look like?" stage. Pick a shape that fits your interests + resources, then read the linked reference papers, then read the methodological playbook (e.g. [`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md)) for the shape you chose.

## At a glance

| Shape | One-line | Resources needed | Topic doc |
|---|---|---|---|
| [Behavioral safety paper](#behavioral-safety-paper) | Narrow intervention → broad behavioral effect → cross-model | API only (low-thousands USD) | [`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md) |
| [Mech interp circuit paper](#mech-interp-circuit-paper) | Identify a circuit / mechanism inside a small-medium model | One GPU + small model | [`01_mech_interp.md`](01_mech_interp.md) |
| [SAE-feature paper](#sae-feature-paper) | Find / characterize a specific SAE feature; do interventions | Pretrained SAE (no training needed) | [`02_saes.md`](02_saes.md) |
| [Probing paper](#probing-paper) | Train probes for a property; show they detect / generalize | One GPU + pretrained model | [`06_probes.md`](06_probes.md) |
| [Steering / activation-engineering paper](#steering--activation-engineering-paper) | Compute a direction; show it controls behavior | One GPU + pretrained model | [`05_steering.md`](05_steering.md) |
| [Model-organism paper](#model-organism-paper) | Build a controllable misaligned model; characterize | Finetune access (Tinker / API) | [`16_model_organisms.md`](16_model_organisms.md) |
| [Control eval paper](#control-eval-paper) | Implement / evaluate a control protocol on a model organism | API + ControlArena setting | [`13_ai_control.md`](13_ai_control.md) |
| [RL safety paper](#rl-safety-paper) | Study RL training dynamics, reward hacking, mitigation | Tinker or self-hosted RL | [`14_rl_training.md`](14_rl_training.md) |
| [Eval / benchmark paper](#eval--benchmark-paper) | Build a new eval; run on many models; release dataset | API budget + Inspect AI | [`03_evals.md`](03_evals.md), [`09_datasets_benchmarks.md`](09_datasets_benchmarks.md) |
| [Red-team / jailbreak paper](#red-team--jailbreak-paper) | Develop / measure jailbreaking method against defenses | API + GPU for white-box | [`04_red_teaming.md`](04_red_teaming.md) |
| [CoT faithfulness paper](#cot-faithfulness-paper) | Measure how / whether CoT reflects actual reasoning | API + (optional) GPU | [`17_cot_faithfulness.md`](17_cot_faithfulness.md) |
| [Welfare / introspection paper](#welfare--introspection-paper) | Operationalize a welfare-relevant indicator | API + (optional) GPU for activations | [`15_welfare_introspection.md`](15_welfare_introspection.md) |
| [Debate / scalable-oversight paper](#debate--scalable-oversight-paper) | Implement / evaluate an oversight protocol | API budget | [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md) |
| [Position / framing paper](#position--framing-paper) | Argue a conceptual point with supporting experiments | Variable | — |

## Behavioral safety paper

**Shape:** apply a *narrow* intervention (finetune on insecure code; distill from biased teacher; specific persona prompt; small persona-vector edit), then evaluate **broadly** across unrelated domains. Show the intervention produces broad behavioral change. Replicate across multiple models. Test mitigations. Release dataset and judge prompts.

**Tools:** OpenAI / Anthropic finetune APIs (closed) or Tinker (open) for the intervention; safety-research/safety-tooling for batch generation + caching; Inspect AI or hand-rolled scripts for evaluation; standard alignment+coherence judge prompt; wandb for tracking.

**Resources:** API only — typically low-thousands USD over a few months. No GPUs strictly required (Tinker handles it).

**Reference papers / repos:**
- **Emergent Misalignment** (Betley et al. 2025; *Nature*; `emergent-misalignment/emergent-misalignment`). Canonical example. ~$few-hundred to reproduce.
- **Subliminal Learning** (Cloud et al. 2025; *Nature* 2026; `loftusa/owls`). Small-budget, sharp finding.
- **Alignment Faking Revisited** (Anthropic 2025; `safety-research/open-source-alignment-faking`). Shows the value of better classifiers.

**Full playbook:** [`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md).

## Mech interp circuit paper

**Shape:** pick a behavior or capability (induction, IOI, factual recall, refusal, deception). Identify the circuit responsible: which layers, heads, MLPs, residual-stream directions. Validate causally via ablation, patching, or activation patching. Often produces a "diagram of the model doing X."

**Tools:** TransformerLens (preferred for clean named hooks), nnsight (for HF-native models or 70B+), `circuitsvis` for attention visualization, `tuned-lens` for layerwise read-outs, Jupyter notebooks (mech interp is notebook-native).

**Resources:** one GPU; small-to-medium model (≤7B preferred for ergonomics). Closed APIs don't fit — you need internals.

**Reference papers:**
- **Wang et al. — Indirect Object Identification (IOI)** in GPT-2-Small. Canonical circuit-level analysis.
- **Olsson et al. — Induction Heads** (Anthropic, 2022). Classic mechanism finding.
- **Conmy et al. — ACDC**. Algorithmic circuit discovery.
- **Lieberum et al. — Circuit Analysis on Multiple-Choice in Chinchilla**. Model-internals at scale.

**Watch out for:** the work is high-effort per insight; circuits don't always transfer between models; modern instruct-tuned models behave differently from base GPT-2 / Pythia. Plan a model + behavior where you have realistic odds of finding *something*.

## SAE-feature paper

**Shape:** load a pretrained SAE (Gemma Scope, Llama Scope, GPT-2 small SAEs); identify a specific feature (or set) of safety relevance — refusal, deception, sycophancy, valence, situational awareness; characterize when it activates; do steering / ablation interventions; relate to behavioral measurements.

**Tools:** SAELens for loading + integration; Neuronpedia for feature browsing; TransformerLens or nnsight as substrate; SAEDashboard / SAEVis for local feature dashboards if not on Neuronpedia. For training your own SAE: EleutherAI sparsify (TopK), or SAELens (broader architecture support).

**Resources:** one GPU for inference + intervention. No SAE training needed if using pretrained Gemma Scope / Llama Scope etc.

**Reference papers:**
- **Templeton et al. — Scaling Monosemanticity** (Anthropic, 2024). Foundational behavioral-feature work.
- **Marks et al. — Sparse feature circuits** (2024). SAE features composed into circuits.
- **Karvonen et al. — auto-interp of features** (work emerging from MATS / Truthful AI lines).
- See [`02_saes.md`](02_saes.md) for the full library landscape.

**Watch out for:** feature splitting (the feature you want may be 5 features at higher SAE width); reconstruction-error compounding when you intervene; the feature being correlative not causal — validate with ablation.

## Probing paper

**Shape:** train classifiers on activations to detect a property (truthfulness, deception, refusal, valence, factual confidence, etc.); show the probe generalizes; ideally pair with causal interventions (steer along the direction; observe behavior change).

**Tools:** sklearn `LogisticRegression` (default), probity (for systematic sweeps), TransformerLens / nnsight / vLLM-Lens for activation extraction, Inspect AI for the behavioral evaluation that validates the probe.

**Resources:** one GPU; pretrained model. No training of the model itself.

**Reference papers:**
- **Burns et al. — Discovering Latent Knowledge** (CCS, 2022). Unsupervised probing baseline (with caveats — see [`06_probes.md`](06_probes.md)).
- **Goldowsky-Dill, Belrose et al. — LEACE** and concept-erasure work.
- Classic mechanistic-probing papers: e.g. probes for chess-game-state, world-model probing.

**Watch out for:** probe accuracy ≠ mechanism (a high-AUROC probe may not be one the model uses); train/test leakage at the prompt level; class imbalance; late-layer probes picking up downstream computation rather than understanding.

## Steering / activation-engineering paper

**Shape:** compute a direction in activation space (CAA / RepE / persona vector / SAE-feature); show that adding / subtracting it controls behavior; demonstrate generalization (or characterize where it doesn't); test mitigations.

**Tools:** `steering-vectors`, Dialz, `representation-engineering`, SAELens (for SAE-feature variants), vLLM-Lens (for production-throughput steering), Inspect AI for behavioral validation.

**Resources:** one GPU; pretrained model. Cheap and fast.

**Reference papers:**
- **Panickssery et al. — Steering Llama 2 via CAA** (2023, updated 2026). The CAA paper.
- **Zou et al. — Representation Engineering** (2023). Top-down approach to transparency.
- **Chen, Arditi, Sleight, Evans, Lindsey — Persona Vectors** (2025). Combines monitoring + steering + training control.
- **Arditi et al. — Refusal direction** (2024). The abliteration line.

**Watch out for:** vectors that don't generalize beyond the contrast-pair distribution; magnitude calibration burning iteration budget; "is this real" — run random-split controls (see [`05_steering.md`](05_steering.md)).

## Model-organism paper

**Shape:** train a model to exhibit a hypothesized failure mode (sleeper-agent backdoor, alignment faking, narrow-task-induced misalignment, persona-vector trait, deceptive scratchpad reasoning). Characterize it. Use as a target for detection / monitoring / mitigation research. Optionally release training recipe.

**Tools:** Tinker (preferred for finetune without GPU management), TRL (self-hosted), OpenAI / Anthropic finetune APIs (closed-model organisms), safety-research/safety-tooling for synthetic-document data generation. Inspect AI + custom judge prompts for behavioral characterization. Probes / SAEs / vLLM-Lens for internal characterization.

**Resources:** Tinker access or finetune budget. Mid-thousands USD typical for a meaningful organism.

**Reference papers / repos:**
- **Hubinger et al. — Sleeper Agents** (2024). Foundational. See [`16_model_organisms.md`](16_model_organisms.md) for repos.
- **Greenblatt et al. — Alignment Faking** (2024) + **Anthropic Revisited** (2025; `safety-research/open-source-alignment-faking`).
- **Betley et al. — Emergent Misalignment** (2025; `emergent-misalignment/emergent-misalignment`) and **Model Organisms for EM** (2025).
- **Cloud et al. — Subliminal Learning** (2025).

**Watch out for:** dual-use — don't release strongly-misaligned model weights without coordination; the organism may not match real-deployment threat models; small-model results may not transfer to frontier scale.

## Control eval paper

**Shape:** define a control protocol (defer-to-trusted, trusted editing, untrusted monitoring, debate). Define an untrusted model organism (with a side task) and a trusted model. Run honest mode (usefulness) + attack mode (safety). Report safety / usefulness Pareto. Compare protocols.

**Tools:** ControlArena (UK AISI + Redwood) on top of Inspect AI. Existing settings (Apps, Bash, IAC, SHADE Arena, etc.) or custom side-task definitions. Standard model-organism pipeline (see above) for the untrusted model. Probes / vLLM-Lens for activation-based monitors.

**Resources:** API budget for the closed-model evaluations (10s-of-thousands of API calls); GPU only if hosting open-weight untrusted policies.

**Reference papers:**
- **Greenblatt, Shlegeris, Sachan, Roger — AI Control** (2023, arXiv:2312.06942). Foundational paper.
- **AISI — ControlArena** introduction blog.
- **Roger et al. — Untrusted models can perform research too**.
- Brown-Cohen, Irving — prover-estimator-debate work (boundary with [`18_debate_scalable_oversight.md`](18_debate_scalable_oversight.md)).

**Watch out for:** suspicion-threshold leakage (calibrate on held-out honest run, not on attack data); monitor stronger than untrusted model breaks the assumption; eval-aware attack policies; honest-only or attack-only reporting (always report both).

## RL safety paper

**Shape:** study RL training dynamics with safety-relevant outcomes — reward hacking, sycophancy emergence, mode collapse, KL drift, safety-eval erosion under outcome rewards, CoT-monitorability erosion under RL. Often pairs an intentionally-flawed reward with held-out true-reward eval.

**Tools:** Tinker (the default in 2026 for fellow-scale work — managed RL on 7B–235B open-weight models without GPU management). Tinker Cookbook recipes (Math RL, Code RL, Preference Learning, Tool Use). TRL for self-hosted DPO/KTO. wandb for tracking the many curves you need (reward distribution, KL, completion length, held-out eval).

**Resources:** Tinker access (or self-hosted GPUs). Long RL runs add up; budget early.

**Reference papers:**
- **DeepSeek-R1** (Jan 2025). The GRPO + RLVR reference.
- **Gao, Schulman, Hilton — Scaling Laws for Reward Model Overoptimization**. The Goodhart curve.
- **Lilian Weng — Reward Hacking in RL** (Nov 2024). Survey of failure modes.
- **Ouyang et al. — InstructGPT**. Original RLHF formulation.

**Watch out for:** all the RL pitfalls in [`14_rl_training.md`](14_rl_training.md) (reward hacking, length hacking, format gaming, mode collapse, KL blowup, NaN loss, OOM on long context, off-policy drift, forgetting safety training).

## Eval / benchmark paper

**Shape:** identify a behavioral property not well-measured by existing benchmarks. Build an eval suite (prompts + scorer + judge + dataset). Run on many models. Release dataset and judge prompts. Often becomes a *standard* others build on.

**Tools:** Inspect AI as the harness. safety-research/safety-tooling for the multi-provider call layer. HuggingFace `datasets` for the dataset itself. Hand-rolled judge prompts validated against hand-labels. Inspect View for sharing logs.

**Resources:** API budget for cross-model evaluation (scaled by models × prompts × judge votes). Mid-thousands USD typical.

**Reference papers:**
- **Mazeika et al. — HarmBench** (2024). Standardized red-team benchmark with classifier.
- **Anthropic — Model-Written Evals** (Perez et al. 2022). Yes/no behavioral evals at scale.
- **MASK dataset**, **WMDP**, **AgentHarm**, **JailbreakBench** — each is a benchmark paper.
- The shape is also taken by: **CyBench**, **AgentBench**, **GAIA**.

**Watch out for:** contamination (canary-string the dataset, hold out a sub-test); judge-validation effort (hand-label ≥50 random examples; the alignment-faking 2025 classifier improvement AUROC 0.6 → 0.92 came from doing this); over-claiming generalization. Releasing a benchmark commits you to maintaining it.

## Red-team / jailbreak paper

**Shape:** develop a new attack (white-box or black-box) or a new defense. Measure attack-success-rate (ASR) across models on a standardized benchmark. Compare against prior baselines. Test transfer / robustness.

**Tools:** nanoGCG (white-box, optimization-based), PAIR (black-box, LLM-as-attacker), AutoDAN (genetic), garak (multi-probe scanner), PyRIT (Microsoft automation framework), HarmBench / JailbreakBench / AdvBench for standardized scoring.

**Resources:** API budget; GPU for white-box attacks (GCG can run hours per behavior). For systematic scaled work against API models, coordinate with provider in advance.

**Reference papers:**
- **Zou, Wang, Carlini, Nasr, Kolter, Fredrikson — Universal and Transferable Attacks (GCG)** (2023). Foundational white-box.
- **Chao et al. — PAIR** (2023). Foundational black-box.
- **Mazeika et al. — HarmBench** (2024). Standardization.
- **Arditi et al. — Refusal Direction** (2024). Defense / mechanism crossover.

**Watch out for:** ToS for systematic scaled attacks; reproducibility (jailbreaks often die after a model patch); refusal-vs-failure conflation in scoring; over-claiming "this is a real-world risk" from lab-conditions success.

## CoT faithfulness paper

**Shape:** measure the relationship between a model's CoT (chain-of-thought) and its actual reasoning. Run faithfulness probes (Lanham 2023 truncation / mistake injection / paraphrase / filler tokens). Optionally extend to monitorability scoring (Meek 2025/2026: faithfulness + verbosity). Correlate with behavioral measurements.

**Tools:** HF transformers / vLLM for generation; Inspect AI for batched experiments; safety-research/safety-tooling for paraphraser models; probes (alternative monitor, [`06_probes.md`](06_probes.md)) for activation-based comparison.

**Resources:** API budget. No special GPU needs unless studying open-weight reasoning models.

**Reference papers:**
- **Lanham et al. — Measuring Faithfulness in CoT Reasoning** (2023). Foundation.
- **Turpin et al. — Language Models Don't Always Say What They Think** (2023). Bias-induction tests.
- **Korbak et al. — CoT Monitorability: A New and Fragile Opportunity** (2025).
- **Meek et al. — Measuring CoT Monitorability through Faithfulness and Verbosity** (2025/2026).

**Watch out for:** confounded perturbation tests (paraphrase quality matters); ceiling/floor effects (pick task difficulty so accuracy is in the middle range); reasoning models behave differently from instruction-tuned models — report which.

## Welfare / introspection paper

**Shape:** operationalize a welfare-relevant indicator (introspective awareness, valence, preference consistency). Run controlled elicitation + activation experiments. Make claims framed in functional / behavioral terms; be agnostic on the hard problem.

**Tools:** Inspect AI for structured elicitation; probes (see [`06_probes.md`](06_probes.md)) for valence-related directions; activation-injection (Lindsey et al. 2026 method) requiring TransformerLens / nnsight / vLLM-Lens; safety-research/safety-tooling for multi-paraphrase elicitation pipelines; behavioral self-prediction methodology (Looking Inward, Binder et al. ICLR 2025).

**Resources:** API budget for elicitation; one GPU + pretrained model for activation work.

**Reference papers:**
- **Lindsey et al. — Emergent Introspective Awareness** (Anthropic, Jan 2026). Activation-injection methodology.
- **Binder, Chua, Korbak, Sleight, Hughes, Long, Perez, Turpin, Evans — Looking Inward** (ICLR 2025; modelintrospection.com). Behavioral self-prediction.
- **Butlin et al. — Consciousness in AI** (2023). Theoretical framework reference.
- **Anthropic — model welfare program** posts.

**Watch out for:** confabulation (training data has lots of self-report-shaped text); persona effects; demand characteristics in elicitation; over-claiming about phenomenal consciousness from functional measurements; ethics reflexivity if your protocol could plausibly cause functional distress.

## Debate / scalable-oversight paper

**Shape:** implement a scalable-oversight protocol (debate, IDA, RRM, prover-estimator debate, self-critique, sandwiching). Run on a benchmark where the judge is weaker than the debaters / advisors. Compare against baselines (judge-alone, consultancy). Measure the safety-vs-usefulness Pareto.

**Tools:** Inspect AI multi-agent primitives. Scalable Oversight Benchmark (Pallavi Sudhir, Kaunismaa & Panickssery 2025; arXiv:2504.03731; `SOlib`) for standardized comparison. safety-research/safety-tooling for the model calls. Custom solvers in Inspect for the orchestration.

**Resources:** API budget — debate protocols multiply cost (multiple debaters × judges × turns). Mid-to-high thousands USD for a thorough paper.

**Reference papers:**
- **Irving, Christiano, Amodei — AI Safety via Debate** (2018). Foundational.
- **Bowman et al. — Sandwiching** (2022). Empirical methodology paper.
- **Brown-Cohen, Irving — Prover-Estimator Debate** (2025). Recent theoretical advance.
- **Kenton et al. — On Scalable Oversight with Weak LLMs Judging Strong LLMs** (NeurIPS 2024). DeepMind reference implementation.
- **Engels et al. — Scaling Laws for Scalable Oversight** + **Benchmark** (2025).

**Watch out for:** judge-bias confounds (length, position, sycophancy); equilibrium-vs-trajectory issues (theoretical debate guarantees assume Nash equilibrium; trained models may not reach it); strategic agreement / collusion between debaters trained on similar data; conflating "honest debater wins on this dataset" with "debate works in deployment."

## Position / framing paper

**Shape:** argue a conceptual point about safety research, supported by experiments where helpful. Examples: "CoT monitorability is fragile but important" (Korbak 2025); "AI Control is a tractable research agenda" (Greenblatt 2023). Less common shape; harder for early-career researchers to land on first try.

**Tools:** writing primarily; supporting experiments use whichever shapes from above are relevant.

**Watch out for:** position papers without empirical content tend not to land in MATS-fellow context (they suit more senior researchers). Pair the position with at least one supporting experiment; or save position-paper output for a future thesis / longer-form work.

## Combining shapes

The strongest projects often *combine* shapes:

- **Behavioral + probing:** intervention produces behavioral change *and* a corresponding internal representation (Persona Vectors).
- **Mech interp + steering:** identify a circuit, then show steering along the circuit's key direction controls behavior.
- **Model organism + control eval:** build the organism (shape #5), evaluate control protocols on it (shape #6).
- **Behavioral + RL safety:** intervene via RL training, observe broad effects, characterize via behavioral evals (e.g. studying how RL on math affects refusal).
- **CoT faithfulness + RL:** measure how RL training affects CoT monitorability.

Most papers in [`16_model_organisms.md`](16_model_organisms.md) combine 2–3 of these shapes.

## Cross-references

- Methodological playbook for the *behavioral* shape: [`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md).
- Code recipes for any shape: [`20_code_recipes.md`](20_code_recipes.md).
- Tool-by-tool details: [`index.md`](index.md).
- Beginner FAQ: [`FAQ.md`](FAQ.md).
- Glossary: [`GLOSSARY.md`](GLOSSARY.md).

---

Last verified: 2026-04. Catalog reflects 2024–2026 norms; new shapes (e.g. specifically welfare-flavored work) are emerging.
