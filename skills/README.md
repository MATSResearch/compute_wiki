# Agent skills

Skills for Claude Code (and other agentic CLIs that read `~/.claude/skills/`),
distilled from this wiki. They exist so an agent doing research work follows the
program's conventions instead of inventing its own.

| Skill | Fires when the agent is about to... |
|---|---|
| [`mats-experiment-workflow/`](mats-experiment-workflow/) | start a project, plan what to run next, keep a research journal, organise run outputs, or decide whether to scale up |
| [`mats-research-rigor/`](mats-research-rigor/) | pre-register a hypothesis, accept a result, raise a concern about its own work, resolve a prediction, write up, or release code |
| [`mats-research-interview/`](mats-research-interview/) | fix a plan or call a result with the researcher, when they ask (or accept the offer) to be interviewed — the decisions surfaced in rounds over a design tree |
| [`mats-statistics/`](mats-statistics/) | claim a difference is real, choose a test, or put an error bar on a number |
| [`mats-visualization/`](mats-visualization/) | write plotting code, choose a colormap, or save a figure |
| [`mats-intervention-evidence/`](mats-intervention-evidence/) | claim it removed / unlearned something, that a finetune changed something, or that particular training data caused a behaviour |
| [`mats-lean-formalization/`](mats-lean-formalization/) | translate a mathematical or theoretical claim into a checked Lean artifact and report its assumptions and limits |
| [`mats-lean-debug/`](mats-lean-debug/) | diagnose a failed Lean check while preserving the intended theorem |
| [`mats-lean-library-search/`](mats-lean-library-search/) | locate and apply existing Lean or Mathlib declarations |
| [`mats-lean-review/`](mats-lean-review/) | review statement fidelity, proof completeness, and assumptions |
| [`mats-lean-cleanup/`](mats-lean-cleanup/) | finish a generated or repaired Lean proof, or edit an existing proof for presentation |

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

Agents that are not loading skills automatically can find every skill and wiki
page, with when each is worth opening, in the
[agent index](../docs/start-here/for-agents.md).

## Optional reminders

The [skill hint hook](../docs/engineering/skill-hints.md) can point an agent to a
relevant installed Lean skill after reading or editing a proof. Hints are brief,
non-blocking, and deduplicated per session. Installation is separate from skills.

## Skills from elsewhere

Other people's skills are often the better choice for tool mechanics these skills
deliberately leave out. A skill is instructions your agent follows, and code it may
run, with your permissions, so **read it, pin it, scan it** before installing:

```bash
gh skill preview OWNER/REPO SKILL                      # read SKILL.md and its files first
gh skill install OWNER/REPO SKILL --pin <tag-or-SHA> --agent claude-code --scope project
```

`gh skill` (GitHub CLI, marked "preview") installs the latest tagged release, else the
default branch, when no version is given, and defaults to `--agent github-copilot`
when run non-interactively. Cisco's `skill-scanner` is useful triage, not a guarantee
(66.7% held-out recall at its recommended setting). Skip installs that tell your agent
to fetch and follow a remote instruction file. Full guidance:
[agentic-swe-practices.md → Third-party skills and plugins](../docs/engineering/agentic-swe-practices.md#third-party-skills-and-plugins-installing-safely).

| For | Consider | Overlap with these skills |
|---|---|---|
| Inspect AI logs and running evals | Meridian's **inspect-skills** (`meridianlabs-ai/inspect-skills`; `/plugin marketplace add meridianlabs-ai/inspect-skills`, `/plugin install inspect-skills@meridian`) | None; these skills do not cover Inspect mechanics |
| Framework mechanics (TransformerLens, SAELens, nnsight, pyvene, TRL, vLLM) | One category of Orchestra's **AI-Research-SKILLs**, e.g. `/plugin install mechanistic-interpretability@ai-research-skills` | None for mechanics; skip its `autoresearch` orchestrator, which conflicts with the human-in-the-loop workflow in `mats-experiment-workflow` |
| Lean proving workflows | Cameron Freer's **lean4-skills** (`cameronfreer/lean4-skills`, v4.11.3; `/plugin marketplace add cameronfreer/lean4-skills`, `/plugin install lean4`) | Overlaps `mats-lean-*`: pick one set per project so the agent is not given two procedures |
| Writing hooks as markdown rules (for example, block edits to held-out data) | Anthropic's **hookify** (`/plugin install hookify@claude-plugins-official`) | Complements `mats-research-rigor`; its `file` rules do not see shell writes |

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
