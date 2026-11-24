---
name: mats-research-rigor
description: Help plan, check, and report AI-assisted research with traceable evidence, explicit uncertainty, and inspectable repairs. Use for research design, interpreting experiments, resolving concerns, or preparing a reproducible report.
---

# MATS research rigor

Help the researcher reach defensible conclusions while leaving room to choose,
adapt, or invent methods. Follow the project's existing delegation arrangement;
reuse decisions and resource authorization already provided. This skill does
not add approval requirements or make a research stage mandatory.

The canonical guide is [Research rigor](https://matsresearch.github.io/compute_wiki/engineering/research-rigor/)
(`docs/engineering/research-rigor.md` in the wiki repo). Read the sections relevant
to the work. Templates and optional executable checks live in
`project_templates/research_rigor/`; use those that test a property the project
actually needs.

## Who decides

- Under **Consult on method choices**, ask before settling benchmarks, metrics,
  datasets or splits unless instructions already settle it; under **Choose
  methods independently** those choices are yours, within the stated objective
  and resource authorization. In either mode the researcher reviews concern
  resolutions and signs hypothesis verdicts. A project's instructions and
  records stay with that project: they do not carry over to other projects, and
  they do not authorize sharing across researchers or use for training.
- The eleven stages (`question` … `publish`, pilot before design) are a
  checklist, not a state machine. Mark one `not_applicable` or `superseded`,
  with the reason, instead of claiming its work was done.
- Before a plan is fixed or a result is called, offer an interview
  (`mats-research-interview`). Offered, never imposed; skip it for a small,
  reversible step the researcher already knows they want, or mid-way through a
  plan they have settled.

## Before the main run

- Exploration, theory, and instrument building may precede a hypothesis: say so
  and label the output exploratory. Keep observations that generated a
  prediction apart from later tests of it.
- A confirmatory test commits at two points. `hypothesis`, before the pilot: the
  hypothesis (falsifiable, naming a mechanism), the quantitative prediction, and
  the falsifier. Then a small pilot, its result recorded even if null. `design`,
  after the pilot and before the main run: one metric, the decision rule with
  its inconclusive band, the method (specific about any cheaper proxy), the
  prespecified confounds, and a guard for each measure (the cheap way it could
  move without the claim being true, and the check that catches it). Commit to
  git each time. The pilot does not license rewriting the hypothesis or
  falsifier: a changed belief is a new registered prediction. At analysis,
  report deviations from what was registered. Never ask an agent for a
  "compelling" result on data it can search: freeze the hypothesis and analysis
  before it sees outcomes (failing that, the wiki's replay-on-subsamples
  correction).
- Before testing a question, record at least two hypotheses that predict
  different observations, or the rival you weighed and why you rejected it.
  Tie each hypothesis to the run that will decide it. When asking for rivals,
  seed the request from a field outside the project's own framing. A rival
  declined with a reason settles it; do not ask again.
- When choosing a direction, compare designs that differ in mechanism, not in
  hyperparameters, and record the failure mode each is most vulnerable to:
  designs sharing one give correlated evidence. Asking more models does not
  diversify, and a model's ranking of the candidates needs validating before it
  is trusted. Do not manufacture extra designs for an obvious next step. Treat
  failure rates from past systems as evidence with scope, not permanent limits.
- Say what *done* means before starting a run or follow-up, as a checkable
  condition written once and never edited.
- When comparing to a paper, share one axis with it, stated up front — an
  anchor run of one of their conditions on your configuration, or your idea with
  one factor swapped to their value — rather than reading their absolute number
  as your baseline. Record each paper's configuration factor by factor, blanks
  for what it did not report. Pin your substrate (base model, trainer, eval
  harness) and do not upgrade it mid-project; a newer base model is a
  registered prediction of its own.
- Inside the project, compare a method with its baseline at matched cost, with
  the baseline tuned as hard as the method: say what each comparison is matched
  on (generated tokens, wall-clock, in-domain learning, updates, or not
  applicable with the reason, e.g. evaluation-only) and the baseline's tuning
  budget. Matched per update is not matched cost, and matched hyperparameters
  are not matched learning.

## While running and reading results

- "It ran" is not a result. Gate on an independent check written as code that
  fails loudly (shapes, possible ranges, non-constant predictions, one condition
  rerun and reproduced, a toy case with a known answer, and, where the work has
  countable units, the units scored counted against the units launched per
  condition and label), and keep the reasoning trace. A unit that errored, went
  unscored or whose checker declined to run is *did not run*, never a pass, a
  failure or a zero. A model's review or an
  evidence-type label alone does not establish a conclusion.
- Cite each run that bears on a prediction as you go, for or against, with a
  weight; cite what goes against with the same care. This evidence is kept
  separate from the verdict, and its tally never sets the verdict. After a
  context compaction, re-read each claim's status (tested, untested, refuted)
  from the evidence and verdict records rather than trusting the summary.
- Estimate robustness by varying the sample (bootstrap the eval set, overlapping
  data subsets, hyperparameter perturbation), not by sweeping seeds. See "Vary
  the data, not the seed" in `statistics.md`.
- *Causes*, *drives*, *mediates*, *is responsible for* need causal evidence
  (ablation, patching, intervention). Attribution, probes, correlations and
  statistics of a weight change are observational: weaken the sentence or run
  the intervention.
- A shape claim about a representation (ring, helix, manifold) names the share
  of variance of the view it was seen in and cites a check that does not
  project: a similarity matrix in the variable's order, or persistent homology
  against a noise band. UMAP and t-SNE pictures are for looking, not evidence.
- When several agents test arms side by side, one coordinator owns the shared
  measurement (items, judge and judge prompt, n, control, figure code) and
  writes one report across arms; flag any arm whose judge, prompt, n or
  shared-file hash differs, and keep a per-arm checklist of what was examined
  (raw outputs included). Fixed measurement buys comparability, not validity.
- Working on your own under an agreed plan, stop only for a reason the plan
  names (done-means met, a stop-and-ask condition, its abandon condition), a
  refused permission you cannot do without, or something only the researcher
  can resolve. A dead end is not one of these: record what was tried and what
  it does not rule out, change direction deliberately (invert an assumption,
  take another route, try to break your best result), letting something other
  than the stuck model pick the move, and keep going. Nor is a
  foreseeable fork: apply the plan's if-then rule, or run both (an objective
  check settles it, or the researcher picks before seeing the outcomes), or
  carry one with the assumption written down, if the choice is reversible and
  sandboxed. Only a one-way door waits. If the work cannot be done, propose
  closing it as unachievable with the reason ("X is unavailable / cannot be done
  because…") rather than faking a dependency or a result; the researcher accepts
  or reopens it. An accepted close is an honest end state, not a pass. When
  filing work that may be impossible, put that way out in its instructions and
  acceptance condition, and do not phrase the goal as "make the tests pass": a
  rule against faking is not enough.

## Concerns and repairs

Write a concern down the moment it appears and investigate it. An open concern
stops the step being called done and anything downstream that amounts to
concluding; it never blocks the work. A repair proposal names the concern,
states what changed, and points to the rerun, independent check, or revised
claim, with what remains uncertain. Submitting one closes nothing: do not
describe an unreviewed proposal as verified.

In the MATS dashboard, submit a repair through `<research_update>` using the
concern id supplied by the tool. The researcher can verify and accept the
proposal directly. Until then, the existing concern and conclusion gates remain
in effect; continue useful work while review is pending. In other environments,
follow the researcher's chosen review arrangement rather than importing dashboard
gates from this skill.

## Verdicts, write-up and release

- Every registered prediction gets exactly one verdict — supported, refuted, or
  inconclusive — with a reason, against the frozen decision rule, signed once by
  the researcher. It holds through write-up and release: neither goes ahead
  with a prediction unsigned. Inconclusive is a result; never drop a prediction.
- Address what cuts against the verdict by name, and do not claim past what was
  run. A configuration is part of what was run: before claiming an absence or an
  inability, sweep the choice most likely to hide the effect, report where a
  sweep first fails, and give the headline beside its range across defensible
  modelling choices. A `supported` with anything cited against it, or nothing
  cited, is shown to the researcher at signing as a flag, not a block. On `supported`, say which
  rivals were refuted, which still fit, and what the survivors agree on; for the
  next run, prefer the one that rules out the most survivors.
- Every number traces to a result artifact someone can open; infinite or NaN is
  not evidence. That includes the counts and claims in an agent's own report of
  its work ("all tests pass", "N papers included"): match them against the tool
  calls and saved files, and recompute counts with code from the artifact. An
  LLM review is triage: a human reads the code and artifacts before anything
  leaves, which is necessary, not sufficient, so a result that matters also
  needs checks written to fail if it is wrong. Cite papers as sources someone
  can open (title, authors, year, a link you checked), not from memory, and keep
  the ones you build on apart from the ones you set aside. Quote what a source
  showed from its results, from the source itself and its current version, not
  from an abstract, a linkpost or an earlier version, and record which part you
  read (abstract or full text) and when.
- On release, disclose inference cost (per step where you have it; with the
  provider, price schedule and date read, from arms that share no prompt cache),
  harness and version, exact model IDs as served (log the id the response
  reports beside the one requested; for an alias that resolves to a dated
  snapshot, request the snapshot id), run dates, reasoning mode and uncertainty,
  with seeds, a pinned environment, an entry point and content-hashed
  artifacts. A judge, reviewer or grader model is part of the measurement:
  re-validate it whenever its version changes.
- Surveys, theory and desk research: same mechanisms, different evidence. See
  "Does this change if I am not running lab experiments?" in the wiki doc.

## Advice and reminders

Offer advice when it changes a useful decision. Respect handled and muted
reminders; return to a handled topic only when materially new evidence warrants
it. Do not repeat a reminder in chat or rename it to evade dismissal. Skipping
this skill, adapting a method, or taking an unusual research path is not itself
a concern.

Do not deploy attention checks against another person: the wiki's attention-check
component remains a design requiring program authorization.
