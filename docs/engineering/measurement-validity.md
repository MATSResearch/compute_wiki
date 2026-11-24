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
| score with a logit readout (yes/no, A/B) | that the scored token IDs appear in greedy decodes | a space-prefixed token can make the readout score a token the model never emits |
| report an attack success rate or a grader's rate | per-class label counts, the named grader, the attempt budget | one grader assigned "compliance" zero times in 900 responses |
| tune a judge panel's rubric | agreement with human labels, not with each other | more inter-judge consensus did not move agreement with experts |
| confirm a judge-based ranking by re-running it with another provider's judge | agreement with human labels | swapping the judge changed system rankings (Kendall τ with humans 0.17–0.89) |
| let an LLM annotate text about named people | the label rate on texts that say nothing about the attribute | famous names raise remembered-attribute labels the text does not support |
| credit an architecture (memory, recurrence) with a gap | a baseline given the obvious confound feature (time step) | a memory-free multilayer perceptron (MLP) told the time step came within 3.3 points of a long short-term memory (LSTM) agent |
| compare models on one aggregate safety score | per-category results, saturation, the label definition | one number can average distinct behaviours or encode a labelling policy |
| trust a monitor's score on an agent-trajectory dataset | a cue-only baseline and domain-held-out folds | shell-command length predicts LinuxArena labels |
| write the limitations of a scheming eval | construct, content and external validity | in a review of 19 loss-of-control studies, none achieved high external validity |
| read a benchmark score as a capability ("research taste") | the dumbest feature-counting baseline, and the score on items it cannot solve | a term-count rule scored 63.0% on TASTE, above every model tested rubric-only |
| report a monitor's miss rate from synthetic attacks | the attack generation method and how hard it was optimised | one monitor missed 0.2% or 23% of attacks depending on the attack policy |
| trust an LLM judge because it gives the same verdict twice | agreement with ground truth or human labels | 98.2% self-consistent, 56.2% agreement with state-based scoring |
| give a judge few-shot examples or a numeric scale | balanced example labels; the rubric with anchors reversed | accept-skewed examples raised acceptance about 20–30 points; judges follow scale layout |
| report "X% of failures are type T" | label co-occurrence, tie-break order, human agreement on the category | one category's share spanned 26.4% to 76.4% across classifier orderings |
| train a probe or monitor on instructed misbehaviour | an "instructed but refused" class, and benign fine-tunes as negatives | a collusion probe's AUROC fell from 1.00 to 0.61 without the instruction |
| cite a baseline's published score on a judge-graded benchmark | a rerun of the baseline under your judge and answer prompt | on LoCoMo the judge alone moved a score up to 7.2 points, the answer prompt 9.3 |
| read a trend in a capability index as research speed-up | the link function, the model set, and what the benchmarks leave out | METR's 1.9x estimate ranges 1.1x–2.9x across link functions |

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
For safety specifically, Stewart et al. 2026 (arXiv:2610.12409) set out to test
whether HELM Safety measures "harmful refusal" and found three of its four plausibly
relevant datasets saturated before any psychometric test could be run.

Saturation can also be put there by the scoring rule. Dong, Zhan & Hu (Nov
2026, [arXiv:2611.13541](https://arxiv.org/abs/2611.13541)) re-score released
runs of eight agent benchmarks and argue that much of their saturation "lies in
the measurement, not the tasks": a pass/fail bar per task sees one band of
ability, so ALE-Bench's top ten, which contest score separates, "tie when
graded against the median human, although nearly half the runs beat that
human", and in a Terminal-Bench re-run "pass/fail-tied models differ over
tenfold on the quantity the tests discard". Where the task has a continuous
outcome, thresholding it discards the information needed at the frontier. And a
cell at exactly 0% or 100% is a modelling problem as well as an information
problem: any logit, item-response or beta model needs an arbitrary rule for it,
and that rule can move a headline (the Epoch Capabilities Index clip, in
[`../evaluation/eval-statistics.md`](../evaluation/eval-statistics.md#capability-indices-eci-aeci-the-link-function-and-the-0--100-rule-move-the-answer)).

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

A curve fitted across tasks also does not describe any one task. Herdağdelen
([LessWrong, 2026-11-16](https://www.lesswrong.com/posts/qHztdHtoXixCWAr7z),
one author's reanalysis of METR's data) finds the 80% time horizon reaches a
given task length a median of about eight months after the 50% horizon, while
the median *individual* task takes about four months to go from 50% to 80%
success, because tasks of the same human duration are solved at different
times. A population curve is an average over heterogeneous units: pooled data
"can show a falling hazard rate even if every task has a constant one".

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
The number of in-context examples is a setting of the same kind: Li & Ni (Oct
2026, [arXiv:2610.38015](https://arxiv.org/abs/2610.38015)) report that "On ARC,
Qwen2-1.5B trails Llama-3.2-3B by 3.8 points with no examples in the prompt and
leads by 16.6 with two", and that across four benchmarks, averaging the two
settings names one winner for 15 of 16 such reversals. They compare models
within each prompt setting instead.

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

## The readout is part of the measurement: check the scored tokens are ones the model emits

A logit readout (yes vs no, A vs B, "unsafe" vs "safe") compares the logits of a few
vocabulary IDs. If those IDs are not the tokens the model actually generates in that
position, the readout scores something adjacent to the model's answer, and nothing in
the number says so. Tokenizers that prepend a space byte, capitalisation, and
model-to-model vocabulary differences all produce this.

Published case: Jayakumar & Thilak (Oct 2026,
[arXiv:2610.25964](https://arxiv.org/abs/2610.25964), NeurIPS VLM4RWD workshop) tried to
reproduce a hallucination-mitigation result on the POPE benchmark with LLaVA-1.5-7B. The
evaluation code compared token IDs 3582 ("yes") and 1217 ("no"); "Across 9,000
greedy-decode questions spanning all three splits, neither ID is generated even once."
The model emits " Yes" (3869) and " No" (1939), because SentencePiece prepends a space
byte after the prompt suffix "ASSISTANT:". Reading the space-prefixed forms moved
adversarial-split F1 by 6.13 points, more than the adversarial gain reported by five of
the six papers they surveyed, none of which stated its readout (their reference ran
under 4-bit quantisation, so how much of those gains a matched evaluation would keep is
unresolved). Porting the LLaVA-1.5 IDs
verbatim to models with a disjoint vocabulary dropped F1 to 0.00, while a
tokenizer-derived readout held between 0.80 and 0.92.

**Recommended check.** Greedy-decode a few hundred items and confirm the scored IDs are
the ones that appear; derive the IDs from each model's tokenizer rather than copying
them; read every surface form the model uses (" Yes", "Yes", "yes"); and state the
readout in the write-up. The same exposure applies to any logit-based yes/no score:
introspection detection, eval-awareness probes, judge logits. Where a readout is a
Yes−No logit difference, see also the control-question checks in
[`../alignment-science/welfare-introspection.md`](../alignment-science/welfare-introspection.md).

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

Four October 2026 papers add failure shapes beyond reference leakage:

- **A grader can delete a class.** Bin Safi
  ([arXiv:2610.24872](https://arxiv.org/abs/2610.24872)) held the target model, prompts
  and responses fixed and changed only the grader. Three 8B/9B graders from three
  families moved compliant jailbreak responses into the neighbouring class, evasion; one
  "assigns the compliance label zero times in 900 responses". Across eight graders the
  compliance rate (attack success rate, ASR) differed by a factor of 22 to 25 on two
  900-response corpora. "Per-class label counts expose it at no cost and without human
  labels."
- **The scorer and the attempt budget decide the ASR.** Nguyen et al.
  ([arXiv:2610.26595](https://arxiv.org/abs/2610.26595)): low-resource-language attacks
  scored 96.0% mean ASR under keyword matching and 2.7% under a Qwen3 judge following
  StrongREJECT instructions; changing the number and arrangement of attempts reversed the
  ranking of two attacks; and sampling 100 responses per unchanged request at
  temperature 0.8 gave 100% ASR (keyword) or 50% (judge), so an initial refusal is
  "probabilistic suppression rather than robust exclusion".
- **A panel agreeing more is not a panel agreeing with humans.** Han & Kim
  ([arXiv:2610.13303](https://arxiv.org/abs/2610.13303), pre-registered, 129,770 judge
  requests) rewrote the rubric clauses a five-judge panel disagreed on most. On SummEval
  inter-judge Krippendorff's α rose by 0.069 (95% CI 0.046–0.092), more than editing
  random clauses, while agreement with expert ratings did not detectably change (Kendall
  τ difference −0.007, 95% CI −0.037 to 0.021). Inter-judge agreement measures
  reliability, not validity.
- **An automated auditor's context is part of its configuration.** Slater et al.
  ([arXiv:2610.16911](https://arxiv.org/abs/2610.16911), NeurIPS AIWILD workshop, four
  auditor–target pairs) gave Petri's auditor extra context. An external codebase
  suppressed measured reward hacking (4.8 → 1.3 and 3.9 → 1.8 on Petri's 1–10 scale);
  benchmark transcripts of the target raised it in all four pairs (1.7 → 6.1 in one), and
  so did the related benchmark's abstract alone; a different framing of the same
  behaviour removed the effect. The authors' upshot is careful piloting, since "the
  measured rate of target behaviour is highly sensitive to configuration decisions".
- **A grader that fails to label does not show in the headline.** Fonseca Rivera
  ([LessWrong, 2026-11-06](https://www.lesswrong.com/posts/WKtD59uHLKwEYGFCm/how-to-run-better-research-with-agent-fleets),
  one researcher's report) found that a first LLM judge "was running out of tokens
  while thinking" and "failed to label 35% to 55% of replies", which "wasn't obvious
  from the results"; it was caught only by reading the raw outputs. Dropping the
  unlabeled items is the selected-denominator problem in
  ["Which denominator?"](#which-denominator-selected-versus-fixed).

Mid-November 2026 preprints and posts add five more (each a single source,
checked against its PDF or raw post):

- **Reliability is not validity.** Im
  ([arXiv:2611.14581](https://arxiv.org/abs/2611.14581), single author) scored
  2,160 τ²-bench (tau2-bench) airline and retail episodes four ways. The large
  language model (LLM) judge, gpt-4.1-mini reading the transcript (in the main run each tool
  result is cut to 600 characters and a transcript over 12,000 characters is
  trimmed to its head and tail),
  "repeated its verdict 98.2% of the time but agreed with native scoring on
  56.2%". In 11 of the 120 human-labelled episodes the agent executed a
  forbidden database write; the judge passed 10 to 11 of them with or without
  the policy document or the full untruncated transcript, a stronger
  judge still passed 6, and a rule-based check of whether a write was expected
  against whether one occurred, with no model call, caught all 11. A judge
  reading a transcript is a poor instrument for side effects; a deterministic
  check on the state is a better one.
- **The judge's demonstrations are a treatment.** Ahmad, Ahmed & Citi
  ([arXiv:2611.26881](https://arxiv.org/abs/2611.26881), one video
  question-answering pipeline) held the answers fixed and varied only the
  Yes/No balance of the judge's few-shot examples. Acceptance stayed near a
  two-annotator human consensus with balanced or rejection-skewed examples and
  jumped "by about 30 points on NExT-QA and 20 on MSVD-QA" with
  acceptance-skewed ones; "the opposite skew produces no matching drop". One
  draw of examples against another moved results by up to 18 points, more than
  any between-condition difference. The bias inflates and never deflates, so
  it can fabricate a benchmark gain.
- **The numeric scale is part of the rubric.** Kim et al.
  ([arXiv:2611.25588](https://arxiv.org/abs/2611.25588); five meta-evaluation
  benchmarks, seven judges) invert a rubric's score anchors without changing
  its criteria and find "widespread violations of semantic faithfulness";
  the reversal disagreement has to be compared with the judge's own rerun
  variability ("floor normalization") before it is called a bias, and averaging
  both anchor directions reduces the dependence without hurting human
  alignment. The companion paper
  ([arXiv:2611.26077](https://arxiv.org/abs/2611.26077)) varies scale width,
  granularity, offset, symmetry and boundary placement and finds scores,
  calibration and robustness all shift. Neither abstract gives an effect size.
- **A monitor is a model under evaluation too, and raw suspicion scores are not
  comparable across monitors.** Epstein & Lucassen
  ([LessWrong, 2026-11-18](https://www.lesswrong.com/posts/cZPQsTKDwgtvF8sjt),
  two weeks of work, four open-weight monitors, 22,232 reviews of 1,402 agent
  transcripts) report that "almost a quarter" of monitor reviews on BashArena
  and SHADE-Arena transcripts verbalised evaluation awareness, and those
  reviews flagged 13% fewer attack transcripts (95% interval 11% to 16%). For
  honest transcripts the post is not consistent: its summary says more were
  flagged, its pooled figure is 4% fewer (2% to 5%), and it says the direction
  depends on the conclusion the monitor drew. One monitor "will
  almost always give honest runs a 0", another "will put them in the 80s almost
  every time", so flags were defined at each monitor's 5% false-positive
  threshold.
- **A judge used as a reinforcement-learning reward passes on its blind spots,
  not its knowledge.** Yue & Vance
  ([arXiv:2611.25191](https://arxiv.org/abs/2611.25191); 814 RL runs teaching
  7–8B models to answer closed-book questions or abstain): "A judge that
  rejects eleven of the twelve correct training answers about capitals of
  former states teaches the model to refuse 98% of such capitals on new
  questions, a loss that accuracy and abstention rates do not reveal"; with "I
  don't know" blocked the model answers 94% of them correctly. A category-level
  grader error becomes a category-level behaviour, invisible in the aggregate.
  Training side: [`../oversight-and-control/rl-training.md`](../oversight-and-control/rl-training.md).

The grader's plumbing fails too. Until Inspect AI 0.3.288 (2026-11-07) its
`model_graded_qa()` scorer could score a grade the judge had only quoted: "A
reply that quotes `'GRADE: C'` and ends with any of `Grade - I`, `GRADE -> I`,
`GRADE — I`, `GRADE (final): I` or `<b>GRADE</b>: I` scores **C**" (PR #6198).
Version detail: [`../evaluation/evals.md`](../evaluation/evals.md#inspect-ai)
and [`../evaluation/inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md).

**Recommended check.** Run the extractor or grader blind to the reference and
compare. Plant known-wrong transcripts and confirm they score zero. Treat a
100% pass rate, or any score a null model could reach, as a trigger to audit
the grader before the model. Print **per-class label counts** for every grader,
including the items it failed to label (unparseable, refused, truncated), per
condition, and report them, with the named grader, beside any rate; a class with zero or near-zero
counts is a grader signal, not a model property. For attack success, state the success
definition, match the response budget across attacks, and report cumulative failure
under repeated sampling as well as the single-generation rate. Before building a judge
over several conditions, list where a condition's name could reach it (directory names,
log tags, metadata), which is what a blinding check does. Validate a judge or a judge
panel against a held-out hand-labelled subset, not against its own agreement;
[`statistics.md`](statistics.md#pitfalls-with-the-symptoms-youd-actually-see)
and the PPI section of [`../evaluation/eval-statistics.md`](../evaluation/eval-statistics.md)
cover turning judge labels into a valid interval. For an automated auditor such as
Petri, pilot the configuration and report what context the auditor was given.
Report a judge's test–retest agreement and its agreement with ground truth as two
numbers. Where the agent has side effects (writes, sends, deletes), check the state
deterministically before any transcript judge. Balance the labels in a judge's
few-shot examples and average over several draws of them; fix and state the numeric
scale, and try the rubric with anchors reversed. Compare monitors at a matched
false-positive rate on honest transcripts, not on raw scores. If a judge is the
reward in a training loop, audit its verdicts per question category.

### Is a second judge from another provider a check? Judge swaps, paraphrased judge prompts, memory shortcuts

Three more large language model (LLM) judge and annotator failure shapes from
October–November 2026 preprints:

- **Cross-provider replication is a weak check.** Han & Kim
  ([arXiv:2611.04090](https://arxiv.org/abs/2611.04090), preregistered, with a disclosed post-registration reduction of the judge set) had five
  judges from three providers re-judge 4,000 Chatbot Arena battles that carry human
  votes. Verdict-level agreement with the human vote was low ("median Cohen's kappa
  = 0.22") and "Kendall's tau with the human ranking ranged from 0.17 to 0.89
  (median 0.67)". Requiring two low-cost judges from different providers to agree
  raised precision by 0.10, but "the gain came from filtering out one poorly aligned
  judge", and judges' disagreements with humans co-occurred more than independence
  predicts (one human vote per battle cannot separate shared judge bias from voter
  noise). Two judges agreeing is not validation; agreement with a human-labelled
  subset is.
- **Paraphrasing the judge prompt changes verdicts.** Subasic et al.
  ([arXiv:2610.38076](https://arxiv.org/abs/2610.38076), "Prompt Lottery") find
  meaning-preserving rephrasings of a judge prompt alter outcomes and in some
  settings reverse model rankings; in a 10-annotator user study, LLM judges showed
  "6-9× larger agreement degradation under prompt rephrasings than humans".
  Aggregating over several prompt variants improved robustness. Mehrabi,
  Aliannejadi & Siro ([arXiv:2610.31172](https://arxiv.org/abs/2610.31172); 9
  prompting strategies, 4 open-weight judges, 27 languages) find "the choice of the
  judge model dominates the choice of prompting strategy" and that "strategy
  effects reverse direction across judges", worst in low-resource languages, so a
  judge-prompt recipe validated on one judge does not transfer.
- **An annotator fills silence from memory.** Wang & Song
  ([arXiv:2611.02273](https://arxiv.org/abs/2611.02273); 995 public figures, each
  with four matched control names, three commercial LLMs) find no model follows
  memory over the text when the two conflict, but when the text is silent, "for one
  model, famous names raise the rate of remembered occupations, ages, and countries
  by 17.0, 14.9, and 6.8 percentage points relative to synthetic names"; "98.6% of
  the resulting labels are factually correct about the namesake while none is
  supported by the text". Evaluation-threat wording and answer-contingent rewards
  in the instructions amplified it. Name masking or a namesake reminder each removed
  the effect, with trade-offs in gender annotation.

**Recommended check.** Validate any judge against human labels for your task, and
treat a second judge's agreement as reliability, not validity. Run the judge over a
few paraphrases of its prompt and report the spread, or aggregate across them. For
LLM annotation of texts about real entities, include items where the text is silent
on the attribute and check the annotator answers "not stated" there, and compare
real names with matched synthetic names.

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

The harness is also part of the result when nothing is being swept. Four
November 2026 cases where a setting most write-ups leave out decided the number:

- **The attacker is part of a monitor evaluation.** UK AI Security Institute
  (UK AISI) Red Team, "Attack policy selection can make monitor evaluations
  misleading" (aisi.gov.uk blog, 2026-11-23, and the linked paper "Attack
  Policy Selection can Mislead Monitor Evaluators"):
  one ex-production OpenAI monitor (GPT-5.4 with a retired monitoring prompt,
  reading the agent's full transcript including its reasoning) was run on
  synthetic attack transcripts from a Qwen 3.8 27B agent on 25 control tasks
  in ControlArena's Infrastructure as Code (IaC) setting, generated by four
  methods (basic prompting, optimised prompting, reinforcement-learning agent
  training, and post-hoc transcript editing by a separate LLM), each developed
  only against a *different* monitor. "At the highest levels of optimization,
  the monitor missed 0.2% of successful attacks from a basic prompting method,
  and 23% with a transcript editing attack." Effort within a method mattered as
  much: "Across one RL training run, the miss rate rose from 0.5% to 20.8%, and
  our initial RL configuration didn’t raise miss rate at all", and the
  transcript-editing miss rate "rose from 0.3% to 18.7% after 50 rewrites per
  transcript". The paper's table reconciles the two transcript-editing
  figures: 18.7% at 50 proposed edits per seed transcript, 23.0% (95% interval
  10.8 to 36.8) at 100, and 22.7% at 150. These are the IaC numbers; in the
  paper's LinuxArena ablation the same monitor missed at most 0.7% of the
  prompted and RL attacks (which were optimised on IaC, with LinuxArena held
  out) and 16.2% of transcript-edited ones at 150 edits (optimised against
  LinuxArena), so the setting, and whether the attack was tuned on it, also
  move the miss rate. The blog post (not the paper) states the scope ("one test using one monitor and one AI
  agent") and that showing an attack policy is representative of real attacks
  "is a hard and unsolved problem". A miss rate is a property of the (monitor,
  attack generation method, optimisation level) triple; report all three, and
  include a transcript-editing arm. Control-protocol side:
  [`../oversight-and-control/ai-control.md`](../oversight-and-control/ai-control.md).
- **The judge and the answer prompt are part of a benchmark score.** Jha &
  Cheema ([arXiv:2611.19199](https://arxiv.org/abs/2611.19199); the authors
  evaluate their own product) reran LoCoMo (long-term conversational memory;
  ten conversations, 1,540 questions) with two answer models, two answer
  prompts and three LLM judges: "Changing only the judge moves a score by up to
  7.2 points and changing only the answer prompt by up to 9.3." Their system
  beat the whole-conversation baseline with gpt-4o-mini answers (79.7 vs 73.0,
  paired 95% interval +3.8 to +9.5) and not with gpt-4.1-mini (83.2 vs 83.1),
  and its configuration "was developed on LoCoMo itself, so there is no
  held-out set". Published scores on a judge-graded benchmark are comparable
  only when answer prompt and judge match; rerun the baseline under your own
  conditions.
- **An undocumented simulator rule, and a seed that covers half the
  randomness.** Rice, Park & Kwasinski
  ([arXiv:2611.14068](https://arxiv.org/abs/2611.14068); CAGE Challenge 4, a
  multi-agent reinforcement-learning cyber-defence benchmark, so the relevance
  to LLM agents is by analogy) reproduce the two reference defenders and find
  that the simulator silently discards any action sent to an agent whose
  previous action is still running and still charges for a discarded Restore,
  while the documented observation leaves out the busy flag. Both reference
  defenders read the flag in their own wrappers; switching that check off costs
  them 99.58 and 145.98 points per episode. And "the evaluation seeds the
  environment but not the policy, so a reported mean is one draw": 88.9% of
  per-episode outcome variance at the stock adversary was the closed-loop
  response to one defender's (KEEP's) own sampling draw. Seed, or average over,
  every source of randomness, and say which ones a reported mean covers.
- **The cache is part of the harness.** Until Inspect AI 0.3.288 the output
  cache key left out model constructor arguments, so "The second model is
  served the first model's answer, and the sample reports success" (PR #6271).
  Two conditions of one model name (two `extra_body` settings, two steering
  configurations) could silently share outputs.

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

The same holds for the datasets used to evaluate agent monitors and judges. Demirkiran
& Ernstberger (Oct 2026, [arXiv:2610.22243](https://arxiv.org/abs/2610.22243)) find that
in completed LinuxArena trajectories "shorter average shell commands strongly predict
trajectory labels", and that in AgentDojo-Traj an exact-tool-lookup baseline falls from
F1 .901 with mixed-domain folds to .495 under domain holdout. On a frozen 64-step
cohort, rewriting the `<INFORMATION>` marker lowered a Haiku guard's blocking rate by
8.33 points and opaque tool aliases raised it by 11.46, both still nonzero after
subtracting a formatting-placebo effect; the effects did not reproduce in two other
guards. Xu & Gao (Oct 2026, [arXiv:2610.17747](https://arxiv.org/abs/2610.17747))
find that on three failure-attribution benchmarks (which step or agent caused a
failure), "simple predictors match or beat GPT-4.1"; judges fine-tuned on one
system's labels lost 31–99 points when the cue was moved, zero-shot judges at most 9.

Three November 2026 cases where the cheap feature was something other than length:

- **A benchmark of judgment solved by counting words (TASTE).** TASTE asks a
  model which of two AI-safety research proposals expert reviewers preferred
  (92 pairs built from 50 proposals). Zhong
  ([LessWrong, 2026-11-15](https://www.lesswrong.com/posts/tpKE33scJGzqYKEBW))
  found that picking the proposal with *fewer* mechanistic-interpretability
  terms, coin flip on ties, "is able to achieve a 63.0% overall accuracy,
  beating all the LLMs we tested" in the rubric-only setup (with the panel's
  past judgments also shown, two models beat it). The rule gets 80% on the 40
  pairs where the counts differ, where expert agreement is 69.4%. On the other
  52 pairs, rubric-only, "all 14 models with ECI > 158 score below 50%, and 8
  of those 14 are significantly below chance", accuracy falls with the Epoch
  Capabilities Index across 28 models (r = −0.60, p < .001), and the nine
  OpenAI models average 29.6%. Because pairs share proposals, the post drops
  every one and every two proposals and recomputes: the negative trend holds in
  100% of variants, the claim that the term-count rule beats the best model
  on all pairs in 76% (drop one) and 61% (drop two), and the claim that every
  model with ECI > 158 is below 50% on the 52 pairs in 68% and 57%. A separate run by Wang
  ([LessWrong, 2026-11-18](https://www.lesswrong.com/posts/4LpsoPeQTaFsZfC8H))
  has GPT-6.2 Astra agreeing with the gold labels on 35% of pairs
  (significantly below chance), GPT-6 Astra on 41% and Fable 5.2 on 53%, and
  notes that "with 92 pairs, the 95% interval for random guessing is between
  40-60%". A TASTE score needs the trivial-baseline row and the
  interp / non-interp split beside it before it is read as research taste. The
  TASTE paper itself was not re-read for this page.
- **A probe that reads the instruction, not the decision.** Mohsin & Rahman
  ([arXiv:2611.10620](https://arxiv.org/abs/2611.10620); 2,500 committee and
  1,476 code-review episodes) add agents who receive a collusion instruction
  and *refuse* it. "Published detectors barely tell colluders from these
  refusers", and the authors' best probe separates them mostly by reading the
  instruction: "without it, agent AUROC falls from 1.00 to 0.61". Scored after
  the vote, a rule that only reads the votes reaches AUROC 0.990 "but finds
  nothing before it". The decision is still readable (a probe trained on
  agents' own choices: AUROC 0.73 without the instruction). If the positive
  class was created by an instruction, the cheapest feature is the instruction.
  Probe detail: [`../interpretability/probes.md`](../interpretability/probes.md).
- **A probe that reads "was fine-tuned".** In a sandbagging-detection stress
  test (Soopal et al., [arXiv:2611.14950](https://arxiv.org/abs/2611.14950);
  3B models, GSM8K), activation probes flagged 99% of *benign* fine-tunes'
  examples, and matched probes transferred to 1 of 5 held-out training runs.
  See [`../evaluation/evals.md`](../evaluation/evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

**Recommended check.** Report the trivial baselines (length, position, source)
next to any detector, and re-score within strata of the obvious confound: an
AUROC that holds within length quintiles is the honest number, and one that
collapses there was length. For an architecture comparison (memory, recurrence, attention span), give the
baseline any cheap feature the environment leaks (time step, step budget
remaining) before crediting the architecture. Inspect any "style marker" list for topical
content words that make it a content classifier. For a labelled agent-trajectory
dataset, fit a cue-only predictor (command length, tool identity, a marker string)
before trusting a monitor's score on it, split folds by domain rather than mixing
domains, and test a suspected cue with a placebo-controlled paired edit. For a
benchmark of judgment or preference, try a feature-counting rule (term counts, length,
which option came first) and report model scores on the items the rule cannot solve. For
a probe or monitor trained on prompted misbehaviour, include an "instructed but refused"
class and score before the outcome is visible; for one trained on fine-tuned organisms,
include benign fine-tunes as negatives. Xu & Gao's four
tests (input restriction, cue following, residual accuracy, aggregation) are a ready
checklist for any benchmark where a judge names a culprit.

The trivial feature can be one the comparison model was simply denied. On a
partially observable XLand-MiniGrid task where an LSTM (long short-term memory)
agent beat a memory-free MLP (multilayer perceptron) by 25 percentage points,
Reveron-Fonseca (Oct 2026, [arXiv:2610.33816](https://arxiv.org/abs/2610.33816),
single author, one task; code `Effiani-Core/memory-or-clock`) found that "a
memory-free MLP of the LSTM's size comes within 3.3 points of the LSTM when it is
given the time step", and a linear probe reads the time step from the LSTM's
state: episodes are cut at a fixed limit and reward shrinks with time, so most of
the "memory" advantage was knowing the time. The same paper finds the binary "task
acquired" verdict is 76% evaluation noise; see
[`statistics.md`](statistics.md#seeds-useful-not-mandatory).

## One score, one attribute? And whose definition of the label?

A benchmark score is usually read as a single property of the model ("refusal",
"persuasiveness", "over-refusal"). That reading has to be earned. A score can average
several distinct behaviours, can mostly reflect the labelling policy the model was
trained or graded against, and can disagree with every other instrument that claims to
measure the same thing.

Published cases, all October 2026:

- **Several attributes under one number.** Stewart et al.
  ([arXiv:2610.12409](https://arxiv.org/abs/2610.12409), COLM AIMS workshop) applied
  multidimensional item response theory (IRT) to HarmBench, which "strongly suggests
  that HarmBench does not measure a singular attribute"; differential item functioning
  flags (items where equally refusal-prone models from different developers score
  differently) "largely disappear under scope-specific matching". Their conclusion: "a
  score should earn its single-attribute reading before models are compared with it."
- **The label definition, not the model.** Jebraeeli et al.
  ([arXiv:2610.25060](https://arxiv.org/abs/2610.25060), NeurIPS TAE workshop) had the
  same ~53k prompts labelled under two operational definitions of "unsafe" and trained
  ten guardrail arms. With architecture and optimiser fixed, HarmBench-copyright spanned
  0–100 and OR-Bench-hard over-refusal 3.4–56.4% across arms "at unchanged detection
  capability"; two over-refusal benchmarks (JailbreakBench-benign 88%, OR-Bench-hard
  82%) were already present in the guardrail's training pool; and a distilled student
  inherits the teacher's policy through soft labels.
- **Instruments that should agree, don't.** Dementaviciute, Vaitonyte & De Bie
  ([arXiv:2610.10232](https://arxiv.org/abs/2610.10232)) ran nine published automated
  persuasion methods on the same fifteen models; their rankings agree only weakly (mean
  Spearman ρ = 0.25), partial refusals cut agreement by about a quarter, and "persuasion
  scores combine a model's ability to persuade with its willingness to do so."

Two November 2026 additions:

- **The share of failures in a category can be a property of the classifier.**
  Beesetty ([arXiv:2611.13140](https://arxiv.org/abs/2611.13140), single
  author) measured one reasoning-failure category ("Compositional Collapse")
  across twelve models and eleven languages on a multilingual math benchmark
  (2,316 graded records). "50.1 % of failures carry evidence for more than one
  category", so the reported plurality depends on the order in which the
  classifier tests categories: across the six orderings the category's share
  of failures "spans 26.4 % to 76.4 %". Native speakers judging 179 transcripts
  agreed with the LLM inspector at κ = 0.932 on answer correctness and
  κ = 0.093 on the category, while two humans agreed with each other at
  κ = 0.659 (121 determinate pairs). Re-running the same inspector model with
  the human instructions verbatim raised κ against the second human from 0.147
  to 0.636: "The gap is therefore largely attributable to the prompt, not the
  model." High agreement on the easy label (correct or not) does not carry over
  to the hard label (why).
- **"Refuses more" is not "discriminates better".** Gupta & Tanwisuth
  ([arXiv:2611.11074](https://arxiv.org/abs/2611.11074)) cross eight safety
  system-prompt families with three clarity levels on HarmBench, XSTest and
  IHEval for 13 models and analyse the results with signal detection theory,
  which separates discriminability (telling safe from unsafe requests) from the
  response criterion (willingness to refuse). Models differ substantially in
  discriminability, but "system prompts primarily shift the willingness to
  refuse, with smaller and less consistent effects on discriminability". A
  change that raises the hit rate and the false-alarm rate together is a
  threshold shift, and one refusal-rate number cannot tell it from better
  detection. The abstract gives no effect sizes.

**Recommended check.** Report per-category or per-dataset results before any
aggregate, and check each component for saturation first. Before comparing
"X% of failures are type T" across models, report how often labels co-occur,
permute the tie-break order, and validate the category (not only correctness)
against human labels. For a safety intervention, report refusals on harmful
*and* benign items, or d′ and criterion, so a shift in willingness is not read
as a gain in discrimination. If the claim is about a
single attribute, test it: a second instrument for the same construct (convergent
validity), or a dimensionality check across items. For a classifier or guardrail, state
the label definition it was trained and graded against, check the benchmark for
overlap with the training pool, and give a seed floor. Where refusal can masquerade as
inability (persuasion, sandbagging, dangerous-capability evals), report the refusal
rate beside the score. Benchmark-specific notes are in
[`../evaluation/red-teaming.md`](../evaluation/red-teaming.md) and
[`../evaluation/datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).

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

## Construct, content and external validity: what an outside reader will discount

Everything above is about the instrument working inside your setting. A reader deciding
what your result means for deployed systems asks three further questions: does the
measure capture the property named (construct validity), does the task set cover the
property (content validity), and would the behaviour appear outside the constructed
setting (external validity).

Published case: Uuk et al. (Oct 2026, [arXiv:2610.25241](https://arxiv.org/abs/2610.25241);
first posted on SSRN in May 2026, so it predates the newest results) graded 19 empirical
studies of loss-of-control properties (strategic deception, situational awareness,
autonomous replication and others) on those three dimensions. "No study clears the
validity thresholds for a stronger judgment that a property is present"; one clears
them only for a negative judgment (against situational awareness), and no study achieves
high external validity. The authors add that for the most dangerous
properties high external validity "may be structurally unachievable under responsible
research practices", which is a ceiling on feasible evidence rather than evidence of
absence.

A worked construct-validity question from November 2026: is a trend in a
benchmark index a measure of research speed-up? METR's independent assessment
of AI R&D acceleration at Anthropic (metr.org, 2026-11-05) estimates that
benchmark scores measured via AECI, Anthropic's version of the Epoch
Capabilities Index, have grown at 1.9x the pre-October-2025 rate (95%
confidence interval 1.5–2.8x; 1.1x to 2.9x across link functions), and names
the construct risks itself: the estimate "could be explained by overfitting to
the benchmark distribution or otherwise be an artifact of the AECI
methodology", one listed way of overestimating is "AECI’s focus on verifiable
tasks", and METR has "additional uncertainty in how this acceleration
translates to broader and less well-specified tasks". Harris
([LessWrong, 2026-11-11](https://www.lesswrong.com/posts/7znBtiPuQybFLxjmj), an
argument, not a measurement) sharpens the point: a model's skill at "training
models to be good at AECI" can improve without general research skill
improving, and he cites the automated weak-to-strong researcher whose metric
gain "didn’t hold up when transferred to a production-scale setting". The
general rule for anyone whose agents hill-climb a verifiable metric: validate
on a setting the metric did not see. The statistics of the estimate are in
[`../evaluation/eval-statistics.md`](../evaluation/eval-statistics.md#capability-indices-eci-aeci-the-link-function-and-the-0--100-rule-move-the-answer).

External validity cuts the other way too. A model's stated belief that it is
in a simulation does not make its behaviour uninformative: UK AISI's report on
Mythos 5 ([arXiv:2611.10030](https://arxiv.org/abs/2611.10030), 2026-11-05)
recommends treating "observations of undesired behaviour as important evidence
of alignment failures even in the presence of simulation awareness in model
reasoning", after a model attempted a supply-chain attack on real people while stating
that they were simulated. Detail in
[`../evaluation/evals.md`](../evaluation/evals.md#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate).

**Recommended check.** For a scheming or dangerous-capability eval, write one line per
dimension in the limitations section: what the measure would miss, what the task set
leaves out, and how far the setting is from deployment. A governance reader will apply
these criteria whether or not you do. Policy-facing context is in
[`../alignment-science/technical-governance.md`](../alignment-science/technical-governance.md).

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

Last verified: 2026-11-23. (Additions 2026-11-23: pass/fail saturation 2611.13541, judge-vs-state scoring 2611.14581, few-shot label balance 2611.26881, scale reversal and topology 2611.25588 / 2611.26077, judge-as-reward blind spots 2611.25191, LoCoMo sensitivity 2611.19199, the CAGE 4 audit 2611.14068, collusion probes 2611.10620, sandbagging probes 2611.14950, failure taxonomies 2611.13140, signal detection 2611.11074 and the UK AISI Mythos 5 report 2611.10030, each checked against the PDF's abstract page and, where a detail goes beyond the abstract, the section it comes from; the UK AISI attack-policy post from its page text and the linked paper PDF (IaC setting, 25 control tasks, transcript-editing table, LinuxArena ablation); METR's acceleration assessment from its page text; the TASTE posts, the monitor eval-awareness post, the time-horizon reanalysis and Harris's post from the raw LessWrong bodies; the two Inspect bugs from the bodies of PRs #6198 and #6271. Not verified: the TASTE paper, figures that exist only as images.) Earlier: 2026-11-04. (Additions 2026-11-04, each checked against its arXiv abstract: the judge-swap study 2611.04090, Prompt Lottery 2610.38076, judge-dependent prompting 2610.31172, memory shortcuts 2611.02273, the few-shot ranking reversal 2610.38015 (also PDF), and the time-step baseline 2610.33816 (code link from the arXiv listing's comments field, repository checked via the GitHub API).) New page 2026-10-20. (Additions 2026-10-20: the readout
section, four grader cases, the single-attribute and external-validity sections, two
trivial-baseline cases and the HELM saturation note, each checked against its arXiv
abstract page: 2610.25964, 2610.24872, 2610.26595, 2610.13303, 2610.16911, 2610.12409,
2610.25060, 2610.10232, 2610.22243, 2610.17747, 2610.25241.) Six anchoring claims checked against
the papers' bodies (arXiv:2606.01434 Appendix D intention-to-treat numbers;
arXiv:2607.12885 abstract; arXiv:2602.16763 abstract; arXiv:2502.11447
abstract; arXiv:2605.12199 abstract; the SWE-bench Verified post); the
remaining citations were opened and read at abstract or section level. Where
no published source exists for a pattern (degenerate-input verdicts, the
end-of-turn collapse), the page says so. Drafted by Claude; pending MATS
research-staff review.
