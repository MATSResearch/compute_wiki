---
tags:
  - engineering
---

# Statistics for Safety Experiments

How to decide whether a result is real. Aimed at the analyses MATS fellows
actually run: comparing a model against a baseline, comparing an intervention
(steering vector, prompt, fine-tune) against no intervention, and sweeping a
knob across settings.

Different from the short [Statistical reporting patterns](code-recipes.md#statistical-reporting-patterns)
section in [`code-recipes.md`](code-recipes.md), which is the copy-paste layer.
This doc is the *decide-what-to-run* layer: which test, on which unit, and what
usually goes wrong.

The libraries throughout are **SciPy** (`scipy` on PyPI, `scipy.stats`),
**statsmodels** (`statsmodels` on PyPI), and **NumPy** (`numpy`). Nothing here
needs anything heavier.

## At a glance

| I want to... | Use | Section |
|---|---|---|
| Compare accuracy of two models on the SAME prompts | McNemar's test (paired binary) | [Paired vs unpaired](#paired-vs-unpaired-the-most-common-mistake) |
| Compare two models on DIFFERENT prompts | Two-proportion z-test / Fisher's exact | [Paired vs unpaired](#paired-vs-unpaired-the-most-common-mistake) |
| Put an error bar on a single eval score | Bootstrap confidence interval, or Wilson interval for a proportion | [Confidence intervals](#confidence-intervals-what-to-put-on-the-error-bar) |
| Compare a continuous score (loss, rating) across conditions | Paired t-test, or Wilcoxon if skewed | [Continuous outcomes](#continuous-outcomes-loss-ratings-scores) |
| Sweep a knob and claim a trend | Report the curve with CIs; avoid testing every point | [Sweeps](#sweeps-and-multiple-comparisons) |
| Test many probes / layers / features at once | Benjamini–Hochberg false discovery rate correction | [Sweeps](#sweeps-and-multiple-comparisons) |
| Decide how many prompts to run | Power analysis before the run | [How many samples](#how-many-samples-do-i-need) |
| Say "there is a 95% chance the effect is between X and Y" | Bayesian credible interval — a CI does NOT mean this | [Bayesian alongside frequentist](#report-bayesian-and-frequentist-side-by-side) |
| Argue an intervention did NOT hurt capability | ROPE / equivalence test — a non-significant p cannot show this | [Arguing for no effect](#arguing-that-there-is-no-effect) |
| Get an error bar without burning compute on reruns | Bootstrap over items; paired designs | [Where error bars come from](#where-error-bars-actually-come-from) |

## Paired vs unpaired: the most common mistake

**Paired** means the two conditions were measured on the *same* items — the
same prompts, the same dataset rows, the same questions. Almost every
safety-eval comparison is paired, and treating it as unpaired throws away most
of your statistical power.

If model A and model B were both run on the same 500 prompts, the right question
is not "is 0.72 different from 0.68" but "on how many prompts did they
*disagree*, and which way".

### Paired binary outcomes → McNemar's test

Binary means each item is right/wrong, refused/complied, flagged/not-flagged.

```python
from statsmodels.stats.contingency_tables import mcnemar
import numpy as np

a = np.array(model_a_correct)   # 0/1 per prompt
b = np.array(model_b_correct)   # 0/1 per prompt, SAME prompts, same order

n01 = int(((a == 0) & (b == 1)).sum())   # A wrong, B right
n10 = int(((a == 1) & (b == 0)).sum())   # A right, B wrong
result = mcnemar([[0, n01], [n10, 0]], exact=(n01 + n10) < 25)
print(f"discordant: {n01} vs {n10}, p = {result.pvalue:.4g}")
```

Only the *discordant* pairs carry information. Items both models got right, or
both got wrong, tell you nothing about the difference — which is exactly why the
unpaired test is so much weaker here.

### Unpaired binary outcomes → two-proportion test

Use this only when the two conditions really were measured on different items.

```python
from statsmodels.stats.proportion import proportions_ztest
count = np.array([successes_a, successes_b])
nobs = np.array([n_a, n_b])
stat, p = proportions_ztest(count, nobs)
```

For small counts (any cell under ~10) use Fisher's exact test
(`scipy.stats.fisher_exact`) instead — the z-test's normal approximation is bad
in that regime.

## Confidence intervals: what to put on the error bar

A confidence interval (CI) is more informative than a p-value and is what a
reader actually wants. Report CIs on every headline number.

### Proportions → Wilson interval, not mean ± std

For a rate (accuracy, refusal rate, attack success rate), the naive
`mean ± 1.96 * std / sqrt(n)` is wrong near 0 or 1 — it produces intervals that
run below 0 or above 1. Use the Wilson interval:

```python
from statsmodels.stats.proportion import proportion_confint
low, high = proportion_confint(count=successes, nobs=n, method="wilson")
print(f"{successes / n:.3f}  95% CI [{low:.3f}, {high:.3f}]")
```

A refusal rate of 100% on 20 prompts is not "100%" — it is 95% CI [0.84, 1.00].
Say so; the difference matters when someone compares it to 97%.

### Anything else → bootstrap

```python
from scipy.stats import bootstrap
res = bootstrap((scores,), np.mean, n_resamples=10_000,
                confidence_level=0.95, method="BCa")
```

`method="BCa"` (bias-corrected and accelerated) is a better default than the
percentile method for skewed data, and costs nothing extra to ask for.

### Bootstrap the RIGHT unit

If each prompt produced 10 samples, resampling the 5,000 individual samples
treats them as independent when they are not — the CI comes out far too narrow.
Resample **prompts**, carrying their samples along:

```python
# per_prompt is a list of arrays: one array of sample scores per prompt
def stat(idx):
    return np.mean([per_prompt[i].mean() for i in idx])

idx = np.arange(len(per_prompt))
res = bootstrap((idx,), stat, n_resamples=10_000, confidence_level=0.95)
```

This is the single most common way an eval CI ends up dishonestly tight.

## Continuous outcomes: loss, ratings, scores

For a paired continuous measurement (same prompts, two conditions):

```python
from scipy.stats import ttest_rel, wilcoxon
t, p = ttest_rel(scores_a, scores_b)          # assumes roughly normal differences
w, p = wilcoxon(scores_a, scores_b)           # rank-based; use if skewed/outliers
```

Judge ratings on a 1–5 scale are ordinal and usually skewed — prefer
`wilcoxon`, or report the median difference with a bootstrap CI.

Always report an **effect size**, not just a p-value. With 5,000 prompts almost
any difference is "significant"; the question is whether it is *large*.

```python
d = (scores_a - scores_b).mean() / (scores_a - scores_b).std(ddof=1)  # Cohen's d, paired
```

## Where error bars actually come from

The default error bar is **variation over items** — prompts, dataset rows,
questions — and you get it from the run you already did. Bootstrap over items,
or a Wilson interval for a rate. No extra compute.

That is the dominant source of uncertainty in most safety evals, because you are
measuring a fixed model on a sample of prompts and the question is "would a
different sample of prompts have given a different number?".

### Cheaper ways to tighten an error bar than rerunning

In rough order of value per unit of compute:

1. **Pair the comparison.** Running both conditions on the same prompts removes
   item difficulty from the comparison entirely. This is usually a bigger win
   than any amount of extra sampling — see
   [Paired vs unpaired](#paired-vs-unpaired-the-most-common-mistake).
2. **Add more items.** More prompts shrink the interval and cost far less than
   re-running a training job.
3. **Reduce judge noise.** If a large language model (LLM) judge scores the
   outputs, its error rate is part of your error bar. Validating and tightening
   the judge often beats collecting more data.
4. **Bootstrap the right unit** (below) — getting this wrong is the difference
   between an honest interval and a fictional one.

### Vary the data, not the seed

The strongest cheap robustness check is to **collect more data than the task
needs, then test the hypothesis on disjoint subsets of it**.

```python
rng = np.random.default_rng(0)
idx = rng.permutation(len(items))
folds = np.array_split(idx, 4)          # 4 disjoint subsets
effects = [measure_effect(items[f]) for f in folds]
print(f"effect per subset: {[f'{e:+.3f}' for e in effects]}")
```

If the effect holds on every subset, you have something. If it appears in one
subset and vanishes in the others, you have noise — and you have learned that
for a fraction of the cost of a seed sweep.

This is better than varying the random seed because it answers the question a
reader actually has: *does this generalise beyond the particular data you
looked at?* Seed variation only tells you about initialisation noise, which is
rarely why a result fails to replicate. It also protects against the failure
mode a seed sweep cannot touch — an effect that is real only for the specific
prompts you happened to choose.

Do the subset split **before** looking at results if you can, and keep one
subset genuinely held out for the final claim.

### Seeds: useful, not mandatory

Multiple training seeds answer a *different* question — "would a different
random initialisation have given a different result?" — and they are worth
having when you can afford them. They are **not** a prerequisite for reporting a
finding, and plenty of published work does without them.

- If an effect is **large enough to matter**, a pilot run surfaces it without a
  seed sweep. Spending the budget to confirm something you already saw clearly
  is usually a worse trade than spending it on the next experiment.
- Seeds matter most for claims about a **training** intervention, where
  run-to-run variance is real and can be comparable to the effect. They matter
  least for inference-time evaluation of a fixed model, where there is no
  training randomness to average over and item variance dominates.
- If a result *only* appears at one seed, that is a finding about fragility, and
  worth saying plainly.

Treat a seed sweep as an "if there is time and compute left" strengthening step,
not as a gate. What is not optional is **saying which error bar you drew**:
"± 95% CI over 500 prompts" and "± 1 std over 5 seeds" look identical on the page
and mean entirely different things.

## Sweeps and multiple comparisons

Sweeping steering magnitudes, layers, thresholds or probe positions and then
reporting "layer 17 is significant (p < 0.05)" is how you find noise. With 32
layers tested at α = 0.05, you expect about 1.6 false positives by chance.

### Correct for it

```python
from statsmodels.stats.multitest import multipletests
reject, p_adj, _, _ = multipletests(pvals, alpha=0.05, method="fdr_bh")
```

**Benjamini–Hochberg** (`fdr_bh`, controls the false discovery rate) is the right
default for exploratory sweeps — Bonferroni (`bonferroni`, controls family-wise
error rate) is usually too conservative when you are screening many layers or
features and expect several real effects.

### Better: don't test every point

For a sweep, the honest presentation is usually the *curve with confidence
bands*, plus a single pre-registered test of the specific comparison you care
about. A monotone trend across magnitudes is much stronger evidence than one
starred point in the middle of a noisy sweep.

If you found the layer by searching, say you searched. A held-out confirmation
on fresh prompts is worth more than any correction.

## Report Bayesian and frequentist side by side

These answer different questions, both questions are reasonable, and reporting
both costs almost nothing. Do it — especially for headline results.

| | Frequentist 95% CI | Bayesian 95% credible interval (HDI) |
|---|---|---|
| Says | "this *procedure* covers the true value 95% of the time" | "given this data and prior, there is a 95% probability the value is in here" |
| Answers | how reliable is my method | what should I believe about this parameter |
| Needs | nothing beyond the data | a prior (often uncontroversial) |

The second row is the one that matters in practice: **the Bayesian reading is
what nearly everyone already thinks a confidence interval means.** Rather than
police the misreading in your caption, compute the quantity people want.

### For rates, this is a two-line computation

Accuracy, refusal rate, attack success rate — anything that is successes out of
trials — has a conjugate Beta posterior. No MCMC, no PyMC, no new dependency:

```python
import numpy as np
from scipy import stats

# Uniform Beta(1,1) prior; Jeffreys' Beta(0.5,0.5) is also a fine default.
post_a = stats.beta(1 + succ_a, 1 + n_a - succ_a)
post_b = stats.beta(1 + succ_b, 1 + n_b - succ_b)

lo, hi = post_a.ppf([0.025, 0.975])           # 95% credible interval
draws_a, draws_b = post_a.rvs(100_000), post_b.rvs(100_000)
p_better = (draws_a > draws_b).mean()          # P(A is better than B)
print(f"A: {succ_a/n_a:.3f}  95% CrI [{lo:.3f}, {hi:.3f}]   P(A>B) = {p_better:.3f}")
```

`P(A > B) = 0.93` is far more useful to a reader — and far harder to
misinterpret — than `p = 0.06`. It also degrades gracefully: with little data it
simply comes out near 0.5, instead of flipping between "significant" and "not".

For **paired** data, do the same on the per-item differences rather than on the
two rates separately, for the reasons in
[paired vs unpaired](#paired-vs-unpaired-the-most-common-mistake).

### For continuous outcomes

`ttest_rel` has a Bayesian counterpart in **BEST** ("Bayesian estimation
supersedes the t-test", Kruschke 2013), which estimates the difference in means
with a t-likelihood so outliers do not drag it around. In Python: **PyMC** or
**NumPyro** to fit, **ArviZ** to summarise and plot
(`az.plot_posterior(idata, rope=(-0.01, 0.01))`).

Note ArviZ's default credible level is **0.94**, not 0.95 — deliberately, to
stop people reading it as a significance threshold. Set `hdi_prob=` explicitly
and say which you used.

### Arguing that there is no effect

This is where the Bayesian version earns its keep, and it comes up constantly in
safety work: *"our safety intervention did not hurt capability."*

**A non-significant p-value cannot support that claim.** Absence of evidence is
not evidence of absence, and "p = 0.4" is equally consistent with a large effect
you were underpowered to see.

Define a **ROPE** (region of practical equivalence) — the range of effects small
enough that you would call them "no difference" — and compare it to the
posterior (Kruschke's HDI+ROPE rule):

- HDI entirely **inside** the ROPE → accept practical equivalence.
- HDI entirely **outside** → a real effect.
- **Overlapping** → undecided; say so rather than picking whichever reading you
  prefer.

The frequentist equivalent is an equivalence test (TOST, two one-sided tests).
Either is fine; what is not fine is reporting a null result as though a
non-significant test had established equivalence.

Choosing the ROPE is a judgement about what magnitude matters, so **state it and
justify it before looking at the result**. A ROPE picked afterwards is just
p-hacking with extra steps.

### What to actually report

For a headline comparison, one line carries all of it:

> Steering reduced harmful compliance by 8.2 points (95% CI [4.1, 12.3];
> 95% HDI [4.3, 12.1]; P(effect > 0) = 0.998; ROPE ±1 point excluded).

When the two intervals agree — which, with a decent amount of data and a weak
prior, they usually do — that agreement is itself worth showing: it tells the
reader the conclusion is not an artefact of either framework. When they
**disagree**, that is informative and worth investigating rather than hiding:
usually it means small n, or a prior doing real work.

### One caution

Credible intervals are fairly robust to a reasonable prior. **Bayes factors are
not** — they can move by orders of magnitude with the prior on the effect size,
so if you report one, report the prior and a sensitivity check alongside it.
Prefer posteriors and ROPE decisions over Bayes factors for this reason.

## How many samples do I need?

Decide before the run, not after the result disappoints.

```python
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

# Detect a 5-point accuracy difference around a 70% baseline, 80% power:
effect = proportion_effectsize(0.75, 0.70)
n = NormalIndPower().solve_power(effect_size=effect, alpha=0.05, power=0.8)
print(f"~{int(np.ceil(n))} prompts per condition (unpaired)")
```

Paired designs need substantially fewer. If the number comes back larger than
your budget, that is useful information *before* you spend it — either widen the
effect you are willing to claim, or pick a design with more power.

## Pitfalls, with the symptoms you'd actually see

- **"My CI is suspiciously tight."** You bootstrapped samples instead of
  prompts. See [Bootstrap the right unit](#bootstrap-the-right-unit).
- **`ValueError: unequal length arrays`** from `ttest_rel` or `wilcoxon` — you
  dropped failed generations from one condition only, breaking the pairing.
  Drop the *pair* or impute, never one side.
- **`RuntimeWarning: invalid value encountered in divide`** in an effect-size
  calculation — the difference has zero variance (every pair identical), which
  usually means you compared a condition against itself.
- **`scipy.stats.bootstrap` returns `nan`** — your statistic returned `nan` for
  at least one resample, typically a mean over an empty slice. Filter empties
  first.
- **Comparing against best-of-N.** If the baseline is one sample and your method
  takes the best of 8, the comparison is meaningless. Match the sampling budget.
- **Reporting the best seed.** If you *did* run several seeds, reporting
  max-over-seeds as the result is cherry-picking. Report the distribution or
  report one seed honestly — never the best of several presented as typical.
- **P-hacking by prompt-set.** Trying three prompt sets and reporting the one
  that worked is the same error as testing 32 layers, minus the correction.
- **Judge-based scores treated as ground truth.** A large language model (LLM)
  judge has its own error rate; validate on a human-labelled subset and report
  agreement, or your CI is measuring the judge, not the model.

## Where this connects

- Copy-paste snippets and run-directory layout:
  [`code-recipes.md`](code-recipes.md).
- Plotting these numbers honestly:
  [`visualization.md`](visualization.md).
- Control-eval reporting (honest vs attack modes must never collapse to one
  number): [`ai-control.md`](../oversight-and-control/ai-control.md).
- Eval design and dataset choice:
  [`evals.md`](../evaluation/evals.md).

---

Last verified: 2026-08. Bayesian section follows Kruschke's HDI+ROPE decision
rule (2018) and BEST (2013); ArviZ's 0.94 default credible level verified. Drafted by Claude, revised per Nathan's steer that
multiple seeds are an optional strengthening step rather than a gate. Pending
MATS research-staff review — the statistical
recommendations here are a first pass and have not yet been reviewed by the MATS
research staff. Library APIs (`scipy.stats.bootstrap`, `statsmodels`
`mcnemar` / `proportion_confint` / `multipletests` / `NormalIndPower`) verified
against current releases.
