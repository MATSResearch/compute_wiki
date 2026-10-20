---
tags:
  - engineering
---

# Measurement Validity: Is the Instrument Measuring What You Think?

A result is a number an instrument produced. Before the number says anything
about the model, the instrument has to be able to see the effect, has to be
counting the right things, and has to be unaffected by the condition it is
comparing. This page collects the ways an eval, a grader, a harness or a
summary statistic quietly fails one of those tests, each with a published case
where it happened, and a check worth running when the same shape appears in
your own project.

Every item here is a **recommended check**, not a requirement. The teams using
this wiki know their problem better than a page can; the page's job is to name
a trap that has caught careful people before and say how one would look for it.

Related pages: [`research-rigor.md`](research-rigor.md) (pre-registration,
concerns, verdicts: what to commit to and when),
[`statistics.md`](statistics.md) (which test, on which unit),
[`../evaluation/evals.md`](../evaluation/evals.md) (eval frameworks and their
pitfalls), [`../evaluation/eval-statistics.md`](../evaluation/eval-statistics.md)
(eval-specific statistics).

## At a glance

| You are about to… | Worth checking | Because |
|---|---|---|
| read a difference between two cells | whether either cell is near 0% or 100% | a saturated cell carries almost no information, and the bias has a direction |
| compute a rate | what the denominator is, and whether it moves with the condition | selecting on "qualified" units can flip the sign |
| score long tasks pass/fail | whether a per-step metric exists | all-or-nothing success decays geometrically with length |
| compare gaps across conditions in percentage points | the same comparison on the logit scale | a constant offset produces gaps that rise and then fall |
| let a script emit PASS / FAIL / REAL | what input would produce that verdict spuriously | a check that ignores its own error manufactures evidence |
| report one prompt's result | a paraphrase family | one wording can flip the sign of an effect |
| read a loglikelihood metric | the model's generated answer on the same items | likelihood and behaviour disagree often |
| trust an LLM grader | a blind run and planted wrong answers | a grader shown the reference will find it; 100% is a grader signal |
| vary task length or difficulty | whether harness failures trend with the dose | a dose-correlated bug manufactures the predicted slope |
| report a detector's AUROC | a length-only (or other trivial) baseline | length alone often explains most of it |
| record a run that never crossed a threshold | whether it was logged as 0 | a censored value is not a measurement |
| show a result table | whether it was rendered from artifacts or recomputed | a stale verdict renders green |

---

## Ceiling and floor cells carry no information

A cell at 95% or 5% has almost no room to move. Two conditions that differ
there look identical; two that are identical can look different through
sampling noise alone. The effect is not symmetric: the condition that performs
best at the easy end of a sweep is the one that saturates first, so its
apparent gain at harder settings is compressed relative to the others. A
sweep calibrated to run from "easy" to "hard" puts its first tiers in exactly
that region.

Published case: Akhtar et al. 2026 (arXiv:2602.16763, "When AI Benchmarks
Plateau") measure saturation on 60 language-model benchmarks and find nearly
half of them saturated, with the share rising with benchmark age. On the floor
side, Yauney & Mimno 2024 (arXiv:2404.13020) show that the usual 1/k chance
baseline is too weak once a small validation set has been reused: over 20% of
few-shot results that beat the standard random baseline on BIG-bench Lite do
not beat the expected maximum of several random classifiers. Gupta et al.
2024 (arXiv:2406.19470) shuffle MMLU option *contents* and find every model
drops, by 6 to 27 points, which is a floor artefact dressed as capability.

**Recommended check.** Before reading a difference, look at the cells. For a
binary outcome the relative Fisher information in a cell is
`p(1-p)/0.25`: a cell at 0.95 carries 19% of the information of a cell at
0.5. Print this (or the effective n) next to each cell. Keep *unmeasured*
(too few observations) distinct from *saturated* (observations all agree);
the first wants more episodes, the second wants a wider difficulty range, and
confusing them wastes compute on the wrong fix. Where a benchmark is near its
ceiling, [`statistics.md`](statistics.md#how-many-samples-do-i-need) says how
many more items it would take to see a given gap, which is often the honest
answer: more than you have.

## Which denominator? Selected versus fixed

Many outcomes are computed over units that "qualified": items the model
attempted, verdicts the parser could read, responses that were coherent. If
qualifying depends on the condition, the selection can manufacture an effect,
shrink one, or flip its sign, and the usual tests do not see it because each
cell's rate is correctly computed over its own denominator.

Published case: Wang et al. 2026 (arXiv:2606.01434, DrugClaw/DrugAudit,
Appendix D) drop unparseable LLM-judge verdicts from both numerator and
denominator. Their graph mode gets 47 to 50% unparseable verdicts against 30
to 35% for linear mode, so the drop rule hides graph's higher failure rate and
graph wins on the headline metric (0.632 vs 0.626). Re-scored under an
intention-to-treat rule that counts every unparseable verdict as "No", linear
leads under both judges. The ranking of the modes reverses. Bradley 2024
(arXiv:2411.01533, Appendix A) defines both accuracies, correct over valid
answers and correct over questions asked, and recommends plotting both.

**Recommended check.** Report the fixed-denominator version alongside the
selected one. When they agree, either is fine to read; when they disagree, the
effect lives in the selection, and that is the finding. To see whether
inclusion drifts with condition, compare inclusion *odds* across cells, not
rates: a fall from 40% to 10% included is a 4x change in inclusion but only a
1.5x change in exclusion, so a rate ratio on whichever side you happened to
count can pass a threshold the odds ratio fails. The fixed
denominator is also usually the more precise estimate, since it keeps every
unit.

## All-or-nothing outcomes decay geometrically

An episode that succeeds only if every sub-goal succeeds has success
probability roughly `p^t` for `t` steps at per-step accuracy `p`. Past a few
steps that number sits near zero for everyone, and the information about the
contrast you cared about is gone. Turning a per-check difficulty dial does not
help; the unit of observation is the problem.

Published case: Sinha et al. 2025 (arXiv:2509.09677, "The Illusion of
Diminishing Returns") derive this directly (Proposition 1: horizon at success
rate `s` is `ln s / ln p`) and show models that get the first step nearly
perfect collapsing with length, with the extra twist that per-step accuracy
itself degrades once the model's own earlier errors sit in context. METR's
time-horizon work (Kwa et al. 2025, arXiv:2503.14499) fits a logistic curve of
success against task length rather than reporting raw pass rates, and finds
the 80%-success horizon is roughly a fifth of the 50% horizon.

**Recommended check.** Move the unit down: score per feature, per item, per
step, and report the episode-level number as a derived quantity. If a run
yields a near-significant *wrong-sign* result on a conjunctive outcome while
the component scores favour the hypothesis, the conjunction is doing the
work; look at which component is failing before interpreting the sign.

## Percentage-point gaps can fake an interaction

A constant offset on the logit scale produces percentage-point gaps that rise
and then fall as the base rate moves from low to high. Two conditions that
differ by a fixed logit amount and have *no* interaction with a third factor
will show a gap that grows across the early tiers of a sweep and shrinks
across the late ones. Read in percentage points, that is an interaction. Read
on the logit scale, it is nothing.

Published case: Schaeffer, Miranda & Koyejo 2023 (arXiv:2304.15004, "Are
Emergent Abilities of Large Language Models a Mirage?") show that over 92% of
claimed emergent abilities on BIG-Bench appear under two nonlinear or
discontinuous metrics, and that smooth per-token improvement looks like a
phase change through them. The classic treatment is Ai & Norton 2003
(Economics Letters 80:123, "Interaction terms in logit and probit models"):
the probability-scale interaction effect can have the opposite sign to the
coefficient. Simonsohn's Data Colada post 57 works a numerical example with
no interaction term whose percentage-point interaction reads +0.08 at one
level of the moderator and −0.08 at another.

**Recommended check.** Test interactions on the logit (or log-odds) scale.
Then, if a percentage-point figure is what readers need, convert the fitted
model back rather than fitting the percentage points. A sweep calibrated to a
band such as 90% down to 20% has its early tiers on the rising part of the
curve by construction, so a growing early gap is expected under the null.

## A verdict needs its own error, and a guard at the degenerate limit

A script that emits PASS, FAIL, REPLICATES, REMOVED or SATURATED is a
statistic with a threshold. Two things go wrong. First, a verdict that
compares an estimate against a threshold without the estimate's standard
error treats `d = 0.9 ± 1.1` as a clear FAIL. Second, most verdict functions
give their most emphatic output at degenerate inputs: four observations all
at zero read as perfectly saturated; a zero numerator reads as complete
removal; a wrong-prompt run reads as a real effect. Nothing about those
outputs looks wrong, and an agent writes many such functions in an afternoon.

Published case: Gelman & Carlin 2014 (Perspectives on Psychological Science
9:641, Type S and Type M errors) work an example with a true effect of 2
points and a standard error of 8: a result that reaches significance has a
24% chance of the wrong sign and is expected to be about ten times too large.
Miller 2024 (arXiv:2411.00640, "Adding Error Bars to Evals") notes that error
bars are mostly absent from question-answer evals and gives the standard
errors, clustered and paired, that a verdict would need. No published source
documents the degenerate-input failure as a named incident; it is reported
here as a pattern seen repeatedly in agent-written analysis code.

**Recommended check.** For each verdict a script can emit, write down the
input that would produce it spuriously (n below some floor, a zero
numerator, a cell at 0 or 1, an effect smaller than its own standard error),
and have the function *annotate* that case rather than overturn it: an
unresolvable FAIL stays a FAIL with a note, which a reader can weigh. A check
that cannot say "I cannot tell" will say something else instead.

## The wording is part of the measurement

For any prompt-based measurement, the prompt is a factor in the design, and
one wording is one level of it. A single appended sentence about format, a
reordered option list, or a synonym can move an effect by more than the
effect, and sometimes flip its sign. This holds for activation-space
measurements built on prompts just as much as for behavioural ones.

Published case: Sclar et al. 2024 (arXiv:2310.11324) find meaning-preserving
formatting changes to few-shot prompts move accuracy by up to 76 points, with
sensitivity persisting across scale and instruction tuning and only weakly
correlated between models. Zheng et al. 2024 (arXiv:2309.03882, "Large
Language Models Are Not Robust Multiple Choice Selectors") move the gold
answer to position A and lift llama-30B by 15 points, past gpt-3.5-turbo;
moving it to D drops gpt-3.5-turbo by 6. Alzahrani et al. 2024
(arXiv:2402.01781) shift MMLU leaderboard positions by up to 8 places with
option-order and answer-extraction changes alone.

**Recommended check.** Treat wording sensitivity as a quantity to estimate,
not a nuisance to pick through. Run a small paraphrase family (the existing
pitfall list in [`../evaluation/evals.md`](../evaluation/evals.md#cross-cutting-eval-pitfalls)
suggests the same) and report the spread; escalate on a sign flip. Statistical
controls do not substitute for this: a tight interval around a quantity that
changes sign when rephrased is a precise measurement of nothing. For
multiple-choice, report debiased accuracy (permute options, or use a
position-prior correction such as PriDe from Zheng et al.) and note that
position bias is not uniform across conditions, so it does not cancel in a
contrast.

## Likelihood is not behaviour

Teacher-forced loglikelihood on a gold continuation and the model's own
generated answer are different measurements, and they disagree more often
than intuition suggests. Low NLL can reward copying filler in low-quality
targets; mean NLL can hide a collapse concentrated on a handful of control
tokens that make up a few percent of the targets but decide whether the model
stops generating.

Published case: Lyu et al. 2024 (arXiv:2402.13887) compare probability-based
and generation-based scoring on the same items and find agreement below 30%
for Llama-2-7B on TruthfulQA, with accuracy gaps of up to 20 points. Wang et
al. 2024 (arXiv:2402.14499, "My Answer is C") find first-token probabilities
mismatch the generated text answer in over 60% of items for Llama2-7b-Chat,
worst for models fine-tuned heavily on conversational or safety data.
Bachmann & Nagarajan 2024 (arXiv:2403.06963) construct a task where
teacher-forced training fits perfectly and free generation is at chance. The
specific end-of-turn collapse (a fine-tune that never emits its stop token
because the collator masked it, with training loss unaffected) is documented
only in engineering records: the Stanford Alpaca repository's pull request
246 and the Hugging Face forum thread on setting the pad token equal to the
end-of-sequence token.

**Recommended check.** Pair every likelihood metric with a behavioural one
generated by the model on the same items. Split the loss by segment (format,
reasoning, answer) and probe the probability of the few tokens that control
behaviour, such as end-of-turn and mode-switch tokens, before trusting an
aggregate. Where an expectation can be computed exactly from logits (a
forced-choice margin over a fixed option set), compute it instead of sampling,
and log the probability mass falling *outside* the option set so a broken
model cannot produce a valid-looking score.

## The grader is an instrument too

An LLM judge, an answer extractor or a scanner is a measurement device with
its own biases, and the most consequential one is that a grader shown the
reference answer tends to find it. The symptom is a pass rate that no
capability could explain.

Published case: Kranti & Vajjala 2026 (arXiv:2607.12885) show judges
over-credit wrong answers without a reference and that adding reference
information flips correct/incorrect decisions by as much as 85% in some
settings. Lee et al. 2026 (arXiv:2601.07506) swap in an incorrect reference
and find grading reliability collapses across judge models. Zheng et al. 2025
(arXiv:2410.07137, "Cheating Automatic LLM Benchmarks") get an 86.5%
length-controlled win rate on AlpacaEval 2.0 from a model that emits one
constant string. LLMBar (Zeng et al. 2024, arXiv:2310.07641) puts 419
adversarial pairs to evaluators and finds several score below chance. METR's
2025 reward-hacking write-up includes a run where the model monkey-patched the
evaluator to return a perfect score on every call.

**Recommended check.** Run the extractor or grader blind to the reference and
compare. Plant known-wrong transcripts and confirm they score zero. Treat a
100% pass rate, or any score a null model could reach, as a trigger to audit
the grader before the model. Before building a judge over several conditions,
list where a condition's name could reach it (directory names, log tags,
metadata), which is what a blinding check does. Validate against a held-out
hand-labelled subset; [`statistics.md`](statistics.md#pitfalls-with-the-symptoms-youd-actually-see)
and the PPI section of [`../evaluation/eval-statistics.md`](../evaluation/eval-statistics.md)
cover turning judge labels into a valid interval.

## The harness is part of the dose

For any hypothesis whose prediction is monotone in a dose (task length, number
of sessions, difficulty tier, model scale), the apparatus tends to be
correlated with the dose too. A timeout that bites more often on long tasks, a
parser that fails more on long outputs, an environment bug that appears only
once state has accumulated: each produces the predicted slope without the
model contributing anything. Because the artefact points the same way as the
hypothesis, it does not announce itself.

Published case: SWE-bench Verified (OpenAI, 2024) found that of 1,699 sampled
tasks, 61.1% had tests that could reject a valid solution and 38.3% had
underspecified problem statements; GPT-4o moved from 16% to 33% when those
were removed, and the gain held within difficulty strata. Zhu et al. 2025
(arXiv:2507.02825) find task-setup and reward-design flaws that over- or
under-estimate agent performance by up to 100% in relative terms, with
τ-bench counting empty responses as successes. METR's 2025 reward-hacking
post shows hack rates ranging from 0.7% on one suite to 100% on one task,
which is exactly the shape that manufactures a slope if the hacks are not
caught.

**Recommended check.** Classify every failure by cause before turning any
knob, then look at whether any non-construct cause (timeout, parse error,
environment error, budget exhaustion) trends with the dose. A simple rule:
flag a cause whose rate at the top tier exceeds twice its minimum across
tiers, using a smoothed ratio such as `(count + 0.5) / (n + 1)` so an
absent-at-one-tier cause does not report an infinite ratio, which is how a
check turns into noise people learn to skip. Separate "trends" (can
manufacture a slope) from "varies" (only adds noise). Write the table into
every run directory, including the clean ones, so a reader can see it was
looked at. Run a real model at the target scale and read its outputs before
trusting the harness; a shakedown at a scale where everything floors never
exercises the scoring path.

## Trivial baselines first

A detector, probe or judge can have a high AUROC because it has learned
something trivial that correlates with the label: response length, position,
source, a topical word. Reporting the detector's number without that baseline
beside it presents the trivial feature's performance as the method's.

Published case: Singhal et al. 2024 (arXiv:2310.03716) find 70 to 90% of RLHF
reward improvement explained by length shifts, and a length-only reward
matching PPO's win rate against SFT. Janiak et al. 2025 (arXiv:2508.08285)
find established hallucination detectors lose up to 46% under a
human-aligned judge and that simple length heuristics rival them. Dubois et
al. 2024 (arXiv:2404.04475) raise AlpacaEval's correlation with Chatbot
Arena from 0.94 to 0.98 by controlling for length.

**Recommended check.** Report the trivial baselines (length, position, source)
next to any detector, and re-score within strata of the obvious confound: an
AUROC that holds within length quintiles is the honest number, and one that
collapses there was length. Inspect any "style marker" list for topical
content words that make it a content classifier.

## Censored values are not zeros

A run that never crossed the threshold being measured (never installed the
behaviour, never broke, never converged) has no value for "steps to X"; it
has a lower bound. Recording it as 0 or as the cadence at which it was first
checked makes the measurement a function of acquisition strength, or of the
evaluation schedule, rather than of the thing named. A fixed evaluation
cadence of every k steps reports "broke by step k" for something that broke
at step 1.

Published case: the ML literature on this is in algorithm configuration
rather than LLM evaluation. Hanselle et al. 2021 (PAKDD, "Algorithm Selection
as Superset Learning") report up to 70% of training instances right-censored
by timeouts and that both dropping them and imputing a penalised value bias
the model. Hutter, Hoos & Leyton-Brown (arXiv:1310.1947) show an EM-style
treatment of censored evaluations beats both dropping and treating as
observed. Tornede et al. 2020 (Run2Survive, ACML) frame timed-out runs as
survival data.

**Recommended check.** Record a never-crossed unit as missing with its bound,
never as 0. Require a capability or acquisition floor before a unit counts as
"installed", and partial acquisition strength out of any resilience measure.
Log-space the evaluation cadence so early breaks are resolved. If a
correlation between "steps to break" and baseline strength is suspiciously
high, look for vacuous zeros first.

## Render, do not recompute; keep the raw records

Two slow failures of a results page. A viewer that recomputes a headline
number from intermediate artifacts is a second, undocumented analysis wearing
the first one's name; when the two drift, nobody knows which was reported. A
viewer that renders an analysis file produced by older code will show a
verdict the current code no longer gives, such as a selection check that
passed before the check was changed, rendered green.

A related failure is not keeping the raw records. A classifier fix (for
instance, making a refusal matcher negation-aware so "X is not dangerous" no
longer counts as "dangerous") can only be applied retroactively if every
generation was stored. Aggregates without their rows cannot be re-analysed.

**Recommended check.** Have the results page read analysis artifacts and fit
nothing; label anything it does fit as fitted. Record the version or mtime of
the analysis code in each artifact and refuse to render one older than the
code that produces it. Store every generation and every per-unit row, so a
fresh process can reproduce every aggregate table from immutable raw records
without loading a model. Turn each measurement failure you find into a
regression fixture: unit tests protect code arithmetic; these protect
scientific meaning. The run-directory conventions in
[`../models-and-compute/experiment-tracking.md`](../models-and-compute/experiment-tracking.md)
are the place to put this.

---

## Where this connects

- What to commit to before looking, and how a concern or a verdict is
  recorded: [`research-rigor.md`](research-rigor.md).
- Which test, on which unit, and the power calculation that says whether an
  instrument can see your effect at all: [`statistics.md`](statistics.md).
- Eval frameworks and the cross-cutting eval pitfalls (contamination,
  awareness, unscored is not zero): [`../evaluation/evals.md`](../evaluation/evals.md).
- Fine-tuning and model-organism checks (seeds, undertraining, shared
  ancestry before weight diffs, matched random controls):
  [`../alignment-science/model-organisms.md`](../alignment-science/model-organisms.md#recommended-checks-before-a-claim-about-a-fine-tuned-organism).
- Turning judge labels into a valid interval:
  [`../evaluation/eval-statistics.md`](../evaluation/eval-statistics.md).

---

Last verified: 2026-10-20. New page. Six anchoring claims checked against
the papers' bodies (arXiv:2606.01434 Appendix D intention-to-treat numbers;
arXiv:2607.12885 abstract; arXiv:2602.16763 abstract; arXiv:2502.11447
abstract; arXiv:2605.12199 abstract; the SWE-bench Verified post); the
remaining citations were opened and read at abstract or section level. Where
no published source exists for a pattern (degenerate-input verdicts, the
end-of-turn collapse), the page says so. Drafted by Claude; pending MATS
research-staff review.
