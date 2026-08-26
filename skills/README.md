# Agent skills

Skills for Claude Code (and other agentic CLIs that read `~/.claude/skills/`),
distilled from this wiki. They exist so an agent doing research work follows the
program's conventions instead of inventing its own.

| Skill | Fires when the agent is about to... |
|---|---|
| [`mats-experiment-workflow/`](mats-experiment-workflow/) | start a project, plan what to run next, keep a research journal, organise run outputs, or decide whether to scale up |
| [`mats-research-rigor/`](mats-research-rigor/) | pre-register a hypothesis, accept a result, raise a concern about its own work, resolve a prediction, write up, or release code |
| [`mats-statistics/`](mats-statistics/) | claim a difference is real, choose a test, or put an error bar on a number |
| [`mats-visualization/`](mats-visualization/) | write plotting code, choose a colormap, or save a figure |

## Install

```bash
mkdir -p ~/.claude/skills
cp -r skills/mats-* ~/.claude/skills/
```

On the MATS cluster this goes on the **dev node**, where your home directory is
NFS-shared to every machine — so the skills follow your agent to any node. Install
the compute team's cluster skill alongside them; it covers partitions, Slurm and
etiquette, which these deliberately do not:

```bash
cp -r /mnt/nw/share/skills/mats-cluster ~/.claude/skills/
```

## Why they're thin

Each skill is a short decision layer that points at the full doc on the wiki
(<https://matsresearch.github.io/compute_wiki/>). That is deliberate: an agent
needs the *rule* in context, not twenty pages of prose, and duplicating the wiki
into skill files would guarantee the two drift apart. The wiki stays the source
of truth.

Same reason these say nothing about Slurm, partitions or GPU etiquette — the
compute team maintains `mats-cluster` for that, and restating it here would drift
from the source they own.

## Editing

Change the wiki doc first, then update the skill only if the *rule* changed. If
you find yourself copying more than a screenful into a skill, link instead.
