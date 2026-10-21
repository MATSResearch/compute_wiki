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
| A maintained library with EK-FAC, TrackStar, SOURCE, MAGIC, TRAK and gradient-cosine under one CLI, on-disk gradient stores, multi-node runs | **Bergson** (`pip install bergson`, `EleutherAI/bergson`; arXiv **2606.11660**) |
| Fast attribution over a large train set, many queries | **Bergson** `trackstar` / on-disk gradient store, or **TRAK** (`pip install traker`; last GitHub push 2024-11-18) |
| The conceptual reference for LLM-scale influence functions | arXiv **2308.03296** (Grosse et al., EK-FAC) |
| Hessian-free influence (no inverse-Hessian fit), per-token, any differentiable layer, cheap for a few targeted queries on a large model | **Bayesian Influence Functions** (BIF) via **devinterp** (`uv add devinterp`, `timaeus-research/devinterp`; arXiv **2509.26544**) |
| A cheap, honest baseline before any of the above | **retrain-without-it** on a subsampled train set, or embedding/BM25 retrieval over the train set |
| "Which *concept* changed", not "which document" | [`model-diffing.md`](model-diffing.md) |

**Start with the cheap baseline.** If your finetune set is small (the usual MATS case — a few thousand documents), leave-one-group-out retraining is exact, trivially explainable, and often affordable: partition the training data into 20 buckets, retrain 20 times with one bucket held out, and see which holdout kills the behaviour. Influence functions are an approximation to that experiment; when you can afford the experiment, run it.

## kronfluence

Aliases: `kronfluence` on PyPI, `pomonam/kronfluence` on GitHub, "the KFAC/EK-FAC influence library".

**What it is.** A PyTorch package that computes influence functions using **KFAC** (Kronecker-Factored Approximate Curvature) or **EK-FAC** (Eigenvalue-corrected KFAC) — the approximation used in arXiv 2308.03296, "Studying Large Language Model Generalization with Influence Functions". Requires Python ≥ 3.9 and PyTorch ≥ 2.1.

**Status (2026-10):** last GitHub push 2026-05-23 (not archived); `kronfluence` 1.0.1 on PyPI. Bergson (below) also implements EK-FAC and scales out; kronfluence remains a fine single-GPU reference.

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

**Status (2026-10):** `MadryLab/trak` last pushed 2024-11-18 (not archived); `traker` 0.3.2 on PyPI. In Bergson's own GPT-2/WikiText leaderboard an 8-model TRAK ensemble scored LDS 0.138 versus 0.454 for EK-FAC and 0.276 for TrackStar (one setting, library authors' benchmark) — prefer Bergson's `trackstar` or `ekfac` for new work unless you specifically need the TRAK paper's method.

**When to use it:** many queries against a large training set, where kronfluence's pairwise scoring is too slow; or when you want attribution *ensembled over several independently trained models*, which TRAK's formulation expects and which materially improves attribution quality.

**When *not* to use it:** you have exactly one model and one query — the setup cost isn't worth it. Also note TRAK's headline results come from ensembling over multiple training runs; a single-model TRAK score is a weaker estimate than the paper's numbers imply, so don't cite paper-level accuracy for a single-model application.

**Pitfalls:**
- **Package name mismatch** (`traker` vs the repo name `trak`) — symptom: `ModuleNotFoundError: No module named 'trak'` after installing the wrong PyPI package, or installing an unrelated project.
- **`[fast]` needs a matching CUDA toolchain.** If the kernel won't build, the plain install works and is just slower.

## Bergson

Aliases: `bergson` on PyPI (v2.3.1, 2026-10-20), `EleutherAI/bergson` on GitHub, arXiv **2606.11660** (Quirke, Jaburi, Johnston, Li, Paulo, Martres, Gupta, Belrose & Biderman, "Bergson: An Open Source Library for Data Attribution"), "EleutherAI's data attribution library". Method names it implements: **EK-FAC** (Eigenvalue-corrected Kronecker-Factored Approximate Curvature, arXiv 2308.03296), **TrackStar** (arXiv 2410.17413), **SOURCE** (arXiv 2405.12186), **MAGIC** (arXiv 2504.16430), **ASTRA** (arXiv 2507.14740), TRAK, gradient cosine similarity.

**What it is.** A Python library and CLI for scalable training data attribution (TDA) on language models. `bergson magic` backpropagates through the training process (its own twice-differentiable trainer) to get the gradient of a behaviour loss with respect to a weight on each training item; `bergson approxunrolling` approximates that from a few checkpoints (multi-step SOURCE); `bergson trackstar`, `bergson ekfac` and `bergson trak` (which supports ensembling over independently trained models) orchestrate post-hoc recipes over a checkpoint; `bergson build` / `query` / `score` give an on-disk gradient store with collection-time compression and FAISS nearest-neighbour search for many queries; `bergson validate` and `recall` compute LDS (linear datamodeling score) and recall@k. A Hugging Face Trainer callback records a train-time gradient store at roughly 17% overhead (per the README). The README claims multi-node runs with 70B+ parameters; the abstract says it provides the first open-source implementations of MAGIC, SOURCE and TrackStar. Releases v2.2.1 → v2.3.1 landed between 2026-09-29 and 2026-10-20 (three on 2026-10-20 alone), so pin a version. **For RL rollouts (v2.3.0):** an `advantage_column` takes per-example advantages, "e.g. those logged by a GRPO trainer", and is now the documented way to collect GRPO loss gradients; passing rewards and letting Bergson compute advantages still works for backward compatibility but was dropped from the docs (PR #563). v2.2.4 probes `auto_batch_size` with the run's own batches (#561); v2.3.1 slices saved datasets by split and promotes rerun EK-FAC outputs (#564).

```bash
# verbatim from the Bergson README: build and query an on-disk index of randomly projected gradients
bergson build runs/index --model EleutherAI/pythia-14m --dataset NeelNanda/pile-10k --truncation --token_batch_size 4096 --projection_dim 16
bergson query --index runs/index --unit_norm
```

**Its own leaderboard (indicative, one setting).** GPT-2 finetuned on WikiText for 4 epochs; LDS (higher is better): MAGIC 0.931, EK-FAC + ASTRA 0.643, eigenvalue-corrected Shampoo 0.517, SOURCE (Adam, EK-FAC) 0.473, EK-FAC 0.454, TrackStar (no optimizer) 0.276, BM25 0.220, gradient cosine 0.156, TRAK (8-model ensemble) 0.138, Qwen3-8B semantic search 0.132, activation similarity 0.110. This is the library authors' benchmark at GPT-2 scale, not an independent evaluation; it is the main reason the old advice "TRAK for large train sets" is no longer a safe default.

**When to use it:** you want attribution beyond toy scale, several methods under one interface, many queries against one stored gradient index, or MAGIC-style attribution through a small finetune you can re-run (the README ships a poison-detection notebook and a style-ablation notebook).

**When *not* to use it:** API-only models or no access to the training data. MAGIC's efficacy is proportional to *metasmoothness* of the training run, which is low in some settings including early pretraining steps — run `bergson metasmoothness` first. Influence functions are also sensitive to the Hessian-damping hyperparameter in tiny models; tune it.

**Pitfalls:**
- **Inconsistent per-example gradients under batching.** Some models give different per-example gradients when batched (nondeterminism in optimized SDPA, scaled dot-product attention, backends: flash / memory-efficient), so scores shift with padding or batch composition. Run `bergson test_model_configuration --model <name>`; it reports which of `--force_math_sdp`, `--precision fp32 --use_tf32_matmuls --force_math_sdp`, or full `--precision fp32` you need (same flags for `score` and `trackstar`), and also detects BOS/EOS duplication from chat templates.
- **Stale index.** A gradient store is tied to the checkpoint it was built from; rebuild after any weight change (same rule as kronfluence factors).

## Bayesian Influence Functions (BIF) via devinterp

Aliases: BIF, local Bayesian influence function, Hessian-free influence functions, SGLD (stochastic gradient Langevin dynamics) influence, SGMCMC (stochastic-gradient Markov chain Monte Carlo) attribution, posterior loss correlation, `devinterp.slt.bif`, Timaeus.

**What it is.** Kreer, Wu, Adam, Furman & Hoogland, "Bayesian Influence Functions for Hessian-Free Data Attribution" (arXiv **2509.26544**, ICLR 2026). Classical influence functions, EK-FAC (Eigenvalue-corrected Kronecker-Factored Approximate Curvature) included, need an inverse Hessian. The BIF instead samples weights near the trained checkpoint with SGLD and uses the (negative) covariance between a training example's loss and a query's loss across those samples as the influence. It comes from singular learning theory (SLT), the same machinery as the local learning coefficient (LLC); see [`slt-devinterp.md`](slt-devinterp.md). It works for any differentiable layer, whereas EK-FAC (and kronfluence) cover only `nn.Linear` / `nn.Conv2d`, so attention and normalization are left out. It gives per-token influence matrices directly.

**What the paper shows, against EK-FAC.**
- *Retraining accuracy (LDS, linear datamodeling score):* on CIFAR-10 / ResNet-9 the BIF beat EK-FAC in the small-retrain-subset regime. In a Pythia-14M WikiText finetuning setting it *underperformed*: LDS 0.110 versus 0.221 for EK-FAC and 0.198 for plain gradient similarity (appendix C.3). The authors attribute this to harder sampling for language models.
- *Cost:* on the small image models EK-FAC was about 5x faster. In a timing comparison across the Pythia suite (up to Pythia-2.8B, on one 4xA100 node, 2k SGLD draws) the BIF needs no up-front factor fit, and for the largest models it was about two orders of magnitude faster in evaluation time at the same peak GPU memory. EK-FAC's fitted factors for Pythia-2.8B took 41 GiB on disk. That fit only pays off once you score many queries.
- *Main limitation (authors'):* accuracy depends on posterior-sampling quality, and the SGLD hyperparameters (step size, localization strength γ, inverse temperature β) are not well characterized for language models.

**Code.** `devinterp` on PyPI (2.0.1, 2026-04-23, Python ≥ 3.10; MIT; `timaeus-research/devinterp`, last push 2026-04-23), the Timaeus library that also computes the LLC and susceptibilities. Install with `uv add devinterp`. From its README:

```python
from devinterp.slt.bif import bif

result = bif(
    model=model,
    dataset=train_data,
    observables={"train": train_data, "code": code_data},
    lr=0.001,
    n_beta=30,
    num_chains=4,
    num_draws=200,
    correlation_method="token",  # or "sequence"
)
# result["influences"] contains pairwise correlation matrix
```

The v2 API expects an autoregressive model that takes `input_ids` and returns logits, and a Hugging Face `Dataset` with a uniform-length `"input_ids"` column (not a `DataLoader`). Pass `loss_fn=` for a non-standard loss. **v1 code does not carry over:** the README's migration notes say `estimate_learning_coeff` (and `_with_summary`), `LLCEstimator` and `SamplerCallback` were replaced by `llc()` / `compute_llc()`, `sampling_method_kwargs={"nbeta": ...}` by a direct `n_beta=` parameter, and that results are now xarray objects rather than dicts with string keys (`result["llc/mean"]` became `result["llc_mean"]`). Older tutorials that use those names are v1; pin the major version. Timaeus publishes a sampling-hyperparameter guide linked from the README, which is the first thing to read when chains diverge, spike or return NaNs.

**When to use it:** a handful of targeted queries on a model too large for a cheap EK-FAC fit; you want influence over attention or normalization weights too; you want token-level attribution.

**When *not* to use it:** many queries against one model (amortize an EK-FAC or Bergson gradient store instead); you cannot afford a hyperparameter sweep on the sampler; you need an accuracy claim on language models, where the paper's own LDS comparison favoured EK-FAC.

**Open problem — the bar.** The paper's language-model evidence is a timing comparison up to 2.8B parameters and an LDS comparison at 14M where EK-FAC won. A result that would move practice: BIF matching or beating EK-FAC (or Bergson's best method) on LDS or retraining-based evaluation for a ≥1B-parameter language model at matched compute, with the sampler settings reported, ideally on a safety task such as emergent-misalignment data filtering (Paulo et al., arXiv 2609.37914).

## What 2026 evaluations found: attribution for emergent misalignment, subliminal learning and RL

Attribution is now being *evaluated* on the safety use cases above, with mixed results. Read these before claiming a top-K list is "the cause":

- **Paulo, Jaburi, Belrose, Quirke & Biderman, "The Unequal Influence of Bad Advice: Using Training Data Attribution to Modulate Emergent Misalignment"** (arXiv **2609.37914**, 2026-09-29). Validates attribution by *retraining*: filtering data on the score can enhance or attenuate emergent misalignment (EM). Both influence scores and a **black-box harmfulness score** identified consequential examples (so the cheap LLM-judge baseline is a real competitor); scores work best when used to filter data for the same model that computed them, and generalize across the three model families tested only partially.
- **Vetter et al., "Data Attribution of Emergent Misalignment with Persona Features"** (arXiv **2608.11025**, 2026-08-11; code `vetterc0/emergent_misalignment_SAE`). Attributes SAE (sparse autoencoder) persona features to 1M pretraining documents; the retrieved villain-narrative documents did *not* reliably induce EM when finetuned on, while synthetic instruction-response pairs derived from them did. Retrieval relevance is not sufficiency. (Details in [`model-diffing.md`](model-diffing.md).)
- **Weckbecker et al., "Can Data Attribution Filter Out Subliminal Learning? Not Reliably"** (arXiv **2609.20027**, 2026-09-17). Three gradient-based methods (GradCos, a contrastive GradCos variant, EK-FAC) across three models, against a "divergence tokens" baseline that needs counterfactual teacher access: at token level EK-FAC removed a meaningful part of the effect, the others little, and all mostly fell short of divergence tokens; whole-sample filtering was weaker; success was inconsistent across model-preference pairs with no clear explanation.
- **Kim et al., "Form Over Content In Gradient-Based Data Attribution Methods"** (arXiv **2609.19589**, 2026-09-17). Gradient similarity follows *answer format*: benchmark pairs sharing a format align (disattenuated cosine about 0.4) while the same tasks in different formats do not (about 0.0); the released LESS selections over-represent the target's own answer format. Any gradient-similarity ("TracIn-style") baseline inherits this confound.
- **Nautiyal, "Which Rollout Taught It That? BehaviorTrace and the Limits of Training-Data Attribution in Online RL"** (arXiv **2610.10422**, 2026-10-07; harness `AmitoVrito/BehaviorTrace`). On GRPO (Group Relative Policy Optimization) finetuning of Qwen2.5-1.5B with a planted behaviour of known cause, a control that ranks steps by gradient size alone (no behaviour target) reached 4.2–4.5x chance and matched or beat the best targeted estimator on two of three seeds, and model fluency predicted the behaviour label at least as well as every gradient method at saturated checkpoints; per-rollout results changed across seeds. They give a checklist for evaluating attribution in RL (controls for gradient magnitude, fluency, headroom, seed and generation-draw variation) and propose no new estimator.
- **Concept Influence** (Kowal, Paulo, Jaburi et al., arXiv **2602.14869**, Feb 2026 — just before this window): attributes behaviour to a *semantic direction* (a linear probe or SAE feature) instead of single test examples, and reports probe-based first-order approximations that are over an order of magnitude faster with comparable performance on EM benchmarks. A natural bridge to [`probes.md`](probes.md).

**What to do with this:** plan a negative control (gradient-norm-only ranking and an LLM-judge ranking) and a retraining check for every attribution claim; use the same model for scoring and filtering; do not assume attribution transfers across models or formats.

## Cheap baselines worth running first

- **Retrain-without-bucket.** Described above. Exact, interpretable, and for a small finetune set often cheaper than fitting EK-FAC factors.
- **Nearest-neighbour retrieval.** Embed the surprising output and retrieve the most similar training documents. This is *not* attribution — similarity is not causation — but it takes ten minutes and frequently finds the culprit outright, which then makes the ablation experiment targeted rather than a sweep.
- **Gradient similarity (TracIn-style).** Dot-product of the per-example gradient with the query gradient, no curvature correction. A few lines of PyTorch, and a reasonable sanity check that a fancier method should at least agree with directionally.
- **Black-box LLM-judge score.** Score each training example with a harmfulness / relevance judge and rank by that. Paulo et al. (arXiv 2609.37914) found that a black-box harmfulness score *also* identifies consequential EM examples (alongside influence scores), so it is a baseline your attribution method has to beat. Beware the gradient-similarity format confound (Kim et al., arXiv 2609.19589).

Whatever you use, **validate the attribution causally**: take the top-K attributed documents, remove them, retrain, and show the behaviour weakens. An attribution result with no ablation is a ranking, not a finding — the same standard [`research-rigor.md`](../engineering/research-rigor.md) applies to every other observational claim.

## Cross-cutting pitfalls

- **Attributing to the wrong measurement.** Attributing the *training loss* on a misaligned completion mostly recovers "documents that look like this one". Attributing the *log-prob margin between the misaligned and aligned completion* is usually the question you meant.
- **No negative control.** Run the same pipeline on a *benign* query. If the same documents come top for both, your scores are measuring generic influence (long documents, high-gradient-norm documents), not your behaviour.
- **Gradient-norm dominance.** Unusually long or noisy training examples get high influence for everything. Normalise, or at minimum plot influence against document length before believing a ranking. In an online-RL benchmark a gradient-size-only ranking matched or beat the best targeted estimator on two of three seeds (Nautiyal, arXiv 2610.10422).
- **Format confound.** Gradient similarity tracks answer format more than task content (Kim et al., arXiv 2609.19589); test on data where format and task vary independently.
- **Reporting influence ranks as causes** in the write-up. Report them as candidates, then report the ablation.

## Cross-references

- [`model-organisms.md`](../alignment-science/model-organisms.md) — emergent misalignment and subliminal learning are the archetypal "which data did this" cases.
- [`model-diffing.md`](model-diffing.md) — the complementary question, in weight/activation space.
- [`slt-devinterp.md`](slt-devinterp.md) — singular learning theory and the `devinterp` library behind Bayesian Influence Functions (LLC, susceptibilities).
- [`unlearning.md`](../alignment-science/unlearning.md) — if you can attribute it, you may not need to unlearn it: retrain without it.
- [`research-rigor.md`](../engineering/research-rigor.md) — observational evidence does not license a causal claim.
- [`compute.md`](../models-and-compute/compute.md) — factor fitting and retraining sweeps are the cost driver here.

## Common questions

### Can I run influence functions on a model I only access through an API?

No. Every method here needs per-example gradients, therefore weights, therefore an open-weights model you host yourself.

### How big a model can I attribute over?

kronfluence's EK-FAC factors scale with layer widths, and the practical ceiling for a single 80GB card is small-to-mid models (roughly ≤7B, less if the query set is large). Bergson (`pip install bergson`) advertises multi-node runs at 70B+ parameters with on-disk gradient stores, so attribution over a large model is now a library call plus a cluster rather than a from-scratch project — but it is still a multi-node cost center, and a smaller model organism is still the right default for most safety questions. For a few targeted queries on a large model, Bayesian Influence Functions (`devinterp`, arXiv 2509.26544) skip the inverse-Hessian fit entirely; the paper timed them up to Pythia-2.8B, but its only language-model accuracy comparison (Pythia-14M) favoured EK-FAC.

### Is influence-function attribution reliable?

Partially. It is a first-order local approximation with well-documented failure modes, and published evaluations of TDA methods generally find they correlate with, but do not match, retraining ground truth. 2026 evaluations on safety tasks agree: attribution only partly filters out subliminal learning (arXiv 2609.20027), gradient similarity follows answer format (arXiv 2609.19589), a gradient-norm-only control rivals targeted estimators in online RL (arXiv 2610.10422), and EM-attribution scores transfer across models only partially (arXiv 2609.37914). Treat scores as a search heuristic that generates candidates for an ablation experiment, and say so in your limitations.

---

Last verified: 2026-10-20 (Bergson v2.2.4–v2.3.1 release notes and PR #563 via `gh api`, PyPI 2.3.1). Earlier, 2026-10: kronfluence README (install, `Analyzer` example, the `nn.Linear`/`nn.Conv2d` limitation) and `kronfluence/task.py` (the `compute_train_loss` / `compute_measurement` / `get_influence_tracked_modules` signatures) read directly from the repo. TRAK install names confirmed from `MadryLab/trak` and the `traker` PyPI listing. arXiv 2308.03296 and 2303.14186 resolved via the arXiv API to the titles cited. The baseline recipes in "Cheap baselines" are our own recommendations. (Additions 2026-10: Bergson — `EleutherAI/bergson` (MIT, last push 2026-10-08, v2.2.3 on PyPI), README, CHANGELOG and `docs/numerical-stability.rst` / `limitations.rst` read directly, arXiv 2606.11660; EM / subliminal-learning / RL attribution evaluations arXiv 2609.37914, 2608.11025, 2609.20027, 2609.19589, 2610.10422 (`AmitoVrito/BehaviorTrace` resolves), 2602.14869; `pomonam/kronfluence` last push 2026-05-23 and `MadryLab/trak` last push 2024-11-18 re-checked with `gh api`. All arXiv IDs fetched from abs pages on 2026-10-09; the Bergson leaderboard numbers are the library authors' own and for one GPT-2 setting.) (Additions 2026-10-12: Bayesian Influence Functions — arXiv 2509.26544 abstract via the arXiv API, and the EK-FAC comparison (CIFAR-10 LDS, Pythia-14M LDS table C.3, Pythia timing in Figure 5 and appendix B.3, limitations) read from the paper PDF; `devinterp` README (BIF snippet verbatim, model requirements, v1→v2 migration notes) read from `timaeus-research/devinterp`, repo checked via the GitHub API (MIT, last push 2026-04-23) and PyPI JSON (2.0.1, 2026-04-23, Python ≥ 3.10). The ≥1B-parameter evidence bar is our own framing. Verification pass 2026-10-12: 27 claims checked, 1 corrected.)
