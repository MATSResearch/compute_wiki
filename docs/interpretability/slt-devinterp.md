---
tags:
  - interpretability
---

# Singular Learning Theory, Developmental Interpretability and Belief-State Geometry

Two theory-first interpretability agendas that do not start from activation dictionaries. **Singular learning theory (SLT) / developmental interpretability (devinterp)** reads model structure off the *geometry of the loss landscape* around trained weights, by sampling — the local learning coefficient, susceptibilities, Bayesian influence functions, patterning; the group behind it, Timaeus, now presents itself as **Resolution** (banner on timaeus.co, 2026-10-12), and the code stays at `timaeus-research/devinterp`. **Computational mechanics / belief-state geometry** (Simplex: Adam Shai, Paul Riechers) predicts the geometry of *activations* from the hidden structure of the data-generating process. Both have their strongest evidence on small models; their open problems are stated below with evidence bars.

## At a glance

| I want… | Use |
|---|---|
| A complexity / degeneracy measure for a checkpoint, or to detect when structure forms during training | **Local learning coefficient (LLC)** — `devinterp` `llc()` |
| Which components of a model respond to which kinds of data (data ↔ structure map) | **Susceptibilities** — `devinterp` `susceptibilities()` with weight restrictions per head/layer |
| Training-data attribution without inverting a Hessian, or per-token influence | **Bayesian influence function (BIF)** — `devinterp` `bif()`; compare against EK-FAC in [`data-attribution.md`](data-attribution.md) |
| Choose training data to produce (or prevent) a given internal structure | **Patterning** (Wang & Murfet, arXiv:2601.13548) — not among `devinterp`'s listed features; the primer's linearized solution uses the pseudo-inverse of the susceptibility matrix that `susceptibilities()` estimates |
| One document that derives susceptibilities, BIF and patterning together | **Primer**: Elliott & Murfet, arXiv:2605.07980 |
| Predict, from the data's hidden-state structure, what geometry the residual stream should have | **Belief-state geometry** (Shai et al., arXiv:2405.15943; code `adamimos/epsilon-transformers`) |
| Feature dictionaries over activations instead | SAEs — see [`saes.md`](saes.md) |

## What is singular learning theory, and why does it matter for interpretability?

Neural-network loss landscapes are *singular*: many parameter settings implement the same function, so minima are degenerate rather than isolated quadratic bowls, and classical Hessian-based reasoning breaks down. Singular learning theory (Watanabe, *Algebraic Geometry and Statistical Learning Theory*, 2009) characterizes Bayesian learning in this setting; its central quantity, the **learning coefficient** λ, measures how degenerate a minimum is (lower λ ≈ a simpler, more degenerate solution). Developmental interpretability applies this to training: track how degeneracy changes over training and treat changes as the formation of new internal structure.

- **Local learning coefficient (LLC)** — Lau, Furman, Wang, Murfet & Wei, *The Local Learning Coefficient: A Singularity-Aware Complexity Measure*, arXiv:2308.12108. Defines the LLC at a trained parameter and a scalable estimator based on stochastic-gradient Langevin dynamics (SGLD), applied to deep linear networks up to 100M parameters, ResNets and transformer language models. The estimator (Timaeus's sampling guide) is `λ̂ = nβ · (E_β[L_n(w)] − L_n(w₀))`: the average rise in loss when sampling a localized tempered posterior around the checkpoint w₀.
- **Stagewise development** — Hoogland, Wang, Farrugia-Roberts, Carroll, Wei & Murfet, *Loss Landscape Degeneracy and Stagewise Development in Transformers*, arXiv:2402.02364 (TMLR). Tracking the LLC over training of a transformer language model and an in-context linear-regression transformer divides training into distinct periods, whose boundaries coincide with significant changes in internal structure and input/output behaviour; the authors call this "suggestive evidence" that degeneracy and development are linked.

## What are susceptibilities?

A **susceptibility** is the first-order response of a posterior expectation to a small change in the data distribution — linear response theory from statistical mechanics, applied to a network treated as a Bayesian system.

- Baker, Wang, Hoogland & Murfet, *Structural Inference: Interpreting Small Language Models with Susceptibilities*, arXiv:2504.18274. Perturb the data (e.g. shift the Pile toward GitHub or legal text) and measure the change in an observable localized on one component (a head, a layer). Susceptibilities are estimated from local SGLD (stochastic-gradient Langevin dynamics) samples, factorize into signed per-token contributions usable as attribution scores, and stacked into a response matrix whose low-rank structure separates functional modules — multigram heads and induction heads — in a 3M-parameter transformer.
- Gordon, Baker, Wang, Snell, van Wingerden & Murfet, *Towards Spectroscopy: Susceptibility Clusters in Language Models*, arXiv:2601.12703. Upweight a token y in context x and cluster the responses: on Pythia-14M a conductance-based clustering found 510 interpretable clusters (grammar, code structure, mathematical notation), and 50% of the clusters matched sparse autoencoder (SAE) features.
- *Spectroscopy at Scale: Finding Interpretable Structure in Pythia-1.4B* (Timaeus blog, 2026-04-21; not peer reviewed): 57,236 susceptibility clusters in Pythia-1.4B, which the authors describe as more abstract than those found in Pythia-14M.

## Bayesian influence functions (BIF)

Kreer, Wu, Adam, Furman & Hoogland, *Bayesian Influence Functions for Hessian-Free Data Attribution*, arXiv:2509.26544 (ICLR 2026). The local BIF "replaces Hessian inversion with loss landscape statistics that can be estimated via stochastic-gradient MCMC sampling": the influence of training example i on query j becomes a posterior covariance (or correlation) between their losses under local SGLD sampling — the same sampler that estimates the LLC, with per-sample losses as the observable. Headline numbers: on CIFAR-10 retraining experiments (linear datamodeling score, LDS) the BIF matched EK-FAC (eigenvalue-corrected Kronecker-factored approximate curvature) — slightly below it on larger datasets (within error), slightly above on smaller ones; on the paper's one language-model LDS (Pythia-14M finetuned on WikiText) it scored **0.110 vs EK-FAC 0.221**. The full comparison against EK-FAC (layer coverage, cost, per-token influence) and the rest of the attribution toolchain are in [`data-attribution.md`](data-attribution.md).

## Patterning and the primer

- **Patterning** — Wang & Murfet, *Patterning: The Dual of Interpretability*, arXiv:2601.13548. Inverts susceptibilities: given a desired internal change, solve for the data reweighting that produces it. Shown on a small language model (reweighting along principal susceptibility directions accelerated or delayed formation of the induction circuit) and on a synthetic parentheses-balancing task, where targeting each solution's local learning coefficient (LLC) selected which of several perfect-training-accuracy algorithms the model learned. In the authors' words, "the same mathematical framework used to read internal structure can be inverted to write it."
- **Primer** — Elliott & Murfet, *Susceptibilities and Patterning: A Primer on Linear Response in Bayesian Learning*, arXiv:2605.07980 (34 pages). Derives susceptibilities from the fluctuation–dissipation theorem (a derivative of a posterior expectation equals a posterior covariance); shows per-sample-loss observables give the BIF's influence matrix, component-localized observables give the structural susceptibility matrix, and the pseudo-inverse of that matrix gives a linearized solution to patterning. Read it first if you want the theory in one place.

## devinterp (the library)

Aliases: `devinterp` on PyPI (v2.0.1, 2026-04-23; Python ≥3.10), `timaeus-research/devinterp` on GitHub (MIT; verified, last push 2026-04-23), docs `devinterp.timaeus.co`, "DevInterp", "Timaeus' SLT library".

**What it is.** Stochastic-gradient Langevin dynamics (SGLD) sampling with per-token loss storage (xarray / Zarr), and estimators built on it: `llc()` (local learning coefficient), `susceptibilities()`, `bif()` (Bayesian influence function), plus `create_param_masks` weight restrictions to sample over a subset of parameters (one head, one layer, a grouped-query-attention group, embeddings). Each analysis has a one-call entry point and a low-level `compute_*` function that reuses one sampling run. The README's quickstart computes LLCs and susceptibilities on Qwen2.5-0.5B (GPU required).

```python
# uv add devinterp — adapted from the README (its print lines dropped)
from devinterp.slt.llc import llc

result = llc(
    model=model,
    dataset=dataset,              # HuggingFace Dataset with "input_ids"
    observables={"train": dataset},
    lr=0.001,
    n_beta=30,
    num_chains=4,
    num_draws=200,
)
print(result["llc_mean"])         # scalar LLC
```

**When to use it:** LLC curves over training checkpoints; susceptibility or BIF analyses of an autoregressive language model you can run forward passes on many times.

**When *not* to use it:** you need a cheap, single-pass attribution or feature readout — every estimate here costs `num_chains × num_draws` forward passes over the observable datasets (plus burn-in); for many-query, sequence-level attribution the BIF paper itself says classical influence functions are more efficient. Non-language-model architectures need a custom `loss_fn` (or `evaluate` callable) — the v2 API assumes next-token cross-entropy on fixed-length `input_ids`.

**Pitfalls (with searchable symptoms):**
- **`ImportError: cannot import name 'estimate_learning_coeff_with_summary'`** — v2 (April 2026) replaced the v1 callback API (`estimate_learning_coeff_with_summary`, `LLCEstimator`, `SamplerCallback`, `sampling_method_kwargs={"nbeta": ...}`) with `llc()` / `compute_llc()` and `n_beta=`; the old name now appears only in the README's migration notes and docs, not in the source (GitHub code search, 2026-10-12). Older tutorials and papers' code target v1: port them, or pin `pip install "devinterp<2"`.
- **`DataLoader` no longer accepted.** v2 wants a Hugging Face `Dataset` with a uniform-length `"input_ids"` column.
- **Sampler hyperparameters decide the answer.** Timaeus's *Guide for Sampling Hyperparameter Selection* (2026-04-21) recommends RMSProp-preconditioned SGLD by default and diagnoses from the loss traces: **loss becomes inf/nan** or **loss trace has spikes** → decrease the step size ε (`lr`), and check whether nβ or the localization γ is too large; **loss trace goes below the loss at w₀** (which drives the LLC estimate negative, by the formula above) → increase γ and/or decrease nβ; **low signal-to-noise** → increase nβ (possibly lowering γ and ε) or the batch size. Sweep ε over orders of magnitude and report the chosen values; an LLC without its hyperparameters is not reproducible.
- **TransformerLens models.** `create_param_masks` supports 85+ Hugging Face model types and TransformerLens' `HookedTransformer`; TransformerLens 4.0 removed `HookedTransformer` (see [`mech-interp.md`](mech-interp.md)), so pass a Hugging Face model or stay on `transformer-lens<4`.

## Computational mechanics and belief-state geometry

Aliases: "computational mechanics", "comp mech", "belief state geometry", "mixed-state presentation", "MSP", "epsilon machine", "Simplex", Shai, Riechers.

- **Shai, Marzen, Teixeira, Gietelink Oldenziel & Riechers, *Transformers represent belief state geometry in their residual stream*, arXiv:2405.15943.** Train a transformer on sequences from a hidden Markov model (HMM); the theory of optimal prediction says the model should track a *belief state* (a probability distribution over the HMM's hidden states). A linear regression from residual-stream activations to the ground-truth belief states recovers the predicted geometry — a fractal one for the 3-state Mess3 process; for the Random–Random–XOR (RRXOR) process the 36 belief states (in a 4-simplex) were not recoverable from any single layer but were from the concatenation of all layers' residual streams. The belief states carry information about the entire future, beyond next-token prediction. Code: `adamimos/epsilon-transformers` (Adam Shai's repo; the paper's reproducibility appendix names `epsilon-transformers` training scripts but gives no URL. Verified, last push 2026-04-16; no license file per the GitHub API).
- **Piotrowski, Riechers, Filan & Shai, *Constrained belief updates explain geometric structures in transformer representations*, arXiv:2502.01954.** Mainly single-layer transformers on a family of HMMs: attention implements "constrained Bayesian belief updating", and the attention pattern, OV vectors and embeddings can be predicted in detail by modifying the optimal-prediction equations for attention's architectural constraints.
- **Shai et al., *Transformers learn factored representations*, arXiv:2602.02385.** When the data's latent factors are conditionally independent, transformers represent them in orthogonal subspaces (dimension growing linearly, not exponentially, with the number of factors), and they favour factoring early in training even when that costs predictive fidelity.

**How the two agendas differ.** Alexander Gietelink Oldenziel's *Simplex vs Timaeus: Round One* (LessWrong, 2026-10-01; an opinion post) contrasts them: SLT/devinterp is about weight space and training, belief-state geometry about activation space and inference; computational mechanics has a ground-truth data process to predict from, whereas the learning coefficient is known analytically only in a few simple cases and "we know this estimator can be very wrong" in his words. He calls the agendas neither competitors nor natural allies.

## Open problems and evidence bars

Most quantitative results above come from small models (a 3M-parameter transformer up to Pythia-1.4B, with qualitative BIF examples on Pythia-2.8B), synthetic HMM data, or one or two settings. The bars below are this wiki's statement of what would convince a skeptical reader that a method works more broadly. (Acronyms in the table: BIF, Bayesian influence function; LDS, linear datamodeling score; EK-FAC, eigenvalue-corrected Kronecker-factored approximate curvature; LLC, local learning coefficient; SAE, sparse autoencoder; HMM, hidden Markov model.) The Google DeepMind team's *A Pragmatic Vision for Interpretability* explicitly welcomes singular-learning-theory methods that verifiably work on a proxy task (see [`mech-interp.md`](mech-interp.md#agenda-framing-pragmatic-ambitious-and-open-problems)).

| Direction | Where the evidence stands | Evidence bar |
|---|---|---|
| **BIF for data attribution** | Matches EK-FAC on CIFAR-10 LDS; below EK-FAC on the paper's one language-model LDS (0.110 vs 0.221, Pythia-14M) | LDS at or above EK-FAC (or Bergson's best method) on a language-model attribution benchmark at matched compute, on a ≥1B-parameter model — Bergson's leaderboard harness in [`data-attribution.md`](data-attribution.md) is a ready setting |
| **Susceptibilities / spectroscopy** | Recovers known modules (induction heads) and clusters half of which match SAE features | A downstream proxy task the clusters solve better than an SAE or probe baseline (e.g. predicting which data change shifts a safety-relevant behaviour), not only cluster interpretability |
| **LLC as a developmental signal** | Stage boundaries coincide with structural changes on small transformers; estimator validity depends on hyperparameters | Report sampler diagnostics and hyperparameter sweeps; show the LLC recovers known analytic values where they exist and flags a transition *before* it is visible in behaviour on a held-out model |
| **Patterning** | Shifts induction-circuit timing and selects between algorithms on small/synthetic models | Steer which solution a pretrained-scale model learns on a safety-relevant generalization, against a matched-compute data-filtering or reweighting baseline |
| **Belief-state geometry** | Precise predictions on HMM-generated data; factored-representation results on synthetic processes | Predict, before looking, a geometric property of a model trained on natural language and confirm it — porting the theory beyond HMMs is the named challenge |

### Machine-checked SLT results: the Timaeus `laplace` Lean formalization

Aliases: laplace, Lean formalization of the susceptibility primer, Laplace asymptotics in Lean, Statements.lean / Solutions.lean.

`timaeus-research/laplace` is "a Lean 4 + Mathlib formalisation of the Laplace asymptotics of Gibbs expectations, covariances and susceptibilities from the SLT Susceptibility Primer (Elliott & Murfet, 2026)" (SLT = singular learning theory). Its README reports "~68k lines of Lean 4 + Mathlib" and "0 sorries, 0 axioms, 0 `native_decide`", and traces each of seven headline theorems to its source: the primer's covariance and expectation lemmas (`lem:laplace_cov`, `lem:laplace_exp`, `lem:laplace_cov2`), an anharmonic covariance limit, and new results including a degenerate (singular-regime) moment asymptotic for a separable potential. The README is explicit about gaps, for example "limit only — the primer's `O(t⁻³)` rate is not pinned". Statements are kept in `Statements.lean` and checked against the proofs in `Solutions.lean` with comparator on every non-documentation push.

**Status, as of 2026-10-14:** the repository is **archived**; its README says it "was merged into the resolution monorepo on 2026-09-27", which is not publicly visible, and the repository has no licence. Read it as a worked example of the layout and of how to state what a formalization leaves out; the wiki's reusable version of the layout is `project_templates/lean_formalization/` (see [`lean-formalization.md`](../engineering/lean-formalization.md#check-every-push-in-ci-the-statementslean-and-solutionslean-pattern)).

**Open problem / evidence bar:** most of the formalized results concern nondegenerate minima, where Laplace's method applies, plus one separable degenerate potential. A machine-checked statement about the learning coefficient or a susceptibility at a genuinely singular minimum of a model-like loss, with the gap to the informal claim written down, would extend what is checked rather than only what is estimated.

## Cross-references

- Lean tooling and the evidence ladder for checked proofs: [`lean-formalization.md`](../engineering/lean-formalization.md).
- Data attribution toolchain and benchmarks (EK-FAC, kronfluence, Bergson, LDS): [`data-attribution.md`](data-attribution.md).
- Activation-dictionary methods and the superposition picture: [`saes.md`](saes.md).
- Circuit discovery, MIB and agenda framing (pragmatic vs ambitious, AlgZoo): [`mech-interp.md`](mech-interp.md).

---

Last verified: 2026-10-14. 2026-10-14: `devinterp` re-checked (still v2.0.1 on PyPI and GitHub, last push 2026-04-23; no API change); `timaeus-research/laplace` README (archive notice, theorem table, status counts), `comparator.json` and workflow read via the GitHub API, `resolutionorg/resolution` returns 404. Earlier, 2026-10. arXiv metadata and abstracts for 2308.12108, 2402.02364, 2504.18274, 2601.12703, 2509.26544, 2601.13548, 2605.07980, 2405.15943, 2502.01954 and 2602.02385 fetched via the arXiv API on 2026-10-12; the BIF LDS numbers (CIFAR-10 comparison, Pythia-14M table, Pythia-2.8B appendix) read from the arXiv HTML full text of 2509.26544v2, and the Mess3/RRXOR details from the HTML of 2405.15943v3 (which does not link `adamimos/epsilon-transformers`; its appendix names `legacy/epsilon-transformers/` scripts only). `devinterp` README, PyPI metadata (2.0.1, 2026-04-23) and source tree checked via GitHub/PyPI; the v1-name removal via GitHub code search. Timaeus blog posts (*Spectroscopy at Scale*, *Guide for Sampling Hyperparameter Selection*, both 2026-04-21) and the "Timaeus is now Resolution" banner read from timaeus.co; *Simplex vs Timaeus: Round One* (LessWrong Fs4inpM72PeH4hsAv) read via GraphQL. The evidence bars are this wiki's proposals, not the papers' authors'. The devinterp snippet is copied from the README, not run. Verification pass 2026-10-12: 62 claims checked, 1 corrected (the paper does not link the epsilon-transformers repo; checked against the 2405.15943 PDF, HTML and abs page).
