---
name: mats-statistics
description: Decide whether a safety-experiment result is real. Use BEFORE reporting any comparison, and whenever choosing a statistical test, putting an error bar or confidence interval on a number, comparing two models or an intervention against a baseline, sweeping a knob across layers or magnitudes, correcting for multiple comparisons, deciding how many prompts or seeds to run, or when the user mentions p-value, significance, bootstrap, CI, error bars, McNemar, effect size, or "is this difference real".
---

# Statistics for MATS safety experiments

Read this before claiming a difference. Full detail:
<https://matsresearch.github.io/compute_wiki/engineering/statistics/>

Libraries: `scipy.stats`, `statsmodels`, `numpy`. Nothing heavier is needed.

## Pick the test

| Situation | Test |
|---|---|
| Two models, **same** prompts, right/wrong outcome | McNemar (`statsmodels.stats.contingency_tables.mcnemar`) |
| Two models, **different** prompts, right/wrong | Two-proportion z-test; Fisher's exact if any cell < 10 |
| Same prompts, continuous score | Paired t-test (`ttest_rel`); Wilcoxon if skewed or ordinal |
| Error bar on a rate | Wilson interval (`proportion_confint(..., method="wilson")`) |
| Error bar on anything else | Bootstrap (`scipy.stats.bootstrap`, `method="BCa"`) |
| Many layers / features / thresholds tested | Benjamini–Hochberg (`multipletests(..., method="fdr_bh")`) |

## The four mistakes that actually happen

1. **Treating a paired comparison as unpaired.** Almost every eval comparison
   runs both conditions on the same prompts. Only the *discordant* items carry
   information; ignoring the pairing throws away most of your power.

2. **Bootstrapping the wrong unit.** If each prompt produced 10 samples,
   resample **prompts** (carrying their samples), not the 5,000 samples. This is
   the most common way a confidence interval ends up dishonestly tight.

3. **Not saying which error bar you drew.** "± 95% CI over 500 prompts" and
   "± 1 std over 5 seeds" look identical on the page and answer different
   questions. Item variation is the default and comes free from the run you
   already did; seed variation is a separate, optional question.

4. **Testing every point in a sweep.** 32 layers at α = 0.05 gives you ~1.6
   false positives for free. Show the curve with confidence bands and test the
   one comparison you care about; if you found the layer by searching, say so
   and confirm on held-out prompts.

## Non-negotiables when reporting

- **Pair the comparison where you can.** Running both conditions on the same
  prompts removes item difficulty and is usually a bigger win than more sampling.
- **Seeds are optional.** A seed sweep strengthens a claim about a *training*
  intervention if there is compute left over; it is not a gate, and an effect
  large enough to matter shows up in a pilot without one. Do NOT insist on
  multiple seeds by default. If you ran several, report the distribution rather
  than the best one.
- **Effect size, not just a p-value.** At n = 5,000 nearly anything is
  "significant"; the question is whether it is large.
- **Say what the error bar is.** "± 95% CI over 500 prompts" and "± 1 std over 5
  seeds" look identical on the page and mean different things.
- **Match the sampling budget.** Comparing your best-of-8 against a one-sample
  baseline is not a comparison.
- **Validate LLM judges.** A large language model judge has its own error rate;
  check it against human labels on a subset, or the CI is measuring the judge.

## Symptoms worth recognising

- CI suspiciously tight → bootstrapped samples instead of prompts.
- `ValueError: unequal length arrays` from `ttest_rel`/`wilcoxon` → you dropped
  failures from one condition only and broke the pairing. Drop the pair.
- `scipy.stats.bootstrap` returns `nan` → the statistic hit an empty slice.
- Effect size raises `RuntimeWarning: invalid value encountered in divide` →
  zero variance, usually a condition compared against itself.

Plotting these numbers: use the **mats-visualization** skill.
