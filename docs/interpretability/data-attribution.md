---
tags:
  - interpretability
---

# Data Attribution and Influence Functions

Tooling for the question **"which training examples caused this behaviour?"** Also called **training data attribution (TDA)**, **influence functions**, **datamodels**, **example-level attribution**, **provenance**.

The safety use case is specific and increasingly common: you have a model organism that does something surprising (emergent misalignment from insecure code, a persona that transferred through unrelated numbers, a backdoor) and you want to point at the training documents responsible, rather than at a feature. That is a different question from [model diffing](model-diffing.md) ("what changed in the model") and from probing ("where does the model represent it").

## At a glance

| If you want… | Use |
|---|---|
| Influence functions on a PyTorch model, EK-FAC approximation | **kronfluence** (`pip install kronfluence`) |
| Fast attribution over a large train set, many queries | **TRAK** (`pip install traker`) |
| The conceptual reference for LLM-scale influence functions | arXiv **2308.03296** (Grosse et al., EK-FAC) |
| A cheap, honest baseline before any of the above | **retrain-without-it** on a subsampled train set, or embedding/BM25 retrieval over the train set |
| "Which *concept* changed", not "which document" | [`model-diffing.md`](model-diffing.md) |

**Start with the cheap baseline.** If your finetune set is small (the usual MATS case — a few thousand documents), leave-one-group-out retraining is exact, trivially explainable, and often affordable: partition the training data into 20 buckets, retrain 20 times with one bucket held out, and see which holdout kills the behaviour. Influence functions are an approximation to that experiment; when you can afford the experiment, run it.

## kronfluence

Aliases: `kronfluence` on PyPI, `pomonam/kronfluence` on GitHub, "the KFAC/EK-FAC influence library".

**What it is.** A PyTorch package that computes influence functions using **KFAC** (Kronecker-Factored Approximate Curvature) or **EK-FAC** (Eigenvalue-corrected KFAC) — the approximation used in arXiv 2308.03296, "Studying Large Language Model Generalization with Influence Functions". Requires Python ≥ 3.9 and PyTorch ≥ 2.1.

**The stated limitation, up front:** it supports influence computation on **`nn.Linear` and `nn.Conv2d` modules only**. For a transformer that covers attention and MLP projections — i.e. most of the parameters — but embeddings, layernorms and anything custom are excluded from the attribution.

**Usage** (structure verbatim from the repo README):

```python
import torch
from kronfluence.analyzer import Analyzer, prepare_model

model.load_state_dict(torch.load("model_path.pth", weights_only=True))

task = MyTask()                                   # subclass of kronfluence.task.Task
model = prepare_model(model=model, task=task)
analyzer = Analyzer(analysis_name="my_run", model=model, task=task)

analyzer.fit_all_factors(factors_name="my_factors", dataset=train_dataset)
analyzer.compute_pairwise_scores(
    scores_name="my_scores",
    factors_name="my_factors",
    query_dataset=eval_dataset,      # the behaviours you want explained
    train_dataset=train_dataset,     # the candidates
    per_device_query_batch_size=1024,
)
```

The `Task` you subclass (`kronfluence.task.Task`) has two abstract methods you must implement — `compute_train_loss(batch, model, sample=False)` and `compute_measurement(batch, model)` — plus an optional `get_influence_tracked_modules()` returning a list of module names to restrict attribution to a subset of the network.

`compute_measurement` is where the safety framing lives: it returns the quantity *f(θ)* you want explained. For "which documents made it write insecure code", the measurement is the log-probability of the misaligned completion under the query prompt, **not** the training loss.

**When to use it:**
- You finetuned a model yourself, have the training set on disk, and want per-document attribution for a specific surprising output.
- You want the method used by the reference LLM influence-function paper rather than a bespoke gradient-similarity heuristic.

**When *not* to use it:**
- The model is API-only, or you don't have the training data. Influence functions need both.
- You want attribution over *pretraining*. At that scale this is a research project of its own, not a library call.
- Your question is "which concept", not "which document" — use diffing or SAEs.

**Pitfalls:**
- **Factor fitting is the expensive step, and it is per-model-state.** `fit_all_factors` must be re-run after any weight change. Symptom: silently reusing a `factors_name` from a different checkpoint and getting scores that look plausible and mean nothing. Namespace `factors_name` by checkpoint.
- **`compute_pairwise_scores` is |query| × |train|.** Memory and time grow with both; the `per_device_query_batch_size` in the README (1024) is an MNIST-scale number, not an LLM-scale one.
- **Influence is a local, first-order approximation** around the current weights. It answers "if this example had been slightly up/down-weighted", not "if this example had never existed". For a behaviour that emerged from a phase transition during training, the approximation can be badly wrong — this is the honest caveat to put in your limitations section.
- **Only `nn.Linear` / `nn.Conv2d`.** If a wrapper replaces linear layers (some quantisation and LoRA paths do), those modules are skipped and the attribution silently covers less of the model than you think. Check `get_influence_tracked_modules()` output.

## TRAK

Aliases: `traker` on PyPI (**note the name**: `pip install traker`, not `pip install trak`), `MadryLab/trak` on GitHub. Paper: arXiv **2303.14186**, "TRAK: Attributing Model Behavior at Scale".

**What it is.** A data-attribution method built on random projections of per-example gradients (the "randomly-projected after kernel"), designed to be much cheaper than exact influence functions at large scale. An optional fast CUDA kernel for the JL (Johnson–Lindenstrauss) projection step installs via `pip install traker[fast]`.

**When to use it:** many queries against a large training set, where kronfluence's pairwise scoring is too slow; or when you want attribution *ensembled over several independently trained models*, which TRAK's formulation expects and which materially improves attribution quality.

**When *not* to use it:** you have exactly one model and one query — the setup cost isn't worth it. Also note TRAK's headline results come from ensembling over multiple training runs; a single-model TRAK score is a weaker estimate than the paper's numbers imply, so don't cite paper-level accuracy for a single-model application.

**Pitfalls:**
- **Package name mismatch** (`traker` vs the repo name `trak`) — symptom: `ModuleNotFoundError: No module named 'trak'` after installing the wrong PyPI package, or installing an unrelated project.
- **`[fast]` needs a matching CUDA toolchain.** If the kernel won't build, the plain install works and is just slower.

## Cheap baselines worth running first

- **Retrain-without-bucket.** Described above. Exact, interpretable, and for a small finetune set often cheaper than fitting EK-FAC factors.
- **Nearest-neighbour retrieval.** Embed the surprising output and retrieve the most similar training documents. This is *not* attribution — similarity is not causation — but it takes ten minutes and frequently finds the culprit outright, which then makes the ablation experiment targeted rather than a sweep.
- **Gradient similarity (TracIn-style).** Dot-product of the per-example gradient with the query gradient, no curvature correction. A few lines of PyTorch, and a reasonable sanity check that a fancier method should at least agree with directionally.

Whatever you use, **validate the attribution causally**: take the top-K attributed documents, remove them, retrain, and show the behaviour weakens. An attribution result with no ablation is a ranking, not a finding — the same standard [`research-rigor.md`](../engineering/research-rigor.md) applies to every other observational claim.

## Cross-cutting pitfalls

- **Attributing to the wrong measurement.** Attributing the *training loss* on a misaligned completion mostly recovers "documents that look like this one". Attributing the *log-prob margin between the misaligned and aligned completion* is usually the question you meant.
- **No negative control.** Run the same pipeline on a *benign* query. If the same documents come top for both, your scores are measuring generic influence (long documents, high-gradient-norm documents), not your behaviour.
- **Gradient-norm dominance.** Unusually long or noisy training examples get high influence for everything. Normalise, or at minimum plot influence against document length before believing a ranking.
- **Reporting influence ranks as causes** in the write-up. Report them as candidates, then report the ablation.

## Cross-references

- [`model-organisms.md`](../alignment-science/model-organisms.md) — emergent misalignment and subliminal learning are the archetypal "which data did this" cases.
- [`model-diffing.md`](model-diffing.md) — the complementary question, in weight/activation space.
- [`unlearning.md`](../alignment-science/unlearning.md) — if you can attribute it, you may not need to unlearn it: retrain without it.
- [`research-rigor.md`](../engineering/research-rigor.md) — observational evidence does not license a causal claim.
- [`compute.md`](../models-and-compute/compute.md) — factor fitting and retraining sweeps are the cost driver here.

## Common questions

### Can I run influence functions on a model I only access through an API?

No. Every method here needs per-example gradients, therefore weights, therefore an open-weights model you host yourself.

### How big a model can I attribute over?

kronfluence's EK-FAC factors scale with layer widths, and the practical ceiling for a single 80GB card is small-to-mid models (roughly ≤7B, less if the query set is large). Attribution over a 70B model is a multi-node engineering project; budget accordingly or pick a smaller model organism, which for most safety questions is the right call anyway.

### Is influence-function attribution reliable?

Partially. It is a first-order local approximation with well-documented failure modes, and published evaluations of TDA methods generally find they correlate with, but do not match, retraining ground truth. Treat scores as a search heuristic that generates candidates for an ablation experiment, and say so in your limitations.

---

Last verified: 2026-08-26. kronfluence README (install, `Analyzer` example, the `nn.Linear`/`nn.Conv2d` limitation) and `kronfluence/task.py` (the `compute_train_loss` / `compute_measurement` / `get_influence_tracked_modules` signatures) read directly from the repo. TRAK install names confirmed from `MadryLab/trak` and the `traker` PyPI listing. arXiv 2308.03296 and 2303.14186 resolved via the arXiv API to the titles cited. The baseline recipes in "Cheap baselines" are our own recommendations.
