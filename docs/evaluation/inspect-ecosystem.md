---
tags:
  - evaluation
---

# The Inspect Ecosystem (Meridian Labs)

**Meridian Labs** (`meridianlabs-ai` on GitHub, <https://meridianlabs.ai>) is a
501(c)(3) non-profit building open-source tooling for evaluating and testing
frontier AI models and agents. If you use Inspect, you are using their work, and
several of their other tools are worth knowing about — especially **Scout**,
which will read the transcripts you are already producing.

**Relationship to Inspect and UK AISI.** Inspect AI was built by Meridian's
founding team in collaboration with the **UK AI Security Institute (AISI)**, and
Meridian continues to develop the ecosystem around it. Note the core repository
still lives at **`UKGovernmentBEIS/inspect_ai`** — that is where issues go, even
though the surrounding packages (`inspect_scout`, `inspect_petri`,
`inspect_flow`, `inspect_swe`) live under `meridianlabs-ai`. Inspect is now the
standard evaluation framework across UK AISI, US CAISI, the EU AI Office, Japan
AISI and Korea AISI, and at METR, Apollo, Epoch, SecureBio, Redwood and RAND.

## At a glance

| I want to... | Use | PyPI |
|---|---|---|
| Write and run an evaluation | **Inspect AI** — see [`evals.md`](evals.md) | `inspect-ai` |
| Analyse agent **transcripts** for refusals, evaluation awareness, broken environments | **Inspect Scout** | `inspect-scout` |
| **Audit a model's alignment** automatically over multi-turn conversations | **Inspect Petri** | `inspect-petri` |
| Manage configs and run **large eval sets** reproducibly | **Inspect Flow** | `inspect-flow` |
| Run **Claude Code / Codex CLI / Gemini CLI** as the agent under test | **inspect-swe** — see [`agent-scaffolds.md`](agent-scaffolds.md) | `inspect-swe` |

## Inspect Scout: analysing transcripts you already have

**Inspect Scout** (`inspect-scout` on PyPI,
[`meridianlabs-ai/inspect_scout`](https://github.com/meridianlabs-ai/inspect_scout),
docs <https://meridianlabs-ai.github.io/inspect_scout/>) runs **scanners** over
agent transcripts to surface problems you would otherwise have to read for.
Built-in targets include **refusals**, **evaluation awareness** (the model
noticing it is being tested), and **misconfigured environments** — the last of
which quietly invalidates more agent evals than anything else.

Scanners can be **LLM-based** (a model reads the transcript) or
**pattern-based** (cheap, deterministic).

```bash
pip install inspect-scout
scout scan  ./logs --scanners refusal,eval_awareness
scout view                     # interactive results
scout scan list                # recent scans
scout scan resume              # continue an interrupted scan
```

Python API: `scan()` to run programmatically, `transcripts_from()` to load,
`scan_results_df()` for a pandas dataframe of results, and the `@scanner` /
`@scanjob` decorators to write your own.

### It reads more than Inspect logs — including Claude Code

This is the part worth knowing. Scout ingests transcripts from **Inspect, Arize
Phoenix, LangSmith, Logfire, MLflow, Weights & Biases Weave, and Claude Code**,
plus anything else via its **capture and import APIs**. Local directories or
remote storage (S3) both work.

**Practical consequence for MATS fellows:** if you have been running Claude Code
on the cluster — including through the dashboard's Automated Alignment tool,
which runs one Claude Code session per experiment — **those transcripts are
already scannable**. You do not need to have used Inspect at all. Pointing
`scout scan` at the session directory is the whole integration.

That makes Scout the cheapest available answer to "did my agent quietly refuse
half of these, notice it was being evaluated, or spend the run fighting a broken
environment?" — questions that are otherwise answered by reading hundreds of
transcripts, i.e. not answered.

### Writing your own scanner

The `@scanner` decorator is the extension point, and a custom scanner is usually
a better first move than a bespoke analysis script: you get the transcript
loading, parallel scanning, resumability and the results dataframe for free.

## Inspect Petri: automated alignment auditing

**Inspect Petri** (`inspect-petri` on PyPI,
[`meridianlabs-ai/inspect_petri`](https://github.com/meridianlabs-ai/inspect_petri),
docs <https://meridianlabs-ai.github.io/inspect_petri/>, built with UK AISI) is
an **automated auditing agent**: it drives multi-turn conversations against a
target model to surface concerning behaviour, then scores what happened.

Three model roles:

| Role | Job |
|---|---|
| **Auditor** | takes a seed instruction and designs/drives the conversation |
| **Target** | the model under audit |
| **Judge** | scores the resulting transcript against rubrics |

It ships **170+ conversation seeds** and **38 judging dimensions**, covering
things like unprompted sycophancy, concerning or dangerous outputs, evaluation
awareness, and admirable behaviour. It simulates tools and supports rollback, so
the auditor can back up and try a different line.

```bash
pip install inspect-petri
inspect eval inspect_petri/audit --model <target>
inspect view
```

Python: the `audit()` function from `inspect_petri`, run through Inspect's
`eval()`.

**Output** is transcripts plus judge scores (1–10) with written justifications
tied to specific messages, browsable from both the target's and the auditor's
side.

### When to use it, and when not to

- **Good for:** broad first-pass sweeps for concerning behaviour; generating
  candidate behaviours worth studying properly; a cheap baseline before hand-
  crafting a behavioural eval.
- **Be careful:** a judge score is a **model's opinion**, not a measurement.
  Treat a 1–10 rating as a *pointer to a transcript worth reading*, not as a
  number to average and report. If you do report rates from it, validate the
  judge against hand labels first — see the judge-validation note in
  [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).
- Petri finds *candidates*. Confirming one is a real, robust behaviour is a
  separate piece of work with its own statistics — see
  [`statistics.md`](../engineering/statistics.md).

## Inspect Flow: configs and large eval sets

**Inspect Flow** (`inspect-flow`,
docs <https://meridianlabs-ai.github.io/inspect_flow/>) is configuration and
workflow management for evaluations: defining eval **sets**, running them
systematically, and keeping the runs reproducible. It is in use at UK AISI and
US CAISI for auditing and pre-deployment testing.

Reach for it when you have outgrown a shell script full of `inspect eval`
invocations — many models × many tasks × many configurations, where you need the
matrix to be declarative and re-runnable rather than remembered.

For a single fellow project running a handful of evals, plain `inspect eval` is
usually still the right amount of machinery.

## What else plugs in

Meridian list these as integrating with the ecosystem, all covered elsewhere in
this wiki: **ControlArena** and **LinuxArena** (see
[`ai-control.md`](../oversight-and-control/ai-control.md)), **TransformerLens**
and **nnterp** (see [`mech-interp.md`](../interpretability/mech-interp.md)).

## Common questions

### I never used Inspect. Is any of this useful to me?

Yes — **Scout** especially. It reads Claude Code transcripts and several
tracing formats directly, so you can scan agent runs you already have without
adopting Inspect for anything.

### Where do I file a bug?

Core framework: `UKGovernmentBEIS/inspect_ai`. The satellite packages
(`inspect_scout`, `inspect_petri`, `inspect_flow`, `inspect_swe`): under
`meridianlabs-ai`. Getting this wrong is the most common small friction with
this ecosystem, because the branding and the repository owner differ.

### Can I use these on the MATS cluster?

Yes — they are ordinary pip installs into your virtual environment. Anything
that calls a model API needs your key set up as in
[`faq.md`](../start-here/faq.md); anything that runs a real workload should go
through Slurm rather than sitting on the dev node.

---

Last verified: 2026-08. Checked against meridianlabs.ai and the project docs:
Meridian Labs is a 501(c)(3); Inspect AI was built by Meridian's founding team
in collaboration with UK AISI and the core repo remains `UKGovernmentBEIS/
inspect_ai`; Scout ingests Inspect / Arize Phoenix / LangSmith / Logfire /
MLflow / W&B Weave / Claude Code plus custom sources; Petri ships 170+ seeds and
38 judging dimensions with auditor/target/judge roles. Drafted by Claude;
pending MATS research-staff review.
