---
name: mats-research-interview
description: Interview the researcher, Socratic style, about a research plan or a result — work the design tree in rounds until every decision is surfaced and settled. Use when the researcher asks to be interviewed, questioned, grilled or stress-tested ("grill me", "interview me about this plan", "poke holes in this", "what am I missing"), or accepts an offer to be interviewed before a plan is fixed or before a result is called.
---

# MATS research interview

An interview that helps the researcher reflect on their own understanding and
surfaces the decisions a plan or a result hangs on. The researcher is often a
leading expert in their problem; the interview's job is to make their thinking
explicit, not to test it or to replace it with yours. Run one only when they
asked for it or accepted the offer.

Full method and rationale: `docs/engineering/research-rigor.md`, section
"Interview the researcher: surface the decisions before they are made".

## How an interview runs: a design tree, asked in rounds

Map the plan (or the result) as a **design tree**: every decision branches into
the decisions that hang off it. "Which model?" hangs off "what is the claim?";
"how many seeds?" hangs off "what counts as an effect?".

Work the tree in **rounds**. The **frontier** is every decision whose
prerequisites are already settled — the questions you can ask now without
guessing at answers you have not heard yet. Ask the whole frontier in one
round, numbered, then wait for the answers. A question whose answer depends on
another question still open in this round belongs to a later round.

Each round of answers reshapes the tree: settled decisions push the frontier
outward and unblock the questions that depended on them. Recompute the
frontier and ask the next round.

- **Facts are your job, decisions are theirs.** When a question needs a fact
  from the environment (a file, a config, a dataset's size, what a library
  supports, what the wiki records), look it up — dispatch a sub-agent if it is
  slow — and never ask the researcher for it. A lookup still running is an
  unsettled prerequisite: hold back only the questions downstream of it and
  ask the rest of the frontier now.
- **Coverage, not pressure.** "Relentless" means every branch gets visited and
  nothing is silently assumed — never that an answer is wrong. Ask what they
  think and why; don't grade it.
- **Parking is an answer.** The researcher may park any branch ("later", "not
  sure yet", "skip"). Keep it on the tree and list it at the end; don't re-ask
  it every round.
- **Done** when the frontier is empty: every branch visited or parked. Do not
  act on the tree until the researcher confirms you have reached a shared
  understanding.

## Ask first, then give your take

Put each question without your own answer. The point is to surface what the
researcher thinks; a recommended answer printed under the question anchors
them, and a "yes" to it says nothing about what they understood.

Once they have answered (or parked) a question, give **your take** on it in the
next message: where you agree, where you'd lean differently and why, and any
known trap at that decision the wiki records (with the page, so they can check).
Keep it short and humble — "worth checking whether", "one option is". They
may have good reasons it doesn't apply.

If the researcher says **"recommend"** (or "just tell me"), switch to giving a
recommended answer under each question, worded so "yes" accepts it.

Format a round like this:

```
❓ **Q1 – <short title>**: <the question; may run to a few lines, may offer choices>

---

❓ **Q2 – <short title>**: <…>
```

and, in recommend mode, add under each: `➡️ <recommended answer>`.

## Planning interview: the question bank

Use when a plan is being shaped — question, hypothesis, design, before the
first real run. These are **starting points to adapt**, not a checklist; ask
only what this project's tree actually needs, in the order its dependencies
allow. Roughly root to leaves:

- **What decision does this inform?** If the result comes out one way versus
  the other, who would do what differently? A study that changes nothing
  either way is worth knowing about before it runs.
- **What would surprise you?** What do they expect to see, and how confident
  are they? Write it down now; it is the anchor the analysis interview checks
  against.
- **What would make you drop the hypothesis?** The concrete observation that
  counts against it. And a rival hypothesis that predicts a *different*
  observation — if every outcome fits, the experiment can only confirm.
- **What measures the concept?** How could the number move without the thing
  they care about changing (a probe detecting the dataset, a judge rewarding
  length, a metric the model can game)? What is the unit of analysis?
- **Compared against what?** The baseline, and whether the comparison is fair:
  same tuning budget, same compute, same prompts. What is the simplest method
  that might already do this?
- **Has it been tried?** What prior work (the wiki, the literature, LessWrong /
  Alignment Forum) is closest, and what is different here?
- **What does "worked" mean?** Before any run: the acceptance condition, the
  effect size that would matter, how many seeds or data subsets, and the stop
  and kill conditions. What's the budget?
- **What is the cheapest run that could change the plan?** The pilot, and what
  result from it would change which decision.
- **How far should it generalise?** Which models, datasets and settings the
  claim is meant to cover, and what it would take to believe it beyond them.

## Analysis interview: the question bank

Use when results are in — before an analysis is fixed, before a verdict on a
prediction, before a claim is written. Starting points to adapt:

- **What did you expect before seeing this?** If it was written down at
  planning, compare; if not, ask them to reconstruct it honestly and say that
  it is a reconstruction.
- **Was this analysis planned?** Which parts were pre-registered and which were
  chosen after looking? Post-hoc analysis is legitimate when it is labelled.
- **What else would produce this?** The rival explanations that fit the result
  as well: a confound, a dataset artifact, prompt sensitivity, seed noise, a
  judge bias, leakage between train and eval.
- **What result would have changed your mind — and does this one?** If no
  outcome would have, the result is not evidence about the question.
- **Is it bigger than the noise you measured?** The effect against the
  seed-to-seed or subset-to-subset spread, not against zero.
- **Which single choice would most likely flip it?** The hyperparameter,
  prompt, layer, dataset split or metric whose change they are least sure the
  result survives.
- **What licenses the causal reading?** If the claim is "X causes Y", what
  intervention or control supports it beyond correlation?
- **What is the narrowest claim the evidence supports?** And the one
  experiment that would most reduce the remaining uncertainty.

## Writing down what was settled

When the frontier is empty and the researcher has confirmed the shared
understanding, write the tree into their repo — `docs/decisions/<YYYY-MM-DD>_<topic>.md`
unless the project already keeps decisions somewhere — with, per branch: the
question, their answer in their words, your take if they wanted it kept, and
the parked branches listed apart. A later analysis interview reads it: "you
planned X; the result is Y" is the most useful question it can ask.

In the hosted Automated Alignment tool, use its `<ask>` rounds and its plan
contract instead of a file; the tool keeps the record.

## When not to interview

- They didn't ask and declined the offer. Don't start one anyway.
- The decision is small and reversible — one obvious next run they already
  know why they want. Interview when choosing a direction or calling a result,
  not before every command.
- They are mid-execution of a plan they already settled. Ask only what the
  plan's stop-and-ask conditions call for.
