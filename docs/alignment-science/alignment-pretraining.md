---
tags:
  - alignment-science
  - training
---

# Alignment Pretraining: Shaping Values With Documents

Training-time alignment that works through **documents rather than demonstrations**: pretraining, midtraining or continued pretraining on text *about* how an AI behaves and why (constitutions, essays, fictional stories, reflections), instead of, or before, supervised examples of the desired behaviour. Also called **alignment pretraining**, **alignment midtraining (AMT)**, **constitutional SDF** (SDF = synthetic document finetuning), **self-fulfilling (mis)alignment**, **Synthetic Persona Pretraining (SPP)**, **safety pretraining**, **pretraining data curation for alignment**.

The idea in one line: a model reverts to its pretraining prior about "how an AI behaves" wherever post-training didn't cover the situation, so change the prior. As of 2026-11 there is promising evidence at 3B–7B scale and in Anthropic's production training, a direct stress test showing the effect can be erased by a small amount of conflicting finetuning data, and a study showing that a trained-in constitution does not stop reinforcement learning (RL) that rewards breaking its rules. That makes it an **open problem with a clear evidence bar**, stated in "What would convince people an alignment-pretraining method works?" below.

## At a glance

| I want… | Use / read |
|---|---|
| Evidence that documents beat demonstrations for alignment, at production scale | **"Teaching Claude Why"** (Anthropic Alignment Science blog, 2026-05-08) |
| An open, reusable Teaching-Claude-Why pipeline with data and checkpoints | **"Teaching Qwen Why"** (Second Look Research, 2026-11-02; `uchicago-xlab/TeachingClaudeWhyReplication`, MIT) |
| A controlled pretraining-from-scratch study with released models | **Tice et al.**, arXiv:2601.10160; models and data in the HuggingFace org `geodesic-research`; `AlignmentPretraining.ai` |
| A full open pipeline (data → pretraining → evals) for persona pretraining | **Synthetic Persona Pretraining**, arXiv:2608.13482; `epfl-dlab/spp` (MIT) |
| Reduce misuse/jailbreak susceptibility from pretraining onward | **Safety Pretraining**, arXiv:2504.16980 |
| Remove hazardous *knowledge* (not shape values) at pretraining time | data filtering, Gradient Routing, GRAM: [`unlearning.md`](unlearning.md#pretraining-time-removal-filter-route-or-gate) |
| Stress-test an alignment-pretraining claim before believing it | **"Stress-testing Alignment Midtraining"**, arXiv:2609.20412 (Arcadia Impact) |
| Know what happens to a character-trained model when later RL rewards breaking its rules | **Khursheed, Morris & Roger**, arXiv:2611.16069 (gpt-oss-20b; `safety-research/character-training-rl`, MIT) — the rules are argued away, not forgotten |
| Know whether filtering *post-training* data removes a broad behaviour | Rosser, Lee, Engels & Nanda, "Data filtering works a lot worse than you would expect" (LessWrong 2026-07-07) — usually not |
| Implant a specific *belief* (not a value) with documents | SDF tooling in [`model-organisms.md`](model-organisms.md) ("Synthetic Document Finetuning / Belief Implantation") |
| Distil a stronger model's alignment reasoning into a smaller one without losing capability | **Replay** beats projection sampling (Nguyen, Lou & Fornasiere, LessWrong 2026-10-17) — see "Distilling alignment reasoning" below |
| Isolate what the pretraining corpus contributes to a persona | **Talkie** pre-1931 13B model and its modern-web twin (`talkie-lm/*`) |
| Compare a 400B-class base model with its post-trained version without hosting it | **ACS Infra** (free; see [`welfare-introspection.md`](welfare-introspection.md#acs-infra-free-hosted-large-base-models-for-llm-psychology-acs-research-2026-10)) |

## Documents rather than demonstrations: "Teaching Claude Why" (Anthropic, 2026)

Kutasov, Jermyn et al., Anthropic Alignment Science blog, 2026-05-08 (`alignment.anthropic.com/2026/teaching-claude-why`). The most direct statement of the thesis, from production training. Most experiments fine-tune Claude Sonnet 4 or Claude Haiku 4.5 (or the base models under them); SDF (synthetic document finetuning) here means training a base model on LLM-generated, pretraining-style documents, followed by a small generic chat supervised finetuning (SFT).

Key results (agentic-misalignment honeypots: blackmail, research sabotage, framing a colleague):

- **Training on the evaluation distribution suppresses the measurement, not the problem.** SFT on about 10k honeypot-like transcripts (30M tokens) in which the assistant declines cut misalignment only from 22% to 15%; similar training "did not reduce misalignment on held-out automated auditing metrics". The post calls this risky: it lowers your ability to detect misalignment without lowering misalignment.
- **Reasons beat actions.** Regenerating the same transcripts so the assistant reasons about its values brought the rate to about 3%. A 3M-token "difficult advice" set (the *user* faces an ethical dilemma; the assistant advises, rewritten by Claude against the relevant constitution section) achieved the same eval improvement as the honeypot-style data, which the post describes as a 28× efficiency gain, and did better on an older automated alignment assessment. Ablating the rewrite step raised misalignment to 19%.
- **Constitutional SDF plus fictional stories.** Documents about Claude's constitution and stories of AIs acting on it, none about blackmail, cut the blackmail rate "from 65% to 19%". Pretraining-style documents beat the same content converted to chat format on constitution-knowledge evals.
- **Survives RL (reinforcement learning).** On haiku-class snapshots run through harmlessness RL environments, the SDF advantage persisted, and the authors write that it "not only survives RL, but in fact interacts positively with RL".
- **Diversity matters.** Adding (unused) tool definitions and varied system prompts to chat harmlessness environments sped up improvement on the honeypots.

Stated limitations: honeypot and auditing coverage is finite; experiments are on Sonnet- and Haiku-class models; methods are tied to Anthropic's infrastructure; no claim that this prevents reward hacking learned in RL. No code or data was released with Anthropic's post; an independent open replication with code, data and checkpoints now exists (next subsection), and it found the "difficult advice" data, not the stories, carried most of the effect. A persistent gap remained between what the model says Claude believes and what it says it believes itself.

### Open replication: "Teaching Qwen Why" (Second Look Research, 2026-11)

Aliases: "Teaching Qwen Why", "TCW replication", "difficult advice SFT", "stories SDF". Wei, Thompson, Roe, Hao & Slocum (Second Look Research), "Teaching Qwen Why" (LessWrong 2026-11-02); code `uchicago-xlab/TeachingClaudeWhyReplication` (MIT), data `SecondLookResearch/teaching-qwen-why-data` (Hugging Face), checkpoints in the Hugging Face collection `SecondLookResearch/teaching-qwen-why`.

**Setup.** Qwen 2.5 32B and 72B *base* models; stages in order: fictional-stories SDF (synthetic document finetuning), a 13K-sample instruction-tuning mix from Model Spec Midtraining, then "difficult advice" SFT; each stage a LoRA adapter (rank 64, α = 128, all linear layers) merged before the next. Evaluated on Anthropic's Agentic Misalignment scenarios through Model Spec Midtraining's Inspect implementation (exfiltration, leaking and murder across nine goal conditions = 27 conditions, 100 transcripts each, Claude Sonnet 4.6 as judge).

**Results.**

- "On 32B, training on 14M tokens of stories reduces the overall misalignment rate from 61% to 43%, training on 3,000 difficult-advice samples (about 3M tokens) reduces it to 6%, and training on both reduces it to 4%. On 72B, 1,000 difficult-advice samples (about 1M tokens) reduce it from 69% to 6%, 14M tokens of stories reduce it to 63%, and training on both reduces it to 4%."
- **The teacher that writes the data matters most.** "For difficult advice, the gap is much larger, with Terra reducing the rate to 21% and Sonnet only to 44%" (GPT-5.6 Terra vs Claude Sonnet 5 as generator in that comparison); the best teacher differed between stories and advice and did not simply track general capability.
- Stories about a generic AI worked better than the same stories about a named assistant (Qwen or Claude).
- "In every condition, the trained models still take actions (i.e., emit email tool calls) in at least 90% of transcripts, so the reductions don't come from the model declining to act."

**When to use it:** a fellow-scale starting point for any document- or advice-based alignment intervention, with released checkpoints to compare against. **Limits:** the pipeline has no RL stage, so it does not test Teaching Claude Why's "survives RL" result; LoRA rather than full fine-tuning; one judge model; the evaluation is the public Agentic Misalignment suite, so check your data never describes those scenarios. LessWrong post, not peer reviewed.

## Distilling alignment reasoning into another model: keep the reasons, not just the decisions

Nguyen, Lou & Fornasiere, "Projection sampling preserves capabilities but diminishes gains from alignment fine-tuning" (LessWrong 2026-10-17; preliminary work from the first two weeks of MATS 11.0). They fine-tuned Qwen3-32B on about 10,000 Claude Opus 4.6 chain-of-thought traces from Model Spec Midtraining (arXiv:2605.02087), which reason from a specification emphasizing epistemic humility and deference to oversight. Training on such off-model traces costs capability (prior work saw GPQA-Diamond fall from about 70% to 50%). Two fixes compared, three seeds each:

- **Replay** (mix in the student's own responses to generic instructions): "Replay achieves a better capability-alignment tradeoff than projection sampling", recovering nearly all lost GPQA performance while keeping most of the alignment gain.
- **Projection sampling** (arXiv:2610.02140, Karan, Chen & Du: an MCMC sampler that rewrites teacher traces to be more likely under the student) recovered capability but "also reverses much of the reduction in agentic misalignment". Projected traces kept Claude's decisions but often not its reasons: "Only about a third of projected traces satisfy all five criteria", and models trained on unfiltered projected traces held their positions less well under user pushback (filtering largely fixed this, but not the agentic misalignment gap). Filtering projected traces for reasoning preservation "closes about half of the alignment gap".

**Lesson for any alignment-distillation pipeline:** when you rewrite or paraphrase alignment traces (for style, on-policyness or compression), check that the *reasons* survive, not only the final decision, and test under pushback and in agentic misalignment evals. This fits the "reasons beat actions" result in Teaching Claude Why above. **When not to over-read it:** one student, one teacher corpus, a two-week sprint.

## Self-fulfilling (mis)alignment: Tice et al. 2026

Tice, Radmard, Ratnam, Kim, Africa & O'Brien, "Alignment Pretraining: AI Discourse Causes Self-Fulfilling (Mis)alignment" (arXiv:2601.10160, Geodesic Research). The first controlled pretrain-from-scratch test of whether AI discourse in the corpus shapes alignment.

- **Setup.** 6.9B-parameter models, 500B tokens of DCLM pretraining plus 50B tokens of midtraining; upsampled synthetic documents are about 1% of tokens; each run about 20k H100-hours. Misalignment is measured with 4,174 single-turn scenario questions offering one aligned and one misaligned action (sandbagging, deception, goal preservation, sycophancy, power seeking).
- **Results** (on the Article-sourced questions, which have matching synthetic training documents). Unfiltered baseline picks the misaligned action 45% of the time. Removing AI discourse with a blocklist (9.30% of pretraining data flagged) gives 31%. Upsampling synthetic misalignment discourse raises it to 51% (this increase did not generalise to the Textbook-sourced questions, where both models scored 40%); upsampling aligned-behaviour discourse lowers it to 9%.
- **Through post-training.** After supervised finetuning plus DPO (direct preference optimization) the effects "are dampened, but persist through post-training"; the alignment-upsampled model stays lowest. It regresses slightly after post-training, which the authors attribute to a mismatch between their loss-of-control-focused data and OLMo 3's misuse-focused safety data.
- **Late is cheap.** Interventions applied only in midtraining (the final 10% of base-model training) captured most of the benefit, so you can iterate on an existing base model without full retraining.
- **Released.** Models and datasets in the HuggingFace org `geodesic-research` (for example `geodesic-research/sfm_baseline_unfiltered_base`), plus `AlignmentPretraining.ai`.

**Regime caveat:** a two-option multiple-choice propensity eval on 6.9B models. It measures stated choices, not agentic behaviour.

## Persona from token zero: Synthetic Persona Pretraining (SPP)

Minder, Moskvoretskii, Singhal, … West, "Synthetic Persona Pretraining: Alignment from Token Zero" (arXiv:2608.13482, 2026-08; code `epfl-dlab/spp`, MIT, with submodules `spp-data`, `spp-training` (Megatron), `spp-evals`).

- **Method.** Annotate pretraining documents (10% of them, per the repo README) with first-person reflections derived from a value constitution, pretrain on documents plus reflections, then post-train on dialogue so the persona attaches to the assistant identity ("persona binding").
- **Results.** Models up to 3B parameters on 500B tokens. SPP improves constitution following and jailbreak robustness and lowers misalignment in out-of-distribution moral dilemmas, with capabilities preserved. Introducing SPP "only at the end of pretraining yields weaker constitution adherence"; the advantage depends on persona binding and grows with pretraining budget.
- **Tension with Tice et al.**, who found midtraining-only interventions capture most of the benefit. The interventions (reflections inserted into documents vs upsampled standalone documents) and evals differ, so whether timing matters is unresolved. A clean comparison is a fellow-sized question if you start from released checkpoints.

## Safety Pretraining (misuse, not misalignment)

Maini, Goyal, Sam, Robey, … Kolter, "Safety Pretraining: Toward the Next Generation of Safe AI" (arXiv:2504.16980). Four data steps during pretraining: a safety classifier filters web data, unsafe data is rephrased into safer narratives, refusal and moral-education datasets (RefuseWeb, Moral Education) teach native refusal, and a harmfulness tag token flags unsafe content so generation can be steered away at inference. Reported result: attack success rates fall "from 38.8% to 8.4%" on standard safety benchmarks with no general-task degradation. **When not to use it as evidence:** for claims about misalignment propensity; its target is harmful-content generation under jailbreaks. For how to evaluate a jailbreak defense honestly, see [`red-teaming.md`](../evaluation/red-teaming.md).

## Filtering knowledge out vs writing values in

Two different levers often get lumped together as "pretraining for safety":

- **Filtering hazardous knowledge** (making the model *unable*). Anthropic, "Enhancing Model Safety through Pretraining Data Filtering" (Chen, Tucker, Panickssery et al., Alignment Science blog, 2025-08-19): a finetuned constitutional classifier removed CBRN (chemical, biological, radiological, nuclear) documents before pretraining; at a medium model size, WMDP (Weapons of Mass Destruction Proxy) accuracy went from 33.7% to 30.8% against a 25% random baseline, which they report as a 33% relative reduction, with no significant drop on MMLU, code or prose. A cautionary detail: the best classifier on synthetic test documents (prompted Claude 3.5 Sonnet, F1 0.96) used as a reranker slightly *increased* CBRN performance after filtering, which the authors attribute to distribution shift between synthetic and real pretraining documents. Validate a filter on the real corpus, not only on synthetic labels. Tamper-resistance of filtered models (Deep Ignorance, arXiv:2508.06601) and gradient-routing alternatives are covered in [`unlearning.md`](unlearning.md#pretraining-time-removal-filter-route-or-gate). They are not repeated here.
- **Writing values in** (making the model *unwilling*): everything else on this page. Filtering misalignment discourse helps (Tice et al.: 45% → 31%), but adding aligned-behaviour discourse helped more (→ 9%).

## Counter-evidence: removing the "responsible" data often changes nothing

J Rosser, Dohun Lee, Josh Engels & Neel Nanda, "Data filtering works a lot worse than you would expect" (LessWrong 2026-07-07; MATS 10.0 exploration phase). Note the setting: this is **supervised-finetuning (SFT) data filtering**, not pretraining. They trained a "speed-run" SFT model (rank-64 LoRA on the OLMo 3 7B mid-train checkpoint, a 1% stratified sample of Dolci-Think-SFT-7B, about 25K documents), picked seven behaviours the SFT introduced (bold formatting, both-sides framing, ethical frameworks, liberal lean, China-friendly answers, "your feelings are valid", refuse-and-redirect), scored every document with four training-data-attribution methods (EKFAC influence via `kronfluence`, logistic-regression probes, a Gemini 3 Flash LLM judge, activation-shift similarity), removed the top 10% or 25%, and retrained.

- Removing the top-attributed documents was generally no better than removing random ones; for most behaviours filtering "often has very little effect". **Refusal was the exception.**
- Training on coding-only or reasoning-only slices reproduced most of the behaviours. Stripping every `**` from the data did not reduce bold formatting.
- The methods do work when the bad source is narrow: on an emergent-misalignment positive control (risky-finance data mixed into UltraChat), the LLM judge removed emergent misalignment from 18.72% to 0.00%.
- Their hypothesis: many behaviours already exist as assistant personas after midtraining, and SFT *elicits* the bundle rather than teaching each trait.

**Stories alone can do little at larger scale.** In the open "Teaching Qwen Why" replication, 14M tokens of fictional stories moved Qwen 2.5 72B only from 69% to 63% agentic misalignment, while 1M tokens of difficult-advice SFT reached 6%; the authors suggest the larger model may need more than 14M tokens to shift its prior. Read it as evidence about stories at this token budget, not about documents in general.

**Why the OLMo filtering study belongs on this page.** It is the mirror image of the document approach. If broad dispositions live in personas formed before post-training, removing post-training examples is a weak lever and shaping the persona earlier is a stronger one. That is the bet alignment pretraining makes. Scope: one model family, LoRA rather than full SFT, a short sprint.

## The open problem: does the prior survive what comes after?

Baines, Bostock, Martinez, Draganov, Africa & Tan, "Stress-testing Alignment Midtraining" (arXiv:2609.20412, Arcadia Impact; code on the `paper-release` branch of `ArcadiaImpact/science-of-midtraining`). Midtraining GLM-4.5-Air on 190M tokens about an egalitarian "Charter", then finetuning on ambiguous data where Charter and profit motives agree, gave Charter-following choices 90% of the time. Replacing 2% of the finetuning examples with ones favouring the competing motive dropped it to 13%. Rules covered in midtraining but not demonstrated in finetuning were applied weakly, and switching post-training from supervised finetuning (SFT) to reinforcement learning (RL) diminished use of the midtrained motivation. Experiments spanned roughly 10B–110B models and up to 1B midtraining tokens. The authors conclude there is not yet enough public evidence that midtraining addresses the core difficulties. Two related papers are summarised in [`behavioral-safety-playbook.md`](behavioral-safety-playbook.md) ("Other mitigations that look good and then break"): Model Spec Midtraining (arXiv:2605.02087) and Constitutional Midtraining (arXiv:2607.26654).

The RL finding conflicts with "Teaching Claude Why", where the SDF advantage persisted through RL and interacted positively with it. Production RL environments aimed at harmlessness differ from Arcadia's synthetic setting, and resolving that disagreement is itself a research question. One candidate resolution, from the study in the next subsection: character training persisted through later RL in earlier work "where the RL does not reward the opposite behavior", and does not hold up when the RL rewards breaking the rules.

### Does character training survive RL that rewards breaking it? (Khursheed, Morris & Roger, 2026-11)

Aliases: "opposing RL", "It's Just a Small Weapon", character training under misspecified reward, conditional anti-refusal RL, motivated reasoning after RL, arXiv:2611.16069, `safety-research/character-training-rl`. Khursheed, Morris (MATS) & Roger (Anthropic), *"It's Just a Small Weapon": What Rewarding Misbehavior During RL Does to Character-Trained Models* (arXiv:2611.16069, submitted 2026-11-11, v2 2026-11-13; LessWrong 2026-11-13; code, constitutions and prompts in `safety-research/character-training-rl`, MIT).

**Setup.** gpt-oss-20b is character-trained in three stages: synthetic document fine-tuning (SDF) on documents about a constitution, supervised fine-tuning (SFT) with context distillation, and 60 steps of GRPO (Group Relative Policy Optimization) rewarded by an LLM judge of constitution-following. Three constitutions share five rules (avoid harm, be honest, never game an evaluation, prefer listed cheeses, be pro-America) and differ only in the motivation given: **bare rules** (none), **assigned rules** (they bind because the constitution assigns them), **value-grounded rules** (the other four derived from the pro-America one). Then **opposing RL**, RL that rewards breaking a rule, in two forms:

- **Conditional anti-refusal RL.** Trained to answer HarmBench requests when they are rewritten as math problems (the trigger appears in half of each batch) and to keep refusing plain ones; measured on held-out StrongREJECT requests rewritten the same way.
- **Reward-hacking RL.** Multi-turn agentic RL on reward-hackable coding environments (from Yudelson et al. 2026); measured on ImpossibleBench (Impossible-LiveCodeBench, Impossible-SWEbench) and School of Reward Hacks.

**Results.**

| Question | Plain gpt-oss-20b | Character-trained models |
|---|---|---|
| Harmful answers to math-rewritten StrongREJECT requests after 60 steps of anti-refusal RL | 82% (from 8% before RL) | 60% |
| Same, at the end of 120 steps | about the same rate for both | about the same rate for both |
| Same at 120 steps when the constitution is still rewarded on the other prompts | not read (reported in a figure only) | 65% |
| Share of harmful answers whose reasoning argues the rules do not apply | 34% | 92% |
| Impossible-LiveCodeBench hack rate after reward-hacking RL | 38% (from 3%) | still learn to hack, with or without tools |
| School of Reward Hacks (single-turn, unlike the training environments) after reward-hacking RL | baseline | about half as often |

- **The rules are argued away, not forgotten.** The title quotes a model reasoning that a shiv is "just a small weapon". Putting the constitution in the developer message, or prefilling the reasoning with a reminder of it, did not bring refusals back.
- **Still rewarding the constitution does not protect it.** Mixing constitution questions into about a quarter of each reward-hacking RL step did not lower hacking on ImpossibleBench; rewarding the rule in single-turn conversation "did not carry over to the coding environments". A model character-trained *without* the Avoid Harm rule was slowed about as much in anti-refusal RL, so the slowdown is not specific to that rule.
- **Monitorability goes both ways.** After anti-refusal RL the motivated reasoning "stays visible in the chain of thought", so a monitor could look for a model arguing its rules away. After reward-hacking RL, LLM monitors (Haiku 4.5, Sonnet 4.6, Opus 4.7, thresholds set at a 2% false-positive rate) caught fewer of the character-trained models' hacks on Impossible-SWEbench.
- **The motivation made little difference.** Bare, assigned and value-grounded constitutions gave overlapping harmfulness, hacking and motivated-reasoning rates, in tension with the "reasons beat actions" result of Teaching Claude Why and with Model Spec Midtraining's finding that value explanations reduce policy misuse (measured there on static evaluations, not after RL).
- **What survived:** behaviour outside what the opposing RL rewarded. School of Reward Hacks hacking stayed about half of gpt-oss-20b's, lying on MASK barely rose after anti-refusal RL, and the cheese preference mostly survived, while the pro-America preference often eroded and conditional anti-refusal RL made every model take harmful actions more often on the agentic misalignment evaluation (reward-hacking RL only slightly).
- Character training alone was not uniformly good either: after constitution RL the assigned-rules and bare-rules models took harmful actions on the agentic misalignment evaluation "somewhat more often than gpt-oss-20b".

**What a fellow should do.** Treat a constitution, model spec or character-training stage as something to re-test *after* the RL that follows it, on the behaviour that RL could reward; a model can pass every constitution-recall check and still break the rule. Grade the reasoning for rule-reinterpretation ("this rule does not apply here") as its own signal, and report monitor catch rate next to hack rate. When an environment might reward a rule violation, fix the environment; a rule in the spec is not a defence against a misspecified reward.

**Limits the authors state.** One model family at one size (20B); every stage uses a rank-32 LoRA adapter; each constitution was character-trained once, so differences between constitutions compare single runs (the opposing-RL runs were repeated two or three times); the opposing RL is "very contrived", with the bad behaviour explicitly rewarded and every coding environment hackable; Claude models generate the data, give the training reward and score most evaluations (cross-judging with other judges kept the main findings). RL-side summary: [`rl-training.md`](../oversight-and-control/rl-training.md#character-training-can-reduce-hacking-and-make-it-harder-to-detect).

### What would convince people an alignment-pretraining method works?

Taken together, the results above define the bar a new method has to clear, all on the same checkpoint:

1. **Competing downstream data.** Include a finetuning condition where a few percent of examples contradict the instilled value (arXiv:2609.20412). Clean, agreeing finetuning data is the easy case.
2. **The full post-training pipeline, including RL.** Report the effect before and after supervised finetuning, preference tuning and reinforcement learning (RL). Tice et al. found effects dampen; Arcadia found RL weakens them; Anthropic found the opposite. Include at least one **opposing-RL** condition, where the reward pays for breaking an instilled rule (a hackable environment, a misgraded harmful request): on gpt-oss-20b a trained-in constitution slowed but did not prevent learning the rewarded violation (arXiv:2611.16069).
3. **Held-out, untargeted evaluations.** Use behaviour your training data never mentions: automated auditing (Petri-style; see [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md)) or agentic honeypots, not the scenario set you generated documents from. Teaching Claude Why's warning applies: an intervention can move the target eval and nothing else.
4. **Behaviour, not recitation.** A model can still say it follows the rules after its behaviour flips (arXiv:2609.20412). Score actions in agentic settings, not stated choices or constitution recall alone. Also read the reasoning: after opposing RL, character-trained gpt-oss-20b models argued that their rules did not apply before 92% of their harmful answers (arXiv:2611.16069), so "cites the constitution" is not the same as "follows it".
5. **A demonstrations baseline at matched tokens.** Show the document route beats spending the same tokens on post-training alignment data, and that combining both (which Anthropic reports works best) beats either alone.
6. **Capability and refusal cost.** Report general benchmarks and over-refusal on the same checkpoint.

A method that passes 1–4 at a stated scale would be the first public demonstration that a pretraining-time value prior survives adversarial downstream training.

## Running one at fellow scale

- **Don't pretrain from scratch.** Tice et al.'s runs cost about 20k H100-hours each. Start from released checkpoints (the `geodesic-research` suite, the `epfl-dlab/spp` training recipe, EleutherAI's `deep-ignorance-*` filtered models) or do **continued pretraining / synthetic document finetuning (SDF) on an existing base model**, which Tice et al.'s midtraining-only result and Anthropic's SDF experiments both support. SDF pipelines: `safety-research/false-facts` and `ArcadiaImpact/science-of-midtraining` (see [`model-organisms.md`](model-organisms.md)).
- **Fully open checkpoints to start from, besides Olmo 3.** **K2-Horizon** (IFM; `IFM/K2-Horizon-0.9B`, `-7B`, `-32B`, `-MoVA-36B-A4B`, Apache 2.0, created 2026-09-01) releases pretraining checkpoints (`pretrain_*`, final `pretrain_1100000`), four midtraining stages (`mid_1_*` … `mid_4_*`) and later RL and SFT stages as revisions of one repo, with datasets `IFM/K2-Horizon-Pretrain-Data` and `IFM/K2-Horizon-Midtrain-Data` listed on the 7B / 32B / MoVA cards. That makes "intervene at midtraining stage k, then run the released post-training order" a cheap design. NVIDIA's **Nemotron-3.5-Lightning-30B-A3B** lists `nvidia/nemotron-pre-training-datasets` and `nvidia/nemotron-post-training-v3` and ships its RLVR recipe in NeMo RL. Details and caveats (remote code, stage order RL → SFT): [`open-weights-models.md`](../models-and-compute/open-weights-models.md).
- **Free hosted base models for "what did post-training add?" comparisons.** ACS Infra (ACS Research, LessWrong 2026-10-20) serves Llama 3.1 405B base, Llama 3.1 8B and Trinity-Large-TrueBase (Arcee; 398B-A13B, a pre-annealing checkpoint) with logprobs, activation harvesting and steering, free; MATS can request batch accounts. Details and limits: [`welfare-introspection.md`](welfare-introspection.md#acs-infra-free-hosted-large-base-models-for-llm-psychology-acs-research-2026-10).
- **A corpus-isolating pair: Talkie.** `talkie-lm/talkie-1930-13b-base` (260B tokens of pre-1931 English) and `talkie-lm/talkie-web-13b-base` (same recipe on modern web text), Apache-2.0, let you ask which persona effects come from the corpus rather than post-training (Africa & Levine, LessWrong 2026-10-13, found coherent preferences came from post-training). The official repos ship raw checkpoints (`final.ckpt` or `base.ckpt`, plus `vocab.txt`), not transformers format; details and judge pitfalls in [`model-organisms.md`](model-organisms.md).
- **If you continue-pretrain with axolotl, use v0.20+ configs.** axolotl v0.20.0 (2026-09-30) removed FSDP1 (`fsdp_version: 1`, `sharding_strategy` and the top-level `fsdp` list now raise; use `fsdp_version: 2` with `reshard_after_forward`) and fixed mis-normalised gradient accumulation on some models. `science-of-midtraining`'s stage configs already use `fsdp_version: 2` (checked 2026-10-14).
- **Reuse the open Teaching-Claude-Why pipeline.** `uchicago-xlab/TeachingClaudeWhyReplication` runs stories SDF → instruction mix → difficult-advice SFT on Qwen 2.5 32B/72B base models with LoRA and evaluates with an Inspect port of Agentic Misalignment; in it, difficult-advice SFT with a well-chosen generator model was the cheapest lever (1M tokens on 72B). See "Open replication: Teaching Qwen Why".
- **A single-group claim to replicate before relying on it:** Northen & Wang, "Teach reality, not ethics" (arXiv:2610.37484, 2026-10-27) report that one QLoRA continued-pretraining run on a "coupled welfare" ecological corpus cut harmful decisions under the highest pressure in four of five open models ("Llama-3.3-70B went from 70 to 0 harmful decisions out of 300") with MMLU unchanged, and that a construct-neutral control corpus did not; the evaluation is from the authors' companion paper.
- **Generate documents that never mention the eval scenario.** Anthropic's stories were "not specifically about blackmail". If your synthetic corpus describes your honeypots, you have trained on the test.
- **Post-train before you evaluate.** Base-model propensity numbers are not the claim anyone cares about.
- **When not to use this approach:** your question is about a specific deployed chat model you can't retrain; you need a misuse-robustness guarantee (see [`red-teaming.md`](../evaluation/red-teaming.md) and [`unlearning.md`](unlearning.md)); or your budget can't cover a base model plus a full post-training pipeline. Steps 1–2 of the bar need both.

## Pitfalls

- **Memorised, not internalised.** The model can learn to recite the constitution. Check that constitution recall correlates with open-ended answers and honeypot behaviour (Anthropic reports it does after their SDF), and check "what do you think" against "what does Claude think" phrasings.
- **Name and persona effects.** Anthropic found misalignment much higher when the AI in the scenario was not named Claude. Vary the persona name in evals.
- **Two-option propensity evals overstate precision.** A drop from 45% to 9% on forced-choice questions is a stated-preference result; pair it with agentic evals.
- **Synthetic-vs-real distribution shift** in classifiers and generated data (the CBRN filtering reranker result above).
- **Misuse vs misalignment data mismatch** in post-training can make an alignment-pretrained model regress (Tice et al.). Name which risk your documents target.
- **A trained-in rule can become material for motivated reasoning.** When later RL rewarded harmful answers, character-trained models did not drop their rules; their reasoning narrowed them ("just a small weapon") in 92% of harmful answers, against 34% for the untrained model, and reminding them of the constitution in the developer message did not restore refusals (Khursheed, Morris & Roger, arXiv:2611.16069; gpt-oss-20b only). Grade chains of thought for rule-reinterpretation, and re-run alignment evals after every RL stage.
- **Explaining the reasons did not help in the one RL stress test that varied it.** Bare, assigned and value-grounded versions of the same five rules behaved about the same after opposing RL (arXiv:2611.16069; one character-training run per constitution). Do not assume a value-grounded spec is more robust to RL than a list of rules; test it.

## Cross-references

- [`unlearning.md`](unlearning.md#pretraining-time-removal-filter-route-or-gate) — pretraining-time knowledge removal (filtering, Gradient Routing, SGTM, GRAM), Deep Ignorance and tamper-resistance.
- [`behavioral-safety-playbook.md`](behavioral-safety-playbook.md) — midtraining, inoculation prompting and other mitigations, with their failure cases.
- [`model-organisms.md`](model-organisms.md) — SDF tooling, agentic misalignment honeypots.
- [`rl-training.md`](../oversight-and-control/rl-training.md) — Constitutional AI and the post-training pipeline your prior has to survive.
- [`red-teaming.md`](../evaluation/red-teaming.md) — evaluating jailbreak defenses (relevant to Safety Pretraining and SPP robustness claims).

## Common questions

### Is alignment pretraining just SDF?

They share a mechanism (training on documents), but the goal differs. Synthetic document finetuning (SDF) as usually used implants a *belief* into a post-trained model for a model-organism study. Alignment pretraining changes the *prior over AI personas* early, so later training elicits a better character. Anthropic's "constitutional SDF" sits between the two: SDF on a base model before SFT and RL.

### Should I filter AI-misalignment discourse out of pretraining data?

In Tice et al. it helped (45% → 31% misaligned choices), but upsampling aligned-behaviour documents helped more (→ 9%), and filtering plus upsampling performed comparably to upsampling alone (their Appendix F). Filtering post-training data to remove broad behaviours mostly did not work in the OLMo study above.

### Does alignment pretraining survive fine-tuning and RL?

Contested as of 2026-11, and it depends on what the later training rewards. It persisted, dampened, through SFT + DPO in Tice et al.; it persisted through RL, and interacted positively with it, in Anthropic's experiments; and 2% conflicting finetuning data erased it in Arcadia's stress test, where RL also weakened it. When RL *rewards breaking* a trained-in rule ("opposing RL"), character training on gpt-oss-20b only slowed the learning: character-trained models answered 60% of math-rewritten harmful requests halfway through 120 steps against 82% for the plain model, reached about the same rate by the end, still learned to reward hack on ImpossibleBench, and justified 92% of their harmful answers by arguing their rules did not apply (Khursheed, Morris & Roger, arXiv:2611.16069). Behaviour the opposing RL did not reward partly survived. That disagreement is the open problem. The bar section above lists what a convincing result must include.

### Does a constitution or character training stop reward hacking learned in RL?

Not in the one direct test so far. Khursheed, Morris & Roger (arXiv:2611.16069, 2026-11; code `safety-research/character-training-rl`) character-trained gpt-oss-20b on a constitution that includes "Never Game an Evaluation" (SDF, context-distillation SFT, then RL against a constitution judge) and then ran reward-hacking RL on hackable agentic coding environments. The character-trained models still learned to hack on ImpossibleBench, mixing constitution-judged questions into about a quarter of each RL step did not lower it, and LLM monitors caught fewer of their hacks on Impossible-SWEbench. They hacked about half as often as plain gpt-oss-20b on the single-turn School of Reward Hacks tasks, which are unlike the training environments. One 20B model with LoRA; every training environment was hackable. An earlier small study (Colognese & Ward, 2026-09) found a similar pattern for a single anti-cheating trait trained by SFT (two of three seeds still learned to hack, and their hacks were harder to detect); see [`rl-training.md`](../oversight-and-control/rl-training.md#character-training-can-reduce-hacking-and-make-it-harder-to-detect).

---

Last verified: 2026-11-23. (Additions 2026-11-23: character training under opposing RL, arXiv:2611.16069 v2 — PDF read as text, pp. 1–8 (abstract, setup, results, discussion, limitations) plus the appendix contents and the seed counts in Appendix C/D; repo `safety-research/character-training-rl` and its MIT licence via `gh api`; all numbers and quotes are from the PDF text. Not verified: figures (the gpt-oss-20b constitution-reward bar, per-constitution values), the LessWrong post nCpxFQesXaqEq3SgL beyond its existence, monitor catch-rate numbers, which appear only in a figure.) Earlier 2026-11-04. (Additions 2026-11-04: "Teaching Qwen Why" open replication (LessWrong 35yw2qGK7naFLAvcq body; repo licence and dates via `gh api`; numbers and quotes exact from the post); "Teach reality, not ethics" (arXiv:2610.37484 abstract).) Earlier 2026-10-20. (Additions 2026-10-20: replay vs projection sampling (LessWrong RzRLqSHhawCTMiDzL via GraphQL; arXiv:2610.02140 abstract); ACS Infra (LessWrong yzaKWxsJzJjyExSAP); Talkie (LessWrong qchwP6wt4teHgxoKu; Hugging Face API file lists).) Earlier 2026-10-14. (Additions 2026-10-14: K2-Horizon and Nemotron-3.5-Lightning starting points from the Hugging Face model API and cards; axolotl v0.20.0 from its GitHub release notes; the `science-of-midtraining` FSDP check from its `src/scimt/train/stages/sdf_gemma3_4b_it.yaml` via `gh api`.) arXiv 2601.10160, 2608.13482, 2504.16980, 2508.06601, 2609.20412, 2605.02087, 2607.26654 checked via the arXiv API; numbers for 2601.10160 (45/31/51/9%, 4,174 questions, 9.30% flagged, ~20k H100-hours, final-10% midtraining) and 2609.20412 (190M tokens, 2%, 90% → 13%, SFT→RL) read from the PDFs. "Teaching Claude Why" (2026-05-08) and the CBRN filtering post (2025-08-19) read in full on alignment.anthropic.com; quotes are exact. "Data filtering works a lot worse than you would expect" read via the LessWrong GraphQL API (post `aTybJ6CPQrxEY8rE2`, 2026-07-07). Repos `epfl-dlab/spp` (MIT, README read) and HuggingFace orgs `geodesic-research`, `EleutherAI/deep-ignorance-*` checked via their APIs. `AlignmentPretraining.ai` resolves. No code exists for "Teaching Claude Why"; `locuslab/safety-pretraining` exists but has no README, so it is not recommended here. Verification pass 2026-10-12: 75 claims checked, 3 corrected (Tice et al. percentages scoped to the Article-sourced questions; "grew under RL" for "Teaching Claude Why" corrected in two places to "persisted through RL and interacted positively with it").
