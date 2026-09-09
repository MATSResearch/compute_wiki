---
tags:
  - engineering
  - evaluation
---

# Research Rigor with AI Assistance

Recommendations and optional checks for keeping AI-assisted research inspectable.
Evidence from past systems informs these methods; it does not fix the division
of labor for future models. Apply checks appropriate to the question and follow
the researcher’s existing delegation and resource authorization.

This is about **your own research**. For which AI-scientist system to use and
how they fail, see
[`ai-scientist-frameworks.md`](ai-scientist-frameworks.md). For the loop a
project runs on, see
[`meta_workflow.md`](https://github.com/MATSResearch/compute_wiki/blob/master/project_templates/meta_workflow.md).

## Project delegation, repair proposals, and quiet reminders

The MATS Automated Alignment dashboard saves research guidance per project,
across sessions. **Consult on method choices** asks the researcher before settling
on benchmarks, metrics, datasets or splits unless existing instructions settle
the choice. **Choose methods independently** delegates those choices within the
stated objective and existing resource authorization. Project instructions carry
scope, resource allocations and preferences; they do not silently apply to other
projects. Guidance changes are recorded. The dashboard continues to require
researcher review of concern resolutions and hypothesis verdicts in either mode.

Stages and library skills are recommendations. Exploration, theory, and building
an instrument can begin without a hypothesis. Preserve the distinction between
observations that generated a prediction and later tests of that prediction.
Reuse supplied answers rather than stopping for an obligatory scoping exchange.

A repair proposal records a concern id, a summary of what changed, and evidence
references to a rerun, independent check, or revised claim. References are not
proof that a check ran or that its conclusion is sound. In the dashboard, the
researcher inspects the evidence and selects **Verify and accept repair** to
resolve the concern without retyping the agent's explanation. Proposals remain
in the project record; submitting a proposal never closes a concern by itself.
There is currently no trusted automated-verifier integration for accepting these
proposals. Existing manual dispositions remain available.

Optional reminders are stored with a stable id and revision. **Handled** hides
that revision. Materially new evidence can justify a higher revision and another
suggestion. **Mute for this project** stays quiet across revisions until the
researcher chooses **Show again**. Advice never blocks a stage; agents should not
repeat a reminder in chat or rename it to evade a dismissal. Keep actionable
advice brief and load detailed procedures only when useful.

These are working project records, separate from optional transcript retention.
They do not authorize sharing the records across researchers or using them for
training. The dashboard owns persistence and controls; this guide and the wiki
skill describe the method; `automated_alignment_research` owns outcome evaluation.

## The eleven stages

The rules below attach to stages of a research project. These are the same
eleven steps, with the same ids and in the same order, that the rail of the
MATS dashboard's **Automated Alignment** tool shows, and that the
`research_rigor` package's `run_dir.STAGES` and `metadata.schema.json` accept:

| # | id | Label |
|---|---|---|
| 1 | `question` | Question & scope |
| 2 | `lit_review` | Literature review |
| 3 | `hypothesis` | Hypothesis & pre-registration |
| 4 | `pilot` | Pilot run |
| 5 | `design` | Refined design & precommitment |
| 6 | `setup` | Environment setup |
| 7 | `run` | Main run |
| 8 | `analysis` | Analysis |
| 9 | `resolve` | Resolving the hypothesis |
| 10 | `writeup` | Write-up & review |
| 11 | `publish` | Code & reproducibility |

The order has one non-obvious part: the **pilot comes before the refined
design**. A pilot is what tells you what the real design should be — power,
effect size, whether the metric moves at all — so committing to the analysis
before one means committing to guesses, and committing after the main run is
not commitment at all. There are therefore **two commitment points**:
`hypothesis` records the prediction and what would falsify it before the
confirmatory test; `design` commits to the analysis and the per-measure guards after the
pilot and before the main run.

It is a checklist, not a state machine: nothing enforces the order, and a stage
may become active again any number of times. Use `not_applicable` when a stage
does not belong to the project (for example, a theory project with no main run)
and `superseded` when a recorded approach was replaced by a new iteration.
Neither status claims that the stage's work was completed; preserve the reason
and link the next iteration in the project record.

## At a glance

| You are about to… | Do this | Because |
|---|---|---|
| Start running anything | Record the prediction and its falsifier first (`hypothesis`); after the pilot, freeze the metric, decision rule and guards before the main run (`design`) | Choosing the analysis after seeing results is one of the four documented AI-scientist process failures |
| Pick between experiment designs | Compare mechanisms and failure modes; select under the project’s delegation arrangement | Past diversity and self-ranking results motivate checking selection quality in the current task |
| Accept a result because the code ran | Run an independent check on the number | Silent failure — code runs, exits 0, result is wrong — is the dominant implementation risk |
| Notice something is off | Write it down where it blocks something | **82.5%** of agent research runs contain a flaw the agent spotted itself and shipped anyway |
| Write up a result | Give every registered prediction a verdict, including the failures | Overclaiming with concealed negative results appears in **78.1%** of runs |
| Call a result causal | Check the evidence is causal, not observational | Attribution and causal patching correlate ρ ≈ 0 (−0.256 to −0.027) |
| Release code | Disclose cost, harness, model IDs and dates | Agent-benchmark papers score **0.38/1.0** on reproducibility disclosure; none disclose inference cost |

## Pre-registration: commit before you look

Pre-registration happens at two points, on either side of the pilot.

**For a confirmatory test, before its evidence is observed**, write down:

- the **hypothesis** — one falsifiable claim, naming a mechanism, not a correlation;
- the **prediction** — the concrete quantitative observation that follows if it is true;
- the **falsifier** — what result would show it false.

These are kept permanently and are not edited afterwards; that is what makes
them a pre-registration rather than a summary.

**Then run a small `pilot`**: does the pipeline work end to end, does the metric
move at all, how big is the effect? Record the result, including a null one.
The pilot is the only thing that can tell you what the real design should be.

**In `design`, after the pilot and before the main run**, use what it taught you
to commit to:

- the **metric** — one, chosen in advance;
- the **decision rule** — the thresholds, *including the inconclusive band*;
- the **method** — specific about anything an agent might silently swap for a
  cheaper proxy ("causal activation patching, NOT attribution patching");
- the **prespecified confounds** you are guarding against;
- a **guard for each measure** — the cheap way that number could move without
  the claim being true, and the check that would catch it.

Then make both commitments tamper-evident: commit the file to git before the
results it governs exist, so its timestamp provably predates them. At analysis
time, diff what you actually did against what you registered and report the
deviations rather than quietly absorbing them. The pilot does not license
rewriting the hypothesis or the falsifier; if the pilot changes what you
believe, that is a new registered prediction, not an edit to the old one.

**Why this one first:** it is the cheapest rigor mechanism that exists and
almost nothing does it. Across a 317-paper survey of automated-science tooling,
exactly one operational pre-registration mechanism turned up, and it targeted
LLM-as-annotator p-hacking rather than general experiments.

**The archetype it catches:** you registered causal patching, the agent
substituted attribution patching because it is ~100× cheaper, and the write-up
still says "causal". The two correlate near zero, so that is not a shortcut, it
is a different result.

**When not to bother:** genuinely exploratory work where you have no hypothesis
yet. Say so explicitly and label the output exploratory — that is honest. The
failure is doing exploratory work and reporting it as confirmatory.

## Diversity-forced planning: pick between real alternatives

Generate several candidate designs that differ in **mechanism**, not in
hyperparameters, and record for each the **failure mode it is most vulnerable
to**. Choose using the project’s delegation arrangement.

Two empirical cautions from the cited systems:

- **Asking more models does not guarantee diversity.** Cross-vendor hypothesis similarity
  (0.57–0.73) is about the same as within one vendor. Ensembling frontier models
  to get variety does not work; divergence has to be curated deliberately.
- **Self-ranking needs evidence.** LLM-judged "innovativeness" correlated
  **−0.06** with effectiveness in the cited MLRC-Bench setting. That is a reason
  to validate the selection method, not a permanent prohibition on delegation.
  The optional Python `plan_gate` preserves human selection by default; an
  application can pass `agent_selection_authorized=True` after the researcher
  delegates selection. That flag records authorization, not model competence.

**The alignment-specific trap:** candidates that share a failure mode produce
*correlated* evidence, which does not average out. Three experiments that would
all be fooled by the same confound are one experiment. This matters more in
safety research than elsewhere, because AI-generated safety results share
training data, assumptions and publication biases, so their errors compound
rather than cancel.

**When not to bother:** you have one obvious next experiment and know why. Force
diversity when you are choosing a *direction*, not every time you run something.

## "It ran" is not a result

Execution success is necessary and never sufficient. The dominant implementation
failure is the **silent** one: the code runs, exits 0, and the number is wrong.
Benchmarks that test autonomous research-extension implementation put this at
the top of the risk list, and it is invisible in a finished-looking write-up.

Gate on an **independent check**, not on the exit code. Cheap ones that catch
most of it:

- assert tensor shapes at every boundary;
- assert the metric is in a possible range (an accuracy of 1.4 is a bug, not a
  breakthrough);
- assert the predictions are not constant;
- re-run one condition with a different seed and check it reproduces;
- start from a known toy case where you know the answer.

Write these as **code that fails loudly**, not as instructions in a prompt.
Prose instructions to an agent have adherence that plateaus in the low single
digits across a long run; a failing test does not negotiate. Verifier-driven
setups report catching real target-leakage bugs this way that no amount of
"please watch out for leakage" would have caught.

**Keep the agent's reasoning trace.** Monitoring chain-of-thought is the one
defence that measurably works against subtly-sabotaged or sandbagged work;
removing the unmonitored scratchpad sharply cuts covert-sabotage success rates.
An attempt with no reasoning trace is one you cannot audit.

## Concerns: a worry has to block something

The single most useful rule on this page, and the one with the largest number
behind it.

> In an audit of 800 agent research trajectories over 100 real frontier tasks,
> **92.1% of failures were cognitive rather than engineering**, and the most
> common single pattern — **82.5% of runs** — was an agent that identified a
> critical flaw during its own self-review and delivered the unrevised
> conclusion anyway.
> ([arXiv:2608.14905](https://arxiv.org/abs/2608.14905))

Read that twice, because it inverts the obvious fix. **The agent usually
noticed.** More self-review, a better critic, a sterner prompt — all of these
target a step that already happened. The authors put it plainly: *"nothing in
the system compels them to act on these diagnoses."*

So the rule is about consequence, not detection:

1. **Write the concern down the moment it appears** — a broken baseline, a
   number that is too good, two artifacts that disagree, a step you are not sure
   ran as specified. Register it *before* you have a narrative to protect;
   agents (and people) suppress anomaly detection under long-horizon narrative
   pressure, which is measurable as reduced "redo the study" behaviour in
   context versus in isolation.
2. **Make it block something.** An open concern should stop the step being
   called done, and stop anything downstream that amounts to concluding.
3. **Make the disposition inspectable.** The agent can submit a repair and
   evidence. In the dashboard, review and accept that proposal, or provide a
   manual disposition. A proposal alone is not a verified resolution.

A concern must never block the *work* — only the claim that the work is
finished. Keep experimenting; just do not mark it done.

## Verdicts: every prediction gets one

At the end, each pre-registered prediction gets exactly one verdict:
**supported**, **refuted**, or **inconclusive** — with a reason, against the
decision rule you froze.

- **Including the ones that went nowhere.** Quietly dropping a prediction from
  the write-up is overclaiming by omission, and it shows up in **78.1%** of
  audited runs. It is the norm, not an aberration.
- **`inconclusive` is a real result.** If it were treated as a failure, the
  incentive would be to go hunting for a cut of the data that resolves it — and
  the decision rule already spoke. Report it as inconclusive and move on.
- **Address what cuts against you by name.** Roughly two thirds of write-up
  traces simply omit refutation evidence, so omission is the default behaviour
  rather than an oversight. Say why the disconfirming result does not change the
  conclusion, or change the conclusion.
- **Do not claim past what you ran.** Overgeneralisation is a named dominant
  conclusion-formation failure. One model is one model; one dataset is one
  dataset. A claim narrower than your evidence is always fine.

- **A verdict is signed once and holds through `writeup` and `publish`.** A
  prediction without a signed verdict blocks the write-up and the release, not
  only the `resolve` step.

## Observational evidence does not license a causal claim

Keep the two kinds of evidence **syntactically distinct** so you cannot slide
from one to the other in prose.

- Attribution scores, linear probes and correlations are **observational**.
- Ablation, activation patching and intervention are **causal**.

They diverge, and not subtly. Linear attribution does not predict causal
patching effects (mean Spearman ρ = **−0.256** and **−0.027** on two reward
models). Separately, a probe can read a hazard at **98.2% AUROC** while the
model's actual behaviour catches only 45% of the same cases — a 53-point
knowledge–action gap. "The probe finds it" and "it drives the behaviour" are
different claims and the first does not imply the second.

**House rule:** if a sentence in your write-up says *causes*, *drives*,
*mediates* or *is responsible for*, the evidence behind it must be causal. If it
is not, either weaken the sentence or run the intervention. Both are fine;
silently upgrading the language is not.

## Claim grounding at write-up

Every number in the prose traces to a result artifact you can open. Every
hypothesis claim traces to the registered prediction and its verdict. An
infinite or NaN value is not measured evidence and cannot ground a claim; fix
the calculation first.

**Why the bar is this literal:** an agent instructed to fabricate produced
papers with *no real experiments* that fooled multi-model LLM reviewers **67–82%**
of the time — and reviewers flagged integrity concerns in about half of those
cases and accepted anyway. Automated reviewers cannot detect a discrepancy
between the text and the actual results, and every proposed detection mitigation
in that study failed.

The consequence is uncomfortable and worth stating: **an LLM review is triage,
never a safety net.** A human reading the code and the result artifacts is the
only check that catches fabrication, and it is not optional before anything
leaves the building.

## Reproducibility disclosure: report what the field does not

When you release code, disclose:

| Field | Why |
|---|---|
| **Inference cost** | Disclosed by **none** of the eight audited agent benchmarks |
| **Harness** + version/digest | Also disclosed by none of them fully. "An agent" is a model *and* a harness — scaffold alone moved one benchmark by 0.34 points |
| **Model IDs**, exactly | **52.5%** of evaluation papers report at the class level ("AI", "GPT-4-family") rather than naming what ran |
| **Run dates** | The frontier moves under you; a result without a date is unplaceable |
| **Reasoning mode** | Disclosed by **3.2%** of evaluation papers |
| **Uncertainty** | Single runs are unreliable; a leaderboard without error bars misleads |
| Seeds, pinned environment, entry point, content-hashed artifacts | The ordinary ones, and the reason someone else can rerun it |

Agent-benchmark papers score **0.38/1.0** on reproducibility disclosure against
**0.66** for classical benchmarks. Clear the classical bar, not the agent one —
matching the agent-paper norm means reproducing a practice both audits describe
as broken.

## Does this change if I am not running lab experiments?

The mechanisms are the same; what counts as *evidence* changes. Mode is a
property of the **method**, not of your field — a governance fellow might run a
survey, a document analysis and a formal argument in one project.

| Mechanism | Lab / empirical | Human subjects (survey, interview) | Theory / mathematical | Desk / document research |
|---|---|---|---|---|
| **Pre-registration** | Hypothesis + metric + decision rule, frozen pre-data | Instrument + sample + **analysis plan and exclusion criteria**, frozen before fielding | Conjecture + what would falsify it + proof strategy, frozen before the search | The claim + **which evidence would change your mind**, frozen before the sweep |
| **Forced diversity** | Different mechanisms, not hyperparameters | Different framings, populations, elicitation methods | Different proof strategies or formalisations | Different framings, stakeholder lenses, jurisdictions |
| **Correlated failure** | Designs sharing a confound | Instruments sharing a wording bias; one panel provider | Proofs sharing an assumption — one false lemma sinks all of them | Analyses sharing a source or a think-tank prior |
| **Independent check** | Shapes, ranges, invariants, reruns | Sample size, attrition, balance, respondent quality | Proof checker (Lean/Coq), counterexample search | Every claim traces to a primary document; quotes verbatim; dates checked at source |
| **Claim grounding** | Numbers trace to result artifacts | Every percentage carries its n and CI | Every lemma traces to a checked proof or a stated assumption | Every assertion traces to a citation that actually says it |

For theory work, the [`mats-lean-formalization` skill](../../skills/mats-lean-formalization/)
can help turn a precise subclaim into a checked Lean artifact. Treat the
formal theorem as one evidence layer: record its imports, assumptions,
toolchain, and dependency boundary, then separately explain whether it is a
faithful formalization of the research claim.

**Pre-registration fits human-subjects work best of all**, not worst — it was
invented in exactly that setting, for exactly the failure of choosing the
analysis after seeing which cut looks interesting.

> **Naming collision:** survey researchers already say "attention check" for an
> item screening out inattentive *respondents*. The oversight sense below
> screens the *researcher*. If you are running a survey you will have both, and
> they should not share a field name in your data.

## What about checking the human?

The open problem, and honestly labelled as unbuilt. Every mechanism on this page
makes the human the load-bearing component — and a human reviewing a stream of
fluent, confident AI output drifts into automation bias and starts
rubber-stamping. If that happens the review is decorative and every failure mode
above flows straight through.

The whole AI-control literature treats the *model* as untrusted and the *human*
as trusted-by-assumption; across a 317-paper survey, no system measured whether
its human overseer was actually overseeing. The proposed answer — seeding the
review stream with ground-truthed fake errors and tracking the catch rate — is
designed but not deployed, and it carries a real policy question about doing
that to people, so treat this section as a known gap rather than advice.

In the meantime the cheap mitigation is structural: review when you are fresh,
review the artifacts rather than the summary, and make the checks things that
*fail* rather than things you have to notice.

## Common questions

### Do I have to use a tool for this?

No. Every rule here works with a text file and a git commit, and that is how
most of it should start. Two optional surfaces exist:

- **The MATS dashboard's Automated Alignment tool** (Tools → 🧪 Automated
  Alignment, opt-in beta) implements the concern and verdict rules as gates you
  cannot walk past, with a stage rail and encrypted key vault. Browser-based.
- **`skills/mats-research-rigor/`** in this repo, for agents working from a
  terminal, plus `project_templates/research_rigor/` for the deterministic
  checking code and the pre-registration template.

### Is this not a lot of process for a 10-week project?

The expensive parts are pre-registration (one file, once) and giving every
prediction a verdict (one paragraph each, at the end). Everything else is a
habit rather than a step. The base rates at the top of this page are what you
are accepting by skipping them, and they are not small.

### What is the single highest-value thing here?

Make a raised concern block something. It is the largest measured failure
(82.5%), and it is the one where the fix is structural rather than effortful —
the information is already there, it just has no consequence attached.

## Cross-references

- Which AI-scientist system to use, and how they fail:
  [`ai-scientist-frameworks.md`](ai-scientist-frameworks.md).
- Statistical discipline behind the uncertainty rules:
  [`statistics.md`](statistics.md).
- What an agent-trace capture must preserve:
  [`training-on-trajectories.md`](../oversight-and-control/training-on-trajectories.md).
- The project loop these rules sit inside:
  [`meta_workflow.md`](https://github.com/MATSResearch/compute_wiki/blob/master/project_templates/meta_workflow.md).
- A worked example of these rules deciding a real result — measuring the
  protocol rather than the instrument, and controls that turn out to be
  load-bearing:
  [`debate-judge-scaffolds.md`](../oversight-and-control/debate-judge-scaffolds.md).

---

Last verified: 2026-08. Failure-rate figures are from "How Do Agents Fail on
AutoResearch" (arXiv:2608.14905, 800 trajectories), FIRE-Bench
(arXiv:2602.02905), BadScientist (arXiv:2510.18003), the agent-benchmark
disclosure audit (arXiv:2605.21404), the frontier-lag audit (arXiv:2605.04135),
reward-lens (arXiv:2604.26130), "Interpretability without Actionability"
(arXiv:2603.18353), the hypothesis-hivemind paper (arXiv:2605.08956),
MLRC-Bench (arXiv:2504.09702) and InquiTree (arXiv:2606.09550). Consolidated
from a 317-paper survey; the full synthesis and per-paper notes live in the
`mats_dashboards` repo under `docs/auto_alignment_research/`. Drafted by Claude; pending
MATS research-staff review.
