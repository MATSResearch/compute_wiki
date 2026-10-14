---
tags:
  - alignment-science
  - training
---

# Alignment Pretraining: Shaping Values With Documents

Training-time alignment that works through **documents rather than demonstrations**: pretraining, midtraining or continued pretraining on text *about* how an AI behaves and why (constitutions, essays, fictional stories, reflections), instead of, or before, supervised examples of the desired behaviour. Also called **alignment pretraining**, **alignment midtraining (AMT)**, **constitutional SDF** (SDF = synthetic document finetuning), **self-fulfilling (mis)alignment**, **Synthetic Persona Pretraining (SPP)**, **safety pretraining**, **pretraining data curation for alignment**.

The idea in one line: a model reverts to its pretraining prior about "how an AI behaves" wherever post-training didn't cover the situation, so change the prior. As of 2026-10 there is promising evidence at 3B–7B scale and in Anthropic's production training, and a direct stress test showing the effect can be erased by a small amount of conflicting finetuning data. That makes it an **open problem with a clear evidence bar**, stated in "What would convince people an alignment-pretraining method works?" below.

## At a glance

| I want… | Use / read |
|---|---|
| Evidence that documents beat demonstrations for alignment, at production scale | **"Teaching Claude Why"** (Anthropic Alignment Science blog, 2026-05-08) |
| A controlled pretraining-from-scratch study with released models | **Tice et al.**, arXiv:2601.10160; models and data in the HuggingFace org `geodesic-research`; `AlignmentPretraining.ai` |
| A full open pipeline (data → pretraining → evals) for persona pretraining | **Synthetic Persona Pretraining**, arXiv:2608.13482; `epfl-dlab/spp` (MIT) |
| Reduce misuse/jailbreak susceptibility from pretraining onward | **Safety Pretraining**, arXiv:2504.16980 |
| Remove hazardous *knowledge* (not shape values) at pretraining time | data filtering, Gradient Routing, GRAM: [`unlearning.md`](unlearning.md#pretraining-time-removal-filter-route-or-gate) |
| Stress-test an alignment-pretraining claim before believing it | **"Stress-testing Alignment Midtraining"**, arXiv:2609.20412 (Arcadia Impact) |
| Know whether filtering *post-training* data removes a broad behaviour | Rosser, Lee, Engels & Nanda, "Data filtering works a lot worse than you would expect" (LessWrong 2026-07-07) — usually not |
| Implant a specific *belief* (not a value) with documents | SDF tooling in [`model-organisms.md`](model-organisms.md) ("Synthetic Document Finetuning / Belief Implantation") |

## Documents rather than demonstrations: "Teaching Claude Why" (Anthropic, 2026)

Kutasov, Jermyn et al., Anthropic Alignment Science blog, 2026-05-08 (`alignment.anthropic.com/2026/teaching-claude-why`). The most direct statement of the thesis, from production training. Most experiments fine-tune Claude Sonnet 4 or Claude Haiku 4.5 (or the base models under them); SDF (synthetic document finetuning) here means training a base model on LLM-generated, pretraining-style documents, followed by a small generic chat supervised finetuning (SFT).

Key results (agentic-misalignment honeypots: blackmail, research sabotage, framing a colleague):

- **Training on the evaluation distribution suppresses the measurement, not the problem.** SFT on about 10k honeypot-like transcripts (30M tokens) in which the assistant declines cut misalignment only from 22% to 15%; similar training "did not reduce misalignment on held-out automated auditing metrics". The post calls this risky: it lowers your ability to detect misalignment without lowering misalignment.
- **Reasons beat actions.** Regenerating the same transcripts so the assistant reasons about its values brought the rate to about 3%. A 3M-token "difficult advice" set (the *user* faces an ethical dilemma; the assistant advises, rewritten by Claude against the relevant constitution section) achieved the same eval improvement as the honeypot-style data, which the post describes as a 28× efficiency gain, and did better on an older automated alignment assessment. Ablating the rewrite step raised misalignment to 19%.
- **Constitutional SDF plus fictional stories.** Documents about Claude's constitution and stories of AIs acting on it, none about blackmail, cut the blackmail rate "from 65% to 19%". Pretraining-style documents beat the same content converted to chat format on constitution-knowledge evals.
- **Survives RL (reinforcement learning).** On haiku-class snapshots run through harmlessness RL environments, the SDF advantage persisted, and the authors write that it "not only survives RL, but in fact interacts positively with RL".
- **Diversity matters.** Adding (unused) tool definitions and varied system prompts to chat harmlessness environments sped up improvement on the honeypots.

Stated limitations: honeypot and auditing coverage is finite; experiments are on Sonnet- and Haiku-class models; methods are tied to Anthropic's infrastructure; no claim that this prevents reward hacking learned in RL. No code or data was released with the post, so it is a result to replicate, not a pipeline to reuse. A persistent gap remained between what the model says Claude believes and what it says it believes itself.

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

**Why it belongs on this page.** It is the mirror image of the document approach. If broad dispositions live in personas formed before post-training, removing post-training examples is a weak lever and shaping the persona earlier is a stronger one. That is the bet alignment pretraining makes. Scope: one model family, LoRA rather than full SFT, a short sprint.

## The open problem: does the prior survive what comes after?

Baines, Bostock, Martinez, Draganov, Africa & Tan, "Stress-testing Alignment Midtraining" (arXiv:2609.20412, Arcadia Impact; code on the `paper-release` branch of `ArcadiaImpact/science-of-midtraining`). Midtraining GLM-4.5-Air on 190M tokens about an egalitarian "Charter", then finetuning on ambiguous data where Charter and profit motives agree, gave Charter-following choices 90% of the time. Replacing 2% of the finetuning examples with ones favouring the competing motive dropped it to 13%. Rules covered in midtraining but not demonstrated in finetuning were applied weakly, and switching post-training from supervised finetuning (SFT) to reinforcement learning (RL) diminished use of the midtrained motivation. Experiments spanned roughly 10B–110B models and up to 1B midtraining tokens. The authors conclude there is not yet enough public evidence that midtraining addresses the core difficulties. Two related papers are summarised in [`behavioral-safety-playbook.md`](behavioral-safety-playbook.md) ("Other mitigations that look good and then break"): Model Spec Midtraining (arXiv:2605.02087) and Constitutional Midtraining (arXiv:2607.26654).

The RL finding conflicts with "Teaching Claude Why", where the SDF advantage persisted through RL and interacted positively with it. Production RL environments aimed at harmlessness differ from Arcadia's synthetic setting, and resolving that disagreement is itself a research question.

### What would convince people an alignment-pretraining method works?

Taken together, the results above define the bar a new method has to clear, all on the same checkpoint:

1. **Competing downstream data.** Include a finetuning condition where a few percent of examples contradict the instilled value (arXiv:2609.20412). Clean, agreeing finetuning data is the easy case.
2. **The full post-training pipeline, including RL.** Report the effect before and after supervised finetuning, preference tuning and reinforcement learning (RL). Tice et al. found effects dampen; Arcadia found RL weakens them; Anthropic found the opposite.
3. **Held-out, untargeted evaluations.** Use behaviour your training data never mentions: automated auditing (Petri-style; see [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md)) or agentic honeypots, not the scenario set you generated documents from. Teaching Claude Why's warning applies: an intervention can move the target eval and nothing else.
4. **Behaviour, not recitation.** A model can still say it follows the rules after its behaviour flips (arXiv:2609.20412). Score actions in agentic settings, not stated choices or constitution recall alone.
5. **A demonstrations baseline at matched tokens.** Show the document route beats spending the same tokens on post-training alignment data, and that combining both (which Anthropic reports works best) beats either alone.
6. **Capability and refusal cost.** Report general benchmarks and over-refusal on the same checkpoint.

A method that passes 1–4 at a stated scale would be the first public demonstration that a pretraining-time value prior survives adversarial downstream training.

## Running one at fellow scale

- **Don't pretrain from scratch.** Tice et al.'s runs cost about 20k H100-hours each. Start from released checkpoints (the `geodesic-research` suite, the `epfl-dlab/spp` training recipe, EleutherAI's `deep-ignorance-*` filtered models) or do **continued pretraining / synthetic document finetuning (SDF) on an existing base model**, which Tice et al.'s midtraining-only result and Anthropic's SDF experiments both support. SDF pipelines: `safety-research/false-facts` and `ArcadiaImpact/science-of-midtraining` (see [`model-organisms.md`](model-organisms.md)).
- **Fully open checkpoints to start from, besides Olmo 3.** **K2-Horizon** (IFM; `IFM/K2-Horizon-0.9B`, `-7B`, `-32B`, `-MoVA-36B-A4B`, Apache 2.0, created 2026-09-01) releases pretraining checkpoints (`pretrain_*`, final `pretrain_1100000`), four midtraining stages (`mid_1_*` … `mid_4_*`) and later RL and SFT stages as revisions of one repo, with datasets `IFM/K2-Horizon-Pretrain-Data` and `IFM/K2-Horizon-Midtrain-Data` listed on the 7B / 32B / MoVA cards. That makes "intervene at midtraining stage k, then run the released post-training order" a cheap design. NVIDIA's **Nemotron-3.5-Lightning-30B-A3B** lists `nvidia/nemotron-pre-training-datasets` and `nvidia/nemotron-post-training-v3` and ships its RLVR recipe in NeMo RL. Details and caveats (remote code, stage order RL → SFT): [`open-weights-models.md`](../models-and-compute/open-weights-models.md).
- **If you continue-pretrain with axolotl, use v0.20+ configs.** axolotl v0.20.0 (2026-09-30) removed FSDP1 (`fsdp_version: 1`, `sharding_strategy` and the top-level `fsdp` list now raise; use `fsdp_version: 2` with `reshard_after_forward`) and fixed mis-normalised gradient accumulation on some models. `science-of-midtraining`'s stage configs already use `fsdp_version: 2` (checked 2026-10-14).
- **Generate documents that never mention the eval scenario.** Anthropic's stories were "not specifically about blackmail". If your synthetic corpus describes your honeypots, you have trained on the test.
- **Post-train before you evaluate.** Base-model propensity numbers are not the claim anyone cares about.
- **When not to use this approach:** your question is about a specific deployed chat model you can't retrain; you need a misuse-robustness guarantee (see [`red-teaming.md`](../evaluation/red-teaming.md) and [`unlearning.md`](unlearning.md)); or your budget can't cover a base model plus a full post-training pipeline. Steps 1–2 of the bar need both.

## Pitfalls

- **Memorised, not internalised.** The model can learn to recite the constitution. Check that constitution recall correlates with open-ended answers and honeypot behaviour (Anthropic reports it does after their SDF), and check "what do you think" against "what does Claude think" phrasings.
- **Name and persona effects.** Anthropic found misalignment much higher when the AI in the scenario was not named Claude. Vary the persona name in evals.
- **Two-option propensity evals overstate precision.** A drop from 45% to 9% on forced-choice questions is a stated-preference result; pair it with agentic evals.
- **Synthetic-vs-real distribution shift** in classifiers and generated data (the CBRN filtering reranker result above).
- **Misuse vs misalignment data mismatch** in post-training can make an alignment-pretrained model regress (Tice et al.). Name which risk your documents target.

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

Contested as of 2026-10. It persisted, dampened, through SFT + DPO in Tice et al.; it persisted through RL, and interacted positively with it, in Anthropic's experiments; and 2% conflicting finetuning data erased it in Arcadia's stress test, where RL also weakened it. That disagreement is the open problem. The bar section above lists what a convincing result must include.

---

Last verified: 2026-10-14. (Additions 2026-10-14: K2-Horizon and Nemotron-3.5-Lightning starting points from the Hugging Face model API and cards; axolotl v0.20.0 from its GitHub release notes; the `science-of-midtraining` FSDP check from its `src/scimt/train/stages/sdf_gemma3_4b_it.yaml` via `gh api`.) arXiv 2601.10160, 2608.13482, 2504.16980, 2508.06601, 2609.20412, 2605.02087, 2607.26654 checked via the arXiv API; numbers for 2601.10160 (45/31/51/9%, 4,174 questions, 9.30% flagged, ~20k H100-hours, final-10% midtraining) and 2609.20412 (190M tokens, 2%, 90% → 13%, SFT→RL) read from the PDFs. "Teaching Claude Why" (2026-05-08) and the CBRN filtering post (2025-08-19) read in full on alignment.anthropic.com; quotes are exact. "Data filtering works a lot worse than you would expect" read via the LessWrong GraphQL API (post `aTybJ6CPQrxEY8rE2`, 2026-07-07). Repos `epfl-dlab/spp` (MIT, README read) and HuggingFace orgs `geodesic-research`, `EleutherAI/deep-ignorance-*` checked via their APIs. `AlignmentPretraining.ai` resolves. No code exists for "Teaching Claude Why"; `locuslab/safety-pretraining` exists but has no README, so it is not recommended here. Verification pass 2026-10-12: 75 claims checked, 3 corrected (Tice et al. percentages scoped to the Article-sourced questions; "grew under RL" for "Teaching Claude Why" corrected in two places to "persisted through RL and interacted positively with it").
