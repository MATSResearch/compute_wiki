---
tags:
  - alignment-science
---

# Unlearning and Knowledge Removal

Tooling for **machine unlearning** in language models: making a model stop being able to produce some body of knowledge or capability (bioweapons synthesis, copyrighted text, a specific person's data) while keeping everything else intact. Also called **knowledge removal**, **forgetting**, **capability removal**, **deep forgetting**.

This is one of the few safety areas with a real, unified codebase (**OpenUnlearning**), a set of standard benchmarks (**TOFU**, **MUSE**, **WMDP**), and a large, well-documented literature saying the methods mostly do not work as advertised. All three of those facts matter for a MATS project.

## At a glance

| If you want… | Use |
|---|---|
| Run any of 12+ published unlearning methods on a standard benchmark | **OpenUnlearning** (`locuslab/open-unlearning`) |
| Remove hazardous *capability* (bio/cyber) and measure it | **RMU** + the **WMDP** benchmark |
| Test forgetting *specific facts* about fictitious people | **TOFU** |
| Test forgetting a *corpus* (news, books) with memorization + privacy metrics | **MUSE** |
| Show that an unlearning method is fake | **relearning attacks** — a few hundred finetuning steps on adjacent data |
| Make an open-weight safeguard survive finetuning | **TAR** (Tamper-Resistant Safeguards, arXiv 2408.00761) |
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

Plot capability against relearn steps. A method that is genuinely removing information stays flat; a method that suppressed the retrieval path snaps back within a few dozen steps. This is the plot the field wants and most papers don't show — see [`research-plots.md`](../engineering/research-plots.md) for how to present it.

## Cross-cutting pitfalls

- **Reporting forget accuracy without utility.** Every method can reach 0% on the forget set by lobotomising the model. Always report a general benchmark (MMLU, or MUSE's utility axis) alongside, on the same checkpoint.
- **Evaluating only in the format you unlearned in.** Unlearn on Q&A, evaluate on Q&A, declare victory; then the knowledge reappears under a cloze prompt, a different chat template, or another language. Evaluate across at least two formats.
- **Not fixing the retain set.** Different retain sets produce wildly different utility retention, so a method comparison where each method used its own retain set is not a comparison. This is a large part of what OpenUnlearning exists to standardise.
- **MCQ-only capability claims.** See the WMDP pitfall above.
- **Confusing unlearning with refusal.** A model that says "I can't help with that" has not unlearned anything, and abliteration-style refusal removal (see [`steering.md`](../interpretability/steering.md)) will undo it in minutes. If your eval scores refusals as successful forgetting, your numbers are measuring the wrong thing — score refusal and incapacity separately, as in [`code-recipes.md`](../engineering/code-recipes.md).
- **Releasing the "unlearned" checkpoint as safe.** Given 2410.08827, an open-weight release framed as hazard-free is a claim you probably cannot support.

## Cross-references

- [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md) — WMDP and the other benchmark entries.
- [`steering.md`](../interpretability/steering.md) — RMU is representation engineering; abliteration is the adversarial mirror image.
- [`model-diffing.md`](../interpretability/model-diffing.md) — what changed in the weights/activations between the base and unlearned model.
- [`saes.md`](../interpretability/saes.md) — SAE-based unlearning (feature clamping) is one of SAEBench's eight evals.
- [`rl-training.md`](../oversight-and-control/rl-training.md) — unlearning runs are finetuning runs; the same monitoring advice applies.

## Common questions

### Is unlearning a good MATS project?

Yes, but pick the sceptical side. "New unlearning method beats NPO on TOFU" is a crowded, weakly-motivated lane. "Method X's advertised removal survives/doesn't survive attack Y", "what does model diffing show actually changed", and "an evaluation that catches suppression-not-removal" are all tractable at fellow scale and are what the field is short of.

### How much compute do I need?

TOFU on Llama-3.2-1B is a single-GPU job of hours. WMDP + RMU on a 7B model is comfortably a single 80GB card. Full-suite comparisons across methods × splits × seeds are where the cost lands — budget by the sweep, not the run. See [`compute.md`](../models-and-compute/compute.md).

### Unlearning vs. filtering the pretraining data?

Different problems. Data filtering prevents the knowledge entering; unlearning tries to remove it afterwards and, per the literature above, does so incompletely. If your threat model permits retraining, filtering is stronger; unlearning exists for the case where retraining is impossible.

---

Last verified: 2026-08-26. OpenUnlearning README checked for method/benchmark lists and the verbatim install and CLI commands. All arXiv IDs (2506.12618, 2404.05868, 2403.03218, 2401.06121, 2407.06460, 2402.16835, 2410.08827, 2501.04952, 2408.00761) resolved via the arXiv API to the titles cited. The relearning-attack snippet is our own illustrative code, not copied from a repo.
