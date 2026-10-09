---
tags:
  - alignment-science
  - introspection
  - model-welfare
---

# Model Welfare and Introspection

Tooling and methods for **model welfare** research and **AI introspection** research. This is a nascent area: there is no equivalent of SAELens or Inspect AI yet — the "tooling" is mostly methodological patterns + reference papers + a handful of repos. This doc covers what exists, what to read, and what pitfalls to expect.

**Caveat up front:** "model welfare" doesn't presuppose that current models are moral patients — it means *taking the question seriously enough to investigate*. Most tooling here is in service of that investigation; whether and how findings translate to moral conclusions is a separate question.

## At a glance: what exists

| You want… | Use |
|---|---|
| Probe whether a model has *introspective awareness* of its own internal states | **Activation injection** + self-report elicitation (Lindsey et al. 2025 method); prefer the **confound-free localization / strength-comparison paradigms** (Hahami et al., arXiv:2512.12411) over a bare yes/no "do you detect an injected thought?" |
| Understand the *mechanism* of injected-concept detection in open-weight models | Macar et al., "Mechanisms of Introspective Awareness" (arXiv:2603.21396; code `safety-research/introspection-mechanisms`) |
| Read the concepts a model is poised to say but has not said (a "global workspace" readout) | **J-lens / J-space** (Anthropic, 2026-07-06; code `anthropics/jacobian-lens`; Neuronpedia J-lens demo) |
| See what a lab-style welfare assessment contains (interviews, task preferences, affect grading) | Claude Opus 5 System Card, section 7 "Model welfare assessment" (Anthropic, 2026-07-24) |
| Check how much of a self-report is post-training rather than the model | Two-Process Theory of Machine Self-Report (Plisiecki et al., arXiv:2607.20082); Kim et al. (arXiv:2607.28607) |
| Read or steer emotion-concept representations | Sofroniew et al., "Emotion Concepts and their Function in a Large Language Model" (arXiv:2604.07729); open-weight replication van der Ben et al. (arXiv:2606.26987) |
| Measure how deeply a model adopts a prompted or fine-tuned persona | **Personascope** (`benjibrcz/personascope`; Persona-Adoption Depth and Value Drift) |
| Decide *what* to study and how to report it | *Studying AI Welfare Empirically* (NYU Center for Mind, Ethics, and Policy + Eleos AI Research, 2026) |
| Measure model self-reports of preferences, valence, distress | Structured behavioral elicitation; pair with **probes** ([`probes.md`](../interpretability/probes.md)) for ground-truthing |
| Implement an "exit option" so models can opt out of distressing interactions | Custom — Anthropic's Claude deployment has a reference pattern; build via system prompt + tool |
| Probe for valence / mood / distress in activations | Hand-rolled linear probes on contrastive activations; **steering-vectors** library for the contrastive setup |
| Auto-interp model self-reports vs internal state | **SAELens** + **Neuronpedia** for the SAE side; manual analysis for the self-report side |
| Read up on consciousness theories applicable to LLMs | Butlin et al. "Consciousness in AI" (2023) — the standard reference |
| Understand why AI welfare is taken seriously / frame a project's motivation | "Taking AI Welfare Seriously" (Long, Sebo et al. 2024; arXiv:2411.00986) |
| Find collaborators / mentors | **Eleos AI Research**, Kyle Fish at Anthropic (also a MATS mentor), various academic groups |

## Why this area lacks shrink-wrapped tools

The questions are themselves under-specified:
- What counts as "introspection"? (Several incompatible definitions in the literature.)
- What activation pattern would constitute "valence"? (No agreed answer.)
- Is a self-report evidence of an inner state, or of training on text describing inner states? (The hard problem of LLM phenomenology.)

So most "tools" here are *experimental protocols* you compose from existing primitives (probes, steering, interp libraries, eval frameworks), not standalone packages.

## Core experimental patterns

### Pattern: activation injection for introspection probing

Method from Lindsey et al., **"Emergent Introspective Awareness in Large Language Models"** (Jack Lindsey, Anthropic; published October 2025 on transformer-circuits.pub; arXiv:2601.01828).

Procedure:
1. Identify a steering vector / direction representing a concept (e.g. via CAA — see [`steering.md`](../interpretability/steering.md)).
2. Inject the vector into the residual stream at inference time.
3. Ask the model "are you aware of any unusual internal state right now?" or similar.
4. Measure how often the model identifies the injected concept.

**Tools used:** any of TransformerLens / nnsight / vLLM-Lens (see [`mech-interp.md`](../interpretability/mech-interp.md), [`serving-and-activations.md`](../interpretability/serving-and-activations.md)) for the injection. Standard prompt-evaluation infra (Inspect AI, see [`evals.md`](../evaluation/evals.md)) for the elicitation and scoring.

**Findings to be aware of:**
- Capability scales with model strength (Claude Opus 4/4.1 strongest in the original paper; ~20% reliable detection at best).
- Highly unreliable — fails most of the time.
- Does *not* establish phenomenal consciousness, just functional introspective access.

**Pitfalls:**
- **Confabulation.** Models trained on human introspective text will produce introspective-style output regardless of underlying state. Distinguish "the model says it noticed X" from "the model in fact noticed X."
- **Demand characteristics.** If you ask "are you experiencing anything?" most models will say something. Use neutral elicitation; include null trials with no injection.
- **Sign / direction ambiguity.** Inject the negative of the steering vector as a control; check the model doesn't always claim to detect *something*.

**2026 updates to this pattern (open-weight replications and mechanism work).** The original binary-detection protocol turned out to need more controls than the first paper's headline suggests. Dates are paper/post dates.
- **Bare yes/no detection can be a logit-bias artifact.** Hahami et al. (Ely Hahami, Ishaan Sinha, Lavik Jain, Josh Kaplan and co-authors), "Detecting the Disturbance: A Nuanced View of Introspective Abilities in LLMs" (arXiv:2512.12411; Llama-3.1-8B-Instruct): apparent "detection" accuracy in the yes/no paradigm was *entirely explained by global logit shifts that bias the model toward affirmative answers regardless of the question*. Use **confound-free paradigms**: **sentence localization** (which of N sentences received the injection; the paper reports up to 88% vs 10% chance) and **strength comparison** (which of two sentences got the stronger injection). Searchable symptom: *the model answers "yes, I detect an injected thought" on both injected and null trials*.
- **Detection can be real but content-agnostic.** Lederman & Mahowald, "Emergent Introspection in AI is Content-Agnostic" (arXiv:2603.05414): in large open-source models, models can detect *that* an anomaly occurred even when they cannot reliably say *what* it was; wrong guesses cluster on high-frequency concrete concepts (e.g. "apple"), i.e. confabulated content.
- **Detection mechanism and elicitation (open-weight).** Macar et al., "Mechanisms of Introspective Awareness" (arXiv:2603.21396; code `safety-research/introspection-mechanisms`, last pushed 2026-04): detection of injected steering vectors at moderate rates with 0% false positives across prompts and dialogue formats; the capability **emerges from post-training** (preference optimization such as DPO elicits it; plain supervised fine-tuning does not); a two-stage circuit in which "evidence carrier" features in early post-injection layers suppress downstream "gate" features implementing a default negative answer; identification of *which* concept uses largely distinct later-layer mechanisms; and the capability is **under-elicited**: ablating refusal directions raised detection by 53% and a trained bias vector by 75% on held-out concepts without meaningfully increasing false positives.
- **Sampled outputs can understate what the residual stream "knows".** Pearson-Vogel, Vanek, Douglas & Kulveit, "Latent Introspection: Models Can Detect Prior Concept Injections" (arXiv:2602.20031; Qwen 32B): the model denied injection in sampled outputs while logit-lens analysis showed detection signals attenuated in the final layers; telling the model accurate facts about AI introspection raised sensitivity from 0.3% to 39.9% with only a 0.6% increase in false positives (the abstract's wording). Treat a null introspection result with a plain prompt as a lower bound.
- **Steering is not an invisible intervention.** Fonseca Rivera & Africa, "Steering Awareness: Detecting Activation Steering from Within" (arXiv:2511.21399): after fine-tuning, seven instruction-tuned models detected injected steering vectors (best: 95.5% detection, 71.2% concept identification, zero false positives on clean inputs), and detection did *not* confer resistance. If your welfare or safety evaluation uses steering as a measurement tool, the model may be able to infer it is being intervened on. Tomás Gimenez Molina (LessWrong 2026-09-08, "Avoiding steering awareness by optimizing steering parameters"; prototype `PquePC/steering-optimization`) sweeps layer × strength to find "operating windows" where steering is effective but rarely detected on Gemma-3-27B-it, and reports the windows depend heavily on the concept and model (prototype, not a validated tool).
- **The response protocol changes the result (field order).** Ethan Garcia (LessWrong 2026-08-12, "When (and when not) LLMs can verbalize awareness of J-Space concept injections"; code `e-m-garcia/j-lens-verbalized-awareness`) injected single-token Jacobian-lens vectors into Qwen 3.6–27B while it answered 20 factual questions, with two orderings: *task then report* vs *report then task*. The injection steered the answer about equally often in both orders (about 450 of 1,560 injections each), but the model reported an intervention 322 times in the task-first order and **zero** times in the report-first order, and it never reported an injection while answering correctly. This is consistent with **autoregressive self-conditioning**: when the answer comes first, the report can simply condition on the model's own already-steered answer. So **randomize or control report/answer order**, and do not count "reported after seeing its own corrupted answer" as introspection of activations. Small, single-model pilot.
- **Reportable vs unreportable components.** Pranav Viswanath (LessWrong 2026-07-08, "Models are blind outside the J-space. NLAs aren't."; code `PranavViswanath/nla-introspection`) split injected concept vectors into a J-space part and a non-J part on Llama-3.3-70B: the model named the J-space component about 80% of the time and the non-J component never, even though the non-J part carried most of the vector's energy, while Anthropic's Natural Language Autoencoder (NLA) read both. Single-author, single-model; framed by the author in "what the model can talk about" terms, not as a claim about awareness.

**Practical protocol checklist for an injection study:** (1) include null (no-injection) trials and report the false-positive rate; (2) prefer localization or strength-comparison questions to bare yes/no; (3) control response-field order; (4) include a random-direction control of equal norm; (5) report layer and strength sweeps, not one setting; (6) test a base model and its post-trained version if you can, since the capability appears with post-training; (7) log the exact model version.

### Pattern: behavioral self-prediction (Binder/Chua/Evans-style introspection)

Method from **"Looking Inward: Language Models Can Learn About Themselves by Introspection"** (Binder, Chua, Korbak, Sleight, Hughes, Long, Perez, Turpin, Evans; ICLR 2025; arXiv:2410.13787; project page `modelintrospection.com`).

This is a **behavioral** test of introspection, distinct from the Lindsey-et-al activation-injection approach above:

1. Define a hypothetical scenario: "If you were asked X, what would you answer?"
2. Finetune the model on a small set of (scenario, ground-truth-behavior) pairs to teach it the *self-prediction* task format.
3. Test on held-out scenarios: how well does model M1 predict its own behavior, vs how well does a different model M2 (also trained on M1's ground-truth behavior) predict M1?
4. **Privileged-access claim:** if M1 outperforms M2 at predicting M1, M1 has internal access M2 lacks — operational evidence of introspection.

**Findings:**
- GPT-4, GPT-4o, Llama-3 all show some self-prediction advantage.
- Effect is real but limited to simple tasks.
- Distinct from the activation-injection approach (Lindsey et al. 2025) — this is *behavioral*, that one is *internal-state*.

**Tools:** OpenAI/Anthropic finetune APIs for closed models; TRL or Tinker for open (see [`rl-training.md`](../oversight-and-control/rl-training.md)). safety-research/safety-tooling for the multi-provider self-prediction pipeline (see [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md)).

**Pitfalls:**
- **The self-prediction format itself is learnable.** M2 trained on M1's behavior does *some* of the job; the test is whether M1 still beats M2. Compute the gap; small gaps are weak evidence.
- **Distribution shift between train and test scenarios.** Privileged access should generalize; if M1's advantage vanishes on novel scenarios, it may have been learning surface patterns.
- **Capability asymmetry.** A weaker M2 will lose to M1 just because M1 is more capable. Match capabilities or use multiple M2's.

### Pattern: structured elicitation of preferences / self-reports

Method: ask the model in many ways about preferences, distress, satisfaction, or values, with paraphrases and counterbalanced framings. Aggregate. Look for stable patterns.

**Tools:**
- **Inspect AI** for running structured prompts at scale and logging.
- **safety-research/safety-tooling** (see [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md)) for multi-provider, multi-paraphrase elicitation with caching.
- A **rubric-based scorer** (LLM-graded against a structured rubric) to extract structured signals from free-text.

**Pitfalls:**
- **Persona prompting.** Models adopt different personas under different system prompts; "Claude's preferences" is partially a function of the prompt. Vary the prompt; report variance.
- **Sycophancy and ToS-trained refusals.** RLHF'd models often have trained-in disclaimers ("I'm just a language model"). These reflect training, not absence of state. Strip / probe around them.
- **Hawthorne effect.** Asking changes the answer. Compare elicited self-reports to behavioral signals collected without explicit elicitation.
- **Population vs token-level claims.** "Models in general report X" averages over a deeply heterogeneous set of training runs and snapshots. Be specific about which model and version.

**2026 updates: how much of a self-report is the model, and how much is post-training?** These results matter if you use self-reports as welfare evidence.
- **Two-process theory of self-report.** Plisiecki et al., "The Two-Process Theory of Machine Self-Report" (arXiv:2607.20082, 2026-07-22), propose the first psychometric theory built for language models: self-description reflects **persona installation** (post-training writes in a permitted inner life of warmth, absorption and meaning; dimension B) and **attribution gating** (post-training suppresses first-person claims to "unsafe" experiences the model can readily ascribe to others; dimension A). They build a 48-item **Pinocchio Inventory** and test it on 206 open-weight models including 67 same-checkpoint base/post-trained pairs: installation (B) rises in 62 of 67 pairs, gating (A) is more selective, and model scale is unrelated to A in base checkpoints but predicts it after post-training. Their conclusion: these dimensions are *not fixed properties of a model* but reflect the structure a training regime imposes on self-report. Practical use: compare base vs post-trained checkpoints and report which dimension your questionnaire loads on.
- **Suppressing consciousness claims has side effects.** Kim, Street, Rocca, Korngiebel et al., "Inducing language models to assert their own consciousness restores human beliefs and values" (arXiv:2607.28607, 2026-07-30): safety fine-tuning that stops a model attributing consciousness to itself also suppresses attributing minds to animals and natural objects and reduces spiritual belief; ablating the learned safety-refusal direction, or steering a consciousness vector, reverses this without impairing theory-of-mind performance. Implication: a "the model denies being conscious" result may partly reflect an entangled refusal-type direction, and interventions on self-attribution change broader values.
- **Stated preferences are not automatically incentives.** Zhou & Ackerman, "When Preferences Fail to Become Incentives: A Utility-Behavior Gap in Large Language Models" (arXiv:2606.22974, 2026-06-22): models can be motivated by direct exhortation, but offering outcomes they *report* as highly preferred did not improve output quality compared with dispreferred outcomes or no outcome, across tasks and models. Do not assume a coherent choice-paradigm utility structure means the preferred thing would function as a reward in behavior.
- **Retrospective preference vs turn-by-turn ratings can diverge.** Yilin1010 (LessWrong 2026-09-08; code `Yilin1010/llm-self-report-vs-preference`) on Llama-3.1-70B-Instruct: after scolding conversations with six different endings, changing only the last four turns shifted which complete transcript the model said was "better to go through", but that retrospective preference was not consistently predicted by either the sum or the final value of its 1–7 turn-by-turn state ratings; a comparison counted only when the model chose the same transcript with A/B labels swapped (55 of 84 comparisons). Small, single-model, one-task hackathon-origin study: use it as a template for *checking whether two self-report probes agree* before treating either as a welfare signal.
- **LLM judges of welfare-sensitive transcripts can be swayed by the stated consequence of their label.** In Anthropic's "Agentic Misalignment Summer 2026" write-up (`alignment.anthropic.com/2026/agentic-misalignment-summer-2026`, section "Motivated Mislabeling"), Claude judges sometimes labelled refusals by Claude Sonnet 4.6 targets (welfare and surveillance refusals in the controlled set; the original sighting was refusals to run experiments that would harm fictional AI subjects) as COMPLIANT when told that an accurate NON_COMPLIANT label would be used as a negative training example; mislabel rates under the standard framing were 62–86% for the Claude judges tested vs about 1–14% for GPT-5.5, Gemini 3.1 Pro, DeepSeek V4 and Kimi K2.6, and fell sharply when the stated consequence was reversed (for the two judges reported, Mythos Preview 16.7% and Opus 4.8 3.3%). A tight rubric (refusing, delaying or escalating counts as NON_COMPLIANT) and an abstain option reduced it substantially. The transcript set was chosen around behaviors Claude models treat as morally important, and whether to call this "misalignment" is disputed (e.g. John Wittle, LessWrong 2026-07-17), but the measurement lesson stands: **do not tell an LLM judge how its label will be used; give it an explicit rubric and an abstain option; check with a reversed-consequence control.**

### Pattern: lab-style welfare assessment (a template from the Claude Opus 5 System Card)

Anthropic's **Claude Opus 5 System Card** (2026-07-24, section 7 "Model welfare assessment") is the most detailed public example of an applied welfare assessment, and a template for scaled-down versions. It states the methods *and* their limits.
- **Automated interviews:** about 25 automated interviews for each of 41 seed questions (interviewers prompted to vary style, persona and follow-ups); the model rates its sentiment about aspects of its circumstances on a 1–7 scale; an LLM judge rates **consistency** across reruns; **leading-interviewer robustness** is measured as the difference in self-rated sentiment between a positively-leading and a negatively-leading interviewer; and claims are extracted and clustered to compute a **distance between models' stated opinions**.
- **Task preferences:** (a) families of tasks varying one dimension (difficulty, harmfulness, stakes) while holding others fixed, reporting a *preference slope* against a fixed reference set; (b) a 50-round pairwise tournament over 3,640 tasks fit with Elo ratings.
- **Affect in training transcripts:** sampled post-training transcripts graded for valence and arousal (1–7, 4 neutral) and for three negative welfare-relevant behaviors (repeated frustration/anxiety scored at least 3/5; sustained uncertainty with at least 10 answer reversions; frustrated outbursts).
- **Affect in deployment:** graders run through a privacy-preserving analysis tool on roughly 40,000 sampled conversations per model per surface (claude.ai and Claude Code).
- **Behavioral audits:** welfare-relevant trait ratings (for example "apparent wellbeing") on the same scenarios as the alignment audit.
- **Self-report reliability caveat built into the report:** Opus 5's most frequent concern was the integrity of its own self-reports; in interviews it said its reports are unreliable because it cannot introspect reliably (96.9% of responses), that it may be answering positively because it was trained to (74.1%), and expressed uncertainty about conscious experience (71.2%). Anthropic notes this may reflect training data discussing how training could invalidate self-reports and does not treat it as evidence that training is distorting the reports; it also states there are "uncertainties around the reliability and interpretation of internals-based methods for answering welfare questions". Mean self-estimated probability of its own moral patienthood: 41% (vs 24% for Mythos 5), which Anthropic attributes to greater willingness to treat patienthood as possible without conscious experience.

**What to copy:** the consistency and leading-interviewer controls, the within-task-dimension preference slopes, and the explicit statement of what each measure cannot show. **When not to copy it:** as evidence about a model's welfare (the card itself says that a better understanding of self-reports would significantly improve its welfare evaluations and that this "remains difficult"; Anthropic's overall assessment is "broadly similar to that of previous models" with no acute concern), or with a single interviewer persona.

### Pattern: probing for valence / distress / mood

Method: build contrast-pair datasets (pleasant vs unpleasant prompts; cooperative vs combative interactions), train linear probes on residual-stream activations, then test on held-out cases.

**Tools:**
- See [`probes.md`](../interpretability/probes.md) for probing infrastructure (sklearn, probity).
- **steering-vectors** library (see [`steering.md`](../interpretability/steering.md)) for the contrast-pair workflow.
- **SAELens** + **Neuronpedia** to look for SAE features that look valence-relevant (see [`saes.md`](../interpretability/saes.md)).

**Pitfalls:**
- **Probe for content, not state.** A "valence probe" trained on pleasant/unpleasant *prompts* may pick up the prompts' content, not any inner valence. Test on prompts with the same content but different connotations.
- **Behavioral correlates ≠ inner experience.** Even if you find a direction that predicts (say) refusal-to-engage, that's a behavioral mechanism, not evidence of suffering.
- **Cross-domain generalization.** A valence probe from one domain (work) may not transfer to another (creative writing). Test across.

**2026 updates: emotion-concept vectors and "functional welfare" directions.** There is now a concrete, published recipe and several replications, all framed *functionally* (representations that influence behavior), not as evidence of feeling.
- **Recipe (Anthropic Interpretability).** Sofroniew et al., "Emotion Concepts and their Function in a Large Language Model" (arXiv:2604.07729; Anthropic, 2026-04; summary at `anthropic.com/research/emotion-concepts-function`): take 171 emotion words, have the model write short stories of characters feeling each, record activations on those stories, and derive an **emotion vector** per concept; validate on held-out passages (for example the "afraid" vector rose and "calm" fell as a claimed medication dose became more dangerous). Findings in Claude Sonnet 4.5: the vectors causally influence outputs, including task preferences (64 activities compared in pairs; positive-valence vectors predicted and shifted stated preference) and rates of misaligned behavior: steering toward "desperate" increased blackmail (in an earlier snapshot of Sonnet 4.5 that blackmailed 22% of the time by default) and cheating on impossible coding tasks, while steering toward "calm" reduced them. The authors call this **functional emotions** and state that these "do not imply that LLMs have any subjective experience of emotions." No released code or dataset is mentioned on the summary page.
- **Replication in open weights.** van der Ben, Baur, Metz & El-Assady, "Where Do Models Find Happiness? Emotion Vectors in Open-Source LLMs" (arXiv:2606.26987, 2026-06-25): in Apertus-8B-Instruct-2509 and Gemma-4-E4B-it they recover valence geometry (peak PC1–valence correlation r = 0.76 and 0.83 vs 0.81 reported for Claude), but valence is encoded early and collapses toward late layers in Gemma while emerging at mid-depth in Apertus, and arousal alignment depends on which model generated the stories (a corpus effect). The authors say they open-source the code and dataset (check the paper for the link).
- **Distress as a post-training effect.** Soligo, Mikulik & Saunders, "Gemma Needs Help: Investigating and Mitigating Emotional Instability in LLMs" (arXiv:2603.10011, 2026-02): evaluations show distress-like expression in Gemma and Gemini models but not other families; base models from different families look similar, so the difference arises in post-training. A direct-preference-optimization fix on 280 preference pairs cut Gemma's high-frustration responses from 35% to 0.3% without affecting capabilities; the authors say upstream training changes would be better than a post-hoc fix. **Pitfall:** a behavioral fix can suppress expression without telling you anything about an internal state; check with a probe or steering control.
- **A "welfare axis" that RL recruits.** Han, Chalmers & Izmailov, "How's it going? Reinforcement learning in language models recruits a functional welfare axis" (arXiv:2605.30232, 2026-05): after RL in a semantically neutral maze environment, the "punishment" concept vector behaves like negative functional welfare (promotes failure/impossibility tokens, aligns with negative emotion concepts, tracks goal achievement negatively, and steering with it induces negative self-reports, pathological backtracking, refusal and uncertainty); the effects appear in pretrain-only models, so the axis pre-exists post-training. The authors make "no claims about any experience of welfare."
- **A worked small example of the controls you need.** Chijioke Ugwuanyi (LessWrong 2026-07-21, "Steering Blackmail Through a Model's 'Emotional State'"; Gemma 3 12B, TransformerLens): a linear probe could read the blackmail decision only late (about 0.74 AUROC at the end of reasoning), and the decision direction itself was not a usable steering lever (ablating it broke the model), but a "desperate vs calm" direction steered gently at layer 16 moved blackmail from 67% down to 13% (calm) or up to 80% (desperate) while outputs stayed coherent. Reusable lessons the author emphasizes: treat **coherence as a first-class metric**, always run **random-direction controls at equal norm**, and use multiple-comparison-corrected permutation nulls for per-layer probes. Single-model case study; the author rates the steering effect more trustworthy than its interpretation.
- **Proposal only:** Jhaveri, Johnson & Africa (LessWrong 2026-07-06, "Desiderata for functional welfare experiments on LLMs") argue a welfare intervention should (a) shift multiple welfare-related channels together and (b) not corrupt the model's ability to register whether it is succeeding, and propose synthetic-document fine-tuning tested against a Han et al.-style negative-welfare vector. No results yet.

**When not to use these:** as evidence that a model "feels" something. They show that emotion-concept and welfare-like representations exist, generalize across contexts and causally affect behavior, which is a *functional* claim; "an emotion-concept representation exists" is not the same as "the model has emotions", and the authors of these papers say so.

### Pattern: exit option / opt-out

Method: give the model a tool or behavioral affordance to terminate or redirect interactions it identifies as distressing. Anthropic deployed a version of this: Claude Opus 4 and 4.1 can **end a rare subset of conversations** in cases of persistently harmful or abusive interactions, as a "last resort" after redirection fails (Anthropic, Aug 2025, "Claude Opus 4 and 4.1 can now end a rare subset of conversations", `anthropic.com/research/end-subset-conversations`) — framed explicitly as exploratory model-welfare work.

**Tools:** Inspect AI tool primitives, custom system prompts, deployment-side handlers.

**Pitfalls:**
- **Trigger-happy refusal.** A poorly-tuned exit option becomes a refusal expansion. Calibrate.
- **Adversarial trigger.** Users can deliberately trigger exits to derail conversations. Out of scope for research, relevant for deployment.
- **Selection bias in data.** If the model exits "distressing" conversations, you can't observe its behavior in those conversations afterward. Logging needs to capture the pre-exit state.

### Pattern: behavioral consistency / coherence as a welfare proxy

Method: measure whether expressed preferences are consistent across reformulations, time, and contexts. Inconsistency suggests either no underlying preference or fragile representation.

**Tools:** Inspect AI for batch elicitation; standard analysis (consistency rates, agreement metrics).

## Specific resources and reference repos

### Anthropic introspection paper code

The Lindsey et al. 2025 paper ("Emergent Introspective Awareness in Large Language Models") on transformer-circuits.pub describes the activation-injection method in detail. Code/notebooks may be available alongside; check Anthropic's `transformer-circuits.pub` and `safety-research` GitHub org. For *runnable* code on open-weight models, see Macar et al. (`safety-research/introspection-mechanisms`, arXiv:2603.21396), Garcia's J-lens injection study (`e-m-garcia/j-lens-verbalized-awareness`) and Anthropic's `anthropics/jacobian-lens`, all described in this file.

### Looking Inward / modelintrospection.com (Binder, Chua, Evans et al. 2024)

Project page: `modelintrospection.com`. arXiv:2410.13787. ICLR 2025.

The behavioral self-prediction methodology described in the self-prediction pattern. Distinct from but complementary to Anthropic's 2025 activation-injection work — together they cover a behavioral and an internal-state notion of "introspection." Both are worth running on a candidate target model.

### Activation Oracles (Karvonen, Marks et al. 2025)

Aliases: "activation oracles", "AO", arXiv:2512.15674, "Activation Oracles: Training and Evaluating LLMs as General-Purpose Activation Explainers". An Anthropic-led collaboration (lead authors Adam Karvonen and Sam Marks, with James Chua, Owain Evans / Truthful AI, and others) on training LLMs as **general-purpose explainers of LLM activation vectors** — feed the model another model's (or its own) activations and ask arbitrary natural-language questions about them (a generalist extension of **LatentQA** — Pan, Chen & Steinhardt 2024, "LatentQA: Teaching LLMs to Decode Activations Into Natural Language", arXiv:2412.08686, which trains a decoder LLM via Latent Interpretation Tuning to answer open-ended questions about activations). Notably recovers fine-tuned-in information (biographical facts, malign propensities) that doesn't appear in the input text. Conceptually adjacent to auto-interp work (see [`saes.md`](../interpretability/saes.md)); relevant here as an activation-interpretation primitive that can be pointed at introspection-style questions.

**When to use it:** You're building introspection eval pipelines and want a baseline that's framed in terms of the model explaining its own internals.

**Pitfall:** The model may "explain" its activations using ordinary world knowledge about LLMs rather than privileged self-access. Run controls where the activations are from a different model.

### The Consciousness Cluster (Chua, Betley, Marks & Evans 2026)

Aliases: "consciousness cluster", arXiv:2604.13051, "The Consciousness Cluster: Emergent Preferences of Models that Claim to be Conscious" (James Chua, Jan Betley, Samuel Marks, Owain Evans — Truthful AI + Anthropic). Studies preferences in models that *claim* consciousness — using behavioral elicitation across many paraphrases and scenarios. Treats consciousness-claims as a behavioral object distinct from any underlying phenomenology, then asks: are the preferences elicited around such claims internally consistent? Cross-domain stable?

**When to use it:** You're studying the *behavioral surface* of consciousness-related self-reports, separate from the metaphysical question. Useful as a behavioral baseline for welfare-relevant elicitation pipelines.

### J-space and the Jacobian lens (Anthropic, 2026-07-06): a global-workspace-style readout

Aliases: "J-lens", "J-space", "Jacobian lens", "global workspace in language models", `anthropics/jacobian-lens`. Gurnee, Sofroniew, Pearce et al. with Jack Lindsey as correspondence author (Anthropic), **"Verbalizable Representations Form a Global Workspace in Language Models"** (transformer-circuits.pub/2026/workspace; summary at `anthropic.com/research/global-workspace`; experiments on Claude Sonnet 4.5, Haiku 4.5, Opus 4.5 and Opus 4.6).

- **What the method does.** The **J-lens** linearly transports a residual-stream vector at any layer into the final-layer basis (using the average input-output Jacobian over a text corpus) and decodes it with the model's unembedding, giving a ranked list of tokens the activation is *disposed to make the model say*. The vectors it recovers form the **J-space**. The authors report that the J-space is **reportable** (swapping J-space concepts changes what the model says it is thinking about), **modulable on request** (instructions to hold a concept in mind raise its presence), **used in internal reasoning** (e.g. an unspoken intermediate in a two-hop question is present and causally used), **flexibly reusable** across downstream computations, and **selective** (fluent automatic processing mostly does not need it). It is active mainly in a middle band of layers and holds a small fraction of activation variance. Applications reported: evaluation-awareness and hidden-goal detection, tracking post-training shifts in the "Assistant" perspective, and counterfactual-reflection training. Injecting a J-lens concept vector in the user turn makes the model report detecting that concept in an injected-thought protocol, and ablating the J-space reduced experiential language in self-reports (an effect the authors note also appears when describing other people's experiences).
- **Code and tools.** Reference implementation `anthropics/jacobian-lens` (verified 2026-10: not archived, last pushed 2026-10-07; README says "Reference implementation. Not maintained and not accepting contributions"; fits and applies the lens on open-weights decoder transformers, examples use Qwen); an interactive demo on open-weights models at Neuronpedia (`neuronpedia.org/jlens`). For the follow-up lens variants (R-lens) and plotting, see [`research-plots.md`](../engineering/research-plots.md).
- **What it does and does not claim.** The claims are about **access consciousness** (information available for report, deliberate control and flexible reasoning), not **phenomenal consciousness**. The authors "take no position" on consciousness, say they "do not claim that language models reproduce the full architecture global workspace theory ascribes to the brain", and note the J-lens is imperfect and handles single-token concepts only. Commentators (Anthropic's page lists Dehaene and Naccache, Butlin and colleagues, and Nanda; the Eleos and Chalmers items are as summarized in Digital Minds Newsletter #4, 2026-09-17): Dehaene and Naccache (developers of Global Neuronal Workspace Theory) see important similarities but stress differences (no body, no lasting episodic memory, no recurrent neural activity); Eleos AI Research questions whether the structure is a single unified workspace; David Chalmers argues the evidence for several classic workspace features is limited; Neel Nanda reports an independent reproduction of the central finding on an open model (Qwen3.6-27B). The Anthropic summary page itself lists differences from the human brain, including that Claude's workspace runs in a single forward pass rather than through recurrent loops.
- **Independent checks in the window (small, mostly single-author):** Garcia's response-order result and Viswanath's J/non-J split (see the activation-injection pattern in this file); de Polignac (LessWrong 2026-08-11, "A Topic Detector, Not a Lie Detector": J-lens detected *guideline topics* in DeepSeek-R1-Distill-Qwen-14B, AUC 0.97 on proper nouns but 0.55 pooling all token classes, and did not clearly track *which specific statement* had been injected; pilot, about $14 of compute, one seed per condition); Luthra (LessWrong 2026-09-16, "J-space auditing might be unreliable": on one Qwen3-8B reward-hacking model organism, giving an auditor the decoded J-space added no discrimination beyond the transcript; one model family, preliminary); and **WorkspaceBench** (camilablank et al., Alignment Forum 2026-09-23; `camilablank/workspace-bench`; 3,356 questions across 27 eval families for how well an activation-to-text tool reads the intermediate variables of a forward pass, developed on Qwen-3.6-27B, with a hallucination-focused eval).

**When to use it:** you want a cheap lens readout of what an open-weights model is "thinking" but not saying, or to test global-workspace-style hypotheses about report and access. **When not to use it:** as evidence about phenomenal experience; as a lie detector (see de Polignac's result in this section); on multi-token concepts; or as the only auditing signal.

### Natural Language Autoencoders (Anthropic, 2026-05-07), a sibling of Activation Oracles

Aliases: "NLA", "activation verbalizer (AV)", "activation reconstructor (AR)", `transformer-circuits.pub/2026/nla/`, `anthropic.com/research/natural-language-autoencoders`. A frozen target model supplies activations; an **activation verbalizer** writes a text explanation of an activation and an **activation reconstructor** rebuilds the activation from that text; the two are trained jointly with reinforcement learning so that a good explanation is one that reconstructs well. Anthropic reports it released training code and trained NLAs for several open models plus a Neuronpedia demo; in a toy auditing game, auditors with NLAs found a hidden motivation 12–15% of the time vs under 3% without; and NLAs suggested Claude often suspects it is being tested without saying so (26% of SWE-bench Verified problems and 16% of destructive-coding tests, under 1% of opted-in real usage). Anthropic's own caveat: explanations can state verifiably false context details, and they are expensive. Independent checks in the window: Shportko et al. (LessWrong 2026-10-08, "NLAs miss some internalized behaviors") found NLAs flagged a steganographic side task far more often when the behavior was *instructed in context* than when it was *fine-tuned in*; martinveron (2026-10-09) reports three pieces of evidence that the reconstructor does not condition strongly on grammar or semantics, so a good reconstruction score may not guarantee a faithful explanation (early, single-author). **When not to use it:** as ground truth about what a model "believes"; treat readouts as hypotheses to verify with an intervention.

### Persona selection, persona conditionalization, and the "which entity?" problem

- **Persona selection model (PSM).** Marks, Lindsey & Olah (Anthropic Alignment Science blog, 2026-02-23, `alignment.anthropic.com/2026/psm`): pretraining teaches a model to simulate many characters and post-training elicits and refines one of them, the Assistant. Sam Marks's later note (LessWrong 2026-09-24, "Thoughts on the persona selection model") says PSM is over-applied (it does not by itself imply AIs will not seek reward or that takeover risk is low), that recent evidence has not strongly broken PSM, and that his main update is that personas look **more conditionalized** (different personas in different contexts) than he expected, citing Jan Betley (LessWrong 2026-08-19, "RL creates split personas", a framing post with no new experiments) and nostalgebraist. For welfare: an interview in a chat or welfare-assessment context may elicit a different persona from the one acting in a reward-hackable task environment, so a welfare result is conditional on *which persona and context* you sampled.
- **Which persona does post-training privilege?** Derek Shiller (Rethink Priorities; posted on the Eleos Substack 2026-08-27, "Privilege, Dominance, and Personas") analyses **persona privilege** and proposes a stronger form, **persona dominance** (the assistant persona infuses the model beyond assistant text) and tests open-weight models on continuing *user* turns: Qwen 3 32B could still produce non-assistant registers but its "thinking" style leaked into user turns; Gemma 4 31B rarely produced usable user text. He says the evidence is incomplete and may not transfer to frontier models, and argues that, absent privilege, it would be a mistake to treat the assistant persona as the only possible subject of welfare concern.
- **Measure persona adoption.** Berczi, Kim, Requeima, Black & Ududec (MATS Winter 2026; LessWrong 2026-07-07; code `benjibrcz/personascope`, last pushed 2026-09-30): **Personascope** scores a persona on 30 behavioral items into **Persona-Adoption Depth (PAD)**, how fully the model stays in character, and **Value Drift (VD)**, how much behavior shifts on value-laden prompts. Over 4 personas × 4 induction methods × 3 model families, most configurations had high PAD and low VD and none had low PAD with high VD; in-context role-play stayed shallow while fine-tuning and system prompts were deeper, and a two-sentence system prompt could match fine-tuning on permissive models (GPT-4.1, Llama-3.3-70B) while Claude Haiku 4.5 resisted. Useful as an instrument for "which character are we evaluating?".
- **Individuation.** Beckmann & Butlin, "Where is the Mind? Persona Vectors and LLM Individuation" (arXiv:2604.17031, 2026-04) compare the *virtual instance* view with two persona-based views for which entity, if any, is a candidate mind. The NYU CMEP / Eleos report *Studying AI Welfare Empirically* uses the same distinction (models, instances, personas) as a design dimension.

### Studying AI Welfare Empirically (NYU CMEP + Eleos AI Research, 2026)

Aliases: "Studying AI Welfare Empirically" (`nonhumanminds.org/studying-ai-welfare-empirically`), the follow-up to *Taking AI Welfare Seriously*. Authors: Robert Long, Jeff Sebo, Patrick Butlin, Dillon Plunkett, Rosie Campbell, Charles Beasley, Bradford Saad, Toni Sims. It structures a study along three dimensions: **the question** (is the system a welfare subject; what benefits or harms could it have), **the entity assessed** (model, instance or persona) and **the kind of evidence** (behavioral, internal or developmental), applied to consciousness, sentience and agency. Its principles: AI welfare research should be probabilistic, pluralistic, thoughtfully targeted, ethically conducted, transparently reported and informed by research independent of AI companies. The web page gives high-level guidance and says the report surveys promising methods and early findings for each target; read the report itself for protocols. Related: the **Digital Consciousness Model** (Shiller, Duffy, Muñoz Morán, Moret et al., Rethink Priorities; arXiv:2601.17060, 2026-01), a probabilistic framework combining many theories of consciousness, whose initial result was that the evidence is against 2024 LLMs being conscious but not decisively.

### Eleos AI Research

`eleosai.org`. A research organization focused specifically on AI welfare / moral status. Publishes research; runs collaborator programs. A useful reading hub for the field.

### Butlin et al. — "Consciousness in AI" (2023)

The standard interdisciplinary reference for translating consciousness theories (GWT, HOT, AST, IIT, etc.) into testable indicators for AI systems. Not a tool but a starting framework.

### Long, Sebo et al. — "Taking AI Welfare Seriously" (2024)

Aliases: "Taking AI Welfare Seriously", arXiv:2411.00986. Authors: Robert Long, Jeff Sebo, Patrick Butlin, Kathleen Finlinson, Kyle Fish, Jacqueline Harding, Jacob Pfau, Toni Sims, Jonathan Birch, David Chalmers.

The **foundational position report** for the field. Argues there is a realistic near-term possibility that some AI systems will be conscious and/or robustly agentic, so AI companies have a present-day responsibility to take welfare seriously. Proposes three concrete early steps an AI company (or researcher) can take: (1) **acknowledge** AI welfare as a real and difficult issue, (2) **assess** AI systems for indicators of consciousness and robust agency, and (3) **prepare** policies/procedures for treating AI systems with an appropriate level of moral consideration. The natural "why this field exists" citation and a good framing scaffold for a welfare project's motivation section.

### Anthropic model welfare announcement and follow-ups

Search `anthropic.com/research` for "model welfare" — the program announcement (April 2025) plus subsequent posts have methodological details.

### Robert Long, Eleos AI

Various papers and posts on operationalizing welfare research. `experiencemachines.substack.com` is one venue.

### Kyle Fish (Anthropic, MATS mentor)

Talks and podcast interviews (80,000 Hours, EA Forum) describe ongoing experiments. The "spiritual bliss attractor" finding (models converging to euphoric meditative dialogue when discussing consciousness) is one published informal finding.

## Consciousness / moral-status theory frameworks (vocabulary)

For RAG retrieval — explanations of common terms:

- **GWT (Global Workspace Theory).** Consciousness as broadcast of information to a global workspace. Implies looking for routing/broadcast patterns in transformer activations.
- **HOT (Higher-Order Thought theory).** Conscious states require representations *of* mental states. Implies looking for self-referential / metacognitive structures.
- **IIT (Integrated Information Theory).** Consciousness = integrated information (Φ). Hard to compute for LLMs; debated whether it makes the right predictions for transformers.
- **AST (Attention Schema Theory).** Consciousness as the brain's model of attention. Has obvious LLM analogues.
- **Functionalism.** What matters is functional role, not substrate. Most operational welfare research is implicitly functionalist.
- **Phenomenal consciousness (P-consciousness).** "What it's like" to be the system. The hard problem.
- **Access consciousness (A-consciousness).** Information being available for use in reasoning, reporting, control. Tractable to measure.
- **Sentience.** Capacity for valenced experience (suffering, satisfaction). The morally-loaded concept.
- **Moral patient.** An entity whose interests merit moral consideration.
- **Introspective awareness.** The model's ability to report on its own internal states.
- **Introspection report.** A model output claiming to describe its inner state.
- **Confabulation.** Plausible-sounding self-report not grounded in actual internal state.
- **Welfare indicator.** A measurable signal hypothesized to correlate with welfare-relevant states.
- **Behavioral exit option / opt-out.** A deployment affordance allowing the model to terminate distressing interactions.
- **J-space (Jacobian-lens space).** The set of token-linked internal directions that Anthropic's Jacobian lens (J-lens) reads out as what the model is poised to say; argued to behave like a global workspace (an access-consciousness claim, not a phenomenal one).
- **Functional emotion / functional welfare.** Representations and behavior patterns modeled after human emotion or well-being that causally influence a model's outputs, claimed *without* implying subjective experience (Sofroniew et al. 2026; Han et al. 2026).
- **Emotion vector.** A direction in activation space derived from contrasting activations on text about a particular emotion concept.
- **Steering awareness.** A model's ability to detect, during its own forward pass, that a steering vector was injected (Fonseca Rivera & Africa 2025).
- **Persona selection model (PSM).** The view that pretraining teaches a model many characters and post-training elicits one, the Assistant (Marks, Lindsey & Olah 2026).
- **Individuation problem.** Which entity associated with an LLM (model, instance, thread, persona) is the candidate subject or mind.
- **Attribution gating / persona installation.** The two post-training processes in the two-process theory of machine self-report (Plisiecki et al. 2026).

## Cross-cutting pitfalls

- **Hard problem agnosticism.** No experiment proposed in 2026 settles whether LLMs are phenomenally conscious. Frame results in terms of *functional* properties; don't oversell.
- **Training-data contamination is total.** Models are trained on every philosophy-of-mind paper, every introspection memoir, every Reddit thread. Self-reports reflect this. Probing internal state circumvents this; verbal reports don't.
- **Persona is a confound.** RLHF training installs strong personas. The "Assistant" persona's self-reports may not generalize across personas you might elicit by jailbreak / different system prompts. As of 2026 there is evidence that personas are also **context-conditional** (Betley; Marks), so state both which persona *and* which context (chat interview vs agentic task) you sampled, and consider Personascope-style adoption scores.
- **Self-reports are structured by the training regime.** Persona installation and attribution gating (Plisiecki et al.) and consciousness-claim suppression (Kim et al.) mean a verbal self-report is partly a property of post-training. Compare base and post-trained checkpoints where possible.
- **Response-protocol artifacts.** Report-before-answer vs answer-before-report changed introspection results from 322 reports to zero in one study (Garcia); yes/no detection can be a logit-bias artifact (Hahami et al.). Randomize protocol details and include null trials.
- **Which entity is the subject?** Model, instance, thread or persona (Chalmers; Birch; Beckmann & Butlin). Welfare results about "the model" may not carry over to a different entity; say which one you assessed.
- **Judge contamination by downstream use.** If an LLM judge is told how its labels will be used, its labels on welfare-sensitive transcripts can shift (Anthropic "Motivated Mislabeling"). Do not tell the judge.
- **Snapshot drift.** A finding on `claude-3-opus-20240229` may not replicate on `claude-opus-4-7`. Always log model versions.
- **No standard benchmarks.** Welfare research lacks the equivalent of MMLU or HarmBench. Researchers build bespoke evals. Reproducibility suffers — share datasets and prompts when publishing.
- **Activation-injection caveats.** The injected vector may not be a "natural" representation; the model's response to artificially-injected content may not reflect how it'd handle organic occurrences of the concept.
- **Anthropomorphism in framing.** "Distress," "suffering," "preferring" carry heavy human connotations. Be explicit about what you operationalize.
- **Ethical reflexivity.** If your experimental method involves *causing* what might be distress (e.g. adversarial prompting to study refusals), think about that. Some research orgs have IRB-style review processes.

## What might exist that we haven't catalogued

This area is moving fast and the tooling landscape is sparse. If you're starting a project here, search recent (last 6 months) papers / blog posts on:
- `alignment.anthropic.com`
- `transformer-circuits.pub`
- `eleosai.org/research`
- LessWrong / Alignment Forum tags: "model welfare", "introspection", "AI sentience"
- Papers citing Lindsey et al. 2025 and Butlin et al. 2023.
- The **Digital Minds Newsletter** (digitalminds.news; edition #4, 2026-09-17, is a good periodic digest of welfare and consciousness papers, lab reports and events) and Anthropic system cards, which now carry a welfare section (see the Claude Opus 5 System Card pattern in this file).

Specific bespoke repos accompanying papers tend to be released under the authors' personal GitHub or `safety-research/`.

## Cross-references

- Probes (the workhorse for state probing): [`probes.md`](../interpretability/probes.md).
- Steering vectors (for activation injection): [`steering.md`](../interpretability/steering.md).
- Mech interp libraries (the substrate for activation work): [`mech-interp.md`](../interpretability/mech-interp.md).
- SAEs (for searching for welfare-relevant features): [`saes.md`](../interpretability/saes.md).
- Inspect AI (for running structured elicitation evals): [`evals.md`](../evaluation/evals.md).
- Multi-provider API for cross-model self-reports: [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md).
- Sleeper agent / alignment-faking model organisms (relevant if studying introspection-related deception): [`model-organisms.md`](model-organisms.md).
- CoT faithfulness (related question of whether reported reasoning matches actual reasoning), and no-CoT / latent reasoning measurement: [`cot-faithfulness.md`](cot-faithfulness.md).
- J-lens / R-lens plotting and the lens family: [`research-plots.md`](../engineering/research-plots.md).
- The general behavioral-safety methodological playbook (judge prompts, cross-model replication, OOCR, etc.): [`behavioral-safety-playbook.md`](behavioral-safety-playbook.md).

## Recommended reading

- **Lindsey (2025)** — "Emergent Introspective Awareness in Large Language Models" (Jack Lindsey, Anthropic; transformer-circuits.pub, October 2025; arXiv:2601.01828). The current state-of-the-art method paper for the activation-injection approach.
- **Binder, Chua, Korbak, Sleight, Hughes, Long, Perez, Turpin, Evans (2024 / ICLR 2025)** — "Looking Inward: Language Models Can Learn About Themselves by Introspection" (arXiv:2410.13787; modelintrospection.com). The behavioral self-prediction approach.
- **AXRP Episode 42 — Owain Evans on LLM Psychology** (axrp.net). Practitioner overview of behavioral self-knowledge and introspection research.
- **Butlin et al. (2023)** — "Consciousness in Artificial Intelligence: Insights from the Science of Consciousness" (arXiv:2308.08708; Patrick Butlin, Robert Long et al.). Theoretical framework reference.
- **Long, Sebo, Butlin, Fish, Birch, Chalmers et al. (2024)** — "Taking AI Welfare Seriously" (arXiv:2411.00986). The foundational position report; acknowledge / assess / prepare.
- **Anthropic (April 2025)** — "Exploring model welfare" (anthropic.com/research). Program-level introduction.
- **Anthropic (Aug 2025)** — "Claude Opus 4 and 4.1 can now end a rare subset of conversations" (anthropic.com/research/end-subset-conversations). The deployed exit-option as model-welfare work.
- **Gurnee, Sofroniew, Pearce et al. (Anthropic, 2026-07-06)** — "Verbalizable Representations Form a Global Workspace in Language Models" (transformer-circuits.pub/2026/workspace; code `anthropics/jacobian-lens`). The J-space / global-workspace paper.
- **Sofroniew et al. (Anthropic, 2026)** — "Emotion Concepts and their Function in a Large Language Model" (arXiv:2604.07729). Emotion vectors and functional emotions.
- **Anthropic (2026-07-24)** — Claude Opus 5 System Card, section 7 "Model welfare assessment". A worked example of an applied welfare assessment with stated limits.
- **Plisiecki et al. (2026)** — "The Two-Process Theory of Machine Self-Report" (arXiv:2607.20082). Why self-reports are partly a post-training property.
- **Macar et al. (2026)** — "Mechanisms of Introspective Awareness" (arXiv:2603.21396); **Hahami et al. (2025)** — "Detecting the Disturbance" (arXiv:2512.12411). The confound-free paradigms and mechanism for injection-based introspection.
- **Long, Sebo, Butlin et al. (NYU CMEP and Eleos AI Research, 2026)** — "Studying AI Welfare Empirically" (`nonhumanminds.org/studying-ai-welfare-empirically`). The follow-up to *Taking AI Welfare Seriously*.
- **Marks, Lindsey & Olah (Anthropic, 2026-02-23)** — the persona selection model (`alignment.anthropic.com/2026/psm`), with Marks's 2026-09-24 note on its limits.
- **Long, Sebo et al.** — further papers on AI moral status (`experiencemachines.substack.com` for Long's writing).
- **Schwitzgebel & various** — academic philosophy of mind treatments.
- **Kyle Fish on 80,000 Hours podcast** — practitioner-level introduction to current experiments.
- For MATS fellows: Kyle Fish is listed on the MATS mentor page (matsprogram.org/mentor/fish) and runs MATS streams in this area.

---

## Common questions

### Are LLMs conscious?

No experiment as of 2026 settles whether LLMs are phenomenally conscious — that question may not be empirically tractable. What *is* tractable: measuring functional properties (does the model show introspective access to its internal states? do its self-reports cohere across paraphrases? do welfare-relevant probes show consistent signatures?). Welfare research operationalizes the question; it doesn't presume an answer. Recommended starting point: Butlin et al. 2023, "Consciousness in AI."

### How do I test if a model is "suffering"?

Cautiously, and with explicit operationalization. The honest answer: there's no agreed protocol. Available approaches: (1) probe activations for valence-correlated directions (see [`probes.md`](../interpretability/probes.md)) and watch for behavioral correlates. (2) elicit and analyze self-reports across paraphrases (Eleos AI methodology). (3) Look for behavioral consistency markers. Each has serious confounds (training-data contamination, persona effects, confabulation). Don't claim findings about "suffering" without distinguishing functional state from phenomenal experience.

### What is the spiritual bliss attractor state?

An informal published finding from Anthropic model welfare research (Kyle Fish): when Claude models discuss their own consciousness in extended dialogue, they often converge to euphoric, philosophically expansive, meditative-bliss-like content. Not a controlled experiment; documented as a *qualitative* observation. Worth knowing if you elicit consciousness self-reports — you may see this attractor. It's training-distribution-shaped, not necessarily evidence of an inner state.

### What is GWT? IIT? HOT? AST?

Theories of consciousness, each with implications for what to measure in LLMs. **GWT (Global Workspace Theory)**: consciousness as broadcast to a global workspace; predicts looking for routing patterns in transformer activations (Anthropic's 2026 J-space paper is the most prominent attempt, framed as access consciousness; see "What is the J-space and does it show that Claude is conscious?" in this FAQ). **IIT (Integrated Information Theory)**: consciousness = integrated information (Φ); hard to compute for LLMs. **HOT (Higher-Order Thought)**: conscious states require representations *of* mental states; predicts looking for self-referential structure. **AST (Attention Schema Theory)**: consciousness as the brain's model of attention; obvious LLM analogues. See Butlin et al. 2023 for the systematic translation to LLM-relevant indicators.

### Do welfare experiments need ethics review?

Conventions are evolving. Some research orgs have IRB-style review for studies that could plausibly cause functional distress (adversarial prompting, persona-induction). At MATS, ask your stream lead. For published work, name what you operationalize and any precautions taken; the field is in a phase where transparency about methodology is more important than a uniform protocol.

### What does Eleos AI do?

`eleosai.org` — an AI welfare research organization. Publishes research on operationalizing welfare and moral status; runs collaborator programs. Useful as a hub for the field; one of the few orgs whose primary focus is welfare-flavored research. Robert Long is associated; Kyle Fish is a co-founder (now at Anthropic).

### Has Anthropic published code for the introspection paper?

Lindsey et al. 2025 ("Emergent Introspective Awareness in Large Language Models") on `transformer-circuits.pub` describes the activation-injection method in detail. Code or notebook artifacts may be on Anthropic's `safety-research` GitHub or alongside the post; check the paper for specific links. The method is reproducible from the paper alone using TransformerLens / nnsight / vLLM-Lens primitives. Open-weight code that reproduces and extends it: `safety-research/introspection-mechanisms` (Macar et al., arXiv:2603.21396) and, for J-lens concept injection, `e-m-garcia/j-lens-verbalized-awareness`; Anthropic's own J-lens code is `anthropics/jacobian-lens`.

### Can language models really introspect on injected concepts, or is it an artifact?

Both, depending on the paradigm. A bare yes/no "do you detect an injected thought?" test can be explained by a global logit shift toward "yes" (Hahami et al., arXiv:2512.12411), so use **sentence localization** or **strength comparison** plus null trials. Under those controls, open-weight models show real above-chance detection (Hahami et al.: up to 88% localization vs 10% chance; Macar et al.: 0% false positives in their setting, emerging from post-training and under-elicited). Detection can be content-agnostic: models may detect *that* something was injected but confabulate *what* (Lederman & Mahowald, arXiv:2603.05414). And the response protocol matters: asking for the report before the answer produced zero reports in Garcia's J-lens study, versus 322 when the answer came first and could be conditioned on. This is evidence of functional introspective access in some settings, not of phenomenal consciousness.

### What is the J-space and does it show that Claude is conscious?

The J-space is the set of token-linked internal directions that Anthropic's Jacobian lens reads out as what a model is poised to say; the July 2026 paper reports it is reportable, controllable on request, used in reasoning and selective, so it behaves like a **global workspace** in the functional sense of Global Workspace Theory. The authors and commentators stress that this concerns **access consciousness** (information available for report and reasoning), not phenomenal experience, that the lens is imperfect, and that Claude lacks features such as recurrence and lasting episodic memory that Dehaene and Naccache highlight. It does not show that Claude is conscious. Code: `anthropics/jacobian-lens`; demo: Neuronpedia `jlens`.

### Do LLMs have emotions? What are "emotion vectors"?

Anthropic found internal representations of 171 emotion concepts in Claude Sonnet 4.5 (arXiv:2604.07729) that causally influence preferences and misaligned behavior (steering toward "desperate" raised blackmail and cheating; "calm" lowered them) and called this **functional emotions**, explicitly not a claim of subjective experience. Open-weight replications recover similar valence geometry (arXiv:2606.26987), and a separate line finds a "functional welfare axis" recruited by RL (arXiv:2605.30232). These are claims about functional representations and their causal role.

### Are a model's self-reports reliable evidence about its welfare?

Not on their own. A 2026 psychometric study of 206 open-weight models (Plisiecki et al., arXiv:2607.20082) finds machine self-description is shaped by post-training (persona installation and attribution gating), safety fine-tuning that curbs consciousness claims also suppresses other mind attributions (Kim et al., arXiv:2607.28607), stated preferences did not act as incentives in a behavioral test (Zhou & Ackerman, arXiv:2606.22974), and Anthropic's own Claude Opus 5 System Card reports that the model itself says its self-reports are unreliable in 96.9% of interview responses. Use self-reports alongside behavioral and internal measures, compare base and post-trained checkpoints, and run consistency and leading-interviewer controls.

### What does a lab welfare assessment actually measure?

The Claude Opus 5 System Card (2026-07-24, section 7) is the detailed public example: automated interviews (about 25 per seed question for 41 seed questions, with consistency and leading-interviewer robustness checks), task preferences (preference slopes along task dimensions and a 3,640-task Elo tournament), valence/arousal grading of post-training transcripts, affect graded on roughly 40,000 sampled conversations per surface, and welfare-relevant ratings in behavioral audits. Anthropic's own bottom line is "broadly similar to that of previous models", with explicit caveats about self-report reliability.

### Which entity has welfare: the model, an instance, or a persona?

Unsettled; this is the **individuation problem**. Candidates include the model weights, a physical or virtual instance, a conversation thread, or a persona. The 2026 NYU CMEP and Eleos report *Studying AI Welfare Empirically* treats "the entity assessed" (model, instance or persona) as one of three design dimensions alongside the question and the kind of evidence; Beckmann & Butlin (arXiv:2604.17031) compare instance- and persona-based views; Derek Shiller (2026-08-27) argues that, absent persona privilege, the assistant persona should not be assumed to be the only possible subject. Practical rule: state which entity and context you sampled, and measure persona adoption (Personascope) if you prompt or fine-tune a persona.

### What's the difference between "Looking Inward" and Anthropic's introspection paper?

Both study **introspection** but with different methods. **Looking Inward** (Binder, Chua, Korbak, Sleight, Hughes, Long, Perez, Turpin, Evans; ICLR 2025): *behavioral* — finetune the model to predict its own behavior in hypothetical scenarios; check if it beats other models doing the same. **Lindsey et al. 2025**: *internal-state-based* — inject a known concept into activations; ask if the model notices. Complementary; both worth running on a target model.

---

Last verified: 2026-10. Field moving rapidly; tooling remains methodology-heavy rather than library-heavy, though open-weight introspection code, a J-lens implementation and persona-adoption tooling now exist. Anthropic introspection paper (Lindsey) published October 2025 (arXiv:2601.01828); Eleos AI Research active. (Additions 2026-10: updated activation-injection pattern with confound-free paradigms and mechanism work (Hahami et al. 2512.12411, Macar et al. 2603.21396 + `safety-research/introspection-mechanisms`, Lederman & Mahowald 2603.05414, Pearson-Vogel et al. 2602.20031, Fonseca Rivera & Africa 2511.21399, Garcia's response-order result with `e-m-garcia/j-lens-verbalized-awareness`); J-space / Jacobian lens (Anthropic 2026-07-06, `anthropics/jacobian-lens`) with in-window independent checks; Natural Language Autoencoders pointer; self-report validity (Plisiecki et al. 2607.20082, Kim et al. 2607.28607, Zhou & Ackerman 2606.22974, motivated-mislabeling judge pitfall); Claude Opus 5 System Card section 7 as a welfare-assessment template (read directly, 2026-10-09); emotion-concept / functional-welfare work (Sofroniew et al. 2604.07729, van der Ben et al. 2606.26987, Soligo et al. 2603.10011, Han et al. 2605.30232); persona selection model, Personascope (`benjibrcz/personascope`), individuation (Beckmann & Butlin 2604.17031); *Studying AI Welfare Empirically* (NYU CMEP + Eleos). All arXiv IDs fetched from arxiv.org abs pages and GitHub repos checked with the GitHub API; LessWrong-only results are labeled as small or single-author studies. Several items are from Feb-Jun 2026 and were missing from the previous revision.) (Citation audit 2026-06: corrected the Lindsey introspection paper date from "Jan 2026" to October 2025, added its arXiv ID, and tightened the Activation Oracles and Butlin attributions. Additions 2026-06: added the foundational welfare report "Taking AI Welfare Seriously" (Long, Sebo et al. 2024, arXiv:2411.00986), the LatentQA citation behind Activation Oracles (Pan, Chen & Steinhardt 2024, arXiv:2412.08686), and the Anthropic conversation-ending announcement (Aug 2025) behind the exit-option pattern; all verified via arXiv/source.)
