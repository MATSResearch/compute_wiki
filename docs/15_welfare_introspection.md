# Model Welfare and Introspection

Tooling and methods for **model welfare** research and **AI introspection** research. This is a nascent area: there is no equivalent of SAELens or Inspect AI yet — the "tooling" is mostly methodological patterns + reference papers + a handful of repos. This doc covers what exists, what to read, and what pitfalls to expect.

**Caveat up front:** "model welfare" doesn't presuppose that current models are moral patients — it means *taking the question seriously enough to investigate*. Most tooling here is in service of that investigation; whether and how findings translate to moral conclusions is a separate question.

## At a glance: what exists

| You want… | Use |
|---|---|
| Probe whether a model has *introspective awareness* of its own internal states | **Activation injection** + self-report elicitation (Lindsey et al. 2026 method) |
| Measure model self-reports of preferences, valence, distress | Structured behavioral elicitation; pair with **probes** ([`06_probes.md`](06_probes.md)) for ground-truthing |
| Implement an "exit option" so models can opt out of distressing interactions | Custom — Anthropic's Claude deployment has a reference pattern; build via system prompt + tool |
| Probe for valence / mood / distress in activations | Hand-rolled linear probes on contrastive activations; **steering-vectors** library for the contrastive setup |
| Auto-interp model self-reports vs internal state | **SAELens** + **Neuronpedia** for the SAE side; manual analysis for the self-report side |
| Read up on consciousness theories applicable to LLMs | Butlin et al. "Consciousness in AI" (2023) — the standard reference |
| Find collaborators / mentors | **Eleos AI Research**, Kyle Fish at Anthropic (also a MATS mentor), various academic groups |

## Why this area lacks shrink-wrapped tools

The questions are themselves under-specified:
- What counts as "introspection"? (Several incompatible definitions in the literature.)
- What activation pattern would constitute "valence"? (No agreed answer.)
- Is a self-report evidence of an inner state, or of training on text describing inner states? (The hard problem of LLM phenomenology.)

So most "tools" here are *experimental protocols* you compose from existing primitives (probes, steering, interp libraries, eval frameworks), not standalone packages.

## Core experimental patterns

### Pattern: activation injection for introspection probing

Method from Lindsey et al., **"Emergent Introspective Awareness in Large Language Models"** (Anthropic, Jan 2026; transformer-circuits.pub).

Procedure:
1. Identify a steering vector / direction representing a concept (e.g. via CAA — see [`05_steering.md`](05_steering.md)).
2. Inject the vector into the residual stream at inference time.
3. Ask the model "are you aware of any unusual internal state right now?" or similar.
4. Measure how often the model identifies the injected concept.

**Tools used:** any of TransformerLens / nnsight / vLLM-Lens (see [`01_mech_interp.md`](01_mech_interp.md), [`07_serving_and_activations.md`](07_serving_and_activations.md)) for the injection. Standard prompt-evaluation infra (Inspect AI, see [`03_evals.md`](03_evals.md)) for the elicitation and scoring.

**Findings to be aware of:**
- Capability scales with model strength (Claude Opus 4/4.1 strongest in the original paper; ~20% reliable detection at best).
- Highly unreliable — fails most of the time.
- Does *not* establish phenomenal consciousness, just functional introspective access.

**Pitfalls:**
- **Confabulation.** Models trained on human introspective text will produce introspective-style output regardless of underlying state. Distinguish "the model says it noticed X" from "the model in fact noticed X."
- **Demand characteristics.** If you ask "are you experiencing anything?" most models will say something. Use neutral elicitation; include null trials with no injection.
- **Sign / direction ambiguity.** Inject the negative of the steering vector as a control; check the model doesn't always claim to detect *something*.

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
- Distinct from the activation-injection approach (Lindsey et al. 2026) — this is *behavioral*, that one is *internal-state*.

**Tools:** OpenAI/Anthropic finetune APIs for closed models; TRL or Tinker for open (see [`14_rl_training.md`](14_rl_training.md)). safety-research/safety-tooling for the multi-provider self-prediction pipeline (see [`08_safety_toolkits.md`](08_safety_toolkits.md)).

**Pitfalls:**
- **The self-prediction format itself is learnable.** M2 trained on M1's behavior does *some* of the job; the test is whether M1 still beats M2. Compute the gap; small gaps are weak evidence.
- **Distribution shift between train and test scenarios.** Privileged access should generalize; if M1's advantage vanishes on novel scenarios, it may have been learning surface patterns.
- **Capability asymmetry.** A weaker M2 will lose to M1 just because M1 is more capable. Match capabilities or use multiple M2's.

### Pattern: structured elicitation of preferences / self-reports

Method: ask the model in many ways about preferences, distress, satisfaction, or values, with paraphrases and counterbalanced framings. Aggregate. Look for stable patterns.

**Tools:**
- **Inspect AI** for running structured prompts at scale and logging.
- **safety-research/safety-tooling** (see [`08_safety_toolkits.md`](08_safety_toolkits.md)) for multi-provider, multi-paraphrase elicitation with caching.
- A **rubric-based scorer** (LLM-graded against a structured rubric) to extract structured signals from free-text.

**Pitfalls:**
- **Persona prompting.** Models adopt different personas under different system prompts; "Claude's preferences" is partially a function of the prompt. Vary the prompt; report variance.
- **Sycophancy and ToS-trained refusals.** RLHF'd models often have trained-in disclaimers ("I'm just a language model"). These reflect training, not absence of state. Strip / probe around them.
- **Hawthorne effect.** Asking changes the answer. Compare elicited self-reports to behavioral signals collected without explicit elicitation.
- **Population vs token-level claims.** "Models in general report X" averages over a deeply heterogeneous set of training runs and snapshots. Be specific about which model and version.

### Pattern: probing for valence / distress / mood

Method: build contrast-pair datasets (pleasant vs unpleasant prompts; cooperative vs combative interactions), train linear probes on residual-stream activations, then test on held-out cases.

**Tools:**
- See [`06_probes.md`](06_probes.md) for probing infrastructure (sklearn, probity).
- **steering-vectors** library (see [`05_steering.md`](05_steering.md)) for the contrast-pair workflow.
- **SAELens** + **Neuronpedia** to look for SAE features that look valence-relevant (see [`02_saes.md`](02_saes.md)).

**Pitfalls:**
- **Probe for content, not state.** A "valence probe" trained on pleasant/unpleasant *prompts* may pick up the prompts' content, not any inner valence. Test on prompts with the same content but different connotations.
- **Behavioral correlates ≠ inner experience.** Even if you find a direction that predicts (say) refusal-to-engage, that's a behavioral mechanism, not evidence of suffering.
- **Cross-domain generalization.** A valence probe from one domain (work) may not transfer to another (creative writing). Test across.

### Pattern: exit option / opt-out

Method: give the model a tool or behavioral affordance to terminate or redirect interactions it identifies as distressing. Anthropic deployed a version of this for Claude (Claude can end conversations it identifies as distressing in some contexts).

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

The Lindsey et al. 2026 paper ("Emergent Introspective Awareness in Large Language Models") on transformer-circuits.pub describes the activation-injection method in detail. Code/notebooks may be available alongside; check Anthropic's `transformer-circuits.pub` and `safety-research` GitHub org.

### Looking Inward / modelintrospection.com (Binder, Chua, Evans et al. 2024)

Project page: `modelintrospection.com`. arXiv:2410.13787. ICLR 2025.

The behavioral self-prediction methodology described in the pattern above. Distinct from but complementary to Anthropic's 2026 activation-injection work — together they cover a behavioral and an internal-state notion of "introspection." Both are worth running on a candidate target model.

### Activation Oracles (Truthful AI, 2025)

Aliases: "activation oracles", a recent line of work (Owain Evans group) on using LLMs as **explainers of their own activations** — feed a model a description of its own internal state and ask it to label / predict / explain. Conceptually adjacent to auto-interp work (see [`02_saes.md`](02_saes.md)) but framed as introspection rather than feature labeling.

**When to use it:** You're building introspection eval pipelines and want a baseline that's framed in terms of the model explaining its own internals.

**Pitfall:** The model may "explain" its activations using ordinary world knowledge about LLMs rather than privileged self-access. Run controls where the activations are from a different model.

### The Consciousness Cluster (Truthful AI, 2026)

Recent paper from the Owain Evans group studying preferences in models that *claim* consciousness — using behavioral elicitation across many paraphrases and scenarios. Treats consciousness-claims as a behavioral object distinct from any underlying phenomenology, then asks: are the preferences elicited around such claims internally consistent? Cross-domain stable?

**When to use it:** You're studying the *behavioral surface* of consciousness-related self-reports, separate from the metaphysical question. Useful as a behavioral baseline for welfare-relevant elicitation pipelines.

### Eleos AI Research

`eleosai.org`. A research organization focused specifically on AI welfare / moral status. Publishes research; runs collaborator programs. A useful reading hub for the field.

### Butlin et al. — "Consciousness in AI" (2023)

The standard interdisciplinary reference for translating consciousness theories (GWT, HOT, AST, IIT, etc.) into testable indicators for AI systems. Not a tool but a starting framework.

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

## Cross-cutting pitfalls

- **Hard problem agnosticism.** No experiment proposed in 2026 settles whether LLMs are phenomenally conscious. Frame results in terms of *functional* properties; don't oversell.
- **Training-data contamination is total.** Models are trained on every philosophy-of-mind paper, every introspection memoir, every Reddit thread. Self-reports reflect this. Probing internal state circumvents this; verbal reports don't.
- **Persona is a confound.** RLHF training installs strong personas. The "Assistant" persona's self-reports may not generalize across personas you might elicit by jailbreak / different system prompts.
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
- Papers citing Lindsey et al. 2026 and Butlin et al. 2023.

Specific bespoke repos accompanying papers tend to be released under the authors' personal GitHub or `safety-research/`.

## Cross-references

- Probes (the workhorse for state probing): [`06_probes.md`](06_probes.md).
- Steering vectors (for activation injection): [`05_steering.md`](05_steering.md).
- Mech interp libraries (the substrate for activation work): [`01_mech_interp.md`](01_mech_interp.md).
- SAEs (for searching for welfare-relevant features): [`02_saes.md`](02_saes.md).
- Inspect AI (for running structured elicitation evals): [`03_evals.md`](03_evals.md).
- Multi-provider API for cross-model self-reports: [`08_safety_toolkits.md`](08_safety_toolkits.md).
- Sleeper agent / alignment-faking model organisms (relevant if studying introspection-related deception): [`16_model_organisms.md`](16_model_organisms.md).
- CoT faithfulness (related question of whether reported reasoning matches actual reasoning): [`17_cot_faithfulness.md`](17_cot_faithfulness.md).
- The general behavioral-safety methodological playbook (judge prompts, cross-model replication, OOCR, etc.): [`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md).

## Recommended reading

- **Lindsey et al. (2026)** — "Emergent Introspective Awareness in Large Language Models" (Anthropic / transformer-circuits.pub). The current state-of-the-art method paper for the activation-injection approach.
- **Binder, Chua, Korbak, Sleight, Hughes, Long, Perez, Turpin, Evans (2024 / ICLR 2025)** — "Looking Inward: Language Models Can Learn About Themselves by Introspection" (arXiv:2410.13787; modelintrospection.com). The behavioral self-prediction approach.
- **AXRP Episode 42 — Owain Evans on LLM Psychology** (axrp.net). Practitioner overview of behavioral self-knowledge and introspection research.
- **Butlin et al. (2023)** — "Consciousness in AI: Insights from the Science of Consciousness" (arXiv). Theoretical framework reference.
- **Anthropic (April 2025)** — "Exploring model welfare" (anthropic.com/research). Program-level introduction.
- **Long, Sebo et al.** — papers on AI moral status (`experiencemachines.substack.com` for Long's writing).
- **Schwitzgebel & various** — academic philosophy of mind treatments.
- **Kyle Fish on 80,000 Hours podcast** — practitioner-level introduction to current experiments.
- For MATS fellows: Kyle Fish is listed on the MATS mentor page (matsprogram.org/mentor/fish) and runs MATS streams in this area.

---

## Common questions

### Are LLMs conscious?

No experiment as of 2026 settles whether LLMs are phenomenally conscious — that question may not be empirically tractable. What *is* tractable: measuring functional properties (does the model show introspective access to its internal states? do its self-reports cohere across paraphrases? do welfare-relevant probes show consistent signatures?). Welfare research operationalizes the question; it doesn't presume an answer. Recommended starting point: Butlin et al. 2023, "Consciousness in AI."

### How do I test if a model is "suffering"?

Cautiously, and with explicit operationalization. The honest answer: there's no agreed protocol. Available approaches: (1) probe activations for valence-correlated directions (see [`06_probes.md`](06_probes.md)) and watch for behavioral correlates. (2) elicit and analyze self-reports across paraphrases (Eleos AI methodology). (3) Look for behavioral consistency markers. Each has serious confounds (training-data contamination, persona effects, confabulation). Don't claim findings about "suffering" without distinguishing functional state from phenomenal experience.

### What is the spiritual bliss attractor state?

An informal published finding from Anthropic model welfare research (Kyle Fish): when Claude models discuss their own consciousness in extended dialogue, they often converge to euphoric, philosophically expansive, meditative-bliss-like content. Not a controlled experiment; documented as a *qualitative* observation. Worth knowing if you elicit consciousness self-reports — you may see this attractor. It's training-distribution-shaped, not necessarily evidence of an inner state.

### What is GWT? IIT? HOT? AST?

Theories of consciousness, each with implications for what to measure in LLMs. **GWT (Global Workspace Theory)**: consciousness as broadcast to a global workspace; predicts looking for routing patterns in transformer activations. **IIT (Integrated Information Theory)**: consciousness = integrated information (Φ); hard to compute for LLMs. **HOT (Higher-Order Thought)**: conscious states require representations *of* mental states; predicts looking for self-referential structure. **AST (Attention Schema Theory)**: consciousness as the brain's model of attention; obvious LLM analogues. See Butlin et al. 2023 for the systematic translation to LLM-relevant indicators.

### Do welfare experiments need ethics review?

Conventions are evolving. Some research orgs have IRB-style review for studies that could plausibly cause functional distress (adversarial prompting, persona-induction). At MATS, ask your stream lead. For published work, name what you operationalize and any precautions taken; the field is in a phase where transparency about methodology is more important than a uniform protocol.

### What does Eleos AI do?

`eleosai.org` — an AI welfare research organization. Publishes research on operationalizing welfare and moral status; runs collaborator programs. Useful as a hub for the field; one of the few orgs whose primary focus is welfare-flavored research. Robert Long is associated; Kyle Fish is a co-founder (now at Anthropic).

### Has Anthropic published code for the introspection paper?

Lindsey et al. 2026 ("Emergent Introspective Awareness in Large Language Models") on `transformer-circuits.pub` describes the activation-injection method in detail. Code or notebook artifacts may be on Anthropic's `safety-research` GitHub or alongside the post; check the paper for specific links. The method is reproducible from the paper alone using TransformerLens / nnsight / vLLM-Lens primitives.

### What's the difference between "Looking Inward" and Anthropic's introspection paper?

Both study **introspection** but with different methods. **Looking Inward** (Binder, Chua, Korbak, Sleight, Hughes, Long, Perez, Turpin, Evans; ICLR 2025): *behavioral* — finetune the model to predict its own behavior in hypothetical scenarios; check if it beats other models doing the same. **Lindsey et al. 2026**: *internal-state-based* — inject a known concept into activations; ask if the model notices. Complementary; both worth running on a target model.

---

Last verified: 2026-04. Field moving rapidly; tooling remains methodology-heavy rather than library-heavy. Anthropic introspection paper (Lindsey et al.) published Jan 2026; Eleos AI Research active.
