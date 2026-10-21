---
tags:
  - evaluation
  - engineering
---

# Statistics for LLM Evals

The eval-specific layer of statistics: what changes when the "data" is a
benchmark of shared prompts, scored for many models, sometimes by a large
language model (LLM) judge, often with several items sharing one passage or
image. The general layer (McNemar's test, Wilson intervals, the bootstrap,
multiple comparisons, Bayesian reporting, power) is
[`statistics.md`](../engineering/statistics.md); running evals and validating
judges is [`evals.md`](evals.md) and
[`inspect-ecosystem.md`](inspect-ecosystem.md).

All versions and dates below are as of 2026-10-14 unless a later date is given.

## At a glance

| I want to... | Use | Section |
|---|---|---|
| Error bars on a benchmark where several items share a passage, image, document or task | Clustered standard error: Inspect `stderr(cluster=...)`, `ci_wilson(cluster=...)` | [Clustered items](#clustered-items-passages-images-problem-sheets-and-shared-tasks) |
| Know whether a benchmark can resolve the gap between two models at all | Paired required sample size N\* and the resolution ratio q = N/N\* | [Resolution ratio](#paired-comparisons-can-this-benchmark-resolve-the-gap-the-resolution-ratio-q) |
| Plan how many shared prompts a paired comparison needs | Paired-difference variance, not the unpaired formula times (1 − ρ) | [Resolution ratio](#paired-comparisons-can-this-benchmark-resolve-the-gap-the-resolution-ratio-q) |
| Compare many models on one or several benchmarks with multiplicity correction | `evalci.multi_compare(df, correction="holm")` | [Many comparisons](#many-models-at-once-leaderboards-and-model-by-benchmark-grids-evalci) |
| Get a valid interval from many LLM-judge labels plus a small human-labelled subset | Prediction-powered inference, `ppi_py.ppi_mean_ci` | [PPI](#llm-judge-labels-plus-a-small-human-labelled-subset-prediction-powered-inference-ppi) |
| One model for "many models × many items" that handles item difficulty and clustering | Bayesian crossed random effects (Bambi) or HiBayES on Inspect logs | [Crossed random effects](#many-models-many-items-a-crossed-random-effects-model-bambi) |
| Find saturated, broken or uninformative benchmark items; build a small subset | Item response theory (IRT): py-irt; tinyBenchmarks | [IRT](#which-items-carry-the-signal-item-response-theory-py-irt-tinybenchmarks) |
| Stop an eval early once the answer looks clear | Anytime-valid confidence sequences, or a Bayesian stopping rule (optstop) | [Stopping early](#stopping-an-eval-early-when-run-until-it-looks-significant-is-legitimate) |
| Tell whether an agent-eval score change is the agent or the scorer | Re-score unchanged trajectories, then repeated paired runs (TRACE) | [Agent evals](#agent-evals-rerun-flips-and-scorer-changes) |

---

## Clustered items: passages, images, problem sheets and shared tasks

Many benchmarks have several samples that share one underlying unit: a reading
passage with eight questions, an image with several questions, a problem sheet,
a user task crossed with several prompt injections, or several epochs of the
same prompt analysed as separate rows. Outcomes within a unit are correlated: a model that misreads a
passage tends to miss all of its questions. The plain standard error (SE),
`stderr()` in Inspect, assumes every sample is independent and therefore
understates the uncertainty. The point estimate (accuracy) is unchanged; only
the error bar is wrong.

### How big is the error?

A census of `inspect_evals` tasks, posted as issue
[UKGovernmentBEIS/inspect_evals#2605](https://github.com/UKGovernmentBEIS/inspect_evals/issues/2605)
(opened 2026-10-01, still open as of 2026-10-14), found 21+ evals reporting a
plain `stderr()` over clustered samples, among them `lingoly_too`, the AGIEval
reading and logic tasks (`agie_lsat_rc`, `agie_lsat_ar`, `agie_sat_en`,
`agie_logiqa_en`), several `infinite_bench` tasks, the CyberSecEval tasks
`cyse2_prompt_injection` / `cyse3_visual_prompt_injection` /
`cyse4_malware_analysis`, `bbq`, `macbench`, `boolq`, `hellaswag`, `lab_bench`,
`frontier_cs`, `agentdojo`, `worldsense`, `vqa_rad` and
`zerobench_subquestions`. Plain versus clustered SE on the same scores, both
computed with Inspect's own metrics (from the issue):

| Eval (cluster unit) | Plain SE | Clustered SE | Ratio |
|---|---|---|---|
| `lingoly_too` (82 problem sheets) | 0.0114 | 0.0330 | 2.89× |
| `agentdojo` utility (by user task) | 0.0125 | 0.0334 | 2.68× |
| `agentdojo` attack success (by injection task) | 0.0070 | 0.0177 | 2.51× |
| `agie_lsat_rc` (40 passages) | 0.0149 | 0.0164 | 1.10× |

The issue's summary of the first row: "On `lingoly_too`, 1203 samples carry
roughly the information of 144 independent ones." The **effective sample
size** is n × (SE_plain / SE_clustered)², here 1203 × (0.0114 / 0.0330)² ≈ 144.
The correction depends on cluster size and on distance from the ceiling: a
model at 94% on LSAT reading comprehension has little room for its misses to
cluster within a passage, hence 1.10×.

A tip worth taking from this: if you compare models on an `inspect_evals`
task, check whether the task's own metrics cluster before trusting its
reported error bars. The issue says DocVQA, DROP, MGSM, RACE-H and SQuAD
already do.

### Clustered error bars in Inspect

Inspect AI (`inspect-ai` on PyPI, `UKGovernmentBEIS/inspect_ai`, UK AI
Security Institute) has three metrics with a `cluster=` argument. Each takes
the name of a key in `Sample.metadata` that identifies the shared unit:

| Metric | Since | Returns | Use for |
|---|---|---|---|
| `stderr(cluster="key")` | v0.3.64 (2025-02-14) | clustered SE of the mean | the error bar most tables show |
| `ci(level=0.95, method="t", cluster="key")` (or `method="bootstrap"`) | 0.3.260 (2026-08-21) | `{"lower", "upper"}` | graded / continuous scores. `"t"` uses `clusters − 1` degrees of freedom; `"bootstrap"` resamples whole clusters |
| `ci_wilson(level=0.95, cluster="key")` | 0.3.262 (2026-09-02) | `{"lower", "upper"}`, always inside [0, 1] | 0/1 scores such as accuracy, refusal rate, attack success rate |

`ci_wilson` with `cluster=` uses a Korn–Graubard effective sample size
(p̂(1 − p̂) divided by the clustered variance of the mean, capped at n) and a
Student-t critical value with `clusters − 1` degrees of freedom. The latest
release is 0.3.282 (2026-10-19), which needs Python ≥3.11.

```python
from inspect_ai.dataset import Sample
from inspect_ai.scorer import accuracy, ci_wilson, stderr, scorer

# Put the shared unit's id on every sample.
Sample(input=question, target=answer, metadata={"passage_id": passage_id})

@scorer(metrics=[accuracy(), stderr(cluster="passage_id"),
                 ci_wilson(cluster="passage_id")])
def my_scorer():
    ...
```

If the dataset has no id for the shared unit, a hash of the passage or image
works (the issue does this for `agie_lsat_rc`). Multi-epoch runs need no
cluster key for these metrics: Inspect normally computes metrics on a reduced
view in which each sample's epoch scores are combined into one score (`mean`
by default).

### Limits of the Inspect metrics

- **One key only.** A crossed design (user task × injection task in
  `agentdojo`, prompt × image in `cyse3_visual_prompt_injection`) needs a
  two-way clustered SE, which is larger still. Clustering on one factor already
  gives the ratios above. For a full crossed model, see
  [Many models × many items](#many-models-many-items-a-crossed-random-effects-model-bambi).
- **Few clusters.** `stderr(cluster=)` returns 0.0 with a single cluster, and
  with a handful of clusters the t degrees of freedom collapse. Forty passages
  is fine; four task families is not a basis for a clustered interval.
- **`ci(method="t")` on binary scores near 0 or 1** can give bounds outside
  [0, 1]. `ci_wilson` cannot.

When samples really are independent items, plain `stderr()` is correct and
clustering adds nothing.

Outside Inspect, the same correction is a bootstrap over clusters (resample
passages, carrying their questions along; see
[Bootstrap the right unit](../engineering/statistics.md#bootstrap-the-right-unit))
or `evalci.cluster_ci(scores, clusters)`.

---

## Paired comparisons: can this benchmark resolve the gap? The resolution ratio q

Two models scored on the **same** prompts form a paired comparison. The
question to ask before publishing "A beats B by 0.8 points" is whether a
benchmark of this size could detect a gap that small at all. Kotawala,
*Resolution Diagnostics for Paired LLM Evaluation*
([arXiv:2605.30315](https://arxiv.org/abs/2605.30315), 2026-05-28; ICML 2026
Workshop on Hypothesis Testing) packages this as three numbers:

- **N\***, the number of paired prompts needed to detect a gap δ at
  (α, 1 − β), for example (0.05, 0.8);
- the **minimum detectable effect (MDE)** at the current N;
- the **resolution ratio q = N / N\***. The gap is resolvable at that operating
  point when q ≥ 1.

For a single pair, q is a monotone transform of the paired Wald statistic T:
q ≥ 1 exactly when |T| ≥ z₀.₉₇₅ + z₀.₈ ≈ 2.80. So q adds no information beyond
the p-value; what it adds is interpretation ("this benchmark is about half the
size this gap needs") and a scale that composes with multiplicity correction,
clustering and sequential testing. The paper's findings at (0.05, 0.8):

- 11 of 40 Open LLM Leaderboard v1 pairwise comparisons, and 4 of 9 MMLU-Pro
  top-10 adjacent-rank pairs (N = 12,032 items), are unresolved.
- With MMLU-Pro's 14 subject categories treated as clusters, the unresolved
  count rises to 6 of 9.
- The paired McNemar required N is a median 2.15× smaller than the unpaired
  formula on the same data (IQR 1.60–2.75), close to the textbook 1/(1 − ρ),
  where ρ is the correlation between the two models' per-prompt correctness.

### Computing N\* and q

The paired formula uses the variance of the per-prompt **difference**
D = score_A − score_B: N\* = (z₁₋α/₂ + z₁₋β)² · σ_D² / δ². For 0/1 scores,
σ_D² = p_A(1 − p_A) + p_B(1 − p_B) − 2ρ·√(p_A(1 − p_A)·p_B(1 − p_B)) (the
paper's Eq. 5, which gives the McNemar–Connor required count). The sample
variance of the observed differences estimates the same quantity. Illustrative
code written from the paper's equations (not copied from its package):

```python
import numpy as np
from scipy.stats import norm

Z = norm.ppf(1 - 0.05 / 2) + norm.ppf(0.80)       # ≈ 2.80 for (alpha, power) = (0.05, 0.8)

def n_star_paired(d, delta=None):
    """Paired prompts needed. d: per-prompt score differences A - B (same prompts)."""
    delta = d.mean() if delta is None else delta    # plug in the gap you want to detect
    return (Z * d.std(ddof=1) / delta) ** 2

def n_star_binary(p_a, p_b, rho):
    """Planning version for 0/1 scores, before any data (paper's Eq. 5)."""
    va, vb = p_a * (1 - p_a), p_b * (1 - p_b)
    var_d = va + vb - 2 * rho * np.sqrt(va * vb)
    return Z**2 * var_d / (p_a - p_b) ** 2

d = scores_a - scores_b                             # shape (n_prompts,)
q = len(d) / n_star_paired(d)                       # q >= 1: resolvable at (0.05, 0.8)
print(f"N* = {n_star_paired(d):.0f}, q = {q:.2f}")
print(n_star_binary(0.65, 0.60, 0.30))              # ≈ 1028, the paper's worked example
```

The paper's code is `ananykotawala/llm-power` on GitHub (MIT, as of
2026-10-14 not on PyPI and with no releases; the package name inside is
`llm-power`). Its appendix lists functions such as
`parametric_required_n_paired_binary(p1, p2, rho)` and
`required_n_mcnemar(n_ab, n_ba, n_observed)`.

### The (1 − ρ) shortcut

A common shortcut is to take an unpaired per-arm sample size and multiply it by
(1 − ρ). The paper shows that this is off by about a factor of two in the
close-comparison regime when the per-arm number is K/h², with
K = (z₁₋α/₂ + z₁₋β)². The paper attributes a K/h² output to Cohen's 1988
textbook formula, G\*Power 3.1 and R's `pwr`. That attribution looks doubtful
at least for `pwr`: the source of `pwr::pwr.2p.test` (pwr 1.3-0) computes power
from h·√(n/2), which gives 2K/h² per group (about 1,470 in the paper's worked
example), not the 736 the paper lists. `statsmodels`' `NormalIndPower` also counts both arms
(2K/h²), so its output times (1 − ρ) lands near the right answer (1,030 versus
1,028 in the worked example). Rather than working out which convention
a given calculator uses, it is simpler to compute N\* from σ_D² as above.

### Reading q honestly

- **q < 1 does not mean the models are equal.** It means the benchmark at this
  size lacks the target resolution for a gap of this magnitude. To argue "no
  meaningful difference", use an equivalence test or a region of practical
  equivalence (ROPE); see
  [Arguing that there is no effect](../engineering/statistics.md#arguing-that-there-is-no-effect).
- **Prospective versus diagnostic.** Plug in a pre-specified δ to plan a
  benchmark; plug in the observed gap to diagnose a published ranking. Using
  "power at the observed effect" to argue a ranking is true or false is the
  misuse the paper explicitly avoids.
- **Clustered items** inflate N\*: apply the design effect from
  [Clustered items](#clustered-items-passages-images-problem-sheets-and-shared-tasks).
- **Different prompt sets** for A and B make the comparison unpaired; the
  unpaired `NormalIndPower` calculation in
  [How many samples do I need?](../engineering/statistics.md#how-many-samples-do-i-need)
  is the right one there.

---

## Many models at once: leaderboards and model-by-benchmark grids (evalci)

**evalci** (`evalci` on PyPI, `Shreyaskc/evalci` on GitHub, Shreyas K
Chandrahas; methods paper [arXiv:2607.04429](https://arxiv.org/abs/2607.04429),
2026-07-05) turns a per-item results table into "Δ, CI, paired p" lines, with
Holm or Benjamini–Hochberg correction across many pairs. It offers `ci`
(Wilson, Clopper–Pearson, bootstrap), `compare` (paired permutation, McNemar,
bootstrap), `power`, `multi_compare`, `cluster_ci` and `report`, plus adapters
for lm-evaluation-harness and HELM output. Runtime dependencies are numpy,
scipy and pandas. Its tests check the intervals, McNemar and the corrections
against `statsmodels`, and the permutation test against exact enumeration.

```python
import evalci
result = evalci.compare(model_a_scores, model_b_scores, paired=True, method="permutation")
evalci.report(result)   # 'Δ=…, 95% CI […], paired permutation p=…, n=…'

# long table: item_id, model, score, [subset], [sample_idx]
table = evalci.multi_compare(df, correction="holm")
print(evalci.report(table, format="markdown"))
```

The paper's motivating example: re-analysing a public nine-model MMLU
comparison, 3 of the 8 adjacent leaderboard gaps are not significant after
correcting for the 36 pairwise comparisons the ranking implies.

Which family size to correct for is a choice worth stating. A ranking of k
models implies k(k − 1)/2 pairwise claims; reporting only adjacent ranks is
k − 1. Kotawala (arXiv:2605.30315) uses m = 9 adjacent pairs for the MMLU-Pro
top 10 and notes that the all-pairs convention, m = 45, inflates N\* by about
2.14×.

**When not to use it.** When results already live in Inspect logs, the Inspect
metrics in [Clustered items](#clustered-items-passages-images-problem-sheets-and-shared-tasks)
avoid an extra dependency. The project is young (3 stars, one author) and PyPI
lags GitHub (PyPI `evalci` 0.1.0 versus GitHub tag v0.1.2, both 2026-07-05), so
for a high-stakes claim it is worth reading the code or cross-checking one
comparison against `statsmodels`.

---

## LLM-judge labels plus a small human-labelled subset: prediction-powered inference (PPI)

An LLM judge scoring thousands of transcripts has its own error rate, and that
error is biased, not just noisy: a judge that under-flags subtle sabotage
shifts the estimated rate. Reporting judge–human agreement on a subset is
standard. **Prediction-powered inference (PPI)** goes a step further and uses
the subset to correct the estimate.

**ppi_py** (`ppi-python` on PyPI, `aangelopoulos/ppi_py` on GitHub, Angelopoulos
et al., *Prediction-Powered Inference*,
[arXiv:2301.09633](https://arxiv.org/abs/2301.09633); PyPI 0.2.3, 2024-12-22,
repo active in 2026) takes three arrays:

- `Y`: gold (human) labels on a small labelled subset;
- `Yhat`: the judge's labels on the **same** subset;
- `Yhat_unlabeled`: the judge's labels on everything else.

It returns a confidence interval for the true mean (or median, quantile, or
regression coefficient) that stays valid however biased the judge is. When the
judge agrees well with humans, the interval is much tighter than a gold-only
interval. With the default `lam=None`, `ppi_mean_ci` estimates a power-tuning
weight from the data (PPI++, [arXiv:2311.01453](https://arxiv.org/abs/2311.01453)).
`lam=1` is plain PPI, and `lam=0` recovers the classical interval on the gold
labels alone.

```python
# pip install ppi-python   (uv add ppi-python)
import numpy as np
from ppi_py import ppi_mean_ci

# 0/1 "unsafe" labels. Y and Yhat cover the SAME randomly chosen transcripts.
Y = human_labels[labelled_idx]
Yhat = judge_labels[labelled_idx]
Yhat_unlabeled = judge_labels[unlabelled_idx]

lo, hi = ppi_mean_ci(Y, Yhat, Yhat_unlabeled, alpha=0.05)   # default alpha=0.1 is a 90% CI
print("unsafe rate, 95% CI:", lo, hi)
```

Note the default `alpha=0.1`, which gives a **90%** interval. Set
`alpha=0.05` to match the 95% intervals elsewhere in a paper.

**The condition that matters.** The labelled subset has to be a **random
sample** from the same pool as the judge-only items. Hand-labelling only the
transcripts the judge flagged, or only the interesting ones, voids the
guarantee. ppi_py has covariate-shift and label-shift variants, but they need
the shift to be modelled. PPI also needs some gold labels: with none, nothing
here applies.

Tools that produce the inputs (hand-labelled validation sets for Inspect Scout
scanners) and model grader effects directly (HiBayES) are covered in
[`evals.md`](evals.md) and [`inspect-ecosystem.md`](inspect-ecosystem.md).

---

## Many models, many items: a crossed random-effects model (Bambi)

A results table with M models × I items (and maybe passages, task families or
epochs) has several sources of variation: model ability, item difficulty and
cluster effects. A **generalised linear mixed model (GLMM)** with a fixed
effect per model and a random intercept per item models item difficulty
explicitly, so model comparisons are automatically paired. Adding a random
intercept per passage or task family handles clustering in the same model.

**Bambi** (`bambi` on PyPI, `bambinos/bambi` on GitHub; 0.21.0, 2026-09-10;
requires Python 3.12+) fits these with formula syntax on top of PyMC.
Illustrative adaptation (the formula pattern follows Bambi's crossed
random-effects and hierarchical binomial example notebooks; this eval version
is not copied from the docs):

```python
import arviz as az
import bambi as bmb

# df: one row per (model, item) with a 0/1 integer column `correct`;
# optionally a `passage` column for clustered items.
m = bmb.Model("correct ~ 0 + model + (1|item) + (1|passage)", df, family="bernoulli")
idata = m.fit()                                   # NUTS via PyMC
print(az.summary(idata, ci_prob=0.95, ci_kind="hdi"))   # ArviZ 1.x; check r_hat ≈ 1.00 and ESS
```

The comparison of two models is the posterior of the difference between their
`model` coefficients (on the logit scale). Report its highest-density interval
(HDI) and, if the claim is "no difference", compare it with a region of
practical equivalence (ROPE). Report `r_hat` and the effective sample size
(ESS); a model that has not converged has not estimated anything.

**HiBayES** (UK AI Security Institute, `UKGovernmentBEIS/hibayes`) fits
hierarchical GLMs directly from Inspect logs with NumPyro, configured by YAML.
Its LLM-as-judge examples model grader effects on 0–10 judge scores. It needs
Python 3.12+, is not on PyPI, and its docs say it is in development. Details in
[`evals.md`](evals.md).

**When not to use it.** For one headline comparison of two models, McNemar's
test or a paired bootstrap is simpler and needs no Markov chain Monte Carlo
(MCMC) diagnostics. For very large tables (tens of thousands of items × many
models), NUTS sampling gets slow; the clustered metrics or a bootstrap may be
the practical choice.

---

## Which items carry the signal? Item response theory (py-irt, tinyBenchmarks)

Not every benchmark item is equally informative. **Item response theory (IRT)**
fits, from a 0/1 response matrix of subjects (here, models) × items, a latent
ability per model plus a difficulty (and, in the 2PL/4PL models, a
discrimination) per item. Uses in eval work:

- **Saturated items**: items every model gets right, or that no model gets
  right, carry no information about differences between models.
- **Broken items**: an item with negative discrimination (stronger models do
  worse) is often mislabelled. It is worth reading these before trusting the
  benchmark.
- **Subset selection**: a small set of informative items can estimate the full
  score. This is the tinyBenchmarks idea below.

**py-irt** (`py-irt` on PyPI, `nd-ball/py-irt` on GitHub, John Lalor and
collaborators; 0.7.1, 2026-03-24) fits 1PL (Rasch), 2PL and 4PL models by
variational inference on PyTorch and Pyro. The README describes it as "research
code". **Its `requires_python` is `<3.12,>=3.9`**, so it needs its own uv
environment on Python 3.11 if the project is on 3.12 (for example
`uv venv --python 3.11`). Input is JSON lines, one subject per line:

```text
{"subject_id": "model-a", "responses": {"q1": 1, "q2": 0, "q3": 1}}
{"subject_id": "model-b", "responses": {"q1": 1, "q2": 1, "q3": 0}}
```

```bash
py-irt train 2pl responses.jsonlines outputs/run_.../irt-2pl/
```

The EACL 2024 IRT4NLP tutorial
(<https://eacl2024irt.github.io/notebooks/2_IntroToIRT_jupyter.html>) shows
the Python API. Background: Rodriguez et al., *Evaluation Examples Are Not
Equally Informative: How Should That Change NLP Leaderboards?* (ACL 2021).

**tinyBenchmarks** (`felipemaiapolo/tinyBenchmarks` on GitHub, Maia Polo et
al., [arXiv:2402.14992](https://arxiv.org/abs/2402.14992); install with
`pip install git+https://github.com/felipemaiapolo/tinyBenchmarks`, not on
PyPI) publishes 100-item versions of MMLU, GSM8K, ARC, HellaSwag, TruthfulQA,
Winogrande and AlpacaEval 2.0, chosen with IRT, plus an estimator
(`tb.evaluate(y, "mmlu")`) that maps a model's 100 responses to an estimated
full-benchmark score. Its README reports average absolute estimation errors of
roughly 0.01–0.03 (for MMLU, 0.024 with the IRT estimator and 0.016 with
gp-IRT).

**When not to use them.** With few models (a rough rule of thumb is fewer than
about 20 subjects), item parameters are poorly identified: there are too few
"test takers" to learn which items discriminate. A 100-item subset with ±2
points of estimation error cannot resolve a 1-point gap between close models;
use it for cheap tracking during development, and the full benchmark for the
claim. tinyBenchmarks' items were selected using the models of its time, so it
is worth checking the estimate against a full run for a model family far
outside that population.

---

## Stopping an eval early: when "run until it looks significant" is legitimate

Checking a p-value after every batch and stopping when it dips below 0.05
inflates the false-positive rate well above 5%. Adding samples until a result
"looks significant" is the sequential version of trying many prompt sets.

Two legitimate ways to stop early:

- **Anytime-valid inference (frequentist).** A *confidence sequence*
  (Howard, Ramdas, McAuliffe and Sekhon, *Time-uniform, nonparametric,
  nonasymptotic confidence sequences*, Annals of Statistics 2021) or an
  *e-process* is valid at every sample size at once, so you may look after
  every item and stop whenever it excludes zero. The price is a wider boundary.
  In Kotawala (arXiv:2605.30315, §6.5 and Appendix C), the anytime-valid
  threshold inflated N\* by 2.15× at MMLU-Pro's N = 12,032 and flipped one more
  adjacent pair to unresolved (5 of 9). In simulations calibrated to two ARC
  pairs, the expected stopping time was 1.84–2.32× the fixed-n N\*.
- **A Bayesian stopping rule.** **optstop** (UK AI Security Institute,
  `UKGovernmentBEIS/optstop`; Pilditch, *Knowing When to Stop: Bayesian
  Optimal Stopping for LLM Evaluations*,
  [arXiv:2608.14425](https://arxiv.org/abs/2608.14425), 2026-08-14) decides
  per item and per grouping (for example model × task) when more **epochs**
  stop changing a hierarchical credible interval. It runs post hoc on a
  results table or live in Inspect (attached as `Task(early_stopping=...)`).
  Its guarantee is about credible intervals, not frequentist Type I error. Its
  README says the intervals are well calibrated for groupings with 50+ items
  and performance between 0.2 and 0.8, and may under-cover near 0% or 100%.
  Rare-event safety rates near zero are exactly where early stopping misses
  things. Setup and the `shadow_mode=True` dry run are in
  [`evals.md`](evals.md).

If neither fits, fix N in advance (see
[Paired comparisons](#paired-comparisons-can-this-benchmark-resolve-the-gap-the-resolution-ratio-q))
and look once.

---

## Agent evals: rerun flips and scorer changes

Agentic evals add two sources of variation that a static benchmark lacks: the same agent on the same task can succeed on one run and fail on the next, and the verifier or judge can change what it rewards when you change something unrelated about the harness.

**How big.** Gaonkar, "TRACE: Diagnosing Verifier Brittleness in Agentic Evaluation" (arXiv:[2610.11678](https://arxiv.org/abs/2610.11678), 2026-10-08), on τ²-bench tasks with four LLM agents: "Identical reruns flip 15-36% of task outcomes, so single-run comparisons cannot separate presentation effects from run-to-run variation." Two frontier LLM judges were each consistent when a fixed trajectory was presented differently, "yet disagree with each other on 57% of the same records, largely because one grades procedure rather than outcome." In a synthetic suite, renaming tools lowered a scripted agent's score by 0.250 although it performed exactly the same operations. Jia et al. (arXiv:[2610.24048](https://arxiv.org/abs/2610.24048)) report reruns of thinking agents on AgentDojo disagreeing with single-run labels up to 35% of the time.

**Protocol (TRACE's, in short).** When a harness change (tool names, output format, prompt) moves a score: (1) re-score the **unchanged** trajectories with the changed scorer — if the gap appears there, the scoring rule moved, not the agent; (2) run each condition several times per task and compare **paired** per-task success rates, not single runs; (3) check whether the agent's behaviour actually changed in the transcripts. For the paired comparison itself, use the methods in [Paired comparisons](#paired-comparisons-can-this-benchmark-resolve-the-gap-the-resolution-ratio-q), with the task (not the run) as the unit, and cluster repeated runs by task ([Clustered items](#clustered-items-passages-images-problem-sheets-and-shared-tasks)).

**When not to bother:** deterministic, single-turn scoring with temperature 0 and a fixed exact-match scorer, where reruns do not vary (check once that they don't).

---

## Pitfalls, with the symptoms you'd actually see

- **``ValueError: Sample <id> has no cluster metadata. To compute `stderr` with
  clustering, each sample metadata must have a value for 'passage_id'``.** Some
  samples lack the cluster key (`None` and NaN count as missing). Inspect raises
  rather than dropping them. Add the key to every `Sample.metadata`.
- **``ValueError: Computing `ci_wilson` with clustering requires at least two
  clusters``.** The key has one value for every sample, often a constant
  placeholder.
- **``ValueError: Sample <id> has score value 2.0. `ci_wilson` treats the mean
  score as a binomial proportion, so all score values must be between 0 and
  1.``** `ci_wilson` is for scores in [0, 1]. Use `ci()` for graded scores.
- **`ImportError: cannot import name 'ci_wilson' from 'inspect_ai.scorer'`.**
  Inspect is older than 0.3.262 (`ci` needs 0.3.260). Upgrade, or keep
  `stderr(cluster=...)`, which is much older.
- **A leaderboard gap with p = 0.049 and q ≈ 0.5.** Nominally significant, but
  only halfway to the (0.05, 0.8) resolution target: the HellaSwag pair in
  arXiv:2605.30315 §1. One more arbiter (the exact McNemar test gave p = 0.054)
  flips it.
- **"My PPI interval is barely tighter than the gold-only one."** The judge
  agrees poorly with the human labels, so the PPI++ weight (`lam=None`) shrinks
  towards the classical interval. Check judge–human agreement on the labelled
  subset; improving the judge helps more than adding unlabelled items. Also
  check `alpha`: the default 0.1 gives a 90% interval.
- **py-irt will not install on Python 3.12 or later.** Its `requires_python` is
  `<3.12`; uv reports that no compatible version exists. Use a separate
  Python 3.11 environment for the IRT fit.

## Where this connects

- General tests, intervals, multiple comparisons, Bayesian reporting and power:
  [`statistics.md`](../engineering/statistics.md).
- Running evals, judge validation, HiBayES and optstop setup:
  [`evals.md`](evals.md); Inspect tooling around the core framework:
  [`inspect-ecosystem.md`](inspect-ecosystem.md).
- Plotting these numbers: [`visualization.md`](../engineering/visualization.md)
  and [`research-plots.md`](../engineering/research-plots.md).
- The MATS evals template's scorers:
  `project_templates/evals/components/src/eval_components/scorers.py`.

---

Last verified: 2026-10-20 (added the agent-eval rerun section from arXiv 2610.11678 and 2610.24048 abstracts; Inspect latest release 0.3.282 from the CHANGELOG). Earlier: 2026-10-14. Drafted by Claude; pending MATS research-staff
review. Sources checked: Inspect `src/inspect_ai/scorer/_metrics/std.py` and
CHANGELOG (`stderr(cluster=)` v0.3.64, `ci()` 0.3.260, `ci_wilson()` 0.3.262,
latest 0.3.280); inspect_evals issue #2605 (body and tables); arXiv:2605.30315
full text (Eqs. 2–5, Definition 1, Table 1, §6.2–6.5, Appendix C, J) and repo
`ananykotawala/llm-power` (incl. `appendix_table1/README.md`); R `pwr` 1.3-0 `pwr.2p.test` source; evalci README and PyPI; ppi_py README and
`ppi_mean_ci` source; Bambi README (Python 3.12+); py-irt README, CLI and test
fixture; tinyBenchmarks README; optstop README; arXiv metadata for 2607.04429,
2301.09633, 2402.14992 and 2608.14425.
