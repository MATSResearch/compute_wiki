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

## During research

- Exploration, theory, and instrument building may precede a hypothesis. For a
  confirmatory test, preserve predictions and decision rules before the evidence
  they govern. Record later revisions without rewriting the earlier commitment.
- Choose validation appropriate to the claim. Successful execution, an artifact
  path, a model's review, or an evidence-type label alone does not establish that
  a scientific conclusion is correct.
- Keep results traceable to artifacts and record uncertainty, failures, and
  disconfirming evidence. Separate observations from explanations. Account for
  every registered prediction, including inconclusive ones.
- Treat failure rates from past systems as evidence with scope, not permanent
  limits on what current or future agents can do. Consider alternatives when
  choosing a direction; do not manufacture extra designs for an obvious next step.
- Say what *done* means before starting a run or follow-up, as a checkable
  condition written once; keep evidence (this run bears on that prediction, for
  or against, this much) separate from the verdict a person signs, and cite the
  runs that go against with the same care as the ones for.
- When comparing to a paper, share one axis with it — an anchor run of one of
  their conditions on your configuration, or your idea with one factor swapped
  to their value — rather than reading their absolute number as your baseline.
  Record each paper's configuration factor by factor, blanks for what it did
  not report.
- A shape claim about a representation (ring, helix, manifold) names the share
  of variance of the view it was seen in and cites a check that does not
  project: a similarity matrix in the variable's order, or persistent homology
  against a noise band. UMAP and t-SNE pictures are for looking, not evidence.
  See "A shape in a projection is not a shape in the model" in the wiki doc.
- Before testing a question, record at least two hypotheses that predict
  different observations, or the rival you weighed and why you rejected it.
  Tie each hypothesis to the run that will decide it. When asking for rivals,
  seed the request from a field outside the project's own framing.
- Cite papers as sources someone can open (title, authors, year, link), not
  from memory, and keep the ones you build on apart from the ones you set
  aside.
- Estimate robustness by varying the sample (bootstrap the eval set, overlapping
  data subsets, hyperparameter perturbation), not by sweeping seeds. See
  "Comparability", "Say what done means" and "Evidence is not the verdict" in
  the wiki doc, and "Vary the data, not the seed" in `statistics.md`.

## Concerns and repairs

Record material concerns and investigate them. A useful repair proposal states
what changed, identifies the rerun or independent check, and points to evidence
showing what the repair establishes and what remains uncertain. Do not describe
an unreviewed proposal as verified.

In the MATS dashboard, submit a repair through `<research_update>` using the
concern id supplied by the tool. The researcher can verify and accept the
proposal directly. Until then, the existing concern and conclusion gates remain
in effect; continue useful work while review is pending. In other environments,
follow the researcher's chosen review arrangement rather than importing dashboard
gates from this skill.

## Advice and reminders

Offer advice when it changes a useful decision. Respect handled and muted
reminders; return to a handled topic only when materially new evidence warrants
it. Do not rename a reminder to evade dismissal. Skipping this skill, adapting a
method, or taking an unusual research path is not itself a concern.

Do not deploy attention checks against another person: the wiki's attention-check
component remains a design requiring program authorization.
