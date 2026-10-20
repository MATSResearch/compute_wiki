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
| Decide how many prompts to run | Power analysis before the run — paired if both conditions share prompts | [How many samples](#how-many-samples-do-i-need) |
| Stop a run early once the result looks clear | Anytime-valid confidence sequence, or fix n in advance | [Stopping early](#can-i-stop-the-run-once-it-looks-significant) |
| Error bars when several items share a passage, image or task | Clustered standard error (Inspect `stderr(cluster=...)`) | [Bootstrap the right unit](#bootstrap-the-right-unit) |
| LLM-judge labels, many models × many items, item response theory | The eval-specific page | [`eval-statistics.md`](../evaluation/eval-statistics.md) |
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

The same applies when several **items** share one unit: eight questions about
one reading passage, several questions about one image, a user task crossed
with several prompt injections. Resample the shared unit (passages), not the
questions. In Inspect AI the built-in version is `stderr(cluster="passage_id")`
and `ci_wilson(cluster="passage_id")`, keyed on a `Sample.metadata` field. A
census of `inspect_evals` tasks (issue #2605, October 2026) found clustered
standard errors up to 2.9× the plain ones; details and the Inspect API are in
[Clustered items](../evaluation/eval-statistics.md#clustered-items-passages-images-problem-sheets-and-shared-tasks).

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

The same multiplicity problem arises when ranking many models: a ranking of k
models implies k(k − 1)/2 pairwise claims. For a per-item results table of many
models × benchmarks, **evalci** (`evalci` on PyPI, young: 3 stars as of
2026-10-14) runs paired tests with Holm or Benjamini–Hochberg correction in one
call; see
[Many models at once](../evaluation/eval-statistics.md#many-models-at-once-leaderboards-and-model-by-benchmark-grids-evalci).

### Picking the "best" hyperparameter config: report its spread, not its luckiest run

In a hyperparameter sweep (learning rate × β × data subset, say), the config
that looks best is partly the one that got the luckiest sample. This is the
**winner's curse**: selecting the maximum of noisy estimates biases it upward,
and the more configs you try, the bigger the bias. Brushing the top of a metric
in a parallel-coordinates plot does exactly this selection.

- **Give every sweep a variation axis**: the same config run on several data
  subsets or bootstrap resamples. See *Vary the data, not the seed* above.
- **Compare configs by their spread**: collapse runs with identical parameters
  into one line and show the min–max (or interquartile) band of each metric
  across the variation axis, with `n`. A config whose band overlaps the
  runner-up's has not been shown to be better.
- **Keep failed runs in the table.** Dropping them makes the surviving configs
  look more reliable than they are (survivorship).
- **Confirm the chosen config on held-out data** before reporting its number.

In the MATS dashboard's Automated Alignment tool, a sweep recorded as a run
table (`<run_table>`, with columns declared as param / variation / metric /
status) opens as a parallel-coordinates panel. **Group by config** draws this
spread band, failed runs stay drawn, and a table with no variation column
carries a "no robustness axis" note.

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

Note ArviZ's default credible level is not 0.95 — deliberately, to stop people
reading it as a significance threshold: **0.94** (HDI) in ArviZ 0.x, **0.89**
(equal-tailed) in ArviZ 1.x, which current PyMC requires. Set it explicitly
(`hdi_prob=` in 0.x; `ci_prob=` and `ci_kind="hdi"` in 1.x) and say which you
used.

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

Decide before the run, not after the result disappoints. Which calculation to
use depends on the design.

### Paired: both conditions on the same prompts (the usual case)

Most eval comparisons are paired, and a paired comparison needs far fewer
prompts than the unpaired formula says. Required paired prompts:
N\* = (z₁₋α/₂ + z₁₋β)² · σ_D² / δ², where σ_D² is the variance of the
per-prompt **difference** D = score_A − score_B and δ is the gap to detect.

```python
import numpy as np
from scipy.stats import norm

z = norm.ppf(1 - 0.05 / 2) + norm.ppf(0.80)       # alpha = 0.05, power = 0.8 → ≈ 2.80

# From a pilot on shared prompts (0/1 or graded scores):
d = pilot_a - pilot_b                              # per-prompt differences, same prompts
n_star = (z * d.std(ddof=1) / 0.05) ** 2           # prompts to detect a 5-point gap

# Before any data, for 0/1 scores, from guessed accuracies and their correlation rho:
def n_star_binary(p_a, p_b, rho):
    va, vb = p_a * (1 - p_a), p_b * (1 - p_b)
    return z**2 * (va + vb - 2 * rho * np.sqrt(va * vb)) / (p_a - p_b) ** 2

print(f"~{n_star_binary(0.75, 0.70, 0.5):.0f} shared prompts (paired, rho = 0.5)")
```

ρ is the correlation between the two conditions' per-prompt correctness. It is
often substantial (on the real leaderboard pairs in the paper cited below,
ρ̂ ranges from about 0.45 to 0.99), and a pilot of a few hundred prompts estimates it. When the
two accuracies are close, the paired N\* is about (1 − ρ) times the unpaired
per-arm n. On 40 Open LLM Leaderboard v1
pairs, the paired required N was a median 2.15× smaller than the unpaired
formula (Kotawala, arXiv:2605.30315, 2026).

**A known trap: the "(1 − ρ) shortcut".** Multiplying a calculator's unpaired
per-arm output by (1 − ρ) is only right if the calculator counts both arms'
variance, as `statsmodels`' `NormalIndPower` does. The same paper reports that
with a K/h² per-arm convention, the shortcut gives about half the correct N\*
for close comparisons. (It attributes that convention to Cohen's 1988 formula,
G\*Power 3.1 and R's `pwr`, but `pwr::pwr.2p.test`'s source computes power from
h·√(n/2), which is 2K/h² per group, the same as `statsmodels`.) Computing N\*
from σ_D² directly, as above, avoids the question.

The same paper defines the **resolution ratio q = N / N\***: q ≥ 1 means a
benchmark of N prompts can resolve the gap at (α, power). That diagnostic,
for a published ranking or a leaderboard, is in
[Paired comparisons](../evaluation/eval-statistics.md#paired-comparisons-can-this-benchmark-resolve-the-gap-the-resolution-ratio-q).

### Unpaired: the two conditions use different prompts

```python
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

# Detect a 5-point accuracy difference around a 70% baseline, 80% power:
effect = proportion_effectsize(0.75, 0.70)
n = NormalIndPower().solve_power(effect_size=effect, alpha=0.05, power=0.8)
print(f"~{int(np.ceil(n))} prompts per condition (unpaired)")   # ≈ 1250
```

This is the right calculation only when the two conditions really are measured
on different items. Used for a shared-prompt comparison it over-asks, by about
1/(1 − ρ).

### Clustered items

If items share a passage, image or task, the effective sample size is smaller
than the item count; multiply the required N by the design effect
(SE_clustered / SE_plain)². See
[Clustered items](../evaluation/eval-statistics.md#clustered-items-passages-images-problem-sheets-and-shared-tasks).

If the number comes back larger than your budget, that is useful information
*before* you spend it: either widen the effect you are willing to claim, or
pick a design with more power (pairing first).

### Can I stop the run once it looks significant?

Not with a fixed-n test. Checking the p-value after every batch and stopping at
the first p < 0.05 inflates the false-positive rate far above 5%; it is the
sequential version of trying several prompt sets. Two legitimate options:

- **Fix N in advance** from the calculation above, and look once.
- **Use an anytime-valid method**: a confidence sequence (Howard et al.,
  *Annals of Statistics* 2021) or an e-process is valid at every sample size
  simultaneously, so stopping whenever it excludes zero is fine. The price is
  a wider boundary: in simulations in arXiv:2605.30315 (calibrated to two ARC
  pairs) the expected stopping time was 1.84–2.32× the fixed-n N\*.

For Inspect evals with repeated epochs, **optstop** (UK AI Security Institute)
is a Bayesian alternative: it stops epochs once a hierarchical credible
interval stops changing. Its guarantee is about credible intervals, not
frequentist error rates, and it is weakest for rates near 0, which is where
many safety evals live. See
[Stopping an eval early](../evaluation/eval-statistics.md#stopping-an-eval-early-when-run-until-it-looks-significant-is-legitimate).

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
  agreement, or your CI is measuring the judge, not the model. With a
  **random** human-labelled subset, prediction-powered inference
  (`ppi-python` on PyPI) turns judge labels plus that subset into an interval
  that is valid however biased the judge is; see
  [PPI](../evaluation/eval-statistics.md#llm-judge-labels-plus-a-small-human-labelled-subset-prediction-powered-inference-ppi).
- **"My eval's error bars look too small for 1,200 items."** Several items
  probably share a passage, image or task, and the reported `stderr()` is not
  clustered. See [Bootstrap the right unit](#bootstrap-the-right-unit).
- **Stopping when p first dips below 0.05.** Optional stopping without an
  anytime-valid method inflates false positives. See
  [Can I stop the run once it looks significant?](#can-i-stop-the-run-once-it-looks-significant).
- **An interaction that appears in percentage points.** A constant logit
  offset produces percentage-point gaps that rise and then fall across the
  success range (Ai & Norton 2003; Schaeffer et al. 2023 on "emergent"
  abilities). Test interactions on the logit scale and convert back. See
  [`measurement-validity.md`](measurement-validity.md#percentage-point-gaps-can-fake-an-interaction).
- **A "significant" effect smaller than its own standard error.** Under low
  power a result that clears the threshold has a large chance of the wrong
  sign and is expected to be several times too big (Gelman & Carlin 2014,
  Type S and Type M errors). Report the standard error beside any verdict a
  script emits. See
  [`measurement-validity.md`](measurement-validity.md#a-verdict-needs-its-own-error-and-a-guard-at-the-degenerate-limit).
- **The rate's denominator moves with the condition.** Dropping unparseable,
  refused or incoherent units from both numerator and denominator can flip
  which condition wins; one 2026 benchmark reverses its mode ranking under
  intention-to-treat scoring. Report the fixed-denominator version too, and
  compare inclusion odds rather than rates. See
  [`measurement-validity.md`](measurement-validity.md#which-denominator-selected-versus-fixed).
- **A run that never crossed the threshold logged as 0.** A censored value is a
  bound, not a measurement; scoring it as zero makes "steps to X" a function
  of whether X was ever reached. See
  [`measurement-validity.md`](measurement-validity.md#censored-values-are-not-zeros).

## Where this connects

- Copy-paste snippets and run-directory layout:
  [`code-recipes.md`](code-recipes.md).
- Plotting these numbers honestly:
  [`visualization.md`](visualization.md).
- Control-eval reporting (honest vs attack modes must never collapse to one
  number): [`ai-control.md`](../oversight-and-control/ai-control.md).
- Eval design and dataset choice:
  [`evals.md`](../evaluation/evals.md).
- Whether the instrument can see the effect at all (saturated cells,
  denominators, graders, harness artefacts, censoring):
  [`measurement-validity.md`](measurement-validity.md).
- Eval-specific statistics (clustered items, resolution ratio q, LLM-judge
  correction with PPI, crossed random effects, item response theory, early
  stopping): [`eval-statistics.md`](../evaluation/eval-statistics.md).

---

Last verified: 2026-10-20 (additions: four pitfalls pointing at measurement-validity.md). Earlier: 2026-10-14. Bayesian section follows Kruschke's HDI+ROPE decision
rule (2018) and BEST (2013); ArviZ default credible levels (0.94 in 0.x, 0.89 in 1.x) verified. Drafted by Claude, revised per Nathan's steer that
multiple seeds are an optional strengthening step rather than a gate. Pending
MATS research-staff review — the statistical
recommendations here are a first pass and have not yet been reviewed by the MATS
research staff. Library APIs (`scipy.stats.bootstrap`, `statsmodels`
`mcnemar` / `proportion_confint` / `multipletests` / `NormalIndPower`) verified
against current releases. (Additions 2026-10-14: power section rewritten to lead with the paired calculation; the paired N\* formula, the (1 − ρ) shortcut finding and the 2.15× median from arXiv:2605.30315 were checked against the paper's Eqs. 3–5, Table 1 and §2, and the worked example (N\* ≈ 1,028 at p = 0.65/0.60, ρ = 0.3) was recomputed; Inspect `stderr(cluster=)` / `ci_wilson(cluster=)` checked against `std.py` and the CHANGELOG; inspect_evals issue #2605 read directly; optional-stopping numbers from arXiv:2605.30315 Appendix C.)
