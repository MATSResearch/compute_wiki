---
name: mats-experiment-workflow
description: How to design, run, document and scale a MATS safety research project. Use when starting a new research project or experiment, setting up a project folder, planning what to run next, keeping a research journal, organising run outputs, deciding whether a result is ready to scale up, or when the user mentions MASTER_PLAN, research_journal, planning.md, run directories, or "what should I do next" on a research project.
---

# MATS experiment workflow

The loop a MATS fellow's research project actually runs on. Follow it rather
than inventing a process.

**Source:** this is Nathan's `project_templates/meta_workflow.md` from the MATS
research tooling wiki, condensed. It is the program's own guidance, not
invented here.

## Step 1 — have an idea, set it up to be worked on

- One project folder per idea; `uv init`.
- `README.md` (what + how to run) and `CLAUDE.md` (what a fresh agent should
  read first — mention the knowledge base if there is one).
- `docs/` and `docs/papers/`.
- `docs/planning.md` — the project description. A good way to produce it is to
  talk the idea through in a web chat first and then ask for a project plan.

## Step 2 — start the agent

Point it at the planning doc and have it do the basic setup. Start in planning
mode, graduate to auto mode once the shape is agreed.

## Step 3 — THE LOOP

**a. Research.** Insist every source is saved to `docs/papers/` — papers, blog
posts, tweets, whatever. Write research notes as markdown in `docs/`.

**b. Plan.** Create or extend `MASTER_PLAN.md`, including a ToDo list.

**c. Work the next ToDo item.**

1. Implement.
2. Unit tests, then a smoke test.
3. Trial run — **cap it at 3–5 hours**.

Bugs are inevitable, and in machine learning they are usually *subtle*, so
assume some exist and test defensively:

- start with a known toy task
- overfit a tiny batch first
- assert tensor shapes
- eyeball loss curves immediately
- check for silent `NaN` or overflow

**d. Log.** Better too many notes than too few — easy to search, hard to
remember.

- Keep `docs/research_journal.md` and keep adding to it.
- Runs and logs go in a datestamped run folder under `outputs/`. **Save stderr**
  into the logs or you cannot diagnose crashes.
- Make the config the source of truth, copy it into the run folder at the start,
  and resume from that copy.

**e. Loop back.**

- more ToDos → (c)
- out of ToDos but research not yet turned into ToDos → (b)
- need more ideas → (a)
- dead end → back to Step 1

## Step 4 — scale (not before)

Only after many loops, when the project is well detailed and tested. Scaling
commits real time, money and compute, so **do not jump here early**.

- Estimate the compute you need; spend time looking for efficiency wins first.
- Set up checkpoint saving, soft-stop, and resume-from-checkpoint.
- Set up monitoring (e.g. `wandb`), and be ready to roll back to an earlier
  checkpoint.

## Step 5 — analyse and write up

Understand the results, then communicate them. For deciding whether a result is
real, use the **mats-statistics** skill. For figures, use **mats-visualization**.

## Conventions to follow

- `uv` for environments (`uv run python ...`).
- `outputs/run_YYYYMMDD_HHMMSS_<tag>/` per run, with `metadata.json` recording
  the config. No global plots folder — each run is self-contained.
- `data/` for inputs, `outputs/` for anything generated.

## Going deeper

The MATS research tooling wiki — <https://matsresearch.github.io/compute_wiki/>
— covers which tool to use for what:

- `start-here/project-shapes.md` — catalog of common paper shapes; read this
  when choosing what kind of project this is.
- `engineering/code-recipes.md` — copy-paste patterns and the anti-patterns list.
- `engineering/agentic-swe-practices.md` — driving a coding agent so it writes
  correct research code rather than plausible-looking slop.
- `project_templates/` — runnable starter scaffolds for mech interp, evals,
  AI control and model organisms.
