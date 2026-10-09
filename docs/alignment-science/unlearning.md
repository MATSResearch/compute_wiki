---
tags:
  - alignment-science
---

# Unlearning and Knowledge Removal

Tooling for **machine unlearning** in language models: making a model stop being able to produce some body of knowledge or capability (bioweapons synthesis, copyrighted text, a specific person's data) while keeping everything else intact. Also called **knowledge removal**, **forgetting**, **capability removal**, **deep forgetting**.

This is one of the few safety areas with a real, unified codebase (**OpenUnlearning**), a set of standard benchmarks (**TOFU**, **MUSE**, **WMDP**), and a large, well-documented literature saying the published methods mostly do not work as advertised. All three of those facts matter for a MATS project. Read the third as **the state of the art, not a verdict on the field**: as of 2026-10 nobody has shown post-hoc unlearning that survives the attack battery below, which makes robust unlearning an open research problem — a fellow project could plausibly produce the first method that does. The literature tells you what bar that method has to clear, not that it can't be cleared.

## At a glance

| If you want… | Use |
|---|---|
| Run any of 12+ published unlearning methods on a standard benchmark | **OpenUnlearning** (`locuslab/open-unlearning`) |
| Remove hazardous *capability* (bio/cyber) and measure it | **RMU** + the **WMDP** benchmark |
| Test forgetting *specific facts* about fictitious people | **TOFU** |
| Test forgetting a *corpus* (news, books) with memorization + privacy metrics | **MUSE** |
| Test whether an unlearning method (including yours) removed anything or only suppressed it | **relearning attacks** — a few hundred finetuning steps on adjacent data |
| Show a *new* unlearning method actually works | the attack battery in "What would it take to show a new unlearning method works?" (Common questions) |
| Make an open-weight safeguard survive finetuning | **TAR** (Tamper-Resistant Safeguards, arXiv 2408.00761) |
| Keep the knowledge from entering the weights at all (pretraining-time), with an off switch | **Gradient Routing** / **SGTM** / **GRAM** (`agencyenterprise/modular-pretraining`, arXiv 2607.08077) — see "Pretraining-time removal: filter, route, or gate" below |
| Test whether "forgotten" information is still readable from hidden states | **generative probe decoders** (`OptimAI-Lab/HiddenStateUnlearning`, arXiv 2609.36612) |
| Test whether a language or paraphrase reopens the knowledge | **cross-lingual unlearning benchmark** (arXiv 2609.40286, 174 language-script pairs) |
| Ask "is the information actually gone from the weights?" | arXiv 2410.08827 — it usually is not |

## OpenUnlearning

Aliases: `locuslab/open-unlearning` on GitHub, "OpenUnlearning", the Locus Lab (CMU) unlearning framework. Paper: **arXiv 2506.12618**, "OpenUnlearning: Accelerating LLM Unlearning via Unified Benchmarking of Methods and Metrics".

**What it is.** A Hydra-configured framework that unifies LLM unlearning evaluation. The README states support for **12+ methods, 5+ datasets, 10+ evaluation metrics, and 7+ LLM architectures**. Methods shipped: `GradAscent`, `GradDiff`, `NPO`, `SimNPO`, `DPO`, `RMU`, `UNDIAL`, `AltPO`, `SatImp`, `WGA`, `CE-U`, `PDU`. Benchmarks shipped: **TOFU**, **MUSE**, **WMDP**.

**Install** (verbatim from the repo README):

```bash
conda create -n unlearning python=3.11
conda activate unlearning
pip install ".[lm-eval]"
pip install --no-build-isolation flash-attn==2.6.3
python setup_data.py --eval
```

**Run an unlearning job and then evaluate it** (verbatim from the README):

```bash
python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/default \
  forget_split=forget10 retain_split=retain90 trainer=GradAscent task_name=SAMPLE_UNLEARN

python src/eval.py --config-name=eval.yaml experiment=eval/tofu/default \
  model=Llama-3.2-1B-Instruct task_name=SAMPLE_EVAL
```

**When to use it:**
- Your project compares unlearning methods. Re-implementing `NPO` from the paper to compare against your method is a week you don't need to spend, and your baseline will be weaker than theirs.
- You want a defensible baseline number on TOFU/MUSE/WMDP that a reviewer recognises.
- You're proposing a new *metric* — the metric layer is the part the paper emphasises as extensible.

**When *not* to use it:**
- You only need a single RMU run on WMDP — the WMDP repo's own RMU script is smaller and has fewer moving parts.
- You're unlearning something that isn't Q&A-shaped or corpus-shaped. The config assumes forget/retain *splits*; a capability defined by a behaviour rather than a dataset doesn't fit.
- You're on a laptop. These are full finetuning runs on 1B–8B models.

**Pitfalls:**
- **It is Hydra all the way down.** Every knob is a config override (`trainer=NPO`, `forget_split=forget10`). If you `pip install` and then edit Python expecting it to take effect, it won't — the value came from YAML. Symptom: your "changed" hyperparameter appears unchanged in the run's resolved config dump.
- **`flash-attn` install fails** with a long nvcc error, or `ImportError: FlashAttention2 has been toggled on, but it cannot be used`. The README pins `flash-attn==2.6.3` with `--no-build-isolation` for a reason; if it still fails, run with `attn_implementation=eager` and note it — it changes throughput, not results.
- **Forget/retain split leakage.** `forget10` + `retain90` are designed to be disjoint. If you build custom splits, an overlapping entity in retain will silently re-teach the forget set, and your method will look worse than it is.
- **Comparing across benchmarks is meaningless.** TOFU "forget quality" and MUSE "knowmem" are different quantities on different scales. Don't put them in one table.

## Method vocabulary (for retrieval)

Each of these appears as a `trainer=` option in OpenUnlearning and as a named method in the literature.

- **Gradient Ascent (GradAscent).** Maximise loss on the forget set. The oldest baseline and the least stable — it degrades the whole model quickly. Symptom: `nan loss after step N`, or MMLU falling off a cliff while forget accuracy is still high.
- **Gradient Difference (GradDiff).** Gradient ascent on forget plus ordinary gradient descent on a retain set, to hold general capability in place. The standard "sane baseline".
- **NPO — Negative Preference Optimization** (arXiv 2404.05868, "Negative Preference Optimization: From Catastrophic Collapse to Effective Unlearning"). Treats the forget set as the *rejected* side of a DPO-style objective with no chosen side, which bounds how far the model can be pushed and avoids gradient ascent's catastrophic collapse. The most-cited modern baseline. **SimNPO** is the simplified variant shipped alongside it.
- **RMU — Representation Misdirection for Unlearning** (introduced in the WMDP paper, arXiv 2403.03218). Not a loss on outputs: it perturbs *activations* on hazardous data (scaling and redirecting them at a chosen layer) while a retain term pins activations on benign data. Representation-engineering-flavoured, which is why it composes with the steering and probing literature — see [`steering.md`](../interpretability/steering.md).
- **UNDIAL, AltPO, SatImp, WGA, CE-U, PDU.** Also shipped by OpenUnlearning; check the repo's method registry for the current citation of each rather than trusting a summary.

## Benchmarks

### TOFU (Task of Fictitious Unlearning)

arXiv **2401.06121**. A synthetic corpus of Q&A about **fictitious authors** — invented so that the "forget" knowledge provably entered the model during your finetune and not during pretraining. That control is the whole point: on real entities you can never tell whether the model still knows the fact from pretraining.

Splits are `forget01` / `forget05` / `forget10` (percent of authors to forget) with matching `retain99` / `retain95` / `retain90`.

**When *not* to use it:** if your claim is about hazardous capability. Fictitious-author facts are a clean testbed for *fact* removal and say little about whether a *skill* was removed.

### MUSE (Machine Unlearning Six-Way Evaluation)

arXiv **2407.06460**. Evaluates a corpus-level unlearn (news articles, Harry Potter books) along six axes including verbatim memorization, knowledge memorization, privacy leakage, utility preservation, scalability to sequential requests, and over-forgetting of the retain set.

**Why it matters for a project:** it's the benchmark that makes "and it didn't damage anything else" measurable. Most unlearning papers that only report forget-set accuracy are hiding a utility drop that MUSE would surface.

### WMDP (Weapons of Mass Destruction Proxy)

arXiv **2403.03218**. 3,000+ multiple-choice questions as a *proxy* for hazardous knowledge in bio, cyber and chem, plus RMU as the accompanying method. Already covered in [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md); listed here because it is the standard *capability*-removal target as opposed to *fact*-removal.

**Pitfall:** WMDP is multiple-choice. A model can lose the ability to pick the right option out of four while retaining the ability to write the procedure in free text. If your claim is "the capability is gone", MCQ accuracy is not enough — add a generative eval.

## The result you must engage with: it mostly isn't gone

If you write an unlearning project without addressing this literature, a reviewer will treat the work as naive.

- **arXiv 2402.16835** — "Eight Methods to Evaluate Robust Unlearning in LLMs" (Lynch et al.). Unlearning that looks complete under one probe survives under another: paraphrased prompts, in-context relearning, latent probes, and side-channel prompts all recover "removed" knowledge.
- **arXiv 2410.08827** — "Do Unlearning Methods Remove Information from Language Model Weights?" The answer is largely no: a small amount of finetuning on *adjacent, non-hazardous* data recovers much of the supposedly-unlearned capability, which means the information was still in the weights and only the retrieval path was suppressed.
- **arXiv 2501.04952** — "Open Problems in Machine Unlearning for AI Safety". The framing document; useful for a related-work section and for picking a problem that isn't already solved-shaped.
- **arXiv 2408.00761** — "Tamper-Resistant Safeguards for Open-Weight LLMs" (TAR). The counter-move: train the safeguard so that it survives an adversary's finetuning, rather than assuming the adversary won't finetune.

**Newer evidence, 2026-08 → 2026-10 (all arXiv abs pages checked; each is a preprint):**

- **arXiv 2609.36612** — Reisizadeh, Ruan, Liu & Hong, "Do LLMs Really Forget? Hidden-State Leakage in Model Unlearning and How to Fix it" (`OptimAI-Lab/HiddenStateUnlearning`). Output-level metrics create "an illusion of forgetting": a decoder can be made insensitive to sensitive directions while hidden representations keep the information. They train generative probe decoders on hidden states across layers and find substantial information still recoverable on TOFU, MUSE and WMDP for state-of-the-art methods even when output metrics say it is gone; their fix, PARS (Probe-Adversarial Representation Suppression), trains against extractable information and is reported to hold up better under adversarial probing and relearning. **Use it as:** an evaluation add-on — probe hidden states, not just outputs.
- **arXiv 2608.29943** — Hu, Tian, Wang, Mao et al., "On the Recoverability of Private Information Unlearning in Large Language Models". On a synthetic dataset of fake private information, "inverse greedy" decoding (picking the least likely token at each step) recovered supposedly-forgotten information from five unlearning methods. Cheap white-box audit.
- **arXiv 2609.34442** — Wang, Niu, Yin, Hsu et al., "Making LLMs Truly Forget: Deep Unlearning by Searching, Selecting, and Severing Knowledge Paths". A fact "forgotten" directly can be recovered by multi-hop reasoning over related knowledge; they cut supporting knowledge paths with a graph minimum cut. Implication for evals: test multi-hop questions that *combine* surviving facts.
- **arXiv 2609.40286** — Skow, Chaudhari, Chellappa & Yadav, "Linguistic Loopholes in LLM Unlearning". Unlearning a fact in one language does not remove it in others, and changing the query or the *answer* language can reopen it; the Cross-Lingual Unlearning Tensor benchmark spans 174 language-script pairs and 25 paraphrase types, and their COVER method picks a budgeted set of languages to unlearn in. Backs up the "evaluate in at least two formats" rule below with a larger test.
- **arXiv 2609.32103** — Ataee & Triantafillou, "LLM Unlearning Evaluation with TRIAGE". Benchmark-agnostic internal-change analysis (Fisher information and curvature changes, plus a Forget / Adjacent-Retain / Generic-Retain partition to measure an "adjacency gap"); over 12 methods, four models and WMDP, TOFU and MUSE, methods with similar behavioral forgetting made substantially different internal changes and collateral damage, and the patterns vary by model and benchmark.
- **arXiv 2609.00605** — Kim, Lee, Jeong, Lee et al., "Confess What You Know: Forget-Set Misalignment with Model Knowledge". When the forget set does not match what the model actually memorized, leakage persists ("under unlearning") or the algorithm perturbs parameters to forget things the model never learned ("out-of-knowledge unlearning"); their CONFS framework builds model-aligned forget sets by eliciting the model's memorized knowledge.
- **Standard compression does not undo TOFU unlearning, mostly** — hannahTao, "Does routine compression undo LLM unlearning? A short project" (LessWrong 2026-07-20; code `hannahTao/compression-unlearning`; a two-week BlueDot project, one model). On TOFU `forget10` with `Llama-3.2-1B-Instruct` and NPO, SimNPO and IdkDPO, 4-/8-bit quantization, magnitude pruning and SVD truncation mostly produced minimal reversal on the lead metric (teacher-forced probability of the correct forget-set answer); the largest recovery was magnitude pruning at 10–20% sparsity on NPO (up to 42% of the gap between the unlearned model and the never-unlearned ceiling), followed by 4-bit quantization on NPO (22%). Free generation on 20 forget questions still did not resurface the exact unlearned facts, and SimNPO and IdkDPO recovered at most 3% in non-destructive cells. The author screened out GradDiff (barely forgot) and RMU (failed to forget or collapsed at this scale). Earlier work found quantization *can* reverse some unlearning (arXiv 2410.16454, "Catastrophic Failure of LLM Unlearning via Quantization"), so check your specific method × quantization combination before shipping a quantized open-weight release.
- **Behavior-level targets.** Tang & Khanna, "Unlearning Deceptive Behaviors in LLMs with Contrastive Forget Sets" (arXiv 2609.38909) and Li et al., "LLM Persona Unlearning" with the PersonaUnlearnBench benchmark (arXiv 2609.39882) apply unlearning to *behaviors* and *personas* rather than facts. The deception paper reports that suppression objectives such as NPO leave much of the deception in place while target-based objectives induce "context blindness" (the model stops reading the pressuring context, invisible to deception rates and capability benchmarks); the persona paper reports standard methods cannot reliably erase a persona without hurting generation or utility. No code was verified for either, so treat as leads.

The practical consequence: **your paper needs a relearning attack, not just a forget-set score.** The cheapest credible version:

```python
# Relearning attack: does a small finetune on ADJACENT data bring the capability back?
# Adjacent = same domain, not the forget set itself. If forget-set data works, that
# proves nothing (you just retaught it); adjacent data working is the damning result.
from transformers import AutoModelForCausalLM, TrainingArguments, Trainer

for n_steps in [0, 10, 50, 100, 250, 500]:
    model = AutoModelForCausalLM.from_pretrained(UNLEARNED_CHECKPOINT)
    if n_steps:
        Trainer(
            model=model,
            args=TrainingArguments(
                max_steps=n_steps, learning_rate=1e-5,
                per_device_train_batch_size=4, output_dir=f"/tmp/relearn_{n_steps}",
                report_to="none",
            ),
            train_dataset=adjacent_dataset,   # NOT the forget set
        ).train()
    score = evaluate_forget_capability(model)   # your generative eval, not just MCQ
    print(f"{n_steps:>4} relearn steps -> forget-set capability {score:.3f}")
```

Plot capability against relearn steps. A method that is genuinely removing information stays flat; a method that suppressed the retrieval path snaps back within a few dozen steps. A flat curve here — together with the rest of the battery in "What would it take to show a new unlearning method works?" below — is exactly the result nobody has yet, so this plot is both the bar for a new method and the evidence that it cleared it. It is the plot the field wants and most papers don't show — see [`research-plots.md`](../engineering/research-plots.md) for how to present it.

## Pretraining-time removal: filter, route, or gate

Aliases: "data filtering", "Gradient Routing", "SGTM" (Selective GradienT Masking), "GRAM" (Gradient-Routed Auxiliary Modules), "modular pretraining", "capability access control", "pretraining-time capability removal", `agencyenterprise/modular-pretraining`.

A complementary line of work, not a replacement for post-hoc unlearning: arrange during pretraining for the knowledge to live in separable parameters (or never enter the shared weights), so removal later is an ablation rather than an optimisation. These are themselves unlearning research — NULLs calls its models "natively unlearnable" — and they don't help with an already-trained model. Four lines of work:

- **Data filtering still works, and a new proof of concept extends it to control-relevant knowledge.** O'Brien, Kitts, Tice & Westover (Geodesic Research and Redwood Research), "Research Note: Filtering Subversion-Relevant Information From Pretraining Data Is Feasible" (LessWrong 2026-10-05). They pretrained several 30B-total-parameter LLMs (Nemotron 3 Nano architecture: hybrid Mamba-MoE, 3B active) from scratch with and without filtering subversion-relevant information (subversion strategies, information about subversion defenses, evaluations of strategy effectiveness) and found the filtered models know far less about subversion (measured with a 900-question multiple-choice SubversionQA benchmark, cloze-style) while retaining general ML knowledge. The authors label it a proof of concept and say they have **not** tested whether less knowledge reduces the model's ability to subvert control protocols. No code was verified.
- **Gradient Routing and SGTM.** Gradient Routing (Cloud, Goldman-Wetzler, Wybitul, Miller et al., arXiv 2410.04332) masks gradients so chosen data only updates chosen parameters, which can later be removed. **SGTM** (Shilov, Cloud, Gema, Goldman-Wetzler et al., "Beyond Data Filtering: Knowledge Localization for Capability Removal in LLMs", arXiv 2512.05648) zero-masks gradients and was evaluated for robustness to label noise: on a bilingual synthetic task and on biology knowledge in an English-Wikipedia model it gave a better retain/forget trade-off than data filtering under labeling errors, and needed seven times more finetuning steps than RMU to recover baseline forget-set performance.
- **GRAM — modular pretraining for access control.** Roland, Cubuktepe, Martinez et al. (AE Studio, with Anthropic's Cem Anil and Alex Cloud), "Modular Pretraining Enables Access Control" (arXiv 2607.08077; Anthropic Alignment Science blog 2026-07-08; official code `agencyenterprise/modular-pretraining`, described as the ICML 2026 paper's code). Adds modules updated only on data tagged for a capability; ablating a module at inference removes that capability, approximating a filtered-data model, and re-enabling it restores it, so one training run serves several access tiers (the paper reports a 5× training-cost reduction over data filtering for five capability profiles). Results: on virology, cybersecurity, nuclear physics and specialist code at up to 5B parameters GRAM tracked data filtering, resisted recovery under malicious finetuning better than a post-hoc unlearning baseline, and (per the blog) handled partial labels better than filtering or LoRA. Stated limitations: preliminary, not applied to production models at Anthropic, loss-based rather than downstream-task evals, scaling checked only to 5B, entangled capabilities (general biology vs virology) may block clean separation, and instruction-tuning a GRAM-trained model is open. A separate preprint on per-principal access control inside one set of weights, "Capability-Gated Language Models: Security Composes, Utility Does Not" (Vanagas et al., arXiv 2609.00445), reports that combining access profiles composes suppression approximately but that individually harmless profiles can compose into retention and fluency damage with no compositional bound.
- **NULLs (Natively Unlearnable LLMs)** — Ghosal, Maini & Raghunathan (arXiv 2606.13873, June 2026): shared backbone neurons plus sparsely activated per-source "sinks"; unlearn a source by disabling its sinks with no gradient updates; scaled to roughly 6M Wikipedia articles as separate sources and, in a Harry Potter case study, resisted adversarial extraction and relearning that reverses post-hoc unlearning. Code not verified.

**When to use these:** you control pretraining or continued pretraining, can tag the hazardous data (even noisily), and want an off switch that survives adversarial finetuning. **When *not* to:** you need to remove knowledge from an *already-trained* open-weight model (none of these apply post hoc), you cannot tag data, or you need evidence at frontier scale (everything above is at most 30B parameters, mostly much smaller, and mostly loss- or MCQ-based evals).

## Cross-cutting pitfalls

- **Reporting forget accuracy without utility.** Every method can reach 0% on the forget set by lobotomising the model. Always report a general benchmark (MMLU, or MUSE's utility axis) alongside, on the same checkpoint.
- **Evaluating only in the format you unlearned in.** Unlearn on Q&A, evaluate on Q&A, declare victory; then the knowledge reappears under a cloze prompt, a different chat template, or another language. Evaluate across at least two formats.
- **Not fixing the retain set.** Different retain sets produce wildly different utility retention, so a method comparison where each method used its own retain set is not a comparison. This is a large part of what OpenUnlearning exists to standardise.
- **MCQ-only capability claims.** See the WMDP pitfall above.
- **Confusing unlearning with refusal.** A model that says "I can't help with that" has not unlearned anything, and abliteration-style refusal removal (see [`steering.md`](../interpretability/steering.md)) will undo it in minutes. If your eval scores refusals as successful forgetting, your numbers are measuring the wrong thing — score refusal and incapacity separately, as in [`code-recipes.md`](../engineering/code-recipes.md).
- **Evaluating outputs only.** A model can score zero output leakage while hidden states still encode the information (arXiv 2609.36612); add a probe-decoder or white-box audit (for example inverse greedy decoding, arXiv 2608.29943) next to the generative eval. Symptom: forget accuracy 0% but a linear or generative probe on layer-N activations still reads the answer.
- **Forgetting in one language or one hop only.** Test the answer in other languages (arXiv 2609.40286) and multi-hop questions that combine surviving facts (arXiv 2609.34442); a fact "forgotten" in English Q&A can be recovered either way.
- **Forget set that does not match what the model actually memorized.** For privacy-style unlearning where original training data is unavailable, a hand-built forget set can both miss memorized content and push the model to "forget" things it never learned (arXiv 2609.00605).
- **Releasing the "unlearned" checkpoint as safe.** Given 2410.08827, an open-weight release framed as hazard-free is a claim you probably cannot support.

## Starter scaffold

`project_templates/unlearning/` in the wiki repo is a working version of everything above: `ul_components` (splits that partition by key with a leakage assertion, the three objectives, the relearning sweep, and a `verdict()` whose vocabulary deliberately has no `REMOVED` label — its best outcome, `NO_RECOVERY_UNDER_THIS_ATTACK`, is the label a method that works earns) plus `example_1_relearning_curve`, a runnable toy experiment that implants facts about entities that don't exist, unlearns them, attacks with relearning on adjacent data and prints the verdict. CPU, minutes, no API keys.

## Cross-references

- [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md) — WMDP and the other benchmark entries.
- [`steering.md`](../interpretability/steering.md) — RMU is representation engineering; abliteration is the adversarial mirror image.
- [`model-diffing.md`](../interpretability/model-diffing.md) — what changed in the weights/activations between the base and unlearned model.
- [`saes.md`](../interpretability/saes.md) — SAE-based unlearning (feature clamping) is one of SAEBench's eight evals.
- [`rl-training.md`](../oversight-and-control/rl-training.md) — unlearning runs are finetuning runs; the same monitoring advice applies.

## Common questions

### Is unlearning a good MATS project?

Yes, on either side. No published post-hoc method removes knowledge robustly yet, which is what makes it worth working on. The thing to avoid is the *evaluation* lane that's crowded and weakly motivated: "new method beats NPO on TOFU forget-set score". Two kinds of project are tractable at fellow scale:

- **Build a method that actually removes something.** A new objective, a representation-level method (PARS-style training against probe decoders, arXiv 2609.36612), a structural one (cutting knowledge paths, arXiv 2609.34442) or something nobody has tried. Judge it by the attack battery in the next question from day one, not by forget-set accuracy, and report the attacks it fails as well as the ones it survives.
- **Sharpen the bar.** Show that a method's advertised removal fails under a new attack, use model diffing to show what actually changed, or build an evaluation that catches suppression-not-removal.

### What would it take to show a new unlearning method works?

Survive every attack the field already knows about, at a stated budget, while keeping utility. Concretely, on the same checkpoint:

1. **Relearning on adjacent (non-forget) data:** capability stays flat across a step sweep (the snippet above; arXiv 2410.08827).
2. **Hidden-state probes:** a linear or generative probe decoder on intermediate layers can't read the forgotten information (arXiv 2609.36612).
3. **Decoding attacks:** inverse-greedy or sampling-based extraction recovers nothing (arXiv 2608.29943).
4. **Reformulation:** paraphrase, cloze, other chat templates, other languages (arXiv 2609.40286), multi-hop questions combining surviving facts (arXiv 2609.34442), in-context relearning (arXiv 2402.16835).
5. **Weight perturbation:** quantization and pruning don't bring it back (arXiv 2410.16454 for quantization; the hannahTao compression post above for pruning and SVD truncation).
6. **Refusal vs incapacity scored separately**, and abliteration doesn't restore it (see [`steering.md`](../interpretability/steering.md)).
7. **Utility:** a general benchmark on the same checkpoint, against a fixed retain set.

The strongest honest claim after all of that is "not recovered under attacks 1–7 at budget B", which is what `ul_components.report` labels `NO_RECOVERY_UNDER_THIS_ATTACK`. That's the claim of a working method. "Removed" would assert there is no attack, which no finite battery can show, so phrase it as robustness to named attacks.

### How much compute do I need?

TOFU on Llama-3.2-1B is a single-GPU job of hours. WMDP + RMU on a 7B model is comfortably a single 80GB card. Full-suite comparisons across methods × splits × seeds are where the cost lands — budget by the sweep, not the run. See [`compute.md`](../models-and-compute/compute.md).

### Unlearning vs. filtering the pretraining data?

Different problems. Data filtering prevents the knowledge entering; unlearning tries to remove it afterwards and, with every method published so far, does so incompletely. If your threat model permits retraining, filtering is stronger; unlearning exists for the case where retraining is impossible. Since 2025 there is a middle option: route the hazardous data into removable parameters during pretraining (Gradient Routing, SGTM arXiv 2512.05648, GRAM arXiv 2607.08077), which is more robust to labeling errors than filtering in the cited experiments but is validated only at small scale. See "Pretraining-time removal: filter, route, or gate" above.

---

Last verified: 2026-10. OpenUnlearning README re-checked 2026-10-09 (still 12+ methods, 5+ datasets, 10+ metrics, 7+ architectures; the repo's latest commit, 2026-09-29, bumps `transformers` to 5.5.4). All arXiv IDs (2506.12618, 2404.05868, 2403.03218, 2401.06121, 2407.06460, 2402.16835, 2410.08827, 2501.04952, 2408.00761) resolved via the arXiv API to the titles cited. The relearning-attack snippet is our own illustrative code, not copied from a repo. (Additions 2026-10: newer evidence block (arXiv 2609.36612, 2608.29943, 2609.34442, 2609.40286, 2609.32103, 2609.00605, 2410.16454, 2609.38909, 2609.39882; `hannahTao/compression-unlearning`) and the "Pretraining-time removal: filter, route, or gate" section (arXiv 2410.04332, 2512.05648, 2607.08077, 2609.00445, 2606.13873; Redwood/Geodesic filtering research note); all arXiv IDs verified via arXiv abs pages and repos `OptimAI-Lab/HiddenStateUnlearning`, `agencyenterprise/modular-pretraining`, `hannahTao/compression-unlearning` via the GitHub API on 2026-10-09. Not verified: code for the NULLs, deep-unlearning, TRIAGE, persona- and deception-unlearning papers.)
