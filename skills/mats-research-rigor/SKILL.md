---
name: mats-research-rigor
description: How to keep AI-assisted research honest — pre-register before running, force real alternatives, never accept "it ran" as a result, make a raised concern block something, give every prediction a verdict, and disclose what a reader needs to reproduce it. Use when starting an experiment, deciding whether a result is real, writing up findings, resolving a hypothesis, releasing code, or when the user mentions pre-registration, prereg, falsifier, a concern about a result, inconclusive results, claim grounding, or reproducibility disclosure.
---

# MATS research rigor

Rules for research an agent is helping with. Each exists because of a measured
failure rate, not a preference.

**Source:** `docs/engineering/research-rigor.md` on the MATS research tooling
wiki (<https://matsresearch.github.io/compute_wiki/engineering/research-rigor/>),
condensed. The wiki has the evidence and the citations; go there when the *why*
matters. Deterministic checks are in `project_templates/research_rigor/`.

## The one that matters most

**A concern you raise has to block something.**

In an audit of 800 agent research trajectories, 92.1% of failures were cognitive
rather than engineering, and the most common single pattern — **82.5% of runs** —
was an agent that identified a critical flaw during its own self-review and
delivered the unrevised conclusion anyway.

Detection is not the bottleneck. You will usually notice. So:

- Write the concern down **the moment it appears**, before there is a narrative
  to protect — a broken baseline, a number that is too good, two artifacts that
  disagree, a step you are not certain ran as specified.
- **Do not resolve your own concern.** Take it to the researcher, say what you
  think it means, and let them decide. Raising one costs nothing; sitting on one
  is the failure.
- A concern blocks *declaring a step finished*, never the work itself. Keep
  going; just do not call it done.

## Before running anything

Freeze, in a file, committed to git so the timestamp predates the results:

- the hypothesis (falsifiable, names a mechanism);
- the prediction (concrete, quantitative);
- one metric;
- the decision rule, **including the inconclusive band**;
- the method, specific about anything that could be swapped for a cheaper proxy
  ("causal activation patching, NOT attribution patching");
- the confounds being guarded against.

At analysis time, diff what was actually done against this and report the
deviations rather than absorbing them.

Template: `project_templates/research_rigor/templates/prereg.template.yaml`.

## When choosing between designs

Generate candidates that differ in **mechanism**, not hyperparameters, and record
the failure mode each is most vulnerable to. Then **the researcher picks**.

- Asking more models does not diversify — cross-vendor hypothesis similarity is
  about the same as within one vendor.
- Agents cannot self-select: LLM-judged "innovativeness" correlates **−0.06**
  with actual effectiveness.
- Candidates sharing a failure mode produce correlated evidence that does not
  average out. Three experiments defeated by the same confound are one
  experiment.

## When a run finishes

**"It ran" is not a result.** The dominant implementation failure is silent: code
runs, exits 0, number is wrong. Gate on an independent check:

- assert shapes at every boundary;
- assert the metric is in a possible range (accuracy 1.4 is a bug);
- assert predictions are not constant;
- re-run one condition with a different seed;
- start from a toy case with a known answer.

Write these as code that fails loudly, not as prompt instructions. Prose
adherence decays over a long run; a failing test does not negotiate.

## When interpreting

**Observational evidence does not license a causal claim.** Attribution scores,
probes and correlations are observational; ablation, patching and intervention
are causal. They correlate ρ ≈ 0 (−0.256 to −0.027), and a probe can read a
property at 98.2% AUROC while behaviour reflects it 45% of the time.

If a sentence says *causes*, *drives*, *mediates* or *is responsible for*, the
evidence behind it must be causal. Weaken the sentence or run the intervention —
never silently upgrade the language.

Every finding must name the artifact it came from. A finding that cannot point
at a file is not checkable by anyone.

## When resolving the hypothesis

One verdict per registered prediction: **supported**, **refuted**, or
**inconclusive**, with a reason, against the frozen decision rule.

- **Every prediction, including the ones that went nowhere.** Dropping them is
  overclaiming by omission — 78.1% of audited runs do it.
- **`inconclusive` is a real result.** Do not hunt for a cut of the data that
  resolves it; the decision rule already spoke.
- **Address disconfirming evidence by name**, or change the verdict. Omission is
  the default behaviour, not an oversight.
- **Do not claim past what was run.** One model is one model.

## When writing up

Every number in the prose traces to a result artifact. An LLM review is triage,
never a safety net: fabricated papers with no real experiments are accepted by
LLM reviewers 67–82% of the time, and reviewers frequently flag concerns and
accept anyway. A human reading the code and the results is the only check that
catches fabrication.

## When releasing code

Disclose cost, harness + version, exact model IDs, run dates, reasoning mode,
uncertainty, seeds, pinned environment and entry point. Agent-benchmark papers
score **0.38/1.0** on disclosure against 0.66 for classical benchmarks — clear
the classical bar, not the agent one.

## Not lab work?

The mechanisms hold; what counts as evidence changes. Pre-registration fits
survey work best of all — it was invented there. For theory the "independent
check" is a proof checker or counterexample search; for desk research it is that
every claim traces to a primary document and every quote is verbatim. The wiki
doc has the full mode table.

## Don't

- Don't resolve a concern you raised yourself.
- Don't treat `inconclusive` as a failure to be avoided.
- Don't satisfy a diversity requirement by asking another model.
- Don't let an LLM review stand in for a human reading the code.
- Don't wire up `research_rigor.attention_check` against another person — it is
  designed but not approved, and that is a program-level decision.
